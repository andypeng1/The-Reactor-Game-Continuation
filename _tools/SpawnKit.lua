--[[
	SpawnKit -- the spawn-point correction pass.
	(staged on disk 2026-09-23; install target: ServerScriptService.GameCore.Rebuild.SpawnKit)

	WHAT THIS IS NOT. It builds nothing and moves nothing. No spawn is created,
	moved, renamed or reparented; nothing is destroyed. It writes two booleans per
	spawn and nothing else. No geometry, no appearance property, no name. No
	spawn's CFrame, Size, Transparency or TeamColor is touched.

	WHY. Measured live 2026-09-23. The place holds five SpawnLocations, and with
	`Teams` empty (0 children) every player in it is team-less:

	  TeamSpawns.Spawn1..4      x 257, y 277.1, z 29.4 / 36.9 / 44.4 / 51.9
	                            Neutral = false, TeamColor = White
	                            look = (-1, 0, 0) -- facing west, down the room,
	                            at the console row 135 studs away

	  TeamSpawns.SpawnLocation  x 233, y 402.9, z 1370.0
	                            Neutral = true -- the observed live one

	The live run put the character at (233.0, 406.1, 1370.0): the spawn that got
	CHOSEN is the one 1,370 studs from the game. It is a 20 x 0.5 x 4 plate
	standing in open space -- a ray straight down finds nothing for 500 studs, the
	only solid thing in any direction is a wall 43 studs east (RLGatewayRoom.Floor),
	the only thing overhead a ceiling light 18.5 studs up
	(MovingParts.LoungeCeilLightPart), and FallenPartsDestroyHeight is -500. The
	character does stand on it (FloorMaterial reads Plastic, Y held at 406.1 across
	five seconds), so this was never a fall loop: it is a 20 x 4 invisible plate in
	the void, and the first step off it is the fall.

	All five are Transparency = 1, so none of this is visible before or after. The
	defect is not that the game looks wrong; it is that it starts the player in the
	wrong place, facing nothing.

	WHY THE CORRECTION SETS TWO PROPERTIES AND NOT ONE. The first version of this
	kit retired the stray with `Neutral = false` alone, on the reasoning that a
	Neutral = false spawn "can never fire" for a team-less player. Checking the
	official reference killed that reasoning, and the kill is worth recording:

	    Neutral: "If Neutral is set to false, only players whose Player.TeamColor
	    is equal to SpawnLocation.TeamColor can use the SpawnLocation."
	    Enabled: "When disabled players cannot spawn at the SpawnLocation."

	The stray is TeamColor = White and so are Spawn1..4 -- and the "IF" is not a
	hypothetical, it is the actual state. Player.Neutral says so outright: when a
	player is neutral (which is what a player with no Team is) the Team property is
	nil and "the TeamColor will be white". Every player in this place is therefore
	White-TeamColor, which means Spawn1..4 satisfied `TeamColor == TeamColor` ALL
	ALONG and were ALWAYS eligible.

	That kills the premise this kit was first drafted on. It is not "four dead
	spawns and one bad one"; it is FIVE LIVE SPAWNS, one of which is in the void.
	And it makes `Neutral = false` not merely insufficient but INERT: writing it on
	the stray would have changed nothing at all, because a white player still
	matches a white spawn with the flag down. The first draft would have run
	cleanly, reported a change, and left the defect exactly where it was -- a fix
	whose entire effect was to rewrite a boolean that was already doing nothing.

	THREE READINGS, ONE CORRECTION. The one observation we have does not say which
	of these produced it, and the authored `Enabled` values were never read, so
	none of them is excluded:

	  (a) the in-room spawns are authored Enabled = false, so only the stray could
	      fire -- and then the operative half of the fix is Enabled = true in-room;
	  (b) all five were usable and the stray simply won the choice -- and then the
	      operative half is Enabled = false on the stray;
	  (c) neither, and something else does the choosing.

	The correction does not have to choose, and that is exactly why both properties
	are written against the one positional rule: under every reading the result is
	four usable spawns in the room and zero outside it. Scan() prints the authored
	state before anything is written, so the first run will say which reading held.

	  in the control room's envelope  ->  Neutral = true,  Enabled = true
	  outside it                      ->  Neutral = false, Enabled = false

	Each property has its own job and its own reason. In the room, Neutral = true
	makes the spawn open to any team, and Enabled = true asserts the other half --
	a spawn that is neutral but disabled still cannot fire, so setting only Neutral
	would leave a silent hole if any in-room spawn were authored disabled. Outside,
	Enabled = false retires the stray unconditionally, and Neutral = false states
	the intent rather than relying on Enabled to carry it.

	WHY THE ROOM IS A POSITION TEST AND NOT A NAME LIST. The four live spawns sit at
	x = 257, one stud OUTSIDE the room's own x range (-183..256), because a 2x2
	plate centred on 257 straddles the boundary. The envelope below therefore closes
	at x = 270, the plate's outer face, not the room's wall. y (250..320) and z
	(-70..70) each exclude the stray independently -- it is at 402.9 and 1370 against
	bounds of 320 and 70 -- so the test does not rest on any single axis.
	The test is positional because a name list is exactly what DECISIONS 84 and 86
	each caught being wrong: a container name records where something was authored,
	not what it is or where it ended up.

	SAFETY. Two properties, on at most five instances, all `Enabled`/`Neutral`
	booleans. Both authored values are recorded as attributes before the first
	change, so Revert() is exact. ApplyAll() refuses to run in three cases: no
	spawn found at all, nothing left to change, and -- the one that matters -- no
	spawn lying inside the room, because retiring the stray without putting the
	room in the pool would leave the place with no usable spawn, which is worse
	than what it has now.
--]]

