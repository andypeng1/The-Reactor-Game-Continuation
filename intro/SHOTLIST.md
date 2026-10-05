# TRG 开机片头 —— 视频脚本 / Shot List

> 产物两件：
> **`intro/index.html`**（单文件，双击即可用浏览器打开，可拖进度条）
> 和 **`intro/THE_REACTOR_GAME_intro.mp4`**（同一个片子的视频版，5.66 MiB，1920×1080，无声 ——
> 由 `_tools/intro_render.js` 逐帧渲染，见 §7）。
> 本文件是它的**分镜脚本**：每一镜的时间、画面、出场文字，以及**每一行文案的出处**。
> 生成：2026-10-05（§5 与 §7 于 Phase 92 重写）。

---

## 0. 这是什么 / 怎么放

一段 **35 秒、无声**的 TRG 风格开机片头（loading 那种）。纯 HTML/CSS/JS，
**没有构建步骤、没有 CDN、没有外部字体、没有音频** —— 所有素材都复制在
`intro/assets/`（相对路径），所以从 `file://` 双击打开就能放，不需要起服务器。

播放器在画面底部：`▶` 播放/暂停、`↺` 重播、进度条可拖动。

| 键 | 作用 |
|---|---|
| `空格` | 播放 / 暂停 |
| `←` `→` | ∓1 秒 |
| `Shift+←` `Shift+→` | ∓5 秒 |
| `R` | 重播 |
| `F` | 全屏 |
| `Home` `End` | 片头 / 片尾 |
| `0`–`9` | 跳到第 N 镜 |

**设计空间是固定的 1920×1080**（`#stage`），整块按
`k = min(窗口宽/1920, 窗口高/1080)` 等比缩放居中 —— 所以任何窗口尺寸下
都是同一幅画面，只是大小不同。

**它为什么能随便拖**：整个片头是 `render(t)` —— **t 的纯函数**。进来只有 t，
出去只有样式，没有状态机、没有累积增量、没有任何东西记得"上一帧"。
所以拖进度条是**真的跳**（不是快进），循环第二遍和第一遍**逐字节相同**。
这和工程里 `GameState` 的"单一真相源"是同一条纪律：时间只有一个，所有元素都是它的读者。

---

## 1. 时间轴（脚本本体）

数字全部来自 `intro/index.html` 的 `T` 表 —— 那是权威，本文件只是它的散文版。

| 键 | 秒 | 含义 |
|---|---|---|
| `total` | 35.00 | 片长 |
| `powerOn` | 0.15 | CRT 点亮那一下白闪 |
| `bootTyped` | 0.35 | 开机令开始打字 |
| `panelIn` | 1.60 | 两栏从中间长开 |
| `panelGrow` | 0.55 | 长开用时（`Quad/Out`） |
| `gridIn` | 1.90 | 背景网格淡入 |
| `diagStart` | 3.20 | 诊断行第一条 |
| `diagStep` | 0.155 | 每条间隔 → 45 条收在 3.20..10.02 |
| `logAt` | 3.60 / 5.20 / 6.80 / 8.40 / 10.00 / 11.60 | 右栏 6 条 |
| `fadeOut` | 15.00 | 全体文字开始淡出 |
| `blackHold` | 16.40 | 全黑开始 |
| `logoIn` | 18.20 | 厂标入场 |
| `logoMove` | 20.30 | 缩到 0.55 并滑到左下当水印 |
| `titleIn` | 22.40 | 标题条 |
| `specIn` | 27.20 | 三条规格 |
| `endIn` | 32.00 | `[ERR] Good luck, You'll need it.` |
| `collapse` | 34.30 | CRT 塌成一条线 |
| `off` | 34.90 | 全黑，片尾 |

---

## 2. 分镜表

镜号与 `_tools/intro_check.js` 里的断言标签**同名**，方便对照"这一镜被验过没有"。
时长 = 这一镜占的时间窗。

