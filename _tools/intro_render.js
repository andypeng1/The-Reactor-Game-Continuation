/* intro_render.js -- render intro/index.html to a deterministic mp4.
 *
 * WHY THIS IS NOT A SCREEN RECORDING.  The film is render(t), a pure function
 * of one clock (DECISIONS 303).  So a frame-exact render is just "call
 * render(t), screenshot, next t" -- there is no clock to race, nothing can be
 * dropped, and the same command produces the same file twice.  A realtime
 * capture would be strictly worse: it would sample whatever the page's own
 * requestAnimationFrame happened to be doing, which is exactly the frame
 * timing the film was built not to depend on.
 *
 * The deliverable is NOT modified.  `render` is a top-level `function` in a
 * classic <script>, so it is already a global on the page and CDP can call it.
 * The only thing this script does to the page is:
 *   - stub requestAnimationFrame BEFORE the page script runs, so the film's
 *     own autoplay loop never starts and cannot overwrite a frame it did not
 *     render (the loop and this harness would otherwise both be writing styles);
 *   - display:none the player controls, which are UI, not film.
 *
 * Usage:
 *   node _tools/intro_render.js                      -> full render to intro/THE_REACTOR_GAME_intro.mp4
 *   node _tools/intro_render.js --at 0,3.3,19.5      -> just those frames, as PNGs in _tools/_frames/
 *   node _tools/intro_render.js --fps 60 --out X.mp4
 * Exit: 0 ok / 1 failed -- a broken render must not leave a plausible mp4.
 */
'use strict';

const { spawn } = require('child_process');
const fs   = require('fs');
const os   = require('os');
const path = require('path');

const ROOT   = path.join(__dirname, '..');
const FRAMES = path.join(__dirname, '_frames');

// Not on PATH; the music chain pins ffmpeg the same way (see _tools/music/make_song.py).
const CHROME = process.env.TRG_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const FFMPEG = process.env.TRG_FFMPEG || 'D:\\Bot\\ffmpeg\\bin\\ffmpeg';

const W = 1920, H = 1080, PORT = 9333;

