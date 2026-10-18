# 原版的 UI / 手册文本（逐字）—— 复刻的**文案规格**

> **来源：** `r60` 记录器在一次完整班次上录下的 `TEXT` 通道，落在
> `Data/flow/original_261011-074137`（1418 条 `TEXT` 事件 / 929 个路径）。
> 这一轮是 Phase 113：原版（placeId `17596243941`）经 difz `:28429` 从启动杆走到堆芯熔毁。
>
> **这里的每一句都是原版自己写出来的**，不是我翻译或润色的。**原版的拼写错误一并保留**
> （`recallibrations` / `sucessfully` / `Be weary` / `byfar` / `infastructure` /
> `inferference` / `BOUNDRY` / `RECIEVED`）—— 它们是**原版的一部分**，抹掉它们
> 就不是逐字捕获了。要改就单独标一笔「复刻时修正拼写」。

---

## 0. 先读这个：**事件数不是变化数**

这一份里最容易踩的坑，**这一轮真踩了**：

- **`x.ScreenGui.HintText` 有 100 条 `TEXT` 事件，但只有 4 条消息。**
  那段文字是**打字机逐字**写出来的（`The` → `The obj` → `The object` → …），
  所以记录器的「100 次变化」是 **100 次重绘**，不是 100 个目标。
- 同理，记录器自己会给**整块被改写**的路径打 **`NOISY`**（`… changed 8 times in 8 polls`）：
  `SettingsFrame.ControlsTab.ControlFrame` 那 6 行控件说明**每轮都被整表重画**，
  所以「8 条事件」是 **8 行 × N 轮**，不是 8 次改动。

**规矩：拿到一条路径的「变化次数」之前，先问它是不是被整块重写。** 同族 §0.20
（按边数给面分类，回答的是文件格式）/ §0.21（分母里坐着被测对象）——
**错的量法不报错，它只安静地给你一个数。**

---

## 0.2 **存档里那段文案不是玩家看到的那段** —— 原版会把它改写一遍

（2026-10-18，Phase 143，量自 `Data/originalwatch/*/changes.log`，不是这一份的 `r60` 通道。）

这一份文档的标题写着「逐字」——**逐字是对的，但「哪一份字」有两个答案**。
作者存进 place 里的文案，和服务器开局后**改写出来**的文案，**可以不一样**；
我们手里这份 place（`83752844701736`）存的是**改写之前**的那一版。

量到的两处（`changes.log` 每行是 `路径 | 旧 | 新`，**右边那个才是玩家看到的**）：

| 时刻 | 路径 | 旧（= 我们 place 里现在这份） | 新（= 玩家看到的） |
|---|---|---|---|
| t=129.98（点火那一拍）| `…MonitorUI.ErrorFrame.Frame.DescLabel.Text` ×4 台 | `FATAL SYSTEM ERROR` | `MAINFRAME CONNECTION LOST` |
| 同上 | `…ErrorFrame.Frame.InfoLabel.Text` ×3 台 | `…CHIEF INSTALLATION TECHNICIAN PERSONNEL. [ABSOLUTE SERVICE DENIAL - 02]` | `…SYSTEMS MAINTENANCE PERSONNEL. [ABSOLUTE SERVICE DENIAL - 03]` |
| t=151.33（261002 是 t=120.16）| `Thermal…MalfunctionFrame.TextLabel.Text` | `SYSTEM ERROR` | `PLEASE WAIT` |
| 同上 | `…TextLabel.TextLabel.Text` | `CANNOT IDENTIFY ROOT CAUSE` | `AUTO RECALIBRATION IN PROGRESS` |
| 同上 | 两条 `TextColor3` | `1, 0, 0`（红）| `1, 0.698039, 0.180392`（琥珀）|

**它在五份里的两份出现，而且两次都紧贴点火**（判据用 `control-room 那七台的 ErrorFrame 行` 数，
`grep 'ControlRoomMonitor' | grep -c 'ErrorFrame'`）：

