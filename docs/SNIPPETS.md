# CLAUDE §5 所有关键代码片段

> 磁盘专属前言 —— 不属于游戏内的 `CLAUDE` ModuleScript，校验脚本按「第一个 `## ` 之前
> 整段丢掉」剥掉，长度写死在 `_tools/verify_docs.py` 里。
>
> 本文是从 `CLAUDE.md` 拆出来的 **§5 所有关键代码片段**。权威副本仍然是游戏里的
> `game.ServerScriptService.GameCore.CLAUDE`，改完同一步镜像回模块。
> `CLAUDE.md` 只留每轮都要看的章节；拆的理由与分工见它开头的 §0.0。

## 5. 所有关键代码片段

### 5.1 温度 1 秒结算一次（ReactorState）★ 本次会话核心改动
用户要求：「把温度计算逻辑改成一秒一次」

```lua
-- Config.Reactor
AmbientTemperature = 20, -- cold facility temperature (F)
-- Core temperature is recalculated once per second, not every frame.
TempUpdateInterval = 1.0,
MaxCoreTemperature = 60000,

-- ReactorState.Update —— 在线分支
-- Temperature is recalculated once per second, not every frame.
r.TempAccum = (r.TempAccum or 0) + dt
if r.TempAccum >= cfg.TempUpdateInterval then
    local step = r.TempAccum
    r.TempAccum = 0
    local before = r.Temperature
    -- perTick is per TRGWeb tick; convert to the elapsed seconds.
    r.Temperature += (perTick / Config.Sim.TRGWebTick) * step
    -- One random fluctuation per update, like the prototype.
    r.Temperature += math.random(-cfg.NoiseAmplitude, cfg.NoiseAmplitude)
    -- Small passive loss to ambient (kept from the original model).
    r.Temperature -= (r.Temperature - cfg.AmbientTemperature) * 0.002 * step
    -- P.E.A extraction sink, published by PowerSystem as F per second.
    r.Temperature -= (r.ExtractionHeatRate or 0) * step
    r.Temperature = math.clamp(r.Temperature, cfg.AmbientTemperature, cfg.MaxCoreTemperature)
    -- Fluctuation readout: the change applied on this update.
    r.TempFluctuation = r.Temperature - before
end

-- ReactorState.Update —— 离线/跳闸分支（同一节奏）
-- Offline / tripped: passive cool-down only, on the same 1s cadence.
if not r.Online or r.Tripped then
    r.TempAccum = (r.TempAccum or 0) + dt
    if r.TempAccum >= cfg.TempUpdateInterval then
        local step = r.TempAccum
        r.TempAccum = 0
        local before = r.Temperature
        r.Temperature -= (r.Temperature - cfg.AmbientTemperature) * 0.05 * step
        r.Temperature = math.clamp(r.Temperature, cfg.AmbientTemperature, cfg.MaxCoreTemperature)
        r.TempFluctuation = r.Temperature - before
    end
    ReactorState.UpdateCoreState()
    GameState.Signals.ReactorChanged:Fire(r)
    return
end
```
**注意：** 压力仍按每帧走（用户只要求改温度）。
`r.TempAccum` 用 `(r.TempAccum or 0)` 兼容 `GameState.Reset()` 后的 nil。

**注意 2（`DECISIONS` 79）：** 温度**只有 `ReactorState` 一个写入者**。
`PowerSystem` 曾经在自己的 `Update` 里每帧扣 PEA 抽取热沉，于是这个已经改成
「每秒一跳」的值在两次结算之间还在慢慢变 —— `%.0f` 把它显示成每 3.5 tick 掉 1 F
（实测间隔 0.30/0.40 交替，与 0.02 × 141 GW ÷ 60 的预测吻合）。
现在它只发布 `r.ExtractionHeatRate`，由上面这段 1 秒块统一扣。

### 5.2 拉杆只动 LeverUnion（ControlVisuals）★ 用户强烈纠正的点
用户原话：「拉杆移动的部分是LeverUnion其他部分都不动啊！！！」

**错误的旧实现（整个模型一起转）：**
```lua
-- ❌ 错：PivotTo 会把外壳、底座、文字全部带着转
object:PivotTo(entry.base * CFrame.Angles(angle, 0, 0))
```

