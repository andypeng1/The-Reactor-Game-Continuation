"""One-shot: write Phase 49 and the Phase 48 correction into the disk docs.

Same discipline as the other one-shot scripts: every replacement is asserted to
have landed exactly once, so a silent no-op cannot pass as a successful edit.
The docs are the only copy (CLAUDE.md 0.0), so a half-applied patch is worse
than no patch.
"""
import re
import sys
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')


def patch(path, subs, append=None):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    before = len(text)
    for i, (pat, new, label) in enumerate(subs):
        n = len(re.findall(pat, text, re.S))
        if n != 1:
            sys.exit('%s: %s matched %d times, wanted exactly 1' % (path, label, n))
        text = re.sub(pat, lambda m: new, text, count=1, flags=re.S)
    if append is not None:
        if not text.endswith('\n'):
            text += '\n'
        text += append
    p.write_text(text, encoding='utf-8', newline='\n')
    print('%-26s %7d -> %7d bytes' % (path, before, len(text)))


# ============================================================== PROGRESS.md ==
PROGRESS_APPEND = """
---

## Phase 49 — 温度是怎么算的：`m.fluct` 就是那一步  [PARTLY DONE]

**日期：** 2026-09-26 约 23:40。**触发：** 用户问「温度计算什么的能搞出来的吗？」。
**对象：** `Data/flow/original_260926-230049`，**只读，一个字节都没改**。
**一句话结论：** 结构能定死，增益只到量级，**公式拿不到** —— 每一条都有数。
分析脚本是 `_tools/_attic/scratch/temp_shape.py` / `temp_fit.py` / `temp_fit2.py` /
`temp_seg.py` / `temp_tick.py` / `temp_fluct.py`（草稿，一次性，留在原处当证据）。

### 49.1 `m.temp` 不是一个连续状态，是一个 tick 的输出

- 全文件 `m.temp` 一共变过 **393** 次；其中 **391 次满足
  `temp(下一拍) − temp(这一拍) == m.fluct`，逐字节相等**。剩下 2 次是读序错位
  （一行同时带了上一 tick 的温度和这一 tick 的 `fluct`：t=177.96、t=501.40）。
- 所以 **`temp(t+1) = temp(t) + m.fluct(t)`**。`m.fluct` 不是温度旁边那个「稳定度」，
  **它就是那一 tick 的温度增量**；`m.temp` 是它的累加。校准台上的 NET STABILITY
  给操作员看的就是这个导数 —— 难怪游戏敢让操作员去「判断稳定度」。
- tick 周期（事件间隔）：中位数 **1.79 s**，众数 2.0 s，p10 1.51 / p90 2.04，
  采样约 3.3 Hz，所以抖动就是 ±一拍。**定 ~1.8 s。**
- `m.temp` / `m.press` / `m.fluct` 三个标签**同一行一起变，从不分开** ——
  一个物理步写三个标签。**所以任何「每采一次算一次导数」的做法都是在拟合重绘时刻表**：
  第一次拟合这么干，得到 R² = 0.084、冷却项的符号是反的；改成按 tick 做，同一份数据
  给出 R² = 0.33、符号全对。
- **温度不是一阶惯性环节。** t=560.78–610.97，cblPct=75 / cool=0 / fan=3，增量是
  `+144 +289 +229 +205 +287 +147 +279 … +241 +214 +157` —— 在**时间上平**，
  在**温度上**也平（6625 → 13224 F 一路涨）。一阶惯性应该随接近平衡而收窄，它没有。

### 49.2 能定到的：结构 + 量级

最小二乘，391 个 tick，目标 = `m.fluct`（单位 F/tick）：

| 项 | 系数 ± 标准误 | 读作 |
|---|---|---|
| 常数 | −220.9 ± 43.8 | |
| `ΣcblPct` | **+5.05 ± 0.42** | 每 1% CBL 输出 |
| `c.coolSum` | **−58.2 ± 9.7** | 每台冷却泵（这一趟只用到 1 档） |
| `c.fanCount` | **−32.8 ± 9.4** | 每个风扇 |
| `m.temp` | −0.0068 ± 0.0044 | **与 0 无法区分** |

R² = **0.328**，残差 sd **146 F/tick**。**模型解释了漂移，没解释波动。**
`m.temp` 这一项与 0 无法区分是这一份里最硬的一条：**在 6600–14000 F 这段，
温度本身不产生回正力 —— 温度是个积分器。**

### 49.3 设置对照表（不假设任何模型，直接取中位数，F/tick）

| cblPct | cool | fan | n | 中位 | 温度区间 |
|---|---|---|---|---|---|
| 175 | 2 | 3 | 6 | +246 | 13119..13941 |
| 150 | 3 | 6 | 4 | +34 | 9324..9496 |
| 75 | 0 | 1 | 9 | +13 | 11818..12045 |
| 75 | 0 | 2 | 48 | +16 | 11786..12596 |
| 75 | 0 | 3 | 48 | **+174** | 6916..13224 |
| 75 | 0 | 4 | 8 | +248 | 11088..12752 |
| 75 | 1 | 3 | 72 | +52 | 7344..12980 |
| 75 | 1 | 4 | 44 | +14 | 9113..13556 |
| 75 | 2 | 3 | 56 | −38 | 6625..13963 |
| 75 | 2 | 4 | 68 | −49 | 9069..13716 |
| 75 | 3 | 3 | 4 | −124 | 8892..9341 |
| 45 | 0 | 6 | 8 | **−619** | 7978..12386 |

最后一行是 Equinox 之后的衰减，不是常规设置。**表里自己就自相矛盾**
（`cool=0 fan=2` 是 +16 而 `cool=0 fan=3` 是 +174），原因是每一行的操作员都把控制
动成了对温度的反应 —— 见 49.5(b)。

### 49.4 第二个锚：冷启动确实在文件里，而且和监视器接得上

`s.Core.TemperatureVal`：`0` → `9420 F`，**96.6 s**，**≈ 98 F/s**（三个 CBL 都在 Lvl 4
—— 也就是 `c.cbl*Pct` 各自 100，`Σ = 300`；冷却 1 档、风扇 4 个）。
它最后一拍是 **t=97.90 的 9420**；`m.temp` 第一拍是 **t=98.77 的 9330**。
差 90 F / 0.87 s = **103 F/s**，和 98 F/s **同速**。
**两个源在 t≈98 接得上** —— 这同时说明两件事：`s.Core.TemperatureVal` 到 t=97.90 为止
可信，`m.temp` 从 t=98.77 起可信。**冷启动那半场一直在这份文件里。**

### 49.5 拿不到的，以及为什么

**(a) 增益不可外推。** 冷启动那段实测 **+180 F/tick**（98 F/s × 1.8 s），
49.2 那个拟合给 **+1104 F/tick**，**差 6 倍**。CBL 输出从 75% 翻到 300%，
净加热几乎没变 —— **这个关系是饱和的，线性模型只在拟合过的带里成立。**

**(b) 控制器是反馈，不是实验。** 操作员每一次动控制都是对温度的回应，所以回归量
和被解释量共线。最直接的证据：池化拟合里 `coolSum·T` 的系数是**正的**（`+0.0101`），
字面意思是「冷却越强、高温时掉热越少」—— **物理上反的**。那不是发现的物理，是共线性。
**这一条是整件事的根**：一次有人开着的班次不是阶跃响应实验。

**(c) 回正力定不下来 —— 而且这个测试是干净的。** 在**固定设置内部**做，控制混叠
就影响不到：`(75,2,4)` 跨 9069–13716 F 这 4600 F，斜率 **+0.3 F / 1000 F，corr +0.01**
（**平的，没有回正力**）；`(75,1,3)` 跨 7344–12980 F，斜率 **−40.4，corr −0.52**
（τ ≈ 25 tick ≈ **45 s**）；`(75,0,3)` 斜率 **−33.5，corr −0.58**。
**同样大的跨度，一组有回正、一组没有。τ 没法从这一趟里定出来。**

**(d) 噪声不是白噪声，不能撒 iid。** 去掉漂移后的残差：sd **145.5 F**，偏度 **−1.36**
（左尾重，大跌比大涨狠），**lag-1 自相关 0.655**。它是**持续的**。
想复刻手感要复刻这个自相关，不能撒独立噪声。
（对数感：sd 146 F/tick 的白噪声跑 428 拍会散开 sd ≈ 3010 F；实测温度跨 6591–13963 F。）

**(e) `c.cbl*Lvl` 不是读出来的，是采集器自己算的。** `readCBL()`
（`_tools/TRG_original_recorder.luau:986-1010`）写的是
`lvl = clamp(floor(pct/25), 1, 5)`，注释里就写着「derived level ... so a reader can see
where the quantisation happens」。**它和 `Pct` 是同一个量的两种写法，不是两个独立测量。**
真正从游戏里读出来的是 `PowerLabel` 的文字（`c.cbl*Pct`，取值 {10,25,50,75,100,125}）。

**(f) 冷却档位这一趟只用到 0 和 1。** `readCoolant()`（`:1013-1035`）数
`Light1..Light3` 有几盏亮，所以 `c.cool*` 是 **0..3 的档位**、`c.coolSum` 是 0..9 的和。
这一趟 `c.cool1/2/3` **只出现过 0 和 1**，`c.coolSum` 只到 3。
所以 −58 F/tick 是 **1 档**的增益，**2/3 档这一份没有**。
两种可能分不开（见 `QUESTIONS.md` P2）：操作员没用到 2/3 档，**或者**读数只认第一盏灯的颜色。
在 AIRemake 的 `Workspace.Consoles.ThermalConsole.CoolantControl1` 上点过：
子物体是 `Light1/Light2/Light3` + `PW1ClickPart/PW2ClickPart/PW3ClickPart` ——
**3 灯 3 档**，采集器的 `for j = 1, 3` 是对的。但**原版那一台没有开着，没能对**。

**(g) `s.Core.TemperatureVal` 在 t=97.90 冻结在 9420，之后再不更新**，
而同一个结构里的 `s.Core.RadiationVal` 一路写到 **t=866.87（414 次）**。
所以「stats 全冻了」不是通则，机制不明 —— **不编。**

### 49.6 给 remake 用的一句话

**把温度当积分器，不要当惯性环节。** 每 tick
`ΔT = 加热(ΣcblPct) − k_cool·冷却档位 − k_fan·风扇数 + 噪声`，
`加热` 在 75% 以上饱和，噪声带 lag-1 自相关 ≈ 0.65、sd ≈ 145 F/tick、左偏。
`k_cool ≈ 58`（1 档）、`k_fan ≈ 33`（F/tick）。**回正项要么没有、要么 τ 在 45–90 s 之间
且这一份定不下来** —— 这是唯一必须靠 remake 自己调、或者靠下一趟专门测的参数。

---

## Phase 48 更正（2026-09-26 23:40）

**上面 Phase 48 那节原来写错了三处，而且用户当场就纠正过**（原话：
`我就是先注入才开的核心啊，核心开好之后我按start`）。

1. ~~「采集器第一份『中途注入』的产出」~~ → **不是中途注入。是冷启动。**
   `B 1 t=1.34`：`s.Core.TemperatureVal=0 s.Core.OutputVal=0 s.Core.RadiationVal=0`，
   六个风扇全 0、三台冷却泵全 0、三个 CBL 全 0；`EVT2072–2078 CLICK StartUpLever` ×7
   （t≈2–13 s）就是开机；`s.Core.TemperatureVal` 从 0 爬到 9420；`s.GameActive`
   在 **t=98.47** 才 false→true。
2. ~~「缺冷启动那半场」~~ → **半场一直在文件里**，见 49.4。
3. ~~「`flow=false` 因为注入时核心已开着」~~ → 因果反了。`flow=false` 是**结构性的**：
   `flow` 是 `tostring(sawDown)`，`sawDown` 要 `flowArmed`，`flowArmed` 要
   `isRunning`（`tempF >= 5600`，也就是 `m.temp` 有读数）连续 3 拍。
   **冷启动的一趟永远给不出 `flow=true`**，核心冷了 88 秒也一样。

**错在哪：** 我把 `m.temp` 当成了堆芯温度。它是**监视器的标签**，而监视器在 t≈99 之前
读的是 `ERR F`（`EVT1139`）—— **监视器最瞎的时候正是堆芯最冷的时候。**
`EVT2017 CLOCK the clock already reads past 12:00PM at inject; the core is up` 这句也一样：
它的依据是 `q.up = q.clock > 0`，而 `q.clock` 是个**自由走的表盘**（冷堆时 710→715
一路在走，堆芯正停在 0 F）。Phase 48 修了这句话的**措辞**（改成按 `clockStartedUp` 分辨），
**没修它的依据** —— 依据还是「表盘过了正午 = 核心开着」。这条进 `QUESTIONS.md` P3。

**顺带撤回一条：** Phase 48 说「Equinox 把两个 CBL 打到 10%」。同样的 25→10
在 **t=188.71** 和 **t=548.75** 也出现过，那两次没有 Equinox。所以「Equinox 干的」
这一份文件**不支持** —— 它是同时发生的两件事，不是一条因果。
"""


