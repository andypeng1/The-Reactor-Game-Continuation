# PROMO —— 宣传片怎么做的（Phase 120）

> 一句话：`promo/index.html` 是一部 **纯 `render(t)`** 的 76 秒片子，
> 由 `_tools/intro_render.js` 用无头 Chrome 逐帧拍成无声 mp4，
> 再和**原版 `ReactorStartup.mp3`** 拼出来的音轨合成。

---

## 1. 文件都在哪

| 文件 | 是什么 |
|---|---|
| `promo/index.html` | **片子本体**。1920×1080，一个 `render(t)` 决定第 t 秒长什么样 |
| `promo/shots/s*.jpg` | 15 张**巡礼底板**（Edit 模式下 `screen_capture` 拍的，1248×600） |
| `promo/shots/ig*.jpg` | 5 张**点火底板**（同机位的亮/暗对照，§6） |
| `promo/assets/*.png` | 素材图标（METU / 激光 / 泵 / 六边形标记等） |
| `promo/THE_REACTOR_promo.mp4` | **成品**（画面 + 音乐），1920×1080 / 30 fps / 76.000 s |
| `promo/THE_REACTOR_promo_silent.mp4` | 无声母版（渲染器的原始产物） |
| `promo/_bed.m4a` | 拼出来的音轨（下面 §3） |
| `_tools/intro_render.js` | 渲染器（`intro` 那部片子共用，本片没改它一行） |

**渲染器不用改**：第二部片子就是**又一个遵守同样契约的 HTML**。

```bash
# 无声母版（~22 分钟）
node _tools/intro_render.js --page promo/index.html --out promo/THE_REACTOR_promo_silent.mp4 --fps 30
# 只拍几帧看画面 / 只读值（几秒）
node _tools/intro_render.js --page promo/index.html --at 16.2,19.0 --eval '<expr>'
```

`--at` 出 PNG，`--eval` 在那几个时刻求值 —— **两样都要做**：
图证明「看起来对」，读数证明「真的是那个值」（CLAUDE.md §0.14b）。

---

## 2. 时间轴（76.00 s）

| 时间 | 内容 |
|---|---|
| 0.00–5.60 | 远景 `s09_est_far`（cold open，无字幕） |
| 5.60–9.70 | 标题 **THE REACTOR / 反应堆 · 值班员** |
| **9.70–16.20** | **静音段**：画面推到全黑，启动日志逐行打出（13 行） |
| **16.20** | **★ 反应堆点火**：白闪 + 舱体出现，日志第 14 行 `COMBUSTION LASERS FIRING` |
| 15.75–71.04 | 12 个 4.44 s 的巡视镜（CBL / 舱体 / Isotope E / E-Vent / PEA / 控制室 / 主控台 / M.A.S.S / METU / Icarus / 熔毁） |
| 71.04–76.00 | 尾卡 **THE REACTOR** |

字幕用的是**游戏自己的原文**（`docs/ORIGINAL_UI_TEXT.md` §1 的 23 行启动日志），
不是编的。

---

## 3. 音乐：为什么是两个文件、为什么是这么拼的

**要的是原版 `asstes/music/ReactorStartup.mp3`**（2025-01-16，263.89 s），
**不是** `ReactorStartup_Remix.mp3`（那是上一轮我自己做的）。这是操作员当场更正的一条。

两条音轨的结构**不一样**，所以对齐点必须重新量：

| | 静音段 | 声音回来的那一瞬 |
|---|---|---|
| Remix（我做的） | 10.30 → 16.20（5.90 s） | +18.8 dB @ 16.20 s |
| **原版（要用的）** | **0.00 → 2.25 s** | **+34.5 dB @ 2.30 s** |

原版**只有开头那一处静音**，之后是一路不断的持续音（50 ms RMS 一帧一帧扫过 263.9 s，
`-30/-35/-40 dB` 三个阈值下最长静音run 都是 **0.00..2.25**）。它**没有**中段的静音。

