"""Turn a MIDI file into a finished piece of music -- the notes played, and an
arrangement built around what the notes actually do.

The operator's request (2026-10-11) was "基于那个做一个音乐": make a piece of
music based on that MIDI.  So the MIDI is the MATERIAL, not the specification.
That is the difference between this tool and its two siblings:

  make_song.py  composes an original melody and measures a reference only for
                its grid, key, texture and loudness -- no note is transcribed.
  remix.py      samples a reference RECORDING and builds a kit around it.
  midi_song.py  plays the source's own notes, and derives every arrangement
                decision from measurements of those notes.

WHAT THE SOURCE GIVES AND WHAT IT DOES NOT

Measured by `midi_grid.py`, not assumed:

  grid       60.000 bpm, 4/4, 384 ticks/quarter, 22.50 bars = 90.00 s
  texture    4 piano staves, 936 notes in 296 onsets, all program 0
  dynamics   velocity is CONSTANT PER TRACK -- 100 on the melody staff, 50 on
             the accompaniment, 24 on the two low staves that enter at bar 17.
             So the file states a MIX and no PHRASING.  Nothing in it says
             which note of a phrase is the loud one, because every note of a
             phrase is at the same velocity.  Phrasing therefore has to come
             from somewhere else, and here it comes from register, from the
             note's position in the bar, and from the measured section arc --
             all derived, and all labelled as derived in the report.
  key        F# natural minor; D#, G and A# never sound in any of the 936 notes

That last fact is worth stating because it is the thing that makes this
arrangement auditable: a render of a nine-pitch-class source must still have
nine pitch classes, so the delivered audio can be checked against the source
for identity rather than merely for plausibility.  `--check` does exactly that,
and it is the same test that showed the operator's MIDI is NOT the recording in
asstes/music (DECISIONS 461) -- there it disproved identity, here it proves it.

Requires ffmpeg (D:\\Bot\\ffmpeg\\bin) and numpy.  ASCII output only -- the
console here is GBK.

    python midi_song.py --probe        measure only, print the plan
    python midi_song.py                render, master, encode, check
    python midi_song.py --check        re-measure the delivered files
"""

import argparse
import glob
import math
import os
import subprocess
import sys
import time
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "asstes", "music")
OUTDIR = os.path.join(HERE, "out")
sys.path.insert(0, HERE)

import analyze                        # noqa: E402
import dsp                            # noqa: E402
import make_song as ms                # noqa: E402
import midi_grid as mgrid             # noqa: E402

SR = 44100
NAME = "ReconstructingMoreScience"
REPORT = os.path.join(ASSETS, NAME + ".report.txt")

# ============================== the piano voice ==============================
# A struck string, not a held tone: the partials are slightly stretched by the
# string's stiffness, the high ones die first, and there is a hammer noise at
# the onset.  Those three things are most of what separates "piano" from "sine
# with an envelope".
PARTIAL_MAX = 18
PARTIAL_FALL = 1.35         # amplitude ~ k^-this
INHARM = 0.0004             # partial k sits at k*f*sqrt(1 + B*k^2)
DECAY_C4 = 1.60             # seconds, at MIDI note 60
DECAY_SEMIS = 26.0          # rising this many semitones halves the decay
PARTIAL_DAMP = 0.55         # partial k decays this much faster than k=1
SILENT_TC = 6.9             # -60 dB.  A partial is only generated up to here:
                            # past it its own exponential has made it inaudible,
                            # so the samples would cost time and change nothing
TAIL_MAX_S = 5.0            # and the whole note stops here, with a release
RELEASE_S = 0.40            # so the stop is a decay rather than a chop
HAMMER_MS = 6.0
HAMMER_LVL = 0.30
HAMMER_HI = 2200.0
NOTE_PEAK = 0.22            # peak of one note at velocity 127, after the
                            # partial sum is normalised.  Set so ~70 notes per
                            # bar land the pre-master mix near full scale by
                            # themselves; without it the master's target-RMS gain
                            # would have to swing by whatever the accidental sum
                            # happened to be.
VEL_CURVE = 1.15            # amplitude ~ (vel/127)^1.15 -- deliberately nearly
                            # linear.  Velocity in THIS file is one constant per
                            # staff (100 / 50 / 24), i.e. the transcriber stating
                            # a BALANCE between four staves, not a player stating
                            # a phrasing.  A steep curve would read a mix decision
                            # as a performance decision and turn a 2:1 balance
                            # into 4.6:1 (CLAUDE.md 0.18: a word that makes the
                            # choice for you means you are not measuring)

# ============================== the performance ==============================
HUMAN_MS = 12.0             # +- onset scatter; a step-entered file played
                            # exactly on the grid is the one thing that cannot
                            # be fixed later, and a real hand is never on it
HUMAN_SEED = 20261011
PEDAL_MS = 45.0             # the damper closes over this long before a change
PEDAL_FLOOR = 0.10
PEDAL_GUARD_MS = 8.0        # a note starting just before a change keeps its
                            # attack: the gate must not soften an onset
PAN_SPAN = 0.55             # low notes left, high notes right
PAN_CENTRE = 58             # MIDI note that sits centre
BEAT_ACCENT = 0.06          # downbeats a touch stronger than upbeats -- derived,
                            # since the file itself gives every note of a phrase
                            # the same velocity

# ============================== the arrangement ==============================
# Levels are stated RELATIVE TO THE PIANO BUS, in dB, and applied after the
# piano is rendered.  Absolute per-bus constants looked equivalent and are not:
# the first version set the sub's gain directly and it came out as the loudest
# thing in a solo piano piece (sub -19.5 dB RMS against the piano's -21.2 on a
# 4-bar run).  A ratio cannot do that -- whatever the passage, the sub sits
# where it was told to sit.
SUB_DB = -13.0              # the sub doubles the measured lowest sounding note
PAD_DB = -17.0              # pad tones are the bar's OWN pitch classes
MARK_PEAK = 0.45            # NOT a dB-relative level, and that is the point: an
                            # impact is a transient, so its RMS is a small
                            # fraction of its peak and levelling it by RMS is
                            # levelling it by the wrong number.  Set that way,
                            # the marks bus came out with a PEAK of 1.03 -- one
                            # impact louder than the whole rest of the mix --
                            # and the master's headroom pass then scaled the
                            # entire piece down 6 dB to make room for it, which
                            # is why the first delivered file measured -22 dB
                            # against a -16 dB target.  A percussive layer is
                            # specified by its peak.
