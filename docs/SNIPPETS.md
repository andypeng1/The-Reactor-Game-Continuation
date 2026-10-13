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

### 5.15 顶点数不同的两条开环缝起来（Bridge Edge Loops）★ Phase 84

Roblox 的 MeshPart 是一份**做完的三角形汤**，那一侧没有任何算子能拿两条**边数不同**的环
把它们缝起来 —— 要手算那 n + m 个三角形再写进文件。这是基于部件的建模**到不了**的一类形状，
**不是"更难"，是不可达**。所以这类活是 Blender 的。

```python
bm = bmesh.new()
with trg.layer(bm, MAT_BASE):
    base_rings = trg.revolve(bm, [(BASE_R, BASE_Z[0]), (BASE_R, BASE_Z[1])], n=18)
with trg.layer(bm, MAT_TOP):
    top_rings  = trg.revolve(bm, [(TOP_R,  TOP_Z[0]),  (TOP_R,  TOP_Z[1])],  n=24)

# 只删"相对的那一对"端面，而且必须用 FACES_ONLY。
# 默认上下文会把面和它的棱、点一起带走 —— 那正是整条环，之后就没东西可桥了，
# 而失败长得像"Bridge Edge Loops 什么都没做"。
doomed = [cap_face(bm, base_rings[-1]), cap_face(bm, top_rings[0])]
if None in doomed:
    raise SystemExit("找不到两条接缝端面；拒绝猜")
bmesh.ops.delete(bm, geom=doomed, context="FACES_ONLY")

# 前置断言：正好两条环，18 和 24。喂给它四条开环它照样会产出"一个"网格。
sizes = sorted(len(l) for l in rim_loops(bm))
if sizes != [18, 24]:
    raise SystemExit("期望环长 [18, 24]，实际 %s；拒绝架桥" % sizes)

with trg.layer(bm, MAT_BAND):
    res = bmesh.ops.bridge_loops(bm, edges=[e for e in bm.edges if len(e.link_faces) == 1])
assert len(res["faces"]) == 18 + 24          # 边数不同 → 三角形扇，正好 n + m 个
```

**四条会复发的：**

1. **`context="FACES_ONLY"` 是这里的全部关键。** 默认删除会把棱和点一起带走 ——
   带走的就是要桥的那条环。
2. **空隙不是余量，空隙就是桥。** 两条环若共面，桥出来的是 42 个**退化**三角形：
   零面积、看不见，而"42 个面"**照样成立**。凡"计数对、内容空"的地方都再配一条几何断言。
3. **`cap_face` 要按顶点**集合**认，不能按边数认** —— 两个端面多边形边数相同，
   `len(f.verts) == n` 分不出上下。认错就删错端，两条环跑到模型两端、相距 4.6 stud，
   桥成一个吞掉整根柱子的桶。
4. **倒角是角度过滤的，所以它滤的其实是"形状对不对"。** 正确的带子只倾 20.6° < 25° → 被跳过；
   一块**交叉**的带子很陡 → 倒角去吃它，把带子切碎、把两条环从设计高度上拽下来
   （verts 126 → 240，`band_faces` 直接归 0）。**错的带子会被倒角藏起来**：
   看起来不像"错了"，像"那一段什么都没有"。

**怎么读回来（`_tools/blender/transition_pillar_check.py`）：** 重新导入 `.fbx` **和** `.glb`，
断言 ①闭合流形 ②单壳 ③两条环的**边数与半径** ④带子 42 个**三角形** ⑤不扭 ⑥无退化面。

```python
# glTF 没有地方放多边形，所以它把每个角拆成独立顶点：504 个顶点焊完只剩 126 个,
# 和 FBX 一模一样。不焊接，open_edges=504 / components=128 这数是**关于问法的**,
# 不是关于文件的。跨格式比较前一律先按位置焊接。
def welded(obj):
    key_of, pos, index = {}, [], []
    for v in obj.data.vertices:
        w = obj.matrix_world @ v.co                       # ← 文件单位
        k = (round(w.x, 5), round(w.y, 5), round(w.z, 5))
        if k not in key_of:
            key_of[k] = len(pos)
            pos.append((w.x * SPU, w.y * SPU, w.z * SPU))  # ← 乘回 stud 才能比设计数
        index.append(key_of[k])
    return pos, [tuple(index[i] for i in p.vertices) for p in obj.data.polygons]
```

**扭不扭只能靠面在哪。** 一条扭过的带子**面数相同、同样闭合、同样单壳** ——
分开它们的只有位置：

```python
floor_r = 0.9 * min(BASE_R, TOP_R)          # 门槛由设计推出来，不手挑
worst = min(math.hypot(sum(pos[i][0] for i in f) / len(f),
                       sum(pos[i][1] for i in f) / len(f)) for f in band)
# 正确 2.1837 ／ 交叉 0.5898 ／ 门槛 1.8900
```

**变异开关（写在构建脚本里，`sys.argv` 门控）：** `--no-bridge`（10 红）、
`--twist`（**全绿，负结果**：`recalc_face_normals` 抹掉翻转，`bridge_loops` 按几何推对应关系，
绕向传不到带子上）、`--cross`（**只有 twist 那一行红**）。
**一条从没红过的断言是装饰** —— 前两次变异都没把 twist 逼红，所以补了第三种。

### 5.16 量一个件的真实占据范围：先看 `Shape`（★ Phase 85，§0.18 第三张脸）

`Size` 有三种坏法，**全都安静**：**旋转过**的件要逐轴投三根基向量（§0.18）；
**非 Block** 的件**根本没有那个尺寸**（本条）；**分组汇总**会把错的压得很合理。

```lua
local function extents(p)                       -- 世界轴上的真实占据范围
    local s, R, U, L = p.Size, p.CFrame.RightVector, p.CFrame.UpVector, p.CFrame.LookVector
    if p:IsA("Part") then
        -- Ball: 直径 = min(Size)，三个分量都等于它。Cylinder: 轴长取一个分量、
        -- 直径取另两个的 min —— Roblox 取的是 min(Size.Y, Size.Z)，轴沿局部 X。
        local d = math.min(s.X, s.Y, s.Z)
        if p.Shape == Enum.PartType.Ball then
            s = Vector3.new(d, d, d)
        elseif p.Shape == Enum.PartType.Cylinder then
            s = Vector3.new(s.X, math.min(s.Y, s.Z), math.min(s.Y, s.Z))
        end
    end
    return Vector3.new(
        math.abs(R.X)*s.X + math.abs(U.X)*s.Y + math.abs(L.X)*s.Z,
        math.abs(R.Y)*s.X + math.abs(U.Y)*s.Y + math.abs(L.Y)*s.Z,
        math.abs(R.Z)*s.X + math.abs(U.Z)*s.Y + math.abs(L.Z)*s.Z)
end
```

**证据长什么样**：`Size=(0.5, 46, 35)` 的 `Shape=Ball` 是**一颗 0.5 stud 的弹珠**，
不是一块 46×35 的板。**判据**：把它染成一个刺眼的颜色再拍一张 ——
显出的是**一圈细环**（1 stud 的盘被 0.9 的盘盖住）而不是一块铺满画面的板，量法当场作废。
**别用「再读一遍属性」自证**：读的是同一个错前提，两次都错也会一致。

**顺带**：`Size` **不随 `Shape` 变**。`(0.5,46,35)` / `(0.45,41.4,31.5)` 这种「板尺寸 + Ball 形状」的
组合是**改形状的化石** —— 死参数是线索，能反推原设计，不是噪声。

### 5.17 桥的一头是**一个已经存在的环**：`annulus` + 删端面 ★ Phase 86

§5.15 拿 `trg.revolve` 做两头。**如果一头是场景里已经有的那圈墙**（Phase 86 的那种），
`revolve` 就用不上了：它把一条**开环剖面**车一圈、**每端封一个 n-gon**，
而**环的端面是一个「带孔的 n-gon」** —— 没有任何单个多边形是那个形状。
所以端面必须**自己铺 n 个四边形**，这也正好让「删掉端面」变成一个定义清楚的操作：
删完**剩两条开环**（外环和内环），正是桥要的东西。

```python
def annulus(bm, n, a_out, a_in, z0, z1):
    """A closed n-sided tube: outer wall, inner wall, and a ring at each end."""
    o0, o1 = ring(bm, n, a_out, z0), ring(bm, n, a_out, z1)
    i0, i1 = ring(bm, n, a_in,  z0), ring(bm, n, a_in,  z1)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))    # 外壁
        bm.faces.new((i0[k], i0[j], i1[j], i1[k]))    # 内壁
        bm.faces.new((i0[k], i0[j], o0[j], o0[k]))    # z0 那圈的端面
        bm.faces.new((i1[k], i1[j], o1[j], o1[k]))    # z1 那圈的端面
```

**半径从 apothem 反解，不要反过来**（`r = apothem / cos(pi/n)`）：邻居在场景里**摸到的是侧面**，
量到的那个数就是 apothem。从 circumradius 出发，两条环就会在顶点处碰上、在每边中间留一条缝 ——
**看起来像是「差一点点」的那种错**。

```python
# 「全部顶点都在这个高度」而不是「任一顶点」：侧壁的两端也碰 z0/z1，
# 按「任一」选会把壁也选走，然后模型变成一条没有壁的带子。
def end_faces(bm, z, tol=1e-6):
    return [f for f in bm.faces if all(abs(v.co.z - z) < tol for v in f.verts)]
```

**四条会复发的：**

1. **环可以有好几条，先数再桥。** `rim_loops(bm)` 数出 `[18, 18, 24, 24]`——
   **四条**，不是两条（外壁和内壁各来一条）。不对就 `SystemExit`，
   `bridge_loops` 喂错配对照样还你一个合法网格（**DECISIONS 267**）。
2. **给环命名：先按高度，再按半径。** 两个高度是唯一的；半径在 24 边那一侧很近
   （内环 64.55 vs 外环 68.59），认错是静默的。
3. **配对要断言「同侧」。** 外环去接内环也是 84 个三角形、也闭合、也是单壳 ——
   只有面**在哪**能分辨。所以每个带面必须**同时含一个 18 编号的点和一个 24 编号的点，
   且后缀相同**：
   ```python
   e18 = [t for t in ts if t.startswith("18")]; e24 = [t for t in ts if t.startswith("24")]
   ok = e18 and e24 and e18[0][2:] == e24[0][2:]
   ```
   变异 `--wrong-pair` 只让这一行红（84 bad）——**最有判别力的那个变异**。
4. **`--no-bridge` 会让「不扭」那一行一起红，但红在「带子是空的」上**（min 打印 `-1.0`），
   不是红在扭上。**红了要问红在什么上**（DECISIONS 205/270）。

**顺带一条**：同一个 FBX 镜像 `(bx,by,bz) → (−bx,bz,by)` 会不会打乱相位，**取决于多边形的对称群**。
18 边（20° 一步）和 24 边（15° 一步）的顶点集**都对 180° 旋转不变** → 镜像后是同一个集合 →
**导入不用转**。**偏移 7.5° 的 24 边就不行**。写「不需要修正」时要把对称群一起写下来。

**第五、六条属于「设计」不属于「算子」，但它们是这个形状真正难的地方：**
量出来的数（apothem / 相位 / 平台高度）和挑的数（外圈 apothem、各段高度）
**在代码里必须长得不一样**，否则下一个人调比例时会顺手把读数一起调了（**DECISIONS 274**）；
倒角要**关掉**不是调小 —— 过渡带倾 55°，`finish()` 那个 25° 过滤器会吃掉全部 84 个三角形
（**DECISIONS 276**）。

