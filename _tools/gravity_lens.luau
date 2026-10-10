-- ==== GravityLens -- an EditableMesh gravitational lens ====
--
-- What this is: a polar sheet of triangles whose vertex COLOURS carry a lensed
-- nebula and whose vertex POSITIONS are rewritten every frame. The operator
-- asked for the dynamic part to be the vertex edits themselves, so the motion is
-- not a CFrame spin and not a UV scroll: every vertex is re-placed by the lens
-- map on each pass while its colour stays welded to it. That is what makes the
-- swirl legible -- the pattern moves because the mesh it is painted on moves.
--
-- Three rules this file keeps on purpose:
--   * it never writes to the camera. The lens is placed once and left there.
--   * zero backslashes. The Studio editing layer escape-decodes text that
--     travels through a tool call, so one backslash can arrive as a different,
--     broken program (CLAUDE.md 0.10). The gate checks for it.
--   * no Luau-only syntax, so the same bytes parse under stock Lua 5.1 and can be
--     gated by a real parser before they are ever shipped.
--
-- The EditableMesh API in this Studio is the OLD, indirection-based one. Measured,
-- not read off a doc page:
--   AddVertex(Vector3) -> vertexId
--   AddTriangle(v1, v2, v3) -> faceId
--   GetFaceColors(faceId) -> {colorId, colorId, colorId}   (one slot per VERTEX)
--   SetColor(colorId, Color3)          -- keyed by colour id, NOT by Color3
--   SetPosition(vertexId, Vector3)     -- local object space, rendering follows
--   SetVertexColor / SetVertexPosition / RemoveVertex / GetTriangles: absent.
-- A vertex keeps ONE colour slot across every face that uses it, but the id is
-- handed out at first use in face order, so it cannot be computed in advance --
-- it has to be read back while the faces are being added. build() does exactly
-- that and counts any vertex whose slot disagrees, so the assumption is checked
-- rather than assumed (CLAUDE.md 0.18: a wrong assumption does not error, it
-- quietly gives you a number).

local AssetService = game:GetService("AssetService")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")

local NL = string.char(10)

local M = {}
M.TAG = "lens-a1"

-- Measured ceilings. Named so the build can fail on a NUMBER rather than on the
-- engine's own phrasing -- "Triangle count above limit" arrives from deep inside
-- a half-finished loop and says nothing about which knob to turn.
local CAP_VERTICES = 60000
local CAP_TRIANGLES = 20000

local CFG = {
	-- ---- topology. Both ceilings below were MEASURED on this Studio, not read
	-- off a doc page: AddVertex stopped at 60000 with "Vertex count above limit",
	-- and AddTriangle stopped at 20000 with "Triangle count above limit". The
	-- second one is the binding constraint here, forty times over.
	-- 64 * 152 = 9728 vertices and 63 * 152 * 2 = 19152 triangles, which leaves
	-- 848 triangles of headroom under the cap.
	RINGS = 64,
	SPOKES = 152,

	-- ---- geometry, in studs
	R_MAX = 46,
	RADIAL_EXP = 1.55,   -- R = R_MAX * (i/RINGS) ^ EXP: dense at the centre, where
	                     -- the lens map compresses everything into a few studs
	DIP_DEPTH = 11,      -- how far the sheet dives into the throat
	DIP_RADIUS = 0.26,   -- normalised radius at which the dive is half done

	-- ---- the lens itself, in units of R_MAX
	R_SHADOW = 0.30,     -- inside this the sheet is black: the silhouette
	R_EINSTEIN = 0.52,   -- the radius every ray converges on
	RING_BOOST = 2.4,    -- extra brightness baked onto the photon ring
	RING_WIDTH = 0.012,
	R_VIGNETTE = 0.86,   -- colours fade from here to the rim, so the circular
	                     -- boundary of the sheet does not read as a disc edge
	FADE_IN = 0.055,

	-- ---- motion. Amplitudes are fractions of R_MAX; the ripple is in studs.
	SWIRL = 0.30,        -- peak extra azimuth, near the throat, of frame dragging
	SWIRL_PERIOD = 23,
	BREATHE = 0.045,     -- radial breathing, so rings cross the Einstein radius
	BREATHE_PERIOD = 11,
	RIPPLE = 1.5,        -- out-of-plane wave through the sheet
	RIPPLE_PERIOD = 7,
	UPDATE_HZ = 30,      -- 13824 SetPosition calls per pass; 30 Hz is cheap enough
	                     -- and 60 Hz of full-mesh rewrites is not free

	-- ---- where it sits. Derive it, do not invent it: while building this, the
	-- operator's edit camera was at (-115.80, 7.70, 4.84), so ORIGIN is 75 studs
	-- ahead of that on the level, at y = 58 -- high enough that the 46-stud sheet
	-- clears the baseplate at y = 0 with 12 studs to spare, and never buried in
	-- it. FACING is the unit vector from the sheet back toward that camera, so the
	-- disc is presented face-on. Both were computed from a READ of the camera.
	-- Nothing here ever writes to it.
	ORIGIN = Vector3.new(-151.1, 58.0, 71.0),
	FACING = Vector3.new(0.4099, -0.4912, -0.7686),
}
M.CFG = CFG

