"""Read a Standard MIDI File's own grid -- tempo, meter, tracks, notes, chroma.

Why this exists separately from `analyze.py`: `analyze.py` measures AUDIO, and
everything this project knows about tempo is inferred from a spectrogram.  A
MIDI file carries the answer as data -- division, tempo events, time signatures,
and note-on/note-off ticks -- so it is a ruler of a different kind: it does not
estimate the grid, it IS the grid.  When both exist for the same music the MIDI
settles questions the comb score only votes on (see PROGRESS Phase 111: the bar
phase was decided by +1.01 dB over a 1.0 dB threshold, which a MIDI would simply
state).

`--compare` is the check that has to come first, though: before trusting a MIDI
as the grid *for a given recording*, measure whether it is the same music at
all.  Two recordings of one piece share a pitch-class set even when they differ
in tempo, key (up to a rotation) and arrangement, so the test is the MIDI's
chroma against the audio's -- and the sharpest form of it is not the best
circular shift but whether the SETS can be reconciled at all.  A file with three
empty pitch classes cannot be a rotation of one that uses all twelve.

No dependency on mido or any MIDI library: an SMF is a container of length-
prefixed chunks with variable-length quantities, and that is the whole format.

    python _tools/music/midi_grid.py <file.mid>
    python _tools/music/midi_grid.py <file.mid> --compare <audio> [--sr 22050]
"""

import collections
import struct
import sys

import numpy as np

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


# ------------------------------------------------------------------ parsing
def _vlq(b, i):
    """Variable-length quantity: 7 bits per byte, high bit = 'more follows'."""
    v = 0
    while True:
        if i >= len(b):
            raise ValueError('truncated variable-length quantity')
        c = b[i]
        i += 1
        v = (v << 7) | (c & 0x7F)
        if not (c & 0x80):
            return v, i


def parse(path):
    """Return {'format', 'ntrks', 'tpq', 'tracks': [...]} for a format 0/1 SMF.

    Running status is the one piece of this format that bites: a status byte may
    be omitted when it repeats, so the byte after a delta time is *either* a
    status or the first data byte of the previous one.  Getting that backwards
    does not raise -- it desynchronises the track and reports a wrong note count.
    """
    d = open(path, 'rb').read()
    if d[:4] != b'MThd':
        raise ValueError('not a MIDI file: header is %r' % d[:4])
    hlen = struct.unpack('>I', d[4:8])[0]
    fmt, ntrks, div = struct.unpack('>HHH', d[8:14])
    if div & 0x8000:
        raise ValueError('SMPTE division (%d) is not handled' % div)
    i = 8 + hlen

    tracks = []
    while i < len(d):
        if d[i:i + 4] != b'MTrk':
            raise ValueError('expected MTrk at %d, found %r' % (i, d[i:i + 4]))
        tlen = struct.unpack('>I', d[i + 4:i + 8])[0]
        end = i + 8 + tlen
        j = i + 8
        tick = 0
        run = None
        t = dict(name=None, notes=[], tempos=[], timesigs=[], progs=[], chans={},
                 length=0)
        open_notes = collections.defaultdict(list)
        while j < end:
            dt, j = _vlq(d, j)
            tick += dt
            if d[j] & 0x80:
                run = d[j]
                j += 1
            if run is None:
                raise ValueError('running status with no status at byte %d' % j)
            st = run
            if st == 0xFF:
                mt = d[j]
                j += 1
                ln, j = _vlq(d, j)
                data = d[j:j + ln]
                j += ln
                if mt == 0x03:
                    t['name'] = data.decode('latin-1')
                elif mt == 0x51:
                    t['tempos'].append((tick, int.from_bytes(data, 'big')))
                elif mt == 0x58:
                    t['timesigs'].append((tick, data[0], 2 ** data[1]))
                continue
            if st in (0xF0, 0xF7):
                ln, j = _vlq(d, j)
                j += ln
                continue
            hi = st & 0xF0
            if hi in (0xC0, 0xD0):
                v = d[j]
                j += 1
                if hi == 0xC0:
                    t['progs'].append((tick, v))
                continue
            pitch, vel = d[j], d[j + 1]
            j += 2
            key = (st & 0x0F, pitch)
            if hi == 0x90 and vel > 0:
                open_notes[key].append(tick)
                t['chans'][st & 0x0F] = t['chans'].get(st & 0x0F, 0) + 1
            elif hi == 0x80 or (hi == 0x90 and vel == 0):
                if open_notes[key]:
                    on = open_notes[key].pop()
                    t['notes'].append((on, tick, pitch, st & 0x0F))
        t['length'] = tick
        tracks.append(t)
        i = end
    return dict(format=fmt, ntrks=ntrks, tpq=div, tracks=tracks)


