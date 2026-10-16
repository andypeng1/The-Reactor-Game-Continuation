#!/usr/bin/env python
"""coolant_from_log.py -- where the console's coolant numbers come from.

    python -X utf8 _tools/coolant_from_log.py

The desktop console's third control (three Isotope E pumps, each 0..3) removes
`120 x (p1 + p2 + p3)` degrees a tick.  Two of the three sources for that
constant are source files (`Data/TRGWeb.luau:178`, our remake's
`Config.Sim.PumpCooling`); this file is the third, and it is a READING off
`Data/DataCollection.Log` -- the shipped game's own recording of a live shift --
rather than a quote:

  1. the exact identity.  The log records the original's own prediction every
     sample, `predictions.predDT`, and
         predDT * 5 == 65 * sum(cbl.level) - 120 * sum(coolant.levels)
     holds on ALL of its records with a maximum error of 0.  Two constants
     read out of a running game rather than out of a file.  The same block
     prints the near-miss spellings (which fields also satisfy it, and which
     one does not) -- an identity that is satisfied by three different
     spellings has not identified which one the game used.
  2. the recorded per-tick temperature increments, grouped by the level pair
     that was held, against the same line.  This is the part that says the
     line is the game's BEHAVIOUR and not only its bookkeeping; it is also
     where the recording's limits show up, and they are printed rather than
     smoothed: the pre-start stretches where nothing moves, and the terminal
     collapse, where the line and the reading part company for good.
  3. the pump levels the recording actually visits (0..3, which is the widget's
     range) and how much of it was spent with the lasers DARK -- the case the
     console's placement decision turns on.

ASCII only on stdout: this console is GBK.
"""

import io
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "Data", "DataCollection.Log")

HEAT_PER_CBL_LEVEL = 65.0     # TRGWeb: `(CBL1 + CBL2 + CBL3)*65`
COOL_PER_PUMP_LEVEL = 120.0   # TRGWeb: `(pump1 + pump2 + pump3)*120`


def records():
    """The JSON records, with the ModuleScript wrapper taken off."""
    raw = io.open(LOG, encoding="utf-8").read()
    body = raw.split("[[==", 1)[1].rsplit("==]]", 1)[0]
    return [json.loads(line) for line in body.splitlines() if line.strip()]


def payload(record):
    return record["data"]["payload"]


def cbl_sum(p):
    """The CBL sum the identity wants: the LEVEL sum, not `cbl.power`.

    Easy to get wrong, and the identity is the oracle: `power` is a different
    quantity wearing a similar name (it reads 10 at level 0 and 100 at level 4,
    where the level is an index).  `level` and `level x active` agree on every
    record here, so this log cannot tell those two apart -- see the run.
    """
    return sum(p["cbl"]["level"])


def pump_sum(p):
    return sum(p["coolant"]["levels"])


def line(C, K):
    """The original's per-tick temperature increment, from the two constants."""
    return HEAT_PER_CBL_LEVEL * C - COOL_PER_PUMP_LEVEL * K


def reading_one(ticks):
    print("1. THE IDENTITY -- the original's own arithmetic, recorded live")
    worst = 0.0
    for r in ticks:
        p = payload(r)
        want = line(cbl_sum(p), pump_sum(p))
        worst = max(worst, abs(p["predictions"]["predDT"] * 5.0 - want))
    print("   predDT * 5  ==  %.0f*sum(cbl.level) - %.0f*sum(pump levels)"
          % (HEAT_PER_CBL_LEVEL, COOL_PER_PUMP_LEVEL))
    print("   %d records, maximum |error| = %r" % (len(ticks), worst))
    if worst != 0.0:
        print("   NOT EXACT -- the constant moved, or the field did")

    # The near-miss spellings.  An identity that three spellings satisfy has
    # not identified the game's own expression; the `power` one it REJECTS,
    # which is what makes the others worth reading.
    def count(fn):
        bad = 0
        for r in ticks:
            p = payload(r)
            if abs(p["predictions"]["predDT"] * 5.0 - fn(p)) > 0.5:
                bad += 1
        return len(ticks) - bad

    print("   also satisfied by:")
    print("     sum(cbl.level where active)   %d / %d"
          % (count(lambda p: HEAT_PER_CBL_LEVEL
                   * sum(l for l, a in zip(p["cbl"]["level"], p["cbl"]["active"])
                         if a)
                   - COOL_PER_PUMP_LEVEL * pump_sum(p)), len(ticks)))
    print("     coolant.sumLevel              %d / %d"
          % (count(lambda p: HEAT_PER_CBL_LEVEL * cbl_sum(p)
                   - COOL_PER_PUMP_LEVEL * p["coolant"]["sumLevel"]),
             len(ticks)))
    print("   and REJECTED by:")
    print("     sum(cbl.power), which is not the level   %d / %d"
          % (count(lambda p: HEAT_PER_CBL_LEVEL * sum(p["cbl"]["power"])
                   - COOL_PER_PUMP_LEVEL * pump_sum(p)), len(ticks)))
    print("   (so the log says `level`, and says nothing about whether a dark\n"
          "    laser contributes -- the two agree wherever both are defined)")