-- ========== SMALL MATHS ==========

local function clamp01(x)
	if x < 0 then return 0 end
	if x > 1 then return 1 end
	return x
end

local function smoothstep(edge0, edge1, x)
	local t = clamp01((x - edge0) / (edge1 - edge0))
	return t * t * (3 - 2 * t)
end

-- A hash that needs nothing but doubles. math.sin of a large multiple of a
-- constant is chaotic enough for decoration; it is not a PRNG and is not used as
-- one, so it does not matter that it is not one.
local function hash01(a, b, seed)
	local v = math.sin(a * 127.1 + b * 311.7 + seed * 74.7) * 43758.5453123
	return v - math.floor(v)
end

local function valueNoise(x, y, seed)
	local xi = math.floor(x)
	local yi = math.floor(y)
	local xf = x - xi
	local yf = y - yi
	local u = xf * xf * (3 - 2 * xf)
	local v = yf * yf * (3 - 2 * yf)
	local a = hash01(xi, yi, seed)
	local b = hash01(xi + 1, yi, seed)
	local c = hash01(xi, yi + 1, seed)
	local d = hash01(xi + 1, yi + 1, seed)
	local ab = a + (b - a) * u
	local cd = c + (d - c) * u
	return ab + (cd - ab) * v
end

-- ========== THE SOURCE PLANE ==========
-- The source plane is what you would see with no hole in the way. The lens maps
-- an observed radius R to a source radius
--     beta = R - rE^2 / R
-- which is the point-mass lens equation. beta goes NEGATIVE inside the ring, and
-- that is not a bug: it is the second image, mirrored through the centre. Rays
-- at R == rE all land on beta == 0, which is why the ring carries the colour of
-- exactly one source point -- so a bright core is put there on purpose.

local function blobColour(h)
	if h < 0.45 then
		return 0.55 + 0.45 * h, 0.72 + 0.28 * h, 1.0
	elseif h < 0.8 then
		local k = (h - 0.45) / 0.35
		return 1.0, 0.72 - 0.20 * k, 0.45 + 0.20 * k
	end
	return 1.0, 0.55, 0.85
end

-- Bright knots in the source plane. These are what smear into arcs: a round blob
-- of radius 0.03 source units is several vertices wide over most of the sheet, so
-- unlike a point star it survives being painted with vertex colours and cannot
-- alias into flicker when the sheet rotates.
local BLOBS = {}
do
	local k
	for k = 1, 14 do
		local ang = hash01(k, 1, 3.7) * 6.283185
		local rad = 0.10 + 0.62 * hash01(k, 2, 5.1)
		BLOBS[k] = {
			x = rad * math.cos(ang),
			y = rad * math.sin(ang),
			r = 0.030 + 0.055 * hash01(k, 3, 8.3),
			h = hash01(k, 4, 1.9),
			b = 0.55 + 0.75 * hash01(k, 5, 2.3),
		}
	end
end