# ------------------------------------------------------------------ measures
def seconds(ticks, tpq, us_per_quarter=1_000_000):
    """Ticks -> seconds.  The tempo is taken as given, not inferred: a MIDI's
    tempo events are how the file *says* it wants to be played, and a 60 bpm
    file can be a 90 bpm performance written down lazily."""
    return [tk * (us_per_quarter / 1e6) / tpq for tk in ticks]


def chroma(notes, weight='count'):
    """12-vector from (on, off, pitch, ch) events.

    `count` is how many times a pitch sounds; `duration` is how long it sounds
    for.  They disagree the same way RMS and peak do -- a piano's left hand
    holds long low notes while the right hand plays many short ones -- so a
    chroma claim has to say which one it used.
    """
    v = np.zeros(12)
    for on, off, pitch, _ch in notes:
        v[pitch % 12] += 1.0 if weight == 'count' else max(0, off - on)
    return v / (v.sum() or 1.0)


def best_shift(a, b):
    """Best circular shift of `a` onto `b`, as (semitones, pearson r).

    Rotations are the right family because a transposed arrangement is the
    common case.  But the result means nothing without the emptiness check
    below: if `a` has pitch classes that are exactly zero and `b` has none,
    every rotation is refuted and the winner is just the best of a bad set.
    """
    def z(v):
        return (v - v.mean()) / (v.std() + 1e-12)
    za, zb = z(a), z(b)
    scores = [(float(np.dot(np.roll(za, s), zb) / 12.0), s) for s in range(12)]
    return max(scores)[1], max(scores)[0]


def compare(midi_chroma, audio_chroma, lines):
    """Can these two be the same music?  Ask the rotated version, not the raw one.

    The tempting test is "does the MIDI use every pitch class?" -- but a
    transposed arrangement is the normal case, so a raw emptiness test rejects
    too much.  The sound version is to rotate first and *then* look for empty
    classes: if the best-scoring rotation still puts a pitch class at zero where
    the audio is loud, no transposition of this MIDI is this recording.  Testing
    only the raw vector would have passed a file that merely happens to be in
    the audio's key while sharing none of its notes.
    """
    s, r = best_shift(midi_chroma, audio_chroma)
    sm = s if s <= 6 else s - 12
    rot = np.roll(midi_chroma, s)
    empty_src = [NAMES[k] for k in range(12) if midi_chroma[k] <= 1e-9]
    empty_rot = [NAMES[k] for k in range(12) if rot[k] <= 1e-9]
    empty_a = [NAMES[k] for k in range(12) if audio_chroma[k] <= 1e-9]
    lines.append('  pitch classes the MIDI never plays:     %s'
                 % (', '.join(empty_src) or '(none)'))
    lines.append('  pitch classes the audio never reaches:  %s'
                 % (', '.join(empty_a) or '(none)'))
    lines.append('  best rotation of the MIDI onto the audio: %+d semitones, r %+.3f'
                 % (sm, r))
    lines.append('  (r is what a rotation test normally gives, but it is a'
                 ' correlation: it is not evidence of authorship by itself)')
    if empty_rot:
        cols = ', '.join('%s %.2f%%' % (NAMES[NAMES.index(n)], 100 * audio_chroma[NAMES.index(n)])
                         for n in empty_rot)
        lines.append('  -> the best rotation still leaves %s empty, and the audio'
                     ' sounds them (%s)' % (', '.join(empty_rot), cols))
        lines.append('     so no transposition of this MIDI is this recording.')
    return s, r


