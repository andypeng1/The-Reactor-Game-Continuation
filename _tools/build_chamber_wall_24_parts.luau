-- build_chamber_wall_24_parts.luau -- the same wall, built from Parts.
--
-- WHY THIS EXISTS. The wall was first built as a single MeshPart through
-- AssetService:CreateEditableMesh -> Content.fromObject -> CreateMeshPartAsync
-- (no upload credential needed), and its geometry verified vertex by vertex. But
-- that route cannot have a collision body: CollisionFidelity SILENTLY DISCARDS
-- writes on a MeshPart whose MeshContent is an Object (four values tried, four
-- read back Default; the imported Uri-backed parts next door accept the same
-- write, so the cause is the route and not Studio). The collision body is
-- therefore a convex hull -- and the hull of a ring is a SOLID DISK 137 studs
-- across, which would seal the chamber. Shipping it with CanCollide = false left
-- the wall as the ONLY thing in that whole neighbourhood a player can walk
-- through: the ring it continues is 19 parts, all CanCollide, and 60 of 60 parts
-- overlapping the wall's own vertical band are solid. So the operator chose:
-- build the wall out of Parts, so the visible shape and the collision body are
-- the same parts and cannot disagree.
--
-- THE CONSTRUCTION IS EXACT, and that is worth stating because it is not obvious.
-- A panel of a regular polygon shell is a BOX: outer face on the polygon face
-- plane at apothem a, inner face parallel at a - WALL, chord 2*a*tan(pi/n) wide.
-- With the chord at exactly 2*a*tan(pi/n) the two half-chords reach the polygon
-- vertices, so adjacent panels meet exactly there and overlap slightly inside --
-- which means the UNION of the n panels IS the polygon shell, corners included.
-- No corner wedges, no gaps, no overshoot.
--
-- The single approximation is the transition band, and it is bounded -- and the
-- bound is MEASURED, not derived. The band's panels are the same boxes leaned 55
-- degrees, so the band's base is a 24-gon of apothem 63.712 while the collar below
-- it is an 18-gon of the same apothem. At the seam the collar's corner reaches
-- 64.6949 and the band's base reaches 64.3946: proud by 0.3002 studs, and the band
-- has overtaken that corner 0.520 studs higher, at world y 49.120. My hand
-- arithmetic said 0.434 and 0.5153, and it was wrong in the first figure because it
-- compared polygon vertices -- the band's panels are boxes, and their corners carry
-- a tangential overhang that a polygon vertex does not have. The measurement
-- supersedes the derivation; both are in cw24_parts_verify.luau.
--
-- THE PHASE IS A READING TOO, and it is the one that was wrong. A regular polygon
-- rotated by half a step has the same apothem, the same chord, the same area and the
-- same silhouette radius -- so "the collar uses the ring's apothem" describes TWO
-- different walls, and only one of them joins. cw24_phase.luau measured which one is
-- in this place: the 18-gon puts a VERTEX at azimuth 0 (720 inward rays, all 18 maxima
-- at 0.0000 mod 20) and its 18 face-centred panels therefore sit at 10 mod 20. A shell
-- built at k*2*pi/n puts a FACE at azimuth 0 -- half a step out -- so the first version
-- put the collar's faces where the ring's corners are, the ring's corners stood 0.98
-- studs proud of the collar, and the collar's own corners floated 0.98 studs clear of
-- the ring's faces. Every check in this file passed anyway, because the phase check
-- compared the panels against their own lattice (phi % step), which any rotation
-- satisfies. A check that cannot fail is not evidence.
--
-- So the phase and the apothem are both read off the ring's SURFACE at build time, and
-- the operator's rule -- 3 collar panels meet 4 wall panels, 18 * 4/3 = 24 -- is now
-- written as a test of that relation (a collar vertex every 60 degrees meets a wall
-- vertex) rather than as a number anyone is asked to trust.
--
-- The three sections, all in the mesh's coordinates (origin at the ring's axis,
-- y = 0 at the platform top, which is where the collar's base sits):
--
--   collar  y  0.00 ->  1.20   18 panels, outer apothem 63.712
--   band    y  1.20 ->  4.20   24 panels, leaned 55 deg outward
--   wall    y  4.20 -> 13.20   24 panels, outer apothem 68.000

