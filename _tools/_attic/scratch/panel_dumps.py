# Dump the raw log.panel captures in file order, to answer one question the
# distinct-row view in startup_chain.py destroys: when the panel holds fewer than
# three messages, which row do they occupy?
#
# RESULT (2026-10-01): the question is not answerable from these captures, and this
# script's premise was wrong. The recorder's snapshot() sorts its rows, so a dump
# lists the same labels alphabetised no matter where they sit on the glass; "which
# row" is not in the bytes. What the dumps DID settle is the row COUNT over time --
# 27 at once during a duplicate-message flood in original_260926-230049, with rows
# retiring in arrival order -- and that, plus the panel's own geometry, is what
# decided the remake's four-row window. See PROGRESS.md Phase 65 and panel_growth.py.
#
# Kept because the "any dump carrying an empty row?" scan at the bottom is still the
# cheapest way to see the authored ['', '', 'E INITIATED'] state in a live capture.
#
# ASCII only (console is GBK).
import re, glob, os

POLL = re.compile(r'^S (\d+) t=([0-9.]+)')
EVT = re.compile(r'^EVT(\d+) (TEXT|TMAP) ([^ ]+) ?(.*)$')


def dumps(path):
    """[(t, [rows])] for every distinct log.panel dump, in file order."""
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
        rows, title = [], ''
        for kv in rest.split('|'):
            k, _, v = kv.partition('=')
            if k == 'TextLabel':
                rows.append(v)
            elif k == 'TitleText':
                title = v
        raw.append(('ev', rows, title))

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
        print('=' * 78)
        print(os.path.basename(f))
        for n, (t, rows) in enumerate(ds[:8]):
            print('  [%2d] t=%-8s rows=%d  %s' % (n, t, len(rows), repr(rows)))
        # Which dumps ever carry an empty row? Those are the informative ones.
        empties = [(n, t, rows) for n, (t, rows) in enumerate(ds) if any(r == '' for r in rows)]
        print('  -- dumps=%d  with-an-empty-row=%d' % (len(ds), len(empties)))
        for n, t, rows in empties[:12]:
            print('     [%2d] t=%-8s %s' % (n, t, repr(rows)))


if __name__ == '__main__':
    main()
