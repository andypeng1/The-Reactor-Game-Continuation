/* continuation_judge.js -- the pass/fail half of the continuation icon's check.
 *
 * Same split as _tools/cover_judge.js and _tools/page_judge.js (DECISIONS_2 309):
 * the browser MEASURES (cover/continuation.html's layoutReport()), this file
 * DECIDES.  A file that measures and then decides what counts as correct tends
 * to quietly redefine correct, so the two stay apart -- and staying apart is
 * what lets --selftest feed this file a deliberately broken report with no
 * browser involved.
 *
 * WHY A THIRD JUDGE.  The cover's rules are about a 1080-square poster with a
 * hero mark, a headline and a footer.  The continuation icon is a 1024-square
 * mark + one word: the objects that can be wrong are different objects, so
 * reusing A1/A5/A10 with renamed fields would be a rule that looks the same and
 * measures something else (CLAUDE.md 0.18).
 *
 * WHAT IS SHARED VERBATIM: the empty-set guard (C1 NAMES the things instead of
 * counting), the near-miss half of the collision rule (C3 reports the closest
 * miss, so "nothing collided" cannot pass because nothing was close), the
 * two-spellings-of-one-shape rule (C6), the asset-polarity rule (C10).
 *
 * WHAT THIS PAGE CANNOT HAVE, AND SAYS SO: it draws no raster asset.  So C10
 * keeps the "declaration matches filter" half and does NOT keep the cover's
 * "at least one layer must declare a real ASSET polarity" guard -- that guard's
 * object is absent here and a guard with no object can only ever be red or
 * vacuous (CLAUDE.md 0.31).  C10 instead requires at least one layer at all.
 *
 * THE RULE THAT IS NEW, AND IT IS THE POINT OF THE PICTURE (C7/C8): the icon is
 * supposed to say "continuation" -- a hexagon that does NOT close, whose open
 * end carries an arrowhead.  If the gap closes it is just a hexagon; if the
 * head is flipped the loop runs backwards.  Both look entirely plausible on a
 * 64px thumbnail, so both are measured, not eyeballed.
 *
 * Usage:
 *   node _tools/intro_render.js --page cover/continuation.html --at 0 --w 1024 --h 1024 \
 *        --eval 'layoutReport()' > report.txt
 *   node _tools/continuation_judge.js report.txt
 *   node _tools/continuation_judge.js --selftest report.txt
 */
'use strict';

const fs = require('fs');

const W = 1024, H = 1024;
const FRAME_IN = 20;                    // #frame's inset, from cover/continuation.html
const INNER = W - 2 * FRAME_IN;         // 984
const SAFE = 6;
const AXIS = W / 2;                     // every centred thing lives on x=512
const MARK_CLEAR = 24;                  // the mark must breathe above the word

