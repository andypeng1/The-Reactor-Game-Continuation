# The Reactor Game — Continuation

This project was inspired by a game on Roblox called 'The Reactor [Maintenance]'.
Since the original game is no longer supported, this project is meant to keep it going.

It is developed against the original game as a **measurement target**, not by
guesswork: single-file scripts under `_tools/` are injected into the original place
(placeId `17596243941`) through a Luau executor, and each one writes its findings to a
local sink rather than to the screen - the operator can start the game **once** per
shift, so a result that only ever existed on screen is lost with the shift that produced
it. `TRG_original_recorder.luau` writes a sample log of only the values that changed; it
reads the player's own GUI as well as the world -- an object's own visible/enabled flag,
and the text of the labels it finds -- and emits a periodic `PERF` line about what the
reading costs, so that "the recorder is eating the frame" and "the client was already
stalling" can be told apart. `TRG_original_watch.luau` is the wide one: a bounded census
of the control room, the core chamber and the alarms, plus every monitor's GUI and every
audio event, opened by the start-up lever and closed when the shift dial reaches noon.
`transport_probe.luau` answers which of the executor's transports actually work, and
costs an injection but no shift. All three need two local services, and
`start_services.bat` in the repo root brings them up: the 8765 sink that receives
their bytes into `Data/` without those bytes ever entering an AI's context, and the
8766 file server they are fetched from. It opens two windows on purpose - each keeps
its own log and closing one does not take the other down - and it warns if either
port is already LISTENING, because a second copy binds nothing and dies, which
otherwise looks exactly like a service that is up. **Nothing under `_tools/` presses
a control.** The
recorder carried an observer-only driver until 2026-09-30 and no longer does - the
operator removed the requirement, and the code is kept in `_tools/_attic/driver/`
together with the measurements it made about the facility's two switches. `bash
_tools/run_tests.sh` gates what is left: six harnesses extracted from the shipped files,
six mutation runs that prove each harness can fail, and a 5.1 parse of both whole files.
The recordings under `Data/flow/` and
`Data/originalwatch/` are what the constants in this repo were calibrated from, and
`DECISIONS*.md` records what each number was derived from and what it is *not* good for.

---

# 反应堆游戏 — Subspace Reactor Backend (GameCore)

A server-authoritative, event-driven simulation of the Icarus Installation
subspace reactor, calibrated to The Reactor Game Wiki and the TRGWeb prototype.

## Layout
GameCore/
  Core/              Config, Signal, GameState, SystemManager, SimulationLoop, Network
  ReactorSystem/     ReactorState, ControlRodSystem (deprecated), CoolantSystem,
                     PowerSystem, CBLSystem, PEASystem, GravatronSystem, METUSystem
  MaintenanceSystem/ DeviceManager, DeviceFactory, MaintenanceController
  FacilitySystem/    FacilityController, FacilityBridge, ConsoleService,
                     ConsoleBinder, BackupPowerSystem
  AlarmSystem/       AlarmController, AlarmMonitor
  EventSystem/       EventController (random incidents + Equinox)
  PlayerSystem/      PlayerController, ShiftSystem
  PROGRESS / DECISIONS / DECISIONS_2 / README   (historical copies -- the disk .md is
                     the record as of 2026-09-26, see below)

DECISIONS IS TWO MODULES ON PURPOSE. ModuleScript.Source is capped at 200000 bytes by the engine,
and in Phase 40 the record passed it - the write was refused outright rather than truncated. Entries
1..74 stay in DECISIONS, under the name every existing reference already uses; 75.. onwards live in
DECISIONS_2. The boundary is an ENTRY NUMBER, so it is a fact about the document rather than about
its length on the day it was cut. **The direction of that copy reversed on 2026-09-26:** mirroring
back into Studio was retired, so DECISIONS.md and DECISIONS_2.md ARE the record and the modules
inside GameCore are historical copies left behind when the mirroring stopped. See DECISIONS 123 and
CLAUDE section 0.0.

## Conventions
- Systems expose Initialize() and Update(dt) and are called with DOT syntax.
- SystemManager runs them in ascending Priority (10..140) on a fixed 10 Hz step.
- GameState is the single source of truth; systems never cache private copies.
- All tunable numbers live in Core.Config - never hardcode them in systems.
- TRGWeb-derived constants are per 2.5 s tick and are converted with
  (dt / Config.Sim.TRGWebTick).

## Control model (Wiki: there are NO control rods)
1. Ambient pressure - Atmosphere Vent (AVB), E-VENT levers
2. CBL intensity    - Combustion Laser power levels 1..5 (MINIMUM..125%)
3. Isotope E        - three coolant pumps, discrete levels 0..3

## Core state thresholds (Fahrenheit)
0 Formation < 6000 | 1 Stable 6000-17500 | 2 High Energy 17500-29500
3 Critical 29500-39000 | 4 Meltdown 39000+ (METU auto-fires)

## Core temperature ownership
ReactorState is the only writer of GameState.Reactor.Temperature (DECISIONS 7). It applies
its whole heat balance in one block once per second (Config.Reactor.TempUpdateInterval), so
every term has to land there. PowerSystem does not subtract its P.E.A extraction sink
directly any more; it publishes the rate as GameState.Reactor.ExtractionHeatRate in
F per second and ReactorState folds it into the same step. A field rather than a getter,
because PowerSystem already requires ReactorState and a call back the other way would close
the require cycle. See DECISIONS 79.

## Shift quotas (GW peak output)
Shift 1: 512 | Shift 2: 1024 | Shift 3: 3072 (Equinox 3x helps reach S3)

## Workspace layout
Sorted from 1828 down to 40 top-level children:
  Workspace.Geometry/       anonymous building blocks
      Meshes, Unions, Wedges, Parts, Floors, Props, Models
  Workspace.Facility/       facility set dressing
      Shafts, Doors, Rooms, Props, Lights, Rigs, Cameras, Emblems
  Workspace.Sounds/Misc     loose sounds (a Sound in a Folder is 2D, as before)
  Workspace.GameCoreTests/  the self-test and control test harnesses
  Workspace.Legacy/         archived empty legacy scripts
  Workspace.Tools/          QPU tool pickups
  Workspace.TeamSpawns/     spawn locations
Functional roots (Core, METU, MES, CRC1-3, GravatronUnit, QuantumMainframe,
PowerExtractionAssembly, MedicalDispenser) and the system folders (Consoles, Monitors,
Stats, Alarms, Lights, RoomLights, Sounds, ...) stay at the top level because the
systems address them by path. Verified: bridgeResolved = 18 and the control test
passes 13/13 after the reorganisation.

## Control surfaces (ClickDetector)
The five control desks, the HDEF generator and the METU ECC receptacles are driven by
ClickDetectors (ConsoleBinder reuses the ones already in the place). Every press prints
  [Console] <player> pressed: <control label>  (<console model>)
and routes the action to ConsoleService.

  MainReactorConsole  : AVB, E-VENT 1-3, Start-Up, Shutdown, Monitor Boot
  ThermalConsole      : pump ON/OFF + PW1-3 levels, fans 1-6, pressurizer, PEA vent
  CBLaserConsole      : purge + PW1-5 power level per laser
  ElectricGridConsole : PEA extraction PW1-4, Gravatron charge / overload
  ALTReactorConsole   : M.A.S.S. 1/2 (status only)
  HDEFGenerator       : power lever, emergency control, cells 1-3
  METU                : ECC receptacle 1/2 (hand refill)

## Control trigger bus (ControlTrigger)
`FacilitySystem.ControlTrigger` is the single implementation of a control press. `ConsoleBinder`
owns only the dot-path table and calls `ControlTrigger.Bind`; the press body - the `[Console]`
print shown above, the `ConsoleFocus` client notification, `ControlVisuals.Pulse`,
`ConsoleService.PerformAction` and the `ControlVisuals.Update()` that follows it - lives there and
nowhere else. A physical ClickDetector press is `ControlTrigger.Fire(part, player)`, so the two
routes cannot drift apart.

Every bound control carries the `GameCoreControl` tag and six attributes: `GameCoreAction`,
`GameCoreArg`, `GameCoreArg2`, `GameCoreLabel`, `GameCoreConsole`, `GameCorePanel`.
`ControlTrigger.Reindex()` re-binds from `CollectionService:GetTagged`, so a part tagged by hand in
Studio starts working on the next server boot without touching the dot-path table. The metadata is
written once, on the first bind: the existing detector connection already closes over that first
definition, so rewriting it later would let the tag and the live behaviour disagree.

### Driving a control from the command bar
Use the BindableFunction, not `require`. The command bar runs in a separate Luau VM where `require`
returns a fresh module instance with an empty `GameState` (CLAUDE section 0.2), so a call through it
prints success and does nothing at all. `ControlTrigger.InstallBus()` installs the handlers from
inside the live server VM, so invoking them from any VM runs live code.

  game.ServerStorage.GameCore.ControlBus:Invoke("count")        -- tagged total + per-console split
  game.ServerStorage.GameCore.ControlBus:Invoke("list")         -- every bound control
  game.ServerStorage.GameCore.ControlBus:Invoke("help")         -- usage
  game.ServerStorage.GameCore.ControlBus:Invoke("ThermalConsole|Cooling Fan 4")
  game.ServerStorage.GameCore.ControlBus:Invoke(part)           -- an Instance works too
  game.ServerStorage.GameCore.ControlBus:Invoke("Cooling Fan 4", player)

`ControlBus` always returns a string, so whatever the command bar prints is the answer. A selector
is an Instance, a dot path, a control label, or `<console>|<label>`; a number indexes into `list`.
`ControlQuery` is the same surface returning tables for scripts:

  game.ServerStorage.GameCore.ControlQuery:Invoke({ verb = "count" })
  game.ServerStorage.GameCore.ControlQuery:Invoke({ verb = "get", Label = "Cooling Fan 4" })

### Why the detector is not always on ClickPart
A ClickDetector fires only for its own parent, or a descendant of that parent. On the Mk2 levers the
`ClickPart` plate sits under a `Collar` and a `Grip`, where no mouse ray reaches it, so
`ControlTrigger.detectorHost` parents the detector to the nearest ancestor model owning exactly
this one click plate - the lever's own model for a lever, the button itself for a button. The walk
deliberately stops at the first ancestor that owns more than one plate; that is what stops a
27-control console panel collapsing into a single hitbox. Three HDEF power cells stay enclosed and
mouse-unreachable on purpose; see DECISIONS 75.

## Control-room monitors
FacilitySystem.MonitorService writes its screens every simulation tick
(Config.Monitor.UpdateInterval = 0), so there is no refresh delay.

THERE ARE SEVEN MONITORS, NOT FIVE. The Wiki says "five consoles, three main monitors, and
four minor monitors" - 3 + 4 = 7 - and Workspace.Monitors really holds seven:
Main, Thermal, Power, Alerts, Quota, Log, Forecast. Earlier revisions of this file listed five
and omitted Log and Forecast; that was a documentation error, not a code change. MonitorService
drives all seven. Log and Forecast were the last two to be wired: both are written as PURE
OBSERVERS - they read GameState and never write it - so the single-writer rule holds and no
simulation behaviour changed. LogControlRoomMonitor is also referenced by Misc.DataCollection
(a ModuleScript nothing runs) and ForecastControlRoomMonitor by nothing else at all.
See DECISIONS 54 and 60.

  MainControlRoomMonitor    -> Temp, Pressure, Radiation, Output, HDEF, PEA stress,
                               Fluctuation, Extraction
  ThermalControlRoomMonitor -> Fan 1-6 ON/OFF, coolant pump LEVEL 1-3
  PowerControlRoomMonitor   -> CBL 1-3 power %, stress %, state, locked 925 F body temp
  QuotaControlRoomMonitor   -> in-game clock, shift quota target + progress %, Equinox
  AlertsControlRoomMonitor  -> 27 facility alert lamps (red = active)
  LogControlRoomMonitor     -> rolling 5-row severity-coded event log (cyan/amber/red),
                               eleven watched signals, change-triggered
  ForecastControlRoomMonitor-> energy-intensity timeline, one bar per 5s sample,
                               width = PowerOutput / current shift quota, plus a
                               priority announcement line

### The monitor binding contract (a rebuild needs zero script changes)
MonitorService resolves every screen BY NAME, so a rebuilt monitor is a drop-in as long as the
names and the hierarchy hold:

  Workspace.Monitors.<Name>ControlRoomMonitor     the Model
    .Screen                                       a BasePart, Neon, Transparency 0
      .MonitorUI                                  SurfaceGui
        .MainMonitorFrame                         Frame
          .GameCoreTitleBar                       Frame   (MonitorKit; ZIndex 0)
          <named children>                        the labels listed above

  local function findMonitor(name)
      local folder = game.Workspace:FindFirstChild("Monitors")
      return folder and folder:FindFirstChild(name)
  end
  local function monitorUI(monitor)
      if not monitor then return nil end
      local screen = monitor:FindFirstChild("Screen")
      return screen and screen:FindFirstChild("MonitorUI")
  end
  local function mainFrame(monitorName)
      local ui = monitorUI(findMonitor(monitorName))
      return ui and ui:FindFirstChild("MainMonitorFrame")
  end

Two things a rebuild must carry over. First, the SurfaceGui lighting mode - and it is NOT one
value for the whole room: **labels are LightInfluence 1, screens are 0.** A new SurfaceGui starts
at 0, which means "always fully illuminated": the plate ignores scene lighting AND exposure
compensation and renders flat white under any grade. That is wrong for a painted label plate and
RIGHT for a monitor, which is an emissive light source that has no business dimming with the
room. Measured: all 121 Mk2 desk plates ship 1 (DECISIONS 45 - shipping them at 0 is what made
the installed desks read washed out), while all 7 shipped monitor MonitorUIs ship 0 and should
stay there. This paragraph previously read "Every shipped original uses 1", which generalised
from the desks to the monitors without measuring them. See DECISIONS 57. Second,
`AlertsFrame.AlertFrame<N>` is indexed by a fixed count of 27, and `GameCoreLevelLabel` on the
Thermal pump frames is auto-created if missing, so neither can be dropped from a rebuild.

## The monitor bezel (Mk2)
All seven monitors were rebuilt in place - 25-34 added parts each, nothing renamed or deleted, so
the binding contract above is untouched and MonitorService needs no change. The additions are
`Bead*` (a bright rail hugging the screen), `Frame*` (a dark housing band outside it), four corner
brackets, `FrameBolt*`, and `ShelfTrim`. Every one is `CanQuery = false` so it is invisible to
gameplay raycasts, and stamped `GameCoreMk2 = true` for one-sweep rollback. Each monitor's outer
width reproduces its original exactly (Main 24.80) and nothing is added at X < 0.10, so no monitor
grew sideways or backward.

THE BEZEL IS TWO BANDS, NOT THREE, AND THAT IS A FINDING ABOUT THIS ROOM RATHER THAN THE PALETTE.
Three tonal bands - dark lip, mid rail, bright rail - were tried in four palette assignments and
rendered as one flat white band every time, because **every Metal part in this room renders white
whatever its albedo**: under Brightness 2.5 + EnvironmentSpecularScale 0.8 the specular reflection
of the environment swamps it, so `darker` (60,60,60 Metal) is indistinguishable from `lighter`
(186 Plastic). The dark band was therefore built in Neon near-black, the one value in the palette
that survived that grade, and also the facility's own recess idiom. Picking the dark band by Neon
was a workaround, not a fix - **the grade was DECISIONS 52's to fix, and the monitor bezel was to
be revisited after that pass.** A bright rail HUGS the screen because the screen is black and a
dark band against it would define nothing. See DECISIONS 58.

THAT PASS HAS NOW HAPPENED AND THE WORKAROUND IS RETIRED. DECISIONS 66 took
`EnvironmentSpecularScale` from 0.8 to 0.15 - the property that was the actual mechanism - and
Phase 21g then moved the 21 dark-band rails (`FrameTop`, `FrameSideL`, `FrameSideR`, three per
monitor) off `Neon 17,17,17` and onto `Metal 75,75,76 / FacilitySteelPanel`, which is the value
those monitors' own `FrameBolt*` parts already carried. The bezel is still two bands carrying the
same job: the bright `Bead*` rail defines the screen edge, the `Frame*` housing band sits outside
it. Only the material of the dark band changed. The one part DELIBERATELY left on Neon is
`Screen`, which is functional - it backs `MonitorUI`/`BootUI` and four `SurfaceLight`s. See
DECISIONS 73.

Each monitor also names itself now, by a property-only edit to the shipped `TextLabel`:
Main / Thermal / Power / Alerts / Quota / Log / Forecast, in the original's own `SMER - ` voice.
The strings are kept short because the label is `TextScaled`. All seven were re-read after a wait
and are stable - nothing rewrites them at runtime.

Two traps, both recorded in DECISIONS 59. To set a nameplate, address the label by its HOST
PART's name: "any TextLabel under a SurfaceGui" matches `Screen.MonitorUI.BootUpText` first on
every monitor, which is not the nameplate, and the mis-edit reads back CORRECT in a data probe
while only the screenshot shows it. And the seven monitor originals were originally re-parented
into the parking folder WITHOUT being moved, so they sat coplanar with the live monitors
(`liveDelta = 0.00`) and drew on top of the rebuild in every screenshot. They now sit at
Y 330 / Z 340, disjoint from the desk row at Y 330 / Z 265, each carrying `GameCoreParkedFrom`
and `GameCoreParkedPivot` so the move reverses with one `PivotTo()` per model.

## CBL body temperature
Wiki: a CBL's net body temperature is a constant 925 F. Config.CBL.BodyTemperatureF
holds it; CBLSystem.GetBodyTemperature() exposes it; it never changes.

## Facility systems
- QPUSystem    six quantum processors inside the Tesseract mainframe degrade from
               constant overclocking (faster at higher core states). A failed QPU
               reduces Stats.ActiveQPUs; all six dead = mainframe meltdown. Click a
               slot with a QPU tool to install a fresh one.
- GatewaySystem the subspace teleport rings (传送环). Rings spin, doors open and the
               pads go live while the reactor is online; stepping on a pad transits
               to the next gateway.
- GravLiftSystem the gravity lifts (重力电梯). Shafts carry operators up or down
               while the Gravatron is healthy; if it fails the shafts go dead.

## Control feedback
Pulling a lever SLIDES it to a detent derived from live state - it does not rotate; the throw is a
pure translation along the lever's own axis, and only its LeverUnion moves:
CBL 1-5, P.E.A extraction 1-4, coolant pump 0-3, fans / E-VENT / start-up 2.
The slide is tweened (0.3 s, Quad/Out, `Config.Visual.LeverTweenSeconds`) rather than snapping, so a
click reads as answered. VisualFeedback on the server is the only writer of those CFrames; the
client-side reflector was retired 2026-09-26 and is not the path to re-enable (DECISIONS_2 187).
The three control-room shutters that lever commands are tweened for the same reason, by the module
that already owns their CFrames (`RoomShell`): 10.58 studs over 0.6 s, Quad/Out,
`Config.Shell.ShutterTweenSeconds`. Levers and panels share one easing vocabulary on purpose - a
single control family should not read as two different games. RoomShell's half is SYSTEMS.md 2.12.
Buttons flash their indicator lamp green on press, then settle to white (ready),
red (unavailable/fault) or dark (spent).

EVERY ROUND BUTTON LIES FLAT, face up, sitting in a bright concentric bezel with its indicator
lamp on the pad beside it. That is what the shipped originals do - the original
AtmosphereVentButton points its axis 70 degrees above horizontal - and the Mk2 desks shipped
them standing on edge until the operator caught it. Two populations are deliberately NOT flat:
the 100 Bolt heads, whose axis is horizontal because a bolt head on a vertical face must face
the operator, and HDEF's guarded EmergencyControl, which is a mushroom button on a vertical
plate and really is pressed forward. A flat button cylinder is a 90 degree roll about Z; the
face label needs no adjustment, because label() writes to NormalId.Right and Right becomes the
top. See DECISIONS 55 and 56, PROGRESS Phase 19h.

## Automated control test
Workspace.GameCoreControlTest simulates operator clicks with a mock supervisor and asserts that
lever pivots move and lamp colours change. A SECOND phase asserts on GameState and on the owning
system rather than on the scene, which is what covers the twelve controls that leave no visible
mark at all. Latest run: 30 pass / 0 fail, 18 levers and 41 lamps, fluctuation sign 5/5, and 12 of
12 state rows PASS.

The fluctuation figure was recorded as 60/60 while PowerSystem still wrote r.Temperature every
frame. That double write is fixed (DECISIONS 79), temperature now settles once per second, and 5 is
what 60 iterations at dt = 1/10 can actually produce. The loop was left alone on purpose. See
DECISIONS 88 for the whole count, including the two failures the probe manufactured and the one
pass it produced by accident.

The 36 / 80 pair that appeared in an earlier revision of this file was the bench doubling every
desk: while Workspace.Rebuild.Models held a rebuilt copy of all six desks, ConsoleBinder.BindRebuild
bound both the live desks and the bench copies. The bench is not in the place, BindRebuild no-ops,
and the test reports the installed-only figures - 18 levers / 41 lamps.

## Rebuild kits
GameCore.Rebuild holds seven kits. Each owns one slice of the rebuild, each is
idempotent, and each is the record of what the authored values were - which is what
makes them the revert path rather than only the build path.

  RebuildKit       the six Mk2 desks as hero-asset geometry
  ControlRoomKit   the Mk2 geometry for the control room itself
  LaserKit         the three CBL lasers, refined in place
  LaserFrame       the rectangular frame around those lasers; additive, no hull change
  ShellKit         the control-room shell correction pass; builds nothing
  CoreKit          the reactor core body and its glow ramp; additive only
  MonitorKit       the monitors' content: dark backing and green title bar

The two content kits snapshot before they write. CoreKit stores each Neon part's
authored hue before rotating it; MonitorKit stores GameCoreAuthoredScreenColor on
each Screen, GameCoreAuthoredTitleColor on each TitleText and
GameCoreAuthoredFrameVisible on each MainMonitorFrame before it touches them. That
is what lets Revert() restore the place exactly and what stops a second Apply()
mistaking the kit's own colour for the authored one.

## Rebuild bench (Mk2 desks)
GameCore.Rebuild.RebuildKit rebuilds the six desks as geometry, on a separate pad
so the shipped facility is untouched. Layout: Workspace.Rebuild.Pad (96x2x96 at
Y 298), with Workspace.Rebuild.Models holding a two-row grid - row 2 is an
untouched clone of each original (REF_*), row 1 the rebuilt desk (MK2_*).

THE BENCH IS NOT IN THE PLACE RIGHT NOW, AND THAT IS NORMAL. It was cleared on
2026-09-21 as part of a workspace cleanup (DECISIONS 67) - 8,293 descendants / 5,367
parts that only existed to build the desks now installed. BuildAll() is SELF-HEALING:
it recreates Workspace.Rebuild and Models if they are missing, so call it and the
bench comes back. Nothing about the bench is state that has to be carried.
Workspace after the sweep: 123,924 BaseParts, 38 top-level containers.
Because the bench is absent, ConsoleBinder.BindRebuild no-ops - which is why the
control test reports the installed-only figures (18 levers / 41 lamps) rather than
doubling them. See the note above.

  RebuildKit.BuildAll()      idempotent: rebuilds every MK2_ desk and REF_ clone
  RebuildKit.Slot(col, row)  world CFrame of a grid slot
  RebuildKit.PALETTE         the palette measured off the originals
  BuildMainReactorConsole / BuildThermalConsole / BuildCBLaserConsole /
  BuildElectricGridConsole / BuildALTReactorConsole / BuildHDEFGenerator

The rebuilt desks reproduce the binding contract exactly - the same dot paths,
the same ClickPart / LeverUnion / LeverOrginPart / NeonPart names, the same model
hierarchy ControlVisuals walks - so ConsoleBinder.BindRebuild drives them with
the shipped CONTROL_DEFS and only the root swapped. It keeps its own counters and
no-ops when the bench is absent. The binding figures moved when the Mk2 desks were
installed, because they ship no ClickDetectors and nearly every control therefore
needed one created: desks=6 controls=68 reused=2 created=66 missing=0. That is the
baseline a future regression is measured against.

Measured: 66/66 anchors resolve on both the clone and the rebuilt desk, and 0
lever-owner differences against the originals. Binding the rebuilt controls
registers 18 levers and 38 lamps on the bench clone set.

ConsoleBinder reports its rebuild pass separately: rebuild desks=6 controls=66 missing=0,
the same 66 controls driven through BindRebuild on the Mk2 models.

TONE PASS (2026-09-23). The desks were rebuilt once more against the originals, this time by
measuring colour AREA SHARE instead of by eye. Four palette keys were found pointing at the wrong
surfaces and two had drifted from their own comments: hull 108 -> 125 and post 86 -> 100 (their
recorded fractions, 0.490 and 0.392, are exactly 125 and 100 over 255 - the values they used to
hold); Deck "darker" (60) -> "light" (163,162,165), because the original's working surface is a
3.50 x 0.25 x 15.00 ParticlePart at 163,162,165 Plastic and Mk2's largest single visible face was
near-black; seamLine "black" -> "seam" (90,90,90), because the original carries a 3.84 x 0.12 x
15.00 Metal slab at 90,90,90 along its brass band; EndCap "dark" -> "seam".

The front was also literally empty. Mk2's louvre banks sit at BODY_X1, 1.5 studs behind the deck
edge, so the cantilevered deck hides them, and the middle 6 studs of cabinet were plain. A new
perfPlate() helper lays a grid of small proud chips across the cabinet front as two banks plus a
centre field and along the lip above the brass. The chips are 50,50,50 SmoothPlastic, NOT unlit -
unlit is Neon, so hundreds of 0.15-stud chips read as one flat black void at any normal distance.
18 near-black hazard bars now run the full length of the brass band, which previously carried them
only on the two end plates.

Result: 220 -> 370 parts on the main desk against the original's 496; the whole set went
283/226/184/220/177/61 -> 433/376/334/370/327/61 in CONSOLES order. HDEFGenerator is unchanged at
61 because it does not go through buildShell and so picked up no perfPlate - a known gap, not an
oversight. See PROGRESS Phase 37 and DECISIONS 106 / 107.

INSTALLED. All six Mk2 desks now sit in Workspace.Consoles under the names of the
desks they replaced, and all seven shipped originals are parked, not deleted - the six
live desks plus the pre-existing duplicate CBLaserConsole, which is harmless there
because nothing resolves it. Each parked model carries GameCoreParkedPivot +
GameCoreParkedFrom, so the move reverses with one PivotTo() per model. Orientation was
solved in world space against each original's own depth/length basis, with an explicit
facing constraint, so every desk is flush with the front face it replaced and faces the
operator.

WHERE THE ORIGINALS LIVE NOW (changed 2026-09-21). They used to be at
Workspace.Rebuild.Originals (Y 330, Z 265). That folder was deleted with the rest of
the bench, so the originals were moved first - they are NOT regenerable, unlike the Mk2
geometry, and they are the rollback path. Current home:

  ServerStorage.GameCoreBaseline.Originals_consoles_and_monitors    14 models
      the 7 pre-rebuild desks (incl. ORIG_CBLaserConsole_DUPLICATE_DEAD)
      plus the 7 ORIG_*ControlRoomMonitor monitors
  ServerStorage.GameCoreBaseline.Superseded_Mk2_preLEDBar
      the 5 MK2PREV_* desks, kept as the Phase 21 comparison set
  ServerStorage.GameCoreBaseline.ReactorCBLs_original
      pre-existing, the CBL originals

To roll an original back, PivotTo() it out of the archive with its GameCoreParkedPivot.
See DECISIONS 67.

HDEFGenerator is NOT a desk: it is a 7.38-high cabinet on a 1.31 x 4.60 footprint,
so it is built by its own cabinet builder rather than the shared hull. It still
answers the shipped dot paths (PowerLever.ClickPart, EmergencyControl,
PowerCell1..3) and needed a +90 degree Y rotation on install, because the
facility original faces world -X and the Mk2 faces local -Z.

Measured against the shipped originals (world AABB, corner method) no Mk2 desk is
deeper than the desk it replaces, so none protrudes into the operator walkway:
Main -1.25, Thermal -0.32, CBLaser +0.02, ElectricGrid +0.02, ALT -1.11, HDEF
+0.06. See DECISIONS 42.

## Refreshing the installed desks
The bench can be rebuilt at any time, but the six INSTALLED desks are copies, so a bench
fix does not reach them. RebuildKit has no Install() - the original install was a one-off
script - so the desks are refreshed by transplant instead. Per desk: park the live model
as MK2PREV_<name> with its pivot recorded in the GameCoreParkedPivot attribute, clone the
corrected bench MK2_<name>, rename it to the live name, re-parent it to Workspace.Consoles,
then anchor it on the live desk.

ANCHOR ON THE BOUNDING BOX, NOT ON THE PIVOT. This section used to say to call
Model:PivotTo(the recorded pivot) and that it "sets position AND rotation exactly, so no
orientation solver is needed". That is only true if both build generations agree on where
the pivot SITS inside the model, and they do not. Measured 2026-09-21: the aggregate
pivot-minus-bounding-box-centre matched on three desks and differed on ThermalConsole by
0.31 studs and ALTReactorConsole by 0.16, so a blind PivotTo would have mis-placed two of
five desks. The correct anchor is convention-independent and also carries rotation:

  local d = liveCF * new:GetBoundingBox():Inverse()
  new:PivotTo(d * new:GetPivot())

All five landed at a measured centre delta of 0.000 on every axis, and the oriented-corner
depths still reproduce DECISIONS 42 to the centimetre. See DECISIONS 68. Generalised: any
future transplant between build generations compares a bounding box, never a pivot - a
pivot is an authoring choice and is allowed to move between generations, the bounding box
is a property of the geometry and is not.

Note the parking folder Workspace.Rebuild.Previous only exists while the bench does. With
the bench cleared, park predecessors under ServerStorage.GameCoreBaseline.Superseded_*
instead, as the Phase 21 pass did. Verified after the last refresh: GameCoreMk2 true on 6/6, EndHazard 2 /
EndHazardBar 12 on the five desks, 0 visible caution decals, and every SurfaceGui at
LightInfluence 1.

ALT and HDEF were refreshed a SECOND time, when ART_DIRECTION 3.2 was closed. An earlier
line here read "the bright collar pair on 6/6"; that was a colour probe over every part
carrying that name, not a count of brightened button bezels, and it overstated the
situation - ALT had no bezel of any kind and HDEF's was coloured as dark as the plate
behind it. Measured on the six installed desks now, by the precise names:
  Main 2/2   Thermal 2/2   CBLaser 3/3   ElectricGrid 1/1   ALT 2/2   HDEF 0/0
    -> 10 CollarOuter/CollarInner pairs across 5 desks.
HDEF carries no CollarOuter/CollarInner at all; its bright ring is a single part named
Collar, sitting at the "light" value. ALT's pair stacks along Y, not X, because its button
sits on a horizontal deck rather than a vertical face; HDEF's collar was recoloured rather
than moved, so the cabinet depth DECISIONS 42 pinned is untouched. See PROGRESS Phase 19f
and DECISIONS 51.

Watch the name: every desk also carries dark structural Collar sleeves at Metal 0.235
(Main 4, Thermal 10, CBLaser 3, ElectricGrid 2, ALT 2), so grepping for Collar over-counts
badly. Only CollarOuter / CollarInner mean "button bezel".

Workspace.Rebuild.Previous is a PARKING SPOT, and a model has to be MOVED into it, not
just re-parented into it - re-parenting alone leaves it standing in the facility. The six
predecessors were briefly left exactly on top of their replacements that way; they now sit
at Y 330 / Z 320, while the shipped originals are parked at Y 330 / Z 265. See
DECISIONS 50.

REBUILDING IN PLACE INSTEAD OF TRANSPLANTING (2026-09-23). The transplant route above needs
Model:PivotTo, and this environment refused it: PivotTo(CFrame) threw "invalid argument #2
(Vector3 expected, got CFrame)" even when handed the model's own GetPivot() offset, so the six
installed desks were refreshed a different way - rebuild in place. RebuildKit's builders are
LINEAR in their origin CFrame, so exact placement needs no orientation solve at all:

  build a throwaway probe Model at CFrame.new() with the same builder
  read the probe's GetBoundingBox() position, call it p
  destroy the probe
  rebuild the real model at CFrame.new(liveCentre - p)

That is exact, because the only difference between the probe and the real build is the origin
offset, and it lands the new desk on the old desk's bounding-box centre with no rotation
assumption whatsoever. Measured drift on all six: 0.000 on every axis. It also removes the
transplant step entirely - nothing is parked as MK2PREV_ and no clone is made, so the Superseded_*
archive grows only when a build generation is retired on purpose.

The rebuild destroys and recreates, so it is only safe where it is SELF-SCOPED: BuildAll removes
only children carrying GameCoreRebuild and warns about any other child it finds, which is the
guard that keeps Workspace.Rebuild.Models.LaserBench (2,869 parts, no GameCoreMk2) intact.

Verified after this pass: GameCoreMk2 present on 6/6, and every binding-critical name held its
count exactly - 30 ClickParts, 21 LeverUnions and 39 NeonParts across the six, identical before
and after. Neither the installed desks nor the builders create ClickDetectors (0 on both);
ConsoleBinder creates them at runtime, which is why a rebuild cannot strand a binding. See
PROGRESS Phase 37.

## Rebuild markers
Every Mk2 model carries the attribute GameCoreMk2 = true. It exists because the install
moved the rebuilt desks into Workspace.Consoles UNDER the originals' own names, so a name
can no longer distinguish a rebuild from the desk it replaced. RebuildKit.PlaceReference
therefore looks up ORIG_<name> in an ARCHIVE and only falls back to Consoles for a model
without the attribute - otherwise the bench would clone an Mk2 as its own reference and
silently compare a thing against itself. See DECISIONS 49.

It resolves the archive from a CANDIDATE LIST rather than one hardcoded path, in order:
Workspace.Rebuild.Originals (where they used to live, so the module still runs against a
place saved before the 2026-09-21 cleanup), then ServerStorage.GameCoreBaseline under
either Originals_consoles_and_monitors or Originals. The old single-path lookup was broken
BY that cleanup, and would have fallen through to Consoles - arming exactly the footgun
DECISIONS 49 exists to prevent. Verified after the fix: 6 of 6 REF clones resolved, part
counts matching the archive exactly (279 / 382 / 316 / 167 / 310 / 545). See DECISIONS 67.

RebuildKit depends on no external texture. Its only one, the facility caution decal
(rbxassetid://267233089), is set to Transparency = 1 in all 5685 of its uses across this
place and a clone-vs-original control shows the originals carry that value too, so the
shipped game never renders it. The desk end hazard is built as geometry instead - a brass
plate with six near-black bars 0.012 proud. See DECISIONS 47.

## SurfaceGui lighting (labels vs screens)
Every SurfaceGui a rebuild creates starts at LightInfluence = 0, which in Roblox means
"always fully illuminated": the plate ignores scene lighting AND exposure compensation and
renders flat white under any grade. Whether that is a bug depends entirely on what the plate
is, and the answer is not the same for both:

  LABELS  -> LightInfluence 1. A painted label plate is a surface like any other; at 0 it
             renders flat white under any grade. The first Mk2 desk install shipped 121 such
             plates at 0, which is what made the installed desks read washed out while the
             floor beside them did not. Fixed in DECISIONS 45.
  SCREENS -> LightInfluence 0. A monitor is an emissive light source, not a painted surface.
             All 7 shipped monitor MonitorUIs are at 0 and that is correct - a screen that
             dims when the room lights go out is the wrong behaviour, and the room's exposure
             grade has no business being applied to pixels meant to be self-lit. Earlier
             revisions of this file told the monitor rebuild to carry 1 forward; that was
             wrong and has been withdrawn.

Rule: labels 1, screens 0. See DECISIONS 57.

## Verification

Workspace.GameCoreSelfTest runs the whole chain headlessly and prints a JSON
report. It disables itself after one run; re-enable it to re-run.

NOTE: Studio's require cache survives script Source edits made through plugins.
Always verify gameplay changes in a fresh Play session, not via Edit-mode
execute_luau, or you may be testing stale modules.

## Rebuild kit

The geometry rework is additive, and it lives in its own assembly apart from the
gameplay tree. Nothing under `ServerScriptService.GameCore.Rebuild` is required by
a system, and no generator touches a name, a CollectionService tag or a
ClickDetector.

  RebuildKit  -- the console Mk2 builders: six desks, 957 pieces, 66 controls
  LaserKit    -- the CBL laser refinish: three machines, colour plus accents
  LaserFrame  -- the CBL laser frame: 125 parts per machine, ribs, rails and ducts, additive
  ShellKit    -- the control-room shell CORRECTION: recolour plus material fix, builds nothing
  ControlRoomKit -- the control-room floor deck (88 pieces) and its cyan walkway accent

### LaserKit is a refinish, not a rebuild

Each `Workspace.ReactorCBLs.Reactor_Laser_Mk3_n` carries 210 MeshParts, 100
UnionOperations, 485 Wedges and 251 live Texture/Decal children. There is no
procedural replacement for any of them, so a primitive rebuild would delete the
authored detail and put boxes in its place. The defect was chromatic instead: the
machine was 103 distinct greys and had no emissive accent at all. `Refine` keeps
every part where it is and changes what it looks like.

  Recolour  -- zone tone by station along the barrel, plus a deterministic +-9
               jitter so the plating does not read as one flat value
  Accents   -- seams, brass collars with bolt circles, cyan inlay strips that
               follow the hull, status lamps, louvre stacks, and the lit aperture
               ring and lens at the muzzle

Each machine gets one generated folder, `Mk2Accents`, destroyed and rebuilt on
every run. It is parented to the laser model itself, and no part inside it is
named after a control, so `ConsoleBinder` and `ControlVisuals` never see it.

### LaserFrame is a frame, not a second hull

LaserKit fixed the lasers' colour and left their shape alone, so the machines stayed long
round barrels beside rectangular, bevelled, brass-banded Mk2 desks. The obvious fix is
wrong: a new hull is a delete plus a build, and there is no procedural replacement for 210
authored MeshParts. `LaserFrame` is therefore additive - 125 new parts per machine in one
folder, `Mk2Frame`, and nothing else.

  Build        -- 7 octagonal rib stations, 4 brass bolts per rib, flank rails in 4 bays,
                  top and bottom ducting per bay, hazard bars on the end ribs, and a brass
                  title plate reading CBL-1 / CBL-2 / CBL-3
  Radii        -- cast, not guessed: every rib corner sits 1.70 studs outside the hull as
                  measured by LaserKit's own SurfaceScanner, swept at 16 points per station
  DeleteFrame  -- removes Mk2Frame from one machine; RevertAll does all three
  BuildAll     -- idempotent across all three, and each machine is built under pcall so one
                  failure does not stop the other two

The coil bay and the muzzle bay carry no rails on purpose - a straight line across a
12.7-stud station would need radius 14 and would read as a hoop rather than a rail. The bay
test enforces that rather than trusting the comment: it casts the mid-span silhouette and
refuses any bay whose middle bulges more than 1.00 stud past its ends.

The folder is built unparented and attached only when complete, so a mid-build throw leaves
the machine exactly as it was. No part is renamed, deleted or moved, no ClickDetector is
created, and every part is CanCollide / CanQuery / CanTouch false, so the frame cannot be
clicked or collided with and gameplay is untouched.

### The core states its own condition

`Rebuild.CoreKit.Glow(state, instant)` rotates the hue of the 57 Neon parts the kit made, and of
the CORE point light, from cyan toward violet across the four core states. It is driven by
`ControlVisuals.driveCore()` - folded into a system that already runs every tick rather than
registered as a 26th system - and it is a pure observer: it reads `GameState.Reactor.CoreState`
and writes colour, nothing else. Its only shadow state is one attribute per part holding the
authored colour, which is also what keeps a re-run idempotent, and `hsvShift` returns its input
untouched at zero shift, so the normal band stays byte-identical to the authored palette.

### Radii come from a raycast

`SurfaceScanner` casts a ray inward from outside the machine at the exact station
and angle a detail sits at. A statistic over the part list answers a different
question - the maximum over the whole machine lands outside the twelve radial
Struts at radius 9.58, and a percentile lands buried inside the shell. See
DECISIONS 78.

`RefineAll()` is idempotent. Run it twice and the colours are byte-identical and
the accent count is 106 both times, so it can be re-run after a mistake.

### The main monitor's diagram is live

`ReactorDiagramFrame` and `CoreDiagramFrame` were authored as static art and are now
driven every tick by `MonitorService.UpdateDiagram`. It is a PURE OBSERVER: it reads
`GameState` and writes nothing, which puts it in the same class as the log writer and the
forecast writer. Nothing about the simulation changes because it exists. See DECISIONS 81.

The two intensity images are driven by WIDTH, not by a fill texture, because both shipped
with a zero-height box parked one frame-height down and two frame-widths right of the
panel. Anything that reads them has to re-anchor them first.

Two things to know before touching this panel:

  GraphFrame1        reactor energy intensity, normalised against the current shift quota
  GraphFrame2        P. E. A. extraction - note the authored order, NOT the diagram order
  GraphDetailThingy  a dead UniversalSynSaveInstance comment stub, not a live animator

The Equinox override applies to the whole diagram - graphs, beams, core, labels and the
warning - because purple for the duration of the event is the one diagram colour the Wiki
names explicitly.

### The diagram's authored colours are bytes

`ReactorDiagramFrame` was authored with `Color3.fromRGB`, so a value read back and re-used
as a rounded decimal drifts off it. The ring family is `fromRGB(40,40,40)`, which reads as
0.15686 rather than 0.16; the core image and the three CBL labels are `fromRGB(80,80,80)`,
which reads as 0.31373 rather than 0.31; the idle CBL beam is `fromRGB(170,208,255)`.
A restore that lands on the rounded decimal is a regression, not a neutral result.

### The seven monitors

All seven were re-checked under the Phase 21c grade (PROGRESS Phase 25). Both trim
members are authored: a Metal band at 75,75,76 with a Plastic bead at 186,186,188 sitting
0.135 studs in front of it. The light border in a capture is the bead, not a mismatch.
The `Screen` part stays Neon 17,17,17 - a flat self-lit backing is the right look for a
screen and the four SurfaceLights under each screen are built on that part. Every screen
must keep `SurfaceGui.LightInfluence = 0`, which is the opposite of the console text
plates at 1. See DECISIONS 80.

### PaletteKit - the facility skin

`ServerScriptService.GameCore.Rebuild.PaletteKit` is the facility-wide appearance pass that
follows ShellKit. ShellKit restyled the control-room shell; PaletteKit restyled everything
else. They deliberately share a threshold (luminance 120) and a target (100,100,100), so
they cannot fight over a part.

The rules: retire the ReactorWallPlate skin onto FacilitySteelPanel, and pull near-grey
structural tones above 120 down to 100,100,100. Exempt are Neon, the lamp names
(`NeonPart`/`Indicator`/`Lamp`/`Glow`/`Light`/`LightPart`), content (`TextPart`,
`FloorTextPart`, `Line`, `Text` by name, or any part carrying a Decal or a Texture) and
anything with hue. Floors keep `FacilityFloorPlate`.

`PaletteKitOrigin` holds `r,g,b|tostring of Material|MaterialVariant` on every part the kit
writes, so `RestoreAll()` is exact and `RestoreFaced()` can undo just the content subset.
`RestretchChunk(limit)` is the entry point for a live run: a single pass over 96,483 parts
freezes Studio, and the chunked form needs no cursor because a part already inside the
palette returns nil from `decide`.

Two facts this module records because they cost real time. A MaterialVariant with no
ColorMap is only a rename of its base material, so retiring a skin is a real visual change.
And artwork does not protect itself from the skin underneath it, because a Texture
composites with the base. See DECISIONS 125 to 127.

### Parking an original facility unit

An original leaves Workspace for `ServerStorage.GameCoreBaseline.Originals_facility` and is renamed
`ORIG_<Name>`. Four attributes are copied from the shipped entries rather than invented, and the
park is only complete when they are written: `GameCoreParkedName` (the original leaf name),
`GameCoreParkedFrom` (the original full path), `GameCoreParkedPivot` (the original pivot, as a real
CFrame attribute) and `GameCoreArchivedFrom` (the archive bay it landed in - the bay, not the
source; both shipped examples settle this).

`ORIG_MedicalDispenser` is the first entry, parked in Phase 44. The archive holds the original; the
live path holds nothing until an Mk2 is installed under the original's own name, which is how the
consoles and monitors were replaced.

Two things to know before parking the next unit. `RebuildKit.PlaceReference` probes only
`Originals_consoles_and_monitors` and `Originals`, so `Originals_facility` is not yet visible to it.
And `FacilityBridge` will warn once per boot for a mapped unit that is parked - that warning is the
per-unit list of what still needs an Mk2, and it clears when the Mk2 lands. Do not add an archive
fallback to silence it: for a unit the bridge actually drives, a ServerStorage instance accepts
`Light.Enabled` and `Sound:Play` and does nothing. See DECISIONS 128 to 130.

## The Rebuild place

A second place, `131274481205639`, holds the original facility's geometry reassembled at
its own world coordinates - the chamber walls, the core column, the CBL lasers - so a
rebuild can be compared against the original one part at a time. It is not the remake's
place: nothing under `GameCore` runs there. Phases 75 to 77 are the assembly log.

### `Workspace.Scene.LaserPortGimbal`

A `Script` shipped from `_tools/laser_port_gimbal.luau`. In Play mode a click on the base
plate cycles the emitter head through five poses and fires a real beam: a Neon cylinder
re-laid every frame from the lens's live CFrame, raycast so it stops at the first thing it
meets, with a glow and an impact marker. `_tools/apply_laser_port_materials.luau` is the
separate colour pass - the meshes carry flat colour factors only, and Roblox's importer
has no per-face material slot, so all eleven parts land identical grey Plastic.

Four things here were measured rather than assumed, and all four are silent when wrong:

  - The joint turns about the **recovered node origin**, not the MeshPart's `Position`.
    Studio's importer re-origins every part somewhere inside its own primitive, so
    `origin = part.CFrame * CFrame.new(-row.off * k)`. Turning about a guessed point does
    not error - the port still moves, it sweeps about a line through nothing.
  - The muzzle direction is the **lens part's own local -X**, not a typed-in angle. The
    lens is the one primitive thin along its X, so that axis *is* the optical axis.
  - The glTF import landed **1.6943x** design size, uniformly: `1.6943 = 10 / 5.902`.
    Roblox's glTF importer reads 10 studs per file unit; the FBX path honours the 5.902
    the files were written at. Because it is uniform the port still assembles and every
    joint works - it is just ~70% larger. Prefer the `.fbx`.
  - Per-frame work lives in an exported `M.stepBeam(rig)` rather than inside the Heartbeat
    connection, because the plugin VM answers `Heartbeat:Wait()` and then never runs the
    callbacks it was handed. Anything that exists *only* inside a connection cannot be
    driven from the only VM available, and `Instance.new("Part")` is born at the world
    origin - so the beam's first frame is placed synchronously in `fire()`.

See CLAUDE.md 0.19, DECISIONS 263 to 266, PROGRESS.md Phase 83.

### `ChamberWall24` - the 18-sided ring, widened to 24

Built in Blender by `_tools/blender/chamber_wall_24.py`, verified by
`_tools/blender/chamber_wall_24_check.py` (76 checks, 0 failed, on both the `.fbx` and the `.glb`;
four mutations each turn their own named assertion red). The colour pass
`_tools/apply_chamber_wall_materials.luau` is **obsolete** - it coloured the *imported* asset for the
two builds that are no longer in the world; the material is set in Blender now, and the import is the
operator's.

**The deliverable is a Blender reference, and the operator does the join himself** (Phase 89).
His instruction: "take that 18-gon into Blender and do the join there, I will use it as a reference
and build it myself". That supersedes Phases 87 and 88, where I built it inside Studio - first as a
single MeshPart, then as 66 Parts. **Neither is in the world now**; the 66-Part model is parked at
`ServerStorage.ChamberWall24_mesh_20261004` (the MeshPart) and `ServerStorage.Wall24_import_20261004`
(the operator's own manual drag, 1.0769x oversized and 3 studs short of joining).
Phase 89 deleted nothing. `docs/TODO.md` 3.5 and `docs/SNIPPETS.md` 5.20 carry the details.

**What he rejected, and why it was a reading error rather than a measurement error:** the Phase 88
wall put the collar's *outer face* on the ring's **apothem** (63.7120), so the ring's 18 **corners**
(64.6951) stood proud of the wall. Phase 88's own comment measured that shoulder as 0.3002 studs and
recorded it as intentional. But "最外围" is the **corner** radius, and a regular n-gon has two radii:
the face plane (apothem) and the corners (circumradius), differing by `1/cos(pi/n)`. Every one of
Phase 88's 5040 raycasts passed, because a raycast asks "is the radius right" and the mistake was
"**which** radius" (CLAUDE.md 0.18, fifth face; DECISIONS 293).

**The corrected join, and it is provably minimal.** A concentric regular m-gon of inradius `R`
contains a concentric regular n-gon of circumradius `R'` iff `R >= R'`, so putting the wall's inner
face plane at `R = R' = 64.6951` is the *smallest* wall that does not intersect the ring - it touches
the ring's corners at six azimuths (0 + 60k, because the 24-gon's vertices are at 0 + 15k) and stands
off by at most 0.9837 studs at the ring's face planes. The alternative - putting the 24-gon's
*vertices* on the ring's corners - gives an inner apothem of 64.1514, and the ring's corner at
azimuth 20 (64.6951) then pokes through it by 0.48 studs. The 3:4 rule is `3 * 20 = 4 * 15 = 60`:
three ring panels and four wall panels per 60-degree sector.

