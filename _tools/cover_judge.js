/* cover_judge.js -- the pass/fail half of the cover's layout check.
 *
 * WHY THERE ARE TWO PROCESSES.  The browser is the only instrument here that has
 * layout, and _tools/intro_render.js is the only thing here that can drive a
 * browser.  So the browser MEASURES (cover/index.html's layoutReport()) and this
 * file JUDGES -- the same split the intro uses (_tools/intro_check.js vs
 * _tools/intro_render.js, DECISIONS_2 309).  A file that measures and then
 * decides what counts as correct tends to quietly redefine correct.
 *
 * It also means this file needs no Chrome and no CDP client: it is a pure
 * function from one JSON blob to an exit code, so it can be run against a
 * deliberately broken report to see whether it can go red at all.
 *
 * Usage:
 *   node _tools/intro_render.js --page cover/index.html --at 0 --w 1080 --h 1080 \
 *        --eval 'layoutReport()' > report.txt
 *   node _tools/cover_judge.js report.txt        # exit 0 / 1
 *   node _tools/cover_judge.js --selftest        # runs the judge on mutants of a good report
 */
'use strict';

const fs = require('fs');

const FRAME_IN = 22;                    // the frame's inset, from cover/index.html
const INNER    = 1080 - 2 * FRAME_IN;   // 1036: everything must live inside this
const SAFE     = 6;                     // px of clearance the rule asks for
const RULE_TOP = 806;                   // #rule's top -- the title must clear it
const BAND_TOP = 704;                   // #titleBand's top -- the hex must clear it
const HR1_TOP  = 92;                    // #hr1's top    -- the hex must start below it
const COS30    = Math.cos(Math.PI / 6);

/* ---------- the rules ----------
 * Each returns {label, ok, detail}.  Nothing here reads the page: it reads the
 * numbers the page produced, which is the point of the split above. */
