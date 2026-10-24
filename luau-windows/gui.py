"""A small tkinter console for `calculation.py`.

    python gui.py

The model below is copied from `calculation.py` (that file, and the .luau next
to it, stay the reference), so this one file reads top to bottom: the numbers,
then the window.  It shows the five values live and lets you change the three
the original hard-codes -- Temperature, ActiveFan, PEALevel.

Readings are ROUNDED FOR THE EYE and nothing else: Pressure accumulates in full
float, exactly as the .luau does.  Rounding the model would make it drift away
from the original, which the .luau comparison can no longer see.  `calculation.py`
stays the place that prints exact values.

To add a control: make the widget next to the others and give it a `command`
that writes `self.sim` then calls `self.on_input(...)`.  To add a readout: one
more `add_readout` line in `_build_readouts`.  There is no framework here.

THE CORE MODEL IS A SECOND, SEPARATE MODEL.  The pressure tables are copied
from `calculation.luau` and are that file's numbers.  The temperature model in
`CORE MODEL` below is the operator's own, fitted to his LEVEL 1-5 logs and
handed over in two passes (2026-10-13, revised 2026-10-14) -- it is not in
calculation.luau, which takes Temperature as an input and never computes it.
So the two are kept in their own blocks and neither is allowed to rewrite the
other's tables: what joins them is the single Temperature value, which the core
model writes and the pressure terms read.

The 2026-10-14 revision (the spec headed "temperature calculation") changed the
temperature model from a closed form to a per-tick STEP.  `core_model_check.py`
is the second spelling of that spec and is what says the window agrees with it.
"""

import math
import tkinter as tk
from tkinter import ttk

# ========== THE MODEL ==========
# Copied from calculation.py.  The three tables keep their 1-based integer
# keys, because those keys ARE the State / PEALevel values -- renumbering them
# to 0-based lists would move every reading by one row, and nothing would error.

STATE_MIN = 5600
STATE_1_MAX = 17500        # exclusive
STATE_2_MAX = 29499        # inclusive, so 29499.5 already belongs to State 3

# The temperature widgets' range.  Named because the core model can and does run
# past the top of it (a runaway is a thing this console should be able to show),
# so the bound is needed as a number, not just as two widget arguments.
TEMP_MIN = 0.0
TEMP_MAX = 40000.0

# ========== THE PRESSURE RECURRENCE ==========
# The chamber pressure is NOT part of the operator's temperature spec: it is
# `calculation.luau`'s authoritative line, which this console has run since its
# first version.  The 2026-10-16 message restates it --
#
#     fan_pressure_drop = fans * 60
#     p_base[s]      = {1: 110, 2: 350, 3: 800}
#     p_temp_mult[s] = {1: 0.01, 2: 0.0075, 3: 0.005}
#     dP = p_base[s] + (T * p_temp_mult[s]) - fan_pressure_drop
#     P_next = P + dP
#
# -- and that restatement is written down here because a model that gets
# restated is a model that can fork.  His `dP` IS these four lines with the PEA
# term taken off; PEA is real in this simulation and in the original, it is
# simply not in the line he sent.  `core_model_check.py` drives all three states
# against his three literals rather than against these dictionaries, so the two
# spellings are compared and not merely both present.
#
# `s` here is the LATCHED PRESSURE STATE (`Sim.State`, keyed 1..3 -- an
# if/elseif chain with no `else`, so a temperature below STATE_MIN leaves the
# previous State standing), and NOT the temperature ROW the heat tables above are
# indexed by.  Both are called "state" in this project and the two tables are
# keyed off different ones (CLAUDE.md 0.31 (5), DECISIONS_2 527); the checker
# drives the case that separates them.
FAN_DRAG = 60.0            # pressure removed per tick, by each active fan

SLOPE = {1: 0.01, 2: 0.0075, 3: 0.005}
PEA_GAIN = {1: 0, 2: 0, 3: 75, 4: 150}
STATE_GAIN = {1: 110, 2: 350, 3: 800}

BANDS = {1: "%g .. %g" % (STATE_MIN, STATE_1_MAX - 1),
         2: "%g .. %g" % (STATE_1_MAX, STATE_2_MAX),
         3: "%g and up" % (STATE_2_MAX,)}


def snap(value):
    """Nearest whole number, halves away from zero.

    Deliberately not Python's round(), which is half-to-even: a reading parked
    on exactly .5 would show as unchanged every other tick, and these really do
    land on .5 -- the slope term is 0.01 x an integer temperature, so a State 2
    tick moves in steps of 0.0075 x T, and sums of those hit .5 exactly.
    """
    whole = int(abs(value) + 0.5)
    return -whole if value < 0 else whole


def shown(value):
    """Every reading on screen, as an integer."""
    return str(snap(value))


def luau_number(value):
    """The way the .luau prints a number (%.14g), kept for the tick period.

    The period is a duration the operator sets, not a reading: 0.25 s rounded
    to a whole number would print as 0, and a control that reports a value it
    does not have is worse than a wide one."""
    return "%.14g" % value


# ========== THE CORE MODEL ==========
# The operator's own temperature model (2026-10-13, revised 2026-10-14).  Not
# from calculation.py -- that file takes Temperature as an input and never
# computes one.  The active heat is his quadratic in `a` (`pure_cbl`, constants
# below), which is an empirical fit he took from his own LEVEL 1-5 logs; until
# the 2026-10-16 spec it was a linear fit, one line per core state.
#
# THE ROW INDEX HERE IS NOT `Sim.State`.  Two different quantities are both
# called "state", and Engine.luau's own comment says so (lines 287-290 there):
#
#   Engine.luau:320   coreState = T > 29500 and 3 or T > 17500 and 2
#                                 or T >= 5600 and 1 or 0
#                     -- a PURE FUNCTION of temperature, with a row 0
#   pressureState     the original's if/elseif chain with NO `else`, so below
#                     5600 the previous state STANDS -- latched, and that is
#                     what Sim.State above mirrors
#
# The operator's table was grouped by the first one, which is why it has a row 0
# (the cold machine) and why his `s` can fall as well as rise.  Sim.State cannot:
# it has no row 0 and it lags after a collapse, so feeding it here would hold the
# heat on after a scram.  `core_state()` below is the pure function.

# His two lists, in his own order -- index = row, so his `[s+1]` (his lists are
# 1-based) is this `[row]` and the slot he never indexes by hand is row 0.
#
# THE HEAT IS ONE CURVE IN `a` FOR EVERY ROW as of the 2026-10-16 spec, and the
# row supplies only the passive addend:
#
#     pure_cbl = {a_eff <= 0: 0, 0.0516 * a_eff^2 + 1.1 * a_eff + 426}
#     passive  = [-455.7, -400, -422, -22]
#
# What that replaced was a LINE PER ROW, `active[row] = (slope, intercept)`,
# fitted from his LEVEL 1-5 logs, with a much smaller passive table beside it:
#
#     active  = {0: (0.0, 0.0), 1: (6.86, 65.5), 2: (7.24, 37.0),
#                3: (6.8, 534.0)}
#     passive = {0: -455.7, 1: -19.2, 2: 0.0, 3: 0.0}      retired 2026-10-16
#
# The old tables stay here, in a comment, rather than in the diff only -- a
# reading that was reversed out has to keep a tooth (CLAUDE.md 0.34 (4): a rule
# only followed when someone remembers it has already been forgotten once), and
# core_model_mutants.py carries a mutant that puts those four lines back.
#
# THREE THINGS ABOUT THE NEW SHAPE, each one a behaviour the panel has never had
# and each one his rather than ours:
#
#   * `passive` SITS OUTSIDE THE LASERS' OFF RULE, so a console with every bank
#     dark now COOLS at its row's rate.  It has never done that: until this spec
#     the row's whole contribution WAS the fit and the fit was gated by "off is
#     ours", so a dark console held still.  Row 1 falls 400 a tick where
#     yesterday it added exactly 0.  This is the largest single change in the
#     spec and it is a decision, not a derivation -- what the shipped log can say
#     about it is a negative result, below.
#   * `p_mult` MULTIPLIES ONLY `pure_cbl` -- his own note on the line is "only
#     multiplies the active heating".  Before, the press band scaled the row's
#     whole line, passive included, so a doubled band also doubled the cooling.
#   * the zero gate is now INSIDE the curve.  That is the same rule this file has
#     always had ("off is ours" is ours, not the spec's: his fit covers levels
#     1..5 and he wrote the a<=0 branch himself), moved from beside the sum to
#     inside one term of it.  What it is NOT is a gate on `passive`.
#
# WHAT THE SHIPPED LOG SAYS ABOUT THE PASSIVE TERM: NOTHING, and that is worth
# recording as a reading rather than passing over.  `_tools/passive_from_log.py`
# asks `Data/DataCollection.Log` for a live chamber with every control off --
# the one case that would show a passive rate -- and finds none: of 39 records
# with CBL sum 0 and pumps 0, every one is `GameActive = false`, and all 84
# records with CBL sum 0 and pumps running are false there too.  So these four
# numbers are his measurement and are implemented as written; the log neither
# corroborates nor contradicts them.
PASSIVE_ROW = (-455.7, -400.0, -422.0, -22.0)   # his `passive`, one per row
# His quadratic, as (a^2, a, constant) rather than multiplied out, so the three
# literals in the spec are the three literals in the file and a reader can check
# them against it without doing arithmetic.  `a` is `a_eff` from the wiki's
# Temperature page -- `0.756 L1 + 0.522 L2 + 0.196 L3`, NOT a mean (Phase 148;
# the block below carries the two examples that identify it).
CBL_CURVE = (0.0516, 1.1, 426.0)

CBL_UNIT = 25.0            # one CBL level; only `noise` divides by it now
CBL_START = 50.0           # PW2: the level the console starts on

# THE THREE LASERS.  The game has three combustion lasers and each one carries
# its own PW1..PW5 (`CBL1-PW5` / `CBL2-PW1` / ... are click labels the shipped
# telemetry log actually contains), so "the CBL level" is three controls, not
# one.
#
# WHAT THEY COMBINE TO, FOURTH AND CURRENT READING (Phase 148, 2026-10-24).
# The TRG wiki's Temperature page is explicit and the earlier readings were not:
#
#   "The engine does NOT use a simple average; instead, it applies a hidden
#    positional weight to each laser."
#   a_eff = 0.756 * L1 + 0.522 * L2 + 0.196 * L3
#
# so bank 1 dominates, bank 3 barely counts, and the three coefficients do NOT
# sum to 1 (they sum to 1.474).  This is neither the sum Phase 136 wrote nor the
# mean the operator asked for on 2026-10-16 and again on 2026-10-16; it is a
# weighted combination and `Core.a_eff` is the one place it is spelled.
#
# The weights are not decoration: the same page works two examples, and the pair
# is what identifies them.  (100, 25, 25) -> a_eff 93.55 -> ~580 F/s in State 1,
# and (25, 25, 100) -> a_eff 51.55 -> ~220 F/s.  The MEAN gives 50 for both, so
# the pair separates the two readings; each example alone would not (the mean
# reproduces the second one to within 10 degrees for the wrong reason -- CLAUDE.md
# 0.31 (1), a check that passes because the thing under test is absent).
#
# TWO RECORDED TENSIONS, neither smoothed over:
#
#   * the page's own PROSE percentages are 51.3 / 35.4 / 13.3 (they sum to 1.0)
#     while its own COEFFICIENTS are 0.756 / 0.522 / 0.196 (they sum to 1.474).
#     They are different quantities -- the percentages are shares of the total,
#     the coefficients are the multipliers -- and the arithmetic in the two
#     worked examples uses the coefficients.  A reading that normalised them to
#     shares would give a_eff = 63.475 on (100,25,25), i.e. ~304 F/s, and does
#     not reproduce 580.  core_model_check.py asserts that falsification.
#   * a_eff now spans 0..184.25 (all three at PW5), past the 25..125 band the
#     operator's fit was taken over.  This reopens, on the high side, the class
#     of question QUESTIONS.md R9 (2) closed on the low side; it is written down
#     and carried, not clamped, because clamping would invent a number the wiki
#     does not contain.
CBL_WEIGHTS = (0.756, 0.522, 0.196)     # a_eff = w1*L1 + w2*L2 + w3*L3
CBL_BANKS = 3

