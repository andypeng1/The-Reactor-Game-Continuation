# AIRemake backend rewrite — working log

> Target place: `83752844701736`, "The Reactor : AIRemake".
>
> **This file does NOT byte-mirror the Studio module, and the previous version of this
> header claimed it did.** Measured 2026-09-26 with `_tools/mirror_check.py`, *before* that
> day's sections were added: the module normalised to **3921 bytes / 65 lines**, this file
> was **8494 bytes / 185 lines**. The module now measures **47040 bytes / 617 lines**, with
> normalised checksum **47040|172228|275675** — re-measured 2026-09-26 after that day's lamp
> section was added to it, a section it had carried twice was removed, and the probe's
> `Disabled` state was recorded in it; it stood at **49723 bytes / 656 lines**, checksum
> **49723|394787|199637**, before those three edits. That
> figure is the one number this header can
> hold still, because editing this file does not move it, whereas this file's own size changes
> with every sentence added here. This file has grown past the 8494 figure quoted above, and
> its current size is deliberately **not**
> restated — a document cannot report its own length correctly inside itself, because every
> correction to that sentence changes it, and chasing the number is how the previous version
> of this header ended up asserting a mirror that did not exist. Measure it instead:
> `python _tools/mirror_check.py docs/airemake/REWRITE_STATUS.md`. They are the same status
> at two depths: the module is a terse in-Studio summary, this file is the long form carrying
> the measurement appendices. Neither is a copy of the other.
>
> That was a real, if harmless, false statement: nothing reads a documentation module at
> runtime, so nothing failed and no test could have caught it. It is corrected here rather
> than fixed by pushing these 185 lines into the module, because re-typing measured content
> by hand is how a measurement stops being one — the rule `_tools/fill_video2_json.py`
> already applies to the user's own JSON. **Both are updated together; neither is
> authoritative over the other, the place is.** Whether to converge them into one is an
> open decision for the user.

## September 26, 2026 — the skeleton is live and verified end to end

### Location, and a name that was wrong twice

The backend is `ServerScriptService.ReactorBackend` — renamed from `ReferenceContent` on
2026-09-26, see the decisions section at the end of this file — 6 children:

| Child | Class | Bytes |
|---|---|---|
| `Config` | ModuleScript | 3558 |
| `Engine` | ModuleScript | 14930 |
| `StateBridge` | ModuleScript | 1835 |
| `ControlBinder` | ModuleScript | 5792 |
| `Runtime` | Script | 2375 |
| `VisualFeedback` | ModuleScript | 14397 |

Total 42887 bytes across the six. **These two rows were wrong until 2026-09-26**
(`Runtime` read 1633, `VisualFeedback` read 4912) — another figure written without
being measured, in a file whose own header now warns about exactly that. Measured by
summing `#Source` over `ReactorBackend:GetDescendants()`.

Earlier notes named `ServerScriptService.ReactorBackend` and this file called that
wrong, because the folder was then named `ReferenceContent`. The rename was decided
on 2026-09-26, so the notes turned out to have been right about the destination and
only early about the date. Before renaming, a grep across all scripts for the old
name found it in exactly one place, and that place was documentation rather than
code, so nothing resolves the backend by path; `Runtime` uses `script.Parent`
throughout and its own log tag has said `[ReactorBackend]` from the start. Verified
after the rename: 6 children, no stale name, `Runtime.Disabled` false.

### Why it looked completely dead

`Runtime.Disabled` was `true`. Every other part of the backend was correct and
inert behind that one flag. Setting it to `false` **in Edit mode** boots the whole
skeleton. Editing it during a playtest does not survive stopping that playtest, so
the Edit-mode write is the one that counts.

### Verified end to end by real clicks, not by reading module state

Four controls were driven through the entire chain — virtual mouse → `ClickDetector`
→ range gate → cooldown gate → `engine:Command` → engine state machine — with the
server's own log as the proof:

```text
[ReactorBackend][Control] andypeng1NB -> MONITOR POWER BUTTON
[ReactorBackend][Control] andypeng1NB -> CONTROL ROOM SHUTTERS SWITCH
[ReactorBackend][Control] andypeng1NB -> MONITOR BOOT BUTTON
[ReactorBackend][Control] andypeng1NB -> MASTER START-UP SWITCH
```

The startup dependency chain was discovered **by execution, not by reading code**:

```text
monitor_power  ->  shutters  ->  boot  ->  start
```

The engine refusals observed while discovering it are correct behaviour, not bugs:

```text
MASTER START-UP SWITCH rejected: Complete control room boot first
MONITOR BOOT BUTTON rejected: Power monitors and open shutters first
```

After `start`, the phase went `Cold → Booting → Ready → Starting → Running`, and the
live readings then moved on their own:

| Field | Before start | After, running |
|---|---|---|
| `Core.TemperatureVal` | 20 | **13885** |
| `Core.PressureVal` | 20 | **2846** |
| `Core.OutputVal` | 0 | **93** |
| `Core.RadiationVal` | 0 | **240** |
| `HDEF.IntegrityVal` | 12 | **11** (decaying) |

The simulation loop runs; it is not merely installed.

### Adjudication order for conflicting constants

From the user's standing rule that TRGWeb is reference material only and must not
be copied wholesale:

```text
live place (DataCollection + workspace instance names)
      >   video   (narration over on-screen text; video 1 over video 2)
      >   TRGWeb  (old HTML prototype)
```

Confirmed live in `Config`: `State1 = 5600` and `StallPressure = 2200`, **not** the
stale TRGWeb values `6000` / `2250`.

## Still open — recorded, not guessed

**The state 3 upper bound is a four-way disagreement.** `DataCollection` 39000,
TRGWeb 39000, video 1 39000, video 2's in-game documentation screen **35000**.
18000/30000 are explicable as roundings of 17500/29500, but 35000 bears no rounding
relationship to 39000. `DataCollection` also contradicts itself: `MELTDOWN_TEMP_F =
38000` against `CORE_STATE_THRESHOLDS` ending at 39000.

**Running the skeleton cannot settle this.** Its own `Sim.MeltdownTemperature` is
authored in this project, so watching it melt at 39000 would only confirm our own
choice — a circular measurement. It needs an external source.

## Missing scaffolding — found September 26, 2026

Three artifacts the disk docs describe **do not exist in the place**. All three were
checked by direct lookup, not by reading a large dump by eye:

| Described in docs | Reality |
|---|---|
| `ServerStorage.BackendBaseline20260925` | **absent** — no such name anywhere in the DataModel |
| `Workspace.ConsoleDesignStaging.MainReactorConsole_NewDesign` | **absent** |
| `ServerScriptService.ReactorBackend` | **now correct** — the folder was renamed to this on 2026-09-26 |

What *does* exist: `Workspace.Geometry` still holds its **23** decorative parts, and
`Workspace._BackendOrganization` holds three folders — `Bindings`, `LegacyAudit`,
`MigrationMarkers` — **all three empty**. The move happened; the ledgers never did.

So the 23 moved parts have no record of their former parents. Nothing was deleted and
no geometry changed — what was lost is only the ability to restore their placement.
There is no Open Cloud key and no local `.rbxl`, so revision recovery is unavailable.

**Partial recovery is still possible without inventing anything:** the move preserved
every CFrame, so each of the 23 parts still sits at its original world position and its
former parent can be derived from the surrounding geometry. **Not done yet.**

## Next

