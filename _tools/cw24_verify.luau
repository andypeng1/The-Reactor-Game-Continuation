-- cw24_verify.luau -- verify ChamberWall24 against the design, and against the ring.
--
-- Two instruments were wrong in the first pass, and both were wrong in the same
-- direction: they answered the question they were asked, confidently, with a
-- number that was not the measurement.
--
--   1. The rim grouping filtered by height only, so the collar's OUTER ring
--      (radius 63.712..64.695) and its INNER ring (59.712..60.633) landed in one
--      bucket. The chord-to-axis minimum over the mixed set is 59.712 -- a real
--      apothem, of a ring that was not the one being asked about (CLAUDE.md 0.18).
--      Fix: band by RADIUS as well as height, and assert the vertex count.
--
--   2. A raycast against a MeshPart queries its COLLISION geometry, and a
--      MeshPart's default CollisionFidelity is a convex hull. The hull of an
--      annulus is a solid disk, so every probe "saw" a surface ~0.6 studs proud
--      of the collar. Fix: read the RENDER mesh (EditableMesh read-back) for
--      shape, and only use raycasts once the collision body is worth trusting.
--
-- Also fixed here: the phase report. rmax is attained at EVERY corner, so the
-- argmax is decided by float32 noise in the last digit -- the first two runs
-- disagreed (340 deg vs 320 deg) on identical geometry. The argmin is unique per
-- sector, so phase is reported as argmin mod (360/n) and must be (360/n)/2.
local AssetService = game:GetService("AssetService")
local NAME = "ChamberWall24"
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

local N18, N24 = 18, 24
local A18, A24 = 63.712, 68.000
local WALL = 4.00
local Z_COLLAR, Z_BAND, Z_TOP = 1.20, 4.20, 13.20
local R_OUT18 = A18 / math.cos(math.pi / N18)
local R_IN18 = (A18 - WALL) / math.cos(math.pi / N18)
local R_OUT24 = A24 / math.cos(math.pi / N24)
local R_IN24 = (A24 - WALL) / math.cos(math.pi / N24)