REV_AMT = 0.30              # big room: this is a slow solo piano
REV_RT60 = 3.20
REV_PREDELAY_MS = 24.0

SOLO_TAIL_S = 4.0           # silence after the last note, so the tail ring-out
                            # is an ending rather than a truncation

# ============================== the master ===================================
# -19.0, not the -16.0 the other two tools use.  This is a solo piano with a
# measured crest factor around 21 dB: a note attack is 21 dB above the average
# level, so reaching -16 dB RMS means pulling 5 dB off every attack -- a file
# that measures correctly and sounds squashed.  Loudness that has to be bought
# with limiting is the one kind you cannot give back, and a platform will
# normalise the quieter file up for free, so the honest target for this
# material is the one the limiter can reach without doing the music's phrasing
# for it.  The master loop prints the limiter's own peak reduction, so how much
# was actually spent getting here is a printed number, not a claim.
TARGET_RMS_DB = -19.0
PRE_CEIL_DB = -0.80         # headroom for the encoders' overshoot
CEIL_DB = -1.00
BUS_COMP_THRESH_DB = -19.0
BUS_COMP_RATIO = 2.4


def say(lines, s):
    lines.append(s)


def db(x):
    return 20.0 * math.log10(max(1e-12, float(np.abs(x).max())))


def midi_hz(p):
    return 440.0 * 2.0 ** ((p - 69) / 12.0)


def bus_at(sig, ref_rms, rel_db):
    """Scale `sig` so its RMS sits `rel_db` below `ref_rms`.

    A silent bus has no RMS to scale, and dividing by it would produce nan
    rather than silence -- so a bus with nothing in it is returned untouched
    (which is the correct answer for a layer that never got a note).
    """
    cur = float(np.sqrt((sig ** 2).mean())) if sig.size else 0.0
    if cur <= 1e-12:
        return sig
    return sig * (ref_rms * 10.0 ** (rel_db / 20.0) / cur)


def pan_gains(p, pan):
    """Equal-power-ish, kept simple: a linear crossfade would drop 3 dB in the
    centre and make the middle of the piano the quiet part."""
    a = 0.5 * (1.0 + pan)
    return math.sqrt(1.0 - a), math.sqrt(a)


# ============================== reading the source ===========================

def find_source(explicit):
    """The operator's file, found rather than hard-coded.

    Its name has spaces, brackets and a colon-less Windows-invalid set, and
    baking a filename that hostile into a tool means the next person cannot run
    it on their own copy.  One .mid in the folder is unambiguous; two is a
    question, and questions go to the report rather than to a guess.
    """
    if explicit:
        return explicit
    hits = sorted(glob.glob(os.path.join(ASSETS, "*.mid")))
    if not hits:
        sys.exit("no .mid in %s -- pass --mid" % ASSETS)
    if len(hits) > 1:
        sys.exit("%d .mid files in %s; pass --mid to say which" % (len(hits), ASSETS))
    return hits[0]


def load_source(path):
    mid = mgrid.parse(path)
    notes = [n for t in mid['tracks'] for n in t['notes']]
    tempos = sorted({x for t in mid['tracks'] for x in t['tempos']})
    us = tempos[0][1] if tempos else 1_000_000
    tpq = mid['tpq']
    return dict(path=path, mid=mid, notes=notes, tpq=tpq, us=us,
                spq=us / 1e6,                       # seconds per quarter
                bpm=60.0 / (us / 1e6))


def tick_s(src, tick):
    return tick * src['spq'] / src['tpq']


# ============================== structure ====================================
# Measured, not declared.  The source's own note counts per bar are strongly
# bimodal -- 18..22 in the opening, 72..81 through the middle, 48 in the
# thinning, then 4..12 in the coda -- so the sections are read off that curve
# rather than imposed on it, which is the same rule remix.py follows (its
# busiest passage is also its quietest, so position was the wrong ruler there;
# here position and density agree, and the numbers are what say so).

def bar_stats(src, n_bars):
    counts = [0] * n_bars
    lows = [None] * n_bars
    pcs = [set() for _ in range(n_bars)]
    for on, off, pitch, _ch, _vel in src['notes']:
        b = int(on / src['tpq'] / 4)
        if not (0 <= b < n_bars):
            continue
        counts[b] += 1
        lows[b] = pitch if lows[b] is None else min(lows[b], pitch)
        pcs[b].add(pitch % 12)
    return counts, lows, pcs


def sections(counts, hi=0.60, lo=0.35):
    """Label each bar full / thin / sparse against its own maximum, then merge
    runs.  Thresholds are fractions of the observed peak, not absolute counts,
    so this reads any file rather than this one."""
    peak = max(counts) if counts else 0
    if peak <= 0:
        return [(0, len(counts), 'sparse')]
    out = []
    for i, c in enumerate(counts):
        lab = 'full' if c >= hi * peak else ('thin' if c >= lo * peak else 'sparse')
        if out and out[-1][2] == lab:
            out[-1][1] = i + 1
        else:
            out.append([i, i + 1, lab])
    return [tuple(x) for x in out]


# ============================== the pedal ====================================
# Harmony changes are read off the notes: for each eighth note, which pitch
# classes are sounding.  When that set changes, the damper closes.  This is what
# a pianist does with the pedal, and deriving it from the material beats
# declaring "pedal down throughout", which on 936 sustained notes is mud.