1. Finish the shift lifecycle end to end. The gates are now **documented rather than
   guessed**: shutdown needs the quota filled **and** the reactor "in State 1 or below"
   (manual #114), i.e. `temperature < Shift.ShutdownLimit = 17000` while `State2 = 17500`
   — so there is a deliberate 500-degree sliver where the core is in state 1 and still
   will not shut down, which manual #84 calls "in the margins of this state". Run → cool
   below 17000 F → meet quota → shutdown → report.
2. **Done 2026-09-26.** ~~Wire the visual adapters.~~ The claim that `VisualFeedback`
   "reports `captured 0 lever baselines, 0 lamp baselines` because it addresses levers by
   the wrong path" was **wrong on both counts** — the count was printed with `#` on a table
   keyed by Instances (always 0), and 21 levers were being captured correctly the whole
   time via the address table below. `Initialize` now counts with `pairs()`. Outstanding
   inside this item: the five lamp families in the module's `DELIBERATELY NOT WIRED` block,
   `OverchargeLever.BigLever` (its fraction is unknown), and `cbl.active` (no visual home).
3. Decide the folder name question, or record it as intentionally unsettled.
4. **New, from the manual.** The live place documents mechanics the skeleton does not
   model, each of which needs a user decision rather than an edit, because `CLAUDE.md`
   §1.4.1 forbids changing mechanics unilaterally: a stallout **warning** band near
   5600–6000 F (today the core goes from healthy straight to `Fail`); coolant-sensor
   unreliability; an ×2 EFE distinct from Equinox; the CBL five-colour status code
   (Overload Red / Integrity Loss Purple / Reaction Loss Blue / High Output Yellow — four
   of which have no palette entry); shift gating (`[SHIFT 2+]` / `[SHIFT 3+]`); and a
   **yellow** rapid flash for grav-overload-ready against a green `Visual.Pulse`.
5. Re-measure the `MONITOR BOOT BUTTON` lever attribution. It is carried over from the
   earlier session rather than measured in this one.

## Appendix — measured lever contract (server-side, 2026-09-26)

29 `LeverUnion` parts exist. **Every one** is `Anchored = true` with no joints, so
direct CFrame assignment is the correct drive mechanism. 28 of 29 carry a `Sound`
child that `VisualFeedback` ignores.

**The levers do NOT share one LookVector.** There are six distinct vectors, so any
hardcoded single rotation axis is necessarily wrong:

| LookVector | Count | Members |
|---|---|---|
| `(0.94,-0.34,0.00)` | 5 | `StartUpBigLever`, `E_VENTLever1..3`, `MainReactorConsole.Model` |
| `(0.93,-0.34,0.12)` | 3 | `ShuttersLever`, `MASS1/2Systems.PowerLever` |
| `(0.93,-0.34,-0.12)` | 2 | `ExtractionLever.BigLever`, `OverchargeLever.BigLever` |
| `(0.91,-0.34,-0.24)` | 12 | `CBL1..3Systems.LargeLever.BigLever`, `CFLever1..6`, `CoolantControl1..3.BigLever` |
| `(-0.94,-0.34,0.00)` | 6 | `CRC1..3.ProcessorInterior.CalibrationConsole.PECLever1/2` |
| `(0,-1,0)` | 1 | `HDEFGenerator.PowerLever.BigLever` |

Two further notes. `MainReactorConsole.Model`'s `LeverUnion` is an outlier: no `Sound`
child, and its parent is not a named lever. And the CBL levers live under
`CBLaserConsole`, **not** `ThermalConsole` — which is why `VisualFeedback` marks them
"TBD — not in ThermalConsole".

### Correction to an earlier count

An earlier **client-side** count reported 9 of 29 sharing `(0.91,-0.34,-0.24)`; the
server-side count is 12. The difference is almost certainly `StreamingEnabled = true`
— the client had only streamed part of the scene.

**Rule: with `StreamingEnabled` on, count on the server, never on the client.**

## Appendix — tooling trap: a doc module's `Source` carries a wrapper

While rewriting `ServerStorage.Data.BackendRewritePlan` on 2026-09-26 the prose was
assigned straight to `.Source`, which **stripped its `return [==[ ... ]==]` wrapper**.
The module became prose with no `return` statement — invalid Lua. It was caught only
because the write was verified afterwards with `loadstring`, which is the same reason
the older `NIGHT_LOG` rule exists for `GameCore` docs: *never do character surgery on a
documentation ModuleScript; rewrite it whole, and preserve the wrapper.*

The fix and its check:

```lua
plan.Source = "return [==[" .. prose .. "]==]\n"
local ok, res = pcall(function() return loadstring(plan.Source)() end)
-- ok must be true, and #res must equal #prose exactly
```

**Why it is dangerous: nothing requires a documentation ModuleScript.** No test fails,
no script errors, and the file is not read at runtime — it just becomes unreadable at
the moment someone finally does read it. Documentation has no test coverage, so only an
explicit check catches this.

Related note: Lua's long bracket swallows the newline immediately after the opening
`[==[`, so `"return [==[\n" .. body` yields a body with **no** leading newline. Do not
compute offsets from memory; build the string and assert the round-tripped length.

---

## September 26, 2026 (later) — the place ships its own manual, and one defect fixed

### The highest-authority source was inside the place all along

`Workspace.Consoles` carries a documentation screen on **every** console
(`*.DRMScreen.SurfaceGui.*`): **151 unique strings of in-game operator's manual**, written
by the game's own authors. It sits at the top of the adjudication order above, because it is
the place speaking about itself rather than a video or the old HTML prototype.

Extracted verbatim to [`INGAME_MANUAL.md`](INGAME_MANUAL.md), with a constant-by-constant
reconciliation against `Config`. It was found by accident, while enumerating ClickDetectors
to plan a control sweep — the first query swept the documentation screen's TextLabels and
returned 56 KB. The accident was worth more than the sweep was.

**The four-way state-3 disagreement is closed, and no code change was needed.** The manual
says "State 3 occurs when the reactor temperature is in excess of roughly **29000F**", and
the label is literally `STATE 3 [OPERATIONAL LIMIT]`. `Engine:232` puts the boundary at
`Sim.State3 = 29500`, which agrees. The earlier "39000 from three sources" reading came from
treating the **last element of `CORE_STATE_THRESHOLDS` as the 2→3 edge** — in a four-entry
table it is the 3→4 edge. The skeleton had it right; the disagreement was in how the table
was being read, not in the number.

**`hdef.fault` stops being inferred.** "NOTICE: ACTIVATE THE HDEF GENERATOR ... BE ADVISED
THAT DURING REACTOR OPERATION, THE HDEF GENERATOR CAN OVERHEAT. PERIODICALLY SHUT IT OFF TO
PREVENT OVERLOAD." That names the fault's cause, and matches `HDEFHeatGain = 1` /
`HDEFHeatLoss = 2`: heat accrues while enabled and bleeds off while disabled, which is
exactly the duty cycle the manual instructs the operator to perform. The manual also
confirms, exactly:

| Manual | `Config` |
|---|---|
| "shut down provided the temperature is less than **17000F**" | `Shift.ShutdownLimit = 17000` |
| E-VENTs cool "by **~7000F**" | `Vent.EmergencyDrop = 7000` |
| Equinox "if the Subspace Core has been active for roughly **12 hours [minutes]**" | `Events.EquinoxSeconds = 720` |

And it confirms the Wiki's coolant-sensor claim from the best available source — "coolant
sensory equipment has a tendency to be unreliable during reactor opration" — which the
skeleton does **not** model.

### A real defect: three faults reported on a healthy generator

`VisualFeedback` coloured the HDEF lamps with
`mode = (state.hdef.enabled and not state.hdef.fault) and "ready" or "fault"`. Since `fault`
starts `false` and `enabled` starts `false`, a **switched-off HDEF rendered three red
lamps** — the engine's own default state displayed as three faults — and `state.hdef.fault`
had no visual consequence of its own.

Fixed to the convention the pump block already uses: `enabled` decides whether a lamp is lit
at all; `fault` only chooses the colour of a lamp that is already lit. Verified two ways — a
live click (`Cold` → Off; after `HDEF GEN ACTIVATION SWITCH` → Ready ×3, exactly one lever
moved, delta 0.5000) and a synthetic matrix:

| enabled | integrity | fault | lamps 1..3 |
|---|---|---|---|
| false | 12 | false | Off, Off, Off — **was Fault ×3** |
| true | 12 | false | Ready ×3 |
| true | 12 | true | Fault ×3 |
| true | 5 | false | Ready, Ready, Off |
| true | 0 | true | Off, Off, Off |
| false | 0 | true | Off, Off, Off |

The *split* remains a chosen convention, not a measured one, and is flagged as such. What
the manual upgrades is the fault's **trigger**, previously unobserved.

### The control chain, with only what was actually measured

Each row is a real virtual-mouse click through `ClickDetector` → range gate → cooldown gate
→ `engine:Command` → state machine, with the server log as proof:

| Control | part that moved | measured delta (studs) |
|---|---|---|
| `CONTROL ROOM SHUTTERS SWITCH` | `ShuttersLever.LeverUnion` | 0.5000 |
| `PW3` (CBL power level 3 of 5) | `CoolantControl2.BigLever.LeverUnion` | 0.3333 |
| `HDEF GEN ACTIVATION SWITCH` | `HDEFGenerator.PowerLever.BigLever.LeverUnion` | 0.5000 |

`0.3333` is the detent semantic working: `PUMP_MAX_LEVEL = 3` divides one `THROW_OFFSET`
(0.5000 studs) into `0.5000 × 2/3`. **The lever is a selector; the lamps report effective
contribution** — power level moves the lever, enable/disable does not, and `Light1..3` all
read `0.921569` (Ready). `0.5000` is a full throw.

### Corrections and measurements from this session

- **`StartUpBigLever` carries two ClickParts, named `StartClickPart` and `ShutClickPart`.**
  A filter on `Name == "ClickPart"` finds neither, which is why the master start-up switch
  appeared to have no detector at all. Enumerate `ClickDetector` instances instead. This
  reconciles the September-25 checkpoint's "8 ClickDetectors" for `MainReactorConsole`.
- **`workspace._VisualAudit` does not exist in the Edit-mode place.** The pending cleanup
  item is resolved with no action — it was a Play-mode artefact and is gone.
- **The official mouse tool's y offset re-confirmed at viewport 574×227: exactly +58, x
  exact.** Requested `y = 55.5` → `GetMouseLocation()` returned `113.5`. `Mouse.X/Y` reports
  the *requested* value and `GetMouseLocation()` the corrected one; the mapping is
  **request y = part_pixel_y − 58**.
- **Never choose a stand position by "most open direction".** Taking the max clearance of
  four ray directions selected `RightVector = (0.34, 0.94, 0.04)` — 19.30 studs of open sky
  — and left the player 5.73 studs *above* the button with 3 of 4 sibling controls out of
  range. Constrain candidates to **horizontal projections only** and stand at the
  **midpoint of the needed targets**; all four then fell in range (3.62–4.55).
- **`#` on a table keyed by Instances is always 0** — recurred in a probe of my own, making
  a 23-entry snapshot read as "0 entries" and briefly look like a failed verification. Count
  with `pairs()`. The trap was already documented in `VisualFeedback`'s own comment; it is
  here now too, because it has now cost two sessions.
- **Fixture geometry, measured:** `ALTReactorConsole.ControlRoomSystems`' members are within
  2.316 studs of one another, so one stand point covers all four;
  `MainReactorConsole`'s `MonitorBootButton` and `StartUpBigLever.StartClickPart` are 0.994
  studs apart.
- **The doc-mirror claim was false** — see the header. Measured with
  `_tools/mirror_check.py`, not read.

### What this session did *not* verify

The CBL, extraction, MASS and E-VENT lever families are still not click-tested. Their
*addresses* are proven (`Initialize` resolved all 21 without a gap, and an Edit-mode dry run
measured CBL 0.4000/24.00°, MASS 0.5000/30.00°, extraction 0.5000/30.00° with
`RESTORED_EXACTLY=true`), and the click *plumbing* is proven three times over above — but the
**label→action mapping in `ControlBinder`** for those families is not yet validated, and a
wrong mapping would be silent, not loud. That is the sweep this session set out to do and did
not finish.

**Superseded later the same day — see the section below.** The mapping is now proven for all
62 controls; what remains unexercised is the *clicking*, not the mapping.

## September 26, 2026 (later still) — the label-to-action map, 62 of 62

`ControlBinder` keeps no lookup table. `commandFrom` (lines 16–44) is a single ordered
`if/elseif` chain over the upper-cased label, so **the order is the contract** — the first
matching branch wins, and a label can be claimed by an earlier, broader test.

The audit ran the module's **own** function rather than a copy of it: load
`ControlBinder.Source` with the trailing `return ControlBinder` swapped for
`return commandFrom`, then feed it every label found under `Workspace.Consoles`. A retyped
copy would have proved something about the retyping, not about the module.

**62 ClickDetectors, 62 matched, 0 unmatched.** Exhaustive, not a sample.

| action | indices | count |
|---|---|---|
| `cbl` | levels 1–5 × 3 pumps | 15 |
| `pump_level` | levels 1–3 × 3 pumps | 9 |
| `cbl_purge` | 1–3 | 3 |
| `pump_on` / `pump_off` | 1–3 each | 6 |
| `fan` | 1–6 | 6 |
| `extraction` | 1–4 | 4 |
| `emergency_vent` | 1–3 | 3 |
| `mass_toggle` / `mass_level` | 1–2 each | 4 |
| single | `atmosphere_vent` `hdef` `start` `shutdown` `boot` `monitor_power` `shutters` `mute` `lights` `sam` `grav_charge` `grav_fire` | 12 |

15+9+3+6+6+4+3+4+12 = 62, matching the detector count exactly. Note `start`/`shutdown` are
each a single match — the two `ClickPart`s on `StartUpBigLever` are separated by their
**label text**, not by their part name, which is why the label is the contract.

### One reading of the code that is *not* a defect — recorded so it is not re-flagged

`C-PUMP` is tested with `string.find(u,'C-PUMP')`. In a Lua pattern the hyphen is a **lazy
quantifier**, not a literal, so that call matches `CPUMP` and can never match a label
containing a real hyphen. It is harmless **only** because the authored pump labels contain
none. `E%-VENT` immediately below escapes its hyphen and therefore does match literal hyphens,
so the two families are authored with different conventions. If a pump label is ever
re-authored with a hyphen its clicks stop being counted, and the symptom is **silence, not an
error**. This was flagged as a probable bug on reading the code; measurement is what settled
it, in the opposite direction.

## September 26, 2026 (latest) — the shift lifecycle closed at `Report`, and the 2227 tombstone

**The standing NEXT item is done.** A shift was driven `Running → Stopping → Report` by real
virtual-mouse clicks with the quota met. `Report` is the engine's success terminal (`Engine` line
176 sets `phase='Report'`, `output=0`), and the published flags agreed with it:
`NextShift=true`, `ResetShift=true`, `GameFail=false`, `OutputVal=0`, `EnergyVal=512` of
`QuotaVal=512`, `GameActive=false`, `ActiveQPUs=6`.

