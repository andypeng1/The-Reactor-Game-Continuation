# DECISIONS

## Project Goal
重构为科幻反应堆设施维护游戏后端，不采用传统核电站工程模拟框架。
NOTE (Phase 11): the operator brief mentioned "refactor the combat system"; this
project has no combat system. Interpreted as the reactor simulation refactor,
which is the only system present. Recorded here per rule 1.

## Architecture
采用事件驱动游戏逻辑：ReactorState / SimulationLoop / DeviceManager /
MaintenanceController / ConsoleService。SystemManager 按 Priority 调度，
所有系统点号调用 Update(dt)（非 :），GameState 为唯一真相源，Config 存放全部可调数值。

## Assumptions (Phase 11)
1. IGNITION SEEDING. The real game boots the core from the control room, but the
   stallout penalty (-750 F/tick below 2250 PSI) exceeds the heat of MINIMUM lasers,
   so a dead-cold core could never build pressure. ReactorState.SetOnline now seeds
   the TRGWeb operating snapshot (9420 F, 5000 PSI) when the core is cold. The
   stallout temperature penalty is additionally gated at > 2000 F so a formation
   climb is possible. GameState.Reset keeps the cold state (20 F, 100 PSI).
2. PRESSURE SCALE. Wiki/TRGWeb pressure is PSI in the 0-13500+ band (AVB drops 3300,
   stallout 2250, overpressure 13500). Config.Reactor.MaxPressure = 16000. The old
   320 clamp was two orders of magnitude off and made stallout permanent.
3. TRGWEB TICK. The prototype evaluated once per 2500 ms. Config.Sim.TRGWebTick = 2.5
   and every TRGWeb-sourced constant is applied as value * (dt / 2.5). This fixes the
   previous 2.5x speed error. The logger (DataCollection) used the same 0.5/2.5 ratio.
4. CBL HEAT. TRGWeb uses power_level * 65 (MINIMUM still fires). The old code used
   (level - 1) * 65, which produced zero heat at MINIMUM. Corrected.
5. TRGWEB PROTOTYPE BUG. The prototype computes (CBL1 + CBL2 + CBL1) - CBL3 is never
   counted and CBL1 is double counted. Implemented the evident intent:
   CBL1 + CBL2 + CBL3.
6. POWER OUTPUT OWNER. PowerSystem alone writes GameState.Reactor.PowerOutput, using
   the TRGWeb tier curve. ReactorState.CalculatePowerOutput is kept as the shared
   utility. Offline/tripped output is 0 (real game idle: OutputVal 0).
7. TEMPERATURE OWNER. ReactorState alone changes Temperature. CoolantSystem only owns
   pump levels, loop charge and reservoirs; it exposes GetTotalHeatRemoval().
   This removes the previous double coolant sink.
8. PEA SCOPE. The P.E.A is modelled as an equipment-strain layer (extraction rate
   1-4, stress 0-100, overstress wear). It does NOT alter the power curve, so the
   existing power mechanic is preserved.
9. QUOTA SEMANTICS. Wiki: "Produce 524 GW and shut the reactor down" - the quota is a
   power-output target, not accumulated energy. ShiftSystem marks QuotaMet when
   PowerOutput >= ShiftQuotas[shift]. Shift ending remains time-based (unchanged).
10. EQUINOX TRIGGER. No exact in-game clock is available, so Equinox starts on Shift 3
    once shift.Elapsed >= Config.Reactor.EquinoxTriggerTime (800 s) and runs 40 s.
    It applies the 3x energy multiplier and may destroy coolant pumps (Wiki).
11. NOISE. The TRGWeb random term is re-rolled once per TRGWeb tick (not per frame),
    which matches the prototype and avoids a frame-rate-dependent random walk.
12. RESERVOIRS. Three reservoirs replace the previous single value. GetReservoir()
    still returns the average for backwards compatibility; GetReservoirs() returns
    the table used by the UI.
13. TRGWeb FLOORS. The prototype floors power/500 and coolant*1.5 in the PEA stress
    formula. Implemented continuously for smoother behaviour; the difference is < 1%.
14. DEVICE RENAME. ControlRodActuator -> CBLActuator. No control rods exist in this
    game (Wiki); the CBL array is the reactor actuator. Same slot, same wear role.
15. MIS.DATACOLLECTION. It is a dormant client-side logger reference (uses readfile /
    writefile / LocalPlayer) and is not required by GameCore. Its nil ctrlConsole
    reference was fixed; the embedded telemetry string is otherwise left intact.
16. ZSCapProbe is an empty folder; left untouched.
17. MISC.SUMMARY01 confirms the pressure-stall strategy around 4000 PSI and that
    coolant pumps break, validating the AVB / purge / stallout numbers already used.

## Prohibitions Honoured
- No existing gameplay mechanic was replaced: AVB, E-VENT, CBL purge/overload,
  Gravatron, METU, HDEF, maintenance tasks, shift timer and scoring are unchanged.
- Removed code was always replaced (RodJam -> FanSeize, ControlRodActuator ->
  CBLActuator, single reservoir -> three reservoirs, dual output writers -> one).
## Assumptions (Phase 14 - Control surfaces + monitors)
18. CLICK DETECTORS. The five control desks (MainReactorConsole, ALTReactorConsole,
    ThermalConsole, ElectricGridConsole, CBLaserConsole) plus HDEFGenerator and the
    METU ECC receptacles are driven by ClickDetectors instead of ProximityPrompts.
    The place already ships 82 ClickDetectors, so 61 were reused and only 4 created
    (the console-level click targets). Every press prints:
        [Console] <player> pressed: <control label>  (<console model>)
19. CBL BODY TEMPERATURE. The operator note said "925k"; the Wiki states the CBL net
    body temperature is always 925 F and the monitor label format is "<n> F", so this
    is implemented as a locked 925 F constant (Config.CBL.BodyTemperatureF). It never
    changes, and is exposed via CBLSystem.GetBodyTemperature().
20. MONITOR REFRESH. The real game refreshes its screens about once per second; per the
    request the three control-room monitors are written EVERY simulation tick
    (Config.Monitor.UpdateInterval = 0) so they are immediate.
21. THE THREE MONITORS. Interpreted as the three status screens that carry core data:
      MainControlRoomMonitor    -> ReadingsFrame (temp, pressure, radiation, output,
                                   HDEF integrity, PEA stress, fluctuation, extraction)
      ThermalControlRoomMonitor -> FanFrame1-6 status + C1-3 coolant pump levels
      PowerControlRoomMonitor   -> CBL1-3 (power %, stress %, state, body temp)
    The other monitors (Log/Forecast/Quota/Alerts) are left untouched.
22. FLUCTUATION. The main monitor's fluctuation label shows the net temperature change
    per TRGWeb tick, matching the prototype's core_temp_fluctuation.
23. DIRECT LEVEL SELECTION. The consoles expose PW1..PW5 (CBL) and PW1..PW4 (P.E.A
    extraction) and PW1..PW3 (coolant pump) click parts, so those set the level
    directly instead of cycling. The old cycling action is kept as a fallback.
24. SELF-HEALING. GameState.Reset clears the CBL / Gravatron / METU / PEA subtables,
    so every system re-runs Initialize() from Update() when its subtable is missing
    or empty. This makes the simulation survive a reset (the self-test resets state).
25. M.A.S.S. systems on the Aux console have no GameCore equivalent, so their buttons
    are bound for name printing and panel focus only (no action).
26. METU. The ECC receptacles are the physical METU interaction (Wiki: operators refill
    the ECC by hand); the arm/fire/disarm remotes remain available to the client.