**正确实现：**
```lua
-- Walk up from a click part to the lever's moving piece.
-- The only part that may move is LeverUnion; LeverOrginPart is its hinge.
-- Everything else (housing, base, text) must stay put.
local function findLeverParts(clickPart)
    local node = clickPart
    while node and node ~= game.Workspace do
        if node:IsA("Model") then
            local moving = nil
            for _, d in ipairs(node:GetDescendants()) do
                if d:IsA("BasePart") and d.Name == "LeverUnion" then
                    moving = d
                    break
                end
            end
            if moving then
                -- LeverOrginPart is only a 0.1^3 marker sitting at the handle's
                -- centre, so rotating about it just spins the handle in place.
                -- The real hinge is the bottom of the handle.
                local hingeCF = moving.CFrame * CFrame.new(0, -moving.Size.Y * 0.5, 0)
                return moving, hingeCF, true
            end
        end
        node = node.Parent
    end
    return nil, nil
end

local function applyLever(moving, entry)
    local index = detent(entry.action, entry.arg, entry.arg2)
    if not index and entry.clickIndex then
        index = entry.clickIndex
    end
    if not index then return end
    local states = math.max(2, entry.states or 2)
    local frac = (math.clamp(index, 1, states) - 1) / (states - 1)
    local angle = math.rad(MIN_ANGLE + (MAX_ANGLE - MIN_ANGLE) * frac)  -- 28 .. -28
    -- Swing the handle around the hinge; the rest of the lever never moves.
    local ok = pcall(function()
        if entry.hingeIsPoint then
            local hingeCF = entry.hinge
            local relative = hingeCF:Inverse() * entry.base
            moving.CFrame = hingeCF * CFrame.Angles(angle, 0, 0) * relative
        else
            local relative = entry.hinge:Inverse() * entry.base
            moving.CFrame = entry.hinge * CFrame.Angles(angle, 0, 0) * relative
        end
    end)
    return ok
end
```

**Bind 里必须用 `levers[moving]` 而不是 `levers[object]`；而且不能被「驱动不了拉杆的动作」顶掉：**
```lua
-- A lever can be driven by several click parts (PW1..PW5): keep the action
-- and remember the explicit notch for the last click.
--
-- A control that CANNOT drive a lever must not displace one that can.
-- HDEFGenerator is the case that bit: EmergencyControl sits beside PowerLever,
-- owns no LeverUnion of its own, so its walk climbs to the generator - where the
-- only lever IS PowerLever's. Last bind won, so the emergency control overwrote
-- the power lever's action with hdef_emergency, which has no detent branch, and
-- the lever never moved again.
-- detent() is the single authority on whether an action can drive a lever, so ask
-- it rather than keeping a second list of actions in sync by hand.
local incomingDrives = action and detent(action, 0, 0) ~= nil
local heldAction = levers[moving].action
local heldDrives = heldAction and detent(heldAction, 0, 0) ~= nil
if action and (not heldAction or incomingDrives or not heldDrives) then
    levers[moving].action = action
    levers[moving].arg = arg
    -- Adopt the detent count of the richer action (e.g. a coolant
    -- lever starts as ON/OFF then gains the 0..3 level notches).
    levers[moving].states = STATES[action] or levers[moving].states
end
if arg2 and arg2 >= 1 then
    levers[moving].clickIndex = arg2
end
```

**这道闸的意义（`DECISIONS` 87）：** 全场 **5 个拉杆**能被多个动作走到 ——
`CoolantControl1/2/3` 的 `coolant_pump_on/off/level`，`StartUpBigLever` 的 `startup`/`shutdown`，
以及 `HDEFGenerator` 的 `PowerLever`/`EmergencyControl`。**前四组每个动作都有 `detent` 分支，
所以 last-bind-wins 是正确行为**（`startup`/`shutdown` 判据同样是 `r.Online`，两个都能驱动）；
**只有 HDEF 那一组里 `hdef_emergency` 没有分支**，于是它一绑上去就把拉杆锁死了。

**档位表：**
```lua
local STATES = {
    cfan = 2, event = 2, startup = 2, shutdown = 2,
    hdef_lever = 2, hdef_emergency = 2,
    cbl_set_power = 5, cbl_power = 5,
    pea_set_extraction = 4, pea_extraction = 4,
    coolant_pump = 2, coolant_pump_on = 2, coolant_pump_off = 2,
    coolant_pump_level = 4,
}
```

**实测结果（5 个拉杆全部 PASS）：**
```
CoolantControl1      PASS  swing=0.246 studs  parts=25
E_VENTLever1         PASS  swing=0.223 studs  parts=24
CFLever1             PASS  swing=0.167 studs  parts=24
CBL LargeLever       PASS  swing=0.246 studs  parts=33
PEA ExtractionLever  PASS  swing=0.246 studs  parts=25
```

### 5.3 创建 AI 材质（MaterialVariant）
`generate_material` 生成的变体是**空的**（没有 `Texture` 子节点），必须自己挂贴图，
并且必须是 `MaterialService` 的**直接子节点**才能被 `part.MaterialVariant` 引用。

