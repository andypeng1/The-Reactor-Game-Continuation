"""One-shot: Phase 50 (pressure) + the answered P2 + DECISIONS 141.

Same discipline as patch_docs_49.py, plus one repair: QUESTIONS.md is spliced
by LINE INDEX, not by regex.  The first draft anchored on a phrase that also
appears in prose, so the pattern would have matched zero times -- and because
the appends run before it, PROGRESS.md and DECISIONS_2.md would already have
been written.  So: every anchor is resolved and asserted up front, and nothing
is written until all of them have been found.
"""
import sys
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text, before):
    (ROOT / path).write_text(text, encoding='utf-8', newline='\n')
    print('%-26s %7d -> %7d chars' % (path, before, len(text)))


def append(path, block):
    text = read(path)
    before = len(text)
    if not text.endswith('\n'):
        text += '\n'
    write(path, text + block, before)


PROGRESS_APPEND = """
---

## Phase 50 — 压力：一个风扇 = −60 PSI/tick（用户给的数，文件验过）[DONE]

**日期：** 2026-09-26 约 23:55。**触发：** 用户答了 P2（`没有` —— 冷却泵没用到 2/3 档），
并主动给了一个常数：**`一个风扇每tick降低60PSI`**。**对象：** 同一份文件，**只读**。

### 50.1 最干净的一段：操作员自己替我们做的 A/B

cblPct=75、coolSum=0 **两个都按住不动**，**只有 fan 在 1↔2 之间来回拨**，
压力斜率**精确地在 +58 和 −2 之间跳**：

| t | fan | dP (PSI/tick) |
|---|---|---|
| 700.67 / 702.41 | 3 | **−62** |
| 704.21 | 2 | **−2** |
| 705.98 / 707.70 / 709.44 | 1 | **+58** |
| 711.22 … 732.46（八拍） | 2 | **−2** |
| 734.23 … 739.44（四拍） | 1 | **+58** |
| 741.17 … 748.21（五拍） | 2 | **−2** |
| 751.87 / 753.49 | 1 | **+60** |

**fan 1 → +58、fan 2 → −2、fan 3 → −62** —— 每加一个风扇正好 **−60**，
而且这是**三次独立的跳变**（1↔2 来回四趟 + 2→3 一次）。
**fan=0 时这个工作点的基线 = +118 PSI/tick。**

### 50.2 全文件 12 次风扇拨动，12 次方向全对

| t | fan | 前 | 后 | Δ |
|---|---|---|---|---|
| 134.18 | 3→4 | +11 | −46 | −57 |
| 192.15 | 4→3 | −38 | −2 | **+36** |
| 310.55 | 3→4 | +26 | −21 | −47 |
| 428.54 | 4→3 | −24 | +34 | +58 |
| 490.35 | 3→4 | +24 | −38 | −62 |
| 550.32 | 4→3 | −47 | −10 | **+37** |
| 656.48 | 3→4 | +54 | −8 | −62 |
| 684.74 | 4→3 | −110 | −62 | +48 |
| 704.21 | 3→2 | −62 | −2 | **+60** |
| 734.23 | 2→1 | −2 | +58 | **+60** |
| 741.17 | 1→2 | +58 | −2 | **−60** |
| 806.82 | 2→3 | +4 | −54 | −58 |

**开风扇 → 斜率变负，关风扇 → 变正，12/12 没有一次例外**，中位 |Δ| = 58。
最干净的那几对（基线本身不含糊的，就是 50.1 那趟）**正好是 ±60**。
**用户给的 60 是对的。**

**但线性只验到 3 个风扇，4 个以上这一份答不了。**
fan 3→4 的四次拨动是 −57 / −47 / −62 / −58（中位 −57，还在 60 附近），
**可是 fan=4 的「稳态」窗口（t=310.55–356.26）根本不是常数**：
`−30 −26 −24 −22 −20 −18 −16 −14`，一路朝 0 收敛 —— 那是一个**衰减中的瞬态**，
不是稳态斜率。所以它**既不能否证 60、也不能支持 60**。
**4 个以上风扇会不会饱和 = 未解。**

### 50.3 冷却泵的压力增益**不是**常数

同样按住 fan 和 cblPct，五次 coolSum 拨动的 Δ 是：

| t | cool | Δ (PSI/tick) |
|---|---|---|
| 368.69 | 1→2 | +0 |
| 561.08 | 2→0 | +11 |
| 612.14 | 0→2 | +4 |
| 666.92 | 2→1 | **−102** |
| 695.19 | 1→0 | −4 |

**没有常数。** 那个 −102 是单次跳变，很可能是瞬态。
**所以「一个风扇 −60」这条不能顺手推广到冷却泵。**
冷却泵对压力要么作用很小（≈ 0），要么是借温度间接起作用的 —— **这一份分不开**。
（对照 49.2：冷却泵对**温度**是有确定作用的，−58.2 ± 9.7 F/tick。）

### 50.4 顺带：这条数从**文件外面**锁死了 tick

用户说的「每 tick」和文件里的 tick 是同一个：**压力变化的间隔中位数 1.79 s，
和温度的 1.79 s 一致。** 这是第一次由**文件之外的人**确认 tick ≈ 1.8 s ——
前面那个 1.8 s 是我从采样间隔反推的，现在有了独立的见证。
**意义：** 49.2 那张表里的「F/tick」和用户脑子里的「tick」是同一个单位，
不需要再做任何换算。

### 50.5 压力也是累加量，但它的增量**没有**单独上报

文件里 `m.*` 只有三个键：`m.temp`、`m.press`、`m.fluct`。
**温度有 `m.fluct` 把每拍增量直接报出来（见 49.1），压力没有** —— 压力的增量只能自己差分。
差出来的 dP 有 **80 个不同取值**，最常见的几个是
−2（18 次）、+26（17 次）、+4（15 次）、+2（14 次）、+10（11 次）、
+50（11 次）、−46（11 次）、−44（11 次）—— **不是同一个常数的重复**
（同一条设置下 `+58` 也见过 `+50`），说明**基线本身在漂**（`c.cbl*Pct` 会自己漂，
见 49.5(e)）。**要给压力也做一张和 49.3 一样的表，得先有 `cblPct` 的独立记录。**

### 50.6 给 remake 用

**风扇 → 压力：−60 PSI/tick（已验证，3 个风扇以内）。**
fan=0 时 cblPct=75 / cool=0 那一点的基线是 **+118 PSI/tick**。
压力同样是累加量（不是惯性环节）。**冷却泵 → 压力：这一份没量出来。**
"""


