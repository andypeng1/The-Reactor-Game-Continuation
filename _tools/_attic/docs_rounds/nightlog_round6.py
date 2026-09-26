# -*- coding: utf-8 -*-
"""Append the round-6 entry to NIGHT_LOG.md (disk-only working doc, no module mirror)."""
import io
import os
import sys

P = r"D:\rblxTRGproject\NIGHT_LOG.md"

BLOCK = """
---

## 第六轮 · 材料遍扫补全（顺手证伪了「按形状重新分区」的收益）

### 起点：一次「按材质名过滤」留下的 36% 盲区

`CLAUDE` §3.1 挂着一条「材质分区的细化」。动手前先量现状，结果发现**不是分区不够细，
是上一遍根本没扫完**。那次遍扫的过滤条件是：

```lua
if d.Material == Enum.Material.Metal then
```

这是**对材质名过滤**，而它自己制造了盲区：**本来就写成 `DiamondPlate` 或
`CorrodedMetal` 的部件压根没进这个分支** —— 既没换材质、也没拿到 variant。
而且那次遍扫的汇总行只统计**它碰过的东西**，所以它**结构上不可能报出自己漏了什么**。

实测（除 `GameCoreTests` / `_MCPVisualTracking` 外全部顶层容器）：

```
Metal          48,546 打标      305 未打标
DiamondPlate    5,907 打标    3,194 未打标
CorrodedMetal  44,456 打标        0 未打标
```

`CorrodedMetal` 干净的**原因值得记**：`HEAVY` 那批容器是**显式 SET** 成
`CorrodedMetal` + `ReactorWallPlate` 的，从来不走过滤分支。
`DiamondPlate` 没有这条路径 —— **所以它就成了唯一崩掉的那一类**：
全场 **35%** 的 `DiamondPlate` 面渲染成库存菱形板，紧挨着 65% 带自定义地板贴图的同类件。
**同一个材质名、两种外观，而且不报错**，因为两种都是合法材质。

### 修法

补齐 **3,545 件**：`DiamondPlate` → `FacilityFloorPlate`、`Metal` → `FacilitySteelPanel`。
赋值**按 `Material` 映射、且只赋 `BaseMaterial` 匹配的 variant**，
所以不可能出现「赋值顺带把 `Material` 本身改掉」的副作用。
结果：`tagged 3,545 / failed 0 / untagged remaining 0`。
`CHS:SetWaypoint("CompleteMaterialTagging")` 起止各一次，Ctrl+Z 可回退。

现总数：**Metal 48,983 / DiamondPlate 9,103 / CorrodedMetal 46,951，未打标 = 0**。

> 这三个数和 §2.8 原来的 `49,758 / 5,906 / 44,456` **对不上是正常的** ——
> 那是首次遍扫当时的快照，之后的控制台重建 / 监视器重建 / 激光重做 / LED 条
> 都改过总数。**把快照当不变量读，是这次差点走错路的原因。** §2.8 已改成
> 「现测」并加注。

### 顺手证伪：「按几何角色重新分区」没多少油水

§3.1 那条 TODO 的另一半是「启发式可以更精细」。先把可行性量了 ——
对 `Facility`/`Geometry`/`CullFolder`/`Mainframe`/`MovingParts`/`ChamberWalls`
共 **70,871 件**按形状分类（薄横板 = 地板 / 薄竖板 = 墙 / 其余 = 块）：

```
FLOOR  9,797    WALL  430    CHUNK  60,644
```

**WALL 几乎为空。** 房间绝大部分是「块状」几何，**纯形状启发式没有多少可分配空间**。
真要细分得按「容器意图 + 形状」混合判定。另外量到一条遗留不一致：
`MovingParts`（9,206 件 `ReactorWallPlate`）与 `Mainframe`（14,016 件 `FacilitySteelPanel`）
**同属机械却拿了两种皮** —— 因为当年一个在 `HEAVY`、一个在 `CONSOLE` 名单里，
是**按容器名**分配的结果。**留待下一轮**，没动。

### ★ 我自己踩了文档里写着的那个坑

第一次推 `CLAUDE` 的四段替换时用了 `string.gsub`，**结果一个字都没改**
（`body` 停在 47,185，哈希 `6bf9a1af` = 改前值）。
原因正是本文件反复记的那条：**这些字面量里有 `*`、`(`、`.`、`-`，在 Lua 模式里全是魔法字符。**
`string.gsub` 把它们当模式解释，于是匹配不到。

改成 **`string.find(hay, old, 1, true)` + `string.sub` 拼接**（pattern-free surgery）后一次通过。
**`DECISIONS` / `PROGRESS` 用的是纯追加（不经 gsub），所以第一次就成功了 ——
两者对照正好证明问题出在 gsub，不在文本本身。**

### 文档对账（§0.0）

三份模块 + 磁盘，**逐哈希一致**（长度只作参考，不当判据）：

```
DECISIONS  body=136402  hash=252eb4aa   (新增 84)
PROGRESS   body=97645   hash=4d2e5469   (新增 Phase 29)
CLAUDE     body=49133   hash=014ac9ae   (§2.8 / §2.9 / §3.1 / §6)
README     未改动
```

`CLAUDE` 磁盘 raw = 50,459（含 §0.0 的 1,326 字节磁盘专属段），body 用既定的
`b[:327] + b[1653:]` 裁切；**改前先断言这个裁切得到 47,185 / `6bf9a1af`**，
不成立就不动手 —— 否则裁切偏了会拿一个错误的哈希去对账。

顺带更正两处旧数：`Workspace` 的 **ClickDetector 实例 = 941**（旧记 1,023，
§2.9 与 §6 都已改）；以及「设施外壳没有绑定风险」这句**只对四个容器成立** ——
`MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` 确实 `CD=0`，
但 `Facility` 有 **16**、`MovingParts` **30**、`Geometry` **1**。

### 未删的东西（记下来免得以后误判）

`MaterialService` 里有 3 个**空壳 variant**：`MaterialVariant`、`MaterialVariant1`
（base 都是 Plastic）、`CoolantRepeatingTexture`（base Concrete）。
**都没有 `Texture` 子节点、都被 0 个部件引用。** 前两个的形态
和 §5.3 警告的 `generate_material` 空产物一模一样，大概是那一步的残渣。
**故意不删**：0 引用的 variant 视觉上是惰性的，删它**不给玩家带来任何可见收益**，
却越过了「只改外观属性」的安全线。记在这里，免得以后的遍扫把它当成有意为之。

### 素材包的意外收获（对那条被卡的音效任务有用）

`TRG Sounds & Images pack` 的**文件名末尾就带原始 asset id**
（`particle_smoke_528256032.png` = 场景里用得最多的那张常态贴图，
`rbxassetid://528256032`，121 个发射器在用；`Radioactive Particle_9264702528.png` =
`9264702528`，就是那 20 个 `Aura`）。**所以「重传 + 改指向」这条路是通的，
而且映射可以机械化。**

实测包内：**836 个不同 id**（`.png` 407 / `.ogg` 422 / `.mp3` 7），只有 2 个文件
名字里没有 id（`Hyffrds face !!!.png`、`README.txt`）。
场景侧不同 id = 657，所以这个 join 是「两个集合求交」。

**join 工具已经写好放在 `_tools/`**：`assmap.py`（枚举包 + 对账）与
`scene_dump.lua`（在 Studio 里打印 `KIND<TAB>id<TAB>count`）。
**没跑完的原因**：命令栏 VM 里 `writefile`/`readfile`/`appendfile`/`listfiles`
**全是 `nil`**（本轮实测确认），所以场景侧那 657 行**只能手抄**才能落盘对账 ——
而这活儿是给**被卡的**上传任务做准备的（缺 `ROBLOX_OPEN_CLOUD_API_KEY` / `ROBLOXCORURITY`，
且**不允许自行去翻凭证**）。等用户在、能授权上传时再跑，那时手抄一次的代价才值得。

### 下一步（优先级）

1. ~~文档字节对账~~ / ~~监视器新调色复核~~ / ~~Task A 激光~~ / ~~`TempLabel` 第二写入者~~
   / ~~主监视器示意图~~ / ~~常态氛围 VFX~~ **均已完成或已证伪**。
2. **材料一致性** —— **本轮完成**（3,545 件，未打标归零）。
3. **仍未开始：设施外壳 / 房间内部** —— 下一块该动手的。
   本轮补了两条走之前必须知道的：
   - **不是全部无绑定风险**：`Facility` CD=16 / `MovingParts` 30 / `Geometry` 1；
   - **`ART_DIRECTION` §5 明确记着「没有走廊 / 建筑结构的照片」**，
     所以外壳**要以本 place 原版为准**，不能照官方素材想象结构；
     §3.6 的「堆芯青→紫」是**新增视觉机制，需用户拍板**，不要自己上。
   控制室实测：地板 = `Geometry.Floors.ControlRoomFloor`（`58,60,64` 菱形板，51×0.8×70，
   y=276.5），上方 y=298.6 的 `Geometry.Unions.Union`（`160,160,160`）是天花板。
   `ART_DIRECTION` §2.1 的红线仍然有效：**控制台不得与环境脱节。**
4. **`MovingParts` vs `Mainframe` 的皮不一致** —— 按容器名分配的遗留，见上。
5. 英雄资产 `generate_mesh` —— 注意本插件的 `generate_mesh` / `generate_material`
   **返回「NOT SUPPORTED in 3rd-party plugins」**，要走内置 Studio MCP。
6. `ART_DIRECTION` §3.5 屏幕内容**故意押后**；§3.6 等用户拍板。
7. **素材上传** —— 被凭证卡住，工具已备好。

**§0.9：改完提醒用户 Ctrl+S。** 本轮改了**场景属性 3,545 处**（材料 variant）
与**三个文档模块**，**全在内存里，没保存就全丢。**
"""

raw = io.open(P, "rb").read()
old = raw.decode("utf-8")
if "第六轮 · 材料遍扫补全" in old:
    print("section already present -- ABORT")
    sys.exit(1)

out = (old + BLOCK).encode("utf-8")
io.open(P + ".bak6", "wb").write(raw)
io.open(P, "wb").write(out)
print("NIGHT_LOG.md %d -> %d (delta %+d)" % (len(raw), len(out), len(out) - len(raw)))
