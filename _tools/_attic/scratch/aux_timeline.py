# Second pass over the auxiliary screen capture: strip the animation, keep the drama.
#
# The 1.16 M lines are ~95% two things: the seven GlitchFrame glitch animations
# (Position/Size every frame, 157k writes each) and the six power graphs. What a
# person actually SEES change during a start-up is a few thousand writes, and they
# are the ones worth reading in order.
#
# ASCII only out (memory: windows-console-codec).
import re, io, os

SRC = 'Data/auxcollection/startup/ScreenChanges.txt'
OUT = '_tools/_attic/scratch/aux_timeline.txt'

L = re.compile(r'^Time:\[([0-9:]+)\]<-O:\[([^\]]*)\]<-C:\[([^\]]*)\]<-V:\[(.*)\]$')

# Properties that are a picture of the machine rather than a spinning animation.
KEEP = {'Visible', 'Text', 'Enabled', 'BackgroundTransparency', 'CanvasPosition',
        'Rotation', 'Image', 'ImageColor3', 'ImageTransparency', 'BackgroundColor3',
        'TextColor3', 'TextTransparency', 'ZIndex', 'ScrollingEnabled', 'RichText'}


def secs(t):
    h, m, s = (int(x) for x in t.split(':'))
    return h * 3600 + m * 60 + s


def main():
    rows = []
    logs = []
    with io.TextIOWrapper(open(SRC, 'rb'), encoding='utf-8', errors='replace') as fh:
        for raw in fh:
            m = L.match(raw.rstrip('\n').rstrip('\r'))
            if not m:
                continue
            t, path, prop, val = m.groups()
            if prop not in KEEP:
                continue
            if val.startswith('{') and prop in ('BackgroundTransparency', 'Visible', 'Text'):
                pass
            rows.append((secs(t), path, prop, val))
            if 'LogControlRoomMonitor' in path and prop == 'Text':
                logs.append((secs(t), path, val))

    t0 = rows[0][0]
    w = open(OUT, 'w', encoding='ascii', errors='replace')

    def p(*a):
        w.write(' '.join(str(x) for x in a) + '\n')

    p('=== KEPT WRITES: %d (of 1162737) ===' % len(rows))
    p('=== every write, deduped against the previous value of the same (path,prop) ===')
    last = {}
    shown = 0
    for t, path, prop, val in rows:
        key = (path, prop)
        if last.get(key) == val:
            continue
        last[key] = val
        shown += 1
        short = path.replace('Workspace.Monitors.', '').replace('.Screen.MonitorUI', '')
        p('%5d  %-16s %-22s %s' % (t - t0, prop, val, short))
    p('')
    p('distinct-value writes = %d' % shown)

    p('')
    p('=== THE LOG PANEL: every Text write under LogControlRoomMonitor ===')
    prev = None
    for t, path, val in logs:
        if val == prev:
            continue
        prev = val
        p('%5d  %s' % (t - t0, path.replace('Workspace.Monitors.LogControlRoomMonitor.Screen.MonitorUI', '')))
        p('           %s' % val)

    w.close()
    print('WROTE', OUT, 'kept', len(rows), 'distinct', shown, 'log-text-writes', len(logs))


if __name__ == '__main__':
    main()