| 镜 | 时间 | 画面 | 出场文字 | 备注 |
|---|---|---|---|---|
| **S0** | 0.00–1.60 | 黑底 + CRT 噪点 + 一条白色回扫带；屏幕中间自己打出开机令（逐字） | `[CONS] BOOT-UP INITIALIZED` | **游戏里没有这一段** —— 游戏是直接跳进面板的。留它是为了让片头有个"开机"动作。 |
| **S1** | 1.60–3.20 | 两栏面板从中间 `Quad/Out` 长开；三颗状态灯逐颗由冷转绿 | 栏头 `SUBSPACE REACTOR MANAGEMENT NODE` / `BOOT LOG` | 手感抄自操作员自己那份 `Addition/Shift4.luau` 的两条 Tween |
| **S2** | 3.20–11.60 | 左栏 45 行诊断**整行整行**往下刷（光标钉在最新一行），右栏 6 条开机日志积累，下方 4 条读数条逐条到顶 | 见 §3.1 | 全片最长的一镜，就是"加载中"那个感觉本身 |
| **S3** | 15.00–16.40 | 文字先走、外框后走，一行一行错开灭 | —— | 灭按行序错开 12 ms，不是像抹布一下抹平 |
| **S4** | 16.40–18.20 | **全黑**（约 1.8 秒） | —— | 操作员原话："the screen is supposed to go black for a bit of time"。**没有断言** —— 这是一个"没有东西"的镜，只能验它前后两边 |
| **S5** | 18.20–20.30 | 厂标（SM 六边形）淡入 + 一圈"叮"的圆环收拢 | `SYNTHESIS MANUFACTURING CORPORATION` | 收拢的动作是个纯 CSS 环，没有声音 |
| **S6** | 20.30–22.40 | 厂标缩到 0.55、滑到左下角，变成常驻**水印** | 同上 | 水印落点避开了 HUD 时间码（都在左下；相差 150px 而不是 52px） |
| **S7** | 22.40–27.20 | 标题条压满全宽（危险条纹）+ 转动的堆芯徽记 | `THE REACTOR GAME` / `SUBSPACE REACTOR INSTALLATION · OPERATOR SHIFT SIMULATION` | 底栏那句在此时翻成琥珀色 —— 全片唯一的"实时"提示 |
| **S8** | 27.20–32.00 | 三条规格卡依次升起 | `NO CONTROL RODS` / `THREE INDIRECT SYSTEMS` / `ONE SHIFT TO GET IT RIGHT` | **全片唯一不是游戏原文的文案**（见 §3.3） |
| **S9** | 32.00–35.00 | `[ERR]` 那行 → CRT 塌成一条线 → 那条线也收成一个点 → 全黑 | `[ERR] Good luck, You'll need it.` / `ICARUS INSTALLATION · SECTOR 04 · REPORT FOR DUTY` | 塌线只压 `#film`，**不碰播放器** |

HUD（左上两行 tag、右上 REC、左下 `T+00:00:00` 时间码）在 S1 起亮、S3 灭 ——
**它只属于"终端"那几镜**：全黑那段必须是真的黑，而时间码 + REC 压在标题卡上
会让它读起来像一个视频播放器，而不是一张标题。

---

## 3. 文案逐条出处

**这一节是这份文档存在的理由。** 片头里的字不是编的；下面把每一行标出来源，
**重建的那几行列明是重建的，不混进"实测"里**。

出处代号：

| 代号 | 含义 |
|---|---|
| **V** | **逐字恢复自采集** —— 操作员在原版游戏里抓的产物里就有这一行 |
| **G** | **游戏里别处的字符串原文** —— 不是这一屏抓到的，但确实是游戏自己的文案 |
| **R** | **重建** —— 从来没进过任何一份产物；沿用游戏的做法（前缀 / 全大写 / `>` 分隔 / 连拼写错误照抄）写出来的 |

> 采集产物 = `Data/flow/original_*`、`Data/auxcollection/startup/ScreenChanges.txt`。
> 这些目录是 `.gitignore` 的，所以**逐字抄进代码里就是留档**。

### 3.1 左栏 45 行诊断（`DIAGNOSTIC.rows`）

