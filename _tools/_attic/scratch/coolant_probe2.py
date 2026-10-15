import io, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG = os.path.join(ROOT, "Data", "DataCollection.Log")
raw = io.open(LOG, encoding="utf-8").read()
body = raw.split("[[==", 1)[1].rsplit("==]]", 1)[0]
recs = [json.loads(l) for l in body.splitlines() if l.strip()]
ticks = [r for r in recs if r["data"].get("type") == "tick"]
pay = lambda r: r["data"]["payload"]
# exactness
worst = 0.0
for r in ticks:
    p = pay(r)
    d = abs(p["predictions"]["predDT"]*5.0 - (65.0*sum(p["cbl"]["level"]) - 120.0*sum(p["coolant"]["levels"])))
    worst = max(worst, d)
print("max |predDT*5 - (65*C - 120*K)| over 477 ticks: %r" % worst)
# are predDT values multiples of 1/5?
fracs = set()
for r in ticks:
    v = pay(r)["predictions"]["predDT"]
    fracs.add(round((v*5) % 1, 6))
print("distinct fractional parts of predDT*5:", sorted(fracs)[:6])
# actDT vs levels
print()
print("tick  Csum Ksum   actDT   predDT   tempF_delta(observed)")
prev = None
rows = []
for r in ticks:
    p = pay(r)
    C = sum(p["cbl"]["level"]); K = sum(p["coolant"]["levels"])
    act = p["actuals"]["actDT"]; pred = p["predictions"]["predDT"]
    tf = p["reactor"]["tempF"]
    d = None if prev is None else tf - prev
    prev = tf
    rows.append((C, K, act, pred, d, tf))
# regression actDT ~ a*C + b*K + c on ticks where nothing jumped; use only ticks
# whose observed tempF delta equals actDT (the arithmetic ones)
import statistics
pairs = [(C,K,act) for (C,K,act,pred,d,tf) in rows]
# least squares 3 unknowns via normal equations
import itertools
def lstsq(rows):
    # rows: list of (y, x1, x2)
    n = len(rows)
    A = [[0.0]*4 for _ in range(4)]
    for y, x1, x2 in rows:
        v = [x1, x2, 1.0, y]
        for i in range(4):
            for j in range(4):
                A[i][j] += v[i]*v[j]
    # gaussian elimination
    for i in range(3):
        piv = max(range(i,3), key=lambda r: abs(A[r][i]))
        A[i], A[piv] = A[piv], A[i]
        for r in range(3):
            if r != i and A[i][i]:
                f = A[r][i]/A[i][i]
                for c in range(4):
                    A[r][c] -= f*A[i][c]
    return [A[i][3]/A[i][i] for i in range(3)]
fit = lstsq([(act,C,K) for (C,K,act,pred,d,tf) in rows])
print("all 477 ticks:  actDT = %.4f*C %+.4f*K %+.4f" % tuple(fit))
print("          65/120 would be:     65.0000*C -120.0000*K  +0")
# only the stretch where it holds (find where actDT != 65C-120K)
bad = [(i,C,K,act) for i,(C,K,act,pred,d,tf) in enumerate(rows) if abs(act-(65*C-120*K)) > 1]
print("ticks where actDT != 65C-120K:", len(bad), bad[:5], "..." , bad[-3:] if bad else "")
good = [(C,K,act) for (C,K,act,pred,d,tf) in rows if abs(act-(65*C-120*K)) <= 1]
print("ticks where it holds:", len(good))
if len(good) > 10:
    print("   fit on those only: actDT = %.4f*C %+.4f*K %+.4f" % tuple(lstsq(good)))
