# CLAUDE §3 待办事项 / 下一步计划

> 磁盘专属前言 —— 不属于游戏内的 `CLAUDE` ModuleScript，校验脚本按「第一个 `## ` 之前
> 整段丢掉」剥掉，长度写死在 `_tools/verify_docs.py` 里。
>
> 本文是从 `CLAUDE.md` 拆出来的 **§3 待办事项 / 下一步计划**。权威副本仍然是游戏里的
> `game.ServerScriptService.GameCore.CLAUDE`，改完同一步镜像回模块。
> `CLAUDE.md` 只留每轮都要看的章节；拆的理由与分工见它开头的 §0.0。

## 3. 待办事项 / 下一步计划

### 3.1 几何体重做（**已撤销** —— 用户 2026-09-26「不需要重做建模，请删除」）
用户原话：「哎算了你整个游戏重新建模把我看不下去了」+「全部重做，特效与图片资产可使用」
后续指令：「控制室难道不重做吗？所有东西都要重做哦」

**已完成：**
- [x] 灯光大修 + AI 材质（见 2.8）
- [x] 控制台几何体：倒角、凹槽、**内嵌式按钮** —— 六张台，66 控件 / **957 件**
      （1024 是 HDEF 机柜改写前的数字，见 `DECISIONS` 43）
- [x] `SurfaceGui` **真实文字标签** —— Mk2 上的文字是从原版读回来的真字符串
- [x] **圆按钮改为平放**（用户报告）—— 两个按钮构建器各绕 Z 滚 90 度，六张台统一
      （`DECISIONS` 55 / 56）
- [x] **整机就位** —— 六张 Mk2 已搬进 `Workspace.Consoles` 并沿用原版台子的名字。
      **注意：`Workspace.Rebuild.Originals` 现在已不存在**，原版台子那一次的停放位置
      没了；要回退只能靠 `ServerStorage.GameCoreBaseline` 与 Mk2 的构建代码 `RebuildKit`
- [x] **七台监视器就地重建** —— 亮轨 + 深色壳带 + 四角支架 + 螺栓 + 底沿 + 各自铭牌（Phase 20c）
- [x] **Log / Forecast 屏接上** —— 纯观察者，仿真零改动（Phase 20d）
- [x] **三台 CBL 激光翻新**（`NIGHT_LOG` Task A）—— `Rebuild.LaserKit`，
      `Workspace.ReactorCBLs.Reactor_Laser_Mk3_1/2/3` 每台 +106 件（2,763 → 2,869）。
      **是翻新不是重建**：每台带 210 个 MeshPart / 100 个 UnionOperation /
      485 个 Wedge / 251 个活的 Texture·Decal，没有程序化替代品，按 §1.4 不能删。
      原机 103 种颜色**全是灰**、零自发光 —— 毛病在配色不在结构，所以只改
      `Color` 并增件：名字、标签、ClickDetector 一个没动。
      半径由 `SurfaceScanner` **射线**测得（不是对部件表取统计量，见 `DECISIONS` 78）；
      新增 7 站点配色、黄铜箍 + 螺栓圈、青色嵌条、状态灯、枪口发光环 + 镜片。
      幂等已验证（连跑两遍颜色逐字节相同），实机三台 0.34 秒跑完。
      **注意：`NIGHT_LOG` 里记的激光尺寸（98.0 × 36.7 × 36.7，Mk3_1 在
      (−61.4, 280.6, −0.7)）是错的**，实测轴向跨度 −57.72..+20.00、壳半径 4.78–8.08。
- [x] **三台 CBL 激光二次重做**（`PROGRESS` Phase 39 / `DECISIONS` 108-110）—— `Rebuild.LaserFrame`，
      **加件不换壳**：每台 +125 件（肋 56 / 螺栓 28 / 侧轨 8 / 风管 8 / 灯带 8 / 危险条 16 / 铭牌 1）
      外加 4 个 `PointLight` 和 1 个 `SurfaceGui`（`CBL-1/2/3`），全部落在新建的 `Mk2Frame` 文件夹里。
      **为什么不重建外壳**：每台 2,655 件作者手打的壳（210 MeshPart / 100 Union / 485 Wedge /
      251 个活 Texture·Decal）没有程序化替代品，按 §1.4 不能删；而拿一个素箱子盖住细节机是**更差**的
      轮廓，只是又多一种风格。第一次翻新（`LaserKit`）只改颜色，**桶还是圆的**，跟控制室里方正、
      带黄铜箍的 Mk2 台子并排就是别扭 —— 这一轮把方正的观感做在**外壳之外的框架**上。
      半径全部**射线实测**（肋角落在实测壳面外 1.70）；**8 点扫描改 16 点**抓到了真问题：
      肋 7 从 9.78 跳到 10.52，通风凸包正好落在 22.5° 的采样盲区里。
      线圈舱与枪口舱**故意不上侧轨**（12.7 studs 的站点拉直线要半径 14，会读成一个圈），
      而且这条由**测试强制**而非靠注释：中段射线超过端头 1.00 就拒绝该舱。
      幂等、可逆（`DeleteFrame` / `RevertAll`）；名字、标签、`ClickDetector` 一个没动，
      全部 `CanCollide/CanQuery/CanTouch = false`。