function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});

  /* C0 -- the frame of reference.  Forgetting --w/--h letterboxes the stage and
     every coordinate below is in the wrong space; that is the realistic failure,
     not a made-up one. */
  add('C0 the design space is 1024x1024 and fills the viewport',
      m.stage.w === W && m.stage.h === H && m.innerW === W && m.innerH === H,
      `stage ${m.stage.w}x${m.stage.h}, viewport ${m.innerW}x${m.innerH}`);

  /* C1 -- non-vacuity, said before anything is judged.  Every rule below is
     "fits" / "does not collide", and both are free on a page that drew nothing. */
  const want = ['title', 'sub'];
  const missing = want.filter(id => {
    const t = m.text.find(x => x.id === id);
    return !t || !t.text;
  });
  const mk = m.mark || {};
  const head = (mk.head || {});
  add('C1 the two words and the three parts of the mark are present',
      missing.length === 0 &&
      (mk.worstAt !== undefined && mk.worstAt >= 0) &&
      (mk.gap > 20) && (head.len > 20) && (mk.coreR > 10),
      (missing.length ? `MISSING: ${missing.join(',')}` : 'CONTINUATION + THE REACTOR GAME present') +
      `; loop gap ${mk.gap}px, head ${head.len}px, core r ${mk.coreR}px`);

  /* C2 -- every text block is inside the frame.  Roblox re-crops this image into
     a circle and into several card slots; type under the frame edge is type that
     gets cut. */
  const outside = m.text.filter(t =>
    t.left < FRAME_IN + 4 || t.right > W - FRAME_IN - 4 ||
    t.top  < FRAME_IN + 4 || t.bottom > H - FRAME_IN - 4);
  add('C2 every text block is inside the frame',
      outside.length === 0,
      outside.length ? outside.map(t => `${t.id} [${t.left}..${t.right}]x[${t.top}..${t.bottom}]`).join('; ')
                     : `${m.text.length} blocks inside [${FRAME_IN + 4}..${W - FRAME_IN - 4}]`);

  /* C3 -- no two text blocks overlap, AND some pair was close enough to matter.
     The two lines are 31px apart by their glyph boxes, so this rule is
     load-bearing rather than decorative. */
  let pairs = 0, worst = null, minGap = Infinity;
  for (let i = 0; i < m.text.length; i++) for (let j = i + 1; j < m.text.length; j++){
    const a = m.text[i], b = m.text[j];
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 0 && oy > 0){
      pairs++;
      if (!worst || ox * oy > worst.area) worst = {a: a.id, b: b.id, area: ox * oy, oy};
    } else if (ox > 0){
      const g = Math.max(a.top, b.top) - Math.min(a.bottom, b.bottom);
      if (g < minGap) minGap = g;
    }
  }
  add('C3 no two text blocks collide, and the nearest pair really is close',
      pairs === 0 && minGap < 40,
      pairs ? `${worst.a} over ${worst.b} by ${worst.oy.toFixed(2)}px (${worst.area.toFixed(0)}px2)`
            : (minGap === Infinity
                 ? 'NO TWO BLOCKS SHARE A COLUMN -- this test has no force'
                 : `0 colliding; closest vertical miss ${minGap.toFixed(2)}px`));

  /* C4 -- the word.  Three claims: it fits the inner width, its glyph height
     survives the 1/5 thumbnail (Roblox's card size), and the number printed is
     the one a reader actually gets.  Centring is C9's job, not this one. */
  const title = m.text.find(t => t.id === 'title');
  const tW = title ? title.right - title.left : NaN;
  const tH = title ? title.bottom - title.top : NaN;
  add('C4 the word fits the width and stays readable at 1/5',
      !!title && tW <= W - 2 * FRAME_IN - 16 && tH >= 80,
      title ? `width ${tW.toFixed(1)} of ${W - 2 * FRAME_IN - 16}, glyph height ${tH.toFixed(1)}px ` +
              `(${(tH / 5).toFixed(2)}px at 1/5)`
            : 'no title measured');

  /* C5 -- the mark is inside the frame AND clears the word under it.  A mark
     that drifts down does not collide until it is already 40px into the type;
     the clearance is what keeps the lockup from turning into one blob. */
  const b = mk.bounds || {};
  const clear = (b.bottom !== undefined && title) ? title.top - b.bottom : NaN;
  add('C5 the mark is inside the frame and clear of the word',
      b.left  > FRAME_IN + SAFE && b.right  < W - FRAME_IN - SAFE &&
      b.top   > FRAME_IN + SAFE && b.bottom < H - FRAME_IN - SAFE &&
      clear >= MARK_CLEAR,
      `mark x[${b.left}..${b.right}] y[${b.top}..${b.bottom}], ` +
      `${Number.isFinite(clear) ? clear.toFixed(1) : 'n/a'}px above the word (needs ${MARK_CLEAR})`);

  /* C6 -- the drawn loop is the analytic hexagon.  The page writes the points
     attribute from HEX_R/centre and the report parses it BACK; a hand-edited
     string, a swapped vertex order or a drifting radius all show up here.  The
     cover's A6/A7 argument: two hexagons that are not the same hexagon still
     both look like hexagons. */
  add('C6 the drawn loop is the analytic hexagon',
      mk.worstVertexPx < 0.5,
      `worst corner ${mk.worstVertexPx}px off (corner #${mk.worstAt})`);

  /* C7 -- THE LOOP IS OPEN.  Bounded on both sides: a gap that closes reads as
     a finished hexagon, and a gap that swallows half the edge reads as a broken
     shape.  The arrowhead may not fill the gap either -- that is why the
     reading is tip-to-start, not the gap itself.  And the tip must sit on the
     edge's own line, not float inside or outside it. */
  add('C7 the loop is open: a bounded gap with the arrowhead inside it, on the edge',
      mk.gapFrac >= 0.12 && mk.gapFrac <= 0.55 &&
      mk.tipToStart >= 8 && mk.tipToStart < mk.gap &&
      mk.tipOffEdge < 1.0 &&
      mk.start[1] > mk.end[1],
      `gap ${mk.gap}px (${(mk.gapFrac * 100).toFixed(1)}% of R), tip-to-start ${mk.tipToStart}px, ` +
      `tip off the edge line ${mk.tipOffEdge}px, start below end: ${mk.start[1] > mk.end[1]}`);

  /* C8 -- the arrowhead runs WITH the loop, at a size that reads.  A reversed
     head is the quiet failure here: the picture still looks like an arrow, it
     just says "go back". */
  add('C8 the arrowhead runs with the loop and is the right size',
      head.dot > 0.99 && head.len >= 24 && head.len <= 90 &&
      head.half >= 16 && head.half <= 60,
      `head ${head.len}x${head.half * 2}px, dot with the run direction ${head.dot}`);

  /* C9 -- one vertical axis.  The mark's centre, the word and the subtitle are
     all centred on x=512; a lockup can satisfy every "fits" rule above and
     still be visibly off-centre. */
  const mid = t => (t.left + t.right) / 2;
  const sub = m.text.find(t => t.id === 'sub');
  add('C9 the mark, the word and the subtitle share one vertical axis',
      Math.abs(mk.cx - AXIS) <= 0.5 &&
      !!title && Math.abs(mid(title) - AXIS) <= 2 &&
      !!sub && Math.abs(mid(sub) - AXIS) <= 2,
      `mark ${mk.cx}, word ${title ? mid(title).toFixed(2) : 'n/a'}, ` +
      `subtitle ${sub ? mid(sub).toFixed(2) : 'n/a'} (axis ${AXIS})`);

  /* C10 -- decorative layers: every layer declares its polarity and its filter
     agrees, and no layer is switched off.  The pixel half of this lesson lives
     in _tools/cover_layers.sh. */
  const art = d => d.art === 'white' || d.art === 'black' || d.art === 'gradient';
  const wrong = m.decor.filter(d =>
    d.art === 'white'    ?  /invert/.test(d.filter)
  : d.art === 'black'    ? !/invert/.test(d.filter)
  : d.art === 'gradient' ?  /invert/.test(d.filter)
  : true);
  const dark = m.decor.filter(d => d.opacity <= 0);
  const badD = [...wrong.map(d => `${d.id}: art ${d.art} but filter '${d.filter}'`),
                ...dark.map(d => `${d.id}: opacity ${d.opacity}`)];
  if (!m.decor.length) badD.push('no decorative layer declared -- the rule has no force');
  add('C10 every decorative layer declares its polarity, matches its filter and is on',
      badD.length === 0,
      badD.length ? badD.join('; ')
                  : `${m.decor.length} layers (${[...new Set(m.decor.map(d => d.art))].join('+')}), ` +
                    `every filter matches its art, no layer at opacity 0`);

  /* C11 -- the core is INSIDE the loop, at a size where it reads as a core.
     "Inside" alone is free on a mark with R=245; the band says the core is a
     sixth to a third of the loop's radius, which is what makes it a core
     rather than a speck or a second ring. */
  add('C11 the core sits inside the loop at a core-sized proportion',
      mk.coreR / mk.r >= 0.10 && mk.coreR / mk.r <= 0.30,
      `core r ${mk.coreR} is ${(mk.coreR / mk.r * 100).toFixed(1)}% of the loop radius ${mk.r}`);

  return out;
}

