"""core_model_mutants.py -- do the checks in core_model_check.py have teeth?

    python core_model_mutants.py

A green checker proves nothing on its own.  CLAUDE.md 0.31 (1) is the reason
this file exists: an assertion can pass because the thing it is about is not in
the room, and the run looks exactly the same as a real pass.  The question to
ask about every check is "to make THIS red, what has to be present?", and the
only honest way to answer it is to break the thing on purpose and watch.

So: each mutant below is one small edit to `gui.py`, applied to a COPY in a
temporary directory.  The checker then runs against the copy.  A mutant that
leaves the checker green is a HOLE -- some line the checks never actually read
-- and this script exits 1.  Each mutant also names the check it must redden,
because "something went red" is not the same reading as "the right thing went
red" (the failure count alone cannot tell those apart).

Three things this deliberately does NOT do:

  * it does not mutate the working tree -- the edits happen in a temp dir, so a
    crash mid-run cannot leave a half-edited gui.py behind (CLAUDE.md 0.4);
  * it does not skip the baseline -- if the unmutated checker is already red,
    every mutant "fails" for that reason and the whole run is noise, so the
    baseline is run first and a red one aborts;
  * it does not compare counts of failures -- one mutant reddening forty checks
    is not a better mutant than one reddening exactly the one it should.

ASCII only on stdout: this console is GBK.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = "core_model_check.py"
TARGET = "gui.py"

# (name, the exact text to replace, what to put there, a check that MUST fail)
#
# Every `old` must appear EXACTLY ONCE in gui.py -- asserted below rather than
# hoped for, because a substring anchor that matches in the wrong place is
# CLAUDE.md 0.13, and it fails by silently editing something else.
MUTANTS = (
    ("the stall rate becomes our own game's",
     "STALL_FLUC = -586.0",
     "STALL_FLUC = -750.0",
     "his -586, exactly, with every bank dark"),

    ("the stall gate is written with a bare <",
     "    return pressure <= AVB_STALLOUT_PSI",
     "    return pressure < AVB_STALLOUT_PSI",
     "stalled(2200) -- his `<=`"),

    ("the stall floor moves off 2200",
     "AVB_STALLOUT_PSI = 2200.0",
     "AVB_STALLOUT_PSI = 2500.0",
     "stalled(2200.1) -- not quite"),

    ("the stall is not remembered for the readout",
     "        self.last_stall = stall",
     "        self.last_stall = False",
     "the step gated on it"),

    # The 2026-10-16 correction, in both directions.  His `dT` is piecewise, so
    # the stall branch REPLACES the whole expression; the two mutants below are
    # the two ways of un-replacing it -- let the dark lasers zero it (the old
    # reading had the lasers' off-rule in charge), and let the tremor ride on
    # top (the reading QUESTIONS.md R12 files).  Both anchor on the same line
    # on purpose: there is one stall branch, and it is the thing under test.
    ("a stalled tick is allowed to be zeroed by the dark lasers",
     "        return STALL_FLUC, amp, STALL_FLUC, 0.0, True, 0.0",
     "        return STALL_FLUC, amp, (STALL_FLUC if power > 0.0 else 0.0), "
     "0.0, True, 0.0",
     "his -586, exactly, with every bank dark"),

    ("the tremor rides on a stalled tick, as it did before the correction",
     "        return STALL_FLUC, amp, STALL_FLUC, 0.0, True, 0.0",
     "        return STALL_FLUC, amp, STALL_FLUC, noise(t, power), True, 0.0",
     "a stalled tick with every bank LIT moves by exactly -586"),

    ("the stall stops swallowing the pump term",
     "        return STALL_FLUC, amp, STALL_FLUC, 0.0, True, 0.0",
     "        return STALL_FLUC, amp, STALL_FLUC, 0.0, True, coolant",
     "the stall out-ranks the pumps too"),

    ("the vent takes our own Config's 3000 instead of the measured 3300",
     "AVB_PSI_DROP = 3300.0",
     "AVB_PSI_DROP = 3000.0",
     "the press took the wiki's 3300"),

    ("the drop is allowed to go negative",
     "        self.Pressure = max(0.0, before - AVB_PSI_DROP)",
     "        self.Pressure = before - AVB_PSI_DROP",
     "the pressure is floored at 0"),

    ("our Config's 26 ticks carried into the original's tick length",
     "AVB_COOLDOWN_TICKS = 15",
     "AVB_COOLDOWN_TICKS = 26",
     "the cooldown is the wiki's 15 ticks"),

    ("the cooldown never runs",
     "        if self.vent_ticks > 0:\n            self.vent_ticks -= 1",
     "        if self.vent_ticks > 0:\n            pass",
     "cooldown with 14 tick(s) to go"),

    ("the press does not start the clock at all",
     "        self.vent_ticks = AVB_COOLDOWN_TICKS",
     "        self.vent_ticks = 0",
     "the cooldown is the wiki's 15 ticks"),

    # --- the three laser banks ----------------------------------------------
    # What the fit consumes changed on 2026-10-16 from the SUM of the three
    # banks to their MEAN, and that is a change no panel layout can show: all
    # three spellings light the same radios and the tile reads a number in every
    # case.  Three mutants, one per wrong reading -- and note the check each one
    # is sent to: the three-banks section is driven at 125/50/0 rather than his
    # worked example's 125/75/25, because the mean of an arithmetic triple IS
    # the middle bank and a check written there could not separate the mean from
    # a glance at bank 2.
    ("his `a_avg` goes back to being the sum of the banks",
     "        return (sum(bank / CBL_UNIT for bank in self.banks) / CBL_BANKS) * CBL_UNIT",
     "        return sum(bank / CBL_UNIT for bank in self.banks) * CBL_UNIT",
     "his `a` is their mean, not their sum"),

    ("his `a_avg` reads one bank instead of their mean",
     "        return (sum(bank / CBL_UNIT for bank in self.banks) / CBL_BANKS) * CBL_UNIT",
     "        return self.banks[0]",
     "...nor any one bank"),

    ("the mean is divided by one bank instead of by three",
     "/ CBL_BANKS) * CBL_UNIT",
     "/ 1) * CBL_UNIT",
     "his `a` is their mean, not their sum"),

    ("the spec's `T < 5600` moves down to 5000",
     "CORE_ROW_1_AT = 5600",
     "CORE_ROW_1_AT = 5000",
     "the spec's `T < 5600` is the STATE_MIN this file already had"),

    # --- the coolant pumps ---------------------------------------------------
    # Ways the third control can be wrong while the panel still looks right.
    # The first four are the placement choices made in COOLANT_PER_LEVEL plus
    # the constant itself; the last three are the unit it multiplies, which is
    # what the 2026-10-16 correction moved (three pumps -> one average pump).

    ("the cooling constant becomes a remembered number",
     "COOLANT_PER_LEVEL = 120.0",
     "COOLANT_PER_LEVEL = 100.0",
     "the cooling is 120 a MEAN level, averaged over three"),

    ("the cooling is added instead of removed",
     "        temperature = sim.Temperature + actual + tremor - cooling",
     "        temperature = sim.Temperature + actual + tremor + cooling",
     "a dark laser bank does not silence the pumps"),

    ("the cooling is tucked under the lasers' off-rule",
     "            row, self.power, sim.Pressure, self.t, self.cooling)",
     "            row, self.power, sim.Pressure, self.t,\n"
     "            self.cooling if self.power > 0.0 else 0.0)",
     "a dark laser bank does not silence the pumps"),

    ("the cooling is scaled by pMultiplier like the heat is",
     "        temperature = sim.Temperature + actual + tremor - cooling",
     "        temperature = sim.Temperature + actual + tremor - cooling * amp",
     "the press multiplier does not scale the cooling"),

    ("the three pump levels are read as one pump",
     "        coolant_avg = sum(self.pumps) / float(COOLANT_PUMPS)",
     "        coolant_avg = self.pumps[0]",
     "the cooling is 120 a MEAN level, averaged over three"),

    ("the pump average goes back to being the sum",
     "        coolant_avg = sum(self.pumps) / float(COOLANT_PUMPS)",
     "        coolant_avg = float(sum(self.pumps))",
     "the cooling is 120 a MEAN level, averaged over three"),

    # The tremor's own scaling: `a_avg / 25`, which is why a dark laser bank is
    # silent.  Dropping the division makes every level read as if it were maxed.
    ("the tremor stops scaling by a_avg over 25",
     "    level = power / CBL_UNIT",
     "    level = power",
     "noise(1)"),
)


def read(path):
    with open(path, "rb") as handle:
        return handle.read().decode("utf-8")


def run_checker(where):
    """Run the checker in `where`.

    Returns (number of checks run, [failed check names]).  The first is None
    when the checker never got to its own summary line, which is a crash and
    not an empty run (CLAUDE.md 0.6: a crash and a pass can leave the same exit
    code, so the TEXT is what says which happened).
    """
    proc = subprocess.run([sys.executable, "-X", "utf8", CHECKER],
                          cwd=where, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    failed = [line.split("FAILED:", 1)[1].strip()
              for line in text.splitlines() if line.startswith("  FAILED:")]
    for line in text.splitlines():
        if line.endswith("failed") and "checks," in line:
            return int(line.split()[0]), failed
    return None, text.strip().splitlines()[-6:]


def main():
    source = read(os.path.join(HERE, TARGET))
    for name, old, _new, _want in MUTANTS:
        hits = source.count(old)
        # Anchors are asserted unique BEFORE anything is written -- the whole
        # point of 0.13 is that a non-unique anchor edits the wrong block and
        # says nothing.
        if hits != 1:
            print("BAD ANCHOR  %s: %d occurrence(s) in %s" % (name, hits, TARGET))
            return 1

    where = tempfile.mkdtemp(prefix="trg_mutants_")
    try:
        shutil.copyfile(os.path.join(HERE, CHECKER), os.path.join(where, CHECKER))
        print("baseline: the unmutated checker, in %s" % where)
        shutil.copyfile(os.path.join(HERE, TARGET), os.path.join(where, TARGET))
        total, failed = run_checker(where)
        if total is None or failed:
            print("baseline is %s -- every mutant below would 'fail' for that "
                  "reason and the run would be noise"
                  % ("a crash: %s" % failed if total is None else "already red"))
            return 1
        print("baseline ok: %d checks, 0 failed\n" % total)

        holes = []
        for name, old, new, want in MUTANTS:
            with open(os.path.join(where, TARGET), "wb") as handle:
                handle.write(source.replace(old, new).encode("utf-8"))
            total, failed = run_checker(where)
            if total is None:
                print("CRASH  %-56s %s" % (name, failed))
                holes.append(name)
                continue
            # Substring, not equality: the `want` strings above are written the
            # way a reader would say the check out loud, and the check's own
            # name may carry a prefix ("...and the pressure is floored at 0").
            hit = any(want in name for name in failed)
            print("%5s  %-56s %2d red%s"
                  % ("ok" if (failed and hit) else "HOLE", name, len(failed),
                     "" if hit else "   -- but not: %s" % want))
            if not failed or not hit:
                holes.append(name)
                if failed:
                    print("         it reddened: %s" % "; ".join(failed[:4]))
        print("\n%d mutants, %d survived or reddened the wrong check"
              % (len(MUTANTS), len(holes)))
        return 1 if holes else 0
    finally:
        shutil.rmtree(where, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:               # noqa: BLE001 -- CLAUDE.md 0.6: an
        import traceback                # uncaught exception here can leave
        traceback.print_exc()           # rc = 0, and "the runner crashed"
        sys.exit(1)                     # then reads as "no holes found".
