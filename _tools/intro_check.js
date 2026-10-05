/* intro_check.js -- headless verification of intro/index.html
 *
 * WHY THIS EXISTS. The intro is a film; "it looked right when I opened it" is
 * exactly the kind of evidence this project does not accept (CLAUDE.md §4.4).
 * What CAN be checked without a browser is the half that is a pure function:
 * render(t). So this harness builds a throwaway DOM, evaluates the real
 * <script> block out of the shipped file -- the deliverable's own bytes, not a
 * copy -- and reads the resulting inline styles back at chosen instants.
 *
 * Two kinds of assertion live here and they are NOT the same thing:
 *   COVERAGE -- at t, this element is on screen, because the shot list says so
 *   GUARD    -- this specific defect cannot come back
 * Every guard is a defect that was actually written and then fixed; a check
 * that has never been red is decoration (DECISIONS_2 298).
 *
 * WHAT THIS CANNOT SEE, and does not pretend to: anything CSS solves.
 * Layout, blending, whether the noise texture tiles, whether fonts resolve --
 * all of that is the browser's half. Those four facts are checked against the
 * shipped HTML as text and are labelled (source) so they are not mistaken for
 * a render. Neither half substitutes for the other (CLAUDE §0.14b).
 *
 * Run:  "D:\nodejs\node" _tools\intro_check.js [path-to-html]
 *       The optional path exists so the harness can be pointed at a MUTATED
 *       COPY -- a check that has never been red is decoration (DECISIONS_2 298),
 *       and the only way to know these can go red is to make them.
 *       _tools/intro_mutants.py does exactly that.
 * Exit: 0 all ok / 1 something failed -- including a crash, so a broken
 *       harness cannot look like a pass (CLAUDE §0.6).
 */
'use strict';
const fs   = require('fs');
const path = require('path');

const HTML_PATH = process.argv[2] || path.join(__dirname, '..', 'intro', 'index.html');
const html = fs.readFileSync(HTML_PATH, 'utf8');

/* ---------- a DOM just big enough for this file, and no bigger ---------- */
function stubNode(){
  const node = {
    className:'', textContent:'', dataset:{},
    style: new Proxy({}, {
      set(o,k,v){ o[k]=v; return true; },
      get(o,k){ return o[k]===undefined ? '' : o[k]; },
    }),
    classList:(function(){
      const s = new Set();
      return { add:c=>s.add(c), remove:c=>s.delete(c), contains:c=>s.has(c),
               toggle:(c,f)=>{ const on = f===undefined ? !s.has(c) : !!f; on?s.add(c):s.delete(c); return on; } };
    })(),
    appendChild(c){ return c; },
    addEventListener(){}, setPointerCapture(){},
    getBoundingClientRect(){ return {left:0,width:1000}; },
  };
  node.querySelector = () => stubNode();     // .val / .bar s -- written, never read
  return node;
}
const byId = new Map();
const getById = id => (byId.has(id) || byId.set(id, stubNode()), byId.get(id));

global.document = {
  getElementById:getById, createElement:()=>stubNode(), addEventListener(){},
  documentElement:{ requestFullscreen(){} }, fullscreenElement:null,
};
global.window = { innerWidth:1920, innerHeight:1080, addEventListener(){} };
global.performance = { now:()=>0 };
global.requestAnimationFrame = ()=>0;        // never re-enter tick()
global.setTimeout = ()=>0;  global.clearTimeout = ()=>{};

/* ---------- load the deliverable's own script ---------- */
function bail(msg){ console.log('FAIL ' + msg); process.exit(1); }

let render, T, DIAGNOSTIC, BOOTLOG, diagNodes, logNodes;
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) bail('no <script> block in ' + HTML_PATH);
try {
  ({render, T, DIAGNOSTIC, BOOTLOG, diagNodes, logNodes} = new Function(
      m[1] + '\n;return {render,T,DIAGNOSTIC,BOOTLOG,diagNodes,logNodes};')());
} catch (e) { bail('the shipped script does not evaluate: ' + e.message); }

/* ---------- helpers ---------- */
const results = [];
const ok = (label, pass, detail) => results.push({label, pass:!!pass, detail:detail||''});
const op = id => parseFloat(getById(id).style.opacity || '0');
const num = id => parseFloat(getById(id).style.width || '0');
const str = id => getById(id).style.transform || '';
const dOp = i => parseFloat(diagNodes[i].style.opacity || '0');
const lOp = i => parseFloat(logNodes[i].style.opacity || '0');

/* ---------- 1. the timeline must not produce garbage anywhere ---------- */
{
  const bad = [];
  for (let t = 0; t <= T.total + 1e-9; t += 0.05){
    try { render(+t.toFixed(3)); } catch (e) { bad.push(`t=${t.toFixed(2)} threw: ${e.message}`); continue; }
    for (const [id,node] of byId)
      for (const k of ['opacity','width','transform','backgroundPosition','letterSpacing','top','left'])
        if (/NaN|undefined/.test(String(node.style[k] || ''))) bad.push(`t=${t.toFixed(2)} ${id}.${k}=${node.style[k]}`);
  }
  ok('no NaN/undefined style on the whole timeline', bad.length===0, bad.slice(0,3).join(' | '));
}