```lua
local MS = game:GetService("MaterialService")
local specs = {
    { name = "FacilitySteelPanel", base = Enum.Material.Metal,         id = "rbxassetid://113678561896495", tile = 8 },
    { name = "FacilityFloorPlate", base = Enum.Material.DiamondPlate,  id = "rbxassetid://99453180185807",  tile = 14 },
    { name = "ReactorWallPlate",   base = Enum.Material.CorrodedMetal, id = "rbxassetid://132401913334608", tile = 18 },
}
for _, s in ipairs(specs) do
    local old = MS:FindFirstChild(s.name)
    if old then old:Destroy() end
    local mv = Instance.new("MaterialVariant")
    mv.Name = s.name
    mv.BaseMaterial = s.base
    local tex = Instance.new("Texture")
    tex.Name = "Texture"
    tex.Texture = s.id
    tex.StudsPerTileU = s.tile
    tex.StudsPerTileV = s.tile
    tex.Parent = mv
    mv.Parent = MS
end
```

### 5.4 全场景材质应用（100,120 个部件，3.87 秒）
```lua
local ws = game.Workspace
local CHS = game:GetService("ChangeHistoryService")
pcall(function() CHS:SetWaypoint("MaterialPass") end)

local CONSOLE = { Consoles=true, Monitors=true, MonitorsFacility=true, Alarms=true,
    MedicalDispenser=true, Tools=true, Mainframe=true, QuantumMainframe=true,
    MES=true, MainframeToolStorageCull=true, Stats=true, ClickInfo=true, UISounds=true }
local HEAVY = { ChamberWalls=true, ReactorCBLs=true, Core=true, GravatronUnit=true,
    METU=true, CoolantReserviors=true, PowerExtractionAssembly=true, GravitationShafts=true,
    CRC1=true, CRC2=true, CRC3=true, MovingParts=true, PhysicsObjects=true }

local stats = { steel = 0, wall = 0, floor = 0, skipped = 0 }
local function isFloor(d)
    local s = d.Size
    return s.Y <= 1.5 and (s.X >= 8 or s.Z >= 8)
end

local done = 0
for _, top in ipairs(ws:GetChildren()) do
    if (top:IsA("Model") or top:IsA("Folder")) and top.Name ~= "GameCoreTests" then
        local mode = CONSOLE[top.Name] and "steel" or (HEAVY[top.Name] and "wall" or "mixed")
        for _, d in ipairs(top:GetDescendants()) do
            if d:IsA("BasePart") then
                if d.Material == Enum.Material.Metal then
                    if mode == "steel" then
                        d.MaterialVariant = "FacilitySteelPanel"; stats.steel += 1
                    elseif mode == "wall" then
                        d.Material = Enum.Material.CorrodedMetal
                        d.MaterialVariant = "ReactorWallPlate"; stats.wall += 1
                    else
                        if isFloor(d) then
                            d.Material = Enum.Material.DiamondPlate
                            d.MaterialVariant = "FacilityFloorPlate"; stats.floor += 1
                        else
                            d.MaterialVariant = "FacilitySteelPanel"; stats.steel += 1
                        end
                    end
                else
                    stats.skipped += 1
                end
                done += 1
                if done % 8000 == 0 then task.wait() end
            end
        end
    end
end
```
**结果：** `steel 49,758 / wall 44,456 / floor 5,906 / skipped 24,746`

### 5.5 灯光大修（画面难看的根因）

> **⚠️ 下面这段代码是当时的改动，不是现状。** 现基线值见 §2.8 顶部的更正表
> 与 `DECISIONS` 66。`EnvironmentSpecularScale` 已从 0.8 降到 **0.15**。
```lua
local L = game.Lighting

-- ---------- 1. Atmosphere (air/depth) ----------
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
atm.Name = "Atmosphere"
atm.Density = 0.38
atm.Offset = 0.25
atm.Color = Color3.fromRGB(199, 191, 180)
atm.Decay = Color3.fromRGB(106, 100, 94)
atm.Glare = 0.15
atm.Haze = 1.2
atm.Parent = L

-- ---------- 2. Environment lighting (the big fix) ----------
L.EnvironmentDiffuseScale = 0.6      -- 之前是 0，所有 PBR 材质全死
L.EnvironmentSpecularScale = 0.8     -- 之前是 0，金属像塑料
L.Brightness = 2.5
L.Ambient = Color3.fromRGB(31, 28, 26)
L.OutdoorAmbient = Color3.fromRGB(89, 97, 107)
L.ExposureCompensation = 0.15
L.ShadowSoftness = 0.3
L.GlobalShadows = true

-- ---------- 3. Sun rays ----------
local sr = L:FindFirstChildOfClass("SunRaysEffect") or Instance.new("SunRaysEffect")
sr.Name = "SunRays"
sr.Intensity = 0.08
sr.Spread = 0.85
sr.Parent = L
```

