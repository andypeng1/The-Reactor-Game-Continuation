"""Prove that the end-of-shift harness can FAIL, and can fail for the right reason.

A green suite is only evidence if the suite is capable of going red. The panel and
driver harnesses are checked by inspection of their scenarios; `endReason` cannot
be, because its failure mode is not a wrong answer -- it is a wrong SEAL, either
too early (a truncated file with a valid-looking receipt, which looks finished) or
too late (no receipt at all, which is the 18:35 capture). Both are silent.

So each guard is disabled in the SHIPPED recorder, the harness is rebuilt from it,
and the run must go red ON THE ASSERTION THAT GUARDS THAT PROPERTY. Not "red
somewhere" -- a suite that fails for an unrelated reason on every mutation would
pass a check that only looked at the exit code.

The recorder is restored from the bytes read at startup, so a crash mid-way cannot
leave a mutated script on disk. The clean harness is rebuilt at the end for the
same reason: `_end_states.luau` is generated and must not be left holding a
mutant.

    python _tools/selftest_end_test.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORDER = ROOT / "TRG_original_recorder.luau"
BUILDER = ROOT / "build_end_test.py"
LUA = r"D:\Lua\5.1\lua.exe"
STATES = ROOT / "_end_states.luau"

# Each entry: a name, the exact shipped text to replace, what to put there, and
# the assertion string that must be the one to go red. The `why` is the real bug
# the mutation models -- a mutation nobody would ever write proves nothing about
# the code, only about the harness's ability to notice any difference at all.
MUTATIONS = [
    (
        "the everRan gate is removed",
        "\tif not everRan then return nil end\n",
        "",
        "E2 a cold opening never seals itself",
        "A level test on a cold core seals the file two seconds after inject. A1 "
        "makes this the state EVERY run now starts in, so it is a total loss.",
    ),
    (
        "the cold dwell is cut to one poll",
        "\t\tif coldPolls >= Config.SealColdSamples then",
        "\t\tif coldPolls >= 1 then",
        "E4 one poll short of the cold dwell",
        "A single dip below the trip line ends the recording, and the receipt "
        "makes it look like a shift that finished.",
    ),
    (
        "the shift-end signal is gated on the core being down",
        "if flagEdge('s.GameActive', true, false) then",
        "if flagEdge('s.GameActive', true, false) and sawDown then",
        "E1 true to false seals on the FIRST poll",
        "Requiring two signals to agree before sealing is the plausible "
        "implementation of D4, and it loses the file whenever the temperature "
        "readout lags -- which is the 18:35 capture exactly.",
    ),
]

# Mutations the suite has to SURVIVE, because the harness reads the number
# instead of carrying one. Green is the pass condition here, which is the
# opposite of every entry above, and so is the claim: not "the recorder is
# guarded" but "the harness has no opinion of its own".
#
# The 1000 F correction is why this class exists. The builder's Config used to be
# a typed copy of the recorder's, so moving the cold-trip line left the dwell test
# measuring the line the recorder had just stopped using -- green, and about
# nothing. A test that only ever goes red cannot tell that case from a working
# one, so this one is asserted to stay green AND to show the new number.
FOLLOW_MUTATIONS = [
    (
        "the cold-trip line moves",
        "\tLowTripF        = 1000,",
        "\tLowTripF        = 800,",
        "LowTripF = 800,",
        "The built states file must carry the shipped number. A typed copy would "
        "keep 1000 and go on passing about a line nothing uses.",
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
    return run([LUA, "-e", "print(assert(loadfile('_tools/_end_states.luau'))())"])


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
                      " reading the shipped number" % (name, must_contain))
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
          " and the %d the harness is meant to FOLLOW leave it green while moving"
          " the number it measures"
          % (len(MUTATIONS), len(FOLLOW_MUTATIONS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
