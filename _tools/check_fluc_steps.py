"""Verify analyze_fluc_steps.py, and prove each check has teeth.

The deliverable's numbers are only as good as the reader that produced them,
and this reader makes several choices the operator's sentence did not settle
(dedupe, the two readings of 连续升高, which column is `c`, and what row 1
means).  So each claim gets a mutation that targets it: if a check cannot be
made to fail, it is decoration.

Run:  python check_fluc_steps.py [logs.csv]
"""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_fluc_steps as A  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:\rblxTRGproject\Data\analyze\logs.csv"

passed = []
failed = []


def check(name, ok, detail=""):
    (passed if ok else failed).append(name)
    print("  %-36s %s %s" % (name, "ok" if ok else "FAIL", detail))


def analyse(body, dedupe=True):
    samples = A.dedupe(body) if dedupe else [
        {"t": r[0], "temp": int(r[1]), "pres": int(r[2]), "fluc": int(r[3])}
        for r in body]
    steps = [{"t": c["t"], "fluc": c["fluc"],
              "dT": c["temp"] - p["temp"], "dP": c["pres"] - p["pres"]}
             for p, c in zip(samples, samples[1:])]
    return samples, steps


def rising(steps, key):
    """A and B, as the deliverable defines them."""
    a = [s for s in steps if s[key] > 0]
    b = [s for r in A.runs(steps, key) for s in r]
    return a, b


