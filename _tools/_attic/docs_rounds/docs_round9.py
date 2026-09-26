# -*- coding: utf-8 -*-
"""Round 9 doc updates: the control-test coverage round, and the dead HDEF lever it exposed.

Disk side. The same fragments are spliced into the four mirrored ModuleScripts from Studio, and
both sides are then compared by BODY HASH, never by byte count -- byte-neutral drift defeats
counting, which has cost this project two rounds (DECISIONS 83 / NIGHT_LOG round 5).

roll(disk) with no offset for PROGRESS / DECISIONS / README: the module source is
`return [==[` + TWO newlines + disk bytes + `]==]` + newline, and a REMEMBERED offset is part of
the contract and drifts silently (it cost round 7 a full false MISMATCH). CLAUDE is compared after
its disk-only 0.0 section is stripped with the established b[:327] + b[1653:] cut -- every edit
below lands far past byte 1653, so the cut region is untouched.

NO SCENE WRITE HAPPENED THIS ROUND. Two Source edits: ControlVisuals (the bind guard) and
GameCoreControlTest (re-render after Arm, plus the new state phase). Nothing here records a change
to the place's geometry.

Constraint carried over from the module side: no fragment may contain a double-quote character or
a backslash, because the Studio-side splice builds each fragment from double-quoted Lua strings
and the edit layer decodes Lua escapes once (CLAUDE 0.10). Asserted below.
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


# ============================== DECISIONS 87 / 88 ==============================

DEC_87 = """87. THE HDEF POWER LEVER'S ANIMATION HAD BEEN DEAD SINCE BIND TIME - A COLLISION BETWEEN TWO CONTROLS THAT RESOLVE TO THE SAME LEVER.

    WHAT BROKE. ConsoleBinder defines two controls on HDEFGenerator: PowerLever.ClickPart with
    action hdef_lever, and EmergencyControl with action hdef_emergency. HDEFGenerator owns exactly
    ONE LeverUnion, and it is PowerLever's. ControlVisuals.findLeverParts climbs Model ancestors
    from the click part and returns on the FIRST ancestor owning a LeverUnion, so BOTH controls
    resolve to that same lever. Bind order in the def table is PowerLever, then EmergencyControl,
    then the three PowerCells, and Bind overwrote the lever entry unconditionally - so the action
    ended up as hdef_emergency.

    WHY THAT IS FATAL AND NOT MERELY WRONG. detent() is the only place that decides which actions
    can move a lever, and it has no hdef_emergency branch. detent returns nil, applyLever returns
    early, and the handle never moves again. The control still FIRES: the bus reports the action
    engaged, BackupPowerSystem.LeverPulled flips, the lamp changes colour. Nothing in the log and
    nothing on any monitor says the animation is gone - the lever is simply frozen at whatever
    angle it was last rendered at.

    CONFIRMED LIVE BEFORE THE FIX. Invoke on HDEF Power Lever reported the action engaged while the
    LeverUnion's CFrame was byte-identical afterwards, and the diagnostics list showed
    action=hdef_emergency detent=-1 with no hdef_lever entry anywhere in it.

    THE ACTUAL HIJACKER IS NOT THE POWER CELLS. hdef_cell is not in STATES, so Bind skips its lever
    branch entirely and the three power cells never touch the lever. The collision is PowerLever
    against EmergencyControl alone. That matters: the obvious suspect - three controls crowded onto
    one generator - is not the one, and a fix aimed at it would have missed.

    THE FIX ASKS detent() RATHER THAN KEEPING A SECOND LIST. Bind now installs an incoming action
    only if the lever holds no action yet, or the incoming action has a detent branch, or the held
    one does not:

        local incomingDrives = action and detent(action, 0, 0) ~= nil
        local heldAction = levers[moving].action
        local heldDrives = heldAction and detent(heldAction, 0, 0) ~= nil
        if action and (not heldAction or incomingDrives or not heldDrives) then ... end

    A detented action can therefore never be displaced by a non-detented one, while last-bind-wins
    survives among detented actions - which is what PW1..PW5, coolant on/off/level and
    startup/shutdown rely on. Asking detent() instead of enumerating the actions a second time
    means the guard and the renderer cannot drift apart.

    WHY A GENERAL GUARD AND NOT A SPECIAL CASE FOR HDEF. Every lever reachable by more than one
    action was enumerated. There are five. Four are legitimate and every one of their actions is
    detented: coolant_pump_on / coolant_pump_off / coolant_pump_level on the three CoolantControl
    levers, and startup / shutdown on StartUpBigLever, both of which read r.Online. Exactly one is
    pathological, and the test had already flagged it. So the guard is general in form and touches
    exactly one lever in fact.

    MEASURED AFTER. The diagnostics list carries 18 levers and the HDEF entry now reads
    action=hdef_lever detent=2 states=2, with no hdef_emergency anywhere in it. The test row for
    HDEF power lever reports moved=true with a CFrame delta of 0.169 studs in X."""

DEC_88 = """88. THE CONTROL TEST'S UNCOVERED SET WAS MIS-COUNTED, AND THE PROBE ITSELF MANUFACTURED A FALSE FAIL AND A SPURIOUS PASS.

    THE CATEGORY ERROR IN CLAUDE 3.3. That item listed four things as uncovered CONTROLS -
    coolant_recalibrate, QPU replacement, Gateway, GravLift - as if they were one family.
    ConsoleBinder's def table contains no QPU, Gateway or GravLift entry at all. Those are
    standalone FacilitySystem modules, not actions on the control bus, so a console-control test is
    the wrong instrument for them and always was. The genuinely uncovered CONTROLS numbered twelve:
    coolant_recalibrate, startup, shutdown, monitor_boot, pressurizer_vent, pea_vent,
    gravatron_charge, gravatron_overload, hdef_lever, hdef_emergency, hdef_cell, metu_ecc.

    WHY THEY WERE UNCOVERED. The existing test only knew how to assert on the SCENE - does the pivot
    move, does the lamp change colour. Most of those twelve are visually stateless: pressing them
    changes a number and nothing physical. Covering them required a second phase asserting on
    GameState and on the owning system instead of on the scene, a capability this file did not have.

    THE PROBE MANUFACTURED TWO FAILURES. The first re-run reported pass:28 fail:2, and BOTH failures
    were the test's fault, not the scene's. Some rows need a precondition (startup refuses while the
    reactor is already online), so a row declares an Arm step. Arm writes GameState - but the lever
    is a RENDER of GameState and only moves when ControlVisuals.Update runs. The loop sampled the
    pivot immediately after Arm and before any re-render, so it read the PREVIOUS state's angle.
    When the armed state happened to match the stale render, a lever that really does swing on the
    click was reported as did-not-move. Fixed by re-rendering after Arm:

        if t.Arm then t.Arm(); ControlVisuals.Update(); task.wait(0.35) end

    AND ONE SPURIOUS PASS. Worse than the false failures: the Reactor shutdown row passed for the
    wrong reason. It passed only because the Reactor startup row before it had already left the
    scene in the armed pose, so the stale read happened to be correct. A probe that can pass by
    accident is not a probe.

    THE FLUCTUATION COUNT FELL FROM 60/60 TO 5/5, AND THAT IS CORRECT. The recorded 60/60 measured
    the double-writer bug fixed in DECISIONS 79 - PowerSystem wrote r.Temperature every frame, so
    all 60 iterations produced a real delta. Temperature now settles once per second, so 60
    iterations at dt = 1/10 can produce about five real updates. The loop was left untouched on
    purpose: it is measuring the 1 Hz cadence, and 5/5 is what the cadence actually is.

    MEASURED AFTER. pass:30 fail:0, finalStatus PASS, visuals 18 levers / 41 lamps, fluctuation
    checks 5 signMatches 5, and a 12-row stateTests table all PASS."""

# ============================== PROGRESS Phase 32 ==============================

PROG_ENTRY = """## Phase 32 - Control-test coverage: twelve controls, and a dead lever found on the way  [DONE]

