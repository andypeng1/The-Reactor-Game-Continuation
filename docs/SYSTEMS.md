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


