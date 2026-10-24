-- apply_cbl_laser_mk4_materials.luau
--
-- WHY THIS EXISTS. Roblox's importer splits an incoming mesh into one MeshPart
-- per material, which is the split we want, and then throws the materials away:
-- every part arrives as Material.Plastic with a grey Color. A MeshPart has ONE
-- Color and ONE Material and no per-face slot, so a flat-coloured multi-material
-- mesh can only arrive coloured if something sets those properties afterwards.
-- That is this script. Same job, same reasoning as
-- _tools/apply_laser_port_materials.luau; read that header for the long version.
--
-- HOW IT FINDS THE RIGHT PART -- BY SIZE, NOT BY NAME. The importer's naming
-- (Foo, Foo.001, ...) follows the primitive order today, but that order is the
-- importer's business and not a promise. Every row below is a MEASURED bounding
-- box of one material's faces, printed by cbl_laser_mk4.py between
-- MATERIAL_TABLE_BEGIN / END in the same run that wrote the delivered .fbx --
-- so these numbers are not retyped from a render.
--
-- THE MATCH IS ABSOLUTE, NOT SHAPE-ONLY, and that was measured rather than
-- chosen: the first version fitted a free overall scale k and left Core/Cyan
-- AMBIGUOUS against Core/White (MEASURED 2026-10-24 by the stub harness: with
-- exact sizes the scale-free fit scored 0.0000 and 0.0171 against a 0.02 margin,
-- because the two rows differ almost entirely in SCALE -- 42.81 vs 41.28 -- and
-- fitting k cancels exactly the difference that tells them apart). With k forced
-- to 1 the same pair separates by 0.043, and everything else by far more. The
-- import scale is not unknown anyway -- the operator types 5.902 -- so a part
-- that does not match within MaxSizeErr is a WRONG IMPORT to report, with the
-- implied scale in the line, not a candidate to paint at any scale. That is also
-- what makes the .glb route (1.6943x too big) self-diagnosing.
--
-- AMBIGUITY IS REFUSED. A candidate must beat the runner-up by MinMargin or the
-- part is left untouched and reported. A silent mis-pairing would paint the
-- wrong colour on the wrong piece and look deliberate (CLAUDE.md 0.18: a wrong
-- measurement does not error, it quietly gives you a number).
--
-- THE NUMBERS. Sizes are in the frame Roblox reports after an FBX import at
-- 5.902: (X, Y-up, Z). That is the build's own (x, z, y) -- the export rotates
-- Blender Z-up into Studio Y-up, so the tuple is permuted, not rescaled. The
-- four objects are:
--   Mount  the fixed trunnion cradle
--   Body   the machine
--   Prongs the muzzle claw
--   Core   plasma tube + helices + lens + aperture rings
--
-- COLOURS. Blender's base colours are LINEAR, Color3 is sRGB. The triplets
-- below are the file's linear values through the sRGB transfer function --
-- copying the linear numbers across would have produced parts about a third as
-- bright as the previews the operator approved. The three emissive materials
-- (Cyan / Amber / White -- strength 5 / 4 / 9 in the build) become Neon, because
-- an emissive flat colour is the one thing a Roblox Material cannot express.
--
-- It only touches Color and Material on MeshParts: no renaming, no reparenting,
-- no moving, no deleting (CLAUDE.md 6). Safe to run twice.

local CONFIG = {
	-- Name fragment used to find the imported assembly. The importer names the
	-- container after the file, so this is "CblLaserMk4" for both a Model and a
	-- flat drop into Workspace.
	RootName = "cbllasermk4",
	-- Largest relative size error that still counts as a match (RMS over the
	-- three axes). 0.02 is 2%: the delivered 5.902 import is exact to well under
	-- 0.1%, so this only absorbs float noise and a rounded Size readout -- while
	-- the nearest WRONG pair on this asset (Core/Cyan vs Core/White) is 0.043.
	MaxSizeErr = 0.02,
	-- A match must beat the second-best candidate by this margin, or the part is
	-- reported AMBIGUOUS and left alone. Same value as the LaserPort script.
	MinMargin = 0.02,
	-- Warn when the implied import scale is further than this from 1.0. Not a
	-- match criterion (MaxSizeErr already bounds it per axis); this catches a
	-- match that fits overall but is a little off in every axis at once.
	ScaleWarn = 0.02,
}