| 录像 | 点火（`Core.CORE.Transparency 1→0`）| 控制室 `ErrorFrame` 改写 | 时间窗 |
|---|---|---|---|
| `261001-125207` | 129.98 | **63 行** | 129.98 … 140.68（~10.7 s）|
| `261011-074207` | 2288.86 | **14 行** | 2290.82 … 2291.26（0.44 s，点火后 1.96 s）|
| `260930-200834` | 92.50 | **0 行** | — |
| `261002-140021` | 97.72 | **0 行** | — |
| `261011-041406` | 没点过火 | **0 行** | — |

所以 **「每局都写」和「只发生过一次」两句话都不成立**：两次都在点火窗口内、方向固定，
但**触发条件未决**（两次有、两次没有，按现有的读数分不出是什么把它们分开的）。

> **【2026-10-18 当日更正】** 这一段原来写的是「这是一次性改写，五份录像里只有 `261001-125207`
> 有这些行，另外四份一行都没有」。**数字是错的，结论因此也错**。
> 错因：我数的是 `ErrorFrame` 在**同类第二组监视器**（`MonitorsFacility.*`）上的行，把它们当成了
> 唯一来源，而 `261011-074207` 里**控制室那七台也有 14 行**（同目录另有 74 行属于 `MonitorsFacility`）。
> 教训同 §621：**「只有一处」和「一处都没有」一样，先问数的是什么**（取舍 621）。

**这块浮层真的亮过 —— 而且亮的时候已经是改写后的那句。**
`261001-125207` 在 `t=129.98`（点火同刻）把 **29 块屏**的 `ErrorFrame.Visible` 一起 `false→true`
（控制室 7 块 + 设施 22 块），`t=140.68` 一起回 `false` —— **10.70 s**；
日志里**改写在前、`Visible` 在后**，所以第一帧看到的就是 `MAINFRAME CONNECTION LOST`。
同 tick 里 `CautionFrame.ImageLabel.Position` 走 6 步（`Y.Scale` `1 → 5`，7 块控制室屏同步）。
**这是"存档 ≠ 屏幕"最硬的一层证据**：那 10.7 秒里，玩家屏幕上确实没有 `FATAL SYSTEM ERROR`。
但**控制室那七块五局里只亮过一局**，设施那 22 块在 `261011-074207` 里走的是另一套
（逐块崩溃-修复，每块 107.9–112.0 s）—— **触发条件不能互相挪用**（`PROGRESS.md` Phase 143 §六）。

**规矩（这条比上面那几条都容易复发）：**
- 从 place 里读出来的字符串，是**作者存下的兜底值**，不是**玩家看到的字**。
  要引用"屏幕上写着什么"，引的是日志行**右边那一半**。
- 反过来：`Visible=false` 的 frame **照样会被写**。属性变化不看可见性，
  所以「这块从没亮过」**推不出**「这块的文案没被改过」。
- 判据是**逐条比**，不是"看起来一样"：`-02` 和 `-03` 差两个字符，`CHIEF` 少一个词 ——
  两句话**都读得通**，读得通不是证据。

同族 §0.14b（能看图之后，量错的尺子会更早暴露）/ §0.32（装饰层安静地为空）：
**「存档里有什么」和「玩家看到什么」是两个读数，而它们在这里不相等。**

---

## 1. 启动日志（`log.panel`，23 行，按首次出现顺序）

原版监视器上的系统日志，`<b>[ALERT]</b>` / `<b>[WARN]</b>` 是它自己的富文本标签。
这一串就是**启动序列的完整叙事**，从 `SUBSPACE REACTOR START-UP SEQUENCE INITIATED`
一路到 `STATE 0 DETECTED, STALLOUT POSSIBLE`：

