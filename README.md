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

### World health check, and the Phase 96 restore

Phase 96 undid a lag-reduction "park" that had moved roughly 982 Workspace roots into
`ServerStorage.ParkedFacility_20261006` and, on the way, merged same-named roots into one.
The merge is what broke the control room - it destroyed *grouping*, which is what held the
room together. Two facts make that recoverable only in part:

- Roblox allows duplicate sibling names. Lua's `Parent` assignment never renames, so 109 roots
  named `Model` coexisted happily; the merge was unnecessary as well as irreversible.
- `Model:GetPivot()` survives child removal, so the 45 emptied shells still report their
  original world pivots - the only pointer to what was lost, and a *point*, not data.

Everything else was reconstructed and measured. Current numbers, all read from the place:

| Check | Value |
|---|---|
| `Workspace` BaseParts (+ `ParkedFacility`, now empty) | **91,905** |
| `Workspace` top-level roots (Part / Model / Folder) | **1,210** |
| Control room seal - horizontal 720-ray fan from `(113, y, 0)` at y 281.5 / 283.0 / 286.0 | **0 / 2160 leaks** |
| Ceiling above the console (upward rays from y 280.5, 20 probes) | **20 / 20 hit**, y 288-298 |
| `MovingParts.ControlRoom{L,M,R}Shutter` | one each - `RoomShell`'s three literal paths resolve |
| Scripts mentioning `ParkedFacility` / the merged containers | **0** |

Two freshly merged hallway containers were split back by index with three guards (sum of blocks
equals child count; the first block is still in append order; enough same-named empty shells to
receive the rest) and then re-measured geometrically - four contiguous 15-stud blocks,
x163..178 / 178..193 / 193..208 / 208..223. Four things could **not** be restored and are
disclosed rather than guessed: the 45 merged `Model` roots (476 children, 1,539 parts), 53
nodes whose original nesting is not recorded, the `Meshes` grouping folder (its contents are
present as loose nodes - grouping lost, nothing visible lost), and 236 nodes left at the
Workspace top level. None of these change rendering or physics; world CFrames are untouched.

Method and per-ray evidence: `PROGRESS.md` Phase 96. Rules: `docs/SYSTEMS.md` section 2.17
(how to answer "did I just break the world"), `docs/TODO.md` section 3.7 (the moving-things
policy and the four outstanding accounts), `CLAUDE.md` section 0.22, `DECISIONS_2.md` 334-340.

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
- FacilityCascade the world's half of the start-up chain (Phase 122): the seven lamp
               groups dim and re-light in waves, the three CBLs charge, spin up and fire,
               the chamber alarm flashes for ~11 s, and the core goes critical - all of it
               riding the engine's own `StartupSteps` (beats at steps 2/11/14/16), never a
               second timeline. It is the one adapter driven from Heartbeat directly
               (`Step(dt)`) rather than the one-second logic gate, because its ramps are
               continuous. Its baseline is READ FROM THE WORLD, so a probe that lights the
               world in Edit mode destroys it - recover with `_tools/cold_baseline.py`,
               see `docs/SNIPPETS.md` 5.29 and SYSTEMS.md 2.22.

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

## Ending a shift
A shift ends two ways: the quota is met (`phase = Report`) or the engine fails the plant
(`phase = Failed`, e.g. `Power extraction assembly overload` when `peaStress` reaches 100).
Past either ending `Engine:Command` refuses every control with `'Shift ended'` - and that refusal
is a server-console warn, so a player sees the shift simply stop.

That was the whole problem until Phase 124: `StarterGui.ScreenGui.EndShiftHandler` has been in
this place all along and had **never once appeared**, because its two ends were never connected -
nothing fired `ReplicatedStorage.EndShift`, nothing listened to `ReplicatedStorage.MiscEvent`
(which is the remote that screen actually fires), and nothing fired `ReplicatedStorage.ResetEvent`.
`SSS.ReactorBackend.EndShiftBridge` is the missing transport: an output adapter on the same terms
as `LogPanel` (holds no state, reads `engine.state.phase`), publishing once per ending per player,
with every gate left to `Engine` - a client can only ask for a transition the engine is already
willing to make. `StarterPlayerScripts.EndShiftResume` is the other half: the original got the
player out by *teleporting* them, and a respawn re-clones `StarterGui`, which is what put the
interface back. This place has no teleport and no lobby (no `TeleportService` call exists anywhere
in it), so that script closes the screen itself and restores visibility from a baseline **captured
off the world at boot**. See SYSTEMS.md 2.23 and DECISIONS_2 516-518.

THE MONEY ON THE REPORT IS ZERO, AND THAT IS A TRUE STATEMENT. This build has no economy, so the
per-stat money lines are sent **empty** rather than zeroed - the screen appends no stat row at all
for an empty table - and the total lands on the screen's own authored zero-total branch (grey money
text and ` ... Good Job`). `OT` is `HH:MM.mmm`, not `HH:MM:SS.mmm`, because that is the shape the
label was authored with. The acknowledge button holds `'Lobby'` by default, and since there is no
lobby it is rewritten to the engine's own `reset` - refusing instead would answer "the shift ended
and there is no way out" with a console line and no exit. What the screen is genuinely missing is
the economy it reports on; that is `QUESTIONS.md` R4, not a wiring decision.

## Monitor content - the alerts grid and the subspace forecast
`RoomShell` decides which *face* each of the seven control-room monitors shows. Nothing decided
what was *on* those faces, and two of them had been dead since the place was built:
`AlertsControlRoomMonitor`'s 27-row indicator grid and `ForecastControlRoomMonitor`'s deep-scan
announcement. `script_grep` over the whole DataModel returned zero readers for `AlertsFrame`,
`TimeSliceTemplate`, `AnnouncementFrame` and `EFEFrame`.

`SSS.ReactorBackend.AlertsPanel` fills the grid. Each of the 27 tiles is a grey plate with a
black label and, at ZIndex 0 behind it, a full-size child named `Frame` whose
`BackgroundColor3` is that row's category colour - toggling that one child's `Visible` is the
entire mechanism, and the original's recordings never wrote any property on this monitor except
that one. The rows come from the in-game manual (`Workspace.Consoles.ElectricGridConsole.
DRMScreen`, the `AlertsFrame.{General,Moderate,Major,Malfunctions}Frame` pages), so the
thresholds are the originals': 400 GW/H for high energy output, 75% for P.E.A stress, 400F for
temperature fluctuation, ~6000F for stallout. Rows 1-9 are the start-up family and light in any
phase; rows 10-27 are live conditions and only count while the reactor is Running or Stopping.
Two rows - `ENERGY FLUCTUATION` and `P.E.A MALFUNCTION` - have no engine counterpart this build
models, so they are left dark and printed at boot rather than aliased onto something that only
looks like them (DECISIONS_2 522). The refresh is signature-gated on the 27-bit lit set, so a
quiet second writes nothing at all.

`SSS.ReactorBackend.ForecastPanel` plays the deep scan, transcribed to the poll from the
recording at `Data/originalwatch/260930-200834`: announcement at +0.00, beep at +3.35, verdict
and ping at +5.04, ping off at +9.37, announcement off at +12.89, timeline off at +14.63. The
verdict is not a fixed string - the only future subspace event this engine models is the
Equinox, so the scan projects that clock and reports whether it lands inside the facility's
horizon (`HADEN THRESHOLD BREACH ~3:15 AM` in red, or `ANOMALY DETECTED, MARGIN ~...` in
yellow). The clock map itself is ours, not the capture's, and is labelled as such. The EFE
banner is on **all seven** monitors - which is the manual's own words, "when an EFE is about to
occur, all monitors will display a warning" - and it carries its own countdown, because the
capture's `BannerSeconds = 10.25` is longer than the announcement timeline it used to be bound
to (DECISIONS_2 524).

`AlertsControlRoomMonitor` was also the one monitor with **no `EFEFrame`**, so the manual's
"all monitors" would have skipped the alarms screen. It now has one: a clone of the full-width
variant, which is what its own `MainMonitorFrame` uses, byte-identical to the other six. That is
a restoration of a symmetric element, not new content, and it is purely additive - nothing
existing was moved, renamed or deleted (DECISIONS_2 523).

Both were first verified in Edit mode by requiring the real modules against the real instances and
reading back instance properties - 27 `Frame.Visible` values, the announcement's text and
colour, three `Sound.Playing` flags and seven `EFEFrame.Visible` flags - which needs no Play
session at all (DECISIONS_2 526, SNIPPETS.md 5.32). They have since been verified **in a running
game** as well (Phase 127): four clicked controls drove the chain into `Running` and a per-frame
sampler recorded the deep scan landing on the capture's offsets to within a frame (announcement at
+0.00, beep +3.350, verdict +5.051, timeline +12.900, stop +14.634), and the seven `EFEFrame`s
going visible on one identical timestamp and hidden on another exactly 10.250 s later - a 0 ms
spread where the capture had 70 ms. Two things the live run measured that the config cannot:
`EFEPing` is 3.3493 s long, so it ends itself 0.987 s before `PingOffAt = 9.37` can stop it, and
the deep scan always reaches the breach verdict, because it fires inside `Starting` where
`elapsed` is still 0, so `untilEquinox` is always exactly 720 inside the 900 s horizon
(DECISIONS_2 534/535, QUESTIONS.md R6). See SYSTEMS.md 2.24.

## Monitor content - the four readout screens
Four of the seven monitors - Main, Power, Thermal and Quota - shipped carrying the author's static
placeholders (`NIL F`, `140 F`, `100%`, `0 GW/H`, `11:50 PM`, `524 GW`, `OFFLINE`) and nothing ever
wrote them. The scripts the original used to drive them, the `GraphDetailThingy` family, are empty
in this place - the save tool that produced it dropped server scripts - so the original's
implementation is genuinely unrecoverable and was never going to be ported. What *is* recoverable is
the shape of every reading: `Data/originalwatch/*/changes.log` records each label's observed value
verbatim, so the formats (`%.0f F`, `%.0f PSI`, `%.0f GW/H`), the quotas' crossing into `TW`, and the
two clocks are all read off the original's own recordings rather than invented.

`SSS.ReactorBackend.ReadoutPanel` wires 36 readings: Main's eight-row `ReadingsFrame` (temperature,
P.E.A stress, fluctuation, chamber pressure, **net** output, extraction, radiation, HDEF integrity),
Power's three CBL groups (body temperature, stress, power, a state *word*, and a pressure bar),
Thermal's three reservoir bars and six chamber-fan `ON`/`OFF` labels, and Quota's clock, target,
progress bar and `EquinoxFrame` colours. It writes `Text`, `Size` and two colours and nothing else,
so it is disjoint from every adapter above it - `RoomShell` still owns which face is shown, and the
two write no property in common.

THE THREE BAR FAMILIES DO NOT RIDE THE SAME HALF OF THE `UDim2`. The reservoirs ride `Y.Scale`,
the CBL graphs ride `Y.Offset` as integers 0..100, and the quota bar rides `X.Scale`. `Offset` is an
integer in Roblox and truncates on assignment, which is invisible from the outside - a truncated 0
and an unwritten 0 are the same number, and the first version of this module read back as though it
had never written anything. So the driven *component* is declared per bar in `Config.Readouts.Bars`
rather than inferred from the axis, and `barSize` writes both halves of the driven axis and
preserves the other one whole (DECISIONS_2 549/550).

