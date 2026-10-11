local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- One shot per call: the executor kills a task at 60 s, so the spacing between
-- samples has to come from outside the game.  A script that tried to wait 135 s
-- was cut off mid-run, and "the script was killed" and "the label never changed"
-- would have looked the same from here.
local P = game:GetService('Players')
local out = { tok = TOKEN, players = #P:GetPlayers() }

local pg = P.LocalPlayer:FindFirstChild('PlayerGui')
local sg = pg and pg:FindFirstChild('ScreenGui')
if sg then
  for _, d in ipairs(sg:GetDescendants()) do
    if d:IsA('TextLabel') and d.Text ~= '' then
      if d.Text:match('WAITING FOR PLAYERS') then out.wait = d.Text
      elseif d.Text:match('%d+:%d+%s*[AP]M') then out.clock = out.clock or d.Text end
    end
  end
end

local S = workspace:FindFirstChild('Stats')
if S then
  local a = S:FindFirstChild('GameStart')
  local b = S:FindFirstChild('GameActive')
  out.start = a and a.Value
  out.active = b and b.Value
end
out.t = os.time()
return out
