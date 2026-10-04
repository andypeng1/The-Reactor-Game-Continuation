-- cw24_phase.luau -- READ ONLY. Where are the ring's corners, and where are mine?
--
-- WHY THIS EXISTS. The join was verified as a RADIUS -- collar 63.7120 against the
-- live ring 63.7114, delta 0.0006 -- and never as an ANGLE. But a regular polygon
-- ROTATED BY HALF A STEP has the same apothem, the same chord, the same area and
-- the same silhouette radius. Every radius check passes while the two rings disagree
-- at every single corner. So the only instrument that can see this is a comparison
-- of angles against the ring that is already in the place (CLAUDE.md 0.18).
--
-- Three independent estimates of the same angle, because one estimate that agrees
-- with itself is not evidence:
--   a) the azimuth of each ring panel's own Position (its centre lies on the face
--      normal, so its azimuth IS the face-centre azimuth);
--   b) the azimuth of each ring panel's CFrame.ZVector (the outward normal itself);
--   c) a 720-ray inward sweep from outside -- its local maxima are the vertices and
--      its local minima are the face centres, measured on the surface rather than
--      read off a part.
--
-- Nothing here writes. It reports, and the reading is the point.

local workspace = game:GetService("Workspace")

local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)
local R_OUT = 120.0          -- start the sweep outside everything
local STEP_DEG = 0.5

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

local function azim(v)
	return math.deg(math.atan2(v.Z, v.X))
end

-- signed distance to the nearest multiple of `step` -- 0 means "on the grid",
-- +/- step/2 means "exactly half a step off". Wrapping is the whole point: the two
-- candidate answers are separated by half a step, so a wrapped difference names
-- which one it is without any comparison logic.
local function offGrid(d, step)
	local r = d % step
	if r > step * 0.5 then r = r - step end
	return r
end

-- ============================================================ the ring that is there

local ring
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "18" and d:IsA("Folder") and #d:GetChildren() > 5 then
		ring = d
	end
end
if not ring then
	return "could not find the 18-side ring -- nothing to measure against, refusing to report"
