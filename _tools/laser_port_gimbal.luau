-- laser_port_gimbal.luau
--
-- Click the port and it aims and fires. Paste as a `Script` in the Model that
-- holds the three `*_Node` children; it runs in Play mode.
--
-- WHY THE PIVOTS ARE COMPUTED AND NOT WRITTEN DOWN. Roblox's importer re-origins
-- every MeshPart somewhere inside its own primitive, so a part's Position is
-- neither the node's origin nor its own bbox centre -- and `Model:GetPivot()` is
-- no help either (measured 2026-10-04: the yoke and head nodes answered with the
-- SAME pivot, which cannot be true of two different nodes). Rotating a gimbal
-- about a guessed point does not error: the port still moves, it just sweeps
-- about a line that is not its post, which reads as "the hinge is loose"
-- (CLAUDE.md 0.18). So the node origin is RECOVERED here, at run time, from the
-- parts' own Positions minus each primitive's design bbox offset -- and every
-- part of a node is a separate, independent estimate of that same origin, so the
-- check is free: they must all agree.
--
-- The design offsets below are in the STUDS/glTF frame -- i.e. the frame Studio
-- reports, not Blender's. Measured from the .glb on 2026-10-04; the mapping from
-- the Blender frame is (x, y, z) -> (-x, z, y), which is why the sign of every
-- X offset here is flipped relative to the generator.
--
-- The two joints are applied tilt-then-pan, as one rigid chain: tilting about a
-- pin that the pan has already swung away would be measuring the pan twice. That
-- ordering is not a style choice -- it is the same one the FBX round-trip check
-- poses, so a wrong axis shows up in both places.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

-- Returns the rig API, and self-installs when it is a Script. That dual shape is
-- not ornament: it is the only way to DRIVE this file's own bytes from a test.
-- A Script cannot be required, so a test would have to re-type the derivation --
-- and then the thing that passed is a copy of the deliverable, which is the
-- mistake CLAUDE.md 0.17 records ("each channel carries half"). As a
-- ModuleScript, `require` hands back exactly what will run.
local M = {}

local CONFIG = {
	-- Long enough to read as a mechanism, short enough not to feel laggy.
	TweenSeconds = 0.45,
	-- Every part of one node estimates the same origin; if they disagree by more
	-- than this fraction of the fitted scale, the matching is wrong and the port
	-- would swing about a made-up line. Refuse rather than move.
	OriginTolerance = 0.02,
	-- The beam. Long enough to leave the room, short enough that a miss is still a
	-- miss; the raycast cuts it short the moment it meets anything.
	BeamLength = 120,
	BeamWidth = 0.16,
	BeamSeconds = 0.7,
	BeamRGB = { 249, 153, 89 },
}

-- One row per glTF primitive, in the order the exporter wrote them (which is the
-- order the importer names them: Foo, Foo2, Foo3 ...). `off` is the primitive's
-- bounding-box centre in the node's local frame -- the thing to subtract from
-- Position to get back to the node origin.
local DESIGN = {
	Base = {
		{ off = Vector3.new(-0.4300, 0.0000, 0.0000), size = Vector3.new(1.3000, 1.6000, 1.6000) },
		{ off = Vector3.new(-0.0650, 0.0000, 0.0000), size = Vector3.new(0.1700, 1.2886, 1.2886) },
		{ off = Vector3.new(-0.2000, 0.0000, 0.0000), size = Vector3.new(0.2686, 0.2686, 0.9600) },
	},
	Yoke = {
		{ off = Vector3.new(0.0000, 0.4650, 0.0000), size = Vector3.new(0.6800, 0.9300, 1.9800) },
		{ off = Vector3.new(0.0000, 0.4500, 0.0000), size = Vector3.new(0.6800, 0.9000, 1.7600) },
		{ off = Vector3.new(0.0000, 0.7400, 0.0000), size = Vector3.new(0.3742, 0.3800, 1.9800) },
	},
	EmitterHead = {
		{ off = Vector3.new(-0.4000, 0.0000, 0.0000), size = Vector3.new(1.7200, 1.3600, 1.3600) },
		{ off = Vector3.new(0.0500, 0.0000, 0.0000), size = Vector3.new(0.8200, 0.9200, 0.9200) },
		{ off = Vector3.new(-0.5000, 0.0000, 0.0000), size = Vector3.new(1.5200, 1.3600, 1.3600) },
		{ off = Vector3.new(0.1800, -0.1900, 0.0000), size = Vector3.new(0.3208, 0.2568, 1.0897) },
		{ off = Vector3.new(-1.0700, 0.0000, 0.0000), size = Vector3.new(0.1000, 0.6239, 0.6239) },
	},
	ReceiverHead = {
		{ off = Vector3.new(-0.3018, 0.0000, 0.0000), size = Vector3.new(1.5236, 1.5417, 1.5417) },
		{ off = Vector3.new(0.1300, 0.0000, 0.0000), size = Vector3.new(0.6600, 0.9200, 0.9200) },
		{ off = Vector3.new(-0.3800, 0.0000, 0.0000), size = Vector3.new(1.2800, 1.5417, 1.5417) },
		{ off = Vector3.new(0.1800, -0.1900, 0.0000), size = Vector3.new(0.3131, 0.2527, 1.0830) },
		{ off = Vector3.new(-1.0200, 0.0000, 0.0000), size = Vector3.new(0.1200, 0.2600, 0.2600) },
	},
}

