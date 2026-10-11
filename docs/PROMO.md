# PROMO —— 宣传片怎么做的（Phase 120）

> 一句话：`promo/index.html` 是一部 **纯 `render(t)`** 的 76 秒片子，
> 由 `_tools/intro_render.js` 用无头 Chrome 逐帧拍成无声 mp4，
> 再和**原版 `ReactorStartup.mp3`** 拼出来的音轨合成。

---

## 1. 文件都在哪

| 文件 | 是什么 |
|---|---|
| `promo/index.html` | **片子本体**。1920×1080，一个 `render(t)` 决定第 t 秒长什么样 |
| `promo/shots/*.jpg` | 15 张**截图底板**（Edit 模式下 `screen_capture` 拍的，1248×600） |
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
SILENCE run 9.70..16.20 s (6.50 s)
BIGGEST RISE 33.6 dB at t=16.25 s (-55.5 -> -21.9 dB)   ← 点火那一帧
```

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
这一轮用的 `Workspace.PROMO_LIGHTS`（8 个 0.2³ 的 Part 挂 PointLight）就是用完即删的，
删完量了 `gone=true`（CLAUDE.md §0.12 第 3 条：Workspace 里的东西正在渲染，动它就是改世界）。
