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
