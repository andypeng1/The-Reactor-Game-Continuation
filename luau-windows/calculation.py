"""Python port of `calculation.luau` -- the chamber-pressure integrator.

The original is a Lune script (`require("@lune/task")` is only needed for the
1 Hz `task.wait`).  This keeps the same numbers, the same order of operations
and the same latched `State`, so the two print the same lines for the same
input -- which is how it was checked, by diffing both outputs.
"""
import time

# ========== STATE ==========

# The five values the tick carries.  Temperature / ActiveFan / PEALevel are
# inputs (constant here because the original's driver is not in this file);
# Pressure is the accumulator; State is written below and read back.
current = {
    "Temperature": 5600,
    "Pressure": 6000,
    "ActiveFan": 0,
    "PEALevel": 1,
    "State": 1,
}

# The three tables are keyed 1..3 (1..4 for PEA) in the original, because Luau
# tables are 1-based and the keys are the State / PEALevel values themselves.
# Keep the integer keys instead of shifting to 0-based lists: an off-by-one
# here would silently change every reading.
PressureBenefitPreTemp = {1: 0.01, 2: 0.0075, 3: 0.005}
PressureBenefitPEA = {1: 0, 2: 0, 3: 75, 4: 150}
PressureBenefitState = {1: 110, 2: 350, 3: 800}

# p = g_{n}[b] - 60n + s_{n}[b] t + d_{n}[q]
# i.e. state gain + (pre-temp slope * Temperature) + PEA gain - 60 per fan.


def tick(state):
    """Advance `state` by one tick.  Returns nothing; Pressure is the carrier.

    EXTRACTED, NOT REWRITTEN (2026-10-18).  This body was `main_loop`'s until
    `_tools/pressure_parity.py` needed to drive it faster than 1 Hz and without
    a print per tick -- the console in `gui.py` carries a hand copy of this
    recurrence, and nothing was comparing the two (docs/TODO.md 3.8 item 3, the
    one that file calls worth doing).  A harness that has to scrape stdout once
    a second cannot run a boundary sweep; the same arithmetic behind a call can.

    The three lines `main_loop` keeps below are the whole of what moved out, and
    they still run in this order when the file is executed: state, then
    Pressure, then print.  Nothing about the numbers changed -- that is not a
    claim, it is what `_tools/pressure_parity.py` measures on every run, against
    the second spelling in `gui.py`.
    """
    # State is latched, not derived: the original's if/elseif chain has no
    # `else`, so a Temperature below 5600 (cold, or not yet started) leaves the
    # previous State standing rather than resetting it.
    if 5600 <= state["Temperature"] < 17500:
        state["State"] = 1
    elif 17500 <= state["Temperature"] <= 29499:
        state["State"] = 2
    elif state["Temperature"] > 29499:
        state["State"] = 3

    state["Pressure"] += (
        PressureBenefitState[state["State"]]
        + PressureBenefitPreTemp[state["State"]] * state["Temperature"]
        + PressureBenefitPEA[state["PEALevel"]]
        - 60 * state["ActiveFan"]
    )


def main_loop():
    tick(current)

    # Luau formats a number with "%.14g", so an integral double prints as
    # "6166" and not Python's repr "6166.0".  Match it, or the two logs cannot
    # be diffed.  flush=True so a killed run still shows the lines it printed.
    print("Pressure: " + ("%.14g" % current["Pressure"]), flush=True)


# The guard is what makes the module importable: without it, the harness above
# would hang on the import.  Running `python calculation.py` still lands here
# and still prints one line a second, which is the behaviour this file had.
if __name__ == "__main__":
    while True:
        main_loop()
        time.sleep(1)