**消费端那条（上色脚本）**：判断「这一件是哪一段」用**尺寸比例**，而**归一化必须各自除以自己** ——
两件都除以「场景里最宽的那件」只在**导入恰好是设计尺寸**时才抵消（**DECISIONS 275**）。
上面这几条都在 `PROGRESS.md` Phase 86。


---

### 5.18 在 Studio 里从零建一个 MeshPart（**不需要上传凭据**），以及它的碰撞体代价 ★ Phase 87

**问题**：`ROBLOX_OPEN_CLOUD_API_KEY` 没设，`upload_asset` 走不通，于是「Blender 建好、人手动拖进 Studio」
是唯一的路 —— 而那条路**已经被用户否掉了**：**「你自己在 studio 里面做，我这里人工调整肯定不准确」**（他拖过一次，
结果偏 1.0769 倍、接缝差 3 stud）。

**答案**：`AssetService` 有一条**不上传**的路。网格作为**对象**存在这个 place 里
（`Content.SourceType = Object`，`serialization.can_save` 为真），不经过 asset 服务器，**不要凭据**。

```lua
local AssetService = game:GetService("AssetService")

local mesh = AssetService:CreateEditableMesh()
local ids = {}
for i, v in ipairs(verts) do
    ids[i] = mesh:AddVertex(v)                 -- Vector3 -> int64 顶点 id
end
for _, t in ipairs(tris) do
    mesh:AddTriangle(ids[t[1]], ids[t[2]], ids[t[3]])
end

local ok, mpOrErr = pcall(function()
    -- CreateMeshPartAsync 是 Yields 的，而且会抛错（尺寸/内容不合法时）
    return AssetService:CreateMeshPartAsync(Content.fromObject(mesh))
end)
if not ok then
    mesh:Destroy()
    error(mpOrErr)
end
local mp = mpOrErr
mp.Name = "ChamberWall24"
mp.Anchored = true
mp.CFrame = CFrame.new(CENTRE)   -- 网格局部 (0,0,0) 就是 pivot，不重新原点化
mp.Parent = workspace
mesh:Destroy()                   -- Content 已经握着它了，克隆出来的这份可以丢
```

**两条与导入器实质不同的性质**（都用上了，不是巧合）：

1. **不重新原点化。** `MeshSize == Size`，局部 `(0,0,0)` **就是** pivot。
   所以 `CFrame.new(CENTRE)` 精确把「网格里 y=0 那个环」放到 CENTRE。
   （导入器相反：Phase 83 里 `Model:GetPivot()` 在导入模型上直接不可用，
   每个 MeshPart 的 `Position` 既不是节点原点也不是它自己的包围盒中心。）
2. **建之前就能自检。** 顶点/三角形还没交给引擎时就能断言
   （计数、每条有向边恰好一次、每条无向边恰好两次、欧拉特征、有向体积），
   `AddTriangle` 拒掉退化面。**这比事后量便宜得多。**

**唯一可信的读回**：`MeshPart.MeshContent` -> `AssetService:CreateEditableMeshAsync(content)`
-> `GetVertices()` / `GetPosition(id)`。这是**往返**，不是自证。
（**2026-10-10 更正，Phase 110**：这条**只在拥有那个对象的那个进程里**成立。
换一个进程，同一句调用**不报错**，而是回你**一个单位立方体**（1536 顶点、跨 `(0,0,0)..(1,1,1)`）——
`SourceType = Object` 的网格是**进程局部**的，不跨网络。所以在别人的进程里，
「读回一个网格」和「读回**那个**网格」在类型上同形。取舍 **449/450**，见 **§5.25**。）
**不要用射线验形状** —— 见下面的代价。

**代价：碰撞体。** `MeshContent.SourceType = Object` 的 MeshPart 上，
`CollisionFidelity` **写不进去**：Default / Hull / PreciseConvexDecomposition / Box
四个值**四次赋值全部 `pcall` 返回 ok、四次读回 `Default`**，re-parent 无效。
**对照证明这不是 Studio 的锅**：邻座 `SourceType = Uri` 的导入件接受同一个写。
所以碰撞面**永远是凸包**。环面的凸包是**实心圆盘** —— 一块 137.17 stud 的盘会把腔室封死。

```lua
-- 交付态：一面「走得过去」的墙，好过一座「进不去」的腔室。
-- 两个都是谎，选小的那个 —— 而且把原因写在这里，不只是写进报告。
mp.CanCollide = false
mp.CanQuery  = false   -- 只关 CanCollide 是把物理关掉了、把它留给了查询
```

**什么时候值得走这条路**：形状是**程序化**的（从常量算得出来）、**不需要碰撞**（装饰、视觉延续）、
而且**导入器那条路已经证明不准确**。**什么时候不值得**：需要精确碰撞，或者需要 UV / 贴图
（EditableMesh 的这条写入路径不含材质映射）。

**顺带两条纪律**（都在 `DECISIONS_2` 279..285）：
会**写**世界的探针必须还原成**它找到的值**（不是它想要的值）；
**永远不可能通过**的检查是噪音 —— 原来那条「Precise 让腔室保住开口」永远红，
改成写**发现** + 两条真正可能失败的断言。

**这条路是有出路的**：同一面墙改用**普通 Part** 拼，外形与碰撞就由同一批件负责了，
而且射线从此能量到真几何 —— 见 **§5.19**（`## Phase 88`）。

---

## 5.19 用普通 Part 拼一个正多边形壳（union 精确等于壳），以及斜接带的面板 ★ Phase 88

§5.18 讲的是「在 Studio 里从零建 MeshPart」那条路，末尾是它的**代价**：碰撞体永远是凸包。
这一节是那条代价的**出路** —— 同一面墙改用普通 Part 拼，**外形与碰撞由同一批件负责**。
（触发它的是一个测出来的事实：那面墙是**整个邻里唯一不参与物理**的一件，
环 19/19、与它重叠的 60/60 全是实心 —— 「保守」在这里等于「玩家能穿过去」。）

### 一条不显然的恒等式

**正 n 边形壳的一个面 = 一个 Box**，只要弦长取满：

```lua
-- 外层在 apothem a 的多边形面上，内面平行，厚度 WALL
local half  = math.pi / n
local chord = 2 * apothem * math.tan(half)   -- ★ 取满，不是取小一点
local rMid  = apothem - WALL * 0.5           -- Box 中心在自己面的法线上
for k = 0, n - 1 do
    local phi = k * 2 * half
    local nrm = Vector3.new(math.cos(phi), 0, math.sin(phi))
    -- CFrame.Angles(0, yaw, 0) 把局部 +Z 送到 (sin yaw, 0, cos yaw)
    -- 我们要 +Z = 向外的法线，所以 yaw = pi/2 - phi
    local p = Instance.new("Part")
    p.Shape = Enum.PartType.Block
    p.Size  = Vector3.new(chord, height, WALL)
    p.CFrame = CFrame.new(CENTRE + nrm * rMid + Vector3.new(0, yBase + height * 0.5, 0))
             * CFrame.Angles(0, math.pi / 2 - phi, 0)
    p.Anchored, p.CanCollide, p.CanQuery = true, true, true
    p.Parent = model                            -- CFrame 必须在 Parent 之前（§0.19）
end
```

**弦取满时，两个半弦正好够到多边形的顶点**，于是相邻面板在顶点处**恰好相接**、
在内侧轻微重叠 —— **一圈面板的并集就是这个多边形壳本身，角也在内**。
不用楔形补角、没有缝、也不外凸。

弦**不取满**（环 `18` 自己取的是 `20.705`，真弦 `22.468`）就会在每个顶点留一个 V 形缺口，
得靠一块 `UnionOperation` 盖板补 —— 那是另一种做法，**不是错的，但要知道自己选的是哪种**。

**两条提醒：**

- `CFrame.LookVector` 是 **−Z**（相机约定）。把它当「向外的法线」用，
  法线会**指向轴心**，而所有 apothem 检查**照样全绿**（量的是半径，不看朝向）。
  要用 `CFrame.ZVector`，并且另写一条 `dot2(ZVector, radial) > 0.999` 的检查。
- **角的相位**：`rem = phi % step; err = min(rem, step − rem)` —— 负方位角在 Lua 里
  向下取整是对的，不用自己加圈。

### 斜接带：同一种盒子，旋转 + 厚度换成**垂直厚度**

内外两个表面是两条**平行线**，所以厚度是**垂直距离**，不是水平间距：

```lua
local lean = math.atan2(dR, dY)            -- 0 = 竖直，pi/2 = 水平
local uR, uY = dR / len0, dY / len0        -- 沿斜面，向外向上
local uR_, uY_ = -uY, uR                   -- 垂直斜面，向内向上
local thickness = WALL * math.cos(lean)    -- ★ 4.00 * cos(55.02) = 2.2930，不是 4.00
```

写成 `WALL` 会让带**厚出 74%**。
端面**垂直于斜面**，所以上端面从 `(A_outer, y_top)` 往**内上**方走 ——
**外缘恰好止于墙脚**时端面永远不超过墙的外表面。这是设计约束：
外缘越过墙脚，斜带就会在墙面外露出一圈薄毛边，**而所有量 apothem 的检查一条都不会红**。
下端**故意沿斜向往 collar 里塞 0.60**，把接缝从一条刀刃变成一段搭接。

### 交付数字一律实测，不手算

接缝处的台肩：**手算 0.434、实测 0.3002**。
手算错在拿两个**多边形顶点**相减 —— 面板是**盒子**，它的角在切向上**悬出**那个顶点
（带宽按**顶端** apothem 取，在底端该窄 1.13）。同一份手算里的**另一项**
（带追上该角的高度 0.5153 vs 实测 0.520）却几乎全对，因为它算的是**面中心方向**，
那里没有悬出 —— **同一个几何量，一个方向对、一个方向错**（§0.18 的家族）。

手算是用来**定形状**的；**交付数字一律实测，两个都写下来**，错的那个写在实测旁边。

### 换法子的收益：终于能被射线量了

射线打的是**碰撞体**。MeshPart 那条路上，射线只会打到那个 137 stud 的凸包盘，
**量不到形状**；Part 这条路上**几何体就是碰撞体**，于是这些检查第一次有意义：

```lua
-- 7 个高度 × 720 方位各打一条向内的射线，一条都不许漏 —— 壳闭合
-- 某高度向内打，落点半径应当等于该高度的设计 apothem
-- 中间那根半径（rho 55）必须 MISS —— 否则腔室被堵死了
```

实测：**5040/5040 无漏**、collar 停在 63.7120（设计 63.7120）、wall 停在 68.0000、
墙顶在 y 60.6000、rho 55 **MISS**、66/66/66 `CanCollide`/`CanQuery`/`Anchored`。

### 四条附带纪律

1. **有自检再让它进世界。** 建完先按**Part 自己的 `CFrame`/`Size`**（而不是建它用的变量）
   跑一遍全部断言，不过就 `Destroy()` 并在返回值里说明。
2. **守卫要守不可逆的那一步，不是「这脚本跑过」。** 存档 idempotent：
   只有「世界里还有待存的东西 **且** 存档名已被占」才拒绝。
3. **同名的旧件搬走、不删** —— 它是**已验过的那一版**（`ServerStorage.<name>_<date>`）。
4. **接缝要在两侧各量一次**，用**同类仪器**：环自己量到 63.7114，
   新件量到 63.7120，差 **0.0006** —— 和自己比不算数，和**已经在那里的东西**比才算。

