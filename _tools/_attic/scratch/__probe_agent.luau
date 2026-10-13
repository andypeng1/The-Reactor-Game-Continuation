-- __probeAgent -- Play-session-only, dropped into ServerScriptService. It is both
-- the recorder and the actuator, because they are two halves of one interaction
-- and splitting them would mean two injections that have to agree about names.
--
-- WHY IT EXISTS. TODO 3.14 (1) is that the NORMAL, quota-completing `Report` has
-- never been exercised live -- Phase 124 drove `Failed`, which leaves through the
-- same transport with a different reason string, and that is not the same claim.
-- Getting there needs a full shift, and _tools/quota_policy_sim.luau says a shift
-- can be won for SIXTEEN clicks (boot chain 4, two fans off 2, three pumps on 3,
-- six purges, one shutdown). Sixteen clicks is a live job, but every one of them
-- needs the character within the six studs ControlBinder measures -- so the rig's
-- whole cost is the parking, and this file does the parking.
--
-- (1) ACTUATOR -- watch workspace.__probeCmd. On each new value it finds the
-- control by its ClickPartText label (the same contract ControlBinder resolves
-- against, so this cannot aim at something the binder would read differently),
-- puts the character's root AT that control, and writes an eye/aim pair onto
-- workspace.__probe for the client camera holder to follow. Because the root is
-- placed at zero distance, the range gate is met by construction rather than by
-- arithmetic, and because the eye is placed along a direction a raycast proved
-- open, the click does not have to see through the console it is standing in.
--
-- The character is anchored and every part of it is muted (Transparency 1,
-- CanCollide/CanQuery/CanTouch false). Anchored because a root that falls to the
-- floor between parks is a root that is somewhere else by the time the click
-- lands; CanQuery false so the click's own ray passes THROUGH the character
-- rather than hitting it (CLAUDE 0.11: Mouse.Target and the camera's own ray
-- disagree about Transparency=1 parts, so the character must be out of the query
-- set, not merely invisible).
--
-- (2) RECORDER -- CLAUDE 0.16: a playtest's prints cannot be read from outside,
-- so the only prints worth having are the ones turned into instance state. Two
-- streams: every `[ReactorBackend]` line tapped from LogService (this is where
-- the control DELIVERY oracle lives: `<player> -> <LABEL>` is a delivery,
-- `rejected: <err>` is a delivery the engine refused, and neither is a request
-- that never arrived), and the reactor's own published numbers out of
-- workspace.Stats -- which live in SUBFOLDERS (Stats.Core.TemperatureVal), not as
-- direct children, a detail that makes a wrong read return nothing at all.
--
-- AND ITS OWN DEATH (CLAUDE 0.17): this runs in a thread nobody awaits, so "in
-- flight and idle" and "threw on the first frame" are byte-identical from
-- outside. Both loops are pcall-wrapped and a throw writes SAMPLER DIED.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10): newlines come from string.char(10), and
-- no inner double quote is ever needed.

local RunService = game:GetService('RunService')
local LogService = game:GetService('LogService')
local Players = game:GetService('Players')
local ws = game.Workspace
local NL = string.char(10)

local function ensure(name, class)
    local node = ws:FindFirstChild(name)
    if node and node:IsA(class) then return node end
    if node then node:Destroy() end
    node = Instance.new(class)
    node.Name = name
    node.Parent = ws
    return node
end

local probe = ensure('__probe', 'Folder')
local cmd = ensure('__probeCmd', 'StringValue')
local report = ensure('__probeReport', 'StringValue')