def sounding_changes(src, lines):
    """When the damper closes, read off the notes rather than declared.

    THE RULE IS THE BASS, and that is a measurement, not a preference.  Three
    proxies were measured on this file before one was chosen:

        sounding pitch-class set, every eighth      165-229 changes
        sounding set, eighth, symmetric diff >= 3    47
        pitch class of the LOWEST sounding note      42   <- this one

    The set-based rules fire on any note entering or leaving, and on a 296-onset
    texture in 23 bars that is a change every half second -- a stutter, not a
    pedal; 165 dips in 92 s is a tremolo on the damper.  What a pianist pedals on
    is where the HARMONY moves, and in this material that is the bass: it
    alternates between F# and D and changes about twice a bar.  The two
    independent proxies landing at 42 and 47 is the reason to trust it -- one
    number would have been a coincidence (CLAUDE.md 0.20: one error is a clue,
    and it takes two agreeing measurements to call it).
    """
    step = src['spq']                       # a quarter note, in seconds
    ticks_per_step = src['tpq']
    # The piece's own length, from the notes -- not from a bar count handed in.
    total = tick_s(src, max(n[1] for n in src['notes']))
    spans = [(on, off, pitch) for on, off, pitch, _c, _v in src['notes']]
    prev = None
    changes = []
    t0 = 0.0
    while t0 < total:
        a = t0 / src['spq'] * ticks_per_step
        b = a + ticks_per_step
        low = None
        for (on, off, pitch) in spans:
            if on < b and off > a:
                low = pitch if low is None else min(low, pitch)
        if low is not None:
            pc = low % 12
            if prev is not None and pc != prev:
                changes.append(t0)
            prev = pc
        t0 += step

    # The rejected rule, measured on the same run rather than quoted from the
    # docstring: a reader who doubts the choice should be able to see both
    # numbers without editing the file.
    h = src['spq'] / 2.0
    prev_set, alt = None, 0
    t0 = 0.0
    while t0 < total:
        a = t0 / src['spq'] * ticks_per_step
        b = a + ticks_per_step / 2.0
        cur = frozenset(p % 12 for (on, off, p) in spans if on < b and off > a)
        if cur:
            if prev_set is not None and cur != prev_set:
                alt += 1
            prev_set = cur
        t0 += h
    return changes, alt


def pedal_gate(n, changes_s, lines):
    gate = np.ones(n)
    a_len = max(1, int(PEDAL_MS * 1e-3 * SR))
    u_len = max(1, int(6e-3 * SR))
    for t in changes_s:
        i = int(round(t * SR))
        a0 = max(0, i - a_len)
        if a0 < i:
            ramp = np.linspace(1.0, PEDAL_FLOOR, i - a0)
            np.minimum(gate[a0:i], ramp, out=gate[a0:i])
        j = min(n, i + u_len)
        if j > i:
            gate[i:j] = np.minimum(gate[i:j], np.linspace(PEDAL_FLOOR, 1.0, j - i))
    say(lines, "  pedal: %d harmony changes, gate floor %.2f over %.0f ms"
        % (len(changes_s), PEDAL_FLOOR, PEDAL_MS))
    if not changes_s:
        say(lines, "  NOTE no harmony changes found -- the pedal never closes, "
                   "which on a sustained texture is mud")
    return gate


# ============================== the piano ====================================

def piano_note(pitch, dur_s, vel, seed):
    """One struck note.

    Returns a mono array long enough to contain the natural decay, which is
    usually LONGER than the written duration -- held-pedal piano.  Cutting it at
    the written duration instead is what makes a MIDI render sound like a
    metronome with pitch.
    """
    f0 = midi_hz(pitch)
    dec = DECAY_C4 * 2.0 ** ((60 - pitch) / DECAY_SEMIS)
    # A note runs until the SLOWEST partial is inaudible, or until TAIL_MAX_S,
    # whichever comes first.  Both bounds are needed: the first is the honest
    # end of the sound, the second is because a D2's fundamental would take
    # 20 s to reach -60 dB and the piece is 92 s long.
    n = int(round(min(SILENT_TC * dec, max(dur_s + 0.25, TAIL_MAX_S)) * SR))
    n = max(n, int(0.05 * SR))
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    for k in range(1, PARTIAL_MAX + 1):
        f = f0 * k * math.sqrt(1.0 + INHARM * k * k)
        if f >= SR * 0.45:
            break
        dk = dec / (1.0 + PARTIAL_DAMP * (k - 1))
        # Only as far as THIS partial is audible.  The high partials die
        # quickly, so on a bass note this is where nearly all the saving is:
        # partial 18 of a D2 is silent after 1.9 s while the whole note runs 5.
        m = min(n, max(2, int(round(SILENT_TC * dk * SR))))
        tt = t[:m]
        ph = rng.uniform(0.0, 2.0 * math.pi)     # in-phase partials sum to an
        out[:m] += ((k ** -PARTIAL_FALL) * np.exp(-tt / dk)
                    * np.sin(2 * math.pi * f * tt + ph))
    # Hammer: a short bright burst, louder and brighter as the note rises.
    hn = min(n, max(1, int(HAMMER_MS * 1e-3 * SR)))
    if hn > 1:
        noise = rng.standard_normal(hn)
        noise = dsp.highpass(noise, SR, HAMMER_HI * (0.5 + pitch / 127.0))
        out[:hn] += noise * HAMMER_LVL * np.exp(-np.arange(hn) / (hn / 3.0))
    # Truncation by TAIL_MAX_S is a decay, not a cut: fade the last RELEASE_S.
    rl = min(n, int(RELEASE_S * SR))
    if rl > 2 and SILENT_TC * dec > n / SR + 1e-9:
        out[n - rl:] *= np.cos(np.linspace(0.0, math.pi / 2, rl)) ** 2
    # 4 ms raised-cosine attack.  Without it the first sample of a sum of
    # partials is a step, and a step is a click.
    a = min(n, max(2, int(4e-3 * SR)))
    out[:a] *= np.sin(np.linspace(0.0, math.pi / 2, a)) ** 2
    amp = (vel / 127.0) ** VEL_CURVE
    pk = float(np.abs(out).max())
    return out * (NOTE_PEAK * amp / max(1e-9, pk))


