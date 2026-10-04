-- cw24_parts_verify.luau -- the Part-built wall, checked against the design AND
-- against the ring it continues.
--
-- This file exists because the previous wall could not be tested for the thing
-- that mattered. It was a MeshPart whose collision body was a convex hull -- the
-- hull of a ring is a SOLID DISK -- so every raycast into it answered about the
-- hull, and the fix was to take it out of physics entirely. That is what made it
-- the only walk-through object in a solid neighbourhood.
--
-- Now the same rays answer about the actual geometry, because the geometry IS the
-- collision body. So the checks below can finally include the ones that were
-- impossible: no gaps anywhere on the shell, and the right radius at the right
-- height.
--
-- Everything here reads INSTANCE STATE (parts' CFrames and Sizes, and the world's
-- own raycasts). Nothing reads a module table: a module read would answer about a
-- private copy of the numbers and not about what is standing in the place
-- (CLAUDE.md 0.2).

local ServerStorage = game:GetService("ServerStorage")
local NAME = "ChamberWall24"
local PARK = "ChamberWall24_mesh_20261004"
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

local N18, N24 = 18, 24
-- A18 is the ring's apothem as measured off its own surface, not a number anyone chose.
-- This file re-measures it live further down and requires the recorded value to agree
-- within 0.005, so this line is a record and not an input.
local A18, A24 = 63.7114, 68.000
local WALL = 4.00
local Z_COLLAR, Z_BAND, Z_TOP = 1.20, 4.20, 13.20
local LEAN = math.atan2(A24 - A18, Z_BAND - Z_COLLAR)

-- The ring's own outer apothem, measured independently by a 720-ray sweep against
-- the plain Parts in the place (not against this model). The join is a claim about
-- two surfaces, so it is stated as a delta between two measurements of the same
-- kind -- never as a check of my design number against itself.
local RING_APOTHEM = 63.7114

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

-- ============================================================ find it

local model
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == NAME and d:IsA("Model") then
		model = d
	end
end
if not model then
	return "no Model named " .. NAME .. " under Workspace"
end
say("model %s", model:GetFullName())

-- The parked mesh: the point is that it is OUT of the world, so this is a check on
-- its absence as much as its presence.
local parked = ServerStorage:FindFirstChild(PARK)
want(parked ~= nil and parked:IsA("MeshPart"),
	"the previous MeshPart is parked as ServerStorage.%s (%s)",
	PARK, parked and parked.ClassName or "MISSING")
local leftover = 0
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("MeshPart") and d.Name == NAME then
		leftover += 1
	end
end
want(leftover == 0, "no MeshPart named %s is left in the world (%d)", NAME, leftover)

-- ============================================================ the parts