/* ---------- args ---------- */
const argv = process.argv.slice(2);
const arg = (name, dflt) => {
  const i = argv.indexOf('--' + name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : dflt;
};
const FPS   = Number(arg('fps', '30'));
const AT    = arg('at', null);                       // comma-separated seconds -> PNG probe
const EVAL  = arg('eval', null);                     // expression to read back AT each probed t
const CHECK = argv.includes('--check');              // layout assertions in the real browser
const OUT   = path.resolve(ROOT, arg('out', path.join('intro', 'THE_REACTOR_GAME_intro.mp4')));
// The page path is overridable for the same reason intro_check.js's is: the
// only way to know a check can go red is to point it at a broken copy.
const PAGE  = path.resolve(ROOT, arg('page', path.join('intro', 'index.html')));

/* The measurement for --check.  The browser measures, THIS FILE judges -- see
   the note above judge() for why those are kept apart. */
const MEASURE = `(() => {
  const scEl = document.getElementById('scroll'), listEl = document.getElementById('diagList');
  const rows = [...listEl.children];
  const ts = [];
  for (let t = 3.0; t <= 12.51; t += 0.25) ts.push(Math.round(t * 100) / 100);
  const sweep = [];
  for (const t of ts) {
    render(t);
    const sc = scEl.getBoundingClientRect(), listTop = listEl.getBoundingClientRect().top;
    // Two different questions, deliberately measured separately:
    //   lit  -- opacity > 0.5, "how many rows a viewer has finished reading"
    //   lastBottom -- the bottom of the LAST row with any opacity at all,
    //     i.e. the true lower edge of the content. Comparing the bottom edge to
    //     the pane's bottom is the claim "the newest line is pinned to the
    //     bottom"; comparing the newest FULLY-LIT row would instead be asking
    //     about the 0.05s fade, which is a different face (CLAUDE.md 0.18).
    let lit = 0, vis = 0, live = null, lastBottom = null;
    for (const r of rows) {
      const op = parseFloat(r.style.opacity);
      if (!(op > 0)) continue;
      const b = r.getBoundingClientRect();
      lastBottom = b.bottom;
      if (op > 0.5) {
        lit++;
        if (b.bottom > sc.top + 0.5 && b.top < sc.bottom - 0.5) vis++;
        if (r.classList.contains('live')) live = (b.top >= sc.top - 0.5 && b.bottom <= sc.bottom + 0.5);
      }
    }
    sweep.push({t, lit, vis, live, lastBottom, listTop,
      winTop: sc.top, winBottom: sc.bottom, winH: sc.height, rowH: rows[0].offsetHeight});
  }
  // a whole-frame read, so "the pane scrolled correctly" cannot be true of a
  // film that draws nothing at all
  render(24.0);
  const ttl = document.getElementById('title').getBoundingClientRect();
  render(33.0);
  const err = document.getElementById('endMsg').getBoundingClientRect();

  // ---- the back half: does any visible text land on any other visible text?
  // This is the property the film shipped broken (the 170px title sat on top of
  // the three specs and the sign-off for the whole last third) and NO stub-DOM
  // check could see it: every element really was opacity:1 at the right time.
  const TEXT = ['title','subtitle','endMsg','endTag'];
  const back = [];
  for (let t = 22.0; t <= 34.21; t += 0.25) {
    render(Math.round(t * 100) / 100);
    const items = [];
    const push = el => {
      // effective opacity = the element's own times every ancestor's, because
      // the cards fade as a GROUP -- a child's own opacity stays 1 the whole way.
      let o = 1;
      for (let n = el; n && n !== document.body; n = n.parentElement)
        o *= parseFloat(getComputedStyle(n).opacity);
      if (o <= 0.35) return;                       // not "visible" for this test
      // the GLYPH box, not the border box. #title is left:0;right:0, so its
      // border box is the whole 1920 width; comparing those would say two
      // centred lines collide whenever they merely share a row of the screen.
      const rg = document.createRange();
      rg.selectNodeContents(el);
      const b = rg.getBoundingClientRect();
      items.push({id: el.id, top:b.top, bottom:b.bottom, left:b.left, right:b.right});
    };
    for (const id of TEXT) push(document.getElementById(id));
    for (const s of document.querySelectorAll('#specCard .spec')) push(s);
    const t0 = Math.round(t * 100) / 100;
    let pairs = 0, worst = null;
    for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
      const a = items[i], b = items[j];
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox <= 0 || oy <= 0) continue;
      pairs++;
      if (!worst || ox * oy > worst.area)
        worst = {t: t0, a: a.id, b: b.id, area: ox * oy, oy};
    }
    back.push({t: t0, n: items.length, pairs, worst});
  }
  // ---- clipped text: can the viewer READ what the film drew? ----
  // The property is NOT "nothing is ever cut". A terminal pane legitimately cuts
  // a long line at its edge. The property is "nothing is cut WITHOUT SAYING SO":
  // an element whose ink runs past the box that clips it must be ellipsising.
  // Found by the eye (a row chopped mid-word at the pane edge); no vertical or
  // opacity check can see it -- the row is on screen, fully lit, and 446px of it
  // simply is not there.
  const clip = [];
  for (let t = 0.0; t <= 34.51; t += 0.5) {
    render(Math.round(t * 100) / 100);
    const seen = [];
    for (const el of document.querySelectorAll('#film *')) {
      let hasText = false;
      for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) hasText = true;
      if (!hasText) continue;
      let o = 1;                       // same effective-opacity rule as L5
      for (let n = el; n && n !== document.body; n = n.parentElement)
        o *= parseFloat(getComputedStyle(n).opacity);
      if (o <= 0.35) continue;
      const rg = document.createRange();
      rg.selectNodeContents(el);
      const b = rg.getBoundingClientRect();
      if (!b.width) continue;
      let anc = null;                  // nearest box that can clip, self included
      for (let n = el; n && n !== document.body; n = n.parentElement)
        if (getComputedStyle(n).overflow !== 'visible') { anc = n; break; }
      if (!anc) continue;
      const a = anc.getBoundingClientRect();
      const cut = Math.max(0, b.right - a.right, a.left - b.left,
                              b.bottom - a.bottom, a.top - b.top);
      if (cut <= 0.5) continue;
      seen.push({id: el.id || (el.className + '') || el.tagName, cut: Math.round(cut),
                 marked: getComputedStyle(el).textOverflow === 'ellipsis',
                 text: (el.textContent || '').trim().slice(0, 46)});
    }
    if (seen.length) clip.push({t: Math.round(t * 100) / 100, n: seen.length,
      unmarked: seen.filter(s => !s.marked).length,
      worst: seen.sort((x, y) => y.cut - x.cut)[0]});
  }

  return JSON.stringify({sweep, back, clip,
    title:{w: ttl.width, h: ttl.height, y: ttl.top}, end:{w: err.width, h: err.height}});
})()`;

function bail(msg){ console.error('FAIL ' + msg); cleanup(1); }

let chrome = null;
const tmpProfile = fs.mkdtempSync(path.join(os.tmpdir(), 'trg-intro-'));
function cleanup(code){
  try { if (chrome && !chrome.killed) chrome.kill(); } catch (e) {}
  try { fs.rmSync(tmpProfile, {recursive:true, force:true}); } catch (e) {}
  process.exit(code);
}

/* ---------- a minimal CDP client over the built-in WebSocket (Node >= 22) ---------- */
class CDP {
  constructor(ws){ this.ws = ws; this.id = 0; this.pending = new Map(); this.events = [];
    ws.addEventListener('message', ev => {
      const m = JSON.parse(ev.data);
      if (m.id !== undefined){
        const p = this.pending.get(m.id); this.pending.delete(m.id);
        if (!p) return;
        m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result);
      } else { this.events.push(m); }
    });
  }
  send(method, params){
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, {resolve, reject});
      this.ws.send(JSON.stringify({id, method, params: params || {}}));
    });
  }
  async waitEvent(method, ms){
    const t0 = Date.now();
    for(;;){
      const i = this.events.findIndex(e => e.method === method);
      if (i >= 0) return this.events.splice(i, 1)[0];
      if (Date.now() - t0 > (ms || 15000)) throw new Error('timed out waiting for ' + method);
      await sleep(20);
    }
  }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function getJSON(url){
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ' -> HTTP ' + r.status);
  return r.json();
}

