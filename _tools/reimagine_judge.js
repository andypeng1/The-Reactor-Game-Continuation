/* reimagine_judge.js -- the pass/fail half of the Reimagine icon's check.
 *
 * Same split as _tools/rebuild_judge.js and _tools/continuation_judge.js
 * (DECISIONS_2 309): the browser MEASURES (cover/reimagine.html's layoutReport()),
 * this file DECIDES.  Keeping them apart is also what lets --selftest feed this
 * file deliberately broken reports with no browser involved.
 *
 * WHAT THE PICTURE IS (Phase 152).  The previous two icons both said their thing
 * with a centred mark and a word underneath.  This one changes how the whole
 * picture speaks:
 *
 *     one vertical axis -- the brand mark's OWN axis -- splits the picture.
 *     left  = the mark as DRAWN     (white line art, interior empty)
 *     right = the mark as CAST      (interior filled amber, line art untouched)
 *
 * and the same axis cuts the word: REIMA | GINE.
 *
 * Two consequences decide what is worth checking here:
 *
 *   (a) "the same drawing on both sides" is LITERAL -- the mark is one <img>
 *       spanning the axis; the amber is a half-disc underneath it.  So the
 *       claim is not "the halves look alike", it is "nothing was re-drawn".
 *       The DOM can only say the picture was built that way; whether the ink on
 *       the two halves really is one drawing per radius is measured by
 *       _tools/reimagine_pieces_check.py, which holds no constant at all.
 *   (b) the word is TWO copies with identical boxes, differing only in colour
 *       and clip.  That makes "the word changes treatment" a REGISTRATION rather
 *       than a placement -- and a registration is a thing you can lose silently
 *       (the two copies drift, and the cut becomes two cuts).
 *
 * WHAT THIS FILE DELIBERATELY DOES NOT CHECK: "the amber radius equals the
 * ring's inner radius".  Both numbers come from the same page constant, so the
 * comparison would be a check measuring a constant against itself -- CLAUDE.md
 * 0.31 (6).  R6 only bounds the disc to the interior; the exact coincidence is
 * the pixel instrument's reading, taken from the ink.
 *
 * Usage:
 *   node _tools/intro_render.js --page cover/reimagine.html --at 0 --w 1024 --h 1024 \
 *        --eval 'layoutReport()' > report.txt
 *   node _tools/reimagine_judge.js report.txt
 *   node _tools/reimagine_judge.js --selftest report.txt
 */
'use strict';

const fs = require('fs');

const W = 1024, H = 1024;
const FRAME_IN = 20;                    // #frame's inset, from cover/reimagine.html
const SAFE = 6;
const ASSET_PX = 515;                   // the brand file's own edge, in asset pixels

/* The two design tokens, quoted from src/ReactorBackend/Config.luau
   (Config.Visual.Ready / Config.Visual.Amber).  cover/index.html takes its
   colours from the same place.  The pixel instrument measures the amber's hue
   with no literal at all, so this pair is not the only witness (DECISIONS_2 655). */
const TOKEN_READY = 'rgb(235, 235, 235)';
const TOKEN_AMBER = 'rgb(255, 128, 1)';

/* Parse `inset(a b c d)` in px (what getComputedStyle gives for clip-path).
   Returns null for anything else -- an unparseable clip must fail the rule, not
   silently contribute a zero.  (-1 would be a number; null is not.) */
function insetPx(s){
  const m = /^\s*inset\(([^)]*)\)\s*$/.exec(String(s || ''));
  if (!m) return null;
  const t = m[1].trim().split(/\s+/).map(x => {
    const v = /^(-?[\d.]+)px$/.exec(x);
    return v ? +v[1] : (x === '0' ? 0 : NaN);
  });
  if (!t.length || t.some(Number.isNaN)) return null;
  const [a, b = a, c = a, d = b] = t;          // the inset() shorthand, same as CSS
  return {top: a, right: b, bottom: c, left: d};
}

const boxMid = b => ({x: (b.left + b.right) / 2, y: (b.top + b.bottom) / 2});

