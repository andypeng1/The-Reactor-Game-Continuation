"""The part of the model this file CAN identify: per-setting response.

The regression is the wrong instrument here and the reason is structural, not
statistical -- the operator moved every control in RESPONSE to the temperature,
so the regressors are collinear with the thing they explain and the individual
gains come out with the wrong sign. That is property of the file, not of the
method: a session in which someone is flying the machine is not a step-response
experiment.

What survives is the coarser read. Segment the run on "the controls did not
move", and for each stretch report what the temperature did on its own:

  * a stretch that is flat gives an EQUILIBRIUM TEMPERATURE for that control
    setting -- a point of the lookup table, no regression needed;
  * a stretch that is monotone gives a time constant, by fitting
    T(t) = Teq + (T0 - Teq)exp(-t/tau) over the coarse differences.

Those are the two numbers a remake needs, and neither one requires the operator
to have done anything in particular.
"""
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
        rows.append((t, float(cur['m.temp']),
                     sum(float(cur.get('c.cbl%dPct' % i) or 0) for i in (1, 2, 3)),
                     float(cur['c.coolSum'] or 0), float(cur['c.fanCount'] or 0)))

# Collapse to one entry per change of (S, C, F): a segment is a maximal run where
# the inputs are constant BY VALUE, not by "no event" -- the recorder only writes
# changes, so the run has to be reconstructed from the writes that did happen.
segs = []
for t, T, S, C, F in rows:
    key = (S, C, F)
    if segs and segs[-1][0] == key:
        segs[-1][1].append(t)
        segs[-1][2].append(T)
    else:
        segs.append([key, [t], [T]])
print('segments: %d   (a segment = inputs bit-identical, however long it lasts)')
print()
print('  dur    t0     t1     cblPct cool fan   T0      T1     slope F/s   flat?')
useful = []
for (S, C, F), ts, Ts in segs:
    dur = ts[-1] - ts[0]
    if dur < 20 or len(ts) < 8:
        continue
    ts, Ts = np.array(ts), np.array(Ts)
    a = np.polyfit(ts, Ts, 1)
    span = Ts.max() - Ts.min()
    flat = span < 300
    useful.append((dur, S, C, F, Ts[0], Ts[-1], a[0], flat, ts, Ts))
    print('%6.1f %6.0f %6.0f  %6.0f %4.0f %4.0f  %7.0f %7.0f  %+9.1f   %s'
          % (dur, ts[0], ts[-1], S, C, F, Ts[0], Ts[-1], a[0], 'FLAT' if flat else ''))

print()
print('=== flat stretches = points of the equilibrium table ===')
for dur, S, C, F, T0, T1, slope, flat, ts, Ts in useful:
    if flat:
        print('  cblPct=%3.0f  cool=%d  fan=%d  ->  Teq ~ %.0f F  (held %.0f s, drift %+.1f F/s)'
              % (S, C, F, (T0 + T1) / 2, dur, slope))

print()
print('=== monotone stretches: exponential fit for tau ===')
print('  (fit only where the move is big enough that tau is not noise)')
for dur, S, C, F, T0, T1, slope, flat, ts, Ts in useful:
    if flat or abs(T1 - T0) < 800:
        continue
    best = None
    for Teq in np.arange(min(T0, T1) - 20000, max(T0, T1) + 20000, 250.0):
        y = np.log(np.maximum(np.abs(Ts - Teq), 1e-6)) * np.sign(Ts - Teq)
        # only meaningful on one side of Teq; skip windows that straddle it
        if (Ts - Teq).min() < 0 < (Ts - Teq).max():
            continue
        A = np.column_stack([np.ones_like(ts), -ts])
        coef, *_ = np.linalg.lstsq(A, np.log(np.abs(Ts - Teq)), rcond=None)
        res = ((A @ coef - np.log(np.abs(Ts - Teq))) ** 2).sum()
        if best is None or res < best[0]:
            best = (res, Teq, coef[1], coef[0])
    if best:
        res, Teq, invtau, c0 = best
        print('  cblPct=%3.0f cool=%d fan=%d  %.0f->%.0f F over %.0f s:  Teq~%.0f  tau~%.1f s'
              % (S, C, F, T0, T1, dur, Teq, 1.0 / max(invtau, 1e-9)))