/* ---------- judging the layout sweep ----------
 * The browser is the *instrument* (it is the only thing here that has layout);
 * the pass/fail rule is written here, where it can be read and changed without
 * touching the film. A measurement that also decides what counts as correct
 * tends to quietly redefine correct.
 *
 * L1 is the assertion that would have caught the real defect: every row was
 * opacity:1 the whole time and the pane was still empty, because #diagList was
 * bottom-anchored so its 1215px body began 346px ABOVE the window -- and the
 * scroll transform then subtracted again. Every stub-DOM check was green,
 * because a stub DOM has no layout to be wrong about. Only this harness can
 * hold this property. */
function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});
  const s = m.sweep;
  const cap = Math.floor(s[0].winH / s[0].rowH);        // whole rows that fit

  const bad1 = s.filter(r => r.lit > 0 && r.vis < Math.min(r.lit, cap));
  add('L1 lit rows are on screen (up to a full pane)', bad1.length === 0,
      bad1.length ? `first at t=${bad1[0].t}: only ${bad1[0].vis} of ${bad1[0].lit} visible (cap ${cap})`
                  : `${s.length} instants, cap ${cap}`);

  const bad2 = s.filter(r => r.live === false);
  add('L2 the cursor row is never scrolled out', bad2.length === 0,
      bad2.length ? `first at t=${bad2[0].t}` : 'always inside');

  // "scrolled" is read off the layout (block pushed above the pane top), not
  // recomputed from the row count -- recomputing it here would be restating the
  // film's own formula back to itself and would pass for any transform at all.
  const scroll = s.filter(r => r.listTop < r.winTop - 0.5);
  const bad3 = scroll.filter(r => Math.abs(r.winBottom - r.lastBottom) > 1.0);
  add('L3 the newest row rides the bottom once full', scroll.length > 0 && bad3.length === 0,
      !scroll.length ? 'NEVER SCROLLED -- this test has no force'
      : bad3.length ? `first at t=${bad3[0].t}: content bottom is ${(bad3[0].winBottom - bad3[0].lastBottom).toFixed(1)}px off the pane bottom`
      : `${scroll.length} scrolled instants`);

  add('L4 the title card is laid out at t=24', m.title.w > 200 && m.title.h > 20,
      `title ${m.title.w.toFixed(0)}x${m.title.h.toFixed(0)}`);
  add('L4 the sign-off is laid out at t=33', m.end.w > 100 && m.end.h > 10,
      `endMsg ${m.end.w.toFixed(0)}x${m.end.h.toFixed(0)}`);

  // L5: the back half must not stack text on text. The `co.length > 0` half is
  // the empty-set lesson (CLAUDE.md 0.6): "no two things collide" is free on a
  // sweep where only one thing was ever on screen, so the check has to show it
  // had material to collide.
  const overlap = m.back.filter(r => r.pairs > 0);
  const co      = m.back.filter(r => r.n >= 2);
  const first   = overlap[0];
  add('L5 no two visible text blocks collide (back half)',
      overlap.length === 0 && co.length > 0,
      !co.length ? 'NEVER TWO BLOCKS ON SCREEN AT ONCE -- this test has no force'
      : first ? `first at t=${first.t}: ${first.worst.a} over ${first.worst.b} by ${first.worst.oy.toFixed(0)}px (${first.worst.area.toFixed(0)}px2)`
              : `${co.length}/${m.back.length} instants carry 2+ blocks, 0 colliding`);

  // L6: a cut must be MARKED. `clip.length > 0` is the same empty-set guard as
  // L5 -- if the film never cut anything the rule would be free, so the check
  // has to show it had something to cut.
  const uncut = m.clip.filter(r => r.unmarked > 0);
  const c0    = uncut[0];
  add('L6 nothing is cut off without saying so',
      uncut.length === 0 && m.clip.length > 0,
      !m.clip.length ? 'NOTHING WAS EVER CUT -- this test has no force'
      : c0 ? `first at t=${c0.t}: ${c0.worst.id} cut ${c0.worst.cut}px unmarked -- '${c0.worst.text}'`
           : `${m.clip.length} instants cut something, every one marked`);

  return out;
}

