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

-- Measured inputs. A18 is a design number whose acceptance test is a DELTA against
-- the ring that is already in the place, not a check against itself (see
-- cw24_verify.luau, "the join"). A24 is a pure design choice.
local A18 = 63.712
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
local function shell(n, apothem, yBase, height, prefix)
	local half = math.pi / n
	local chord = 2 * apothem * math.tan(half)
	local rMid = apothem - WALL * 0.5
	local parts = {}
	for k = 0, n - 1 do
		local phi = k * 2 * half
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

-- ---- collar: the 18-gon, continuing the ring's own surface
local collar = shell(18, A18, 0, Z_COLLAR, "Collar")

-- ---- wall: the 24-gon, above the flare
local wallSec = shell(24, A24, Z_BAND, Z_TOP - Z_BAND, "Wall")

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
	local phi = k * 2 * half24
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

local function checkShell(parts, n, apothem, yBase, height, label)
	for _, p in ipairs(parts) do
		local c = outerFaceCentre(p)
		local flat = Vector3.new(c.X - CENTRE.X, 0, c.Z - CENTRE.Z)
		local phi = math.atan2(flat.Z, flat.X)
		local step = 2 * math.pi / n
		local rem = phi % step
		local err = math.min(rem, step - rem) * 180 / math.pi
		want(math.abs(flat.Magnitude - apothem) < 1e-3,
			"%s %s outer face at %.5f (design %.5f)", label, p.Name, flat.Magnitude, apothem)
		want(err < 1e-3, "%s %s corner phase off by %.4f deg", label, p.Name, err)
		want(math.abs(c.Y - (CENTRE.Y + yBase + height * 0.5)) < 1e-3,
			"%s %s outer face centre y %.4f (design %.4f)", label, p.Name, c.Y,
			CENTRE.Y + yBase + height * 0.5)
	end
end

checkShell(collar, 18, A18, 0, Z_COLLAR, "collar")
checkShell(wallSec, 24, A24, Z_BAND, Z_TOP - Z_BAND, "wall")

-- The band cannot be checked by radius alone: its outer face is a tilted plane, so
-- an apothem is only meaningful at a given height. Check that the two design points
-- lie ON the face instead -- which is the actual claim being made.
local wOut = Vector3.new(uY, -uR, 0)             -- the face normal in (r, y)
for _, p in ipairs(model:GetChildren()) do
	if string.sub(p.Name, 1, 4) == "Band" then
		local c = outerFaceCentre(p)
		local flat = Vector3.new(c.X - CENTRE.X, 0, c.Z - CENTRE.Z)
		local nrm = flat.Unit
		local step = 2 * math.pi / 24
		local rem = math.atan2(flat.Z, flat.X) % step
		want(math.min(rem, step - rem) * 180 / math.pi < 1e-3,
			"band %s corner phase off", p.Name)
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
