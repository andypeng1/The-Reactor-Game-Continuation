#!/usr/bin/env python3
"""Mutation suite for boot_harness.luau.

A check that cannot go red is not a check.  Each mutation below breaks one
behaviour the shipped recorder is supposed to have, and the harness must report a
FAIL whose name matches -- so this proves the harness is measuring the shipped
file rather than agreeing with itself.

Every mutant is written under its own PID-unique directory.  run_tests.sh is not
concurrency-safe (PROGRESS.md Phase 68: two runs that share a fixed mutant path
delete each other's products and report NOT DETECTED), so nothing here may share a
name with anything else, ever.

Usage: selftest_boot.py [--keep]
Exit:  0 every mutation was detected, 1 one was not.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# A real Windows path, not the /d/... form the shell uses: this runs in Python,
# which hands the string straight to CreateProcess.
LUA = os.environ.get('LUA', 'D:/Lua/5.1/lua.exe')
SRC = os.path.join(HERE, 'TRG_original_boot.luau')
HARNESS = os.path.join(HERE, 'boot_harness.luau')

# (label, scenario, check that must go red, old, new)
MUTATIONS = [
    (
        'no coalescing: the signal handler writes at event time',
        'default',
        'sixty changes inside one tick become at most one line',
        """            if not dirtySet[key] then
                dirtySet[key] = true
                dirty[#dirty+1] = { obj = obj, full = full, prop = prop, key = key }
            end""",
        """            dirtySet[key] = true
            emit(string.format('Time:[%s]<-O:[%s]<-C:[%s]<-V:[%s]',
                wallClock(), full, prop, fmt(obj[prop])))""",
    ),
    (
        'the geometry filter is emptied, so the decoration floods again',
        'default',
        'the decoration produces no line at all for its geometry',
        "    GeometrySkip = { '.GlitchEffect' },",
        "    GeometrySkip = { '.NothingAtAll' },",
    ),
    (
        'the change-and-revert rule: the seed is dropped',
        'default',
        'a value that changed and reverted inside one tick is not recorded',
        "                lastValue[key] = okV and fmt(v) or '<read failed>'",
        "                lastValue[key] = nil",
    ),
    (
        'no DescendantAdded hook: a clone made during the run is invisible',
        'default',
        'a label created during the run is watched',
        "        connections[#connections+1] = Monitors.DescendantAdded:Connect(function(obj)",
        "        connections[#connections+1] = workspace.ChildAdded:Connect(function(obj)",
    ),
    (
        'the birth record is dropped, so a clone is registered but never read',
        'default',
        'a label born during the run is written with the text it was born with',
        "            if not SEALED then register(obj, true) end",
        "            if not SEALED then register(obj) end",
    ),
    (
        'the midnight wrap seals again, cutting the run in the ignition ramp',
        'default',
        'midnight does not end the run -- on this world it is the shift START',
        "            elseif text == '12:00 AM' then",
        "            elseif text == '12:00 AM' then\n                seal('wrap', 'the dial went back to 12:00 AM')",
    ),
    (
        'the mark is written as a data line instead of a comment',
        'default',
        "every data line matches the archived readers' pattern exactly",
        "                emit('# MARK midnight at ' .. wallClock() ..",
        "                emit('MARK midnight at ' .. wallClock() ..",
    ),
    (
        'the write budget is raised out of the way, so nothing is ever cut',
        'default',
        'a key that crossed its budget stops writing at exactly the budget',
        '    MaxWritesPerKey = 2000,',
        '    MaxWritesPerKey = 100000,',
    ),
    (
        'RightShift is bound, stealing the other recorder\'s seal key',
        'default',
        "the recorder's seal key is not bound here",
        "            elseif name == 'Enum.KeyCode.RightControl' then",
        "            elseif name == 'Enum.KeyCode.RightShift' then",
    ),
    (
        'the noon seal never fires',
        'default',
        'the 12:00 PM handoff seals the run',
        "            if text == '12:00 PM' then",
        "            if text == '11:00 PM' then",
    ),
    (
        'the header is written before the world is checked',
        'noroot',
        'the death costs no capture line',
        """    if not arm() then return end
    -- A header, so the artifact says what it is without needing meta.txt.  It is
    -- a comment line and no reader matches it.
    emit('# build=' .. CONFIG.Build .. ' start=' .. wallClock() ..
        ' root=' .. CONFIG.RootName .. ' tick=' .. tostring(CONFIG.SampleInterval) ..
        ' transport=' .. TRANSPORT)""",
        """    emit('# build=' .. CONFIG.Build .. ' start=' .. wallClock() ..
        ' root=' .. CONFIG.RootName .. ' tick=' .. tostring(CONFIG.SampleInterval) ..
        ' transport=' .. TRANSPORT)
    if not arm() then return end""",
    ),
]


def run(path, scenario):
    proc = subprocess.run(
        [LUA, HARNESS, path, scenario],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    # The console here is GBK and the harness prints ASCII, but a Lua compile error
    # quotes the source -- so take the bytes and decode explicitly.
    return proc.stdout.decode('utf-8', 'replace')


def main(argv):
    keep = '--keep' in argv
    with open(SRC, 'r', encoding='utf-8') as fh:
        source = fh.read()

    work = tempfile.mkdtemp(prefix='boot_mut_%d_' % os.getpid())
    print('mutant workspace: %s' % work)

    # Baseline first: the harness must be green on the shipped file in each
    # scenario used below, or a "detected" verdict would be meaningless.
    baseline = {}
    for scenario in sorted({m[1] for m in MUTATIONS}):
        out = run(SRC, scenario)
        fails = [l for l in out.splitlines() if l.startswith('FAIL')]
        baseline[scenario] = len(fails)
        print('baseline %-12s %s' % (scenario, out.strip().splitlines()[-1]))
        if fails:
            print('BASELINE NOT GREEN in %s:' % scenario)
            for l in fails:
                print('    ' + l)
            return 1

    detected = 0
    undetected = []
    for i, (label, scenario, expect, old, new) in enumerate(MUTATIONS, 1):
        if source.count(old) != 1:
            print('%2d. ANCHOR NOT UNIQUE (%d hits): %s' % (i, source.count(old), label))
            undetected.append(label)
            continue
        path = os.path.join(work, 'mutant_%02d.luau' % i)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(source.replace(old, new))
        out = run(path, scenario)
        lines = out.splitlines()
        compiled = not any('does not compile' in l for l in lines)
        hit = any(l.startswith('FAIL ' + expect + ' ') or l == 'FAIL ' + expect for l in lines)
        tail = lines[-1] if lines else '(no output)'
        print('%2d. %-4s %-58s %s' % (i, 'RED' if hit else 'GREEN', label, tail))
        if not compiled:
            print('       the mutant did not compile, so it tested nothing')
        if hit:
            detected += 1
        else:
            undetected.append(label)

    if not keep:
        shutil.rmtree(work, ignore_errors=True)

    print('%d of %d detected' % (detected, len(MUTATIONS)))
    if undetected:
        print('NOT DETECTED:')
        for label in undetected:
            print('    ' + label)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