### 5.6 灯光溢出（给 Neon 部件加 PointLight）
```lua
local CAP = 260
local added = 0
local PRIORITY = { "Alarms", "RoomLights", "Lights", "Monitors", "MonitorsFacility", "Core", "ReactorCBLs" }

local function area(p)
    local s = p.Size
    return (s.X * s.Y + s.Y * s.Z + s.X * s.Z)
end

for _, name in ipairs(PRIORITY) do
    local top = ws:FindFirstChild(name)
    if top then
        for _, d in ipairs(top:GetDescendants()) do
            if added >= CAP then break end
            if d:IsA("BasePart") and d.Material == Enum.Material.Neon
                and not d:FindFirstChildOfClass("PointLight") then
                if area(d) >= 1.2 then
                    local pl = Instance.new("PointLight")
                    pl.Color = d.Color
                    pl.Brightness = 2.2
                    pl.Range = math.clamp(area(d) * 2.2, 6, 22)
                    pl.Shadows = false
                    pl.Parent = d
                    added += 1
                end
            end
        end
    end
end
```

### 5.7 正确的运行时验证模式 ★ 必读
**因为 0.2 的坑，验证必须读实例状态。**

**测 1Hz 节奏 —— 采样 TextLabel 的变化时间戳：**
```lua
local mon = game.Workspace.Monitors.MainControlRoomMonitor
local fluct
for _, d in ipairs(mon:GetDescendants()) do
    if d:IsA("TextLabel") and d.Name == "FluctuationLabel" then fluct = d end
end

local last = fluct.Text
local stamps = {}
local t0 = os.clock()
while os.clock() - t0 < 5 do
    if fluct.Text ~= last then
        stamps[#stamps+1] = { os.clock() - t0, fluct.Text }
        last = fluct.Text
    end
    task.wait()
end
local gaps = {}
for i = 2, #stamps do
    gaps[#gaps+1] = string.format("%.2f", stamps[i][1] - stamps[i-1][1])
end
-- 实测输出: FluctuationLabel: 5 changes in 5.0s | gaps: 1.10 1.10 1.10 1.10
```

**测拉杆 —— 对比所有部件的 CFrame：**
```lua
local lever = game.Workspace.Consoles.ThermalConsole.CoolantControl1.BigLever
local before, order = {}, {}
for _, d in ipairs(lever:GetDescendants()) do
    if d:IsA("BasePart") then
        before[d] = d.CFrame
        order[#order+1] = d
    end
end
-- ... 触发状态变化 ...
task.wait(0.5)
local moved = {}
for _, d in ipairs(order) do
    if d.Parent and (d.CFrame.Position - before[d].Position).Magnitude > 0.001 then
        moved[#moved+1] = d.Name
    end
end
-- 判定: #moved == 1 and moved[1] == "LeverUnion"
```

### 5.8 在 Edit 模式验证新代码（绕过 require 缓存）
```lua
local modScript = game.ServerScriptService.GameCore.FacilitySystem.ControlVisuals
local CV = loadstring(modScript.Source)()   -- 全新实例，绕过缓存
```

### 5.9 文档 ModuleScript 格式
```lua
return [=[
# 标题

内容...

]=]
```
**注意：内容里不能出现「右方括号+两个等号+右方括号」这个序列。**

### 5.10 拉杆的平滑落位（VisualFeedback.poseLever）★ Phase 59
> **§5.2 是旧的。** 它是 `ControlVisuals` 的**旋转**写法，已被取代 ——
> 现在写拉杆 CFrame 的是 `SSS.ReactorBackend.VisualFeedback`，运动是**纯平移**。
> 照着 §5.2 改会退回一个**已经撤过的**方案（`DECISIONS_2` 187）。

改成 tween 之前（一帧落位，没有动画，但档位是对的）：
```lua
part.CFrame = entry.baseline + entry.baseline.LookVector * throwDistance(level, maxLevel, entry.travel)
```

现在：
```lua
local function poseLever(key: string, level: number, maxLevel: number)
    local entry = levers[key]
    if not entry then return end
    local part = entry.part
    if not part.Parent then return end

    -- The goal is a pure translation along the lever's own axis: CFrame +
    -- Vector3 adds to the position and leaves the rotation alone, which is
    -- what makes carrying over a stored baseline exact.
    local goal = entry.baseline + entry.baseline.LookVector * throwDistance(level, maxLevel, entry.travel)

    -- Cancel before create. Two live tweens on one property both write it
    -- every frame and the winner is decided per frame, so a second click
    -- mid-flight can park the union on a detent nobody asked for. Cancel
    -- leaves it where it is, so the new throw continues from there rather
    -- than snapping back to the last completed stop.
    if entry.tween then entry.tween:Cancel() end
    local tween = TweenService:Create(part, leverTweenInfo, {CFrame = goal})
    entry.tween = tween
    tween:Play()
end
```

