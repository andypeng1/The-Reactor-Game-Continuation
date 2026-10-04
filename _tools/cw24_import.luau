-- cw24_import.luau -- the imported Wall24 next to the built one, and why
-- CollisionFidelity refused to be written.
--
-- The hypothesis to test: CollisionFidelity was settable on neither Default nor
-- Hull nor PreciseConvexDecomposition nor Box on the built MeshPart (all four read
-- back Default), while re-parenting did not help either. If the SAME property IS
-- writable on a MeshPart whose MeshContent is a Uri -- the imported ones -- then
-- the cause is the runtime Content-from-Object route, not Studio, and that is a
-- limit worth writing down instead of working around.
--
-- Also: the imported Wall24 is 1.0769x the built one and 0.873 off centre, so it
-- does not meet the 18-gon ring. Whether it is load-bearing (CanCollide) decides
-- whether removing it is a cosmetic cleanup or a physics change.
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

local built, imported = nil, {}
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("MeshPart") and string.find(d.Name, "ChamberWall") then
		local isUri = false
		pcall(function()
			isUri = d.MeshContent.SourceType == Enum.ContentSourceType.Uri
		end)
		if isUri then
			imported[#imported + 1] = d
		else
			built = d
		end
	end
end
if not built then
	return "no built ChamberWall found"
end

local function describe(label, p)
	say("%s", label)
	say("  %s", p:GetFullName())
	say("  CanCollide %s  CanQuery %s  CanTouch %s  Anchored %s  Massless %s",
		tostring(p.CanCollide), tostring(p.CanQuery), tostring(p.CanTouch),
		tostring(p.Anchored), tostring(p.Massless))
	say("  Material %s  Color %.3f %.3f %.3f  Transparency %.3f  Reflectance %.3f",
		tostring(p.Material), p.Color.R, p.Color.G, p.Color.B, p.Transparency, p.Reflectance)
	local was = p.CollisionFidelity
	say("  CollisionFidelity (as found) %s", tostring(was))
	-- Can this one be written? Try Precise and read straight back.
	local ok = pcall(function()
		p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
	end)
	say("  set Precise -> ok=%s  reads back %s", tostring(ok), tostring(p.CollisionFidelity))
	-- A probe that writes must put it back to what it found, not to what the probe
	-- wanted. Restoring to a fixed value would silently edit a part nobody asked
	-- about (CLAUDE.md 0.13: the failure that looks like nothing happening).
	pcall(function()
		p.CollisionFidelity = was
	end)
	say("  restored  -> %s", tostring(p.CollisionFidelity))
end

say("==== built (MeshContent = Object) ====")
describe("built", built)

say("")
say("==== imported (MeshContent = Uri) ====")
table.sort(imported, function(a, b)
	return a.Position.Y < b.Position.Y
end)
for i, p in ipairs(imported) do
	describe(string.format("imported #%d", i), p)
end

-- ============================================================ do they overlap

-- The built wall occupies an annulus about CENTRE; the import is an annulus about
-- its own centre. Measure the import's own axis by firing at it alone.
say("")
say("==== the import's own axis ====")
local okAll = true
for _, p in ipairs(imported) do
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { p }
	params.IgnoreWater = true
	local y = p.Position.Y
	local lo, hi = math.huge, -math.huge
	for k = 0, 359 do
		local th = math.rad(k)
		local dir = Vector3.new(math.cos(th), 0, math.sin(th))
		local o = Vector3.new(CENTRE.X + dir.X * 120, y, CENTRE.Z + dir.Z * 120)
		local h = workspace:Raycast(o, -dir * 240, params)
		if h then
			local r = 120 - h.Distance
			lo = math.min(lo, r)
			hi = math.max(hi, r)
		else
			okAll = false
		end
	end
	say("  %-34s y %8.4f   rho %.4f .. %.4f   (own Size.X/2 = %.4f)",
		p.Name, y, lo, hi, p.Size.X * 0.5)
end
say("  all rays hit: %s", tostring(okAll))

-- ============================================================ the built wall, one more time

say("")
say("==== built wall, geometry that will not be re-derived from Size ====")
local mp = built
say("  Position %s", tostring(mp.Position))
say("  Size   %s", tostring(mp.Size))
say("  MeshSize %s", tostring(mp.MeshSize))

return table.concat(out, string.char(10))
