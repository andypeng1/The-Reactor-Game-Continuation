/* rebuild_judge.js -- the pass/fail half of the Rebuild icon's check.
 *
 * Same split as _tools/continuation_judge.js and _tools/cover_judge.js
 * (DECISIONS_2 309): the browser MEASURES (cover/rebuild.html's layoutReport()),
 * this file DECIDES.  A file that measures and then decides what counts as
 * correct tends to quietly redefine correct, so the two stay apart -- and
 * staying apart is what lets --selftest feed this file a deliberately broken
 * report with no browser involved.
 *
 * WHAT THE PICTURE IS.  Same language as the Continuation icon (Phase 149/150):
 * frame, the game's own SMC mark (intro/assets/sm-core.png), a ring drawn at the
 * mark's own radius, one word.  What the ring SAYS is different:
 *     continuation = the ring is cut open and the cut end grows an arrowhead
 *                    -- it is still going;
 *     rebuild      = the ring is missing one bay, and THAT BAY is being carried
 *                    back in: the same arc, same width, same radius, lifted 54px
 *                    out along the bay's mid-radius, in amber, with a guide line
 *                    running from the ring's outer edge to the part's inner edge.
 *
 * THE RULES THAT ARE THE POINT (R8/R9/R10), all three of which look like a
 * perfectly fine icon at 64px:
 *     R8  the part is the SAME arc as the hole -- if it is narrower or wider it
 *         stops being "the missing piece" and becomes decoration;
 *     R9  the part really is LIFTED -- seated in its slot it closes the ring and
 *         the icon becomes a plain badge, with "rebuild" gone entirely;
 *     R10 the part is aimed at its hole and the guide is on that same axis --
 *         a part hovering beside the hole reads as debris.
 *
 * THE ASSET NUMBERS USED BELOW ARE MEASURED, NOT ASSUMED.  Radial profile of
 * sm-core.png at 1440 angles, alpha >= 128:
 *     r 235 -> 9.5%   (the three arms' last real coverage)
 *     r 236 -> 3.3%   r 237..241 -> 0%      <- the empty band the clip lives in
 *     r 242 -> 12.4%  r 243..256 -> 100%    (the ring itself)
 *     r 257 -> 97.6%  r 258 -> 2.7%         (the ring's outer antialiased edge)
 * so: arms end at 236, ring inner edge at 242, ring centre 249.5, ring width
 * 15.2 -- all in ASSET pixels, scaled by S = EMBLEM_S / 515, which is read back
 * from the img box the browser reported.
 *
 * THE PIXELS ARE A SEPARATE WITNESS.  _tools/rebuild_pieces_check.py holds no
 * radius constant: it measures the ring in the ASSET and the ring in the
 * DELIVERED PNG and compares them, then finds the one empty bay and the one
 * blob outside the ring and checks they are the same width.  R8/R9/R10 above
 * are readings of the SVG paths; that file is a reading of the ink.
 *
 * Usage:
 *   node _tools/intro_render.js --page cover/rebuild.html --at 0 --w 1024 --h 1024 \
 *        --eval 'layoutReport()' > report.txt
 *   node _tools/rebuild_judge.js report.txt
 *   node _tools/rebuild_judge.js --selftest report.txt
 */
'use strict';

const fs = require('fs');

const W = 1024, H = 1024;
const FRAME_IN = 20;                    // #frame's inset, from cover/rebuild.html
const SAFE = 6;
const AXIS = W / 2;                     // every centred thing lives on x=512
const MARK_CLEAR = 24;                  // the mark must breathe above the word

/* Asset geometry, in the asset's own pixels (see the header).  Independent
   evidence the drawn geometry is compared AGAINST -- not copied from the page. */
const ASSET_PX      = 515;
const ASSET_RING_R  = 249.5;
const ASSET_ARM_END = 236;
const ASSET_RING_IN = 242;

/* The two design tokens, quoted from src/ReactorBackend/Config.luau
   (Config.Visual.Ready / Config.Visual.Amber) -- the same source cover/index.html
   takes its colours from.  The pixel instrument measures the amber's HUE with no
   literal at all, so this pair is not the only witness (DECISIONS_2 655). */
