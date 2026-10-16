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

The spec is the 2026-10-16 revision -- the message headed "Correction", a
per-tick STEP:

    a_avg          = ((c_1 + c_2 + c_3) / 3) * 25
    coolant_avg    = (p_1 + p_2 + p_3) / 3      <- moved 3 times; it is back
    coolant_effect = coolant_avg * 120                       (see below)
    s              = {T < 5600: 0, T < 17500: 1, T < 29500: 2, 3}
    base_heat      = [0, 6.86*a_avg + 65.5, 7.24*a_avg + 37, 6.8*a_avg + 534][s+1]
                     + [-455.7, -19.2, 0, 0][s+1]
    p_mult         = {P <= 11500: 1, P <= 27000: 2, 4}
    noise          = 15*(a_avg/25)*sin(t/1.5) + 10*(a_avg/25)*sin(t/0.7)
                     + 5*(a_avg/25)*sin(t/0.3)
    dT             = {P <= 2200: -586, base_heat*p_mult - coolant_effect + noise}
    T'             = T + dT

with ONE TERM OF IT MOVING THREE TIMES.  The message wrote `coolant_avg = (p_1 +
p_2 + p_3) / 3` and multiplied that; the next message said not to average the
cooling; the one after that said to average it after all.  So the line above is
his first and his third word on the unit, and the middle one -- `sum * 120`, no
division at all -- is kept as a mutant rather than as a live check, because a
spec visited three times has to keep a tooth on the reading it was reversed OUT
of as well as on the one it landed on (CLAUDE.md 0.34).  Before any of those,
the sum was this console's own reading of the three sources rather than a word
of his; that is what made it look like the safer default, and it is why the
sources are still quoted at length under `his_cooling` below.  What did NOT move
is the banks': they were averaged in the same message as the pumps and have
stayed averaged through all of it, because
their mean is pinned by his fitted band (`a = 25..125`) and the pumps have no
such band.  That asymmetry is the whole reason the two halves of one message
could land differently, and it is why the checker holds them to different
things rather than to one rule about "the mean".

His own worked example -- the numbers the message carries, c = 5/3/1,
p = 2/2/2, T = 12000, P = 8000, t = 1 -- is driven through the panel in its own
section below, so the spec is checked as an instance and not only term by term.
Its tail (`coolant_effect = 240`, `dT = 375.465...`, `T' = 12375`) belongs to
the averaged reading, which is the one in force again, so the example is driven
as he wrote it and nothing is annotated as a discrepancy.  The sum's own tail
for those same pumps -- 720, -104.53, 11895 -- stays in the section as a print,
so the reading that was in force for part of the day is recorded without being
asserted as a live number (CLAUDE.md 0.31 (1): an identity that cannot go red is
a print, not a check).

That supersedes the 2026-10-14 revision (`T' = T + (active[row] +
passive[row]) * pMultiplier + noise(t) + cooling`), which in turn replaced the
2026-10-13 closed form `T0 + (rate + noise(x)) * x`.  Three things moved and
each is checked by name here: the banks are AVERAGED and not summed, the stall
is now the whole of `dT` (no heat, no pump term, no tremor) where the earlier
reading had it set the rate with the tremor still riding on the reading, and the
pumps are averaged too -- which is the one of the three whose direction changed
after it first landed.

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


def check_close(name, got, want, tol):
    """The same, for a value two spellings of one formula need not agree on in
    the last bits -- used ONCE in this file, and the reason is measured.

    `gui.noise` sums its three sines with `sum()`, and CPython 3.12+ makes
    `sum()` a COMPENSATED sum for floats: it lands a few ulps nearer the true
    value than his own left-to-right `a + b + c` does.  The gap at a_avg = 75,
    t = 1 is 7.105e-15, twelve orders below the smallest thing the check has to
    catch (swapping two amplitudes moves that reading 2.4 degrees).  Everywhere
    else the two spellings here are bit-identical and `check` is the right
    instrument -- a tolerance is a hole, and it is only worth opening where the
    gap is measurable, explainable and named.
    """
    CHECKS[0] += 1
    gap = abs(got - want)
    if gap <= tol:
        print("ok   %-44s within %g (gap %g)" % (name, tol, gap))
        return True
    print("FAIL %-44s got %r, wanted %r (gap %g > %g)"
          % (name, got, want, gap, tol))
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
# translation.  As of the 2026-10-16 correction his rule spells that first slot
# out (`T < 5600: 0`), and 5600 is the number this file's sibling already carried
# from `Config.Sim.State1` -- two spellings of one threshold are checked against
# each other rather than one of them being restated here.
#
# `a` is his `a_avg` everywhere below, so `his_a_avg` is what a caller who has
# three bank LEVELS reaches for, and what a caller who already has an `a` passes
# straight through.

