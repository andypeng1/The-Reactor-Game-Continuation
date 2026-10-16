#!/usr/bin/env python
"""passive_from_log.py -- does the shipped game cool with EVERYTHING off?

    python -X utf8 _tools/passive_from_log.py

The operator's 2026-10-16 spec puts the passive term OUTSIDE the lasers' off
rule and outside the quadratic:

    pure_cbl = {a_avg <= 0: 0, 0.0516*a_avg^2 + 1.1*a_avg + 426}
    dT       = {P <= 2200: -586, pure_cbl*p_mult + passive[s] - coolant + noise}

so a row's `passive` (-455.7 / -400 / -422 / -22) applies whether or not a
laser is lit.  That is a behaviour the panel has never had: until this spec the
row's whole contribution sat under gui.py's own "off is ours" gate, so a dark
console held still.

This file asks the shipped game -- `Data/DataCollection.Log` -- what it does
with every control off.  It is the same kind of reading as the two siblings
(`coolant_from_log.py`, `avb_from_log.py`): the log is the original recording
itself, and `reactor.fluctuation` is its own per-tick temperature increment.

Three readings, printed rather than asserted (a number that cannot go red is a
print, CLAUDE.md 0.31):

  1. the settled increments with CBL sum 0 and pump sum 0, split by whether the
     machine was running (`stats.GameActive`) -- because a cold machine sitting
     at 0 F before ignition would answer -0.0 and mean nothing by it;
  2. the same split by core state, since his `passive` is per row;
  3. the recorded `tempF` across those stretches, so the increment has a second
     witness: two fields have to agree before the number is a measurement
     (CLAUDE.md 0.14b).

ASCII only on stdout: this console is GBK.
"""

import io
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "Data", "DataCollection.Log")

STATE_MIN = 5600.0


def records():
    """The JSON records, with the ModuleScript wrapper taken off."""
    raw = io.open(LOG, encoding="utf-8").read()
    body = raw.split("[[==", 1)[1].rsplit("==]]", 1)[0]
    return [json.loads(line) for line in body.splitlines() if line.strip()]


def payload(record):
    return record["data"]["payload"]


def core_row(temp_f):
    if temp_f < 5600:
        return 0
    if temp_f < 17500:
        return 1
    if temp_f < 29500:
        return 2
    return 3


def main():
    ticks = []
    for index, record in enumerate(records()):
        p = payload(record)
        if "reactor" not in p or "cbl" not in p:
            continue
        reactor, cbl = p["reactor"], p["cbl"]
        if "fluctuation" not in reactor or "sumLevel" not in cbl:
            continue
        stats = p.get("stats", {})
        ticks.append({
            "index": index,
            "tempF": reactor.get("tempF"),
            "fluct": reactor["fluctuation"],
            "cbl": cbl["sumLevel"],
            "pump": p.get("coolant", {}).get("sumLevel"),
            "active": bool(stats.get("GameActive")),
        })

    print("%s\n%d records carrying both a CBL sum and a fluctuation\n"
          % (LOG, len(ticks)))

    both_off = [t for t in ticks if t["cbl"] == 0 and t["pump"] == 0]

    print("1. EVERY CONTROL OFF (cbl sum 0, pump sum 0) -- %d of them"
          % len(both_off))
    for name, group in (("running (GameActive true)",
                         [t for t in both_off if t["active"]]),
                        ("not running",
                         [t for t in both_off if not t["active"]])):
        if not group:
            print("   %-24s none" % name)
            continue
        print("   %-24s n = %-4d fluctuation: %s"
              % (name, len(group),
                 sorted(set(round(t["fluct"], 6) for t in group))))
        print("   %-24s tempF range %s .. %s"
              % ("", min(t["tempF"] for t in group),
                 max(t["tempF"] for t in group)))

    running = [t for t in both_off if t["active"]]
    print("\n2. THE RUNNING ONES, by his row (from tempF)")
    if not running:
        print("   none -- the log never holds the machine running with every "
              "control off")
    for row in (0, 1, 2, 3):
        group = [t for t in running if core_row(t["tempF"]) == row]
        if not group:
            continue
        print("   row %d   n = %-4d fluctuation %s   tempF %s .. %s"
              % (row, len(group),
                 sorted(set(round(t["fluct"], 6) for t in group)),
                 min(t["tempF"] for t in group), max(t["tempF"] for t in group)))

    print("\n3. TEMPERATURE ACROSS CONSECUTIVE RUNNING SAMPLES, all off")
    deltas = []
    for before, after in zip(ticks, ticks[1:]):
        if not (before["active"] and after["active"]):
            continue
        if before["cbl"] or after["cbl"] or before["pump"] or after["pump"]:
            continue
        if before["tempF"] is None or after["tempF"] is None:
            continue
        deltas.append((before["index"], after["index"],
                       after["tempF"] - before["tempF"],
                       before["fluct"], after["fluct"]))
    print("   %d consecutive pairs" % len(deltas))
    for index, nxt, delta, f_before, f_after in deltas[:12]:
        print("   %4d -> %4d   tempF moved %+8.3f   (fluctuation %+9.3f then "
              "%+9.3f)" % (index, nxt, delta, f_before, f_after))
    if len(deltas) > 12:
        print("   ... %d more" % (len(deltas) - 12))
    if deltas:
        print("   median tempF move %+.3f"
              % statistics.median(d[2] for d in deltas))

    # The section that SETTLES the claim core_model_check.py's coolant block
    # used to carry ("the shipped log has 84 records at CBL sum 0 with the pumps
    # running").  The count is right; the inference was not, and the field that
    # separates them is the same one section 1 splits on.
    #
    # It used to print nothing at all here, because every group it built was
    # empty -- and a section that prints nothing because its list was empty
    # reads exactly like a section that had nothing to ask (CLAUDE.md 0.20: the
    # empty set tells two lies, `all([])` is true and a silent absence is not a
    # reading).  Both sides now say "none" out loud.
    print("\n4. THE SAME QUESTION ONE STEP WIDER: cbl sum 0, pumps ON")
    wide = [t for t in ticks if t["cbl"] == 0 and t["pump"]]
    print("   %d record(s) with the lasers dark and the pumps running"
          % len(wide))
    for pump in sorted(set(t["pump"] for t in wide)):
        for name, group in (("running", [t for t in wide
                                         if t["pump"] == pump and t["active"]]),
                            ("not running", [t for t in wide if t["pump"] == pump
                                             and not t["active"]])):
            if not group:
                print("   pump sum %-2s  %-12s none" % (pump, name))
                continue
            print("   pump sum %-2s  %-12s n = %-4d fluctuation %s   (the 65/120 "
                  "line says %g)"
                  % (pump, name, len(group),
                     sorted(set(round(t["fluct"], 6) for t in group)),
                     -120.0 * pump))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:               # noqa: BLE001 -- CLAUDE.md 0.6
        import traceback
        traceback.print_exc()
        sys.exit(1)
