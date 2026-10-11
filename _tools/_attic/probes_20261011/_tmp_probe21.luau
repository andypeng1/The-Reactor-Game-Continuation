local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- The game's controller is a server Script in Workspace, so its Source is
-- normally not sent to the client at all.  Rather than assume, ask -- and ask
-- about the executor's own dump helpers too, since those read the script cache
-- by a different route than the property does.
local out = { tok = TOKEN }

out.fns = {}
for _, n in ipairs({ 'getscriptbytecode', 'getscripthash', 'getscriptclosure',
                     'getcustomasset', 'decompile', 'dumpstring' }) do
  out.fns[n] = type(_G[n])
end

local ctrl = workspace:FindFirstChild('MainGameControllerScript')
out.found = ctrl ~= nil
if ctrl then
  local ok, src = pcall(function() return ctrl.Source end)
  out.sourceOk = ok
  if ok and type(src) == 'string' then
    out.sourceLen = #src
    out.sourceHead = src:sub(1, 600)
  else
    out.sourceErr = tostring(src)
  end
  local ok2, bc = pcall(function() return getscriptbytecode(ctrl) end)
  if ok2 and type(bc) == 'string' then
    out.bytecodeLen = #bc
    out.bytecodeTail = bc:sub(-200)
  else
    out.bytecodeErr = ok2 and tostring(bc) or 'call failed'
  end
end

return out
