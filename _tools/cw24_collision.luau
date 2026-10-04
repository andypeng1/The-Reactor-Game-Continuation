-- cw24_collision.luau -- settle the collision body, and check the wall for
-- intersections with what is already in the chamber.
--
-- Two questions the build could not answer on its own:
--
--   Q1  CollisionFidelity was set to PreciseConvexDecomposition and every probe
--       came back byte-identical, which is the signature of a write that did not
--       take. If it cannot be changed, a MeshPart's collision here is a CONVEX
--       HULL -- and the hull of an annulus is a solid disk 137 studs across, so
--       "it did not take" is not a cosmetic detail.
--
--   Q2  This wall was designed to apothem 68.000 / circumradius 68.587, and the
--       chamber's own inner tube was measured in Phase 77 at D135.6, i.e. radius
--       67.8. If that tube is still there, the wall's corners stand 0.8 studs
--       proud of it. Nobody has checked, and "it looked fine in the numbers" is
--       exactly the failure CLAUDE.md 0.18 is about.
local NAME = "ChamberWall24"
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)
local A18, A24 = 63.712, 68.000

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

local mp
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == NAME and d:IsA("MeshPart") then
		mp = d
		break
	end
end
if not mp then
	return "no " .. NAME .. " found"
end

local function params(inst)
	local p = RaycastParams.new()
	p.FilterType = Enum.RaycastFilterType.Include
	p.FilterDescendantsInstances = { inst }
	p.IgnoreWater = true
	return p
end

local function faceAt(inst, y, rho)
	local p = params(inst)
	local o = Vector3.new(CENTRE.X + rho, y, CENTRE.Z)
	local h = workspace:Raycast(o, Vector3.new(-rho * 2, 0, 0), p)
	return h and (rho - h.Distance) or nil
end

local function holeAt(inst, rho, y0)
	local p = params(inst)
	local o = Vector3.new(CENTRE.X + rho, CENTRE.Y + y0, CENTRE.Z)
	local h = workspace:Raycast(o, Vector3.new(0, -200, 0), p)
	return h and h.Position.Y or nil
end

-- ============================================================ Q1

say("==== CollisionFidelity ====")
local order = {
	"Default",
	"Hull",
	"PreciseConvexDecomposition",
	"Box",
}
for _, name in ipairs(order) do
	local ok = pcall(function()
		mp.CollisionFidelity = Enum.CollisionFidelity[name]
	end)
	local readback = tostring(mp.CollisionFidelity)
	local face = faceAt(mp, CENTRE.Y + 0.6, 90)
	local hole = holeAt(mp, A18 - 1.5, 60)
	local wall = faceAt(mp, CENTRE.Y + 8.0, 90)
	say("%-26s set=%s  read=%-40s collar=%s hole=%s wall=%s", name, tostring(ok),
		readback,
		face and string.format("%.4f", face) or "MISS",
		hole and string.format("HIT y=%.3f", hole) or "MISS",
		wall and string.format("%.4f", wall) or "MISS")
end
-- Truth for the collar's outer face is 64.6949 (its corner radius), the wall's is
-- 68.5868, and a hollow ring must MISS going down through its own hole.
say("truth: collar 64.6949, wall 68.5868, hole MISS")

-- A written property and a rebuilt physics body are two different events. Force
-- the second: re-parenting makes the engine re-derive collision from the mesh.
say("")
say("-- after re-parenting, with Precise in place --")
mp.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
local parent = mp.Parent
mp.Parent = nil
mp.Parent = parent
task.wait()
say("read back %s", tostring(mp.CollisionFidelity))
say("collar face %s   hole %s   wall face %s",
	tostring(faceAt(mp, CENTRE.Y + 0.6, 90)),
	tostring(holeAt(mp, A18 - 1.5, 60)),
	tostring(faceAt(mp, CENTRE.Y + 8.0, 90)))
say("Massless %s  RootPart-ish  AssemblyMass %.4f", tostring(mp.Massless), mp.AssemblyMass)

-- ============================================================ Q2

say("")
say("==== does the wall intersect anything already here ====")
-- Unfiltered rays, so this reports the WORLD, not the part under test. Coming in
-- from rho=200 along +X at several heights and printing the first few surfaces.
local heights = { 47.4, 48.6, 51.6, 55.0, 60.6 }
for _, y in ipairs(heights) do
	local o = Vector3.new(CENTRE.X + 200, y, CENTRE.Z)
	local h = workspace:Raycast(o, Vector3.new(-400, 0, 0))
	local line = {}
	local guard = 0
	while h and guard < 12 do
		guard += 1
		local r = 200 - h.Distance
		line[#line + 1] = string.format("r=%.3f %s(%s)", r, h.Instance.Name, h.Instance.ClassName)
		o = o + Vector3.new(-(h.Distance + 0.05), 0, 0)
		h = workspace:Raycast(o, Vector3.new(-400, 0, 0))
		if o.X < CENTRE.X - 200 then
			break
		end
	end
	say("y=%6.2f  %s", y, table.concat(line, "  |  "))
end

return table.concat(out, string.char(10))