配置端（`Config.Visual`）：
```lua
-- Must sit BELOW RefreshSeconds: the refresh is signature-gated, so a stop
-- still being animated when the next pose arrives is a stop the union never
-- rests on.
LeverTweenSeconds=0.3,
```
读取端**不能**让一个 `nil` 把机制打下去（`DECISIONS_2` 190）—— 缺键就退回模块自带的
0.3 s，并**只 warn 一次**（每帧 warn 会把真消息变成噪音）。

**两个必须有的安全性质**（`DECISIONS_2` 188 / 189）：
1. **创建前先 `Cancel()`** —— 见上面代码里的注释。
2. **同一个实例被重新解析时沿用旧 `baseline` / `travel`**：
```lua
if known and known.part == part then
    if known.tween then known.tween:Cancel() end
    levers[key] = {part = part, baseline = known.baseline, travel = known.travel}
else
    local amount = travel
    if fromStop then amount = smallThrow(part) end
    levers[key] = {part = part, baseline = part.CFrame, travel = amount}
end
```
`smallThrow(part)` 是从该 rig 自己的 `ClickPart` 读 throw 的**符号**的，只在 union
坐在两个档位之一时才成立。半路重新测量会把**档位之间**的姿势当基准，符号可能反过来，
此后**每一抛都走错方向而且没有任何症状**（去错档位的拉杆仍然是一根在动的拉杆）。

**怎么验的（`§4.4` 要求真实验证；`§0.16` 挡着「读运行中的游戏」）** ——
不要等 Play 模式，用 Edit 模式的 `Heartbeat` 在进程内采样：
```lua
-- Edit 模式有真的 Heartbeat（实测 ~45-47 Hz），TweenService 也照常推进，
-- 所以「在两次工具调用之间」也能采到中途的姿势。
local conn = game:GetService("RunService").Heartbeat:Connect(function()
    -- 记下 part.CFrame，顺便在到达某个行程百分比时打断（Cancel + 重新 pose），
    -- 用来量「打断处有没有跳变」——这是端点检查看不见的那一半。
end)
```
本轮量到的数：**203 个不同姿势、单调、沿轴纯平移**；同 rig 的另外 23 个兄弟部件
和另外 20 根拉杆**逐位相同**（没被误伤）；两个档位都是**逐位精确**落位；
打断在行程 **41.8%** 处，跨过 cancel 的那一步 **0.000000 studs**，最终仍在
t = 13.498 s 精确落到远档。（**时间是按工具调用次数推进的**，
`task.delay` 不是可靠时钟 —— 0.4 s 的会在一次重调用**内部**烧掉，7.5 s 的**从没烧到**。）

---

### 5.11 百叶窗的缓动（`RoomShell.applyShutters`）★ Phase 60

**同一件事的另一半**：§5.10 是**控制台**上的拉杆（`VisualFeedback`），
这里是拉杆**指向**的三扇门（`RoomShell`）。落位公式**一个字没改**，
改的只有「怎么到那里」。

`Config.Shell` —— 和 `ShutterTravel` 做邻居（`Config` 与逻辑分离）：

```lua
-- How long the shutters take to travel that 10.58, read by RoomShell.
-- Deliberately not the levers' 0.3: a shutter moves about 15 times the
-- distance of a lever throw, so the same number would make the panel
-- crawl. 0.6 s is 17.6 studs/s, which is what a powered door looks like
-- -- and it is short enough that a double-toggle lands its second tween
-- while the first is still on screen, which is why RoomShell cancels the
-- live one before creating another instead of letting two share it.
ShutterTweenSeconds = 0.6,
```

`RoomShell` 的三段。**缓动词汇故意和拉杆一样**（`Quad` / `Out`）——
一个控制家族不该有两种手感；**缓动不进 `Config`**，它不是谁能调的旋钮：

```lua
-- ========== TWEEN ==========
-- Declared above Initialize because Initialize reads the config key. A local
-- declared after the function body still compiles, but the name inside
-- Initialize would resolve to a global and read nil -- the failure looks like
-- the knob doing nothing, with no error anywhere.
local DEFAULT_SHUTTER_TWEEN_SECONDS = 0.6
local SHUTTER_EASING_STYLE = Enum.EasingStyle.Quad
local SHUTTER_EASING_DIRECTION = Enum.EasingDirection.Out
local shutterTweenInfo = TweenInfo.new(
    DEFAULT_SHUTTER_TWEEN_SECONDS, SHUTTER_EASING_STYLE, SHUTTER_EASING_DIRECTION)
local warnedShutterTweenSeconds = false
```

**`DEFAULT_SHUTTER_TWEEN_SECONDS` 不是白写的**：配置坏掉时它不是错，是退路 ——
但**只说一次**，而且要说清行程没受影响（`DECISIONS_2` 190）。
「与成功无法区分的错误路径不是错误处理」，所以这里 warn 而不是静默：