Twelve clicks this run, **all accepted**. Acceptance is read from `ControlBinder`'s own log,
which prints `-> <LABEL>` for every click that reaches it *including rejected ones* and appends
`rejected: <reason>` to those — so acceptance is the arrow line with no rejection after it, and
**no line at all means the click missed the detector entirely**: `MONITOR POWER BUTTON`,
`CONTROL ROOM SHUTTERS SWITCH`, `MONITOR BOOT BUTTON`, `C-PUMP 1/2/3 ON BUTTON`,
`COOLING FAN SWITCH 4/5/6`, `MASTER START-UP SWITCH`, `CBL-1/2/3 PRESSURE PURGE BUTTON`,
`MASTER SHUTDOWN SWITCH`.

### The values that did not fit, and why they fit after all

At `Report`, `Stats.Core` read `TemperatureVal=2227` and `PressureVal=16229` — but temperature had
been 13823 immediately before the `SHUTDOWN` click, and `Engine:Step` returns at line 184 unless
`phase=='Running'`, so nothing should have written it. Two probes made it look like a rogue
second writer:

- writing `TemperatureVal=9999` **reverted to 2227 within 3 s**;
- yet a `GetPropertyChangedSignal` watcher fired **0 times** over 2.5 s, and `debug.traceback`
  inside the handler returns an **empty stack**, so the writer could not be named that way.

Both symptoms are explained **without** a second writer:

- `StateBridge` is the only live publisher and it is faithful — writes of `EnergyVal=3`,
  `HDEFVal=7`, `OutputVal=111`, `QuotaVal=1` each came back as the engine's own `512, 0, 0, 512`.
  So `state.temperature` really is 2227.
- There is **exactly 1 instance named `TemperatureVal`** in the whole DataModel, so no
  swapped-in duplicate was being read.
- The engine's write set was then **enumerated by execution, not by reading**: a private
  `Engine` instance was replayed through the same command sequence with its state table wrapped
  in a proxy whose `__newindex` logs every write to `temperature` with a `debug.traceback`.
  Over a full 400-step shift the engine writes temperature on **exactly two lines — 224 (the
  integration) and 230 (the clamp, which writes a no-op every other step)** — and the shutdown
  window produced **0 writes**, leaving temperature at 14077 both before and after shutdown.

**The cause is the CBL overload clock.** `Engine:Reset` line 40 boots each CBL at **`level=2`**,
not 1. At level 2, line 217 charges `device.pressure` at `(level−1)*CBLPressurePerLevel = +0.6/s`,
crossing `CBLStressThreshold 75` at **125 s** of Running; line 218 then gains stress at
`CBLStressGain 0.4/s` to 100 at **~375 s**; line 219 sets `fault=true, active=false` and warns
`CBL overloaded`. All three fault together because their clocks are identical.

Cold arithmetic confirms the default level rather than assuming it: heat = 3 CBLs × level 2 ×
`CBLHeat 65` = **390**, cooling = 3 pumps × level 1 × `PumpCooling 120` = **360**, net +30 × the
0.4 per-step scale = **+12/s**, which is exactly the **+12.1/s** measured live. After the fault
heat is 0 while the pumps still cool, so line 224 runs at **~−138/s**: temperature falls off a
cliff while pressure is still coasting — precisely the pair (2227, 16229), and `coreState 0`
explains `RadiationVal=120` and `OutputVal=0`. The shift was winnable only because the `SHUTDOWN`
click landed inside the **~60–90 s window** before the crash reached `StallTemperature 2000`, and
shutdown requires temperature below `ShutdownLimit 17000` and energy at/above quota, both of which
still held. Reproduced in a replay that was **not** clicked: it left Running at `t=618` as
`phase=Failed`, reactor stallout.

**The remedy is already in the engine** — no code changed, no gameplay constant moved.
`cbl_purge` (lines 106–110) sets `device.pressure=0` and relieves `CBLPurgeStressRelief 25` with
`CBLPurgeCooldown 4`, so purging every ~100 s holds `device.pressure` below 75 forever and stress
never leaves 0. A fault is recoverable only through `Repair`, whose line 156 clears `fault` only
when `stress==0`, and line 104 refuses the `cbl` command outright while faulted. A missed purge
cadence costs the shift.

### Two bridge gaps, measured and left alone

`StateBridge` makes 19 `set()` calls: `Core.{TemperatureVal, PressureVal, OutputVal, RadiationVal,
HDEFVal, BreachVal, EnergyVal, QuotaVal, StressVal}`; `Stats.{GameActive, GameStart, GameFail,
NextShift, ResetShift, ChamberGravity, GravatronActive, DecayFields, ActiveQPUs}`;
`CBLn.{Active, TempVal}`; `Fans.Fan1..6`. It does **not** publish `Stats.HDEF.IntegrityVal`,
`Stats.ReportsDone`, `Stats.AutoMed`, `Stats.ISEBreach`, `Stats.MainframeMeltdown`.

- **RETRACTED 2026-09-26: `HDEF.IntegrityVal` does not lie, because nothing is listening.** This
  bullet used to claim that anything reading the HDEF gauge saw a full generator on a breached one.
  A grep over every script in `Workspace` (106), `StarterGui` (6) and `ReplicatedStorage` (1) finds
  **zero readers and zero writers**: the frozen 12 is displayed nowhere. It is a dangling
  ValueObject. The scale question it raised is real, and is recorded in the decisions section at the
  end of this file.
- **RETRACTED 2026-09-26: `ReportsDone` is an acknowledgement counter, not a report counter.** Its
  reader is `StarterGui.ScreenGui.EndShiftHandler` (610 lines), which compares the value against the
  **player count** to print `Waiting for report acknowledgement signatures [n/N]`. So it never
  counted completed shifts, and the shipped game's own telemetry records it as **0 in all 477
  ticks** — there was no writer upstream either. It stays 0 because the acknowledgement path was
  never finished, not because a shift counter is missing.
- The other three are read **only** by `ServerStorage.Data.DataCollection.Log`, which per
  CLAUDE.md §0.12 can never run — dead data, not a defect.

### The end-shift transport is unwired — the real remaining gap

Across all **427 scripts**, the place has **exactly one gameplay server-side `OnServerEvent`
listener**: the `ResetEvent` binding in `Runtime` added 2026-09-26. The other eight are Roblox
CoreGui internals (chat, sound, VR). **Nothing on the client fires `ResetEvent`.** The legacy
report UI fires `ReplicatedStorage.MiscEvent` with a mode string instead — and `MiscEvent` has
**no listener anywhere** — while that same UI waits on `EndShift.OnClientEvent`, which nothing
fires either. `ToolEvent`, fired by every QPU and tool `ClientScript`, likewise has no listener.

