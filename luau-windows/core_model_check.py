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


def readout(values, prefix):
    """The one reading whose label starts with `prefix`.

    `screen()` is keyed by rendered LABEL TEXT, which is what makes it a real
    reading of the screen rather than a lookup of the model -- but one label
    embeds a number the model also carries (`stallout  pres <= 2200`), and
    addressing it by its full text would make a change to that constant raise
    KeyError inside the checker instead of failing the check about it.  A crash
    and a red check are different readings (core_model_mutants.py is what found
    this), so the number is left out of the address and the prefix is asserted
    unique instead.
    """
    hits = [key for key in values if key.startswith(prefix)]
    if len(hits) != 1:
        raise KeyError("%r matched %d readings: %r" % (prefix, len(hits), hits))
    return values[hits[0]]


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


def his_cooling(levels):
    """What the pumps take off a tick: 120 a level, summed, added OUTSIDE his
    line and outside `pMultiplier`.

    Spelled from the three sources rather than from `gui.COOLANT_PER_LEVEL`:
    the original's own line in `Data/TRGWeb.luau` (`- (coolant_pump1_power +
    coolant_pump2_power + coolant_pump3_power)*120`), our remake's
    `Config.Sim.PumpCooling`, and the shipped log's exact identity
    `predDT*5 == 65*sum(cbl.level) - 120*sum(coolant.levels)` over all of its
    477 records (`_tools/coolant_from_log.py` prints it).  Reading the constant
    back off the module would make this a tautology.
    """
    return 120.0 * sum(levels)


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
    check("the readout list is what the grid holds", len(values) >= 28, True)

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
    check("CBL starts at PW2 on the first bank", console.cbl_vars[0].get(), 50)
    check("...and the other two are dark",
          [var.get() for var in console.cbl_vars[1:]], [0, 0])
    headers = [text_of(w) for w in right.winfo_children()
               if "core model" in text_of(w)]
    check("the panel prints his equation",
          headers[0] if headers else "",
          "the core model   T' = T + baseFluc * press + noise(t) - cooling")

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
    # ONE bank at PW5, the other two dark.  His fit's `a` runs 25..125, which is
    # a single laser's worth, so "PW5 on the console" is a = 125 and not 375 --
    # the three-maxed case is its own check below, marked as an extrapolation.
    console.cbl_vars[0].set(125)
    for var in console.cbl_vars[1:]:
        var.set(0)
    console.on_power()
    check("his `a` is the power value", console.core.power, 125.0)
    console.step_once()
    values = screen(right)
    check("row 3 held", values["row  (ACTIVE/PASSIVE index)"], "3")
    check("PW5 on one bank is his a = 125, his literals",
          values["baseFluc  active + passive"],
          gui.shown(his_base_fluc(3, 5)))

    # "off" is ours, not the spec's: the fit covers levels 1..5 and there is no
    # level 0 in it, so zero CBL is defined as adding nothing rather than by
    # extrapolating the line down to a = 0 (which would still add row 1's
    # intercept).  The tremor scales with the level, so it goes quiet too, and
    # the reading holds exactly still.
    print("\n-- off (level 0, not in the fit) --")
    for var in console.cbl_vars:
        var.set(0)
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

    # --- the three laser banks ----------------------------------------------
    # The game has three combustion lasers and each carries its own PW1..PW5, so
    # the panel has three rows of radios; what the fit eats is their SUM.  Held
    # on row 3, where `a` has the largest coefficient (6.8), so a check made here
    # fails loudly if the sum is ever read as only one bank -- on row 0 `a` does
    # nothing at all and every version of this would pass (CLAUDE.md 0.31 (1)).
    print("\n-- three banks, and their sum is his a --")
    console.reset()
    console.arm_var.set(True)
    console.on_arm()
    console.auto_var.set(False)
    console.on_auto()
    console.core_var.set(3)
    console.on_core_state()
    for index, power in enumerate((75, 25, 0)):
        console.cbl_vars[index].set(power)
    console.on_power()
    check("the three banks hold three different powers", console.core.banks,
          [75.0, 25.0, 0.0])
    check("his `a` is their sum, not any one of them", console.core.power, 100.0)
    console.step_once()
    values = screen(right)
    check("the three banks on screen", values["a1 / a2 / a3  banks"],
          "75 / 25 / 0")
    check("the sum on screen", values["a   total = his a"], "100")
    check("row 3 at a = 100 is his level 4, his literals",
          values["baseFluc  active + passive"], gui.shown(his_base_fluc(3, 4)))

    # a = 375 is past the end of the fit.  Said out loud in the run, not only in
    # the source comment: the line extends exactly, and that the reactor stays
    # linear out there is the fit's assumption rather than a measurement.
    for var in console.cbl_vars:
        var.set(125)
    console.on_power()
    check("three maxed banks reach a = 375", console.core.power, 375.0)
    check("...which is his own line, three times past the fitted range",
          gui.fluctuation(3, 375.0), his_base_fluc(3, 15))
    print("     (the fit covers a = 25..125, i.e. ONE bank; a = 375 is an "
          "extrapolation -- QUESTIONS.md)")

    # --- the three coolant pumps --------------------------------------------
    # The third of the game's three control means.  The CONSTANT is measured
    # (see his_cooling); what is checked here is where it SITS, because that
    # part is a choice and not a reading -- CLAUDE.md 0.31's question, asked of
    # a spec that arrived after the model it lands in:
    #   * it is its own term rather than so many CBL levels' worth of negative
    #     `a`, so it works with the lasers dark (the shipped log has 84 records
    #     at CBL sum 0 with the pumps running) and it is not a per-row quantity;
    #   * it is outside `pMultiplier`, because no source puts a pressure factor
    #     on it and multiplying would be inventing one;
    #   * the stall still out-ranks it, so his -586 stays exactly -586.
    # Every one of those three is driven and then broken on purpose in
    # core_model_mutants.py -- a check that only ever sees the pumps at zero
    # would pass with the whole feature missing.
    print("\n-- coolant: three pumps, each 0..3, -%g a tick --"
          % gui.COOLANT_PER_LEVEL)
    console.reset()
    console.arm_var.set(True)
    console.on_arm()
    console.auto_var.set(False)
    console.on_auto()
    console.core_var.set(3)
    console.on_core_state()
    for var in console.cbl_vars:
        var.set(0)
    console.on_power()
    check("the pumps start dark, like the game's",
          [var.get() for var in console.pump_vars], [0, 0, 0])
    check("...so nothing is being cooled", console.core.cooling, 0.0)

    for index, level in enumerate((3, 0, 1)):
        console.pump_vars[index].set(level)
    console.on_coolant()
    check("three pumps hold three different levels", console.core.pumps, [3, 0, 1])
    check("the cooling is 120 a level, summed over three",
          console.core.cooling, his_cooling([3, 0, 1]))
    # The lasers are dark for the tick below, so his line adds nothing and the
    # tremor is scaled by a level of zero: what is left is the pumps alone.
    # This is the check that says the "off is ours" rule stops at the lasers.
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("the pumps on screen", values["p1 / p2 / p3  pumps"], "3 / 0 / 1")
    # Addressed by prefix, not by its full text: the label embeds the constant
    # that is under test, so a mutant of that constant has to fail a CHECK and
    # not raise a KeyError inside this file (readout() says the same thing
    # about the stallout label, and that is where this was learned).
    check("the cooling on screen", readout(values, "cooling"),
          gui.shown(his_cooling([3, 0, 1])))
    check("a dark laser bank does not silence the pumps",
          float(values["T'  next tick's temperature"]) - temp,
          -his_cooling([3, 0, 1]))

    # The pumps and the lasers together, on a row where `a` has a real
    # coefficient, against his equation plus the measured cooling.  This is the
    # only check here that reads BOTH controls at once, so it is the one that
    # would catch the cooling being routed through his line (which would make
    # the total depend on the row and on `a` in a way no source describes).
    console.pump_vars[0].set(2)
    console.pump_vars[1].set(3)
    console.pump_vars[2].set(0)
    console.on_coolant()
    console.cbl_vars[0].set(75)
    console.cbl_vars[1].set(25)
    console.cbl_vars[2].set(0)
    console.on_power()
    temp = console.sim.Temperature
    pressure = console.sim.Pressure
    console.step_once()
    values = screen(right)
    # `core.t` AFTER the step: the model accumulates it before it computes, so
    # that is the x the tremor was taken at.  Read before the step it would be
    # one period stale, which is the kind of off-by-a-tick that only shows up
    # as a small disagreement in the last digit.  Compared as SCREENED values
    # (`shown` on both sides), because the readout is a whole number and
    # comparing a rounded reading against an unrounded sum tests the rounding.
    want = (his_temperature(temp, 3, 4, pressure, console.core.t)
            - his_cooling([2, 3, 0]))
    check("heat and cooling in one tick, his literals",
          values["T'  next tick's temperature"], gui.shown(want))

    # `pMultiplier` is a property of the pressure, and the cooling is not: from
    # 20000 PSI the multiplier is 2, and a check made at 1 could not tell the
    # two apart.  This one can -- it is the only place the difference is
    # visible, so it is the check a "cooling inside the multiplier" mutant has
    # to redden.
    console.sim.Pressure = 20000.0
    for var in console.cbl_vars:
        var.set(0)
    console.on_power()
    for var in console.pump_vars:
        var.set(0)
    console.pump_vars[2].set(1)
    console.on_coolant()
    check("the press is doubled up here", gui.press_multiplier(console.sim.Pressure),
          2.0)
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("the press multiplier does not scale the cooling",
          values["T'  next tick's temperature"],
          gui.shown(temp - his_cooling([0, 0, 1])))

    # The stall out-ranks the pumps, exactly as it out-ranks the lasers: his
    # -586 is a rate for a crumpled core and it does not become -586 minus 1080
    # because three pumps are running.  Driven at the gate's own boundary
    # rather than below it, so the same tick also says the gate is still the
    # one the stall section below reads.
    console.sim.Pressure = gui.AVB_STALLOUT_PSI
    for var in console.pump_vars:
        var.set(3)
    console.on_coolant()
    check("three pumps at their maximum", console.core.cooling,
          his_cooling([3, 3, 3]))
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("the stall out-ranks the pumps too",
          values["T'  next tick's temperature"],
          gui.shown(temp + gui.STALL_FLUC))
    check("...and the cooling is what the step zeroed, not what the panel says",
          readout(values, "cooling"), "0")
    print("     (maximum coolant is -%g a tick: in THIS console's currency that "
          "is about a third of three maxed banks, where the original's own "
          "ratio would drown them -- his fitted heat line is ~2.6x the "
          "original's 65 a level, and the constant is the measured one rather "
          "than a rescaled one -- QUESTIONS.md)"
          % his_cooling([3, 3, 3]))

    # Put the pumps back before the next section.  Not tidiness: every check
    # below is about the stall, the vent and the rows, and a section that walks
    # off leaving 1080 a tick of cooling running would make them read a
    # different console -- silently, since none of them asks about the pumps.
    for var in console.pump_vars:
        var.set(0)
    console.on_coolant()
    check("...and back off again, so the sections below run the console they "
          "used to", console.core.cooling, 0.0)

    # --- the stall, which is the operator's rule ----------------------------
    # Driven rather than planted: the fans walk the pressure down at 194 a tick
    # and the loop stops when the SCREEN says the chamber is stalled -- the
    # readout is the gate, so the run cannot disagree with the panel about when
    # it got there.
    print("\n-- the stall: his `if pres <= 2200 then fluc = -586` --")
    console.reset()
    console.arm_var.set(True)
    console.on_arm()
    for var in console.cbl_vars:
        var.set(0)
    console.on_power()
    console.fan_var.set(6)
    console.on_fan()
    steps = 0
    while steps < 500:
        console.step_once()
        steps += 1
        if readout(screen(right), "stallout") == "STALLED":
            break
    values = screen(right)
    check("the fans walked the pressure into the stall", steps < 500, True)
    check("...and the panel says so", readout(values, "stallout"), "STALLED")
    check("...with the chamber still above the floor",
          float(values["Pressure"]) > 0, True)

    before = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("the step gated on it", values["stall  this step"], "STALL")
    check("his -586, exactly, with every bank dark",
          values["actualFluc  base x press"], "-586")
    check("...and the temperature moved by exactly that",
          console.sim.Temperature - before, gui.STALL_FLUC)
    check("...which the screen agrees with",
          values["T'  next tick's temperature"],
          gui.shown(console.sim.Temperature))
    check("...and the tile re-checks its own gate",
          gui.stalled(console.core.last_pressure), console.core.last_stall)
    check("...and the pressure it gated on is on the screen",
          values["p   this step started from"],
          gui.shown(console.core.last_pressure))

    # The boundary, which is the spec's `<=` and not Engine.luau:313's `<`.
    # Both spellings are exercised so a future edit to either is a red check and
    # not a rumour; the one PSI between them is measure zero on a float run.
    print("\n-- the gate, at his boundary --")
    check("stalled(2200) -- his `<=`", gui.stalled(2200.0), True)
    check("stalled(2200.1) -- not quite", gui.stalled(2200.1), False)
    check("stalled(0) is still stalled", gui.stalled(0.0), True)

    # --- the Atmosphere Vent Button -----------------------------------------
    # Pressure is PLANTED here, not driven, because the console has no pressure
    # control -- the operator's own way down is the fans, and that path is
    # exercised above.  What is under test below is the button's arithmetic and
    # its clock, and both are about a single press.
    print("\n-- AVB: -3300, once, then 15 ticks --")
    console.reset()
    console.arm_var.set(True)
    console.on_arm()
    for var in console.cbl_vars:
        var.set(0)
    console.on_power()
    console.sim.Pressure = 5016.0
    console.on_vent()
    values = screen(right)
    check("the press took the wiki's 3300",
          values["vent  last drop (PSI)"], "3300")
    check("...off the pressure that was on the screen", values["Pressure"], "1716")
    check("the cooldown is the wiki's 15 ticks",
          values["vent  cooldown left (ticks)"], "15")
    check("the button is out of service", str(console.vent_button.cget("state")),
          "disabled")
    check("...and says WHY, not just grey", console.vent_text.get(), "cooldown 15")

    # A press is an EVENT.  If the drop were a term in `terms()` the temperature
    # would fall 3300 a tick for as long as the button was held, which is a
    # different device -- and "nothing happened" is what that looks like from
    # one reading, so the clock and the pressure are both read.
    print("\n-- the vent is a one-shot, not a per-tick term --")
    held = console.sim.Pressure
    console.on_vent()
    check("a second press is refused", "AVB refused" in log_text(console), True)
    check("...and it moved nothing", console.sim.Pressure, held)
    check("...and it did not restart the clock", console.sim.vent_ticks, 15)

    print("\n-- the cooldown runs on the console's own tick --")
    for n in range(1, 16):
        console.step_once()
        values = screen(right)
        check("cooldown with %2d tick(s) to go" % (15 - n),
              values["vent  cooldown left (ticks)"], str(15 - n))
    check("...and the button is back", str(console.vent_button.cget("state")),
          "normal")
    check("...and says so", console.vent_text.get(), "ready")

    # The wiki's third number is not a fourth rule: 5500 is exactly
    # 2200 + 3300, the highest pressure one press can still stall from.  Both
    # sides of it are pressed, so the derivation is a reading and not a claim.
    print("\n-- the wiki's 5500 is the derivation 2200 + 3300 --")
    console.reset()
    console.sim.Pressure = gui.AVB_NO_COOL_ABOVE          # 5500
    console.on_vent()
    values = screen(right)
    check("a press at 5500 lands exactly on the floor", values["Pressure"], "2200")
    check("...and that IS a stall", readout(values, "stallout"), "STALLED")
    console.reset()
    console.sim.Pressure = gui.AVB_NO_COOL_ABOVE + 1.0    # 5501
    console.on_vent()
    values = screen(right)
    check("a press one PSI higher does not", values["Pressure"], "2201")
    check("...and is not a stall", readout(values, "stallout"), "no")

    # From below the drop, the number the caller gets back is what actually
    # moved -- otherwise the log would claim 3300 the chamber never felt.
    print("\n-- the drop is clamped, and what is reported is what moved --")
    console.reset()
    console.sim.Pressure = 1000.0
    console.on_vent()
    values = screen(right)
    check("from 1000 the drop reported is the 1000 there was",
          values["vent  last drop (PSI)"], "1000")
    check("...and the pressure is floored at 0", values["Pressure"], "0")

    root.destroy()
    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    for name in FAILURES:
        print("  FAILED: %s" % name)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
