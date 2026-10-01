# Fourth pass: WHICH MONITOR shows WHAT, during the boot window.
#
# The remake's RoomShell.faceFor maps Booting -> BootFrame, but BootFrame is a
# direct child of MonitorUI on only 3 of the 7 monitors (Main / Thermal / Power);
# collectFaces uses FindFirstChild, so on the other four the Booting phase has
# nothing to show and falls through to the splash fallback.  Before calling that
# a defect I have to ask whether the ORIGINAL is arranged the same way -- the
# capture answers it directly, because it is a per-instance write log.
#
# ASCII only out (memory: windows-console-codec).
import re, io, collections

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_bootfaces.txt'

L = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')
MON = re.compile(r'Workspace\.Monitors\.([A-Za-z]+)Monitor\.Screen\.MonitorUI\.([A-Za-z0-9]+)')
FACES = ('BootFrame', 'PreStartupFrame', 'MainMonitorFrame', 'ShutdownFrame',
         'ErrorFrame', 'Logo', 'BootIcon', 'CompanyLogo', 'SmallLogo',
         'DiagnosticFrame', 'GlitchEffect', 'BootUI', 'TransferIcon',
         'ConnectionFrame', 'ProtocolFrame', 'DetonationFrame', 'EFEFrame')
PROPS = ('Visible', 'Enabled')


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def main():
    # frame -> monitor -> [seconds on which it was written]
    hits = collections.defaultdict(lambda: collections.defaultdict(list))
    texts = collections.defaultdict(list)          # (frame,monitor) -> first Text/TitleText values
    t0 = None
    for raw in io.TextIOWrapper(open(SRC, 'rb'), encoding='utf-8', errors='replace'):
        m = L.match(raw.rstrip('\n').rstrip('\r'))
        if not m:
            continue
        t, path, prop, val = m.groups()
        s = secs(t)
        if t0 is None:
            t0 = s
        mm = MON.search(path)
        if not mm:
            continue
        mon, frame = mm.group(1), mm.group(2)
        if frame in FACES and prop in PROPS:
            hits[frame][mon].append(s - t0)
        elif frame in FACES and prop == 'Text':
            texts[(frame, mon)].append((s - t0, val))

    w = open(OUT, 'w', encoding='ascii', errors='replace')

    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    p('t0 (first record in FILE order) == %s' % t0)
    p('')
    p('=== which monitors were WRITTEN per face, and when ===')
    for frame in FACES:
        if frame not in hits:
            continue
        mons = hits[frame]
        p('%-18s on %d monitor(s)' % (frame, len(mons)))
        for mon in sorted(mons):
            ss = sorted(mons[mon])
            p('    %-10s n=%-6d %s' % (mon, len(ss), ss[:12]))

    p('')
    p('=== first non-numeric Text write per (face, monitor) ===')
    NUM = re.compile(r'^[0-9.,% /:-]*$')
    for (frame, mon), vals in sorted(texts.items()):
        vals.sort()
        keep = [(t, v) for t, v in vals if not NUM.match(v)][:3]
        if keep:
            p('  %-16s %-10s %s' % (frame, mon, keep))

    w.close()
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