So the shift is **engine-complete and UI-orphaned**: the phase machine can be driven and a shift
can be won, but the legacy report screen will never be shown and its reports counter will read 0
forever. Re-driving the legacy UI vs. writing a new one is an open choice that belongs to the user.

### Click method, now rule-based rather than hand-tuned

- A control's **panel normal is its smallest size axis mapped through its CFrame**: round buttons
  of size `(0.053, 0.267, 0.267)` are thin in local X → normal = `RightVector`; levers of size
  `(1.0, 0.25, 0.85)` are thin in local Y → normal = `UpVector`. Camera eye =
  `part.Position + normal*6`. This rule reproduced the previous session's hand-tuned fan camera
  to within **0.6 studs**.
- Pixels are found by scanning **integer** viewport pixels, keeping only those whose first
  raycast hit carries a `ClickDetector` whose `ClickPartText` equals the wanted label, and picking
  the match nearest the match-set centroid.
- A cached pixel is valid only under the exact `CFrame.lookAt(eye, anchor)` that produced it, so
  the cache stores `{px, py, eye, anchor}` and the pose is re-held before clicking.
- Reach is **character-based** against `Interaction.MaximumDistance 6`, so one park covers a
  cluster: 4 ALT controls within 0.51/2.10 studs, 8 main controls within 4.9 studs, the CBL
  purges from CBL-2 at 4.95 studs.

### Tooling fact, measured

**`loadstring` is not available in the `rblx_execute_luau` VM** — the call fails with
`loadstring() is not available` from the Assistant's own wrapper, so CLAUDE.md §0.3's advice to
`loadstring` a module to bypass the require cache **does not apply to this tool family**. What
works instead, for a constructor-style module, is to `require` it and build a private instance:
`require(Engine)` returns a fresh module table whose `Engine.new(Config)` yields an **isolated**
state — which is what made the replay above possible and non-destructive. That `require` is not
the running game's engine (§0.2), which is exactly why the replay could not disturb the live one.

### What this session did *not* touch

The CBL, extraction, MASS and E-VENT **click** families are still unexercised (their mapping is
proven, and the CBL *purge* family was clicked this run). No source file was edited: the only
Studio change of the session was leaving Play mode. The `HDEF.IntegrityVal` and `ReportsDone`
publish gaps and the end-shift transport are recorded above and need a decision, not a patch.
**Both gaps were re-measured and re-classified on 2026-09-26** — see the decisions section at the end
of this file; neither is a publish gap, and one of them is a scale error instead.

---

## September 26, 2026 (video 3) — the third video, and the two systems the backend lacks

`Videos/` gained a third video: *The Reactor – The Best Roblox Game You've Never Played*
(502.64 s, 640×360, @theginypig — the same author as video 1). It is summarised in that folder's
`SingleSummary.md` and `Information.json`, and folded into `Videos/TotalSummary.md`.

**Constant table contribution: zero.** Its only number is "over 18,000 F", which restates video 2's
documentation screen and therefore `Sim.State2 = 17500`. It is silent on the state 3 upper bound, so
**35000 vs 39000 remains unresolved** and still needs a live measurement.

**It is also the weakest source of the three.** Same author as video 1, but video 1 teaches mechanics
while this one sells a feeling. The narrator admits three times that he does not know — the gravity
room's purpose, that coolant pipes degrade, and that he has never beaten Shift 3 — and closes by
asking for a subscription. The adjudication order gains a third narration tier:

```
live place  >  video 1 narration  >  video 3 narration  >  video 2 on-screen OCR
```

### What it does contribute is scope

Two systems it describes have no code in the backend at all:

| Missing | Detail |
|---|---|
| **Economy** | an inter-run lobby where upgrades are bought with the previous run's profit; the company is greedy; the player pays out of pocket for radiation treatment and coolant; upgrades are committed before teleporting into the facility |
| **Shift tiers** | Shift 1 basic control → Shift 2 adds the mainframe and software failures → Shift 3 opens the reactor chamber for internal components plus a gravity room → Shift 4 unreached and doubted. New systems unlock and new rooms open per shift, so the shift **number is a progression gate**, not a repeat counter |
| **Rooms** | `coolant room`, `server room` — the backend has no concept of rooms |
| **Pipe ageing** | `coolant pipes degrade over time`, distinct from the existing `PumpWearPerLevel` pump wear |

**None of it was implemented.** Every claim is narration-only: none of the 42 sampled frames shows a
lobby, an upgrade shop, a currency figure or any menu UI, so the economy sits below even the video
tier and must be verified in the live place first.

### A hypothesis that was tested and withdrawn

`Stats.ReportsDone` was proposed here as the natural shift number, which would have re-ranked it from a
publish gap to a missing design element. **It is false, on two independent grounds**, both checked on
2026-09-26. The legacy `EndShiftHandler` uses the value as an **acknowledgement signature count** — it
compares it against `#game.Players:GetPlayers()` — not as a shift index. And the shipped game's own
telemetry in `ServerStorage.Data.DataCollection.Log` records it as **0 in all 477 ticks**, so it had no
writer upstream either. The shift number is instead a **parameter of the end-shift event** (`p4`), never
a `Stats` value. What remains true is the direction of the gap: nothing in the backend branches on a
shift index, and `NextShift`/`ResetShift` are booleans.

### The one piece of hard evidence: an independent check on the label map

Five console group captions appear repeatedly in video 3 and match `ControlBinder` actions one for
one: `MONITORS`/`PWR` → `monitor_power`, `ROOM LIGHT`/`PWR` → `lights`, `ALARM MUTE`/`TOG` → `mute`,
`CONTROL ROOM SHUTTERS`/`OPEN` → `shutters`, `M.A.S.S.1 FUNCTIONS`/`ACTIVATION BUTTONS` →
`mass_toggle`/`mass_level`. The earlier 62-of-62 audit ran `ControlBinder`'s own `commandFrom` over
the place's own labels — internally consistent but self-referential. **This is the first outside
corroboration of those labels.**

It also narrows a stale suspicion: the `CTRL n SYSTEMS` / `CTRL 2 POWER` panels, previously suspected
of belonging to a different game because video 2's copy matched nothing here, appear in video 3 on a
console that is unambiguously this game's, **filmed by a different author**. The suspicion narrows to
that video's inventory panel alone.

### Method change worth carrying

A string read from a contact sheet is admitted only if it **reproduces on a second independent read**,
and *which kind of check* is recorded, because the two available checks catch different failures:

| Check | Catches | Cannot catch |
|---|---|---|
| re-read the **same sheet** | an **unstable** string | a **consistently invented** string |
| re-read a **single frame** | an **invented** string | — |

`CTRL 2 SYSTEMS` came back as `CTRL 3 SYSTEMS` on the second sheet read, so its index is unusable.
In video 3 the single-frame reads returned **no text at all** while the sheets plainly had text, so
only the weaker check was available. Two casualty classes are recorded as excluded: `TESSERAC`, and
everything the vision sidecar produced in `mode=ui` — it invented `SUPERNOVA ACTIVE`,
`FACILITY PROTOTYPES`, and a claim that the engine was Unreal at 1080p/4K from a 640×360 source.
**Use `mode=ocr` only.**

---

## September 26, 2026 (decisions) — four questions answered, and two of my own claims withdrawn

The four open questions were put to the user. The answers: **write a new report UI only if it beats the
original**; question two was not understood as phrased; **set the visual refresh to 1 s**; the folder
name is my call. Two changes were made and two claims were retracted.

### Change 1 — `Config.Visual.RefreshSeconds` 0.2 → 1

Despite its name this is the **single outer tick gate** in `Runtime`, so it covers logic and visuals
together; there is no second loop. Logic cadence does **not** change: `Engine:Update` accumulates `dt`
and steps only in `Sim.Step = 1` chunks, so at 0.2 the engine was already stepping once per second and
merely driving the lamps five times a second. At 1.0 the accumulate, the step and the refresh become the
same event and no residual is carried. Verified by loading `Config.Source` into a throwaway ModuleScript
for a fresh compile — the require cache would have returned pre-edit bytecode — which returned
`refreshSeconds 1`, `refreshType number`, `Sim.Step 1`, `sourceLen 4115`, `probeGone true`.

### Change 2 — the backend folder is renamed `ReactorBackend`

A grep across all scripts for the old name found it in exactly **one** place before the rename, and that
place was documentation. Nothing resolved the backend by path; `Runtime` uses `script.Parent` and its log
tag has said `[ReactorBackend]` since the start. The tree now agrees with the code and with the historical
notes this file used to call wrong. Verified after the rename: 6 children, no stale name,
`Runtime.Disabled` false.

### Retraction 1 — `ReportsDone` is not the shift number

See the withdrawal above. The decisive evidence is the legacy UI's own use of the field, plus 477 shipped
ticks of it reading 0.

### Retraction 2 — `HDEF.IntegrityVal` is not a lying instrument, but a scale question replaces it

Nothing reads or writes it anywhere: 106 `Workspace` scripts, 6 `StarterGui`, 1 `ReplicatedStorage`, all
zero matches. But measuring the shipped telemetry turned up something better. Across the same 477 ticks
`HDEF.IntegrityVal` takes the values **99** (319 times), **12** (154 times) and 93, 76, 57, 31 once each,
so the shipped scale runs from about **12 up to about 100**. `Config.Device.HDEFMaxIntegrity` is **12**,
which puts the shipped *floor* where the ceiling should be, and `VisualFeedback` divides that 12 into
three lamps of 4 on the strength of it. This is a constant-provenance question with real evidence behind
it rather than a publish gap — but it is a balance change, so it was **reported and held** rather than
applied unilaterally. **The user then set the range to 0-100 on 2026-09-26 and it was applied** — see the
HDEF section at the end of this file.

### The report UI: use the original, and the real gap is the transport