/* ---------- mutations ----------
 * A check that cannot go red is noise (CLAUDE.md 0.31), so the judge is run
 * against deliberately wrong reports.  Every mutation edits the REPORT, not the
 * page -- that is what makes it runnable without a browser.  Each one is a
 * failure this page can actually have; the two that matter most are C7/C8's
 * subject (an icon whose whole job is "it keeps going"), because a closed loop
 * and a reversed arrow both still look like a fine icon at 64px. */
function mutate(name, fn){ return {name, fn}; }
const MUTANTS = [
  mutate('the stage is letterboxed in a 1024 viewport',
         m => { m.stage.w = 512; m.stage.h = 512; return m; }),
  mutate('the word is empty',
         m => { m.text.find(t => t.id === 'title').text = ''; return m; }),
  mutate('the arrowhead is missing',
         m => { m.mark.head.len = 0; return m; }),
  mutate('the subtitle runs past the frame',
         m => { m.text.find(t => t.id === 'sub').right = W - 4; return m; }),
  mutate('the subtitle is dropped onto the word',
         m => { const s = m.text.find(t => t.id === 'sub'); s.top = 820; s.bottom = 846; return m; }),
  mutate('the word runs past the right frame edge',
         m => { m.text.find(t => t.id === 'title').right = W - 2; return m; }),
  /* This one is C4's WIDTH clause with nothing else wrong: still inside the
     frame (27..997 is inside 24..1000) and still centred (mid 512), so only the
     "fits with clearance" reading can catch it.  The height clause has its own
     mutant below -- a rule with two clauses gets two readings (DECISIONS_2 592). */
  mutate('the word outgrows the safe width while staying inside the frame',
         m => { const t = m.text.find(t => t.id === 'title'); t.left = 27; t.right = 997; return m; }),
  mutate('the word is too small to read at 1/5',
         m => { const t = m.text.find(t => t.id === 'title'); t.bottom = t.top + 70; return m; }),
  mutate('the mark is pushed out through the frame',
         m => { m.mark.bounds.right = W - 4; return m; }),
  mutate('the mark drifts down into the word',
         m => { m.mark.bounds.bottom += 60; return m; }),
  mutate('one corner of the loop is drawn off its own vertex',
         m => { m.mark.worstVertexPx = 3.2; return m; }),
  mutate('the gap closes, so the loop reads as a finished hexagon',
         m => { m.mark.gap = 4; m.mark.gapFrac = 0.016; return m; }),
  mutate('the arrowhead grows until it fills the gap',
         m => { m.mark.tipToStart = 2; return m; }),
  mutate('the arrowhead floats off the edge it belongs to',
         m => { m.mark.tipOffEdge = 18; return m; }),
  /* The loop's direction is read twice: once from which end is which (C7) and
     once from the head-vs-run dot (C8).  Each gets its own mutant so neither
     reading is riding on the other's teeth (DECISIONS_2 592). */
  mutate('the loop is drawn the other way round',
         m => { const s = m.mark.start, e = m.mark.end; m.mark.start = e; m.mark.end = s; return m; }),
  mutate('the arrowhead is flipped, so the loop runs backwards',
         m => { m.mark.head.dot = -1; return m; }),
  mutate('the arrowhead is too small to read',
         m => { m.mark.head.len = 12; m.mark.head.half = 8; return m; }),
  mutate('the word is off the axis',
         m => { const t = m.text.find(t => t.id === 'title'); t.left += 20; t.right += 20; return m; }),
  mutate('the mark is off the axis',
         m => { m.mark.cx = 520; return m; }),
  mutate('a decorative layer is switched off',
         m => { m.decor.find(d => d.id === 'vig').opacity = 0; return m; }),
  mutate('the gradient glow is inverted',
         m => { m.decor.find(d => d.id === 'glow').filter = 'invert(1)'; return m; }),
  mutate('a new decorative layer declares no polarity',
         m => { m.decor.push({id: 'grid2', opacity: 0.4, blend: 'screen', filter: '', art: null}); return m; }),
  mutate('the core grows out past the loop',
         m => { m.mark.coreR = 300; return m; }),
  mutate('the core shrinks to a speck',
         m => { m.mark.coreR = 10; return m; }),
];

