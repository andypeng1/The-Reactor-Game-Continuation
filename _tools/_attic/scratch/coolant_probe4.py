import io, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
raw = io.open(os.path.join(ROOT, "Data", "DataCollection.Log"), encoding="utf-8").read()
recs = [json.loads(l) for l in raw.split("[[==",1)[1].rsplit("==]]",1)[0].splitlines() if l.strip()]
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
def line(p): return 65*sum(p["cbl"]["level"]) - 120*sum(p["coolant"]["levels"])
for lag in (0, 1):
    band = {20:0, 60:0, 150:0, 10**9:0}
    n = 0
    worst = []
    for i in range(len(d)-1):
        if i - lag < 0: continue
        obs = pay(d[i+1])["reactor"]["tempF"] - pay(d[i])["reactor"]["tempF"]
        want = line(pay(d[i-lag]))
        n += 1
        for b in sorted(band):
            if abs(obs-want) <= b: band[b] += 1
        worst.append((abs(obs-want), i, obs, want))
    worst.sort(reverse=True)
    print("levels taken %d record(s) BEFORE the delta: n=%d  within20 %d  within60 %d  within150 %d  total %d"
          % (lag, n, band[20], band[60], band[150], band[10**9]))
    print("   worst 4:", [(w[1], w[2], w[3]) for w in worst[:4]])