```
<b>[ALERT]</b> - SUBSPACE REACTOR START-UP SEQUENCE INITIATED
<b>[WARN]</b> - ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY
<b>[WARN]</b> - ACTIVATING POWER EXTRACTION ASSEMBLY
PRIMING ISOTOPE E COOLANT NETWORK
CALIBRATING REACTOR SENSOR NETWORK
E-VENT STRUCTURES PRIMED
<b>[WARN]</b> - SUBSPACE RIFT ACTIVE, RADIATION WARNING
PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM
<b>[WARN]</b> - INITIATING DEEP SCAN PROCEDURE
<b>[ALERT]</b> - PRIMING ALL COMBUSTION LASERS
DEEP SCAN PROCEDURE COMPLETED
M.E.T.U DIAGNOSTICS ACCEPTABLE
<b>[ALERT]</b> - ALL SYSTEMS READY, CORE IGNITION IMMINENT
<b>[WARN]</b> - ELECTROMAGNETIC ANOMALIES DETECTED
ANOMALY PROCEDURE OVERRIDEN BY PRIORITIZED DIRECTIVE
<b>[ALERT]</b> - COMBUSTION LASERS FIRING
<b>[ALERT]</b> - START-UP COMPLETED
<b>[WARN]</b> - COMPLETE MAINFRAME CRASH DETECTED
<b>[WARN]</b> - MAINFRAME OPERATIONAL CAPACITY MAY BE REDUCED IN FUTURE ACTIVATIONS
<b>[WARN]</b> - MULTIPLE ELECTROMAGNETIC ABNORMALITIES DETECTED
PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS
<b>[ALERT]</b> - INSUFFICIENT PRESSURE, CBL OUTPUT REDUCED
<b>[WARN]</b> - STATE 0 DETECTED, STALLOUT POSSIBLE
```

**叙事顺序值得记**：启动 → 撤离 → PEA → 同位素 E 冷却网 → 传感器校准 → E-VENT →
子空间裂隙 → 大气调节 → 深扫 → CBL 点火 → 深扫完成 → METU 诊断 → 就绪 → 电磁异常 →
异常流程被**更高优先级指令覆盖** → 激光发射 → 启动完成 → 同时**主框架崩溃**
（`COMPLETE MAINFRAME CRASH DETECTED`）→ 容量可能下降 → 多重电磁异常 → 压力不足。

**最后两行是失败路径**：`INSUFFICIENT PRESSURE, CBL OUTPUT REDUCED` →
`STATE 0 DETECTED, STALLOUT POSSIBLE`（同 §0 那条 `cblPct` 掉到 10 的读数）。

---

## 2. 提示文字（`x.ScreenGui.HintText`）—— 打字机，共 3 条

| # | 文本 | 状态 |
|---|---|---|
| 1 | `The objective of this game is to meet the company's energy quota while keeping the reactor stable. Equipment will begin to fail as you progress further throughout the night.` | 完整 |
| 2 | `Good luck. If you want more details, use the Digital Reactor Manual by the Electric Grid Console.` | 完整 |
| 3 | `Insufficient pressure will result in 'pressure-stall' which will rapi…` | **被截断** —— 记录在 `EVT3568` 结束，比 `SEAL`（`EVT3575`）早 7 行 |

第 3 条是**记录截断**，不是原版没写完：班次在它打完整之前就封了。

---

## 3. 悬停提示（`x.MouseFrame.PromptText`）—— 控件的名字

原版对每个可交互件给一句**全大写**的名字，而且有个**距离闸门**：

```
TOO FAR                       ← 够不着的时候
ROOM LIGHT BUTTON
MONITOR POWER BUTTON
MONITOR BOOT BUTTON
CONTROL ROOM SHUTTERS SWITCH
MASTER START-UP SWITCH        ← 启动杆
```

`TOO FAR` 出现在最前（`EVT2252`，那时角色还没走到控制台），其余在 `EVT3124..3153` 之间
随鼠标扫过逐个出现。**这 6 个字符串就是控制台那句「鼠标提示」的规格。**

---

## 4. 设置里的按键表（`SettingsFrame.ControlsTab`）—— 6 条绑定

原版**自己列出来的**操作表（`TitleLabel` = 动作，`TextLabel` = 键）：

| 键 | 动作 |
|---|---|
| `LEFT CTRL` | `GRAV-DOWN` |
| `MMB / F` | `M.E.S REPAIR GUN` |
| `G` | `DROP / DISEMBARK` |
| `V` | `MOUSE UNLOCK` |
| `C` | `SETTINGS` |
| `L` | `GUI TOGGLE` |

同一页的标签页名：`LOCAL SETTINGS`。

**注意**：这 6 行是**每轮整表重画**的（被记录器标 `NOISY`），所以「8 条事件」≠ 8 次改动 —— 见 §0。

---

## 5. CBL 的状态机（`x.CBL{1,2,3}Frame.StateLabel`）

**这是原版 CBL 自己的状态名，按顺序出现**：

