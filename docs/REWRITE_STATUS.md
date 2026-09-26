# AIRemake backend rewrite — working log

> **Superseded 2026-09-26.** The maintained AIRemake status document is
> [`airemake/REWRITE_STATUS.md`](airemake/REWRITE_STATUS.md), whose authoritative twin is
> the Studio module `ServerStorage.Data.BackendRewritePlan`. This file is kept for its
> September-25 history, which is reproduced unchanged below, plus the corrections that
> reading it against the live place produced.

Date: 2026-09-25. Target place: 83752844701736, The Reactor : AIRemake.

This is a disk-only work log, not a replacement for existing mirrored documents.
The historic GameCore documentation describes a different place (114398686378058).
Do not assume those systems exist in AIRemake or overwrite historic mirrors with
new-place claims. Studio remains authoritative for its current source.

## Corrections, 2026-09-26, from checking this file against the live place

Two artifacts this file describes **do not exist**, both checked by direct lookup
rather than by eye:

- `Workspace.ConsoleDesignStaging.MainReactorConsole_NewDesign` — absent. No
  Workspace child has "Staging" or "Design" in its name.
- `ServerStorage.BackendBaseline20260925` — absent. `ServerStorage` holds only
  `Data`, and a full DataModel search for "BackendBaseline" returns nothing.

The folder name this file and its siblings use for the backend,
`ServerScriptService.ReactorBackend`, is also wrong: that folder does not exist and
`ServerScriptService` has exactly one child, `ReferenceContent`.

**Superseded later on 2026-09-26.** The backend folder was renamed in Edit mode from
`ReferenceContent` to `ReactorBackend`, so the paragraph immediately above has it
backwards as of today: `ServerScriptService.ReactorBackend` now exists and holds the six
backend children, and `ReferenceContent` no longer does. The rename is recorded in
`airemake/DECISIONS.md`, `airemake/PROGRESS.md`, and the module's own LOCATION paragraph,
which had likewise been asserting the absence while the folder was being read out of.

Nothing was deleted and no geometry changed. What is missing is (a) the staging copy
and (b) the per-part record of where the 23 moved decorative parts came from. There is
no Open Cloud key and no local place file, so revision recovery is unavailable. Partial
recovery is still possible without inventing anything, because the move preserved every
CFrame: each part still sits at its original world position, so its former parent can be
derived from surrounding geometry. Not done yet.

Also worth recording: the backend rewrite this file proposes is the one that already
exists, in the folder now named `ReactorBackend` and named `ReferenceContent` at the time
of writing, and it is **verified working** — see
`airemake/REWRITE_STATUS.md`. The single reason it had appeared dead was
`Runtime.Disabled = true`.

## September 25 implementation checkpoint (unchanged)

- The live place has `Workspace.Consoles.MainReactorConsole` with 496 descendants,
  310 BaseParts, 8 ClickDetectors, 5 `LeverUnion` parts, and 7 `NeonPart` indicators.
- A reversible staging copy was created as
  `Workspace.ConsoleDesignStaging.MainReactorConsole_NewDesign`, offset +20 studs on X
  from the live console. It retains the original hierarchy and all name-bound controls.
- The staging copy carries `DesignSource = Workspace.Consoles.MainReactorConsole` and
  `DesignStatus = Staging copy`; the live console was not renamed, moved, or deleted.
- The copy is intentionally not in `Workspace.Consoles`, so the existing backend's
  console binder cannot accidentally register duplicate controls.

## Next safe design step (unchanged)

Replace only visual geometry inside the staging copy. Preserve the exact names
`ClickPart`, `LeverUnion`, `LeverOrginPart`, `NeonPart`, control model names, and
existing detector/attribute contracts. Validate descendant count and control anchors
before any staged design is promoted.

> Note: `Workspace.Consoles` currently holds exactly six consoles —
> `MainReactorConsole`, `ElectricGridConsole`, `ALTReactorConsole`, `CBLaserConsole`,
> `HDEFGenerator`, `ThermalConsole`. The measured lever contract for all 29
> `LeverUnion` parts, including their six distinct LookVectors, is tabulated in
> `airemake/REWRITE_STATUS.md`.
