local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- fireclickdetector changed nothing on the server.  Two very different stories
-- produce that identical result, and they need different fixes:
--   (a) the signal never fired at all  -> the executor's function is a no-op
--   (b) the signal fired, but only in the CLIENT's VM -> the server never heard
--       it, because a real ClickDetector reaches the server by the client
--       turning an input event into a remote, and a bare signal fire skips that
-- One sentinel on the same signal tells them apart: if MY listener fires, the
-- signal fired.  Measure the local signal and the server state in one pass so
-- neither can be mistaken for the other.
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

-- Closer than last time: the last position measured 6.05 studs in 3D against a
-- 6-stud activation distance, so "in range" was decided by a rounding error.
hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.5)

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
local shut = big:FindFirstChild('ShutClickPart')
local cdStart = start and start:FindFirstChildOfClass('ClickDetector')
local cdShut = shut and shut:FindFirstChildOfClass('ClickDetector')

local heard = {}          -- which of my own listeners the fire reached
local function watch(tag, cd)
  if cd == nil then return end
  pcall(function()
    cd.MouseClick:Connect(function() heard[tag] = (heard[tag] or 0) + 1 end)
  end)
end
watch('start', cdStart)
watch('shut', cdShut)

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
local method = 'none'
if type(fireclickdetector) == 'function' and cdStart then
  local ok, err = pcall(fireclickdetector, cdStart)
  method = ok and 'fireclickdetector' or ('FAILED: ' .. tostring(err))
else
  method = 'unavailable (have=' .. tostring(type(fireclickdetector)) .. ')'
end

task.wait(1.0)
local heardImmediately = {}
for k, v in pairs(heard) do heardImmediately[k] = v end

task.wait(9.0)
local after = stats()

local agg = { tok = TOKEN, method = method,
  heard_immediate = heardImmediately, heard_final = heard,
  signalFired = (heardImmediately.start or 0) > 0,
  serverChanged = before ~= after,
  before = before, after = after,
  dist3d = string.format('%.2f', (hrp.Position - start.Position).Magnitude),
}
return agg
