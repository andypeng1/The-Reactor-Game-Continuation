
---

## Phase 130 — 「airemake似乎没有把屏幕上的数据应用上去」：四台屏的实时读数（2026-10-14）

**这一轮就是 `QUESTIONS.md` R5 的选项 A 落地**（R5 已按「不回就照推荐办」结掉）。
起因是操作员原话：「**airemake似乎没有把屏幕上的数据（比如温度什么的）应用上去捏**」。
新模块 `SSS.ReactorBackend.ReadoutPanel`（23956 B，`Runtime.server.luau` 里 require +
在 `publish()` 里按序 `Refresh`），**游戏本体的玩法机制一行没动** ——
它只写 `Text` / `Size` / `EquinoxFrame` 的两个颜色，和上面每个适配器**属性不相交**。

### 一、接了什么：36 个读数

`Initialize` 自己报数：`[ReadoutPanel] captured 36 readings on
Main/Power/Thermal/Quota`，**没有** `incomplete capture` warn。

| 屏 | 读数 |
|---|---|
| **Main** | 八行读数（温度 / 应力 / 波动 / 腔压 / 净输出 / 提取率 / 辐射 / HDEF 完好度） |
| **Power** | 三条 CBL：机身温度、应力、功率、**状态词**、压力图条 |
| **Thermal** | C1..C3 储液条、六个风扇 `ON`/`OFF` |
| **Quota** | 时钟、目标 `512 GW`、配额进度条、Equinox 条的两个颜色 |

一条**原版没驱动而这里驱动了**的例外写在模块头里：`ReadingsFrame.StressLabel` ——
全库**一条** `StressLabel.Text` 写入都没有，但它是真引擎字段（`s.peaStress`），
留着它读作者的 `0 %` 一整场是更差的选择。

### 二、**格式规范不是发明的，是从原版自己的录像里读出来的**

`Data/originalwatch/*/changes.log` 每一行都是 `旧值 | 新值`，所以**每一条读数的形状**
（`%.0f F` 还是别的、条形图骑 `Scale` 还是 `Offset`）**是从证据里抄的**，不是猜的。
证据不固定的那几个数，集中声明在 `Config.Readouts` 里，而不是就地糊一个：

- `Clock = {StartMinute=710, MinutesPerSecond=1}` —— 五份录像量出来的**速率 0.977~0.990 min/s、
  起点恒 710**。
- `Target.SIThreshold=1000 / SIDivisor=1000 / SIDecimals=3`、`LevelPercent=25`（提取率每档 25%）、
  `CblPrimingStep=11` / `CblFiringStep=14`。

### 三、真正难的那一条：**`UDim2.Offset` 是整数**

第一版把三条储液条写成了**没动过的样子**：读数停在作者摆的
`{1, 0}, {0.00999999978, 0}`。查的顺序是：

1. `grep` 证明**没有别的模块写** `BarFrame` —— 排除抢写。
2. 活写一次 `UDim2.new(1,0,0,0.5)`，**当场读回 `{1,0},{0,0}`**；0.25、0.75 同样归零。
   → **`Offset` 是整数，赋值时截断**。
3. 回头逐字读录像：三条**储液条**骑的是 `{1,0},{f,0}`（**Y.Scale**），
   CBL 压力图骑的是 `{2,0},{0,N}`（**Y.Offset**，整数 0..100），
   配额进度条骑的是 `{f,0},{1,0}`（**X.Scale**）。**三族骑的不是同一半。**

**修法**：`BarSpec` 从「轴」改成「**分量**」——`Component = 'XScale' | 'YScale' | 'YOffset'`
逐条在 `Config.Readouts.Bars` 里声明，`barSize` 把**驱动轴的两半都写**
（另一半归 0），**另一根轴整根保留**。后一条不是洁癖：录像里 CBL 图**作者摆的**是
`{2,0},{0.75,0}`（满高），**每一个驱动值**却都是 `{2,0},{0,N}` ——
即 `Y.Scale` 被按回 0。带着一个没人在维护的 `Scale` 会把条按一个没人算的数缩放。

**这个坑是安静的**：**被截断的 0 和没写过的 0 是同一个数**（§0.18 同一族）。

### 四、屏幕上有两个时钟，而且**两个都对**

- `Config.Readouts.Clock` —— 设施挂钟，**从 710 分（正午起算）按 1 min/s 走**。
  实测：一发 Play 跑 47 s，`3:14 AM → 4:00 AM`，**正好 1 分钟每秒**。
- `Config.Forecast.Clock` —— **深扫的判决轴**，配置成 `23:00` 起、`1/3 min/s`。
  它在每一次深扫上**结构性地钉住**：因为 `time + untilEquinox = EquinoxSeconds` 恒等，
  `720 × 1/3` 分正好是录像里的 **3:00 AM**。

把后者改成前者会**打断那个标定**，所以两个都留着，理由写在 Config 的注释里。

### 五、**故意不接**的，Initialize 当场打印出来（§0.13：清单不写就等于不存在）

- **七族染色**：`CBLImageLabel` / `CPumpImageLabel` / `FanImageLabel` / `CoreImageLabel` /
  `CoronaImageLabel` / `PowerLabel.TextColor3` / `FluctuationLabel.TextColor` ——
  录像把每个**颜色**都记全了，**没记「按什么选」**。接它 = 发明规则。