# ============================================================ DECISIONS_2.md ==
DECISIONS_APPEND = """
138. A MONITOR LABEL IS NOT THE STATE, AND IT GOES BLIND EXACTLY WHEN THE STATE IS MOST INTERESTING.

    WHAT HAPPENED. Phase 48 read `m.temp` and announced that the operator had injected
    mid-shift. The operator said they had injected first and started the core afterwards. The file
    is on their side: `B 1 t=1.34` carries `s.Core.TemperatureVal=0 s.Core.OutputVal=0
    s.Core.RadiationVal=0` with every fan, every coolant pump and every CBL off, and
    `EVT2072-2078 CLICK StartUpLever` -- seven clicks at t=2..13 s -- is the power-on. What made the
    wrong reading look right is one line: `EVT1139 TEXT x.temp ERR F`. The monitors had not been
    booted, so the label being read was printing `ERR F` for the first 99 seconds.

    WHY THIS IS WORTH WRITING DOWN AS A DECISION RATHER THAN A SCRUPLE. The wrong source was the
    only CONTINUOUS one. `m.temp` runs t=98.8 to t=868.9, the whole shift; `s.Core.TemperatureVal`
    covers the cold start and then freezes at 9420 at t=97.90. A reader who wants a temperature
    curve reaches for the series that spans the run, and that series begins exactly where the part
    that was asked about ends. Neither source is wrong; each is blank over the half the other one
    covers, and picking either alone yields a confident answer about the wrong half. The failure
    mode is not carelessness, it is that continuity reads as authority.

    HOW TO APPLY. Before reading a series as a state, ask whether it is a LABEL -- something a
    screen prints, which can print `ERR`, which can lag a tick, and which can be blank because
    nobody turned the screen on. `s.Core.*` is the state; `m.*` is a screen. And when two sources
    overlap, splice them rather than choosing between them: they meet at t~98 with `s.Core` at 9420
    (t=97.90) and `m.temp` at 9330 (t=98.77) -- 90 F over 0.87 s, which is 103 F/s against the
    98 F/s the stat had been climbing at. The splice is not a fudge, the AGREEMENT is the check.

139. `m.fluct` IS THE TEMPERATURE STEP, AND THAT REWRITES WHAT "STABILITY" MEANS.

    WHAT HAPPENED. 391 of the 393 rows where `m.temp` moved satisfy
    `temp(next) - temp(this) == m.fluct`, exactly; the other two are a read-order artefact (a row
    carrying one tick s temperature and the next tick s fluct). So `temp(t+1) = temp(t) +
    m.fluct(t)`. `m.fluct` is not a second reading sitting beside the temperature. It is the
    per-tick increment, and `m.temp` is its running sum.

    WHY THIS IS WORTH WRITING DOWN. It changes the shape of the model, and it is not a detail that
    can be recovered from the field name. `temp` is an accumulator: there is nothing to fit on it
    and no time constant to read off it. The quantity with a law behind it is `fluct`. It also
    explains the calibration console -- NET STABILITY is showing the derivative directly, which is
    why the operator can be asked to judge a stability reading at all.

    A SECOND CONSEQUENCE, filed here because it is the same measurement. The tick is real: gaps
    between `m.temp` changes are median 1.79 s, mode 2.0 s, p10 1.51 / p90 2.04 at a ~3.3 Hz poll,
    and `m.temp`, `m.press` and `m.fluct` move on the same row and never separately. One physics
    step writes all three. So a derivative taken per poll is fitting the repaint schedule: the
    first attempt at this fit returned R2=0.084 with physically backwards signs for exactly that
    reason, and the same data asked per tick returns R2=0.33 with every sign right. When a series
    moves in quantised bursts, the burst is the sample.

140. AN OPERATOR'S INPUTS ARE A RESPONSE, NOT AN EXPERIMENT.

    WHAT HAPPENED. Fitting the per-tick temperature step on the controls gives, per tick:
    `sum(cblPct)` +5.05 +- 0.42, `coolSum` -58.2 +- 9.7, `fanCount` -32.8 +- 9.4, R2 0.33. The
    one term that is not a control -- the current temperature -- comes back at -0.0068 +- 0.0044,
    indistinguishable from zero across a 6600..14000 F band. But the same fit also puts a POSITIVE
    coefficient on `coolSum*T`, i.e. coolant losing its bite as the core heats up. That is
    backwards, and it is not a small correction.

    WHY. Every control was moved in response to the temperature it is being regressed against. The
    operator turned coolant on because the core was hot, so high coolant coincides with high
    temperature by construction and the interaction term absorbs the coincidence. Twenty-eight
    degrees per second appears in both directions across stretches whose controls differ by one
    fan, because what is being fitted is a person's policy, not the machine's response.

    HOW TO APPLY. Split "can a model be read off this file" into two questions with different
    answers. GAINS: order of magnitude only, and only inside the band that was actually flown --
    `sum(cblPct)` reaches 300 during the cold start where the fit predicts +1104 F/tick and the
    file shows +180, a factor of six, because the CBL s effect saturates above ~75%. STRUCTURE:
    recoverable outright, and the load-bearing results here are structural -- that the temperature
    does not feed back on its own rate. And the honest test is the one that does not pool: inside a
    single control setting the mix cannot confound anything. `(cbl 75, cool 2, fan 4)` spans
    9069..13716 F with a slope of +0.3 F per 1000 F and correlation +0.01: flat, no restoring
    force, over 4600 F. `(75, 1, 3)` over a similar span gives -40.4 with correlation -0.52, i.e.
    tau ~ 45 s. Both are in the file, both are real, and they disagree, so tau is not determinable
    from this run -- and the correct response to that is to say so, not to fit harder.
"""


