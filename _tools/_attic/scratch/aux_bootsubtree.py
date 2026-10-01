# Fifth pass: the BootFrame subtree itself, as the original writes it.
#
# The operator handed the capture over specifically as "direct evidence for the
# start-up screen", so the thing worth extracting is not the tally but the SHAPE
# of the screen: which sub-frames exist under BootFrame, in what order they are
# revealed, and what they say.  That is what the remake's BootFrame has to be
# compared against.
#
# Names only, values only where they are text: the Position/Size churn is
# animation and is already counted in aux_report.txt.
#
# ASCII only out (memory: windows-console-codec).
import re, io, collections

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_bootsubtree.txt'

L = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')
ROOT = 'MainControlRoomMonitor'


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def main():
    # subpath (below BootFrame) -> prop -> sorted list of (t, val)
    sub = collections.defaultdict(lambda: collections.defaultdict(list))
    t0 = None
    for raw in io.TextIOWrapper(open(SRC, 'rb'), encoding='utf-8', errors='replace'):
        m = L.match(raw.rstrip('\n').rstrip('\r'))
        if not m:
            continue
        t, path, prop, val = m.groups()
        s = secs(t)
        if t0 is None:
            t0 = s
        i = path.find('.MonitorUI.BootFrame')
        if i < 0 or ROOT not in path:
            continue
        rest = path[i + len('.MonitorUI.BootFrame'):]
        if not rest:
            rest = '<BootFrame itself>'
        sub[rest][prop].append((s - t0, val))

    w = open(OUT, 'w', encoding='ascii', errors='replace')

    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    p('BootFrame subtree as seen on %s (t relative to the MonitorBootButton click)' % ROOT)
    p('%d distinct descendant paths below BootFrame' % len(sub))
    p('')
    for rest in sorted(sub):
        props = sub[rest]
        p(rest)
        for prop in sorted(props):
            vs = sorted(props[prop])
            times = sorted(set(t for t, _ in vs))
            span = 't=%d..%d n=%d' % (times[0], times[-1], len(vs)) if times else ''
            if prop in ('Text', 'Name'):
                seen, kept = set(), []
                for t, v in vs:
                    if v not in seen:
                        seen.add(v)
                        kept.append((t, v[:80]))
                p('    %-22s %s  distinct=' % (prop, span))
                for t, v in kept[:40]:
                    p('        t=%-5d %s' % (t, v))
            else:
                vals = sorted(set(v for _, v in vs))
                p('    %-22s %s  values=%s' % (prop, span, vals[:8]))

    w.close()
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
