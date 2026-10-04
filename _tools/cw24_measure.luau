-- cw24_measure.luau -- READ ONLY probe of the 18-sided platform rim in [Rebuild].
--
-- Why this runs at all: the Blender build asserts its input (apothem 63.712, a
-- VERTEX on +X, platform top y = 47.400) and refuses to guess. Those three
-- numbers were measured in this place last session. This script re-takes the
-- measurement from the live DataModel BEFORE anything is built, so the build is
-- guarded by a reading rather than by a memory -- and so that a moved ring is a
-- refusal, not a wall that lands 3 studs off (CLAUDE.md 0.18: a wrong ruler does
-- not error, it answers confidently).
--
-- It creates nothing, moves nothing, writes no property. Everything it learns, it
-- prints.

local HINT = Vector3.new(-12.200, 47.400, -85.362)

-- ============================================================ locate

-- Workspace has more than one thing named like a folder; and FindFirstChild is
-- not a path here (CLAUDE.md 0.14). So: enumerate every Folder/Model named "18"
-- with a plausible number of part children and take the one nearest the hint.
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
					best = { inst = d, parts = parts, mean = p, dist = dist }
				end
			end
		end
	end
	return best
end

local ring = findRing()
if not ring then
	warn("CW24 no 18-ring found anywhere in Workspace")
	return
end

print(string.format("CW24 ring %s  parts %d  distFromHint %.3f",
	ring.inst:GetFullName(), #ring.parts, ring.dist))
print(string.format("CW24 mean of part positions  %.4f %.4f %.4f",
	ring.mean.X, ring.mean.Y, ring.mean.Z))

-- ============================================================ parts

local lo = Vector3.new(math.huge, math.huge, math.huge)
local hi = Vector3.new(-math.huge, -math.huge, -math.huge)
for i, p in ipairs(ring.parts) do
	lo = Vector3.new(math.min(lo.X, p.Position.X - p.Size.X * 0.5),
		math.min(lo.Y, p.Position.Y - p.Size.Y * 0.5),
		math.min(lo.Z, p.Position.Z - p.Size.Z * 0.5))
	hi = Vector3.new(math.max(hi.X, p.Position.X + p.Size.X * 0.5),
		math.max(hi.Y, p.Position.Y + p.Size.Y * 0.5),
		math.max(hi.Z, p.Position.Z + p.Size.Z * 0.5))
	print(string.format("CW24 part %2d %-28s %-9s size %8.3f %7.3f %8.3f  pos %9.3f %8.3f %9.3f",
		i, p.Name, p.ClassName, p.Size.X, p.Size.Y, p.Size.Z,
		p.Position.X, p.Position.Y, p.Position.Z))
end
-- NOTE: this bbox is Position +/- Size/2, which is only correct for an unrotated
-- part. It is reported as a sanity envelope, NOT used as a measurement -- a
-- rotated part makes this number confidently wrong (CLAUDE.md 0.18).
print(string.format("CW24 axis-aligned envelope  X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f",
	lo.X, hi.X, lo.Y, hi.Y, lo.Z, hi.Z))

-- ============================================================ centre

-- The panels of a regular ring are equally spaced, so their mean IS the centre
-- exactly (the sum of the unit vectors cancels). Anything that is not one of the
-- repeated panels would bias that mean, so the majority size wins and the
-- outliers are named rather than silently averaged in.
local groups = {}
for _, p in ipairs(ring.parts) do
	local key = string.format("%.3f|%.3f|%.3f", p.Size.X, p.Size.Y, p.Size.Z)
	groups[key] = groups[key] or {}
	table.insert(groups[key], p)
end
local topKey, topList = nil, {}
for k, v in pairs(groups) do
	if #v > #topList then
		topKey, topList = k, v
	end
end

local sum = Vector3.new(0, 0, 0)
for _, p in ipairs(topList) do
	sum = sum + p.Position
end
local centre = sum / #topList

print(string.format("CW24 majority size %s  count %d  (of %d parts)",
	topKey, #topList, #ring.parts))
for k, v in pairs(groups) do
	if k ~= topKey then
		print(string.format("CW24 outlier group %s  count %d", k, #v))
	end
end
print(string.format("CW24 CENTRE from majority mean  %.4f %.4f %.4f", centre.X, centre.Y, centre.Z))
print(string.format("CW24 delta vs hint  %.4f %.4f %.4f",
	centre.X - HINT.X, centre.Y - HINT.Y, centre.Z - HINT.Z))

-- ============================================================ radial probe

-- 720 inward raycasts on a circle of radius 90, at the ring's own mid height, so
-- the number that comes out is the surface a neighbour would actually touch --
-- not a number derived from Size, which is a local-axis quantity and lies about
-- rotated parts.
local PROBE_R = 90
local probeY = (lo.Y + hi.Y) * 0.5
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Include
params.FilterDescendantsInstances = { ring.inst }
params.IgnoreWater = true

local N = 720
local rmin, rmax, rminAt, rmaxAt = math.huge, -math.huge, 0, 0
local misses, samples = 0, {}
for k = 0, N - 1 do
	local th = 2 * math.pi * k / N
	local dir = Vector3.new(math.cos(th), 0, math.sin(th))
	local origin = Vector3.new(centre.X + PROBE_R * dir.X, probeY, centre.Z + PROBE_R * dir.Z)
	local hit = workspace:Raycast(origin, -dir * (PROBE_R * 2), params)
	if hit then
		local r = PROBE_R - hit.Distance
		samples[k] = r
		if r < rmin then rmin, rminAt = r, k end
		if r > rmax then rmax, rmaxAt = r, k end
	else
		misses = misses + 1
	end
end

print(string.format("CW24 probe at y=%.3f over %d rays: misses=%d", probeY, N, misses))
print(string.format("CW24 rmin %.4f at %.2f deg   rmax %.4f at %.2f deg   span %.4f",
	rmin, rminAt * 0.5, rmax, rmaxAt * 0.5, rmax - rmin))
print(string.format("CW24 rmax / rmin = %.5f   (cos(10 deg) = %.5f -> the max sits on a CORNER)",
	rmax / rmin, math.cos(math.rad(10))))

-- Where the profile breaks. On an 18-gon with a vertex on +X the radius is
-- extremal at 0, 20, 40 ... (corners) and minimal at 10, 30, 50 ... (side
-- midpoints), so a run of |dr| large enough to see should land on those.
local breaks = {}
for k = 0, N - 1 do
	local a, b = samples[(k - 1) % N], samples[k]
	if a and b and math.abs(b - a) > 0.02 then
		breaks[#breaks + 1] = string.format("%.2f", k * 0.5)
	end
end
print(string.format("CW24 profile breaks (deg): %s", table.concat(breaks, " ")))

print("CW24 MEASURE DONE")
