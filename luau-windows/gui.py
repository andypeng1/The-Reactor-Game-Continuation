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
from `calculation.luau` and are that file's numbers.  The temperature table in
`CORE MODEL` below is the operator's own, read off the shipped game's 477-tick
log (`DataCollection.Log`) as the mean dT per unit time at each core state --
it is not in calculation.luau, which takes Temperature as an input and never
computes it.  So the two are kept in their own blocks and neither is allowed to
rewrite the other's tables: what joins them is the single Temperature value,
which the core model writes and the pressure terms read.
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
# The operator's own temperature model (2026-10-13).  Not from calculation.py --
# that file takes Temperature as an input and never computes one.  These numbers
# come from the shipped game's own 477-tick log (`DataCollection.Log`, one record
# per second): the mean dT per unit time at each core state, which is an
# empirical linearisation of what Engine.luau does tick by tick.
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

BASE_RATE = {0: -455.7, 1: 559.0, 2: 580.0, 3: 1036.0}

CBL_REFERENCE = 50.0       # his LEVEL2: the power the rates above were taken at
PRESS_BANDS = ((2500.0, 1.15), (4000.0, 1.08))   # first match wins, else 1.0
NOISE_TERMS = ((40.0, 1.5), (25.0, 0.7), (15.0, 0.3))   # (amplitude, period)

# Engine.luau:320's three thresholds, written the way that line writes them.
# They are the same Config.Sim numbers the band constants above encode, but for
# a float temperature the encoding does not round the same -- State 3 is "greater
# than 29500", and STATE_2_MAX is 29499 only because a pressure reading is whole.
CORE_ROW_1_AT = 5600       # >= is row 1
CORE_ROW_2_ABOVE = 17500   # >  is row 2
CORE_ROW_3_ABOVE = 29500   # >  is row 3

# CBL power, at the levels Engine.luau:109 accepts (`integer(value, 1, 5)`).
# "off" is ours: the original has no off, but a machine with every laser dark is
# the condition his row 0 was measured in, and without a zero the model could
# never be told to stop making heat.
CBL_LEVELS = ((0, "off"), (25, "PW1"), (50, "PW2"), (75, "PW3"),
              (100, "PW4"), (125, "PW5"))


def core_state(temperature):
    """Engine.luau:320, threshold for threshold, including the 0.

    Not Sim.State: that one is latched and has no row below 5600.  This is a
    read of the temperature, so it is recomputed every tick and can fall.
    """
    if temperature > CORE_ROW_3_ABOVE:
        return 3
    if temperature > CORE_ROW_2_ABOVE:
        return 2
    if temperature >= CORE_ROW_1_AT:
        return 1
    return 0


def press_factor(pressure):
    """His `pressFactor`, read from the LIVE pressure at the start of the step.

    His Desmos has this as a hand-set slider; here it is that slider wired to
    the chamber, so it bends the rate once the pressure model has been dragged
    down.  The console starts at 6000, so it starts at 1.0.
    """
    for limit, factor in PRESS_BANDS:
        if pressure < limit:
            return factor
    return 1.0


def noise(x):
    """His `noise(x)`: three sines instead of a random number.

    Deliberately reproducible -- the same x has to give the same temperature, or
    there is nothing to compare a rerun against.
    """
    return sum(amplitude * math.sin(x / period)
               for amplitude, period in NOISE_TERMS)


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