local SpawnKit = {}

local ORIGIN_NEUTRAL = "SpawnKitAuthoredNeutral"
local ORIGIN_ENABLED = "SpawnKitAuthoredEnabled"

-- The control room's envelope, widened in x to the outer face of the door
-- spawns. y and z each exclude the stray plate independently (it is at 402.9 and
-- 1370 against bounds of 320 and 70), so the test does not rest on one axis.
local ROOM_MIN = Vector3.new(-200, 250, -70)
local ROOM_MAX = Vector3.new(270, 320, 70)

local function inRoom(p)
	return p.X >= ROOM_MIN.X and p.X <= ROOM_MAX.X
		and p.Y >= ROOM_MIN.Y and p.Y <= ROOM_MAX.Y
		and p.Z >= ROOM_MIN.Z and p.Z <= ROOM_MAX.Z
end

local function spawns()
	local out = {}
	for _, d in ipairs(game.Workspace:GetDescendants()) do
		if d:IsA("SpawnLocation") then out[#out + 1] = d end
	end
	return out
end

-- The one place the rule lives, so Scan and ApplyAll cannot disagree.
-- Returns nil when the spawn already satisfies it.
local function decide(sp)
	local want = inRoom(sp.Position)
	if sp.Neutral == want and sp.Enabled == want then return nil end
	return {
		neutral = want,
		enabled = want,
		why = want
			and "in the control room but not usable (Neutral / Enabled)"
			or "outside the control room but usable -- the live fallback",
	}
end

-- Dry run. Reports what would change and never writes.
--
-- `inRoomAtAll` counts spawns that lie in the room whatever their state, which is
-- deliberately NOT the same as `fixInRoom` (the ones needing a write): the guard in
-- ApplyAll has to know the room has a candidate even when every candidate is
-- already correct, or it would refuse the very run that only has to retire the stray.
function SpawnKit.Scan()
	local rep = { total = 0, inRoomAtAll = 0, fixInRoom = 0, fixOutRoom = 0, samples = {} }
	for _, sp in ipairs(spawns()) do
		rep.total = rep.total + 1
		local room = inRoom(sp.Position)
		local d = decide(sp)
		if room then rep.inRoomAtAll = rep.inRoomAtAll + 1 end
		if d then
			if room then
				rep.fixInRoom = rep.fixInRoom + 1
			else
				rep.fixOutRoom = rep.fixOutRoom + 1
			end
			if #rep.samples < 8 then
				rep.samples[#rep.samples + 1] =
					string.format("%s  ->  Neutral = %s, Enabled = %s   (%s)",
						sp:GetFullName(), tostring(d.neutral), tostring(d.enabled), d.why)
			end
		end
	end
	return rep
end

local function recordOnce(sp)
	-- Two attributes, each guarded with ~= nil rather than a truth test: false is a
	-- value worth restoring, and a truth test would re-snapshot an already-corrected
	-- spawn on a second run, freezing the post-apply value as the "authored" one.
	if sp:GetAttribute(ORIGIN_NEUTRAL) == nil then
		sp:SetAttribute(ORIGIN_NEUTRAL, sp.Neutral)
	end
	if sp:GetAttribute(ORIGIN_ENABLED) == nil then
		sp:SetAttribute(ORIGIN_ENABLED, sp.Enabled)
	end
end

function SpawnKit.ApplyAll()
	local rep = SpawnKit.Scan()
	if rep.total == 0 then
		warn("[SpawnKit] no SpawnLocation found -- refusing to run")
		return nil, rep
	end
	if rep.fixInRoom == 0 and rep.fixOutRoom == 0 then
		-- Either already applied, or the place no longer matches the measurement this
		-- kit was written against. Both are reasons to stop, not to report success:
		-- silently doing nothing would hide a wrong assumption.
		warn("[SpawnKit] scan found nothing to change -- refusing to run")
		return nil, rep
	end
	-- Retiring the stray without putting the room in the pool would leave the place
	-- with no usable spawn at all, which is worse than what it has now. Note this
	-- tests the room's CANDIDATES, not the pending writes, so a run that only has to
	-- disable the stray still proceeds.
	if rep.inRoomAtAll == 0 then
		warn("[SpawnKit] no spawn lies in the control room -- refusing to run")
		return nil, rep
	end

	local CHS = game:GetService("ChangeHistoryService")
	pcall(function() CHS:SetWaypoint("SpawnKitApply") end)

	local stats = { scanned = 0, applied = 0, failed = 0, skipped = 0 }
	for _, sp in ipairs(spawns()) do
		stats.scanned = stats.scanned + 1
		local d = decide(sp)
		if d then
			recordOnce(sp)
			local ok = pcall(function()
				sp.Neutral = d.neutral
				sp.Enabled = d.enabled
			end)
			if ok then
				stats.applied = stats.applied + 1
			else
				stats.failed = stats.failed + 1
			end
		else
			stats.skipped = stats.skipped + 1
		end
	end

	pcall(function() CHS:SetWaypoint("SpawnKitApply-done") end)
	return stats, rep
end

-- Post-apply readback: what the place holds now, not what the last Apply said it
-- wrote. `usableInRoom` is the number Roblox can actually choose from, which is the
-- only count that answers "will the player start in the control room".
-- `strayUsable` must be 0 when this pass is finished.
function SpawnKit.Verify()
	local rep = { total = 0, inRoomAtAll = 0, usableInRoom = 0, strayUsable = 0, list = {} }
	for _, sp in ipairs(spawns()) do
		rep.total = rep.total + 1
		local p = sp.Position
		local room = inRoom(p)
		if room then rep.inRoomAtAll = rep.inRoomAtAll + 1 end
		local usable = sp.Neutral and sp.Enabled
		if usable and room then rep.usableInRoom = rep.usableInRoom + 1 end
		if usable and not room then rep.strayUsable = rep.strayUsable + 1 end
		rep.list[#rep.list + 1] = string.format(
			"%s  Neutral=%s Enabled=%s  (%d, %d, %d)  inRoom=%s",
			sp:GetFullName(), tostring(sp.Neutral), tostring(sp.Enabled),
			p.X, p.Y, p.Z, tostring(room))
	end
	return rep
end

function SpawnKit.Revert()
	local n, failed = 0, 0
	for _, sp in ipairs(spawns()) do
		local rawN = sp:GetAttribute(ORIGIN_NEUTRAL)
		local rawE = sp:GetAttribute(ORIGIN_ENABLED)
		if rawN ~= nil or rawE ~= nil then
			local ok = pcall(function()
				if rawN ~= nil then sp.Neutral = rawN end
				if rawE ~= nil then sp.Enabled = rawE end
				sp:SetAttribute(ORIGIN_NEUTRAL, nil)
				sp:SetAttribute(ORIGIN_ENABLED, nil)
			end)
			if ok then
				n = n + 1
			else
				failed = failed + 1
			end
		end
	end
	return { restored = n, failed = failed }
end

return SpawnKit