Rewriting was rejected. The legacy `EndShiftHandler` is 610 lines of authored choreography over a
purpose-built GUI tree: a hold-for-1.5-seconds acknowledgement gesture, a stat-by-stat animated money
tally, an intermission screen, a next/reset/lobby branch, a **67-second secret ending** that fires on
shift 3 with the quota met, and a **22-line diagnostic easter egg**. A rewrite would delete content.

What is missing is the transport, and the legacy script states its own contract:

| Direction | Remote | State |
|---|---|---|
| server → client | `EndShift.OnClientEvent` with (statLines, endReason, totalMoney, shiftNumber, sessionTable, metuFraction) | **nothing fires it** |
| client → server | `MiscEvent:FireServer(mode)` where mode is `Next` / `Reset` / `Lobby` | **no server listener** |

It cannot be wired honestly yet: **most of that payload is money** — per-stat gains and losses plus a net
total — and this backend has no economy. Filling the screen with invented or zeroed money would put false
numbers in front of the operator, which is the same failure the HDEF lamp fix removed. **The legacy UI is
therefore the specification of the missing economy, not a component to reimplement.

---

## September 26, 2026 (HDEF) — the integrity scale corrected to 0-100, and a live boot to check it

**The user's instruction:** `HDEF Integrity 量程为 0-100`. That settles the scale question the previous
section raised and left open, and it matches the shipped telemetry exactly: `ServerStorage.Data.
DataCollection.Log` records `HDEF.IntegrityVal` over 477 ticks as 99 (×319), 12 (×154) and 93 / 76 / 57 /
31 once each — a band inside 0-100. The old constant, 12, was the shipped **floor** read as the ceiling.

Three files changed.

| File | Change |
|---|---|
| `Config` | `Device.HDEFMaxIntegrity` 12 → **100**, with the evidence and the side effect written into the comment |
| `VisualFeedback` | the lamp step is now **derived**: `Config.Device.HDEFMaxIntegrity / HDEF_LAMP_SEGMENTS` (3), replacing the literal `HDEF_LAMP_STEP = 4` |
| `StateBridge` | now publishes `Stats.HDEF.IntegrityVal` from `state.hdef.integrity` — the field the shipped game actually carried integrity in |

**Why the lamp step had to stop being a literal.** `4` was one quarter of 12. Left alone it would have lit
all three lamps on a generator at integrity 13 — nearly empty — the moment the ceiling moved. It is derived
now, so the partition follows the constant instead of shadowing it.

**Verified, not assumed.** `Config` was loaded through a throwaway ModuleScript for a fresh compile (the
require cache would have returned pre-edit bytecode), returning `maxIntegrity 100`, `refreshSeconds 1`,
`Sim.Step 1`, `sourceLen 4738`. A scan of every script in the DataModel for the retired literal
`HDEF_LAMP_STEP` returned **zero hits**, so no caller was left behind. And a six-case truth table over the
new partition was *computed from the source* rather than reasoned about:

| integrity | enabled | fault | lamps lit |
|---|---|---|---|
| 100 | true | false | 3 |
| 67 | true | false | 3 |
| 34 | true | false | 2 |
| 33 | true | false | 1 |
| 1 | true | false | 1 |
| 0 | true | false | 0 |
| 50 | true | **true** | 0 |
| 50 | **false** | false | 0 |

### The boot, by real clicks

`Runtime.Disabled` is false and the whole startup chain was driven again this run — four controls, four
acceptances, read from `ControlBinder`'s own log with no `rejected:` after any of them:

```text
[ReactorBackend][Control] andypeng1NB -> MONITOR POWER BUTTON
[ReactorBackend][Control] andypeng1NB -> CONTROL ROOM SHUTTERS SWITCH
[ReactorBackend][Control] andypeng1NB -> MONITOR BOOT BUTTON
[ReactorBackend][Control] andypeng1NB -> MASTER START-UP SWITCH
```

Phase reached `Running` and the published values moved on their own: `TemperatureVal 20 → 9883 → 13604`,
`OutputVal 0 → 80 → 92`, `RadiationVal 240`, `PressureVal 4728`, `CBL1/2/3.Active` true with `TempVal`
9883, `EnergyVal` climbing toward `QuotaVal 512`. **`HDEF.IntegrityVal` reads 99 and so does
`Core.HDEFVal`** — the two now agree, where the old pair disagreed (12 against 0) purely because the
ceiling was wrong.

### The HDEF duty cycle, exercised end to end

`HDEF GEN ACTIVATION SWITCH` was clicked once, accepted. The three lamps — address
`Consoles.HDEFGenerator.PowerLever.BigLever.Neon1..3`, **found by asking `VisualFeedback`'s own address
table** after a first sweep for parts literally named `NeonPart` returned 20 room lights and none of them —
went from the off colour to lit, which is the correct partition at integrity 99 against a step of 33.33:

| | `Neon1` | `Neon2` | `Neon3` | `LeverUnion` rotation block |
|---|---|---|---|---|
| before | `0.176471` | `0.176471` | `0.176471` | `0, -1, 0 / 0, 0, 1 / -1, 0, 0` |
| after | `0.921569` | `0.921569` | `0.921569` | `0, -0.5, 0.866 / 0, 0.866, 0.5 / -1, 0, 0` |

The rotation block is a clean **60°** about the lever's own axis — `THROW_DEGREES = 60` — and only
`LeverUnion` carries it.

### A display boundary found on the way, and not "fixed"

Integrity publishes as **99 while the generator is on and healthy**, and the engine's own value there is
`99.975`. Line 180 recovers toward the maximum and clamps at it, then line 241 subtracts the decay in the
same step, so the value oscillates just under the ceiling and `math.floor` reports one short of it. The
same boundary existed at the old maximum 12, where it read 11; it is a rounding display, not a scale
error, and changing `math.floor` to a round would be a display decision rather than a correction, so it is
recorded here and left alone.

### The one real change in feel, and it is a balance question

`HDEFDecay` and `HDEFRecovery` are **per-second rates**, so against a maximum of 100 they are eight times
(100 / 12 = 8.33) gentler in absolute terms than they were against 12. At `coreState 1` the generator drains at `0.025/s`,
i.e. **4000 s** to empty where twelve units allowed 480 s; at `coreState 3` it is `0.075/s`, 1333 s against
the old 160 s. Whether the rate should be rescaled with the ceiling is the user's call, not something to
settle here.

### Also recorded: a probe of my own that lied

A first read of the `Stats` tree appeared to show `GameStart` and `CBL1.Active` **missing**, which looked
like several of `StateBridge`'s 19 `set()` calls silently landing on nothing. They were not. The helper was
written `n and n.Value or 'nil'`, and in Lua `false or 'nil'` is `'nil'`, so **a `BoolValue` that is
currently false is reported as absent**. The tree is complete — 41 descendants, including every BoolValue
the backend publishes. A falsy-read trap in a probe, the same family as the `#`-on-an-Instance-keyed-table
trap this file already carries.**

## September 26, 2026, second pass — the HDEF overheat path was finally fired, and the stallout turned out to be the manual's own design

Three replays against `Engine.new(Config)`, each booted through the full chain, none of them touching
the live engine. They close the item the in-game manual left open when it named `hdef.fault` as a state
nothing had ever been observed to set.

### Zero input fails at 102 s, and that is authored

The six outtake fans are reset `true` on line 35, and line 217 charges pressure by
`floor(temperature / PressureDivisor) - fans * FanPressure`, which at `StartupTemperature 9420` is
`188 - 420`, i.e. about **-93 psi/s**. Pressure therefore falls from the `5000` line 163 sets, crosses
`StallPressure 2200`, and line 220 subtracts `StallCooling 750` from the temperature, which then falls
through `StallTemperature 2000` — **`Fail('Reactor stallout')` at 102 seconds of Running**.

Nothing was changed for this, because the manual documents the coupling itself: item 31 tells the
operator to *disable the outtake fans periodically when in State 1 to avoid stallout*, and item 87 puts
stallout possibility below roughly 6000 F. What is measured is that **the fans are the only control that
reverses the sign of the pressure derivative at startup temperature**, so any shift observed to survive
for several hundred seconds necessarily ran with them off; no other reading of that longer run is
available from the record kept of it.

### The generator's 100 s clock loses a race it should not, when the pumps are idle

With the fans off and the generator on but the pumps left idle, heat climbs at exactly
`HDEFHeatGain 1/s` as designed — and the shift still dies first, at **91 s**, because `peaStress`
reaches 100 and line 236 fails it with `Power extraction assembly overload`. That is about **nine
seconds short** of the overheat.

Turning the three C-Pumps on as well holds `peaStress` at zero (`StressPumpRelief` pays for the
extraction), and then the generator clock wins outright:

| t | phase | temp | press | stress | hheat | hfault |
|---|---|---|---|---|---|---|
| 1 | Running | 10207 | 4717 | 2.4 | 2 | false |
| 50 | Running | 10950 | 8858 | 0.0 | 51 | false |
| **99** | Running | 11536 | 13272 | 0.0 | **100** | **true** |
| 125 | Running | 13250 | 15824 | 0.0 | 48 | true |
| 150 | Running | 15343 | 18669 | 0.0 | 0 | true |
| 278 | **Failed** | 39292 | 53343 | 8.4 | 0 | true |

Line **174** sets `hdef.fault` and `hdef.enabled = false`, and it is **the only line in the engine that
sets fault**; heat then decays at `HDEFHeatLoss 2/s` through 98, 48 and 0. So the manual's documented
duty cycle — *periodically shut it off* — is reachable in normal play, and what it takes is the pumps
running, not the generator alone.

The same run then melted down at t=278 at temperature 39292, which is line 234 against
`MeltdownTemperature 39000`, because running with the fans off drove pressure to 53343 while a State 3
core adds `State3Heat 700/s`. That is the manual's own advice to keep an E-VENT ready, and it is
likewise unmodified.