DECISIONS_APPEND = """
141. A CONSTANT THE OPERATOR HANDS YOU IS A HYPOTHESIS, AND CHECKING IT IS THE CHEAPEST THING IN THE FILE.

    WHAT HAPPENED. The operator volunteered `一个风扇每tick降低60PSI`. The file was already open,
    so it was checked rather than filed. Twelve fan toggles across the run, twelve correct
    directions, median |delta| = 58 PSI/tick; and one stretch where the operator toggled fan 1 and
    2 four times with cblPct and coolSum held still, in which the pressure slope snapped between
    +58 and -2 -- a difference of exactly 60. The number is right.

    WHY THIS IS WORTH A DECISION AND NOT A THANK-YOU. A number from the operator arrives with more
    authority than a number from a fit and less evidence: it is one person's memory of a system
    they have been running, and it is exactly the kind of figure that ends up in a Config table
    and is never questioned again. It is also nearly free to test, because the operator has
    already spent the run doing A/B tests on the machine -- every control they touched twice is a
    step response they did not know they were performing. Checking cost one query. Believing it
    unchecked would have cost a wrong constant sitting in the remake under a comment saying it was
    measured.

    THE CHECK FOUND THE LIMIT AS WELL AS THE VALUE, which is the part a bare confirmation would
    have missed. The linearity holds to three fans. fan 3->4 toggles give -47 to -62, but the
    fan-4 window at t=310..356 is not a steady slope at all -- it walks -30, -26, -24, ..., -14,
    converging toward zero, i.e. it is a transient that happens to be labelled with the right fan
    count. So above three fans the file neither confirms nor denies saturation, and that is what
    gets written down. A number accepted on authority would have been recorded as linear
    everywhere.

    HOW TO APPLY. Check it before filing it, and report the limit alongside the value. And take
    the units seriously: the operator said "per tick", the file's pressure changes land 1.79 s
    apart and its temperature changes land 1.79 s apart, so the tick in their sentence and the
    tick in the data are the same ~1.8 s. That agreement was not derivable from the file alone --
    the file can only measure its own cadence -- and it means every gain in F/tick or PSI/tick is
    already in the unit they will think in. The same check also says what NOT to generalise: the
    coolant pumps' pressure deltas across five toggles are +0, +11, +4, -102 and -4, so the tidy
    -60 belongs to the fans and does not transfer.
"""


