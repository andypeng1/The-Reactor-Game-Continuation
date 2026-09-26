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
because it is the only thing that can re-prove this matrix after any change to an address or a colour.

### Document drift, recorded rather than closed here

`ServerStorage.Data.BackendRewritePlan` is the in-game counterpart of this file and is **not** a
byte-mirror of it. It carried four sections — the label-to-action audit, the shift lifecycle, video 3
and the four decisions — and was missing the HDEF integrity scale, the HDEF overheat run, the
per-family lever throw and the click chain that came after them. This section was added to it; the
earlier five were not, and that gap is recorded here rather than quietly passed over. Two documents
that are updated together and are not byte-mirrors will drift, and the drift is visible only by
counting sections.
