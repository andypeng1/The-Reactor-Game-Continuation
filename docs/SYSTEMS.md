# CLAUDE §2 已完成的系统

> 磁盘专属前言 —— 不属于游戏内的 `CLAUDE` ModuleScript，校验脚本按「第一个 `## ` 之前
> 整段丢掉」剥掉，长度写死在 `_tools/verify_docs.py` 里。
>
> 本文是从 `CLAUDE.md` 拆出来的 **§2 已完成的系统**。权威副本仍然是游戏里的
> `game.ServerScriptService.GameCore.CLAUDE`，改完同一步镜像回模块。
> `CLAUDE.md` 只留每轮都要看的章节；拆的理由与分工见它开头的 §0.0。

## 2. 已完成的系统

### 2.1 架构总览
```
ServerScriptService/
  GameCore/                      ← 主程序集
    GameCore            [Script]       入口，注册 25 个系统
    Core/
      Config            [ModuleScript] 全部可调参数
      GameState         [ModuleScript] 唯一真相源（single source of truth）
      SystemManager     [ModuleScript] Entries/Systems/Get/Initialize/Register/Update
      Network           [ModuleScript] 运行时 RemoteEvent
    ReactorSystem/
      ReactorState      [ModuleScript] TRGWeb 温度/压力模型
      CBLSystem         [ModuleScript] 3 台激光
      CoolantSystem     [ModuleScript] 3 泵 + 3 储液罐 + 传感器
      PowerSystem       [ModuleScript] PowerOutput 唯一写入者
      PEASystem         [ModuleScript] 电力抽取
    FacilitySystem/
      ConsoleService    [ModuleScript] 全部点击动作
      ControlTrigger    [ModuleScript] 【唯一】点击实现 + CollectionService 标签 + 命令栏总线
      ConsoleBinder     [ModuleScript] 只留点号表，转发给 ControlTrigger.Bind
      ControlVisuals    [ModuleScript] 拉杆动画 + 灯色
      MonitorService    [ModuleScript] 7 台控制室监视器
      QPUSystem / GatewaySystem / GravLiftSystem
      BackupPowerSystem [ModuleScript] 导出 HDEFIntegrity
    PROGRESS / DECISIONS / README / CLAUDE  [ModuleScript] 文档

Workspace/
  GameCoreTests/
    GameCoreSelfTest    [Script]  自检（跑一次自动禁用）
    GameCoreControlTest [Script]  控件测试 13 项
  Consoles/             ← 6 张桌子，68 个控件
  Monitors/             ← Main / Thermal / Power / Quota / Alerts / Log / Forecast 监视器

StarterPlayer/StarterPlayerScripts/
  ReactorMonitorClient  [LocalScript] MESUI 布局绑定
```

**设计模式：**
- 事件驱动 + 固定 10Hz 时间步
- `SystemManager` 按 priority 分发，系统用 **点号调用** `system.Update(dt)`
- `Config` 持有全部可调参数；`GameState` 是唯一真相源，**系统不得缓存副本**
- 系统优先级范围 10–140
- **点击只有一套实现**：`ControlTrigger.Fire()`；物理点击与命令栏调用是同一条代码路径

### 2.2 系统清单（25 个）
ReactorState / CBLSystem / CoolantSystem / PowerSystem / PEASystem /
MonitorService / ControlVisuals / ConsoleBinder / ConsoleService /
QPUSystem / GatewaySystem / GravLiftSystem / BackupPowerSystem /
ShiftSystem / EventController / DataCollection / … （共 25）

### 2.3 已实现的机制（全部按 Wiki / TRGWeb 校准）

**时间基准**
```lua
Config.Sim.TRGWebTick = 2.5   -- 所有 TRGWeb 常量都是「每 2.5 秒一跳」
                              -- 换算方式: dt / TRGWebTick
Config.Reactor.TempUpdateInterval = 1.0  -- 温度改为 1 秒结算一次（用户要求）
```

**压力（PSI 量纲）**
| 参数 | 值 |
|---|---|
| MaxPressure | 16000 |
| 点火 | 5000 PSI / 9420 F |
| 失速 stallout | < 2250 PSI |
| 超压 overpressure | > 13500 PSI |
| AVB | −3300 PSI，26s CD，压力 > 5500 PSI 时无效 |
| E-VENT | −4000 F，每班次单次使用 |

**堆芯温度状态**（`Config.Reactor.CoreStateThresholds`）
```
6000 / 17500 / 29500 / 39000 F
State 3 自加热: +700 F / tick（>29500 F）
```

**发电档位**（TRGWeb 公式）
```
t < 某阈值 → 档位 1: t/250 + 50
          → 档位 2: t/160 + 100
          → 档位 3: t/120 + 250
          → 档位 4: t/45  + 400
```

**CBL（化学泵浦激光）**
- 3 台激光，档位 1..5
- 加热 = `power_level × 65` / tick（**MINIMUM 档也会点火**）
- **堆芯体温度锁定 925 K**（用户明确确认 "925k"）
- 激光被摧毁时显示 `ERR`
- 过载 = 暂时断电 + 自动重启；**只有 Shift 3+ 才永久损失 integrity**

**冷却（Isotope E）**
- 3 台泵，档位 0..3
- 移除热量 = `120` / 档位 / tick
- 3 个储液罐
- **传感器可靠性系统（Phase 18，我做的）**：
  - 每泵独立 `CoolantPumpStability` (0–100)
  - 漂移 `SensorDegradePerSecond 0.30` + 每级堆芯状态 `SensorStateBonus 0.22`，运行时 ×1.5
  - < 60 → 监视器显示琥珀色 `SENSOR n%`，读数不可信
  - < 25 → 输出被压低至 `SensorOutputPenalty 0.45`
  - 手动校准：点热控台 `CoolantControl{i}.BigLever` → 恢复到 100，30s 冷却

**班次配额**
```
Shift 1: 512 GW   Shift 2: 1024 GW   Shift 3: 3072 GW（峰值输出）
```

**Equinox 事件**
```
Shift 3，班次秒 600（= 12:00 PM），3× 能量持续 40 秒，冷却泵会爆炸
```

### 2.4 控制系统（68 个控件 / 6 张桌子）
```
[ConsoleBinder] desks=6 controls=68 reused=2 created=66 missing=0
[ConsoleBinder] rebuild desks=6 controls=66 missing=0
control bus ready: tagged=73 reindexed=73
```
- 用 **ClickDetector**（不是 ProximityPrompt，用户要求的）
- 每次按下都会打印 `[Console] <player> pressed: <label> (<console>)`
- `Workspace.Consoles` 下 6 张台，**authored ClickDetector = 0**，66 个由绑定器创建
- 点击逻辑全部在 `FacilitySystem.ControlTrigger`；`ConsoleBinder` 只剩点号表
- 每个控件带 `GameCoreControl` 标签 + 6 个属性（Action/Arg/Arg2/Label/Console/Panel）；
  `ControlTrigger.Reindex()` 从标签重建，手工在 Studio 打标签的部件下次开服就能用
- 命令栏用 `ServerStorage.GameCore.ControlBus:Invoke(...)` —— **不要 require**（见 §0.2）。
  `ControlBus` 返回字符串；`ControlQuery` 是同一套接口返回表，给脚本用
- **ClickDetector 不一定挂在 `ClickPart` 上**：拉杆的板块被 `Collar`/`Grip` 埋住，
  鼠标射线到不了它，所以挂到最近的「只拥有这一块板」的祖先 Model 上。
  面板那种拥有很多板的祖先**不能**挂，否则整块面板变成一个巨大 hitbox（见 `DECISIONS` 75）
- 装机前的原版读数是 `desks=7 controls=68 reused=61 created=7 missing=0`。
  `desks 7→6` 是因为重复的 `CBLaserConsole` 已停用；`reused 61→2` / `created 7→66`
  是因为 Mk2 台子不自带 ClickDetector。逐项对账见 `DECISIONS` 43，
  装机过程见 `PROGRESS` 的 `INSTALLED` 段。

**桌子清单：**
`MainReactorConsole` / `ThermalConsole` / `CBLaserConsole` /
`ElectricGridConsole` / `HDEFGenerator` / `ALTReactorConsole` / …

### 2.5 拉杆与灯（ControlVisuals）
```
18 个拉杆，41 盏灯
```
（原记 31 盏：Mk2 台子给更多控件配了独立指示灯，见 `DECISIONS` 43。）
- **拉杆只允许 `LeverUnion` 这一个部件移动**（用户强烈纠正过）
- 转轴 = 拉杆**底部**，不是 `LeverOrginPart`
- 档位：CBL 5 / PEA 4 / 冷却泵 4 / 风扇·E-VENT·启停 2
- 灯：稳态白/红/暗 + 按下时 0.6s 绿色 `Pulse` 闪烁

**拉杆的运动 —— Phase 59（2026-09-30）起是 tween。**
这是本节最容易读错的地方，所以把「谁在写」「怎么动」「多快」拆开写：

- **写入者是 `SSS.ReactorBackend.VisualFeedback`，不是 `ControlVisuals`** ——
  模块自己第 4 行就写着它是这些 CFrame 的单一写入者，`Engine` 从不碰部件。
  §5.2 那套 `ControlVisuals` 的**旋转**写法**已被取代**（旧的，别再照着改）。
- **运动契约是平移，不是旋转**：拉杆沿自己的 `baseline.LookVector` 滑到档位。
  `CFrame + Vector3` 只加位置、保留旋转，所以「把存下来的 `baseline` 接着用」是精确的
  （`part.CFrame.LookVector == baseline.LookVector` 恒成立）。
- **档位 → 位移** = `throwDistance(level, maxLevel, travel)`
  = `(clamp(level,1,maxLevel) - 1) / (maxLevel - 1) * travel`。
  **level 1 给出 throw 0，也就是作者原本摆的那个姿势** ——
  1 档不是一个需要动画的位移，而是原点。这解释了为什么 `poseToggle(key, on)`
  只能是 2 或 1（`TOGGLE_MAX_LEVEL`）。
- **`Config.Visual.LeverArcDegrees`（50）现在没有任何读者**。它是旧的旋转写法留下的键，
  当前写入者是纯平移的；grep 到它**不要**据此以为 throw 会转（`DECISIONS_2` 187）。
- **落位方式**：`TweenService:Create(part, leverTweenInfo, {CFrame = goal}):Play()`，
  时长取自 `Config.Visual.LeverTweenSeconds`（**0.3 s**，`Quad` / `Out`）。
  **它必须短于 `Config.Visual.RefreshSeconds`（1 s）**：refresh 是**签名门控**的
  （输入不变就早退，姿势只在有输入动过时才重写），所以下一次姿势到来时还在动的档位，
  就是**这根 union 永远不会停在上面的档位**。
- 两个必须有的安全性质：创建新 tween 前先 `Cancel()` 旧的（否则一个属性上两个活 tween
  逐帧竞争）；**同一个实例**被重新解析时沿用旧 `baseline` / `travel`
  （`smallThrow` 只在 union 坐在档位上时才读得对符号）。理由见 `DECISIONS_2` 188 / 189。
- **数量是本轮实测，和本节上面的旧数字对不上**：place 里 **41** 个 `LeverUnion`
  （`CLAUDE.md` §6 记的 32 是旧的），模块自己有 **21** 个 lever key。
  `18 个拉杆` / `31 盏灯` / `41 盏灯` 这几个数和「模块会写的 21 个 lever / 31 个 lamp key」
  是**不同的集合**，不要互相加减。(`DECISIONS` 43 记的那次装机变动仍然有效。)

**上面写的是「控制台上的东西」。控制台指向的东西**（房间灯带、七台监视器、
三扇百叶窗门）由**另一个模块**写 —— 见 §2.12。

### 2.6 监视器（MonitorService）
| 监视器 | 内容 |
|---|---|
| **Main** | 温度 / 压力 / 辐射 / 输出 / HDEF / PEA 应力 / 波动 / 抽取率 |
| **Thermal** | 风扇 ON/OFF，泵 `ON L<n>` / `OFF` / `FAULT`（红）+ 传感器 % |
| **Power** | CBL 功率 % / 应力 % / 状态 / `925 K` 或 `ERR`，Wiki 配色（过载红 / 完整性紫 / 反应蓝 / 高输出黄） |
| **Quota** | 游戏内时钟 6AM→6PM，配额目标 + 百分比，Equinox 边框 |
| **Alerts** | 27 盏灯，由实时状态驱动 |
| **Log** | 滚动 5 行、按严重度配色的事件日志（青 / 琥珀 / 红），监视 11 个信号，变化触发 |
| **Forecast** | 能量强度时间轴，每 5 秒一根柱，宽度 = PowerOutput / 当前班次配额，外加一行优先级公告 |

**监视器一共 7 台，不是 5 台。** Wiki 原文：「five consoles, three main monitors, and four
minor monitors」= 3 + 4 = 7，`Workspace.Monitors` 也确实是 7 台。本文档与 `README` 早期版本
写的 5 台是**记录错误，不是代码缺陷** —— 脚本一行都不用改，七台本来就在。
七台现在**全部有写入者**：Log 与 Forecast 是最后接上的两台，都写成**纯观察者**
（只读 `GameState`，从不写），single-writer 规则不变，仿真行为零改动（`DECISIONS` 54 / 60）。

**重建监视器的绑定契约（零脚本改动）：**

```
Workspace.Monitors.<Name>ControlRoomMonitor    Model
  .Screen                                      BasePart，Neon，Transparency 0
    .MonitorUI                                 SurfaceGui
      .MainMonitorFrame                        Frame
        <具名子节点>                            上表列出的标签
```

四条必须带过去：
① **`LightInfluence`：标签是 1，屏幕是 0**。新建 `SurfaceGui` 默认是 0，而 0 = 「永远全亮」，
无视场景光照**和**曝光补偿。控制台文字板必须是 **1**（Mk2 装台那次漏了 121 块，
就是「装好的台子发白」的根因，`DECISIONS` 45）；但**监视器是反的** ——
七台 `MonitorUI` 实测一律 0，且 0 才对：屏幕是自发光像素，不该被房间曝光调色。
`DECISIONS` 57 纠正了「全部用 1」这条旧概括，重建时**不要**把 1 带过去。
② `AlertsFrame.AlertFrame<N>` 是按**固定 27 个**索引的，Thermal 泵框上的
`GameCoreLevelLabel` 缺失时会被自动创建 —— 两者都不能在重建里丢掉。
③ Forecast 的 `ScrollingFrame` 只有 **292px** 真正空着：底部 60px 压在公告浮层
（ZIndex 5）下面，所以柱数上限是 `ForecastSlices = 11` 而不是 14（`DECISIONS` 62）。
④ **`MainMonitorFrame.Visible` 必须是 true，且 `GameCoreTitleBar` 不能漏掉。**
前者出厂在 **Alerts 上是 false 且没有任何脚本置真** —— `MonitorService` 每 tick 写的
27 盏灯全落在看不见的子树里（`DECISIONS` 105）；后者是内容层的绿色标题条，横跨 frame。
重建（或搬屏幕）后跑一次 `MonitorKit.Apply()` 再 `Probe()`，期望
`navy 7/7 greenBar 7/7 fullWidth 7/7 knockedOut 7/7 hiddenFrames 0/7`。

**刷新率：** `Config.Monitor.UpdateInterval = 0` → **每个 tick 都刷新**
（真实游戏有约 1 秒延迟，用户要即时。）

### 2.7 测试
| 测试 | 结果 |
|---|---|
| `GameCoreSelfTest` | `finalStatus: PASS`，`bridgeResolved 18`，`devices 15` |
| `GameCoreControlTest` | `pass:30 fail:0`，`finalStatus: PASS`，`levers:18 lamps:41`，`fluctuation signMatches 5/5`（另有 12 项 `stateTests` 表全 PASS） |
| GameCore 启动 | `[GameCore] started: 25 systems, 12 devices` |
| 控制总线 | `tagged=73 reindexed=73`；物理点击与总线调用产生同一条 `[Console]` |