# ======================================================= docs/RECORDER_HOWTO.md ==
HOWTO_FLOW_OLD = r"- `flow=true` —— 开机的半场.*?而它是一份完整、封存、什么都没丢的文件。"
HOWTO_FLOW_NEW = """- `flow=true` —— 记录期间**见过核心从运行状态掉下来**（`sawDown` 落地）。
  判据的线是 `CoreThresholds[1] = 5600 F` —— 游戏自己的 stallout 线（`INGAME_MANUAL` 87：
  「Stallout Possibility will occur if the core temperature is below ~ 6000F」），
  **不是** 2000 F 那条低温跳闸（`Q1`），两件不同的事。
- **`flow=false` 读作「没见它掉下来过」，不是「数据丢了」，更不是「这一份里核心从没冷过」。**
  `sawDown` 要先 `flowArmed`，而 `flowArmed` 要 `isRunning`（`tempF >= 5600`，也就是
  `m.temp` 有读数）连续 `DebounceSamples = 3` 拍 —— **核心还没开起来的时候这个门根本不开**。
  所以**冷启动的一趟在结构上永远给不出 `flow=true`**。`2026-09-26 23:00` 那一份核心冷了
  88 秒（`B 1 t=1.34` 三个 `s.Core.*` 全是 0，`EVT2072–2078 CLICK StartUpLever` 就是开机），
  `flow` 照样是 `false`。
  **冷启动的证据在 `s.Core.TemperatureVal`，不在收据这个字段里。** 见下。

### 温度要看哪一列（2026-09-26 加，Phase 49 量出来的）

**两条序列是互补的，各自只覆盖一半，而且它们接得上：**

| 序列 | 覆盖 | 性质 |
|---|---|---|
| `s.Core.TemperatureVal` | t≈0 → **t=97.90**（0 → 9420 F，≈98 F/s），之后**冻在 9420 不动** | 游戏自己的**状态** |
| `m.temp` | **t=98.77** → 结束 | 监视器上的**标签**，监视器没开机时读 `ERR F` |

接缝处的证据：`s.Core` 最后一拍 t=97.90 是 **9420**，`m.temp` 第一拍 t=98.77 是 **9330**
—— 90 F / 0.87 s = **103 F/s**，和那 98 F/s 同速。**两边对得上，所以两段都可信。**

**`m.fluct` 就是那一 tick 的温度增量**（391/393 行满足
`temp(下一拍) − temp(这一拍) == m.fluct`，逐字节相等）：
`temp` 是 `fluct` 的累加。**tick ≈ 1.8 s**（间隔中位数 1.79、众数 2.0），
`m.temp`/`m.press`/`m.fluct` 三个标签同一步一起变。
**别拿「每采一次」当时间步去算导数** —— 那是在拟合重绘时刻表。

**这一趟量出来的增益（F/tick，1 档冷却、只在 cblPct=75 那条带里可信）：**
`ΣcblPct` **+5.05/%**、每台冷却泵 **−58**、每个风扇 **−33**，当前温度项 **≈ 0**
（也就是**温度不回正，是个积分器**）。**别外推**：冷启动那段 CBL 输出 300%，
实测只有 +180 F/tick，线性模型给 +1104 —— **差 6 倍，这个关系是饱和的。**
噪声 sd ≈ 145 F/tick，**lag-1 自相关 0.655**（不是白噪声）。详见 `PROGRESS.md` Phase 49。"""


