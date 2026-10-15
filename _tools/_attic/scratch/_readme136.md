
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
CBL sum 0 with the pumps at 1, 2 or 3, so the original itself ran that way. It is added **outside**
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