**注意：** `GameCoreSelfTest` 跑一次后会**自动禁用自己**。
重新验证前要 `Disabled = false`。

**注意 2：** `fluctuation` 从旧记的 `60/60` 变成 **`5/5` 不是退步**。
`60/60` 量的是 `DECISIONS` 79 修掉的双写入 bug（`PowerSystem` 每帧写 `r.Temperature`），
所以 60 次迭代次次都有真增量。温度现在 1 秒才结算一次，`dt = 1/10` 的 60 次迭代
只能产生约 5 次真实更新。这个循环**故意没动** —— 它量的就是 1Hz 节奏本身。

**注意 3：** 旧记的 `pass:13` 是只跑第一阶段时的数字；第二阶段（12 项状态断言）
是 `DECISIONS` 88 补上的，见 §3.3。

### 2.8 视觉层（本会话完成，已保存验证）

> **⚠️ 2026-09-21 更正：下面这张表已过时，不要当现状读。**
> 通宵期间做过一次「偏暗」调色实验，用户看过之后说**「保留这版」**，
> 于是它成了新基线（`DECISIONS` 66 / `PROGRESS` Phase 21c）。**Lighting 里的实际值现在是**：
>
> | 属性 | 下表（旧） | **实际（现基线）** |
> |---|---|---|
> | `Brightness` | 2.5 | **1.2** |
> | `EnvironmentDiffuseScale` | 0.6 | **0.42** |
> | `EnvironmentSpecularScale` | 0.8 | **0.15** |
> | `ExposureCompensation` | 0.15 | **−0.08** |
> | `Ambient` | (31,28,26) | **(25,24,27)** |
> | `OutdoorAmbient` | (89,97,107) | **(52,60,72)** |
> | `Atmosphere.Density` | 0.38 | **0.20** |
> | `Atmosphere.Glare` | 0.15 | **0.08** |
> | `Atmosphere.Haze` | 1.2 | **0.45** |
> | `Atmosphere.Color` | (199,191,180) | **(120,128,138)** |
> | `Atmosphere.Decay` | (106,100,94) | **(38,36,40)** |
> | `Bloom.Intensity` | 1.15 | **0.85** |
> | `Bloom.Threshold` | 0.95 | **1.15** |
> | `ColorCorrection.Contrast` | 0.12 | **0.20** |
> | `ColorCorrection.Saturation` | −0.06 | **+0.02** |
> | `SunRays` / `ShadowSoftness` / `ClockTime` / `GlobalShadows` | 0.08/0.85, 0.3, 12, true | 未变 |
>
> **最关键的一条是 `EnvironmentSpecularScale` 0.8 → 0.15。** 下面 §2.8 那节记的
> 「本房间所有 `Metal` 部件不管 albedo 多少全渲染成白色」（`DECISIONS` 58 / 59）就是它造成的 ——
> 高光项压过漫反射，所以 `darker`(60,60,60 Metal) 和 `lighter`(186 Plastic) 渲染成同一个值。
> 降到 0.15 **不是审美改动，是那个 bug 的修复**。监视器深色壳带当初被迫改用 Neon 近黑只是绕路，
> 现在可以回头重做 —— **七台监视器已在新调色下复核完毕**（`PROGRESS` Phase 25 / `DECISIONS` 80）：Metal 壳带在新调色下回深灰，不再过曝成白。
>
> **教训：核对 Lighting 一定要读实例。** 这一轮我照这张表去核对，结果每一项都对不上，
> 白白多绕了一圈。文档里的数值会漂，`Workspace`/`Lighting` 里的不会。

**灯光大修** — 这是「画面难看」的**根本原因**：
```
EnvironmentDiffuseScale  0    → 0.6    ← 之前是 0，所有 PBR 材质全死
EnvironmentSpecularScale 0    → 0.8    ← 之前是 0，金属看起来像塑料
Brightness               2    → 2.5
Ambient                  (1,1,1) 纯白 → (31, 28, 26) 暖深灰
OutdoorAmbient           (0.27³)   → (89, 97, 107) 冷蓝灰
ExposureCompensation     0    → 0.15
ShadowSoftness           —    → 0.3
Atmosphere               不存在 → 密度 0.38 / offset 0.25 / 色 (199,191,180)
                                 decay (106,100,94) / glare 0.15 / haze 1.2
SunRaysEffect            不存在 → intensity 0.08 / spread 0.85
Bloom                    1/24 → 1.15 / 26 / threshold 0.95
ColorCorrection          全 0 → brightness 0.02 / contrast 0.12 /
                                 saturation −0.06 / tint (255,249,240)
```

**AI 材质（3 张，已生成并全量应用）**
`MaterialService` 下的 3 个 `MaterialVariant`：
| 名字 | BaseMaterial | 贴图 assetId | StudsPerTile | 应用数（现测） |
|---|---|---|---|---|
| `FacilitySteelPanel` | Metal | `rbxassetid://113678561896495` | 8 | **48,983** |
| `FacilityFloorPlate` | DiamondPlate | `rbxassetid://99453180185807` | 14 | **9,103** |
| `ReactorWallPlate` | CorrodedMetal | `rbxassetid://132401913334608` | 18 | **46,951** |

**关键洞察：全场景 80.2%（100,120 个）部件都是同一个默认 `Metal` 材质。**
换掉这一层 = 换掉整个游戏的观感。

> **⚠️ 这三个数是「现在」实测，不是不变量。** 三种材质**全部带 variant、未打标 = 0**。
> 旧值 `49,758 / 5,906 / 44,456` 是首次遍扫当时的快照；之后控制台 / 监视器重建、
> 激光重做、LED 条都改过总数，**别拿旧数对账**（`DECISIONS` 84、`PROGRESS` Phase 29）。
>
> 那次遍扫**按材质名过滤（只处理 `Metal`）**，所以**本来就写成 `DiamondPlate` 的
> 3,194 个部件根本没进循环**，渲染成库存菱形板，紧挨着 5,907 个带
> `FacilityFloorPlate` 的同类件 —— **同一材质名、两种外观，而且永远不会报错**。
> 已补齐 3,545 件（只匹配 `BaseMaterial`，避免赋值顺带改写 `Material` 本身），失败 0。
>
> `MaterialService` 另有 3 个**空壳 variant**（`MaterialVariant` / `MaterialVariant1`
> base Plastic、`CoolantRepeatingTexture` base Concrete），**无 `Texture` 子节点、
> 0 引用**，形态同 §5.3 的 `generate_material` 空产物。**故意不删**（§1.4 / §6）。

**灯光溢出**
给 `RoomLights` 里 260 个较大的 Neon 部件加了 `PointLight`
（之前它们「自己亮但不照亮任何东西」）。

### 2.9 场景规模（重要数字）
| 项 | 数量 |
|---|---|
| Workspace 总部件 | **127,111**（封存前 129,980，见 §2.11） |
| 顶层容器 | 42（整理前 1828） |
| ClickDetector 实例 | **941**（旧记 1,023，见 `DECISIONS` 84；实测 Consoles 内 69） |
| `LeverUnion` | 32 |
| `NeonPart` 灯 | 1,145 |
| Consoles 文件夹 | 2,381 |

**顶层大容器：** `CullFolder`(21,727) / `Mainframe`(17,078) /
`CoolantReserviors`(15,504) / `MovingParts`(13,094) / `Facility`(11,010) /
`ReactorCBLs`(8,291) / `QuantumMainframe`(6,071) / `Geometry`(5,695) /
`Lights`(2,659) / `GravitationShafts`(2,621) / `CRC1-3`(各 2,548) /
`Consoles`(2,381) / `ChamberWalls`(2,267) / `PowerExtractionAssembly`(1,921) /
`METU`(1,612) / `MonitorsFacility`(1,364) / `GravatronUnit`(1,266) /
`Alarms`(974) / `RoomLights`(561) / `MedicalDispenser`(483)

### 2.10 场景里已有的特效（不用重做！）
`Workspace.Core` 里**已经内置了 60+ 个粒子发射器**：
- `EFEParticlePart` 上 12 个：Meltdown / ThunderquakeLightning / Plasma /
  Gravquake / EquinoxRad / Lightning / MASS / Ambient / Outer / Mal
- 16 台 Laser 各带 `Fire` + `LaserHitParticle1/2` + `PointLight` + `FireLight`
- `Effects` 部件上约 30 个：Explosion×7 / Meltdown×6 / Instability×4 /
  EFE×7 / Equinox×2 / Core×2 / MASSParticle / ShieldShockwave
- `ForceField` / `Shockwave` / `Radiation` / `GlassBreak`

**问题不是「没特效」；但上面那句「只在事件触发时才喷」只能说对了一半。**
实测（`DECISIONS` 83、`PROGRESS` Phase 28）：

- `Workspace.Core` 确实全事件驱动 —— 97 个发射器**一个都没开**（`on=0 off=97`）。
- 但**整个设施早就有常态层**：全场景 **278 个发射器 `Enabled` 且 `Rate > 0`**，
  关着的 1,368 个才是事件触发那批。扣掉 `CullFolder` 里不渲染的 20 个，
  **258 个是真正在跑的常态氛围**，主力是 `Smoke` ×105 —— 就是「蒸汽 / 热气」本身。
  分布：`Geometry` 93 / `Facility` 56 / `Mainframe` 38 / `MovingParts` 21 /
  `GravitationShafts` 18 / `CoolantReserviors` 10 / `GravatronUnit` 10 / `METU` 7。
- 所以该做的**不是「造一层常态氛围」，而是让已有这层真的显示出来**：
  278 个里 **277 个的贴图是自定义资产 id**（只有 1 个用内置 `rbxasset://`），权限一断
  就等于「在喷但看不见」—— 不会报错，也不会有人发现。

---

### 2.11 旧件封存（2026-09-22，Phase 33）

原版的房间流式加载机制停了（`CullController` 是回收的反编译件、躺在 SS 里不跑），
`GameState` 也**从来没有房间/扇区概念**，所以世界冻在最后一次保存的状态。据此封存了两件：

| 从 | 到 | 部件 | 性质 |
|---|---|---|---|
| `ReplicatedStorage.CulledParts` | `ServerStorage.CulledParts` | **38,869** | 5 个未加载的扇区房间；RS 不渲染但会复制 |
| `Workspace.Reactor_Laser_Mk3_3` | `ServerStorage.Reactor_Laser_Mk3_3_StrayCopy` | **2,869** | 重建残渣；在反应堆舱外，零点击器/属性/标签 |

两个对象各带一个 `ORIGIN` StringValue 记录来历与还原方法。**没有删除任何东西。**

**计数变化（实测）：** RS 38,875 → **6**；Workspace 129,980 → **127,111**；SS 11,754 → **53,492**。
第一次搬迁 **Workspace 一件没动**，这就是「世界没被改动」的证据。

**仍然开着、需要用户拍板的**（可见、但没有任何活代码读它）：
`MovingParts`(13,094) / `ReactorCBLs`(8,609) / `Geometry`(5,695) /
`GravitationShafts`(2,621) / `ChamberWalls`(2,267)。
它们**正在渲染**，搬走 = 画面少东西，所以不能自作主张。

**`CullFolder`(21,727) 不在这张表里，也永远不要加进去** ——
Workspace 根本没有 `ControlRoom` 容器，玩家所在的房间就是 `CullFolder.ControlRoom`。
它零引用只说明没有脚本**点名**它。

**那 5 个扇区房间现在不在世界里。** `Workspace.Facility.Rooms` 装的是通往它们的
走廊 / 连接件 / 门厅（`MainHallwaySegment` / `HallwayRoomConnector` / `HMGatewayRoom` …），
**不含房间本身**。要不要恢复房间流式加载是设计决策，不是清理。

### 2.12 `RoomShell` —— 控制台**指向**的那些东西的写入者（灯带 / 监视器 / 百叶窗）

`SSS.ReactorBackend.RoomShell` 和 `VisualFeedback` 是**一对**，分工是一条线：
**`VisualFeedback` 写控制台上的东西**（拉杆、灯），**`RoomShell` 写那些控制台指向的东西**
（房间灯带、七台监视器、三扇百叶窗门）。两边都是 `--!strict`、都有一个
`Refresh(state, config)` 入口、都用**签名门**（`lastSignature`）挡掉没变化的 tick ——
所以「一个值只有一个写入者」（§2.5）在这条线上也是成立的：
**没有第二个模块碰这些部件。**

| `RoomShell` 写什么 | 在哪 | 由哪个 `state` 字段驱动 |
|---|---|---|
| 20 个 `NeonPart` 的颜色/透明度 + 8 个光源的 `Enabled` | 房间灯带 | `state.lights` |
| 7 台监视器（电源灯 / 屏幕光 / `ScreenGui.Enabled` / 若干面 `Visible`） | `Monitors` | `state.monitorPower`、`state.booted`、`state.phase` |
| **3 扇门的 `Frame.CFrame`** | `Workspace.MovingParts.ControlRoom{L,M,R}Shutter.Frame` | `state.shuttersOpen` |

**Phase 60（2026-09-30）起，百叶窗是 tween，不是瞬移。**

- **写入者没换**，换的只是「怎么到那里」（`DECISIONS_2` 187）。
- 行程 `Config.Shell.ShutterTravel = 10.58`；**开 = 关 减去世界空间的 `(0, 10.58, 0)`**。
  这个减法必须在**世界空间**做：中间那扇门的 `Frame` 绕 Y 转了 90°，
  写成 `CFrame.new(0,-travel,0)` 就是绕它**自己**的轴。
- 时长 `Config.Shell.ShutterTweenSeconds = 0.6`，`Quad` / `Out`（和拉杆同一套缓动词汇）。
  **不是**拉杆的 0.3：门走 **10.58** studs，拉杆一抛约 **0.7**，差 15 倍 ——
  同一个数会让门以 35 studs/s 飞过去。0.6 s 是 17.6 studs/s，一扇**带动力**的门的样子。
- 每扇门带一个**活 tween 句柄**，**创建新的之前先 `Cancel()` 旧的**（`DECISIONS_2` 188）：
  一个属性上两个活 tween 逐帧竞争、赢家按帧决定，中点连点可能把门停在
  **谁都没要求过的高度** —— 而那是**世界状态**，不是控制台上的一个姿势。
  `Cancel()` 留在原地，新 tween 从那里继续。
- **时长是配置，缓动不是**（和拉杆同一条）：缓动是机构的手感，不是谁能调的旋钮。
- `Config.Shell.ShutterTweenSeconds` 缺失或非正数时**只 `warn` 一次并退回模块自带的 0.6**，
  **行程不受影响**；warn 里明说行程没变，免得读的人去找一扇坏门（`DECISIONS_2` 190）。

**门的位置只从世界里读一次**（`shuttersCaptured` 闩，`Initialize` **故意不清它**）：
开位是「关位减行程」，所以**关位只能读一次** —— 等 `Refresh` 把门放下去之后再读，
读到的是**开位**，那个开关从此**反着**。闩只在**读全**时才落（`#shutters == 3`），
所以读了一半不会被冻在半个状态里。

**两个容易搞混的名字：**
`Config.Visual.LeverArcDegrees`（50）属于**旧的 `ControlVisuals`**（旋转式写入者），
`RoomShell` 和 `VisualFeedback` **都不读它**；
`StarterPlayer.StarterPlayerScripts.VisualFeedback` 是一个
`SUPERSEDED 2026-09-26` 的**客户端**反射器，**属性层确认 `Disabled = true`** ——
如果它活着，它就是一个逐 `Heartbeat` 写 `LeverUnion.CFrame` 的第二写入者，
会把服务端那个 tween **逐帧按回去**（Phase 59 之前它真的赢过，见 `PROGRESS` 59.2）。

### 2.13 `LogPanel` —— 开机消息链的第一个真读者（2026-10-01，Phase 65）

`SSS.ReactorBackend.LogPanel`，**只有一个出口**：`LogPanel.Refresh(engine)`。