local ServerStorage = game:GetService("ServerStorage")
local workspace = game:GetService("Workspace")

local NAME = "ChamberWall24"
local PARK = "ChamberWall24_mesh_20261004"
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

-- A24 is a pure design choice: how far out the new wall stands. WALL, the three heights
-- and TUCK are choices. A18 and the phase are NOT -- both are read off the ring's own
-- surface below, because a chosen value with a tolerance around it is a weaker
-- statement than the reading, and the tolerance is exactly where the half-step hid.
local A24 = 68.000
local WALL = 4.00
local Z_COLLAR = 1.20
local Z_BAND = 4.20
local Z_TOP = 13.20

-- How far the band's panels are tucked down into the collar. The lean is 55 deg,
-- so a tuck of 0.60 buries the lower end 0.34 studs below the seam, where the
-- collar is 4.00 thick and the band at that height is only 2.29 thick
-- perpendicular -- the tuck is what stops the seam from being a knife edge.
local TUCK = 0.60

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

-- ============================================================ find the template

-- The ring's panels are the template for everything cosmetic: Material, Color,
-- Reflectance and the six surface types come off one of them. Mirroring the
-- neighbour is how the wall stays one object with the thing it continues,
-- instead of two objects that happen to touch.
local ring
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "18" and d:IsA("Folder") and #d:GetChildren() > 5 then
		ring = d
	end
end
if not ring then
	return "could not find the 18-side ring -- refusing to build something that has a stated join to it"
end
local template
for _, d in ipairs(ring:GetChildren()) do
	if d:IsA("BasePart") and d.Name == "Part" then
		template = d
		break
	end
end
if not template then
	return "the ring has no plain Part to mirror -- refusing to guess at the finish"
end
say("template: %s", template:GetFullName())
say("  Material %s  Color %.3f %.3f %.3f  Reflectance %.3f  surfaces %s/%s/%s",
	tostring(template.Material),
	template.Color.R, template.Color.G, template.Color.B, template.Reflectance,
	tostring(template.TopSurface), tostring(template.FrontSurface), tostring(template.BottomSurface))

-- ====================================================== measure the ring's surface

-- Phase and apothem come off the SURFACE, not off any part's Position or Size. A Part's
-- Size is a statement about its own local frame -- the ring's 18 panels do not share one
-- orientation, so a "position minus half the size" reading would be a guess dressed as a
-- measurement (CLAUDE.md 0.18). A 720-ray inward sweep has no local frame to get wrong:
-- its minima ARE the face centres and its maxima ARE the vertices.
--
-- It is also self-checking, which is the whole point. If the phase were off by half a
-- step the minima would land on the vertices instead, and every one of the three
-- assertions below would fire: 18 minima 20 deg apart, all at the same radius, 10 deg
-- from 18 maxima that are all at rmin/cos(pi/18). There is no way for this to quietly
-- agree with a wrong answer, because a wrong answer does not have that shape.
local STEP18 = 2 * math.pi / 18
local STEP24 = 2 * math.pi / 24

local RING_PROBE_Y = 47.075
local NRAY = 720

local ringRay = RaycastParams.new()
ringRay.FilterType = Enum.RaycastFilterType.Include
ringRay.FilterDescendantsInstances = { ring }
ringRay.IgnoreWater = true

local prof = {}
local miss = 0
for k = 0, NRAY - 1 do
	local th = (k / NRAY) * 2 * math.pi
	local dir = Vector3.new(math.cos(th), 0, math.sin(th))
	local o = Vector3.new(CENTRE.X + dir.X * 100, RING_PROBE_Y, CENTRE.Z + dir.Z * 100)
	local h = workspace:Raycast(o, -dir * 200, ringRay)
	if h then
		prof[k] = (Vector3.new(h.Position.X, RING_PROBE_Y, h.Position.Z)
			- Vector3.new(CENTRE.X, RING_PROBE_Y, CENTRE.Z)).Magnitude
	else
		prof[k] = nil
		miss += 1
	end
end
if miss > 0 then
	return string.format("only %d of %d probe rays hit the ring -- refusing to build off a partial reading",
		NRAY - miss, NRAY)