**未开始：**
- [x] **控制台二次重做（含冷却液校准）** —— **已完成**（`PROGRESS` Phase 40 / `DECISIONS` 115-121）。
      用户 2026-09-23 指定：排在 CBL 二次重做之后、其余任务之前。Mk2 台子被评价「太丑」，
      而**冷却液校准**（`coolant_recalibrate`，Wiki 记该传感器设备「有不可靠的倾向」、
      需要「手动干预校准」）**本来连灯都是死的** —— `lampState` 里根本没有这个动作，
      `applyLamp` 直接 early-return，那盏灯永远停在作者配的颜色上。
      **量出来的起点**：`ORIG_MainReactorConsole` 有 **113 件恰好 20.00 度**绕 Z 的部件、
      贯穿整张台子 —— 那才是六张台并排时「看着别扭」的真正来源，而 **Main 正是最平的一张**。
      给 Main 补了 **1.55 深的斜面寄存器**（`RegPlate`/`RegRim`/`RegWell` + `RegSkirt` + 危险条），
      七个控件用**一次刚性重挂**（`P * (A^-1 * pose)`）站到斜面上，台子高度对外零变化（6.250）。
      **第一版把 20 度做成了 40 度**（`P` 自带 rake 又乘了一次）：装机成功、高度对得上、
      七个 dot-path 全部解析、截图看着也像那么回事，**只有量角度能发现**（`DECISIONS` 117）。
      冷却液那盏灯**按 `atmosphere_vent` 的先例加了分支**（冷却中 `spent`、冷却完 `ready`，
      **故意不加 `STATES` 条目**）—— 但 **Phase 42 实测这个分支从来没有执行过**：
      `ConsoleBinder` 先按 `coolant_pump_on` 把同一组 `Light1/2/3.NeonPart` 认领了，
      而 `Bind` 的升级路径只在原 action 为 nil 时才生效，于是**没有任何部件绑在
      `coolant_recalibrate` 上**，那一段是死代码。更糟的是按一次会把那三盏灯**永久留在闪烁色**
      （`PULSE_COLOR` = `90,255,120`）：上面那句「`applyLamp` 直接 early-return」不只是灯不亮 ——
      它同时是**唯一清掉闪烁的地方**，所以 early-return 等于把闪烁色钉死。
      **两半都已修**（`applyLamp` 回落到 `entry.base`，且只在真的变色时写入）并**已验证** ——
      一次真点击记录到的色变序列是
      `(235,235,235) → (90,255,120) → (235,235,235)`，间隔 0.71 秒。见 `DECISIONS` 124。
      `HDEFGenerator` **故意不动** —— 它是机柜不是台子。
- [x] **监视器屏幕内容的暗底 + 亮绿标题条**（`ART_DIRECTION` §3.5）—— **已完成**
      （`PROGRESS` Phase 36 / `DECISIONS` 104、105）。七个 `Screen` 由 Neon `17,17,17`
      改为 `10,22,48`（同亮度，只动蓝通道 —— 那层「Neon 近黑」正是 §3.5 记的那笔绕路，
      与规格里的暗底是**同一个部件**，所以一笔改动同时结清两项）。每个 `MainMonitorFrame`
      新增 `GameCoreTitleBar`（`120,255,140`，ZIndex 0，**横跨整个 frame**），顶层
      `TitleText` 挖空成底色。**宽度取 frame、只有高度取 title** —— `TitleText` 是
      AutomaticSize，按文字宽度走的条在 380px 小屏上接近满宽、在 1045–1220px 大屏上只有
      30%，同一条规则两种外观；第一版还继承了 title 的 AnchorPoint，居中的那条会把满宽
      条推出去一半。**没有动的两处都是量出来的**：`PowerNeon` 是电源灯不是色带；Power 台
      嵌套的 `CBL<i>Frame.TitleText` 每 tick 被 `MonitorService` 重写，静态改色会被覆盖
      却看着像生效。回滚：`Rebuild.MonitorKit.Revert()`。