/* ---------- main ---------- */
(async function main(){
  if (!fs.existsSync(CHROME)) bail('no browser at ' + CHROME + ' (set TRG_CHROME)');
  if (!fs.existsSync(PAGE))   bail('no page at ' + PAGE);

  chrome = spawn(CHROME, [
    '--headless=new',
    '--remote-debugging-port=' + PORT,
    '--user-data-dir=' + tmpProfile,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
    '--hide-scrollbars', '--mute-audio',
    // Text rendering is the one thing that is not deterministic across
    // machines; pinning these makes two runs on THIS machine identical.
    '--force-color-profile=srgb', '--font-render-hinting=none', '--disable-lcd-text',
    '--window-size=' + W + ',' + H,
    'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  chrome.stderr.on('data', () => {});          // chrome is chatty on stderr

  // wait for the debug endpoint
  let target = null;
  for (let i = 0; i < 100; i++){
    try {
      const list = await getJSON('http://127.0.0.1:' + PORT + '/json/list');
      target = list.find(t => t.type === 'page');
      if (target && target.webSocketDebuggerUrl) break;
    } catch (e) {}
    await sleep(150);
  }
  if (!target) bail('chrome never opened a debuggable page on port ' + PORT);

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.addEventListener('open', res, {once:true});
    ws.addEventListener('error', () => rej(new Error('websocket failed')), {once:true});
  });
  const cdp = new CDP(ws);

  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');

  // 1. kill the film's own loop before it exists. Without this the page's
  //    requestAnimationFrame autoplay would keep calling render() behind us.
  await cdp.send('Page.addScriptToEvaluateOnNewDocument', {source:
    'window.requestAnimationFrame = function(){ return 0; };'});

  // 2. pin the viewport so fit() sees exactly 1920x1080 -> scale 1, and the
  //    screenshot is exactly the design space (no letterbox to crop).
  await cdp.send('Emulation.setDeviceMetricsOverride',
    {width:W, height:H, deviceScaleFactor:1, mobile:false});

  const url = 'file:///' + PAGE.replace(/\\/g, '/');
  await cdp.send('Page.navigate', {url});
  await cdp.waitEvent('Page.loadEventFired', 20000);
  await sleep(250);                            // let CSS backgrounds decode

  // 3. the player is a control surface, not part of the film
  const hid = await cdp.send('Runtime.evaluate', {expression:
    '(()=>{const g=[];for(const id of ["player","bigplay","hint"]){const e=document.getElementById(id);' +
    'if(e){e.style.display="none";g.push(id);}}' +
    'if(typeof render!=="function")throw new Error("render is not global on the page");' +
    'return g.join(",")+" | innerW="+innerWidth+" innerH="+innerHeight;})()',
    returnByValue:true});
  if (hid.exceptionDetails) bail('page setup failed: ' + JSON.stringify(hid.exceptionDetails.exception));
  console.log('page ready: ' + hid.result.value);

  // Drive the clock. Everything visual follows from this one call, so both the
  // screenshot and the --eval read below see the same instant.
  async function drive(t){
    const r = await cdp.send('Runtime.evaluate', {expression:`render(${t})`, returnByValue:true});
    if (r.exceptionDetails) throw new Error('render(' + t + ') threw: ' + JSON.stringify(r.exceptionDetails.exception));
  }
  async function shot(t, file){
    await drive(t);
    const s = await cdp.send('Page.captureScreenshot',
      {format:'png', fromSurface:true, captureBeyondViewport:false});
    const buf = Buffer.from(s.data, 'base64');
    fs.writeFileSync(file, buf);
    return buf.length;
  }
  async function readback(t, expression){
    await drive(t);
    const r = await cdp.send('Runtime.evaluate', {expression, returnByValue:true});
    if (r.exceptionDetails) throw new Error('eval threw: ' + JSON.stringify(r.exceptionDetails.exception));
    return r.result.value;
  }

  /* ---------- probe mode: a few frames, as PNGs, for a human/vision look ----------
     --eval is the other half of that: a screenshot proves it *looks* right to a
     reader, --eval proves *what the values are*.  CLAUDE.md 0.14b: the wrong
     measurement is quiet, the wrong picture is loud -- so take both. */
  if (AT || EVAL){
    fs.mkdirSync(FRAMES, {recursive:true});
    for (const t of (AT || '0').split(',').map(Number)){
      if (EVAL){
        const v = await readback(t, EVAL);
        console.log(`  t=${t.toFixed(3)} eval -> ${typeof v === 'string' ? v : JSON.stringify(v)}`);
      }
      if (AT){
        const f = path.join(FRAMES, 'probe_' + String(t).replace('.', '_') + '.png');
        const n = await shot(t, f);
        console.log(`  t=${t.toFixed(3)} -> ${path.relative(ROOT, f)}  ${(n/1024).toFixed(0)} KiB`);
      }
    }
    console.log('probe done (no mp4 written)');
    return cleanup(0);
  }

  /* ---------- --check: the layout half, which the stub-DOM harness cannot see ---------- */
  if (CHECK){
    const r = await cdp.send('Runtime.evaluate', {expression: MEASURE, returnByValue:true});
    if (r.exceptionDetails) bail('measurement threw: ' + JSON.stringify(r.exceptionDetails.exception));
    const res = judge(JSON.parse(r.result.value));
    let bad = 0;
    for (const a of res){
      if (!a.ok) bad++;
      console.log(`${a.ok ? 'ok  ' : 'FAIL'}  ${a.label}  [${a.detail}]`);
    }
    console.log(bad ? `${res.length - bad} ok, ${bad} FAILED` : `${res.length} ok, 0 failed`);
    return cleanup(bad ? 1 : 0);
  }

  /* ---------- full render ---------- */
  // 0..total INCLUSIVE, so the last frame is the film's actual end state
  // (fully black) rather than 0.03 s short of it.
  const total = await (async () => {
    const r = await cdp.send('Runtime.evaluate', {expression:'T.total', returnByValue:true});
    return Number(r.result.value);
  })();
  const N = Math.round(total * FPS) + 1;
  fs.rmSync(FRAMES, {recursive:true, force:true});
  fs.mkdirSync(FRAMES, {recursive:true});

  console.log(`film total=${total}s, ${N} frames @ ${FPS} fps`);
  const t0 = Date.now();
  for (let i = 0; i < N; i++){
    const t = i / FPS;
    await shot(t, path.join(FRAMES, 'f' + String(i).padStart(5, '0') + '.png'));
    if (i % 60 === 0 || i === N - 1){
      const pct = ((i + 1) / N * 100).toFixed(0);
      const eta = i ? ((Date.now() - t0) / i * (N - i) / 1000).toFixed(0) : '?';
      console.log(`  frame ${i + 1}/${N} (t=${t.toFixed(2)}s) ${pct}%  eta ${eta}s`);
    }
  }
  const grabbed = Date.now() - t0;

  // the capture loop is over; the browser is not needed for the encode
  chrome.kill();

  console.log(`captured ${N} frames in ${(grabbed/1000).toFixed(1)}s; encoding ...`);
  await new Promise((resolve, reject) => {
    const ff = spawn(FFMPEG, [
      '-y', '-v', 'error', '-stats',
      '-framerate', String(FPS),
      '-i', path.join(FRAMES, 'f%05d.png'),
      // crf 18 + slow: this is a dark film full of film grain and scanlines,
      // which is the worst case for a block-based codec -- the grain is what
      // eats the bitrate, so a fast preset visibly smears the noise layer.
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
      '-pix_fmt', 'yuv420p',          // yuv420p, not yuv444: players want it
      '-movflags', '+faststart',       // moov atom first, so it streams/previews
      OUT,
    ], {stdio: ['ignore', 'inherit', 'inherit']});
    ff.on('exit', c => c === 0 ? resolve() : reject(new Error('ffmpeg exit ' + c)));
    ff.on('error', reject);
  });

  const bytes = fs.statSync(OUT).size;
  console.log(`wrote ${path.relative(ROOT, OUT)}  ${(bytes/1048576).toFixed(2)} MiB`);
  fs.rmSync(FRAMES, {recursive:true, force:true});
  cleanup(0);
})().catch(e => bail(e && e.message ? e.message : String(e)));