end
say("ring: %s  (%d children)", ring:GetFullName(), #ring:GetChildren())

local center = CENTRE
local panels, plate = {}, nil
for _, d in ipairs(ring:GetChildren()) do
	if d:IsA("UnionOperation") then
		plate = d
	elseif d:IsA("BasePart") then
		panels[#panels + 1] = d
	end
end
say("  %d plain panels + %s", #panels, plate and ("1 " .. plate.ClassName) or "NO PLATE")

-- two estimates per panel: where its centre sits, and which way its face points
local byPos, byFace = {}, {}
for _, p in ipairs(panels) do
	local flat = Vector3.new(p.Position.X - center.X, 0, p.Position.Z - center.Z)
	byPos[#byPos + 1] = azim(flat)
	local z = p.CFrame.ZVector
	byFace[#byFace + 1] = azim(Vector3.new(z.X, 0, z.Z))
end
table.sort(byPos)
table.sort(byFace)

local step18 = 360 / 18
say("")
say("---- the ring's 18 panels, azimuth of Position (deg, sorted) ----")
for i, a in ipairs(byPos) do
	say("  %2d  %10.4f   offGrid %+8.4f", i, a, offGrid(a, step18))
end
say("")
say("---- the same 18 panels, azimuth of CFrame.ZVector ----")
for i, a in ipairs(byFace) do
	say("  %2d  %10.4f   offGrid %+8.4f", i, a, offGrid(a, step18))
end

-- ============================================================ the surface itself

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.FilterDescendantsInstances = {}
params.IgnoreWater = true

-- Only the ring, so the profile is the ring's own silhouette and not the wall's.
params.FilterType = Enum.RaycastFilterType.Include
params.FilterDescendantsInstances = { ring }

local N = math.floor(360 / STEP_DEG)
local r, az = {}, {}
for k = 0, N - 1 do
	local th = math.rad(k * STEP_DEG)
	local dir = Vector3.new(math.cos(th), 0, math.sin(th))
	local o = Vector3.new(center.X + dir.X * R_OUT, 47.075, center.Z + dir.Z * R_OUT)
	local hit = workspace:Raycast(o, -dir * (R_OUT * 2), params)
	az[k] = math.deg(th)
	r[k] = hit and (hit.Position - Vector3.new(center.X, 47.075, center.Z)).Magnitude or nil
end

local miss, rmin, rmax = 0, math.huge, 0
for k = 0, N - 1 do
	if not r[k] then
		miss += 1
	else
		rmin = math.min(rmin, r[k])
		rmax = math.max(rmax, r[k])
	end
end
say("")
say("---- 720-ray sweep at y 47.075, ring only ----")
if miss > 0 then
	say("  MISSES: %d of %d -- the profile is not closed, the numbers below are partial", miss, N)
end
say("  rmin %.4f  rmax %.4f  (circumradius vs apothem: ratio %.6f, cos(pi/18) = %.6f)",
	rmin, rmax, rmax / rmin, math.cos(math.pi / 18))

local maxAz, minAz = {}, {}
for k = 0, N - 1 do
	local pm, nm = (k - 1) % N, (k + 1) % N
	if r[k] and r[pm] and r[nm] then
		if r[k] > r[pm] and r[k] > r[nm] then maxAz[#maxAz + 1] = az[k] end
		if r[k] < r[pm] and r[k] < r[nm] then minAz[#minAz + 1] = az[k] end
	end
end
say("  local maxima (vertices): %d   local minima (face centres): %d", #maxAz, #minAz)
say("  vertex azimuths mod %.1f:", step18)
for _, a in ipairs(maxAz) do say("    %10.4f  offGrid %+8.4f", a, offGrid(a, step18)) end
say("  face-centre azimuths mod %.1f:", step18)
for _, a in ipairs(minAz) do say("    %10.4f  offGrid %+8.4f", a, offGrid(a, step18)) end

-- ============================================================ what I built

local model
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "ChamberWall24" and d:IsA("Model") then model = d end
end
if not model then
	say("")
	say("no Model named ChamberWall24 in the world -- nothing of mine to compare")
	return table.concat(out, string.char(10))
end
say("")
say("mine: %s  (%d children)", model:GetFullName(), #model:GetChildren())

local groups = {}
for _, p in ipairs(model:GetChildren()) do
	if p:IsA("BasePart") then
		local key = (string.match(p.Name, "^%a+")) or "?"
		groups[key] = groups[key] or {}
		local c = p.CFrame * Vector3.new(0, 0, p.Size.Z * 0.5)   -- local +Z is outward
		local flat = Vector3.new(c.X - center.X, 0, c.Z - center.Z)
		local t = groups[key]
		t[#t + 1] = { name = p.Name, az = azim(flat), rad = flat.Magnitude, y = c.Y }
	end
end

local order = { "Collar", "Band", "Wall" }
for _, key in ipairs(order) do
	local t = groups[key]
	if not t then
		say("  (no %s parts)", key)
	else
		local n = #t
		local step = 360 / n
		table.sort(t, function(a, b) return a.az < b.az end)
		local rmin2, rmax2 = math.huge, 0
		for _, e in ipairs(t) do
			rmin2 = math.min(rmin2, e.rad)
			rmax2 = math.max(rmax2, e.rad)
		end
		say("")
		say("---- %s: %d panels, outer-face radius %.4f .. %.4f, own step %.4f deg",
			key, n, rmin2, rmax2, step)
		for _, e in ipairs(t) do
			say("  %-10s az %10.4f  r %9.4f  y %8.4f  spacing %+8.4f",
				e.name, e.az, e.rad, e.y, offGrid(e.az - t[1].az, step))
		end
	end
end

-- ============================================================ the join

-- The collar and the wall are joined by DIFFERENT relations, and asking one group the
-- other group's question is exactly how a half step hid for a whole phase. The collar
-- is a continuation of the ring, so its FACES belong on the ring's faces. The wall is a
-- 4/3 refinement of it, so its VERTICES belong on the ring's vertices -- and only every
-- third ring vertex can carry one, because 3 * 20 = 4 * 15 = 60.
if #byPos > 0 then
	local ringFace = byPos[1]
	local collar, band, wall = groups.Collar, groups.Band, groups.Wall

	local ringVertex = ringFace
	do
		local best
		for _, a in ipairs(maxAz) do
			local d = offGrid(a - ringFace, step18)
			if not best or math.abs(d) < math.abs(best) then best = d end
		end
		ringVertex = ringFace + (best or step18 * 0.5)
	end

	say("")
	say("---- the join ----")
	say("  ring: faces at %.4f, vertices at %.4f (every %.1f deg)",
		ringFace, ringVertex, step18)

	if collar then
		local worst = 0
		for _, e in ipairs(collar) do
			worst = math.max(worst, math.abs(offGrid(e.az - ringFace, step18)))
		end
		say("  collar FACES vs the ring's faces: worst %.4f deg  (0 = joined, 10 = half a step out)",
			worst)
	end

	if wall then
		-- A wall face centre sits half a wall-step from a wall vertex.
		local wallV = wall[1].az + 180 / #wall
		local coincide, worstOff = 0, 0
		for _, a in ipairs(maxAz) do
			local d = offGrid(a - wallV, 360 / #wall)
			if math.abs(d) < 0.01 then
				coincide += 1
			else
				worstOff = math.max(worstOff, math.abs(d))
			end
		end
		say("  wall VERTICES vs the ring's vertices: %d of the ring's 18 carry one (18/3 = 6 by the 4/3 rule)",
			coincide)
		say("    the other %d ring vertices have no wall vertex, nearest is %.4f deg away -- expected, not a gap",
			18 - coincide, worstOff)
	end

	-- The operator's own statement of the join, counted rather than derived: from one
	-- ring vertex to the next (60 deg = 3 ring panels) there are 3 collar panels and 4
	-- wall panels. This is the number that is wrong when the phase is wrong.
	local function countIn(t, from, span)
		local c = 0
		for _, e in ipairs(t) do
			if ((e.az - from) % 360) < span then c += 1 end
		end
		return c
	end
	if collar and wall then
		say("  one 60 deg sector, ring vertex to ring vertex:")
		say("    collar panels %d (3 by the rule)   wall panels %d (4 by the rule, 18 * 4/3 = 24)",
			countIn(collar, ringVertex, 60), countIn(wall, ringVertex, 60))
	end
end

return table.concat(out, string.char(10))
