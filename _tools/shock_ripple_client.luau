--[[
	ShockRippleClient -- the shock disc, as one continuous sheet.

	The 12-ring version (ShockRipple.C1..C12) moves in 5-stud steps: twelve
	discrete lifts, which reads as steps and not as a wave. This one is a
	single editable mesh whose height is a function of radius, so the motion
	is continuous -- but the SHAPE is kept as it is drawn.

	TWO MOTIONS, chosen by the Motion attribute (both are kept; neither
	replaces the other):

	  "wave" (default) -- a crest is born at the middle and travels outward at
	    Speed studs per second, Width of a Period wide, and the next one
	    follows Period seconds behind it. This is the Phase 118 look.

	  "pulse" -- the whole sheet heaves up and down together. The height is
	    Amplitude * envelope(radius) * sin(2*pi*t/Period), so the middle swings
	    the full +/- Amplitude and the rim does not move at all. Speed and
	    Width are not used by this motion.

	BOTH MOTIONS RUN THROUGH THE SAME ENVELOPE, and the Falloff attribute is
	its exponent:

	    envelope(r) = (0.5*(1 + cos(pi*r/RADIUS))) ^ Falloff

	It is the raised cosine that gives 1 at the centre and EXACTLY 0 at the
	rim, with slope 0 at both ends, so neither the middle nor the edge shows a
	seam -- and raising a function to a power keeps the value and both slopes
	at 0, so no Falloff value can introduce a crease. The exponent is what
	decides HOW MUCH of the crest survives the trip out:

	  Falloff = 0  -- no decay at all: every crest crosses the whole disc at
	                  full height. This is exactly the Phase 118 wave, which is
	                  why it is still reachable rather than deleted.
	  Falloff = 1  -- a crest is half height at half the radius and gone at the
	                  rim (the standing default).
	  Falloff = 2  -- taller for longer near the middle, then drops away fast.

	The rim is mathematically still for every Falloff above 0, and exactly
	still, not nearly: cos(pi) is -1.0 to the last bit in double precision, so
	the base is 0.0 and 0.0^p is 0.0 for any p > 0. At Falloff = 0 the rim
	moves -- that is what "no decay" means, and it is the operator's choice to
	make.

	THE SHAPE IS AN 18-GON, and that is measured, not assumed. The disc
	(Cylinder2) has 54 vertices on its rim but only 18 distinct angles, 20.00
	degrees apart starting at 10 degrees, and the 18 Neon parts sit on those
	very corners at r = 59.78 while the corners themselves are at r = 60
	(the mesh rim is 100 units, scaled by 0.6). So this sheet keeps 18 flat
	wedges with hard corners, exactly like the art -- it is the MOTION that
	becomes continuous, not the outline. Every wedge has its own corner
	vertices so the edges stay crisp instead of being smoothed away.

	WHY IT RUNS ON THE CLIENT. A mesh built with Content.fromObject does not
	replicate: build it on the server and the server sees the real thing while
	every client gets a placeholder. So each client builds its own copy from
	the same numbers and animates it locally. That also means this script has
	to report on itself -- see the Diag section below.

	HOW THE SHEET GETS ON SCREEN. WRITING MeshContent IS NOT ALLOWED from a
	game script -- "the current thread cannot write 'MeshContent' (lacking
	capability NotAccessible)", measured on a fresh MeshPart as well as on the
	disc. AssetService:CreateMeshPartAsync is allowed, and the part it returns
	holds the EditableMesh itself, not a copy. So the mesh is moulded once,
	handed to a part, and every later frame only moves vertices in place.

	It touches nothing the server owns in any lasting way: the disc (Wave) is
	faded out on this client only while the wave runs, and hidden again when it
	stops. No gameplay state is read or written, and the original Cylinder2 is
	never touched.
]]

local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local AssetService = game:GetService("AssetService")

-- ========== FINDING IT ==========
-- By tag, not by path: this place has nine children of Workspace called
-- "Folder", so any path is a guess that works right up until the day it does
-- not. Both lookups RETRY instead of waiting once. The first version of this
-- script called WaitForChild("Wave", 15) and timed out, which means a client
-- can hold the rig while the world under it has not finished arriving (see
-- StreamingEnabled below) -- a single wait is a coin toss on load order.
local function waitForTagged(seconds)
	local deadline = os.clock() + seconds
	repeat
		local found = CollectionService:GetTagged("ShockRippleRig")[1]
		if found ~= nil then
			return found
		end
		task.wait(0.25)
	until os.clock() > deadline
	return nil
