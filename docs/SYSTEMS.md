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
| **规格来源** | `asstes/music/ReactorStartup.mp3`（别人的母带，**gitignored、不进仓库**）——`make_song.TARGET` 里每个数都是**对它测出来的**（`analyze.py` → `.report.txt`），**旋律一个音都没转录** |
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