The target is the platform rim in The Reactor [Rebuild]: `Workspace.Folder.Folder.Folder.18`, an
18-sided ring nineteen parts long, apothem **63.7114** with corners at **64.6951** and a **vertex** on
+X (1440 inward raycasts at 0.25 degrees, zero misses; the ratio 1.015439 matches `1/cos(pi/18)` =
1.015427). It sits flush on the existing platform top plane, `y = 47.400`.

Three things are measured and one is chosen, and the code keeps them visibly apart (DECISIONS 274).
Measured: the inner ring's apothem, its vertex phase, and the platform top plane. Chosen: the
outer apothem and the three heights - so the wall is a 13.2-stud parapet with a 3.3-stud overhang,
which is a taste call, not a reading.

Four things here were measured rather than assumed:

  - **Roblox MeshParts cannot bridge two open rims with different vertex counts.** Going 18 to 24
    needs 18x2 triangles per surface computed by hand; there is no operator on the Roblox side that
    will do it, because an imported mesh is a finished triangle soup. So the join is built where the
    operator exists, and the band is the deliverable rather than a by-product.
  - **`bmesh.ops.delete(..., context="FACES_ONLY")`** - the default takes edges and vertices with the
    face, and the ring you were trying to expose is one of them. The failure looks like
    "Bridge Edge Loops did nothing".
  - **The gap between the two rims is not slack, it is the bridge.** If they were coplanar the 42
    triangles per surface would all be zero-area - invisible, while "42 faces" still passes.
  - **The rims are named by height, then by radius within the pair**, and `bridge_loops` will happily
    pair the wrong two and return a valid mesh. The build asserts the rim count and sizes before
    bridging and the band's two edges after; `--wrong-pair` is the mutation that proves the
    assertion is load-bearing.