**它补的是一个「只写不读」的洞。**`Engine:Log` 从写下第一天起就在往
`engine.events` 里记事件，而**全 DataModel 没有任何读者** —— 唯一提到它的
`MCP_FlowCollector` 读的是它**自己 new 出来的**私有 engine。所以整条开机链
（Phase 65 量到的 16 条消息）此前**写进了空气**。

| 项 | 值 |
|---|---|
| 写进哪个容器 | `Monitors.LogControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.LogsFrame` |
| 一次显示几行 | **4**（`365 / (60 + 20)` —— `LogsFrame` 的高度除模板高度加 `UIListLayout` 的 `Padding`） |
| 哪些事件上台 | `SHOWN = {ALERT, WARN, ERROR, INFO}`，**取最新四条** |
| 哪些不上台 | `CONTROL` —— `Engine:Command` 每条被接受的指令都记一条，那是**审计**不是机器说的话 |
| 颜色从哪来 | **模板自己的** `TextLabel.TextColor3`：青 `0.667,1,1` / 橙 `1,0.667,0` / 红 `1,0.306,0.306` |
| 写哪些实例 | **clone**（`Visible=true`、`LayoutOrder` 升序），每次刷新**先销毁上一批** |
| **不**碰的东西 | `TemplateLogFrame1/2/3` 本身 —— 它们的 `Visible=false`、`Text` 是原版存档残字 |

**为什么是 clone 而不是直接写模板**：模板是**原版美术的一部分**，
其中 `TemplateLogFrame3.TextLabel` 上那句残字 `E INITIATED` 是**这条链当初确实
经这三格渲染过的唯一物证**。写进去就把它毁了。clone 的代价是每拍重建几个实例，
收益是退出时 `LogsFrame` 回到「只有一个 `UIListLayout`」的原样。

**`RichText = true` 决定的另一件事**：捕获里那些 `<b>[ALERT]</b> - …` 是**真 payload**，
不是抓取 artifact，所以 `Config.Shift.StartupSteps[i].text` **连标记一起存**，
`kind` 另存一份给不想解析富文本的读者。

**由谁调**（`SSS.ReactorBackend.Runtime`，三处）：
初始化（第 31 行）、`ControlBinder` 的 publish 回调（第 38 行，在 `StateBridge.Publish` 之前）、
以及 `Heartbeat` 块里（第 55 行，在 `RefreshSeconds = 1` 的累加器**内**，
**不在**签名门后面 —— 事件流不是状态，签名对它是错的工具）。

**没做的**：`MaxCatchupSteps = 10` 意味着一次卡顿超过 10 拍时，`AdvanceStartup`
照发不误（表驱动，不漏），但面板**每秒只重画一次**，所以玩家看到的是**最新的四条**，
中间的可能一眼都没出现。原版有没有这个问题没量（`PROGRESS` 65.8）。

### 2.14 `BootPanel` —— 开机屏那 14 秒里唯一会动的东西（2026-10-01，Phase 67）

`SSS.ReactorBackend.BootPanel`，**只有一个出口**：`BootPanel.Refresh(state, config)`
（外加一次 `BootPanel.Initialize(config)`）。

**它补的是另一个「只写不读」同族的洞，这次是「摆了但永不出现」。**
remake 的 `BootFrame` 上那 45 个诊断 `TextLabel`、6 个 `TitleText`、1 个 `CompanyLogo`
**全部存盘为 `Visible=false`，而全 DataModel 没有任何东西会把它们放出来** ——
`RoomShell` 只切**整张脸**的 `Visible`，不动脸里面的东西。所以开机屏此前是**静止美术**。

| 项 | 值 |
|---|---|
| 数据源 | `Config.Shell.BootScreen.Reveals` —— **7 条**，`{at=秒, diagnostic={a,b}, log={a,b}, clearDiagnostic, clearLog, companyLogo}` |
| 长在哪几台 | **3 / 7**（Main / Thermal / Power）—— 与捕获里 `BootFrame` 只写这 3 台一致 |
| 驱动的属性 | 只有 `Visible`，**51 个 label**（45 诊断 + 6 标题）+ `CompanyLogo` |
| 相位门 | 只在 `state.phase == 'Booting'` 时按 `state.phaseTime` 走表；离开相位 → 全部收起 |
| 签名门 | `'Booting:<step>'` / `'idle'` —— 与 `RoomShell` 各自独立 |
| **不**碰的东西 | 任何 `Position`/`Size`/`Rotation`/`CanvasPosition` |

**为什么不做动画**：捕获里那 99.7% 的位移行是**按变化才写**的，一秒最多一个采样 ——
够说「什么时候动了」，不够说「沿着哪条曲线动」。**布尔活得过采样，曲线活不过。**
重建一条曲线 = 在采样之间**发明**形状再拿它当测量结果，那比不做动画更糟
（`DECISIONS_2` **231**）。

**单一写入者没破**：`RoomShell` 写 `BootFrame.Visible`，`BootPanel` 写**那张脸里面**
label 的 `Visible`。属性不相交 —— 这是它能成为第二个写入者的**理由**，不是事后补的验证
（`DECISIONS_2` **232**）。

**旧基线 `BootSeconds` 3 → 14**：t=8 之后屏上再无新内容，t=14 时 `PreStartupFrame`
在**七台**上出现。3 是自认的 presentation default；先前两次估的 21.8 s / ≤11 s
量的都是「MONITOR BOOT → 主拉杆被接受」，中间夹着玩家走位，**不是这一段**。

**验证**：`aux_expect.py`（从捕获重放）对 `aux_compare.py`（读真部件）**14/14 秒全等**，
两个变异各在预期的秒数段变红；跑完标签全部回到隐藏、临时件销毁
（`PROGRESS.md` 67.4）。**没在真 playtest 里看过一眼**，也没验世界侧（67.5）。

### 2.15 `intro/` —— 浏览器可播的 35 秒无声片头 + 它的视频版（2026-10-05，Phase 91/92/94）

**不在游戏里，不在 Studio 里** —— 这是一个**独立交付物**，双击就能用浏览器打开。
它是本仓库里唯一一件「渲染在浏览器而不是 Roblox」的东西，所以它有自己的验证链。

| 项 | 值 |
|---|---|
| 交付 | `intro/index.html`（单文件，可拖进度条）+ **`intro/THE_REACTOR_GAME_intro.mp4`**（视频版，5.61 MiB）+ `intro/SHOTLIST.md`（**脚本本体**：分镜 / 时间轴 / 逐行出处 / 渲染链） |
| 片长 | 35.00 s（mp4 = **1051 帧 / 35.033 s**），**无声**（操作员明确要求不用 `asstes/` 里的音乐） |
| 依赖 | 无。无构建、无 CDN、无 web font、无音频；素材**复制**在 `intro/assets/`（原始目录名带空格，引用会踩 URL 编码） |
| 架构 | **整片是 `render(t)`** —— t 的纯函数，没有状态机、不记上一帧 |
| 设计空间 | 固定 1920×1080 的 `#stage`，按 `min(w/1920, h/1080)` 等比缩放居中 |
| 结构 | `#film` **故意拆出 `#stage`**：CRT 收线只压 `#film`，播放器不被压扁 |
| 文案 | 24 行 **V**（逐字采集）/ 8 行 **G**（游戏别处原文）/ 13 行 **R**（重建）；6 条日志全 V；3 条规格卡是全片唯一非原文 |
| 渲染链 | `_tools/intro_render.js` —— CDP over Node 自带 `WebSocket`；逐帧 `render(i/fps)` + 截图 → ffmpeg `libx264 -preset slow -crf 18 -pix_fmt yuv420p` |
| 验证 | 桩 DOM `intro_check.js` **24 ok** ／ 真浏览器 `intro_render.js --check` **7 ok** ／ `intro_mutants.py` **13/13 变异红 + 3/3 FOLLOW 绿** ／ `ffprobe` **1051/1051 帧** |

**为什么是纯函数**：拖进度条要**真的跳**（不是快进）、循环要**逐字节可复现**、
出场时间要能**在 `T` 表里读到**。这与 `GameState` 的单一真相源同源（`DECISIONS_2` **303**）。
**这条纪律在渲染那一步兑现**：因为 `render(t)` 是纯的，「渲成视频」就只是
「`render(i/fps)` → 截图 → 下一帧」—— **没有时钟要抢、没有帧会丢、跑两遍出同一个文件**。
**它不是录屏**（**310**）。

**文字不是编的**：节奏抄操作员自己的 `Addition/Shift4.luau`；文字来自
`Data/flow/original_*` 与 `Data/auxcollection/startup/ScreenChanges.txt`（都 gitignored，
**逐字抄进代码就是留档**）。出处分三档而不是两档 —— G 并进 V 就是过度声称（**304**）；
拼写错误（`ACCEPETED` / `INFASTRUCTURE`）是**数据**不是 bug（**305**）。

**两个 harness，因为片子有两半，各自只能持有一半**（`DECISIONS_2` **307**）：

- `intro_check.js`（**桩 DOM**）：假 DOM、求值 file 自己的 `<script>` 字节、在选定时刻读
  内联样式回（同 §0.2 的「读实例、不读模块」）。**看不见排版** —— 桩里没有布局可错。
- `intro_render.js --check`（**真无头 Chrome**）：每 0.25 s 采一次
  `getBoundingClientRect()` 与行高，判 5 条 `L*`。**浏览器当尺子、判据写在 Node 里**
  （**309**）。`--at` / `--eval` 还能只出几帧 PNG 或读回表达式，供人看 / 供脚本读（§0.14b）。
  另有两段扫描：**22.0..34.2 每 0.25 s 判 `L5`**（两块可见文字有没有压在一起）、
  **全程 0..34.5 每 0.5 s 判 `L6`**（有没有字被裁掉而没有记号）。

**六个真缺陷，全是「没有任何东西会报错」那种**：开机令永久停在半句、黑场开始时边框还亮
一半、淡出越过了片长所以**从来没真的黑过** —— 前三个是桩 DOM 抓到的。**第四个只有真浏览器
看得见**：`#diagList` 锚在 `bottom:0`，1215px 的块塞进 630px 的窗 → 顶端落在 **−346px**，
滚动变换又减第二次，于是**面板前 7 秒是空的**、之后最多可见 2 行（能装 23 行），
**而每一行 `opacity` 确实是 1，那 24 条断言句句为真**。**读实例状态 ≠ 读屏幕**（§0.2 第七张脸）。

**第五、第六个是操作员用眼睛报出来的**（Phase 94，原话「结尾整个贼大的 THE REACTOR GAME
把后面字全挡住了」）：

- **标题压字**：`#titleCard` 是整屏覆盖层，`#title` 在 170px 时那块墨占 y 400..570，
  而 `sp2`(430..484)、`sp3`(542..596)、片尾那句(492..543)、页脚(566..584) **全落在里面**。
  **两个 harness 当时都是绿的，理由还不一样**：桩 DOM 结构上没有布局（307），
  布局 harness 量的是 `m.title.w > 200 && m.title.h > 20` —— 那条 1920×170 的带子**完美通过**。
  **这是 §0.2 第八张脸：每个元素各自都对，和它们互相盖住，是两个问题。**
  修法是 `#title` 两套几何（`HERO` → `MAST`），在第一条规格落墨前 0.15 s
  **抬上去缩成页眉**，把中段 300..620 空出来。断言 **`L5`**（同屏两两相交面积）从此看着它。
- **字被裁掉没记号**：诊断面板里两条开机记录比面板宽，
  `[LOG] THIS SYSTEM IS OWNED AND OPERATED BY …` 的墨到 **1671** 而面板右边缘 **1225**
  —— **吃掉 446 px**，断在词中间。行在屏上（L1 绿）、光标在窗内（L2 绿）、
  最新一行贴底（L3 绿）、`opacity` 是 1。**每一句都是真的，而 446px 的字不在那儿。**
  修法是一条声明 `overflow:hidden;text-overflow:ellipsis`（**不换行** —— 行高必须是一条常量，
  滚动算式靠它；**不缩字号** —— 那会把「滚动的终端」换成「一张静态列表」，是换效果不是修缺陷）。
  断言 **`L6`**（裁了要有记号，**不是**不许裁）从此看着它。

**渲染链三个必须做对的地方**（`intro_render.js` 注释里有全文）：① `requestAnimationFrame`
必须**在页面脚本之前**被掐掉（`Page.addScriptToEvaluateOnNewDocument`），否则页面自己的自动播
循环会在背后覆写已驱动的帧；② 视口**钉成**恰好 1920×1080，`fit()` 才给出 scale 1；
③ `#player`/`#bigplay`/`#hint` 是 UI 不是片子，渲染前 `display:none`。

**进仓库的是 mp4，不是中间帧**：1051 张 PNG（~300 MB）是过程产物，跑完自己删，
在 `.gitignore` 里（`_tools/_frames/`，同 `_tools/_harness_out/` 的理由 —— 跑到一半被杀
不留东西在暂存区）（**312**）。

**三个 harness 故意不挂进 `_tools/run_tests.sh`** —— 那个 gate 管的是注入 Luau 脚本，
这三个要 `D:\nodejs\node`（不在 PATH，§0.6）。手动跑：
`"D:\nodejs\node" _tools/intro_check.js` /
`"D:\nodejs\node" _tools/intro_render.js --check` /
`python _tools/intro_mutants.py`。
细节 `PROGRESS.md` 91/92/94，取舍 **303..312**、**322..326**。


### 2.16 `_tools/music/` —— 一首按**量出来的规格**写的原创曲（2026-10-05/06，Phase 93/95）

**也不在游戏里** —— 独立交付物，工具链在 `_tools/music/`，成品在 `asstes/music/`。

| 项 | 值 |
|---|---|
| 交付 | `asstes/music/ReactorShift.ogg`（5,908,619 B）/ `.mp3`（6,334,005 B）/ `.report.txt` |
| 时长 / 调性 | **263.84 s / 89.25 bpm / F 大调五声** / 97 小节 / 260.8 s + 3.0 s 尾 |
| **规格来源** | `asstes/music/ReactorStartup.mp3`（**别人的录音、别人的曲子** —— 操作员 2026-10-11 给的来源：`[WIP] (Piano) Portal 2 OST - Reconstructing More Science - Aperture Science Psychoacoustic Laboratories`，**一份钢琴改编**；**gitignored、不进仓库**）——`make_song.TARGET` 里每个数都是**对它测出来的**（`analyze.py` → `.report.txt`），**旋律一个音都没转录** |
| 生成 | `_tools/music/make_song.py`（**唯一**）—— 纯 numpy，无 torch、无模型、无外部素材 |
| 依赖 | numpy。合成原语在 `dsp.py`（加法/拨弦/滤波/混响 IR），编码走 ffmpeg |

**架构三条：**

1. **单一真相源 = `lead_plan()`。** 旋律是一张表
   （`(bar, beat, note, dur, tag)`，104 个事件），**渲染器和尺子读同一张表** ——
   尺子因此不可能量到自己的一份私有副本（取舍 333）。
   五个主题：`a` 三音动机的**陈述/移调应答**、`b` **上行句**（B2 顶到 C6）、
   `ctr` **反向**的下行长音对位，外加两段加速过门、一段**无旋律**尾段（81–91）、
   末句是增值的 A。覆盖 16..95 小节，响 100.0 s / 260.8 s = **38.3%**。
2. **电平是旋钮，不是缓存产物。** 缓存 `stems.npz` 里存的是**单位电平**的
   `leadD`/`leadS`，电平由 `with_lead()` 在**装配时**施加一次。
   `--reuse` 因此不会悄悄送出旧电平（取舍 331）；`with_lead()` **幂等**，
   `load_stems()` 对旧格式**直接报错**而不是产出一首「什么都正常、就是没旋律」的曲子。
