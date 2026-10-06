"""Verify analyze_fluc_steps.py, and prove each check has teeth.

The deliverable's numbers are only as good as the reader that produced them,
and this reader makes several choices the operator's sentence did not settle
(dedupe, the two readings of 连续升高, which column is `c`, and what row 1
means).  So each claim gets a mutation that targets it: if a check cannot be
made to fail, it is decoration.

TWO CAPTURES, and they are not the same animal.  logs.csv is a long,
noisy shift with 39 divergences in it; logs.txt is a 91-second monotone
runaway.  Three choices that were load-bearing on the first are invisible
on the second, and those three are checked AS follows -- green, with the
reason written down -- rather than quietly dropped.

Run:  python check_fluc_steps.py [logs.csv|logs.txt]
"""
import contextlib
import csv
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_fluc_steps as A  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:\rblxTRGproject\Data\analyze\logs.csv"

# Both live in Data/analyze.  The checker dispatches on the shape A.load sniffed
# rather than on the extension, so a renamed copy is still read correctly -- and
# the discriminator itself is checked in dispatch_claims().
LOGS_CSV = r"D:\rblxTRGproject\Data\analyze\logs.csv"
LOGS_TXT = r"D:\rblxTRGproject\Data\analyze\logs.txt"

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


def runs1(steps, key):
    """The run test with the threshold lowered to 1 -- i.e. every rise.

    Only used to show what the threshold is holding back.  On logs.csv that
    is 26 steps; on logs.txt it is nothing at all.
    """
    out, cur = [], []
    for s in steps:
        if s[key] > 0:
            cur.append(s)
        else:
            if cur:
                out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    ax = sum((x - mx) ** 2 for x in xs) ** .5
    ay = sum((y - my) ** 2 for y in ys) ** .5
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (ax * ay)


