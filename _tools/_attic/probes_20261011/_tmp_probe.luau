local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- What the executor actually exposes, and where the one control I need to press
-- is.  fireclickdetector fired the signal in round 1, but "it worked last time"
-- is not the same as "it is present now" -- and a silent fallback to
-- cd.MouseClick:Fire fires only the CLIENT listeners, which looks identical in
-- code and does nothing on the server.  So the name of what ran is part of the
-- answer, not a detail of the implementation.
local have = {
  fireclickdetector = type(fireclickdetector) == 'function',
  firetouchinterest = type(firetouchinterest) == 'function',
  getgenv = type(getgenv) == 'function',
  request = type(request) == 'function',
}

local lever = workspace:FindFirstChild('Consoles')
local path, cd = 'Consoles?', nil
if lever then
  local main = lever:FindFirstChild('MainReactorConsole')
  if main then
    local big = main:FindFirstChild('StartUpBigLever')
    if big then
      local p = big:FindFirstChild('StartClickPart')
      if p then
        path = p:GetFullName()
        cd = p:FindFirstChildOfClass('ClickDetector')
      end
    end
  end
end

local P = game:GetService('Players')
local lp = P.LocalPlayer
local ch = lp and lp.Character
local hrp = ch and ch:FindFirstChild('HumanoidRootPart')

return {
  tok = TOKEN,
  have = have,
  leverPath = path,
  leverPos = (cd and cd.Parent and tostring(cd.Parent.Position)) or '?',
  hasCD = cd ~= nil,
  maxDist = cd and cd.MaxActivationDistance or '?',
  charPos = hrp and tostring(hrp.Position) or 'no char',
  players = #P:GetPlayers(),
}
