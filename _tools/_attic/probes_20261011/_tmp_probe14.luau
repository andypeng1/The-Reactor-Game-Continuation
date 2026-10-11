local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Round 1's core came on when the in-game clock reached 720, not when a lever was
-- clicked, so the thing to read is the clock.  Find every time-shaped label rather
-- than assume one path: the recorder aliased it as q.timeText / TimeFrame.TimeLabel
-- and a wrong guess here would read as "no clock".
local P = game:GetService('Players')
local out = { tok = TOKEN, players = #P:GetPlayers() }
local lp = P.LocalPlayer
local pg = lp and lp:FindFirstChild('PlayerGui')
if pg == nil then return { tok = TOKEN, err = 'no PlayerGui' } end

local times = {}
for _, d in ipairs(pg:GetDescendants()) do
  if d:IsA('TextLabel') and d.Text ~= '' then
    local txt = d.Text
    if txt:match('%d+:%d+%s*[AP]M') or txt:match('^%d+:%d+$') or txt:match('[AP]M$') then
      times[#times+1] = d:GetFullName() .. ' = [' .. txt .. ']'
    end
  end
end
if #times > 25 then times = { 'too many: ' .. #times } end
out.timeLabels = times

-- the shift gate: round 1 showed an intermission frame with shift/player labels
local sg = pg:FindFirstChild('ScreenGui')
local iret = {}
if sg then
  for _, d in ipairs(sg:GetDescendants()) do
    if d:IsA('GuiObject') and (d.Name == 'IntermissionFrame' or d.Name == 'WaitFrame'
      or d.Name == 'ShiftLabel' or d.Name == 'PlayerLabel' or d.Name == 'StartupFrame') then
      iret[#iret+1] = string.format('%s vis=%s%s', d.Name, tostring(d.Visible),
        d:IsA('TextLabel') and (' [' .. d.Text .. ']') or '')
    end
  end
end
out.gate = iret

-- the reactor's own state, so the clock reading has something to sit beside
local S = workspace:FindFirstChild('Stats')
if S then
  local t = {}
  for _, seg in ipairs({ 'GameStart', 'GameActive' }) do
    local n = S
    for s in seg:gmatch('[^.]+') do n = n and n:FindFirstChild(s) end
    t[#t+1] = seg .. '=' .. (n and tostring(n.Value) or '?')
  end
  out.stats = table.concat(t, ' ')
end

return out