# ------------------------------------------------------------------ reporting
def report(mid, lines):
    """Print the file's structure and return (all_notes, problems).

    The problems list is the parser's own tripwire.  A desynchronised track --
    running status read one byte off, a meta length skipped by the wrong amount
    -- does not raise; it keeps producing events, just not the file's ones.  A
    note that ends after its track's end-of-track tick cannot exist in a
    well-formed file, so counting those turns "parsed something" into "parsed
    this file".
    """
    lines.append('format %d   %d tracks   %d ticks per quarter'
                 % (mid['format'], mid['ntrks'], mid['tpq']))
    allnotes = []
    problems = []
    for k, t in enumerate(mid['tracks']):
        ps = [p for (_on, _off, p, _c) in t['notes']]
        lines.append('  track %d  "%s"  %d ticks  %d sounding notes'
                     % (k, t['name'], t['length'], len(t['notes'])))
        if ps:
            lines.append('     pitch %d..%d   programs %s   channels %s'
                         % (min(ps), max(ps), sorted({v for _tk, v in t['progs']}),
                            sorted(t['chans'])))
        if t['tempos']:
            for tk, us in t['tempos'][:6]:
                lines.append('     tempo at tick %d: %d us/quarter = %.4f bpm'
                             % (tk, us, 60_000_000.0 / us))
        if t['timesigs']:
            lines.append('     time signatures: %s' % (t['timesigs'][:6],))
        stray = sum(1 for x in t['notes'] if x[1] > t['length'])
        if stray:
            problems.append('track %d: %d note(s) end after tick %d'
                            % (k, stray, t['length']))
        allnotes += t['notes']
    lines.append('  %d sounding notes total' % len(allnotes))
    return allnotes, problems


def main(argv):
    if not argv:
        sys.exit(__doc__)
    path = argv[0]
    lines = ['== %s ==' % path]
    mid = parse(path)
    notes, problems = report(mid, lines)
    if problems:
        for p in problems:
            lines.append('  INCONSISTENT: %s' % p)

    tpq = mid['tpq']
    tempos = sorted({x for t in mid['tracks'] for x in t['tempos']})
    us = tempos[0][1] if tempos else 1_000_000
    # The piece ends at the last note-OFF.  Writing `on + off` here instead --
    # which is what this line said first -- adds two absolute ticks together and
    # reports a piece exactly twice as long as it is; the note that exposes it is
    # whichever sits latest in the track.  A duration that lands on a suspiciously
    # round multiple of the real one is this mistake, not a long fade.
    end = max(x[1] for x in notes)
    sec = seconds([end], tpq, us)[0]
    lines.append('  last note-off at tick %d = %.2f quarters = %.2f bars of 4/4'
                 % (end, end / tpq, (end / tpq) / 4.0))
    lines.append('  at %d us/quarter that is %.2f s' % (us, sec))
    if len(tempos) > 1:
        lines.append('  NOTE: %d distinct tempo events; the duration above uses'
                     ' the first only' % len(tempos))

    cnt = chroma(notes, 'count')
    dur = chroma(notes, 'duration')
    lines.append('')
    lines.append('  pitch-class share          count    duration')
    for k in range(12):
        lines.append('     %-2s                    %6.2f%%   %6.2f%%'
                     % (NAMES[k], 100 * cnt[k], 100 * dur[k]))

    if '--compare' in argv:
        au_path = argv[argv.index('--compare') + 1]
        import analyze
        sr = 22050
        if '--sr' in argv:
            sr = int(argv[argv.index('--sr') + 1])
        x = analyze.decode(au_path, sr, 1).astype(np.float64)
        S = analyze.stft(x, n=4096, hop=2048)
        C = analyze.chroma(S, sr, 4096)
        au = C.mean(axis=1)
        au = au / au.sum()
        lines.append('')
        lines.append('  -- against %s --' % au_path)
        lines.append('     audio chroma: %s'
                     % '  '.join('%s %.2f' % (NAMES[k], 100 * au[k])
                                 for k in range(12)))
        compare(dur, au, lines)

    text = '\n'.join(lines)
    # The console here is GBK; the text is UTF-8.  Write through the binary
    # buffer so a bracketed path or a non-ASCII track name cannot kill the run
    # at the last step (same trap as _tools/music/make_song.py).
    sys.stdout.buffer.write((text + '\n').encode('utf-8'))
    return 1 if problems else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
