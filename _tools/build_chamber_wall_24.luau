-- build_chamber_wall_24.luau -- build the 18->24 chamber wall INSIDE Studio.
--
-- Why this exists instead of an .fbx drag-in: the user's words were
--   "你自己在studio里面做，我这里人工调整肯定不准确"
-- -- a human dragging an asset cannot hit a sub-stud target, and the target here
-- is exact: the collar's outer face must be coplanar with the existing ring's
-- outer face (same apothem 63.712, same corner phase) and its bottom plane must
-- be the ring's top plane (y 47.400). So the geometry is built from the same
-- constants as _tools/blender/chamber_wall_24.py and handed straight to
-- AssetService:CreateEditableMesh() + CreateMeshPartAsync(). Content.fromObject
-- stores the mesh as an object WITHIN THE PLACE, so no upload credential is
-- needed -- which matters, because ROBLOX_OPEN_CLOUD_API_KEY is not set here.
--
-- Same design table as the Blender script. If one moves, the other must move.
local N18, N24 = 18, 24
local A18, A24 = 63.712, 68.000
local WALL = 4.00
local Z_COLLAR, Z_BAND, Z_TOP = 1.20, 4.20, 13.20

-- radii are always derived from the apothem: r = apothem / cos(pi/n)
local R_OUT18 = A18 / math.cos(math.pi / N18)
local R_IN18 = (A18 - WALL) / math.cos(math.pi / N18)
local R_OUT24 = A24 / math.cos(math.pi / N24)
local R_IN24 = (A24 - WALL) / math.cos(math.pi / N24)

-- Where the collar's BASE centre goes. y is the platform top plane (47.400), NOT
-- the mean of the ring's part positions (47.075) -- the parts are 0.650 tall, so
-- their centres sit half a thickness below the surface they present.
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)
local HINT = Vector3.new(-12.200, 47.400, -85.362)
local NEW_NAME = "ChamberWall24"

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

-- ============================================================ 1. locate the ring