def reading_two(ticks):
    print("\n2. THE RECORDED INCREMENTS -- grouped by the level pair held")
    print("   The recorder samples faster than the game ticks, so a sample\n"
          "   whose `fluctuation` repeats the previous sample's is a settled\n"
          "   reading of one tick; those are what is grouped here.")
    groups = {}
    previous = None
    for r in ticks:
        p = payload(r)
        key = (cbl_sum(p), pump_sum(p))
        tremor = p["reactor"]["fluctuation"]
        if previous is not None and tremor == previous:
            groups.setdefault(key, []).append(tremor)
        previous = tremor

    print("\n   C  K    line    n  median     min     max")
    for key in sorted(groups, key=lambda k: -len(groups[k])):
        C, K = key
        values = groups[key]
        print("   %d  %d  %6.0f  %4d  %6.0f  %6.0f  %6.0f"
              % (C, K, line(C, K), len(values), statistics.median(values),
                 min(values), max(values)))
    settled = [(C, K, statistics.median(v)) for (C, K), v in groups.items()
               if statistics.median(v) != 0.0]
    close = [1 for (C, K, med) in settled if abs(med - line(C, K)) <= 100]
    print("\n   %d of the %d pairs with a non-zero settled reading sit within\n"
          "   100 degrees of the line (the game adds its own random term, and\n"
          "   the recording is a sample of it, not the arithmetic)"
          % (len(close), len(settled)))
    print("   The misses are NAMED rather than averaged away:")
    print("     * median exactly 0 -- the pre-start stretches (GameActive\n"
          "       false): the chamber is not being simulated, so nothing moves\n"
          "       whatever the line says.")
    print("     * C3 K9 -- the terminal collapse.  The line says %.0f, the\n"
          "       reading is about -436: a different regime, and the same\n"
          "       collapse the AVB tool names." % line(3, 9))

    # One clean pair, so the cooling side gets a number of its own rather than
    # only a table.  C is held at 15 and only K moves.
    c15 = {K: statistics.median(v) for (C, K), v in groups.items()
           if C == 15 and len(v) >= 4}
    if len(c15) >= 2:
        lo, hi = min(c15), max(c15)
        per = (c15[hi] - c15[lo]) / float(hi - lo)
        print("\n   The one same-C pair with enough samples: holding CBL at 15,\n"
              "   K %d -> %d moves the reading %.0f -> %.0f, i.e. %.1f a pump\n"
              "   level against the model's -%.0f"
              % (lo, hi, c15[lo], c15[hi], per, COOL_PER_PUMP_LEVEL))
        print("   BOUNDARY: those two stretches are far apart in time, so the\n"
              "   reactor's own drift is inside that difference.  It is a\n"
              "   consistent reading, not a second measurement of 120 -- the\n"
              "   exact identity in 1 is the one that pins the constant.")


def reading_three(ticks):
    print("\n3. THE PUMP LEVELS THIS RECORDING VISITS")
    levels = {}
    dark = 0
    for r in ticks:
        p = payload(r)
        for value in p["coolant"]["levels"]:
            levels[value] = levels.get(value, 0) + 1
        if cbl_sum(p) == 0 and pump_sum(p) > 0:
            dark += 1
    print("   per-pump levels seen: %s"
          % ", ".join("%d x%d" % (k, v) for k, v in sorted(levels.items())))
    print("   (0..3, which is the range Engine.luau:110 validates and the range\n"
          "    the console's radios carry)")
    print("   %d of %d records have the CBL dark with the pumps running"
          % (dark, len(ticks)))
    # CORRECTION 2026-10-16.  The count above is right and the sentence it was
    # closing with was not: it read "-- the case the placement decision turns
    # on: a dark laser bank must not silence the pumps, and here the game ran
    # that way."  Split by the log's own `stats.GameActive`, not one of those
    # records is a machine that was being simulated -- 62 are the pre-start
    # stretch (tempF 0, fluctuation 0, pumps at 1 each) and 22 the post-collapse
    # tail (tempF 1063, fluctuation -1255, pumps at 3 each).  The original
    # wording is kept because it was written from a real reading; what was wrong
    # is the inference, at the cost of one more field (CLAUDE.md 0.31 (1): a
    # number of the right SHAPE answering a question it cannot is exactly this
    # failure, and this instrument made it).
    #
    # The split was "79 ... and 5" in this comment's first draft, and both of
    # those were invented: they sum to 84, they sit in the right sentence, and
    # no criterion on those records produces them (checked, not assumed -- the
    # only split the data offers is 62/22, by pump level and by tempF alike).
    # The PRINTED counts were always measured; the prose wandered off them.
    # CLAUDE.md 0.18, and note which half of the writing that was.
    running = sum(1 for r in ticks
                  if cbl_sum(payload(r)) == 0 and pump_sum(payload(r)) > 0
                  and payload(r).get("stats", {}).get("GameActive"))
    print("   ...of which %d have stats.GameActive true, so the log does NOT\n"
          "   show the game cooling with the lasers dark (see\n"
          "   _tools/passive_from_log.py, which asks the same question of the\n"
          "   same field)" % running)
    print("   -- the case the placement decision turns on: a dark laser bank\n"
          "   must not silence the pumps.  The exact identity in 1 is what\n"
          "   carries that argument; this count does not.")


def main():
    allrecords = records()
    ticks = [r for r in allrecords if r["data"].get("type") == "tick"]
    kinds = {}
    for r in allrecords:
        kinds[r["data"].get("type")] = kinds.get(r["data"].get("type"), 0) + 1
    print("%s" % LOG)
    print("%d records: %s\n" % (len(allrecords),
                                ", ".join("%d %s" % (v, k) for k, v in
                                          sorted(kinds.items(),
                                                 key=lambda kv: -kv[1]))))
    reading_one(ticks)
    reading_two(ticks)
    reading_three(ticks)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:                  # a deliberate exit passes through
        raise
    except BaseException:               # noqa: BLE001 -- CLAUDE.md 0.6: an
        import traceback                # uncaught exception can leave rc = 0,
        traceback.print_exc()           # and "the reading crashed" then looks
        sys.exit(1)                     # byte-for-byte like "all clear".
