"""Fit the game's own tick, not a sampled derivative.

The fine trace settled what `m.temp` actually is. It is not a continuous state
being sampled: `m.temp`, `m.press` and `m.fluct` all move on the SAME row and
never separately, at a cadence of ~1.8 s (gaps 1.57..2.15 s over 900 s). That is
one physics tick writing three labels, and between ticks all three hold. So the
honest unit of analysis is the TICK, and the honest target is the per-tick
increment `dTemp`, not a derivative sampled 3x/s.

That also kills the exponential reading the segment table suggested: over
t=560.78..610.97 with cbl=75, cool=0, fan=3 the increments are +144, +289, +229,
+205, +287, +147, +279 ... +241, +214, +157 -- flat in TIME and flat in
TEMPERATURE while the core climbs 6625 -> 13224 F. A first-order lag would have
the increment shrink as it approached equilibrium. This one does not.

So fit, per tick:

    dTemp = a + b*sum(cblPct) + c*coolSum + f*fanCount + k*T

and read `k`: k ~ 0 means the core is a LINEAR RAMP in temperature (heat in and
out both temperature-independent over the observed band), not an exponential
relaxation. That single coefficient decides which of the two model families a
remake should use, so it is worth the fit rather than an eyeball.
"""
import numpy as np

SRC = 'Data/flow/original_260926-230049'
WANT = ['m.temp', 'c.cbl1Pct', 'c.cbl2Pct', 'c.cbl3Pct', 'c.coolSum', 'c.fanCount']

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
        raw.append((t, float(cur['m.temp']),
                    sum(float(cur.get('c.cbl%dPct' % i) or 0) for i in (1, 2, 3)),
                    float(cur['c.coolSum'] or 0), float(cur['c.fanCount'] or 0)))

ticks = []
for i in range(1, len(raw)):
    t1, T1, S1, C1, F1 = raw[i]
    t0, T0, S0, C0, F0 = raw[i - 1]
    if T1 == T0 or not (0.5 <= t1 - t0 <= 4.0):
        continue
    # a tick that straddles a control change is not a step response of either
    # setting; keep only the ticks the controls sat still through.
    if (S0, C0, F0) != (S1, C1, F1):
        continue
    ticks.append((t0, T0, S0, C0, F0, T1 - T0, t1 - t0))

t0 = np.array([x[0] for x in ticks])
T = np.array([x[1] for x in ticks])
S = np.array([x[2] for x in ticks])
C = np.array([x[3] for x in ticks])
F = np.array([x[4] for x in ticks])
dT = np.array([x[5] for x in ticks])
dt = np.array([x[6] for x in ticks])
print('clean ticks %d   dt median %.2f s   dTemp %.0f..%.0f' % (len(ticks), np.median(dt), dT.min(), dT.max()))

# Normalise to a per-second rate so a merged tick cannot pose as a fast one.
# dt is ~1.8 s throughout, so this is a small correction, not a rescaling.
rate = dT / dt


def report(X, y, names, label):
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss = 1.0 - ((y - pred) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-9)
    print()
    print('--- %s   n=%d   R2=%.3f ---' % (label, len(y), ss))
    for n, c in zip(names, coef):
        print('   %-9s %+13.5g F/s per unit' % (n, c))
    return coef, ss


X = np.column_stack([np.ones_like(T), S, C, F, T])
names = ['const', 'sumPct', 'coolSum', 'fanCount', 'T']
coef, _ = report(X, rate, names, 'all clean ticks')
print('   => the T term is %s' % ('ZERO within noise: the core ramps, it does not relax'
                                  if abs(coef[4]) * T.mean() < abs(rate).mean() * 0.25
                                  else 'real: this really is a relaxation'))

# Standard error on the T coefficient, so "near zero" can be stated as a number
# instead of a vibe.  Only the diagonal of (X'X)^-1 is needed, no scipy.
resid = rate - X @ coef
dof = max(len(rate) - X.shape[1], 1)
s2 = (resid ** 2).sum() / dof
cov = s2 * np.linalg.inv(X.T @ X)
se = np.sqrt(np.diag(cov))
print()
print('   coefficient +- standard error:')
for n, c, s in zip(names, coef, se):
    print('     %-9s %+12.4g +- %.4g' % (n, c, s))
print('   T term: %.4g +- %.4g  ->  %s' % (
    coef[4], se[4],
    'not distinguishable from zero' if abs(coef[4]) < 2 * se[4] else 'distinguishable from zero'))

print()
print('=== per-setting medians (the lookup table, no model assumed) ===')
print('  cblPct cool fan   n    median dT/tick   span')
groups = {}
for (_, _, s, c, f, d, _) in ticks:
    groups.setdefault((s, c, f), []).append(d)
for key in sorted(groups, key=lambda k: -len(groups[k])):
    v = np.array(groups[key])
    if len(v) < 5:
        continue
    print('  %5.0f %4.0f %3.0f %5d   %+10.0f F     %+.0f..%+.0f'
          % (key[0], key[1], key[2], len(v), np.median(v), v.min(), v.max()))