-- One row per (part, material), sizes in delivered studs, Roblox frame.
local DESIGN = {
	{ part = "Mount", mat = "Hull",   size = { 21.6000, 18.7200, 23.0400 } },
	{ part = "Mount", mat = "Dark",   size = { 15.0962, 15.5756, 19.6800 } },
	{ part = "Mount", mat = "Brass",  size = {  5.2800,  5.2800, 19.2640 } },
	{ part = "Mount", mat = "Hazard", size = { 15.0962,  0.9280, 15.0962 } },

	{ part = "Body", mat = "Hull",   size = { 52.6400, 16.8000, 16.8000 } },
	{ part = "Body", mat = "Dark",   size = { 56.8320, 16.4850, 15.8400 } },
	{ part = "Body", mat = "Brass",  size = { 44.8000, 20.3840, 16.8960 } },
	{ part = "Body", mat = "Hazard", size = {  1.2800, 14.0012, 14.1343 } },
	{ part = "Body", mat = "Cyan",   size = { 36.2160, 13.8171, 15.0018 } },
	{ part = "Body", mat = "Amber",  size = {  0.6720,  0.3200,  3.5520 } },

	{ part = "Prongs", mat = "Brass", size = { 8.4800, 11.7882, 13.5996 } },

	{ part = "Core", mat = "Cyan",  size = { 42.8074, 12.1600, 12.6781 } },
	{ part = "Core", mat = "White", size = { 41.2837, 11.8877, 11.8900 } },
}

-- Roblox Material + sRGB colour per named material. The three metals share
-- Material.Metal and differ only in colour, which is what they were in Blender
-- too (metallic 0.82 / 0.70 / 1.00, no texture). Hazard is painted plate, not
-- bare metal (metallic 0.15), so it gets SmoothPlastic.
local LOOK = {
	Hull   = { material = Enum.Material.Metal,         rgb = { 133, 138, 145 } },
	Dark   = { material = Enum.Material.Metal,         rgb = {  60,  63,  68 } },
	Brass  = { material = Enum.Material.Metal,         rgb = { 191, 155,  91 } },
	Hazard = { material = Enum.Material.SmoothPlastic, rgb = { 234, 197,  48 } },
	Cyan   = { material = Enum.Material.Neon,          rgb = {  66, 229, 255 } },
	Amber  = { material = Enum.Material.Neon,          rgb = { 255, 162,  53 } },
	White  = { material = Enum.Material.Neon,          rgb = { 229, 250, 255 } },
}

local function axis(v, i)
	return (i == 1 and v.X) or (i == 2 and v.Y) or v.Z
end

-- Best-fitting row for an observed Size. Returns row, implied scale k, the two
-- errors. err is the RMS relative size error at k = 1 (so it measures SIZE, not
-- shape); k is the mean of the per-axis ratios and is DIAGNOSTIC only -- it
-- says how far the import scale is from the 5.902 the table was measured at.
local function bestRow(size)
	local best, bestErr, secondErr, bestScale
	for _, row in ipairs(DESIGN) do
		local k = 0
		local err = 0
		for i = 1, 3 do
			local d = axis(size, i) / row.size[i] - 1
			k = k + 1 + d
			err = err + d * d
		end
		k = k / 3
		err = math.sqrt(err / 3)
		if not bestErr or err < bestErr then
			secondErr = bestErr
			bestErr, best, bestScale = err, row, k
		elseif not secondErr or err < secondErr then
			secondErr = err
		end
	end
	return best, bestScale, bestErr, secondErr
end

-- The imported assembly: every Model/Folder whose name carries the file name,
-- outermost only (a nested one would double-count). Fallback covers an import
-- that landed as loose MeshParts directly under Workspace.
local function findRoots()
	local roots = {}
	for _, obj in ipairs(workspace:GetDescendants()) do
		if (obj:IsA("Model") or obj:IsA("Folder"))
			and obj.Name:lower():find(CONFIG.RootName, 1, true) then
			local nested = false
			local up = obj.Parent
			while up and up ~= workspace do
				if (up:IsA("Model") or up:IsA("Folder"))
					and up.Name:lower():find(CONFIG.RootName, 1, true) then
					nested = true
					break
				end
				up = up.Parent
			end
			if not nested then
				table.insert(roots, obj)
			end
		end
	end
	return roots
end

local roots = findRoots()
local parts = {}
if #roots > 0 then
	for _, root in ipairs(roots) do
		for _, d in ipairs(root:GetDescendants()) do
			if d:IsA("MeshPart") then
				table.insert(parts, d)
			end
		end
	end
