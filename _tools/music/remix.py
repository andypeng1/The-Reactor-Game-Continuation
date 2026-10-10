"""Remix `asstes/music/ReactorStartup.mp3` -- the reference recording itself, re-arranged.

WHAT THIS IS, AND HOW IT DIFFERS FROM make_song.py
    `make_song.py` measured the reference and then wrote an ORIGINAL track to
    that measurement; the reference's notes are not in its output at all.  This
    tool does the opposite.  The reference *is* the body of the piece here -- its
    melody, harmony and texture are what you hear -- and everything this file
    writes sits on top of it: kick, clap, hats, sub, pads, risers, ducking and
    filtering.  That is what "remix" means, and it is the one form where being
    unable to hear matters least, because the parts that have to sound good are
    the parts I did not write.

WHAT I THEREFORE DID NOT HAVE TO INVENT, AND WHAT I STILL HAVE TO CHECK
    Rhythm is the half that *can* be checked without ears: either the kick lands
    on the reference's own onsets or it does not, and that is a number.  So the
    grid below is measured (tempo, beat phase, bar phase) and then the checks at
    the end measure the result -- grid gain over a random phase, the distance
    from every kick to the nearest low-band onset in the reference, the octave
    profile against the reference's, and the peak step against the reference's
    peak step (a click is a step nobody wrote).  What cannot be checked is
    whether it sounds good.  That judgement is the operator's; see PROGRESS.

THE ONE THING THAT MUST NOT GO WRONG QUIETLY
    The bar phase ("which of the four beats is the one") is a choice among four
    candidates whose scores are close, and picking the wrong one moves the whole
    drum kit by one beat -- which SOUNDS fine on its own and is wrong against the
    music (CLAUDE.md 0.20: the boundary lands on the data and only half is
    wrong).  The probe prints the margin between the best and second-best bar
    phase for exactly that reason; a small margin is a finding, not a detail.

Requires ffmpeg (D:\\Bot\\ffmpeg\\bin) and numpy.  ASCII output only -- the
console here is GBK (CLAUDE.md, console codec).

Usage:
    python _tools/music/remix.py --probe     # grid + sections only, no render
    python _tools/music/remix.py             # render, master, encode, check
    python _tools/music/remix.py --check     # re-check the files on disk
"""

import argparse
import hashlib
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "asstes", "music")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze                                            # noqa: E402
import dsp                                                # noqa: E402
import make_song as ms                                    # noqa: E402

SR = 44100
NAME = "ReactorStartup_Remix"
REF = os.path.join(ASSETS, "ReactorStartup.mp3")
OUTDIR = os.path.join(HERE, "out")
REPORT = os.path.join(ASSETS, NAME + ".report.txt")

# make_song's helpers (`add`, `impact`, `klaxon`, `bass_note`) close over that
# module's own SR.  Every one of them would silently land at the wrong TIME if
# the two modules disagreed, so the agreement is asserted rather than assumed.
assert ms.SR == SR, "make_song.SR changed: its instruments no longer fit this grid"

# ============================== the grid ==============================
# Tempo comes from analyze.py's autocorrelation (92.25 bpm, strength 0.700 on the
# reference).  The report searched it in 0.25 bpm steps, which is 0.27% -- over a
# 264 s track that is 0.7 s of drift, so the coarse answer is refined here by a
# fine search around it against the same grid score the phase uses.
BPM_LO, BPM_HI = 80.0, 105.0
BPM_FINE_STEPS = 121       # +-1.5 bpm in 0.025 steps
NPHASE = 480               # phase candidates per beat (86 fps / 480 = 0.18 ms)
BAR_DB_MIN = 1.0           # downbeat must clear the mean beat by this much to count
OUTRO_DB = 1.0             # the tail must be this much quieter than the median to count
DYNAMIC_LO, DYNAMIC_HI = 0.60, 1.15   # how far the kit may follow the reference's level

# The reference's own key: D minor r=+0.693 on top of F major +0.685 (a relative
# pair, which is what one would expect from a piece that spends its time on the
# shared notes).  The added bass pedals D2 -- the LOWEST candidate, because a
# wrong root in the bass is the one mistake a low-end check can still catch.
D2 = 73.416

# ============================== levels ==============================
# The reference decodes with a peak of 1.1498 -- above full scale -- so it cannot
# go into a mix at unity and the added material has to be built around a trimmed
# version.  It is trimmed to just under full scale, NOT to a nice-looking -7 dB:
# at -7 the reference's RMS came out around -25 dBFS and the first render's check
# measured the reference holding only 8.9% of the track's energy, i.e. the drums
# had become the piece and the reference the garnish.  That is the opposite of
# what a remix is.
REF_PEAK_DB = -0.5
REF_HP_HZ = 62.0           # where the drums play, the reference loses its sub
REF_INTRO_HP_HZ = 220.0    # and in the intro it loses everything below that
REF_INTRO_DB = -3.5

# Kit levels are RELATIVE WEIGHTS, not absolute peaks.  The whole bus is scaled
# once, after it is summed, so that its RMS is a chosen fraction of the trimmed
# reference's -- see KIT_RMS_MULT.  An absolute peak per instrument would mean a
# different balance for every input file, and I cannot hear the result to correct
# it: this reference alone decodes 8 dB over a nominal peak.  kick = 1.0.
KICK_W = 1.00
CLAP_W = 0.50
HAT_W = 0.20
SUB_W = 0.42
PAD_W = 0.42
RISER_W = 0.42
IMPACT_W = 0.75
KLAXON_W = 0.26
# 0.85 puts the reference at 1/(1+0.85^2) = 58% of the track's energy for
# uncorrelated material, which is what "the reference is the body" means as a
# number.  The check prints the measured share so this is not self-reported.
KIT_RMS_MULT = 0.85