# ========== THE COOLANT PUMPS (Isotope E) ==========
# The third of the game's three control means, and the only one this console was
# still missing: three pumps, each held at 0..3, that REMOVE heat rather than
# adding it.
#
# AVERAGED -- and this one line moved THREE times in a single day, so what
# follows is the whole list and not the latest word.  That is CLAUDE.md 0.34's
# rule read literally: for a spec that has been visited more than once the
# question is WHICH LINES it reaches, and the answer here has been "this one,
# every time".
#
#   * Phase 136, when the pumps arrived: no division at all.  The constant
#     multiplies the SUM of the three levels, 0..1080 a tick -- and that was this
#     console's own reading of the three sources rather than a word of his,
#     which is what made the sum look like the safer default for a while.
#   * Phase 137, the message headed "Correction": the SAME message averaged the
#     laser banks and the pumps, so `coolant_avg = (p1 + p2 + p3) / 3`, `x 120`,
#     0..360.
#   * Phase 138, "don't use the mean for the cooling": the average came back off
#     the PUMPS ONLY -- the banks kept theirs -- so the sum returned.
#   * Phase 139, "never mind, use the mean for the cooling after all": the
#     average is back.  Same line as Phase 137, and it is written the same way,
#     `coolant_avg * 120`, so the two visits are ONE spelling rather than two
#     that happen to agree -- `Core.cooling` is where it is spelled.
#
# The one division that never moved is the BANKS'.  It arrived in the same
# message as the pumps' and has survived all four, because it has a reason of its
# own: his fit spans `a = 25..125`, exactly one laser's worth, so the mean keeps
# the reading inside the band the line was fitted over (QUESTIONS.md R9 (2) is
# the extrapolation that closes with it).  The pumps have no fitted band to stay
# inside, so their unit is the operator's call -- and he has now called it twice
# one way and once the other.
#
# WHAT THAT LEAVES, since all three sources below write the SUM: the divergence
# can no longer hide inside a claim that they agree.  The constant is still their
# measured 120 and only the unit it multiplies moved, from three pumps to one
# average pump -- so for the same three positions this console takes off exactly
# a third of what their arithmetic says.  That is a real divergence, filed rather
# than smoothed (QUESTIONS.md R11 has the table), and nothing is rescaled to make
# the two agree.
#
# The constant is not remembered, it is measured -- three ways, and the third
# one is exact rather than close:
#
#   * `Data/TRGWeb.luau:178` (the original's own prototype, on disk):
#         core_temp = core_temp + (CBL1 + CBL2 + CBL3)*65
#                               - (coolant_pump1 + coolant_pump2 + coolant_pump3)*120
#                               + core_temp_random;
#     with `increasecoolantpumpNpower` clamping at 3 and `decrease` at 0, which
#     is where the 0..3 range above comes from.
#   * our own remake: `Config.Sim.PumpCooling = 120` (Engine.luau:280 applies it
#     as `heat*CBLHeat - cooling*PumpCooling` over the enabled, intact pumps).
#   * the shipped game's own telemetry, `Data/DataCollection.Log`: its
#     `predictions.predDT` is the original's arithmetic recorded live, and
#     `predDT * 5 == 65*sum(cbl.level) - 120*sum(coolant.levels)` holds on ALL
#     477 records with a maximum error of exactly 0.  That is the strongest of
#     the three -- two of the numbers in it (65 and 120) are read off a running
#     game rather than a source file.  `_tools/coolant_from_log.py` prints it.
#
# WHERE IT SITS IN THE STEP, which is the one real choice here and is a
# CLAUDE.md 0.31-style question ("what does this spec override?").  The console's
# temperature is HIS fit -- since 2026-10-16, `dT = pure_cbl*p_mult + passive[s]
# - coolant_effect + noise` (or exactly -586, stalled) -- and the cooling could
# be either (a) added to it as its own term, or (b) routed through his heating as
# so many CBL levels' worth of negative `a`.  It is (a), for three reasons:
#
#   * (b) would silence the pumps exactly when they matter most.  His heating is
#     gated by the "off is ours" rule -- `pure_cbl` is 0 with every bank dark,
#     which is the spec's own first branch -- and a dark laser bank is not a
#     reason for a pump to stop working.  Feeding the cooling in as negative `a`
#     would put it under that gate and under the quadratic with it.
#     CORRECTION (2026-10-16, the same day): this argument used to close with
#     "the log has that case in it: 84 records at CBL sum 0 with the pumps at 1,
#     2 or 3".  It does not: all 84 of those records carry
#     `stats.GameActive = false` -- 62 are the pre-start stretch (tempF 0,
#     pressure 0, pumps at 1 each) and 22 are the post-collapse tail (tempF
#     1063, fluctuation -1255, pumps at 3 each) -- so the chamber was not being
#     simulated in any of them.  (This split read "79 ... and 5" in the first
#     version of this correction: two numbers that sum to 84, sit in the right
#     sentence, and match no reading at all -- the data offers exactly one
#     split, by pump level and by tempF alike.  The count above it was always
#     measured; the prose was written around it and wandered.  CLAUDE.md 0.18,
#     and note which half of the writing it was.)  The claim was a count of
#     the right shape answering a question it cannot: "the file contains these
#     records" is not "the machine ran that way" (CLAUDE.md 0.31 (1), and the
#     original text is kept because it was written from a real reading).
#     The argument does not need the log: it rests on the identity below, where
#     the pump term is a term of the ORIGINAL's own per-tick arithmetic,
#     independent of the CBL and present in `TRGWeb.luau:178` as its own
#     subtrahend.
#   * (b) would make the cooling a per-ROW quantity, because it would have to
#     live in a term the row indexes.  Nothing in any of the three sources
#     suggests the pumps cool a hot core differently from a cold one.
#   * the sources have no pressure factor on it either, so it is added OUTSIDE
#     `pMultiplier` -- multiplying it by the press band would be inventing a
#     number no source has.  (The 2026-10-16 spec moved `passive` out of that
#     multiplication as well, so as of this phase the band scales exactly one
#     term: the lasers' own heat.)
#
# The stall still out-ranks it -- and since the 2026-10-16 correction it
# out-ranks EVERYTHING, because his `dT` is piecewise and the -586 sits where
# the whole expression would be: no heat, no pump term and no tremor on a
# stalled tick.  Before that it was read as a rate with the tremor still riding
# on the reading, which is a different answer the moment the banks are lit; the
# two readings are one line apart and QUESTIONS.md R12 has the other one.
#
# WHAT IT COSTS AT THE TOP (the residue of QUESTIONS.md R11).  Averaging the
# pumps puts the cooling at a third of what the sources' arithmetic gives, so the
# ratio it makes against this console's own heat is a third of the original's.
# Measured at the two maxima rather than asserted:
#
#   * the original's own ratio: its nine pump levels (1080) outweigh its own
#     maximum laser heat (15 levels x 65 = 975).  The pumps win at the top.
#   * here, since the 2026-10-16 spec: the same three pumps, averaged, are 360,
#     against three maxed banks at `pure_cbl(125) = 1369.75`.  The pumps LOSE,
#     and by row -- 39.4% / 37.1% / 38.0% / 26.7% -- where the original's own
#     margin was 110.8%.  The spread across rows is now entirely `passive`'s:
#     the active term is one curve for every row, so the row only decides how
#     much is subtracted from it.  Row 3 is the odd one because its passive is
#     the SMALLEST (-22), not because of any part of the heat.
#     (The retired per-row lines gave 903.8 / 942 / 1384 and 39.8% / 38.2% /
#     26.0% -- the same three-pump readings against different heat.)
#   * his pressure multiplier widens it again, and that is his: from 11500 PSI
#     the heat is doubled and from 27000 quadrupled, while the cooling is never
#     scaled (core_model_check.py has the check that says so).
#
# Two separate things make a pump level cheaper here than in the original -- his
# heat is steeper per unit of `a`, and the mean is a further factor of three --
# and they are worth keeping apart, because only the second one is this
# console's own doing.  The constant stays the measured 120 either way, and
# nothing is rescaled to make a ratio come out.
#
# "STEEPER PER UNIT OF `a`" NO LONGER HAS ONE NUMBER, and that is a change the
# quadratic made to the R11 table rather than a detail of it.  Against the
# original's own 65 per CBL level (2.6 per unit of `a`), the retired line was a
# flat 2.638x at every point -- that was row 1's slope, 6.86 / 2.6.  A quadratic
# has a slope that changes with where you measure: 1.42x at a = 25, 2.41x at
# 50, 5.38x at the top of the fit (14.0 / 2.6 -- an earlier draft of this comment
# said 5.39, which is what the number looks like before it is computed; the
# checker prints 5.38 for the same ratio).  So the divergence is now
# a function of the laser level, smallest exactly where his fit starts and
# largest where it ends, and any single multiplier quoted for it would be a
# reading taken at one point and reported as if it held everywhere.
COOLANT_PER_LEVEL = 120.0  # degrees a tick, per pump level
COOLANT_PUMPS = 3
# The game's own range: 0 (off) to 3, which is what `increasecoolantpumpNpower`
# clamps to and what Engine.luau:110 validates (`integer(value, 1, 3)`).
COOLANT_LEVELS = ((0, "off"), (1, "1"), (2, "2"), (3, "3"))

# His pMultiplier, as a table: the first limit the pressure is at or below wins,
# and past the last one the amplification is 4.  Replaces the old hand-set
# pressFactor bands ((2500, 1.15), (4000, 1.08)), which came from the Desmos
# sliders rather than from the wall he describes.
PRESS_AMP = ((11500.0, 1.0), (27000.0, 2.0))    # else 4.0

# (amplitude per CBL level, period).  His amplitudes, scaled by `a_eff / 25` --
# the MEAN of the three banks, since the 2026-10-16 correction, which is his own
# `15 * (a_eff / 25) * sin(t / 1.5)` written out; the 2026-10-13 version had
# these as flat 40/25/15 with no level term at all.
NOISE_TERMS = ((15.0, 1.5), (10.0, 0.7), (5.0, 0.3))

# The row thresholds, written the way the spec writes them:
#   s = {T < 5600: 0, T < 17500: 1, T < 29500: 2, 3}
# Row 0 IS in that rule as of the 2026-10-16 correction, and the number it puts
# there -- 5600 -- is the one this file already had: `STATE_MIN` above, which is
# `Config.Sim.State1` and Engine.luau:320's `T >= 5600 and 1 or 0`.  Before the
# correction the rule began at 17500 and row 0 was this file's own invention,
# kept because PASSIVE_ROW[0] is a measured number (-455.7 was the old
# BASE_RATE[0] -- the one entry that has survived three spellings of the heat)
# and because the row radios below are built from the table, so a row no
# temperature could reach would be a button that does nothing.  Two spellings of
# one threshold agreeing is a reading and not a coincidence, so it is checked
# (core_model_check.py asserts it against STATE_MIN rather than restating 5600).
#
# NOTE the spelling differs from Engine.luau:320's by one degree at each of the
# two upper boundaries, and that is the spec's spelling, not an accident: it says
# `T < 17500` where that line says `T > 17500`, so exactly 17500 is row 2 here
# and row 1 there, and exactly 29500 is row 3 here and row 2 there.  Both points
# are measure zero on a float run; recorded rather than smoothed over, because a
# silent one-degree drift between two spellings of one threshold is the kind of
# thing this file's own comments exist to prevent.
CORE_ROW_1_AT = 5600       # below this, row 0 (the cold machine) -- his `T < 5600`
CORE_ROW_2_AT = 17500      # <  is row 1; >= is row 2
CORE_ROW_3_AT = 29500      # <  is row 2; >= is row 3

# CBL power, at the levels Engine.luau:109 accepts (`integer(value, 1, 5)`).
# "off" is ours: the original has no off, and the spec's fit covers levels 1..5
# only.  Without a zero the model could never be told to stop, so off is defined
# as "add nothing" rather than by extrapolating the fit down to a = 0.  That
# rule now lives inside `pure_cbl`, as the spec spells it (`a_eff <= 0: 0`),
# which is also why a dark console can still lose heat at its row's rate: the
# gate is on the lasers' term and not on the row's.
CBL_LEVELS = ((0, "off"), (25, "PW1"), (50, "PW2"), (75, "PW3"),
              (100, "PW4"), (125, "PW5"))