else
	for _, d in ipairs(workspace:GetChildren()) do
		if d:IsA("MeshPart") then
			table.insert(parts, d)
		end
	end
end

local lines = {}
table.insert(lines, ("CblLaserMk4: %d root(s), %d MeshPart(s)")
	:format(#roots, #parts))
if #parts == 0 then
	table.insert(lines, "nothing to paint -- import the .fbx first (type 5.902)")
end

local painted, skipped = 0, 0
local usedRow, namePartWarn = {}, 0
-- How many parts each row matched. A row that matches zero times means a piece
-- never arrived (or arrived at a size nobody measured); a row matching twice
-- means the importer split one material into two shells -- exactly the
-- `material=-1` bevel defect the build was fixed for, so it is worth seeing.
local rowHits = {}
for i = 1, #DESIGN do
	rowHits[i] = 0
end

for _, part in ipairs(parts) do
	local row, k, err, second = bestRow(part.Size)
	local margin = (second and (second - err)) or 1
	local rowIndex = table.find(DESIGN, row)

	-- The part's own name still says which of the four objects it came from.
	-- It is not used to pick the row -- but when it disagrees with the shape
	-- match, one of the two is wrong and the operator should hear about it.
	local hinted = part.Name:find("Mount") and "Mount"
		or part.Name:find("Prongs") and "Prongs"
		or part.Name:find("Body") and "Body"
		or part.Name:find("Core") and "Core"
		or nil

	if err > CONFIG.MaxSizeErr then
		-- Nothing is close. Say what was seen and what scale it implies, so a
		-- 1.6943 import reads as a diagnosis rather than as an empty scan.
		table.insert(lines, ("  %-30s NO MATCH  size (%.3f, %.3f, %.3f) -- nearest %s/%s err %.3f, implies import scale %.4f")
			:format(part.Name, part.Size.X, part.Size.Y, part.Size.Z,
				row.part, row.mat, err, k))
		skipped = skipped + 1
	elseif margin < CONFIG.MinMargin then
		table.insert(lines, ("  %-30s AMBIGUOUS (err %.4f vs %.4f) -- left untouched")
			:format(part.Name, err, second or -1))
		skipped = skipped + 1
	else
		local look = LOOK[row.mat]
		part.Material = look.material
		part.Color = Color3.fromRGB(look.rgb[1], look.rgb[2], look.rgb[3])
		rowHits[rowIndex] = (rowHits[rowIndex] or 0) + 1
		usedRow[row.mat] = (usedRow[row.mat] or 0) + 1
		local flag = ""
		if math.abs(k - 1) > CONFIG.ScaleWarn then
			flag = flag .. ("  *** import scale %.4f (typed 5.902?) ***"):format(k)
		end
		if hinted and hinted ~= row.part then
			namePartWarn = namePartWarn + 1
			flag = flag .. ("  *** name says %s, shape says %s ***"):format(hinted, row.part)
		end
		table.insert(lines, ("  %-30s -> %-6s %-6s %-13s rgb(%d,%d,%d)  k=%.4f err=%.4f%s")
			:format(part.Name, row.part, row.mat, look.material.Name,
				look.rgb[1], look.rgb[2], look.rgb[3], k, err, flag))
		painted = painted + 1
	end
end

-- Every DESIGN row should have been used exactly once. Report both directions:
-- this is the check that turns "the file looked right in Blender" into "every
-- piece of it is on screen".
for i, row in ipairs(DESIGN) do
	if rowHits[i] == 0 then
		table.insert(lines, ("  MISSING  %s/%s -- no imported part has this size")
			:format(row.part, row.mat))
	elseif rowHits[i] > 1 then
		table.insert(lines, ("  *** %s/%s matched %d parts (one material split into shells?)")
			:format(row.part, row.mat, rowHits[i]))
	end
end

table.insert(lines, ("painted %d part(s), %d skipped, %d name/shape disagreement(s)")
	:format(painted, skipped, namePartWarn))

-- Both channels: the MCP tool returns the chunk's value, the console carries the
-- prints, and a silent empty return is indistinguishable from "nothing to do"
-- (CLAUDE.md 0.17). The separator is built with string.char, not an escape --
-- text pushed through the Studio tool layer is decoded once (CLAUDE.md 0.10), so
-- this file contains no backslash at all.
local SEP = string.char(10)
for _, line in ipairs(lines) do
	print(line)
end
return table.concat(lines, SEP)