# ============================================================ QUESTIONS.md ==
QUESTIONS_OLD = r"\*\*现在有一条：P1。\*\*.*?不是「数据坏了」。"
QUESTIONS_NEW = """**现在有两条要你回答：P1 和 P2。** 都不是「哪坏了」——
没有任何东西坏 —— 而是**只有你能回答的问题**。P1 是行为事实，
P2 是「某一趟你手上做了什么」。P3 是我的活，列出来让你知道我要改哪行。

## P1 — ✅ 已答（2026-09-26 23:40）：冷启动那半场**已经到手了**，不用再跑

**这一条是我问错了。** 我当时的依据是文件里的
`EVT2017 CLOCK the clock already reads past 12:00PM at inject; the core is up`，
而你当场说的是 `我就是先注入才开的核心啊`。**你对，那句话错。**

`EVT2017` 的依据是 `q.up = q.clock > 0` —— 而 `q.clock` 是个**自由走的表盘**。
证据在文件里：核心冷着的那段时间（`s.Core.TemperatureVal` **恰好是 0**），
表盘一路 710→711→712→713→714→715 照走不误。**表盘不是堆芯的指示器。**

真正的冷启动证据，全都在这一份里：
- `B 1 t=1.34`：`s.Core.TemperatureVal=0 s.Core.OutputVal=0 s.Core.RadiationVal=0`，
  六个风扇全 0、三台冷却泵全 0、三个 CBL 全 0；
- `EVT2072–2078 CLICK StartUpLever` ×7（t≈2–13 s）—— **那才是开机**；
- `s.Core.TemperatureVal` 从 0 爬到 **9420 F**，**96.6 s**，≈ **98 F/s**；
- `s.GameActive` 在 **t=98.47** 才 false→true；
- 接缝：`s.Core` 最后是 t=97.90 的 9420，`m.temp` 第一拍是 t=98.77 的 9330 ——
  **两个源对得上**。

所以 **P1 撤掉**，不需要再花一次注入去换那半场。

**顺带撤回两条我自己写的错话：**
1. `flow=false` **不是**「核心从没冷过」。它是结构性的：冷启动的一趟**永远**给不出
   `flow=true`。正确的口径已经改进 `docs/RECORDER_HOWTO.md`。
2. 「Equinox 把两个 CBL 打到 10%」—— 同样的 25→10 在 t=188.71 和 t=548.75 也出现过，
   那两次没有 Equinox。这一份文件**不支持**那条因果。

## P2 — 🟡 这一趟，你有没有把**冷却泵开到 2 档或 3 档**？

**要你答的就一句话：有 / 没有。** 这一条分得开两个完全不同的修法，只有你知道答案。

**背景：** 冷却泵的档位（0..3）是采集器数 `CoolantControl1/2/3` 底下 `Light1..Light3`
**有几盏亮**得来的。这一趟整个文件里，三台泵的读数**只出现过 0 和 1**，
`c.coolSum` 也只到 3 —— 也就是说**记录里没有任何一次是 2 档或 3 档**。

两种可能，后果完全不同：

| 你的回答 | 意思 | 我要做的 |
|---|---|---|
| **P2:A —— 没有，我只用了开关/1 档** | 这是**行为事实**，不是 bug | 2/3 档的增益这一份就是没有。要不要专门补一趟由你定 |
| **P2:B —— 有，我开到过 2 档 / 3 档** | 那就说明**读数坏了**：第 2、3 盏灯亮的时候没被认出来（很可能是那两盏灯用了不同的「亮」颜色，撞不上 `Config.NeonOn` 的容差） | 我去改 `readCoolant()`，改成数灯的同时**同时读 `PW*ClickPart` 的位置**，两条腿互相印证 |

**为什么值得问：** 这是「温度计算」这件事上唯一还缺的一个增益（`coolSum` 那一列
只标定到 1 档：**−58 F/tick**）。而且不管是哪种答案，采集器都该顺手加固 ——
**只靠灯的颜色判档位**是一条腿站着，这一份文件正好没把这件事证伪掉。

## P3 — 📌 我自己的活，不用你答（列出来让你知道我要改哪）

`EVT2017` 那句 `the core is up` 的**依据**还是错的。Phase 48 只改了它的**措辞**
（按 `clockStartedUp` 分辨中途注入和冷启动），**没改依据** —— 依据仍然是
`q.up = q.clock > 0`，也就是「表盘过了正午 = 核心开着」，而表盘是自由走的。

正确的开机见证者是 **`s.GameActive` false→true**（这一份里 t=98.47，只写过 2 次），
它和封存信号是同一个字段的两端。我打算把「班次开始了」这句话挂到它上面，
`q.clock` 只留作读数、不再下结论。**这一条不影响任何读数，只是让那句话不再撒谎。**"""