# ========== THE ATMOSPHERE VENT BUTTON AND THE STALLOUT ==========
# The operator's 2026-10-16 spec fragment:
#
#     if pres <= 2200 then
#         fluc = -586 -- 实测失速暴跌速率
#     end
#     return fluc
#
# and the same message asked for an AVB button.  They are one feature: the
# AVB's cooling IS the stallout (the wiki's Atmosphere Vent Button page: "the
# biggest use ... is to intentionally induce a Pressure Stallout"), so the
# button has no temperature effect of its own and the rule is a property of
# the chamber.  That is also why they arrived together.
#
# `fluc` is the per-tick TEMPERATURE increment, and that is settled rather
# than guessed: Engine.luau:319 ends the same step with
# `s.fluctuation = s.temperature - before`, so in this project's own spelling
# of the game "fluctuation" is literally the temperature change of one tick.
# The stall line in the game is Engine.luau:313,
#
#     if s.pressure < c.Sim.StallPressure then s.temperature -= c.Sim.StallCooling end
#
# -- the same rule, on the same side of the equation, with 750 where he
# measured 586.  Two differences, recorded rather than smoothed:
#   * the comparison: the game uses `<`, his fragment uses `<=`, and the wiki's
#     prose says "less than 2200 PSI" -- so the tie is 2 to 1 against him.  One
#     PSI, at exactly 2200, kept as his because his is the spec written for THIS
#     console.  Measure zero on a float run -- the same kind of note as
#     CORE_ROW_2_AT's one degree.
#   * the rate: 750 is what THIS REMAKE's Config carries (`Sim.StallCooling`),
#     and 586 is what he measured off the original.  The console drew from the
#     original everywhere else, so 586 is what is modelled here and 750 is
#     where our own game differs.  The shipped log's six ordinary spin-downs
#     plunge -538 .. -801 a tick (the sample at the bottom of each dip; the
#     collapse at the end of the recording is a different regime and is left
#     out) -- a band that contains BOTH 586 and 750, so the log cannot break
#     the tie and does not claim to.  What breaks it is that the console is a
#     model of the original.  `_tools/avb_from_log.py` prints the band.
STALL_FLUC = -586.0        # his measured plunge, per tick

# The vent itself.  From the wiki's Atmosphere Vent Button page, and the drop
# is ALSO measured -- six AVB clicks in the shipped telemetry log
# (Data/DataCollection.Log), read as the one big pressure step near each click
# (a click lands between samples, so it has to be found as a discontinuity
# rather than off "the sample before and after"): 6702->3202, 4238->938,
# 4308->1008, 4654->1354, 4384->1084, 5016->1852.  Four land on exactly -3300;
# the other two are -3300 plus the chamber's own movement across the same
# interval (+200 and -136), which is what a click landing mid-tick looks like.
# `_tools/avb_from_log.py` prints those six, and the stall band below.
#
# WHICH number the console should carry was the one real question here: our
# own remake's Config (ReactorBackend.Config.Vent) says AtmosphereDrop = 3000
# and Cooldown = 26.  On the drop the wiki is not of one voice either -- it
# says "instantly reduces reactor pressure by 3300 PSI" twice and "around
# 3000" once -- but the 3300 is what the log measured four times out of six,
# and it is what the wiki's own 5500 threshold is made of (2200 + 3300).
# So the console models the original with 3300; our game was left alone
# (CLAUDE.md 1.4 #1) and both numbers are in QUESTIONS.md.
AVB_PSI_DROP = 3300.0      # one press, one-shot -- not per tick
AVB_STALLOUT_PSI = 2200.0  # at or below this the chamber stalls

# The cooldown, in TICKS -- and the unit is the whole story.  The wiki gives
# it twice over: "a cooldown of about 25-26 seconds, or around 15 reactor
# ticks".  Those are the same duration in two clocks, which puts a reactor
# tick at 25.5/15 = 1.7 s -- and THIS console's tick is the operator's own
# `calculation.luau` tick (`task.wait(1)`, the tick its `period` box is
# labelled after).  Every other per-tick number in this model is the
# original's PER-TICK value rather than a per-second one -- `FAN_DRAG = 60`
# is the wiki's own "60 PSI of pressure per core tick" -- so the cooldown is
# carried in that same currency: 15 reactor ticks.  Our Config's 26 is the
# same ~26 seconds spelled in ITS clock (a 1-second step), not a
# disagreement about the device; what that means for the ~1.7x faster wall
# clock of either model is a question, not a fix (QUESTIONS.md).
AVB_COOLDOWN_TICKS = 15
# The shipped log agrees with the seconds side: the gaps between its six
# presses are 26, 58, 27, 26, 36 s, so the button was unavailable for AT
# LEAST 26 s -- the smallest gap is the closest that log gets to a cooldown,
# and it lands on the wiki's 25-26 s.  `_tools/avb_from_log.py` prints them.
#
# KNOWN SIMPLIFICATION: the wiki says the cooldown is not a constant -- "Based
# on the State, the button will take longer to refresh after use, but will
# always reduce roughly the same amount of PSI".  A fixed 15 ticks is the
# state-1 reading of a state-dependent number, and the wiki gives no per-state
# values.  Written down rather than smoothed over (QUESTIONS.md).

# The wiki's third number is not a fourth rule.  It says the button "cannot
# cool the reactor if you press it at any PSI above 5500", and 5500 is exactly
# AVB_STALLOUT_PSI + AVB_PSI_DROP -- the highest pressure a single press can
# still take into stallout.  Derived here so the two can never drift apart,
# and the checker exercises both sides of it (a vent from 5500 stalls, a vent
# from 5501 does not).
AVB_NO_COOL_ABOVE = AVB_STALLOUT_PSI + AVB_PSI_DROP          # 5500

# ========== THE E-VENTS (Emergency Ventilators) ==========
# NOT the AVB above, and the difference cost a check to settle: the AVB lowers
# PRESSURE and cools only by inducing a stall; the E-Vents lower TEMPERATURE
# directly and do not touch pressure.  The wiki has two pages on them and they
# agree on every number this console needs:
#
#   "There are a total of 3 E-Vents."
#   "Each is controlled by its own switch on the Main Reactor Console."
#   "When one of the E-Vents is activated, $90.000 is subtracted from your
#    A.E.R.N. Report"
#   "E-Vents are only refilled after each shift."
#   "cool down the core by approximately 7000 degrees"
#
# So: three buttons, each usable ONCE per shift, each ~7000 F, no cooldown
# (the one-shot refill is the whole restriction -- no page mentions a timer,
# and inventing one would be inventing a device).  `Reset` is this console's
# new shift, so it refills them, exactly as a shift boundary does in the game.
# The money is reported, not modelled: this console has no economy.
E_VENT_COUNT = 3
E_VENT_DROP = 7000.0       # one activation, one-shot -- not per tick

# ========== MELTDOWN ==========
# The wiki's Temperature page ends its state table at
#   "State 4 (Meltdown) | >= 39,000 | - | Core meltdown, game over"
# and its Core States page says the same number with a caveat worth keeping:
#   "'State 4/METU Deployment' - 39,000F + (Not a state mentioned in the game,
#    thus the quotes.)"
# i.e. 39,000 is a threshold the COMMUNITY uses; the game itself does not print
# "State 4".  The console keeps `core_state()` at rows 0..3 (the operator's own
# `s` has exactly four entries and 39,000 is not one of its branches), and
# carries the crossing as a separate LATCH instead of a fifth row: a row would
# need a passive value nobody has written down, and the wiki says the
# temperature stops mattering at that point ("Power generation, temperature,
# and any other variable values are considered unimportant").
CORE_MELTDOWN_AT = 39000.0


def melted(temperature):
    """The wiki's `>= 39,000`: the core has melted down."""
    return temperature >= CORE_MELTDOWN_AT


def stalled(pressure):
    """His rule's gate, written once so the panel and the model cannot
    disagree about it: `pres <= 2200`.

    The boundary is his `<=`, not Engine.luau:313's `<`.  That is deliberate
    and it is now a minority vote: our remake's engine uses `<`, and the
    wiki's own prose says the stall is "making chamber pressure reach less
    than 2200 PSI".  Two sources say `<`, his spec says `<=`, and the two
    differ at exactly one PSI -- a measure-zero point on a float run.  His is
    the one written for THIS console, so his is the one implemented, and the
    1-PSI tie is recorded here rather than smoothed (the same kind of note as
    CORE_ROW_2_AT's one degree).
    """
    return pressure <= AVB_STALLOUT_PSI


def core_state(temperature):
    """The spec's `s`, and as of the 2026-10-16 correction that is all of it --
    his rule spells row 0 out (`T < 5600: 0`), where before it started at 17500
    and the row below was this file's own.

    A read of the temperature, so it is recomputed every tick and can fall.
    Not Sim.State: that one is latched and has no row below 5600.
    """
    if temperature < CORE_ROW_1_AT:
        return 0
    if temperature < CORE_ROW_2_AT:
        return 1
    if temperature < CORE_ROW_3_AT:
        return 2
    return 3


def pure_cbl(a_eff):
    """His `pure_cbl`: the lasers' own heating, `0.0516 a^2 + 1.1 a + 426`.

    A quadratic in `a_eff`, the wiki's weighted combination of the three banks,
    and THE ROW IS NOT IN IT.  Until the 2026-10-16 spec this term was one line
    per row (`active[row]`), so "which row" changed the slope of the heating as
    well as the offset; now it changes only the offset (`passive` below).

    The zero gate is in here, under the spec's own first branch
    (`a_eff <= 0: 0`).  It is this file's rule rather than a fit: his line is
    fitted over levels 1..5 and off is a position the original does not have, so
    rather than extrapolate down to a = 0 a dark console adds nothing at all.
    Being inside the curve rather than beside it is visible on the panel -- the
    tile reads 0, not 426 -- and it is the only reason the passive term can sit
    outside it and still leave a dark console cooling rather than heating.

    `a_eff ** 2`, not `a_eff * a_eff`: the two differ in the last bit for about
    0.2% of inputs (measured, and it is the same family as Python's `sum()` being
    a compensated sum, CLAUDE.md 0.33 (1)).  His literal is `a_eff^2`, which is
    `pow(a, 2)` in any language, so `**` is the spelling that matches it -- and
    the checker spells his formula with the same operator for the same reason.
    """
    if a_eff <= 0.0:
        return 0.0
    square, linear, constant = CBL_CURVE
    return square * a_eff ** 2 + linear * a_eff + constant


def passive(row):
    """His `passive`: what a row loses with nothing running, per tick.

    Outside the lasers' off rule and outside `p_mult` (see the constants block):
    a dark console falls at this rate and a high press band does not double it.

    Row 0 is the one entry with a history -- -455.7 was `BASE_RATE[0]` in the
    closed-form model this console ran before Phase 126, so the number survives
    its third spelling.  It matched the retired row-0 line exactly
    (`active[0] = (0, 0)`), which is how it was identified as the same quantity
    and not a new one.
    """
    return PASSIVE_ROW[row]


def press_multiplier(pressure):
    """His `pMultiplier`: at or below 11500 normal, at or below 27000 doubled,
    above that quadrupled -- the chamber pressure amplifying the temperature
    swing rather than replacing it."""
    for limit, factor in PRESS_AMP:
        if pressure <= limit:
            return factor
    return 4.0


PRESS_COLOURS = {"normal": "#202020", "high": "#8a5a00", "extreme": "#a00000"}


def press_band(pressure):
    """Which of the wiki's three bands the chamber is in: "normal", "high" or
    "extreme".

    Derived from PRESS_AMP rather than from a second copy of 11500 and 27000 --
    one source, so the colour on the panel cannot disagree with the multiplier
    the model used.  The wiki's table overlaps at exactly 27000 ("11500-27000"
    and ">= 27000"); this follows `press_multiplier`'s `<=`, which is the same
    reading the spec's `{P <= 27000: 2, 4}` takes, so 27000 is still HIGH.
    """
    for limit, factor in PRESS_AMP:
        if pressure <= limit:
            return "normal" if factor == 1.0 else "high"
    return "extreme"


def press_band_text(pressure):
    """The band, with the boundary it is under, for a readout value.

    The boundary is in the VALUE and not in the label: readouts are addressed by
    prefix, and a number in the address is a number a mutation can move out from
    under a checker (DECISIONS_2 583).
    """
    for limit, _factor in PRESS_AMP:
        if pressure <= limit:
            return "%s  (<= %g)" % (press_band(pressure), limit)
    return "%s  (> %g)" % (press_band(pressure), PRESS_AMP[-1][0])