### A method correction, because it invalidated the first replay of the session

**The four startup commands cannot be issued in one burst at t=0.** Line 83 requires `phase == 'Ready'`
for `start`, and line 161 sets `Ready` only after `BootSeconds 3` of `Update` calls, so a chain fired
all at once returns `true, true, true, false` and leaves the shift sitting in `Ready`. The symptom was a
trace that ran four hundred steps without ever reaching `Running`, and the fix is to let the phase
machine advance between commands — five `Update` seconds after `monitor_power`, the shutters and the
boot, twelve after the start — which is also how the live virtual-mouse clicks have to be spaced.

### The lever throw was one number for four families, and the place's own template library says otherwise

`VisualFeedback` carried a single constant, `THROW_TRAVEL = 1.6`, applied to all 23 console levers,
and it moved them by *rotating about a marker* rather than sliding. That is where the number and the
motion both came from: the 11 airlock and gateway `LeverModel` rigs under `MovingParts.DecayFields`
carry 0.500 studs plus 60 degrees, and a door bar's motion had been generalised to every console
lever in the facility. Not one of those eleven rigs is a console lever. They are all
AirlockConsole or GatewayConsole door bars.

Two independent sources then gave the real travel, and both were measured rather than inferred.

**The console detent stacks.** The builder laid a click target on each console for every level,
along the line the lever slides, with the union parked on the first one:

| family | console | targets | span | levels |
|---|---|---|---|---|
| C-Pump | `CoolantControl1-3` | 0.001 / 0.799 / 1.599 | 1.599 | 3 |
| CBL | `CBL1-3Systems` | 0.000 / 0.400 / 0.800 / 1.203 / 1.603 | 1.603 | 5 |
| Extraction | `ExtractionLever` | 0.026 / 0.549 / 1.099 / 1.674 | 1.674 | 4 |
| Start-up | `StartUpBigLever` | 0.023 / 1.663 | 1.686 | 2 |

The target count equals the level count in all four, and the union sits on the first target in all
four. That is the rule the art encodes: **level 1 is the authored position.**

**`ReplicatedStorage.Levers`, the builder's own template library.** Four families parked at the
world origin -- `2Level`, `3Level`, `5Level`, `SmallLever`, 733 descendants -- and it is the only
source that says anything about the four controls whose consoles carry no per-level target at all.
A paragraph that used to stand in the module read that silence as the art giving no travel to read.

`SmallLever` is the one that mattered. Its `Up` union sits at x 88.225 and its `Down` union at
88.925: a throw of **0.700** studs. Its `ClickPart` sits at x 88.475 in **both** copies, which is the
fact the whole sign rule falls out of -- the click target is fixed to the console and only the union
slides. Twelve live levers wear that rig: six `CFLever`, three `E_VENTLever`, `ShuttersLever` and
the two `MASS` `PowerLever`s. They were being thrown 1.600, which is **2.29 times** the distance the
art authors.

The same library settles two smaller questions. `2Level` ships as `Up` and `Down` copies whose click
targets are named `Shut` and `Start`, at -0.023 and +1.663 -- so the two-stop family's authored stop
is Shut and its throw runs along **+LookVector**, which is where `StartUpBigLever`'s 1.686 comes
from. And `LeverOrginPart` is **not** a pivot and not a duplicate of the union: in `3Level.Level1` it
reads 0.001 from the union, in `Level2` 0.800 and in `Level3` 1.600, so it is the fixed level-1
origin marker and the union slides away from it. A claim that used to stand in the module -- that it
sits at exactly the union's position in all seven console levers that have one -- was a measurement
of seven levers that all happened to be parked on their first stop.

### The old pose is not a pose this art contains

This is the argument that needs no semantic, and it is why the fix was not a judgement call. For the
CFLever rigs the module drew the union at `U0 + 1.600 * LV`. That rig's two authored stops are
`U0 - 0.658 * LV` and `U0 + 0.042 * LV`. **1.600 is not between them.** A running fan was being drawn
1.6 studs out along an axis whose entire authored extent is 0.7 studs long on the other side of the
origin. The same reading applied to the fans versus the shutters, which are both authored on Down and
have opposite engine levels, is what retired the apparent contradiction between them without
inventing a semantic for either.

### The fix, and why the small family's throw is signed

`TRAVEL` is now measured per family -- `small 0.700`, `start 1.686`, `pump 1.599`, `cbl 1.603`,
`extract 1.674`, and `generic 1.6` standing in for the two controls that really do declare no detents
of their own. `HDEFGenerator.PowerLever` carries one `ClickPart` and `OverchargeLever.BigLever` none,
so there is no span to read for those two. `throwDistance` now takes the travel as an argument, and
`poseLever` **translates** along the lever's own baseline `LookVector`, which matters because the HDEF
lever's `LookVector` is `(0, -1, 0)` and it has to travel straight down rather than along world Y by
accident.

The small family is the one whose throw can be **negative**, and the sign is read per rig rather than
written down. `ClickPart` is fixed and only the union slides, so moving the union by delta moves
`d = (ClickPart.Position - union.Position) . LookVector` by **minus delta**. Going from the stop a rig
sits on to the other stop is therefore `d` minus *that other stop's own offset*, which is +0.700 for a
rig authored on Up and -0.700 for one authored on Down. Reading each rig's own `d` is what makes a rig
parked slightly off its stop land exactly on both: the CFLevers read -0.408, which is 0.042 short of
Down, so their throw is -0.658 and they finish exactly on the Up stop instead of 0.042 past it.

Measured live, all twelve: `E_VENTLever1-3` read +0.250, `MASS1-2.PowerLever` +0.248, `ShuttersLever`
-0.450 and `CFLever1-6` -0.408. The first five are authored on Up and the last seven on Down, and that
is not guessable from the engine's levels -- the fans and the shutters are both authored on Down and
have opposite engine levels -- so the direction comes from the art and the only thing the engine
decides is *which* of the two stops to show.

### Verified three ways

**An Edit-mode sweep of all 21 levers, both endpoints, against the live art.** `Initialize` was called
on a freshly compiled copy of the module, then `Refresh` twice -- once with every control at level 1
and once with every control at its top level -- reading each union's displacement along its own axis.
All 21 matched their family's expected throw (**0 failures**), and for the eleven small-family levers
the *posed* endpoint landed on a canonical stop to within 0.002 studs: `dMax = +0.250` for the fans,
the MASS levers and the shutters, `-0.450` for the E-VENT levers. The place was then restored from a
snapshot taken before the sweep and re-read: **0 restore failures**, so the sweep left the DataModel
identical to how it found it.

**The live server.** Reading every small-family lever out of the running game gives
`fan1/2/6 = +0.250`, `vent1/2 = +0.250`, `mass1 = +0.248`, `shutters = -0.450`. The engine boots
`fans = true`, so the six fans are at level 2 and are sitting exactly on the Up stop. Under the old
constant the same reading would have been **-2.008**.

**A real click, both endpoints, on both sides of the network.** A click on
`Consoles.ThermalConsole.CFLever1.ClickPart` (label `COOLING FAN SWITCH 1`, logged by `ControlBinder`
as `andypeng1NB -> COOLING FAN SWITCH 1`) took the union from the Up stop back to the art's authored
off pose, and a second click returned it to the stop:

| | union CFrame | d | verdict | `OfflineLight` |
|---|---|---|---|---|
| before | `108.1075, 280.1422, -15.5210` | +0.250 | Up stop | `0.176471` grey |
| click | `108.7046, 279.9172, -15.6809` | -0.408 | authored off pose | `1, 0.27451, 0.156863` red |
| click | `108.1075, 280.1422, -15.5210` | +0.250 | **Up stop** | `0.176471` grey |

Server and client agreed to the last float at both endpoints, and `CFLever2` never moved.

### Three gates between a virtual click and a lever, two of which are not obvious

The click rig cost more than it should have, and the reason is that a raycast hitting the ClickPart is
not sufficient for the click to be accepted.

1. **`MaxActivationDistance` is 6, measured.** `ClickDetector` gates on the distance from the
   *character* to the detector, not on the mouse ray. The character was 1397 studs away in the gateway
   room, and the click was correctly rejected with the mouse already reading `Mouse.Target` as the
   ClickPart. The standing spot used was 4.00 studs from the part, found by raycasting a ring of
   offsets for a floor position with a clear line to the target.
2. **StreamingEnabled means the console is not on the client at all.** `CFLever1.ClickPart` resolved
   to `NIL` client-side. `Player:RequestStreamAroundAsync` streams a region to that client **without
   moving anyone**, which fixes visibility but not gate 1 -- both are needed, and satisfying either one
   alone produces a click that silently does nothing.
3. **The camera must be held, not set.** The tool wrapper resets `CameraType` after each call and the
   reset can land between press and release, re-aiming the ray mid-click. Binding
   `RunService:BindToRenderStep(name, Enum.RenderPriority.Camera.Value + 1, fn)` to re-assert the
   camera every frame is what makes the press and the release hit the same part. With it, the aim read
   back `camType=Scriptable`, `camPos=117.00,280.05,-18.00` and
   `mouse.Target=Workspace.Consoles.ThermalConsole.CFLever1.ClickPart` immediately before the click.

The `+58 px` y offset on the mouse tool reproduced exactly: a 574x227 viewport, a request of `y = 55`,
and `UserInputService:GetMouseLocation()` reading back `287, 113` -- the viewport centre. The viewport
also resized between tool calls within the same session, so the pixel must be recomputed per call.

### The click chain, finished: a real click on the shutter, and what it cost

The shutter family was clicked for real and every leg of the chain was measured, not inferred. A
server-side listener attached to the detector itself counted `MouseClick fired = 1`, so the click is
known to have reached the binder rather than being assumed from a state change:

