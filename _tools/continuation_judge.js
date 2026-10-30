/* continuation_judge.js -- the pass/fail half of the continuation icon's check.
 *
 * Same split as _tools/cover_judge.js and _tools/page_judge.js (DECISIONS_2 309):
 * the browser MEASURES (cover/continuation.html's layoutReport()), this file
 * DECIDES.  A file that measures and then decides what counts as correct tends
 * to quietly redefine correct, so the two stay apart -- and staying apart is
 * what lets --selftest feed this file a deliberately broken report with no
 * browser involved.
 *
 * WHAT THE PICTURE IS NOW (Phase 150 rework).  The operator said of the first
 * icon 「有点奇怪啊改一下，而且是trg的continuation，你TRG也要有一定体现」.  So
 * the hero is no longer a hexagon I drew: it is the game's own SMC mark
 * (intro/assets/sm-core.png, the same file the cover uses -- 引用不复制), and
 * the *only* thing the page changes about it is that the mark's outer ring is
 * cut open and the cut end carries an arrowhead.  The page clips the asset's
 * own ring away at r=240 asset px and draws a replacement ring at the asset's
 * own radius (249.5 asset px), so "the ring" and "the brand's ring" are the
 * same circle -- C6 is the rule that says so, and it is the rule that would go
 * red if someone moved the drawn ring a few pixels in or out.
 *
 * THE RULES THAT ARE THE POINT (C7/C8): the ring does not close, and the head
 * runs along it.  If the gap closes the mark is just a logo; if the head is
 * flipped the ring runs backwards; if the head is a big fat triangle whose base
 * is 5x the stroke it stops being the stroke's own tip and becomes a hat stuck
 * on the ring -- which is exactly what made the first version look odd.  All
 * three still look like a plausible icon at 64px, so all three are measured.
 *
 * THE ASSET NUMBERS USED BELOW ARE MEASURED, NOT ASSUMED.  Radial profile of
 * sm-core.png at 1440 angles, alpha >= 128:
 *     r 235 -> 9.5%   (the three arms' last real coverage)
 *     r 236 -> 3.3%   r 237..241 -> 0%      <- the empty band the clip lives in
 *     r 242 -> 12.4%  r 243..256 -> 100%    (the ring itself)
 *     r 257 -> 97.6%  r 258 -> 2.7%         (the ring's outer antialiased edge)
 * so: arms end at 236, ring inner edge at 242, ring centre 249.5, ring width
 * 15.2 -- all in ASSET pixels, scaled by S = EMBLEM_S / 515.
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
const SAFE = 6;
const AXIS = W / 2;                     // every centred thing lives on x=512
const MARK_CLEAR = 24;                  // the mark must breathe above the word

/* Asset geometry, in the asset's own pixels (see the header).  These are the
   independent evidence the drawn geometry is compared AGAINST -- they are not
   copied from the page's constants. */
const ASSET_PX      = 515;
const ASSET_RING_R  = 249.5;
const ASSET_ARM_END = 236;
const ASSET_RING_IN = 242;