而片子要的是「**先有音乐 → 静音 6.5 s → 声音回来正好是点火**」。
原版给不了 6.5 s 的静音，所以**用原版拼一条音轨**（`promo/_bed.m4a`）：

```
[film 0.00- 9.70]  原版 02.30-12.00   （从它自己声音起头的地方开始，省掉开头 2.3 s 静音）
[film 9.70-16.20]  纯静音 6.50 s      （这是真的零，不是压低）
[film16.20-76.00]  原版 12.00-71.80   （接回原版，和 A 段连着）
```

```bash
ffmpeg -y -i asstes/music/ReactorStartup.mp3 -filter_complex "\
[0:a]atrim=start=2.30:end=12.00,asetpts=PTS-STARTPTS,afade=t=out:st=9.42:d=0.28[s1];\
anullsrc=r=44100:cl=stereo,atrim=start=0:end=6.50,asetpts=PTS-STARTPTS[s2];\
[0:a]atrim=start=12.00:end=71.80,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.05,afade=t=out:st=57.30:d=2.50[s3];\
[s1][s2][s3]concat=n=3:v=0:a=1[out]" -map "[out]" -ac 2 -ar 44100 -c:a aac -b:a 192k promo/_bed.m4a
```

**A 段和 C 段是连着的**（`2.30→12.00` 接 `12.00→71.80`），所以听起来就是原版走到 12.00 s
处被插进 6.5 s 静音、然后从原处接着走。**只有一次「没声音→有声音」**，就在 16.20。

合成：

```bash
ffmpeg -y -i promo/THE_REACTOR_promo_silent.mp4 -i promo/_bed.m4a \
       -map 0:v -map 1:a -c:v copy -c:a copy -shortest promo/THE_REACTOR_promo.mp4
```

**验收（量成品文件本身，不量中间物）：**

```
silencedetect   silence_start 9.693492 | silence_end 16.201383 | duration 6.507891
volumedetect    整片 mean -15.1 | max -0.0
                静音段 11–15 s  mean -91.0   ← 数字零，-91 是量化底
                点火后 21–25 s  mean -18.1 | max -5.8
跨 16.20 的两个窗（互不相交）：16.05–16.20 = -91.0 dB ，16.22–16.37 = -19.5 dB
```

**「至少升 71 dB」**：静音段是真正的零，所以那个 -91.0 是**底不是值**，只能给下界。

> **★ 一处复现不了的旧数**：本节原来记的是 `BIGGEST RISE 33.6 dB at t=16.25 s`。
> 2026-10-12 按记忆重写那个度量（`astats:reset=1` + `ametadata=print` 抽 50 ms RMS 找最大跳变），
> **成品和 `_bed.m4a` 给出逐字节相同的输出**，两个都报 `BIGGEST RISE 63.5 dB at t=0.00 s`
> —— **同一个数出现在两个不同文件上，说明错的是尺子**（CLAUDE.md §0.20 同族）。
> 那个 33.6 dB **这轮没有复现**，因此**没有被改写成新数**，只被上面两条可复现的量取代；
> 「当时的量法找不回来了」这件事一并留在这里，而不是把行删掉（取舍 **507**）。

**验收（画面）：** 从**成品**里 `-ss` 抽五帧（不是浏览器截的，「渲染器说对」和
「交付的这个文件对」是两件事），见 §6.4。

---

## 4. 两个坑

**① 每切一刀黑一帧。** 原来每镜的透明度写的是
`ramp(p, t0, t0+XF) * (1 - ramp(p, t1-XF, t1))` —— 上一镜在 `[t1-XF, t1]` 淡出，
下一镜在 `[t1, t1+XF]` 淡入，**两个窗口不重叠**：切点那一帧两镜都是 0，
于是 12 个切点各黑一帧、前后各 0.45 s 变暗。**改成一个跨在切点上的窗口**
（`ramp(p, t0-XF, t0+XF) * (1 - ramp(p, t1-XF, t1+XF))`）后，
相邻两镜的淡入淡出落在**同一区间、互为补数**，合成恒等于 1。
探条读数：切点处 `sum=1.00 | max=0.50`（两镜各半），不再有黑帧。

