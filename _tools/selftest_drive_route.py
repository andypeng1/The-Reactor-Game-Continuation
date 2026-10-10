# -*- coding: utf-8 -*-
"""Break d7's click primitive and its seq floor, one way per mutant, and require
the check that guards each one to turn red -- while a named other check stays
green.

WHY THE GREEN HALF IS LOAD-BEARING.  A mutation that reddens everything proves
only that the harness can fail somewhere, not that any particular check has
anything to do with any particular defect.  The pairs below are chosen so the
surviving check is the one that would otherwise be a plausible place for the
same defect to hide: the argument-vs-read-back mutation leaves the no-read-back
case green, and the floor mutations leave the ordinary first-run case green.

WHY THIS IS NOT PARANOIA.  R1 and S1b are the two properties whose absence cost
real things: R1's absence is 58 px of silent miss (d1..d4), and S1b's absence is
a full replay of the command file that ran straight through a `stop` and on into
the session-ender.  Both were green-by-accident before they were green-by-test.

Anchors are asserted to occur exactly once before being used.  A drifted anchor
must fail loudly and never silently edit nothing -- in this project a non-unique
anchor once wrote a whole function into the wrong block with no symptom.

Mutant sources are written to _tools/ as _drive_route_mutant.luau, never over
the shipped file, and the shipped file's digest is checked before and after.
"""

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.join(ROOT, "TRG_original_drive.luau")
MUTANT = os.path.join(ROOT, "_drive_route_mutant.luau")
BUILDER = os.path.join(ROOT, "build_drive_route_test.py")

BASE_LUA = os.path.join(ROOT, "_drive_route_states.luau").replace(os.sep, "/")
MUT_LUA = os.path.join(ROOT, "_drive_route_mut_states.luau").replace(os.sep, "/")
LUA = "D:/Lua/5.1/lua.exe"

C_READBACK = "R1 the button is handed the ENGINE-REPORTED point, not the argument"
C_AFTER = "R2 the location is read AFTER the move, not in the same call"
C_NOREAD = "R4 an unreadable location fires NO button event"
C_FLOORRND = "R3 a fractional read-back is FLOORED, not rounded"
C_RAISELOC = "R5 a raising location is reported, and still fires no button event"
C_ERRMOVE = "R6 a refused move is named and stops the press"
C_ZERO = "R7 a legitimate 0,0 read-back is not mistaken for a failure"
C_FIRST = "S1a a fresh run with no state file executes the file and forgets nothing"
C_LAG = "S1b an EMPTY read after a write does NOT replay -- only 4 runs"
C_MEMWIN = "S2 the in-memory floor wins when it is higher than the file"
C_LOWER = "S3 a lower floor does not suppress real commands"
C_FLOORIS = "S4 writing a smaller seq does not lower the floor"
C_ATFLOOR = "S5 a command exactly at the floor does not run again"
C_NOWORK = "S7 a pass with nothing new still arms the floor"


class AnchorError(Exception):
    pass


def sub_once(src, old, new):
    n = src.count(old)
    if n != 1:
        raise AnchorError("anchor must occur exactly once, found %d:\n%r" % (n, old))
    return src.replace(old, new, 1)


# Each mutant: (name, why, [(old, new), ...], EXACTLY the checks that go red,
#               the checks that must stay green)
#
# The red set is EXACT, not a lower bound.  "At least R1 went red" is satisfied
# by a mutation that reddens everything, and a suite where every check is wired
# to every defect has no precision at all (取舍 306).  Listing the extras -- R3
# and R7 for M-ARG -- is the point: they are the other cases that read the same
# line, and a reader can see exactly how far the mutation reaches.
MUTANTS = [
    ("M-ARG", "clicks the guess instead of the engine's answer -- d1..d4's bug",
     [("local x, y = math.floor(cur.X), math.floor(cur.Y)",
       "local x, y = math.floor(gx), math.floor(gy)")],
     [C_READBACK, C_AFTER, C_FLOORRND, C_ZERO], [C_NOREAD, C_ERRMOVE]),

    ("M-CEIL", "rounds the read-back up instead of flooring it",
     [("local x, y = math.floor(cur.X), math.floor(cur.Y)",
       "local x, y = math.ceil(cur.X), math.ceil(cur.Y)")],
     [C_FLOORRND], [C_READBACK, C_ZERO]),

    ("M-NOFLOOR", "keeps the floor on disk only -- one empty read replays the file",
     [("  if (M._seq or 0) > last then last = M._seq end\n", "")],
     [C_LAG, C_MEMWIN, C_NOWORK], [C_FIRST, C_LOWER]),

    # M-NORAISE moved with the fix.  It used to remove the raise inside saveSeq
    # and could redden S1b; after d9 the dispatching pass raises the floor itself,
    # so a pass WITH work is covered twice over and S1b survives either line being
    # removed.  Left pointing at the old line the mutant would have gone green and
    # read exactly like a defect that is no longer there.
    #
    # It now shares its red set with M-NOWORK, and that is the finding rather than
    # a redundancy: "absent" and "conditional" differ only on a pass with nothing
    # new, so S7 is the single point at which either is observable.  C_LAG is
    # named must-stay-green to say so out loud -- the work-pass case does NOT
    # depend on this line.
    ("M-NORAISE", "never raises the floor from the dispatching pass",
     [("  if maxSeq > (M._seq or 0) then M._seq = maxSeq end\n", "")],
     [C_NOWORK], [C_FIRST, C_LAG, C_LOWER, C_FLOORIS]),

    # M-NOWORK is the hole the fix closes: it restores the conditional raise,
    # so a quiet pass leaves the floor unarmed and the next laggy read replays
    # from the top.  It does not disturb the case that gets its floor from a
    # pass WITH work (S1b), which is why that one is named as must-stay-green:
    # a mutant that reddens everything proves only that the suite can fail.
    ("M-NOWORK", "arms the floor only when the pass had work",
     [("  if maxSeq > (M._seq or 0) then M._seq = maxSeq end",
       "  if maxSeq ~= last and maxSeq > (M._seq or 0) then M._seq = maxSeq end")],
     [C_NOWORK], [C_FIRST, C_ATFLOOR]),

    ("M-LOWER", "lets a smaller seq lower the floor",
     [("  if n > (M._seq or 0) then M._seq = n end", "  M._seq = n")],
     [C_FLOORIS], [C_FIRST, C_ATFLOOR]),
]

