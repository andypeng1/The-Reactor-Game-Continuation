# S.R.S.U. — Subspace Radiation Suppression Unit（设定集）

> **状态（2026-10-11 当天更新两次）：设定 + 实物。**
> 第一次是用户原话「Subspace Radiation Suppression Unit - S. R. S. U 你给他添加点设定」；
> 当天晚些的第二句是 **「建模我做了 BottomSuppressionStructure」** —— 于是这件东西
> **从纸上进了 place**：六台一组，实例名 **`BottomSuppressionStructure`**，
> 装在 `Workspace.Folder.Chamber`（重建台）。**逐项实测见 §4.5。**
> **代码侧仍然是零**：不接 `ReactorBackend`、不进 `Stats`、不新增任何控制原语 ——
> 现有玩法机制一个字没动（§1.4 第 1 条）。要不要接进模拟，见 §9；
> `QUESTIONS.md` **S1** 的 **B** 已经由他那一句答掉了。
>
> **来由：** 2026-10-11 用户原话 ——
> 「Subspace Radiation Suppression Unit - S. R. S. U 你给他添加点设定」。
>
> **名字的出处（说清楚，免得以后有人以为它是原版的）：** 全仓库 / 全 Wiki 扫描
> **零命中**（`grep -ri 'suppress'` 在 `reactor.fandom.com` 的 207 KB 快照里 0 条，
> `Suppression Unit` 0 条）。**它是新造的，不是复刻。**
> 原版那侧的一次实例扫描**没跑成**（`:28429` 执行器拒连，WinError 10061），
> 所以「原版里没有这个东西」这句目前**只由 Wiki + 仓库两份证据撑着**，不是三份。

---

## 0. 一页速览

| 项 | 值 |
|---|---|
| 全称 | **Subspace Radiation Suppression Unit** |
| 缩写 | **S.R.S.U.**（本项目的点号缩写惯例：`S.A.M.O.S.` / `M.A.S.S` / `H.D.E.F` / `P.E.A` / `M.E.T.U` / `C.B.L`） |
| 型号 | S.R.S.U. **Mk II** |
| 制造商 | **Synthesis Manufacturing**（正典，手册 #91 / #130 逐字） |
| 实物件名 | **`BottomSuppressionStructure`** —— place 里的实例名；设定里的全称是它的型号名 |
| 装在哪 | 堆芯**底部**：六台一组、**60° 均布**（az 0/60/…/300），环半径 **54.35**，全都 **y = 34.76**；**正好嵌在洗涤环 `RadiationScrubberUnitMK2`（六台，az 30/90/…/330，r ≈ 56.1，y = 36.90）的内侧、下方、错开 30°** |
| 干什么 | **不是挡辐射，是把它抵消掉。** |
| 一句话 | M.A.S.S 洗腔体、H.D.E.F 挡控制室，**S.R.S.U. 掐源头**。 |
| 玩家能不能操作 | **不能**（设定如此，见 §8）—— 它随启动序列自动通电 |

---

## 1. 名字怎么拆

- **Subspace** —— 堆芯本身就是「a wormhole or gateway into Subspace」（手册 #91 逐字）。
  辐射的来源**不是燃料**，是**那道门**。启动序列里那行
  `<b>[WARN]</b> - SUBSPACE RIFT ACTIVE, RADIATION WARNING` 说的就是它。
- **Radiation** —— 单位是 **roentgen（伦琴）**。原版监视器读的就是
  *"chamber radiation in roentgens"*。
- **Suppression** —— 关键词，而且**和 scrubber 是两个词**。抑制 ≠ 屏蔽 ≠ 洗涤。
- **Unit** —— 模块化单元，可单台换、单台校准（同 M.E.S 有 MkII 变体那套思路）。

---

## 2. 它为什么必须存在（世界观里的那个缺口）

设施原本有两层防线，**两层都在下游**：

| 层 | 设备 | 在哪一侧 | 正典里的代价 |
|---|---|---|---|
| 腔体洗涤 | **M.A.S.S Rails** | 辐射**已经产生之后** | 降低可提取的 net output（手册 #105 / #139） |
| 房间屏蔽 | **H.D.E.F** | 控制室**这一侧** | integrity 持续衰减；E-Power 能补它，但补的时候会过热（手册 #125 / #135） |

