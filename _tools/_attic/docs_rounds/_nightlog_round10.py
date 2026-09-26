# -*- coding: utf-8 -*-
"""Append the round-10 entry to NIGHT_LOG.md (disk-only working doc, no module mirror).

Round 10 is unusual: the round's ONLY artifact is _tools/SpawnKit.lua on disk, because the
Studio plugin's Luau channel is hung and stayed hung. So this entry is half finding, half
incident report -- and the incident is mine.
"""
import io
import sys

P = r"D:\rblxTRGproject\NIGHT_LOG.md"

BLOCK = r"""
---

## 第十轮 · 唯一能用的出生点离游戏 1,370 studs（附一次我自己把 Studio 写死的事故）

**这一轮的产物只有磁盘上的 `_tools/SpawnKit.lua`。** 没往场景里写一个字节 ——
原因是`Studio` 的插件 Luau 通道被我自己的一个死循环卡死了（见 §4），
**这一轮的后半段全程在「只能读缓存状态、不能执行代码」的条件下度过。**
先把发现记全，事故记在 §4-§5。

### 1. 真正的发现：五个出生点里，唯一能用的那个在虚空里

`Workspace` 下共 **5** 个 `SpawnLocation`。`Teams` **是空的（0 个子件）**，
而 Roblox 的规则是：**对没有队伍的玩家，只有 `Neutral = true` 的出生点会被选用。**
实测这五个的分布是：

```
TeamSpawns.Spawn1..4       x 257,  y 277.1,  z 29.4 / 36.9 / 44.4 / 51.9
                           Neutral = false,  TeamColor = White
                           look = (-1, 0, 0)  -- 朝西，正对 135 studs 外的控制台排

TeamSpawns.SpawnLocation   x 233,  y 402.9,  z 1370.0
                           Neutral = true     -- 所以这是唯一活着的一个
```

**于是「唯一能用的出生点」就是「离游戏最远的那个」——1,370 studs。**
它是一块 **20 × 0.5 × 4** 的板子悬在空处：从它垂直向下的射线**500 studs 内什么都没有**，
四向唯一实体是东边 43 studs 的一面墙（`RLGatewayRoom.Floor`），
头顶唯一的东西是 18.5 studs 上一盏天花板灯（`MovingParts.LoungeCeilLightPart`）。
本 place 的 `FallenPartsDestroyHeight = -500`。

**在场确认**：`andypeng1NB team=NONE pos=(233.0, 406.1, 1370.0)`。

那四个朝向正确的**永远不可能触发**。它们的朝向就是作者的意图写成向量：
**开局正对控制台排与监视器组**。

**五个全是 `Transparency = 1`。** 所以这个缺陷**改前改后都看不见** ——
它不是「画面不对」，是「玩家从错误的地方开始」。

### 2. 我自己的第一个假设是错的（不是「掉进虚空」）

第一版结论是「角色会一直往下掉」。**探针打脸**：采样 5 秒，
`Y` **恒定在 406.1**、`state=Running`、`HP=100`、`FloorMaterial=Plastic` ——
**角色是站在板子上的**，不是坠落。

射线之所以报 `VOID`，是因为**射线起点在板子内部**。
所以缺陷是「一块 20×4 的隐形板子悬在空中，三面是虚空」，
而不是「坠落循环」——**一步踩空才是掉到 −500。**

> 又一遍本项目的同一课：**射线从被测物体内部起步，量到的是被测物体自己。**

### 3. 修法：位置判定，不是名字清单；`SpawnKit` 已 staged

两条规则，零几何体改动：

```
控制室包络之内  ->  Neutral = true
控制室包络之外  ->  Neutral = false
```

`Enabled` **五个一律不动**，所以那个流浪出生点**没有被废掉**，
只是**不再是「无队伍玩家」的回退项**。四个能用的顶掉一个坏的，`Revert()` 全部还原。

`_tools/SpawnKit.lua` 已按 `ShellKit` 的同一套约定写好
（`targets()` 枚举 / `decide()` 是规则唯一住所 / `Scan()` 只读干跑 /
`recordOnce()` 首次改动前把原值写进属性 / `ApplyAll()` **在「扫出来无事可做」时拒绝运行** /
`Verify()` 事后回读 / `Revert()`）。
安装目标 `ServerScriptService.GameCore.Rebuild.SpawnKit`，**等通道恢复即可装**。

**包络为什么是 x = 270 而不是房间的 x 上限 256**：那四个出生点在 **x = 257**，
比房间自己的 x 范围（−183..256）**正好多 1 stud** ——
因为一块 2×2 的板子中心落在 257 上时会**跨过边界**。
所以包络按**板子的外表面**闭合，不按墙心。y（250..320）与 z（−70..70）
**各自独立地**把流浪板子排除在外（它在 402.9 和 1370），
**所以这个判定不靠单一轴成立。**

**判据为什么用位置而不是名字清单**：`DECISIONS` 84 和 86 各自抓到过一次名字清单出错。
**容器名字记录的是「它当初被放在哪」，不是「它是什么、它后来在哪」。**

### 4. ★ 事故：我自己写的一个不 yield 的死循环，把 Studio 主线程写死了

这是本轮最该记的一条，因为**它比上面那个发现重要**。

我发给 Studio 的一段测量脚本里，残留了一个「向上走找顶层容器名」的半成品循环：

```lua
local m = d.Parent and d.Parent.Name or '?'
while m and m ~= d.Name do
    local up = d.Parent          -- 赋了 never use 的变量，m 从不改变
end
```

`m` 与 `d` 在循环体里**从不改变**，所以除了「父件名恰好等于自己的名字」这一种情况，
**它必然无限循环**。而且我**一个 `task.wait()` 都没写** —— 纯自旋，**不 yield**。

**后果与诊断**：Roblox 的插件代码跑在 **Studio 主线程**上，Luau 是**协作式**调度 ——
**一个不 yield 的循环没有任何东西能抢占它**。所以症状不是「那个调用失败」，
而是**整个插件 Luau 通道死掉，而且官方插件与第三方插件一起死**：

```
还能答的（走缓存状态，不需要活的插件往返）:
  rblx_list_roblox_studios       -> 正常列出 8b90fb6d-...
  rblx_get_studio_state          -> 正常返回 Edit / Available DataModels: Edit
  rblx_get_console_output        -> 正常

死掉的（需要一次新的插件往返）:
  rblx_execute_luau              -> Target is not reachable
                                    (createExecuteLuauBridge_loadCodeAsync, Edit)
  rblx_script_read               -> ReadFileTool_readFile
  rblx_search_game_tree          -> GameTreeTool_explore
  第三方 execute_luau             -> Studio plugin connection timeout
  第三方 get_handler_health       -> Studio plugin connection timeout
```

**「两个插件同时死」这一条本身就是判据**：我最初以为只是官方插件的桥坏了，
但**两个互不相干的插件不可能同时坏**，除非它们共用同一个被卡住的主线程。

**恢复尝试（全部失败）**：12 s / 45 s / 120 s / 240 s 间隔重试，跨度约 14 分钟，
之后又过了更长的时间 —— **一次都没恢复**。这与诊断一致：
**一个已经在跑的 Luau 线程没有超时、没有被杀、也没有被抢占的路径。**

### 5. 我为什么没有强行关掉 Studio（这条是判断，要用户拍板）

`manage_instance` 能 `close`，但 **`launch` 必须指定 source**：

- `source: "published_place"` 装的是**最后一次发布**的版本，
  **不是**用户本地这次编辑会话里的内容 —— 可能**静默回退掉一大批重建工作**；
- 只 `close` 不 `launch`，留给用户的是一个**关掉的 Studio、没开任何 place** ——
  **比一个「用户自己重启一下就好」的 Studio 更糟。**

所以**两条路都比现状差，我没动。** 正确做法是**用户重启 Studio**
（如果 UI 也冻住了，用任务管理器结束进程；重启时 Studio 会提供自动保存/恢复）。

**这一轮没有任何场景改动处于风险中**：本轮所有写入**要么是只读探针，
要么是两次 Play 测试**，而 Play 期间的写入是**运行时副本、停止即丢**。
所以这里没有「没保存的活」这回事。

> **教训（写给下一轮的我）**：命令栏/插件里的脚本**不是沙箱**。
> 「不写 `task.wait()`」在这里**不是风格选择，是能冻住整个 IDE 的手段**。
> 发任何带 `while` / `repeat` / `for` 的探针之前，
> **先问「如果条件永远不成立，它靠什么退出」** —— 答不上来就别发。

### 6. 顺手结掉的一项：材质分区「不一致」实测不是缺陷

`CLAUDE` §3.1 挂着「材质分区细化」。本轮用两遍 AABB 量完了：

**`ReactorWallPlate` 与 `FacilitySteelPanel` 的分界跟的是「设施哪一侧」，不是容器名。**

```
反应堆侧  合计 37,592   MovingParts 9,206 / CoolantReserviors 12,754 /
                        ReactorCBLs 7,487 / GravitationShafts 2,321 /
                        ChamberWalls 1,859 / PowerExtractionAssembly 1,858 /
                        METU 1,219 / GravatronUnit 888
控制侧    合计 29,209   Mainframe 14,016 / Facility 7,077 /
                        QuantumMainframe 4,799 / Geometry 3,223 /
                        MainframeToolStorageCull 94
```

AABB 那一遍是决定性的：`Mainframe`、`QuantumMainframe`、`CoolantReserviors`、
`METU`、`GravatronUnit` 在控制室**内部有 0 个部件**
（`Mainframe` 坐在 X ≈ 366–516，而控制室的 X 上限是 256）。

**两间房、两种皮 —— 是合理的，不是缺陷。** 强行重分区 9,206 个部件是纯粹的搅动。
按本项目自己的先例（反应堆舱那一轮结论也是「无需修正」、且**故意不写 kit** ——
**一个 scan 报「无需修正」的 kit 是负债**），此项**结案，不动任何东西**。

### 7. 本轮工具坑（新增，其中第一条差点让我得出反向结论）

- **`Workspace.StreamingEnabled = true`，所以「Client 数据模型里做的空间扫描」全部无效。**
  客户端只持有**附近**的实例。我用 Client 模式跑的那一遍报了**只有 1 个 SpawnLocation**，
  并且显示出生点的「地板」是 y=0 的 Baseplate、**六个方向全 OPEN** —— 物理上不可能。
  真相是：控制室被流式卸载了，而那块「地板」是**玩家自己的** `Blue Council Halo.Handle` @ y=409.4。
  **改到 Edit 测量，5 个出生点和真正的地板才全部出现。**
- **射线从被测部件内部起步 → 报 VOID。** 见 §2，这就是我第一版假设的来源。
- **第三方 `execute_luau` / `eval_server_runtime` 在本环境不可用**（`Connected peers: edit` only）；
  能用的是官方 `rblx_*` 那一套。（已是记忆项，本轮再次确认。）
- **`rblx_start_stop_play` 刚返回 "Game Stopped" 之后**，
  `createExecuteLuauBridge_loadCodeAsync` 会**偶发**报两次 `Target is not reachable`，
  **重试即成功** —— 与 §4 那种永久挂死**症状相同、性质不同**，别混为一谈。
  区分方法：**重试一次。** 偶发的会过，永久的不会。
- **一次调用里同时做「全 Workspace + ServerStorage 后代扫描」会超时**（`-32001`）。
  拆小。（这条第九轮也记过，本轮又踩。）
- 控制台是 **GBK**：`python -c` 里打印 `\u2b50` 之类会 `UnicodeEncodeError`。

### 8. 下一轮要做的（通道恢复后，按顺序）

1. **装 `SpawnKit`**：`_tools/SpawnKit.lua` -> `ServerScriptService.GameCore.Rebuild.SpawnKit`，
   先 `Scan()`（只读干跑）再 `ApplyAll()`，然后 `Verify()`。
2. **Play 实测**：确认角色出现在**控制室里、正对控制台排**（这是 `Spawn1..4` 的朝向意图），
   而不是 1,370 studs 外那块板子上。
3. **同一步补文档**（§1.4）：`PROGRESS` 一个新 phase + `DECISIONS` 一条 ——
   出生点缺陷、**位置判定而非名字清单**这条规则、以及**自旋死循环 = 冻住 IDE** 这条仪器教训。
   **`PROGRESS` / `DECISIONS` 是模块的镜像，不许先在磁盘上写。**
4. 回到 `ART_DIRECTION` §3.1 剩下的真项：**设施外壳与房间内部的装饰**
   （`MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` 实测是灯具/监视器装置，不是建筑外壳）、
   **英雄资产**（拉杆握把用 `rblx_generate_mesh`；堆芯外壳已有 `CoreKit`）。

### 9. 仍需上层的判断（不能由我定）

- **Studio 需要用户重启**（§5）。这是本轮唯一的阻塞项，且**只能由用户解除**。
- 出生点修法本身（四条规则 vs 三条、要不要把流浪板子 `Enabled = false`）
  —— 我按 §3 做了决定，但**装之前值得你看一眼**。
- **几何体重做的累计缩水要当面报**（沿用第九轮）：实测把「所有东西都要重做」收敛成了
  「控制室**修正**而非重建、反应堆舱**实测无缺陷**、四个所谓『设施外壳』容器
  **实测是灯具/监视器装置不是建筑外壳**」。**这些是证据，不是借口，但需要你拍板。**
- `ART_DIRECTION` §3.6（堆芯青→紫）等用户确认；§3.5（监视器内容暗底 + 亮绿标题条）故意押后。
- 素材上传仍被凭证卡住（**不允许自行翻凭证**）。
- `MovingParts` vs `Mainframe` 同属机械两种皮 —— 偏好问题，不是缺陷。

**文档状态：本轮没碰任何 Section。** 四个 ModuleScript 与磁盘四份 `.md` **都停在
`PROGRESS 120392/75085461`、`DECISIONS 177159/08b72446`、`CLAUDE 62580/2b6be228`
（§0.0 磁盘专属 2524）、`README 35125/4975dff8`** —— 即 `verify_docs.py` 收口时的那组值，
**本轮一个字节都没动**，所以不需要重新校验。
"""

raw = io.open(P, "rb").read()
old = raw.decode("utf-8")
if "第十轮 · 唯一能用的出生点" in old:
    print("section already present -- ABORT")
    sys.exit(1)

if "local up = d.Parent" in old:
    print("the runaway snippet is already in the log -- ABORT (would double-append)")
    sys.exit(1)

out = (old + BLOCK).encode("utf-8")
io.open(P + ".bak10", "wb").write(raw)
io.open(P, "wb").write(out)
print("NIGHT_LOG.md %d -> %d (delta %+d), backup NIGHT_LOG.md.bak10"
      % (len(raw), len(out), len(out) - len(raw)))
