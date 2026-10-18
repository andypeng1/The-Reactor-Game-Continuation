"""Cross-check the console's pressure recurrence against `calculation.py`.

    python -B pressure_parity.py

WHY THIS FILE EXISTS.  `gui.py` carries a HAND COPY of `calculation.py`'s
pressure model.  The copy is deliberate (the console has to run without the
.luau, and that file's header says so), but two spellings kept in step by a
person reading both is not a check -- and nothing was comparing them.
docs/TODO.md 3.8 item 3 calls this the one item in that section worth doing, in
these words: "要真守住，得有一个 harness 同时驱动两边、逐拍比 Pressure（在
全精度上比，不是比取整后的显示）".  This is that harness.

`core_model_check.py` does NOT cover this.  It drives the TEMPERATURE model and
reads the screen; the pressure terms are merely its input.  The two files meet
at one value (Temperature) and this is the only place the meeting is measured.

WHAT IS COMPARED.  Both sides are driven from ONE input sequence, one tick at a
time -- Temperature, ActiveFan (0..6: the seven radio buttons at gui.py:1132)
and PEALevel (1..4: the keys of PEA_GAIN).  After each tick both Pressures are
compared at FULL PRECISION: not through "%.14g", not through the widgets'
display rounding.  The display rounding is what makes two models look equal for
a long time after they have parted.

THE ALLOWANCE IS NAMED, DERIVED, AND PRINTED.  gui.py adds its four terms with
`sum(self.terms())`; calculation.py writes them out as `a + b + c + d`.  On
CPython 3.12+ `sum()` over floats is a compensated (Neumaier) sum, so the two
spellings CAN differ in the last bits with neither being wrong -- this repo
measured a 7.10543e-15 gap between two spellings of one formula once already
(DECISIONS_2 585, CLAUDE.md 0.33).  So the comparison is a tolerance.  Three
rules keep that tolerance from becoming a rubber stamp:

  * it is a BOUND, not a round number.  Each tick performs a fixed number of
    roundings on each side, so the allowance grows with the tick count and with
    the magnitude of the reading:
        PARITY_ULPS * ticks_so_far * eps * max(1, |P|)
    PARITY_ULPS is 4: the naive chain of four terms rounds at most ~3 times
    about the result, and the compensated one is the more accurate of the two.
  * the MEASURED delta is printed on every run, including when it is 0 and even
    when it is 0 the whole way -- "the allowance went unused" is a reading, and
    a run that silently consumes it is the one worth being suspicious of.
  * the smallest divergence this check must catch is seven orders of magnitude
    above it.  The closest two entries in any table are SLOPE's 0.0075 vs 0.005,
    i.e. 0.0025 * 5600 = 14 PSI in one tick, against an end-of-sweep allowance
    of ~1e-4 PSI.  A tolerance whose failure threshold is not orders of
    magnitude above what it must ignore is just a way to turn red into green.
    The gap is printed with the worst delta so the ratio can be re-checked by
    whoever reads this next.

WHAT THIS CANNOT SEE.  Both spellings can be wrong together -- this file is a
parity check, not a specification check.  The reference is `calculation.luau`;
the structural claims this harness does pin (the latch, which band the exact
boundaries belong to) are asserted separately below, against the docstring that
file and `Engine.luau` both state.

Exit status is 1 if any check failed, 0 if all passed.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calculation
import gui

# ========== THE SWEEP ==========

SEED = 20261018
TICKS = 20000

# gui.py's own ranges, not invented here: fans are the seven radio buttons in
# `_build_controls` (range(0, 7)) and PEA's keys ARE the four buttons.
FANS = tuple(range(0, 7))
PEAS = tuple(sorted(gui.PEA_GAIN))

# A scripted first lap that walks every boundary from both sides, then leaves a
# state latched and reads a COLD temperature under it.  The latch is the part
# that cannot be reached by a random walk in reasonable time: below STATE_MIN
# nothing is written, so the only way to see whether both spellings agree about
# "nothing happens" is to get into a state and then remove its cause.
#
# Each entry is (Temperature, expected-Pressure-terms-change); the expected
# State is asserted separately, below, as a claim about the REFERENCE file.
LADDER = (
    5600.0,        # exactly STATE_MIN -> State 1
    17499.9999,    # just under the 1/2 boundary -> stays 1
    17500.0,       # exactly the boundary -> 2 (the file says exclusive above)
    17500.0001,    # just over -> stays 2
    1000.0,        # COLD, from State 2 -> the latch keeps 2
    29499.0,       # exactly STATE_2_MAX -> 2 (inclusive)
    29499.0001,    # one ten-thousandth over -> 3
    29500.0,       # -> 3
    1000.0,        # COLD, from State 3 -> the latch keeps 3
    40000.0,       # -> 3
    5599.9999,     # COLD, from State 3 -> the latch keeps 3
    5600.0,        # -> 1
    5599.9999,     # COLD, from State 1 -> stays 1
)


def build_policy():
    """The input sequence both spellings are driven with.

    Deterministic from SEED.  Three phases:
      1. the LADDER, with every (fan, PEA) combination cycling under it, so the
         latch is exercised while the other two inputs are not held still;
      2. a full cross product -- every State, every fan count, every PEA level
         -- because a table entry that no tick ever reaches is a constant this
         check does not test (CLAUDE.md 0.31: ask what must be present for it
         to go red; an unreached row is never present);
      3. a seeded random walk, so the two accumulators run long enough for any
         per-tick rounding to show up as drift rather than cancel.
    """
    rng = random.Random(SEED)
    out = []

    combos = [(fan, pea) for fan in FANS for pea in PEAS]
    for i, temp in enumerate(LADDER):
        for j in range(len(combos)):
            fan, pea = combos[(i * len(combos) + j) % len(combos)]
            out.append((temp, fan, pea))

    # Temperatures chosen to sit inside each band, not on a boundary: this
    # block is about covering the table entries, and the boundaries have their
    # own lap above.
    for temp in (6000.0, 20000.0, 30000.0):
        for fan in FANS:
            for pea in PEAS:
                out.append((temp, fan, pea))

    temp = 15000.0
    for _ in range(TICKS - len(out)):
        temp += rng.uniform(-900.0, 900.0)
        temp = min(45000.0, max(0.0, temp))
        out.append((temp, rng.choice(FANS), rng.choice(PEAS)))

    return out


# ========== THE TWO DRIVERS ==========

def run_calculation(policy):
    """Drive `calculation.tick` -- the reference spelling."""
    state = {
        "Temperature": 5600,
        "Pressure": 6000,
        "ActiveFan": 0,
        "PEALevel": 1,
        "State": 1,
    }
    trace = []
    for temp, fan, pea in policy:
        state["Temperature"] = temp
        state["ActiveFan"] = fan
        state["PEALevel"] = pea
        calculation.tick(state)
        # Full precision: the float itself, never "%.14g".
        trace.append((state["Pressure"], state["State"]))
    return trace


def run_gui(policy):
    """Drive `gui.Sim.tick` -- the hand copy.

    The inputs are written straight onto the instance, which is what the
    console's own callbacks do (`self.sim.Temperature = ...` then `on_input`).
    Nothing else on `Sim` is touched: in particular `vent()` is never called,
    because the AVB is a ONE-SHOT the reference file does not model at all --
    it is not part of the recurrence and comparing it would be a false failure.
    """
    sim = gui.Sim()
    trace = []
    for temp, fan, pea in policy:
        sim.Temperature = temp
        sim.ActiveFan = fan
        sim.PEALevel = pea
        sim.tick()
        trace.append((sim.Pressure, sim.State))
    return trace


# ========== THE COMPARISON ==========

PARITY_ULPS = 4.0
EPS = sys.float_info.epsilon


def allowance(tick, pressure):
    """How far apart the two spellings may be after `tick` additions.

    `tick` is 1-based.  The derivation is in the module docstring; the short
    version is that each side makes a bounded number of roundings per addition
    and the two orders differ by at most a few ulps of the running result.
    """
    return PARITY_ULPS * tick * EPS * max(1.0, abs(pressure))


def compare(left, right):
    """Compare two traces.  Returns (state_diffs, pressure_diffs, worst).

    `worst` is (delta, its allowance, tick) for the largest delta that stayed
    INSIDE the allowance, so a run that used none of it can say 0 rather than
    say nothing.
    """
    state_diffs = []
    pressure_diffs = []
    worst = (0.0, 0.0, 0, 0.0)
    for i, ((lp, ls), (rp, rs)) in enumerate(zip(left, right), start=1):
        if ls != rs:
            state_diffs.append((i, ls, rs))
        delta = abs(lp - rp)
        limit = allowance(i, lp)
        if delta > limit:
            pressure_diffs.append((i, lp, rp, delta, limit))
        elif delta > worst[0]:
            worst = (delta, limit, i, lp)
    return state_diffs, pressure_diffs, worst


# ========== THE CHECKS ==========

CHECKS = [0]
FAILURES = []


def check(name, ok, detail=""):
    CHECKS[0] += 1
    if ok:
        print("ok   %-46s %s" % (name, detail))
    else:
        print("FAIL %-46s %s" % (name, detail))
        FAILURES.append(name)


def stated_state(temp, previous):
    """The reference's State transition, written out a third time -- on
    purpose.  If this copy and either driver disagree, the disagreement is the
    finding; deriving one from another would let a shared typo pass."""
    if 5600 <= temp < 17500:
        return 1
    if 17500 <= temp <= 29499:
        return 2
    if temp > 29499:
        return 3
    return previous


def main():
    policy = build_policy()
    print("pressure parity: calculation.py vs gui.py, %d ticks, seed %d"
          % (len(policy), SEED))

    left = run_calculation(policy)
    right = run_gui(policy)

    # ---- coverage: what the sweep actually put in front of the comparison ----
    states = sorted({s for _, s in left})
    fans = sorted({f for _, f, _ in policy})
    peas = sorted({p for _, _, p in policy})
    combos = {(s, f, p) for (_, f, p), (_, s) in zip(policy, left)}
    temperatures = [t for t, _, _ in policy]
    pressures = [p for p, _ in left]

    check("every State is reached", states == [1, 2, 3], repr(states))
    check("every fan count 0..6 is used", fans == list(FANS), repr(fans))
    check("every PEA level 1..4 is used", peas == list(PEAS), repr(peas))
    check("every (State, fan, PEA) is used", len(combos) == 3 * 7 * 4,
          "%d of %d" % (len(combos), 3 * 7 * 4))

    # ---- structural claims about the REFERENCE, not a parity result ----
    # These are the sentences in calculation.py's docstring and in Engine.luau
    # ("State latched, no else").  A parity check cannot see both sides losing
    # them together, so they are asserted against a third spelling.
    st = 1
    for temp, _, _ in policy:
        st = stated_state(temp, st)
    check("the third spelling agrees with calculation on State",
          st == left[-1][1], "last State %d vs %d" % (st, left[-1][1]))

    latch = run_calculation([(6000.0, 0, 1), (30000.0, 0, 1), (1000.0, 0, 1)])
    check("a cold reading does not reset a latched State",
          latch[-1][1] == 3, "State fell to %d" % latch[-1][1])
    boundaries = {
        "5600 is State 1":        run_calculation([(5600.0, 0, 1)])[-1][1] == 1,
        "5599.9999 from 1 stays": run_calculation([(6000.0, 0, 1), (5599.9999, 0, 1)])[-1][1] == 1,
        "17500 is State 2":       run_calculation([(17500.0, 0, 1)])[-1][1] == 2,
        "29499 is State 2":       run_calculation([(29499.0, 0, 1)])[-1][1] == 2,
        "29499.0001 is State 3":  run_calculation([(29499.0001, 0, 1)])[-1][1] == 3,
    }
    for name, ok in boundaries.items():
        check(name, ok)

    # ---- the parity itself ----
    state_diffs, pressure_diffs, worst = compare(left, right)
    check("both spellings pick the same State every tick",
          not state_diffs,
          "" if not state_diffs else "first at tick %d: %d vs %d" % state_diffs[0])
    check("Pressure agrees within the named allowance",
          not pressure_diffs,
          "" if not pressure_diffs else
          "first at tick %d: %r vs %r, delta %g > %g" % pressure_diffs[0])

    delta, limit, tick, at_pressure = worst
    used = (delta / limit * 100.0) if limit else 0.0
    # The unit this is really in: an ulp of the reading at that tick.  "5.8e-11"
    # says nothing on its own; "one ulp" says the two spellings differ by the
    # least amount a double can hold, which is the number the allowance was
    # derived for.  Print both, because the ulp count is the one that means
    # something and the percentage is the one that sits next to the bound.
    ulps = delta / math.ulp(at_pressure) if at_pressure else 0.0
    print("     measured worst delta %g at tick %d = %g ulp of %g "
          "(%.4g%% of its allowance %g)"
          % (delta, tick, ulps, at_pressure, used, limit))
    check("the allowance is not the thing holding it together",
          delta < 14.0 / 1e6,
          "worst delta %g must stay 6+ orders under one SLOPE step (14 PSI)" % delta)

    # A reading both traces share, so a sweep that quietly ran on empty input
    # cannot pass: the Pressure must actually have moved, and far enough that
    # the accumulation phase mattered.
    check("the sweep moved Pressure far enough to accumulate",
          max(pressures) - min(pressures) > 1e5,
          "range %g .. %g" % (min(pressures), max(pressures)))
    check("Temperature actually crossed all three bands",
          min(temperatures) < 5600 < 17500 < 29499 < max(temperatures),
          "range %g .. %g" % (min(temperatures), max(temperatures)))

    # ---- determinism, so a later red is the model and not the sweep ----
    check("the sweep is deterministic",
          run_calculation(policy) == left and run_gui(policy) == right)

    # ---- the ruler has teeth: mutate each side and require it to go red ----
    print("\nmutants (each must be caught, and the last must not):")

    def under_mutation(factory):
        """Run the whole sweep with one constant moved, then put it back.

        `factory` applies the change and returns the undo.  The undo runs in a
        `finally` so a mutant that makes a driver raise cannot leave the module
        patched for the next mutant or for the exit report.
        """
        restore = factory()
        try:
            l = run_calculation(policy)
            r = run_gui(policy)
        finally:
            restore()
        sd, pd, _ = compare(l, r)
        return (sd, pd)

    def patch(obj, attr, value):
        old = getattr(obj, attr)
        setattr(obj, attr, value)
        return lambda: setattr(obj, attr, old)

    def patch_item(table, key, value):
        old = table[key]
        table[key] = value
        return lambda: table.__setitem__(key, old)

    mutants = [
        # (name, mutate-then-restore factory, which side it hits)
        ("gui.STATE_GAIN[3] + 0.02",
         lambda: patch_item(gui.STATE_GAIN, 3, gui.STATE_GAIN[3] + 0.02)),
        ("gui.SLOPE[2] x (1 + 1e-7)",
         lambda: patch_item(gui.SLOPE, 2, gui.SLOPE[2] * (1.0 + 1e-7))),
        ("gui.PEA_GAIN[4] + 1",
         lambda: patch_item(gui.PEA_GAIN, 4, gui.PEA_GAIN[4] + 1)),
        ("gui.FAN_DRAG - 1",
         lambda: patch(gui, "FAN_DRAG", gui.FAN_DRAG - 1.0)),
        ("gui.STATE_2_MAX 29499 -> 29500",
         lambda: patch(gui, "STATE_2_MAX", 29500)),
        ("calculation.STATE_GAIN[1] + 0.02",
         lambda: patch_item(calculation.PressureBenefitState, 1,
                            calculation.PressureBenefitState[1] + 0.02)),
        # The null mutant: a name neither tick reads.  If this one goes red the
        # comparison is not measuring the model, it is measuring the module.
        ("gui.BANDS untouched (null mutant)",
         lambda: patch(gui, "BANDS", dict(gui.BANDS))),
    ]

    for name, factory in mutants:
        sd, pd = under_mutation(factory)
        hit = sd[0][0] if sd else (pd[0][0] if pd else None)
        if "null" in name:
            check(name, not sd and not pd, "still green, as it must be")
        else:
            check(name, bool(sd or pd),
                  "caught at tick %s" % hit if hit else "NOT CAUGHT")

    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    for name in FAILURES:
        print("  FAILED: %s" % name)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
