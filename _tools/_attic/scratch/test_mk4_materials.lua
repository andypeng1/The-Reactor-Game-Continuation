-- test_mk4_materials.lua -- run _tools/apply_cbl_laser_mk4_materials.luau under
-- Lua 5.1 with stubbed Roblox types, and check the parts it would paint.
--
-- WHY: the script ships to Studio, and Studio is not connected in this session
-- (list_roblox_studios returned nothing), so the one thing that CAN be tested
-- here is the matching logic itself: does every design row find its own part,
-- does an import-scale slip still match but get flagged, is a duplicated shell
-- reported, is an absent piece reported. It cannot test what Roblox's importer
-- names or splits things into -- that needs the real import.
--
-- The stub is deliberately dumb: no Instance tree, just the four calls the
-- script makes (GetDescendants, GetChildren, IsA, Size/Name). Vector3 has .X/.Y/.Z
-- because the script reads the axes one at a time.
--
-- RUN
--   D:\Lua\5.1\lua.exe _tools\_attic\scratch\test_mk4_materials.lua
local SCRIPT = "D:/rblxTRGproject/_tools/apply_cbl_laser_mk4_materials.luau"

local fails, checks = 0, 0
local function check(ok, label, detail)
  checks = checks + 1
  if not ok then fails = fails + 1 end
  print(string.format("  %-52s %s%s", label, ok and "OK" or "*** FAIL ***",
                      detail and ("  " .. detail) or ""))
end

local function V(x, y, z)
  return { X = x, Y = y, Z = z }
end

local function set(list)
  local t = {}
  for _, v in ipairs(list) do t[v] = true end
  return t
end

-- Roblox stubs -----------------------------------------------------------------
local function makeEnv(children)
  local env = {}
  env.Enum = { Material = { Metal = { Name = "Metal" },
                            SmoothPlastic = { Name = "SmoothPlastic" },
                            Neon = { Name = "Neon" } } }
  env.Color3 = { fromRGB = function(r, g, b) return { R = r, G = g, B = b } end }
  local ws = {}
  ws.GetDescendants = function() return children end
  ws.GetChildren = function() return children end
  env.workspace = ws
  env.table = { find = function(t, v)
    for i, x in ipairs(t) do
      if x == v then return i end
    end
    return nil
  end, insert = table.insert, concat = table.concat }
  env.string = string
  env.math = math
  env.ipairs = ipairs
  env.print = function() end   -- the chunk prints its report; the test reads the return
  setmetatable(env, { __index = _G })
  return env
end

-- One fake MeshPart per (part, mat) row, with an optional size multiplier.
local DESIGN = {
  { "Mount", "Hull", { 21.6000, 18.7200, 23.0400 } },
  { "Mount", "Dark", { 15.0962, 15.5756, 19.6800 } },
  { "Mount", "Brass", { 5.2800, 5.2800, 19.2640 } },
  { "Mount", "Hazard", { 15.0962, 0.9280, 15.0962 } },
  { "Body", "Hull", { 52.6400, 16.8000, 16.8000 } },
  { "Body", "Dark", { 56.8320, 16.4850, 15.8400 } },
  { "Body", "Brass", { 44.8000, 20.3840, 16.8960 } },
  { "Body", "Hazard", { 1.2800, 14.0012, 14.1343 } },
  { "Body", "Cyan", { 36.2160, 13.8171, 15.0018 } },
  { "Body", "Amber", { 0.6720, 0.3200, 3.5520 } },
  { "Prongs", "Brass", { 8.4800, 11.7882, 13.5996 } },
  { "Core", "Cyan", { 42.8074, 12.1600, 12.6781 } },
  { "Core", "White", { 41.2837, 11.8877, 11.8900 } },
}

local function meshPart(name, size)
  return { Name = name, Size = size, IsA = function(_, c) return c == "MeshPart" end,
           Material = "unset", Color = "unset" }
end