| # | 文字 | 前缀 | 出处 |
|---|---|---|---|
| 1 | `[CONS] BOOT-UP INITIALIZED` | CONS | V |
| 2 | `[CORE SYS] NEW INSTRUCTIONS ACCEPETED...` | CORE | V |
| 3 | `[PRI MAINFRAME] PRIMING SYSTEMS > CONSOLE COMMAND NETWORK TO EXPERIMENTAL ‘SUBSPACE’ REACTOR INFASTRUCTURE` | PRI | V |
| 4 | `[PRI MAINFRAME] CB LASER CONSOLE > READY` | PRI | V |
| 5 | `[PRI MAINFRAME] MAIN REACTOR CONSOLE > READY` | PRI | V |
| 6 | `[PRI MAINFRAME] THERMAL CONSOLE > READY` | PRI | V |
| 7 | `[PRI MAINFRAME] ALT REACTOR CONSOLE > READY` | PRI | V |
| 8 | `[PRI MAINFRAME] ELECTRIC GRID CONSOLE > READY` | PRI | V |
| 9 | `[PRI MAINFRAME] H.D.E.F EMITTERS > READY` | PRI | V |
| 10 | `[PRI MAINFRAME] ALL SYSTEMS PRIMED` | PRI | V |
| 11 | `[CORE SYS] RUNNING PRELIMINARY DIAGNOSTICS...` | CORE | V |
| 12 | `[PRI MAINFRAME] COMPUTATIONAL FACILITIES > OK` | PRI | V |
| 13 | `[PRI MAINFRAME] CBL REACTION STABILIZATION SYSTEM > OK` | PRI | V |
| 14 | `[CORE SYS] CONTINGENCY PROTOCOLS > STANDBY` | CORE | V |
| 15 | `[PRI-MAINFRAME] CONSOLE CONTROL SYSTEMS > OK` | PRI | V |
| 16 | `[PRI-MAINFRAME] REACTOR SENSOR ARRAYS > OK` | PRI | V |
| 17 | `[PRI-MAINFRAME] GENERAL MONITORING SYSTEMS > OK` | PRI | V |
| 18 | `[CORE SYS] PRELIMINARY DIAGNOSTICS COMPLETED` | CORE | V |
| 19 | `[LOG]` | LOG | V |
| 20 | `[LOG] M.E.T.U STATUS - FULLY OPERATIONAL` | LOG | **G** |
| 21 | `[LOG] E-VENT STRUCTURES PRIMED` | LOG | **G** |
| 22 | `[LOG] PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM` | LOG | **G** |
| 23 | `[LOG] CALIBRATING REACTOR SENSOR NETWORK` | LOG | **G** |
| 24 | `[LOG] ISOTOPE E COOLANT LOOP > 3 / 3 PUMPS RESPONSIVE` | LOG | **R** |
| 25 | `[LOG] COMPUTATIONAL BENCHMARKS UNSATISFIED` | LOG | **G** |
| 26 | `[LOG] QPU ARRAY > 6 / 6 NOMINAL` | LOG | **R** |
| 27 | `[LOG] H.D.E.F FIELD INTEGRITY > 100 %` | LOG | **R** |
| 28 | `[LOG] PRESSURE EXTRACTION ASSEMBLY > AUTHORIZED` | LOG | **R** |
| 29 | `[LOG] CHAMBER ATMOSPHERE > SEALED` | LOG | **R** |
| 30 | `[LOG] GEIGER ARRAY > 14 RAD UNITS, WITHIN NOMINAL` | LOG | **R** |
| 31 | `[LOG] CONTROL ROOM SHUTTERS > RETRACTED` | LOG | **R** |
| 32 | `[LOG] PRIMARY MAINFRAME > TESSERACT LINK ESTABLISHED` | LOG | **G** |
| 33 | `[LOG] OPERATOR CREDENTIALS VERIFIED` | LOG | **R** |
| 34 | `[LOG] REACTOR STATE > COLD, NO FISSION PRODUCT INVENTORY` | LOG | **R** |
| 35 | `[LOG] STATE 1 THRESHOLD 5600 F / STATE 2 17500 F` | LOG | **R** |
| 36 | `[LOG] CONTROL RODS > NOT INSTALLED` | LOG | **R** |
| 37 | `[LOG] CBL ARRAY 1..3 > STANDBY` | LOG | **R** |
| 38 | `[LOG] HDEF GENERATOR > PERIODIC SHUTOFF ADVISED` | LOG | **G** |
| 39 | `[LOG] NOTICE: COOLANT SENSING TENDS TO BE UNRELIABLE` | LOG | **G** |
| 40 | `[LOG] SHIFT QUOTA > 512 / 1024 / 3072 UNITS` | LOG | **R** |
| 41 | `[LOG] ` （空） | LOG | V |
| 42 | `[ERR] Good luck, You'll need it.` | ERR | V |
| 43 | `[CORE SYS] INSTRUCTIONS COMPLETED` | CORE | V |
| 44 | `[LOG] THIS SYSTEM IS OWNED AND OPERATED BY THE SYNTHESIS MANFUACTURING CORPORATION - UNAUTHORIZE USAGE WILL RESULT IN SEVERE LEGAL REPROCUSSIONS` | LOG | V |
| 45 | `[LOG] THIS WINDOW WILL NOW CLOSE` | LOG | V |