DUCK_MAIN = 0.16           # how far the kick pushes the reference down
DUCK_CLIMAX = 0.22
DUCK_RELEASE_S = 0.16

REV_AMT = 0.16             # drum send to the reverb bus
DLY_AMT = 0.12             # clap send to the ping-pong delay
DELAY_BEAT = 0.75          # dotted 8th at any tempo

# ============================== sections ==============================
# Where the parts change is measured; what each part DOES is chosen here.  The
# split matters: a change-point detector is allowed to say "something happened at
# bar 41", it is not allowed to say "bar 41 is the drop".
CP_WIN_BARS = 6            # bars either side of a candidate boundary
CP_MIN_GAP_BARS = 8
CP_MAX = 5
CP_THRESHOLD = 0.85        # in units of the z-scored feature distance


# ============================== small helpers ==============================

def say(lines, s):
    print(s)
    lines.append(s)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def db(x):
    return 20.0 * np.log10(max(float(x), 1e-12))


def pan(x, p):
    """Equal-power pan -> (L, R).  Written out rather than calling
    dsp.pan_mono because that function's pan convention (which end is which)
    is not something I can hear and so not something I should assume."""
    th = (float(p) + 1.0) * (np.pi / 4.0)
    return x * np.cos(th), x * np.sin(th)


# ============================== the grid ==============================

def stft_flux(mono):
    """Onset envelope (full band) and a low-band one, on analyze.py's ruler
    (n=2048, hop=512 at 44.1 kHz) so the numbers stay comparable to the
    reference's own report."""
    n, hop = 2048, 512
    S = analyze.stft(mono, n, hop)
    fps = SR / hop
    fr = np.fft.rfftfreq(n, 1.0 / SR)
    d = np.diff(S, axis=1)
    flux = np.concatenate([[0.0], np.maximum(d, 0.0).sum(axis=0)])
    dlo = np.diff(S[fr < 160.0], axis=1)
    flux_lo = np.concatenate([[0.0], np.maximum(dlo, 0.0).sum(axis=0)])
    return S, fr, flux, flux_lo, fps


def _samp(flux, start, step):
    """Linear-interpolated envelope samples at `start, start+step, ...`.
    None if the grid is degenerate or too short to mean anything."""
    n = len(flux) - 1
    if step < 2.0 or start < 0.0 or start >= n - 1:
        return None
    idx = np.arange(start, n - 1, step)
    if len(idx) < 8:
        return None
    i0 = np.floor(idx).astype(np.int64)
    frac = idx - i0
    return flux[i0] * (1.0 - frac) + flux[i0 + 1] * frac


def _comb_score(flux, beat_f, phase_f):
    """mean(on-beat) - mean(off-beat), both spanning the whole track.

    NOT the mean at beat positions, which is what this started as and which
    cannot work: shifting the phase by a whole beat drops one beat off the front
    of a finite track, and this reference's envelope climbs all the way to its
    140 s climax, so a later start scores higher for a reason that has nothing to
    do with the beat.  Measured on the first run: the four bar-phase candidates
    scored 59.3554 / 59.5056 / 59.6567 / 59.8085 -- monotonically increasing by
    0.77% in total, which is that slope and not a downbeat.  The comb's two sets
    interleave and cover the same span, so the slope cancels to first order.
    CLAUDE.md 0.21: the denominator was doing the choosing."""
    on = _samp(flux, phase_f, beat_f)
    off = _samp(flux, phase_f + 0.5 * beat_f, beat_f)
    if on is None or off is None:
        return -1.0, 0.0, 0.0
    a, b = float(on.mean()), float(off.mean())
    return a - b, a, b


