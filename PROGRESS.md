# PROGRESS

## Phase 1 - Workspace analysis  [DONE]
Mapped Workspace facility models and folders (Core, Mainframe, GravatronUnit, METU,
MES, CRC1-3, PowerExtractionAssembly, Consoles, Alarms, Monitors, CoolantReserviors...).

## Phase 2 - Backend rewrite (GameCore)  [DONE]
Core / ReactorSystem / MaintenanceSystem / FacilitySystem / AlarmSystem /
EventSystem / PlayerSystem written and registered by priority.

## Phase 3 - Physics tuning + verification  [DONE]
Live self-test PASSED in Play mode.

## Phase 4 - Interaction layer  [DONE]
Runtime RemoteEvents + ConsoleService + ConsoleBinder (26 ProximityPrompts).

## Phase 6 - Real control-point binding  [DONE]
Bound the real consoles incl. CBLaserConsole, ThermalConsole, HDEFGenerator.

## Phase 7 - Control-point wiring  [DONE]
Prompts call ConsoleService.PerformAction directly (server module).

## Phase 8 - HDEF/CBL/Gravatron/METU Deeper Gameplay  [DONE]
CBLSystem, GravatronSystem, METUSystem created and wired.

## Phase 9 - Wiki Calibration  [DONE]
CoreState thresholds, AVB, E-VENT, CBL levels, quotas, PEA stress, METU, Gravatron.

## Phase 10 - TRGWeb calibration  [DONE]
Read ServerScriptService.Misc.TRGWeb and calibrated Config.

## Phase 11 - Stabilization + TRGWeb/Wiki fidelity pass  [DONE]
BUGS FIXED
  - ConsoleService.Initialize referenced undefined r/cfg -> every new remote handler
    threw nil-index. Scoped correctly.
  - Reactor startup deadlock (stallout penalty > MINIMUM laser heat). Added ignition
    seeding (TRGWeb 9420 F / 5000 PSI) in ReactorState.SetOnline + stallout gate at 2000 F.
  - EventController.RodJam referenced the removed RodInsertion field -> replaced with
    a rodless FanSeize event.
  - PowerOutput was written twice. PowerSystem is now the single owner (TRGWeb tiers).
  - Coolant heat removal was applied twice. ReactorState owns temperature;
    CoolantSystem exposes GetTotalHeatRemoval().
  - Random temperature integrated per frame -> now re-rolled once per TRGWeb tick.
  - CBL overload used to permanently degrade lasers to MINIMUM and inject +2000 F.
    Wiki-correct behaviour: total power loss + auto-restart; integrity loss on Shift 3+.
  - METU clamped temperature through a C/F conversion -> now clamps to 20000 F.
  - METU pressure clamp dropped below the stallout floor -> now floored above it.
  - DataCollection nil ctrlConsole reference fixed.
CALIBRATION
  - Config.Sim.TRGWebTick = 2.5; TRGWeb constants convert via dt/2.5.
  - Pressure on the PSI scale: MaxPressure 16000, ignition 5000.
  - CBL heat = power_level * 65 per tick (MINIMUM still fires).
  - PowerSystem TRGWeb tiers (t/250+50 ... t/45+400) + Equinox 3x + 0 when offline.
  - NEW PEASystem (extraction 1-4, TRGWeb stress formula, overstress wear).
  - ShiftSystem quota tracking (512/1024/3072 GW peak output).
  - EventController Equinox event (Shift 3, 3x energy, 40 s, pump explosions).
  - CoolantSystem: three reservoirs, discrete pump levels 0-3, loop charge scales cooling.
  - BackupPowerSystem exports HDEFIntegrity; snapshot exposes PEA/Reservoir/Shift/Equinox.
  - DeviceFactory: ControlRodActuator -> CBLActuator.
  - GameCore default start = TRGWeb balanced state (CBL 2, pumps 1).

## Phase 12 - Verification  [DONE]
Fresh Play-mode run (20 systems, 12 devices):
  ignition 9420 F / 5000 PSI
  t20s  temp 8756 F, state 1, 154 GW (Wiki S1 124-200)
  t200s temp 10744 F, state 1, 167 GW, sustained (no collapse)
  t300s temp 24114 F, state 2, 450 GW (Wiki S2 400+)
  reservoirs [77.9, 77.9, 77.9], HDEF 100%, quota 512, Equinox inactive
  finalStatus PASS, ok true, zero SystemManager update failures
  ReactorMonitorClient binds the MESUI layout successfully.

## Phase 13 - Documentation  [DONE]
README module added. PROGRESS/DECISIONS/README are valid Luau module sources.

## Phase 14 - Click controls + live control-room monitors  [DONE]
CONTROL SURFACES (ClickDetector, replaces ProximityPrompt)
  - ConsoleBinder now attaches/reuses ClickDetectors and prints every press:
        [Console] <player> pressed: <control label>  (<console model>)
  - 7 desks, 65 controls bound, 0 unbound, 61 existing detectors reused, 4 created.
  - MainReactorConsole   : AVB, E-VENT 1-3, Start-Up, Shutdown, Monitor Boot
  - ThermalConsole       : pump ON/OFF, pump levels PW1-3, fans 1-6, pressurizer, PEA vent
  - CBLaserConsole       : purge + direct PW1-5 power level per laser
  - ElectricGridConsole  : PEA extraction PW1-4, Gravatron charge, Gravatron overload
  - ALTReactorConsole    : M.A.S.S. 1/2 activation + power lever (status only)
  - HDEFGenerator        : power lever, emergency control, cells 1-3
  - METU                 : ECC receptacle 1/2 (hand refill, Wiki)
MONITORS (Workspace.Monitors, refreshed every tick = immediate)
  - MainControlRoomMonitor.ReadingsFrame: Temp, Pressure, Radiation, Output, HDEF,
    Stress, Fluctuation, Extraction
  - ThermalControlRoomMonitor: FanFrame1-6 ON/OFF + C1-3 pump level labels (added)
  - PowerControlRoomMonitor: CBL1-3 Power %, Stress %, State, and the locked 925 F body temp
  - New module FacilitySystem.MonitorService (priority 125).
CBL BODY TEMPERATURE
  - Config.CBL.BodyTemperatureF = 925, locked in CBLSystem; CBLSystem.GetBodyTemperature().
  - Config.Monitor = { UpdateInterval = 0 } (0 = every tick).
ROBUSTNESS
  - Systems self-heal: CBL / Gravatron / METU / PEA re-initialise their GameState
    subtables if a GameState.Reset cleared them. Zero SystemManager failures after the
    self-test resets the world.
VERIFICATION (fresh Play session)
  - [GameCoreSelfTest] PASS: t20s State 1 153 GW; t200s State 1 150 GW;
    t300s State 3 36352 F, 1207 GW, quota met, integrity 100%.
  - Monitors observed live: Main Temp 8386 F / Pressure 7215 PSI / Output 152 GW /
    Fluctuation +36 F / Extraction 50%; Thermal fans OFF, pumps LEVEL 1;
    Power CBL Temp 925 F, Power 50%, Stress 23%, State FIRING.
  - 21 systems, 12 devices, no runtime errors.


## Phase 15 - Workspace organisation + remaining monitors  [DONE]
WORKSPACE SORTED (1828 -> 137 top-level children)
  - Workspace.Geometry/  Meshes(72) Unions(13) Wedges(4) Parts(1429) Floors(34)
                         Props(23) Models(109)
  - Workspace.Legacy/    archived the empty MainGameControllerScript + MiscScript
  - Workspace.Tools/     the three QPU tools
  - Workspace.TeamSpawns/ the five spawn locations
  - ServerScriptService.Misc/_ZSCapProbe (empty leftover folder archived)
  - Functional models/folders (Core, METU, Consoles, Monitors, Stats, ...) stay at top
    level so FacilityBridge / ConsoleBinder / MonitorService paths still resolve.
  - Verified safe first: 1072/1081 geometry parts anchored, zero welds, no references.
FINAL WORKSPACE LAYOUT (1828 -> 40 top-level children)
  Workspace/
    Core, METU, MES, CRC1-3, GravatronUnit, QuantumMainframe,
    PowerExtractionAssembly, MedicalDispenser        <- functional roots (paths kept)
    Consoles, Monitors, MonitorsFacility, Stats, Alarms, Lights, RoomLights,
    Sounds, MovingParts, CoolantReserviors, ReactorCBLs, SoundBlocks, UISounds,
    GravitationShafts, ChamberWalls, CullFolder, DebrisEffects,
    MainframeToolStorageCull, PhysicsObjects, ClickInfo, Mainframe   <- system folders
    Geometry/   Meshes(72) Unions(13) Wedges(4) Parts(1429) Floors(34) Props(23) Models(109)
    Facility/   Shafts(10) Doors(9) Rooms(32) Props(4) Lights(8) Rigs(6) Cameras(2) Emblems(8)
    Sounds/Misc (19 loose sounds - a Sound in a Folder is 2D exactly like one in Workspace)
    GameCoreTests/ GameCoreSelfTest, GameCoreControlTest
    Legacy/  (archived empty legacy scripts)
    Tools/   (QPU tools)      TeamSpawns/ (5 spawn locations)
  - Only decorative / unreferenced objects were moved, so every system path still
    resolves: verified by the self-test reporting bridgeResolved = 18 and by the
    control test still passing 13/13 after the reorganisation.

MONITORS (all five control-room screens now live, refreshed every tick)
  - QuotaControlRoomMonitor : in-game clock (6:00 AM -> 6:00 PM per shift), quota
                              target + live progress %, Equinox frame.
  - AlertsControlRoomMonitor: 27 named alert lamps from real conditions.
  - Config.Reactor.EquinoxTriggerTime moved to shift-second 600 so the clock reads
    12:00 PM exactly when the Equinox begins.
VERIFICATION (fresh Play session)
  - Quota monitor: "6:16 AM" / "512 GW [31%]" / Equinox hidden.
  - Alerts monitor: exactly 7 lamps lit (RECT, SUBSPACE, CBL, CORE, PUMP, HDEF, G-GATE).
  - [GameCoreSelfTest] PASS: t300s State 3, 31808 F, 1106 GW, quota met.
  - 21 systems, 65 click controls bound, no runtime errors.

## Phase 16 - Control feedback, monitor states, automated click test  [DONE]
BUGS THE OPERATOR REPORTED, AND THE FIXES
  1. Temperature fluctuation showed "+" while the core was cooling.
     -> ReactorState now measures the real Temperature delta over the tick instead
        of predicting it, so the sign always matches the actual direction.
        Test: fluctuation signMatches 60 / 60.
  2. Levers did not move when pulled.
     -> New FacilitySystem.ControlVisuals rotates each lever to a detent derived
        from live state (CBL 5 notches, P.E.A 4, coolant pump 4, fans/E-VENT/start-up 2).
        A lever first bound as ON/OFF adopts the richer detent count when re-bound.
  3. Buttons had no visible feedback.
     -> ControlVisuals.Pulse() fires a 0.6 s green flash on every press, then the
        steady state is restored: white = ready, red = unavailable/fault, dark = spent.
        (The AVB lamp correctly reads red while pressure is above 5500 PSI.)
  4. The CBL monitor kept showing "on" and 925 even when the laser was destroyed.
     -> State now reads OFFLINE / POWERING / FIRING / ACTIVE / OVERLOAD / DESTROYED,
        the temperature shows ERR when destroyed, and the Wiki colour code is applied
        (Overload red, Integrity loss purple, Reaction loss blue, High output yellow).
  5. The coolant pump screen never showed ON/OFF or failure.
     -> Each C-frame now reads "ON  L<n>", "OFF" or FAULT (red) and the pump image
        is tinted red when the pump device has failed.
AUTOMATED CLICK TEST
  - Workspace.GameCoreControlTest drives ConsoleService.PerformAction with a mock
    supervisor, then compares lever pivots and lamp colours before/after.
  - Result: pass 13, fail 0; levers 18, lamps 31; fluctuation 60/60.
  - It re-arms a known reactor state first so the self-test's reset cannot skew it.
## Phase 17 - QPU replacement, subspace gateways, gravity lifts  [DONE]
THREE NEW SYSTEMS (22 -> 25 systems, no runtime errors)
1. QPUSystem (priority 47) - the QPU replacement programme
   - Six processors at Workspace.QuantumMainframe.QPU1..QPU6MaintenanceInterior.
   - Each QPU wears constantly (overclocking) plus extra wear per core state
     (Config.QPU.DegradePerSecond 0.04 + OverclockPerCoreState 0.02), matching the
     Wiki: overclocking degrades QPUs and forces frequent replacement.
   - The slot's QPULight turns green (>50), amber (<50) or red (failed).
   - A failed QPU drops Workspace.Stats.ActiveQPUs; all six dead raises MAINFRAME
     MELTDOWN and sets Stats.MainframeMeltdown.
   - Replacement: click the slot carrying a QPU tool (spares sit on the rigs); the
     tool is consumed and the QPU returns to 100.
2. GatewaySystem (priority 48) - the subspace teleport rings (传送环)
   - Finds every Facility.Rooms.*GatewayRoom and caches its GatewayRing1-5, doors,
     neon parts, effect part and TeleportBoundingBox.
   - While the reactor is online the rings spin (alternating direction), the neon
     goes live-blue, the blast doors turn transparent/non-colliding and the effect
     becomes visible; everything reverts when the core is down.
   - Touching a pad transits the operator to the next gateway with a cooldown.
3. GravLiftSystem (priority 49) - the gravity lifts (重力电梯)
   - Finds every Facility.Shafts.* shaft, direction from the name (Descending = down).
   - While the Gravatron is healthy and the reactor online, an operator inside a shaft
     is carried along it at Config.GravLift.Speed; if the Gravatron fails the shafts
     lose power and stop holding them.
CONFIG: Config.QPU / Config.Gateway / Config.GravLift.
VERIFICATION (fresh Play session): 25 systems, self-test PASS (bridgeResolved 18),
control test PASS 13/13, fluctuation 60/60, zero SystemManager failures.

## Phase 18 - Coolant sensor recalibration (修冷却)  [DONE]
Wiki: "coolant sensory equipment has a tendency to be unreliable during reactor
operation" and "requires manual intervention for recalibration".

  - Each of the three pumps now carries a sensor stability value (0..100) in
    GameState.Reactor.CoolantPumpStability. It drifts constantly
    (Config.Coolant.SensorDegradePerSecond 0.30) plus extra drift per core state
    (SensorStateBonus 0.22) and 1.5x while the pump is running.
  - Below SensorUnreliableBelow (60) the thermal monitor appends "SENSOR n%" in
    amber to that pump's readout; below SensorFailureBelow (25) the pump's real
    output is scaled down to as little as SensorOutputPenalty (0.45), so a drifted
    sensor genuinely weakens the coolant loop.
  - Recalibration: click the pump's BigLever on the thermal console
    ("Coolant Pump N Sensor Recalibration") -> CoolantSystem.Recalibrate(index)
    restores stability to 100 with a 30 s cooldown (Config.Coolant.RecalibrationCooldown).
  - ConsoleBinder now binds 68 controls (was 65) with 0 unbound.
VERIFICATION (live): forced stability 10 -> output factor 0.67, IsReliable false;
Recalibrate -> true, stability back to 100; immediate retry -> false (cooldown).
Self-test PASS, control test PASS 13/13, 25 systems, no runtime errors.

## Phase 19 - Console rebuild (Mk2 desks)  重新建模  [IN PROGRESS]
Operator task: rebuild the game's geometry on a bench beside the originals,
reusing the shipped art / audio / VFX, with every function intact and the docs
kept in sync.

CONTRACT FIRST
  Before modelling, the binding contract was reverse-engineered and then checked
  against the originals themselves:
    - ConsoleBinder resolves dot paths ("E_VENTLever1.ClickPart"); a target is a
      BasePart, else the node's ClickPart child, else its first BasePart.
    - ControlVisuals walks UP from a click part to the nearest Model that owns a
      LeverUnion and rotates that single part about the BOTTOM CENTRE of its
      bounding box. findLampParts does the same for NeonPart/Indicator/Lamp/Glow
      and returns all of them.
  Because the contract is path-based and root-agnostic, the rebuilt desks need no
  engine change: the same CONTROL_DEFS drive them with only the root swapped.

DESIGN LANGUAGE (measured, not guessed)
  The first pass used hand-picked "sci-fi grey" and blew out to pure white under
  the place's lighting (Brightness 2.5 + Bloom + Exposure +0.15). The palette was
  then measured off the real consoles: large light panels are Plastic, not Metal;
  Metal is reserved for body / frame / seams; pure-black Neon (0.067) is how the
  original draws its dark seams. Recorded in RebuildKit.PALETTE.

BENCH (Workspace.Rebuild)
  Pad 96x2x96 (DiamondPlate + FacilityFloorPlate) on verified-clear ground at
  Y 298, with rails, corner posts, hazard stripes and four masted floodlights.
  Models/ holds a two-row grid: row 2 = an untouched clone of each original
  (REF_*), row 1 = the rebuilt desk (MK2_*), so they compare side by side.

SIX DESKS REBUILT (GameCore.Rebuild.RebuildKit)
  BuildMainReactorConsole    7 controls, 182 parts
  BuildThermalConsole       26 controls, 245 parts
  BuildCBLaserConsole       18 controls, 188 parts
  BuildElectricGridConsole   6 controls, 146 parts
  BuildALTReactorConsole     4 controls, 135 parts
  BuildHDEFGenerator         5 controls, 128 parts
  Total 66 controls. (The count first read 1024 parts; re-measured on the installed
  desks it is 957, because the HDEF cabinet rewrite replaced the shared hull - see
  DECISIONS 43.) All six share one hull builder, so the desks read as a family. Labels are the original strings read back off the real
  consoles ("CHAMBER VENTILATION FUNCTIONS", "OUTTAKE FAN n", "COOLANT PUMP n",
  "PRESSURIZER VENT", "PEA VENTILATION", "EMERGENCY-VENT n", "START-UP /
  SHUTDOWN", "BOOT"), not invented text.

REBUILD BINDING (ConsoleBinder.BindRebuild)
  A strictly additive second pass. It looks for MK2_<name> under
  Workspace.Rebuild.Models and replays the same CONTROL_DEFS through the same
  resolveTarget/attachClick, so the rebuilt desks get ClickDetectors, panel
  focus, ConsoleService actions and ControlVisuals feedback for free. It keeps
  its own counters and no-ops when the bench is absent, so the shipped desks'
  figures stay byte-identical and remain a usable regression baseline.

VERIFICATION
  Anchors:   66/66 paths resolve on BOTH the reference clone and the Mk2 desk.
  Ownership: 0 lever-owner differences against the originals across all 66
             controls (including the original's "walk up to the root" fallback).
  Feedback:  binding the Mk2 controls through ControlVisuals registers 18 levers
             and 38 lamps; all 66 controls drive a lever, matching the originals.
  Visual:    screenshot at each checkpoint; ChangeHistoryService waypoints set.

FOOTPRINT GATE  (cleared - full table and reasoning in DECISIONS 42)
  Six rebuilt desks measured against their shipped originals, world AABB, corner
  method (Model:GetExtentsSize() is NOT usable here - it reports in the pivot's
  own frame, and HDEF's pivot is rotated 90 degrees, so X and Z come back swapped):
    MainReactorConsole    7.34 x 6.15 x 15.00  ->  6.09 x 6.25 x 15.08
    ThermalConsole        7.35 x 6.24 x 15.00  ->  7.03 x 6.25 x 15.33
    CBLaserConsole        4.07 x 5.88 x 15.00  ->  4.09 x 6.25 x 15.06
    ElectricGridConsole   4.07 x 5.88 x 15.00  ->  4.09 x 6.25 x 15.25
    ALTReactorConsole     7.55 x 6.15 x 15.00  ->  6.44 x 6.25 x 15.06
    HDEFGenerator         4.60 x 7.38 x 1.31   ->  4.65 x 7.38 x 1.38
  Nothing is deeper than the original it replaces, so nothing enters the walkway.

HDEF IS A CABINET, NOT A DESK (BuildHDEFGenerator)
  The six control surfaces do not share one hull after all. HDEFGenerator stands
  7.38 high on a 1.31 x 4.60 footprint, so it is built in its own local frame:
  a carcass that is a real FRAME (both the glazed cell window and the inset
  control bay are genuine openings, not decals), three PowerCell holders each
  with its own NeonPart so one cell can never light its neighbours, and a
  recessed control bay carrying the H.D.E.F. plates, a compact knife switch and
  the guarded emergency button. It keeps the shipped dot paths
  (PowerLever.ClickPart, EmergencyControl, PowerCell1..3, EmergencyControl.ClickPart)
  and takes a +90 degree Y rotation on install.

INSTALLED  (the desks are IN THE FACILITY now)
  All six Mk2 desks were moved off the bench into Workspace.Consoles and took the
  names of the desks they replaced. All seven shipped originals - the six live ones
  plus the dead duplicate CBLaserConsole - were PARKED, not deleted, in
  Workspace.Rebuild.Originals at Y 330 / Z 265 (X 40, 66, 92, 118, 144, 170, 196).
  Each parked model carries GameCoreParkedPivot (its exact pivot before the move)
  and GameCoreParkedFrom, so the install reverses with one PivotTo() per model and
  nothing has to be rebuilt from memory.

  Orientation was solved in world space against each original's own depth/length
  basis, with an explicit facing constraint, because a distance-only score silently
  picks rel=180 and aims the desk at the wall. Final result - front face flush with
  the original's front face, operator side correct:
    MainReactorConsole     yaw   +0.00   front +0.000   back -1.248
    ThermalConsole         yaw  +15.00   front -0.000   back -0.324
    CBLaserConsole         yaw  -15.00   front +0.000   back +0.019
    ElectricGridConsole    yaw   +7.50   front -0.000   back +0.017
    ALTReactorConsole      yaw   -7.50   front -0.000   back -1.111
    HDEFGenerator          yaw  +90.00   front +0.000   back +0.062

  New binding baseline on the installed desks:
    [ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0
    [ConsoleBinder] rebuild desks=0 controls=0 missing=0
  desks 7->6 (the duplicate is gone), reused 61->2 / created 7->66 (the Mk2 desks
  ship no ClickDetectors), missing still 0, and BindRebuild correctly no-ops.
  Lamps 31 -> 41, levers unchanged at 18. Full reasoning in DECISIONS 43.

  Regression, fresh Play session on the installed desks:
    [GameCoreControlTest] pass 13, fail 0, levers 18, fluctuation signMatches 60/60
    [GameCoreSelfTest] PASS, bridgeResolved 18, devices 15, resetOk true
    [GameCore] 25 systems, 12 devices, no runtime errors.

THE WASH-OUT (fixed). The washed-out screenshots recorded in DECISIONS 44 were not the
palette, not the steel MaterialVariant and not the grade. Every SurfaceGui the rebuild
created had LightInfluence = 0, Roblox's default, and 0 means "always fully
illuminated": those plates ignore scene lighting AND exposure, so they render flat
white under any grade while the floor beside them obeys it. The originals all use 1.
    MK2  MainReactorConsole   39 SurfaceGuis, 39 unlit,  0 lit
    ORIG MainReactorConsole   31 SurfaceGuis,  0 unlit, 31 lit
Fixed by setting LightInfluence = 1 on 121 SurfaceGuis across the six installed desks
(109 host parts). Re-shot from the same camera, the amber and red buttons, the AVB red
cap, the cyan accent strips and the panel banding all became visible - they had been
rendering as flat white and were not there to see before. Four options were weighed and
the reasoning is in DECISIONS 45. Carry this forward: the monitor rebuild is all
SurfaceGuis.

THE ART PASS (Phase 19d). Two items off ART_DIRECTION, plus three defects they exposed.

  Button bezels (ART_DIRECTION 3.2). Brightened the collar: CollarOuter "dark" ->
  "lighter", CollarInner "post" -> "light", so a control now reads as a dark cap sunk
  into a light chamfered bezel instead of a sticker lying on the panel. Two palette
  lookups, no geometry moved, no names changed. DECISIONS 46.

  End hazard as geometry (ART_DIRECTION 3.3). The plan to reuse the facility's own
  caution decal was dropped. Measured: the asset renders as a flat WHITE band here, and
  more decisively, all 5685 of its uses in this place - named CautionLine / Caution and
  distributed across Mainframe 1565, CullFolder 1538, MovingParts 743, CoolantReserviors
  661 and a dozen smaller roots - sit at Transparency = 1.00, and a clone-vs-original
  control shows the value survives Clone(). The author disabled it absolutely everywhere,
  so it is not part of the shipped look. Replaced with a brass EndHazard plate and six
  near-black EndHazardBar panels 0.012 proud of it. RebuildKit now depends on no external
  texture at all, so the bench renders identically no matter what loads. DECISIONS 47.

  The 11 visible bands on the installed desks are gone. Those six desks predate the
  change and each carried the decal at Transparency 0 on its plinth Hazard part
  (2+2+2+2+2+1 = 11); they really were rendering white bands. All 11 are now hidden, and
  the installed Main desk re-shot from the operator side confirms no band.

  Two defects the pass exposed:
    - buildShell's entire end treatment had never been visible. Its posts were placed
      INSIDE the body box (z0 + 0.06), so they came out exactly flush with the body face
      and the EndCap was buried 0.03 inside it. Invisible in every screenshot, because
      dead geometry looks exactly like no geometry. Found by raycasting the end of the
      desk for the hazard work. Fixed and verified: EndCap z = [140.450 .. 140.510],
      EndHazard z = [140.380 .. 140.460]. DECISIONS 48.
    - PlaceReference would have cloned an Mk2 desk as its own reference, because the
      install reused the originals' names. Silent - the comparison still runs, it just
      compares a thing against itself. Repaired with a GameCoreMk2 attribute plus a
      parked-original-first lookup; verified 6/6 REF_ clones carry ClickDetectors and
      6/6 MK2_ carry none. DECISIONS 49.

  ONE HONEST CAVEAT. The decal audit ran as a single call that both mutated and reported,
  and its report overflowed the tool result - so it was issued blind and its exact
  changes are not recoverable. The end state is consistent with it having touched only
  the 11 intended instances, and nothing the user had saved was at risk, but that is an
  inference, not a measurement. It is recorded in DECISIONS 49 rather than smoothed over.

## Phase 19e - Installing the corrected desks (pivot transplant)

Phase 19d fixed the bench. The six INSTALLED desks had none of it: not the bright
bezels (DECISIONS 46), not the end hazard geometry (48), not the retired decal (47).
Rebuilding the install from scratch was not available - the orientation solver was a
one-off script and RebuildKit has no Install() - so the desks were refreshed in place by
pivot transplant. For each desk: park the live one as MK2PREV_<name> in
Rebuild.Previous with its pivot recorded, clone the corrected bench MK2_<name>, rename
it to the live name, re-parent to Workspace.Consoles, then Model:PivotTo(the recorded
pivot). Model:PivotTo sets the pivot exactly, position and rotation, so no solver is
needed at all - HDEF landed at 0.00 on every axis.

VERIFIED on all six live desks after the transplant:
  GameCoreMk2 attribute      true on 6/6
  CollarOuter                0.729, 0.729, 0.737 on 6/6
  CollarInner                0.639, 0.635, 0.647 on 6/6
  EndHazard / EndHazardBar   2 / 12 on the five desks (HDEF is a cabinet - none by design)
  visible caution decals     0 on 6/6
  SurfaceGui LightInfluence  0 plates at 0 on 6/6 - every plate is 1 (DECISIONS 45 held)
  bench vs live part names   identical on 6/6, so the transplant lost nothing
  operator walkway           a raycast into each desk hits that desk's own FrontLip or
                             BrassBand - nothing parked standing in front of it

The oriented-corner depth re-measurement reproduced DECISIONS 42 to the centimetre:
Main -1.25, Thermal -0.32, CBLaser +0.02, ElectricGrid +0.02, ALT -1.11, HDEF +0.06.

Functional verification, fresh Play session, then Play stopped and the Edit datamodel
re-read to confirm the work had persisted (CLAUDE 0.4):
  [GameCoreSelfTest]    finalStatus PASS, devices 15, bridgeResolved 18, areas 7
  [ConsoleBinder]       desks=6 controls=68 reused=2 created=66 missing=0
  [ConsoleBinder]       rebuild desks=6 controls=66 missing=0
  [GameCore]            started: 25 systems, 12 devices
  [GameCoreControlTest] pass 13, fail 0, levers 36, lamps 80, signMatches 60/60

THE DOUBLED TEST FIGURES ARE NOT A REGRESSION. levers 36 / lamps 80 and rebuild desks=6
all differ from the recorded baseline (18 / 41 / desks=0) because ConsoleBinder.
BindRebuild keys off MK2_* under Workspace.Rebuild.Models, and the art pass regenerated
those on the bench. The test counts the six installed desks AND the six bench rebuilds.
That is exactly what BindRebuild is for. The README baseline has been corrected.

A MISTAKE, RECORDED RATHER THAN SMOOTHED OVER. The parking step re-parented the outgoing
desks but did not move them, so for the whole refresh the control room held twelve desks
in six positions - each live desk with its predecessor on top of it. It surfaced only
because a diagnostic raycast from the operator side returned
MK2PREV_MainReactorConsole where it should have returned the live desk. Fixed by moving
all six to Y 330 / Z 320 and re-verified by the same raycast. Re-parenting is not
parking. DECISIONS 50.

Screenshot capture could not confirm any of this visually: rblx_screen_capture returned
byte-identical frames for two different camera positions, its camera_position argument
did not move the render camera, and capture_screenshot returned Too many concurrent
requests. The evidence above is therefore numeric - instance state, raycasts, oriented
corner AABBs and a Play session - which is strong but is NOT the visual sign-off
DECISIONS 44 asks for. Item 44 stays OPEN.

ART_DIRECTION 3.2 WAS ONLY PARTLY DONE AT THIS POINT. The bright bezel had reached 8 button
pairs across 4 desks (Main 2, Thermal 2, CBLaser 3, ElectricGrid 1). This paragraph first
said ALT and HDEF "have none"; that was an overstatement written from a part-name count and
it is CORRECTED in Phase 19f - HDEF's PowerCell1-3 are display cells behind a glazed window,
not buttons, and HDEF's one real button already had a bezel that was merely coloured as dark
as the plate behind it. ALT was the only REAL gap. Both are closed now; the bright pair
measures 10 pairs across 5 desks, plus HDEF's single Collar. Note that a DIFFERENT part is
also named Collar - every desk carries dark structural Collar sleeves at Metal 0.235 (Main 4,
Thermal 10, CBLaser 3, ElectricGrid 2, ALT 2) - so grepping for Collar over-counts.
DECISIONS 50 / 51.

NOT YET DONE
  - The control-room monitors, the facility shell and the room interiors have
    not been rebuilt.
  - The install is functionally signed off but NOT visually signed off: DECISIONS 44
    stays open. The unlit-SurfaceGui defect behind the washed-out screenshots is
    fixed (DECISIONS 45), but the desks still read light overall. That residue is the
    hull and the near-white label plates under Brightness 2.5 / EnvSpec 0.80, which is
    a scene-grade question the operator has not ruled on yet.
  - ART_DIRECTION backlog, in the order I would take it (3.2 is CLOSED - see Phase 19f):
      3.5  monitors - dark navy plate with a bright green header bar. Highest value of
           the remainder, and the whole surface is SurfaceGuis, so the LightInfluence
           lesson (DECISIONS 45) applies to every plate.
      3.4  vertical red LED bar-graphs / amber dot-matrix. A Main-desk temp+pressure
           pair and a Power-desk CBL power trio would be the cheapest high-recognition
           detail left.
      3.6  core cyan -> purple at State 2. NEW visual mechanic, needs sign-off.
      6    darker overall grade. Needs sign-off, and ART_DIRECTION 2.1 warns it must
           not be done piecemeal.
  - Workspace.Rebuild.Models still holds the six REF_* clones, and the bench still
    carries Rebuild.Pad plus its mast and rails. The clones are redundant now that the
    desks are installed and can be cleared once the desks are signed off - but NOT
    before, because they are the only visual reference for the install. RebuildKit.
    BuildAll is idempotent and destroys only what it produced. The Pad's hazard stripes
    were built by a one-off command using the decal item 47 retired, so they are
    invisible; the pad is scaffolding and goes with the bench.

## Phase 19f - ART_DIRECTION 3.2 closed (ALT bezel, HDEF collar)

Phase 19e closed with "3.2 is only partly done". This closes it: two RebuildKit changes
and one pivot transplant, reusing the procedure from DECISIONS 50.

  ALT   CollarOuter 1.28 x 0.16 x 1.28 "lighter" at DECK_TOP + 0.29, and CollarInner
        1.14 x 0.14 x 1.14 "light" at DECK_TOP + 0.33, under the 1.00 ActivationButton
        whose top face stays at DECK_TOP + 0.49. THE ROTATION AXIS IS THE POINT: the four
        shared-hull desks mount their controls on a VERTICAL face, so their rings stack
        along X - forward, toward the operator. ALT's button sits on a HORIZONTAL deck, so
        its plates must stack along Y. Same idiom, different axis; copying the shared-hull
        geometry verbatim would have buried the plates inside the deck and changed nothing
        visible. ALT has two ActivationButtons, so it gained two pairs.
  HDEF  its existing EmergencyControl.Collar recoloured "post" -> "light". Colour only,
        deliberately: nothing moved, so the 1.365 cabinet depth item 42 pinned is untouched,
        and the Guard behind it stays "deep", so the bright ring is the innermost element
        exactly as CollarInner is on the shared-hull desks.

A CORRECTION CARRIED IN. Re-reading the builder before acting on this file's own earlier
claim: HDEF's PowerCell1-3 are display cells behind a glazed window recess (Cell 0.86 x
5.20 x 0.50 inside the WIN_X0/WIN_Y0 window), NOT controls; and HDEF's one real button,
EmergencyControl, already carried a 0.10 x 0.94 x 0.94 Collar cylinder in front of the
Guard - coloured "post", i.e. exactly as dark as the plate behind it. The honest statement
is therefore: the four shared-hull desks carry the bright pair, ALT had no bezel of any
kind, and HDEF had a bezel that was not bright. The rule this earns: when a "the code lacks
X" claim was written from a COUNT, re-read the builder before acting on it - a part-name
count says what exists, it never says what a part is for.

MEASURED ON THE SIX INSTALLED DESKS AFTER THE TRANSPLANT (CollarOuter / CollarInner):
  Main 2/2   Thermal 2/2   CBLaser 3/3   ElectricGrid 1/1   ALT 2/2   HDEF 0/0
  -> 10 bright pairs across 5 desks, up from item 50's 8 across 4. HDEF carries no
  CollarOuter/CollarInner at all; its bright ring is the single part named Collar, now
  sitting at the "light" value 0.639216, 0.635294, 0.647059.

VERIFIED (numeric - see the screenshot note below).
  ALT went 178 -> 182 parts (the four new plates); HDEF unchanged at 76. Both landed at
  moved 0.000000 from their recorded pivots.
  World AABB against the shipped originals (oriented-corner method):
      ALT   (8.27 6.25 15.89) vs (9.44 6.15 15.86) = -1.18 / +0.10 / +0.04  still not deeper
      HDEF  (1.38 7.38 4.65)  vs (1.31 7.38 4.60)  = +0.06 / 0.00 / +0.05  reproduces item 42
  THE BEZEL DOES NOT STEAL THE CLICK from the bound control MASS1Systems.ActivationButton,
  which had to be measured rather than assumed. Rays from overhead, front-steep, back-steep,
  side+X, grazing (0.55 above the face) and shallow-front ALL return ActivationButton; the
  plates top out 0.090 below the button face. The one ray that returns something else comes
  in from -X across the neighbouring control and hits PowerLever.Grip, a real control.
  A first attempt returned NOTHING for every ray, which is not the same as "no occluder":
  those rays ended exactly ON the button's top surface, and a boundary hit does not register.
  Overshooting by 1.4x is what made the measurement mean anything - read an all-NOTHING
  raycast as a broken test before reading it as clearance.

Functional sign-off, fresh Play session:
  [ConsoleBinder]       desks=6 controls=68 reused=2 created=66 missing=0
  [ConsoleBinder]       rebuild desks=6 controls=66 missing=0
  [GameCore]            started: 25 systems, 12 devices
  [GameCoreSelfTest]    finalStatus PASS, bridgeResolved 18, devices 15, hdefIntegrity 100
  [GameCoreControlTest] pass 13, fail 0, levers 36, lamps 80, signMatches 60/60
created=66 / missing=0 is the baseline the original install produced, so the transplant
cost no binding. A Mk2 desk holds ZERO ClickDetectors in Edit mode on purpose - the game
creates them at server start - so "0 detectors" on an installed desk is expected, not a
broken bind.

THREE TOOLING TRAPS, recorded because they cost most of this phase (full text: DECISIONS 51).
(a) LINE NUMBERS FROM THE SCRIPT EDIT TOOLS DO NOT AGREE WITH THE LIVE .Source.
    delete_script_lines was asked for 875-883 and reported newLineCount 1194 while a direct
    read of .Source returned 1186, and it removed a different nine lines: it took out ALT's
    ActivationButton, its label, its PowerLever model and three comments, leaving
    plv.Parent pointing at a plv that no longer existed. Only a loadstring() compile check
    caught it. Rule: after any line-numbered edit, re-read the region AND compile.
(b) edit_script_lines CAN REPORT FAILURE AFTER THE WRITE HAS LANDED. The HDEF collar edit
    returned "old_string not found" twice and the change was present both times; retrying
    what looked like a failure is what DUPLICATED the ALT bezel. Rule: re-read before
    retrying.
(c) Instance:GetAttributes() RETURNS AN EMPTY LIST in the plugin VM even when GetAttribute()
    on the same instance returns the value. Probe by name, never enumerate - the whole
    park/restore protocol rides on GameCoreParkedPivot.
(d) Lua LONG BRACKETS EAT THE NEWLINE AFTER THE OPENING BRACKET; Python's do not. An item
    spliced in as [==[ then newline then 52. landed as "...carries it.52." because Lua skips
    exactly one newline immediately after the opening bracket, while the Python mirror, written
    as a triple-quoted string, kept it - so the two sides differed by exactly one byte. Rule:
    never rely on the leading newline of a long bracket when splicing into a doc; put the
    content flush against the bracket, and compare the checksum on BOTH sides, which is what
    caught this one.

THE DOC MIRROR IS VERIFIED BY CHECKSUM, NOT BY LENGTH. While mirroring this phase's DECISIONS
text the two sides came back len 51259 vs 46049. The cumulative-length drill - cumulative
(lineNo, len, sum) every 50 lines, then shrink the first diverging window - localised it to a
duplicated item 51 at the tail. The repair then tripped (b) again: delete_script_lines(633,
701) reported "endLine out of range (633-633)" and had in fact already applied. Both sides
now measure len=46049 sum=3901539 weighted=88995714928, where weighted = sum of byte * the
byte's 1-based index.

SIGNED OFF, A PHASE LATE. Screenshot capture recovered - rblx_screen_capture renders
again and its camera_position argument moves the render camera - so the comparison item 44
asked for was finally taken. The first shot contradicted the assumption this paragraph was
written under, and Phase 19g records the controlled re-test that followed. Item 44 CLOSES.

NOT YET DONE
  - The control-room monitors, the facility shell and the room interiors have not been
    rebuilt.
  - Workspace.Rebuild.Models still holds the six REF_* clones and the bench still carries
    Rebuild.Pad. The clones are the only visual reference for the install, so they clear
    only after sign-off.
  - RebuildKit still has no Install() / Uninstall(); every install has been a one-off
    script. Worth writing before the next transplant.

## Phase 19g - Visual sign-off, and the "too white" claim overturned

rblx_screen_capture works again after three sessions of failure, and its camera_position
argument does move the render camera. Shots taken: a wide control-room view, an operator-side
close-up of the installed MK2 ALT desk, and then the controlled pair below.

WHAT THE FIRST SHOT SAID. The installed MK2 ALT desk renders BRIGHT - its deck reads as a
near-white slab against the dark monitor wall behind it - so "the Mk2 palette is too light"
looked settled. An area-weighted Colour probe of the same desk said the opposite, and two
contradictory readings of one object mean the test is wrong, not the object.

THE CONTROLLED RE-TEST. MK2_<desk> and its untouched REF_ clone sit on the SAME bench, in the
same two-row grid, under the same sky, so measuring both at once removes lighting entirely as
a variable. One camera covering both rows was shot from +X (fronts) and from -X (backs).

  area-weighted Colour luminance, same bench, same frame:
    MK2  Main 0.339  Thermal 0.349  CBLaser 0.351  ElectricGrid 0.347  ALT 0.348  HDEF 0.338
    REF  Main 0.464  Thermal 0.458  CBLaser 0.465  ElectricGrid 0.460  ALT 0.462  HDEF 0.312

  Every rebuilt desk is DARKER than the desk it replaces, by about a quarter. HDEF is the
  exception on BOTH sides - it was always the dark one, and the rebuild tracks it.

WHY THE FIRST SHOT MISLED. It compared two different lighting environments, not two palettes:
the installed desk stands inside the facility under the room grade, its REF twin in open air.
The +X bench shot shows the rebuilt row with MORE visible structure and colour - brass trim,
bezels, dense small controls - than the original row behind it, whose faces are large flat
navy slabs. The -X shot shows both rows reading as the same dark navy cabinet from the back.

THE MATERIAL-COVERAGE GAP IS NOT A GAP. Mk2 carries FacilitySteelPanel on ~62% of its Metal
area and the originals on 100%, which reads like an omission worth closing. It is not: the
bare Metal is 259 of its 287 area of BrassBand / Hazard / BrassSeamBot / BrassSeamTop - the
brass trim, which is deliberately untextured, because a riveted steel texture through a brass
band stops reading as brass. Checked, then left alone.

A BAD PROBE, CORRECTED. An earlier raycast set concluded the parked ORIG_ALT "faces -X". It
does not. Every ray was cast 3.9+ studs ABOVE a 6.15-tall desk, so the +X rays missed
everything and the -X hits landed on unrelated geometry 30+ studs away. The bench shots settle
it properly: both rows face +X, fronts are the LCD faces, backs are the plain cabinet. The
facing constraint of DECISIONS 43 was never in question.

DECISION: no palette change, and no Mk2-specific grade change. DECISIONS 52 carries the
options and why the remaining washed look is deferred to the shell/room phase as one grade.

NOW UNBLOCKED
  - The six REF_* clones and Rebuild.Pad exist to support the comparison item 44 asked for.
    That comparison now exists, so the bench can be cleared once the user has seen it.
  - RebuildKit still has no Install() / Uninstall(). Worth writing before the next phase.

## Phase 20: The control room itself (rebuilt in place)

The brief changed. The reconstruction started on a bench beside the six desks, but the scope is
the whole game - "控制室难道不重做吗？所有东西都要重做哦" - so the room AROUND the rebuilt
desks moves to the front of the queue, and the bench is no longer where the work happens.

WHY THE BENCH IS THE WRONG INSTRUMENT FOR A SURFACE. The A/B that settled DECISIONS 52 worked
because MK2_<desk> and REF_<desk> sat under ONE lighting environment, so lighting was held
constant and only the palette varied. A floor has no neutral environment to hold constant:
essentially all of its appearance IS how light falls on it. A bench floor would therefore have
recreated the exact confound that test existed to remove, and any conclusion drawn from it
would have been about the sky, not the floor. Surfaces are rebuilt IN PLACE instead - the new
work is laid over PART of the room and the camera is pointed at the seam, with the shipped slab
still in frame two studs away under the identical grade as the control.

### 20a. The deck (done)

New module `GameCore.Rebuild.ControlRoomKit`, whose whole job is the room around the desks:

    RestyleBase()                retints the shipped slab (Workspace.Geometry.Floors.
                                 ControlRoomFloor) and records its original colour, material
                                 and MaterialVariant in the attribute GameCoreDeckOriginal
    RestoreBase()                parses that attribute back and clears it
    BuildDeck(rowFrom, rowTo)    lays the plate grid; the row range exists so a PARTIAL deck
                                 can be laid for an in-place A/B
    BuildAccent(xCenter, width)  one recessed cyan Neon line at X 99.60
    RebuildAll(rowFrom, rowTo)   RestyleBase -> BuildDeck -> BuildAccent
    Grid()                       the shared grid metric, so no builder drifts out of alignment

DECK = X 91.55..142.45, Z -35.95..34.55, top Y 276.9. Plates are 6.00 studs on a 6.30 pitch
(0.30 gap), 0.20 thick, standing 0.05 proud of the slab: **8 columns x 11 rows = 88 plates**
over the whole floor. The grid is CENTRED in the slab so the leftover strip splits evenly
against both walls rather than leaving a wide margin on one side and none on the other.

Every added part is `CanCollide = false`, so the walking surface never changes height, and
nothing in the room is renamed or deleted.

**Deterministic tonal drift, not `math.random`.** Each plate's value is hashed off its own grid
indices - `v = 76 - ((i * 7 + j * 13) % 5) * 2` - so rebuilding the deck always reproduces it
byte for byte. A random drift would make every rebuild a different floor and no A/B would be
repeatable. With no drift at all, an 8 x 11 grid of one colour reads as a single flat sheet with
lines drawn on it, which is the defect being fixed.

**Coplanar faces z-fight.** The accent strip runs down the centre of a plate column, so with its
top at exactly the plate top the two faces fought and the line flickered. It now stands 0.03
proud.

**Measured:** `plates=88 cols=8 rowsTotal=11 builtRows=11`, Deck children 88, accent present.
Checked for overlap against every console part before building.

### 20b. The washed-out room was my own regression (done)

The first A/B (ScreenCapture_7 against ScreenCapture_1, identical camera) showed the deck seams
clearly, but the improvement was modest - a (74,76,80) plate was rendering as pale grey. Probing
the fixtures found **1149 PointLights facility-wide, 81 inside the control room, 39 of them room
fixtures**; separating shipped from mine gave the cause:

    Workspace.Lights.ControlRoomLowerLights.RoomLight.NeonPart  bri 0.2  range 10  shadows true   <- shipped
    Workspace.Consoles.ThermalConsole.CoolantControl1.*        bri 0.8  range  3  shadows false  <- shipped (x9)
    Workspace.RoomLights.ControlRoomLights.LightCell.*         bri 2.2  range 22  shadows false  <- MINE (x28)

All 28 are from the previous session's "light spill" pass. They are **11x the shipped
brightness, 2.2x the range, and cast no shadows** - tiled across a closed 50 x 21 x 70 room,
which is uniform fill from every direction, and that is precisely how a room loses its shading.

Retuned to `bri 1.0 / range 11 / shadows true`, with each host part's original values written to
a `GameCoreLightOriginal` attribute first, so the change reverses per light.
**ScreenCapture_8 from the same camera shows the seams and the tonal drift reading again - the
room is no longer a flat white box.**

Lesson carried forward: **when a room reads flat, audit the LIGHTS before the palette.**
DECISIONS 52 spent a full controlled test ruling out a palette that was never the problem.

### 20c. The monitor bank (done)

Seven monitors, not five. Rebuilt IN PLACE for the same reason as the deck: what a bezel reads
as depends on how light falls on it, so it is judged in the room and never on the bench.

**What was wrong.** The shipped bezel is a zero-depth white picture frame - no step, no
fasteners, no seam - and all seven carried the identical, useless nameplate
`SMER - CONTROL ROOM MONITOR`. The screen CONTENT was already good and was left alone.

**Built additively.** 25-34 parts per monitor: a bright `Bead*` rail hugging the screen, a dark
`Frame*` housing band outside it, four corner brackets, 14-23 `FrameBolt*`, and a `ShelfTrim`
lip. Every part is Anchored, CanCollide=false, CanTouch=false, **CanQuery=false** so no future
gameplay raycast can see it, and stamped `GameCoreMk2 = true` for one-sweep rollback. Nothing is
renamed or deleted. `outerW` reproduces each original's own measured width exactly (Main 24.80),
so no monitor grows sideways, and nothing is added at X < 0.10, so none grows backward either.

**THE THREE-VALUE BEZEL COLLAPSED, AND THAT IS THE FINDING.** The design was a dark lip, the
original's mid value, and one bright rail. Four screenshots of four different palette assignments
all showed a single flat white band. The cause is not the palette: **every `Metal` part in this
room renders white whatever its albedo**, because under Brightness 2.5 + EnvironmentSpecularScale
0.8 the specular reflection of the bright environment swamps it. `darker` (60,60,60 Metal) is
indistinguishable from `lighter` (186 Plastic). A 0.205-stud margin cannot carry three bands at a
readable width anyway, so the bezel is now TWO: the bright rail, which is what defines the screen
edge against a black screen, and a dark housing band outside it built in **Neon near-black**
rather than a dark Metal - Neon being the one value in this palette that survives the grade, and
the facility's own recess idiom. **The real fix is the grade: DECISIONS 52 still owns it.**

**Per-monitor nameplates.** A property-only edit to the shipped `TextLabel` - no rename, no
delete. Main / Thermal / Power / Alerts / Quota / Log / Forecast each name themselves now. Kept
to the original's own voice (the `SMER - ` prefix and dash style) and kept SHORT, because the
label is `TextScaled` and a longer string shrinks to fit.

**Two defects found while doing it, both mine** (DECISIONS 59):

1. **The boot text on all seven was clobbered.** The selector matched "any TextLabel under a
   SurfaceGui", which is `Screen.MonitorUI.BootUpText`, not the nameplate on the part named
   `TextPart`. The data read back correct on all seven; only the screenshot showed the new string
   ghosted over the header while the strip still read the old one. Restored from the parked
   clones - all seven originals are empty placeholders filled at runtime.
2. **The seven monitor originals were never MOVED into the parking folder, only re-parented**,
   so they sat exactly coplanar with the live monitors (`liveDelta=0.00` on all seven) and every
   screenshot had the original drawing on top of the rebuild - its own nameplate included, which
   is what produced the ghosting that (1) was first blamed for. Same trap README already
   documents for `Rebuild.Previous`, second confirmed instance. Now moved to Y 330 / Z 340,
   disjoint from the desk row at Y 330 / Z 265, with `GameCoreParkedFrom` / `GameCoreParkedPivot`
   recorded so it reverses with one `PivotTo()` per model.

**Verification.** All seven photographed individually, head-on along their own screen normals:
Main `SMER - MAIN REACTOR MONITOR` (34 parts / 23 bolts), Thermal `SMER - THERMAL LOOP MONITOR`
(32/21), Power `SMER - CBL POWER MONITOR` (32/21), Alerts `SMER - FACILITY ALARMS` (25/14),
Quota `SMER - SHIFT QUOTA` (25/14), Log `SMER - EVENT LOG` (25/14), Forecast
`SMER - FORECAST` (25/14). All clean, no ghosting. Nameplate strings re-read after a 2s wait and
all seven STABLE, so nothing rewrites them at runtime.

### 20d. The Log and Forecast monitors come alive (done)

Two of the seven screens had never been driven by anything. The Log monitor's three severity row
templates and the Forecast's entire timeline - a ScrollingFrame, a timestamped TimeSliceTemplate
and an announcement band - all shipped in the place HIDDEN AND UNUSED, and MonitorService updated
five monitors out of seven. Both are wired now, and both are written as PURE OBSERVERS: they read
GameState and never write it, so the single-writer rule holds and no simulation behaviour
changed. `MonitorService.Update` dispatches seven calls, each defined once and called once, in
order Main - Thermal - Power - Quota - Log - Forecast - Alerts (DECISIONS 60).

THE LOG MONITOR rolls a five-row severity-coded event log over eleven watched signals. It fires
only on a CHANGE and stays silent the first time a signal is seen, so it opens on three boot lines
instead of a dump of the initial state. It reuses the author's own three row templates rather than
inventing UI: their chrome is identical and only the accent bars differ, so one template is pooled
once and recoloured per severity - cyan / amber / red.

THE FORECAST MONITOR draws one bar per sample, width = PowerOutput / the current shift's quota,
labelled with the same `formatClock` the Quota monitor already uses, so it is tied directly to the
operator's actual objective. It is sampled on a deliberate 5-second cadence rather than every
tick, because a timeline is a history and its resolution should be a choice rather than a side
effect of the refresh rate.

BOTH BUILD A FIXED POOL ONCE in `Initialize`, and only mutate text, size and colour after that.
`Config.Monitor.UpdateInterval` is 0 - the monitors refresh every simulation tick - so a
`:Clone()` in the paint path would allocate ten times a second forever. 29 instances total: 5 log
rows and 11 time slices, every one stamped `GameCoreMk2 = true` for one-sweep rollback.

THREE DEFECTS, ALL MINE, ALL CAUGHT BEFORE ANYTHING RAN (DECISIONS 61):

1. `setText` resolved to a nil global. A `local function` declared textually AFTER the insertion
   point is not in scope, and the block had been spliced in above the file's helper locals.
2. The pool was not idempotent, so a second `Initialize` stacked a duplicate set of rows on top of
   the ones already saved into the place.
3. `UpdateQuota` and `UpdateAlerts` were running TWICE per tick, because the first splice inserted
   AFTER its anchor while passing the full replacement text.

AND ONE DEFECT IN THE AUTHORED LAYOUT (DECISIONS 62). Fourteen time slices "fit" the 355px scroll
frame on paper - 14 x 20 + 13 x 5 = 345 - and still bled three rows through the announcement
overlay in practice, because the frame's bottom 60px sits under `AnnouncementFrame` (AbsY
372..432, ZIndex 5 against the rows' 1, at 50 % background transparency). Only 292px is actually
clear, and 25n - 5 <= 292 gives n = 11. The frame height was left alone: `ThresholdTexture`
(130 x 353) and `BorderFrame` (3 x 355) are authored to that same 355, so shrinking it would tear
the chrome.

VERIFICATION, read from instance state and never from module state. Rows span Y 80..350, clearing
the announcement top at 372. A driven shift - Elapsed 0 to 660, outputs 300 up to 3072 and back
down to 150 - produced eleven bars of 26 / 78 / 139 / 208 / 267 / 252 / 191 / 130 / 78 / 39 / 13
px, colours cyan - yellow - red - yellow - cyan. Pool counts 11 after a deliberate second
`Initialize`, row height 20px on all eleven, stray instances 0. The Log monitor rests on its three
boot lines and rolls correctly under driven amber and red events.

## Phase 5 - (this number was never used)
There is no Phase 5 and there never was - the sequence jumps 4 to 6. Nothing is missing from
the work, only from the numbering, and renumbering now would break every DECISIONS reference
that cites a phase by number. Recorded here so nobody spends time hunting for it.

## Phase 19h - Round buttons go flat (operator's correction)   [DONE]

The operator caught this one, verbatim:
    "控制台上面的按钮（就是圆形的那种）是立起来的，但正常应该是平放"
-- the round console buttons stand upright; they should lie flat.

MEASURED FIRST, and he was right. A census of every PartType.Cylinder on the six installed
desks, classified by how far each part's circular axis tilts off horizontal:

    Main 26   Thermal 44   CBLaser 29   ElectricGrid 23   ALT 20   HDEF 2    = 144
    FLAT 0    UPRIGHT 144    TILT 0

Not one flat part in the whole control room. 100 of those 144 are Bolt heads, and those are
correct as they stand - RebuildKit's own comment already says so ("Cylinder's circular axis IS
its local X, so an unrotated bolt head already faces the operator"). The other 44 belong to 15
round buttons, and every single one was standing on edge.

THE GROUND TRUTH is the shipped original, and it settles the question outright.
Workspace.Rebuild.Originals.ORIG_MainReactorConsole.AtmosphereVentButton:

    Part       Cylinder  size=0.10/0.64/0.64   right=(0.34, 0.94, 0.00)
    ClickPart  Cylinder  size=0.10/0.60/0.60   right=(0.34, 0.94, 0.00)
    NeonPart   Block     size=0.12/0.14/0.12   right=(0.34, 0.94, 0.00)

An axis 70 degrees above horizontal. A round button in this facility is a pad you press DOWN
on, not a disc you press forward: its 0.80 x 0.10 x 0.80 pad is canted 20 degrees off
horizontal so the button face is normal to it, and the 0.12 NeonPart cube sits BESIDE the
button on that same plate. The Mk2 had all three of those wrong.

THE FIX IS ONE ROLL. A Roblox Cylinder's circular axis is its local X, so standing that axis
up is 90 degrees about Z:

    L(o, x, y, z, 0, 0, math.rad(90))

Both button builders in RebuildKit now stack their discs along +Y instead of +X. The face
label needed no change at all - label() writes to NormalId.Right, and Right IS the end cap
that is now the top. Which is why the AVB and BOOT legends read correctly on their faces in
the capture without a line of label code being touched.

    15 buttons flattened:  Main 2   Thermal 8   CBLaser 3   ElectricGrid 1   ALT 0   HDEF 0

TWO THINGS THE ROLL BROKE, BOTH CAUGHT BEFORE THE INSTALL.

1. The indicator lamp. Upright, the collar was a disc standing at x + 0.10 and only 0.14
   thick, so NeonPart 0.52 further back along the same pad was clear of it. Laid flat the
   collar sweeps the whole pad in every direction, and the old spot at x - 0.42 fell INSIDE
   its radius - the lamp would have been swallowed by the bezel. It moves to the front edge
   of the pad, which is exactly where the original puts its own 0.12 cube. Since a flat
   collar leaves no room on a 1.40 square pad, the Base is now 1.40 x 1.50 deep - the same
   reasoning as the original's 1.00 x 1.14 pad, whose extra depth exists for that same cube.

2. smallButton's rings were intersecting the deck. A 0.90 vertical disc centred 0.30 above
   the surface reached 0.15 BELOW it, so the pump-station buttons were buried to their
   midline - and no screenshot ever showed it, because the deck hid the buried half. Laying
   them flat and treating `y` as the assembly's low edge rather than its centre puts them ON
   the deck.

VERIFIED, bench and installed, by reading instance state rather than module state:

    bench vs installed, cylinders by orientation, all six desks:  MATCH, 0 mismatches
      Main 6/20/0   Thermal 24/20/0   CBLaser 9/20/0   ElectricGrid 3/20/0
      ALT 0/20/0    HDEF 0/2/0                          (FLAT / UPRIGHT / TILT)
    lowest |RightVector.Y| among the flat parts: 1.000  - dead level, not merely close
    installed round buttons checked 8, geometric faults 0
      (lamp clear of the collar, lamp inside the pad, face up)
    cylinders left at an intermediate angle on the five shared-hull desks: 0
    ClickParts carrying a SurfaceGui: 14, of which 0 are missing their text

THEN A REAL PLAY SESSION, because geometry that is right can still be wired wrong. The
control test clicks the controls for real, and the lamp it watches is the one that MOVED:

    [ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0
    [ConsoleBinder] rebuild desks=6 controls=66 missing=0
    [GameCoreControlTest] pass:13 fail:0   levers:36 lamps:80   finalStatus:PASS
      fluctuation signMatches 60/60
      {"name":"AVB lamp","lampBefore":"0.882353, 0.156863, 0.156863",
                         "lampAfter":"0.352941, 1, 0.470588","lampChanged":true}

That last line is the one that mattered: the relocated NeonPart is still found by
ControlVisuals.findLampParts, still bound to atmosphere_vent, and still pulses green on
press. The binding counts are unchanged from the documented baseline, which is what "no
regression" looks like here.

THE INSTALLED DESKS WERE REFRESHED by pivot transplant (README, "Refreshing the installed
desks") - the route Phase 19e established - because an edit to RebuildKit does not reach a
copy that already lives in Workspace.Consoles. Per desk: park the live model as
MK2PREV_<name> in Workspace.Rebuild.Previous with its pivot recorded, clone the corrected
bench MK2_<name>, rename it to the live name, re-parent to Consoles, PivotTo(the recorded
pivot). Six parked, six installed. The three monitor panels visible above the AVB button in
the final capture are still driving live values (PEA STRESS 23 %, HDEF 100 %, FLUCT +36 F).

## Phase 20e: The four documents are re-reconciled (done)

CLAUDE had drifted 2016 bytes from its disk mirror across two sections, and carried one rule
that pointed the wrong way. Found by comparing section-size tables, not by reading either file -
the prose was fluent throughout and none of it was visible in a read.

  section 2.6  game   669 -> 2806 bytes   Log/Forecast rows, the seven-monitor note, the
                                          monitor binding contract, and - corrected - the
                                          LightInfluence rule
  section 3.1  game   750 -> 2229 bytes   the rebuild checklist brought up to date
  Four stale counts fixed on both sides: desks 7->6, reused 61->2 / created 7->66,
  lamps 31->41, parts 1024->957. All four were superseded by the install and never propagated.
  LightInfluence: both sides told the monitor rebuild to carry 1 forward. DECISIONS 57 says
  labels 1, screens 0 - a screen is emissive and must not take the room's exposure grade.
  Corrected before a rebuild could follow the wrong line.
  ForecastSlices = 11 constraint added (DECISIONS 62).

DECISIONS 64 was out of order in the DISK file only; moved to the end, byte-neutral (74239
before and after). One trailing blank line dropped from the game DECISIONS body.

All four documents now reconcile exactly:
  CLAUDE    disk 38409 = game 37083 + section-0.0 1326   (the only sanctioned difference)
  DECISIONS disk 77729 = game 77729
  PROGRESS  and README were already byte-equal before this entry
See DECISIONS 65.

## Phase 21 - LED bar graphs, the darker grade kept, and the bench cleared (done)

### 21a. ART_DIRECTION 3.4 - the vertical LED bar graph (the last open console item)

ART_DIRECTION 3.4 lists the three indicator forms the reference consoles use, and notes Mk2
had none of the first one: the vertical red LED bar graph. Added to buildInstrumentFace as
barGraph(root, o, z, litFraction, caption).

PLACEMENT. The two inner margins between the three screen panels are the only free vertical
space on the riser face - 0.90 studs at local Z -2.25 and +2.25, which is exactly the panel
pitch, so the columns land in rhythm with the screens instead of being parked in whatever gap
happened to be left over. Checked against every other part of the face before placing them:
the title plate (Y 5.62-6.00), both accent rails (Y 3.65-3.75 and 5.41-5.51), the gauge rings
(Y 3.30-3.86) and the switch bank (Y 6.10-6.14) all clear Y 3.96-5.28 at that Z.

FORM. A recessed darker frame, an unlit well inside it, then 9 BarSegment blocks read
bottom-up, the lit ones redneon and the rest dark. lit is ROUNDED to the nearest segment
rather than floored, so a two-thirds-full column reads as two thirds instead of one short.
Only the topmost lit segment carries a PointLight - one per segment would be 18 lights a desk
for no visible gain at this size. An engraved white chin plate carries the caption.

DECORATIVE, AND DELIBERATELY SO. MonitorService owns every real readout. Nothing here is named
for a control and no part of it is a ClickPart, so ConsoleBinder never resolves it and
ControlVisuals never sees it. The lit fractions are fixed per desk rather than driven. See
DECISIONS 69 for why that is the design decision and not a shortcut.

  24 new parts per desk = 2 frames + 2 wells + 18 segments + 2 captions.
  Five desks carry it - HDEFGenerator has its own instrument face and is not a
  buildInstrumentFace caller:  Main TEMP/PSI, Thermal FLOW/TEMP, CBLaser PWR/LOAD,
  ElectricGrid EXTR/GRAV, ALT MASS/AUX.

VERIFIED BY READING INSTANCE STATE, per desk - lit and dark per column against the requested
fraction, plus a scan for any segment that is neither red nor dark:

  MainReactorConsole   0.72 -> 6 lit / 3 dark    0.41 -> 4 lit / 5 dark
  ThermalConsole       0.55 -> 5 lit / 4 dark    0.35 -> 3 lit / 6 dark
  CBLaserConsole       0.80 -> 7 lit / 2 dark    0.62 -> 6 lit / 3 dark
  ElectricGridConsole  0.48 -> 4 lit / 5 dark    0.66 -> 6 lit / 3 dark
  ALTReactorConsole    0.58 -> 5 lit / 4 dark    0.30 -> 3 lit / 6 dark
  stray colours among all BarSegments on all five desks: 0

### 21b. The install anchored on the bounding box, not on the pivot

The route DECISIONS 50 established records the live desk's pivot and PivotTo()s the
replacement onto it. That is only exact if both generations agree on where the pivot SITS
inside the model, and they do not. Measured pivot minus bounding-box centre matched exactly on
three desks and differed on ThermalConsole by 0.31 studs and on ALTReactorConsole by 0.16.

DECIDED: anchor on the bounding box instead - d = liveCF * new:GetBoundingBox():Inverse(),
then new:PivotTo(d * new:GetPivot()). Convention-independent, and it carries the live desk's
rotation as well. All five landed with a measured centre delta of 0.000 on every axis.
See DECISIONS 68.

### 21c. The darker grade is kept, and 2.1 is no longer deferred

The operator's answer on the grade experiment was 保留这版 - keep this version. It is the
baseline now, not a probe. Values and reasoning in DECISIONS 66, which supersedes the
"deferred to the shell phase" half of DECISIONS 52.

NOTE FOR THE NEXT PASS: the seven monitors were rebuilt under the OLD grade. The dark band on
their bezels had to be worked around with Neon near-black because at EnvironmentSpecularScale
0.8 every Metal part rendered white regardless of albedo. That property is now 0.15, so the
workaround may no longer be needed and the console palette should separate properly for the
first time. Worth a look before the next rebuild stage.

### 21d. The rebuild bench was cleared, after archiving what could not be regenerated

Operator instruction: 多余的、没有的、废掉的都删掉，好让我知道你现在正在做的是那些.

Workspace.Rebuild is gone - 8,293 descendants / 5,367 parts across three folders, plus 19
loose bench parts. What it held and what happened to each part of it is itemised in
DECISIONS 67. The short version: the Mk2 geometry is regenerable from RebuildKit and was
deleted; the pre-rebuild originals are NOT regenerable and were archived to
ServerStorage.GameCoreBaseline.Originals_consoles_and_monitors (14 models).

That move broke RebuildKit.PlaceReference, which looked the originals up at the old path and
would have silently fallen through to Workspace.Consoles - handing the bench an Mk2 as its own
reference, the exact footgun DECISIONS 49 was written about. Fixed by making the archive a
LOOKUP CANDIDATE rather than a replacement, so the module keeps working against a place saved
before the cleanup. Re-run and verified: 6 of 6 REF clones resolved, with part counts matching
the archive exactly (279 / 382 / 316 / 167 / 310 / 545).

BuildAll was confirmed to self-heal - it recreates Workspace.Rebuild and Models if they are
missing - so the bench is a tool that can be cleared and regenerated, not state that has to be
carried. The bench it rebuilt during that test was cleared again in the same pass.

Workspace after the sweep: 123,924 BaseParts, 38 top-level containers, no Rebuild folder.

### 21e. Full verification of the console work

Structural, against the desks being replaced:

  control dot-paths       28 across the 5 desks, missing 0, added 0
  LeverUnion / NeonPart   20 / 34, identical old and new
  parts                   970 -> 1090, +120 = 24 x 5, i.e. exactly the bar graphs

Runtime, a real play session, the same three gates the project has used since Phase 16:

  [ConsoleBinder]       desks=6 controls=68 reused=2 created=66 missing=0
  [GameCoreSelfTest]    finalStatus PASS   bridgeResolved 18   devices 15
  [GameCoreControlTest] pass:13 fail:0   levers:18 lamps:41   signMatches 60/60

All three are identical to the documented baseline. No regression.

### 21f. Documentation-integrity defects found during this phase's section-0.0 mirror, and fixed

TWO DEFECTS, both found while verifying the mirror rather than trusting it.

(1) MIXED RULERS. The byte figures quoted in DECISIONS 65, CLAUDE section 0.0 and PROGRESS were
gathered with two different rulers - character counts for the game modules, byte counts for the
disk mirrors - so they do not diff. Full analysis in DECISIONS 71. No content was missing from
that, but the tables could not be used as a check while they mixed units.

(2) THE DISK MIRROR HAD DRIFTED AHEAD OF THE MODULE. Comparing the two on ONE ruler - bytes,
plus the count of non-ASCII characters as a content fingerprint - showed DECISIONS, README and
PROGRESS reconciling exactly once the 18-character return-wrapper was removed, but PROGRESS
carrying 611 extra characters on the disk side, all of them inside Phase 21. A per-section count
localised it in one step: every section matched to the character except Phase 21, and reading
that section showed FOUR passages that had been written to the disk mirror and never propagated
back into the module - "See DECISIONS 69" (21a), "See DECISIONS 68" (21b), the whole
monitor-recheck NOTE (21c), and the post-sweep Workspace tally (21d).

The game module is authoritative, so the fix was to propagate the four passages INTO the module,
not to delete them from disk. PROGRESS now matches to the character - Phase 21 measures 6,617 on
each side - and README reconciles to a single character. Two residuals remain, both measured
rather than assumed: DECISIONS entries 71 and 72 differ by 10 and 4 characters of WORDING
(whitespace-stripped comparison, so not a wrapping artefact), both written during this same
mirror pass; and CLAUDE is larger on disk by design, because section 0.0 lives only there. The
71/72 gap is wording drift with no content lost, and is left flagged rather than edited blind at
the tail of a session.

RE-MEASURE WITH ONE RULER. #s in Luau and wc -c both count BYTES and agree; a UTF-8-aware
reader's len() counts CHARACTERS and will not. Compare the count of non-ASCII characters too -
it is a cheap content fingerprint that survives line-wrapping differences. And do NOT walk the
source with gmatch("[^\n]*"): that pattern matches the empty string, so it yields an extra match
per line and roughly doubles the count (DECISIONS 72).

## Phase 22 - Every console press goes through one function (ControlTrigger)  [DONE]

**What this phase was for.** The operator asked for the ClickDetector click logic to be extracted
into a server-callable ModuleScript, bound uniformly through CollectionService, and drivable from
the Studio command bar - explicitly without any plugin-side injection API - while leaving physical
ClickDetector presses working.

**ControlTrigger [ModuleScript] is the new single entry point.**
`ServerScriptService.GameCore.FacilitySystem.ControlTrigger`, 629 lines, holds `Bind` / `Fire` /
`Resolve` / `List` / `Reindex` / `Command` / `InstallBus` and the metadata vocabulary.
`ConsoleBinder` kept only its dot-path table: its 58-line `attachClick` body became a 10-line call
site that forwards to `ControlTrigger.Bind`. The click body itself - the `[Console] <player>
pressed: <label> (<console>)` print, the `ConsoleFocus` client notification,
`ControlVisuals.Pulse`, the `ConsoleService.PerformAction` call and the `ControlVisuals.Update()`
that follows it - now exists in exactly one place, and a physical press is nothing but
`Fire(part, player)`.

**The command bar is driven by a BindableFunction, and it has to be.** A `require()` from the
command bar runs in a fresh Luau VM and gets an EMPTY `GameState` - the trap CLAUDE section 0.2
records. Instances are shared between VMs and module tables are not, so
`ServerStorage.GameCore.ControlBus` is the bridge: `ControlTrigger.InstallBus()` sets
`bus.OnInvoke` from inside the LIVE server VM, and any other VM invoking it therefore runs live
code. Verified from a foreign VM: `ControlBus:Invoke("count")` returned the live table rather than
a zeroed one.

    game.ServerStorage.GameCore.ControlBus:Invoke("count")
    game.ServerStorage.GameCore.ControlBus:Invoke("list")
    game.ServerStorage.GameCore.ControlBus:Invoke("ThermalConsole|Cooling Fan 4")

**Binding is tag-driven.** Every bound control carries the `GameCoreControl` tag plus six
attributes (`GameCoreAction`, `GameCoreArg`, `GameCoreArg2`, `GameCoreLabel`, `GameCoreConsole`,
`GameCorePanel`). `Reindex()` walks `CollectionService:GetTagged` and re-binds idempotently, so a
part tagged by hand in Studio starts working on the next server boot without touching the dot-path
table at all. The tag is written once, on the first bind: overwriting it on a later pass would let
the tag disagree with the detector, whose existing connection already closes over the first
definition.

**The counts did not move.** `[ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0`
is byte-identical to the baseline CLAUDE 2.4 records, and the new line reads
`control bus ready: tagged=73 reindexed=73`. Both in-place tests still pass at their baseline
numbers: `GameCoreSelfTest finalStatus PASS, bridgeResolved 18, devices 15` and
`GameCoreControlTest pass:13 fail:0, levers:18 lamps:41, signMatches 60/60`. No gameplay was
changed - a refusal still reaches the player through `Network.Notify` exactly as before.

**73 tagged parts for 74 attachments, and that is pre-existing.** Six desks plus 68 controls is 74
bind calls but only 73 tagged parts, because one HDEF part is the resolved target of two
definitions. In the original code the desk pass connected first and the control pass then hit the
`GameCoreBound` guard, so the behaviour is unchanged; the record-metadata-once rule is what keeps
the tag consistent with that single connection.

**One real defect found and fixed while verifying.** See DECISIONS 75: the ClickDetector was
parented to the click plate, and on a lever the plate sits buried under the Collar and the Grip,
so a mouse could not reach it at all. 25 detectors now live on their own assembly model instead.
Physical-click reachability went from 68/73 to 70/73, and the measurement is in DECISIONS 75.

**A deliberately untouched remainder.** Three HDEF power cells (`PowerCell1.Cell`,
`PowerCell2.NeonPart`, `PowerCell3.Cell`) are still unreachable by mouse. Measured from 50
verified-free ray origins at 6, 9 and 12 studs, not one ray reaches them - so they are genuinely
enclosed inside the rebuilt HDEF cabinet, not a probe artefact. The same probe reports 26 hits for
a control lever, which is the control case that proves the method. Relocating those detectors
needs a decision about what the operator is supposed to click - the cell behind its glass, or the
bay lip - which is a gameplay question rather than a binding one. Left open on purpose and
recorded in DECISIONS 75. All three remain fully drivable from the command bar.

**Two tooling traps were paid for during this phase, both recorded in DECISIONS 76.** The Studio
edit layer decodes Lua escape sequences before they reach the file, so a newline written as the
two-character escape inside a short string arrives as a real line break and is a syntax error.
`ControlTrigger` is therefore written with zero backslash characters on purpose. And the official
mouse-input tool's y coordinate is not viewport space - it reads 58 px low at this viewport size,
which is what made the first physical clicks miss.

## Remaining / Known
- Coolant sensor recalibration is tuned to the Wiki's
  intended difficulty (Wiki: coolant pumps break, pressure-stall strategy exists).
- External sound assets in the place are not authorised for this account (pre-existing,
  unrelated to GameCore).
- Equinox trigger time is shift-second 600 (12:00 PM on the quota monitor).

### 21g. The monitor shell re-graded - the Neon near-black band retires (done)

PHASE 20c LEFT ONE ITEM OPEN, and named it: the dark housing band around the seven screens was
built in Neon near-black **as a workaround**, because under the then-current grade every `Metal`
part in that room rendered white whatever its albedo. 20c closed with "the real fix is the grade:
DECISIONS 52 still owns it". DECISIONS 66 delivered that grade - `EnvironmentSpecularScale`
0.8 -> 0.15 - so the workaround no longer has a reason to exist, and this phase retires it.

**What changed.** 21 parts, three per monitor: `FrameTop`, `FrameSideL`, `FrameSideR`. Each went
from `Neon 17,17,17` to `Metal 75,75,76` with `MaterialVariant = FacilitySteelPanel` - the exact
value and variant already carried by the 14-23 `FrameBolt*` on the same monitor. Appearance
properties only. No part was renamed, moved, resized, reparented or deleted.

**What deliberately did NOT change.** `Screen` stays `Neon 17,17,17` on all seven. It is not
decoration: it is the backing that hosts `MonitorUI`, `BootUI`, and four `SurfaceLight`s, and a
near-black self-lit panel is what an off LCD reads as. Seven of the 28 `Neon 17,17,17` parts in
the bank were therefore in scope and 21 were out; the split is the whole content of this change.

The bright `Bead*` rail (Plastic 186,186,188) and the corner brackets and `ShelfTrim` (Plastic
163,162,165) were already outside the Neon set and were not touched, so the three-value bezel 20c
designed - bright rail, dark housing band, bolts - is intact. What changed is only that the dark
band is now real dark metal instead of a Neon stand-in.

**Why the change is safe.** `grep_scripts` on `FrameSide` returns 0 matches across all 180
scripts, so no binding reads those names - which is what CLAUDE section 6 requires before an
appearance edit. The full 21-part set was re-read after the write: 21/21 on `Metal 75,75,76 /
FacilitySteelPanel`, 0 off, and `Screen` re-read as still `Neon 17,17,17` on 7/7. ChangeHistory
waypoints were set before and after, so Ctrl+Z reverses it in one step.

**Judged in the room, per 20c's own rule.** Photographed from inside the control room along the
Main panel's normal and from a corner angle. The housing band now reads as a brushed metal trim
that picks up a specular gradient along its length, and it sits next to bolts of the identical
material rather than next to a flat black stripe. No monitor lost its edge definition against
its own black screen, because the bright `Bead*` rail is what carries that edge and it was never
part of the Neon set.

**SCOPE NOTE, recorded so the number is not misread later.** `Neon 17,17,17` is not a monitor
idiom - it is the facility's own recess idiom and 804 such parts exist across Workspace, on
coolant processor frames, gateway alarm plates, door levers, control-panel text and screens. This
phase touched 21 of them, all under `Workspace.Monitors`, and nothing else. The other 783 are
original work and out of scope.

**Follow-on.** The seven monitors were rebuilt under the OLD grade and this is their first review
under the new one, which was the open item NIGHT_LOG carried into this round. The five console
desks and the deck were reviewed under the new grade in 21c-21e; the monitor bank was not, and
now is. No further grade work is outstanding on the bank.

## Phase 23 - The three CBL lasers (Task A)  [DONE]

NIGHT_LOG priority 3 asked for the three combustion lasers in `Workspace.ReactorCBLs` to be
rebuilt. They were measured first, and the measurement changed what the job was.

**What the three machines actually are.** 2,763 BaseParts each: 210 MeshParts, 100
UnionOperations, 485 Wedges and 251 live Texture/Decal children, with 2,607 of the parts solid hull
already carrying `ReactorWallPlate`. That is authored work, not a blockout, so a primitive rebuild
would delete all of it and put boxes in its place - which CLAUDE section 1.4 forbids, because there
is no replacement for an authored mesh. The defect was chromatic, not structural. Measured against
the archived before-state, each machine carried 103 distinct colours and every one of them was a
desaturated grey: 99,98,100 on 816 parts, 163,162,165 on 248, 223,222,225 on 125, 176,175,177 on
121, 145,145,145 on 120, 53,53,53 on 96. No emissive accent anywhere, so in the now-dark reactor
hall the machine read as a pale tube.

**So Task A was delivered as an additive refinish.** `GameCore.Rebuild.LaserKit` recolours and adds.
It renames nothing, deletes nothing and moves nothing, so the CLAUDE section 6 binding contract and
the single-writer rule are both untouched. The originals are archived whole in
`ServerStorage.GameCoreBaseline.ReactorCBLs_original`, so a rollback is a copy from there and no
per-part colour backup has to be stored in the place.

**What was written, per laser.**
- 2,408 / 2,410 / 2,408 parts recoloured - `Color` only - across CorrodedMetal, Plastic and
  SmoothPlastic.
- 106 new parts under one new folder each, `Mk2Accents`: 2 dark seam rings, 3 brass collars with
  lips and 12-head bolt circles, 1 brass breech ring, 36 cyan inlay strips in three segments,
  6 status lamps, 4 louvre stacks, and a lit cyan aperture ring with its lens and lip.
- Part count 2,763 -> 2,869 per laser, exactly +106. Neon across the machine 101 -> 162, so 61 of
  the new parts are emissive. Workspace BaseParts 124,869 -> 127,111, of which this phase accounts
  for +318; the rest of the difference is the Mk2 console install, the LED bars and the monitor
  work already recorded above.
- 100 unions, 485 wedges and 251 decals per laser preserved. 0 of the new parts carry a
  ClickDetector or a `GameCoreControl` tag, so nothing new can be clicked.

**The frame comes from the beam, not from the pivot.** The models arrived from the ripper with
arbitrary pivots - the Mk3_1 pivot looks along (0,-0.97,0.26), which has nothing to do with the
barrel. The frame is therefore derived from `Laser.LaserPart`, a 40-stud part whose own X axis is
the barrel axis. Everything the module writes is in barrel coordinates: +X breech to muzzle, +Y up.

**Which end is the muzzle was settled by measurement, not assumption.** The axis direction is
ambiguous in a near-symmetric tube. It was resolved from authored part names: `FiringEffectPart`
sits at +7.40, the 48 `CautionTape` hazard plates span +4.46 to +5.96, a ring of MeshParts sits at a
single station +5.22, and the hull pieces stop dead at +5.86. Hazard tape and firing effect at the
same end means the muzzle is +X. Getting that backwards would have put the aperture on the breech.

**Three drafts of the radius, and the third was wrong for a subtler reason than the first two.**
`Profile` first bucketed part CENTRES, so every on-axis disc read as radius 0.00 while the real hull
sits at 5 to 7. It was fixed to measure each part's true extent over all eight corners of its
oriented box - but a bare percentile is still the wrong question, because the machine carries a cage
of twelve Struts at radius 9.58 and a stack of thin discs at 9.9, so a maximum gave a 20-stud washer
while a 60th percentile gave a ring buried inside the shell. Adding an angular filter to pick the
local surface did not rescue it either: at most stations no part centre lies within 26 degrees of
+Y at all, because the plating is not centred on the cardinals. `SurfaceScanner` now casts a ray
inward from outside the machine at the exact station and angle each accent needs. It reads clean and
consistent - hull radius 8.08 at the breech, 5.86 at the seam, 4.78 at the muzzle, uniform to
within 0.02 all the way round - and it showed the analytic build had been sizing the breech two
studs too small.

**A self-referential bug worth recording.** The earlier version measured, on a second run, the
accents the first run had built: `SeamA` came back as hull at radius 10.52 and `Collar2` at 14.00,
so every re-run inflated the next. `Profile` now excludes `Mk2Accents`, and `Accents` builds its
parts with `CanQuery = false`, which keeps them out of the raycast as well.

**Two defects found by looking at photographs, not by counting parts.** The breech cap is two
`Meshes/ThinCircle2` discs 14.3 studs across - the single widest flat surface on the machine - and
the first zone table painted that whole end with the brightest tone, so it caught the most light and
read as a pale mass. The rear cap is now the darkest zone, which also gives the brass `BreechRing`
at -52.5 a dark field to read as a bright rim against. Separately, the pale lump on the emitter head
turned out to be `SlightlyBetterSpinnyThing/Effects`: solid opaque CorrodedMetal unions authored at
(188,187,190) sitting inside a folder literally named Effects, which the skip list had been
protecting as if it were a particle rig. Material, not folder, is what protects the FX layer - every
real emitter and glow in there is Neon, Glass or transparent.

**The pass is idempotent, and finding that out took a second run.** `Recolour` skips anything below
luminance 0.25 so as not to lighten the parts authored at pure black - but `steelDark` tones to
luminance 0.185, so a second run treated its own output as deliberately black and skipped it. The
threshold is now 0.10, above the three SmoothPlastic pieces at (0,0,0) and well below the darkest
palette tone. Verified by running the whole pass twice against the bench clone: 2,411 recoloured on
both runs, byte-identical colours, 106 accents both times, descendant count steady at 4,102.

**Still open, and deliberate.** The 110 parts per laser that stay desaturated grey are the ones
carrying a Texture or a Decal - the 48 hazard tape plates, the 12 grates and the 24 decal'd plates.
Their base colour is only a tint on artwork that is doing the visible work, so recolouring them
would dim the tape. The bare Plastic pieces that had no texture were in scope, and were toned.

## Phase 24 - The TempLabel second writer  [DONE]

The open question in CLAUDE section 3.2 is closed. The main monitor's `TempLabel` was
changing at irregular sub-second intervals (0.40 0.72 0.38 0.30 0.80 0.40 0.70 0.10)
while `FluctuationLabel`, written by the same function on the same tick, held a steady
1.10s. Both labels were sampled together in a live server, and the pattern was a large
step once every ~1.1s - the core's own once-per-second update - with a 1 F drop about
three times a second in between.

That in-between drop was `PowerSystem.Update`:

  r.Temperature -= r.PowerOutput * cfg.ExtractionHeatLoss * dt

a per-frame write to a value that had just been converted to change once per second.
`ExtractionHeatLoss` is 0.02 and output is about 141 GW at ignition, so the sink is
2.8 F/s delivered as 0.28 F per frame - one display step every 3.5 ticks, or 0.35s.
The sampler measured 0.30s and 0.40s alternating.

The fix keeps the number and moves the write. PowerSystem now publishes
`r.ExtractionHeatRate` in F per second; ReactorState subtracts it inside its own
once-per-second block. ReactorState alone now writes `Temperature`, which is what
DECISIONS 7 said in the first place.

  before   TempLabel 0.162 0.364 0.664 1.063 1.363 1.462 1.757 2.164 2.466
  after    TempLabel 0.918 2.017 3.123 4.224 5.329 6.423 7.514
           gaps      1.10  1.11  1.10  1.10  1.09  1.09

The two labels now change on the same step, which they never did. Cooling magnitude is
intact - mean step -129 F before, -134 F after, the difference being the extraction sink
now folded into the step. `TempFluctuation` also stops understating every reading by
about 3 F, because it now measures the complete per-second change.

Verified in a fresh Play session: GameCoreSelfTest `finalStatus: PASS`, `resetOk` true,
`devices 15`, `bridgeResolved 18`; GameCoreControlTest `pass:13 fail:0`,
`levers:18 lamps:41`. Full reasoning, the ruled-out hypotheses and the failed traceback
route are in DECISIONS 79.

## Phase 25 - The seven monitors under the new grade  [DONE]

CLAUDE section 3.1 carried one open item out of Phase 20: all seven monitors were rebuilt
before the darker grade landed in Phase 21c, and had never been looked at under it. They
have now, both ways.

INSTANCE STATE FIRST. Every Lighting value matches the DECISIONS 66 table to the digit -
Brightness 1.200, EnvironmentDiffuseScale 0.420, EnvironmentSpecularScale 0.150,
ExposureCompensation -0.080, Ambient (25,24,27), OutdoorAmbient (52,60,72), Atmosphere
Density 0.20 / Glare 0.08 / Haze 0.45 / Color (120,128,138) / Decay (38,36,40), Bloom
0.85 / 26 / 1.15, ColorCorrection 0.02 / 0.20 / +0.02, SunRays 0.08 / 0.85, ClockTime 12,
GlobalShadows true, ShadowSoftness 0.300. All seven screens are Neon (17,17,17) with
SurfaceGui.LightInfluence 0.00, which is the documented contract for a screen backing.

THE DECISIVE PROBE. The reason this item existed at all is DECISIONS 58 and 59: under
EnvironmentSpecularScale 0.8 every Metal part rendered white whatever its albedo was, so a
monitor that read correctly and a monitor that was merely blown out look identical in a
capture, and no property panel separates them. The way out is to delete the variable. Both
trim members - the Metal band and the Plastic beads - were set to ONE albedo, 75,75,76,
and the room was captured: the band came back dark grey while the ceiling light panels in
the same frame came back pure white. Under the old grade the band would have gone with
them. The specular fix is confirmed on the real parts, not only on the property value.

A false alarm worth recording, because it cost time twice. In the ordinary captures the
light outer border is the authored Plastic bead at 186,186,188, which sits 0.135 studs in
front of the Metal band at 75,75,76. Two different members at two different depths, which
is the design intent. No defect.

THE NEON SCREEN BACKING STAYS, and not because the workaround is still needed - it is
not, a dark panel would stay dark now. It stays because a flat, self-lit, shadow-free
surface is the right look for a screen, because each screen's four SurfaceLights are built
on that part, and because it is a binding-critical host that no possible gain justifies
touching. Here the workaround and the right answer coincide; the reason it is kept is the
second one.

All seven nameplates carry the authored SMER - ... house style: SMER - MAIN REACTOR
MONITOR, SMER - THERMAL LOOP MONITOR, SMER - CBL POWER MONITOR, SMER - SHIFT QUOTA,
SMER - EVENT LOG, SMER - FACILITY ALARMS, SMER - FORECAST. Read back and left exactly as
authored.

## Phase 26 - The main monitor diagram is live  [DONE]

CoreDiagramFrame's two intensity screens and ReactorDiagramFrame's CBL, coolant-pump and
P.E.A nodes now follow the simulation. This was the last static panel on the main monitor.

They shipped dead, and not merely switched off: both GraphImageLabels are Visible=false
AND carry a zero-height box parked one full frame-height down and roughly two frame-widths
to the right (Position.X.Scale 1.900 for GraphFrame1, 1.817 for GraphFrame2).
GraphDetailThingy, the Script inside CoreDiagramFrame, is a three-line
UniversalSynSaveInstance comment stub with no logic. The art was authored unused rather
than switched off later, and the original animation is not recoverable from the place.

  GraphFrame1         reactor energy intensity   PowerOutput / ShiftQuotas[shift], the
                                                 same normalisation the Forecast monitor
                                                 uses, so the two screens agree
  GraphFrame2         P. E. A. EXTRACTION        PEASystem.GetExtractionRate() / 4, the
                                                 inverse of the readings frame, which
                                                 prints the same number times 25
  WarnningImageLabel 1-3                          visible at P.E.A stress 100, or for the
                                                 duration of an Equinox event
  ReactorDiagram CBL1-3                           LaserFrame visible only while the laser
                                                 is beaming; CBLImageLabel tinted on the
                                                 same key the power monitor uses
  ReactorDiagram CoolantPump1-3                   CoolantBlockFrame green running, red fault
  ReactorDiagram CoreImageLabel                   lit while the reactor is online
  everything                                      purple (190,80,255) for the duration of
                                                 an Equinox event, per the Wiki

The bar is driven by WIDTH. The authored box is re-anchored to (0,0,0,0) and sized
frac,0,1,0 rather than filled by a texture, so it reads correctly whatever the image is,
and at zero width the panel is exactly the static art it replaced - a dead reactor looks
like the old monitor, not like an empty one.

PURE OBSERVER. It reads GameState and never writes it, so no simulation value moves
because of this file - the rule DECISIONS 54 and 60 set for the log and the forecast. It
is folded into MonitorService rather than registered as a system, so the documented system
count, the SystemManager priority table and GameCoreSelfTest are all untouched.

VERIFIED LIVE FIRST. In a real Play session the live server's own Update produced
g1 w=0.141 and g2 w=0.250 at 0.50,0.73,0.86, three beams visible at 0.47,0.78,1.00, the
core visible at its authored 0.31,0.31,0.31 and pumps at 0.47,1.00,0.86. Those colours
exist only in the new code, so the new path is confirmed executing against live data.

Then branch by branch, in Edit mode, with MonitorService.Initialize() called first so the
cache is populated. Without that call an execute_luau require returns an empty module whose
cache is nil, UpdateDiagram early-returns, and four different inputs come back
byte-identical - the signature of the CLAUDE 0.2 fresh-VM trap, not of a bug under test.

  half output, stress 40    g1 0.500 at 1.00,0.85,0.32 (amber)   g2 0.750   warn hidden
  stress 100                warning triangles visible at 1.00,0.00,0.00
  Equinox                   g1 1.000, everything at 0.75,0.31,1.00, warning visible
  offline                   g1 0.000 and hidden, core hidden, every beam hidden

The two GraphImageLabels were then returned to the authored parked state - Visible false,
Position 1.900 and 1.817 by 1.000, Size 2.000 by 0 - and read back to confirm it. Full
reasoning and the bug this feature hit on the way in are in DECISIONS 81.

## Phase 27 - The four documents are byte-mirrors  [DONE]

The doc mirror had been checked with byte counts for several sessions, and a byte count cannot see a
divergence that MOVES bytes instead of adding them. All four pairs were re-checked with a rolling
hash over the whole body (DECISIONS 82). It found five real differences in DECISIONS and one moved
blank line in each of README and PROGRESS - every one of them invisible to the checks that had been
passing.

All four are now byte-identical to their modules, except CLAUDE, which is longer on disk by exactly
the disk-only section 0.0. Three of the five differences were editing drift; two were silent tool
damage:

    - the Studio edit layer had decoded a newline escape inside a quoted Luau example and split the
      source line in two, in entry 71's own recipe;
    - the disk had kept the literal long-bracket terminator where the module is forbidden to
      contain it, and entry 77 had recorded that as permanent rather than removable.

Both are written up in DECISIONS 82 with the pattern-free repair method, and the mirror rule now has
an exact number attached: the wrapper is 17 bytes, not "about 18".

## Phase 28 - The ambient layer was already there, and two emitters were dead  [DONE]

The third item under Priority 6 was "ambient VFX (heat haze, steam, current)", listed as not
started. Measuring before building changed that: the layer exists. 278 ParticleEmitters across
Workspace are Enabled with a nonzero Rate, against 1,368 that are off, so the always-on ambient
layer is real and 258 of those sit outside CullFolder. The dominant family is Smoke at 105.

Workspace.Core is the exception and is exactly as CLAUDE 2.10 describes it: on=0, off=97, every
core emitter gated behind an event.

One real defect came out of the same pass. Two enabled emitters carried a Texture of 6422188442'
- a bare id with no asset prefix and a trailing apostrophe - which cannot resolve, so both have
always drawn nothing. Normalised to rbxassetid://6422188442 and re-audited: malformed is now zero
out of 29,269 asset references checked.

The audit method matters for the next session: a string-shape check, not an asset fetch.
CreateEditableImageAsync was tried as an authorization probe and gave opposite answers on two
consecutive runs, so it is not usable as an oracle here.

DECISIONS 83 carries the numbers and the reasoning. CLAUDE 2.10, 3.1 and 3.4 are corrected in the
same step, since 2.10's "only fire when an event triggers" was the line pointing at work already
done.

## Phase 29 - The material pass skipped a third of its targets  [DONE]

The pass that applied the three AI materials filtered on Material == Metal, so parts already
authored as DiamondPlate or CorrodedMetal never entered the loop and were neither converted nor
tagged. Its own summary counted only what it touched, so it could not report the gap.

Measured: Metal 48,546 tagged / 305 untagged, DiamondPlate 5,907 tagged / 3,194 untagged,
CorrodedMetal 44,456 tagged / 0 untagged. CorrodedMetal survived only because the HEAVY
containers set it explicitly instead of matching it.

Fixed by tagging 3,545 parts - DiamondPlate to FacilityFloorPlate, Metal to FacilitySteelPanel -
mapping on Material and assigning only variants whose BaseMaterial matches, so the Material
itself can never be rewritten as a side effect. Tagged 3,545, failed 0, untagged remaining 0.
Totals are now Metal 48,983 / DiamondPlate 9,103 / CorrodedMetal 46,951, all tagged.

CLAUDE 2.8's counts were a snapshot of the first pass, not an invariant; they are updated and
labelled as such. The night log's claim that the facility shell is ClickDetector-free holds for
the four containers it named but not for the shell as a whole - Facility has 16, MovingParts 30,
Geometry 1 - and CLAUDE 2.9's ClickDetector total is 941, not 1,023.

Three empty MaterialVariants (MaterialVariant, MaterialVariant1, CoolantRepeatingTexture) have no
Texture child and zero references; left in place deliberately and recorded rather than deleted.

DECISIONS 84.
## Phase 30 - Control-room shell: corrected, not rebuilt  [DONE]

The shell was assumed bare and was going to get a 182-part panel-and-rib field plus a ceiling
bulkhead and a cove. The kit's own clash audit returned HARD=0 / SOFT=713, and the 713 soft hits
forced a structural dump that refuted the premise: all four walls already carry panel fields,
vertical slats and ribs, and the west side is a duct chase with 26.5 x 4 x 10 beams crossing
fifteen studs into the room. Two of the planned specs would also have buried a security camera
TextPart. The plan was dropped whole, and the kit builds nothing.

What the shell actually needed was a correction. The room already runs a 100/75/60/50 ladder and
two things sat outside it: the ceiling slab plus 16 wall parts wearing DiamondPlate and
FacilityFloorPlate - the floor's material and the floor's variant - at 160, and 13 FrontWall
parts at 205. Every wall was brighter than the desk hull at 108.

The first rule was a blanket luminance threshold, and the dry run caught it recolouring 25 light
plates and 2 amber signal lights. Fittings, not surfaces. The gate moved from the tone to the
material variant.

Applied: recoloured 80, resteeled 25, failed 0, skipped 1,291 of 1,379. Verified live - zero
structural parts above luminance 120, zero FacilityFloorPlate on the shell, all 27 fittings
preserved, 88 origin records. The shell's brightest large surface is now 100, below the desk
hull, so ART_DIRECTION 2.1's red line holds numerically. Appearance properties only;
ControlRoom holds zero ClickDetectors.

DECISIONS 85.

## Phase 31 - Reactor-chamber wall tone: measured, refuted, no write  [DONE]

ART_DIRECTION 3.6 wants the chamber to read as a near-black box, so 230 wall parts at 200,205 -
the largest bright family in the facility at 378,704 studs of face, 71 per cent of the chamber's
large surface, wearing the same material and the same variant as the room's own 96..127 panel
family - looked like the DECISIONS 84/85 defect class repeating.

The FULL non-Neon tone histogram of the wall subtrees refuted it: a continuous ladder 0 through
255, mode 192-207 at 1,040 of 4,079, with 229 parts above the suspected family. The suspected tone
is the room's dominant tone.

The wrong reading came from restricting that histogram to large faces. Large-face statistics are
not the room's tone, and here they diverge completely - 980 of the 1,138 non-Neon parts in the
190-223 band ARE the walls, so the filter keeps the walls and hides the ladder they sit in. The
aperture decided the finding.

Confirmed three ways: the band above 223 is 269 parts and 2,044 studs of face with zero parts at
face 300 or more; the 267 FacilityFloorPlate and 12 bright Concrete parts in wall scope are
vertical strips at thin 0.1-0.2, i.e. detail trim; Mainframe's 2,405-part bright family is labels
and line work at 7,719 studs in total.

A tone-distance outlier test was also tried facility-wide and is the wrong instrument - it flags
CullFolder's 55 surfaces that are only the chamber's walls against the control room's shell. The
instrument that works is material-role mismatch, and re-running round 7's ceiling test finds no
recurrence.

No scene write. No kit, deliberately. Queries kept in _tools/shell_audit.lua.

DECISIONS 86.

## Phase 32 - Control-test coverage: twelve controls, and a dead lever found on the way  [DONE]

CLAUDE 3.3 listed coolant_recalibrate, QPU replacement, Gateway and GravLift as uncovered controls.
The QPU / Gateway / GravLift half of that is a category error - ConsoleBinder has no entry for any
of them, they are standalone FacilitySystem modules, and a console-control test is the wrong
instrument. The genuinely uncovered controls numbered twelve.

All twelve are now covered by a second test phase that asserts on GameState and on the owning
system rather than on the scene: coolant_recalibrate, startup, shutdown, monitor_boot,
pressurizer_vent, pea_vent, gravatron_charge, gravatron_overload, hdef_lever, hdef_emergency,
hdef_cell, metu_ecc.

THE REAL FINDING. Extending the test exposed a defect that had nothing to do with coverage: the
HDEFGenerator power lever had been frozen since bind time. ConsoleBinder binds both PowerLever
(hdef_lever) and EmergencyControl (hdef_emergency) on HDEFGenerator, the generator owns one
LeverUnion, both controls walk to it, and Bind overwrote the first action with the second.
detent() has no hdef_emergency branch, so the handle never moved again - while the control still
fired, the state still flipped and the lamp still changed colour. Nothing reported it.

Fixed in ControlVisuals.Bind with a guard that asks detent() whether an incoming action can drive a
lever, and refuses to let a non-driving action displace a driving one. Enumerated facility-wide,
five levers are reachable by more than one action; four are legitimate and all-detented, and
exactly one was pathological. DECISIONS 87.

THE PROBE WAS ALSO WRONG. The first re-run reported pass:28 fail:2, and both failures were the
test's: rows with an Arm precondition sampled the lever pivot before ControlVisuals.Update had
re-rendered the armed state. One row passed only because the preceding row left the scene armed - a
spurious pass, which is worse than a false failure. Fixed by re-rendering after Arm. DECISIONS 88.

Fluctuation went from the recorded 60/60 to 5/5 and is correct: the old figure measured the
double-writer bug fixed in Phase 24 / DECISIONS 79.

MEASURED: pass:30 fail:0, finalStatus PASS, visuals 18 levers / 41 lamps, fluctuation 5/5, a
12-row stateTests table all PASS, and the lever diagnostics list now reading action=hdef_lever
detent=2 where it previously read action=hdef_emergency detent=-1.

Two Source edits, no scene write.

## Phase 33 - LEGACY QUARANTINE

THE TWO MOVES, AND THE NUMBERS THAT PROVE THEY WERE INERT.

  ReplicatedStorage.CulledParts  ->  ServerStorage.CulledParts                 38869 parts
  Workspace.Reactor_Laser_Mk3_3  ->  ServerStorage.Reactor_Laser_Mk3_3_StrayCopy  2869 parts

  ReplicatedStorage BaseParts   38875 -> 6
  Workspace BaseParts          129980 -> 127111
  ServerStorage BaseParts       11754 -> 53492

  Workspace changing at all on the first move would have been the alarm; it did not change. Both
  parks carry a StringValue named ORIGIN recording what they are, where they came from and how to
  undo them. Nothing was deleted.

WHY THE FIRST MOVE IS FREE. ReplicatedStorage does not render, so those parts were already
invisible. It DOES replicate, so every client was receiving 38869 instances it never drew and
holding them for the session. That is the whole win. See DECISIONS 90.

WHY THE SECOND MOVE IS FREE. The loose laser sat outside the reactor chamber, carried no
ClickDetector, no attribute and no tag, and no live script names ReactorCBLs at all. See
DECISIONS 94.

VERIFICATION - Play mode, server datamodel, read as INSTANCE STATE not module state:

  [GameCore] started: 25 systems, 12 devices
  REAL ERRORS=0  REAL WARNS=0        (after filtering the known asset-permission flood)
  Consoles ClickDetectors=69        GameCoreControl tagged=73
  Stats: ActiveQPUs=6  MainframeMeltdown=false  GravatronActive=true
  Monitor labels live: SMER - MAIN REACTOR MONITOR / PENDING REACTOR ACTIVATION / CBL1-3 / P. E. A.

THE AUDIT THAT FOUND THEM, INCLUDING ITS OWN THREE WRONG INSTRUMENTS.

  Instrument 1 counted readers by container name and treated the four document modules as code. It
  inflated the bound set and it made Mainframe look like a prize.

  Instrument 2 tested twins by instance NAME. Parts are overwhelmingly named Part, Union and Wedge,
  so every generic name matched something and Geometry scored a meaningless 100 percent.

  Instrument 3 compared POSITION AND SIZE instead, and returned 0 percent for everything tested.
  That is the correct answer and the opposite of instrument 2: none of the parked content is a
  duplicate of anything. It is the only copy that exists, which is why parking is the right action
  and deletion is not.

  Instrument 4 had to exclude ServerStorage before it meant anything, because scripts parked there
  never run. See DECISIONS 91 and 92.

STILL OPEN - VISIBLE CONTAINERS WITH NO LIVE READER

  These cannot be parked without changing what the player sees, so they are the user call, not mine:

    MovingParts       13094 parts  1807 tex  842 unions  no live driver; MovementController is dead
    ReactorCBLs        8609 parts  1644 tex  300 unions  pure scenery; CBLSystem never reads models
    Geometry           5695 parts  1525 tex  130 unions  367 SurfaceGuis
    GravitationShafts  2621 parts    12 tex  204 unions  102 point lights
    ChamberWalls       2267 parts   172 tex   26 unions

  CullFolder (21727 parts) is NOT on that list and must not be added. Workspace has no ControlRoom
  container at all, so the room the operator stands in is CullFolder.ControlRoom, and CullFolder is
  the live world.

  The five unloaded sector rooms are in ServerStorage.CulledParts and are absent from the world.
  Workspace.Facility.Rooms holds the corridors, connectors and gateways that lead to them but not
  the rooms themselves. Reviving room streaming is a design decision, not a cleanup.

DONE THIS PHASE
  [x] ReplicatedStorage.CulledParts -> ServerStorage   38869 parts out of client replication
  [x] Workspace.Reactor_Laser_Mk3_3 -> ServerStorage    2869 parts of rebuild residue
  [x] ORIGIN markers on both, nothing deleted, everything reversible in one reparent
  [x] Play-mode verification with zero real errors

DOC MIRROR REPAIRED, SAME STEP
  PROGRESS and DECISIONS each carried one extra final line holding nothing but a period.
  Neither disk mirror had it. It is a scar from the eaten-period repair recorded in
  DECISIONS 95 -- the lost period came back on its own line instead of at the end of its
  sentence. Removed from both modules; no disk write was needed, both mirrors were already
  right, and a lone period line renders as its own paragraph.

  THE MIRROR RULE, NOW GENERAL AND MEASURED. Take the ModuleScript Source, take the string
  body between the long-string brackets, strip the newlines at both ends and put exactly one
  back. That is the disk file, byte for byte, for all four docs. Nothing is fitted to the
  disk it is checked against: the search tried every head crop 0..6 against every tail crop
  0..6 and reported which crop reproduced the disk hash. CLAUDE.md stays longer
  than its module on purpose -- section 0.0 exists only on disk, and dropping the whole
  block, heading to heading, reproduces the module hash exactly. The size is not written
  down: section 0.0 is editable on disk, so a frozen figure rots the next time it improves.
  See DECISIONS 96.

## Phase 34 - Reactor core rebuilt: it was never rendering at all  [DONE]

THE CORE WAS NOT THERE, and that is a measurement rather than a complaint.
Workspace.Core.CORE is a 9^3 Neon part at Transparency 1.00, its PointLight ships
enabled=false, and all 97 ParticleEmitters, 53 Beams and 26 PointLights under
Workspace.Core are off. Within 35 studs of the core centre there are 0 enabled
glow-capable instances against 191 disabled.

WHAT THE OPERATOR WAS LOOKING AT -- the green glow, attributed at last. The column from
the operator's eye through the core was walked part by part to 205.40 studs, 165 hits.
The only green thing on it, OverHeatEffectPart (col 0,255,0), is Transparency 1.00, and
CORE itself is hit at t=100.40, also Transparency 1.00. The glow is the far chamber wall
(ChamberWalls...Walls.Part, col 205,205,205) at 205.40 studs, seen straight through an
invisible core, lifted by Bloom and tinted by the Atmosphere over that distance. So the
core drew nothing -- and the centre of frame was never empty, it was a hole onto a bright
wall. A header note in CoreKit claimed otherwise and has been corrected there.

CoreKit.Build() makes Workspace.CoreAssembly: 237 parts, 57 Neon, all Anchored, all with
CanCollide / CanTouch / CanQuery false. Pure pixels -- they cannot push a character, fire
a Touched event, or be found by a workspace raycast. Nothing was renamed, deleted, moved
or recoloured, and Workspace.Core still has 344 descendants. CoreKit.Remove() is the whole
undo: 127348 parts back to 127111, the exact pre-build number, and Probe reads the flag
restore back as 237 of 237.

INSTRUMENT CORRECTIONS, all three of them mine.
  GetPartsInPart is a bounding-box instrument. It reported 166 overlaps, among them a
  hollow chamber wall of 81.7 x 116.4 x 137.4 whose box comes within 6.61 studs of the
  core centre while its real surfaces stay far outside. Two hits were genuine; one of
  those, the laser barrel 2.56 studs out, is deliberate and now reads as the beam
  erupting from the core.
  A bounding-box distance cannot tell a hoop from a disc. It gave 0.00 studs for a frame
  whose interior is empty and 7.83 for a cylinder whose box corners are the only thing
  near, and the reach of 18.08 that fell out of it was a box corner -- a place no part
  occupies. Verify now prints counts and the farthest part CENTRE instead.
  THE WORST ONE: the first occlusion proof was a tautology. It found ray distances equal
  before and after the build on all 512 rays. That equality was guaranteed by
  CanQuery=false on the new parts, not by geometry, so the scan could not have failed.
  CoreKit.Probe() replaces it: it turns CanQuery on for the scan, restores it, and reads
  the restore count back out of the instances, so a leak reports as a number.

CoreKit.Probe(512): 204 rays land on the assembly, its surface lies 6.41 to 8.67 studs
from the centre, the nearest pre-existing surface is 2.56 studs out, closest approach to
the world 3.59, rays beyond the world 0, worst excess 0.

TWO VISUAL PASSES, both decided by looking at the render rather than by reasoning. Pass
one, 0.42 to 0.45 stud ribs with 6 meridians at phase 0 over an opaque body, photographed
as a fat pale barrel with one hoop and one bar through it. Pass two thickens the ribs to
0.62 and 0.72, cuts the body to 0.45 transparency over a white-hot heart at 0.46 of its
radius, lifts the cage steel off the near-black it was, and moves to 8 meridians offset by
half a gap.

WHY THE PHASE MATTERS, and it is not a matter of taste. At phase 0 the ribs at 0 and 180
degrees lie in the plane through the eye and the core, so both project onto one vertical
bar, while 90 and 270 collapse into the silhouette. A six-rib cage therefore reads as a
bar plus a circle -- from the one seat in the game that looks at this object along that
axis. Half a gap puts every rib on its own ellipse.

THE CORE NOW LIGHTS ITS CHAMBER. CORE carried a PointLight all along -- brightness 30,
range 60, colour (0,150,255), shadows on -- shipping disabled while no script in the place
touches it. CoreKit.Light(true) enables it at brightness 8 and remembers the authored
value, so Light(false) restores 30. This is the phase's highest-value change: a glowing
core that lit nothing is most of why the chamber read flat. The DECISIONS 52 red line
holds by measurement: nearest control-room part 101.0 studs, monitors 103.6, consoles
113.5, all outside the light's 60-stud range.

## Phase 35 - The core states its own condition, and a silent fault found on the way  [DONE]

THE CORE NOW DISCOLOURS BEFORE ANY GAUGE IS READ. CoreKit.Glow() rotates the hue of every Neon
part it made - 57 of them - from cyan toward violet as the reactor climbs its four core states,
and rotates the CORE point light with it so the thing lighting the chamber follows the thing
being lit. It is a pure observer: it reads GameState.Reactor.CoreState and writes nothing but
colour. No simulation value moves, no part is added, moved or renamed.

IT DID NOTHING AT ALL FOR A WHOLE SESSION, AND NOTHING ELSE BROKE. The driver was
`pcall(CoreKit.Glow, state)` at the tail of ControlVisuals.Update, and the module exported no
Glow at all. The edit that added the section had anchored on the string `return CoreKit`, whose
first occurrence in the file is inside `return CoreKit.Verify()` - Build()'s tail, line 391 - so
the entire section, function definition included, was written INSIDE Build()'s body. Glow
existed only while Build ran and went out of scope with its locals. pcall(nil, ...) then failed
quietly, every tick, forever. What made it expensive instead of obvious is that consoles, lamps,
levers and all seven monitors kept working perfectly: there was no symptom to chase, only an
absence.

THE FIX WAS A PURE RE-ORDER, GATED BEFORE IT WAS WRITTEN. Move lines 286-389 to just before the
file's real final `return CoreKit`, and refuse to write unless the byte count is unchanged and
every `function CoreKit.<name>` opens at depth 0. 28,895 bytes in, 28,895 out. The post-fix map
is Build 181 d=0, Remove 290 d=0, Verify 300 d=0, Probe 362 d=0, Light 440 d=0, Glow 524 d=0,
final depth 0. A fresh Instance.new('ModuleScript') carrying the current Source - the one oracle
here with no cached bytecode - then reported Glow as a function.

THE DRIVER WAS HARDENED, NOT JUST REPAIRED. pcall around a name that may not exist is exactly
what turned the fault into silence, so the name is now checked first and a missing Glow warns
once, loudly; the pcall is kept for what it is really for, because a throwing Glow must not take
the dispatch loop down with it. ControlVisuals.Update ends in driveCore().

MEASURED IN BOTH DIRECTIONS. Pinned to state 4 the core reads 100,25,122 x1 / 140,66,218 x30 /
171,64,232 x1 / 249,242,255 x1 / 77,27,114 x24 with the CORE light at 187,0,255; driven back to
ambient it returns to exactly the authored 26,78,122 / 28,92,114 / 64,178,232 / 66,192,218 /
242,252,255. Samples 0.3 s apart through the fade show intermediate colours, so the change is a
tween and not a snap. At severity 0 the core is byte-identical to the authored palette: the
observer touches nothing it observes. Both ends were also rendered from inside the chamber - the
cyan cage and the violet one - because a colour ramp is one of the few changes here that can be
settled by looking.

A GUARD EDITED WHILE PLAY RUNS IS NOT IN THE RUNNING SESSION. The first live run after adding
the hsvShift identity guard still read 26 -> 25 and 28 -> 27 on the red channel, and looked like
the guard had failed. It had not been loaded: the edit landed after that session started, so the
running module kept its old bytecode - CLAUDE 0.3 and 0.4, met again. A fresh Play start reads
the authored palette byte-exact, and the place was never wrong: edit mode held 26,78,122 and
28,92,114 with no attributes on any part, and holds them again now.

## Phase 36 - The monitors get their content, and one of them was never on  [DONE]

ART_DIRECTION 3.5 IS CLOSED. All seven control-room monitors now carry the dark navy backing and
the bright green title bar the spec asks for. That was the last open item in the monitor rebuild,
and it is the same edit as the verification debt section 3.5 recorded when the dark shell band was
first done with a Neon near-black as a workaround.

THE WORKAROUND AND THE SPEC TURNED OUT TO BE ONE OBJECT. Each monitor has exactly two Neon parts -
Screen and PowerNeon. Screen is the backing, authored Neon 17,17,17, and 17,17,17 is precisely the
"Neon near-black" the doc flagged for a second look once the palette went dark. So the spec's dark
backing and the recorded debt were never two jobs. Screen is now Neon 10,22,48: the same luminance,
spent on the blue channels instead of spread evenly, so the screen stays unambiguously dark and the
labels keep their contrast against it.

THE TITLE BAR IS SIZED TO THE FRAME, NOT TO THE TEXT, AND THAT WAS THE SECOND ATTEMPT. The first
pass padded a box around each monitor's TitleText, which is auto-sized, so the bar tracked the
*text* width. The seven monitors span two frame widths - 380 px on the four small screens, 1045 to
1220 px on Main, Power and Thermal - so one rule produced a near-full bar on the small desks and a
30 percent stub on the big ones. The second pass spans the frame and takes only its vertical extent
from the title. A stub green label was never what a title bar means, and the inconsistency between
the two families was the tell.

THE BAR IS ZINDEX 0 ON PURPOSE. Every readout in the frame sits above it, so whatever dims the
title - the Forecast desk's announcement pill at ZIndex 5, Main's SafetyFrame at 3 - dims the bar by
exactly as much. The bar can never occlude content and can never make a title less legible than it
already was.

A MONITOR THAT HAD NEVER BEEN ON. AlertsControlRoomMonitor ships with MainMonitorFrame.Visible
false, and nothing in the codebase ever sets it true. MonitorService writes all 27 of that frame's
lamps on every tick, and AlertsFrame is a child of that frame, so the lamps were being painted into
something nobody could see - and the new title bar was invisible there too, which is what made it
show up. This codebase already treats this exact class of authored false as a bug on the Forecast
panel and calls it one, so the same fix applies for the same reason. The frame is the monitor's
face; what gets hidden on purpose is a child state frame such as ShutdownFrame or ErrorFrame. The
monitor now reads REACTOR ALERTS over the full 3 by 9 lamp grid.

NOT TOUCHED, AND BOTH REASONS ARE MEASUREMENTS RATHER THAN CAUTION. PowerNeon 255,0,0 on every
monitor is the power lamp, not a band. And the nested CBL1Frame..CBL3Frame.TitleText on the Power
desk is rewritten every tick by MonitorService through cblStatusColor(), so a static recolour there
would be overwritten and do nothing while looking like it worked; the top-level TitleText that
MonitorService never writes is the one this pass owns. Finding that out required grepping for
TextColor3 rather than trusting the intuition that a title is a title.

VERIFIED IN BOTH DATAMODELS. Edit probe: navy 7/7, greenBar 7/7, fullWidth 7/7, knockedOut 7/7,
unsnapshotted 0/7, hiddenFrames 0/7. Screenshots of Main, Forecast, Power and Alerts under a
Scriptable camera. Then a Play session with MonitorService demonstrably ticking - TempLabel and
FluctuationLabel moving on the 1Hz cadence, temperature falling 454 to 61 F - after which the same
five counters still read 7/7 and all seven snapshot attributes still held the authored values. The
refresh loop does not fight this pass.

REVERT IS MonitorKit.Revert(). Every colour overwritten was snapshotted onto the instance first -
GameCoreAuthoredScreenColor on each Screen, GameCoreAuthoredTitleColor on each TitleText,
GameCoreAuthoredFrameVisible on each frame - so a revert restores the place exactly and a second
Apply cannot mistake our navy for the authored value. Same pattern CoreKit uses for the reactor
glow.

## Phase 37 - The Mk2 desks, measured against the originals instead of eyeballed  [DONE]

WHAT THE USER SAID. The Mk2 consoles are ugly; redo them. Nothing about the gameplay changes -
same six desks, same dot paths, same controls, same part names.

TWO THEORIES DIED BEFORE ONE SURVIVED, AND BOTH DEATHS ARE WORTH KEEPING.

  Theory 1, from a screenshot: the originals are warm brass-bodied and Mk2 is cool grey, so the
  body needs warming. Counted instead of eyeballed. ORIG_MainReactorConsole's 496 parts are
  dominated by near-neutral grey - 53 parts at rgb(125,124,126) Metal, then 16 at
  rgb(125,125,125), 16 at rgb(105,105,105), 34 light rgb(163,162,165) across Plastic and Metal,
  16 cyan rgb(128,187,219), 18 unlit rgb(17,17,17), 16 dark rgb(75,75,76), 8 at rgb(60,60,60).
  There is no brass body. The warmth is a brass band plus amber screens - small in area, both
  fully saturated, and human colour impression integrates saturation rather than area.

  Theory 2, from the same screenshot: then the tone is the problem and the body needs darkening.
  Already refuted by an A/B under the current grade and recorded in RebuildKit's palette header,
  so it is not tried a third time.

WHAT THE MEASUREMENT ACTUALLY SHOWED. Weighted by surface area, not by part count - part counts
are dragged around by hundreds of 0.19-stud chips. Share of total area:

    tone                  ORIG    before    after
    125,125,125 Metal     39.8%    25.1%     25.1%
     90,90,90  Metal       8.9%     0.0%     18.4%   (caveat below)
    197,143,78 brass      10.6%    15.7%     15.7%
    163,162,165 Plastic   10.2%    ~0%        9.7%
     50,50,50  Smooth     10.7%     8.9%      8.9%
     75,75,76  Metal       1.2%    10.8%      6.3%
      0,0,0    Metal       1.5%    15.7%      1.8%

FOUR PALETTE KEYS POINTED AT THE WRONG SURFACES, AND TWO HAD DRIFTED.

  hull and post had drifted from their own comments. Their recorded fractions, 0.490 and 0.392,
  ARE 125 and 100 over 255 - the values they used to hold. The colours had been darkened to 108
  and 86 without the comments following, and 108 is not on the original's ladder at all.
  Restored to 125 and 100. This also matches what ART_DIRECTION recorded the place measuring.

  Deck was "darker" (60,60,60). The original's working surface measures 3.50 x 0.25 x 15.00 at
  163,162,165 Plastic, full desk length - its largest single visible face. Mk2's largest surface
  was near-black. Now "light". A warning above the old value said running a bright strip across
  the deck turns the working surface into a white slab; that warning was about bright RAILS on a
  hull that was itself 108, where there is no value contrast anywhere. With the hull back at 125
  it no longer applies, and the comment now says why. RailNose moved "light" -> "lighter" in the
  same pass, or the nose would be invisible against a 163 deck.

  seamLine was "black". The original carries a 3.84 x 0.12 x 15.00 Metal slab at 90,90,90 along
  the top of its brass band - same place, same full length. Now "seam". EndCap was "dark"
  (75,75,76), nine times the original's share of that tone; now "seam".

CAVEAT ON THE 90,90,90 ROW. 18.4 percent against the original's 8.9 is NOT a real overshoot. The
metric counts every face, including the two large 4.04 x 14.90 faces of each 0.09-thick seam
strip that are pressed against the brass band and can never be seen. The visible part of a seam is
15 x 0.09. Chasing that figure down would mean deleting a seam the original also has.

THE FRONT WAS ALSO LITERALLY EMPTY, WHICH IS WHAT THE METRIC MISSED. Mk2's two louvre banks sit at
BODY_X1, 1.5 studs behind the deck edge, so the cantilevered deck hides them from every normal
viewing angle; and the middle 6 studs of cabinet were plain. The original's front is dense across
its whole width. Three additions:

  * a new perfPlate() helper - a grid of small proud chips - now runs across the cabinet front as
    two banks plus a centre field, and along the lip above the brass band.
  * BandHazard: 18 near-black bars standing proud of the brass, running its whole length. They used
    to exist only on the two end plates, which left the long front run of brass plain - and that
    is the run the operator looks at for a whole shift.
  * perfPlate's chips are "deep" (50,50,50 SmoothPlastic), NOT "unlit". The first version used
    unlit for contrast and the chips came out as solid black blocks: unlit is Neon, so hundreds of
    0.15-stud chips merge into one flat void at any normal viewing distance. 50 matte grey on a 125
    hull reads as perforation. Compared in screenshots before and after the swap.

RESULT. MainReactorConsole 220 -> 370 parts against the original's 496. All six, in the CONSOLES
order: 283/226/184/220/177/61 -> 433/376/334/370/327/61. HDEFGenerator is unchanged at 61 because
it does not go through buildShell, so it picked up no perfPlate - a known gap, not an oversight.

REINSTALLED AND VERIFIED BY COUNT, NOT BY EYE. All six rebuilt in place in Workspace.Consoles.
Bounding-box centre drift 0.000 on every desk and every axis. Every name CLAUDE section 6 lists as
binding-critical held its count exactly - 30 ClickParts, 21 LeverUnions and 39 NeonParts across the
six, identical before and after, 0 lever-owner differences. Neither the installed desks nor the
builders create ClickDetectors; ConsoleBinder creates them at runtime, which is why a rebuild
cannot strand a binding. Screenshots of the room and of an installed desk's front.

STILL OPEN. Mk2 is 6.09 studs deep in X against the original's 7.34 - intentional, and documented
in README ("no Mk2 desk is deeper than the desk it replaces"), but RebuildKit's own shell-dimension
comment claimed it reproduced the original's "7.3 x 6.15 x 15.0 envelope". That claim was never
measured and is false in X. Corrected in place, with the correction recording that it was false
rather than quietly deleting it.

## Phase 38 - The rebuilt desks pass their click test in a live session  [DONE]

WHY THIS PHASE EXISTS. CLAUDE section 1.4 rule 5 says a change is not finished until it is verified
for real. The Mk2 console rebuild had only been verified in Edit mode, by clicking a lever through
the command bar and diffing CFrames - which proves the GEOMETRY responds, not that the SHIPPED PATH
works. The shipped path is not a CFrame write: it is a ClickDetector, a server-side handler, a
ControlTrigger dispatch and a gameplay effect. This phase ran the whole thing in Play mode.

WHAT WAS READ, AND WHY IT WAS READ THAT WAY. Instance state only, never module state - CLAUDE
section 0.2, which exists because a command-bar require gets a fresh empty VM and reported
"temperature not running" three separate times on a reactor that was running fine. Every figure
below comes from a TextLabel on a monitor, a part's CFrame, or a line in the output log.

THE PROOF IS THE CONSOLE'S OWN LOG, WHICH IS STRONGER THAN A DIFF. Clicking the E-VENT levers on the
installed MainReactorConsole produced, in order:

    [Console] andypeng1NB pressed: E-VENT Lever 1 (MainReactorConsole)
    [Info]    E-VENT 1 fired: core cooled
    [Console] andypeng1NB pressed: E-VENT Lever 2 (MainReactorConsole)
    [Warning] E-VENT 2 already spent this shift

Two different physical controls, each named correctly BY THE GAME, each producing a different
gameplay outcome - and then the one-shot guard refusing a second use inside one shift, with its own
warning. A CFrame diff cannot show any of that: it shows that a part moved, not that the right part
moved or that anything downstream happened.

NO REACTOR RESET OCCURRED, AND THAT WAS CHECKED RATHER THAN ASSUMED. "The levers are back at rest"
reads like a reset. The monitors say otherwise:

    CORE TEMP  8 386 F      PRESSURE  7 215 PSI     OUTPUT  152 GW
    RADIATION  NOMINAL      HDEF      100 %          FLUCT   +36 F
    PEA STRESS 23 %         EXTRACT   50 %           STATE   FIRING

LEVER POSE AND LAMP COLOUR ARE COMPUTED AT RUNTIME, WHICH A LATER READ PROVED. During the session
E_VENTLever3 measured armed (r12 = -0.4695) with a lit NeonPart at 0.941, while the other three
measured at rest (r12 = +0.4695) with NeonParts at 0.086. Read again in the SAVED place after the
session stopped, all four levers read the identity rotation 1,0,0,0,1,0,0,0,1 and all four NeonParts
read 0.922 - a THIRD value, neither lit nor spent. So neither the pose nor the lamp is authored
state: both are written from GameState while the game runs, and stopping the session reverts them.
CONSEQUENCE FOR THE NEXT VERIFIER: lever pose can only be read from inside a Play session. Reading
it in Edit mode always returns rest, which is the false negative section 0.2 warns about wearing
different clothes.

A MEASUREMENT THAT COST AN HOUR AND PROVED NOTHING. The first attempt to read lever state sampled a
rotation-matrix component that is exactly 0.0000 in EVERY pose these levers take, so all four looked
identical in every state - including states that were provably different - and the diff reported all
four as CHANGED. The component that carries the swing is r12. Recorded as DECISIONS 113, because the
same family of wrong-component read had already produced a bogus all-CHANGED diff once before in
this project.

RESULT. Run from Edit mode through a full Play session and stopped cleanly. The desks are verified
end to end: detector, handler, dispatch, gameplay effect, and the one-shot guard.

## Phase 39 - The CBL lasers, second pass: a frame, not a new hull  [DONE]

WHAT THE USER SAID. "CBL再二次重做一下，游戏本身玩法必须保持不变" - give the CBL lasers a second
rebuild pass, and the gameplay must not change. It came in the same breath as the rebuild of
everything else, and right after the consoles were called ugly, so the target is the thing a first
pass could not reach.

WHY THE FIRST PASS COULD NOT FINISH THE JOB. LaserKit fixed the COLOUR and left the SHAPE LANGUAGE
alone. The machine measured before that pass as sixteen desaturated greys - the largest, 99,98,100,
on 816 parts - with no emissive accent anywhere, so it read as a pale tube in a dark hall. LaserKit
repainted it and added ring collars, seam rings, cyan inlays, status lamps and a muzzle glow ring.
What it did not change is that the machine is a long ROUND barrel carrying round ring collars, while
every console in the control room is a rectangular, bevelled, brass-banded Mk2 desk. That mismatch is
what the operator pointed at, and a recolour cannot touch it.

WHY A FRAME AND NOT A NEW HULL. The barrels are authored: about 2,655 opaque hull parts per laser,
which the README breaks down as 210 MeshParts, 100 UnionOperations, 485 Wedges and 251 live
Texture/Decal children. CLAUDE section 1.4 forbids removing a feature without a replacement, and
there is no procedural replacement for an authored mesh. A new hull could therefore only be built by
covering the old one - and a plain box in front of a detailed machine is a worse silhouette, not a
better one. The frame is additive: the machine still shows through the bays, and the rectangular read
comes from the ribs, rails and ducting around it. Revert is one folder deletion per laser.

WHAT IT BUILDS. Rebuild.LaserFrame, 125 parts per laser, all new, all under a folder named Mk2Frame:

    56  rib plates, 7 octagonal stations at their +8, +1, -8, -13, -26, -34, -46
    28  brass bolt heads, 4 per rib at the cardinal angles
     8  flank rails, 2 per bay across 4 bays
     8  ducting runs, top and bottom of each of those bays
     8  service strips, one cyan Neon run per bay per face
    16  hazard bars, a lit and a dark bar at each diagonal of the two end ribs
     1  brass title plate reading CBL-1 / CBL-2 / CBL-3

The coil at their x=-20 is the widest station on the machine by a factor of two - 12.7 studs against
5 to 7 everywhere else - so the two ribs either side BRACKET it rather than straddling it, and that
bay carries no rail: a straight line there would need radius 14 and would read as a hoop rather than
a rail. The bay between ribs 1 and 2 is open for the same reason, because the flange at x=+4 fills
it. Both are left visible on purpose, and the bay test ENFORCES that rather than trusting the
comment: it casts the mid-span silhouette and refuses any bay whose middle bulges more than 1.00 stud
past its ends.

EVERY RADIUS IS CAST. Rib corners sit 1.70 studs outside the machine's measured surface, measured with
LaserKit's own SurfaceScanner - the same instrument the first pass used, and for the same reason,
because a numeric profile of part CENTRES is the wrong question here and gave two straight wrong
answers in Phase 23. The cast radii came back as ribs 1 to 6 on the 8.40 floor and rib 7 at 10.52, so
the frame follows a barrel whose true radius runs from 4.1 to 8.8.

THE 16-POINT SWEEP WAS NOT DECORATION. The first version swept 8 angles, which are exactly the angles
the rib plate CENTRES sit on - the least demanding case, since each plate spans about 22.9 degrees
either side of its centre. Rib 7 measured 9.78 under that sweep and 10.52 under a 16-point sweep: the
vent bulge that would have clipped it sits at a 22.5-degree offset, precisely between the old
samples. LaserKit's own ringRadius already swept 16 for this reason. Recorded as DECISIONS 109.

COLOUR VERIFIED BY READ, NOT BY EYE. A dark-hall screenshot makes the frame look cyan-dominant, and
that reading is wrong: the plates are the exact Mk2 greys 68,69,74 and 92,93,98 in CorrodedMetal with
the ReactorWallPlate variant, bolts 197,143,78 Metal, rails and ducts 46,47,51, and only the service
strips are Neon. What reads as cyan is those strips plus the machine's own emitter glow behind the ribs.

RESULT. All three built and verified by count: 125 parts, 4 PointLights and 1 SurfaceGui each,
identical across Mk3_1/2/3. Two screenshots, one close and one wide. Gameplay untouched: no part
renamed, deleted or moved, no ClickDetector created, no name from CLAUDE section 6 touched, and the
frame is decoration only - CanCollide, CanQuery and CanTouch all false.

STILL OPEN. Mk3_2 and Mk3_3 each carry 8 more descendants than Mk3_1 before the frames are counted.
Not investigated, and not this phase's doing: each laser has exactly 125 frame parts.

## Phase 40 - The six desks get raked registers, and the controls were leaning at double  [DONE]

Scope, from the user's instruction: after the CBL lasers' second pass, redo the consoles - including the
coolant calibration - then continue. The Mk2 desks were called ugly, and Main was the flattest of the
six: the other four carry raked control surfaces while Main laid its whole control row on the deck.

WHAT WAS MEASURED BEFORE ANYTHING WAS WRITTEN. ORIG_MainReactorConsole carries 113 parts at exactly
20.00 degrees about Z, and they run the desk's full 15-stud length. That is the original's idiom, and
it is what the eye reads as missing when the six desks are seen together. Deliberately NOT copied: a
full-deck rake. 4.10 studs of deck at 20 degrees rises 1.49 and drives into the instrument face at
Y 3.96, so on this desk the rake is a REGISTER - 1.55 deep, hinged at the deck's front edge, rising
0.56.

WHAT IT BUILDS. Three layers in BuildMainReactorConsole - RegPlate / RegRim / RegWell at +0.11 / +0.21
/ +0.25 over the rake line, the same stack deckModule lays for the other four desks - plus RegSkirt
closing the wedge behind the plate and a two-tone hazard bar along the front rim. The three layers are
INLINED rather than calling deckModule, which builds exactly that stack for the other four: deckModule
is declared further down the same chunk, so a call from here would resolve to nothing at all, and
inlining three parts is cheaper than reordering three shared builders that four other desks depend on.

The controls are then remounted in ONE pass over a table of seven (name, z) pairs, rather than teaching
buildLever / buildBigLever / buildButton / buildKeypad about rakes: those four also serve CBL, Electric,
Thermal and ALT, each at its own register depth, and four rake arguments would be four chances to
arrive at four different answers. The mount is a rigid re-expression - with A the deck point under a
control and P the register point above it, each part's new pose is P * (A^-1 * pose) - so every
assembly lands square on the slope, base flush and handle normal to the register. That is what the
original does with its own controls, its button axes measuring (0.34, 0.94, 0.00).

Tilting the levers is safe, and not by assumption: ControlVisuals captures both the hinge and the rest
pose FROM the part's CFrame at bind time and writes every swing as hinge * Angles(angle) *
inverse(hinge) * base, so a lever whose rest pose is already raked swings in the register's own frame.

THE DEFECT, AND HOW IT WAS FOUND. The first version wrote P * REG_ROT * (A^-1 * pose). P already
carries REG_ROT, so the rake was applied twice. It installed cleanly, passed a height check against an
independent baseline, resolved all seven dot paths, and looked plausible in a screenshot. What caught
it was measuring the angle: RegPlate read 20.00 degrees off vertical and EVERY control read 40.00, with
the buttons' flat-laid collars at 50.00 - which is 90 minus 40. The register was right and the controls
leaned at double. Fixed by dropping the second rotation and taking P on the register's own top surface,
from the plate's own numbers rather than a second copy of the rake arithmetic. Re-measured after:
every control part at 20.00 or 70.00, the 70.00 parts being cylinders whose AXIS measures 0.020 degrees
off the register normal. Recorded as DECISIONS 117.

Also fixed this phase, carried over from the CBL desk: rakeY returns an ABSOLUTE deck height, and the
CBL pressure pad fed it into a +Y translation as a delta, flying the pad 4.20 studs up and putting that
desk 2.03 studs over its riser. Now rakeY(X, frontX) - DECK_TOP.

ACCEPTANCE. MainReactorConsole: height 6.250 against the independent MK2PREV_MainReactorConsole_preBar
baseline, top at 282.833, seven dot paths resolving, no part at the 40.00 or 50.00 signature, and lever
base plates clearing the register's top face by exactly +0.0100 studs - the hundredth that stops a 0.22
base plate and a 0.22 register plate speckling into one another's plane. Two screenshots: the register
reads as a solid riser with the controls standing normal to it, matching the other four desks.

COOLANT CALIBRATION. ConsoleBinder binds coolant_recalibrate to ThermalConsole.CoolantControl<i>.BigLever,
whose LeverUnion sits at 20.00 on the raked register like every other control. It had no lamp state at
all, so applyLamp returned early and the lamp sat on its authored colour forever - a dead prop. It now
follows the atmosphere_vent branch exactly: spent while CoolantSystem's 30-second cooldown runs, ready
after. No STATES entry, deliberately - see DECISIONS 121.

HDEFGenerator was left alone on purpose. It is 4.65 x 7.38 x 1.38 - a cabinet, not a desk - with its own
frame carcass, glazed cell window, three power cells and brass cap band. A raked register is the desk
family's idiom, and bolting one onto a cabinet would be the style mismatch this pass exists to remove.

VERIFICATION, AND ITS LIMIT. The lamp branch was tested by extracting the shipped lampState text out of
the live module and running it against ten cases - 10 passed, 0 failed - including the 30-second
boundary, per-pump isolation, and the existing atmosphere_vent branches as a regression check. See
DECISIONS 118 for why the extracted text and not a retyped copy.

What could NOT be done is the simulated click. Workspace.StreamingEnabled is true and the place has one
SpawnLocation at (233, 402.9, 1370) - about 1400 studs from the control room and 120 studs below it - so
a playtest client has neither the console geometry nor a path to it: the client's Consoles folder held
97 descendants against thousands on the server, and ThermalConsole 42 against 651. A real click test
therefore also needs a spawn near the desks. The click bindings here are verified by dot-path resolution
and by the ClickParts' CanQuery, NOT by a mouse. Recorded so the next session does not read this as a
click-tested phase.

STILL OPEN. ServerStorage.Mk2Pass1 holds two superseded Main builds (PASS2TMP_MainReactorConsole and
PASS2FLAT_MainReactorConsole) and Mk2Stage holds NEW_MainReactorConsole; all three should be cleaned up
BY IDENTITY, never by index - see DECISIONS 119.

## Phase 41 - The documentation hit the engine's own ceiling  [DONE]

Scope: close out the section 0.0 step for Phase 40. It turned into a structural change.

The disk halves landed first -- PROGRESS +6208 bytes, DECISIONS +12717 for entries 115-123 -- and then
writing DECISIONS into its ModuleScript was REFUSED outright: Source is capped at 200000 bytes and the
image is 202893. For the first time in this project the divergence ran the other way, with the DISK
ahead and the MODULE stale, and no amount of care would have made it fit. This is not the 40.0K
CLAUDE.md warning, which was a soft context-budget complaint about a perfectly representable file.

DECISIONS is now two modules, cut at ENTRY 75:

    DECISIONS    103355 bytes  roll 2e994db6   entries 1..74
    DECISIONS_2  102387 bytes  roll 191bd85e   entries 75..123

The boundary is an entry number, not a byte offset, so it is a fact about the document rather than
about its length on the day it was cut -- the same reasoning the CLAUDE.md split used when it ordered
itself by section number. verify_docs.py now checks each file against its own module AND asserts the
seam: part 1 must end at 74, part 2 must run contiguously from 75. Two hashes alone would not have
said where the cut was.

The two module halves were built INSIDE Studio, from the module's own existing text plus the new
blocks, and deliberately never transmitted. DECISIONS.md contains two backslashes, both in early
entries quoting Lua code, and section 0.10's escape decoding would have turned them into real
newlines on the way in. The splitter reports which parts carry backslashes so the writer knows which
ones must be moved rather than sent. That is a constraint on the write path, not a defect in the
document, and it is now written down as one.

PROGRESS is at 140880 of the same 200000 -- roughly five phases of headroom at this phase's 12.7K.
Recorded so the next session watches it instead of discovering it the way this one did.

Also updated: README (the module list plus why DECISIONS is two), section 0.0's mapping table, and
docs/TODO.md section 3 -- the console second pass checked off, with new entries for the
StreamingEnabled/spawn finding and for the Source ceiling. verify_docs.py is rc=0 against all five
modules.

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

## Phase 43 - The facility is one skin again  [DONE]

Scope: appearance only. `PaletteKit` (new module, Rebuild) writes Color, Material and MaterialVariant
and nothing else. No part is created, renamed, moved or destroyed, so nothing in the CLAUDE 6 binding
table can be affected, and no gameplay mechanic changed.

WHAT WAS WRONG. Workspace held 129,578 BaseParts in 20 Material/Variant combos, and the two largest
differed in BASE MATERIAL at nearly equal size: Metal/FacilitySteelPanel 49,316 (38.1%) and
CorrodedMetal/ReactorWallPlate 47,167 (36.4%). Two skins over one ladder of tones. The Mk2 desks were
then built on a third skin (SmoothPlastic, body 50,50,50), so the rebuilt area matched neither half it
stood between. That is the operator's "the front and the back look different".

WHY THE MATERIAL IS THE WHOLE STORY, MEASURED RATHER THAN INFERRED. All three project
MaterialVariants carry NO ColorMap:

    FacilitySteelPanel   base=Metal          colorMap=(none)  studs=10
    ReactorWallPlate     base=CorrodedMetal  colorMap=(none)  studs=10
    FacilityFloorPlate   base=DiamondPlate   colorMap=(none)  studs=10

A variant with no ColorMap is a rename of its base material. What the player sees is therefore the
STOCK texture multiplied by the part Color, and nothing was overriding the rust.

WHAT WAS WRITTEN. 53,029 parts: 47,166 rust parts retired onto FacilitySteelPanel, plus 5,863
near-grey structural parts above luminance 120 pulled down to 100,100,100 - ShellKit's own threshold
and target, so the two kits agree by construction. Three classes were exempt, each measured rather
than assumed: lamps (1), content (5,218 - TextPart/FloorTextPart/Line at lum 248, plus anything
carrying a Decal or a Texture) and hue (10,103 - brass 194,150,68, hazard yellow 190,149,0, coolant
blue 110,153,202, violet 134,102,202 and the rest, which is the facility's coding). Floors keep
FacilityFloorPlate.

REVERSIBLE BY RECEIPT. Color, Material and MaterialVariant go into attribute PaletteKitOrigin before
the first write, so RestoreAll() is exact; 53,029 receipts were recorded during the run.
RestretchChunk exists because a single non-yielding pass over 96,483 parts freezes Studio - it slices
the work and is resumable without a cursor, because a part that already matches the palette falls out
of the pending set by itself.

THE FIRST APPLIED RESULT HAD A DEFECT, AND THE RENDER FOUND IT. The first rules retired rust even
under artwork, on a written claim that "a Decal is unaffected by the material underneath it". A
same-camera capture of the coolant deck showed CoolantReserviors.C1.Union - 178 by 1 by 80, carrying
a Texture - go from dark olive to BRIGHT YELLOW. A Texture tiles with transparency and composites
WITH the base material, so the skin shows through it. The claim was false, and RestoreFaced() put
back exactly the parts carrying authored artwork: 1,555 of them.

WHY 1,555 AND NOT 1,307. A child-count census had predicted 1,307 (858 with a Texture plus 449 with a
Decal). RestoreFaced selects with the SAME isContent() predicate the rule calls, and that predicate
also matches by NAME - 248 structural parts are named TextPart or Line. Using the rule's own
predicate is what makes the number trustworthy; a second hand-rolled test would have been a second
thing to be wrong. See DECISIONS 126.

VERIFIED BY READING INSTANCES, NOT THE RETURN VALUE. Census after: Metal/FacilitySteelPanel 96,482
from 49,316; ReactorWallPlate 1,556 = the 1,555 restored plus GravatronUnit.LightPart, which is a
lamp and was never touched. Receipts remaining 51,474 = 53,029 - 1,555. The exempt classes read
unchanged: TextPart still 248,248,248, Line still 163,162,165, ClickPart still 239,184,56, Neon still
7,424, Plastic plus SmoothPlastic still 12,030.

THE VISIBLE RESULT. Matched-camera captures from (180,320,80) toward the chamber walls: pale,
washed-out grey before, dark steel after - the Mk2 direction. The control-room deck, which is the
reference area and was already correct, is identical in both, which is the cross-check that the
rules did not disturb what was already right.

A PROBE THAT READ THE WRONG PART. The first verification pass reported C1.Union as DiamondPlate with
no children, contradicting the plate that had just been diagnosed. C1 has more than one child named
Union and FindFirstChild returns the first; the child count was the tell. Identity, not path - the
rule from DECISIONS 119, re-learned on a READ instead of a delete. See DECISIONS 127.

STILL OPEN. The per-unit parking of the original facility into ServerStorage is untouched by this
phase: PaletteKit changes appearance in place and moves nothing.

## Phase 44 - The first unit is parked, and the warning is the ledger  [DONE]

Scope: data. One model changed parent and name; nothing inside it was created, renamed, deleted or
altered, so no gameplay mechanic moved and no name in the CLAUDE 6 binding table is involved.

WHAT MOVED. Workspace.MedicalDispenser -> ServerStorage.GameCoreBaseline.Originals_facility,
renamed ORIG_MedicalDispenser. 483 BaseParts, 625 descendants, ExtentsSize 7.1 by 11.8 by 5.8,
pivot 249.039581, 281.426758, 52.893997.

WHY THIS UNIT WAS THE PILOT, MEASURED RATHER THAN ASSUMED. The operator picked it on the strength
of a reference graph of one line. That claim was then tested two more ways. First, the sole
executable hit is FacilityBridge:24, a ROOT_MAP entry, and nothing anywhere reads
FacilityBridge.Resolved.MedicalDispenser - the bridge's only consumers are CacheLights (RoomLights,
Lights) and CacheAlarmSounds (Alarms), and FacilityBridge.Get is called by no one. Second, the
unit's only trigger host, TriggerPart, appears in ZERO scripts, and the sole live Touched:Connect
in the project is GatewaySystem:51 bound to one named box, not a workspace sweep. So in this build
the medical station is decorative: it renders and nothing drives it.

THE LEDGER IS COPIED, NOT INVENTED. Four attributes, in the format the shipped entries already use:

    GameCoreParkedName     string   MedicalDispenser
    GameCoreParkedFrom     string   Workspace.MedicalDispenser
    GameCoreParkedPivot    CFrame   249.039581, 281.426758, 52.8939972, 1, 0, 0, 0, 1, 0, 0, 0, 1
    GameCoreArchivedFrom   string   ServerStorage.GameCoreBaseline.Originals_facility

GameCoreArchivedFrom names the BAY, not the source. Both shipped examples settle it:
ORIG_MainReactorConsole carries ParkedFrom = Workspace.Consoles.MainReactorConsole and
ArchivedFrom = Workspace.Rebuild.Originals. Writing the source path there would have duplicated
ParkedFrom and carried no information - a field that looks populated and says nothing.

WHY A NEW GROUP. GameCoreBaseline held three: Originals_consoles_and_monitors, ReactorCBLs_original
and Superseded_Mk2_preLEDBar. None of them is a home for a standalone facility unit, so
Originals_facility was created. Note that RebuildKit.PlaceReference probes only
Originals_consoles_and_monitors and Originals by name, so Originals_facility is NOT yet visible to
that helper - registering it belongs to the install machinery that does not exist yet, and saying
otherwise would be a convention nothing reads.

VERIFIED BY READING INSTANCES BACK. Before and after: parts 483, descendants 625, pivot delta
0.000000 studs. Workspace no longer holds the name; the parked node is at
ServerStorage.GameCoreBaseline.Originals_facility.ORIG_MedicalDispenser with all four attributes
present and typed as listed above.

VERIFIED BY PLAYTEST, NOT BY READING THE CODE. Workspace.GameCoreTests.GameCoreSelfTest was run
with the model already parked. It reports finalStatus PASS, ok true, and bridgeResolved 17. The map
holds 18 entries and 17 of those names exist in Workspace, so the before value was 18: the count
dropped by exactly the one unit parked, and the whole system chain still runs. The log carries
exactly one new line, [FacilityBridge] missing workspace model: MedicalDispenser. The 118 error
lines are the known sound-authorization spam and none of them is new.

THE ONE WARNING IS THE POINT, NOT NOISE. Parking a mapped unit makes the bridge warn once per boot,
and the tempting fix is to let it fall back to the archive. That would be worse than the warning:
for the units whose descendants the bridge actually drives - RoomLights, Lights, Alarms - a
fallback would hand back a ServerStorage instance, and Light.Enabled or Sound:Play on it would
succeed and do nothing. That is the silent failure CLAUDE 0.13 names, and it would be
indistinguishable from success. The warning is emitted exactly while a parked unit has no Mk2 at its
old path, and it clears itself when the Mk2 is installed under the original's own name - which is
the pairing the operator asked for. The warning is the ledger.

STILL OPEN. No Mk2 exists for this unit, so the world is one medical station poorer until one is
built, and nothing on the bench or in RebuildKit supplies it. The remaining units are untouched.
And a repeatable install still does not exist: MK2PREV_, GameCoreBench and Install each appear ZERO
times in RebuildKit's 1796 lines, so the superseded-Mk2 archive and the install step were both done
by one-off scripts.

## Phase 45 - The leg the player sees, and the throw is per family rather than one number  [DONE]

Scope: the lever feedback path and the lever geometry it drives. No engine value was changed and no
part was created, renamed or destroyed; what changed is which writer owns `LeverUnion.CFrame` and
`NeonPart.Color`, and how far a lever is drawn from its stop. The full note is
`_tools/_attic/apply/_phase45_lever_feedback.md`, 12903 bytes; this is the narrative.

PROVING A CLICK WAS ACCEPTED IS NOT PROVING THE PLAYER SAW ANYTHING. The complaint was that a click
with no feedback animation accomplishes nothing, and it was correct: the server was moving the levers
and the client was not showing it.

THE SECOND WRITER. `StarterPlayer.StarterPlayerScripts.VisualFeedback` - a 148-line LocalScript with
`Disabled = false` - wrote `LeverUnion.CFrame` and `NeonPart.Color` on every Heartbeat from
`workspace.Stats`. It was a second writer of the exact parts the server module owns, and it won,
because a client-side write is not overwritten until the server next changes that property.

Measured at one instant, both sides: the client held `ThermalConsole.CFLever1.LeverUnion` at
`155.540, 262.269, -28.231` while the server held `110.157, 279.370, -16.070`. The difference is
`|delta| = 50.000` along the union's own LookVector, because `Config.Visual.LeverArcDegrees` is `50`
and was being read as a stud distance - the variable in that script even carried the comment
`-- repurposed as travel distance in studs`. Six fan levers stood 50 studs off their consoles. And the
C-Pump 3 lever sat pinned at its authored CFrame on the client while the server held it 0.8 studs out,
so a lever that had just been clicked appeared not to move at all.

THE FIX IS A DISABLE RATHER THAN A DELETE. `Disabled = true` was written in Edit mode, because a change
made during a playtest is discarded when that playtest stops. A header was added recording the
supersession, so the file stays as the record of the client-side approach. Nothing is lost by turning
it off: the server module covers every lever and lamp this one touched and several it did not, and a
server CFrame write reaches a client when the part streams in, so StreamingEnabled is not a reason to
keep a client copy. What the client does lose is a 23-lever plus lamp write loop on every frame.

THE SINGLE-WRITER PROPERTY IS NOW MEASURED, NOT ASSERTED. A scan of all 126 scripts finds exactly two
that mention `LeverUnion` - the disabled LocalScript and `ReactorBackend.VisualFeedback` - and three
that mention `NeonPart`, those two plus `ServerStorage.Data.DataCollection`, which is in ServerStorage
and therefore never runs. One live writer.

VERIFIED LIVE, BOTH HALVES. Position: a real click on
`Consoles.ThermalConsole.CoolantControl1.PW2ClickPart`, label `C-PUMP SWITCH 1 - LEVEL 2`, logged
`[ReactorBackend][Control] andypeng1NB -> C-PUMP SWITCH 1 - LEVEL 2`; the union moved `|delta| 0.79994`,
exactly `throwDistance(2, 3)`, along its own LookVector, and `CoolantControl2` and `CoolantControl3`
did not move. The client read the same position to the last float. Colour: a real click on
`Consoles.ThermalConsole.CFLever1.ClickPart` slid the union 1.600 studs back to its authored CFrame and
took `CFLever1.OfflineLight.NeonPart` from `0.176471, 0.176471, 0.176471` to
`1, 0.27451, 0.156863`, the Fault red, with `CFLever2` and `CFLever3` unchanged in position and colour
at both ends. Server and client agreed on all six values byte for byte.

NOT A DEFECT: THE C-PUMP LEVEL LAMPS ARE DARK UNTIL THE PUMP IS SWITCHED ON. Clicking
`C-PUMP SWITCH 1 - LEVEL 2` alone leaves `CoolantControl1.Light1` to `Light3` at the off grey, and that
is correct - the module gates them on `pump.enabled`, not on `pump.level`, which is the stated rule
that the lever carries the selection and the lamps carry the effective contribution. Reading three dark
lamps as a broken lamp writer is the mistake this note exists to prevent.

THE RESTING POSE: THREE FAMILIES LEGITIMATELY REST DISPLACED. `Engine:Reset` boots `fans = true`,
`cbl.level = 2` and `extraction = 2`, while the authored geometry is the level-1 or off pose. So before
the player touches anything, six fan levers rest 1.600 studs out, three CBL levers 0.400 and the
extraction lever 0.533. Nothing was changed for this. The lever is showing the engine's own state and
the engine's own initial values are the authority. That "authored means off" is also not an assumption:
`StartUpBigLever`'s `ShutClickPart` sits at the authored position and its `StartClickPart` is +1.663
along the LookVector, so the authored stop is Shut and the throw runs along +LookVector.

LeverUnion IS 29, NOT 23. Six of the 29 are `CRC1/2/3.ProcessorInterior.CalibrationConsole.PECLever1`
and `PECLever2` inside the QPUs. They sit outside `Workspace.Consoles` and carry no ClickDetector, so
they are not player controls, and the lever table correctly excludes them. A count of 23 was a count of
console levers, not of parts named LeverUnion.

THE THROW WAS ONE NUMBER FOR FOUR FAMILIES. `THROW_TRAVEL = 1.6` was applied to all 23 console levers,
and the motion was `CFrame.Angles` about a marker rather than a slide. Both came from
`MovingParts.DecayFields`: the eleven `LeverModel` rigs there carry 0.500 studs plus 60 degrees, and
every one of them is an AirlockConsole or GatewayConsole door bar. Not one is a console lever.

`ReplicatedStorage.Levers` IS THE AUTHORITY. Four families parked at the world origin, 733
descendants: `2Level`, `3Level`, `5Level`, `SmallLever`. It is the builder's own template library, and
the only source that says anything about the four controls whose consoles carry no per-level target at
all. Measured: `SmallLever.Up` union x 88.225, `SmallLever.Down` union x 88.925, so the throw is 0.700;
`ClickPart` x 88.475 in both copies, which is the fact the sign rule falls out of. `2Level` ships as
Up/Down copies whose click targets are named `Shut` (-0.023) and `Start` (+1.663). `3Level.Level1/2/3`
unions at 88.012 / 88.812 / 89.612, step 0.800, span 1.600, with `LeverOrginPart` constant at 88.012 -
so it is the fixed level-1 origin marker, and neither a pivot nor a duplicate of the union. Twelve live
levers wear the SmallLever rig: six `CFLever`, three `E_VENTLever`, `ShuttersLever` and the two `MASS`
`PowerLever`s. All were being thrown 1.600, which is 2.29x the authored distance.

THE ARGUMENT THAT NEEDS NO SEMANTIC. For the CFLever rigs the old code drew the union at
`U0 + 1.600 LV`. That rig's authored stops are `U0 - 0.658 LV` and `U0 + 0.042 LV`. 1.600 is not
between them, so a running fan was drawn at a pose the art does not contain. The same reading retires
the apparent fans-against-shutters contradiction - both authored on Down, opposite engine levels -
without inventing a semantic for either.

THE SIGN RULE. `ClickPart` is fixed and only the union slides, so moving the union by delta moves
`d = (ClickPart.Position - union.Position) . LookVector` by minus delta. The throw from the stop a rig
sits on to the other stop is `d` minus that other stop's own offset: +0.700 for a rig authored on Up,
-0.700 for one authored on Down. Reading each rig's own `d` lands a rig parked off its stop exactly on
both - the CFLevers read -0.408, which is 0.042 short of Down, so their throw is -0.658 and they finish
on the Up stop rather than 0.042 past it. Live, all twelve: `E_VENTLever1-3` +0.250,
`MASS1-2.PowerLever` +0.248, `ShuttersLever` -0.450, `CFLever1-6` -0.408. Five authored on Up and seven
on Down, and that is not derivable from the engine's levels, because the fans and the shutters are both
authored on Down with opposite engine levels.

THE CLICK RIG HAS THREE GATES, NOT ONE. `ClickDetector.MaxActivationDistance = 6` gates on the distance
from the character to the detector, not on the mouse ray, so a raycast reporting `Mouse.Target == the
ClickPart` while the character stands 1397 studs away in the gateway room is a correctly rejected
click. `StreamingEnabled` leaves the console off the client entirely (`CFLever1.ClickPart` resolved to
NIL), and `RequestStreamAroundAsync` fixes visibility and not the range gate. And the camera must be
held rather than set - `BindToRenderStep(name, Enum.RenderPriority.Camera.Value + 1, fn)` - because the
wrapper's post-call `CameraType` reset can land between press and release and re-aim the ray mid-click.
Satisfying one or two of the three produces a click that silently does nothing.

VERIFIED THREE WAYS. An Edit-mode sweep of all 21 levers at both endpoints reported
`failures=0 restoreFailures=0`, every small-family lever landing ON-STOP within 0.002 studs, and the
place restored byte-identically from a snapshot taken before the sweep. Live server: `fan1/2/6` +0.250,
`vent1/2` +0.250, `mass1` +0.248, `shutters` -0.450 - and the engine boots `fans = true`, so the fans
sit on the Up stop, where the old constant would have read -2.008. A real click on `CFLever1.ClickPart`:
`d` +0.250 -> -0.408 -> +0.250, `OfflineLight` grey -> fault red -> grey, server and client agreeing to
the last float and `CFLever2` never moving.

A NOTE THAT RECORDED A FIX IT DID NOT MAKE. An earlier version of this note said the stale paragraph in
`ServerStorage.Data.BackendRewritePlan` had been "corrected in place". That was false. It still read
that the backend folder is `ServerScriptService.ReferenceContent` and that
`ServerScriptService.ReactorBackend` "does not exist", at a moment when every read of the live DataModel
was resolving `ReactorBackend` successfully. It is corrected now, in the same change as this phase. The
lesson is narrow: a note that records a fix it did not make is worse than no note, because it stops the
next reader from checking.

RIG FINDINGS WORTH CARRYING. The +58 px y offset applies to the official input tool, not only the
third-party one. The viewport resized between tool calls inside one session - 574x227 first, 1020x480
later - so the pixel must be recomputed per call rather than cached, and a stale pair of numbers aims at
nothing. One tool click sequence produced two MouseClick events on two adjacent ClickParts, because the
wrapper resets the camera after the call and a click whose press and release straddle that reset has
its ray re-aimed; the mitigation is to issue the press and the release as one atomic `mouseButtonClick`
with no intervening wait, and to prefer a control that has a single ClickPart.

## Phase 46 - The thirteen lamps are proven, and Initialize was not idempotent  [DONE]

Scope: the lamp matrix and one server-side probe. No engine value was changed and no geometry was
touched. The probe is kept as a re-runnable instrument in `ServerScriptService.MCP_LampProbe`. The long
form is in `docs/airemake/PROGRESS.md` and `docs/airemake/REWRITE_STATUS.md`.

THE THIRTEEN LAMPS CARRIED AS UNPROVEN ARE PROVEN, 38 OF 38. The families are `shutter`, `mute`,
`atmo`, `vent1-3`, the two gravatron lamps, `sam1-2` and the three CBL pressure buttons.

THEY WERE UNPROVEN BECAUSE THE PROBE WAS WRONG, NOT BECAUSE THE LAMPS WERE. The probe is a Server
Script, and Server Scripts start in an undefined order: it lost a race with Runtime, ran
`VisualFeedback.Refresh` against a module whose `levers` and `lamps` tables were still empty, and so
measured a module that touched nothing. Every `poseLever` and `lightLamp` returns early when its key is
absent, so the probe read each part's authored colour, constant across every case - exactly what a
broken lamp looks like. Every start-up comparison read `delta 0.0000` for the same reason; five of them
counted as passes because nothing had moved, and the sixth, `starting != cold`, as a failure.

THE CASE THAT PASSES IS THE TELL, NOT THE CASE THAT FAILS. Only seven of the thirty-eight cases passed,
and the two colour cases that passed are what named the fault rather than hiding it: `atmo while
running` and `cbl1 nominal` both read `Nominal`, because
`MainReactorConsole.AtmosphereVentButton.NeonPart` and `CBL1-3Systems.PressureButton.NeonPart` are
authored `(137,255,147)` and `Config.Visual.Nominal` was measured off them. A lamp cannot read a palette
entry by accident unless nothing painted it. A failure uniform across every case is a property of the
instrument, not of the subject.

WHAT IS PROVEN, FAMILY BY FAMILY. `shutterLamp` closed to `Amber`, open to `Off`. `muteLamp` off to
`Off`, on to `Fault`. `atmoLamp` cold to `Off`, running to `Nominal`, inside its own cooldown back to
`Off`. `vent1-3Lamp` unused to `Off`, spent to `Fault`. `cbl1-3Lamp` `Off` while inactive, `Nominal`,
`Yellow` at PW5, `Purple` on stress, `Blue` below stall pressure, `Fault`, and all four precedence
pairs, each beating the branch it must. `gravSwitchLamp` `Idle` to `Off`, `Charging` and `Armed` both to
`Ready`. `gravArmedLamp` `Charging` to `Off`, `Armed` to `Yellow` only. `samLamp1-2` `Off`, then
`Nominal` on both lamps together. The master start-up lever is proven the same way: `Starting` moves it
1.686 studs, exactly `TRAVEL.start`; `Cold`, `Booting`, `Ready` and `Report` all read `delta 0.0000`
against `Cold`, and `Running` and `Stopping` are deliberately the same pose as `Starting`.

THE DEFECT THAT FELL OUT OF IT: Initialize WAS NOT IDEMPOTENT. The probe's own `Initialize` call and
Runtime's produced two capture lines in one playtest, and they disagreed:

    1st: fan1=-0.658 fan2=-0.658 fan3=-0.658 fan4=-0.659 fan5=-0.659 fan6=-0.659
    2nd: fan1=+0.700 fan2=+0.700 fan3=+0.700 fan4=+0.700 fan5=+0.700 fan6=+0.700

Only the first is a measurement. `smallThrow` reads a SmallLever's sign from the union's current
position - level 1 is whichever stop the rig is found on - and Runtime's own first `Refresh` had already
driven the six fans to their far stop, because the engine boots with the fans running. The second
capture therefore measured the rig standing on its other stop and inverted the travel of every fan for
the rest of the session. The lever still moves on a click; it moves the wrong way and lands on a pose
the art does not contain, and nothing in the console reports it.

THAT ALSO RETIRES AN EARLIER EXPLANATION. The flapping signs in a boot log had been attributed to the
place having displaced levers. It had not: an Edit-mode measurement of all twelve SmallLever rigs found
0 of 12 off their home stops, every rig reading exactly the `d` the module's own note records -
`vent1-3` at 0.2502 against 0.250, `mass1-2` at 0.2482 against 0.248, `shutters` at -0.4501 against
-0.450, `fan1-6` at -0.4078 and -0.4094 against -0.408. The flapping was two `Initialize` calls per
session all along.

THE FIX. `Initialize` no longer empties `levers` and `lamps`: a key whose part is still parented keeps
its first capture, and only a key whose part has gone is re-resolved. A repeat call is now a no-op for
poses, which is what makes it safe to call from more than one place. Verified by re-running: the two
`throws:` lines are byte-identical, and the captures read 54 and 54 where they read 54 and 52 before.
That last pair is its own small fix - the SAM lamps are captured by walking the keyboard rather than by
resolving a path, and their `captured` increment sat inside the branch that added them, so a repeat call
counted two fewer than the first. The one number an operator watches for a lost capture was the one
number that moved on its own.

`workspace.MCP_LAMPTEST` is created at runtime and does not survive the playtest, so nothing the probe
writes reaches the saved place. The probe is kept because it is the only thing that can re-prove this
matrix after any change to an address or a colour.

DOCUMENT DRIFT, RECORDED RATHER THAN CLOSED. `ServerStorage.Data.BackendRewritePlan` is the in-game
counterpart of the rewrite-status file and is not a byte-mirror of it. It carried four sections - the
label-to-action audit, the shift lifecycle, video 3 and the four decisions - and was missing the HDEF
integrity scale, the HDEF overheat run, the per-family lever throw and the click chain that came after
them. This section was added to it; the earlier five were not, and that gap is recorded here rather than
quietly passed over. Two documents that are updated together and are not byte-mirrors will drift, and
the drift is visible only by counting sections.

## Phase 47 - The loose geometry is folded in, and the rollback is one string in ServerStorage  [DONE]

Scope: scene structure and the working folder. Parts changed parent and nothing else - no name in
the CLAUDE 6 binding table was renamed or deleted, no part was created or destroyed, and the
whole-place BasePart total is unchanged at 91905. The numbers, the rollback path and the
verification table are in `baseline/organize_20260926.md`; this is the narrative.

WHY THE PREVIOUS PASS HAD TO SKIP THEM, AND WHY THIS ONE DID NOT. The 2026-09-25 pass built
Workspace.Geometry and then moved 23 parts while skipping 1149, because its reference screen
matched the SUBSTRING ".Part" - which appears in most scripts in the project - so almost every
candidate was declared uncertain. This round asks the question per NAME and gets a different
answer, and that difference is the entire reason 779 could move. Across 123 live scripts, with
ServerStorage excluded because scripts there never run (CLAUDE 0.12, DECISIONS 91):
workspace:GetChildren and workspace:GetDescendants, any casing, ZERO call sites; direct field
access to Part / Line / TextPart / Floor / FloorTextPart / Grate / Baseplate, ZERO. The only live
FindFirstChild calls ask for Stats, Consoles and MCP_LAMPTEST, and the only live WaitForChild
asks for Consoles. So the claim is not "nothing seems to reference them" - it is that the access
path does not exist.

WHAT MOVED. 19 loose Sounds into the existing Workspace.Sounds, 0 collisions; and 779 inert parts
into Workspace.Geometry, which went from 23 children to 802. The 23 it already held are readable
in the class split: they are the UnionOperations, the 8 extra MeshParts and the WedgeParts, while
mine are Part 704, MeshPart 70, SpawnLocation 5. Root children ran 1802, then 1785, then 1006,
then 999. That chain closes exactly: 1802 - 1006 = 796 = 17 sounds + 779 parts, so 17 of the 19
sounds were at the root and 2 came from nested positions; and 1006 - 999 = 7 top-level deletions,
because the other 24 deleted instances were nested and never touched the root count.

THE ONLY MOVED CLASS WITH GAMEPLAY MEANING GOT ITS OWN PROOF. SpawnLocation was 5 of the 779, so
it was screened separately rather than carried on the group's evidence: SpawnLocation, Spawn1..4,
SpawnPoint and FindFirstChildWhichIsA all resolve to zero live references, and the two
GetChildren hits belong to Roblox's own Rig.Animate, which walks a character and not Workspace,
and to StarterGui.ScreenGui.EndShiftHandler. Then behaviour confirmed it: the operator spawned at
233, 406.09, 1370 from both the server and the client, which is the moved SpawnLocation at
233, 402.9, 1370 plus the pivot offset. A relocated spawn that still spawns is a better proof
than any amount of reading.

WHAT WAS DELETED. 31 instances: 27 empty Folders named in no live script, 3 comment-only stub
Scripts verified by stripping comments and asserting the remainder is empty rather than by
reading them, and _BackendOrganization with its 3 children. The last one is the pattern from
CLAUDE 0.12: its only referrer was ServerStorage.Data.BackendRewritePlan, and a script in SS
never runs, so that reference was dead. The 179 empty Models were deliberately NOT deleted - 178
of them are nested inside prefabs as same-named Model.Model.Model.Outer chains, so a script may
be walking them by depth rather than by name. The two empty Folders whose names DO appear in live
code, Alarms.ControlRoom and Alarms.Gravatron, were kept.

A DISCLOSURE, AND IT IS MINE TO MAKE. The descendant count fell by 37 while 31 instances were
listed as deleted. The extra 6 were CreepySounds' children, destroyed with the script. They are
not recoverable: they were destroyed before I inspected them, and
baseline/airemake_audit_20260925.json records the script and a roots census but has no children
section. The script was Enabled=false, a placeholder saveinstance stub whose source is a comment,
and nothing referenced it or its children - but Enabled=false is a property of the SCRIPT, not of
its children, and I let the safety argument about the script cover the whole unit. That is the
error, stated narrowly.

THE ROLLBACK IS ONE STRING IN SERVERSTORAGE, AND ITS KEY IS NOT THE NAME. 779 records,
HttpService:JSONEncode, 197602 bytes, as a single StringValue in ServerStorage rather than as 779
ObjectValues in Workspace - and SS specifically because it does not replicate, which was verified
live rather than assumed ("rollback record leaked to client (must be false): false"). A name
keyed restore does NOT work here and this was measured rather than reasoned: 768 of the 779 parts
are named literally Part, and a name index over Geometry matched only 344 records while returning
lines like "Part cls=Part geo=true root=true", the same name resolving in two containers at once.
Position works - matched at 0.05 studs over every BasePart in Workspace, 768 records find exactly
one part, 11 find coincident twins, and ZERO find nothing. All 779 are accounted for. The 11
coincident ones are a property of the art and are the only records a human has to look at.

TWO WRONG READINGS DISCARDED BEFORE THEY WERE WRITTEN DOWN. A %.3f string key over the CFrame
reported 55, then 66, of 779 records as missing; the misses were a rounding boundary where a
recorded double and a live float32 fall either side of the third decimal, and the tell was that
WIDENING the search LOWERED the hit count, which a real absence cannot do. And a name-keyed index
reported inGeometry 344 with 435 not found, which reads as 435 parts lost; my branch was counting
a name found in BOTH containers as "neither", which with 768 parts named Part is the common case.
Both are recorded because each looked like a real defect for one call, and both were the
measurement rather than the data.

VERIFIED BY READING INSTANCES BACK, IN EDIT MODE, AFTER THE PLAYTEST. Workspace direct children
999, descendants 146685, whole-place BaseParts 91905, Geometry 802, Sounds 29, loose Sounds left
at the root 0, rollback 197602 bytes, _BackendOrganization gone from both Workspace and
ServerStorage, both MCP probes still in ServerScriptService, top-level empty Folders 0, and
Workspace.MCP_LAMPTEST absent in Edit mode, which confirms it is runtime-only and never reaches
the saved place. No Lua errors, only the known sound-authorization spam of CLAUDE 0.8.

ONE PROCESS FACT WORTH CARRYING. solo_playtest action=stop returned
{"message":"Playtest stop signal sent.","success":true} twice and Studio stayed in Play - the Edit
probe still answered "Edit datamodel is not available in Play mode" - while rblx_start_stop_play
with is_start=false returned "Game Stopped" and actually stopped it. The plugin was healthy
throughout (get_handler_health: stuck false, no slow endpoints), so this was not a hang. The stop
signal is not the same thing as Studio leaving Play.

THE WORKING FOLDER. _tools went from 132 top-level entries to 24, with 82 one-off files moved into
_tools/_attic/ under mirror / docs_rounds / apply / nightlog / scratch / bridges / logs and a
MANIFEST.txt recording what went where; __pycache__ deleted; _tools/models/hub, which is the
pinned whisper model cache and not clutter, left alone; and the 212 MiB zip KEPT because the
operator declined. verify_docs.py and its self-test were archived rather than repaired: the
checker pinned a hash of a Studio CLAUDE module, and with docs no longer mirrored into Studio
there is no Studio copy left for it to compare against, so the whole checker is dead rather than
just its pin - and it had already gone permanently red, because section 0.0's own policy banner
grew 980 bytes past its SEC00_LEN pin, so its rc 0 to 1 to 0 self-test could never hold again. A
check that is always red is noise, and it is CLAUDE 0.13's disease in another costume. The archive
weakened nothing and that was measured after both passes: run_tests.sh rc=0 with the recorder
byte-identical at 126009 bytes and 2817 lines, selftest_driver_test catching 4 of 4 mutations on
their named assertions, and selftest_end_test 3 of 3.

RESOLVED 2026-09-26 (QUESTIONS.md O4:A). This file is the canonical phase history; docs/airemake is
kept on disk as the long-form reference for the work it already covers, and is no longer appended to.
The two phases that had been recorded in neither - the lever feedback and the lamp proof - are
back-filled above as Phase 45 and Phase 46, which is why this pass is numbered 47 rather than 45. The
numbering below Phase 45 comes from the order the work was done, taken from file mtimes rather than
assigned: the lever-feedback note is 12:51, the four lamp-proof payloads 13:59, this pass about 21:00.

ALSO RESOLVED (QUESTIONS.md O5:A). ShutdownEndsShift false is kept as a documented alternative
configuration rather than deleted, so the four selftest_driver_test mutation proofs that hang off it
keep their subject.

CORRECTED HERE. CLAUDE 8 had called TempLabel's second writer the one open item while this file's own
Phase 24 is titled "The TempLabel second writer  [DONE]". That claim was stale and is struck through
in CLAUDE 8 as of this pass.

## Phase 48 - The clock announced two things that did not happen, and the receipt named the wrong hand  [DONE]

**What was run.** The operator injected `_tools/TRG_original_recorder.luau` into the ORIGINAL game
once and produced `Data/flow/original_260926-230049`: 1357508 bytes, 4775 lines, session 23:00:49,
about 14 minutes, sealed on its last line with a complete `## RECEIPT` -
`samples=2786 events=3574 postfails=0 spilled=0 dropped=0 hooks=1003 drive=shut_down/user-shut`.
Nothing was dropped and nothing failed. The whole harness was green before this reading
(`run_tests.sh` rc=0) and the suite is green after it.

**What the file contains, which is not what was asked for.** It does NOT contain the cold power-on
half. `EVT2017` says so in the file's own words - `the clock already reads past 12:00PM at inject;
the core is up` - and it follows from the receipt: `flow=false`, because `flow` is literally
`tostring(sawDown)` (line 1204) and `sawDown` needs `tempF < CoreThresholds[1] = 5600` for
`DebounceSamples = 3` consecutive polls, while `m.temp` held 12865 to 12979 F across the entire
run. `flow=false` here means "the core was never seen down", not "the data is missing". 5600 F is
the game's own stallout line (`INGAME_MANUAL` 87, "below ~ 6000F"), not the 2000 F low-temp trip
the operator named in `Q1`; they are different instruments and only one of them is what `flow` uses.

**What it does contain, which is worth more than the half it lacks.** The run caught the EQUINOX
chain end to end. The quota panel had been carrying `12PM marks the beginning of an equinox event,
which will result in major damage!` the whole time; at exactly 12:00 PM the log printed
`[ALERT] - EQUINOX EVENT IMMINENT! SHUTDOWN ADVISABLE!`, and six minutes later two CBLs collapsed -
`c.cbl1Pct 25->10`, `c.cbl3Pct 25->10`, `CBL1Frame.StateLabel LOW OUTPUT`,
`CBL3Frame.StateLabel LOW OUTPUT`, flagged `UNATTR` with `last click 97 polls ago` so the equinox
did it and not a click. Pressure then fell 2542 to 1070, four monitors read
`MAINFRAME CONNECTION LOST`, and `s.MainframeMeltdown` went true at `tempF=7978`, which is what
sealed the file. Quota stood at `q.scale 0.26`. That is a complete, unforced recording of the
game's worst event, and it also confirms `B2`: `fc.panel` now re-resolves per sample
(`descendants=30 rows=8` then `descendants=217 rows=46`) instead of the single unusable snapshot
from the earlier run, so the `B2` note is closed.

**Defect 1 - the CLOCK event announced a shift boundary in the middle of a shift.** `q.up` is
`q.clock > 0` over a dial that puts noon at 0, so 12:00 PM is the one minute on the whole 12-hour
face that reads false; every other minute reads true. On a run injected with the core up the dial
has to travel a full circle before it reads past noon again, and when it does, `announceClock`
emitted a pair 60 s apart:

    EVT3490 CLOCK the clock is back at 12:00 PM
    EVT3495 CLOCK the clock passed 12:00PM: the shift has started

Both are false. `m.temp` held 12865 to 12979 F across them, and the raw text marched 11:59 AM to
12:00 PM to 12:01 PM with no reset, so nothing ended and nothing started. What is actually at noon
is the place describing itself: `INGAME_MANUAL` 114 and 148, "12PM marks the beginning of the
Equinox Event", against a shift of 6:00 AM to 6:00 PM (`DECISIONS` 28). The second line is the
dangerous one, because it is indistinguishable from the real crossing - it IS the real crossing.
The inject state is the only thing that tells them apart, so the fix keeps it: `clockStartedUp`
records what the first read was, and a run that was already up at inject gets
`the clock moved to <raw text> -- the dial, not a shift boundary: the core was already up at
inject` instead. A run injected before the shift starts is untouched and still announces the
crossing exactly as before.

**Defect 2 - the receipt attributed a meltdown to the operator.** Line `EVT3573` read
`the operator shut it down: s.MainframeMeltdown=true`, and `drive=shut_down/user-shut`. The
`said` field proves no operator was involved: it is the THIRD of four fallbacks, and the code's own
comment above it says the fallbacks exist for shifts "that ended some other way - a cold trip, a
machine-room meltdown". The file contains no shutdown-lever click anywhere: 124 CLICK events, 2 of
them `SAMKeyboard`, none on `StartUpBigLever.ShutClickPart`, and no `v.shutdown` either. The fix
makes the sentence follow the flag - `v.shutdown` keeps `the operator shut it down:`, the other
three say `the shift ended:` - and leaves the VERDICT alone, because `user-shut` answers "who
pressed" and "not the driver" is the honest answer for a meltdown too. Renaming it would have moved
the receipt field, the HOWTO table and four mutation proofs to say the same thing less precisely.

**Why the fix does not discard the reading.** It refuses the interpretation, not the observation.
The raw text still goes out and `readQuota` still writes `q.clock` / `q.up`, so the moment stays in
the file and can be re-derived later. This is not a new principle - the HOWTO had already written
it down, listing "or it wraps at some point" among the reasons for keeping the underived strings
next to the derived ones - and it is the reason this wrap was FOUND rather than guessed at: the
raw text is what showed 11:59 AM to 12:00 PM to 12:01 PM as one continuous march.

**Verification.** `_tools/build_clock_test.py` is new and takes its subject from the SHIPPED
recorder by text, like the other three: it extracts `announceClock` and the three latches it closes
over, because a harness that re-declared them would go green on a recorder with the door deleted.
`_tools/selftest_clock_test.py` is new and breaks each of the three properties in turn, asserting
the suite goes red on the NAMED assertion rather than merely red. Two of the three point in
opposite directions on purpose: the wrap door must swallow a mid-shift pair, and the cold opening
must still announce its crossing, so a fix that swallowed everything would pass the first and lose
the event's whole purpose. Results - `run_tests.sh` rc=0, clock `10 PASS, 0 FAIL`, the other three
harnesses unchanged; the mutation proofs catch all 3 of 3 (the door removed, the latch armed at
inject so it swallows the real crossing, and the wrap message stripped of its reading), and the
recorder comes back clean afterwards. The instrument is now 128612 bytes and 2861 lines, from
126009 and 2817. No event kind was renamed and no receipt field moved, so existing files still read
the same way.

**What this run does not settle.** Whether the operator should spend another injection aiming at a
cold start. Nothing about the recording is lost, so it is a question of what is wanted, not of what
is broken. It is the open item in `QUESTIONS.md`.

---

## Phase 49 — 温度是怎么算的：`m.fluct` 就是那一步  [PARTLY DONE]

**日期：** 2026-09-26 约 23:40。**触发：** 用户问「温度计算什么的能搞出来的吗？」。
**对象：** `Data/flow/original_260926-230049`，**只读，一个字节都没改**。
**一句话结论：** 结构能定死，增益只到量级，**公式拿不到** —— 每一条都有数。
分析脚本是 `_tools/_attic/scratch/temp_shape.py` / `temp_fit.py` / `temp_fit2.py` /
`temp_seg.py` / `temp_tick.py` / `temp_fluct.py`（草稿，一次性，留在原处当证据）。

### 49.1 `m.temp` 不是一个连续状态，是一个 tick 的输出

- 全文件 `m.temp` 一共变过 **393** 次；其中 **391 次满足
  `temp(下一拍) − temp(这一拍) == m.fluct`，逐字节相等**。剩下 2 次是读序错位
  （一行同时带了上一 tick 的温度和这一 tick 的 `fluct`：t=177.96、t=501.40）。
- 所以 **`temp(t+1) = temp(t) + m.fluct(t)`**。`m.fluct` 不是温度旁边那个「稳定度」，
  **它就是那一 tick 的温度增量**；`m.temp` 是它的累加。校准台上的 NET STABILITY
  给操作员看的就是这个导数 —— 难怪游戏敢让操作员去「判断稳定度」。
- tick 周期（事件间隔）：中位数 **1.79 s**，众数 2.0 s，p10 1.51 / p90 2.04，
  采样约 3.3 Hz，所以抖动就是 ±一拍。**定 ~1.8 s。**
- `m.temp` / `m.press` / `m.fluct` 三个标签**同一行一起变，从不分开** ——
  一个物理步写三个标签。**所以任何「每采一次算一次导数」的做法都是在拟合重绘时刻表**：
  第一次拟合这么干，得到 R² = 0.084、冷却项的符号是反的；改成按 tick 做，同一份数据
  给出 R² = 0.33、符号全对。
- **温度不是一阶惯性环节。** t=560.78–610.97，cblPct=75 / cool=0 / fan=3，增量是
  `+144 +289 +229 +205 +287 +147 +279 … +241 +214 +157` —— 在**时间上平**，
  在**温度上**也平（6625 → 13224 F 一路涨）。一阶惯性应该随接近平衡而收窄，它没有。

### 49.2 能定到的：结构 + 量级

最小二乘，391 个 tick，目标 = `m.fluct`（单位 F/tick）：

| 项 | 系数 ± 标准误 | 读作 |
|---|---|---|
| 常数 | −220.9 ± 43.8 | |
| `ΣcblPct` | **+5.05 ± 0.42** | 每 1% CBL 输出 |
| `c.coolSum` | **−58.2 ± 9.7** | 每台冷却泵（这一趟只用到 1 档） |
| `c.fanCount` | **−32.8 ± 9.4** | 每个风扇 |
| `m.temp` | −0.0068 ± 0.0044 | **与 0 无法区分** |

R² = **0.328**，残差 sd **146 F/tick**。**模型解释了漂移，没解释波动。**
`m.temp` 这一项与 0 无法区分是这一份里最硬的一条：**在 6600–14000 F 这段，
温度本身不产生回正力 —— 温度是个积分器。**

### 49.3 设置对照表（不假设任何模型，直接取中位数，F/tick）

| cblPct | cool | fan | n | 中位 | 温度区间 |
|---|---|---|---|---|---|
| 175 | 2 | 3 | 6 | +246 | 13119..13941 |
| 150 | 3 | 6 | 4 | +34 | 9324..9496 |
| 75 | 0 | 1 | 9 | +13 | 11818..12045 |
| 75 | 0 | 2 | 48 | +16 | 11786..12596 |
| 75 | 0 | 3 | 48 | **+174** | 6916..13224 |
| 75 | 0 | 4 | 8 | +248 | 11088..12752 |
| 75 | 1 | 3 | 72 | +52 | 7344..12980 |
| 75 | 1 | 4 | 44 | +14 | 9113..13556 |
| 75 | 2 | 3 | 56 | −38 | 6625..13963 |
| 75 | 2 | 4 | 68 | −49 | 9069..13716 |
| 75 | 3 | 3 | 4 | −124 | 8892..9341 |
| 45 | 0 | 6 | 8 | **−619** | 7978..12386 |

最后一行是 Equinox 之后的衰减，不是常规设置。**表里自己就自相矛盾**
（`cool=0 fan=2` 是 +16 而 `cool=0 fan=3` 是 +174），原因是每一行的操作员都把控制
动成了对温度的反应 —— 见 49.5(b)。

### 49.4 第二个锚：冷启动确实在文件里，而且温度是一条**连续**的线

> **2026-09-27 重写。** 本节原来那句「`0` → `9420 F`，**96.6 s**，**≈ 98 F/s**」
> 是错的，错法和更正见下面的 49.4b。**结论「半场在文件里」不变，而且比原来更强** ——
> 温度根本不是两段拼起来的，它是一条线。

`s.Core.TemperatureVal` 一共只有 23 个样本：`B 1 t=1.34` 是 **0**，然后
**整整 88.5 s 一个样本都没有**（采集器只写变化，所以那 88.5 s 里它一直**恰好等于 0 F**），
到 **t=88.53** 才是 `510`。从那里到 **t=97.90 的 9420**，**9.37 s**、**+8910 F**。
（三个 CBL 都在 Lvl 4 —— `c.cbl*Pct` 各自 100，`Σ = 300`；冷却 1 档、风扇 4 个。）

**但温度没在那儿断。** 监视器那一路 `t.ReadingsFrame.TempLabel` **第一次出现正是
t=88.53，一路写到 t=865.09**。把它和 `m.temp` 并排：

| 序列 | 首拍 | 末拍 | 样本数 |
|---|---|---|---|
| `t.ReadingsFrame.TempLabel` | t=88.53 | t=865.09 | **416** |
| `m.temp` | t=98.77 | t=865.09 | **394** |

**416 − 394 = 22 —— 正好是 `s.Core.TemperatureVal` 有值的那 22 拍**（t=88.53..97.90）。
两边重合的每一拍数值也一一相同：t=96.20 都是 9207、t=97.06 都是 9244、
t=97.90 都是 9420、t=98.77 都是 9330、t=100.57 都是 9324、t=102.52 都是 9366、
t=104.11 都是 9393。**`t.ReadingsFrame.TempLabel` 和 `m.temp` 是同一个读数** ——
`m.*` 那一路要等监视器开机后才开始记，`t.*` 那一路早 22 拍就有。

所以从 **t=88.53 一路到关机（t=865.09），温度是一条线，中间没有缝**。
**不需要拼接**。（DECISIONS 138 里那段「拼在 t≈98」是在**没看 `t.ReadingsFrame.TempLabel`**
的前提下写的。）

### 49.4b 【更正】那个 98 F/s 是平均值，分母里 88.5 s 是零

原句「`0` → `9420 F`，**96.6 s**，**≈ 98 F/s**」算的是 `9420 / 96.56`。真实形状是**两段**：

| 段 | 区间 | 时长 | 变化 |
|---|---|---|---|
| 平在 0 | t=1.34 → 88.53 | **88.5 s** | 一个样本都没有，恒 0 F |
| 起堆 | t=88.53 → 97.90 | **9.37 s** | 510 → 9420 F，**均 +951 F/s** |

斜坡本身也不匀速：逐拍速率从 **+1642 / +1630 / +2303 / +2013 F/s** 起，
衰减到 **+210 / +104 / +14 F/s** —— **是趋近平台的一阶形状**，平台就在 9420 附近，
不是一条匀速直线。

**「103 F/s 和 98 F/s 同速」这条佐证作废。** 它拿 9420（t=97.90，`s.Core.TemperatureVal`
的**最后一拍**）减 9330（t=98.77）：那是 **−90 F，方向是往下的**，而前面是往上的 ——
两个反号的数拿来比「速率」没有意义；而且 9420 之后 `s.Core.TemperatureVal`
**到文件结束一次都没再出现**，它是**终点**，不是斜坡上的一个中途点。
**何况这条读数本来就不用拼**（见 49.4）。

`EVT2072–2078 StartUpLever` 那句也顺带更正：**是 8 次，EVT2072–2079**。

### 49.5 拿不到的，以及为什么

**(a) 增益不可外推 —— 但「饱和」这条本文件没证出来。** 冷启动那段实测 **+180 F/tick**，
那是 `98 F/s × 1.8 s`，而 98 F/s 是 49.4b 里那个**含 88.5 s 零的平均值**。
按真实的斜坡算（`951 F/s × 1.8 s`）是 **+1712 F/tick**，比 49.2 拟合出的 **+1104**
还**高** 1.6 倍。更要紧的是两个数**不是同一个工况**：+1712 是**开机瞬态**里的一拍
（堆芯离平衡很远，而且起堆是脚本驱动的），+1104 是从**稳态班次**数据拟合的。
**所以「CBL 从 75% 翻到 300% 时净加热饱和」在本文件里既没被证明、也没被否证 ——
这条挂起来。**（原先写的「差 6 倍」是拿两个错口径的数相减。）

**(b) 控制器是反馈，不是实验。** 操作员每一次动控制都是对温度的回应，所以回归量
和被解释量共线。最直接的证据：池化拟合里 `coolSum·T` 的系数是**正的**（`+0.0101`），
字面意思是「冷却越强、高温时掉热越少」—— **物理上反的**。那不是发现的物理，是共线性。
**这一条是整件事的根**：一次有人开着的班次不是阶跃响应实验。

**(c) 回正力定不下来 —— 而且这个测试是干净的。** 在**固定设置内部**做，控制混叠
就影响不到：`(75,2,4)` 跨 9069–13716 F 这 4600 F，斜率 **+0.3 F / 1000 F，corr +0.01**
（**平的，没有回正力**）；`(75,1,3)` 跨 7344–12980 F，斜率 **−40.4，corr −0.52**
（τ ≈ 25 tick ≈ **45 s**）；`(75,0,3)` 斜率 **−33.5，corr −0.58**。
**同样大的跨度，一组有回正、一组没有。τ 没法从这一趟里定出来。**

**(d) 噪声不是白噪声，不能撒 iid。** 去掉漂移后的残差：sd **145.5 F**，偏度 **−1.36**
（左尾重，大跌比大涨狠），**lag-1 自相关 0.655**。它是**持续的**。
想复刻手感要复刻这个自相关，不能撒独立噪声。
（对数感：sd 146 F/tick 的白噪声跑 428 拍会散开 sd ≈ 3010 F；实测温度跨 6591–13963 F。）

**(e) `c.cbl*Lvl` 不是读出来的，是采集器自己算的。** `readCBL()`
（`_tools/TRG_original_recorder.luau:986-1010`）写的是
`lvl = clamp(floor(pct/25), 1, 5)`，注释里就写着「derived level ... so a reader can see
where the quantisation happens」。**它和 `Pct` 是同一个量的两种写法，不是两个独立测量。**
真正从游戏里读出来的是 `PowerLabel` 的文字（`c.cbl*Pct`，取值 {10,25,50,75,100,125}）。

**(f) 冷却档位这一趟只用到 0 和 1。** `readCoolant()`（`:1013-1035`）数
`Light1..Light3` 有几盏亮，所以 `c.cool*` 是 **0..3 的档位**、`c.coolSum` 是 0..9 的和。
这一趟 `c.cool1/2/3` **只出现过 0 和 1**，`c.coolSum` 只到 3。
所以 −58 F/tick 是 **1 档**的增益，**2/3 档这一份没有**。
两种可能分不开（见 `QUESTIONS.md` P2）：操作员没用到 2/3 档，**或者**读数只认第一盏灯的颜色。
在 AIRemake 的 `Workspace.Consoles.ThermalConsole.CoolantControl1` 上点过：
子物体是 `Light1/Light2/Light3` + `PW1ClickPart/PW2ClickPart/PW3ClickPart` ——
**3 灯 3 档**，采集器的 `for j = 1, 3` 是对的。但**原版那一台没有开着，没能对**。

**(g) `s.Core` 里那几路读数各自停在不同时刻**：`TemperatureVal` 停在
**t=97.90（9420）**、`OutputVal` 也停在 **t=97.90**、`PressureVal` 停在 **t=116.43**，
而 `RadiationVal` 一路写到 **t=866.87（414 次）**。**所以「stats 全冻了」不是通则。**
**温度这一路也不是断了** —— 它换了个名字继续（`t.ReadingsFrame.TempLabel` = `m.temp`，
一路到 t=865.09，见 49.4）。**但 `s.Core` 自己那三个值为什么会在 t=97.90 / t=116.43
停笔，机制不明 —— 不编。**

### 49.6 给 remake 用的一句话

**把温度当积分器，不要当惯性环节。** 每 tick
`ΔT = 加热(ΣcblPct) − k_cool·冷却档位 − k_fan·风扇数 + 噪声`，
`加热` 在 75% 以上饱和，噪声带 lag-1 自相关 ≈ 0.65、sd ≈ 145 F/tick、左偏。
`k_cool ≈ 58`（1 档）、`k_fan ≈ 33`（F/tick）。**回正项要么没有、要么 τ 在 45–90 s 之间
且这一份定不下来** —— 这是唯一必须靠 remake 自己调、或者靠下一趟专门测的参数。

### 49.7 开机那 96 秒里，配堆的是机器，不是手

**（2026-09-27 新查的，起因是用户问「完整的开机流程是不是没记录」。）**

**记全了。** 从 `B 1 t=1.34` 的完全冷态到 t=868.94 的封存，两头都在文件里。
t=1.95→13.39（11.4 s）操作员的 **20 次点击**也都带名字：

```
EVT2060 CLICK RoomLight        EVT2067 CLICK MonitorBoot
EVT2061 CLICK MonitorPower     EVT2071 CLICK HDEF-PowerLever
EVT2062 CLICK Shutters         EVT2072-2079 CLICK StartUpLever   <- 8 次
```

后面紧跟 `EVT2081 [ALERT] SUBSPACE REACTOR START-UP SEQUENCE INITIATED` 和
`EVT2084 PowerLabel 524 GW → 3.001 TW` —— **面板跟着变了，所以这 20 条不是注入时的假事件。**

> 顺带一个读法上的坑：`S 2 t=1.95` 是 **poll 头**，写在它下面的 EVT 行属于
> **这个 poll 之后到下一个 poll 之间**的窗口，也就是 t=1.95→13.39 —— 不是「610 ms 里
> 点了 20 下」。`dt=610` 是距上一个 poll 的时间，不是这段事件窗口的宽度。

**但 t=13.39 到 t=90.48 这 77 秒，一次 CLICK 都没有**，而堆在这段时间里被配好了：

| t | 变了什么 | 形状 |
|---|---|---|
| 31.39 | `c.cool1/2/3` 0→1 | **三台在同一个 poll 里一起跳** |
| 35.95→38.42 | `c.fan1..fan6` 0→1 | 按 1→6 顺序，**每 0.30–0.60 s 一个** |
| 59.62 | `c.cbl*On` 0→1、`Lvl` 0→4 | **三个在同一个 poll 里一起跳** |
| 85.39 | `c.cbl*Pct` 100→50、`Lvl` 4→2 | **三个在同一个 poll 里一起跳** |

它们全是 `UNATTR`，括注里「last click N polls ago」的指针**一律指回 t≈2–13 那次开机**。

**读法：这些不是人点的，是开机序列自己配的，操作员只投了启动杆。** 三条证据：
① **同一个 poll 里三台一起跳** —— 手做不到；
② 六个风扇**等间隔、按序号**依次开 —— 是脚本的形状，不是手速；
③ **钩子是活的** —— 同一份文件在 t=90 之后照样抓到 `Coolant3-OFF`(t=124.30)、
`Fan4/5/6`(t=107–132)、`CBL*-PW*`(t=113–120)、`CBL1-PURGE`(t=118.24)，
而且全场 `PROMPT` 事件为 **0**（所以也不是走的 ProximityPrompt）。
**这一条是推断，不是直读** —— 文件给的是「变化发生了、没人点」，把它归给开机序列是解释。
但它同时解释了「开机为什么要 96 秒」：**前 88 秒是序列在铺场子，堆芯就停在 0 F 上。**

**教训（采集器那条）：`UNATTR` 只在「钩子这段时间是活的」时才等于「没人点」。**
要断言「没人点」，先在同一份文件里找到**同类控制在别处被抓到的 CLICK** ——
这里就是 Coolant / Fan / CBL 三族在 t>90 都被抓到了，所以 t<90 的缺席才算数。
（进 `DECISIONS_2.md` 144。）

---

## Phase 48 更正（2026-09-26 23:40）

**上面 Phase 48 那节原来写错了三处，而且用户当场就纠正过**（原话：
`我就是先注入才开的核心啊，核心开好之后我按start`）。

1. ~~「采集器第一份『中途注入』的产出」~~ → **不是中途注入。是冷启动。**
   `B 1 t=1.34`：`s.Core.TemperatureVal=0 s.Core.OutputVal=0 s.Core.RadiationVal=0`，
   六个风扇全 0、三台冷却泵全 0、三个 CBL 全 0；`EVT2072–2078 CLICK StartUpLever` ×7
   （t≈2–13 s）就是开机；`s.Core.TemperatureVal` 从 0 爬到 9420；`s.GameActive`
   在 **t=98.47** 才 false→true。
2. ~~「缺冷启动那半场」~~ → **半场一直在文件里**，见 49.4。
3. ~~「`flow=false` 因为注入时核心已开着」~~ → 因果反了。`flow=false` 是**结构性的**：
   `flow` 是 `tostring(sawDown)`，`sawDown` 要 `flowArmed`，`flowArmed` 要
   `isRunning`（`tempF >= 5600`，也就是 `m.temp` 有读数）连续 3 拍。
   **冷启动的一趟永远给不出 `flow=true`**，核心冷了 88 秒也一样。

**错在哪：** 我把 `m.temp` 当成了堆芯温度。它是**监视器的标签**，而监视器在 t≈99 之前
读的是 `ERR F`（`EVT1139`）—— **监视器最瞎的时候正是堆芯最冷的时候。**
`EVT2017 CLOCK the clock already reads past 12:00PM at inject; the core is up` 这句也一样：
它的依据是 `q.up = q.clock > 0`，而 `q.clock` 是个**自由走的表盘**（冷堆时 710→715
一路在走，堆芯正停在 0 F）。Phase 48 修了这句话的**措辞**（改成按 `clockStartedUp` 分辨），
**没修它的依据** —— 依据还是「表盘过了正午 = 核心开着」。这条进 `QUESTIONS.md` P3。

**顺带撤回一条：** Phase 48 说「Equinox 把两个 CBL 打到 10%」。同样的 25→10
在 **t=188.71** 和 **t=548.75** 也出现过，那两次没有 Equinox。所以「Equinox 干的」
这一份文件**不支持** —— 它是同时发生的两件事，不是一条因果。

### Phase 49 的 §8 摘要原文（2026-09-27 从 CLAUDE.md 搬来，逐字未改）

**Phase 49 —— 温度是怎么算的。结构定死了，增益只到量级，公式拿不到。**
① **`m.fluct` 就是那一 tick 的温度增量**（393 次 `m.temp` 变化里 391 次
`temp(下一拍) − temp(这一拍) == m.fluct`，逐字节相等），所以 **`m.temp` 是它的累加**，
tick ≈ **1.8 s**，**温度是积分器不是惯性环节**。
② 拟合（391 tick）：`ΣcblPct` **+5.05/%**、冷却泵 **−58**、风扇 **−33**、
**温度项 ≈ 0**（−0.0068 ± 0.0044），R² 0.33，残差 sd 146 F/tick —— **解释了漂移，没解释波动**。
③ **拿不到的原因**：操作员每次动控制都是对温度的回应 → 回归量共线；增益**不可外推**
（冷启动 CBL 300%，实测 +180 F/tick 而模型给 +1104，饱和）；回正项在固定设置内部互相矛盾 →
**τ 定不下来**；噪声 lag-1 自相关 0.655，不是白噪声。细节与全部数字见 `PROGRESS.md` 49。
④ **冷启动那半场一直在文件里，温度是一条线、不用拼**：`s.Core.TemperatureVal` 在 **0 F 上
平了 88.5 s**，然后 **9.37 s** 从 510 爬到 **9420 F**（一阶趋近形状）。
监视器那一路 `TempLabel` 和 `m.temp` **是同一个读数**（394 + 22 = 416，重合处数值相同）。
**旧写的「0→9420 F / 96.6 s ≈ 98 F/s」和「103 F/s 同速」都作废**（分母里 88.5 s 是零；
9420 之后那个值再没出现过，它是终点不是中途点）。**开机那 96 秒里配堆的是机器不是手**：
t=13.39→90.48 共 **77 秒零 CLICK**，冷却三泵、三个 CBL 各在**同一个 poll 里一起跳**，
六个风扇**等间隔按序**开 —— 操作员只投了启动杆（`StartUpLever` **×8**）。

**为什么搬：** 跟 Phase 53 那次同一个理由 —— 这一节是**跑动细节**，
而 `CLAUDE.md` 每轮都要进上下文。搬的是**同一段文本**，不是摘要，所以
`CLAUDE.md` 那边留一句指针就够，数字不会两处漂移。

---

## Phase 50 — 压力：一个风扇 = −60 PSI/tick（用户给的数，文件验过）[DONE]

**日期：** 2026-09-26 约 23:55。**触发：** 用户答了 P2（`没有` —— 冷却泵没用到 2/3 档），
并主动给了一个常数：**`一个风扇每tick降低60PSI`**。**对象：** 同一份文件，**只读**。

### 50.1 最干净的一段：操作员自己替我们做的 A/B

cblPct=75、coolSum=0 **两个都按住不动**，**只有 fan 在 1↔2 之间来回拨**，
压力斜率**精确地在 +58 和 −2 之间跳**：

| t | fan | dP (PSI/tick) |
|---|---|---|
| 700.67 / 702.41 | 3 | **−62** |
| 704.21 | 2 | **−2** |
| 705.98 / 707.70 / 709.44 | 1 | **+58** |
| 711.22 … 732.46（八拍） | 2 | **−2** |
| 734.23 … 739.44（四拍） | 1 | **+58** |
| 741.17 … 748.21（五拍） | 2 | **−2** |
| 751.87 / 753.49 | 1 | **+60** |

**fan 1 → +58、fan 2 → −2、fan 3 → −62** —— 每加一个风扇正好 **−60**，
而且这是**三次独立的跳变**（1↔2 来回四趟 + 2→3 一次）。
**fan=0 时这个工作点的基线 = +118 PSI/tick。**

### 50.2 全文件 12 次风扇拨动，12 次方向全对

| t | fan | 前 | 后 | Δ |
|---|---|---|---|---|
| 134.18 | 3→4 | +11 | −46 | −57 |
| 192.15 | 4→3 | −38 | −2 | **+36** |
| 310.55 | 3→4 | +26 | −21 | −47 |
| 428.54 | 4→3 | −24 | +34 | +58 |
| 490.35 | 3→4 | +24 | −38 | −62 |
| 550.32 | 4→3 | −47 | −10 | **+37** |
| 656.48 | 3→4 | +54 | −8 | −62 |
| 684.74 | 4→3 | −110 | −62 | +48 |
| 704.21 | 3→2 | −62 | −2 | **+60** |
| 734.23 | 2→1 | −2 | +58 | **+60** |
| 741.17 | 1→2 | +58 | −2 | **−60** |
| 806.82 | 2→3 | +4 | −54 | −58 |

**开风扇 → 斜率变负，关风扇 → 变正，12/12 没有一次例外**，中位 |Δ| = 58。
最干净的那几对（基线本身不含糊的，就是 50.1 那趟）**正好是 ±60**。
**用户给的 60 是对的。**

**但线性只验到 3 个风扇，4 个以上这一份答不了。**
fan 3→4 的四次拨动是 −57 / −47 / −62 / −58（中位 −57，还在 60 附近），
**可是 fan=4 的「稳态」窗口（t=310.55–356.26）根本不是常数**：
`−30 −26 −24 −22 −20 −18 −16 −14`，一路朝 0 收敛 —— 那是一个**衰减中的瞬态**，
不是稳态斜率。所以它**既不能否证 60、也不能支持 60**。
**4 个以上风扇会不会饱和 = 未解。**

### 50.3 冷却泵的压力增益**不是**常数

同样按住 fan 和 cblPct，五次 coolSum 拨动的 Δ 是：

| t | cool | Δ (PSI/tick) |
|---|---|---|
| 368.69 | 1→2 | +0 |
| 561.08 | 2→0 | +11 |
| 612.14 | 0→2 | +4 |
| 666.92 | 2→1 | **−102** |
| 695.19 | 1→0 | −4 |

**没有常数。** 那个 −102 是单次跳变，很可能是瞬态。
**所以「一个风扇 −60」这条不能顺手推广到冷却泵。**
冷却泵对压力要么作用很小（≈ 0），要么是借温度间接起作用的 —— **这一份分不开**。
（对照 49.2：冷却泵对**温度**是有确定作用的，−58.2 ± 9.7 F/tick。）

### 50.4 顺带：这条数从**文件外面**锁死了 tick

用户说的「每 tick」和文件里的 tick 是同一个：**压力变化的间隔中位数 1.79 s，
和温度的 1.79 s 一致。** 这是第一次由**文件之外的人**确认 tick ≈ 1.8 s ——
前面那个 1.8 s 是我从采样间隔反推的，现在有了独立的见证。
**意义：** 49.2 那张表里的「F/tick」和用户脑子里的「tick」是同一个单位，
不需要再做任何换算。

### 50.5 压力也是累加量，但它的增量**没有**单独上报

文件里 `m.*` 只有三个键：`m.temp`、`m.press`、`m.fluct`。
**温度有 `m.fluct` 把每拍增量直接报出来（见 49.1），压力没有** —— 压力的增量只能自己差分。
差出来的 dP 有 **80 个不同取值**，最常见的几个是
−2（18 次）、+26（17 次）、+4（15 次）、+2（14 次）、+10（11 次）、
+50（11 次）、−46（11 次）、−44（11 次）—— **不是同一个常数的重复**
（同一条设置下 `+58` 也见过 `+50`），说明**基线本身在漂**（`c.cbl*Pct` 会自己漂，
见 49.5(e)）。**要给压力也做一张和 49.3 一样的表，得先有 `cblPct` 的独立记录。**

### 50.6 给 remake 用

**风扇 → 压力：−60 PSI/tick（已验证，3 个风扇以内）。**
fan=0 时 cblPct=75 / cool=0 那一点的基线是 **+118 PSI/tick**。
压力同样是累加量（不是惯性环节）。**冷却泵 → 压力：这一份没量出来。**

---

## Phase 51 — 上版本控制，推到 GitHub（`The-Reactor-Game-Continuation`）[DONE]

**日期：** 2026-09-27 00:05。**触发：** 用户给了仓库地址并说「既然你能 git，那 push 吧」。
**对象：** 工作文件夹本身，不是游戏。

### 51.1 之前是什么都没有

`D:\rblxTRGproject` **从来没有过 `.git`**（`/c/Users/andypeng1NB/BloxBot` 和 `D:\BloxBot` 也没有）。
远端 `https://github.com/andypeng1/The-Reactor-Game-Continuation` 是 **public**、MIT、
只推过一次（`e299752`，2026-09-17），里面**只有 3 个文件**：
`LICENSE` / `README.md` / `reactor_telemetry.txt`。

### 51.2 做了什么

| 步骤 | 结果 |
|---|---|
| `git init -b main` | — |
| 初始提交 | `3ed1dd4`，**173 个文件 / 9.04 MB** |
| 与 `origin/main` 合并 | `--allow-unrelated-histories`（两边没有共同祖先），只有 `README.md` 冲突（add/add） |
| 冲突解决 | **取本地那份** —— 它已经把远端那段「This project was inspired by…」前言抄进去了，所以两边的内容都在 |
| 推送 | `e299752..3461509  main -> main` |
| 远端核对 | 树里 **191 项**，`LICENSE` 和 `reactor_telemetry.txt` 原样保留 |

最终 **175 个文件**在版本控制里。

### 51.3 故意没进去的四个东西

`.gitignore` 里每一条都写了理由 —— 因为**忽略文件是以后唯一会有人去看的地方**：

| 排除 | 大小 | 为什么 |
|---|---|---|
| `_tools/models/` | **5986 MB** | whisper 模型缓存，可重建 |
| `TRG Sounds & Images pack/` + `.zip` | **426 MB** | 原版游戏的拆包资产；zip 另外还超 GitHub 单文件 **100 MB 硬限** |
| `Videos/` | **104 MB** | 三个**第三方 YouTube 攻略视频**，只是拿来本地转写的 |
| `.ai/`、`.claude/settings.local.json`、`scheduled_tasks.lock` | <1 MB | 机器本地缓存 / 本地权限状态 |

**总盘子 6527 MB → 进仓库 9.04 MB。** 排除的 99.9% 是模型缓存；
**但排除清单不只是关于大小** —— 资产包 214 MB、视频 104 MB 都在 GitHub 限额以内，
它们被排掉是因为**不是我们的东西**，这个判断文件大小替你做不了。

**保留的：** `src/`（ReactorBackend 本体）、全部 `.md` 文档、`docs/`、
`Data/`（含 7 份 `flow/original_*` 采集文件 + `DataCollection.Log`）、
`_tools/`（去掉 `models/`）、`baseline/`、`Addition/`、`Run.ps1`。

### 51.4 顺带定了一件以前没有的事：行尾

全局 `core.autocrlf=true` 会在 checkout 时**把每一份 `.md` 改写成 CRLF** ——
而这个工程的文档是**按字节当工件**的（`DECISIONS` 96 就是「长度相同、内容不同」
那个真出过的 bug）。所以加了 `.gitattributes` 钉成 `* text=auto eol=lf`，
并把这个 repo 的 `core.autocrlf` 设成 `false`。仓库里存 LF，工作区那份下次
checkout 才会跟着变。

### 51.5 留了一条给用户拍板

`Data/TRGWeb.luau`（357 行）、`Data/DataCollection.luau`（489 行）、
`Data/Summary01.luau`（37 行）是**原版游戏 ModuleScript 的逐字副本**，
现在跟着 public 仓库公开了。已进 `QUESTIONS.md` **P5**。

### 51.6 第二笔提交：git 主机不通，改走 `api.github.com`

Phase 51 的文档提交（本地 `f1aadb6`）**推不出去**：`git push` 连试五次，
分别报 `Empty reply from server` / `Recv failure: Connection was reset`，
最后三次稳定在 `Failed to connect to github.com port 443 after 21080 ms`。

但没有全断 —— 同一次测量里两个主机是分开的：

| 主机 | 结果 |
|---|---|
| `api.github.com` | **HTTP 200，0.43 s** |
| `github.com` | **000，21 s 超时** |

GitHub 的 git 传输和 REST API 是**两个域名**，在这台机器上前者被挡住、后者通。
所以改走 `/git/blobs` → `/git/trees` → `/git/commits` → `PATCH /git/refs/heads/main`
把**同一棵树**写上去，脚本是 `_tools/_attic/scratch/api_push.py`。

**这为什么不是「换了内容再推」：** git 的 tree sha 是**内容哈希**（对每条记录的
路径 + 模式 + blob sha 求哈希），所以脚本在动 ref 之前先断言
**服务器算出来的 tree sha == 本地 `HEAD^{tree}`**（`20c3caba…`）——
对上才证明远端那棵树和本地那次提交**逐字节相同**，而不是「看起来一样」。
再读回来核对：**192 条记录 = 176 个 blob + 16 个目录**，176 个 blob 逐个与
本地 `git ls-tree -r HEAD` 比对，**0 处不同**。

顺带：文件数 **175 → 176**（多的是 `patch_docs_51.py` 自己）。

**留下的一个坑（记下来，下次别当成事故）：** 远端那笔提交是 **`1109d362`**，
不是本地的 `f1aadb6` —— 内容一模一样（tree 相同、parent 相同、message 只差
GitHub 抹掉的一个结尾换行），但作者身份被换成了 GitHub 的
`andypeng1NB <132412750+andypeng1@users.noreply.github.com>`，而且**它那个对象里还有
复现不出来的头**：拿同样的 tree / parent / 作者 / 时间戳手工 `hash-object`，
出来的是 `dd3f8ba`，不是它。所以**下一笔 `git push` 会被判成 non-fast-forward**。
网络通的时候一行解决，**内容完全相同、不会丢东西**：

```
git fetch origin && git reset --hard origin/main
```

同一个脚本随后又推了一笔（本地 `09a93c8` → 远端 `46439ebd`）。**所以这不是一次性事故，
而是这条通道的常态：走 API 出去的每一笔，远端 sha 都和本地不同。**

### 51.7 收口那一行要改一个字：`reset --hard` 会吃掉你手上的新提交

**（2026-09-27，网络恢复后第一次 `git push` 就撞上了。）**

那天 `github.com:443` 又能连了 —— 所以**那个封锁是间歇的，不是「不通」**。
推 `41a7de0` 得到的是正经的 `! [rejected] non-fast-forward`（以前是 21 s 超时），
和 51.6 预告的一模一样。收口这次用的是：

```
git fetch origin                      # efe5775，树 = 229b6eee
git rev-parse origin/main^{tree}      # 229b6eee2d5574e68d3aed6d3a1f551ed4a043e9
git rev-parse HEAD~1^{tree}           # 229b6eee2d5574e68d3aed6d3a1f551ed4a043e9  <- 相同
git rebase origin/main                # 提示 skipped previously applied commit 09a93c8 / 24fb5ca
git push origin main                  # efe5775..205f627
```

**先比 `^{tree}` 再 rebase** —— 树相同才证明 `origin/main` 和自己那个 parent
是同一份内容，rebase 才是无损的；不然就是把别人的提交盖掉。
`git rebase` 还会自己认出 `09a93c8` / `24fb5ca` **「previously applied」** ——
因为它们的**内容**早就在远端了，只是 sha 不同。这条提示本身就是 51.6 那个坑的旁证。

**注意 `reset --hard` 和 `rebase` 不是一回事：** 51.6 写的
`git fetch origin && git reset --hard origin/main` 只在**手上没有新提交**时成立 ——
它把 `main` 直接指到远端，本地那笔就没了。**有本地新提交时用 `git rebase origin/main`。**
51.6 保留原文不改（它是当时那条命令的记录），口径以本节为准。

**顺带一个坑（脚本自己踩的）：** 这台机器的控制台编码是 **GBK**，Python 里
`subprocess.run(..., text=True)` 会用它去解 `gh api` 的 UTF-8 输出。
第一笔推成功是因为那笔提交的 message 全是 ASCII；第二笔在读回时**死在提交信息里的破折号上**
（`UnicodeDecodeError: 'gbk' codec`）。现在一律 `capture_output=True` 拿 bytes、
再手动 `.decode('utf-8')`。

---

## Phase 52 — 世界那一半：控制室开灯、监视器供电、开机链的其余三步  [DONE]

**用户的话：**「那你把现在把那个我们的项目的完整开机流程做了（包括控制室开灯，监视器供电什么的）」。

### 52.1 缺的从来不是逻辑，是「世界」那一半

先把账量清楚：整条开机链**早就完整地在 `Engine` 里**，而且是带闸门的 ——
`monitor_power`（掉电顺手清 `booted`）、`shutters`、`lights`、`mute`、
`boot`（`not monitorPower or not shuttersOpen` → `'Power monitors and open shutters first'`）、
`start`（`not booted or not monitorPower or not shuttersOpen` → `'Complete control room boot first'`）。

六个控件也都在 `workspace.Consoles` 里，**标签**和 `ControlBinder.commandFrom` 逐字对上：

| 标签 | part |
|---|---|
| `ROOM LIGHT BUTTON` | `ALTReactorConsole.ControlRoomSystems.RoomLightButton.ClickPart` |
| `MONITOR POWER BUTTON` | `ALTReactorConsole.ControlRoomSystems.MonitorPowerButton.ClickPart` |
| `CONTROL ROOM SHUTTERS SWITCH` | `ALTReactorConsole.ControlRoomSystems.ShuttersLever.ClickPart` |
| `MONITOR BOOT BUTTON` | `MainReactorConsole.MonitorBootButton.ClickPart` |
| `MASTER START-UP SWITCH` / `MASTER SHUTDOWN SWITCH` | `MainReactorConsole.StartUpBigLever.StartClickPart` / `.ShutClickPart` |

**（注意 `ControlBinder` 是按标签绑的，不是按实例名** —— 所以 grep `RoomLightButton`
在它里面 0 命中，一开始差点得出「压根没绑」的错误结论。）

**缺的是这些开关对世界的后果。** 三个按钮自己**没有 NeonPart**（`VisualFeedback` 地址表末尾记着），
而全 DataModel 里**没有任何脚本**提过 `RoomLights` / `MonitorUI` / `PowerNeon` ——
世界那一半是**当美术做出来、然后没接线**。`RoomShell` 就是那根线。

### 52.2 `RoomShell`：谁写什么

单一写入者，跟 `VisualFeedback` 同一个形状（先 `Initialize` 采引用、再 `Refresh` 按签名门控写）：

| 控制 | 写什么 |
|---|---|
| `ROOM LIGHT` | `RoomLights.ControlRoomLights` 的 20 个 `NeonPart` 的 Color + Transparency，8 个 `LightPart` 上 `SurfaceLight.Enabled` |
| `MONITOR POWER` | 每台监视器 `PowerNeon.Color`、`Screen.SurfaceLight.Enabled`、`Screen.MonitorUI.Enabled` |
| `MONITOR BOOT` + `MASTER START-UP` | 每台监视器**作者画好的那几个画面**里哪一个 `Visible`（`Booting`→`BootFrame`；`Ready`→待机画面 + `PreStartupFrame`；`Starting`/`Running`→`MainMonitorFrame`；`Stopping`/`Report`→`ShutdownFrame`；`Failed`→`ErrorFrame`） |

颜色不是选的，是**量**的（进 `Config.Shell`）：同排**亮着**的兄弟灯格
（`SynthRoomLight` / `CRC1Lights`）都是 `(248,248,248)` 透明 0.25，旁边跟一个 Transparency 1 的
「发射体」壳；而 `ControlRoomLights` 是唯一被作者做成 `(17,17,17)` 透明 0.50 + 8 个 `SurfaceLight`
全关的一格 —— **这两对就是同一份美术的两个作者位置。** Brightness / Range / Face **故意不写**，
每一格保留自己的（0.25 / 32 / Bottom），写它等于**发明光**而不是恢复光。

### 52.3 我犯的三个错，前两个是在场景里改出来的（自动保存已开，所以都是真的）

**① 我把 8 个发射体壳当成灯了。** 采集按 `Material == Neon` 收，把 Transparency **1.00** 的
`LightPart` 一起收进 `lamps`，`applyLights` 于是把它们的 Transparency **从 1.00 写成 0.50** ——
**把看不见的发射体变成看得见。** 改法是**按结构分**（`FindFirstChildWhichIsA('SurfaceLight')`
→ 发射体，只**检查不写**；否则才是灯），并把 8 个壳修回 1.00。
依据：这个 place 里**所有 64 个发射体壳都精确在 1.000**，而颜色各不相同（有 `(255,255,0)`）——
**发射体的外观是灯具设计、不是照明状态**，所以灯能动、它不能。
修完矩阵 12 行全是 `transp=1.00..1.00`，`Initialize: lamps=20 emitters=8 monitors=7`（原来是 28 / 48）。

**② 断电时我没管画面，于是同一个引擎状态留下两个不同的世界。** 原来只在「有电」那支写
`Visible`，断电那支原样不动 —— 我进场景时看到的是**五台监视器停在待机画面、三台停在 `BootFrame`**，
而它们的美术其实是一样的。改成**两支都写**：断电 = 全部 `owned` 画面 `Visible=false`。
现在 `DETERMINISTIC: true`（`Running→断电` 与 `Failed→断电` 结果相同）。

**③（§0.13 那一类）`Initialize` 原来是追加的。** 采引用是这里唯一能被跑两次的东西，追加的话
第二次就把每张写表翻倍 —— 写是幂等的所以**看不出来**，但会白干一整场。改成开头清空三张表。

### 52.4 `Engine` 只动了一个初值

`Reset` 里 `lights` 从 `true` 改成 `false`。**没有动任何闸门、代价或时序。**
理由是**两处互相独立的地方都把冷态作者成「暗的」**：这个 place 存着 `ControlRoomLights`
全 20 盏 `(17,17,17)` + 8 个 `SurfaceLight` 关着，而同排每一格都是亮的；而且**发售版的录像里，
进控制室后第一个动作就是 `CLICK RoomLight`（`EVT2060`）**，紧跟 `LAMPPAL g=0,0,0`。
**原来的 `true` 会让那第一下点击把房间关掉。**

### 52.5 `StateBridge` 第一次「创造」东西

`StateBridge` 本来是**兼容适配器**：只写 place 里已经有的节点。四个开关
（`Lights` / `MonitorPower` / `ShuttersOpen` / `Booted`）`Workspace.Stats` 从来没有过，
所以加了一个 `ensure()` 建 `BoolValue` —— **让它成为开机链留在实例上的痕迹**，
任何东西（包括我）都能读到，而不必去读模块状态（§0.2）。

### 52.6 验证：分成「验到的」和「没验到的」

**验到的（读实例状态，权威）：**

- 六个控件标签逐字对上 `commandFrom`，都在 `workspace.Consoles` 下（所以 `Bind` 会扫到）；
- `RoomShell` 采集 `20 灯 / 8 发射体 / 7 监视器`；
- 12 个手搭状态 → 画面映射全对，读的是真属性；
- **冷态：** 灯 `(17,17,17)`/0.50、8 个 `SurfaceLight` 关、监视器 `(255,0,0)`、`uiEnabled=false`、可见画面 0；
- **通电：** 灯 `(248,248,248)`/0.25、发射体 `Enabled=true`、七台全绿 `(137,255,147)` + 各自待机画面；
- `DETERMINISTIC: true`（12 态里对比得出）；
- **磁盘 ↔ Studio 七个模块逐字节相同**：`cmp` 全 `IDENTICAL`，md5 也对
  （`Config 7548d2efebcb6a180e07186dfe6bca2e`、`RoomShell a9c4e7ab5b8d6ff7495d7e38ad2c3f50`，两边一致）。

**没验到的，说清楚：** 「真的跑起来点一下会怎样」**没验**。这台机器上
`solo_playtest` / `start_playtest` 能起来（`isRunning: true`），但插件**不注册 server peer** ——
`get_connected_instances` 永远只有 `edit`，`eval_server_runtime` 和 `execute_luau target='server'`
一律 `No "server" peer answered`，playtest 里的 `print` 也读不到（见 `CLAUDE.md` §0.16）。
**两个截图工具也都不认我给的相机** —— 两次不同相机位给出**逐字节相同**的画面（§0.14），
所以「开灯前后拍两张图对比」这条也走不通。
**这一轮的验证靠的是实例属性和源码，不是运行日志、也不是图。** 没验的那一半不假装验过。

### 52.7 收尾

- place **还原成作者写的冷态**（灯灭、监视器断电、可见画面 0），相机放回一个正常人看的位置；
- 为截图临时改名的**两个 Model 都改回 `Camera` 了**（§0.14）；
- `_tools/serve.py`（磁盘 → Studio 的字节通道，`receive.py` 的镜像）留下来，
  `allow_reuse_address = False` 是**故意的**（Windows 上重复绑定会静默成功、老进程吃掉流量，见文件里的注释）。

### 52.8 没做、留给用户的（进了 `QUESTIONS.md` 🔴）

**这一段 2026-09-27 被用户当场推翻，原文留在下面当证据。** 我写的「玻璃没有可以量的行程」，
错在**两处**：收的不是玻璃，是 `Workspace.MovingParts.ControlRoom(L/M/R)Shutter` 整个 **Model**；
行程也不是量不到，是用户直接给的 —— **向下 10.58**。我当时在玻璃自己的框里找「上面」的开口，
而行程其实在**旁边的墙里**。几何从来没缺，是搜索方向指反了。裁决与实现见 Phase 53。

~~**卷帘门的玻璃没有可以量的行程。** `Workspace.MovingParts` 里没有、`Geometry` 里没有、
`ReplicatedStorage.CulledParts` 的 **89448** 个后代里 **0 命中**；而框只比玻璃高 **0.32 studs**，
整块收上去玻璃会**浮在自己的框上面**。**量不到就不编。**
控制台那一半（拉杆 + `OfflineLight`）是 `VisualFeedback` 的，本来就好使 —— 缺的只有玻璃本身。~~

---

## Phase 53 — 卷帘门收在哪儿，和一台「只监听、不猜」的房间监视器  [DONE]

用户一句话把 Phase 52 的两半都点了：

> 收玻璃干什么？？收的是 `game.Workspace.MovingParts.ControlRoom`（L/M/R）`Shutter`，
> 需要他下降 **10.58** 个单位，还有**你根本不会做开机**，你写个脚本，
> 就**监听整个控制室内容和腔室内容**

于是这一阶段做了三件事：把行程接上、把监视器写出来、把「我不会做开机」这句话当成结论
而不是情绪 —— 它是**对的**，理由见 53.3。

### 53.1 卷帘门：收的是 Model，行程是 10.58 向下

`Config.Shell.ShutterTravel = 10.58`，`RoomShell.applyShutters` 写的是
**每个 shutter 的 `Frame`**（`Glass` 焊在它上面，动 `Frame` 就是动整扇）。

三个 Model 的实测：三个都关在 **Y ≈ 282.199**，开在 **Y ≈ 271.619**，**Δ 恰好 −10.5800**。
M 那一扇的 `Frame` 旋转是单位阵，只有它的 `Glass` 转了 90° —— 所以位移必须写成
**世界空间**的减法（`closed - Vector3.new(0, travel, 0)`），不能写 `closed * CFrame.new(0,-travel,0)`：
后者沿**自身局部** Y 走，对 M 来说虽然一样是向上，但没有任何理由去依赖「旋转恰好无害」。

几何上为什么是 10.58：`Glass` 高 **10.650**，加上去正好让它的顶边和 **276.7** 的窗台齐平 ——
它不是一个整齐的数，**因为它本来就不是猜的**。

### 53.2 `_tools/room_watch.luau`：只读、不猜、把「没变化」当默认

一份**只读**的单文件脚本（`ServerScriptService.MCP_RoomWatch` + 一个 11 行的
`MCP_RoomWatchRunner` 在旁边 `Start()` 它）。它不 `require` `ReactorBackend` / `Config` / `Engine`，
所以它也能丢进一个没有这些的 place 里，也不会被 §0.15 那种过期 `require` 喂错表。
**它写世界吗？不写。** 全文件没有任何一处对被监视实例的 `=`。

**它监听什么（`rooms.txt` 的原文，43 个根，0 个缺）：**

| 组 | 实例 | 属性 | 根 |
|---|---|---|---|
| **ControlRoom** | 5,089 | — | 8 |
| **Chamber** | 25,053 | — | 35 |
| 合计 | **30,142** | **235,038** | **43 找到 / 0 缺失** |

ControlRoom 的 8 个根：`Consoles`(3,636)、`Monitors`(1,754)、`RoomLights.ControlRoomLights`(84)、
`MovingParts.ControlRoom{L,M,R}Shutter`(各 6)、`MovingParts.ControlRoomMAP{Left,Right}`(各 3)。
Chamber 的 35 个根里最大的几个：`ReactorCBLs`(11,993)、`CoreAntenna`(4,146)、`DecayFields`(3,912)、
`ChamberWalls`(2,800)、六个 `ReactorClamps`(各 451)、三个 `E_VENT`(各 537)、`Core`(344)、
`CHMBRBlastDoor`(212)、六个 `METUSpire`(各 106)、六个 `ChamberFan`(各 94)、
`CoolantPipes`(529)、`CoolantParticleParts`(78)、`FanTriggerParts`(24)、`ISEParticleParts{ ,2}`(各 8)、
三根 `ChamberCoolantPipe`(13/14/14)。

**故意不在里面的：** `HDEF`、`Gravatron`、`Mainframe`、`MES`、`Lounge`、`CRC1-3` —— 用户点名的是
「整个控制室内容和腔室内容」，多收一个房间就是把信噪比还给噪音。

`Script`（16 个）也在表里：**只读它们的属性，不读 `.Source`**，所以那条
「用 `Source` 当指纹会被别人的编辑搅乱」的坑不适用。

**四份产物 + 一份披露**，都推到本机 HTTP sink（`_tools/receive.py`），字节不进上下文：
`rooms.txt`（覆盖，一次）、`inventory.txt`（30,142 行，每个实例一条 + 这个类读了哪些属性，一次）、
`summary.txt`（**有变化才重写**，每个动过的键一行，带当前值 / 起始值 / 变化次数）、
`changes.log`（追加的时间线）、`suppressed.txt`（**被抑制的键的名单**）。

### 53.3 「你根本不会做开机」—— 这句话是对的，而且我有据

不是语气问题。Phase 52 的 52.8 写着「玻璃的行程量不到」，我当时**在玻璃自己的框里**找上面
有没有开口 —— 而行程在**旁边的墙里**。同一个错误在 52.1 里也出现过一次（「缺的是世界那一半」），
两次都是**先读代码、再假定世界**，而不是**先量世界**。
所以这一阶段的产物**故意是一台只读的仪器**，而不是又一个我猜出来的实现。

这台仪器在我自己身上已经抓到三次错，全部是**只有跑起来才会出现**的：

1. **`HoldScans` 那个「到点就判它是事件」的设计是错的。** 第一次跑：90 秒 1,045 行，
   榜首是两个 `ChamberFan`（47 / 46 行）——它们第一次动完之后**静了 32 秒**，
   于是在还没露出真面目之前就被判成了事件。**年龄不是证据，环填满才是。**
   改成「环超过 8 就判 ambient，静够 5 拍就写出去」之后：同样窗口 **232 行**。
2. **抑制不能「先写后擦」。** sink 是**追加**的，第 9 拍触发规则时，
   第 1..8 拍**早就落到盘上了**。run 4 的 `suppressed.txt` 老老实实写着
   `1,891 × 8 line(s) erased`，而 `changes.log` 一行没少（7,557,244 字节 / 15,527 行）。
   擦除在内存里是真的、在盘上是**看不见的**。现在的做法是**扣在手里不写**。
3. **第一次跑环设计时，循环在第一拍就死了，而且死得无声无息。** `releaseQuiet` 对每个键做
   `tick - lastTick[j]`，而 `register` 现在把 `lastTick` 置 nil —— **算 nil 报错**，
   发生在 `task.spawn` 出来的线程里，**没有任何人 await 它**。症状是 `rooms.txt` /
   `inventory.txt` 写完之后**再也不长**，和「在跑但什么也没发生」**长得一模一样**。
   现在 `scan` 外面套 `pcall`，错了就写一份 **`error.txt` 到 sink**，并在 `Status()` 里报 `fatal=`。

第 3 条是 §0.16 那条「运行的那一半验不了」的**正面解法**：不让工具**替我**看，让**脚本自己**留痕。

### 53.4 实测（`Data/roomwatch_run{2,3,4,5,6}` 是失败版本，`Data/roomwatch` 是当前版本）

| 版本 | 窗口 | `changes.log` | 抑制键数 |
|---|---|---|---|
| run 4（先写后擦） | 90 s | **15,527 行 / 7,557,244 B** | 1,891（无效） |
| run 6（到点判事件） | ~180 s | 3,716 行 | 1,9xx（无效） |
| **当前**（环 + 静默释放） | ~150 s | **232 行 / 84,730 B** | **1,943** |

**当前版本这一轮 232 行全部来自 Chamber，ControlRoom 一行没有** —— 因为**没人碰控制台**。
这不是漏收：`rooms.txt` 里 ControlRoom 的 5,089 个实例一个不少地在看，只是**值没变**，
而「没变化不要收集」是用户自己定的规矩。要验控制室那一半，得有人去按。

**抑制是无损的**：`summary.txt` 里每个动过的键**连被抑制的一起**都有当前值 / 起始值 / 完整变化次数，
`suppressed.txt` 逐个点名 —— 所以「不在 `changes.log` 里」永远不会被误读成「没动过」。

### 53.5 这一阶段顺带确认的两条工具事实

- **第三方 `mcp__robloxstudio__execute_luau` 的插件 VM 把 `HttpService:GetAsync` 打成了桩**
  （`pcall` 回 `ok=true, type=nil`，而 `serve.py` 那边**真的**记了 `SENT`），
  于是 `m.Source = src` 会死在 `ProtectedString expected, got nil`。
  **官方 `rblx_execute_luau` + `datamodel_type:"Edit"` 走真 HTTP**（`type=string`）。→ 见 `CLAUDE.md` §0.17。
- **`rblx_start_stop_play(is_start=false)` 是唯一停得掉 playtest 的**（§0.16 旧记）。
  这一阶段每次推源码前都要先停它，因为 `Edit datamodel is not available in Play mode`。


### 53.6 收尾实测（run 8 定稿，run 9 起在跑）

`Data/roomwatch_run8/` 是设计定稿之后那一整趟的记录，`t=3.41s` 到 `t=404.83s`，全程**零操作员输入**：

| 文件 | 数 |
|---|---|
| `changes.log` | **844 行 / 317,769 B**，**844 行全部 group=Chamber，ControlRoom 零行** |
| `suppressed.txt` | **1,942 个键**被判定 ambient（表头 + 每个键一行 = 1,947 行） |
| `summary.txt` | **1952 / 235038** 个属性动过（`t=412.9s`，那一拍扫描 **112 ms**） |
| `rooms.txt` | 43 个根、30,142 实例、235,038 属性，**与 run 6 逐字节相同** |
| `error.txt` | **不存在** —— 扫描循环没死 |

抑制版和 run 4 的 15,527 行 / 7.5 MB 比，是 **~18× 行数、~24× 字节**的收缩，而抑制掉的键数是
1,942 对 1,891（**更多**）—— 也就是说少写出去的不是「少看了」，是「看全了但没写」。

`rooms.txt` 在 run 6 和 run 8 之间**逐字节相同**，这是一条独立的自检：覆盖范围不随运行漂移。

**run 9 已经在跑**（09:46 起，用的就是下面 53.7 推上去的那份 43,920 B 源码），
目的只有一个：**等有人真的去动控制台**，好用同一台仪器记下 ControlRoom 那一半 ——
这是到目前为止唯一**没验过**的东西。

### 53.7 源码同步：disk 43,920 B = Studio 43,920 B

| 方向 | 通道 | 结果 |
|---|---|---|
| disk → Studio | `serve.py`:8773 + 官方 `rblx_execute_luau`(Edit) `GetAsync` | `fetched=43920 before=43806 after=43920` |
| Studio → disk | `receive.py`:8765 + `PostAsync` | `sync8_room_watch.luau` 43920 B |
| 比对 | `cmp` + `md5sum` | **`d34face4d2bbb442000972a91d96dc3c` 两边相同** |

`D:\Lua\5.1\lua.exe` 的 `loadfile` 语法闸也过（`PARSE OK`）。

**顺带量到的目录事实：** readback 落地的其实是 `_tools/_pull/verify/readback/`，不是
`Data/roomwatch/readback/`（后者是早先几轮的位置，已把它和 run 8 一起归档）。
文档里写的路径和使用中的路径不是同一条，是这一轮才发现的。

### 53.8 `.gitignore` 加了 `Data/roomwatch*/inventory.txt`

**七份 `inventory.txt` 逐字节相同**（run2/3/4/5/6/8 + 当前，md5 `5ae9ab97526f39b3fbe530d12f97f6f3`，
各 5,278,228 B）—— 因为它是**同一个世界的快照**，几趟之间没人改过世界。
七份就是 37 MB 的同一个文件，而**没有任何东西读它**：`rooms.txt`（5.7 KB）才是推导出来的答案，
那个**在版本控制里**；这份 dump 重跑一次就有。
所以进 `.gitignore`，不进仓库 —— 文件本身**留在磁盘上**，没有删。
加之前 `Data/roomwatch*` 合计 **81 MB**，加之后进仓库的约 **7 MB**。

**2026-09-27 补测：把十趟归档的 `changes.log`（48 MB 原文）也提交进去，仓库反而变小了。**
`Data/roomwatch_run{2,3,4,5,6,8,9,11,12,13}/` 合计 **47.9 MB** 进版本控制，提交后
`git gc`：`size-pack` **4.01 MiB**，`.git` 从 **9.0 MB 降到 4.2 MB** ——
**降了**，因为 gc 顺手把之前散着的对象也打包了，而这些日志互相 delta 压得极好
（几十万行几乎一样的 `| Chamber | …CFrame |` 行）。
**所以「日志很大」不是不进仓库的理由，`inventory.txt` 那条的理由是「没有东西读它」** ——
`changes.log` 恰好相反：`DECISIONS` 152/153/154 和本节的每一个数字都指名引用它们。
两件事看起来像同一个判断（都带 MB 数），其实是**两个判据**，混起来会同时做错两边。

### 53.9 音频那一半：`Played` / `Stopped` / `Ended` 三个 hook，和一条只有轮询看不见的事实

用户要求：**「哦对别忘了监听音频的播放情况」**。音频是这一阶段加的第二类监听，和属性监听
**不是同一种东西**，所以单独记。

**为什么是事件不是轮询。** 属性监听每 `Interval=1` s 扫一遍 235,318 个属性，那是「现在是什么」；
但一个 0.73 s 长的音效，在 1 s 的扫描间隔里**开始又结束**，两次扫描都看不见它 —— 轮询在
结构上就量不到短音效。所以音频走 `Sound.Played` / `Stopped` / `Ended` 三个信号。
**这三个名字不是查文档查来的，是量出来的**：`rblx_get_http` 那次网络挂了，所以改成让引擎自己
回答 —— 507 个 Sound × 3 个信号 = **1,521 个 hook，`0 refused`**。挂上就是存在。

**监听范围。** 43 个根里的 Sound（**280 个**，与独立探针数的数字**逐个吻合**）走**双路**：
属性监听（`Playing` / `Volume` / `Pitch` / `SoundId` / `Looped` / `SoundGroup`）+ 事件 hook。
另外两个根**只挂 hook、不挂属性监听** —— `SoundService`（8 个子物体里只有 **1 个** Sound，
它是**混音总线**不是场景）和 `Workspace.Sounds`（308 个子物体里 **226 个** Sound，
Phase 47 才搬进去的散件）。合计 **507 Sound / 1,521 hook**。
`SoundGroup` 进属性列表是因为**那七个组名（`EnvironmentSounds` / `Interactables` /
`ControlRoomSounds` / `MESSounds` / `MusicSounds` / `SpecialSounds` / `AlarmSounds`）
是游戏自己的分类**，不是我从 asset id 猜的。

**两个文件。** `audio.txt` 是**时间线**（append，每行一个事件）；`audio_tally.txt` 是**快照**
（rewrite，每个出过声的 Sound 一行 + 按总线汇总）—— 因为前者跑一小时会很长，而「什么都没响」
必须是一句**有出处**的话，不能是一个空文件。

**`Data/roomwatch_run11` 暴露的两个缺陷，和 `run12` 的裁决。** run 11 的 `audio.txt`
只出现 `STOPPED`，**一条 `PLAYED` 都没有**。
有两个候选解释：(a) **hook 看见的是「变化」不是「状态」** —— 挂上 hook 时那个风扇声**已经在响**，
`Played` 这个跳变**在过去**，永远补不回来；(b) `Pitch = 0.00` 说明它**从来没真的开始**，
所以本来就没有 `Played`。**一个样本分不出这两个，所以我写了 `MCP_AudioProbe` 去分**。

探针（临时 `Script`，跑完已 `Destroy`）先普查：43 个根下 **280 个 Sound，23 个 `Playing`，
280 个有 `SoundId`，264 个 `Pitch > 0`**。然后 TEST A 挑一个**停着、有 `SoundId`、`Pitch = 1.00`**
的（`Consoles.ALTReactorConsole.MASS1Systems.PowerLever.LeverUnion.LeverSound`，841 B 的短音效）
调 `:Play()`。**判决：(a) 成立，(b) 被推翻** —— 引擎**看见了**：

```
t=6.08 09:58:04 | ControlRoom | Consoles.ALTReactorConsole.MASS1Systems.PowerLever.LeverUnion.LeverSound | PLAYED  | bus=Interactables | id=rbxassetid://209530691 | vol=0.50 pitch=1.00 looped=false
t=6.81 09:58:05 | ControlRoom | ... | ENDED   | bus=Interactables | id=rbxassetid://209530691 | vol=0.50 pitch=1.00 looped=false
```

**`ENDED − PLAYED = 0.73 s`，正是那个音效的长度** —— hook 那条路整条通了。
（探针自己那行 `Playing 2s after :Play() = false` **不是**「播放失败」：片段 0.73 s，
2 s 之后它**已经播完了**。谁把这一行读成失败，就是把 §0.2 那条假阴性换个地方再犯一次。
`stops=0 ends=1` 也是同一个道理 —— `:Stop()` 打在**已经播完**的声音上，`Stopped` 不该响。）

**修复的两个点。** ① `attachAudio` 挂完 hook 后**读一次 `Playing`**，为真就发一条
`ALREADY-PLAYING` 事件（`audio.txt` 里 23 行），并把 `id` / `bus` 从实例上读下来 ——
于是 hook 的盲区**由属性监听补上**，这正是双路设计存在的理由。② `audio_tally.txt` 加
`# 23 were ALREADY playing …` 那句报表。

**`Data/roomwatch_run13` 又抓出我自己一个缺陷（已修、已验证）。** `audio_tally` 的行过滤写的是
`plays/stops/ends > 0`，而 `ALREADY-PLAYING` 那条路**三个都不加** —— 后果是：
那 23 行**一行都不打印**，`[ALREADY PLAYING AT t=0]` 这个标记是**够不到的代码**，
头部 `# 1 of them have been audible` 少数 23，而**汇总行 `plays by bus: Interactables=1`
把整个环境声底噪说成了零**。改后 `run13`：

```
# 507 Sound(s) hooked; 1521 hook(s) attached, 0 refused; 0 play/stop/end event(s) seen
# 23 of them have been audible; 0 play(s) were caught by the poll and NOT by a hook
# 23 were ALREADY playing when the watcher attached -- a hook cannot see those, and
# their asset and bus were read off the instance instead of off a Played event
# audible by bus: EnvironmentSounds=20  (none)=3
```

23 行全部打出、全部带 `[ALREADY PLAYING AT t=0]`、`plays=0 stops=0 ends=0` ——
**`plays=0` 本身就是「hook 漏了它」的证据**，而「有没有出声」现在按「有没有行」算，
两个问题分开回答，谁也不冒充谁。汇总行也从 `plays by bus` 改名 `audible by bus`，
因为一个 `t=0` 就响着的 loop **贡献不了任何 play**，按 play 汇总是按错的东西汇总。

**顺带量到的一条真事实：23 个里有 15 个 `Pitch = 0.00` 而 `Playing = true`**（另 4 个 0.40、
4 个 1.00）。`Playing` 单看**不等于「听得见」**。这正好是 `Pitch` 进属性列表的理由 ——
游戏大概是靠把 `Pitch` 从 0 推上去**让环境声随着状态变响**，那条曲线只有属性监听看得见。

**盲区（有意不看的，和 43 个根同一条理由）：** `Workspace.MovingParts.Synthesisers.*`
的 286 个 Sound、`Workspace.MonitorsFacility.VitaMonitor{1..4}…Flatline`、
`Workspace.SoundBlocks.MainframeSoundBlock.*` —— 都不在 43 个根里，**一个都不挂**。
`Workspace.Sounds` 那 226 个**挂了 hook 但不在属性监听里**，所以它们的 `Playing`
只能靠 `Played`/`Stopped` 事件推，**没有 t=0 的起始值**。

**哪一半验了、哪一半没验（§0.16）：** 验了的是**工具自己** —— 507/1,521/0 refused、
280 与独立探针逐个吻合、`PLAYED`+`ENDED` 真的落盘、`ENDED − PLAYED` 等于片段长度、
23 行环境声在 `run13` 正确打出、三个 sink 文件在 `run11`/`run12`/`run13` 之间字节级稳定。
**没验的是「操作员动作会响什么」** —— 三趟里没有一只手碰过控制台
（`MCP_AudioProbe` 是唯一的声源，而且它是我）。控制台上任何一个按钮会响什么，
**现在还是空的**，这一条不要写成「已验」。

### 53.10 混音台也要看：`SoundGroup.Volume`，和一个「看起来生效但永远跑不到」的分支

**这一段是从我自己注释里的一句假话长出来的。** `attachAudioOnly` 上面那段注释写着
audio-only 那两个根「their properties do not move, only their playback does」——
这句对**音效库**（`Workspace.Sounds`，226 个 Sound 全是放音用的资产）是对的，
对**混音台**是**假的**：`SoundService` 底下那 7 个 `SoundGroup` 是**每一条总线**，
`EnvironmentSounds` 的 `Volume` 只要被推下去，23 个环境音 loop **照样读 `Playing = true`**，
tally 照样把它们报成「audible」—— **房间已经静了，记录说它还在响**。
这正是这一整套东西最怕的那类错：不是漏读，是**读数正确而结论相反**。

**先量再改。** 现场数出来的：
`SoundService` = **7 个 `SoundGroup`** + 1 个 `Sound`（+ 根自身），
`Workspace.Sounds` = **226 个 `Sound` + 70 个 `SoundEffect` + 12 个 `Folder` + 1 个 `SurfaceAppearance`**。
七个总线的实测 `Volume`：`EnvironmentSounds=1`、`Interactables=4`、`ControlRoomSounds=1`、
`MESSounds=1`、`MusicSounds=1`、`SpecialSounds=0`、`AlarmSounds=0.6` ——
**`SpecialSounds` 已经是 0**，也就是说「总线把声音关掉了」这件事在这个 place 里**已经发生过**，
只是当时没人在看。

**改动三处。** ① `propsFor` 加 `SoundGroup` 分支 → `{'Volume'}`（一个键）。
② `attachAudioOnly` 里非 `Sound` 的现在交给**普通属性监听**（`propsFor` 认就 `register`）。
③ `register` 因为要被**它上面**的 `attachAudioOnly` 调到，按 `buildAudioIndex` 那个老办法
**前置声明** —— 第 699 行从 `local function register` 改成 `function register`，
否则会**再创建一个新的 local**，而上面那个引用到的还是 nil。
**代价量得很清楚**：实例 30,142 → **30,219（+77）**，属性 235,318 → **235,553（+235）**。
**+235 能逐项对上**：7 个 `SoundGroup` × 1 + 33×4 + 16×2 + 8×2 + 7×6 + 3×1 + 3×1 =
7+132+32+16+42+3+3 = **235**。
**顺带发现原来 `Workspace.Sounds` 里那 70 个 `SoundEffect` 一个都没被监听过** ——
它们本来就在 `propsFor` 的契约里（`SoundEffect` 分支早就有，连每种效果的参数都分开列了），
只是那个分支**从来没被走到过**，因为整个库不在属性监听范围里。

**我自己在这一轮里犯的错，记下来因为它太像对的。** 我给 `propsFor` **又加了一个
`SoundEffect` 分支**（返回 `{'Enabled'}`）。它**一行都不会执行** —— `SoundEffect` 分支在
**上面**（第 242 行）已经认领了这个类，Lua 的 `elseif` 从上往下匹配，第二个永远够不到。
它是**死代码，而且长得和活代码一模一样**：名字对、类对、注释还解释得挺像回事。
**判据不是读它，是问「还有谁认领这个类」** —— 一个 `elseif` 链里，同一个 `IsA` 出现两次，
第二次就是死的，这个检查是**纯结构的**，不需要跑。
已删，并在原位留了一句注释说明为什么不能加回来。

**同一轮里第二个「打了但没打印」。** `report.byGroup['Audio']` 我建了、`register` 也往里面
记了类计数，但 `coverageReport` 打印分组时遍历的是 **`GROUPS` 那个具名列表**
（只有 ControlRoom / Chamber），所以 `Audio` 那一组**根本不会被打印** ——
后果是头部说 30,219 个实例，而多出来的 77 个**在任何地方都查不到出处**。
「比上一趟多了 77 个」读起来就成了一件没法解释的事。已改成在 `GROUPS` 之后单独打印：

```
## Audio -- 77 instances OUTSIDE the two rooms, watched as properties
   EqualizerSoundEffect     33
   DistortionSoundEffect    16
   PitchShiftSoundEffect     8
   ReverbSoundEffect         7
   SoundGroup                7
   CompressorSoundEffect     3
   EchoSoundEffect           3
```

**验的（`Data/roomwatch_run15`）：** `error.txt` **没有** —— 这就是前置声明那处**真的绑上了**
的证明（`register` 若是 nil，`attachAudioOnly` 会在第一拍就抛，`error.txt` 会有东西），
比 grep 那句 `function register` 强得多。`rooms.txt` 与 run 14 **只差新增的 `## Audio` 一节**
（`diff` 只有那 9 行），`audio_tally.txt` 与 run 14 **只差时间戳**。
30,219 / 235,553 在 run 14 和 run 15 **两趟逐字节相同**，说明它是确定的、不是抖出来的。

### Phase 53 的 §8 摘要原文（2026-09-27 从 `CLAUDE.md` 搬来，逐字未改）

> 这一节原本住在 `CLAUDE.md` §8。`CLAUDE.md` 是每轮自动进上下文的文件，
> 而这一节是 Phase 53 的跑动细节 —— 每轮都要读的只有「当前在跑什么」，
> 细节属于这里。**搬运不改一个字**，只是换了住处。

**Phase 53（2026-09-27）—— 卷帘门收在 `ControlRoom{L/M/R}Shutter`（向下 10.58），
外加一台只读的房间监视器。** 用户纠正了两处：收的是 **Model** 不是玻璃；行程是 **10.58 向下**
（世界侧独立确认：三个都关在 Y≈282.199、开在 Y≈271.619，**Δ 恰好 −10.5800**，
10.58 正好让 10.650 高的 `Glass` 顶边和 276.7 的窗台齐平）。位移必须是**世界空间**减法，
因为 M 那扇的 `Frame` 转了 90°。`_tools/room_watch.luau` + `_room_watch_runner.luau`
（`SSS.MCP_RoomWatch` / `MCP_RoomWatchRunner`）**只读、不写世界**，监听 **43 个根 / 30,142 个实例 /
235,038 个属性**（ControlRoom 5,089，Chamber 25,053），产物四份推本机 sink：
`rooms.txt` / `inventory.txt` / `summary.txt` / `changes.log` + 一份 `suppressed.txt`。
**抑制是「扣在手里不写」，不是「先写后擦」** —— sink 是追加的，擦除在盘上等于没做
（run 4 的 `changes.log` 真写了墓碑「its first 8 line(s) erased」，run 5 的 `suppressed.txt`
真报了 `# 1942 key(s) suppressed as ambient`，而它的 `changes.log` 一行没少 —— 擦除只在内存里）。
判据是**环填满 = ambient**、**静够 5 拍 = event**；**「到点就判事件」是错的**
（run 6：90 秒 1,045 行，榜首是两个静了 32 秒才动的风扇）。run 8 跑满 **405 s**：
**844 行 / 317,769 字节**，**1,942 个键**进 `suppressed.txt`，`1952/235038` 个属性动过，
一拍扫描 **112 ms**，**844 行全部 group=Chamber、ControlRoom 零行**（没人碰控制台，不是漏收）。
三次错全部只有跑起来才看得见，第三条让它现在**自己写 `error.txt`**。
**音频走另一条路：`Sound.Played/Stopped/Ended`，507 Sound / 1,521 hook / 0 refused**
（三个事件名是**量出来的**不是查来的）。理由是 0.73 s 的片段在 1 s 轮询里**开始又结束**，
轮询**结构上**看不见；代价是 **hook 看见的是「变化」不是「状态」** —— t=0 就响着的 23 个环境声
**永远发不出 `Played`**，所以挂 hook 时**另读一次 `Playing`** 补上（`ALREADY-PLAYING` 行）。
探针判决：停着且 `Pitch=1.00` 的音效 `:Play()` → `PLAYED t=6.08` / `ENDED t=6.81`，
**差 0.73 s = 片段长度**，hook 整条通。**23 个里有 15 个 `Pitch=0.00` 而 `Playing=true`** ——
`Playing` 单看**不等于听得见**，这就是 `Pitch` 进属性列表的理由。
**混音台也看**：7 个 `SoundGroup` 的 `Volume` 进属性监听（`SpecialSounds` 实测**已经是 0**）——
`Playing` 为真而总线被调零，是这套东西最怕的那类错：**读数正确而结论相反**。
代价 **+77 实例 / +235 属性**（30,219 / 235,553），逐项对得上。产出 `audio.txt` 时间线 +
`audio_tally.txt` 快照（含 `audible by bus` 汇总）。**`Data/roomwatch*/inventory.txt` 七份
逐字节相同（md5 `5ae9ab97`），已进 `.gitignore`** —— 盖的是同一个没变过的世界，`rooms.txt` 才是答案。
**`QUESTIONS.md` 现在有一条待你拍板的：D11（这两个 SSS 实例留在发版里还是删）。**

---

## Phase 54 — 监听**原游戏**：一份先普查、后记账的开机记录器  [DONE — 本机验过，原游戏还没跑]

**这一轮的起点是一次更正。** Phase 53 那台房间监视器是照 **AIRemake**（placeId
`83752844701736`）做的，而用户 2026-09-27 说的是：

> 我说的整个控制室+核心腔室+音频监听是监听原游戏的，又不是现在的，（目的为了让你知道开机做什么

所以三件（控制室 / 核心腔室 / 音频）全部**重新对准原版**（placeId `17596243941`），
而且**目的是语义的**：`你根本不会做开机` —— 这台东西的产物要能回答「开机到底做了什么」，
不是「有没有东西在动」。

### 54.1 为什么不是把 `room_watch.luau` 改个根就完事

`room_watch.luau` 的根是**写死**的：`ControlRoom` / `Chamber` 五个具体路径。那是**在我们自己的
place 里**量出来的，因为那个 place 我们全部看过。**原版我一次都没看过** ——
写死一组根等于把我的猜测当事实，而猜错了的后果是**静默的**：根不存在就是零行，
「没事发生」和「根名写错了」在输出上长得一模一样，这正是 §0.16 那一类错误。

于是这台东西**先普查、再选根**：
1. 列出候选根（`workspace` 的直接子物体 + 几个服务）；
2. **按实例数从小到大**取，直到 `TotalBudget = 80000` 为止 —— 从小的开始是**故意的**：
   先拿到「小而可能有意思」的容器，而不是让一个 4 万件的巨物把预算吃光；
3. **把选择过程本身写成产物**（`rooms.txt`）：谁进了、谁没进、**为什么**（
   `over PerRootBudget (30000)` 之类），以及被跳过的根**往里钻一层**列个梗概，
   让「没被监听」和「不存在」区分得开。

### 54.2 产物

一份单文件、**只读**、注入即用（不 `require` 任何东西 —— 原版里没有我们的模块）：

| 文件 | 内容 |
|---|---|
| `tree.txt` | 普查：路径、类、实例数 |
| `rooms.txt` | 监听范围 + **选择规则** + 跳过原因 + 被跳过根的钻探 |
| `inventory.txt` | 被监听的实例与属性清单（一条 `path | prop` 一行） |
| `summary.txt` | 每个被监听属性的当前值、原始值、变化次数 |
| `changes.log` | **时间线**：`t=` 定宽 + `\| group \| path.prop \| old \| new` |
| `suppressed.txt` | 判为 ambient 而被扣下的键 + **判据** + 以 discrete 放行的**条数** |
| `audio.txt` | 播放时间线：`PLAYED` / `STOPPED` / `ENDED` / `ALREADY-PLAYING` |
| `audio_tally.txt` | 音频快照 + `audible by bus` |
| `error.txt` | **只在它自己死掉时**写 —— 它自己报告自己的死因 |

热键：`RightShift` 立刻把所有文件推一遍，`RightControl` 停。
重新注入会**先停掉上一台**（`_G.TRG_ORIGINAL_WATCH` 守卫），不会两台抢同一个 sink。

### 54.3 这一轮真正值钱的，是验的过程里翻出来的四个错

**① `judged` 是个只写不读的变量 —— 而 `summary.txt` 一直在替它说话。**
`judged` 在 286 行声明、723 行清空、1181 和 1253 行各写一次，**没有任何地方读它**。
而 `suppressed.txt` 的表头写着「A key that IS in changes.log was judged the other way:
it went quiet long enough for its held lines to be written out」—— **一句话描述了一个
从没被算过的判断**。（这跟 DECISIONS 159 是同一类：**写了没人读**，和**读了走不到**互为镜像。）
已加 `judgedCount()`，且**刻意排除同时是 ambient 的键** —— 不然这个数会对读者找不到的键
说「已记录」。现在表头是真话，而且这个数**成了 `releaseQuiet()` 唯一的可观测面**（见 ②）。

**② 「这一行在文件里」不等于「这一行是被放出来的」。**
`Watch.Report()` 每 30 拍调一次 `drainHeld()`，把**任何还扣着的环全部倒出来**。
所以「把整个静默放行规则删掉」**不会让任何一行从 `changes.log` 里消失**，
只会让它们**晚 ≤30 拍**到 —— 所有产物逐字节相同（时间戳除外）。
**变异测试就是在这里逮到我的**：M1（静默放行永不触发）第一版断言的是
「the discrete key reached changes.log」，结果它**不变红**。查下去才发现
`releaseQuiet` 的保真度只体现在**延迟**上，而盘上没有任何东西记录这个差异。
修法不是改断言，是**让差异可观测** —— 即 ① 的计数器。改完之后 M1 才真的红。

**③ 第四处前置声明。** `judgedCount` 定义在 `suppressedReport` **下面**，
所以 `suppressedReport` 里那句调用编译成**全局读取** → nil → 第一次要报告就抛
（`attempt to call global 'judgedCount' (a nil value)`）。
**这次不是跑挂了才发现：是 harness 第一次跑就报了**，因为它在同一拍就要求了
`suppressed.txt`。这是把「跑一次要 405 秒、出错只能看 `error.txt`」的东西
放进 120 拍的桩里的全部意义。

**④ `--dump` 传了等于没传。** harness 的参数解析（48 行）正确设了 `DUMP = true`，
但落盘那段判的是 `arg[1] == '--dump'` —— **带路径参数时 `arg[1]` 是路径**，
于是 `lua watch_harness.luau <mutant> --dump` **静默不写任何文件**，
而空目录读起来像「这个变异体没有产出」，不像「这个开关被忽略了」。
是**想做基线/变异体产物对拍**的时候撞出来的 —— diff 把每个文件都报成不同，
因为有一边根本不存在。现在判 `DUMP`，并支持 `--out=DIR`。

顺带两处早先已修、这里记全的：`rooms.txt` 表头曾写「0 root(s) skipped」而正文列着
`Facility`（读的是从没被写过的 `report.skipped`，该读参数）；`changes.log` 曾按
**释放顺序**而不是**移动顺序**输出（一次释放十几个键时按 `pairs()` 走）——
对一个**存在的全部意义就是开机的先后**的文件来说这是硬伤，已改成
「tick 跟着每一行走」+ 每批按 `(tick, key)` 归并排序。时间戳同时改成定宽
`t=%010.2f`，否则 `sort changes.log` 会把 `t=10.20` 排到 `t=9.50` 前面 ——
**排序工具静默搞乱，比不排序更坏**。

### 54.4 验的 / 没验的，分开写（§0.16）

**验过的（本机，`bash _tools/run_tests.sh` 全绿）：**
- `watch_harness.luau`：把一个合成的 Workspace（含 4 万个 Pipe 的巨物、一个没有信号的
  `BlindBlip`、两个开局就响的环境声、一个中途 `Destroy` 掉的部件）喂给**出厂的那份**
  watcher，**43 PASS / 0 FAIL**；`--boom`（让一次属性读取抛错）**4 PASS / 0 FAIL**，
  断言 `error.txt` **被写出来**且带 tick 和错误本身。
- `selftest_watch.py`：**13 个变异，13 个全部按预期变红**，且每个都另配一条
  **必须保持绿**的断言 —— 否则「把 watcher 砸烂」也能满足「目标断言变红」，
  什么也没证明。基线 43 条全绿，出厂文件 md5 全程未变
  （`88ab0fdac69a9e325084e32dc03ca3b1`）。
- 变异的锚点**每条都断言在源码里恰好出现一次**（§0.13）；不唯一就报**测试自己坏了**，
  不跳过。

**没验的：它一次都没在原版里跑过。** 原版我进不去（MCP 够不着，
Solara 要在客户端里手动注入），所以以下全部**是设计意图，不是观测**：
- 普查选出来的根**是不是**控制室和核心腔室；
- `80000` 的预算在原版**够不够**（我们自己的 place 30,219 实例 / 235,553 属性 / 112 ms
  一拍是量过的，原版的规模未知）；
- 原版有没有**同名重路径**、有没有把 `Sound` 藏在 `ReplicatedStorage` 里
  （`attachAudioOnly` 特意**只认** `SoundGroup` / `SoundEffect` / `Sound`，
  就是为了走进去时不把每个模板都变成被监听的键 —— 这条有 harness 覆盖，但覆盖的是桩）。

跑起来之后**第一件事是读 `rooms.txt`**：那里会直接写出它选了哪些根、为什么、
跳过了谁。如果选错了根，`rooms.txt` 会明说，而不是给一个安静的空文件。

### 54.5 怎么跑（两条命令）

```
python -m http.server 8766 --bind 127.0.0.1 --directory _tools
```

然后在**原版游戏**里、**进了班次之后**，用 Solara 执行：

```lua
loadstring(game:HttpGet('http://127.0.0.1:8766/TRG_original_watch.luau'))()
```

sink（8765）**已经在跑**，不用另起。两个热键：`RightShift` 立刻催一遍，`RightControl` 停。

**注意注入时机**：`ALREADY-PLAYING` 那一批**只在注入那一拍读得到** ——
开局就响着的声音**永远不会**发出 `Played`（DECISIONS 157）。
所以**要抓开机就趁开机前注入**，进了班次再注入等于把开机那一段让掉。

### 54.6 两个脚本一起跑：热键撞了，注入前修掉

用户 2026-09-27 决定**采集器和监视器一起注入**（同一次开机），问「注入器那边怎么说」。
照着回答之前先对了一遍两个脚本**共用的三处**：全局变量、输出路径、热键。

- **全局变量：不冲突。** 采集器只用 `getgenv()` 取 `request`（执行器的 HTTP），不设守卫；
  监视器的守卫在自己的命名空间 `_G.TRG_ORIGINAL_WATCH`。
- **输出路径：不冲突。** 同一个 sink（8765）、不同子目录 ——
  采集器 `Data/flow/original_<stamp>/`，监视器 `Data/originalwatch/<stamp>/`。
- **热键：撞了，而且是最坏的一种撞法。** 采集器 `SealKey = RightShift` = **封存并结束这一趟**；
  而监视器当时也把 `RightShift` 绑成「立刻把所有文件推一遍」。
  两个脚本在同一个会话里、**这一次开机只能花一次** —— 于是
  「我想催一下监视器」按下去，**实际是把采集器的文件封了，那一趟就白瞎了**。

**这个错，两边的测试都看不见。** 监视器的 harness 看不见：这个键在人按之前什么都不做，
而它做的事**发生在另一个脚本里**。采集器的测试也看不见：在它自己那个文件里，
`RightShift` **完全按写好的那样在工作**。两套测试在这个组合下**全绿**。
它长在两个**各自都正确**的程序接缝上 —— 这一类缺陷，把任何一个程序单独测到死都够不着。

**修法是监视器让路，而让路的理由是不对称。** 监视器那个键是**方便**
（想早点拿到文件就按一下，不按就等下一个汇报拍）；采集器那个键是**承诺**
（按一下这一趟就结束了）。两个功能抢同一个稀缺资源时，
**主张更弱的那个退让** —— 这是「每个键是什么意思」的性质，不是谁先写的。

**顺手加了防回归的检查**，而它故意长得很怪：**读监视器的源码**，
源码里出现 `KeyCode.RightShift` 就红。这不是在测行为 —— 但**恰恰是这里该用的工具**，
因为要守的性质是「这个文件不声称拥有这个键」，那是**文本的性质**。
行为测试得先按一个键、再跑到另一个程序里去看损失。

**产出的检查**：`watch_harness.luau` 新增 `the watcher does not steal the recorder's seal key`，
**43 → 44 PASS**。监视器 79,588 字节，md5 `338c985c298b9cd17db68b5b925dc1a4`，
13/13 变异仍全部按预期变红。

**同一天顺手撞出来的第二条**：`8766` 起不来/连不上的时候，用户看到的是
**「拒绝连接」**。这台机器上探测到的是 **TimeoutError 而不是 RST**（Windows 防火墙丢包），
所以浏览器说 refused、脚本说 timeout，**是同一件事的两种表现**：
那个端口上没有任何进程在听。修完之后 8766 发的字节数与磁盘**逐字节相同**（79,588）。

### 54.7 D11 拍板：Phase 53 那台机器撤了（2026-09-27）

**这节是 §54.1 那次更正的收尾。** 方向既然错了，Phase 53 留在 **AIRemake** 里的
`MCP_RoomWatch` + `MCP_RoomWatchRunner` 就没有用户了 —— 你答的是 **D11:B**，
理由是一句话：

> D11:不用吧，采集的是原游戏里面的

**执行：** 两个实例已从 Edit 模式的数据模型删掉。事后独立读回
`SSS children = 3`：`MCP_LampProbe` / `MCP_FlowCollector` / `ReactorBackend` ——
**删的只有 Phase 53 那对**，两个 MCP 探针按先前定下的规矩留着。

**删之前先把「代码不丢」证掉，而不是假定 `_tools/` 里有：**
在 Studio 里 `HttpService:GetAsync('http://127.0.0.1:8766/room_watch.luau')`
把**磁盘那一份**读进**同一个 VM**，和 `ModuleScript.Source` **逐字符**比，
回 `IDENTICAL, 68907 chars` / `IDENTICAL, 462 chars`。
**只比长度不算数** —— §0.0 记着「长度相同而内容不同」在这个工程里真实发生过。
再 `rblx_script_grep "RoomWatch"` 扫全 DataModel：命中**只有这两个文件自己**
（`RoomWatch.Snapshot` / `RoomWatch.Start` 那些自引用），**没有第三方绑定**，
所以删掉不会让别的脚本变成哑的 —— 这正是 §0.12 第 2 条那条纪律要求的检查方向。

**那两个数字是有时间戳的，写清楚：** `462` 是**删除那一刻**磁盘上
`room_watch_runner.luau` 的字符数。删完之后我往那份文件的头注释里补了一段
「**2026-09-27 起不再安装**（D11:B）」+ sink 端口是 **8771 而不是 8765** 的提醒，
于是它现在是 **916 字节**、md5 `350fff2fcbc10800a35be5518a0455b8` ——
**所以「逐字符相等」这条从那一刻起对 runner 不再成立**，它是一次**已完成的**比对，
不是一条**还成立**的不变式。5.1 parse 过了。（`room_watch.luau` 没动，
仍是 68,907 字节 / md5 `40508436741174919539ef0361eb9c84`。）

**没有违反 §1.4 第 2 条**（不要在没有替代品的情况下删除功能）：替代品就是那两个文件本体，
`room_watch_runner.luau` 的注释里写着装法，重新注入就回来。**丢掉的只是「默认常驻」这件事。**

**代价，分清楚写（§0.16 那条纪律）：**
- **失去的**：AIRemake 这个 place 里「跑起来的游戏发生了什么」又回到读不到的状态。
  以后要看得重新注入，并且**得先起 sink**（`room_watch.luau` 的 `CONFIG.Sink` 是
  `127.0.0.1:8771`，和原游戏那套的 8765 是**两个不同的端口**，别混）。
- **没失去的**：`_tools/room_watch.luau` / `room_watch_runner.luau` 两个文件、
  `Data/roomwatch*/` 那七份产物、以及 `PROGRESS.md` Phase 53 里 run 1..15 的全部数字。
- **顺带**：停 playtest 时那个 Team Create 复现提示的来源**推断**只剩两个探针 ——
  **没实测过还弹不弹**，等下一次停 playtest 才知道，`QUESTIONS.md` 里记的就是「推断不是结论」。

---

## Phase 55（2026-09-27）—— 卡顿的仪表，和玩家 GUI 采集器

**这一轮的活是你一句话派下来的：**

> 好了，但是有个问题啊，太卡了，还有你在加个功能，收集玩家的GUI数据

拆成两半写。**哪一半验了、哪一半没验，分开说**（§0.16）。

### 55.1 「太卡」这一半：先量，再改，别凭感觉改

**量的是你自己跑完的那一趟**：`Data/flow/original_260927-111843`
（513,073 字节，430 samples，封存完整，`postfails=0 spilled=0 dropped=0`）。

| 读数 | 值 | 出处 |
|---|---|---|
| 轮询实际频率 | **1.66 Hz**（平均 602 ms；标称 4 Hz = 250 ms） | `S 2` t=5.22 → `S 430` t=263.11，428 poll / 257.89 s |
| （含开头那一段的话） | 1.63 Hz（612 ms） | 430 poll / 263.11 s —— 第一拍里含脚本启动 |
| `dt` 最小 / p50 | **266 / 316 ms** | S 行的 `dt=` |
| `dt` p90 / p99 / 最大 | **1422 / 1802 / 2220 ms** | 同上 |
| 有变化的键 | 133 个 | 去重后的变化键 |
| 每条 S 行的变化对 | **17.3**（2610 对 / 151 行） | `MaxPairsPerLine=240`，一次都没触发分块 |
| 其中 `t.` 读数文本占 | **2277 / 2610 = 87%** | 变化对按前缀分类：`t.` 2277、`m.` 172、`s.` 159、`q.` 96 |

**`dt` 的读法要小心，这里是我自己先读错了一次的地方：** `lastPoll = now` **每一拍都写**，
但 `dt=` **只在有变化的那 151 拍上打印**（S 行只在 `#changed > 0` 时才存在）。
所以那组百分位是**以「这一拍有变化」为条件**的样本 —— 而「有变化」和「这一拍很长」是相关的
（拖得久的一拍更容易攒出变化），**它偏向长尾**，不是全体拍数的间隔分布。
**全体拍数的数字**只能从两端的 `t=` 拿：`S 2` 到 `S 430` 之间 428 拍走了 257.89 s，**602 ms/拍**。
**最大值 2220 ms 属于 `S 2`**，它的前一拍里含脚本启动，所以那个最大值不代表稳态。

**`dt` 最小 266 ms 仍然是决定性的**：某一拍确实在 266 ms 后接了下一拍，
**所以这个循环能跑到目标附近，它是被饿着的，不是天生就慢。**
（反过来不成立 —— 因为 `dt` 只在有变化的拍上打印，全体拍数里的最小值只会 ≤ 266，
这条只能当「可达」的证据用，不能当「常态」的证据。）

**输出路径也排掉了**：只有 133 个变化的键、每行 17.3 对、一次分块都没发生，
`dropped=0 spilled=0 postfails=0` —— 成本在**读**，不在**写**。

**我先前那份「热点排序」错了，错在拿错了游戏的零件表。** 我当时按
`readLamps` 约 8 次分配 × **1,000 盏灯** × 4 Hz ≈ 32,000 次/秒 把它排在第一，
那个 1,000 是 **AIRemake** 那边的 `NeonPart` 数。**原版自己的文件是这么说的**：

| 读数 | 值 | 说明 |
|---|---|---|
| `z.parts` / `z.systems` | **28 / 20** | 灯矩阵一共 28 个部件 —— 不是 1,145 |
| `STATADD` | **38** | `Workspace.Stats` 只有 38 个值 |
| `READOUTS found` | **1115** | 每个 poll 要走 1115 个标签 |
| `readouts`（收据） | 1157 | 跑到封存时的记录数 |

**所以真正的大头是 readout 走查** —— 1115 个标签／poll，实测 1.66 Hz 下约 **1,850 次
读取+模式匹配／秒**（标称 4 Hz 的话是 4,460），**灯（28）和 Stats（38）都是可以忽略的量级。**
S 行的变化对分布从另一头印证了同一件事：**2610 对里 2277 对是 `t.`，87%** —— readout
不只是最贵的读，也是最多的写。
**这条更正比任何优化都重要：一个按错误零件表算出来的热点排序，越精确越像勤奋。**

**加进去的是仪表，不是猜测** —— 一律 `os.clock`，每 `Config.PerfPolls = 240` 个采样报一次：

```
PERF polls= hz= read_ms= pass_ms= flush_ms= wall_ms= cpu_pct= read_pct= worst_ms=
```

- `read_ms` 是**读**占的（`perfReads` 在 emit 工作**之前**关掉，所以「读贵」和「写贵」
  分得开，两者的补救办法不一样）；
- `pass_ms` 是整个 poll 占的；`flush_ms` 是 `flush()` 占的（它里面有 HTTP，
  是唯一会阻塞的调用）；
- `hz` / `wall_ms` 是**客户端给了多少**。**`dt` 长一件事说明不了两件事**
  —— 「采集器吃了这一帧」和「客户端本来就在卡」在 `dt` 上长得一模一样，
  这正是要把两组数分开的原因；
- S 行的行首多了一个 `rd=`（这一拍读了几毫秒），那样单拍的长尾也能归因。

**顺手做的两处等价改写**（都是**先证明等价**再改，不是「看着更快」）：

1. `packedColor` —— `readLamps` 原来每盏灯每拍拼一个 `"r,g,b"` 字符串，
   3 次字符串分配 + 2 次拼接 × 每盏 × 每拍。**那个字符串唯一的用途是当表键**，
   文件里从来没有它。现在打包成一个整数，图例（`LAMPPAL`）需要时再从整数拼回来。
   （灯只有 28 盏，所以这一条**省得不多** —— 改它是因为它严格更省，不是因为它是瓶颈。）
2. `readReadouts` 先选分支再 `gsub` —— 那个 `gsub('%s+',' ')` 原来**无条件**跑在
   每一个标签上，而它的结果只在 `num == nil` 那一支被读。**先 `match` 再决定**
   不可能改变答案：被删掉的那个值在这条路径上从来没有人读。
   （同一份文件里 TEXT=1126 条，所以这一条省得也不多 —— 同上。）

**没动的是** readout 走查里那句 `tonumber(raw:match('([+-]?%d+%.?%d*)'))`：
每拍每个标签一次，是剩下最大的一笔，但把它换成先 `tonumber(raw)` 会在
**`"0x10"` 这类字符串上改变行为**（Lua 5.1 的 `tonumber` 认十六进制，模式不认），
而**采集器一趟只能跑一次**。**用一个没验证过的等价性去换速度，是拿一趟数据赌。**
先看 `PERF` 的数字。

**必须说清楚的一条：这一半的「卡」是**假设**在采集器身上的。** `dt` 长自己证明不了
是采集器造成的，`PERF` 就是为了把这件事分开才存在的。**在你有 PERF 数字之前，
不要把「已优化」当成「已解决」。**

### 55.2 收集玩家 GUI 数据（`g.*`）

**为什么这件事只能采集器干**：`PlayerGui` **只在拥有它的客户端里存在，什么都不复制**。
服务端看不见它，`room_watch` 那一路（对着服务端）也看不见它。**只有注入到客户端里的
脚本**能看见 —— 也就是这份采集器，而它一趟只能跑一次。

**两个命名空间，故意分开，因为「一个事实只有一个写入者」是这工程的硬规矩：**

| 键 | 内容 | 谁来读 |
|---|---|---|
| `g.<key>` | 对象**自己**的旗标（GuiObject 的 `Visible` / ScreenGui 的 `Enabled`） | 本模块，每拍一次读，变过才写 |
| `t./x.<key>` | 标签的**文字** | **交给上面那套 readout 走查**（走查已经有 chatter guard、TMAP、ANIM/NOISY 裁决） |

**第二条是关键的取舍**：玩家屏幕上的标签文字**不在这里读**。
在这里再建一套「读文字 + 去抖 + 判颤抖」就是**同一个字符串有两个意见**
（§4.3 第 2 条），而那套机器已经存在而且测过了。

**旗标是**探**出来的，不是按类名猜的** —— 2026-09-27 在 Studio 里量的：

| 类 | `Visible` | `Enabled` |
|---|---|---|
| `LayerCollector`（ScreenGui / SurfaceGui / BillboardGui / GuiMain） | **抛错** | 可读 |
| `GuiObject`（Frame / TextLabel / TextButton / TextBox / ImageLabel / ViewportFrame / CanvasGroup / ScrollingFrame） | 可读 | **抛错** |

**没有任何一个类两个都答，而且问错的那个不是 `nil`，是 error。** 所以
`IsA('LayerCollector') and ... or ...` 今天正确、**明天加了新类就静默错**，
而错的代价不是一行坏数据：`readGui` 抛 → 整个 `pollOnce` 抛 → **那一趟什么都不记**。
于是 `flagReaderFor(d)` 用 `pcall` **每个对象在 rebuild 时探一次**（不是每拍），
**两个都不答的对象直接丢掉并计数**，不猜。

**采集器自己的面板按血缘排除，不按名字**（`isOwnGui`）：面板每拍改自己的文字四次，
把它录进来就是**录自己**，而且 readout 的 chatter guard 迟早会把它判成 `NOISY` ——
文件里就会出现一条**骂自己家标签**的投诉，长得像一条关于游戏的发现。
按血缘而不是按名字，**改名字放不回来**（harness 的 G3 就是验这个）。
`isOwnGui` 是这一节**唯一一个前向声明**：只有函数必须在定义之前可见，
`local` 只要存在就行（这个区别本工程丢掉过一晚，状态块里写着）。

上限 `MaxGuiObjects = 600` / `MaxGuiLabels = 400`，**计数和溢出分开报**：
「600 个对象」和「至少 600 个对象」是两条不同的结论，只有一条说明记录不完整。

产物：`gm.objects= over= unreadable= labels= label_over=` 每拍一行，
外加每个新键一条 `GMAP`（`g.` 键出现在变化行里而在整份文件里找不到 `GMAP`，
就是一个没人认领的布尔 —— 和 `TMAP` / `LAMPMAP` 存在的理由一样）。

### 55.3 验的是一份**会抛出错的 mock**，不是一份方便的 mock

`_tools/build_gui_test.py` 从**发出去的那份** `TRG_original_recorder.luau` 里
**按文本抽**两个区块 + `keyForLabel`，写成 `_tools/_gui_states.luau`。
**一份都不在这里重新声明** —— 一个跟自己抄的副本一致的 harness，证明不了发出去的那份。

mock 里的 `Visible` / `Enabled` **不是字段，是会抛错的 metatable 分支**，
按上面那张表精确地抛 —— 引擎就是这样的。**一个回 `nil` 的 mock 会让错的读取器
在这里通过、在游戏里死掉。**

**39 条 PASS / 0 FAIL。** G9 数的是**属性读取次数**（`FLAG_READS`）而不是计时：
`readGui` 一拍恰好每个记录读一次旗标，rebuild 每个对象摊到 1～2 次探针 ——
**「一拍一次」是这个设计成立的全部理由，而被数出来的代价不是被声称的代价。**

`_tools/selftest_gui.py`：**10 个变异，10 个都在指定的那条断言上红了，发出去的那份
md5 没动。** 其中三个是这一节的设计本身的守卫：
- 「键只取标签名」→ G5 红（两个同名标签合成一个，其中一个从此不再报变化，**静默**）；
- 「只排面板的直接子物体」→ G3 红（差一层血缘就漏进去了，正是 §0.12 那条纪律）；
- 「每拍把旗标沿血缘解析成**有效**可见性」→ G10 红 —— 这条是**故意钉住这个设计**的：
  `g.` 记的是对象自己的旗标，**不是**玩家能不能看见；**把它「修好」成有效可见性
  会让每一拍多一次祖先读取，那是这整个设计要避免的那笔账。**

`bash _tools/run_tests.sh` 全绿：两份文件各自 5.1 解析、5 个 builder、5 个 harness、
watch 44 PASS、watch --boom 4 PASS、watch 变异 13/13、gui 变异 10/10。

### 55.4 顺手翻出来的：187 个重复的 readout 键，和 12 个被冤枉的标签

**这不是这一轮要做的活，是加仪表的时候顺手读到的，但它比优化重要。**

原版那一趟自己的 `READOUTS` 行写着：

```
EVT1118 READOUTS found=1115 distinct=928 monitors=yes consoles=*Label
```

**1115 条记录压在 928 个键上 —— 187 个键是重复的。** 而 12 条 `ANIM` 行
**每一条的措辞都是 `moved 5 times`**（`5 = Config.AnimChangesPerPoll + 1`，
一次都没有 6 或 7）：

```
EVT1267 ANIM ...DisconnectFrame.Frame.Frame.TextLabel moved 5 times inside one poll; dropped as an animation
```

**这 12 个标签被当成「一拍的动画」丢掉了，而那句话不是真的。** 理由：
`st.thisPoll` **每拍在 `readReadouts` 结尾清零**，一个 poll 里每个记录只 +1，
所以**正常情况下它永远到不了 5**；它到 5，只能是**同一个键上挂了 ≥5 条记录**，
一个 poll 里被加了 5 次。**187 个重复键是文件自己报的数，不是我从别处推的。**

**那个 `5` 本身是可读的，而且它读出来的是「几条记录」**：`st.thisPoll = st.thisPoll + 1`
在**每个记录**上各跑一次，而 `st` 是按 `rec.key` 取的 —— 所以同键的记录**共用那个计数器**，
它数的是这个键上挂了几条记录。12 条全是 `5` 而不是 6 或 7，是因为 `> 4` 在**头一拍**就触发、
紧接着 `st.dead` 关掉这个键（后面的记录再也进不来）—— **所以这 12 个键各自恰好有 5 条记录**，
不是「很多条」。187 条重复里，**48 条来自这 12 个键**。

`buildReadouts` 里那对守卫（`seenLabel[label]` 按实例、`seen[key]` 按键）
**按读起来的样子是堵死的**，而文件说没堵死。**我没能靠读源码定出它漏在哪，
所以我不写「因为 X」。** 见 `QUESTIONS.md` **P6**。

**代价是要说清楚的：** `st.dead = true` 之后那个键**整趟不再被读**，
所以这 12 个监视器/控制台读数**是从记录里消失了的**，
而文件里留下的那句话把锅推给了游戏的动画。

### 55.5 顺带纠正一个**关于文档自己的**数字：40.0K 那一关数的是**字符**，不是字节

写这一节的 §8 摘要时我按「`CLAUDE.md` 39,553 **字节**，离 40,000 只剩 447」去压缩，
并且真删了几段——**这个数读错了**。§0.0 自己给了同一份文本的两个计量：
**整份是 45,050 字符**（第 53 行，报警的门槛），而模块报出 `(62580, 2b6be228)`
（第 87/100 行，那是 Lua 的 `#s`，**字节**）。同一份文本 45,050 与 62,580 并存，
**只能是码位 vs 字节** —— 所以**报警数的是 Unicode 码位**，45,050 > 40,000 才对得上。

**当前 `CLAUDE.md` 是 22,269 码位**（39,624 字节），离那一关还有 **17,731 码位**，
根本不需要压缩。压缩本身**没有损失**（被删掉的每一段都在 `PROGRESS.md` 里有更全的版本，
核对过：D11 的验证细节在 §8 自己的 D11 段、Phase 51 的分档数字在 51.2/51.3、
Phase 47 的数字在 47），但**它是我按一个错的计量做的决定**。

**新规矩：文档的体量以模块报出的那一对 `(字节, 哈希)` 为准，要不要压缩看码位。**
两个都能量，**别拿字节去过一个按码位设的门槛** —— 这是同一类错误在文档层的版本：
拿错单位的数字，越精确越像勤奋（同 §55.1）。

## Phase 56（2026-09-27）—— 把「警报」钉进监视器，把 sink 的目录掰正

**一句话：** 用户给了两条只有他知道的事实（警报在 `game.Workspace.Alarms`；其中一员叫
`ReactorALARM`），据此给监视器加了 `Pinned = {'Alarms'}`；顺手把 8765 的 `--dir` 从
`_tools/_pull/verify` 掰回 `Data`，并把上一趟那份文件搬进 `Data/flow/`。

### 56.1 为什么 pin，而不是等着「第一次注入教我们」

Phase 54 的信条是「第一次注入**就是**用来教我们这棵树的，所以 `Pinned = {}` 是对的」。
这条信条**没有被推翻**，它只是多了一个新前提：**根名现在有人知道了。**
用户直接念出 `game.Workspace.Alarms`，并说「警报这里都有」。

那是他**从原版读出来的路径**，不是我们猜的 —— 这一点决定了它能不能进 `Pinned`：
那个字段的语义是「按名字看，哪怕普查规则本来不会选它」，所以填进去的**每一个名字都必须
是被证明存在的**，否则它就是一条静默的假话（名字不存在 = 零效果 = 和「选中了」同形，
同 §0.13 那条「缺失没有症状」）。

**参照物是 AIRemake，不是原版 —— 这一点必须写在纸面上。** 用户的说法是「现在我们的
workspace 里面就是相当于原版，你可以参照，但是路径可能有变化（因为我让你整理了）」。
量到的是：

| 项 | 值 |
|---|---|
| `Workspace.Alarms` | `Folder`，9 个子物体，**2,334 个后代** |
| 八个按房间/设备分的子 Folder | `Rad` `ReactorChamber` `ControlRoom` `Coolant` `Facility` `ReactorLounge` `Gravatron` `Mainframe` |
| 外加一个散的 | `Sound`（`AlarmPumpMalfunction`） |
| 里面的 `Sound` / `SoundEffect` | **99 / 213**（Compressor 44、Distortion 62、Echo 44、Equalizer 63） |
| 灯 | `PointLight` 16 + `SurfaceLight` 52 |
| 会亮会变的实体 | `Part` 842 + `MeshPart` 72 + `UnionOperation` 60 + `Model` 90 |

**为什么 2,334 个后代还是不够、非要 pin：** 两个上限是 `PerRootBudget = 30000` 和
`TotalBudget = 80000`，而**整个 Workspace 大约 9.2 万个实例**（Phase 47 记的 Part 总数
91,905）。也就是说**预算必然被耗尽**，剩下的只是「耗尽在 `Alarms` 之前还是之后」——
而选根是**从小到大**，排在它前面的那些小根加起来会不会先吃掉 8 万，**没有答案，只有赌**。
被 pin 的名字**同时豁免两个上限**
（`r.n > CONFIG.PerRootBudget and not pinned[r.name]`、`r.n > budget and not pinned[r.name]`），
代价是一个 `2,334 / 80,000` 的小根。**pin 不取代普查**：`rows` 还是每一个直接子物体，
`tree.txt` 照写全，`rooms.txt` 把这份名单印在 `# pinned by name:` 那一行 —— 豁免是
**写在产物里**的，不是靠读者猜的。

### 56.2 这个分支之前一次都没跑过，所以先把它测出来

`Pinned` 一直是 `{}`，那条 `not pinned[r.name]` **从未执行过**。改它之前先补测试，
而且**不新造 fixture** —— 加一个「超过 PerRootBudget 的根」要 30,001 个 mock 实例，
而 harness 里**现成有一个 4 万件的 `Facility`**：

- harness 加一条**正向**断言：`rooms.txt` 里必须出现 `# pinned by name: Alarms`
  （基线 44 → **45 checks**）。它证明的是**声明**，不是豁免；
- 变异表加两条（13 → **15**），豁免那一半由它们证：
  - `Pinned = {'Alarms'}` → `{}`：`rooms.txt names the root pinned by name` 必须红；
  - `Pinned = {'Alarms'}` → `{'Facility'}`：**没被 pin 的根反而被豁免** ——
    `the giant is absent from the watch` 必须红（`Facility` 变 `WATCHED`，
    `## roots NOT watched` 整段消失，那段是被 `if #skipped > 0 then` 挡着的，已核过）。
  **两条都点了 `must_pass`，两条都没有 OVER-BROAD。**

`bash _tools/run_tests.sh` 全绿、`rc=0`：`watch: 45 PASS`、`watch(boom): 4 PASS`、
`watch mutations: 15 of 15`、`gui mutations: 10 of 10`、`recorder 145028 / 3194`、
`watcher 80575 / 1636`（改前 79588 / 1623）。

**没做到的那一条，写在这里：** harness 的 fixture 里**没有**一个叫 `Alarms` 的根，
所以「pin 生效」是在 `Facility` 这个**替身**上证的，不是在那个名字上证的。
名字本身对不对，只有原版那一趟能回答 —— 而它现在**有产物可查**：
`rooms.txt` 的 `# pinned by name:` 那一行，加上 `## Alarms (...)` 有没有作为一个
watched root 出现。

### 56.3 8765 的目录：产物自己写的路径，和 sink 实际的 `--dir` 对不上

两个脚本的头注释都写着 `receive.py --dir D:/rblxTRGproject/Data`，**而跑着的那台是以
`--dir _tools/_pull/verify` 起的** —— 于是上一趟的文件落在
`_tools/_pull/verify/flow/original_260927-111843`：一份**和它自己的文档不符**的产物。
用户的问法是「8765怎么说？」。

动手前先量了两件事：**① 没有任何代码依赖那个目录**（全仓库只有 `PROGRESS.md` 两处、
`QUESTIONS.md` 一处是**叙述**，没有任何 `.py` / `.sh` / `.luau` 读它）；
**② 两个注入脚本里写死的只有端口**（`http://127.0.0.1:8765/`），目录是 sink 自己的事。
所以掰正是零风险的。

做的是：把 8765 停掉，以 `--dir D:/rblxTRGproject/Data` **detached** 起回来
（PID 2976 → **14948**，stdout 落在 `_tools/_attic/sink8765.log`），`GET /` 回 `receiver up`；
把上一趟那份文件搬进 `Data/flow/`，**搬前搬后 md5 都是
`d4582db5cba1728dd04b521adf3d096d`**（比哈希，不比长度 —— 同 `DECISIONS` 96）。
8766 由用户自己在本地起好了，两台脚本都取得到。

### 56.4 顺带记下的两条事实（都是用户给的，不是我量的）

1. **`ReactorALARM`** —— 用户说「警报是这个」，随后补的是容器（`Workspace.Alarms`）。
   在 AIRemake 的 `Alarms` 里**没有一个直接子物体叫这个名字**（9 个孩子下面是各房间的
   声音），所以它是**更深处**的一个实例名，具体是 `Sound` 还是别的类**没量，不写**。
   想知道，跑一趟就有 `inventory.txt`。
2. **警报的音频那一半本来就跑不掉。** `Workspace` 在 `AUDIO_ROOTS` 里，
   `attachAudioOnly` 会把**树里每一个 `Sound`** 挂上 `Played`/`Stopped` 并轮询 `Playing`、
   把每一个 `SoundGroup`/`SoundEffect` 注册进属性表 —— **这跟选根有没有选中 `Alarms` 无关**。
   换句话说：**根被跳过不会让警报变哑**；pin 买到的是**属性那一半**
   （`Color` / 灯的 `Enabled` / `Brightness` / 音效参数 / `HingeConstraint`），
   不是音频那一半。

---

## Phase 57（2026-09-27）—— 记录窗口，和那趟「救回来了却被 SEAL」的班次

**触发：** 用户跑完一轮之后给了两条互相独立的东西。一条是**窗口**：

> 「何时记录？何时结束记录？我进控制室之后，按下开机拉杆开始记录，游戏时间到12：00结束记录」
> 「原来的record功能不变」

另一条是**一次真的班次**：

> 「反应堆低温失速好像是低于1000F关机，我当时失速到2000F一下救回来了，但是脚本还是SEAL了」

**两半的验证状态必须分开写，因为它们差得很远：** 窗口那一半**只在 harness 里验过**
（104 条检查、25 个变异），**原版一次都没跑**；SEAL 那一半是**被那一趟的文件喂出来的**，
本机全绿，但**下一趟注入才是它的第一次实战**。

### 57.1 窗口挡的是「记录」，不是「观察」

这是本节所有设计的总纲，写错了会让「拉杆之前什么都没发生」和「发生了但被扣住」
变成同一句话。**扫描、属性监视、计数器、ambient 判定、音频 hook 在窗口关着的时候
全部照跑**；被拦下的只有**两份时间线**：

| 文件 | 受窗口管 | 为什么 |
|---|---|---|
| `changes.log` | **是** | 它就是「记录」这个词的所指 |
| `audio.txt` | **是** | 同上，声音也是时间线的一部分 |
| `summary.txt` / `inventory.txt` / `audio_tally.txt` / `health.txt` / `window.txt` | **否** | 这些是**状态**不是流水。窗口要是也管它们，一趟「拉杆没按下」的班次就只剩一个空目录 —— 和「监视器根本没注入」**同形**，而这正是 §0.16 反复踩的那类混淆 |

推论：**「窗口开着之前什么都没发生」这句话，是由不受管的状态文件作证的**，
不是由时间线的空白作证的。harness 里对应的检查就是那对
（`QUICK BOOT UP INITIALIZED` 在 `summary.txt` 里、不在 `changes.log` 里）。

### 57.2 窗口打开之前发生的事，穿着两件衣服 —— `withheld=0` 那个 bug

**这是本轮唯一一个先上线、后被自己的 harness 抓住的错。**

窗口打开时（`openWindow`）要做两件事：**数**一下有多少行被规则扣住了，然后**丢**掉它们。
第一版只数了 `#logLines`。于是 harness 读到一个**自相矛盾**的产物：

```
t=1 ... 某行的戳是 1
t=2 ... 另一行的戳是 2
t=3 | WINDOW | OPEN | ... | 0 line(s) before this were withheld by the rule
```

**OPEN 标记自己在说「之前一行都没有」，而它下面那两行就压在上面。** 原因不复杂：
一个**还在动**的键，它的行在 `held` 环里，不在 `logLines` 里 —— `releaseQuiet` 要等到
那个键安静 `QuietScans` 拍之后才把它们写出来，那已经是窗口打开**之后**的事了。
所以计数只覆盖了直接写入的那一半，环里那一半**既没被数、也没被丢**，直接漏进了时间线。

修法是**两样一起做**：`openWindow` 里把环一起数、一起清空。计数从 0 变成 **8**，
再把 STEPS[2] 那记「拉杆之前销毁一个实例」（唯一一条**不走环**的直写）算进去，
harness 现在读到的是 **9 line(s)**。

**顺带换掉了那条检查本身。** 第一版用的是字符串探针：搜 `QUICK BOOT UP INITIALIZED`
在不在时间线里。**它两头都错** —— 既漏掉了上面那次真实的泄漏，也会在一份**正确**的文件上
误报，因为**同一个字符串正好是窗口之后那条合法行的 `from` 值**
（`TitleText.Text | QUICK BOOT UP INITIALIZED | REACTOR ONLINE`）。
现在断言的是**戳的不变量**：**窗口打开之后，没有任何一行的戳早于 OPEN 标记**。
字符串可以合法地出现在值的两头，戳不行 —— 它就是这个文件的因果方向本身。

### 57.3 四个失败面，四个场景（不是四种说法）

窗口的失败空间是**四**个方向，每个都单独跑一遍（`run_tests.sh` 全部 gate 住）：

| 场景 | 演的是 | 结果 |
|---|---|---|
| `--nolever` | 拉杆的**部件在**、ClickDetector 不在 | 6 PASS；窗口由游戏自己的 `Stats.GameActive` 打开，`window.txt` 说 hook 没接上 |
| `--nopath` | 部件的**路径根本解析不到** | 5 PASS；同上，且 miss 信息**点名它找的是哪条路径** |
| `--nowindow` | 什么都不打开窗口 | 6 PASS；时间线仍然到达 sink，压在 `NO WINDOW` 标记底下 |
| `--closewin` | 表盘走到 12:00 | 7 PASS；**唯一一个自己结束一趟的行为** |

**`--nolever` 和 `--nopath` 是拆出来的，不是一开始就有的。** 原来是一个 `--nolever`，
fixture 把部件改了名，于是「路径解析不到」和「部件没有 ClickDetector」被混进同一条分支里 ——
而那条 miss 信息当时只说「路径解析不到」，**不说哪条路径**。两处都改了：
watcher 现在把路径拼进 miss 字符串（`the path does not resolve: ...`），
因为**注入进去的脚本没有控制台**，这行字是操作员唯一的线索。

**`--nowindow` 还有一个只有它才看得见的坑。** 它一开始报
`changes.log was never written at all` —— 不是 watcher 的错：harness 用
`error('HARNESS_STOP', 0)` 从 `task.wait` 里解开循环，**循环之后那段代码在这个 fixture 里
根本不会执行**，而 `NO WINDOW` 那条路正好住在循环之后。所以这个场景改成在 STEPS[50]
**按下操作员的 RightControl** —— 一趟窗口从没打开的班次，本来也只有人能结束它。

### 57.4 低温失速那一趟：一句话「我救回来了」，底下是三处在数

用户那句报告，拆开是**三件互不相同的事**，而且**每一件都能单独让一趟班次被封存**。

**(1) 边界把「停堆又起来」当成了一次 shutdown → restart。**
这是最像用户描述的那一条。`pollOnce` 的流边界原来只有两种结局：核心掉下去（DOWN）、
核心起来且**期间点亮过东西**（UP → settle → 封存）。而「掉下去又被救回来、
**期间什么都没点**」这个形状**没有归宿**：它会被塞进 UP 那条路，于是一趟**没有关机**的
班次被判成关机重启。现在多了第三种：`RECOVER` —— 核心回到线上而 `startedSinceDown`
是假，那就**清掉 `sawDown`**、**不发 UP**、**不进 settle**。
用户的抱怨（「文件把一次失速说成 shutdown / restart」）就是这条。

**(2) backstop 挂在一个「边」上，于是恢复之后它还在数。**
`SealDownSamples = 40` 那条是兜底：核心读着像停了 40 拍、又没有任何结束信号 → 封存。
它原来的守卫是 `sawDown`，而 **`sawDown` 是从 DOWN 一直保持到有人清它的边** ——
所以它**穿过一次恢复继续数**，然后在一个**明明在跑**的堆芯上开火。
12:32 那一趟就是活证据：DOWN 在 t=549.73，**t=567.57 就已经回到线上**，
而封存在 recorder **自己发出 UP 之后 0.33 秒**落下，理由是「已经下来 40 拍」。
代价不只是判错 —— 它**抢走了 settle 那条路的结局**，于是收据把锅记在兜底上而不是
复活上。**一个错的死因比没有死因更坏**：收据是读者不再重新推导时唯一会信的那一行。

修法用的是**同一个表达式**（`t >= Config.CoreThresholds[1]`），而且写成了**三段**而不是
「先清零再落回原来的两支」—— 后者会在一个**确定在跑**的拍上把计数器留在 1，
让恢复之后的停留**少一拍**。这种差一，只有 harness 看得见；这个 harness 就看见了。

**(3) 「跳闸停机」是关于一个曾经开着的堆芯的判断。**
`everRan` 是给两条温度臂加的门。理由只有一个，而且是用户给的（`A1`）：
**新班次开局堆芯是冷的** —— 冷堆**按定义**就在低温线以下，所以一个「电平」判定会在注入
两秒之后把一份什么都没录到的文件封存掉。**能说「跳闸停机」的，只有曾经开过的堆芯。**

**(4) 热端（核心熔毁）改读温度，不再借 `s.MainframeMeltdown`。**
`MeltdownF = 39000` 是**堆芯**的线，`s.MainframeMeltdown` 是**机房**的旗标（D9）——
18:35 那一趟旗标在 t=719.86 亮起时温度才 ~13000 F，旧标签让文件宣称了一次
它从没见过的 39000 度熔毁。现在两条各归各位，热臂带 `SealHotSamples` 停留。

**关于用户给的两个数：** 低温线在这份文件里是 **`LowTripF = 2000`**（Q1 里用户自己给的
确切线），用户这次说的是「好像是低于1000F」。两个数只差在这份**注入脚本的封存线**上
（游戏自己的行为不受影响），已作为**新的一条**记进 `QUESTIONS.md` —— 一句话就能定。

### 57.5 两个一模一样的 sort，需要两个见证 —— 24 → 25

`selftest_watch.py` 有 24 个变异，跑出来 **23/24**，唯一没被认出来的是
`the held lines are appended without being sorted`。原因**不是** fixture 缺见证，
而是**我盯错了那个 sort**：watcher 里有**两个函数体一模一样的 `table.sort`** ——
`releaseQuiet` 的 `batch`（变异锚的就是它）和 `drainHeld` 的 `pending`。
新加的 A/B 交错拍（116..119）**只喂到后一个**：它们在循环解开时还挂在环里，
是 `Report()` 的 `drainHeld` 把它们倒出来的，而那个 sort 变异**没碰过**。

看懂之后改了两处：

1. **补第二对拍（100..102）喂 `releaseQuiet`**，并且**两条环的最后一拍必须相同** ——
   释放条件是**严格**的 `tick - last > QuietScans`（5），所以「A 的末拍 102、B 的末拍 103」
   会在 **108 和 109 两拍分别释放**，一条一批、各自已经有序，变异自然看不出来。
   第一版就是那么写的，产物里那四行是 `100, 102, 101, 103`（**按键分组**），
   一眼就能看出是两批而不是一批。改法：STEPS[102] **同时**动 A 和 B。
2. **给第二个 sort 也补一个变异**（`the end-of-run drain is appended without being sorted`）。

现在 **25 个变异 25 个按预期变红**。教训是那类**只在变异测试里显形**的错：
两条一模一样的代码路径，一条被见证、另一条被文档替它说话。

### 57.6 另外两处小事

- **出口路径的注释在说一个不可能发生的触发。** 注释写「窗口一直没开、表盘走到 12:00」
  就把时间线倒出来 —— 而表盘是窗口的**关闭**规则，`closeWindow` **正确地拒绝**
  一个没开过的窗口，所以那条路**永远不会通过表盘到达**。它不是无害的：
  只读那段话的人会以为 `--nowindow` 有一个时钟出口，于是**不会去找它真正的出口**。
  已改成按代码写（跑到结束），并把 `--nowindow` 为什么必须自己按 RightControl 写进去了。
- **`Workspace` 大写不是 Roblox 全局**（只有小写 `workspace` 是）。写错**编译得过**、
  每一个路径都回 nil —— 后果是**没有拉杆钩子、没有表盘、没有兜底旗标、窗口永远不开**，
  而且**全程静默**（监视器照常观察，只是把整趟扣住，`window.txt` 会说三条**都存在**的路径
  「解析不到」）。harness 抓到了它。代码里现在有这段注释。

### 57.7 收到的那张纸

`bash _tools/run_tests.sh`，**全绿、`rc=0`**：

```
recorder parses: Lua 5.1        watcher parses: Lua 5.1
panel / driver / end / clock / gui / flow   rc=0（六份采集器 harness）
watch: 68 PASS, 0 FAIL
watch(boom): 5   watch(boot): 7   watch(nolever): 6
watch(nopath): 5  watch(nowindow): 6  watch(closewin): 7      合计 104 条检查
watch mutations: 25 of 25 detected, shipped file untouched
gui mutations: 10 of 10
end mutations: 3/3 load-bearing      flow mutations: 8（7 条承重，1 条记为冗余）
recorder: 149895 bytes, 3272 lines
watcher:  116492 bytes, 2209 lines
```

**md5：** 采集器 `08b5caef4a32be6e900d3885b91432da`、
监视器 `1ad9a04588efe55d3d9a92118dfc241e`。
**采集器与已推送的那一份不同了** —— 所以**下一次注入两份都要重新注入**，
不能只注监视器。

### 57.8 没做到的，写在这里

- **这两个版本（改完之后的）都还没在原版里跑过。** 窗口的窗口期（拉杆 → 12:00）
  **一次都没有在真游戏里经历过**；它现在只有 harness 的背书，而 harness 的树是 fixture。
  **更正一条：** 本文写到这里时我按「监视器从未在原版里跑过」写，
  用户随后说他那一轮 `watch` 和 `record` **都开了** —— 而**盘上只有采集器的字节**
  （`Data/originalwatch/` 不存在）。**这一条更正和它的证据写在 57.10**，
  结论是「监视器可能没被注入、也可能死在第一次 POST 之前」，两种在盘上同形。
- **`--nowindow` 之外，`NO WINDOW` 那条出口在真机上还有第三种到达方式**（用户中途
  按 RightControl 停），本机是用同一个键演的，所以这一条算是**近距离近似**，
  不是直接观测。
- **低温线 1000 还是 2000**，见上（`QUESTIONS.md` 新增一条）。
- **窗口本身**（拉杆 → 12:00）**这一趟也没有被观测到**，原因和上一条同一类：
  它只在 harness 的 fixture 树上开过。

### 57.9 这一轮收到的答复，和它们各自落到哪一行

用户这一轮给了三句答复（`P4:A P5:都行，看你 P6:看你`）+ 一条举报（低温失速）+ 一条指示
（记录窗口的边界）。**五件事，五处落点，一个都不攒**：

| 拿到的东西 | 落点 |
|---|---|
| **P4:A** —— 下次注入顺手把三台冷却泵拧到 2 档停约半分钟、再 3 档停约半分钟 | `QUESTIONS.md` P4（已答）；填的是温度模型上**最后一个没标定的增益**（1 档 = −58.2 F/tick） |
| **P5 → 我定为 A**（留着那三份原版源码逐字副本） | `QUESTIONS.md` P5（已答）+ **`DECISIONS_2` 180** |
| **P6 → 我定为 A**（带探针，先拿机制再改行为） | `QUESTIONS.md` P6（已答）+ **`DECISIONS_2` 181** |
| **低温失速被误封**（三处独立原因） | 本文 57.1–57.4 + `DECISIONS_2` 177..179；**剩下的那个数**新开 `QUESTIONS.md` **P7** |
| **记录窗口归监视器** | 本文 57.1–57.3；**采集器的 record 一个字没动**（用户原话「原来的record功能不变」） |

**P5 那条值得单独说一句，因为我把选项本身读错了：** P5:B 的措辞是「撤掉」，
而那三份已经在 `3461509` 里推出去过 —— `git rm` 只影响**下一个** commit，
已经 push 的历史收不回来（要收得 rewrite history + force push，风险比留着大）。
所以 B 的真实含义是**「从现在起不再发布」，不是「撤回」**，而我在题面里把这条说轻了
（还写了「约一分钟就完事」—— 一分钟只够 `git rm`，不够改掉 `DECISIONS`/`QUESTIONS`
里那几百处引用）。**这两处措辞错误和 180 一起记下来，因为下一个问题会照着同一套措辞问。**

### 57.10 你说的那一趟：采集器的文件在盘上，监视器**一个字节都没到**

**先说采集器 —— 它完整，而且那个 bug 是它自己写下来的。**

`Data/flow/original_260927-123212`（1099854 字节，
`samples=1159 lines=4940 events=4310 postfails=0 spilled=0 dropped=0 flow=true
drive=watching/watching readouts=1437 hash=9417c6da`）：

```
PHASE2 DOWN t=549.73
PHASE3 UP   t=567.57                                      ← 救回来了
EVT4310 SEAL held down 40 polls with no end signal        ← 0.33 秒之后封存
```

**「held down 40 polls with no end signal」和它上面 0.33 秒的 UP 互相矛盾** ——
同一份文件里，一句计数**否认了它下面那行证据**（和 174 是同一种病，只是这次在收据里）。
这就是 57.4 修的那三处：兜底挂在**边**上，所以它**穿过恢复继续数**，
而且**抢走了 settle 的结局**，把错死因写进收据。**你报的那件事，这份文件就是证据本身。**

**再说监视器 —— 零字节，而这次不是「没验」，是「量出来没有」。**

按设计，第一个该出现的路径是 `Data/originalwatch/<stamp>/hello.txt`，
而它是在**普查之前**发的（源码 line 94 的注释 + line 2029 的调用）。**那个目录不存在。**
同一趟里的三个读数：

| 读数 | 值 | 怎么量的 |
|---|---|---|
| sink 8765 的进程启动时刻 | **12:14:55** | `Win32_Process.CreationDate` |
| 采集器那一趟 | **12:32:12 → 12:41** | 文件名里的时间戳（起始）+ 文件 mtime（末笔） |
| 采集器落盘 | ✅ `Data/flow/original_260927-123212` | 收据完整 |
| 监视器落盘 | ❌ **没有**（`Data/originalwatch/` 不存在） | `ls` + 全工程 `find` |

**两个脚本走的是同一个 sink、同一个 `HttpService`、同一场游戏** —— 一个到了、一个没到。
所以这不是「HttpService 被挡」，也不是「sink 当时不在」（8765 在 12:14:55 就起来了，
比那一趟早 17 分钟），**而是监视器那一侧的代码根本没有执行到第一次 POST。**

**能解释它的有两条，而它们在盘上分辨不出来：**
1. **没被注入**（或注入的不是这一份）；
2. **被注入了，但死在第一次 POST 之前**（取脚本失败、执行器里 parse 失败、`GetService` 抛错…）。

**第 2 条是我这套自检的一个真缺口，而这里要如实说清楚：** `--boot` 那个场景
（harness `--boot`，本文 57.7）盖的是「**普查**抛错」—— 它证明普查死了 hello.txt 还会到。
但 **hello.txt 本身是 `Watch.Start()` 的第一件事**，在它**之前**还有整份文件的顶层代码
（服务查询、常量、几百行函数定义）。**「在 hello 之前就死」在盘上和「从没注入」
逐字节一样**，而这两种情况的处置完全不同（一个是再注一次就好，另一个是脚本有 bug）。

**我没有为此改代码，也没有加信标 —— 那需要你拍板**（`QUESTIONS.md` **P8**）。
理由是：唯一能在 sink 不通时留下证据的地方就是**游戏内部**（或执行器的本地文件系统），
而「只读、不写世界」是监视器从 Phase 54 起一直遵守、并且写进 `DECISIONS` 的性质，
把一条我反复引用过的性质悄悄改掉，比这个缺口本身更糟。


## Phase 58（2026-09-27）—— 把「哪一趟是旧副本」变成读得出来的，和那趟失速真正的死因  [DONE — 本机验过，原游戏还没跑]

你这一轮给了三条：**P7 = 1000F**、**P8 = 你看**、以及一句「我现在做什么」。
第三条是这节存在的理由 —— 一次注入只能花一次，所以**注入之前该验什么必须先写在盘上**。
在动手之前先把两件旧事量清楚，因为它们的结论会改变这次注入该带什么。

### 58.1 那趟失速：**P7 不修它**，而且死因在文件里写着

先说会让你意外的那句：**低温线改成 1000 F 对那趟没有用。**
`Data/flow/original_260927-123212` 里 `m.temp` 在窗口内是

```
t=549.17  5586       t=558.18  4316  ← 最低点          t=567.57  5810
          5133  4808  4597  4323     4351  4677  4999  5405
```

**最低 4316 F，离 2000 和 1000 都还差 2300 F 以上**，冷跳闸那条臂**一次都没到过**。
真正结束那一趟的是它下面那行：

```
EVT4310 SEAL held down 40 polls with no end signal
```

`SealDownSamples = 40` 的**兜底**（游戏二十多秒没给任何信号，我就自己封存），
而它和它上面 0.33 秒前的 `PHASE3 UP` 直接矛盾 —— 那是 57.4 修的三处
（兜底挂在**边**上、穿过恢复继续数、抢走 settle 的结局）。

**所以 P7 是一个正确的更正，不是一个修复，而且它到得太巧：**
如果我只是把 2000 改成 1000，这条记录读起来就像「你报的问题处理完了」，
而真正要看的 40 拍兜底反而被这句话盖住了。这条写进了采集器 `Config.LowTripF` 上面的
注释（**不是只写新数字**），取舍是 `DECISIONS_2` **182**。

### 58.2 你的 12:41:40 那一趟跑的是**旧副本** —— 三个 build 标签

上一节那张表里要看的第二样东西是**时间**：

| 项 | 时刻 |
|---|---|
| 你那趟封存 | **12:41:40** |
| 采集器修好版的 mtime | **13:58:44** |
| 监视器修好版的 mtime | **13:54:07** |

**77 分钟。** 你那趟跑的是 Phase 57 修完**之前**的两份，所以 57.4 那三处
（`RECOVER` / 兜底挂边 / `everRan` 门）在你手上那份里**根本不存在** ——
「修好了吗」这个问题在 12:41 那一刻的答案是「还没有」。

这件事我没法在盘上事后分辨（两版都不留版本号），所以补的是**以后**能分辨：
三个脚本各自加一个 build 标签，并且**每一个点名这一趟的产物里都要出现它**：

| 脚本 | 标签 | 出现在哪 |
|---|---|---|
| `TRG_original_recorder.luau` | `Config.Build = 'r58'` | 文件头 `# ... change recorder build=r58` |
| `TRG_original_watch.luau` | `CONFIG.Build = 'w58'` | `bootReport()`、`health()`、**信标** |
| `transport_probe.luau` | 时间戳目录 `probe/<STAMP>/` | 每个产物路径里 |

harness 那份**不是手打的**：`watch_harness.luau` 用
`string.match(src, "Build%s*=%s*'w(%d+)'")` **从已发货的监视器里读**，
读不到就 `os.exit(1)`。手打一个 `w58` 进 harness 就是 183 那条病。

### 58.3 监视器零字节的真正嫌疑：**两个脚本的传输层不是同一套**

57.10 把「监视器零字节」挂起来等 P8。P8 我答的是三部分，第一部分是**直接嫌疑**：

- **采集器**的 `pickHttp()` 是一把**梯子**：`syn.request → http_request → request →
  http.request → fluxus.request → krnl.request → getgenv().request → HttpService:PostAsync`；
- **监视器**只写了**最后一个**：`HttpService:PostAsync`。

**两者都能到 sink 吗？** 采集器那趟到了（收据 `postfails=0`），监视器没到。
如果他的执行器**只有** `syn.request` 这一类（把 `PostAsync` 关掉），
那么在**同一个会话里**跑同一份梯子，一个通、一个不通 —— 完全解释零字节，
而且和「死在第一次 POST 之前」区分不开。

**盘上原来的证据差一口气：** 采集器的头是
```
# session 260927-123212 placeId=17596243941 jobId=90812af2-... player=andypeng1NB transport=http8765
```
它说**有**一条能用的 POST 通道，但**不说赢的是哪一个** —— `http8765` 是我给它起的名字，
不是候选名。所以采集器的头现在多带候选名（`transport=http8765/<httpName>`，来自
`pickHttp()` 返回的第二个值），监视器 `health()` 多一行 `transport=`。

### 58.4 `transport_probe.luau`：一个不花班次的诊断

**这是「你现在做什么」的答案的第一步。** 它只做一件事：
把上面那把梯子的**每一个候选**都试一次，把结论写到 sink。九个候选：

```
syn/http_request/request/http/fluxus/krnl/getgenv   kind='post'
httpget                                             kind='get'
httpservice                                         kind='post'，外面包一层 pcall
```

**规矩三条：**
1. **只有 `kind == 'post'` 能当 winner** —— GET 能通只说明「网络通」，
   而两个采集脚本**要的是 POST**，让 GET 赢就等于下次真跑的时候通道不存在；
2. **每个候选各试一次，不重试** —— 重试会把「挂住」变成「跑很久」，
   而它是在**游戏主线程**上跑的；
3. **摘要通过 winner 发出去**，没有 winner 就**只存在于 `print` 里** ——
   这是刻意的例外（监视器刻意不打印），因为「一个都没有」这件事
   **没有通道可以写**，不留个 print 就等于没有答案。

`_G.TRG_TRANSPORT_PROBE = {stamp, winner, summary}` 是给**第二次注入**留的口子：
`transport_probe.luau` 用 `loadstring` 自己再跑一遍（用户说 Solara V3 走 loadstring），
那时不必找文件。

### 58.5 监视器：加了梯子、加了信标、加了标签

三处改动，按文件顺序：

- **`-- ========== TRANSPORT ==========`（line 522）**：和采集器**同一个顺序**的梯子，
  选出来的名字进 `TRANSPORT`，函数进 `httpFn`；`sendOnce(req)` 统一收口 ——
  传输不存在、抛错、没回结果表、状态码非 2xx，**四种失败各有各的字**。
- **`-- ========== THE ALIVE BEACON ==========`（line 609）**：
  这是 P8 第二部分，也是**比 `hello.txt` 更早**的那个阈值。
  `hello.txt` 是 `Watch.Start()` 的**第一件事**，而 `Start()` 是整份文件的**最后一句** ——
  它之前还有注册、音频、普查的几百行顶层代码。所以**信标放在整份文件的工作之前**：
  它一响，读者就把三种情形分开了：

  | sink 里看到什么 | 说明 |
  |---|---|
  | **什么都没有** | 没注入，或注入的不是这一份（**这一格还是瞎的**，见 58.8） |
  | **只有 `alive.txt`** | 加载了，死在顶层代码里 —— 去看它带的那行 `note` |
  | **`alive.txt` + `hello.txt`** | `Start()` 进去了，剩下的看 `tree.txt` / `error.txt` |

  它**故意不走 `post()`**：`post()` 的掉线计数在 `Start` 才重新对时的运行时钟上，
  而信标跑在 `Start` 之前 —— 折进去会写出一个**负数**的 `sink_down_total`。
  取舍是 `DECISIONS_2` **186**。
- **`bootReport()`**：`build=` / `transport=` / `prefix=` / `sink=` / `t=`。

harness 的第一到达权**从 `hello.txt` 挪到 `alive.txt`**（`arrival('alive.txt') == 1`），
并且断言它**早于** `hello.txt`、带着 `build=w<CONFIG_BUILD>`、点名 `transport=`、
点名自己的 `prefix`。`hello.txt` 守弱一点的那几条（早于 `tree.txt` 等）。
**74 PASS / 0 FAIL**（原 68），六个场景 `--boom` 5 / `--boot` 7 / `--nolever` 6 /
`--nopath` 5 / `--nowindow` 6 / `--closewin` 7 全绿。
变异测试 **25 → 27**，新增两条都钉在信标上（另一个文件先到 → 红在
`alive.txt was the FIRST thing at the sink`；信标带一个**不是发货版**的 build 标签 →
红在 `alive.txt carries the build tag, so a stale copy is visible as stale`）。

### 58.6 探针第一版**调用的形状是错的**，而 harness 是绿的

这条值得单独写，因为它是这一轮唯一一个「会静默地把答案反过来」的错。

第一版探针每个候选都传 `(url, body)`。**request 那一族要的是请求表**
（`{Url=…, Method='POST', Body=…, Headers={…}}`），所以在真实执行器上
**每一个能用的传输都会抛错**，然后被报告成「坏的」—— **正好是探针要回答的那个问题的反面。**

**而 harness 当时是绿的。** 因为它的桩写的是
`function(req) sentB[#sentB+1] = req.Url ... end`，而 `req` 那时是个**字符串**：
`('http://…').Url` 走字符串元表解到 `string.Url` = **nil**，
`t[#t+1] = nil` 是**静默的空操作**，桩照样返回 `{StatusCode = 200}`。

**两重静默叠在一起**：桩太宽容，于是错的调用看起来对；字符串元表又把桩自己的记账吃掉了，
于是连「桩没收到东西」都看不见。这就是我为什么又加了 `selftest_transport_probe.py`
（4 个变异，各自红在**点名的那条**检查上，`finally` 里从启动时的字节还原）：

| 变异 | 要求红在 |
|---|---|
| 调用形状退回 `(url, body)` | `B every call to the transport is a request TABLE` |
| `code < 200 or code > 299` → `false` | `C it is reported present and NOT working` |
| winner 不再要求 `kind == 'post'` | `D and with no POST transport there is still no winner` |
| `res.Error` 那一串 → `nil` | `D and the raise is named rather than swallowed into "status 0"` |

**4 个变异全部被抓住，23 PASS / 0 FAIL。** 规矩写进 `DECISIONS_2` **184**
（桩必须**断言它收到的形状**，不能只对它做出反应）和 **183**
（读配置的 harness 才跟得上配置；抄一份的跟不上）。

### 58.7 这一轮的账

```
bash _tools/run_tests.sh          →  rc=0, 133 条 ok
  panel/driver/end/clock/gui/flow  全部 rc=0（flow 26 checks、end 24 assertions）
  watch                            74 PASS / 0 FAIL，六个场景全绿
  watch mutations                  27 of 27 detected
  gui mutations                    10 of 10 detected
  transport_probe                  23 PASS / 0 FAIL，4 个变异 4 个红在点名的检查上
  flow mutations                   8 个变异按规格动作
```

| 脚本 | 字节 | 行 | md5 |
|---|---|---|---|
| `TRG_original_recorder.luau` | 152467 | 3304 | `9979a0b20ff41c2d1e78938cd8d7fc8c` |
| `TRG_original_watch.luau` | 126531 | 2386 | `e83d725dee65993738f99d66a609ce80` |
| `transport_probe.luau` | 10752 | 217 | `5acde17d2bccfa65949c9a4b2bec9a90` |

### 58.8 这一轮**没有**验到的，写在这里

- **三份脚本一次都没在原版里跑过。** 原版树我一次都没看过，所有「这个口径够不够」
  都是设计意图不是观测。
- **信标那一格还是瞎的：** 「顶层代码在第 609 行**之前**就抛错」和「从没注入」
  逐字节一样。要把这格也补上，得把信标放到**整份文件的第一行**，
  而那时连 `CONFIG` 都还没读完 —— **代价大于收益，我没做，也不打算做**，
  这条要一直写在 P8 的答案里。
- **P4:A 的冷却泵 2/3 档那趟还没跑** —— 要等这次注入。
- **P6:A 的 187 个重复键探针没写进这轮** —— 它要动采集器的 readout 走查，
  而这一轮的两处改动已经改过采集器了，**两件事不叠在同一个注入里**。

---

## Phase 59（2026-09-30）—— 拉杆的位移改成 tween

**起因（用户原话）：** 「把 VisualFeedback 的拉杆改成平滑 tween，拉杆移动也 tween 行吗」。
**他只问了拉杆**（`拉杆` 说了两次），没提灯 —— 所以只动拉杆，灯的写入路径一个字没改。

### 59.1 改了哪两处

| 文件 | 原字节 | 现字节 | 改动 |
|---|---|---|---|
| `SSS.ReactorBackend.VisualFeedback` | 33390 | **38996** | `poseLever` 一帧落位 → tween；新增两个安全性质 |
| `SSS.ReactorBackend.Config` | 9838 | **10350** | `Visual` 表新增 `LeverTweenSeconds = 0.3`（512 字节） |

**上表是 Phase 59 当时的数字，不是现值。** Phase 60 又往同一个 `Config` 里加了
`Shell.ShutterTweenSeconds`，所以 `Config` 现值 **10943** / djb2 `0xdc1c7e23`
（`VisualFeedback` 的 38996 此后再没变）。这里留着 `10350`，因为它是那一步**量到的**数 ——
改成后来的值就等于把走过的路抹平。六个模块的对齐现状见 60.1。

**「原字节」这两格是怎么来的，分开说 —— 因为其中一格上一版是错的（我自己写的
`10270` 从来没量过，是编的）。** `VisualFeedback` 的 `33390` 是**已验证**的：
`_tools/_pull/verify/VisualFeedback.pre-phase59.luau` 就是改前正文（`§0.15` 那条
「`#Source` 与磁盘逐字节相同」的方法量过）。`Config` 的 `9838` 是**这轮在 Studio 里量的**：
取活的 `Config.Source`（**10350**，djb2 `0x3a122108`），把两个锚点之间的整段删掉
（`RefreshSeconds=1,` 的末尾 → `LeverTweenSeconds=0.3,` 的末尾），剩下的 `9838` 字节
djb2 `0x97f981b8` —— 删掉的正是我自己写的那 512 字节（打印出来逐字符看过，
首行是我留的空行、末行是 `LeverTweenSeconds=0.3,`），所以 `9838` 是**测量**不是推算。

**顺带一个 `§0.15` 式的新陷阱（这轮才现形）：磁盘上那份
`_tools/_pull/verify/Config.pre-phase59.luau` 是 8975 字节 / djb2 `0x4052f78a`，
它和改前的活模块差 863 字节 —— 它是 **2026-09-27 01:27** 拉的（Phase 53/54 那阵，
和 `§0.15` 记的那个 `8975` 对得上），**Phase 58 改了 `Config` 之后没重拉**。
它**不是错的**，是**旧的**；「磁盘上有一份 `Config.luau`」这件事**不等于**它是最新的。
所以本轮把这两份改名成 `*.pre-phase59.luau`，让陈旧性写在文件名上，而不是靠记性。
（`_pull/verify/` 是临时核对区，不是文档化的镜像，`CLAUDE.md:455` / `PROGRESS` 3537 那几处
只提到它的存在。）

> **2026-09-30 更正（Phase 60 复查）：** 上面把「改前正文」的落点写成了
> `_tools/_pull/verify/Config.pre-phase59.luau`。**那句给旧副本下的判断是对的**
> （8975 确实比改前活模块旧 863 字节），但**参照物选错了** —— 权威的「改前」是
> **`src/ReactorBackend/Config.luau`**：`git show HEAD:src/ReactorBackend/Config.luau`
> 量出来正是 **9838 字节 / djb2 `0x97f981b8`**，和上面那条「把 512 字节块删掉」的推导
> **逐位对得上**。教训是 `_pull/verify/` 是一次性核对区，**只能证伪、不能当基准**；
> 要拿「上一版正文」就找 `src/`（有 git 背书）或 git 本身。

`poseLever` 原来是：

```lua
part.CFrame = entry.baseline + entry.baseline.LookVector * throwDistance(level, maxLevel, entry.travel)
```

现在是 `TweenService:Create(part, leverTweenInfo, {CFrame = goal}):Play()`，其中
`leverTweenInfo = TweenInfo.new(Config.Visual.LeverTweenSeconds, Quad, Out)`。

**两个旧代码不需要、新代码必须有的性质**（`DECISIONS_2` 188 / 189）：

1. **创建前先 `Cancel()`** —— 一个属性上两个活着的 tween 会逐帧竞争，赢家按帧决定，
   所以「连点两下」可能让 union 停在一个**谁都没要求过的档位**上。`Cancel()` 把它留在
   已到达的位置，新 tween 从那里开始 —— 这也正是「中途打断的 throw 继续走，
   而不是弹回上一次走完的档位」的原因。
2. **同一个实例被重新解析时沿用旧 `baseline` / `travel`** —— `smallThrow(part)` 是从
   该 rig 自己的 `ClickPart` 读 throw 的**符号**的，而它只在 union 坐在两个档位之一时成立。
   一次重新 `Initialize` 如果发生在半路，重新测量会把**档位之间的姿势**当成基准 ——
   符号可能反过来，此后这个拉杆**每一抛都走错方向，而且没有任何症状**
   （去错档位的拉杆仍然是一根在动的拉杆）。

### 59.2 为什么动画放在**服务端这个模块**里，而不是走客户端

用户上一轮刚放进来 `ReplicatedStorage.Functions.Functions`（8 个 helper，含 `TweenModel` /
`MultiTween` / `TweenModelAroundPivot`），这个 place 里**本来也**已经有一条 tween 中继
（`ReplicatedStorage.TweeningEvent` → `ReplicatedFirst.ClientTweenReplicatedFirst`，
12 行）。**两条都故意没用**：

- 它们都把**动画这一串写**放在客户端，而 `VisualFeedback` 是这些 CFrame 的**单一写入者**
  （模块自己第 4 行就这么写）。把 tween 交给客户端 = **两个写入者**
  （`DECISIONS` 里反复出现的那条，用户特别在意的点）。
- 客户端那一路**已经被撤过一次**：`StarterPlayer.StarterPlayerScripts.VisualFeedback`
  的头注释记着 `SUPERSEDED 2026-09-26: disabled, not deleted.`，
  以及当时的现场症状 ——「C-Pump 3 的拉杆在客户端停在它作者给的 CFrame 上，
  而服务端把它按在 1.6 studs 之外，于是玩家点下去**什么都看不到动**」，
  并写明「客户端赢了，因为客户端写过的属性在服务端下次改它之前不会被覆盖」。
- 另外实测那套库**在拉杆上不可用**：`TweenModel` 在 41 个 `LeverUnion` 上全部报错
  （0 个有 `PrimaryPart`）；`TweenModelAroundPivot` 对拉杆**永远走 `warn` 分支**
  （41/41 的 `LeverUnion.PivotOffset == CFrame.new()`），而它真走 offset 分支时会把模型**撕开**
  （门↔主件距离 11.358 → 5.000 studs，主件落在离刚性旋转意图 10.198 studs 的地方）；
  它那条「传 Part 当模型」的分支**每次都报错**（`GetPrimaryPartCFrame is not a valid member of Part`）。
  只有单独对 `LeverUnion` 用 `MultiTween` 是对的（原位转 45.0°，平移 0.00 studs）。

**所以：`TweenService` 原样在服务端调，写进已有的单一写入者。** 时长进 `Config.Visual`
（和 `PulseSeconds` / `RefreshSeconds` 做邻居），**缓动不进 Config** —— 它不是谁能调的
数字，是机构的手感：`Quad/Out` 减速进档，像手推的定位拉杆；`Sine/InOut`
（`RS.Functions.Functions` 对一切都用它）起步慢，读起来像马达。

### 59.3 验证（§4.4）—— 全部通过，9/9

驱动的是**发货的 `Refresh` 本身**，不是复刻的逻辑：把 `Config` + `VisualFeedback`
`Clone()` 到 `SSS.__vfTest` 再 `require`（§0.15），指向的仍是 `workspace` 里的真部件。

| 检查 | 结果 |
|---|---|
| 是动画不是瞬移 | **203 个互不相同的姿势**（810 帧里） |
| 落位**逐字节**精确 | 中断过的那一抛仍 `union.CFrame == farStop` |
| 每段行程单调 | 通过 |
| 纯平移、沿拉杆自己的轴 | 沿轴 **0.6578 studs**，垂直分量 **0.00e+00** |
| 自己 rig 里只有 `LeverUnion` 动了 | **23 个其他部件逐字节不动** |
| 全设施其他拉杆一律没动 | **20 根逐字节不动** |
| 21 根拉杆全部还原成作者姿势 | 0 处不符 |
| 31 盏灯全部还原成作者颜色 | 0 处不符 |
| 临时 rig 已销毁 | 通过 |

**中断那一路是重点**，做法是把中断**放进 `Heartbeat` 回调里**（引擎驱动，47 Hz，
**不受工具往返时间影响**）：10 s 的抛掷，在 `t = 3.515 s` 也就是**行程的 41.8%** 处反向。

- **`Cancel()` 没有跳变**：中断前最后一帧与中断后第一帧的投影**逐字节相同**
  （step = 0.000000 studs）。
- **打断过的 throw 仍然精确落档**：`t = 13.498 s` 时 `CFrame == farStop`，逐字节。
- 顺带一个交叉验证：35% 的**时间**对应 41.8% 的**行程** —— 正是 `Quad/Out` 前段快的形状，
  这不是假设，是量出来的。

**发货的 0.3 s 这一档也单独验过**：第一抛用的就是 clone 里原封不动的
`LeverTweenSeconds = 0.3`，`final alpha = 1.000000000`，落位逐字节。

### 59.4 两件必须记下来的事

**① 我把世界改坏了，然后修回来了（`DECISIONS_2` 191）。**
第一次做行为验证时死在 `task.wait`（**插件 VM 里 `task.wait` 不能 yield**），
而它**死之前**已经跑完了 `Initialize` + 一次 quiet `Refresh` —— 那次 `Refresh` 走真实路径，
**把 31 盏模块管理的灯全刷成了 quiet 姿势**，把作者的颜色覆盖掉了。没有任何东西报错。

修回来靠的是 **`execute_luau` 的写入确实进 change history**：`Undo` 两次
（一次撤探针留下的 `__probeMarker`，一次撤那次 `Refresh` 事务），灯回到
`17,17,17` / `0,0,0` / `255,0,0` / `255,255,0` —— **这些是模块不可能产出的颜色**，
而模块自己的注释独立地预测了最后两个（警报静音灯作者给的就是纯红、gravatron
armed 灯纯黄）。所以撤回来的是**真正的作者值**，不是另一个系统姿势。
`Undo` 是全局栈，所以每次撤完都拿两个模块的 `Source` 字节数当护栏
（38996 / 10350，撤完必须没变）—— 变了就立刻 `redo`。

**② §0.15 又抓到一次现行。**
`require(SSS.ReactorBackend.Config).Visual.LeverTweenSeconds` 在插件 VM 里回 **nil**，
而 `Config.Source` 里明明有 `LeverTweenSeconds=0.3,`（10350 字节），
**新 `Clone()` 出来的实例 require 出来是 0.3**。这正是 §0.15 说的那张脸：
**过期的 require 递给你的是少键的表**，而如果消费者是 `poseLever`，
症状就会落在**别的模块**的报错上。这次没花时间，因为**源码和 clone 都查了**。

### 59.5 这一轮**没有**验到的，写在这里

- **Edit 模式下的 tween 帧率不是 Play 模式的帧率。** 我量到的 203 个不同姿势是在
  Edit 模式（`Heartbeat` 47 Hz）下。Play 模式逐帧步进，只会更细，不会更粗 ——
  但**「Play 模式里看起来是平滑的」这句话我没有测过**，因为 §0.16：
  这套工具注册不了 server / client peer，跑起来的游戏读不到。
- **7 个其他 rig 家族（pump / cbl / extract / mass / shutters / hdef / vent / startup）的
  throw 长度**没有单独重测。它们走的是**同一个** `poseLever`，而 `TRAVEL` 表里
  每个家族的数字是早就量过的；我验的 `fan1` 属于 SmallLever 家族。
- **`LeverArcDegrees = 50` 这个键和本次改动无关** —— 它是 `ControlVisuals`（旧的旋转式写入者）
  的，不是 `VisualFeedback`（平移式）的。两个模块的名字太像，别混。
- **`task.delay` 的长引信比墙钟慢得多**：0.4 s 的引信在一次重调用**内部**就跑完了，
  而 9.5 s 的引信要过好几轮工具调用才落地，7.5 s 那个我到最后也没读到。
  跨调用等时间**不要**靠 `task.delay`，靠**两次工具调用本身**（`TweenService` 是引擎驱动的，
  它会在调用之间正常走完）。

---

## Phase 60（2026-09-30）—— 百叶窗的开关也 tween，外加一个跑服务的 `.bat`

**起因（用户原话）：** 「百叶窗的开关也要tween，还有你生成个.bat用于运行那两个服务
（发端口那个什么的」。两件事分开做，分开验。

### 60.1 「百叶窗的开关」是那三扇门，不是那根拉杆

先查了一件容易搞错的事：`百叶窗` 的**拉杆**（
`Consoles.ALTReactorConsole.ControlRoomSystems.ShuttersLever.LeverUnion`）
**Phase 59 已经 tween 过**了 —— 它走的就是 `poseLever`，和另外 20 根拉杆一条路。
所以用户那个「**也**」指的是**门本身**：`RoomShell.applyShutters` 一直是
`frame.CFrame = goal` 一帧落位，**10.58 studs 瞬移**，而它自己的开关正在 0.7 studs 上缓动 ——
一块面板在跳、它的开关在走，读起来就像控制台上唯一一件没接线的东西。

| 文件 | 原字节 | 现字节 | djb2 | 改动 |
|---|---|---|---|---|
| `SSS.ReactorBackend.Config` | 10350 | **10943** | `0xdc1c7e23` | `Shell` 表新增 `ShutterTweenSeconds = 0.6` |
| `SSS.ReactorBackend.RoomShell` | 16665 | **19401** | `0x95a54194` | `applyShutters` 瞬移 → tween；新增 `ShutterEntry` 与 Cancel-before-create |

**动画又一次放进了「已经拥有那个值」的模块**（`DECISIONS_2` 187）：`RoomShell` 是这三扇门
CFrame 的单一写入者，`VisualFeedback` 碰都不碰它们，所以这里没有第二个写入者要处理。
这条正好是 Phase 59 那条的镜像 —— 那次是拉杆归 `VisualFeedback`，这次是门归 `RoomShell`。

**为什么是 0.6 而不是拉杆的 0.3：** 门走 **10.58** studs，拉杆一抛约 **0.7**，
差 15 倍。同一个 0.3 会让门以 35 studs/s 飞过去，比瞬移好不了多少。0.6 s 是 17.6 studs/s ——
一扇**带动力**的门的样子。缓动仍然**不进 Config**（和 Phase 59 同一条理由）：
它不是谁能调的数字，是机构的手感，`Quad/Out` 和拉杆用同一套词汇，
**一个控制家族不该有两种手感**。

**两个非显然点：**

1. **创建前先 `Cancel()`**（`DECISIONS_2` 188）。和拉杆那边同理：一个属性上两个活着的 tween
   逐帧竞争，赢家按帧决定。但门这里更难看 —— 中点被打断的话，面板可能停在**谁都没要求过的高度**，
   而那是**世界状态**，不是 Console 上的一个姿势。`Cancel()` 留在原地，新 tween 从那里继续。
2. **tween 常量声明在 `Initialize` 之前**。`Initialize` 要读 `ShutterTweenSeconds`，
   而一个**声明在函数体之后**的 `local` 仍然编译得过，函数里的名字却解析成**全局**、读出来 `nil`
   —— 症状是「这个旋钮没反应」，**报错一个字都没有**。

`applyShutters` 原来是：

```lua
shutter.frame.CFrame = open and (shutter.closed - travel) or shutter.closed
```

现在是 `Cancel()` 之后 `TweenService:Create(frame, shutterTweenInfo, {CFrame = goal}):Play()`。
**落位仍然是同一个 `goal`**，所以「开 = 关 − (0,10.58,0)」这条世界空间减法的语义**一个字没动**
（中间那扇 `Frame` 绕 Y 转了 90°，所以不能写成 `CFrame.new(0,-travel,0)`）——
变的只有「怎么到那里」。

### 60.2 验证（§4.4）—— 驱动的就是发货的 `Refresh`

把 `Config` + `RoomShell` `Clone()` 到 `SSS.MCP_ShutterVerify` 再 `require`（§0.15），
**指向的仍是 `workspace` 里的真部件**；驱动的是**真的 `RoomShell.Refresh`**，不是复刻的逻辑。
`initialize` 抓到 **20 灯 / 8 光源 / 7 监视器 / 3 扇门**，三者 `Anchored` 全 `true`。

| 检查 | 量到的 |
|---|---|
| 关 → 开：全程单调，**没有一次向上** | `worstUpStepY = 0` |
| 开位落点 | `[271.619, 271.619, 271.620]`，期望 `[271.619, 271.619, 271.620]`，**误差 0** |
| 行程 | **10.580**（= `ShutterTravel`） |
| 开 → 关：回到作者姿势 | `[282.199, 282.199, 282.200]`，**误差 0** |
| 关的过程**从不向下** | `worstDownStep = 0`（151 tick） |
| 真正走完耗时 | **0.583 s**（配置 0.6） |
| 中途 `Cancel` **不跳变** | 开关那一刻前后两帧差 **0**（`switchGap = 0`） |
| 被打断后仍精确落档 | `[282.199, 282.199, 282.200]`，误差 0 |
| 刚性：门里 6 个部件相对 `Frame` 的偏移 | 漂移 **0**（`Glass` 跟着走，被焊着） |
| 门以外被写到的属性 | **0**（无 `NeonPart` 颜色/透明度、无 GuiObject、无 ScreenGui） |
| 还原后世界漂移 | **0**，临时 Folder 已删 |

**「门以外 0 写入」这一格是特意设计出来的，不是运气**（`DECISIONS_2` 192）：验证脚本先把
**整个写入面**（三扇门里所有 `BasePart` 的 CFrame + 全 Workspace 的 `NeonPart` 颜色/透明度 +
**全 DataModel 的 GuiObject 与 LayerCollector`）都存了一份，再拿 `Refresh` 的 quiet 那一拍
去比对。它回 `0`，说明我传的 `state` 就是世界的现姿势 —— 于是后面那三拍里
**唯一会动的只有门**，实验是干净的；同时这些快照就是还原用的那份。

### 60.3 一个必须记下来的方法论坑：Edit 模式的 `Heartbeat` 是**突发投递**的

第一版分析里，逐 tick 位移出现了 **2.707 studs / 16 ms**（≈ 227 studs/s），
而 `Quad/Out` 走 10.58 studs / 0.6 s 的**峰值速度只有 35.3 studs/s** ——
差了 6.4 倍，看起来就像门在起手处**猛跳一下**，而那正是这次改动要消灭的东西。
**我没有把它当噪声放过去**，理由见 `DECISIONS_2` 193。

分开量了两件事，结论是**采样假象，不是跳变**：

- **宏观曲线是对的**：`task.wait(0.25)` 时门在 **274.882**，即行程的 **69.2%**。
  `Quad/Out` 解 `1-(1-x)^2 = 0.692` 得 `x = 0.445`，即 `t = 0.267 s` —— 和 0.25 s 对得上。
  真正落位耗时 **0.583 s**，行程 **10.580** 分毫不差。
- **逐 tick 的位移不能用来判断平滑**：121 个回调里 **111 个** `|Δy| < 0.005`
  —— tween 跟着**渲染步**走，而 `Heartbeat` 回调是**成串**投递的，
  于是「没动」和「一下动很多」交替出现，**总时间和总位移都对**。
- **换成 50 ms 时间桶**：最大桶内位移 **1.934**，而解析上限是 **1.763**
  （`2 × 10.58 / 0.6 × 0.05`）；桶边界最多能跨到 0.1 s，对应上限 3.53 ——
  1.934 落在诚实区间内。

**所以规矩是：Edit 模式下量「动得平不平」，用时间桶 + 总时长，不要用逐 tick 差。**

### 60.4 `src/ReactorBackend/` 七个模块全部对齐（本轮顺手做掉的欠账）

`export_rbxm` 在这台机器上**是坏的**（两次 `MCP error -32603: Studio plugin connection timeout`，
单发和并发都试过），所以字节级同步只能靠**读回来比哈希**。第三方的 `get_script_source`
这次也超时了；**官方 `rblx_execute_luau` 是活的**（§0.17 那条通道判对了）。
39 KB 的源码不进上下文：起一个**临时** sink（**8790**，不是项目的 8765）收，
比完 md5 再搬进 `src/`，用完立刻停掉、删掉临时目录。

| `src/ReactorBackend/` | 字节 | djb2 | 对活模块 |
|---|---|---|---|
| `Config.luau` | 10943 | `0xdc1c7e23` | **IN SYNC** |
| `ControlBinder.luau` | 5792 | `0xdb33f7bc` | **IN SYNC** |
| `Engine.luau` | 15612 | `0xda7a023a` | **IN SYNC** |
| `RoomShell.luau` | 19401 | `0x95a54194` | **IN SYNC** |
| `Runtime.server.luau` | 4108 | `0x3f0fb2b0` | **IN SYNC** |
| `StateBridge.luau` | 3878 | `0x33e54650` | **IN SYNC** |
| `VisualFeedback.luau` | 38996 | `0x0c1c5712` | **IN SYNC** |

`VisualFeedback.client.luau`（6510 / `0x63ca7e60`）在 `ReactorBackend` 下**没有对应物**，
它镜像的是 `StarterPlayer.StarterPlayerScripts.VisualFeedback`（同字节同哈希）。
顺手在**属性层**确认了它 `Disabled = true` ——
头注释写着 `SUPERSEDED 2026-09-26: disabled, not deleted.`，而**注释会撒谎、属性不会**。
这条很重要：如果它活着，它就是一个**逐 `Heartbeat` 写 `LeverUnion.CFrame` 的客户端写入者**，
Phase 59 加在服务端的那个 tween 会被它**逐帧按回去**。

### 60.5 `start_services.bat`（项目根，2303 字节，纯 ASCII + CRLF）

把 `docs/RECORDER_HOWTO.md` 里那两条命令收进一个双击就能起的文件：**8765 = `receive.py`
sink（写入 `Data\`）**，**8766 = `http.server`（伺服 `_tools\`）**。
两个**独立窗口**，各留各的日志，关一个不影响另一个。

三个不显然的地方，都是照着踩过的坑写的：

- **`cd /d "%~dp0"` 放在最前**，因为 `--directory _tools` 是**相对路径**；
  不 `cd` 的话从别的目录双击就伺服到别处去了。两个目标路径仍然给全（`%~dp0Data` / `%~dp0_tools`）。
- **起之前先看端口**（`netstat | findstr LISTENING`）。第二次起的那个**不会响亮地失败** ——
  端口被占，它绑不上就死，窗口一闪而过，**看起来和「服务已经在跑」一模一样**。
- **横幅里直接印出 `loadstring(...)` 那一行和热键**，省一次翻文档；
  `RightShift` = 采集器封存，`RightAlt` = 监视器推文件，`RightControl` = 停。

**没有运行它** —— 起后台服务不是这轮该做的事（用户没说现在就开）。
写完之后做的检查是**不会启动任何东西的那部分**：`where py` 判定走 `py -3` 分支、
两条端口探测在当前（两个端口都空着）都**不**报 warn、两个目标文件都在。
**当前端口状态：8765 和 8766 都是空的**（`curl` 回 `000`）。

### 60.6 这一轮**没有**验到的，写在这里

- **Play 模式里门看起来平不平，没测**（§0.16：这套工具注册不了 server / client peer）。
  上面所有数字都是 **Edit 模式**（`Heartbeat` ≈ 60 Hz）量的。Play 逐帧步进只会更细 ——
  但**这是推断，不是观测**。
- **「拉开机拉杆 → 百叶窗缓动」这条端到端链路没跑**：我是直接驱动 `RoomShell.Refresh`
  验的这个写入者。`state.shuttersOpen` 由 `Runtime` 从 `Engine` 状态推上来，
  那段没动过，但**没在这轮里跑过**。
- **`Config.Shell.ShutterTweenSeconds` 走的是哪一支没区分开**：live 是 `0.6`、
  模块兜底也是 `0.6`，所以量到的 0.583 s **不能证明**它读的是 Config 而不是兜底。
  真要分开得临时改成别的值 —— 那会动 `Config`，这轮没做（`DECISIONS_2` 190 的
  warn-once 分支因此也**没被执行过**）。

### 60.7 回归门（`bash _tools/run_tests.sh`）

**rc=0，528 行，全绿。**这一轮**一个 `_tools/` 文件都没改**，所以这道门在这轮是
**确认**而不是**证明** —— 它说的是「我改的东西没有波及脚本那半边」，不是「我改对了」。
后半句由 §60.2 那张表负责。

逐节：`clock 10/0` · `watch 74/0` · `watch(boom) 5/0` · `watch(boot) 7/0` ·
`watch(nolever) 6/0` · `watch(nopath) 5/0` · `watch(nowindow) 6/0` · `watch(closewin) 7/0` ·
`transport_probe 23/0`。变异：watch 27/27、gui 10/10、transport_probe 4/4、
end 3/3（全承重）、flow 8/8（7 承重 + 1 记账为冗余）。

**发货文件三个 md5 当场复核，与 §58 记的一致**（核 md5，不核时间 —— Phase 58 那次
「你这趟跑的是旧副本」就是时间误导人）：
采集器 `9979a0b20ff41c2d1e78938cd8d7fc8c`、
监视器 `e83d725dee65993738f99d66a609ce80`、
探针 `5acde17d2bccfa65949c9a4b2bec9a90`。

---

## Phase 61（2026-09-30）—— 第一个真的在原版里跑起来的注入：三个脚本都到了，窗口没开

**这一趟的全部数据在盘上，全部由「脚本自己写文件」这条路拿到（§0.16/§0.17）。**
用户自己起了两个服务（`start_services.bat`）：sink `receive.py --port 8765 --dir Data`（PID 8508）、
文件服务 `http.server 8766 --dir _tools`（PID 19532）。注入顺序是老规矩：先起服务 → 注入 → 走人。

### 61.1 三个脚本**都跑起来了**，这一条以前从来没有过字节支持

| 脚本 | 证据 | 结论 |
|---|---|---|
| `transport_probe.luau` | `Data/probe/260930-200834/summary.txt` | **第一次真的回答出传输问题** |
| `TRG_original_watch.luau` | `Data/originalwatch/260930-200834/` 11 份产物，**没有 `error.txt`** | 普查 + 扫描 + 音频全都活了 |
| `TRG_original_recorder.luau` | `Data/flow/original_260930-200834`（512393 字节 / 3349 行） | 完整抓下一次开机 |

**传输判决（第一次有数）**：`winner=http_request`。能用：`http_request`(200)、`request`(200)、
`http`(200)、`getgenv`(200)。不在：`syn`、`fluxus`、`krnl`。在位但坏：
`httpservice`（`loadstring:82: Blocked function`）、`httpget`（`invalid argument #1`）。
**所以两份脚本走的那把梯子在这一台执行器上第一级就中** —— 之前只有「它没写文件」这一种观测。

**用户自己注入时用的就是 `game:HttpGet(...)`**，而它确实工作（字节到了盘上）——
探针把 `httpget` 判成坏的是**探针的调用形状**（`(url, body)` 对 `request` 族），
不是 `HttpGet` 本身。读探针产物时别把这两件事混起来。

**监视器**：`rooms.txt` 头 `71236 instances, 557548 watched properties, 1823 roots watched,
3 root(s) skipped`、`61602 instance(s) needed a path suffix`、`pinned by name: Alarms`。
`inventory.txt` 11.7 MB、`changes.log` 10439 行、`audio.txt` 79432 字节、
`audio_hooks=4131 refused=0 events=320`、`sink=ok`、`sink_outages=0`、`fatal=none`。
**采集器**：`EVT2 START hooks=1019`、开机链完整 ——
`CLICK RoomLight` → `MonitorPower` → `Shutters` → `MonitorBoot` → **`CLICK StartUpLever`** →
`CLICK HDEF-PowerLever`，随后 `COMPUTATIONAL BENCHMARKS UNSATISFIED` /
`PRIMING ALL COMBUSTION LASERS` / `TESSERACT MAINFRAME OVERCLOCK INITIATED` /
`ALL SYSTEMS READY, CORE IGNITION IMMINENT`，`s.CBL*.TempVal=875→925`。

### 61.2 【缺陷一，已修】开窗口的那个 hook 装晚了 28 秒

`window.txt` 一句话把两个事实钉在一起：
```
opened_at=not yet why=(nothing has opened it)
lever_hooked=true
```
**「hook 装上了」和「什么都没打开它」同时为真。** 而采集器那边
`CLICK StartUpLever` 夹在 `S 40 t=18.11` 和 `S 67 t=27.03` 之间 —— 拉杆是 **t≈20 s** 按的。
监视器第一行 `changes.log` 是 **t=47.93**：**普查占掉了 48 秒**，而 `attachWindow()` 在
`pcall(bootWalk)` **之后**。于是 hook 对着一个**已经发生过的点击**连上了线，
而文件里的读法和一个拼错的 `LeverPath` **完全一样**。

原注释替这个顺序辩护的那句话是「the census finishes in seconds」——**测量是 48 秒**，
它依赖的「操作员要走过去所以有掩护」是 15 秒。**修**：`attachWindow()` 挪到 `Start()`
里同步调用（`task.spawn` 之前）。**安全**，因为它不碰普查的任何产物：`resolvePath`
从 `workspace` 往下 `FindFirstChild`，不看 `ents` / 选根 / 预算。
**代价这一头是全部**：窗口只开十分钟（61.3），而开机不能重来（「我没办法随便开关机」）。

**守卫**：`--boot` 场景（普查故意抛错）多一条检查 —— **普查死了 hook 也必须装上**。
它同时是「hook 不依赖普查」的**证明**而不只是症状。变异测试加一条
（`if #ents > 0 then attachWindow() end` = 「只在普查之后才装」，见 `DECISIONS_2` 200），
`watch mutations 27/27 → 28/28`，`watch(boot) 7 → 8 PASS`。

### 61.3 `EndMins = 720` **是对的** —— 我推翻的是我自己上一轮的判断

我上一轮说「12:00 是中午，720 把窗口提前到换班前十分钟」——**错的，先撤回。**
`Stats.GameActive` 在整个倒计时里是 `false`，在 **720 前后两分钟**翻成 `true`
（`original_260926-230049` t=98.47、`260927-123212` t=153.58），然后**跨过中午一直为真到那趟结束**。
所以**半夜 12:00 是「班次开始」，中午是交接** —— 而那两句玩家规则要的窗口，
正好是 `GameActive` 变真时**结束**的那一段。四个观测趟**全部**注于 `q.clock=710`（11:50 PM），
所以窗口宽十个游戏分钟 ≈ **两个真实分钟**（实测 **12.3 真实秒 / 游戏分钟**）。

**我上一轮为什么会读错**：`260927-123212` 在 720 之后一路跑到 `q.clock=1130`（6:50 AM）
而且没有任何边界事件 —— 看起来正好否定 720 是边界。它否定的是「720 对**采集器**是边界」；
**两份脚本问的不是同一个问题。** 一个文件两个消费者两个边界，这一条写进 `DECISIONS_2` 199。

> **【2026-09-30 更正 —— 本节整段作废，见下。】**
>
> 用户当天把「12：00」这个歧义钉死了：**「何时结束？：时钟到达12PM时结束」**。
> **12PM 是中午**，所以窗口的终点是 **11:59 AM → 12:00 PM 的交接**（表盘 `1439 → 0`），
> 不是 `EndMins = 720`（半夜）。
>
> 上面这段推理里唯一错的是**结论**，它的**证据**是对的、也是我读错的原因：
> `s.GameActive` 确实在 720 前后由假变真、确实跨过中午一直为真。但这说明的是
> **半夜 12:00 是「班次开始」（开机那一刻），中午才是交接** ——
> 而玩家要记录的正好是**开机之后的一整个班次**，也就是从拉杆一直录到**第二天中午**，
> 约 **730 个游戏分钟**。我上一轮把「`GameActive` 变真」当成了窗口的终点，
> 其实它是窗口的**起点**（拉杆就在那个位置按下）。
>
> 我这个错还有一个形状上的教训：**`EndMins = 720` 这个名字本身就带着答案的暗示**
> ——「End」是**我起的名**，而它其实是个「开始」。一份配置项的名字如果替你回答了问题，
> 那你读到的就不是测量。取舍更正写进 `DECISIONS_2` **201**（它更正 199）。
>
> 代码已经改了（**2026-09-30，`w60`**）：阈值换成**下降沿**。
> 表盘在一次班次里**单调**（710→717 是一趟，710→0 是另一趟），所以「到了一个值」根本
> 表达不了交接 —— `mins >= 0` 在每一趟的每一拍都为真。现在存的是**落差**：
> `WrapDropMins = 60`（只有 1439→0 的落差能产生它；表盘在班次内不会倒退），
> `EndPolls = 2`（连着两拍都读到下降才算，一次误解析不能花掉只能开一次的那次开机）。
> 60 这个数还有一条实测量撑腰：班次活起来之后表盘约 **1 游戏分钟 / 真实秒**，
> 而监视器自己的扫描在饿着的时候量到 **1089 ms** —— 一次六秒的卡顿会把交接后的第一拍
> 落到 12:06 PM，任何「接近 0」的窗口都会漏掉，落差不会。

### 61.4 【缺陷二，已修】窗口没开时队列在长，而上限在吃队列的头

`health.txt` 报 `dropped=794`、`summary.txt` 头一行就是
`# WARNING: 794 queued change(s) were dropped`。机制是**两个机制复合**：
`flush()` 在 `windowState` 为 `'waiting'` 时**什么都不投**（那正是窗口的指令），
而下面那个 `MaxQueue` 截断**每一拍都照跑**。于是「窗口关着 = 队列只进不出 = 上限吃队头」。

数量级不是舍入：这趟 46 秒产出 10439 行，其中 **t=70..80 那一个十秒桶里 6463 行**
（CBL 点火那一段）。**4000 的上限比一次开机的峰值还小**，所以这种趟**每一趟都丢开头**。
`4000 → 20000`（约 4 MB，按实测 190 字节/行）。取舍 `DECISIONS_2` 198。

**和 61.2 是耦合的**：截断**只在窗口关着的时候咬**，所以它**恰恰摧毁窗口失败那些趟的证据**。
修好 hook 拆掉扳机，抬高上限拆掉底下的坑。

### 61.5 回归门（`bash _tools/run_tests.sh`，rc=0，530 行，全绿）

`watch 74/0` · `watch(boom) 5/0` · **`watch(boot) 8/0`** · `watch(nolever) 6/0` ·
`watch(nopath) 5/0` · `watch(nowindow) 6/0` · `watch(closewin) 7/0` · `transport_probe 23/0`；
变异 **watch 28/28**（新增那条见 200）、gui 10/10、transport_probe 4/4、end 3/3、flow 8/8。

**三个 md5（注入前核这个，别核时间）：**
采集器 **152467 / 3304 / `9979a0b20ff41c2d1e78938cd8d7fc8c`（未改）**、
监视器 **130438 / 2439 / `ac2af3cc030a042b81584d1e476d09b2`（build `w59`）**、
探针 **10752 / 217 / `5acde17d2bccfa65949c9a4b2bec9a90`（未改）**。
**8766 当场 curl 复核：三个 md5 与盘上逐一相同。**

**下一趟只重注监视器一份就够**（采集器和探针这一轮没改），
但**两份一起重注也无害** —— 只是别按 `RightShift`（那是采集器的封存键）。

> **【以上三个 md5 已全部作废】Phase 62 在同一批里改掉了采集器和监视器两份，
> 现在以 Phase 62 的表为准。** 这一节保留的是**当时那一趟**的字节，
> 它记录的是「61 那一趟跑的是哪一份」—— 那件事不会因为后面改了脚本而变。

---

## Phase 62（2026-09-30）—— 采集器：driver 整个删掉，反应堆读数加一道「核心真的开了」的闸  [DONE — 本机验过，原游戏还没跑]

用户这一轮的三句话（原文，是他对**三份注入脚本**的分工说明）：

> `transport_probe.luau`：**不变** —— 探针不需要动。
>
> `TRG_original_recorder.luau`：**注入后立刻开始（注意在核心完全开启前不要采集温度、压力等），
> 并且不需要什么driver，只需要seal：SEAL的情况是1：手动关机，2：核心自动关机如熔毁，温度过低等**
>
> `TRG_original_watch.luau`：**多功能，以后需要监视更多东西，但是现在目的：采集开机内容，
> 何时采集？：玩家按下开机按钮时开始监听所有控制室+腔室+警报+音频变化（所有监视器的GUI也要！）
> 何时结束？：时钟到达12PM时结束**

**监视器那一半这一轮一个字都没改** —— 它已经是那句描述了：`Pinned = {'Alarms', 'Monitors',
'MonitorsFacility'}` 就是「所有监视器的GUI也要」（61.2 已经是它最近一次改动），
窗口的终点改成 12PM 见 61.3 的更正框。**改的是采集器，两件：A1 核心闸，A2 删 driver。**

### 62.1 A2 —— DRIVER 整段删除：**十一刀，每一刀两端都断言**

「不需要什么driver，只需要seal」是**删一个能力**，不是改一个数字，所以它撞的是 §1.4 第 2 条
（不许在没有替代品的情况下删除功能）。**替代品是操作员自己的手**，而这个替代品**本来就在文件里**：

**关键的一读：CLICK hook 不在 DRIVER 段里。** 删之前先确认了这一点 ——
hook 遍历世界里**每一个** `ClickDetector` 和 `ProximityPrompt`（1019 个），按路径命名。
所以 driver 走了之后，**操作员自己按的每一个开关照样进文件**，
而且比 driver 记的更全（driver 只按那两个，hook 记全部）。
**这一条是这次删除之所以安全的原因，不是它的注解。**

十一刀全部用**行区间**切，每一刀**两端各断言一个子串**（`_tools/_attic/_scratch_strip_driver.py`，
一次性手术脚本，已归档）：152467 → 120575 字节、3304 → 2633 行。
其中**第 5 刀（1588..2163，整个 DRIVER 段）两端都是没特征的**（一个空行和一个裸 `end`），
所以它**额外钉了四个邻居**：上面那段的收尾 `end`、DRIVER banner、下面的空行、
**以及 CLICK hook 的注释行** —— 这一刀最不能带走的就是 hook。
**第 4 刀（driveStep 调用点）是唯一一个「失败模式是静默」的**：它上下的
`local tempF = last['m.temp']` / `local isRunning = ...` / `if not flowArmed then`
是 FLOW 边界要用的，切过头会切出一个**能解析、但 flow 永远不 arm** 的文件，
所以那三行单独钉了断言。

**带走的是两个「只为 driver 存在」的东西**，而不是留着当没读数的配置项：
`ShutdownEndsShift`（只在 `driveStep` 里读）和 `pollDt`（唯一读者是 `driveStep` 的调用点）。
**留一个没有读者的 config 键 = 一条关于不复存在的行为的声明**（§0.13）。

**三份 driver 文件进了 `_tools/_attic/driver/`**（`build_driver_test.py` /
`selftest_driver_test.py` / `_driver_states.luau`），**不是删掉**：那里的场景是**关于这台机器
两个开关的测量**，万一 driver 要回来，那是现成的全部已知。`run_tests.sh` 里那段
「THERE WAS A SIXTH」把这件事和理由写清楚了；第 2 条约束的代价分栏见 `DECISIONS_2` **202**。

**顺带修掉四处过期的散文**：hook 的「wall-clock stamp ... for the same reason the driver s
dwell timers did」、receipt、SAM announce、以及 `(the on-screen phase, the driver's waiting_up)`。
**散文说的谎和代码说的谎一样贵** —— 它会让下一个人以为还有个 driver 在按东西。

### 62.2 A1 —— THE CORE GATE：「核心完全开启前不要采集温度、压力等」

**信号是 `Stats.GameActive`，而且它是量出来的不是猜的。** 盘上两趟把它**从两边夹住**：

| 趟 | `GameActive` | 说明 |
|---|---|---|
| `original_260930-200834`（61 那趟） | **一次都没真过** | 拉杆**按了**（`EVT3170 CLICK StartUpLever`）、开机 banner 一路跑到 `ALL SYSTEMS PRIMED`，**核心仍然没亮**：整份文件只有 4 次状态跳变、全在 t=5.28。所以它**不在拉杆上**发生，**也不在 banner 结束时**发生 |
| `original_260926-230049` | **t=98.47 变真** | `s.Core.TemperatureVal` 在 t=1.34 是 0 → t=88.53 是 510 F → t=97.90 是 9420 F → **t=98.47 `GameActive=true`**。它在**点火斜坡的顶端**翻，那正好就是「核心完全开启」 |

**「闸」是 latch，不是每拍求值的谓词，而 latch 不是为了省 CPU：**
被闸住的正是**关机之后还要继续读**的那些读者 —— 冷跳闸那条臂要在 `SealColdSamples` 拍里
读 `m.temp` 低于 `LowTripF`。**一个「`GameActive` 变假就把闸关上」的实现，
会把停机规则赖以成立的那些读数全部静音** —— 也就是用户点名的 SEAL 条件 2 永远检测不到。

**「扣住」= 根本不写，不是过滤。** 关键实现细节：闸关着时**连 `last` 都不碰**。
过滤（写进 `last` 但不发）和扣住**产出逐字节相同的文件**，一直到**点火那一拍的值恰好等于
开机前的值**为止 —— 而那**恰恰是常见情况**（冷堆温度就是 0），于是过滤版读到「没变化」，
**点火永远不会被报出来**。这是这个文件里最难看出来的一行错，所以它有自己的变异测试。

**它故意不管的东西**：通用读数走查（`t.*`）和设施面板。**那两处正是开机流程本身被记下来的地方**，
把它们闸掉等于把这次采集的目的扔掉。闸只管**反应堆自己的读数**（`ReactorFrame` 的标签和
`Stats.Core`）。

**`Stats.Core` 是「容器测试」不是叶子名单**：`path == 'Core' or path:sub(1, 5) == 'Core.'`
—— 名单会被一次改名静默逃掉，容器不会（`TemperatureVal` / `PressureVal` / `RadiationVal` /
`OutputVal` / `HDEFVal` / `BreachVal` 全在它底下，以后加进去的东西不用改这个文件就覆盖到）。

**闸开的时候发一条 `COREGATE` 事件**，所以文件自己带着「从这里开始的读数是活的」这个事实：
读者不用再从温度反推「核心是在这里开的」还是「采集器来的时候就已经开着」。**只发一次**
（每拍一条就是两千行噪音，而这个文件的整个设计是一行 = 一个变化）。

**遍历本身不闸**：`seen[path]` 照旧先填，所以被扣住的键**仍然是 STATADD/STATDEL 记账认识的键**，
容器的来去照旧记 —— 否则闸开前那一拍会宣布整个 `Core` 容器消失了。

### 62.3 【本机验过，原游戏还没跑】闸的 harness：32 条，十条组

`_tools/build_gate_test.py` 从**发货的采集器**里按文本抽出**两段**（闸本身、和 `readStats` 整段），
按原顺序缝起来 —— 只抽一半的 harness 会同意一个**不发货的版本**。
`_gate_states.luau`（16997 字节 / 422 行）是产物，**改 builder，不改它**。

**G1** 猜不开（假 / 缺 / 同名非 ValueObject / 真）· **G2** 会 latch（旗标变假后仍开）·
**G3** 什么算核心读数（`Core` ✓ / `Core.TemperatureVal` ✓ / `Core.A.B` ✓ / `CoreStuff` ✗ /
`Reactor.Core` ✗ / `Cor` ✗）· **G4** 扣住就是**没写**（核心值不在 `wrote` 里、**也不在 `last` 里**，
而**非核心的照写**，包括闸自己要读的 `s.GameActive=false`）·
**G5** 点火以**新键**到达（同一个值，闸开后**仍然要写**）· **G6** `readStats` 自己会开闸 ·
**G7** `COREGATE` 三拍只发一次 · **G8** 清单仍看得见被扣的键（`statsSeen[...] == true`，无 `STATDEL`）·
**G9** `Core` 底下的 `StringValue` 走 `putText` 那条路也被扣（闸只盖 `put` 会漏掉开机前的错误文本）·
**G10** 闸**重新取** `Stats`。

### 62.4 这套 harness 逼出来的一个**真缺陷**，和三个 harness 自己的错

**真缺陷（G10 找到的）**：`coreGateOpen` 只读加载时抓的那份 `MainData`。
采集器**在 `Workspace.Stats` 存在之前**注入的话，它拿到 nil，闸会一直关到**别的读者**恰好刷新它
—— 也就是这个闸的行为**取决于「属性走查有没有先跑」**，而两个调用者的设计本来就是要拆掉这种顺序依赖。
**修**：`coreGateOpen` 自己 `if MainData == nil then MainData = Workspace:FindFirstChild('Stats') end`。
**G10 是「注入得早」那一趟会精确命中的场景。**

**三个 harness 自己的错**（每一个都先让 harness 红在一个正确版本上）：
① `block_from` 数 `function`/`end` 词元 → 被 `readStats` 里那句一行的
`if ... then scan(...) end` 骗过，把函数切开了。**改成按缩进取**
（往下第一个**正好是 `end`** 的行），并且**加了词元断言**：切短了就红，不会安静地测半个函数。
② 闸那段以 `local` 开头而不是 `function`，所以按缩进只能取到 `coreGateOpen` 的尾巴、
把 `isCoreStat` 落在外头 —— **改成先切 `isCoreStat`、再往回放宽**，并断言它不在声明之上。
③ `reset()` 原来定义在**被抽出来的闸上方**，于是 `coreLive = false` 写的是**全局**，
而闸读它自己的**局部**同名变量 —— **latch 在场景之间从不清除**，
G5/G7/G9/G10 集体红在一个正确的采集器上。挪到 TAIL（抽出区下方）。
**一个 reset 悄悄不干活的 harness，是一个把上一场景的状态当答案报出来的 harness。**

另外两条**断言**自己的错：G5 原来断言「开机前那一拍关于核心什么都没写」，
用 `keys(0) == ''` 判 —— 但 `s.GameActive=false` 是**合法**会被写的，
所以改成 `not has(wrote, 's.Core.TemperatureVal=0')`。以及 harness 原来**返回字符串但退出码是 0**，
于是行内 `selftest` 把六个真的变红了的变异全报成「stayed GREEN」——
**一个失败对 `$?` 不可见的套件只是一半的套件**（`_end_states.luau` 早就写了 `os.exit(1)`，抄过来）。

### 62.5 变异测试：**6 条必须红在指定的那条检查上，2 条必须保持绿**

`_tools/selftest_gate_test.py`。每条都是**有人真的会写出来的**错，不是随机改动：

| 变异 | 被哪条抓住 | 它模拟的真错 |
|---|---|---|
| 「扣住」变成「过滤」（写进 `last` 但不发） | **G5** | 上面 62.2 那条最难看出来的一行错 |
| 闸不再 latch | **G2** | 「变假就关闸」→ 停机规则赖以成立的读数被静音 |
| `isCoreStat` 放宽成前缀测试 | **G3** | `CoreStuff` 之类被吞掉，症状只是「某个键出现得晚」 |
| `readStats` 依赖 `readReactor` 先跑 | **G6** | 顺序依赖。**在真跑里看不出来**（真循环里 readReactor 就是先跑），所以只能在这里抓 |
| 同名非 ValueObject 当旗标 | **G1** | `Folder.Value` 在 Roblox 里是 **error**，会在第一拍把整份采集带走，而且没有收据 |
| 闸不再重新取 `Stats` | **G10** | 62.4 那个真缺陷 |

**保持绿的两条**（这一类「绿才是通过条件」）：① **闸的默认值是开的** ——
harness 对它是**瞎的，而且是有理由的瞎**：`reset()` 在每个场景开头清 latch，
所以声明的初值在任何检查跑之前就被覆盖了。**写下来是为了让它继续是一个已知盲区，
而不是变成一个以后被人重新发现的洞**；它也顺带证明**变异体确实到了 harness**
（states 文件里带着新的声明）。② 闸的注释被改动 —— 证明**抽的是发货字节**，
不是一个会过期的副本。

**顺带修了两处「builder 把值也钉住」的错**，两次都表现为
「红了，但红在错的检查上」：`GATE_OPEN` 锚点和 `local coreLive = false` 词元**都带着初始值**，
所以「默认值改成 true」这个变异让 **builder 建不出来**，而 **builder 拒绝构建不算 harness 抓到东西**。
锚点和词元只该钉**声明**，不该钉**它说什么** —— 钉了值，builder 就成了采集器行为的第二份副本。

### 62.6 回归门（`bash _tools/run_tests.sh`，**rc=0**）

`panel/end/clock/gui/flow/gate` 六个 harness 全部 rc=0；`clock 10 PASS`；
`gate **32 PASS / 0 FAIL**`；`watch 74/0` · `watch(boom) 5/0` · `watch(boot) 8/0` ·
`watch(nolever) 6/0` · `watch(nopath) 5/0` · `watch(nowindow) 6/0` · `watch(closewin) 7/0` ·
`transport_probe 23/0`；变异 **gate 6/6 + 2 FOLLOW**、**watch 29/29**、gui 10/10、
transport_probe 4/4、end 3/3、flow 8/8。

**三个 md5（注入前核这个，别核时间）：**
采集器 **121202 / 2644 / `48f2c155b7d6342f07cafcfb4404e9e8`（build `r60`，**改过**）**、
监视器 **136927 / 2527 / `2d3d7da48db284e64f0321b5d226e605`（build `w60`，**改过**）**、
探针 **10752 / 217 / `5acde17d2bccfa65949c9a4b2bec9a90`（未改）**。

**下一趟：采集器和监视器**两份**都要重注**（61 那趟存的旧副本分别是 **`r58` / `w58`** ——
先前这里写的是 `w59`，**错**：产物第 2 行 `build=r58`、`alive.txt` 第 2 行 `build=w58`，
盘上没有产物带 `w59`）。
**别按 `RightShift`** —— 那是采集器的封存键。
`_tools/_attic/_scratch_strip_driver.py` 是这一轮的一次性手术脚本，**已归档，不要再跑**
（它会拒绝第二次运行，但它是按行号切的，行号只对当时那份文件有效）。

### 62.7 这一轮**没有**做的事

- **探针不变**（用户明说）。
- **监视器一个字没改**（12PM 那件事 61.3 已经做完）。
- **没在原游戏里跑过**。上面每一条都是**本机**证据：源码 + harness + 变异。
  **哪一半验了、哪一半没验，分开写**（§0.16）——
  验过的是「代码是它声称的样子」，**没验的是「在原版里它真的是那个样子」**。
- **P4:A 冷却泵 2/3 档**、**P6:A 的 187 键探针**照旧排开、不叠在这一轮。


---

## Phase 63（2026-09-30）—— 把 Phases 59–62 提交进仓库，以及提交路上翻出来的三件事  [DONE — 本机验过]

**这一节不是新功能**，是「把前面四个 Phase 落袋」这一步自己的记录 —— 但它翻出来三件事，
其中一件差点让一个 **11.7 MB 的文件**进仓库，所以它有自己的条目。

### 63.1 提交的切法：**两个**

四个 Phase 的改动本来是一坨未提交的工作树。按**主题**切成两刀，而不是按 Phase 切四刀：

| 提交 | 内容 | 为什么不并进另一刀 |
|---|---|---|
| `c816196` | Phase 59/60 的**两个 tween**（`VisualFeedback` / `RoomShell` / `Config`）+ `start_services.bat` + `docs/SYSTEMS.md` + `docs/airemake/REWRITE_STATUS.md` | 这是**游戏内**的事 |
| `3244802` | Phase 61/62 的**注入脚本**（`_tools/**`）+ 两个 `docs/` + `.gitignore` + 三组标定产物 + `MANIFEST.txt` | 这是**注入工具**的事 |

**为什么不是「一刀一个 Phase」**：`git add -p` 在这个环境里不可用（交互式），而
**`Config.luau` 同时带着 59 和 60 两个常数**，按文件切不干净。
按主题切是文件边界上唯一诚实的切法，而它恰好也把「游戏内」和「注入工具」分开了。
第一刀重做了一次 —— `_tools/build_driver_test.py` 的改名（R）**早就在索引里**，
第一次 `git commit` 把它一起扫进去了，而它的名字跟 tween 一个字的关系都没有。
`reset --soft` + `restore --staged` 重做，改名回到第二刀。

### 63.2 【翻出来的事一】`Data/originalwatch*/inventory.txt` 的规则**静默匹配不到任何东西**

第一版的规则是**照抄** roomwatch 那条写的 —— 而两边的路径**不同形**：

```
Data/roomwatch_runN/inventory.txt          ← 旧规则 Data/roomwatch*/inventory.txt 匹配得到
Data/originalwatch/<run>/inventory.txt     ← 同一个形状匹配不到：多一层
```

后果：`git add Data/originalwatch` 把 **11,684,084 字节**放进了索引（`--stat` 报 123,423 行插入），
而**没有任何东西会报错** —— 忽略规则匹配不到就是匹配不到。
修法是 `Data/originalwatch*/**/inventory.txt`，并且**用 `git check-ignore -v` 验它真的命中**
（它会回显是哪一行规则命中的，这正是「规则写了」和「规则生效了」的区别）。
取舍 `DECISIONS_2` **206**。

### 63.3 【翻出来的事二】`_tools/_probe/` 不是产物，是 **harness 的 fixture run**

提交前它是唯一没被任何规则覆盖、也没被任何文档提到的未跟踪目录（37 KB）。
差点当成「某次真实采样的孤儿产物」，**读它自己的三个字段就知道不是**：

- `rooms.txt` 的根叫 `LateA` / `LateB` / `Repeated` / `PreLeverGone` —— 合成的；
- `audio_tally.txt` 的资产 id 是 `rbxassetid://111` / `//222` / `//333` / `//444`；
- `health.txt` 自己的 `sink_last_error` 写着 `_tools/watch_harness.luau:400`。

所以它是**监视器 harness 的夹具跑**，进 `.gitignore`（和 `_harness_out/` 同一类）。
**有一件事我说不出来**：它为什么在 `_tools/` 而不是 `Data/` —— sink 无论 `--dir` 是什么
都写 `originalwatch/<run>/`，而这里的目录名是 `_probe`，所以**中间有人搬过**。
注释里就写成「搬过，机制不明」，不编一个。

**顺带否掉一个我原本要做的更正**：一度以为这 37 KB 是「09-27 那趟监视器真的跑过」的字节、
足以推翻 CLAUDE.md Phase 54 那句「跑过没有字节支持」。**不是** —— 夹具跑的产物不是原游戏的产物，
所以那句话说的事**没有变**，一个字都不用改。这正是 §0.13 那条的现代版：
**断言「没有」之前，先确认自己看的是什么**。

### 63.4 【翻出来的事三】LF 的 `.bat`：**测了，不用改**

`.gitattributes` 钉的是 `* text=auto eol=lf`，所以新提交的 `start_services.bat` 在
Windows 上**会以 LF 检出**。这是经典的批处理坏法，我准备加一条 `*.bat eol=crlf` 例外 ——
**先测**：在 `%TEMP%` 里造两份同样形状的（带 `&&` 控制块、带 `if (...)` 括号块、
带 `goto`/label），一份 CRLF 一份 LF，用 `cmd /c` 各跑一遍。

**两边逐字节一样的输出，连 `goto`/label 那版也一样**（那版的报错是 `setlocal` 的语法，
两份都报）。所以**不加例外**：这台机器上 cmd.exe 不在乎。
取舍 `DECISIONS_2` **208** —— 条目本身就是「不要凭直觉改，先测」。

### 63.5 本轮的验证

- `bash _tools/run_tests.sh` **rc=0**，跑的**就是提交进去的那份字节**：
  recorder `121202 / 2644`、watcher `136927 / 2527`（与 `r60` / `w60` 的记录一致），
  gui 变异套件自报 `shipped file untouched (md5 48f2c155b7d6342f07cafcfb4404e9e8)`，
  gate 变异 `6/6 红 + 2 个 FOLLOW 保持绿`，flow 变异 `8 条按预期`，
  watch / gui / end / 探针各套件自报 rc=0。
- **跑测试没有留下垃圾**：今天这一趟跑完 `git status` 没有任何未跟踪文件 ——
  harness 的 sink 捕获是自建的临时目录，跑完自清。
- `_tools/_attic/MANIFEST.txt` **落后了 21 个文件**（其中就有 driver 那三个，
  也就是 §1.4 第 2 条要指向的那份存档），已按文件系统重新生成成**排序索引 + 生成日期**，
  让「它还准不准」这件事**从文件本身读得出来**。取舍 **207**。

## Phase 64（2026-10-01）—— 「注入之后游戏贼卡」：监视器让帧 + 份额上限（`w61`）  [DONE — 本机验过，原版还没跑]

用户原话一句：「**哦对了还有个问题我注入之后游戏贼卡，解决一下**」。改的是**监视器**，
采集器（`r60`）**一个字节没动** —— 下面第 64.1 节就是「为什么是它」。

### 64.1 先定位，不先改：卡的是监视器，不是采集器

两个脚本**各自测了自己**，所以这一条不需要推理：

| 来源 | 自报 | 读法 |
|---|---|---|
| `Data/originalwatch/261001-125207/health.txt` | `scan_ms=2197`，`watched=71587 props=559942`，`Interval=1` | 一次扫描 2.2 秒，循环每 1 秒就要下一次 —— **一个周期 3.2 秒里有 2.2 秒是它的**，约 **70% 的客户端** |
| `Data/flow/original_261001-125206` 的 `PERF` 行 | `cpu_pct=10.9 worst_ms=885.1` | 采集器占 **11%**，最坏单拍 0.9 秒 |

**这两个数不是估计，是两台脚本在同一趟里各自量的。** 所以「贼卡」的绝大多数在监视器上。

还有一条**被自己的产物否掉的注释**，一起在 `w61` 里改掉了：`Interval` 上面原本写着
「the budget below is set to keep a scan near 300 ms」。那句话是按**我们自己的 place**
标的（30219 件 / 235553 属性，112 ms）；原版是三倍大（71587 / 559942），同一个预算
放进来就是 2197 ms。**注释没有错，错在它是关于另一个 place 的** —— 而原版才是它要跑的地方。

### 64.2 两个旋钮，因为这是两种伤

- **`MaxBlockMs = 25`** —— 让帧。普查 / 扫描 / 建索引**三条**长走查每 25 ms 让一帧，
  2.2 秒的冻结变成 ~90 个短块。**每让一帧要等一个 frame**，所以这是拿墙上时间换响应性。
- **`DutyTarget = 0.30`** —— 份额上限。**光让帧治不了 70%**：那两秒的活还是两秒，
  摊到更多帧上只是把疼摊开。所以循环按**实测的** `scan_ms` 反推该睡多久
  （`idle = work * (1 - target) / target`），把自己压到 30% 以下。

`health.txt` 因此多报四个数：`scan_ms / sleep_ms / duty / yields`。
**"the census finishes in seconds" 那句话的现代版本就是这四个数** —— 修没修好由下一趟的产物说。

### 64.3 【翻出来的事】时间型让帧，把 harness 变成抛硬币

`w61` 改完第一次跑 `bash _tools/run_tests.sh`：**`watch: 73 PASS, 1 FAIL`**，
红的是 `the pre-lever lines were withheld and counted`（`withheld_before_open=0`）。

按 §0.13 的纪律先量块深度再改：把 `MaxBlockMs` 分别设成 `100000` 和 `0` 重跑 ——
`100000` 回到 **74/0**，`0` 掉到 **27/47**。所以让帧**是**唯一的原因，但**不是**唯一的表现：
同一份**未改动**的 `w61` 连跑四次，**3 红 1 绿**。

**根因**：`watch_harness.luau` 用**数 `task.wait` 的次数**来驱动它的变异时间线
（`STEPS[waits]`，`waits` 每被调一次加一）。`breathe()` 让的每一帧都是一次 `task.wait`，
于是「拉杆那一下（`STEPS[3]`）落在普查之前还是之后」取决于**这一趟有多少次让帧真的触发**
—— 而那是**机器负载**的函数。**一份判取决于机器快慢的 fixture，分不清「脚本坏了」和「机器忙」。**

**修法**（`watch_harness.luau`）：**只有带参数的 `task.wait` 才推进时间线。**
循环的节奏是 `task.wait(CONFIG.Interval)`（带参数），让帧是 `task.wait()`（无参数）——
**无参数的那次不是这趟班次的一步**。修完连跑 **8 次，8 次都是 74/0**，
且 `bare_waits=2` 说明**被忽略的那条路确实被走到了**（不是「没触发所以没麻烦」）。

### 64.4 让帧只许改「什么时候」，不许改「记了什么」—— 这条是量出来的，不是断言的

上面那半句只是「让 fixture 不再被它影响」。真正要守的性质是另一条，而且它是**可测的**：

`run_tests.sh` 新增 **`=== watch slicing differential ===`**：跑**发货的那份**，
再跑一份**把 `MaxBlockMs` 强制成 0** 的副本（每 64 个实例让一帧，最碎的切法），
要求两份 `changes.log` **除墙上时钟那一列外逐字节相同**。

结果：**`slicing: PASS -- 19 log line(s) identical with the yield budget at 0`**。

三条纪律写进了这段脚本本身：① 替换前**先断言锚点唯一**（`MaxBlockMs` 在好几条注释里
出现过，宽松的模式会改散文而不改配置还看着是绿的）；② 基线日志**少于 5 行就判失败**
—— 两个空文件当然逐字节相同，那种绿什么都没证明；③ 时钟列**是**允许不同的那一列，
所以剥掉它再比，而不是放宽成「差不多」。

### 64.5 【翻出来的事】注释里一句关于 `duty` 的假话

`duty` 原来注释成「the share of the wall clock -- scan plus the frame waits inside it, plus the sleep」。
**`scanMs` 来自 `os.clock()`，那是 CPU 时间，让帧等的那一帧根本不进它。**
所以照原话读会把 `duty` 读成墙上份额，而它不是。已改成：它是**最后一次扫描的 Lua 工作量**
对**墙上周期**的比，**并且指出偏差的方向** —— 真实周期比 `scan_ms + Interval + sleep_ms`
更长（多出的正是让出去的那些帧），所以**真实份额在打印值之下**：打印 ≤ 目标 = 确实没超，
打印 > 目标 = 值得再看一眼，而不是判决。

### 64.6 上一趟（`261001-125206` / `261001-125207`）的读数

这一趟的产物是这一轮修复的**依据**，也是两份新东西第一次跑在真班次里：

**① 你按了两次开机，游戏只认第二次 —— 盘上的字节说的是同一件事。**
`EVT3163 CLICK StartUpLever` → 提示词翻成 `MASTER SHUTDOWN SWITCH` → **立刻翻回**
`MASTER START-UP SWITCH`，描述是 `Will beep green after proper control room boot-up.`
→ `EVT3167 CLICK StartUpLever` → `EVT3169 ... SUBSPACE REACTOR START-UP SEQUENCE INITIATED`。
**第一下按在「控制室还没 boot 完」上，被游戏退回了；序列是第二下起的。** 你说的没错。

**但监视器的窗口是在第一下开的**（`window.txt`：`opened_at=29.73 why=the start-up lever was clicked at ...`）。
它的判据是「那个 `ClickDetector` 被点了」，**分不出被接受的那一下和被退回的那一下**。
两下相隔约 1.5 秒、中间没有可观测事件，所以这一趟没有任何实际损失 ——
**记下来是因为它不是这一趟才有**：窗口开早一点点，对「开机链完整」这个用途是安全的，
对「从开机那一刻起逐拍记录」是**差 1.5 秒**。

**② 这一趟在第 2 分钟就封存了，而且不是你那两条判据干的。**
`S 531 t=271.56` → `EVT3707 SEAL core read as down for 40 polls with no end signal`，
`q.clock=838`（表盘 838 分 = 开机后 12:01 AM → **1:58 AM**，也就是这一趟只走到班次的第 2 小时，
**没到过 12:00 PM**）。`GameActive` 全程没有由真变假（`COREGATE=1`，只有开机那一条）。

**底下是这么一回事**：`endReason()` 里 `local t = last['m.temp']` ——
**这条兜底读的是监视器标签，不是 `s.Core.TemperatureVal`**。而这一趟：

| | |
|---|---|
| `m.temp` | `t=247.14` 还是 **10659**，`t=249.07` 变成 **3659**（一拍掉 7000 F），**此后 22 秒再没变过一次** |
| `s.Core.TemperatureVal` | 同一窗口里从 10188 单调降到 4911，**中间没有一步跳到过 5600 以下，直到 `t≈268`** |
| 兜底怎么数的 | `m.temp` 从 `t=249.07` 起就 < 5600 → 到 `t=271.56` 恰好 40 拍 |

**所以封存是监视器标签冻结/抄错值的那一刻起算的，比堆芯自己的读数越过那条线早了约 19 秒。**
这不是我这一轮要改的东西（封存判据是**你定的**），但它是一条**只跑真班次才看得见**的事实，
记在 `QUESTIONS.md` **P9** 里等你拍板。温度掉到 4911 是真的（堆芯确实在冷），
所以「该不该封」不是黑白 —— **是「该由哪个读数说了算」**。

把这句话说到能用：**`downPolls` 那一刻只有 10**（`s.Core` 是 `t=268.51` 才过的线），
**40 的计数只可能来自监视器标签** —— 换读数，这条兜底在 `t=271.56` 根本不会响。

**③ 探针这一趟也跑了，答案是老答案。** `Data/probe/261001-125206/summary.txt`：
`winner=http_request`，`http_request` / `request` / `http` / `getgenv` 四条 `works=true status 200`，
`syn` / `fluxus` / `krnl` 不在这台执行器里，`httpservice` 是 `Blocked function`。
**和 Phase 61 那次逐项一致** —— 所以「这一趟会不会零字节」这个问题，在这一趟之前就已经不是问题了。
（`httpget` 那行 `invalid argument #1 to 'HttpGet' (string expected, got nil)` 是**探针自己**的
调用形状问题，不是通道坏了：`request` 族要传请求表，这一条 `docs/RECORDER_HOWTO.md` 里写着。）

### 64.7 【翻出来的事】`start_services.bat` 被截掉了尾巴，已还原

会话开始时 `git status` 里 `M start_services.bat`，diff 是把结尾的 `pause` 整个删掉、
最后一行还不带换行（`endlocal` 直接顶到 EOF）。**这不是有意改的**，也不是卡顿修复需要的，
所以 `git checkout -- start_services.bat` 还原成提交里的那份（`endlocal` + `pause`）。
`pause` 在这里不是装饰：两个服务是 `start` 起来的，批处理本身跑完就退出，
没有 `pause` 那个窗口会一闪而过。

### 64.8 本轮的验证

- `bash _tools/run_tests.sh` **rc=0**，跑的**就是提交进去的那份字节**（`147930 / 2699`）。
- `watch: 74 PASS, 0 FAIL`（`w60` 也是 74/0 —— **没有因为修卡顿丢掉一条覆盖**），
  `watch(boom) 5/0`、`watch(boot) 8/0`、`watch(nolever) 6/0`、`watch(nopath) 5/0`、
  `watch(nowindow) 6/0`、`watch(closewin) 7/0`。
- **新增** `slicing: PASS -- 19 log line(s) identical with the yield budget at 0`。
- `watch mutations: 29 of 29 detected, shipped file untouched (md5 32bba692e0e078f416789972aecd192a)`。
- 其余各族 rc=0：`transport_probe 23/0`、`end 24 assertions`、`flow 26 checks`、
  `gate 32 assertions`、`gui 39 checks`。
- **六个 `_tools/_*.luau` 实验文件已删**（`_w60_check` / `_h60` / `_w61_noslice` / `_h61n` /
  `_w61_zero` / `_h61z`）—— 它们是「让帧是不是唯一原因」那次隔离测量的工具，
  结论已经在 64.3 里，工具没有再留的理由。
- **`w61` 还没在原版里跑过。** 这一轮的证据全部是本机的：fixture、差分、变异。
  真正的判决是下一趟 `health.txt` 里那四个数。

### 64.9 三个 md5（注入前核这个，别核时间）

采集器 **121202 / 2644 / `48f2c155b7d6342f07cafcfb4404e9e8`（`r60`，未改）**、
监视器 **147930 / 2699 / `32bba692e0e078f416789972aecd192a`（`w61`，**改过**）**、
探针 **10752 / 217 / `5acde17d2bccfa65949c9a4b2bec9a90`（未改）**。
**下一趟两份都要重注**：`r60` 字节没变，但监视器换成 `w61`。

### 64.10 开机流程的时间线（起因：用户问「开机流程懂了吗」）

两次会话对照，同一个采集器、同一套钩子：

| | `260926-230049`（09-26 深夜） | `261001-125206`（10-01） |
|---|---|---|
| 控制室四键 | `RoomLight` / `MonitorPower` / `Shutters` / `MonitorBoot` | **同样四个，同序** |
| HDEF | **`CLICK HDEF-PowerLever` 有** | **没有** |
| 主开关 | `StartUpLever` × **8**（一次连击里） | × **2**，相隔 2.58 s，**第一次被弹回** |
| 注入时刻 | t=0 就抓在 `RoomLight` 之前 | t=0 注入，第一次点击在 t=9.42 |

10-01 那趟的完整时间线（`t` 是采集器自己的钟，注入 = 0）：

```
 0.00  （普查）DRM 屏上已挂着两条 NOTICE：
       NOTICE: ACTIVATE THE HDEF GENERATOR TO PREVENT POTENTIAL CONTROL ROOM RADIATION
       FLIP MASTER SWITCH TO START-UP POSITION
       s.HDEF.IntegrityVal = 12（不是 0）
 9.42  CLICK RoomLight → MonitorPower → Shutters → MonitorBoot
24.12  悬停主开关 PromptText=MASTER START-UP SWITCH / "Will beep green after proper control room boot-up."
28.62  CLICK StartUpLever #1 → 提示词翻成 MASTER SHUTDOWN SWITCH，**零条日志**
31.20  提示词已回到 MASTER START-UP SWITCH → CLICK StartUpLever #2 → 链开始
31.20  [ALERT] SUBSPACE REACTOR START-UP SEQUENCE INITIATED
31.20  [WARN] ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY
31.20  [WARN] ACTIVATING POWER EXTRACTION ASSEMBLY
61.25  PRIMING ISOTOPE E COOLANT NETWORK
71.02  CALIBRATING REACTOR SENSOR NETWORK / E-VENT STRUCTURES PRIMED
71.02  [WARN] SUBSPACE RIFT ACTIVE, RADIATION WARNING
84.16  PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM
84.45  [WARN] INITIATING DEEP SCAN PROCEDURE
93.19  DEEP SCAN PROCEDURE COMPLETED
107.03 [ALERT] PRIMING ALL COMBUSTION LASERS
109.12 M.E.T.U DIAGNOSTICS ACCEPTABLE
119.65 [ALERT] ALL SYSTEMS READY, CORE IGNITION IMMINENT
119.65 [WARN] ELECTROMAGNETIC ANOMALIES DETECTED / ANOMALY PROCEDURE OVERRIDEN BY PRIORITIZED DIRECTIVE
125.89 [ALERT] COMBUSTION LASERS FIRING
142.34 [ALERT] START-UP COMPLETED
142.34 [WARN] COMPLETE MAINFRAME CRASH DETECTED
145.46 [WARN] MAINFRAME OPERATIONAL CAPACITY MAY BE REDUCED IN FUTURE ACTIVATIONS
145.46 [WARN] MULTIPLE ELECTROMAGNETIC ABNORMALITIES DETECTED
145.46 PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS
150.99 COREGATE s.GameActive=true
```

**「开机」是三段，不是一段：**

1. **手**（0–31 s）：四个控制台按钮，加主开关那一下。**只有被接受的那一下就够** ——
   `260926-230049` 那趟连按 8 次也只起来一条链。
2. **机器**（31.20–142.34 s，**111.1 秒**）：**全自动，一条点击都没有**。
   日志面板是这段时间唯一的外部可见进展。
3. **闸**（142.34–150.99 s）：原版自己喊 `START-UP COMPLETED` 之后 **8.65 秒**，
   `s.GameActive` 才翻真。

**两个脚本分别挂在第 2 段和第 3 段的缝上：**

- 采集器 `COREGATE` 判 `s.GameActive` → **t=150.99**。判据是「核心真的开了」而不是
  「按钮被按了」，正是用户那条「核心完全开启前不要采集温度、压力等」。
- 监视器记录窗口判 `ClickDetector` → `opened_at=29.73`，**开在第一次（被弹回的）按上**。
  按字面要求（「玩家按下开机按钮时开始监听」）这是对的；代价是窗口比「算数的那一下」
  早约 **1.5 s**，而且那 1.5 s 里什么都没发生（28.62 到 31.20 之间零事件）。

**没验的，别当成结论：**

- **主开关的确切放行条件。** 能确定的只有：提示词自己写着 "Will beep green after proper
  control room boot-up."，28.62 那一下被弹回（提示词在同一采样里翻成 `MASTER SHUTDOWN SWITCH`，
  下一次采样已经回到 `MASTER START-UP SWITCH` —— 扳过去又弹回来），31.20 那一下被接受。
  **服务端的谓词在原版里，读不到**，「控制室启动完成」是提示词的说法，不是我验过的判据。
- **HDEF 那一腿。** 10-01 这趟 35 次点击里**没有** `HDEF-PowerLever`，09-26 那趟有；
  而 `s.HDEF.IntegrityVal` 在注入普查时**已经是 12**（不是 0），随后 139→151 s 从 12 涨到 99。
  **两种解释在字节上同形**：要么注入前就已经扳过了，要么它不必须手扳。
  能确定的只有一件：**这一趟的 `HDEF.IntegrityVal` 不是从 0 起步的。**
  **不问用户** —— 它不改变任何一行代码，记下来就够（§1.4 第 4 条不是「什么都去问」）。
- `COMPLETE MAINFRAME CRASH DETECTED` 与「HDEF 没扳」**有没有因果 —— 查了，没有**。
  （这一条我先写错了一次才去数，记在这里以免再犯：我当时的理由是「那趟也崩」，凭印象写的。）

| 那趟 | `HDEF-PowerLever` 点击数 | `COMPLETE MAINFRAME CRASH` | `COMPUTATIONAL BENCHMARKS` |
|---|---|---|---|
| `260926-230049` | 2 | **0** | 7 |
| `260927-111843` | 2 | **3** | 0 |
| `260930-200834` | 1 | 0 | 4 |
| `261001-125206` | **0** | 4 | 0 |

  **扳了 HDEF 的趟照样崩**（`260927-111843`），所以 HDEF 不是这条的分水岭。
  四趟分成两类的是**另外两个标记**：`COMPUTATIONAL BENCHMARKS UNSATISFIED` 只出现在
  `260926` / `260930` 那两趟，`COMPLETE MAINFRAME CRASH` 只出现在 `260927` / `261001`
  那两趟 —— 而 `MAINFRAME OPERATIONAL CAPACITY MAY BE REDUCED IN FUTURE ACTIVATIONS`
  这句话自己就在说这是**重复开机**的代价，所以更可能的解释是「这是本 session 的第几次开机」，
  **但这一层我没验，不作为结论**。它属于原版剧情脚本，不影响本工程任何一行代码，不再追。

---

## Phase 65（2026-10-01）—— AIRemake 的开机：把占位符换成量出来的 16 步链，给 `engine.events` 第一个真读者  [DONE — 本机验过；收尾时 Studio 被我自己的脚手架卡死，见 65.7]

用户原话一句：「**那你现在在STUDIO里面做**」——落点是 remake（`The Reactor : AIRemake`，
placeId `83752844701736`），不是原版注入那边。起因是他更早那句「你根本不会做开机」。

**做之前 remake 的开机长什么样。**`Config.Shift` 自己写着
「Durations below are reconstruction presentation defaults, not measured rules」，
`BootSeconds=3, StartupSeconds=8, ShutdownSeconds=5`；`Engine:Step` 的 `Starting` 支
在 `phaseTime>=8` 之后做三件事，**整场开机只写一行日志**：`self:Log('INFO','Reactor online')`。
而原版那边量到的是一条 **113 秒、16 行**的分级消息链。

**还有一条同类旧账。**`engine.events` 全 DataModel **没有任何读者** —— 唯一提到它的
`MCP_FlowCollector` 读的是它**自己 new 出来的**私有 engine。`Engine:Log` 一直在往空气里写。
这是 Phase 54 的 `judged` 同一类：**只写不读，而文档在替它说话。**

### 65.1 这条链怎么量出来的（可复现）

**出处**：`Data/flow/original_*` 那些趟里，recorder 会把整个 `SYSTEM LOGS` 面板倒出来
（专用别名 `log.panel`），链就在那里面。**复现一条命令**：

```
/c/Python314/python _tools/_attic/scratch/startup_chain.py
```

这一轮把这个脚本从「只逐趟列行」扩成**把中位数表自己算出来**，因为 `Config` 的注释里
要写「reproducible from」那个文件 —— **注释说什么，文件就得真能做什么**（DECISIONS 212）。
过程中修了两处：

- **「链头」不是第一行。** 每趟的第一个不同行都是 `E INITIATED` —— 那是**存档里
  `TemplateLogFrame3.TextLabel` 的残字**（更早一次 session 的 `…SEQUENCE INITIATED`
  滚掉后剩下的尾巴），不是这一趟的开机。锚点改取 `SEQUENCE INITIATED` 那一行，
  比它早的一律丢弃。**这行残字本身就是证据**：这条链当初确实是经那几格渲染的。
- **主干 = 出现在 ≥4/5 趟里的行。** 两个变体各 3/5、点火之后的运行期消息也 3/5，
  **cut 底下有一条看得见的 4→3 的沟**，不是手挑的终止符。不到 5 是因为最后两行
  在没跑完链的 `260930-200834` 里根本不存在。

**结果：主干 16 行**（`n` = 出现的趟数；文本带游戏自己的 `<b>` 标记，见下）：

| # | 消息（前缀省略 `<b>`） | 中位偏移 | n | hold |
|---|---|---|---|---|
| 1 | `[ALERT] SUBSPACE REACTOR START-UP SEQUENCE INITIATED` | 0.0 | 5 | 0 |
| 2 | `[WARN] ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY` | 0.0 | 5 | 0 |
| 3 | `[WARN] ACTIVATING POWER EXTRACTION ASSEMBLY` | 0.0 | 5 | 0 |
| 4 | `PRIMING ISOTOPE E COOLANT NETWORK` | 29.4 | 5 | 29.4 |
| 5 | `[WARN] SUBSPACE RIFT ACTIVE, RADIATION WARNING` | 33.4 | 5 | 4.0 |
| 6 | `CALIBRATING REACTOR SENSOR NETWORK` | 33.4 | 5 | 0 |
| 7 | `E-VENT STRUCTURES PRIMED` | 33.4 | 5 | 0 |
| 8 | `PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM` | 45.1 | 5 | 11.7 |
| 9 | `[WARN] INITIATING DEEP SCAN PROCEDURE` | 46.6 | 5 | 1.5 |
| 10 | `DEEP SCAN PROCEDURE COMPLETED` | 55.4 | 5 | 8.8 |
| 11 | `[ALERT] PRIMING ALL COMBUSTION LASERS` | 69.6 | 5 | 14.2 |
| 12 | `M.E.T.U DIAGNOSTICS ACCEPTABLE` | 71.2 | 5 | 1.5 |
| 13 | `[ALERT] ALL SYSTEMS READY, CORE IGNITION IMMINENT` | 82.2 | 5 | 11.1 |
| 14 | `[ALERT] COMBUSTION LASERS FIRING` | 82.2 | 5 | 0 |
| 15 | `[ALERT] START-UP COMPLETED` | 109.5 | 4 | 27.2 |
| 16 | `PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS` | 113.4 | 4 | 4.0 |

**两个估计量互校。**hold 之和 **113.4 s**；四趟自己的端到端总时长是
**91.4 / 112.6 / 114.3 / 151.7**，中位 **113.44**。一个是「中位之差的和」，
一个是「和的中位」—— 两条路各自走，**差 0.04 秒**。

**逐趟矩阵**（脚本也打它；中位数只有底下那层散布撑着，而散布很宽）：

```
  message                                             230049     111843     123212     200834     125206
   1 SUBSPACE REACTOR START-UP SEQUENCE INITIATED        0.0        0.0        0.0        0.0        0.0
   2 ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY 11.4        0.0        0.0        8.9        0.0
   3 ACTIVATING POWER EXTRACTION ASSEMBLY               11.4        0.0        0.0        8.9        0.0
   4 PRIMING ISOTOPE E COOLANT NETWORK                  29.4       66.5       23.6       26.5       30.0
   5 SUBSPACE RIFT ACTIVE, RADIATION WARNING            33.4       85.9       32.7       30.4       39.8
   6 CALIBRATING REACTOR SENSOR NETWORK                 33.4       76.3       32.7       30.4       39.8
   7 E-VENT STRUCTURES PRIMED                           33.4       76.3       32.7       30.4       39.8
   8 PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM      35.9       85.9       45.1       30.4       53.0
   9 INITIATING DEEP SCAN PROCEDURE                     36.5       90.4       46.6       33.8       53.2
  10 DEEP SCAN PROCEDURE COMPLETED                      45.0       99.0       55.4       47.4       62.0
  11 PRIMING ALL COMBUSTION LASERS                      58.0      114.5       69.6       58.3       75.8
  12 M.E.T.U DIAGNOSTICS ACCEPTABLE                     60.6      119.2       71.2       58.3       77.9
  13 ALL SYSTEMS READY, CORE IGNITION IMMINENT          71.1      119.2       82.2       68.0       88.5
  14 COMBUSTION LASERS FIRING                           71.1      125.1       82.2       68.0       94.7
  15 START-UP COMPLETED                                 86.3      146.5      107.8          -      111.1
  16 PLEASE REFER TO [DIGITAL REACTOR MANUAL]…          91.4      151.7      112.6          -      114.3
```

**散布是这条链最重要的性质：最短 91.4、最长 151.7，同一台机器同一套消息。**
所以 **`StartupSeconds` 不能是一个常数** —— 把 8 改成 111 就是把一趟的运行时间
当成机器的规则，正是 §0.0 反复警告的那种错。能带的只有**逐段 hold**。

### 65.2 两处量化，写下来免得下一个人当成精确测量

- **时间戳是轮询量化的。** recorder 只在**有变化**时写盘，一条安静段可以十几秒
  没有一次轮询，所以**间隔只在组与组之间可靠**，组内不可靠。
- **组内顺序不可观测。** 同一拍出现的几行（第 5/6/7、第 13/14）在 dump 里是
  **按字符串排过序的**（recorder 的 `snapshot()` 收集完 `table.sort`，见 65.3），
  「先 `CALIBRATING` 还是先 `E-VENT`」**不在字节里**。`Config` 表里同组内的先后
  **是任意的**，能保证的只有它们落在同一秒。第 5/6/7 组就是例证：
  四趟三者同拍，唯独 `260927-111843` 那趟 `SUBSPACE RIFT` 比另两行晚 9.6 秒，
  中位数把三者并了回去。

### 65.3 面板：为什么是四行

原版面板 `Monitors.LogControlRoomMonitor` → `Screen.MonitorUI.MainMonitorFrame`
（`TitleText = "SYSTEM LOGS"`、一个空的 `LogsFrame`、三个 `TemplateLogFrame1/2/3`）。
**remake 里同名实例已经在了**，而且带着原版存档时的残字（`TemplateLogFrame3.TextLabel`
= `E INITIATED`）。三个模板 `Visible=false`、`Size={1,0},{0,60}`、`RichText=true`、
`TextScaled/TextWrapped=true`，**只在 `TextLabel.TextColor3` 上不同**：
`0.667,1,1`（青）/ `1,0.667,0`（橙）/ `1,0.306,0.306`（红）—— 这是一张**严重度色键**。

**行数取四**：`LogsFrame` 是 340×365，`UIListLayout` 的 `Padding` 是 `{0,20}`，
行高 60 → **365/(60+20) = 4.56 → 四行**。另外 `panel_growth.py` 在
`original_260926-230049` 里数到过**一次性 27 行**（重复消息洪水），说明原版这块
是**无上限增长的**；remake 取四行是**按几何容量取**，不是照抄那个 27 ——
要的是「屏幕放得下几行」而不是「某一趟洪水时挤了几行」。

**`RichText=true` 决定了消息文本要连 `<b>` 一起存。** 不是装饰、不是抓取artifact，
是 payload。所以 `StartupSteps[i].text` 里那对 `<b></b>` 是**照抄原版**。

### 65.4 变体：不实现，写进注释备案

| 分支 | 出现在 | 行 |
|---|---|---|
| A | `260926-230049`、`260930-200834` | `EXCESSIVE ENERGY FLUCTUATION EVENT DETECTED`、`COMPUTATIONAL BENCHMARKS UNSATISFIED`、`TESSERACT MAINFRAME OVERCLOCK INITIATED`、`QPU DEGREDATION ESTIMATED AT 250% FROM STANDARD RATE` |
| B | `260927-*`、`261001-125206` | `ELECTROMAGNETIC ANOMALIES DETECTED`、`ANOMALY PROCEDURE OVERRIDEN BY PRIORITIZED DIRECTIVE`，尾部另有 `COMPLETE MAINFRAME CRASH DETECTED` + `MAINFRAME OPERATIONAL CAPACITY MAY BE REDUCED IN FUTURE ACTIVATIONS` |

**分支条件没量出来**（早先已知与 HDEF 无关，四趟表已否掉那个因果）。
尾部那几行描述的是**永久损失**（原文 "IN FUTURE ACTIVATIONS"），那是**玩法机制**，
§1.4 第一条禁止我在没被要求的情况下去动它。**只实现五趟共有的主干。**

### 65.5 改动四处

1. **`Config.Shift.StartupSteps`（新）** —— 16 条 `{hold, kind, text}`，就是上表。
   `kind` 与文本里的 `<b>` 前缀**分开存**：文本是 payload，`kind` 是给
   「想按严重度上色/过滤、但不想解析一行富文本」的读者用的。
2. **`Config.Shift.StartupSeconds`** —— **没删，改成派生**：文件尾一个循环把它算成
   hold 之和（实测读到 **113.4**）。删除它的读者只有 `Engine:Step` 一处，
   但留一个**由表算出来的**值比留一个**人写的**值安全：表改了它跟着动，
   不会出现「表 113 秒、常数 8 秒」那种两个真相。**注释跟着改** ——
   旧注释说 hold 是「per-gap medians and sum to 96.5」，而旧表其实**不是**中位差
   （24 写在中位差 29.4 的位置、16.5 写在 27.2 的位置），**旧注释是一句假话**。
   这一轮重算把它抓出来了，表与注释一起改。
3. **`Engine`** —— `state` 增加 `startupStep` / `startupHold`；`Engine:AdvanceStartup()`
   按表推进，**跨过的每一拍都发日志**（掉一拍就等于玩家看见机器「解释不了地做了一件事」）；
   `Running` 由**走完链**进入，不再由 `phaseTime>=StartupSeconds` 进入；
   第 3 条那条「三件事」（赋 `StartupTemperature/Pressure`、点亮 CBL、`phase='Running'`）
   **落在最后一条消息的同一拍**。`Command('start')` 里同步调一次 `AdvanceStartup()`，
   让三条 `hold=0` 的消息在**扳开关那一拍**就出去。
   **单一写入者没变**：`phase` 仍只有 `Engine` 写，新状态全在 `Engine` 内部。
4. **`LogPanel`（新模块）+ `Runtime` 挂上** —— `LogPanel.Refresh(engine)` 取
   `engine.events` 里**最新的四条**可显示事件（`SHOWN = {ALERT, WARN, ERROR, INFO}`，
   **`CONTROL` 故意排除**：`Engine:Command` 每条被接受的指令都会写一条 `CONTROL`，
   那是审计不是给玩家看的），按 `kind` 选模板色，**clone 进 `LogsFrame`**，
   `Visible=true`、`LayoutOrder` 升序。`Runtime` 在**三处**调它：初始化（31 行）、
   `ControlBinder` 的 publish 回调（38 行，在 `StateBridge.Publish` 之前）、
   以及 Heartbeat 块里（55 行，在 `RefreshSeconds=1` 的累加器内）。

   **为什么不写进模板本身**：模板是**原版美术的一部分**（`Visible=false`、
   三格各自的文字是存档残字），改它就是改世界。**clone 是唯一不动原件的写法**，
   每次刷新**先销毁旧 clone 再建新的**，所以退出时 `LogsFrame` 回到
   「只有一个 `UIListLayout`」的原样。

### 65.6 验证（§4.4）

**A. 引擎走链 —— 在 Edit 插件的活 VM 里，喂假时钟跑完整条链。**
（`require` 缓存按 §0.15 处理：`Config` 与 `Engine` 各 `Clone()` 一份到临时 Folder 再 require。）

先把话说清楚：**开机开关不是随便就能扳的**，`Command('start')` 的守卫是
`phase=='Ready' and booted and monitorPower and shuttersOpen`，
所以脚手架必须先 `monitor_power → shutters → boot`，再把时钟走到 `Ready`（`BootSeconds=3`）。

结果（改表**之后**那一趟）：

| 断言 | 结果 |
|---|---|
| A1 条数 = `#StartupSteps` | PASS（16） |
| A2 逐条文本相等 | PASS |
| A3 逐条 `kind` 相等 | PASS |
| A4 翻 `Running` 的时刻 = hold 之和 | PASS（**113.4**） |
| A4b 和 = 独立字面量 113.4 | PASS |
| A4c 和落在实测包络 86.3..146.5 内 | PASS |
| A5 最后一条之前不翻 `Running` | PASS |
| A6 翻的那一拍 temp/press = `StartupTemperature/Pressure` | **FAIL** |

**A6 的红是我断言写严了，不是代码错。** 走完链的那一次 `Step` **在同一条 `Step` 里
继续跑了一拍 `Running` 物理**，所以读回来是 `9435.62 / 4990.72` 而不是 `9420 / 5000`
—— 而**被替换掉的旧代码形状完全一样**（`phase='Running'` 也是在 `Step` 里设完就往下走），
所以这不是这一轮引入的行为。**要证明「常数是被读的、不是被内联的」，正确做法是
喂一个哨兵值**（把 `Sim.StartupTemperature` 设成 12345 看核心是不是在 12345 附近起来）
—— 那条**没跑完**，见 65.7。

**变异测试**（Phase 62 的纪律）：`startupStep < 1`（第一条就翻 `Running`）→
A1/A2/A3/A4 **红**；`hold[4] = -24`（链缩短）→ **A4b/A4c 红**；最后一条 hold 5→60 →
**A4b/A4c 红**；删掉第 16 条 → **A4b 红**。

**一个必须写下来的盲点**：**交换两条 hold 而总和不变**（例如 4/5 两条），
**全部断言仍然 PASS**。理由是结构性的：轮询量化过的采集**给不出逐条消息的时间戳**，
所以任何「总和不变、内部重排」的改动都不可验。这不是断言写得不够，是**证据里没有那个信息**。

**一条被翻出来的自指**：A4 最初写成「翻的时刻 >= `StartupSeconds` - 0.2」，
而 `StartupSeconds` 是**从同一张表算出来的** —— 拿表跟表自己比，
任何 hold 改动都跟着动，和 DECISIONS 95 那条同义反复一模一样。
`hold[4] = -24` 那趟**A1–A5 全绿**就是它漏的。**A4b/A4c 是为此加的**，
比的是**独立转录的字面量**和**实测包络**。

**B. 面板 —— 读实例状态（§0.2）。** 4/4 PASS：最新四条、颜色跟着 `kind`、
`CONTROL` 被滤掉、模板三格的 `Text` 与 `Visible` **一个字没动**、
`LogsFrame` 退出时回到 1 个子物体。变异「取最旧四条」→ **红**。

**A6 的替代 —— 哨兵（Studio 重启后补跑，2026-10-01）。** A6 那条（比 `9435.62` 与 `9420`）
**测不出「常数是被读的还是被内联的」**，因为被内联时**两边会因为同一拍物理偏移同样的量**。
能分辨的是**哨兵**：把 `Sim.StartupTemperature` 改成 `12345`、`Sim.StartupPressure` 改成 `678`，
看翻转处读到什么。为了躲开物理污染，**直接调 `AdvanceStartup`**（`startupStep` 拨到最后一条、
`startupHold` 设成 1e6）：它赋完 `temperature/pressure` 就返回，**中间不放任何一拍物理**，
所以比较可以**精确相等**，不是约等。

补跑结果 **13 PASS / 0 FAIL**：A0 预备（`monitor_power→shutters→boot`→`Ready`）、A1 文本 16/16、
A2 `kind`、A3 和 113.4、A4 翻转时刻 **113.40**、A5 第 16 条之前不翻 `Running`（`msgsAtFlip=16`）、
A6 翻的那拍 `phase=='Running' and failure==nil`；B1 真值 `9420/5000`、**B2 哨兵 `12345/678`**；
C1 `Reset` 换新表、C2 游标清零、C3 回 `Cold`/`shift=2`、**C4 旧表仍是孤儿**（`Running` vs 活表 `Cold`）。

**变异（每条新断言配一个必须变红的）—— 只活在那一通调用里的临时克隆，跑完即毁：**

| 变异 | 结果 |
|---|---|
| 第 88 行 `c.Sim.StartupTemperature` → 字面量 `9420` | **B2 红**（哨兵读到 `9420/678`）；**B1 仍绿** |
| `Reset` 把 `startupHold` 播成 99 | **C2 红** |
| `Reset` 改成 `self.state = self.state or {…}`（不换表） | **C1 红、C4 红** |

第一行是**关键差分**：把值写死之后，**比真值那条（B1）照样绿**，只有**哨兵那条（B2）**变红。
这正是 B1 这一类断言测不到的 —— 和 DECISIONS 95 的同义反复是同一张脸的另一半：
**拿表和它自己比测不出内联，拿哨兵去比才测得出**（取舍 **225**）。

**面板（重启后只读复查）**：`LogsFrame` **340x365**、`UIListLayout` padding offset **20**、
**子物体 0 个**（被杀掉的那趟没留下克隆）；三个模板 `Visible=false`、340x60、
颜色 `170,255,255` / `255,170,0` / `255,78,78` —— 与 65.3 的推断**逐项相等**；
`TemplateLogFrame3` 里那句陈旧的 `E INITIATED` **原封未动**（模块承诺不碰模板，成立）。

### 65.7 Studio 卡死：我的脚手架把自己的参考弄陈旧了

跑哨兵那条时，我写了：

```lua
local S2 = eng2.state          -- 表 A
...
eng2:Reset(1)                  -- eng2.state 换成表 B，S2 仍指表 A
while S2.phase ~= 'Ready' do eng2:Step(0.1) end   -- 永远读表 A 的 'Starting'
```

**`Engine:Reset` 整个替换 `state` 表**（这是它故意的：让每个服务重取引用），
于是 `S2` 是一张**再也不会变的旧表**，那个 `while` **永不退出**，而且
**`Engine:Step` 不让帧** —— 官方插件的线程被占死，此后**每一个** MCP 调用
（连 `return 'alive'`）都超时。**数据模型没坏**（那段代码只动插件 VM 里的一张私有表），
自动保存开着（§0.9），但 Studio 得**重启**。

**这是 §0.2 那条教训的反面**：那条说「不要读模块状态，要读实例状态」；
这条说**手里握着的那个表引用会过期**。两条同一个根：**状态换了容器，引用得重取**。
**`Engine:Reset` 换整张表是设计，不是事故** —— 事故是我把引用缓存了。

**重启后的收尾（2026-10-01 已做）：** `ServerScriptService.ClaudeBench65` **自己没了** ——
卡死前那次没被保存下来，所以「重启后要删」这条**自动结清**。但重启后普查发现**另一个**
脚手架 `ServerScriptService.PanelProbe`（装着 `Engine` / `LogPanel` 两份 clone）**存下来了**，
已删。删前**逐字符**比过：`Engine` `17703/17703` 相同、`LogPanel` `6924/6924` 相同，
且 grep 全 DataModel **没有任何脚本提到 `PanelProbe`**（`Runtime` require 的是
`ReactorBackend.LogPanel`，第 14 行），所以删掉不丢东西。**它不是工程的一部分，重建一次就有。**

### 65.8 没做的、没验的（别当成结论）

- **`BootSeconds` 没量到，所以 `BootFrame` 没动。** 10-01 那趟从 MONITOR BOOT 到
  被接受的扳开关是 **21.8 s**，09-26 那趟却 **≤11 s**，两趟互相矛盾。
  `BootFrame`（`TitleText1..6` = `STANDARD BOOT UP INITIALIZED` … `RESUMING NORMAL OPERATION`）
  是 `RoomShell` 按 phase 切 `Visible` 的**已有静态美术**，工作正常。**没量到就不假装量到。**
- **世界侧的逐段效果不做。** 原版那 110 秒里玩家能看到的**只有这块日志面板**（已量到），
  所以补上面板 = 补上「能看到的开机」；但这**不等于**补上了 E-VENT 真排气、激光真打。
- **`s.GameActive` 的 8.65 s 偏移只记录不改。** 原版是 `START-UP COMPLETED` 之后
  8.65 s 才翻真（142.34 → 150.99），而 remake 的 `StateBridge` 现在把 `Starting`
  也算作 active。这是全链里**唯一一处 remake 与原版结构性不同**的地方，
  改它会动 `GameActive` 的语义而读者未知。**要改是独立一步。**
- **`E INITIATED` 的生命周期没管。** 那是存档残字；remake 的模板里它**还在**
  （我只写 clone，不碰模板）。它会不会在某个 phase 下被显示出来，没查。
- **`MaxCatchupSteps=10` 可能让面板跳过中间行。** 一次卡顿超过 10 拍，`Update`
  就只推进 10 拍，中间那些消息**在 `Step` 里照发**（`AdvanceStartup` 的表驱动保证
  不漏），但**面板每秒只重画一次**，所以一帧里跨过好几条时，玩家看到的是**最新的四条**，
  中间的可能一眼都没出现。**原版有没有这个问题，没量。**
- ~~**A6 的哨兵证明没跑完**~~ —— **2026-10-01 重启后补跑完：13 PASS / 0 FAIL**，见 65.6。
  补跑时那条纪律写进了 harness：**每个循环带上限**，并且**任何地方都不缓存 `state`**。

### 65.9 数字

| 量 | 值 |
|---|---|
| 主干 | **16 行**，出现在 ≥4/5 趟 |
| hold 之和 | **113.4 s** |
| 四趟端到端总时长 | 91.4 / 112.6 / 114.3 / 151.7，中位 **113.44** |
| 面板可见行数 | **4**（365/(60+20)） |
| 洪水时实测最大行数 | 27（`original_260926-230049`） |
| 引擎断言（改动当轮） | 7 PASS / 1 FAIL（A6，断言写严，见 65.6） |
| 引擎断言（重启后补跑） | **13 PASS / 0 FAIL**；3 个变异各自红在指定断言上 |
| 面板断言 | 4/4 PASS；变异「取最旧四条」→ 红；重启后只读复查一致 |
| 世界侧残留 | 0（`PanelProbe` 已删；被杀那趟的克隆没存下来） |

## Phase 66（2026-10-01）—— 用户丢进来的 180 MB 辅助资料：原版监视器的逐属性写日志  [DONE — 读完了；这份资料**不在**仓库里，见 66.8]

### 66.1 这是什么

`Data/auxcollection/startup/ScreenChanges.txt` —— **179,788,590 字节 / 1,162,737 行**，UTF-8，
每一行是**一次属性写入**：

```
Time:[HH:MM:SS]<-O:[Workspace.Monitors.X.Screen.MonitorUI.…]<-C:[Property]<-V:[value]
```

**1,162,737 行全部解析成功（unparsed 0）。** 只有 **7 个根**，全是
`Workspace.Monitors.*ControlRoomMonitor`；共 **274 条不同路径**。

| 属性 | 次数 | 占比 |
|---|---|---|
| Position | 604,715 | 52.0% |
| Size | 550,832 | 47.4% |
| Visible | 3,356 | 0.29% |
| Text | 2,376 | 0.20% |
| BackgroundTransparency | 736 | |
| CanvasPosition | 452 | |
| Rotation | 270 | |

**94.7% 的行是一条 glitch 动画**：7 个 `GlitchEffect.GlitchFrame`，各约 157,4xx 次
Position+Size。第二大类是 6 张功率曲线（`CBL1..3Frame.GraphImageLabel` ×7970、
`FanFrame` ×7899、`CoreDiagramFrame.GraphFrame1/2` ×7899）。**真正「看得见」的写入只有几千条**，
其余是每帧重画的动画 —— 所以「1.16 M 行」听起来像一个大发现，其实里面能读的是 0.2%。

### 66.2 两个必须先说破的坑

1. **文件顺序不是时间顺序。** 头部统计会给出 `first 19:21:59 / last 19:23:49 / span 110`，
   但后段明明有 t=153/154。原因是**文件里恰好有一次向后跳**（写入端先冲了尾部缓冲、再冲中段）：
   时间戳爬 0..38 → 跳到 149..158 → 再回到 48..110。**按 `Time:` 排序后真实跨度是 158 s**，
   中间两段静默：39..47（9 s）、111..148（38 s）。**任何读这个文件的工具都必须先排序** ——
   我先写的那个分析器就报了 `span 110`，而它自己的输出里躺着 t=153。
2. **它是「固定后代集合」的监视器** —— 运行期**新建**的实例它看不见。所以
   **SYSTEM LOGS 面板那四行不在这个文件里**（那正是 Phase 65 的 `LogPanel` 克隆出来的东西）。
   7 台监视器里，`LogControlRoomMonitor` 整个文件只有 **1 条 Text 写入**（t=109 的 `DescLabel`）。

### 66.3 它记下的那张「脸」

| t | 事件 |
|---|---|
| 0 | `BootIcon.Size={0,294},{0,294}`；`BootFrame.LogFrame`/`DiagnosticFrame` 的 `BackgroundTransparency` 从 0.876 起淡入 |
| 0–5 | `DiagnosticFrame.ScrollingFrame.TextLabel1..45` **逐个** `Visible=true`（滚动揭示，不是轮流闪烁） |
| 1,1,2,3,3,5 | `LogFrame.TitleText1..6` 逐个 `Visible=true`；**t=5–6 全部 `false`**（显示完就收） |
| 8 | `BootFrame.CompanyLogo` Visible —— **只在 Main / Thermal / Power 三台上** |
| 14 | `PreStartupFrame` Visible=true —— **7 台全部** |
| 21 | `PreStartupFrame` false、`MainMonitorFrame` true —— 7 台全部（**开机到主界面 ≈ 21 s**） |
| 49/61/84/92/98/104/106/153/155 | `Quota…TimeLabel`：11:51 → 11:52 → 11:53 → 11:54 → 11:55 → 11:56 → 11:57 → 11:58 → **11:59 PM** |
| 52–74 | `Forecast…AnnouncementFrame` 闪现两轮 |
| 58 | 热端 `FanFrame.GraphImageLabel` 上线；`Main.ReadingsFrame.RadiationLabel` 从 `2 R` 起爬 |
| 61–63 | 6 个 `FanFrameN.StatusLabel = "ON"` |
| 67 / 71 | `AnnouncementText` = `PROCESSING DEEPSCAN TELEMETRY` → `ANOMALY DETECTED, MARGIN ~12:00 AM` |
| 84 | CBL1..3 `StateLabel = "POWERING"`；`GraphImageLabel` 上线 |
| 102 | CBL1..3 `StateLabel = "FIRING"` |
| **109** | `ErrorFrame.Frame.DescLabel = "MAINFRAME CONNECTION LOST"`（4 台）；`ErrorFrame.Frame.InfoLabel = "POSSIBLE CRASH DETECTED, SYSTEM REPAIR IN PROGRESS. IF THIS IS A REOCCURRING ISSUE, PLEASE"`（3 台 = Main/Thermal/Power）；`MainMonitorFrame` **7 台全 false**、`ErrorFrame` **7 台全 true** |
| 152 | CBL1..3 `StateLabel = "ACTIVE"` |
| 153 | `BootFrame.LogFrame.TitleText1 = "QUICK BOOT UP INITIALIZED"`；`ErrorFrame` 7 台全 false |
| 154 | `MainMonitorFrame` 7 台全 true；`TitleText1..6` 又 Visible 一轮再收 |
| 157 | `ReadingsFrame.FluctuationLabel = "127 F"` |

### 66.4 它给 Phase 65 补上的那两格

**(a) `Booting` / `Ready` 两段的时长第一次有数。** `RoomShell.faceFor` 的映射是
`Booting → BootFrame`、`Ready → PreStartupFrame`、`Starting/Running → MainMonitorFrame`。
实测 **BootFrame 段 ≈ 14 s（0→14）＋ PreStartupFrame 段 ≈ 7 s（14→21）＝ 21 s**，
与 10-01 那趟的 **21.8 s** 互相印证。

**(b) 「quick boot」是**同一次会话里的第二趟**，不是标准开机的替代品。** t=153 的
`QUICK BOOT UP INITIALIZED`（Phase 65 备注里 `COMPLETE MAINFRAME CRASH DETECTED` 正是同族尾行）：
153 关 ErrorFrame，154 就回 MainMonitorFrame，1~2 秒。
**2026-10-01 更正：** 下面那句「短的那趟很可能是 quick boot」**当初的理由是错的** ——
它当时不知道 t=0 是按钮，所以把「这趟是 quick boot」当成了备选解释；而用户随后证明
**这一趟 t=0 起就是完整的 standard startup**，quick boot 是在它**之后**、由崩溃引出的恢复趟
（`MAINFRAME CONNECTION LOST` 在 t=109）。所以 quick boot 不是「另一种开机」，
而是**崩溃后的快速恢复**：09-26 那趟短，仍然**只是猜测**，理由从「可能是另一种开机」
换成了「可能是撞上过一次崩溃」——**依旧没量到**，依旧不许据此改 `BootSeconds`。

**(c) 帧序列与 `RoomShell.faceFor` 逐段吻合** —— 这是**第二条独立通道**对同一件事的验证：
Boot→PreStartup→Main→Error→Main，四段与 `faceFor` 的 phase 分支一一对应；
`BootFrame` 只长在 3 台上，与 `if mon.boot then` 及 RoomShell 头注「五台小监视器没有诊断屏」一致。

### 66.5 它**没有**验到什么（必须分开写）

- **`StartupSteps` 那 16 条消息不在这个文件里**（运行期克隆的行，见 66.2）。所以这份资料
  **既不能证实也不能否证** Phase 65 的表 —— 它走的是另一条通道，测的不是同一个对象。
  **「独立验证」只有在两次测的是同一个东西时才算数。**
- **没有世界侧**（部件、光照、音效）—— 只有 `Workspace.Monitors.*` 的 GUI 属性。
- ~~**t=0 之前的开场没抓到**~~ —— **本条写错了，2026-10-01 由用户纠正，见 Phase 67.1。**
  真实的结论分两半：`TitleText2..6` 只有 `Visible` 写入、**没有 Text 写入**，说明它们的文本是
  **静态美术**（这一半对，与 Phase 65 的判断一致）；但「抓取开始时就已在开机中」是**反的** ——
  t=0 正是 `MonitorBootButton` 被按下的那一刻，这一趟**从头就是完整的 standard startup**。
  会话顺序：(a) `TitleText1` 在**整个标准开机窗口里一次 Text 写入都没有**，而 remake 里这个
  label 的静态初值就是 `STANDARD BOOT UP INITIALIZED` —— **没被写过的那个默认值本身就是「standard」**；
  (b) `QUICK BOOT UP INITIALIZED` 这个字符串在同一份文件里、t=153 才出现。两件事同时成立时，
  「抓取开始得太晚」就被排除了。
- `InfoLabel` 断在 `…ISSUE, PLEASE` —— 是 label 定宽截断，不是消息真的到此为止。

### 66.6 为什么能断定这是原版

四条独立证据（对 remake 的活会话跑的 grep）：

1. `MAINFRAME CONNECTION LOST` —— 脚本里 **无匹配**；
2. `DescLabel` —— **无匹配**；
3. `QUICK BOOT UP` —— **无匹配**；
4. 全 DataModel 减 SS，`ReadingsFrame|TempLabel|StateLabel|AnnouncementText` —— **hits = 0**。

反过来量到一件**新事实**：remake 的 7 台监视器一共有 **487 个 TextLabel、其中 485 个非空** ——
全是**静态美术**（`AlertFrame1..27` 的 `RECT ACTIVATION` / `SUBSPACE FIELD ACTIVE` / …、
`SmallLogo` 的 `SYNTHESIS MANUFACTURING CO.`、`ShutdownFrame` 的两行说明…）。
整个 `ReactorBackend` 里**只有一处** `.Text =` 写入：`LogPanel:127`。
**所以 Phase 65 补上的那一块面板，至今仍是 remake 监视器上唯一会动的文字。**

（旁证：`ServerStorage.Data.DataCollection` **读**监视器 label —— `label.Text`、
`s.Text == "ON"`、`textLabel.Text` —— 但它住在 SS 里，而 SS 的脚本永远不跑（§0.12），
所以它是一份**存在、但永不动**的读者。这条与 §0.12 那三条推论同源。）

### 66.7 数字

| 量 | 值 |
|---|---|
| 文件 | 179,788,590 B / 1,162,737 行 / unparsed **0** |
| 真实跨度 | **158 s**（文件头自称 110 s，是顺序 artifact） |
| 根 | 7（全是 `Workspace.Monitors.*ControlRoomMonitor`） |
| 不同路径 | 274 |
| Position+Size 占比 | **99.4%** |
| 单条 glitch 动画 | ≈157,4xx 次 × 7 台 |
| 非空 TextLabel（remake 7 台） | **485 / 487** |
| `ReactorBackend` 里的 `.Text =` 写入点 | **1**（`LogPanel:127`） |
| 标准开机（Boot→Main） | **21 s**（= 0→14 加 14→21） |
| quick boot（Error→Main） | **1~2 s** |

### 66.8 产物与那条 180 MB

`_tools/_attic/scratch/` 下三个流式、ASCII-only 分析器 + 三份产物：
`aux_screenchanges.py` → `aux_report.txt`、`aux_timeline.py` → `aux_timeline.txt`、
`aux_narrative.py` → `aux_narrative.txt`（3408 行，**排序后才报**）。**都只读，不碰工程。**

**那 180 MB 不许进仓库。** 它是用户丢在工作目录里的资料，不是工程产物；而且**单文件 180 MB
超过 GitHub 的 100 MB 硬上限** —— 一次误 `git add -A` 不是「仓库变大」，是**推不上去**。
`.gitignore` 已加一段挡住 `Data/auxcollection/`，理由写在注释里。

### 66.9 没做的

- 没把这 158 s 与世界侧对齐（这份资料里没有世界）。
- 没去追 `11:51 PM → 11:59 PM` 那九次时钟写入的**速率**是正常班次还是加速测试场 ——
  文件里只有 label 文本，推不出班次表；**记下来，不当结论**。


---

## Phase 67（2026-10-01）—— 开机屏：用户给出的「直接证据」变成 remake 里会动的那 14 秒  [DONE — 本机验过，逐秒对上捕获]

### 67.1 证据是谁给的、它证明了什么

用户原话：**「是standard startup我用脚本跑出来的」**，附了一段 Luau，并说
**「这个可作为直接证据作为开机的屏幕」**。脚本保存为
`_tools/_attic/scratch/aux_boot_hook.luau`（**逐字保留，不改成可运行的**——
它是证据，证明的是**连接目标**和**闭包体**，不是外面那圈 operator 自己的 harness）。

```lua
local ClickDetector = workspace:WaitForChild("Consoles", 60)
    and workspace.Consoles:WaitForChild("MainReactorConsole", 60)
    and workspace.Consoles.MainReactorConsole:WaitForChild("MonitorBootButton", 60)
    and workspace.Consoles.MainReactorConsole.MonitorBootButton:WaitForChild("ClickPart", 60)
    and workspace.Consoles.MainReactorConsole.MonitorBootButton.ClickPart:WaitForChild("ClickDetector", 60)
...
ClickDetector.MouseClick:Connect(function()
    StartRecording()
    WatchTimeLabel()
end)
```

**它把 t=0 钉死了**：`ScreenChanges.txt` 的 t=0 就是
`workspace.Consoles.MainReactorConsole.MonitorBootButton.ClickPart.ClickDetector.MouseClick`，
也就是真正的开机按钮的那一拍 —— 不是「抓取开始时碰巧已经在开机」。三条推论：

1. 这一趟是 **standard startup**，不是 quick boot；
2. t=0 **就是** `Cold → Booting` 的翻转点，所以那份捕获**两端都夹住了同一个事件**，
   开机时长第一次是**测**出来的，不是推的；
3. **§66.5 里「抓取开始时就已在开机中」是错的，已在原地划掉并更正**（新证据改写旧结论，
   旧结论留在原处不删，只标注作废 —— 与 §0.0 的一贯做法一致）。

一条独立旁证：`LogFrame.TitleText1` 在**整个标准开机窗口里一次 Text 写入都没有**，
而 remake 里这个 label 的静态初值正是 `STANDARD BOOT UP INITIALIZED`。
**没被写过的那个默认值本身就是「standard」**；`QUICK BOOT UP INITIALIZED` 是同一个
label 在 t=153 才被写进去的。两条同时成立，「抓取开始太晚」被排除。

### 67.2 量到的那张时间表（t = 按下 MONITOR BOOT 之后的秒）

诊断滚动屏 `DiagnosticFrame.ScrollingFrame.TextLabel1..45` 是**逐段揭示**的，不是一次全出：

| t | 诊断标签（累计可见） | `LogFrame.TitleText` | `CompanyLogo` |
|---|---|---|---|
| 0 | 1–8 | — | 0 |
| 1 | 1–25 | 1–2 | 0 |
| 2 | 1–27 | 1–3 | 0 |
| 3 | 1–43 | 1–5 | 0 |
| 4 | 1–45 | 1–5 | 0 |
| 5–13 | **全部收起** | **只剩 6** | 0（t≥8 起为 1） |

`BootFrame` 只在 **Main / Thermal / Power 三台**上，另四台没有 —— 与 remake 里
`RoomShell`「五台小监视器没有诊断屏」的结构一致。remake 实测同样是
`Main/Power/Thermal +boot`、其余四台 `-boot`：**这一条是量出来的巧合，不是照着原版摆的**。

### 67.3 改了什么

| # | 位置 | 改动 |
|---|---|---|
| ① | `SSS.ReactorBackend.Config.Shift` | `BootSeconds` 3 → **14**，并换掉那条自认占位的注释 |
| ② | `SSS.ReactorBackend.Config.Shell` | 新增 `BootScreen.Reveals`：**7 条**，就是 67.2 那张表 |
| ③ | `SSS.ReactorBackend.BootPanel` | **新模块**（~200 行）：按 `state.phaseTime` 把那张表施加到真实 label 的 `Visible` 上 |
| ④ | `SSS.ReactorBackend.Runtime` | `require` + `Initialize` + 初刷；publish 回调与 Heartbeat 各加一次 `Refresh` |

**`BootSeconds = 14` 的来由**：它在 t=8 之后就不再有内容（`CompanyLogo` 是最后一条），
而 t=14 `PreStartupFrame` 在**七台**上出现。3 是自认的 presentation default；
先前两次估的（10-01 flow 趟 21.8 s、09-26 ≤11 s）**量的都不是这一段** ——
它们量的是「MONITOR BOOT → 主拉杆被接受」，而主拉杆还要 `booted AND monitorPower AND
shuttersOpen`，中间夹着玩家走位。

**只建模可见性，不建模曲线。** 那份捕获里 `Position`/`Size`/`Rotation`/`CanvasPosition`
占 99.7%，但它是**按变化才写**的（一秒内最多一次采样），**够说「什么时候动了」，
不够说「沿着哪条曲线动的」**。所以 `BootPanel` **故意不做**任何位移/缩放/滚动动画：
「一行行在对的秒数出现、但不动」比「按一条谁也没量过的曲线缓动」**是更小的谎**。
（布尔值活得过采样，曲线活不过 —— 这就是分界线。）

### 67.4 怎么验的（§4.4）

**两边是两个互不相见的产物，比的是同一台机器。**

- **期望侧**：`_tools/_attic/scratch/aux_expect.py` 直接从 180 MB 原始行**重放** `Visible` 写入，
  产出 `aux_expect.txt`。它**没有见过 remake 的代码**。
  （重放里唯一有歧义的一格：同一秒内同一个 label 同时出现 `false` 和 `true` 写入 ——
  那是「先全隐藏、再单独显示一个」的写法，而**文件顺序在一秒之内也不可靠**。
  文件顺序恰好把 `false` 放在后面，照它读会把日志框从 t=5 一直空白到 153。
  同一对写入在 t=154 的 quick boot 里又出现一次、且那次结束时**一定是显示的**，
  所以 `true` 是这里的读法。**没有 show-then-hide 的样本；真出现时这条规则会读错，
  所以它被写下来而不是被假设。**）
- **实测侧**：`rblx_execute_luau`（官方工具，`datamodel_type:"Edit"`，§0.17 通道）
  用**克隆**的真 `Config`/`Engine`/`BootPanel`（§0.15：过期的 require 递过来的是少键的表）
  喂**假时钟**跑满整个 `Booting`，每一步之后读**真实部件**的 `Visible`（§0.2：读实例，不读模块）。
- **对照**：`aux_compare.py`，**14/14 秒全部相等，0 处不符**。
- **变异测试**（不能变红的检查不是证据）：
  - 去掉 t=5 那条的 `clearDiagnostic` → **t=5..13 全部变红**（诊断屏该收没收）；
  - `BootSeconds` 14 → 20 → **t=14..22 全部变红**（翻相位的时刻跟着走）。
  两个变异都被抓到。索引不是用眼睛数的（at=5 是**第 6 条**，不是第 5 条），
  是**搜出来**的 —— 「按位置读表」正是这一轮要抓的那类错。
- **收尾**：跑完把 `phase` 复位并刷一次，确认**驱动过的那 49 个 label 全部回到隐藏**，
  临时 Folder 销毁 ——**世界恢复原样**。
- **回归**：`bash _tools/run_tests.sh` 仍 rc=0。

### 67.5 **没有**验到的（必须分开写）

- **没在真 playtest 里看过一眼。** 验证走的是「假时钟 + 读实例」，不是「真人按一下按钮」。
  能证明的是**面板在正确的秒数变成正确的样子**，不是「玩家看到它了」。
- **没验世界侧**：原版那 14 秒里 E-VENT 排气、激光打火、音效，remake 一概没有。
  本轮只把**屏幕上看得见的那块**补上。
- **t=14 之后那一格捕获仲裁不了**：原版**从没写过 `BootFrame.Visible`**
  （它是**层层叠**，不是切来切去），所以捕获说不出原版在 `Ready` 那一刻是把开机屏
  **收起来**还是**盖在下层**。remake 的 `RoomShell.applyMonitors` 是**先全部收**再放选中的那张。
  这是**换屏方式**的差别，不是**屏上内容**的差别，**记为未测**、不计入「相符」（见 `aux_compare.py` 末尾）。
- **t=5 那条「全收」在捕获里没有任何解释**：为什么诊断屏在第 5 秒整屏收起、日志框只剩第 6 行，
  文件里没有对应的一句话。**照实保留，没有抹平成更好看的形状。**

### 67.6 数字

| 量 | 值 |
|---|---|
| 捕获里 `BootFrame` 后代路径 | **57** |
| remake 里被驱动的 label | **51** = 45 诊断 + 6 标题（数量由表里的**区间**推出，不另写一个计数常量） |
| 揭示条目 | **7** |
| `BootSeconds` | **14**（原 3） |
| 对上捕获的秒 | **14 / 14**，0 不符 |
| 变异 | **2 / 2 变红** |
| 开机屏长在哪几台 | **3 / 7**（Main / Thermal / Power），与捕获一致 |
| 开机屏出现前的 `authored-visible` | **0** |


---

## Phase 68（2026-10-01）—— 把「有 git 背书的那份代码」追平，以及「同时跑两遍测试」教我的事

Phase 67 收尾时按 §0.0 去核 `bash _tools/run_tests.sh`，**第一次读到的是红的**
（`watch mutations: 17 of 29 detected`，另一次 `25 of 29`），而 Phase 67.4 里我**已经写下了**
「回归 rc=0」。那条断言是**先写后验**的 —— 按 §1.4 第 4/5 条，这一节先把这件事说清楚。

### 68.1 那两次红不是回归，是**我自己把同一套测试跑了两遍**

背景任务那次和前台那次**同时在跑**。`_tools/selftest_watch.py` 用的是**两个写死的路径**：

```python
MUTANT = os.path.join(ROOT, "_tools", "_watch_mutant.luau")   # 唯一一份变异体
mutdir = os.path.join(ROOT, "_tools", "_mut_out")             # 唯一一个输出目录
...
shutil.rmtree(os.path.join(ROOT, "_tools", "_mut_out"), ignore_errors=True)  # 收尾时删掉
```

两遍互相覆盖变异体、互相 `rmtree` 对方的产物目录 → 变异体的产物**凭空消失** →
报成「NOT DETECTED」（其中一条更准确：`the mutant did not run at all`）。
换句话说，**它不报错，它报成「这条纪律没被守住」** —— 一个只在并发时出现的假阳性。

- 单独跑一遍：**`watch mutations: 29 of 29 detected`**，全 495 行输出，**rc=0**。
- 同时跑两遍：17/29 与 25/29，两次**给出不同的数字**（这本身就是「被污染」的指纹 ——
  一个确定性的 harness 不可能两次给自己不同的答案）。
- 其中**背景那一遍退出码是 0**：污染可以让 rc 也失去意义。
- `shipped file untouched (md5 32bba692e0e078f416789972aecd192a)` 在**两遍里都印着** ——
  所以「发货文件没被动过」这条保护**在污染下依然成立**，被破坏的只有**判决**。

**结论：`run_tests.sh` 不是并发安全的，跑之前确认没有第二份在跑。** 判据不是它的 rc，
是它的 `N of M detected` 那一行。

### 68.2 `src/ReactorBackend/` 追平（漂了 3 个 Phase）

PROGRESS 4766-4769 把 `src/` 定为**有 git 背书的那份「上一版正文」**，但它是**旧的** ——
Phase 59/62/65/67 改的都是 Studio 里的活模块，`src/` 停在 `c816196`。

做法（§0.17 的通道 + memory 里那条「字节不进上下文」）：

1. Studio（官方 `rblx_execute_luau`，`Edit`）把 10 个实例的 `Source` **POST** 到
   `http://127.0.0.1:8765/reflect/<磁盘名>`（sink `_tools/receive.py` 本来就在跑，不重启）。
2. 同一段脚本**自带 CRC-32**，把 `<磁盘名> <字节数> <crc32>` 也 POST 成 `__manifest.txt`。
3. 本机算出收到的每个文件的 CRC-32，与 manifest 比 —— **0 处不符**。
4. **比过之后**才 `cp` 进 `src/`，然后再比一遍 —— **10/10 逐位相同**。

按 §0.0 那条老规矩，**全程比哈希、不比字节数**；字节数只用来**发现**谁可能变了。

| 磁盘 | Studio 实例 | 磁盘旧 | Studio | 判 |
|---|---|---|---|---|
| `Config.luau` | `SSS.ReactorBackend.Config` | 10943 | 21693 | **改了 +10750** |
| `Engine.luau` | `…Engine` | 15612 | 17703 | **改了 +2091** |
| `Runtime.server.luau` | `…Runtime` [Script] | 4108 | 4991 | **改了 +883** |
| `LogPanel.luau` | `…LogPanel` | — | 6924 | **新增** |
| `BootPanel.luau` | `…BootPanel` | — | 13873 | **新增** |
| `StateBridge.luau` / `ControlBinder.luau` / `VisualFeedback.luau` / `RoomShell.luau` / `VisualFeedback.client.luau` | 同名 | — | — | **逐字节相同** |

那 5 份「相同」有意义：它们说明漂移**不是**「整份镜像都没人管」，而是
Phase 59/60 那阵有人**手工拉过一部分**（RoomShell / VisualFeedback mtime 是 09-30），
而之后新写的模块**没有进过镜像**。**半新半旧比全旧更难认** —— 这正是要查一次的原因。

命名约定从对照表里读出来：`ModuleScript → <Name>.luau`；`Script → <Name>.server.luau`
（`Runtime`）；`LocalScript → <Name>.client.luau`（`StarterPlayerScripts.VisualFeedback`）。
`Data/reflect/` 是这次的中转区，已进 `.gitignore` —— **权威是 `src/`，不是它**。

### 68.3 本轮**没有**做的事

- **没有 commit**（用户没让）。
- **没有重跑 Phase 67 的逐秒对照** —— 它验的是 Studio 里的活模块，而本轮**一个字节都没改**
  Studio 侧（只读 `Source` + POST），所以那份 14/14 仍然成立，不需要重测。
  **「我没改它」是推理，不是测量** —— 依据是 68.2 那 10 个 crc32 与 Phase 67 记的
  `BootPanel`/`Config` 状态一致，以及本轮对 Studio 的全部调用都是读。
- **`.gitignore` 改动未提交**，与其它改动一起等用户。

---

## Phase 69（2026-10-01）—— 拉取 TRG-WIKI：104 页，**一个字节的正文都没变**

用户的「拉去做了快点」= 刷新 `reactor.fandom.com` 的快照（**不是 git 仓库**，见 memory
`trg-wiki-snapshot` / `DECISIONS_2` 209）。产物 `D:\RobloxAssetsDownloader\TRGWiki.json`。

**结果：wiki 自 09-30 起没动。**

| 量 | 值 |
|---|---|
| 页数 | **104**（ns 0 = **75**，ns 14 = **29**） |
| 新增 / 删除 | **0 / 0** |
| 正文改动 | **0** |
| 修订时间戳改动 | **0** |
| `pulled` | `2026-09-30T13:58:26Z` → `2026-10-01T12:14:54Z` |

所以「拉一次」这次的产出是**一句负结论**：没有新东西要读。

### 69.1 工具：`_tools/trgwiki_pull.py`（stdlib）

用户自己那份 `D:\RobloxAssetsDownloader\TRGWikiPull.py` **没动**（它在另一个仓库里，
memory 明确写了不许往那儿提交）。新工具放在**我们的**仓库里，两个理由：

1. 那份顶部 `import requests`，而 `/c/Python314/python` **没装 requests**。
   不为这个装包 —— 同样的 API 用 `urllib.request` 走通。**跑两次，rc=0。**
2. **`apnamespace=0` 不是「全部页面」**（memory 209 的坑）：2026-09-22/23 wiki 把正文挪进了
   Category 命名空间（`Shifts` → `Category:Shifts`，逐字节相同），所以忠实的 ns0-only 刷新会
   **77 → 75 并静默丢掉班次机制那篇**。本工具拉 **ns 0 ∪ ns 14** 并**把差值打出来**。

### 69.2 【坑】「内容相同」不等于「文件相同」——我第一版丢了三层元数据

第一版照抄用户脚本的输出形状（`wiki` / `source` / `total_pages` / `pages`），写完一 diff：
**正文 0 处不同、时间戳 0 处不同，但文件 207437 → 207311**。差在**顶层键**：

```
old keys = [api, namespaces, pages, pulled, source, total_pages, wiki]
new keys = [pages, source, total_pages, wiki]          ← 丢了三个
```

**用户那份脚本根本不写这三个键** —— 所以 09-30 那份不是它产的，而**照抄它的形状就是删功能**
（`CLAUDE.md` §1.4 #2）。补回后除 `pulled` 外**逐字段相同**、字节数也回到 207437。

`namespaces: [0, 14]` 是关键那个：**它是「ns 0 ∪ 14」这个决定唯一的记录**。
丢了它，下一个人看着一份干净的 JSON **分不出**「忠实的一次拉取」和「只拉了 ns0 的一次」——
而那正是 209 记的那个坑。

**教训（和 §0.0 那条是一对）：** §0.0 说「**别只比字节数**」（长度相同≠内容相同）；
这条是它的对偶 ——「**别只比你以为重要的那几个字段**」。我比了 `content` 和 `timestamp`，
两者都相同，就差点把「文件变了」判成「什么都没变」，而变的是**我没去看的那一层**。

备份：`TRGWiki.json.261001.bak`（脚本自己写的；**已存在就跳过**，所以重跑不会把「拉取前」
覆盖成「拉取后」）。重跑验证：`--no-write` 不需要，第二次跑 `added/removed` 仍为 0/0。

## Phase 70（2026-10-02）—— 优化用户自己写的开机采集脚本：新文件 `_tools/TRG_original_boot.luau`

用户原话（这一轮的活就是这一句）：**「优化一下我写的那个开机（主要是采集，然后我注入）」**。

「我写的那个开机」指的是 **`C:\Users\andypeng1NB\AppData\Local\SolaraTab\Test.lua`**
（4935 字节 / 4564 字节文本 / 160 行）—— 用户自己在 Solara V3 里 `loadstring` 注入的
**开机屏逐属性变化采集器**。**那个文件一个字都没改**（执行器会重写 tab 目录下的所有文件，
改它等于白改）。优化落在**本仓库的新文件** `_tools/TRG_original_boot.luau`，
用户从 8766 上 `HttpGet` 下来注入。

**先读了它，再说优化了什么** —— 它自己的产物就是优化的靶子：
`Data/auxcollection/startup/ScreenChanges.txt`，**1,162,737 行 / 179,788,590 字节 / 158 秒**。

### 70.1 靶子是量出来的，不是猜的

| # | 缺陷（从它的源码和产物读出来的） | 这一份怎么处理 |
|---|---|---|
| a | `WatchProperties` 按 ClassName 挂，`Position`/`Size` 在表里 → `…MonitorUI.GlitchEffect.GlitchFrame` 每帧写一行 = **99.4% 的行** | `GeometrySkip = {'.GlitchEffect'}` —— **按路径**不挂几何属性，源头不产生 |
| b | `appendfile` 且从不先 `writefile` → **两次注入串成一个文件**（Phase 66 那个「文件顺序不是时间顺序」的来源） | 首次覆盖、之后追加；本地名带时间戳 |
| c | 没有 `DescendantAdded` → 运行期克隆的开机帧永远看不见 | 挂 `Monitors.DescendantAdded` |
| d | 没有传输层 → 手搬 180 MB | POST 到 8765 的 `originalboot/` |
| e | 没有体积上限（实测 **1.14 MB/s**） | 每键 2000 行 / 全局 24 MB / 2 s 或 64 KB 冲一次 |
| f | 每行都算一次 `GetFullName()` | 登记时算一次，之后复用 |
| g | 白名单缺 `Image` / `ImageTransparency` / `TextTransparency` / 颜色 / `ZIndex` | 补上 |
| h | 停止条件 `'12:00 AM'` 和班次开盘撞车（表盘开盘就是 12:00 AM），且没有手动停止键 | 等 **11:59 AM → 12:00 PM 的交接**；`RightControl` 手动封存 |
| i | 没有自报死因 | `alive` / `hello` / `boot` / `meta` / `error` |

**根没有动**：它第 68 行是 `workspace:FindFirstChild("Monitors")`，这一份的 `RootName` 也是
`'Monitors'` —— **作用域逐字相同**，没有借优化收窄。

### 70.2 收尾时被测试台翻出来的东西（这一轮最花时间的部分）

新写了三个本机工具，都在 `_tools/`：

- **`boot_harness.luau`**（702 行）—— 假世界 + 假 sink + 虚拟时钟。五个场景：
  `default` **29 PASS** / `nobutton` 6 / `noroot` 6 / `nosink` **30 PASS + 1 SKIP** /
  `rightcontrol` 28，合计 **99 PASS / 0 FAIL / 1 SKIP**。
- **`verify_boot_capture.py`** —— 从**七个旧分析器自己的源码里**把行格式正则读出来，
  要求七个**完全一致**再逐行验捕获（三个捕获共 **6015 行，0 行不合法**）。
- **`selftest_boot.py`** —— **8 个变异，8 个都被抓住**。

**它翻出的四个 bug，全是「测试在说谎」那一类，值得记：**

1. **`nosink` 场景声明了却从来没真拒过**（`SINK_UP` 声明后从没被压低），于是四条红线
   对着一个**一直在工作**的 sink —— 四条 fail **不指向被测物**。
2. **`noroot` 断言的是「加载时就报死」**，而文件的契约是「**按下才解析世界**」——
   那条契约是**故意的**（StreamingEnabled 下加载时没有根通常只是「还没到」，
   为它杀一趟是假警报）。改的是**测试**，不是文件。
3. **`dump()` 写出一行 `'0'`**：`f:write(string.gsub(...))` —— gsub 返回 `(text, count)`，
   **第二个返回值被当成第二个参数写进文件**。一个字符的疏忽，症状是**数据损坏**。
4. 测试台自己的**缓冲相位依赖**（Phase 64 那个硬币）：现在每次测量前先 `flushNow()`，
   `RightAlt` 那条则是**先等过一次定时器**再测，让变化**可证地落在无定时器的窗口里**。

**真正改了一次被测文件**：`startRecording()` 原来先 `emit(表头)` 再 `arm()`，
所以一次失败的按键会留下**一个只含表头的文件** —— 看起来像「开始了」、像「有数据」。
现在 `arm()` 在前，失败时 `ScreenChanges.txt` **一个字节都不动**，死因写在 `meta.txt`。

### 70.3 验证状态（分开写）

**验了（本机，不进游戏）**：`bash _tools/run_tests.sh` **rc=0**，里面新加三道门 ——
整文件 **Lua 5.1 解析**、`boot_harness.luau` 五个场景、`verify_boot_capture.py`、`selftest_boot.py`。

**没验（必须说清楚）**：**它一次都没在原版里跑过。** 因此三条是**设计意图不是观测**：
`GeometrySkip` 的粒度够不够、每键 2000 行切得对不对、`MaxPendingLines = 20000`
够不够扛开机峰值。**跑完第一件事读 `suppressed.txt` 和 `meta.txt` 的 `dropped_chunks=`**。

### 70.4 三个身份数（注入前核这个，别核时间）

| | 字节 | 行 | md5 |
|---|---|---|---|
| `TRG_original_boot.luau` | **38609** | **835** | **`243adb577f1442a069144f0bbb6df8f0`** |

这一份比另两份**更硬**：采集器/监视器经 Studio 编辑层搬运，这一份是 `HttpGet` 直取 ——
**盘上就是注入进去的那个字节**，中间没有一层会改文本。

字节性质**这次是量过的、不是断言的**：0 个反斜杠、0 个 CRLF、结尾有换行、纯 ASCII。

用法全文 `docs/BOOT_HOWTO.md`。取舍 `DECISIONS_2.md` **236..242**。

---

## Phase 71（2026-10-02）—— 第一趟真机跑出来的两个缺陷：`b1` → `b2`

`_tools/TRG_original_boot.luau`（Phase 70 交付的那份）**第一次在原版里跑起来了**。
产物 `Data/originalboot/261002-133048/`，`meta.txt` 记着 `build=b1` ——
**这份产物自带它是哪一版跑出来的**，所以下面每个数字都能对回代码。

### 71.1 干净的那几项（设计目标本身，全部有字节支持）

| | 值 |
|---|---|
| `hello.txt` | `root_visible_at_inject=true`；`waiting_for=Workspace.Consoles.MainReactorConsole.MonitorBootButton` |
| `boot.txt` | `t0=13:31:01` —— **按到了那一个 `ClickDetector`** |
| `meta.txt` | `reason=wrap` / `elapsed_s=94.93` / `lines=5156` / `bytes=874526` |
| 传输 | `sink_chunks=47` / `sink_bytes=874526` / `local_chunks=0` / **`dropped_chunks=0`** / **`suppressed_keys=0`** / `sink_error=none` |
| 正文 | 5156 行、5155 数据行、**0 行不合法**（`verify_boot_capture.py`）、**`.GlitchEffect` 路径 0 条** |
| 速率 | **≈9.2 KB/s** —— 对照 `Test.lua` 的 **≈1.14 MB/s**（1,162,737 行 / 179,788,590 字节 / 158 s） |

`dropped_chunks=0` 是一次真峰值下的 `MaxPendingLines = 20000` 判决，
`suppressed_keys=0` 是每键 2000 行预算没有切到任何键，
`.GlitchEffect` 零条是那条「按路径而不是按类型」的几何过滤第一次被真数据检验。
**三项**都是 Phase 70 里写着「这是设计意图不是观测」的东西，现在其中三项变成了观测。
**还有三项没变成观测**（`GeometrySkip` 的粒度、预算切点、`MaxPendingLines` 的余量），
见 71.5。

**`t0` 存在本身就是「注入早于按下」的证据**（2026-10-02 澄清）：采集器是**按下才 `arm()`**、
才做普查建基线，所以按之前的静止画面**构造上不产生行**；晚注入的趟会缺 `t0`
（`hello.txt` 那句 note 说的就是这件事）。`boot.txt` 有 `t0=13:31:01`、第一行数据也在
`13:31:01`，两者同秒不是巧合，是设计。

### 71.1.1 这份产物里有什么（按 `Workspace.Monitors.<X>.Screen` 分组，5155 数据行）

| 子树 | 行数 | 主要内容 |
|---|---|---|
| `AlertsControlRoomMonitor` | **1936** | `AlertFrame1..9` 的 `Visible`（1924 行）逐格显隐 |
| `PowerControlRoomMonitor` | 1373 | CBL 图 + `TempLabel` |
| `MainControlRoomMonitor` | 1113 | `RadiationLabel` 55 / `HDEFLabel` 43 / `TempLabel` 36 / `PressureLabel` 36 / `OutputLabel` 34 |
| `ThermalControlRoomMonitor` | 540 | 风扇图 |
| `LogControlRoomMonitor` | 116 | **只有透明度**，见 71.3 |
| `Forecast` / `Quota` | 55 / 22 | |

属性分布：`Visible` 2257 / `Position` 2142 / **`Text` 280** / `Size` 111 / `ImageColor3` 104 /
`BackgroundTransparency` 102 / `CanvasPosition` 61。**`Text` 那 280 行全部落在别的 label 上**
（读数、表盘），而整份文件里 `ALERT` / `IGNITION` / `COMBUSTION` / `PRIMING` / `SEQUENCE`
**一个字符串都没有** —— 开机链念出来的那串消息**只**走日志面板那三格，
所以 71.3 丢的不是一部分旁白，是**全部**旁白。这也是这份产物值得留下的原因：
它是**唯一**一份（`GeometrySkip` 生效后）干净的 4 Hz 开机屏样本 —— 5155 行里
`.GlitchEffect` **零条**，而 `Test.lua` 那 1,162,737 行里 **99.4%** 就是它；
**能读的比例从 0.2% 变成 100%**。

### 71.2 缺陷一：`wrap` 规则在班次的**开盘**处封存

`b1` 的时钟规则是「`12:00 PM` 封存；`12:00 AM` **且已经离开过开盘值**也封存」。
写它的前提是**假设表盘开盘就是 `12:00 AM`**（Phase 62 那条推断）。
第一趟给出的是反面：

| 时刻 | 表盘 | 同拍别处在发生什么 |
|---|---|---|
| `t0` = 13:31:01 | 那一按 | — |
| `t≈18 s` | **`11:51 PM` 是第一个读数** | 「离开过开盘值」这个保险**第一次读数就被解除** |
| `t≈88 s` | `11:59 PM` | 温度 248 F / 输出 0 GW/H / HDEF 5 % |
| `t≈95 s` | 跨到 **`12:00 AM`** | **点火**：温度 248 → 9478 F、输出 0 → 146 GW/H、HDEF 5 → 99 %、热工监视器 `AUTO RECALIBRATION IN PROGRESS` |
| `t=94.93 s` | — | `b1` 在这里封存 |

开机链的 `START-UP COMPLETED` 在四趟实测里是 **86..146 s**（中位 109，Phase 65），
所以那一刀**大概率切在链子结束之前**。规则本身没有写错代码 —— **是它防的那件事没被写进去**：
「只在离开开盘值之后」这个保险，要防的正是「开盘值」这件事，而实测的开盘值是 `11:51 PM`。
**没有场景覆盖这条路径**（见 71.6），所以它一路绿到真机上。

### 71.3 缺陷二：出生时的值被当成基线播掉 —— 日志面板的**文本一行都没有**

`b1` 挂上了 `DescendantAdded`（Phase 66/67 的教训），登记就播种成基线。
第一趟里 `TemplateLogFrame1/2/3` 那三格的**唯一**一类行是透明度：

```
TemplateLogFrame{1,2,3}.{BufferFrame,Frame,Frame2}|BackgroundTransparency   共 104 行
TemplateLogFrame{1,2,3}.TextLabel|TextTransparency                         （含在上面）
TemplateLogFrame*|Text                                                     0 行
```

**开机自己那句旁白一个字都没抓到。** 机制不是猜的，是排除出来的：`Text` 在
`WatchProperties.TextLabel` 里（同一趟有 280 行 `Text` 落在别的 `TextLabel` 上），
所以若那个实例在按下时就存在，任何一次 `Text` 赋值都会在下一个 tick 变成一行。
没有，就说明**实例是在按下之后才出现的**，而它第一次被看见时消息**已经在里面**——
**游戏先写文本、再把帧挂进树**。登记把消息本身播成了基线，之后没有任何变化能跟它不同。
（三格的首次出现时刻 13:31:23 / 13:31:25 / 13:31:41，首值是渐隐中途的 ≈0.52 / 0.54 / 0.52，
与「新实例挂进来、渐隐继续跑」一致；**但这条不能只靠首值判断**，判定用的是「`Text` 若有变化必然会被记下」。）

### 71.4 改了什么（`b1` → `b2`，42056 字节 / 886 行 / `852753d6861c23836c3cd634611bd04a`）

1. **午夜不封存，改成一行注释标记**：`# MARK midnight at HH:MM:SS … the run continues`。
   理由是同一张表：那是班次的**开盘**，而且**那一刻本身就是有用的锚点**，丢掉它是另一种缺陷。
   正午照旧封存（用户自己给监听窗口定的终点）。**用注释行**而不是新字段，是因为行格式冻结
   （`DECISIONS_2` 237）而 `#` 行七个读者全都跳过（`DECISIONS_2` 244）。`seenNonNoon` 整段删掉。
2. **出生记录**：`register(obj, born)` —— 只有 `DescendantAdded` 那条路传 `born=true`，
   该实例的每个被监视键在登记时把基线设成 NUL 哨兵（`fmt()` 的输出里不可能有 NUL）并在下一个
   tick 写真实值，走的还是「一键一行」那条路、也照旧吃每键预算。初始全树普查**照旧静默播种**
   —— 那是「改了又改回去不算数」这条规则的全部（`DECISIONS_2` 245）。
   代价写在 `docs/BOOT_HOWTO.md` §1.2：运行期克隆的一棵子树会多写一遍它的属性。

### 71.5 验证（本机）与**没验的**

本机：`bash _tools/run_tests.sh` **rc=0** ——
`default` **33 PASS** / `nobutton` 6 / `noroot` 6 / `nosink` **34 + 1 SKIP** / `rightcontrol` **30**，
**0 FAIL**；`verify_boot_capture.py` 三个捕获 **6039 行 / 0 行不合法**；
`selftest_boot.py` **11 个变异 11 个抓住**（新增三个：丢掉出生记录、让午夜重新封存、
把 `# MARK` 写成数据行）。

**没验的：** 71.1 那张表全部是 `b1` 的字节，而 `b2` 的两处改动**一次都没在原版里跑过**。
出生记录会不会在开机峰值写得太多（这是 `b2` 新引入的量，`b1` 的 5156 行**不能**用来预测它）、
`START-UP COMPLETED` 那句到底长什么样、以及 `GeometrySkip` 的粒度 —— **都还是设计意图**。
跑完第一件事仍是读 `suppressed.txt` 和 `meta.txt` 的 `dropped_chunks=`。

### 71.6 测试台漏掉的那条场景（会复发，所以要写下来）

原来的时钟场景只把 `12:00 AM` 当**开盘值**试了一次，于是「离开过之后倒退回午夜要封存」
这条规则**没有任何场景覆盖**。场景现在是按**实测的形状**摆的：
`11:51 PM → 11:59 PM → 12:00 AM`，并要求它不封存、且留下一个 `# MARK`。
**照着自己想象的输入写场景，等于照着想象的输入改代码** —— 而这里想象的输入
（开盘 = `12:00 AM`）和真机的输入（开盘 = `11:51 PM`）只差一次读数。

## Phase 72（2026-10-02）—— 第二趟真机：`b2` 的两处改动各自判决，以及翻出来的第三条缺陷（`b3`）

用户的最后一句是「**12:00AM是反应堆开机完成，还有搞完了**」。这句话把这一趟的读法定死了：
`12:00 AM` 是**开机完成**的时刻、不是收盘；产物到手就是**跑完了一整趟开机**。
于是去读第二趟的字节 —— Phase 71 里那两条「还没验的」全部有了答案，
而同一批字节**翻出了第三条缺陷**。

产物三份，同一趟班次（`14:00–14:07` 左右）：

| 目录 | 谁 | 自报 |
|---|---|---|
| `Data/originalboot/261002-140017/` | 这一份（`b2`） | `build=b2` / `reason=hotkey` / `detail=RightControl` |
| `Data/flow/original_261002-140019` | `r60` 采集器 | 1,022,890 字节的**文件**（不是目录） |
| `Data/originalwatch/261002-140021/` | `w61` 监视器 | 11 份产物、无 `error.txt` |

### 72.1 干净的那几项（在 **4 倍于 `b1` 的量**下）

`meta.txt`：`elapsed_s=428.82` / `lines=25007` / `bytes=4178252` /
`sink_chunks=200` / `sink_bytes=4178252` / **`dropped_chunks=0`** /
**`suppressed_keys=0`** / `sink_error=none`。

Phase 71.5 里我写着「出生记录会不会在开机峰值写得太多，`b1` 的 5156 行**不能**预测它
—— 跑完第一件事是读 `suppressed.txt` 和 `dropped_chunks=`」。答案：
**5 倍的行、4 倍的字节，一个都没丢、一个键都没撞上预算。** 这是 `b1` 结构上
回答不了、只能靠这一趟回答的那一格。

### 72.2 缺陷一（午夜）的判决：**成立**

`# MARK midnight` **恰好一行**（`ScreenChanges.txt:4228`，`at 14:02:10`），
而捕获继续记到 **`14:07:44`**，也就是越过 `b1` 被切断的那一刻 **5 分多钟**。
Phase 71.4 的第 1 条（午夜改注释、不封存）从设计意图变成观测。

### 72.3 缺陷二（出生记录）的判决：**只成立一半 —— 这就是 `b3`**

`b1` 的 `Text` 行是 **0**，`b2` 是 **3**，三条都在开局 28 秒内：

| 时刻 | 实例 | 文本 |
|---|---|---|
| `14:00:45` | `…LogsFrame.TemplateLogFrame3.TextLabel` | `<b>[ALERT]</b> - SUBSPACE REACTOR START-UP SEQUENCE INITIATED` |
| `14:00:47` | `…TemplateLogFrame2.TextLabel` | `<b>[WARN]</b> - ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY` |
| `14:01:03` | `…TemplateLogFrame1.TextLabel` | `PRIMING ISOTOPE E COOLANT NETWORK` |

也就是**每格的第一条**。然后**整整 6 分 41 秒**（`14:01:03` → `14:07:44` 最后一行）
**再没有一条 `Text`** —— 而同一趟、同一个 `LogsFrame`：

| 仪器 | 它数到的日志面板消息 |
|---|---|
| 这一份（`b2`） | **3** |
| `r60`（`Data/flow/original_261002-140019`） | **35 条不同的消息**，含 `START-UP COMPLETED` |
| `w61`（`Data/originalwatch/261002-140021`） | 那三格的 `TextLabel` 被**销毁 47 次**（`12 + 27 + 8` 个不同实例） |

**三者说的不是三件事，是同一件事的三个侧面**：面板**每条消息克隆一行新实例、
复用那三个固定名字**，行渐隐完就销毁。所以「35 条消息」是真的、
「47 次销毁」是真的、而这一份只看见 **3** —— 那 3 是**测量缺陷**，不是面板行为。

### 72.4 根因：**键是路径，不是实例**（在交付的源码里，不在猜测里）

`register()` 的门是 `keys[key] == nil`，`key = full .. '|' .. prop` ——
一个**按路径**的一次性门。后果有两层，第二层才是致命的：

1. 同一路径的第二个实例**整段跳过**（不挂信号、不记出生）；
2. 而**活下来的那条连接指着已经被 `Destroy()` 的旧行**。

第二层意味着：就算旧行再也不变，它也**占着**这个键 ——
新实例的每一次 `Text` 赋值**没有任何东西在看**。

**三方独立佐证**（都在产物里，不是推理）：
`Rotation` 只 18 行、`ZIndex` 只 23 行，且全部落在 `14:01` 之前，
而采集器在整趟里是活的；`r60` 记到 35 条；`w61` 数到 47 次销毁。

`b3` 的修法（`_tools/TRG_original_boot.luau`）：

- 新状态 `ownerOf[key]` / `connOf[key]` / `entryOf[key]`；
- `watch()` 把连接记进 `connOf[key]`；
- 新助手 `mark(key, obj, full, prop)` 把「哪些键脏了」和「这份条目属于谁」**分开**：
  信号里只 `mark`，tick 才写行；
- `register()` 里追加一支：`elseif born and ownerOf[key] ~= obj then`
  → 断掉旧连接（否则一条死连接会继续往一条它已经不占的路径上写，
  产物就会报出面板**从没显示过**的消息）、挂新实例的信号、出生记录重来一次。
- `keys[key]` 与 `writes[key]` **故意保留**：每键预算是**按路径**记的，
  因为 `suppressed.txt` 的账本写的就是路径。

### 72.5 顺手修掉的一处说谎（文档级）

`TRG_original_boot.luau` 第 2 行的头注释还写着 `(build b1)`，而 `CONFIG.Build`
已经走过 `b2` —— 产物自报的名字取自**代码**里的那个（所以两趟的 `meta.txt` 都是对的），
**只有注释在撒谎**。`b3` 一并改成 `(build b3)`。**散文说的谎和代码说的谎一样贵。**

### 72.6 我自己的一个更正：表盘的速率，我上一轮猜错了

同一份产物里有 **318** 次 `QuotaControlRoomMonitor…TimeFrame.TimeLabel` 的 `Text`：

| 时刻 | 表盘 |
|---|---|
| `14:00:54` | `11:51 PM` —— 第一个读数 |
| `14:02:10` | `12:00 AM` —— 9 个表盘分钟用了 76 s（均值 ≈8.4 s/表盘分钟），**单步间隔在 2..23 s 之间跳** |
| `14:02:10` 之后 | **恰好 1 表盘分钟 / 真秒**，一路保持 |
| `14:07:22` | `5:08 AM` —— 最后一次读数 |

所以「午夜后 1 表盘分钟/真秒」是对的，**我此前按「8.75 s 恒速」外推到正午的
「≈105 分钟」是错的**（按 1 s/表盘分钟，午夜到正午只剩 ≈7 分钟真实时间）。
`w61` 源码注释里那句「roughly thirteen real minutes」指的是同一件事，方向是对的。

**这条更正值得留一句**：错在**把一段慢区间的斜率当成常数**，而它恰好在一个
不是慢而是**另一套速率**的区间边界上。同类错误在这份文档里出现过不止一次
（§0.0 那条「凡按名字替我回答问题的配置项，读到的就不是测量」）。

### 72.7 验证（本机）与**没验的**

`bash _tools/run_tests.sh` **rc=0**：

- `boot_harness.luau` 五场景 —— `default` **37** / `nobutton` 6 / `noroot` 6 /
  `nosink` **38 + 1 SKIP** / `rightcontrol` **34**，**0 FAIL**；
- `verify_boot_capture.py` 三个捕获 **6132 行 / 0 行不合法**，
  正则仍是从七个读者源码里读出来的；
- `selftest_boot.py` **12 个变异，12 个都被抓住**（新增第 7 条：
  把 `elseif born and ownerOf[key] ~= obj then` 换成 `elseif false then`，
  必须红在 `a second instance on the same path is recorded too, so a path is not an object`）。

测试台新增：信号桩补了一个**真的 `Disconnect`**（原来没有，
于是脚本自己的 `pcall(conn:Disconnect)` 会静默失败、把**正确的**文件报成坏的）、
`LOGS` fixture、新 §5b「`THE SAME PATH, TWICE`」四条断言；
表头检查改成**从交付的源码里读 `Build`**，不再在测试台里硬编一份
（那个字面量是「每次构建都会变的那一个数」的第二份副本）。

**没验的：** `b3` **自己一次都没在原版里跑过**。本机证据在 §72.7，真机证据要等下一趟注入。
**跑完第一件事**：`grep -c 'TemplateLogFrame' ScreenChanges.txt` 看那个数是不是从 3 涨到几十，
以及 `Text` 行里有没有 `START-UP COMPLETED`。

### 72.8 测试台漏掉的第二个形状（和 71.6 同类，所以写在一起）

`b2` 的出生记录**有**测试、也**真红过** —— 但那个场景克隆的是一个**新路径**
（`TemplateLogFrame4`）。真正的病灶是**同一个路径上的第二个实例**，
那个形状当时**不在测试台里**。于是 `b2` 带着一套「全绿」的测试上了真机。

**71.6 与 72.8 合起来是一句话：测试台只覆盖你想到的形状，
而缺陷长在你没想到的那个形状上。** 两次的补救都只能是**同一条**：
让产物本身带上足够的信息，好让真机替你补形状。

### 72.9 顺带记下、**没有动**的一件事

remake（`The Reactor : AIRemake`）的 `LogPanel`（Phase 65）**复用**那三格固定 label，
而原版**每条消息克隆一行新的**。这是 remake 与原版的一处**结构性差异**，
与 Phase 65 的表直接相关 —— 本轮**只记录不改**（§1.4 第 1 条：不动玩法机制）。

## Phase 73（2026-10-02）—— operator 问「那你开机能写吗」，于是把开机在活 VM 里**当场重跑一遍**  [DONE — 本机验过]

原话：**「那你开机能写吗」**。这不是要我再写一遍 —— 是要我拿东西出来。Phase 54 里
同一件事他说的版本是「你根本不会做开机」。所以这一轮**不写代码**，把 remake 里那两半
各驱动一遍，读实例状态（§0.2），再把数字写下来。

### 73.1 通道：官方那条这次被沙箱挡住，只有插件 VM 能 `require`

（同一条已写进 `CLAUDE.md` §0.17。）官方 `rblx_execute_luau`（`datamodel_type:"Edit"`）
在 `SSS.ReactorBackend` 上**两种写法都被拒**，而 `ReactorBackend` 整条文件夹带着
`Capabilities = LoadUnownedAsset (and 3 more)`：

| 写法 | 报错 |
|---|---|
| `Clone()` 到临时 Folder 再 require（§0.15 的现成解法） | `cannot reparent 'Config' to 'ServerScriptService.__StartupDemo' since '…__StartupDemo' has additional values for the Capabilities property: LoadUnownedAsset (and 3 more)` |
| 克隆进 `ReactorBackend` 自己 | `cannot reparent '__demo_Config' to 'ServerScriptService.ReactorBackend' since '…ReactorBackend' has additional values …` |
| 直接 `require(backend.Config)` | `cannot require 'Config' since 'Config' has additional values for the Capabilities property: LoadUnownedAsset (and 3 more)` |

**两条通道各管一半，别用一条的失败去否定另一条。** §0.17 原来记的是「源码搬运走官方」，
理由是插件 VM 的 `GetAsync` 是桩；这一轮补的是**反方向**：**要 `require` 工程模块并在活 VM 里
驱动它，走第三方 `mcp__robloxstudio__execute_luau`** —— 那个 VM 允许 `Clone()` 到临时
Folder 再 require。三次报错都指向「目标」而不指向「沙箱」，这一点和第 225 行那条
`ProtectedString expected, got nil` 是同一张脸。

**代价记下来**：这一条花了三次调用才试出来。下次撞上 `Capabilities` 字样，
**直接换通道，不要改写法**。

### 73.2 上半：开机链（`Config.Shift.StartupSteps` + `LogPanel`），当场跑

私有 `Engine`（`random` 喂常量 0）+ 假时钟，`monitor_power → shutters → boot`，
再 `start` 之后按 1 s 拍推进。**读的是真监视器上那三格 label**：

```
StartupSteps = 16 messages, hold sum 113.4 s
BootSeconds  = 14 s, 7 reveals
boot -> Ready at 14 s;  Running at t=114 s after the master switch
chain replay: 16 non-control events, first 16 vs the table -> mismatches=0
  first: <b>[ALERT]</b> - SUBSPACE REACTOR START-UP SEQUENCE INITIATED
  last : PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS
log panel draws 4 row(s) -- newest four:
  [TemplateLogFrame3] <b>[ALERT]</b> - ALL SYSTEMS READY, CORE IGNITION IMMINENT
  [TemplateLogFrame3] <b>[ALERT]</b> - COMBUSTION LASERS FIRING
  [TemplateLogFrame3] <b>[ALERT]</b> - START-UP COMPLETED
  [TemplateLogFrame1] PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS
```

四格**正是最新四条**（不是最旧四条），前三条走红模板、最后一条走青色模板 ——
`TEMPLATE_BY_KIND` 的 `ALERT → TemplateLogFrame3` / `INFO → TemplateLogFrame1` 当场成立。
翻 `Running` 在 **t=114**，hold 之和 **113.4**（差的那一拍是 `startupHold` 整数累加、
最后一条 hold=4 的累计门槛 113.4 跨到 114 才满足）。

### 73.3 我自己的断言错了，**而那个错本身就是这条检查的变异证据**

第一趟跑出 **`mismatches=13`**。不是引擎错：`Command('start')` 先调 `AdvanceStartup()`
发掉三条 `hold=0`，**之后**才在函数尾部 `self:Log('CONTROL', 'start')`（Engine 第 195 行），
所以 `eng.events[base+i]` 从第 4 条起整体错位一格 —— **13 = 16 − 3**，数对得上。
把 `CONTROL` 滤掉之后 **0 错**。

**这条不是澄清，是证据**：它证明这组断言**会红**，而且红在它该红的地方
（Phase 62 的纪律：一条红不了的检查不是检查）。我没有为它另造变异 —— 变异自己撞上来了。

### 73.4 下半：开机屏（`Config.Shell.BootScreen` + `BootPanel`），当场跑

`BootFrame` **在主控室监视器上**，不在日志监视器上 —— 第一趟因此报了
`attempt to index nil with 'DiagnosticFrame'`。普查结果（顺带量到的）：

```
MainControlRoomMonitor +boot   PowerControlRoomMonitor +boot   ThermalControlRoomMonitor +boot
Alerts / Forecast / Log / Quota  -boot
```

**七台里只有三台带 `BootFrame`**（`Config` 第 40 行说的是 `PreStartupFrame` 写七台，不是这个）。

驱动 `BootSeconds=14` 那一趟，t = 按下开机键之后的整秒：

| t | phase | diag 可见 | log 可见 | logo |
|---|---|---|---|---|
| 0 | Booting | 1–8 | – | 0 |
| 1 | Booting | 1–25 | 1–2 | 0 |
| 2 | Booting | 1–27 | 1–3 | 0 |
| 3 | Booting | 1–43 | 1–5 | 0 |
| 4 | Booting | 1–45 | 1–5 | 0 |
| 5 | Booting | **–**（清空） | **6** | 0 |
| 6–13 | Booting | – | 6 | 0（t=8 起 logo=1） |
| **14** | **Ready** | – | – | 0 |

与 `Config.Shell.BootScreen.Reveals` 的 7 条**逐条对上**：t=0 的 1–8、t=1 的 9–25 + log 1–2、
t=2 的 26–27 + log 3、t=3 的 28–43 + log 4–5、t=4 的 44–45、t=5 那条「清空 diag + 清 log 1–5 +
只亮 log 6」的怪条目、t=8 的 `CompanyLogo`。t=14 翻 `Ready` 时整屏收掉 —— 那是 `RoomShell`
按 phase 换脸，不是 `BootPanel` 写的。

### 73.5 世界还原（动过的都要放回去）

- `LogsFrame` 演示前 **1** 个子物体，演示后销毁自己画的行 → 回到 **1**。
- `BootFrame` 下所有 `GuiObject` 的 `Visible` 演示前**快照**，演示后**按快照逐个写回**
  （authored-visible **69 → 69**）。快照而不是「再 refresh 一次清干净」，因为
  **捕获分不出「authored 隐藏后被显示」和「author-ed 可见从没被碰过」**（Phase 67 那条），
  所以只有快照能保证逐位还原。
- 临时 Folder `SSS.__Demo` 用完 `Destroy()`。

### 73.6 没验的

**世界侧的逐段视觉仍然没有** —— E-VENT 真的排气、激光真的打，remake 没做，这一轮也没做。
原版那 ~110 秒里**玩家能看到的只有这块日志面板**（Phase 66/67 从捕获里量到），
所以补上面板 = 补上「**能看到的**开机」；这**不等于**补上了世界侧的逐段效果。
另外 65.8 那张「没做的」表**整张仍然有效**（`s.GameActive` 的 8.65 s 偏移只记录不改、
`MaxCatchupSteps` 可能跳行、`E INITIATED` 的生命周期没管）。

### 73.7 数字

| 量 | 值 |
|---|---|
| 链条数 / hold 之和 | 16 / **113.4 s** |
| 翻 `Running` | t=**114** s after the master switch |
| 逐条比对 | **16/16，mismatches=0**（错位那趟是 13，见 73.3） |
| 面板行数 / 内容 | **4**，最新四条，3 红 + 1 青 |
| `BootSeconds` / reveals | **14 s** / **7** |
| 开机屏 T | `Ready` at t=**14** |
| 跳闸（`BootFrame` 载体） | **3 / 7** 台控制室监视器 |
| 世界残留 | **0**（两个快照都逐位还原） |

## Phase 74（2026-10-02）—— 「为啥机房这么容易坏掉」

> 你的原话：**「为啥机房这么容易坏掉」**

问的是**原版**，不是 remake。定住这条的不是我的猜测，是你自己 2026-09-26 那句
`D9:"MainframeMeltdown"是机房熔毁又不是核心熔毁`（`QUESTIONS.md` D9）——
「机房」= `s.MainframeMeltdown`，而它今天仍然是 `_tools/TRG_original_recorder.luau`
第 2284 行那条封存判据。所以这一轮是**去产物里把它的规格挖出来**，不是改代码。
（顺带核对：`MainframeMeltdown` 在这次会话里被确认**只存在于原版** ——
`rblx_script_grep` 在 AIRemake 全 DataModel 里零命中。）

### 74.1 规格不用猜 —— 原版把说明书放进了世界里，而我们的产物抓到了它

`Workspace.Consoles.ElectricGridConsole.DRMScreen.SurfaceGui.MainFrame.MainframeFrame.OperationsFrame.TextLabel`
就是 Digital Reactor Manual 的 MAINFRAME 段，flow 产物按 `EVT<n> TEXT <path> <文本>`
逐条记了下来（`Data/flow/original_261002-140019` 与 `…261001-125206` 两趟**逐字相同**）。

**逐字抄在下面。** 理由不是好看：`Data/` 是 gitignored，
**不抄进仓库就等于这一趟没抓过**，而下一个人会去重新抓一遍同样的东西。

> Overview - The 'Tesseract' **Quantum Mainframe** is the world's most powerful Quantum
> Supercomputer, responsible for **maintaining** extremely complex machinery such as the:
> **CBLs, Reactor Console Command Interface, Gateway Transporters, Medical Dispensers,** and more.
>
> Majority of its computational operations are controlled by **QPUs**, which have a tendency to
> **degrade**, especially in unfavorable environmental conditions or overclocking scenarios.
>
> When a **QPU fails completely,** it will cause connected systems to reconnect and adjust their
> operations to the remaining QPUs which often results in **devices enacting a soft-reboot protocol**
> or in the case of the **control room monitors, experience a blue visual distortion.**
>
> To **replace a QPU**, operators will first have to disconnect any remaining connections it has to
> the mainframe. This can be done by **disabling any red indicators on a QPU receptacle.** Once the
> **old QPU** is **extracted**, a **new one** can be **inserted**, and integration will happen automatically.
>
> Additionally, components of the **mainframe may catch on fire** from reactor operation. It's advised
> that when operators are preparing to replace a QPU, they **equip a fire extinguisher.** Excessive
> **fires** may raise the mainframe temperature and **cause QPUs to degrade at a much faster rate.**
>
> TLDR: If all QPUs degrade fully, the gateway transporters will remain offline until one is replaced.
> Be aware of mainframe fires, as if theres enough, they can trigger a mainframe meltdown which will
> cause QPUs to degrade faster.
>
> **Gateway Transporters, Medical dispensers, and especially the control room consoles will be
> non-functional** if there are too few QPUs or the mainframe completely shuts down.
>
> Large stockpiles of QPUs tend to be counterintuitive, so operators **may have to use a Synthesiser
> Unit** in order to sucessfully replace dying QPUs. Be weary that the mainframe is always kept at
> extremely low temperatures, and as such haste is of the essence. **{wip system}**
>
> Operators are required to **replace** the affected QPU **as soon as possible**, otherwise machines
> across the facility will begin to shut off in order to conserve resources.

（`<b>` 是原样存在的 markup，上面把标签去掉了、粗体留下；原文里的拼写错误
—— `sucessfully`、`inferference`、`weary` —— **一个没改**，因为它们是这段文本的身份。）

### 74.2 「容易」不是手感，是四条机制叠出来的

1. **它是按 uptime 计的磨损，不是故障。** 「QPUs … have a tendency to **degrade**, especially
   in … **overclocking** scenarios」。Tesseract 是全设施唯一一台，要算 CBL + 控制台 +
   传送门 + 医疗机 —— **它天生就在超频**。你什么都不做它也在掉。
2. **火灾是唯一的加速器。** 「components of the mainframe **may catch on fire from reactor
   operation**」，而火 **cause QPUs to degrade at a much faster rate**。所以机房里的火
   不是布景；原版自己建议你**带着灭火器去换 QPU**。
3. **Shift 1 豁免。** 维基 `Central Mainframe` 页：QPU「will not degrade whatsoever on Shift 1」，
   而 Mainframe Meltdowns「usually occur at the **middle and end of Shift 2** due to
   **prolonged reactor operation time**」。**教学班不折磨你** —— 所以你第一次看见它，
   大概就是 Shift 2 中段。
4. **它是配额，不是故障。** 6 个 QPU →「you can only have **six QPU meltdowns** before
   control room functions cease to work」。前五次是**提示**（监视器蓝屏 / 软重启），
   第六次才真的瘫，而且要**换 QPU 才恢复**（「permanent until a QPU is replaced」）。

**加一条不是机制的机制**：那段说明自己盖着 **`{wip system}`** 的章。
原版这个系统**本来就没做完** —— 所以「怎么老坏」有一部分答案是：它现在只有坏这一半。

### 74.3 我们自己的产物怎么说（实测，不是转述）

11 趟可用的 `Data/flow/original_*` 里，**只有 2 趟**真的抓到了旗标翻起：

| 趟 | 翻起 | 那一刻的温度 | 同一拍还写了什么 |
|---|---|---|---|
| `original_260926-183529` | `t=719.86` s（`dt=386`） | —— | 三台监视器的 `ErrorFrame.Frame.InfoLabel=3` |
| `original_260926-230049` | `t=868.94` s（`dt=296`） | **7978 °F** | `…DisplayMonitor…ReactorMonitoring.ErrorFrame…=3`、`Screen.CBLMonitoring…=3`，随后 `SEAL machine room meltdown` |

两条意思：

- **它落在开机后 ~12–14.5 分钟**，而那时温度只有 **7978 °F** —— 离核心熔毁那条
  `MeltdownF=39000` 差了**五倍**。所以「机房熔毁」根本**不是**「堆芯要炸了」，
  这正是 D9 当初要拆开的那两件事，这次由产物第二次确认。
- **它在全设施监视器上同时出现**（`MonitorsFacility.DisplayMonitor` 也在列），
  不是只有控制室。这与 74.1 那段「machines across the facility will begin to shut off
  in order to conserve resources」对得上。

### 74.4 屏幕上你会看到的那两句话（逐字，每台监视器各一份）

```
x.Screen.<任何一台>.GlitchFrame.Frame.Frame.TextLabel
  MAINFRAME CONNECTION OVERLOAD
  An unknown error in the mainframe is causing this device to experience electronic
  inferference. This could be due to failing computational systems. Please contact
  IT Personnel if this issue persist.

x.Screen.<任何一台>.DisconnectFrame.Frame.Frame.TextLabel
  OPERATOR ERROR                     ← 标题
  To resolve this issue, please make sure the proper mainframe data connection is
  working / active. If problems persist, please contact System Maintenance Personnel.
```

这两段在**主控室 7 台和 `MonitorsFacility` 里那几台上一模一样**，
所以「机房一打喷嚏，全设施的屏幕一起花」这件事在产物里是**可数的**，不是印象。

### 74.5 remake 这边：机房不是「容易坏」，是**根本没装**

| | 原版 | remake |
|---|---|---|
| 旗标 | `MainframeMeltdown`（BoolValue，住在 `Workspace.Stats` 下） | **不存在**（全 DataModel `rblx_script_grep` 零命中） |
| QPU 数 | 会掉，掉满 6 次控制室瘫 | `StateBridge` 第 57 行：`set(stats,'ActiveQPUs',6)` —— **写死的 6** |
| 机房几何 | `QuantumMainframe`（6,071 件） | `Mainframe`(17,078) + `QuantumMainframe`(6,071)，**只有皮** |

**`ActiveQPUs` 这条值得单说**：remake 把原版的那个**槽位**照着搭出来了
（名字对、类型对、写进 `Workspace.Stats`），然后**焊死在 6**。
也就是说，将来要接这条机制，接的口子在，缺的只是**写入者** ——
和 `engine.events` 在 Phase 65 之前「只写不读」是**同一类洞的另一半**。

### 74.6 没验的 / 不替你决定的

- **没验**：原版 QPU 降解的**速率**（每 QPU 多少秒掉一格）、火灾对速率的**倍率**、
  6 次里每次的间隔。产物里那两个时刻是**旗标翻起**，不是「第一个 QPU 掉了」。
  要量速率得直接读 Tesseract 上的 QPU receptacle 指示灯，而我们的产物**没有对准它**。
- **不去动**：remake 要不要把这条机制做出来，是**玩法决策**（CLAUDE.md §1.4 第一条：
  NEVER CHANGE EXISTING GAMEPLAY MECHANICS）。所以这条变成 `QUESTIONS.md` 的 **P10**，
  **我没有替你做**。

---

## Phase 75（2026-10-03）—— Rebuild 的第一刀：腔室从 AIRemake 搬过来，并**摆回原版的世界坐标**

**两个新 place**：`The Reactor : AIRemake`（placeId `83752844701736`，Workspace 999 个子物体）
是**参照**；`The Reactor [Rebuild]`（placeId `131274481205639`）是**新主场，从零重做整个游戏**。
用户要的第一刀是**堆芯本体（中轴那一摞）**，且**几何必须一致**（尺寸 / 位置 / 层次）。

### 75.1 三个通道，只有第三个能真正高亮

| 通道 | 结果 | 结论 |
|---|---|---|
| 官方 `rblx_execute_luau`（`Edit`）+ `Selection:Set(want)` | 回 `ok=true n=3`，**用户屏幕没有任何反应** | 沙箱 VM 有它**自己**的 `Selection`，动不了真 UI |
| 第三方 `mcp__robloxstudio__selection`（`action=set`） | `{"error":"Unknown endpoint: /api/set-selection"}` | 这条路由**在装着的插件版本里根本没实现** —— 工具在，后端不在 |
| 第三方 `mcp__robloxstudio__execute_luau`（插件 VM）+ `Selection:Set` | 回 `ok=true n=3`，**用户看到高亮，回「好了」** | 插件 VM 是**真插件**，它的 `Selection` 就是实时 UI 那一份 |

**规矩**：要让用户「看到」，走**第三方 `execute_luau`**；官方那条只用来读写实例属性。
同 §0.17 的精神 —— 两条通道各管一半，一条的失败是关于那一条的，不是关于代码的。

### 75.2 第一刀搬了什么

AIRemake 里 `Workspace` 的**前三个容器**，全部在顶层、路径唯一：

| 容器 | 部件 | 是什么 |
|---|---|---|
| `ChamberWalls` | 2267 | **腔室房间壳**（29 个子模型：墙本体 265、`DetailSegment1/2` 各 323、两扇 `Door`、`MASSRail1/2` 导轨…） |
| `Core` | 21 | **堆芯本体** —— 一个 9³ 的 `CORE` 部件 + 6 个特效件（`EFEParticlePart` 150³ 等） |
| `PowerExtractionAssembly` | 1921 | 中轴的**功率提取总成**（93 个子件：`PEABottom` 349、`CentralPlating` 210…） |

**腔室的空间范围**（原版）：`x −120..121 / y −67..495 / z −118..117`，中心 `(0.569, 214.083, −0.107)`。

顺便记清楚**没搬的邻居**（下一刀会用到）：`ReactorCBLs`（3 台 `Reactor_Laser_Mk3`，8291）、
`METU`（1612，在正上方）、`RCBlastDoor`、`GravGate`、两条 catwalk、`ChamberCoolantPipe1/2/3`、
`Lights.ChamberLights`、`Alarms.ReactorChamber`。`Consoles` / `Monitors` 在 `x≈110` 那一侧，
是**控制室**、不是腔室。

### 75.3 怎么证明搬对了：指纹 + 精度阶梯

**件数对得上不算验过** —— 「件数相同、件不同」是最难认的一种错。两把尺子：

1. **逐件指纹**：每个 `BasePart` 取 `名称|类别|尺寸|朝向|材质|颜色|透明度|MeshId|子件数`，
   排序后滚动哈希。抓「件数一样、件不一样」。
2. **相对位置指纹**：各件减去该容器**质心**之后再排序哈希 —— 平移不变，贴进来的偏移自动消掉。
   抓「件一样、摆法不一样」。

**第一版差点误判。** 在固定 `0.01` stud 上取整时 `PowerExtractionAssembly` 两边**对不上**
（`c9d47b4c…` vs `10913aab…`），而同一时刻 `ChamberWalls` 和 `Core` 连 `0.001` 都一致。
把阈值做成**阶梯**（0.001 → 0.2，共 13 档）才看清：

| 取整步长 | 两边一致？ |
|---|---|
| 0.001 / 0.002 / 0.003 / 0.005 | 否 |
| **0.008** | **是** |
| 0.01 / 0.015 | 否 |
| 0.02 / 0.03 / 0.05 / 0.08 / 0.1 / 0.2 | 是 |

**残差 ≈ 1e-6 stud，是 float32 的账**：Roblox 的部件坐标是 32 位浮点，同一份几何从 `y≈250`
搬到 `y≈50` 之后，同一个真实坐标的**表示**就变了最后几位。`ChamberWalls` / `Core` 能在
`0.001` 上一致，只是因为它们的坐标本来就落在能精确表示的格点上。
**不是几何错，也不是搬运错** —— 但**只有在量了阶梯之后才能这么说**。

### 75.4 摆正：墙早就在原位，堆芯是**另一次**贴进来的

量三个 Model 的 pivot（6 位小数）时发现：`ChamberWalls` 那个 pivot **两边一模一样**
（`(−11.737000, 221.724426, −3.838837)`），而 `Core` / `PEA` 各差同一个
`Δ = (+0.633843, −193.746674, −146.267456)`。**两个独立测点算出的 Δ 一致到 6 位**，
所以不是测量噪声，也不是「同一次粘贴」—— 原来是**两次**。

于是把两件 `PivotTo` 推回 `−Δ`（用 `ChangeHistoryService` 包着，**Ctrl+Z 可撤销**）。
摆正后逐位核对：

| 容器 | AIRemake 包围盒 min → max | Rebuild 摆正后 |
|---|---|---|
| `ChamberWalls` | `−120.022,−67.313,−117.506 → 121.161,495.479,117.293` | **逐位相同** |
| `Core` | `−99.110,205.612,−92.114 → 84.990,355.612,95.048` | **逐位相同** |
| `PowerExtractionAssembly` | `−65.294,219.349,−47.949 → 32.132,286.021,46.833` | **逐位相同** |

`Core` 的 pivot 也从 `(−9.241157, 86.865326, −146.870224)` 落到
`(−9.875000, 280.611600, −0.602770)`，原版是 `(−9.875000, 280.612000, −0.602770)`。

**所以 Rebuild 现在和原版共用一套世界坐标** —— 以后继续搬别的件，用同一次贴法就会自动对齐。
取舍 **251** / **252**。

### 75.5 没做的事

- **没搬** `ReactorCBLs` / `METU` / 腔壁细节 / 冷却管 / 两个 catwalk —— 下一刀。
- **没定** Rebuild 的 `Baseplate`（`2048×16`，顶面 `y=0`）怎么办：腔室往下到 `y=−67.3`，
  底下 67 个 stud 埋在板里。原版那边是 `Terrain`（`2044×252×2044 @ (0,0,0)`）盖住同一段。
  Baseplate 是**世界的一部分**、不是我的，**先问再动**。
- **没删** Rebuild 里的残留：`__incoming`（空）、`__XFER_IN`（空）、`Test`（一张**完全透明**的
  Neon 板 + 一个 `Script`）、3 个 `Union`、`Folder`（18 根 21.1 长的金属条，绕 `(−12, 11.3, −85)`
  围成半径约 60 的环）。**来源没查清之前不删**（§1.4 第二条）。

---

## Phase 76（2026-10-03）—— Rebuild 腔室第二刀：**尺子先修，再重做堆芯那一摞**

> 这一 Phase 里所有数字都是**读实例**得到的（§0.2），量的是 `Workspace.RebuildColumn_v2`
> 和 AIRemake 的 `Workspace.PowerExtractionAssembly`。Rebuild 的 placeId 是
> **131274481205639**（本轮第一次记下来）。

### 76.1 **先更正 §75.4：那两个包围盒是用错方法算的**

§75.4 那张「三件包围盒逐位相同」的表，三个数都是按
`min = CFrame.Position − Size*0.5` / `max = CFrame.Position + Size*0.5` 算的。
**这个算法对旋转过的件是错的** —— `Size` 是**局部轴**上的尺寸，不是世界轴上的。

最干净的例子是 `PowerExtractionAssembly.ThermalOutline`：它的 `Size` 是
`8.4 × 39.6 × 39.6`，而它**平躺着**（局部 X 竖直、8.4 就是厚度）。
naive 法把它的局部 Y 当成世界 Y，于是凭空造出一个 **39.6 高**的圆柱，
把整个 PEA 的顶从 **y 270.4** 抬到 **y 286.0** —— 虚高 **15.6 stud**。

正确的有向包围盒（OBB）逐轴取三个基向量在世界轴上的投影：

```lua
local cf, s = d.CFrame, d.Size
local R, U, L = cf.RightVector, cf.UpVector, cf.LookVector
local ex = math.abs(R.X)*s.X + math.abs(U.X)*s.Y + math.abs(L.X)*s.Z
local ey = math.abs(R.Y)*s.X + math.abs(U.Y)*s.Y + math.abs(L.Y)*s.Z
local ez = math.abs(R.Z)*s.X + math.abs(U.Z)*s.Y + math.abs(L.Z)*s.Z
local p = cf.Position
local mn = Vector3.new(p.X-ex/2, p.Y-ey/2, p.Z-ez/2)
local mx = Vector3.new(p.X+ex/2, p.Y+ey/2, p.Z+ez/2)
```

**两条仍然成立、两条要改**：

- 仍然成立：「逐位相同」作为**比较**是有效的 —— 同一个错方法量两个 place，
  两边一起错，差仍然为 0。搬运本身没问题。
- 仍然成立：`ChamberWalls` / `Core` 在 0.001 就对上（取舍 252 的解释不受影响）。
- **要改**：§75.4 那张表里的**数字不是包围盒**，是「局部尺寸直接加减」的量。
  不要拿它们当尺寸用。
- **要改**：我第一次建 `RebuildColumn_v1` 就是照这把虚高的尺子建的，
  **高了 16 stud**（建到 y 286.4）。这就是本轮返工的原因。取舍 **253**。

### 76.2 原版 `PowerExtractionAssembly` 的真实分层（OBB 重量）

按直接子物体分组，每组的 OBB / 件数 / 世界 y：

| 家族 | 件数 | y | 直径 / 跨度 | 是什么 |
|---|---|---|---|---|
| `PEAModule` ×3 | **557** | 216.4–246.9 | 90.9 × 98.1 | **三座宽舱段，占了大半**（不是三根细柱） |
| `PEABottom` | 349 | 231.8–**237.2** | 38.5 | **只有 5.4 高的薄盘** |
| `PEAHexagon` ×36 | 36 | 228.0–231.8 | 85.3 × 93.5 | 一圈六角砖，比舱段**小**、在里侧 |
| `PEAUpperBottom` | 18 | 237.1–245.6 | 38.5 | 第二段盘 |
| `CentralPlating` | 210 | 246.8–261.3 | 37.2 | 中心镀层筒 |
| `PhotoVoltaicRing` ×38 | **702** | 246.6–269.9 | 39.0 | **23.4 高的带**（不是一圈薄板） |
| `Frame` ×3 | 30 | 262.4–267.2 | 38.5 | 三道环 |
| `PEAVent` | 10 | 263.9–265.7 | 38.5 | 排气盘 |
| `ThermalOutline` | 1 | 262.0–270.4 | 39.6 | **平躺的 8.4 厚圆盘**（顶就是它） |
| `Pipe` | 1 | 264.7–268.7 | 24.0 | 中心管 |
| `CentralNeon` | 1 | 265.0–266.9 | 13.6 | 中心灯 |
| **合计** | **1921** | **216.4 .. 270.4** | **90.9 × 98.1** | 54 高 |

`Core`（21 件，全 `Transparency = 1.00`）是**纯 FX 架**：9³ 的 `CORE` 锚点 +
15 个 `Laser*.BoomPart`（4³ Neon），y 239.8–333.5 —— 它比 PEA 高出去一截，
**所以「堆芯顶」不能拿 `Core` 的包围盒当依据**。

### 76.3 反解：三座舱段是**宽板**不是柱子

拿 ±60° 那座舱段（θ=−60°，径向 u=(0.5,−0.866)、切向 v=(0.866,0.5)）解包围盒：

```
z 最大 |z| = 0.866·R + 0.5·T = 49.05
x 最大     = 0.5·R  + 0.866·T = 43.0
```

解得 **R ≈ 42…44.5（径向）**、**T ≈ 22…25.4（切向半宽）** ——
也就是每座舱段是**大约 50 stud 宽、30 高、26 厚的板**，不是立方体。
`v1` 做成 30×30.5×30 的立方体，这就是它 X 只有 73.8（原版 90.9）的原因。

**这套解在 Z 上自相矛盾**（用 R=47.875 反推得 |z|=52.5，而实测 49.05）——
说明原版这三座舱段**不是**「三个全等的径向盒子」，或者分组里混了非径向对称的件。
我没有继续追这个矛盾，取 R=44.5 / T=24.5 折中。取舍 **254**。

### 76.4 `RebuildColumn_v2` 实测 vs 原版

| | v2 | 原版 | 差 |
|---|---|---|---|
| 宽 X | **89.8** | 90.9 | −1.2% |
| 高 Y | **54.1** | 54.0 | +0.2% |
| 深 Z | **101.4** | 98.1 | +3.4% |
| 底 / 顶 y | **216.4 / 270.5** | 216.4 / 270.4 | 对上 |

**258 件**（原版 1921），位置 `(140.125, −0.603)` —— 故意放在被复制的那份**正东 150 stud**，
方便左右对比。材质 `Metal` 142 / `DiamondPlate` 58 / `Neon` 58，9 种颜色。

自下而上六层（局部 X = 径向外、Z = 切向、Y = 竖直）：

1. **三座宽舱段**（120°，中心 r=30）：主体 25×30.5×44（径向 16–41）、外板 3.5×26×36
   （到 r 44.5）、上下盖 30×2×47、两条 `DiamondPlate` 束带、7 片竖鳍、2 条铁锈色管、
   5 根螺栓、2 条橙 `Neon`。
2. **36 片六角砖**（r 40，y 229.9，斜 12°）。
3. **两段底座法兰盘**：D 38.5，5.4 高 @234.5 / 8.5 高 @241.35，外加 D 42 的两道薄法兰。
4. **中心镀层筒**：D 37.2 × 14.5 @254.05，8 片外鳍 + 16 根螺栓。
5. **38 片光伏板带**：两圈各 19 片（r 17.6 / 19.6），21 高、斜 8°，各带一条橙 Neon 面。
6. **顶**：三道 `Frame` 环（D 38.5）、`PEAVent` 排气盘 + 10 片叶、橙色 `ThermalOutline` 盘
   （D 39.6 × 8.4，**顶就是它**）、中心 `PipeSeg` 环、黑色 `CentralNeon`、`ShaftTopCap`。

### 76.5 两处已知偏差，**没硬凑**

- **Z 深 3.4%**：撑到 Z 极值的是舱段上下盖的切向宽度（47）。
- 想再收 Z 只能缩顶盖切向宽，而顶盖同时是 +X 的极值来源 ——
  **缩了 Z 好、X 坏，两个方案的绝对误差和反而更差**（4.6 → 4.9）。
  所以停在 89.8 / 54.1 / 101.4。取舍 **254**。

### 76.6 没做的

- `ChamberWalls`（2267 件）、`ReactorCBLs`（8291）、`METU`（1612）、腔壁细节、冷却管、
  两个 catwalk —— **下一刀**。
- 被复制的三份原件的**删除**（用户说的是「拷贝当尺子」，尺子用完再拆）。
- Rebuild 里的残留（`Test` / 3 个 `Union` / 18 根金属条 / 两个空 Folder）—— 来源仍没查清。
- Rebuild 的 `Baseplate` 怎么处理 —— 仍然悬着（§75.5）。

---

## Phase 77（2026-10-03）—— Rebuild 腔室第三刀：**整间腔室**重建成 `RebuildChamber`

同样是「先量、再建」，全部数字读实例（§0.2 + §0.18 的 OBB）。原版数据取自 AIRemake 的
`Workspace.ChamberWalls`（官方 studio_id `1c7e2ebb-792b-4d9f-8bfd-e56d4d9c7903`，
placeId `83752844701736`）。

### 77.1 原版 `ChamberWalls` 的真实分层（2267 件 / 19 组）

| 组 | 件数 | y | 跨度 | 是什么 |
|---|---|---|---|---|
| `Part` | **2002** | 0.1–347.5 | 211.9 × 210.9 | **外壳格栅**（见 77.2） |
| `Wedge` | 118 | 259.9–310.3 | 210.9 × 205.5 | 顶部倒角圈 |
| `LowerWalls` ×23 | 23 | 203.9–262.7 | 217.8 × 226.4 | 中段加厚环（Union） |
| `Meshes/Circle` ×8 | 8 | 24.1–204.1 | **D 175** | 混凝土内环 |
| `LowerNeon` ×11 | 11 | 0–152.0 | **D 135.6** | 内筒霓虹 |
| `UppgerGravTrigger` | 1 | **351.9–503.4** | D 135.6 | 上半段竖管（比外壳还高 156） |
| `LowerGravTrigger` | 1 | 152.0–164.5 | D 135.6 | 中隔环 |
| `Grass` / `KillNeon` | 1+1 | 0–1 / 27.0 | D 135.6 | 地板 / 击杀面 |
| `Union` / `CautionLines` / `Trapezoid` | 1+2+28 | — | — | 墙面零件 |
| 那 56 件一簇（见 77.3） | 56 | 286.5–294.6 | — | **两条观察窗带** |
| **合计** | **2267** | **0 .. 503.4** | **220.3 × 226.4** | |

**半径直方图**（`Part` 那 2002 件）只有四档：**r≈100 占 1918**、r≈60 占 36、r≈80/90 各 24。
也就是说外壳是一圈**半径 100 的格栅**，不是实心筒。

### 77.2 那 2002 个 `Part` 是「竖肋 + 横带 + 面板」的格栅

尺寸直方图（前几名）：`0.4×0.1×18.3` ×189、`0.1×27.9×0.2` ×160、`0.2×27.9×0.2` ×140、
`0.1×25.4×0.2` ×50、`0.4×27.9×0.2` ×40……全是**零点几 stud 厚的薄板**。
按 27.9 高一段推，347 高大约分 **12 段**。

重建用的是：一张内壳皮 + **72 根通高竖肋** + **12 道横带** + **72×12 片薄面板**，
再加中段 24 片加厚块、60 片 132° 倾斜的倒角板、上下两道法兰环。

### 77.3 【坑】**分组包围盒会把四条分开的东西合成一条不存在的平板**

那一簇 56 件按名字汇总出来是
`MeshPart  sz 106.4 × 8.0 × 205.8  ctr (-51.6, 290.5, -0.7)` ——
**看起来就是一块横穿腔室的 106 × 8 × 206 的平板**，我差点照着它建一块平台。

逐件打出来才发现：它们的 **θ 从 ±88.5° 一路排到 ±153.9°**，也就是
**±Z 两侧各一条 θ 跨度 64° 的弧形观察窗带**（y 287–294），
带金属框 + 玻璃 + 橙 Neon + 铭牌 + 壁灯。
那个 106 × 206 只是**把两条弧带各自的包围盒并起来**的结果 ——
**没有任何一件是这个形状**。取舍 **255**。

**同一条坑的另一面**：`Union` 那件单独量是 `40.9 × 55.5 × 27.8 @ (77.5, 235.0)`，
相对轴心 r ≈ **87.4**。我第一版按「贴着外墙」放在 r=104，多探出去 10 stud，
`x` 一下从 108 变成 118 —— **一个位置读错，包围盒立刻从对称变不对称**，
这就是它报出来的方式。

### 77.4 重建结果 `RebuildChamber`（轴心 `(140.125, −0.603)`）

**1377 件**（原版 2267），八层：

1. **地板 + 内筒**（r 67.8）：Grass 地板、`KillNeon` 面、16 片橙 Neon 内筒板 + 32 根竖肋
   （y 0–152）、24 片 `LowerGravTrigger`（y 152–164.5）、24 片上半竖管（y 352–503.4）
   + 16 根外肋。
2. **混凝土内环**（D 175）：8 圈，y 24–204。**注意它比内筒大、比外壳小** —— 三层是套着的。
3. **外壳格栅**（r ~100）：内壳皮（D 199 通高 347）+ 72 根竖肋 + 12 道横带
   + 864 片薄面板（`Metal` / `DiamondPlate` 交替）。
4. **中段加厚环**（y 203.9–262.7）：24 片 + 上下各 24 根螺栓。
5. **顶部倒角**（r 105 @ y260 → r 60 @ y310）：**60 片 132° 倾斜板**
   （原版用 118 个 `Wedge`，我用倾斜 Box —— 省掉楔形朝向的坑），上下两道法兰环。
6. **外壳上沿**（y 347）：法兰 + 36 根螺栓。
7. **两条观察窗带**（θ 89–152 与 −89–−152，y 287–294）：各 16 格，
   每格 = 框 + 玻璃 + Neon 灯条，第 3/6/10/13 格加铭牌。
8. **墙面零件**：2 条黄色警示带（θ 0/180）、28 片 trapezoid 板（θ 158–202）、
   一个壁箱（r 87.4）。

| | 我建的 | 原版（相对轴心） | 差 |
|---|---|---|---|
| X | 216.0（−108..108） | 220.3（−112.4..107.9） | −2.0% |
| Y | **503.5** | **503.4** | **+0.02%** |
| Z | 216.0（−108..108） | 226.4（−113.3..113.1） | −4.6% |

半径统一取 108，原版在 110–113 之间（且**不对称**）。**没去凑那个不对称** ——
取舍 **254** 同一条：能改善一面的改动如果让总量更差就不是改善；
而且原版那点不对称很可能来自 MeshPart 的自身偏移，不是设计意图。

### 77.5 没做的

- 原版那 2267 件里**独有的 mesh**（`Meshes/Circle` / `Trapezoid` / `TrapizoidCube`）
  我用 `Concrete` 圆柱和 Box **代替**了 —— 形状近似，不是同一批资产。取舍 **256**。
- 被复制的 `ChamberWalls` / `Core` / `PowerExtractionAssembly` **还在** Rebuild 里，
  **没删**（尺子还没用完）。
- `Core`（21 件）**没有重建**：它全 `Transparency = 1.00`，是纯 FX 架，
  没有可见几何可重建。
- 交互点（`ClickPart` / 拉杆 / 监视器）**没搬** —— 那是下一阶段。


### 78. 辐射滤芯 / 擦除器（Scrubber）MK2（2026-10-03）

在空白处新做了一套，**不是**改 `RadiationScrubberMK1`（那块地面格栅是既有资产，§6 里的名字，没碰）。

**位置**：`Workspace.radiation_scrubber_mk2`，世界坐标
x **-68.85..-59.20** / y **0.00..9.10** / z **25.42..33.70**（9.65 x 9.10 x 8.28）。
放在 MK1 格栅（x -57.52..-36.64，z 25.17..34.07）**正西**的空地。
**净距**：离 MK1 西面 **1.68**，离西墙立柱（x -69.05）**0.20**。
**零重叠**（逐件 OBB 求交，对全 DataModel 227 件非地形件跑了一遍，hits = 0）。

**三件套，不是一个柜子**：
1. **`misc/radiation_scrubber_mk2`**（33 件）—— 开放式框架机柜：
   底座 + 4 腿（`Dark taupe` / `Metal`）-> 台（0.9 高）->
   两侧板 + 背板 + 顶 + 底（5.6 高 x 8.0 深）-> **正面完全敞开**（只有 4 根边框条），
   里面就是滤芯。顶上出风管（`Black` / `Metal`，1.0 x 0.8 x 2.0）+ 背面进风格栅。
   西侧面挂**控制面板**（`Institutional white` 面板 + 1 个 `Really black` 旋钮 + 3 个
   `Bright yellow` 指示灯）。
2. **`misc/radiation_filter_cartridge`**（18 件）—— **可抽出的滤芯**：
   外框（`Medium brown` / `Metal`，3.0 x 4.0 x 6.4）+ 内芯（`Institutional white`，
   2.8 x 3.8 x 6.2）+ **10 片横向滤纸**（每片 2.6 x 3.8 x 0.1）。
   两个提耳（`Dark taupe`）。**建在机柜里**，就是「推进去」的状态；
   另外**单独存了一份**在机柜西侧（-70.8，2.0，29.6），是备件。
3. **辐射等级牌**：柜子正面底部一块 **`Medium blue` / `ForceField`** 板
   （6.0 x 0.4 x 0.2）—— 和 MK1 那块 `Grade` 同一手法（ForceField 材质 + 蓝色），
   一眼认出是辐射设备。

**做法**：`generate_build` 程序化生成 -> `import_build` 摆位 ->
**逐件 OBB 实测净距**（§0.18 那把尺子，这次量的是**空隙**不是尺寸）。
第一次摆位偏西 3.10、偏东 3.43（撞墙 / 撞 MK1），靠实测挪了两次到 0.20 / 1.68。
**没有用** `set_property` / `create_object` 逐件建 —— 33 件手敲太容易出错，
而且 `generate_build` 出来的 JSON 就是可复用的资产（`build-library/misc/`）。

**没做的**：没有脚本、没有 `ClickDetector`、没有绑定（§6 —— 这是纯视觉资产）。

## Phase 79 (2026-10-04) - Blender 管道通了，而第一个读数反驳了我自己的说法

用户问「我如何让你能连接到 Blender」。我给了两条路（A 无头脚本 / B blender-mcp），
建议先走 A；用户「ok，按你说的做」→ 本轮做 A。

**环境（实测，同时更正 CLAUDE.md §0.6）**
- Blender 5.1.2 `D:\Blender 5.1\blender.exe`，`--background --python` 可用
- Python 3.14.7 `C:\Python314`，有 pip；**没有** uv / uvx / pipx
- Node.js 其实在 `D:\nodejs`（§0.6 原文那句「NOT FOUND」是错的，已改）
- `ROBLOX_OPEN_CLOUD_API_KEY` / creator id **都没设** -> `upload_asset` 传不了
  fbx，最后一公里得操作员自己拖进 Studio

**管道**：`_tools/blender_chamber_grate.py`，产物落 `D:\BlenderRobloxTestProjects`。
一次吐出 `.glb` / `.fbx` / `.blend` + 两张 Workbench 正交渲染 PNG。

**靶子选了腔室外壳格栅** —— 就是我在对话里说「Blender 一个 revolve + array 就出来了，
不用 2002 个 Part」的那个东西。所以这是一次对我自己论点的检验，不是随便建着玩。

**实测**（脚本自己回读网格，不信构建循环）
- 72 肋 x 12 段 + 13 条环形横带 -> **1 个 mesh**
- bbox `201.79 x 201.79 x 347.00`（z 0.00..347.00）
- **35712 verts / 37440 polys / 67968 tris**，`open_edges = 0`（全是闭合实体）
- 对照：Studio 那版 **2002 个 Part**，每 box 12 tris 约 **24024 tris**

**结论（不粉饰）**
1. **实例数我赢了**：2002 -> 1。Roblox 在乎 draw call，这条是真的。
2. **三角面我输了**：67968 vs ~24024，**2.8 倍**。倒角（bevel）就是代价。
3. **我说「Studio 只能 primitive，所以我只能堆积木」—— 这条是错的。** 我给出去的
   Blender 版里**肋还是 box**，和 Studio 里一模一样的那个 primitive。Blender 让我
   够得到真曲面，我伸手拿了个方块。**媒介不是约束，我是。** 这一轮真正用了媒介的
   只有两处：横带做成真环形（4n 个面，不是 n 个方块）、以及倒角 —— 都真，都不是曲面。
4. **我看不见结果。** 两张 PNG（447 KB / 537 KB —— 不是空白帧，但这只是**文件大小**
   的推断，不是我看过）。剪影好不好只能由操作员判。

**没做的**
- 没走 blender-mcp（路 B）。它的卖点是我「看见视口」，而我看不了图；对我真正有用的
  是**操作员开着 Blender 当我的眼睛**，那条等需要时再装。
- 肋的截面还是矩形，没做面片级。
- **没量 Blender 单位 -> stud 的换算**（glTF 米制 / FBX 自己的约定 / Roblox 导入系数）。
  脚本头部已写明「不要假设 1.0，导入一次读 MeshPart.Size 把系数告诉我」。

## Phase 80 (2026-10-04) - RadiationScrubberUnit：按我自己的想法做的第一个东西

用户给了三件：① 报回尺寸 `1190.965, 2048, 1190.966`；② 「卡顿优化太明显了，完全没有
丝毫卡顿」；③ 「你做个 RadiationScrubberUnit 我看看（按照你自己的理解）」+「blender-mcp 整上」。

### 80.1 5.902 与那个 2048

比值三个轴一致 = **5.902**，纯缩放没换轴。**2048 是 Roblox 单件上限，而
`347 x 5.902 = 2047.99` —— 我的外壳卡在上限上差 0.01**，再高一点读回来就是夹过的数，
而夹过的尺寸看不出是夹过的。已钉进 `trg.py:STUDS_PER_UNIT`，取舍 **258**。

### 80.2 「完全没有丝毫卡顿」是这轮最硬的证据

2002 Part → 1 mesh，tri 数涨了 2.8 倍，而**不卡了**。这条把瓶颈钉在 **draw call**
不在面数上，而且它是**操作员在游戏里看到的**，不是我推的。比我任何推理都值钱。

### 80.3 blender-mcp 接上了

- addon（`ahujasid/blender-mcp`，用户点名）在 **Blender 5.1 上 `REGISTER_OK`**
  —— 这是之前唯一的未知（它 `bl_info` 写的最低 3.0）。已装进
  `%APPDATA%\Blender Foundation\Blender\5.1\scripts\addons\addon.py`
- server：`pip install blender-mcp`（这台没有 uv）→
  `C:\Users\andypeng1NB\AppData\Roaming\Python\Python314\Scripts\blender-mcp.exe`
- 已 `claude mcp add blender` 进 `~/.claude.json`（project scope）。
  **要用还得两步**：Blender 里勾上 addon + `N` 面板 Connect（起 9876），
  以及**重启这个 Claude 会话**。
- 走这条路的**真实理由**不是「我能看视口」（我看不了图），是**操作员开着 Blender
  当我的眼睛** —— 我跑一段代码，他看，他说「太胖了」。那是我唯一缺的仪器。

### 80.4 新增 `_tools/blender/trg.py`（共用库）

`revolve`（任意母线车削，r=0 的点收成极点所以封头是封头不是截断的筒）、
`sweep_arc`（弯管）、`tube`（任意方向直管，**故意不用 `create_cone`** ——
它的 radius 参数名在 Blender 版本间改过，而**半径错了不报错，只给你一个显得很像故意的形状**）、
`panel_arc`（弧形板：平面 box 贴在 r=2.62 的筒上，边缘会差四分之一 stud，看得见）、
`finish`（**只倒角真正是角的边** —— 按 face angle 过滤。第一版对 64 边圆柱的每条边都倒，
那是把面数花在没有角的地方）、`measure`、`export`、`render`。

### 80.5 我做的东西

`_tools/blender/radiation_scrubber.py`。**设计理由全部写在文件头**（是设计，不是测量）。
要点：立式压力容器而不是框架柜（净化器本来就是个容器）；中段**带螺栓圈的法兰**是
唯一一个机制手势（说明「这里能开，滤芯在里面」）；排气走**真弯管**；**不对称**
（+Y 进气 / -Y 操作面 / +X 排气）；面板是**弧形板**不是贴上去的平盒子。

**实测** `6.92 x 6.60 x 9.67`（z -0.02..9.65），**5550 verts / 5500 polys / 10956 tris**，
`open_edges = 0`。三视图 + iso 在 `D:\BlenderRobloxTestProjects\RadiationScrubberUnit_*.png`。

**对面数的读数**：scrubber 的形状比 ChamberGrate 复杂得多，tris 只有它的**六分之一**。
**曲面是更便宜的表示，不是更贵的** —— 这条否掉了我自己前面的推理，取舍 **259**。

### 80.6 我自己的评价（看不到，所以这是预测不是结论）

**我认为好的是**：母线一次车出来所以全身无接缝；中段螺栓圈是唯一一个机制手势，
没有被稀释。
**我怀疑弱的是**：剪影大概很平 —— 一个带封头的圆筒加一根管子；5 条一样的格栅条
是我「循环」的本能不是设计；三个灯排一排是最没有想象力的一种解法；比例是我**选**的
不是**配**的。预测对了还是错了，得看三张 PNG。

### 没做的
- 没量 glb 那条路的换算（只量了 FBX）。`expected_studio_size` 那行是 FBX 的假设。
- 没真的**看**那三张渲染（292 / 316 / 284 KB，从大小推不是空白，但这是推断）。
- `D:\_tmp_bmcp\addon.py` 那份临时副本还在原地没删（安装失败时的备选）。

## Phase 81 (2026-10-04) — LaserPort：一对端口（一个发射 / 一个接收）+ 交接夹整理

用户原话：**「帮我做一个那种激光端口你能理解吧，一个发射，一个接收，还有
D:\BlenderRobloxTestProjects\整理一下」**。

### 81.1 坐标系是整个设计的起点，所以先说它

两个头都是**沿 +X 出光**的墙挂件，安装板在 x ∈ [-0.22, 0]，墙在 x = -0.22。
这样**一对端口的摆法就是「把两块板贴到面对面的两堵墙上」**：接收端放到
`(GAP, y, z)` 再绕 Z 转 180°，两个口就对着看了。**光束不进 mesh** ——
它得随操作员定的间距伸缩，mesh 做不到（除非被缩放），所以游戏里它是一根 Part，
渲染里的那根只存在于渲染里。

为了让这件事成立，先把 `trg.revolve` / `trg.cylinder` 加了 `axis` 参数。**不是**
「绕 Z 建好再旋转 mesh」—— 那样会静默地换掉「哪个局部轴朝上」，不报错，只是东西躺着或
倒着，而**倒着要等导入之后才看得出来**。母线沿哪根轴走，就在哪根轴上建。

### 81.2 设计：共用底座 + 只换头（这是「看得出是一对」的唯一手段）

结构部分由**同一个函数**建：安装板 / 四颗螺栓 / 台阶式轮毂 / 两条轭臂 /
一根枢轴销 + 两个销盖。**没有标签可读，所以「像一对」只能靠共用的东西。**

底座里每一条都互相咬合，改一个就会露馅：`HEAD_R = 0.47` 必须**小于**轭臂内侧面
`0.49`（头才嵌得进去）；发光灯画在**安装板正面**而**不是轮毂顶** —— 轮毂顶会和轭臂
撞（臂占 |z| ∈ [0.49, 0.71]、x ∈ [0.40, 1.20]、|y| ≤ 0.16）；两条冷却管走 **+Y/-Y**
两条道，因为那是轭臂唯一没占的两个方向。

**只有头不一样，而两只头都几乎一样长** —— 发射端明显比接收端长会读成**失误**，
不会读成**区别**：

| | 头 | 口 |
|---|---|---|
| 发射 | 5 片散热齿 | 外扩罩 + **内凹**碟，透镜在罩**里面**（口齐平的透镜读成「洞」，内凹的才读成「源」） |
| 接收 | 3 片散热齿 | 大喇叭口；**喇叭的内壁是这条母线的一部分**（母线折返），所以口是真锥面，不是粘上去的盘 |

散热齿是**母线里的方齿**，不是一片片单独的盘 —— 同样的剪影，面数少得多，一整块连续
曲面，没有「盘和筒相接」的那条缝。

材料 6 种，两端共用同一张表：`PortMount / PortBody / PortDark / PortCoolant /
PortLensEmit（橙，自发光）/ PortLensRecv（绿，自发光）`。

### 81.3 实测（不是构建循环里那几个数，是从 mesh 读回来的）

```
LaserEmitterPort   size=2.38 x 1.88 x 1.96   x=-0.22..2.16
                   verts=4611 polys=4537 tris=9134  open_edges=0
LaserReceiverPort  size=2.14 x 1.88 x 1.96   x=-0.22..1.92
                   verts=3620 polys=3530 tris=7148  open_edges=0
```

`open_edges = 0` 两边都是 —— 闭合的实体，不是一圈圈立着的壳。
尺寸和建之前估的 2.38 对上了；接收端我估 2.08、实际 **1.92**，差在传感器凸台的位置，
**是我估错了，不是量错了**。

**这里有一条读法上的坑**：`trg.measure()` 只报 z。两只头**沿 X 不同**，
所以只看尺寸根本分不出谁是谁 —— 给读回的报告补了 x / y 两个区间，
这不是装饰，是让这行数字能回答「这是哪一个」。

### 81.4 `trg.py` 这一轮加的（都是为了上面这件事）

1. `_AXES` + `revolve(..., axis=)`，`cylinder` 跟着透传。已验证 `axis="Z"` 的默认
   输出和改之前**逐位相同**（`c + w*t + u*r·cos + v*r·sin` 展开就是原来的 `(cx + r cos,
   cy + r sin, t)`）。
2. `export(objs, ...)` 现在**接一个对象或一张表**，显式 `select_set` + `use_selection=True`。
   向后兼容：`radiation_scrubber.py` 那行调用一个字没改。

### 81.5 交接夹整理（用户明确要求的第二件事）

```
D:\BlenderRobloxTestProjects\
  ChamberGrate\            (fbx glb blend blend1 2 张渲染)
  RadiationScrubberUnit\   (fbx glb blend 3 张渲染)
  LaserPort\               (两个模型各 fbx/glb/blend + 渲染 4 张)
  README.md                (新)
  DMR.blend DMR.fbx  Ball.obj Ball.mtl  Part1_diff.png Part1_nmap.png
  NeonBox.fbx  Test1.fbx  From_RBLX\        <- 操作员自己的，一个都没动
```

**只搬我自己生成的。** 他那份留在根目录**是有理由的**：`DMR.blend` 可能按**相对路径**
引用 `Part1_diff.png` / `Part1_nmap.png`，搬走有把它弄断的风险，而那是**他的**文件。
`From_RBLX\` 是空的，没动。三个脚本的 `OUT_DIR` 都已改成对应子目录。

### 81.6 顺手量到的一件事：ChamberGrate 的 fbx/glb **大了 5.9 倍**

Phase 79 那份是**在没有 `global_scale` 的情况下导出的**（当时换算比还不知道），
所以它按 5.902 studs/单位导入，横向落到 **1191 stud**，而高度**正好压到 Roblox
2048 的单件上限**上（347 × 5.902 = 2047.99）。它本来是给一个 200 stud 的腔室外壳做的。
**重跑一遍脚本**就得到正确尺寸的一份；新做的两个是 1/5.902 导出的，是对的。
已写进 `README.md`。

### 没做的
- **没量 glb 那条路的换算** —— 只量过 FBX（还是通过 ChamberGrate 间接量的）。
  `expected_studio_size` 那行是 FBX 的假设，glb 的假设**至今没有检验器**。
- **没看到那 4 张渲染**。文件是 320 / 336 / 184 / 154 KB，从大小推不是空白，
  **但这是推断**。剪影好不好看是操作员的判断，不是我的（同 Phase 80 的界线）。
- **没进 Studio**。两个 mesh 都没导入过，`2.38 x 1.88 x 1.96` 是 Blender 单位下的
  读数，Studio 里应该是同一个数 —— **这条是可检验的预测，不是已验证的事实**。

## Phase 82 (2026-10-04) — LaserPort 重做成**可转向**的（像摄像头那样的云台）

用户原话：**「我希望是那种可以像摄像头那样动的激光发射、接收端口，现在这个版本只能往一个方向」**。
这是对 Phase 81 那次交付的更正，不是新需求。

### 82.1 上一版动不了，原因有**两层**，而且第二层才是关键

我把抱怨当成一个线索查下去，得到两条：

1. **一个 mesh 是刚体。** Roblox 的 MeshPart 里没有任何一部分能单独转 —— 想把整个头
   （散热齿 + 罩 + 透镜）做成一个 mesh，就等于宣布它永远朝一个方向。
2. **而且那个「关节」是错的关节。** 上一版的销**沿 Z（竖直）**，穿过**从上、下夹着头**
   的两条臂。竖销 + 上下臂（屋顶和地板用一根柱子连起来）那是个 **pan（水平旋转）**关节 ——
   头却是**焊在轭上**的，所以那根销什么都没瞄。**tilt（俯仰）根本不存在。**

第 2 条比第 1 条重要：只把它切成三块而不动那根销，会得到「能水平转、永远不能俯仰」的
一个东西 —— **看起来改过了，还是只能朝一个方向上下**。

### 82.2 三个刚体，每件的**原点就落在它自己的转轴上**

```
LaserPortBase    不动       原点在安装板中心      1.30 x 1.60 x 1.60   tris=1840  open_edges=0
LaserPortYoke    pan        原点在 pan 轴        0.68 x 1.98 x 0.93   tris=1168  open_edges=0
Laser...Head     tilt       原点在俯仰销         1.72/1.54 x 1.36/1.54 x 1.36/1.54  tris=6842/4856
```

**关节不在代码里，在 mesh 的局部坐标系里。** 件绕**自己的原点**转，所以把原点建在轴上
就是在建关节。发射端整组 `2.14 x 1.98 x 2.34`。

改法上还有一条：**冷却管不能跨关节**。管子是硬的，跨着关节转一次就撕开。所以现在每段管子
都**整个待在一个刚体内部**（底座接头 → 隐藏走线 → 头自己的耳轴），而不是从底座一直连到头。

### 82.3 同一对转轴，**两套坐标系，两个名字**（我在这上面栽了一次）

| | Blender 里 | 导入 Studio 后 |
|---|---|---|
| pan | 绕 **Z** | 绕 local **Y** |
| tilt | 绕 **Y** | 绕 local **Z** |

FBX 导入把 Blender 的 Z 映射成 Studio 的 Y、Blender 的 Y 映射成 Studio 的 Z。所以脚本里
`aim()` 写的是 `Rotation(pan, "Z")` / `Rotation(tilt, "Y")`，而**打给操作员的那行 SUMMARY
写的是「pan 绕 local Y、tilt 绕 local Z」** —— 差的那一下**是映射，不是不一致**。两边都没改，
各标各的坐标系，因为混起来正好会得到「pan 绕 Y」这种**在对的机器上用错的轴**的说明。
上一版 SUMMARY 那行没写坐标系，是这一轮补的。

### 82.4 这一轮第一次**把交付的文件读回来**（`_tools/blender/laser_port_check.py`）

构建循环不是证据（同 §0.2：读实例、不读模块）。所以新写了一个往返检查：把**两个 FBX
重新导入**，逐件读原点、尺寸、tris，然后**摆姿态再读一次**。

```
FILE LaserEmitterPort  nodes=3  (LaserEmitterHead, LaserPortBase, LaserPortYoke)
  LaserEmitterHead   origin_studs=(0.660, 0.000, 0.860)  size=1.72 x 1.36 x 1.36  tris=6842
  LaserPortBase      origin_studs=(0.000, 0.000, 0.000)  size=1.30 x 1.60 x 1.60  tris=1840
  LaserPortYoke      origin_studs=(0.660, 0.000, 0.120)  size=0.68 x 1.98 x 0.93  tris=1168
  origin_gap_vs_design  base 0.0000 / yoke 0.0000 / head 0.0000  studs   OK
```

**三件的原点与设计值差 0.0000** —— 导出**没有**把变换烘进几何体，关节活下来了。尺寸和 tris
与构建时打印的那份**逐位相同**。这个数字重要，因为**烘焙过的原点在 Blender 里看不出来**：
件摆得完全正确，只是永远动不了。

摆姿态分**两段**验，因为两个关节的不变量不一样 —— tilt 的销**会被 pan 带走**：

```
tilt: rot_vs_Ry(tilt) err=0.000000 OK | muzzle (1.920,0.662,0.860) -> (1.802,0.662,0.328)
      dist_to_pin_XZ 1.2600 -> 1.2600 OK
pan:  rot_vs_Rz(pan)*Ry(tilt) err=0.000000 OK | muzzle -> (1.109,1.241,0.328)
      dist_to_pan_axis_XY 1.3199 -> 1.3199 OK
muzzle swung 1.130 studs total
```

**一次「失败」其实是对的设计**：**pan 不让头的原点移动**。两个轴**都在同一条竖直线上**
（只在 Z 上差 0.74），所以 pan 绕它转，原点原地不动 —— 我一开始把这当成缺陷。**该动的是
枪口，不是原点**，所以检查改成跟踪**一个顶点**（枪口环上 x 最大的那个）。
`1.2600 -> 1.2600`（到销的距离）和 `1.3199 -> 1.3199`（到 pan 轴的距离）是**刚性**的证据。

**两个自打脸的错，都是尺子错**（同 §0.18 那一类，记录在案免得下次重犯）：

1. **studs vs 文件单位**：FBX 是按 `global_scale = 1/5.902` 导出的，**文件里存的是
   studs/5.902**。把「以 studs 写的设计值」和「以文件单位读回来的平移」直接相减，报了
   **5.3141 studs 的误差**，而那两个件**其实是精确的**。错的量法不报错，它只安静地给一个数。
2. **不变量测在错的平面上**：绕一条轴旋转，保距要在**垂直于那条轴**的平面里量（pan 是
   Blender Z → XY 面；tilt 是 Blender Y → XZ 面）；而且 tilt 的不变量只能在 **pan 之前**量，
   因为销自己会被 pan 转走。三条都错会合起来报一次「NOT RIGID」。
   最后一条尤其值得记：`pan: dist 1.3199 -> 1.3199` 里的第一个数**不是原始值 1.4233** ——
   **是 tilt 已经改过的值**，拿 1.4233 去比会把 tilt 的锅扣在 pan 上。

**变异**（每条断言都要有一个必须变红的变异，DECISIONS 205）：
把 `TILT_PIVOT` 的 z 从 0.86 改成 0.90 → **12 ok / 2 failed / exit 1**；把 tilt 的轴从 `"Y"`
改成 `"X"` → **9 ok / 5 failed / exit 1**。第二个变异还翻出一件有意思的事：接收端的枪口
**正好落在过销的那条 X 轴上**，所以「绕错轴」对它**改不了任何距离** —— 距离检查抓不到，
只有**旋转**检查抓到。**两类检查缺一不可**，不是保险起见各来一份。
正常跑：**14 ok / 0 failed / exit 0**。

### 82.5 转了多大范围

- **pan ±90°**。硬限是**算出来的**：罩口最远端在 `x = 0.66 + 1.26·cos a`，`a ≈ 116°` 才
  碰到自己那面墙。90 取在它里面。
- **tilt ±75°**。**这个是选的，不是推出来的** —— 我检查过的东西里没有一件在 ~120° 之前
  挡住它，而「一个能对着地板看的摄像头」不是我要的。**没做扫掠体积检查**，所以满 tilt 时
  头**可能**擦到自己的轭臂。

### 82.6 交接夹（用户要求的第二件事）

操作员**自己**把根目录拆了：他的文件**和那份 README** 进了 `Misc\`，`From_RBLX\` 空着留在
根上。**我照他摆的来，没有搬回去** —— README 就地更新。`DMR.blend` 和它引用的
`Part1_diff.png` / `Part1_nmap.png` 现在**在同一个 `Misc\` 里**，相对引用仍然成立。

README 里换了那张表（**四个件**，不是两个模型）、加了「三件刚体 + 转轴的配方」段、
并把 `ChamberGrate` 那条 ⚠ 挪回了它自己那张表下面（上一版加段落时把它挤到了 LaserPort
那节之后）。

### 没做的
- **没进 Studio**。`2.14 x 1.98 x 2.34` 是 Blender 单位下的读数；Studio 里该是同一组数
  （Y/Z 互换），**这条仍是可检验的预测**。
- **没做扫掠体积检查**（见 82.5）。
- **glb 那条路的换算仍未验** —— `laser_port_check.py` 读的是 **FBX**。glb 的假设至今没有检验器。
- **没看那 5 张渲染**（新增 `LaserPortAimed_iso.png`：两端都摆到 pan 32° / tilt 22°）。
  剪影好不好看是操作员的判断。
- **`LaserPort.blend` 是整场**（四个件都在），两个 FBX/GLB 才是要导入的东西 —— 上一版给
  每次导出都存一份 `.blend`，得到两个**逐字节相同**的文件换了名字；这一版改成只存一份。

## Phase 83 (2026-10-04) — LaserPort 进 Studio：上色、点一下转云台、**并且真的打出激光**

用户两句话是本轮的靶子：「你上完色之后呢，搞个脚本，点击它就让它懂（动）一下」、
「还有你得让它真能射出激光」。三条硬要求：**点一下就动**、**真打出激光**、**真实验证**。

### 83.1 为什么导入进来没有颜色（量出来的原因，不是猜的）

`D:\BlenderRobloxTestProjects\LaserPort\LaserEmitterPort.glb` 里**材质是纯色因子**：
0 张贴图、0 个 image、0 组 UV，`baseColorFactor` 是一个平色。Roblox 的 glTF 导入器
**没有 per-face 材质槽**，所以每个 MeshPart 一律落成 `Material=Plastic` + 灰色 `Color` +
空 `TextureID` —— 十一个件**全是同一个灰**。**这不是导入坏了，是格式本身没有地方放那个色。**
修法只能是把「哪个件该是什么色」重新说一遍：`_tools/apply_laser_port_materials.luau`。

**认件用形状，不用名字、不用顺序**（见 265）：每个候选件都能拟合出一个比例 k，
取残差最小者，并且**要求次优解离得足够远**。

| 件 | 材质 | 颜色 |
|---|---|---|
| `PortMount`（底座 / 轭臂基体 / 头壳） | Metal | rgb(101,105,110) |
| `PortBody` | Metal | rgb(173,177,182) |
| `PortDark` | Metal | rgb(77,80,85) |
| `PortCoolant` | Metal | rgb(200,155,108) |
| `PortLensEmit` | **Neon** | rgb(249,153,89) |

实测：`painted 11 part(s), 0 skipped`，逐件读回 `tex=""`、`anchored=true`。

### 83.2 那个 .glb 本身是坏的，而这正是它两轮没被发现的原因

`trg.export()` 的 glTF 分支只缩放 `o.scale`，**没有缩放 `o.location`**。结果是
**几何缩到了 1/5.902，件与件的间距还是设计尺度** —— 那不是「小模型」，那是**一碰就散的模型**。
FBX 那条路没事，因为 `global_scale` 连平移一起缩。

两轮没查出来的原因值得写下来：`laser_port_check.py` **只读 .fbx**，而操作员导入的是 **.glb**。
**一个只读一个文件的检查器，对另一个文件什么都没说**（同 §0.17「每条通道各管一半」）。
现在检查器**两个格式都读**；这个缺陷被留成变异夹具 `D:\_tmp_bmcp\buggy_glb` 复现过一次。

**轴向的落点（这一条推得最久）**：文件是**直立**的，不是躺着的。
`Roblox 的尺寸 = (Blender_x, Blender_z, Blender_y)`（Blender 的 up 落在 Roblox 的 up 上），
对应的位置映射是 **`Roblox_offset = F · (−blender_x, blender_z, blender_y)`** —— **x 取反**，
行列式 +1，是正常旋转。设计表里那些 X 偏移**符号全反**，就是因为表是在 Roblox/studs 坐标系里写的。
（这条是拿 FBX 那趟的权威读数 `LaserPortYoke size_studs=0.68 x 1.98 x 0.93` 去对 Studio 实测的
`1.1522 x 1.5757 x 3.3548` 钉死的。）

**导入倍数 ×1.69434 = 10 / 5.902**，十一个件独立拟合、误差 ≤ 0.0007。也就是说
Roblox 的 glTF 那条路按 **10 studs/文件单位** 读，而 FBX 那条路认 `STUDS_PER_UNIT = 5.902`。

### 83.3 云台：节点原点**重建**，不是写死

导入器会把每个 MeshPart 重新原点化到它自己的图元里面（**既不是节点原点，也不是它自己的包围盒中心**），
所以一个件的 `Position` 拿不到转轴。而 `Model:GetPivot()` 在导入的模型上**直接不可用**：
实测**轭臂和头两个节点回了逐字节相同的 pivot**，两个不同的节点不可能共用同一个 pivot。

办法是**减掉每个图元在设计表里的包围盒偏移**：
`origin = part.CFrame * CFrame.new(-row.off * k)`。
**同一节点的每一件都是同一个原点的独立估计** —— 所以「它们必须一致」是一道**免费的检查**。
实测三组全中：

| 节点 | 原点 | 由几件一致得出 |
|---|---|---|
| Base | (−55.0973, 1.3555, 16.3750) | 3 / 3 |
| Yoke | (−56.1973, 1.5555, 16.3750) | 3 / 3 |
| EmitterHead | (−56.1973, 2.7075, 16.3750) | **5 / 5** |

由此得到两条轴：**pan = 过 (x=−56.1973, z=16.3750) 的竖直线**；
**tilt = 过 (x=−56.1973, y=2.7075) 的 Z 向线**。两条轴的 x 相同是**构造决定的**
（一根立柱同时带着两个关节），所以脚本把这条当成**断言**：不成立就说明认错了件，
而认错件的结果是「绕一条穿过空气的线转」——**它会动，只是动得不对**（§0.18 同一族）。

**实测（跑的是交付物自己的字节，见 83.6）**：

| 检查 | 结果 |
|---|---|
| pose2（pan 45°）底座位移 | **0.000000** |
| pose2 其余件到 pan 轴的距离漂移 | **0.000004**（摆幅 1.388 studs） |
| pose4（tilt 25°）头部件到 tilt 销的距离漂移 | **0.000003**（摆幅 0.785 studs） |

tilt 的不变量**只能在 pan 之前量**：销会被 pan 带走，pan 之后再量那个距离是对一个已经荡走的销量，
**会把刚体运动报成断裂**（Phase 82 已踩过，这里沿用）。

### 83.4 激光是真打的

光束是一个**真 Part**，不是贴图：`Material=Neon`、`Shape=Cylinder`（Roblox 圆柱沿自己的 X），
每帧从**镜片的实时 CFrame** 重新摆一次，并且用 `workspace:Raycast` **打在第一个挡路的东西上**。
「永远停在同一个距离」那是**光束的贴图**；**打在墙上**才叫激光。

方向**不是填一个角度常数**，而是镜片自己的 **local −X**（那个件沿自身 X 最薄，那条轴就是光轴）。
**两个分支都跑到了**：

| 检查 | 结果 |
|---|---|
| 光束近端→远端距离 vs `Size.X` | **120.0000 / 120.0000** |
| 光束轴 · 镜片 −X | **1.000000** |
| 打空（120 studs 内没东西） | `size.X=120`、落点标记**隐藏** |
| 打中（2.66 studs） | `size.X=2.66`、落点标记**可见** |
| 头摆走之后再走一帧 | 光束跟着走了 **59.32 studs**，方向点积仍 **1.000000** |
| 出生位置 | **不在世界原点**（见 83.5） |

### 83.5 两个真缺陷，都是这一轮自己撞出来的

**① 每帧的工作藏在连接里 = 验不了。** 实测插件 VM **会**答应 `Heartbeat:Wait()`
（返回 0.0190 s），却**从不执行你交给它的回调** —— 3 拍 **0 次**回调，而 `conn.Connected` 是 **true**。
所以任何**只活在 `Connect` 里面**的东西，从唯一能驱动的那个 VM 里**看不见**（§0.2 换了张脸）。
改法不是绕过，是**把它提出来**：`M.stepBeam(rig)` 成为公开函数、**连接里调用的就是它** ——
测的是**同一段代码**而不是副本，连接本身缩成一行。（取舍 263）

**② Part 出生在世界原点。** 上面那个提取顺手翻出一个**真 bug**：光束在 `fire()` 返回之前
**从没被摆过**，于是在第一次 Heartbeat 之前，它是一条 **120 stud 长的 Neon 圆柱躺在 (0,0,0)**——
**一根横穿地图的橙色杆子**。现在 `fire()` 里**同帧先摆一次**再进循环。
（取舍 264；这条不是为了让测试好过，它是**玩家看得见**的东西。）

### 83.6 交付形状与「测的是交付物自己的字节」

交付物是 `Workspace.Scene.LaserPortGimbal`，一个 **`Script`**（`Enabled=true`，493 行，19590 字节）。
**必须是 Script 而不是 ModuleScript**：ModuleScript **自己不会跑**，而 ClickDetector
**只在 Play 模式下存在**（取舍 266）。

于是「测的是不是交付物」只有一条正路：**把 `Script.Source` 读出来**，塞进一个临时
`ModuleScript`（§0.15 的现成路线，用在 Script 上），再 `require`。`Script` 的双形状
（`script:IsA("Script")` 时自装，否则只导出表）就是为这条路留的。

**字节级的证据**：`HttpService:GetAsync` 从 `_tools/serve.py`（8768）取盘上的文件，
与 Studio 里那份**逐字节比较**：
`served 19590 / studio 19590 / IDENTICAL = true`。**不比长度，比字节**（DECISIONS 95/183）。
sha256 `94ea44522bfcb925955476bb7505a3a493e2d00084b1106dc30a230044caa94f`，
**0 个反斜杠**（所以 §0.10 的转义解码是**可证明的空操作**）、**0 个 CRLF**。

`M.install` 单独跑过：ClickDetector 挂在 **`LaserPortBase`**（底座不动，玩家不用追着点）、
`MaxActivationDistance = 40`、**连调两次 install 仍然只有 1 个 detector**（幂等）。

**收尾核了世界没被我改坏**：十一个件的 Position 与导入那天的读数**逐位相同**
（`LaserPortBase (−55.8258, 1.3555, 16.3750)` 等），`LaserBeam` / `LaserImpact` /
临时 Folder / 那个多余的 ModuleScript **全部已删**。

### 83.7 通道：`HttpEnabled` 现在是开的

用户 2026-10-04：「Httpsget我开了」「刚刚开的」。于是官方 `rblx_execute_luau` 的 `GetAsync`
**真的走 HTTP 了**（此前是 `HTTP requests are not enabled`）。这不是小事：**byte 级的校验
第一次可以只走一条命令**，不必「插件写 + 回推」。
留着没变的两条：插件 VM 的 `GetAsync` **仍是桩**（§0.17）；`PostAsync` 两边都能用。

### 没验的（分开写，不要混进上面）

- **真实的鼠标点击没做**。`ClickDetector.MouseClick` **没有玩家就点不了**，而这个插件
  不注册 server/client peer（§0.16），Play 模式里读不回来。验到的是**处理器两半各自独立验过**
  （`applyPose` 的几何、`M.fire` 的光束）加上入口 `M.install` 的副作用；
  **没有验的是那个鼠标事件本身**。
- **TweenService 的补间没验**（要会走的帧）。它**补到的目标 CFrame 是验过的** ——
  同一段目标计算，`tween=false` 那条路逐位读过。
- **接收端没导进来**。脚本能认 `ReceiverHead`，但 Studio 里现在只有发射端。
- **水平那一枪在 120 studs 内没打到任何东西** —— 那个方向是空的。这是**摆位事实，不是缺陷**。
- **好不好看是操作员的判断**，不是我的。
- 我自己在收尾时打了一列 `tilt` 指标（`|R.Y| + |U.Z| − 1`）是**错的尺子**，十一个件都报 −1，
  也就是什么都没告诉我。**「件没有烘旋转」的真正证据**是三组原点由 3/3/3/5 个独立估计
  在 4e-6 内一致 —— 不是那一列。

## Phase 84 (2026-10-04) — TransitionPillar：18 边接 24 边，Bridge Edge Loops 的 42 个三角形

用户原话（本轮唯一一句，出自 Phase 83 收尾之后）：

> 帅，创建一个 18 边的圆柱体底座，一个 24 边的圆柱体顶部。删除两者的顶面和底面，
> 使用"桥接边循环（Bridge Edge Loops）"功能，自动生成从 18 边到 24 边的平滑三角过渡网格。

### 84.1 为什么这件事**只能**在 Blender 这边做

Roblox 的 MeshPart 是一份**做完的三角形汤**：那一侧没有任何算子能拿两条**顶点数不同**的开环
把它们缝起来 —— 要做只能手算那 42 个三角形再写进文件。这是基于部件的建模**到不了**的唯一一类形状。
不是"更难"，是**不可达**。所以这不是"顺手用 Blender"，是**非它不可**。

### 84.2 一句话的两种读法，我选了哪一种（**读错的话改两行**）

「删除两者的顶面和底面」字面上有两解：

| 读法 | 后果 |
|---|---|
| **(a)** 两个圆柱的**四个**端面全删 | 四条开环。`bridge_loops` **照样产出**一个网格（它会两两配对），只是**不是这个** |
| **(b)** 只删**相对的那一对**（底座的顶面 + 顶部圆柱的底面） | 正好两条边界环，18 与 24；产出的正是那句"平滑三角过渡网格" |

**我选 (b)**，因为它是让 `bridge_loops` 有定义的那一读，也是用户描述的那一读。
(a) 不是"报错"，是**安静地产出另一个东西** —— 这一族的失败全都不报错。
判据落在 `doomed = [cap_face(bm, base_rings[-1]), cap_face(bm, top_rings[0])]` 这一行；
要改成 (a) 只需再删 `base_rings[0]` 与 `top_rings[-1]`。

### 84.3 数字（几何是免费选择，拓扑是交付物）

```
BASE_SIDES, BASE_R, BASE_Z = 18, 2.40, (0.00, 1.60)   -- 底座
TOP_SIDES,  TOP_R,  TOP_Z  = 24, 2.10, (2.40, 4.60)   -- 顶部
```

半径、高度、倒角都是**我挑的**。**必须精确的是拓扑**：一个闭合流形、一条 18 边环接一条 24 边环、
中间正好 18 + 24 = **42 个三角形**、而且**不扭**。所以这三个数在构建脚本里**断言**，
再由 `transition_pillar_check.py` 从**导出后的文件**里读回来 —— 构建脚本自己的 printout
不算证据（§0.6，Studio 侧 §0.2 的同一条）。

**`BASE_Z[1] = 1.60` 与 `TOP_Z[0] = 2.40` 之间那 0.8 stud 的空隙不是余量，它就是桥。**
两个端面若共面，两条环就在同一高度，桥出来的带子高度为零 —— 42 个**退化三角形**：
零面积、看不见，而"42 个面"这个计数**照样成立**。（检查里因此有一条 zero-area 断言。）

### 84.4 三件工具

- `_tools/blender/transition_pillar.py` —— 建 + 导出 + 出图。三个变异开关（见 84.6）。
- `_tools/blender/transition_pillar_check.py` —— **重新导入** `.fbx` 和 `.glb`，逐条读回拓扑。
- 倒角是**角度过滤**的：带子向内倾 `atan(0.30/0.80) = 20.6°`，低于 25° 门槛，
  所以**两条接缝环被刻意跳过**，42 个三角形原样活下来。这一条是**量出来的**（`band_faces=42`），
  不是假设的。

### 84.5 验证：**两种格式各 20 项，全绿**（`CHECK 20 ok, 0 failed`，rc=0）

```
FILE TransitionPillar.fbx   as stored: verts=126 polys=128 tris=248  welded: 126 faces=128
FILE TransitionPillar.glb   as stored: verts=504 polys=248 tris=248  welded: 126 faces=248
  closed manifold: open_edges=0        OK
  single shell:    components=1        OK
  rim lower: z=1.600 n=18 (want 18)    OK | r=2.4000..2.4000 (want 2.40) OK
  rim upper: z=2.400 n=24 (want 24)    OK | r=2.1000..2.1000 (want 2.10) OK
  band faces=42 (want 42)              OK
  band all triangles: 42 of 42         OK
  band not twisted: min centroid radius=2.1837 (floor 1.8900)  OK
  no degenerate faces: 0               OK
  size_studs = 4.80 x 4.73 x 4.60      （Roblox 帧 4.80 x 4.60 x 4.73）
```

**面数 248 我手核过一遍**：底座壁 18 四边形(36) + 顶壁 24 四边形(48) + 底 18 边形(16)
+ 顶 24 边形(22) + 倒角环 18+24 四边形(84) + 带子 42 = **248** ✓。
**126 个顶点** = 84 + 两条倒角环各 21 ✓。

**Y 是 4.73 不是 4.80**：18 边形的 max|y| = 2.4·sin(80°) = 2.3637，因为它的角度相位和 24 边形不同 ——
两个不同边数的直接后果，**不是缺陷**。

### 84.6 变异测试：三条，结果分别是**红 / 绿 / 红**（DECISIONS 205 的纪律）

| 变异 | 结果 | 说明 |
|---|---|---|
| `--no-bridge` 不架桥 | **10 项红，rc=1** | `open_edges=42`、`components=2`、`band=0`。**两条接缝环的计数与半径照旧全绿** —— 缺桥根本碰不到它们。检查是**对准了**，不只是响 |
| `--twist` 翻转顶部圆柱的绕向 | **20 项全绿，逐位相同** | **负结果，而且是真结果**：绕向错**传不到**带子上。两条独立原因都得成立才可能：`trg.finish` 会 `recalc_face_normals` 抹掉翻转；`bridge_loops` 按**几何**推对应关系，不按你递给它的环序 |
| `--cross` 手工搭一条对侧相接的带子 | **18 绿 2 红，只有 twist 那一行红** | `min centroid radius=0.5898`（正确值 2.1837，门槛 1.8900）。**闭合、单壳、两条环的边数与半径、带子 42 个三角形 —— 全对**，只有它红 |

`--cross` 那一条是**先量后信**才写下的：我原本断言"扭转测得出"，而前两次变异让它**一次都没红过**
（一次是空带子的副作用）。**没演示过的断言就是没证据的断言**，所以硬造了第三种变异把它逼红。

**`--cross` 顺带翻出一个真性质**：倒角的 25° 角度过滤**依赖带子是对的**。
正确的带子只倾 20.6° → 被跳过；**交叉的带子很陡 → 倒角会去吃它**，
把每个带子三角形切碎、并把两条环从设计高度上拽下来（verts 126 → 240，`band_faces` 直接归 0）。
也就是说：**一块错的带子会被倒角藏起来**，看起来不像"错了"，像"那一段什么都没有"。
所以这个变异是把倒角关掉跑的（`bevel=0.0 if CROSS else 0.06`），否则它埋掉自己存在的理由。

### 84.7 glTF 那 504 个顶点 —— 问错了问题，不是文件坏了

`.glb` 读回来 `verts=504 polys=248 open_edges=504 components=128`，看着像导出坏透了。
**不是**：glTF **没有地方放多边形**，所以它把**每个角**都拆成独立顶点（法线在倒角处不同、
UV 在缝上不同）。**按位置焊接之后是 126 个顶点** —— 和 FBX **一模一样**。
两个文件描述**同一个实体**，只是只有一个还把拓扑留在索引里。

**规矩**：想对两种格式问**同一个问题**，先按位置焊接。`welded()` 就是干这个的。
不焊的话，`open_edges=504` 这种数是**关于我问法的缺陷**，不是关于文件的 ——
与 §0.18「错的量法不报错，它只安静地给你一个数」同族。

### 84.8 两个**我自己**的错，都在检查器里（不是资产里）

1. **单位陷阱**：Blender 场景坐标是**文件单位**，文件里装的是 studs/5.902。
   我拿原始坐标去比**以 stud 写死的**高度 1.600 / 2.400 → **每一条环都返回 n=0**，
   读起来像"导出坏了"，其实是"比较坏了"。`laser_port_check.py` 里那个 `u(v) = v/SPU`
   就是为这个存在的，我这次没抄。修法：`pos` 一律 `* SPU` 之后再比。
2. **检查器的 label 传错槽位**：`mark(ok, "OK")` 在失败时回 `"*** OK ***"` —— **每一行红的都印成绿的**。
   改成 `verdict(ok, good, bad)`，**报失败**。**输出不能一眼读懂的检查器就是会被跳过的检查器。**

### 没验的（分开写，不要混进上面）

- **没有进 Studio**。这一份是**导出的字节**验过（两种格式、逐条拓扑），
  **没有**导入 Roblox 去过 —— 按 Phase 83 的实测，glTF 那条路会把它放大 **1.6943 倍**，
  FBX 那条路 1:1。**要进 Studio 就导 `.fbx`**（同 LaserPort 那条结论）。
- **材质没验**。三个材质槽（`PillarBase` / `PillarBand` / `PillarTop`）是纯色因子，
  按交接夹 README 那条：**Roblox 导入器没有逐面材质槽**，进来是一身灰 `Plastic`，
  要上色得另写一个 `apply_*_materials.luau`（LaserPort 那份可以照着改）。
  带子**故意是另一个颜色**（黄铜）才看得见 —— 2.4 stud 半径上的 42 个三角形，眼睛自己找不到。
- **好不好看是操作员的判断**，不是我的。
- **倒角 0.06 是个我挑的数**，没做过扫掠检查，也没量过它在 Roblox 里吃不吃轮廓。

### 交付物

`D:\BlenderRobloxTestProjects\TransitionPillar\` —— `.fbx` / `.glb` / `.blend` / 两张渲染
（`_iso.png` / `_side.png`）。源码：`_tools/blender/transition_pillar.py`（构建 + 3 个变异开关）、
`_tools/blender/transition_pillar_check.py`（读回，rc=1 于失败）。

## Phase 85 (2026-10-04) — `Workspace.idk`：一块 46×35 的「玻璃板」是我自己的尺子造出来的

用户原话两轮：**「看下Workspace.idk」**，然后 **「哦对如果你需要看一些东西的样子…我把它导出为
obj 或者其他格式然后导入 blender 你能不能知道到它的样子」**。这一轮**没有改任何东西**
（中途动过两处属性做实验，已逐项还原，见 85.5），产出是**读**和**一条新坑**。

### 85.1 它是什么

`Workspace.idk`（Rebuild，`131274481205639`）23 个子物体 / 32 个后代，全在
`(-63.15, ·, 8.02)`、`Orientation (0,0,90)`：一座 **1 stud 见方的台座**。

- **台座**：`Part` **Cylinder** `Size=(0.125,1,1)` → **直径 1**（不是 1×1 方板）在 y=0.06；
  上面压一个直径 0.9 的同形件；`Union` `(0.781,0.75,0.75)` 是**机身**；4 根 `Block` 十字拉杆
  （y=0.27）、4 片 `Wedge` 十字叶片（y=0.45）、4 片 `Wedge` 支脚（y≈0.16）、
  两圈白色细环 `(0.01,1,0.76)`（y=0.24 / 0.36）、一片带 **4 张 `Texture`**
  （`rbxassetid://3538900065`，`StudsPerTileU/V = 0.5`）的圆盘（y=0.30，压在机身下）。
- **核心**：两个**球**套在一起 —— `Part` **Ball** 白 / `Glass` / `Transparency=0.90` / 直径 **0.5**；
  里面套 `Neon` **Ball** 黑 / `Transparency=0` / 直径 **0.45**。`Neon` 挂 `Attachment`
  ＋一个**停用的** `CoreParticle2`（`rbxassetid://75202463`，rate 5、lifetime 2..3、speed 0）。
- **扭曲层**：`Distortion` MeshPart（`rbxassetid://111479291067913`），`Glass`，`CanCollide=false`，
  **`Transparency = 2.00`** —— 这个属性只有 `0..1`，2 是**一个不存在的档位**，渲染器按 1 处理（全透）。
  上面挂 `Highlight`（fill 红 / `FillTransparency=0.5` / outline 白 / `DepthMode=AlwaysOnTop` / `Adornee=nil`）。
- **`Script`**：`BindToRenderStep("Lens", Camera.Value+1)`，每帧
  `lens.CFrame = CFrame.lookAt(anchor, cam.CFrame.Position) * CFrame.Angles(-pi/2,0,0)`
  —— 让那片 `MeshPart` 永远正对相机；`anchor` 是**脚本启动那一刻**读下的位置。
- **`ModuleScript`**：用户自己的注记——
  「这个可用于实现 黑洞立场扭曲效果 但是存在不足：光照上去会有反射，以及有明显的方格子」。

### 85.2 这一轮最贵的一条：**非 Block 的 `Size` 不是一个尺寸**

我一开始读到的是「`46.000 × 1.650 × 34.960` 的玻璃板、`41.4 × 31.5` 的黑板」——
**那是我算出来的，不是它长出来的**：

```
25  Part  Ball  size=(0.500, 46.000, 34.960)  Glass  tr=0.90
26  Neon  Ball  size=(0.450, 41.400, 31.464)  Neon   tr=0.00
```

`Ball` 的直径是 `min(Size)` —— **0.5 和 0.45**。41.4 与 31.464 **是死的**：渲染器不看它们，
只有 `min` 说话。`Cylinder` 同理（轴取一个分量，直径取另两个的 `min`）。
于是「位置 ± Size/2」这条老尺子（**§0.18**）在非 Block 上**换了第三种坏法**：
不是朝向搞错，是**那个尺寸根本不存在**。

**两张截图、两次射线一路都在说同一句话，是我的算术在撒谎**：全景里找不到那块板；
近距离俯拍里 35 stud 的盘该铺满整帧却没有；`GetPartBoundsInBox` 在 `idk` 之外只捞出 9 件，
全是邻居（LaserPort 三节 + 洗涤器那条 20.8 stud 的横杆）。**「错的量法不报错，它只安静地给你一个数」
——同一条教训第三次上门。**

**判据是一次染色实验**（85.5）：把底座圆盘染蓝之后，画面上出现的不是一块板而是**一圈细蓝环**
（直径 1 的盘被直径 0.9 的盘盖住，只露一圈边）—— **1 stud，不是 46**。

### 85.3 那两个死尺寸多半是**换过 Shape 的残留**

`(0.5, 46, 35)` 和 `(0.45, 41.4, 31.5)` 摆在一起，就是「一块玻璃板 + 一块小一圈的黑板」
—— 典型的黑洞底幕。**`Size` 不会随 `Shape` 变**，换成 Ball 之后参数留在原地，形状缩成一颗弹珠。
**「明显的方格子」很可能就是那两块板还在的时候**（46×35 上按半 stud 一铺就是 92×70 格）。
**这一条是推测，不是测量**：现在场景里能出格子的只有两处 —— 那片 0.75 圆盘上的 4 张 `Texture`
（藏在机身下），和 **baseplate 自己的 `Texture`**（`rbxassetid://6372755229`，8 stud/格，只在 Top 面）。

### 85.4 两个不足，各自的落点

| 用户写的 | 我认为是什么 | 一行话的改法 |
|---|---|---|
| 光照上去会有反射 | `Glass`。Roblox 的 Glass **透明度再高也留着高光**，0.90 的白球照样有亮边 | 白球改 `Material=Plastic`（哑光）／`SmoothPlastic`（微亮），`Reflectance=0` |
| 有明显的方格子 | 85.3 的两条候选之一 | 4 张 `Texture` 的 `StudsPerTileU/V` 调大，或直接 `Transparency=1` 关掉 |

### 85.5 我动过的东西（**逐项还原，但有一条是推断**）

为了知道「画面上到底是什么」做过一次染色实验，**已还原**：

| 物件 | 原值（读到的） | 我改成 | 还原成 |
|---|---|---|---|
| 底座圆盘 `Part` Cylinder `(0.125,1,1)` | col `0.471` 灰 / tr `0` / **material 没读到** | 蓝 `(0,120,255)` / SmoothPlastic | col `(120,120,120)` / tr `0` / **`Metal`（推断）** |
| `Neon` Ball | 黑 / `Neon` / tr `0` | 红 `(255,0,0)` / SmoothPlastic | 黑 / `Neon` / tr `0` ✓ |

**`Neon` 那条逐位还原；底座那条的 `material` 是推断** —— 改之前我没有读它，
而它周围 22 件全是 `Metal`、颜色也是那一档的 `#787878`，故按 `Metal` 还原。
**这是这一轮唯一一处「我说不准」的地方。**

**同轮另有一件事要交代**：我用 API 调过一次 Studio 的 `undo`（本想撤销自己的染色）。
它**什么都没撤销**，而 `undo` **不告诉你它改了哪一条** —— 那是一次**盲写**。
属性写入看来根本没进撤销栈。**结论：`undo` 不能当清理工具用**（取舍 **272**）。

### 85.6 没验的

- **`Highlight` 到不到屏幕上**：Edit 模式的截图里它和那件 `Transparency=2.00` 的 MeshPart
  都不足以分辨；「红填充 + 白描边」是**读出来的属性**，不是看到的画面。
- **`Distortion` 那个 mesh 长什么样**：`rbxassetid://111479291067913`；
  本机 `get_asset_thumbnail` 要 `ROBLOX_OPEN_CLOUD_API_KEY`（没设，当场报错）。
- **方格子到底是哪一处**（85.3 两条候选）：没做「关掉 `Texture` 再拍一张」的对照实验。

### 交付物

无。这一轮只读；**世界逐项还原**（85.5 那一处推断除外）。

**⚠ 86 号更正（2026-10-04）：85.4 表里「白球改 `Material=Plastic`」那条建议已作废。**
用户原话「**不对啊，你改成plastic就没有那种扭曲的效果了啊**」—— 那个扭曲**就是** `Glass`
的折射，是我拿功能换的 bug。**不要执行那一行。** 见 Phase 86.7。

---

## Phase 86 (2026-10-04) — `Workspace.Folder.Folder.Folder.18`：18 边往外扩成 24 边，**接缝就是交付物**

用户原话两句：「**哦对了，wokspace子文件夹下面有个文件夹叫18，我需要你往外扩展为24边形墙壁，
并且要正确衔接**」。

**这一轮世界零改动**（中途为验证建过一个临时文件夹 `__CWMatTest`，已删，复核 `leftovers=0`）。
产物在盘上和操作员交接夹里：**没有进 Studio**，理由在 86.5。

### 86.1 那个「18」是什么（量出来的）

- **720 条由外向内射线**：`rmin=63.711`、`rmax=64.695`、**零漏**；剖面在
  `0°, 20°, 40° …` 处折 —— 所以 **63.712 是 apothem（侧面），64.695 = 63.712/cos(10°) 是
  circumradius（角）**，并且**顶点落在 +X 上，不是边**。这一条是「衔接」唯一不能搞错的事实。
  面板各占 ±9.6°，`Union` 那块板的角楔补上每个顶点约 0.8° 的缝 → **环是闭合的**，
  面板与板的侧面在 apothem 63.712 上**共面**。
- **竖直落点 probe**：`r=58` 打到 `Folder>Folder>Union` y=47.400；`r=60/62/64` 打到
  `Folder>18>Union` y=47.400；`r=56, 50, 30, 0` **什么都没有** → **平台是个圆环**，
  中心有半径 ≈57 的洞，两个环的顶面**同在 y = 47.400**。
- **是两个同心 18 边环，不是一份被复制**：

  | 容器 | 件数 | 段尺寸 | y | plate apothem |
  |---|---|---|---|---|
  | `Workspace.Folder.Folder.Folder`（内唇） | 19 | `20.000 × 1.750 × 1.875` | 46.525 | 58.588 |
  | `…Folder.18`（**就是它**） | 19 | `20.707 × 0.650 × 5.000` | 47.075 | **63.712** |

- **顺带一条会再复发的**：`Workspace.Folder` 下面 **5 个孩子全叫 `Union`**，
  所以 `FindFirstChild("Workspace").FindFirstChild("Folder")` 走的是**另一支**——
  探针报 `Folder.Folder.Folder = false`，而 `Workspace.Folder.Folder.Folder.18` 明明在。
  **§0.14 同族：`FindFirstChild` 不是一条路径。**

### 86.2 为什么这活只能在 Blender 做

同 §5.15 / Phase 84：Roblox 那边的 MeshPart 是一份做完的三角形汤，**没有任何算子能拿两条
边数不同的开环缝起来**（要手算 18 + 24 = 42 个三角形）。**不是更难，是不可达。**
所以「正确衔接」这四个字，落点就是那条 **84 个三角形**（内外各 42）的过渡带。

### 86.3 设计（`_tools/blender/chamber_wall_24.py` 顶部 design 块）

| 段 | 范围 | 形状 |
|---|---|---|
| collar | z 0.00 → 1.20 | **18 边**，apothem **63.712**（与场景里那个逐位相同） |
| **bridge** | z 1.20 → 4.20 | 以上两环之间，**内外各 42 个三角形** |
| wall | z 4.20 → 13.20 | **24 边**，apothem **68.000**（比 18 边**外扩 4.288**） |

壁厚 **4.00**；顶点相位 0（顶点在 +X）。三条要写下来的：

1. **底座是齐平的，往上才外扩。** 18 边的角点 `64.695` **正好等于平台 rmax `64.695`**，
   所以 collar 的角坐在平台外沿上；外扩发生在 y ≥ 48.6 以上。代价是**上部悬挑 3.3 stud**
   （平台在 r>65 就是空的，probe 里 `r=66/70` 打不到东西）。**这是「往外扩展」这句话的直接后果，
   我选了留着它** —— 想要不悬挑就把 `A24` 调回 63.712，但那就不是「往外」了。
2. **导入后不需要任何相位修正，理由要写清楚。** FBX 导入的映射是 `(bx,by,bz) → (−bx, bz, by)`，
   即 Studio 方位角 = `180° − b`。18 边顶点每 20°、24 边每 15°，**两个集合都对 180° 旋转不变**，
   于是也对这个镜像不变。**一个偏移 7.5° 的 24 边就不是**，那种设计必须在导入后转。
   —— 不变性是一条**关于这个设计的**结论，不是关于导出器的。
3. **不倒角是决定，不是漏掉。** `trg.finish()` 的倒角按 25° 过滤，而这条带子倾
   `atan(4.288 / 3.0) = 55°`，**远在门槛之外** → 倒角会去吃全部 84 个三角形把它们切碎。
   这是管线的一条真性质（**DECISIONS 269：过滤器的「角度」其实滤的是「形状对不对」**），
   诚实做法是**关掉**，而不是把 offset 调到小得看不出损伤。

### 86.4 验证（§0.6：构建循环不是证据）

`_tools/blender/chamber_wall_24_check.py` **把导出的文件重新读回来**，`.fbx` 和 `.glb` 各 16 项、
**共 32 项全绿，rc=0**（**两种格式是两个独立证人** —— `.glb` 那条分支在 LaserPort 上曾经
悄悄坏了两轮而 `.fbx` 全绿）。断言逐条：闭合流形、单壳、**四条环的 n 与半径**、
两个多边形各自的 **apothem**、带子 **84 个三角形**、**配对同侧**、不扭、无退化面、高度。

读数：`verts=168 polys=210 tris=336 open_edges=0`；`137.17 × 13.20 × 137.17`（Roblox 帧）。

**三个变异，各自红在自己的行上：**

| 变异 | 结果 |
|---|---|
| `--no-bridge` | 20 ok / **12 红**（洞 84、双壳、带子 0） |
| `--wrong-pair` | 28 ok / **4 红，只有「配对」那两行**（84 bad）← **判别力最强的一个** |
| `--cross` | 24 ok / **8 红**（洞 42、带子 42、**扭 19.61 < 门槛 54.57**） |

**一条负结果要记**：`--no-bridge` 下「不扭」那行**也是红的**，但理由是**带子为空**
（min centroid radius 打印 `-1.0`），不是它扭了。**那一行在「没有带子」时没有判别力** ——
和 DECISIONS 205/270 同一条：红了要问**红在什么上**。

**没验的（分开写）**：没进过 Studio（86.5）、材质没验、真实鼠标点击没验、
墙高 13.2 与 `A24=68` 是我挑的数（不是量出来的）。

### 86.5 交付路径：**得你拖进去**

`upload_asset` 要 `ROBLOX_OPEN_CLOUD_API_KEY`（`asset:write`）+ creator id，**两个都没设**；
`import_rbxm` 在这个插件上是 `Unknown endpoint`。所以：

```
D:\BlenderRobloxTestProjects\ChamberWall24\ChamberWall24.fbx   ← 拖进 The Reactor [Rebuild]
```

**scale 填 1.0**（这份是按 1/5.902 导的，FBX 那条路 1:1；**导 `.fbx` 不要导 `.glb`**，
glTF 那条是 1.6943 倍）。落位：**底面中心 `(-12.200, 47.400, -85.362)`，不需旋转。**
导入后 `Size` 应该是 `137.17 × 13.20 × 137.17` —— **这个数就是全部的检查**。

材质不随导入保留（Roblox 导入器没有逐面材质槽），所以另写了
`_tools/apply_chamber_wall_materials.luau`：按**形状比例**认件（不是名字、不是顺序）。
三个分支**都在真机上跑过**（临时件，已删）：

| 场景 | 结果 |
|---|---|
| 设计尺寸 129.39×1.20 / 137.17×3.00 / 137.17×9.00 + 一个 5³ | **3 中 1 拒**，5³ 报 `UNMATCHED (score 4.7470)`，颜色没动 |
| 上面三个**整体 ×1.6943** + 一个刻意做的平局件 | **3 中 1 歧义**，报 `AMBIGUOUS (WallBand vs WallBase: 0.1348 vs 0.1348)` |
| 读数回验 | `Metal` + `(162,166,172) / (221,196,149) / (200,205,209)`，被拒的那个仍是红 `Plastic` |

**第一版是错的，而且是这个测试抓出来的。** 它把「两边都除以**场景里最宽的那个**」当成了归一化
——那只在导入**恰好是设计尺寸**时才成立。×1.6943 那一轮，它把形状比例**打印得和设计一模一样**
（`1.00000, 0.00927` / `1.00000, 0.02187`），然后**四件全部拒收**。正确的做法是
**各自除以自己**的最大维。**一条只有在「参数正好等于默认值」时才成立的归一化不是归一化。**
（DECISIONS 275）

### 86.6 新通道：**官方 sandbox 能 HTTP，而且有 `loadstring`**

§0.17 那张表说官方 `rblx_execute_luau` 走真 HTTP。这一轮补上另一半：**它还有 `loadstring`**。
于是本机起一个静态文件服务（8766，`python -m http.server`）就能把盘上的 `.luau`
**按它自己的字节**推进 Studio 跑：

```lua
local H = game:GetService("HttpService")
local f = loadstring(H:GetAsync("http://127.0.0.1:8766/_tools/apply_chamber_wall_materials.luau"))
local ok, err = pcall(f)
```

**好处三条**：不用誊写（跑的就是盘上那串字节）、不撞 `Capabilities`（§0.17 那个墙是
`require` 工程模块才有的）、**不进编辑层**（§0.10 的转义解码坑一并绕开）。
**注意**：它是**真 HTTP**，所以按需起停；`start_services.bat` 里那个 8766 本来就是这件事。

### 86.7 玻璃那条：**撤回一条建议，交出一半答案**

用户原话两句：「**不对啊，你改成plastic就没有那种扭曲的效果了啊**」、
「**或者还有一种可能，你可以自定义材质，让它不反射光，而有折射效果**」。

- **撤回**：85.4 建议的白色 Glass 球改 `Plastic` —— **作废**。那个「扭曲」**就是** `Glass`
  的折射，改 `Plastic` 是拿功能换 bug。而且两个 `idk` 的 Glass 件 `Reflectance` **本来就是 0**
  （已读），所以**没有一个单独的镜面层可以关** —— 那点亮边就是 `Glass` 自己的着色器，
  在 `Lighting.EnvironmentSpecularScale = 1.00` 下出来的。
- **他的第二条猜对了**：`MaterialVariant`，`BaseMaterial = Glass`，配一张**白的 `RoughnessMap`**
  和/或**黑的 `MetalnessMap`**。**但两个贴图都要一个已上传的 `ContentId`** ——
  没有上传凭据，这条路**现在走不通**（同 86.5）。
- **不需要上传的三条替代**：① `Lighting.EnvironmentSpecularScale` 1 → 0（**全局**，
  会影响世界上每一件，不只是那颗球）；② `Material = Water`（有折射、高光弱一些）；
  ③ 把 `Glass` 的 `Color` 压黑 —— 高光还在，只是不刺眼。

**这条错处方曾经住进 `CLAUDE.md` §8 的 Phase 85 段**（那一份每轮都进上下文），
已在原处改成更正 + 指向 **`DECISIONS_2` 278**。那条取舍记的是判断本身：
**当症状的成因就是被要求的功能时，不要修症状。**

### 交付物

`_tools/blender/chamber_wall_24.py`（构建）、`_tools/blender/chamber_wall_24_check.py`（读回，
失败 `exit 1`）、`_tools/apply_chamber_wall_materials.luau`（上色）；
产物在 `D:\BlenderRobloxTestProjects\ChamberWall24\`（`.fbx` / `.glb` / `.blend` / 两张渲染）。
**世界零改动。**

落地没做（无上传凭据），步骤写在 `docs/TODO.md` **§3.5**。
交接夹那一侧 `README.md` 也加了 `ChamberWall24\` 一节（同 LaserPort / TransitionPillar 的体例）。