CLAUDE 3.3 listed coolant_recalibrate, QPU replacement, Gateway and GravLift as uncovered controls.
The QPU / Gateway / GravLift half of that is a category error - ConsoleBinder has no entry for any
of them, they are standalone FacilitySystem modules, and a console-control test is the wrong
instrument. The genuinely uncovered controls numbered twelve.

All twelve are now covered by a second test phase that asserts on GameState and on the owning
system rather than on the scene: coolant_recalibrate, startup, shutdown, monitor_boot,
pressurizer_vent, pea_vent, gravatron_charge, gravatron_overload, hdef_lever, hdef_emergency,
hdef_cell, metu_ecc.

THE REAL FINDING. Extending the test exposed a defect that had nothing to do with coverage: the
HDEFGenerator power lever had been frozen since bind time. ConsoleBinder binds both PowerLever
(hdef_lever) and EmergencyControl (hdef_emergency) on HDEFGenerator, the generator owns one
LeverUnion, both controls walk to it, and Bind overwrote the first action with the second.
detent() has no hdef_emergency branch, so the handle never moved again - while the control still
fired, the state still flipped and the lamp still changed colour. Nothing reported it.

Fixed in ControlVisuals.Bind with a guard that asks detent() whether an incoming action can drive a
lever, and refuses to let a non-driving action displace a driving one. Enumerated facility-wide,
five levers are reachable by more than one action; four are legitimate and all-detented, and
exactly one was pathological. DECISIONS 87.