end

local rMin, rMax = math.huge, 0
for k = 0, NRAY - 1 do
	rMin = math.min(rMin, prof[k])
	rMax = math.max(rMax, prof[k])
end

local faceAz, vertexAz = {}, {}
for k = 0, NRAY - 1 do
	local p, n = prof[(k - 1) % NRAY], prof[(k + 1) % NRAY]
	local th = (k / NRAY) * 2 * math.pi
	if prof[k] < p and prof[k] < n then faceAz[#faceAz + 1] = th end
	if prof[k] > p and prof[k] > n then vertexAz[#vertexAz + 1] = th end
end

local function offDeg(d, step)
	local rem = d % step
	return math.deg(math.min(rem, step - rem))
end

if #faceAz ~= 18 or #vertexAz ~= 18 then
	return string.format("the ring's profile shows %d face minima and %d vertices, not 18 and 18 -- refusing to build on a reading that does not have the shape of the ring",
		#faceAz, #vertexAz)
end
local ringPhase = faceAz[1]
for i, a in ipairs(faceAz) do
	if offDeg(a - ringPhase, STEP18) > 0.05 then
		return string.format("ring face minima are not 20 deg apart (%.4f deg off at #%d) -- refusing to build",
			offDeg(a - ringPhase, STEP18), i)
	end
end
for _, a in ipairs(vertexAz) do
	if offDeg(a - ringPhase - STEP18 * 0.5, STEP18) > 0.05 then
		return string.format("a ring vertex is not half a step from the face lattice -- refusing to build")
	end
end
if math.abs((rMax / rMin) - 1 / math.cos(math.pi / 18)) > 1e-4 then
	return string.format("the ring's profile is not a regular 18-gon: vertex/face ratio %.6f, cos(pi/18)^-1 %.6f",
		rMax / rMin, 1 / math.cos(math.pi / 18))
end

local A18 = rMin

say("")
say("ring measured off its surface, not assumed:")
say("  face minima at %+.4f deg mod 20 -> its VERTICES are at %+.4f deg mod 20 (that is the phase)",
	math.deg(ringPhase) % 20, (math.deg(ringPhase) + math.deg(STEP18) * 0.5) % 20)
say("  apothem %.4f (face plane)  circumradius %.4f (the ring's outermost extent)",
	rMin, rMax)
say("  ratio %.6f vs 1/cos(pi/18) %.6f, %d minima / %d vertices, all 20 deg apart",
	rMax / rMin, 1 / math.cos(math.pi / 18), #faceAz, #vertexAz)

local parent = ring.Parent
if not parent then
	return "the ring has no parent -- refusing to build"
end

-- ============================================================ guards

-- Re-running has to be a decision, not an accident: building a second copy on top
-- of the first would leave two coincident walls and no way to tell which one is
-- load-bearing. The name IS already taken on the first run -- by the MeshPart this
-- script exists to replace -- so hold only when the occupant is something else.
local existing = parent:FindFirstChild(NAME)
if existing and not existing:IsA("MeshPart") then
	return parent:GetFullName() .. " already has a " .. NAME .. " of class " .. existing.ClassName
		.. " -- delete it first if you mean to rebuild"
end
local oldMesh
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("MeshPart") and d.Name == NAME then
		oldMesh = d
	end
end
-- Parking is idempotent, not once-only. Refuse only in the case that would actually
-- lose something: a mesh still standing in the world AND the park name already taken,
-- which forces a human to say which record is which. A re-run of an already-parked
-- wall finds nothing to park and just rebuilds the panels.
if oldMesh and ServerStorage:FindFirstChild(PARK) then
	return "ServerStorage already holds " .. PARK .. " and a MeshPart named " .. NAME
		.. " is still in the world -- resolve one of the two by hand"
end

-- ============================================================ build

local model = Instance.new("Model")
model.Name = NAME

local built = 0
local function panel(label, pos, size, yaw, tilt)
	local p = Instance.new("Part")
	p.Name = label
	p.Shape = Enum.PartType.Block
	p.Size = size
	-- CFrame before parent, always: a Part is born at the world origin, and a
	-- 17-stud panel lying across the map for one frame is a thing that has
	-- actually happened here before (CLAUDE.md 0.19).
	p.CFrame = CFrame.new(pos) * CFrame.Angles(0, yaw, 0) * CFrame.Angles(tilt, 0, 0)
	p.Anchored = true
	p.CanCollide = true
	p.CanQuery = true
	p.Material = template.Material
	p.Color = template.Color
	p.Reflectance = template.Reflectance
	p.TopSurface = template.TopSurface
	p.BottomSurface = template.BottomSurface
	p.LeftSurface = template.LeftSurface
	p.RightSurface = template.RightSurface
	p.FrontSurface = template.FrontSurface
	p.BackSurface = template.BackSurface
	p.Parent = model
	built += 1
	return p
end

-- A vertical polygon shell: n panels whose outer faces are the polygon's faces.
-- The chord is the full 2*a*tan(pi/n), which is what makes adjacent panels meet
-- at the vertices instead of leaving a notch between them.
-- `phase` is the azimuth of panel 1's FACE CENTRE. It is a parameter and not k*2*half
-- because the join is a relation to the ring, not a property of this function: built at
-- k*2*pi/n every shell puts a face on azimuth 0, and the ring keeps a vertex there.
local function shell(n, phase, apothem, yBase, height, prefix)
	local half = math.pi / n
	local chord = 2 * apothem * math.tan(half)
	local rMid = apothem - WALL * 0.5
	local parts = {}
	for k = 0, n - 1 do
		local phi = phase + k * 2 * half
		local nrm = Vector3.new(math.cos(phi), 0, math.sin(phi))
		local pos = CENTRE + nrm * rMid + Vector3.new(0, yBase + height * 0.5, 0)
		-- CFrame.Angles(0, yaw, 0) sends local +Z to (sin yaw, 0, cos yaw); we want
		-- +Z to be the outward normal, so yaw = pi/2 - phi.
		parts[#parts + 1] = panel(prefix .. tostring(k + 1), pos,
			Vector3.new(chord, height, WALL), math.pi / 2 - phi, 0)
	end
	say("%s: %d panels, apothem %.4f, chord %.4f, y %.2f..%.2f",
		prefix, n, apothem, chord, yBase, yBase + height)
	return parts
end

say("")
say("building %s under %s", NAME, parent:GetFullName())

-- ---- collar: the 18-gon, continuing the ring's own surface. Faces on faces: the
-- collar's panels sit exactly where the ring's panels sit, so the collar's vertices
-- land on the ring's vertices (63.7114 -> 64.6951, both read off the surface above).
-- This one argument is the whole fix.
local collar = shell(18, ringPhase, A18, 0, Z_COLLAR, "Collar")

-- ---- wall: the 24-gon, above the flare. Half an 18-step plus half a 24-step puts the
-- wall's VERTEX on the ring's vertex lattice -- which is the same statement as the
-- operator's own, 3 collar panels meeting 4 wall panels (18 * 4/3 = 24). Written as the
-- phase it is an azimuth; written as the relation it is 60 deg of collar vertex
-- coinciding with a wall vertex, and that is asserted directly below rather than
-- trusted to the arithmetic here.
local wallPhase = ringPhase + STEP18 * 0.5 + STEP24 * 0.5
local wallSec = shell(24, wallPhase, A24, Z_BAND, Z_TOP - Z_BAND, "Wall")

-- ---- band: the flare between them. Each panel is the same kind of box, leaned by
-- the angle the two rims subtend. Its outer face is the plane through
-- (A18, Z_COLLAR) and (A24, Z_BAND); its thickness is the PERPENDICULAR distance
-- between that plane and the inner one, which is WALL * cos(lean) -- the inner rim
-- sits WALL studs inside the outer one HORIZONTALLY, and a leaned surface has less
-- perpendicular thickness than horizontal separation.
local dR = A24 - A18
local dY = Z_BAND - Z_COLLAR
local len0 = math.sqrt(dR * dR + dY * dY)
local lean = math.atan2(dR, dY)                  -- 0 = vertical, pi/2 = horizontal
local uR, uY = dR / len0, dY / len0              -- along the lean, outward-and-up
local iR, iY = -uY, uR                           -- perpendicular, inward-and-up
local thickness = WALL * math.cos(lean)

local r0, y0 = A18 - uR * TUCK, Z_COLLAR - uY * TUCK   -- the tucked lower end
local len = len0 + TUCK
local rFace, yFace = (r0 + A24) * 0.5, (y0 + Z_BAND) * 0.5
local rMid, yMid = rFace + iR * thickness * 0.5, yFace + iY * thickness * 0.5

say("Band: lean %.2f deg, face length %.4f (tucked %.2f into the collar), perpendicular thickness %.4f",
	math.deg(lean), len, TUCK, thickness)

local half24 = math.pi / 24
local bandChord = 2 * A24 * math.tan(half24)
for k = 0, 23 do
	local phi = wallPhase + k * 2 * half24
	local nrm = Vector3.new(math.cos(phi), 0, math.sin(phi))
	panel("Band" .. tostring(k + 1),
		CENTRE + nrm * rMid + Vector3.new(0, yMid, 0),
		Vector3.new(bandChord, len, thickness),
		math.pi / 2 - phi, lean)
end
say("Band: 24 panels, chord %.4f, outer rim %.4f -> %.4f", bandChord, A18, A24)

-- ============================================================ self-check, before it is in the world

-- Everything above is arithmetic on numbers I chose; this is the part that can be
-- wrong. The check reads the PART's own CFrame and Size -- the same state a reader
-- outside would see -- rather than the variables used to build it, so it tests the
-- delivered thing and not the intent.
local bad = {}
local checked = 0
local function want(ok, fmt, ...)
	checked += 1
	if not ok then
		bad[#bad + 1] = string.format(fmt, ...)
	end
end

local function outerFaceCentre(p)
	-- local +Z is the outward normal for every panel built here
	return p.CFrame * Vector3.new(0, 0, p.Size.Z * 0.5)
end

local function checkShell(parts, n, phase, apothem, yBase, height, label)
	for _, p in ipairs(parts) do
		local c = outerFaceCentre(p)
		local flat = Vector3.new(c.X - CENTRE.X, 0, c.Z - CENTRE.Z)
		local phi = math.atan2(flat.Z, flat.X)
		local step = 2 * math.pi / n
		-- Anchored at the shell's OWN phase, not at azimuth 0. The property being
		-- asserted is even spacing; anchoring at 0 would also assert something nobody
		-- wants -- that the shell is rotated a particular way -- and the join is decided
		-- elsewhere, against the ring.
		local err = offDeg(phi - phase, step)
		want(math.abs(flat.Magnitude - apothem) < 1e-3,
			"%s %s outer face at %.5f (design %.5f)", label, p.Name, flat.Magnitude, apothem)
		-- Say exactly what this does and does not claim. It claims the panels are evenly
		-- spaced about the axis -- a real property, and one a mistyped chord would break.
		-- It is NOT the join check and never was: every rotation of a regular polygon is
		-- evenly spaced. This line passed on the half-step-rotated build. The join check
		-- is the relative one below.
		want(err < 1e-3, "%s %s is off its own %d-fold lattice by %.4f deg", label, p.Name, n, err)
		want(math.abs(c.Y - (CENTRE.Y + yBase + height * 0.5)) < 1e-3,
			"%s %s outer face centre y %.4f (design %.4f)", label, p.Name, c.Y,
			CENTRE.Y + yBase + height * 0.5)
	end
end

checkShell(collar, 18, ringPhase, A18, 0, Z_COLLAR, "collar")
checkShell(wallSec, 24, wallPhase, A24, Z_BAND, Z_TOP - Z_BAND, "wall")

-- ---- the join: measured against the ring, not against itself.
-- This is the check whose absence let the half-step ship. Nothing above compares the
-- new work to the thing it continues, so nothing above could see a rotation.
local function azOfWorld(v)
	return math.atan2(v.Z - CENTRE.Z, v.X - CENTRE.X)
end

for _, p in ipairs(collar) do
	local off = offDeg(azOfWorld(outerFaceCentre(p)) - ringPhase, STEP18)
	want(off < 1e-3,
		"COLLAR NOT JOINED: %s sits %.4f deg off the ring's own panels -- a half step reads as 10.0000 here",
		p.Name, off)
end
for _, p in ipairs(wallSec) do
	local off = offDeg(azOfWorld(outerFaceCentre(p)) - wallPhase, STEP24)
	want(off < 1e-3, "wall %s sits %.4f deg off the wall's own lattice", p.Name, off)
end

-- The operator's rule as a test of the RELATION rather than of a number: every 60 deg
-- of collar vertex must land on a wall vertex, i.e. every 3 collar panels meet 4 wall
-- panels. This is the assertion that would have caught the original defect, and it
-- reads 10.0000 deg -- not 0 -- when the phase is wrong.
local collarVertexAz = ringPhase + STEP18 * 0.5
local wallVertexAz = wallPhase + STEP24 * 0.5
for k = 0, 5 do
	local cv = collarVertexAz + k * (math.pi / 3)
	local off = offDeg(cv - wallVertexAz, STEP24)
	want(off < 1e-3,
		"3:4 JOIN OFF: collar vertex at %.4f deg misses the nearest wall vertex by %.4f deg",
		math.deg(cv), off)
end
say("")
say("join: collar faces on the ring's faces, wall vertices on the ring's vertex lattice,")
say("      every 60 deg of collar vertex meeting a wall vertex (18 * 4/3 = 24).")

-- The band cannot be checked by radius alone: its outer face is a tilted plane, so
-- an apothem is only meaningful at a given height. Check that the two design points
-- lie ON the face instead -- which is the actual claim being made.
local wOut = Vector3.new(uY, -uR, 0)             -- the face normal in (r, y)
for _, p in ipairs(model:GetChildren()) do
	if string.sub(p.Name, 1, 4) == "Band" then
		local c = outerFaceCentre(p)
		local flat = Vector3.new(c.X - CENTRE.X, 0, c.Z - CENTRE.Z)
		local nrm = flat.Unit
		local off = offDeg(azOfWorld(c) - wallPhase, STEP24)
		want(off < 1e-3, "band %s sits %.4f deg off the wall's own lattice", p.Name, off)
		for _, q in ipairs({ { A18, Z_COLLAR }, { A24, Z_BAND } }) do
			-- the design point, in world space, at this panel's azimuth
			local w = CENTRE + nrm * q[1] + Vector3.new(0, q[2], 0)
			local d = w - c
			local dr = nrm.X * d.X + nrm.Z * d.Z
			local off = math.abs(dr * wOut.X + d.Y * wOut.Y)
			want(off < 2e-3, "band %s: design point r=%.3f y=%.3f is %.5f off the outer face",
				p.Name, q[1], q[2], off)
		end
	end
end

say("")
say("self-check: %d checks, %d failed", checked, #bad)
for _, b in ipairs(bad) do
	say("  FAIL " .. b)
end
if #bad > 0 then
	model:Destroy()
	return table.concat(out, string.char(10)) .. string.char(10)
		.. "NOTHING WAS BUILT -- the panels failed self-check, so the model was thrown away before it could reach the world."
end

-- ============================================================ park the mesh, then swap in

-- The MeshPart is not deleted. It is the verified artifact -- 168 vertices, 336
-- faces, read back and asserted against the design -- and the reason this wall
-- exists at all. It goes to ServerStorage, where it stops rendering and stops
-- simulating, under a name that says what it is.
if oldMesh then
	local meshParent = oldMesh.Parent
	oldMesh.Parent = ServerStorage
	oldMesh.Name = PARK
	say("parked the MeshPart as %s (was %s.%s)", oldMesh:GetFullName(), meshParent:GetFullName(), NAME)
else
	local already = ServerStorage:FindFirstChild(PARK)
	say("no MeshPart named %s left in the world -- the record is already parked as ServerStorage.%s (%s)",
		NAME, PARK, already and already.ClassName or "MISSING -- check ServerStorage by hand")
end

model.Parent = parent
say("built %s holding %d parts", model:GetFullName(), #model:GetChildren())
say("")
say("totals: %d panels = 18 collar + 24 band + 24 wall; all Anchored, CanCollide, CanQuery", built)
say("the wall is now SOLID. It was not before -- see the header.")

return table.concat(out, string.char(10))