-- The poses a click cycles through. Angles in degrees; pan is about world Y,
-- tilt about world Z. Kept small: this is a camera head, not a turret.
local POSES = {
	{ pan = 0, tilt = 0, label = "rest" },
	{ pan = 45, tilt = 0, label = "pan right" },
	{ pan = 45, tilt = -30, label = "pan right, tilt down" },
	{ pan = 0, tilt = 25, label = "tilt up" },
	{ pan = -45, tilt = -20, label = "pan left, tilt down" },
}

local function axisOf(v, i)
	return (i == 1 and v.X) or (i == 2 and v.Y) or v.Z
end

-- Shape-only match: an imported model carries no promise of any particular
-- scale, so each candidate is fitted and the residual compared. Same matcher as
-- the colour script, for the same reason (a silent mis-pairing looks deliberate).
local function bestRow(size, rows)
	local best, bestErr, secondErr, bestScale
	for _, row in ipairs(rows) do
		local k = 0
		for i = 1, 3 do
			k = k + axisOf(size, i) / axisOf(row.size, i)
		end
		k = k / 3
		local err = 0
		for i = 1, 3 do
			local d = axisOf(size, i) / (axisOf(row.size, i) * k) - 1
			err = err + d * d
		end
		err = math.sqrt(err / 3)
		if not bestErr or err < bestErr then
			secondErr, bestErr, best, bestScale = bestErr, err, row, k
		elseif not secondErr or err < secondErr then
			secondErr = err
		end
	end
	return best, bestScale, bestErr, secondErr
end

-- The MeshPart that corresponds to one specific design primitive. Needed because
-- the muzzle is not "the last part" or "the one with the smallest X" -- it is
-- row 5, and which MeshPart that landed on depends on the exporter's material
-- order. Asking by shape keeps that a fact about the file rather than about the
-- order I happened to write the generator in.
local function partForRow(node, kind, rowIndex)
	local want = DESIGN[kind][rowIndex]
	local found, foundErr
	for _, part in ipairs(node:GetChildren()) do
		if part:IsA("MeshPart") then
			local row, _, err = bestRow(part.Size, DESIGN[kind])
			if row == want and (not foundErr or err < foundErr) then
				found, foundErr = part, err
			end
		end
	end
	return found
end

local function nodeKind(name)
	if name:find("ReceiverHead") then
		return "ReceiverHead"
	elseif name:find("EmitterHead") then
		return "EmitterHead"
	elseif name:find("Yoke") then
		return "Yoke"
	elseif name:find("Base") then
		return "Base"
	end
end

