"""Verify analyze_fluc_steps.py, and prove each check has teeth.

The deliverable's numbers are only as good as the reader that produced them, and
this reader makes three choices the operator's sentence did not settle (dedupe,
the two readings of 连续升高, and what to do about the `Fluc` column disagreeing
with the visible temps).  So each claim gets a mutation that targets it: if a
check cannot be made to fail, it is decoration.

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
    print("  %-34s %s %s" % (name, "ok" if ok else "FAIL", detail))


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

    # ---- the claims, on the real file ------------------------------------
    check("header is Time/Temp/Pres/Fluc", header == ["Time", "Temp", "Pres", "Fluc"])
    check("444 rows", len(body) == 444, "got %d" % len(body))
    check("279 distinct samples", len(samples) == 279, "got %d" % len(samples))
    check("278 steps", len(steps) == 278, "got %d" % len(steps))

    # telescope: every delta sums to last-first.  Independent of dedup (repeats
    # contribute 0) but NOT of dropping rows, which is the mutation below.
    for key, col in (("dT", "temp"), ("dP", "pres")):
        total = sum(s[key] for s in steps)
        span = samples[-1][col] - samples[0][col]
        check("telescope %s" % key, total == span, "%d vs %d" % (total, span))

    mism = [s for s in steps if s["dT"] != s["fluc"]]
    check("Fluc == dTemp on 239/278", len(mism) == 39, "%d differ" % len(mism))
    check("mismatch is one window",
          {s["t"] for s in mism} == {s["t"] for s in steps
                                     if "16:29:28" <= s["t"] <= "16:30:08"},
          "%s .. %s" % (mism[0]["t"], mism[-1]["t"]))
    # The window is dark: fluc says up, the temps say down.  If this ever flips
    # to the same sign the block is no longer special and the story is wrong.
    check("window signs disagree",
          sum(s["fluc"] for s in mism) > 0 > sum(s["dT"] for s in mism),
          "fluc %+d vs dTemp %+d" % (sum(s["fluc"] for s in mism),
                                     sum(s["dT"] for s in mism)))
    # A rising step in the window is the only place the two columns could give
    # the operator different answers.
    check("1 rising step affected",
          sum(1 for s in mism if s["dT"] > 0) == 1,
          "%d" % sum(1 for s in mism if s["dT"] > 0))

    def counts(key, want_a, want_b):
        a, b = rising(steps, key)
        return len(a) == want_a and len(b) == want_b

    check("dTemp A=109 B=83", counts("dT", 109, 83))
    check("dPres A=82 B=81", counts("dP", 82, 81))
    # B is a strict subset of A by construction -- a FOLLOW, which must stay
    # green under every mutant below.  A subset that ever leaves A means the
    # run/window logic and the sign test have gone out of sync.
    for key in ("dT", "dP"):
        a, b = rising(steps, key)
        check("B subset of A (%s)" % key, set(map(id, b)) <= set(map(id, a)))

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
    #    late".  It must fit strictly worse than reading it in place, or the
    #    "239 of 278" number is describing a lag rather than the column.
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

    print()
    print("RESULT: %d ok, %d FAILED" % (len(passed), len(failed)))
    if failed:
        for f in failed:
            print("  FAILED: %s" % f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
