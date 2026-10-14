"""Checks for the core temperature model in `gui.py`.

    python core_model_check.py

The window is built and withdrawn, then driven a tick at a time.  Every number
is read back OFF THE WIDGETS -- `screen()` walks the grid and resolves each
label's textvariable -- because a value that is right in the model and wrong on
the screen is exactly the failure this file exists to catch, and reading
`Core`'s own attributes could never see it.

Nothing here re-runs `gui.py`'s arithmetic to compare it against itself (that
would pass even if both were wrong): the anchors are his equation transcribed
straight from the spec as it was handed over, with his own literals.

The spec is the 2026-10-14 revision -- the one headed "temperature calculation",
a per-tick STEP:

    T' = T + (active[row] + passive[row]) * pMultiplier + noise(t)

which replaced the 2026-10-13 closed form `T0 + (rate + noise(x)) * x`.  The
differences are not cosmetic and two of them are checked here by name: the noise
is added to the reading rather than multiplied into a rate, and a row change
changes the increment instead of moving a whole line.

Exit status is 1 if any check failed, 0 if all passed, so a broken run is not a
silent one.  ASCII only on stdout -- this console is GBK.
"""

import math
import sys
import tkinter as tk

import gui

FAILURES = []
CHECKS = [0]


def check(name, got, want):
    CHECKS[0] += 1
    if got == want:
        print("ok   %-44s %r" % (name, got))
        return True
    print("FAIL %-44s got %r, wanted %r" % (name, got, want))
    FAILURES.append(name)
    return False


# ========== reading the screen ==========

def text_of(widget):
    """What a widget is displaying.

    A label wired to a textvariable answers '' to cget('text'), so the variable
    has to be resolved -- reading cget alone would report every readout in the
    window as blank, and a check against a blank screen is a check that cannot
    fail.
    """
    try:
        name = str(widget.cget("textvariable"))
    except tk.TclError:
        name = ""
    if name:
        return widget.getvar(name)
    try:
        return widget.cget("text")
    except tk.TclError:
        return ""


def screen(parent):
    """{label text: shown value} for every readout, read off the grid.

    Walks the widgets rather than the Console's own list of readouts, so a
    readout that was built but never placed on the grid is invisible here too --
    which is the right answer, because it is invisible on screen as well.
    """
    cells = {}
    for widget in parent.winfo_children():
        info = widget.grid_info()
        if not info:
            continue
        key = (int(info["row"]), int(info["column"]))
        cells.setdefault(key, []).append(widget)
    out = {}
    for (row, column), widgets in cells.items():
        if column != 1 or (row, 0) not in cells:
            continue
        out[text_of(cells[(row, 0)][0])] = " ".join(text_of(w) for w in widgets)
    return out


def log_text(console):
    return console.log_text.get("1.0", "end")


# ========== his equation, transcribed from the spec ==========
# Literals as handed over, in his order.  This is a second spelling of the spec,
# not a call back into gui.py.
#
# His `s` runs 1..3 and his lists are 1-based, so he writes `active[s+1]`; the
# leading slot -- index 1 to him -- is what row 0 reads below.  Writing the lists
# out 0-based in his own order makes the index the row, which is the whole of the
# translation.

def his_active(row, level):
    a = level * 25.0
    return [0, 6.86 * a + 65.5, 7.24 * a + 37, 6.8 * a + 534][row]


def his_passive(row):
    return [-455.7, -19.2, 0, 0][row]


def his_base_fluc(row, level):
    return his_active(row, level) + his_passive(row)


def his_press(pressure):
    if pressure <= 11500:
        return 1
    if pressure <= 27000:
        return 2
    return 4


def his_noise(x, level):
    return (15 * level * math.sin(x / 1.5)
            + 10 * level * math.sin(x / 0.7)
            + 5 * level * math.sin(x / 0.3))


def his_temperature(temp, row, level, pressure, x):
    return temp + his_base_fluc(row, level) * his_press(pressure) + his_noise(x, level)


# ========== the run ==========