THE PROBE WAS ALSO WRONG. The first re-run reported pass:28 fail:2, and both failures were the
test's: rows with an Arm precondition sampled the lever pivot before ControlVisuals.Update had
re-rendered the armed state. One row passed only because the preceding row left the scene armed - a
spurious pass, which is worse than a false failure. Fixed by re-rendering after Arm. DECISIONS 88.

Fluctuation went from the recorded 60/60 to 5/5 and is correct: the old figure measured the
double-writer bug fixed in Phase 24 / DECISIONS 79.

MEASURED: pass:30 fail:0, finalStatus PASS, visuals 18 levers / 41 lamps, fluctuation 5/5, a
12-row stateTests table all PASS, and the lever diagnostics list now reading action=hdef_lever
detent=2 where it previously read action=hdef_emergency detent=-1.

Two Source edits, no scene write."""

# ============================== CLAUDE patches ==============================

CL_ROW_OLD = "| `GameCoreControlTest` | `pass:13 fail:0`，`levers:18 lamps:41`，`fluctuation signMatches 60/60` |\n"
CL_ROW_NEW = "| `GameCoreControlTest` | `pass:30 fail:0`，`finalStatus: PASS`，`levers:18 lamps:41`，`fluctuation signMatches 5/5`（另有 12 项 `stateTests` 表全 PASS） |\n"

CL_NOTE_OLD = "**注意：** `GameCoreSelfTest` 跑一次后会**自动禁用自己**。\n重新验证前要 `Disabled = false`。\n"
CL_NOTE_NEW = CL_NOTE_OLD + """
**注意 2：** `fluctuation` 从旧记的 `60/60` 变成 **`5/5` 不是退步**。
`60/60` 量的是 `DECISIONS` 79 修掉的双写入 bug（`PowerSystem` 每帧写 `r.Temperature`），
所以 60 次迭代次次都有真增量。温度现在 1 秒才结算一次，`dt = 1/10` 的 60 次迭代
只能产生约 5 次真实更新。这个循环**故意没动** —— 它量的就是 1Hz 节奏本身。

**注意 3：** 旧记的 `pass:13` 是只跑第一阶段时的数字；第二阶段（12 项状态断言）
是 `DECISIONS` 88 补上的，见 §3.3。
"""

CL_BUG_OLD = "- [x] 主监视器的示意图框（`ReactorDiagramFrame` / `CoreDiagramFrame`）**仍是静止的** ——\n      已接上（`PROGRESS` Phase 26 / `DECISIONS` 81）。纯观察者，只读 `GameState`。\n"
CL_BUG_NEW = CL_BUG_OLD + """- [x] **HDEF 电源拉杆的动画从绑定那一刻起就是死的** —— 已修
      （`PROGRESS` Phase 32 / `DECISIONS` 87）。`HDEFGenerator` 上 `PowerLever`（`hdef_lever`）
      与 `EmergencyControl`（`hdef_emergency`）会走到**同一个** `LeverUnion`（该机只有这一个），
      `Bind` 原先无条件覆盖，于是动作变成**没有 `detent` 分支**的 `hdef_emergency`，
      `applyLever` 直接 early-return，**拉杆从此不再动** —— 而控件照常触发、状态照常翻转、
      灯照常变色，**日志与监视器都不报错**。`Bind` 现在先问 `detent()` 这个动作能不能驱动拉杆，
      连「不能驱动的动作顶掉能驱动的动作」这条路径一起堵掉。
      全场共 **5 个拉杆**能被多个动作走到，**4 个合法且每个动作都有 detent，只有 HDEF 这一个是病态的**。