- [x] **控制室外壳 —— 修正而非重建**（`PROGRESS` Phase 30 / `DECISIONS` 85）——
      `Rebuild.ShellKit`，**新建 0 件**。原计划是四面墙 182 件板/肋 + 天花板压顶 + 凹槽，
      被它自己的碰撞审计推翻（`HARD=0 SOFT=713`）：四面墙**本来就做满了** ——
      东墙 = `Union 40.1×21.25×0.75` 底板 + 10 片 0.125 薄竖板 + 4 根通高肋；
      南北墙 = 下部板场 + 上部大板 + `0.2×13.25` 竖格栅；西侧 `FrontWall`
      **根本没有整片墙面**，是跨进房间 15 studs 的管道井。
      而且那 182 件里有 2 件会埋掉一个摄像头 `TextPart`（(141.80, 295.85, −0.71)）。
      **真正的缺陷**：天花板板与 16 件墙件戴着 `DiamondPlate` + `FacilityFloorPlate`
      （**地板自己的材质和 variant**）@160，`FrontWall` 另有 13 件 @205 ——
      全都**亮过控制台 hull 的 108**，于是家具成了亮墙上的暗块。
      房间本来就有 `100/75/60/50` 阶梯（1,379 件里 702 件在 100）。
      改：重着色 80 + 换材质 25，失败 0，**27 件灯具/信号灯全保**，壳面最亮大面降到 **100**。
      **差点改坏的**：第一版判据是「亮度 > 120」，干跑显示它会**把 25 件灯板和 2 盏琥珀信号灯
      改成灰色** —— 判据因此从「亮度」换成「材质 variant」：戴 `FacilitySteelPanel` /
      `FacilityFloorPlate` 的是结构，没戴 variant 的是灯具，一律不碰。
      纯外观属性，未增删改移任何部件；`ControlRoom` 下 ClickDetector = 0。
- **（已撤销的待办，2026-09-26）** 设施外壳 / 房间内部 —— **控制室已完成；反应堆舱已实测，无需改动**
      （`PROGRESS` Phase 31 / `DECISIONS` 86）。原先这里挂着「剩下的不是修正而是装饰 + 英雄资产」
      作为后续任务；用户 2026-09-26 明确「不需要重做建模，请删除」，**该任务已删**，
      下面保留的是那一次实测的记录本身。
      实测结论：舱壁那 230 件 `200,205`（全场最亮大面族，378,704 studs²）**不是离群值**
      —— 该子树的**完整**非 Neon 色调阶梯是 **0 → 255 连续分布，众数就在 192–207（1,040/4,079）**，
      上方还有 229 件在 240–255。**那次误判的根因是只统计大面（face ≥ 300）**
      —— 大面统计 ≠ 房间色调：舱里 1,138 件 190–223 的非 Neon 件有 980 件**就是墙本身**，
      过滤掉小件等于把墙留在一个被抽空的分布里看。**口径决定结论。**
      三条独立复核：>223 的 269 件总面积仅 2,044 studs²（占墙族 0.5%），
      **face ≥ 300 的 0 件**；墙子树里的 267 件 `FacilityFloorPlate` + 12 件亮 `Concrete`
      **全是竖直薄条**（thin 0.1–0.2），是装饰嵌条；`Mainframe` 那 2,405 件亮件是
      `Line` 1,421 + `TextPart` 776 + 白风扇，共 7,719 studs²。
      **判据本身也记一笔**：按「色调距离」找离群是错的仪器 —— 它把 `CullFolder` 里
      「舱壁 vs 控制室新壳」报成 55 件离群；真正管用的是**材料角色错配**，而第七轮那个
      「地板材质+variant 装在天花板」的全场复测**无复发**。
      **本轮零场景写入**，也**故意没写 kit**（一个 scan 报「无需修正」的 kit 是负债）。
      `MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` 仍是原版（实测为灯具/监视器装置，非建筑外壳）。
- **（已删除的待办，2026-09-26）** ~~英雄资产用 `generate_mesh` 重做：堆芯外壳、拉杆握把~~ —— 用户撤销。
- [x] **常态氛围 VFX —— 本来就有，不是缺失项**（`DECISIONS` 83、`PROGRESS` Phase 28）。
      实测 **278 个发射器 `Enabled` 且 `Rate > 0`**（`CullFolder` 外 **258 个**），主力 `Smoke` ×105。
      本轮真正修的是**两个永远画不出来的**：`Texture` 写成裸 id `6422188442'`（缺前缀 + 多一个撇号），
      已规范成 `rbxassetid://6422188442`，`MALFORMED` 归零。
      **剩下的不是造层，是贴图权限 + 观感。**
- [x] **竖直红 LED 条形图**（`ART_DIRECTION` §3.4）—— **已完成**（`DECISIONS` 69、
      `PROGRESS` Phase 21a）。五张台各两条 9 段竖列，共 **+120 件**（24 × 5）。
      纯装饰、不驱动 —— 没有任何部件以控件命名，`ConsoleBinder` 不解析它，
      `ControlVisuals` 不看它，28 条 dot-path 一条没变。
