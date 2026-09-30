"""Prove that the driver harness can FAIL, and can fail for the right reason.

A green suite is only evidence if the suite is capable of going red. The end
harness has had this proof since the day it was written; the driver harness had
it only by hand, and the change this file was added for is exactly the kind that
makes a hand-proof go stale.

WHY THIS ONE WAS NEEDED NOW. The driver's shutdown rule used to be "press, then
watch the temperature fall". It is now "press, and the shift is over", with the
game's own end-of-shift flag as the only confirmation. That flips two scenarios
rather than adjusting them:

  * S2 used to assert `inert` -- a plant that ignored the press was named by the
    driver. It now asserts `shut_down`, because a plant that ignores the press
    cannot be told from one that obeys it at the moment of the press.
  * S9 is new, and it is the whole replacement for the deleted proof window.

Both assertions are green. Neither is obviously load-bearing to a reader, because
the states on either side of them look alike -- `shut_down` and `waiting_down`
are both terminal-looking, and a confirmation written forty times looks like a
confirmation written once until somebody counts.

So each guard is disabled in the SHIPPED recorder, the harness is rebuilt from
it, and the run must go red ON THE ASSERTION THAT GUARDS THAT PROPERTY. Not "red
somewhere" -- a suite that fails for an unrelated reason on every mutation would
pass a check that only looked at the exit code.

The recorder is restored from the bytes read at startup, so a crash mid-way
cannot leave a mutated script on disk. The clean harness is rebuilt at the end
for the same reason: `_driver_states.luau` is generated and must not be left
holding a mutant.

    python _tools/selftest_driver_test.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "TRG_original_recorder.luau"
BUILDER = ROOT / "build_driver_test.py"
LUA = r"D:\Lua\5.1\lua.exe"
STATES = ROOT / "_driver_states.luau"

# Each entry: a name, the exact shipped text to replace, what to put there, and
# the assertion string that must be the one to go red. The `why` is the real bug
# the mutation models -- a mutation nobody would ever write proves nothing about
# the code, only about the harness's ability to notice any difference at all.
#
# The first two mutations target the PRESS path, which is no longer the live
# configuration: `D7` has the operator pressing the shutdown lever himself, so
# the shipped default is `DrivePressControls = false` and S1 opts into the press
# explicitly. That does not weaken either mutation -- the press path is still
# shipped code behind that flag, and S1 is still the scenario that would go red
# if the flag's true branch broke. It does mean the named scenario has to be the
# one that runs that configuration, or the mutation would be "caught" by a
# scenario that never pressed anything.
MUTATIONS = [
    (
        "the press no longer ends the run",
        "\t\tdrive.verdict = 'shut-accepted'\n"
        "\t\tif Config.ShutdownEndsShift then\n"
        "\t\t\tdrive.state = 'shut_down'\n"
        "\t\telse\n"
        "\t\t\tdrive.state = 'waiting_down'\n"
        "\t\tend\n",
        "\t\tdrive.verdict = 'shut-accepted'\n\t\tdrive.state = 'waiting_down'\n",
        "S1 hot core, driver holds the controls",
        "This is the old model, one line wide: the driver presses and then waits "
        "for the core to come down before it calls the shift over. It parks in "
        "waiting_down whenever the temperature does not fall -- which, per the "
        "18:35 noise floor, is most of the time -- and every press-path scenario "
        "asserts shut_down.",
    ),
    (
        "the shutdown is believed only once the core reads as down",
        "\t\tdrive.verdict = 'shut-accepted'\n\t\tif Config.ShutdownEndsShift then\n",
        "\t\tdrive.verdict = 'shut-accepted'\n\t\tif Config.ShutdownEndsShift and not isRunning then\n",
        "S1 hot core, driver holds the controls",
        "The plausible half-repair: stop watching the temperature FALL, but still "
        "refuse to call it a shutdown until the readout says the core is down. It "
        "reads as caution and is the same mistake -- on the operator's own account "
        "the lever has already done the work, so this waits for a report that "
        "arrives 414 seconds after the press if it arrives at all.",
    ),
    (
        "the signal already written down is reported again",
        "\t\tif said ~= nil and said ~= drive.shutSaid then\n",
        "\t\tif said ~= nil then\n",
        "S11 the machine room melts down",
        "This is the latch, and it has to latch on WHICH SIGNAL rather than on a "
        "boolean, because `watching` ends on the first signal and `shut_down` then "
        "searches the same world again. Without the comparison, the one flag that "
        "ended the wait is reported a second time one poll later as though the "
        "machine had said something new. S11 has exactly one end signal, so its "
        "count must be 0; S9 has two, so its count is 1. A boolean latch would "
        "pass S11 and fail S9, and a missing latch passes neither.",
    ),
    (
        "the operator's press is re-labelled as the driver's",
        "\t\t\tif drive.verdict == 'shut-accepted' then\n",
        "\t\t\tif true then\n",
        "S9 the operator presses and the game confirms",
        "This is the defect the shipped code actually had, and it is the reason a "
        "verdict assertion exists at all. The confirmation block ran for both "
        "verdicts and stamped `shut-confirmed` on the operator's own press one poll "
        "after the file had said `user-shut`. `shut-confirmed` means the executor's "
        "press landed, so the receipt claimed a press the executor never made -- on "
        "a run whose entire point is answering who pressed. Every state assertion "
        "stayed green; only the verdict could see it.",
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
    return run([LUA, "-e", "print(assert(loadfile('_tools/_driver_states.luau'))())"])


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
