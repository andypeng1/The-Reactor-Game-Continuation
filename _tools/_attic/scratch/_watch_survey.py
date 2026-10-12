"""Survey the original-game watches: what changed, in which container, when.

Reads Data/originalwatch/*/changes.log (format:
    t=0000047.93 20:09:23 | Container | Full.Path | old | new)
and reports, per run, the time span and the container tally, then -- for the
runs long enough to carry a start-up -- a per-10-second histogram of the
containers whose changes are *the start-up*, so the shape of the original's
boot can be read off the recording instead of invented.

ASCII output only: this console is GBK and print() of anything else dies.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')
WATCH = ROOT / 'Data' / 'originalwatch'
LINE = re.compile(r'^t=(\d+\.\d+) \d\d:\d\d:\d\d \| ([^|]+?) \| (.+?) \| (.*)$')

# The containers the start-up is made of, versus the ones that are just the
# plant idling (monitors redraw every tick; Stats carries the sim's own values).
INTEREST = ('Lights', 'ReactorCBLs', 'Core', 'Effects', 'METU', 'ChamberWalls',
            'GravityLens', 'MovingParts', 'Alarms')


def read(run):
    log = run / 'changes.log'
    if not log.exists():
        return []
    rows = []
    for raw in log.read_text(encoding='utf-8', errors='replace').splitlines():
        m = LINE.match(raw)
        if m:
            rows.append((float(m.group(1)), m.group(2).strip(),
                         m.group(3).strip(), m.group(4)))
    return rows


def detail(run, rows, container, depth=2):
    """For one container: which sub-group and which property moved, and when
    the first one did.  The first-change time is the start-up beat -- it says
    'this thing came on at second N' without anyone having to read a curve."""
    groups = defaultdict(lambda: {'n': 0, 'first': None, 'props': Counter()})
    for t, c, path, _v in rows:
        if c != container:
            continue
        segs = path.split('.')
        g = '.'.join(segs[:depth])
        prop = segs[-1]
        e = groups[g]
        e['n'] += 1
        e['props'][prop] += 1
        if e['first'] is None or t < e['first']:
            e['first'] = t
    print('-- %s / %s : %d group(s)' % (run.name, container, len(groups)))
    for g in sorted(groups, key=lambda g: groups[g]['first']):
        e = groups[g]
        tops = ' '.join('%s:%d' % kv for kv in e['props'].most_common(4))
        print('   t=%7.1f  %-34s n=%-5d %s' %
              (e['first'], g[:34], e['n'], tops))


def main():
    for run in sorted(p for p in WATCH.iterdir() if p.is_dir()):
        rows = read(run)
        if not rows:
            print('%s: no changes.log' % run.name)
            continue
        span = (min(r[0] for r in rows), max(r[0] for r in rows))
        tally = Counter(r[1] for r in rows)
        print('== %s  %d line(s)  t=%.1f..%.1f s' % (run.name, len(rows),
                                                     span[0], span[1]))
        for name, n in tally.most_common(12):
            print('     %-18s %5d' % (name, n))
    print()
    print('=== per-10s histogram of the interesting containers ===')
    for run in sorted(p for p in WATCH.iterdir() if p.is_dir()):
        rows = [r for r in read(run) if r[1] in INTEREST]
        if not rows:
            continue
        buckets = defaultdict(Counter)
        for t, container, _path, _v in rows:
            buckets[int(t // 10) * 10][container] += 1
        print('-- %s  (%d interesting change(s))' % (run.name, len(rows)))
        for t0 in sorted(buckets):
            cells = ' '.join('%s=%d' % kv for kv in
                             sorted(buckets[t0].items(), key=lambda kv: -kv[1]))
            print('   t=%3d-%3d  %s' % (t0, t0 + 10, cells))
    print()
    print('=== first change per sub-group, per container ===')
    for run in sorted(p for p in WATCH.iterdir() if p.is_dir()):
        rows = read(run)
        if len(rows) < 3000:            # a census, not a session
            continue
        for container in ('Lights', 'ReactorCBLs', 'Core', 'Alarms'):
            detail(run, rows, container)
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