| | `LeverUnion` | delta | `OfflineLight.NeonPart` |
|---|---|---|---|
| before | `123.444, 279.549, 17.132` | -- | `255,128,1` amber |
| after click | `122.792, 279.789, 17.046` | `-0.652, +0.240, -0.086` | `45,45,45` off |

The delta magnitude is **0.700 studs**, which is the authored throw of the `SmallLever` rig the shutter
wears, to the last float. Both halves of the standard are therefore met at once: the click was accepted
*and* the player can see it -- the lever slid its own distance and the lamp changed colour.

### A client-authored teleport does not exist on the server

This is the gate that cost the most time and the one worth carrying forward. Writing
`hrp.CFrame = ...` from the **client** moves only the client's copy. The client read its own distance to
the ClickPart as `5.000`, comfortably inside the 6-stud gate, while the server read the same character at
`233.000, 406.087, 1370.000` -- `distance HRP->ClickPart = 1363.372`. Every click was refused, and the
client had no way to tell: its own view of the character was exactly where it had put it.

The standing spot has to be established **server-side**, and then the client's copy follows by
replication. `ControlBinder`'s gate reads `player.Character.HumanoidRootPart`, so the server's number is
the only one that decides. Anchoring the root, zeroing `AssemblyLinearVelocity` and forcing the Humanoid
out of its walking state on the server is what holds the position; a live Humanoid otherwise re-asserts
its own idea of where it should be.

### The camera and the character are independent; the mouse ray lives in a third space

Two separate coordinate facts, both measured:

- `Mouse.ViewSizeY = 111` while `Camera.ViewportSize.Y = 227`, and
  `UserInputService:GetMouseLocation()` reads `287, 171` when `Mouse.Y` reads `113`. The gap is a
  constant **58**, which is why the tool's requested `y` and the camera's viewport `y` differ by it at
  any viewport size. The practical rule already recorded in this file -- request `camera_viewport_y - 58`
  -- is the whole consequence.
- `Mouse.Target` is computed in the Mouse's space, not the camera's. At the same reported pixel the
  camera ray struck `ShuttersLever.ClickPart` while `Mouse.Target` reported
  `Workspace.Consoles.ALTReactorConsole.Part`, a `Transparency = 1` part that occludes in one space and
  not the other. A raycast that says "the ClickPart is under this pixel" is therefore not evidence that
  the Mouse agrees, and it is the Mouse that `ClickDetector` listens to.

`VirtualInputManager` is not a way around any of this. `SendMouseMoveEvent` fails with
`The current thread cannot call 'SendMouseMoveEvent' (lacking capability RobloxScript)` when called
from the plugin's Luau context, so an in-script clicker cannot be built; the click has to come from the
tool, with the pixel computed for it.

### The server-side probe: the FireClickDetector this project can actually have

The user's instruction was to stop paying for real clicks -- "写个类似于FireClickDetector的东西，没必要真的点".
The obstacle is that no script can fire a `ClickDetector`'s signal, and a `require` from the plugin VM
returns fresh module tables, so a probe run from `execute_luau` would drive a phantom.

The seam that works is a temporary `Script` parented to `ServerScriptService` during the playtest. It
executes in the **live server VM**, so `require(backend.VisualFeedback)` yields the very table `Runtime`
holds, baselines captured at boot included, while `Engine.new(Config, random)` supplies a private state
to drive -- which is the seam `Engine`'s own header documents: "Tests inject a deterministic random
source instead of modifying live gameplay." The engine instance `Runtime` owns is a local inside its
`xpcall` and is deliberately not reachable, and that is fine: the thing under test here is the
state-to-lamp mapping, not the live engine.

Two properties make the results trustworthy rather than merely plausible:

- Addresses are repeated in the probe rather than read out of `VisualFeedback`'s own table, so a probe
  cannot pass because the module was given the same wrong address it is being checked against.
- `Refresh` skips a repaint whose signature is unchanged, so every case is preceded by a baseline state
  whose signature is deliberately unlike any case. No case can read a colour left over from the one
  before it. A case whose signature *did* collide would in any case be asking for the same targets, so
  the gate can suppress work but cannot manufacture a pass.

Colours are compared through a palette-name lookup against `Config.Visual`, and anything outside the
palette reports itself as `OFF-PALETTE r,g,b` rather than passing as a near miss of the nearest key.

**The probe was written and enabled, and its output was never read**: the MCP bridge dropped between
enabling the script and reading `workspace.MCP_LAMPTEST`. Its results are therefore recorded nowhere
and must not be treated as established. The script itself is Play-mode only and does not survive the
session.

## The shipped telemetry as a measurement source

`ServerStorage.Data.DataCollection.Log` is 602,762 bytes holding **477 tick records, 44 log entries and 24
clicks** recorded on 2026-09-18. By the user's statement, **one gametick is one second**, so its timestamps,
its record count and its per-tick deltas are all on the same clock as `Config.Visual.RefreshSeconds`. It had
been cited in these documents before only for two negative results (`ReportsDone` held at 0, `HDEF.IntegrityVal`
ranging 12 to 99). Read as a source it is much more than that, and this section is what a full pass over it
establishes.

### The core-state thresholds are Fahrenheit

This was previously adjudicated by *agreement* -- `DataCollection`, `TRGWeb` and video 1 all say
5600/17500/29500/39000, the in-game manual says roughly 29000 for state 3, and video 2's screen says 35000.
Agreement is not measurement. The log measures it.

`reactor` publishes **two** temperatures, `tempC` and `tempF`, and they are not interchangeable: they differ
by a factor of 1.8. Sorting the 477 ticks by `coreState` and taking the extremes of each state gives the true
boundaries:

| quantity | state 0 max | state 1 min | state 1 max | state 2 min |
|---|---|---|---|---|
| `reactor.tempF` | 4851 | 6288 | 17449 | 18309 |
| `reactor.tempC` | 2677 | 3475 | 9676 | 10153 |

The state machine reads **`tempF`**. `State1 = 5600` falls in `(4851, 6288)`; `State2 = 17500` falls in
`(17449, 18309)` -- a 51 F margin, against a gap of 860. On `tempC` neither constant is inside a gap, or
within a thousand of one. A four-entry table also has a 3-to-4 edge, which is how the earlier 39000 reading
arose; this measurement is about the first two edges only.

Two unit facts fall out of the same pass and matter for reading any future log:

- `tempF - (tempC * 1.8 + 32)` is **never negative and never exceeds 1.6 F** over the 332 comparable ticks.
  That is the signature of `tempC = floor(x)` and `tempF = round(x * 1.8 + 32)` on **one** underlying float,
  not of two independent simulations. They are one quantity displayed twice.
- `tempC == -18` in **173 of 332** ticks. `-18 C` is exactly `0 F`. That is the idle floor, and a tick
  reading it is a reactor that is not running rather than a cold one.

### The log cannot settle the state 3 upper bound, and that is a result

The one constant still open is whether the state 3 upper bound is **35000** (video 2's documentation screen,
read twice) or **39000** (`DataCollection`, `TRGWeb`, video 1). The log is silent on it, structurally:

- `coreState` never exceeded **2** in any of the 477 ticks.
- `reactor.tempF` never exceeded **26637**, so the core was never taken past `State3 = 29500`.
- `GameFail`, `MainframeMeltdown` and `Core.BreachVal` are **false in all 477 records**.

Searching this source for the answer is a search that cannot succeed rather than one that has not yet
succeeded. The plan of record stands: burn the core between 35000 and 39000 and see whether it melts.

### The C-Pump fault is an event, not an integrity scalar

`VisualFeedback` carries `PUMP_FAULT_INTEGRITY = 25` and flagged it in its own source as *a chosen number, not
a measured one*. The obvious next move is to look the number up, and the telemetry is where that search goes
to die: its whole coolant block is `{sumLevel, levels[3]}`, and sweeping every leaf key in all 477 records
finds no pump integrity, no stability, no reservoir, no wear, no fault flag. That measurement stands -- but
the conclusion first drawn from it does not. **The shipped simulation had no integrity scalar, and the
quantity this constant stands for is not integrity.** The user named it on 2026-09-26: it is the pump's
**stability**, whose readout is the gauge on the calibration console. TRGWeb, the authoritative prototype
parked in the same ServerStorage.Data, declares `coolant_pump1_Stability = 100` for each of the three pumps
and only ever displays it, never writes it -- so 100 is full, the telemetry's silence is a gap in that log
rather than the absence of the mechanic, and `PUMP_FAULT_INTEGRITY` now has a name to sit under instead of
being an orphan integer. The gauge itself is built and completely unwired:
`Workspace.CRC1-3.ProcessorInterior.CalibrationConsole.PECScreen.SurfaceGui.ProcessorFrame.StabilityFrame`
carries a TextLabel reading NET STABILITY and a Bar fill behind it, and no script in the project references
StabilityFrame or CalibrationConsole at all.

What the shipped game did instead is visible as an event chain, and it is a different mechanic:

```
19:21:14  coolant levels  0,0,0  ->  3,3,3        (stepwise over 4 s)
19:21:15  [WARN]  C-PUMP 1 HIGH OUTPUT
19:21:17  [WARN]  C-PUMP 2 HIGH OUTPUT
19:21:17  [WARN]  C-PUMP 3 HIGH OUTPUT
19:21:33  [ALERT] C-PUMP MALFUNCTION DETECTED
19:21:34  [WARN]  IDENTIFICATION ERROR: SENSORS IMPAIRED
19:21:38  coolant levels  3,3,3  ->  0,0,0        (5 gt after the alarm)
19:21:49  C-PUMPS REACTIVATED
19:21:50  coolant levels  0,0,0  ->  2,2,2        (1 gt after the message)
19:21:54  coolant levels  2,2,2  ->  3,3,3        (ramping back)
```