def csv_claims(header, body):
    """The four-column capture: 444 rows over a shift, and the mutants.

    Unchanged from when this file was a single main(); the header argument is
    what used to be read off SRC directly.
    """
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

    def q(vals, t):
        return vals[min(len(vals) - 1, int(t * (len(vals) - 1)))]

    a_mean, a_med = group([s for s in dsteps if s["c"] > 0])
    b_sel = [s for r in A.runs(dsteps, "c") for s in r]
    b_vals = sorted(s["d"] for s in b_sel)
    b_mean = sum(b_vals) / len(b_vals)
    check("A mean -1.0608 vs median +0.01498",
          abs(a_mean + 1.0608425) < 1e-6 and abs(a_med - 0.0149812734) < 1e-9,
          "mean %+.6g median %+.6g" % (a_mean, a_med))

    # B is the reading the operator chose -- 「只算连续升高处」 -- so its whole row
    # is pinned rather than just its mean: these are the numbers that go out.
    # The mean carries the same small-denominator caveat as A (c = 1 on one step
    # gives d = -34), so the median is what describes a typical step.
    check("B mean -0.79845", abs(b_mean + 0.79845432) < 1e-6, "%+.6g" % b_mean)
    check("B median +0.0636943, min -34, max +3.0769231",
          abs(b_vals[len(b_vals) // 2] - 0.06369426752) < 1e-9
          and b_vals[0] == -34 and abs(b_vals[-1] - 3.0769231) < 1e-7,
          "%+.8g %+g %+g" % (b_vals[len(b_vals) // 2], b_vals[0], b_vals[-1]))
    check("B p10 -1.3684211, p90 +0.3030303",
          abs(q(b_vals, .1) + 1.3684211) < 1e-7 and abs(q(b_vals, .9) - 0.3030303) < 1e-7,
          "%+.8g %+.8g" % (q(b_vals, .1), q(b_vals, .9)))
    check("B sum(c) = +14225, sum(dP) = +199",
          sum(s["c"] for s in b_sel) == 14225 and sum(s["dP"] for s in b_sel) == 199,
          "%+d %+d" % (sum(s["c"] for s in b_sel), sum(s["dP"] for s in b_sel)))

    # The run test is keyed on the TEMPERATURE delta, because 「升温」 names the
    # temperature column.  All three candidate keys give a different set, so the
    # key is doing work rather than being a detail of phrasing: keying on the
    # pressure delta would answer a different question (81 steps) and keying on
    # the file's own column a third (98).  This is what says the 83 above is the
    # temperature reading specifically.
    keys = {k: [s for r in A.runs(dsteps, k) for s in r] for k in ("c", "dP", "fluc")}
    check("run key c/dP/fluc -> 83/81/98",
          [len(keys["c"]), len(keys["dP"]), len(keys["fluc"])] == [83, 81, 98],
          "%s" % {k: len(v) for k, v in keys.items()})
    art = [s for s in dsteps if s["c"] > 0]
    check("B drops 26 lone rises from A, sum +828",
          len(art) - len(b_sel) == 26
          and sum(s["c"] for s in art) - sum(s["c"] for s in b_sel) == 828,
          "%d steps, sum %+d" % (len(art) - len(b_sel),
                                 sum(s["c"] for s in art) - sum(s["c"] for s in b_sel)))

    # The two readings of 「平均」 disagree by a factor of ~17: where the mean is
    # set by the small denominators, the pooled ratio is not.  Both are right
    # answers to different questions, so the gap is the thing worth pinning.
    pooled = sum(s["dP"] for s in dsteps if s["c"] > 0) / sum(
        s["c"] for s in dsteps if s["c"] > 0)
    check("pooled sum(dPres)/sum(c) = -0.06384",
          abs(pooled + 0.063841095) < 1e-8, "%+.8g" % pooled)
    b_pool = sum(s["dP"] for s in b_sel) / sum(s["c"] for s in b_sel)
    check("B pooled sum(dPres)/sum(c) = +0.0139895",
          abs(b_pool - 0.01398945518) < 1e-8, "%+.8g" % b_pool)

    # Choosing B rather than A is not cosmetic: it decides the SIGN of the
    # pooled ratio.  The 26 steps the run test drops are shallow in temperature
    # (+828 over 26 steps) and steep in pressure (-1160), so including them
    # drags sum(dPres)/sum(c) from +0.01399 to -0.06384.  Said out loud so the
    # choice is not read as a rounding of the same result.
    dropped = [s for s in art if id(s) not in {id(x) for x in b_sel}]
    check("the 26 lone rises: sum c +828, sum dP -1160",
          len(dropped) == 26 and sum(s["c"] for s in dropped) == 828
          and sum(s["dP"] for s in dropped) == -1160,
          "%d steps, c %+d, dP %+d" % (len(dropped), sum(s["c"] for s in dropped),
                                       sum(s["dP"] for s in dropped)))
    check("choosing B flips the pooled ratio's sign",
          pooled < 0 < b_pool, "A %+.6g vs B %+.6g" % (pooled, b_pool))

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

    # 8. the run test keyed on the wrong column.  Both alternatives are numbers
    #    a plausible implementation would actually produce, and both differ from
    #    83 -- so "run key c/dP/fluc -> 83/81/98" is load-bearing, and the 83 is
    #    pinned to the temperature reading rather than to "some run test".
    check("mut run key on dP -> 81", len(keys["dP"]) == 81 and len(keys["dP"]) != 83,
          "%d steps" % len(keys["dP"]))
    check("mut run key on fluc -> 98", len(keys["fluc"]) == 98 and len(keys["fluc"]) != 83,
          "%d steps" % len(keys["fluc"]))


def txt_claims(header, body):
    """The labelled-line capture: 89 rows over 91 seconds, all of them rising.

    The headline is a NEGATIVE.  logs.csv forced three choices -- B vs A, which
    column is `c`, which column the run test keys on -- and this file cannot
    distinguish any of them, because both channels rise on every step.  The
    three FOLLOWS below are where that is written down.
    """
    samples, steps = analyse(body)
    rows = A.build_rows(samples)
    dsteps = [r for r in rows if r["c"] is not None]
    n = len(dsteps)

    check("columns are Time/Temp/Pres/Fluc", header == A.SOURCE_COLS, "%s" % header)
    check("89 rows", len(body) == 89, "got %d" % len(body))
    check("53 distinct samples", len(samples) == 53, "got %d" % len(samples))
    check("52 steps", len(steps) == 52, "got %d" % len(steps))
    check("53 table rows, n = 1..53", [r["n"] for r in rows] == list(range(1, 54)),
          "n %d..%d" % (rows[0]["n"], rows[-1]["n"]))

    for key, col in (("c", "temp"), ("dP", "pres")):
        total = sum(s[key] for s in dsteps)
        span = samples[-1][col] - samples[0][col]
        check("telescope %s" % key, total == span, "%d vs %d" % (total, span))

    # THE logs.csv ANOMALY DOES NOT REPRODUCE.  There the file's own Fluc
    # disagrees with the recomputed difference on 39 consecutive steps; here it
    # agrees on every one.  So that divergence belongs to that window and not to
    # the recorder, and the third column is not broken in general.
    dis = [s for s in dsteps if s["c"] != s["fluc"]]
    check("fluc == c on 52/52", not dis, "%d differ" % len(dis))

    a, b = rising(steps, "dT")
    runst = A.runs(dsteps, "c")
    check("52/52 rise, 0 fall, 0 flat",
          len(a) == 52 and not [s for s in steps if s["dT"] <= 0],
          "rise %d" % len(a))
    # Monotone on both channels, so one run of 52: 「只算连续升高处」 selects the
    # whole capture and B is not a subset of A here, it is A.
    check("one run of 52 -- B == A == all", len(runst) == 1 and len(b) == 52 == len(a),
          "%d runs, %d steps" % (len(runst), len(b)))

    check("row 1 has no c and no d",
          rows[0]["c"] is None and rows[0]["d"] is None,
          "c=%r d=%r" % (rows[0]["c"], rows[0]["d"]))
    check("no step has c == 0", not [r for r in dsteps if r["c"] == 0])
    bad = [r for r in dsteps if r["c"] and r["d"] != r["dP"] / r["c"]]
    check("d == dPres / c on all 52", not bad, "%d bad" % len(bad))

    vals = sorted(r["d"] for r in dsteps)

    def q(t):
        return vals[min(len(vals) - 1, int(t * (len(vals) - 1)))]

    check("d mean +1.0945741", abs(sum(vals) / n - 1.0945741) < 1e-6,
          "%+.8g" % (sum(vals) / n))
    check("d median +1.0079365", abs(q(.5) - 1.0079365) < 1e-7, "%+.8g" % q(.5))
    check("d p10 +0.87640449 p90 +1.1503268",
          abs(q(.1) - 0.87640449) < 1e-7 and abs(q(.9) - 1.1503268) < 1e-7,
          "%+.8g %+.8g" % (q(.1), q(.9)))
    check("d min +0.46422339 max +3.1960784",
          abs(vals[0] - 0.46422339) < 1e-7 and abs(vals[-1] - 3.1960784) < 1e-7,
          "%+.8g %+.8g" % (vals[0], vals[-1]))
    pooled = sum(r["dP"] for r in dsteps) / sum(r["c"] for r in dsteps)
    check("pooled sum(dPres)/sum(c) = +1.0178509", abs(pooled - 1.0178509) < 1e-7,
          "%+.8g" % pooled)
    check("|d - 1| <= 0.5 on 46/52",
          sum(1 for v in vals if abs(v - 1) <= .5) == 46,
          "%d" % sum(1 for v in vals if abs(v - 1) <= .5))

    # WHY d SITS AT 1 -- measured, not assumed.  Not because a ratio was chosen
    # to be 1, but because the two channels are the same escalating ramp: the
    # correlation is the highest of the three pairings available here, which is
    # what rules out "d=1 by construction" and "d=1 by coincidence" alike.
    cc = [r["c"] for r in dsteps]
    pp = [r["dP"] for r in dsteps]
    dd = [r["d"] for r in dsteps]
    check("corr(dT, dP) = +0.946571", abs(pearson(cc, pp) - 0.946571) < 1e-5,
          "%+.6f" % pearson(cc, pp))
    check("corr(dT,dP) beats both corr(d,*) pairings",
          abs(pearson(cc, pp)) > abs(pearson(dd, cc))
          and abs(pearson(cc, pp)) > abs(pearson(dd, pp)),
          "d/dT %+.6f  d/dP %+.6f" % (pearson(dd, cc), pearson(dd, pp)))
    # Level, not shape: over the tail the pooled ratio is 1 to four digits even
    # though both rates doubled twice on the way there.
    tail = dsteps[19:]
    tpool = sum(r["dP"] for r in tail) / sum(r["c"] for r in tail)
    check("last 33 steps pooled +0.9996665", abs(tpool - 0.999666492) < 1e-8,
          "%+.8g" % tpool)

    # §0.21, WITH A SECOND MECHANISM AT THE OTHER END.  The denominator is the
    # measured object, and it is what makes d BIG: all five high steps sit on
    # the five smallest temperature increments in the file.  But the single low
    # step is not the mirror image -- its c is large (rank 40 of 52) and it is
    # the PRESSURE that is small (266 against a median of 496).  One
    # "small denominator" story would explain five of the six.
    d_sorted = sorted(cc)
    p_sorted = sorted(pp)
    out = [r for r in dsteps if abs(r["d"] - 1) > .5]
    high = [r for r in out if r["d"] > 1]
    low = [r for r in out if r["d"] < 1]
    check("6 steps out of band, all in the first 19 seconds",
          len(out) == 6 and out[-1]["t"] == "18:39:00",
          "%d, last %s" % (len(out), out[-1]["t"] if out else "-"))
    check("the 5 high ones sit on the 5 smallest c",
          len(high) == 5 and sorted(r["c"] for r in high) == d_sorted[:5],
          "%s" % sorted(r["c"] for r in high))
    check("the 1 low one has a LARGE c (rank 40) and a small dP",
          len(low) == 1
          and sum(1 for v in cc if v < low[0]["c"]) + 1 == 40
          and low[0]["dP"] < p_sorted[26],
          "c %d rank %d, dP %d vs median %d"
          % (low[0]["c"], sum(1 for v in cc if v < low[0]["c"]) + 1, low[0]["dP"],
             p_sorted[26]))

    # The pressure channel is quantised and the temperature channel is not: 22
    # of the 51 pressure increments step by exactly +2, and not one temperature
    # increment does.  Two columns off the same readout, two lattices.
    dd_p = [pp[i] - pp[i - 1] for i in range(1, n)]
    dd_t = [cc[i] - cc[i - 1] for i in range(1, n)]
    p2 = sum(1 for v in dd_p if v == 2)
    t2 = sum(1 for v in dd_t if v == 2)
    check("d(dP) == +2 on 22/51 steps, d(dT) == +2 on 0/51",
          p2 == 22 and t2 == 0, "dP %d, dT %d" % (p2, t2))

    # Two round numbers end the capture.  Neither is asserted to MEAN anything.
    check("capture ends at Pres 32768 (=2^15), Temp 38651",
          samples[-1]["pres"] == 32768 and samples[-1]["temp"] == 38651,
          "%d %d" % (samples[-1]["pres"], samples[-1]["temp"]))
    # 2^15 is a clamp candidate, but the last step (+994) is in line with the
    # three before it (+978/+982/+988), so "clamped" and "coincidence" are the
    # same picture from this file alone.  Nothing here says which it is.
    check("final dP +994 sits inside the run 978/982/988",
          [r["dP"] for r in dsteps[-4:]] == [978, 982, 988, 994],
          "%s" % [r["dP"] for r in dsteps[-4:]])

    # ---- mutants: each must redden its own check --------------------------
    print()
    print("  -- mutations --")

    _, m = analyse(body, dedupe=False)
    mm = [s for s in m if s["dT"] != s["fluc"]]
    check("mut nodedupe -> fluc oracle red",
          len(m) == 88 and len(mm) == 36, "%d steps, %d differ" % (len(m), len(mm)))

    strided = [samples[i + 2]["temp"] - samples[i]["temp"]
               for i in range(0, len(samples) - 2)]
    check("mut strided walk -> telescope red",
          sum(strided) != samples[-1]["temp"] - samples[0]["temp"],
          "%d vs %d" % (sum(strided), samples[-1]["temp"] - samples[0]["temp"]))

    # The rival explanation of the third column -- "Fluc is dTemp one step
    # late" -- dies harder here than on logs.csv: it fits 0 of the 51 steps
    # against 52 in place.
    lag = sum(1 for i in range(1, len(steps)) if steps[i]["fluc"] == steps[i - 1]["dT"])
    check("mut lag-by-one -> 0 of 51 match", lag == 0, "%d" % lag)

    inv = [r for r in dsteps if r["dP"] and r["c"] / r["dP"] != r["d"]]
    check("mut invert d = c/dPres -> red", len(inv) == n, "%d differ" % len(inv))

    # THREE FOLLOWS.  Each is green BY CONSTRUCTION, and each green is a
    # statement about this capture rather than about the code.  All three were
    # load-bearing on logs.csv -- B vs A was 83 against 109 steps, swapping the
    # file's column for the recomputed one moved a row, and the run key gave
    # 83/81/98 -- and on a monotone 52-step ramp with fluc == c on every step,
    # none of them can move, so there is nothing for the mutant to redden.
    # Written down so the blind spot is known rather than assumed covered; a
    # check that has never been seen to fail is decoration (取舍 205/355).
    b1 = [s for r in runs1(steps, "dT") for s in r]
    check("FOLLOW: mut runs>=1 -> still 52 (no lone rises to drop)",
          len(b1) == 52 == len(b), "%d" % len(b1))
    flipped = [r for r in dsteps if r["fluc"] and r["dP"] / r["fluc"] != r["d"]]
    check("FOLLOW: mut fluc-as-c -> 0 rows move (fluc == c everywhere)",
          not flipped, "%d rows" % len(flipped))
    keys = {k: [s for r in A.runs(dsteps, k) for s in r] for k in ("c", "dP", "fluc")}
    check("FOLLOW: run key c/dP/fluc -> 52/52/52",
          [len(keys["c"]), len(keys["dP"]), len(keys["fluc"])] == [52, 52, 52],
          "%s" % {k: len(v) for k, v in keys.items()})


def dispatch_claims():
    """The fact main() branches on, asserted rather than commented.

    Both captures report the SAME four column names, because the .txt has no
    header line and the names are synthesised for it.  So `header ==
    A.SOURCE_COLS` was true for both files -- it could not tell them apart, and
    for one run of this checker the CSV capture was fed to the txt claims,
    which died on its legitimate c == 0 step.  What actually differs is
    structural: one file spends a line on a header and the other does not.

    Loaded by path rather than via SRC, so this reads the same two files
    whichever one the checker was pointed at.
    """
    if not (os.path.exists(LOGS_CSV) and os.path.exists(LOGS_TXT)):
        return
    hs, _, fs = A.load(LOGS_CSV)
    ht, _, ft = A.load(LOGS_TXT)
    check("the two captures name the same four columns", hs == ht,
          "%s vs %s" % (hs, ht))
    check("and differ on the sniffed format -- the only thing to branch on",
          fs != ft, "%s vs %s" % (fs, ft))
    # The mutant is the old code.  Green by construction, and that green IS the
    # finding: this test cannot separate the two inputs, so a checker built on
    # it branches one way regardless of which capture it opened.
    check("FOLLOW: mut dispatch on header -> both take one branch",
          hs == A.SOURCE_COLS and ht == A.SOURCE_COLS,
          "old test true for both")
    print()


def run_analyzer(path, outdir):
    """Run the analyzer for real.  main() reads sys.argv and prints a report."""
    saved = sys.argv
    sys.argv = ["analyze_fluc_steps.py", path, outdir]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            A.main()
    finally:
        sys.argv = saved


def rows_of(path):
    with open(path, "rb") as fh:
        return list(csv.reader(io.StringIO(fh.read().decode("utf-8"))))


def writer_claims():
    """THE CSV IS THE DELIVERABLE, and until now nothing in here opened one.

    Every claim above exercises A.load / A.build_rows / A.runs -- the READER.
    Nothing ran A.main(), so the three files it writes were checked by nobody,
    and one of them shipped as a header with zero rows.  The cause was a name:
    `fmt` is the number formatter row_of() calls, and a new local binding
    `fmt = load(...)[2]` in main() turned every call into "csv"(90) ->
    TypeError.  The analyzer opened steps_all.csv, wrote the header, died on
    row 1, and left a 69-byte stub.

    Note WHICH green survived that.  This checker already pinned A.fmt(-0.0)
    == "0" and it stayed green throughout: the shadow lived in a FRAME, and
    everything here was looking at a NAMESPACE.  A module-level test cannot
    see a function-local rebinding -- so the fix is not another unit test, it
    is to run the program and read what came out.
    """
    tmp = tempfile.mkdtemp(prefix="fluc_out_")
    try:
        for path, n_all, n_rise in ((LOGS_CSV, 279, 134), (LOGS_TXT, 53, 52)):
            if not os.path.exists(path):
                continue
            name = os.path.basename(path)
            run_analyzer(path, tmp)
            pref = ("" if name.lower() == A.DEFAULT_SRC
                    else name.replace(".", "_") + "_")
            allf = os.path.join(tmp, pref + "steps_all.csv")
            risef = os.path.join(tmp, pref + "rise_steps.csv")
            sumf = os.path.join(tmp, pref + "d_summary.txt")

            got_all = len(rows_of(allf)) - 1
            got_rise = len(rows_of(risef)) - 1
            check("%s: steps_all has a row per sample" % name,
                  got_all == n_all, "want %d got %d" % (n_all, got_all))
            check("%s: rise_steps has the rising steps" % name,
                  got_rise == n_rise, "want %d got %d" % (n_rise, got_rise))
            check("%s: d_summary.txt is not empty" % name,
                  os.path.exists(sumf) and os.path.getsize(sumf) > 0,
                  "%d B" % (os.path.getsize(sumf) if os.path.exists(sumf) else -1))
            # Row 1 is the operator's own /nil/ line: the sample with no
            # predecessor.  It is in steps_all and deliberately NOT in
            # rise_steps, which is the shape difference between the two files.
            first = rows_of(allf)[1]
            check("%s: row 1 carries no c and no d" % name,
                  first[0] == "1" and first[4] == "" and first[7] == "",
                  "n=%r c=%r d=%r" % (first[0], first[4], first[7]))

        # The mutant is the bug, reproduced exactly: shadow the module's fmt
        # with a string, as main() did, and the analyzer dies the same way and
        # leaves the same stub.  Red here would mean the writer no longer
        # depends on row_of()'s formatter and this check tests nothing.
        if os.path.exists(LOGS_CSV):
            sub = os.path.join(tmp, "shadow")
            os.makedirs(sub, exist_ok=True)
            kept = A.fmt
            A.fmt = "csv"
            try:
                err = None
                try:
                    run_analyzer(LOGS_CSV, sub)
                except TypeError as exc:
                    err = exc
                stub = os.path.join(sub, "steps_all.csv")
                n = len(rows_of(stub)) - 1 if os.path.exists(stub) else None
                check("mut shadow fmt -> raises, header-only stub",
                      err is not None and n == 0,
                      "%s, %r rows" % (type(err).__name__ if err else "no error", n))
            finally:
                A.fmt = kept
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def same_path(a, b):
    """Path equality that survives how the caller spelled it.

    `SRC in (LOGS_CSV, LOGS_TXT)` looks like a guard and is one only when the
    argv string happens to be spelled exactly like the literal -- normcase +
    abspath, because a relative path is the natural thing to type.  When it is
    not, the branch is skipped and dispatch_claims() prints nothing: three
    checks gone, RESULT still 0 FAILED.
    """
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def is_capture(path):
    return any(same_path(path, p) for p in (LOGS_CSV, LOGS_TXT))


def main():
    if is_capture(SRC):
        dispatch_claims()
    header, body, kind = A.load(SRC)
    if kind == "txt":
        txt_claims(header, body)
    else:
        csv_claims(header, body)
    print()
    writer_claims()

    print()
    print("RESULT: %d ok, %d FAILED" % (len(passed), len(failed)))
    if failed:
        for f in failed:
            print("  FAILED: %s" % f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