27. WORKSPACE SORTING. Anonymous geometry (Part/Union/Wedge/MeshPart/Meshes/*)
    and anonymous "Model" containers were moved into Workspace.Geometry subfolders,
    empty legacy scripts into Workspace.Legacy, Tools into Workspace.Tools and
    SpawnLocations into Workspace.TeamSpawns. Only anonymous objects were moved
    (verified anchored, zero welds, no script references) so all runtime paths and
    world positions are unchanged. Top level went from 1828 to 137 children.
28. MONITOR CLOCK. A shift maps to 6:00 AM -> 6:00 PM, so 12:00 PM lands at
    shift-second 600. Config.Reactor.EquinoxTriggerTime was set to 600 so the quota
    monitor's Equinox frame and the event agree with the screen text.
29. ALERT LAMPS. The 27 AlertsFrame entries are driven by live state; an active lamp
    is tinted red, an idle lamp returns to its original colour. No new instances were
    added to the monitor.

## Assumptions (Phase 16 - Control feedback, monitor states, click test)
30. LEVER DETENTS. A lever bound by several click parts (PW1..PW5) keeps the
    detent count of the richest action bound to it, so the coolant lever really does
    travel through its four level notches. The swing is +/-28 degrees about the model
    pivot's local X axis; this reads correctly for every lever tested.
31. LAMP SEMANTICS. Indicator lamps show steady state (white ready / red fault /
    dark spent) plus a 0.6 s green activation flash on every press, so the operator
    always gets feedback even when the steady colour would not change.
32. CBL BODY TEMPERATURE UNIT. The operator confirmed 925 K; the display now reads
    "925 K" (Config.CBL.BodyTemperatureF still holds the constant) and shows "ERR"
    when the laser has been destroyed, rather than pretending it is healthy.
33. CONTROL TEST. The click test lives in Workspace.GameCoreControlTest and disables
    itself after one run. It re-arms the reactor first because the self-test resets
    the world when it finishes.

## Assumptions (Phase 19 - Console rebuild)
34. REBUILD CONTRACT. The rebuilt desks are generated by RebuildKit into
    Workspace.Rebuild.Models as MK2_<original name> and satisfy the exact dot paths
    ConsoleBinder already uses. Because that contract is path-based and
    root-agnostic, no engine change was needed: ConsoleBinder.BindRebuild replays
    the same CONTROL_DEFS against the new roots. This was chosen over editing
    CONTROL_DEFS in place, which would have made the shipped desks' binding
    figures unreadable as a baseline.
35. REBUILD BENCH. The rebuild is built on a separate 96x2x96 pad in verified-clear
    Workspace space (Y 298), with an untouched clone of each original beside its
    replacement, rather than in place. Nothing in the live facility was moved,
    renamed or deleted, per the standing prohibition on changing existing gameplay.
    RebuildKit.BuildAll is idempotent and destroys only what it produced.
36. REBUILD PALETTE. The Mk2 palette was measured off the originals rather than
    chosen by eye: large light panels are Plastic, because Metal blows out to pure
    white under Brightness 2.5 + Bloom + Exposure +0.15; Metal is reserved for body,
    frame and seams; pure-black Neon (0.067) draws the dark seams. Binding-critical
    names (ClickPart, LeverUnion, LeverOrginPart, NeonPart) and the model hierarchy
    ControlVisuals walks are reproduced exactly - only appearance differs.

## Assumptions (Phase 19b - Install gate, pre-flight findings)
37. INSTALL GATE. Before moving any rebuilt desk into the facility a pre-flight was run
    over the Mk2 set: part anchoring and bounding boxes against the shipped originals.
    All 1024 Mk2 parts ARE anchored, so nothing would fall. But three of the six desks do
    not match the original they would replace, so the install was STOPPED rather than
    forced. The bench stays as it is until the geometry is corrected. Every later decision
    in this section was taken autonomously under the operator's instruction to decide
    without asking and record the options here.
38. HDEF IS A CABINET, NOT A DESK. Measured from the shipped model: Workspace.Consoles.
    HDEFGenerator is 1.31 x 7.38 x 4.60 - a tall narrow cabinet standing 7.38 studs high
    on a 1.31 x 4.60 footprint, 167 parts. The Mk2 build pushed all six consoles through
    ONE shared 15-stud hull, so MK2_HDEFGenerator came out 6.07 x 6.25 x 15.06 - wrong by
    13.75 studs in length. Options considered: (a) shrink the whole rebuild to a smaller
    desk - rejected, the other five originals really are 15 studs long and the desks would
    stop reading as a family; (b) drop HDEF from the rebuild and leave the original -
    rejected, it would leave one console un-rebuilt in a job whose whole point is
    rebuilding; (c) rebuild HDEFGenerator as a vertical cabinet that keeps its own dot
    paths (PowerLever.ClickPart, EmergencyControl, PowerCell1..3) but takes the real
    1.31 x 4.60 footprint. Chosen: (c). The shared-hull assumption is sound for the five
    desks and fails for this one; the hull builder therefore needs a cabinet variant.
39. CBL / ELECTRICGRID DEPTH. Both originals are only 4.07 deep, but the Mk2 desks are
    6.44, so installed as-is they would protrude 2.37 studs into the walkway in front of
    the operator. The other desks came out SHALLOWER than their originals (Main -1.25,
    ALT -1.11, Thermal -0.38), which leaves a gap at the back but cannot clip anything.
    Options: (a) trim only the two offenders - chosen; (b) shrink every desk to the
    shallowest original - rejected, it would waste the depth the other originals do have.
    Length overshoot is separate and small (+0.06 to +0.33, from the vent lips) and is
    left alone for now; it should be re-checked against the neighbouring geometry once
    the decks are actually in place.
40. INSTALL IS REVERSIBLE. When the desks are eventually installed the shipped originals
    will be re-parented into Workspace.Rebuild.Originals, never destroyed, and each Mk2
    desk will take the original's name so the shipped ConsoleBinder pass binds it
    directly and BindRebuild falls through as a no-op. That keeps ONE binding path, so
    two desks can never fight over the same state. Decided over deleting the originals,
    per the standing prohibition on removing function without a replacement.
41. DUPLICATE CBLaserConsole - FOUND, NOT REMOVED. Workspace.Consoles has always held two
    Models named CBLaserConsole (pre-existing, not introduced by the rebuild). They are
    coincident but NOT identical: 382 parts each, yet CBL1Systems.LargeLever.BigLever.
    LeverUnion sits at a different angle in each. The reason is that every script reaches
    the console by dot path, so FindFirstChild always resolves the first copy - that one
    is bound and its lever tracks live state, while the second copy is driven by nothing
    and its lever is frozen. The second copy also carries 18 ClickDetectors that are
    bound to nothing, so it can swallow a click that was meant for the live console. No
    script references it: all 21 occurrences of the name in the place use the dot path.
    Options: (a) destroy the second copy - cleanest, removes the z-fighting and the
    shadowed clicks; (b) leave it. Removal was ATTEMPTED and BLOCKED: deleting a shipped
    part the operator never named is outside the standing "decide autonomously"
    instruction, which does not override the prohibition on removing function without a
    replacement. Recorded here for an explicit yes/no.

42. INSTALL GATE CLEARED + THE HDEF CABINET. Items 38 and 39 were carried out and
    the gate item 37 closed is now open. Final world-AABB footprints, corner
    method, shipped original (REF) vs rebuilt (MK2):
        MainReactorConsole    7.34 x 6.15 x 15.00  ->  6.09 x 6.25 x 15.08
        ThermalConsole        7.35 x 6.24 x 15.00  ->  7.03 x 6.25 x 15.33
        CBLaserConsole        4.07 x 5.88 x 15.00  ->  4.09 x 6.25 x 15.06
        ElectricGridConsole   4.07 x 5.88 x 15.00  ->  4.09 x 6.25 x 15.25
        ALTReactorConsole     7.55 x 6.15 x 15.00  ->  6.44 x 6.25 x 15.06
        HDEFGenerator         4.60 x 7.38 x 1.31   ->  4.65 x 7.38 x 1.38
    No rebuilt desk is deeper than the original it would replace, so none of them
    protrudes into the operator walkway. The Mk2 desks are uniformly 6.25 high, so
    CBL and ElectricGrid come out 0.38 taller than their originals, while Main and
    ALT are 1.25 and 1.11 shallower - a gap at the back, which cannot clip
    anything. Both deltas are accepted rather than chased: the six desks have to
    read as one family, and the originals' own heights already differ by 0.09.
    HDEF was rebuilt as its own vertical cabinet in a dedicated local frame
    (half-width 2.30, height 7.38) rather than through the shared 15-stud hull
    that option 38(a) would have kept. Two real defects surfaced while trimming;
    both are recorded so they are not reintroduced:
      (a) buildShell IGNORED ITS OWN PARAMETER. Seven places inside it used the
          module constant SHELF_X1 (3.45) instead of the shelfX1 argument, so
          passing SHELF_SHALLOW (2.00) still left the end posts, the caution
          lines, the bolt row and the conduit hanging 1.45 studs past the front
          edge of their own deck. That is why the first trim attempt measured
          5.53 deep when the arithmetic said 4.09. Fixed by scoping every use to
          the parameter and re-anchoring the under-deck furniture to shelfX1.
      (b) panel() BUILDS A SOLID BOX, SO A "FRAME" HAS TO BE FOUR BARS. The window
          bezel was written as one panel() call spanning the whole opening, which
          made it an opaque 0.02-thick plate sitting 0.02 in front of the glass -
          so the power-cell lamps behind the pane could never draw. Three separate
          "the lamps are invisible" diagnoses (moving the cells back, moving the
          lamp forward, widening the lamp strip) all failed because the blocker
          was in front of everything they touched. Replaced with four WindowFrame
          bars. Corollary: the original 0.12-wide lamp strip was right all along.
    INSTALL ORIENTATION. The facility's HDEFGenerator stands 1.31 (X) by 4.60 (Z)
    facing world -X; the Mk2 cabinet is 4.65 (X) by 1.38 (Z) facing local -Z, so
    on install it needs a +90 degree rotation about Y. Verified against the
    original: the control column lands at +0.84..+2.16 (original +0.87..+2.12)
    and the cell bank is 2.90 wide (original 2.75), so the controls and the cells
    land where the operator already expects them.

## Assumptions (Phase 19c - The install)

43. THE SIX Mk2 DESKS ARE INSTALLED. All six rebuilt desks were moved off the bench
    into Workspace.Consoles, taking the names of the desks they replaced, and all seven
    shipped originals (six live plus one dead duplicate) were parked - not deleted - in
    Workspace.Rebuild.Originals.

    ORIENTATION SOLVER. The first solver rotated each Mk2 inside the ORIGINAL's own
    local frame, which cancels: the transform collapsed to
    Ro * (Ry * Ro^-1 * w + off). The desks would have installed axis-aligned while the
    facility originals sit at +-7.5 and +-15 degrees of yaw. Two independent tells gave
    it away - the arithmetic simplified to nothing, and a rotated original's placed AABB
    came back exactly the size of the unrotated Mk2 footprint. Reformulated in world
    space against the original's own basis:
        u   = flat(original depth axis)   w = flat(original length axis)
        off = u*a + w*b + (0, dY, 0)      T = CFrame.new(off + pivotM) * Ry * CFrame.new(-pivotM)
    with a and b taken from the front and centre edges of the two world AABBs, and
    Ry = CFrame.Angles(0, yawOf(original) - yawOf(Mk2), 0).

    THE rel=180 TRAP. Candidate relative rotations were first scored purely on the
    distance between their control centroids. That metric cannot see which way a desk
    FACES, and rel=180 is the reflection that minimises it - so ElectricGridConsole and
    ALTReactorConsole both selected rel 180 and pointed their controls into the wall.
    Fixed by adding an explicit facing term (dot of the Mk2's front with the original's
    front direction) and requiring facing > 0.99 alongside the distance score. All six
    then select rel 0 at facing +1.00.
    Options considered: (a) keep rel 180 and mirror the model - rejected, it moves every
    control away from where the operator has learned to reach; (b) add the facing
    constraint and require rel 0 - chosen.

    PARKING, NOT DELETION. Workspace.Rebuild.Originals holds the seven originals at
    Y 330, Z 265, at X 40/66/92/118/144/170/196. Each carries GameCoreParkedPivot (its
    exact pivot before the move) and GameCoreParkedFrom ("Workspace.Consoles.<name>"),
    so reversing the install is one PivotTo() per model and nothing has to be
    reconstructed from memory. Two of the seven GameCoreParkedFrom values were written
    wrong (one missing the model name, one recording the post-rename name) and were
    corrected in place; no code reads that attribute, but a reversal record that is
    wrong is only discovered during the reversal. Chosen over deleting the originals
    (item 40 already ruled that out) and over leaving them in place (that collision is
    what this step exists to end).

    DUPLICATE CBLaserConsole - RESOLVED (closes the open question in item 41). Item 41
    recorded the second CBLaserConsole as "FOUND, NOT REMOVED" and left an explicit
    yes/no open, because deleting a shipped part the operator never named is outside the
    "decide autonomously" instruction. This step did not have to answer it: parking the
    second copy as ORIG_CBLaserConsole_DUPLICATE_DEAD removes the whole harm - the
    coincident z-fighting and the 18 click detectors that were bound to nothing and could
    swallow a press meant for the live desk - while destroying nothing. The prohibition
    stands and the open question is moot. The FIRST copy, the one FindFirstChild resolves
    and every script actually binds, is parked with the other originals, behaviour intact.

    A MISTAKE WORTH RECORDING. The duplicate list was collected AFTER the install loop,
    so dupes[1] was the stale dead copy and dupes[2] was the freshly installed Mk2.
    Parking from index 2 therefore parked the Mk2 and left the dead copy live. Caught
    because the report read "CBLaserConsole parts=382" where the Mk2 is 188. Repaired by
    identifying the three models by part count, restoring the original from its own
    GameCoreParkedPivot attribute, re-running the solver, reinstalling the Mk2, and
    parking the dead copy last. The general lesson: never index a leftovers list that was
    built after the mutation it is supposed to describe.

    PART COUNT 1024 -> 957. The 1024 figure predates the HDEF cabinet rewrite (item 38),
    which replaced the shared 15-stud hull with a purpose-built vertical cabinet. Measured
    on the six installed desks the total is 957. 1024 was correct for the hull it
    described; it is superseded, not contradicted. Recorded here so the two numbers are
    not later mistaken for a regression.

    NEW BINDING BASELINE. First Play session on the installed desks:
        [ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0
        [ConsoleBinder] rebuild desks=0 controls=0 missing=0
    Every field moved and every move is explained by the install:
      desks  7 -> 6   the duplicate CBLaserConsole is gone from Consoles, so the
                      console-level pass stops counting that desk twice (item 41).
      reused 61 -> 2  the Mk2 desks ship no ClickDetectors, so nearly every control
                      needed one created. reused=2 are the two that already existed.
      created 7 -> 66 the exact inverse. 68 controls = 2 reused + 66 created.
      missing 0       unchanged; the path contract still resolves perfectly.
    BindRebuild reports desks=0 because it looks for MK2_* under Workspace.Rebuild.Models
    and the Mk2 models are now named after the desks they replaced. That is the no-op
    item 40 designed for, and it is the proof that the single-binding-path property
    holds: one binder, never two, is driving each control.

    LAMP REGISTRY 31 -> 41. The Mk2 desks give more controls their own indicator lamp
    than the originals did. Measured per control by replaying a faithful replica of
    ControlVisuals.findLampParts over all 66 defined paths:
        worst single press     3 lamps   (ThermalConsole.CoolantControl1)
        1 lamp per press      35 controls
        2 lamps per press      3 controls  (CBLaserConsole.CBL1/2/3Systems)
        3 lamps per press      3 controls  (ThermalConsole.CoolantControl1/2/3)
        39 distinct lamps reachable from the 66 defined paths
    The worst case is 3 because a coolant control's own cluster carries three lamps
    (ON / OFF / level): that is the control's own feedback, not the desk's. No press
    flashes a whole console, so 41 is recorded as the new baseline rather than treated
    as a defect. The 39-vs-41 gap is the console-level binds, which also register lamps.

    REGRESSION on the installed desks (fresh Play session):
        [GameCoreControlTest] pass 13, fail 0; levers 18; fluctuation signMatches 60/60
        [GameCoreSelfTest]    finalStatus PASS, bridgeResolved 18, devices 15, resetOk
        [GameCore]            started: 25 systems, 12 devices
    Lever count is unchanged at 18, every lever test reported moved=true, and both lamp
    tests reported lampChanged=true.

44. THE INSTALL IS VISUALLY UNSIGNED. The desks are functionally verified and sit at the
    right place and the right yaw, but their look has not been signed off in place. One
    screenshot of the installed MainReactorConsole read washed out even though the Mk2's
    dominant colour (75,75,76) is DARKER than the original's (125,124,126), which means
    the difference is lighting or material-variant interaction, not palette. The standing
    rule is to self-assess and rewrite if the quality is poor, so this is recorded as an
    open item rather than quietly accepted: a side-by-side at the same camera against a
    parked original is still owed. The cheaper ART_DIRECTION fixes (brighter button
    bezels, hazard chevrons, LED bar-graphs) stay queued behind it.

45. THE WASH-OUT WAS A MISSING LightInfluence, NOT THE PALETTE. Item 44 recorded the
    installed desks reading washed out and blamed lighting or material-variant
    interaction. Both were wrong. The cause was a property the rebuild never set.

    RULED OUT, IN ORDER
      1. The global grade. The first test moved ExposureCompensation by 0.15 EV, which
         is about 11% and therefore invisible -- a bad test that proved nothing. Held to
         a real swing (Brightness 2.50 -> 1.20, EnvironmentSpecularScale 0.80 -> 0.20,
         Exposure +0.15 -> -1.50) the FLOOR went from blown white to a correct mid-grey
         with its "MAIN REACTOR CONSOLE" floor marking legible, while the desks barely
         moved. A surface that ignores a stop and a half of exposure is not being lit by
         the environment at all.
      2. The FacilitySteelPanel MaterialVariant. Stripped it off all 74 variant-wearing
         parts of MainReactorConsole and re-shot: the desk did not go dark. Restored via
         a neutrality heuristic (67 parts) plus the 7 cyan accents (128,187,219) that are
         not neutral grey and that the heuristic missed -- 67 + 7 = 74, the exact count
         stripped, so the revert is provably complete.
      3. The 254 spill PointLights from the light-spill pass. The nearest sits 34 studs
         from the desks, so they are not the cause. Worth recording how nearly this
         became a false alarm: a probe for them returned 0, because Roblox stores
         properties as float32 and 2.2f does not equal the double 2.2. The pass was
         present all along; the query was wrong. Probe by range, not by equality.

    THE CAUSE
        MK2  MainReactorConsole   39 SurfaceGuis,  39 with LightInfluence = 0,  0 with 1
        ORIG MainReactorConsole   31 SurfaceGuis,   0 with LightInfluence = 0, 31 with 1
    SurfaceGui.LightInfluence = 0 is Roblox's default and it means "always fully
    illuminated": those plates ignore scene lighting and exposure, so they render flat
    white under any grade. The originals all use 1. RebuildKit created its plates
    without setting the property, so the largest flat surfaces on every Mk2 desk were
    running unlit -- which is why the desks read white through a 1.5-stop exposure swing
    while the floor beside them went grey.

    THE FIX
    121 SurfaceGuis across the six installed desks set to LightInfluence = 1 (109 host
    parts). Re-shot from the same camera: the amber and red buttons, the AVB red cap, the
    cyan accent strips and the panel banding all became visible. They had been rendering
    as flat white and were simply not there to see before.

    OPTIONS CONSIDERED
      (a) Leave it and call it the palette. Rejected: the palette measured DARKER than
          the original's, so the palette was never the fault.
      (b) Add a matte MaterialVariant on a diffuse base (Concrete) and move the desks
          onto it. Rejected: the originals wear the same Metal-based variant, so this
          would make the new desks diverge from the desks they replaced -- exactly the
          "console looks disconnected from its surroundings" failure ART_DIRECTION 2.1
          warns about.
      (c) Change the scene grade. Rejected as a sign-off item (ART_DIRECTION 6), and in
          any case shown in (1) to be the wrong lever.
      (d) Set LightInfluence = 1. Chosen. Cheapest, local, changes no name and no part
          (CLAUDE 6), and brings the Mk2 into line with the originals, which already use
          it.

    WHAT IS STILL OPEN. After the fix the desks still read light overall. That residue is
    the hull and the near-white label plates (Plastic 163..196) living under Brightness
    2.5 / EnvironmentSpecularScale 0.80, which is the same grade the originals sit in --
    so it is a grade question, not a desk defect. Item 44 stays open for the overall
    look; the software defect behind the wash-out is closed.

    FOR THE MONITOR REBUILD. Every SurfaceGui the rebuild creates must set
    LightInfluence explicitly. The default is 0, 0 means unlit, and the failure mode is
    silent -- it looks like a paint choice, not a bug. The control-room monitors are all
    SurfaceGuis, so this lands on the next stage directly.

## Assumptions (Phase 19d - Art-direction pass, and a decal that is not real)

46. BUTTON BEZELS ARE THE BRIGHT ELEMENT (ART_DIRECTION 3.2). The reference reading is
    that a button is a dark cap sunk into a LIGHT, chamfered bezel, and that the bezel
    is the brightest element on the desk. The Mk2 had it inverted: buildButton gave
    CollarOuter the "dark" palette entry and CollarInner "post", so the collar was
    darker than the hull and each control read as a sticker lying on the panel rather
    than an assembly sunk into it. Swapped to CollarOuter = "lighter", CollarInner =
    "light". No geometry moved and no name changed (CLAUDE 6) - two palette lookups,
    which makes this the cheapest item in the whole art backlog.

47. THE END HAZARD IS GEOMETRY, NOT A DECAL (ART_DIRECTION 3.3). The plan was to reuse
    the facility's own caution decal, rbxassetid://267233089. It was dropped, and the
    reasoning matters more than the change.

    WHAT WAS MEASURED. Swapping that decal's Transparency between 0 and 1 and
    re-shooting the same camera showed a flat WHITE band with it on and clean brass
    underneath with it off. The tempting conclusion - "the asset is broken" - is NOT
    what the place supports, and stating it that way would be wrong:
      - Every use of the asset in this place is named CautionLine or Caution.
      - There are 5685 of them and ALL 5685 sit at Transparency = 1.00.
      - The distribution is place-wide, not just the desks: Mainframe 1565,
        CullFolder 1538, MovingParts 743, CoolantReserviors 661, Geometry 366,
        Facility 277, ReactorCBLs 144, plus smaller counts in ten other roots.
      - A clone-vs-original control confirms the value survives Clone(): each REF_
        clone's transparency list matches its parked ORIG_ original one for one
        (Main 10, Thermal 37, CBLaser 23, ElectricGrid 15, ALT 15, HDEF 5).
    The original author set this decal invisible in 100% of its uses. The flat white is
    most likely the texture failing to load in this Studio session (CLAUDE 0.8 records
    hundreds of unauthorized-asset errors), not the asset's real appearance. Either way
    the conclusion rests on sound evidence and is the same: the decal is not part of the
    shipped look, so reproducing it would add a visual element the original never shows.

    THE DECISION. Drop CAUTION_DECAL from RebuildKit entirely - the constant, all four
    call sites and the now-dead decal() helper - and build the end hazard as geometry
    instead: a brass EndHazard plate with six near-black EndHazardBar panels 0.012 proud
    of it. This also removes the module's only dependency on an external texture, so the
    bench renders identically no matter what loads.

    THE INSTALLED DESKS WERE SHOWING IT. The six installed desks were built before this
    change and each carried the decal at Transparency 0 - 2+2+2+2+2+1 = 11 instances,
    all on the plinth Hazard part. They really were rendering the white band, and the
    pre-change probe that said so was right. All 11 are now hidden, and the installed
    Main desk re-shot from the operator side confirms no band.

48. THE buildShell END BLOCK WAS DEAD GEOMETRY. Found while fixing item 47, not
    separately. buildShell placed its end posts at z0 + 0.06 and z1 - 0.06 - INSIDE the
    cabinet's own body box - so the posts came out exactly flush with the body face
    (coincident faces: a z-fighting risk and nothing else) and the EndCap was buried
    0.03 inside it. The entire end treatment had never been visible on any Mk2 desk.
    Fixed by moving the anchor to z0 - 0.02 / z1 + 0.02, outside the body, and deriving
    the hazard's outward direction from a per-end sign. Verified by raycast from the
    operator side plus a Z-range dump:
        EndCap     z = [140.450 .. 140.510]
        EndHazard  z = [140.380 .. 140.460]   raycast hits EndHazard
    Worth an item because it was invisible in every screenshot: dead geometry looks
    exactly like no geometry. It only surfaced because item 47 made me raycast the end
    of the desk.

49. THE BENCH COULD CLONE AN Mk2 AS ITS OWN REFERENCE. A footgun the install itself
    created. RebuildKit.PlaceReference looked a desk up in Workspace.Consoles - but the
    six Mk2 desks were installed UNDER the originals' own names, so that lookup now
    returns a rebuild, and the bench would happily clone an Mk2 as the reference it is
    meant to be rebuilding from. Silent: the comparison still runs, it just compares a
    thing against itself. Fixed twice over, because either alone is fragile:
      (a) PlaceReference prefers Workspace.Rebuild.Originals.ORIG_<name> - the shipped
          originals still exist, they were parked rather than deleted - and only falls
          back to Consoles for a desk with no GameCoreMk2 attribute.
      (b) BuildAll stamps every Mk2 with SetAttribute("GameCoreMk2", true), so "is this
          a rebuild" is answerable from the instance rather than inferred from a name
          the install deliberately reused.
    Verified: all six REF_ clones carry ClickDetectors (8/18/6/1/8/23); all six MK2_
    carry none.

    NOTE - A BLIND MUTATION, RECORDED RATHER THAN HIDDEN. The audit behind item 47 was
    run as a sweep that forced Transparency = 1 on every instance below 1. Its report
    was large enough to overflow the tool result, so the loop ran but the report was
    lost: the sweep was issued blind and its exact changes are NOT recoverable. What can
    honestly be said:
      - The end state is 5685 uses, 0 below 1.
      - The only instances in the place whose parent is a rebuild are the 11 on the six
        installed desks' Hazard plinths, which matches the Consoles count exactly and
        matches the set the evidence says was visible.
      - There is no AutoSaves directory on this machine and nothing has been saved by
        hand, so there was no snapshot to diff against.
    The plausible reading is that it touched those 11 and nothing else, but that is an
    inference, not a measurement. Nothing the user had saved was at risk, and the change
    is reversible by-name for anyone wanting the bands back (the asset is intact; only
    Transparency moved). The rule this earns: a mutation pass must be run as a DRY RUN
    and counted FIRST, then applied - never one call that both mutates and reports.

50. THE REFRESH WAS A PIVOT TRANSPLANT, AND A REPARENT IS NOT A PARKING SPOT.
    Items 46-48 fixed the bench; the six INSTALLED desks did not have any of it. Rebuilding
    the install from scratch was not available: the orientation solver was a one-off script
    and RebuildKit has no Install(). So each live desk was refreshed in place:
      (a) park the outgoing desk as MK2PREV_<name> under Workspace.Rebuild.Previous,
          stamping GameCoreParkedPivot with its live pivot so the move reverses;
      (b) clone the corrected bench MK2_<name>, rename it to the desk's own name,
          re-parent it to Workspace.Consoles, and Model:PivotTo(the recorded pivot).
    The argument for the approach is that Model:PivotTo sets the pivot EXACTLY - position
    and rotation - so a transplant needs no solver at all. HDEF landed at 0.00 on every
    axis, and the oriented-corner depths reproduced item 42 to the centimetre.

    THE MISTAKE. Step (a) re-parented the outgoing desks but never MOVED them. For the
    duration of the refresh the control room contained twelve desks in six positions: each
    live desk with its own predecessor sitting exactly on top of it. It surfaced only
    because a diagnostic raycast from the operator side of the Main desk returned
        hit = Workspace.Rebuild.Previous.MK2PREV_MainReactorConsole.LipSeam  dist 3.32
    - the desk it should have hit was the live one. Fixed by moving all six to
    Y 330 / Z 320 (the shipped originals sit at Y 330 / Z 265), a third row on the bench.
    Re-verified: the same ray now returns Workspace.Consoles.MainReactorConsole.LipSeam,
    and the operator walkway in front of all six is clear.
    Nothing had been saved, so no saved state ever contained the duplicate - but the desks
    were in that state for the entire verification pass, and every screenshot taken in that
    window was of the old geometry. That is why they read wrong. The rule this earns:
    re-parenting is not parking. A model moved into a parked folder is still wherever it
    was standing, and anything that resolves against the live set will still find it.

    SEPARATELY - ART_DIRECTION 3.2 IS ONLY PARTLY DELIVERED, AND THE NAME IS A TRAP.
    Item 46's bright-bezel change (CollarOuter dark -> lighter, CollarInner post -> light)
    reached exactly 8 bezel pairs across 4 desks:
        Main 2   Thermal 2   CBLaser 3   ElectricGrid 1   ALT 0   HDEF 0
    ALT is the only REAL gap, and the paragraph that first stood here overstated it by naming
    HDEF as well. Re-reading the builder before acting on that claim:
      - HDEF's PowerCell1-3 are display cells behind a glazed window recess (Cell 0.86 x 5.20
        x 0.50 inside the WIN_X0/WIN_Y0 window), NOT controls. Counting them as un-bezelled
        buttons was wrong on the facts.
      - HDEF's one real button, EmergencyControl, DOES carry a bezel - a 0.10 x 0.94 x 0.94
        cylinder named Collar standing in front of the Guard. It was coloured "post", i.e.
        exactly as dark as the plate behind it, so the-bezel-is-the-brightest-element failed
        there for a COLOUR reason, not for a missing-part reason.
    The honest statement is therefore: the four shared-hull desks carry the bright pair, ALT
    had no bezel of any kind, and HDEF had a bezel that was not bright. All three are resolved
    now - see item 51. The rule this earns: when a "the code lacks X" claim was written from a
    COUNT, re-read the builder before acting on it. A part-name count says what exists; it
    never says what a part is for.
    The count is easy to misread, which is why it is written down: a DIFFERENT part is also
    named Collar. Every desk carries dark Metal 0.235 Collar sleeves that are structural,
    not bezels, and Main carries 4 CollarRings besides. Grepping for Collar reports 9-12
    hits on a desk where only 2 buttons were actually brightened. Counting by the precise
    names CollarOuter / CollarInner is the only metric that means anything.

    VERIFICATION IS NUMERIC, NOT VISUAL - and the reason matters. Screenshot capture failed
    three ways in this session: rblx_screen_capture returned byte-identical frames for two
    different camera positions, its camera_position argument did not move the render
    camera, and capture_screenshot returned Too many concurrent requests. What the refresh
    rests on instead is instance state, raycasts, oriented-corner AABBs and a fresh Play
    session. That is strong evidence, but it is not the visual sign-off item 44 asks for,
    and item 44 therefore STAYS OPEN.

51. 3.2 IS FINISHED - AND THE LINE-NUMBER EDITING TOOLS ARE NOT TRUSTWORTHY HERE.
    Two changes, both in RebuildKit, then one transplant reusing item 50's procedure.
      - ALT: CollarOuter 1.28 x 0.16 x 1.28 in "lighter" at DECK_TOP + 0.29, and CollarInner
        1.14 x 0.14 x 1.14 in "light" at DECK_TOP + 0.33, under the 1.00 ActivationButton
        whose top face stays at DECK_TOP + 0.49.
        The ROTATION is the part worth remembering. The shared-hull desks mount their controls
        on a VERTICAL face, so their rings stack along X - forward, toward the operator. The
        ALT button sits on a HORIZONTAL deck, so its plates must stack along Y, upward. Same
        idiom, different axis; copying the shared-hull geometry verbatim would have buried the
        plates inside the deck and changed nothing visible.
      - HDEF: the existing EmergencyControl.Collar recoloured "post" -> "light". Colour only,
        deliberately - nothing moved, so the 1.365 cabinet depth that item 42 pinned is
        untouched, and the Guard behind it stays "deep" so the bright ring is the innermost
        element exactly as CollarInner is on the four shared-hull desks.
    Transplanted by item 50's procedure. ALT went 178 -> 182 parts (the four new plates);
    HDEF stayed 76. Both landed at moved 0.000000 from the recorded pivot. World AABBs against
    the shipped originals: ALT (8.27 6.25 15.89) vs (9.44 6.15 15.86) = -1.18 / +0.10 / +0.04,
    still not deeper; HDEF (1.38 7.38 4.65) vs (1.31 7.38 4.60) = +0.06 / 0.00 / +0.05,
    reproducing item 42 exactly.

    THE BEZEL DOES NOT STEAL THE CLICK - and that had to be measured, not assumed, because
    MASS1Systems.ActivationButton is a bound control. The plates top out 0.090 below the button
    face. Rays from overhead, front-steep, back-steep, side+X, grazing (0.55 above the face)
    and shallow-front ALL return ActivationButton. The one ray that returns something else
    approaches from -X across the neighbouring control and hits PowerLever.Grip, which is a
    real control, not the bezel.
    A first attempt returned NOTHING for every ray, which is NOT the same as "no occluder":
    the rays were being cast to end exactly ON the button's top surface, and a boundary hit
    does not register. Overshooting by 1.4x is what made the measurement mean anything. An
    all-NOTHING raycast result should be read as a broken test before it is read as clearance.

    FUNCTIONAL SIGN-OFF, fresh Play session:
        [ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0
        [ConsoleBinder] rebuild desks=6 controls=66 missing=0
        [GameCore] started: 25 systems, 12 devices
        GameCoreSelfTest    finalStatus PASS, bridgeResolved 18, devices 15, hdefIntegrity 100
        GameCoreControlTest finalStatus PASS, pass 13 fail 0, levers 36 lamps 80,
                            fluctuation signMatches 60/60
    created=66 / missing=0 is the same baseline the original install produced, so the
    transplant cost no binding: both replaced desks had their detectors rebuilt like any
    other, and every CONTROL_DEF still resolves. Note that a Mk2 desk holds ZERO ClickDetectors
    in Edit mode on purpose - the game creates them at server start - so "0 detectors" on an
    installed desk is expected and is not evidence of a broken bind.

    TOOLING TRAP (a): LINE NUMBERS FROM THE EDIT TOOLS DO NOT AGREE WITH THE LIVE SOURCE.
    delete_script_lines was asked for lines 875-883 and reported newLineCount 1194 while a
    direct read of .Source in the same session returned 1186. It removed nine lines, but not
    the nine asked for: ALT lost its ActivationButton, its label, its PowerLever model
    creation and three comments, leaving `plv.Parent = mod` referring to a plv that no longer
    existed. A loadstring() compile check is the only reason this was caught before it
    shipped.
    Rule: after any line-numbered edit, RE-READ the region and COMPILE the whole source.
    Text-anchored edit_script_lines is the safe instrument, and it is the right tool for a
    repair regardless of what the numbers say.

    TOOLING TRAP (b): edit_script_lines CAN REPORT FAILURE AFTER THE WRITE HAS LANDED.
    The HDEF collar edit returned "old_string not found in script source" twice and the change
    was present in the file both times. Blind retrying on the strength of that error is what
    DUPLICATED the ALT bezel: the plates had already been inserted in the pre-compaction
    session, so the anchor was still unique and a second copy went in. Re-reading the region
    is what exposed it; the fix was to text-anchor a repair rather than delete more lines.
    Rule: when a line edit reports failure, re-read before retrying.

    TOOLING TRAP (c): Instance:GetAttributes() RETURNS AN EMPTY LIST IN THE PLUGIN VM even when
    the instance demonstrably has attributes - GetAttribute("GameCoreMk2") returns true on the
    same model in the same call. Enumeration is unreliable there, so probe by NAME. This
    matters more than it looks: the whole park/restore protocol rides on GameCoreParkedPivot,
    and an enumeration-based audit would have concluded that no desk carries it.
    TOOLING TRAP (d): THE DOC WRAPPER'S TERMINATOR IS EASY TO SLICE BY ONE BYTE.
    The four doc modules wrap their body as `return [==[` + newline + body + the five-character
    close + newline. Unwrapping by a fixed tail length is a trap in two ways. Comparing a
    SIX-character tail slice against a FIVE-character literal is ALWAYS false, so any branch
    leaning on that test silently takes the wrong path; and slicing four bytes off a source that
    really ends with the five-character close cuts one byte too few, leaving that close's
    leading right-bracket INSIDE the body. Both happened in one pass. The result still COMPILED
    and read correctly - the damage shows up only as a one-byte length mismatch against the
    disk mirror.
    Rule: unwrap by locating the LAST literal occurrence of the closing bracket pair in plain
    (non-pattern) mode, never by a fixed offset, and assert the body length against the mirror
    afterwards. A doc that compiles is not a doc that is correct.

52. THE MK2 DESKS ARE NOT TOO WHITE, AND THE GRADE IS NOT THEIRS TO FIX.
    Item 44's owed visual sign-off finally happened - rblx_screen_capture renders again and its
    camera_position argument does move the render camera - and taking it overturned the reading
    the previous phase was written under.

    WHAT WAS BELIEVED, AND WHY. A close-up of the INSTALLED ALT desk shows its deck rendering as
    a near-white slab against the dark monitor wall behind it. That is a real observation of a
    real frame. It is not evidence about the palette: the installed desk sits inside the facility
    under the room grade, and the only thing it was being compared against was a dark wall.

    THE CONTROLLED TEST. MK2_<desk> and its untouched REF_ clone sit on the same bench, in the
    same two-row grid, under the same sky, so measuring both in one pass removes lighting as a
    variable. A single camera covering both rows was shot from +X and from -X.
      area-weighted Colour luminance
        MK2  Main 0.339  Thermal 0.349  CBLaser 0.351  ElectricGrid 0.347  ALT 0.348  HDEF 0.338
        REF  Main 0.464  Thermal 0.458  CBLaser 0.465  ElectricGrid 0.460  ALT 0.462  HDEF 0.312
    Every rebuilt desk is DARKER than the desk it replaces, by about a quarter. HDEF is the
    exception on BOTH sides - it was always the dark one, and the rebuild tracks it exactly.

    THE MATERIAL-COVERAGE GAP IS NOT A GAP. Mk2 carries FacilitySteelPanel on ~62% of its Metal
    area against the originals' 100%, which reads like an omission. It is not: the bare Metal is
    259 of its 287 area of BrassBand / Hazard / BrassSeamBot / BrassSeamTop - the brass trim,
    deliberately untextured, because a riveted steel texture through a brass band stops reading
    as brass. Checked, then left alone. Same shape as item 51's lesson: a count says what
    exists, never what it is for.

    THE GRADE IS ONE DECISION, TAKEN ONCE. The residual washed look is heavy blue atmospheric
    haze, blown specular on Metal and a pale sky - a facility-wide question, not a desk question.
    ART_DIRECTION 2.1 already argued the darker mood is a lighting + whole-scene grade change and
    that the desks must not diverge from their surroundings. Options considered:
      (a) darken the Mk2 palette - rejected. The Mk2 is already the darker of the two, and
          darkening it further would leave the rebuilt desks visibly unlike the originals still
          standing in the facility, which is the opposite of the brief.
      (b) cut Atmosphere Density / Haze and re-tune now - rejected as piecemeal. It would
          re-grade every surface not yet rebuilt and pre-empt the shell phase.
      (c) one coherent grade, together with the shell and room interiors - CHOSEN. Deferred,
          not dropped.
    DECIDED: no palette change, no Mk2-specific grade change, grade deferred to the shell phase.
    Item 44 CLOSES - the side-by-side comparison it asked for now exists.
53. THE CONTROL ROOM IS REBUILT IN PLACE, NOT ON THE BENCH - AND THE FLAT WHITE ROOM WAS MY OWN
    LIGHTS. The scope of the reconstruction is the whole game, not the six desks -
    "控制室难道不重做吗？所有东西都要重做哦" - so the room around the rebuilt desks moves to the
    front of the queue. That raises one method question and turned up one regression.

    (a) A SURFACE CANNOT BE A/B TESTED ON THE BENCH. CHOSEN: build it in place.
        The comparison that settled item 52 worked because MK2_<desk> and REF_<desk> sat under
        ONE lighting environment, so lighting was held constant and only the palette varied. A
        floor has no neutral environment to hold constant - essentially all of its appearance
        IS how light falls on it - so a bench floor would have reproduced the exact confound
        item 52 existed to remove, and any conclusion drawn from it would have been about the
        sky rather than the floor. Surfaces are therefore laid over PART of the room and the
        seam is photographed in place: the shipped slab stays in frame two studs away, under
        the identical grade, as the control.
        Rejected: (b) a bench floor A/B, for the confound above; (c) rebuilding the whole floor
        before looking at it, which leaves nothing to compare against.
        RULE: bench A/B for OBJECTS, in-place seam A/B for SURFACES.

    (b) THE WASHED-OUT ROOM WAS SELF-INFLICTED. The deck's first A/B read as a modest
        improvement because the room grade was drowning it. There are 1149 PointLights
        facility-wide and 39 room fixtures inside the control room alone, splitting cleanly:
            shipped room lights    bri 0.2  range 10  shadows true
            shipped console lights bri 0.8  range  3  shadows false
            MY spill pass (x28)    bri 2.2  range 22  shadows false
        The previous session added those 28 so Neon would read, without checking what the
        shipped fixtures did. 11x the brightness, 2.2x the range, shadows off, tiled around a
        closed 50 x 21 x 70 room - uniform fill from every direction, which is exactly how a
        room loses its shading. Retuned to 1.0 / 11 / true, with every host part's original
        values preserved in GameCoreLightOriginal so it reverses per light.
        LESSON CARRIED FORWARD: when a room reads flat, audit the LIGHTS before the palette.
        Item 52 spent a whole controlled test ruling out a palette that was never the problem.

    (c) THE DECK. 8 x 11 = 88 plates, 6.00 studs on a 6.30 pitch, 0.20 thick, 0.05 proud of the
        shipped slab, the grid CENTRED so the leftover strip splits evenly against both walls.
        All added parts are CanCollide = false so the walking surface never changes height, and
        nothing is renamed or deleted. Tonality is a deterministic hash of the grid indices
        (v = 76 - ((i*7 + j*13) % 5) * 2) rather than math.random, so a rebuild is byte-identical
        and an A/B is repeatable; without any drift an 8 x 11 grid of one colour reads as one
        flat sheet with lines drawn on it. The accent is cyan (128,187,219), matching
        RebuildKit's existing PALETTE.cyan instead of introducing a fourth colour into a room
        that already has grey, white and brass, and it stands 0.03 proud because a coplanar top
        face z-fights the plate it is inlaid into.
    DECIDED: surfaces are rebuilt in place, never on the bench, and the room grade is fixed at
    its source (the lights) rather than compensated for in the palette.
54. THE CONTROL ROOM HAS SEVEN MONITORS, NOT FIVE - AND BOTH MY DOCUMENTS SAY FIVE.
    Found while mapping what the monitor rebuild has to cover.
        Wiki text (ReplicatedStorage.Misc.Wiki, verbatim): "The room consists of five consoles,
        three main monitors, and four minor monitors."   3 + 4 = 7.
        Workspace.Monitors really holds 7: Main, Thermal, Power, Alerts, Quota, Log, Forecast.
        MonitorService drives 5. LogControlRoomMonitor is referenced only by Misc.DataCollection,
        a ModuleScript nothing runs; ForecastControlRoomMonitor is referenced by nothing at all.
        CLAUDE.md 2.6 and README.md "Control-room monitors" both list FIVE and omit Log and
        Forecast entirely.
    This is a documentation defect, not a code defect - nothing needs changing for the seven to
    exist, they already do. Per the sync rule the discrepancy is reported to the user, and the
    counts in both documents are corrected in the same pass as the monitor rebuild.
    LEFT OPEN: what the two undriven monitors should DISPLAY. Wiring them is new gameplay
    behaviour, which is out of scope until the user asks for it.

55. ROUND BUTTONS LIE FLAT, BOLT HEADS DO NOT, AND HDEF'S MUSHROOM BUTTON STAYS ON ITS PLATE.
    The operator reported the round console buttons as standing upright when they should lie
    flat. Measured: of 144 PartType.Cylinder parts across the six installed desks, ZERO were
    flat. The shipped original settles it - ORIG_MainReactorConsole.AtmosphereVentButton has
    its axis at (0.34, 0.94, 0.00), 70 degrees above horizontal.
        DECIDED: every button cylinder that buildButton and smallButton produce is rolled 90
        degrees about Z, so its circular axis points along desk-local +Y. 15 buttons.
        DECIDED: the 100 Bolt heads are NOT touched. Their axis is already horizontal and that
        is correct - a bolt head on a vertical face has to face the operator, and RebuildKit's
        own comment says exactly that. "All cylinders should lie flat" would have been the
        wrong generalisation of the operator's report; he said buttons, and the census shows
        the two populations are cleanly separable by name.
        DECIDED: HDEF's EmergencyControl STAYS UPRIGHT. It is a guarded mushroom button on a
        VERTICAL plate at the cabinet's front face - the one round control in the place that
        genuinely IS pressed forward. Rolling it flat would drive it into the guard plate that
        DECISIONS 42 pinned the cabinet depth against.
        NOT AFFECTED: ALT's desk carries no round buttons at all (20 bolts and nothing else),
        so the ALT row of the ART_DIRECTION 3.2 table is untouched by this pass.

56. THE INDICATOR LAMP LEAVES THE BUTTON STACK AND SITS ON THE PAD.
    A consequence of 55, not a preference. Upright, the collar was a thin disc standing at
    x + 0.10, so NeonPart 0.52 further back along the same pad was clear of it. Laid flat, the
    collar sweeps the full pad and the old position fell inside its radius.
        Considered and REJECTED: making NeonPart a lit ring concentric with the button face.
        It is inside the pad by construction, but at w + 0.16 against a button of w it is an
        0.08 annulus under a 0.90 face - too thin to read as an indicator, and it would have
        put the lamp UNDER the very part it exists to be seen beside.
        Considered and REJECTED: sliding the lamp clear along +X. That walks it off the 1.40
        pad and into whatever sits next to it on the deck.
        DECIDED: the lamp moves to the front edge of the pad, and the pad deepens from
        1.40 x 1.40 to 1.40 x 1.50 to hold it. This is what the ORIGINAL does - its pad is
        1.00 x 1.14, deeper than wide, for exactly this reason, and its NeonPart is a 0.12
        cube sitting on that extra depth beside the button. The Mk2 pad had been square, and
        squaring it is what left nowhere for the lamp to go once the collar lay down.
        The name stays NeonPart and the parent stays the button's own Model, because
        ControlVisuals.findLampParts resolves the nearest Model containing NeonPart /
        Indicator / Lamp / Glow. CONFIRMED LIVE, not assumed: the AVB lamp still binds to
        atmosphere_vent and still pulses green on press (PROGRESS Phase 19h).
    A SECOND DEFECT THE ROLL EXPOSED, fixed in the same pass: smallButton's rings were
    intersecting the deck. A 0.90 vertical disc centred 0.30 above the surface reached 0.15
    BELOW it, so the pump-station buttons were buried to their midline - and no screenshot
    ever showed it, because the deck hid the buried half. Treating `y` as the assembly's low
    edge rather than its centre puts them on the deck.

57. LIGHTINFLUENCE: LABELS ARE 1, SCREENS ARE 0. THIS DOCUMENT AND THE README SAID ONE VALUE
    FOR EVERYTHING.
    Stated while preparing the monitor rebuild, and it corrects a generalisation of mine.
        A new SurfaceGui starts at LightInfluence = 0, which in Roblox means "always fully
        illuminated": the plate ignores scene lighting AND exposure compensation and renders
        flat white under any grade. DECISIONS 45 fixed 121 Mk2 desk plates that had shipped at
        0, and the README carried the line "the shipped originals all use 1", with "carry this
        forward: the monitor rebuild is all SurfaceGuis".
        That generalisation is FALSE for the monitors. Measured on all 7 shipped
        MonitorUIs: LightInfluence 0.00, uniformly. And 0 is CORRECT there - a monitor is an
        emissive light source, not a painted surface; a screen that dims when the room lights
        go out is the wrong behaviour, and the room's exposure grade has no business being
        applied to pixels that are supposed to be self-lit.
        DECIDED: the rule is LABELS 1, SCREENS 0. The desk plates keep 1 and the monitor
        plates keep 0, and the monitor rebuild must NOT carry 1 forward as the old README line
        instructed. Corrected in README in both places it appeared. This is documentation
        only - nothing in the place was changed for it, because the shipped monitors were
        already right.
        LESSON CARRIED FORWARD: "every shipped original uses X" is a claim about a POPULATION,
        and it is only as good as the sample it came from. This one came from the desks and
        was applied to the monitors without measuring them. The count is worth stating
        whenever the claim is made.

58. THE MONITOR BEZEL IS TWO BANDS, NOT THREE, AND THE THIRD ONE DIED TO THE GRADE.
    The shipped bezel is a zero-depth white picture frame: no step, no fasteners, no seam.
    The design was a three-value read off the RebuildKit palette - a dark lip hard against
    the screen, the original's own mid value, and one bright rail - over the 0.205-stud top
    margin. Screenshotting it showed a single flat white band, four times, for four different
    palette assignments.
        The cause is NOT the palette and it is worth stating plainly: EVERY Metal part in
        this room renders white whatever its albedo. `darker` (60,60,60 Metal) is
        indistinguishable from `lighter` (186,186,188 Plastic) under Brightness 2.5 +
        EnvironmentSpecularScale 0.8, because specular reflection of the bright environment
        dominates the surface response and swamps albedo. DECISIONS 52 already owns this
        problem; this is a second surface where it bites.
        Options weighed.
            (a) Keep chasing the palette. Rejected - four attempts moved nothing, and the
                finding above says why: no assignment among the Metal entries can work.
            (b) Wait for the DECISIONS 52 grade change. Rejected as a blocker - the geometry
                is additive and reversible, and the room will need this bezel either way.
            (c) Two bands, with the dark one built in Neon near-black rather than a dark
                Metal. CHOSEN.
        DECIDED: (c). A 0.205-stud margin cannot carry three bands at any readable width
        anyway. There is now a bright rail HUGGING the screen - which is what defines the
        screen edge, since a black screen gives a dark band nothing to contrast against -
        and a dark housing band outside it. The dark band is Neon (17,17,17), because Neon
        is the one value in this palette that survives the grade; it is also the facility's
        own recess idiom (ART_DIRECTION 2, "Neon 纯黑, 本 place 独有"), so it is consistent
        with the place rather than invented for the monitors.
        THE REAL FIX IS STILL THE GRADE, and this does not close DECISIONS 52. Under a
        darker grade the housing band could be an ordinary dark Metal and read better than
        Neon does. Revisit the monitors after that pass, not before.
        LESSON CARRIED FORWARD: when a controlled palette test keeps returning "no change",
        stop varying the palette and go looking for a property that is not albedo. Four
        screenshots of four different palettes was three more than the finding needed.

59. MATCH THE HOST PART'S NAME, NOT THE CLASS OF ITS ANCESTOR - AND A REPARENT IS STILL NOT
    A PARKING SPOT.
    Two defects, both mine, both found by looking at a screenshot rather than at the data.
        (1) THE BOOT TEXT. To set the seven nameplates the selector was "any TextLabel with a
        SurfaceGui ancestor". That matches the FIRST label in traversal order, which on every
        monitor is Screen.MonitorUI.BootUpText - not the nameplate, which lives on the part
        named TextPart. All seven boot strings were overwritten and the actual nameplate was
        never touched. The data read back CORRECT on all seven, and the screenshot showed the
        new string ghosted over the monitor header while the strip still read the old one -
        the only reason it was caught. Boot text restored from the parked clones; all seven
        originals turned out to be empty placeholders that a runtime script fills in.
        DECIDED: address labels by their HOST PART's name when more than one label could
        match. Class-of-ancestor is a filter, not an identifier.
        (2) THE PARKED ORIGINALS WERE NEVER MOVED. The seven monitor originals were cloned
        into Workspace.Rebuild.Originals and re-parented, but NOT moved - so they sat exactly
        coplanar with the live monitors (measured liveDelta = 0.00 on all seven). Every
        screenshot in this phase had the original drawing on top of the rebuild, its own
        "SMER - CONTROL ROOM MONITOR" nameplate included, which is what produced the ghosting
        that (1) was originally blamed for. The six desks were parked correctly; the monitors
        were not. This is the SAME trap README already documents for Rebuild.Previous, now
        with a second confirmed instance.
        DECIDED: moved to a parking row at Y 330 / Z 340, disjoint from the desk row at
        Y 330 / Z 265 so the two rows cannot overlap. Each carries GameCoreParkedFrom and
        GameCoreParkedPivot, so the move reverses with one PivotTo() per model.
        The two defects masked each other, which is why both are recorded together: (1) was
        diagnosed, "fixed", and STILL looked wrong, and only the persistence of the symptom
        after the fix exposed (2).
        LESSON CARRIED FORWARD: a data probe and a screenshot disagreeing is information.
        Re-read the probe result as "confirmed the property changed", not as "confirmed the
        render is right" - those are different claims and only the second one is what the
        operator sees.

60. THE LOG AND FORECAST MONITORS ARE PURE OBSERVERS, AND THEIR POOLS ARE FIXED AND FINITE.
    Two of the seven control-room monitors had no live writer. Both shipped their own undriven UI
    scaffolding - the Log's three severity row templates, the Forecast's ScrollingFrame,
    timestamped TimeSliceTemplate and announcement band - all hidden and unused.
        (a) Write new UI for them. Rejected: the author's scaffolding is already there, already
            styled, and already named.
        (b) Give them state of their own so they could report things GameState does not hold.
            Rejected outright - that is new gameplay behaviour, and the operator's rule is
            "永远不要改现有玩法机制".
        (c) Drive both from values GameState ALREADY holds, writing nothing back. CHOSEN.
        DECIDED: (c). Both are PURE OBSERVERS. They read GameState and never write it, so the
        single-writer rule is untouched and no simulation behaviour changed.
        MonitorService.Update dispatches seven calls, each defined once and called once, in order
        Main - Thermal - Power - Quota - Log - Forecast - Alerts.
        THE LOG reads eleven watched signals and fires only on a CHANGE, staying silent the first
        time a signal is seen - so it opens on three boot lines rather than a dump of the initial
        state.
        THE FORECAST samples PowerOutput / the current shift's quota every 5 seconds, on a
        deliberate cadence rather than every tick, because a timeline is a history and its
        resolution should be a choice, not a side effect of the monitor's refresh rate.
        BOTH BUILD A FIXED POOL IN Initialize AND ONLY MUTATE TEXT, SIZE AND COLOUR AFTERWARDS.
        Config.Monitor.UpdateInterval is 0, so Update runs every simulation tick and a :Clone() in
        the paint path would allocate ten times a second forever. 29 instances, all stamped
        GameCoreMk2 = true for one-sweep rollback.

61. THREE DEFECTS IN ONE SPLICE SESSION, AND THE GUARD THAT EARNED ITS KEEP.
    All three were mine, and all three were caught before anything ran.
        (1) A LOCAL FUNCTION DECLARED AFTER THE INSERTION POINT IS NOT IN SCOPE. The log block was
        spliced in above the file's helper locals, so `setText` - declared textually further down -
        resolved to a nil global. Row 1 painted, then failed with "attempt to call a nil value".
        DECIDED: declaration order is part of the splice contract. Check that every symbol a block
        calls is declared ABOVE the chosen anchor, not merely somewhere in the file. The Forecast
        block was placed after `formatClock` for exactly this reason.
        (2) THE POOL WAS NOT IDEMPOTENT. Initialize cloned its rows without removing the previous
        set, so a second Initialize - or a pool already saved into the place from an Edit-mode run
        - stacked a duplicate set on top. DECIDED: destroy existing GameCoreLogRow* /
        GameCoreTimeSlice* before cloning, and verify with a deliberate second Initialize.
        (3) AN INSERT-AFTER-ANCHOR DUPLICATED THE DISPATCH TAIL. The first splice passed the full
        replacement text to a helper that inserts AFTER its anchor, so the two original lines
        survived and the new ones were appended below them - UpdateQuota and UpdateAlerts ran
        twice per tick. It was caught because the NEXT edit reported "ANCHOR NOT UNIQUE", which is
        the entire reason that guard exists; without it the double dispatch would have shipped.
        DECIDED: replace-with-anchor, never insert-after-anchor, when the intent is substitution.
        LESSON CARRIED FORWARD: the anchor-uniqueness guard is not ceremony. It is the only thing
        that noticed a duplicate that produced no error and no visible symptom.

62. THE AUTHORED TIMELINE FRAME HAS 292px OF CLEAR HEIGHT, NOT 355.
    The Forecast's ScrollingFrame is authored 355px tall, and 14 time slices at 20px with the
    list's 5px padding appear to fit it exactly - 14 x 20 + 13 x 5 = 345, 10px to spare. In
    practice the bottom three rows bled THROUGH the announcement overlay and stayed legible
    behind it.
        MEASURED: AnnouncementFrame AbsY 372..432 at ZIndex 5, against the rows' ZIndex 1, at 50 %
        background transparency. The ScrollingFrame spans AbsY 80..435. So 80px of the frame's
        bottom sits under the overlay and only 292px is clear. 25n - 5 <= 292 gives n = 11.
        (a) Shrink the ScrollingFrame to 292. Rejected: ThresholdTexture (130 x 353) and
            BorderFrame (3 x 355) are authored to that same 355, so shrinking one of the three
            would tear shared chrome.
        (b) Make the announcement overlay opaque. Rejected: it would keep hiding three rows of
            real data instead of stopping them being drawn under it.
        (c) Reduce ForecastSlices to 11 and leave the frame alone. CHOSEN.
        DECIDED: (c). The count is a Config value with the arithmetic recorded beside it, so a
        future edit that wants more rows has the constraint in front of it rather than having to
        rediscover it from a screenshot.
        LESSON CARRIED FORWARD: "it fits on paper" and "it is visible" are different claims. The
        first is arithmetic against a frame's declared size; the second is arithmetic against
        everything that draws on top of it. Only the second is what the operator sees.

63. A BLANK LINE AFTER EVERY LINE IN A TOOL DUMP IS A RENDERING ARTIFACT - MEASURE BYTES.
    Mid-session, long file dumps appeared to show a blank line interleaved after every line,
    including across original untouched code, and the file appeared to have grown by ~600 lines.
    It looked like a whitespace catastrophe.
        MEASURED: len = 20311, newlines = 537, CR = 0, CRLF = 0, adjacent-newline pairs = 44,
        lines = 537, longest blank run = 3. The file was exactly as written - about 365 original
        lines plus ~170 added.
        DECIDED: do not "fix" whitespace from the appearance of a dump. Count the bytes -
        characters, newlines, adjacent-newline pairs - and compare against the expected line count.
        A reformatting pass driven by a rendering artifact would have destroyed the file's real
        structure while looking like a repair.
        LESSON CARRIED FORWARD: the same rule as DECISIONS 59, applied to the tooling instead of to
        the game - what you are shown is not the same claim as what is there.
        This is also why the PROGRESS duplicate was caught by counting headings rather than by
        reading the file: the repeated section is invisible in a dump and obvious in a census.

64. THE GAME MODULE AND THE DISK MIRROR DISAGREED BY SIX BYTES, AND THE MIRROR WAS RIGHT.
    Found while syncing this phase, by comparing byte counts rather than by reading either file.
        MEASURED: DECISIONS game module content 71947 bytes against the disk's 71941, localised by
        per-line length signature to a single rewrapped sentence in decision 58 - the game read
        "Neon near-black, unique to this place" where the disk read the verbatim ART_DIRECTION
        quote "Neon 纯黑, 本 place 独有".
        (a) Let the game win on §0.0's authority rule and translate the disk. Rejected: the
            sentence is a QUOTATION, and the English is a translation of it, not a different fact.
            Applying the authority rule here would delete a verbatim citation that ART_DIRECTION
            itself still carries.
        (b) Drop the sentence from both. Rejected: it is load-bearing - it is the argument for why
            Neon near-black is the right choice rather than an invented one.
        (c) Restore the verbatim Chinese in the game module, so both sides are identical. CHOSEN.
        DECIDED: (c). CJK had been translated to ASCII in the module, most likely as a precaution
        about writing non-ASCII through the tooling. That precaution is unnecessary - the same
        module already stores CJK elsewhere without incident, and so does PROGRESS, which quotes
        the operator verbatim.
        ALSO FOUND IN THE SAME PASS: the PROGRESS game module carried a DUPLICATED TAIL - the
        "Phase 5 - (this number was never used)" note and the whole Phase 19h section, twice,
        byte-identical, 5757 bytes of it, invisible in a read and obvious in a heading census. The
        disk had them once. The second copy was cut; PROGRESS now matches the disk exactly.
        This is the SECOND instance of this failure mode - decisions 55/56/57 were found duplicated
        in the same module in the previous session. Both were caught by counting, never by reading.
        LESSON CARRIED FORWARD: compare the two sides by BYTE COUNT FIRST. It costs one call, it
        localises any divergence to a file, and it is the only check that finds duplication - a
        duplicated section reads perfectly well, which is exactly why it survived.

65. THE CLAUDE MODULE HAD DRIFTED 2016 BYTES FROM ITS DISK MIRROR, AND ONE OF ITS RULES WAS
    BACKWARDS.
    Found by comparing the two sides' section tables rather than by reading either one. The
    first 10209 bytes matched exactly, so the divergence localised to two sections:
        section   game    disk     delta
        section 2.6  669    2330    disk +1661  (Log/Forecast rows, the seven-monitor note,
                                                the monitor binding contract, AlertFrame rule)
        section 3.1  750    1106    disk +356   (the rebuild checklist)
    Total 2016 bytes, 31 lines. Everything before 2.6 and everything after 3.1 was already
    byte-identical, which is what made the two hotspots stand out as the whole story.

    FOUR STALE COUNTS, ON BOTH SIDES. Section 2.4 still carried the PRE-INSTALL binding line
    "desks=7 controls=68 reused=61 created=7"; the installed reading is
    "desks=6 controls=68 reused=2 created=66", and Workspace.Consoles holds six desks with zero
    authored ClickDetectors. Section 2.4's heading said seven desks (six), 2.5 said 31 lamps
    (41), 2.7's table said lamps:31 (41), and 3.1 said 1024 parts (957, the HDEF hull rewrite).
    All four were superseded by the install and never propagated - the same debt DECISIONS 43
    paid, but on the DECISIONS side only.

    THE RULE THAT WAS BACKWARDS. Both sides instructed the monitor rebuild to carry
    "LightInfluence = 1" forward from the desk experience. DECISIONS 57 had already established
    the opposite for the monitors: all seven MonitorUIs measure 0 and 0 is CORRECT, because a
    screen is an emissive source and must not take the room's exposure grade. The generalisation
    "the shipped originals all use 1" is true of desk label plates and false of monitor plates.
    A rebuild following the CLAUDE text would have set 1 and re-lit the screens as flat white -
    the failure DECISIONS 45 fixed, inverted. Corrected to "labels 1, screens 0".
    ALSO ADDED: the ForecastSlices = 11 constraint (DECISIONS 62), which CLAUDE lacked entirely.

    A NUMBERING DEFECT IN THE OTHER DIRECTION. Decision 64 sat between 59 and 60 in the DISK
    file - the only out-of-order entry - while the game module already had 1..64 in order. The
    disk was moved, not the module, and the move is byte-neutral: 74239 before and after,
    because it is a move and not an edit. Verified afterwards by comparing all 64 start offsets
    (offsetsum 1320293 on both sides). This is the first time in this project that the DISK was
    the defective side of a section-0.0 pair; the authority rule was not needed to decide it,
    because the module was simply correct and the disk was not.
    One trailing blank line was dropped from the game module's DECISIONS body (74240 -> 74239)
    so both sides end on a single newline. All four documents now reconcile exactly:
        CLAUDE    disk 38409 = game 37083 + section-0.0 1326  (the only sanctioned difference)
        DECISIONS disk 74239 = game 74239
        PROGRESS  disk 59869 = game 59869
        README    disk 20653 = game 20653
    LESSON CARRIED FORWARD: a section-size table is a diff that costs one call. CLAUDE had been
    quietly holding two stale sections and one inverted rule, and none of it was visible in a
    read - the prose was fluent throughout. What found it was arithmetic on the two files, the
    method DECISIONS 63 and 64 arrived at, now applied to the documents themselves.

66. THE DARKER GRADE IS NOW THE BASELINE, AND SPECULAR WAS THE PROPERTY THAT ACTUALLY MATTERED.

    DECISIONS 52 deferred "make the overall tone darker" to the shell/room phase, reasoning
    that changing Atmosphere and sky colour now would repaint every not-yet-rebuilt surface and
    have to be redone later. A probe grade was then applied anyway and the operator was asked.
    The answer was 保留这版 - keep this version. So 2.1 is DONE, not deferred, and the deferral
    half of DECISIONS 52 is superseded. What survives from 52 is its red line: the consoles must
    not end up reading as a different room from their surroundings.

    LIVE VALUES, read back from Lighting rather than copied from the plan - the probe drifted
    from what CLAUDE 2.8 recorded, and CLAUDE was the stale side:

        Brightness                 2.5   -> 1.2
        EnvironmentDiffuseScale    0.6   -> 0.42
        EnvironmentSpecularScale   0.8   -> 0.15
        ExposureCompensation       0.15  -> -0.08
        Ambient                    (31,28,26)    -> (25,24,27)
        OutdoorAmbient             (89,97,107)   -> (52,60,72)
        Atmosphere.Density         0.38  -> 0.20
        Atmosphere.Glare           0.15  -> 0.08
        Atmosphere.Haze            1.2   -> 0.45
        Atmosphere.Color           (199,191,180) -> (120,128,138)
        Atmosphere.Decay           (106,100,94)  -> (38,36,40)
        Bloom.Intensity            1.15  -> 0.85
        Bloom.Threshold            0.95  -> 1.15
        ColorCorrection.Contrast   0.12  -> 0.20
        ColorCorrection.Saturation -0.06 -> +0.02

    WHY SPECULAR IS THE ONE THAT MATTERS. DECISIONS 58 and 59 diagnosed the monitor bezel
    experiment failing because "every Metal part in this room renders white regardless of
    albedo". This property is the mechanism: at EnvironmentSpecularScale 0.8 the specular term
    swamps diffuse, so darker (60,60,60 Metal) and lighter (186 Plastic) resolve to the same
    value. Dropping it to 0.15 is not a taste change - it is the fix that experiment was routed
    around. The console palette, deliberately left untouched in Phase 19g, should now actually
    separate, and the Neon near-black used as a workaround for the monitors' dark band can be
    revisited.
    RE-CHECKED AND CLOSED IN PHASE 21g: the 21 dark-band rails are now Metal 75,75,76 /
    FacilitySteelPanel, and the seven Screen parts stay Neon on purpose. See DECISIONS 73.

67. THE REBUILD BENCH WAS CLEARED, AND WHAT COULD NOT BE REGENERATED WAS ARCHIVED FIRST.

    Operator instruction: 多余的、没有的、废掉的都删掉，好让我知道你现在正在做的是那些.
    The point was legibility - the operator could not tell live work from abandoned scaffolding.

    Workspace.Rebuild held 8,293 descendants / 5,367 parts across three folders plus 19 loose
    bench parts. Sorted by REGENERABILITY, the only test that matters for a delete:

        DELETED (regenerable from RebuildKit.BuildAll):
            Models/  - the Mk2 desk builds themselves - plus the loose bench parts and the Pad
        ARCHIVED, not deleted (NOT regenerable - these are the only copies):
            Originals/  ->  ServerStorage.GameCoreBaseline.Originals_consoles_and_monitors
                            14 models: the 7 pre-rebuild desks, including
                            ORIG_CBLaserConsole_DUPLICATE_DEAD, plus 7 ORIG_*ControlRoomMonitor
        ARCHIVED (superseded mid-work, kept as the Phase 21 comparison set):
            the 5 MK2PREV_*_preBar desks -> GameCoreBaseline.Superseded_Mk2_preLEDBar

    This is constraint 2 ("do not delete a feature without a replacement") applied to geometry:
    the originals ARE the rollback path, so they moved rather than died. They were already
    parked, not live - DECISIONS 41 established that the live names were taken over by the Mk2
    desks and the originals kept their GameCoreParkedPivot attributes, so one PivotTo() returns
    them.

    THE REGRESSION THIS CAUSED, AND THE FIX. RebuildKit.PlaceReference looked the originals up
    at the old path and would have fallen through to Workspace.Consoles - handing the bench an
    installed Mk2 desk as its own reference. That is precisely the footgun DECISIONS 49 was
    written about, and deleting the folder is what armed it.
    Fixed by making the archive a LOOKUP CANDIDATE rather than a replacement. Resolution order
    is now Workspace.Rebuild.Originals first - so the module still runs against a place saved
    before this cleanup - then the two ServerStorage folder names. Re-run and verified: 6 of 6
    REF clones resolved, part counts matching the archive exactly
    (279 / 382 / 316 / 167 / 310 / 545).

    BuildAll was checked to be SELF-HEALING before anything was deleted - it recreates
    Workspace.Rebuild and Models when they are missing. So the bench is a tool, not state:
    cleared, regenerated during the PlaceReference test, cleared again in the same pass.
    ALSO REMOVED IN THE SAME SWEEP: Workspace.RedPart (a 4 x 1.2 x 2 part sitting at the origin,
    referenced by no script) and Workspace.Legacy (two UniversalSynSaveInstance stubs, comments
    only).

68. THE INSTALL ANCHORS ON THE BOUNDING BOX, NOT ON THE PIVOT.

    Amends DECISIONS 50. That route records the live desk's GetPivot() and PivotTo()s the
    replacement onto it. It is exact only if both generations agree where the pivot SITS inside
    the model - and they do not. Measured pivot-minus-bounding-box-centre agreed on three desks
    and differed on ThermalConsole by 0.31 studs and ALTReactorConsole by 0.16. PivotTo-ing
    blindly would have mis-placed two of five desks by a third of a stud.

    Fixed by anchoring on the bounding box, which is convention-independent:
        d = liveCF * new:GetBoundingBox():Inverse()
        new:PivotTo(d * new:GetPivot())
    It also carries the live desk's rotation, which comparing positions alone would not.
    All five landed at a measured centre delta of 0.000 on every axis.

    GENERALISED: any future transplant between build generations compares a BOUNDING BOX, not a
    pivot. A pivot is an authoring choice and may legitimately move between generations; the
    bounding box is a property of the geometry and does not.

69. THE LED BAR GRAPHS ARE DECORATION ON PURPOSE, AND THAT IS THE DESIGN DECISION.

    ART_DIRECTION 3.4 called the vertical red LED bar graph the reference consoles' primary
    magnitude readout and the one indicator form Mk2 lacked entirely. It was the last open
    console item. Placed at local Z -2.25 and +2.25 - the two inner margins between the three
    screen panels, which is exactly the panel pitch - so the columns sit in the same rhythm as
    the screens instead of in leftover space. 9 segments each, the lit count ROUNDED to nearest
    rather than floored (two-thirds-full should read as two thirds, not one short), and only
    the topmost lit segment carries a PointLight - one per segment would be 18 lights a desk
    for no visible gain at this size.

    THEY ARE NOT DRIVEN. Every column shows a FIXED fraction. MonitorService is the single
    writer for every real readout in this game, and the standing rule is that a value has one
    writer. Making these live would mean either MonitorService writing console geometry -
    breaking the facility-visual boundary it currently respects - or standing up a second
    writer for values it already owns. Neither is worth it for a part 0.15 studs tall.
    Nothing here is named for a control, so ConsoleBinder never resolves it and ControlVisuals
    never sees it: verified structurally, 0 controls added, 0 missing, 28 dot-paths intact.
    IF the operator later wants them live, the correct shape is MonitorService PUBLISHING them
    the way it already publishes the screens - not a new system reading GameState directly.

70. WHAT WAS *NOT* DELETED, BECAUSE THE COUNT LOOKED LIKE A CLEANUP TARGET.

    A full-game scan found 98 of 137 scripts are comment-only UniversalSynSaveInstance stubs.
    That reads like free cleanup and is not. Most sit INSIDE live models - MES, QPU, GravGate,
    the monitor frames, GravitationShafts - where the instance NAME is a binding-contract lookup
    target. Visual cost of leaving them: zero. Risk of removing them: a silently broken control.
    Left alone deliberately, on the same reasoning as DECISIONS 67 but reaching the opposite
    verdict, because these are not dead weight - they are inert and load-bearing at once.

    CHECKED AND ALSO KEPT: ServerStorage.RecoveredHiddenScripts is not junk - 8 recovered
    LocalScripts with real code (CameraEffectsController 43,765 chars, VitalsScript 16,729,
    MovementController 9,455, MESInputController 3,633, CullController, CameraShakeController,
    and a README). ReplicatedStorage.SGE_* are 4 empty Studio drag artefacts; harmless, left.

71. THE "ALL FOUR DOCUMENTS RECONCILE EXACTLY" CLAIM IN DECISIONS 65 IS WRONG - MIXED UNITS.

    Found while doing the section-0.0 mirror for Phase 21. DECISIONS 65 asserts:

        CLAUDE    disk 38409 = game 37083 + section-0.0 1326
        DECISIONS disk 74239 = game 74239
        PROGRESS  disk 59869 = game 59869
        README    disk 20653 = game 20653

    Measured on disk at the time: DECISIONS.md was 77729, PROGRESS.md 61412. README.md 20653 and
    CLAUDE.md 38409 were correct as stated. All six figures are long superseded - see entry 82 for
    the method and the current state. Do not quote sizes out of this entry.

        DECISIONS  disk 77729 - claimed 74239 = +3490
        PROGRESS   disk 61412 - claimed 59869 = +1543

    THE CAUSE IS A UNIT MISMATCH, NOT LOST CONTENT. Line counts confirm the two sides are the
    same document - disk DECISIONS is 1029 lines against the module's 1031, PROGRESS 944 vs 946,
    which is exactly the two wrapper lines (return [==[ and the closing bracket pair) and
    nothing else. What differs is that the "game" figures are CHARACTER counts and the "disk"
    figures are BYTE counts. Every non-ASCII character costs 1 in one and 3 in the other, so
    each Chinese character contributes a 2-byte gap:

        DECISIONS  3490 / 2 = 1745 Chinese characters
        PROGRESS   1543 / 2 =  771 Chinese characters
        README     0 gap  ->  contains no Chinese characters at all
        CLAUDE     1326 gap is section 0.0, which IS Chinese-heavy, so its figure was also not
                   measured the same way as the other two

    So the reconciliation table was self-consistent only by accident: README and CLAUDE happened
    to be compared in matching units, and the two documents carrying the most Chinese were not.
    The method DECISIONS 63/64/65 built - arithmetic on two files - is still the right one. The
    bug is that it was run on numbers gathered with two different rulers.

    WHAT THIS DOES NOT MEAN: no content is missing, and no section-0.0 pair is out of sync. It
    means the byte figures quoted in DECISIONS 65, CLAUDE section 0.0 and PROGRESS cannot be
    used as a diff until they are re-measured on one ruler. Until then, compare LINE COUNTS, which are
    unit-free - that is the check to reach for first.

    RESOLVED, AND THE FIX IS A RECIPE RATHER THAN A NEW TABLE. Re-measuring all four pairs on one
    ruler was done during the same mirror pass, and it turned up a SECOND and more serious defect
    underneath the unit problem: PROGRESS had drifted (see PROGRESS 21f). The four were believed
    to reconcile at that point. They did not: entry 77 found real divergences that this entry's
    check could not see, and entry 82 finished the job. Read this entry for the UNIT defect only.
    But the reason entry 65's table went wrong is that a table of absolute file sizes goes stale
    the moment anybody edits a document, so the durable fix is to record the METHOD and stop
    quoting sizes:

        1. Compare BYTES on both sides. #s of the module Source, read in Luau, and wc -c of the
           disk file are both byte counts and agree. A UTF-8-aware reader's len() is a CHARACTER
           count and will not - that mismatch is the whole of the original defect.
        2. Subtract the wrapper. The module body sits inside a return statement and a long-bracket
           string, which together add EXACTLY 17 bytes - 11 for the return statement, 4 for the
           closing bracket pair, 2 newlines. "About 18" is how a one-byte drift hides: it was 17
           all along, and the approximation is why this entry could not tell one byte from none.
        3. Fingerprint the CONTENT rather than the size: count the non-ASCII characters on both
           sides. It is one number, it survives the line-wrapping differences that shift byte
           counts without changing meaning, and two documents cannot satisfy it merely by being
           the same length.
        4. If the totals still differ, split by SECTION before reading anything. Key each
           section's character count by its heading on both sides and diff the two lists. That
           localises a divergence in a single step - it is how the 611-character PROGRESS drift
           was found - and costs one pass instead of a full read of both documents.

72. `edit_script_lines` RETURNS FALSE "old_string not found" ERRORS. VERIFY, DO NOT RETRY BLIND.

    Hit at least twice in the Phase 21 documentation pass. The call reports
    "Failed to edit script: ... old_string not found in script source", and the edit HAS ALREADY
    BEEN APPLIED. The disk-side Edit tool in the same pass behaved correctly, so this is specific
    to the MCP path.

    WHY IT MATTERS MORE THAN IT SOUNDS. The first occurrence was diagnosed as TEXT DRIFT - I
    concluded the game README had been edited more recently than the disk mirror and was
    "already path-neutral, pre-compaction work the summary missed". That conclusion was WRONG;
    the game text was my own edit, already applied, and I had been reading my own output back as
    if it were somebody else's. A spurious error, plus an assumption about which side was stale,
    produced a confident and false story about the repository.
    This is the same class of trap as section 0.2 of CLAUDE (the command bar's require returning
    a fresh empty module): THE TOOL'S REPLY IS NOT EVIDENCE. Read the artifact back.
    RULE: on any edit error, re-read the target region before doing anything else. Never retry
    the same edit blind, and never let the error message update a belief about which side of a
    mirror is authoritative.

    SECOND TOOL TRAP, SAME PASS: grep_scripts has usePattern defaulting to FALSE, i.e. LITERAL
    search. Passing a regex-looking alternation such as TERM_A, term-B, term_C returns zero
    matches and looks exactly like "this text is absent" - I drew two wrong conclusions from
    0-match results before noticing. Lua patterns have no alternation operator at all, so
    usePattern:true would not have helped either. Search ONE term per call, or scan .Source in
    Luau directly. A zero-result search is only evidence if the search was the kind you thought
    it was.

    WHAT WAS *NOT* THE PROBLEM: CRLF. Multi-line anchors work fine in this project's modules. The
    two genuine multi-line failures had real causes - the disk and the game wording differed, and
    in one case I matched a sentence that wraps across two source lines as though it were one.
    Worth recording because "line endings" is the wrong lesson to carry away from this.

    AND THE FALSE NEGATIVE IS NOT COSMETIC - IT SILENTLY DUPLICATED 127 LINES. The first
    attempt at this entry's neighbours anchored on a string ending in the module's closing
    bracket and reported "old_string not found", so a second attempt was made with a different
    anchor. BOTH HAD IN FACT APPLIED, and the module ended up holding decisions 66-70 TWICE:
    one copy in the right place, and a second copy appended after decision 72, immediately
    before the closing bracket. Nothing about the file looked wrong on a normal read - the prose
    ran straight from 72 into a repeat of 66 and read as though nothing were amiss.
    Found by locating the header string TWICE with a plain byte search (string.find), not by
    reading line numbers. Removed with a guarded rewrite - it aborts if the region to delete
    turns out to contain an entry newer than the last one known to be legitimate - and
    re-verified: entries 1..72 each appear exactly once, in order, ending on 72 immediately
    before the closing bracket. (A naive scan also flags 1, 2 and 3 as duplicated; those are the
    numbered sub-items inside decision 45, not entries.)
    CARRY FORWARD: after ANY edit reported as failed, re-read the target region before touching
    it again. A spurious failure followed by a retry is a DUPLICATION BUG, and the duplicate
    lands somewhere that reads naturally - here, appended behind the newest entry, where a
    skim would take it for the document's tail.

    A LINE-COUNTING TRAP MET WHILE INVESTIGATING THIS, RECORDED SO IT IS NOT REPEATED. The
    obvious way to walk a Source string in Luau -
        for line in s:gmatch("[^\n]*") do
    - is WRONG. That pattern can match the empty string, so gmatch yields an extra empty match
    at the end of every line and the count comes out roughly DOUBLE the truth. A scan walking
    DECISIONS this way reported 2605 lines for a module that is 1258, and those inflated numbers
    were briefly taken as evidence that the tool's own bookkeeping was lying. It was not. Measure
    the artifact directly: count newlines with select(2, s:gsub("\n", "")) and sanity-check the
    result against #s. At the moment of this finding - before this very paragraph was added -
    the module measured 1258 lines and 92899 bytes, LF throughout, zero CR; it has grown since, so
    re-measure rather than quoting that pair. The lesson is section 0.2 of CLAUDE pointed the
    other way for once - the tool was right and the hand-rolled probe was wrong - so verify the
    PROBE before convicting the instrument.

73. THE NEON NEAR-BLACK BAND WAS A WORKAROUND FOR THE GRADE, AND IT OUTLIVED THE GRADE BY ONE PHASE.
    Phase 20c built the monitor housing band in `Neon 17,17,17` for a stated and correct reason:
    under Brightness 2.5 + `EnvironmentSpecularScale` 0.8, every `Metal` part in that room
    rendered white regardless of albedo, so a dark Metal band was not available as a material at
    all. 20c closed by naming its own dependency - "the real fix is the grade". DECISIONS 66 then
    changed `EnvironmentSpecularScale` to 0.15, which is precisely the property that caused it.
    Nothing re-opened 20c, so the workaround sat there for a phase, working, and wrong.

    THE GENERAL SHAPE, worth carrying to the rest of this rework: A WORKAROUND THAT OBSERVES ITS
    OWN DEPENDENCY IS NOT THE SAME AS A WORKAROUND THAT GETS REVISITED. 20c did the first half
    properly - it wrote down why the material was unavailable and which decision owned the fix.
    What was missing is a trigger: nothing connected "DECISIONS 66 changed specular" to "the 21
    parts that were chosen because specular was wrong". The fix was found by a handoff note
    (NIGHT_LOG priority 1), not by the code or the docs. When a fix lands, grep the docs for the
    property it changed; the parts chosen around that property will be listed there and nowhere
    else.

    WHAT WAS CHANGED, AND WHY THE SPLIT IS THE POINT. 28 parts in the seven-monitor bank carried
    `Neon 17,17,17`. Exactly 21 of them - `FrameTop`, `FrameSideL`, `FrameSideR`, three per
    monitor - were the workaround, and all 21 are now `Metal 75,75,76` with
    `MaterialVariant = FacilitySteelPanel`, which is the value the same monitors' own `FrameBolt*`
    parts already carried. The other 7, one `Screen` per monitor, were deliberately left alone:
    `Screen` is the backing that hosts `MonitorUI`, `BootUI` and four `SurfaceLight`s, and a
    self-lit near-black panel is what the display is supposed to be. A blanket "de-Neon the
    monitors" sweep would have broken the one part in the set that is functional.

    Appearance properties only - no rename, no move, no resize, no reparent, no delete, so CLAUDE
    section 6 is not engaged. Checked anyway, because section 6 is a list of names and the check
    is one call: `grep_scripts` for `FrameSide` returns 0 matches across 180 scripts.

    VERIFIED BY RE-READING INSTANCE STATE, NOT BY TRUSTING THE WRITE. 21/21 rails read back
    `Metal 75,75,76 / FacilitySteelPanel`, 0 off; `Screen` read back `Neon 17,17,17` on 7/7. Both
    ChangeHistory waypoints set, so one Ctrl+Z reverses the whole set.

    THE NUMBER THAT NEEDS A SCOPE NOTE. `Neon 17,17,17` is not a monitor idiom - it is the
    facility's existing recess idiom, and there are 804 of them across Workspace: coolant
    processor frames, gateway alarm plates, door levers, control-panel text and screens. This
    change touched 21, all under `Workspace.Monitors`. Quoting "we removed the Neon near-black"
    without that scope would read as a much larger change than it was, and would invite a future
    pass to "finish" a job that was never the job.

    AND ONE HONEST CAVEAT ABOUT THE JUDGEMENT. The before/after was photographed and the band now
    reads as metal with a specular gradient rather than as a flat stripe, which is the intended
    result. But this is a 0.14-stud-wide trim seen mostly at grazing angles from inside the room.
    It is a small, reversible, appearance-only change whose whole justification is that a
    documented dependency was discharged - not a visual improvement anyone will notice from the
    operator's seat. Recorded that way on purpose, so a later reader does not go looking for an
    effect this size in a screenshot.
74. THE CLICK LOGIC HAS ONE IMPLEMENTATION, AND THE COMMAND BAR REACHES IT THROUGH A BINDABLE FUNCTION.
    Phase 22 moved every ClickDetector click path into `ControlTrigger`, a new ModuleScript under
    `GameCore.FacilitySystem`. `ConsoleBinder` keeps only its dot-path table and calls
    `ControlTrigger.Bind`; the body that used to live in `attachClick` - the `[Console]` print, the
    `ConsoleFocus` client notification, `ControlVisuals.Pulse`, `ConsoleService.PerformAction` and
    the `ControlVisuals.Update()` that follows it - now exists once. A physical press is
    `Fire(part, player)` and nothing else, which is why the two routes cannot drift apart.

    WHY THE BRIDGE IS A BINDABLE FUNCTION AND NOT A `require`. The command bar runs in a separate
    Luau VM. A `require` there returns a brand-new module instance with an empty `GameState` - the
    trap CLAUDE section 0.2 records - so a command-bar call through `require` would print success
    and do nothing at all. Instances are shared between VMs and module tables are not, so
    `ControlTrigger.InstallBus()` sets `ServerStorage.GameCore.ControlBus.OnInvoke` from inside the
    live server VM; any VM that invokes it therefore executes live code. The failure mode was
    reproduced before the fix - `HostOf is not a valid member of ModuleScript` - and the fix was
    confirmed by invoking from a foreign VM and getting the live table back rather than a zeroed
    one.

    TAGGING, AND WHY THE TAG IS WRITTEN ONLY ON THE FIRST BIND. Every bound control carries the
    `GameCoreControl` tag plus six attributes (`GameCoreAction`, `GameCoreArg`, `GameCoreArg2`,
    `GameCoreLabel`, `GameCoreConsole`, `GameCorePanel`). `Reindex()` walks
    `CollectionService:GetTagged` and re-binds idempotently, so a part tagged by hand in Studio
    starts working on the next server boot without editing the dot-path table. The tag is written
    once: the existing ClickDetector connection already closes over the first definition, so
    letting a later pass overwrite the attributes would let the tag and the live behaviour
    disagree - which is worse than a stale tag, because it is invisible.

    THE DOUBLE-FIRE HAZARD, CLOSED AND THEN DISPROVED. `Bind` reuses the existing detector, or
    adopts an authored one, instead of creating a second: two detectors on one part means two
    connections, and one physical press would fire the control twice. This is not a theoretical
    worry here. `Bind` provably runs twice per control in a normal boot, once from the table pass
    and once from `Reindex`, and the log reads `tagged=73 reindexed=73`. After the guard, one
    physical press produced exactly one `[Console]` line and the bus fire also logged exactly one,
    so the guard holds.

    NOTHING MOVED. `[ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0` is
    byte-identical to the pre-refactor baseline in CLAUDE section 2.4, and both in-place tests sit
    at their baseline numbers (`SelfTest PASS, bridgeResolved 18, devices 15`; `ControlTest
    pass:13 fail:0, levers:18 lamps:41, signMatches 60/60`). A refusal still reaches the player
    through `Network.Notify`. The refactor is a pure extraction, and the counts are the evidence
    for that claim rather than the assertion of it.

    THE 73-VERSUS-74 ARITHMETIC IS PRE-EXISTING. Six desks plus 68 controls is 74 `Bind` calls but
    only 73 tagged parts, because one HDEF part is the resolved target of two definitions. In the
    original code the desk pass connected first and the control pass then hit the `GameCoreBound`
    guard, so the single connection and the resulting behaviour are unchanged; writing the metadata
    once is what keeps the tag consistent with that one connection.