```lua
    local seconds = config and config.Shell and config.Shell.ShutterTweenSeconds
    if typeof(seconds) == 'number' and seconds > 0 then
        shutterTweenInfo = TweenInfo.new(seconds, SHUTTER_EASING_STYLE, SHUTTER_EASING_DIRECTION)
    elseif not warnedShutterTweenSeconds then
        warnedShutterTweenSeconds = true
        warn(string.format("[RoomShell] Config.Shell.ShutterTweenSeconds is %s, not a positive number, so shutters take the module's own %.2f s. The travel itself is unaffected.", tostring(seconds), DEFAULT_SHUTTER_TWEEN_SECONDS))
    end
```

每个门条目带一个**活 tween 句柄**（`--!strict` 下要 `type` 别名，
和 `VisualFeedback` 的 `levers` 同一处理）；**创建前先 `Cancel()`**：

```lua
type ShutterEntry = {path: string, frame: BasePart, closed: CFrame, tween: Tween?}
local shutters: {ShutterEntry} = {}

local function applyShutters(open, config)
    local travel = Vector3.new(0, config.Shell.ShutterTravel, 0)
    for _, shutter in ipairs(shutters) do
        local frame = shutter.frame
        if frame.Parent then
            local goal = open and (shutter.closed - travel) or shutter.closed
            -- Cancel before create. See the note on ShutterEntry.
            if shutter.tween then shutter.tween:Cancel() end
            local tween = TweenService:Create(frame, shutterTweenInfo, {CFrame = goal})
            shutter.tween = tween
            tween:Play()
        end
    end
end
```

**`open` 那一支是 `closed - travel`（减 `Vector3`），不是 `closed * CFrame.new(...)`**：
中间那扇门的 `Frame` 绕 Y 转了 90°，减 `Vector3` 是引擎自己的「世界空间平移」，
和操作员那句「下降 10.58」是同一个操作。

**验证配方（§4.4），量到的数：** `Clone()` 到 `SSS.<temp>` 再 `require`（§0.15 → 绕过缓存），
驱动**发货的 `RoomShell.Refresh`**，并用 `RunService.Heartbeat` 采样。

- 关 → 开 `worstUpStepY = 0`；落点 `[271.619, 271.619, 271.620]`，**误差 0**；行程 **10.580**。
- 开 → 关回到作者姿势，**误差 0**，`worstDownStep = 0`（151 tick）。
- 真正走完 **0.583 s**（配置 0.6）。
- 中途 `Cancel`：开关那一刻前后两帧差 **0**，最终还是精确落档。
- 门里的 `Glass` 相对 `Frame` 漂移 **0**（焊着的，跟着走）；门以外写入 **0**。

> **⚠️ Edit 模式下逐 tick 的位移读不出「平不平」。** 第一版分析里出现过
> **2.707 studs / 11.9 ms**（≈ 227 studs/s），而 `Quad/Out` 的峰值只有 35.3 studs/s。
> 那是**采样假象**：tween 跟渲染步走，而 `Heartbeat` 回调**成串**投递 ——
> 121 个回调里 **111 个** `|Δy| < 0.005`。**换成 50 ms 时间桶**（最大 1.934，
> 解析上限 1.763）才读得出形状。细节与判据见 `DECISIONS_2` 193 / `PROGRESS` 60.3。

### 5.12 把事件流画进原场面板：**clone 模板，绝不写模板** ★ Phase 65

`SSS.ReactorBackend.LogPanel` 只有一个出口。**原件（源码）是真相**，这里是形状与理由。

```lua
local MONITOR    = 'LogControlRoomMonitor'
local MAIN_FRAME = 'MainMonitorFrame'
local LIST_FRAME = 'LogsFrame'
local ROWS       = 4          -- 365 / (60 + 20)：帧高除以模板高加 UIListLayout 的 Padding

-- CONTROL 不在里面：Engine:Command 每条被接受的指令都记一条，那是审计不是机器说的话。
local SHOWN = {ALERT = true, WARN = true, ERROR = true, INFO = true}

-- 严重度 -> 模板。颜色不在代码里，在模板自己的 TextLabel.TextColor3 上：
-- 青 0.667,1,1 / 橙 1,0.667,0 / 红 1,0.306,0.306。
local TEMPLATE_BY_KIND = {
    INFO  = 'TemplateLogFrame1', WARN = 'TemplateLogFrame2',
    ALERT = 'TemplateLogFrame3', ERROR = 'TemplateLogFrame3',
}

-- 取**最新**四条，保持旧在前、新在后。倒着走 + insert(1, ...) 是刻意的：
-- 正着走再 table.remove 会把「最新」写成「最旧」，而那是最不容易看出来的错法。
local wanted = {}
for index = #events, 1, -1 do
    local event = events[index]
    if SHOWN[event.kind] then
        table.insert(wanted, 1, {kind = event.kind, text = event.message})
        if #wanted == ROWS then break end
    end
end

-- 先拆上一批 clone，再建这一批。模板一个字都不动。
```