**② 渲染器 `rmSync` EPERM。** 第一次全量渲染死在
`FAIL EPERM, Permission denied: ...\_tools\_frames`。原因不是权限坏：
**那次会话 shell 的工作目录恰好就是 `_tools/_frames`**，而 Windows 拒绝删除
任何进程当前所在的目录。`cd` 到工程根再跑就好了。

---

## 5. 截图是怎么来的

Edit 模式下用 `screen_capture` **显式给 `camera_position` + `look_at_position`** 拍的
（CLAUDE.md §0.14：官方那个工具现在给不同相机位会出不同且正确的画面）。
要开灯 / 开粒子的话，**临时件必须删掉并回头验证删掉了** ——
巡礼那一轮用的 `Workspace.PROMO_LIGHTS`（8 个 0.2³ 的 Part 挂 PointLight）就是用完即删的，
删完量了 `gone=true`（CLAUDE.md §0.12 第 3 条：Workspace 里的东西正在渲染，动它就是改世界）。

**点火那五张（§6）用的是场景自己的灯，不是补光** —— 要的是「亮起来」这件事本身，
补光拍不出它。所以这一轮动的是 **`NeonPart.SurfaceLight.Enabled`**（舱内 98 盏）
和 **`SurfaceGui.MonitorUI.Enabled`**（七台监视器，**默认是 false**，
只把 `MainMonitorFrame.Visible` 置 true 是不够的 —— 那是我第一个假阴性）。
拍完逐组还回去，读数写在 §6.3。

---

## 6. 点火级联（16.20 → 19.45）

**上一版的问题**（操作员 2026-10-12）：「开机腔室得有点变化吧？开灯、CBL 开机什么的
（注意有很多东西要动比如**子空间预测**）你这个开机啥都没有是什么意思」。
白闪只说明"有事情发生"，**没有一样东西在画面上是"刚启动"的**。

片子是**底板结构**，所以开灯**不能靠调色** —— 一张没开灯的实拍拧亮度只会变成过曝的暗图。
**必须去拍**。五张 `ig1..ig5` 是**同机位**拍的两两对照：

| 板 | 内容 | 抓拍时动的是什么 |
|---|---|---|
| `ig1_chamber_off` | 主舱全景，灯全关 | 什么都没开 |
| `ig2_chamber_on` | **同一个相机**，灯全开 | 98 盏 `NeonPart` 的 `SurfaceLight` |
| `ig3_cbl` | CBL-1 特写，出射 | CBL 阵列 |
| `ig4_core` | 堆芯俯视，临界 | 那颗发青的盘 |
| `ig5_monwall` | 控制室监视器墙上电 | 七台的 `SurfaceGui.MonitorUI.Enabled` |

**ig1/ig2 是"真的少了一层黑"**，不是把 `brightness` 从 1.04 拧到 1.10 ——
这是这五张存在的理由，也是它们必须**实拍**的理由。

### 6.1 三条规则

```js
const IG_XF = 0.30;
op = ramp(p, t0-IG_XF, t0+IG_XF) * (1 - ramp(p, t1-IG_XF, t1+IG_XF));   // 和 5.1 同一套
```

**① 覆盖率是「和」不是 `max`**（取舍 502）。窗口跨在切点上、互为补数，
所以交叠处两边加起来恒等于 1，五条的和就是一个合法的 0..1 覆盖率。
`max()` 会在每个切点掉到 0.5，那 0.6 秒里巡礼的说明条会从缝里漏出来。

