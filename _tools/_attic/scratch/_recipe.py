"""Print one container's property recipe from an original-game watch.

For every distinct (path, old -> new) in the window, print the FIRST time it
happens and how many times it happened, so a start-up beat can be read off the
recording instead of invented.  A per-unit prefix (the leading segments that
differ per copy -- IndustrialAlarm3., Reactor_Laser_Mk3_2.) is folded away, so
the eight alarms collapse to one recipe.

usage: _recipe.py <run> <container> [t0] [t1] [--raw]

ASCII output only: this console is GBK.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')
WATCH = ROOT / 'Data' / 'originalwatch'
LINE = re.compile(r'^t=(\d+\.\d+) \d\d:\d\d:\d\d \| ([^|]+?) \| (.+?) \| (.*)$')
TILDE = re.compile(r'\s*~\([^)]*\)')
DUP = re.compile(r' #[0-9]+(?=\.|$)')
DROP = {'DESTROYED', 'ADDED'}


def fold(path, container):
    """Drop the container and every segment up to and including the last one
    that looks like a per-copy suffix (Name<digits>), plus the watcher's own
    ' #n' duplicate marks."""
    segs = DUP.sub('', path).split('.')
    while segs and segs[0] != container:        # containers are nested too
        segs.pop(0)
    segs = segs[1:]
    for i, s in enumerate(segs):
        if re.search(r'\d$', s):
            nxt = i + 1
            if nxt < len(segs):
                return '.'.join(segs[nxt:])
    return '.'.join(segs)


def main():
    argv = [a for a in sys.argv[1:] if a != '--raw']
    raw = '--raw' in sys.argv
    run = WATCH / argv[0]
    container = argv[1]
    t0 = float(argv[2]) if len(argv) > 2 else 0.0
    t1 = float(argv[3]) if len(argv) > 3 else 1e9

    rows = []
    for line in (run / 'changes.log').read_text(encoding='utf-8',
                                                errors='replace').splitlines():
        m = LINE.match(line)
        if not m:
            continue
        t = float(m.group(1))
        if not (t0 <= t <= t1) or m.group(2).strip() != container:
            continue
        path = TILDE.sub('', m.group(3).strip())
        if not raw:
            path = fold(path, container)
        if path.split('.')[-1] in DROP:
            continue
        rows.append((path, m.group(4).strip(), t))

    seen = defaultdict(Counter)
    first = {}
    for path, val, t in rows:
        seen[path][val] += 1
        first.setdefault(path, t)

    print('== %s / %s  t=%.1f..%.1f : %d change(s), %d distinct path(s)'
          % (run.name, container, t0, t1, len(rows), len(seen)))
    for path in sorted(seen, key=lambda p: (first[p], p)):
        vals = ' ; '.join('%s x%d' % (v, n) for v, n in seen[path].most_common(6))
        print('  t=%7.2f  %-58s  %s' % (first[path], path[:58], vals[:110]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
