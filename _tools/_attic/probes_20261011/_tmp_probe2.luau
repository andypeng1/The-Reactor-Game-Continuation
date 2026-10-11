local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- The last probe returned 'Consoles?' for a path that was never built, and that
-- string cannot tell "Workspace.Consoles is missing" from "MainReactorConsole is
-- missing" -- two different problems with two different fixes.  A sentinel that
-- survives the failure it is supposed to describe is not a measurement.  So this
-- walk reports the deepest node it actually reached, by name.
local stops = {}
local node = workspace
local missingAt = 'n/a'
for _, seg in ipairs({ 'Consoles', 'MainReactorConsole', 'StartUpBigLever', 'StartClickPart' }) do
  local nxt = node and node:FindFirstChild(seg)
  if nxt == nil then
    missingAt = seg .. ' under ' .. tostring(node and node:GetFullName())
    node = nil
    break
  end
  node = nxt
end

local cd = node and node:FindFirstChildOfClass('ClickDetector')

-- Enumerate what IS under Consoles, so "not found" becomes "these are the names".
local kids = {}
local cons = workspace:FindFirstChild('Consoles')
if cons then
  for _, c in ipairs(cons:GetChildren()) do
    kids[#kids+1] = c.Name .. '(' .. c.ClassName .. ')'
  end
  table.sort(kids)
end

return {
  tok = TOKEN,
  missingAt = missingAt,
  reached = node and node:GetFullName() or 'nil',
  hasCD = cd ~= nil,
  maxDist = cd and cd.MaxDistance or 'no-cd',
  consoleKids = kids,
  nconsoleKids = #kids,
}
