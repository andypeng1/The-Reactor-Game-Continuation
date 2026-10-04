-- cw24_diag.luau -- why do the raycasts disagree with the design?
--
-- The build reported the 24-gon wall dead on (apothem 67.9980, circum 68.5873,
-- corner at 60 deg -- all exactly right) while the 18-gon collar came out
-- inflated by ~0.6 studs. One surface of the same mesh cannot be right and the
-- other wrong, so the measurement is what is suspect.
--
-- A raycast against a MeshPart queries its COLLISION geometry, and a MeshPart's
-- default CollisionFidelity is a convex hull. The hull of an annulus is a solid
-- disk: it has no inner surface at all, and its lateral surface is the fan from
-- the 18-gon's corners at y 0..1.2 out to the 24-gon's corners at y 4.2. That is
-- exactly the shape that would read ~0.6 studs proud at the collar's height while
-- reading correctly up the straight 24-gon. So: read the RENDER mesh directly.
local AssetService = game:GetService("AssetService")
local NAME = "ChamberWall24"
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

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
say("part %s", mp:GetFullName())
say("CollisionFidelity %s", tostring(mp.CollisionFidelity))
say("MeshSize %s", tostring(mp.MeshSize))
say("Size     %s", tostring(mp.Size))
say("Position %s", tostring(mp.Position))
say("CenterOfMass (local) %s", tostring(mp.CenterOfMass))

-- ============================================================ API probe

local function probe(label, fn)
	local ok, v = pcall(fn)
	say("api %-28s %s", label, ok and ("ok " .. tostring(v)) or ("ERR " .. tostring(v)))
	return ok, v
end
probe("MeshContent", function()
	return tostring(mp.MeshContent)
end)
probe("MeshId", function()
	return "'" .. tostring(mp.MeshId) .. "' (len " .. #tostring(mp.MeshId) .. ")"
end)
probe("CreateEditableMeshAsync", function()
	return tostring(AssetService.CreateEditableMeshAsync)
end)

-- ============================================================ read the mesh back

-- Ground truth for the RENDER mesh: pull it back into an EditableMesh and read
-- every vertex. This is the same instrument the build used to place the vertices,
-- so the comparison is like-for-like -- and unlike a raycast it cannot be
-- answered by a collision proxy.
local content
local okC = pcall(function()
	content = mp.MeshContent
end)
if not okC or content == nil then
	say("cannot read MeshContent; falling back to raycast-only evidence")
	return table.concat(out, string.char(10))
end

local okM, meshOrErr = pcall(function()
	return AssetService:CreateEditableMeshAsync(content)
end)
if not okM then
	say("CreateEditableMeshAsync failed: %s", tostring(meshOrErr))
	say("(the texture/geometry wrap is one-way in this Studio build -- recorded as a limit, not worked around)")
	return table.concat(out, string.char(10))
end
local m2 = meshOrErr

local okV, vidsOrErr = pcall(function()
	return m2:GetVertices()
end)
if not okV then
	say("GetVertices failed: %s", tostring(vidsOrErr))
	return table.concat(out, string.char(10))
end
local ids = vidsOrErr
say("read back %d vertices", #ids)

local okF, fidsOrErr = pcall(function()
	return m2:GetFaces()
end)
local faceCount = okF and #fidsOrErr or -1
say("read back %d faces", faceCount)

local V = {}
for i, id in ipairs(ids) do
	V[i] = m2:GetPosition(id)
end

local lo = Vector3.new(math.huge, math.huge, math.huge)
local hi = Vector3.new(-math.huge, -math.huge, -math.huge)
for _, v in ipairs(V) do
	lo = Vector3.new(math.min(lo.X, v.X), math.min(lo.Y, v.Y), math.min(lo.Z, v.Z))
	hi = Vector3.new(math.max(hi.X, v.X), math.max(hi.Y, v.Y), math.max(hi.Z, v.Z))
end
say("read-back bbox  X %.4f..%.4f  Y %.4f..%.4f  Z %.4f..%.4f", lo.X, hi.X, lo.Y, hi.Y, lo.Z, hi.Z)
say("read-back size  %.4f x %.4f x %.4f", hi.X - lo.X, hi.Y - lo.Y, hi.Z - lo.Z)

-- Vertices on the collar's OUTER rim: local y exactly Z_COLLAR and radius near
-- R_OUT18. The apothem is then the closest approach of a chord between adjacent
-- rim vertices to the axis -- the same rule the place itself was measured with.
local function rim(group, y, rmin, rmax)
	local pts = {}
	for _, v in ipairs(V) do
		if math.abs(v.Y - y) < 1e-3 then
			local r = math.sqrt(v.X * v.X + v.Z * v.Z)
			if r >= rmin and r <= rmax then
				pts[#pts + 1] = v
			end
		end
	end
	table.sort(pts, function(a, b)
		return math.atan2(a.Z, a.X) < math.atan2(b.Z, b.X)
	end)
	local apothem = math.huge
	local radMin, radMax = math.huge, -math.huge
	for i, p in ipairs(pts) do
		local q = pts[i % #pts + 1]
		local r = math.sqrt(p.X * p.X + p.Z * p.Z)
		radMin = math.min(radMin, r)
		radMax = math.max(radMax, r)
		local d = q - p
		local t = -(p.X * d.X + p.Z * d.Z) / (d.X * d.X + d.Z * d.Z)
		t = math.clamp(t, 0, 1)
		local c = Vector3.new(p.X + d.X * t, 0, p.Z + d.Z * t)
		apothem = math.min(apothem, c.Magnitude)
	end
	say("%-14s %d verts  circum %.4f..%.4f  apothem %.4f", group, #pts, radMin, radMax, apothem)
	return #pts, apothem
end

local nCollar, apCollar = rim("collar outer", 1.20, 60, 70)
local nWall, apWall = rim("wall outer", 4.20, 65, 72)
local nLid, apLid = rim("wall top", 13.20, 60, 72)
local nBase, apBase = rim("collar base", 0.00, 60, 70)

-- ============================================================ RETRACTION

-- The four numbers printed above are NOT the four rims they are labelled as, and
-- the verdict this file used to print from them was wrong.
--
-- rim() here bands by HEIGHT ONLY. At y = 1.20 the collar has TWO rings -- outer
-- 63.712..64.695 and inner 59.712..60.633 -- and both land in the one bucket, in
-- azimuthal order, so the chord-to-axis minimum runs across the 59.712 set too.
-- That is where the old "collar apothem 59.7120" and "36 verts, not 18" came
-- from: a real apothem, of a ring nobody asked about (CLAUDE.md 0.18, third
-- face). Nothing about the mesh was wrong.
--
-- The question this file was written to answer has been answered, so it is not
-- repaired here -- it is retired. The corrected verifier bands by RADIUS as well
-- as height and asserts the vertex count, which is what makes mixing two rings
-- impossible rather than merely unlikely. Run that one.
say("")
say("RETIRED: the rims above are mis-bucketed (height only, two rings per bucket).")
say("Use cw24_verify.luau -- it bands by radius too and counts the vertices.")

return table.concat(out, string.char(10))
