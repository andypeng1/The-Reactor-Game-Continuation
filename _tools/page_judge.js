/* page_judge.js -- the pass/fail half of the 16:9 game-page image's layout check.
 *
 * Same split as _tools/cover_judge.js (DECISIONS_2 309): the browser measures
 * (cover/page.html's layoutReport()), this file decides what counts as correct.
 * A file that measures and then decides tends to quietly redefine correct.
 *
 * WHY A SECOND JUDGE INSTEAD OF A FLAG ON THE FIRST.  cover_judge's rules are
 * written against a 1080x1080 space and a VERTICAL lockup -- the hexagon is
 * bounded above by the frame and below by the title.  In the 16:9 page the
 * hexagon and the type sit SIDE BY SIDE, so the bounding neighbours are
 * different objects and the columns share a horizontal axis instead of a
 * vertical one.  Reusing A5/A10 with swapped names would have been a rule that
 * looks the same and measures something else (CLAUDE.md 0.18: a word that makes
 * the choice for you is not a measurement).
 *
 * WHAT IS SHARED, VERBATIM: the empty-set guard (W1 names the four objects
 * instead of counting), the near-miss half of the collision rule (W3 reports
 * the closest miss, so "nothing collided" cannot pass because nothing was
 * close), the two-hexagons-are-one-shape rule (W6/W7), the asset-polarity rule
 * (W8) and the mark-inside-the-hexagon rule (W9).
 *
 * Usage:
 *   node _tools/intro_render.js --page cover/page.html --at 0 --w 1920 --h 1080 \
 *        --eval 'layoutReport()' > report.txt
 *   node _tools/page_judge.js report.txt
 *   node _tools/page_judge.js --selftest report.txt
 */
'use strict';

const fs = require('fs');

const W = 1920, H = 1080;
const FRAME_IN = 26;                    // the frame's inset, from cover/page.html
const INNER_W = W - 2 * FRAME_IN;       // 1868
const SAFE = 6;                         // px of clearance the rules ask for
const COS30 = Math.cos(Math.PI / 6);
const TEXT_LEFT_MIN = 1030;             // the type column's left edge (design value)

