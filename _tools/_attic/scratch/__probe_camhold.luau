-- __probeCamHold -- a Play-session-only LocalScript for Players.<me>.PlayerScripts.
--
-- WHY THE CLIENT HAS TO OWN THIS. The camera is the client's own object: whatever
-- the server writes to workspace.CurrentCamera, the client's default camera script
-- overwrites on the next frame. The click ray, meanwhile, is cast by the client
-- from ITS camera through ITS mouse position -- so the camera is the one piece of
-- the rig that cannot be moved from the server datamodel.
--
-- WHY IT IS NOT A ONE-SHOT SETTING EITHER. Setting camera.CFrame once and leaving
-- CameraType alone lasts one frame. Setting CameraType = Scriptable stops the
-- default scripts from moving it, but a LocalScript that only runs once still
-- loses the CFrame to whatever ran before it in the frame. Binding to
-- RenderStep at Camera+1 means this runs after the camera stage, every frame, so
-- the pose in the attributes is the pose the click is cast from. CLAUDE 0.25 (2)
-- is the same fact from the other side: a holder that is still bound is what makes
-- screen_capture show the HOLDER's view -- which here is the point, and is why it
-- must be unbound before any picture is trusted as the world's own view.
--
-- WHY THE SERVER PARK AND NOT A CLIENT ONE. The character is client-owned, so a
-- LocalScript CAN move it -- but the server's ControlBinder measures reach() from
-- the server's copy of the root, and the humanoid keeps applying its own forces to
-- an unanchored character. Anchoring and placing it from the server makes the pose
-- the gate reads exactly the pose that was asked for. So: server parks and aims,
-- client only follows the aim.
--
-- WHAT IT READS. Six attributes on workspace.__probe, written by __probeAgent:
-- EyeX/Y/Z and AimX/Y/Z. Attributes replicate, so the server can set them and this
-- script sees them without any RemoteEvent to keep in sync.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10): newlines come from string.char(10).

local Players = game:GetService('Players')
local RunService = game:GetService('RunService')
local ws = game.Workspace
local NL = string.char(10)

-- The log lives on the client, so it is readable through the Client datamodel and
-- not through the server's. That is deliberate: the numbers that matter (phase,
-- Stats, control delivery) are the server agent's, and this file only has to say
-- whether the camera is actually following.
local holder = ws:FindFirstChild('__probeLog')
if not holder then
    holder = Instance.new('StringValue')
    holder.Name = '__probeLog'
    holder.Parent = ws
end

local lines = {}
local function say(text)
    lines[#lines + 1] = text
    if #lines > 40 then table.remove(lines, 1) end
    holder.Value = table.concat(lines, NL)
end

local applied, misses = 0, 0
local lastStatus = nil

RunService:BindToRenderStep('__probeCamHold', Enum.RenderPriority.Camera.Value + 1, function()
    local ok, err = pcall(function()
        local probe = ws:FindFirstChild('__probe')
        if not probe then misses += 1; return end
        local ex, ey, ez = probe:GetAttribute('EyeX'), probe:GetAttribute('EyeY'), probe:GetAttribute('EyeZ')
        local ax, ay, az = probe:GetAttribute('AimX'), probe:GetAttribute('AimY'), probe:GetAttribute('AimZ')
        if not (ex and ey and ez and ax and ay and az) then return end
        local camera = ws.CurrentCamera
        if not camera then return end
        camera.CameraType = Enum.CameraType.Scriptable
        camera.CFrame = CFrame.lookAt(Vector3.new(ex, ey, ez), Vector3.new(ax, ay, az))
        applied += 1
        local status = tostring(probe:GetAttribute('Status'))
        if status ~= lastStatus then
            lastStatus = status
            local vp = camera.ViewportSize
            say(string.format('AIM %s | vp %dx%d | applied %d misses %d',
                status, vp.X, vp.Y, applied, misses))
        end
    end)
    if not ok then say('HOLDER DIED: ' .. tostring(err)) end
end)

say('HOLDER UP at ' .. tostring(ws:GetServerTimeNow()))