class Core:
    """The operator's temperature model, driving Sim.Temperature.

    His equation, literally:

        T(x) = T_0 + (baseRate[s] * a/50 * pressFactor + noise(x)) * x

    Two properties of it are worth knowing before reading the code.

    ONE: it is a closed form, not a step.  T is recomputed from T_0 and the
    whole elapsed x every tick, so when the row changes the line changes slope
    and the reading JUMPS by (new rate - old rate) * x -- small going 1 -> 2
    (559 to 580, so 21 * x, about 460 at the crossing) and large going 2 -> 3
    (580 to 1036, so 456 * x, about nineteen thousand at its crossing).  That is
    his model, not a defect: in Desmos, dragging `s` moves the line, and the
    graph is a line through T_0.  The alternative (adding a small increment per
    tick, which is what Engine.luau does) would give a kinked curve and no jump,
    and would be a different model.  The row is read from the temperature the
    PREVIOUS tick ended on, the way Engine.luau gates its own state terms on the
    temperature before the update.

    TWO: `noise(x)` is inside the multiplication by x, exactly as written.  So it
    is not a tremor on a reading, it is a tremor on the SLOPE: at x = 100 the
    +-80 degree wobble is a +-8000 degree spread, and two runs that differ only
    in where you stopped are hundreds of degrees apart.  Its stated purpose was
    to stop the number flickering, and as written it does do that (the sines are
    fixed, not random) -- but it is also the largest term in the model by about
    x = 30, where 80x overtakes 559.  Kept as written.  If it is ever wanted as a
    tremor on the value instead of the slope, the shape is
    `T_0 + rate * x + noise(x)` -- the wobble OUTSIDE the x.

    Arming is what makes it live.  The slider is this file's own way of setting a
    temperature and the model is a way of computing one; they cannot both be in
    charge of one number, so the model is armed rather than installed, and with
    the box unticked not one line below runs.
    """

    def __init__(self):
        self.armed = False
        self.auto = True
        self.power = CBL_REFERENCE
        self.state = 0            # the row held by hand, when auto is off
        self.t0 = 0.0             # his T_0: the temperature when armed
        self.x = 0.0              # his x: seconds elapsed since armed
        self.reset_trace()

    def reset_trace(self):
        """The last step's numbers, for the readout.  Cleared rather than zeroed,
        so a tile cannot show a term belonging to a step that never happened."""
        self.last_row = None
        self.last_rate = 0.0
        self.last_factor = 1.0
        self.last_noise = 0.0
        self.last_temperature = 0.0

    def rearm(self, sim):
        """Take the current temperature as T_0 and put his x back to 0."""
        self.t0 = float(sim.Temperature)
        self.x = 0.0
        self.reset_trace()

    def multiplier(self):
        """His `cblMulti`: how far the CBL power is from the level-2 point the
        rates were measured at.  Off gives exactly 0, because the lasers ARE the
        heat -- with no way to reach zero the model could never stop making it."""
        return self.power / CBL_REFERENCE

    def row(self, sim):
        return core_state(sim.Temperature) if self.auto else self.state

    def step(self, sim):
        """One tick.  Returns the temperature the model wants, None when off.

        Called BEFORE sim.tick(), which is the order Engine.luau uses: the
        temperature moves first, and the pressure state is read off the
        temperature the same tick ended with, so the slope term uses the new
        value rather than the old one.

        x is accumulated rather than derived from `(ticks - x0) * period`,
        because the period is a control: changing it halfway would otherwise
        rewrite the whole run's elapsed time, including the part already drawn.
        """
        if not self.armed:
            return None
        self.x += sim.period
        row = self.row(sim)
        factor = press_factor(sim.Pressure)
        rate = BASE_RATE[row] * self.multiplier() * factor
        wobble = noise(self.x)
        temperature = self.t0 + (rate + wobble) * self.x
        self.last_row = row
        self.last_factor = factor
        self.last_rate = rate
        self.last_noise = wobble
        self.last_temperature = temperature
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
        self.cbl_var = tk.IntVar(value=int(self.core.power))
        self.core_var = tk.IntVar(value=self.core.state)
        self.auto_var = tk.BooleanVar(value=self.core.auto)
        self.core_text = tk.StringVar()

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
        power = ttk.Frame(core)
        power.pack(fill="x", pady=(4, 0))
        ttk.Label(power, text="CBL").pack(side="left")
        for value, name in CBL_LEVELS:
            ttk.Radiobutton(power, text=name, value=value, variable=self.cbl_var,
                            command=self.on_power).pack(side="left", padx=2)

        rows = ttk.Frame(core)
        rows.pack(fill="x", pady=(2, 0))
        ttk.Label(rows, text="row").pack(side="left")
        for value in sorted(BASE_RATE):
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
        ttk.Label(parent, textvariable=var, anchor="e",
                  font=self.MONO_BIG if big else self.MONO,
                  ).grid(row=row, column=1, sticky="e", padx=(12, 0))
        self.readouts.append((var, getter))
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
                  text="the core model   T = T0 + (rate + noise(x)) x",
                  font=self.BOLD).grid(row=row, column=0, columnspan=2,
                                       sticky="w", pady=(0, 4))
        row += 1
        # The same discipline as the pressure terms: whatever the model actually
        # multiplied, not a second computation of it.  Each is cleared when the
        # model is off, so nothing here can show a step that did not happen.
        row = self.add_readout(parent, row, "T0",
                               lambda: shown(self.core.t0))
        row = self.add_readout(parent, row, "x   elapsed since armed (s)",
                               lambda: luau_number(self.core.x))
        row = self.add_readout(parent, row, "row  (baseRate index)",
                               lambda: "-" if self.core.last_row is None
                               else str(self.core.last_row))
        row = self.add_readout(parent, row, "rate  per second",
                               lambda: self._step_value("last_rate"))
        row = self.add_readout(parent, row, "noise(x)",
                               lambda: self._step_value("last_noise"))
        row = self.add_readout(parent, row, "noise(x) x  the slope term",
                               lambda: self._step_value("last_noise_x"))
        row = self.add_readout(parent, row, "T(x)",
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
        if name == "last_noise_x":
            return shown(self.core.last_noise * self.core.x)
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
            self.log("# core model ARMED: T0 = %s, x = 0 (the slider is off)"
                     % shown(self.core.t0))
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
        self.core.power = float(self.cbl_var.get())
        self._line_changed()
        self.on_input("CBL power = %g  (x%s of the level-2 point)"
                      % (self.core.power, luau_number(self.core.multiplier())))

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
        """A coefficient moved, so the last step's numbers describe a line that
        no longer exists -- his formula is a line through T0 with the CURRENT
        rate, so changing the rate changes the whole past, not just the future.
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
        if not core.armed:
            row = core.row(self.sim)
            rate = (BASE_RATE[row] * core.multiplier()
                    * press_factor(self.sim.Pressure))
            return ("off - the slider owns Temperature\n"
                    "row %d at %s would give %s/s"
                    % (row, shown(self.sim.Temperature), shown(rate)))
        row = core.last_row if core.last_row is not None else core.row(self.sim)
        # Before the first step there are no terms to report, and a zero would
        # read as one.  Same dash convention as the readouts above.
        fresh = core.last_row is None

        def num(value):
            return "-" if fresh else shown(value)

        return ("x      %s s      T0 %s\n"
                "row    %s%s   rate %s/s\n"
                "CBL    %g x%s    press x%s\n"
                "noise  %s      noise.x %s\n"
                "T(x)   %s"
                % (luau_number(core.x), shown(core.t0),
                   row, " (auto)" if core.auto else " (held)",
                   num(core.last_rate),
                   core.power, luau_number(core.multiplier()),
                   luau_number(core.last_factor),
                   num(core.last_noise),
                   num(core.last_noise * core.x),
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
                # A row change moves the WHOLE line, so the reading jumps by more
                # than a tick's worth.  Saying so in the log is the difference
                # between a model and a glitch.
                self.log("# core row %s -> %d at x = %s s: T = %s"
                         % (was_row, self.core.last_row,
                            luau_number(self.core.x), shown(temperature)))
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
        # starting temperature is what Reset means -- but T0 and x are taken from
        # the fresh state, or the model would carry the old run's line into it.
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
            self.log("# core model still armed: T0 = %s, x back to 0"
                     % shown(self.core.t0))
        self._refresh()
        self._schedule()

    def _refresh(self):
        for var, getter in self.readouts:
            var.set(getter())
        self.core_text.set(self._core_text())
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