function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});

  const mk = m.mark || {};
  const head = (mk.head || {});
  const em = (mk.emblem || {});
  const S = (em.w || 0) / ASSET_PX;       // asset px -> design px, read from the img box

  /* C0 -- the frame of reference.  Forgetting --w/--h letterboxes the stage and
     every coordinate below is in the wrong space; that is the realistic failure,
     not a made-up one. */
  add('C0 the design space is 1024x1024 and fills the viewport',
      m.stage.w === W && m.stage.h === H && m.innerW === W && m.innerH === H,
      `stage ${m.stage.w}x${m.stage.h}, viewport ${m.innerW}x${m.innerH}`);

  /* C1 -- non-vacuity, said before anything is judged.  Every rule below is
     of the form "this sits in the right place"; all of them are free on a page
     that drew nothing.  So name the four things the picture is made of. */
  const want = ['title', 'sub'];
  const missing = want.filter(id => {
    const t = m.text.find(x => x.id === id);
    return !t || !t.text;
  });
  add('C1 both words, the brand asset, the ring and the head are all present',
      missing.length === 0 &&
      typeof em.src === 'string' && em.src.length > 0 && em.w > 0 &&
      Number.isFinite(mk.r) && mk.gapDeg > 0 && mk.sweepDeg > 0 &&
      head.len > 0 && Array.isArray(head.tip),
      (missing.length ? `MISSING: ${missing.join(',')}` : 'CONTINUATION + THE REACTOR GAME present') +
      `; asset ${em.w}px, ring r ${mk.r}, gap ${mk.gapDeg}deg, head ${head.len}px`);

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

  /* C3 -- no two text blocks overlap, AND some pair was close enough to matter. */
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
     the one a reader actually gets. */
  const title = m.text.find(t => t.id === 'title');
  const tW = title ? title.right - title.left : NaN;
  const tH = title ? title.bottom - title.top : NaN;
  add('C4 the word fits the width and stays readable at 1/5',
      !!title && tW <= W - 2 * FRAME_IN - 16 && tH >= 80,
      title ? `width ${tW.toFixed(1)} of ${W - 2 * FRAME_IN - 16}, glyph height ${tH.toFixed(1)}px ` +
              `(${(tH / 5).toFixed(2)}px at 1/5)`
            : 'no title measured');

  /* C5 -- the mark is inside the frame AND clears the word under it. */
  const b = mk.bounds || {};
  const clear = (b.bottom !== undefined && title) ? title.top - b.bottom : NaN;
  add('C5 the mark is inside the frame and clear of the word',
      b.left  > FRAME_IN + SAFE && b.right  < W - FRAME_IN - SAFE &&
      b.top   > FRAME_IN + SAFE && b.bottom < H - FRAME_IN - SAFE &&
      clear >= MARK_CLEAR,
      `mark x[${b.left}..${b.right}] y[${b.top}..${b.bottom}], ` +
      `${Number.isFinite(clear) ? clear.toFixed(1) : 'n/a'}px above the word (needs ${MARK_CLEAR})`);

  /* C6 -- THE DRAWN RING IS THE BRAND'S RING.  Two clauses, two readings:
       (a) circle-ness: the path is sampled at nine points and every radius
           agrees.  A path built from the wrong control points bulges or kinks
           and still looks like an arc at 64px;
       (b) the radius is the asset's ring radius, computed from the img box that
           the browser reported.  This is the claim the page makes in its own
           comment -- "和印出来的那圈同一个半径" -- and (a) cannot see it,
           because a ring drawn at the wrong radius is a perfectly good circle.
     A rule with two clauses gets two mutants (DECISIONS_2 592). */
  const R_want = ASSET_RING_R * S;
  add('C6 the drawn ring is a circle at the brand ring\'s own radius',
      (mk.rMax - mk.rMin) <= 0.5 &&
      Math.abs(mk.r - R_want) <= 2.0,
      `radius spread ${(mk.rMax - mk.rMin).toFixed(3)}px over 9 samples; ` +
      `drawn r ${mk.r} vs the asset's ${R_want.toFixed(2)} (off ${Math.abs(mk.r - R_want).toFixed(2)}, allowed 2.0)`);

  /* C7 -- THE RING IS OPEN.  Bounded on both sides: a gap that closes reads as a
     finished logo, and a gap that swallows half the ring reads as a broken
     shape.  The arrowhead may not fill the gap either -- that is why the reading
     is tip-to-start, and why it is also expressed as a FRACTION of the gap: an
     absolute number would pass a tiny gap and a huge head at the same time. */
  const openFrac = mk.tipToStart / mk.gap;
  add('C7 the ring is open: a bounded gap the head does not fill',
      mk.gapDeg >= 30 && mk.gapDeg <= 90 &&
      mk.sweepDeg >= 270 && mk.sweepDeg <= 330 &&
      mk.tipToStart >= 40 && openFrac <= 0.85,
      `gap ${mk.gapDeg}deg (sweep ${mk.sweepDeg}deg, chord ${mk.gap}px), ` +
      `tip-to-start ${mk.tipToStart}px = ${(openFrac * 100).toFixed(1)}% of the gap (max 85%)`);

  /* C8 -- THE HEAD IS THE RING'S OWN TIP.  Four claims:
       - it runs with the ring (dot), not against it;
       - its BASE sits on the ring, so it is not a floating triangle (this is the
         reading that would have caught the version the operator called 有点奇怪:
         its base was 68px wide -- five times the stroke -- and it read as a hat);
       - its size is a stroke-tip, not a blob and not a speck;
       - its TIP is exactly where a tangential head of that length puts it:
         R' = sqrt(r^2 + len^2).  That last one is a third spelling of the same
         triangle, computed from two independent readings (the sampled radius and
         the polygon's own points), which is what makes it able to disagree. */
  const tipWant = Math.sqrt(mk.r * mk.r + head.len * head.len) - mk.r;
  add('C8 the head is the ring\'s own tip: on the ring, along it, right size',
      head.dot > 0.99 &&
      mk.baseOffRing <= 0.5 &&
      head.len >= 40 && head.len <= 100 &&
      head.half >= 9  && head.half <= 30 &&
      Math.abs(mk.tipOffRing - tipWant) <= 0.5,
      `head ${head.len} x ${head.half * 2}px (stroke ${mk.ringW}), dot ${head.dot}; ` +
      `base off the ring ${mk.baseOffRing}px; tip off the ring ${mk.tipOffRing} ` +
      `(a tangential ${head.len}px head must be ${tipWant.toFixed(2)}, allowed 0.5)`);

  /* C9 -- one vertical axis. */
  const mid = t => (t.left + t.right) / 2;
  const sub = m.text.find(t => t.id === 'sub');
  add('C9 the mark, the word and the subtitle share one vertical axis',
      Math.abs(mk.cx - AXIS) <= 0.5 &&
      Math.abs((em.left + em.w / 2) - AXIS) <= 0.5 &&
      !!title && Math.abs(mid(title) - AXIS) <= 2 &&
      !!sub && Math.abs(mid(sub) - AXIS) <= 2,
      `mark ${mk.cx}, asset ${Number.isFinite(em.left) ? (em.left + em.w / 2).toFixed(2) : 'n/a'}, ` +
      `word ${title ? mid(title).toFixed(2) : 'n/a'}, ` +
      `subtitle ${sub ? mid(sub).toFixed(2) : 'n/a'} (axis ${AXIS})`);

  /* C10 -- decorative layers: every layer declares its polarity and its filter
     agrees, and no layer is switched off.  The pixel half of this lesson lives
     in _tools/cover_layers.sh. */
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

  /* C11 -- THE HERO IS THE BRAND'S OWN FILE, AND THE CLIP ONLY TAKES THE RING.
     This is the operator's half of the request ("你TRG也要有一定体现"): the mark
     is intro/assets/sm-core.png, the same file the cover uses -- not redrawn,
     not traced, not "close enough".  The clip is the one pixel operation done to
     it, and it has to land in the empty annulus between the arms' ends (236) and
     the ring's inner edge (242): smaller and it chops the arms' tips off flat,
     larger and a sliver of the asset's own ring survives beside the drawn one.
     Both failures are one or two pixels and neither one looks wrong at 64px. */
  const clipLo = ASSET_ARM_END * S, clipHi = ASSET_RING_IN * S;
  add('C11 the hero is the brand asset, cropped only where the asset is empty',
      /sm-core\.png$/.test(String(em.src)) &&
      Math.abs(em.w - em.h) <= 0.5 &&
      Math.abs((em.top + em.h / 2) - mk.cy) <= 0.5 &&
      em.opacity > 0 && em.opacity <= 1 &&
      em.clip > clipLo && em.clip < clipHi,
      `${em.src} ${em.w}x${em.h} at opacity ${em.opacity}, ` +
      `clip r ${em.clip} inside the empty band ${clipLo.toFixed(1)}..${clipHi.toFixed(1)}`);

  return out;
}