def find_grid(flux, flux_lo, fps, lines):
    """(bpm, beat_phase_frames, confidence) with the evidence printed.

    The tempo candidates come from analyze.tempo on THIS flux -- the same
    function and the same flux expression analyze.py's own report used, so the
    numbers stay comparable to it rather than being a second opinion from a
    second ruler (CLAUDE.md 0.18).  Its 0.25 bpm step is 0.27%, which is 0.7 s of
    drift over 264 s, so the winner is refined here by a fine search against the
    same comb the phase uses."""
    cand = analyze.tempo(flux, fps)
    if not cand:
        raise RuntimeError("no tempo candidate: the reference has no pulse to find")
    say(lines, "  tempo candidates from the reference's report ruler:")
    for val, bpm in cand[:5]:
        say(lines, "    %7.2f bpm  strength %.3f%s"
            % (bpm, val, "   <- in window" if BPM_LO <= bpm <= BPM_HI else ""))

    # Fold octave relatives into the window: a candidate at 184.5 is the same
    # pulse as one at 92.25 and the report lists both.
    inwin = []
    for val, bpm in cand:
        for f in (1.0, 0.5, 2.0):
            if BPM_LO <= bpm * f <= BPM_HI:
                inwin.append((val, bpm * f))
                break
    if not inwin:
        raise RuntimeError("no tempo candidate in %.0f..%.0f bpm" % (BPM_LO, BPM_HI))
    coarse = inwin[0][1]
    say(lines, "  coarse    %.2f bpm (folded into the window)" % coarse)

    best = (-1e18, coarse, 0.0)
    for bpm in np.linspace(coarse - 1.5, coarse + 1.5, BPM_FINE_STEPS):
        beat_f = 60.0 / bpm * fps
        for k in range(0, NPHASE, 8):
            sc = _comb_score(flux, beat_f, k * beat_f / NPHASE)[0]
            if sc > best[0]:
                best = (sc, bpm, k * beat_f / NPHASE)
    _, bpm, _ = best
    step = (BPM_FINE_STEPS - 1) and (3.0 / (BPM_FINE_STEPS - 1))
    if min(bpm - (coarse - 1.5), (coarse + 1.5) - bpm) < step:
        say(lines, "  NOTE refined tempo sits on the edge of the +-1.5 bpm window: "
                   "the window is too narrow and this answer is not the maximum "
                   "of the score, only the maximum of the window.")

    beat_f = 60.0 / bpm * fps
    bs = (-1e18, 0.0)
    for k in range(NPHASE):
        sc, on, off = _comb_score(flux, beat_f, k * beat_f / NPHASE)
        if sc > bs[0]:
            bs = (sc, k * beat_f / NPHASE)
    score, phase_f = bs
    _, on, off = _comb_score(flux, beat_f, phase_f)
    say(lines, "  refined   %.3f bpm -- beat %.4f s, bar %.4f s" % (bpm, 60.0 / bpm, 240.0 / bpm))

    # Null: the same comb at 24 phases spread over one beat.  On-beat over
    # off-beat as a ratio is the readable form (an absolute flux level is not
    # comparable between tracks); the spread of the null says how much of it is
    # noise.
    null = []
    for k in range(24):
        sc, a, b = _comb_score(flux, beat_f, phase_f + k * beat_f / 24.0)
        if sc >= 0.0 and b > 1e-9:
            null.append(a / b)
    r = on / max(1e-9, off)
    say(lines, "  comb      on-beat/off-beat %.3fx (%.2f dB); null 24 phases "
               "%.3f..%.3f" % (r, 20 * np.log10(max(1e-9, r)),
                               float(np.min(null)), float(np.max(null))))

    # Bar phase: which of the four beats is the downbeat, scored on the LOW band
    # alone ("the one" is where the low onsets are; the full-band flux is
    # dominated by content that has nothing to do with the beat).  Every
    # candidate is scored from the SAME beat grid -- slot k versus the other
    # three -- so no candidate samples more or less of the track than another.
    m = []
    for k in range(4):
        v = _samp(flux_lo, phase_f + k * beat_f, 4.0 * beat_f)
        m.append(float(v.mean()) if v is not None else -1.0)
    if min(m) < 0.0:
        raise RuntimeError("bar grid ran off the end: %r" % (m,))
    mean_m = float(np.mean(m))
    say(lines, "  beat-slot low-band means (beats 0..3): "
        + "  ".join("%.4f" % v for v in m))
    k_best = int(np.argmax(m))
    gain_db = 20.0 * np.log10(max(1e-12, m[k_best] / max(1e-12, mean_m)))
    say(lines, "  bar phase -> beat %d, its slot %+.2f dB vs the mean beat "
               "(thresh %.1f dB)" % (k_best, gain_db, BAR_DB_MIN))
    conf = 1.0
    if gain_db < BAR_DB_MIN:
        conf = 0.0
        say(lines, "  NOTE downbeat under %.1f dB: this reference has no "
                   "measurable bar accent on the low band, so the kit's phase "
                   "within the bar is a coin toss and may sit one beat off the "
                   "music.  Checked rather than assumed -- the pattern is "
                   "written per bar either way." % BAR_DB_MIN)

    return bpm, phase_f + k_best * beat_f, conf


# ============================== sections ==============================

def bar_features(S, fr, fps, n_bars, phase_s):
    """One row per bar: level, and the mid+hi share.  Level alone cannot see the
    reference's own climax (its 140-150 s block is not louder, it is *denser* --
    the 10 s table in its report shows mid jumping 15% -> 51% there), so the
    spectral share is a feature in its own right."""
    lvl = np.zeros(n_bars)
    dense = np.zeros(n_bars)
    for b in range(n_bars):
        t0 = phase_s + b * (60.0 / BPM_LAST[0] * 4.0)
        i0 = int(round(t0 * fps))
        i1 = i0 + int(round((60.0 / BPM_LAST[0] * 4.0) * fps))
        i1 = min(i1, S.shape[1])
        i0 = min(i0, max(0, i1 - 1))
        if i1 - i0 < 2:
            lvl[b] = lvl[max(0, b - 1)]
            dense[b] = dense[max(0, b - 1)]
            continue
        sl = S[:, i0:i1]
        P = (sl ** 2).sum(axis=1)
        tot = float(P.sum()) + 1e-12
        lvl[b] = 10.0 * np.log10(tot / (i1 - i0) + 1e-12)
        dense[b] = float(P[(fr >= 250.0) & (fr < 2000.0)].sum()) / tot
    return lvl, dense


def change_points(feat, win, min_gap, max_n, thresh, lines):
    """Boundaries where a rolling before-window and after-window disagree.
    Deliberately crude and snapped to bars -- a second opinion on where the parts
    are, not a claim about the composer's intent."""
    nb = feat.shape[1]
    z = (feat - feat.mean(axis=1, keepdims=True)) / (feat.std(axis=1, keepdims=True) + 1e-9)
    cands = []
    for b in range(win, nb - win):
        a = z[:, b - win:b].mean(axis=1)
        c = z[:, b:b + win].mean(axis=1)
        cands.append((float(np.linalg.norm(a - c)), b))
    cands.sort(key=lambda t: -t[0])
    picked = []
    for sc, b in cands:
        if sc < thresh:
            break
        if any(abs(b - p) < min_gap for p in picked):
            continue
        picked.append(b)
        if len(picked) == max_n:
            break
    bounds = [0] + sorted(picked) + [nb]
    say(lines, "  boundaries (bar): " + ", ".join(str(b) for b in bounds))
    return bounds


