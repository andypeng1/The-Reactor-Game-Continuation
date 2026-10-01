# How many message rows does the original's log panel hold at once, and does the
# count ever fall?
#
# Why: the recorder's snapshot() walks every TextLabel under MainMonitorFrame and
# writes "Name=Text" sorted, empties dropped. So the row count in a dump is the
# number of non-empty labels in that whole subtree -- and the 09-30 run reached six
# message rows at once, which three fixed rows cannot hold. Before LogPanel can
# claim to render the original's panel, the shape of that list has to be known:
# is it a growing session log, or a fixed window?
#
# ASCII only (console is GBK).
import re, glob, os

POLL = re.compile(r'^S (\d+) t=([0-9.]+)')
EVT = re.compile(r'^EVT(\d+) (TEXT|TMAP) ([^ ]+) ?(.*)$')
TITLE = 'SYSTEM LOGS'


def dumps(path):
    raw, cur = [], None
    for line in open(path, 'rb').read().decode('utf-8', 'replace').splitlines():
        m = POLL.match(line)
        if m:
            raw.append(('t', float(m.group(2))))
            continue
        m = EVT.match(line)
        if not m:
            continue
        _, kind, alias, rest = m.groups()
        if kind != 'TEXT' or alias != 'log.panel':
            continue
        rows = [kv.partition('=')[2] for kv in rest.split('|') if kv.startswith('TextLabel=')]
        raw.append(('ev', rows))

    out, prev = [], None
    for i, item in enumerate(raw):
        if item[0] == 't':
            prev = item[1]
            continue
        if item[1] == cur:
            continue
        cur = item[1]
        t = prev
        if t is None:
            t = next((r[1] for r in raw[i:] if r[0] == 't'), None)
        out.append((t, item[1]))
    return out


def main():
    for f in sorted(glob.glob('Data/flow/original_*')):
        ds = dumps(f)
        if not ds:
            continue
        print('=' * 78)
        print(os.path.basename(f))
        seen, counts, maxn = set(), [], 0
        for t, rows in ds:
            msgs = [r for r in rows if r != TITLE]
            counts.append((t, len(msgs)))
            maxn = max(maxn, len(msgs))
            seen.update(msgs)
        print('  dumps=%d  max-row-count=%d  distinct-rows-ever=%d' % (len(ds), maxn, len(seen)))
        print('  counts over time: ' + ' '.join('%d' % c for _, c in counts))
        # does any row ever leave? compare each dump's set against the previous
        prev = set()
        for t, rows in ds:
            cur = set(r for r in rows if r != TITLE)
            gone = prev - cur
            if gone:
                print('  t=%-8s lost: %s' % (t, sorted(gone)))
            prev = cur


if __name__ == '__main__':
    main()