/* ---------- the rules ---------- */
function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});

  /* W0 -- the frame of reference.  If the stage is not 1920x1080 the renderer is
     letterboxing and every coordinate below is in the wrong space.  This is the
     realistic failure here, not a made-up one: pass --w 1080 --h 1080 to the
     renderer and the page's own stage gets scaled down inside a square viewport. */
  add('W0 the design space is 1920x1080 and fills the viewport',
      m.stage.w === W && m.stage.h === H && m.innerW === W && m.innerH === H,
      `stage ${m.stage.w}x${m.stage.h}, viewport ${m.innerW}x${m.innerH}`);

  /* W1 -- non-vacuity, said before anything is judged.  Every rule below is
     "nothing collides" / "nothing is outside", and both are free on a page that
     drew nothing.  So this names the four objects and asks that the two drawn
     things have real size. */
  const want = ['title', 'badge', 'footL', 'footR'];
  const missing = want.filter(id => { const t = m.text.find(x => x.id === id); return !t || !t.text; });
  const hexW = m.hex.right - m.hex.left;
  add('W1 the four things this page is made of are present and have size',
      missing.length === 0 && hexW > 100 && m.mark.w > 100,
      (missing.length ? `MISSING: ${missing.join(',')}` : 'title + badge + both footer lines present') +
      `; hexagon ${hexW.toFixed(0)}px wide, mark ${m.mark.w.toFixed(0)}px`);

  /* W2 -- every text block is inside the frame.  Roblox re-crops this image into
     several slots; a footer under the frame edge is a footer that gets cut. */
  const outside = m.text.filter(t =>
    t.left < FRAME_IN + 4 || t.right > W - FRAME_IN - 4 ||
    t.top  < FRAME_IN + 4 || t.bottom > H - FRAME_IN - 4);
  add('W2 every text block is inside the frame',
      outside.length === 0,
      outside.length ? outside.map(t => `${t.id} [${t.left}..${t.right}]x[${t.top}..${t.bottom}]`).join('; ')
                     : `${m.text.length} blocks inside [${FRAME_IN + 4}..${W - FRAME_IN - 4}] x [${FRAME_IN + 4}..${H - FRAME_IN - 4}]`);

  /* W3 -- no two text blocks overlap, AND some pair was close enough to matter.
     Both halves matter: 0 colliding is free on a page whose blocks are far
     apart; minGap is the near-miss report that says the rule had something to
     prevent.  The badge and the headline are 17 px apart by their font boxes,
     so this rule is load-bearing rather than decorative. */
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
  add('W3 no two text blocks collide',
      pairs === 0 && minGap < 40,
      pairs ? `${worst.a} over ${worst.b} by ${worst.oy.toFixed(2)}px (${worst.area.toFixed(0)}px2)`
            : (minGap === Infinity
                 ? 'NO TWO BLOCKS SHARE A COLUMN -- this test has no force'
                 : `0 colliding; closest vertical miss ${minGap.toFixed(2)}px`));

  /* W4 -- the headline.  Four claims in one: both lines were measured (an
     empty titleLines array must not pass "every line fits"), every line is
     inside the right frame edge, the line ADVANCE is big enough to survive the
     thumbnail downscale, and the lockup clears the rule beneath it.
     The advance, not the font size, is what the reader gets: at 1/5 (Roblox's
     card size) 110.19px of advance is 22px, and that is the number printed. */
  const title = m.text.find(t => t.id === 'title');
  const lines = m.titleLines || [];
  const lineRight = lines.length ? Math.max(...lines.map(l => l.right)) : NaN;
  const advance = lines.length === 2 ? lines[1].top - lines[0].top : NaN;
  add('W4 the headline is two measured lines, fits, and clears the rule under it',
      !!title && lines.length === 2 &&
      lineRight < W - FRAME_IN - 4 &&
      advance >= 100 &&
      title.bottom < m.rule.top - 8,
      title ? `lines ${lines.length}, widest right ${lineRight.toFixed(1)} (limit ${W - FRAME_IN - 4}), ` +
              `advance ${Number.isNaN(advance) ? 'n/a' : advance.toFixed(2)}px ` +
              `(${(advance / 5).toFixed(2)}px at 1/5), bottom ${title.bottom} vs rule ${m.rule.top}`
            : 'no title measured');

  /* W5 -- the two columns do not touch: the hexagon is to the LEFT of every
     piece of the type lockup (badge, headline, rule) with clearance, and the
     hexagon is inside the frame.  This is the 16:9 form of cover's A5: there
     the hexagon was bounded above/below, here it is bounded sideways. */
  const colLeft = Math.min(...m.text.filter(t => t.id !== 'footL' && t.id !== 'footR')
                                   .map(t => t.left), m.rule.left);
  add('W5 the hero hexagon sits left of the type column with clearance, inside the frame',
      m.hex.right + SAFE < colLeft &&
      m.hex.top > FRAME_IN + SAFE && m.hex.bottom < H - FRAME_IN - SAFE &&
      m.hex.left > FRAME_IN + SAFE,
      `hex x[${m.hex.left}..${m.hex.right}] y[${m.hex.top}..${m.hex.bottom}]; ` +
      `type column starts at ${colLeft.toFixed(1)} (needs > ${(m.hex.right + SAFE).toFixed(1)})`);

  /* W6/W7 -- the two hexagons are the same shape (same argument as cover's
     A6/A7: the panel is clipped by a CSS percentage polygon, the frame is an
     SVG polygon computed from HEX_R; if the box is not 2*cos30 : 2 they are two
     different hexagons and both still look like hexagons). */
  add('W6 the hero panel box has the pointy-top hexagon proportion',
      Math.abs(m.hex.ratio - m.hex.want) < 0.01,
      `height/width ${m.hex.ratio}, want ${m.hex.want} (2/(2cos30))`);
  add('W7 the CSS clip and the SVG frame are the same hexagon',
      m.hex.worstVertexPx < 0.5,
      `worst vertex ${m.hex.worstVertexPx}px apart (vertex #${m.hex.worstAt})`);

  /* W8 -- decorative layers: the declaration of asset polarity must match the
     filter, and no layer may be switched off.  Phase 132 found two layers at
     exactly zero and two at 1%-14% amplitude with every other rule green; the
     pixel half of that lesson lives in _tools/cover_layers.sh, this is the
     style half. */
  const asset = m.decor.filter(d => d.art === 'white' || d.art === 'black');
  const wrongFilter = m.decor.filter(d =>
    d.art === 'white'    ?  /invert/.test(d.filter)
  : d.art === 'black'    ? !/invert/.test(d.filter)
  : d.art === 'gradient' ?  /invert/.test(d.filter)
  : true);
  const dark = m.decor.filter(d => d.opacity <= 0);
  const badD = [...wrongFilter.map(d => `${d.id}: art ${d.art} but filter '${d.filter}'`),
                ...dark.map(d => `${d.id}: opacity ${d.opacity}`)];
  if (!asset.length) badD.push(`no layer declares an ASSET polarity (${m.decor.length} declared) -- the rule has no force`);
  add('W8 every decorative layer declares its asset polarity and its filter matches it',
      badD.length === 0,
      badD.length ? badD.join('; ')
                  : `${m.decor.length} layers (${[...new Set(m.decor.map(d => d.art))].join('+')}), every invert matches its art`);

  /* W9 -- the manufacturer mark must stay inside the hexagon it is drawn in.
     The mark is a separate element that is NOT clipped, so growing past the
     hexagon does not raise anything: it just draws a line across another line. */
  const hcx = (m.hex.left + m.hex.right) / 2, hcy = (m.hex.top + m.hex.bottom) / 2;
  const R = (m.hex.bottom - m.hex.top) / 2;
  const verts = [];
  for (let i = 0; i < 6; i++){
    const a = (-90 + 60 * i) * Math.PI / 180;
    verts.push([hcx + R * Math.cos(a), hcy + R * Math.sin(a)]);
  }
  let minSlack = Infinity, worstEdge = null;
  for (let i = 0; i < 6; i++){
    const p = verts[i], q = verts[(i + 1) % 6];
    const ex = q[0] - p[0], ey = q[1] - p[1], len = Math.hypot(ex, ey);
    const cross = pt => ((pt[0] - p[0]) * ey - (pt[1] - p[1]) * ex) / len;
    const sign = cross([hcx, hcy]) >= 0 ? 1 : -1;
    const slack = sign * cross([m.mark.cx, m.mark.cy]) - m.mark.w / 2;
    if (slack < minSlack){ minSlack = slack; worstEdge = i; }
  }
  add('W9 the hero mark stays inside the hexagon it is drawn in',
      minSlack >= 8,
      `mark r=${(m.mark.w / 2).toFixed(1)} at (${m.mark.cx},${m.mark.cy}) in a hexagon of R=${R}: ` +
      `tightest of the six edges (#${worstEdge}) leaves ${minSlack.toFixed(1)}px`);

  /* W10 -- the two columns share one optical midline, and the rule is the
     headline's tail rather than a third floating object.  Both numbers were
     chosen as invariants, not as observations: the hexagon's centre is the
     stage's centre, and the rule sits 20..90 px under the headline.  A page
     whose lockup drifts (badge up, headline down) still passes every "fits"
     rule above; this is the rule that notices the drift. */
  const hexCy = (m.hex.top + m.hex.bottom) / 2;
  const tail = m.rule.top - title.bottom;
  add('W10 the hexagon is vertically centred and the rule is the headline\'s tail',
      Math.abs(hexCy - H / 2) <= 8 && tail >= 20 && tail <= 90,
      `hex centre y=${hexCy.toFixed(1)} (stage ${H / 2}, off by ${(hexCy - H / 2).toFixed(1)}); ` +
      `rule ${tail.toFixed(1)}px under the headline (want 20..90)`);

  return out;
}