def assign_roles(bounds, dense, lvl, lines):
    """Roles: position for the head, the reference's own numbers for the rest.

    The first segment is the intro -- it always is, and a 15 s filtered opening
    is the safe reading of one.  Everything after that is decided by measurement,
    because position alone reads this track backwards.  Its densest passage
    (bars 50-57, mid share 0.44 against 0.12-0.19 everywhere else) is also its
    QUIETEST (37.1 dB against a 41.9 dB median), and its last 88 s are its
    LOUDEST (46.7 dB).  The positional rule this started as would therefore have
    put the busiest drum pattern over the quietest music and highpassed the
    loudest 88 s of the track.

    So: the outro exists only if the tail is measurably quieter than the median
    section; the climax is the segment with the highest combined z-score of level
    AND density (density alone picks the quiet bridge); the segment right before
    it builds.  Everything else is a verse, which is what the body of this track
    is."""
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        segs.append(dict(a=a, b=b, dense=float(dense[a:b].mean()),
                         lvl=float(lvl[a:b].mean())))
    if len(segs) == 1:
        segs[0]["role"] = "main"
        say(lines, "  one segment only -- the whole track is 'main'")
        return segs
    for s in segs:
        s["role"] = None
    segs[0]["role"] = "intro"

    med = float(np.median([s["lvl"] for s in segs]))
    last = segs[-1]
    if last["role"] is None and last["lvl"] < med - OUTRO_DB:
        last["role"] = "outro"
        say(lines, "  tail %+.1f dB against the %.1f dB median level -> outro"
            % (last["lvl"] - med, med))
    else:
        say(lines, "  tail %+.1f dB against the %.1f dB median level: this "
                   "reference ENDS LOUD, so there is no outro section and the "
                   "tail keeps the main treatment (no 88 s highpass)"
            % (last["lvl"] - med, med))

    rest = [s for s in segs[1:] if s["role"] is None]
    Lv = np.array([s["lvl"] for s in rest])
    Dv = np.array([s["dense"] for s in rest])
    if len(rest) == 1:
        e = np.array([1.0])
    else:
        e = (Lv - Lv.mean()) / (Lv.std() + 1e-9) + (Dv - Dv.mean()) / (Dv.std() + 1e-9)
    k = int(np.argmax(e))
    rest[k]["role"] = "climax"
    if k > 0 and rest[k - 1]["role"] is None:
        rest[k - 1]["role"] = "build"
    for s in rest:
        if s["role"] is None:
            s["role"] = "main"
    say(lines, "  energy (z level + z density) per candidate segment:")
    for s, ev in zip(rest, e):
        say(lines, "    bar %3d  %-7s  e %+5.2f   %+.1f dB, dense %.3f"
            % (s["a"], s["role"], ev, s["lvl"] - med, s["dense"]))
    return segs


# ============================== the music ==============================

BEAT = 0.0                 # filled in by main(); module-level so the helpers
BAR = 0.0                  # below can be read on their own
BPM_LAST = [0.0]


def at(bar, beat=0.0):
    return GRID_S + bar * BAR + beat * BEAT


GRID_S = 0.0


def drum_pattern(role, bar):
    """(kick beats, clap beats, hat step, hat accent stride).  Half-time feel:
    the kick sits on 1 and 3 of a four-beat bar, which against the reference's
    90.000 bpm reads as a heavy 45 bpm crawl -- the tempo of a machine under
    load, which is what this world is."""
    if role == "build":
        # The last two bars before a drop double the hats; that acceleration is
        # the whole reason a build reads as one.
        return [0.0, 2.0], [1.0, 3.0], (0.25 if bar % 2 else 0.5), 2
    if role == "climax":
        kick = [0.0, 1.5, 2.0, 3.5]
        clap = [1.0, 3.0] + ([2.75] if bar % 2 else [])
        return kick, clap, 0.25, 2
    kick = [0.0, 2.0] + ([3.5] if bar % 4 == 3 else [])
    return kick, [1.0, 3.0], 0.5, 2


