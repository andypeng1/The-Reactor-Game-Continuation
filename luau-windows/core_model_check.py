"""Checks for the core temperature model in `gui.py`.

    python core_model_check.py

The window is built and withdrawn, then driven a tick at a time.  Every number
is read back OFF THE WIDGETS -- `screen()` walks the grid and resolves each
label's textvariable -- because a value that is right in the model and wrong on
the screen is exactly the failure this file exists to catch, and reading
`Core`'s own attributes could never see it.

Nothing here re-runs `gui.py`'s arithmetic to compare it against itself (that
would pass even if both were wrong): the anchors are his equation transcribed
straight from the model as it was handed over, with his own literals.

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


# ========== his equation, transcribed from the hand-over ==========
# Literals as given: baseRate, the LEVEL2 reference, and the three sines.  This
# is a second spelling of the spec, not a call back into gui.py.

def his_base_rate(row):
    return [-455.7, 559, 580, 1036][row]


def his_noise(x):
    return 40 * math.sin(x / 1.5) + 25 * math.sin(x / 0.7) + 15 * math.sin(x / 0.3)


def his_temperature(t0, row, power, pressure, x):
    press = 1.15 if pressure < 2500 else (1.08 if pressure < 4000 else 1.0)
    return t0 + (his_base_rate(row) * (power / 50.0) * press + his_noise(x)) * x


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
    check("T(x) is blank before any step", values["T(x)"], "-")
    check("the readout list is what the grid holds", len(values) >= 18, True)

    for _ in range(3):
        console.step_once()
    values = screen(right)
    check("Temperature untouched by the model", values["Temperature"], "5600")
    check("pressure after 3 unchanged ticks", values["Pressure"], "6498")
    check("latched pressure state", values["Pressure state (latched)"], "1")
    check("core state read from temperature",
          values["Core state (from Temperature)"], "1")

    # --- the boundaries of the pure function --------------------------------
    # The whole reason this is not Sim.State: 17500 is row 1, 17500.1 is row 2,
    # and there is a row 0 the latched state can never reach.
    print("\n-- core_state boundaries (Engine.luau:320) --")
    check("core_state(5599.9)", gui.core_state(5599.9), 0)
    check("core_state(5600)", gui.core_state(5600), 1)
    check("core_state(17500)", gui.core_state(17500), 1)
    check("core_state(17500.1)", gui.core_state(17500.1), 2)
    check("core_state(29500)", gui.core_state(29500), 2)
    check("core_state(29500.1)", gui.core_state(29500.1), 3)
    check("noise(0)", gui.noise(0.0), 0.0)

    # --- armed --------------------------------------------------------------
    print("\n-- armed: the model owns Temperature --")
    console.arm_var.set(True)
    console.on_arm()
    values = screen(right)
    check("x starts at 0", values["x   elapsed since armed (s)"], "0")
    check("T0 is the temperature when armed", values["T0"], "5600")
    check("no step yet, so no terms", values["T(x)"], "-")
    check("slider out of service", str(console.temp_slider.cget("state")),
          "disabled")
    check("spinbox out of service", str(console.temp_spin.cget("state")),
          "disabled")
    check("row buttons off while auto", str(console.core_buttons[0].cget("state")),
          "disabled")
    check("CBL starts at the level-2 reference", console.cbl_var.get(), 50)
    t0 = float(values["T0"])

    # One tick at a time, against his equation with his literals.  x is the
    # tick period (1.0 s), so at the Nth tick x = N.
    for n in (1, 2, 3):
        pressure = console.sim.Pressure
        console.step_once()
        values = screen(right)
        want = his_temperature(t0, 1, 50, pressure, float(n))
        check("x after tick %d" % n, values["x   elapsed since armed (s)"], str(n))
        check("row at tick %d" % n, values["row  (baseRate index)"], "1")
        check("rate at tick %d" % n, values["rate  per second"], "559")
        check("noise(%d)" % n, values["noise(x)"], gui.shown(his_noise(n)))
        check("T(%d) against his equation" % n, values["T(x)"], gui.shown(want))

    # --- the row changes, and the line with it ------------------------------
    # A closed form means the whole line moves when the row does, so the reading
    # jumps by (new rate - old rate) * x -- about 21 * 22 going 1 -> 2, and
    # about 456 * 42 going 2 -> 3.  The second one is the visible one.
    print("\n-- the row changes, and the line with it --")
    steps = 0
    while values["row  (baseRate index)"] != "2" and steps < 200:
        console.step_once()
        values = screen(right)
        steps += 1
    check("row followed the temperature up", values["row  (baseRate index)"], "2")
    check("...and crossed at about x = 22", 15.0 < console.core.x < 30.0, True)
    check("log records the row change", "core row 1 -> 2" in log_text(console),
          True)

    previous = 0
    steps = 0
    while steps < 200:
        previous = int(values["T(x)"])
        console.step_once()
        values = screen(right)
        steps += 1
        if values["row  (baseRate index)"] == "3":
            break
    check("row 3 reached", values["row  (baseRate index)"], "3")
    check("the 2 -> 3 jump is bigger than a tick",
          int(values["T(x)"]) - previous > 5000, True)
    check("log records that one too", "core row 2 -> 3" in log_text(console),
          True)

    # The runaway is the model's to have: TEMP_MAX is the slider's range, not a
    # physical limit, and a console that silently capped the temperature at the
    # top of its own widget would hide the failure it is there to show.
    print("\n-- the runaway is not clipped to the slider --")
    for _ in range(20):
        console.step_once()
    values = screen(right)
    check("temperature past the slider top",
          int(values["T(x)"]) > int(gui.TEMP_MAX), True)
    check("the reading on screen is the model's own value",
          values["T(x)"], gui.shown(console.sim.Temperature))
    check("the box carries the number past the slider top",
          int(console.temp_box.get()) > int(gui.TEMP_MAX), True)
    check("press factor 1.0 above 4000",
          "press x1" in console.core_text.get(), True)

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
    # Reset first: the runaway above ran x out to 180-odd seconds, and his row 0
    # line from T0 = 5600 reaches the floor long before that.  Both are correct,
    # but the check below is about the line, not about the floor.
    print("\n-- row held by hand --")
    console.reset()
    values = screen(right)
    check("reset puts the temperature back", values["Temperature"], "5600")
    check("reset puts x back", values["x   elapsed since armed (s)"], "0")
    check("reset clears the step terms", values["T(x)"], "-")
    check("armed survives a reset", console.arm_var.get(), True)

    console.auto_var.set(False)
    console.on_auto()
    check("row buttons live again",
          str(console.core_buttons[0].cget("state")), "normal")
    console.core_var.set(0)
    console.on_core_state()
    values = screen(right)
    check("changing the line clears the stale step", values["T(x)"], "-")
    check("...including the rate", values["rate  per second"], "-")
    pressure = console.sim.Pressure
    console.step_once()
    values = screen(right)
    check("row 0 in use", values["row  (baseRate index)"], "0")
    check("row 0 is the cooling rate", values["rate  per second"], "-456")
    check("row 0 at high pressure, his equation",
          values["T(x)"],
          gui.shown(his_temperature(console.core.t0, 0, 50, pressure,
                                    console.core.x)))
    check("negative and moving down", int(values["T(x)"]) < int(values["T0"]),
          True)

    # --- the power multiplier ----------------------------------------------
    print("\n-- CBL power --")
    check("press_factor below 2500", gui.press_factor(2000.0), 1.15)
    check("press_factor below 4000", gui.press_factor(3000.0), 1.08)
    check("press_factor above 4000", gui.press_factor(9000.0), 1.0)
    console.cbl_var.set(0)
    console.on_power()
    pressure = console.sim.Pressure
    console.step_once()
    values = screen(right)
    check("off gives no heat", values["rate  per second"], "0")
    check("off leaves only the noise term",
          values["T(x)"],
          gui.shown(his_temperature(console.core.t0, 0, 0, pressure,
                                    console.core.x)))
    console.cbl_var.set(125)
    console.on_power()
    console.auto_var.set(True)
    console.on_auto()
    check("full power is 2.5x the reference",
          gui.luau_number(console.core.multiplier()), "2.5")

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