**上游没人管。** 门就在那里开着，泄漏出来的东西先填满腔体、再去压 H.D.E.F，
而这两层都只能**承接后果**。

S.R.S.U. 的定位就是这个缺口：**在源头把泄漏抵消掉。**
三层于是闭合，且三层的动词各不相同 —— 这让它不抢任何现有设备的活：

> **源头 抑制（S.R.S.U.） → 腔体 洗涤（M.A.S.S） → 房间 屏蔽（H.D.E.F）**

---

## 3. 原理（自洽的伪科技，别拿它当物理）

**① 为什么常规屏蔽没用。**
腔体里跑的不是中子通量。那道门吐出来的是**相位噪声** ——
一堆与本地时空不同相的场涨落。铅和水对**通量**有效，对**相位**近似透明，
所以加厚墙体不会让读数掉一格。旧方案之所以是「洗」（M.A.S.S），
正是因为能做的只有**把已经泄进腔体的那部分捞走**。

**② 它怎么抵消。**
每个作业面朝堆芯发一束**反相参考波**，六束按三相分组、在裂隙口叠加，把
泄漏场的**振幅**按相位差压下去 —— 不是吸收，是**对消**，
所以单元本身不发热、不积垢，读数掉下来的时候腔体是**冷**的。

**对消的是源头那一份**；从腔壁上弹回来、会再填回去的那一份，由每台外侧的
**混凝土屏蔽板**收尾（就是实物里的 `SuppressionPanel`，§4.5）。
这也解释了实物为什么一台里**走线走管的件比屏蔽板多得多** ——
`ConnectionNode` 186×2 vs `SuppressionPanel` 22×2：**它主要是一台带电的机器，不是一堵墙。**

**③ 为什么是六台（三相 × 两两正对）。**
实物是**六台**（§4.5）：每相由**一对正对的作业面**产生，6 = 3 × 2。
**单台**失谐只会让那一相弱掉一半 —— 读数是**慢慢**往上爬的，不是跳变；
**一相的两台都失谐**，合成场才**塌成两束**，覆盖出现一道缝，缝的方位上读数先涨。
**这是设定里唯一可被玩家看见的失效形态**。
（六台也是它为什么刚好嵌得进去：**每 30° 一座洗涤塔，每 60° 一台抑制台**，两圈错开一格。）

**④ 它为什么会失谐。**
EFE / Equinox 会把单元扔出相位（手册 #93：Equinox 对电子设备有破坏性影响）。
**这时候单元没坏**，只是不同相了 —— 拧回来就行。
这一条刻意对齐正典里那句「coolant sensory equipment has a tendency to be
unreliable… 需要手动干预校准」的调子：**设施里的精密东西都要人伺候。**

**⑤ 为什么不全功率常开。**
抑制场与 **P.E.A 抽取回路共用相位参考**。场越强，可提取的净输出越低 ——
**取舍的类型和 M.A.S.S Rails 完全一样**（手册 #105：M.A.S.S 会干扰堆芯能量输出，
而且「can be mitigated with a lower M.A.S.S Power Level」）。
**它的价钱是玩法里早就有的那种价钱，不是新发明的一种。**

---

## 4. 外观 / 美术规格

底子按 `ART_DIRECTION.md`：近黑机身 + 青色发光 + 少量暖色点缀、黄黑警示。
**下表是「将来接逻辑时」的状态配色提案** —— 已经建出来的实物用的是它**自己**的一套
蓝/红（§4.5 末尾），跟这张表**不是同一套值**；真要统一，统一到实物那边去。
表里的键都取自本 place 实测过的键（`src/ReactorBackend/Config.luau` 的 `Visual`），
一个都不要新调：

| 状态 | 颜色键（实测值） | 为什么是它 |
|---|---|---|
| 待机 / 未通电 | `Off` (45,45,45) | 场未建立 |
| 场建立（健康） | `Nominal` (137,255,147) | 本 place 自己的「一切正常」绿 |
| **失谐** | `Amber` (255,128,1) | 这个键的语义**本来**就是「在役但不可用」—— 失谐正好是它 |
| 对消放电的一瞬 | `Yellow` (240,220,60) | 与「可点火」共用一个键 |
| 过载 | `Fault` (255,70,40) | |
| 相位参考丢失 | `Purple` (150,60,220) / `Blue` (60,130,240) | 与 CBL 的状态码同族 |