def render_piano(src, n_bars, gate, n, lines):
    role_at = np.zeros(n_bars, dtype=object)
    for a, b, lab in sections(bar_stats(src, n_bars)[0]):
        for i in range(a, b):
            role_at[i] = lab
    # A derived arc: sparse sections sit back, full sections come forward.  This
    # is the phrasing the file does not carry (its velocity is constant per
    # track), so it is labelled derived wherever it is reported.
    role_gain = {'sparse': 0.72, 'thin': 0.85, 'full': 1.00}
    beat_s = src['spq']

    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(HUMAN_SEED)
    placed = 0
    for on, off, pitch, _ch, vel in sorted(src['notes']):
        bar = int(on / src['tpq'] / 4)
        if not (0 <= bar < n_bars):
            continue
        role = role_at[bar] or 'sparse'
        beat_in_bar = (on / src['tpq']) - bar * 4.0
        accent = 1.0 + (BEAT_ACCENT if beat_in_bar < 1e-6 else 0.0)
        gain = role_gain[role] * accent
        dur_s = tick_s(src, off - on)
        sig = piano_note(pitch, dur_s, vel, seed=int(on) * 31 + pitch)
        jitter = rng.uniform(-HUMAN_MS, HUMAN_MS) * 1e-3
        # Clamp, do not drop.  `continue` here was silently losing notes: the
        # humanisation can push an onset at tick 0 back to a negative sample
        # index, and the render that shipped reported 933 placed against the
        # file's 936.  Losing a note because of a 12 ms timing nudge is the
        # wrong trade -- the nudge is cosmetic and the note is the music.  The
        # report line below prints placed-OF-total so this cannot go quiet.
        i0 = max(0, min(n - 1, int(round((tick_s(src, on) + jitter) * SR))))
        seg = gate[i0:i0 + len(sig)]
        if seg.size:
            sig = sig[:seg.size] * seg
            # The attack guard: the damper ramp must not eat an onset.
            g = min(len(sig), max(1, int(PEDAL_GUARD_MS * 1e-3 * SR)))
            sig[:g] /= np.maximum(1e-6, gate[i0:i0 + g])
        pan = max(-1.0, min(1.0, (pitch - PAN_CENTRE) / 24.0)) * PAN_SPAN
        gl, gr = pan_gains(pitch, pan)
        j = min(n, i0 + len(sig))
        L[i0:j] += sig[:j - i0] * gain * gl
        R[i0:j] += sig[:j - i0] * gain * gr
        placed += 1
    say(lines, "  piano: %d of %d notes placed, jitter +-%.0f ms, pan %.2f span"
        % (placed, len(src['notes']), HUMAN_MS, PAN_SPAN))
    return L, R


# ============================== the arrangement ==============================
# Every layer below is derived from a measurement of the source, never from a
# taste decision: the sub doubles the note the source itself sounds lowest in
# each bar, and the pad voices the pitch classes the source itself sounds in
# each bar.  Nothing here invents a note the MIDI does not play.

def render_sub(src, n_bars, lows, n, lines):
    beat_s = src['spq']
    out = np.zeros(n)
    voiced = 0
    for b in range(n_bars):
        if lows[b] is None:
            continue
        f = max(28.0, midi_hz(lows[b]) / 2.0)
        dur = 4 * beat_s
        sig = dsp.sine(f, dur + 0.5, SR)
        sig *= dsp.env(dur + 0.5, SR, attack=0.20, decay=dur + 0.3, sustain=0.0,
                       release=0.45, curve=1.4)
        i0 = int(round(b * dur * SR))
        j = min(n, i0 + len(sig))
        if j > i0:
            out[i0:j] += sig[:j - i0]
            voiced += 1
    say(lines, "  sub: %d bars voiced from the lowest sounding note (%.1f..%.1f Hz)"
        % (voiced, min(v for v in [midi_hz(x) / 2 for x in lows if x] or [0]),
           max(v for v in [midi_hz(x) / 2 for x in lows if x] or [0])))
    return out


def render_pad(src, n_bars, pcs, n, lines):
    beat_s = src['spq']
    out = np.zeros(n)
    used = set()
    for b in range(n_bars):
        if not pcs[b]:
            continue
        freqs = []
        for pc in sorted(pcs[b]):
            for octv in (3, 4):
                f = midi_hz(12 * (octv + 1) + pc)
                if 160.0 <= f <= 700.0:
                    freqs.append(f)
                    break
        if not freqs:
            continue
        used |= pcs[b]
        dur = 4 * beat_s
        sig = dsp.pad_chord(freqs, dur + 0.8, SR, attack=1.1, seed=100 + b)
        i0 = int(round(b * dur * SR))
        j = min(n, i0 + len(sig))
        if j > i0:
            out[i0:j] += sig[:j - i0]
    say(lines, "  pad: %d of 12 pitch classes voiced from the bars themselves"
        % len(used))
    return out


def render_marks(src, n_bars, n, lines):
    """One soft impact where the measured sections change.  Not per bar: a hit
    every 4 s under a 60 bpm piano is a drum machine, and the source is not
    giving any reason to add one."""
    counts = bar_stats(src, n_bars)[0]
    bounds = [a for (a, _b, _l) in sections(counts)[1:]]
    out = np.zeros(n)
    for b in bounds:
        sig = ms.impact(f_hi=88.0, f_lo=34.0, tau=0.08, dur=2.8, seed=200 + b)
        i0 = int(round(b * 4 * src['spq'] * SR))
        j = min(n, i0 + len(sig))
        if j > i0:
            out[i0:j] += sig[:j - i0]
    say(lines, "  marks: %d impacts at measured boundaries %s" % (len(bounds), bounds))
    return out


# ============================== master =======================================

def frame_rms(x, ms_win=50.0):
    w = max(1, int(ms_win * 1e-3 * SR))
    n = len(x) // w
    if n < 1:
        return np.array([dsp.rms_db(x)])
    f = x[:n * w].reshape(n, w)
    return 20.0 * np.log10(np.maximum(1e-9, np.sqrt((f ** 2).mean(axis=1))))