- [~] 材质分区的细化 —— **一致性已补齐，启发式本身仍待细化**（`DECISIONS` 84、
      `PROGRESS` Phase 29）。已做：把遍扫漏掉的 3,545 件补齐，三种材质现在
      **未打标 = 0**（`FacilitySteelPanel` 48,983 / `FacilityFloorPlate` 9,103 /
      `ReactorWallPlate` 46,951）。**未做：按几何角色重新分区。**
      顺手量了可行性 —— 对 `Facility`/`Geometry`/`CullFolder`/`Mainframe`/
      `MovingParts`/`ChamberWalls` 共 70,871 件按形状分类，结果是
      **FLOOR 9,797 / WALL 430 / CHUNK 60,644**：房间绝大部分是「块状」几何，
      **纯形状启发式没有多少可分配的空间**。真要细分得按「容器意图 + 形状」
      混合判定，而不是只看形状 —— 另外 `MovingParts`（9,206 件 `ReactorWallPlate`）
      与 `Mainframe`（14,016 件 `FacilitySteelPanel`）同属机械却拿了两种皮，
      这是按容器名分配的遗留不一致，**留待下一轮**。
- [x] **整体调子转向更暗**（`ART_DIRECTION` §2.1）—— **已完成，且不再是「需用户确认」**
      （`DECISIONS` 66、`PROGRESS` Phase 21c）。原先按 `DECISIONS` 52 押后到外壳阶段，
      后来还是做了一次「偏暗」实验，用户看过后说**「保留这版」**，于是直接成为基线。
      **§2.8 顶部那张更正表就是现在的实际值**，尤其是 `EnvironmentSpecularScale` 0.8 → **0.15**
      —— 那不是审美，是 §2.8/§5.5 记的「Metal 全渲染成白色」的**修复**。
      `DECISIONS` 52 的红线仍然有效：**控制台不得与环境脱节。**
      **七台监视器已在新调色下复核完毕**（`PROGRESS` Phase 25 / `DECISIONS` 80）：
      决定性的一步是把 Metal 壳带与 Plastic 亮边**设成同一个 albedo 75,75,76** 再截图 ——
      壳带回深灰、同框的天花板灯板纯白。旧调色下两者都会过曝成白。`Screen` 保持 Neon 17,17,17。
- [x] **主监视器示意图接上实时数据**（`PROGRESS` Phase 26 / `DECISIONS` 81）—— 两条能量柱
      （堆芯强度 / P.E.A 抽取）、三支 CBL 光束、三个冷却泵方块、核心辉光、P.E.A 警告三角，
      Equinox 期间整块转紫。纯观察者，不写 `GameState`；折进 `MonitorService` 而**不**注册为第 26 个系统。

- [x] **堆芯随堆芯状态变色（`ART_DIRECTION` §3.6）** —— `PROGRESS` Phase 35 / `DECISIONS` 101-103。
      `Rebuild.CoreKit.Glow` 把 57 个 Neon 件与 CORE 点光的色相随四个堆芯状态从青转到紫；
      驱动在 `ControlVisuals.driveCore()`（折进已有系统，不新增第 26 个系统）。
      纯观察者，只写颜色；**severity 0 时逐字节等于设计色**（HSV 往返守卫，`DECISIONS` 103）。
      踩过的坑记在 §0.13。两个端点都已渲染确认（青色笼 / 紫色笼）。

**回退手段：** Mk2 的构建代码在 `RebuildKit`；装机前的取舍与动手前必查项见
`NIGHT_LOG.md` 的「明早的决策点」。

### 3.2 已知 Bug / 疑点
- [x] **`TempLabel` 的第二个写入者已找到并修掉**：温度值本身是 1Hz 变的
      （`FluctuationLabel` 间隔稳定 1.10s 已证实），
      但 `TempLabel` 变化间隔不规则（`0.40 0.72 0.38 0.30 0.80 0.40 0.70 0.10`）。
      写它的是 `PowerSystem.Update` —— 每帧 `r.Temperature -= r.PowerOutput * cfg.ExtractionHeatLoss * dt`。
      **已修（`DECISIONS` 79 / `PROGRESS` Phase 24）**：`PowerSystem` 不再写温度，
      只发布 `r.ExtractionHeatRate`（F/s），由 `ReactorState` 在自己的 1 秒块里扣；
      系数、速率、每秒总量都没变，只是把写权还给唯一所有者（`DECISIONS` 7）。
      修复后 `TempLabel` 间隔 1.10 1.11 1.10 1.10 1.09 1.09，与 `FluctuationLabel` 同步跳变。
- [x] 主监视器的示意图框（`ReactorDiagramFrame` / `CoreDiagramFrame`）**仍是静止的** ——
      已接上（`PROGRESS` Phase 26 / `DECISIONS` 81）。纯观察者，只读 `GameState`。
- [x] **HDEF 电源拉杆的动画从绑定那一刻起就是死的** —— 已修
      （`PROGRESS` Phase 32 / `DECISIONS` 87）。`HDEFGenerator` 上 `PowerLever`（`hdef_lever`）
      与 `EmergencyControl`（`hdef_emergency`）会走到**同一个** `LeverUnion`（该机只有这一个），
      `Bind` 原先无条件覆盖，于是动作变成**没有 `detent` 分支**的 `hdef_emergency`，
      `applyLever` 直接 early-return，**拉杆从此不再动** —— 而控件照常触发、状态照常翻转、
      灯照常变色，**日志与监视器都不报错**。`Bind` 现在先问 `detent()` 这个动作能不能驱动拉杆，
      连「不能驱动的动作顶掉能驱动的动作」这条路径一起堵掉。
      全场共 **5 个拉杆**能被多个动作走到，**4 个合法且每个动作都有 detent，只有 HDEF 这一个是病态的**。