def main():
    patch('PROGRESS.md', [], PROGRESS_APPEND)
    patch('DECISIONS_2.md', [], DECISIONS_APPEND)
    patch('docs/RECORDER_HOWTO.md', [(HOWTO_FLOW_OLD, HOWTO_FLOW_NEW, 'the flow gloss')])
    patch('QUESTIONS.md', [(QUESTIONS_OLD, QUESTIONS_NEW, 'the P1 banner and section')])

    # CLAUDE.md: the Phase 48 paragraph in section 8.
    old48 = (r"\*\*Phase 48 —— 采集器第一份「中途注入」的产出，和它暴露的两处假话。\*\*"
             r".*?无事件种类改名、无收据字段移动。")
    new48 = """**Phase 48 —— 采集器第一份完整「冷启动 → Equinox → 熔毁」的文件，和它暴露的两处假话。**
`Data/flow/original_260926-230049`（1357508 字节，完整 `## RECEIPT`，
`postfails=0 spilled=0 dropped=0`）**抓全了 Equinox 整条链**：12:00 PM 触发
（`INGAME_MANUAL` 114/148 原文「12PM marks the beginning of the Equinox Event」）→
两个 CBL 掉到 10% → 压力 2542→1070 → `MAINFRAME CONNECTION LOST` →
`s.MainframeMeltdown=true tempF=7978` 封存。顺手确认 **B2 已修**。
改了两处**只改措辞、不删读数**：① `CLOCK` 事件在中途注入时会把「表盘绕回正午」说成
「班次开始」—— 两句只隔 60 秒而 `m.temp` 那一刻 12865→12979 F，**两句都是假的**；
现在按注入那一拍的状态（`clockStartedUp`）分开记。② 封存那句
`the operator shut it down: s.MainframeMeltdown=true` 把机器的锅记在人头上；
现在措辞跟旗标走。裁决名 `user-shut` **没动**。
新增 `_tools/build_clock_test.py` + `_tools/selftest_clock_test.py`
（3 个变异改坏，各自在**指定断言**上红，`clock: 10 PASS, 0 FAIL`）；
采集器 126009 → **128612 字节**，无事件种类改名、无收据字段移动。

**Phase 48 更正（2026-09-26 23:40）：** 上面那节原来写的是「**中途注入**」「**缺**冷启动
半场」「`flow=false` 因为注入时核心已开着」—— **全错**，用户当场纠正过
（`我就是先注入才开的核心啊`）。文件站在用户那边：`B 1 t=1.34` 三个 `s.Core.*` 全 0、
风扇/冷却/CBL 全 0，`EVT2072–2078 CLICK StartUpLever` ×7 就是开机，
`s.Core.TemperatureVal` 0→9420 爬了 96.6 s。**我错在把 `m.temp` 当成了堆芯温度** ——
它是监视器标签，而监视器到 t≈99 都在读 `ERR F`：**监视器最瞎的时候正是堆芯最冷的时候**。
`flow` 只能答「有没有见它掉下来」；**冷启动的一趟在结构上永远给不出 `flow=true`**。
`EVT2017` 那句 `the core is up` 的**依据**（`q.up = q.clock > 0`）也是错的 ——
表盘自由走，冷堆时 710→715 照走。另外「Equinox 把 CBL 打到 10%」这份文件**不支持**
（同样的 25→10 在 t=188.71 / t=548.75 也出现过，没有 Equinox）。

**Phase 49 —— 温度是怎么算的（用户问「温度计算什么的能搞出来的吗？」）。**
**结构定死了，增益只到量级，公式拿不到。**
① **`m.fluct` 就是那一 tick 的温度增量**：393 次 `m.temp` 变化里 391 次满足
`temp(下一拍) − temp(这一拍) == m.fluct`，逐字节相等 —— `m.temp` 是它的累加。
tick ≈ **1.8 s**。**温度是积分器不是惯性环节**（t=560.78–610.97，cool=0/fan=3，
增量在时间和温度上都是平的：6625→13224 F）。
② 拟合（391 tick，目标 `m.fluct`）：`ΣcblPct` **+5.05/%**、冷却泵 **−58**、
风扇 **−33**、**温度项 ≈ 0**（−0.0068 ± 0.0044，与 0 无法区分），R² 0.33，
残差 sd 146 F/tick —— **解释了漂移，没解释波动**。
③ **拿不到的原因**：操作员每一次动控制都是对温度的回应，所以回归量共线
（`coolSum·T` 的系数符号是反的）；增益**不可外推**（冷启动 CBL 300%，实测 +180 F/tick
而模型给 +1104，差 6 倍，饱和）；回正项在固定设置内部互相矛盾
（`(75,2,4)` 跨 4600 F 是**平的** corr +0.01，`(75,1,3)` 是 −40.4/1000F corr −0.52），
**τ 定不下来**；噪声 lag-1 自相关 **0.655**，不是白噪声。
④ **冷启动半场一直在文件里**，而且和监视器接得上：`s.Core.TemperatureVal` 0→9420 F /
96.6 s ≈ **98 F/s**，最后一拍 t=97.90 的 9420 对上 `m.temp` 第一拍 t=98.77 的 9330
（103 F/s，同速）。"""
    patch('CLAUDE.md', [(old48, new48, 'the Phase 48 paragraph in section 8')])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
