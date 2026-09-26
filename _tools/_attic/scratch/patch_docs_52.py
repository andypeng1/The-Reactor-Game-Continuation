"""One-shot: correct the cold-start numbers, and record what the start-up actually was.

Four files, ten anchors.  Every anchor is resolved and asserted unique (or counted)
before anything is written, because three of these strings appear in more than one
file and a substring swap in the wrong one is silent.

The corrections, all from re-reading Data/flow/original_260926-230049:

  1. "0 -> 9420 F / 96.6 s ~ 98 F/s" divides by a span that is 88.5 s of zero.
     The real shape is 88.5 s flat at 0 F, then 9.37 s to 9420 F (mean +951 F/s).
  2. "103 F/s, same speed" compares a FALL (9420 -> 9330) against a RISE, and 9420 is
     a terminal value, not a waypoint.  The claim is void either way.
  3. There is no splice to make.  `t.ReadingsFrame.TempLabel` is the same reading as
     `m.temp` -- 394 + 22 = 416 samples, equal on every overlapping poll -- and it runs
     t=88.53 to t=865.09.  One series, unbroken.
  4. The saturation argument in 49.5(a) used the wrong rate AND the wrong regime.
  5. `EVT2072-2078` is eigth events, 2072-2079, not seven.
  6. New: the plant is configured between t=13.39 and t=90.48 with zero CLICK events,
     in lockstep, at even spacing, in numeric order.
"""
import sys
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text, before):
    (ROOT / path).write_text(text, encoding='utf-8', newline='\n')
    print('%-18s %7d -> %7d chars' % (path, before, len(text)))


def swap(path, old, new, note):
    """Replace one exact, unique occurrence.  Unique, not first: every one of these
    anchors is short enough that an accidental second copy would be a silent edit to
    the wrong paragraph."""
    text = read(path)
    n = text.count(old)
    if n != 1:
        sys.exit('%s: anchor for [%s] matched %d times, want 1:\n%s'
                 % (path, note, n, old[:200]))
    write(path, text.replace(old, new), len(text))


def append(path, block):
    text = read(path)
    write(path, text + block, len(text))


# --------------------------------------------------------------------------- PROGRESS

P_494_OLD = """### 49.4 第二个锚：冷启动确实在文件里，而且和监视器接得上

`s.Core.TemperatureVal`：`0` → `9420 F`，**96.6 s**，**≈ 98 F/s**（三个 CBL 都在 Lvl 4
—— 也就是 `c.cbl*Pct` 各自 100，`Σ = 300`；冷却 1 档、风扇 4 个）。
它最后一拍是 **t=97.90 的 9420**；`m.temp` 第一拍是 **t=98.77 的 9330**。
差 90 F / 0.87 s = **103 F/s**，和 98 F/s **同速**。
**两个源在 t≈98 接得上** —— 这同时说明两件事：`s.Core.TemperatureVal` 到 t=97.90 为止
可信，`m.temp` 从 t=98.77 起可信。**冷启动那半场一直在这份文件里。**
"""