-- Build a flat list of parts; `skip` drops a row, `extra` appends parts,
-- `mul` scales every size, `rename` maps index -> name override.
local function build(opts)
  local parts = {}
  for i, row in ipairs(DESIGN) do
    if i ~= (opts.skip or -1) then
      local s = row[3]
      local m = opts.mul or 1
      local name = (opts.rename and opts.rename[i]) or ("CblLaserMk4" .. row[1] .. "_" .. row[2])
      parts[#parts + 1] = meshPart(name, V(s[1] * m, s[2] * m, s[3] * m))
    end
  end
  for _, e in ipairs(opts.extra or {}) do
    parts[#parts + 1] = meshPart(e[1], V(e[2][1], e[2][2], e[2][3]))
  end
  return parts
end

local function run(parts, rootName)
  local chunk = assert(loadfile(SCRIPT))
  local env = makeEnv(parts)
  setfenv(chunk, env)
  -- The script finds the assembly by name. Every fake part is named
  -- CblLaserMk4*, so the fallback branch (loose MeshParts under Workspace) is
  -- the one under test here; the Model branch needs a real Instance tree.
  local report = chunk()
  return report, parts
end

local function painted(parts)
  local n = 0
  for _, p in ipairs(parts) do
    if p.Color ~= "unset" then n = n + 1 end
  end
  return n
end

print("== A. exact sizes: every row matches its own part, nothing skipped")
local rep, parts = run(build({}))
check(painted(parts) == #DESIGN, "all rows painted", painted(parts) .. "/" .. #DESIGN)
check(not rep:find("MISSING"), "no MISSING row")
check(not rep:find("AMBIGUOUS"), "no AMBIGUOUS row")
check(not rep:find("matched 2 parts"), "no duplicated shell")
check(not rep:find("import scale"), "no scale warning")
check(rep:find("painted 13 part%(s%), 0 skipped, 0 name/shape disagreement"), "tally line",
      (rep:match("painted %d+ part%(s%), %d+ skipped, %d+ name/shape") or "not found"))
-- Spot-check one colour and one material: the emissive parts must be Neon and
-- the hull must be the sRGB value, not the linear one.
local function rgbOf(p)
  if type(p.Color) ~= "table" then return "unset" end
  return string.format("%d,%d,%d", p.Color.R, p.Color.G, p.Color.B)
end
local core = parts[12]
check(core.Material.Name == "Neon", "Core/Cyan is Neon", core.Material.Name)
check(core.Color.R == 66 and core.Color.G == 229 and core.Color.B == 255,
      "Core/Cyan is sRGB 66,229,255", rgbOf(core))
local hull = parts[1]
check(hull.Material.Name == "Metal", "Mount/Hull is Metal", hull.Material.Name)
local hazard = parts[4]
check(hazard.Material.Name == "SmoothPlastic", "Mount/Hazard is SmoothPlastic", hazard.Material.Name)

print("== B. imported at 1.6943x (the .glb route): nothing painted, each line diagnoses it")
local rep2, parts2 = run(build({ mul = 1.69432 }))
check(painted(parts2) == 0, "nothing painted", painted(parts2) .. "/" .. #DESIGN)
check(rep2:find("NO MATCH"), "every part reported NO MATCH")
check(rep2:find("implies import scale 1%.694"), "the implied scale is named",
      (rep2:match("implies import scale [%d%.]+") or "not found"))

print("== B2. a 0.05% size wobble still matches everything")
local rep2b, parts2b = run(build({ mul = 1.0005 }))
check(painted(parts2b) == #DESIGN, "all rows painted", painted(parts2b) .. "/" .. #DESIGN)
check(not rep2b:find("NO MATCH"), "no NO MATCH row")

print("== C. one material arriving as two shells (the bevel defect)")
local rep3, parts3 = run(build({ extra = { { "CblLaserMk4Body_Hull", { 52.6400, 16.8000, 16.8000 } } } }))
check(rep3:find("Body/Hull matched 2 parts"), "duplicate reported",
      (rep3:match("%*%*%* Body/Hull matched %d parts") or "not found"))

print("== D. a piece missing from the import")
local rep4 = run(build({ skip = 11 }))
check(rep4:find("MISSING  Prongs/Brass"), "missing row reported",
      (rep4:match("MISSING  [^\n]+") or "not found"))

print("== E. name and shape disagree")
local rep5 = run(build({ rename = { [5] = "CblLaserMk4Mount_Something" } }))
check(rep5:find("name says Mount, shape says Body"), "disagreement reported",
      (rep5:match("%*%*%* name says %a+, shape says %a+") or "not found"))

print(string.format("CHECK %d ok, %d failed", checks - fails, fails))
os.exit(fails == 0 and 0 or 1)
