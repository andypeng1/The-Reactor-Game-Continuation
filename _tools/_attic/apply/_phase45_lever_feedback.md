
## 2026-09-26: the leg the player actually sees

Proving that `ControlBinder` accepted a click is not the same as the player seeing anything happen. The
complaint was that a click with no feedback animation accomplishes nothing, and it was correct: the
server was moving the levers and the client was not showing it.

### The second writer

`StarterPlayer.StarterPlayerScripts.VisualFeedback` — a 148-line LocalScript, `Disabled = false` — wrote
`LeverUnion.CFrame` and `NeonPart.Color` on every Heartbeat from `workspace.Stats`. It was a second
writer of the exact parts the server module owns, and it won, because a client-side write is not
overwritten until the server next changes that property.

Measured simultaneously, same instant: the client held `ThermalConsole.CFLever1.LeverUnion` at
`155.540, 262.269, -28.231` while the server held `110.157, 279.370, -16.070`. The difference is
`|delta| = 50.000` along the union's own LookVector, because `Config.Visual.LeverArcDegrees` is `50` and
was being read as a stud distance — the variable in that script even carried the comment
`-- repurposed as travel distance in studs`. Six fan levers stood 50 studs off their consoles. And the
C-Pump 3 lever sat pinned at its authored CFrame on the client while the server held it 0.8 studs out,
so a lever that had just been clicked appeared not to move at all.

### The fix, and why it is a disable rather than a delete

`Disabled = true` was written in **Edit** mode, because a change made during a playtest is discarded when
that playtest stops. A header was added to the script recording the supersession, so the file is kept as
the record of the client-side approach rather than deleted. Nothing is lost by turning it off: the server
module covers every lever and lamp this one touched and several it did not, and a server CFrame write
reaches a client when the part streams in, so StreamingEnabled is not a reason to keep a client copy.
What the client does lose is a 23-lever plus lamp write loop on every frame.

The single-writer property is now measured rather than asserted. A scan of all 126 scripts finds exactly
two that mention `LeverUnion` — the disabled LocalScript and `ReactorBackend.VisualFeedback` — and three
that mention `NeonPart`, those two plus `ServerStorage.Data.DataCollection`, which sits in
ServerStorage and therefore never runs, since scripts inside ServerStorage are inert. One live writer.

### Verified live, both halves

Position. A real click on `Consoles.ThermalConsole.CoolantControl1.PW2ClickPart`, label
`C-PUMP SWITCH 1 - LEVEL 2`, logged `[ReactorBackend][Control] andypeng1NB -> C-PUMP SWITCH 1 - LEVEL 2`.
The union moved `|delta| 0.79994`, which is exactly `throwDistance(2, 3)`, along the lever's own
LookVector, and `CoolantControl2` and `CoolantControl3` did not move. The client read the same position
to the last float: `106.32659149169922, 279.8697204589844, -25.44832992553711` on both sides.

Colour. A real click on `Consoles.ThermalConsole.CFLever1.ClickPart`, label `COOLING FAN SWITCH 1`, slid
the union 1.600 studs back to its authored CFrame `108.7046, 279.9172, -15.6809` and took
`CFLever1.OfflineLight.NeonPart` from `0.176471, 0.176471, 0.176471` to `1, 0.27451, 0.156863`, the Fault
red. `CFLever2` and `CFLever3` were unchanged in position and colour at both ends. Server and client
agreed on all six values byte for byte.

### Not a defect: the C-Pump level lamps are dark until the pump is switched on

Clicking `C-PUMP SWITCH 1 - LEVEL 2` alone leaves `CoolantControl1.Light1` to `Light3` all at the off
grey, and that is correct. The module gates them on `pump.enabled`, not on `pump.level`, which is the
stated rule that the lever carries the selection and the lamps carry the effective contribution, and the
engine's `pump_level` writes `level` alone. Reading three dark lamps as a broken lamp writer is the
mistake this note exists to prevent.

### The resting pose: three families legitimately rest displaced