local function sourceColour(sx, sy)
	local n = 0.50 * valueNoise(sx * 3.0, sy * 3.0, 11)
		+ 0.28 * valueNoise(sx * 7.0, sy * 7.0, 23)
		+ 0.16 * valueNoise(sx * 15.0, sy * 15.0, 37)
		+ 0.06 * valueNoise(sx * 31.0, sy * 31.0, 53)
	-- Ridged noise: turning a smooth field into its distance from the middle gives
	-- seams instead of blobs, which is what turns a cloud into a nebula.
	local fil = valueNoise(sx * 5.0, sy * 5.0, 71)
	fil = 1 - math.abs(2 * fil - 1)
	fil = fil * fil * fil

	local r, g, b
	if n < 0.45 then
		local k = n / 0.45
		r = 0.030 + 0.100 * k
		g = 0.045 + 0.090 * k
		b = 0.140 + 0.220 * k
	elseif n < 0.72 then
		local k = (n - 0.45) / 0.27
		r = 0.130 + 0.440 * k
		g = 0.135 + 0.020 * k
		b = 0.360 + 0.050 * k
	else
		local k = (n - 0.72) / 0.28
		r = 0.570 + 0.430 * k
		g = 0.155 + 0.360 * k
		b = 0.410 + 0.260 * k
	end
	r = r + 0.10 * fil
	g = g + 0.55 * fil
	b = b + 0.65 * fil

	local k
	for k = 1, #BLOBS do
		local bl = BLOBS[k]
		local dx = sx - bl.x
		local dy = sy - bl.y
		local q = (dx * dx + dy * dy) / (bl.r * bl.r)
		if q < 6 then
			local w = math.exp(-q) * bl.b
			local br, bg, bb = blobColour(bl.h)
			r = r + br * w
			g = g + bg * w
			b = b + bb * w
		end
	end

	local core = math.exp(-(sx * sx + sy * sy) / 0.0012)
	r = r + 1.15 * core
	g = g + 1.12 * core
	b = b + 1.05 * core
	return r, g, b
end

-- The colour a vertex carries, given its OBSERVED radius R and azimuth phi.
-- Colours are baked once at build time and never touched again; the motion is
-- entirely in the positions.
local function vertexColour(R, phi)
	if R <= CFG.R_SHADOW then
		return 0, 0, 0
	end
	local rE = CFG.R_EINSTEIN
	local beta = R - (rE * rE) / R
	local r, g, b = sourceColour(beta * math.cos(phi), beta * math.sin(phi))

	local ring = math.exp(-((R - rE) / CFG.RING_WIDTH) ^ 2)
	local boost = 1 + CFG.RING_BOOST * ring
	r = r * boost
	g = g * boost
	b = b * boost

	local fade = smoothstep(0, CFG.FADE_IN, R) * (1 - smoothstep(CFG.R_VIGNETTE, 1, R))
	return r * fade, g * fade, b * fade
end

-- ========== BUILD ==========

local function build()
	local rings = CFG.RINGS
	local spokes = CFG.SPOKES

	local wantVerts = rings * spokes
	local wantTris = (rings - 1) * spokes * 2
	if wantVerts > CAP_VERTICES then
		error(string.format("topology asks for %d vertices, the cap is %d",
			wantVerts, CAP_VERTICES))
	end
	if wantTris > CAP_TRIANGLES then
		error(string.format("topology asks for %d triangles, the cap is %d",
			wantTris, CAP_TRIANGLES))
	end

	local em = AssetService:CreateEditableMesh()

	local verts = {}
	local rn = {}
	local rad = {}
	local dip = {}
	local phi = {}
	local cosv = {}
	local sinv = {}

	local i, j
	for j = 1, spokes do
		local a = (j - 1) * 2 * math.pi / spokes
		phi[j] = a
		cosv[j] = math.cos(a)
		sinv[j] = math.sin(a)
	end

	for i = 1, rings do
		local t = i / rings
		local u = t ^ CFG.RADIAL_EXP
		rn[i] = u
		rad[i] = u * CFG.R_MAX
		dip[i] = -CFG.DIP_DEPTH * (CFG.DIP_RADIUS ^ 2) / (CFG.DIP_RADIUS ^ 2 + u * u)
		local R = rad[i]
		local z = dip[i]
		local row = {}
		for j = 1, spokes do
			row[j] = em:AddVertex(Vector3.new(R * cosv[j], R * sinv[j], z))
		end
		verts[i] = row
	end

	-- Colour slots come back one per vertex, allocated at first use, so they are
	-- harvested here while the faces go in. conflicts counts the case where the
	-- same vertex is reported with two different slots, which would mean the slot
	-- is per face-corner after all and the whole colour pass is wrong.
	local colourOf = {}
	local conflicts = 0
	local faces = 0

	local function link(a, b, c)
		local f = em:AddTriangle(a, b, c)
		faces = faces + 1
		local cols = em:GetFaceColors(f)
		local vs = { a, b, c }
		local k
		for k = 1, 3 do
			local prev = colourOf[vs[k]]
			if prev == nil then
				colourOf[vs[k]] = cols[k]
			elseif prev ~= cols[k] then
				conflicts = conflicts + 1
			end
		end
	end

	for i = 1, rings - 1 do
		for j = 1, spokes do
			local jn = j % spokes + 1
			link(verts[i][j], verts[i + 1][j], verts[i + 1][jn])
			link(verts[i][j], verts[i + 1][jn], verts[i][jn])
		end
	end

	local coloured = 0
	for i = 1, rings do
		for j = 1, spokes do
			local r, g, b = vertexColour(rn[i], phi[j])
			local cid = colourOf[verts[i][j]]
			if cid ~= nil then
				em:SetColor(cid, Color3.new(clamp01(r), clamp01(g), clamp01(b)))
				coloured = coloured + 1
			end
		end
	end

	local ok, partOrErr = pcall(function()
		return AssetService:CreateMeshPartAsync(Content.fromObject(em))
	end)
	if not ok then
		em:Destroy()
		error("CreateMeshPartAsync refused the sheet: " .. tostring(partOrErr))
	end
	local part = partOrErr

	part.Name = "GravityLens"
	part.Anchored = true
	part.Material = Enum.Material.Neon
	part.Color = Color3.new(1, 1, 1)
	part.CFrame = CFrame.lookAt(CFG.ORIGIN, CFG.ORIGIN - CFG.FACING.Unit)
	-- The sheet is a surface, not a wall: it must not collide, must not be hit by
	-- rays, and must not cast a shadow onto the operator's facility. Only the
	-- appearance is wanted; everything else would be a side effect on the world.
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	pcall(function() part.DoubleSided = true end)

	local old = workspace:FindFirstChild("GravityLens")
	if old ~= nil then
		old:Destroy()
	end
	part.Parent = workspace

	local state = {
		em = em,
		part = part,
		verts = verts,
		colourOf = colourOf,
		rn = rn,
		rad = rad,
		dip = dip,
		phi = phi,
		cosv = cosv,
		sinv = sinv,
		rings = rings,
		spokes = spokes,
		clock = 0,
		last = -1,
		passes = 0,
		stats = {
			vertices = rings * spokes,
			faces = faces,
			coloured = coloured,
			colourConflicts = conflicts,
			unmapped = rings * spokes - coloured,
		},
	}
	return state