def render_drums(n_bars, role_of_bar, lvl, lines):
    """Everything this file adds, on the measured grid.  Returns the stereo kit
    bus and the kick-only bus (the kick bus drives the sidechain, so it is kept
    apart) plus the per-bar level-following gain, which the duck depth needs."""
    n = int(round((GRID_S + n_bars * BAR + 8.0) * SR))
    busL = np.zeros(n)
    busR = np.zeros(n)
    kickbus = np.zeros(n)

    # Follow the reference's own level at a quarter slope.  A fixed kit level is
    # the one thing I cannot check by ear, and this reference spans 10 dB: bars
    # 50-57 sit 4.8 dB under the median while the tail is 5 dB over it.  At full
    # slope the kit would be a fader ride; at zero it crushes the quiet bridge.
    med = float(np.median(lvl))
    g_dyn = np.clip(10.0 ** ((lvl - med) / 40.0), DYNAMIC_LO, DYNAMIC_HI)
    say(lines, "  level follow: %.2f..%.2f (median bar %.1f dB)"
        % (float(g_dyn.min()), float(g_dyn.max()), med))

    k1 = dsp.kick(0.75, SR, f_lo=D2, f_hi=150.0, tau=0.040, decay=0.38)
    k2 = dsp.kick(0.75, SR, f_lo=D2 / 2.0, f_hi=150.0, tau=0.055, decay=0.55)
    clap = dsp.metal_hit(0.45, SR, f0=392.0, seed=7, bright=0.85)
    clap = clap + 0.5 * dsp.metal_hit(0.45, SR, f0=294.0, seed=9, bright=1.1)
    hat = dsp.tick(0.09, SR, seed=5, lo=6500, hi=13000)
    hat2 = dsp.tick(0.07, SR, seed=6, lo=9000, hi=15000)
    sub = ms.bass_note(D2, 1.15)

    nkick = nclap = nhat = nsub = 0
    for bar in range(n_bars):
        role = role_of_bar[bar]
        if role in ("intro", "outro"):
            continue
        kicks, claps, step, accent = drum_pattern(role, bar)
        gb = float(g_dyn[bar])
        kg = gb * (1.0 if role != "climax" else 1.12)
        for i, bt in enumerate(kicks):
            v = (k1 if (bar + i) % 3 else k2) * KICK_W * kg
            ms.add(kickbus, v, at(bar, bt))
            ms.add(busL, v, at(bar, bt))
            ms.add(busR, v, at(bar, bt))
            nkick += 1
        for i, bt in enumerate(claps):
            g = CLAP_W * gb * (0.75 if bt > 2.5 else 1.0)
            l, r = pan(clap, -0.18 if i % 2 else 0.18)
            ms.add(busL, l, at(bar, bt), g)
            ms.add(busR, r, at(bar, bt), g)
            nclap += 1
        t = 0.0
        i = 0
        while t < 4.0 - 1e-9:
            strong = (i % accent) == 0
            v = (hat if strong else hat2) * HAT_W * gb * (1.0 if strong else 0.62)
            if role == "climax":
                v = v * 1.1
            l, r = pan(v, 0.30 * (1 if i % 2 else -1))
            ms.add(busL, l, at(bar, t))
            ms.add(busR, r, at(bar, t))
            nhat += 1
            t += step
            i += 1
        # The sub pedals the root.  It is deliberately NOT panned: a sub that
        # moves between the channels is mono-incompatible, and this track's job
        # is to sit under a game mix that may be summed anywhere.
        if role == "climax":
            for j in range(4):
                ms.add(busL, sub * SUB_W * gb * 0.85, at(bar, float(j)))
                ms.add(busR, sub * SUB_W * gb * 0.85, at(bar, float(j)))
                nsub += 1
        else:
            ms.add(busL, sub * SUB_W * gb, at(bar, 0.0))
            ms.add(busR, sub * SUB_W * gb, at(bar, 0.0))
            nsub += 1

    say(lines, "  drums: %d kicks, %d claps, %d hats, %d subs over %d bars"
        % (nkick, nclap, nhat, nsub, n_bars))
    return busL, busR, kickbus, g_dyn


def render_furniture(segs, n, lines):
    """Pads at each part's start, a reversed vent into the climax, impacts on the
    seams, two klaxons at the top of the climax.  None of this is rhythmic, so
    none of it depends on the grid being right -- which is why it is the layer
    allowed to be decorative."""
    bus = np.zeros(n)
    npad = nimp = nkla = nris = 0
    for i, s in enumerate(segs):
        t = at(s["a"], 0.0)
        role = s["role"]
        g = {"intro": 0.7, "build": 1.0, "climax": 1.15, "main": 0.9}.get(role, 0.9)
        pad = dsp.pad_chord([D2 * 2, D2 * 2 * (6 / 5), D2 * 2 * (3 / 2)],
                            min(10.0, (s["b"] - s["a"]) * BAR), SR, attack=2.2, seed=i)
        ms.add(bus, pad * PAD_W * g, t)
        npad += 1
        if role in ("build", "main") and i < len(segs) - 1:
            ris = dsp.steam(6.5, SR, f_lo=250, f_hi=7000, seed=40 + i)[::-1].copy()
            ms.add(bus, ris * RISER_W, max(0.0, at(s["b"], 0.0) - 6.3))
            nris += 1
        if role in ("climax", "main") and i > 0:
            ms.add(bus, ms.impact() * IMPACT_W, t)
            nimp += 1
        if role == "climax":
            for off in (2.0, 5.0, 9.0):
                # Clamped to the segment: a klaxon 9 bars into a 8-bar climax
                # lands in the next part, which is a seam nobody asked for.
                if s["a"] + off < s["b"]:
                    ms.add(bus, ms.klaxon(2.4, rate=5.0) * KLAXON_W,
                           at(s["a"] + off))
                    nkla += 1
    say(lines, "  furniture: %d pads, %d risers, %d impacts, %d klaxons"
        % (npad, nris, nimp, nkla))
    return bus


# ============================== mix ==============================

def _step_per_bar(values, n):
    """Step a per-bar sequence into a per-sample one, with the edges held."""
    v = np.zeros(n)
    for bar, val in enumerate(values):
        i0 = max(0, min(n, int(round(at(bar, 0.0) * SR))))
        i1 = max(0, min(n, int(round(at(bar + 1, 0.0) * SR))))
        if i1 > i0:
            v[i0:i1] = val
    a = max(0, min(n, int(round(GRID_S * SR))))
    b = max(0, min(n, int(round(at(len(values), 0.0) * SR))))
    v[:a] = values[0]
    v[b:] = values[-1]
    return v


def bar_curve(role_of_bar, key, n, smooth_s):
    """A per-sample curve stepped per bar and smoothed -- the crossfade between
    sections, so the reference's filter opens over ~0.3 s instead of clicking.

    `key` is a role -> value function, or a ready per-bar array.  The second form
    is needed by the duck depth, which is a role schedule scaled by the
    reference's measured level and so is not a function of the role alone."""
    values = [key(r) for r in role_of_bar] if callable(key) else list(key)
    return dsp.smooth(_step_per_bar(values, n), int(smooth_s * SR))


def sidechain(kickbus, depth, n):
    """Gain curve from the kick's own envelope.  A boxcar follower, so the duck
    has a flat top and a smooth release; it is a production device, so its
    "wrongness" against a real attack/release compressor does not matter here."""
    e = dsp.smooth(np.abs(kickbus), int(0.012 * SR))
    e = dsp.smooth(e, int(DUCK_RELEASE_S * SR))
    e = e / max(1e-9, float(e.max()))
    return 1.0 - depth * e