**形态（规格）：** 扁柱体 + 面向堆芯的一面**发射环**（不是镜面，是环形放电口），
背面接两路：一路冷却、一路相位参考线缆（参考线缆**要能看出来是往 P.E.A 那边去的** ——
这是 §3⑤ 那条取舍的唯一视觉线索）。

> **实物和这条规格不一样 —— 以实物为准（§4.5）。** 他建出来的是一台**作业面**：
> 38.79 长的切向主梁 + 两套成对的节点/格栅/灯 + 外侧的混凝土屏蔽板，
> **不是「一个扁柱体」**。本节其余部分（尤其是下面那张灯色表）都还是**提案**。

**同族件：** `_tools/blender/` 那批（`radiation_scrubber` / `laser_port` / `chamber_grate`
/ `chamber_wall_24` / `ring_bridge_18_24` / `transition_pillar`），共用件是 `trg.py`。
设定上 S.R.S.U. 是 `radiation_scrubber` 的**祖辈** —— 手册 #96 说 M.A.S.S 是
「deionization 腔体里那些 scrubber 的放大版」，那就让 S.R.S.U. 长得像
**同一族的更老、更笨、更贵**的那一件。

---

## 4.5 实物 —— 重建台里已经有的那一圈（2026-10-11 逐项实测）

用户原话：**「建模我做了 BottomSuppressionStructure」**。
下面每一个数都是从 place 里**读回来的**（`execute_luau`，只读），不是照设计稿抄的。
这一节取代了本文件早先那句「三台、120°、装在 collar 上」—— 那是设定稿，
**实物是六台、60°、装在堆芯底部**。

**摆在哪：**

| 项 | 实测 |
|---|---|
| 实例名 | `BottomSuppressionStructure`（**同一个父级下有 6 个同名兄弟** —— Roblox 允许兄弟重名，§0.22） |
| 在哪 | `Workspace.Folder.Chamber` 里 6 台；`Workspace.Folder` 里另留 **1 台母板**（543 件、15 个子件、比成品多 2 个散件 + 一个 `Frame`）。（`Workspace` 下有 **8 个**叫 `Folder` 的东西，所以认路要靠 `…Folder.Chamber` 这个子件关系，别靠名字。） |
| 环的几何 | 中心 = 堆芯轴 **(−12.16, −85.41)**；半径 **54.35 ± 0.03**；方位角 **0 / 60 / 120 / 180 / 240 / 300**（±0.1°）；**六台全在 y = 34.76** |
| 离地多高 | 腔体底板在 y ≈ **11.13**（正下方射线 23.63）→ 这一圈**悬在底板以上 21.7 stud** |
| 每台多大 | **38.79（切向）× 3.78（高）× 7.59（径向）**，541 件 |
| 和洗涤环的关系 | `RadiationScrubberUnitMK2` 六台在 **r ≈ 56.1、y = 36.90、az 30/90/…/330** —— 新环在它**里侧 1.75、下方 2.14、错开 30°**，**正好落在六座洗涤塔的空档里** |
| 旁边还站着什么 | 以堆芯轴为中心的一层**壳**：`Union` 119.2×10.8×117.4（跨 **y 27.0–48.5**）＋ `BottomLine` 117.3×0.2×116 的板（y ≈ 37.0–37.5）。新环在**这层壳的半径以内** |
| 有没有撞上 | **有，很小**：每台的主梁两端都插进**相邻洗涤塔 `Frame` 的零件**里（`GetPartsInPart` 逐件量的：每台 3–4 件，y=36.9），另外每台都碰到那层壳。**深度没量**（`GetPartsInPart` 只回答是/否） |

**每台由什么组成（541 件，全部成对）：**