function judge(m){
  const out = [];
  const add = (label, ok, detail) => out.push({label, ok, detail});

  /* A0 -- the frame of reference itself.  If the stage is not 1080x1080 the
     renderer is letterboxing, and every coordinate below is in the wrong space. */
  add('A0 the design space is 1080x1080 and fills the viewport',
      m.stage.w === 1080 && m.stage.h === 1080 && m.innerW === 1080 && m.innerH === 1080,
      `stage ${m.stage.w}x${m.stage.h}, viewport ${m.innerW}x${m.innerH}`);

  /* A1 -- non-vacuity, said before anything is judged.  Most of the rules below
     are "no two things collide" / "nothing is outside": both are free on a page
     that drew two things, or nothing (CLAUDE.md 0.20, the empty set lies twice). */
  add('A1 there is enough on the page for the rules to have force',
      m.text.length >= 12 && m.cells.length === 4,
      `${m.text.length} text blocks, ${m.cells.length} bar cells`);

  /* A2 -- every text block is inside the frame.  #hazard and #bar are elements,
     so this is about the type: a cover whose subtitle runs under the frame edge
     is a cover that will be cropped differently by whoever uploads it. */
  const outside = m.text.filter(t =>
    t.left < FRAME_IN + 4 || t.right > 1080 - FRAME_IN - 4 ||
    t.top  < FRAME_IN + 4 || t.bottom > 1080 - FRAME_IN - 4);
  add('A2 every text block is inside the frame',
      outside.length === 0,
      outside.length ? outside.map(t => `${t.id} [${t.left}..${t.right}]x[${t.top}..${t.bottom}]`).join('; ')
                     : `${m.text.length} blocks inside [${FRAME_IN + 4}..${1080 - FRAME_IN - 4}]`);

  /* A3 -- no two text blocks overlap.  This is the intro's L5 rule; it is here
     because the title band, the title, the rule and the subtitle are four
     separately positioned things, and "they all look fine" is not a reading.
     Both halves matter: 0 colliding AND some pairs that were close enough to
     collide.  minGap is the near-miss report -- if it is huge, nothing was
     ever at risk and the rule proved nothing. */
  let pairs = 0, worst = null, minGap = Infinity;
  for (let i = 0; i < m.text.length; i++) for (let j = i + 1; j < m.text.length; j++){
    const a = m.text[i], b = m.text[j];
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 0 && oy > 0){
      pairs++;
      if (!worst || ox * oy > worst.area) worst = {a: a.id, b: b.id, area: ox * oy, oy};
    } else if (ox > 0){
      // same columns: how much air is between them vertically?
      const g = Math.max(a.top, b.top) - Math.min(a.bottom, b.bottom);
      if (g < minGap) minGap = g;
    }
  }
  add('A3 no two text blocks collide',
      pairs === 0 && minGap < 40,
      pairs ? `${worst.a} over ${worst.b} by ${worst.oy.toFixed(2)}px (${worst.area.toFixed(0)}px2)`
            : (minGap === Infinity
                 ? 'NO TWO BLOCKS SHARE A COLUMN -- this test has no force'
                 : `0 colliding; closest vertical miss ${minGap.toFixed(2)}px`));

  /* A4 -- the title.  Two separate claims: it fits the inner width (a 96px
     condensed line is close to the limit at this size) and it clears the rule
     under it. */
  const title = m.text.find(t => t.id === 'title');
  add('A4 the title fits and clears the rule under it',
      !!title && (title.right - title.left) < INNER && title.bottom < RULE_TOP,
      title ? `w=${(title.right - title.left).toFixed(1)} of ${INNER}, bottom ${title.bottom} vs rule ${RULE_TOP}`
            : 'no title measured');

  /* A5 -- the hero hexagon fits between the two things that bound it: the top
     hairline above and the title band below. */
  add('A5 the hero hexagon sits between the top rule and the title band',
      m.hex.top > HR1_TOP + SAFE && m.hex.bottom < BAND_TOP - SAFE &&
      m.hex.left > FRAME_IN + SAFE && m.hex.right < 1080 - FRAME_IN - SAFE,
      `hex x[${m.hex.left}..${m.hex.right}] y[${m.hex.top}..${m.hex.bottom}] ` +
      `(limits: top>${HR1_TOP + SAFE}, bottom<${BAND_TOP - SAFE})`);

  /* A6 -- THE TWO HEXAGONS ARE THE SAME SHAPE.  The hero panel is clipped by a CSS
     percentage polygon, so its vertices are whatever the box's proportions make
     them; the frame is an SVG polygon computed from HEX_R.  If the box is not
     exactly 2*cos30 : 2, the drawn frame and the panel's edge are two different
     hexagons -- and both of them LOOK like hexagons, so nothing about the
     picture would say so.  Ratio first, then the vertices themselves. */
  add('A6 the hero panel box has the pointy-top hexagon proportion',
      Math.abs(m.hex.ratio - m.hex.want) < 0.01,
      `height/width ${m.hex.ratio}, want ${m.hex.want} (2/(2cos30))`);
  add('A7 the CSS clip and the SVG frame are the same hexagon',
      m.hex.worstVertexPx < 0.5,
      `worst vertex ${m.hex.worstVertexPx}px apart (vertex #${m.hex.worstAt})`);

  /* A8 -- every readout bar value fits its own cell.  This is the one rule about
     something being EATEN rather than colliding: `white-space:nowrap` means an
     over-wide value does not wrap, it just runs out of the cell and under the
     next one's divider.  Measured per cell, value against ITS cell, because a
     total-width check cannot see a value crossing a divider. */
  const tight = m.cells.filter(c => !c.v.fits || !c.k.fits);
  add('A8 every bar cell holds its own key and value',
      tight.length === 0,
      tight.length ? tight.map(c => `${c.id} '${c.v.text}' ${c.v.fits ? '' : 'value ' + c.v.w + 'px in ' + c.cellW}`).join('; ')
                   : m.cells.map(c => `${c.id}=${c.v.slack.toFixed(0)}px slack`).join(', '));

  /* A9 -- 装饰层不是"画上去就算数"。
     出处是一次真实缺陷：五个装饰层里两个在画上**逐像素等于零**、另外两个的
     振幅塌到 1%–14%，而页面照样渲染成功、其它九条规则全绿。两种"恒等变换"，
     都不报错：
        `filter:invert(1)` 作用在**近白的**线稿上（量出来 nested-hex
        rgb(235,235,235)、sm-logo rgb(228,228,228)）把它转成黑，压在近黑的底上 ——
        层还在，振幅从 Δ24 掉到 Δ3（这一条不是零，是"看不见"）；
        `mix-blend-mode:screen` 拿**黑**素材当上源（stripes rgb(0,0,0)），
        而 screen(底, 0) = 底 —— 这一条**是零**：把这一层按旧写法渲染出来，
        与把它整层关掉相比 0 px 差、最大 Δ0。
     "看不见"和"没画"在盘上长得一模一样（0.18/0.19），所以量的是像素，
     不是样式（_tools/cover_layers.sh）；这一条只抓得住样式这一半。
     断言写成**双条件**：素材是白的 ⟺ 不许 invert；素材是黑的 ⟺ 必须 invert。
     素材的极性浏览器量不到（file:// 下 canvas 读背景图被污染），所以由每一层
     在 HTML 上用 `data-art` 声明，声明旁边写着量出它的那条命令 ——
     这条断言检的是"声明和 filter 一致"，而声明的出处是可复查的。
     第三种声明是 `gradient`（纯 CSS 画的层，本来就没有素材）：它**更不许**
     invert —— 反色只会产出调色板里没有的颜色（青 → 橙），那是发明。 */
  const wrongFilter = m.decor.filter(d =>
    d.art === 'white'    ?  /invert/.test(d.filter)
  : d.art === 'black'    ? !/invert/.test(d.filter)
  : d.art === 'gradient' ?  /invert/.test(d.filter)
  : true);                                  // 没声明 = 不知道极性 = 红
  const dark = m.decor.filter(d => d.opacity <= 0);
  const kinds = new Set(m.decor.map(d => d.art));
  add('A9 no decorative layer is a no-op',
      kinds.has('black') && kinds.has('white') && wrongFilter.length === 0 && dark.length === 0,
      (wrongFilter.length || dark.length)
        ? [...wrongFilter.map(d => `${d.id}: art ${d.art} but filter '${d.filter}'`),
           ...dark.map(d => `${d.id}: opacity ${d.opacity}`)].join('; ')
        : (kinds.has('black') && kinds.has('white')
             ? `${m.decor.length} layers declared (${[...kinds].join('+')}), every invert matches its art`
             : `${m.decor.length} layers, declared kinds [${[...kinds].join(',')}] -- ` +
               `need both a black and a white one or this rule has no force`));

  /* A10 -- 六边里那枚厂标不许捅出六边的边线（Phase 133）。
     厂标是一个**独立的、不受 clip-path 裁切**的元素（被裁的是面板）。所以它一旦
     长得比六边能装的大，就会**穿过那圈实线、跑到六边外面去** —— 而它跑出去那部分
     照样画得出来，画出来只是"一条线穿过了另一条线"，读图不会说这是错的。
     判据用**到六条边线的有符号距离**（内为正），不是"半径 ≤ 内切圆"：后者只在
     厂标正好居中时成立，而"居中"本身没有断言。这条与 §0.31 那条同族 ——
     要让它红，得先有一个真的越界的尺寸在场。 */
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
    // 六边自己的中心一定在内部，所以它给出的符号就是"内"的方向。
    const sign = cross([hcx, hcy]) >= 0 ? 1 : -1;
    const slack = sign * cross([m.mark.cx, m.mark.cy]) - m.mark.w / 2;
    if (slack < minSlack){ minSlack = slack; worstEdge = i; }
  }
  add('A10 the hero mark stays inside the hexagon it is drawn in',
      minSlack >= 8,
      `mark r=${(m.mark.w / 2).toFixed(1)} at (${m.mark.cx},${m.mark.cy}) in a hexagon of R=${R}: ` +
      `tightest of the six edges (#${worstEdge}) leaves ${minSlack.toFixed(1)}px`);

  return out;
}

