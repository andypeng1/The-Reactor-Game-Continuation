# -*- coding: utf-8 -*-
"""Phase 42, disk side: retract two Phase 40 claims and append the record.

Two kinds of edit, and the difference matters.

APPENDS (PROGRESS phase 42, DECISIONS_2 entry 124) follow the established rule: the disk file is the
module image, so the new disk file is rstrip + one blank line + the block + one newline. Each append
ASSERTS the file already hashes to what the module reports, because appending to a file that is
already wrong produces a longer wrong file and the verifier would then be comparing two unknowns.

IN-PLACE REPLACEMENTS (docs/TODO.md section 3, DECISIONS_2 entry 121) assert the anchor occurs
EXACTLY once before writing. Section 0.13 is the reason: an anchor that is not unique by construction
lands the edit in the wrong block and the result still parses.

The false claim is being REMOVED rather than merely superseded, and that is deliberate. A log can
carry a retraction next to the thing it retracts, but docs/TODO.md section 3 is a live to-do list: an
entry there that says simulated clicks are impossible will be believed and acted on, which is the
whole failure mode. So it is rewritten in place as well as recorded in PROGRESS.

Run with the argument 'check' to print what would change without writing anything.
"""
import io
import os
import sys

D = r"D:\rblxTRGproject"


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


# (name, expected length, expected hash) as the modules reported BEFORE this phase. PROGRESS and
# DECISIONS_2 are asserted; docs/TODO.md is part of the CLAUDE module and is checked by
# verify_docs.py against that module's own numbers, so there is no smaller baseline to assert here.
APPENDS = [
    ("PROGRESS", 143156, "7a916aaa", "_phase42_progress.md"),
    ("DECISIONS_2", 102387, "191bd85e", "_phase42_decisions_124.md"),
]

# ---------------------------------------------------------------- docs/TODO.md
T_LAMP_OLD = """      冷却液那盏灯按 `atmosphere_vent` 的先例接上：冷却中 `spent`、冷却完 `ready`，
      **故意不加 `STATES` 条目**（`DECISIONS` 121）。`HDEFGenerator` **故意不动** —— 它是机柜不是台子。
"""
T_LAMP_NEW = """      冷却液那盏灯**按 `atmosphere_vent` 的先例加了分支**（冷却中 `spent`、冷却完 `ready`，
      **故意不加 `STATES` 条目**）—— 但 **Phase 42 实测这个分支从来没有执行过**：
      `ConsoleBinder` 先按 `coolant_pump_on` 把同一组 `Light1/2/3.NeonPart` 认领了，
      而 `Bind` 的升级路径只在原 action 为 nil 时才生效，于是**没有任何部件绑在
      `coolant_recalibrate` 上**，那一段是死代码。更糟的是按一次会把那三盏灯**永久留在闪烁色**
      （`PULSE_COLOR` = `90,255,120`）：上面那句「`applyLamp` 直接 early-return」不只是灯不亮 ——
      它同时是**唯一清掉闪烁的地方**，所以 early-return 等于把闪烁色钉死。
      **两半都已修**（`applyLamp` 回落到 `entry.base`，且只在真的变色时写入）并**已验证** ——
      一次真点击记录到的色变序列是
      `(235,235,235) → (90,255,120) → (235,235,235)`，间隔 0.71 秒。见 `DECISIONS` 124。
      `HDEFGenerator` **故意不动** —— 它是机柜不是台子。
"""

