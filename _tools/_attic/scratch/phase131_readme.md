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
