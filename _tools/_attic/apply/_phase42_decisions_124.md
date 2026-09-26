124. A TEST OF THE PREDICATE IS NOT A TEST OF THE WIRING.

    WHAT HAPPENED. Phase 40 added a lampState branch so that coolant_recalibrate - a momentary action
    with a real 30-second cooldown and no lever position - would be shown by the lamp instead of the
    lever, and recorded that the lamp now says "spent while cooling, ready after". DECISIONS 121 is
    that record. Measured against the running place, no part is bound to coolant_recalibrate at all.
    The branch never executes.

    WHY. Three parts decide it, and each is individually reasonable.

      * ConsoleBinder line 45 binds CoolantControl<i>.OnButton.ClickPart with action coolant_pump_on.
        The BigLever, bound at line 51 with coolant_recalibrate, comes second.
      * ControlVisuals.findLampParts walks up from a click part to the nearest Model holding a lamp,
        and OnButton's own ClickPart is not named for one - it is "ClickPart", not "NeonPart". Both
        binds therefore resolve to the SAME three parts: CoolantControl<i>.Light1/2/3.NeonPart.
      * Bind upgrades an existing lamp entry only when its action is falsy - the condition reads
        "elseif action and not entry.action". By the time the BigLever binds, the LEDs already carry
        coolant_pump_on, which is truthy, so the upgrade is skipped and coolant_recalibrate ends up
        attached to nothing.

    lampState has no branch for coolant_pump_on either, so it returns nil for these parts - and that
    is where a second, worse defect was hiding. ControlVisuals.Pulse writes PULSE_COLOR
    unconditionally on every press and sets a 0.6-second timer. applyLamp was both the timer's only
    clearer AND an early return on a nil state. So the flash was cleared, no steady state was written,
    and the part simply kept the flash colour - permanently. Measured: after one press
    CoolantControl1 and CoolantControl2 read (90,255,120) indefinitely, while the untouched
    CoolantControl3 still read its authored (235,235,235). Any press on any unmanaged control in the
    place did this.

    THE FIX, AND WHY IT IS THIS ONE. applyLamp now falls back to entry.base instead of returning, and
    writes only when the colour actually changes. entry.base is captured at Bind, so it is the
    authored colour - the correct resting state for a lamp whose action has no branch, and a strictly
    better default than "leave whatever was there", which is exactly how the flash colour became
    permanent. The per-tick guard is not an optimisation: this loop visits every lamp every frame, and
    an unconditional assignment would mark the property dirty sixty times a second for a colour that
    is not moving.

    WHAT WAS DELIBERATELY NOT CHANGED. The binding precedence. Which control should own the three
    station LEDs is a design question - RebuildKit describes them as the pump LEVEL indicator,
    coolant_pump_level has no branch either, and the original leaves OnButton and OffButton with no
    lamp of their own - and answering it by reordering two binds would be guessing with the test
    scene. DECISIONS 121's design decision (a momentary action is displayed by a lamp, never by a
    lever position) still stands. What it did not have was any part to display it.

    VERIFIED IN THE FALSIFIABLE FORM. A Heartbeat sampler recording every colour change of
    CoolantControl1.Light1.NeonPart through one real simulated click:

        0.02 s  (235,235,235)    5.57 s  (90,255,120)    6.28 s  (235,235,235)

    The third reading is the test, and it did not exist before the fix. Managed lamps were read in the
    same run and are unchanged: StartUpBigLever (22,22,22), E_VENTLever1 (240,240,240),
    E_VENTLever2 (22,22,22), E_VENTLever3 (240,240,240), MonitorBootButton (240,240,240).

    THE GENERAL LESSON. DECISIONS 118 is good practice and is not the problem: it tested the shipped
    text rather than a retyped copy, which is exactly right. The problem is that the claim being made
    was about WIRING - "the lamp says it" - while the test was of a PREDICATE. Extracting and running
    the function proves the function is correct; it cannot prove the function is reached. The tell is
    the one DECISIONS 120 gives: ask what would have to be true for the claim to fail, and if the test
    could pass while the claim is false, it is not a test of the claim. Here it passed and the claim
    was false. Phase 42 records the sibling case - "the client cannot reach the console" - which
    failed the same way for the same reason: an inference written down as a measurement.
