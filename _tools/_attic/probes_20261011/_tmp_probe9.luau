local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Both synthetic-input routes came back empty -- and "empty" has two readings I
-- must not blend: the game may not listen to virtual input at all, or the game
-- may not route this lever through input in the first place.
--
-- So look at the wiring instead of at the input.  A ClickDetector handled on the
-- SERVER is reached by the engine's own remote and cannot be driven from here;
-- a HANDLER in a client LocalScript is reached by the signal fire that already
-- works.  Which one it is decides which of the two roads is even worth walking,
-- and the names on disk say which one it is without guessing.
local out = { tok = TOKEN }

local function names(root, kinds, cap)
  local t = {}
  for _, d in ipairs(root:GetDescendants()) do
    if kinds[d.ClassName] then
      t[#t+1] = d:GetFullName() .. ' [' .. d.ClassName .. ']'
      if #t >= cap then t[#t+1] = '...cap' break end
    end
  end
  return t
end

-- 1. the lever itself: everything that could carry a handler or a prompt
local big = workspace:FindFirstChild('Consoles')
  and workspace.Consoles:FindFirstChild('MainReactorConsole')
  and workspace.Consoles.MainReactorConsole:FindFirstChild('StartUpBigLever')
local leverParts = {}
if big then
  for _, d in ipairs(big:GetDescendants()) do
    leverParts[#leverParts+1] = d.ClassName .. ' ' .. d.Name
  end
end
out.leverTree = leverParts

-- 2. prompts in the whole console block -- a hold-to-interact lever would live
--    here and would explain why a plain click does nothing
out.prompts = names(workspace:FindFirstChild('Consoles') or workspace,
  { ProximityPrompt = true }, 40)

-- 3. the client-side code: StarterPlayerScripts is reparented into PlayerScripts
--    at runtime, so that is where the live copy is
local P = game:GetService('Players')
local ps = P.LocalPlayer and P.LocalPlayer:FindFirstChild('PlayerScripts')
out.playerScripts = ps and names(ps, { LocalScript = true, Script = true, ModuleScript = true }, 60) or 'no PlayerScripts'

-- 4. remotes the client can see -- a start button forwarded to the server needs
--    one of these
local RS = game:GetService('ReplicatedStorage')
out.remotes = {}
for _, d in ipairs(RS:GetDescendants()) do
  if d:IsA('RemoteEvent') or d:IsA('RemoteFunction') then
    out.remotes[#out.remotes+1] = d:GetFullName() .. ' [' .. d.ClassName .. ']'
  end
end
if #out.remotes > 60 then out.remotes = { '...too many: ' .. #out.remotes } end

-- 5. any BindableEvent / script living directly under the lever
out.underLever = big and names(big, { Script = true, LocalScript = true, ModuleScript = true,
  RemoteEvent = true, BindableEvent = true }, 20) or 'no lever'

return out
