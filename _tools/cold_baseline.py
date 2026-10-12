"""Recover the facility's authored (cold) property values from the recorder runs.

Why this exists
---------------
`FacilityCascade` captures its own baseline by reading the world at Initialize
and puts it back on rewind.  That is the right design for a place that is saved
cold, and it is why a probe that lights the world in Edit mode destroys the
baseline: the next Initialize captures the lit state as "authored", and the
start-up then has nothing to show.

The recording is the way out.  Every line of `changes.log` is
`old -> new`, so the `old` of a path's EARLIEST appearance is that path's value
at t=0 -- exactly the authored state -- and our facility was copied from the
original, so the instance paths match by construction (Config's own paths were
derived from these same logs).

Output: a tab-separated `path<TAB>property<TAB>value`, one line per distinct
property, which Studio fetches over localhost (never through the clipboard, and
never through an edit tool that would decode escapes -- CLAUDE.md 0.10).

usage: cold_baseline.py <out.tsv> [container ...]

ASCII output only: this console is GBK.
"""
import re
import sys
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')
WATCH = ROOT / 'Data' / 'originalwatch'
DEFAULT = ['Lights', 'ReactorCBLs', 'Alarms', 'Core']

# The watcher disambiguates duplicate names with ` ~(x, y, z)` and ` #n`; both
# are the WATCHER's addressing, not the game's, so neither survives into a path
# we can resolve in our own place.
TILDE = re.compile(r' ~\([^)]*\)')
HASH = re.compile(r' #[0-9]+')
TIME = re.compile(r'^t=([0-9.]+) [0-9:]+$')


def rows(run):
    """Yield (t, container, path, old, new) for one run.

    Split from the RIGHT, never with a regex over the tail: `.` matches `|`, so
    a lazy group for the path and a greedy one for the values both happily
    swallow a ` | ` and hand back `path | old` as the path and the new value as
    the old one -- which reads as a perfectly plausible table in which every
    lamp's cold colour is its lit colour."""
    for raw in (run / 'changes.log').read_text(encoding='utf-8',
                                               errors='replace').splitlines():
        head, old, new = raw.rsplit(' | ', 2)
        fields = head.split(' | ', 2)
        if len(fields) != 3:
            continue
        m = TIME.match(fields[0].strip())
        if not m:
            continue
        yield (float(m.group(1)), fields[1].strip(), fields[2].strip(),
               old.strip(), new.strip())


def main():
    out_path = Path(sys.argv[1])
    keep = sys.argv[2:] or DEFAULT
    best = {}                       # (path, prop) -> (t, value)
    per_container = {}
    for run in sorted(WATCH.iterdir()):
        log = run / 'changes.log'
        if not log.exists():
            continue
        for t, container, path, old, new in rows(run):
            if container not in keep:
                continue
            path = HASH.sub('', TILDE.sub('', path)).strip()
            prop = path.rsplit('.', 1)[-1]
            per_container[container] = per_container.get(container, 0) + 1
            key = (path, prop)
            prev = best.get(key)
            if prev is None or t < prev[0]:
                best[key] = (t, old)

    table = sorted(best.items())
    lines = ['%s\t%s\t%s' % (p, prop, value) for (p, prop), (t, value) in table]
    # newline='' with an explicit '\n': the repo pins `* text=auto eol=lf`, and
    # Path.write_text translates '\n' to os.linesep on Windows, so the default
    # would leave a CRLF file in an LF tree -- which git then rewrites on the
    # next touch, leaving the working copy permanently dirty with an empty diff.
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(lines) + '\n')

    print('containers scanned: %s' % ', '.join('%s=%d' % kv
                                               for kv in sorted(per_container.items())))
    print('distinct path/property pairs: %d  ->  %s' % (len(lines), out_path))
    by_prop = {}
    for (p, prop), (t, value) in table:
        by_prop[prop] = by_prop.get(prop, 0) + 1
    print('by property: %s' % ', '.join('%s=%d' % kv
                                        for kv in sorted(by_prop.items(),
                                                         key=lambda kv: -kv[1])[:14]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