P_494_NEW = """### 49.4 第二个锚：冷启动确实在文件里，而且温度是一条**连续**的线

> **2026-09-27 重写。** 本节原来那句「`0` → `9420 F`，**96.6 s**，**≈ 98 F/s**」
> 是错的，错法和更正见下面的 49.4b。**结论「半场在文件里」不变，而且比原来更强** ——
> 温度根本不是两段拼起来的，它是一条线。

`s.Core.TemperatureVal` 一共只有 23 个样本：`B 1 t=1.34` 是 **0**，然后
**整整 88.5 s 一个样本都没有**（采集器只写变化，所以那 88.5 s 里它一直**恰好等于 0 F**），
到 **t=88.53** 才是 `510`。从那里到 **t=97.90 的 9420**，**9.37 s**、**+8910 F**。
（三个 CBL 都在 Lvl 4 —— `c.cbl*Pct` 各自 100，`Σ = 300`；冷却 1 档、风扇 4 个。）

**但温度没在那儿断。** 监视器那一路 `t.ReadingsFrame.TempLabel` **第一次出现正是
t=88.53，一路写到 t=865.09**。把它和 `m.temp` 并排：

| 序列 | 首拍 | 末拍 | 样本数 |
|---|---|---|---|
| `t.ReadingsFrame.TempLabel` | t=88.53 | t=865.09 | **416** |
| `m.temp` | t=98.77 | t=865.09 | **394** |

**416 − 394 = 22 —— 正好是 `s.Core.TemperatureVal` 有值的那 22 拍**（t=88.53..97.90）。
两边重合的每一拍数值也一一相同：t=96.20 都是 9207、t=97.06 都是 9244、
t=97.90 都是 9420、t=98.77 都是 9330、t=100.57 都是 9324、t=102.52 都是 9366、
t=104.11 都是 9393。**`t.ReadingsFrame.TempLabel` 和 `m.temp` 是同一个读数** ——
`m.*` 那一路要等监视器开机后才开始记，`t.*` 那一路早 22 拍就有。

所以从 **t=88.53 一路到关机（t=865.09），温度是一条线，中间没有缝**。
**不需要拼接**。（DECISIONS 138 里那段「拼在 t≈98」是在**没看 `t.ReadingsFrame.TempLabel`**
的前提下写的。）

### 49.4b 【更正】那个 98 F/s 是平均值，分母里 88.5 s 是零

原句「`0` → `9420 F`，**96.6 s**，**≈ 98 F/s**」算的是 `9420 / 96.56`。真实形状是**两段**：

| 段 | 区间 | 时长 | 变化 |
|---|---|---|---|
| 平在 0 | t=1.34 → 88.53 | **88.5 s** | 一个样本都没有，恒 0 F |
| 起堆 | t=88.53 → 97.90 | **9.37 s** | 510 → 9420 F，**均 +951 F/s** |

斜坡本身也不匀速：逐拍速率从 **+1642 / +1630 / +2303 / +2013 F/s** 起，
衰减到 **+210 / +104 / +14 F/s** —— **是趋近平台的一阶形状**，平台就在 9420 附近，
不是一条匀速直线。

**「103 F/s 和 98 F/s 同速」这条佐证作废。** 它拿 9420（t=97.90，`s.Core.TemperatureVal`
的**最后一拍**）减 9330（t=98.77）：那是 **−90 F，方向是往下的**，而前面是往上的 ——
两个反号的数拿来比「速率」没有意义；而且 9420 之后 `s.Core.TemperatureVal`
**到文件结束一次都没再出现**，它是**终点**，不是斜坡上的一个中途点。
**何况这条读数本来就不用拼**（见 49.4）。

`EVT2072–2078 StartUpLever` 那句也顺带更正：**是 8 次，EVT2072–2079**。
"""

swap('PROGRESS.md', P_494_OLD, P_494_NEW, '49.4 body')

P_495A_OLD = """**(a) 增益不可外推。** 冷启动那段实测 **+180 F/tick**（98 F/s × 1.8 s），
49.2 那个拟合给 **+1104 F/tick**，**差 6 倍**。CBL 输出从 75% 翻到 300%，
净加热几乎没变 —— **这个关系是饱和的，线性模型只在拟合过的带里成立。**
"""

P_495A_NEW = """**(a) 增益不可外推 —— 但「饱和」这条本文件没证出来。** 冷启动那段实测 **+180 F/tick**，
那是 `98 F/s × 1.8 s`，而 98 F/s 是 49.4b 里那个**含 88.5 s 零的平均值**。
按真实的斜坡算（`951 F/s × 1.8 s`）是 **+1712 F/tick**，比 49.2 拟合出的 **+1104**
还**高** 1.6 倍。更要紧的是两个数**不是同一个工况**：+1712 是**开机瞬态**里的一拍
（堆芯离平衡很远，而且起堆是脚本驱动的），+1104 是从**稳态班次**数据拟合的。
**所以「CBL 从 75% 翻到 300% 时净加热饱和」在本文件里既没被证明、也没被否证 ——
这条挂起来。**（原先写的「差 6 倍」是拿两个错口径的数相减。）
"""

swap('PROGRESS.md', P_495A_OLD, P_495A_NEW, '49.5(a)')

P_495G_OLD = """**(g) `s.Core.TemperatureVal` 在 t=97.90 冻结在 9420，之后再不更新**，
而同一个结构里的 `s.Core.RadiationVal` 一路写到 **t=866.87（414 次）**。
所以「stats 全冻了」不是通则，机制不明 —— **不编。**
"""

