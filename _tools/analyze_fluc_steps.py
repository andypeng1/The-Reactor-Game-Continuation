"""Derive the per-sample ratio d = dPres / dTemp from Data/analyze/logs.csv.

The operator's rule, verbatim and in two passes:

    (1) 「相邻两个数据，如果不一样，就算deltapressure/deltatemperature(也就是fluc),
        只算连续升高处」
    (2) 「a b c  ... 而有 c_n = a_n - a_(n-1)；我要拉表格的内容就是
        d = (b_n - b_(n-1)) / c_n」

    walk ADJACENT samples, collapsing repeats; the gap between two samples is a
    step; per step the answer is the RATIO of the pressure change to the
    temperature change.

Pass (2) settled two things pass (1) left open, and both are recorded here:

  * THE SLASH IN 「deltapressure/deltatemperature」 IS A DIVISION, not a list.
    That is the whole deliverable: one column, d = dPres / dTemp.
  * `c_n` IS RECOMPUTED FROM THE TEMPERATURES, not read out of the file's third
    column.  The operator writes c_n = a_n - a_(n-1) as the definition.  The
    file's own `Fluc` column agrees with that definition on 239 of 278 steps and
    disagrees on 39 -- one contiguous window, 16:29:28..16:30:08, whose edges sit
    exactly where `Pres` freezes at 5007, and over which the two columns sum to
    OPPOSITE signs (fluc +1113 vs dTemp -6735).  So anything that pulls the
    file's third column straight into a spreadsheet gets those 39 rows wrong;
    this script's `c` column is the correct one and `fluc` is carried beside it
    so the divergence stays visible.  The mechanism is not established.

Three further choices the wording does not settle, made explicit rather than
folded into the answer:

  1. IDENTICAL NEIGHBOURS ARE ONE SAMPLE, NOT A ZERO STEP.  The capture polls
     faster than the game ticks, so most values appear on two consecutive rows.
     The file's `Fluc` column carries the previous delta forward across a repeat
     (16:27:14 and 16:27:15 both say 90), which is what says a repeat is the
     same sample seen twice rather than a step of zero.  So the walk is over
     DEDUPLICATED samples: 444 rows -> 279 samples -> 278 steps.
  2. ROW 1 HAS NO PREVIOUS SAMPLE, so it has no c and no d.  That is the
     `/nil/` in the operator's own table, and it is why the table has one more
     row than there are steps.
  3. 「连续升高」 HAS TWO READINGS.  A = every step whose dTemp is positive,
     isolated rises included.  B = only steps inside a maximal run of two or
     more consecutive rises (a lone rise is not 连续).  Both are emitted; a
     zero step breaks a run in both.

Usage:  python analyze_fluc_steps.py [logs.csv] [outdir]
"""
import csv
import io
import os
import sys

HEADER = ["n", "Time", "Temp", "Pres", "c", "fluc", "dPres", "d",
          "T_rise", "T_run", "P_rise", "P_run", "fluc_eq_c"]

LEGEND = ("  a = Temp   b = Pres   c = dTemp (recomputed)   d = dPres / c\n"
          "  `fluc` is the file's own third column, kept beside c, not used as c.")


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


def build_rows(samples):
    """One row per SAMPLE, indexed n = 1..N.

    Indexed by sample rather than by step because that is the table the
    operator wrote: row 1 is a real reading that simply has nothing before it,
    so c and d are empty there rather than absent from the table.
    """
    rows = []
    for i, s in enumerate(samples):
        prev = samples[i - 1] if i else None
        c = None if prev is None else s["temp"] - prev["temp"]
        dp = None if prev is None else s["pres"] - prev["pres"]
        # `not c` covers both "no previous sample" and "c == 0" -- a genuine
        # divide-by-zero, not a value to invent.  Left empty on purpose.
        d = None if not c else dp / c
        rows.append({"n": i + 1, "t": s["t"], "temp": s["temp"], "pres": s["pres"],
                     "fluc": s["fluc"], "c": c, "dP": dp, "d": d})
    return rows


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