def linked_compress(L, R, sr, thresh_db=-17.0, ratio=2.6, win_ms=140.0):
    """One gain from the mid, applied to both.  Two independent per-channel
    compressors would move the stereo image, which is a real defect and not a
    style: the reference's L/R correlation is +0.792 and it should stay there."""
    mid = 0.5 * (L + R)
    e = dsp.smooth(np.abs(mid), int(round(win_ms * 1e-3 * sr)))
    edb = 20.0 * np.log10(np.maximum(e, 1e-9))
    over = np.maximum(0.0, edb - thresh_db)
    g = 10.0 ** (-over * (1.0 - 1.0 / max(1.0, ratio)) / 20.0)
    return L * g, R * g


# ============================== checks ==============================

def kick_alignment(kick_times, roles, flux_lo, fps, lines):
    """Distance from every added kick to the nearest low-band onset in the
    REFERENCE.  This is the check that can actually fail: if the bar phase is
    wrong the median lands near half a beat (333 ms) instead of near zero, and
    unlike the grid gain it is measured against the music rather than against
    my own kick.

    The p90 is reported per role as well as overall, and that is not decoration.
    The first render's overall p90 was 4575 ms while its median was 26 ms, and
    an unqualified p90 like that reads as a broken grid.  It was not: this
    reference's quiet bridge (bars 50-57, 4.8 dB under the median level) has no
    strong low onsets to land on, so a kick there is far from the nearest one by
    construction.  Without the by-role split that reading cannot be told apart
    from a real misalignment."""
    f = flux_lo.copy()
    thr = float(np.percentile(f, 92.0))
    pk = []
    for i in range(1, len(f) - 1):
        if f[i] >= thr and f[i] >= f[i - 1] and f[i] > f[i + 1]:
            pk.append(i / fps)
    if not pk:
        say(lines, "  kick alignment: no reference onsets found -- NOT MEASURED")
        return
    pk = np.array(pk)
    d = np.array([float(np.min(np.abs(pk - t))) for t in kick_times])
    say(lines, "  kick -> nearest reference low onset: median %.0f ms, "
               "p90 %.0f ms (n=%d, half a beat is %.0f ms)"
        % (1000 * np.median(d), 1000 * np.percentile(d, 90), len(d), 1000 * BEAT / 2))
    roles = np.asarray(roles)
    for r in sorted(set(roles.tolist())):
        m = roles == r
        say(lines, "    %-7s median %6.0f ms  p90 %6.0f ms  (n=%d)"
            % (r, 1000 * np.median(d[m]), 1000 * np.percentile(d[m], 90), int(m.sum())))


def octave_table(x, sr, n=8192, hop=2048):
    S = analyze.stft(x, n, hop)
    fr = np.fft.rfftfreq(n, 1.0 / sr)
    P = (S ** 2).mean(axis=1)
    edges = [20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240, 20000]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (fr >= a) & (fr < b)
        out.append(float(P[m].sum()) if m.any() else 1e-30)
    return edges, out


def peak_step(x):
    """Largest single-sample step, and the 99.99th percentile of steps.  A click
    is a step nobody wrote; comparing against the reference's own steps is what
    makes the number mean something, because absolute step size is a function of
    how much high end the signal legitimately has."""
    d = np.abs(np.diff(x))
    return float(d.max()), float(np.percentile(d, 99.99))


def check_files(lines, master_L=None, master_R=None, ref=None):
    """Everything measurable about what is on disk right now."""
    for ext in (".mp3", ".ogg"):
        p = os.path.join(ASSETS, NAME + ext)
        if not os.path.exists(p):
            say(lines, "  MISSING %s" % p)
            continue
        x = analyze.decode(p, SR, 1)
        say(lines, "  %-6s %10d B  %7.3f s  peak %.4f  rms %+.2f dB  md5 %s"
            % (ext, os.path.getsize(p), len(x) / SR, float(np.abs(x).max()),
               dsp.rms_db(x), md5_of(p)[:12]))
    if master_L is None or ref is None:
        return
    mono = 0.5 * (master_L + master_R)
    e_ref = float((ref ** 2).mean())
    e_add = float(((mono - ref) ** 2).mean())
    corr = float(np.corrcoef(mono, ref)[0, 1])
    say(lines, "  reference share of energy %.1f%%   mix/ref corr %+.3f"
        % (100.0 * e_ref / (e_ref + e_add), corr))
    rm, rp = peak_step(mono)
    fm, fp = peak_step(ref)
    say(lines, "  max step  remix %.4f (p99.99 %.4f)   reference %.4f (%.4f)"
        % (rm, rp, fm, fp))
    if rm > 3.0 * fm:
        say(lines, "  NOTE max step is over 3x the reference's -- listen for a click")
    em, eo = octave_table(mono, SR)
    _, ro = octave_table(ref, SR)
    say(lines, "  octave profile, remix minus reference (dB):")
    for (a, b), x1, x2 in zip(zip(em[:-1], em[1:]), eo, ro):
        say(lines, "    %5d-%-5d  %+6.1f" % (a, b, 10 * np.log10(x1 / x2 + 1e-12)))


def write_report(lines):
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\nwrote %s" % REPORT)


