#!/usr/bin/env python
"""avb_from_log.py -- where the console's AVB numbers and stall rate come from.

    python -X utf8 _tools/avb_from_log.py

Three readings, all off `Data/DataCollection.Log` -- the shipped game's own
recording of a live shift -- so that the two constants in `luau-windows/gui.py`
(the 3300 the button takes off, and the ~600 a stalled tick gives back) are
reproducible instead of remembered:

  1. that `fluctuation` IS the per-tick temperature increment, which is the
     thing the operator's `fluc` names.  Checked against tempF's own deltas
     rather than against any source file, so it is a reading and not a quote.
     Two stretches are expected to disagree and both are named in the output:
     the priming jump (tempF 0 -> 9588 in one sample) and the collapse, where
     the sampled state stops being the tick's arithmetic.
  2. the six AVB presses and the pressure each one moved.  The drop is found
     as the one big pressure STEP near each click, because a click lands
     between samples and the naive "sample before, sample after" straddle
     sometimes has the step already inside its first sample.  Whatever the
     chamber was doing across that same interval is printed BESIDE the drop,
     since printing the drop alone hands a reader a number whose denominator
     is invisible (CLAUDE.md 0.21).
  3. every sample at or below 2200 PSI and its `fluctuation` -- the band the
     stall plunge lives in.  Read as dips, with the collapse at the end of the
     recording named and kept out of the band.

ASCII only on stdout: this console is GBK.
"""

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "Data", "DataCollection.Log")


def records():
    """The JSON records, with the ModuleScript wrapper taken off."""
    raw = io.open(LOG, encoding="utf-8").read()
    body = raw.split("[[==", 1)[1].rsplit("==]]", 1)[0]
    return [json.loads(line) for line in body.splitlines() if line.strip()]


def reactor(record):
    return record["data"]["payload"]["reactor"]


def dedupe(records):
    """One row per tick.

    The recorder samples faster than the game ticks, so between ticks several
    samples come back byte-identical.  Every reading below that means "per
    tick" has to drop those repeats first: on the raw list "the sample after
    the press" is usually a verbatim repeat of the sample before it, and the
    button then measures a drop of 0 -- a reading about the recorder's sample
    rate wearing the costume of a reading about the button (CLAUDE.md 0.18:
    a wrong ruler does not error, it just hands you a number).
    """
    out = []
    for record in records:
        if out:
            state, last = reactor(record), reactor(out[-1])
            if (state["tempF"], state["pressure"], state["fluctuation"]) == (
                    last["tempF"], last["pressure"], last["fluctuation"]):
                continue
        out.append(record)
    return out


