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

---

