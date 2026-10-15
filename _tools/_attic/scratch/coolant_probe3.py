import io, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG = os.path.join(ROOT, "Data", "DataCollection.Log")
raw = io.open(LOG, encoding="utf-8").read()
body = raw.split("[[==", 1)[1].rsplit("==]]", 1)[0]
recs = [json.loads(l) for l in body.splitlines() if l.strip()]
ticks = [r for r in recs if r["data"].get("type") == "tick"]
pay = lambda r: r["data"]["payload"]
def dedupe(rs):
    out = []
    for r in rs:
        if out:
            a, b = pay(r)["reactor"], pay(out[-1])["reactor"]
            if (a["tempF"], a["pressure"], a["fluctuation"]) == (b["tempF"], b["pressure"], b["fluctuation"]):
                continue
        out.append(r)
    return out
d = dedupe(ticks)
print("raw %d, deduped %d" % (len(ticks), len(d)))
rows = []
for i in range(len(d)-1):
    p, q = pay(d[i]), pay(d[i+1])
    C = sum(p["cbl"]["level"]); K = sum(p["coolant"]["levels"])
    obs = q["reactor"]["tempF"] - p["reactor"]["tempF"]
    rows.append((obs, C, K, p["actuals"]["actDT"], p["predictions"]["predDT"], p["reactor"]["fluctuation"]))
print("first 12 deduped transitions:  observed  Csum Ksum  actDT  predDT  fluctuation")
for r in rows[:12]:
    print("   %8d  C%-2d K%-2d  actDT %8s  predDT %8s  fluc %8s" % r)
def lstsq(rs):
    A = [[0.0]*4 for _ in range(4)]
    for y, x1, x2 in rs:
        v = [x1, x2, 1.0, y]
        for i in range(4):
            for j in range(4):
                A[i][j] += v[i]*v[j]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(A[r][i]))
        A[i], A[piv] = A[piv], A[i]
        if not A[i][i]:
            return None
        for r in range(3):
            if r != i:
                f = A[r][i]/A[i][i]
                for c in range(4):
                    A[r][c] -= f*A[i][c]
    return [A[i][3]/A[i][i] for i in range(3)]
allrows = [(o, C, K) for (o, C, K, a, pr, fl) in rows]
print("\nfit on all %d transitions: obs = %.4f*C %+.4f*K %+.4f" % (len(allrows), *lstsq(allrows)))
# where does 65C-120K match the observation?
win = [(o, C, K) for (o, C, K, a, pr, fl) in rows if abs(o - (65*C - 120*K)) <= 40]
print("transitions within +-40 of 65C-120K: %d / %d" % (len(win), len(rows)))
if len(win) > 5:
    print("   fit there: obs = %.4f*C %+.4f*K %+.4f" % (*lstsq(win),))
# correlation with fluctuation field
print("\nfluctuation vs 65C-120K on the first 30 transitions:")
for (o, C, K, a, pr, fl) in rows[:30]:
    print("   obs %8d  65C-120K %8d  fluc %8s  actDT %8s" % (o, 65*C-120*K, fl, a))
