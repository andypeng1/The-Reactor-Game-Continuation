local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- The signature is measured: VirtualInputManager:SendMouseButtonEvent takes
-- (x, y, mouseButton, isDown, <Instance>, <int>).  So now press the switch for
-- real and read three separate things, because "the reactor started" is only one
-- of the ways this can go and the other two look identical from the stats alone:
--   * did the CLIENT's ClickDetector fire (sentinel)?
--   * did the SERVER's Stats move?
--   * did the lever part itself move (the union swings when it is thrown)?
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
local lever = big:FindFirstChild('LeverUnion')
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

local function stats()
  local S = workspace:FindFirstChild('Stats')
  if not S then return 'no Stats' end
  local t = {}
  for _, seg in ipairs({ 'GameStart', 'GameActive', 'Core.TemperatureVal', 'Core.PressureVal',
                         'HDEF.IntegrityVal', 'CBL1.Active', 'Fans.Fan1' }) do
    local n = S
    for s in seg:gmatch('[^.]+') do n = n and n:FindFirstChild(s) end
    t[#t+1] = seg .. '=' .. (n and tostring(n.Value) or '?')
  end
  return table.concat(t, ' ')
end

local before = stats()
local leverBefore = tostring(lever.CFrame)

aim(); task.wait(0.15)
local vp3 = cam:WorldToViewportPoint(start.Position)
local X, Y = vp3.X, vp3.Y + inset.Y

pcall(function() vim:SendMouseMoveEvent(X, Y, false) end)
task.wait(0.20)
local okD, errD = pcall(function() vim:SendMouseButtonEvent(X, Y, 0, true, game, 1) end)
task.wait(0.12)
local okU, errU = pcall(function() vim:SendMouseButtonEvent(X, Y, 0, false, game, 1) end)

task.wait(6.0)
local after = stats()

return {
  tok = TOKEN,
  pt = string.format('%.0f,%.0f', X, Y),
  down = okD and 'ok' or tostring(errD),
  up = okU and 'ok' or tostring(errU),
  sentinel = heard,
  before = before,
  after = after,
  serverChanged = before ~= after,
  leverMoved = leverBefore ~= tostring(lever.CFrame),
}