3. **母带是闭环。** 三个 EQ 环把全曲八度轮廓对齐靶（残差最坏 +0.71 dB），
   再按 50 ms 帧把 RMS 拉到 **−15.10 dBFS**。靶：`rms −15.10 / side-mid 0.116 / corr +0.792`，
   落盘 `−15.10 / 0.107 / +0.809`，peak **−2.45 dBFS**（`PEAK_MAX_DB = −0.50` 是留给**编码器过冲**的）。

**验证（四条通道，各自管一半）：**

| 工具 | 量什么 | 现状 |
|---|---|---|
| `check_song.py` | 13 项 **对交付的 mp3/ogg 本身**（时长/峰值/削顶/RMS/动态弧/八度带/纹理/立体声/DC/click/fade） | **26/26 ok**；`--variants` **11/11 各自红在自己那条上** |
| `lead_margin.py` | **旋律相对无旋律伴奏的余量**，每音符一窗，窄带（±1/6 八度）/宽带（到 4×） | 窄带中位 **+6.5 dB**，**0/104 过零**，climax 段 **+12.8** vs groove **+6.4** |
| `analyze.py` | 任意音频 → `.report.txt`（10 s 块的频段占比、p5/p95、八度轮廓、side/mid、corr） | 高潮在**编曲时间线**上可见：中频 14% → **55%** → 23%（140–150 s） |
| `intro_check.js`/`intro_render.js`/`intro_mutants.py` | **片头**（§2.15） —— 和音乐无关，只是在同一个目录话题下 | 见 §2.15 |

**「余量」的定义是硬的**：底必须是 `with_lead(stems, 0, 0)`（定义上不含旋律）。
旧的尺子减的是一个**已经含 melody 的 mix**，误差 **11.4 dB** —— 两个缺陷写在
`lead_margin.py` 自己的文档字符串里（取舍 328/330）。

**没好听这一说**：上面每一个数都是尺子读数，**证明不了它好听**；
「有没有高潮」最终只能由操作员的耳朵答（取舍 332）。**Roblox 侧一个字没动** ——
没有上传凭据，且 `Workspace.Sounds` 是世界的一部分（`docs/TODO.md` §3.6）。
细节 `PROGRESS.md` 93/95，取舍 **313..321**、**327..333**。

**2026-10-11 追补：`_tools/music/remix.py` —— 同一段录音的一版真 remix（Phase 111）**

操作员要的是**真 remix**（改动那段录音，不是只借它的规格），去向是**游戏内音乐**。
和 `make_song.py` 是**兄弟工具，不是一个**：`make_song` 从零合成、旋律一个音都不转录；
`remix` **采样那份母带本身**，在它上面加鼓组、贝斯、结构、drop。

| 项 | 值 |
|---|---|
| 交付 | `asstes/music/ReactorStartup_Remix.ogg`（5,907,868 B）/ `.mp3`（6,407,984 B）/ `.report.txt` —— **三个都 gitignored** |
| 时长 / 节拍 | **266.93 s**（原曲 263.895 s）/ **90.000 bpm** / 97 小节（beat 0.6667 s，bar 2.6667 s） |
| 为什么忽略 | 它是**采样那份母带**做出来的，引用的就是那段录音本身，**不能比它的源更自由地发布**（取舍 **456**）；报告一起忽略（描述同一段音频，数字足以重建混音） |
| 工具 | `_tools/music/remix.py`（**进仓库**）—— 纯 numpy + `dsp.py` 原语 + ffmpeg；重用了 `make_song` 的 `add/klaxon/impact/bass_note/pingpong/write_wav`，**不复用** `ms.encode`/`ms.master`（一个写死 `ms.NAME`，一个瞄 `ReactorShift` 的八度靶） |
| 分数 | 派生数字写在 `PROGRESS.md` Phase 111（因为报告不进仓库） |

**三条和 Phase 93 相互印证的东西：**

1. **尺子是测量的一部分**（取舍 **454**）：仓库里那份 `ReactorStartup.report.txt` 是
   `--nfft 8192` / fps 21.5 的**粗尺子**出的（说 92.25 bpm），细尺子（fps 86.13）上
   90.00 的梳状得分 **326.174** 对 92.25 的 **13.441** —— **90.000 取代 92.25**，
   连理由一起写下来，不抹掉。
2. **小节相位只有 +1.01 dB 的余量**（阈值 1.0 dB）—— 这是全篇**唯一可能在听感上错**的一条：
   选错就是把整套鼓挪一拍，**单独听是对的、和音乐一起是错的**。判据原来是**斜率的**测量
   （四个候选单调、跨度 0.77%），换成**梳状**才成立（取舍 **455**）。
3. **编配是量出来的**（取舍 **457**）：最密的段落（50–57 小节）同时是最安静的（34–38 dB），
   最后 88 s 是最响的（45–47.6 dB）—— 按位置摊会把鼓压错地方、把最响的尾巴高通掉。

**检查（`--check`，对交付的 mp3/ogg 本身重测）：** 原曲占能量 **44.9%**、mix/ref 相关 **+0.753**、
`.mp3` peak 0.8943 / rms −13.42 dB、`.ogg` peak 0.9253 / rms −13.15 dB、八度轮廓相对原曲
+6.2 / +4.9 / +4.5 …（低频不再 +13.5）。**没验的：好不好听** —— 那是耳朵（同 Phase 93/95）。

**2026-10-11 追补（二）：`_tools/music/midi_grid.py` —— 一把**读**MIDI 的尺子（Phase 111 追补）**

操作员同一天往 `asstes/music/` 放了一份 `.mid`（**gitignored**，`asstes/music/*.mid`）并**只给了文件名**。
工具是**为读它而写的**，进仓库（我自己的代码）：