"""

CL_T33_OLD = """### 3.3 测试覆盖缺口
- [ ] `GameCoreControlTest` 还没覆盖：`coolant_recalibrate`、QPU 更换、
      传送环（Gateway）、重力电梯（GravLift）
"""
CL_T33_NEW = """### 3.3 测试覆盖缺口
- [x] **原条目把两类东西并列了，是分类错误。** `ConsoleBinder` 的控件表里
      **根本没有 QPU / Gateway / GravLift** —— 那三个是 `FacilitySystem` 下的独立系统，
      不是控制总线上的动作，拿控制测试去覆盖它们本来就用错了仪器。
      真正没覆盖的**控件是另外十二个**，现已全部覆盖
      （`PROGRESS` Phase 32 / `DECISIONS` 88）：
      `coolant_recalibrate` / `startup` / `shutdown` / `monitor_boot` /
      `pressurizer_vent` / `pea_vent` / `gravatron_charge` / `gravatron_overload` /
      `hdef_lever` / `hdef_emergency` / `hdef_cell` / `metu_ecc`。
      做法是加第二个阶段，断言 `GameState` 与系统状态而**不是**断言场景
      —— 这十二个大多**没有任何可见外观变化**，旧测试那种「看拉杆动没动 / 灯变没变色」
      的仪器对它们无能为力。
- [ ] **仍然缺：QPU 更换 / Gateway / GravLift 的独立测试** —— 它们需要自己的测试文件，
      不该挂在控制测试名下。
"""

CL_BIND_OLD = """**Bind 里必须用 `levers[moving]` 而不是 `levers[object]`：**
```lua
if action then
    levers[moving].action = action
    levers[moving].arg = arg
    -- Adopt the detent count of the richer action (e.g. a coolant
    -- lever starts as ON/OFF then gains the 0..3 level notches).
    levers[moving].states = STATES[action] or levers[moving].states
end
if arg2 and arg2 >= 1 then
    levers[moving].clickIndex = arg2
end
```
"""
CL_BIND_NEW = """**Bind 里必须用 `levers[moving]` 而不是 `levers[object]`；而且不能被「驱动不了拉杆的动作」顶掉：**
```lua
-- A lever can be driven by several click parts (PW1..PW5): keep the action
-- and remember the explicit notch for the last click.
--
-- A control that CANNOT drive a lever must not displace one that can.
-- HDEFGenerator is the case that bit: EmergencyControl sits beside PowerLever,
-- owns no LeverUnion of its own, so its walk climbs to the generator - where the
-- only lever IS PowerLever's. Last bind won, so the emergency control overwrote
-- the power lever's action with hdef_emergency, which has no detent branch, and
-- the lever never moved again.
-- detent() is the single authority on whether an action can drive a lever, so ask
-- it rather than keeping a second list of actions in sync by hand.
local incomingDrives = action and detent(action, 0, 0) ~= nil
local heldAction = levers[moving].action
local heldDrives = heldAction and detent(heldAction, 0, 0) ~= nil
if action and (not heldAction or incomingDrives or not heldDrives) then
    levers[moving].action = action
    levers[moving].arg = arg
    -- Adopt the detent count of the richer action (e.g. a coolant
    -- lever starts as ON/OFF then gains the 0..3 level notches).
    levers[moving].states = STATES[action] or levers[moving].states
end
if arg2 and arg2 >= 1 then
    levers[moving].clickIndex = arg2
end
```

**这道闸的意义（`DECISIONS` 87）：** 全场 **5 个拉杆**能被多个动作走到 ——
`CoolantControl1/2/3` 的 `coolant_pump_on/off/level`，`StartUpBigLever` 的 `startup`/`shutdown`，
以及 `HDEFGenerator` 的 `PowerLever`/`EmergencyControl`。**前四组每个动作都有 `detent` 分支，
所以 last-bind-wins 是正确行为**（`startup`/`shutdown` 判据同样是 `r.Online`，两个都能驱动）；
**只有 HDEF 那一组里 `hdef_emergency` 没有分支**，于是它一绑上去就把拉杆锁死了。
"""

# ============================== README patch ==============================

RD_OLD = """Workspace.GameCoreControlTest simulates operator clicks with a mock supervisor and
asserts that lever pivots move and lamp colours change. Latest run: 13 pass / 0 fail,
36 levers and 80 lamps registered, fluctuation sign 60/60.