local function findRing()
	local best = nil
	for _, d in ipairs(workspace:GetDescendants()) do
		if (d:IsA("Folder") or d:IsA("Model")) and d.Name == "18" then
			local parts = {}
			for _, c in ipairs(d:GetChildren()) do
				if c:IsA("BasePart") then
					parts[#parts + 1] = c
				end
			end
			if #parts >= 15 and #parts <= 25 then
				local p = Vector3.new(0, 0, 0)
				for _, q in ipairs(parts) do
					p = p + q.Position
				end
				p = p / #parts
				local dist = (Vector3.new(p.X, 0, p.Z) - Vector3.new(HINT.X, 0, HINT.Z)).Magnitude
				if not best or dist < best.dist then
					best = { inst = d, parts = parts, dist = dist }
				end
			end
		end
	end
	return best
end

local ring = findRing()
if not ring then
	return "ABORT: no 18-ring found"
end
say("ring %s (%d parts)", ring.inst:GetFullName(), #ring.parts)

-- Guard the build with a live reading, not a remembered number (CLAUDE.md 0.18).
-- 360 inward rays at the ring's own mid height; the deep answer is the apothem.
local function radialProbe(target, y, R)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { target }
	params.IgnoreWater = true
	local N = 720
	local lo, loAt, hi, hiAt, miss = math.huge, 0, -math.huge, 0, 0
	for k = 0, N - 1 do
		local th = 2 * math.pi * k / N
		local dir = Vector3.new(math.cos(th), 0, math.sin(th))
		local o = Vector3.new(CENTRE.X + R * dir.X, y, CENTRE.Z + R * dir.Z)
		local h = workspace:Raycast(o, -dir * (R * 2), params)
		if h then
			local r = R - h.Distance
			if r < lo then lo, loAt = r, k * 360 / N end
			if r > hi then hi, hiAt = r, k * 360 / N end
		else
			miss += 1
		end
	end
	return lo, loAt, hi, hiAt, miss
end

local ringLo, ringLoAt, ringHi, ringHiAt, ringMiss = radialProbe(ring.inst, 47.075, 90)
say("ring probe   apothem %.4f @%.2f deg   circum %.4f @%.2f deg   misses %d",
	ringLo, ringLoAt, ringHi, ringHiAt, ringMiss)

if ringMiss > 0 then
	return string.format("ABORT: %d/%d rays missed the ring -- it is not where the design thinks", ringMiss, 720)
end
if math.abs(ringLo - A18) > 0.02 then
	return string.format("ABORT: ring apothem is %.4f, design says %.4f", ringLo, A18)
end
if math.abs(ringHi / ringLo - 1 / math.cos(math.pi / N18)) > 1e-4 then
	return "ABORT: ring circum/apothem ratio is not 1/cos(10 deg) -- wrong corner count or phase"
end
say("ring matches the design: apothem %.4f (A18), corner phase confirmed", A18)

-- ============================================================ 2. the mesh, as data

-- Vertices and triangles are collected as PLAIN LUA TABLES first, so every
-- invariant below is checked before a single GPU resource exists. A wrong
-- winding or an open surface is then a refusal, not a wrong-looking wall.
local V, T = {}, {}

local function addRing(n, r, y)
	local base = #V
	for k = 0, n - 1 do
		local th = 2 * math.pi * k / n
		V[#V + 1] = Vector3.new(r * math.cos(th), y, r * math.sin(th))
	end
	return base
end

-- (a,b,c,d) in cyclic order; split as (a,b,c)+(a,c,d). Callers choose the cyclic
-- direction, which is what sets the normal: for a triangle (p,q,r) the rendered
-- front normal is (q-p)x(r-p), the right-hand rule.
local function quad(a, b, c, d)
	T[#T + 1] = { a, b, c }
	T[#T + 1] = { a, c, d }
end

-- ---- tube A: the 18-gon collar, y 0.00 -> 1.20. Top annulus DELETED (that rim
-- joins the band), so this piece is an open-ended tube.
local AO0 = addRing(N18, R_OUT18, 0.00)
local AI0 = addRing(N18, R_IN18, 0.00)
local AO1 = addRing(N18, R_OUT18, Z_COLLAR)
local AI1 = addRing(N18, R_IN18, Z_COLLAR)
for k = 0, N18 - 1 do
	local j = (k + 1) % N18
	quad(AO0 + k + 1, AO1 + k + 1, AO1 + j + 1, AO0 + j + 1) -- outer wall, faces out
	quad(AI0 + k + 1, AI0 + j + 1, AI1 + j + 1, AI1 + k + 1) -- inner wall, faces in
	quad(AO0 + k + 1, AO0 + j + 1, AI0 + j + 1, AI0 + k + 1) -- floor, faces down
end

-- ---- tube B: the 24-gon wall, y 4.20 -> 13.20. Bottom annulus DELETED.
local BO0 = addRing(N24, R_OUT24, Z_BAND)
local BI0 = addRing(N24, R_IN24, Z_BAND)
local BO1 = addRing(N24, R_OUT24, Z_TOP)
local BI1 = addRing(N24, R_IN24, Z_TOP)
for k = 0, N24 - 1 do
	local j = (k + 1) % N24
	quad(BO0 + k + 1, BO1 + k + 1, BO1 + j + 1, BO0 + j + 1)
	quad(BI0 + k + 1, BI0 + j + 1, BI1 + j + 1, BI1 + k + 1)
	quad(BO1 + k + 1, BI1 + k + 1, BI1 + j + 1, BO1 + j + 1) -- lid, faces up
end

-- ---- the band: 18 -> 24 cannot be bridged quad-to-quad (18 does not divide 24
-- into matching pairs), so each surface is 18 + 24 = 42 TRIANGLES.
--
-- Monotone merge: walk both rims in increasing azimuth and always advance the one
-- whose next corner comes first. Every step consumes exactly one rim edge, so
-- after 18 + 24 steps every edge of both rims has been used exactly once -- that
-- is what "no twist" means here, and it is asserted below, not assumed.
local function band(lo, nlo, hi, nhi, flip)
	local i, j, made = 0, 0, 0
	while i < nlo or j < nhi do
		local aNext = (i < nlo) and (360 / nlo) * (i + 1) or math.huge
		local bNext = (j < nhi) and (360 / nhi) * (j + 1) or math.huge
		local l = lo + (i % nlo) + 1
		local u = hi + (j % nhi) + 1
		if aNext <= bNext then
			local ln = lo + ((i + 1) % nlo) + 1
			T[#T + 1] = flip and { l, ln, u } or { l, u, ln }
			i += 1
		else
			local un = hi + ((j + 1) % nhi) + 1
			T[#T + 1] = flip and { l, un, u } or { l, u, un }
			j += 1
		end
		made += 1
	end
	return made
end

local outerMade = band(AO1, N18, BO0, N24, false)
local innerMade = band(AI1, N18, BI0, N24, true)
say("band triangles: outer %d + inner %d = %d", outerMade, innerMade, outerMade + innerMade)

-- ============================================================ 3. invariants

local problems = {}
local function require_(ok, msg)
	if not ok then
		problems[#problems + 1] = msg
	end
end

require_(#V == 168, string.format("vertex count %d, design says 168", #V))
require_(#T == 336, string.format("triangle count %d, design says 336", #T))
require_(outerMade == 42 and innerMade == 42, "band triangle counts are not 42 + 42")

-- degenerate triangles: a zero-area face is invisible but still "a face", which
-- is exactly how a bad bridge reports success (CLAUDE.md / DECISIONS 269).
local degenerate = 0
for i, t in ipairs(T) do
	local a, b, c = V[t[1]], V[t[2]], V[t[3]]
	local n = (b - a):Cross(c - a)
	if n.Magnitude < 1e-9 then
		degenerate += 1
		if degenerate <= 5 then
			say("  degenerate triangle #%d  %d %d %d", i, t[1], t[2], t[3])
		end
	end
end
require_(degenerate == 0, string.format("%d degenerate triangles", degenerate))

-- manifold + consistent orientation: every DIRECTED edge used exactly once (that
-- is orientation), every UNDIRECTED edge used exactly twice (that is closure).
local dir, undir = {}, {}
for _, t in ipairs(T) do
	for e = 1, 3 do
		local a, b = t[e], t[e % 3 + 1]
		dir[a .. ">" .. b] = (dir[a .. ">" .. b] or 0) + 1
		local k = a < b and (a .. "-" .. b) or (b .. "-" .. a)
		undir[k] = (undir[k] or 0) + 1
	end
end
local dirBad, undirBad, edges = 0, 0, 0
for _, c in pairs(dir) do
	if c ~= 1 then
		dirBad += 1
	end
end
for _, c in pairs(undir) do
	edges += 1
	if c ~= 2 then
		undirBad += 1
	end
end
require_(dirBad == 0, string.format("%d directed edges are not used exactly once (orientation)", dirBad))
require_(undirBad == 0, string.format("%d edges are not shared by exactly two faces (closure)", undirBad))

-- Euler characteristic. This solid is an annulus rotated about the axis, i.e. a
-- SOLID TORUS, so its boundary is genus 1 and V - E + F must be 0 -- not 2. If
-- this comes out 2 the joint has been closed off into a sphere, which would mean
-- the band is not actually joining the two tubes.
local chi = #V - edges + #T
require_(chi == 0, string.format("Euler characteristic %d, expected 0 (genus 1 boundary of a solid torus)", chi))

-- apothems measured from the vertex data itself, by the same rule the place was
-- measured with: the closest approach of an edge segment to the axis.
local function apothemOf(n, r, y)
	local best = math.huge
	for k = 0, n - 1 do
		local p = Vector3.new(r * math.cos(2 * math.pi * k / n), y, r * math.sin(2 * math.pi * k / n))
		local q = Vector3.new(r * math.cos(2 * math.pi * (k + 1) / n), y, r * math.sin(2 * math.pi * (k + 1) / n))
		local d = q - p
		local t = -(p.X * d.X + p.Z * d.Z) / (d.X * d.X + d.Z * d.Z)
		t = math.clamp(t, 0, 1)
		local c = Vector3.new(p.X + d.X * t, 0, p.Z + d.Z * t)
		best = math.min(best, c.Magnitude)
	end
	return best
end
local ap18 = apothemOf(N18, R_OUT18, Z_COLLAR)
local ap24 = apothemOf(N24, R_OUT24, Z_BAND)
say("apothem of the collar's outer rim %.4f  (design %.4f)", ap18, A18)
say("apothem of the wall's   outer rim %.4f  (design %.4f)", ap24, A24)
-- Tolerance is 1e-3, not 1e-6, and the reason is not sloppiness: Vector3 stores
-- its components as float32, so at magnitude ~64 the representable step is already
-- ~7.6e-6 and the cos/sin/projection round-trip costs a few more. A tighter gate
-- here would fire on the storage format, not on the geometry -- and a check that
-- cries wolf at a fixed epsilon is the same failure as the always-red validator in
-- CLAUDE.md 0.13. Honest resolution at this scale is the 4 decimals the raycast
-- probe in the place can actually deliver.
require_(math.abs(ap18 - A18) < 1e-3, string.format("collar apothem %.6f is not A18 %.6f", ap18, A18))
require_(math.abs(ap24 - A24) < 1e-3, string.format("wall apothem %.6f is not A24 %.6f", ap24, A24))

-- signed volume: positive means the normals point OUT. Computed as the divergence
-- integral sum(a . (b x c))/6 over the triangles.
local vol = 0
for _, t in ipairs(T) do
	local a, b, c = V[t[1]], V[t[2]], V[t[3]]
	vol += a:Dot(b:Cross(c)) / 6
end
say("signed volume %.1f cubic studs (expect ~21700, and it MUST be positive)", vol)
require_(vol > 0, string.format("signed volume is %.1f -- the normals point inward", vol))
require_(vol > 15000 and vol < 28000, string.format("signed volume %.1f is outside the 15000..28000 sanity band", vol))

-- bbox straight from the vertices, not from any Size property (CLAUDE.md 0.18).
local lo = Vector3.new(math.huge, math.huge, math.huge)
local hi = Vector3.new(-math.huge, -math.huge, -math.huge)
for _, v in ipairs(V) do
	lo = Vector3.new(math.min(lo.X, v.X), math.min(lo.Y, v.Y), math.min(lo.Z, v.Z))
	hi = Vector3.new(math.max(hi.X, v.X), math.max(hi.Y, v.Y), math.max(hi.Z, v.Z))
end
say("mesh bbox  X %.4f..%.4f  Y %.4f..%.4f  Z %.4f..%.4f",
	lo.X, hi.X, lo.Y, hi.Y, lo.Z, hi.Z)
say("mesh size  %.4f x %.4f x %.4f  (expect %.4f x %.4f x %.4f)",
	hi.X - lo.X, hi.Y - lo.Y, hi.Z - lo.Z, 2 * R_OUT24, Z_TOP, 2 * R_OUT24)

if #problems > 0 then
	-- Nothing has been created at this point, so a refusal costs nothing -- but it
	-- carries the whole log out with it. A refusal that hides the numbers that
	-- caused it costs a debugging round trip every time.
	return "GEOMETRY REJECTED" .. string.char(10)
		.. table.concat(problems, string.char(10)) .. string.char(10)
		.. "---- log ----" .. string.char(10) .. table.concat(out, string.char(10))
end
say("geometry ACCEPTED: closed, consistently oriented, right size")

-- ============================================================ 4. into the place

local AssetService = game:GetService("AssetService")
local okMesh, meshOrErr = pcall(function()
	return AssetService:CreateEditableMesh()
end)
if not okMesh then
	return "BLOCKED: AssetService:CreateEditableMesh() failed -> "
		.. tostring(meshOrErr)
		.. "  (the docs gate EditableMesh behind 'Enable Mesh / Image APIs' for published games)"
end
local mesh = meshOrErr
say("CreateEditableMesh ok: %s", tostring(mesh))

local ids = {}
for i, v in ipairs(V) do
	ids[i] = mesh:AddVertex(v)
end
for i, t in ipairs(T) do
	mesh:AddTriangle(ids[t[1]], ids[t[2]], ids[t[3]])
end
say("mesh filled: %d vertices, %d triangles", #ids, #T)

-- Content.fromObject keeps the mesh INSIDE the place file (serialization
-- can_save = true), which is the whole reason this route needs no credential.
local content
local okContent, contentOrErr = pcall(function()
	content = Content.fromObject(mesh)
	return content
end)
if not okContent then
	return "FAILED: Content.fromObject(mesh) -> " .. tostring(contentOrErr)
end
say("Content.fromObject ok: %s", tostring(content))

local okPart, partOrErr = pcall(function()
	return AssetService:CreateMeshPartAsync(content)
end)
if not okPart then
	return "FAILED: CreateMeshPartAsync -> " .. tostring(partOrErr)
end
local mp = partOrErr

-- Mirror the neighbour rather than impositing a new look: the wall continues this
-- ring, so it should be made of what the ring is made of.
local ref = ring.parts[1]
mp.Name = NEW_NAME
mp.Anchored = true
-- CanCollide is NOT mirrored from the neighbour, and this is the one place the
-- wall deliberately differs from the ring it continues.
--
-- CollisionFidelity cannot be written on a MeshPart whose mesh came from
-- Content.fromObject: four values were tried (Default, Hull,
-- PreciseConvexDecomposition, Box), all four wrote without error and all four
-- read back Default, and re-parenting did not change that. The same property IS
-- writable on the imported MeshParts next door, whose MeshContent is a Uri -- so
-- the cause is this route, not Studio. The collision body is therefore a CONVEX
-- HULL whatever we ask for, and the hull of a ring is a SOLID DISK 137.17 studs
-- across spanning y 47.4..60.6: it would seal the chamber.
--
-- A wall that is not solid is the smaller lie than a solid disk nobody can see,
-- so: CanCollide false, and CanQuery false as well once the probes below are done
-- (they need CanQuery true to run at all).
mp.CanCollide = false
mp.CanTouch = ref.CanTouch
mp.CanQuery = true
mp.Material = ref.Material
mp.Color = ref.Color
mp.Transparency = ref.Transparency
mp.CastShadow = ref.CastShadow
mp.CFrame = CFrame.new(CENTRE)
mp.Parent = ring.inst.Parent

say("created %s under %s", mp:GetFullName(), tostring(ring.inst.Parent))
say("MeshSize %s   Size %s   Position %s", tostring(mp.MeshSize), tostring(mp.Size), tostring(mp.Position))
say("mirrored from %s: Material %s  Color %s  CanCollide %s",
	ref.Name, tostring(ref.Material), tostring(ref.Color), tostring(ref.CanCollide))

-- ============================================================ 5. read it back

-- CAVEAT, learned the hard way: a raycast against this MeshPart queries the
-- COLLISION body, which is a convex hull (see the CanCollide note above). The
-- hull is coincident with the render mesh up the straight 24-gon and far from it
-- across the collar, so the wall numbers below are right and the collar numbers
-- below are the HULL's, not the mesh's. The render mesh is read back vertex by
-- vertex in cw24_verify.luau; that is where the join is measured.
--
-- Downward probes at three radii. Two of them answer "where did the geometry
-- actually land" (which is how a pivot convention that differs from Roblox's
-- importer gets caught instead of assumed), and the third is a negative control
-- that must miss: nothing exists beyond the 24-gon's circumradius.
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Include
params.FilterDescendantsInstances = { mp }
params.IgnoreWater = true
local function downAt(rho)
	local o = Vector3.new(CENTRE.X + rho, CENTRE.Y + 60, CENTRE.Z)
	local h = workspace:Raycast(o, Vector3.new(0, -200, 0), params)
	if not h then
		return nil
	end
	return h.Position.Y
end
local yCollar = downAt(A18 - 1.5)
local yWall = downAt((A18 + A24) * 0.5)
local yOutside = downAt(A24 + 3.0)
say("top of the collar at rho=%.3f -> %s   (expect %.3f)", A18 - 1.5,
	yCollar and string.format("%.4f", yCollar) or "MISS", CENTRE.Y + Z_COLLAR)
say("top of the wall   at rho=%.3f -> %s   (expect %.3f)", (A18 + A24) * 0.5,
	yWall and string.format("%.4f", yWall) or "MISS", CENTRE.Y + Z_TOP)
say("negative control  at rho=%.3f -> %s   (must MISS)", A24 + 3.0,
	yOutside and string.format("%.4f", yOutside) or "MISS")

-- The two readings that ARE the join: same instrument, same radii, same phase as
-- the existing ring. If the collar's apothem and corner angles match the ring's,
-- the new outer face is coplanar with the old one and the joint is continuous.
local newCollar = { radialProbe(mp, CENTRE.Y + 0.6, 90) }
local newWall = { radialProbe(mp, CENTRE.Y + 8.0, 90) }
say("collar probe @y=%.3f  apothem %.4f @%.2f   circum %.4f @%.2f   misses %d",
	CENTRE.Y + 0.6, newCollar[1], newCollar[2], newCollar[3], newCollar[4], newCollar[5])
say("wall   probe @y=%.3f  apothem %.4f @%.2f   circum %.4f @%.2f   misses %d",
	CENTRE.Y + 8.0, newWall[1], newWall[2], newWall[3], newWall[4], newWall[5])
say("ring   probe @y=47.075  apothem %.4f @%.2f   circum %.4f @%.2f   misses %d",
	ringLo, ringLoAt, ringHi, ringHiAt, ringMiss)

local verdict = {}
verdict[#verdict + 1] = string.format("collar apothem %.4f vs ring %.4f  (delta %.4f)",
	newCollar[1], ringLo, newCollar[1] - ringLo)
verdict[#verdict + 1] = string.format("collar corner at %.2f deg, ring corner at %.2f deg",
	newCollar[4], ringHiAt)
verdict[#verdict + 1] = string.format("wall apothem %.4f (design %.4f)", newWall[1], A24)
say("JOIN %s", table.concat(verdict, " | "))

-- The probes are done, so the part can now be put into the state it ships in:
-- alive to the eye, absent from physics and from every raycast in the game. A
-- hull-shaped collision body is worse than none, because none is a wall you can
-- walk through and a hull is a chamber you cannot enter.
mp.CanQuery = false
say("final: CanCollide %s  CanQuery %s  (the collision body is a hull either way)",
	tostring(mp.CanCollide), tostring(mp.CanQuery))

return table.concat(out, string.char(10))
