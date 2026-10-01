# The cross-check itself: expected (replayed from the raw capture) against
# observed (read off the live instances).  Both sides are text files so the
# comparison can be re-run and re-read without either side being regenerated.
#
# Two independent artifacts, one machine.  The expected side never sees the
# remake's code; the observed side never sees the capture.
#
# ASCII only out (memory: windows-console-codec).
import re, sys

EXPECT = '_tools/_attic/scratch/aux_expect.txt'
OBSERVED = '_tools/_attic/scratch/aux_observed.txt'

ROW = re.compile(r'^\s*t=(\d+)\s+.*?diag=(\S+)\s+log=(\S+)\s+logo=(\d+)\s*$')


def rows(path, stop_at_marker=None):
    found = {}
    stopped = False
    for raw in open(path, encoding='ascii', errors='replace'):
        line = raw.rstrip('\n').rstrip('\r')
        if stop_at_marker and stop_at_marker in line:
            stopped = True
        if stopped:
            continue
        m = ROW.match(line.rstrip())
        if m:
            t, d, l, g = m.groups()
            found[int(t)] = (d, l, g)
    return found


def main():
    # The expected side has two blocks; take only the INTENDED one.
    exp = rows(EXPECT, stop_at_marker='-- FILE-ORDER reading')
    obs = rows(OBSERVED)
    if not exp or not obs:
        print('FAIL  something did not parse: expected=%d observed=%d' % (len(exp), len(obs)))
        return 1

    bad = 0
    past = sorted(t for t in obs if t not in exp)
    for t in sorted(exp):
        e, o = exp[t], obs.get(t)
        if o is None:
            print('FAIL  t=%-3d expected %s but nothing was observed' % (t, e))
            bad += 1
        elif e != o:
            print('FAIL  t=%-3d expected diag=%-9s log=%-4s logo=%s' % ((t,) + e))
            print('            observed diag=%-9s log=%-4s logo=%s' % o)
            bad += 1
        else:
            print('ok    t=%-3d diag=%-9s log=%-4s logo=%s' % ((t,) + e))

    print('')
    print('%d row(s) compared, %d mismatch(es)' % (len(exp), bad))
    if bad:
        print('the module does NOT reproduce the capture')
        return 1
    print('every second of the boot window equals the capture replay')

    if past:
        print('')
        print('observed beyond the capture window, NOT adjudicated by it:')
        for t in past:
            print('  t=%-3d diag=%-9s log=%-4s logo=%s' % ((t,) + obs[t]))
        print('')
        print('  The capture never writes BootFrame.Visible, so it cannot say')
        print('  whether the original hides this screen at the Ready transition or')
        print('  leaves it layered under the next one.  The remake hides it')
        print('  (RoomShell.applyMonitors clears every owned face first).  That is a')
        print('  difference in HOW the screens are swapped, not in what is on them,')
        print('  and it is recorded as unmeasured rather than counted as a match.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