const TOKEN_READY = 'rgb(235, 235, 235)';
const TOKEN_AMBER = 'rgb(255, 128, 1)';

const ang = d => ((d % 360) + 360) % 360;
const angDiff = (a, b) => { const d = Math.abs(ang(a - b)); return d > 180 ? 360 - d : d; };

function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});

  const mk = m.mark || {};
  const ring = (mk.ring || {});
  const piece = (mk.piece || {});
  const guide = (mk.guide || {});
  const em = (mk.emblem || {});
  const S = (em.w || 0) / ASSET_PX;       // asset px -> design px, read from the img box

  /* R0 -- the frame of reference.  Forgetting --w/--h letterboxes the stage and
     every coordinate below is in the wrong space. */
  add('R0 the design space is 1024x1024 and fills the viewport',
      m.stage.w === W && m.stage.h === H && m.innerW === W && m.innerH === H,
      `stage ${m.stage.w}x${m.stage.h}, viewport ${m.innerW}x${m.innerH}`);

  /* R1 -- non-vacuity, said before anything is judged.  Every rule below has the
     form "this sits in the right place", and all of them are free on a page that
     drew nothing. */
  const want = ['title', 'sub'];
  const missing = want.filter(id => {
    const t = m.text.find(x => x.id === id);
    return !t || !t.text;
  });
  add('R1 both words, the brand asset, the ring, the part and the guide are present',
      missing.length === 0 &&
      typeof em.src === 'string' && em.src.length > 0 && em.w > 0 &&
      ring.len > 0 && piece.len > 0 && guide.len > 0,
      (missing.length ? `MISSING: ${missing.join(',')}` : 'REBUILD + THE REACTOR GAME present') +
      `; asset ${em.w}px, ring ${ring.len}px, part ${piece.len}px, guide ${guide.len}px`);

  /* R2 -- every text block is inside the frame.  Roblox re-crops this image. */
  const outside = m.text.filter(t =>
    t.left < FRAME_IN + 4 || t.right > W - FRAME_IN - 4 ||
    t.top  < FRAME_IN + 4 || t.bottom > H - FRAME_IN - 4);
  add('R2 every text block is inside the frame',
      outside.length === 0,
      outside.length ? outside.map(t => `${t.id} [${t.left}..${t.right}]x[${t.top}..${t.bottom}]`).join('; ')
                     : `${m.text.length} blocks inside [${FRAME_IN + 4}..${W - FRAME_IN - 4}]`);

  /* R3 -- no two text blocks overlap, AND some pair was close enough to matter. */
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
  add('R3 no two text blocks collide, and the nearest pair really is close',
      pairs === 0 && minGap < 40,
      pairs ? `${worst.a} over ${worst.b} by ${worst.oy.toFixed(2)}px (${worst.area.toFixed(0)}px2)`
            : (minGap === Infinity
                 ? 'NO TWO BLOCKS SHARE A COLUMN -- this test has no force'
                 : `0 colliding; closest vertical miss ${minGap.toFixed(2)}px`));

  /* R4 -- the word: fits the inner width, survives 1/5, and the height printed is
     the one a reader gets. */
  const title = m.text.find(t => t.id === 'title');
  const tW = title ? title.right - title.left : NaN;
  const tH = title ? title.bottom - title.top : NaN;
  add('R4 the word fits the width and stays readable at 1/5',
      !!title && tW <= W - 2 * FRAME_IN - 16 && tH >= 80,
      title ? `width ${tW.toFixed(1)} of ${W - 2 * FRAME_IN - 16}, glyph height ${tH.toFixed(1)}px ` +
              `(${(tH / 5).toFixed(2)}px at 1/5)`
            : 'no title measured');

  /* R5 -- everything drawn is inside the frame AND clears the word under it. */
  const b = mk.bounds || {};
  const clear = (b.bottom !== undefined && title) ? title.top - b.bottom : NaN;
  add('R5 the mark is inside the frame and clear of the word',
      b.left  > FRAME_IN + SAFE && b.right  < W - FRAME_IN - SAFE &&
      b.top   > FRAME_IN + SAFE && b.bottom < H - FRAME_IN - SAFE &&
      clear >= MARK_CLEAR,
      `mark x[${b.left}..${b.right}] y[${b.top}..${b.bottom}], ` +
      `${Number.isFinite(clear) ? clear.toFixed(1) : 'n/a'}px above the word (needs ${MARK_CLEAR})`);

  /* R6 -- THE DRAWN RING IS THE BRAND'S RING.  Two clauses, two readings:
       (a) circle-ness: nine sampled points, every radius agrees.  A path built
           from the wrong control points bulges or kinks and still looks like an
           arc at 64px;
       (b) the radius is the asset's ring radius, computed from the img box the
           browser reported.  (a) cannot see this: a ring at the wrong radius is
           a perfectly good circle.  Two clauses -> two mutants (DECISIONS_2 592). */
  const R_want = ASSET_RING_R * S;
  add('R6 the drawn ring is a circle at the brand ring\'s own radius',
      (ring.rMax - ring.rMin) <= 0.5 && Math.abs(ring.r - R_want) <= 2.0,
      `radius spread ${(ring.rMax - ring.rMin).toFixed(3)}px over 9 samples; ` +
      `drawn r ${ring.r} vs the asset's ${R_want.toFixed(2)} ` +
      `(off ${Math.abs(ring.r - R_want).toFixed(2)}, allowed 2.0)`);

  /* R7 -- THE RING HAS EXACTLY ONE BAY MISSING.  Bounded on both sides: a ring
     that closes has nothing to rebuild, and a ring missing a third of itself is
     a broken shape rather than a socket. */
  add('R7 the ring is open with exactly one bay missing',
      mk.gapDeg >= 40 && mk.gapDeg <= 70 &&
      ring.sweepDeg >= 290 && ring.sweepDeg <= 320 &&
      Math.abs(ring.sweepDeg + mk.gapDeg - 360) <= 0.5,
      `bay ${mk.gapDeg}deg (ring sweeps ${ring.sweepDeg}deg; the two must add to 360)`);

  /* R8 -- THE PART IS THE BAY'S TWIN.  Same arc, same width, same radius of
     curvature.  This is the reading that says "that is the missing piece";
     a part 10 degrees wider is decoration, and it looks exactly as intentional. */
  add('R8 the part is the same arc as the bay it belongs to',
      Math.abs(piece.sweepDeg - mk.gapDeg) <= 1.0 &&
      (piece.rMax - piece.rMin) <= 0.5,
      `part ${piece.sweepDeg}deg vs bay ${mk.gapDeg}deg ` +
      `(off ${Math.abs(piece.sweepDeg - mk.gapDeg).toFixed(2)}, allowed 1.0); ` +
      `part radius spread ${(piece.rMax - piece.rMin).toFixed(3)}px`);

  /* R9 -- THE PART IS LIFTED, NOT SEATED.  Seat it in its slot and the ring
     closes: the picture becomes a finished badge and "rebuild" disappears, while
     every other rule on this page stays green.  Two readings: how far out the
     part is carried, and how much clear air there is between it and the ring. */
  const lift = piece.r - ring.r;
  const clearance = (piece.r - mk.ringW / 2) - (ring.r + mk.ringW / 2);
  add('R9 the part is carried clear of the ring',
      lift >= 24 && clearance >= 16,
      `carried out ${lift.toFixed(2)}px (needs 24), ` +
      `clear air ${clearance.toFixed(2)}px (needs 16)`);

  /* R10 -- THE PART IS AIMED AT ITS HOLE, AND THE GUIDE IS ON THAT AXIS.
     The guide is the thing that turns "a detached arc" into "a part in transit",
     so it has to be on the bay's own mid-radius -- not merely nearby -- and it
     has to run most of the way between the two objects without touching either
     (touching would also make the pixel instrument read the bay as filled). */
  const gapBetween = (piece.r - mk.ringW / 2) - (ring.r + mk.ringW / 2);
  const inLo = guide.r1 - (ring.r + mk.ringW / 2);        // air at the ring end
  const inHi = (piece.r - mk.ringW / 2) - guide.r2;       // air at the part end
  add('R10 the part is aimed at its bay and the guide runs along that radius',
      angDiff(mk.pieceMid, mk.slotMid) <= 1.0 &&
      angDiff(guide.a1, mk.slotMid) <= 0.5 && angDiff(guide.a2, mk.slotMid) <= 0.5 &&
      inLo > 0.5 && inHi > 0.5 &&
      inLo <= 0.35 * gapBetween && inHi <= 0.35 * gapBetween &&
      (guide.r2 - guide.r1) >= 0.40 * gapBetween,
      `part at ${mk.pieceMid}deg vs bay at ${mk.slotMid}deg ` +
      `(off ${angDiff(mk.pieceMid, mk.slotMid).toFixed(2)}, allowed 1.0); ` +
      `guide at ${guide.a1}..${guide.a2}deg, r ${guide.r1}..${guide.r2} of a ` +
      `${gapBetween.toFixed(2)}px gap -- air ${inLo.toFixed(2)} / ${inHi.toFixed(2)}px`);

  /* R11 -- THE HERO IS THE BRAND'S OWN FILE, AND THE CLIP ONLY TAKES THE RING.
     Same clause as the continuation icon's C11, and for the same reason: the mark
     is not redrawn.  The clip has to land in the empty annulus between the arms'
     ends (236) and the ring's inner edge (242); smaller chops the arms' tips off
     flat, larger leaves a sliver of the asset's own ring beside the drawn one.
     Both are one or two pixels and neither looks wrong at 64px. */
  const clipLo = ASSET_ARM_END * S, clipHi = ASSET_RING_IN * S;
  add('R11 the hero is the brand asset, cropped only where the asset is empty',
      /sm-core\.png$/.test(String(em.src)) &&
      Math.abs(em.w - em.h) <= 0.5 &&
      Math.abs((em.top + em.h / 2) - mk.cy) <= 0.5 &&
      em.opacity > 0 && em.opacity <= 1 &&
      em.clip > clipLo && em.clip < clipHi,
      `${em.src} ${em.w}x${em.h} at opacity ${em.opacity}, ` +
      `clip r ${em.clip} inside the empty band ${clipLo.toFixed(1)}..${clipHi.toFixed(1)}`);

  /* R12 -- one vertical axis. */
  const mid = t => (t.left + t.right) / 2;
  const sub = m.text.find(t => t.id === 'sub');
  add('R12 the mark, the asset, the word and the subtitle share one vertical axis',
      Math.abs(mk.cx - AXIS) <= 0.5 &&
      Math.abs((em.left + em.w / 2) - AXIS) <= 0.5 &&
      !!title && Math.abs(mid(title) - AXIS) <= 2 &&
      !!sub && Math.abs(mid(sub) - AXIS) <= 2,
      `mark ${mk.cx}, asset ${Number.isFinite(em.left) ? (em.left + em.w / 2).toFixed(2) : 'n/a'}, ` +
      `word ${title ? mid(title).toFixed(2) : 'n/a'}, ` +
      `subtitle ${sub ? mid(sub).toFixed(2) : 'n/a'} (axis ${AXIS})`);

  /* R13 -- THE PART IS THE ONLY COLOURED THING.  Amber is the game's
     "in progress" token (Config.Visual.Amber); the ring is Ready grey.  Swap them
     and the icon says the wrong thing while every geometric rule stays green.
     The pixel instrument measures the amber's hue with no literal at all. */
  add('R13 the ring is Ready grey and the part is Amber',
      ring.stroke === TOKEN_READY && piece.stroke === TOKEN_AMBER &&
      ring.stroke !== piece.stroke,
      `ring '${ring.stroke}', part '${piece.stroke}'`);

  /* R14 -- decorative layers: every layer declares its polarity and its filter
     agrees, and no layer is switched off. */
  const wrong = m.decor.filter(d =>
    d.art === 'white'    ?  /invert/.test(d.filter)
  : d.art === 'black'    ? !/invert/.test(d.filter)
  : d.art === 'gradient' ?  /invert/.test(d.filter)
  : true);
  const dark = m.decor.filter(d => d.opacity <= 0);
  const badD = [...wrong.map(d => `${d.id}: art ${d.art} but filter '${d.filter}'`),
                ...dark.map(d => `${d.id}: opacity ${d.opacity}`)];
  if (!m.decor.length) badD.push('no decorative layer declared -- the rule has no force');
  add('R14 every decorative layer declares its polarity, matches its filter and is on',
      badD.length === 0,
      badD.length ? badD.join('; ')
                  : `${m.decor.length} layers (${[...new Set(m.decor.map(d => d.art))].join('+')}), ` +
                    `every filter matches its art, no layer at opacity 0`);

  return out;
}