def main():
    allr = records()
    kinds = {}
    for r in allr:
        kinds[r["data"].get("type")] = kinds.get(r["data"].get("type"), 0) + 1
    print("%s" % LOG)
    print("%d records: %s\n" % (len(allr), ", ".join(
        "%d %s" % (v, k) for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]))))

    rows = [r for r in allr if r["data"].get("type") == "tick"]
    ticks = dedupe(rows)

    # --- 1. what `fluctuation` is -------------------------------------------
    steps = []
    for index in range(1, len(ticks)):
        now, before = reactor(ticks[index]), reactor(ticks[index - 1])
        moved = now["tempF"] - before["tempF"]
        steps.append((index, ticks[index]["timestamp"], moved,
                      now["fluctuation"]))
    disagree = [s for s in steps if abs(s[2] - s[3]) > 1.0]

    print("-- `fluctuation` is the per-tick temperature increment --")
    print("   one row per tick after deduplication: %d (~%d duplicate samples "
          "dropped)" % (len(ticks), len(rows) - len(ticks)))
    print("   tempF's own delta == fluctuation in %d of %d steps"
          % (len(steps) - len(disagree), len(steps)))
    for index, stamp, moved, fluc in disagree:
        print("     %s  tempF moved %9.1f, fluctuation %9.1f" % (stamp[11:], moved, fluc))
    print("   (the two stretches that must not agree: the priming jump, which is\n"
          "    not a tick at all, and the collapse, where the sampled state and\n"
          "    the tick's own arithmetic part ways)\n")

    # --- 2. the six AVB presses ---------------------------------------------
    # A press's drop has to be READ AS A DISCONTINUITY, not taken from "the
    # sample before and the sample after".  The recorder samples faster than
    # the game ticks (see `dedupe`) and a press can land in the same second as
    # a tick, so that straddle sometimes has the step already inside its first
    # sample and reads a drop of 0 or a negative one -- a reading about where
    # the press fell between samples, wearing the costume of a reading about
    # the button.  Within six seconds either side there is exactly one step of
    # this size (the chamber moves tens of PSI a tick, the button moves 3300),
    # so the largest step in the window IS the button, and the window is
    # printed with it.
    presses = [r for r in allr if r["data"].get("type") == "click"
               and r["data"]["payload"].get("control") == "AVB"]

    def clock(stamp):
        hh, mm, ss = (int(part) for part in stamp[11:].split(":"))
        return hh * 3600 + mm * 60 + ss

    print("-- the six AVB presses --")
    if not presses:
        print("   none in this log\n")
    else:
        print("   %-8s %-38s %8s   %10s"
              % ("at", "biggest one-tick drop within 6 s", "drop", "drop-3300"))
        for press in presses:
            when = clock(press["timestamp"])
            near = [i for i in range(len(ticks) - 1)
                    if abs(clock(ticks[i]["timestamp"]) - when) <= 6]
            if not near:
                print("   %-8s no samples within 6 s" % press["timestamp"][11:])
                continue
            i = max(near, key=lambda k: reactor(ticks[k])["pressure"]
                    - reactor(ticks[k + 1])["pressure"])
            before, after = reactor(ticks[i]), reactor(ticks[i + 1])
            drop = before["pressure"] - after["pressure"]
            print("   %-8s %5.0f @%s -> %5.0f @%s %8.0f   %+10.0f"
                  % (press["timestamp"][11:], before["pressure"],
                     ticks[i]["timestamp"][11:], after["pressure"],
                     ticks[i + 1]["timestamp"][11:], drop, drop - 3300.0))
        print("   (the column beside the drop is the chamber's own movement across\n"
              "    the same interval; where it is not 0 the drop is 3300 of button\n"
              "    plus that drift, which is why it is printed next to it)\n")

        # How long the button was UNAVAILABLE.  The gap between two presses is
        # not the cooldown -- the operator may simply have pressed late -- so
        # the reading is the SMALLEST gap, which is a lower bound on the
        # cooldown and the closest this log gets to it.  What the wiki says for
        # comparison: "a cooldown of about 25-26 seconds, or around 15 reactor
        # ticks" -- which is also where the tick length comes from (25.5/15 =
        # 1.7 s), a number neither this log nor our remake's own clock uses.
        stamps = [clock(press["timestamp"]) for press in presses]
        gaps = [b - a for a, b in zip(stamps, stamps[1:])]
        if gaps:
            print("-- how long the button stayed unavailable --")
            print("   gaps between presses (s): %s"
                  % ", ".join("%d" % g for g in gaps))
            print("   the smallest is %d s, so the cooldown is at least that --"
                  % min(gaps))
            print("   consistent with the wiki's \"about 25-26 seconds\", and\n"
                  "   with its \"around 15 reactor ticks\" only if a reactor tick\n"
                  "   is ~1.7 s.  This console's tick is the operator's own\n"
                  "   `calculation.luau` tick (`task.wait(1)`), so the two\n"
                  "   numbers belong to two different clocks.\n")

    # --- 3. the stall -------------------------------------------------------
    # Grouped into DIPS: a run of consecutive samples at or below the floor.
    # Within a dip the lowest-pressure sample is the plunge and the rest are the
    # chamber on its way back up, which is the split the eye makes and the one
    # the two bands below are about.  The pre-start rows (the machine cold at
    # 0 PSI, before the shift) are not dips and are skipped -- including them
    # would put a fluctuation of 0 into the plunge band and drag the reading
    # down with a sample where nothing was running at all.
    print("-- samples at or below 2200 PSI --")
    runs = []
    for index, record in enumerate(ticks):
        # The pre-start rows (the machine cold at 0 PSI, before the shift) are
        # not dips.  Including them puts a fluctuation of 0 into the plunge band
        # and drags the reading down with a sample where nothing ran at all.
        if not record["data"]["payload"]["stats"]["GameActive"]:
            continue
        if reactor(record)["pressure"] > 2200:
            continue
        if runs and runs[-1][-1] == index - 1:
            runs[-1].append(index)
        else:
            runs.append([index])

    for run in runs:
        for index in run:
            state = reactor(ticks[index])
            print("   %s  press %8.0f  tempF %9.1f  fluctuation %8.1f"
                  % (ticks[index]["timestamp"][11:], state["pressure"],
                     state["tempF"], state["fluctuation"]))
        print("        ^ %d sample(s)" % len(run))

    # Which runs are ordinary dips and which is the collapse is a reading off
    # the numbers, not a rule about which one is last.  Every stalled dip but
    # the last ends with the chamber coming back -- the press took the pressure
    # down, the core keeps boiling, and the samples read 938 -> 1288 -> 1638 ->
    # 1988.  The last one runs the other way (2056 -> 1836 -> 1596 -> 1332)
    # with the temperature coming down with it (6288 -> 2318): that is the
    # reactor failing, and averaging it into the stall band would fold two
    # regimes into one number.
    def recovering(run):
        return (reactor(ticks[run[-1]])["pressure"]
                > reactor(ticks[run[0]])["pressure"])

    closed = [run for run in runs if recovering(run)]
    falling = [run for run in runs if not recovering(run)]
    if closed:
        def plunge(run):
            return min(run, key=lambda i: reactor(ticks[i])["pressure"])
        lows = [reactor(ticks[plunge(run)])["fluctuation"] for run in closed]
        climbs = [reactor(ticks[i])["fluctuation"] for run in closed
                  for i in run if i != plunge(run)]
        print("   dips the chamber comes back from: %d of %d"
              % (len(closed), len(runs)))
        print("   plunge (lowest-pressure sample of each): %s"
              % ", ".join("%.0f" % v for v in lows))
        print("   ...so the plunge band is %.0f .. %.0f" % (min(lows), max(lows)))
        if climbs:
            print("   the same dips on the way back up:      %.0f .. %.0f"
                  % (min(climbs), max(climbs)))
    for run in falling:
        print("   NOT counted above -- the pressure is still going down across it\n"
              "   (%s at %.0f PSI falling to %.0f PSI at %s): that is the\n"
              "   collapse, not a dip.  Its samples: %s"
              % (ticks[run[0]]["timestamp"][11:],
                 reactor(ticks[run[0]])["pressure"],
                 reactor(ticks[run[-1]])["pressure"],
                 ticks[run[-1]]["timestamp"][11:],
                 ", ".join("%.0f" % reactor(ticks[i])["fluctuation"]
                           for i in run)))
    print("   (what this band can and cannot settle: it contains BOTH the\n"
          "    operator's -586 and our own remake's Config value of 750, so it\n"
          "    does not choose between them -- the console picks 586 because it\n"
          "    models the original, not because of a reading)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:                  # a deliberate exit passes through
        raise
    except BaseException:               # noqa: BLE001 -- CLAUDE.md 0.6: an
        import traceback                # uncaught exception can leave rc = 0,
        traceback.print_exc()           # and "the checker crashed" then looks
        sys.exit(1)                     # byte-for-byte like "all clear".