Those figures are double the 18 / 41 recorded when only the installed desks were bound,
and that is expected rather than a regression: ConsoleBinder.BindRebuild keys off MK2_*
under Workspace.Rebuild.Models, so while the bench holds a rebuilt copy of every desk the
test counts BOTH the six live desks and the six bench rebuilds. The figure returns to
18 / 41 when the bench is cleared.
"""
RD_NEW = """Workspace.GameCoreControlTest simulates operator clicks with a mock supervisor and asserts that
lever pivots move and lamp colours change. A SECOND phase asserts on GameState and on the owning
system rather than on the scene, which is what covers the twelve controls that leave no visible
mark at all. Latest run: 30 pass / 0 fail, 18 levers and 41 lamps, fluctuation sign 5/5, and 12 of
12 state rows PASS.

The fluctuation figure was recorded as 60/60 while PowerSystem still wrote r.Temperature every
frame. That double write is fixed (DECISIONS 79), temperature now settles once per second, and 5 is
what 60 iterations at dt = 1/10 can actually produce. The loop was left alone on purpose. See
DECISIONS 88 for the whole count, including the two failures the probe manufactured and the one
pass it produced by accident.

The 36 / 80 pair that appeared in an earlier revision of this file was the bench doubling every
desk: while Workspace.Rebuild.Models held a rebuilt copy of all six desks, ConsoleBinder.BindRebuild
bound both the live desks and the bench copies. The bench is not in the place, BindRebuild no-ops,
and the test reports the installed-only figures - 18 levers / 41 lamps.
"""

for _name, _frag in (("DEC_87", DEC_87), ("DEC_88", DEC_88), ("PROG_ENTRY", PROG_ENTRY),
                     ("CL_ROW_NEW", CL_ROW_NEW), ("CL_NOTE_NEW", CL_NOTE_NEW),
                     ("CL_BUG_NEW", CL_BUG_NEW), ("CL_T33_NEW", CL_T33_NEW),
                     ("CL_BIND_NEW", CL_BIND_NEW), ("RD_NEW", RD_NEW)):
    assert "]==]" not in _frag, _name + " would terminate the doc long-string"
    assert '"' not in _frag, _name + " contains a double quote (CLAUDE 0.10)"
    assert "\\" not in _frag, _name + " contains a backslash (CLAUDE 0.10)"

# The two Luau snippets quoted inside the entries DO contain double quotes in the real source;
# they are re-quoted here without them on purpose so the Studio side can build the fragments from
# double-quoted Lua strings. Nothing else in the entries was altered.


def append(name, entry):
    p = os.path.join(D, name + ".md")
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8").rstrip("\n")
    io.open(p + ".bak9", "wb").write(raw)
    out = (text + "\n\n" + entry + "\n").encode("utf-8")
    io.open(p, "wb").write(out)
    print("%-14s %d -> %d (delta %+d)" % (name + ".md", len(raw), len(out), len(out) - len(raw)))
    return out


_BACKED = set()


def patch(name, old, new):
    p = os.path.join(D, name + ".md")
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8")
    n = text.count(old)
    if n != 1:
        print("ABORT %s: anchor count %d" % (name, n))
        sys.exit(1)
    if name not in _BACKED:
        io.open(p + ".bak9", "wb").write(raw)
        _BACKED.add(name)
    out = text.replace(old, new).encode("utf-8")
    io.open(p, "wb").write(out)
    print("%-14s %d -> %d (delta %+d)" % (name + ".md", len(raw), len(out), len(out) - len(raw)))
    return out


if __name__ == "__main__":
    decisions = append("DECISIONS", DEC_87 + "\n\n" + DEC_88)
    progress = append("PROGRESS", PROG_ENTRY)
    claude = patch("CLAUDE", CL_ROW_OLD, CL_ROW_NEW)
    claude = patch("CLAUDE", CL_NOTE_OLD, CL_NOTE_NEW)
    claude = patch("CLAUDE", CL_BUG_OLD, CL_BUG_NEW)
    claude = patch("CLAUDE", CL_T33_OLD, CL_T33_NEW)
    claude = patch("CLAUDE", CL_BIND_OLD, CL_BIND_NEW)
    readme = patch("README", RD_OLD, RD_NEW)
    trimmed = claude[:327] + claude[1653:]
    print()
    print("EXPECT = {")
    print('    "PROGRESS": "%s",' % roll(progress))
    print('    "DECISIONS": "%s",' % roll(decisions))
    print('    "CLAUDE": "%s",' % roll(trimmed))
    print('    "README": "%s",' % roll(readme))
    print("}")
