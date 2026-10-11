local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- The gate says "[60]" and never counts down.  If a timer exists it is somewhere
-- else in the intermission -- a separate label, a bar, a second counter -- so read
-- every text the frame owns rather than the one string that matched my pattern.
local P = game:GetService('Players')
local pg = P.LocalPlayer:FindFirstChild('PlayerGui')
local sg = pg and pg:FindFirstChild('ScreenGui')
if sg == nil then return { tok = TOKEN, err = 'no ScreenGui' } end

local out = { tok = TOKEN, players = #P:GetPlayers() }
local texts = {}
for _, d in ipairs(sg:GetDescendants()) do
  if d:IsA('TextLabel') and d.Text ~= '' and d.Visible then
    texts[#texts+1] = d:GetFullName():gsub('^Players%.[%d]+%.PlayerGui%.ScreenGui%.', '') .. ' = [' .. d.Text .. ']'
  end
end
table.sort(texts)
if #texts > 60 then
  out.n = #texts
  out.texts = {}
  for i = 1, 60 do out.texts[i] = texts[i] end
  out.truncated = true
else
  out.n = #texts
  out.texts = texts
end

-- anything that looks like a countdown, anywhere in the world or the gui
local nums = {}
for _, d in ipairs(game:GetDescendants()) do
  if d:IsA('TextLabel') and d.Text:match('^%[?%d+%]?$') and d.Visible and d.Text ~= '' then
    nums[#nums+1] = d:GetFullName() .. ' = [' .. d.Text .. ']'
    if #nums > 20 then break end
  end
end
out.bareNumbers = nums

return out