function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});

  const mk = m.mark || {};
  const box = mk.box || {};
  const db = mk.discBox || {};
  const tx = m.text || {};
  const tW = tx.titleW || {};
  const tA = tx.titleA || {};
  const sub = tx.sub || {};
  const letters = tx.letters || [];
  const col = m.colours || {};
  const clips = m.clips || {};
  const font = m.font || {};
  const probe = font.probe || {};
  const n = m.cutAfter;

  /* R0 -- the frame of reference.  Forgetting --w/--h letterboxes the stage and
     every coordinate below is in the wrong space. */
  add('R0 the design space is 1024x1024 and fills the viewport',
      m.stage.w === W && m.stage.h === H && m.innerW === W && m.innerH === H,
      `stage ${m.stage.w}x${m.stage.h}, viewport ${m.innerW}x${m.innerH}`);

  /* R1 -- non-vacuity, said before anything is judged.  Every rule below has the
     form "this sits in the right place", and all of them are free on a page that
     drew nothing.  The word is listed letter by letter because "REIMAGINE" is
     the icon's subject: a page that drew "REIMAGNE" is not a near miss. */
  const spelled = letters.map(l => l.ch).join('');
  const want = 'REIMAGINE';
  const missing = [];
  if (!/sm-core\.png$/.test(String(mk.src || ''))) missing.push('brand asset src');
  if (!mk.complete) missing.push('asset not decoded');
  if (!(mk.natural && mk.natural.w === ASSET_PX && mk.natural.h === ASSET_PX))
    missing.push(`asset is not ${ASSET_PX}px square`);
  if (spelled !== want) missing.push(`word reads "${spelled}" not "${want}"`);
  if (!String(tW.text || '').trim()) missing.push('white copy');
  if (!String(tA.text || '').trim()) missing.push('amber copy');
  if (!String(sub.text || '').trim()) missing.push('subtitle');
  if (!(mk.discR > 0)) missing.push('amber disc has no radius');
  if (!(m.decor || []).length) missing.push('no decorative layer');
  add('R1 the word, both of its copies, the subtitle, the asset and the disc are all present',
      missing.length === 0,
      missing.length ? `MISSING: ${missing.join(', ')}`
                     : `${spelled} x2 + ${sub.text}; asset ${mk.natural.w}px, disc r ${mk.discR}px`);

  /* R2 -- the mark is inside the frame.  Roblox re-crops this image. */
  add('R2 the mark is inside the frame',
      box.left > FRAME_IN + SAFE && box.right < W - FRAME_IN - SAFE &&
      box.top > FRAME_IN + SAFE && box.bottom < H - FRAME_IN - SAFE,
      `mark x[${box.left}..${box.right}] y[${box.top}..${box.bottom}] ` +
      `inside [${FRAME_IN + SAFE}..${W - FRAME_IN - SAFE}]`);

  /* R3 -- THE TWO COPIES ARE ONE WORD IN ONE PLACE.  This is the registration the
     whole right-hand treatment rests on: one box, two colours, two complementary
     clips.  If the boxes drift the cut becomes two cuts in two places, and at
     64px that still looks like a word with a coloured half. */
  const dL = Math.abs(tW.left - tA.left), dT = Math.abs(tW.top - tA.top);
  const dW = Math.abs(tW.w - tA.w), dH = Math.abs(tHm(tW) - tHm(tA));
  add('R3 the two copies of the word occupy one and the same box',
      Number.isFinite(dL + dT + dW + dH) && dL <= 0.5 && dT <= 0.5 && dW <= 0.5 && dH <= 0.5,
      `white [${tW.left},${tW.top} ${tW.w}x${tW.h}] vs amber [${tA.left},${tA.top} ${tA.w}x${tA.h}]; ` +
      `deltas ${dL.toFixed(2)} / ${dT.toFixed(2)} / ${dW.toFixed(2)} / ${dH.toFixed(2)}px (allowed 0.5)`);

  /* R4 -- THE AXIS IS THE MARK'S OWN AXIS.  Not "somewhere down the middle": the
     vertical through the brand mark's centre.  That is what makes the split read
     as the object's own symmetry rather than as a straight line laid over it. */
  add('R4 the axis is the mark\'s own vertical axis',
      Math.abs(m.seam - mk.cx) <= 0.5,
      `seam at x=${m.seam}, mark centre at x=${mk.cx} (off ${Math.abs(m.seam - mk.cx).toFixed(2)})`);

  /* R5 -- the amber is centred on the mark.  The half-disc's centre IS the mark's
     centre; the clip is what makes it a half.  Off-centre here means the disc is
     a different circle being hidden, and the amber's edge stops being the axis
     (the pixel instrument measures that edge separately -- it is the seam). */
  const dm = boxMid(box), dd = boxMid(db);
  add('R5 the amber disc is concentric with the mark',
      Math.abs(dm.x - dd.x) <= 0.5 && Math.abs(dm.y - dd.y) <= 0.5,
      `mark centre (${dm.x.toFixed(2)}, ${dm.y.toFixed(2)}), ` +
      `disc centre (${dd.x.toFixed(2)}, ${dd.y.toFixed(2)})`);

  /* R6 -- the disc fills the interior without crossing the ring.  Bounded on both
     sides, and that is all this rule says: the ring's inner wall is the pixel
     instrument's reading (see the header), so this file must not restate it as
     "disc radius == a constant" -- that would be a check comparing a number with
     the number that produced it. */
  const ratio = mk.ringR > 0 ? mk.discR / mk.ringR : NaN;
  add('R6 the disc fills the mark\'s interior and stays inside the ring',
      ratio >= 0.92 && ratio <= 0.98,
      `disc r ${mk.discR} is ${(ratio * 100).toFixed(2)}% of the ring centreline r ${mk.ringR} ` +
      `(window 92..98%; the exact inner-wall coincidence is the pixel instrument's call)`);

  /* R7 -- the axis really splits the mark.  An axis at the edge of the square would
     pass R4 only if the mark were re-centred, so both are needed: this one says
     each half carries at least 40% of the emblem. */
  const leftHalf = m.seam - box.left, rightHalf = box.right - m.seam;
  add('R7 the axis cuts the mark into two substantial halves',
      leftHalf >= 0.40 * box.w && rightHalf >= 0.40 * box.w,
      `left ${leftHalf.toFixed(2)}px, right ${rightHalf.toFixed(2)}px of a ${box.w}px mark ` +
      `(each needs ${(0.40 * box.w).toFixed(1)})`);

  /* R8 -- the word is cut BETWEEN two letters, on that axis.  The cut has to land
     in the gap the type itself provides; a cut through the middle of a glyph
     chops a leg off and reads as damage, not as two halves.  The boundary is read
     from the browser's per-character Ranges, not from an estimate of the kerning. */
  const prev = letters[n - 1], next = letters[n];
  const gapLo = prev ? Math.abs(m.seam - prev.right) : NaN;
  const gapHi = next ? Math.abs(next.left - m.seam) : NaN;
  add('R8 the word changes treatment in the gap between two letters',
      !!prev && !!next && gapLo <= 2 && gapHi <= 2 &&
      prev.right <= m.seam + 0.5 && next.left >= m.seam - 0.5,
      prev && next
        ? `cut after "${prev.ch}" (right edge ${prev.right}) and before "${next.ch}" ` +
          `(left edge ${next.left}), axis ${m.seam}: misses ${gapLo.toFixed(2)} / ${gapHi.toFixed(2)}px ` +
          `(allowed 2)`
        : `cutAfter=${n} does not name two letters (the word has ${letters.length})`);

  /* R9 -- the three bands keep their order and their air.  Measured boxes, so the
     gaps are the line boxes, not the ink: the ink gaps are larger and the pixel
     instrument measures those.  This rule is here to catch a block being pushed
     into its neighbour, which is silent at 64px. */
  const g1 = sub.top - box.bottom, g2 = tW.top - sub.bottom;
  add('R9 mark, subtitle and word are three bands that do not touch',
      g1 >= 24 && g2 >= 2,
      `mark bottom ${box.bottom} -> subtitle top ${sub.top} = ${g1}px (needs 24); ` +
      `subtitle bottom ${sub.bottom} -> word top ${tW.top} = ${g2}px (needs 2)`);

  /* R10 -- everything drawn is inside the frame. */
  const outside = [
    ['mark', box], ['subtitle', sub], ['white word', tW], ['amber word', tA]
  ].filter(([, b]) => b.left < FRAME_IN + 4 || b.right > W - FRAME_IN - 4 ||
                      b.top < FRAME_IN + 4 || b.bottom > H - FRAME_IN - 4);
  add('R10 nothing is drawn outside the frame',
      outside.length === 0,
      outside.length ? outside.map(([id, b]) => `${id} [${b.left}..${b.right}]x[${b.top}..${b.bottom}]`).join('; ')
                 : `all four boxes inside [${FRAME_IN + 4}..${W - FRAME_IN - 4}]`);

  /* R11 -- the mark is the hero: it may not shrink to a badge with a big word. */
  add('R11 the mark is the hero of the picture',
      box.w >= 0.55 * W,
      `mark ${box.w}px = ${(100 * box.w / W).toFixed(1)}% of the width (needs 55%)`);

  /* R12 -- the word carries the width, and is big enough to survive 1/5. */
  const tw = tW.right - tW.left;
  add('R12 the word spans the picture without touching the frame',
      tw / W >= 0.78 && tw / W <= 0.97 && tW.h >= 90,
      `word ${tw.toFixed(1)}px = ${(100 * tw / W).toFixed(1)}% of the width ` +
      `(window 78..97%), line box ${tW.h}px (needs 90)`);

  /* R13 -- the two treatments are the two tokens, and they are not the same one.
     Amber is the game's "in progress" token (Config.Visual.Amber); Ready grey is
     the drawn state.  Swapping them says the wrong thing while every geometric
     rule stays green. */
  add('R13 the left treatment is Ready grey and the right is Amber',
      col.titleW === TOKEN_READY && col.titleA === TOKEN_AMBER && col.disc === TOKEN_AMBER &&
      col.titleW !== col.titleA,
      `word '${col.titleW}' / '${col.titleA}', disc '${col.disc}'`);

  /* R14 -- THE CLIPS ARE CLAIMS ABOUT EACH ELEMENT'S OWN BOX.
     This is the reading that Phase 152 needed and the DOM first refused to give:
     `clip-path: inset()` is measured from the ELEMENT's edges, not the stage, so a
     clip computed as "1024 - 566" from the stage produces a string that looks
     right, reads back correctly, and cuts in the wrong place.  The check therefore
     reconstructs each cut from the parsed inset AND the measured box -- never from
     the number the page used to build the string. */
  const cR = insetPx(clips.mkR), cW = insetPx(clips.titleW), cA = insetPx(clips.titleA);
  const cutMark = cR ? box.left + cR.left : NaN;                 // where the half-disc starts
  const cutW   = cW ? tW.left + (tW.w - cW.right) : NaN;          // where the white copy stops
  const cutA   = cA ? tA.left + cA.left : NaN;                    // where the amber copy starts
  const halfOf = box.w / 2;
  add('R14 both clips cut on the axis, reconstructed from each element\'s own box',
      !!cR && !!cW && !!cA &&
      Math.abs(cR.left - halfOf) <= 0.5 && Math.abs(cutMark - m.seam) <= 0.5 &&
      Math.abs(cutW - m.seam) <= 0.5 && Math.abs(cutA - m.seam) <= 0.5,
      `insets parsed; disc starts at ${cutMark}, white stops at ${cutW}, amber starts at ${cutA} ` +
      `(axis ${m.seam}); mark's half-width ${halfOf} vs the disc clip's left inset ` +
      `${cR ? cR.left : 'unparsed'}`);

  /* R15 -- THE CONDENSED FAMILY ACTUALLY RESOLVED.  Two readings (DECISIONS_2 655):
     the stack's width equals the named family's width, AND it differs from plain
     sans-serif.  One reading is not enough -- a missing family falls back to
     sans-serif, so "it measured a number" proves nothing.  Phase 149 learned this
     the hard way: the widths were read correctly and the attribution was not. */
  const cond = font.condW100, an = probe['"Arial Narrow"'], ss = probe['sans-serif'];
  add('R15 the word is set in the named condensed face, not in its fallback',
      Number.isFinite(cond) && Number.isFinite(an) && Number.isFinite(ss) &&
      Math.abs(cond - an) <= 0.01 && (ss - cond) >= 20,
      `stack ${cond}, "Arial Narrow" ${an}, sans-serif ${ss} ` +
      `(delta to the named face ${Number.isFinite(an) ? (cond - an).toFixed(2) : 'n/a'}, ` +
      `to the fallback ${Number.isFinite(ss) ? (ss - cond).toFixed(2) : 'n/a'}, needs >= 20)`);

  /* R16 -- decorative layers: every layer declares its polarity and its filter
     agrees, and no layer is switched off.  Same rule as the other two icons. */
  const wrong = (m.decor || []).filter(d =>
    d.art === 'white'    ?  /invert/.test(d.filter)
  : d.art === 'black'    ? !/invert/.test(d.filter)
  : d.art === 'gradient' ?  /invert/.test(d.filter)
  : true);
  const dark = (m.decor || []).filter(d => d.opacity <= 0);
  const badD = [...wrong.map(d => `${d.id}: art ${d.art} but filter '${d.filter}'`),
                ...dark.map(d => `${d.id}: opacity ${d.opacity}`)];
  if (!(m.decor || []).length) badD.push('no decorative layer declared -- the rule has no force');
  add('R16 every decorative layer declares its polarity, matches its filter and is on',
      badD.length === 0,
      badD.length ? badD.join('; ')
                  : `${m.decor.length} layers (${[...new Set(m.decor.map(d => d.art))].join('+')}), ` +
                    `every filter matches its art, no layer at opacity 0`);

  return out;
}