**② 图像可以溶，文字不能溶**（取舍 503）。说明是**一个字块** `#ignCap`，
跟着**主导的那张图**（`op > ignBest`）**硬切**。第一版每张图各带一个说明跟着淡 ——
19.45 那一帧实测叠成了两行大字（「CORE IGNITION」+「MONITOR NETWORK」各 50%），
**而探条的读数全对**。所以：**探条说对不算对，图说对才算**（§0.14b）。

**③ 字比图早退 0.15 s**：级联最后一张开始溶（19.15）时字已经走完，
巡礼第一镜的说明条从同一刻起从 0 升上来 —— **两条字从来没有同时存在过**。
（角标 `#metaShot` 用的是**同一个门**，否则会出现「大字没了、角标还在报 MONITOR NETWORK」。）

### 6.2 两张脸，都不报错

- **容器没有宽度 → 文字每词一折**（取舍 504）：`#ignCap` 只写了 `left/bottom`，
  0×0 的容器让 `left:0`+auto 宽的子件**每个词边界都折**（实测盒子 287×**121**）。
  修：容器 `right:0`、子件 `white-space:nowrap`。**量法是盒子的"高"。**
- **父层 `transform` → 子件 `z-index` 出不去**（取舍 505）：`#ignite` 带 `scale()`，
  自成一个层叠上下文，整层落在 `#scrim`（z-index 4）底下，白字被角雾压成**灰字**。
  修：把字块**搬出 `#ignite`**，去做 `#caps` 的邻居、和它同一个 z-index
  （顺带赚一条：说明文字本来就不该跟着镜头推）。

### 6.3 抓拍完还回去的读数

```
METULights 32/32 on   （原版的样子，见取舍 506）
其它组 0
Workspace.PROMO_LIGHTS gone = true
```

上一轮记的「98 盏」被当成了全集 → 按 98 关，量回来 **130**。
**一个总数藏得住"是哪一组亮着"**：动手前先记**逐组**读数。

### 6.4 交付件抽帧（`ffmpeg -ss <t>`，从成品里抽）

| 帧 | 大字 | 角标 | 看什么 |
|---|---|---|---|
| `f16.85` | `CHAMBER LIGHTING` / 舱内照明 ×98 · 上线 | `CHAMBER LIGHTING · IGNITION` | **单行**、白字 —— 504/505 两条都修上了 |
| `f17.45` | `CBL ARRAY` / 化学泵浦激光 · 出射 | `CBL ARRAY · IGNITION` | 一条说明 |
| `f18.40` | `REACTOR CORE` / 堆芯 · 临界 | `REACTOR CORE · IGNITION` | 一条说明 |
| `f19.15` | （巡礼那条，**实测 `caps=0.0278`**） | `CORE IGNITION · 01 / 12` | **交接点**：级联的字已走 |
| `f19.45` | `CORE IGNITION` / 堆芯点火 · 5000 PSI · 9420 °F | `CORE IGNITION · 01 / 12` | **那个 bug 的原帧，现在只有一条字** |

**每一帧的角标都和大字同源**（503 那条用的是同一个门）：19.45 的角标报巡礼的 `01 / 12`，
所以那一条大字来自**巡礼**的说明条，不是级联漏下来的 —— **这就是用角标反证大字来源的用法。**

**★ 帧名和探条的时刻差不到一帧，两边都不是错的。** `-ss 16.85` 取的是**覆盖 16.85 的那一帧
（`16.8667`）**，而字块在切点上**硬切** —— 于是帧上是**后一档**的名字。实测：

```
t=16.8333  字块 "Main Chamber"      op=0.5278,0.4722
t=16.8667  字块 "Chamber Lighting"  op=0.4722,0.5278   ← f16.85 抽到的是这一帧
t=17.4667  字块 "CBL Array"                            ← f17.45 抽到的是这一帧
```

**抽帧的图和探条的读数用的是两个不同的时刻** —— 并排读会读成两处矛盾。
