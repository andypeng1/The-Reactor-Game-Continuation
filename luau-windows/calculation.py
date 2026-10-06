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


def main_loop():
    # State is latched, not derived: the original's if/elseif chain has no
    # `else`, so a Temperature below 5600 (cold, or not yet started) leaves the
    # previous State standing rather than resetting it.
    if 5600 <= current["Temperature"] < 17500:
        current["State"] = 1
    elif 17500 <= current["Temperature"] <= 29499:
        current["State"] = 2
    elif current["Temperature"] > 29499:
        current["State"] = 3

    current["Pressure"] += (
        PressureBenefitState[current["State"]]
        + PressureBenefitPreTemp[current["State"]] * current["Temperature"]
        + PressureBenefitPEA[current["PEALevel"]]
        - 60 * current["ActiveFan"]
    )

    # Luau formats a number with "%.14g", so an integral double prints as
    # "6166" and not Python's repr "6166.0".  Match it, or the two logs cannot
    # be diffed.  flush=True so a killed run still shows the lines it printed.
    print("Pressure: " + ("%.14g" % current["Pressure"]), flush=True)


while True:
    main_loop()
    time.sleep(1)
