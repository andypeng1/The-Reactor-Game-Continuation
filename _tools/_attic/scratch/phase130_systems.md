
### 2.25 `ReadoutPanel` —— 四台屏的实时读数（`SSS.ReactorBackend`，2026-10-14，Phase 130）

**它补的是什么。** `Workspace.Monitors` 下七台屏里，`MainControlRoomMonitor`、
`PowerControlRoomMonitor`、`ThermalControlRoomMonitor`、`QuotaControlRoomMonitor`
这**四台**出厂就带着作者的**静态占位**（`'NIL F'` / `'140 F'` / `'100%'` / `'0 GW/H'` /
`'11:50 PM'` / `'524 GW'` / `'OFFLINE'`），**从来没有东西写过它们**：
原版驱动它们的那批 `GraphDetailThingy` 在这个 place 里是**空 Script**，
所以原版实现是**真的不可恢复**的。
每个读数的**格式**因此取自**原版自己的录像** ——
`Data/originalwatch/*/changes.log` 逐字记着每个 label 观察到的值 ——
而证据没钉死的那几个数声明在 `Config.Readouts` 里，不是就地糊一个。

**一个属性一个写入者。** `RoomShell` 管**一台屏显示哪张脸**（写 `frame.Visible`）；
这个模块只写**它不拥有的那些 frame 里的内容** —— label 的 `Text`、
三族条的 `Size`、`EquinoxFrame` 的两个颜色 —— 与 `BootPanel`（boot 行）、
`AlertsPanel`（格子内层彩条）、`ForecastPanel`（公告 + `EFEFrame`）、`StateBridge`
**属性全部不相交**。切法与前三个适配器同源。

**接了什么：36 个读数**（`Initialize` 打印 `captured 36 readings on
Main/Power/Thermal/Quota`，没有 `incomplete capture` warn）：

| 屏 | 读数 |
|---|---|
| **Main** | `ReadingsFrame` 八行：温度 / 应力 / 波动 / 腔压 / **净**输出 / 提取率 / 辐射 / HDEF 完好度 |
| **Power** | 三条 CBL × {机身温度、应力、功率、**状态词**、压力图条} |
| **Thermal** | C1..C3 储液条、六个 `FanFrame%d.StatusLabel` 的 `ON`/`OFF` |
| **Quota** | 挂钟、配额目标、配额进度条、`EquinoxFrame` 的两个颜色 |

**净输出那条不是随手挑的**：`state.output` 是**合成后**的净输出
（`Engine:325`，过提取率、gravitron 质量代价与 equinox 乘子），
`netOutput`（`Engine:322`）是**降额前**的兄弟量，故意不显示 ——
label 自己的词就是 **NET**，而录像的静止态 `'0 GW/H'` 排除了降额前的形式
（光它的偏移量就把读数垫在 50 以上）。

**格式从录像里读，不发明。** `Config.Readouts` 集中声明：

| 键 | 值 | 依据 |
|---|---|---|
| `Clock` | `StartMinute=710, MinutesPerSecond=1` | 五份录像起步恒 710、速率 0.977~0.990 min/s |
| `Format` | `Temperature='%.0f F'` / `Percent='%.0f %%'` / `Pressure='%.0f PSI'` / `Output='%.0f GW/H'` / `Radiation='%.0f R'` | 录像里每个 label 的字面形状 |
| `Target` | `SIThreshold=1000 / SIDivisor=1000 / SIDecimals=3` | 录像里目标值跨进了 `TW` |
| `LevelPercent=25` | 提取率每档 25% | 引擎的 `extraction` 是**档位**（1..4），label 是百分比 |
| `PumpLevelMax=3` | C-pump 的档位上限（`Engine:110` 只认 1..3） |
| `CblPrimingStep=11` / `CblFiringStep=14` | 状态词的两个相位边界 | `Config.Shift.StartupSteps[11]` 是 `PRIMING ALL COMBUSTION LASERS`、`[14]` 是 `COMBUSTION LASERS FIRING` |

**三族条骑的不是同一半** —— 这是这一轮真正难的地方（取舍 549/550）：

| 条 | 录像里的驱动 | `Config.Readouts.Bars` |
|---|---|---|
| C1..C3 储液条 | `{1, 0}, {f, 0}` —— **Y.Scale** | `Component='YScale'`、`DisplayFull=1` |
| CBL 压力图 | `{2, 0}, {0, N}` —— **Y.Offset**，整数 0..100 | `Component='YOffset'`、`DisplayFull=100` |
| 配额进度条 | `{f, 0}, {1, 0}` —— **X.Scale** | `Component='XScale'`、`DisplayFull=1` |

