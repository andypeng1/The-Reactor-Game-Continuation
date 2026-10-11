local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- The console tree is there but the lever's click part is not, and the character
-- is 1000+ studs away on an upper level.  That is the shape of streaming: the
-- model replicates, its small parts do not, until the client is close enough.
--
-- fireclickdetector calls the signal and does not move the character, so being
-- far away is invisible at fire time -- the click just never reaches the server.
-- So: move first, wait for the client to catch up, THEN look for the part.
local P = game:GetService('Players')
local lp = P.LocalPlayer
local ch = lp and lp.Character
local hrp = ch and ch:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local before = tostring(hrp.Position)
-- The lever sits at about (110.4, 279.6, -0.7); the root rides ~4 studs above
-- the floor, and standing back a couple of studs keeps the character out of the
-- console's own geometry so streaming is not fighting a collision.
hrp.CFrame = CFrame.new(110.4, 284.5, 4.5)
task.wait(3.5)

local lever = workspace:FindFirstChild('Consoles')
local main = lever and lever:FindFirstChild('MainReactorConsole')
local big = main and main:FindFirstChild('StartUpBigLever')
local part = big and big:FindFirstChild('StartClickPart')
local cd = part and part:FindFirstChildOfClass('ClickDetector')

local siblings = {}
if big then
  for _, c in ipairs(big:GetChildren()) do
    siblings[#siblings+1] = c.Name .. '(' .. c.ClassName .. ')'
  end
  table.sort(siblings)
end

return {
  tok = TOKEN,
  from = before,
  to = tostring(hrp.Position),
  reachedPart = part ~= nil,
  leverName = part and part:GetFullName() or 'nil',
  hasCD = cd ~= nil,
  maxDist = cd and cd.MaxDistance or 'no-cd',
  started = workspace:FindFirstChild('Stats') and workspace.Stats.GameStart.Value or '?',
  siblings = siblings,
}
