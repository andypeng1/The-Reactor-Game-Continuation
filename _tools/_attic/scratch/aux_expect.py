# Seventh pass: what the boot screen should look like, second by second, read
# straight out of the raw capture.
#
# This is the OTHER SIDE of a cross-check.  BootPanel's schedule lives in
# Config.Shell.BootScreen and was transcribed from the same capture, so comparing
# the module against the table would only prove the module reads its own table.
# This file replays the capture's Visible writes directly and prints the same
# signature the module is asked for, so the two agree only if the module really
# reproduces the machine.
#
# ASCII only out (memory: windows-console-codec).
import re, io, collections

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_expect.txt'
ROOT = 'MainControlRoomMonitor'
MAXT = 13

L = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')
DIAG = re.compile(r'\.MonitorUI\.BootFrame\.DiagnosticFrame\.ScrollingFrame\.TextLabel(\d+)$')
LOGT = re.compile(r'\.MonitorUI\.BootFrame\.LogFrame\.TitleText(\d+)$')
LOGO = re.compile(r'\.MonitorUI\.BootFrame\.CompanyLogo$')


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def ranges(nums):
    nums = sorted(nums)
    if not nums:
        return '-'
    out, start, prev = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append((start, prev))
        start = prev = n
    out.append((start, prev))
    return ','.join(str(a) if a == b else '%d-%d' % (a, b) for a, b in out)


def main():
    events = []
    ties = []
    seen_at = set()
    for raw in io.TextIOWrapper(open(SRC, 'rb'), encoding='utf-8', errors='replace'):
        m = L.match(raw.rstrip('\n').rstrip('\r'))
        if not m:
            continue
        t, path, prop, val = m.groups()
        if prop != 'Visible' or ROOT not in path:
            continue
        s = secs(t)
        if DIAG.search(path):
            key, kind, n = ('d', int(DIAG.search(path).group(1))), 'd', int(DIAG.search(path).group(1))
        elif LOGT.search(path):
            key, kind, n = ('l', int(LOGT.search(path).group(1))), 'l', int(LOGT.search(path).group(1))
        elif LOGO.search(path):
            key, kind, n = ('g', 0), 'g', 0
        else:
            continue
        if (s, key) in seen_at:
            ties.append((s, key))
        seen_at.add((s, key))
        events.append((s, kind, n, val == 'true'))

    t0 = min(e[0] for e in events)
    w = open(OUT, 'w', encoding='ascii', errors='replace')

    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    p('=== EXPECTED boot screen, replayed from the raw capture, %s ===' % ROOT)
    p('(signature is the same one the module is asked for)')
    p('')

    def replay(rule):
        # rule('last', prev, val) -> the state a second ends in, given the writes
        # that second contains in FILE order and the state it started from.
        state = {}
        rows = []
        for rel in range(0, MAXT + 1):
            for s, kind, n, val in events:
                if s - t0 == rel:
                    state[(kind, n)] = rule(state.get((kind, n)), val)
            diag = [n for (k, n), v in state.items() if k == 'd' and v]
            log = [n for (k, n), v in state.items() if k == 'l' and v]
            logo = state.get(('g', 0), False)
            rows.append((rel, ranges(diag), ranges(log), 1 if logo else 0))
        return rows

    file_order = replay(lambda prev, val: val)

    # Where the two readings part company.  A label with exactly one write in a
    # second ends that second in the written state.  A label with BOTH a false and
    # a true write in one second is a blanket-hide followed by a show-one, and the
    # capture cannot say which line the writer emitted first: the file is not in
    # time order even inside a second, and file order happens to put 'false' last
    # for TitleText6 at t=5, which would blank the log frame until the quick boot
    # at t=153.  The quick boot writes the same pair again at t=154 and ends with
    # the line SHOWN, so 'true' is what a both-values second means here.  (No
    # show-then-hide pair exists in this capture; if one ever does, this rule
    # reads it wrong, which is why it is written down instead of assumed.)
    def replay_pairs():
        state = {}
        rows = []
        for rel in range(0, MAXT + 1):
            vals = collections.defaultdict(set)
            for s, kind, n, val in events:
                if s - t0 == rel:
                    vals[(kind, n)].add(val)
            for key, vs in vals.items():
                state[key] = True in vs
            diag = [n for (k, n), v in state.items() if k == 'd' and v]
            log = [n for (k, n), v in state.items() if k == 'l' and v]
            logo = state.get(('g', 0), False)
            rows.append((rel, ranges(diag), ranges(log), 1 if logo else 0))
        return rows

    intended = replay_pairs()

    p('-- INTENDED reading (data the module is checked against)')
    for rel, d, l, g in intended:
        p('t=%-2d diag=%-8s log=%-4s logo=%d' % (rel, d, l, g))

    p('')
    p('-- FILE-ORDER reading, for comparison')
    diff = [r for r, i in zip(file_order, intended) if r != i]
    if not diff:
        p('identical to the intended reading: no second in this window contains two')
        p('writes of one label whose order would matter.')
    else:
        for rel, d, l, g in diff:
            p('t=%-2d diag=%-8s log=%-4s logo=%d' % (rel, d, l, g))
        p('')
        p('the readings differ in %d second(s); the cause is listed below.' % len(diff))

    p('')
    p('=== the same label written twice inside one second (order inside a second is not recoverable) ===')
    for s, key in sorted(set(ties)):
        p('  at t=%d  %s' % (s - t0, key))

    w.close()
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