**统计：V = 24 行，G = 8 行，R = 13 行，共 45 行。**

> **拼写错误是故意留的**：`ACCEPETED`、`INFASTRUCTURE`、`MANFUACTURING`、
> `UNAUTHORIZE`、`REPROCUSSIONS`、`PRIMAIRY` —— 这些**不是打错的**，
> 采集里就是全大写、连拼写错误都照抄的游戏自己的语气。改"对"了才是改错了。

### 3.2 右栏 6 条开机日志（`BOOTLOG`）

**全 6 条 = V**，逐字恢复自采集（`BootFrame.LogFrame.TitleText1..6`）：

1. `QUICK BOOT UP INITIALIZED`
2. `CONNECTION TO PRIMAIRY MAINFRAME ESTABLISHED`
3. `CONNECTION TO REACTOR INFASTRUCTURE NETWORKS ESTABLISHED`
4. `SYSTEM DIAGNOSTICS COMPLETED`
5. `BOOT UP COMPLETED`
6. `RESUMING NORMAL OPERATION`

### 3.3 三条规格卡（`SPECS`）—— 全片唯一的"不是游戏原文"

1. `NO CONTROL RODS`
2. `THREE INDIRECT SYSTEMS`
3. `ONE SHIFT TO GET IT RIGHT`

**这三条是宣传片自己的文案**，不来自任何采集。
内容写的是游戏本身，而这三句都有出处（Wiki 反复确认过：**不存在控制棒**；
三大控制手段 = 环境压力 / CBL / Isotope E）。但它们**不是游戏里的字符串**，
所以在这里明确标出来，不混进上两张表。

### 3.4 右下的 4 条读数（`GAUGES`）

**数字是"冷堆"的量级** —— 开机的读数本来就该长这样。

| 条 | 标签 | 终点 | 起点 | 说明 |
|---|---|---|---|---|
| g1 | `QPU ARRAY` | 6 / 6 | 0 | 6 个 QPU 是满的 |
| g2 | `H.D.E.F INTEGRITY` | 100 % | 64 | 爬上去再定格 |
| g3 | `COOLANT LOOP` | 3 / 3 | 0 | 3 台冷却泵全响应 |
| g4 | `CHAMBER PRESSURE` | 0 PSI | 0 | **故意不动** —— 冷堆压力真的是 0，它空着才是对的 |

### 3.5 别的地方出现的字

- 栏头：`SUBSPACE REACTOR MANAGEMENT NODE` / `BOOT LOG`
- 底栏：`NODE ICARUS-04` · `CORE COLD` · `QUOTA 512 / 1024 / 3072` · `CONTROL RODS NOT INSTALLED`
  （`ICARUS-04` 这个节点号是**编的**；配额三档来自游戏）
- HUD：`SYNTHESIS MANUFACTURING CORPORATION` / `INSTALLATION OVERSEER TERMINAL / REV 04` / `REC` / 时间码
- 落款：`ICARUS INSTALLATION · SECTOR 04 · REPORT FOR DUTY`（**编的**）

---

