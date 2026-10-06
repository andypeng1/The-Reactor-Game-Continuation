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
"""

import tkinter as tk
from tkinter import ttk

# ========== THE MODEL ==========
# Copied from calculation.py.  The three tables keep their 1-based integer
# keys, because those keys ARE the State / PEALevel values -- renumbering them
# to 0-based lists would move every reading by one row, and nothing would error.

STATE_MIN = 5600
STATE_1_MAX = 17500        # exclusive
STATE_2_MAX = 29499        # inclusive, so 29499.5 already belongs to State 3

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
        self.readouts = []          # [(StringVar, callable)]
        self.running = True
        self._after = None

        # One variable per control: Tk holds the shown value, the model is
        # written from the callback.  Never the other way round, so the two
        # cannot disagree about what was clicked.
        self.pea_var = tk.IntVar(value=self.sim.PEALevel)
        self.fan_var = tk.IntVar(value=self.sim.ActiveFan)
        self.period_var = tk.DoubleVar(value=self.sim.period)

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
        ttk.Scale(row, from_=0, to=40000, variable=self.temp_var,
                  command=self.on_temp).pack(side="left", fill="x", expand=True)
        spin = ttk.Spinbox(row, from_=0, to=40000, increment=1, width=7,
                           format="%.0f", textvariable=self.temp_box,
                           command=self.on_temp_box)
        spin.pack(side="left", padx=(6, 0))
        # The arrows apply themselves, but a typed number sits in the box until
        # something reads it.  Enter and leaving the box both apply it, so a
        # typed temperature can never be silently ignored.
        spin.bind("<Return>", lambda _event: self.on_temp_box())
        spin.bind("<FocusOut>", lambda _event: self.on_temp_box())

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
        row = self.add_readout(parent, row, "Core state",
                               lambda: str(self.sim.State))
        row = self.add_readout(parent, row, "State band",
                               lambda: self.sim.band)
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
        """The one place the temperature is written, whichever control asked."""
        clamped = max(0.0, min(40000.0, value))
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
        self.pea_var.set(self.sim.PEALevel)
        self.fan_var.set(self.sim.ActiveFan)
        self.temp_var.set(self.sim.Temperature)
        self.temp_box.set(shown(self.sim.Temperature))
        self.period_var.set(self.sim.period)
        self.log("# reset: Temperature=%s Pressure=%s ActiveFan=%d PEALevel=%d"
                 % (shown(self.sim.Temperature), shown(self.sim.Pressure),
                    self.sim.ActiveFan, self.sim.PEALevel))
        self._refresh()
        self._schedule()

    def _refresh(self):
        for var, getter in self.readouts:
            var.set(getter())
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