**四条纪律**（每条都对应一次真事）：

1. **clone 模板，不写模板。** 模板是原版美术的一部分，`TemplateLogFrame3.TextLabel`
   上那句 `E INITIATED` 是「这条链当初确实经这三格渲染过」的**唯一物证**。写进去就毁了。
   `Visible=false` 的三个模板留在原地，退出时 `LogsFrame` 回到只有一个 `UIListLayout`。
2. **颜色读模板，不要在代码里列一遍。** 三个模板只差 `TextColor3`，那说明色键是
   **原版设计的**；在 Lua 里再写一份就是两个真相。
3. **取最新、不是最旧**，而且**要有断言盯着**。变异「取最旧四条」必须把测试打红 ——
   拿 `events` 的前四条，代码照样跑、面板照样有字、颜色照样对。
4. **`CONTROL` 的排除放在消费端，不放在源头。** `engine.events` 照旧记全部 kind，
   过滤是这张表；将来想要审计轨迹的读者还在。

**驱动一次开机（验证用，Phase 65 实测过）**：`start` 不是随便能扳的，守卫是
`phase=='Ready' and booted and monitorPower and shuttersOpen`，所以顺序必须是

```lua
engine:Command('monitor_power'); engine:Command('shutters')
engine:Command('lights');        engine:Command('boot')
-- 走到 Ready（BootSeconds = 14 s，Phase 67 量的）之后才：
engine:Command('start')
```

> **⚠️ 别把 `engine.state` 存进 local。** `Engine:Reset` **整张表替换** `state`
> （故意的：逼每个服务重取引用）。缓存旧表再等它变，那个 `while` **永不退出**，
> 而 `Engine:Step` **不让帧** —— 官方插件的线程会占死，之后**每一个** MCP 调用超时。
> 2026-10-01 我这么写了一次，Studio 得重启。见 `DECISIONS_2` 224。


### 5.13 把「一句一帧」的捕获变成会动的界面：**只建模布尔** ★ Phase 67

原版开机屏的揭示节奏是从一份**按变化才写**的逐属性捕获里复原的。可复用的不是那张表，
是**怎么判断一个属性能不能从这种捕获里重建**。

```lua
-- Config.Shell.BootScreen —— 只存「什么时候该看见什么」，不存任何运动
Reveals = {
    {at=0, diagnostic={1, 8}},
    {at=1, diagnostic={9, 25}, log={1, 2}},
    {at=2, diagnostic={26, 27}, log={3, 3}},
    {at=3, diagnostic={28, 43}, log={4, 5}},
    {at=4, diagnostic={44, 45}},
    {at=5, clearDiagnostic=true, clearLog={1, 5}, log={6, 6}},
    {at=8, companyLogo=true},
},
```

```lua
-- BootPanel.Refresh —— 相位内按秒走表，签名门只认「第几步」
function BootPanel.Refresh(state, config)
    local schedule = config.Shell.BootScreen
    local booting = state.phase == 'Booting'
    local step = booting and stepFor(state.phaseTime, schedule) or 0
    local signature = booting and ('Booting:' .. step) or 'idle'
    if signature == lastSignature then return end
    lastSignature = signature
    local diagnostic, log, logo = wanted(step, schedule)
    for _, mon in ipairs(monitors) do
        if mon.boot.Parent then
            for n, label in pairs(mon.diagnostic) do label.Visible = diagnostic[n] == true end
            for n, label in pairs(mon.log) do label.Visible = log[n] == true end
            if mon.companyLogo then mon.companyLogo.Visible = logo end
        end
    end
end
```

四条会复发的判断：

1. **「按变化才写」的捕获里，密集属性比稀疏属性更不可信，不是更可信。**
   这份捕获 99.7% 的行是 `Position`/`Size`，但那是一秒最多一次的采样。
   **布尔活得过采样，曲线活不过。** 判据不是「采了多少次」，而是
   **「采样之后，我还知不知道我在断言什么」**。
2. **要不要重建运动，是要单独做的决定，不是「顺手一起还原」。**
   不做动画 = 一行行在对的秒出现但不动；硬做 = 在采样之间**发明**曲线再当测量结果。
   **前者是更小的谎。**
