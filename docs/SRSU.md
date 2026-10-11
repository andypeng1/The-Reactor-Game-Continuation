# S.R.S.U. — Subspace Radiation Suppression Unit（设定集）

> **状态：纯设定。** 这一份是**文案 / 世界内术语 / 美术规格**，不接 `ReactorBackend`、
> 不进 `Stats`、不新增任何控制原语 —— 现有玩法机制一个字没动（§1.4 第 1 条）。
> 要不要让它进模拟，见 §9 与 `QUESTIONS.md` **S1**。
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
| 装在哪 | 腔体 **collar**，三台一组，120° 均布，各朝堆芯 |
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
三台单元各自朝堆芯发一束**反相参考波**。三束在裂隙口叠加，把
泄漏场的**振幅**按相位差压下去 —— 不是吸收，是**对消**，
所以单元本身不发热、不积垢，读数掉下来的时候腔体是**冷**的。

**③ 为什么是三台。**
三相。任意一台失谐，合成的抵消场就**塌成两束**，覆盖出现一道缝，
辐射读数会在缝的方位上先涨。**这是设定里唯一可被玩家看见的失效形态** ——
三台灯里坏一台，读数是**慢慢**往上爬的，不是跳变。

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
**灯色必须复用本 place 实测过的键**（`src/ReactorBackend/Config.luau` 的 `Visual`），
一个都不要新调：

| 状态 | 颜色键（实测值） | 为什么是它 |
|---|---|---|
| 待机 / 未通电 | `Off` (45,45,45) | 场未建立 |
| 场建立（健康） | `Nominal` (137,255,147) | 本 place 自己的「一切正常」绿 |
| **失谐** | `Amber` (255,128,1) | 这个键的语义**本来**就是「在役但不可用」—— 失谐正好是它 |
| 对消放电的一瞬 | `Yellow` (240,220,60) | 与「可点火」共用一个键 |
| 过载 | `Fault` (255,70,40) | |
| 相位参考丢失 | `Purple` (150,60,220) / `Blue` (60,130,240) | 与 CBL 的状态码同族 |

**形态：** 扁柱体 + 面向堆芯的一面**发射环**（不是镜面，是环形放电口），
背面接两路：一路冷却、一路相位参考线缆（参考线缆**要能看出来是往 P.E.A 那边去的** ——
这是 §3⑤ 那条取舍的唯一视觉线索）。

**同族件：** `_tools/blender/` 那批（`radiation_scrubber` / `laser_port` / `chamber_grate`
/ `chamber_wall_24` / `ring_bridge_18_24` / `transition_pillar`），共用件是 `trg.py`。
设定上 S.R.S.U. 是 `radiation_scrubber` 的**祖辈** —— 手册 #96 说 M.A.S.S 是
「deionization 腔体里那些 scrubber 的放大版」，那就让 S.R.S.U. 长得像
**同一族的更老、更笨、更贵**的那一件。

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

1. The S.R.S.U. does not block radiation; it cancels it. Three units sit on the
   chamber collar and each has to be brought into phase with the other two
   before the field holds.
2. A detuned unit is not offline. It still draws power and still counts as
   installed, so read the field gauge rather than the unit lamp.
3. Suppression is not free. The field shares its phase reference with the
   P.E.A extraction loop, so a stronger field means less net output to extract.
4. An E.F.E. will throw the units out of phase. Nothing is damaged when this
   happens; the units simply have to be recalibrated.
5. Vacate the collar walkway while the units are discharging.

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

**如果接入，提案长这样**（齐次乘一项，`srsu` = 同相的单元数 0..3）：

```
radiation = … × max(0, 1 − mass × 0.2) × (1 − srsu × 0.10)
netOutput = … × (1 − srsu × 0.025)
```

- `SuppressionPerUnit = 0.10` —— **选的**（三台全同相 = ×0.7）。
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
- **这一版只在纸上**：盘上没有 S.R.S.U. 的部件，place 里也没有。
  写进 `docs/` 是因为 §0.0 要求「改完同一步把文档补齐」，不是因为东西已经存在。

---

## 9. 待拍板

一句话：**S.R.S.U. 停在纸面上，还是要变成设施里真的存在的东西？**
三个层次，代价递增 —— 明细与建议写在 `QUESTIONS.md` **S1**：

- **A（我默认走这条）** —— 只保留本文件。文案进手册候选池，美术进待建清单。
- **B** —— 做实体：Blender 建 `srsu_unit`（同 `_tools/blender/trg.py` 那套），
  导入重建台，**仍不接逻辑**（一件纯装饰/世界内物件）。
- **C** —— 接逻辑：§7 那两行进 `Engine.luau`，加 `Stats` 字段与监视器一行。
  **这一条会改到模拟的平衡**，按 §1.4 必须先拿到明确授权。