**Import the `.fbx`, never the `.glb`**: Roblox's glTF path reads 10 studs per file unit while the FBX
path honours the 5.902 these files were written at, so the glb lands **1.6943x** too large.
Placement: bottom centre to `(-12.200, 47.400, -85.362)`, **scale 1.0**, no rotation, expected
`138.58 x 13.85 x 138.58`. The phase needs no correction - the 18-gon vertex set (0 + 20k), the
24-gon vertex set (0 + 15k) and the panel set (10 + 20k) are all invariant under a 180-degree
rotation, which is exactly what the FBX importer's `(x,y,z) -> (-x,z,y)` is. The reference file also
carries the ring itself (`ChamberRing18_ref`), deliberately **unbevelled**: the plate's top edge is
the thing being joined to, and bevelling it insets the cap by 0.05 and makes the measured corner read
64.6435 instead of 64.6943. The instrument is not allowed to round off what it measures.

**Three facts about the checker worth carrying.** It re-imports the exported file and reads it back,
so the build loop is never the evidence. It normalises shapes by dividing **each side by its own max**
- the first version of the colour script divided both sides by the scene's widest part, which cancels
only when the import happens to be at design scale and refused all four parts at 1.6943x while
printing ratios identical to the design table (DECISIONS 275). And it **exits 1 on failure only if it
reaches its own exit** - measured on Blender 5.1.2, an uncaught exception under
`--background --python` exits **0**, so a crash and a pass were byte-identical at the shell until a
`try/except BaseException` was added. Related: `all([])` is True and `max(())` raises, so any
assertion whose subject is a *missing* thing passes vacuously or dies silently; guard with `bool(x)`.
Mutations must be written `--python s.py -- --flag`; with `--python s.py --flag` Blender treats the
flag as a file to open, complains, and then **runs to completion anyway** (DECISIONS 295/296).

