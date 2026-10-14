-- __rayCamhold -- Play-session-only, dropped into StarterPlayerScripts as a
-- LocalScript. The MECHANISM half of the ray experiment; __ray_probe.luau is the
-- DELIVERY half. Read that file first for what the experiment is.
--
-- Three jobs, in order of importance:
--
--  1. HOLD THE CAMERA. The park writes Eye*/Aim* attributes; without a camera on
--     that eye the mouse ray points wherever the player's camera happens to be
--     and the click is aimed at nothing. This is the Phase 105/123 rig, unchanged
--     -- except the bind name is left as __probeCamHold so it can be unbound from
--     any VM by name (CLAUDE 0.25 (2): a still-bound holder blinds screen_capture,
--     and a name is global).
--
--  2. RECORD THE MOUSE'S TARGET whenever it changes. `Mouse.Target` is the
--     engine's own answer to "what is under the pointer", computed with whatever
--     TargetFilter is in force -- so this line settles whether the character can
--     block AT ALL, independently of any ray we cast ourselves. If the game sets
--     TargetFilter to the character, the character is invisible to clicks and the
--     whole question is moot; that would be a finding, not a null result.
--
--  3. ON EACH NEW PARK, cast the click ray ourselves three ways and report all
--     three. Same origin, same direction, three filters:
--       rayAll   -- nothing filtered: what a naive ray sees
--       rayNoChar-- the character excluded
--       rayGate  -- the character excluded AND the control itself excluded,
--                   i.e. "what is behind the control", to prove the eye is not
--                   simply buried in geometry
--     A difference between rayAll and rayNoChar IS the character blocking, stated
--     as geometry. Identical lines mean the character is not on the ray at all.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10). Newlines via string.char(10).

local Players = game:GetService('Players')
local RunService = game:GetService('RunService')
local ws = game.Workspace
local NL = string.char(10)
-- SELF-TERMINATION, same reason as __ray_probe.luau: Destroy() stops the main
-- thread and leaves the spawned ones running, so a re-injection would otherwise
-- leave a second camera holder and a second mouse watcher in the same VM.
local me = script

local player = Players.LocalPlayer
local camera = ws.CurrentCamera

local log = ws:FindFirstChild('__probeLog')
if not log then
    log = Instance.new('StringValue')
    log.Name = '__probeLog'
    log.Parent = ws
end

