import io, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG = os.path.join(ROOT, "Data", "DataCollection.Log")
raw = io.open(LOG, encoding="utf-8").read()
body = raw.split("[[==", 1)[1].rsplit("==]]", 1)[0]
recs = [json.loads(l) for l in body.splitlines() if l.strip()]
ticks = [r for r in recs if r["data"].get("type") == "tick"]
print("ticks", len(ticks))
def pay(r): return r["data"]["payload"]
seen = {}
for r in ticks:
    p = pay(r)
    key = (tuple(p["cbl"]["level"]), p["cbl"]["sumLevel"], tuple(p["cbl"]["active"]),
           tuple(p["coolant"]["levels"]), p["coolant"]["sumLevel"], tuple(p["cbl"]["power"]))
    seen[key] = seen.get(key, 0) + 1
print("distinct (cbl level,sum,active | coolant levels,sum | power):", len(seen))
# candidate identities
import itertools
def report(fn, label):
    ok = bad = 0
    examples = []
    for r in ticks:
        p = pay(r)
        pred = p["predictions"]["predDT"] * 5.0
        got = fn(p)
        if abs(pred - got) < 0.51:
            ok += 1
        else:
            bad += 1
            if len(examples) < 3:
                examples.append((pred, got, p["cbl"]["level"], p["cbl"]["active"], p["coolant"]["levels"]))
    print("%-46s ok %3d  bad %3d  %s" % (label, ok, bad, examples[:2] if bad else ""))
report(lambda p: 65.0*sum(p["cbl"]["level"]) - 120.0*sum(p["coolant"]["levels"]), "65*sum(level) - 120*sum(pump)")
report(lambda p: 65.0*sum(l for l,a in zip(p["cbl"]["level"], p["cbl"]["active"]) if a) - 120.0*sum(p["coolant"]["levels"]), "65*sum(level where active) - 120*pump")
report(lambda p: 65.0*sum(p["cbl"]["level"]) - 120.0*p["coolant"]["sumLevel"], "65*sum(level) - 120*coolant.sumLevel")
# what levels look like
lv = {}
for r in ticks:
    p = pay(r)
    k = (tuple(p["cbl"]["level"]), tuple(p["coolant"]["levels"]))
    lv[k] = lv.get(k,0)+1
for k,v in sorted(lv.items(), key=lambda kv:-kv[1])[:20]:
    print(v, k)
