-- Run in Studio via execute_luau (Server datamodel), then paste the output
-- lines (the "KIND<TAB>id<TAB>count" ones) into _tools/scene_assets.tsv.
local function idOf(s)
  if type(s) ~= "string" or s == "" then return nil end
  return string.match(s, "rbxassetid://(%d+)") or string.match(s, "[?&]id=(%d+)")
end
local T = {}
local function add(kind, s)
  local id = idOf(s)
  if not id then return end
  T[id] = T[id] or { n = 0, kinds = {} }
  T[id].n = T[id].n + 1
  T[id].kinds[kind] = (T[id].kinds[kind] or 0) + 1
end
for _, d in ipairs(game.Workspace:GetDescendants()) do
  if d:IsA("ParticleEmitter") then add("PTEX", d.Texture)
  elseif d:IsA("Decal") or d:IsA("Texture") then add("DECAL", d.Texture)
  elseif d:IsA("Sound") then add("SND", d.SoundId)
  elseif d:IsA("MeshPart") then add("MESH", d.MeshId) end
end
local rows = {}
for id, t in pairs(T) do
  local ks = {}
  for k in pairs(t.kinds) do ks[#ks + 1] = k end
  table.sort(ks)
  rows[#rows + 1] = { id = id, n = t.n, k = table.concat(ks, "+") }
end
table.sort(rows, function(a, b)
  if a.n ~= b.n then return a.n > b.n end
  return a.id < b.id
end)
for i = 1, #rows do
  print(rows[i].k .. "\t" .. rows[i].id .. "\t" .. rows[i].n)
end