BANNER_NEW = """**P1 和 P2 都答完了。现在只剩一条 P4，而且它只在你还打算再注入一次时才需要答。**
P3 是我自己的活，列出来让你知道我要改哪一行，**不用你答**。
**没有任何东西坏** —— 下面每一条的答案都已经改进文档了。
"""

P2_NEW = """## P2 — ✅ 已答（2026-09-26 23:55）：`没有`

**你的回答：`没有，还有我有有个数据：一个风扇每tick降低60PSI`**

**「没有」的意思：** 冷却泵这一趟你只用了 **0 档和 1 档**，没开到过 2/3 档。
所以记录里只有 0 和 1 **不是读数坏了**，是**行为事实** —— `readCoolant()`
数 `Light1..Light3` 有几盏亮那条路是好的，不用改。
**代价：** 2/3 档的增益这一份就是没有。温度那边缺的就是这一个数
（1 档 = **−58.2 F/tick**，见 `PROGRESS.md` 49.2）。

**顺手验了你给的那个数（谢谢，它比你以为的有用）：**
文件里 **12 次风扇拨动，12 次方向全对**，中位 |Δ| = **58 PSI/tick**；
最干净的一段（cblPct=75、coolSum=0 按住不动，只有 fan 在 1↔2 来回拨），
斜率**精确地在 +58 和 −2 之间跳**，差**正好 60**。**你说的 60 是对的。**
（细节和它的**边界**见 `PROGRESS.md` Phase 50 —— 线性只验到 **3 个风扇**，
4 个以上这一份答不了；而且这条**不能**推广到冷却泵。）

**这个数还顺手锁死了 tick：** 你说「每 tick」，文件里压力变化的间隔中位数也是
**1.79 s**，**和温度一模一样** —— 这是第一次由文件外面的人确认 tick ≈ 1.8 s。

"""

P4_NEW = """## P4 — 🟡 下次注入（**如果你还打算跑的话**）要不要顺手把冷却泵开到 2、3 档

**前提先讲清楚：** 这一条**只在你还打算再注入一次的时候**才需要答。不打算跑的话它自己作废 ——
**没有任何东西坏，现有的文件是完整的。**

**为什么想到这个：** 温度模型上**只剩这一个增益没标定**。你手上有三台泵，每台 0..3 档，
而记录里只有 0 和 1。想补上，代价很小：

| 选项 | 意思 |
|---|---|
| **P4:A** | 下次注入的时候，开核心之后**顺手把三台冷却泵拧到 2 档停半分钟、再拧到 3 档停半分钟**（别的一概不用改，你平时怎么玩就怎么玩）。这样 2/3 档的增益就有了。 |
| **P4:B** | 不跑了，或者觉得用不上。那 2/3 档这一段就**标为未知**入档，remake 那边留一个待调参数。 |

**不需要现在做任何事。** 你方便的时候跑就行；不跑，这条就作废。

"""