def his_a_avg(c1, c2, c3):
    """His `a_avg = ((c_1 + c_2 + c_3) / 3) * 25`.

    The arguments are LEVELS (0..5), because that is what his message divides;
    `x 25` is what turns the mean level into the `a` his fit was taken in.  The
    division is spelled on the integers, as he wrote it, so this is his
    arithmetic and not a rearrangement of it that happens to agree.
    """
    return ((c1 + c2 + c3) / 3) * 25


def his_active(row, a):
    return [0, 6.86 * a + 65.5, 7.24 * a + 37, 6.8 * a + 534][row]


def his_passive(row):
    return [-455.7, -19.2, 0, 0][row]


def his_base_fluc(row, a):
    return his_active(row, a) + his_passive(row)


def his_press(pressure):
    if pressure <= 11500:
        return 1
    if pressure <= 27000:
        return 2
    return 4


def his_noise(x, a):
    """His `noise`, with the amplitude written as he wrote it: `a / 25` rather
    than a level, so the scaling is checked as a division and not as a stored
    multiplier."""
    return (15 * (a / 25) * math.sin(x / 1.5)
            + 10 * (a / 25) * math.sin(x / 0.7)
            + 5 * (a / 25) * math.sin(x / 0.3))


def his_dT(row, a, pressure, x, cooling):
    """His `dT`, piecewise, spelled the way the correction spells it.

    The stall branch REPLACES the whole expression -- no heat term, no pump
    term, no tremor -- which is the reading that changed on 2026-10-16 and the
    reason this is a function of the five arguments rather than a sum the caller
    assembles.  QUESTIONS.md R12 has the other reading (the -586 as the rate,
    with the noise still added on top).
    """
    if pressure <= 2200:
        return -586
    return his_base_fluc(row, a) * his_press(pressure) - cooling + his_noise(x, a)


def his_temperature(temp, row, a, pressure, x, cooling=0.0):
    return temp + his_dT(row, a, pressure, x, cooling)


