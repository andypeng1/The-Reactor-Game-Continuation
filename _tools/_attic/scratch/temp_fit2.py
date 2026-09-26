"""Same question, but with a derivative estimator that matches the signal.

The first attempt returned R2 = 0.08 whole-file and 0.003 near equilibrium, with
physically backwards signs (coolant adding heat).  That is not a weak model, it
is a broken estimator, and the traceback to why is in the data:

  * median |dT/dt| = 0.0 with a max of 3035 F/s -- the label is a QUANTIZED
    display that repaints in whole-degree steps, sometimes after several polls
    of showing nothing, so a sample-to-sample difference is mostly either 0 or a
    repaint artefact.  The regression was fitting the repaint schedule.

So: measure the step size, then take differences over a ~20 s baseline where the
repaint noise cancels.  That is a correction to the method, not a loosened bar --
the same data, asked a question it can answer.
"""
import collections
import numpy as np

SRC = 'Data/flow/original_260926-230049'
WANT = ['m.temp', 'm.press', 'c.cbl1Pct', 'c.cbl2Pct', 'c.cbl3Pct',
        'c.coolSum', 'c.fanCount']

rows, cur = [], {}
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
        rows.append((t, float(cur['m.temp']), float(cur['m.press'] or 0),
                     sum(float(cur.get('c.cbl%dPct' % i) or 0) for i in (1, 2, 3)),
                     float(cur['c.coolSum'] or 0), float(cur['c.fanCount'] or 0)))

tt = np.array([r[0] for r in rows])
T = np.array([r[1] for r in rows])
P = np.array([r[2] for r in rows])
S = np.array([r[3] for r in rows])
C = np.array([r[4] for r in rows])
F = np.array([r[5] for r in rows])
print('samples %d   t %.1f..%.1f' % (len(tt), tt[0], tt[-1]))

# ---------------------------------------------------- how coarse is the label
d = np.diff(T)
print('consecutive polls with NO change: %d / %d (%.0f%%)'
      % ((d == 0).sum(), len(d), 100.0 * (d == 0).mean()))
nz = np.abs(d[d != 0])
if len(nz):
    g = collections.Counter(np.abs(d[d != 0]).astype(int).tolist())
    print('nonzero steps: n=%d  median %.0f  max %.0f   most common %s'
          % (len(nz), np.median(nz), nz.max(), g.most_common(5)))
    print('  -> the display steps by whole degrees and skips; a 1-poll derivative is noise')

# ------------------------------------------- derivative over a ~20 s baseline
# Pair each sample with the next one at least MINDT later, so the repaint noise
# cancels in the numerator while dt stays short enough that the controls are
# usually the same at both ends.  A pair spanning a control change is kept (the
# change has to appear SOMEWHERE) but the controls are taken as the earlier read.
MINDT, MAXDT = 12.0, 45.0
ix = []
j = 0
for i in range(len(tt)):
    if j < i + 1:
        j = i + 1
    while j < len(tt) - 1 and tt[j] - tt[i] < MINDT:
        j += 1
    if j < len(tt) and MINDT <= tt[j] - tt[i] <= MAXDT:
        ix.append((i, j))
i0 = np.array([a for a, b in ix])
i1 = np.array([b for a, b in ix])
dt = tt[i1] - tt[i0]
rate = (T[i1] - T[i0]) / dt
print('windowed pairs %d   dt median %.1f s   |rate| median %.0f  max %.0f F/s'
      % (len(rate), np.median(dt), np.median(np.abs(rate)), np.abs(rate).max()))


def design(S, C, F, P, T):
    return np.column_stack([np.ones_like(T), S, C, F, P, T, C * T, F * T])


NAMES = ['const', 'sumPct', 'coolSum', 'fanCount', 'press', 'T', 'cool*T', 'fan*T']


def fit(mask, label):
    X = design(S[i0][mask], C[i0][mask], F[i0][mask], P[i0][mask], 0.5 * (T[i0][mask] + T[i1][mask]))
    y = rate[mask]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss = 1.0 - ((y - pred) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-9)
    print()
    print('--- %s   n=%d   R2=%.3f ---' % (label, int(mask.sum()), ss))
    for n, c in zip(NAMES, coef):
        print('   %-9s %+13.5g' % (n, c))
    return coef


allm = np.ones(len(rate), bool)
fit(allm, 'all windowed pairs')
# Controls held still across the whole window: a clean read of the gains, with a
# much smaller n.  If the two disagree the model is not first-order in these.
still = (np.abs(S[i1] - S[i0]) + np.abs(C[i1] - C[i0]) + np.abs(F[i1] - F[i0])) == 0
print('\nwindows with the controls unchanged end to end: %d' % int(still.sum()))
coef_still = fit(still, 'controls held still across the window')

print()
print('--- what the still-window fit implies (F/s per unit) ---')
for n, c in zip(NAMES, coef_still):
    print('   %-9s %+13.5g' % (n, c))