| 项 | 值 |
|---|---|
| 工具 | `_tools/music/midi_grid.py` —— **纯 stdlib 解析 SMF**（`MThd`/`MTrk`/VLQ/**running status**），不依赖 mido |
| 两种用法 | `midi_grid.py <f.mid>`（网格与织体）；`--compare <audio>`（**和一段音频比是不是同一首**） |
| 为什么**另起一把** | `analyze.py` 从频谱**推测**网格；**一份 MIDI 就是网格本身**。同一首曲子上，那个靠 **+1.01 dB vs 1.0 dB 阈值**勉强过线的小节相位，在 MIDI 里是**直接写着的数**（取舍 454/461） |

**它量出来的那份 MIDI：** format 1 / 4 轨全 program 0 / 384 tpq / **一个** tempo `60.0000 bpm` / 4/4 /
**936 个音只落在 296 个 onset**（平均 3.16 音/onset = 四声部）/
tick 34560 = 90.00 四分 = **22.50 小节 = 90.00 s** / **每个 onset 与 offset 都是 96 tick 的整数倍**
（= 十六分）/ 936 个音**只有六种时值**（705 个正好一个十六分）/ 音域 D2..D5。
**「照谱点进去的」转录，不是演奏**（取舍 460/461）。

**它和那份录音**不是**同一首（量出来的）：** MIDI 严格七声，**D#、G、A# 一次不响**；
录音的 chroma **没有空档**，第二大音级就是 **G（11.04%）**。
判据**必须旋转之后再问**：最佳旋转（−4 半音，r +0.680）**仍把 D#、F#、B 留在 0**，
而录音在这三处有 **6.67% / 6.31% / 5.75%** —— **任何移调都不是这份录音**（取舍 461）。

**这个工具写出来的第一件事是抓到了我自己**：曲长那行写成 `max(on + off)`（两个绝对 tick 相加），
把 90.00 s 报成 179.50 s；被同一轮加进去的自检「**有没有音符结束在自己那轨的结尾之后**」抓住
（每条轨都是 0）—— 自检留在工具里，**不过就 exit 1**（取舍 460，同 §0.6）。

**未定：** 操作员要拿这份 MIDI **干什么** —— 在 `QUESTIONS.md` **`M1`**，答之前不动它。


### 2.17 世界自己的健康检查（2026-10-06，Phase 96）

**这一节不为某个系统，是为了回答「我刚才那一下有没有把世界拆了」。**
它必须靠**读数**回答，不能靠眼睛 —— 而 `capture_screenshot` 在这个 place 里
不认显式机位（§0.14），所以「拍两张对比」这条路本来也走不通。

| 检查 | 现状 | 做法 |
|---|---|---|
| **部件总数不变式** | **91,905**（`Workspace` ＋ park，Phase 96 复原后**逐数相同**） | 遍历 `GetDescendants()` 数 `IsA("BasePart")`；**两边都数**（park 空即 0） |
| **根数** | `Workspace` 顶层 **1,210**（Part/Model/Folder） | 直接数 `GetChildren()` |
| **控制室密封** | 从控制台中心 `(113, y, 0)` **水平扇 720 条**（0.5°/条）× **y=281.5 / 283.0 / 286.0 = 2,160 条 → 0 漏** | `Workspace:Raycast` + `RaycastParams`（`Exclude` 掉被量的东西） |
| **天花板在** | 控制台上方 x 95..145 × z ±30，从 **y=280.5 往上**打 **20/20 命中**（y 288–298） | 同上，**方向必须朝上** |
| **那 8 条关键射线** | 全部命中（`down@170/230/spawn3/110console`、`up@170/200`、`east@200/230`） | 同一原点同一方向**复算** —— 「曾经 MISS、现在 HIT」才是证据 |
| **`RoomShell` 的绑定** | `Workspace.MovingParts` 是 Folder，`ControlRoom{L,M,R}Shutter` **各一件** | `FindFirstChild` 逐名，**并且数同名有几个** |

**四条纪律（都是踩出来的）：**

1. **从 y=400 往下打的「地板射线」打到的是天花板** —— 一条**问错面向**的射线会给出一个
   **响亮的、错的**数（§0.18 第五张脸，取舍 337）。**房间水平扫，地板从地板往上探。**
2. **「按名字找容器」先数同名有几个。** Roblox 允许**兄弟重名**（§0.22），
   这个 place 里有 **109 个叫 `Model` 的根** —— `workspace.Camera` 那个坑（§0.14）是同一件事。
3. **绑定要按字面路径复算**，不能只看「容器还在」。`RoomShell` 绑的是
   `'MovingParts.ControlRoomLShutter'` 这样的**字符串路径** —— 多一个同名兄弟，
   路径就落到**错的那个**上，而两个都在、都叫这个名字。
4. **「根还在不在」代替不了「它是不是那个根」。** 部件总数只证明**没有东西凭空消失**，
   不证明**它们还在原来的分组里** —— 后者要么有 ground truth，要么只能披露（取舍 340）。

细节 `PROGRESS.md` 96，取舍 **334..340**，片段 `docs/SNIPPETS.md` §5.23。

### 2.18 `luau-windows/gui.py` —— 一个 tkinter 控制台（2026-10-06，Phase 97）

**它不是游戏的一部分，也不是 Roblox 的一部分。** 它是 `luau-windows/calculation.py`
（那个 .py 和它旁边的 .luau 是**参考**）的一个**观察窗口**：把原来写死的三个量
（Temperature / ActiveFan / PEALevel）变成能改的控件，把五个量**实时**显示出来。
**一个文件，零第三方依赖**（tkinter 是 CPython 自带）。

```
cd D:\rblxTRGproject\luau-windows
python gui.py
```

| 区 | 控件 / 读数 |
|---|---|
| 左 CONTROLS | PEA 4 档**单选**（标题带 `+0 / +0 / +75 / +150`）· 风扇 0..6 **单选**（标题写 `each is -60`）· 温度 **slider + spinbox** · tick period spinbox · Pause / Step / Reset |
| 右 VALUES | Pressure（大号）· Delta · Core state · State band · Temperature · Ticks · Elapsed · Tick period · 分隔线 · `p = g - 60n + s t + d` 的**四项分解** |
| 下 LOG | 只追加的 `tk.Text`；`Pressure: N` 是 .luau 自己的输出，`#` 是注释 |

**取整只贴在显示层**（取舍 343）：`snap()` 是 .5 远离零，**故意不是** `round()`
（银行家舍入 + 这里的数真的会落在 .5）。模型一位不进，因为把模型取整会让它漂离原版，
而那个漂移**恰好在 .luau 对照里看不见**。唯一不取整的读数是 tick period（时长不是读数）。

**「间隔 1」的归属（取舍 342，逐字读过 Tk 9.0.4 的 `ttk/scale.tcl`）：**

| 操作 | slider 的行为 |
|---|---|
| 点 / 按住 trough | **±1**（`ttk::Repeatedly Increment $w ±1`）—— 这就是用户要的那个 |
| slider 上的箭头 | ±1（`<<PrevChar>>` / `<<NextChar>>`） |
| 中键 / 右键在 trough 上 | **跳到点击处**（`Jump`） |
| 拖 thumb | **绝对跟随指针**（`Drag`），此宽度 40000/300 ≈ **133 度/像素** |

`ttk::scale` **没有 `-resolution`**（那是经典 `tk.Scale` 的）**也没有 `-increment`** ——
所以那个能放**精确数字**的控件是 **spinbox**（`-increment=1` + `-format="%.0f"`），
两者都通过 `on_temp` 写模型，`_set_temperature` 是唯一写点。

**加东西（docstring 里也写了）**：加控件 = 摆在别的控件旁边 + 一个 `command` 写 `self.sim`
再调 `self.on_input(...)`；加读数 = `_build_readouts` 里多一行 `add_readout`。**没有框架。**

**验证**（harness 在作业目录，**不在仓库**——它们量的是这台机器的 Tk）：
`drive_console.py` **23 项 / `FAILED: none`**；`check_mutants.py` **10 ok / 0 bad**
（8 个真变异各自红在指定那一项、2 个 FOLLOW 留绿）。
**驱动走 `event_generate`、截图走 `PrintWindow`——全程不动操作员的光标**（取舍 348）。
细节 `PROGRESS.md` 97，取舍 **341..348**。

### 2.19 引力透镜 —— 用 EditableMesh 逐顶点驱动（`ReplicatedStorage.GravityLens` + 客户端引导）（2026-10-10，Phase 109 / 110）

**场景里多出来的一件纯视觉件。** 操作员要的是「黑洞扭曲」那种效果，
**用 editable mesh 编辑顶点做出动态效果**，硬约束是**不要动他的摄像机**
（全程一次都没写 `workspace.CurrentCamera`，也没调用过任何带 `camera_position` 的截图工具）。

| | |
|---|---|
| 在哪个 place | **`The Reactor [Rebuild]`，placeId `131274481205639`**（这一轮唯一接着的 Studio） |
| 盘上源码 | `_tools/gravity_lens.luau` = **24695 字节 / 695 行 / md5 `f65793aa941a7b558225028f0f4917b7` / sum33 `189076020`**（0 反斜杠 / 0 CR）。Phase 109 那份是 18961 字节 / md5 `984bfa338d4e79ec17a40fd080f7497d` —— 那是**服务端**形态，Phase 110 已作废 |
| Studio 里的源码 | `ReplicatedStorage.GravityLens`（`ModuleScript`，**24695 字节 / sum33 `189076020`**）——**唯一一份** |
| Studio 里的引导 | `StarterPlayer.StarterPlayerScripts.GravityLensClient`（`LocalScript`，`require(ReplicatedStorage.GravityLens).start()`）——**Play 模式**里在**客户端**建网格并 `Heartbeat` 驱动 |
| Studio 里的静帧 | `Workspace.GravityLens`（`MeshPart`，Size `92, 92, 10.303`，Neon，`DoubleSided`，落在 `-151.10 58.00 71.00`，朝向 `0.4099, -0.4912, -0.7686`）——**它现在只是摆位锚**：客户端读它的 `CFrame` 再自己建，建完就删掉它。**它本身对任何客户端都不是透镜**（棋盘格占位） |
| 已删除 | `ServerScriptService.GravityLens`（Phase 110 删）——**服务端建出来的网格，客户端画不出来** |
| 拓扑 | `RINGS=64 × SPOKES=152` = **9728 顶点 / 19152 面**（上限 60000 / 20000，留 848 面余量） |
| 物理 | **不参与**：`CanCollide=false`、`CanQuery=false`、`CastShadow=false` —— `SetPosition` 只改**渲染**，碰撞是快照（§5.18） |
| 身份标签 | `M.TAG = "lens-a1"` |

**它画的是什么。** 一张**正对着它的平面盘**，每个顶点按**点质量透镜映射**
`beta = R - rE^2 / R` 采一个源平面的样子（`rE` 是爱因斯坦半径，环内 `beta` 为负 =
源被翻到对面），叠一个高斯**环增亮**（`RING_BOOST = 2.4`，`RING_WIDTH = 0.012`）、
一个 `FADE_IN` 边缘、以及 `R_VIGNETTE` 外的淡出。**动态**来自每帧改 `SetPosition`：
**旋流**（越靠内圈拖得越狠，`SWIRL = 0.30` rad / 23 s）、**呼吸**（`BREATHE = 0.045` / 11 s）、
**涟漪**（`RIPPLE = 1.5` / 7 s），30 Hz。

**为什么是 `Script` 而不是一堆调好的属性：** Edit 模式建出来的 `MeshPart` 是**静帧** ——
可读、可截图、**但不会动**。会动的那一版必须是 Play 里跑起来的脚本，而 **Edit 改 `Source` 不动运行时副本、
Play 里改不落盘**（§0.4）。所以「交付」是**那两个东西 + 同一份字节**（见上手 `docs/SNIPPETS.md` §5.24）。

**验证（三条独立通道）**：① 逐顶点快照 —— `t=0` 时所有 Y 为 **0**，`t=5.75` 时 Y 最大 **2.838**，
且 `outerMoved 1.270` / `innerMoved 1.209` 与运动学一致；② §5.18 往返
（`MeshPart.MeshContent -> CreateEditableMeshAsync`）`worstPositionDelta 0`、
颜色差 `0.0029`（= **1/255**，mesh 的 8 位量化，不是缺陷）；③ **色场**渲成 ASCII PPM
（`receive.py` 侧 CRC `0fa36841` @200² / `42393a69` @300²，两边逐位相同）再由
`_tools/ppm_to_png.py`（纯 stdlib，零依赖，**`-I` 底下也跑得动**）转 PNG，
视觉桥评 **Excellent / 无缺陷**。渲染图之外**单独渲色场**，是因为 `screen_capture` 量的是渲染器
（材质 + 光照 + 后处理一起算进来），而这里要问的是**顶点颜色对不对**。

**「它真的在动」的证据只有一对受控对照**（取舍 443）：`camPos` / `partPos` / 部件 / **模块实例**
（持久 holder `require` → 命中模块缓存）全钉死，只让 `clock` 5.75 → 17.25，
`compare_images` 报**内部图案顺时针转**（内环峰 6 点 → 5 点）。

**Phase 110：它搬到了客户端，而且在跑起来的会话里验过了。** 操作员问
「为什么我进测试之后透镜变成一个小方块」，量到的原因是
**`MeshContent.SourceType = Object` 是进程局部的**：同一个实例、同一句
`CreateEditableMeshAsync(part.MeshContent)`，**建它的那个进程**回 9728 顶点 / 跨 `±46`，
**别处**回 **1536 顶点 / 跨 `(0,0,0)..(1,1,1)`** —— 一个单位立方体，渲染器把它画成
**棋盘格占位**。所以交付改成**在画它的那个进程里建它**：`ServerScriptService.GravityLens` 删掉，
`Workspace.GravityLens` 降格成摆位锚，`ReplicatedStorage.GravityLens` +
`StarterPlayerScripts.GravityLensClient` 顶上去；`M.start()` 里加了能力闸 `meshApiUsable()`
（给不了网格的进程不留棋盘格板子）。

**Play 里量到的三条：** 画出一枚完整透镜（两帧之间内环转过去了）；`MeshContent` 往返取两次、
相隔 1.2 s，最大位移 **0.0072 stud**（与 `SWIRL 0.30 rad / 23 s` 在 `r = 0.073` 上逐位吻合）；
`t+220 s`（约 6600 拍）之后仍是完整透镜，预算恒 `ok`。`passes = 446 / ~15 s` ⇒ **29.7 Hz**。

**没验的 / 待追的：** 早先看到的「客户端自建透镜在持续改写后变棋盘格」**今天没有复现**
（`stride = 1` 全量重写与 `stride = 4` 各跑满 4 分钟都是完整透镜）——
**「每帧写多少」不是已证的机制**，分片 `CFG.SLICE_STRIDE = 4` 只是**保险**；
`Enable Mesh / Image APIs` 这个开关**只有操作员能开**（`QUESTIONS.md` L2）。
细节 `PROGRESS.md` 109/110，取舍 **442..453**，`docs/SNIPPETS.md` **§5.25**。


### 2.20 `_tools/music/midi_song.py` —— 演奏一份 MIDI 的音符（2026-10-11，Phase 112）

`_tools/music/` 里第三个兄弟。**它不是模式，是另一种源**：
`make_song.py` 自己作曲、`remix.py` 采样一段录音、**这一个演奏一份 MIDI 的音符**。
交付 `asstes/music/ReconstructingMoreScience.{ogg,mp3}`（96.000 s）。

**跑法**
```bash
cd _tools/music
python midi_song.py --mid "../../asstes/music/<name>.mid"     # 渲染 + 编码 + 自检
python midi_song.py --mid "..." --probe                        # 只报计划和测量
python midi_song.py --mid "..." --check                         # 只重量已交付的文件
python midi_song.py --mid "..." --bars 4                        # 前 4 小节干跑，不编码
```

**结构**（每个数都是量出来的，不是写的）
- `load_source` → 复用 `midi_grid.parse`（纯 stdlib 的 SMF 解析器）。
- `bar_stats` → 每小节音符数 / 最低音 / 音级集合（`counts, lows, pcs`）。
- `sections` → 按 `hi*peak` / `lo*peak` 分 full/thin/sparse 并合并连续段。
- `pedal_gate` → **每四分音符格的贝斯根音**触发踏板；**被否掉的规则也在同一次跑里印出来**。
- `render_piano` → 加性钢琴音色（`piano_note`，18 个分音、每个分音各自截断），
  加 ±12 ms 人味抖动与按音高的声像。**音符落位用 clamp 不用 continue** —— 丢一个音是错的交易。
- `render_sub` / `render_pad` / `render_marks` → 见 Phase 112 的表。
- `master` → 归一到目标响度是**不动点**（归一到目标 → 限幅 → 测量 → 重来，≤4 趟），
  并把限幅器削掉多少印出来。

**四条写下来的纪律（都是这一轮踩出来的）**
1. **打击层按峰值定级，不按 RMS。** 一个瞬态的 RMS 只是它峰值的一小撮（取舍 463）。
2. **响度目标是不动点，不是一步** —— 在峰值保护之前加的增益，不是到达文件的增益（取舍 464）。
3. **`0.5 * (L+R) ** 2` 是 `0.5 * ((L+R)**2)`**，比单声道 RMS 高 √2，而且不报错（取舍 465）。
4. **相关峰落在梳齿上时，argmax 不是测量** —— 搜索窗要窄于半个网格，并且用物理去判 lag（取舍 466）。

**自检（`check_files`，ogg/mp3 各 10 项）**
时长 / 峰值 / 响度 / **最佳移调是不是零** / chroma 相关 / **事件落位（窗宽半格 + 物理预言）** /
**首个起音的位置** / 单声道兼容 / 无极性翻转 / 无点击。
其中两条是**为了替代两把编错的尺子**而写的：旋转检验替掉 top-4 顺序（取舍 467）、
半格窗 + 物理判据替掉宽窗 argmax（取舍 466）。上手片段见 `docs/SNIPPETS.md` §5.26。


### 2.21 `ShockRipple` —— 冲击波盘的涟漪（`Workspace.Folder.Model.ShockRipple`，2026-10-11，Phase 117 → 118 → 119）

**不是仿真，是画面。** 它不读 `GameState`、不写任何被玩的东西。它把那个特效模型自己的
冲击波盘（`Cylinder2`，直径 120，**本质是个 18 边形**）**另做**一遍，
让一道波从中心跑到边上，一波接一波。

**为什么不去改那块盘本身：** 那个 `Model` 是导入件，`Cylinder2` 被它自己的 `Script` 引用
（`Mesh.Transparency` 那条闪白链）。**原地不动、新件另挂**，`Cylinder2` 一个字节没改。

**当前跑的是 Phase 118 的那张薄片**（用户：「根本不丝滑」，要 EditableMesh）：

- 件：`StarterPlayer.StarterPlayerScripts.ShockRippleClient`（`LocalScript`，
  盘上原文 `_tools/shock_ripple_client.luau`）。
- 形状：一张 `EditableMesh` 薄片，**18 个楔 × 24 个环 × 2 层**（`verts=1800 faces=1728`），
  外半径 60.000；每帧只改顶点的 Y，所以运动是**连续**的。0.85–1.13 ms/帧。
- **两种运动**，由属性 `Motion` 选（两个都留着，没有互相取代）：
  - `"wave"`（**现在的默认**）：一个鼓包在中间出生、以 `Speed` studs/秒往外跑，
    宽度是 `Width` 个 `Period`，下一个隔 `Period` 秒跟上。
  - `"pulse"`：整张网同步上下呼吸 —— 中间 ±`Amplitude`，到边缘衰减到零。
    用 `Amplitude` / `Period` / `Transparency`；`Speed` / `Width` 在这支里不参与。
- **两种运动共用同一个包络，`Falloff` 是它的指数**：
  `envelope(r) = (0.5*(1 + cos(pi*r/RADIUS))) ^ Falloff`。升余弦在 `r = RADIUS` 处**恰好** 0
  （`cos(pi)` 双精度就是 −1，底数是 0，`0^p` 对 p>0 就是 0），两端斜率都是 0，
  而「取幂」不破坏这三条 —— 所以任何 `Falloff` 都不会在中间或边上折出棱来。
  `Falloff = 0` 关掉衰减、就是 Phase 118 那版**全程满高跑到底**的波；
  `1` 是「一半半径处一半高、到边上没了」；`2` 是贴着中间更久、然后陡然掉。
- **它只活在本地客户端**：`Content.fromObject` 做的东西不跨进程（§0.23），
  每个客户端自己建一张 —— 所以**服务端和 Edit 模式都看不到它**，这是设计代价不是 bug。
- 光环：运行中把原盘在本地隐掉（`Wave.Transparency = 1`，客户端本地写入）。
- 调参全在属性面板（改完一帧内生效）：`Motion` / `Falloff 1` / `WaveEnabled` /
  `Amplitude` / `Speed 60` / `Period 1.2` / `Width 0.5` / `Transparency 0.15` /
  `Segments 18` / `Rings 24` / `Reassign false`。改 `Segments`/`Rings` 会重建网格。
- 自检：每半秒把 `t / active / motion / falloff / sheet / disc / ms/frame / 几个环的高度`
  写进 `ShockRipple.Diag`（`StringValue`）；**另有一次读回**，把"件里真的是多高"和
  "脚本这帧写了多高"并排印出来。
  **`Diag` 是唯一能读的东西** —— 服务端和 Edit 里那张网根本不渲染（见上）。
  另：`Instance:GetAttributes()` 在这个助手的沙箱里**回空表**（`GetAttribute(name)` 正常），
  所以按名字读，别指望枚举（取舍 495）。

**Phase 117 那 12 个同心环（`C1`..`C12`）已经不在了 —— 不是停用，是从 DataModel 里删掉了。**
2026-10-11 本轮改写时量的：`Workspace` / `ServerStorage` / `ReplicatedStorage` 三处搜 `C1`/`C12`
**各 0 个**，`ShockRipple` 的兄弟只剩 `Cylinder2` + 18 个 `Neon` + `Ring` + `Script` + `Union`。
**不是这一轮删的**（本脚本从不 `Destroy` 它们），原文里那句「停用不是删除、把 `Enabled` 打回 `true`
就能回来」**已经作废** —— 开关还在、`Rig` 那个 4038 字节的服务端脚本还在，但它现在没有可动的对象。
要恢复只能从旧存档 / 重新建，**别在这份文档的基础上承诺它还能回来**（取舍 496）。

- 老效果仍然值得留的场合：**碰撞 / 射线 / 一次给所有人看**（薄片做不到这三件）。

- 一次性播放的入口（两个驱动共用）：`ShockRipple.Play`（`BindableEvent`）→ `rig.Play:Fire()`。
- 上手片段：薄片见 `docs/SNIPPETS.md` §5.28，CSG 环见 §5.27；取舍 485–498。

### 2.22 `FacilityCascade` —— 世界的开机（`SSS.ReactorBackend.FacilityCascade`，2026-10-13，Phase 122）

**它是什么**：`Runtime.server.luau` 里的第 4 个适配器 —— `VisualFeedback` 管控制台、
`RoomShell` 管控制台**指向**的那些东西（灯带 / 监视器 / 百叶窗）、`BootPanel` 管开机屏里的字，
它管**世界本身**：七组灯、三台 CBL、舱内警报、堆芯。
跟着引擎自己那条链走（`Config.Shift.StartupSteps` 16 条 / `state.startupStep`），
`Config.Cascade.Beats = {Dim=2, Energise=11, Fire=14, Ignite=16}`。

**它拥有哪些属性**（单一写入者，别的模块不许碰）：
- `Workspace.Lights.<组>`：ClampLights / ChamberLights / LoungeLights / SubLoungeLights /
  ControlRoomLowerLights / MaintFacilityLights / METULights 的 `Color`，以及每盏灯对象的
  `Enabled` / `Brightness`。
- `Workspace.ReactorCBLs.Reactor_Laser_Mk3_*`：`Effects.FiringEffectPart.Size/Transparency`、
  三个转子（`Effects.SpinnyThingsFront/Back/SlightlyBetterSpinnyThing`）的
  `Moter.HingeConstraint.AngularVelocity`、七处霓虹色、`SoundPart.AmbientHum.Pitch`、
  各类粒子 `Enabled`、`SoundPart.LaserVentSFX.Playing`、`Laser.Main.Transparency` 与
  `Laser.LaserPart.Transparency`。
- `Workspace.Alarms.ReactorChamber`：`MoterPart.HingeConstraint.AngularVelocity`、
  `SpinnyPart.Neon.Color` 与 `NeonLight.Color`、`NeonLight.IndustrialAlarmLight.Enabled`、
  `MainAlarmPart.IndustrialAlarmSound.Playing`。
- `Workspace.Core.*`：`CORE.Transparency`、`CORE.PointLight.Enabled`、`ProtoCoreLoop`、
  `ExplosiveCoreEffect.Size`、`ForcefieldShockwave.Size/Transparency`、两种爆炸粒子、
  `IgnitonExplosion`（**游戏自己的拼法，别改**）。

**三个入口**（§0.19：每帧的活儿必须是公开函数，不许藏在 `Connect` 里）：
`Initialize(Config)` 抓基线并登记 target；
`Refresh(state, Config)` 跟着 `state.startupStep` 走状态、发事件（每秒的逻辑门与
`ControlBinder` 各调一次）；
`Step(dt)` **不做门控**，由 `Heartbeat` 直接驱动（`math.min(dt, 0.5)`）——
所有连续的量（四段 ramp、firing 球的塌缩、10.9 s 的警报）都在这里，藏在 1 秒的门后面
会把 1.6 s 的淡入变成两个硬台阶。

**基线是世界的数**（不是 Config 里的第二份）：`Initialize` 读每盏灯的
`Color` / `Light.Enabled` / `Brightness`；倒回去靠 `rewind`（`Refresh` 把 step 倒回时触发）。
**实测精确可逆** —— 走完 step 0..16 再倒回 0，读数逐项回到走之前（`PROGRESS` Phase 122 第三节）。

**两个坑**：
1. **探针把世界点亮 = 把授权基线点着。** 下一次 `Initialize` 会把"亮着"当成"授权"，
   整场开机**静默失效**（ramp 从 `on` 到 `on`）。`ColdBaseline=true` 救不了（它的 `off` 也读世界）。
   恢复路线见 `docs/SNIPPETS.md` §5.29（`_tools/cold_baseline.py` → `Data/cold_baseline.tsv`）。
2. **一件灯只有在"没亮着、且颜色不是它自己的点亮色"时才被收进来**：手动把某组点亮，
   那一组就**不会**进这一场的 ramp（看起来像"少了几盏"）。

**验收**：`Data/startup_shots/` 三张同机位图（冷 / CBL 出射 / 点火）
\+ 灯普查 `592/742`、`32` 盏（METU 的）。

**实机验证（Phase 123，2026-10-13）**：整条链在**游戏自己的 Runtime**里跑过一遍
（真点击 `MONITOR POWER → SHUTTERS → BOOT → START`，四条 oracle 全绿），
113.4 s 后 `RuntimePhase=Running`、`RuntimeError` 空，点火那一拍逐条对上 cue：
`CORE.Transparency=0`、`CORE.PointLight.Enabled=true`（brightness 30 / range 60 / 色 `0,149,255`）、
`ProtoCoreLoop.Playing=true`、`ForcefieldShockwave` 111.19 / transp 0.926、
`ExplosiveCoreEffect.Size` 120→80（+10.6 s）、`Laser.Main.Transparency` 3/3 = 0。
灯火按 `>0.2` 同一把尺子前后量：Clamp **48→96**、Chamber **0→78**、Lounge **30→36**（Δ 正是 48/78/6）。
证据图 `Data/startup_shots/4..7_live_*.jpg`；详细读数 `PROGRESS.md` Phase 123。

**这条链在真机上曾被一个**落后的副本**挡住**：Studio 的 `Engine` 比磁盘旧一个版本
（`c.Sim.PressureDivisor` 已被 Config 退休 ⇒ 第一次进 `Running` 就崩在 `Engine:273`）。
十个模块里只有它不同 —— 取舍 **512**。

### 2.23 `EndShiftBridge` + `EndShiftResume` —— 班次结束的握手（`SSS.ReactorBackend.EndShiftBridge` / `StarterPlayerScripts.EndShiftResume`，2026-10-13，Phase 124）

**它补的是什么。** `StarterGui.ScreenGui.EndShiftHandler`（610 行）在这个 place 里
**从来没有出现过一次**，因为它两头都没接上：没人 fire `ReplicatedStorage.EndShift`、
没人监听 `ReplicatedStorage.MiscEvent`（**那才是这块屏幕真正 fire 的 remote**）、
没人 fire `ReplicatedStorage.ResetEvent`。于是一个走到 `Report` 或 `Failed` 的班次
**没有出口**：`Engine:Command` 过了结尾就以 `'Shift ended'` 拒绝一切，
而那是服务端 console 的一条 warn。操作员 2026-10-13 报的
「突然就是 shift ended 了」量的正是这个（取舍 516）。

**两个半边。**

| 边 | 文件 | 做什么 |
|---|---|---|
| 服务端 | `SSS.ReactorBackend.EndShiftBridge` | `Publish(engine)` 每秒跑，相位是 `Report`/`Failed` 时给**每位玩家**发一次报告；`Bind(engine,publish)` 接 `MiscEvent` / `ResetEvent` 并返回绑定到的名字（`Runtime` 把它写成 `ShiftTransport` 属性） |
| 客户端 | `StarterPlayerScripts.EndShiftResume` | 收到 `'Accepted'` 回执就收屏幕、把作者可见性**从世界读回来的**基线复位；`'Refused'` 就把报告交还（§0.24） |

**发出去的六个字段**（`EndShift.OnClientEvent` 的载荷，屏幕 610 行读的就是这六个）：

```lua
lines   = {}                       -- p1 逐条钱的明细。空表 ⇒ 屏幕一行都不加（line 505）
reason  = 'Power extraction assembly overload'  -- p2 也是「配额有没有达成」的判据
total   = 0                        -- 本 build 没有经济，0 是**真话**
shift   = s.shift                  -- 引擎的真值
session = { OT, ST = {Hour,Min,Period,CurrentEnergy,TargetEnergy}, NG, NL }
metu    = 2                        -- ≥2 ⇒ 屏幕不动那行 'METU STATUS - FULLY OPERATIONAL'
```

**三条设计上的取舍，都是「让它看起来像原文 / 不像赝品」：**

1. **钱发空表，不发零表。** 屏幕对空 `lines` **一行都不加**，总额 0 于是落在
   它**自己写好的**零总额分支上（line 553：灰字 + ` ... Good Job`）——
   那是作者画的路径，不是我拼的载荷形状。
2. **`OT` 是 `HH:MM.mmm`，不是 `HH:MM:SS.mmm`。** 标签
   `IntermissionFrame.AdditionFrame.TextFrame.OperationalLabel` 的作者形状就是
   `'%02d:%02d.%03d'`；`122.0 → '00:02.000'`、`7325 → '02:02.000'`
   （**我曾把 `00:02.000` 读成 2 秒**，据此怀疑 `elapsed` 被重置 —— 没有，那是 2 分钟）。
   它读 `s.elapsed` 而不是 `s.time`：`elapsed` 只在 `Running` 里累加，那才是运转时间。
3. **`Lobby` 改写成 `Reset`，不改写成死路。** `HoldButton` 的默认 `v15` 就是 `'Lobby'`，
   所以它是**默认路径**。原文这一刻是传送（重生重克隆 `StarterGui`），
   而这个 place 没有传送也没有大厅。拒绝 = 把操作员的原始抱怨原样还给他（取舍 517）。

**去重键是 `UserId`，放在普通表里**（取舍 518）：原先用 Player 实例做弱键（`__mode='k'`），
真机上量到**一个仍然在 `Players` 里**的 Player 会在第 8 次 GC 被收出去 ——
于是同一个结局**发了两次、正好隔 60 s**。同一个弱点在 `ControlBinder.lastUse` 里
表现为「速率门对一个还在场的玩家悄悄不再生效」。

**它为什么是一个独立模块。** 形状和其它适配器一样：**不持有状态**，
只读 `engine.state.phase`，每帧/每秒的活儿写成公开函数（§0.19），
`Bind` 返回**它真正绑到的**名字 —— 没挂上的传输和没有东西可报的传输长得一样。

**验收**：离线 66 项（`_tools/endshift_payload_test.luau`，含去重与三个词的走向）；
真机一条完整链（`Failed` → 报告 → 按住确认 → `Cold` + 屏幕收下去 + 界面回来），
读数见 `PROGRESS.md` Phase 124 第三节。

### 2.24 `AlertsPanel` + `ForecastPanel` —— 开机链的最后两块屏（`SSS.ReactorBackend`，2026-10-13，Phase 125）

**它们补的是什么。** `Workspace.Monitors` 下七台屏里，`AlertsControlRoomMonitor` 的
27 行指示格和 `ForecastControlRoomMonitor` 的深扫公告**从来没有接线**：
`script_grep` 整个 DataModel，`AlertsFrame` 零个读者，`TimeSliceTemplate`、
`AnnouncementFrame`、`EFEFrame` 同样。`RoomShell` 只管**显示哪一张脸**
（`Booting`/`Ready`/`Starting`/`Running`/`Stopping`/`Report`/`Failed` → 五个 frame 的
`.Visible`），脸**里面**的内容一直没人写。

**一个属性一个写入者。** 两个模块写的都是 **`RoomShell` 不碰的**属性：
`AlertsFrame` 住在 `MainMonitorFrame`（`RoomShell` 写它的 `.Visible`）里，
而 `AlertsPanel` 写的是**格子内层那个彩条 `Frame`**；`ForecastPanel` 写
`AnnouncementFrame`（作者就设成 `Visible=false`）的子件、`EFEFrame`，
以及 `Screen` 上的三个 `Sound` —— `MonitorUI` 自己的 header 已经把 `EFEFrame`
列为「故意不拥有的」。所以切法和 `BootPanel` 同源。

**警报格的机制**（`AlertsPanel`，13863 B）：27 块 100×100 灰片，每块背后
（**ZIndex 0**，label 在 ZIndex 1）压着一个同尺寸、`BackgroundColor3` 为那一行类别色的
`Frame`。**开关那层 `Frame.Visible` 就是全部机制** —— 也是原版录像在这块屏上
**唯一**写过的属性。

| 行 | 条件取自 |
|---|---|
| 1 RECT ACTIVATION | 深扫窗口（`startupStep ∈ {9,10}`）—— 依据是录像里它与深扫公告**同一对轮询**翻转 |
| 2 SUBSPACE FIELD | `startupStep >= 7`（链自己那句 `SUBSPACE RIFT ACTIVE`） |
| 3/4/5/6/7/8/9 CBL·CORE·PUMP·FAN·H.D.E.F.·G-GATE·RADIATION | 引擎的 `cbl[].active`、`coreState`、`pumps[].enabled/integrity`、`fans[]`、`hdef.enabled`、`grav.phase ~= 'Idle'`、`radiation` |
| 10..27 | 手册的阈值（400 GW/H、75%、400F、~6000F）或引擎自己的数（`ShutdownLimit`、`Sim.HighPressure`、`CBLStressThreshold`）；**两行留黑**（取舍 522） |

刷新按**点亮集合**做签名闸（27 个 `'0'`/`'1'` 拼成一个串），所以安静的一拍
**一个属性都不写**。条件行只在 `Running`/`Stopping` 参与判定，1..9 行（起机那些）
在任意相位都参与。

**深扫公告**（`ForecastPanel`，13605 B）逐秒抄自原版录像
(`Data/originalwatch/260930-200834`)：

| 偏移 | 发生什么 |
|---|---|
| +0.00 | `AnnouncementFrame.Visible=true`，文案 `PROCESSING DEEPSCAN TELEMETRY`，绿 |
| +3.35 | `Beep.Playing=true` |
| +5.04 | 文案换判决、颜色换判决色、`Beep→EFEPing`（**同一拍三件事**），**横幅亮** |
| +9.37 | `EFEPing` 灭 |
| +12.89 | 公告灭、颜色回绿、`TimelineComplete` 响 |
| +14.63 | `TimelineComplete` 灭 |

判决**不是固定字符串**：引擎唯一建模的子空间事件是 Equinox
（`Events.EquinoxSeconds = 720`），深扫把那一刻投影成钟点、再和
`Forecast.BreachHorizonSeconds = 900` 比 —— 现在得到
`HADEN THRESHOLD BREACH ~3:15 AM`（红）；不破界则是
`ANOMALY DETECTED, MARGIN ~…`（黄）。钟点映射（`Clock.StartHour=23`、
`MinutesPerSecond=1/3`）**是我们的数**，录像只给了判决的形状（取舍 524）。

**横幅（`EFEFrame`）是七台屏一起亮的**，这就是手册那句「when an EFE is about to occur,
all monitors will display a warning」。它有**自己的秒表**（`bannerLeft` 在 `Step` 里倒计时，
`Refresh` 只 latch `equinox`）—— 原先兜在 `sequence ~= nil` 上会让落地时间比声明的
`BannerSeconds = 10.25` **短 0.66 s**（取舍 524）。
`AlertsControlRoomMonitor` 原本**没有这个件**，本轮补上（取舍 523）。

**形状**：两个都按 `Initialize(config)` + `Refresh(state,config)` 的适配器惯例；
`ForecastPanel` 另有一个 `Step(dt)` 挂在 Heartbeat 上（与 `FacilityCascade` 并列），
因为它的边是亚秒级的 —— 公开函数，不是藏在连接里的活儿（§0.19）。

**验收**（Edit 模式，**不需要 Play**，取舍 526）：把源码拉成临时模块 require 起来，
11 个合成状态驱动警报格、逐帧驱动深扫，读回的全是**实例属性**
（27 个 `Frame.Visible`、`AnnouncementFrame.Visible`、`AnnouncementText.Text`/`TextColor3`、
三个 `Sound.Playing`、七台 `EFEFrame.Visible`）。读数见 `PROGRESS.md` Phase 125 第三节。
**没验的是**：Play 里点四个控制走进 `Running` 那条**真机**路 —— §0.16 的边界照旧，
这一轮验的是模块，不是跑起来的游戏。

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

### 2.26 `luau-windows/gui.py` 的 CORE MODEL —— 操作员自己的温度模型，2026-10-14 换成步进式（Phase 131）

**不是游戏的一部分**（承 §2.18）：它住在操作员桌面那个 tkinter 控制台里，
`luau-windows/calculation.py` / `.luau` 仍是压力模型的权威，`gui.py` 是它的观察窗口。
**这一节说的是窗口里那块 `CORE MODEL`**（Phase 126 起有，Phase 131 换成现在这个形状）：
一块**给桌面控制台自己用的**温度演化模型，让右列的 "Core state" 有东西可算。
**游戏本体一行未动** —— 引擎有自己的温度（`SSS.ReactorBackend.Engine`），两者互不引用。

**形状：`T' = T + baseFluc * press + noise(t)`，一条步进。** `T` 在等号右边 = 上一拍的温度，
由 `Sim` 携带；模型只决定**这一拍加多少**。Phase 126 那一版是闭式解
`T(x) = T_0 + (rate + noise(x)) * x`（每一拍从 `T_0` 重算），Phase 131 换成步进。

| 量 | 取值 | 来源 |
|---|---|---|
| `row` | `T < 5600 → 0`；`< 17500 → 1`；`< 29500 → 2`；否则 `3` | 三个数就是 `Config.Sim.State1/2/3`；行 0 那一档是他的式子没有的（冷机） |
| `ACTIVE[row]` | `0`, `(6.86, 65.5)`, `(7.24, 37.0)`, `(6.8, 534.0)` | 他对 LEVEL 1-5 实测日志的**线性拟合**，存成 (斜率, 截距) |
| `PASSIVE[row]` | `-455.7`, `-19.2`, `0`, `0` | 同上；行 0 那格逐字等于旧表的 `BASE_RATE[0]` |
| `a`（功率） | `level * 25`，即 PW1..PW5 = `25..125` | 单选按钮带的数就是它 |
| `press` | `p <= 11500 → 1`；`<= 27000 → 2`；否则 `4` | 他给的 `pMultiplier` |
| `noise(t)` | `15·level·sin(t/1.5) + 10·level·sin(t/0.7) + 5·level·sin(t/0.3)`，`level = a/25` | 他的三个正弦；加在**读数**上（Phase 126 那一版是加在**斜率**上） |

**六条边界是故意写死的，别去"平滑"它们**：

1. **`s+1` 是他的列表从 1 数起。** 按他的顺序写成 0-based 之后，下标**就是行号**，
   翻译那一步没了（取舍 556）。
2. **`< 17500` 与 `Engine.luau:320` 的 `> 17500` 差一度。** 引擎那一行是
   `T > State3 and 3 or (T > State2 and 2 or (T >= State1 and 1 or 0))` ——
   **上面两档是严格 `>`、底下一档是 `>=`**，而这里三档一律 `<`。
   于是正好 17500 在这里是行 2、在引擎里是行 1（29500 同理）；
   而 5600 两边一致（`>= 5600 → 1` 与 `< 5600 → 0` 是同一件事）。
   按**他给的拼法**实现，并把这一度写进注释与检查器 —— 两点在浮点上都是零测度，
   但两份拼法之间的静默漂移正是这个文件的注释存在的理由。
3. **行 0 他的式子到不了，但我们留着**：`ACTIVE[0] = 0` 且 `PASSIVE[0] = -455.7`，
   那一格是**量出来的数**，行单选按钮也是按这张表建的。
4. **`off`（level 0）不在他的拟合里**（他拟合的是 1..5），定义为**什么都不加** ——
   把 `a = 0` 代进那条线会得到 `+46.3`/拍（那是**截距**，不是激光）。
   因为振幅乘 `level`，0 档连抖动也归零，读数**逐字停住**（取舍 558）。
5. **`T_0` 和 `multiplier()` 删掉了**：步进式没有锚点，这两个量**不再有读者**，
   而摆在读数旁边会和模型的项逐字同形（取舍 559）。
6. **模型是 arm 上去的**（Phase 126 取舍 529）：不勾那一下，**一行都不跑**，
   读数显示 `-`（不是 0）。

**怎么验的**：`luau-windows/core_model_check.py` 是这份规格的**第二份拼写** ——
`his_active` / `his_passive` / `his_base_fluc` / `his_press` / `his_noise` / `his_temperature`
全部用**他给的字面量**，**不回头调 `gui.py`**（锚点不许自证，取舍 530）。
读数**从控件上读回来**（`screen()` 走 grid、解每个标签的 `textvariable`），不读模型内部。
**103 项 / 0 失败 / exit 0**；把 `noise` 挪回时钟上的突变点亮 **4 条**。
配方 `docs/SNIPPETS.md` §5.38，取舍 555..561，全文 `PROGRESS.md` Phase 131。
（Phase 135 把**同一份**检查器扩到 **154 项** —— 加的是三台 CBL bank、AVB 与失速那三块，
见 **§2.27**。）

### 2.27 `luau-windows/gui.py` 的三台 CBL bank、AVB 按钮与失速覆盖（Phase 135，2026-10-16）

**不是游戏的一部分**（承 §2.18 / §2.26）：这一段说的是**操作员桌面那台 tkinter 控制台**，
`luau-windows/calculation.py` / `.luau` 仍是压力模型的权威，`gui.py` 是它的观察窗口。
**游戏本体一行未动，Studio 里一个字节没推。**

来源：操作员的队列「**等会继续完善GUI然后三个激光分别控制，加个AVB按钮**」，
外加他贴来的两行规格（`pres <= 2200` 时 `fluc = -586`，自注"实测失速暴跌速率"）。

| 量 | 取值 | 来源 |
|---|---|---|
| `CBL_BANKS` | `3` | 游戏里三台 CBL 回路，逐台 `heat += level`（`Engine.luau:261-264`） |
| `CBL_UNIT` / `CBL_LEVELS` | `25`；`off / PW1..PW5 = 0/25/50/75/100/125` | 他的 `a = level * 25`；档位表就是他给的那张 |
| `CBL_START` | `50`（PW2 在第一台） | **换版之前那台控制台一直在用的档**，按数保住、不是按控件保住 |
| `Core.power` | **属性** = `sum(self.banks)` | 他拟合里的 `a`。三台满档 = 375，**远超拟合区间**（见下） |
| `STALL_FLUC` | `-586.0`/拍 | 他量的原始游戏；我们 remake 的 `Config.Sim.StallCooling` 是 750 |
| `AVB_PSI_DROP` | `3300.0` | wiki；**出厂日志 6 次点击里 4 次逐字 3300** |
| `AVB_STALLOUT_PSI` | `2200.0` | 他贴的那一行 |
| `AVB_COOLDOWN_TICKS` | `15` | wiki 的"约 25-26 秒，**或大约 15 个反应堆拍**"—— 两句话是同一时长在两台钟上（25.5/15 ≈ 1.7 秒/拍）；这台控制台走**每拍币种**，见下面第 3 条 |
| `AVB_NO_COOL_ABOVE` | `2200 + 3300 = 5500` | **推出来的**，不是抄的第三个常数 |

#### 三台 bank

`Core.banks` 是三元素列表，`power` 是一个**属性**而不是一个字段 ——
每个读者（`fluctuation`、`noise`、面板读数）拿到的是**同一个和**，
所以不存在"面板显示的和模型用的不是同一个数"这条路。
面板上**每台一行单选**（`CBL banks (a = the sum)` 那一框）：
游戏里 `PW1..PW5` 是**五档**，三台回路各选一档 —— 一行总控会是**一个反应堆没有的控件**。

#### AVB 按钮

`Sim.vent()` 是**一次性事件，不是每拍的一项**：wiki 说的是"按一下掉 3300"，
一个能一直按住的按钮是**另一个器件**。行为四条：

1. **冷却里按下去返回 `None`，压力一动不动，钟也不重起** ——
   重起的话后一次按键会把前一次还没走完的冷却重置，而那不是"等 15 拍"。
2. **压力在 0 上夹住**（引擎自己的最后一行也是 `math.max(0, ...)`），
   返回的是**真正移动了多少**，所以日志不会宣称一次压力没感觉到的落差。
3. 面板上按钮**变灰**、旁边一行字写 `ready` / `cooldown N`。
4. 三个读数：`stallout pres <= 2200`（这一拍会不会失速，**下一拍要门控的那个压力**）、
   `vent cooldown left (ticks)`、`vent last drop (PSI)`（**没按过显示 `-`**，
   免得一个 0 被读成"按了没用"）。

#### 失速覆盖：`step_terms()` 里那个次序

`step_terms(row, power, pressure, t)` 是**这条规则的唯一一个拼法**，
`Core.step`（真的加）和面板的"这一拍会加 X/拍"预告**调的是同一个函数** ——
两处拼法会让承诺和行为**无声地漂开**（§0.31 ①）。

**次序**：失速**盖过**行、盖过 CBL 档位、盖过压力乘数；**但不盖过噪声** ——
噪声的振幅自己乘 level，所以**三台全灭时它自己归零**，
于是"一台失速、三台全暗的反应堆**每拍正好掉 586**"是检查器能抓住他的一个数。
**"off 是我们加的、不是规格里的"那条规则在这里输给失速**：
把激光关掉**不会**让一个失速的腔体恢复，所以失速拍上 `actualFluc` 保持负数。

**"失速落在哪一拍"不需要判断**：`press_multiplier` 在 ≤11500 上一律回 1.0，
而失速只在 ≤2200 上开 —— 所以每个失速拍上 `baseFluc` 与 `actualFluc` **逐字相等**。
这是**能验的不变量**，不是一句"反正乘数是 1"。

#### 六条边界（故意写死的，别去"平滑"）

1. **`<=` 与 `Engine.luau:313` 的 `<` 差 1 PSI**（正好 2200 那一点）。
   **这一票现在是 2 比 1 对他**：我们的引擎用 `<`，而 **wiki 自己的原话**是
   "making chamber pressure reach **less than 2200 PSI**"。仍然按**他的写法**实现，
   理由是那一句是**写给这台控制台的规格**；浮点上零测度，写进注释和检查器，
   不许静默漂移（同 §2.26 第 2 条那一度的写法）。
2. **586 与 750 都不是错的**：586 是他量的**原始游戏**，750 是**我们这份 remake** 的配置。
   出厂日志那 6 次普通掉压的谷底是 **−538 .. −801**，**这个区间同时装得下 586 和 750，
   所以它不在这两个之间做选择**。这台控制台取 586 是因为**它是原始游戏的模型**（取舍 575）。
3. **冷却的"15 拍"与"26 秒"是两台钟上的同一个时长，不是分歧。**
   wiki 写的是"**a cooldown of about 25-26 seconds, or around 15 reactor ticks**" ——
   两句一起把反应堆拍定在 **1.7 秒**。这台控制台的钟是**操作员自己那份 `calculation.luau`**
   （`task.wait(1)`，`period` 那个格子就写着 "the .luau waits 1"），
   而模型里**其他每个每拍的数都是原始游戏的每拍值**（`FAN_DRAG = 60` = wiki 的
   "60 PSI of pressure **per core tick**"）—— 所以冷却走**同一个币种：15 拍**。
   我们那份 Config 的 `Cooldown = 26` 是同一个 ~26 秒在**它自己那台钟**（1 秒一步）上的说法。
   秒那一侧的佐证：日志六次按键的间隔是 **26 / 58 / 27 / 26 / 36 秒**，
   最小的 26 秒是日志能给的下界（取舍 **579**）。
4. **`AVB_NO_COOL_ABOVE` 不是第四条规则**：wiki 的"高于 5500 按下去不会冷却"
   说的正是**按键能达成的效果**（把压力送进失速），而 5500 就是这件事的上界。
   所以它是**推出来的**，检查器两侧都跑（从 5500 排气会失速、从 5501 不会）。
5. **已知简化：原版的冷却不是常数。** wiki 原话
   "**Based on the State, the button will take longer to refresh after use**, but will
   always reduce roughly the same amount of PSI" —— 所以这里的固定 15 拍是
   **一个状态相关数的状态 1 读数**，而 wiki **没有给每个状态的值**。
   写下来而不是抹平（`QUESTIONS.md`）。
4. **`vent()` 的返回值是"实际移动了多少"**，不是常数 3300。
5. **三台满档（a = 375）没有测量支持**：拟合跨 `a = 25..125`（**一台**的量程），
   375 是区间的 3 倍，那条线外推得正好，但**线性在外面还成立是拟合的假设** ——
   已标成外推并进 `QUESTIONS.md`（§0.21 第 3 条）。
6. **`a` 的拼法本身也在问**：游戏自己的 `heat += level` 再整体乘 `CBLHeat` 是**和**，
   日志里那个候选模型写的也是 `sumCBL * 65`，所以这里按**和**做 ——
   但"三个激光是对应三台回路还是五档旋钮"这一句话他没有说，同样进了 `QUESTIONS.md`。

#### 怎么验的

- `luau-windows/core_model_check.py`：**154 项 / 0 失败 / exit 0**（Phase 131 时是 103 项）。
  新加的覆盖：三个 bank 的读数与 `a total`、驱动到失速（开 6 台风机直到**屏幕**说 `STALLED`，
  然后 `actualFluc` 逐字 `-586`、`Temperature` 的前后差逐字等于 `gui.STALL_FLUC`）、
  `stalled(2200) / (2200.1) / (0)` 三个边界、AVB 一整节（5016 按掉 3300 → 1716、
  冷却 15、按钮变灰、**界面把为什么说出来**）、一次性那一节（第二次按被拒、
  压力不动、钟不重起）、15 拍冷却的整段循环、**涌现出来的 5500/5501 那一对**、
  以及从 1000 按下时在 0 上夹住。
- `luau-windows/core_model_mutants.py`：**11 条突变 / 0 条存活**，基线 154/0。
  它存在的理由是 §0.31 ①：**绿色的检查器本身不证明任何事** ——
  每条突变**点名**它必须弄红的那一条检查，锚点在写之前**先断言唯一**（§0.13），
  基线非绿就整趟作废（取舍 **578**）。
- `_tools/avb_from_log.py`：rc=0。它打出六个落差与失速区间，
  **所以这两个常数是可复现的读数，不是记住的数**。
- **没验的那一半**：全程没进 Studio / Play，没有人拿鼠标点过这台窗口，
  界面样子没有截过图、也没请谁评过（§4.4 那一半照旧没做）。

取舍 **574..578**，配方 `docs/SNIPPETS.md` §5.40，全文 `PROGRESS.md` Phase 135。

### 2.28 `luau-windows/gui.py` 的三台冷却泵（Isotope E，Phase 136，2026-10-16）

游戏的三条控制手段里的最后一条（`CLAUDE.md` §1.2：AVB / CBL / **Isotope E 冷却回路**）。
**三台泵、每台 0..3 档、每档每拍去掉 120 度**，加进桌面控制台。

**行为**

| 项 | 值 | 出处 |
|---|---|---|
| 每档每拍 | **120 度** | 出厂日志**读出**（见下）+ `Data/TRGWeb.luau:178` + 我们那份 `Config.Sim.PumpCooling` |
| 泵数 | **3** | `TRGWeb` 的 `coolant_pump1/2/3`、`Engine.luau:110` 逐台 `integer(value, 1, 3)` |
| 档位 | **0 / 1 / 2 / 3** | 同上（`increase` 夹 3、`decrease` 夹 0） |
| 起始 | **三台全 0** | 冷启动；这也是 `Engine` 的初值 |
| 落在算式的哪里 | `T' = T + baseFluc*pMultiplier + noise(t) - 120*Σp` | 见"三个选择" |
| 失速时 | **泵被压过**，这一拍的冷却当 0 | 保住"失速 + 全黑 = 恰好 586" |

**"三个选择"（`CLAUDE.md` §0.31 那个问句的三个答案，取舍 581）**

1. **它自己的加项**，不是喂进他拟合那条线的"负 `a`"。后者会**恰好在该起作用的时候
   静音泵** —— 那条线被"off 是咱们自己的规则"把着门，而激光黑着不是泵停转的理由。
   **否证在出厂日志里：84 条记录 `CBL sum 0` 而泵在 1/2/3 档。**
2. **在 `pMultiplier` 外面。** 三个来源没有一个给冷却挂压力因子，乘上去是发明一个数。
3. **失速仍然压过它。** `fluc = -586` 说的是一个塌了的堆芯，不管行、档、压力、泵。
   这保住了检查器**已有的**不变量，而不是把"586"悄悄变成"586 加一个泵项"。

**常数是量出来的，不是记住的** —— `_tools/coolant_from_log.py`（rc=0）

```
predDT * 5  ==  65*sum(cbl.level) - 120*sum(coolant.levels)
477 records, maximum |error| = 0.0
```

出厂日志每一拍记着原版**自己**算的 `predDT`，这条恒等式**在全部 477 条上误差恰好 0**，
**所以 65 和 120 是从一台跑着的游戏里读出来的，不是从源文件里抄的**。

**两条边界**（仪器自己印出来，不留给人猜）：

- **恒等式被三个拼法同时满足**（`level` / `level where active` / `coolant.sumLevel`
  都是 477/477），所以它**钉住常数、钉不住字段**；而 `sum(cbl.power)` **0/477 被否**
  （`power` 是另一个量：level 0 读 10、level 4 读 100，`level` 是索引）。取舍 **582**。
- **日志的"行为"那一半只部分支持它**：按 (C,K) 分组的每拍增量里，
  14 组非零中 **6 组**落在线的 100 度以内（游戏自己还加随机项）；
  中位数恰好 0 的四组是**开机之前**（`GameActive = false`，腔体没在被模拟）；
  **C3 K9** 读 −436 对线 −885，是**终局崩塌**那一套状态。
  唯一一对同 C 的（C15：K0→K3 = 960→670）**给出 −96.7/档**而不是 −120，
  但**两段的漂移在里面**，所以那次是**一致的读数**，不是第二次测量。
  **朴素回归在这份日志上读 LOW**（`52.68·C − 91.64·K − 6.55`）——
  录像采得比游戏拍密，**逐样本差分把回归衰减掉了**；能给出 120 的是那条恒等式。

**一条已知分歧（`QUESTIONS.md` R11）**：他拟合的热线大约是原版每档 65 的 **2.6 倍**
（`ACTIVE[row][0]` = 6.8..7.24 每单位 `a` vs 65/25 = 2.6，行 1 之比 **2.638**）。
于是**在这台控制台的币种里，一档泵买到的东西比原版的热/冷比少**：

| | 原版 | 这台控制台 |
|---|---|---|
| 九档泵 = 1080 度/拍 | **大于**最大激光热（65×15 = **975**） | 行 1 三台满档 = **41.2%**（行 2 **39.2%**、行 3 **35.0%**），压力倍数之前 |

**常数取量出来的那个，算术不为遮它而改。**

**判定**：`luau-windows/core_model_check.py` **168 项 / 0 失败**，
`luau-windows/core_model_mutants.py` **17 条 / 0 条存活或红错**。
两个坑在取数那一侧，都不是模型错：**① 地址里嵌着被测的数**
（那一条突变 `KeyError: 'cooling  -120 x K'`，因为读数的**键**是常数拼的 ——
值可以进检查的正文、不能进检查的地址，取舍 **583**）；
**② 屏上取整过的数不能比未取整的浮点**（三条检查红的错在检查器自己）。

**没验的那一半**：全程没进 Studio / Play / 上传；**界面没有截过图、也没请谁评过**；
"三个泵分别控制"是**我按字面读的**（游戏自己的 `Engine.luau:110` 与 `TRGWeb` 的
三个独立变量与之一致，日志里逐台档位 `0 x696, 1 x489, 2 x11, 3 x235`
说明三台**真的被分开拨过** —— 但这一条是我读出来的）。

取舍 **581..583**，配方 `docs/SNIPPETS.md` §5.41，全文 `PROGRESS.md` Phase 136。

### 2.29 `luau-windows/gui.py` 的核心模型：**修正后**（Phase 137，2026-10-16）

操作员贴来一条以 **`Correction:`** 开头的规格，改掉 Phase 135/136 落进这台桌面控制台的
三处读法。**游戏本体一行代码没动、Studio 里一个字节都没推、没进 Play。**
（这台控制台模拟的是**原版**，不是我们那份 remake；两条线的分歧照旧记在 `QUESTIONS.md`。）

**三处改动**

| # | 项 | 改之前 | 改之后 | 落在哪 |
|---|---|---|---|---|
| ① | 激光台 | `a = c1+c2+c3`（三台**和**，最大 **375**） | `a_avg = ((c1+c2+c3)/3)*25`（**平均**，最大 **125**） | `Core.power`；`fluctuation` 与 `noise` 都吃它 |
| ② | 冷却 | `120 × (p1+p2+p3)`（**和**，最大 **1080**/拍） | `((p1+p2+p3)/3) × 120`（**平均**，最大 **360**/拍） | `Core.cooling` |
| ③ | 失速 | `fluc = -586` 是**速率**，读数上还骑着噪声 | `dT` **整条**换成 −586（没有热、没有泵、没有抖动） | `step_terms` 的失速分支 |