end

M.build = build

-- ========== THE MOTION ==========
-- Every vertex is placed by three motions, all of which are the vertex moving,
-- not the pattern changing:
--   drag    the sheet is rotated hardest nearest the throat -- frame dragging.
--           The colours ride along, so the nebula visibly shears into arcs.
--   breathe a radial wave travelling outward, so rings cross the Einstein ring
--           and the ring thickens and thins.
--   ripple  a wave out of the plane, which shows in the silhouette.
-- Both waves are sin of a phase, not a linearly growing angle: a constantly
-- growing shear would wind the sheet into infinitely fine spirals, which is the
-- winding problem, not a look.

function M.step(state, dt)
	state.clock = state.clock + dt
	if state.clock - state.last < 1 / CFG.UPDATE_HZ then
		return 0
	end
	state.last = state.clock
	local t = state.clock

	local swirl = CFG.SWIRL * math.sin(2 * math.pi * t / CFG.SWIRL_PERIOD)
	local bPhase = 2 * math.pi * t / CFG.BREATHE_PERIOD
	local rPhase = 2 * math.pi * t / CFG.RIPPLE_PERIOD
	local rE = CFG.R_EINSTEIN

	local em = state.em
	local cosv = state.cosv
	local sinv = state.sinv
	local moved = 0
	local i, j

	for i = 1, state.rings do
		local u = state.rn[i]
		local drag = (rE / (rE + u)) ^ 1.5
		local d = swirl * drag
		local cd = math.cos(d)
		local sd = math.sin(d)

		local ramp = smoothstep(0, 0.10, u) * (1 - smoothstep(0.80, 1.0, u))
		local rr = state.rad[i] * (1 + CFG.BREATHE * ramp * math.sin(bPhase - 2.6 * u))
		local zz = state.dip[i] + CFG.RIPPLE * ramp * math.sin(rPhase - 3.2 * u)

		local row = state.verts[i]
		for j = 1, state.spokes do
			local c = cosv[j] * cd - sinv[j] * sd
			local s = sinv[j] * cd + cosv[j] * sd
			em:SetPosition(row[j], Vector3.new(rr * c, rr * s, zz))
			moved = moved + 1
		end
	end
	state.passes = state.passes + 1
	return moved
end

-- ========== SELF-CHECKS AND PICTURES ==========