end

local rig = waitForTagged(20)
if rig == nil then
	warn("[ShockRipple] nothing is tagged ShockRippleRig after 20 seconds")
	return
end

-- ========== REPORT BACK ==========
-- There is no console to read inside a running game, so the script keeps its
-- own note on the rig and the editor reads that back. Without this, "it works"
-- and "the first frame threw" look exactly the same from outside. It is set up
-- before anything that can fail, so a failure has somewhere to be written.
local diag = rig:FindFirstChild("Diag")
if diag == nil then
	diag = Instance.new("StringValue")
	diag.Name = "Diag"
	diag.Parent = rig
end
local notes = {}
local function say(text)
	table.insert(notes, text)
	if #notes > 24 then
		-- streamed in and out over and over: keep the note readable
		table.remove(notes, 1)
	end
	diag.Value = table.concat(notes, " | ")
end
local function live(text)
	diag.Value = table.concat(notes, " | ") .. " || " .. text
end

say("rig=" .. rig:GetFullName())

-- The wait has NO deadline on purpose. The rig's tag and the rig's children
-- replicate separately, so a client can hold the rig while Wave is still on
-- its way -- the first version of this script waited 15 seconds, timed out and
-- gave up with the rig still empty. Waiting is the correct behaviour: there is
-- nothing to draw until Wave lands. Every 2 seconds the note says what is
-- still missing, so "never arrived" is readable from outside.
local part = nil
local waitedFrom = os.clock()
local reportedAt = waitedFrom
repeat
	part = rig:FindFirstChild("Wave")
	if part ~= nil and part:IsA("MeshPart") == false then
		say("Wave is a " .. part.ClassName .. ", not a MeshPart")
		return
	end
	if part == nil then
		local now = os.clock()
		if now - reportedAt >= 2 then
			reportedAt = now
			live(string.format("waiting %.1fs for Wave: the rig has %d children",
				now - waitedFrom, #rig:GetChildren()))
		end
		task.wait(0.25)
	end
until part ~= nil
say(string.format("found Wave after %.1fs", os.clock() - waitedFrom))

-- ========== TUNING ==========
-- Read every frame rather than once, so every knob can be turned while it runs.
local function number(name, fallback, minimum)
	local value = rig:GetAttribute(name)
	if typeof(value) ~= "number" then
		return fallback
	end
	return math.max(value, minimum)
end

local RADIUS = 60      -- studs: the 18 corners of the disc are at exactly 60,
                       -- and the 18 Neon parts sit just inside them at 59.78
local HALF = 0.125     -- half the slab's thickness: the disc it stands in for is
                       -- 0.25 studs thick, and the mesh is BORN that thick.
                       -- That matters beyond looks: MeshSize is a snapshot
                       -- taken when the part is created, and a mesh born flat
                       -- snapshots 0.001 in Y -- which the renderer then
                       -- stretches to whatever Size.Y is (measured: 250x).

local mesh = nil       -- the EditableMesh
local sheet = nil      -- the MeshPart this client built to draw "mesh"
local ids = nil        -- ids[layer][ring][wedge][corner]; layer 1 = top, 2 = bottom
local xz = nil         -- xz[ring][wedge][corner] = that slot's rest position
local heights = nil    -- heights[ring] = the height last written, to skip no-ops
local builtSegments, builtRings = -1, -1

-- ========== THE MESH ==========
-- A polar grid in wedges: a centre, then rings of corners out to RADIUS, two
-- layers (top and bottom) and a rim joining them, so it is a 0.25-stud slab
-- and does not disappear when seen edge-on.
local function build(segments, rings)
	local fresh = AssetService:CreateEditableMesh()
	if fresh == nil then
		return nil
	end

	local step = 2 * math.pi / segments
	local first = step / 2   -- the disc's corners are at 10 + 20k degrees, not at 0

	local freshIds = { {}, {} }
	local freshXZ = {}

	-- the centre: one vertex per wedge per layer, so the wedges meet in a hard
	-- point instead of a smooth fan
	freshXZ[0] = {}
	for wedge = 1, segments do
		freshXZ[0][wedge] = {}
		for corner = 1, 2 do
			freshXZ[0][wedge][corner] = Vector3.new(0, 0, 0)
		end
		for layer = 1, 2 do
			freshIds[layer][0] = freshIds[layer][0] or {}
			freshIds[layer][0][wedge] = {}
			local y = HALF
			if layer == 2 then
				y = -HALF
			end
			for corner = 1, 2 do
				freshIds[layer][0][wedge][corner] = fresh:AddVertex(Vector3.new(0, y, 0))
			end
		end
	end

	for ring = 1, rings do
		local radius = RADIUS * ring / rings
		freshXZ[ring] = {}
		for layer = 1, 2 do
			freshIds[layer][ring] = {}
		end
		for wedge = 1, segments do
			freshXZ[ring][wedge] = {}
			for layer = 1, 2 do
				freshIds[layer][ring][wedge] = {}
			end
			for corner = 1, 2 do
				-- corner 1 of wedge w is the same point as corner 2 of wedge
				-- w - 1, but it is a separate vertex: that is what keeps the
				-- edge between two wedges crisp
				local angle = first + step * (wedge + corner - 2)
				local p = Vector3.new(radius * math.cos(angle), 0, radius * math.sin(angle))
				freshXZ[ring][wedge][corner] = p
				for layer = 1, 2 do
					local y = HALF
					if layer == 2 then
						y = -HALF
					end
					freshIds[layer][ring][wedge][corner] = fresh:AddVertex(Vector3.new(p.X, y, p.Z))
				end
			end
		end
	end

	for wedge = 1, segments do
		-- the first ring out from the centre
		for layer = 1, 2 do
			local centre = freshIds[layer][0][wedge][1]
			local a = freshIds[layer][1][wedge][1]
			local b = freshIds[layer][1][wedge][2]
			if layer == 1 then
				fresh:AddTriangle(centre, a, b)
			else
				fresh:AddTriangle(centre, b, a)
			end
		end
		-- the face: two triangles per wedge for each gap between rings
		for ring = 1, rings - 1 do
			for layer = 1, 2 do
				local innerA = freshIds[layer][ring][wedge][1]
				local innerB = freshIds[layer][ring][wedge][2]
				local outerA = freshIds[layer][ring + 1][wedge][1]
				local outerB = freshIds[layer][ring + 1][wedge][2]
				if layer == 1 then
					fresh:AddTriangle(innerA, outerA, innerB)
					fresh:AddTriangle(innerB, outerA, outerB)
				else
					fresh:AddTriangle(innerA, innerB, outerA)
					fresh:AddTriangle(innerB, outerB, outerA)
				end
			end
		end
		-- the rim of this wedge
		local topA = freshIds[1][rings][wedge][1]
		local topB = freshIds[1][rings][wedge][2]
		local bottomA = freshIds[2][rings][wedge][1]
		local bottomB = freshIds[2][rings][wedge][2]
		fresh:AddTriangle(topA, bottomA, topB)
		fresh:AddTriangle(topB, bottomA, bottomB)
	end

	return fresh, freshIds, freshXZ
end

-- ========== THE PART ==========
-- Writing MeshContent from a game script does not work -- measured, and not
-- only on the disc: a brand new MeshPart refuses the same way, with "the
-- current thread cannot write 'MeshContent' (lacking capability
-- NotAccessible)". AssetService:CreateMeshPartAsync CAN be called, and the
-- part it returns holds the EditableMesh ITSELF rather than a copy: lifting
-- one vertex and reading the part's mesh back showed the lift. So the shape is
-- handed over once, at birth, and every later frame only moves vertices.
--
-- The part is built by this client and never leaves it. That is deliberate:
-- content built this way does not replicate, so a server-side copy would be a
-- placeholder on every screen that matters.
local function makeSheet(fresh)
	if part == nil or part.Parent == nil then
		-- The sheet is built in the disc's space and dressed as the disc, so
		-- while the disc is off the client there is nothing to build it FROM.
		-- This is a wait, not a failure: the disc comes back.
		live("makeSheet: no disc to stand in for at this moment")
		return nil
	end
	local ok, created = pcall(function()
		return AssetService:CreateMeshPartAsync(Content.fromObject(fresh))
	end)
	if ok == false or typeof(created) ~= "Instance" then
		say("CreateMeshPartAsync refused: " .. tostring(created))
		return nil
	end
	created.Name = "WaveSheet"
	created.Anchored = true
	created.Locked = true
	created.CanCollide = false
	created.CanQuery = false
	created.CanTouch = false
	created.CastShadow = false
	-- dressed as the disc it stands in for, so only the SHAPE changes: the
	-- original is ForceField material, white, double sided, 120 x 0.25 x 120
	created.Material = part.Material
	created.Color = part.Color
	created.Reflectance = part.Reflectance
	created.DoubleSided = part.DoubleSided
	-- Size == MeshSize is the identity mapping: one mesh unit is one stud, so
	-- the numbers the wave is written in are the studs the sheet moves. It also
	-- means the scale stays put while the geometry moves, because MeshSize is a
	-- snapshot. (Setting Size to the disc's own 120 x 0.25 x 120 instead asked
	-- the renderer to fit a 0.001-stud-thick snapshot into 0.25 studs -- a 250x
	-- stretch, which showed up on screen as a volcano with a 650-stud crater.)
	created.Size = created.MeshSize
	created.CFrame = part.CFrame
	created.Parent = rig
	return created
end

local function install(segments, rings)
	local fresh, freshIds, freshXZ = build(segments, rings)
	if fresh == nil then
		say("CreateEditableMesh() gave nil here, so the disc keeps its imported mesh")
		return false
	end
	local created = makeSheet(fresh)
	if created == nil then
		return false
	end
	if sheet ~= nil and sheet.Parent ~= nil then
		sheet:Destroy()
	end
	sheet = created
	mesh, ids, xz = fresh, freshIds, freshXZ
	heights = {}
	for ring = 0, rings do
		heights[ring] = 0
	end
	builtSegments, builtRings = segments, rings
	say("built " .. segments .. "-gon x " .. rings .. " rings: verts=" .. #fresh:GetVertices()
		.. " faces=" .. #fresh:GetFaces()
		.. " sheet MeshSize=" .. tostring(created.MeshSize)
		.. " Size=" .. tostring(created.Size))
	return true
end

-- ========== MOVING IT ==========
-- One ring at a time: every vertex in a ring is at the same radius, so they
-- all get the same height and the sheet stays a shape of revolution.
local function applyHeight(ring, height)
	local top = HALF + height
	local bottom = -HALF + height
	local topIds, bottomIds = ids[1][ring], ids[2][ring]
	local ringXZ = xz[ring]
	for wedge = 1, builtSegments do
		local topWedge, bottomWedge = topIds[wedge], bottomIds[wedge]
		local xzWedge = ringXZ[wedge]
		for corner = 1, 2 do
			local p = xzWedge[corner]
			mesh:SetPosition(topWedge[corner], Vector3.new(p.X, top, p.Z))
			mesh:SetPosition(bottomWedge[corner], Vector3.new(p.X, bottom, p.Z))
		end
	end
end

-- ========== THE WAVE ==========
-- A crest is born at the middle and travels outward at Speed studs per second.
-- At radius r the phase is (now - r / Speed) / Period, and a point is raised
-- only for the fraction Width of that period -- so a point sees nothing, then
-- a smooth rise and fall, then nothing again, and the next crest follows
-- Period seconds later. Two crests are in the air at once when Period is
-- shorter than the time one takes to cross.
local started = os.clock()
local pulseUntil = nil

local function waveSpan()
	local speed = number("Speed", 60, 1)
	local period = number("Period", 1.2, 0.05)
	return RADIUS / speed + period * 2
end

local pulse = nil
local pulseConn = nil

-- Re-bound, not bound once: streaming hands back a NEW RemoteEvent, and a
-- connection to the old one dies with it -- quietly, which is the part that
-- matters. So the listener is re-attached whenever the instance changes.
local function rebindPulse()
	local current = rig:FindFirstChild("Pulse")
	if current == pulse then
		return
	end
	if pulseConn ~= nil then
		pulseConn:Disconnect()
		pulseConn = nil
	end
	pulse = current
	if pulse ~= nil and pulse:IsA("RemoteEvent") then
		pulseConn = pulse.OnClientEvent:Connect(function()
			pulseUntil = os.clock() + waveSpan()
		end)
		say("listening on Pulse")
	end
end

rebindPulse()

-- ========== STREAMING ==========
-- This place has StreamingEnabled, so the rig can be taken off the client and
-- handed back later as DIFFERENT instances -- and the Wave that comes back
-- wears the server's imported mesh again, because the mesh written here does
-- not replicate. Without this check the ripple would survive exactly until the
-- first time the player walks away.
-- counted, not acted on: the disc being handed back as a new instance is
-- expected on this client and is reported once per half second, so a number
-- that keeps going up is a fact about streaming rather than a mystery
local discSwaps = 0

local function liveReferences()
	if sheet ~= nil and sheet.Parent == nil then
		-- the client-built sheet went with the rig it hung on
		sheet = nil
	end
	if rig ~= nil and rig.Parent == nil then
		say("the rig was streamed out")
		rig, part, sheet = nil, nil, nil
		builtSegments, builtRings = -1, -1
	end
	if rig == nil then
		rig = CollectionService:GetTagged("ShockRippleRig")[1]
		if rig == nil then
			return false
		end
		say("the rig came back: " .. rig:GetFullName())
		rebindPulse()
	end
	-- The disc itself is looked for again, but its coming and going is NOT a
	-- reason to rebuild: the sheet was dressed from it once and carries its own
	-- CFrame, so the wave keeps moving while the disc is off the client, and
	-- this picks the new instance up to hide it again. Rebuilding here instead
	-- was the bug: streaming hands the disc back as a new instance every so
	-- often, and rebuilding 5904 vertices each time spent the editable-mesh
	-- budget until even reading a mesh back returned nil.
	if part == nil or part.Parent == nil then
		local candidate = rig:FindFirstChild("Wave")
		if candidate ~= nil and candidate:IsA("MeshPart") == true then
			if part ~= nil then
				discSwaps = discSwaps + 1
			end
			part = candidate
		else
			part = nil
		end
	end
	if sheet == nil or sheet.Parent == nil then
		-- the sheet is the one thing that has to exist; without it (or without
		-- a disc to build it from) the next frame tries again
		builtSegments, builtRings = -1, -1
		if part == nil then
			return false
		end
	end
	return true
end

local frameCount = 0
local frameCost = 0
local wasActive = false
local selfMeasured = false

local function step()
	if liveReferences() == false then
		return
	end
	local now = os.clock()

	-- its own switch: the 12 parked rings have "Enabled", and one switch for
	-- two drivers would mean turning the new one on turns the old one on too
	local enabled = rig:GetAttribute("WaveEnabled") ~= false
	local active = enabled or (pulseUntil ~= nil and now < pulseUntil)
	if active == false and wasActive == false then
		-- flat and switched off: nothing to do, nothing to replicate
		return
	end

	-- builtSegments is -1 until the first build, and liveReferences sets it
	-- back to -1 when a streamed-out rig returns, so this one comparison
	-- covers "never built" as well as "changed"
	local segments = math.floor(number("Segments", 18, 3))
	local rings = math.floor(number("Rings", 24, 2))
	if segments ~= builtSegments or rings ~= builtRings then
		if install(segments, rings) == false then
			return
		end
	end

	local amplitude = number("Amplitude", 1, 0)
	local speed = number("Speed", 60, 1)
	local period = number("Period", 1.2, 0.05)
	local width = math.min(number("Width", 0.5, 0.05), 1)
	local transparency = number("Transparency", 0.15, 0)
	local reassign = rig:GetAttribute("Reassign") == true
	-- Falloff is the exponent on the envelope the travelling crest is scaled
	-- by. 0 switches the decay off and gives back the Phase 118 crest, which
	-- crossed the whole disc at full height.
	local falloff = number("Falloff", 1, 0)
	-- Two motion names, and the fallback is the one that was asked for last.
	-- Anything that is not "pulse" reads as the travelling "wave", so a typo
	-- lands on the motion that can be seen moving rather than on the subtle
	-- one.
	local motion = rig:GetAttribute("Motion")
	if motion ~= "pulse" then
		motion = "wave"
	end
	local travelling = motion == "wave"

	local startCost = os.clock()
	local elapsed = now - started
	local moved = false
	local maxHeight = 0
	local peakHeight = 0

	for ring = 0, builtRings do
		local height = 0
		if active then
			local radius = RADIUS * ring / builtRings
			-- The one envelope both motions share. Raised cosine, so it is 1 at
			-- the centre and EXACTLY 0 at r = RADIUS, and its slope is 0 at both
			-- ends: the middle does not come to a point and the rim does not
			-- show a step where the motion stops. Raising it to a power keeps
			-- all three of those properties, so Falloff cannot crease either
			-- end -- it only decides how much of a crest survives the trip out.
			-- Falloff = 0 is deliberately the identity: one branch fewer, and
			-- 0^0 in the exponent form is 1 by Lua's convention rather than by
			-- anything this script controls.
			local envelope = 1
			if falloff > 0 then
				envelope = (0.5 * (1 + math.cos(math.pi * radius / RADIUS))) ^ falloff
			end
			if travelling then
				-- A crest is born at the middle and runs outward, and the
				-- envelope is what makes it die on the way: at Falloff = 1 a
				-- crest that is half height by half the radius is gone by the
				-- rim, instead of stopping against it at full height.
				local phase = (elapsed - radius / speed) / period
				local frac = phase - math.floor(phase)
				if frac < width then
					height = amplitude * envelope
						* 0.5 * (1 - math.cos(2 * math.pi * frac / width))
				end
			else
				-- The whole sheet moves together: Amplitude at the middle,
				-- nothing at all at the rim.
				height = amplitude * envelope * math.sin(2 * math.pi * elapsed / period)
			end
		end
		if height > maxHeight then
			maxHeight = height
		end
		if math.abs(height) > peakHeight then
			peakHeight = math.abs(height)
		end
		if heights[ring] ~= height then
			heights[ring] = height
			applyHeight(ring, height)
			moved = true
		end
	end

	-- Editing an EditableMesh in place is what the part built above is expected
	-- to follow. If a client disagrees, Reassign = true rebuilds that part from
	-- the same mesh on every frame in which something actually moved.
	if moved and reassign then
		local rebuilt = makeSheet(mesh)
		if rebuilt ~= nil then
			if sheet ~= nil and sheet.Parent ~= nil then
				sheet:Destroy()
			end
			sheet = rebuilt
		end
	end

	-- While the wave is up the sheet IS the disc, so the flat one stands down;
	-- with the wave off the sheet goes and the disc's own look comes back.
	local disc = part
	if disc ~= nil and disc.Parent == nil then
		disc = nil
	end
	if sheet ~= nil and sheet.Parent ~= nil then
		if disc ~= nil then
			sheet.CFrame = disc.CFrame
		end
		sheet.Transparency = active and transparency or 1
	end
	if disc ~= nil then
		disc.Transparency = active and 1 or 0.4
	end

	-- One read-back, once, of the part's OWN copy of the mesh. That is a
	-- different question from "what did this script just write", and the
	-- difference is the whole reason the sheet exists. Held back until a crest
	-- is actually up so the number is not just the flat half-thickness.
	if selfMeasured == false and peakHeight >= 0.5 and sheet ~= nil and sheet.Parent ~= nil then
		selfMeasured = true
		local measuredOk, back = pcall(function()
			return AssetService:CreateEditableMeshAsync(sheet.MeshContent)
		end)
		if measuredOk == true and back ~= nil then
			local top = -1e9
			for _, vertex in ipairs(back:GetVertices()) do
				local at = back:GetPosition(vertex)
				if at.Y > top then
					top = at.Y
				end
			end
			say(string.format("the part itself holds ymax=%.2f; this script wrote %.2f",
				top, HALF + maxHeight))
		else
			say("the part would not hand its mesh back for measuring: " .. tostring(back))
		end
	end

	-- half a second of evidence, in a shape short enough to read back
	frameCount = frameCount + 1
	frameCost = frameCost + (os.clock() - startCost)
	if frameCount >= 30 then
		local mid = math.floor(builtRings / 2)
		local far = math.min(builtRings, mid * 2)
		local sheetState = "none"
		if sheet ~= nil and sheet.Parent ~= nil then
			sheetState = "yes"
		end
		live(string.format("t=%.2f active=%s motion=%s falloff=%.1f sheet=%s disc=%d ms/frame=%.2f h[0]=%.2f h[%d]=%.2f h[%d]=%.2f h[%d]=%.2f",
			elapsed, tostring(active), motion, falloff, sheetState, discSwaps,
			1000 * frameCost / frameCount,
			heights[0], mid, heights[mid], far, heights[far], builtRings, heights[builtRings]))
		frameCount = 0
		frameCost = 0
	end

	if pulseUntil ~= nil and now >= pulseUntil then
		pulseUntil = nil
	end
	wasActive = active
end

-- ========== START ==========
if install(math.floor(number("Segments", 18, 3)), math.floor(number("Rings", 24, 2))) then
	RunService.Heartbeat:Connect(step)
	say("running")
end
