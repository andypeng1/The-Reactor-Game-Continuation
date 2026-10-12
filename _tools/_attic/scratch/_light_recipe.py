"""Extract the original game's own start-up recipe for a container.

For one run's changes.log and one container, print every distinct
(path-after-the-container, property, old -> new) recipe with a count, so the
"what does ON look like" can be read off the recording instead of guessed.

Paths carry the watcher's own duplicate-name disambiguator ` ~(x, y, z)`; it is
stripped here, because it is the *watcher's* addressing, not the game's.

ASCII output only: this console is GBK.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')
WATCH = ROOT / 'Data' / 'originalwatch'
LINE = re.compile(r'^t=(\d+\.\d+) \d\d:\d\d:\d\d \| ([^|]+?) \| (.+?) \| (.*)$')
TILDE = re.compile(r'\s*~\([^)]*\)')
DROP = {'DESTROYED', 'ADDED'}


def read(run):
    rows = []
    log = run / 'changes.log'
    if not log.exists():
        return rows
    for raw in log.read_text(encoding='utf-8', errors='replace').splitlines():
        m = LINE.match(raw)
        if m:
            rows.append((float(m.group(1)), m.group(2).strip(),
                         TILDE.sub('', m.group(3).strip()), m.group(4).strip()))
    return rows


def main():
    run = WATCH / sys.argv[1]
    container = sys.argv[2]
    keep = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    rows = [r for r in read(run) if r[1] == container]
    recipes = Counter()
    first = {}
    for t, _c, path, val in rows:
        segs = path.split('.')[1:]                  # drop the container itself
        prop = segs[-1]
        if prop in DROP:
            continue
        key = '.'.join(segs[max(0, len(segs) - 1 - keep):])
        recipes[(key, val)] += 1
        if key not in first:
            first[key] = t
    print('== %s / %s : %d change(s) (%d in recipes)' %
          (run.name, container, len(rows), sum(recipes.values())))
    for (key, val), n in recipes.most_common(60):
        print('   %6d  first=t%8.1f  %-46s  %s' %
              (n, first[key], key[:46], val[:58]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