def fmt(v):
    # `v == 0` catches -0.0: a step where the pressure did not move divides a
    # negative denominator into a negative zero, which reaches a spreadsheet as
    # the text "-0" rather than the number 0.
    if v is None:
        return ""
    if v == 0:
        return "0"
    return "%.10g" % v


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else r"D:\rblxTRGproject\Data\analyze\logs.csv"
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(src))

    header, body = load(src)
    samples = dedupe(body)
    rows = build_rows(samples)

    steps = [r for r in rows if r["c"] is not None]

    # run membership, computed once, read by both the report and the CSV
    for key, letter in (("c", "T"), ("dP", "P")):
        member = set()
        for run in runs(steps, key):
            for s in run:
                member.add(id(s))
        for s in steps:
            s[letter + "_rise"] = s[key] > 0
            s[letter + "_run"] = id(s) in member
    for r in rows:
        for letter in ("T", "P"):
            r.setdefault(letter + "_rise", False)
            r.setdefault(letter + "_run", False)

    # ---------- report -----------------------------------------------------
    print("source      : %s" % src)
    print("columns     : %s" % header)
    print(LEGEND)
    print("rows        : %d" % (len(body) + 1))
    print("samples     : %d distinct  (%d repeats collapsed)"
          % (len(samples), len(body) - len(samples)))
    print("steps       : %d  (every sample except the first)" % len(steps))

    # Cheap invariant, and independent of the run/branch logic below: the steps
    # telescope, so every dTemp must sum to last_temp - first_temp.
    for key, col in (("c", "temp"), ("dP", "pres")):
        total = sum(s[key] for s in steps)
        span = samples[-1][col] - samples[0][col]
        print("telescope %-4s: sum %+6d  ==  last-first %+6d  -> %s"
              % (key, total, span, "ok" if total == span else "MISMATCH"))

    mism = [s for s in steps if s["c"] != s["fluc"]]
    print("fluc == c                : %d of %d  (%d differ)"
          % (len(steps) - len(mism), len(steps), len(mism)))
    if mism:
        print("   first %s   last %s" % (mism[0]["t"], mism[-1]["t"]))

    # the ratio, and what the means are taken over
    print()
    print("== d = dPres / c ==")
    zero = [s for s in steps if s["c"] == 0]
    print("   c == 0 (d undefined) : %d step%s%s"
          % (len(zero), "" if len(zero) == 1 else "s",
             "" if not zero else "   at %s" % ", ".join(s["t"] for s in zero)))
    groups = [("all steps with c /= 0", [s for s in steps if s["c"] != 0]),
              ("A  c > 0 (every rise)", [s for s in steps if s["c"] > 0]),
              ("B  c > 0 inside a run >= 2",
               [s for r in runs(steps, "c") for s in r])]

    def quant(vals, t):
        return vals[min(len(vals) - 1, int(t * (len(vals) - 1)))]

    for name, sel in groups:
        vals = sorted(s["d"] for s in sel)
        print("   %-28s n=%-4d mean %+11.5g  median %+11.5g  p10 %+11.5g  p90 %+11.5g"
              % (name, len(vals), sum(vals) / len(vals),
                 quant(vals, .5), quant(vals, .1), quant(vals, .9)))

    # THE DENOMINATOR IS THE MEASURED OBJECT, and it gets small.  A step where
    # the temperature barely moves divides by almost nothing, so a handful of
    # steps carry the mean -- over the rising steps it even flips its sign
    # against the median.  Said out loud so the mean is not read as "the
    # typical step"; the median and the p10/p90 above are what describe one.
    posr = [s for s in steps if s["c"] > 0]
    for label, sel in (("|c| <= 20", [s for s in posr if s["c"] <= 20]),
                       ("|d| > 1", [s for s in posr if abs(s["d"]) > 1])):
        print("   %-20s : %d of %d rising steps  -> mean is set by these"
              % (label, len(sel), len(posr)))

    # 「平均」 also reads as one ratio over the whole group -- total pressure
    # change divided by total temperature change -- which is NOT the mean of
    # the per-step ratios and is not close to it.  Both are cheap, so both are
    # given rather than one being chosen on the reader's behalf.
    print("   pooled sum(dPres)/sum(c): %s"
          % "   ".join("%s %+.5g" % (n, sum(s["dP"] for s in sel) / sum(s["c"] for s in sel))
                       for n, sel in (("all", groups[0][1]), ("A", groups[1][1]),
                                      ("B", groups[2][1]))))
    print()
    for key, name in (("c", "dTemp"), ("dP", "dPres")):
        letter = "T" if key == "c" else "P"
        rises = [s for s in steps if s[key] > 0]
        runst = runs(steps, key)
        inside = [s for r in runst for s in r]
        print("== %s ==" % name)
        print("   steps               : %d  (rise %d / fall %d / equal %d)"
              % (len(steps), len(rises),
                 sum(1 for s in steps if s[key] < 0),
                 sum(1 for s in steps if s[key] == 0)))
        print("   A  every rise        : %d steps, sum %+d"
              % (len(rises), sum(s[key] for s in rises)))
        print("   B  inside a run >= 2 : %d steps, sum %+d, in %d runs"
              % (len(inside), sum(s[key] for s in inside), len(runst)))
        print("      dropped vs A      : %d steps, sum %+d"
              % (len(rises) - len(inside),
                 sum(s[key] for s in rises) - sum(s[key] for s in inside)))
        print()

    # ---------- outputs ----------------------------------------------------
    def row_of(s):
        return [s["n"], s["t"], s["temp"], s["pres"], fmt(s["c"]), s["fluc"],
                fmt(s["dP"]), fmt(s["d"]),
                int(s["T_rise"]), int(s["T_run"]),
                int(s["P_rise"]), int(s["P_run"]),
                "" if s["c"] is None else int(s["c"] == s["fluc"])]

    all_path = os.path.join(outdir, "steps_all.csv")
    with open(all_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for s in rows:
            w.writerow(row_of(s))
    print("wrote %s  (%d rows + header)" % (all_path, len(rows)))

    rise_path = os.path.join(outdir, "rise_steps.csv")
    with open(rise_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for s in steps:
            if s["T_rise"] or s["P_rise"]:
                w.writerow(row_of(s))
    print("wrote %s" % rise_path)

    # The means on their own, because "样本平均" is a thing to pull into a
    # sheet and a mean buried mid-report is a mean someone re-derives by hand.
    sum_path = os.path.join(outdir, "d_summary.txt")
    with open(sum_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("d = (b_n - b_(n-1)) / c_n,  c_n = a_n - a_(n-1)\n")
        fh.write("source: %s   rows %d -> %d samples -> %d steps\n"
                 % (os.path.basename(src), len(body), len(samples), len(steps)))
        fh.write(LEGEND + "\n")
        fh.write("\n%-30s %6s %14s %14s %14s %14s %14s %14s\n"
                 % ("group", "n", "mean", "median", "p10", "p90", "min", "max"))
        for name, sel in groups:
            vals = sorted(s["d"] for s in sel)
            fh.write("%-30s %6d %14.8g %14.8g %14.8g %14.8g %14.8g %14.8g\n"
                     % (name, len(vals), sum(vals) / len(vals),
                        quant(vals, .5), quant(vals, .1), quant(vals, .9),
                        vals[0], vals[-1]))
        fh.write("\nNOTE: the denominator is the measured object and it gets small --"
                 " a step where\nc barely moves divides by almost nothing. "
                 "The mean is set by those steps\n(see |d| > 1 below); median/p10/p90 "
                 "describe a typical step.\n")
        posr = [s for s in steps if s["c"] > 0]
        fh.write("c == 0 (d undefined): %d step%s\n"
                 % (len(zero), "" if not zero else "  at " + ", ".join(s["t"] for s in zero)))
        fh.write("|c| <= 20: %d of %d rising steps; |d| > 1: %d of %d\n"
                 % (sum(1 for s in posr if s["c"] <= 20), len(posr),
                    sum(1 for s in posr if abs(s["d"]) > 1), len(posr)))
        fh.write("\n「平均」 read the other way -- ONE ratio over the whole group,\n"
                 "sum(dPres)/sum(c), not the mean of the per-step ratios:\n")
        for name, sel in groups:
            fh.write("  %-30s %14.8g\n"
                     % (name, sum(s["dP"] for s in sel) / sum(s["c"] for s in sel)))
    print("wrote %s" % sum_path)


if __name__ == "__main__":
    main()
