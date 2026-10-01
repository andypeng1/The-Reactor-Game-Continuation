# Read the auxiliary capture: a per-property change log of every GUI write during
# a start-up, 180 MB, one line per write:
#
#   Time:[HH:MM:SS]<-O:[full instance path]<-C:[property]<-V:[new value]
#
# This is a finer grain than the recorder's poll snapshots: the recorder samples,
# this catches every individual write in order. It is the first artifact that can
# answer "which face was on the glass at t" without inference.
#
# ASCII only out of this script -- the console here is GBK (memory: windows-console-codec).
# Reports to a file so nothing large enters a context window.
import re, sys, collections, os, io

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_report.txt'

LINE = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')

FACES = ('BootFrame', 'PreStartupFrame', 'MainMonitorFrame', 'ShutdownFrame', 'ErrorFrame',
         'Logo', 'BootIcon', 'CompanyLogo', 'SmallLogo', 'EFEFrame', 'BootUI',
         'DiagnosticFrame', 'ProtocolFrame', 'DetonationFrame', 'ConnectionFrame',
         'TransferIcon', 'GlitchEffect', 'TitleFrame')


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def main():
    lines = matched = 0
    first = last = None
    roots = collections.Counter()
    props = collections.Counter()
    paths = collections.Counter()
    times = collections.Counter()
    faces = []                 # (t, path, property, value) for FACE names
    texts = []                 # (t, path, text)
    enables = []               # (t, path, value) for Enabled on a MonitorUI/SurfaceGui
    unparsed = []
    last_text = {}

    with open(SRC, 'rb') as fh:
        for raw in io.TextIOWrapper(fh, encoding='utf-8', errors='replace'):
            lines += 1
            line = raw.rstrip('\n').rstrip('\r')
            m = LINE.match(line)
            if not m:
                if len(unparsed) < 8:
                    unparsed.append(line[:160])
                continue
            matched += 1
            t, path, prop, val = m.groups()
            if first is None:
                first = t
            last = t
            times[secs(t)] += 1
            seg = path.split('.')
            roots['.'.join(seg[:3])] += 1
            props[prop] += 1
            paths[path] += 1
            tail = seg[-1]
            if tail in FACES and prop == 'Visible':
                faces.append((secs(t), path, prop, val))
            if prop == 'Text':
                if last_text.get(path) != val:
                    last_text[path] = val
                    texts.append((secs(t), path, val))
            if prop == 'Enabled' and ('MonitorUI' in path or path.endswith('.Screen')):
                enables.append((secs(t), path, val))

    w = open(OUT, 'w', encoding='ascii', errors='replace')
    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    p('=== FILE ===')
    p('size bytes   ', os.path.getsize(SRC))
    p('lines        ', lines)
    p('parsed       ', matched, ' (unparsed %d)' % (lines - matched))
    p('first time   ', first, '= s', secs(first) if first else None)
    p('last time    ', last, '= s', secs(last) if last else None)
    p('span seconds ', (secs(last) - secs(first)) if first else None)
    p('distinct secs', len(times))
    if unparsed:
        p('-- unparsed samples --')
        for u in unparsed:
            p('   ', repr(u))

    p('')
    p('=== ROOTS (first three path tokens) ===')
    for k, v in roots.most_common(40):
        p('  %8d  %s' % (v, k))

    p('')
    p('=== PROPERTIES ===')
    for k, v in props.most_common(40):
        p('  %8d  %s' % (v, k))

    p('')
    p('=== INSTANCE PATHS TOUCHED (top 40) ===')
    for k, v in paths.most_common(40):
        p('  %8d  %s' % (v, k))
    p('  distinct paths = %d' % len(paths))

    p('')
    p('=== FACE VISIBILITY WRITES (chronological) ===')
    p('  count = %d' % len(faces))
    for t, path, prop, val in faces:
        p('  %5d  %-6s  %s' % (t - secs(first), val, path))

    p('')
    p('=== MonitorUI / Screen Enabled WRITES ===')
    for t, path, val in enables:
        p('  %5d  %-6s  %s' % (t - secs(first), val, path))

    p('')
    p('=== TEXT WRITES (deduped: only when the value changed) ===')
    p('  count = %d' % len(texts))
    for t, path, val in texts:
        p('  %5d  %s' % (t - secs(first), path))
        p('           %s' % val)

    w.close()
    print('REPORT', OUT, 'lines', lines, 'parsed', matched,
          'faces', len(faces), 'texts', len(texts), 'enables', len(enables))


if __name__ == '__main__':
    main()
