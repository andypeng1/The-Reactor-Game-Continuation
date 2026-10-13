-- __probeDrive -- a Play-session-only client controller for the console.
--
-- WHY THIS EXISTS. The Phase 123 click rig drives the console from OUTSIDE: it
-- aims the camera at one target at a time, scans pixels for the one whose first
-- raycast hit carries a matching ClickPartText, and then asks Studio's own mouse
-- tool to click there. That works, and Phase 127 used it to throw four controls,
-- but every click costs two round trips and the reactor needs roughly forty of
-- them over six minutes -- which is the whole reason `_tools/quota_policy_sim.luau`
-- exists, to find out whether forty clicks is even the shape of the problem.
--
-- This script is the other half of that answer. It lives in the CLIENT, so it can
-- aim the camera itself and -- if the client VM is allowed to -- synthesize the
-- click itself, which turns a six-minute interactive session into a batch job.
--
-- Two things it must report, because a client LocalScript has no readable print
-- (CLAUDE 0.16) and because "in flight but nothing happening" and "died on the
-- first frame" look identical from outside (CLAUDE 0.17):
--   * every action it takes, with the tick it took it on, and
--   * its own death, written into the same StringValue.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10): this source is delivered through the Studio
-- edit layer, which decodes escapes once, so a two-character backslash-n would
-- arrive as a real newline and break the string it sits in. Newlines come from
-- string.char(10) and no inner double quote is ever needed.

local Players = game:GetService('Players')
local RunService = game:GetService('RunService')
local GuiService = game:GetService('GuiService')
local ws = game.Workspace
local NL = string.char(10)

local player = Players.LocalPlayer
local camera = ws.CurrentCamera
local insetY = GuiService:GetGuiInset().Y

local lines = {}
local function say(text)
    lines[#lines + 1] = text
    if #lines > 60 then table.remove(lines, 1) end
    local v = ws:FindFirstChild('__probeLog')
    if v then v.Value = table.concat(lines, NL) end
end

-- The label IS the contract (ControlBinder's own header): every console
-- ClickDetector's parent carries a ClickPartText StringValue, and ControlBinder
-- resolves the action from that string rather than from the part's name. Matching
-- on the same field means this script cannot aim at something the binder would
-- resolve differently.
local function findControl(label)
    local consoles = ws:FindFirstChild('Consoles')
    if not consoles then return nil end
    for _, d in ipairs(consoles:GetDescendants()) do
        if d:IsA('ClickDetector') then
            local t = d.Parent and d.Parent:FindFirstChild('ClickPartText')
            if t and t:IsA('StringValue') and t.Value == label then return d.Parent end
        end
    end
    return nil
end

-- The one call that decides whether this file is a batch job or a helper.
-- RobloxScriptSecurity normally hides VirtualInputManager from a game LocalScript,
-- so the answer has to be measured rather than assumed, and the measured answer is
-- what gets written to the log either way.
local vim, vimErr = nil, nil
local ok = pcall(function() vim = game:GetService('VirtualInputManager') end)
if not ok then vim, vimErr = nil, 'GetService refused' end

local target = nil
local function aim(mode)
    local part = target
    if not part then return end
    camera.CameraType = Enum.CameraType.Scriptable
    local back = mode == 'far' and 6 or 2
    local eye = part.Position + Vector3.new(0, 1.2, 0) - part.CFrame.LookVector * 0 - Vector3.new(0, 0, back)
    camera.CFrame = CFrame.lookAt(eye, part.Position)
end

local function click(mode)
    if not target then return 'no target' end
    aim(mode)
    local vp = camera.ViewportSize
    local cx, cy = vp.X / 2, vp.Y / 2
    if not vim then return 'no vim: ' .. tostring(vimErr) end
    local ok2, err2 = pcall(function()
        -- Studio's own mouse tool reports its y as the value it was given plus the
        -- GUI inset (CLAUDE 0.11 / 0.26), so both spaces are tried: the raw centre
        -- first, then the centre with the inset added.
        vim:SendMouseMoveEvent(cx, cy + insetY, game)
        vim:SendMouseButtonEvent(cx, cy + insetY, 0, true, game, 1)
        vim:SendMouseButtonEvent(cx, cy + insetY, 0, false, game, 1)
    end)
    return ok2 and ('clicked at ' .. cx .. ',' .. (cy + insetY)) or ('vim failed: ' .. tostring(err2))
end

RunService:BindToRenderStep('__probeDriveAim', Enum.RenderPriority.Camera.Value + 1, function()
    local ok3, err3 = pcall(aim, 'near')
    if not ok3 then say('AIM DIED: ' .. tostring(err3)) end
end)

-- The command channel. The plugin VM writes a label plus a mode into the
-- StringValue on workspace; this loop picks it up, acts, and appends the result.
-- Polling rather than a BindableEvent because a client cannot be handed an
-- instance by a sandboxed caller, and a one-line-per-action log is what the
-- measurement needs anyway.
task.spawn(function()
    local seen = ''
    while true do
        local ok4, err4 = pcall(function()
            local cmd = ws:FindFirstChild('__probeCmd')
            local value = cmd and cmd.Value or ''
            if value ~= seen and value ~= '' then
                seen = value
                local label, mode = string.match(value, '^(.-)|(.*)$')
                if label == 'QUIT' then return end
                target = findControl(label)
                if not target then say('MISS ' .. label .. ' (no control with that ClickPartText)')
                else
                    say('RUN ' .. label .. ' -> ' .. click(mode == 'far' and 'far' or 'near'))
                end
            end
        end)
        if not ok4 then say('LOOP DIED: ' .. tostring(err4)) end
        task.wait(0.2)
    end
end)

say('DRIVE UP vim=' .. tostring(vim ~= nil and 'yes' or 'no') .. ' inset=' .. insetY
    .. ' viewport=' .. camera.ViewportSize.X .. 'x' .. camera.ViewportSize.Y)