- [ ] **冷却液站的三盏灯不显示泵档位 —— `DECISIONS` 124 的遗留项，故意没顺手改。**
      `RebuildKit` 把它们描述成「三盏灯显示泵的档位」，而 `lampState` 对 `coolant_pump_level`
      没有分支，所以档位**从来没有被显示过**（不是 Phase 40 之后坏的）。
      档位本身是**四态**（`off / 1 / 2 / 3`，实测该拉杆 `detent=4`），三盏灯正好够做条状或三位的读数，
      所以「三盏灯」这个设计未必错。不知道的是**谁该拥有它们**：原版把灯留在站上
      （`OnButton`/`OffButton` 自己没灯），而现在先绑上的 `coolant_pump_on` 拿走了它们。
      调换两行绑定顺序就能改观，但那等于拿测试场景去猜 —— 先记下来，不当场答。

- [ ] **机房（Tesseract）在 remake 里没装 —— 被 `P10` 挡着，没动。**
      原版的 `s.MainframeMeltdown` 全 DataModel 零命中，
      而 `StateBridge` 第 57 行 `set(stats,'ActiveQPUs',6)` **焊死** ——
      名字和类型都照原版搭了，**缺的只有写入者**（同 `engine.events` 在 Phase 65 之前那个洞的另一半）。
      规格已挖出来（`PROGRESS.md` Phase 74：原版 DRM 的 MAINFRAME 段逐字全文），
      **但这是新加一条玩法机制，只能你拍板**（`CLAUDE.md` §1.4 第一条）—— 见 `QUESTIONS.md` `P10`。
      **速率一个数都没量到**（我量到的是旗标翻起 `t=719.86` / `t=868.94`，
      不是「第一个 QPU 第几秒掉」），所以选「做整条」得**先加一趟采集**。

### 3.3 测试覆盖缺口
- [x] **原条目把两类东西并列了，是分类错误。** `ConsoleBinder` 的控件表里
      **根本没有 QPU / Gateway / GravLift** —— 那三个是 `FacilitySystem` 下的独立系统，
      不是控制总线上的动作，拿控制测试去覆盖它们本来就用错了仪器。
      真正没覆盖的**控件是另外十二个**，现已全部覆盖
      （`PROGRESS` Phase 32 / `DECISIONS` 88）：
      `coolant_recalibrate` / `startup` / `shutdown` / `monitor_boot` /
      `pressurizer_vent` / `pea_vent` / `gravatron_charge` / `gravatron_overload` /
      `hdef_lever` / `hdef_emergency` / `hdef_cell` / `metu_ecc`。
      做法是加第二个阶段，断言 `GameState` 与系统状态而**不是**断言场景
      —— 这十二个大多**没有任何可见外观变化**，旧测试那种「看拉杆动没动 / 灯变没变色」
      的仪器对它们无能为力。
- [ ] **仍然缺：QPU 更换 / Gateway / GravLift 的独立测试** —— 它们需要自己的测试文件，
      不该挂在控制测试名下。
- [x] ~~**模拟点击在这个 place 里够不到控制台**~~ —— **这条是错的，Phase 42 已作废并修正。**
      原文说「全场只有 **1 个** `SpawnLocation`…几何体根本没流送到客户端」。实测：
      `Workspace.TeamSpawns` 里有 **5 个** —— 1 个 `SpawnLocation` @ (233, 402.9, 1370)，
      加 `Spawn1..Spawn4` @ (257, 277.1, 29.4 / 36.9 / 44.4 / 51.9)，**就在台子旁边 122~160 studs**、
      桌面高度、脚下是实地（`Workspace.Geometry.Parts.Part` y=276.94，落差 0.12）。
      那四个是**死的**（`Neutral=false` + `TeamColor=White`，而 `Teams:GetTeams()` 是空的），
      所以「客户端远端出生」没错；但「走不到」是**从一次依赖距离的采样推出来的**：
      远端出生点到控制室的直线**60 个采样只被挡 1 个**，而 97 / 42 那两个数字**是距离造成的** ——
      同一个客户端，角色站到台前之后 `ThermalConsole` 是 **678** 件。
      **真点击已经打通**：`moveTo(427, 115)` + 左键 →
      `[Console] andypeng1NB pressed: Coolant Pump 1 Sensor Recalibration  (ThermalConsole)`，
      即 `ClickDetector → ControlTrigger.Fire → CoolantSystem.Recalibrate`。
      四个必须先量的点：相机要用 `RenderStepped` **每帧重设**（`execute_luau` 每次调用后会把
      `CameraType` 重置回 Custom，转角色是没用的）；瞄准要**投影 + 对该像素做射线**并断言命中的是
      拉杆自己（只投影不够，有四组姿态的射线死在 `Riser` 上）；三个冷却液拉杆**共线**，
      要用垂直于那一排的机位才分得开；工具发的 y 是**请求值 + 58**，且目标要避开左上角 CoreGUI
      聊天窗（否则工具报 `hits CoreGUI`）。完整方法见 `PROGRESS` Phase 42 / `DECISIONS` 124。