`p_mult` 的三段（`<= 11500 → 1` / `<= 27000 → 2` / 其余 `4`）、`noise` 的三个振幅与周期
（15@1.5 / 10@0.7 / 5@0.3，都按 `a_avg/25` 缩放）、四条行线（`ACTIVE` / `PASSIVE`）**一个字没动**，
只换了喂进去的那个 `a`。

**①② 都是"把同一个和除以 3"，于是这台控制台的两条控制手段同时缩到三分之一：**

| 三台满档时 | 改之前（和） | 改之后（平均） |
|---|---|---|
| 冷却 | `120 × 9 = 1080` /拍 | `120 × 3 = 360` /拍 |
| `a` | `375` | `125` |
| 行 1 的热（三台满档） | `6.86×375 + 65.5 − 19.2 = 2618.8` | `6.86×125 + 65.5 − 19.2 = 903.8` |
| 冷却占那行热的比 | **41.2%** | **39.8%**（行 2 **38.2%**、行 3 **26.0%**） |

**占比几乎没动**（热量那侧一起缩了），**绝对量是三分之一** —— `120` 这个常数没变，
**变的是它乘的东西**（三台的和 → 一台平均值）。这些数写在 `gui.py` 的 KNOWN DIVERGENCE 段落里。

**`t = 1` 那个算例（他的算例，驱动出来再逐项从屏幕上读回）**