def encode(wav_path, out_dir, lines):
    """Two codecs, same settings as make_song.py's chain.

    Not `make_song.encode` itself: that one names its output from its own
    module-level NAME, so calling it here would quietly overwrite ReactorShift's
    deliverables with this track's audio -- a mistake that would look like a
    successful render."""
    made = []
    for ext, args in (("ogg", ["-c:a", "libvorbis", "-q:a", "6"]),
                      ("mp3", ["-c:a", "libmp3lame", "-b:a", "192k"])):
        out = os.path.join(out_dir, "%s.%s" % (NAME, ext))
        r = subprocess.run([ms.FFMPEG, "-y", "-v", "error", "-i", wav_path]
                           + args + [out],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            raise RuntimeError("ffmpeg %s failed: %s"
                               % (ext, r.stderr.decode("utf-8", "replace")))
        say(lines, "  wrote %s (%d B)" % (os.path.basename(out), os.path.getsize(out)))
        made.append(out)
    return made


# ============================== pipeline ==============================

def main(argv):
    global BEAT, BAR, BPM_LAST, GRID_S
    ap = argparse.ArgumentParser(description="remix the reference track")
    ap.add_argument("--probe", action="store_true",
                    help="measure the grid and the sections, stop before the render")
    ap.add_argument("--check", action="store_true",
                    help="re-measure whatever is on disk and stop")
    args = ap.parse_args(argv[1:])

    lines = []
    t0 = time.time()
    say(lines, "== %s ==" % NAME)
    say(lines, "  reference %s" % REF)
    say(lines, "  %d bytes  %s" % (os.path.getsize(REF), analyze.probe(REF)))

    if args.check:
        say(lines, "")
        say(lines, "== check (files on disk) ==")
        check_files(lines)
        write_report(lines)
        return 0

    # ---- measure ---------------------------------------------------------
    st = analyze.decode(REF, SR, 2)
    ref = 0.5 * (st[0] + st[1])
    n_ref = ref.size
    say(lines, "  decoded   %d samples, %.3f s stereo, peak %.4f"
        % (n_ref, n_ref / SR, float(np.abs(st).max())))
    trim = 10.0 ** (REF_PEAK_DB / 20.0) / max(1e-9, float(np.abs(st).max()))
    say(lines, "  trim      x%.4f (%.2f dB) -- the reference peaks above full "
               "scale as decoded" % (trim, 20 * np.log10(trim)))

    S, fr, flux, flux_lo, fps = stft_flux(ref)
    say(lines, "")
    say(lines, "== grid ==")
    bpm, phase_f, bar_conf = find_grid(flux, flux_lo, fps, lines)
    BEAT, BAR = 60.0 / bpm, 4.0 * 60.0 / bpm
    BPM_LAST[0] = bpm
    GRID_S = phase_f / fps
    say(lines, "  grid      bpm %.3f  beat %.4f s  bar %.4f s  downbeat %.3f s"
        % (bpm, BEAT, BAR, GRID_S))
    say(lines, "  bar conf  %.2f%s" % (bar_conf, "" if bar_conf else
        "  <- the one thing a listener would hear as wrong; see the NOTE above"))

    n_bars = int(max(1, np.floor((n_ref / SR - GRID_S) / BAR) - 0.05))
    lvl, dense = bar_features(S, fr, fps, n_bars, GRID_S)
    del S

    say(lines, "")
    say(lines, "== structure ==")
    feat = np.vstack([lvl, dense])
    bounds = change_points(feat, CP_WIN_BARS, CP_MIN_GAP_BARS, CP_MAX,
                           CP_THRESHOLD, lines)
    segs = assign_roles(bounds, dense, lvl, lines)
    say(lines, "  %5s %8s %-7s %7s %7s" % ("bar", "t(s)", "role", "level", "dense"))
    for s in segs:
        say(lines, "  %5d %8.1f %-7s %7.1f %7.3f"
            % (s["a"], GRID_S + s["a"] * BAR, s["role"], s["lvl"], s["dense"]))
    role_of_bar = ["main"] * n_bars
    for s in segs:
        for b in range(s["a"], min(n_bars, s["b"])):
            role_of_bar[b] = s["role"]

    if args.probe:
        # The per-bar curve, because the role table above is the RULE's output
        # and the rule can only be judged against the data it was applied to.
        # Four bars per line keeps it readable at 97 bars.
        say(lines, "")
        say(lines, "== per-bar (bar t level dense role), 4 per line ==")
        for b0 in range(0, n_bars, 4):
            row = []
            for b in range(b0, min(n_bars, b0 + 4)):
                row.append("%3d %6.1f %6.1f %.3f %-6s"
                           % (b, GRID_S + b * BAR, lvl[b], dense[b], role_of_bar[b]))
            say(lines, "  " + " | ".join(row))
        say(lines, "")
        say(lines, "  --probe: no render (%.1f s)" % (time.time() - t0))
        write_report(lines)
        return 0

    # ---- render ----------------------------------------------------------
    say(lines, "")
    say(lines, "== render ==")
    busL, busR, kickbus, g_dyn = render_drums(n_bars, role_of_bar, lvl, lines)
    n = len(busL)
    furn = render_furniture(segs, n, lines)
    busL += furn
    busR += furn
    del furn

    # Reference treatment first, so `st` (the decoded stereo, 186 MB) is freed
    # before the reverb -- the reverb is the peak-memory step and the two do not
    # need to be resident at once.
    say(lines, "")
    say(lines, "== reference treatment ==")
    # Where the kit plays, the reference loses everything below 62 Hz -- the kick
    # and the pedal own that octave now.  In the intro (and in an outro, when the
    # tail measured quiet enough for there to be one) it loses everything below
    # 220 Hz instead, which is the classic filtered opening.  The two curves are
    # complementary by construction -- every bar has exactly one role -- so their
    # smoothed sum is 1 and no band is ever counted twice.
    g_drum = bar_curve(role_of_bar,
                       lambda r: 0.0 if r in ("intro", "outro") else 1.0, n, 0.30)
    g_soft = 1.0 - g_drum
    g_lvl = bar_curve(role_of_bar,
                      lambda r: 10.0 ** (REF_INTRO_DB / 20.0)
                      if r in ("intro", "outro") else 1.0, n, 0.30)
    # The duck exists to make room for the kick, so it is scaled by the same
    # level follow the kick itself got: ducking by a fixed amount under a kick
    # that was just turned down 4 dB over-ducks the quiet bridge by the same 4 dB.
    depth = bar_curve(role_of_bar,
                      np.array([{"climax": DUCK_CLIMAX, "build": DUCK_MAIN,
                                 "main": DUCK_MAIN}.get(r, 0.0)
                                * float(g_dyn[b]) for b, r in enumerate(role_of_bar)]),
                      n, 0.06)
    duck = sidechain(kickbus, depth, n)
    say(lines, "  duck: min gain %.3f, %.1f%% of the track under 0.9"
        % (float(duck.min()), 100.0 * float((duck < 0.9).mean())))

    refL = np.zeros(n)
    refR = np.zeros(n)
    for ch, src in ((0, st[0]), (1, st[1])):
        x = src[:n] if src.size >= n else np.pad(src, (0, n - src.size))
        y = (dsp.highpass(x, SR, REF_HP_HZ) * g_drum
             + dsp.highpass(x, SR, REF_INTRO_HP_HZ) * g_soft) * g_lvl * trim * duck
        if ch == 0:
            refL = y
        else:
            refR = y
    del st, ref
    mono_ref = 0.5 * (refL + refR)

    # One scale for the whole kit, set from the reference's OWN energy in this
    # render rather than from a table of peaks.  The first render levelled the
    # instruments absolutely and the check came back "reference share 8.9%" --
    # the drums were the piece.  Levelling the bus against the thing it is
    # covering makes that share a number this file chooses instead: for
    # uncorrelated material it is 1/(1+KIT_RMS_MULT^2).
    rr = float(np.sqrt((0.5 * (refL ** 2 + refR ** 2)).mean()))
    kr = float(np.sqrt((0.5 * (busL ** 2 + busR ** 2)).mean()))
    kscale = (KIT_RMS_MULT * rr) / max(1e-12, kr)
    busL *= kscale
    busR *= kscale
    kickbus *= kscale
    say(lines, "  kit scale x%.3f: ref rms %.5f, kit rms %.5f -> %.5f "
               "(target %.0f%% of the energy on the reference)"
        % (kscale, rr, kr, kr * kscale, 100.0 / (1.0 + KIT_RMS_MULT ** 2)))

    # Wet path.  Two reverb calls rather than one because a single IR convolved
    # into both channels is a mono reverb, which would narrow the piece -- the
    # reference's own L/R correlation is +0.792 and the added material should
    # not drag that toward 1.0.
    dry = 0.5 * (busL + busR)
    w1 = dsp.comb_reverb(dry, SR, rt60=2.4, predelay_ms=16.0, seed=1)
    w2 = dsp.comb_reverb(dry, SR, rt60=3.0, predelay_ms=23.0, seed=2)
    revL, revR = w1[:n] * REV_AMT, w2[:n] * REV_AMT
    del w1, w2
    d1, d2 = ms.pingpong(dry, DELAY_BEAT * BEAT, feedback=0.36, mix=1.0)
    dlyL, dlyR = d1[:n] * DLY_AMT, d2[:n] * DLY_AMT
    del d1, d2, dry

    # ---- mix and master --------------------------------------------------
    say(lines, "")
    say(lines, "== master ==")
    L = refL + busL + revL + dlyL
    R = refR + busR + revR + dlyR
    del busL, busR, kickbus, revL, revR, dlyL, dlyR, refL, refR
    say(lines, "  before the chain: peak %.4f  rms %+.2f dB"
        % (float(np.abs(np.stack([L, R])).max()), dsp.rms_db(0.5 * (L + R))))
    L, R = linked_compress(L, R, SR)
    L, R = dsp.soft_clip(L, drive=1.15), dsp.soft_clip(R, drive=1.15)
    L, R = dsp.limiter_stereo(L, R, SR, ceiling_db=-1.0)
    # Short fade-in: the reference opens with a fade of its own (bar 0 reads
    # 34.5 dB against 41.0 for bar 1), and stacking a 3 s fade on top of that
    # swallows its attack before the first kick.  The 6 s tail is longer than
    # the 3 s of silence after the reference ends, so nothing is cut off.
    L, R = dsp.fade(L, SR, 1.2, 6.0), dsp.fade(R, SR, 1.2, 6.0)
    say(lines, "  after:  peak %.4f  rms %+.2f dB  side/mid %.3f"
        % (float(np.abs(np.stack([L, R])).max()), dsp.rms_db(0.5 * (L + R)),
           ms.side_mid(L, R)[0]))

    os.makedirs(OUTDIR, exist_ok=True)
    wav = os.path.join(OUTDIR, NAME + ".wav")
    ms.write_wav(wav, L, R)
    say(lines, "  wav %s (%d B)" % (wav, os.path.getsize(wav)))
    encode(wav, ASSETS, lines)

    # ---- check -----------------------------------------------------------
    say(lines, "")
    say(lines, "== check ==")
    kicks_t = []
    kicks_r = []
    for bar in range(n_bars):
        if role_of_bar[bar] in ("intro", "outro"):
            continue
        for bt in drum_pattern(role_of_bar[bar], bar)[0]:
            kicks_t.append(at(bar, bt))
            kicks_r.append(role_of_bar[bar])
    kick_alignment(np.array(kicks_t), kicks_r, flux_lo, fps, lines)
    check_files(lines, L, R, mono_ref)

    say(lines, "")
    say(lines, "  total %.1f s" % (time.time() - t0))
    write_report(lines)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        sys.exit(1)
