# -*- coding: utf-8 -*-
"""Close out section 3 (TODO) and README for Phase 40, disk side.

Every replacement asserts its anchor occurs EXACTLY once before writing. Section 0.13 is the reason:
an anchor that is not unique by construction lands the edit in the wrong block, and the result parses
beautifully while being wrong. The same (old, new) pairs are applied to the game-side CLAUDE and
README modules by hand; if the two copies differ by one byte, _tools/verify_docs.py goes red.

Run with the argument 'check' to print the pairs without writing anything.
"""
import io
import os
import sys

D = r"d:\rblxTRGproject"


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


# ---------------------------------------------------------------- README
R_OLD = """  PROGRESS / DECISIONS / README   (documentation modules)
"""
R_NEW = """  PROGRESS / DECISIONS / DECISIONS_2 / README   (documentation modules)

DECISIONS IS TWO MODULES ON PURPOSE. ModuleScript.Source is capped at 200000 bytes by the engine,
and in Phase 40 the record passed it - the write was refused outright rather than truncated. Entries
1..74 stay in DECISIONS, under the name every existing reference already uses; 75.. onwards live in
DECISIONS_2. The boundary is an ENTRY NUMBER, so it is a fact about the document rather than about
its length on the day it was cut. The two disk mirrors DECISIONS.md and DECISIONS_2.md are copies of
the two modules byte for byte. See DECISIONS 123.
"""

# ---------------------------------------------------------------- docs/TODO.md, section 3
T1_OLD = """- [ ] **控制台二次重做（含冷却液校准）** —— 用户 2026-09-23 指定：排在 CBL 二次重做之后、
      其余任务之前。Mk2 台子被评价「太丑」，而**冷却液校准**（`coolant_recalibrate`，
      Wiki 记该传感器设备「有不可靠的倾向」、需要「手动干预校准」）需要一个像样的实体交互点。
      **动手前必须先量**：六台现状件数（433 / 376 / 334 / 370 / 327 / 61）、控件在台面上的分布、
      以及 `coolant_recalibrate` 此刻绑在哪个部件上 —— 不凭印象改。
"""
T1_NEW = """- [x] **控制台二次重做（含冷却液校准）** —— **已完成**（`PROGRESS` Phase 40 / `DECISIONS` 115-121）。
      用户 2026-09-23 指定：排在 CBL 二次重做之后、其余任务之前。Mk2 台子被评价「太丑」，
      而**冷却液校准**（`coolant_recalibrate`，Wiki 记该传感器设备「有不可靠的倾向」、
      需要「手动干预校准」）**本来连灯都是死的** —— `lampState` 里根本没有这个动作，
      `applyLamp` 直接 early-return，那盏灯永远停在作者配的颜色上。
      **量出来的起点**：`ORIG_MainReactorConsole` 有 **113 件恰好 20.00 度**绕 Z 的部件、
      贯穿整张台子 —— 那才是六张台并排时「看着别扭」的真正来源，而 **Main 正是最平的一张**。
      给 Main 补了 **1.55 深的斜面寄存器**（`RegPlate`/`RegRim`/`RegWell` + `RegSkirt` + 危险条），
      七个控件用**一次刚性重挂**（`P * (A^-1 * pose)`）站到斜面上，台子高度对外零变化（6.250）。
      **第一版把 20 度做成了 40 度**（`P` 自带 rake 又乘了一次）：装机成功、高度对得上、
      七个 dot-path 全部解析、截图看着也像那么回事，**只有量角度能发现**（`DECISIONS` 117）。
      冷却液那盏灯按 `atmosphere_vent` 的先例接上：冷却中 `spent`、冷却完 `ready`，
      **故意不加 `STATES` 条目**（`DECISIONS` 121）。`HDEFGenerator` **故意不动** —— 它是机柜不是台子。
"""

T2_OLD = """- [ ] **仍然缺：QPU 更换 / Gateway / GravLift 的独立测试** —— 它们需要自己的测试文件，
      不该挂在控制测试名下。
"""
T2_NEW = """- [ ] **仍然缺：QPU 更换 / Gateway / GravLift 的独立测试** —— 它们需要自己的测试文件，
      不该挂在控制测试名下。
- [ ] **模拟点击在这个 place 里够不到控制台 —— 不是没做，是走不到。**
      `Workspace.StreamingEnabled = true`，全场只有 **1 个** `SpawnLocation`
      （`Workspace.TeamSpawns.SpawnLocation` @ (233, 402.9, 1370)），离控制室约 **1400 studs**、
      低 **120 studs**。实测 playtest 客户端里 `Workspace.Consoles` 只有 **97 件**（服务端几千件）、
      `ThermalConsole` **42 对 651** —— 几何体根本没流送到客户端，也没有路过去。
      所以 Phase 40 的控件绑定是靠 **dot-path 解析 + `ClickPart` 的 `CanQuery`** 验的，**不是靠鼠标**。
      要做真正的点击测试，得先放一个靠近台子的 spawn。
"""

T3_OLD = """      `PreloadAsync` 的逐资源回调在命令栏 VM 里确实不触发（70 个全 `NO-CALLBACK`），别指望它。
"""
T3_NEW = """      `PreloadAsync` 的逐资源回调在命令栏 VM 里确实不触发（70 个全 `NO-CALLBACK`），别指望它。
- [x] **`ModuleScript.Source` 上限 200000 字节 —— `DECISIONS` 已撞上，已拆成两个模块**（`DECISIONS` 123）。
      写入 202893 字节的镜像时被引擎**直接拒绝**（`Provided string length (202910) ... max length (200000)`），
      于是**第一次出现「磁盘在前、模块落后」**：磁盘吃下了 115-122，模块一个字节都没进。
      现在拆成 **`DECISIONS`（条目 1..74，103355 字节）+ `DECISIONS_2`（条目 75..123，102387 字节）**，
      边界是**条目号**而不是字节偏移；两个磁盘镜像 `DECISIONS.md` / `DECISIONS_2.md`
      各自**逐字节等于**自己模块的镜像（这两份不是 `docs/` 卫星文件，没有磁盘专属前言）。
      **写的时候注意**：`DECISIONS.md` 里有 2 个反斜杠（早期条目里 Lua 代码片段中的「反斜杠 + n」），
      所以这一份**只能在 Studio 内部从已有文本搬移出来，不能通过工具调用传文本**（§0.10）。
"""

JOBS = [
    ("README.md", [(R_OLD, R_NEW)]),
    (os.path.join("docs", "TODO.md"), [(T1_OLD, T1_NEW), (T2_OLD, T2_NEW), (T3_OLD, T3_NEW)]),
]

if __name__ == "__main__":
    dry = "check" in sys.argv
    rc = 0
    for rel, edits in JOBS:
        path = os.path.join(D, rel)
        raw = io.open(path, "rb").read()
        text = raw.decode("utf-8")
        before = roll(raw)
        for old, new in edits:
            n = text.count(old)
            label = old.strip().splitlines()[0][:58]
            if n != 1:
                print("*** %s: anchor occurs %d times: %s ***" % (rel, n, label))
                rc = 1
                continue
            text = text.replace(old, new)
            print("%-16s replaced: %s" % (rel, label))
        if rc:
            continue
        out = text.encode("utf-8")
        if not dry:
            io.open(path, "wb").write(out)
        print("%-16s %d -> %d, hash %s -> %s%s"
              % (rel, len(raw), len(out), before, roll(out), "  (dry run)" if dry else ""))
    sys.exit(rc)