## 4. 素材出处（`intro/assets/`）

全部来自本仓库，**复制**（不是引用）过来 —— 因为原始目录名里带空格
（`TRG Sounds & Images pack`），引用会踩 URL 编码。

| 文件 | 来自 | 用在哪 | 出处 |
|---|---|---|---|
| `sm-logo.png` | `TRG Icons/SMLogo_17506216869.png` | 厂标卡 + 左下角水印 | V（美术资产） |
| `sm-core.png` | `SM Icons/SMER Solid Color_15875258759.png` | 标题卡的堆芯徽记 | V |
| `nested-hex.png` | `Logos/nested-hexagons_17370477069.png` | 标题期的背景六边纹 | V |
| `ring.png` | `Simple Icons/Thin Circle Outline_483231231.png` | 厂标入场时收拢的"叮"环 | V |
| `stripes.png` | `Textures/perfectwarningstripesflip_80549325.png` | 标题条的危险条纹 | V |
| `px.png` | `asstes/texture/PurewWhite16x16.png` | 静态噪点用的 16×16 白块（`image-rendering:pixelated`） | V |
| `hex.png` | `Simple Icons/Simple Hexagon_6793543531.png` | —— | **备用，本版未引用** |
| `alert.png` | `Simple Icons/alert_97628760291739.png` | —— | **备用，本版未引用** |

---

## 5. 怎么知道它真的对（验证）

**"我打开看了觉得没问题"不是证据**（CLAUDE.md §4.4）。**片子有两半，
分别只有一种检查器能持有** —— 把它们分开写，是因为合起来会互相冒充：

| 检查器 | 持有什么 | **结构上看不见什么** |
|---|---|---|
| `_tools/intro_check.js`（桩 DOM） | **时间与逻辑**：每一刻该在的东西在不在 | **排版**。桩 DOM 里 `getBoundingClientRect()` 是假的，**没有布局可错** |
| `_tools/intro_render.js --check`（真无头 Chrome） | **布局**：位置 / 尺寸 / 有没有被裁掉 | 需要"页面里根本没有的东西"的断言 |

```
D:\nodejs\node _tools/intro_check.js               # 24 ok / 0 failed
D:\nodejs\node _tools/intro_render.js --check      #  5 ok / 0 failed
python         _tools/intro_mutants.py             # 10/10 变异各红在自己那条 + 1/1 FOLLOW 绿
```

- **`intro_check.js`** 造一个刚够用的假 DOM，把 `index.html` **自己的 `<script>` 字节**
  求值（不是副本），然后在选定的时刻把内联样式读回来。断言分两类：
  **COVERAGE**（第 t 秒这一幕该在，因为分镜这么说）和 **GUARD**（这个缺陷不许回来）。
  另外整条时间轴按 0.05 s 扫一遍，断言没有任何 `NaN`/`undefined` 进到样式里。
- **`intro_render.js --check`** 让浏览器在 t=3.0..12.5 上每 0.25 s 采一次，
  读回 `getBoundingClientRect()` 与行高，判 5 条 `L*` 断言。
  **浏览器是尺子，判定写在 Node 里** —— 量了又判的人会悄悄改判据（DECISIONS_2 309）。
- **`intro_mutants.py`** 驱动**两个** harness，每个变异断言**指定那一条**变红。
  **只红一条才说明断言是精确的。** 另有一类 **FOLLOW**：必须**保持绿**
  （`diag-rowsize`：行高 27→40）—— 一条对什么都会红的检查和对什么都不会红的检查一样没用。

**本轮真的抓到并修掉的四个片子缺陷**（前三条的细节见 PROGRESS Phase 91，
第四条是 Phase 92 新发现的两个之一）：

1. **开机令永远停在半句** —— 55 ms/字打 25 个字要 1.375 s，而面板 1.60 s 就盖上来，
   片子永久显示 `[CONS] BOOT-UP INITI`，**而且没有任何东西会报错**。
2. **黑场开始时外框还亮着一半** —— 收屏窗口原来收到 16.5，越过了 16.40 的黑场起点。
3. **片子从来没真的黑过** —— 黑场窗口是 34.95–35.25，尾巴落在 35.0 的片长**之外**，
   最后一帧只有约 17% 黑。