| 项 | 他写的 | 屏上取整 | 模型算出来 |
|---|---|---|---|
| `a_avg` | `((5+3+1)/3)*25` | `75` | `75.0` |
| 行（`T = 12000`） | `s+1 = 1` | `1` | — |
| `base_heat` | `6.86*75 + 65.5 − 19.2` | `561` | `560.8` |
| `p_mult`（`P = 8000`） | `1` | `1` | `1.0` |
| `coolant_effect` | `((2+2+2)/3)*120` | `240` | `240.0` |
| `noise(1)` | 三条正弦 | `55` | `54.665213986169604` |
| `dT` | `561 − 240 + 54.665…` | `375` | `375.46521398616954` |
| `T_next` | `12000 + dT` | `12375` | `12375.46521398617` |

**"平均"这件事有两份拼写，而它们逐位相同**：`his_a_avg` 是**先加档位、再除 3、再乘 25**，
`Core.power` 是**先除 25（变档位）、再取平均、再乘 25** —— 每一档都是整数、25 精确可表示，
所以这是**同一个算术的两种拼法**，不是"差不多"。
（同一天量到一处**不**逐位相同的地方：`gui.noise` 与手写那份差 **7.10543e-15**，
原因**不在模型**，见下面判定那一段与取舍 **585**。）