## 5.20 给一个**已经存在**的壳外面套一个正 m 边形，并证明接上了 ★ Phase 89

被接的是 `Workspace.Folder.Folder.Folder.18`（18 边形环），要套的是 24 边形墙。
用户的话是判据：「依据 18 那个 part 的**最外围**来扩，每三个 part 接 4 个墙壁，
这样就是 18\*(4/3) = 24」。

### 一、先把「最外围」拆成两个数，因为正 n 边形有**两个**半径

```python
RING_A = 63.7114    # MEASURED -- the face plane (apothem); 1440-ray inward sweep, rmin
RING_R = 64.6951    # MEASURED -- the corners (circumradius), same sweep, rmax
                    # RING_R / RING_A = 1.015439 ; 1/cos(pi/18) = 1.015427  <- agrees
WALL   = 4.00       # FREE -- how far the new wall stands out
```

`最外围` 是 **`RING_R`**。读成 `RING_A` 的话，环的 18 个角从新墙里戳出来（Phase 88 的错）。

### 二、内面平面放在 `RING_R`，而这是**最小**的（不是保守取大）

外接 m 边形（inradius `R`）包含同心正 n 边形（circumradius `R′`）**当且仅当 `R ≥ R′`**：

```python
A24_IN  = RING_R                    # 64.6951 -- touches the ring's corners at 0,60,...,300
A24_OUT = A24_IN + WALL             # 68.6951
```

另一条看起来更「整」的路**不成立**：把 24 边形的**顶点**放在环的角上 →
`a24 = 64.6951*cos(pi/24) = 64.1514`，于是方位 20° 的那个环角（64.6951）
从墙内面（64.2125）里**戳出 0.48 stud**。

### 三、3:4 在方位上：3×20° = 4×15° = 60°

```python
M, N = 24, 18
ring_corners = [0 + 360*k/N for k in range(N)]      # 0 + 20k
ring_faces   = [10 + 360*k/N for k in range(N)]     # 10 + 20k  (the panel centres)
wall_corners = [0 + 360*k/M for k in range(M)]      # 0 + 15k
wall_faces   = [7.5 + 360*k/M for k in range(M)]    # 7.5 + 15k
# one 60 deg sector: ring faces 3, wall faces 4; and 6 of the ring's 18 corners
# (0 + 60k) carry a wall corner. Both are COUNTED in the checker, not derived.
```

### 四、apothem 要按**壳自己的相位**取面法线去拟合

顶点在 `phase + 360k/n` 的正 n 边形，**面法线**在 `phase + 180/n + 360k/n`。
拿顶点方向投影，量回来的是 **circumradius**（一个响亮的错答案，§0.18）：

```python
def apothem(points, n, corner_phase=0.0):
    vals = []
    for k in range(n):
        a = math.radians(corner_phase + 180.0 / n + 360.0 * k / n)
        vals.append(max(p[0]*math.cos(a) + p[1]*math.sin(a) for p in points))
    return sum(vals)/len(vals), max(vals)-min(vals)   # (value, spread)

def fit_apothem(ring, n):
    """Anchored to the ring's OWN phase on purpose. A fit pinned to the world
    lattice answers 'the circumradius' when the ring is rotated half a step --
    a loud answer to a question nobody asked."""
    ph = sum(off_grid(azim(p), 360.0/n) for p in ring) / len(ring)
    a, spread = apothem(ring, n, corner_phase=ph)
    return a, spread, ph
```

`spread` 和值同等重要：它说这壳**是不是**正 n 边形（本机实测 0.0000）。

### 五、转**半格**过掉每一个半径检查 —— 所以相位只能锚在**被接的那件**上

正 n 边形转 `360/2n` 度：apothem、弦长、面积、轮廓半径**全不变**。
`collar 63.7120 对 ring 63.7114，delta 0.0006` **在相位差 10° 时照样通过**。
所以：

```python
w24_ph = phase_of(c24_in, M) + 180.0 / M     # the WALL's face normals
worst = max(rad(p)*math.cos(math.radians(
            abs(off_grid(azim(p) - w24_ph, 360.0/M)))) for p in ring_pts)
ok("J3 no ring vertex inside the wall", worst <= a24_in + TOL)
```

而「接上了没有」的**三条数**（本机实测）：

| 接缝 | 问题 | 实测 |
|---|---|---|
| **J1** | 墙的**内脚环**逐点等于环顶面的轮廓? | 最差顶点间隙 **0.00000 stud** |
| **J2** | 墙**内面平面** = 环的最外围? | **64.6951**（在环的面平面处让开 0.9837）|
| **J3** | 环的每个顶点都在墙的**空腔**里? | 最坏 `r·cos` **64.6327** ≤ 64.6951 |
| **J4** | 60° 扇区里环 3 / collar 3 / 墙 4，且 6 个角对齐? | 全中 |

### 六、**两件载体交付同一个几何时，别数面** —— glTF 没有多边形这个概念

glTF 把每个面三角化，FBX 这条路回读也是三角化的，于是「42 个外面」
从一份文件读成 84、另一份读成 126 —— **两个数都是关于格式的，不是关于墙的**。
改成数**顶点**和**每张命名面的三角形数**（collar 外 = 36，墙外 = 48），两种格式才对得上。
跨格式比较前先**按位置焊接**（glTF 会把属性不同的角拆成独立顶点，
不焊就会把 `open_edges` 读成几百，而那是**关于问法的**）。

### 七、`--background --python` 的检查器：**崩溃的退出码是 0**

```python
try:
    for tag, name, loader in (("FBX", NAME + ".fbx", load_fbx),
                              ("GLB", NAME + ".glb", load_glb)):
        check(tag, os.path.join(OUT_DIR, name), loader)
    done()
except SystemExit:
    raise                      # done()/need() 自己的 sys.exit 要放行
except BaseException:
    traceback.print_exc()
    print("CHECK CRASHED -- treated as a failure")
    sys.exit(1)
```

实测（Blender 5.1.2）：`raise` → **rc=0**；`sys.exit(1)` → rc=1。
所以**没有这个 try，一次崩溃和一次全过在 shell 眼里逐字节同形**。
配合：空集合的两条反方向谎言（`all([])` 为真、`max(())` 抛）——
凡以「缺失的东西」为主语的断言，先 `bool(x)`。

变异要写成 `--python s.py -- --flag`；`--python s.py --flag` 会让 Blender
把 `--flag` 当成**要打开的文件**，然后**照常跑完**。

## 5.21 两个环之间的桥：**规格是别人给的**，所以断言要建在**面**上而不是面数上 ★ Phase 90

**场景**：用户把三角化逐条写下来（`A0-B0-B1` … `A2-B4-B3`，6 组 × 7 = 42），
外加「端面留作 n-gon」「端面蓝、桥接红」。产物是 Blender 参考件，不是 Studio 里任何东西。

**① 「9 个三角形」不够，要的是「**这 42 条关系**」** —— 42 是 Euler 逼出来的
（环面 `F = a + b = 18 + 24`），所以**任何** 6 组 × 7 的方案都满足 Euler：
Euler、闭合、体积**都不能**验证他给的表。能验证的只有把每条关系**重建出来当集合去找面**：

```python
def pos_of(ring, g, off):          # 组的编号就从这里进：小环 3g+off，大环 4g+off
    z, r, n, base = ((Z_SMALL, R_SMALL, N_SMALL, 3*g) if ring == "A"
                     else (Z_LARGE, R_LARGE, N_LARGE, 4*g))
    a = 2.0 * math.pi * ((base + off) % n) / n
    return (round(r*math.cos(a), 5), round(r*math.sin(a), 5), round(z, 5))

lookup = {pos: i for i, pos in enumerate(pts)}          # 按**位置**，不按索引：
for g in range(GROUPS):                                 # 焊接会把索引全洗掉
    for rel in BRIDGE:
        want = {lookup[pos_of(r, g, o)] for (r, o) in rel}
        assert any(set(f) == want for f, _ in faces)    # 逐条关系都必须是一张面
```
`--fan`（改用 `bmesh.ops.bridge_loops` 自己配）**红的正是这一行** —— 它给出的 42 个三角形
**合法、闭合、体积更接近正确**，只是**不是他那 42 条**。**这就是这条断言存在的唯一理由。**

**② 面**分类**绝不能按边数** —— 那是在回答**文件格式**：
glTF 没有多边形类型，端面在 `.glb` 里是 16 + 22 个三角形，于是 `len(f) == 3`
把 38 个端面三角形一起数进来 → 「42 个桥接三角形」读到 **80**。**按 material slot 分类** ——
slot 两个格式都有，而且它本来就是第 6 条在说的事。同理「44 个面」要改问
**三角化后的三角形数** `Σ(len(f) - 2)`（两格式都是 80）。

**③ 「端面是 n-gon」只能在 `.blend`/FBX 里问原话，导出件问**面积和角集**：
```python
ok("the z=0 end face spans all 18 corners", used_lo == ring_lo)
ok("the z=0 end face has the 18-gon's area",
   abs(planar_area(pts, cap_lo) - ngon_area(N_SMALL, R_SMALL)) < 1e-4 * want)
```
一个**残缺的扇面**照样是「端面那个材质的面」——**数面数抓不到它，面积和角集抓得到**。
（实测：FBX 留 `1 + 1` 个 n 边形，GLB 是 `16 + 22` —— **两种格式交付的不是一个东西**。）

**④ 按方位分区，先把方位**吸附到环自己的角格**再除**：
```python
def corner(n, p):                       # n = 环的边数
    return int(round(azim(p) / (360.0 / n))) % n
# 第 g 组：小环 3g..3g+2，大环 4g..4g+3
```
`azim(p) // 60` 和 `round(azim(p) / 60)` **都错**：15° 间距整除 60° → 角**正落在边界上**，
`atan2` 对「标称 60°」回 59.999999，而 Python 的 `round()` 是**银行家舍入**（`round(1.5) == 2`）
→ 实测读出 `[3,4,5,3,5,4]`。吸附留 ~10° 余量，浮点是 ~1e-5。

**⑤ 颜色的断言要**读回文件里的字段**：Workbench 渲染读 `mat.diffuse_color`，
导出器写的是 Principled 的 `Base Color` —— **两个字段**。读回时优先取后者、退前者：
```python
for n in mat.node_tree.nodes:
    if n.type == "BSDF_PRINCIPLED" and "Base Color" in n.inputs:
        c = n.inputs["Base Color"].default_value; return (c[0], c[1], c[2])
return mat.diffuse_color
```
**否则一张看着全对的图救不了一个导出成白色的材质。**

**⑥ 变异要覆盖每条规格**，其中 `--swap-rgb`（只换颜色，不换面用哪个 slot）**是专为颜色那条加的** ——
`--swap-mats`（换面用哪个 slot，颜色不变）**逼不红**它。**专为它造一个变异，别让那条断言装饰着。**

## 5.22 量「一个声部比其它一切响多少」：底必须**定义上**不含它 ★ Phase 95

一个「余量」是 `A - B`，而**分母是选出来的**。这里的三条，任何「减去背景」的量法都用得上。

**① 底不能是「混合减去被测对象」—— 那减掉的是它的第二份拷贝。**
我的编曲把 lead 混进 `mix` 之后，`mix - lead_isolated` 里剩下的**还有 lead 本身**。
正确做法是让**装配**给你一个定义上无 lead 的底。前提是装配对电平**线性**：