/* ---------- main ---------- */
function report(file){
  const raw = fs.readFileSync(file, 'utf8');
  const a = raw.indexOf('{'), b = raw.lastIndexOf('}');
  if (a < 0 || b < 0) throw new Error('no JSON object in ' + file);
  return JSON.parse(raw.slice(a, b + 1));
}

function run(m, quiet){
  const res = judge(m);
  let bad = 0;
  for (const r of res){
    if (!r.ok) bad++;
    if (!quiet) console.log(`${r.ok ? 'ok  ' : 'FAIL'}  ${r.label}  [${r.detail}]`);
  }
  return {res, bad};
}

const argv = process.argv.slice(2);
if (argv.includes('--selftest')){
  const file = argv.find(a => !a.startsWith('--'));
  if (!file){ console.error('usage: continuation_judge.js --selftest <report.txt>'); process.exit(2); }
  const good = report(file);
  const base = run(good, true);
  let bad = 0;
  console.log(`baseline: ${base.res.length - base.bad} ok, ${base.bad} failed`);
  if (base.bad) { console.log('BASELINE IS RED -- fix the page first'); process.exit(1); }
  for (const mu of MUTANTS){
    const m = JSON.parse(JSON.stringify(good));
    const {res} = run(mu.fn(m), true);
    // The rule id is the whole token ("C10"), not its first two characters --
    // otherwise C10 and C1 cannot be told apart (cover_judge's Phase 133 note).
    const red = res.filter(r => !r.ok).map(r => r.label.split(' ')[0]);
    const uniq = [...new Set(red)];
    const ok = red.length >= 1;
    if (!ok) bad++;
    console.log(`${ok ? 'ok  ' : 'FAIL'}  mutant '${mu.name}' -> ${red.length} red [${uniq.join(',')}]`);
  }
  console.log(bad ? `${MUTANTS.length - bad} of ${MUTANTS.length} mutants lit a rule, ${bad} lit NOTHING`
                  : `${MUTANTS.length}/${MUTANTS.length} mutants each lit at least one rule`);
  process.exit(bad ? 1 : 0);
}

const file = argv.find(a => !a.startsWith('--'));
if (!file){ console.error('usage: continuation_judge.js <report.txt>   |   --selftest <report.txt>'); process.exit(2); }
const {res, bad} = run(report(file), false);
console.log(bad ? `${res.length - bad} ok, ${bad} FAILED` : `${res.length} ok, 0 failed`);
process.exit(bad ? 1 : 0);
