--!strict
-- Client-side visual feedback: drives lever position and lamp color by reading
-- workspace.Stats ValueObjects. Server publishes state; client reflects it on
-- the physical controls. This sidesteps StreamingEnabled: the client only
-- updates controls that have streamed in, and workspace.Stats is always loaded.

local VisualFeedback = {}
local RunService = game:GetService("RunService")

-- Lever state is encoded in the control's own geometry and label; movement is
-- translation along the lever's LookVector (all share (0.91,-0.34,-0.24)).
-- Baseline = authored CFrame at client boot; movement = baseline + LookVector * (state * travel).
local leverBaselines: {[Instance]: CFrame} = {}
local lampBaselines: {[Instance]: Color3} = {}

local Config = {
    Visual = {
        LeverArcDegrees = 50, -- repurposed as travel distance in studs
        Ready = Color3.fromRGB(235, 235, 235),
        Off = Color3.fromRGB(45, 45, 45),
        Pulse = Color3.fromRGB(90, 255, 120),
        Fault = Color3.fromRGB(255, 70, 40),
    }
}

local function updateLever(union: BasePart, state: number)
    local baseline = leverBaselines[union]
    if not baseline then return end

    local travel = Config.Visual.LeverArcDegrees
    local offset = baseline.LookVector * (state * travel)
    union.CFrame = baseline + offset
end

local function updateLamp(neon: BasePart, mode: string)
    local colors = Config.Visual
    local target = colors.Off

    if mode == "ready" then target = colors.Ready
    elseif mode == "pulse" then target = colors.Pulse
    elseif mode == "fault" then target = colors.Fault
    elseif mode == "off" then target = colors.Off
    end

    neon.Color = target
end

-- Read workspace.Stats and update visible controls
local function refresh()
    local stats = workspace:FindFirstChild("Stats")
    if not stats then return end

    -- Pumps: read CBL1/2/3.Active (BoolValue) and infer level from lamp pattern
    -- (engine doesn't publish pump level to Stats yet, only active flag)
    for i = 1, 3 do
        local ctrl = workspace.Consoles.ThermalConsole:FindFirstChild("CoolantControl" .. i)
        if ctrl then
            local cblFolder = stats:FindFirstChild("CBL" .. i)
            local active = cblFolder and cblFolder:FindFirstChild("Active")
            local isActive = active and active.Value or false

            local lever = ctrl:FindFirstChild("BigLever")
            local union = lever and lever:FindFirstChild("LeverUnion")
            if union then
                -- Placeholder: assume level 3 when active (engine doesn't publish level yet)
                updateLever(union, isActive and 1 or 0)
            end

            -- Three lamps: Light1/Light2/Light3
            for level = 1, 3 do
                local light = ctrl:FindFirstChild("Light" .. level)
                local neon = light and light:FindFirstChild("NeonPart")
                if neon then
                    local mode = isActive and "ready" or "off"
                    updateLamp(neon, mode)
                end
            end
        end
    end

    -- Fans: read Stats.Fans.Fan1..6 (BoolValue)
    local fansFolder = stats:FindFirstChild("Fans")
    if fansFolder then
        for i = 1, 6 do
            local fanValue = fansFolder:FindFirstChild("Fan" .. i)
            local active = fanValue and fanValue.Value or false

            local cfLever = workspace.Consoles.ThermalConsole:FindFirstChild("CFLever" .. i)
            if cfLever then
                local union = cfLever:FindFirstChild("LeverUnion")
                if union then
                    updateLever(union, active and 1 or 0)
                end

                local offlineLight = cfLever:FindFirstChild("OfflineLight")
                local neon = offlineLight and offlineLight:FindFirstChild("NeonPart")
                if neon then
                    updateLamp(neon, active and "ready" or "off")
                end
            end
        end
    end
end

function VisualFeedback.Start()
    local consoles = workspace:WaitForChild("Consoles", 10)
    if not consoles then
        warn("[VisualFeedback] workspace.Consoles not found")
        return
    end

    -- Capture baseline positions for all levers and lamps that are ALREADY streamed in
    for _, desc in ipairs(consoles:GetDescendants()) do
        if desc.Name == "LeverUnion" and desc:IsA("BasePart") then
            leverBaselines[desc] = desc.CFrame
        end
        if desc.Name == "NeonPart" and desc:IsA("BasePart") then
            lampBaselines[desc] = desc.Color
        end
    end

    -- Listen for NEW levers/lamps streaming in (StreamingEnabled support)
    consoles.DescendantAdded:Connect(function(desc)
        if desc.Name == "LeverUnion" and desc:IsA("BasePart") then
            leverBaselines[desc] = desc.CFrame
        end
        if desc.Name == "NeonPart" and desc:IsA("BasePart") then
            lampBaselines[desc] = desc.Color
        end
    end)

    -- Report initial count, but more will arrive as player moves
    local function countBaselines(tbl)
        local n = 0
        for _ in pairs(tbl) do n += 1 end
        return n
    end
    print(string.format("[VisualFeedback] captured %d lever baselines, %d lamp baselines (initial; more will stream in)",
        countBaselines(leverBaselines), countBaselines(lampBaselines)))

    -- Poll Stats every 0.2 seconds (matches Config.Visual.RefreshSeconds on server)
    RunService.Heartbeat:Connect(function()
        refresh()
    end)
end

return VisualFeedback
