# -*- coding: utf-8 -*-
"""Append the round-7 entry to NIGHT_LOG.md (disk-only working doc, no module mirror)."""
import io

P = r"D:\rblxTRGproject\NIGHT_LOG.md"

BLOCK = """
---

## 第七轮 · 控制室外壳：修正而非重建（外加一次自己误导自己的对账）

### 起点：一个从来没有被量过的前提

`CLAUDE` §3.1 把「设施外壳 / 房间内部」列成待办，`NIGHT_LOG` 第六轮把它标成「下一块该动手的」。
两处都默认了一件事：**外壳是一个等着被填的空盒子。** 这一轮先量，前提当场塌了。

做法是让 `ShellKit` 先只跑**碰撞审计**，不写任何东西。它返回：

```
HARD=0   SOFT=713
```

`HARD=0` 说明 182 件计划件的肋深算对了 —— 与 561 件灯件零冲突。
**但 713 个软命中才是信息量所在**，于是被迫把四面墙结构 dump 出来：

```
Wall (东)    Union 40.1 x 21.25 x 0.75 底板 + 10 片 0.125 薄竖板 + 4 根通高肋
Wall (南)    下部板场 7.95 x 9.95 x 0.1 / 7.75 x 9.75 x 1（y 277.6..287.6）
             上部大板 21.9 x 10.55 x 0.75（y 287.6..298.1）+ 竖格栅 0.2 x 13.25 x 0.75
Wall (北)    南墙镜像
FrontWall    根本没有整片墙面 —— 是管道井，26.5 x 4 x 10 的梁从西墙跨到 x = 108.3
```

**四面墙本来就做满了。** 那 182 件会在手工做的板场上再压一层，
而且其中 **2 件会埋掉一个摄像头 `TextPart`（(141.80, 295.85, −0.71)）**。
计划整个作废：没有板、没有肋、没有压顶、没有凹槽、没有嵌条。**这个 kit 什么都不造。**

### 真正的缺陷：合法材质放在了错误的位置

量下来，房间自己早就有一套自洽的阶梯。壳面的 1,379 件里，
天花板带（`y_top > 296`）读作 `100 × 702 / 75 × 295 / 60 × 84 / 50 × 23`，
另有 16 件墙件本来就在 100。**只有两样东西掉在阶梯外面：**

1. **天花板板**（`Geometry.Unions.Union`，55.58 × 1.00 × 74.03 @ y 298.61）
   戴着 `DiamondPlate` **加上** `FacilityFloorPlate` @ `160,160,160` ——
   **地板自己的材质、地板自己的 variant，装在天花板上。** 另有 16 件墙件同样。
2. 墙是 `160`，`FrontWall` 有 13 件是 `205`。
   而 `RebuildKit` 的控制台调色是 hull 108 / post 86 / dark 75 / darker 60，
   甲板 68..83 —— **每一面墙都亮过最亮的大块台面**，
   于是家具成了亮墙上的暗块。这就是 `ART_DIRECTION` §2.1 那条红线，
   只不过是用色调说出来的。

**和 `DECISIONS` 84 同一类：一个合法材质，放在错误的地方，不产生任何报错。**

### ★ 差点改坏：判据从「亮度」换成「材质 variant」

第一版判据是**一刀切的亮度阈值**（`lum > 120`）。干跑直接显示它会动 **25 件灯板**
（`RebuildKit` 的 `light (163,162,165) Plastic` —— 调色注释明写必须保持 Plastic，
否则过曝成纯白）**加 2 盏琥珀信号灯**（`226,155,64`）。

**那是灯具，不是表面。** 把它们刷灰 = 为了修墙而把房间的照明删掉。

判据因此整体搬家：**戴 `FacilitySteelPanel` / `FacilityFloorPlate` 的是结构，
没戴 variant 的是灯具，一律不碰**；亮度只在结构集合内部决定哪些离群值被拉回来。

### 结果（实例读数，不是模块状态）

```
APPLIED  scanned=1379  recoloured=80  resteeled=25  skipped=1291  failed=0
```

八项核对全过：天花板板已变 `Metal / FacilitySteelPanel / (60,60,60)`；
亮度 > 120 的结构件 **0**；壳面上残留 `FacilityFloorPlate` **0**；
**27 件灯具原封不动**；`ShellKitOrigin` 记录 **88** 条（= 80 + 25 − 17 重叠）；
改后阶梯 `100 × 813 / 75 × 301 / 60 × 87`；样本 origin 属性
`160,160,160|Enum.Material.DiamondPlate|FacilityFloorPlate` 可解析；
`CullFolder.ControlRoom` 下 `ClickDetector` = **0**。

**壳面最亮的大面现在是 100，低于控制台 hull 的 108** —— §2.1 的红线在数值上成立了。

纯外观属性（Color / Material / MaterialVariant），未增删改移任何部件。

### ★★ 我花了一轮时间追一个不存在的分歧

四份文档（模块 + 磁盘）改完后对账，`docs_round7.py` 报**四份全部 MISMATCH**。
我先去试了各种候选哈希，又去查是不是全角标点 / 破折号打错了 ——
**全都不是。**

真因：**模块源码是 `return [==[` + 两个换行 + 磁盘正文 + `]==]` + 一个换行**，
而脚本里写的是**补一个换行**。一个字节的偏移，让四份全部误判。

定位方式：在 Studio 里对 `sub(Source, k, #Source - j)` 做 `k ∈ 12..14, j ∈ 4..6` 的网格扫描，
每个候选去撞磁盘的原始哈希。**`k=14, j=5` 四份一次全中。**

教训：**「记住的偏移量」本身就是契约的一部分，而且它会悄悄漂。**
对账应该用**不需要偏移量的形式** —— `roll(磁盘原始字节)`。
脚本已改成这个形式，EXPECT 换成 `59a40029 / 3dc6be87 / 74dd612d / 746e9237`。
（CLAUDE 仍按既定的 `b[:327] + b[1653:]` 剥掉磁盘专属的 §0.0 段。）

顺带踩到工具层的一个坑并记下来：**Bash 层会把 heredoc 里的 `\\n` 吃掉**，
于是我的探针脚本拿一个被解码过的锚点去比文件，永远 0 命中。
**含转义的脚本用 Write 工具落盘再跑，不要走 shell heredoc。**

### 文档对账（§0.0）

四份模块 + 磁盘，**逐哈希一致**：

```
PROGRESS   len=99222    hash=59a40029   (Phase 30)
DECISIONS  len=140545   hash=3dc6be87   (85)
README     len=32685    hash=74dd612d   (Rebuild 条目 + ShellKit / ControlRoomKit)
CLAUDE     len=50753    hash=746e9237   (§3.1，剥 §0.0 后)
```

### 下一步（优先级）

1. ~~文档镜像对账~~ **本轮完成**（含修掉自己的对账公式）。
2. **仍未开始：设施外壳的其余部分。** 第六轮量到四个容器 **`ClickDetector` = 0**
   （`MonitorsFacility` 1,364 / `RoomLights` 561 / `Alarms` 974 / `Lights` 2,659），
   但 `Facility` 有 16、`MovingParts` 30、`Geometry` 1，**不能当全外壳无绑定风险**。
   已量的设计语言：`Concrete`(125,120) 打底 + `DiamondPlate` + **纯黑 `Neon` 接缝** +
   `SmoothPlastic`(16,18,25)。**控制室的教训：先量，别假设它是空的。**
3. `MovingParts` vs `Mainframe` 的皮不一致（按容器名分配的遗留）。
4. 英雄资产 `generate_mesh` —— 本插件返回 NOT SUPPORTED，要走内置 Studio MCP。
5. `ART_DIRECTION` §3.5 屏幕内容故意押后；§3.6（堆芯青→紫）需用户拍板。
6. **素材上传** —— 被凭证卡住，工具已备好。

**§0.9：改完提醒用户 Ctrl+S。** 本轮改了**场景属性 105 处**（80 重着色 + 25 换材质，
扫过 1,379 件）与**四个文档模块**，**全在内存里，没保存就全丢。**
"""

raw = io.open(P, "rb").read()
old = raw.decode("utf-8")
if "第七轮 · 控制室外壳" in old:
    print("section already present -- ABORT")
    raise SystemExit(1)

out = (old + BLOCK).encode("utf-8")
io.open(P + ".bak7s", "wb").write(raw)
io.open(P, "wb").write(out)
print("NIGHT_LOG.md %d -> %d (delta %+d)" % (len(raw), len(out), len(out) - len(raw)))