```
OFFLINE → POWERING → FIRING → ACTIVE → LOW OUTPUT
```

实测时间轴（三台同步）：`OFFLINE`（`EVT1841/1852`）→ `POWERING`（`EVT3319..3321`）→
`FIRING`（`EVT3345..3347`）→ `ACTIVE`（`EVT3364..3366`）→ `LOW OUTPUT`（`EVT3508..3510`）。
**`LOW OUTPUT` 之后就是 §1 那两行失败日志。**

---

## 6. 数字反应堆手册（`ElectricGridConsole.DRMScreen`）—— 20 页，逐字

**这是原版装在游戏里的手册**，`<b>…</b>` 是它自己的富文本。帧名就是手册的目录结构。

### `BasicsFrame.StartupFrame`
```
FLIP MASTER SWITCH TO START-UP POSITION
```

### `MainframeFrame.OperationsFrame`
```
Majority of its computational operations are controlled by <b>QPUs</b>, which have a tendency to <b>degrade</b>, especially in unfavorable environmental conditions or overclocking scenarios.
```
```
Operators are required to <b>replace</b> the affected QPU <b>as soon as possible</b>, otherwise machines across the facility will begin to shut off in order to conserve resources.
```
```
<b>Gateway Transporters, Medical dispensers, and especially the control room consoles will be non-functional</b> if there are too few QPUs or the mainframe completely shuts down.
```
```
Large stockpiles of QPUs tend to be counterintuitive, so operators <b>may have to use a Synthesiser Unit</b> in order to sucessfully replace dying QPUs. Be weary that the mainframe is always kept at extremely low temperatures, and as such haste is of the essence. {wip system}
```
```
Additionally, components of the <b>mainframe may catch on fire</b> from reactor operation. It's advised that when operators are preparing to replace a QPU, they <b>equip a fire extinguisher.</b> Excessive <b>fires</b> may raise the mainframe temperature and <b>cause QPUs to degrade at a much faster rate.</b>
```

### `LaserConsFrame.OperationsFrame`
```
<b>Pressure purges</b> should be <b>enacted frequently</b> when necessary, as <b>excessive</b> CBL <b>Pressure</b> can lead to <b>excessive</b> CBL <b>Stress,</b> which can eventually <b>cause</b> a CBL to <b>Overload</b>, which will be fined accordingly.
```
```
This can also be used as another extreme method of cooling the core, however this requires a high degree of precision, especially in higher states, and is very frowned upon by maintenance teams.
```
```
<b>Integrity loss</b> will be <b>displayed in purple</b> for the affected CBL, and will require operators to <b>venture inside of the reactor chamber via M.E.S, and repair the hull breaches within a timely manner.</b>
```
```
Allowing the hull breaches to remain for a <b>prolonged period of time</b> will compromise the affected CBL's reaction sequence, and cause it to <b>gain a substantial increase in pressure</b> until repaired or an overload occurs.
```

### `ThermalConsFrame.OperationsFrame`
```
Additionally, the <b>C-Pumps</b> have been observed <b>degrading twice as fast</b> as their usual rate, which at times <b>ruptures or completely destroys</b> the reactor's <b>coolant</b> network.
```
```
Should the <b>pumps fail,</b> you are required to go in the <b>heavy maintenance sub-sector,</b> and make the appropriate <b>repairs / recallibrations.</b>
```

### `HDEFFrame.OperationsFrame`
```
There are two large emitters beside the control room, as well as an <b>emergency generator behind this console</b> that maintain the field's integrity.
```
```
Activating the <b>E-Power Supply</b> will allow the field to <b>regain integrity</b>, but do note that during reactor operation, it has a <b>tendency to overheat</b>, necessitating it be <b>shut off</b> after a certain amount of time.
```

### `GravFrame.OperationsFrame`
```
While <b>overcharges normally damage the gravatron</b>, <b>unsuccessful overloads</b> will result in <b>substantially more damage</b>, however this can be repaired with a repair gun.
```
```
Excessive damage may result in the Gravatron completely shutting down and disabling certain grav-shafts, requiring they be temporarily powered with GCCs (Gravitation Containment Cells).
```