4. **左栏前 7 秒是空的**（Phase 92，**只有真浏览器看得见**）—— `#diagList` 锚在
   `bottom:0`，而它 1215px 高、窗口只有 630px，于是块的顶端落在 **−346px**；
   滚动变换又在往上推同一块东西，**两个位移相加而不是抵消**。实测
   t=4.5 有 9 行亮着而**可见 0 行**、t=6.0 有 18 行而**可见 0 行**。
   **桩 DOM 那 24 条断言全程全绿** —— 每一行 `opacity` 确实是 `1`。
   **读实例状态 ≠ 读屏幕**（CLAUDE.md §0.2 的第七张脸）。

**验不到的（分开写）**：字体/混合模式的像素级效果仍没有独立复验；
真实鼠标拖进度条与键盘快捷键只做过代码审查；只在 Chromium 上看过。
**渲染出来的 mp4 是另一条独立通道**（§7）：帧是从那个文件里**抽回来重新看**的。

---

## 6. 音频

**本片头无声。** 操作员明确要求：不要用 `asstes/` 里的音乐，也不需要音乐。
`intro/index.html` 第 6.13 节是**故意空的**，并在注释里写好了接法：
将来若要加音效，一律由 `t` 驱动（`[at, until]` 窗口 + 记住窗口序号），
**不许写"我是不是已经放过这个了"** —— 那是一个状态机，会让拖进度条变成随机行为。
ogg 素材在 `TRG Sounds & Images pack/HG & SHIFTS Sounds/` 里现成有。

---

## 7. 视频版：`intro/THE_REACTOR_GAME_intro.mp4`（Phase 92）

```
D:\nodejs\node _tools/intro_render.js                    # 全片 -> intro/THE_REACTOR_GAME_intro.mp4
D:\nodejs\node _tools/intro_render.js --at 0,3.3,19.5    # 只出这几帧 PNG（不动 mp4）
D:\nodejs\node _tools/intro_render.js --check            # 只跑排版断言，不出 mp4
```

**它不是录屏，是逐帧驱动的。** 因为整片是 `render(t)`，渲染就是
「`render(i/fps)` → 截图 → 下一帧」：**没有时钟要抢、没有帧会丢、跑两遍出同一个文件**。
实时抓屏只会更差 —— 它采样的恰是片子特意不依赖的那个节奏（页面自己的 `rAF`）。

| 项 | 值（`ffprobe` 量出来的，不是算的） |
|---|---|
| 尺寸 / 编码 | 1920×1080、H.264 **High**、`yuv420p` |
| 帧率 / 帧数 | 30 fps、**1051 帧写入 = 1051 帧读回** |
| 时长 | **35.033 s**（= 1051/30） |
| 体积 / 码率 | **5,932,568 字节（5.66 MiB）** / 1.35 Mbps |
| 音频 | **无** |

**三个必须做对的地方**（都在 `intro_render.js` 的注释里）：

1. **页面的自动播循环要在它存在之前就被掐掉** —— `Page.addScriptToEvaluateOnNewDocument`
   把 `requestAnimationFrame` 打成空函数，**先于页面脚本**注入。否则那个循环会一直
   在背后覆写已经驱动的帧（两个写入者同时在跑，而代码读起来完全正常）。
2. **视口钉成恰好 1920×1080**（`Emulation.setDeviceMetricsOverride`）→ `fit()` 的
   scale 恰好 1，截图就是设计空间本身，没有黑边要裁。
3. **播放器是 UI 不是片子** —— `#player` / `#bigplay` / `#hint` 渲染前 `display:none`。

**成本**：抓 1051 帧 **331 s**（3.17 fps）+ 编码 **39 s** ≈ **6.2 分钟**。

**只有片子那一刻的字节变了，mp4 才会变** —— 这是纯函数的钱在最后一步兑现
（DECISIONS_2 303 / 310）。中间那 1051 张 PNG 是过程产物，跑完自己删，
且在 `.gitignore` 里（`_tools/_frames/`）；**进仓库的是 mp4**。
