# -*- coding: utf-8 -*-
"""Break clickPoint one way per mutant and require the check that guards it to go red.

WHY THIS IS NOT PARANOIA.  The harness went green the first time it ran, and a
suite that has never been broken is indistinguishable from a suite that cannot
break: every check in it could be `check(name, want, want)` and the output would
be byte-identical.  Worse, THIS subject is the one that spent tags d1..d4 being
wrong with no symptom at all, so "it passes" is precisely the observation that
has already been misleading once.

Each mutation therefore names a check that must turn red AND a check that must
stay green.  The green half is load-bearing: a mutation that reddens everything
proves only that the file can fail somewhere, not that any particular check has
anything to do with any particular defect.

Every anchor is asserted to occur exactly once before it is used.  An anchor that
has drifted must fail this test loudly and never silently edit nothing -- that
rule is not decoration in this project: a non-unique anchor once wrote a whole
function into the wrong block and the module stopped exporting it, with no
symptom anywhere.

Mutants are written to _tools/ as _drive_clickpoint_mutant.luau, never over the
shipped file, and the shipped file's digest is checked before and after.
"""

import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
SHIPPED = os.path.join(ROOT, "TRG_original_drive.luau")
MUTANT = os.path.join(ROOT, "_drive_clickpoint_mutant.luau")
BUILDER = os.path.join("_tools", "build_drive_clickpoint_test.py")

BASE_LUA = ROOT.replace(os.sep, "/") + "/_drive_clickpoint_states.luau"
MUT_LUA = ROOT.replace(os.sep, "/") + "/_drive_clickpoint_mut_states.luau"
LUA = "D:/Lua/5.1/lua.exe"

# Which case guards which line of the subject.  Kept here as constants so that a
# mutation cannot name a check that does not exist and pass by not looking.
C_ADD = "C1 a ScreenGui that does not ignore the inset has the inset ADDED"
C_IGNORE = "C2 a ScreenGui with IgnoreGuiInset gets the SAME inset -- the flag labels, it does not branch"
C_FLAGFALSE = "C12 the flag at false is not the flag at true -- no suffix, same point"
C_SURF = "C3 a SurfaceGui is a LAYOUT, not a screen space, and the name says so"
C_NONE = "C4 no LayerCollector ancestor is NAMED, not silently assumed to need nothing"
C_READ = "C8 the inset is READ, not the constant this client happens to have"
C_FLOOR = "C10 a fractional rect is FLOORED, not rounded"
C_POINT = "C11 the inset is a POINT, not a y-offset"


class AnchorError(Exception):
    pass


