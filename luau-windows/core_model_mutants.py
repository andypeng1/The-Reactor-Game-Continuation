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
     "        return 0.0, 0.0, amp, STALL_FLUC, 0.0, True, 0.0",
     "        return 0.0, 0.0, amp, (STALL_FLUC if power > 0.0 else 0.0), "
     "0.0, True, 0.0",
     "his -586, exactly, with every bank dark"),

    ("the tremor rides on a stalled tick, as it did before the correction",
     "        return 0.0, 0.0, amp, STALL_FLUC, 0.0, True, 0.0",
     "        return 0.0, 0.0, amp, STALL_FLUC, noise(t, power), True, 0.0",
     "a stalled tick with every bank LIT moves by exactly -586"),

    ("the stall stops swallowing the pump term",
     "        return 0.0, 0.0, amp, STALL_FLUC, 0.0, True, 0.0",
     "        return 0.0, 0.0, amp, STALL_FLUC, 0.0, True, coolant",
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

    # --- the split, which is what the 2026-10-16 spec actually did -----------
    # Until that message the heat was one table per row: `active[row]`, a slope
    # and an offset each, all of it under the lasers' off rule.  His spec splits
    # it into ONE curve with no row in it plus four row constants, and moves the
    # constants outside the off rule -- which is the one behaviour this spec
    # changes (a console with every bank dark now falls at its row's rate where
    # it used to hold still).
    #
    # Every way of quietly putting the two halves back together is a way to look
    # right, because the panel draws the same tiles either way.  So each gets a
    # tooth, and each is sent to the check that reads the number it moves.
    ("the curve loses its own zero gate",
     "    if power <= 0.0:",
     "    if power <= 0.0 and False:",
     "a dark console adds no curve"),

    ("the row constant is dropped from the tick",
     "        temperature = sim.Temperature + actual + passiv + tremor - cooling",
     "        temperature = sim.Temperature + actual + tremor - cooling",
     "a dark laser bank does not silence the pumps"),

    ("the row constant is scaled by the press band like the heat is",
     "        temperature = sim.Temperature + actual + passiv + tremor - cooling",
     "        temperature = sim.Temperature + actual + passiv * amp + tremor "
     "- cooling",
     "the doubled band scales neither the cooling nor the row constant"),

    # The reverse direction, and the one the whole correction was about: the
    # reading this spec replaced.  A terminal that gated the row's constant on
    # the lasers would hold still with every bank dark, which is what the panel
    # did until 2026-10-16 and what the "off" section now asserts against.
    # CLAUDE.md 0.34 (4): a reading reversed out of the file must not become
    # unfalsifiable in the meantime, so it comes back as a mutant.
    ("the row constant goes back under the lasers' off rule",
     "    return heat, passive(row), amp, active, noise(t, power), False, coolant",
     "    return heat, passive(row) if power > 0.0 else 0.0, amp, active, "
     "noise(t, power), False, coolant",
     "so a dark console falls -- the change this spec makes"),

    # The two middle rows are the pair that can be swapped without any of the
    # numbers looking wrong on their own -- -400 and -422 are both plausible
    # losses for a row, and a reader who did not have the spec open could not
    # say which row either belonged to.  The check that reads all four rows at
    # once is what makes the swap loud.
    ("rows 1 and 2 trade their constants",
     "PASSIVE_ROW = (-455.7, -400.0, -422.0, -22.0)",
     "PASSIVE_ROW = (-455.7, -422.0, -400.0, -22.0)",
     "pure_cbl(50) + passive, the four rows"),

    # --- the coolant pumps ---------------------------------------------------
    # Ways the third control can be wrong while the panel still looks right.
    # The first four are the placement choices made in COOLANT_PER_LEVEL plus
    # the constant itself; the last two are the unit it multiplies.
    #
    # That unit is the line in gui.py that moved three times on 2026-10-16 --
    # averaged, then not, then averaged again -- and the two mutants at the end
    # of this block are the two readings it has actually been written with.  The
    # one in force is the mean, so the SUM is the wrong reading now, and it is
    # the one that has to have a tooth: a spec that has been reversed once can be
    # reversed back, and the reading it was reversed out of must not become
    # unfalsifiable in the meantime (CLAUDE.md 0.34).  Both anchor on the same
    # line and both are sent to the same check, because there is one line and the
    # question about it is which unit it multiplies.

    ("the cooling constant becomes a remembered number",
     "COOLANT_PER_LEVEL = 120.0",
     "COOLANT_PER_LEVEL = 100.0",
     "the cooling is 120 a MEAN level, averaged over three"),

    ("the cooling is added instead of removed",
     "        temperature = sim.Temperature + actual + passiv + tremor - cooling",
     "        temperature = sim.Temperature + actual + passiv + tremor + cooling",
     "a dark laser bank does not silence the pumps"),

    ("the cooling is tucked under the lasers' off-rule",
     "            row, self.power, sim.Pressure, self.t, self.cooling)",
     "            row, self.power, sim.Pressure, self.t,\n"
     "            self.cooling if self.power > 0.0 else 0.0)",
     "a dark laser bank does not silence the pumps"),

    ("the cooling is scaled by pMultiplier like the heat is",
     "        temperature = sim.Temperature + actual + passiv + tremor - cooling",
     "        temperature = sim.Temperature + actual + passiv + tremor "
     "- cooling * amp",
     "the doubled band scales neither the cooling nor the row constant"),

    ("the three pump levels are read as one pump",
     "        coolant_avg = sum(self.pumps) / float(COOLANT_PUMPS)",
     "        coolant_avg = self.pumps[0]",
     "the cooling is 120 a MEAN level, averaged over three"),

    ("the pump mean goes back to being the sum",
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
    """Run the checker in `where`, with the bytecode cache OFF (`-B`).

    Returns (number of checks run, [failed check names]).  The first is None
    when the checker never got to its own summary line, which is a crash and
    not an empty run (CLAUDE.md 0.6: a crash and a pass can leave the same exit
    code, so the TEXT is what says which happened).

    `-B` IS NOT AN OPTIMISATION, IT IS THE FIX FOR A MEASURED LIE.  CPython
    validates a cached .pyc against its source's mtime **in whole seconds** and
    the source's size.  Most mutants below are the SAME LENGTH as the text they
    replace (`-586.0` -> `-750.0`, `2200.0` -> `2500.0`), and the checker takes
    about 0.85 s, so a mutant written inside the same second as the version
    before it produced an identical (seconds, size) pair and Python reused the
    PREVIOUS run's bytecode.  The mutant then never ran, and this script
    reported it as a HOLE -- "the checks have no teeth" -- when in fact nothing
    had been broken.  It was intermittent, which is how it survived: two
    consecutive runs holed two different mutants, and each run's other 22 were
    green.  Measured rather than reasoned: with the cache on, writing a mutated
    `gui.py` and immediately importing it returned the PREVIOUS file's
    `STALL_FLUC`.  No .pyc is written now, so there is nothing to go stale --
    and `_stray_cache` reads that back instead of trusting the flag.
    """
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", CHECKER],
                          cwd=where, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    failed = [line.split("FAILED:", 1)[1].strip()
              for line in text.splitlines() if line.startswith("  FAILED:")]
    for line in text.splitlines():
        if line.endswith("failed") and "checks," in line:
            return int(line.split()[0]), failed
    return None, text.strip().splitlines()[-6:]


def _stray_cache(where):
    """What is in `where`'s __pycache__, if `-B` did not hold.

    The flag above is a request; this is the reading.  A cache that reappears
    puts the staleness back, so it is worth failing the run over rather than
    discovering it as another intermittent HOLE (CLAUDE.md 0.2: read the world,
    do not read the intention).
    """
    cached = os.path.join(where, "__pycache__")
    if os.path.isdir(cached):
        return sorted(os.listdir(cached))
    return []


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
        if _stray_cache(where):
            print("baseline left a bytecode cache behind: %s -- `-B` did not "
                  "hold, so every mutant below could be running the previous "
                  "one's code" % _stray_cache(where))
            return 1

        holes = []
        for name, old, new, want in MUTANTS:
            body = source.replace(old, new)
            with open(os.path.join(where, TARGET), "wb") as handle:
                handle.write(body.encode("utf-8"))
            total, failed = run_checker(where)
            if total is None:
                print("CRASH  %-56s %s" % (name, failed))
                holes.append(name)
                continue
            # Two readings that make "the mutant never ran" impossible to
            # mistake for "the checks have no teeth" (see run_checker): the
            # mutation is on disk in the file the checker compiles, and no
            # bytecode cache is standing in front of it.
            stray = _stray_cache(where)
            if new not in read(os.path.join(where, TARGET)) or stray:
                print("CRASH  %-56s the mutation did not reach the checker%s"
                      % (name, " (cache: %s)" % stray if stray else ""))
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