P_495G_NEW = """**(g) `s.Core` 里那几路读数各自停在不同时刻**：`TemperatureVal` 停在
**t=97.90（9420）**、`OutputVal` 也停在 **t=97.90**、`PressureVal` 停在 **t=116.43**，
而 `RadiationVal` 一路写到 **t=866.87（414 次）**。**所以「stats 全冻了」不是通则。**
**温度这一路也不是断了** —— 它换了个名字继续（`t.ReadingsFrame.TempLabel` = `m.temp`，
一路到 t=865.09，见 49.4）。**但 `s.Core` 自己那三个值为什么会在 t=97.90 / t=116.43
停笔，机制不明 —— 不编。**
"""

swap('PROGRESS.md', P_495G_OLD, P_495G_NEW, '49.5(g)')

P_497 = """
### 49.7 开机那 96 秒里，配堆的是机器，不是手

**（2026-09-27 新查的，起因是用户问「完整的开机流程是不是没记录」。）**

**记全了。** 从 `B 1 t=1.34` 的完全冷态到 t=868.94 的封存，两头都在文件里。
t=1.95→13.39（11.4 s）操作员的 **20 次点击**也都带名字：

```
EVT2060 CLICK RoomLight        EVT2067 CLICK MonitorBoot
EVT2061 CLICK MonitorPower     EVT2071 CLICK HDEF-PowerLever
EVT2062 CLICK Shutters         EVT2072-2079 CLICK StartUpLever   <- 8 次
```

后面紧跟 `EVT2081 [ALERT] SUBSPACE REACTOR START-UP SEQUENCE INITIATED` 和
`EVT2084 PowerLabel 524 GW → 3.001 TW` —— **面板跟着变了，所以这 20 条不是注入时的假事件。**

> 顺带一个读法上的坑：`S 2 t=1.95` 是 **poll 头**，写在它下面的 EVT 行属于
> **这个 poll 之后到下一个 poll 之间**的窗口，也就是 t=1.95→13.39 —— 不是「610 ms 里
> 点了 20 下」。`dt=610` 是距上一个 poll 的时间，不是这段事件窗口的宽度。

**但 t=13.39 到 t=90.48 这 77 秒，一次 CLICK 都没有**，而堆在这段时间里被配好了：

| t | 变了什么 | 形状 |
|---|---|---|
| 31.39 | `c.cool1/2/3` 0→1 | **三台在同一个 poll 里一起跳** |
| 35.95→38.42 | `c.fan1..fan6` 0→1 | 按 1→6 顺序，**每 0.30–0.60 s 一个** |
| 59.62 | `c.cbl*On` 0→1、`Lvl` 0→4 | **三个在同一个 poll 里一起跳** |
| 85.39 | `c.cbl*Pct` 100→50、`Lvl` 4→2 | **三个在同一个 poll 里一起跳** |

它们全是 `UNATTR`，括注里「last click N polls ago」的指针**一律指回 t≈2–13 那次开机**。

**读法：这些不是人点的，是开机序列自己配的，操作员只投了启动杆。** 三条证据：
① **同一个 poll 里三台一起跳** —— 手做不到；
② 六个风扇**等间隔、按序号**依次开 —— 是脚本的形状，不是手速；
③ **钩子是活的** —— 同一份文件在 t=90 之后照样抓到 `Coolant3-OFF`(t=124.30)、
`Fan4/5/6`(t=107–132)、`CBL*-PW*`(t=113–120)、`CBL1-PURGE`(t=118.24)，
而且全场 `PROMPT` 事件为 **0**（所以也不是走的 ProximityPrompt）。
**这一条是推断，不是直读** —— 文件给的是「变化发生了、没人点」，把它归给开机序列是解释。
但它同时解释了「开机为什么要 96 秒」：**前 88 秒是序列在铺场子，堆芯就停在 0 F 上。**

**教训（采集器那条）：`UNATTR` 只在「钩子这段时间是活的」时才等于「没人点」。**
要断言「没人点」，先在同一份文件里找到**同类控制在别处被抓到的 CLICK** ——
这里就是 Coolant / Fan / CBL 三族在 t>90 都被抓到了，所以 t<90 的缺席才算数。
（进 `DECISIONS_2.md` 144。）
"""