```python
NONE_ = ms.assemble(ms.with_lead(base, 0.0, 0.0))   # 定义上无旋律的伴奏
DRY_  = ms.assemble(ms.with_lead(base, ms.LEAD_DRY, 0.0))
WET_  = ms.assemble(ms.with_lead(base, 0.0, ms.LEAD_SEND))
LEAD_ = [DRY_[i] - NONE_[i] + WET_[i] - NONE_[i] for i in (0, 1)]
```
（**干**与**湿**分开装配再相减，是因为 wet 会进混响总线；直接 `assemble(base)` 会把
混响也算进「其余一切」里。）

**② 功率：先把信号加起来，再量。** 两个**分别**量的带功率之和 ≠ **和的**带功率 ——
干湿在音符自己那条带里**相关**，这里差 **约 3 dB**。
**「两半不相关」是你不知道、也不该假设的那件事。**

**③ 幂等，否则双倍。** `with_lead` 返回的表里 lead 已清空，所以 `assemble` 自己调它时
不会再叠一次：

```python
def with_lead(stems, dry=None, send=None):
    d = LEAD_DRY if dry is None else dry
    s = LEAD_SEND if send is None else send
    return dict(stems, mono=stems["mono"] + d * stems["leadD"],
                send=stems["send"] + s * stems["leadS"],
                leadD=np.zeros(len(stems["mono"])), leadS=np.zeros(len(stems["mono"])))
```

**④ 缓存里存的是**单位电平**的那个声部，电平在装配时施加一次。**
否则改了电平再 `--reuse`，**渲染、母带、检查、回放全都完美，而送出去的是旧电平**
（§0.15 那一族最难认的一张脸，取舍 331）。
配一条护栏：旧缓存缺 `leadD` 时**直接报错说清楚怎么修** ——
不要让它被容忍过去，产出一首**什么都正常、就是没有旋律**的曲子。

**⑤ 窄带 / 宽带是两个问题。** 窄带（基频 ±1/6 八度）问「听不听得出音高」，
宽带（基频到 4×）问「听不听得出这个乐器」。
实测：旋律可能**谐波不低而基频很低**（读成织体、不读成曲调），所以两条都要报。

## 5.23 把**误合并**的容器按索引拆回去：护栏 + 拆完再量几何 ★ Phase 96

一个「把同名的根并进一个」的坏循环留下的容器，可以**按索引**拆回去 ——
**前提是每一条边界都能先证明**。这比「看起来对」重要，因为**拆错就是又一次不可逆的搬运**。

**① 三条护栏，任何一条不过就整个 `return`（一个孩子都不动）：**

```lua
local function split(nm, cuts, ownParts, ownFirst)
    local rs = {}
    for _, c in ipairs(W:GetChildren()) do if c.Name == nm then table.insert(rs, c) end end
    table.sort(rs, function(a, b) return np(a) > np(b) end)     -- 最大的那个是被合并的目标
    local big, kids = rs[1], rs[1]:GetChildren()
    local empties = {}
    for i = 2, #rs do if np(rs[i]) == 0 then table.insert(empties, rs[i]) end end

    local total = 0
    for _, n in ipairs(cuts) do total = total + n end
    if total ~= #kids then return end                    -- ① 各块之和 = 孩子数
    -- …逐块量部件数与包围盒…
    if got[1] ~= ownParts then return end                -- ② 孩子还在追加顺序上
    if #empties < #blocks - 1 then return end             -- ③ 有足够的同名空壳接住
    for i = 2, #blocks do
        for _, k in ipairs(blocks[i]) do k.Parent = empties[i - 1] end
    end
end
```

**② 拆完必须再量一次几何 —— 护栏只管算术。** 四个分块要**真的是四段相邻的几何**
（`x163..178 / 178..193 / 193..208 / 208..223`，15 stud 一段首尾相接），
而不是四个各占一角的杂乱集合。实测：

```
MainHallwaySegment   9 roots, big 224 孩子 / 1827 件, 空壳 3 → 459 + 456×3 = 1827 ✓
HallwayRoomConnector 8 roots, big  74 孩子 /  102 件, 空壳 2 → 20 孩子 48 件 + 27 + 27 ✓
```

**③ 「同名空壳」是被合并方的残骸，也是接住它的容器。** 空壳**不要删** ——
它们带着 `ParkedName`/`UnparkedAt` 属性，**`Model:GetPivot()` 在孩子被移走后仍然有效**，
是唯一还能指出「丢了哪一份分组」的东西（取舍 336）。

**④ 不是所有容器都能拆。** 当一个容器的**名字本身就没有信息**（45 个根**全叫 `Model`**）、
零件上**没有任何父属记录**、只剩一堆**彼此只隔 2–15 stud** 的 pivot 时 ——
最近的分配会跑通、会给出 45 个大小合理的容器、**什么都不报错**，而它**大概率是错的**。
**那是「挑的数」，不是「量出来的数」**（取舍 274/340）。**这一格只能披露，不能补。**


## 5.24 用 **EditableMesh** 建一个逐顶点驱动的效果（旧 API 的间接层 + 两个上限 + 字节级交货）★ Phase 109

一个会自己变形的东西：`AddVertex` / `AddTriangle` 建一次拓扑，之后**每帧只改 `SetPosition`**。
三条能让它一次跑通的东西，和三条骗过我的东西。

**① 这台 Studio 是**旧的、按 id 间接**的一套 API —— 每一个名字先用 `pcall` 试，并打报错原文。**
`EditableMesh` 在这里是 **datatype**（`typeof(em) == "Object"`），不是 Instance：
探一个不存在的成员**不是回 `nil`，是抛错**，所以 `if em.Thing then` 这种写法自己就是那一次错误。

```lua
local ok, res = pcall(function() return em.SetVertexColor end)
-- ok == false，而 res 是 "SetVertexColor is not a valid member of EditableMesh"
```

量到的面（2026-10 实测）——**有**：`AddVertex(Vector3)->vid`、`AddTriangle(v1,v2,v3)->fid`、
`GetFaceColors(f)->{cid,cid,cid}`、`SetFaceColors(f,{cid,cid,cid})`（**表**，2 实参）、
`SetColor(cid, Color3)`、`GetColor(cid)`、`SetPosition(vid,Vector3)`、`GetPosition(vid)`、
`GetVertices`、`GetFaces`、`GetFaceUVs`、`SetFaceNormals`、`SetUV`/`GetUV`、`SetNormal`/`GetNormal`、
`Triangulate`、`GetSize`、`Clear`、`Destroy`、`AddColor(Color3, alpha)->cid`。
**没有**：`SetVertexPosition`、`SetVertexColor(s)`、`GetVertexColor`、`SetColors`、`SetUVs`、
`SetVertexNormals`、`RemoveVertex`、`RemoveTriangle`、`GetTriangles`、`GetVertexCount`、
`GetFaceCount`、`HasVertex`、`HasFace`、`Clone`。

**② 颜色 id **算不出来**，而且**按顶点共享** —— 建面的那一刻就要收下来。**
`f1=(a,b,c)` 拿到 889/890/891，`f2=(b,d,c)` 拿到 890/892/891（同一个 `b` 还是 890）。

```lua
local colourOf, conflicts = {}, 0
local function link(a, b, c)
    local f = em:AddTriangle(a, b, c)
    local cols = em:GetFaceColors(f)          -- 只有此刻问得到
    local vs = { a, b, c }
    for k = 1, 3 do
        local prev = colourOf[vs[k]]
        if prev == nil then colourOf[vs[k]] = cols[k]
        elseif prev ~= cols[k] then conflicts = conflicts + 1 end
    end
end
```
`conflicts` **必须**到构建末尾报出来：它是「按顶点」这个前提**唯一**会被证伪的地方，
而证伪了画面**照样对**（每面一个顶点色，肉眼分不出）。

**③ 两个上限先量再用，且**绑定的是三角形那一条**。** 顶点 **60000**、三角形 **20000**；
按面留余量，`build()` 开头用**具名常量**挡住，错的要是自己的话：

```lua
local CAP_VERTICES, CAP_TRIANGLES = 60000, 20000
if wantTris > CAP_TRIANGLES then
    error(string.format("topology asks for %d triangles, the cap is %d", wantTris, CAP_TRIANGLES))
end
```
交付拓扑 `RINGS=64 × SPOKES=152` = 9728 顶点 / **19152 面**（离 20000 有 848）。

**④ 「动态」= 每帧改顶点；渲染跟、物理不跟 —— 所以整件不参与碰撞。**
Roblox 文档：`SetPosition` 当场改渲染，碰撞是**快照**，要 `CreateMeshPartAsync` + `ApplyMesh` 才更新。
一个会挡射线、会撞人的「黑洞」是**改玩法**（§1.4 第 1 条），所以交付成
`CanCollide=false` / `CanQuery=false` / `CastShadow=false`。

**⑤ 造 MeshPart 不需要上传凭据**（§5.18 的同一条）：

```lua
local mesh = AssetService:CreateEditableMesh()
build(mesh)
local mp = AssetService:CreateMeshPartAsync(Content.fromObject(mesh))
mp.Anchored = true; mp.CanCollide = false; mp.CanQuery = false; mp.CastShadow = false
mp.Material = Enum.Material.Neon; mp.DoubleSided = true; mp.Size = CFG.SIZE
mp.CFrame = CFrame.new(CFG.ORIGIN, CFG.ORIGIN + CFG.FACING); mp.Parent = workspace
```
**唯一可信的读回是** `MeshPart.MeshContent -> CreateEditableMeshAsync(content)`（这一轮 `worstPositionDelta 0`）——
（**2026-10-10 更正，Phase 110**：这条**只在拥有那个对象的那个进程里**成立。
换一个进程，同一句调用**不报错**，而是回你**一个单位立方体**（1536 顶点、跨 `(0,0,0)..(1,1,1)`）——
`SourceType = Object` 的网格是**进程局部**的，不跨网络。所以在别人的进程里，
「读回一个网格」和「读回**那个**网格」在类型上同形。取舍 **449/450**，见 **§5.25**。）
`CollisionFidelity` 在 Object-content 的 MeshPart 上**写不进去**，所以别指望它。

**⑥ 把源码搬进 Studio 并按**字节**核 —— 长度 + 校验和，从不只比长度**（§0.17：这条走官方 `rblx_execute_luau`）**：

```lua
local ok, src = pcall(function() return game:GetService("HttpService"):GetAsync(url) end)
-- 官方 VM 里 ok=true, type=string；第三方插件 VM 里 GetAsync 是桩（§0.17）
local sum = 0
for i = 1, #src do sum = (sum * 33 + string.byte(src, i)) % 4294967296 end
-- 与盘上 Python 算的同一条式子在 rc 里逐位比
```
盘上那一侧（同一个式子的 Python 版）：
```python
s = 0
for c in open(p, "rb").read():
    s = (s * 33 + c) % 4294967296
```
**跑它**用 §0.15 的现成解法：`Clone()` 到一个临时 `Folder` 再 `require`（新实例 = 新缓存项 = 重新编译），
用完 `Destroy()`；**并**把启动块包进 `pcall`，把 `M.bootError` **写进模块**再 `warn` ——
否则 `require` 只回一句 `Requested module experienced an error while loading`，
**它指的是调用者，不是出错的那一行**。这一轮正是靠它一秒看到真正的原因是
`Triangle count above limit`（那条上限我那时还没量）。