def master(L, R, lines):
    """Own master, not make_song.master.

    That one targets ReactorShift's octave profile -- it is a curve fitted to
    another finished piece, and running it here would drag this mix toward a
    song it has nothing to do with.  This one does the two things that are
    actually required: put the loudness at a stated target, and stop the peaks
    before the encoders do it for us.

    The loop is not decoration -- it is the fix for a real defect.  The first
    version normalised to the target and THEN took a headroom scale off the
    peaks, so the delivered file measured -22.01 dB against a -16.00 dB target:
    exactly the size of the headroom scale, applied after the number it was
    supposed to satisfy.  A gain you apply before a peak-limiting pass is not
    the gain that reaches the file, because the pass takes some back.  So the
    target is a FIXED POINT here: normalise, limit, measure, repeat until the
    measurement lands, and print the limiter's own reduction so the amount of
    squashing needed to get there is visible rather than implied.
    """
    L = dsp.highpass(L, SR, 24.0)
    R = dsp.highpass(R, SR, 24.0)
    L = dsp.compress(L, SR, BUS_COMP_THRESH_DB, BUS_COMP_RATIO, 140.0)
    R = dsp.compress(R, SR, BUS_COMP_THRESH_DB, BUS_COMP_RATIO, 140.0)

    want = 10.0 ** (TARGET_RMS_DB / 20.0)
    peak_ceil = 10.0 ** (PRE_CEIL_DB / 20.0)
    for it in range(4):
        # Parenthesise the mono SUM, not just its square.  `0.5 * (L+R)**2` is
        # `0.5 * ((L+R)**2)`, which is sqrt(2) above the mono rms -- and it does
        # not raise, it just makes every pass land 3.01 dB under the target
        # while the printed gain claims otherwise (the tell was pass 2 reporting
        # gain 1.0000 and still measuring -22.01 against a -19.00 target).
        cur = float(np.sqrt(((0.5 * (L + R)) ** 2).mean()))
        k = want / max(1e-12, cur)
        L, R = L * k, R * k
        pk = max(float(np.abs(L).max()), float(np.abs(R).max()))
        pre = min(1.0, peak_ceil / max(1e-12, pk))
        L, R = L * pre, R * pre
        lin, rin = L.copy(), R.copy()
        L, R = dsp.limiter_stereo(L, R, SR, CEIL_DB, 8.0, 60.0)
        got = dsp.rms_db(0.5 * (L + R))
        # How far the limiter pulled the loudest moment back down.  Peak gain
        # reduction is the honest number here: it says "the loudest note lost
        # this much", which is what a listener hears as squashing.
        worst = max(float(np.abs(lin - L).max()), float(np.abs(rin - R).max()))
        say(lines, "  pass %d: gain %.4f  headroom %.4f  rms %.2f dB"
                   "  limiter peak reduction %.4f"
            % (it + 1, k, pre, got, worst))
        if abs(got - TARGET_RMS_DB) <= 0.25:
            break
    return L, R


# ============================== deliver ======================================