/* ---------- mutations ----------
 * A check that cannot go red is noise (CLAUDE.md 0.31), so the judge is run
 * against deliberately wrong reports and each mutation must light a rule.
 * The mutations edit the REPORT, not the page -- which is what makes them
 * runnable without a browser and what the measure/judge split buys.
 * Each mutation is a failure this page can actually have: the letterbox one is
 * what forgetting --w/--h produces, and the rest are the realistic edits
 * (someone moves the badge, someone lets the title grow, someone switches the
 * mark's art polarity). */
function mutate(name, fn){ return {name, fn}; }
const MUTANTS = [
  mutate('stage letterboxed in a 1080x1080 viewport', m => { m.innerW = 1080; m.innerH = 1080; return m; }),
  mutate('the headline is empty', m => {
    m.text.find(t => t.id === 'title').text = ''; return m; }),
  mutate('the AIREMAKE badge is missing', m => {
    m.text.find(t => t.id === 'badge').text = ''; return m; }),
  mutate('the footer runs past the frame', m => {
    const f = m.text.find(t => t.id === 'footR'); f.right = W; return m; }),
  mutate('the badge is dropped onto the headline', m => {
    const b = m.text.find(t => t.id === 'badge'); b.top = 470; b.bottom = 492; return m; }),
  mutate('a text block runs past the right frame edge', m => {
    m.text.find(t => t.id === 'title').right = W - FRAME_IN; return m; }),
  /* 这一条只动**行盒子**、不动那个 union 盒子 —— 这样它打到的只能是 W4 自己
     的"每一行都在框内"，而不是 W2 那条"文字块在框内"。同一条缺陷写两个读数时，
     要给每一条各一个单独的突变，否则其中一条的牙从没被证明过（DECISIONS_2 592）。 */
  mutate('only the first headline line grows past the right frame edge', m => {
    m.titleLines[0].right = W - 20; return m; }),
  mutate('the two headline lines are squashed together', m => {
    m.titleLines[1].top = m.titleLines[0].top + 60; return m; }),
  mutate('the badge is moved left over the hexagon', m => {
    const b = m.text.find(t => t.id === 'badge'); b.left = 900; b.right = 1028; return m; }),
  mutate('hero panel box is not a hexagon proportion', m => { m.hex.ratio = 1.0; return m; }),
  mutate('SVG frame drawn at the wrong radius', m => { m.hex.worstVertexPx = 9.4; return m; }),
  mutate('the hero mark grows out through the hexagon outline',
         m => { m.mark.w = 600; m.mark.h = 600; return m; }),
  mutate('the white manufacturer mark is inverted, so it goes black',
         m => { m.decor.find(d => d.id === 'coreMark').filter = 'invert(1)'; return m; }),
  mutate('a decorative layer is switched off with opacity 0',
         m => { m.decor.find(d => d.id === 'vig').opacity = 0; return m; }),
  mutate('a new decorative layer does not declare its asset polarity',
         m => { m.decor.push({id: 'grid2', opacity: 0.4, blend: 'screen', filter: '', art: null}); return m; }),
  mutate('the hexagon is pushed down off the optical midline',
         m => { m.hex.top += 40; m.hex.bottom += 40; return m; }),
  mutate('the rule is lifted until it touches the headline',
         m => { m.rule.top = 675; return m; }),
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
  if (!file){ console.error('usage: page_judge.js --selftest <report.txt>'); process.exit(2); }
  const good = report(file);
  const base = run(good, true);
  let bad = 0;
  console.log(`baseline: ${base.res.length - base.bad} ok, ${base.bad} failed`);
  if (base.bad) { console.log('BASELINE IS RED -- fix the page first'); process.exit(1); }
  for (const mu of MUTANTS){
    const m = JSON.parse(JSON.stringify(good));
    const {res} = run(mu.fn(m), true);
    // 规则号取整个词（"W10"），不是前两个字符 —— 后者会把 W10 打成 "W1"，
    // 分不开"打到 W1"和"打到 W10"（cover_judge 的 Phase 133 实测）。
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
if (!file){ console.error('usage: page_judge.js <report.txt>   |   --selftest <report.txt>'); process.exit(2); }
const {res, bad} = run(report(file), false);
console.log(bad ? `${res.length - bad} ok, ${bad} FAILED` : `${res.length} ok, 0 failed`);
process.exit(bad ? 1 : 0);
