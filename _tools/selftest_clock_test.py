"""Prove that the clock harness can FAIL, and can fail for the right reason.

A green suite is only evidence if the suite is capable of going red. The clock
harness is new, and its subject is a pair of lines that were wrong for as long as
the event has existed without anyone noticing -- which is exactly the situation
in which a harness gets written to agree with whatever the recorder happens to
do. So each of the three properties is broken in the SHIPPED recorder, the
harness is rebuilt from it, and the run must go red ON THE ASSERTION THAT GUARDS
THAT PROPERTY. Not "red somewhere": a suite that fails for an unrelated reason on
every mutation would pass a check that only looked at the exit code.

The three properties are independent, and two of them point in opposite
directions, which is the reason this file has three mutations rather than one:

  * M1 -- a mid-shift inject must not announce a shift start. This is the defect.
  * M2 -- a cold opening MUST still announce it. This is the way the fix for M1
    goes wrong: swallow everything and K1 passes while the event loses its whole
    purpose. A harness with only M1 would happily bless that.
  * M3 -- the reading must survive the claim being dropped. The fix refuses to
    interpret a wrap, and the cheapest way to do that is to stop writing the
    moment down at all, which passes K1 and destroys the datum.

The recorder is restored from the bytes read at startup, so a crash mid-way
cannot leave a mutated script on disk. The clean harness is rebuilt at the end
for the same reason: `_clock_states.luau` is generated and must not be left
holding a mutant.

    python _tools/selftest_clock_test.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "TRG_original_recorder.luau"
BUILDER = ROOT / "build_clock_test.py"
LUA = r"D:\Lua\5.1\lua.exe"
STATES = ROOT / "_clock_states.luau"

# Each entry: a name, the exact shipped text to replace, what to put there, and
# the assertion string that must be the one to go red. The `why` is the real bug
# the mutation models -- a mutation nobody would ever write proves nothing about
# the code, only about the harness's ability to notice any difference at all.
MUTATIONS = [
    (
        "the wrap door is gone",
        "\tif clockStartedUp then\n\t\tif up ~= clockUp then\n",
        "\tif false then\n\t\tif up ~= clockUp then\n",
        "K1 no shift start is announced after a mid-shift inject",
        "This is the shipped code as it stood before this pass, and the mutation is "
        "one word wide. With the door removed, a file injected with the core up "
        "falls through to the ordinary crossing branch, and 12:01 PM is announced "
        "as the start of a shift -- 60 s after it announced a shift ending. Both "
        "lines are false, the temperature across them never moves, and no "
        "downstream reader can tell them from the real thing.",
    ),
    (
        "the latch is armed at inject, so the door swallows the real crossing",
        "\t\tclockSeen, clockUp, clockStartedUp = true, up, up\n",
        "\t\tclockSeen, clockUp, clockStartedUp = true, up, true\n",
        "K2 the cold opening still announces the shift",
        "The plausible over-repair, and the reason K2 exists. `clockStartedUp` is "
        "supposed to record what the INJECT read, on a cold start that is 'not up "
        "yet', so the first crossing is real. Setting it true unconditionally makes "
        "every transition a dial move, which is a quiet way to delete the event: K1 "
        "stays green, the receipt fields are unchanged, and the only thing lost is "
        "the announcement the event was built to make. Nothing in the file would "
        "say so -- an absent CLOCK line looks exactly like a run with no crossing.",
    ),
    (
        "the wrap message stops carrying the reading",
        "\t\t\temitEvt('CLOCK', 'the clock moved to ' .. tostring(last['q.timeText']) ..\n",
        "\t\t\temitEvt('CLOCK', 'the clock moved' ..\n",
        "K4 the moment stays locatable in the file",
        "The cheapest way to stop over-interpreting a reading is to stop writing it "
        "down, and it passes every assertion about what is NOT said. `q.clock` and "
        "`q.up` are still written by readQuota, so the moment is not lost from the "
        "file entirely -- but the one line that puts a reader AT the crossing loses "
        "it, and a reader following the events rather than the sample grid has no "
        "way back to it. Refusing to interpret is not the same as discarding.",
    ),
]


def run(args):
    """rc, combined output. Never raises on a nonzero rc; that IS the datum."""
    p = subprocess.run(args, cwd=str(ROOT.parent), capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def build_and_run():
    rc, out = run([sys.executable, str(BUILDER)])
    if rc != 0:
        return rc, out
    return run([LUA, "-e", "print(assert(loadfile('_tools/_clock_states.luau'))())"])


def failed_lines(out):
    return [ln for ln in out.splitlines() if ln.startswith("FAIL")]


def main() -> int:
    original = RECORDER.read_bytes()

    rc, out = build_and_run()
    if rc != 0:
        print("the clean recorder already fails; fix that before mutating anything")
        print(out)
        return 1
    clean_passes = sum(1 for ln in out.splitlines() if ln.startswith("PASS"))
    print("baseline: rc=0, %d assertions PASS" % clean_passes)

    bad = 0
    try:
        for name, needle, replacement, want_fail, why in MUTATIONS:
            hits = original.decode("utf-8").count(needle)
            if hits != 1:
                print("SKIP %s -- the needle occurs %d times, expected 1" % (name, hits))
                print("     the recorder moved; update this file rather than guessing")
                bad += 1
                continue

            mutated = original.decode("utf-8").replace(needle, replacement, 1)
            RECORDER.write_bytes(mutated.encode("utf-8"))
            mrc, mout = build_and_run()

            fails = failed_lines(mout)
            hit = any(want_fail in f for f in fails)
            other = [f for f in fails if want_fail not in f]

            if mrc == 0:
                print("BAD  %s -- the suite stayed GREEN" % name)
                print("     %s" % why)
                bad += 1
            elif not hit:
                print("BAD  %s -- red, but not on %r" % (name, want_fail))
                for f in fails:
                    print("     %s" % f)
                bad += 1
            else:
                print("OK   %s" % name)
                print("     caught by: %s" % want_fail)
                if other:
                    print("     also red: %s" % "; ".join(other))
    finally:
        RECORDER.write_bytes(original)

    rc, out = build_and_run()
    if rc != 0:
        print("FAIL the recorder did not come back clean after the mutations")
        print(out)
        return 1
    print("restored: rc=0, %d assertions PASS" % sum(
        1 for ln in out.splitlines() if ln.startswith("PASS")))

    if bad:
        print("%d of %d mutations were not caught as specified" % (bad, len(MUTATIONS)))
        return 1
    print("all %d guards are load-bearing: removing any one turns the suite red"
          % len(MUTATIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
