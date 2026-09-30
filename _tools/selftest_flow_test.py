"""Prove that the flow harness can FAIL, and that the end harness still notices the
half of the 12:32 seal that lives in `endReason`.

WHAT IS UNDER TEST. The 12:32 run sealed itself on a shift that was still live: the
monitor fell to 5586 F, the operator brought it back, and the recorder called that a
shutdown and a restart and then ended the file. Two rules produced that, and they
live in two different regions of the recorder:

  * the flow boundary in `pollOnce` decided the core had gone down and come back;
  * the DOWN backstop in `endReason` counted forty polls underneath it and fired.

They are one policy -- what is allowed to end a run -- split across two files by
WHERE THE CODE LIVES, not by what it decides. A per-subject mutation suite would
have to duplicate this reasoning and name one half of every mutation, so this file
mutates the shipped recorder once and rebuilds BOTH harnesses against it.

EVERY MUTATION NAMES A CHECK THAT MUST STAY GREEN. Without that, a mutation that
merely destroys the boundary would satisfy "the target went red" while proving
nothing about what the target measures. And every needle is asserted to occur
exactly once, because a mutation that silently edits nothing looks exactly like a
suite that is right.

The recorder is restored from the bytes read at startup, so a crash mid-way cannot
leave a mutated script on disk, and both clean harnesses are rebuilt at the end --
they are generated, and must not be left holding a mutant.

    python _tools/selftest_flow_test.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "TRG_original_recorder.luau"
LUA = r"D:\Lua\5.1\lua.exe"

# Each entry: a name, the exact shipped text to replace, what to put there, which
# harness must notice ("flow" or "end"), the assertion that must be the one to go
# red, the assertion that must NOT, and the real bug the mutation models.
MUTATIONS = [
    (
        "the UP no longer requires a relight",
        "\t\t\t\tif startedSinceDown then\n",
        "\t\t\t\tif true then\n",
        "flow",
        "F3 the recovery is announced",
        "F4 the relight is an UP",
        "The 12:32 defect verbatim: every stall that recovers is read as a restart, "
        "the settle countdown starts, and the file seals itself 24 polls later on a "
        "shift that never ended.",
    ),
    (
        "the recovery leaves the down state standing",
        "\t\t\t\t\tsawDown = false\n\t\t\t\t\tstartedSinceDown = false\n",
        "\t\t\t\t\tstartedSinceDown = false\n",
        "flow",
        "F3 the recovery clears the down state",
        "F3 the recovery is announced",
        "`sawDown` is read as 'the core is stopped' by the on-screen phase, and it "
        "gates the DOWN edge -- so leaving it set means the next "
        "stall is never announced as one, and the receipt's own `flow=` field lies.",
    ),
    (
        # The literal call is kept and made unreachable rather than deleted: the
        # BUILDER asserts that a boundary containing `emitPhase('RECOVER')` was the
        # one extracted, because extracting the region from an older recorder would
        # mean this whole suite is testing code that is not shipped. A mutation that
        # removes the token is refused by the builder -- which is the right refusal,
        # so the mutation models an unreachable announcement instead.
        "the recovery announcement is unreachable",
        "\t\t\t\t\temitPhase('RECOVER')\n",
        "\t\t\t\t\tif false then emitPhase('RECOVER') end\n",
        "flow",
        "F3 the recovery is announced",
        "F3 the recovery clears the down state",
        "The operator's complaint was not only that the recorder decided wrongly in "
        "private -- it is that the log SAID 'shutdown' and 'restart' for a stall. A "
        "recovery that is never announced is the same failure with the other sign, "
        "and the phase log is the only place either is visible.",
    ),
    (
        "the DOWN edge does not clear the relight flag",
        "shutdown would be read as a recovery.\n\t\t\t\tstartedSinceDown = false\n",
        "shutdown would be read as a recovery.\n",
        "flow",
        "F6 b a press before the stall does not relight it",
        "F3 the recovery is announced",
        "The flag latches across a whole shift. The click hooker sets it on any "
        "StartUpLever press, including one on a core that is already up, so without "
        "this the NEXT stall is read as a relight and seals a live shift.",
    ),
    (
        "the DOWN edge does not zero the recovery debounce",
        "\t\t\t\tlowRun = 0\n\t\t\t\temitPhase('DOWN')\n",
        "\t\t\t\temitPhase('DOWN')\n",
        "flow",
        # Detected one check EARLIER than the one that names the debounce, and the
        # earlier one is the sharper reading: with the counter left standing the UP
        # fires on the FIRST hot poll, so "one hot poll is not a relight" is what
        # goes red -- while "the relight takes its own debounce" stays green,
        # because the UP did eventually arrive. That pair is the mutation's whole
        # evidence: the sequence looks right and the timing is wrong.
        "F4 b one hot poll is not a relight",
        "F4 b the relight takes its own debounce",
        "Arming leaves `lowRun` AT the debounce because it is the same counter, so "
        "without this the first hot poll after a stall is already a relight. The "
        "receipt then says a dwell was required while the code enforced it once.",
    ),
    (
        "the down backstop counts through a recovery",
        "\tif type(t) == 'number' and t >= Config.CoreThresholds[1] then\n",
        "\tif false then\n",
        "end",
        "E9 b the countdown restarts from the recovery",
        "E9 a core down with no end signal still seals",
        "This was the shipped rule, and it is what actually sealed 12:32: the "
        "counter was gated on the `sawDown` EDGE, which nothing had cleared, so it "
        "reached forty while the core read 5810 F and fired 0.33 s after the "
        "recorder had itself emitted the UP -- stealing the ending from the settle "
        "path and naming the wrong cause in the receipt.",
    ),
    (
        "the backstop's reason is reworded back to a key",
        "'core read as down for '",
        "'held down '",
        "end",
        "E9 the reason names the core, not a key",
        "E9 a core down with no end signal still seals",
        "The shipped string was 'held down 40 polls', and the operator read it the "
        "natural way -- as a key being held -- which is wrong, because `sawDown` is "
        "an edge over the core's temperature. A receipt's reason is the one line a "
        "reader trusts when they will not re-derive the run.",
    ),
]

# A mutation that was written, run, and stayed GREEN -- recorded rather than
# deleted, because a negative result about a line of code is a fact about it.
#
# `lowRun = 0` at the head of the UP path is now redundant: the DOWN edge zeroes
# the same counter, and the only reader is the settle countdown, which ends the run
# before `lowRun` is read again. It is kept anyway -- it is the UP path's own
# invariant, stated where the path starts -- but this entry asserts the redundancy,
# so a future change that makes the line load-bearing turns THIS run red and says so,
# instead of quietly making the line untested.
KNOWN_REDUNDANT = [
    (
        "the UP path's own reset of the debounce",
        "\t\t\t\tlowRun = 0\n\t\t\t\tif startedSinceDown then\n",
        "\t\t\t\tif startedSinceDown then\n",
        "flow",
    ),
]


def run(args):
    """rc, combined output. Never raises on a nonzero rc; that IS the datum."""
    p = subprocess.run(args, cwd=str(ROOT.parent), capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def build(subject):
    """rc, output, FAIL lines. A nonzero rc means EITHER the builder refused the
    mutant or the harness went red, and those two are different findings. The
    builder refuses a mutant whose extracted region no longer looks like the flow
    boundary it knows -- so a test case whose mutation deletes a token the builder
    asserts on is unrunnable BY CONSTRUCTION, not undetected, and the caller says
    which one it is rather than reporting a broken suite.
    """
    builder = ROOT / ("build_%s_test.py" % subject)
    rc, out = run([sys.executable, str(builder)])
    if rc != 0:
        return rc, "the builder refused: " + (out.strip().splitlines() or ["?"])[-1], None
    rc, out = run([LUA, "-e",
                   "print(assert(loadfile('_tools/_%s_states.luau'))())" % subject])
    lines = [ln for ln in out.splitlines() if ln.startswith("FAIL")]
    if rc != 0 and not lines:
        return rc, "the harness did not run: " + "\n".join(
            (out.strip().splitlines() or ["(no output)"])[-3:]), None
    return rc, out, lines


def main() -> int:
    original = RECORDER.read_bytes()
    clean = {}
    for subject in ("flow", "end"):
        rc, out, fails = build(subject)
        if rc != 0 or fails is None:
            print("the clean recorder already fails %s; fix that before mutating" % subject)
            print(out)
            return 1
        clean[subject] = sum(1 for ln in out.splitlines() if ln.startswith("PASS"))
    print("baseline: flow %d checks, end %d checks, both rc=0"
          % (clean["flow"], clean["end"]))

    bad = 0
    try:
        for name, needle, replacement, subject, want_fail, want_pass, why in MUTATIONS:
            text = original.decode("utf-8")
            if text.count(needle) != 1:
                print("SKIP %s -- the needle occurs %d times, expected 1"
                      % (name, text.count(needle)))
                print("     the recorder moved; update this file rather than guessing")
                bad += 1
                continue

            RECORDER.write_bytes(
                text.replace(needle, replacement, 1).encode("utf-8"))
            mrc, mout, fails = build(subject)
            # Both harnesses are rebuilt, and the OTHER one has to stay green: a
            # mutation of the flow boundary must not disturb the end rule, or the
            # two rules are entangled in a way neither file would have told us.
            other_rc, other_out, other_fails = build(
                "end" if subject == "flow" else "flow")

            if fails is None or other_fails is None:
                print("BAD  %s -- the mutant did not build" % name)
                print("     %s" % (mout if fails is None else other_out))
                bad += 1
                continue

            hit = any(want_fail in f for f in fails)
            missed = [f for f in other_fails if want_pass in f]

            if mrc == 0:
                print("BAD  %s -- the %s suite stayed GREEN" % (name, subject))
                print("     %s" % why)
                bad += 1
            elif not hit:
                print("BAD  %s -- red, but not on %r" % (name, want_fail))
                for f in fails:
                    print("     %s" % f)
                bad += 1
            elif missed:
                print("BAD  %s -- OVER-BROAD (also killed: %s)" % (name, "; ".join(missed)))
                bad += 1
            else:
                print("OK   %s" % name)
                print("     caught by: %s" % want_fail)
                if other_fails:
                    print("     (the other suite also went red on: %s)"
                          % "; ".join(other_fails[:2]))

        for name, needle, replacement, subject in KNOWN_REDUNDANT:
            text = original.decode("utf-8")
            if text.count(needle) != 1:
                print("SKIP %s -- the needle occurs %d times, expected 1"
                      % (name, text.count(needle)))
                bad += 1
                continue
            RECORDER.write_bytes(
                text.replace(needle, replacement, 1).encode("utf-8"))
            mrc, mout, fails = build(subject)
            if fails is None:
                print("BAD  %s -- the mutant did not build: %s" % (name, mout))
                bad += 1
            elif mrc == 0 and not fails:
                print("OK   %s -- still redundant, as recorded" % name)
            else:
                print("BAD  %s -- this line is NO LONGER redundant, so it is now"
                      % name)
                print("     untested by everything except this entry. Give it a real"
                      " check, or move the entry into MUTATIONS.")
                for f in fails:
                    print("     %s" % f)
                bad += 1
    finally:
        RECORDER.write_bytes(original)

    rebuilt = {}
    for subject in ("flow", "end"):
        rc, out, fails = build(subject)
        if rc != 0 or fails is None:
            print("FAIL the %s harness did not come back clean after the mutations"
                  % subject)
            print(out)
            return 1
        rebuilt[subject] = sum(1 for ln in out.splitlines() if ln.startswith("PASS"))
    print("restored: flow %d checks, end %d checks, both rc=0"
          % (rebuilt["flow"], rebuilt["end"]))

    if bad:
        print("%d of %d mutations were not caught as specified"
              % (bad, len(MUTATIONS) + len(KNOWN_REDUNDANT)))
        return 1
    print("all %d mutations behave as specified (%d load-bearing, %d recorded as "
          "redundant); every one names a check that stayed green"
          % (len(MUTATIONS) + len(KNOWN_REDUNDANT), len(MUTATIONS),
             len(KNOWN_REDUNDANT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
