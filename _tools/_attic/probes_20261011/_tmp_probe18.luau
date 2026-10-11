local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Every clock-shaped label in the whole game, not just the first: the first match
-- was the intermission's static "shift starts at 12:00AM" and stopping there
-- would have called it the clock.  Round 1's live clock was aliased q.timeText
-- and read "11:59 PM" -- space before the meridiem -- so the pattern allows both.
local out = { tok = TOKEN }
local hits = {}
for _, d in ipairs(game:GetDescendants()) do
  if d:IsA('TextLabel') and d.Text ~= '' and d.Text:match('%d+:%d+%s*[AP]M') then
    hits[#hits+1] = d:GetFullName():gsub('^Players%.[%d]+%.PlayerGui%.', 'PG.') .. ' = [' .. d.Text .. ']'
    if #hits > 40 then hits[#hits+1] = '...more' break end
  end
end
out.clocks = hits

-- the quota panel by name, since round 1 called it q.panel and it carried the clock
local q = {}
for _, d in ipairs(game:GetDescendants()) do
  if d:IsA('TextLabel') and d.Parent and d.Parent.Name:match('Quota') then
    q[#q+1] = d:GetFullName() .. ' = [' .. d.Text .. ']'
  end
end
out.quota = #q > 0 and q or 'no Quota-named parents'

return out