swap('PROGRESS.md',
     '\n---\n\n## Phase 48 更正（2026-09-26 23:40）',
     P_497 + '\n---\n\n## Phase 48 更正（2026-09-26 23:40）',
     'insert 49.7 before the Phase 48 correction')

# ------------------------------------------------------------------------------ CLAUDE

C_OLD = """④ **冷启动半场一直在文件里**，而且和监视器接得上：`s.Core.TemperatureVal` 0→9420 F /
96.6 s ≈ **98 F/s**，最后一拍 t=97.90 的 9420 对上 `m.temp` 第一拍 t=98.77 的 9330
（103 F/s，同速）。"""

C_NEW = """④ **冷启动半场一直在文件里**，而且温度**是一条线、不用拼**：`s.Core.TemperatureVal`
在 **0 F 上平了 88.5 s**（t=1.34→88.53 一个样本都没有），然后 **9.37 s** 从 510 爬到
**9420 F**（均 +951 F/s，逐拍从 +2303 衰减到 +210，是趋近平台的一阶形状）。
监视器那一路 `t.ReadingsFrame.TempLabel` 和 `m.temp` **是同一个读数**
（**394 + 22 = 416**，重合的每一拍数值相同），从 t=88.53 连续到 t=865.09。
**旧写的「0→9420 F / 96.6 s ≈ 98 F/s」作废**（分母里 88.5 s 是零）；
**「103 F/s 同速」也作废**（9420→9330 是往**下** 90 F，而 9420 之后
`s.Core.TemperatureVal` 到文件结束一次都没再出现，它是终点不是中途点）。
**开机那 96 秒里配堆的是机器不是手**：t=13.39→90.48 共 **77 秒零 CLICK**，
而冷却三泵、三个 CBL 各在**同一个 poll 里一起跳**、六个风扇**等间隔按序**开 ——
操作员只投了启动杆（`EVT2072–2079 StartUpLever` **×8**，不是 ×7）。"""

swap('CLAUDE.md', C_OLD, C_NEW, 'the Phase 49 bullet 4')

C_X7_OLD = '`EVT2072–2078 CLICK StartUpLever` ×7'
C_X7_NEW = '`EVT2072–2079 CLICK StartUpLever` ×8'
swap('CLAUDE.md', C_X7_OLD, C_X7_NEW, 'the x7 in the Phase 48 correction')

# -------------------------------------------------------------------------- DECISIONS

D_OLD = """    overlap, splice them rather than choosing between them: they meet at t~98 with `s.Core` at 9420
    (t=97.90) and `m.temp` at 9330 (t=98.77) -- 90 F over 0.87 s, which is 103 F/s against the
    98 F/s the stat had been climbing at. The splice is not a fudge, the AGREEMENT is the check."""

D_NEW = """    overlap, prefer the one that spans the run -- but check first whether a third series already
    spans it. Here one did. `t.ReadingsFrame.TempLabel` runs t=88.53 to t=865.09, 416 samples, and
    compares EQUAL to `m.temp` on every overlapping poll; 394 + 22 = 416, and the 22 are exactly the
    polls where `s.Core.TemperatureVal` still had a value. The numbers never needed splicing -- they
    were one reading recorded twice, through two paths that start at different times.
    (This paragraph replaced a wrong one, 2026-09-27: it spliced `s.Core` 9420 at t=97.90 to
    `m.temp` 9330 at t=98.77 and called it "90 F over 0.87 s = 103 F/s, the same speed the stat had
    been climbing at". That compares a FALL against a RISE, and 9420 is a terminal value -- the
    series never appears again after t=97.90 -- not a waypoint. See PROGRESS 49.4b.)"""

swap('DECISIONS_2.md', D_OLD, D_NEW, 'decision 138, the splice sentence')

swap('DECISIONS_2.md',
     '`EVT2072-2078 CLICK StartUpLever` -- seven clicks at t=2..13 s -- is the power-on.',
     '`EVT2072-2079 CLICK StartUpLever` -- eight clicks at t=2..13 s -- is the power-on.',
     'decision 138, the click count')

