"""Shape of the temperature curve vs. the controls, from a real capture.

Scratch: answers "can a temperature model be read off this file", before
anything is committed to _tools/.
"""
import collections
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'Data/flow/original_260926-230049'

KEYS = ['m.temp', 'm.press', 'm.fluct', 's.Core.RadiationVal',
        'c.cbl1Pct', 'c.cbl2Pct', 'c.cbl3Pct', 'c.cbl1Lvl', 'c.cbl2Lvl', 'c.cbl3Lvl',
        'c.cool1', 'c.cool2', 'c.cool3', 'c.coolSum', 'c.fanCount',
        'c.fan1', 'c.fan2', 'c.fan3', 'c.fan4', 'c.fan5', 'c.fan6',
        's.HDEF.IntegrityVal']

rows = []
cur = {}
for ln in open(SRC, encoding='utf-8', errors='replace'):
    if ln[:2] not in ('S ', 'B '):
        continue
    p = ln.split()
    t = float(p[2][2:])
    changes = {}
    for tok in p[3:]:
        if '=' not in tok:
            continue
        k, v = tok.split('=', 1)
        if k in KEYS:
            changes[k] = v
    cur = dict(cur)
    cur.update(changes)
    rows.append((t, dict(cur), changes))

print('samples %d  t %.2f .. %.2f' % (len(rows), rows[0][0], rows[-1][0]))
print()
print('=== control changes (t, key, old -> new) ===')
last = {}
for t, st, ch in rows:
    for k, v in ch.items():
        if not k.startswith('c.'):
            continue
        if last.get(k) != v:
            print('  t=%7.2f  %-12s %s -> %s   (temp=%s press=%s)' % (
                t, k, last.get(k, '-'), v, st.get('m.temp'), st.get('m.press')))
            last[k] = v
print()
print('=== decimated state (every ~20 s) ===')
print('t      temp   press  fluct  cbl1/2/3Pct      cblLvl   cool  fans  rad')
nxt = 0.0
for t, st, ch in rows:
    if t < nxt:
        continue
    nxt = t + 20
    print('%7.1f %6s %6s %6s  %-15s %-8s %-5s %-5s %s' % (
        t, st.get('m.temp'), st.get('m.press'), st.get('m.fluct'),
        '/'.join(str(st.get('c.cbl%dPct' % i, '-')) for i in (1, 2, 3)),
        '/'.join(str(st.get('c.cbl%dLvl' % i, '-')) for i in (1, 2, 3)),
        st.get('c.coolSum'), st.get('c.fanCount'), st.get('s.Core.RadiationVal')))
