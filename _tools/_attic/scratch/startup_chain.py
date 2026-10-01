# Pull the original's start-up message chain out of the recorder captures.
#
# Why this exists: the remake's Config.Shift carries "reconstruction presentation
# defaults, not measured rules" for Boot/Startup/ShutdownSeconds. Before they can
# be replaced by measured values, the message *list* has to be extracted in order,
# with its poll timestamps, from every run we have -- because the order is stable
# across runs but the absolute offsets are not (PROGRESS 64.10).
#
# File format (TRG_original_recorder.luau), three line shapes:
#   S <n> t=<sec> dt=<sec> rd=<sec> key=val|key=val|...   a poll; only written if something changed
#   EVT<n> TEXT <alias> <text to end of line>             a label's text, spaces intact
#   EVT<n> TMAP <alias> <full instance path>              alias -> path, emitted once
# and one special alias:  EVT<n> TEXT log.panel TextLabel=<row>|TextLabel=<row>|TitleText=<title>
# which dumps the whole SYSTEM LOGS panel. That dump is what carries the start-up
# chain, so it is the only thing this script reads.
#
# CORRECTION (2026-10-01): this comment used to say "in reading order". It is not.
# The recorder's snapshot() (TRG_original_recorder.luau ~1649-1670) collects every
# TextLabel under the root, writes "Name=Text" for each and then table.sort()s the
# result, so the dump is alphabetised and carries NO row-order information at all.
# An earlier version of this script relied on that claim and produced a confident,
# wrong row order. chain() below survives the correction because it never used row
# order: it orders messages by their first-appearance TIME, which is a property of
# successive dumps and not of any one dump's row order. Anything that wants the
# on-screen order has to come from the panel's geometry instead -- see PROGRESS.md
# Phase 65.
#
# ASCII only out of this script -- the console here is GBK (memory: windows-console-codec).
import re, glob, os

POLL = re.compile(r'^S (\d+) t=([0-9.]+)')
EVT = re.compile(r'^EVT(\d+) (TEXT|TMAP) ([^ ]+) ?(.*)$')


def scan(path):
    """[(t, rows, title)] for every log.panel dump, in file order.

    t is the poll this dump was noticed on. Events can precede the first poll
    header (the recorder emits its first changes before S 1), so every event is
    first collected with the *preceding* poll time and, where that is None, the
    following one is substituted afterwards. Reading it as 0 would silently
    claim the start-up began at t=0 in every run.
    """
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
        if item[1] == cur:                   # the panel is re-dumped even when static
            continue
        cur = item[1]
        t = prev
        if t is None:                        # before the first poll header
            t = next((r[1] for r in raw[i:] if r[0] == 't'), None)
        out.append((t, item[1], item[2]))
    return out


def chain(path):
    """The start-up messages only, in order, with the t of their first appearance."""
    msgs, firsts, lastrows = [], {}, []
    for t, rows, _title in scan(path):
        for r in rows:
            if not r or r == 'SYSTEM LOGS':
                continue
            if r not in firsts:
                firsts[r] = t
                msgs.append(r)
    return msgs, firsts


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def main():
    runs = {}
    for f in sorted(glob.glob('Data/flow/original_*')):
        dumps = scan(f)
        msgs, firsts = chain(f)
        print('=' * 78)
        print('%s   dumps=%d  distinct rows=%d' % (os.path.basename(f), len(dumps), len(msgs)))
        if not msgs:
            continue
        t0 = firsts[msgs[0]]
        for m in msgs:
            print('  %8.2f  (+%7.2f)  %s' % (firsts[m], firsts[m] - t0, m[:96]))
        runs[os.path.basename(f)] = (msgs, {m: firsts[m] - t0 for m in msgs})

    # ---- the table the remake actually ships, derived rather than transcribed ----
    # Every capture's first distinct row is 'E INITIATED' -- the truncated tail of
    # a previous session's SEQUENCE INITIATED, still sitting in the place's saved
    # TemplateLogFrame3. So the head of the chain is the SEQUENCE INITIATED row,
    # not the first row, and anything timestamped before it is a template artifact
    # (or, for a mid-shift injection, not this start-up at all) and is dropped.
    print('=' * 78)
    print('MEDIAN-OFFSET TABLE  (measured from the SEQUENCE INITIATED row)')
    good, head = {}, None
    for name, (msgs, offs) in sorted(runs.items()):
        start = next((m for m in msgs if 'START-UP SEQUENCE INITIATED' in m), None)
        if start is None:
            print('  skipped %s -- no SEQUENCE INITIATED row at all' % name)
            continue
        rel = {m: offs[m] - offs[start] for m in msgs if offs[m] >= offs[start] - 0.001}
        good[name] = rel
        if head is None:
            head = [m for m in msgs if m in rel]
        else:                                  # keep the union, head-run order first
            for m in msgs:
                if m in rel and m not in head:
                    head.append(m)
    names = sorted(good)
    print('  %d runs: %s' % (len(good), ', '.join(names)))

    def offsets(m):
        return [good[n][m] for n in names if m in good[n]]

    # A row is TRUNK iff every run that got as far as this row carries it. That is
    # what separates the start-up from the two status-message variants and from the
    by_med = sorted((m for m in head if offsets(m)), key=lambda m: median(offsets(m)))
    QUORUM = 4
    trunk = [m for m in by_med if len(offsets(m)) >= QUORUM]
    print('%3s %-62s %8s %3s %8s' % ('#', 'message', 'median', 'n', 'hold'))
    prev, holds = 0.0, []
    for i, m in enumerate(trunk, 1):
        med = median(offsets(m))
        holds.append(med - prev)
        prev = med
        print('%3d %-62s %8.1f %3d %8.1f' % (i, m[:62], med, len(offsets(m)), holds[-1]))
    print('  holds    = %s' % ', '.join('%g' % h for h in holds))
    print('  trunk size = %d   sum of holds = %.1f s' % (len(trunk), sum(holds)))
    below = [m for m in by_med if len(offsets(m)) < QUORUM]
    print('  under the cut: %d rows, most-seen n=%d' % (
        len(below), max((len(offsets(m)) for m in below), default=0)))

    # The per-run matrix behind the medians. Columns are the runs in name order;
    # a dash is a run that never reached that line. Printed because the medians are
    # only as good as the spread underneath them, and the spread is wide.
    print('  --- per-run offsets, seconds from SEQUENCE INITIATED ---')
    print('  %-46s %s' % ('message', ' '.join('%10s' % n[-6:] for n in names)))
    for i, m in enumerate(trunk, 1):
        cells = ['%10s' % ('%.1f' % good[n][m] if m in good[n] else '-') for n in names]
        print('  %2d %-43s %s' % (i, m[-43:], ' '.join(cells)))

    # Independent cross-check: the runs' own end-to-end totals, which were never
    # fed into the medians. A sum-of-medians and a median-of-sums that agree are
    # two estimators derived separately; one tuned to the other would not.
    print('  --- per-run totals to the last trunk row ---')
    tot = offsets(trunk[-1])
    print('    %-50s n=%d  %s  median=%.2f' % (
        trunk[-1][:50], len(tot), ['%.1f' % v for v in sorted(tot)], median(tot)))
    print('  --- variant rows (present in some runs, absent in others) ---')
    for m in by_med:
        if m not in trunk and len(offsets(m)) >= 2:
            print('    n=%d  median=%7.1f  %s' % (len(offsets(m)), median(offsets(m)), m[:66]))


if __name__ == '__main__':
    main()
