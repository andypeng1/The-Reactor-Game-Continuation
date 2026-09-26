"""`m.fluct` IS the temperature step. Fit that.

391 of the 393 rows where `m.temp` moved satisfy `temp_next - temp = m.fluct`
EXACTLY. The other two are a one-tick read-order artefact (a row carrying the
temperature from the tick before and the fluct from the tick after). So:

    temp(t+1) = temp(t) + fluct(t)

`m.fluct` is not a separate "stability" reading sitting beside the temperature --
it is the per-tick INCREMENT, reported on its own. That is also what the
calibration console's NET STABILITY label is showing: the operator reads the
derivative directly, which is why the game can ask them to judge stability.

It rewrites the question. `temp` is an accumulator, not a first-order state, so
there is nothing to fit on `temp`: fit `fluct`, in F per tick (~1.8 s ticks;
gaps mode 2.0 s, p10 1.51, p90 2.04).

The regressors stay the controls. `k` -- the coefficient on the current
temperature -- is the whole ballgame: k = 0 means the core is an integrator that
will wander off on its own, k < 0 means the fluctuations weaken as it heats,
which is the self-limiting term that makes the thing controllable at all.
"""
import numpy as np

SRC = 'Data/flow/original_260926-230049'
WANT = ['m.temp', 'm.fluct', 'm.press',
        'c.cbl1Pct', 'c.cbl2Pct', 'c.cbl3Pct', 'c.coolSum', 'c.fanCount']

raw, cur = [], {}
for ln in open(SRC, encoding='utf-8', errors='replace'):
    if ln[:2] not in ('S ', 'B '):
        continue
    p = ln.split()
    t = float(p[2][2:])
    for tok in p[3:]:
        if '=' not in tok:
            continue
        k, v = tok.split('=', 1)
        if k in WANT:
            cur[k] = v
    if cur.get('m.temp') is not None:
        raw.append((t, float(cur['m.temp']), float(cur['m.fluct']), float(cur['m.press'] or 0),
                    sum(float(cur.get('c.cbl%dPct' % i) or 0) for i in (1, 2, 3)),
                    float(cur['c.coolSum'] or 0), float(cur['c.fanCount'] or 0)))

ev = []
prev = None
for i in range(1, len(raw)):
    t1, T1, FL1, P1, S1, C1, F1 = raw[i]
    t0, T0 = raw[i - 1][0], raw[i - 1][1]
    if T1 == T0:
        continue
    if abs((T1 - T0) - FL1) > 1e-9:      # the two read-order artefacts
        prev = (t1, T1, S1, C1, F1)
        continue
    # the increment belongs to the tick that just happened; the controls that
    # produced it are the ones standing now.  Recorded alongside the previous
    # tick's controls so the pair can be checked for a control move in between.
    ev.append((t1, T1, FL1, P1, S1, C1, F1,
               -1 if prev is None else int((prev[2], prev[3], prev[4]) != (S1, C1, F1))))
    prev = (t1, T1, S1, C1, F1)

t1 = np.array([e[0] for e in ev])
T = np.array([e[1] for e in ev])
y = np.array([e[2] for e in ev])
P = np.array([e[3] for e in ev])
S = np.array([e[4] for e in ev])
C = np.array([e[5] for e in ev])
F = np.array([e[6] for e in ev])
print('tick events %d   t %.1f..%.1f   fluct %.0f..%.0f F' % (len(ev), t1[0], t1[-1], y.min(), y.max()))
moved = np.array([e[7] for e in ev]) == 1
print('events with a control move since the previous event: %d' % moved.sum())


def report(X, names, label):
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss = 1.0 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    resid = y - pred
    s2 = (resid ** 2).sum() / max(len(y) - X.shape[1], 1)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    print()
    print('--- %s   n=%d   R2=%.3f   resid sd %.0f F ---' % (label, len(y), ss, resid.std()))
    for n, c, s in zip(names, coef, se):
        flag = '' if abs(c) > 2 * s else '   (not distinguishable from 0)'
        print('   %-9s %+12.4g +- %-9.4g%s' % (n, c, s, flag))
    return coef, ss


report(np.column_stack([np.ones_like(T), S, C, F, T]),
       ['const', 'sumPct', 'coolSum', 'fanCount', 'T'], 'controls + current temperature')
report(np.column_stack([np.ones_like(T), S, C, F]),
       ['const', 'sumPct', 'coolSum', 'fanCount'], 'controls only (T dropped)')
report(np.column_stack([np.ones_like(T), S, C, F, P]),
       ['const', 'sumPct', 'coolSum', 'fanCount', 'press'], 'controls + pressure')

print()
print('=== fluct by setting: the table, medians in F per tick ===')
g = {}
for e in ev:
    g.setdefault((e[4], e[5], e[6]), []).append(e[2])
print('  cblPct cool fan    n   median   mean    sd    min    max')
for key in sorted(g, key=lambda k: (-k[0], k[1], k[2])):
    v = np.array(g[key])
    if len(v) < 4:
        continue
    print('  %5.0f %4.0f %3.0f %5d  %+7.0f %+7.0f %6.0f %+6.0f %+6.0f'
          % (key[0], key[1], key[2], len(v), np.median(v), v.mean(), v.std(), v.min(), v.max()))

print()
print('=== the temperature band each setting was used in (why the gains are entangled) ===')
for key in sorted(g, key=lambda k: (-k[0], k[1], k[2])):
    v = [e[1] for e in ev if (e[4], e[5], e[6]) == key]
    if len(v) < 4:
        continue
    print('  cblPct=%3.0f cool=%d fan=%d   n=%2d   temp seen %.0f..%.0f F'
          % (key[0], key[1], key[2], len(v), min(v), max(v)))
