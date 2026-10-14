-- __rayProbe -- Play-session-only, dropped into ServerScriptService.
--
-- WHY IT EXISTS. TODO 3.14 (3), open since Phase 124 (DECISIONS_2 519 (1)):
-- "does the character block the click ray" has NO conclusion. The positive
-- experiment failed twice and the negative one succeeded, but the positive
-- failure was explained by the ShuttersOpen gate -- so that experiment could
-- fail for a reason other than the one under test, which is exactly the thing
-- CLAUDE 0.26 (1) says disqualifies it. Nothing has been measured since.
--
-- THE EXPERIMENT. One variable: the character's CanQuery flag. Everything else
-- is held identical -- the same park point (the control's own position, so the
-- six-stud range gate is met by construction), the same eye, the same camera, a
-- control that has NO phase gate of its own (Engine:Command line 119 is the only
-- global gate, and MONITOR POWER is a bare toggle that no branch guards, so the
-- boot chain, the shutters, the quota and the phase are all out of the picture
-- before the first click).
--
-- Three arms, one variable:
--   arm off : CanQuery = false, body at the control   (what every rig so far shipped)
--   arm on  : CanQuery = true,  body at the control   (the character is a queryable body on the ray)
--   arm up  : CanQuery = true,  body lifted 4 studs   (queryable, but clear of the ray)
-- `on` versus `off` is the question. `on` versus `up` is the control that says
-- whether a yes/no difference came from the ray or from the flag itself.
--
-- TWO INDEPENDENT CHANNELS, because either alone is weak. This file reports the
-- DELIVERY oracle -- the engine's own `[ReactorBackend][Control] <player> ->
-- <LABEL>` line, which is the only proof a click reached the binder (CLAUDE 0.26:
-- a refused delivery and a click that never landed are different events and the
-- log distinguishes them). __ray_camhold.luau reports the MECHANISM -- what the
-- click ray actually hits -- which turns "no delivery" into "the ray hit X".
-- A delivery outage with no mechanism is a coincidence; a delivery outage whose
-- mechanism reads `rayAll hits HumanoidRootPart` is a cause.
--
-- THE AIM IS A READOUT, NOT AN ASSUMPTION (learned the hard way this session).
-- The first version of this file picked the eye with the Phase 128 rig's rule:
-- cast horizontally at the CONTROL'S OWN HEIGHT and take the first clear
-- direction. That answered a different question. COOLING FAN SWITCH 1 is
-- recessed behind the ThermalConsole face, so all 16 of those directions were
-- "clear" at the control's height while the actual eye-to-control segment was
-- blocked from every one of them -- and the rig would have clicked a CFLever and
-- recorded a clean, silent, entirely wrong negative. It is CLAUDE 0.18 (fifth
-- face): a word ("open") that makes the choice for you, so what you read is not a
-- measurement. findEye now requires the segment the click will actually travel,
-- and reports what that segment hits with the character excluded. A park whose
-- `eyeHits` is not the control is a VOID park, and the Status line says so.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10): newlines come from string.char(10), and
-- no inner double quote is ever needed.

local RunService = game:GetService('RunService')
local LogService = game:GetService('LogService')
local Players = game:GetService('Players')
local ws = game.Workspace
local NL = string.char(10)
-- SELF-TERMINATION. Destroying a Script stops its main thread but NOT the
-- threads it spawned, so a re-injection over a live one leaves the old actuator
-- and the old log tap running -- measured this session as two sets of lines at
-- the same t= in one report. Every loop below therefore also checks that this
-- script is still in the tree, which is the one condition Destroy() does change.
local me = script

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

-- ========== THE DELIVERY ORACLE ==========
-- Four shapes, and only the first is a landing:
--   `<player> -> <LABEL>`      reached the binder; carried to Engine:Command
--   `rejected: <err>`          reached it and the ENGINE refused
--   `[Gate] refused ...`       never reached the binder at all
--   nothing                    the click never got to the detector
-- READ THE PAIR, NOT THE LINE. ControlBinder prints the `-> <LABEL>` line even
-- when Engine:Command returned false, so a landing is `-> ` AND no `rejected:`
-- beside it. And `[Gate]` is CUMULATIVE and rate-limited to one warn per 5 s,
-- so it must be read as a delta.
LogService.MessageOut:Connect(function(message, kind)
    if me.Parent == nil then return end
    local ok, err = pcall(function()
        local text = tostring(message)
        if string.find(text, 'ReactorBackend', 1, true) or string.find(text, '[Control]', 1, true) then
            push(string.format('%s %s', tostring(kind), text))
        end
    end)
    if not ok then push('LOG TAP DIED: ' .. tostring(err)) end
end)

-- ========== DID THE DETECTOR FIRE AT ALL ==========
-- The delivery line proves a click reached ControlBinder. This one step earlier
-- proves it reached the DETECTOR. The two failure shapes are otherwise identical
-- from the outside -- both are silence -- and they call for opposite fixes: no
-- detector line means the ray never activated the ClickDetector, so the question
-- is about input or geometry, not about the binder.
task.spawn(function()
    local consoles = ws:WaitForChild('Consoles', 30)
    if not consoles then push('NO CONSOLES'); return end
    local armed = 0
    for _, d in ipairs(consoles:GetDescendants()) do
        if d:IsA('ClickDetector') then
            local label = d.Parent.Name
            local t = d.Parent:FindFirstChild('ClickPartText')
            if t and t:IsA('StringValue') then label = t.Value end
            armed += 1
            d.MouseClick:Connect(function(player)
                if me.Parent == nil then return end
                push('DETECTOR ' .. label .. ' by ' .. player.Name)
            end)
        end
    end
    push('DETECTOR WATCH ARMED on ' .. tostring(armed))
end)

-- ========== THE CHARACTER ==========
-- `queryable` is the one variable. Everything else in this function is fixed.
local function mute(queryable)
    local player = Players:GetPlayers()[1]
    local character = player and player.Character
    if not character then return nil end
    for _, part in ipairs(character:GetDescendants()) do
        if part:IsA('BasePart') then
            part.Transparency = 1
            part.CanCollide = false
            part.CanQuery = queryable
            part.CanTouch = false
        end
    end
    local root = character:FindFirstChild('HumanoidRootPart')
    if root then root.Anchored = true; root.CFrame = CFrame.new(0, -500, 0) end
    return character
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

-- THE EYE IS WHERE THE CLICK CAN ACTUALLY TRAVEL FROM.
-- Candidate eyes ring the control at three radii and four heights; a candidate
-- is accepted only if the segment from it to the control's own centre hits the
-- control itself, with the CHARACTER EXCLUDED. Excluding the character is what
-- makes this CanQuery-independent, so both arms are handed the SAME eye and the
-- arms differ in the flag and in nothing else.
--
-- The largest radius is tried first so the eye is as far from the console as the
-- click allows; the shortest is 2.5, well inside the six-stud interaction range.
local function findEye(part, character)
    local aim = part.Position
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = {character}
    for _, dist in ipairs({3.5, 5, 2.5}) do
        for _, lift in ipairs({0.7, 2.5, 4.5, 6.5}) do
            for i = 0, 15 do
                local angle = math.rad(i * 22.5)
                local dir = Vector3.new(math.cos(angle), 0, math.sin(angle))
                local eye = aim + dir * dist + Vector3.new(0, lift, 0)
                local hit = ws:Raycast(eye, aim - eye, params)
                if hit and (hit.Instance == part or hit.Instance:IsDescendantOf(part)) then
                    return eye, dir, lift, dist, hit.Instance
                end
            end
        end
    end
    return nil
end

-- HOW MANY character parts sit on the segment from the eye to the control.
-- NOTE WHAT THIS MEASURES: raycasts respect CanQuery, so this is 0 in the off
-- arm and is not a neutral description of the geometry. It is a SECOND reading of
-- the same flag, from the server's side -- 0 versus several is the flag working,
-- stated as geometry. The arms' comparability is established by the root and eye
-- coordinates in the Status line instead, which do not depend on CanQuery at all:
-- identical coordinates in two arms means the park did not move, and then any
-- delivery difference has to be the flag.
local function partsOnSegment(eye, aim, character)
    local dir = (aim - eye)
    local dist = dir.Magnitude
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Include
    params.FilterDescendantsInstances = {character}
    local hits = 0
    local from = eye
    for _ = 1, 8 do
        local hit = ws:Raycast(from, dir.Unit * dist, params)
        if not hit then break end
        hits += 1
        from = hit.Position + dir.Unit * 0.05
        if (from - eye).Magnitude >= dist then break end
    end
    return hits
end

local function park(spec)
    local label, arm = string.match(spec, '^(.-)|(.*)$')
    if not label then return 'BAD SPEC ' .. spec end
    local queryable = (arm == 'on' or arm == 'up')
    local lift = (arm == 'up') and 4 or 0
    local character = mute(queryable)
    if not character then return 'NO CHARACTER' end
    local part = findControl(label)
    if not part then return 'MISS ' .. label end
    local root = character:FindFirstChild('HumanoidRootPart')
    if not root then return 'NO ROOT ' .. label end
    root.CFrame = CFrame.new(part.Position + Vector3.new(0, lift, 0))
    local eye, dir, eyeLift, eyeDist, eyeHit = findEye(part, character)
    if not eye then
        probe:SetAttribute('Status', 'NO EYE for ' .. label .. ' -- every candidate segment is blocked')
        probe:SetAttribute('Scan', string.format('%s|%s|VOID|%.2f', label, arm, ws:GetServerTimeNow()))
        push('NO EYE for ' .. label)
        return 'NO EYE ' .. label
    end
    probe:SetAttribute('EyeX', eye.X); probe:SetAttribute('EyeY', eye.Y); probe:SetAttribute('EyeZ', eye.Z)
    probe:SetAttribute('AimX', part.Position.X)
    probe:SetAttribute('AimY', part.Position.Y)
    probe:SetAttribute('AimZ', part.Position.Z)
    local onSegment = partsOnSegment(eye, part.Position, character)
    local reach = (root.Position - part.Position).Magnitude
    probe:SetAttribute('Arm', arm)
    probe:SetAttribute('OnSegment', onSegment)
    -- Root and eye in absolute coordinates: these are what establish that two
    -- arms are the same experiment. They never read CanQuery, so they cannot be
    -- fooled by the variable under test. `eyeHits` is the park's own verdict on
    -- whether it is aimed at all -- the readout whose absence cost this session
    -- one whole wrong experiment.
    probe:SetAttribute('EyeHits', eyeHit:GetFullName())
    probe:SetAttribute('Status', string.format(
        'arm=%s canQuery=%s lift=%d onSegment=%d reach=%.2f eyeLift=%.1f eyeDist=%.1f root=(%.2f,%.2f,%.2f) eye=(%.2f,%.2f,%.2f) eyeHits=%s %s',
        arm, tostring(queryable), lift, onSegment, reach, eyeLift, eyeDist,
        root.Position.X, root.Position.Y, root.Position.Z,
        eye.X, eye.Y, eye.Z, eyeHit.Name, label))
    -- Scan is written LAST and carries the arm, so the client measures exactly
    -- once per park and cannot mistake a re-read of the old value for a new event.
    probe:SetAttribute('Scan', string.format('%s|%s|%.2f', label, arm, ws:GetServerTimeNow()))
    push(probe:GetAttribute('Status'))
    return 'PARK ' .. label .. ' ' .. arm
end

task.spawn(function()
    local seen = ''
    while true do
        if me.Parent == nil then return end
        local ok, err = pcall(function()
            local value = cmd.Value
            if value ~= seen and value ~= '' then
                seen = value
                push(park(value))
            end
        end)
        if not ok then push('ACTUATOR DIED: ' .. tostring(err)) end
        task.wait(0.1)
    end
end)

-- ========== THE NUMBERS ==========
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
        for _, key in ipairs({'TemperatureVal', 'PressureVal', 'OutputVal', 'EnergyVal', 'QuotaVal'}) do
            local v = core:FindFirstChild(key)
            if v and v:IsA('ValueBase') then
                local value = v.Value
                if last[key] ~= value then last[key] = value; parts[#parts + 1] = key .. '=' .. tostring(value) end
            end
        end
    end
    if #parts > 0 then push(table.concat(parts, ' ')) end
end

-- Fan state is the click's own footprint: `fan` is a bare toggle, so the arm
-- that lands and the arm that does not are told apart by this readout as well.
local function fanLine()
    local backend = game.ServerScriptService:FindFirstChild('ReactorBackend')
    local engine = backend and backend:GetAttribute('RuntimePhase')
    local stats = ws:FindFirstChild('Stats')
    local fans = stats and stats:FindFirstChild('Fans')
    if not fans then return end
    local on = {}
    for i = 1, 6 do
        local v = fans:FindFirstChild('Fan' .. i)
        -- The value may be a BoolValue or a folder holding one; probe both rather
        -- than assuming, because a wrong read here returns nothing at all.
        local value = nil
        if v and v:IsA('ValueBase') then value = v.Value
        elseif v then
            for _, c in ipairs(v:GetChildren()) do
                if c:IsA('BoolValue') then value = c.Value end
            end
        end
        on[#on + 1] = (value == true) and '1' or (value == false) and '0' or '?'
    end
    local text = 'fans=' .. table.concat(on, '') .. ' phase=' .. tostring(engine)
    if last.__fans ~= text then last.__fans = text; push(text) end
end

local ok, err = pcall(function()
    push('RAY PROBE UP')
    local frames = 0
    while frames < 60 * 60 * 20 do
        if me.Parent == nil then return end
        frames += 1
        local fine, problem = pcall(scan)
        if not fine then push('SCAN DIED: ' .. tostring(problem)); return end
        pcall(fanLine)
        RunService.Heartbeat:Wait()
    end
    push('RAY PROBE HIT ITS OWN FRAME LIMIT')
end)
if not ok then push('RAY PROBE DIED OUTSIDE: ' .. tostring(err)) end