def noise(x, a_eff):
    """His `noise(t)`: three sines instead of a random number, amplitude scaled
    by `a_eff / 25` -- the wiki's own spelling
    (`15 * (a_eff / 25) * sin(t / 1.5)`).

    `a_eff / 25` is no longer a "level": with the positional weights a_eff is a
    weighted sum, so all three banks at PW5 put this factor at 7.37 rather than
    at 5.  That is what the formula says and it is carried as written.

    Deliberately reproducible -- the same t has to give the same temperature, or
    there is nothing to compare a rerun against.  Unlike the 2026-10-13 version
    this is added to the READING, not multiplied into a rate, so its amplitude
    is what it says it is: +-15 degrees a term at one laser's worth, not +-15
    degrees per second.
    """
    level = a_eff / CBL_UNIT
    return sum(amplitude * level * math.sin(x / period)
               for amplitude, period in NOISE_TERMS)


def step_terms(row, a_eff, pressure, t, coolant=0.0):
    """What one tick adds, before it is added: (pure_cbl, passive, press, heat,
    noise, stall, cooling).

    ONE SPELLING OF THE RULE, called both by Core.step and by the panel's own
    "would add X/tick" preview.  Two spellings would let the promise and the
    behaviour drift apart, and the drift would be silent -- which is the exact
    failure CLAUDE.md 0.31 (1) is about.

    The order matters here and it is the operator's: the STALL OUT-RANKS
    everything else.  His rule is about the chamber, not about the lasers: at
    2200 PSI or below the reactor is stalled and the temperature falls at the
    measured 586 a tick whatever the row, the banks and the pressure multiplier
    say.  It is also the one case where the "off is ours" rule must NOT win --
    turning the lasers off does not un-stall a chamber, so a stalled tick stays
    negative with every bank dark.

    AND SINCE THE 2026-10-16 CORRECTION THE STALL IS THE WHOLE TICK.  His `dT`
    is piecewise -- `dT = {P <= 2200: -586, (pure_cbl * p_mult) + passive[s] -
    coolant_effect + noise}` -- so a stalled tick has no heat, no pump term and
    no tremor: it falls by exactly 586 and that is all.  The reading before the
    correction had the stall setting the RATE with the tremor still riding on
    the reading, which differs the moment the banks are lit; the two spellings
    are one line apart and QUESTIONS.md R12 carries the other one.

    Note what the stall's precedence buys the passive term: -586 is the whole
    tick, so a stalled chamber falls at the measured rate rather than at its
    row's -22 or -455.7, and the row stops mattering at exactly the moment the
    stall rule does.

    The first two numbers returned are the two halves of his heat, kept apart so
    the panel can show which one moved -- `pure_cbl` and `passive` are two
    different kinds of number (a fit and a measurement) and a single summed
    "baseFluc" tile would hide the one an operator is looking for.

    `coolant` comes in already averaged and multiplied (Core.cooling owns that
    arithmetic) rather than as three levels, so this function stays a function
    of the four numbers the step actually uses.
    """
    stall = stalled(pressure)
    amp = press_multiplier(pressure)
    if stall:
        # Every number here is one the panel has to be able to show: the tile
        # that says "noise 0" and the tick that moved by exactly -586 have to be
        # the same story (this file's own rule -- every readout is a term the
        # step actually used, and a term from a step that did not happen is what
        # `reset_trace` exists to prevent).  The two heat halves come back as 0
        # rather than as what they would have been, for the same reason: on this
        # tick there was no heat term, so the panel must not show one.
        return 0.0, 0.0, amp, STALL_FLUC, 0.0, True, 0.0
    # The "off is ours" gate is inside `pure_cbl` now (it used to be the ternary
    # that built `actual` here), and `a_eff` is zero when and only when all three
    # banks are, since every bank is a level and no level is negative -- the
    # weights are all positive, so a weighted sum of non-negative terms is zero
    # only at all-zero.  The PUMPS are not under that gate, nor under the row's:
    # a dark laser bank is no reason for a pump to stop pumping (the constants
    # block above has the placement argument, and what the log can and cannot say
    # about it).
    heat = pure_cbl(a_eff)
    # `p_mult` multiplies the ACTIVE heating only.  His note on that line says
    # so ("only multiplies the active heating"), and the placement is visible
    # twice: a high press band does not amplify a row's passive loss, and a dark
    # console -- whose `heat` is 0 -- has nothing for the band to multiply, so
    # the -400 of row 1 is -400 at every pressure.
    active = heat * amp
    # The tremor is the operator's own term and it rides on the READING (that
    # was the point of the 2026-10-14 revision).  It goes quiet by itself when
    # every bank is dark, because its amplitude is scaled by `a_eff / 25`.
    return heat, passive(row), amp, active, noise(t, a_eff), False, coolant