`barSize` 把**驱动轴的两半都写**（另一半归 0）、**另一根轴整根保留** ——
录像里 CBL 图作者摆的是 `{2, 0}, {0.75, 0}`（满高）而每个驱动值都是 `{2, 0}, {0, N}`，
即 `Y.Scale` 被按回了 0。**`Offset` 在 Roblox 里是整数、赋值即截断**，
所以储液条那种需要亚像素分辨率的量（实测 `0.441554189`）**只能骑 `Scale`** ——
这就是分量按条声明、不从「轴」推的原因。

**两个时钟，两个都对**（取舍 551）：

- `Config.Readouts.Clock` —— 设施挂钟。实测一发 Play 跑 47 s 从 `3:14 AM` 到 `4:00 AM`。
- `Config.Forecast.Clock` —— 深扫的**判决轴**（`23:00` 起、`1/3 min/s`），
  它每次深扫都**结构性钉在录像的 3:00 AM** 上（`720 × 1/3` 分），因为它和
  `untilEquinox` 是同一个恒等式的两边。**改成前者会打断那个标定**，所以两个都留。

**故意不接的，`Initialize` 当场打印**（§0.13：清单不写就等于不存在）：

- **七族染色** —— `CBLImageLabel` / `CPumpImageLabel` / `FanImageLabel` /
  `CoreImageLabel.ImageColor3` / `CoronaImageLabel.ImageColor3` /
  `PowerLabel.TextColor3` / `FluctuationLabel.TextColor`。录像把**颜色**记全了，
  **没记「按什么选」**；接它 = 发明规则。
- **两条原版驱动而这里不驱动的条**：`FanFrame` 的 **NET C-PUMP FLOW RATE**
  （录像 0..75，本引擎唯一流量量是 `Σ pump.level ∈ 0..9`，**没有比值**）、
  `CoreDiagramFrame.GraphFrame1` 的 **REACTOR ENERGY INTENSITY**
  （录像三处 75/150/250，**不知道哪个状态出的**）。把 9 缩到 75 就是
  **一个挑的数穿着一个量出来的数的衣服**（§0.18）。
- **`CoreDiagramFrame.GraphFrame2`（P. E. A. EXTRACTION）录像里只有 `Visible`**，
  一条 `Size` 都没有 —— 没有可复刻的条。
- **一条反向的例外**：`ReadingsFrame.StressLabel` **接了，虽然原版从没驱动过它**
  （全库一条 `StressLabel.Text` 写入都没有）。它是真引擎字段（`state.peaStress`），
  而另一种做法是让一个标签读着作者的 `'0 %'` 过一辈子。

**刷新按渲染值做签名闸**：签名是**拼起来的那些字符串本身**（不是对漂移的摘要），
所以两个不同的状态**不可能撞在同一个签名上**，而安静的一拍**一个属性都不写**。
写入前逐件查 `Parent` —— 一个能熬过班次重启的适配器也能熬过**屏被拆掉**，
而写一个已销毁的实例会抛错。

**形状与位置。** `Initialize(config)` + `Refresh(state,config)`，没有 `Step`
（它上面没有亚秒级的东西）。`Runtime.server.luau:18` require、
`:64` initialize、`publish()` 里 `:84` 在 `ForecastPanel` 之后、
`LogPanel` 之前刷新 —— 放在 `StateBridge.Publish` 之前，所以**一次控制造成的
读数和它读的那个杠杆不会差一拍**。

**验收**（Phase 130，真机 Play）：四个控制**真点击**（`MONITOR POWER → SHUTTERS →
BOOT → MASTER START-UP`，四条 `ControlBinder` 接受行、无 `rejected:`）走进
`phase=Running`；CBL 状态词四级全走一遍（`OFFLINE → POWERING → FIRING → ACTIVE`）；
一次真点击 `C-PUMP 1 ON BUTTON` 之后 C1 储液条读回 `{1, 0}, {0.333333343, 0}`
（**小数骑在 `Scale` 上，旧的整数写法写不出这个数**）。读数全部**从实例读**。
细节见 `PROGRESS.md` Phase 130 第六节、配方 `docs/SNIPPETS.md` §5.37。
**没验的是**：屏幕上**排布/溢出**的视觉效果（这一轮没有可用的机位对着这四台屏，
它们的 `Screen` 件还是 `CanQuery=false`）—— 验的是**值和机制**，不是**版面**。