def his_cooling(levels):
    """What the pumps take off a tick: his `coolant_avg * 120`, added OUTSIDE
    his line and outside `pMultiplier`.

    The AVERAGE is his own spelling, and this is the term that has moved three
    times in one day: the message that introduced the pumps wrote it with no
    division, the "Correction" message averaged it, the next took the average
    back off the pumps alone, and the one after that -- Phase 139 -- put it
    back.  What is transcribed here is the FIRST and the LAST of those, which
    are the same line; the two middle readings are the ones the mutants below
    are aimed at.  gui.py's constants block is where the whole list lives.

    The 120 is untouched through all four, and it is spelled from the three
    sources rather than from `gui.COOLANT_PER_LEVEL`, so this is not a
    tautology: the original's own line in `Data/TRGWeb.luau`
    (`- (coolant_pump1_power + coolant_pump2_power + coolant_pump3_power)*120`),
    our remake's `Config.Sim.PumpCooling`, and the shipped log's exact identity
    `predDT*5 == 65*sum(cbl.level) - 120*sum(coolant.levels)` over all of its
    477 records (`_tools/coolant_from_log.py` prints it).  All three spell the
    SUM while this line spells the mean, and that is the divergence
    QUESTIONS.md R11 files rather than folds away: same constant, different
    unit, exactly a factor of three at every position.
    """
    coolant_avg = sum(levels) / 3.0
    return coolant_avg * 120.0


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
    # The correction spells row 0's threshold out, and 5600 is a number this
    # project already had from two other directions (Config.Sim.State1 and
    # Engine.luau:320's `T >= 5600 and 1 or 0`).  Checked as a reading rather
    # than restated in gui.py, so a future edit to either spelling is red here.
    check("the spec's `T < 5600` is the STATE_MIN this file already had",
          gui.CORE_ROW_1_AT, gui.STATE_MIN)

    # --- his two lists, against the model's one table -----------------------
    print("\n-- active + passive, his literals --")
    for row in (0, 1, 2, 3):
        for level in (1, 3, 5):
            name = "fluctuation(row %d, a=%d)" % (row, level * 25)
            check(name, gui.fluctuation(row, level * 25.0),
                  his_base_fluc(row, level * 25.0))
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
    # ...which is a_avg = 50/3 since the correction, NOT 50 and NOT 150.  The
    # console's opening POSITION is unchanged; what the spec changed is what that
    # position means, so this is checked here rather than papered over by moving
    # the default (moving a control to defend a reading is the wrong direction).
    check("one bank at PW2 is his a_avg = 50/3, not 50",
          console.core.power, his_a_avg(2, 0, 0))
    check("...and it is not the sum either", console.core.power == 50.0, False)
    # The pumps' own opening position, checked HERE because here it is still the
    # widget's default and nowhere later is: `Console.reset()` starts a run, it
    # does not restore a control position, so it leaves the radios exactly where
    # the previous section left them (the coolant section below sets them dark
    # for itself rather than assuming this).
    check("the pumps start dark, like the game's",
          [var.get() for var in console.pump_vars], [0, 0, 0])
    check("...so nothing is being cooled", console.core.cooling, 0.0)
    headers = [text_of(w) for w in right.winfo_children()
               if "core model" in text_of(w)]
    check("the panel prints his equation", headers[0] if headers else "",
          "the core model   dT = base_heat * p_mult - coolant_effect + noise"
          "   (or exactly -586, stalled)")

    # All three banks on PW2 before the regression below.  ONE bank at PW2 is
    # a_avg = 16.67 now, and the point of the three ticks below is his equation at
    # a known `a` -- three at PW2 is a_avg = 50, which is the `a` this section was
    # written at and the level his fit's own PW2 is.  The opening position is
    # checked just above, where it belongs.
    for var in console.cbl_vars:
        var.set(50)
    console.on_power()
    check("three banks at PW2 are his a_avg = 50", console.core.power,
          his_a_avg(2, 2, 2))

    # One tick at a time, against his equation with his literals.  The tick
    # period is 1.0 s, so at the Nth tick t = N and a = 50 (PW2 on all three).
    deltas = []
    for n in (1, 2, 3):
        pressure = console.sim.Pressure
        temp = console.sim.Temperature
        console.step_once()
        values = screen(right)
        want = his_temperature(temp, 1, 50.0, pressure, float(n))
        deltas.append(float(values["T'  next tick's temperature"]) - temp)
        check("t after tick %d" % n, values["t   elapsed since armed (s)"], str(n))
        check("row at tick %d" % n, values["row  (ACTIVE/PASSIVE index)"], "1")
        check("baseFluc at tick %d" % n, values["baseFluc  active + passive"], "389")
        check("press x at tick %d" % n, values["press x   pMultiplier"], "1")
        check("actualFluc at tick %d" % n, values["actualFluc  base x press"], "389")
        check("noise(%d)" % n, values["noise(t)"],
              gui.shown(his_noise(float(n), 50.0)))
        check("T' at tick %d against his equation" % n,
              values["T'  next tick's temperature"], gui.shown(want))

    # The revision, in one line: the noise is ADDED, so its amplitude is what it
    # says it is (+-30 at a = 50) and a tick moves by about baseFluc.  In the old
    # closed form the same three sines were inside the multiplication, so the
    # same t gave a wobble of 30 * t and the step was 389 + 30t.
    print("\n-- the noise is a tremor on the reading, not on the slope --")
    check("noise(1) is tens, not tens x t", abs(his_noise(1.0, 50.0)) < 100, True)
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
    # The tight one: row 1's base is 389.3 and row 2's is 399.0 at a = 50, so
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
    # amplitude, a hair over 100 at a = 50, whatever t is.  t here is in the
    # thirties.
    check("a late tick still moves by base x press",
          abs(tail[2] - his_base_fluc(tail[0], 50.0) * tail[1]) < 150, True)

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
    check("row 0 at a = 50, his equation",
          values["T'  next tick's temperature"],
          gui.shown(his_temperature(temp, 0, 50.0, pressure, console.core.t)))
    check("negative and moving down",
          float(values["T'  next tick's temperature"]) < temp, True)

    # --- CBL power ----------------------------------------------------------
    # `a = level * 25`, which is the number the radios carry, so PW5 is level 5.
    # Row 3 held by hand for the on-screen check: at row 0 the level has no
    # effect at all (active[0] is 0), so a check made from the row the console
    # happens to be on would pass without ever looking at `a`.
    print("\n-- CBL power is his `a` --")
    for level in (1, 2, 5):
        check("fluctuation(row 3, a=%d)" % (level * 25),
              gui.fluctuation(3, level * 25.0), his_base_fluc(3, level * 25.0))
    console.auto_var.set(False)
    console.on_auto()
    console.core_var.set(3)
    console.on_core_state()
    # ONE bank at PW5 and the other two dark: since the correction that is a
    # THIRD of the bank's own value, so a single laser at its maximum is
    # a_avg = 41.67 and the top of his fit needs all three.  That is the price
    # the correction paid, said out loud on the panel rather than hidden.
    console.cbl_vars[0].set(125)
    for var in console.cbl_vars[1:]:
        var.set(0)
    console.on_power()
    check("one bank at PW5 is his a_avg, a third of it",
          console.core.power, his_a_avg(5, 0, 0))
    check("...and it is NOT the bank's own value, as it was before",
          console.core.power == 125.0, False)
    console.step_once()
    values = screen(right)
    check("row 3 held", values["row  (ACTIVE/PASSIVE index)"], "3")
    check("one bank at PW5, his literals",
          values["baseFluc  active + passive"],
          gui.shown(his_base_fluc(3, his_a_avg(5, 0, 0))))

    # All three at PW5: the one control position that reaches the top of his
    # fit, where before the correction one bank did.  The ceiling moved with the
    # unit, and this is where the panel shows it.
    for var in console.cbl_vars:
        var.set(125)
    console.on_power()
    check("all three at PW5 reach the top of his fit, a = 125",
          console.core.power, his_a_avg(5, 5, 5))
    console.step_once()
    values = screen(right)
    check("...and row 3 there is his own line at a = 125",
          values["baseFluc  active + passive"],
          gui.shown(his_base_fluc(3, 125.0)))

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
    # the panel has three rows of radios; what the fit eats is their MEAN.  Held
    # on row 3, where `a` has the largest coefficient (6.8), so a check made here
    # fails loudly if the mean is ever read as only one bank or as the sum -- on
    # row 0 `a` does nothing at all and every version of this would pass
    # (CLAUDE.md 0.31 (1)).
    #
    # PW5 / PW2 / dark on the three banks: a_avg = ((5 + 2 + 0) / 3) * 25 = 58.33.
    # Deliberately NOT his worked example's c = 5/3/1, and for a measured reason:
    # the mean of 5/3/1 is exactly 3, so a_avg = 75 IS the middle bank's own value
    # and a check written there cannot tell "the mean of the three" from "bank 2"
    # -- which is the one reading this section exists to rule out.  An asymmetric
    # triple is the only kind that can: 58.33 is nobody's bank value, so a check
    # that read one bank (or their sum, 175) goes red.  His own example is checked
    # in full, at a_avg = 75, two sections down.
    print("\n-- three banks, and their mean is his a_avg --")
    console.reset()
    console.arm_var.set(True)
    console.on_arm()
    console.auto_var.set(False)
    console.on_auto()
    console.core_var.set(3)
    console.on_core_state()
    for index, power in enumerate((125, 50, 0)):
        console.cbl_vars[index].set(power)
    console.on_power()
    check("the three banks hold three different powers", console.core.banks,
          [125.0, 50.0, 0.0])
    check("his `a` is their mean, not their sum", console.core.power,
          his_a_avg(5, 2, 0))
    check("...and it is not the sum", console.core.power == 175.0, False)
    check("...nor any one bank", console.core.power in (125.0, 50.0, 0.0),
          False)
    console.step_once()
    values = screen(right)
    check("the three banks on screen", values["a1 / a2 / a3  banks"],
          "125 / 50 / 0")
    check("the mean on screen", values["a_avg  his a, mean of the 3"], "58")
    check("row 3 at a_avg = 58.33, his literals",
          values["baseFluc  active + passive"],
          gui.shown(his_base_fluc(3, his_a_avg(5, 2, 0))))

    # The ceiling, checked rather than asserted in a comment.  Before the
    # correction three maxed banks reached a = 375 -- three times past the end of
    # his fit, where the reactor's behaviour was the line's assumption and not a
    # measurement (QUESTIONS.md R9 (2)).  Under the mean the ceiling is 125, the
    # top of the fitted band, and the extrapolation is gone by construction.
    check("no control position can exceed the fitted band's top, a = 125",
          gui.fluctuation(3, his_a_avg(5, 5, 5)), his_base_fluc(3, 125.0))
    print("     (the fit covers a = 25..125; under the sum, three maxed banks "
          "read 375 -- three times past the end of it.  The correction retires "
          "that reading -- QUESTIONS.md R9 (2))")

    # --- his own worked example ---------------------------------------------
    # The message that carried the correction ends with a worked instance:
    # c = 5/3/1, p = 2/2/2, T = 12000, P = 8000, t = 1.  Checked as an instance
    # and not only term by term, because every term-by-term check above passes at
    # any `a` -- this is the one that says the WHOLE expression, assembled in the
    # panel's own order, lands where he says it lands.
    #
    # Pressure and temperature are PLANTED (the console has no pressure control
    # and T is the slider's job while unarmed), which is exactly the licence the
    # AVB section below takes: the run is one tick long, so nothing has to be
    # reached by driving.
    print("\n-- his own worked example: T = 12000, P = 8000, t = 1 --")
    console.arm_var.set(False)
    console.on_arm()
    console.reset()
    console.auto_var.set(True)
    console.on_auto()
    for index, power in enumerate((125, 75, 25)):
        console.cbl_vars[index].set(power)
    console.on_power()
    for index, level in enumerate((2, 2, 2)):
        console.pump_vars[index].set(level)
    console.on_coolant()
    console.arm_var.set(True)
    console.on_arm()
    console.sim.Temperature = 12000.0
    console.sim.Pressure = 8000.0
    console.step_once()
    values = screen(right)
    check("his example: t = 1 after one tick",
          values["t   elapsed since armed (s)"], "1")
    check("his example: row 1 at T = 12000",
          values["row  (ACTIVE/PASSIVE index)"], "1")
    check("his example: a_avg = ((5+3+1)/3)*25 = 75",
          console.core.power, his_a_avg(5, 3, 1))
    check("his example: base_heat on screen", values["baseFluc  active + passive"],
          "561")
    check("...and the model's own number is his 6.86*75 + 65.5 - 19.2",
          gui.fluctuation(1, his_a_avg(5, 3, 1)), 560.8)
    check("...and my transcription of that line agrees to the last bit",
          his_base_fluc(1, his_a_avg(5, 3, 1)), 560.8)
    check("his example: p_mult = 1 at P = 8000",
          values["press x   pMultiplier"], "1")
    # His instance says coolant_effect = 240 here, and it is the live reading
    # again: the message that carried the example averaged the three pumps, the
    # next took that division off, and the one after that put it back, so his
    # own worked example and the console are on the same reading for the second
    # time.  The other one is printed immediately below rather than dropped --
    # and printed rather than CHECKED, because with the mean in force there is
    # nothing left that can fail on it (CLAUDE.md 0.31 (1)).
    check("his example: coolant_effect = 240 at p = 2/2/2",
          readout(values, "cooling"), "240")
    check("...and the model's own number is his (2+2+2)/3 * 120",
          console.core.cooling, 240.0)
    print("     (the other reading of these same pumps -- his second word, and "
          "the one in force for part of the day -- takes off 720, and its tail "
          "is dT = -104.53 and T' = 11895.  Both numbers are his own "
          "arithmetic; which one the panel shows is his choice of unit and it "
          "has flipped three times.)")
    check("his example: noise(1) = 54.665...", values["noise(t)"], "55")
    # Closed at the SCREEN layer, which is where the console makes its promise,
    # plus one bounded comparison underneath it: the two spellings of his three
    # sines are NOT bit-identical, and the reason is not the model.  See
    # check_close -- CPython's `sum()` is compensated for floats, so the panel's
    # own spelling lands 7.1e-15 away from his left-to-right `a + b + c`.
    check("...and the model's own number is his three sines at a_avg = 75",
          gui.shown(gui.noise(1.0, his_a_avg(5, 3, 1))), "55")
    check_close("...and the two spellings agree to 1e-12, not to the last bit",
                gui.noise(1.0, his_a_avg(5, 3, 1)),
                his_noise(1.0, his_a_avg(5, 3, 1)), 1e-12)
    check("...and my transcription of those sines is the literal he wrote",
          his_noise(1.0, his_a_avg(5, 3, 1)), 54.665213986169604)
    check("his example: dT = 561 - 240 + 54.665... = 375.465..., shown as 375",
          gui.shown(console.sim.Temperature - 12000.0), "375")
    check("his example: T' = T + dT", values["T'  next tick's temperature"],
          "12375")
    check("...and his formula, assembled independently, says the same",
          values["T'  next tick's temperature"],
          gui.shown(his_temperature(12000.0, 1, his_a_avg(5, 3, 1), 8000.0, 1.0,
                                    his_cooling([2, 2, 2]))))

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
    # The pumps are SET dark here, not assumed dark: `Console.reset()` starts a
    # run, it does not restore a control position, and the worked-example section
    # above left the radios at 2/2/2.  (The widget's own default is checked up in
    # the opening section, where nothing has moved it yet -- this line used to
    # live here, and it was passing for the wrong reason until 2026-10-16.)
    for var in console.pump_vars:
        var.set(0)
    console.on_coolant()
    check("the pumps dark, so nothing is being cooled", console.core.cooling, 0.0)

    for index, level in enumerate((3, 0, 1)):
        console.pump_vars[index].set(level)
    console.on_coolant()
    check("three pumps hold three different levels", console.core.pumps, [3, 0, 1])
    check("the cooling is 120 a MEAN level, averaged over three",
          console.core.cooling, his_cooling([3, 0, 1]))
    check("...and that is not the sum of the three",
          console.core.cooling == 120.0 * sum([3, 0, 1]), False)
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
    # Both sides SCREENED: the average puts a division in the number here, so the
    # reading may not be a whole one -- for p = 3/0/1 the mean is 4/3 of a level
    # and the cooling is 160 exactly, but 2/2/1 gives 200 and 1/0/0 gives 40 with
    # the same shape, and the choice of example is not what decides whether the
    # division is there.  This is the same "compare at one layer" rule the T'
    # checks below spell out; it was kept through the day the sum was in force
    # precisely so that it could not be forgotten when the mean came back.
    check("a dark laser bank does not silence the pumps",
          values["T'  next tick's temperature"],
          gui.shown(temp - his_cooling([3, 0, 1])))

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
    want = his_temperature(temp, 3, his_a_avg(3, 1, 0), pressure, console.core.t,
                           his_cooling([2, 3, 0]))
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
    # -586 is a rate for a crumpled core and it does not become -586 minus 360
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
    # NOT a "the tremor is zero here" check: the banks are dark for this tick, so
    # the tremor would be zero whether the stall zeroed it or not -- a check that
    # cannot fail for the right reason (CLAUDE.md 0.31 (1)).  The lit-banks case
    # is driven down in the stall section, where the two spellings of R12 differ.
    print("     (maximum coolant is -%g a tick: in THIS console's currency that "
          "is about a third of three maxed banks, where the original's own "
          "ratio would drown them -- his fitted heat line is ~2.6x the "
          "original's 65 a level, and the constant is the measured one rather "
          "than a rescaled one -- QUESTIONS.md R11)"
          % his_cooling([3, 3, 3]))

    # Put the pumps back before the next section.  Not tidiness: every check
    # below is about the stall, the vent and the rows, and a section that walks
    # off leaving 360 a tick of cooling running would make them read a
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

    # The reading that CHANGED on 2026-10-16, driven where the two spellings
    # actually differ.  With every bank dark the tremor is zero by its own
    # scaling, so the tick above cannot tell his piecewise `dT` (the stall is the
    # whole expression) from the earlier reading (the -586 as the RATE, with
    # noise still added on top -- QUESTIONS.md R12).  With all three banks lit
    # they part company: his says -586 and nothing else, the other says
    # -586 + noise(t), tens of degrees away.
    console.cbl_vars[0].set(125)
    console.cbl_vars[1].set(125)
    console.cbl_vars[2].set(125)
    console.on_power()
    check("...and for this tick a_avg is at the top of the fit",
          console.core.power, his_a_avg(5, 5, 5))
    tremor_now = his_noise(console.core.t, his_a_avg(5, 5, 5))
    print("     (the tremor the OTHER reading would have added here: %r)"
          % tremor_now)
    before = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("a stalled tick with every bank LIT moves by exactly -586",
          console.sim.Temperature - before, gui.STALL_FLUC)
    check("...so his -586 is the whole of dT, not the rate under a tremor",
          values["T'  next tick's temperature"],
          gui.shown(before + gui.STALL_FLUC))
    check("...and the noise tile shows the zero the step used",
          values["noise(t)"], "0")
    check("...and the bar says STALL", values["stall  this step"], "STALL")
    check("...with his own branch on it",
          "STALL %g" % gui.STALL_FLUC in console.core_text.get(), True)
    # The non-vacuity guard for the check two lines up: if the tremor happened to
    # be ~0 at this t, the screen's "0" would pass with the old reading too, and
    # the check would be alive but unable to fail (CLAUDE.md 0.31 (1)).  Print
    # the number so the margin is a reading rather than a hope.
    check("...and that zero is the stall's doing, not a coincidence of t",
          abs(tremor_now) > 1.0, True)

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