/* the two copies' heights, guarded so a missing copy reads as NaN rather than
   throwing a TypeError that would look like "the judge crashed" (CLAUDE.md 0.6
   is about exactly this shape: a crash and a pass must not look alike). */
function tHm(t){ return (t && typeof t.h === 'number') ? t.h : NaN; }

/* ---------- mutations ----------
 * A check that cannot go red is noise (CLAUDE.md 0.31), so the judge is run
 * against deliberately wrong reports.  Every mutation edits the REPORT, not the
 * page -- that is what makes it runnable without a browser.  Each is a failure
 * this page can actually have, and each would still look like a fine icon at
 * 64px.
 *
 * Rules carrying two independent readings get two mutants apiece (DECISIONS_2
 * 592): R3 (drift vs size), R6 (too big vs too small), R8 (through a glyph vs
 * after the wrong letter), R9 (both gaps), R13 (the disc vs the word's halves),
 * R14 (three separate cuts), R15 (fallback vs no probe at all),
 * R16 (off vs mis-declared).
 */
function mutate(name, fn){ return {name, fn}; }
const MUTANTS = [
  /* R0 */
  mutate('the stage is letterboxed in a 1024 viewport',
         m => { m.stage.w = 512; m.stage.h = 512; return m; }),
  /* R1 */
  mutate('the brand asset never loaded',
         m => { m.mark.src = ''; m.mark.complete = false; m.mark.natural = {w: 0, h: 0}; return m; }),
  mutate('the word is misspelled',
         m => { m.text.letters[5].ch = 'N'; return m; }),
  mutate('the second copy of the word is empty',
         m => { m.text.titleA.text = ''; return m; }),
  mutate('the amber disc is not drawn at all',
         m => { m.mark.discR = 0; m.mark.discBox = {left: 566, top: 400, right: 566, bottom: 400, w: 0, h: 0};
                return m; }),
  mutate('no decorative layer is declared',
         m => { m.decor = []; return m; }),
  /* R2 */
  mutate('the mark is pushed out through the left of the frame',
         m => { m.mark.box.left = 10; return m; }),
  /* R3 -- two clauses */
  mutate('the amber copy drifts right, so there are two cuts',
         m => { m.text.titleA.left += 6; m.text.titleA.right += 6; return m; }),
  mutate('the amber copy is set at a different size',
         m => { m.text.titleA.h -= 20; m.text.titleA.bottom -= 20; return m; }),
  /* R4 */
  mutate('the axis moves off the mark\'s centre',
         m => { m.seam += 6; return m; }),
  /* R5 */
  mutate('the disc drifts up out of the mark\'s centre',
         m => { m.mark.discBox.top -= 8; m.mark.discBox.bottom -= 8; return m; }),
  /* R6 -- two clauses */
  mutate('the disc grows to the ring and swallows it',
         m => { m.mark.discR = m.mark.ringR; return m; }),
  mutate('the disc shrinks to a dot in the middle',
         m => { m.mark.discR = 60; return m; }),
  /* R7 */
  mutate('the axis sits near the mark\'s edge instead of through it',
         m => { m.mark.box.left = 480; m.mark.box.right = 1100; return m; }),
  /* R8 -- two clauses */
  mutate('the cut falls through the middle of a letter',
         m => { m.text.letters[4].right = m.seam + 30; return m; }),
  mutate('the cut lands after a different letter',
         m => { m.cutAfter = 4; return m; }),
  /* R9 -- two clauses */
  mutate('the subtitle is dropped onto the word',
         m => { m.text.sub.top = 800; m.text.sub.bottom = 828; return m; }),
  mutate('the mark descends into the subtitle',
         m => { m.mark.box.bottom = 780; m.mark.cy += 70; return m; }),
  /* R10 */
  mutate('the word runs past the right frame edge',
         m => { m.text.titleW.right = W - 2; m.text.titleA.right = W - 2; return m; }),
  mutate('the subtitle runs past the frame',
         m => { m.text.sub.right = W - 4; return m; }),
  /* R11 */
  mutate('the mark shrinks to a badge',
         m => { m.mark.box = {left: 416, top: 250, right: 716, bottom: 550, w: 300, h: 300}; return m; }),
  /* R12 */
  mutate('the word is too short to carry the width',
         m => { m.text.titleW.right = m.text.titleW.left + 500;
                m.text.titleA.right = m.text.titleA.left + 500; return m; }),
  /* R13 -- two clauses */
  mutate('the disc is drawn in Ready grey, so the right half stops reading as cast',
         m => { m.colours.disc = TOKEN_READY; return m; }),
  mutate('the two halves of the word swap colours',
         m => { m.colours.titleW = TOKEN_AMBER; m.colours.titleA = TOKEN_READY; return m; }),
  /* R14 -- the three cuts, one apiece.  The first is the real Phase 152 bug. */
  mutate('the white copy is clipped as if inset() were measured from the stage',
         m => { m.clips.titleW = 'inset(0px 458px 0px 0px)'; return m; }),
  mutate('the amber copy\'s clip is off by twelve pixels',
         m => { m.clips.titleA = 'inset(0px 0px 0px 517.42px)'; return m; }),
  mutate('the disc clip no longer halves the mark',
         m => { m.clips.mkR = 'inset(0px 0px 0px 240px)'; return m; }),
  /* R15 -- two clauses */
  mutate('the condensed face is missing and the word falls back to sans-serif',
         m => { m.font.condW100 = m.font.probe['sans-serif']; return m; }),
  mutate('the font probe was never taken',
         m => { m.font.probe = {}; return m; }),
  /* R16 -- two clauses */
  mutate('a decorative layer is switched off',
         m => { m.decor.find(d => d.id === 'vig').opacity = 0; return m; }),
  mutate('a decorative layer\'s filter contradicts its declared polarity',
         m => { m.decor.find(d => d.id === 'scan').filter = 'invert(1)'; return m; }),
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
  if (!file){ console.error('usage: reimagine_judge.js --selftest <report.txt>'); process.exit(2); }
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
if (!file){ console.error('usage: reimagine_judge.js <report.txt>   |   --selftest <report.txt>'); process.exit(2); }
const {res, bad} = run(report(file), false);
console.log(bad ? `${res.length - bad} ok, ${bad} FAILED` : `${res.length} ok, 0 failed`);
process.exit(bad ? 1 : 0);