**⑦ 证明「动」：一对只有时钟不同的图，外加从色场渲出来的 PPM。**
`camPos` / `partPos` / 部件 / **模块实例**（用持久 holder `require` → 命中缓存）全钉死，
只让 `clock` 5.75 → 17.25，然后**用 `compare_images` 比**，不用眼睛下结论。渲染图之外再渲一张**颜色场**：

```lua
local function pushPPM(url, n)          -- 色场，不是渲染图：绕开材质/光照/后处理
    local rows = { "P3", n .. " " .. n, "255" }
    for y = 1, n do
        local t = {}
        for x = 1, n do
            local r, g, b = sourceColour(...)   -- 直接问颜色函数
            t[#t+1] = string.format("%d %d %d", r*255, g*255, b*255)
        end
        rows[#rows+1] = table.concat(t, " ")
    end
    HttpService:PostAsync(url, table.concat(rows, string.char(10)))   -- §0.10：一个反斜杠都不写
end
```
`receive.py` 那一侧记 `RECV <name> <bytes> <crc32>`，两边 CRC **逐位相同**才算到（`0fa36841` @200²、
`42393a69` @300²）；PNG 由纯 stdlib 的 `_tools/ppm_to_png.py` 转 —— 它零依赖，
**所以 `-I` 底下也跑得动**（下面 ⑨ 那条：这台机器**有** Pillow，`-I` 把它藏起来了）。

**⑧ 一个恒为黑的采样点，是「这条检查没在测东西」的唯一信号。** 第一版 `verify` 拿第 1 环比颜色 ——
那是阴影中心，源色和比对函数**同时趋近 0**，于是断言恒真（§0.13）。改成沿 1,6,11,… 环展开，
并**报最亮的采样值**（`brightestSample 2.148`）；`worstColourDelta 0.0029` 是 mesh 的 **8 位量化**，不是缺陷。


**⑨ 「这台机器没有 Pillow」是**我说的，而且是错的** —— `-I` 把它藏起来了（取舍 448）。**
`python -I -c "import PIL"` -> `ModuleNotFoundError`；`python -c "import PIL"` -> **`PIL 12.3.0`**。
落点是**用户级** site-packages（`%APPDATA%\Python\Python314\site-packages`），
而 **`-I` 正是把用户 site 从 `sys.path` 摘掉的那个开关**（本仓库的每条 Python 命令都带它，
为的是防别人种下的 `import json`）。**`-E` 单独用没事，`-s` 单独就能复现**；`numpy` 在同一个目录，同样被藏。
判「有没有这个包」**两个解释器各问一次**，不一致就说明是**标志**藏的。
（`_tools/ppm_to_png.py` 仍然留着纯 stdlib —— 那反而是更好的性质：它在 `-I` 底下也跑得动。）


---

## 5.25 用 `EditableMesh` 做的东西必须**在画它的那个进程里建** —— `SourceType = Object` 不跨网络 ★ Phase 110

**症状（操作员原话）：** 「为什么我进测试之后透镜变成一个小方块」。

**量到的原因。** 同一个实例、同一句 `AssetService:CreateEditableMeshAsync(part.MeshContent)`：

| 在哪个进程 | `GetVertices()` | 包围盒 |
|---|---|---|
| 建它的那个（Edit） | **9728** | `(-46.00 -46.00 -11.00) .. (46.00 46.00 -0.70)` |
| 别处（Play 客户端） | **1536** | `(0.000 0.000 0.000) .. (1.000 1.000 1.000)` |

1536 顶点、跨 1.0 —— **一个单位立方体**。而新建的 `CreateEditableMesh()` 是 **0 顶点 0 面**，
所以 1536 **不是空网格、不是错误**，是引擎给的**替代品**；渲染器再把它画成**棋盘格占位**、
尺寸按部件的包围盒（`92 x 92 x 10.303`）。**操作员看到的那块「小方块」就是这个。**

**结论：`Content.fromObject(editableMesh)`（`MeshContent.SourceType = Object`）活在创建它的那个进程的内存里。**
**服务端建的网格，客户端画不出来。**

```lua
-- 解药不是「把网格发过去」，是「在画它的那个进程里建它」。
-- 交付因此分成两份：一份源码（ReplicatedStorage 里的 ModuleScript），
-- 一个引导（StarterPlayerScripts 里的 LocalScript 去 require 它并 start()）。
-- 服务端那份 Script 删掉了 —— 它建出来的东西任何客户端都看不到。

-- 摆位可以从服务端/Edit 留下的静帧上读，但那份静帧本身对客户端是棋盘格，
-- 所以读完就收掉它，别留在世界让玩家看见。
local frame = workspace:FindFirstChild("GravityLens")
local cf = CFrame.lookAt(CFG.ORIGIN, CFG.ORIGIN - CFG.FACING.Unit)
if frame ~= nil and frame:IsA("BasePart") then cf = frame.CFrame end
local s = build(cf)                 -- 只建不删
if frame ~= nil then frame:Destroy() end
```

**能力闸：给不了网格的进程，别留一块棋盘格板子。**

```lua
local function meshApiUsable()
	local okCreate, em = pcall(function() return AssetService:CreateEditableMesh() end)
	if not okCreate then return false, "CreateEditableMesh refused: " .. tostring(em) end
	-- CreateEditableMesh() 在给不了的进程里返回 nil，而不是抛错（取舍 450）
	if em == nil then return false, "CreateEditableMesh returned nil" end
	local v = em:AddVertex(Vector3.new(0, 0, 0))
	em:SetPosition(v, Vector3.new(3, 0, 0))
	if math.abs(em:GetPosition(v).X - 3) > 0.0001 then
		return false, "wrote 3, read back " .. tostring(em:GetPosition(v).X)
	end
	return true, "ok"
end
```

**怎么在「游戏的 VM」里验它**（§0.17 的同一条，这一轮才补上）：
`execute_luau` 跑的不是游戏那个 VM，**交付路径必须自己跑过自己**。
在 `Players.LocalPlayer.PlayerScripts` 下放一个临时 `LocalScript` 让它自己测，
把结论写进 workspace 上一个 `StringValue`，插件 VM 再读**那个值**：

```lua
local out = Instance.new("StringValue")
out.Name = "LensReport"; out.Value = "booting"; out.Parent = workspace
local M = require(game:GetService("ReplicatedStorage"):WaitForChild("GravityLens", 30))
local s = M.start()
task.spawn(function()
	while true do
		task.wait(2)
		out.Value = string.format("passes=%d parent=%s err=%s",
			s.passes, tostring(s.part.Parent), tostring(M.stepError))
	end
end)
```

**摆位的坑（取舍 453）：** `cam.CFrame * CFrame.new(0, 0, -260)` **不是「相机前方 260 stud」**。
相机 look 向下 15 度时，它把东西放到**地下 67 stud**，而 `WorldToViewportPoint` 照样回
`onScreen = true` —— 在视锥里，只是在基板底下。用相机的**水平**方向
（`Vector3.new(look.X, 0, look.Z).Unit`）加一个**指定高度**。**投影在屏不等于看得见。**

**在跑起来的会话里量到的三条**：Play 里画出完整的透镜（两帧之间内环转过去了）；
`MeshContent` 往返两次相隔 1.2 s，最大位移 **0.0072 stud**（与 `SWIRL 0.30 rad / 23 s`、
喉部半径 `0.073` 推算逐位吻合）；`t+220 s`、约 6600 拍之后仍是完整透镜，
`CreateEditableMesh()` 预算恒 `ok`。

**没证的那一条（别把它写成机制）：** 我一度把「客户端自建透镜变棋盘格」归因于
「每帧全量重写 9728 个顶点太多」。**这一轮没有复现** —— `stride = 1`（每拍全量）与 `stride = 4`
各跑满约 4 分钟都是完整透镜。分片（`CFG.SLICE_STRIDE = 4`，每拍 ≤ 2432 次写入、
整张 0.13 s 刷新一遍）**留着当保险，不当必需**（取舍 451）。

细节 `PROGRESS.md` 110，取舍 **449..453**，`docs/SYSTEMS.md` **§2.19**，`docs/TODO.md` **§3.11.13**。


---

## 5.26 演奏一份 MIDI 的音符（+ 两把编错的尺子，和它们为什么必须**换掉**而不是调一下）★ Phase 112

上手 `_tools/music/midi_song.py`。三个可以单独抄走的片段，每个都配**它为什么长这样**。

### 一、源是**音符**时，「量出来的规格」长什么样

`analyze.py` 量的是**音频**，所以关于速度的一切都是猜的。MIDI 把答案当**数据**带着走
（division / tempo 事件 / 拍号 / note-on/off tick），所以它是**另一种尺子**：
它不估计那个格，**它就是那个格**。用它之前先做一次 `--compare`（`midi_grid.py`）——
两首不同的曲子也会共享一堆音级，所以问法要**先旋转再问空档**，不是直接问。

```python
# 每小节音符数 -> 段落标签：这个文件的形状是它自己说出来的，不是我定的
counts, lows, pcs = bar_stats(src, n_bars)   # 每小节 [音符数, 最低响音, 音级集合]
segs = sections(counts)                      # full / thin / sparse，相邻同类合并
```

**四个层全部照这条走**：结构 ← `counts`；踏板 ← 每四分格的 `lows`（贝斯根音）；
sub ← 每小节的 `lows`；pad ← 每小节的 `pcs`。
**做决定的那一行旁边，把被否掉的那条也印出来** —— 这样「我选了 A」当场就是**数**，不是一句话。

```python
say(lines, "  pedal rule: bass root -> %d changes; the sounding-set rule would"
           " give %d (rejected)" % (len(changes), len(other)))
```

### 二、两把**编错的尺子**，以及「换掉」的判据

两条都是**看起来会通过**的检查。判据不是「结果不好看」，是**它在对照上表现不对**。

**(1) 相关峰落在梳齿上 → argmax 不是测量。**
源文件每个音都在十六分格上，于是 flux↔onset-train 的相关是**梳子**，
齿与齿**分数打平**（0.240 / 0.224 / 0.224 / 0.215，而物理预测的 −2 帧是 0.215）。
宽窗取 max = 报出**哪颗齿碰巧赢了**。改法有两半，缺一不可：

```python
grid_fr = tick_s(src, src['tpq'] / 4.0) * SR / hop   # 十六分 = 21.5 帧
half    = max(2, int(round(grid_fr / 2.0)))          # 窗只要半格 —— 齿进不来
pred    = -n / (2.0 * hop)                           # STFT 帧自己的中心化，是**预言**
win     = cc[c - half:c + half + 1]
lag     = int(np.argmax(win)) - half
ok      = peak > 0.15 and abs(lag - pred) <= 2.5 and ratio > 3.0
```

**并且齿的分数照印**（`alias`）。「相关分不开零和一个十六分」正是窗必须窄的理由；
把齿藏起来、只印赢的那个数，这条检查就变成便宜话了。

**(2) 排名测试拿**全数**基准比**带通**测量 → 它量的是音色不是音符。**
`top-4 音级` 在**录音**上全对（r 0.894），换到合成音色上就不对（B 10.84% vs 源 4.70%），
因为带通里**高音露基频、低音只露泛音**。换成**旋转检验**（有零点差：另外 11 个移调）：

```python
def key_rotation(au, ref):
    best = None
    for s in range(12):
        rr = float(np.corrcoef(au, np.roll(ref, s))[0, 1])
        if best is None or rr > best[1]:
            best = ((s if s <= 6 else s - 12), rr)
    return best          # 零旋转 r +0.813 胜出，次好 +0.508
```