CLAUDE_P50 = """

**Phase 50 —— 压力：一个风扇 = −60 PSI/tick（用户给的数，文件验过）。**
用户主动给了常数 `一个风扇每tick降低60PSI`，当场拿文件验：**12 次风扇拨动 12 次方向全对**，
中位 |Δ| = 58 PSI/tick；最干净的一段（cblPct=75、coolSum=0 按住不动，只拨 fan 1↔2 四趟）
斜率**精确在 +58 和 −2 之间跳，差正好 60** —— **用户是对的**，fan=0 基线 +118 PSI/tick。
**边界一并记下：线性只验到 3 个风扇**（fan=4 那个窗口是衰减瞬态，不是稳态斜率，
`−30→−14` 朝 0 收敛）；**而且这条不能推广到冷却泵**（五次 coolSum 拨动的 Δ 是
+0/+11/+4/−102/−4，没有常数）。
**顺带：这条数从文件外面锁死了 tick** —— 用户说的「每 tick」和压力变化的间隔
**1.79 s** 一致，和温度的 1.79 s 也一致，这是第一次有外部见证确认 tick ≈ 1.8 s。"""


def find(lines, pred, what):
    for i, ln in enumerate(lines):
        if pred(ln):
            return i
    sys.exit('QUESTIONS.md: no line matching %s' % what)


def splice_questions():
    path = 'QUESTIONS.md'
    text = read(path)
    before = len(text)
    lines = text.split('\n')

    i_head = find(lines, lambda s: s.startswith('# 🟡 等你回答'), 'the 等你回答 heading')
    i_p1 = find(lines, lambda s: s.startswith('## P1 —'), '## P1')
    i_p2 = find(lines, lambda s: s.startswith('## P2 —'), '## P2')
    i_p3 = find(lines, lambda s: s.startswith('## P3 —'), '## P3')
    i_b2 = find(lines, lambda s: s.startswith('## B2 —'), '## B2')
    # the `---` + blank line that separate P3 from B2; P4 goes just before it
    i_sep = i_b2
    while i_sep > i_p3 and lines[i_sep - 1].strip() == '':
        i_sep -= 1
    if i_sep == i_b2 or lines[i_sep - 1].strip() != '---':
        sys.exit('QUESTIONS.md: could not find the --- before ## B2')

    out = (lines[:i_head + 1]
           + BANNER_NEW.split('\n')[:-1]
           + lines[i_p1:i_p2]
           + P2_NEW.split('\n')[:-1]
           + lines[i_p3:i_sep]
           + P4_NEW.split('\n')
           + lines[i_sep:])
    text = '\n'.join(out)
    for needle, label in (('## P2 — ✅ 已答（2026-09-26 23:55）', 'the new P2'),
                          ('## P4 — 🟡', 'the new P4'),
                          ('## P1 — ✅ 已答（2026-09-26 23:40）', 'the preserved P1'),
                          ('## B2 — ✅', 'the preserved B2')):
        if text.count(needle) != 1:
            sys.exit('QUESTIONS.md: %s appears %d times after the splice'
                     % (label, text.count(needle)))
    if 'P2:A —— 没有，我只用了开关/1 档' in text:
        sys.exit('QUESTIONS.md: the old P2 table survived the splice')
    write(path, text, before)


def splice_claude():
    path = 'CLAUDE.md'
    text = read(path)
    before = len(text)
    anchor = '（103 F/s，同速）。'
    n = text.count(anchor)
    if n != 1:
        sys.exit('CLAUDE.md: the Phase 49 tail matched %d times' % n)
    i = text.index(anchor) + len(anchor)
    write(path, text[:i] + CLAUDE_P50 + text[i:], before)


def main():
    # Resolve every anchor and read every file FIRST, so a failure cannot leave
    # some files patched and others not.
    for p in ('PROGRESS.md', 'DECISIONS_2.md', 'QUESTIONS.md', 'CLAUDE.md'):
        read(p)
    q = read('QUESTIONS.md')
    for needle in ('# 🟡 等你回答', '## P1 —', '## P2 —', '## P3 —', '## B2 —'):
        if q.count(needle) != 1:
            sys.exit('QUESTIONS.md: %r appears %d times' % (needle, q.count(needle)))
    c = read('CLAUDE.md')
    if c.count('（103 F/s，同速）。') != 1:
        sys.exit('CLAUDE.md: the Phase 49 tail is not unique')
    if 'Phase 50' in read('PROGRESS.md'):
        sys.exit('PROGRESS.md already has a Phase 50 -- not running twice')

    splice_questions()
    splice_claude()
    append('PROGRESS.md', PROGRESS_APPEND)
    append('DECISIONS_2.md', DECISIONS_APPEND)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
