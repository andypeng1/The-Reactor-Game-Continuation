local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Two synthesizers exist and they are not interchangeable, so each is tried on
-- its own and the stats are read between them.  If both ran before one read, a
-- success could not be attributed to either -- the same reason _tmp_fire.luau
-- reported the NAME of what it ran instead of just the outcome.
--
-- ClickButton1 took a Vector2 (the Vector3 error named the expected type, which
-- is what that error was for).  VirtualInputManager wants a button index; 0 is
-- MouseButton1.
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.0)

local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
local function aim()
  cam.CFrame = CFrame.lookAt(start.Position + Vector3.new(0, 2.2, 3.2), start.Position)
end
aim()
task.wait(0.4); aim(); task.wait(0.2)

local vu = game:GetService('VirtualUser')
local vim = game:GetService('VirtualInputManager')
local inset = game:GetService('GuiService'):GetGuiInset()

local function stats()
  local S = workspace:FindFirstChild('Stats')
  if not S then return 'no Stats' end
  local t = {}
  for _, seg in ipairs({ 'GameStart', 'GameActive', 'Core.TemperatureVal', 'Core.PressureVal' }) do
    local n = S
    for s in seg:gmatch('[^.]+') do n = n and n:FindFirstChild(s) end
    t[#t+1] = seg .. '=' .. (n and tostring(n.Value) or '?')
  end
  return table.concat(t, ' ')
end

local function where()
  aim()
  local vp3, visible = cam:WorldToViewportPoint(start.Position)
  return Vector2.new(vp3.X, vp3.Y + inset.Y), visible and vp3.Z > 0, vp3
end

local log = {}
local base = stats()

-- ---- attempt 1: VirtualUser:ClickButton1 -----------------------------------
local p1, vis1 = where()
task.wait(0.15)
local ok1, err1 = pcall(function() vu:ClickButton1(p1) end)
log[#log+1] = string.format('ClickButton1(%s) -> %s', tostring(p1), ok1 and 'called' or ('FAILED: ' .. tostring(err1)))
task.wait(6.0)
local s1 = stats()
log[#log+1] = 'after ClickButton1: ' .. s1
local won = s1 ~= base

-- ---- attempt 2: VirtualInputManager down/up (only if 1 changed nothing) -----
if not won then
  local p2, vis2 = where()
  task.wait(0.15)
  pcall(function() vim:SendMouseMoveEvent(p2.X, p2.Y, false) end)
  task.wait(0.15)
  local ok2a, err2a = pcall(function() vim:SendMouseButtonEvent(p2.X, p2.Y, 0, true, false) end)
  task.wait(0.10)
  local ok2b, err2b = pcall(function() vim:SendMouseButtonEvent(p2.X, p2.Y, 0, false, false) end)
  log[#log+1] = string.format('VIM down/up(%s) -> %s / %s', tostring(p2),
    ok2a and 'down' or ('down FAILED: ' .. tostring(err2a)),
    ok2b and 'up' or ('up FAILED: ' .. tostring(err2b)))
  task.wait(6.0)
  local s2 = stats()
  log[#log+1] = 'after VIM: ' .. s2
  won = s2 ~= base
end

local p3, vis3, vp3 = where()
return {
  tok = TOKEN,
  base = base,
  final = stats(),
  serverChanged = won,
  log = log,
  onScreen = tostring(vis3),
  screenPt = tostring(p3),
  camT = tostring(cam.CameraType),
}