**顺带补一把绝对的尺子**：网格量化让「整首平移一个十六分」在相关里**不可见**，
但**曲子的开头是唯一的** —— 第一个音在 tick 0 就该在采样 0 发出一记起音，不是 250 ms 静音。

### 三、母带：响度目标要是**不动点**，打击层要按**峰值**定级

```python
want, ceil = 10 ** (TARGET_RMS_DB / 20.0), 10 ** (PRE_CEIL_DB / 20.0)
for it in range(4):
    cur = float(np.sqrt(((0.5 * (L + R)) ** 2).mean()))   # 括号：0.5*(L+R)**2 会高 √2
    L, R = L * (want / max(1e-12, cur)), R * (want / max(1e-12, cur))
    pk  = max(float(np.abs(L).max()), float(np.abs(R).max()))
    L, R = L * min(1.0, ceil / pk), R * min(1.0, ceil / pk)
    L, R = dsp.limiter_stereo(L, R, SR, CEIL_DB, 8.0, 60.0)
    if abs(dsp.rms_db(0.5 * (L + R)) - TARGET_RMS_DB) <= 0.25:
        break
```

**三条为什么**：① 在峰值保护**之前**加的增益不是到达文件的增益（保护会拿走一部分），
所以目标是**不动点**不是一步；② `0.5 * (L + R) ** 2` 是 `0.5 * ((L+R)**2)`，高 √2 且**不报错**
（指纹：一趟 gain 1.0000 却稳定偏离 √2——**算式错，不是被控对象错**）；
③ **打击层按峰值定级** —— `marks` 原来跟着 sub/pad 用 RMS，峰值冲到 1.0261，
母带的余量保护于是把**整首**降 6 dB（交付 −22.01 vs 目标 −16.00）。
一个瞬态的 RMS 只是它峰值的一小撮，**按信号的性质选尺子，不是按项目里其他层用了什么**。

细节 `PROGRESS.md` 112，取舍 **463..469**，`docs/SYSTEMS.md` **§2.20**，`docs/TODO.md` **§3.6**。

## 5.27 把一个圆盘切成同心环，并让一圈一圈抬起来（CSG 版）★ Phase 117

**场景：** 一块 `MeshPart` 圆盘（`Cylinder2`，直径 120）要变成会起伏的涟漪 ——
从中心往外数 12 个环，C1 抬 → C2 抬 → C1 落 → C3 抬……（用户原话的节奏）。

**一、切环。** Roblox 没有 ring 图元。三条路里选 CSG（另两条：一圈拿小件拼 → 太碎；
Blender 出网格再导入 → 最后一公里要上传凭据，走不通）。**外圆盘减内圆盘**：

```lua
local GS = game:GetService("GeometryService")
-- Part.Shape = Cylinder 的轴在【局部 X】，绕 Z 转 90 度把它立成"厚度沿世界 Y"
local cf = CFrame.new(cx, y, cz) * CFrame.Angles(0, 0, math.pi / 2)

local outer = Instance.new("Part")
outer.Shape = Enum.PartType.Cylinder
outer.Size = Vector3.new(0.25, dOuter, dOuter)   -- 厚度沿局部 X；直径 = min(Y, Z)
outer.CFrame = cf
outer.Anchored = true

local inner = outer:Clone()
inner.Size = Vector3.new(1, dInner, dInner)      -- 要挖穿它，所以做厚一点
inner.CFrame = cf

local ring = GS:SubtractAsync(outer, { inner })[1]   -- 一圈 0.02 秒
ring.CFrame = cf
ring.UsePartColor = true          -- ← 少了这一句，下面设的 Color 会被无视（取舍 486）
ring.Color = Color3.new(1, 1, 1)
ring.Material = Enum.Material.ForceField
ring.Anchored = true
ring.CanCollide = false
ring.CanQuery = false             -- 特效不该拦住任何射线 / 点击
ring.CanTouch = false
ring.CastShadow = false
ring.Parent = model
```

`dInner = 0` 的那一圈（最里面那块）就是一块实心小盘 —— 不用特殊照顾，`{}` 都不传。
**12 圈、直径 120 → 每圈 5 stud。**

**二、起波。** 一个环的位移只由它自己的相位决定：

```lua
-- u < 0：还没轮到它；u >= 1：它已经落回去了。
-- 两头都是 0，所以一波过去以后盘面是平的，下一波再从中心开始。
local function ringOffset(t, index, amplitude, period, lag)
	local u = (t - (index - 1) * lag) / period
	if u < 0 or u >= 1 then
		return 0
	end
	return amplitude * 0.5 * (1 - math.cos(2 * math.pi * u))
end
```

`lag = period / 4` → **同一刻约两圈在半空**（波峰长度 = 半个周期 / 每圈延迟）。
想更像水面就加大 `lag`，想更"跳"就减小。
整波长度 `(N-1)·lag + period`，加上静默期 `gap` 就是循环周期。

驱动那一半照 §0.19 的规矩写成**具名函数**，连接只有一行 `RunService.Heartbeat:Connect(step)`；
每帧只在**真的动了**的时候写 CFrame（静默期那些帧一个字节都不发）。

**三、三个坑（都是这一轮踩的）**
1. **`UsePartColor` 默认 false** —— union 出生时带着 CSG 烘进去的颜色，`Color` 照写、照读、
   **不生效**。验收图会整盘一个颜色，看起来像"CSG 没挖洞"（取舍 486）。
2. **射线答的是碰撞体** —— union 的 `CollisionFidelity` 默认落到凸包，
   **环的凸包就是实心盘**，横向射线会"证明"这 12 个环全是实心叠在一起。
   **要么看图，要么先把 `CollisionFidelity` 改成 `PreciseConvexDecomposition`**（取舍 485）。
3. **`Cylinder` 的轴在局部 X** —— 判"平不平"要查 `RightVector`，
   查 `UpVector` 会把 12 个环全报成"轴不竖直"（取舍 485 的同族）。

**四、要改圈数：** `RING_COUNT` 在脚本里，但**几何是命名的**（`C1`..`C12`），
所以改圈数 = 重建几何 + 改常量，不是一个数。**这是当初选 12 的代价**（取舍 487）。

> **§5.27 之后的版本（Phase 118）见 §5.28** —— 同一块盘，但 12 个 CSG 环被换成
> **一张 `EditableMesh` 薄片**（用户：12 级台阶「根本不丝滑」）。§5.27 的那些件**没删**，
> 只是停用；CSG 那套做法在需要**真几何**（要碰撞、要射线、要多人同步）时仍然是对的。

---

## 5.28 用**一张 EditableMesh 薄片**做连续的涟漪（+ 必须每客户端自建的东西怎么交付）★ Phase 118

**场景：** 同一块 120 直径的盘要做涟漪，但台阶要**连续**。
用户同时给了一条形状约束：「那个图形本质上就是18边形」。

**一、先把那句话量成事实。** 网格的顶点角度分桶（这里是半径 100 处）：

```lua
-- 把网格要回来（建它的那个进程里才有，见 §5.25），然后按角度去重
local em = AssetService:CreateEditableMeshAsync(part.MeshContent)
local seen = {}
for _, v in ipairs(em:GetVertices()) do
	local p = em:GetPosition(v)
	local deg = math.floor(math.deg(math.atan2(p.Z, p.X)) + 0.5) % 360
	seen[deg] = true
end
-- 读数：18 个角度，10 30 50 … 350（间隔 360/18 = 20）
```

**量到 18 之后要把它拆成两半**：楔面是**硬**的（18 个），径向的运动是**连续**的。
于是网格 = **18 个楔 × N 个环 × 2 层**，**每楔的两个角点各自复制一份顶点**（边才硬）。

**二、建网。** 一层一层来，顶点按 `[层][环][楔][角]` 存住（后面每帧只按这个索引写 Y）：

```lua
local RADIUS, HALF = 60, 0.125      -- 世界半径；半厚（生下来就是 0.25 厚，见坑 1）
local function build(segments, rings)
	local em = AssetService:CreateEditableMesh()   -- 抠不出来时返回 nil，不抛错（§5.25）
	local step = 2 * math.pi / segments
	local first = step / 2              -- 第一个角点；角落在 first + k*step
	local ids, xz = {}, {}
	for layer = 1, 2 do
		local y = HALF
		if layer == 2 then y = -HALF end
		ids[layer], xz[layer] = {}, {}
		-- 环 0：圆心一楔一个（每楔各有一份，免得共享顶点把法线拉平）
		ids[layer][0], xz[layer][0] = {}, {}
		for wedge = 1, segments do
			ids[layer][0][wedge] = { em:AddVertex(Vector3.new(0, y, 0)) }
			xz[layer][0][wedge] = { Vector3.new(0, 0, 0) }
		end
		for ring = 1, rings do
			ids[layer][ring], xz[layer][ring] = {}, {}
			local radius = RADIUS * ring / rings
			for wedge = 1, segments do
				local a = first + (wedge - 1) * step
				local b = a + step
				ids[layer][ring][wedge], xz[layer][ring][wedge] = {}, {}
				for i, ang in ipairs({ a, b }) do   -- 两个角点，各自一份顶点
					local p = Vector3.new(radius * math.cos(ang), y, radius * math.sin(ang))
					ids[layer][ring][wedge][i] = em:AddVertex(p)
					xz[layer][ring][wedge][i] = Vector3.new(p.X, 0, p.Z)
				end
			end
		end
	end
	-- 面：两层各自朝外，所以第 2 层的绕法相反（否则背面被剔除）
	-- 圆心扇 2 个三角形 / 楔，环与环之间 2 个 / 楔，最外圈再加一圈侧壁把上下两层缝合
	...
	return em, ids, xz
end
```

**三、交给渲染器：写 `MeshContent` 是写不进去的。** 唯一的门是
`CreateMeshPartAsync`，而它返回的件**持有那张网本身**（不是拷贝）：

```lua
local created = AssetService:CreateMeshPartAsync(Content.fromObject(em))
created.Anchored, created.CanCollide = true, false
created.CanQuery, created.CanTouch, created.CastShadow = false, false, false
created.Material, created.Color, created.DoubleSided = disc.Material, disc.Color, disc.DoubleSided
created.Size = created.MeshSize        -- ← 恒等映射：1 网格单位 = 1 stud（见坑 1）
created.CFrame = disc.CFrame
created.Parent = rig
```

**四、每帧只动 Y。** 同一个环上所有顶点同高，所以形状永远是旋转体：

```lua
local function applyHeight(ring, height)      -- 具名函数（§0.19），连接里才没有逻辑
	for wedge = 1, builtSegments do
		for corner = 1, 2 do
			local p = xz[ring][wedge][corner]     -- 建网时存下的 XZ，别再算 sin/cos
			em:SetPosition(ids[1][ring][wedge][corner], Vector3.new(p.X, HALF + height, p.Z))
			em:SetPosition(ids[2][ring][wedge][corner], Vector3.new(p.X, -HALF + height, p.Z))
		end
	end
end
```

相位与 §5.27 完全一样（`frac = ((t - r/speed)/period) % 1`，`frac < width` 才抬），
**区别只在于半径是连续的**：`radius = RADIUS * ring / rings`，
所以隆起是**一个光滑的包**，不是几级台阶。实测一条波扫过去的半径剖面（按 10 stud 分桶取平均）：

