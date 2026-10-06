"""Derive dTemp / dPres between adjacent distinct samples of Data/analyze/logs.csv.

The rule the operator gave, verbatim:

    「相邻两个数据，如果不一样，就算deltapressure/deltatemperature(也就是fluc),
      只算连续升高处」

    walk ADJACENT samples; when two differ, the step between them is a delta
    (deltapressure and deltatemperature); only count the rises.

Three decisions that the wording does not settle, each made explicit rather
than folded into the answer -- see the README beside the output:

  1. IDENTICAL NEIGHBOURS ARE ONE SAMPLE, NOT A ZERO STEP.  The capture polls
     faster than the game ticks, so most values appear on two consecutive rows.
     The file's own `Fluc` column carries the previous delta forward across a
     repeat (16:27:14 and 16:27:15 both say 90), which is what says a repeat is
     the same sample seen twice rather than a step of zero.  So the walk is over
     DEDUPLICATED samples: 444 rows -> 279 samples -> 278 steps.
  2. 「连续升高」 HAS TWO READINGS.  A = every step whose delta is positive,
     isolated rises included.  B = only steps inside a maximal run of two or
     more consecutive rises (a lone rise is not 连续).  Both are emitted; a
     zero step breaks a run in both.
  3. THE FILE'S `Fluc` COLUMN IS NOT ALWAYS THE TEMPERATURE DELTA.  It equals
     the recomputed dTemp on 239 of 278 steps and disagrees on 39, all inside
     one contiguous window (16:29:28..16:30:08) that begins and ends exactly
     where `Pres` sits frozen at 5007.  Over that window the `Fluc` values sum
     to +1113 while the visible Temp falls 6982 -- opposite signs, so the two
     columns are not describing the same quantity there.  The mechanism is not
     established.  Both numbers are carried in the output so the mismatch stays
     visible instead of being silently resolved.

Usage:  python analyze_fluc_steps.py [logs.csv] [outdir]
"""
import csv
import io
import os
import sys

HEADER = ["Time", "Temp", "Pres", "Fluc", "dTemp", "dPres",
          "T_rise", "T_run", "P_rise", "P_run", "fluc_eq_dTemp"]


def load(path):
    """Rows are utf-8-sig (the file opens with a BOM) and CRLF-quoted."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    return rows[0], [r for r in rows[1:] if len(r) == 4 and r[0]]


def dedupe(body):
    out = []
    for t, temp, pres, fluc in body:
        temp, pres, fluc = int(temp), int(pres), int(fluc)
        if out and out[-1]["temp"] == temp and out[-1]["pres"] == pres:
            out[-1]["rows"] += 1
            out[-1]["last"] = t
            continue
        out.append({"t": t, "last": t, "temp": temp, "pres": pres,
                    "fluc": fluc, "rows": 1})
    return out


def runs(steps, key):
    """Maximal runs of >= 2 consecutive rises; a zero or a fall ends a run."""
    out, cur = [], []
    for s in steps:
        if s[key] > 0:
            cur.append(s)
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
    if len(cur) >= 2:
        out.append(cur)
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else r"D:\rblxTRGproject\Data\analyze\logs.csv"
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(src))

    header, body = load(src)
    samples = dedupe(body)

    steps = []
    for prev, cur in zip(samples, samples[1:]):
        steps.append({
            "t": cur["t"], "temp": cur["temp"], "pres": cur["pres"],
            "fluc": cur["fluc"],
            "dT": cur["temp"] - prev["temp"],
            "dP": cur["pres"] - prev["pres"],
        })

    # run membership, computed once, read by both the report and the CSV
    for key, letter in (("dT", "T"), ("dP", "P")):
        member = set()
        for run in runs(steps, key):
            for s in run:
                member.add(id(s))
        for s in steps:
            s[letter + "_rise"] = s[key] > 0
            s[letter + "_run"] = id(s) in member

    # ---------- report -----------------------------------------------------
    print("source      : %s" % src)
    print("columns     : %s" % header)
    print("rows        : %d" % (len(body) + 1))
    print("samples     : %d distinct  (%d repeats collapsed)"
          % (len(samples), len(body) - len(samples)))
    print("steps       : %d" % len(steps))

    # Cheap invariant, and independent of the run/branch logic below: the steps
    # telescope, so every dT must sum to last_temp - first_temp.  If a row were
    # dropped or a repeat counted twice, this is what would catch it.
    for key, col in (("dT", "temp"), ("dP", "pres")):
        total = sum(s[key] for s in steps)
        span = samples[-1][col] - samples[0][col]
        print("telescope %-4s: sum %+6d  ==  last-first %+6d  -> %s"
              % (key, total, span, "ok" if total == span else "MISMATCH"))

    mism = [s for s in steps if s["dT"] != s["fluc"]]
    print("Fluc == dTemp            : %d of %d  (%d differ)"
          % (len(steps) - len(mism), len(steps), len(mism)))
    if mism:
        print("   first %s   last %s" % (mism[0]["t"], mism[-1]["t"]))
        print("   sum(Fluc) %+d  vs  sum(dTemp) %+d  over the differing steps"
              % (sum(s["fluc"] for s in mism), sum(s["dT"] for s in mism)))

    print()
    for key, name in (("dT", "dTemp"), ("dP", "dPres")):
        letter = "T" if key == "dT" else "P"
        rises = [s for s in steps if s[key] > 0]
        runst = runs(steps, key)
        inside = [s for r in runst for s in r]
        zero = [s for s in steps if s[key] == 0]
        print("== %s ==" % name)
        print("   steps               : %d  (rise %d / fall %d / equal %d)"
              % (len(steps), len(rises),
                 sum(1 for s in steps if s[key] < 0), len(zero)))
        print("   A  every rise        : %d steps, sum %+d, median %+d, max %+d"
              % (len(rises), sum(s[key] for s in rises),
                 sorted(s[key] for s in rises)[len(rises) // 2],
                 max(s[key] for s in rises)))
        print("   B  inside a run >= 2 : %d steps, sum %+d, in %d runs"
              % (len(inside), sum(s[key] for s in inside), len(runst)))
        print("      dropped vs A      : %d steps, sum %+d"
              % (len(rises) - len(inside),
                 sum(s[key] for s in rises) - sum(s[key] for s in inside)))
        print("   first rise %s  last rise %s"
              % (rises[0]["t"], rises[-1]["t"]))
        print()

    # ---------- outputs ----------------------------------------------------
    csv_path = os.path.join(outdir, "rise_steps.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for s in steps:
            if s["T_rise"] or s["P_rise"]:
                w.writerow([s["t"], s["temp"], s["pres"], s["fluc"],
                            s["dT"], s["dP"],
                            int(s["T_rise"]), int(s["T_run"]),
                            int(s["P_rise"]), int(s["P_run"]),
                            int(s["dT"] == s["fluc"])])
    print("wrote %s" % csv_path)

    all_path = os.path.join(outdir, "steps_all.csv")
    with open(all_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for s in steps:
            w.writerow([s["t"], s["temp"], s["pres"], s["fluc"],
                        s["dT"], s["dP"],
                        int(s["T_rise"]), int(s["T_run"]),
                        int(s["P_rise"]), int(s["P_run"]),
                        int(s["dT"] == s["fluc"])])
    print("wrote %s" % all_path)


if __name__ == "__main__":
    main()