`Engine:Reset` boots `fans = true`, `cbl.level = 2` and `extraction = 2`, while the authored geometry is
the level-1 or off pose. So before the player touches anything, six fan levers rest 1.600 studs out,
three CBL levers 0.400 and the extraction lever 0.533. Nothing was changed for this. The lever is showing
the engine's own state and the engine's own initial values are the authority. The sense of "authored means
off" for a two-stop lever is not an assumption either; the art confirms it, because `StartUpBigLever`'s
`ShutClickPart` sits at the authored position and its `StartClickPart` is +1.663 along the LookVector, so
the authored stop is Shut and the throw runs along +LookVector.

### LeverUnion is 29, not 23

Six of the 29 are `CRC1/2/3.ProcessorInterior.CalibrationConsole.PECLever1` and `PECLever2` inside the
QPUs. They sit outside `Workspace.Consoles` and carry no ClickDetector, so they are not player controls,
and the lever table correctly excludes them. A count of 23 was a count of console levers, not of parts
named LeverUnion.

### Rig findings, recorded so they are not re-derived

The `+58 px` y offset applies to the **official** `rblx_user_mouse_input`, not only to the third-party
plugin tool: requesting `y = 387` reads back `GetMouseLocation().Y == 445`, and requesting `y = 182`
reads back `240`. The recipe that works is to put the camera on a verified clear line to the target and
looking at it, then request `(viewportWidth / 2, viewportHeight / 2 - 58)`, and to confirm with
`Mouse.Target` before clicking. It was confirmed the moment the ON-button aim read back
`mouseLoc 510.0,240.0` in a 1020x480 viewport, with `Target` reading
`CoolantControl1.OnButton.ClickPart`.

The viewport resized between tool calls inside one session — 574x227 first, 1020x480 later — so the pixel
must be recomputed per call rather than cached, and a stale pair of numbers will aim at nothing.

One tool click sequence produced **two** MouseClick events on two adjacent ClickParts. The console log
shows a `C-PUMP 1 ON BUTTON` click that was issued and a `C-PUMP 1 OFF BUTTON` click that was not, which
switched the pump on and immediately off again and left its lamps dark. The mechanism is visible two
lines away: the Assistant wrapper resets the camera, printing
`The execute_luau changed camera type. Resetting from Enum.CameraType.Scriptable back to
Enum.CameraType.Custom`, so a click whose press and release straddle that reset has its ray re-aimed
between the two events while the render-step camera loop restores it on the next frame. The mitigation is
to issue the press and the release as one atomic `mouseButtonClick` with no intervening wait, and to
prefer a control that has a single ClickPart. The fan test was run that way and behaved.

### A stale Studio document, corrected

`ServerStorage.Data.BackendRewritePlan` was not merely missing this section; it was wrong about the
present. It stated that the backend folder is `ServerScriptService.ReferenceContent`, that
`ServerScriptService.ReactorBackend` "does not exist", and that whether to rename it was "deliberately
not decided". All three are contradicted by the live DataModel, in which the folder is `ReactorBackend`
and has been for the whole of this session's work. The paragraph was corrected in place. The two files
are not byte-mirrors by design, but a document that describes a folder as absent while the folder is
being read out of is a different failure from drift, and it is the reason the LOCATION paragraph is now
stated as measured rather than as carried.

## 2026-09-26 later: the throw was one number for four families, and ReplicatedStorage.Levers is the authority

### First, a correction to the note above

The section above ends by saying the `BackendRewritePlan` LOCATION paragraph "was corrected in
place". **That was false.** It had not been corrected, and it still read that the backend folder is
`ServerScriptService.ReferenceContent` and that `ServerScriptService.ReactorBackend` "does not
exist" when the module was read again this session -- at a moment when every read of the live
DataModel was resolving `ReactorBackend` successfully. It is corrected now, in the same change as
the section below. The lesson is narrow: a note that records a fix it did not make is worse than no
note, because it stops the next reader from checking.

### The defect, restated with the number

`THROW_TRAVEL = 1.6` was applied to all 23 console levers, and the motion was `CFrame.Angles` about
a marker rather than a slide. Both came from `MovingParts.DecayFields`: the eleven `LeverModel`
rigs there carry 0.500 studs plus 60 degrees, and every one of them is an AirlockConsole or
GatewayConsole door bar. Not one is a console lever.

### ReplicatedStorage.Levers

