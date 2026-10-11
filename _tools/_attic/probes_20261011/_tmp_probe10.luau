local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- The lever is server-side (no client LocalScript exists, no control remote, no
-- prompt), so the engine's own input path is the only road left.  That road is
-- VirtualInputManager, and it refuses a 5th-only call with "Argument 6 missing"
-- and refuses 0 as the 6th with "unable to cast value to Object".
--
-- Rather than guess which Instance, offer several and read the error each one
-- produces: the error names the class it wanted, which is a fact, while my guess
-- at the signature is not.  The sentinel stays attached so "the client processed
-- the click" and "the server reacted" remain separately visible.
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
local cd = start:FindFirstChildOfClass('ClickDetector')
local heard = 0
pcall(function() cd.MouseClick:Connect(function() heard = heard + 1 end) end)

hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.0)

local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
local function aim()
  cam.CFrame = CFrame.lookAt(start.Position + Vector3.new(0, 2.2, 3.2), start.Position)
end
aim(); task.wait(0.4); aim(); task.wait(0.2)

local vim = game:GetService('VirtualInputManager')
local inset = game:GetService('GuiService'):GetGuiInset()
local vp3 = cam:WorldToViewportPoint(start.Position)
local X, Y = vp3.X, vp3.Y + inset.Y

local candidates = {
  game = game,
  workspace = workspace,
  currentCamera = cam,
  localPlayer = P.LocalPlayer,
  playerGui = P.LocalPlayer and P.LocalPlayer:FindFirstChild('PlayerGui'),
  coreGui = game:GetService('CoreGui'),
}

local tries = {}
for label, inst in pairs(candidates) do
  if inst ~= nil then
    local ok, err = pcall(function() vim:SendMouseButtonEvent(X, Y, 0, false, false, inst) end)
    tries[#tries+1] = string.format('6th=%s -> %s', label, ok and 'ACCEPTED' or tostring(err))
  end
end
table.sort(tries)

-- If any was accepted, do a real down/up with it and watch the sentinel.
local used, before, after = 'none', nil, nil
local function stats()
  local S = workspace:FindFirstChild('Stats')
  if not S then return 'no Stats' end
  local t = {}
  for _, seg in ipairs({ 'GameStart', 'GameActive', 'Core.TemperatureVal' }) do
    local n = S
    for s in seg:gmatch('[^.]+') do n = n and n:FindFirstChild(s) end
    t[#t+1] = seg .. '=' .. (n and tostring(n.Value) or '?')
  end
  return table.concat(t, ' ')
end
before = stats()
local accepted = nil
for _, label in ipairs({ 'game', 'workspace', 'currentCamera', 'playerGui', 'localPlayer', 'coreGui' }) do
  local inst = candidates[label]
  if inst then
    if pcall(function() vim:SendMouseButtonEvent(X, Y, 0, false, false, inst) end) then accepted = inst; used = label break end
  end
end
if accepted then
  aim(); task.wait(0.15)
  pcall(function() vim:SendMouseMoveEvent(X, Y, false) end)
  local h0 = heard
  pcall(function() vim:SendMouseButtonEvent(X, Y, 0, true, false, accepted) end)
  task.wait(0.12)
  pcall(function() vim:SendMouseButtonEvent(X, Y, 0, false, false, accepted) end)
  task.wait(4.0)
  after = stats()
  tries[#tries+1] = string.format('clicked with %s: sentinel %d->%d  %s', used, h0, heard, after)
end

return {
  tok = TOKEN, tries = tries, used = used,
  before = before, after = after,
  serverChanged = before ~= (after or before),
  sentinel = heard,
}
