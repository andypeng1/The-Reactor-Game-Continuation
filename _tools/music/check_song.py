"""Verify the delivered track against the spec it was composed to.

Why this exists: "it rendered" is not evidence that it matches anything.  The
numbers that define this piece -- duration, loudness, octave profile, stereo
width -- are all measurements, so they can all be re-measured on the finished
file and compared.  This does that, on the DELIVERED artifact (the mp3), not
on the in-memory buffers, because what ships is what has to be right.

The targets are imported from make_song.py rather than retyped.  A checker
that keeps its own copy of the spec is a second source of truth, and the day
the two disagree the checker will confidently certify the wrong thing.

Every check has a variant that must turn it red.  An assertion that has never
failed is decoration (DECISIONS 84/268), so `--variants` runs the whole panel
and fails if any variant leaves its target check green.

Usage:
  python _tools/music/check_song.py                 # check the deliverables
  python _tools/music/check_song.py --variants      # prove the checks bite
  python _tools/music/check_song.py --file X.mp3    # check something else
Exit: 0 all pass, 1 a check failed, 2 usage / missing input.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp                                              # noqa: E402
from analyze import decode                              # noqa: E402
import make_song as ms                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "asstes", "music")

# Tolerances.  Each is set from what the pipeline can actually hold, not from
# what would be nice: a lossy encode moves the octave profile by a few tenths,
# so demanding 0.1 dB would fail on the codec and teach me nothing.
TOL_DUR_S = 0.60          # seconds against the reference's 263.895
TOL_RMS_DB = 1.00         # mean RMS, 50 ms frames
TOL_RANGE_DB = 3.00       # p95-p5 of frame RMS, against the reference's arc
TOL_BAND_DB = 2.50        # worst single octave band
TOL_BAND_MEAN_DB = 1.20   # mean absolute band error
TOL_SIDE_MID = 0.045      # absolute, on a 0..inf ratio
TOL_CORR = 0.080          # absolute, on -1..1
# Texture of the top end.  THIS IS THE CHECK THAT WAS MISSING, and its absence
# is why the piece passed 12/12 while sounding like rain: every other number
# here is a level or a balance, and a continuous hiss has all of those right.
# Tolerances are wide enough for the codec (which moves the top octave by a few
# tenths of a dB) and narrow enough that the continuous bed -- 2.6 dB hot on the
# floor, spread 3.10 against the reference's 6.26 -- cannot pass.
TOL_TEX_DB = 1.50         # median and p90, each
TOL_TEX_SPREAD_DB = 2.00  # p90 - median
TOL_TEX_WITHIN = 0.080    # fraction of frames within 6 dB of the floor
# The delivered peak must keep this much headroom below full scale.  NOT a
# window around the limiter's -1.0 dB ceiling: the limiter only acts when the
# material reaches it, and this piece sits under, so the in-memory peak is
# -2.05 dBFS.  What the check is for is the lossy encoders, which overshoot --
# they push that -2.05 to -1.14 (mp3) and -0.91 (ogg).  A ceiling with room
# for that overshoot is the honest statement; a tight window around a ceiling
# the material never touches would only have been measuring an earlier mix.
#
# Those were -2.65 / -2.16 before the air bed became a gated rhythm, and the
# shrink to -1.11 / -0.82 was the gate's own doing: sharper transients give the
# transform codecs more to smear.  Raising the melody 21.6 dB moved it again,
# to -1.14 / -0.91, with the in-memory peak essentially unchanged (-2.03 ->
# -2.05) -- the loudness loop pins the RMS and the limiter catches the peaks, so
# a louder element buys overshoot without buying level.  The ogg now has
# 0.41 dB of room left, so this number is worth re-reading every time the top
# end changes shape -- and the -0.50 is kept rather than raised because it still
# measures 0 samples at full scale after decoding.
PEAK_MAX_DB = -0.50
CLIP_FRAC = 1e-5          # fraction of samples allowed at full scale
DC_MAX = 0.005
# Boundary de-click.  The file must start and end at (near) zero, because a
# buffer that starts or stops on a non-zero sample produces a step, and a step
# is a click.  The measured window is 2 ms, which is where a de-click fade is
# still doing its work.  NOT the reference's behaviour: it opens on 2 s of
# EXACT digital silence (-160 dBFS), an artifact of how it was ripped, and a
# margin set to match that would be asserting the artifact rather than the
# intent.  A 20 ms linear fade (make_song.EDGE_FADE_MS) puts the first 2 ms at
# -24.8 dB re body; 15 dB leaves ~10 dB of room.
FADE_MS = 2.0
FADE_MARGIN_DB = 15.0
# |first sample| and |last sample| must be under this.  Not 0: the master's
# fade puts the WAV's boundaries at EXACTLY 0.0 (measured), but the lossy
# decoders do not reconstruct it -- their transform rings at the edge.  Measured
# boundary samples: mp3 5.4e-4 / 4.4e-4, ogg 9.3e-5 / 1.0e-3.  So the number is
# set above what the codecs do, which is -60 dBFS and inaudible, rather than
# below it, which would be measuring the encoder.  The variant that has to break
# this sits at 0.4, two orders of magnitude clear.
EDGE_ZERO = 2.0e-3
# A click is one isolated jump standing out from the signal's own slew.  The
# test is a ratio so it does not depend on level, and the baseline is LOCAL.
#
# The first version divided the loudest step by the GLOBAL 99.99th percentile
# step, which was fine while the material was smooth.  When the air bed became
# a gated 8th-note rhythm, the attacks of that rhythm moved into the top 0.01%
# of steps -- so the percentile rose to meet the splice and the check went DEAD:
# the healthy file measured 1.98 and the 0.9 splice measured 3.23, both under
# the old 4.0.  The variant panel caught it, which is exactly what it is for.
#
# A click is a step that is isolated -- huge next to its own neighbourhood, not
# next to the whole piece.  So each candidate is divided by the median step in
# a +-5 ms window around it, which is a property the music does not have.  The
# separation is now 8x instead of 1.6x: healthy 15.9 (a kick attack), a 0.9
# splice 129.7.  The threshold sits at the geometric midpoint, 2.8x of room
# either way.  Only the top 200 steps are tested -- the maximum is attained at
# a large step, so scanning the small ones could not change the answer.
CLICK_LOCAL_MAX = 45.0
CLICK_WIN_MS = 5.0
CLICK_TOPK = 200


def load(path):
    """Deliverable -> (stereo 44.1 kHz float64 (2,n), mono)."""
    st = decode(path, 44100, 2)
    return st, st.mean(axis=0)


def click_ratio(x, win_ms=CLICK_WIN_MS, topk=CLICK_TOPK):
    """(worst local step ratio, its sample index).

    For each of the `topk` largest sample-to-sample steps, divide it by the
    median step in a +-win_ms window around it.  A musical transient is large
    but not alone; a splice is large and alone."""
    d = np.abs(np.diff(x))
    w = int(round(win_ms * 1e-3 * 44100))
    idx = np.argpartition(d, -topk)[-topk:]
    best, arg = 0.0, 0
    for i in idx:
        lo, hi = max(0, int(i) - w), min(len(d), int(i) + w + 1)
        r = float(d[i]) / (float(np.median(d[lo:hi])) + 1e-12)
        if r > best:
            best, arg = r, int(i)
    return best, arg


def checks(st):
    """Every measurement, as (id, ok, text).  Pure: no printing, no exit."""
    out = []
    L, R = st[0], st[1]
    M = (L + R) * 0.5

    def add(cid, ok, text):
        out.append((cid, bool(ok), text))

    dur = st.shape[1] / 44100.0
    add("dur", abs(dur - 263.895) <= TOL_DUR_S,
        "duration %.3f s (ref 263.895, tol %.2f)" % (dur, TOL_DUR_S))

    pk = float(max(np.abs(L).max(), np.abs(R).max()))
    pk_db = 20 * np.log10(pk + 1e-12)
    add("peak", pk_db <= PEAK_MAX_DB,
        "peak %.4f (%.2f dBFS), must keep %.2f dB of headroom"
        % (pk, pk_db, -PEAK_MAX_DB))

    frac = float((np.abs(st) >= 0.999).mean())
    add("clip", frac <= CLIP_FRAC, "samples at full scale %.2e (max %.1e)"
        % (frac, CLIP_FRAC))

    rms = float(ms.frame_rms_db(M).mean())
    add("rms", abs(rms - ms.TARGET_RMS) <= TOL_RMS_DB,
        "mean RMS %+.2f dBFS (target %+.2f, tol %.2f)"
        % (rms, ms.TARGET_RMS, TOL_RMS_DB))

    # The arc: loudness SHAPE, independent of the mean above.  A flat piece and
    # a dynamic one can share a mean, so the mean cannot see this -- which is why
    # the panel was green while the delivered file was a 4.5 dB slab against the
    # reference's 14.6 dB.  p95-p5 rather than min/max so a single stray frame
    # (a boundary, a codec glitch) cannot set the number.
    fr = ms.frame_rms_db(M)
    p5 = float(np.percentile(fr, 5.0))
    p95 = float(np.percentile(fr, 95.0))
    add("range", abs((p95 - p5) - ms.TARGET_RANGE_DB) <= TOL_RANGE_DB,
        "arc p5 %+.2f p95 %+.2f -> %.2f dB (target %.2f, tol %.2f)"
        % (p5, p95, p95 - p5, ms.TARGET_RANGE_DB, TOL_RANGE_DB))

    prof = ms.octave_profile(M)
    d = prof - np.array(ms.TARGET_DB)
    worst = int(np.argmax(np.abs(d)))
    add("band", float(np.abs(d).max()) <= TOL_BAND_DB,
        "worst band %+5.1f dB at %d-%d Hz (tol %.1f)"
        % (d[worst], ms.OCT_EDGES[worst], ms.OCT_EDGES[worst + 1], TOL_BAND_DB))
    add("bandmean", float(np.abs(d).mean()) <= TOL_BAND_MEAN_DB,
        "mean |band error| %.2f dB (tol %.2f)"
        % (float(np.abs(d).mean()), TOL_BAND_MEAN_DB))

    # Top-end texture: is the 2-8 kHz energy a FLOOR or a RHYTHM?  Band power
    # above is blind to the difference, so this is the only thing in the panel
    # that can catch a hiss dressed as content.
    med, p90, spread, within = ms.texture_stats(M)
    ok_tex = (abs(med - ms.REF_TEX_MED_DB) <= TOL_TEX_DB
              and abs(p90 - ms.REF_TEX_P90_DB) <= TOL_TEX_DB
              and abs(spread - (ms.REF_TEX_P90_DB - ms.REF_TEX_MED_DB))
              <= TOL_TEX_SPREAD_DB
              and abs(within - ms.REF_TEX_WITHIN) <= TOL_TEX_WITHIN)
    add("texture", ok_tex,
        "2-8k med %+.2f p90 %+.2f spread %.2f within %.1f%% "
        "(ref %+.2f %+.2f %.2f %.1f%%)"
        % (med, p90, spread, 100 * within, ms.REF_TEX_MED_DB,
           ms.REF_TEX_P90_DB, ms.REF_TEX_P90_DB - ms.REF_TEX_MED_DB,
           100 * ms.REF_TEX_WITHIN))

    sm = ms.side_mid(L, R)[0]
    add("sidemid", abs(sm - ms.TARGET_SIDE_MID) <= TOL_SIDE_MID,
        "side/mid %.3f (target %.3f, tol %.3f)"
        % (sm, ms.TARGET_SIDE_MID, TOL_SIDE_MID))

    corr = float(np.corrcoef(L, R)[0, 1])
    add("corr", abs(corr - ms.TARGET_CORR) <= TOL_CORR,
        "L/R corr %+.3f (target %+.3f, tol %.3f)"
        % (corr, ms.TARGET_CORR, TOL_CORR))

    dc = float(M.mean())
    add("dc", abs(dc) <= DC_MAX, "DC offset %+.5f (max %.4f)" % (dc, DC_MAX))

    ratio, at = click_ratio(M)
    add("click", ratio <= CLICK_LOCAL_MAX,
        "worst step / local median %.1f at %.2f s (max %.1f), step %.4f"
        % (ratio, at / 44100.0, CLICK_LOCAL_MAX,
           float(np.abs(np.diff(M)).max())))

    # Boundary de-click: the samples AT the boundary must be zero (a step there
    # is a click), and the first/last FADE_MS must be under the body.
    e0 = float(max(abs(st[0][0]), abs(st[1][0])))
    e1 = float(max(abs(st[0][-1]), abs(st[1][-1])))
    h = int(round(FADE_MS * 1e-3 * 44100))
    body = float(np.sqrt((M ** 2).mean()) + 1e-12)
    head = float(np.sqrt((M[:h] ** 2).mean() + 1e-12))
    tail = float(np.sqrt((M[-h:] ** 2).mean() + 1e-12))
    hd, tl = 20 * np.log10(head / body), 20 * np.log10(tail / body)
    add("fade", max(e0, e1) <= EDGE_ZERO and hd <= -FADE_MARGIN_DB
        and tl <= -FADE_MARGIN_DB,
        "edge |x| %.1e / %.1e (max %.0e); first/last %.0f ms %+.1f / %+.1f dB "
        "under body (want <= %+.0f)"
        % (e0, e1, EDGE_ZERO, FADE_MS, hd, tl, -FADE_MARGIN_DB))
    return out


# ============================== variants ==============================
# Each returns a mutated stereo array and the check it is required to break.

def _lp(st, fc):
    return np.stack([dsp.lowpass(st[0], 44100, fc), dsp.lowpass(st[1], 44100, fc)])


def _slab(s):
    """Level every 50 ms frame to the file's median loudness -- i.e. delete the
    arc.  This is not a synthetic straw man: it is the exact defect the range
    check exists to catch, because the delivered piece really did ship as a flat
    ~4.5 dB bed.  A variant has to produce the thing its check detects."""
    n = s.shape[1]
    h = 2205
    fr = s[:, :n // h * h].reshape(s.shape[0], -1, h)
    r = np.sqrt((fr ** 2).mean(axis=(0, 2)) + 1e-12)
    tgt = float(np.median(r))
    m = np.clip(np.repeat(tgt / (r + 1e-12), h), 0.0, 8.0)
    if m.size < n:
        m = np.concatenate([m, np.full(n - m.size, m[-1])])
    return s * m[:n]


def _hiss(s):
    """Put a continuous HF floor under the track -- the exact defect the texture
    check exists to catch, and the one the piece actually shipped with.  The
    noise is scaled so its in-band RMS equals the track's own floor, which
    lifts the floor 3 dB and leaves the peaks where they are: band power barely
    moves, the spread collapses.  That is the whole point -- a variant has to
    produce the thing its check detects."""
    rng = np.random.default_rng(11)
    n = rng.standard_normal(s.shape)
    b = np.stack([dsp.bandpass(n[0], 44100, ms.TEX_BAND_HZ[0], ms.TEX_BAND_HZ[1]),
                  dsp.bandpass(n[1], 44100, ms.TEX_BAND_HZ[0], ms.TEX_BAND_HZ[1])])
    lvl = 10 ** (ms.REF_TEX_MED_DB / 20.0)
    b *= lvl / (float(np.sqrt((b ** 2).mean())) + 1e-12)
    return s + b


VARIANTS = {
    "gain+6": (lambda s: s * 2.0, "peak", "6 dB hotter -- the ceiling is gone"),
    "gain-6": (lambda s: s * 0.5, "rms", "6 dB quieter -- loudness target missed"),
    "slab": (_slab, "range", "every frame levelled to the median -- the arc gone"),
    "mono": (lambda s: np.stack([s.mean(axis=0), s.mean(axis=0)]), "sidemid",
             "collapsed to mono -- width target missed"),
    "dark": (lambda s: _lp(s, 4000.0), "band", "low-passed -- top octaves gone"),
    "hiss": (_hiss, "texture",
             "a continuous HF floor -- the rain the operator heard, band power unchanged"),
    # Gain into a hard ceiling, because that is what clipping IS.  The previous
    # version clipped at 0.5, which produces flat-topped distortion but not one
    # sample at the digital ceiling -- and the clip check counts samples at
    # >= 0.999, so it measured 0.00e+00 and stayed green.  A variant has to
    # produce the thing its check detects, or it is the decoration it exists to
    # disprove.  This one lands the peaks at exactly 1.0, which correctly takes
    # the peak check red as well: clipping to full scale does lose headroom.
    "clip": (lambda s: np.clip(s * 4.0, -1.0, 1.0), "clip",
             "gain into a full-scale ceiling -- hard clipping"),
    "truncate": (lambda s: s[:, :-20 * 44100], "dur", "20 s cut off the end"),
    "dc": (lambda s: s + 0.05, "dc", "0.05 of DC injected"),
    "click": (lambda s: np.concatenate(
        [s[:, :1000], s[:, 1000:1001] + 0.9, s[:, 1001:]], axis=1),
        "click", "one 0.9 sample step spliced in"),
    "edge": (lambda s: np.concatenate(
        [np.full((s.shape[0], 1), 0.4), s[:, 1:]], axis=1),
        "fade", "boundary step at sample 0 -- the click the fade prevents"),
}


def run_variants(st):
    print("== variant panel: every check needs one that makes it fail ==")
    bad = []
    for name, (fn, expect, why) in VARIANTS.items():
        res = checks(fn(st.copy()))
        failed = [cid for cid, ok, _ in res if not ok]
        hit = expect in failed
        print("  %-9s expect %-8s -> %s  %s"
              % (name, expect, "RED" if hit else "GREEN !!",
                 ",".join(failed) or "(nothing)"))
        if not hit:
            bad.append("%s (%s) did not turn %s red" % (name, why, expect))
    if bad:
        print("")
        for b in bad:
            print("  FAIL %s" % b)
        return 1
    print("  all %d variants red on their own check" % len(VARIANTS))
    return 0


def main(argv):
    if "--variants" in argv:
        path = os.path.join(ASSETS, ms.NAME + ".mp3")
        if not os.path.exists(path):
            print("missing %s" % path)
            return 2
        st, _ = load(path)
        return run_variants(st)

    files = []
    if "--file" in argv:
        files = [argv[argv.index("--file") + 1]]
    else:
        for ext in ("mp3", "ogg"):
            p = os.path.join(ASSETS, "%s.%s" % (ms.NAME, ext))
            if os.path.exists(p):
                files.append(p)
    if not files:
        print("nothing to check under %s" % ASSETS)
        return 2

    rc = 0
    for path in files:
        print("== %s (%d bytes) ==" % (path, os.path.getsize(path)))
        st, _ = load(path)
        for cid, ok, text in checks(st):
            print("  %-9s %s  %s" % (cid, "ok  " if ok else "FAIL", text))
            if not ok:
                rc = 1
        print("")
    print("CHECK %s" % ("failed" if rc else "ok"))
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        sys.exit(1)