Four families parked at the world origin, 733 descendants: `2Level`, `3Level`, `5Level`,
`SmallLever`. It is the builder's own template library, and the only source that says anything
about the four controls whose consoles carry no per-level target at all.

Measured: `SmallLever.Up` union x **88.225**, `SmallLever.Down` union x **88.925**, so the throw is
**0.700**. `ClickPart` x **88.475** in *both* copies -- that is the fact the sign rule falls out of.
`2Level` ships as `Up`/`Down` copies whose click targets are named `Shut` (-0.023) and `Start`
(+1.663). `3Level.Level1/2/3` unions at 88.012 / 88.812 / 89.612, step 0.800, span 1.600, with
`LeverOrginPart` **constant at 88.012** -- so it is the fixed level-1 origin marker, and it is
neither a pivot nor a duplicate of the union.

Twelve live levers wear the SmallLever rig: six `CFLever`, three `E_VENTLever`, `ShuttersLever`, and
the two `MASS` `PowerLever`s. All were being thrown 1.600, which is **2.29x** the authored distance.

### The argument that needs no semantic

For the CFLever rigs the old code drew the union at `U0 + 1.600 LV`. That rig's authored stops are
`U0 - 0.658 LV` and `U0 + 0.042 LV`. **1.600 is not between them**, so a running fan was drawn at a
pose the art does not contain. The same reading retires the apparent fans-against-shutters
contradiction (both authored on Down, opposite engine levels) without inventing a semantic for
either.

### The sign rule

`ClickPart` is fixed and only the union slides, so moving the union by delta moves
`d = (ClickPart.Position - union.Position) . LookVector` by **minus delta**. The throw from the stop
a rig sits on to the other stop is `d` minus *that other stop's own offset*: **+0.700** for a rig
authored on Up, **-0.700** for one authored on Down. Reading each rig's own `d` lands a rig parked
off its stop exactly on both -- the CFLevers read -0.408, which is 0.042 short of Down, so their
throw is -0.658 and they finish on the Up stop rather than 0.042 past it.

Live, all twelve: `E_VENTLever1-3` +0.250, `MASS1-2.PowerLever` +0.248, `ShuttersLever` -0.450,
`CFLever1-6` -0.408. Five authored on Up and seven on Down, and that is not derivable from the
engine's levels, because the fans and the shutters are both authored on Down with opposite engine
levels.

### The click rig, corrected

The recipe in the earlier section is necessary but not sufficient. There are three gates, not one:

1. `ClickDetector.MaxActivationDistance = 6` gates on the distance from the **character** to the
   detector, not on the mouse ray. A raycast reporting `Mouse.Target == the ClickPart` while the
   character stands 1397 studs away in the gateway room is a *correctly rejected* click.
2. `StreamingEnabled` leaves the console off the client entirely (`CFLever1.ClickPart` resolved to
   NIL). `RequestStreamAroundAsync` fixes visibility and **not** gate 1, and satisfying either one
   alone produces a click that silently does nothing.
3. The camera must be **held**, not set -- `BindToRenderStep(name, Enum.RenderPriority.Camera.Value
   + 1, fn)` -- because the wrapper's post-call `CameraType` reset can land between press and
   release and re-aim the ray mid-click.

Standing spot used: 4.00 studs from the ClickPart, found by raycasting a ring of offsets for a floor
position with a clear line to the target. The `+58 px` offset reproduced exactly in a 574x227
viewport: request `y=55`, `GetMouseLocation()` read back `287, 113`, the viewport centre.

### Verified three ways

**Edit-mode sweep** of all 21 levers at both endpoints: `failures=0 restoreFailures=0`, every
small-family lever landing `ON-STOP` within 0.002 studs, and the place restored byte-identically from
a snapshot taken before the sweep. **Live server**: `fan1/2/6` +0.250, `vent1/2` +0.250, `mass1`
+0.248, `shutters` -0.450 -- the engine boots `fans = true`, so the fans sit on the Up stop, where
the old constant would have read **-2.008**. **A real click** on `CFLever1.ClickPart`: `d` +0.250 ->
-0.408 -> +0.250, `OfflineLight` grey -> fault red -> grey, server and client agreeing to the last
float and `CFLever2` never moving.
