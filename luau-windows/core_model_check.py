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

The spec is the 2026-10-16 revision as amended by the wiki's Temperature page
(Phase 148, 2026-10-24), a per-tick STEP:

    a_eff          = 0.756*c_1 + 0.522*c_2 + 0.196*c_3   <- was the mean
    coolant_avg    = (p_1 + p_2 + p_3) / 3      <- moved 3 times; it is back
    coolant_effect = coolant_avg * 120                       (see below)
    s              = {T < 5600: 0, T < 17500: 1, T < 29500: 2, 3}
    pure_cbl       = {a_eff <= 0: 0, 0.0516*a_eff^2 + 1.1*a_eff + 426}
    passive        = [-455.7, -400, -422, -22][s]     (his `[s+1]`, 1-based)
    p_mult         = {P <= 11500: 1, P <= 27000: 2, 4}
    noise          = 15*(a_eff/25)*sin(t/1.5) + 10*(a_eff/25)*sin(t/0.7)
                     + 5*(a_eff/25)*sin(t/0.3)
    dT             = {P <= 2200: -586,
                      pure_cbl*p_mult + passive - coolant_effect + noise}
    T'             = T + dT

THE BANKS ARE NO LONGER AVERAGED -- they are weighted, 0.756 / 0.522 / 0.196
by position.  The wiki says so twice (prose and formula), and the reason the
mean cannot be the reading is that the wiki carries TWO worked examples whose
DIFFERENCE is the evidence: (100,25,25) heats ~580 F/s and (25,25,100) ~220,
while the mean is 50 levels for both and gives one number for both.  The pair
is checked below, not either example alone -- the mean reproduces the SECOND
example to within ~10 F, so a single-example check would pass on the wrong
formula (CLAUDE.md 0.31 (1), the vacuous pass, in its arithmetic form).

Two tensions in the same page are carried rather than smoothed:

  * its PROSE percentages (51.3 / 35.4 / 13.3) sum to 1.0, its COEFFICIENTS
    (0.756 / 0.522 / 0.196) sum to 1.474.  Normalising the coefficients to
    percentages and using them gives 303.7 F on the first example, not 580 --
    so the coefficients are the formula and the percentages are prose about
    their ORDER.  A falsification check pins that.
  * a_eff at all three PW5 is 184.25, past the 25..125 band the old fit was
    taken in.  Carried, not clamped, and printed as such.

