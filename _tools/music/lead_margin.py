"""Is the lead audible over its own accompaniment?  Measured, per note.

The margin is 10*log10(lead / everything-else-sounding-at-that-instant) over
each note's own window, in two bands:

    narrow = +-1/6 octave around the note's fundamental (the pitch carrier)
    wide   = that fundamental out to 4x (the harmonics)

Measured PRE-master, because the master EQ loop pins the octave profile and an
element's prominence is exactly what such a loop flattens; post-master the
number is not the same quantity.

Two things this ruler does that the previous one did not, both of which changed
the answer by more than 10 dB:

  * the rest is assembled from a stem set whose lead is set to ZERO, so it
    contains no melody at all.  The earlier version subtracted an isolated lead
    buffer from a mix that the new composition had already put the lead into,
    which is not a rest -- it is the mix again, with a second copy of the lead
    on top of the first.
  * the melody's power is the bandpower of the summed dry+wet signal, not the
    sum of two separately-measured bandpowers.  Those two differ by 3 dB here
    because the dry and the wet are correlated in the note's own band.

And a margin is only a margin against an accompaniment with no melody in it,
so with_lead(..., 0, 0) is the definitional half of this file.
"""
import sys

import numpy as np

sys.path.insert(0, "D:\\rblxTRGproject\\_tools\\music")
import dsp                                                      # noqa: E402
import make_song as ms                                          # noqa: E402


def main():
    """Print the margin report.  Wrapped rather than left at module scope so
    that importing this file does not assemble four full mixes, and so the exit
    code is explicit -- same shape as make_song.main and check_song.main."""
    gb = {k: ms.bar_gains(k) for k in ms.LAYERS}
    base = ms.load_stems()

    print("assembling: no lead / lead-dry only / lead-wet only ...", flush=True)
    NONE_ = ms.assemble(ms.with_lead(base, 0.0, 0.0))
    DRY_ = ms.assemble(ms.with_lead(base, ms.LEAD_DRY, 0.0))
    WET_ = ms.assemble(ms.with_lead(base, 0.0, ms.LEAD_SEND))
    LEAD_ = [DRY_[i] - NONE_[i] + WET_[i] - NONE_[i] for i in (0, 1)]


    def bp(L, R, a, b, lo, hi):
        if b - a < 64:
            return 1e-30
        yl = dsp.bandpass(L[a:b], ms.SR, lo, hi)
        yr = dsp.bandpass(R[a:b], ms.SR, lo, hi)
        return float((yl ** 2).mean() + (yr ** 2).mean())


    rows = []
    for bar, beat, note, dur, tag in ms.lead_plan():
        gl = gb["lead"][bar] if 0 <= bar < ms.N_BARS else 0.0
        if gl <= 0.01:
            continue
        a = int(round(ms.at(bar, beat) * ms.SR))
        b = min(len(LEAD_[0]), a + int(round(max(dur, 0.45) * ms.SR)))
        if b - a < 64:
            continue
        f0 = ms.hz(note)
        lo = f0 / 2 ** (1 / 6.)
        rows.append((bar, note, tag, ms.section_of(bar),
                     10 * np.log10(max(bp(LEAD_[0], LEAD_[1], a, b, lo, f0 * 2 ** (1 / 6.)), 1e-30)
                                   / max(bp(NONE_[0], NONE_[1], a, b, lo, f0 * 2 ** (1 / 6.)), 1e-30)),
                     10 * np.log10(max(bp(LEAD_[0], LEAD_[1], a, b, lo, f0 * 4.0), 1e-30)
                                   / max(bp(NONE_[0], NONE_[1], a, b, lo, f0 * 4.0), 1e-30))))

    # An empty set says two lies: all([]) is true and median([]) is nan.  Every
    # number below is a median over `rows`, so if the loop filtered everything out
    # this ruler would print "nan" in six places and exit 0 -- which reads exactly
    # like a measured result.  Say it instead (DECISIONS 295/296).
    if not rows:
        raise SystemExit(
            "no note events were measured: lead_plan() returned nothing that clears the "
            "lead gain gate, or every window came out shorter than 64 samples.\n"
            "Refusing to report a median over an empty set.")

    nar = np.array([r[4] for r in rows])
    wid = np.array([r[5] for r in rows])
    print("")
    print("  lead level: dry %.2f  send %.2f   (%.2fx the 1.02/0.40 reference point)"
          % (ms.LEAD_DRY, ms.LEAD_SEND, ms.LEAD_DRY / 1.02))
    print("  n = %d note events" % len(rows))
    print("  ALL      narrow median %+.1f dB   wide median %+.1f dB"
          % (np.median(nar), np.median(wid)))
    print("  narrow: %d of %d events under 0 dB"
          % (int((nar < 0).sum()), len(nar)))

    print("")
    print("  by section (median narrow / wide, count):")
    secs = {}
    for r in rows:
        secs.setdefault(r[3], []).append(r)
    for s in sorted(secs, key=lambda k: min(x[0] for x in secs[k])):
        v = np.array([[x[4], x[5]] for x in secs[s]])
        print("    %-10s %+6.1f / %+6.1f   n=%d"
              % (s, np.median(v[:, 0]), np.median(v[:, 1]), len(v)))

    print("")
    print("  by tag (a=theme A statement, b=theme B/B2 ascent, ctr=counter-line):")
    for t in ("a", "b", "ctr"):
        v = np.array([[x[4], x[5]] for x in rows if x[2] == t])
        if len(v):
            print("    %-4s %+6.1f / %+6.1f   n=%d"
                  % (t, np.median(v[:, 0]), np.median(v[:, 1]), len(v)))

    print("")
    print("  the worst 12 events by narrow margin:")
    for r in sorted(rows, key=lambda x: x[4])[:12]:
        print("    bar %2d %-3s %-4s (%-8s) narrow %+6.1f" % (r[0], r[1], r[2], r[3], r[4]))

    L, R = ms.assemble(base)
    print("")
    print("  whole mix (pre-master): side/mid %.3f  corr %+.3f  rms %+.2f dB"
          % (ms.side_mid(L, R)[0], float(np.corrcoef(L, R)[0, 1]),
             dsp.rms_db((L + R) * 0.5)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        sys.exit(1)
