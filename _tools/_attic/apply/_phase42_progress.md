## Phase 42 - The click was never unreachable, and the coolant lamp was never lit  [DONE]

Scope: retract two Phase 40 claims that had been reasoned rather than measured, and fix the defect the
second one was hiding. No gameplay mechanic changed. The only code edit is a colour fallback in
ControlVisuals.applyLamp.

WHAT PHASE 40 SAID. "What could NOT be done is the simulated click. Workspace.StreamingEnabled is true
and the place has one SpawnLocation at (233, 402.9, 1370) - about 1400 studs from the control room and
120 studs below it - so a playtest client has neither the console geometry nor a path to it." On that
basis the phase was recorded as verified by dot-path resolution and CanQuery, NOT by a mouse, and
docs/TODO.md section 3 carried it forward as a standing blocker.

WHY IT WAS WRONG, MEASURED. The place has FIVE SpawnLocations, not one:

    SpawnLocation     (20.0, 0.5, 4.0)  Neutral=true   TeamColor=Medium stone grey  (233.0, 402.9, 1370.0)
    Spawn1..Spawn4    ( 2.0, 0.2, 2.0)  Neutral=false  TeamColor=White  Transparency=1  CanCollide=false
                                        (257.0, 277.1, 29.4 / 36.9 / 44.4 / 51.9)

Spawn1..Spawn4 stand on solid floor - Workspace.Geometry.Parts.Part at y=276.94, a 0.12-stud drop -
122 to 160 studs from the desks, at desk height. They are dead, and that half of the Phase 40 reading
was right: Teams:GetTeams() is empty, so four spawns that are Neutral=false with TeamColor=White can
never be selected, and the live client really does appear at (233.0, 406.1, 1370.0). What did not
follow is "unreachable". A straight ray from the far spawn to the control room is blocked in 1 of 60
samples. And the streaming reading was a DISTANCE artefact, not a wall: the same client that saw 42
ThermalConsole descendants from 1336 studs away saw 678 of them once its character stood at the desk.
Nothing ever needed a new spawn.

A REAL CLICK, AND THE METHOD. With the character inside the detector's 32-stud MaxActivationDistance
and the camera pinned, moveTo(427, 115) plus a left click produced, on the server:

    [Console] andypeng1NB pressed: Coolant Pump 1 Sensor Recalibration  (ThermalConsole)
    [Info] C-Pump 1 sensors recalibrated

That is ClickDetector -> ControlTrigger.Fire -> CoolantSystem.Recalibrate, from the real input
pipeline, on a control chosen in advance rather than hit by luck. Four things had to be measured
before it would land, and each had already produced a false negative:

  1. Camera. execute_luau resets CameraType back to Custom after every call, so the pose has to be
     held by a RenderStepped handler that re-asserts Scriptable and CFrame each frame. Rotating the
     CHARACTER instead does nothing while that pin is up - fourteen PivotTo iterations moved the
     target's pixel by zero.
  2. Aim. Project the target's LeverUnion with WorldToViewportPoint, then RAY-TEST that pixel and
     assert the hit is the lever's own model. Projecting alone is not enough: of four poses that put
     pump 3 at a plausible pixel, the ray died on ThermalConsole.Riser at 3.3 studs. GetPartBoundsIn
     Radius is not a substitute - it reported near=0 for a pose whose ray was blocked at 1.57 studs.
  3. Separation. The three coolant levers are collinear along Z, so an arbitrary camera renders them
     about 6 pixels apart and a small rotation swaps the target. A pose perpendicular to the row -
     cam (112.0, 283.0, -28.5) looking at the row centre - separates them to x = 427 / 284 / 211.
  4. The tool's own y. rblx_user_mouse_input sends requested_y + 58; asking for y=91 lands at 149.
     The target must also clear the CoreGUI chat band in the top-left, which the tool reports as
     "hits CoreGUI" when the click would be swallowed.

DECISIONS 120 says a check whose answer cannot be false is not a check. "The client cannot reach the
console" was written from a single distance-dependent sample and never falsified, so it read as a
measurement while being an inference. It is corrected here, in the TODO section that carried it, and
in the Phase 40 text above it.

THE SAME SHAPE, TWICE. Phase 40 also wired a lamp to coolant_recalibrate so that a momentary action
would be visible, and recorded that the lamp now says "spent while cooling, ready after". Measured
against the running place, the lamp says nothing at all - no part is bound to that action, so the
branch is dead code - and worse, every press left the three station LEDs stuck on the activation
flash colour. Full diagnosis, fix and verification are DECISIONS 124. The shared cause is worth
naming because it is not the lamp: DECISIONS 118 had "verified" the lamp by extracting lampState's
text and unit-testing the predicate. That is a real test, of a different claim. The predicate was
correct. Nothing was bound to it.

VERIFICATION OF THE FIX. A Heartbeat sampler recording every colour CHANGE of
CoolantControl1.Light1.NeonPart through one real simulated click gave

    0.02 s   (235,235,235)   authored base
    5.57 s   ( 90,255,120)   the activation flash, PULSE_COLOR
    6.28 s   (235,235,235)   back to base, 0.71 s after the flash

The third reading is the test, and it did not exist before the fix. Managed lamps were read in the
same run and are unchanged: StartUpBigLever (22,22,22), E_VENTLever1 (240,240,240), E_VENTLever2
(22,22,22), E_VENTLever3 (240,240,240), MonitorBootButton (240,240,240).

STILL OPEN. coolant_pump_level has no lampState branch either, so the three LEDs that RebuildKit
describes as "three LEDs showing the pump level" show no level. Which control should own them - the
station, as the original has it, or the ON button that currently wins the bind - is a design question,
recorded rather than guessed.