local lines = {}
local t0 = ws:GetServerTimeNow()
local function push(text)
    lines[#lines + 1] = string.format('t=%.3f %s', ws:GetServerTimeNow() - t0, text)
    if #lines > 400 then table.remove(lines, 1) end
    report.Value = table.concat(lines, NL)
end

-- ========== THE LOG TAP ==========
LogService.MessageOut:Connect(function(message, kind)
    local ok, err = pcall(function()
        local text = tostring(message)
        if string.find(text, 'ReactorBackend', 1, true) or string.find(text, '[Control]', 1, true) then
            push(string.format('%s %s', tostring(kind), text))
        end
    end)
    if not ok then push('LOG TAP DIED: ' .. tostring(err)) end
end)

-- ========== THE CHARACTER ==========
-- The park point is the control itself, so the mutes are not cosmetic: without
-- CanQuery=false the character would be the first thing the click's ray hits.
local muted = nil
local function mute()
    local player = Players:GetPlayers()[1]
    local character = player and player.Character
    if not character or character == muted then return end
    muted = character
    for _, part in ipairs(character:GetDescendants()) do
        if part:IsA('BasePart') then
            part.Transparency = 1
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
        end
    end
    local root = character:FindFirstChild('HumanoidRootPart')
    if root then root.Anchored = true; root.CFrame = CFrame.new(0, -500, 0) end
    push('character muted and anchored')
end

local function findControl(label)
    local consoles = ws:FindFirstChild('Consoles')
    if not consoles then return nil end
    for _, d in ipairs(consoles:GetDescendants()) do
        if d:IsA('ClickDetector') then
            local part = d.Parent
            local t = part and part:FindFirstChild('ClickPartText')
            if t and t:IsA('StringValue') and t.Value == label then return part end
        end
    end
    return nil
end

-- Which way is out of the console? Eight horizontal rays, 8 studs, first clear
-- one wins. Hard-coding an offset would have to be right for every console in the
-- row and would be silently wrong for the one that faces the other way.
local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Exclude
local function openDirection(part)
    rayParams.FilterDescendantsInstances = {muted}
    local probes = {}
    for i = 0, 7 do
        local angle = math.rad(i * 45)
        probes[#probes + 1] = Vector3.new(math.cos(angle), 0, math.sin(angle))
    end
    local origin = part.Position
    local best, bestDist = nil, -1
    for _, dir in ipairs(probes) do
        local hit = ws:Raycast(origin, dir * 9, rayParams)
        local dist = hit and (hit.Position - origin).Magnitude or 9
        if dist > bestDist then best, bestDist = dir, dist end
        if not hit then return dir, 9 end
    end
    return best, bestDist
end

local function park(label)
    mute()
    local part = findControl(label)
    if not part then return 'MISS ' .. label end
    local player = Players:GetPlayers()[1]
    local character = player and player.Character
    local root = character and character:FindFirstChild('HumanoidRootPart')
    if not root then return 'NO ROOT ' .. label end
    root.CFrame = CFrame.new(part.Position)
    local dir = openDirection(part)
    local eye = part.Position + dir * 3.5 + Vector3.new(0, 0.7, 0)
    probe:SetAttribute('EyeX', eye.X); probe:SetAttribute('EyeY', eye.Y); probe:SetAttribute('EyeZ', eye.Z)
    probe:SetAttribute('AimX', part.Position.X)
    probe:SetAttribute('AimY', part.Position.Y)
    probe:SetAttribute('AimZ', part.Position.Z)
    probe:SetAttribute('Scan', label)
    probe:SetAttribute('Status', string.format('%s at %.1f,%.1f,%.1f reach %.2f',
        label, root.Position.X, root.Position.Y, root.Position.Z, (root.Position - part.Position).Magnitude))
    push(probe:GetAttribute('Status'))
    return 'PARK ' .. label
end

task.spawn(function()
    local seen = ''
    while true do
        local ok, err = pcall(function()
            local value = cmd.Value
            if value ~= seen and value ~= '' then
                seen = value
                park(value)
            end
        end)
        if not ok then push('ACTUATOR DIED: ' .. tostring(err)) end
        task.wait(0.1)
    end
end)

-- ========== THE NUMBERS ==========
-- Stats.Core and Stats.CBL1..3 and Stats.Fans: the values are in subfolders.
local last = {}
local lastPhase = 'unread'
local function scan()
    local backend = game.ServerScriptService:FindFirstChild('ReactorBackend')
    local phase = backend and tostring(backend:GetAttribute('RuntimePhase')) or 'none'
    if phase ~= lastPhase then lastPhase = phase; push('phase=' .. phase) end
    local stats = ws:FindFirstChild('Stats')
    if not stats then return end
    local core = stats:FindFirstChild('Core')
    local parts = {}
    if core then
        for _, key in ipairs({'TemperatureVal', 'PressureVal', 'StressVal', 'OutputVal', 'EnergyVal', 'QuotaVal'}) do
            local v = core:FindFirstChild(key)
            if v and v:IsA('ValueBase') then
                local value = v.Value
                if last[key] ~= value then last[key] = value; parts[#parts + 1] = key .. '=' .. tostring(value) end
            end
        end
    end
    for i = 1, 3 do
        local folder = stats:FindFirstChild('CBL' .. i)
        local v = folder and folder:FindFirstChild('Active')
        if v and v:IsA('ValueBase') and last['cbl' .. i] ~= v.Value then
            last['cbl' .. i] = v.Value
            parts[#parts + 1] = 'CBL' .. i .. (v.Value and '=on' or '=off')
        end
    end
    if #parts > 0 then push(table.concat(parts, ' ')) end
end

local ok, err = pcall(function()
    push('AGENT UP')
    mute()
    local frames = 0
    while frames < 60 * 60 * 40 do
        frames += 1
        local fine, problem = pcall(scan)
        if not fine then push('SCAN DIED: ' .. tostring(problem)); return end
        RunService.Heartbeat:Wait()
    end
    push('AGENT HIT ITS OWN FRAME LIMIT')
end)
if not ok then push('AGENT DIED OUTSIDE: ' .. tostring(err)) end