-- The mesh stores what it was given, or it does not. This walks the round trip
-- that docs/SNIPPETS.md 5.18 names as the only trustworthy read-back: MeshContent
-- back into a fresh EditableMesh, then read positions and colours off it. It is a
-- round trip rather than a self-report, so it can disagree with the build.
function M.verify(state)
	local out = { tag = M.TAG }
	local ok, back = pcall(function()
		return AssetService:CreateEditableMeshAsync(state.part.MeshContent)
	end)
	if not ok then
		out.roundTrip = "refused: " .. tostring(back)
		return out
	end
	out.roundTrip = "ok"
	local n = 0
	local i, j
	local worstPos = 0
	for i = 1, state.rings, 17 do
		for j = 1, state.spokes, 29 do
			local vid = state.verts[i][j]
			local p = back:GetPosition(vid)
			local want = state.em:GetPosition(vid)
			local d = (p - want).Magnitude
			if d > worstPos then worstPos = d end
			n = n + 1
		end
	end
	out.sampled = n
	out.worstPositionDelta = worstPos

	local cols = back:GetFaceColors(back:GetFaces()[1])
	out.colourSlotsOnFirstFace = #cols

	-- Colours are checked by VALUE on rings that actually carry one. Sampling the
	-- innermost ring would have compared black against black -- a check that
	-- cannot fail is not a check, and it would have reported a perfect pass for a
	-- mesh with no colours on it at all.
	local worstCol = 0
	local checked = 0
	local brightest = 0
	for i = 1, state.rings, 5 do
		local vid = state.verts[i][1]
		local cid = state.colourOf[vid]
		if cid ~= nil then
			local got = back:GetColor(cid)
			local wr, wg, wb = vertexColour(state.rn[i], state.phi[1])
			local dr = math.abs(got.R - clamp01(wr))
			local dg = math.abs(got.G - clamp01(wg))
			local db = math.abs(got.B - clamp01(wb))
			local d = math.max(dr, math.max(dg, db))
			if d > worstCol then worstCol = d end
			local lum = clamp01(wr) + clamp01(wg) + clamp01(wb)
			if lum > brightest then brightest = lum end
			checked = checked + 1
		end
	end
	out.colourChecked = checked
	out.worstColourDelta = worstCol
	out.brightestSample = brightest
	back:Destroy()
	return out
end

-- Renders the COLOUR field to an ASCII PPM and POSTs it to a local sink, so the
-- picture can be looked at without going anywhere near the operator's camera and
-- without megabytes of text crossing the tool boundary. Sampling the colour
-- field is the honest check for "does this read as a lens": the geometry is where
-- the motion lives, the colour is where the lens image lives.
function M.pushPPM(url, n)
	n = n or 220
	local rows = { "P3", tostring(n) .. " " .. tostring(n), "255" }
	local py, px
	for py = 1, n do
		local row = {}
		for px = 1, n do
			local ux = (px - 0.5) / n * 2 - 1
			local uy = (py - 0.5) / n * 2 - 1
			local r, g, b = 0, 0, 0
			local rr = math.sqrt(ux * ux + uy * uy)
			if rr <= 1 then
				r, g, b = vertexColour(rr, math.atan2(uy, ux))
			end
			row[#row + 1] = string.format("%d %d %d ",
				math.floor(clamp01(r) * 255 + 0.5),
				math.floor(clamp01(g) * 255 + 0.5),
				math.floor(clamp01(b) * 255 + 0.5))
		end
		rows[#rows + 1] = table.concat(row)
	end
	local body = table.concat(rows, NL)
	local ok, err = pcall(function()
		HttpService:PostAsync(url, body)
	end)
	return ok, err, #body
end

-- ========== START ==========
-- In Play this builds and animates. In Edit it only builds, because there is no
-- simulation to hang an animation on -- so requiring this file from the edit
-- sandbox is also how the still frame gets placed.
--
-- The boot is wrapped and its failure is recorded rather than thrown. A module
-- that throws is reported by its caller as "Requested module experienced an
-- error while loading", which names the CALLER and not the fault, and the real
-- message is then nowhere -- a script that dies must say why (CLAUDE.md 0.17).

local bootOk, bootErr = pcall(function()
	local s = build()
	M.state = s
	if RunService:IsRunning() then
		M.conn = RunService.Heartbeat:Connect(function(dt)
			M.step(s, dt)
		end)
	end
end)
if not bootOk then
	M.bootError = tostring(bootErr)
	warn("[GravityLens] " .. M.TAG .. " boot failed: " .. M.bootError)
end

return M