```
0.00 0.48 2.13 1.71 0.17 0.00      <- 包在往外走；下一拍中心又起一个
```

**五、交付（这一半最容易被忽略）：`Content.fromObject` 做的东西不跨进程**（§5.25）。
放服务端 → 每个客户端拿到**单位立方体占位**。所以：
**效果脚本必须是 `StarterPlayerScripts` 里的 `LocalScript`，每个客户端自己建一张。**
代价说清楚：**Edit 模式看不到它**（脚本不跑），**服务端也看不到它**（东西只活在那个客户端里），
所以"它到底长什么样"只能靠**客户端读数 + 自检**，不能靠服务端检查。

**六、四个坑（全部量过）**
1. **`MeshSize` 是建件那一刻的快照。** 网格生下来是平的 → `MeshSize.Y` 快照到 **0.001**
   → `Size.Y = 0.25` 就是 **250 倍** Y 拉伸，屏幕上是一台**火山**（直径 650 的坑口）。
   修法两件一起做：**网格生下来就是 `±0.125` 的板** + **`Size = created.MeshSize`**。
   自检读数：`MeshSize = Size = 118.1769, 0.25, 120`（X 小于 120 = 18 边形的**对边距**）。
2. **`MeshContent` 的拒绝是关于权限的，不是关于那件资产的**：新建一个空 `MeshPart`
   一样回 `lacking capability NotAccessible`。**判据永远是"换个空白同款件再试一次"**（取舍 488）。
3. **重建条件别挂在别人的生命周期上。** `StreamingEnabled` 下 `Wave` 会被送走再送回来
   （**另一个实例**）；一见 `part.Parent == nil` 就重建 → 6 次重建把可编辑网格的预算耗到
   **连 `CreateEditableMeshAsync` 读回自己都返回 nil**。薄片要的只有**出生时的外形 + 站位**，
   所以：**圆盘走了波照跑，圆盘回来了再隐它一次，只有薄片自己没了才重建**（取舍 489）。
4. **读回来说是"平"的，有两种来源**：竞态（刚重建，`heights` 还是 0）、真的是平的。
   分开它们的不是读数，是**时间**。所以自检要印**两句话并排**：

```lua
-- 每帧记下这一帧写进去的最大高度，找一个隆起真的起来的时刻读回一次：
local ok, back = pcall(function() return AssetService:CreateEditableMeshAsync(part.MeshContent) end)
-- ...逐顶点取 max Y...
Diag.Value = string.format("the part itself holds ymax=%.2f; this script wrote %.2f", top, HALF + maxHeight)
-- 实测：ymax=2.62  本脚本写了 2.62   （2.62 = 0.125 + 满峰 2.5）
```

**七、和 §5.27 的关系**（决定要哪一个）：要**碰撞 / 射线 / 一次给所有人看** → §5.27 的 CSG 件；
要**连续变形**（丝滑）→ §5.28 的薄片，但它**只活在本地客户端**。
当初是两种并存的（12 个环用 `Enabled` 停用、薄片用 `WaveEnabled`，两个开关**故意不共用**，
否则开新的会顺带开旧的）—— **但 2026-10-11 复查时那 12 个环已经被从 DataModel 里删掉了**
（`Workspace` / `SS` / `RS` 搜 `C1`/`C12` 各 0 个），所以那条"打回开关就能回来"的路**没有了**。
**教训：文档里写的"某功能只是停用、随时可恢复"是一句有保质期的断言** ——
别人（不是这个脚本）删掉之后，盘上的字还在，世界已经不在了（取舍 496）。
留开关的时候，顺带写下**怎么验证被留的东西还在**。

**八、两种运动共用同一个包络，`Falloff` 是它的指数。**
行波和呼吸只差一个**乘数**，所以别重写 —— 加一个 `Motion` 属性，两支并存，
再把那个乘数提成一个共用的量：

```lua
-- Falloff = 0 是恒等（关掉衰减，就是那版「全程满高跑到边上」的行波）
local falloff = number("Falloff", 1, 0)
local motion = rig:GetAttribute("Motion")
if motion ~= "pulse" then motion = "wave" end     -- 拼错落在看得见的那一支上
local travelling = motion == "wave"

-- 共用的包络：中间 1，r = RADIUS 处恰好 0，两端斜率 0（不顶尖、不起折痕）
local envelope = 1
if falloff > 0 then
	envelope = (0.5 * (1 + math.cos(math.pi * radius / RADIUS))) ^ falloff
end

if travelling then
	height = amplitude * envelope
		* 0.5 * (1 - math.cos(2 * math.pi * frac / width))     -- 鼓包形状
else
	height = amplitude * envelope * math.sin(2 * math.pi * elapsed / period)
end
```

四条要记住的：

1. **零要在数学上真的是零。** `math.cos(math.pi)` 在双精度里**就是 `−1`**，
   所以底数是 `0.0`，`0.0^p` 对任何 `p > 0` 就是 `0.0` —— 最外那圈是**逐位的 0**，
   不是 `1e-7` 那种「小到看不见」。今天两种写法在屏幕上一样；
   **改半径（60 → 600）的时候就不一样了**（取舍 494）。
2. **`sin`，不是行波那个 `0.5·(1−cos)`。** 「上下动」是**有符号**的（+A 到 −A）；
   行波那条上升沿只走正的一半。**一句话里最容易漏掉的就是这个符号。**
3. **每帧会写满 1800 个顶点。** 行波时只有鼓包那一段在变；呼吸模式每一帧 25 个环全变，
   所以帧花费从 0.85 涨到 1.13 ms（安静窗口）。**要省就调 `Rings`，别去动公式。**
4. **验收（这是「不动」唯一的量法）：两次读数之差，不是「数很小」。**
   ```lua
   -- 把 r >= 59.9 的顶点单独挑出来，隔 0.9 秒读两次（一次读数分不清静止和过零）
   A rim y = -0.1250 .. +0.1250   centre top y = +0.831
   B rim y = -0.1250 .. +0.1250   centre top y = +0.835
   ```
   再加一条**形状**断言：半半径处的高度应当**正好是中间的一半**（升余弦在 r/2 处 = 0.5）
   —— 比「边缘数值很小」强得多，因为它同时钉住了衰减的形状。

**九、给行波加衰减 = 把那个包络乘到行波上，然后**用 A/B 证明它是那个乘数**。
`Falloff = 1` 时，鼓包跑到一半半径就只剩一半高，跑到边上没了；
`Falloff = 0` 是恒等，鼓包**满高撞到边上**。两组读数（同一套 `Amplitude=5 Speed=6
Period=4 Width=1`，**只动 `Falloff` 一个数**，22 秒 / 12 秒各采一遍，取每环的最大值）：

```
Falloff=1   max h[0]=5.00   max h[12]=2.49   max h[24]=0.00     ← 44 个采样里 h[24] 全是 0.00
Falloff=0   max h[0]=4.99   max h[12]=5.00   max h[24]=4.98     ← 全程满高，边上也在动
```

**为什么必须是 A/B、不能只报那三个数**：单看 `2.49` 说明不了任何事 ——
它既可能是衰减，也可能只是「鼓包本来就只长到 2.5」。**差是量出来的，单个数不是**（取舍 497）。

顺带三条：

- **慢下来才量得到。** `Diag` 每 30 帧刷一次（≈0.5 s），而采样窗口是 `Width × Period`：
  默认的 `0.5 × 1.2 = 0.6 s` 只够一次采样，峰值会被系统性读低（worst case 15%）。
  量的时候把 `Period` 开到 4、`Width` 开到 1 → 窗口 4 s，8 个采样点，误差 ~4%。
  **这是量法的问题，不要为了量它去改代码把"峰值"记进 `Diag`。**
- **行波的空间宽度 = `Speed × Width × Period`。** 所以「把 `Period` 调慢一点好采样」
  会顺带把鼓包拉宽（这次 `Period=4` 时是 24 stud），**两个旋钮不是正交的**。
- **`Motion` 取值的兜底要和你想要的默认一致。** 代码里写
  `if motion ~= "pulse" then motion = "wave" end`，所以**删掉 `Motion` 属性得到的是行波**；
  上一次默认是呼吸 —— 兜底值和盘上的值不一致时，谁去「清一下属性」谁就会看到一个不同的效果
  （取舍 493 的同族）。

## 5.29 把一个「探针点亮的 Edit 世界」恢复到授权（冷）状态 ★ Phase 122

**什么时候用**：`FacilityCascade.Initialize` 的基线是**从世界读**的（对的设计），
所以任何一次在 Edit 里跑过点亮级联的探针，都会把「亮着」变成下一次 `Initialize`
认下的授权 —— 整场开机**静默失效**（ramp 从 `on` 到 `on`）。
`ColdBaseline=true` 救不了（它的 `off` 也读世界）。

**唯一的出路是原版自己的录像**：`Data/originalwatch/*/changes.log` 每行是
`t=… | 容器 | 全路径 | old | new`，所以**每个 (路径, 属性) 最早一次出现的 `old`
就是它的 t=0 值** —— 而我们的设施是从原版复制来的，实例路径按构造就对得上。

### ① 生成冷表

```
PYTHONIOENCODING=utf-8 python _tools/cold_baseline.py Data/cold_baseline.tsv
```

`_tools/cold_baseline.py` 里两条写法是必须的，改回去会得到一张**看起来很合理**的错表：

```python
# 从右边切，不要用正则去套尾部：`.` 匹配 `|`，
# 于是「懒组当路径 + 贪心组当值」会笑着把 `path | old` 交回来当路径。
head, old, new = raw.rsplit(' | ', 2)
```

```python
# 观察者的 ` ~(x, y, z)` 与 ` #n` 是它自己的寻址，不是游戏的；
# 不去掉，48 个同名兄弟会塌成一行，「写进 48 件」变成「写进 1 件」，而张数不报错。
TILDE = re.compile(r' ~\([^)]*\)')
HASH = re.compile(r' #[0-9]+')
```

### ② 把表送进 Studio（字节不进上下文）

```bash
python _tools/serve.py --dir Data --port 8769      # 用完记得杀
```

官方 `rblx_execute_luau`（Edit 数据模型）里 `HttpGet` 到 `http://127.0.0.1:8769/cold_baseline.tsv`，
逐行 apply。**三条必须写对**：

```lua
-- ① 点路径的最后一段是属性，不是子件（DECISIONS 509）
local parentPath, prop = string.match(path, '^(.*)%.([^%.]*)$')

-- ② 每一层的同名兄弟都要展开（父路径自己就可能指向多个同名件）
local function resolve(base, seg)      -- 返回数组
    local out = {}
    for _, node in ipairs(base) do
        for _, kid in ipairs(node:GetChildren()) do
            if kid.Name == seg then table.insert(out, kid) end
        end
    end
    return out
end

-- ③ 值要按形状认，不能一律当字符串
--    1 个 -> number     2 个 -> NumberRange
--    3 个 -> Color3（全在 0..1）/ Vector3（否则）
--    true/false -> bool
```

实测一遍：`wrote=809 failed=0`，`missingPath=9`（全是 `Lights.MaintFacilityLights.*`,
而我们自己的 `Initialize` 本来就说那一组是空的 —— **缺的东西先 `bool(x)` 再断言**，§0.6）。

### ③ 录像没行的地方，用**我们自己的算术**（不是猜）