/* ---------- mutations ----------
 * A check that cannot go red is noise (CLAUDE.md 0.31), so the judge is run
 * against deliberately wrong reports.  Every mutation edits the REPORT, not the
 * page -- that is what makes it runnable without a browser.  Each one is a
 * failure this page can actually have, and each one would still look like a
 * fine icon at 64px.
 *
 * Rules carrying two independent readings get two mutants apiece (DECISIONS_2
 * 592): R6 (circle-ness vs radius), R7 (bay size vs "adds to 360"), R8 (width vs
 * arc-ness), R9 (carried out vs clear air), R10 (aimed vs the guide's ends). */
function mutate(name, fn){ return {name, fn}; }
const MUTANTS = [
  /* R0/R1 */
  mutate('the stage is letterboxed in a 1024 viewport',
         m => { m.stage.w = 512; m.stage.h = 512; return m; }),
  mutate('the word is empty',
         m => { m.text.find(t => t.id === 'title').text = ''; return m; }),
  mutate('the brand asset never loaded',
         m => { m.mark.emblem.src = ''; m.mark.emblem.w = 0; return m; }),
  mutate('the carried part is not drawn at all',
         m => { m.mark.piece.len = 0; return m; }),
  mutate('the guide line is not drawn at all',
         m => { m.mark.guide.len = 0; return m; }),
  /* R2/R3 */
  mutate('the subtitle runs past the frame',
         m => { m.text.find(t => t.id === 'sub').right = W - 4; return m; }),
  mutate('the subtitle is dropped onto the word',
         m => { const s = m.text.find(t => t.id === 'sub'); s.top = 820; s.bottom = 846; return m; }),
  /* R4 */
  mutate('the word runs past the right frame edge',
         m => { m.text.find(t => t.id === 'title').right = W - 2; return m; }),
  mutate('the word is too small to read at 1/5',
         m => { const t = m.text.find(t => t.id === 'title'); t.bottom = t.top + 70; return m; }),
  /* R5 */
  mutate('the mark is pushed out through the frame',
         m => { m.mark.bounds.left = 4; return m; }),
  mutate('the mark drifts down into the word',
         m => { m.mark.bounds.bottom += 60; return m; }),
  /* R6 -- two clauses */
  mutate('the drawn ring is no longer a circle',
         m => { m.mark.ring.rMax = m.mark.ring.r + 6; return m; }),
  mutate('the drawn ring sits at the wrong radius',
         m => { m.mark.ring.r += 40; m.mark.ring.rMin += 40; m.mark.ring.rMax += 40; return m; }),
  /* R7 -- two clauses */
  mutate('the bay closes, so the ring is whole and there is nothing to rebuild',
         m => { m.mark.gapDeg = 4; m.mark.ring.sweepDeg = 356; return m; }),
  mutate('the bay swallows a third of the ring',
         m => { m.mark.gapDeg = 120; m.mark.ring.sweepDeg = 240; return m; }),
  mutate('the bay and the sweep no longer add up to a whole ring',
         m => { m.mark.gapDeg = 56; m.mark.ring.sweepDeg = 286; return m; }),
  /* R8 -- two clauses */
  mutate('the part is wider than the bay it belongs to',
         m => { m.mark.piece.sweepDeg = 66; return m; }),
  mutate('the part is not an arc at all',
         m => { m.mark.piece.rMax = m.mark.piece.r + 6; return m; }),
  /* R9 -- two clauses */
  mutate('the part is seated in its slot, so the ring closes and rebuild vanishes',
         m => { m.mark.piece.r = m.mark.ring.r; m.mark.piece.rMin = m.mark.ring.r;
                m.mark.piece.rMax = m.mark.ring.r; return m; }),
  mutate('the part is carried out only a hair',
         m => { const r = m.mark.ring.r + 10;
                m.mark.piece.r = r; m.mark.piece.rMin = r; m.mark.piece.rMax = r; return m; }),
  /* R10 -- three clauses */
  mutate('the part hovers beside its bay instead of over it',
         m => { m.mark.pieceMid = m.mark.slotMid + 22; return m; }),
  mutate('the guide points off-axis',
         m => { m.mark.guide.a1 = m.mark.slotMid + 6; m.mark.guide.a2 = m.mark.slotMid + 6; return m; }),
  mutate('the guide grows until it touches the ring',
         m => { m.mark.guide.r1 = m.mark.ring.r + m.mark.ringW / 2; return m; }),
  mutate('the guide shrinks to a stub',
         m => { const lo = m.mark.ring.r + m.mark.ringW / 2;
                m.mark.guide.r1 = lo + 4; m.mark.guide.r2 = lo + 8; return m; }),
  /* R11 */
  mutate('the hero is some other file',
         m => { m.mark.emblem.src = '../intro/assets/other.png'; return m; }),
  mutate('the clip is too small, so it chops the arms\' tips off flat',
         m => { m.mark.emblem.clip = 200; return m; }),
  mutate('the clip is too large, so a sliver of the asset\'s own ring survives',
         m => { m.mark.emblem.clip = 248; return m; }),
  mutate('the hero is squeezed instead of square',
         m => { m.mark.emblem.h = 460; return m; }),
  /* R12 */
  mutate('the word is off the axis',
         m => { const t = m.text.find(t => t.id === 'title'); t.left += 20; t.right += 20; return m; }),
  mutate('the asset is off the mark\'s centre',
         m => { m.mark.emblem.left += 20; return m; }),
  /* R13 */
  mutate('the ring and the part swap colours',
         m => { m.mark.ring.stroke = TOKEN_AMBER; m.mark.piece.stroke = TOKEN_READY; return m; }),
  mutate('the carried part is drawn in Ready grey, so colour stops saying "in progress"',
         m => { m.mark.piece.stroke = TOKEN_READY; return m; }),
  /* R14 */
  mutate('a decorative layer is switched off',
         m => { m.decor.find(d => d.id === 'vig').opacity = 0; return m; }),
  mutate('the gradient glow is inverted',
         m => { m.decor.find(d => d.id === 'glow').filter = 'invert(1)'; return m; }),
  mutate('a new decorative layer declares no polarity',
         m => { m.decor.push({id: 'grid2', opacity: 0.4, blend: 'screen', filter: '', art: null}); return m; }),
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
  if (!file){ console.error('usage: rebuild_judge.js --selftest <report.txt>'); process.exit(2); }
  const good = report(file);
  const base = run(good, true);
  let bad = 0;
  console.log(`baseline: ${base.res.length - base.bad} ok, ${base.bad} failed`);
  if (base.bad){ console.log('BASELINE IS RED -- fix the page first'); process.exit(1); }
  for (const mu of MUTANTS){
    const m = JSON.parse(JSON.stringify(good));
    const {res} = run(mu.fn(m), true);
    // The rule id is the whole token ("R10"), not its first two characters --
    // otherwise R1 and R10 cannot be told apart (cover_judge's Phase 133 note).
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
if (!file){ console.error('usage: rebuild_judge.js <report.txt>   |   --selftest <report.txt>'); process.exit(2); }
const {res, bad} = run(report(file), false);
console.log(bad ? `${res.length - bad} ok, ${bad} FAILED` : `${res.length} ok, 0 failed`);
process.exit(bad ? 1 : 0);