Three properties, all measured: a fault's **observable is the pumps going to zero**, not a gauge drifting;
reactivation restores them to **level 2 against the level 3 they held**, so recovery is partial; and the
companion `IDENTIFICATION ERROR: SENSORS IMPAIRED` fires **one second after** the malfunction, which is the
mechanism behind the in-game manual's item 92 -- that coolant sensing has a tendency to be unreliable. In the
shipped game **a pump fault blinds the identification instead of reporting a number.** A rewrite that shows a
precise integrity figure and names the faulted pump is strictly more informative than the original, which is
a design choice worth making deliberately rather than by accident.

Whether the reactivation at 19:21:49 is automatic or a player click is **not determinable from this log** --
see the next subsection.

### The click entries are a partial record and are not an inventory

The log carries 24 `click` records naming ten distinct controls: `HDEF-Power`, `AVB`, `CBL1-PW1`,
`CBL1-PW5`, `CBL2-PW1`, `CBL2-PW5`, `Coolant1-ON`, `Coolant1-OFF`, `Coolant2-ON`, `Coolant2-OFF`,
`Coolant3-OFF`, `MASS1-Activate`, `MASS2-Activate`.

They are **incomplete**, and the proof is inside the same file. The log records core ignition at 19:18:16 and
`[ALERT] START-UP COMPLETED` at 19:18:34, which cannot happen without the startup, monitor-power and shutter
controls being operated -- and **not one of those appears among the 24**. Likewise the coolant levels rise to
`3,3,3` at 19:21:14 with no coolant click logged anywhere near it.

So the click records are evidence of **naming** and nothing else. An absent entry is not an absent event, and
any question of the form "did the player do X" cannot be answered from this file. The naming evidence is
still real and is a genuine alternative to the current design: the shipped encoding is a **flat single string
of the form `control-value`** (`CBL1-PW5`, `Coolant3-OFF`), where `ControlBinder` uses an `(action, index,
value)` triple through an ordered 62-branch chain. That was considered and not adopted.

### Two alarm mappings, measured

Both are **commanded-level** alarms rather than sensor conditions, which is worth knowing before building a
condition-based alarm layer:

- `C-PUMP n HIGH OUTPUT` fires when pump `n` is commanded to **level 3** -- observed at 19:21:15/17 against
  levels `3,3,3`, absent against `2,2,2` at 19:21:50, and back at 19:21:53/54 as the pumps ramp to 3.
- `CBL n HIGH OUTPUT` fires when CBL `n` is commanded to **level 5** (`PW5`) -- observed at 19:18:45/46
  immediately after `CBL1-PW5` and `CBL2-PW5`, against a CBL level of 4 earlier that produced no warning.

Coolant level is also **commanded rather than simulated**: three `OFF` clicks at 19:18:52 to 19:18:54 stepped
`1,1,1` to `0,0,0` one gametick each. That one-tick response is what makes the five-second gap between the
malfunction alarm and the pump zeroing a real, authored delay rather than logging latency.

### What this changes

Nothing in the backend was changed for any of it, and one item is now closed as unanswerable from this
source. The concrete consequences are: the state-threshold unit is measured rather than inferred;
`PUMP_FAULT_INTEGRITY = 25` is now labelled in the module rather than carried as an unproven constant: the
user's 2026-09-26 naming makes it the pump's stability and the calibration console's NET STABILITY gauge its
readout, with 25 still a chosen threshold, and the original's event-and-partial-recovery model is recorded
as the alternative; and any future claim that a control was or was not operated cannot be sourced from
`DataCollection.Log`.
future claim that a control was or was not operated cannot be sourced from `DataCollection.Log`.

## September 26, 2026 (lamps) — the thirteen lamps proven, and an Initialize that was not idempotent

The thirteen lamps carried as unproven since they were wired — `shutter`, `mute`, `atmo`, `vent1-3`,
the two gravatron lamps, `sam1-2` and the three CBL pressure buttons — are proven, **38 of 38**, by
the server-side probe under `ServerScriptService.MCP_LampProbe`.

They were unproven because the probe was wrong, not because the lamps were. The probe is a **Server
Script**, and Server Scripts start in an undefined order: it lost a race with `Runtime`, ran
`VisualFeedback.Refresh` against a module whose `levers` and `lamps` tables were **still empty**, and
so measured a module that touched nothing. Every `poseLever` and `lightLamp` returns early when its
key is absent, so the probe read each part's **authored** colour, constant across every case — which is
exactly what a broken lamp looks like. Every start-up comparison read `delta 0.0000` for the same
reason, five of them counted as passes because nothing had moved and the sixth, `starting != cold`, as
a failure.

Only seven of the thirty-eight cases passed, and **the two colour cases that passed are what named the
fault rather than hiding it**: `atmo while running` and `cbl1 nominal` both read `Nominal`, because
`MainReactorConsole.AtmosphereVentButton.NeonPart` and `CBL1-3Systems.PressureButton.NeonPart` are
authored `(137,255,147)` and `Config.Visual.Nominal` was **measured off them**. A lamp cannot read a
palette entry by accident unless nothing painted it. The probe now calls
`VisualFeedback.Initialize(Config)` itself, prints any error `Refresh` throws instead of dying
silently, and reports its own key count rather than using `#` on a string-keyed table.

What is proven, family by family:

| family | proven |
|---|---|
| `shutterLamp` | closed to `Amber`, open to `Off` |
| `muteLamp` | off to `Off`, on to `Fault` |
| `atmoLamp` | cold to `Off`, running to `Nominal`, inside its own cooldown back to `Off` |
| `vent1-3Lamp` | unused to `Off`, spent to `Fault` |
| `cbl1-3Lamp` | `Off` while inactive, `Nominal`, `Yellow` at PW5, `Purple` on stress, `Blue` below stall pressure, `Fault`, and **all four precedence pairs**, each beating the branch it must |
| `gravSwitchLamp` | `Idle` to `Off`, `Charging` and `Armed` both to `Ready` |
| `gravArmedLamp` | `Charging` to `Off`, `Armed` to `Yellow` only |
| `samLamp1-2` | `Off`, then `Nominal` on both lamps together |

The master start-up lever is proven the same way: `Starting` moves it **1.686 studs**, exactly
`TRAVEL.start`; `Cold`, `Booting`, `Ready` and `Report` all read `delta 0.0000` against `Cold`, and
`Running` and `Stopping` are deliberately the same pose as `Starting`.

### The defect that fell out of it: `Initialize` was not idempotent

The probe's own `Initialize` call and `Runtime`'s produced **two** capture lines in one playtest, and
they disagreed:

```
1st: fan1=-0.658 fan2=-0.658 fan3=-0.658 fan4=-0.659 fan5=-0.659 fan6=-0.659
2nd: fan1=+0.700 fan2=+0.700 fan3=+0.700 fan4=+0.700 fan5=+0.700 fan6=+0.700
```

Only the first is a measurement. `smallThrow` reads a SmallLever's sign from the union's **current**
position — level 1 is whichever stop the rig is found on — and `Runtime`'s own first `Refresh` had
already driven the six fans to their far stop, because the engine boots with the fans running. The
second capture therefore measured the rig standing on its other stop and **inverted the travel of
every fan for the rest of the session**. The lever still moves on a click; it moves the wrong way and
lands on a pose the art does not contain, and nothing in the console reports it.

This also explains, after the fact, the flapping signs in the earlier boot log, which had been
attributed to the place having displaced levers. It had not: an Edit-mode measurement of all twelve
SmallLever rigs taken while writing this found **0 of 12 off their home stops**, and every rig read
exactly the `d` the module's own note records — `vent1-3` at `0.2502` against `0.250`, `mass1-2` at
`0.2482` against `0.248`, `shutters` at `-0.4501` against `-0.450`, `fan1-6` at `-0.4078` and
`-0.4094` against `-0.408`. The flapping was two `Initialize` calls per session all along.

The fix is that `Initialize` no longer empties `levers` and `lamps`: a key whose part is still
parented keeps its first capture, and only a key whose part has gone is re-resolved. A repeat call is
now a no-op for poses, which is what makes it safe to call from more than one place. Verified by
re-running the playtest: the two `throws:` lines are **byte-identical**, and the captures read **54 and
54** where they read 54 and 52 before.

That last pair is its own small fix. The SAM lamps are captured by walking the keyboard rather than by
resolving a path, and their `captured` increment sat **inside** the branch that added them, so a
repeat call counted two fewer than the first. The one number an operator watches for a lost capture
was the one number that moved on its own; the increment is now outside the branch.

`workspace.MCP_LAMPTEST` is created at runtime and does not survive the playtest, so nothing the probe
writes reaches the saved place. The probe is kept as a re-runnable instrument rather than deleted,
because it is the only thing that can re-prove this matrix after any change to an address or a
colour, and it is left in `ServerScriptService` with `Disabled` set to true so the saved place carries
no live probe and re-running it is one flag rather than a rewrite.

### Document drift, recorded rather than closed here

`ServerStorage.Data.BackendRewritePlan` is the in-game counterpart of this file and is **not** a
byte-mirror of it. Counting headings is a bad measure of it, which is the lesson: it carries four
`## ` headings, but its fourth holds items ONE through EIGHT, so the HDEF integrity scale, the HDEF
overheat run and the per-family lever throw with its three click gates are all already there. What it
was missing is the section above this one — the shipped telemetry as a measurement source — and it had
a defect of its own: its `EIGHT` section was present **twice, byte for byte**, `8600` bytes each, and
the duplicate was deleted while writing this.

So the drift here is one section, not five, and it took reading the item list rather than the heading
list to see it. The telemetry section is still absent from `BackendRewritePlan`; that gap is recorded
rather than closed. Two documents that are updated together and are not byte-mirrors will drift, and
the drift is visible only by reading the structure rather than by counting any one level of it.