local groups = { Collar = {}, Band = {}, Wall = {} }
local unknown = {}
for _, p in ipairs(model:GetChildren()) do
	local g = string.match(p.Name, "^(%a+)" )
	if p:IsA("BasePart") and groups[g] then
		groups[g][#groups[g] + 1] = p
	else
		unknown[#unknown + 1] = p.Name .. " (" .. p.ClassName .. ")"
	end
end
want(#model:GetChildren() == 66, "the model holds 66 parts (%d)", #model:GetChildren())
want(#unknown == 0, "every child is a Collar/Band/Wall panel (%s)", table.concat(unknown, ", "))
want(#groups.Collar == 18, "18 collar panels (%d)", #groups.Collar)
want(#groups.Band == 24, "24 band panels (%d)", #groups.Band)
want(#groups.Wall == 24, "24 wall panels (%d)", #groups.Wall)

-- The three flags are the whole point of the rebuild, so they are checked on every
-- single part rather than sampled.
local notSolid, notAnchored, notQuery = 0, 0, 0
for _, p in ipairs(model:GetChildren()) do
	if not p.CanCollide then notSolid += 1 end
	if not p.Anchored then notAnchored += 1 end
	if not p.CanQuery then notQuery += 1 end
end
want(notSolid == 0, "all 66 parts are in physics (CanCollide) -- %d are not", notSolid)
want(notAnchored == 0, "all 66 parts are Anchored -- %d are not", notAnchored)
want(notQuery == 0, "all 66 parts answer raycasts (CanQuery) -- %d do not", notQuery)

-- The finish must match the ring, or the wall reads as a different object sitting
-- on top of it. Compare against the ring rather than against a remembered colour.
-- The same walk also collects the ring's own panel azimuths, because the ring is the
-- reference for two things -- its finish and its PHASE -- and one walk that answers
-- both is one place to be wrong instead of two.
local ringPart
local ringFaceAzs = {}
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "18" and d:IsA("Folder") and #d:GetChildren() > 5 then
		for _, c in ipairs(d:GetChildren()) do
			if c:IsA("BasePart") and c.Name == "Part" then
				ringPart = ringPart or c
				ringFaceAzs[#ringFaceAzs + 1] =
					math.atan2(c.Position.Z - CENTRE.Z, c.Position.X - CENTRE.X)
			end
		end
	end
end
if ringPart then
	local sample = groups.Wall[1]
	want(sample.Material == ringPart.Material,
		"the wall wears the ring's Material (%s vs %s)", tostring(sample.Material), tostring(ringPart.Material))
	want(math.abs(sample.Color.R - ringPart.Color.R) < 1e-3
		and math.abs(sample.Color.G - ringPart.Color.G) < 1e-3
		and math.abs(sample.Color.B - ringPart.Color.B) < 1e-3,
		"the wall wears the ring's Color (%.3f %.3f %.3f vs %.3f %.3f %.3f)",
		sample.Color.R, sample.Color.G, sample.Color.B,
		ringPart.Color.R, ringPart.Color.G, ringPart.Color.B)
else
	say("(the ring was not found, so the finish was not compared against it)")
end

-- ============================================================ the ring's PHASE

-- The one thing every radius check in this file is blind to. A regular polygon
-- ROTATED BY HALF A STEP has the same apothem, the same chord, the same area and the
-- same silhouette: the collar's outer face at 63.7114 against the ring's 63.7114 is
-- satisfied by BOTH rotations, so it is not a join check and never was. The join is
-- an angle, and the only authority for it is the ring that is already in the place.
--
-- Reduced to one number: the unwrapped mean of the ring's 18 face azimuths. The
-- unwrap matters -- a plain mean of angles that straddle +-180 is meaningless.
local ringFaceAz
if #ringFaceAzs > 0 then
	local step18 = 2 * math.pi / N18
	local base = ringFaceAzs[1]
	local sum = 0
	for _, a in ipairs(ringFaceAzs) do
		local d = a - base
		sum += d - math.floor(d / step18 + 0.5) * step18
	end
	ringFaceAz = base + sum / #ringFaceAzs
end
want(ringFaceAz ~= nil, "the ring's phase was read off its own panels (%s)",
	ringFaceAz and string.format("%.4f deg", math.deg(ringFaceAz)) or "MISSING")
-- And the wall's phase is DERIVED from it, not chosen: half an 18-step puts a VERTEX
-- where a face was (so the collar's faces inherit the ring's faces), then half a
-- 24-step puts the wall's own vertices back on the ring's -- and only every third
-- ring vertex can carry one, because 3 * 20 = 4 * 15 = 60. That relation is the
-- operator's own "18 * (4/3) = 24" and it is checked as a count below.
local wallFaceAz = ringFaceAz and (ringFaceAz + math.pi / N18 + math.pi / N24)
if ringFaceAz then
	say("ring phase: %d face azimuths, mean %.4f deg; its vertices fall at %.4f deg",
		#ringFaceAzs, math.deg(ringFaceAz), math.deg(ringFaceAz) + 180 / N18)
	say("            collar faces belong at %.4f deg, wall faces at %.4f deg",
		math.deg(ringFaceAz), math.deg(wallFaceAz))
else
	say("(the ring's phase could not be read, so the join is not checked at all)")
end

local function include(inst)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { inst }
	params.IgnoreWater = true
	return params
end

-- ============================================================ geometry, from the parts themselves

-- The outer face of a panel is its +Z face: p.CFrame * (0, 0, Size.Z/2). For the
-- collar and the wall that face is vertical, so its horizontal distance from the
-- axis IS the apothem. For the band it is leaned, so the useful statement is that
-- the two design rims lie ON the face.
local function faceCentre(p)
	return p.CFrame * Vector3.new(0, 0, p.Size.Z * 0.5)
end
local function flat(v)
	return Vector3.new(v.X - CENTRE.X, 0, v.Z - CENTRE.Z)
end
-- How far this panel's face centre is from a GIVEN azimuth, taken around the nearest
-- multiple of the shell's step. The phase is a parameter and not a constant, and that
-- is the whole correction: the previous version was `math.atan2(...) % step`, which
-- measures a panel against azimuth 0 -- a rotation nobody asked for -- and therefore
-- reports 0 for every rotation of the shell. It answered "is this shell regularly
-- spaced", which is true of all 18 rotations, while the question was "is this shell
-- the one that joins" (CLAUDE.md 0.18: a check that cannot fail is not evidence).
local function phaseErr(p, phase, step)
	local f = flat(faceCentre(p))
	local d = math.atan2(f.Z, f.X) - phase
	local rem = d % step
	return math.min(rem, step - rem)
end

local function checkVertical(list, n, phase, apothem, yBase, height, label, phaseName)
	local step = 2 * math.pi / n
	local worstApothem, worstPhase, worstY = 0, 0, 0
	for _, p in ipairs(list) do
		local f = flat(faceCentre(p))
		worstApothem = math.max(worstApothem, math.abs(f.Magnitude - apothem))
		worstPhase = math.max(worstPhase, phaseErr(p, phase, step))
		worstY = math.max(worstY, math.abs(faceCentre(p).Y - (CENTRE.Y + yBase + height * 0.5)))
		-- and the face must actually point outward, not merely be at the right radius.
		-- ZVector is +Z; LookVector is MINUS Z (camera convention) and would point
		-- at the axis -- reading the right property is the whole check here.
		local nrm = p.CFrame.ZVector
		want(math.abs(nrm.Y) < 1e-4, "%s %s face is vertical (normal.Y %.6f)", label, p.Name, nrm.Y)
		local radial = flat(faceCentre(p))
		want(dot2(nrm, radial) > 0.999,
			"%s %s face points outward (dot %.5f)", label, p.Name, dot2(nrm, radial))
	end
	want(worstApothem < 1e-3, "%s: every outer face is at apothem %.4f (worst off by %.6f)",
		label, apothem, worstApothem)
	-- 0.01 deg is a thousandth of the half-step error this is here to catch, and it is
	-- comfortably above the scatter in the ring's own authored panels (~0.002 deg),
	-- which is the floor: the reference is a real object, not a number.
	want(worstPhase < 0.01, "%s: every face centre sits on %s (worst %.5f deg off)",
		label, phaseName, worstPhase)
	want(worstY < 1e-3, "%s: every face centre is at its section's mid height (worst off by %.6f)",
		label, worstY)
end

function dot2(a, b)
	return (a.X * b.X + a.Z * b.Z) / (math.sqrt(a.X * a.X + a.Z * a.Z) * math.sqrt(b.X * b.X + b.Z * b.Z))
end

-- A missing ring degrades these to the old azimuth-0 question instead of erroring, so
-- the rest of the geometry is still reported -- but the miss is already on the record
-- above, and the phase name says so out loud rather than being quietly mislabelled.
local collarPhase, collarPhaseName = ringFaceAz or 0, "the ring's own face lattice"
local wallPhaseV, wallPhaseName = wallFaceAz or 0, "its 4/3-derived face lattice"
if not ringFaceAz then
	collarPhaseName = "azimuth 0 -- the ring is MISSING, see the failure above"
	wallPhaseName = collarPhaseName
end

checkVertical(groups.Collar, N18, collarPhase, A18, 0, Z_COLLAR, "collar", collarPhaseName)
checkVertical(groups.Wall, N24, wallPhaseV, A24, Z_BAND, Z_TOP - Z_BAND, "wall", wallPhaseName)

-- The band. Its outer face is a tilted plane, so an apothem only means something at
-- a stated height; the claim worth checking is that the rims it was designed to
-- join are points ON that plane.
local wOut = Vector3.new(math.cos(LEAN), -math.sin(LEAN), 0)   -- face normal, in (r, y)
local worstOnFace, worstLean, worstPhaseB = 0, 0, 0
for _, p in ipairs(groups.Band) do
	local c = faceCentre(p)
	local nrm = flat(c).Unit
	worstPhaseB = math.max(worstPhaseB, phaseErr(p, wallPhaseV, 2 * math.pi / N24))
	for _, q in ipairs({ { A18, Z_COLLAR }, { A24, Z_BAND } }) do
		local w = CENTRE + nrm * q[1] + Vector3.new(0, q[2], 0)
		local d = w - c
		local dr = nrm.X * d.X + nrm.Z * d.Z
		worstOnFace = math.max(worstOnFace, math.abs(dr * wOut.X + d.Y * wOut.Y))
	end
	-- the panel's own normal must be the leaned one, not a vertical one
	local n3 = p.CFrame.ZVector
	local horiz = math.sqrt(n3.X * n3.X + n3.Z * n3.Z)
	worstLean = math.max(worstLean, math.abs(horiz - math.cos(LEAN)), math.abs(n3.Y + math.sin(LEAN)))
end
want(worstPhaseB < 0.01, "band: every panel sits on the wall's own face lattice (worst %.5f deg off)",
	worstPhaseB)
want(worstOnFace < 2e-3, "band: both design rims lie on every outer face (worst %.6f studs)", worstOnFace)
want(worstLean < 1e-3, "band: every panel is leaned %.2f deg (worst off by %.6f)",
	math.deg(LEAN), worstLean)

-- ============================================================ the join

-- Same kind of measurement on both sides of the seam, so the difference is
-- meaningful even if both instruments share a bias. Both sides are measured LIVE and
-- the same way -- 720 inward rays at the structure's own mid height, minimum radius
-- -- because comparing my design number against itself would be a tautology that
-- passes even if both were wrong (DECISIONS 95, restated in DECISIONS_2 183).
local ringFolder
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "18" and d:IsA("Folder") and #d:GetChildren() > 5 then
		ringFolder = d
	end
end
local ringApothem
if ringFolder then
	local rp = include(ringFolder)
	local lo = math.huge
	for k = 0, 719 do
		local th = math.rad(k * 0.5)
		local dir = Vector3.new(math.cos(th), 0, math.sin(th))
		-- the ring's panels are centred at world y = CENTRE.Y - 0.325, so this is
		-- their mid height -- the height at which the apothem is the answer
		local o = Vector3.new(CENTRE.X + dir.X * 120, CENTRE.Y - 0.325, CENTRE.Z + dir.Z * 120)
		local hit = workspace:Raycast(o, -dir * 240, rp)
		if hit then
			lo = math.min(lo, (Vector3.new(hit.Position.X - CENTRE.X, 0, hit.Position.Z - CENTRE.Z)).Magnitude)
		end
	end
	if lo < math.huge then
		ringApothem = lo
	end
end
want(ringApothem ~= nil, "the ring's own outer apothem, measured in the place now (%s)",
	ringApothem and string.format("%.4f", ringApothem) or "MISS")
if ringApothem then
	say("     the ring's top is at world y %.4f, the collar's base is at %.4f -- the wall stands on it",
		CENTRE.Y, CENTRE.Y)
	want(math.abs(ringApothem - RING_APOTHEM) < 0.005,
		"the live ring measurement agrees with the recorded 720-ray probe (%.4f vs %.4f)",
		ringApothem, RING_APOTHEM)
	local worstJoin = 0
	for _, p in ipairs(groups.Collar) do
		worstJoin = math.max(worstJoin, math.abs(flat(faceCentre(p)).Magnitude - ringApothem))
	end
	want(worstJoin < 0.01,
		"the collar's outer face is coplanar with the ring's own (worst delta %.4f studs)", worstJoin)
end
say("outward growth: %.4f studs of apothem over %.2f studs of height (%.2f deg lean)",
	A24 - A18, Z_BAND - Z_COLLAR, math.deg(LEAN))

-- The operator's own statement of the join, counted rather than derived: from one ring
-- vertex to the next (60 deg) there are 3 collar panels and 4 wall panels -- 18 * 4/3 =
-- 24 -- and of the ring's 18 vertices exactly 6 carry a wall vertex, because
-- 3 * 20 = 4 * 15 = 60. Both counts are needed and neither is enough: a count cannot
-- see a ROTATION (any 15 deg lattice has 4 points in any 60 deg window, so this reads
-- 4 whether or not the wall is phased right), while the phase check above cannot see
-- how many panels there are. Two questions, two instruments.
if ringFaceAz and #groups.Wall == N24 then
	local function azDeg(p)
		local f = flat(faceCentre(p))
		return math.deg(math.atan2(f.Z, f.X))
	end
	local vertexDeg = math.deg(ringFaceAz) + 180 / N18
	local function countIn(list, span)
		local c = 0
		for _, p in ipairs(list) do
			if ((azDeg(p) - vertexDeg) % 360) < span then c += 1 end
		end
		return c
	end
	local nCollar = countIn(groups.Collar, 60)
	local nWall = countIn(groups.Wall, 60)
	want(nCollar == 3, "one 60 deg sector of the ring carries 3 collar panels (%d)", nCollar)
	want(nWall == 4, "and 4 wall panels (%d) -- 18 * (4/3) = 24", nWall)
	-- Which ring vertices a wall vertex lands on: this one DOES see the rotation, but
	-- only as 0 vs 6 -- the ring's vertices mod 15 take three values, six each, so a
	-- shift of exactly 5 or 10 deg still reads 6. The phase check above is what pins
	-- the rotation; this is what shows the 4/3 rule happening.
	local carried = 0
	for k = 0, N18 - 1 do
		local rv = vertexDeg + k * (360 / N18)
		local best = math.huge
		for _, p in ipairs(groups.Wall) do
			local d = (azDeg(p) + 180 / N24 - rv) % (360 / N24)
			best = math.min(best, math.min(d, 360 / N24 - d))
		end
		if best < 0.01 then carried += 1 end
	end
	want(carried == 6, "%d of the ring's 18 vertices carry a wall vertex (6 by 18/3)", carried)
end

-- ============================================================ the shell has no gaps

-- Six heights across the three sections, 720 rays each. Every one must hit, and
-- this is the check the MeshPart could never pass: its hull is solid, so it would
-- have "passed" trivially, and its render mesh could not be probed at all.
local params = include(model)

local misses, minRho, maxRho = 0, math.huge, -math.huge
for _, y in ipairs({ 0.05, 0.60, Z_COLLAR + 0.05, 2.70, Z_BAND + 0.05, 8.70, Z_TOP - 0.05 }) do
	local lo, hi, n = math.huge, -math.huge, 0
	for k = 0, 719 do
		local th = math.rad(k * 0.5)
		local dir = Vector3.new(math.cos(th), 0, math.sin(th))
		local o = Vector3.new(CENTRE.X + dir.X * 120, CENTRE.Y + y, CENTRE.Z + dir.Z * 120)
		local h = workspace:Raycast(o, -dir * 240, params)
		if h then
			local r = (Vector3.new(h.Position.X - CENTRE.X, 0, h.Position.Z - CENTRE.Z)).Magnitude
			lo, hi, n = math.min(lo, r), math.max(hi, r), n + 1
		else
			misses += 1
		end
	end
	minRho, maxRho = math.min(minRho, lo), math.max(maxRho, hi)
	say("  y %6.2f : %3d/720 rays hit   rho %.4f .. %.4f", y, n, lo, hi)
end
want(misses == 0, "the shell is closed at every height tested (%d of 5040 rays missed)", misses)

-- The documented approximation, measured rather than asserted: at the seam the
-- 18-gon's corner stands proud of the 24-gon the band starts from.
local function sweepMax(y)
	local hi = -math.huge
	for k = 0, 3599 do
		local th = math.rad(k * 0.1)
		local dir = Vector3.new(math.cos(th), 0, math.sin(th))
		local o = Vector3.new(CENTRE.X + dir.X * 120, CENTRE.Y + y, CENTRE.Z + dir.Z * 120)
		local h = workspace:Raycast(o, -dir * 240, params)
		if h then
			hi = math.max(hi, (Vector3.new(h.Position.X - CENTRE.X, 0, h.Position.Z - CENTRE.Z)).Magnitude)
		end
	end
	return hi
end
local cornerCollar = sweepMax(Z_COLLAR - 0.05)
local cornerBand = sweepMax(Z_COLLAR + 0.05)
say("the seam: 18-gon corner reaches %.4f, the band's base reaches %.4f (proud by %.4f studs)",
	cornerCollar, cornerBand, cornerCollar - cornerBand)
want(cornerCollar - cornerBand > 0, "the collar's corner does stand proud at the seam (documented)")
want(cornerCollar - cornerBand < 0.5, "and it is bounded under half a stud (%.4f)",
	cornerCollar - cornerBand)

-- And the nub is transient, which is the other half of the claim. Measure the band's
-- surface in the exact direction of a collar CORNER -- a ring vertex, read off the
-- ring instead of hardcoded, because which azimuth that is is a reading and not a
-- choice (CLAUDE.md 0.18) -- and find the height at which the band has overtaken the
-- corner's own radius. A bound is asserted rather than the figure the arithmetic
-- predicts, because that arithmetic is mine while the measurement is the place's.
local cornerDeg = ringFaceAz and (math.deg(ringFaceAz) + 180 / N18) or 20
-- The angle between that corner and the nearest wall face centre is the whole reason
-- the nub exists at all, and it is a consequence of the 18:24 ratio rather than an
-- input: 10 deg from the collar's own face, 5 or 10 from the wall's. Printed because
-- the shape of the seam is what this section is about.
local offWallFace = math.abs(((cornerDeg - math.deg(wallFaceAz or 0) + 180 / N24) % (360 / N24)) - 180 / N24)
local function radialAt(y, deg)
	local th = math.rad(deg)
	local dir = Vector3.new(math.cos(th), 0, math.sin(th))
	local o = Vector3.new(CENTRE.X + dir.X * 120, CENTRE.Y + y, CENTRE.Z + dir.Z * 120)
	local h = workspace:Raycast(o, -dir * 240, params)
	return h and (Vector3.new(h.Position.X - CENTRE.X, 0, h.Position.Z - CENTRE.Z)).Magnitude or nil
end
local crossover, hc = nil, 0.0
while hc < 2.0 do
	local r = radialAt(Z_COLLAR + hc, cornerDeg)
	if r and r >= cornerCollar then
		crossover = hc
		break
	end
	hc += 0.005
end
say("     the corner is at %.4f deg, %.4f deg off the nearest wall face centre",
	cornerDeg, offWallFace)
say("     the band overtakes it %.3f studs above the seam (world y %.3f)",
	crossover or -1, CENTRE.Y + Z_COLLAR + (crossover or 0))
want(crossover ~= nil and crossover > 0.2 and crossover < 1.0,
	"the nub is gone within a stud of height (%s)", crossover and string.format("%.3f", crossover) or "never")

-- ============================================================ now it is solid, and that is testable

-- `deg` is not cosmetic: every one of these distances is a distance to a FACE, so a
-- ray aimed 12.5 deg off the nearest face centre measures apothem/cos(12.5) and lands
-- a whole stud away from the design plane. The azimuth is an argument so that the
-- caller has to say which surface it means (CLAUDE.md 0.18 -- the wrong surface does
-- not error, it answers confidently).
local function downAt(rho, y0, len, deg)
	local th = math.rad(deg or 0)
	local dir = Vector3.new(math.cos(th), 0, math.sin(th))
	local o = Vector3.new(CENTRE.X + dir.X * rho, CENTRE.Y + y0, CENTRE.Z + dir.Z * rho)
	local h = workspace:Raycast(o, Vector3.new(0, -len, 0), params)
	return h and h.Position.Y or nil
end
-- A wall/band FACE CENTRE direction: where every radial distance to those panels is
-- the apothem itself. Read from the phase, never assumed to be +X.
local faceDeg = (wallFaceAz and math.deg(wallFaceAz) or 0) + 180
local function inwardAt(y, rho, deg)
	local th = math.rad(deg or 0)
	local dir = Vector3.new(math.cos(th), 0, math.sin(th))
	local o = Vector3.new(CENTRE.X + dir.X * rho, CENTRE.Y + y, CENTRE.Z + dir.Z * rho)
	local h = workspace:Raycast(o, -dir * (rho * 2), params)
	return h and (rho - h.Distance) or nil
end

local hCollar = inwardAt(0.60, 90, math.deg(ringFaceAz or 0))
want(hCollar ~= nil and math.abs(hCollar - A18) < 0.01,
	"a ray into the collar stops at rho %.4f (design %.4f)", hCollar or -1, A18)
local hWall = inwardAt(8.70, 90, faceDeg)
want(hWall ~= nil and math.abs(hWall - A24) < 0.01,
	"a ray into the wall stops at rho %.4f (design %.4f)", hWall or -1, A24)
local hTop = downAt(66.0, 20, 12, faceDeg)
want(hTop ~= nil and math.abs(hTop - (CENTRE.Y + Z_TOP)) < 0.01,
	"the wall's top rim is at world y %.4f (design %.4f)", hTop or -1e9, CENTRE.Y + Z_TOP)

-- The hole is still a hole. This is the check that would have caught a solid disk.
local hHole = downAt(55.0, 20, 40)
want(hHole == nil, "the middle is still open -- a downward ray at rho 55 hits nothing (%s)",
	hHole and string.format("y=%.3f", hHole) or "MISS")
-- ...and at rho 62 the first surface is the BAND'S INNER FACE, not the collar's top.
-- The first version of this check said "the collar's top", and the collar's top is
-- not exposed anywhere: the band's inner surface springs from the collar's own inner
-- rim (both at apothem A18 - WALL), so above the seam there is no ledge at all. A
-- ray that lands on the band's inner slope instead was the geometry being right and
-- the question being wrong (CLAUDE.md 0.18).
--
-- Aimed at a wall FACE CENTRE (-X here, the one 180 deg from the wall's own phase),
-- because that is where the inner face is its own apothem from the axis; anywhere else
-- the ray meets the same plane at apothem/cos(delta) and the design figure would be
-- wrong by more than a stud. This used to read +X, which was a face centre only under
-- the OLD phase -- a hardcoded azimuth that quietly stopped meaning what it said.
local innerRadial = (A18 - WALL)
local slope = (A24 - A18) / (Z_BAND - Z_COLLAR)
local wantY = CENTRE.Y + Z_COLLAR + (62.0 - innerRadial) / slope
local hInner = downAt(62.0, 20, 40, faceDeg)
want(hInner ~= nil and math.abs(hInner - wantY) < 0.01,
	"at rho 62 the ray lands on the band's inner face at y %.4f (design %.4f)", hInner or -1e9, wantY)
say("     (the collar's top is covered there: its inner rim IS the band's springing line)")

say("")
if #bad == 0 then
	say("ALL CHECKS PASS -- %d ok, 0 failed", checks)
else
	say("%d of %d CHECK(S) FAILED", #bad, checks)
end
return table.concat(out, string.char(10))