def write_wav(path, L, R):
    x = np.clip(np.stack([L, R], axis=1), -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def encode(wav_path, out_dir, lines):
    """Own encoder -- make_song.encode names its output from make_song's own
    NAME, so calling it here would quietly overwrite ReactorShift's files with
    this track.  Same settings as the other two tools."""
    made = []
    for ext, args in (("ogg", ["-c:a", "libvorbis", "-q:a", "6"]),
                      ("mp3", ["-c:a", "libmp3lame", "-b:a", "192k"])):
        out = os.path.join(out_dir, "%s.%s" % (NAME, ext))
        r = subprocess.run([ms.FFMPEG, "-y", "-v", "error", "-i", wav_path]
                           + args + [out], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        if r.returncode != 0:
            raise RuntimeError("ffmpeg %s failed: %s"
                               % (ext, r.stderr.decode("utf-8", "replace")))
        say(lines, "  wrote %s (%d B)" % (os.path.basename(out), os.path.getsize(out)))
        made.append(out)
    return made


def md5_of(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ============================== the check ====================================
# THE PLAN WAS A CHROMA TEST AND THE CHROMA TEST DOES NOT WORK HERE.
#
# The source uses only 9 of the 12 pitch classes, so a render of it should too,
# and the same instrument proved the operator's MIDI is not the recording
# (DECISIONS 461).  Run in this direction it came back r = 0.30 on a 4-bar
# render with four pitch classes in the audio that the source never plays --
# C at 8.3% against a source that never touches it.  That is not a bad render:
# it is the instrument.  On the RECORDING the test was sharp because the signal
# was a piano and nothing else.  Here I have added 936 hammer transients, a
# 3.2 s reverb and a noise impact, all broadband, and broadband energy lands in
# every one of the 12 classes at once.  A histogram over pitch classes can only
# see what the noise floor lets it see, so the same ruler is sharp on one signal
# and blunt on another.  (Weighting the source by COUNT rather than by duration
# does raise it to r = 0.74 -- a piano's spectrum follows its onsets, not its
# written durations -- but 0.74 is still not a check, and no floor-subtraction
# trick recovered the zeros.)
#
# So the strong check is a POSITIVE one, at the level the claim is actually
# made: the notes.  For each onset the MIDI states, the delivered audio must
# have a spectral peak at that note's fundamental frequency.  That is robust to
# a broadband floor by construction -- it asks for a peak, and noise does not
# produce peaks.  `r` is still printed, with the caveat, because it is a real
# number and hiding it would make the failure invisible.

CHROMA_BAND = (300.0, 3000.0)   # measured on the RECORDING, not on this render:
                                # there the four strongest classes come back
                                # exactly right (r 0.894) and over the full band
                                # they do not (r 0.738), because the hammer and
                                # reverb dominate the octaves above it.  The
                                # four-strongest claim does NOT survive the move
                                # to a synthetic voice (see key_rotation), which
                                # is why the check below is the rotation test and
                                # the top-4 is only printed.


def band_chroma(mono, n=4096, hop=1024, band=CHROMA_BAND):
    """Pitch-class share inside a frequency band.

    The full-spectrum version of this is nearly flat: 936 hammer transients and
    a 3.2 s reverb are broadband and land in all twelve classes at once.  The
    band where the piano's fundamentals and first partials live is what puts the
    notes back on top of the floor.
    """
    S = analyze.stft(mono, n=n, hop=hop)
    fr = np.fft.rfftfreq(n, 1.0 / SR)
    keep = (fr >= band[0]) & (fr <= band[1])
    M, f = S[keep, :], fr[keep]
    pc = analyze.hz_to_pc(f)
    C = np.zeros((12, M.shape[1]))
    for p in range(12):
        rows = pc == p
        if rows.any():
            C[p] = M[rows].sum(axis=0)
    v = C.mean(axis=1)
    return v / max(1e-12, v.sum())


def key_rotation(au, ref):
    """Which transposition of the source is this audio in?

    The top-4 rank test this replaces was a RANK on numbers that are not ranks.
    The reference counts every note once; the measurement is an FFT restricted
    to CHROMA_BAND, where a high note shows its fundamental and a low one shows
    only harmonics -- so the band couples weight to register, and the ordering
    is a fact about the VOICE, not about the notes.  (The band was tuned to come
    out right on the RECORDING; on this synthetic voice it does not, and the
    measured 12.8% of the audio's chroma sitting on the three classes the source
    never plays is the same effect, not a wrong note.)

    Asking which of the twelve rotations fits best is the same measurement made
    properly, because it has a null -- the other eleven rotations -- and it
    answers the question that matters: is the render in the source's key, or has
    something transposed it?  Measured on the delivered ogg: zero wins at
    r +0.813 while the next best rotation scores +0.508.
    """
    best = None
    for s in range(12):
        rr = float(np.corrcoef(au, np.roll(ref, s))[0, 1])
        if best is None or rr > best[1]:
            best = ((s if s <= 6 else s - 12), rr)
    return best


def onset_timing(src, mono, lines, hop=512, n=2048):
    """Do the render's events sit where the MIDI says they do?

    Two limits are MEASURED here, and the first version of this check walked
    straight into both.

    (1) The search window.  Every onset in this file lands on a sixteenth -- 250
    ms, 21.5 frames at this hop -- so the correlation is a COMB with a tooth
    every 21.5 frames, and the teeth are all the same height: measured peaks at
    +19, -24, +41 and -46 frames scored 0.240, 0.224, 0.224 and 0.215, while the
    alignment the physics actually predicts sits at -2 frames scoring 0.215.
    Taking the argmax over a wide window therefore reports whichever ALIAS won
    the coin toss -- which is what shipped: "lag +19 frames (221 ms)", one
    sixteenth of nothing.  A maximum over aliases is not a measurement, so the
    window is half a grid wide, narrow enough that no alias is inside it, and the
    nearest alias is printed beside the answer so its exclusion is visible.

    (2) Where the answer should be.  An STFT frame is n/hop wide, so it only
    begins to contain an onset n/(2*hop) frames after the onset -- -2 frames at
    these settings, -23 ms.  That is a PREDICTION, and the check tests it
    (|lag - predicted| <= 2.5) instead of merely excusing a lag: a render with a
    real 100 ms error would put the peak 8.6 frames out and fail.

    The control is unchanged and still what makes the number mean something --
    the identical train rotated half the piece away, scored in the same window.
    """
    S = analyze.stft(mono, n=n, hop=hop)
    d = np.maximum(0.0, np.diff(S, axis=1)).sum(axis=0)
    d = d - d.mean()
    frames = d.size
    train = np.zeros(frames)
    for on, _off, _p, _c, _v in src['notes']:
        i = int(round(tick_s(src, on) * SR / hop))
        if 0 <= i < frames:
            train[i] = 1.0
    train = train - train.mean()

    cc = np.correlate(d, train, 'full') / (np.std(d) * np.std(train) * frames + 1e-12)
    c = len(cc) // 2

    grid_fr = tick_s(src, src['tpq'] / 4.0) * SR / hop      # the sixteenth, in frames
    half = max(2, int(round(grid_fr / 2.0)))
    pred = -n / (2.0 * hop)

    def best(ref):
        seg = cc if ref is train else (
            np.correlate(d, ref, 'full')
            / (np.std(d) * np.std(ref) * frames + 1e-12))
        seg = seg[c - half:c + half + 1]
        j = int(np.argmax(seg)) - half
        return float(seg.max()), j

    peak, lag = best(train)
    ctrl, _ = best(np.roll(train, frames // 2))
    ratio = peak / max(1e-9, abs(ctrl))
    # The alias, measured as a TOOTH and not as the grid line: the teeth sit at
    # +19 and -24 frames, not at exactly +/-21.5, so sampling the nominal grid
    # position reads 0.078 and makes the exclusion look free when the real tooth
    # is 0.240 against the aligned peak's 0.215.  It is not free -- on the
    # correlation alone the two are indistinguishable, and that is precisely why
    # the window below is narrow and the lag is tested against the physics.
    a = max(1, int(round(grid_fr)))
    tol = max(1, int(round(0.2 * grid_fr)))
    teeth = [float(cc[c + s * k * a - tol:c + s * k * a + tol + 1].max())
             for s in (1, -1) for k in (1, 2)]
    alias = max(teeth)
    lines.append("     onset timing: r %+.3f at lag %+d frames (%.0f ms), predicted"
                 " %+.1f (window centring); control (train rotated half-way)"
                 " %+.3f -> ratio %.1f"
                 % (peak, lag, lag * 1000.0 * hop / SR, pred, ctrl, ratio))
    lines.append("       the search is half a grid wide (%.1f frames, a sixteenth"
                 " = %.1f) because the source's onsets are quantised to it: the"
                 " nearest alias scores %+.3f, so a wider window would report"
                 " a tooth at random"
                 % (half, grid_fr, alias))
    return peak, lag, ratio, pred, alias


def first_onset(src, mono, lines):
    """Where does the audio actually start?

    The absolute landmark the correlation above cannot supply.  A uniform shift
    by a whole sixteenth is invisible to a correlation on a sixteenth grid --
    that is exactly what the comb shows -- but it is not invisible here: the
    piece's first note is at tick 0, the renderer places it at sample 0, so the
    file must begin with an attack rather than a quarter-second of silence.
    """
    w = int(round(0.010 * SR))
    k = mono[:len(mono) // w * w].reshape(-1, w)
    e = np.sqrt((k ** 2).mean(axis=1))
    hot = e > 0.05 * float(e.max())
    idx = int(np.argmax(hot)) if hot.any() else -1
    ms = -1.0 if idx < 0 else idx * w * 1000.0 / SR
    first_tick = min(x[0] for x in src['notes'])
    lines.append("     first onset in the audio: %s; the source's first note is at"
                 " tick %d (%.0f ms)"
                 % ("none found" if idx < 0 else "%.0f ms" % ms,
                    first_tick, 1000.0 * tick_s(src, first_tick)))
    return ms, 1000.0 * tick_s(src, first_tick)


def check_files(src, lines):
    ok, bad = 0, []
    tpq = src['tpq']
    # count-weighted, for the reason in the header above: a piano's chroma
    # follows its onsets, not its written durations
    src_chroma = mgrid.chroma(src['notes'], 'count')
    absent = sorted([mgrid.NAMES[k] for k in range(12) if src_chroma[k] <= 1e-9])

    for ext in ("ogg", "mp3"):
        p = os.path.join(ASSETS, "%s.%s" % (NAME, ext))
        if not os.path.exists(p):
            bad.append("%s missing" % ext)
            continue
        x = analyze.decode(p, SR, 2)
        mono = 0.5 * (x[0] + x[1])
        dur = mono.size / SR
        pk = float(np.abs(x).max())
        rms = dsp.rms_db(mono)
        side = 0.5 * (x[0] - x[1])
        sm = float(np.sqrt((side ** 2).mean()) / max(1e-12, np.sqrt((mono ** 2).mean())))
        corr = float(np.corrcoef(x[0], x[1])[0, 1])

        au = band_chroma(mono.astype(np.float64))
        r = float(np.corrcoef(au, src_chroma)[0, 1])
        rot, rot_r = key_rotation(au, src_chroma)
        top4 = sorted([mgrid.NAMES[k] for k in
                       sorted(range(12), key=lambda k: -au[k])[:4]])
        want4 = sorted([mgrid.NAMES[k] for k in
                        sorted(range(12), key=lambda k: -src_chroma[k])[:4]])

        say(lines, "  -- %s --" % ext)
        say(lines, "     %.3f s  peak %.4f  rms %+.2f dB  side/mid %.3f  corr %+.3f"
            % (dur, pk, rms, sm, corr))
        say(lines, "     chroma %g-%g Hz vs the count-weighted source: r %+.3f"
            % (CHROMA_BAND[0], CHROMA_BAND[1], r))
        say(lines, "     best-fitting transposition of the source: %+d semitones"
                   " at r %+.3f (zero rotation scores %+.3f)"
            % (rot, rot_r, r))
        say(lines, "     four strongest classes: audio %s / source %s -- PRINTED,"
                   " not checked: the band weights a high note by its fundamental"
                   " and a low one by its harmonics, so this ordering is a fact"
                   " about the voice"
            % (', '.join(top4), ', '.join(want4)))
        say(lines, "     (the source leaves %s empty; the audio does NOT show that"
                   " -- its own hammer and reverb fill every class, so the"
                   " emptiness is not testable on the delivered file)"
            % ', '.join(absent))
        peak, lag, ratio, pred, alias = onset_timing(
            src, mono.astype(np.float64), lines)
        fms, fsrc = first_onset(src, mono.astype(np.float64), lines)

        checks = [
            ("duration", abs(dur - EXPECT_S) < 0.20,
             "%.3f s vs %.3f expected (piece + %.1f s ring-out)"
             % (dur, EXPECT_S, SOLO_TAIL_S)),
            ("peak", pk <= 1.0, "%.4f" % pk),
            ("loudness", abs(rms - TARGET_RMS_DB) < 2.0,
             "%+.2f dB vs %+.2f target" % (rms, TARGET_RMS_DB)),
            ("the source's key is the best fit", rot == 0 and rot_r > 0.75,
             "best %+d semitones at r %+.3f" % (rot, rot_r)),
            ("chroma matches the source", r > 0.75, "r %+.3f" % r),
            ("events sit where the MIDI says",
             peak > 0.15 and abs(lag - pred) <= 2.5 and ratio > 3.0,
             "r %+.3f lag %+d fr (predicted %+.1f), control ratio %.1f"
             % (peak, lag, pred, ratio)),
            ("the audio starts with the piece",
             fms >= 0 and fms < 60.0,
             "first onset %.0f ms, source's first note %.0f ms" % (fms, fsrc)),
            ("mono compatible", sm < 0.35, "side/mid %.3f" % sm),
            ("no polarity flip", corr > -0.2, "corr %+.3f" % corr),
        ]
        steps = np.abs(np.diff(mono))
        mx = float(steps.max())
        checks.append(("no click", mx < 0.85, "max step %.4f" % mx))
        for name, good, detail in checks:
            say(lines, "       [%s] %-28s %s" % ("ok" if good else "FAIL", name, detail))
            if good:
                ok += 1
            else:
                bad.append("%s: %s (%s)" % (ext, name, detail))
    say(lines, "  %d ok, %d failed" % (ok, len(bad)))
    for b in bad:
        say(lines, "    FAIL %s" % b)
    return bad


EXPECT_S = 0.0      # filled in by main() from the source's own length


# ============================== pipeline =====================================

def main(argv):
    global EXPECT_S
    ap = argparse.ArgumentParser(description="render a MIDI into a piece of music")
    ap.add_argument("--mid", help="source .mid (default: the only one in asstes/music)")
    ap.add_argument("--probe", action="store_true", help="measure and print the plan only")
    ap.add_argument("--check", action="store_true", help="re-measure the delivered files")
    ap.add_argument("--bars", type=float, help="render only this many bars (dry run)")
    args = ap.parse_args(argv[1:])

    lines = []
    t0 = time.time()
    src_path = find_source(args.mid)
    src = load_source(src_path)
    # Where this run's report goes.  Only a full render or a --check owns the
    # delivered name; --probe and --bars describe something that is not the
    # deliverable and go to out/.
    if args.probe or args.bars:
        os.makedirs(OUTDIR, exist_ok=True)
        report_path = os.path.join(OUTDIR, "%s_probe.report.txt" % NAME)
    else:
        report_path = REPORT
    if args.bars:
        # A dry run: everything downstream reads src['notes'], so trimming here
        # exercises the real pipeline on a prefix instead of a special case.
        cut = int(round(args.bars)) * 4 * src['tpq']
        src['notes'] = [n for n in src['notes'] if n[0] < cut]
        if not src['notes']:
            sys.exit("--bars %g leaves no notes" % args.bars)
    notes, tpq = src['notes'], src['tpq']
    end_tick = max(n[1] for n in notes)
    n_bars = int(math.ceil(end_tick / tpq / 4.0))
    total_s = n_bars * 4 * src['spq']
    EXPECT_S = total_s + SOLO_TAIL_S

    say(lines, "== %s ==" % NAME)
    say(lines, "  source  %s" % os.path.basename(src_path))
    say(lines, "  %d bytes  %d notes  %d staves  %.4f bpm  %.2f bars  %.2f s"
        % (os.path.getsize(src_path), len(notes), src['mid']['ntrks'],
           src['bpm'], n_bars, total_s))

    if args.check:
        say(lines, "")
        say(lines, "== check (files on disk) ==")
        bad = check_files(src, lines)
        # Print as well as write.  The first version of this branch only wrote
        # the report, so `--check` was silent on the console and looked like a
        # crash rather than a check that found something.
        write_report(lines, report_path)
        print_report_on_stdout(lines)
        return 1 if bad else 0

    counts, lows, pcs = bar_stats(src, n_bars)
    segs = sections(counts)
    say(lines, "")
    say(lines, "== structure (measured from the note counts per bar) ==")
    for a, b, lab in segs:
        say(lines, "  bars %5.2f..%-5.2f  %-6s  %d..%d notes/bar"
            % (a, b, lab, min(counts[a:b]), max(counts[a:b])))
    say(lines, "  notes per bar: %s" % counts)

    changes, alt = sounding_changes(src, lines)
    say(lines, "")
    say(lines, "== harmony ==")
    pcs_all = sorted(set().union(*pcs)) if any(pcs) else []
    say(lines, "  pitch classes sounding: %s (%d of 12)"
        % (', '.join(mgrid.NAMES[k] for k in pcs_all), len(pcs_all)))
    say(lines, "  pedal rule: bass root -> %d changes; the sounding-set rule "
               "would give %d (rejected)" % (len(changes), alt))

    if args.probe:
        gate = pedal_gate(int(total_s * SR), changes, lines)
        write_report(lines, report_path)
        print_report_on_stdout(lines)
        return 0

    n = int(round((total_s + SOLO_TAIL_S) * SR))
    gate = pedal_gate(n, changes, lines)

    say(lines, "")
    say(lines, "== render ==")
    pl, pr = render_piano(src, n_bars, gate, n, lines)
    sub = render_sub(src, n_bars, lows, n, lines)
    pad = render_pad(src, n_bars, pcs, n, lines)
    marks = render_marks(src, n_bars, n, lines)

    piano_rms = float(np.sqrt(((0.5 * (pl + pr)) ** 2).mean()))
    sub = bus_at(sub, piano_rms, SUB_DB)
    pad = bus_at(pad, piano_rms, PAD_DB)
    mpk = float(np.abs(marks).max())
    if mpk > 1e-12:
        marks = marks * (MARK_PEAK / mpk)

    for nm, sig, rel in (("piano", 0.5 * (pl + pr), 0.0), ("sub", sub, SUB_DB),
                         ("pad", pad, PAD_DB)):
        say(lines, "  %-6s rms %+7.2f dB (%5.1f vs piano)  peak %.4f"
            % (nm, dsp.rms_db(sig), rel, float(np.abs(sig).max())))
    say(lines, "  %-6s peak %.4f -> %.2f (set by PEAK, not RMS: an impact's rms"
               " is a small fraction of its peak)"
        % ("marks", mpk, MARK_PEAK))

    wet_l = dsp.comb_reverb(pl + pad, SR, rt60=REV_RT60, predelay_ms=REV_PREDELAY_MS, seed=11)
    wet_r = dsp.comb_reverb(pr + pad, SR, rt60=REV_RT60, predelay_ms=REV_PREDELAY_MS, seed=12)
    L = np.zeros(max(n, len(wet_l)))
    R = np.zeros(max(n, len(wet_r)))
    for buf, a in ((L, pl), (R, pr)):
        buf[:len(a)] += a
    for buf, a in ((L, sub), (R, sub), (L, marks), (R, marks)):
        buf[:len(a)] += a
    L[:len(wet_l)] += wet_l * REV_AMT
    R[:len(wet_r)] += wet_r * REV_AMT

    # Trim to a stated length.  comb_reverb's wet tail runs on past the buffer
    # until its own rt60 dies, so the first delivered file came out 3.704 s
    # longer than the piece and failed its own duration check -- the length was
    # wherever the tail happened to end, which is not a length anybody chose.
    # The cut lands SOLO_TAIL_S after the last note, where the tail is around
    # -60 dB, and a short cosine fade makes the cut a fade instead of a step.
    tail_lost = (L.size - n) / float(SR)
    L, R = L[:n].copy(), R[:n].copy()
    f = int(round(0.15 * SR))
    if 1 < f < n:
        w = 0.5 * (1.0 + np.cos(np.linspace(0.0, math.pi, f)))
        L[-f:] *= w
        R[-f:] *= w
    say(lines, "  reverb rt60 %.2f s at %.2f send; trimmed to %.3f s"
        " (%.3f s of tail discarded, faded)"
        % (REV_RT60, REV_AMT, n / float(SR), max(0.0, tail_lost)))

    L, R = master(L, R, lines)
    os.makedirs(OUTDIR, exist_ok=True)
    out_wav = os.path.join(OUTDIR, "%s%s.wav" % (NAME, "_dryrun" if args.bars else ""))
    write_wav(out_wav, L, R)
    say(lines, "  wav %s (%d B)" % (out_wav, os.path.getsize(out_wav)))
    if args.bars:
        # A prefix is a timing and level probe, not a deliverable: encoding it
        # to asstes/music would leave a 4-bar file under the finished track's
        # name, which is the kind of thing that gets shipped by accident.
        say(lines, "  dry run (first %g bars) -- not encoded, not checked" % args.bars)
        say(lines, "  total %.1f s" % (time.time() - t0))
        write_report(lines, report_path)
        print_report_on_stdout(lines)
        return 0
    encode(out_wav, ASSETS, lines)

    say(lines, "")
    say(lines, "== check (files on disk) ==")
    bad = check_files(src, lines)
    say(lines, "  total %.1f s" % (time.time() - t0))
    write_report(lines, report_path)
    print_report_on_stdout(lines)
    return 1 if bad else 0


def print_report_on_stdout(lines):
    # UTF-8 through the binary buffer: the console is GBK and a non-ASCII path
    # or track name would kill the run at the very last step.
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))


def write_report(lines, path=None):
    # A dry run must not land on the delivered name.  A 4-bar prefix written to
    # asstes/music/<NAME>.report.txt looks exactly like the finished report and
    # the numbers in it are the prefix's -- same trap as the .wav above.
    with open(path or REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