### 3.4 环境 / 工具
- [ ] 装 Node.js 让 `@6xvl/robloxstudio-mcp` 能用（见 0.6）
- [ ] 项目根 `opencode.json` 已写好，重启 opencode 生效
- [x] **Studio 截图可以直达 —— 上一条记录是错的，已更正（2026-09-23）。** 原记录说
      `capture_screenshot` 只把图片**内联**返回、不落盘，而 sidecar 只认「路径 / URL / data URL」，
      「两边接不上」。**实测：`rblx_screen_capture` 返回的图在本会话里直接可见** ——
      不需要 sidecar、不需要落盘，本轮 CBL 二次重做的两张验收图就是这么看的。
      仍然成立的两点：`describe_image` 确实只认路径/URL；
      `PreloadAsync` 的逐资源回调在命令栏 VM 里确实不触发（70 个全 `NO-CALLBACK`），别指望它。
- [x] **`ModuleScript.Source` 上限 200000 字节 —— `DECISIONS` 已撞上，已拆成两个模块**（`DECISIONS` 123）。
      写入 202893 字节的镜像时被引擎**直接拒绝**（`Provided string length (202910) ... max length (200000)`），
      于是**第一次出现「磁盘在前、模块落后」**：磁盘吃下了 115-122，模块一个字节都没进。
      现在拆成 **`DECISIONS`（条目 1..74）+ `DECISIONS_2`（条目 75..124）**，
      边界是**条目号**而不是字节偏移；两个磁盘镜像 `DECISIONS.md` / `DECISIONS_2.md`
      各自**逐字节等于**自己模块的镜像（这两份不是 `docs/` 卫星文件，没有磁盘专属前言）。
      **写的时候注意**：`DECISIONS.md` 里有 2 个反斜杠（早期条目里 Lua 代码片段中的「反斜杠 + n」），
      所以这一份**只能在 Studio 内部从已有文本搬移出来，不能通过工具调用传文本**（§0.10）。

### 3.5 资产的落地状态（2026-10-04 第三次重写；Phase 89 换了终点；Phase 90 多了一件）

**终点又变了，而且是用户自己定的。** 这一节的三个版本对应三条路：

| 版本 | 教什么 | 结局 |
|---|---|---|
| 一 | 手动拖 fbx | 他拖了：**1.0769 倍**、偏 0.873、**没接上** |
| 二（Phase 88） | 我在 Studio 里用 66 个 Part 建 | 他说**「依据18那个part的最外围来扩」** —— 那一版把 collar 外面放在**面平面**（63.7120），环的**角**（64.6951）从墙里戳出来。**驳回。** |
| 三（Phase 89，**现在**） | **把环连参考件一起交到 Blender，衔接在那边做，他自己照做** | 用户原话：「**你把那个18边形搞到blender然后再衔接，我直接作为参考自己做**」 |