def main():
    root = tk.Tk()
    root.withdraw()
    console = gui.Console(root)
    root.update_idletasks()

    top = root.winfo_children()[0]
    right = [w for w in top.winfo_children()
             if int(w.grid_info().get("column", -1)) == 1][0]
    values = screen(right)

    # --- the model is off, and stays out of the way -------------------------
    print("\n-- core model off (the console as it was) --")
    check("Arm starts unchecked", console.arm_var.get(), False)
    check("T' is blank before any step", values["T'  next tick's temperature"], "-")
    check("the readout list is what the grid holds", len(values) >= 21, True)

    for _ in range(3):
        console.step_once()
    values = screen(right)
    check("Temperature untouched by the model", values["Temperature"], "5600")
    check("pressure after 3 unchanged ticks", values["Pressure"], "6498")
    check("latched pressure state", values["Pressure state (latched)"], "1")
    check("core state read from temperature",
          values["Core state (from Temperature)"], "1")

    # --- the boundaries of the pure function --------------------------------
    # The whole reason this is not Sim.State: the row is recomputed from the
    # temperature every tick and can fall, and there is a row 0 the latched state
    # can never reach.  The two upper boundaries are the SPEC's spelling
    # (`T < 17500`, `T < 29500`), which puts exactly 17500 in row 2 and exactly
    # 29500 in row 3 -- one degree lower than Engine.luau:320's `>` at the same
    # two numbers.  Recorded here so the difference is a reading, not a rumour.
    print("\n-- core_state boundaries (the spec's `s`) --")
    check("core_state(5599.9)", gui.core_state(5599.9), 0)
    check("core_state(5600)", gui.core_state(5600), 1)
    check("core_state(17499.9)", gui.core_state(17499.9), 1)
    check("core_state(17500)", gui.core_state(17500), 2)
    check("core_state(29499.9)", gui.core_state(29499.9), 2)
    check("core_state(29500)", gui.core_state(29500), 3)
    check("noise(0, 50) is 0", gui.noise(0.0, 50.0), 0.0)

    # --- his two lists, against the model's one table -----------------------
    print("\n-- active + passive, his literals --")
    for row in (0, 1, 2, 3):
        for level in (1, 3, 5):
            name = "fluctuation(row %d, level %d)" % (row, level)
            check(name, gui.fluctuation(row, level * 25.0),
                  his_base_fluc(row, level))
    print("-- pMultiplier, his literals --")
    check("press_multiplier(11500)", gui.press_multiplier(11500.0), 1.0)
    check("press_multiplier(11500.1)", gui.press_multiplier(11500.1), 2.0)
    check("press_multiplier(27000)", gui.press_multiplier(27000.0), 2.0)
    check("press_multiplier(27000.1)", gui.press_multiplier(27000.1), 4.0)
    check("press_multiplier(0)", gui.press_multiplier(0.0), 1.0)

    # --- armed --------------------------------------------------------------
    print("\n-- armed: the model owns Temperature --")
    console.arm_var.set(True)
    console.on_arm()
    values = screen(right)
    check("t starts at 0", values["t   elapsed since armed (s)"], "0")
    check("T is the live temperature", values["T   this step starts from"], "5600")
    check("no step yet, so no terms", values["T'  next tick's temperature"], "-")
    check("slider out of service", str(console.temp_slider.cget("state")),
          "disabled")
    check("spinbox out of service", str(console.temp_spin.cget("state")),
          "disabled")
    check("row buttons off while auto", str(console.core_buttons[0].cget("state")),
          "disabled")
    check("CBL starts at PW2", console.cbl_var.get(), 50)
    headers = [text_of(w) for w in right.winfo_children()
               if "core model" in text_of(w)]
    check("the panel prints his equation",
          headers[0] if headers else "",
          "the core model   T' = T + baseFluc * press + noise(t)")

    # One tick at a time, against his equation with his literals.  The tick
    # period is 1.0 s, so at the Nth tick t = N and level = 50/25 = 2.
    deltas = []
    for n in (1, 2, 3):
        pressure = console.sim.Pressure
        temp = console.sim.Temperature
        console.step_once()
        values = screen(right)
        want = his_temperature(temp, 1, 2, pressure, float(n))
        deltas.append(float(values["T'  next tick's temperature"]) - temp)
        check("t after tick %d" % n, values["t   elapsed since armed (s)"], str(n))
        check("row at tick %d" % n, values["row  (ACTIVE/PASSIVE index)"], "1")
        check("baseFluc at tick %d" % n, values["baseFluc  active + passive"], "389")
        check("press x at tick %d" % n, values["press x   pMultiplier"], "1")
        check("actualFluc at tick %d" % n, values["actualFluc  base x press"], "389")
        check("noise(%d)" % n, values["noise(t)"],
              gui.shown(his_noise(float(n), 2)))
        check("T' at tick %d against his equation" % n,
              values["T'  next tick's temperature"], gui.shown(want))

    # The revision, in one line: the noise is ADDED, so its amplitude is what it
    # says it is (+-30 at level 2) and a tick moves by about baseFluc.  In the old
    # closed form the same three sines were inside the multiplication, so the
    # same t gave a wobble of 30 * t and the step was 389 + 30t.
    print("\n-- the noise is a tremor on the reading, not on the slope --")
    check("noise(1) is tens, not tens x t", abs(his_noise(1.0, 2)) < 100, True)
    check("...so each of the three ticks moved by about baseFluc",
          all(abs(delta - 389) < 80 for delta in deltas), True)

    # --- the row changes, and NOTHING jumps ---------------------------------
    # In the closed form the row moved the whole line: crossing 2 -> 3 added
    # (1036 - 580) * x -- about nineteen thousand degrees by the time it was
    # crossed.  A step has no line to move.  This is the check that says so.
    print("\n-- the row changes, and nothing jumps --")
    steps = 0
    crossing = None
    previous_delta = None
    while steps < 400:
        was_row = console.core.last_row
        before = console.sim.Temperature
        console.step_once()
        steps += 1
        delta = console.sim.Temperature - before
        if console.core.last_row != was_row:
            crossing = (was_row, console.core.last_row, delta)
            break
        previous_delta = delta
    values = screen(right)
    check("a row change was reached", crossing is not None, True)
    check("...and it is 1 -> 2", crossing[0:2], (1, 2))
    check("...and the reading moved by one tick, not by a line",
          abs(crossing[2]) < 3000, True)
    # The tight one: row 1's base is 389.3 and row 2's is 399.0 at level 2, so
    # the tick that changes row moves like the tick before it (within 10 x amp).
    # Under the closed form this same comparison read ~19000 against ~500.
    check("...and the tick at the change moved like the one before it",
          abs(crossing[2] - previous_delta) < 100, True)
    check("log records the row change", "core row 1 -> 2" in log_text(console),
          True)

    steps = 0
    tail = None
    while steps < 400:
        before = console.sim.Temperature
        pressure = console.sim.Pressure
        row = console.core.row(console.sim)
        console.step_once()
        steps += 1
        if console.core.last_row == 3:
            tail = (row, his_press(pressure), console.sim.Temperature - before)
            break
    values = screen(right)
    check("row 3 reached", console.core.last_row, 3)
    check("...and the pressure reached its second band",
          gui.press_multiplier(console.sim.Pressure) >= 2, True)
    check("log records that one too", "core row 2 -> 3" in log_text(console),
          True)

    # The headline of the revision, measured where it used to matter: with the
    # sines inside the multiplication the tremor overtook the rate by t = 30, so
    # a tick moved by base * press + noise(t) * t.  Added, a tick moves by
    # base * press plus the DIFFERENCE of two sines -- bounded by twice the
    # amplitude, a hair over 100 at level 2, whatever t is.  t here is in the
    # thirties.
    check("a late tick still moves by base x press",
          abs(tail[2] - his_base_fluc(tail[0], 2) * tail[1]) < 150, True)

    # The runaway is the model's to have: TEMP_MAX is the slider's range, not a
    # physical limit, and a console that silently capped the temperature at the
    # top of its own widget would hide the failure it is there to show.
    print("\n-- the runaway is not clipped to the slider --")
    for _ in range(20):
        console.step_once()
    values = screen(right)
    check("temperature past the slider top",
          float(values["T'  next tick's temperature"]) > gui.TEMP_MAX, True)
    check("the reading on screen is the model's own value",
          values["T'  next tick's temperature"],
          gui.shown(console.sim.Temperature))
    check("the box carries the number past the slider top",
          int(console.temp_box.get()) > int(gui.TEMP_MAX), True)
    check("press x is showing the amplification on screen",
          values["press x   pMultiplier"] in ("2", "4"), True)
    check("baseFluc on screen is row 3's",
          values["baseFluc  active + passive"], "874")

    # --- the guards ---------------------------------------------------------
    print("\n-- a control cannot out-argue the model --")
    frozen = values["Temperature"]
    console.temp_box.set("12345")
    console.on_temp_box()
    values = screen(right)
    check("typed temperature refused while armed", values["Temperature"], frozen)
    check("...and the box is put back",
          console.temp_box.get(), gui.shown(console.sim.Temperature))

    # --- a row held by hand -------------------------------------------------
    # Reset first: the runaway above ran t out to 180-odd seconds and the
    # temperature past the slider's ceiling, and the check below is about the
    # row, not about where the run got to.
    print("\n-- row held by hand --")
    console.reset()
    values = screen(right)
    check("reset puts the temperature back", values["Temperature"], "5600")
    check("reset puts t back", values["t   elapsed since armed (s)"], "0")
    check("reset clears the step terms", values["T'  next tick's temperature"], "-")
    check("armed survives a reset", console.arm_var.get(), True)

    console.auto_var.set(False)
    console.on_auto()
    check("row buttons live again",
          str(console.core_buttons[0].cget("state")), "normal")
    console.core_var.set(0)
    console.on_core_state()
    values = screen(right)
    check("changing the row clears the stale step",
          values["T'  next tick's temperature"], "-")
    check("...including the increment", values["actualFluc  base x press"], "-")
    pressure = console.sim.Pressure
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("row 0 in use", values["row  (ACTIVE/PASSIVE index)"], "0")
    check("row 0 is the cooling term",
          values["baseFluc  active + passive"], "-456")
    check("row 0 at level 2, his equation",
          values["T'  next tick's temperature"],
          gui.shown(his_temperature(temp, 0, 2, pressure, console.core.t)))
    check("negative and moving down",
          float(values["T'  next tick's temperature"]) < temp, True)

    # --- CBL power ----------------------------------------------------------
    # `a = level * 25`, which is the number the radios carry, so PW5 is level 5.
    # Row 3 held by hand for the on-screen check: at row 0 the level has no
    # effect at all (active[0] is 0), so a check made from the row the console
    # happens to be on would pass without ever looking at `a`.
    print("\n-- CBL power is his `a` --")
    for level, power in ((1, 25), (2, 50), (5, 125)):
        check("fluctuation(row 3, a=%d)" % power, gui.fluctuation(3, float(power)),
              his_base_fluc(3, level))
    console.auto_var.set(False)
    console.on_auto()
    console.core_var.set(3)
    console.on_core_state()
    console.cbl_var.set(125)
    console.on_power()
    check("his `a` is the power value", console.core.power, 125.0)
    console.step_once()
    values = screen(right)
    check("row 3 held", values["row  (ACTIVE/PASSIVE index)"], "3")
    check("full power on screen, his literals",
          values["baseFluc  active + passive"],
          gui.shown(his_base_fluc(3, 5)))

    # "off" is ours, not the spec's: the fit covers levels 1..5 and there is no
    # level 0 in it, so zero CBL is defined as adding nothing rather than by
    # extrapolating the line down to a = 0 (which would still add row 1's
    # intercept).  The tremor scales with the level, so it goes quiet too, and
    # the reading holds exactly still.
    print("\n-- off (level 0, not in the fit) --")
    console.cbl_var.set(0)
    console.on_power()
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("off adds no fluctuation", values["actualFluc  base x press"], "0")
    check("off adds no tremor either", values["noise(t)"], "0")
    check("off holds the reading still",
          values["T'  next tick's temperature"], gui.shown(temp))

    console.auto_var.set(True)
    console.on_auto()

    # --- disarm -------------------------------------------------------------
    # The row choice is not tied to arming, only the temperature widget is: a
    # held row is exactly what you reach for while the model is running.
    print("\n-- disarm --")
    console.auto_var.set(False)
    console.on_auto()
    check("a held row is usable while armed",
          str(console.core_buttons[0].cget("state")), "normal")
    console.arm_var.set(False)
    console.on_arm()
    check("slider back in service", str(console.temp_slider.cget("state")),
          "normal")
    check("row buttons still live",
          str(console.core_buttons[0].cget("state")), "normal")
    check("the model's value handed to the slider",
          console.temp_box.get(), gui.shown(console.sim.Temperature))

    console.temp_box.set("9000")
    console.on_temp_box()
    values = screen(right)
    check("the slider works again", values["Temperature"], "9000")

    root.destroy()
    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    for name in FAILURES:
        print("  FAILED: %s" % name)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