/* ---------- mutations ----------
 * A check that cannot go red is noise (CLAUDE.md 0.6/0.31), so the judge is run
 * against deliberately wrong reports and each mutation must light a NAMED rule.
 * The mutations are edits to the REPORT, not to the page: that is what makes
 * this runnable without a browser, and what the rule "the browser measures, the
 * file judges" buys. */
function mutate(name, fn){
  return {name, fn};
}
const MUTANTS = [
  // The realistic failure, not a made-up one: run the renderer without --w/--h
  // and the viewport is 1920x1080, so the square stage gets letterboxed inside
  // the screenshot and every coordinate in this report is in the wrong space.
  mutate('stage letterboxed in a 1920x1080 viewport', m => { m.innerW = 1920; return m; }),
  mutate('subtitle runs past the frame', m => {
    const s = m.text.find(t => t.id === 'subtitle'); s.right = 1080; s.left = -20; return m; }),
  mutate('title collides with the subtitle rule', m => {
    const t = m.text.find(t => t.id === 'title'); t.bottom = 812; return m; }),
  mutate('hexagon pushed into the title band', m => { m.hex.bottom = 700; return m; }),
  mutate('hero panel box is not a hexagon proportion', m => { m.hex.ratio = 1.0; return m; }),
  mutate('SVG frame drawn at the wrong radius', m => { m.hex.worstVertexPx = 9.4; return m; }),
  mutate('the hero mark grows out through the hexagon outline',
         m => { m.mark.w = 560; m.mark.h = 560; return m; }),
  mutate('quota value overflows its cell', m => {
    const c = m.cells.find(x => x.id === 'c3'); c.v.fits = false; c.v.slack = -40; return m; }),
  mutate('only two things on the page', m => { m.text = m.text.slice(0, 2); return m; }),
  // The three real defects this round, all "renders fine, changes no pixel":
  // a black asset fed to screen without inverting, a near-white one inverted
  // into black, and a layer left at opacity 0.
  mutate('the stripe band loses its invert, so screen blends black onto black',
         m => { m.decor.find(d => d.id === 'titleBand').filter = 'none'; return m; }),
  mutate('the hex lattice inverts a near-white asset into black',
         m => { m.decor.find(d => d.id === 'hexes').filter = 'invert(1)'; return m; }),
  mutate('a decorative layer is switched off with opacity 0',
         m => { m.decor.find(d => d.id === 'hazard').opacity = 0; return m; }),
  mutate('a new decorative layer does not declare its asset polarity',
         m => { m.decor.push({id: 'stripes2', opacity: 0.4, blend: 'screen',
                              filter: 'invert(1)', art: null}); return m; }),
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
  if (!file){ console.error('usage: cover_judge.js --selftest <report.txt>'); process.exit(2); }
  const good = report(file);
  const base = run(good, true);
  let bad = 0;
  console.log(`baseline: ${base.res.length - base.bad} ok, ${base.bad} failed`);
  if (base.bad) { console.log('BASELINE IS RED -- fix the cover first'); process.exit(1); }
  for (const mu of MUTANTS){
    const m = JSON.parse(JSON.stringify(good));
    const {res} = run(mu.fn(m), true);
    // 规则号取整个词（"A10"），不是前两个字符 —— 后者会把 A10 打成 "A1"，
    // 于是 `--selftest` 的读数分不开"打到 A1"和"打到 A10"（Phase 133 实测，
    // 一个 1 red [A1] 看着像打错了规则，其实是它对的那一条）。同 §0.20 一族：
    // 展示用的截断把两个不同的东西压成同一个字符串。
    const red = res.filter(r => !r.ok).map(r => r.label.split(' ')[0]);
    const uniq = [...new Set(red)];
    // "lights exactly the rule it is aimed at" is the strong form; more than one
    // is still evidence the rule can fail, but it is a weaker statement and the
    // count is printed so the difference is visible rather than averaged away.
    const ok = red.length >= 1;
    if (!ok) bad++;
    console.log(`${ok ? 'ok  ' : 'FAIL'}  mutant '${mu.name}' -> ${red.length} red [${uniq.join(',')}]`);
  }
  console.log(bad ? `${MUTANTS.length - bad} of ${MUTANTS.length} mutants lit a rule, ${bad} lit NOTHING`
                  : `${MUTANTS.length}/${MUTANTS.length} mutants each lit at least one rule`);
  process.exit(bad ? 1 : 0);
}

const file = argv.find(a => !a.startsWith('--'));
if (!file){ console.error('usage: cover_judge.js <report.txt>   |   --selftest <report.txt>'); process.exit(2); }
const {res, bad} = run(report(file), false);
console.log(bad ? `${res.length - bad} ok, ${bad} FAILED` : `${res.length} ok, 0 failed`);
process.exit(bad ? 1 : 0);
