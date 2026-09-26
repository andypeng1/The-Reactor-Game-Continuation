--!strict
-- Drives lever position and lamp color from engine state.
-- Levers translate along their LookVector (not rotate); lamps switch between
-- Ready/Off/Pulse/Fault colors. All 29 levers share LookVector (0.91,-0.34,-0.24).
--
-- The movement contract is linear: 0 → retracted (baseline position),
-- 1 → extended (baseline + LookVector * travel distance). Travel distance is
-- inferred from Config.Visual.LeverArcDegrees as a placeholder that became studs.

local VisualFeedback = {}
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

-- Lever state is encoded in the label: "C-PUMP 1 LEVEL 3" → pump 1 at level 3,
-- "COOLING FAN 2" → fan 2 (binary), etc. The baseline position is the authored
-- CFrame at game launch; movement = baseline + LookVector * (state * travel).
local leverBaselines: {[Instance]: CFrame} = {}
local lampBaselines: {[Instance]: Color3} = {}

-- Pulse state for transient feedback (button press acknowledged but not yet
-- reflected in the engine state, or a momentary event like grav fire).
local pulseTargets: {[Instance]: number} = {}

local function updateLever(union: BasePart, state: number, config: any)
    local baseline = leverBaselines[union]
    if not baseline then return end

    -- state is normalized 0..1 for this control (e.g. pump level 0..3 → 0, 0.33, 0.67, 1)
    local travel = config.Visual.LeverArcDegrees -- repurposed as travel distance in studs
    local offset = baseline.LookVector * (state * travel)
    local target = baseline + offset

    -- Instant for now; TweenService later if the user wants smoothing
    union.CFrame = target
end

local function updateLamp(neon: BasePart, mode: string, config: any)
    local colors = config.Visual
    local target = colors.Off -- default

    if mode == "ready" then target = colors.Ready
    elseif mode == "pulse" then target = colors.Pulse
    elseif mode == "fault" then target = colors.Fault
    elseif mode == "off" then target = colors.Off
    end

    neon.Color = target
end

-- Map engine state to lever positions and lamp colors
local function refresh(state: any, config: any)
    -- Pumps: 3 levers, each 0..3 levels + enabled flag
    for i = 1, 3 do
        local pump = state.pumps[i]
        if not pump then continue end

        -- Find lever: CoolantControl{i}.BigLever.LeverUnion
        local ctrl = workspace.Consoles.ThermalConsole:FindFirstChild("CoolantControl" .. i)
        if ctrl then
            local lever = ctrl:FindFirstChild("BigLever")
            local union = lever and lever:FindFirstChild("LeverUnion")
            if union then
                local normState = pump.enabled and (pump.level / 3) or 0
                updateLever(union, normState, config)
            end

            -- Three lamps: Light1/Light2/Light3, one per level
            for level = 1, 3 do
                local light = ctrl:FindFirstChild("Light" .. level)
                local neon = light and light:FindFirstChild("NeonPart")
                if neon then
                    local mode = "off"
                    if pump.enabled and pump.level >= level then
                        mode = pump.fault and "fault" or "ready"
                    end
                    updateLamp(neon, mode, config)
                end
            end
        end
    end

    -- Fans: 6 binary levers (CFLever1..6)
    for i = 1, 6 do
        local active = state.fans[i]
        local cfLever = workspace.Consoles.ThermalConsole:FindFirstChild("CFLever" .. i)
        if cfLever then
            local union = cfLever:FindFirstChild("LeverUnion")
            if union then
                updateLever(union, active and 1 or 0, config)
            end

            local offlineLight = cfLever:FindFirstChild("OfflineLight")
            local neon = offlineLight and offlineLight:FindFirstChild("NeonPart")
            if neon then
                updateLamp(neon, active and "ready" or "off", config)
            end
        end
    end

    -- CBL: 3 levers, each 0..5 levels + active flag
    -- (Geometry location TBD — not in ThermalConsole)

    -- Shutters, monitor power, lights, mute, etc. — binary levers
    -- (Geometry location TBD)
end

function VisualFeedback.Initialize(config: any)
    -- Capture baseline positions for all levers
    for _, desc in ipairs(workspace.Consoles:GetDescendants()) do
        if desc.Name == "LeverUnion" and desc:IsA("BasePart") then
            leverBaselines[desc] = desc.CFrame
        end
        if desc.Name == "NeonPart" and desc:IsA("BasePart") then
            lampBaselines[desc] = desc.Color
        end
    end

    print(string.format("[ReactorBackend][Visual] captured %d lever baselines, %d lamp baselines",
        #leverBaselines, #lampBaselines))
end

function VisualFeedback.Refresh(state: any, config: any)
    refresh(state, config)
end

return VisualFeedback