### `AltConsFrame.OperationsFrame`
```
The <b>M.A.S.S Rails</b> are a massively upscaled variant of the scrubbers found in deionization chambers which help protect vital machinery and personnel from chamber emissions.
```

### `AlertsFrame.MajorFrame`
```
<b>Hazardous Chamber Radiation</b> and <b>High Chamber Pressure</b> will both <b>decrease</b> the <b>H.D.E.F's integrity</b>, however High Chamber Pressure will also cause an <b>increase</b> in <b>Temp Fluctuation.</b>
```
```
<b>High CBL Power</b> will cause the <b>CBL pressure</b> & subsequently the <b>stress</b> to rise dramatically, and <b>High CBL Stress</b> is a sign that a <b>pressure purge is needed</b> to avoid imminent overload.
```

### `CoreFrame.StatesFrame.EquinoxLabel`
```
This is byfar the most mysterious phenomena of the subspace core, however further research has been suspended due to the unacceptable amount of damage it causes to company infastructure.
```

> **手册里那两条机制值得单独记**（它们把散落的系统串起来了）：
> **① 废热泵（C-Pumps）在运行时以两倍速率劣化**，坏掉会**炸掉冷却网** → 去重型维护区修。
> **② HPU（QPU）劣化 → 太少 → 全设施的机器开始断电**（门送器 / 医疗分配器 / **控制室控制台**），
> 主框架还会**着火**，着火又加快 QPU 劣化。
> ③ **HDEF 完整性**被「危险辐射」和「高压」双双扣，而「高压」还**额外**抬高温度波动。
> ④ **M.A.S.S Rails** = 去离子舱净化器的放大版。

---

## 7. 监视器的三种故障页（Disconnect / Reboot / Glitch）

每一台监视器都有这三套文案（屏幕关掉或主框架故障时显示）。
**逐字如下**（注意 `inferference` / `RECIEVED` / `recieve` 都是原版的拼写）：

**`DisconnectFrame`**
```
OPERATOR ERROR
NO DATA IS ACTIVELY BEING RECIEVED
To resolve this issue, please make sure the proper mainframe data connection is working / active. If problems persist, please contact System Maintenance.
```

**`RebootFrame`**
```
SYSTEM REBOOT
DO NOT TURN OFF DEVICE
This was likely caused due to an update or system crash. Please wait, and do not turn off the device. If problems persist, please contact IT personnel.
```

**`GlitchFrame`**
```
INTERFERENCE
MAINFRAME CONNECTION OVERLOAD
An unknown error in the mainframe is causing this device to experience electronic inferference. This could be due to failing computational systems. Please …
```

`DisplayMonitor` / `VitaMonitor1..3` 各一套，文案相同 —— 所以这是**一套模板用在 N 台监视器上**。

---

## 8. 两个面板的文案

### 配额面板（`q.panel`）
```
PowerText = TARGET:
PowerLabel = 524 GW          ← 常量，整班没变过
TextLabel  = EQUINOX STATE
TextLabel  = Remember: Time is of the essence! Overtime starts …
TextLabel  = 12PM marks the beginning of an equinox event, which will result in major damage! Any company property damaged or destroyed in any form will be docked from your paycheck.
```
`q.timeText` 是**班次钟**：`11:50 PM` → `12:00 AM` → … → `1:15 AM`（一条一分钟地走）。
`q.scale` 是**配额进度条**：`0.01` → `0.14` 单调上升。

### 预报面板（`fc.panel`）
```
TitleText    = SUBSPACE FORECAST
SubTitleText = ENERGY INTENSITY TIMELINE
SubTitleText = HADEN THRESHOLD
TextLabel    = TEMPORAL BOUNDRY
TextLabel    = ENERGY FLUCTUATIONS EXCEED SENSOR RANGE
TextLabel    = PRIORITY ANNOUNCEMENT
AnnouncementText = PENDING SUBSPACE DEEPSCAN
                 → PROCESSING DEEPSCAN TELEMETRY
                 → ANOMALY DETECTED, MARGIN ~12:00 AM
TimeLabel    = 12:00 PM / 12:20 AM / 12:40 AM / 1:00 …   ← 时间轴刻度，**逐格画上去的**
```

**`MARGIN ~12:00 AM`** 与 §9 的 `CLOCK` 说明同一条线：
**过 12:00 PM 就是开机**（`QUESTIONS.md` 早先记的 B1）。