3. **一条 `false` 和一条 `true` 落在同一秒里，是「先全隐藏、再单独显示一个」。**
   而**文件顺序在一秒之内也不可靠** —— 照文件顺序读会把日志框空白 145 秒（本文件里真发生过）。
   判读法：**同一对写入在一段里出现两次、其中一次有确定的终态**，用那次定这个模式。
   **没有 `show-then-hide` 样本；真出现时这条规则会读错，所以它必须被写下来，不能被假设。**
4. **验证要拿两个互不相见的产物比。** 「拿模块比它自己读的那张表」是同义反复
   （`DECISIONS` 95 的老问题）。这里：**期望侧**从 180 MB 原始行重放，
   **实测侧**喂假时钟跑真模块再读**真部件**（§0.2），两侧在 `aux_compare.py` 里对。
   **再配两个变异**（去掉 `clearDiagnostic`、改 `BootSeconds`），两个都得变红 ——
   **不能变红的检查不是证据。**

> **⚠️ t=0 那一格也得进测试。** `ControlBinder` 的 publish 回调**与点击同拍**，
> 所以命令路径上也要 `Refresh` 一次。少了它，t=0 报的是**按之前**的屏 —— 而它长得
> 和「按了但没反应」一模一样。我的验证台就是这么红了一次才发现的。

### 5.14 绕一条**不在任何一件上**的轴转一件：恢复节点原点 ★ Phase 83

导入进来的 MeshPart 有个反直觉的性质：**它的 `Position` 既不是节点的原点，也不是它自己的
包围盒中心** —— Roblox 的导入器把每个 MeshPart 在它自己的 primitive 内部**重新取了一个原点**。
云台的关节轴因此**不落在任何一个件上**，只能从实例状态反解。

```lua
-- origin = 件的 CFrame 乘回「这个 primitive 在节点局部空间里的 bbox 中心」的负值。
-- row.off 是设计表里该 primitive 的局部 bbox 中心（节点局部空间），k 是导入缩放。
local function nodeOrigin(part, row, k)
    return part.CFrame * CFrame.new(-row.off * k)
end

-- 绕「过 pivot 的那条 axis 线」转，而不是绕 pivot 这个点转
local function worldSpin(pivot, axis, degrees)
    return CFrame.new(pivot) * CFrame.fromAxisAngle(axis, math.rad(degrees)) * CFrame.new(-pivot)
end
```

同一个节点的**每一个** MeshPart 都是同一个原点的**独立估计** —— 所以「它们对不对得上」是一次
**免费的检查**。这里 3 件 / 3 件 / 5 件各自算出同一点，最大分歧 **4e-6 stud**；对不上就说明
设计表把件配错了。

四条会复发的：

1. **绕错的点不会报错。** 端口照样动 —— 它只是绕一条**穿过空气的线**扫，看起来像松掉的铰链。
   `Model:GetPivot()` 救不了你：拿它分别问 yoke 和 head，回的是**逐字节相同的 pivot**，
   两个不同的节点不可能是这个数。
2. **识别部件既不能用名字、也不能用顺序。** 导入的名字和顺序都不稳，而**配错是静默的** ——
   颜色会涂到别的件上、原点会从错误的 primitive 里减出来。这里按**形状**认（尺寸 + 是不是
   thin along X），并且**次优匹配太接近就拒绝**那个件，宁可少认不认错。
3. **每帧的工作不要藏在连接里。** 插件 VM 会答应 `Heartbeat:Wait()`（回 0.0190 s），
   而它拿走的回调**一次都不跑**（3 拍 0 次，同期 `conn.Connected == true`）。
   **只存在于连接里的代码，从我唯一能驱动的那个 VM 里是测不到的** —— §0.2 换了身衣服。
   抽成 `M.stepBeam(rig)` 之后，测试台调的是**连接调的那段同一代码**，不是它的副本。
4. **`Instance.new("Part")` 生在世界的原点。** 不立刻摆位，刚打出去的激光会有一帧是
   一根 120 stud 的 Neon 圆柱**横躺在 (0,0,0)** —— 这是看得见的 artefact，不是理论问题。
   所以 `fire()` 里**同步**先摆一次，连接只当钟。

**验法（§4.4 的那种「检查部件位置」）：** 断言**不动的那件真的没动**（base 位移 0.000000）、
**绕轴不变量成立**（pan 轴距离漂移 4e-6，摆动 1.388 stud）、**两个分支都走到**
（打空 → `Size.X = 120` 且落点标记隐藏；命中 → `Size.X = 2.66` 且标记可见）、
以及**跟随**（头转过去之后光束跟了 59.32 stud，而 `axis · lens-dir` 仍然是 `1.000000`）。

> **⚠️ 出射方向也别拍脑袋写一个角度。** 用的是**镜片自己局部的 −X**
> （`-lens.CFrame.RightVector`），因为镜片是唯一一个沿 X 薄的 primitive，
> **那条轴就是光轴**。写死的角度错了不会报错，只会安静地打偏。
