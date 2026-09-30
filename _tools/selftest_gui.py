#!/usr/bin/env python3
"""Break the player-GUI reader on purpose, one thing at a time, and check that the
SPECIFIC check which should notice is the one that turns red.

WHY THIS IS NOT PARANOIA.  The harness went green on the second run it was ever
executed, and the version before that failed only because it asked the reader for
keys the reader never produced -- i.e. it was measuring the harness, not the
reader.  A suite that has never been broken is indistinguishable from a suite
that cannot break: every check in it could be `check('x', true)` and the output
would be byte-identical.  So each entry below makes a known-bad recorder and
confirms the right check objects.

The reader is the one subsystem in this file that CANNOT be tested in the game.
PlayerGui does not exist on the server and nothing about it replicates, so it can
only run inside an injected script -- which gets one shot per shift, in the
original game, which the operator can only start once.  A green harness is the
only evidence available before that shot is spent, which is exactly why the
harness has to be shown to be capable of failing.

Each mutation names a check that must STAY green as well.  Without that, a
mutation that simply destroys the reader would satisfy "the target check went
red" while proving nothing about what the target check measures.

INDENTATION.  The recorder is tab-indented, so the anchors below contain REAL
tabs -- unlike build_gui_test.py, whose HEAD spells them as backslash-t.  Every
anchor is asserted to occur exactly once before it is used: an anchor that has
drifted must fail the test loudly, never silently edit nothing.  That rule is not
decoration here -- a non-unique anchor once wrote a whole function into the wrong
block in this project and the module stopped exporting it with no symptom at all.

  python _tools/selftest_gui.py

Prints one line per mutation and exits 1 if any of them was not detected.
"""
import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(ROOT, "_tools", "TRG_original_recorder.luau")
MUTANT = os.path.join(ROOT, "_tools", "_recorder_mutant.luau")
BUILDER = os.path.join("_tools", "build_gui_test.py")
# Forward slashes, spelled out rather than joined: these two are pasted into a
# Lua single-quoted string, and os.path.join would hand it backslashes -- which
# Lua then eats as escapes, so loadfile fails and the child reports an empty
# result that looks exactly like a suite with nothing to say.
BASE_LUA = "_tools/_gui_states.luau"
MUT_LUA = "_tools/_gui_mutant_states.luau"
LUA = "D:/Lua/5.1/lua.exe"


class AnchorError(Exception):
    pass


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def slice_once(src, spec, what):
    """The text a mutation replaces: either an exact unique substring, or the
    span from a unique start marker through the first unique end marker after it.

    The two-marker form exists because some of these blocks are twenty lines of
    comments and typing them out invites a typo that would look like a drifted
    anchor.  Both markers are still asserted unique -- that is the part that
    matters, since the span itself is only as trustworthy as its edges.
    """
    if isinstance(spec, tuple):
        start, end = spec
        if src.count(start) != 1:
            raise AnchorError("%s: start marker occurs %d times"
                              % (what, src.count(start)))
        i = src.index(start)
        j = src.index(end, i)
        if j < 0:
            raise AnchorError("%s: end marker is not after the start" % what)
        return src[i:j + len(end)]
    if src.count(spec) != 1:
        raise AnchorError("%s: anchor occurs %d times" % (what, src.count(spec)))
    return spec