- **两条原版驱动而这里不驱动的条**（Initialize 单独打一行）：
  `FanFrame` 的 **NET C-PUMP FLOW RATE**（录像 0..75，本引擎唯一流量量是
  `cooling = Σ pump.level` ∈ 0..9，**没有比值**）、
  `CoreDiagramFrame.GraphFrame1` 的 **REACTOR ENERGY INTENSITY**（录像三处 75/150/250，
  **不知道哪个状态出的**）。把 9 缩放到 75 就是**一个挑的数穿着一个量出来的数的衣服**（§0.18）。
- **`CoreDiagramFrame.GraphFrame2`（P. E. A. EXTRACTION）录像里只有 `Visible`，一条 `Size` 都没有** ——
  没有可复刻的条。

> 这最后三条是**这一轮新加进模块头的**。原来的头里写着
> 「`CoreDiagramFrame` 只是名字、没有数据可驱动」——**那是错的**，
> 而一句自信的假话比没有这句更坏。

### 六、真机验证（§4.4：模拟点击 → 读实例属性）

Studio `1e41e681-c295-44e4-86ad-32231a7a7644`，**推源码顺序 stop → push → start**（§0.17）。
两个文件 `GetAsync` 推入后**当场回读比对**：`Config.luau exact=true`、
`ReadoutPanel.luau exact=true`（**比字节，不是比长度**，§0.0）。

**点击装置**走 §0.26 的老配方：服务端泊车（**客户端的泊车不落到服务端**，
`DECISIONS_2` 那条第 6 坑）+ 客户端整数像素扫描 + 官方 `user_mouse_input`。
四个控制**共用同一个像素 `(287, 71)`**（视口 575×259，inset 58），
**每一击都有 `-> <LABEL>` 且后面没有 `rejected:`** —— 那是送达判据（`ControlBinder` 的 oracle）。

**① 储液条靠一次真点击证明它是活的：**

```
[ReactorBackend][Control] andypeng1NB -> C-PUMP 1 ON BUTTON
C1={1, 0}, {0.333333343, 0}   ← 1/3 骑在 Scale 上
C2={1, 0}, {0, 0}   C3={1, 0}, {0, 0}
```

`0.333333343` 是**小数**，而旧写法只能给出整数 `Offset` —— **这一下同时否掉了「没写」和「写错那一半」两件事**。

**② 开机链整条走通，CBL 状态词四级全见过**（`MONITOR POWER → SHUTTERS → BOOT → MASTER START-UP`，
四击全部送达）：

```
t=  0.0  OFFLINE OFFLINE OFFLINE  ph=Ready     t=3:14 AM
t=  3.9  OFFLINE OFFLINE OFFLINE  ph=Starting
t= 72.7  POWERING POWERING POWERING
t= 85.8  FIRING   FIRING   FIRING
t=117.8  ACTIVE   ACTIVE   ACTIVE  ph=Running  t=5:11 AM
```

（采样器 0.2 s 写进一个 `StringValue`，读数**从实例读**，§0.19。）
**`OFFLINE` 不是「作者摆的字符串恰好对上」** —— `POWERING` / `FIRING` / `ACTIVE`
是**只有这个模块会发的词**，走上去才算证明（`OFFLINE` 一个值不算）。
72.7→85.8 是 13.1 s，正坐在第 11 步那 **14.2 s** 的 hold 上。

**`Running` 下四台屏的整幅读数**（节选）：温度 `13654 F`、应力 `16 %`、
波动 `111 F`、腔压 `2839 PSI`、净输出 `92 GW/H`、提取率 `50 %`、辐射 `240 R`、
HDEF `99 %`；CBL 三条 `ACTIVE`、机身 `12916 F`、图条 `{2,0},{0,100}`；
六台风扇 `ON`；配额条 `{0.111979164, 0}`；Equinox 条 `0,0,0` / `1,0,0`（**闲置色**，正确）。

### 七、两个**看起来像缺陷、其实是对的**的东西（都量过才敢下结论）

- **七台屏全在闪红色 `FATAL SYSTEM ERROR`** —— 全部七个 `ErrorFrame.Visible` 都是 `true`。
  但那是**这一趟班次跑到 `Failed` 之后**拍的：`RoomShell.faceFor` 里
  `phase == 'Failed'` → `{mon.errorFrame}`，**是设计如此**。
  录像里 261 行 `ErrorFrame` **全是 `DescLabel.Text` / `InfoLabel.Text` 的文本替换，
  一条 `Visible` 都没有** —— 面由我们这边选，而选对了。
- **推论**：四台屏的读数住在 `MainMonitorFrame` 上，而它**只在 `Starting` / `Running` 显示**；
  `Cold` / `Ready` 显示闲置 splash，`Stopping` / `Report` 显示 `ShutdownFrame`。
  **这也是原版自己的设计**（录像里 `MainMonitorFrame` 的写入都聚在跑起来的窗口里）。

### 八、还欠的（照实写）

- R5 里点名的 `MalfunctionFrame` / `SAMFrame` 两个**告警浮层**仍未接（它们的 `Visible` 由
  `RoomShell` 之外没人管的那套谓词决定，和染色是同一类缺证据）。
- 五族染色、两条无映射的条、§3.16 里那几行 —— 见模块头的清单。
- §3.14 ②④⑤、§3.15 ③④⑤、§3.17 未动。`QUESTIONS.md` 本轮**未新增条目**（`R6` 仍挂着）。

**收尾**：`start_stop_play(false)`，Studio 停在 Edit。Play 期的探针（`workspace.__probeTrace`、
像素扫描函数、相机保持器）全是运行时注入，**停 Play 即消失**（§0.4）。