/* ---------- 2. COVERAGE -- the shot list, as assertions ---------- */
// Stronger than "it appeared": the line must be WHOLE while still fully
// opaque, which is exactly what the 55 ms/char draft failed -- it was still
// writing when the panel started covering it, so the film permanently showed
// "[CONS] BOOT-UP INITI" and nothing anywhere reported it.
render(1.40);
ok('S1 the boot command is whole by t=1.4, and still solid',
   getById('bootLine').textContent === '[CONS] BOOT-UP INITIALIZED' && op('bootLine') > 0.95,
   '"' + getById('bootLine').textContent + '" @ ' + op('bootLine').toFixed(2));
render(2.30); ok('S1 that command has cleared by t=2.3', op('bootLine') < 0.01);
render(2.60);
ok('S2 the two panes are up by t=2.6', op('panel') > 0.95);
ok('S2 the three status lamps are lit', getById('lamp1').style.background.includes('nominal'));
render(3.30);  ok('S3 diagnostic row 1 is on at t=3.3',  dOp(0)  > 0.95);
render(10.20); ok('S3 diagnostic row 45 is on at t=10.2', dOp(44) > 0.95);
render(10.20);
ok('S3 the cursor rides the newest row, and only it',
   diagNodes[44].classList.contains('live') && !diagNodes[43].classList.contains('live'));
render(11.90); ok('S3 all six boot-log lines are on at t=11.9',
   [0,1,2,3,4,5].every(i=>lOp(i) > 0.95));
render(16.20);
ok('S4 panel, grid and HUD have all cleared by t=16.2',
   op('panel') < 0.02 && op('bgGrid') < 0.02 && op('hud') < 0.02);
render(19.50); ok('S6 the company logo is on at t=19.5',      op('logoCard') > 0.95);
render(20.90); ok('S6 the chime ring has collapsed by 20.9',  op('chime') < 0.02);
render(25.00); ok('S6 the logo has settled as a watermark',   op('watermark') > 0.3);
render(24.00);
ok('S7 the title is on at t=24.0', op('title') > 0.95);
ok('S7 the caution band spans the full frame', num('titleBand') === 1920, num('titleBand')+'px');
render(31.00); ok('S8 spec line 3 is on at t=31.0',           op('sp3') > 0.95);
render(33.00); ok('S9 the [ERR] line is on at t=33.0',        op('endMsg') > 0.95);
render(34.80); ok('S9 the CRT has collapsed to a line',       /scaleY\(0\.0008\)/.test(str('film')));
render(34.99); ok('S9 the screen is black at t=35.0',         op('blackout') > 0.95);

/* ---------- 3. GUARD -- the four defects that were actually written ---------- */
// G1. The controls sit inside #stage, and #stage carries its own click-to-toggle.
//     Without stopPropagation a click on Play runs Play AND the toggle, so the
//     button pauses itself. The fix is a structural one, so the check is one:
//     the player must be a sibling of #film, i.e. after its closing marker.
{
  const closeFilm = html.indexOf('</div><!-- /film -->');
  const player    = html.indexOf('<div id="player">');
  ok('G1 #player is a sibling of #film, not inside it',
     closeFilm > 0 && player > closeFilm,
     'CRT collapse must not squash the controls');
}
// G1b. ...and the handler that makes the click safe must actually be there.
ok('G1b the controls stop click propagation to #stage',
   /\$\('player'\)\.addEventListener\('click',\s*stop\)/.test(html));
// G2. Typing 45 lines a character at a time at 40 ms cannot finish inside a
//     0.155 s slot, so two dozen rows sit half-written -- which is a broken
//     terminal, not a scrolling one. Rows must reveal whole. Measured, not read:
//     the row's text is already complete the instant it becomes visible.
{
  render(10.10);                       // row 44 is 0.155 s old here
  ok('G2 diagnostic rows reveal whole, never half-typed',
     diagNodes[44].textContent === DIAGNOSTIC.rows[44][0],
     '"' + diagNodes[44].textContent.slice(-24) + '"');
}
// G3. The watermark landed on top of the HUD timecode -- both bottom-left.
//     CSS sets that offset, so the check reads the stylesheet.
ok('G3 the watermark clears the timecode',
   /#watermark\{[^}]*bottom:150px/.test(html.replace(/\s+/g,'')),
   'was bottom:52px, same corner as .tc');
// G4. The collapse must move #film only. If it moved #stage the player would
//     collapse with it and the end card would have no visible controls.
{
  render(34.80);
  ok('G4 the collapse never touches #stage',
     !/scaleY/.test(getById('stage').style.transform || ''),
     '#' + 'stage transform = "' + (getById('stage').style.transform||'(none)') + '"');
}

/* ---------- report ---------- */
let pass = 0, failed = 0;
for (const r of results){
  console.log((r.pass ? 'ok   ' : 'FAIL ') + r.label + (r.detail ? '   [' + r.detail + ']' : ''));
  r.pass ? pass++ : failed++;
}
console.log(`\n${pass} ok, ${failed} failed`);
process.exit(failed ? 1 : 0);