# TRIED, AND NOT KEPT.  Both were mutated and both were removed, for the reason
# written down here rather than silently -- a check that has never been shown
# able to fail is decoration, and so is a mutant whose symptom cannot be told
# from a broken harness.
#
#   * the nil-check on the read-back ("cur == nil").  Removing it makes the
#     subject index nil, which RAISES, which aborts the harness: check count
#     14 -> 0.  A crash is not a silent defect -- it is the loudest thing there
#     is -- and this suite exists for the silent ones.  It is pinned instead by
#     R4, which passes only because the check returns a named refusal.
#   * dropping the wait between the move and the read.  On the stub, `task.wait`
#     is a counter, not a clock, so the mutant differs from the subject only in
#     that counter -- R2's `waits=2` does catch it, but R2 would then be
#     measuring the stub's bookkeeping rather than the shipped ordering.  R2 is
#     kept because it is cheap and it does pin the order; the mutant is not,
#     because passing it would prove nothing about a real client.
NOT_MUTANTS = ["nil-check on the read-back (removing it aborts -- see above)",
               "the wait between move and read (the stub has no clock)"]


def run_harness(lua_path):
    p = subprocess.run([LUA, lua_path], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def parse(out):
    red, green, total = set(), set(), 0
    for line in out.splitlines():
        if line.startswith("PASS "):
            total += 1
            green.add(line[5:].strip())
        elif line.startswith("FAIL "):
            total += 1
            red.add(line[5:].strip())
    return red, green, total


def main():
    old_md5 = hashlib.md5(open(SHIPPED, "rb").read()).hexdigest()
    src = open(SHIPPED, encoding="utf-8").read()

    print("baseline")
    rc, out = run_harness(BASE_LUA)
    red, green, total = parse(out)
    print("  rc=%d  checks=%d  red=%d" % (rc, total, len(red)))
    if rc != 0 or red:
        print(out)
        print("the unmutated harness is not green -- fix that first")
        return 1

    bad = 0
    for name, why, edits, must_red, must_green in MUTANTS:
        try:
            m = src
            for old, new in edits:
                m = sub_once(m, old, new)
        except AnchorError as e:
            print("FAIL %s  anchor drifted: %s" % (name, e))
            bad += 1
            continue

        open(MUTANT, "w", encoding="utf-8", newline="\n").write(m)
        b = subprocess.run([sys.executable, "-I", BUILDER, MUTANT, MUT_LUA],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if b.returncode != 0:
            print("FAIL %s  builder refused the mutant: %s" % (name, why))
            print(b.stdout.decode("utf-8", "replace"))
            bad += 1
            continue
        mrc, mout = run_harness(MUT_LUA)
        mred, mgreen, mtotal = parse(mout)

        problems = []
        # EXACT red set.  A mutant that reddens a check nobody predicted is
        # telling you something -- either the mutation reaches further than the
        # description says (fine, write it down) or your check is entangled with
        # another case (not fine).  Both are worth stopping for; only one of them
        # is fixed by widening the expectation.
        for c in sorted(set(must_red) - mred):
            problems.append("expected RED, still green: %s" % c)
        for c in sorted(mred - set(must_red)):
            problems.append("expected GREEN, went red (unpredicted): %s" % c)
        for c in must_green:
            if c not in mgreen:
                problems.append("expected GREEN, went red: %s" % c)
        if sorted(mred) != sorted(set(must_red)):
            problems.append("red set is %d, expected %d" % (len(mred), len(set(must_red))))
        # An abort is a red for the wrong reason: nothing ran, so nothing is
        # proven.  Every mutant must still have produced a full verdict.
        if mtotal != total:
            problems.append("check count changed %d -> %d (the harness aborted "
                            "rather than reporting)" % (total, mtotal))

        if problems:
            bad += 1
            print("FAIL %s  %s" % (name, why))
            for p in problems:
                print("     " + p)
        else:
            print("ok   %s  red=%d  (%s)" % (name, len(mred), why))

    new_md5 = hashlib.md5(open(SHIPPED, "rb").read()).hexdigest()
    if new_md5 != old_md5:
        print("FAIL the shipped driver changed during this run")
        bad += 1

    # Clean up after ourselves.  A run killed halfway would otherwise leave a
    # deliberately broken copy of a shipped file in the tree -- and `git add -A`
    # is automatic here, so "left behind" and "committed" are one step apart.
    # The generated files are also listed in .gitignore for the same reason.
    for p in (MUTANT, MUT_LUA):
        if os.path.exists(p):
            os.remove(p)
    print()
    print("MUTANTS %d ok, %d bad   (shipped md5 %s unchanged)" %
          (len(MUTANTS) - bad, bad, new_md5[:16]))
    # Printed on purpose.  A mutation that was tried and dropped is a result; a
    # suite that silently stops testing something because the case was awkward
    # reports green for a reason nobody can see.
    for nm in NOT_MUTANTS:
        print("not kept: %s" % nm)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