| 子件 | 台数 | 件数 | 实测尺寸 | 备注 |
|---|---|---|---|---|
| `ConnectionNode` | ×2 | 186 | 3.08×3.27×0.9 | **占掉一台的三分之二**；带 `RopeConstraint`（一台 18 根绳/线）—— §3⑤ 那条「相位参考线缆」在实物里就是它 |
| `SuppressionPanel` | ×2 | 22 | 5.47×2.92×0.1 | **混凝土块 + 5.85 高的金属立柱**；坐在 r ≈ **56.8–57.4**，比作业面本体更靠外 |
| `Grate` | ×2 | 17 | 3.17×5.9×0.53 | 带 SurfaceGui 文字 |
| `ManagementNode` | ×2 | 21 | 1.1×3.13×0.13 | 带 SurfaceGui 文字 |
| `Light` | ×2 | 12 | 1.05×2.98×0.21 | |
| `RedLight` | ×2 | 12 | 2.97×0.19×0.8 | |
| `Frame` | ×1 | — | 38.79×3.78×6.89（UnionOperation） | 主梁 |

**每一类子件都是两个** —— 就是 §3③ 里「一相 = 一对正对的作业面」的物理形态。

**它自己带的字（实物上本来就有，不是本文件的文案候选）：**

- `BOTTOM CHAMBER GRATE POINT`（在 `Grate` 上）
- `BOTTOM CHAMBER CONNECTION NODES`（在 `ManagementNode` 上）

**它自己带的灯（实物自己的一套值，不是 `Config.Visual` 那套）：**
蓝 `PointLight` `(0, 0.333, 1)`；红 `SurfaceLight` `(1, 0.313726, 0.313726)` ×2；
白 `SurfaceLight`；红 `PointLight`（挂在粒子附件上）。粒子两套：
`rbxassetid://10809840874`（rate 3）、`rbxassetid://7142136429`（rate 5），每台各 12 个。

> **没量到的（说清楚，别当成量过了）：**
> ① 环**正上方**打了 200 stud **打空** —— 但「打不到」不等于「没有东西」
> （可能是 `CanQuery = false`），所以关于天花板/上盖**一个字都不写**。
> ② **径向范围不能用包围盒对角线去推。** 一根 38.79 长的切向主梁，
> 它的 AABB 半对角线会把它算成「伸到 r ≈ 32」—— 那是量法的产物，不是几何。
> 能用的只有两句话：**本体在 r = 54.35，屏蔽板在 r ≈ 57**。
> ③ `:28429` 那侧（原版）**这一轮仍然拒连**（`WinError 10061`），
> 所以「原版没有这件东西」依旧只由 Wiki + 仓库**两份**证据撑着。

---

## 5. 场内怎么读它（给玩家的信息面）

监视器一行 / 报警条（语气照抄启动序列那行 `[WARN] - SUBSPACE RIFT ACTIVE, RADIATION WARNING`）：

```
S.R.S.U. FIELD NOMINAL
S.R.S.U. SUPPRESSION 62%
S.R.S.U. DETUNED - RECALIBRATION REQUIRED
```

启动序列里插两句（分别在深扫之前、之后）：

```
[INFO] - SUPPRESSION FIELD ESTABLISHED
[WARN] - SUPPRESSION FIELD DETUNED
```

**一条纪律（写给以后的我）：** 上面这些是**文案候选**，不是已经进游戏的字。
`docs/ORIGINAL_UI_TEXT.md` 收的是**原版逐字**捕获的东西，**不要往那里放**。

---

## 6. 手册条目（英文，可直接进 `docs/airemake/INGAME_MANUAL.md` 的候选行）

1. The S.R.S.U. does not block radiation; it cancels it. Six units ring the
   bottom of the chamber, and all three phases have to be brought into phase
   before the field holds.
2. A detuned unit is not offline. It still draws power and still counts as
   installed, so read the field gauge rather than the unit lamp.
3. Suppression is not free. The field shares its phase reference with the
   P.E.A extraction loop, so a stronger field means less net output to extract.
4. An E.F.E. will throw the units out of phase. Nothing is damaged when this
   happens; the units simply have to be recalibrated.
5. Vacate the chamber floor under the suppression ring while the units are
   discharging.

> 第 2 条是故意写成这样的：**它把本项目自己的那条教训（读对的那个东西）变成了世界内的一句话**
> （§0.2 / §0.18 家族：错的量法不报错，它只安静地给你一个数）。