local out = {}
local bad = {}
local checks = 0
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end
local function want(ok, fmt, ...)
	local msg = string.format(fmt, ...)
	checks += 1
	if not ok then
		bad[#bad + 1] = msg
	end
	say("%s %s", ok and "  ok  " or " FAIL ", msg)
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
say("Position %s   Size %s", tostring(mp.Position), tostring(mp.Size))
say("CollisionFidelity %s", tostring(mp.CollisionFidelity))

-- ============================================================ the render mesh

local m2 = AssetService:CreateEditableMeshAsync(mp.MeshContent)
local ids = m2:GetVertices()
local V = {}
for i, id in ipairs(ids) do
	V[i] = m2:GetPosition(id)
end
say("render mesh: %d vertices, %d faces", #V, #m2:GetFaces())
want(#V == 168, "vertex count %d == 168", #V)

local lo = Vector3.new(math.huge, math.huge, math.huge)
local hi = Vector3.new(-math.huge, -math.huge, -math.huge)
for _, v in ipairs(V) do
	lo = Vector3.new(math.min(lo.X, v.X), math.min(lo.Y, v.Y), math.min(lo.Z, v.Z))
	hi = Vector3.new(math.max(hi.X, v.X), math.max(hi.Y, v.Y), math.max(hi.Z, v.Z))
end
say("bbox  X %.4f..%.4f  Y %.4f..%.4f  Z %.4f..%.4f", lo.X, hi.X, lo.Y, hi.Y, lo.Z, hi.Z)
want(math.abs((hi.X - lo.X) - 2 * R_OUT24) < 1e-3, "width %.4f == 2*R_OUT24 %.4f", hi.X - lo.X, 2 * R_OUT24)
want(math.abs((hi.Y - lo.Y) - Z_TOP) < 1e-3, "height %.4f == Z_TOP %.4f", hi.Y - lo.Y, Z_TOP)
want(math.abs(lo.Y) < 1e-4, "mesh local y=0 is the collar's base (got %.4f)", lo.Y)

-- One rim: vertices at height y whose radius falls in [rmin, rmax]. Both the band
-- and the count are asserted, so mixing two rings into one bucket cannot pass.
local function rim(label, y, rmin, rmax, wantN, wantApothem, wantCirc)
	local pts = {}
	for _, v in ipairs(V) do
		if math.abs(v.Y - y) < 1e-3 then
			local r = math.sqrt(v.X * v.X + v.Z * v.Z)
			if r >= rmin and r <= rmax then
				pts[#pts + 1] = { v = v, th = math.atan2(v.Z, v.X) }
			end
		end
	end
	table.sort(pts, function(a, b)
		return a.th < b.th
	end)
	local apothem, radLo, radHi = math.huge, math.huge, -math.huge
	for i, p in ipairs(pts) do
		local q = pts[i % #pts + 1]
		local r = math.sqrt(p.v.X * p.v.X + p.v.Z * p.v.Z)
		radLo = math.min(radLo, r)
		radHi = math.max(radHi, r)
		local d = q.v - p.v
		local t = -(p.v.X * d.X + p.v.Z * d.Z) / (d.X * d.X + d.Z * d.Z)
		t = math.clamp(t, 0, 1)
		local c = Vector3.new(p.v.X + d.X * t, 0, p.v.Z + d.Z * t)
		apothem = math.min(apothem, c.Magnitude)
	end
	say("%-18s %2d verts  circum %.4f  apothem %.4f", label, #pts, radHi, apothem)
	want(#pts == wantN, "%s has %d verts (want %d)", label, #pts, wantN)
	want(math.abs(apothem - wantApothem) < 1e-3, "%s apothem %.4f (want %.4f)", label, apothem, wantApothem)
	want(math.abs(radHi - wantCirc) < 1e-3, "%s circumradius %.4f (want %.4f)", label, radHi, wantCirc)
	return apothem, radHi, pts
end

say("---- rims ----")
local apCollarOut, circCollarOut, ptsCollarOut = rim("collar outer y=1.2", Z_COLLAR, 62.0, 66.0, 18, A18, R_OUT18)
rim("collar inner y=1.2", Z_COLLAR, 58.0, 62.0, 18, A18 - WALL, R_IN18)
rim("collar base  y=0.0", 0.00, 62.0, 66.0, 18, A18, R_OUT18)
rim("wall outer   y=4.2", Z_BAND, 66.0, 70.0, 24, A24, R_OUT24)
rim("wall inner   y=4.2", Z_BAND, 62.0, 66.0, 24, A24 - WALL, R_IN24)
local apWallOut, circWallOut = rim("wall top     y=13.2", Z_TOP, 66.0, 70.0, 24, A24, R_OUT24)
rim("wall top in  y=13.2", Z_TOP, 62.0, 66.0, 24, A24 - WALL, R_IN24)

-- Corner phase, from the rims rather than from a raycast. Vertex k of an n-gon
-- built with (r cos, y, r sin) sits at 360k/n; the design puts vertex 0 on +X.
local function cornerPhase(pts, n)
	local step = 360 / n
	local worst = 0
	for _, p in ipairs(pts) do
		local d = math.abs(p.th * 180 / math.pi) % step
		local e = math.min(d, step - d)
		worst = math.max(worst, e)
	end
	return worst
end
want(cornerPhase(ptsCollarOut, 18) < 0.01, "collar corner max phase error %.4f deg", cornerPhase(ptsCollarOut, 18))

-- The join is a claim about two surfaces, so it is stated as one: the collar's
-- outer face must be coplanar with the existing ring's outer face. Both numbers
-- come from the same kind of instrument (a chord-to-axis minimum over a rim), so
-- a shared bias cancels and the difference is meaningful.
local ringOuterApothem = 63.7114 -- measured in the place by the 720-ray probe
say("---- the join ----")
want(math.abs(apCollarOut - ringOuterApothem) < 0.01,
	"collar apothem %.4f vs the existing ring's %.4f (delta %.4f)",
	apCollarOut, ringOuterApothem, apCollarOut - ringOuterApothem)
want(math.abs(circCollarOut - apCollarOut * 1 / math.cos(math.pi / 18)) < 1e-3,
	"collar circum/apothem ratio is 1/cos(10 deg) -> a VERTEX sits on +X, same as the ring")
want(math.abs(apWallOut - A24) < 1e-3, "the wall flares to apothem %.4f (design %.4f)", apWallOut, A24)
say("outward growth: %.4f studs of apothem over %.2f studs of height (%.1f deg lean)",
	A24 - A18, Z_BAND - Z_COLLAR, math.deg(math.atan((A24 - A18) / (Z_BAND - Z_COLLAR))))

-- ============================================================ collision

-- The first build wrote CollisionFidelity = PreciseConvexDecomposition and every
-- probe came back byte-identical. That reads as "the write took and changed
-- nothing"; it is not. The property SILENTLY DISCARDS writes on a MeshPart whose
-- mesh came from Content.fromObject -- four values were tried on this part and
-- four read back Default, and re-parenting did not help. The test that makes the
-- cause visible is next door: the imported MeshParts under Workspace.Wall24 hold
-- a Uri and DO accept the same write (they arrive already set to Precise). So it
-- is a limit of the no-upload route, not a Studio bug and not a wrong call.
--
-- The consequence is not cosmetic. A MeshPart's collision body is a convex hull
-- by default, and the hull of a ring is a SOLID DISK. Measure it, then pick the
-- lesser lie.
local function downAt(target, rho, y0)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { target }
	params.IgnoreWater = true
	local o = Vector3.new(CENTRE.X + rho, CENTRE.Y + y0, CENTRE.Z)
	local h = workspace:Raycast(o, Vector3.new(0, -200, 0), params)
	return h and h.Position.Y or nil
end
local function inwardAt(target, y, rho)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { target }
	params.IgnoreWater = true
	local o = Vector3.new(CENTRE.X + rho, y, CENTRE.Z)
	local h = workspace:Raycast(o, Vector3.new(-rho * 2, 0, 0), params)
	return h and (rho - h.Distance) or nil
end

say("---- collision ----")
-- Both probes need CanQuery, so it is re-asserted first: this script has to be
-- re-runnable against a part that already ships in its final state.
mp.CanQuery = true
local holeHull = downAt(mp, A18 - 1.5, 60)
local collarHull = inwardAt(mp, CENTRE.Y + 0.6, 90)
say("the collision body as measured: hole probe %s, collar face at rho %s",
	holeHull and string.format("HIT y=%.3f", holeHull) or "MISS",
	collarHull and string.format("%.4f", collarHull) or "MISS")
say("  a hollow ring MISSes the hole probe and shows the collar at %.4f;", R_OUT18)
say("  this is solid there, and its collar face is the fan out to the 24-gon.")

-- Characterization, not a requirement: the requirement is that the write is not
-- RELIED on, not that it keeps failing. If this ever goes red the platform gained
-- the ability and the note above went stale -- re-measure before celebrating.
local wasFidelity = mp.CollisionFidelity
local okSet = pcall(function()
	mp.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
end)
say("write CollisionFidelity=Precise -> ok=%s, reads back %s (was %s)",
	tostring(okSet), tostring(mp.CollisionFidelity), tostring(wasFidelity))
want(okSet and mp.CollisionFidelity == wasFidelity,
	"CollisionFidelity is silently read-only on an Object-backed MeshPart")

-- The state this ships in, and both flags are load-bearing: CanCollide would put
-- a 137-stud solid disk into physics, CanQuery would hand the same disk to every
-- raycast in the game.
mp.CanCollide = false
mp.CanQuery = false
want(mp.CanCollide == false, "the wall is out of physics (CanCollide false)")
want(mp.CanQuery == false, "the wall is out of raycasts (CanQuery false)")

say("")
if #bad == 0 then
	say("ALL CHECKS PASS -- %d ok, 0 failed", checks)
else
	say("%d of %d CHECK(S) FAILED", #bad, checks)
end
return table.concat(out, string.char(10))