# name, anchor spec, replacement, must go red, must stay green
MUTATIONS = [
    (
        "the key is the label name alone",
        ("local function keyForLabel(label, seen)",
         "\treturn label:GetFullName()"),
        "local function keyForLabel(label, seen)\n\treturn label.Name",
        ["G5 two same-named labels get two keys"],
        ["G1 the screen reads its Enabled"],
    ),
    (
        "the panel's own children are excluded, its grandchildren are not",
        ("function isOwnGui(inst)",
         "\treturn inst == g or inst:IsDescendantOf(g)"),
        "function isOwnGui(inst)\n"
        "\tlocal g = buoy.gui\n"
        "\tif g == nil then return false end\n"
        "\treturn inst == g or (inst.Parent ~= nil and inst.Parent == g)",
        ["G3 the panel text label is not a record"],
        ["G3 the panel is not a record"],
    ),
    (
        "the structural events are connected but do nothing",
        ("\t\tpg.DescendantAdded:Connect", "\t\tend)"),
        "\t\tlocal _ = pg\n\tend)",
        ["G7 adding a screen sets the dirty flag"],
        ["G1 the frame reads its Visible"],
    ),
    (
        "g.objects is computed and never offered",
        "put('g.objects', guiCount)",
        "local _objects = guiCount",
        ["G8 every poll offers g.objects"],
        ["G8 every poll offers g.over"],
    ),
    (
        "the flag is resolved up the ancestry every poll",
        ("\tfor i = 1, #guiRecords do",
         "\t\tput(rec.key, rec.read(rec.inst))"),
        "\tfor i = 1, #guiRecords do\n"
        "\t\tlocal rec = guiRecords[i]\n"
        "\t\tlocal v = rec.read(rec.inst)\n"
        "\t\tlocal p = rec.inst.Parent\n"
        "\t\twhile p ~= nil do\n"
        "\t\t\tif p:IsA('LayerCollector') then\n"
        "\t\t\t\tv = v and p.Enabled\n"
        "\t\t\telseif p:IsA('GuiObject') then\n"
        "\t\t\t\tv = v and p.Visible\n"
        "\t\t\tend\n"
        "\t\t\tp = p.Parent\n"
        "\t\tend\n"
        "\t\tput(rec.key, v)",
        ["G10 a Visible child under a hidden frame still reads true"],
        ["G10 the frame it is hiding under reads false"],
    ),
    (
        "the object cap is never reached",
        ("\t\t\telseif n >= Config.MaxGuiObjects then",
         "\t\t\t\tover = over + 1"),
        "\t\t\telseif false then\n\t\t\t\tover = over + 1",
        ["G6 the count reflects the cap"],
        ["G1 the frame reads its Visible"],
    ),
    (
        "the GUI manifest line is built and never emitted",
        ("\temitEvt('GUI', 'objects='", "guiLabelOver))"),
        "\tlocal _guiEvt = 'objects=' .. tostring(n) ..\n"
        "\t\t' over=' .. tostring(over) ..\n"
        "\t\t' unreadable=' .. tostring(unreadable) ..\n"
        "\t\t' labels=' .. tostring(guiLabels) ..\n"
        "\t\t' label_over=' .. tostring(guiLabelOver)",
        ["G2 the GUI event names the unreadable count"],
        ["G2 a class that answers neither flag is not a record"],
    ),
    (
        "a rebuild does not invalidate the readout sweep",
        "\treadoutDirty = true\n\tguiDirty = false",
        "\tguiDirty = false",
        ["G7 the rebuild also invalidates the readout sweep"],
        ["G7 the late screen is a record after one poll"],
    ),
    (
        "g.labels is computed and never offered",
        "put('g.labels', guiLabels)",
        "local _labels = guiLabels",
        ["G8 every poll offers g.labels"],
        ["G8 every poll offers g.objects"],
    ),
    (
        "an unreadable object is dropped without being counted",
        "\t\t\t\tunreadable = unreadable + 1",
        "\t\t\t\tunreadable = unreadable + 0",
        ["G2 the GUI event names the unreadable count"],
        ["G2 a class that answers neither flag is not a record"],
    ),
]


