local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- LocalScripts anywhere, not just PlayerScripts.  A LocalScript under StarterGui
-- is cloned into PlayerGui at runtime and would not have shown up in the earlier
-- scan, and its existence changes the answer completely: a client-side handler
-- CAN be reached by firing the GUI signal, while a server-side one cannot.
local out = { tok = TOKEN }
local ls = {}
for _, d in ipairs(game:GetDescendants()) do
  if d:IsA('LocalScript') or d:IsA('BaseScript') and d.ClassName ~= 'Script' and d.ClassName ~= 'ModuleScript' then
    ls[#ls+1] = d:GetFullName() .. ' [' .. d.ClassName .. ']'
  elseif d:IsA('Script') then
    ls[#ls+1] = d:GetFullName() .. ' [Script]'
  end
  if #ls > 80 then ls[#ls+1] = '...more' break end
end
out.scripts = ls

-- the MouseFrame the recorder named, and whatever it is parented to
local mf = nil
for _, d in ipairs(game:GetDescendants()) do
  if d.Name == 'MouseFrame' then mf = d break end
end
if mf then
  out.mouseFrame = mf:GetFullName()
  local kids = {}
  for _, c in ipairs(mf:GetDescendants()) do
    kids[#kids+1] = c.ClassName .. ' ' .. c.Name
  end
  out.mouseFrameKids = kids
else
  out.mouseFrame = 'none'
end

return out