原版和我们的副本在**三处合法地不一样**：`ControlRoomLowerLights` / `SubLoungeLights`
原版**静止时灯就是开的**（`Enabled=true`），我们这一份静止是暗的 —— 判据是
**我们自己的 t0 普查**（全设施 32 盏亮灯全是 METU 的）。所以那两组**只回滚 `Enabled`**,
颜色与亮度保留原版值。`LightPart.Color`（9 件）与 `LoungeLights`（6 件）**录像一行都没有**，
靠算术黑回去：t0 `48/96` 而点亮后 `96/96` ⇒ 恰好 48 件由黑转白（亮度只升不降），
Lounge `78/84 → 84/84` ⇒ 6 件。

### ④ 判据是**逐项相同**，不是「看起来回来了」

恢复后必须与走之前**另一次独立**的普查逐项相同（这一轮 `592/742`、`32` 盏），
且逐组加起来正好落在总数上。

### ⑤ 附：`rewind` 精确可逆 —— 所以「克隆驱一遍」是安全动作

把 `Config` + `FacilityCascade` `Clone()` 进一个临时 Folder 再 `require`（§0.15），
用**它自己的公开函数**驱动：`Initialize` → 逐 step `Refresh` → `Step(dt)`；
完了 `Refresh({startupStep=0, phase='Starting'})` 倒回去。实测逐项回到走之前
（球 `30,30,30`、beam `1`、core `1`、PointLight `false`）——
**这就是「拍完图世界还是干净的」的凭据**，不用进 §0.5 那张冷表。

## 5.30 真机点一个控制：属性机位 + 客户端保持器 + 整数像素（★ Phase 123）

Phase 122/123 用的全套装置，**全部在 Play 会话里**、`VirtualInputManager` 不可用的前提下
（§0.11 家族：它 `lacking capability RobloxScript`）。分四件东西，各归各的 VM：

**(1) 服务端做 park（**必须**服务端）**。客户端的 `hrp.CFrame = …` 只动客户端那一份，
服务端仍把角色留在出生点、每一次点击都被 6 studs 的距离门拒掉，**两边都看不出来**（§0.11 第 6 条）。
顺手把角色每个 `BasePart` 打哑（`Transparency=1, CanCollide=false, CanQuery=false, CanTouch=false`）
—— `CanQuery=false` 让它同时从**我的射线**和 **Mouse 的射线**里消失。

**(2) 机位写进属性，客户端保持器照着摆。** `workspace.__probe` 上放 6 个属性
（`EyeX/Y/Z`、`AimX/Y/Z`）+ `Scan`（要扫的标签）+ `Result`（扫描结果）。
`Players.<me>.PlayerScripts` 里插一个 `LocalScript`（§0.23 ②：**只有插进去的脚本才在游戏 VM 里跑**）：

```lua
RunService:BindToRenderStep('__probeCamHold', Enum.RenderPriority.Camera.Value + 1, function()
  local ex, ey, ez = attr('EyeX'), attr('EyeY'), attr('EyeZ')
  local ax, ay, az = attr('AimX'), attr('AimY'), attr('AimZ')
  if ex and ax then
    camera.CameraType = Enum.CameraType.Scriptable
    camera.CFrame = CFrame.lookAt(Vector3.new(ex, ey, ez), Vector3.new(ax, ay, az))
  end
end)
```

**于是「重设机位」= 改 6 个属性**（服务端写，自动复制到客户端），
不需要每次重建脚本，也不需要跨 VM 递函数。

**(3) 像素扫描：解析投影 + 整数像素 ±34 + 首击命中判据。**
`Camera:WorldToViewportPoint(aim)` 给出中心（实测总是 `510.5, 240.0`），
在 ±34 px 的方格里逐**整数**像素 `Camera:ViewportPointToRay(px+0.5, py+0.5)`，
只留**首击**实例沿父链四层内带着 `ClickPartText == 想要的标签` 的像素，
取**最靠近命中点集质心**的那个。判据是「首击带对标签」而不是「射线打得中」——
`Mouse.Target` 与相机射线在 `Transparency=1` 的件上**答案不同**（§0.11）。

**(4) 官方鼠标工具点它，y 要减 58。** `tool_y = viewport_y − inset`
（`GuiService:GetGuiInset().Y`，本轮实测 58：请求 `510,200` → `GetMouseLocation()` 回 `510,258`）。
`moveTo` 之后**要留 ~450 ms** 再按，否则 `Mouse.Target` 还没更新。

**两条不管就会白跑一遍的**：
**① 机位和像素绑死** —— 缓存里必须连 `eye/aim` 一起存，点之前重设同一个 `lookAt`；
本轮四个件里有三个的像素是 **(510,239)**、一个是 **(512,238)**，**2 px 之隔**。
**② 拍图前先 `RunService:UnbindFromRenderStep('__probeCamHold')`** ——
保持器会让 `screen_capture` 的显式机位静默失效（两张不同请求 → 逐字节相同，取舍 513）。

---

### 5.31 在真机上驱动一次点击并**证明它送达了**，以及三个会安静骗人的工具 ★ Phase 124

Phase 123 的 §5.30 给了「怎么算像素」；这一节给的是 **「怎么知道那一下真的到了」**，
以及三个当天踩到的、**报成功但不是那件事**的工具。

**(1) 送达判据是服务端那条打印，不是 `Booted` 之类的状态位。**

`ControlBinder` 每次**通过门**的点击会打一行：

```
[ReactorBackend][Control] <player> -> <LABEL>
```

而 `Engine:Command` 的每一次拒绝打的是 `[ReactorBackend][Control] <label> rejected: <err>`，
另外 `noteGate` 每 5 s 汇一次 `[ReactorBackend][Gate] refused N out-of-range and M rate-limited…`。
**三条分得开**：`->` 是送达、`rejected:` 是送达但被门拒、`[Gate]` 是根本没到。
只有前两条的**并集**才证明「鼠标那一下打在了件上」。

**本轮的反面教材**：`MONITOR BOOT` 反复失败，我拿 `Booted=false` 当判据，
于是「点空了」和「门拒了」在我的读数里**逐字相同**；真因是 `ShuttersOpen=false`
（`boot` 的门）。**读数相同、路径两条 ⇒ 那个读数不是证据**（§0.26 ①）。

**(2) GUI 中点：请求坐标就是中点本身，不用加也不减 58。**

```lua
-- 视口点 V 与屏幕点的关系：V = absolutePosition + size/2 + inset
-- user_mouse_input 请求的坐标 S 满足 GetMouseLocation() = (S.x, S.y+58)
-- 而 GetGuiInset().Y = 58  ⇒  V.y = S.y + 58
-- 两式相减：请求 absolutePosition.Y + size.Y/2 时，58 恰好抵消。
local centre = button.AbsolutePosition + button.AbsoluteSize/2
-- 于是请求 (centre.X, centre.Y) 即可（Phase 124 实测：HoldButton abs=490,111 size=55,60
-- → 请求 (517,141) → 按住 1.7 s → 回执 {'Reset',1,'Accepted'}）
```

**边界**：只在**那个**视口下逐位成立（`AbsolutePosition` 量的是 CoreUISafe 空间，
y 从顶栏**下面**量起）。本轮视口 575.2×259.2，上一轮 1020×550 —— 换视口要重量。

**(3) 一个按住型按钮的完整发法**（`HoldButton` 要连续按住 ~1.5 s）：

```lua
actions = {
  {action='moveTo', x=centre.X, y=centre.Y},
  {action='mouseButtonDown', mouse_button='left'},
  {action='wait', wait_time_ms=1700},        -- 比门槛留 ~200 ms 余量
  {action='mouseButtonUp', mouse_button='left'},
}
```

**(4) 三个会安静骗人的工具，用之前先想清楚它们报的是什么。**

| 工具 | 它安静地报什么 | 判据 |
|---|---|---|
| `ok and v or 'default'` | `v==false` 时报成「读不到」 | 值域有 `false`/`nil` 就写 `if`（§0.26 ②） |
| Assistant 沙箱里的 `Connect` | 「接上了」但回调这一轮**一次没跑** | 别把每帧的活儿藏在连接里（§0.19）；判据改用实例状态 |
| 一次 >55 s 的阻塞等待 | 直接杀掉 Play 桥、Studio 回 Edit | 切片，每段 ≤55 s（§0.26 ③） |

**(5) 一条「跨过结局」的端到端链，照这个顺序读**（本轮实测通过的）：

```
Server: RuntimePhase / Stats.Core.*        ← 结局真的发生了
Client: 载荷字段逐个对屏幕读的那六个数      ← 发的是不是那个东西
Client: 屏幕上的字（Title / MoneyText）     ← 玩家看到的是不是它
Client: 回执 {mode, shift, 'Accepted'}     ← 请求有没有被接受
Server: RuntimePhase 变回 'Cold'           ← 引擎真的转换了
Client: 屏幕 Visible=false、界面复位回作者值 ← 玩家真的能继续玩
```

**最后一条要跟作者值比，不是跟「我记得应该是 true」比**：
`VitalsFrame.Visible` 我一度以为是 `true`，直接读到 `false`、`StarterGui` 侧的
**作者值也是 `false`** —— 复位是对的（§0.24：基线从世界读）。

**(6) 拉回整个后端文件夹，逐件比 —— 「我推过」不可证伪，「逐文件比」可证。**

```bash
# 盘侧：起一个**空**目录当接收端（每次都用新的：旧目录里的残件会被当成这次的证据）
C:/Python314/python.exe _tools/receive.py --port 8765 --dir _tools/_pull/round124
```

```lua
-- Studio 侧（官方 execute_luau，datamodel_type='Edit'；PostAsync 在两个 VM 里都能用）
local HttpService=game:GetService('HttpService')
local b=game:GetService('ServerScriptService'):FindFirstChild('ReactorBackend')
for _,k in ipairs(b:GetDescendants()) do
  if k:IsA('LuaSourceContainer') then
    HttpService:PostAsync('http://127.0.0.1:8765/'..k.Name..'.luau', k.Source)
  end
end
```

```bash
C:/Python314/python.exe _tools/compare_backend.py --pulled _tools/_pull/round124
```

`_tools/compare_backend.py` 比的是**内容哈希**（不比长度 —— 同长不同字节在这里真发生过），
逐件打 `SAME` / `DIFF` / `???`（没有唯一对应的盘上文件）/ `ABSENT`（盘上有、拉回来没有），
**任一非空即 exit 1**。Phase 124 那次是 **12/12 SAME**；Phase 123 那次正是靠这个格式
暴露了「十个相同、`Engine` 一个落后一个版本」。

**三条边界**：
**① 接收目录必须每次新建** —— 残件会冒充这一次的结论。
**② 上一轮的 `receive.py` / `serve.py` 进程还活着，而且它可能抢走这一次的连接。**
本轮实测：`netstat` 上有**三个** PID 同时 LISTENING 在 8765，命令行分别是三个不同的 `--dir`；
我的 POST **没有**进我这一轮起的那个目录，而是进了**上一轮那个**（`--dir …/studio_backend`）。
Windows 的 `SO_REUSEADDR` 让新 bind **成功而不报错**，所以「我起了新 sink」和
「文件进了新 sink」是两件事。**动手前先 `netstat -ano | grep <port>` +
`Get-CimInstance Win32_Process` 看命令行**，复用或杀掉，别假定端口是你的。
**③ `LuaSourceContainer` 只覆盖这个文件夹** —— `StarterPlayerScripts.EndShiftResume`
**不在** `SSS.ReactorBackend` 里，得单独拉一次（本轮就是单独拉的）。