---

## 9. 启动时记录器自己的三条断言

```
EVT2280 SAM   SAM is off at inject
EVT2281 CLOCK the clock already reads past 12:00PM at inject; the core is up
EVT3401 COREGATE Stats.GameActive went true; the core is fully on and the reactor readings start from this poll
```

`CLOCK` 这一条是**「12PM 闸门」的实测证据**：记录器在注入时发现钟**已经过了 12:00 PM**，
而堆芯是起的。即**这一轮的注入时刻本来就在窗口内**。

---

## 10. 灯色调色板（`LAMPPAL`，6 色）

原版 `NeonPart` 用的 6 个颜色，记录器在 `EVT2260..2264` 一次性记下，`f` 直到 `EVT3162` 才用：

| 键 | RGB | 看起来是 |
|---|---|---|
| `a` | `137,255,147` | 绿（正常） |
| `b` | `17,17,17` | 近黑（灭） |
| `c` | `255,0,0` | 红（警报） |
| `d` | `240,240,240` | 白 |
| `e` | `255,255,0` | 黄（警告） |
| `f` | `0,0,0` | 黑 |

---

## 11. 控制变量清单（`UNATTR` 通道）—— 原版**自己动**的那些

这是本轮最有用的一块：`r60` 的 `UNATTR` 通道专门记**没有对应点击却变了的控制**。
在一轮我按了 11 下的班次里，它抓到了原版**自动**驱动的每一个控制：

```
c.cool1 0->1   c.cool2 0->1   c.cool3 0->1          ← 冷却泵自己开（EVT3250..3252）
c.fan1  0->1 … c.fan6 0->1                          ← 六台风扇自己开（EVT3266..3277）
c.cbl1Pct 100->50  c.cbl1Lvl 4->2  （×3）           ← CBL 从 4 档降到 2 档（EVT3367..3372）
c.cbl1Pct  50->10  c.cbl1Lvl 2->1  （×3）           ← 再降到 1 档（EVT3513..3518）
c.cbl1On    1->0   c.cbl1Lvl 1->0  （×3）           ← 全部关掉（EVT3569..3574），紧接 SEAL
```

**两个可复用的结论：**
1. **原版的 CBL 有一台自动斜坡**：`Lvl 4 → 2 → 1 → 0`、`Pct 100 → 50 → 10`，
   全程**没有任何点击**。这是**启动序列的一部分**，不是玩家操作，也不是 bug。
2. **控制变量名就是这些**：`cool1..3` / `fan1..6` / `cbl{1,2,3}On` / `cbl{1,2,3}Lvl` / `cbl{1,2,3}Pct`。
   复刻时对得上这套名字，记录器的 `UNATTR` 就能直接拿去比对。

> 对照记忆里 `cbl-overload-clock` 那条「CBL 在 2 档启动」：**这一次是先过 4 档再落到 2 档** ——
> 斜坡的**起点**是 4，**稳态**是 2。两条不矛盾，但合起来才是完整形状。

---

## 12. 终局文案（熔毁页）

`SEAL` 之后七台监视器停在这一套（详见取舍 473）：

```
BOOTING IN PROGRESS
SHUTDOWN PROTOCOL
REACTOR SHUTDOWN PROTOCOL
CORE COLLAPSE DETECTED - PLEASE WAIT WHILE THE REACTOR COMPLETES ITS AUTOMATED
SHUTDOWN INSTRUCTIONS. ANY INTERRUPTIONS IN THIS PROCESS MAY RESULT IN DAMAGE
OR INJURY.
REACTOR ENERGY QUOTA NOT MET
SMER - CONTROL ROOM MONITOR
```

---

## 13. 数字快闪（备查）

```
EVT1535 READOUTS found=932 distinct=906 monitors=yes consoles=*Label
EVT1    START   reactorFrame=false thermal=true cbl=true power=true stats=true logs=true gui=true hooks=80
```
`REACTORFRAME=false` 值得注意：**记录器在注入时**已经**找不到反应堆框架**这一路读数
（`stats` 那一路是后来才起来的，见 `COREGATE`）。这是**通道覆盖范围**的记录，不是游戏状态。