`_tools/blender/transition_pillar.py` is the same family of work - an 18-sided base bridged to a
24-sided top - and is likewise built and verified but not imported. See PROGRESS.md Phases 84 and 86,
DECISIONS 267 to 277.

### `RingBridge18_24` - the same join at unit scale, to the operator's own triangle list

Built by `_tools/blender/ring_bridge_18_24.py`, verified by
`_tools/blender/ring_bridge_18_24_check.py` (**53 checks, 0 failed**, split evenly across the `.fbx`
and the `.glb`; six mutations each turn their own named assertion red). Delivered to
`D:\BlenderRobloxTestProjects\RingBridge18_24\`.

**This one is a specification, not a scene reading.** For Phases 84/86/87/88/89 the radii came out of
the world (63.712, 64.695, 68.000). Here the operator gave a numbered spec and it is abstract:
an 18-gon of radius 0.8 at z=0, a 24-gon of radius 1.2 at z=1, both end faces kept as n-gons, red
bridge triangles, blue end faces. **His list starts at "3." - items 1 and 2 never arrived**, and they
were not guessed. He also wrote the triangulation out line by line: six groups of three small
corners and four large ones, seven triangles each, `A0-B0-B1`, `A0-A1-B2`, `A0-B2-B1`, `A1-A2-B3`,
`A1-B3-B2`, `A2-A3-B4`, `A2-B4-B3`.

**"radius 0.8" has two readings and both are printed.** A regular n-gon has a circumradius (to the
corners) and an apothem (to the face planes), differing by `cos(pi/18)` = 1.5%. The build takes the
circumradius - it is what you get when you place vertices on a circle of radius r, and the only
reading under which "the two rings are coaxial on one circle family" carries content - and prints the
apothem (`0.787846 / 1.189734`) beside it. That is Phase 89's lesson used forwards: the error there
was choosing the wrong one of two radii while every check measured the other (DECISIONS 293/297).

**42 is forced by Euler, so Euler cannot validate the list.** For an annulus with `a` and `b` boundary
vertices, `chi = (a+b) - (3F+a+b)/2 + F = 0`, so `F = a+b = 18+24 = 42`. *Any* six-groups-of-seven
scheme satisfies it. What the checker can validate is his **42 relations specifically**: it rebuilds
each one as a position set and looks for a face with exactly that set. `--fan` (bridge via
`bmesh.ops.bridge_loops`) produces a valid, closed, 42-triangle band that is *not* his - and reddens
that assertion, which is the whole reason it exists (DECISIONS 298).

**His seven relations are not consistently wound - measured: 12 of the 84 interior edges run the same
direction twice.** It does not matter here, because the solid is closed and `recalc_face_normals`
derives outward from the geometry alone. It would matter if he builds the band **open** (no caps, or
one cap): then there is no inside to derive from and those 12 faces come out flipped, which is
invisible in the viewport with backface culling off. Same finding as Phase 84's `--twist` negative
result (DECISIONS 265/300).

**The two formats do not ship the same asset.** FBX has a polygon type and its importer rebuilds
`1 x 18-gon + 1 x 24-gon`; glTF has none and ships `16 + 22` triangles. So item 4's "the end faces are
kept as n-gons" is literally true in the FBX and only true *by area* in the glb. The export-side
assertion is therefore the format-independent half - the cap spans all 18 (resp. 24) corners and has
the ring's full area, which a partial fan would fail - and the shipped face count is printed rather
than asserted. Bridge faces are identified by **material slot, never by side count**: `len(f) == 3`
counted glTF's 38 cap triangles too and read "80 bridge triangles" (DECISIONS 299).

**Import the `.fbx`** (the glb lands 1.6943x, as always). Radius is in scene units, so the FBX path
(`global_scale = 1/5.902`) gives **`14.1648 x 14.1648 x 5.9020`** studs. No Studio import happened -
there is no upload credential on this machine - so that size is computed, not measured. The material
assertion reads the colour back **out of the file** (Principled Base Color, falling back to
`diffuse_color`) rather than trusting the Workbench render, which reads the other field: a picture can
be entirely right about a material that exported white (DECISIONS 300). Volume is confirmed two
independent ways - prismatoid `3.111157480` vs a divergence sum over the shipped faces `3.111157526`,
delta `4.53e-08` - and the tolerance is `1e-6` relative because **Blender stores vertex coordinates as
float32**, so a 1e-9 tolerance tests the storage format, not the geometry.

See PROGRESS.md Phase 90, DECISIONS 297 to 302, docs/SNIPPETS.md 5.21.