def main():
    header, body = A.load(SRC)
    samples, steps = analyse(body)
    rows = A.build_rows(samples)
    dsteps = [r for r in rows if r["c"] is not None]

    # ---- the claims, on the real file ------------------------------------
    check("header is Time/Temp/Pres/Fluc", header == ["Time", "Temp", "Pres", "Fluc"])
    check("444 rows", len(body) == 444, "got %d" % len(body))
    check("279 distinct samples", len(samples) == 279, "got %d" % len(samples))
    check("278 steps", len(steps) == 278, "got %d" % len(steps))
    check("279 table rows, n = 1..279",
          [r["n"] for r in rows] == list(range(1, 280)))

    # telescope: every delta sums to last-first.
    for key, col in (("c", "temp"), ("dP", "pres")):
        total = sum(s[key] for s in dsteps)
        span = samples[-1][col] - samples[0][col]
        check("telescope %s" % key, total == span, "%d vs %d" % (total, span))

    mism = [s for s in dsteps if s["c"] != s["fluc"]]
    check("fluc == c on 239/278", len(mism) == 39, "%d differ" % len(mism))
    check("mismatch is one window",
          {s["t"] for s in mism} == {s["t"] for s in dsteps
                                     if "16:29:28" <= s["t"] <= "16:30:08"},
          "%s .. %s" % (mism[0]["t"], mism[-1]["t"]))
    # The window is dark: fluc says up, the temps say down.  If this ever flips
    # to the same sign the block is no longer special and the story is wrong.
    check("window signs disagree",
          sum(s["fluc"] for s in mism) > 0 > sum(s["c"] for s in mism),
          "fluc %+d vs c %+d" % (sum(s["fluc"] for s in mism),
                                 sum(s["c"] for s in mism)))
    check("1 rising step affected",
          sum(1 for s in mism if s["c"] > 0) == 1,
          "%d" % sum(1 for s in mism if s["c"] > 0))

    def counts(key, want_a, want_b):
        a, b = rising(steps, key)
        return len(a) == want_a and len(b) == want_b

    check("dTemp A=109 B=83", counts("dT", 109, 83))
    check("dPres A=82 B=81", counts("dP", 82, 81))
    # B is a strict subset of A by construction -- a FOLLOW, which must stay
    # green under every mutant below.
    for key in ("dT", "dP"):
        a, b = rising(steps, key)
        check("B subset of A (%s)" % key, set(map(id, b)) <= set(map(id, a)))

    # ---- the ratio d = dPres / c -----------------------------------------
    check("row 1 has no c and no d",
          rows[0]["c"] is None and rows[0]["d"] is None,
          "c=%r d=%r" % (rows[0]["c"], rows[0]["d"]))
    # Recomputed here from the row's own fields, so it pins the definition
    # rather than the arithmetic that produced it.
    bad = [r for r in dsteps if r["c"] != 0 and r["d"] != r["dP"] / r["c"]]
    check("d == dPres / c on all 277", not bad, "%d bad" % len(bad))
    zero = [r for r in dsteps if r["c"] == 0]
    check("c == 0 on exactly 1 step, d empty",
          len(zero) == 1 and zero[0]["d"] is None,
          "%d zero, d=%r" % (len(zero), zero[0]["d"] if zero else None))

    # The operator's own five-row excerpt, located by its own numbers: a, b,
    # then the next four steps' c and d, exactly as he wrote them.
    i = next(k for k, s in enumerate(samples)
             if s["temp"] == 8264 and s["pres"] == 3507)
    got_c = [r["c"] for r in rows[i + 1:i + 5]]
    got_d = [r["d"] for r in rows[i + 1:i + 5]]
    check("his excerpt: c = 267,159,279,282", got_c == [267, 159, 279, 282], "%s" % got_c)
    check("his excerpt: d = 4/267 .. 12/282",
          got_d == [4 / 267, 6 / 159, 10 / 279, 12 / 282], "%s" % got_d)

    # The table goes into a spreadsheet, so a negative zero is a real defect:
    # `-0` reads as text there, not as the number 0.  A step where the pressure
    # did not move over a negative denominator produces exactly that float.
    # Rendered through the same function the CSV writer uses, so this is the
    # cell text and not a proxy for it.
    cells = [A.fmt(r["d"]) for r in dsteps]
    check("no '-0' rendered into the d column", "-0" not in cells,
          "%d cells" % len(cells))
    check("fmt folds -0.0 to '0'",
          A.fmt(-0.0) == "0" and A.fmt(0.0) == "0" and A.fmt(-0.5) == "-0.5",
          "%r %r %r" % (A.fmt(-0.0), A.fmt(0.0), A.fmt(-0.5)))

    # A / B means and the pooled ratio -- printed, and pinned so a change in
    # either reading of 「平均」 cannot slip through unnoticed.
    def group(sel):
        vals = sorted(s["d"] for s in sel)
        return sum(vals) / len(vals), vals[len(vals) // 2]

    a_mean, a_med = group([s for s in dsteps if s["c"] > 0])
    b_mean, _ = group([s for r in A.runs(dsteps, "c") for s in r])
    check("A mean -1.0608 vs median +0.01498",
          abs(a_mean + 1.0608425) < 1e-6 and abs(a_med - 0.0149812734) < 1e-9,
          "mean %+.6g median %+.6g" % (a_mean, a_med))
    check("B mean -0.79845", abs(b_mean + 0.79845432) < 1e-6, "%+.6g" % b_mean)
    # The two readings of 「平均」 disagree by a factor of ~17: where the mean is
    # set by the small denominators, the pooled ratio is not.  Both are right
    # answers to different questions, so the gap is the thing worth pinning.
    pooled = sum(s["dP"] for s in dsteps if s["c"] > 0) / sum(
        s["c"] for s in dsteps if s["c"] > 0)
    check("pooled sum(dPres)/sum(c) = -0.06384",
          abs(pooled + 0.063841095) < 1e-8, "%+.8g" % pooled)

    # ---- mutants: each must redden its own check --------------------------
    print()
    print("  -- mutations --")

    # 1. no dedup: repeats become zero steps.  The Fluc oracle is what catches
    #    it, because a repeat carries the previous delta forward, not 0.
    _, m = analyse(body, dedupe=False)
    mm = [s for s in m if s["dT"] != s["fluc"]]
    check("mut nodedupe -> fluc oracle red",
          len(m) != 278 and len(mm) != 39,
          "%d steps, %d differ" % (len(m), len(mm)))

    # 2. the telescope is a TAUTOLOGY over the step list: any set of consecutive
    #    differences sums to last minus first, so editing the input cannot move
    #    it.  (A mutant that deletes a raw row stays green -- tried, and that
    #    green is correct, not a miss.)  What it DOES cover is a walk that is not
    #    a walk, so that is what the mutant has to break: pair each sample with
    #    the one after next.
    strided = [samples[i + 2]["temp"] - samples[i]["temp"]
               for i in range(0, len(samples) - 2)]
    check("mut strided walk -> telescope red",
          sum(strided) != samples[-1]["temp"] - samples[0]["temp"],
          "%d vs %d" % (sum(strided), samples[-1]["temp"] - samples[0]["temp"]))

    # 3. the competing explanation of the same column: "Fluc is dTemp one step
    #    late".  It must fit strictly worse than reading it in place.
    lag = sum(1 for i in range(1, len(steps))
              if steps[i]["fluc"] == steps[i - 1]["dT"])
    check("mut lag-by-one -> worse fit", lag < 239,
          "%d steps match a lag vs 239 in place" % lag)

    # 4. run threshold 1 instead of 2: B must equal A, so the A=109 B=83 pair
    #    is what says the strict reading is the one in force.
    def runs1(steps_, key):
        out, cur = [], []
        for s in steps_:
            if s[key] > 0:
                cur.append(s)
            else:
                if cur:
                    out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return out
    b1 = [s for r in runs1(steps, "dT") for s in r]
    check("mut runs>=1 -> B becomes A", len(b1) == 109, "%d" % len(b1))

    # 5. the ratio inverted (d = c / dPres).  Every downstream summary moves,
    #    so the d == dPres / c check is the one that has to catch it.
    inv = [r for r in dsteps if r["dP"] != 0 and r["c"] / r["dP"] != r["d"]]
    check("mut invert d = c/dPres -> red", len(inv) == len(
        [r for r in dsteps if r["dP"] != 0]), "%d differ" % len(inv))

    # 6. the file's own column used as the denominator instead of the
    #    recomputed difference.  This is the one that caught ME: I wrote the
    #    mutant expecting all 39 diverging steps to move, and it came back with
    #    1.  The reason is the denominator-vs-measured-object family again --
    #    38 of the 39 sit inside the frozen-pressure window, where dP == 0, and
    #    0 over anything is 0.  So the column choice moves exactly ONE row.
    dz = [r for r in mism if r["dP"] == 0]
    check("38 of the 39 divergences have dP == 0", len(dz) == 38, "%d" % len(dz))
    flipped = [r for r in dsteps if r["fluc"] != 0 and r["dP"] / r["fluc"] != r["d"]]
    ok = ([r["n"] for r in flipped] == [78]
          and abs(flipped[0]["d"] - 0.9635634) < 1e-6
          and abs(flipped[0]["dP"] / flipped[0]["fluc"] - 0.8981132) < 1e-6)
    check("mut fluc-as-c -> only n=78 moves", ok,
          "moved n=%s" % [r["n"] for r in flipped])

    # 7. row 1 collapsed to a step of zero instead of "no predecessor".  The
    #    operator's own table writes /nil/ there; a 0 would be a reading nobody
    #    took.  Rebuild the first row the wrong way and ask the same question.
    def build_wrong_first(samples_):
        out = []
        for i, s in enumerate(samples_):
            prev = samples_[i - 1] if i else s
            c = s["temp"] - prev["temp"]
            dp = s["pres"] - prev["pres"]
            out.append({"n": i + 1, "t": s["t"], "temp": s["temp"],
                        "pres": s["pres"], "fluc": s["fluc"], "c": c, "dP": dp,
                        "d": None if not c else dp / c})
        return out
    w = build_wrong_first(samples)[0]
    check("mut row1 gets c=0 -> red on shape",
          not (w["c"] is None and w["d"] is None),
          "row 1 c=%r d=%r" % (w["c"], w["d"]))

    print()
    print("RESULT: %d ok, %d FAILED" % (len(passed), len(failed)))
    if failed:
        for f in failed:
            print("  FAILED: %s" % f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
