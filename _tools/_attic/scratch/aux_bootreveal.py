# Sixth pass: the exact reveal schedule of the boot screen.
#
# The operator handed the capture over as "direct evidence for the start-up
# screen", and a screen is a schedule: which line appears when.  The remake's
# BootFrame already carries the same art (45 ScrollingFrame labels, 6 LogFrame
# titles, a CompanyLogo) but nothing animates it -- so the numbers below are the
# animation table, not a description.
#
# Emitted as a Lua-ready table so the module that consumes it can be checked
# against this file line by line.
#
# ASCII only out (memory: windows-console-codec).
import re, io, collections

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_bootreveal.txt'
ROOT = 'MainControlRoomMonitor'

L = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def main():
    first_true = {}
    allvis = collections.defaultdict(list)
    t0 = None
    for raw in io.TextIOWrapper(open(SRC, 'rb'), encoding='utf-8', errors='replace'):
        m = L.match(raw.rstrip('\n').rstrip('\r'))
        if not m:
            continue
        t, path, prop, val = m.groups()
        s = secs(t)
        if t0 is None:
            t0 = s
        if prop != 'Visible' or ROOT not in path:
            continue
        i = path.find('.MonitorUI.BootFrame')
        if i < 0:
            continue
        rest = path[i + len('.MonitorUI.BootFrame'):]
        allvis[rest].append((s - t0, val))
        if val == 'true' and rest not in first_true:
            first_true[rest] = s - t0

    w = open(OUT, 'w', encoding='ascii', errors='replace')

    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    p('=== BootFrame reveal schedule, %s, t = seconds after the MonitorBootButton click ===' % ROOT)
    p('')
    p('-- every BootFrame descendant that was ever made visible, with the second it happened')
    for rest in sorted(first_true, key=lambda r: (first_true[r], r)):
        toggles = sorted(allvis[rest])
        p('  t=%-4d %-46s all-toggles=%s' % (first_true[rest], rest, toggles))

    p('')
    p('-- grouped by second (what the screen shows when)')
    by_t = collections.defaultdict(list)
    for rest, t in first_true.items():
        by_t[t].append(rest)
    for t in sorted(by_t):
        p('  t=%-4d %3d  %s' % (t, len(by_t[t]), ', '.join(sorted(by_t[t])[:6])
                                + (' ...' if len(by_t[t]) > 6 else '')))

    w.close()
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
