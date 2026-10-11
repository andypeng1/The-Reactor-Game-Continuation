local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- fireclickdetector produced no server-side change at all: GameStart stayed
-- false, temp stayed 0.  That is consistent with the signal being fired in the
-- CLIENT's VM only -- a ClickDetector normally works by the client turning a
-- real input event into a remote for the server, and a signal fire skips that
-- step entirely.  So the next thing to try is a real input event, and the first
-- requirement is knowing where on screen the part actually is.
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end
hrp.CFrame = CFrame.new(110.4, 284.5, 4.5)
task.wait(2.5)

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local kids = {}
for _, c in ipairs(big:GetChildren()) do
  kids[#kids+1] = c.Name .. '(' .. c.ClassName .. ')'
end
table.sort(kids)

local part = big:FindFirstChild('StartClickPart')
local cd = part and part:FindFirstChildOfClass('ClickDetector')
local cam = workspace.CurrentCamera

local screen, onScreen, dist = 'no part', false, '?'
if part and cam then
  local v3, visible = cam:WorldToViewportPoint(part.Position)
  screen = string.format('%.0f,%.0f  z=%.1f  vis=%s', v3.X, v3.Y, v3.Z, tostring(visible))
  onScreen = v3.Z > 0 and visible
  local h = hrp.Position
  local d = (Vector3.new(h.X, 0, h.Z) - Vector3.new(part.Position.X, 0, part.Position.Z)).Magnitude
  dist = string.format('%.2f studs horizontal', d)
end

return {
  tok = TOKEN,
  kids = kids,
  partPos = part and tostring(part.Position) or 'nil',
  partSize = part and tostring(part.Size) or 'nil',
  hasCD = cd ~= nil,
  maxDist = cd and cd.MaxActivationDistance or 'no-cd',
  responseRadius = cd and cd.MaxActivationDistance or '?',
  screen = screen,
  onScreen = onScreen,
  dist = dist,
  charPos = tostring(hrp.Position),
  camPos = cam and tostring(cam.CFrame.Position) or 'no cam',
}