def digest(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def slice_once(src, spec, what):
    """Replace `spec` (an exact unique substring, or a (start, end) pair of
    unique markers) and hand back the new source.  Nothing is guessed."""
    if isinstance(spec, tuple):
        start, end = spec
        if src.count(start) != 1:
            raise AnchorError("%s: start marker occurs %d times"
                              % (what, src.count(start)))
        if src.count(end) != 1:
            raise AnchorError("%s: end marker occurs %d times"
                              % (what, src.count(end)))
        i = src.index(start)
        j = src.index(end) + len(end)
        return src, i, j
    if src.count(spec) != 1:
        raise AnchorError("%s: anchor occurs %d times" % (what, src.count(spec)))
    return src, spec


MUTATIONS = [
    # (name, anchor, replacement, must_go_red, must_stay_green)
    (
        "the conversion drops the inset",
        "  local p = ap + inset + as / 2",
        "  local p = ap + as / 2",
        [C_ADD],
        # C_SURF and C_NONE are the CONTROLS, and they are chosen for a reason:
        # both are cases whose inset is zero, so dropping the inset cannot move
        # them.  They are green here for the same reason they are green on the
        # shipped file -- not because the mutation failed to land anywhere.
        # C_IGNORE used to be here and had to move: under d6 the ignore-inset
        # case takes the SAME inset as every other ScreenGui, so it reddens
        # alongside C1, and a control that reddens is not a control.
        [C_SURF, C_NONE],
    ),
    (
        "the conversion subtracts the inset",
        "  local p = ap + inset + as / 2",
        "  local p = ap - inset + as / 2",
        [C_ADD],
        [C_SURF],
    ),
    (
        "the inset is hardwired to this client's 58",
        "        inset = Vector2.new(gi.X, gi.Y)",
        "        inset = Vector2.new(0, 58)",
        [C_READ],
        [C_ADD],
    ),
    (
        "the inset is hardwired and only in y",
        "        inset = Vector2.new(gi.X, gi.Y)",
        "        inset = Vector2.new(0, gi.Y)",
        [C_POINT],
        [C_ADD],
    ),
    (
        "IgnoreGuiInset stops being read",
        "        local okf, flag = pcall(function() return lc.IgnoreGuiInset end)",
        "        local okf, flag = true, false",
        [C_IGNORE],
        [C_ADD, C_FLAGFALSE],
    ),
    (
        "the flag at FALSE is lumped in with the flag at true",
        "        if okf and flag == true then space = space .. '/ignoreinset' end",
        "        if okf and flag ~= nil then space = space .. '/ignoreinset' end",
        [C_FLAGFALSE],
        [C_ADD, C_IGNORE],
    ),
    (
        "every LayerCollector is treated as a ScreenGui",
        "    if lc:IsA('ScreenGui') then",
        "    if true then",
        [C_SURF],
        [C_ADD],
    ),
    (
        "an unknown space is given a measured name",
        "  local space = 'nospace'",
        "  local space = 'inset+0,58'",
        [C_NONE],
        [C_ADD],
    ),
    (
        "the point is rounded instead of floored",
        "  return Vector2.new(math.floor(p.X), math.floor(p.Y)), inset, space",
        "  return Vector2.new(math.floor(p.X + 0.5), math.floor(p.Y + 0.5)), inset, space",
        [C_FLOOR],
        [C_ADD],
    ),
]


def run(cmd, cwd=REPO):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    # This console is GBK; the harness prints ASCII but never assume it.
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_builder(src, out):
    return run([sys.executable, "-I", BUILDER, src, out])


def run_harness(lua_path):
    return run([LUA, lua_path])


def build_and_run(src, lua_out, tag):
    rc, out = run_builder(src, lua_out)
    if rc != 0:
        return None, "the builder refused %s:\n%s" % (tag, out)
    if "backslash bytes 0" not in out:
        return None, "the builder did not report zero backslash bytes for %s:\n%s" % (tag, out)
    rc, out = run_harness(lua_out)
    if "PASS " not in out:
        return None, "the harness printed nothing for %s:\n%s" % (tag, out)
    return out, None


def main():
    before = digest(SHIPPED)
    src = open(SHIPPED, encoding="utf-8").read()

    print("=== baseline (shipped, unmutated) ===")
    out, err = build_and_run(SHIPPED, BASE_LUA, "the shipped file")
    if err:
        print(err)
        return 1
    reds = [l for l in out.splitlines() if l.startswith("FAIL ")]
    if reds:
        print("the shipped file does not pass its own harness -- refusing to "
              "mutate a red reader:")
        print(out)
        return 1
    print("%d check(s) green on the shipped bytes" % out.count("PASS "))

    print("=== mutations ===")
    ok = True
    for name, anchor, replacement, must_red, must_green in MUTATIONS:
        print("--- %s" % name)
        try:
            _, spec = slice_once(src, anchor, name)
        except AnchorError as e:
            print("    ANCHOR DRIFTED: %s" % e)
            ok = False
            continue
        if isinstance(spec, str):
            mutant = src.replace(spec, replacement, 1)
        else:
            i, j = spec
            mutant = src[:i] + replacement + src[j:]
        with open(MUTANT, "w", encoding="utf-8", newline="\n") as f:
            f.write(mutant)
        out, err = build_and_run(MUTANT, MUT_LUA, name)
        if err:
            print("    %s" % err)
            ok = False
            continue
        lines = out.splitlines()
        red_lines = [l for l in lines if l.startswith("FAIL ")]
        green_lines = [l for l in lines if l.startswith("PASS ")]
        missing = [c for c in must_red if not any(c in l for l in red_lines)]
        broke = [c for c in must_green if not any(c in l for l in green_lines)]
        if missing:
            print("    NOT DETECTED -- expected these to go red:")
            for c in missing:
                print("      %s" % c)
            ok = False
        if broke:
            print("    OVER-BROAD -- these were supposed to stay green:")
            for c in broke:
                print("      %s" % c)
            ok = False
        if not missing and not broke:
            print("    red as expected (%s), and %d check(s) still green"
                  % (", ".join(must_red), len(must_green)))

    for p in (MUTANT, MUT_LUA, BASE_LUA):
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists(MUTANT + ".bak"):
        os.remove(MUTANT + ".bak")

    after = digest(SHIPPED)
    if before != after:
        print("THE SHIPPED FILE CHANGED during this run: %s -> %s" % (before, after))
        return 1

    print("=== %s ===" % ("all mutations behaved" if ok else "PROBLEMS ABOVE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