-- node origin = the one point every part's Position agrees on, once each part's
-- own bbox offset is removed. Returns the origin and the spread of the estimates.
local function nodeOrigin(node)
	local kind = nodeKind(node.Name)
	local rows = DESIGN[kind]
	local sums, n, ks, pts = Vector3.zero, 0, {}, {}
	for _, part in ipairs(node:GetChildren()) do
		if part:IsA("MeshPart") then
			local row, k, err, second = bestRow(part.Size, rows)
			if not second or (second - err) < 0.02 then
				return nil, ("cannot identify %s by shape (err %.4f vs %.4f)")
					:format(part.Name, err, second or -1)
			end
			-- part.CFrame, not Position: if anything ever rotates these parts the
			-- offset has to go through the same rotation, and a CFrame subtraction
			-- is the version that keeps working when that happens.
			local origin = part.CFrame * CFrame.new(-row.off * k)
			pts[#pts + 1] = origin.Position
			sums = sums + origin.Position
			ks[#ks + 1] = k
			n = n + 1
		end
	end
	if n == 0 then
		return nil, "no MeshParts in " .. node.Name
	end
	local mean = sums / n
	table.sort(ks)
	local scale = ks[math.max(1, math.ceil(#ks / 2))]
	local spread = 0
	for _, p in ipairs(pts) do
		spread = math.max(spread, (p - mean).Magnitude)
	end
	if spread > CONFIG.OriginTolerance * scale then
		return nil, ("%s: parts disagree on the origin by %.4f studs (scale %.4f)")
			:format(node.Name, spread, scale)
	end
	return { origin = mean, scale = scale, spread = spread, count = n }
end

local function worldSpin(pivot, axis, degrees)
	return CFrame.new(pivot) * CFrame.fromAxisAngle(axis, math.rad(degrees)) * CFrame.new(-pivot)
end

local function buildRig(root)
	local nodes, err = {}, nil
	for _, child in ipairs(root:GetChildren()) do
		if child:IsA("Model") and child.Name:match("_Node$") then
			local kind = nodeKind(child.Name)
			if kind then
				local geo
				geo, err = nodeOrigin(child)
				if not geo then
					return nil, err
				end
				nodes[kind] = { model = child, geo = geo, kind = kind }
			end
		end
	end
	local base, yoke = nodes.Base, nodes.Yoke
	local head = nodes.EmitterHead or nodes.ReceiverHead
	if not (base and yoke and head) then
		return nil, "need a Base, a Yoke and a Head under " .. root:GetFullName()
	end
	-- The pan axis is the vertical through the yoke's origin, the tilt axis the
	-- horizontal Z through the head's. Both sit at the same x by construction
	-- (one post carries both), so that agreement is asserted rather than assumed:
	-- if it fails, the two nodes were identified wrongly and one of them will
	-- swing about a line through nothing.
	local panPoint = Vector3.new(yoke.geo.origin.X, 0, yoke.geo.origin.Z)
	local tiltPoint = Vector3.new(head.geo.origin.X, head.geo.origin.Y, 0)
	local dx = math.abs(yoke.geo.origin.X - head.geo.origin.X)
	if dx > 0.02 * yoke.geo.scale then
		return nil, ("pan and tilt posts disagree in x by %.4f studs (scale %.4f) -- one of them is not the part I think it is")
			:format(dx, yoke.geo.scale)
	end

	local parts = {}
	for _, entry in ipairs({ base, yoke, head }) do
		for _, part in ipairs(entry.model:GetChildren()) do
			if part:IsA("MeshPart") then
				parts[#parts + 1] = { part = part, role = entry, rest = part.CFrame }
			end
		end
	end
	return {
		base = base, yoke = yoke, head = head,
		panAxis = Vector3.new(0, 1, 0),
		tiltAxis = Vector3.new(0, 0, 1),
		panPoint = panPoint, tiltPoint = tiltPoint,
		tiltPointFull = Vector3.new(tiltPoint.X, tiltPoint.Y, yoke.geo.origin.Z),
		parts = parts,
		-- Row 5 of both head tables is the lens: the one primitive thin along its
		-- own X. That axis IS the optical axis, so the beam needs no extra angle
		-- constant -- it is the lens's local -X, and it swings with the head
		-- because it is read fresh from the live CFrame every frame.
		lens = partForRow(head.model, head.kind, 5),
		-- The port must not shoot itself. Excluded from the raycast by model, not
		-- by name, so a renamed part cannot quietly become a shield.
		filter = { base.model, yoke.model, head.model },
		index = 1,
	}
end

local function applyPose(rig, index, tween)
	local pose = POSES[index]
	local pan = worldSpin(rig.panPoint, rig.panAxis, pose.pan)
	local tilt = worldSpin(rig.tiltPointFull, rig.tiltAxis, pose.tilt)
	for _, entry in ipairs(rig.parts) do
		local target
		if entry.role == rig.head then
			target = pan * tilt * entry.rest
		elseif entry.role == rig.yoke then
			target = pan * entry.rest
		else
			target = entry.rest
		end
		if tween then
			TweenService:Create(entry.part, tween, { CFrame = target }):Play()
		else
			entry.part.CFrame = target
		end
	end
	rig.index = index
	print(("[laser_port] pose %d/%d  %s  (pan %d deg, tilt %d deg)")
		:format(index, #POSES, pose.label, pose.pan, pose.tilt))
end

M.buildRig = buildRig
M.applyPose = applyPose
M.POSES = POSES

-- ============================================================ FIRING
--
-- The beam is a separate Part, rebuilt from the lens's LIVE CFrame on every
-- Heartbeat for as long as it burns. That is not laziness about welding: the head
-- is mid-tween for most of the shot, and a beam that only knew where the muzzle
-- was when the click arrived would be a beam leaving a port that has already
-- swung away from it -- visibly detached, and the one thing a laser must not look
-- like is detached.
--
-- It stops at the first thing the raycast meets rather than running its full
-- length. A beam that always ends at the same distance in mid-air is a decal of a
-- beam; a beam that lands on the wall is a laser.
local function outOfLens(lens)
	-- Outward is the lens's own -X: the lens is the far face of the head, and its
	-- thin axis runs along the beam. No angle constant is typed here on purpose --
	-- see the header on why a guessed direction is invisible when it is wrong.
	return lens.CFrame * CFrame.new(-lens.Size.X / 2, 0, 0), -lens.CFrame.RightVector
end

local function beamFrame(pos, dir)
	local x = dir.Unit
	local ref = math.abs(x.Y) > 0.9 and Vector3.new(0, 0, 1) or Vector3.new(0, 1, 0)
	local y = (ref - x * ref:Dot(x)).Unit
	return CFrame.fromMatrix(pos, x, y, x:Cross(y))
end

-- ONE FRAME OF THE SHOT -- named and exported rather than living inline in the
-- connection. Measured 2026-10-04: the plugin VM answers `Heartbeat:Wait()` and
-- still never runs the callbacks it was handed (0 callbacks over 3 ticks, while the
-- connection reported Connected = true). So anything that exists ONLY inside a
-- connection is unverifiable from the only VM I can drive -- CLAUDE.md 0.2 again in
-- new clothes. Extracted, a test calls the SAME code the connection calls instead of
-- a copy of it, and the connection itself becomes one line you can read at a glance.
function M.stepBeam(rig)
	local shot = rig.beam
	if not shot then
		return nil
	end
	local origin, dir = outOfLens(shot.lens)
	local hit = workspace:Raycast(origin.Position, dir * shot.length, shot.params)
	local span = hit and hit.Distance or shot.length
	shot.core.Size = Vector3.new(math.max(span, 0.1), CONFIG.BeamWidth, CONFIG.BeamWidth)
	shot.core.CFrame = beamFrame(origin.Position + dir * (span / 2), dir)
	if hit then
		shot.mark.CFrame = CFrame.new(hit.Position + hit.Normal * 0.1)
		shot.mark.Transparency = 0
	else
		shot.mark.Transparency = 1
	end
	-- Kept on the rig so a test can ask what the shot hit. Returning it from here
	-- would hand back the state at fire time, which is nil by construction -- the
	-- first raycast has not run yet.
	rig.lastHit = hit
	return span, hit
end

function M.fire(rig, length, seconds)
	local lens = rig.lens
	if not lens then
		return nil, "no lens part on the head -- nothing to fire from"
	end
	length = length or CONFIG.BeamLength
	seconds = seconds or CONFIG.BeamSeconds
	-- One shot at a time: a second click restarts the beam rather than stacking a
	-- second one on the same muzzle.
	if rig.stopBeam then
		rig.stopBeam()
	end

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = rig.filter

	local core = Instance.new("Part")
	core.Name = "LaserBeam"
	core.Anchored = true
	core.CanCollide = false
	core.CanQuery = false
	core.CanTouch = false
	core.CastShadow = false
	core.Material = Enum.Material.Neon
	core.Color = Color3.fromRGB(CONFIG.BeamRGB[1], CONFIG.BeamRGB[2], CONFIG.BeamRGB[3])
	core.Shape = Enum.PartType.Cylinder  -- a Roblox cylinder runs along its own X
	core.Size = Vector3.new(length, CONFIG.BeamWidth, CONFIG.BeamWidth)
	core.Parent = workspace

	local glow = Instance.new("PointLight")
	glow.Brightness = 5
	glow.Range = 30
	glow.Color = core.Color
	glow.Parent = lens

	local mark = Instance.new("Part")
	mark.Name = "LaserImpact"
	mark.Anchored = true
	mark.CanCollide = false
	mark.CanQuery = false
	mark.CanTouch = false
	mark.CastShadow = false
	mark.Material = Enum.Material.Neon
	mark.Color = core.Color
	mark.Shape = Enum.PartType.Ball
	mark.Size = Vector3.new(1.1, 1.1, 1.1)
	mark.Transparency = 1
	mark.Parent = workspace

	-- The frame's work lives in M.stepBeam; this connection is only the clock.
	rig.beam = { lens = lens, core = core, mark = mark, length = length, params = params }
	-- Place it NOW, not on the next tick. A Part is born at the world origin, so
	-- without this line a freshly fired shot spends a frame or more as a 120-stud
	-- neon cylinder lying through (0,0,0) -- a real artefact that shows up as an
	-- orange rod across the map, not a theoretical one.
	M.stepBeam(rig)
	local conn
	conn = RunService.Heartbeat:Connect(function()
		M.stepBeam(rig)
	end)

	local function stop()
		if conn then
			conn:Disconnect()
			conn = nil
		end
		local hit = rig.lastHit
		if hit then
			print(("[laser_port] beam off -- hit %s at %.1f studs")
				:format(hit.Instance:GetFullName(), hit.Distance))
		else
			print("[laser_port] beam off -- nothing within " .. tostring(length) .. " studs")
		end
		core:Destroy()
		mark:Destroy()
		glow:Destroy()
		rig.beam = nil
		rig.stopBeam = nil
	end
	rig.stopBeam = stop
	task.delay(seconds, stop)
	-- Hand back the part itself, not a boolean: a test that can read the beam's
	-- CFrame and Size can tell a shot that landed from one that missed, and a
	-- boolean cannot.
	return core
end

-- Hangs the ClickDetector and drops the rig onto pose 1. Returns the rig, or nil
-- plus the reason -- the caller decides how loudly to say it.
function M.install(root)
	local rig, err = buildRig(root)
	if not rig then
		return nil, err
	end
	print(("[laser_port] rig %s  scale=%.4f  pan axis x=%.4f z=%.4f  tilt axis x=%.4f y=%.4f")
		:format(root.Name, rig.yoke.geo.scale, rig.panPoint.X, rig.panPoint.Z,
			rig.tiltPoint.X, rig.tiltPoint.Y))
	-- ipairs and an explicit lookup, not `pairs` over a table literal: the printed
	-- order is then fixed, and these lines are the only evidence a reader gets
	-- that the three nodes were identified as the three things they are.
	for _, row in ipairs({ { "Base", rig.base }, { "Yoke", rig.yoke }, { "Head", rig.head } }) do
		local entry = row[2]
		print(("[laser_port]   %-5s origin=(%.4f, %.4f, %.4f) from %d part(s), spread %.5f")
			:format(row[1], entry.geo.origin.X, entry.geo.origin.Y, entry.geo.origin.Z,
				entry.geo.count, entry.geo.spread))
	end

	-- The clickable thing is the base plate: it does not move, so a player aiming
	-- at the port never has to chase it.
	local target = rig.base.model:FindFirstChildWhichIsA("MeshPart")
	if not target then
		return nil, "no base MeshPart to hang a ClickDetector on"
	end
	local detector = target:FindFirstChildWhichIsA("ClickDetector")
	if not detector then
		detector = Instance.new("ClickDetector")
		detector.MaxActivationDistance = 40
		detector.Parent = target
	end
	if rig.lens then
		print("[laser_port] lens: " .. rig.lens:GetFullName())
	else
		warn("[laser_port] no lens part found on the head -- it will aim but not fire")
	end

	detector.MouseClick:Connect(function()
		applyPose(rig, (rig.index % #POSES) + 1, TweenInfo.new(
			CONFIG.TweenSeconds, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut))
		-- Fire AFTER the tween starts, not before: the beam reads the lens's live
		-- CFrame every frame, so it tracks the swing rather than lagging a shot
		-- behind it.
		M.fire(rig)
	end)

	applyPose(rig, 1, false)
	return rig
end

if script:IsA("Script") then
	local rig, err = M.install(script.Parent)
	if not rig then
		-- Say WHY. A failed install and an unregistered click are the same
		-- nothing-happened from the outside (CLAUDE.md 0.17), so this line is the
		-- only thing standing between the operator and that ambiguity.
		warn("[laser_port] not installed: " .. tostring(err))
	end
end

return M