class Sim:
    """The five values the tick carries, plus what the display wants."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.Temperature = 5600.0
        self.Pressure = 6000.0
        self.ActiveFan = 0
        self.PEALevel = 1
        self.State = 1
        self.period = 1.0
        self.ticks = 0
        self.delta = 0.0
        # The vent's own state.  Presses are one-shot events, not a term in
        # `terms()`: the wiki's drop is 3300 on the press and nothing per tick,
        # so a button that stayed down would be a different device.
        self.vent_ticks = 0        # ticks of cooldown still to run
        self.vent_count = 0        # how many presses have landed
        self.last_vent_drop = 0.0  # what the last one actually took off
        # The three E-VENTS, separately from the AVB above.  One-shot each,
        # refilled by reset() -- which is this console's shift boundary, the
        # only thing the wiki says refills them.  `e_vent_count` is kept beside
        # the flags so a panel can say "1 of 3 used" without counting a list.
        self.e_vent_used = [False] * E_VENT_COUNT
        self.e_vent_count = 0
        self.last_e_vent_drop = 0.0

    @property
    def elapsed(self):
        return self.ticks * self.period

    @property
    def band(self):
        return BANDS.get(self.State, "?")

    def terms(self):
        """The four terms of p = g - 60n + s t + d, separately.  The display
        and the tick both read this, so a tile cannot show a term that the sum
        did not use."""
        return (STATE_GAIN[self.State],
                SLOPE[self.State] * self.Temperature,
                PEA_GAIN[self.PEALevel],
                -FAN_DRAG * self.ActiveFan)

    @property
    def can_vent(self):
        return self.vent_ticks <= 0

    def vent(self):
        """Press the Atmosphere Vent Button.  Returns the PSI actually removed,
        or None when the button is still on cooldown.

        The number applied is `AVB_NO_COOL_ABOVE`'s, not the wiki's -- that 5500
        is a statement about what the button ACHIEVES, and the achievement is the
        stall.  There is no separate "will not cool" branch to write, because the
        only reason to press this button is the 2200 floor and the drop is what
        takes you to it.  What the floor itself does to the temperature is
        `STALL_FLUC`'s job, down in Core.step.

        The clamp at 0 is the only place the two numbers can disagree with the
        wiki's arithmetic: from 1000 PSI a "3300 drop" would go negative, and
        pressure is floored at 0 in the game (Engine.luau's final
        `math.max(0, ...)`).  What the caller gets back is what actually moved,
        so a log line cannot claim a drop the chamber never felt.
        """
        if not self.can_vent:
            return None
        before = self.Pressure
        self.Pressure = max(0.0, before - AVB_PSI_DROP)
        self.vent_ticks = AVB_COOLDOWN_TICKS
        self.vent_count += 1
        self.last_vent_drop = before - self.Pressure
        return self.last_vent_drop

    def can_e_vent(self, index):
        return 0 <= index < E_VENT_COUNT and not self.e_vent_used[index]

    def e_vent(self, index):
        """Fire E-Vent `index`.  Returns the degrees Fahrenheit actually removed
        -- floored at TEMP_MIN -- or None when that vent is already spent.

        The clamp is the same discipline as `vent()`'s pressure floor: from
        3,000 F a "7000 degree" activation cannot remove 7000, and a log line
        must not claim a drop the core never felt.  The wiki says
        "approximately 7000", so the exact number is this constant and the
        approximation is the wiki's word for it.

        Applied HERE rather than in Core.step because it is a button, not a
        term: it happens between ticks, it happens once, and a per-tick term
        would turn 7000 into 7000 a tick.
        """
        if not self.can_e_vent(index):
            return None
        before = self.Temperature
        self.Temperature = max(TEMP_MIN, before - E_VENT_DROP)
        self.e_vent_used[index] = True
        self.e_vent_count += 1
        self.last_e_vent_drop = before - self.Temperature
        return self.last_e_vent_drop

    def tick(self):
        # Latched, not derived: the original's if/elseif chain has no `else`,
        # so a Temperature below 5600 leaves the previous State standing.
        if STATE_MIN <= self.Temperature < STATE_1_MAX:
            self.State = 1
        elif STATE_1_MAX <= self.Temperature <= STATE_2_MAX:
            self.State = 2
        elif self.Temperature > STATE_2_MAX:
            self.State = 3

        self.delta = sum(self.terms())
        self.Pressure += self.delta
        self.ticks += 1
        # The cooldown runs on ticks, not seconds -- the same unit the console
        # already uses for the fans (FAN_DRAG is the wiki's "60 PSI per core
        # tick").  The wiki gives both spellings of the same wait ("about 25-26
        # seconds, or around 15 ticks"), so on the tick count the console can
        # honour exactly, its cooldown is 15 and not 26.
        if self.vent_ticks > 0:
            self.vent_ticks -= 1


class Core:
    """The operator's temperature model, driving Sim.Temperature.

    His equation, literally (2026-10-16, second revision that day), with the
    input line replaced on 2026-10-24 by the wiki's own (Phase 148):

        a_eff       = 0.756*c1 + 0.522*c2 + 0.196*c3   (was ((c1+c2+c3)/3)*25)
        pure_cbl    = {a_eff <= 0: 0, 0.0516*a_eff^2 + 1.1*a_eff + 426}
        passive     = [-455.7, -400, -422, -22]         indexed by `s`
        coolant     = ((p1 + p2 + p3) / 3) * 120
        dT = {P <= 2200: -586,
              (pure_cbl * p_mult) + passive[s] - coolant + noise}    otherwise
        T' = T + dT

    with `p_mult` his pressure bands (multiplying the ACTIVE heating only) and
    `t` = seconds since armed.  (The coolant term's unit moved three times on
    2026-10-16 -- divided, then not, then divided again -- and the order with its
    dates is in the constants block above, which is the one place keeping the
    whole list.  The reading checked is the one his own message spells:
    `coolant_avg = (p_1 + p_2 + p_3) / 3`, then `x 120`.)
    The helpers above are the named parts of it, so this class is only
    the order they are applied in.  (The 2026-10-14 spelling was
    `T' = T + baseFluc * pMultiplier + noise(t)`; what the two corrections since
    added is the first branch, spelled as the whole of `dT`, and the split of
    `base_heat` into a curve that ignores the row and a row constant that does
    not.)

    It is a STEP, and that is the whole of the revision.  What it replaced was a
    closed form, `T0 + (rate + noise)*x`: a line through T0, whose slope the row
    picked, recomputed from scratch every tick.  All three of the things wrong
    with that were known while it was in use -- the docstring here said so -- and
    the spec fixes each one:

      * `noise(x)` was INSIDE the multiplication, so it was a tremor on the slope
        and not on the reading: at x = 100 the +-80 degree wobble was a +-8000
        degree spread, and two runs that differed only in where you stopped were
        hundreds of degrees apart.  The spec puts it outside, added to T.
      * the rate table was one level-averaged number per row, so the CBL could
        only scale it.  That is also why the old table had no `a` in it at all
        while the CBL control moved a multiplier beside it.  The spec fits `pure_cbl`
        against the LEVEL 1-5 logs, so the lasers' heat is a curve in `a`.
      * a row change moved the WHOLE line: the reading jumped by (new rate - old
        rate) * x, which crossing 2 -> 3 was about nineteen thousand degrees.
        That is a property of a line through T0, not of a reactor.  A step has no
        such jump; what a row change does here is change the increment.

    The noise amplitudes went from flat 40/25/15 to 15/10/5 x level, and the
    hand-set pressFactor bands to his pMultiplier (1/2/4).  Same sines, same
    periods, same row thresholds, and the old row-0 number survives verbatim --
    `PASSIVE_ROW[0]` is -455.7, which was `BASE_RATE[0]`.  This is his model
    refined, not a different one.

    REVISED AGAIN 2026-10-16 (Phase 140), and this is the deepest change the
    model has had.  Two things in it, one arithmetic and one behavioural:

      * the heat stopped being one line per row.  `active[row]` is gone; what is
        left is a single quadratic, `pure_cbl`, which does not know what row it
        is in, plus `passive[s]`, which does nothing else.  A row change used to
        change the SLOPE of the heating; it now changes only the offset.  The
        four retired lines and their passive table are kept in the constants
        block, and a mutant puts them back -- a reading that was reversed out
        must not become unfalsifiable (CLAUDE.md 0.34 (4)).
      * `passive` moved OUT of the lasers' off rule and out of `p_mult`.  This is
        the one that changes what the panel does rather than how it computes:
        with every bank dark this console now COOLS at its row's rate (400 a tick
        at row 1) where it has always held still, and the pressure band no longer
        amplifies the row's loss.  Both are his spec's placement; what the
        shipped log can say about the first is a negative result (constants block
        above), so it is implemented as written.

    THE EARLIER REVISION OF THE SAME DAY (Phase 137) is still in force except
    where the one above overrides it, and two of its three moves are in this
    class:

      * `a` went from the SUM of the three banks to their MEAN (`a_avg`), and
        the top of the fit went with it: `a = 375` is unreachable by construction
        now, its ceiling is 125 = all three at PW5.  That dissolves the
        extrapolation R9 (2) was carrying rather than answering it.
        PHASE 148 REPLACED THE MEAN with the wiki's positional weights, and that
        ceiling goes back up: `a_eff` reaches 184.25 with all three at PW5, past
        the 25..125 band the fit covers.  The extrapolation R9 (2) retired is
        therefore open again at the top, and it is carried rather than clamped
        (constants block above).
      * the pumps were averaged in the same message -- then not, then averaged
        again, so `120 x (p1 + p2 + p3) / 3` is where they ended: 360 for three
        maxed pumps.  The three moves are in the constants block above with
        their phases; what is worth repeating here is that ONLY the pumps' unit
        ever moved.  The banks' mean has been in every version since the
        correction, because it is about a fitted band covering one laser's worth
        of `a`; the pumps have no band to stay inside, so their unit is the
        operator's call, and he has now made it twice one way and once the
        other.
      * the third is a READING and not arithmetic -- his `dT` is piecewise, so a
        stalled tick is his -586 with no heat, no pump term and no tremor, where
        Phase 135 read the -586 as the rate with the tremor still riding on the
        reading.  QUESTIONS.md R12 has both spellings and the one line between
        them.

    One thing the correction did NOT move, and it is worth saying because the
    numbers around it all changed: `T < 5600: 0` is the first branch of his `s`
    and this file already had 5600 at `CORE_ROW_1_AT`, from `Config.Sim.State1`
    and Engine.luau:320's `T >= 5600 and 1 or 0`.  Three sources, one number, so
    it is checked against `STATE_MIN` rather than restated.

    Arming is what makes it live.  The slider is this file's own way of setting a
    temperature and the model is a way of computing one; they cannot both be in
    charge of one number, so the model is armed rather than installed, and with
    the box unticked not one line below runs.
    """

    def __init__(self):
        self.armed = False
        self.auto = True
        # Three banks, each 0..125 in steps of 25.  The control POSITION is where
        # it always was -- PW2 on the first bank, the other two dark -- and since
        # Phase 148 that position reads a_eff = 0.756 * 50 = 37.8, because the
        # first bank is the heavy one.  (Under the mean it read 50/3 = 16.67.)
        # The panel's opening READING has moved with every reading of the input
        # line and it keeps moving; the default is deliberately not moved to
        # defend the old number -- a control position chosen to make a readout
        # come out right is the same mistake as a ruler chosen to make a
        # measurement come out right.
        self.banks = [CBL_START] + [0.0] * (CBL_BANKS - 1)
        # Three coolant pumps, each 0..3, all off at start -- which is where the
        # game starts them and where this console started before they existed,
        # so opening the panel shows the same temperature as it always did.
        self.pumps = [0] * COOLANT_PUMPS
        self.state = 0            # the row held by hand, when auto is off
        self.t = 0.0              # his t: seconds elapsed since armed
        # The wiki's >= 39,000 latch.  A LATCH and not a row: see
        # CORE_MELTDOWN_AT -- the row table stops at 3 and the wiki says the
        # temperature stops mattering past this point.  Cleared by rearm().
        self.melted = False
        self.reset_trace()

    @property
    def a_eff(self):
        """The wiki's `a_eff`: the three banks under their positional weights.

            a_eff = 0.756 * L1 + 0.522 * L2 + 0.196 * L3

        `L1..L3` are the bank VALUES (0, 25, 50, 75, 100, 125) -- the wiki says
        "the power values of CBL 1, 2, and 3: 25, 50, 75, 100, or 125", so the
        coefficients multiply the values directly and no /25 rescaled "level" is
        introduced.  Summed LITERALLY, left to right, in the wiki's own order:

        `sum()` is a compensated (Neumaier) sum in CPython 3.12+ and gives a
        last-bit different answer from `w1*c1 + w2*c2 + w3*c3` (CLAUDE.md 0.33
        (1), measured at 7.1e-15 on the retired mean).  The checker spells the
        same expression independently with the same operators, so both sides
        round the same way and the comparison stays exact.

        A property rather than a stored number, because a stored a_eff is a
        second copy of something the banks already say and the two could drift.
        Every reader -- `pure_cbl`, `noise`, the readouts -- asks for it.

        FOURTH READING of this one line: sum (Phase 136), mean (operator,
        2026-10-16), sum (operator, 2026-10-16), mean (operator, 2026-10-16),
        and now the wiki's weights from its own Temperature page.  The earlier
        spellings are mutants in core_model_mutants.py rather than history.
        """
        w1, w2, w3 = CBL_WEIGHTS
        return w1 * self.banks[0] + w2 * self.banks[1] + w3 * self.banks[2]

    def set_bank(self, index, value):
        self.banks[index] = float(value)

    @property
    def cooling(self):
        """What the pumps take off, per tick: his `coolant_avg * 120`.

        The same shape as `power` and for the same reason: a stored mean is a
        second copy of something the three widgets already say, and the copy is
        the one that goes stale.  Positive here, because that is what it is --
        the subtraction happens in one place, in `step_terms`, so the sign
        cannot be applied twice.

        THIS IS THE LINE THAT MOVED THREE TIMES on 2026-10-16 -- his message
        spelled it this way, the next took the division off the pumps alone, and
        the one after that put it back.  The constants block above keeps the
        whole list with its phases; CLAUDE.md 0.34 is the reason it is kept
        there rather than summarised as "the latest word": a spec visited more
        than once gets asked WHICH LINES it reaches, and the answer has been
        this line every time.  It is spelled as his literal -- `sum / 3`, then
        `x 120` -- rather than as an algebraically equal rearrangement, so a
        fourth visit cannot land on a differently-rounded way of writing the
        same thing.

        The constant is untouched at the measured 120; what moved is the unit it
        multiplies, from three pumps to one average pump.  One notch on each of
        three pumps therefore takes off 120 here, where the sources' own
        arithmetic says 360 for the same three positions -- that factor of
        exactly three is the whole of the cooling side of QUESTIONS.md R11.
        """
        coolant_avg = sum(self.pumps) / float(COOLANT_PUMPS)
        return coolant_avg * COOLANT_PER_LEVEL

    def set_pump(self, index, value):
        self.pumps[index] = int(value)

    def reset_trace(self):
        """The last step's numbers, for the readout.  Cleared rather than zeroed,
        so a tile cannot show a term belonging to a step that never happened."""
        self.last_row = None
        self.last_heat = 0.0
        self.last_passive = 0.0
        self.last_amp = 1.0
        self.last_actual = 0.0
        self.last_noise = 0.0
        self.last_start = 0.0
        self.last_temperature = 0.0
        # The stall, as the step found it.  `last_pressure` is kept so the
        # readout can be re-checked against its own gate: the tile that says
        # "stalled" and the number it was stalled at come from one tick, and
        # `stalled(last_pressure) == last_stall` is an invariant the checker
        # asserts rather than a coincidence it hopes for.
        self.last_pressure = 0.0
        self.last_stall = False
        self.last_cooling = 0.0
    def rearm(self, sim):
        """Put his t back to 0.

        There is no T0 to take any more: a step has nothing to re-anchor, because
        the temperature is carried by Sim and the model only ever adds to it.
        What arming restarts is the clock the noise rides on, so two runs of the
        same length see the same tremor.  `sim` is still passed in because the
        caller has one and because a future anchor would need it -- not because
        anything below reads it.
        """
        self.t = 0.0
        self.melted = False
        self.reset_trace()

    def row(self, sim):
        return core_state(sim.Temperature) if self.auto else self.state

    def step(self, sim):
        """One tick.  Returns the temperature the model wants, None when off.

        Called BEFORE sim.tick(), which is the order Engine.luau uses: the
        temperature moves first, and the pressure state is read off the
        temperature the same tick ended with, so the next tick's row comes off
        the value this one produced.

        t is accumulated rather than derived from `ticks * period`, because the
        period is a control: changing it halfway would otherwise rewrite the
        whole run's elapsed time, including the part already drawn.
        """
        if not self.armed:
            return None
        # The meltdown latch, BEFORE the step: once the core is past 39,000 the
        # wiki says "temperature ... considered unimportant", so the console
        # stops moving the number rather than modelling a state whose passive
        # rate nobody has published.  The CROSSING tick still reports its
        # temperature -- the reading that melted it is the last honest one --
        # and every tick after returns None, which is the same "no step" the
        # console already uses for an unarmed model.
        if self.melted:
            return None
        self.t += sim.period
        row = self.row(sim)
        # `sim.Pressure` here is the tick's own STARTING pressure, because this
        # runs before Sim.tick().  Engine.luau tests the stall against the
        # pressure AFTER that tick's update -- one tick later in the same story.
        # The console keeps the starting value, because that is the number on
        # the screen at the moment the operator presses Step and the readout
        # re-checks its own tile with it; mixing the two instants is how a
        # screen stops adding up (CLAUDE.md 0.27, second face).
        heat, passiv, amp, actual, tremor, stall, cooling = step_terms(
            row, self.a_eff, sim.Pressure, self.t, self.cooling)
        # Four terms by name rather than one sum: `passive` is a row constant and
        # `actual` is the lasers' heat after the band, and a reader has to be
        # able to see which of them moved (the panel shows all four).
        temperature = sim.Temperature + actual + passiv + tremor - cooling
        self.last_row = row
        self.last_heat = heat
        self.last_passive = passiv
        self.last_amp = amp
        self.last_actual = actual
        self.last_noise = tremor
        self.last_cooling = cooling
        self.last_start = sim.Temperature
        self.last_temperature = temperature
        self.last_pressure = sim.Pressure
        self.last_stall = stall
        if melted(temperature):
            self.melted = True
        return temperature


# ========== THE WINDOW ==========

class Console:
    TITLE = "Reactor console - calculation.py"
    MONO = ("Consolas", 11)
    MONO_BIG = ("Consolas", 22, "bold")
    BOLD = ("Segoe UI", 9, "bold")

    #: A Text widget that only ever grows is a memory leak with a scrollbar on.
    LOG_MAX_LINES = 2000

    def __init__(self, root):
        self.root = root
        root.title(self.TITLE)
        root.minsize(820, 600)

        self.sim = Sim()
        self.core = Core()
        self.readouts = []          # [(StringVar, callable)]
        self.readout_widgets = {}   # label -> ttk.Label, for look-as-reading

        # The wiki's three pressure bands, as colour.  A LIGHT theme, so
        # "normal" is the theme's own ink rather than white (the wiki's "white
        # pressure" describes the GAME's dark screen, and copying that word here
        # would paint an invisible number on a white panel -- CLAUDE.md 0.32's
        # lesson about copying the sentence instead of the thing).  High and
        # extreme are dark amber and dark red: legible on white, and ordered by
        # weight the way the bands are.
        self._style = ttk.Style(root)
        for band, colour in PRESS_COLOURS.items():
            self._style.configure("Press_%s.TLabel" % band, foreground=colour)
        self.running = True
        self._after = None

        # One variable per control: Tk holds the shown value, the model is
        # written from the callback.  Never the other way round, so the two
        # cannot disagree about what was clicked.
        self.pea_var = tk.IntVar(value=self.sim.PEALevel)
        self.fan_var = tk.IntVar(value=self.sim.ActiveFan)
        self.period_var = tk.DoubleVar(value=self.sim.period)

        # The core model's own controls.  Its state lives in Core, but every
        # widget needs a variable to read its position from.
        self.arm_var = tk.BooleanVar(value=self.core.armed)
        # One variable per laser bank, not one for "the CBL level": there are
        # three devices down there and the panel has to be able to hold them at
        # three different powers.
        self.cbl_vars = [tk.IntVar(value=int(bank)) for bank in self.core.banks]
        # Same again for the coolant pumps: three devices, three variables, and
        # the model consumes their mean.
        self.pump_vars = [tk.IntVar(value=int(pump)) for pump in self.core.pumps]
        self.core_var = tk.IntVar(value=self.core.state)
        self.auto_var = tk.BooleanVar(value=self.core.auto)
        self.core_text = tk.StringVar()

        # The vent's own widgets, so its cooldown can be shown and the button
        # taken out of service while it runs.
        self.vent_button = None
        self.vent_text = tk.StringVar()
        self.e_vent_buttons = []
        self.e_vent_text = tk.StringVar()

        # The two temperature widgets are held so the model can take them out of
        # service while it is armed -- see _sync_core_widgets.
        self.temp_slider = None
        self.temp_spin = None
        self.core_buttons = []

        # Temperature is the one control with two widgets, so it gets two
        # variables rather than one shared.  A DoubleVar holds the slider's
        # fractional position, and its string form is "5604.0" -- which is what
        # a spinbox sharing it would print.  The box needs the integer, so it
        # keeps its own StringVar, written only from here.  The two cannot
        # drift: everything that changes the model goes through
        # _set_temperature, which writes the box, and the box path is the only
        # one that writes the slider back.
        self.temp_var = tk.DoubleVar(value=self.sim.Temperature)
        self.temp_box = tk.StringVar(value=shown(self.sim.Temperature))

        self._build()
        self.log("# %s" % self.TITLE)
        self.log("# a bare 'Pressure: N' line is the .luau's own output; "
                 "lines starting with # are commentary")
        self._refresh()
        self._schedule()

    # ----- layout -----

    def _build(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="both", expand=True)
        top.columnconfigure(0, weight=0, minsize=400)
        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)

        left = ttk.Frame(top)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._build_controls(left)

        right = ttk.Frame(top)
        right.grid(row=0, column=1, sticky="nsew")
        self._build_readouts(right)

        self._build_log()

    def _build_controls(self, parent):
        ttk.Label(parent, text="CONTROLS", font=self.BOLD).pack(anchor="w")

        # A radiobutton row is the fast switcher: one click, one level, and the
        # selected button is visible afterwards.  The PEA captions are built
        # from the table itself so they cannot describe a different number.
        pea = ttk.LabelFrame(parent, text="PEA level", padding=6)
        pea.pack(fill="x", pady=4)
        for level in sorted(PEA_GAIN):
            ttk.Radiobutton(pea, text="%d  (+%g)" % (level, PEA_GAIN[level]),
                            value=level, variable=self.pea_var,
                            command=self.on_pea).pack(side="left", padx=2)

        fan = ttk.LabelFrame(parent, text="Active fans (each is -%g)" % FAN_DRAG,
                             padding=6)
        fan.pack(fill="x", pady=4)
        for count in range(0, 7):
            ttk.Radiobutton(fan, text=str(count), value=count,
                            variable=self.fan_var,
                            command=self.on_fan).pack(side="left", padx=2)

        # The Atmosphere Vent Button, beside the fans because it is the other
        # thing that moves pressure -- and it is NOT a term in the sum above:
        # it is a one-shot event, so it could not be a row of radios even if it
        # wanted to be.  The cooldown is shown as a number rather than as a
        # disabled button alone, because "you cannot press this" and "this
        # thing has no function" look the same on a greyed-out widget
        # (CLAUDE.md 0.19's family).
        avb = ttk.LabelFrame(parent, text="Atmosphere vent (AVB)", padding=6)
        avb.pack(fill="x", pady=4)
        self.vent_button = ttk.Button(avb, text="VENT  -%g PSI" % AVB_PSI_DROP,
                                      command=self.on_vent)
        self.vent_button.pack(side="left")
        ttk.Label(avb, textvariable=self.vent_text, font=self.MONO,
                  ).pack(side="left", padx=(8, 0))
        ttk.Label(avb, text="stall at %g; no cooling above %g"
                  % (AVB_STALLOUT_PSI, AVB_NO_COOL_ABOVE),
                  font=self.MONO).pack(side="left", padx=(10, 0))

        # THE E-VENTS.  A different device from the AVB above: they take 7,000 F
        # off the core directly and touch no pressure, there are three of them,
        # and each is spent once per shift -- so a "used" state has to be
        # VISIBLE, not just a disabled widget (CLAUDE.md 0.19's family again:
        # "spent" and "broken" would otherwise look the same).
        ev = ttk.LabelFrame(parent, text="E-Vents (emergency coolant)",
                            padding=6)
        ev.pack(fill="x", pady=4)
        self.e_vent_buttons = []
        for index in range(E_VENT_COUNT):
            button = ttk.Button(
                ev, text="E-VENT %d  -%g F" % (index + 1, E_VENT_DROP),
                command=lambda i=index: self.on_e_vent(i))
            button.pack(side="left", padx=(0, 4))
            self.e_vent_buttons.append(button)
        ttk.Label(ev, textvariable=self.e_vent_text, font=self.MONO,
                  ).pack(side="left", padx=(8, 0))

        temp = ttk.LabelFrame(parent, text="Temperature", padding=6)
        temp.pack(fill="x", pady=4)
        # A slider cannot step by 1: ttk::scale has no -resolution (that is the
        # classic tk scale's option) and no -increment either, so its steps are
        # pixel-sized -- here 40000 over a 300-pixel widget, so 133 degrees per
        # pixel.  That width is the layout's, not a choice: it was 293 and 137
        # degrees per pixel until the redundant `temp_value` label beside the
        # slider came out, and nothing in the code would have said so.  The
        # spinbox is what makes "interval 1" true: it is the control you can
        # hold an exact number in, and it is the same widget the tick period
        # below already uses.  Both write the model through on_temp.
        row = ttk.Frame(temp)
        row.pack(fill="x")
        self.temp_slider = ttk.Scale(row, from_=TEMP_MIN, to=TEMP_MAX,
                                     variable=self.temp_var, command=self.on_temp)
        self.temp_slider.pack(side="left", fill="x", expand=True)
        self.temp_spin = ttk.Spinbox(row, from_=TEMP_MIN, to=TEMP_MAX, increment=1,
                                     width=7, format="%.0f",
                                     textvariable=self.temp_box,
                                     command=self.on_temp_box)
        self.temp_spin.pack(side="left", padx=(6, 0))
        # The arrows apply themselves, but a typed number sits in the box until
        # something reads it.  Enter and leaving the box both apply it, so a
        # typed temperature can never be silently ignored.
        self.temp_spin.bind("<Return>", lambda _event: self.on_temp_box())
        self.temp_spin.bind("<FocusOut>", lambda _event: self.on_temp_box())

        self._build_core_controls(parent)

        period = ttk.LabelFrame(parent, text="Tick period (the .luau waits 1)",
                                padding=6)
        period.pack(fill="x", pady=4)
        spin = ttk.Spinbox(period, from_=0.05, to=10.0, increment=0.05, width=8,
                           textvariable=self.period_var, command=self.on_period)
        spin.pack(side="left")
        spin.bind("<Return>", lambda _event: self.on_period())
        ttk.Label(period, text="seconds").pack(side="left", padx=6)

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", pady=(12, 0))
        self.pause_button = ttk.Button(buttons, text="Pause", width=8,
                                       command=self.toggle_run)
        self.pause_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="Step", width=8,
                   command=self.step_once).pack(side="left", padx=2)
        ttk.Button(buttons, text="Reset", width=8,
                   command=self.reset).pack(side="left", padx=2)

        self.status = ttk.Label(parent, text="", font=self.MONO, anchor="w")
        self.status.pack(fill="x", pady=(12, 0))

    def _build_core_controls(self, parent):
        core = ttk.LabelFrame(parent, text="Core model (temperature)", padding=6)
        core.pack(fill="x", pady=4)
        ttk.Checkbutton(core, text="armed - T comes from the model, not the slider",
                        variable=self.arm_var,
                        command=self.on_arm).pack(anchor="w")

        # A row of radiobuttons per choice, for the same reason PEA and the fans
        # use one: one click, one value, and what is selected stays visible.  The
        # captions come from the table, so a button cannot name a power the model
        # does not use.
        #
        # ONE ROW PER LASER.  The game has three and each carries its own
        # PW1..PW5, so a single "CBL" row would be a control the reactor does not
        # have.  The model consumes their WEIGHTED sum -- see CBL_WEIGHTS -- and
        # since Phase 148 the panel computes that rather than assuming the banks
        # are interchangeable.
        power = ttk.LabelFrame(
            core, text="CBL banks (a = 0.756 L1 + 0.522 L2 + 0.196 L3)",
            padding=6)
        power.pack(fill="x", pady=(4, 0))
        for index, var in enumerate(self.cbl_vars):
            line = ttk.Frame(power)
            line.pack(fill="x")
            ttk.Label(line, text="CBL %d" % (index + 1), width=6,
                      ).pack(side="left")
            for value, name in CBL_LEVELS:
                ttk.Radiobutton(line, text=name, value=value, variable=var,
                                command=self.on_power).pack(side="left", padx=2)

        # The third control means, beside the other two things that move the
        # temperature.  Three pumps, each 0..3 -- the game's own range, and one
        # row per pump for the same reason the lasers got one: "the coolant
        # level" is three devices, not one knob.  The caption carries the
        # constant and says what it multiplies -- the MEAN of the three.  (It
        # said "total" for one message of 2026-10-16, between the two spellings
        # of the model; the caption is the one place the panel says the unit in
        # words, so it has had to move with the model every time.)
        pumps = ttk.LabelFrame(
            core, text="Coolant pumps (Isotope E, -%g x mean level /tick)"
            % COOLANT_PER_LEVEL, padding=6)
        pumps.pack(fill="x", pady=(4, 0))
        for index, var in enumerate(self.pump_vars):
            line = ttk.Frame(pumps)
            line.pack(fill="x")
            ttk.Label(line, text="C-PUMP %d" % (index + 1), width=9,
                      ).pack(side="left")
            for value, name in COOLANT_LEVELS:
                ttk.Radiobutton(line, text=name, value=value, variable=var,
                                command=self.on_coolant).pack(side="left", padx=2)

        rows = ttk.Frame(core)
        rows.pack(fill="x", pady=(2, 0))
        ttk.Label(rows, text="row").pack(side="left")
        for value in range(len(PASSIVE_ROW)):
            button = ttk.Radiobutton(rows, text=str(value), value=value,
                                     variable=self.core_var,
                                     command=self.on_core_state)
            button.pack(side="left", padx=2)
            self.core_buttons.append(button)
        ttk.Checkbutton(rows, text="auto (follow Temperature)", variable=self.auto_var,
                        command=self.on_auto).pack(side="left", padx=(10, 0))

        ttk.Label(core, textvariable=self.core_text, font=self.MONO,
                  justify="left", anchor="w").pack(fill="x", pady=(4, 0))
        self._sync_core_widgets()

    def _sync_core_widgets(self):
        """Keep the controls saying which of them currently owns the temperature.

        Disabling is not decoration: the model writes a float every tick, and a
        slider whose thumb was left somewhere else would drag it back on the next
        click.  The row buttons go the same way while `auto` is ticked, because a
        row the model is choosing is not one you can also be holding.
        """
        temperature_state = "disabled" if self.core.armed else "normal"
        self.temp_slider.configure(state=temperature_state)
        self.temp_spin.configure(state=temperature_state)
        row_state = "disabled" if self.core.auto else "normal"
        for button in self.core_buttons:
            button.configure(state=row_state)

    def add_readout(self, parent, row, label, getter, big=False):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=1)
        var = tk.StringVar()
        widget = ttk.Label(parent, textvariable=var, anchor="e",
                           font=self.MONO_BIG if big else self.MONO)
        widget.grid(row=row, column=1, sticky="e", padx=(12, 0))
        self.readouts.append((var, getter))
        # Kept by label so a readout whose LOOK is part of its reading can be
        # restyled in _refresh -- the pressure band is the first one (its colour
        # is the wiki's own three-band table, and a number alone would make the
        # operator read the bands off a table instead of off the panel).
        self.readout_widgets[label] = widget
        return row + 1

    def _build_readouts(self, parent):
        parent.columnconfigure(1, weight=1)
        ttk.Label(parent, text="VALUES", font=self.BOLD,
                  ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        row = 1
        row = self.add_readout(parent, row, "Pressure",
                               lambda: shown(self.sim.Pressure), big=True)
        row = self.add_readout(parent, row, "Delta this tick",
                               lambda: shown(self.sim.delta))
        # Two different quantities are both called "state" -- see the CORE MODEL
        # block.  This one is latched from the pressure and is what the slope
        # tables below are keyed by; the other is a pure read of the temperature.
        row = self.add_readout(parent, row, "Pressure state (latched)",
                               lambda: str(self.sim.State))
        row = self.add_readout(parent, row, "State band",
                               lambda: self.sim.band)
        row = self.add_readout(parent, row, "Core state (from Temperature)",
                               lambda: str(core_state(self.sim.Temperature)))
        row = self.add_readout(parent, row, "Temperature",
                               lambda: shown(self.sim.Temperature))
        row = self.add_readout(parent, row, "Ticks",
                               lambda: str(self.sim.ticks))
        row = self.add_readout(parent, row, "Elapsed",
                               lambda: shown(self.sim.elapsed))
        row = self.add_readout(parent, row, "Tick period",
                               lambda: luau_number(self.sim.period))
        # The vent and the stall, read live: this is the pressure the NEXT step
        # will gate on, so it is the number the operator is deciding with.
        row = self.add_readout(parent, row, "stallout  pres <= %g" % AVB_STALLOUT_PSI,
                               lambda: "STALLED" if stalled(self.sim.Pressure)
                               else "no")
        row = self.add_readout(parent, row, "vent  cooldown left (ticks)",
                               lambda: str(self.sim.vent_ticks))
        # Dashed until a press has landed, so a 0 cannot be read as "the vent
        # did nothing" when in fact it has not been pressed.
        row = self.add_readout(parent, row, "vent  last drop (PSI)",
                               lambda: "-" if not self.sim.vent_count
                               else shown(self.sim.last_vent_drop))
        # The E-VENTS, on the same discipline as the AVB: a count that says how
        # many are left, and a dash until one has fired so a 0 cannot be read as
        # "it did nothing".  The label carries no constant -- a number in the
        # label is a number in the ADDRESS, which is how a mutant once crashed a
        # checker instead of reddening it (DECISIONS_2 583).
        row = self.add_readout(parent, row, "e-vents  left of 3 this shift",
                               lambda: "%d of %d" % (
                                   E_VENT_COUNT - self.sim.e_vent_count,
                                   E_VENT_COUNT))
        row = self.add_readout(parent, row, "e-vent  last drop (F)",
                               lambda: "-" if not self.sim.e_vent_count
                               else shown(self.sim.last_e_vent_drop))
        row = self.add_readout(parent, row, "press band",
                               lambda: press_band_text(self.sim.Pressure))

        ttk.Separator(parent, orient="horizontal",
                      ).grid(row=row, column=0, columnspan=2, sticky="ew",
                             pady=(8, 4))
        row += 1
        ttk.Label(parent, text="the four terms of  p = g - 60n + s t + d",
                  font=self.BOLD).grid(row=row, column=0, columnspan=2,
                                       sticky="w", pady=(0, 4))
        row += 1
        # Each term is read from the same tuple the tick summed, so editing a
        # table moves the term and the delta together.
        for index, label in enumerate(("g   state gain",
                                       "s t  slope x temperature",
                                       "d   PEA gain",
                                       "-60n  fan drag")):
            row = self.add_readout(
                parent, row, label,
                (lambda i: lambda: shown(self.sim.terms()[i]))(index))

        ttk.Separator(parent, orient="horizontal",
                      ).grid(row=row, column=0, columnspan=2, sticky="ew",
                             pady=(8, 4))
        row += 1
        ttk.Label(parent,
                  text="the core model   dT = pure_cbl * p_mult + passive[s]"
                       " - coolant + noise   (or exactly -586, stalled)",
                  font=self.BOLD).grid(row=row, column=0, columnspan=2,
                                       sticky="w", pady=(0, 4))
        row += 1
        # The same discipline as the pressure terms: whatever the model actually
        # added, not a second computation of it.  Each is cleared when the model
        # is off, so nothing here can show a step that did not happen.
        row = self.add_readout(parent, row, "T   this step starts from",
                               lambda: shown(self.sim.Temperature))
        # The three banks, and the weighted a_eff the fit actually consumes.
        # `a_eff` is read live rather than off the trace because it is a control
        # position, not a term of the step -- and because a control that has been
        # moved clears the trace anyway (see _line_changed).
        row = self.add_readout(parent, row, "a1 / a2 / a3  banks",
                               lambda: " / ".join(shown(bank)
                                                  for bank in self.core.banks))
        row = self.add_readout(parent, row, "a_eff  weighted sum of the 3",
                               lambda: shown(self.core.a_eff))
        # The pumps, read live like the banks: a control position, not a term of
        # the step -- and the step's own cooling is below, where a stale value
        # has somewhere to hide (it is cleared by _line_changed like the rest).
        row = self.add_readout(parent, row, "p1 / p2 / p3  pumps",
                               lambda: " / ".join(str(pump)
                                                  for pump in self.core.pumps))
        row = self.add_readout(parent, row,
                               "cooling  -%g x mean(p1..p3)" % COOLANT_PER_LEVEL,
                               lambda: self._step_value("last_cooling"))
        row = self.add_readout(parent, row, "p   this step started from",
                               lambda: self._step_value("last_pressure"))
        row = self.add_readout(parent, row, "stall  this step",
                               lambda: "-" if self.core.last_row is None
                               else ("STALL" if self.core.last_stall else "no"))
        row = self.add_readout(parent, row, "t   elapsed since armed (s)",
                               lambda: luau_number(self.core.t))
        row = self.add_readout(parent, row, "row  (passive index)",
                               lambda: "4 MELTDOWN" if self.core.melted
                               else ("-" if self.core.last_row is None
                                     else str(self.core.last_row)))
        # The wiki's >= 39,000.  A latch with its own tile rather than a fifth
        # row, because a row would need a passive constant nobody has published
        # (CORE_MELTDOWN_AT).  Once set, the model stops stepping.
        row = self.add_readout(parent, row, "meltdown  core reached the wall",
                               lambda: "YES" if self.core.melted else "no")
        # The two halves of the heat, as separate tiles on purpose: `pure_cbl` is
        # a curve in `a` that does not know the row, `passive` is a constant that
        # does nothing else, and a single summed "baseFluc" row would have hidden
        # exactly the distinction the 2026-10-16 spec is about -- a dark console
        # shows 0 in the first and its row's number in the second.
        row = self.add_readout(parent, row, "pure_cbl  0.0516 a^2 + 1.1 a + 426",
                               lambda: self._step_value("last_heat"))
        row = self.add_readout(parent, row, "passive  this row's constant",
                               lambda: self._step_value("last_passive"))
        row = self.add_readout(parent, row, "press x   pMultiplier",
                               lambda: self._step_value("last_amp"))
        row = self.add_readout(parent, row, "activeFluc  pure_cbl x press",
                               lambda: self._step_value("last_actual"))
        row = self.add_readout(parent, row, "noise(t)",
                               lambda: self._step_value("last_noise"))
        row = self.add_readout(parent, row, "T'  next tick's temperature",
                               lambda: self._step_value("last_temperature"))

    def _step_value(self, name):
        """A core-model readout: '-' until the first step, then the number the
        model itself used.

        Dashes rather than zeros, for the same reason the temperature box and
        the rows of the original's own tables are not zero-filled: a 0 here is
        indistinguishable from a step that genuinely added nothing, and the one
        thing this panel must never do is show a term from a step that has not
        happened.
        """
        if self.core.last_row is None:
            return "-"
        return shown(getattr(self.core, name))

    def _build_log(self):
        wrap = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="LOG", font=self.BOLD).pack(anchor="w")
        box = ttk.Frame(wrap)
        box.pack(fill="both", expand=True)
        self.log_text = tk.Text(box, height=9, wrap="none", font=self.MONO,
                                state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(box, orient="vertical", command=self.log_text.yview)
        bar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=bar.set)

    def log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        last = int(self.log_text.index("end-1c").split(".")[0])
        if last > self.LOG_MAX_LINES:
            self.log_text.delete("1.0", "%d.0" % (last - self.LOG_MAX_LINES + 1))
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ----- the controls write the model -----

    def on_pea(self):
        self.sim.PEALevel = int(self.pea_var.get())
        self.on_input("PEA level = %d" % self.sim.PEALevel)

    def on_fan(self):
        self.sim.ActiveFan = int(self.fan_var.get())
        self.on_input("Active fans = %d" % self.sim.ActiveFan)

    # ----- the core model's controls -----

    def on_arm(self):
        self.core.armed = bool(self.arm_var.get())
        if self.core.armed:
            self.core.rearm(self.sim)
            self.log("# core model ARMED: T = %s, t = 0 (the slider is off)"
                     % shown(self.sim.Temperature))
        else:
            # Hand the value back to the slider before it comes alive again: the
            # model has been writing a float the thumb never saw, so the next
            # click would otherwise jump from wherever the thumb was parked.
            self.temp_var.set(self.sim.Temperature)
            self.temp_box.set(shown(self.sim.Temperature))
            self.log("# core model off: Temperature stays at %s"
                     % shown(self.sim.Temperature))
        self._sync_core_widgets()
        self.on_input("core model %s" % ("armed" if self.core.armed else "off"))

    def on_power(self):
        """One of the bank radios moved.

        All three are read back, not just the one that fired: the command is
        bound once per button and a single callback cannot tell which one called
        it, and reading all three is what makes `a_eff` the panel's own number
        instead of a guess at it.
        """
        for index, var in enumerate(self.cbl_vars):
            self.core.set_bank(index, var.get())
        self._line_changed()
        self.on_input("CBL banks = %s  (a_eff = %g)"
                      % (" / ".join(shown(bank) for bank in self.core.banks),
                         self.core.a_eff))

    def on_coolant(self):
        """One of the pump radios moved.

        All three read back, exactly like on_power and for the same reason: the
        command is bound once per button and one callback cannot tell which of
        them fired.  Reading all three is what makes the mean the panel's own
        number rather than a guess at it.
        """
        for index, var in enumerate(self.pump_vars):
            self.core.set_pump(index, var.get())
        self._line_changed()
        self.on_input("Coolant pumps = %s  (mean %g; -%g/tick)"
                      % (" / ".join(str(pump) for pump in self.core.pumps),
                         sum(self.core.pumps) / float(COOLANT_PUMPS),
                         self.core.cooling))

    def on_vent(self):
        """Press the AVB.

        The button is disabled while the cooldown runs, but the guard here is
        not a copy of that: a disabled widget is a state of the WIDGET, and this
        is the rule of the DEVICE.  A path to a reading with two ends is how a
        screen starts lying (CLAUDE.md 0.26, first face).
        """
        before = self.sim.Pressure
        drop = self.sim.vent()
        if drop is None:
            self.log("# AVB refused: %d ticks of cooldown left"
                     % self.sim.vent_ticks)
        else:
            self.log("# AVB: %s -> %s PSI (-%s), cooldown %d ticks"
                     % (shown(before), shown(self.sim.Pressure), shown(drop),
                        AVB_COOLDOWN_TICKS))
            if stalled(self.sim.Pressure):
                # The whole point of the button, and the moment the operator's
                # stall rule starts charging 586 a tick.  Said out loud because
                # the temperature readout alone would look like a slow leak.
                self.log("# AVB: chamber at or below %g -- STALLED.  T now "
                         "falls %g per tick while it holds"
                         % (AVB_STALLOUT_PSI, STALL_FLUC))
        self._refresh()
        self._schedule()

    def on_e_vent(self, index):
        """Fire one E-Vent.

        The button is disabled once spent, and the guard in `Sim.e_vent` is not
        a copy of that -- one is a state of the widget, the other the rule of
        the device (the same split as `on_vent`).

        The temperature is written to the model AND to both widgets here: the
        E-Vent acts between ticks, so there is no `advance()` to do it, and a
        slider still showing the pre-vent number would be the panel disagreeing
        with the number the next tick starts from.
        """
        before = self.sim.Temperature
        drop = self.sim.e_vent(index)
        if drop is None:
            self.log("# E-VENT %d refused: already used this shift" % (index + 1))
        else:
            self.temp_var.set(self.sim.Temperature)
            self.temp_box.set(shown(self.sim.Temperature))
            self.log("# E-VENT %d: T %s -> %s F (-%s), %d of %d used this shift"
                     % (index + 1, shown(before), shown(self.sim.Temperature),
                        shown(drop), self.sim.e_vent_count, E_VENT_COUNT))
            if drop < E_VENT_DROP:
                # The floor, said out loud: the wiki's "approximately 7000" could
                # not all be removed because there was less than that to remove.
                self.log("# E-VENT %d: floored at %s F -- only %s was left"
                         % (index + 1, shown(TEMP_MIN), shown(before)))
        self._refresh()
        self._schedule()

    def on_core_state(self):
        self.core.state = int(self.core_var.get())
        self._line_changed()
        self.on_input("core model row = %d, held by hand" % self.core.state)

    def on_auto(self):
        self.core.auto = bool(self.auto_var.get())
        self._sync_core_widgets()
        self._line_changed()
        self.on_input("core model row: %s"
                      % ("follow Temperature" if self.core.auto
                         else "held at %d" % self.core.state))

    def _line_changed(self):
        """A coefficient moved, so the last step's numbers belong to a tick that
        would no longer come out the same -- the heat is read off the row and the
        CBL, so changing either changes what this tick adds.
        Clearing (rather than recomputing) is deliberate: recomputing would put a
        new temperature on screen for a tick that has already been logged and
        already moved the pressure."""
        self.core.reset_trace()

    def _core_text(self):
        """His equation, term by term, under the controls that set it.

        Written out rather than summarised because the equation is the point: the
        number on the right has to be checkable against the numbers on the left,
        the same way the pressure readouts expose the four terms of one sum.
        """
        core = self.core
        banks = " / ".join(shown(bank) for bank in core.banks)
        pumps = " / ".join(str(pump) for pump in core.pumps)
        if core.melted:
            # The model has latched (CORE_MELTDOWN_AT).  Said here rather than
            # only in the log because a preview that keeps promising "would add"
            # numbers after the model has stopped would be the panel inventing a
            # step (CLAUDE.md 0.19's family: absent and invisible).
            return ("MELTDOWN - the core passed %g F and the model has stopped\n"
                    "a_eff %s = %g   T %s\n"
                    "Reset (a new shift) clears the latch"
                    % (CORE_MELTDOWN_AT, banks, core.a_eff,
                       shown(self.sim.Temperature)))
        if not core.armed:
            row = core.row(self.sim)
            # The preview calls the SAME function the step does, so "would add"
            # cannot come out as a second opinion -- and that includes the stall
            # branch, which the old preview would have had no way to know about.
            heat, passiv, amp, actual, tremor, stall, cooling = step_terms(
                row, core.a_eff, self.sim.Pressure, core.t + self.sim.period,
                core.cooling)
            return ("off - the slider owns Temperature\n"
                    "a_eff %s = %g   row %d at T = %s\n"
                    "pumps %s   cooling -%g\n"
                    "would add %s/tick (pure_cbl %s x %s + passive %s)%s"
                    % (banks, core.a_eff, row, shown(self.sim.Temperature),
                       pumps, cooling, shown(actual + passiv + tremor - cooling),
                       shown(heat), luau_number(amp), shown(passiv),
                       "  STALL" if stall else ""))
        row = core.last_row if core.last_row is not None else core.row(self.sim)
        # Before the first step there are no terms to report, and a zero would
        # read as one.  Same dash convention as the readouts above.
        fresh = core.last_row is None

        def num(value):
            return "-" if fresh else shown(value)

        stall = core.last_stall and not fresh
        return ("t      %s s      T %s\n"
                "row    %s%s   pure_cbl %s   passive %s%s\n"
                "a_eff  %s = %g   press x %s\n"
                "active %s      noise %s      cooling -%s\n"
                "p      %s      %s\n"
                "T'     %s"
                % (luau_number(core.t), shown(self.sim.Temperature),
                   row, " (auto)" if core.auto else " (held)",
                   num(core.last_heat), num(core.last_passive),
                   "   STALL %g" % STALL_FLUC if stall else "",
                   banks, core.a_eff, luau_number(core.last_amp),
                   num(core.last_actual),
                   num(core.last_noise),
                   num(core.last_cooling),
                   num(core.last_pressure),
                   "STALL - pres <= %g" % AVB_STALLOUT_PSI if stall
                   else "stall no",
                   num(core.last_temperature)))

    def on_temp(self, _value=None):
        # The slider moved.  Two ways it does that both land here: dragging
        # its thumb jumps to the pointer (about 137 degrees per pixel across
        # this width), while clicking or holding the trough repeats +-1 --
        # Tk's own binding is `ttk::Repeatedly Increment $w -1|1`.  Arrow keys
        # on it are +-1 as well.  So the snapping in _set_temperature is what
        # keeps every path agreeing about what "one step" means.
        try:
            value = float(self.temp_var.get())
        except (ValueError, tk.TclError):
            # The slider holds something that is not a number -- only possible
            # if something else wrote the variable.  Put the model back rather
            # than guessing.
            self.temp_var.set(self.sim.Temperature)
            return
        self._set_temperature(value)

    def on_temp_box(self):
        """The spinbox stepped, or a typed number was entered."""
        try:
            value = float(self.temp_box.get())
        except (ValueError, tk.TclError):
            # Not a number in the box: restore it instead of guessing at a
            # typo -- the same rule the tick period follows.
            value = self.sim.Temperature
        self._set_temperature(value)
        # The thumb has to follow a typed number, or the slider and the box
        # would point at two different temperatures.  This re-fires on_temp
        # once; that path never writes the slider's variable back, so it stops.
        self.temp_var.set(self.sim.Temperature)

    def _set_temperature(self, value):
        """The one place a CONTROL writes the temperature, whichever one asked.

        While the core model is armed this refuses.  That is not belt-and-braces:
        FocusOut fires when the spinbox is disabled under the focus ring, so
        without this the act of arming the model could immediately re-apply
        whatever number happened to be sitting in the box.

        The box is put back on the way out, because a refused edit must not stay
        on screen looking applied -- an ignored keystroke is one thing, a box
        reporting a temperature the model never used is another.
        """
        if self.core.armed:
            self.temp_box.set(shown(self.sim.Temperature))
            return
        clamped = max(TEMP_MIN, min(TEMP_MAX, value))
        self.sim.Temperature = float(snap(clamped))
        self.temp_box.set(shown(self.sim.Temperature))
        # No log line: a drag fires this on every pixel and would bury the log.
        self._refresh()

    def on_period(self):
        try:
            period = float(self.period_var.get())
        except ValueError:
            # An unparseable box restores the model value.  Clamping a typo
            # into a number would be a silent edit to the run's time base.
            self.period_var.set(self.sim.period)
            return
        self.sim.period = max(0.05, period)
        self.period_var.set(self.sim.period)
        self.on_input("tick period = %s s" % luau_number(self.sim.period))

    def on_input(self, message):
        self.log("# " + message)
        self._refresh()
        self._schedule()

    # ----- the clock -----

    def _schedule(self):
        if self._after is not None:
            self.root.after_cancel(self._after)
            self._after = None
        if self.running:
            # 20 ms floor: after(0) is a busy loop.
            self._after = self.root.after(max(20, int(self.sim.period * 1000)),
                                          self._tick)

    def _tick(self):
        self._after = None
        if not self.running:
            return
        self.advance()
        self._schedule()

    def advance(self):
        # The core model first, then the tick -- Engine.luau's own order: the
        # temperature is advanced and the pressure is read off the temperature
        # the same tick ended with, so the slope term uses the new value.
        # Temperature is not routed through _set_temperature, which refuses while
        # armed; this is the model's write, and it is the only one.
        was_row = self.core.last_row
        was_melted = self.core.melted
        temperature = self.core.step(self.sim)
        if temperature is not None:
            # Floored at 0 only.  A negative temperature is not a thing and the
            # slider cannot show one; the ceiling is the model's to exceed, since
            # 40000 is this window's range and not a physical limit.
            self.sim.Temperature = max(TEMP_MIN, float(temperature))
            # The slider is moved only while the value is inside its range: past
            # the top it has nowhere to put the thumb, and the box -- which is
            # text and has no range -- is the one that shows the truth.
            if self.sim.Temperature <= TEMP_MAX:
                self.temp_var.set(self.sim.Temperature)
            self.temp_box.set(shown(self.sim.Temperature))
            if self.core.last_row != was_row:
                # Nothing jumps: a step changes its increment, it does not move a
                # line.  Still worth a log line, because this is the moment the
                # reading starts climbing at a different rate -- and because it
                # is where the old closed form used to jump by tens of thousands,
                # so a reader looking for that jump needs to be told it is gone.
                self.log("# core row %s -> %d at t = %s s: T = %s"
                         % (was_row, self.core.last_row,
                            luau_number(self.core.t), shown(temperature)))
        if self.core.melted and not was_melted:
            # The wiki's >= 39,000 and the end of the model.  Logged as a
            # LATCH, not as a fourth row: the model stops moving the number
            # from here (CORE_MELTDOWN_AT), so "nothing is happening" and "the
            # model has stopped" have to be told apart on the screen.
            self.log("# MELTDOWN: T reached %s F (>= %g).  The temperature model "
                     "stops here -- Reset (a new shift) rearms it"
                     % (shown(self.sim.Temperature), CORE_MELTDOWN_AT))
        self.sim.tick()
        self.log("Pressure: " + shown(self.sim.Pressure))
        self._refresh()

    def step_once(self):
        self.advance()

    def toggle_run(self):
        self.running = not self.running
        self.pause_button.configure(text="Run" if not self.running else "Pause")
        self.log("# " + ("running" if self.running else "paused"))
        self._schedule()
        self._refresh()

    def reset(self):
        self.sim.reset()
        # The model keeps its arm state across a reset -- a new run from the same
        # starting temperature is what Reset means -- but t goes back to 0 with
        # the fresh state, or the noise would carry the old run's clock into it.
        self.core.rearm(self.sim)
        self.pea_var.set(self.sim.PEALevel)
        self.fan_var.set(self.sim.ActiveFan)
        self.temp_var.set(self.sim.Temperature)
        self.temp_box.set(shown(self.sim.Temperature))
        self.period_var.set(self.sim.period)
        self.log("# reset: Temperature=%s Pressure=%s ActiveFan=%d PEALevel=%d"
                 % (shown(self.sim.Temperature), shown(self.sim.Pressure),
                    self.sim.ActiveFan, self.sim.PEALevel))
        if self.core.armed:
            self.log("# core model still armed: t back to 0 (T = %s)"
                     % shown(self.sim.Temperature))
        self._refresh()
        self._schedule()

    def _refresh(self):
        for var, getter in self.readouts:
            var.set(getter())
        self.core_text.set(self._core_text())
        # The pressure tile's COLOUR is part of its reading (the wiki's three
        # bands), so it is set from the same function the model gates on.
        big_pressure = self.readout_widgets.get("Pressure")
        if big_pressure is not None:
            big_pressure.configure(
                style="Press_%s.TLabel" % press_band(self.sim.Pressure))
        for index, button in enumerate(self.e_vent_buttons):
            if self.sim.can_e_vent(index):
                button.configure(state="normal")
            else:
                button.configure(state="disabled")
        used = self.sim.e_vent_count
        self.e_vent_text.set(
            "all %d ready" % E_VENT_COUNT if not used
            else ("%d of %d used -- refilled only by Reset (a new shift)"
                  % (used, E_VENT_COUNT)))
        if self.vent_button is not None:
            # A greyed-out button with nothing beside it reads as "this thing is
            # broken"; the word is what separates "out of service for N ticks"
            # from "has no function" (CLAUDE.md 0.19's family -- invisible and
            # absent are two failures, and they need two readings).
            if self.sim.can_vent:
                self.vent_button.configure(state="normal")
                self.vent_text.set("ready")
            else:
                self.vent_button.configure(state="disabled")
                self.vent_text.set("cooldown %d" % self.sim.vent_ticks)
        self.status.configure(
            text="tick %d    elapsed %s s    %s"
                 % (self.sim.ticks, shown(self.sim.elapsed),
                    "running" if self.running else "paused"))


def main():
    root = tk.Tk()
    Console(root)
    root.mainloop()


if __name__ == "__main__":
    main()