def run_builder(src_path, out_path):
    proc = subprocess.run([sys.executable, BUILDER, src_path, out_path],
                          cwd=ROOT, capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def run_harness(lua_path):
    """Returns (ok_names, fail_names, rc, note).

    The report is read from BOTH streams, because the harness puts it on stderr
    when it goes red and on stdout when it goes green: it writes the report to
    stderr and exits before returning, so a failing run leaves stdout empty.  A
    parser that only read stdout would therefore see every mutant as "did not run
    at all" -- the one error that looks like a broken test rather than a broken
    reader.  Bytes then decode: this console is GBK and a text=True read dies on
    any non-ASCII the child happens to emit.
    """
    proc = subprocess.run([LUA, "-e",
                           "print(assert(loadfile('%s'))())" % lua_path],
                          cwd=ROOT, capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    oks, fails = set(), set()
    for line in (out + "\n" + err).splitlines():
        if line.startswith("PASS "):
            oks.add(line[5:].strip())
        elif line.startswith("FAIL "):
            fails.add(line[5:].strip())
    if not oks and not fails:
        tail = err.strip().splitlines() or out.strip().splitlines()
        return oks, fails, proc.returncode, \
            "\n".join(tail[-3:]) if tail else "(no output at all)"
    return oks, fails, proc.returncode, out


def build_and_run(src_path, out_path):
    rc, output = run_builder(src_path, out_path)
    lines = output.strip().splitlines()
    if rc != 0:
        return None, None, "the builder refused: " + (lines[-1] if lines else "?")
    if "backslash bytes 0" not in output:
        return None, None, "the builder produced backslashes: " + output.strip()
    oks, fails, hrc, raw = run_harness(out_path)
    if hrc != 0 and not oks and not fails:
        return None, None, "the harness did not load: " + raw
    return oks, fails, None


def main():
    before = digest(SHIPPED)

    print("baseline: ", end="")
    rc, output = run_builder(SHIPPED, BASE_LUA)
    if rc != 0:
        print("the builder failed on the SHIPPED recorder:\n" + output)
        return 1
    oks, fails, hrc, raw = run_harness(BASE_LUA)
    if not oks and not fails:
        print("the baseline harness did not load:\n" + raw)
        return 1
    if fails or hrc != 0 or not oks:
        print("RED -- %d ok, %d fail. Fix the reader before mutating it."
              % (len(oks), len(fails)))
        for name in sorted(fails):
            print("   failing: " + name)
        return 1
    print("GREEN (%d checks)" % len(oks))
    baseline_ok = len(oks)

    source = open(SHIPPED, "r", encoding="utf-8", newline="").read()

    bad = 0
    for name, spec, replacement, must_fail, must_pass in MUTATIONS:
        try:
            anchor = slice_once(source, spec, name)
        except AnchorError as exc:
            print("  %-58s ANCHOR DRIFTED -- %s" % (name, exc))
            bad += 1
            continue

        with open(MUTANT, "w", encoding="utf-8", newline="") as fh:
            fh.write(source.replace(anchor, replacement, 1))

        moks, mfails, note = build_and_run(MUTANT, MUT_LUA)
        if moks is None:
            print("  %-58s the mutant did not build -- %s" % (name, note))
            bad += 1
            continue

        missing = [c for c in must_fail if c not in mfails]
        broke = [c for c in must_pass if c not in moks]

        if not moks and not mfails:
            print("  %-58s the mutant did not run at all" % name)
            bad += 1
        elif missing:
            print("  %-58s NOT DETECTED (no red on: %s)" % (name, "; ".join(missing)))
            bad += 1
        elif broke:
            print("  %-58s OVER-BROAD (also killed: %s)" % (name, "; ".join(broke)))
            bad += 1
        else:
            print("  %-58s red as expected: %s" % (name, must_fail[0]))

    for path in (MUTANT, MUT_LUA):
        if os.path.exists(path):
            os.remove(path)
    shutil.rmtree(os.path.join(ROOT, "_tools", "_mut_base"), ignore_errors=True)

    after = digest(SHIPPED)
    if before != after:
        print("the SHIPPED recorder changed during the run -- that must never happen")
        return 1

    print()
    total = len(MUTATIONS)
    print("gui mutations: %d of %d detected, %d baseline checks, shipped file untouched (md5 %s)"
          % (total - bad, total, baseline_ok, after))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
