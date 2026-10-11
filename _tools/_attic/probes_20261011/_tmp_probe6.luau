local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- A local signal fire cannot reach the server, so the click has to be a real
-- input event.  Two things must hold before synthesizing one, and both are
-- measurable rather than assumable:
--   1. the part must be ON SCREEN -- the earlier reading put it at x=-951 with
--      vis=false, and a click at that coordinate is not a click on the lever,
--      it is a click on whatever happens to live there (or nothing);
--   2. the coordinates must be in the same space the synthesizer uses.  The
--      camera-space and screen-space origins differ by GuiService:GetGuiInset()
--      -- 58 px on this machine -- so a viewport point fed to the mouse API
--      lands 58 px above the target.
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.0)

local cam = workspace.CurrentCamera
-- Stand the camera where the lever fills the centre of the frame.  The offset is
-- along the lever's own facing so the pad is looked at head-on rather than at a
-- grazing angle, which is what makes the raycast actually hit a 0.5-stud pad.
cam.CameraType = Enum.CameraType.Scriptable
local eye = start.Position + Vector3.new(0, 2.2, 3.2)
cam.CFrame = CFrame.lookAt(eye, start.Position)
task.wait(0.4)
cam.CFrame = CFrame.lookAt(eye, start.Position)

local avail = {
  VirtualUser = pcall(function() return game:GetService('VirtualUser') end),
  VIM = pcall(function() return game:GetService('VirtualInputManager') end),
  SendMouseButtonEvent = false,
  SendMouseMoveEvent = false,
  ClickButton1 = false,
}
local vu, vim
pcall(function() vu = game:GetService('VirtualUser') end)
pcall(function() vim = game:GetService('VirtualInputManager') end)
if vim then
  avail.SendMouseButtonEvent = type(vim.SendMouseButtonEvent) == 'function'
  avail.SendMouseMoveEvent = type(vim.SendMouseMoveEvent) == 'function'
end
if vu then avail.ClickButton1 = type(vu.ClickButton1) == 'function' end

local vp3, visible = cam:WorldToViewportPoint(start.Position)
local inset = game:GetService('GuiService'):GetGuiInset()
local sx, sy = vp3.X, vp3.Y + inset.Y
local vps = cam.ViewportSize
local onScreen = visible and vp3.Z > 0 and sx > 0 and sx < vps.X and sy > 0 and sy < vps.Y

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

local before = stats()
local did = {}
-- Refuse to click at a coordinate that is not demonstrably the lever.  A click
-- fired "anyway" would still look like an answer in the stats read below.
if onScreen then
  if vim and type(vim.SendMouseMoveEvent) == 'function' then
    pcall(function() vim:SendMouseMoveEvent(sx, sy, false) end)
    did[#did+1] = 'VIM:MouseMove'
    task.wait(0.15)
  end
  if vu and type(vu.ClickButton1) == 'function' then
    local ok, err = pcall(function() vu:ClickButton1(Vector3.new(sx, sy, 0)) end)
    did[#did+1] = ok and 'VirtualUser:ClickButton1' or ('VU FAILED: ' .. tostring(err))
  elseif vim and type(vim.SendMouseButtonEvent) == 'function' then
    local ok, err = pcall(function() vim:SendMouseButtonEvent(sx, sy, 0, true, false) end)
    did[#did+1] = ok and 'VIM:down' or ('VIM down FAILED: ' .. tostring(err))
    task.wait(0.08)
    pcall(function() vim:SendMouseButtonEvent(sx, sy, 0, false, false) end)
    did[#did+1] = 'VIM:up'
  else
    did[#did+1] = 'no synthesizer available'
  end
else
  did[#did+1] = 'REFUSED: part not on screen'
end

task.wait(8.0)
local after = stats()

return {
  tok = TOKEN,
  avail = avail,
  viewport = string.format('%.0fx%.0f', vps.X, vps.Y),
  insetY = inset.Y,
  viewportPt = string.format('%.0f,%.0f z=%.2f vis=%s', vp3.X, vp3.Y, vp3.Z, tostring(visible)),
  screenPt = string.format('%.0f,%.0f', sx, sy),
  onScreen = onScreen,
  did = did,
  serverChanged = before ~= after,
  before = before,
  after = after,
}
