"""Try to read a temperature model off the capture.

Question being asked: is `dTemp/dt` a function of the controls that this file can
identify?  Fit, in F/s:

    dT/dt = t0 + t1*sum(cblPct) + t2*coolSum + t3*fanCount
              + t4*T + t5*coolSum*T + t6*fanCount*T

The control*T terms are the ones that matter physically: a coolant loop or a fan
removes heat in proportion to how much hotter the core is than what it dumps to,
so its effect has to scale with T.  A fit without them would put the coolant's
whole effect into a constant, which is exactly the mistake that produces a model
that looks fine at one temperature and is wrong everywhere else.

Reported for the whole file and for the near-equilibrium subset, because the
two answer different questions: the full fit is dominated by the fast swings, the
subset is what the gains look like when nothing is moving.
"""
import numpy as np

SRC = 'Data/flow/original_260926-230049'

WANT = ['m.temp', 'm.press', 'm.fluct', 's.Core.RadiationVal',
        'c.cbl1Pct', 'c.cbl2Pct', 'c.cbl3Pct', 'c.coolSum', 'c.fanCount']

rows = []
cur = {}
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
    rows.append((t, dict(cur)))

T, S, C, F, P, FL = [], [], [], [], [], []
for t, st in rows:
    if st.get('m.temp') is None:
        continue
    T.append(float(st['m.temp']))
    S.append(float(st['c.cbl1Pct'] or 0) + float(st['c.cbl2Pct'] or 0) + float(st['c.cbl3Pct'] or 0))
    C.append(float(st['c.coolSum'] or 0))
    F.append(float(st['c.fanCount'] or 0))
    P.append(float(st['m.press'] or 0))
    FL.append(float(st['m.fluct'] or 0))
tt = np.array([t for t, st in rows if st.get('m.temp') is not None])
T, S, C, F, P, FL = map(np.array, (T, S, C, F, P, FL))

print('temp samples %d   t %.1f..%.1f   T %.0f..%.0f F' % (len(T), tt[0], tt[-1], T.min(), T.max()))

# dT/dt over consecutive samples, only where the gap is short enough that a
# finite difference means anything.  1.5 s is ~5 polls at this poll rate.
dt = np.diff(tt)
dT = np.diff(T)
ok = (dt > 0) & (dt <= 1.5)
rate = dT[ok] / dt[ok]
mid = 0.5 * (T[:-1][ok] + T[1:][ok])
Sm = S[:-1][ok]
Cm = C[:-1][ok]
Fm = F[:-1][ok]
Pm = P[:-1][ok]
print('finite-difference pairs %d   |dT/dt| median %.1f  max %.0f F/s' % (
    len(rate), np.median(np.abs(rate)), np.abs(rate).max()))


def design(S, C, F, T):
    one = np.ones_like(T)
    return np.column_stack([one, S, C, F, T, C * T, F * T])


def fit(mask, label, weights=None):
    X = design(Sm[mask], Cm[mask], Fm[mask], mid[mask])
    y = rate[mask]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss = 1.0 - ((y - pred) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-9)
    print()
    print('--- %s   n=%d   R2=%.3f ---' % (label, mask.sum(), ss))
    names = ['const', 'sumPct', 'coolSum', 'fanCount', 'T', 'cool*T', 'fan*T']
    for n, c in zip(names, coef):
        print('   %-9s %+14.6g' % (n, c))
    print('   implied equilibrium at coolSum=2, fanCount=4, sumPct=75:')
    # solve  t0 + t1*S + t2*C + t3*F + (t4 + t5*C + t6*F)*T = 0
    for c_, f_ in ((0, 0), (2, 4), (3, 6)):
        den = coef[4] + coef[5] * c_ + coef[6] * f_
        num = coef[0] + coef[1] * 75 + coef[2] * c_ + coef[3] * f_
        print('     cool=%d fan=%d -> Teq = %s F' % (c_, f_, '%.0f' % (-num / den) if abs(den) > 1e-12 else 'undefined'))
    return coef, ss


fit(np.ones(len(rate), bool), 'whole file')
fit(np.abs(rate) < 2.0, 'near equilibrium (|dT/dt| < 2 F/s)')

print()
print('--- the fluct column is not a rate: fluct vs dT/dt correlation %.3f ---' % (
    np.corrcoef(FL[1:][ok], rate)[0, 1]))