DEC_144 = """

144. AN UNATTRIBUTED CHANGE MEANS "NOT THIS CLIENT" -- AND THAT IS ONLY EVIDENCE IF THE HOOK IS PROVABLY ALIVE.

    WHAT HAPPENED. The operator asked whether the full start-up sequence had been recorded. The
    states are all there: the capture opens on a fully cold plant (`s.Core.TemperatureVal=0`, every
    fan, every pump and every CBL off, `s.GameActive=false`) and closes on the seal. The operator s
    own clicks are there by name too -- twenty between t=1.95 and t=13.39, ending with
    `EVT2072-2079 CLICK StartUpLever` eight times and followed by `EVT2081 SUBSPACE REACTOR START-UP
    SEQUENCE INITIATED` and `PowerLabel 524 GW -> 3.001 TW`, so the panels confirm they were real
    presses and not an artefact of attaching the recorder. Then, for seventy-seven seconds, the
    plant is configured -- three coolant pumps onto level 1, six fans on, three CBLs onto level 4
    and back to level 2 -- and NOT ONE click is recorded.

    WHY THE ABSENCE IS STILL READABLE. Taken alone, "no click" proves nothing: the client may have
    been out of activation range, or the control may never have been hooked. What makes it readable
    here is a positive control inside the same file -- later, the same three control families DO
    produce clicks (Coolant3-OFF at t=124.30, Fan4/5/6 at t=107-132, CBL*-PW* at t=113-120), and the
    PROMPT count for the whole run is zero, so the presses did not arrive by ProximityPrompt either.
    With the hook demonstrably alive, the earlier silence is evidence. And the SHAPE agrees: the
    three coolant pumps change in the same poll, the three CBLs change in the same poll, and the six
    fans come on in numeric order at 0.30-0.60 s intervals. Hands do not do that; a script does. So
    the machine configured the plant and the operator threw the lever -- which is also why the core
    sits at exactly 0 F for the first 88 s of a 98 s start-up.

    THE PART TO REMEMBER. `UNATTR` is a claim about the observing client, not about the world. It
    becomes a claim about the world only when you can point at the same instrument working elsewhere
    in the same recording. A hook that is checked once, at attach, carries no such guarantee -- its
    value is entirely borrowed from the clicks that did arrive, so the clicks that did arrive are
    part of the evidence, not just the result.

    HOW TO APPLY. Before reading an absence as evidence, look for a positive control in the same
    file: the same family, the same instrument, a different time. And when the shape of the changes
    is available -- lockstep, even spacing, ordinal order -- read it; shape distinguishes a script
    from a hand more cheaply than any instrumentation does.
"""

append('DECISIONS_2.md', DEC_144)

# --------------------------------------------------------------------------- QUESTIONS

Q_OLD = """- `EVT2072–2078 CLICK StartUpLever` ×7（t≈2–13 s）—— **那才是开机**；
- `s.Core.TemperatureVal` 从 0 爬到 **9420 F**，**96.6 s**，≈ **98 F/s**；
- `s.GameActive` 在 **t=98.47** 才 false→true；
- 接缝：`s.Core` 最后是 t=97.90 的 9420，`m.temp` 第一拍是 t=98.77 的 9330 ——
  **两个源对得上**。"""

Q_NEW = """- `EVT2072–2079 CLICK StartUpLever` **×8**（t≈2–13 s）—— **那才是开机**；
- `s.Core.TemperatureVal` 在 **0 F 上平了 88.5 s**（t=1.34→88.53 无样本），
  然后 **9.37 s** 爬到 **9420 F**；
- `s.GameActive` 在 **t=98.47** 才 false→true；
- **温度是一条线，不用拼**：`t.ReadingsFrame.TempLabel` 和 `m.temp` 是同一个读数
  （**394 + 22 = 416**，重合的每一拍数值相同），t=88.53 → t=865.09 连续。
- 顺带：t=13.39→90.48 有 **77 秒零 CLICK**，而冷却三泵 / 三个 CBL 各在同一个 poll 里
  一起跳、六个风扇等间隔按序开 —— **配堆的是开机序列，不是手**（`PROGRESS.md` 49.7）。

> **2026-09-27 更正：** 上面原来写「96.6 s ≈ 98 F/s」和「接缝对得上（103 F/s 同速）」——
> 两条都错，见 `PROGRESS.md` 49.4b。**P1 撤掉的结论不变。**"""

swap('QUESTIONS.md', Q_OLD, Q_NEW, 'the P1 cold-start evidence list')

print('\nall four files patched')