local lines = {}
local t0 = ws:GetServerTimeNow()
local function push(text)
    lines[#lines + 1] = string.format('t=%.3f %s', ws:GetServerTimeNow() - t0, text)
    if #lines > 300 then table.remove(lines, 1) end
    log.Value = table.concat(lines, NL)
end

-- ========== 1. THE CAMERA ==========
local EYE = Vector3.new()
local AIM = Vector3.new()
local haveTarget = false

RunService:UnbindFromRenderStep('__probeCamHold')
RunService:BindToRenderStep('__probeCamHold', Enum.RenderPriority.Camera.Value + 1, function()
    -- A render-step bind outlives the script that made it, so it has to be the
    -- first thing dropped when this script leaves the tree -- otherwise a stale
    -- holder keeps pinning the camera with no script behind it (CLAUDE 0.25 (2)).
    if me.Parent == nil then
        RunService:UnbindFromRenderStep('__probeCamHold')
        return
    end
    local probe = ws:FindFirstChild('__probe')
    if not probe then return end
    local ex, ey, ez = probe:GetAttribute('EyeX'), probe:GetAttribute('EyeY'), probe:GetAttribute('EyeZ')
    local ax, ay, az = probe:GetAttribute('AimX'), probe:GetAttribute('AimY'), probe:GetAttribute('AimZ')
    if not (ex and ey and ez and ax and ay and az) then return end
    EYE = Vector3.new(ex, ey, ez)
    AIM = Vector3.new(ax, ay, az)
    haveTarget = true
    if camera then
        camera.CameraType = Enum.CameraType.Scriptable
        camera.CFrame = CFrame.lookAt(EYE, AIM)
    end
end)

-- ========== 2. WHAT THE POINTER IS OVER ==========
-- Every change, so the log carries the whole history of the mouse without a
-- per-frame flood. TargetFilter is printed once on the first line, because a
-- filter that already excludes the character changes what the question even is.
local mouse = player:GetMouse()
local function describe(instance)
    if not instance then return 'nil' end
    local parent = instance.Parent
    return string.format('%s(%s) in %s', instance.Name, instance.ClassName,
        parent and parent.Name or 'nil')
end

-- ========== DID THE INPUT EVEN ARRIVE ==========
-- One step before the detector: whether the synthetic click is delivered to this
-- VM at all, and what the engine thought was under the pointer when it was. A
-- click that never arrives and a click that arrives aimed at the wrong thing
-- look the same from the server, and they are different problems.
game:GetService('UserInputService').InputBegan:Connect(function(input, processed)
    if me.Parent == nil then return end
    push(string.format('input %s processed=%s', input.UserInputType.Name, tostring(processed)))
end)
mouse.Button1Down:Connect(function()
    if me.Parent == nil then return end
    push(string.format('BUTTON1DOWN at (%d,%d) target=%s', mouse.X, mouse.Y, describe(mouse.Target)))
end)

task.spawn(function()
    local ok, err = pcall(function()
        push('CAMHOLD UP  targetFilter=' .. describe(mouse.TargetFilter))
        local lastTarget = nil
        while true do
            if me.Parent == nil then return end
            local now = mouse.Target
            if now ~= lastTarget then
                lastTarget = now
                push('mouse -> ' .. describe(now))
            end
            RunService.Heartbeat:Wait()
        end
    end)
    if not ok then push('MOUSE WATCH DIED: ' .. tostring(err)) end
end)

-- ========== 3. THE CLICK RAY, THREE WAYS ==========
local lastScan = nil
local function castFrom(origin, direction, filterList)
    local params = RaycastParams.new()
    if filterList then
        params.FilterType = Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances = filterList
    else
        params.FilterType = Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances = {}
    end
    local hit = ws:Raycast(origin, direction * 40, params)
    if not hit then return 'nil' end
    return string.format('%s(%s) d=%.2f', hit.Instance.Name, hit.Instance.ClassName,
        (hit.Position - origin).Magnitude)
end

local function measure(tag)
    if not haveTarget then push('MEASURE ' .. tag .. ' NO EYE YET'); return end
    local character = player.Character
    local dir = (AIM - EYE)
    local dist = dir.Magnitude
    if dist < 1e-3 then push('MEASURE ' .. tag .. ' EYE ON AIM'); return end
    local unit = dir / dist
    local body = {}
    if character then body = {character} end

    -- The click's own ray first. Whether the mouse is currently at the aim is a
    -- separate fact and is reported, not assumed -- so a stale pointer cannot be
    -- read as a blocked ray.
    local uray = mouse.UnitRay
    local over = mouse.Target
    local atAim = false
    if over then
        local gap = (over.Position - AIM).Magnitude
        atAim = gap < 3
    end
    push(string.format('MEASURE %s mouseTarget=%s mouseAtAim=%s', tag, describe(over), tostring(atAim)))
    push('  mouseRay  ' .. castFrom(uray.Origin, uray.Direction, nil))
    push('  mouseNoCh ' .. castFrom(uray.Origin, uray.Direction, body))
    push('  eyeAll    ' .. castFrom(EYE, unit, nil))
    push('  eyeNoChar ' .. castFrom(EYE, unit, body))
    local gatePart = nil
    local probe = ws:FindFirstChild('__probe')
    if probe and over then gatePart = over end
    local gateFilter = {}
    for _, v in ipairs(body) do gateFilter[#gateFilter + 1] = v end
    if gatePart then gateFilter[#gateFilter + 1] = gatePart end
    push('  eyeNoCharNoPart ' .. castFrom(EYE, unit, gateFilter))

    -- The character's own parts, counted by the client's own raycast -- the
    -- replicated CanQuery, not the server's value, because the client is the VM
    -- the click is built in (CLAUDE 0.23 (2)).
    local queryableParts, totalParts = 0, 0
    if character then
        for _, p in ipairs(character:GetDescendants()) do
            if p:IsA('BasePart') then
                totalParts += 1
                if p.CanQuery then queryableParts += 1 end
            end
        end
    end
    push(string.format('  character parts=%d queryable=%d', totalParts, queryableParts))
end

task.spawn(function()
    local ok, err = pcall(function()
        while true do
            if me.Parent == nil then return end
            local probe = ws:FindFirstChild('__probe')
            if probe then
                local scan = probe:GetAttribute('Scan')
                if scan and scan ~= lastScan then
                    lastScan = scan
                    -- Two beats so the camera bind has placed the eye this frame;
                    -- measuring on the arrival frame would ray from the previous
                    -- park's eye and silently mislabel the arm (CLAUDE 0.27 (2):
                    -- two readings in one session are not one instant).
                    RunService.RenderStepped:Wait()
                    RunService.RenderStepped:Wait()
                    measure(scan)
                end
            end
            task.wait(0.1)
        end
    end)
    if not ok then push('SCAN WATCH DIED: ' .. tostring(err)) end
end)