- [x] **`ChamberWall24` 参考件 —— 已交付在 `D:\BlenderRobloxTestProjects\ChamberWall24\`。**
      `.blend` / **`.fbx`（要导的就是这一个）** / `.glb` / 三张渲染图。
      **衔接是当前值定的，不是保守取大**：外接 24 边形（inradius `R`）包含环
      （circumradius `R′`）当且仅当 `R ≥ R′`，所以 `A24_IN = RING_R = 64.6951` **就是最小可行值**
      —— 它在 6 个方位（`0+60k`）**恰好碰到**环的角。
      四条接缝实测：**J1 最差顶点间隙 0.00000 stud**、**J2 = 64.6951**、
      **J3 最坏 `r·cos` 64.6327 ≤ 64.6951**、**J4 60° 扇区 环 3 / collar 3 / 墙 4 且 6 个角对齐**。
      **落地**：底面中心 `(-12.200, 47.400, -85.362)`、scale **1.0**、不旋转，
      期望 `Size ≈ 138.58 × 13.85 × 138.58`；**相位不用补**（三套顶点集都对 180° 镜像不变）。
      **必须导 FBX**：glTF 那条路进 Studio 是 **1.6943 倍**（10 / 5.902）。
      验证 76 项 / 0 失败（两种格式各 38），四个变异各红在自己的断言上。
      细节 `PROGRESS.md` Phase 89，取舍 **293..296**，片段 `docs/SNIPPETS.md` §5.20。
- [x] **`RingBridge18_24` 参考件 —— 已交付在 `D:\BlenderRobloxTestProjects\RingBridge18_24\`。**
      **用户逐条给的规格**（我收到的消息从「3.」开始，**1、2 两条没到**）：
      小环 18 边 r=0.8 z=0、大环 24 边 r=1.2 z=1、端面留作 n-gon、
      42 个桥接三角形（关系逐字抄在 `PROGRESS.md` Phase 90）、**蓝端面 + 红桥接**。
      **这是抽象件**：半径是**场景单位**（0.8 / 1.2），不是从世界里量出来的尺寸 ——
      与 `ChamberWall24` 的关系是「同一条 18 接 24 的线上第六件，但**规格是他写的**」。
      进 Studio 期望 `14.1648 × 14.1648 × 5.9020` studs（FBX 那条路；**glTF 是 1.6943 倍，不要导**）。
      `.blend` / **`.fbx`** / `.glb` / 三张渲染图。验证 **53 项 / 0 失败**（两种格式），
      六个变异**各红在自己的断言上**。细节 `PROGRESS.md` Phase 90，取舍 **297..302**，片段 §5.21。
      **没验的**：没进 Studio（无上传凭据）、Studio 侧材质没读。
- [x] **Studio 里那一版（Phase 88 的 66 个 Part）—— 已不在世界里，也不该再建。**
      世界现在**没有任何 `ChamberWall*` 件**，只剩 `ServerStorage` 两份存档
      （`ChamberWall24_mesh_20261004` = Phase 87 那版 MeshPart；
      `Wall24_import_20261004` = 他手动拖的那份，1.0769 倍、体量 147.72）。
      **Phase 89 没有删任何东西。** 脚本 `build_chamber_wall_24_parts.luau` 留在盘上作历史。
- [x] **「手动拖 fbx」那条路 —— 已作废，保留作历史。**
      拖进来的那份**整体是设计尺寸的 1.0769 倍**（三个件、每个件的三个轴**全是这个系数**，
      所以是**均匀**的，不是哪个轴填错），中心偏 **0.873**，
      内面离环最外围还差 **3 stud**，**根本没接上**。
      已搬成 `ServerStorage.Wall24_import_20261004`（**没删**）。
- [ ] **`LaserPort` / `TransitionPillar` / `RadiationScrubberUnit` 要按设计**重量一遍尺寸。
      理由：退役那份导入墙的 1.0769 倍是**均匀**的，指向**导出链**而不是某一次操作。
      同一套链出来的 `LaserPort`（Phase 83，走 glTF，那边已知是 **1.6943 倍**）和
      `TransitionPillar`（Phase 84）**可能一样中招**。
      **做法**：拿 `_tools/blender/*_check.py` 里那份**设计数字**（那些脚本已经把导出物重新导入量过）
      对 Studio 里已导入的实例读 `MeshSize`，比一遍。**在量之前不要假定它们是对的。**
      （1.0769 这个系数本身**没查来源** —— 那份已退役，不值得为它开一轮。）
- [ ] **这三件的材质**同样只在 Blender 侧验过。`LaserPort` 的落地脚本已写
      （`_tools/apply_laser_port_materials.luau`），`TransitionPillar` / `RadiationScrubberUnit` 还没有。
- [ ] **`ChamberWall24` 的材质也没在 Studio 验过** —— 它现在走的是**导入器**
      （用户自己导 FBX），所以材质在 Blender 侧怎么设就怎么进来。
- [ ] `_tools/apply_chamber_wall_materials.luau` **作废** —— 它是给**导入物**上色的，
      而它要匹配的那两版（Phase 87 的 MeshPart、Phase 88 的 66 个 Part）**都已经不在世界里**。
      文件留在盘上作历史，别跑它。

### 3.6 音乐（Phase 93；Phase 95 把内容换了一遍）

`asstes/music/ReactorShift.{ogg,mp3}`（**263.84 s / 89.25 bpm / F 大调五声**，按量出来的规格写的原创曲）
**已经在盘上、已经进仓库、已经过了 13 项检查 + 11 个变异**（`_tools/music/check_song.py`）。

- [ ] **进 Roblox 这件事没做，而且是卡在凭据上，不是卡在代码上。**
      `ROBLOX_OPEN_CLOUD_API_KEY` 与 creator id **都没设**，所以 `upload_asset` 走不通。
      **要接的话**：上传成 Audio 资产 → 拿 `rbxassetid`。**落地点没有现成的插槽** ——
      普查在 `PROGRESS.md` 3650 行附近：`SoundService` 底下是 **7 条总线**
      （其中 `MusicSounds` 实测 `Volume = 1`），`Workspace.Sounds` 里是 **226 个散件 Sound**，
      **没有任何一个叫 `Music`**。所以「接哪儿」是个**新决定**，不是找一个空位填进去。
      **动手前先问**：`Workspace.Sounds` 是**世界的一部分**（§0.12 第 3 条）。
- [ ] **听感没验过，也验不了** —— texture 与旋律余量是**尺子**不是耳朵（取舍 313/317）。
      「下雨感没了」「旋律清楚了」「**有没有高潮**」**只有操作员能判**；
      他下一次的听后感就是下一次测量。**Phase 95 之后这一条更硬**：
      旋律余量现在是**量出来**的（窄带中位 +6.5 dB、高潮段 +12.8、0/104 过零），
      但那证明的是「旋律站得出来」，**不是「这是一段曲子」**（取舍 332）。
- [ ] **`_tools/music/` 的三个检查器没有进 `run_tests.sh`**：`check_song.py` 要
      **10 分钟量一版**（解码两个格式 + 11 个变异各自跑一遍），和现在那条秒级流水线不是一个量级，
      所以**故意没挂**。要挂的话得先给它一个 `--fast` 档（只跑真文件、跳过变异）。

- [ ] **Phase 95 之后仍然没有换工具。** GitHub 上的开源整曲生成器
      （YuE / ACE-Step / SongGeneration / SongGen / InspireMusic，地址在 `PROGRESS.md` 95.1）
      查过、**不采用** —— 理由三条写在取舍 **327**，第一条是**我听不见**
      （拿它迭代 = 每轮都把判断交给操作员的耳朵），**不是硬件**。
      **顺带更正一条错话**：torch **有** cp314 win_amd64 的轮子（0.12 GB），
      「装不了 torch」不成立。
- [ ] **`_tools/music/lead_margin.py` 是新增的尺子，也没挂 `run_tests.sh`**：
      它一次跑**四遍 `assemble`**（无 lead / 只 dry / 只 wet / 整混），约 5 分钟 ——
      和 `check_song.py` 同一个理由（量级不对，故意不挂）。
- [ ] **旧的旋律余量尺子已作废**（它减的「底」里有旋律，两个缺陷写在
      `lead_margin.py` 的文档字符串里）。**别再引用「+6.9 dB」那个数** ——
      它是对着含旋律的底外推出来的，实测是 **−4.5 dB**（取舍 330）。

---

### 3.7 世界的「搬运」规矩，与 Phase 96 留下的四笔账

**规矩（Phase 96 之后，任何一次动世界之前先过这一条）：**

1. **搬东西 = 改世界。** §0.12 第 3 条：RS 里的部件不渲染，**Workspace 里的在渲染**。
   所以「把 Workspace 的东西挪去别处减 lag」这件事**必须先问用户**，而且要先答一个问题：
   **这些东西现在是不是在渲染、玩家此刻看不看得见。** Phase 96 的那次 park 恰恰没答这一问。
2. **要搬就整根搬，永远不要为了搬运先合并同名根**（取舍 335，§0.22）。
   Roblox 允许兄弟重名；合并毁掉的是**分组**，而分组没有名字、没有属性、没有绑定。
3. **undo 不是清理工具**（取舍 272）。要「撤销」就得**重建**，并给出能**独立复算**的不变式
   （部件总数 **91,905**、`Workspace.Consoles` 解析得到、射线穿透数）。
4. **拆一个合并过的容器之前先写护栏**（取舍 338，片段 `docs/SNIPPETS.md` §5.23），
   拆完**再量一次几何** —— 算术护栏不等于几何正确。

**四笔已知的、没补回去的账**（都**只改分组、不改外观**，渲染与物理不受影响）：

| 账 | 量 | 为什么补不回来 |
|---|---|---|
| **45 个同名 `Model` 根被并成 `Model[1]`** | 476 孩子 / 1,539 部件 | 容器名字就是 `Model`（全 DataModel 109 个同名）；零件上**没有任何父属记录**；45 个空壳只剩 pivot，彼此只隔 2–15 stud —— 最近邻分配**大概率是错的**（取舍 340） |
| **53 个还原节点的原始嵌套** | 24 个有父级路径（`RestoredFrom` 比 park 前缀深）、29 个属性被截断且没有节点名 | 记录本身不完整 |
| **`Meshes` 分组文件夹** | 4 个 `Hexagon` + `platform_marshmallow` **以散件在世界上** | 文件夹没了（全 DataModel **0 命中**）—— **只丢分组，没丢东西** |
| **236 个还原节点留在 Workspace 顶层** | Folder 2 / MeshPart 27 / Model 36 / Part 165 / UnionOperation 2 / WedgePart 4（5,740 部件） | 原容器不可考；世界坐标没变，所以**看得见的部分没错** |

**`ServerStorage.ParkedFacility_20261006` 现在是空的 —— 故意留着。**
它是这次操作唯一的现场痕迹（292 个根带着 `UnparkedAt="2026-10-06"`），删掉它等于
把「这里发生过什么」也删掉。**要删随时可删，但不是现在。**

**45 个空 `Model` 壳同理，不要删** —— 它们的 `GetPivot()` 是那 1,539 个零件
「原本属于哪几堆」的**唯一**线索（取舍 336）。留着不花任何代价。