THE HEAT IS NOT ONE LINE PER ROW ANY MORE.  It was `base_heat = active[row] +
passive[row]` -- four lines in `a`, `[0, 6.86a + 65.5, 7.24a + 37, 6.8a + 534]`
-- and this spec replaces both tables with ONE quadratic that does not know what
row it is in, plus a per-row constant.  Three things follow from the shape and
each is a live check below rather than a note:

  * a row change alters the OFFSET only.  Under the old tables it altered the
    slope of the heat as well, which is why the row-3 section below had to hold
    a row by hand to make a level visible; the checks that relied on that are
    not merely renumbered, they are about a different thing now.
  * the passive term is OUTSIDE the lasers' off rule.  `pure_cbl(0)` is 0 and
    `passive[row]` is not, so a console with every bank dark cools at its row's
    rate -- row 1 falls 400 a tick where it used to hold exactly still.  This is
    the one behavioural change in the spec, and the section that had asserted
    "off holds the reading still" now asserts the opposite.
  * `p_mult` multiplies `pure_cbl` alone (his note: "only multiplies the active
    heating"), so it never scales the passive loss and never scales the cooling.

ONE TERM MOVED THREE TIMES (the coolant's unit).  The message before this one
wrote `coolant_avg = (p_1 + p_2 + p_3) / 3` and multiplied that; the next said
not to average the cooling; the one after that said to average it after all;
this spec spells the average again.  So the line above is his first, third and
fourth word on the unit, and the middle one -- `sum * 120`, no division at all
-- is kept as a mutant rather than as a live check, because a spec visited that
many times has to keep a tooth on the reading it was reversed OUT of as well as
on the one it landed on (CLAUDE.md 0.34).  Before any of those, the sum was this
console's own reading of the three sources rather than a word of his; that is
what made it look like the safer default, and it is why the sources are still
quoted at length under `his_cooling` below.  The banks moved once, on
2026-10-24, and they did NOT move to a different aggregate -- they stopped
aggregating: the wiki's weights make the reading positional, so the old
mean/sum question is now a question about a formula that no longer takes
either.  The mean is kept as a MUTANT (it still reproduces one of the wiki's
examples), which is where a superseded reading belongs when it can still
produce a plausible number.

His own worked example -- the numbers the message before this one carried,
c = 5/3/1, p = 2/2/2, T = 12000, P = 8000, t = 1 -- is driven through the panel
in its own section below, so the spec is checked as an instance and not only
term by term.  IT IS DRIVEN WITH THIS SPEC'S HEAT, so its tail belongs to the
new shape and the old tail is a receipt rather than an expectation: the row-1
line plus the pump mean read `coolant 240` and `T' 12375`, and the same inputs
under the quadratic read `passive -400`, `pure_cbl 799`, `dT 213.415...`,
`T' 12213`.  Both are printed (CLAUDE.md 0.31 (1): a number that cannot go red
is a print, not a check), and the retired tail is labelled as retired in place.

This spec supersedes the 2026-10-14 revision (`T' = T + (active[row] +
passive[row]) * pMultiplier + noise(t) + cooling`), which replaced the
2026-10-13 closed form `T0 + (rate + noise(x)) * x`.  Everything the EARLIER
2026-10-16 message moved is still in force and is checked by name below: the
stall is the whole of `dT` (no heat, no pump term, no tremor), and the pumps
are averaged -- the one of the three whose direction changed after it landed.

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
    value than his own left-to-right `a + b + c` does.  The gap at the wiki's
    first example's `a_eff` (93.55), t = 1 is ~7e-15, twelve orders below the
    smallest thing the check has to catch (swapping two amplitudes moves that
    reading 2.4 degrees).  Everywhere
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
# `a` is `a_eff` everywhere below, so `his_a_eff` is what a caller who has three
# bank LEVELS reaches for, and what a caller that already holds an `a` passes
# straight through.

def his_a_eff(c1, c2, c3):
    """The wiki's `a_eff = 0.756 * L1 + 0.522 * L2 + 0.196 * L3`.

    The arguments are LEVELS (0..5), which is what every call site in this file
    and the panel's radio buttons carry; `* 25` inside each term turns a level
    into the `L` the formula takes.  Multiplying the level by 25 first is
    exact in binary (25 is a power-of-two times an integer below 2^53), so this
    is bit-identical to gui.py's `w1 * bank_value`, and the terms are written
    left to right -- not `sum()`, which is compensated (CLAUDE.md 0.33 (1)).

    Not a weighted MEAN: dividing by 1.474 would rescale every reading by two
    thirds, and the wiki's own examples are in the unnormalised units.
    """
    return 0.756 * (c1 * 25) + 0.522 * (c2 * 25) + 0.196 * (c3 * 25)


def his_a_mean(c1, c2, c3):
    """The superseded reading, kept because it can still produce a plausible
    number: the plain mean of the three bank values.

    It is kept as a live spelling and not only as a mutant, because the point
    of the wiki's two examples is precisely that this formula REPRODUCES ONE OF
    THEM -- (25,25,100) comes out 210 against the wiki's ~220 -- and does not
    reproduce the other.  A check that only asserted the first example would go
    green on this function, which is what the pair below exists to prevent.
    """
    return ((c1 + c2 + c3) / 3) * 25


def his_a_percent(c1, c2, c3):
    """The wiki's PROSE percentages applied as shares: 51.3% / 35.4% / 13.3%.

    These sum to 1.0 and the coefficients sum to 1.474, so this is the other
    reading the same page supports -- and it is falsified by the page's own
    first example (63.475 -> ~304 F, not ~580).  A second spelling that a
    reader could arrive at honestly, held here so the falsification is a
    measurement rather than a remark.
    """
    return 0.513 * (c1 * 25) + 0.354 * (c2 * 25) + 0.133 * (c3 * 25)


def his_pure_cbl(a):
    """His `pure_cbl = {a_eff <= 0: 0, 0.0516 * a_eff^2 + 1.1 * a_eff + 426}`.

    The row is not an argument, and that is the point of the function's shape
    rather than a convenience: as of the 2026-10-16 spec the lasers' heat is ONE
    curve for every row, and the row supplies only its constant (`his_passive`).
    A signature that took a row here would let a row-dependent reading of the
    heat pass unnoticed.

    `a ** 2` and not `a * a`, deliberately: the two operations differ in the last
    bit for about 0.2% of inputs (measured), Python's `**` is `pow(a, 2)`, and
    `pow` is what a `^` in the spec's own language compiles to.  Spelling this
    with `*` would make this file a second, slightly different, formula -- the
    same family as `sum()` being a compensated sum, and the reason `check_close`
    exists rather than a blanket tolerance (CLAUDE.md 0.33 (1)).
    """
    if a <= 0:
        return 0
    return 0.0516 * a ** 2 + 1.1 * a + 426


def his_passive(row):
    """His `passive`, 0-based in his own order -- see the note above: his lists
    are 1-based, so the slot he writes `[s+1]` is this `[row]`, and his own
    comment on the numbers fixes which is which: 状态1 = -400 and 状态2 = -422,
    which is `[1]` and `[2]` here and would be `[2]` and `[3]` under a literal
    `[s+1]` read (out of range at the top row, and -422 for his state 1)."""
    return [-455.7, -400, -422, -22][row]


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

    `p_mult` multiplies `his_pure_cbl` ALONE and the passive term is added
    outside the multiplication -- his own note on that line, "only multiplies the
    active heating".  Written as the sum of four terms in his order, so the
    placement is visible here instead of being implied by where a parenthesis
    fell.
    """
    if pressure <= 2200:
        return -586
    return (his_pure_cbl(a) * his_press(pressure)
            + his_passive(row) - cooling + his_noise(x, a))


def his_temperature(temp, row, a, pressure, x, cooling=0.0):
    return temp + his_dT(row, a, pressure, x, cooling)


def his_line(row, a, multiplier):
    """His `pure_cbl * p_mult + passive[s]`: a row's whole contribution to a
    tick, before the tremor and before the pumps.

    Its own function because the shape of this sum is the thing the 2026-10-16
    spec changed, and writing it out in one place is what lets three different
    callers -- the tick regression, the row-change tail, the worked example --
    agree about WHERE `passive` sits instead of each assembling its own sum.
    `p_multiplier` is passed in already evaluated (`his_press(P)`), because the
    callers that compare against a driven run hold the multiplier that tick
    used, and one of them holds the pressure instead.
    """
    return his_pure_cbl(a) * multiplier + his_passive(row)


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


def his_dp(state, temperature, fans):
    """His pressure recurrence:
        p_base[s] + T * p_temp_mult[s] - fans * 60.

    This one is a RESTATEMENT rather than a new arriving model: the same three
    lines are `calculation.luau`'s authoritative chamber-pressure formula with
    the PEA term taken off, and this console has always run them (gui.Sim.tick
    / Sim.terms).  It is written out here because the spec restates it, and a
    restatement nothing reads is how two models quietly fork.

    His `s` is the LATCHED PRESSURE STATE -- `Sim.State`, keyed 1..3 with no
    row 0, latched by an if/elseif chain with no `else` -- and NOT the
    temperature row the heat tables use.  Both are called "state" in this
    project, and the two tables are indexed by different ones.

    The slope is what the temperature is multiplied by HERE (the caller passes
    the temperature the tick ended with); `fans` is the fan count.
    """
    base = {1: 110.0, 2: 350.0, 3: 800.0}[state]
    slope = {1: 0.01, 2: 0.0075, 3: 0.005}[state]
    return base + temperature * slope - fans * 60.0


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

    # --- his quadratic and his passive constants ----------------------------
    # The heat used to be one LINE per row, so the thing to check was a table of
    # four lines; it is now one curve for every row plus a constant that does
    # nothing else, and the two are checked separately because that separation IS
    # the spec.  `a` runs over the levels his fit was taken at (25 is PW1, 125 is
    # PW5) plus the zero his own branch spells out.
    print("\n-- pure_cbl, his literals --")
    for a in (0.0, 25.0, 50.0, 75.0, 100.0, 125.0):
        check("pure_cbl(%g)" % a, gui.pure_cbl(a), his_pure_cbl(a))
    # His curve does not know the row, and that is the claim the old per-row
    # tables made false.  Checked by holding `a` and moving the row: a signature
    # that took a row would show up here as four numbers where one is wanted.
    check("pure_cbl takes no row: one curve for all four",
          [gui.pure_cbl(50.0) for _row in (0, 1, 2, 3)],
          [his_pure_cbl(50.0)] * 4)
    # The `a <= 0` branch and the curve it hides.  Without the branch this is
    # 426 at a = 0 and the console's dark reading would climb; it is also the
    # ONLY reason `passive` can sit outside the gate (gui.pure_cbl says so).
    check("pure_cbl(0) is his zero branch, not his intercept",
          gui.pure_cbl(0.0), 0.0)
    check("...and the curve it hides is not zero", his_pure_cbl(1e-9) > 426.0,
          True)
    check("...nor is the gate only for exact zero", gui.pure_cbl(-1.0), 0.0)

    print("-- passive, his literals --")
    for row in (0, 1, 2, 3):
        check("passive(%d)" % row, gui.passive(row), his_passive(row))
    # The composed number at a = 50, as a receipt for the arithmetic: these four
    # are what the panel's two tiles add up to, and the retired per-row tables
    # gave a different four at the same `a` (154.3 / 210 / 188 / 588 here,
    # against -455.7 / 389.3 / 399 / 874 there -- the row-3 entry is the number
    # the runaway section below used to read, and the row-0 one is the only
    # entry of the old four that was negative).
    check("pure_cbl(50) + passive, the four rows",
          [gui.pure_cbl(50.0) + gui.passive(row) for row in (0, 1, 2, 3)],
          [154.3, 210.0, 188.0, 588.0])
    print("     (the retired per-row tables gave -455.7 / 389.3 / 399 / 874 at "
          "the same a = 50; the new four are one curve plus four constants)")

    print("-- pMultiplier, his literals --")
    check("press_multiplier(11500)", gui.press_multiplier(11500.0), 1.0)
    check("press_multiplier(11500.1)", gui.press_multiplier(11500.1), 2.0)
    check("press_multiplier(27000)", gui.press_multiplier(27000.0), 2.0)
    check("press_multiplier(27000.1)", gui.press_multiplier(27000.1), 4.0)
    check("press_multiplier(0)", gui.press_multiplier(0.0), 1.0)

    # The wiki's three bands, and the colour the console gives them.  The bands
    # are DERIVED from PRESS_AMP -- one source, so a mutant of a threshold moves
    # the multiplier and the label together -- and the colour is a legibility
    # choice on a light theme, not the wiki's "white / yellow / red" (that
    # describes the game's dark screen).  What is checked is that the three names
    # get three distinct foregrounds and that the boundaries fall where the wiki
    # puts them, including the one place the wiki's own table overlaps (27000,
    # which its `<= 27000 -> 2` settles as HIGH).
    print("-- the wiki's three pressure bands --")
    check("11500 is still normal", gui.press_band(11500.0), "normal")
    check("11500.1 is high", gui.press_band(11500.1), "high")
    check("27000 is still high", gui.press_band(27000.0), "high")
    check("27000.1 is extreme", gui.press_band(27000.1), "extreme")
    check("...which is the multiplier's own boundary, not a second table",
          [gui.press_multiplier(p) for p in (11500.0, 11500.1, 27000.0,
                                             27000.1)],
          [1.0, 2.0, 2.0, 4.0])
    check("three distinct colours", len(set(gui.PRESS_COLOURS.values())), 3)
    check("...keyed by the band names", sorted(gui.PRESS_COLOURS),
          ["extreme", "high", "normal"])
    check("the label carries the threshold it used", gui.press_band_text(8000.0),
          "normal  (<= 11500)")
    check("...and the top band names the floor it passed",
          gui.press_band_text(30000.0), "extreme  (> 27000)")

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
    # ...which is a_eff = 0.756 * 50 = 37.8 since Phase 148, NOT 50 and NOT 150.
    # The console's opening POSITION is unchanged; what the spec changed is what
    # that position means, so this is checked here rather than papered over by
    # moving the default (moving a control to defend a reading is the wrong
    # direction).  37.8 is also a helpful number to have in hand: it is neither
    # of the two old aggregates, so an untouched Phase-147 model goes red here
    # before it can produce a plausible tick.
    check("one bank at PW2 is a_eff = 37.8, not 50",
          console.core.a_eff, his_a_eff(2, 0, 0))
    check("...and it is not the sum either", console.core.a_eff == 50.0, False)
    check("...nor the mean of the three", console.core.a_eff == 50 / 3, False)
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
          "the core model   dT = pure_cbl * p_mult + passive[s] - coolant"
          " + noise   (or exactly -586, stalled)")

    # All three banks on PW2 before the regression below.  ONE bank at PW2 is
    # a_eff = 37.8 now, and the point of the three ticks below is his equation at
    # a known `a` -- three at PW2 is a_eff = 1.474 * 50 = 73.7, which is the `a`
    # this section is driven at.  The opening position is checked just above,
    # where it belongs.
    for var in console.cbl_vars:
        var.set(50)
    console.on_power()
    check("three banks at PW2 are a_eff = 73.7", console.core.a_eff,
          his_a_eff(2, 2, 2))

    # One tick at a time, against the wiki's equation with its literals.  The
    # tick period is 1.0 s, so at the Nth tick t = N and a_eff = 73.7 (all three
    # banks at PW2).  A_PW2 is spelled from the wiki's weights rather than
    # written as the literal 73.7, so the tick section moves with the weights and
    # is not a second copy of a number that could drift away from them.
    A_PW2 = his_a_eff(2, 2, 2)
    deltas = []
    for n in (1, 2, 3):
        pressure = console.sim.Pressure
        temp = console.sim.Temperature
        console.step_once()
        values = screen(right)
        want = his_temperature(temp, 1, A_PW2, pressure, float(n))
        deltas.append(float(values["T'  next tick's temperature"]) - temp)
        check("t after tick %d" % n, values["t   elapsed since armed (s)"], str(n))
        check("row at tick %d" % n, values["row  (passive index)"], "1")
        check("pure_cbl at tick %d" % n,
              values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "787")
        check("passive at tick %d" % n,
              values["passive  this row's constant"], "-400")
        check("press x at tick %d" % n, values["press x   pMultiplier"], "1")
        check("activeFluc at tick %d" % n,
              values["activeFluc  pure_cbl x press"], "787")
        check("noise(%d)" % n, values["noise(t)"],
              gui.shown(his_noise(float(n), A_PW2)))
        check("T' at tick %d against his equation" % n,
              values["T'  next tick's temperature"], gui.shown(want))

    # The revision, in one line: the noise is ADDED, so its amplitude is what it
    # says it is (+-88 at a_eff = 73.7) and a tick moves by about `pure_cbl` minus
    # the row's passive.  In the old closed form the same three sines were inside
    # the multiplication, so the same t gave a wobble of 88 * t and the step was
    # 787 + 88t.  Under this spec the same tick moves by 787 - 400 = 387.
    print("\n-- the noise is a tremor on the reading, not on the slope --")
    check("noise(1) is tens, not tens x t", abs(his_noise(1.0, A_PW2)) < 300, True)
    check("...so each of the three ticks moved by about pure_cbl - passive",
          all(abs(delta - 387) < 120 for delta in deltas), True)

    # --- the row changes, and NOTHING jumps ---------------------------------
    # In the closed form the row moved the whole line: crossing 2 -> 3 added
    # (1036 - 580) * x -- about nineteen thousand degrees by the time it was
    # crossed.  Under the quadratic the row moves a CONSTANT and nothing else
    # (passive is 22 lower on row 2 than on row 1), so a step has no line to
    # move.  This is the check that says so.
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
    # The tight one: the row changed 1 -> 2, so the step's only difference from
    # the tick before it is 22 degrees of passive plus whatever the tremor did
    # between those two ticks -- and the tremor's own swing is bounded by one
    # period's worth of its three sines (about 82 at a = 50, `15/1.5 + 10/0.7 +
    # 5/0.3` times the level scaling of 2).  So a change of a line's worth
    # (~19000 against ~500 under the closed form) has nowhere to hide here.
    check("...and the tick at the change moved like the one before it",
          abs(crossing[2] - previous_delta) < 110, True)
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
    # forties, and `tail[0]` is the row that tick was actually taken in (2: the
    # row is recomputed, so the tick that CROSSES into 3 is still row 2's).
    check("a late tick still moves by his line",
          abs(tail[2] - his_line(tail[0], A_PW2, tail[1])) < 220, True)

    # The runaway is the model's to have -- and since Phase 148 it has an END.
    # This section used to say "the reading goes past the top of the slider",
    # which was the way of saying the widget did not clip it.  It can no longer
    # say that, and the reason is not a clip: the wiki's meltdown wall (39,000 F)
    # sits BELOW the slider's own top (40,000), so the model latches and stops
    # before the widget's range could ever hide it.  The honest replacement is a
    # statement about WHICH limit stopped it: it reached the game's wall, it is
    # still below the widget's top, and the panel says so.
    print("\n-- the runaway ends at the meltdown wall, not at the slider --")
    steps = 0
    while steps < 400 and not console.core.melted:
        console.step_once()
        steps += 1
    values = screen(right)
    check("the core ran to the meltdown wall", console.core.melted, True)
    check("...at or past the wiki's 39,000 F",
          console.sim.Temperature >= gui.CORE_MELTDOWN_AT, True)
    check("...and BELOW the slider's top, so the widget is not what stopped it",
          console.sim.Temperature < gui.TEMP_MAX, True)
    check("the reading on screen is the model's own value",
          values["T'  next tick's temperature"],
          gui.shown(console.sim.Temperature))
    check("the row readout says MELTDOWN where the row would be",
          values["row  (passive index)"], "4 MELTDOWN")
    check("...and the flag beside it", values["meltdown  core reached the wall"],
          "YES")
    check("press x is showing the amplification on screen",
          values["press x   pMultiplier"] in ("2", "4"), True)
    # The pair that makes the new shape visible on the panel: the CURVE tile is
    # the same number whatever row the console is in, and the row is entirely in
    # the constant beside it.  A single summed "baseFluc" tile -- which is what
    # was here -- could not show that distinction, and read 874 at this point
    # under the retired per-row tables.
    check("pure_cbl on screen is the row-independent curve",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "787")
    check("...and the row 3 constant is the tile next to it",
          values["passive  this row's constant"], "-22")

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
    # Reset first: the runaway above ran t out to 180-odd seconds and latched the
    # meltdown wall, and the check below is about the row, not about where the
    # run got to.
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
    check("...including the increment",
          values["activeFluc  pure_cbl x press"], "-")
    pressure = console.sim.Pressure
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("row 0 in use", values["row  (passive index)"], "0")
    check("row 0's passive is his -455.7",
          values["passive  this row's constant"], "-456")
    check("...and the curve beside it does not know the row",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "787")
    check("row 0 at a_eff = 73.7, his equation",
          values["T'  next tick's temperature"],
          gui.shown(his_temperature(temp, 0, A_PW2, pressure, console.core.t)))
    # Row 0 used to be the row where the lasers did NOTHING (its `active` line
    # was exactly 0) and the only reading it could give was its -455.7.  Under
    # the quadratic the level works on every row, and row 0 at a_eff = 73.7
    # HEATS: 787.3 - 455.7 is +331.6.  So the reading that used to be here
    # ("negative and moving down") is now the opposite, and the only console
    # that falls is one with every bank dark -- the "off" section below is where
    # that lives.
    check("...so row 0 at this a_eff heats, where it used to hold still",
          float(values["T'  next tick's temperature"]) > temp, True)

    # --- CBL power ----------------------------------------------------------
    # `a = level * 25`, which is the number the radios carry, so PW5 is level 5.
    # Row 3 held by hand for the on-screen checks.  The reason is no longer the
    # old one -- under the retired tables row 0 was the single row where `a` had
    # no effect at all, so a check made from whatever row the console happened
    # to be in could pass without ever looking at `a` (CLAUDE.md 0.31 (1));
    # his quadratic is the same curve everywhere, so that hazard is gone by
    # construction.  Row 3 is held now because it has the smallest passive, so a
    # misread level moves the composed number furthest.
    print("\n-- CBL power is his `a` --")
    for level in (1, 2, 5):
        check("pure_cbl(a=%d)" % (level * 25),
              gui.pure_cbl(level * 25.0), his_pure_cbl(level * 25.0))
    console.auto_var.set(False)
    console.on_auto()
    console.core_var.set(3)
    console.on_core_state()
    # ONE bank at PW5 and the other two dark.  Under the mean this was a third of
    # the bank's own value (41.67); under the weights it is 0.756 * 125 = 94.5,
    # so POSITION now buys more than the bank is worth and still less than the
    # bank is worth: the first laser carries three quarters of its own power,
    # the third carries a fifth of it.
    console.cbl_vars[0].set(125)
    for var in console.cbl_vars[1:]:
        var.set(0)
    console.on_power()
    check("one bank at PW5 is 0.756 * 125 = 94.5",
          console.core.a_eff, his_a_eff(5, 0, 0))
    check("...and it is NOT the bank's own value, as it was before",
          console.core.a_eff == 125.0, False)
    console.step_once()
    values = screen(right)
    check("row 3 held", values["row  (passive index)"], "3")
    check("one bank at PW5: his curve at a = 94.5",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "991")
    check("...and row 3's constant on the tile beside it",
          values["passive  this row's constant"],
          gui.shown(his_passive(3)))

    # All three at PW5.  This is the ceiling, and it is PAST the 25..125 band the
    # old fit was taken in -- carried, not clamped (CLAUDE.md 0.34 rules that a
    # superseded reading is retired loudly rather than silently rescaled).  The
    # two checks here hold both halves: the arithmetic, and the fact that the
    # arithmetic is now extrapolating.
    for var in console.cbl_vars:
        var.set(125)
    console.on_power()
    check("all three at PW5: a_eff = 1.474 * 125 = 184.25",
          console.core.a_eff, his_a_eff(5, 5, 5))
    check("...which is PAST the 25..125 band the fit was taken in",
          console.core.a_eff > 125.0, True)
    print("     (a_eff ceiling 184.25 vs fit top 125.0: %+.2f%% -- "
          "extrapolated, carried, not clamped)"
          % ((his_a_eff(5, 5, 5) / 125.0 - 1.0) * 100.0))
    console.step_once()
    values = screen(right)
    check("...and row 3's curve at a = 184.25 is his own",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "2380")
    check("...with row 3's constant unchanged beside it",
          values["passive  this row's constant"], "-22")

    # "off" is ours, not the spec's, for the CURVE: the fit covers levels 1..5
    # and there is no level 0 in it, so zero CBL is defined as adding nothing
    # rather than by extrapolating the quadratic down to a = 0 (which would
    # still add its own 426).  The tremor scales with the level, so it goes
    # quiet too.
    #
    # What the 2026-10-16 spec does NOT put under that rule is `passive`.  It is
    # added outside -- his own note says the multiplier takes the active heating
    # only -- so a console with every bank dark COOLS at its row's rate.  That
    # is the one behavioural change in the spec, and this section used to assert
    # the exact opposite ("off holds the reading still"), because until now the
    # row's whole contribution sat under the same gate.
    #
    # Row 0 is held for it so the loss is the largest of the four (-455.7 a
    # tick); on row 3 the same claim would read -22 and a sign error would be
    # 22 degrees wide instead of 456.
    print("\n-- off: the curve is ours to zero, the passive is not --")
    console.core_var.set(0)
    console.on_core_state()
    for var in console.cbl_vars:
        var.set(0)
    console.on_power()
    temp = console.sim.Temperature
    console.step_once()
    values = screen(right)
    check("row 0 held, so the loss below is the biggest of the four",
          values["row  (passive index)"], "0")
    check("a dark console adds no curve",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "0")
    check("...and no tremor either", values["noise(t)"], "0")
    check("...so nothing is amplified", values["activeFluc  pure_cbl x press"],
          "0")
    check("...but the row's passive still takes its cut",
          values["passive  this row's constant"], "-456")
    check("so a dark console falls -- the change this spec makes",
          values["T'  next tick's temperature"],
          gui.shown(temp + his_passive(0)))

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
    # the panel has three rows of radios; what the fit eats is their WEIGHTED sum
    # `a_eff = 0.756 L1 + 0.522 L2 + 0.196 L3`.  Held on row 3, whose passive is
    # the smallest, so a check made here moves furthest if the weighting is ever
    # read as a mean, a sum, or the wrong bank.
    #
    # PW5 / PW2 / dark on the three banks: a_eff = 94.5 + 26.1 + 0 = 120.6.
    # Deliberately an ASYMMETRIC triple, which under the old mean was needed for
    # a different reason (the mean of 5/3/1 is exactly the middle bank, so no
    # check there could tell "the mean" from "bank 2").  Under the weights the
    # asymmetry is what makes three DIFFERENT readings separable: the mean gives
    # 58.33, the sum 175, bank 1 alone 125, and the weights 120.6.
    print("\n-- three banks, each weighted by its position --")
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
    check("a_eff is the weighted sum, not the mean", console.core.a_eff,
          his_a_eff(5, 2, 0))
    check("...and it is not the sum", console.core.a_eff == 175.0, False)
    check("...nor the mean", console.core.a_eff == his_a_mean(5, 2, 0), False)
    check("...nor any one bank", console.core.a_eff in (125.0, 50.0, 0.0),
          False)
    console.step_once()
    values = screen(right)
    check("the three banks on screen", values["a1 / a2 / a3  banks"],
          "125 / 50 / 0")
    check("the weighted sum on screen",
          values["a_eff  weighted sum of the 3"], "121")
    check("row 3 at a_eff = 120.6, the wiki's curve",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "1309")
    check("...and the row's constant, which is what makes it row 3's",
          values["passive  this row's constant"], "-22")

    # --- the wiki's TWO examples, because one of them is not decisive ---------
    # The wiki states the pair as the demonstration that position matters:
    # `(100, 25, 25)` heats ~580 F/s in State 1 and `(25, 25, 100)` ~220 F/s.
    # The whole evidence is in their DIFFERENCE, and the mean cannot produce one:
    # it reads 50 levels for both.  But the mean DOES reproduce the second
    # example to within ~10 F (210 vs 220) -- so a check that pinned only one of
    # the pair would go green on the superseded formula.  Both are checked, and
    # the difference is checked as a quantity, which is the thing that has no
    # value at all under the mean (0.0).
    #
    # "~580 F/s in State 1" is `pure_cbl(a_eff) * p_mult + passive[1]` with
    # p_mult = 1: the wiki's rate is the whole of dT at that instant, minus noise
    # (which it does not quote), so the check is against the noise-free line.
    print("\n-- the wiki's pair, and why one example is not evidence --")
    first = his_a_eff(4, 1, 1)      # (100, 25, 25), State 1
    second = his_a_eff(1, 1, 4)     # (25, 25, 100), State 1
    line1 = his_line(1, first, his_press(8000.0))
    line2 = his_line(1, second, his_press(8000.0))
    check("a_eff for (100,25,25) is 93.55", first, 93.55)
    check("a_eff for (25,25,100) is 51.55", second, 51.55)
    check("...so the two readings are 360.66 apart",
          round(line1 - line2, 2), 360.66)
    print("     (first %g vs wiki '~580'; second %g vs wiki '~220')"
          % (line1, line2))
    check("the first example reproduces '~580 F/s'",
          abs(line1 - 580.0) < 5.0, True)
    # The mean, on the SAME two positions, gives one number for both: this is the
    # falsification, and it is a measurement rather than a note.
    mean1 = his_line(1, his_a_mean(4, 1, 1), his_press(8000.0))
    mean2 = his_line(1, his_a_mean(1, 1, 4), his_press(8000.0))
    check("the mean cannot separate the pair", mean1 - mean2, 0.0)
    # It reproduces the SECOND one to within 10 F, which is exactly why a
    # single-example checker would have passed the wrong formula.
    check("...and it lands within 10 F of the second example",
          abs(mean2 - line2) < 10.0, True)
    print("     (mean reading on both positions: %g -- vs the wiki's pair "
          "of ~580 and ~220)" % mean1)
    # The wiki's PROSE percentages applied as shares are the other honest
    # reading of the same page, and its own first example falsifies them.
    pct_first = his_line(1, his_a_percent(4, 1, 1), his_press(8000.0))
    check("the prose percentages (51.3/35.4/13.3) miss the first example",
          abs(pct_first - 580.0) < 5.0, False)
    print("     (51.3/35.4/13.3 -> 63.475 -> %g F/s, and they sum to 1.0 "
          "while the coefficients sum to 1.474: the prose describes the ORDER, "
          "the coefficients are the formula)" % pct_first)
    check("the coefficients sum to 1.474, the percentages to 1.0",
          (0.756 + 0.522 + 0.196, 0.513 + 0.354 + 0.133), (1.474, 1.0))

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
          values["row  (passive index)"], "1")
    # Under the wiki's weights the same three positions read a_eff = 138.55,
    # not the mean's 75 -- (5,3,1) is exactly the triple where position and
    # magnitude disagree most in this file.
    check("his example: a_eff = 0.756*125 + 0.522*75 + 0.196*25 = 138.55",
          console.core.a_eff, his_a_eff(5, 3, 1))
    check("...which is not the mean of the three positions",
          console.core.a_eff == his_a_mean(5, 3, 1), False)
    # The heat is now TWO numbers on the panel where it used to be one: his
    # curve at a_eff = 138.55 (1568.92) and row 1's own constant (-400).  Both
    # are his literals, and the 561 this section used to read was the retired
    # tables' 6.86*75 + 65.5 - 19.2 -- kept in the print below as a receipt.
    check("his example: his curve on screen",
          values["pure_cbl  0.0516 a^2 + 1.1 a + 426"], "1569")
    check("...and row 1's constant beside it",
          values["passive  this row's constant"], "-400")
    check("...and the model's own curve is his 0.0516*a^2 + 1.1*a + 426",
          gui.pure_cbl(his_a_eff(5, 3, 1)), his_pure_cbl(his_a_eff(5, 3, 1)))
    check("...and row 1's own constant is his -400",
          gui.passive(1), his_passive(1))
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
          "the one in force for part of the day -- takes off 720.  Both numbers "
          "are his own arithmetic; which one the panel shows is his choice of "
          "unit and it has flipped three times.)")
    check("his example: noise(1) = 100.985...", values["noise(t)"], "101")
    # Closed at the SCREEN layer, which is where the console makes its promise,
    # plus one bounded comparison underneath it: the two spellings of his three
    # sines are NOT bit-identical, and the reason is not the model.  See
    # check_close -- CPython's `sum()` is compensated for floats, so the panel's
    # own spelling lands 7.1e-15 away from his left-to-right `a + b + c`.
    check("...and the model's own number is his three sines at a_eff = 138.55",
          gui.shown(gui.noise(1.0, his_a_eff(5, 3, 1))), "101")
    check_close("...and the two spellings agree to 1e-12, not to the last bit",
                gui.noise(1.0, his_a_eff(5, 3, 1)),
                his_noise(1.0, his_a_eff(5, 3, 1)), 1e-12)
    check("...and my transcription of those sines is the literal he wrote",
          his_noise(1.0, his_a_eff(5, 3, 1)), 100.98487197045065)
    # The tail, and the receipt for the old one.  Under this spec the tick is
    # 1568.924 - 400 - 240 + 100.985 = 1029.909..., so T' = 13030; the retired
    # tables' own line (560.8 - 240 + 54.665 = 375.465, T' = 12375) is printed
    # rather than checked, because it is not the model any more and a check on it
    # could only ever be green for the wrong reason (CLAUDE.md 0.31 (1)).
    print("     (the retired per-row line at this same instance read base_heat "
          "561, dT 375.465, T' 12375 -- 6.86*75 + 65.5 - 19.2.  The mean-based "
          "Phase-147 reading of the same instance was 798.75 - 400 - 240 + "
          "54.665, i.e. T' 12213; both are receipts.)")
    check("his example: dT = 1568.924 - 400 - 240 + 100.985 = 1029.909..., "
          "shown as 1030",
          gui.shown(console.sim.Temperature - 12000.0), "1030")
    check("his example: T' = T + dT", values["T'  next tick's temperature"],
          "13030")
    check("...and his formula, assembled independently, says the same",
          values["T'  next tick's temperature"],
          gui.shown(his_temperature(12000.0, 1, his_a_eff(5, 3, 1), 8000.0, 1.0,
                                    his_cooling([2, 2, 2]))))
    check("...which is his line, his two heat terms and all",
          gui.shown(his_line(1, his_a_eff(5, 3, 1), his_press(8000.0))), "1169")
    check("...and the model's own line agrees with the transcription",
          gui.shown(gui.pure_cbl(console.core.a_eff) * gui.press_multiplier(8000.0)
                    + gui.passive(1)),
          gui.shown(his_line(1, console.core.a_eff, his_press(8000.0))))

    # --- the three coolant pumps --------------------------------------------
    # The third of the game's three control means.  The CONSTANT is measured
    # (see his_cooling); what is checked here is where it SITS, because that
    # part is a choice and not a reading -- CLAUDE.md 0.31's question, asked of
    # a spec that arrived after the model it lands in:
    #   * it is its own term rather than so many CBL levels' worth of negative
    #     `a`, so it works with the lasers dark (the shipped log has 84 records
    #     at CBL sum 0 with the pumps running) and it is not a per-row quantity;
    #     CORRECTION 2026-10-16, the sentence above is kept as it was written
    #     because that is how it was read at the time: all 84 of those records
    #     carry `stats.GameActive = false`, so the machine was NOT running in any
    #     of them and the log does not show the game cooling with the lasers
    #     dark.  The reading that overturned it is `_tools/passive_from_log.py`
    #     section 4, which asks this exact question (cbl sum 0, pumps on) and
    #     answers "none".  The PLACEMENT below is unaffected -- it is still a
    #     choice made to match the spec, it just is not corroborated by that
    #     count any more;
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
    # The lasers are dark for the tick below, so the curve adds nothing and the
    # tremor is scaled by a level of zero: what is left is the row's own passive
    # and the pumps.  This is the check that says where the spec drew its line --
    # "off is ours" holds for the CURVE (a dark bank contributes 0), and does
    # NOT hold for the row's constant, which is the one behaviour this spec
    # changes: a console with every bank dark now falls at its row's rate
    # instead of holding still.
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
    # `his_passive(3)` and not zero: the row is held at 3 by hand here, and the
    # spec's one new behaviour is that its constant lands on a dark console too.
    # Leaving it out of the expectation would make this check pass under the OLD
    # reading -- which is precisely the thing being changed -- so the term that
    # distinguishes them has to be in the sum (CLAUDE.md 0.31 (1)).
    check("a dark laser bank does not silence the pumps",
          values["T'  next tick's temperature"],
          gui.shown(temp + his_passive(3) - his_cooling([3, 0, 1])))

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
    want = his_temperature(temp, 3, his_a_eff(3, 1, 0), pressure, console.core.t,
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
    # The name covers BOTH terms that must not be scaled here, not just the
    # cooling: a console with every bank dark has nothing for the band to
    # multiply, so row 3's -22 is -22 at 1 and at 2 as well.  They sit in the
    # same sum, so one check on the sum cannot say which of them moved -- and a
    # mutant that scaled the row constant would otherwise redden a check whose
    # name talks only about the pumps (misleading reds are how a wrong map gets
    # written, CLAUDE.md 0.29).
    check("the doubled band scales neither the cooling nor the row constant",
          values["T'  next tick's temperature"],
          gui.shown(temp + his_passive(3) - his_cooling([0, 0, 1])))

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
    #
    # Where the two controls stand against each other -- the open half of R11.
    # The top of the fit is a = 125 (three banks at PW5, and since 2026-10-16 the
    # mean of the three), and the row's composed heat there is the curve under
    # p_mult 1 plus that row's constant: 914.05 / 969.75 / 947.75 / 1347.75.
    # Composed from the model and compared at the SCREEN layer, so the four
    # numbers here are the ones the panel would print, and the decimals live in
    # the print below.  What is PRINTED and not checked is the comparison to the
    # original, because that ratio is a property of the two games and not of
    # this one.
    top = 125.0
    check("the top of the fit, composed per row",
          [gui.shown(gui.pure_cbl(top) * gui.press_multiplier(10000.0)
                     + gui.passive(row)) for row in (0, 1, 2, 3)],
          ["914", "970", "948", "1348"])
    print("     (maximum coolant is -%g a tick.  Against the composed heat at the "
          "top of the fit that is %s of the four rows, where the original's own "
          "1080 against ITS 975 a row was 110.8%% -- and note the one-number "
          "form of that claim is gone: his fitted line is steeper than the "
          "original's 65 a level by 1.42x at a = 25, 2.41x at 50 and 5.38x at "
          "125, so there is no single factor.  The constant stays the measured "
          "one and the arithmetic is not bent around it -- QUESTIONS.md R11)"
          % (his_cooling([3, 3, 3]),
             " / ".join("%.1f%%" % (100.0 * his_cooling([3, 3, 3])
                                    / (gui.pure_cbl(top)
                                       * gui.press_multiplier(10000.0)
                                       + gui.passive(row)))
                        for row in (0, 1, 2, 3))))

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
          values["activeFluc  pure_cbl x press"], "-586")
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
    check("...and for this tick a_eff is at its ceiling",
          console.core.a_eff, his_a_eff(5, 5, 5))
    tremor_now = his_noise(console.core.t, his_a_eff(5, 5, 5))
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

    # --- the Emergency Vents ------------------------------------------------
    # The wiki's two pages agree on the shape and this section checks the shape:
    # THREE of them, each its own switch, each ~7,000 F off the core, each
    # usable ONCE per shift, refilled only by a new shift.  What it does NOT do
    # is touch pressure -- unlike the AVB, which is the whole difference between
    # the two emergency devices -- and that is checked too, because "cooled the
    # core" and "cooled the core and moved the chamber" read the same on the
    # temperature tile alone.
    #
    # The drop is an EVENT, like the AVB's: -7000 once, not -7000 a tick.
    print("\n-- E-Vents: three, -7000 each, once per shift, room only --")
    console.reset()

    def left():
        """How many vents this shift still has -- read from the count, the one
        place the console keeps it, rather than from a second tally."""
        return gui.E_VENT_COUNT - console.sim.e_vent_count

    check("three of them", len(console.e_vent_buttons), gui.E_VENT_COUNT)
    check("...all ready on a new shift", left(), 3)
    check("...and the panel says so", console.e_vent_text.get(), "all 3 ready")
    console.sim.Temperature = 20000.0
    before_p = console.sim.Pressure
    dropped = console.sim.e_vent(0)
    # The literal 7000.0, NOT `gui.E_VENT_DROP`.  Comparing the drop against
    # the constant that produced it is the vacuous shape CLAUDE.md 0.31 (1)
    # warns about: the mutant run showed it staying green while the constant
    # moved to 6500, and only the temperature check beside it caught that.
    check("one press takes the wiki's ~7000", dropped, 7000.0)
    check("...off the temperature", console.sim.Temperature, 13000.0)
    check("...and the pressure is untouched", console.sim.Pressure, before_p)
    check("...and that one is spent", left(), 2)
    check("...so a second press of the SAME vent is refused",
          console.sim.e_vent(0), None)
    # The other two are separate switches, not a shared pool: the wiki is
    # explicit ("each is controlled by its own switch"), so spending #1 must
    # leave #2 and #3 live.
    check("the other two still work", left(), 2)
    console.on_e_vent(1)
    check("...vent 2 fired", left(), 1)
    check("...and its drop landed", console.sim.Temperature, 6000.0)
    console.on_e_vent(2)
    check("all three spent", left(), 0)
    check("...and the panel says so", console.e_vent_text.get(),
          "3 of 3 used -- refilled only by Reset (a new shift)")
    check("...with every button out of service",
          [str(button.cget("state")) for button in console.e_vent_buttons],
          ["disabled"] * 3)
    check("a spent vent cannot cool a dead core",
          console.sim.e_vent(0), None)
    # One press is one event, not a term: the model's own tick does not add
    # another -7000 on top of whatever the lasers are doing.
    temp_before = console.sim.Temperature
    console.step_once()
    check("a tick after the last vent does not take another 7000",
          abs(console.sim.Temperature - temp_before) < 3000, True)
    # Floored at the model's minimum, and the REPORTED drop is what moved --
    # the same rule as the AVB's clamp, for the same reason (a log line that
    # claims 7000 the core never lost is a false reading).
    console.reset()
    console.sim.Temperature = 3000.0
    check("from 3000 only 3000 is reported", console.sim.e_vent(0), 3000.0)
    check("...and the core sits at the floor", console.sim.Temperature,
          gui.TEMP_MIN)
    # Refilled by a new shift, which is what Reset is.
    console.reset()
    check("Reset is the refill", left(), 3)

    # --- the meltdown wall --------------------------------------------------
    # The wiki's "State 4 (Meltdown) | >= 39,000 | game over" is a WALL, not a
    # fourth row: `core_state` still returns 0..3 (that is what the passive
    # table indexes) and the wall is a separate latch.  Both sides of it are
    # checked, plus the latch's own behaviour, because "the model stopped" and
    # "the model is still running and happened not to move" are the same reading
    # from the outside (CLAUDE.md 0.19's family).
    print("\n-- the meltdown wall is a latch, not a row --")
    check("38999.9 F is not melted", gui.melted(38999.9), False)
    check("39000 F is", gui.melted(39000.0), True)
    check("...and the state index still stops at 3", gui.core_state(40000.0), 3)
    console.reset()
    console.arm_var.set(True)
    console.on_arm()
    console.sim.Temperature = 38999.0
    console.step_once()
    check("a tick from 38,999 did not latch", console.core.melted, False)
    console.sim.Temperature = 39500.0
    console.step_once()
    check("a tick from 39,500 DID latch", console.core.melted, True)
    frozen_t = console.sim.Temperature
    console.step_once()
    check("...and the model now refuses to step", console.sim.Temperature,
          frozen_t)
    check("...so the latch is what stopped it, not the arithmetic",
          console.core.melted, True)
    console.reset()
    check("Reset rearms it", console.core.melted, False)
    # --- has always run -------------------------------------------------------
    #     fan_pressure_drop = fans * 60
    #     dP = p_base[s] + (T * p_temp_mult[s]) - fan_pressure_drop
    # is `calculation.luau`'s authoritative line with its PEA term taken off, and
    # `Sim.terms()`/`Sim.tick()` have spelled it that way since the first
    # version.  It is checked here because the spec restates it, and a model
    # that gets restated is a model that can fork without anything going red.
    #
    # `s` in this block is the LATCHED PRESSURE STATE (`Sim.State`, 1..3, an
    # if/elseif chain with no `else`), NOT the temperature ROW the heat tables
    # are indexed by.  The two are both called "state" in this project and the
    # tables are keyed off different ones; the case that separates them is
    # driven at the end of this section (CLAUDE.md 0.31 (5), DECISIONS_2 527).
    print("\n-- the pressure recurrence: p_base[s] + T*p_temp_mult[s] - fans*60 --")
    check("his three base gains", gui.STATE_GAIN, {1: 110, 2: 350, 3: 800})
    check("his three temperature slopes", gui.SLOPE, {1: 0.01, 2: 0.0075, 3: 0.005})
    check("...and his 60 for each fan", gui.FAN_DRAG, 60.0)
    check("...keyed 1..3, exactly as his table is -- there is no row 0",
          sorted(gui.STATE_GAIN), [1, 2, 3])
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
    for var in console.pump_vars:
        var.set(0)
    console.on_coolant()
    console.fan_var.set(6)
    console.on_fan()
    # PEA at 1 is `PEA_GAIN[1] = 0`: his dP has no PEA term at all, so the level
    # that contributes nothing is the one that makes the two spellings
    # comparable.  (The term is real in this simulation and in the original --
    # it is simply not in the line the operator sent.)
    console.pea_var.set(1)
    console.on_pea()
    for state, temperature, want in ((1, 12000.0, "-130"),
                                     (2, 20000.0, "140"),
                                     (3, 30000.0, "590")):
        console.sim.State = state
        console.sim.Temperature = temperature
        check("his dP at state %d, T = %g, 6 fans" % (state, temperature),
              gui.shown(sum(console.sim.terms())), want)
        print("      %g + %g*%g - 6*60 = %s"
              % (gui.STATE_GAIN[state], gui.SLOPE[state], temperature, want))
    # The fans, isolated: the same state with them off must differ by exactly
    # their own 360, which is the only reading here that says the last term is
    # the fans and not six times something else.
    console.fan_var.set(0)
    console.on_fan()
    check("...and the fans are exactly the -360 at state 3",
          gui.shown(sum(console.sim.terms())), gui.shown(his_dp(3, 30000.0, 0.0)))
    console.fan_var.set(6)
    console.on_fan()
    # The separation that has to be driven, not assumed: 12000 is temperature ROW
    # 1 and pressure STATE 3, and this table is the state's.  The two spellings
    # are -130 and 500 -- 630 apart -- so a model that reached for the row here
    # could not look right.
    console.sim.State = 3
    console.sim.Temperature = 12000.0
    check("12000 is temperature row 1", gui.core_state(12000.0), 1)
    check("...and the pressure table is the STATE's, not that row's",
          gui.shown(sum(console.sim.terms())), "500")
    print("      (the row's own spelling of this same tick would be %s)"
          % gui.shown(his_dp(1, 12000.0, 6.0)))
    # One real tick, through the console's own order: the model first, then the
    # pressure -- so the slope rides the temperature the tick ENDED with, which
    # is why the expectation reads it after the step rather than before it.
    # Row 3 held and every bank dark, so the temperature falls by that row's
    # passive and stays inside state 3.
    console.sim.State = 3
    console.sim.Temperature = 30000.0
    before = console.sim.Pressure
    console.step_once()
    values = screen(right)
    check("...and the tick ended in state 3 still", console.sim.State, 3)
    check("the tick's dP, his line at the temperature it ended with",
          values["Delta this tick"],
          gui.shown(his_dp(3, console.sim.Temperature, 6.0)))
    check("...and the pressure moved by exactly that",
          values["Pressure"],
          gui.shown(before + his_dp(3, console.sim.Temperature, 6.0)))

    root.destroy()
    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    for name in FAILURES:
        print("  FAILED: %s" % name)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