T_CLICK_OLD = """- [ ] **模拟点击在这个 place 里够不到控制台 —— 不是没做，是走不到。**
      `Workspace.StreamingEnabled = true`，全场只有 **1 个** `SpawnLocation`
      （`Workspace.TeamSpawns.SpawnLocation` @ (233, 402.9, 1370)），离控制室约 **1400 studs**、
      低 **120 studs**。实测 playtest 客户端里 `Workspace.Consoles` 只有 **97 件**（服务端几千件）、
      `ThermalConsole` **42 对 651** —— 几何体根本没流送到客户端，也没有路过去。
      所以 Phase 40 的控件绑定是靠 **dot-path 解析 + `ClickPart` 的 `CanQuery`** 验的，**不是靠鼠标**。
      要做真正的点击测试，得先放一个靠近台子的 spawn。
"""
T_CLICK_NEW = """- [x] ~~**模拟点击在这个 place 里够不到控制台**~~ —— **这条是错的，Phase 42 已作废并修正。**
      原文说「全场只有 **1 个** `SpawnLocation`…几何体根本没流送到客户端」。实测：
      `Workspace.TeamSpawns` 里有 **5 个** —— 1 个 `SpawnLocation` @ (233, 402.9, 1370)，
      加 `Spawn1..Spawn4` @ (257, 277.1, 29.4 / 36.9 / 44.4 / 51.9)，**就在台子旁边 122~160 studs**、
      桌面高度、脚下是实地（`Workspace.Geometry.Parts.Part` y=276.94，落差 0.12）。
      那四个是**死的**（`Neutral=false` + `TeamColor=White`，而 `Teams:GetTeams()` 是空的），
      所以「客户端远端出生」没错；但「走不到」是**从一次依赖距离的采样推出来的**：
      远端出生点到控制室的直线**60 个采样只被挡 1 个**，而 97 / 42 那两个数字**是距离造成的** ——
      同一个客户端，角色站到台前之后 `ThermalConsole` 是 **678** 件。
      **真点击已经打通**：`moveTo(427, 115)` + 左键 →
      `[Console] andypeng1NB pressed: Coolant Pump 1 Sensor Recalibration  (ThermalConsole)`，
      即 `ClickDetector → ControlTrigger.Fire → CoolantSystem.Recalibrate`。
      四个必须先量的点：相机要用 `RenderStepped` **每帧重设**（`execute_luau` 每次调用后会把
      `CameraType` 重置回 Custom，转角色是没用的）；瞄准要**投影 + 对该像素做射线**并断言命中的是
      拉杆自己（只投影不够，有四组姿态的射线死在 `Riser` 上）；三个冷却液拉杆**共线**，
      要用垂直于那一排的机位才分得开；工具发的 y 是**请求值 + 58**，且目标要避开左上角 CoreGUI
      聊天窗（否则工具报 `hits CoreGUI`）。完整方法见 `PROGRESS` Phase 42 / `DECISIONS` 124。
"""

# ---------------------------------------------------------------- DECISIONS_2, entry 121
E121_OLD = """    control that already had this problem - the convention is usually already in the file.
"""
E121_NEW = """    control that already had this problem - the convention is usually already in the file.

    CORRECTED IN PHASE 42 - see DECISIONS 124. The lamp does not say it. No part is bound to
    coolant_recalibrate: the station's three LEDs are claimed by coolant_pump_on first, because
    ConsoleBinder binds the ON button before the BigLever and Bind only upgrades a lamp whose action
    is falsy. So this branch has never run. Worse, the press left those three LEDs on the activation
    flash colour permanently, because applyLamp was both the flash's only clearer and an early return
    on a nil state. The DECISION above still stands - a momentary action is displayed by a lamp and
    never by a lever position - it simply had no part to display it. Both halves are fixed and
    verified in Phase 42.
"""

EDITS = [
    (os.path.join("docs", "TODO.md"), [(T_LAMP_OLD, T_LAMP_NEW), (T_CLICK_OLD, T_CLICK_NEW)]),
    ("DECISIONS_2.md", [(E121_OLD, E121_NEW)]),
]


def main():
    dry = "check" in sys.argv
    rc = 0

    for name, want_len, want_hash, block_file in APPENDS:
        path = os.path.join(D, name + ".md")
        raw = io.open(path, "rb").read()
        got = roll(raw)
        if len(raw) != want_len or got != want_hash:
            print("%-12s *** REFUSING: disk is %d/%s, module says %d/%s ***"
                  % (name, len(raw), got, want_len, want_hash))
            rc = 1
            continue
        block = io.open(os.path.join(D, "_tools", block_file), "rb").read()
        trimmed = block.rstrip(b"\r\n \t")
        if trimmed != block:
            print("%-12s note: trimmed %d trailing whitespace bytes" % (name, len(block) - len(trimmed)))
        block = trimmed
        if b"\\" in block:
            print("%-12s *** block contains a backslash (section 0.10) ***" % name)
            rc = 1
            continue
        if b"]==]" in block:
            print("%-12s *** block contains the module terminator ***" % name)
            rc = 1
            continue
        new = raw.rstrip(b"\r\n") + b"\n\n" + block + b"\n"
        if not dry:
            io.open(path, "wb").write(new)
        print("%-12s %d -> %d, hash %s -> %s%s"
              % (name, len(raw), len(new), got, roll(new), "  (dry run)" if dry else ""))

    for rel, pairs in EDITS:
        path = os.path.join(D, rel)
        raw = io.open(path, "rb").read()
        text = raw.decode("utf-8")
        before = roll(raw)
        for old, new in pairs:
            n = text.count(old)
            label = old.strip().splitlines()[0][:56]
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

    return rc


if __name__ == "__main__":
    sys.exit(main())
