"""Prove that the CORE GATE harness can FAIL, and can fail for the right reason.

A green suite is only evidence if the suite is capable of going red. That matters
more here than anywhere else in _tools/, because the gate ships into a game the
operator can start ONCE per shift: if the harness has no opinion, the next
evidence is a wasted run.

Every mutation below is a real bug somebody would plausibly write, not a random
edit -- a mutation nobody would ever make proves nothing about the code, only
about the harness's ability to notice any difference at all. The one that matters
most is `the hold becomes a filter`: writing the pre-boot value into `last` and
declining to emit produces byte-identical output to holding it, right up until
the ignition poll carries a value EQUAL to the pre-boot one. Then the filtered
version sees "no change", the ignition is never reported, and the file looks
like a shift that simply started late.

The recorder is restored from the bytes read at startup, so a crash mid-way
cannot leave a mutated script on disk. The clean harness is rebuilt at the end
for the same reason: `_gate_states.luau` is generated and must not be left
holding a mutant.

And two mutations the suite is meant to FOLLOW -- stay green while the bytes it
read move. One of them is the gate defaulting to OPEN: the harness is blind to it
for a real reason (reset() clears the latch before any check), and writing that
down is how it stays a known blind spot rather than becoming a hole somebody
re-discovers. Green is the pass condition for that class, which is the opposite of
every entry above, and so is the claim -- not "the recorder is guarded" but "the
harness has no copy of its own to go stale".

    python _tools/selftest_gate_test.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "TRG_original_recorder.luau"
BUILDER = ROOT / "build_gate_test.py"
LUA = r"D:\Lua\5.1\lua.exe"
STATES = ROOT / "_gate_states.luau"

# Each entry: a name, the exact shipped text to replace, what to put there, the
# assertion string that must be the one to go red, and the real bug it models.
MUTATIONS = [
    (
        "the hold becomes a FILTER: the value is remembered but not emitted",
        "\t\t\t\tif coreLive or not isCoreStat(path) then\n",
        "\t\t\t\tif isCoreStat(path) and not coreLive then last['s.' .. path] = d.Value end\n"
        "\t\t\t\tif coreLive or not isCoreStat(path) then\n",
        "G5 the SAME value is written once the gate opens",
        "The one-line mistake this harness exists for, and the reason it is "
        "first. It emits exactly the same bytes as the shipped version until the "
        "ignition reading happens to equal the pre-boot one -- which is the "
        "common case, since a cold core's temperature IS 0 and the first live "
        "sample is a small number that can round to it.",
    ),
    (
        "the gate stops latching",
        "\tcoreLive = true\n",
        "",
        "G2 the gate stays open when the flag goes back to false",
        "A live predicate instead of a latch. The cold-trip arm reads `m.temp` "
        "AFTER the shutdown, so this silences the very readings the seal rule is "
        "made of -- the recorder would never detect the automatic shutdown the "
        "operator named as seal condition 2.",
    ),
    (
        "isCoreStat becomes a careless prefix test",
        "\treturn path == 'Core' or path:sub(1, 5) == 'Core.'\n",
        "\treturn path == 'Core' or path:sub(1, 4) == 'Core'\n",
        "G3 a longer name is NOT",
        "`CoreStuff` and any future `CoreShell` container would be swallowed, and "
        "their readings held back for the whole pre-boot -- silently, since the "
        "only symptom is a key that appears late.",
    ),
    (
        "readStats relies on readReactor having run first",
        "\tcoreGateOpen()\n",
        "",
        "G6 readStats opens the gate by itself",
        "The ordering dependency the two-caller design exists to remove. In the "
        "shipped loop readReactor does run first, so this mutation is invisible "
        "in a real run -- which is exactly why it has to be caught here.",
    ),
    (
        "a same-named non-ValueObject is assumed to be the flag",
        "\tif flag == nil or not flag:IsA('ValueBase') then return false end\n",
        "\tif flag == nil then return false end\n",
        "G1 a same-named NON-ValueObject is survived",
        "`MainData:FindFirstChild('GameActive').Value` on a Folder is an error, "
        "and it would be raised inside the poll -- taking the whole recording "
        "with it, on the first poll, with no receipt.",
    ),
    (
        "the gate stops re-fetching Stats",
        "\tif MainData == nil then MainData = Workspace:FindFirstChild('Stats') end\n"
        "\tlocal flag = MainData and MainData:FindFirstChild('GameActive')\n",
        "\tlocal flag = MainData and MainData:FindFirstChild('GameActive')\n",
        "G10 the gate opens once the folder appears",
        "The REAL defect this harness found. `MainData` is captured once at "
        "load, so a recorder injected before `Workspace.Stats` exists holds a "
        "nil and keeps the gate shut until some other reader refreshes it -- the "
        "gate's behaviour depending on whether the stats scan ran first.",
    ),
]

# The class that must stay GREEN. Not "the recorder is guarded" but "the harness
# reads the shipped file and has no copy of its own to go stale" -- a builder
# that extracted a region into a stored string would pass every check above and
# still test a version of the recorder that no longer ships.
FOLLOW_MUTATIONS = [
    (
        "the gate defaults to OPEN",
        "local coreLive = false\n",
        "local coreLive = true\n",
        "local coreLive = true\n",
        "The state the recorder was in before 2026-09-30, and the state the operator "
        "asked to have changed -- and this harness is BLIND to it, on purpose. "
        "`reset()` clears the latch at the top of every scenario, so the initial "
        "value is overwritten before any check runs, and no G-check can see it. "
        "Recorded here rather than deleted so that nobody adds it back as a "
        "mutation and reads the green as a hole in the checks: the thing that "
        "covers it is the shipped default and the diff, not a scenario. What this "
        "entry DOES prove is that the mutant reached the harness -- the states file "
        "carries the new declaration -- so the blindness is the harness's, not the "
        "runner's failure to apply the edit.",
    ),
    (
        "the gate's own comments move",
        "-- Read from the game's own flag and not from a temperature, because the\n",
        "-- MUTATED-SENTINEL: read from the game's own flag, not a temperature,\n",
        "MUTATED-SENTINEL",
        "The generated harness must carry the shipped bytes. If this stayed green "
        "without the sentinel appearing, the builder was testing a stored copy.",
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
    return run([LUA, "-e", "print(assert(loadfile('_tools/_gate_states.luau'))())"])


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

        for name, needle, replacement, must_contain, why in FOLLOW_MUTATIONS:
            hits = original.decode("utf-8").count(needle)
            if hits != 1:
                print("SKIP %s -- the needle occurs %d times, expected 1" % (name, hits))
                bad += 1
                continue

            mutated = original.decode("utf-8").replace(needle, replacement, 1)
            RECORDER.write_bytes(mutated.encode("utf-8"))
            mrc, mout = build_and_run()
            states = STATES.read_text(encoding="utf-8")

            if mrc != 0:
                print("BAD  %s -- a change the harness is supposed to FOLLOW turned it red" % name)
                for f in failed_lines(mout):
                    print("     %s" % f)
                print("     %s" % why)
                bad += 1
            elif must_contain not in states:
                print("BAD  %s -- the states file has no %r, so the harness is not"
                      " reading the shipped bytes" % (name, must_contain))
                print("     %s" % why)
                bad += 1
            else:
                print("OK   %s" % name)
                print("     the states file carries %r and the suite stayed green" % must_contain)
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
        print("%d of %d mutations were not caught as specified"
              % (bad, len(MUTATIONS) + len(FOLLOW_MUTATIONS)))
        return 1
    print("all %d guards are load-bearing: removing any one turns the suite red,"
          " and the %d the harness is meant to FOLLOW leave it green while the"
          " bytes it reads move"
          % (len(MUTATIONS), len(FOLLOW_MUTATIONS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
