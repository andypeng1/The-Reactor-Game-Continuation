local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Read the intermission's own subtree, not the whole GUI: the previous dump was
-- alphabetically truncated at the E's and filled with the end-game report, which
-- is always present in the tree and always invisible.  Reading the frame by path
-- cannot be flooded by unrelated siblings.
local P = game:GetService('Players')
local pg = P.LocalPlayer:FindFirstChild('PlayerGui')
local sg = pg and pg:FindFirstChild('ScreenGui')
if sg == nil then return { tok = TOKEN, err = 'no ScreenGui' } end

local out = { tok = TOKEN, players = #P:GetPlayers() }
out.jobId = game.JobId
out.privateServerId = game.PrivateServerId
out.privateServerOwner = tostring(game.PrivateServerOwnerId)
out.placeId = game.PlaceId
out.maxPlayers = P.MaxPlayers
out.playerNames = {}
for _, pl in ipairs(P:GetPlayers()) do out.playerNames[#out.playerNames+1] = pl.Name end

for _, frameName in ipairs({ 'IntermissionFrame', 'WaitFrame', 'AdditionFrame' }) do
  local f = sg:FindFirstChild(frameName, true)
  if f then
    local t = {}
    t[#t+1] = '[' .. f.Name .. '] vis=' .. tostring(f.Visible)
    for _, d in ipairs(f:GetDescendants()) do
      if d:IsA('TextLabel') and d.Text ~= '' then
        t[#t+1] = '  ' .. d.Name .. ' = [' .. d.Text .. ']'
      end
    end
    out[frameName] = t
  else
    out[frameName] = 'not found'
  end
end

return out