---

## 7. 数值 —— **提案，不是实测**（现有公式在 `src/ReactorBackend/Engine.luau:328`）

**现在的真相（实测，改不动）：**

```
radiation = RadiationPerState(120) × (coreState + 1) × max(0, 1 − mass × 0.2)
```

`mass` 是**已启用的 M.A.S.S 档位之和**（每台 1 或 2 档），不是台数。
S.A.M.O.S. 在 `radiation > 600` 时不可用（`SAMRadiationLimit = 600`）。

**600 这个数不是随便定的 —— 它正好是 State 4 的裸辐射值。**
也就是说：**不洗，S.A.M.O.S. 从 State 5 起就自己不干了。** 这是现成的、真实的注脚。

| coreState | mass=0 | mass=2 | mass=4 |
|---|---|---|---|
| 0 | 120 | 72 | 24 |
| 1 | 240 | 144 | 48 |
| 2 | 360 | 216 | 72 |
| 3 | 480 | 288 | 96 |
| 4 | **600** | 360 | 120 |
| 5 | **720** ✗ | 432 | 144 |

（✗ = 越过 S.A.M.O.S. 的 600 线。）

**如果接入，提案长这样**（齐次乘一项；`srsu` = **同相的相数** 0..3 ——
实物是六台 = **三相 × 两台**，所以计数单位是「相」，不是「台」）：

```
radiation = … × max(0, 1 − mass × 0.2) × (1 − srsu × 0.10)
netOutput = … × (1 − srsu × 0.025)
```

- `SuppressionPerPhase = 0.10` —— **选的**（三相全同相 = ×0.7）。
- `OutputCostPerUnit = 0.025` —— **对的是实测值**：与 `MASSOutputCostPerLevel` 同量级，
  所以「更强的抑制 = 更少的净输出」这条取舍在数值上也和 M.A.S.S 同族。

**如果接入，它也不该让 S.A.M.O.S. 变成永远可用** —— 那会把一条现成的
难度线抹平。这是**接入时**的硬约束，不是现在的决定。

---

## 8. 边界（不能碰的）

- **不改任何现有机制**（§1.4 #1）。上面 §7 全部标着「提案」。
- **不新增控制原语**：设定上 S.R.S.U. **没有独立控制面**，它随启动序列自动通电、
  自己保持相位。所以它不占 `ControlTrigger` 的位、不进控制台、不需要新 `ClickPart`。
- **名称不进 §6 的脚本绑定名单**：`ClickPart` / `LeverUnion` / `NeonPart` /
  `*ControlRoomMonitor` / `Text` / `Core` / `EFEParticlePart` / `Effects`
  **一个都不许被这个名字族占用**，也不许拿它们给 S.R.S.U. 的部件命名。
- **实物已经在 place 里了**（2026-10-11，用户自己搭的，见 §4.5）——
  但**代码侧依然是零**：`ReactorBackend` 一行都没有，`Stats` 里没有它的字段，
  全 place 脚本里 `Suppress` **0 命中**（`script_grep` 量的，不是猜的）。
  这一版进 `docs/` 是因为 §0.0 要求「改完同一步把文档补齐」。
- **不要为了「布置得更整齐」去搬它**：东西在 `Workspace` 里就是**在渲染**，
  搬走 = 改变世界（§0.12 第 3 条）。要挪，先问。

---

## 9. S1 的答案（2026-10-11 当天就给了）

`QUESTIONS.md` **S1** 问的是三个层次，**用户当天用一句话选了 B** ——
「建模我做了 BottomSuppressionStructure」。所以：

- ~~**A —— 只停在纸上**~~ —— **过期**，他直接把实物做出来了。
- **B —— 已经落地。** 六台 + 一台母板在重建台里，实测见 §4.5。
  **做法和 S1 里写的不一样**：我写的是「Blender 建 `srsu_unit` 再导入」，
  他是**在 Studio 里直接搭的**。**结果一样（有实体、不接逻辑），过程不必回头补。**
- **C（接逻辑）—— 仍然是空的。** §7 那两行还是提案；要动它，
  按 §1.4 第 1 条得他明确点头。
