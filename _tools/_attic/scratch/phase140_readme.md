
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