`ReadingsFrame.StressLabel` is the one reading wired that the original never drove - there is not a
single `StressLabel.Text` write in the whole corpus. It is a real engine field, and the alternative
was a label reading the author's `0 %` for the life of the place. Everything deliberately *not*
wired is printed at boot instead of being left for a reader to notice: the seven colour tints (the
corpus carries every colour but not the predicate that chooses one), the `NET C-PUMP FLOW RATE` bar
(corpus 0..75 against this engine's 0..9 pump-level sum, no ratio), and `REACTOR ENERGY INTENSITY`
(corpus 75/150/250, no clue which state produced any of them). Scaling 9 onto 75 would be a picked
number wearing a measured one's clothes (DECISIONS_2 552).

Verified in a running game: four clicked controls drove the chain into `Running`, the CBL state word
walked its whole ladder (`OFFLINE` → `POWERING` → `FIRING` → `ACTIVE`), and a real click on
`C-PUMP 1 ON BUTTON` left the first reservoir bar at `{1, 0}, {0.333333343, 0}` - a *fraction*
riding `Scale`, which the integer path could never have produced (DECISIONS_2 553). See SYSTEMS.md
2.25, SNIPPETS.md 5.37 and PROGRESS.md Phase 130.

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

### The gravity lens - `_tools/gravity_lens.luau`

A **`ModuleScript` at `ReplicatedStorage.GravityLens`** that builds a **gravitational lens** out of an
`EditableMesh` and animates it **by moving its vertices**, plus a **`LocalScript`** at
`StarterPlayer.StarterPlayerScripts.GravityLensClient` that requires it and calls `start()`. The still
`MeshPart` at `Workspace.GravityLens` (`92, 92, 10.303`, Neon, `-151.10 58.00 71.00`, laid against
`0.4099, -0.4912, -0.7686`) is **no longer the deliverable** - it is the **placement anchor** the client
reads its `CFrame` from before building its own copy and destroying it. The operator's constraint was **do not touch my camera**:
nothing in that file writes `workspace.CurrentCamera`, and no screenshot tool was ever handed a
`camera_position`.

The disc samples a point-mass lens map, `beta = R - rE^2 / R`, so the source plane is inverted
inside the Einstein radius; a Gaussian ring brightens it there, and three clock-driven terms move it -
a swirl that drags the inner rings hardest (0.30 rad / 23 s), a breathe (0.045 / 11 s) and a ripple
(1.5 / 7 s) at 30 Hz. Topology is `64 x 152` = **9728 vertices / 19152 triangles**, against measured
caps of **60000 / 20000** - the triangle cap is the binding one, and `build()` names both so a
too-big topology errors in my own words rather than in the engine's.

Four things here were measured, and **three of them are silent when wrong**:

  - **This Studio's `EditableMesh` is the old, indirection-based API** - a face records *colour ids*,
    and a colour id maps to a `Color3`. It is a **datatype, not an Instance**, so probing a member
    that does not exist **throws instead of returning nil**; every name had to be tried under `pcall`
    and the error text read. `SetColor(vertexId, ...)` replies `Expected Color id, received Vertex id` -
    three separate errors that all describe argument shapes and none of which says "this is indirect".
  - **Colour ids cannot be computed.** They are allocated at first use in face order and **shared per
    vertex** (`f1=(a,b,c)` gets 889/890/891, `f2=(b,d,c)` gets 890/892/891), so `GetFaceColors` has to
    be harvested the moment each face is created. The build's `colourConflicts = 0` is the only place
    that assumption can be falsified - and if it were false the picture would still look right.
  - **`SetPosition` moves the render and not the collision** (Roblox's own docs): physics is a snapshot
    that needs `CreateMeshPartAsync` + `ApplyMesh`. So the whole thing is `CanCollide`, `CanQuery` and
    `CastShadow` false - a black hole that blocks raycasts would be a gameplay change.
  - **Edit is not Play, and a process is not another process.** The `MeshPart` built in Edit mode is a
    still frame; the moving half has to be rebuilt where it is drawn. Source and instance were checked
    by **length *and* a polynomial checksum** (`24695`, `189076020`), never by length alone.
  - **`MeshContent.SourceType = Object` is process-local.** This is the one that produced the operator's
    bug report, in Phase 110. Same instance, same call `CreateEditableMeshAsync(part.MeshContent)`:
    the process that built it returns **9728 vertices spanning `+/-46`**; any other process returns
    **1536 vertices spanning `(0,0,0)..(1,1,1)`** - a **unit cube**, which the renderer paints as the
    unresolvable-content checkerboard sized to the part. A server-built mesh **cannot be drawn by a
    client at all**, and the client is never told no. The fix is not to ship the mesh but to **build it
    in the process that draws it**.

Verification came from three independent channels: a per-vertex read-back at two phases (`t=0` all Y
zero, `t=5.75` Y max **2.838**, with `outerMoved 1.270` / `innerMoved 1.209` matching the motion maths);
the section 5.18 round trip (`MeshContent` -> `CreateEditableMeshAsync`, `worstPositionDelta 0`, colours
within `0.0029` = one 8-bit step, i.e. the mesh quantises colour); and a **colour-field** render pushed
as ASCII PPM through `_tools/receive.py` (crc32 matched on both sides) and converted by
`_tools/ppm_to_png.py`, a stdlib-only encoder. It was written on the belief that **Pillow is not
installed here** - that belief was wrong (see PROGRESS.md Phase 109 and DECISIONS_2 448): Pillow 12.3.0
is installed, in the **per-user** site-packages, and `python -I` - the flag every one of these tools is
run with - strips the user site from `sys.path`, so `import PIL` fails there and looks exactly like an
absent package. The encoder stays anyway: stdlib-only means it runs under `-I` too. The
colour field is rendered separately from a screenshot because `screen_capture` measures the *renderer* -
material, lighting and post-processing included - and the question was whether the *vertex colours* are
right. The one picture that shows it actually moving is a controlled pair: same camera position, same
part position, same module instance (a persistent holder, so `require` hits the module cache), only the
clock changed 5.75 -> 17.25, and `compare_images` reports the internal pattern rotating clockwise.

Phase 110 then closed the gap that the last paragraph of the Phase 109 write-up admitted: the moving
half had never been observed in a running session. It has now. In Play, the shipped path draws a
complete lens (two frames seconds apart show the inner ring rotated), the `MeshContent` round trip
taken twice 1.2 s apart moves a vertex by **0.0072 studs** (matching the configured `SWIRL = 0.30 rad /
23 s` at the throat radius), and at `t+220 s` - about 6600 passes - it is still a complete lens with the
`CreateEditableMesh()` budget reporting `ok` throughout. `passes = 446` over ~15 s is **29.7 Hz**, so the
30 Hz is now a measurement rather than a setting. A slice knob (`CFG.SLICE_STRIDE = 4`: at most 2432
`SetPosition` calls per tick, a full refresh every 0.13 s) ships as **insurance, not as a proven
requirement** - an earlier checkerboard on a client-built lens did not reproduce, and that one has no
mechanism yet.

**Not verified:** `EditableMesh` in a running experience wants the **Enable Mesh / Image APIs** toggle
(which needs 13+ and ID verification and is not scriptable, so only the operator can flip it -
`QUESTIONS.md` L2); the lens still sits in this Rebuild place rather than in the game's (`QUESTIONS.md`
L1); and the one checkerboard seen earlier is unexplained.

See PROGRESS.md Phase 109 and 110, DECISIONS_2 442 to 453, docs/SNIPPETS.md 5.24 and 5.25, docs/SYSTEMS.md 2.19.

---

## The intro film - `intro/`

`intro/index.html` is a **35-second, silent, TRG-style boot/loading intro** for this project.
It is one file with no build step, no CDN, no web font and no audio, so it opens by
double-clicking it (`intro/assets/` is copied, not referenced - the source directory name
contains spaces). Press space to play.**Its script is `intro/SHOTLIST.md`.**

**The whole film is `render(t)`, a pure function of one clock.** There is no state machine
and nothing remembers the previous frame, so scrubbing the bar is a real seek rather than a
fast-forward, a loop is byte-identical to the first pass, and every element's entrance time
is readable in the `T` table instead of being recovered by tracing code. That is the same
discipline as `GameState` being the single source of truth (DECISIONS 303).

`#stage` is a fixed 1920x1080 design space scaled to fit, so every window shows the same
picture. `#film` is deliberately split out of `#stage`: the end-of-film CRT collapse applies
`scaleY` to `#film` only, so the player controls are not squashed with it.

**The text is not invented.** The choreography is the operator's own `Addition/Shift4.luau`
(the two `Quad/Out` `UDim2` tweens, the 45 rows revealed one at a time, the collapse, and the
"black for a bit of time" hold). The words come from capture: 24 of the 45 diagnostic rows
are **verbatim** from `Data/flow/original_*` and `Data/auxcollection/startup/ScreenChanges.txt`,
and all 6 boot-log lines are verbatim from `BootFrame.LogFrame.TitleText1..6`. Those directories
are gitignored, so copying the lines into the source **is** the archive. Provenance is recorded
per line in three grades rather than two - **V** verbatim from capture, **G** a genuine game
string captured elsewhere, **R** reconstructed (13 rows) - because folding G into V would
overclaim which capture it came from (DECISIONS 304). The spelling errors
(`ACCEPETED`, `INFASTRUCTURE`, `MANFUACTURING`) are data, not bugs; "fixing" them would make
every "verbatim" claim false (DECISIONS 305).

**Verified on two channels, because the film has two halves and each channel can only hold
one of them.** `_tools/intro_check.js` builds a throwaway DOM, evaluates the shipped file's
**own `<script>` bytes**, and reads the resulting inline styles back at chosen instants - the
same "read instance state, not module state" rule as CLAUDE 0.2. It reports **24 ok / 0 failed**,
including a 0.05 s sweep of the whole timeline asserting no `NaN`/`undefined` reaches any style.
It cannot see **layout**: a stub DOM has no `getBoundingClientRect()` to be wrong about.
`_tools/intro_render.js --check` is the other half - a real headless Chrome, driven over CDP,
sampling the actual box metrics every 0.25 s from t=3.0 to 12.5 and judging 5 assertions,
plus two later sweeps: every 0.25 s across 22.0..34.2 for **L5** (do two visible text blocks
ever overlap) and every 0.5 s across the whole film for **L6** (is anything cut off without
saying so). **7 ok / 0 failed**. The browser is the instrument and the pass/fail rule lives in
Node, because a measurement that also decides what counts as correct tends to quietly redefine
correct (DECISIONS 309). `_tools/intro_mutants.py` now drives **both** harnesses and requires
the *named* assertion to go red: **13/13 caught, each reddening exactly one check** - one red
is what makes an assertion precise (DECISIONS 306) - plus three **FOLLOW** mutants that must
stay green, since a check that fires on everything is as useless as one that never fires
(DECISIONS 311, 325).

**Six real defects were caught, all of the "nothing anywhere reports it" kind.** Three in the
stub-DOM half: the boot command permanently stuck half-typed, the pane frame still half-lit
when the black hold began, and the fade-out running past the end of the film so it never
actually went black. The fourth was **invisible to every one of those 24 assertions**:
`#diagList` was anchored to `bottom:0`, so a 1215px block inside a 630px window began 346px
*above* the pane and the scroll transform subtracted a second time - the pane was empty for the
first seven seconds and never showed more than 2 of the 23 rows that fit. Every row really was
`opacity:1`, which is all the stub harness asks. **Reading instance state is not the same as
reading the screen** - CLAUDE 0.2 in a new costume (DECISIONS 307).

**The last two the operator found by eye**, and both had every check green when he did
(Phase 94). `THE REACTOR GAME` at 170px owns y 400..570, and the three spec lines, the
sign-off and the footer all sit inside that band - so the title simply covered them. The
stub DOM has no layout to be wrong about, and the layout harness was asking whether the title
was *laid out*, which that 1920x170 band does perfectly: **every element being right, and two
elements colliding, are two different questions** (CLAUDE 0.2, eighth costume). The fix is
two geometries for `#title` (`HERO` -> `MAST`): the big centred read first, then it lifts and
shrinks into a top masthead 0.15 s before the first spec line inks in, which is not the cards
"making room" - the band is simply no longer there. Then, following the same thread, two boot
rows turned out to be wider than the pane: the longest one's ink reaches x=1671 against a pane
edge at 1225, so **446px of it was chopped mid-word with no mark** - on screen, `opacity: 1`,
green on every existing check. The fix is one declaration
(`overflow:hidden;text-overflow:ellipsis`); not wrapping, because the scroll arithmetic needs
the row height to stay one constant, and not a smaller font, because that trades the scrolling
terminal for a static list - **changing what the film looks like is not the same as fixing what
it hides** (DECISIONS 322..326).

Both intro harnesses are **deliberately not wired into `_tools/run_tests.sh`**: that gate is
about the injected Luau recorder/watcher/boot scripts, and these need `D:\nodejs\node`, which
is not on PATH on this machine (CLAUDE 0.6). Run them by hand:

    "D:\nodejs\node" _tools/intro_check.js
    "D:\nodejs\node" _tools/intro_render.js --check
    python _tools/intro_mutants.py

**The video.** `intro/THE_REACTOR_GAME_intro.mp4` is the same film as a file: **5,881,392 bytes
(5.61 MiB)**, 1920x1080, H.264 High, `yuv420p`, 30 fps, **1051 frames**, **35.033 s**, silent.
(Re-rendered after Phase 94's layout fixes - same format, same frame count; the first cut was
5,932,568 bytes, a difference no viewer could see.)
It is rendered by `_tools/intro_render.js`, and **it is not a screen recording** - since the film
is `render(t)`, a frame-exact render is just "call `render(i/fps)`, screenshot, next i", so
there is no clock to race, nothing can be dropped, and the same command writes the same bytes.
Realtime capture would be strictly worse because it samples the page's own
`requestAnimationFrame` cadence, which is exactly the timing the film was built not to depend
on. Two details make it work: `requestAnimationFrame` is stubbed out **before the page script
runs** (`Page.addScriptToEvaluateOnNewDocument`), or the page's own autoplay loop keeps
overwriting driven frames behind the renderer; and the viewport is pinned to exactly 1920x1080
(`Emulation.setDeviceMetricsOverride`) so `fit()` computes scale 1 and there is no letterbox to
crop. The 1051 intermediate PNGs (~300 MB) are scratch and gitignored; the mp4 is the
deliverable and is tracked (DECISIONS 310, 312). Re-render with
`"D:\nodejs\node" _tools/intro_render.js` (~6.2 min).

**What is not verified:** pixel-level font/blending behaviour is still not independently
re-checked, the mouse and keyboard controls have only been code-reviewed, and the film has only
been seen in one Chromium. The film is silent by request (no audio from `asstes/`); section 6.13
of the file is left empty with the t-driven hook written down, because a "have I played this
already" flag would turn scrubbing into a random walk.

See PROGRESS.md Phases 91 and 92, DECISIONS 303 to 312.

## The promo film - `promo/`

`promo/index.html` is a **76-second, 1920x1080 trailer with music**, built on the same contract
as the intro: **the whole film is `render(t)`, a pure function of one clock** (DECISIONS 303).
`_tools/intro_render.js` rendered it **without a single change** -- a second film is another
HTML page that keeps the same contract, not a second pipeline. It renders 2,281 frames over
~22 minutes to `promo/THE_REACTOR_promo_silent.mp4` (video only; the renderer's encode is silent).

**Its plates are captures, taken in Edit mode.** Twenty camera-positioned `screen_capture`
shots of the working place (`promo/shots/`), plus the game's own startup log for the text:
the 13 lines typed out during the hush are verbatim from `docs/ORIGINAL_UI_TEXT.md` section 1,
with `COMBUSTION LASERS FIRING` landing on the ignition frame. The temporary lighting rig used
to take the shots (`Workspace.PROMO_LIGHTS`) was deleted afterwards and the deletion verified
(`gone=true`) -- Workspace content is live, so moving it is changing the world (CLAUDE 0.12).

**The ignition is a cascade of five more plates, not a bigger flash (Phase 121).** The operator's
note was that the startup showed nothing happening: "开机腔室得有点变化吧？开灯、CBL 开机什么的
（注意有很多东西要动比如子空间预测）". A film built on stills cannot *brighten* its way to a lit
chamber, so the five `ig1..ig5` plates were captured from the same camera positions in pairs --
ig1/ig2 are one camera with the chamber's 98 `NeonPart` surface lights off and then on, so the
light coming up is really the light coming up. They cross-dissolve over 16.20-19.45 with the
tour's own window rule, and the coverage value is the **sum** of the stage opacities rather than
their max: because the windows straddle each cut and are complementary, the sum is exactly 1
across a dissolve, whereas `max()` would drop to 0.5 at every cut and leak the tour caption
through (DECISIONS 502).

Two defects in that cascade were caught **by looking at the frames, not by reading the probe** --
the probe agreed with the code the whole time. At the hand-off the cascade's per-plate caption and
the returning tour caption were both at 50%, printing two large captions on top of each other; the
caption is now a single text block that **hard-switches** to whichever plate dominates while the
images dissolve under it (DECISIONS 503). Moving it into a shared container then wrapped it
silently -- an absolutely positioned child of a zero-width box breaks at every word boundary, and
the measurement that catches it is the **height** of the box, not its presence (DECISIONS 504) --
and that container sat inside the `transform`ed layer of the plates, which traps `z-index` in its
own stacking context, so the corner scrim was dimming the white text to grey (DECISIONS 505).

**One thing in the cascade is an honest substitute.** The operator named the subspace forecast
panel specifically. Its plot is built at *runtime*, so in Edit mode that monitor is blank by
construction -- a part-by-part comparison of the FORECAST and MAIN `MainMonitorFrame`s shows an
empty `ScrollingFrame` and only the hidden template. Rather than fake it, the beat uses the
monitor wall, and the caption says "Monitor Network" rather than naming the forecast.

**The music is the operator's reference track, not the remix -- and that correction re-measured
the whole timeline.** The first cut synced to `ReactorStartup_Remix.mp3`; the operator corrected
this ("**不是你做的，是最开始的那个**", 2026-10-11). The two files differ by 3 s in length but
**not** in structure, and the difference is the one that matters:

| | quiet stretch | sound returns |
|---|---|---|
| Remix | 10.30 -> 16.20 s | +18.8 dB at 16.20 s |
| **`ReactorStartup.mp3` (used)** | **0.00 -> 2.25 s** | **+34.5 dB at 2.30 s** |

The original has **only** its lead-in silence -- a 50 ms RMS sweep of all 263.9 s finds no
mid-track gap at any of -30/-35/-40 dB. So the 6.5 s hush the film needs cannot come from the
track's own gap and is **built**: `promo/_bed.m4a` is the original from 2.30->12.00 s, then a
true 6.50 s of silence, then the original resumed at 12.00 s. The two music segments abut
(12.00 meets 12.00), so the bed has **exactly one silence-to-sound transition** and it lands on
the ignition. Measured on the delivered file, not on the ingredients:

```
silencedetect  silence_start 9.693492 | silence_end 16.201383 | duration 6.507891
volumedetect   11-15 s (the hush)   mean -91.0 dB   <- digital zero; -91 is the quantiser floor
               21-25 s (after ign.) mean -18.1 dB | max -5.8 dB
straddling 16.20, two disjoint windows: 16.05-16.20 = -91.0 dB vs 16.22-16.37 = -19.5 dB
```

That last pair is **at least** 71 dB, not 71 dB: the hush is a true digital zero, so where it
reads -91.0 that is the floor rather than a level.

**One figure from the previous round could not be reproduced, and it is left standing rather
than rewritten.** The line here used to read `BIGGEST RISE 33.6 dB at t=16.25 s`. Rebuilding
that metric from memory (`astats:reset=1` + `ametadata=print`, 50 ms RMS, biggest jump) gives
**byte-identical output for the muxed film and for `_bed.m4a` alone** -- both report
`BIGGEST RISE 63.5 dB at t=0.00 s`. The same number on two different files means the **ruler**
is wrong, not either file (DECISIONS 507), so the old figure neither became evidence nor got
quietly overwritten: the two reproducible measurements above replace it, and the fact that the
original method is gone is recorded next to it (DECISIONS 507).

**One real defect was caught by reading the delivered file back.** Each plate faded out on
`[t1-XF, t1]` while the next faded in on `[t1, t1+XF]` -- **non-overlapping windows**, so at
every cut *both* were at zero and the film dipped to a fully black frame (12 cuts, 0.45 s each
way). Both windows are now centred on the cut so the ramps are complementary
(`sum=1.00 | max=0.50` at every boundary). It was found on a contact sheet pulled from the
finished mp4 -- the twelve instants sampled had landed on the cuts, which is why a first glance
read as "the extractor is broken" until the numbers were read (DECISIONS 499 to 507).

**And the cascade was checked on the delivered file, not in the browser** -- five instants
(`16.85 / 17.45 / 18.40 / 19.15 / 19.45`) pulled back out of the finished mp4. "The renderer
agrees" and "this file is right" are two different claims. `19.45` is the frame the
double-caption defect lived on, and it now carries exactly one caption; in every frame the
corner label names the same source as the large text, which is how the last one is known to be
the tour's returning caption and not a leftover of the cascade. Note that a frame pulled at
`-ss 16.85` is the frame *covering* 16.85 (16.8667) while a probe reads `render(16.85)` exactly,
and the caption hard-switches at the cut -- so the two differ by one stage and neither is wrong
(DECISIONS 508).


**The promo's audio is not tracked.** `promo/_bed.m4a` and the muxed `promo/THE_REACTOR_promo.mp4`
carry the reference recording, so they are gitignored for the same reason the track is; the
silent master and the plates are our own render and are tracked. Rebuild both with the commands
in `docs/PROMO.md`.

## The cover - `cover/`

`cover/THE_REACTOR_GAME_cover.png` is a **1080x1080 (1:1) game cover** for TRG:AIREMAKE,
drawn by `cover/index.html`. **Four things are on it**: the frame, the hexagon with the
manufacturer's mark, the title with its `AIREMAKE` badge, and the footer. Phase 134 cut it down
from about fifteen elements (`要素太多了，不需要这么复杂`); what went - the HUD readouts over the
hexagon, the subtitle and specs lines, the four-cell readout strip, the diagonal title band, the
background grid and hex pattern, the core glow, the hazard band, the dashed rings and vertex
ticks, the CRT noise - lives in git history and is not rebuilt in the docs.

It re-renders to **the same picture**, not to the same bytes: twelve consecutive renders in
Phase 132/133 split 10/2 into two byte forms - 792,813 / md5 `6feba9bd8cea91be2917be605b8f1a36`
and 792,812 / `f9e17bcdaa07ae67ddb47c66f4e331d0` - that differ by **one pixel, one grey level**
(the antialiased hexagon edge at (790, 583)), and the split's ratio was not stable either.
Phase 134's build came out **12/12 byte-identical** (496,559 bytes / `5bd615a72093da2b35cff97e156c56a9`),
which is a positive result but **not proof the mechanism was fixed** - it was never proven, and
the criterion stays **pixels, not hashes**; `docs/COVER.md` section 4.

**Nothing under `promo/` is used any more.** The hexagon holds `intro/assets/sm-core.png`,
the manufacturer's mark - a line drawing, not a photograph, and one already in the repo's
tracked art (the page footer draws the same asset). That was the operator's call in Phase 133
(`好吧，不用实拍图片`); the in-game ignition capture it replaced is still in the repo, untouched,
because `promo/` remains the films' and the store page's material. `QUESTIONS.md` R8 asks whether
the instruction stops at the cover.

**It is the third page that obeys one contract**, so it needs no renderer of its own: a fixed
`#stage`, a global `render(t)`, a `fit()` that scales it to the window. A still page just makes
`render(t)` accept `t` and ignore it - nothing on the page changes with time, so there is no
state to leave behind and no frame to scrub back to. `_tools/intro_render.js` gained `--w`,
`--h` and `--shot`, all defaulting to what the two films already passed, so neither film
changed. `--w 1080 --h 1080` is not optional: without it `fit()` scales the square stage into a
1920x1080 viewport and **every coordinate in the measurement is in the wrong space** - which is
why A0 measures that before anything else.

**The measurement and the verdict are two files.** `cover/index.html` only reports
(`layoutReport()`); `_tools/cover_judge.js` decides **A0..A10 with A8 retired** and exits 1 on any
failure, so it is a pure function from JSON to exit code and runs with no browser at all - which
is what makes `--selftest` possible: **12 mutants, each reddening exactly the rule it is aimed
at** (the most realistic being "forgot `--w/--h`"). Current: **10 ok / 0 failed**. A10 is the
rule the mark added: the mark is the one layer element `clip-path` does not cut, so growing it
does not look wrong - it looks like one line crossing another - and the rule measures how much
air is left between its circumcircle and the six edges (39.4 px).

**Two rules retired with the elements that were their object** (Phase 134), because a rule whose
object is deleted can only go permanently red, and a permanently red check is noise: A8 ("every
cell of the readout strip holds its own value" - the strip is gone), and A9's "both a black and a
white asset must be present" (the only two black assets on the page were the title band and the
hazard band). What stayed had to be **re-asked one at a time**, and the answer went both ways:
A3 ("the closest pair is under 40 px") needed no change - the closest pair is now the two footer
lines at 14.00 px - while A1, the non-vacuity rule, had to **get stronger**, because an emptier
page makes "nothing collides" cheaper. A1 stopped counting (`>= 12 text blocks, 4 cells`) and
started **naming the four things** that must be present and sized.

**The defect worth reading about is in the decoration.** In the Phase-132 build six layers
carried no text and sat on no geometric assertion, and **four of the five then present were wrong
while nine of the ten rules were green** - two of them contributing exactly zero pixels. Two
mechanisms, both silent: `mix-blend-mode:screen` fed a black asset (`screen(base, 0) == base`, so
`stripes.png` - measured rgb(0,0,0) - erased the title band and the hazard band entirely), and
`filter:invert(1)` on near-white art (which turns it black, dropping the amplitude from delta 24
to delta 3). Four layers are left (`#coreMark`, `#smMark`, `#scan`, `#vig`);
`_tools/cover_layers.sh` renders the cover once per layer with that one layer switched off and
diffs the pixels - all four change pixels, and each diff lands in that layer's own declared box
(the mark's in its 420 px box plus its 38 px `drop-shadow`, the scanlines inside the 22 px frame
inset, the vignette over everything). The layout judge's A9 covers the half pixels cannot see
(each layer declares its asset's polarity in `data-art`, and the rule asserts that declaration
and the computed `filter` agree, plus "at least one layer declares a real asset"). Nothing here
errors in any of those cases. Full write-up: `docs/COVER.md`.

**"The layer changes pixels" is not "the pixels are that asset"** - a flat white square would
pass every other instrument here. `_tools/cover_mark_check.py` compares the render against the
asset's own alpha, and its output is a **threshold sweep rather than a pair**, because on this
page there is no clean cut: the mark's faintest ink (142) is dimmer than the brightest non-ink
pixel in the same box (159 - the hexagon's own outline and the mark's drop-shadow). What survives
is that the whole drawing is present (all 44663 ink pixels bright at t<=80) and that every radial
band out to the outer ring reads 99.7%-100%. Phase 133's build read **80.7%** in that outermost
band and the docs blamed the hexagon tint darkening it; the measured shape of that darkening says
otherwise (it was the tint's own top-to-bottom gradient plus the black text-shadow on each HUD
line), and how much each contributed was **not separated** - `docs/COVER.md` section 4.

**The wording is a judgement call, not a measurement.** The title reads `THE REACTOR GAME`
with an amber `AIREMAKE` badge - i.e. **not** `TRG: AIREMAKE` - because that name is the brand
line in both films. It is `QUESTIONS.md` **R7**, and it is one line to change.

## The 16:9 game-page image - `cover/page.html`

`cover/THE_REACTOR_GAME_page.png` is the **1920x1080 promotional image** Roblox's Game details
page asks for, and it exists because the operator handed over the empty slot in Phase 144
(`这个是游戏主界面的那种背景宣传图 / 还没有做，交给你了`). The icon above that slot is the
Phase-132/133 cover, already uploaded.

**It is not the square cover letterboxed.** Centring 1080x1080 inside 1920x1080 would leave
420 px of black on each side, which reads as an unfinished image in a thumbnail carousel, so the
page is **re-laid out**: the hexagon stands on the left, the type column on the right, the four
elements unchanged (frame / hexagon + mark / title + `AIREMAKE` badge / footer), the same four
palette entries, the same two assets, the same `render(t)` contract. The one visible departure is
the title: **two lines at 116 px** instead of one line at 96 px, because the right column is
864 px wide and one 116 px line measures 1088 px here (Arial Narrow is absent, so the fallback is
wider). The judge therefore measures the **line advance** (110.19 px, i.e. 22.04 px at Roblox's
1/5 card size) rather than the CSS font size - the advance is what a reader at that size gets.

**The instruments were parameterised, not copied.** `_tools/cover_layers.sh` and
`_tools/cover_mark_check.py` grew environment overrides (`PAGE/W/H/TAG/SHOT`, `SHOT/BOX/BOX_X/BOX_Y`)
whose defaults are the cover's, so every command already written in these docs still means what it
meant; the cover was re-rendered afterwards and came out **byte-identical** (`5bd615a7…`,
496,559 B, all four layer counts unchanged). The layout judge could not be shared: its rules were
written against a vertical lockup in a square, and the 16:9 page bounds the hexagon sideways. A
copy with renamed rules would have looked the same and measured something else, so
**`_tools/page_judge.js` is a second judge with W0..W10** - 11 ok / 0 failed and **17/17 mutants**,
including one that moves only the title's line boxes (so W4's own "every line fits" claim is proven
separately from W2's "the text block fits").

**Verified:** two renders byte-identical; four decorative layers each change pixels (195354 / 543 /
203788 / 1112794, all with max delta >= 48); the mark is that asset and not a blob (all 46656 ink
pixels bright at t<=80, every radial band 99.7%-100% at t=120); read at full size and at 384x216,
where **both title lines stay legible** and the small `AIREMAKE` badge does not (the reader model
promptly invented the word `PRESENTS` there, which is its known failure mode at small sizes).
**Not verified:** anything about Roblox's own cropping or compression, and the upload - no
`asset:write` key is configured, so the file goes in by hand. Full write-up: `docs/COVER.md` §7.

## The music - `asstes/music/ReactorShift.{ogg,mp3}`

An original track, **263.84 s**, 89.25 bpm, F major pentatonic, 97 bars. It is composed in
Python by `_tools/music/make_song.py` (numpy only - no model, no torch, no sampled material)
and encoded with ffmpeg. Two encodes are shipped because Roblox and browsers disagree about
codecs; both are the same audio.

**Its specification is a measurement, not a mood.** `asstes/music/ReactorStartup.mp3` is the
reference the operator named - his own identification of the source (2026-10-11) is
`[WIP] (Piano) Portal 2 OST - Reconstructing More Science - Aperture Science Psychoacoustic
Laboratories`, a piano arrangement of a Portal 2 OST cue - and every number in `make_song.TARGET` was
measured off it with `_tools/music/analyze.py`: the per-octave profile, the 10 s block
band shares, the p5/p95 dynamic arc, side/mid and L/R correlation. **No melody was
transcribed from it** - it fixes the *shape*, not the notes. The reference and its report are
**gitignored and never committed** (someone else's master, and this repository is public);
only the original track and its own report are tracked.

**The melody is a table, not a schedule buried in a render loop.** `lead_plan()` returns
104 `(bar, beat, note, dur, tag)` events, and **the renderer and every ruler read that same
table** - so a ruler cannot end up measuring a private copy of the composition. Five themes:
`a` the three-note motif stated and then answered by transposition, `b` an ascending line
(B2 tops out on C6), `ctr` a descending counter-line moving in contrary motion, plus two
accelerating fills and a final augmented statement. The lead sounds in 38.3% of the piece
and is deliberately absent for bars 81-91.

**The level of that voice is a knob, not a cache artifact.** The cached stems hold the lead at
*unit* level; `with_lead()` applies the level once at assembly, and is idempotent so nothing
can fold the same lead in twice. Before this, changing the level and running `--reuse`
re-rendered, re-mastered, re-measured and played back perfectly - while shipping the old level.

**What the audio checks are.** `_tools/music/check_song.py` re-measures 13 properties on the
**delivered mp3 and ogg themselves** (duration, peak, clipping, RMS, dynamic arc, octave bands
and their mean, the texture of the 2-8 kHz top end, stereo width, correlation, DC, click
steps, edge fades) against targets imported from `make_song.py` - deliberately imported rather
than retyped, because a checker with its own copy of the spec certifies the wrong thing the day
they disagree. Every check has a variant that must turn it red; `--variants` runs all 11 and
fails if any leaves its target green.

`_tools/music/lead_margin.py` answers a different question: **how far above its own
accompaniment is the melody, per note, in the note's own critical band.** It is measured
PRE-master, because the master EQ loop pins the octave profile and prominence is exactly what
such a loop flattens. Two things define it, and both cost a round to learn: **the rest it
divides by must contain no melody at all** - `with_lead(stems, 0, 0)`, which is exact because
assembly is linear in stem levels - and **power is measured on the summed signal**, not as the
sum of two separately measured bandpowers (those differ by 3 dB here because dry and wet are
correlated in the note's own band). Measured now: median **+6.5 dB** narrow-band, **0 of 104
events below 0 dB**, and **+12.8 dB in the climax against +6.4 in the groove**.

**What is not verified: whether it sounds good.** Every figure above is a ruler reading. The
ruler can show that the melody stands out of its accompaniment and that the middle of the
track is unlike its ends (the 10 s block share of the mid band runs 14% -> 55% -> 23% across
140-150 s, where the old version never left 3-21%) - it cannot show that this is a tune. That
judgement belongs to the operator's ears, and it is the third time he has supplied it.
Nothing has been changed in Roblox: there are no upload credentials here, and
`Workspace.Sounds` is part of the world.

Run it with `python _tools/music/make_song.py` (add `--stems` to re-render the cache, `--reuse`
to assemble from it, `--probe` to print the raw profile). The three music harnesses are
**deliberately not wired into `_tools/run_tests.sh`** - that gate is seconds; `check_song.py`
is about ten minutes and `lead_margin.py` assembles four full mixes.

See PROGRESS.md Phases 93 and 95, DECISIONS 313 to 321 and 327 to 333, and
`docs/SYSTEMS.md` section 2.16.

## The remix - `asstes/music/ReactorStartup_Remix.{ogg,mp3}`

A remix built **on top of** `ReactorStartup.mp3` rather than alongside it: the reference recording
is kept and transformed - its own material is sampled, re-levelled and ducked - with a drum kit,
sub, pads, risers, impacts and an arrangement charted against it. **266.93 s, 90.000 bpm, 97 bars.**

**It is not committed, and the reason is the recording it quotes.** Sampling that master means the
result carries the same recording, so it cannot be published any more freely than its source can.
`ReactorStartup_Remix.mp3`, `.ogg` and its report are all in `.gitignore`, next to the reference
itself. The *tool* - `_tools/music/remix.py` - is tracked, because the arrangement table, the
parameters and the checker are original and independent of the sampled audio. The derived numbers
live in PROGRESS Phase 111 for the same reason: the report they would normally sit in is ignored.

**The tempo in the stored report was wrong, and the ruler was why.** `ReactorStartup.report.txt`
was generated with `--nfft 8192` / 21.5 fps and says 92.25 bpm. On the fine ruler the rest of the
code uses (`n=2048`, hop 512, 86.13 fps) 90.00 scores **326.174** on the comb against 92.25's
**13.441** - a factor of 24, with sharp shoulders. 90.000 supersedes it, and the superseded number
is kept with its reason rather than deleted: "why do the two reports disagree" is a question that
comes back.

**The bar phase is the one measurement that could still be audibly wrong.** Which of the four
beats carries the downbeat wins by **+1.01 dB against a 1.0 dB threshold** - it scraped through.
Pick the wrong one and the whole kit moves by one beat, which sounds fine on its own and is wrong
against the music. The first metric was worse than a close call: scoring the mean envelope on each
beat gave four candidates in monotone order, 59.3554, 59.5056, 59.6567, 59.8085 - a 0.77% spread
that was the envelope's slope (this track climbs to its climax at 140 s), not a downbeat. The comb
- on-beat against the interleaved off-beat, same span for every candidate - is what cancels it.

**Roles come from measurement, not from position.** The reference's busiest passage (bars 50-57)
is also its quietest (34-38 dB), and its last 88 s are its loudest (45-47.6 dB). Charting by
position would put the busiest kit over the quietest music and highpass the loudest section; the
instrumentation follows the z-scores of level and density instead, and the tail keeps the main
treatment rather than being given a fake outro.

**The mix balance is measured on the delivered encodes.** Reference share of energy **44.9%**
(was 8.9%), mix/reference correlation **+0.753** (was +0.360), and the octave profile is +6.2 /
+4.9 / +4.5 / +4.2 / +5.6 dB over the reference instead of +13.5 / +12.3 / +11.0 dB in the bass.
The original bug was levelling a reference pulled to about -25 dBFS RMS against a kit levelled in
absolute peaks; the fix is one measured scale for the whole kit bus.

**What is not verified: whether it sounds good.** Every number above is a ruler reading, and the
+1.01 dB bar phase is the single one that could be wrong in a way an ear would catch. There are
still no upload credentials here, so nothing has been wired into Roblox - and `Workspace.Sounds`
is part of the world.

Run it with `python _tools/music/remix.py` (`--probe` for the grid and the structure table only,
`--check` to re-measure an existing render). See PROGRESS.md Phase 111, DECISIONS 454 to 459, and
`docs/SYSTEMS.md` section 2.16.

## The MIDI - `asstes/music/*.mid`

Also ignored (see `.gitignore`): a MIDI file **is** the notes, with no recording in between to make
the derivation arguable, so it gets the same treatment as the reference it would be derived from.
The operator put one there on 2026-10-11 and named it himself:

```
[WIP] (Piano) Portal 2 OST - Reconstructing More Science - Aperture Science Psychoacoustic Laboratories.mid
```

**What it is**, measured rather than assumed: format 1, four staves all on program 0 (acoustic grand),
384 ticks per quarter, one tempo event of 60.000 bpm in 4/4, **936 sounding notes in only 296 unique
onsets**, ending at tick 34560 = 90.00 quarters = **22.50 bars = 90.00 s**. Every onset and offset is
a multiple of 96 ticks, so it is quantized exactly to the sixteenth, and the 936 notes use just **six
distinct lengths** (705 of them exactly one sixteenth). That is a step-entered transcription, not a
performance - a played piano has dozens of durations. Range D2..D5.

**It is not the recording, and that is a measurement, not a guess.** The MIDI is strictly diatonic:
**D#, G and A# never sound, in any of the 936 notes.** The audio's chroma has no empty class at all,
and its second-largest is **G at 11.04%** - the pitch class the MIDI never plays. Rotating the MIDI
onto the audio does not rescue it: the best rotation (-4 semitones, r +0.680) still leaves D#, F# and
B at zero where the audio sounds them at 6.67%, 6.31% and 5.75%. **No transposition of this MIDI is
this recording.** They share a title, not a performance - and note that the title's own `[WIP]` tag is
what the audio corroborates (DECISIONS 459).

`_tools/music/midi_grid.py` is the ruler for this, and it is tracked because it is original. It parses
an SMF with stdlib only (no mido), reports the tempo/meter/texture grid, and with `--compare <audio>`
runs the transposition test above. It is a ruler of a different kind from `analyze.py`: `analyze.py`
infers a grid from a spectrogram, whereas a MIDI **is** the grid - which is why the bar phase that
scraped through at +1.01 dB against a 1.0 dB threshold would be stated outright in a MIDI of the same
music. It follows that the file has to be *shown* to be the same music before it can be spent as one.

```bash
python _tools/music/midi_grid.py path/to/file.mid
python _tools/music/midi_grid.py path/to/file.mid --compare asstes/music/ReactorStartup.mp3
```

## The MIDI render - `asstes/music/ReconstructingMoreScience.{ogg,mp3}`

The operator's answer to `M1` was `A` -- render it to audio -- and these are the
files: 96.000 s, 23 bars at 60 bpm, built from the 936 notes in the `.mid` he
put in `asstes/music/`.

It is the third sibling in `_tools/music/`, not a third mode:
`make_song.py` composes, `remix.py` samples a recording, and
**`midi_song.py` plays a MIDI's own notes**. Every arrangement layer is measured
off the source rather than chosen:

- the section map comes from the file's own per-bar note counts;
- the pedal follows the bass root on a quarter-note grid (42 changes), and the
  rejected rules print the same run so the choice is data, not taste;
- the sub doubles each bar's lowest sounding note, the pad voices each bar's own
  pitch classes, and the marks land only on measured section boundaries (3).

Two of its checks had to be **replaced rather than tuned**, and the reason is
worth carrying:

- **An argmax over aliases is not a measurement.** Every onset in this file sits
  on a sixteenth (250 ms = 21.5 frames), so the onset correlation is a comb with
  teeth at +19 / -24 / +41 / -46 frames scoring 0.240 / 0.224 / 0.224 / 0.215 --
  and the alignment the physics predicts (-2 frames) scores 0.215. The first
  version took the maximum over a wide window and reported "lag +19 frames
  (221 ms)", a whole sixteenth of nothing. The window is now half a grid wide
  and the lag is tested against `-n/(2*hop)`, with the alias printed beside it.
- **A top-4 pitch-class ranking is not a note test.** The reference counts every
  note once; the measurement is an FFT in 300-3000 Hz, where a high note shows
  its fundamental and a low one only its harmonics -- so the band couples weight
  to register (B reads 10.84% against the source's 4.70%). That band was tuned
  on the *recording*, where the top-4 came out right; on a synthetic voice it
  does not. It is replaced by asking which of the twelve rotations fits best,
  which has a null: zero wins at r +0.813 against +0.508 for the next.

The master's loudness target is a **fixed point** (normalise, limit, measure,
repeat) rather than a step, the mix is trimmed to a stated length, and a
percussive bus is levelled by peak rather than rms. Target loudness is -19 dB
rather than the -16 dB the other two tools use: this material's crest factor is
about 21 dB, so reaching -16 would mean shaving 5 dB off every attack.

The `.mid` and all three audio files are gitignored -- the derivation is the
thinnest of the three cases, because it reproduces the composition itself rather
than pointing at a recording. See `docs/SYSTEMS.md` 2.20 and PROGRESS Phase 112.

## The console in `luau-windows/`

`luau-windows/calculation.luau` is the operator's own transcription of the reactor's pressure
update, and `calculation.py` is the same thing in Python. Neither is a game system: they are a
small standalone model of the tick, with Temperature, ActiveFan and PEALevel hard-coded.

`luau-windows/gui.py` is a window onto that model. Run it with:

```
cd D:\rblxTRGproject\luau-windows
python gui.py
```

One file, no third-party packages. The left column is the three hard-coded values turned into
controls - PEA level and fan count as radio rows (one click, one level, and the selection stays
visible), Temperature as a slider with a spinbox beside it, tick period as a second spinbox,
plus Pause / Step / Reset. The right column shows Pressure, the per-tick delta, the core state
and its band, Temperature, the tick count, elapsed time and the period, and then breaks the
tick's own four terms apart: `p = g - 60n + s t + d`. The log at the bottom holds the `.luau`'s
own `Pressure: N` output plus `#` commentary.

**Two things about the Temperature control are worth knowing before touching it.** A `ttk`
scale has neither a `-resolution` nor an `-increment` option - both were tried - so its steps
are pixel-sized and a pixel is worth about `40000 / width` degrees (133 at the current 300 px).
What makes the operator's "interval 1" true is the **spinbox**: it is the control you can hold
an exact number in. Both write through one path, `_set_temperature`. Clicking or holding the
scale's trough does step by exactly one, because Tk's own binding is
`ttk::Repeatedly Increment $w ±1`; dragging the thumb is absolute, and a right-click in the
trough jumps.

**Readings are rounded for the eye and nothing else.** The model accumulates in full float,
exactly as the `.luau` does, because rounding the model would let it drift away from the
original - and that drift is precisely what the `.luau` comparison is blind to. The rounding
is half-away-from-zero, deliberately not Python's `round()`: these values really do land on
`.5`, and half-to-even would make one of them look unchanged every other tick.

**The verification does not touch the operator's mouse.** He asked me to stop moving his
cursor, so the harness drives the widgets through Tk's own `event_generate` (the same Tcl
bindings run, and the window can stay invisible) and photographs them with `PrintWindow`,
which asks the window to redraw itself - no raising, no focus stealing, no cursor. It is also
more accurate, not less: `event_generate` works in widget-local coordinates, so the 58-pixel
DPI inset that spoiled an earlier round of click testing cannot arise. The harness is in the
job directory rather than the repo, since it measures this machine's Tk rather than the
deliverable.

See PROGRESS.md Phase 97 and DECISIONS 341 to 348.


### Phase 126 - the operator's own temperature model

The console used to take Temperature as an input, because `calculation.luau` does. The operator
handed over a model that *computes* it - read off the shipped game's own 477-tick log - and asked
for it to live in this window. It is in, in its own block, and it is **armed rather than
installed**: with the box unticked not one line of it runs and the console behaves exactly as it
did before.

```
T(x) = T0 + (baseRate[state] * power/50 * pressFactor + noise(x)) * x
baseRate    = [-455.7, 559, 580, 1036]      x = seconds since arming
pressFactor = 1.15 below 2500, 1.08 below 4000, else 1.0
noise(x)    = 40 sin(x/1.5) + 25 sin(x/0.7) + 15 sin(x/0.3)
```

His `state` is **not** the console's `Sim.State`. Two quantities in this game are both called
"state": the latched pressure band (the original's if/elseif chain with no `else`, which is what
`Sim.State` mirrors) and `coreState`, a pure function of temperature with a row 0 for the cold
machine (`Engine.luau:320`). His rates were grouped by the second, which is why his table has a
row 0 and why his `s` can fall. So the model derives its row from the temperature, and a
`Core state (from Temperature)` readout now sits beside the latched one to keep the two apart.

Two properties of the equation are kept as written rather than quietly corrected, and both are
visible on screen. `x` is elapsed **time**, so the rate is multiplied by it - and `noise(x)` is
**inside** that multiplication, which makes it a tremor on the slope rather than on the reading:
a ±80 degree wobble is ±8000 at x = 100. It grows with time, the opposite of the "stop the number
flickering" it was written for. Both are his to change; the alternative shape is named in the
code beside each, not substituted.

The right column gained `T0` / `x` / `row` / `rate` / `noise(x)` / `noise(x)*x` / `T(x)`, read
from the same values the step itself used, and they show a dash rather than a zero until the
first step - a term from a step that has not happened cannot appear. `luau-windows/core_model_check.py`
drives all of it: **70 checks, read back off the widgets** rather than off the model, because a
value that is right in the model and wrong on the screen is the failure worth catching. It found
two, and both are fixed. See PROGRESS.md Phase 126 and DECISIONS_2 527-530.

**Revised in Phase 131.** The operator's refined spec replaced the closed form above with a
per-tick step; the block just below is that revision. This one is left exactly as it was written.


### Phase 131 - the console's temperature model, rewritten as a step

**No game code was changed this phase either.** The operator handed over a revised temperature
model headed "temperature calculation (refined)" and asked for it to go into the same console.
It does not sit beside the Phase 126 model - it replaces it, and the evidence for that is in the
spec itself (the new tables are the same fit as the old one, not a second opinion).

```
row       = 0 if T < 5600;  1 if T < 17500;  2 if T < 29500;  else 3
a         = level * 25                    # the power the CBL radios carry, so a IS `power`
baseFluc  = active[row] + passive[row]
active    = [0, 6.86a + 65.5, 7.24a + 37, 6.8a + 534]
passive   = [-455.7, -19.2, 0, 0]
press x   = 1 if p <= 11500;  2 if p <= 27000;  else 4
noise(t)  = 15 level sin(t/1.5) + 10 level sin(t/0.7) + 5 level sin(t/0.3)
T'        = T + baseFluc * press x + noise(t)      # a step, not a closed form
```

**The shape changed, and that is the whole point.** `T` is on both sides: the model decides how
much the *next* tick adds, and the console carries the temperature. Phase 126's was a closed form,
`T(x) = T0 + (rate + noise(x)) * x`, recomputed from `T0` every tick. A step has no anchor, so
`T0` and the level-2 `multiplier()` are gone rather than left sitting in the readouts with no
reader - a number that is displayed but no longer computed is the same shape as a computed one.

That also fixes, by construction, the three defects the Phase 126 code named in its own comments
and left in place: the operator handed over exactly the alternative those comments had written
down. `noise` is added to the **reading**, not multiplied into the slope, so a ±80 wobble is ±80
and does not grow with `t` (at `t ≈ 30` it had outweighed the whole rate term). Each row is a line
in `a`, so a CBL level scales the rate instead of one averaged number being scaled by a multiplier
from somewhere else. And a row change changes the **increment**, not the whole line: crossing
2 -> 3 used to move the reading by about 19,000 degrees at x = 100, which is a property of "a line
through T0", not of a reactor.

Three judgement calls are recorded rather than smoothed over. His lists are 1-based with a leading
slot - `s + 1`, with `s` in 1..3 - so writing them 0-based in his own order makes the index the row,
and his leading slot *is* row 0: `passive[0] = -455.7` is the Phase 126 `baseRate[0]` verbatim,
which is what says the two tables are one fit and not two. His `s` spells `T < 17500` where
`Engine.luau:320` spells `T > 17500`, so exactly 17500 is row 2 here and row 1 there; the spec's
spelling is implemented and the one degree is written into a comment and six boundary checks rather
than quietly reconciled. And `off` (CBL 0) is outside his fit, which starts at level 1: `a = 0`
through his line gives +46.3 per tick - that is the intercept, not the lasers - so `off` is defined
as adding nothing, which also silences the noise, since its amplitude carries `level`.

`core_model_check.py` was rewritten as the second spelling of the same spec - his literals, not a
call back into `gui.py` - and read every value off the widgets. **103 checks, 0 failed.** Two checks
in the first draft passed *vacuously* and were replaced: they ran with the row held at 0, where
`active[0]` is 0, so the CBL level had no effect at all and the assertion could not fail - CLAUDE
0.26 (1) from the other side, where a criterion that can pass for a reason other than the one under
test is no more of an experiment. A mutation putting the tremor back on the clock
(`+ noise(t) * t`) lights 4 of them, one of which was written at `t ≈ 35` precisely because the
first three ticks cannot see that shape. See PROGRESS.md Phase 131, DECISIONS_2 555-561,
docs/SYSTEMS.md 2.26, docs/SNIPPETS.md 5.38.


### Phase 135 - three laser banks, an AVB button, and the stall he measured

**No game code was changed this phase either.** Three changes went into the console, in the order
he asked for them: the CBL is now **three independently selectable banks** instead of one
five-position control, the AVB button exists, and his stall rule - a line of Lua he pasted, with
its own gloss "实测失速暴跌速率" - is in the model.

```
CBL   three rows, each off / PW1..PW5 = 0/25/50/75/100/125
      the model takes `a` = the SUM of the three banks
AVB   3300 PSI off the chamber, floored at 0, then 15 ticks before it answers again
STALL if pressure <= 2200 then the tick's fluctuation is -586, whatever the lasers are doing
```

**His spec was half a line.** What arrived was `if pres <= 2200 then fluc = -586` with the tail of
the *previous* line (`破2200)`) still attached to the front, which reads as two rules until you
notice the first fragment has no opener. It takes over two things at once - the tick's fluctuation
*and* the earlier "off adds nothing, which also silences the noise" - and both are written into the
comment, because a spec dropped into a model has to be asked what it overrides (DECISIONS_2 577).

**All three constants were read off the shipped game's own recording**, `Data/DataCollection.Log`,
through `_tools/avb_from_log.py`, so none of them is remembered:

- **The six AVB presses** have to be read as a *discontinuity*, not as "the sample before and the
  sample after". The recorder samples faster than the game ticks, so a press landing in the same
  second as a tick can have the step already inside its first sample and read `drop 0` - which is
  what three of the six did, before the log was deduplicated and the drop taken as the largest
  one-tick step within ±6 s. **Four of the six then read 3300 exactly** (6702→3202, 3300 with the
  chamber's own +0/+0/+200 drift printed beside it). DECISIONS_2 574.
- **The stall band is -538 .. -801**, and it contains **both** his -586 and our own remake's
  `Config.StallCooling = 750`. A band that holds both candidates chooses neither, so the console
  takes his because it models the original, not because of a reading. DECISIONS_2 575.
- **The cooldown is 15 ticks**, which is *not* a disagreement with our remake's `Cooldown = 26`.
  The wiki's "about 25-26 seconds, or around 15 reactor ticks" is one duration in two clocks
  (25.5/15 ≈ 1.7 s per core tick); every other per-tick constant here is the original's per-core-tick
  value (`FAN_DRAG = 60` is the wiki's "60 PSI of pressure per core tick"), so 15 is the consistent
  currency and 26 is the same ~26 s in our remake's own 1-second clock. The log's own six press gaps
  (26, 58, 27, 26, 36 s) put a floor under it. DECISIONS_2 579.

Two of the wiki's own sentences are recorded as **known simplifications** rather than smoothed: the
cooldown is state-dependent in the original ("Based on the State, the button will take longer to
refresh after use") with no per-state values given, so 15 is a state-1 reading of a state-dependent
number (DECISIONS_2 580); and the wiki is not of one voice on the drop either - "3300 PSI" twice,
"around 3000" once, with its own 5500 threshold (= 2200 + 3300) derived from the 3300.

**The instruments.** `core_model_check.py` is the second spelling of the same spec and reads every
number off the widgets: **154 checks, 0 failed**. It is not enough on its own - a green checker
proves nothing - so `core_model_mutants.py` breaks `gui.py` on purpose, eleven times, each in a temp
copy and each naming the check it must redden: **11 mutants, 0 survived**. Its first draft reported
two holes that were not holes: one mutant *crashed* the checker (a crash and a failure leave the
same failure count - CLAUDE.md 0.6), and one reddened a check whose name carries a prefix, which an
equality match read as "survived". So it reports three things, not one: crashed / reddened the wrong
check / reddened the right one. DECISIONS_2 578.

`_tools/avb_from_log.py` itself had three defects, all of the "wrong ruler, no error" family: the
undeduplicated press straddle, the collapse at the end of the recording averaged into the stall
band (it is a different regime - pressure still falling across the whole run, temperature collapsing
with it), and the pre-start rows (`GameActive = false`, 0 PSI) dragging a 0 into the band. The
dashboard's claim that "750 is not in the band" was mine and was wrong.

**Not verified:** nothing was pushed to Studio, Play was never entered, and no window appeared on his
screen - this is the desktop side, and the console is verified by reading numbers off its widgets,
not by looking at it. `a = 375` (three banks at PW5) is **three times** the fitted range (25..125)
and is an extrapolation, labelled as one. Whether "三个激光" means three banks is asked in
QUESTIONS.md R9, and the 3000-vs-3300 in our own `Config.Vent` in R10. See PROGRESS.md Phase 135,
DECISIONS_2 574-580, docs/SYSTEMS.md 2.27, docs/SNIPPETS.md 5.40.


### Phase 136 - three coolant pumps, and the last of the three controls

**No game code was changed this phase either.** "冷却控制呢？三个冷却泵分别控制" - the third of
the game's three control means (CLAUDE.md 1.2: AVB venting, CBL strength, the Isotope E cooling
loop) is now on the console. Three pumps, each held at 0..3, each level removing **120 degrees a
tick**, added as its own term:

```
T' = T + baseFluc * pMultiplier + noise(t) - 120 * (p1 + p2 + p3)
```

**The constant is read, not remembered.** `_tools/coolant_from_log.py` (new, rc 0, the
`avb_from_log.py` shape) prints the strongest of the three sources:

```
predDT * 5  ==  65*sum(cbl.level) - 120*sum(coolant.levels)
477 records, maximum |error| = 0.0
```

The shipped recording carries the original's own per-tick prediction, and that identity holds on
**all 477** of them with an error of exactly zero - so both constants in it come off a running game
rather than out of a source file (the other two sources, `Data/TRGWeb.luau:178` and our remake's
`Config.Sim.PumpCooling = 120`, are quoted rather than read).

**But the identity is satisfied by three spellings and the tool prints all four.** `sum(cbl.level)`,
`sum(level where active)` and `coolant.sumLevel` all read 477/477 - this log cannot tell them apart -
while `sum(cbl.power)` is **rejected 0/477**, which is why the other three are worth reading at all
(`power` is a different quantity wearing a similar name: it reads 10 at level 0 and 100 at level 4,
where `level` is an index). An identity with no counter-example beside it does not say whether it
recognised the expression or was merely loose. DECISIONS_2 582.

**Three placement decisions** went with it, and they are the same question CLAUDE.md 0.31 asks of any
spec - *what does this override?* (DECISIONS_2 581). The cooling is **its own additive term** rather
than a negative `a` fed through his fitted line, because that line is gated by the "off adds nothing"
rule and a dark laser bank is not a reason for a pump to stop working - the log has **84 records** at
CBL sum 0 with the pumps at 1, 2 or 3, so the original itself ran that way.
**CORRECTION 2026-10-16: the count is right and the inference is not.** Split by the log's own
`stats.GameActive`, **not one** of those 84 records was a machine being simulated - 62 are the
pre-start stretch (`tempF` 0, `fluctuation` 0) and 22 the post-collapse tail (`tempF` 1063,
`fluctuation` -1255) - so the log does **not** show the original cooling with the lasers dark, and
it does not carry the placement. What still does is the exact identity above, which holds on all
477 records and belongs to no state at all. The same question is asked again - out loud, and with
the empty groups printed as `none` rather than skipped - in `_tools/passive_from_log.py` section 4;
DECISIONS_2 594, CLAUDE.md 0.31 (1). It is added **outside**
`pMultiplier`, because no source puts a pressure factor on it. And the **stall still out-ranks it**,
which preserves the invariant the checker already held him to: a stalled, dark reactor falls at
exactly 586, not at 586 plus a pump term.

**What the log's behaviour half says, and does not.** Grouped by the (C,K) pair held, **6 of the 14
non-zero settled readings** sit within 100 degrees of the line (the game adds its own random term).
The misses are named rather than averaged: the four groups whose median is exactly 0 are the
**pre-start** stretches (`GameActive = false` - the chamber is not being simulated, so nothing moves
whatever the line says), and C3 K9 reads -436 against a line of -885 because it is the **terminal
collapse**, a different regime. The one same-C pair with enough samples (CBL held at 15, K 0 to 3)
gives **-96.7 a pump level** against the model's -120 - and the boundary is written beside it: those
two stretches are far apart in time, so the reactor's own drift is inside that difference. It is a
consistent reading, not a second measurement of 120.

**A regression over this log reads LOW** (`52.68*C - 91.64*K - 6.55`), and that is the sample rate,
not the model: the recorder samples faster than the game ticks, so per-sample differences attenuate
the fit. The two readings do not disagree - one measures the arithmetic, the other measures the
sampling - and the identity is the one that pins the constant.

**One divergence is left standing rather than smoothed** (QUESTIONS.md R11). His fitted heat line is
about **2.6x** the original's 65 per CBL level (measured: `ACTIVE[row][0]` is 6.8..7.24 per unit of
`a` against 65/25 = 2.6, a ratio of 2.638 at row 1). So in *this* console's currency a pump level buys
less than the original's own heat/cool ratio implies: the original's nine pump levels (1080) outweigh
its maximum laser heat (975), where here the same nine take off **41.2%** of three maxed banks as row
1 writes them (39.2% at row 2, 35.0% at row 3) - before the press multiplier, which cuts it further.
The constant is the measured one and the arithmetic was not rescaled to hide that.

> **[Phase 137 correction, kept rather than edited away]** Those three percentages were measured
> under the *pre-correction* unit, where the banks and the pumps were **summed**; the paragraph above
> is what was true then. After the correction both are means: three maxed pumps take off **360**
> against the original's **1080** (exactly a third), which is **39.8%** of three maxed banks at row 1
> (38.2% row 2, 26.0% row 3) - the shares nearly unmoved, the absolute number a third. The 2.638x
> slope ratio is **per unit of `a`**; the same act (one notch on each of the three banks) is 0.88x.

**The instruments**, with two traps found on the reading side rather than the model side:
`core_model_check.py` is now **168 checks, 0 failed** (the second spelling is
`his_cooling(levels) = 120.0 * sum(levels)`, his literals and not a call back into `gui.py`), and
`core_model_mutants.py` is **17 mutants, 0 survived or reddened the wrong check**. The first trap is
that **a value may appear in a check's text but never in its address** - the readout's *key* was
built from the constant (`"cooling  -%g x K"`), so the mutant that changes the constant **crashed the
checker** with a `KeyError` instead of reddening an assertion; both lookups now go through
`readout(values, "cooling")`. That is the same trap as Phase 135's `stallout pres <= 2200`
(DECISIONS_2 583). The second is the one from Phase 131: three new checks first went red on sub-unit
residuals (`691.0` against `691.0244...`) because a **rounded screen reading was compared against an
unrounded float** - the fault was in the checker, not the model.

**Not verified:** nothing was pushed to Studio, Play was never entered, and no window appeared on his
screen. The console is verified by reading numbers off its widgets, not by looking at it - **the
window has never been screenshotted, and nobody has been asked whether it is usable.** `a = 375`
(three banks at PW5) remains an extrapolation, and so are the cooling assertions that sit on it.
"三个冷却泵分别控制" was read literally as three pumps with a 0..3 each, which the game's own
`Engine.luau:110` and the log's per-pump distribution (`0 x696, 1 x489, 2 x11, 3 x235` - level 2
appears only 11 times, so the three really were set separately) both support; that is still my
reading, not his words. See PROGRESS.md Phase 136, DECISIONS_2 581-583, docs/SYSTEMS.md 2.28,
docs/SNIPPETS.md 5.41.

### Phase 137 - the correction: a mean, a mean, and a stall that swallows the whole tick

He sent back a spec prefixed **`Correction:`**, and it changed three readings of the console's core
model. Nothing in the game itself was touched, nothing was pushed to Studio, and Play was never
entered. The three deltas:

| # | was | now |
|---|---|---|
| 1 | `a = c1+c2+c3` (the three banks **summed**, max **375**) | `a_avg = ((c1+c2+c3)/3)*25` (their **mean**, max **125**) |
| 2 | cooling `= 120*(p1+p2+p3)` (summed, max **1080**/tick) | `((p1+p2+p3)/3) * 120` (a **mean**, max **360**/tick) |
| 3 | the stall wrote **`fluc`** (a *rate*) and the tremor still rode on the reading | `dT = {P <= 2200: -586, ...}` - the stall replaces the **whole** `dT` |

Both means are "divide that same sum by three", so **both of the console's controls shrink to a
third** at once. The *share* barely moves (three maxed pumps take 41.2% off three maxed banks at row
1 before, **39.8%** after; 38.2% at row 2, 26.0% at row 3) because the heat side shrinks with it -
**the absolute number is what changed**. The constant 120 was not edited; the thing it multiplies
was.

**His worked example reproduces item by item** (`c = 5/3/1`, `p = 2/2/2`, `T = 12000`, `P = 8000`,
`t = 1`): `a_avg` 75, row 1, base heat **561**, `p_mult` 1, `coolant_effect` **240**, `noise(1)`
**55** (54.665213986169604), `dT` **375**, `T'` **12375** - every one of them read off the widgets,
against a second spelling written with his literals.

**Two things the correction did to the books, in opposite directions.** It **retired** the `a = 375`
extrapolation (QUESTIONS.md R9 (2)): the fit spans `a = 25..125`, and three maxed banks are now
*exactly* 125, so the panel cannot reach outside the fitted band at all - not capped, just out of
range. And it **enlarged** the R11 divergence to its literal size: three maxed pumps take off **360**
here against the original's **1080** - exactly a third. R11's table is now split into two rows
because one phrase ("per level") was carrying two candidate bases: the same act (one notch on each of
the three banks) is **0.88x** the original's, while the slope **per unit of `a`** is **2.638x**. Both
numbers are right; they measure different things.

**The stall entry is filed as QUESTIONS.md R12** - a record, not a question, because his `dT` is
later than that older `fluc` line and says something different. The two readings only separate when
the lasers are lit (`noise` scales by `a_avg/25`, so with every bank dark its amplitude is zero and
the two agree bit for bit). The checker therefore drives all three banks to PW5 *and* the press into
stall, and prints the margin: **44.24123751141943 degrees** on that tick, where his literal says 0.

**201 checks, 0 failed; 23 mutants, 0 survived or reddened the wrong check** (up from 168 and 17).
The part worth keeping is the **four defects in the checker itself**, all green wrong rulers:

- **a check written on his worked example could never bite.** The mean of an arithmetic triple *is*
  its middle term, so at `c = 5/3/1` the mean is 75 - bank 2's own value - and "the mean" and "a
  glance at bank 2" came out identical. The whole section moved to the asymmetric `125/50/0`
  (`a_avg` 58.33, no bank's value) before `...nor any one bank` had teeth at all.
- **the two spellings do not agree bit for bit, and the reason is not the model.** `gui.noise` and
  the hand-written one differ by **7.10543e-15**: **CPython 3.12+ makes `sum()` a compensated
  (Neumaier) sum**, so it lands closer to the true value than `a + b + c`. One named tolerance
  (`1e-12`) with its reason printed on the line, **everywhere else still bit-exact** - and the gap is
  twelve orders below the smallest thing that check has to catch (swapping two amplitudes = 2.4
  degrees).
- **an assertion's position is part of its meaning.** "The pumps start dark" was written after a
  section that had already moved the pumps, and went red - because **`Console.reset()` starts a run,
  it does not restore a control position** (it never touches the banks' or pumps' radios). It
  reddened for a reason that has nothing to do with the console changing; it moved to the opening.
- **one mutant had no teeth.** Its conditional landed in the `base` slot of the return tuple instead
  of the `actual` slot the check reads, so `actualFluc` stayed -586 and nothing reddened. The runner
  reported `HOLE` - which is what "the checks have no teeth" looks like too. The two holes need
  opposite fixes.

**A third thing this round needed** (DECISIONS_2 584): a correction is not only an addition, so the
question to ask it is **"what does it override, and what does it retroactively confirm?"** One of the
three deltas had a shape the other two did not - a *branch's precedence* rather than a unit - and the
correction also **confirmed** a number the file already had (row 0's `T < 5600`, which is `STATE_MIN`
/ `Engine.luau:320`), so the check now compares against that rather than restating the constant.

**Not verified:** no screenshots, nobody asked whether it is usable, and the **UI is unchanged** (the
same radios) - the model's reading of them is what moved, so "does it look different?" answers "no",
and that is not a missed verification. Nothing was pushed to Studio; the correction was not verified
against our own game (two separate lines - this console models the *original*). R11 is not resolved;
it is now three times as large. See PROGRESS.md Phase 137, DECISIONS_2 584-588, docs/SYSTEMS.md 2.29,
docs/SNIPPETS.md 5.42.

> **[Phase 138 correction, kept rather than edited away]** "it is now three times as large" **and
> its literal size of 360** held for part of one day. The next message the same day took the average
> back off **the pumps only**, so cooling is `(p1+p2+p3) * 120` again (max **1080**) and the R11
> divergence on that side is **zero**. The two table rows above (0.88x / 2.638x) are unaffected - they
> are the heat side, and the heat side did not move. See the Phase 138 section below.


### Phase 138 - taking the average back off the pumps: a sum again, and a receipt left standing

He sent four words and a verb: **"冷却别用平均，重写写一下"** - *don't use the mean for the cooling,
rewrite it.* No numbers in it. It is a **retraction**, not an addition: the mean was his own, landed
by the Phase 137 `Correction:` above, so the question this round had to answer was not "what does it
add" but **"which lines does it reach"**.

**The two means had the identical shape and opposite fates.** Phase 137 divided two sums by three -
the laser banks' and the pumps' - so the sentence could not be resolved from the shape. **One stays,
one goes**, and the reason is asymmetric:

| | Phase 137 | now | why |
|---|---|---|---|
| `a_avg = ((c1+c2+c3)/3)*25` | mean, max 125 | **unchanged** | the fit was done over `a = 25..125` - **one** laser's worth; three banks summed run three times outside it |
| `coolant_avg = (p1+p2+p3)/3` | mean, max 360 | **retracted → `(p1+p2+p3)*120`, max 1080** | the pump's 120 was **read off a running copy of the original**, and it multiplies a sum there; **there is no fitted band to stay inside** |

`120` was not edited either time; what it **multiplies** is what moved. The sum is what all three
sources say - the original's own prototype (`Data/TRGWeb.luau:178`), our remake
(`Config.Sim.PumpCooling`), and the strongest one, the shipped log's identity of 477 ticks with
**maximum error exactly 0.0**. So this is the model **re-agreeing with its own evidence**, not a new
number.

**His worked example's tail is the receipt of the retracted reading.** The first five items (`a_avg`
75, row 1, base heat 561, `p_mult` 1, `noise(1)` 55) are untouched; the last three move:

| item | his (mean) | now (sum) |
|---|---|---|
| `coolant_effect` | 240 | **720** |
| `dT` | 375.465… (shown 375) | **−104.53478601383044** (shown **−105**) |
| `T'` | 12375 | **11895** |

All three old numbers **stay in the checker** - they are the receipt that the earlier reading was
really applied, not a misremembering (same rule as CLAUDE.md 0.14/0.29: the wrong ruler's conclusion
is kept, uncut, with a marker). But **only 720 is asserted**; "his 240 is 720/3" is a `print`,
because an identity that cannot fail is noise (CLAUDE.md 0.31 ① - *to make this red, what has to be
present?*). So "his worked example reproduces" now has a precise shape: **the first five items
verbatim; the last two belong to a different reading, and that reading was retracted.**

**Three user-visible strings moved with the model, and no check reads any of them.** The pumps'
`LabelFrame` caption, the readout row's label and the `on_coolant` log line all said "mean". The
checker **cannot** see them **on purpose**: it addresses that readout **by prefix** because the label
embeds the tested constant `120`, and a constant in the *address* makes the fetch blow up (`KeyError`)
rather than the assertion go red (DECISIONS_2 583). The price is explicit: **"caption says mean,
arithmetic does a sum" cannot go red here.** The only defence left is a grep after the edit, and the
only surviving hits are the deliberate historical quotations.

**201 checks, 0 failed; 23 mutants, 0 survived or reddened the wrong check** - unchanged counts, and
no check was deleted or turned green: two pump mutants were **re-anchored** and one **renamed**,
because a spec visited twice has **two** wrong readings and a mutant must redden on the one that was
*pointed at*. The old mutant was "the mean goes back to being the sum"; it is now *"the pump sum is
divided by three again, as one reading of the spec had it"* - **the middle reading is the one this
message names.** One more, smaller: a comment's **reason** evaporated with the change (the row-1
screening rule explained itself by "a mean puts a division in the number"), and reasons expire
silently - the rule stays, the reason is replaced.

**What R11 looks like now:** the cooling half is **zero** - same constant, same unit, all three
sources agreeing. What remains is entirely the heat side, and it does not go away:

| row (three maxed banks = `a_avg` 125) | three maxed banks' heat | 1080 as a share | the original's own |
|---|---|---|---|
| 1 | **903.8** | **119.5%** (**pumps win**) | 1080 against 975 → **110.8%** (pumps win) |
| 2 | **942** | **114.6%** (**pumps win**) | same |
| 3 | **1384** | **78.0%** (**heat wins**) | - (the `+534` term takes no `a` at all) |

So **"the original's nine pump notches (1080) beat its own maximum laser heat (975)" is a property
this console now has too** - the same number beating heat of the same magnitude. **Option B retires**:
what it wanted to restore was exactly that ratio, and the sum hands it back **with no rescaling
whatsoever** (317/level never entered `gui.py`). **C stays open** - those three heat values are the
checker's own output from his literals, and row 3 is the row where heat still wins.

**Not verified:** no Studio, no Play, not a byte pushed, **no window appeared on his screen**; the
console has still never been screenshotted and nobody has been asked whether it is usable. The UI
controls did not change (same radios) - what changed is how the model reads them, so "does it look
different?" answers "no". Not verified against our own game either: this console models the
*original*, and "the original's maxed pumps beat its maxed lasers" was measured **in the shipped log
and in this console's arithmetic**, not on our remake. R11 is **half closed, half still open**. See
PROGRESS.md Phase 138, DECISIONS_2 589-593, docs/SYSTEMS.md 2.30, docs/SNIPPETS.md 5.43.



> **[Phase 139 correction, kept rather than edited away]** "Option B retires ... the sum hands it
> back" **and** "R11 is half closed, half still open" both belong to the sum day. The operator put
> the mean back the same day, so **B is open again** and the divergence is three times wide. See
> the Phase 139 section below.

### Phase 139 - the cooling takes the mean again, and twelve signs get their new words

Two things this round, one in the game and one on the desktop.

**In Studio.** 「把那个BottomPipe文件夹里面的surfacegui里面的text的内容改成REACTOR FUEL TRANSPORT RING」
points at the **Folder** `BottomPipes` (plural) - not at the 27 **Models** named `BottomPipe`
(singular), which are a different thing in this place, and not at two signs reading
`FUEL TRANSPORTATION` that sit outside it. The folder holds **12 TextLabels**, all on pipe parts at
y = 46.5; all **12** now read `REACTOR FUEL TRANSPORT RING`, with **0** other text left in it.
Written in one `TryBeginRecording` block with **zero backslashes** (CLAUDE.md 0.10) and verified by
**reading `Text` back off the instances**, not by looking at a screenshot - so what the signs
*look like* (type size, wrapping, decal orientation) is not verified. **Three signs were
deliberately left alone** because they are not in the folder he named, and that is a reading of the
word "folder", not a measurement - say the word and they change in one pass.

**On the desktop.** 「算了冷却计算还是平均吧」 - the **fourth** visit to one line of `gui.py` in a
single day: Phase 136 a sum (this console's own reading of the three sources, not a word of his),
Phase 137 his `Correction:` making it a mean, Phase 138 「冷却别用平均」 taking it off, and now the
mean back - **written exactly as Phase 137 wrote it**. Only the pumps moved: `a_avg`, the banks'
mean, was already a mean and did not move, and the stall branch did not move. `120` itself never
changed; what it multiplies is what keeps changing.

**The three sources all spell the sum** (the original's own prototype `TRGWeb.luau:178`, our
remake's `Config.Sim.PumpCooling = 120`, and the shipped log's identity
`predDT*5 == 65*sum(cbl.level) - 120*sum(coolant.levels)` over all 477 records, max error 0.0) -
so this is the one line that does not listen to them, and it has now been turned over four times.
What that costs is a comment: the constants block carries **all four phases** (which day, whose
words, which version), because the only thing that stops the next round from turning it back is
the line remembering its own history. The **three operator-facing strings** (the `LabelFrame`
caption, the readout row, the `on_coolant` log line) moved back with it - and **no check can read
them**: the checker fetches that readout **by prefix**, because the label embeds the constant, so a
changed constant crashes the *fetch* instead of reddening a check. The defence is a grep after the
edit, which is exactly what caught it.

His worked example is back to Phase 137's reading (`coolant_effect` 240, `dT` 375.465..., `T'`
12375), and **Phase 138's reading stays on the page as a `print`** - 720 / -104.53 / 11895 is the
receipt of a retired reading, and "720 divided by 3 is 240" is not a line that can fail, so it is
not an assertion.

**The instrument itself had a real defect, and that is the round's actual find.** The mutant prover
came back with an **intermittent** `HOLE`: one run holed `the stall is not remembered for the
readout`, the next run reddened a *different* check. Two contradictory readings mean the problem is
not in the thing being measured. Measured cause: CPython validates a `.pyc` against its source's
mtime **in whole seconds** plus its size, most mutants here are the **same length** as the text they
replace, and a checker run takes about 0.85 s - so a mutant written inside the same second as the
version before it reuses the **previous** run's bytecode. The mutant never ran, and what it
reported was "these checks have no teeth", the exact reverse of the truth - and a conclusion that
sends you to **fix the checks**. Fixed with `-B` (write no bytecode) **plus reading that back**
(`__pycache__` is checked after the baseline and after every mutant) **plus asserting each mutant's
own new text is on disk in the file the checker compiles**; all three guards were negative-tested,
and the whole repo was swept - `selftest_boot.py` drives its mutant loop through **Lua** and
`check_fluc_steps.py` only writes output, so this file was the only place with the defect.

**Not verified:** no Play, no upload, nothing pushed to `ReactorBackend`, **no window appeared on
his screen**, and this console has still never been screenshotted. The UI controls did not change
(same radios) - what changed is how the model reads them, so "does it look different?" answers
"no". Not verified against our own game either: this console models the *original*. **R11 is back to
two open options** (keep the measured 120 / rescale to 317 a level / go and question the heat line
itself) - and the two reasons a pump is cheap here must be counted separately: his heat line is
2.638x steeper per `a`, and this divide by three, and **only the second is this console's own doing**.
See PROGRESS.md Phase 139, DECISIONS_2 594-599, docs/SYSTEMS.md 2.31, docs/SNIPPETS.md 5.44.

### Phase 140 - the whole spec, pasted: the heat becomes one curve, and `passive` walks out of the gate

The operator sent a full specification for the console's model and closed with
"不需要我多说什么了" - nothing more to explain. It restated a lot of what this console already
ran, and **restating is harder than adding**: you go and check anything new, and you nod at
anything familiar. So the round started with a three-column table - *what he wrote / what the
console makes of it / new or old* - and seven of its ten lines came back **old**. That table is
the evidence for "seven lines I did not have to touch"; without it there is only memory, and
memory does not tell you which line it skipped.

**Three lines were real, and all three are his.**

**The heat stopped being four lines and became one curve.** `pure_cbl = {a_avg <= 0: 0,
0.0516*a_avg^2 + 1.1*a_avg + 426}` - **the row is not in it**. The row's only job now is the
constant it subtracts: `passive = [-455.7, -400, -422, -22]` (was `-455.7 / -19.2 / 0.0 / 0.0`).
So "which row runs hot" changed its meaning: row 3 is the hottest not because its heat is
largest but because **its `passive` is the smallest (-22)**. Retired shapes - the four per-row
lines and the old table - **stay in the file as comments**, with a mutant that puts them back
(a rule that is only obeyed while someone remembers it has been forgotten once already).

**`passive` moved outside the "off means zero" gate, and that is the round's largest change.**
The old shape was `actual = 0.0 if power <= 0.0 else base * amp`, with `base` carrying the whole
row - so **a console with every bank dark held exactly still**. His spec puts the zero gate
*inside* `pure_cbl` and leaves `passive` outside it: **row 1 now cools by 400 a tick where
yesterday it was 0.** A new tool was written to ask the shipped log about it,
`_tools/passive_from_log.py`, and the log answers with a **negative result**: all 39 records with
`CBL sum 0` and every pump off have `GameActive` false, and so do the 84 from the cooling side -
**there is not one live core with all four controls off in that recording**. The four numbers are
implemented as he wrote them, and the log neither confirms nor denies them.

**The pressure band multiplies one term.** It used to multiply the whole `base`, `passive`
included, so the doubling band doubled the cooling too. His own note on the line says "只乘主动加热"
- **same constant, same branch, moved one parenthesis out, and it is a different rule.**

**The pressure recurrence he pasted is not new.** `fan_pressure_drop`, `p_base`, `p_temp_mult`,
`dP` are four-for-four the line this console has run since its first version - which is
`calculation.luau:34` **minus its PEA term**. Since `PressureBenefitPEA[1] = 0`, **his line is
exactly the PEA-level-1 case**: the two spellings agree word for word with PEA off and only part
company at level 3 (+75) or 4 (+150). Kept as it is, with a source note above `FAN_DRAG`, and
the question of whether PEA belongs here at all filed as **QUESTIONS.md R13**.

**His own state block is a worked example** - he did not send one this time. Driven one tick
(`c = p = 0`, `fans = 6`, `T = 20000`, `P = 7000`, `t = 1`): **T 20000 -> 19578**, `dT = -422`.
The pressure half gives **136.835 and not 140**, because that line reads the tick's **ending**
temperature (20000 would give 140) - **two instants, not one error** (CLAUDE.md 0.27).

**Numbers the checker pins:** `pure_cbl(125) = 1369.75`, so the top of the fit is **914.05 /
969.75 / 947.75 / 1347.75** by row (the screen shows `914 / 970 / 948 / 1348`), and a full
coolant 360 against those is **39.4% / 37.1% / 38.0% / 26.7%** where the original's own line is
110.8%. **"How much steeper is his heat line" is no longer one number**: the curve's slope
`0.1032a + 1.1` against the original's 2.6 per unit of `a` is **1.42x at a = 25, 2.41x at 50 and
5.38x at 125**, where the retired straight line was 2.638x everywhere - which is why the ratio
quoted across the older docs needed a word, not a new constant.

**And the round found a number that was written rather than measured.** The cooling side's
disproof sentence read "of those 84 records, 79 are the pre-start stretch and 5 the post-collapse
tail" - and **neither of those came from a reading**. Every criterion that can be tried on those
84 records (pump level, `tempF`, `fluctuation`, `cbl.sumLevel`, `active`) produces **one split and
only one: 62 / 22**. The two invented numbers sum to exactly 84 and sit in exactly the right
sentence, and they had been copied into **three** places (`luau-windows/gui.py`,
`_tools/coolant_from_log.py`, this README), each carrying the tone of a measurement. All three
keep the original sentence and carry a dated correction naming which half was measured.
**A number being measured does not mean the one next to it was** - and this is the same family as
CLAUDE.md 0.18, aimed at the writing half instead of the reading half. One more of the same shape:
`gui.py` said the slope ratio was "5.39x at the top of the fit", which is what the number looks
like before it is computed; it is 5.38x, and the checker prints the same.

**Not verified:** no Studio, no Play, no upload, **no window appeared on his screen**, and this
console has still never been screenshotted or reviewed by anyone. The UI controls did not change
(same radios) - what changed is how the model reads them, so "does it look different?" answers
"no". `passive` is implemented from his literals with **no external evidence at all**. And this
console still models the *original*, not our remake - nothing in it would notice if
`Engine.luau`'s constants fell behind.

`python -X utf8 luau-windows/core_model_check.py` -> **232 checks, 0 failed** (was 201);
`core_model_mutants.py` -> **28 mutants, 0 survived or reddened the wrong check** (was 23) - and
two of the five new mutants are "put the old shape back", because after a spec is changed once,
**the mutant that most needs teeth is the one that reverses it**.
See PROGRESS.md Phase 140, DECISIONS_2 600-605, docs/SYSTEMS.md 2.32, docs/SNIPPETS.md 5.45.

### Phase 141 - the floor vent becomes electromagnetic, and "the size must not change" becomes a check

The operator handed over `BottomChamberMAchine.gltf` from the Roblox export and said what it is
and what it should become, with a hard constraint in the same breath: *"it's that kind of floor
vent grate you get in the floor, but I want to change it into the electromagnetic kind, you know
what I mean, do it for me, and the size must not change."*

Measured first: it is a shallow grate, **8.8668 x 8.2505 x 0.6250 studs**, 15 mesh parts and 154
triangles. The diamond-mesh face everyone reads as geometry is a **128x128 X decal on a degenerate
quad, tiled 16.15 x 6.15 times** - two triangles. Take the decal away and what is left is a frame,
a black base plate and two olive strips.

So the rebuild deletes exactly one thing (that decal), changes exactly one property (the two
`Neon` strips become `EM_Field`), and adds **4 objects / 23 pieces** inside the rim: 13 field
blades, 2 side rails, 2 coil housings and 6 coil rings. Nothing was authored from a size - the
parts were placed in the **black base plate's own frame**, and two inputs were read rather than
assumed: which side is up (asked of the decal) and how high the ceiling is (the highest existing
vertex on that side, +0.275 above the plate face). The tallest new part reaches 0.235.

The constraint is enforced where it can actually fail: the script re-imports the shipped `.glb`
**and** the `.fbx` and compares three sizes and three minima against the file that came out of
Roblox. **14 checks, 0 failed**, largest deviation **3.81e-06 studs**. That check earned its keep
immediately - the first build was **2.37 studs too tall** because it authored in glTF node space
and guessed which axis was the thickness (the importer permutes: the node table says
`[8.075, 0.35, 3.075]`, the imported object says `8.075 / 3.075 / 0.3500`). Every number in the
build loop was right; only the axis was wrong, which is invisible from inside the loop.

Two more defects the same check surfaced: the FBX came out **anisotropic (7.83 x 7.23 x 0.34)**
because the parts hang off a `Model` empty and hand-scaling both parents and children scales some
of them twice - `global_scale` is the tool, touch no transform; and nine FBX material references
were being dropped because the glTF importer shares one mesh datablock between nodes that carry
different material slots - `make_single_user(obdata=True, material=True)` before exporting, then
read the materials back by re-importing rather than trusting the absence of warnings.

Deliverables in `D:\BlenderRobloxTestProjects\FloorVentEM\`: `.glb`, `.fbx`, `.blend`, three
previews. **Import the `.fbx` with 5.902 in the dialog.** The `.glb` is 1:1 in Blender units, but
the glTF path into Studio lands **1.6943x** (`10 / 5.902`, measured in Phase 83) - that constant is
written in a dozen places in this repo and the first draft of this delivery still said "the glb
drops in at the original size". A known constant that is not applied in the one sentence that
ships is not known; corrected in the script, PROGRESS, README and CLAUDE.md. **Not verified:** no Studio, no Play, no upload
(the API key and creator id are still unset, so he drags these in himself); **emission has to be
set to `Neon` in Studio** - glTF emissive does not necessarily land as Neon; and the shipped file
was compared against the exported original, **not** against the instance in the place. The
previews look unpolished because the renderer has no bloom, contact shadow or environment - that
is the picture, not the asset.

Also this round, and it will bite the next Blender script: under `--background
--factory-startup` a **relative** output path resolves against the **drive root**, not the process
cwd (`os.getcwd()` kept reporting `D:\rblxTRGproject`), so three renders printed `wrote ...` and
landed in `C:\_tools\...`. Directories and all. A bare filename instead throws. `preview_gltf.py`
now calls `os.path.abspath` where it decides where the bytes go.

See PROGRESS.md Phase 141, DECISIONS_2 606-609, CLAUDE.md 0.37.

### Phase 147 - "a cooler laser modelled on the CBL": Mk4, and a checker that had to be red three times

The brief, verbatim: "那个仿照CBL做个更帅的激光（blender". An art task, not a gameplay one:
zero lines of game code, zero bytes pushed to Studio. The reference is the Mk3 CBL at
`Workspace.ReactorCBLs.Reactor_Laser_Mk3_*` as **measured in Phase 23** (98.0 x 36.7 x 36.7
studs, grey hull, brass collars, cyan accents, hazard plates, a lit cyan aperture at +X).
**Studio was not connected this session**, so no side-by-side measurement of the original was
taken; the proportions are authored from that historical reading.

Three changes, all about what a laser looks like rather than what it measures: the closed tube
becomes an **open one** (two cowlings with windows on +/-Z crossed by six ribs, through which a
ribbed plasma tube wrapped in three white helices is visible - and that core is its own object
whose origin sits on the barrel axis, so it can spin in Studio); the flat muzzle becomes a
**three-prong claw** around a recessed lens and two floating emissive rings; and the breech gets
a **power stack** of three capacitor drums with cyan charge bands, so the machine has a silhouette
at both ends. Four objects - `Mount`, `Body`, `Prongs`, `Core` - every origin at (0,0,0), which
is the trunnion / barrel axis and therefore the pivot. Delivered assembly box **64.592 x 23.040 x
27.360 studs**, **74004 triangles**.

Deliverables in `D:\BlenderRobloxTestProjects\CblLaserMk4\`: `.fbx` (913180 B), `.glb` (3781416 B),
`.blend`, four previews from the same run. **Drag the `.fbx` in and type 5.902**; the `.glb` route
is 1.6943x too big. Materials do not survive Roblox's importer - it splits the mesh per material
(which is what we want) and then discards them, leaving Plastic + grey - so
`_tools/apply_cbl_laser_mk4_materials.luau` repaints by **absolute size** afterwards, touching only
`Color` and `Material`.

Four checks, all green: the re-import checker (`cbl_laser_mk4_check.py`) **86 ok / 0 failed**,
which loads both formats back, measures node names, the six assembly faces, every origin, every
per-material box edge, triangle counts and watertightness, and then makes **the two exporters
witness each other** - the only row that quotes no hand-typed constant; the table transcription
check (`check_mk4_mat_table.py`) **30 ok / 0 failed**, tying the build log's size table, the build
script's linear colours (through sRGB) and the Luau's integer triplets together, and refusing to
read a log older than the delivered `.fbx`; a Lua 5.1 stub harness that runs the shipped `.luau`
against a fake `workspace` **18 ok / 0 failed**; and seven mutations, each red on a different
assertion family, with a `none` control at 86/0.

Three of those reds were real defects. `bmesh.ops.bevel`'s `material=-1` means **slot 0**, not
"inherit", so the whole muzzle came out hull-coloured while triangles, sizes and the bounding box
were perfect. A duplicated revolve profile endpoint produced **8468 zero-area triangles** -
invisible to every measurement except the one that looks at faces. And the watertightness
criterion itself was wrong: the first version counted any edge not used exactly twice, reporting
**48 holes** on the Body that were all at x = 23.36 (design `X_SHROUD1`), each used **four**
times, because a 48-gon Hull cap and a 48-gon Dark cap sit face-to-face at the same station and
radius. A closed surface has every edge used an **even** number of times; "twice more than it
should be" and "once" are different failures. The `split` mutation also slipped through the
cross-format row until that row compared **world boxes** as well as local sizes - a pure
translation changes neither size nor triangle count.

One measurement worth keeping: the `.glb` is byte-identical across rebuilds
(`e1980dcedff7cb43a2f442e8797d1d62`), while the `.fbx` differs by **339 bytes of 913180** in
sparse 4-byte creation-time/UID fields. So an FBX delivery can only be verified geometrically,
never by hash - and the two formats' fates must not be extrapolated from each other.

**Not verified:** no Studio (so the `.fbx` was never imported and the material script never ran on
a real import), no side-by-side with the Mk3, no Roblox render of the Neon parts, no Play, no
upload, no cursor movement. See PROGRESS.md Phase 147, DECISIONS_2 631-638, CLAUDE.md 0.41,
docs/SNIPPETS.md 5.50.

### Phase 148 - the Temperature page: a weighted `a_eff`, a meltdown wall, and three E-Vents

The operator handed over `https://reactor.fandom.com/wiki/Temperature` with "基于这个继续完善GUI".
Nine tenths of that page agreed with the desktop console already; the one real disagreement was
how three laser banks combine into one `a`. The page is explicit:

> "The engine does NOT use a simple average; instead, it applies a hidden positional weight to
> each laser." `a_eff = 0.756 * L1 + 0.522 * L2 + 0.196 * L3`

so `Core.a_eff` replaces the mean that Phases 137-139 kept flipping between. **What identifies it
is the page's own pair of worked examples, not either one alone**: `(100,25,25)` gives `a_eff` 93.55
and **580.49 F/tick** against the page's ~580, and `(25,25,100)` gives 51.55 and **219.83** against
~220. The mean returns 50 for both, and it lands within about ten degrees of the *second* example -
so checking only that one would "confirm" the wrong reading. Three falsifications are now live
assertions, including the page's own prose percentages (51.3/35.4/13.3, summing to 1.0) which
reproduce neither example (they give ~304 on the first) because the coefficients sum to 1.474 and
are multipliers, not shares.

`a_eff` now tops out at **184.25** (all three banks at PW5), past the 25..125 band the operator's
fit was taken over. It is carried, not clamped: clamping to 125 would make "three full banks" and
"two and a half" the same heat, an equation no source contains (DECISIONS 641).

Two more pieces come from the same reading session. **The meltdown wall** (`CORE_MELTDOWN_AT =
39000.0`) is a latch, `Core.melted`, rather than a fourth `core_state` row - that return value
indexes `PASSIVE_ROW` and the pressure table. The crossing tick still reports its temperature and
every tick after returns `None`; the panel row reads `4 MELTDOWN`. The wall sits **below** the
slider's top (40,000), which is why the old "the temperature runs past the slider" section was
re-aimed at *which* limit stopped the model. **Three E-Vents** (`can_e_vent` / `e_vent`) are one-shot
switches at ~7000 F each, refilled by `reset()` (this console's shift boundary), floored at
`TEMP_MIN`, and they do **not** touch pressure - that is what separates them from the AVB.

**282 checks, 0 failed; 34 mutants, 0 survived or reddened the wrong check** (up from 232 and 28);
`pressure_parity.py` 24 / 0. The mutant run earned its keep this round by catching the checker
itself: `check("one press takes the wiki's ~7000", dropped, gui.E_VENT_DROP)` compared the result
to the constant that produced it, so moving the constant to 6500 left it green and only the
neighbouring temperature check went red (CLAUDE.md 0.31 (6), DECISIONS 642).
No game code changed, Studio was not connected, and the desktop window was not screenshotted.

### Phase 149 - the Continuation icon: a hexagon that does not close

The operator asked for a 1:1 icon for *The Reactor Game - Continuation* - "别太复杂" (not too complex),
"要体现Continuation" (it has to read as continuation). The mark is the facility's own hexagon drawn with
one edge left open, and the open end carries an amber arrowhead running clockwise: a closed hexagon says
"a built facility", the gap plus the arrow say "it is still going". A small plasma-cyan hexagon at the
centre is the core - without it the mark reads as a washing machine's "rinse again". No badge, no footer,
no manufacturer mark: three things, not the cover's four.

**The concept is a pair of rules that can go red**, not an eyeball. C7 asserts the gap is 12%..55% of R
(42.0%), that the arrow tip is 8..gap px from where the stroke starts (48.9), and that the tip sits on
the edge's own line (0 px); C8 asserts that the head's direction dotted with the stroke's run direction
is 1.0. Both failures still look like a perfectly good icon at 64 px, which is why they are measured.
`continuation_judge.js` reads 12 ok / 0 failed and 24/24 mutants light a rule. The layer runway went
past decoration for the first time: all six parts (loop / head / core / glow / scan / vignette) change
pixels when switched off.

The 1024 master is 606769 B / md5 `a0baba54…`, byte-identical over nine renders **within one machine
state** - an earlier batch (535110 B / `2a3a83db…`, 2/2 identical) is a second, equally stable rendering
of the same page: mean 0.705/255 apart, max 57, 2191 pixels > 8 (0.21%), and indistinguishable at 64 px
(max 3, no pixel > 8). Forcing software and forcing GPU rasterisation both reproduce the shipped one, so
the mechanism is unestablished; identify the file by md5 and the picture by pixels, with the magnitudes
written down (DECISIONS_2 651). The 512 upload file (153156 B, `optimize=True`) is a LANCZOS downscale
of the judged frame, not a second render that was never judged; a native 512 differs by mean 1.40/255
(3.1% of pixels > 8, all on glyph edges) - the same picture twice.

The font probe corrected an old reading: `var(--cond)` measures bit-for-bit equal to Arial Narrow
(982.38 at 100 px), and Phase 144's 1088.55 is exactly Arial Narrow's own width at 116 px - so that
build did use Arial Narrow and the "not installed" explanation was wrong. The two-line decision stands
(the narrowest candidate, Impact, still needs 976 > 864). New lesson in CLAUDE.md 0.42.

**Not verified:** no upload (no `asset:write`), no Studio and no Play, no game code touched, Roblox's
crop of the icon was never measured, the 512 was not judged on its own (it inherits by construction),
and "does it look good" is a judgement, not a reading. See docs/COVER.md section 8, PROGRESS.md
Phase 149, DECISIONS_2 645-651, docs/SNIPPETS.md 5.52, docs/TODO.md 3.23.

### Phase 150 - the Continuation icon, reworked: the TRG mark, and an arrow that is the stroke itself

The operator looked at Phase 149's icon and said 「有点奇怪啊改一下，而且是trg的continuation，
你TRG也要有一定体现」 - it reads oddly, and it is *TRG's* continuation, so TRG itself has to show
up in it. Both halves of that sentence are now measurements.

**Why it read oddly, in one number.** The v2 arrow was a second object laid on top of the gap: its
base was 68 px across against a 13 px stroke. Every rule was green, because no rule asked whether
the head and the ring were *one thing*. v3 is a single open circle whose stroke ends in its own
triangular tip. C8 now asserts `baseOffRing` (the base centre sits on the ring: measured 0) and
`tipOffRing` against the tangential solution `sqrt(r*r + len*len) - r`, so "it is part of the stroke"
is a reading, not a hope.

**"TRG has to show up" became the game's own file.** The centre is `intro/assets/sm-core.png` - the
same asset the cover uses, referenced not copied (Phase 133) - clipped to r = 240 asset px to cut
away the mark's own ring. That radius is measured, not chosen: 1440 rays through the asset's alpha
give arms out to 236, an **empty band 237..241**, and the asset's ring starting at 242. Clipping at
240 keeps 4 px of margin above and 2 below; 3 px either way either shaves the arms' tips or leaves a
double ring, and both would be invisible at 64 px. C11 pins the asset by `src`, a square box centred
on the ring, and a clip strictly inside that empty band.

**One rule's two halves had to come from two sources.** C6 compared the page's `249.5 * S` against
the judge's own literal `249.5` - the §0.31 (6) shape: change one and it goes red, change both and it
stays green. The replacement is `_tools/continuation_ring_check.py`, which holds no radius constant
at all: it measures the ring in `sm-core.png` and the ring in the delivered PNG and compares them
(249.8 : 250.0 asset px, -0.22 within a +-3.0 band; stroke width -0.58). On its first run it went
red on a **correct** picture: coverage of the drawn ring is capped at `1 - 56/360 = 84.4%` by the
gap, while the threshold it was using is 0.90 - a check only a *failed* design could pass. The fix
is two thresholds (asset 0.90 / drawn 0.70), not a looser one.

**The gap has two numbers and both are kept.** The path opens it 56 degrees; the pixels say 39.38,
because the arrowhead is itself ink (66 px at r 242.2 = 15.6 degrees, so 56 - 15.6 is about 40.4).
The remaining 1.0 degree was not separated and is written down rather than smoothed away.

`continuation_judge.js` reads 12 ok / 0 failed with 31/31 mutants lighting a rule (C6/C7/C8 get two
mutants each). `cover_mark_check.py` gained `CLIPR` (default 0, so every earlier command is unchanged):
41011 ink px inside the clip, 22370 set aside outside it, recall 1.0000 at t <= 100. All six layers
still change pixels when switched off. The 1024 master is 620594 B / md5 `ea0107d6…` (3/3 identical)
and the 512 upload file is 169140 B / `7adad5da…`, a LANCZOS downscale of the judged frame.

**Not verified:** no upload (no `asset:write`), no Studio and no Play, no game code touched, Roblox's
crop of the icon was never measured, the 1.0 degree between the path's gap and the measured clear
opening is unexplained, and "does it look good" is a judgement, not a reading. See docs/COVER.md
section 8.7, PROGRESS.md Phase 150, DECISIONS_2 652-657, docs/SNIPPETS.md 5.53, docs/TODO.md 3.23.

### Phase 151 - a Rebuild icon: the ring is missing one bay, and that bay is being carried back

The operator's whole request was 「做个Rebuild的图标」 - make a Rebuild icon. Same contract as the
other two 1:1 images: a `cover/` page, a 1024 master, a 512 upload file, judged by instruments
rather than by eye, documented on disk in the same pass. Game code: zero lines.

**Same visual language, and the ring says something else.** Continuation's ring is cut open and the
cut end grows an arrowhead - it is still going. Rebuild's ring is **missing an entire bay**, and that
bay is **carried outside it**, in amber, with a dashed guide along the bay's mid-radius. So the idea
lands on three geometric readings, and each one fails in a way that still looks like a fine icon at
64 px: **R8** the part is the bay's twin (same 56 deg, same curvature) - otherwise it is decoration;
**R9** the part really is carried out (54 px, 39.24 px of clear air = 2.66 ring widths) - seat it and
the ring closes and *rebuild* disappears; **R10** the part is aimed at its slot (0.00 deg) with the
guide on that same radius - otherwise it is debris. "The ring has a gap" alone is not Rebuild; it is
Continuation's shape.

`rebuild_judge.js` reads 15 ok / 0 failed with 35/35 mutants lighting a rule (R6/R7/R8/R9/R10 each get
two, from two readings that can separate). `rebuild_pieces_check.py` is the second instrument and holds
none of the page's constants: it measures the ring in the asset and the ring in the delivered PNG
(249.8 : 250.0 asset px), counts bays in the band (one, 55.88 deg at 188.06), finds the part **by
colour** so a part at the wrong radius is still found, and reads the air in ring widths. 9/9 on the
master **and 9/9 on the 512**, which is judged separately rather than inherited.

**Four measurement errors, none of which reported an error** (CLAUDE.md 0.44). The scan was cropped to
the emblem's own square, which cut off the part that is deliberately outside it - "the part is not on
the picture" on a picture that plainly has it. Angular extent was binned per pixel, which left an empty
0.125 deg bin at exactly 180 deg and split one 56 deg arc into 19.6 + 35.6. The helper `angular_runs`
counted *gaps*, which is right for the bay and exactly inverted for the part (it reported the largest
EMPTY stretch, 160 deg at 80 deg). And thickness was compared as a ratio, which passed at 1.143 on the
master and failed at 1.286 on the 512 while the pixel *difference* was +2.0 at both - the denominator
carried the scale.

The pixel instrument's teeth were proven on three real broken renders, not on doctored JSON: part
seated (8/9 red, `bays` included), part recoloured Ready (5/9, `part_colour` leading), bay widened
(1/9 - only `bay_width`, which is what a good ruler does). All seven layers change pixels when
switched off. `bash _tools/icon_runs.sh {rebuild|continuation}` runs the whole chain and is idempotent
on the delivered files (both continuation md5s unchanged).

**Not verified:** no upload (no `asset:write`), no Studio, no Play, no game code touched; Roblox's crop
is still unmeasured; the subtitle is unreadable at 256 px (read as "THE READING GAME") and the font
size was not changed, because changing it would break the 1:1 layout; and the pixel instrument has only
been run at 1024 and 512 - below that its absolute-pixel thickness reading turns back into a ratio
problem. "Does it look good" is a judgement; at 64 px the read is a broken white ring, an amber arc in
the gap, and the word REBUILD, and at 256 px the verb it reads as is **"Arriving"**.

See docs/COVER.md section 9, PROGRESS.md Phase 151, DECISIONS_2 658-666, docs/SNIPPETS.md 5.54,
docs/TODO.md 3.24.

### Phase 152 - a Reimagine icon: one axis splits the same mark into two states

Three sentences from the operator: 「设计个TRG-reimagine的」, 「可以参考所有素材」, and the binding
one, **「别跟之前设计的一样」** - do not make it the same as the previous designs. Both earlier
icons are a centred emblem with a line of type underneath, differing only in what the ring says. So
this one changes the **topology**: one vertical axis (the emblem's own, x = 566) splits the picture,
and the same x cuts the word REIMA|GINE inside a letter gap that was measured with a `Range`, not
guessed.

**"Two states" had to be literal.** The mark is drawn **once** - a single `<img>` spanning both
halves - and the amber is a disc *underneath* it, radius = the ring's inner wall,
(249.5 - 15.2/2) x S = 291.22. So "both halves are the same bytes" holds by construction rather
than by resemblance, and the instruments only have to show it was not broken: the two copies of the
word share one box to 0.00 px (R3), and the ink coverage per radius matches between the halves to
L1/total = 0.0146.

`reimagine_judge.js` reads 17 ok / 0 failed with 32/32 mutants. R14 is the one this phase needed:
`clip-path: inset()` is measured from **the element's own box**, not the canvas, so the first
version's `inset(0 458 0 0)` left the white copy ending at 499 and the amber copy starting at 626 -
a 127 px hole - **while `getComputedStyle().clipPath` read back exactly right**. R14 rebuilds each
clip from its own element's box (`box.left + cR.left`, and the mirror for the other copy) and
requires all three to land on the axis.

`reimagine_pieces_check.py` holds none of the page's constants: it fits a circle to the white
ring's **outer** edge (577 rows, centre 565.29/399.63, r 310.00, worst residual 0.65 px), takes the
axis from that fitted centre, and measures the amber against it. The first version fitted the
circle to the amber's boundary instead and got r 274 with a 90 px residual, because the mark's own
arms and hexagons sit on top of the amber and a near-tangential hexagon chord hides a 113 px stretch
of the arc. 12 readings / 0 failed on the master **and 12 / 0 on the 512**, judged separately.

**The expensive lesson is about the ruler** (CLAUDE.md 0.45). The first version defined the seam as
"the leftmost amber pixel" and then checked "nothing amber is left of the seam" - a tautology: paint
amber 40 px further left and the seam follows it. The mutation lit **four other readings** and the
one it was aimed at never moved, so "four reds" hid "the right one stayed green". The seam now comes
from the white ink (the fitted ring centre) and the amber's left edge is what gets measured - two
independent sources, 0.71 px apart. Three more instrument bugs came out of the same selftest run: the
mutation loop shared a module-level `GEO` dict and a ring-breaking mutant poisoned the two after it
(3 false failures); a one-pixel antialiasing gap let the "longest run" band split and report the
picture clean; and the 512 was judged by a per-radius maximum that went red on the correct file
(0.283 vs 0.219 - raster noise), replaced by a normalised L1 that reads 0.01459 and 0.01479 at the
two scales.

The chain's teeth were shown end to end, not only inside the instruments: removing the emblem's clip
in a temporary page (one `sed`) sends the amber across the axis and turns **3 readings red**.
`bash _tools/icon_runs.sh reimagine` runs render -> judge -> pixels -> 512 -> pixels again -> md5; the
two older icons re-run byte-identical (`ea0107d6…`, `bf2545d5…`).

Master `cover/THE_REACTOR_GAME_reimagine_icon.png` 1024x1024, 577756 B, md5 `41b49a55…`, identical
across 5 renders. Upload file 512x512, 164879 B, md5 `8b08e786…`.

**Not verified:** no upload (no `asset:write`), no Studio, no Play, no game code touched; Roblox's
crop of a 1:1 is still unmeasured; 256 px and 64 px were neither measured nor looked at this time;
the pixel instrument has only run at 1024 and 512. "Does it look good" is a judgement - at 512 the
read is a white line-art mark on black on the left, solid amber on the right with the white lines
still on top, and the amber stopping cleanly at the ring.

See docs/COVER.md section 10, PROGRESS.md Phase 152, DECISIONS_2 667-674, docs/SNIPPETS.md 5.55,
docs/TODO.md 3.25.

### Phase 153 - the startup sequence gets a voice-over script, with timecodes derived from Config

「我要开始配音了，先来个反应堆开机的（先来个开机序列启动」 - the operator is about to record
voice-over and wants the reactor startup first. `docs/VO_STARTUP.md` holds two scripts: **A**, the
system announcement - the game's own 16 log lines, verbatim, at their real timecodes; and **B**, an
eight-line narration in English and in Chinese, each line backed by a source (no control rods per the
wiki, three Isotope E loops and five CBL power levels per `Config`/`Engine:Command`, coolant sensors
that drift per the wiki, and a closing beat measured in Phase 127: an unattended startup reaches
`Failed` **143.3 s** after `Running`).

The 16 timecodes are **derived, not copied**. The chain is `Config.Shift.StartupSteps` and
`Engine:AdvanceStartup` logs step N when the accumulated dwell reaches `sum(hold[1..N])`, so
`_tools/startup_vo_timing.py` folds that sum and emits the table; the doc's block is fenced by
`<!-- VO-TIMELINE:BEGIN/END -->` and `--check docs/VO_STARTUP.md` compares it line by line, exit 1
on any difference (verified red by editing one timestamp to 46.9, and verified that a missing path
crashes loudly rather than passing). It is a **drift** check: it catches "Config changed, doc did
not", not "Config is wrong" - the evidence for Config is the five captures behind Phase 65.

What the arithmetic surfaced is the useful part: **three places write two or three lines in a single
tick** - 1+2+3 at 0.0 s, 5+6+7 at 33.4 s, 13+14 at 82.2 s. The `SYSTEM LOGS` panel is a ticker, not
a narrator, so a voice artist reading those as three separate beats is inventing something the
machine never did. Each burst does have a long tail (29.4 / 11.7 / 27.2 s), so the script reads each
burst in one breath and then leaves the picture alone. The order **inside** a burst is not in the
bytes at all (Phase 65.2: the recorder sorts before dumping), so picking a comfortable order is not
an edit - but the finished cut cannot claim it was the original's.

The chain is a median, not a rule: four complete runs measured 91.4 / 112.6 / 114.3 / 151.7 s. Hence
the recording brief asks for one second of clean air either side of every line instead of locking
anything to a second.

**No original announcer exists to copy.** Filename search across the 429 audio files in
`TRG Sounds & Images pack/` finds no announcement; the only "startup" audio on disk is
`asstes/music/ReactorStartup.mp3`, the operator's own Portal 2 piano reference track. So the doc says
"there is nothing to reference", not "the original had no voice" - a sound could hide under another
name - and the tone choices are judgements that must not be written downstream as a restoration.

**Not verified:** not one line has been recorded; `est. read` is an assumption of 2.5 words/second
(when the first take exists, the number to revisit is that constant, not the timecodes); no Studio,
no Play, no upload, **game code 0 lines**; the teleprompter, the Chinese gloss and script B are
hand-written, so `--check` does not cover them.

See docs/VO_STARTUP.md, PROGRESS.md Phase 153, DECISIONS_2 675-679, docs/TODO.md 3.26,
QUESTIONS.md R15.

### Phase 127 - the two new monitor panels, in a running game

Phase 125 wired the alerts grid and the subspace forecast and verified them by requiring the real
modules in Edit mode. Both were owed a run in a live game, and 2026-10-14 provided one: the whole
`ReactorBackend` folder was pulled back and compared file by file first (14 same, 0 different), then
four clicked controls drove the chain from cold into `Running` with all four delivery lines and no
refusals.

The deep scan played on the capture's own offsets, to within one frame - announcement +0.00, beep
+3.350, verdict +5.051 (`HADEN THRESHOLD BREACH ~4:39 AM`, red), timeline +12.900, announcement off
+12.900, stop +14.634 against `TimelineOffAt = 14.63` measured off a 40-line per-frame sampler that
only writes when a flag changes. The seven EFE banners went visible on **one identical timestamp**
and hidden on another exactly 10.250 s later - a 0 ms spread, where the original's capture showed
70 ms. Both panels replicate: the 27 alert rows read identically from Server and Client, and the
client's announcement label holds the same verdict string.

Three things the live run measured that no module-level test could. The ping asset is 3.3493 s, so
`PingOffAt = 9.37` never gets to stop it - the sound ends itself 0.987 s early. The deep scan can
only ever return the breach verdict, because it fires inside `Starting` where `elapsed` is still 0,
leaving `untilEquinox` at exactly 720 inside the 900 s horizon; the anomaly branch is unreachable
under this tuning. And a start-up left to itself fails 143.3 s into `Running` (P.E.A stress reaching
100), which puts the Phase 124 end-of-shift screen in front of the player again - a second,
independent reproduction of the exact complaint ("suddenly the shift ended") that transport was
built for. Two of these are questions: QUESTIONS.md R6. See PROGRESS.md Phase 127 and
DECISIONS_2 531-538.


### Phase 128 - a whole shift, run to the quota ending, in a live game

Phase 124 connected the end-of-shift screen and live-verified only the **failure** ending; the same
screen's other ending - quota met - had never been exercised. It now has. **16 real clicks through
real ClickDetectors** took one shift from a cold machine to `phase=Report` with `Energy 512/512`:
4 for the boot chain, 2 fans off, 3 coolant pumps on, 6 CBL purges, 1 shutdown. Sixteen delivery
lines, zero `rejected:`, zero `[Gate] refused`.

The window read out **113.154 s** from `Starting` to `Running` against a `Shift.StartupSeconds` of
**113.39999999999999** - a number `Config` *derives* at load by summing the 16 `StartupSteps`'
`hold` values (an earlier note of "109.4" had missed the `hold = 4` step). 0.25 s apart is one
Heartbeat sample, so this is a free independent check on a derived constant. The other four
intervals land on their configured values too: `Booting → Ready` 13.501 against `BootSeconds = 14`,
`Stopping → Report` 4.571 against `ShutdownSeconds = 5`.

**The phase's real find was a defect in my own offline planner.** `_tools/quota_policy_sim.luau`
issued its set-and-forget block on the *loop's first iteration* - four `Update` calls after the
startup chain had already ended, i.e. four seconds of `Running` with **no coolant in the machine**.
With three CBLs at level 2 the entry temperature line runs `6 * 65 * 0.4 = 156 F/s`, so the whole
trajectory entered `Running` **615 F hot**, and at those temperatures the state-1 pressure line is
worth `0.004` per degree - about **+2.5 PSI/s**, roughly **800 PSI of margin the machine never had**.
It reported `Pmin 3226`; the live shift reached **2804**. Fixed by moving the block into the chain,
which is also where a real player throws those clicks. A wrong harness is worse when it reports a
*better* number, because a worse one gets investigated.

A genuine negative came out of the correction: across 12 noise streams the winner is not fragile
(the floor bottoms at 2475 against the 2200 stall line) but "12/12 reached Report" is **not** the
same claim as "there is plenty of margin", and the file now says so rather than averaging it away.

Also measured, and owed to the same live run: `Engine:Update(dt)` steps at a fixed `Sim.Step`, so
counting calls is not counting seconds; the two endings are byte-identical on shift 1 **by
construction** (`EndShiftHandler:437` sets a `Quota` flag whose only two readers are both gated on
shift 3), which predicts where shift 3 will differ rather than leaving it as "we never saw a
difference"; and `phase=Report` proves the transport delivered, not that the quota was met - the
quota is proved by the fact that `Engine:Command('shutdown')` *refuses* below it, and this one was
accepted. See PROGRESS.md Phase 128, DECISIONS_2 539-543, docs/SNIPPETS.md 5.35.


### Phase 129 - a two-round-old open question, closed: the character does not block the click

**No game code was changed this phase.** The target was `docs/TODO.md` 3.14 (3), open since Phase 124:
"does the character block the click ray" had **no conclusion** - the positive experiment failed twice,
but that failure was already explained by the `ShuttersOpen` gate, and a criterion that can fail for a
reason other than the one under test is not an experiment (CLAUDE 0.26 (1)). It now has a conclusion.

Three arms, one variable. The only thing that moves is the character's `CanQuery`:

| arm | `CanQuery` | body | parts on the eye-to-control segment | delivered |
|---|---|---|---|---|
| `off` | false | on the control | 0 | yes |
| **`on`** | **true** | **on the control** | **4** | **yes** |
| `up` | true | lifted 4 studs | 0 | yes |

`on` is the question; `up` is the control for "the flag did something else". Both deliver, so the flag
has no effect on delivery. All three arms read the **same** root and eye coordinates to two decimals
(the eye search excludes the character, so it is `CanQuery`-independent) - the rig did not move.
The target is `MONITOR POWER BUTTON`, chosen because `Engine:Command` toggles it in a bare branch with
**no phase gate of its own**, so the boot chain, the shutters, the quota and the phase are all out of
the picture before the first click. A fourth piece of evidence that needs neither logs nor rays:
`Stats.MonitorPower` read `true`, the click landed, it read `false`.

**The real find is that the ray I had been measuring is not the ray the click uses.** At one instant,
1 ms apart: the engine's own `Mouse.Target` said `ClickPart in MonitorPowerButton`, while a
`Workspace:Raycast` sent from the *same* `mouse.UnitRay` hit the character's `Handle` at 1.01 studs.
`Workspace:Raycast` does not exclude the clicking player's own character; the ray the engine dispatches
the click with does. `Mouse.TargetFilter` reading `nil` only means "no *extra* exclusion" - the engine's
built-in exclusion of the local character is not visible through that property, and Phase 124 read that
`nil` as "the character is not excluded". Both readings are kept, because *whose* ruler it is, is part
of the conclusion.

**So `docs/SNIPPETS.md` 5.35 (3) - "the character must be `CanQuery = false`" - is wrong**, and it is
wrong for exactly that reason. It has a correction marker rather than a rewrite (a wrong ruler had
written its conclusion into the document the next run would read; the original text was true of what
was measured at the time). `CanQuery = false` is no longer *required*, but still worth keeping, on a
different ground: it removes the character from your own diagnostic casts, so your readings agree with
the engine's.

**Boundary, not to be extrapolated:** the character was muted and anchored throughout
(`Transparency=1 / CanCollide=false / CanTouch=false / Anchored=true`) and only `CanQuery` moved.
"Does a normal, standing, moving character block the click" was **not** measured.

Three side lessons from the same session, each a reading that was not the reading it looked like:
the old aiming rule (cast horizontally at the control's own height, take the first clear direction)
answers "clear at that height", not "clear line of sight" - a recessed switch had all 16 candidates
clear while the actual descending segment was blocked from every one, so the rig would have clicked the
wrong part and recorded a clean, silent, wrong negative, and "the park is aimed" is now the `eyeHits`
readout rather than an assumption; `Destroy()` does not kill `task.spawn`-ed threads (measured as two
sets of lines at the same `t=` in one report), so every loop has to check `script.Parent == nil` itself;
and "it is within 3 studs" is not "it is that part" - a guard criterion against stale pointers returned
a false positive because it asked about proximity instead of identity. See PROGRESS.md Phase 129,
DECISIONS_2 544-548, docs/SNIPPETS.md 5.36.


### Phase 100 - the driver: the half of the channel that presses things

The state recorder (`_tools/TRG_original_state.luau`, tag `s2`) is read-only by construction:
it never writes the world and it never presses anything. Pressing is what `fireclickdetector`
is for, and `fireclickdetector` is an executor-side function - so it needed a second injected
file. `_tools/TRG_original_drive.luau` (tag `d1` when this section was written; it has moved
on several times since - for its current identity read the table in `docs/RECORDER_HOWTO.md`
section 13.9) lives in the same executor VM and is driven
by a **command file**: I write `<seq> <verb> <args>` into `trg_cmd.txt` from Windows, it
executes every sequence number it has not executed before, and appends the outcome to
`trg_drive_log.txt`. The sequence is monotonic and the last one is persisted in
`trg_drive_state.txt`, so a re-injection does not replay old commands; the command file is
deliberately **never truncated**, because it is the durable record of what was asked, and a
lost command would be invisible if it were cleared after reading.

Verbs: `census` / `stats` / `fire` / `fireall` / `near` / `ls` / `pos` / `stop`.
`fireclickdetector(cd)` and `cd.MouseClick:Fire(lp)` are logged **separately**, because the
first goes through the executor and the second only fires the client's listeners while the
game's logic runs on the server - the two look identical in code and can differ in effect.
Every fire teleports the character next to the part first (`fireclickdetector` does not move
the character, so any distance check still sees the real position and a click fired from
across the map is rejected with no error anywhere), and every fire is followed by a
measurement: `fire CHANGED ...` or `fire NOCHANGE ...`, read from `Workspace.Stats` by the
driver itself. `NOCHANGE` is a real result - a negative measurement, not a failure.

It has not pressed anything yet. The executor's MCP worker registered once, delivered 31
tasks between 13:10:32 and 13:29:37, and has since lapsed: `execute-script` is refused with
`No Roblox executor is connected.` while the WebSocket keeps polling (25317 `WS_POLL` lines).
The files, the autoexec stub and the queued commands are all in place, and there is not a
single `trg_drive_*` file in the workspace - the stub has never fired, because nothing has
been injected since. Because on disk "never ran" and "ran and failed" are byte-identical, the
stub writes a marker line before it loads. The next injection starts the driver on its own;
see `docs/RECORDER_HOWTO.md` section 13.9 and `docs/TODO.md` section 3.11.

**Not verified: it has never pressed anything.** Every statement above about *how* it presses
comes from reading its source, not from watching it run.

*Superseded by Phase 106, below: that is the round it pressed the game's own
switches and the reactor came up.*


### Phase 102-103 - the driver ran live, then the session was lost

Phase 102 is the round the driver finally ran inside a live client. The anti-idle went from `d2`
to `d3` by adding one observability field: `antiIdle(force)` became `antiIdle(force, why)` and
the log line grew a `via <verb|timer|idled>` tail. Behaviour did not change by a byte - but the
field paid for itself the same evening, because a hot reload leaves the old module's `Player.Idled`
connection alive in the same VM: at 23:27:39 two lines one second apart were byte-identical except
for that word, and without it they read as "it moved twice in one second" (DECISIONS 410).
Measured auto-gaps are 120.1-150.0 s and all of them are events; the 240 s periodic path is
starved, because every `Idled` resets the timer it is waiting on. That is a backstop that works
by having only one live leg.

Phase 103 is a negative result, and it is written as one. `d4` is the **fourth press route**:
`d3`'s three routes all press a *signal*, and the live `caps` read back `firesignal=nil` and
`getconnections=nil` (while `fireclickdetector` was present), so `press` reported
`no route worked`. But a button is not only a signal - it is also a **rectangle** at a known
screen position, and `VirtualInputManager:SendMouseButtonEvent` can click that. Same family as
the anti-idle's `VirtualUser` path: in-game synthetic input, never the operator's cursor.

`d4` is **staged and never loaded**. It is byte-identical in the repo and in the executor's
workspace, it parses, and it has never run a single line. The session went away before it could
be verified, and all three routes back were measured dead:

- `open-roblox-game` sends a launch URL with an empty `gameinfo:`, so the client redeems a ticket
  that does not exist and gets `403 Forbidden ... Authentication ticket was invalid` (2 of 2
  attempts). The session that did work - launched from the operator's own browser - has **zero**
  `authentication-ticket` lines and joins, then teleports, then arrives.
- `launch-roblox`'s schema is `{workerId, path}`. There is no place parameter, so the daemon has
  no route to an authenticated session.
- A browser deep link opened three `msedge` processes and no `RobloxPlayerBeta` in 90 seconds.

The attach anatomy explains all of it without any new mechanism: Solara's `findMainWindow` runs
**exactly once per process, about a second after the process appears, and never rescans**. The one
client it caught (window handle 67336, attached 79 s later) was already running when Solara
started. Both later clients report `process_window: 0`. **Client first, then Solara.**

See PROGRESS.md Phase 103 and DECISIONS 411 to 415.

### Phase 106 - the boot chain, pressed for real

The driver's fourth press route landed on the game's own switches this round, and the
reactor came up. Four things here were measured rather than assumed.

**What was blocking the click was not the button.** `UnlockUI` is a full-screen
`TextButton` (`1151.2 x 714.4` at `0, -58`) and a `GetGuiObjectsAtPosition` census at
the pixel reported it as the *only* Active object there. Hiding it is not the fix:
with `UnlockUI.Visible = false` the press still counted `MouseClick=0`, and only
`ScreenGui.Enabled = false` turned it into a landing press (`MouseClick=1`). Why
`Visible` alone is not enough has two surviving readings; what *works* has one
(DECISIONS 426).

**A client-counted `ClickDetector.MouseClick` is not an oracle.** The press that did
land on `StartUpBigLever` reported `MouseClick=0` while the server changed two
replicated values; an earlier press that reported `MouseClick=1` changed none,
because it came before `MonitorBoot`. `Workspace.Stats` - 32 `ValueBase`s, under the
`Core` / `Fans` / `CBL1..3` / `HDEF` folders - is the only oracle (DECISIONS 427).

**The chain, in the game's own order**, each step read as a before/after diff of
`Stats`. The master start-up switch's own tooltip - *"Will beep green after proper
control room boot-up"* - is literal, and the step it waits on is `MonitorBoot`:

| step | part | `MouseClick` | `Stats` delta |
|---|---|---|---|
| RoomLight | `ALTReactorConsole...RoomLightButton.ClickPart` | 1 | none (lamps are not in `Stats`) |
| MonitorPower | `ALTReactorConsole...MonitorPowerButton.ClickPart` | 1 | none |
| Shutters | `ALTReactorConsole...ShuttersLever.ClickPart` | 1 | none |
| MonitorBoot | `MainReactorConsole.MonitorBootButton.ClickPart` | 1 | 6 - `CBL1..3.Active false->true`, `CBL1..3.TempVal 140->791` |
| StartUp | `MainReactorConsole.StartUpBigLever.StartClickPart` | 0 | 2 - `Core.BreachVal false->true`, `HDEF.IntegrityVal 12->20` |
| HDEF PowerLever | `HDEFGenerator.PowerLever.ClickPart` | 1 | 5 - `IntegrityVal 20->66`, `OutputVal 0->61`, `PressureVal 20->3126`, `RadiationVal 360->474`, `TemperatureVal 0->4009` |

Three seconds later: temperature 4009 -> 7842 F, pressure 3126 -> 6097 PSI, output
61 -> 120 GW, HDEF integrity -> 88. Temperature and pressure both start at zero and
the output comes off the floor, so this is the reactor lighting and not a readout
moving.

**The sixth step is the destructive one.** It was left running, and `HDEF.IntegrityVal`
climbed 12 -> 20 -> 66 -> 88 -> 99. The operator reported the outcome: *"HDEF Generator
爆炸了（其实是过热，开时间太长就会这样）"*, and then corrected the fix I inferred from it: *"HDEF Generator
过热是必然的，冷却没办法减缓"* - **cooling does not slow it down.** The rule is
only *do not leave that generator running*; the C-Pumps are not its remedy (DECISIONS
429). The operating procedure, with the per-step aim directions and the
collector-hiding preamble, is `docs/TODO.md` section 3.11.10.

**Two readings of "the reactor is on" disagree, and both belong in the report.**
`Stats.GameActive=true`, `Core.OutputVal=144` GW and `TemperatureVal=9420 F`, while
`Stats.GameStart=false`, the quota monitor's `PreStartupFrame` still read
`PENDING REACTOR ACTIVATION`, and the log monitor's headline was `CORE COLLAPSE
DETECTED - PLEASE WAIT WHILE THE REACTOR COMPLETES ITS AUTOMATED SHUTDOWN
INSTRUCTIONS` - which was there *before* any of these presses. Temperature, pressure
and output then sat byte-frozen for 20 s with only radiation creeping (676 -> 715),
which is the shape of a shutdown integrator rather than a live core. The quota clock
went 11:50 PM -> 12:47 AM, so midnight passed and the shift opened.

See PROGRESS.md Phase 106 and DECISIONS 426 to 430.


## Documentation layout

`CLAUDE.md` is the file auto-loaded into an assistant's context every session, so as of
2026-10-10 it carries only what must be seen **every round**: the doc-sync rules (0.0), the
numbered "blood-and-tears" lessons (0 through 0.44), the project overview (1), the
operator's preferences (4), the do-not-touch list (6), the references (7), a one-sentence
summary (8), and the operational "before you act" rules. The per-Phase digest of Phases
47-107 - **1155 lines, 67% of the old 1725-line file** - was moved out to `docs/PHASES.md`.
Section numbers were **not** renumbered, so every `0.13` / `2.6` / `5.9` cross-reference in
`PROGRESS.md`, `DECISIONS*.md` and this file still resolves. The authoritative long form
stays in `PROGRESS.md` and `DECISIONS*.md`; `docs/PHASES.md` is the condensed look-up by
Phase number.

`docs/SRSU.md` (2026-10-11) is the first **device bible** in that layout: the in-universe
setting for the *Subspace Radiation Suppression Unit*. It started as **setting only**, and the
operator built the physical thing the same day - six units named `BottomSuppressionStructure`
in `Workspace.Folder.Chamber` (rebuild place), so the file's geometry now quotes **measured**
values (section 4.5) rather than the design draft. **The code side is still zero**: nothing of
it is in `ReactorBackend`, `Stats` or `ControlTrigger`, and `script_grep` finds no reference to
the name anywhere in the place. It is registered in the `CLAUDE.md` 0.0 table so it gets read
before anyone writes that device's copy, art spec or numbers. Wiring it into the simulation is
the one open piece of `QUESTIONS.md` **S1**.

