local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Press the master start-up switch, and report which call actually did it.
-- fireclickdetector fires the signal directly and bypasses the input pipeline's
-- distance gate; the MouseClick:Fire fallback fires only the CLIENT's listeners,
-- so on a server-authoritative game it can look identical here and do nothing
-- there.  The name of what ran is therefore part of the result.
local function snap()
  local S = workspace:FindFirstChild('Stats')
  if not S then return { stats = 'no Stats' } end
  local function v(p)
    local n = S
    for seg in p:gmatch('[^.]+') do
      if n == nil then return '?' end
      n = n:FindFirstChild(seg)
    end
    return n and tostring(n.Value) or '?'
  end
  return {
    start = v('GameStart'), active = v('GameActive'),
    temp = v('Core.TemperatureVal'), press = v('Core.PressureVal'),
    rad = v('Core.RadiationVal'), out = v('Core.OutputVal'),
    integ = v('HDEF.IntegrityVal'), cbl1 = v('CBL1.Active'),
    fans = v('Fans.Fan1'),
  }
end

local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end
hrp.CFrame = CFrame.new(110.4, 284.5, 4.5)
task.wait(3.0)

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local part = big:FindFirstChild('StartClickPart')
local cd = part and part:FindFirstChildOfClass('ClickDetector')
if cd == nil then return { tok = TOKEN, err = 'no clickdetector', kids = #big:GetChildren() } end

local before = snap()
local method = 'none'
if type(fireclickdetector) == 'function' then
  local ok, err = pcall(fireclickdetector, cd)
  method = ok and 'fireclickdetector' or ('fireclickdetector FAILED: ' .. tostring(err))
else
  local ok, err = pcall(function() cd.MouseClick:Fire(P.LocalPlayer) end)
  method = ok and 'MouseClick:Fire (fallback)' or ('fallback FAILED: ' .. tostring(err))
end

task.wait(10)
local after = snap()

local delta = {}
for k, v in pairs(after) do
  if before[k] ~= v then delta[k] = tostring(before[k]) .. ' -> ' .. tostring(v) end
end

return {
  tok = TOKEN, method = method,
  maxDist = cd.MaxActivationDistance,
  before = before, after = after, delta = delta,
}