/* ---------- mutations ----------
 * A check that cannot go red is noise (CLAUDE.md 0.31), so the judge is run
 * against deliberately wrong reports.  Every mutation edits the REPORT, not the
 * page -- that is what makes it runnable without a browser.  Each one is a
 * failure this page can actually have.
 *
 * Three rules carry two readings each and so get two mutants apiece
 * (DECISIONS_2 592): C6 (circle-ness vs radius), C7 (the gap's size vs the head
 * filling it), C8 (tangential vs on-the-ring).  A mutant is only allowed in if
 * the picture it produces would still look like a fine icon at 64px. */
function mutate(name, fn){ return {name, fn}; }
const MUTANTS = [
  /* C0/C1 -- the frame of reference, and "something was drawn at all" */
  mutate('the stage is letterboxed in a 1024 viewport',
         m => { m.stage.w = 512; m.stage.h = 512; return m; }),
  mutate('the word is empty',
         m => { m.text.find(t => t.id === 'title').text = ''; return m; }),
  mutate('the brand asset never loaded',
         m => { m.mark.emblem.src = ''; m.mark.emblem.w = 0; return m; }),
  /* C2/C3 -- type inside the frame, type not on type */
  mutate('the subtitle runs past the frame',
         m => { m.text.find(t => t.id === 'sub').right = W - 4; return m; }),
  mutate('the subtitle is dropped onto the word',
         m => { const s = m.text.find(t => t.id === 'sub'); s.top = 820; s.bottom = 846; return m; }),
  /* C4 -- the word's width and its height, each on its own (DECISIONS_2 592) */
  mutate('the word runs past the right frame edge',
         m => { m.text.find(t => t.id === 'title').right = W - 2; return m; }),
  mutate('the word outgrows the safe width while staying inside the frame',
         m => { const t = m.text.find(t => t.id === 'title'); t.left = 27; t.right = 997; return m; }),
  mutate('the word is too small to read at 1/5',
         m => { const t = m.text.find(t => t.id === 'title'); t.bottom = t.top + 70; return m; }),
  /* C5 -- the mark vs the frame and vs the word */
  mutate('the mark is pushed out through the frame',
         m => { m.mark.bounds.right = W - 4; return m; }),
  mutate('the mark drifts down into the word',
         m => { m.mark.bounds.bottom += 60; return m; }),
  /* C6 -- two clauses: is it a circle, and is it the brand ring's circle */
  mutate('the drawn ring is no longer a circle',
         m => { m.mark.rMax = m.mark.r + 6; return m; }),
  mutate('the drawn ring sits at the wrong radius',
         m => { m.mark.r += 40; m.mark.rMin += 40; m.mark.rMax += 40; return m; }),
  /* C7 -- two clauses: the gap's size, and the head not filling it */
  mutate('the gap closes, so the mark is just a logo again',
         m => { m.mark.gapDeg = 4; m.mark.sweepDeg = 356; return m; }),
  mutate('the gap swallows half the ring',
         m => { m.mark.gapDeg = 200; m.mark.sweepDeg = 160; return m; }),
  mutate('the head grows until it fills the gap',
         m => { m.mark.tipToStart = 6; return m; }),
  /* C8 -- four clauses, the two quiet ones get their own mutants */
  mutate('the head floats off the ring it is supposed to end',
         m => { m.mark.baseOffRing = 14; return m; }),
  mutate('the head is flipped, so the ring runs backwards',
         m => { m.mark.head.dot = -1; return m; }),
  mutate('the head is a speck',
         m => { m.mark.head.len = 12; m.mark.head.half = 5; return m; }),
  mutate('the head is a fat blob five times the stroke',
         m => { m.mark.head.half = 60; return m; }),
  mutate('the head is not where a tangential head of that length goes',
         m => { m.mark.tipOffRing = m.mark.tipOffRing + 12; return m; }),
  /* C9 -- one axis */
  mutate('the word is off the axis',
         m => { const t = m.text.find(t => t.id === 'title'); t.left += 20; t.right += 20; return m; }),
  mutate('the mark is off the axis',
         m => { m.mark.cx = 520; return m; }),
  mutate('the asset is off the mark\'s centre',
         m => { m.mark.emblem.left += 20; return m; }),
  /* C10 -- decorative layers */
  mutate('a decorative layer is switched off',
         m => { m.decor.find(d => d.id === 'vig').opacity = 0; return m; }),
  mutate('the gradient glow is inverted',
         m => { m.decor.find(d => d.id === 'glow').filter = 'invert(1)'; return m; }),
  mutate('a new decorative layer declares no polarity',
         m => { m.decor.push({id: 'grid2', opacity: 0.4, blend: 'screen', filter: '', art: null}); return m; }),
  /* C11 -- the hero.  Three clauses, three mutants: it is the brand file, the
     clip only takes empty pixels, and it is actually on. */
  mutate('the hero is some other file',
         m => { m.mark.emblem.src = '../intro/assets/other.png'; return m; }),
  mutate('the clip is too small, so it chops the arms\' tips off flat',
         m => { m.mark.emblem.clip = 200; return m; }),
  mutate('the clip is too large, so a sliver of the asset\'s own ring survives',
         m => { m.mark.emblem.clip = 248; return m; }),
  mutate('the hero is squeezed instead of square',
         m => { m.mark.emblem.h = 460; return m; }),
  mutate('the hero is faded out',
         m => { m.mark.emblem.opacity = 0; return m; }),
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
