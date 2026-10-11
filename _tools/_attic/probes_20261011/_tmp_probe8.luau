local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- ClickButton1 accepted the call and did nothing.  Three readings separate the
-- ways that can be true, and they are cheap to take together:
--   * the signal sentinel says whether the CLIENT's ClickDetector even processed
--     the input as a click (if not, the coordinate or the event shape is wrong);
--   * debug.info says how many arguments these natives actually take, instead of
--     my guessing the signature and reading the resulting "argument 6 missing"
--     as a property of the API rather than of my call;
--   * the two coordinate spaces (viewport vs screen, 58 px apart) get tried
--     separately, because the lever is a 0.5-stud pad and 58 px can miss it.
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
local cd = start:FindFirstChildOfClass('ClickDetector')

local heard = 0
pcall(function()
  cd.MouseClick:Connect(function() heard = heard + 1 end)
end)

hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.0)

local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
local function aim()
  cam.CFrame = CFrame.lookAt(start.Position + Vector3.new(0, 2.2, 3.2), start.Position)
end
aim(); task.wait(0.4); aim(); task.wait(0.2)

local vu = game:GetService('VirtualUser')
local vim = game:GetService('VirtualInputManager')
local inset = game:GetService('GuiService'):GetGuiInset()

local arity = {}
local function ar(name, f)
  local ok, n = pcall(function() return debug.info(f, 'a') end)
  arity[name] = ok and n or ('? : ' .. tostring(n))
end
ar('ClickButton1', vu.ClickButton1)
ar('SendMouseButtonEvent', vim.SendMouseButtonEvent)
ar('SendMouseMoveEvent', vim.SendMouseMoveEvent)

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

local base = stats()
local log = {}

local function attempt(label, x, y)
  aim()
  local h0 = heard
  local ok, err = pcall(function() vu:ClickButton1(Vector2.new(x, y)) end)
  task.wait(2.5)
  log[#log+1] = string.format('%s (%.0f,%.0f) call=%s sentinel %d->%d  %s',
    label, x, y, ok and 'ok' or tostring(err), h0, heard, stats())
  return stats() ~= base
end

local vp3, visible = cam:WorldToViewportPoint(start.Position)
local vy = vp3.Y
local sy = vp3.Y + inset.Y
local changed = attempt('viewport-space', vp3.X, vy)
if not changed then
  changed = attempt('screen-space', vp3.X, sy)
end
if not changed then
  -- 6 args per the arity read; the 5-arg call failed only because the 6th was
  -- nil, so give it the same button/down-ness again as a neutral value.
  aim(); task.wait(0.15)
  pcall(function() vim:SendMouseMoveEvent(vp3.X, sy, false) end)
  task.wait(0.15)
  local h0 = heard
  local ok1, e1 = pcall(function() vim:SendMouseButtonEvent(vp3.X, sy, 0, true, false, 0) end)
  task.wait(0.10)
  local ok2, e2 = pcall(function() vim:SendMouseButtonEvent(vp3.X, sy, 0, false, false, 0) end)
  task.wait(2.5)
  log[#log+1] = string.format('VIM 6-arg down/up: %s / %s  sentinel %d->%d  %s',
    ok1 and 'down' or tostring(e1), ok2 and 'up' or tostring(e2), h0, heard, stats())
  changed = stats() ~= base
end

return {
  tok = TOKEN,
  arity = arity,
  base = base,
  final = stats(),
  serverChanged = changed,
  sentinelTotal = heard,
  log = log,
  viewportPt = string.format('%.1f,%.1f', vp3.X, vy),
  screenPt = string.format('%.1f,%.1f', vp3.X, sy),
  vis = tostring(visible),
}
