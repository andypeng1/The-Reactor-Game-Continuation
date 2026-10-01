# Third pass: the capture is NOT in file order.
#
# Walking it, seconds climb 0..38, jump to 149..158, then resume at 48..110 --
# exactly one backward jump, i.e. the writer flushed its last buffer before its
# middle one. The Time: stamp is the truth, the file order is a delivery artifact.
# Real chronology: 0..38, a 10 s silent gap, 48..110, a 38 s silent gap, 149..158.
#
# So: sort by time, then report the drama rather than the animation.
# ASCII only out (memory: windows-console-codec).
import re, io, collections

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_narrative.txt'

L = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')
NUMERIC = re.compile(r'^[0-9.,% -]*$')


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def main():
    rows = []
    for raw in io.TextIOWrapper(open(SRC, 'rb'), encoding='utf-8', errors='replace'):
        m = L.match(raw.rstrip('\n').rstrip('\r'))
        if m:
            t, path, prop, val = m.groups()
            rows.append((secs(t), path, prop, val))
    rows.sort(key=lambda r: (r[0],))
    t0 = rows[0][0]

    w = open(OUT, 'w', encoding='ascii', errors='replace')

    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    def short(path):
        return (path.replace('Workspace.Monitors.', '')
                    .replace('.Screen.MonitorUI', ''))

    p('=== NARRATIVE: first write to each (path, property), in real time order ===')
    seen = set()
    for t, path, prop, val in rows:
        key = (path, prop)
        if key in seen:
            continue
        seen.add(key)
        p('%5d  %-20s %-24s %s' % (t - t0, prop, val[:70], short(path)))
    p('  distinct (path,property) pairs = %d' % len(seen))

    p('')
    p('=== VISIBLE WRITES outside the alert blinker ===')
    for t, path, prop, val in rows:
        if prop != 'Visible' or '.AlertsFrame.' in path:
            continue
        p('%5d  %-6s %s' % (t - t0, val, short(path)))

    p('')
    p('=== TEXT WRITES that are not plain numbers ===')
    prev = {}
    for t, path, prop, val in rows:
        if prop != 'Text' or NUMERIC.match(val):
            continue
        if prev.get(path) == val:
            continue
        prev[path] = val
        p('%5d  %-68s %s' % (t - t0, short(path), val[:90]))

    p('')
    p('=== VISIBLE toggle counts per path (the blinker, ranked) ===')
    vs = collections.Counter()
    for t, path, prop, val in rows:
        if prop == 'Visible':
            vs[short(path)] += 1
    for k, v in vs.most_common(25):
        p('  %6d  %s' % (v, k))

    p('')
    p('=== per-second write counts (all properties) ===')
    per = collections.Counter(t - t0 for t, _, _, _ in rows)
    for k in sorted(per):
        p('  %5d  %8d  %s' % (k, per[k], '#' * min(50, per[k] // 400)))

    w.close()
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