**行 0 的门限：规格追上了代码，行为一个字没变。** 修正那条规则第一次写出 `T < 5600: 0`
（在那之前规格从 17500 起，**行 0 是这台控制台自己补的** —— `PASSIVE[0] = -455.7` 就是旧的
`BASE_RATE[0]`，是个量出来的数；而且行单选按钮是从表里长出来的，所以一条温度到不了的规则
会生出一个按不动的按钮）。`5600` **早就躺在文件里**：`STATE_MIN`（`Config.Sim.State1`、
`Engine.luau:320` 的 `T >= 5600 and 1 or 0`）。
判定因此是**拿它跟 `STATE_MIN` 比**，不是在校验器里再写一遍 5600 ——
**两种拼法给出同一个数 = 一个读数、不是巧合**；以后任一边改了，是红，不是一句传闻。

**`a = 375` 那条外推自己消解了**（`QUESTIONS.md` R9 ②）。拟合跨 `a = 25..125`；
改之前三台满档是 `375`，也就是区间的 **3 倍**，按外推对待。平均之后三台满档**恰好是 125**
—— 不是封了顶，是**够不到那条线外面**。判定里因此有"任何控件位置都到不了 125 以上"这一条。

**失速那一格见 `QUESTIONS.md` R12。** 他的修正是 `dT = {P<=2200: -586, …}` ——
**整条 `dT` 被 −586 取代**，而 Phase 135 那两行写的是 `fluc`（速率），读数上还骑着噪声。
两种读法**只在激光亮着时分开**：激光全暗时 `noise` 的振幅本身就是 0（它按 `a_avg/25` 缩放），
**两边逐字相同** —— 所以"激光全暗那一拍"**分不出**这两种读法。
判定因此**把三台激光全推到 PW5 再踩进失速**，并印出那条余量：
**那一拍两种读法差约 `44.24123751141943` 度**，而他的字面是"差 0"。

**判定**：`luau-windows/core_model_check.py` **201 项 / 0 失败**（改前 168），
`luau-windows/core_model_mutants.py` **23 条 / 0 条存活或红错**（改前 17）。
**这一轮最值得记的是检查器自己的四个缺陷** —— 四个都是**绿着的错尺子**
（取舍 **585..588**；而"一条修正该问什么"是 **584**）：

1. **用他的算例写的"不是任何一台"永远绿。** `c = 5/3/1` 的均值**恰好是中间那一项**
   （3 档 = 75）—— 算术三元组的性质。于是 `a_avg = 75` 与"读了第二台"**逐字相同**。
   换成**非对称**的 `125 / 50 / 0`（`a_avg = 58.33`，不是任何一台的数）才有牙。
2. **两份拼写差 `7.10543e-15`** —— 原因不在模型：**CPython 3.12+ 的 `sum()` 对浮点是补偿和**
   （Neumaier），它落在比 `a + b + c` 更接近真值的位置。那一处开了一个**写明了理由的容差**
   （`check_close(…, 1e-12)`，并把量到的差打在同一行），**其余全部仍然要求逐位相同**；
   量到的差比那条检查要抓的最小东西（换两个振幅 ≈ 2.4 度）小十二个数量级。
3. **一条断言站错了位置。**「泵一开始是关着的」坐在**已经动过泵**的那一节后面而红了 ——
   因为 `Console.reset()` **是开始一次运行，不是复位面板**（它不碰激光和泵的单选按钮）。
   它红的**不是因为控制台改了**，是因为它测的是**控件的默认值**。
4. **突变器自己写错了一条**：条件写进了 `base` 槽而不是 `actual` 槽 → 那个突变什么都没改到
   → 0 红 → 被 runner 报成 `HOLE`。**`HOLE` 不只可能是"检查没牙"，也可能是"突变没牙"**，
   而这两种洞的**修法方向相反**。

**没验的那一半**：全程没进 Studio / Play / 上传；**窗口没有截过图、也没请谁评过好不好用**；
**界面一个控件没动**（同一批单选按钮），变的是模型吃它们的方式 —— "看着变了吗"的答案是"没变"，
这不是漏验；他这条修正**没有在游戏本体上验证过**（两条线）；
**R11 那条分歧没有解决、反而放大了三倍**（三台满泵：360 vs 原版 1080）。

取舍 **584..588**，配方 `docs/SNIPPETS.md` §5.42，全文 `PROGRESS.md` Phase 137。

### 2.30 冷却**收回平均**：泵回到求和（Phase 138，2026-10-16）

操作员一句话：「**冷却别用平均，重写写一下**」。§2.29 那条 `Correction:` 里的**两个平均**，
他只收回了**泵**那一个；`a_avg`（三个激光的平均）和"失速吞掉整条 `dT`"**一个字没动**。

| | §2.29 落地时（平均） | 现在（求和） |
|---|---|---|
| 算式 | `coolant_effect = ((p1+p2+p3)/3) × 120` | **`coolant_effect = (p1+p2+p3) × 120`** |
| 三台满档 | **360** /拍 | **1080** /拍 |
| 一号泵上 1 档 | 40 /拍 | **120** /拍 |
| 代码里 | `coolant_avg = sum(pumps)/3`，再 `× 120` | `return sum(self.pumps) * COOLANT_PER_LEVEL` |

`120` **一个字没改**；改的是**它乘的东西**（一台平均值 → 三台之和）。三处来源写的都是求和
（`Data/TRGWeb.luau:178`、我们那份 `Config.Sim.PumpCooling`、出厂日志 477/477 最大误差 0 的
恒等式 `predDT*5 == 65*sum(cbl.level) - 120*sum(coolant.levels)`），
所以这一改是**模型和它自己的证据重新对上**，不是新数。

**他的算例随之换尾**（`c = 5/3/1, p = 2/2/2, T = 12000, P = 8000, t = 1`，前五项一个字没动）：

| 项 | 他写的（平均） | 现在（求和） |
|---|---|---|
| `coolant_effect` | 240 | **720** |
| `dT` | 375.465…（屏上 375） | **−104.53478601383044**（屏上 **−105**） |
| `T'` | 12375 | **11895** |

他的 240 / 375 / 12375 **属于另一个读数**，而那句话已经把那个读数收回了。
三条都留在检查器里，但**只有 720 是断言**："240 正是 720 的三分之一"是**打出来的**
（一条永远不会红的检查是噪音，§0.31 ①）。

**R11 的冷却那一半没有了**：常数对、单位对、三处来源全部对上。剩下的是热那一侧：

| 行（三台满档 = `a_avg` 125） | 三台满档的热 | 满泵 1080 的占比 | 原版自己 |
|---|---|---|---|
| 行 1 | **903.8** | **119.5%**（**泵赢**） | 1080 对 975 = 110.8%（泵赢） |
| 行 2 | **942** | **114.6%**（**泵赢**） | 同上 |
| 行 3 | **1384** | **78.0%**（**热赢**） | ——（`+534` 这一项不吃 `a`） |

三个热值都是**检查器自己用他的字面量算出来打印的**。于是
**"原版九档泵（1080）压得过它自己的最大激光热（975）"这条性质，这台控制台现在也有了** ——
同一个数压过同一量级的热。R11 的 **B 选项（把泵折算成 317/档）因此退休，没有做任何折算**；
**C 选项（回头查热线本身偏不偏大）照旧挂着**。压力倍数一上来（11500 以上 ×2、27000 以上 ×4）
热就反超，而**冷却从不被乘**（有一条突变专治这个）。

**三个字符串跟着模型动了**（`LabelFrame` 标题 / 读数行标签 / `on_coolant` 的日志行），
而**它们一条检查都读不到**，且**读不到是故意的**：检查器按**前缀**取那个读数
（标签里嵌着常数 `120`，常数一动**取数先崩**而不是断言红，取舍 583）。
所以"标题说平均、算式在求和"在盘上**不会红**，防线只有改完 grep。

判定 `core_model_check.py` **201 项 / 0 失败**、`core_model_mutants.py` **23 条 / 0 条存活或红错**；
新增/改名的那条突变是"把求和又除以三"（**回到被收回的那个读数**，而不是回到最早的）。
**没有一条检查被删、也没有一条被改绿** —— 换的是泵那两条的锚点与去红的检查名。

取舍 **589..593**，配方 `docs/SNIPPETS.md` §5.43，全文 `PROGRESS.md` Phase 138。

### 2.31 冷却**又要平均**：泵那一行一天里的第四次（Phase 139，2026-10-16）

> **更正（Phase 139）**：上面 §2.30 那段写的是**求和那天**的读数（满泵 1080、
> "冷却那一侧的分歧回到零"）。**那一整段随之作废**，原文不改，见本节。

操作员原话：「**算了冷却计算还是平均吧**」。这是同一条行一天里的第四次：

| Phase | 泵那一行 | 满档（三台都上到 3） |
|---|---|---|
| 136 | `Σp × 120`（这台控制台自己对三处来源的读法，**没有他一个字**） | 1080 |
| 137 | `(Σp / 3) × 120`（他那条 `Correction:`） | 360 |
| 138 | `Σp × 120`（「冷却别用平均」） | 1080 |
| **139** | **`(Σp / 3) × 120`**（「算了还是平均吧」，**逐字等于 Phase 137**） | **360** |

**动的只有泵那一行。** 激光 `a_avg`（三台的**平均**，满档 125）本来就是平均，没动；
失速那条分支（`dT` 整条换成 −586）也没动。
`120` 这个常数**一个字没改** —— 改的始终是**它乘的东西**。

```python
    @property
    def cooling(self):
        coolant_avg = sum(self.pumps) / float(COOLANT_PUMPS)
        return coolant_avg * COOLANT_PER_LEVEL
```

**三处来源的算术全部写的是求和**（原版原型 `Data/TRGWeb.luau:178`、
我们那份 `Config.Sim.PumpCooling = 120`、出厂日志 477/477 最大误差 0.0 的恒等式），
**而这一行是唯一不听它们的那一行** —— 它已经被拨过去拨回来过。
所以 `gui.py` 那段注释带着**全部四个阶段**，而不只是"现在是什么"（取舍 **594**）。

**给操作员看的三个字符串也跟着翻回去了**（`LabelFrame` 标题 → `mean level /tick`、
读数行 → `cooling  -%g x mean(p1..p3)`、`on_coolant` 日志行 → `(mean %g; -%g/tick)`）。
**这三处一条检查都读不到，而且读不到是故意的** —— 检查器按**前缀**取那个读数
（标签里嵌着常数，常数一动取数先崩，取舍 583）。防线只有**改完 grep**（取舍 **595**）。

**R11 回到"两个选项"**：360 对三台满档激光的热 903.8 / 942 / 1384 =
**39.8% / 38.2% / 26.0%**（原版自己的同一条是 1080 对 975 = **110.8%**），
所以 **B（把泵折算成 317/档）复活**，A 是我按的，C 照旧挂着（取舍 **599**）。

**判定** `core_model_check.py` **201 项 / 0 失败**、`core_model_mutants.py`
**23 条 / 0 存活或红错**（连跑三次相同）。**没有一条检查被删或被改绿**，
换的是泵那两条突变的锚点与它们去红的检查名。

**本轮还修了量它的那把尺子**：突变器报过一次**间歇性 `HOLE`**，真因是
**同长度、同一秒写下的 `gui.py` 让 CPython 复用了上一趟的 `.pyc`**，
于是突变根本没跑、而它报出来是"检查没有牙"（**方向逐字相反**）。
修法是检查器一律 `-B` 跑 + 把"没有字节码缓存"**读回来**（取舍 **596/597**），
配方 `docs/SNIPPETS.md` **§5.44**。

取舍 **594..599**，配方 `docs/SNIPPETS.md` §5.44，全文 `PROGRESS.md` Phase 139。
**没进 Studio（除了那 12 个文字）、没进 Play、没上传、没有窗口出现在他屏幕上。**
