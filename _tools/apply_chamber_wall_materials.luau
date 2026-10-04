-- apply_chamber_wall_materials.luau
--
-- WHY THIS EXISTS, again. Roblox's 3D importer splits an imported mesh into one
-- MeshPart per material -- which is the split we want -- and then throws the
-- materials away: every part lands Material.Plastic with a grey Color and an empty
-- TextureID (measured on the laser port, 2026-10-04: 11 parts, Material=Plastic,
-- Color 0.196/0.275/0.353 -- a per-NODE grey, not even per-material).
--
-- For ChamberWall24 that would be worse than cosmetic. The wall is an 18-sided
-- collar, a brass band that flares out to 24 sides, and a 24-sided top; all three
-- are the same grey otherwise, and the BAND IS THE WHOLE POINT of the asset -- 84
-- triangles wrapped round a 65-stud ring are not something the eye finds by itself.
-- Whole thing flattened to one colour, the join stops being legible.
--
-- HOW IT FINDS THE RIGHT PART. Not by name and not by order -- name and order are
-- the importer's business, not a promise, and a mis-pairing is silent. By SHAPE,
-- and by shape RATIOS rather than absolute sizes, because the absolute number
-- depends on which file was imported and on the importer's scale constant:
--
--     base      X = 129.39  Y = 1.20   (the 18-gon collar, one wall thick)
--     band      X = 137.17  Y = 3.00   (18 sides out to 24)
--     top       X = 137.17  Y = 9.00   (the 24-sided wall)
--
-- Each of those becomes, after dividing by ITS OWN largest dimension, a pair of
-- pure numbers -- base (1.0, 0.00927), band (1.0, 0.02187), top (1.0, 0.06561) --
-- and each part is divided by its own largest the same way. Both sides scaled, so
-- a part's size is irrelevant to whether it matches: only its proportions are.
--
-- The first version of this divided BOTH sides by the widest part in the scene.
-- That is not the same thing, and it is wrong in the one case that matters: it
-- only cancels when the import happens to be at design scale. Fed a set scaled
-- uniformly by 1.6943, it printed ratios identical to the design ratios to four
-- decimals and then refused every one of them. Caught 2026-10-04 by running it
-- against synthetic parts at both scales -- which is why that test exists.
--
-- It REFUSES rather than guesses: a part whose best row does not beat the runner-up
-- by MinMargin is reported AMBIGUOUS and left alone, and a part matching no row is
-- reported UNMATCHED. Painting the wrong colour on the wrong piece looks
-- deliberate -- the same failure mode as a wrong ruler (CLAUDE.md 0.18).
--
-- COLOURS are the Blender base colours put through the linear -> sRGB transfer
-- function (Blender stores linear, Roblox Color3 is sRGB; copying the linear
-- numbers straight across gives a part about a third as bright as the render).
--
-- Run from the Studio command bar, or via MCP. It only touches Color / Material on
-- MeshParts: it does not rename, reparent, move or delete anything (CLAUDE.md 6).

local CONFIG = {
	-- Parent of the imported parts. Scanned for MeshParts if it is a Folder/Model;
	-- if nil, the whole Workspace is scanned for parts named like the file.
	Root = nil,
	NamePrefix = "ChamberWall24",
	-- A match must beat the second-best row by this relative margin, or the part is
	-- reported AMBIGUOUS and left alone.
	MinMargin = 0.02,
	-- Report the raw sizes it saw even when everything matches. This is the line
	-- that tells you the importer's scale is not what you assumed.
	AlwaysReportSizes = true,
}

-- One row per glTF primitive, in the order the exporter wrote them. Sizes are in
-- the Roblox frame (Y up) as they land at the FBX importer's 5.902 studs/unit;
-- ratios are what the matcher actually uses.
local DESIGN = {
	{
		mat = "WallBase", material = Enum.Material.Metal, color = Color3.fromRGB(162, 166, 172),
		size = { 129.39, 1.20, 129.39 },
		note = "18-sided collar sitting on the platform rim",
	},
	{
		mat = "WallBand", material = Enum.Material.Metal, color = Color3.fromRGB(221, 196, 149),
		size = { 137.17, 3.00, 137.17 },
		note = "the 18->24 bridge, 42 triangles per surface",
	},
	{
		mat = "WallTop", material = Enum.Material.Metal, color = Color3.fromRGB(200, 205, 209),
		size = { 137.17, 9.00, 137.17 },
		note = "the 24-sided wall",
	},
}

-- ============================================================ collection

local function collect()
	if CONFIG.Root then
		local root = typeof(CONFIG.Root) == "Instance" and CONFIG.Root
			or game:GetService("Workspace"):FindFirstChild(CONFIG.Root, true)
		if not root then
			return nil, "no instance at Root"
		end
		local out = {}
		if root:IsA("MeshPart") then
			table.insert(out, root)
		end
		for _, d in ipairs(root:GetDescendants()) do
			if d:IsA("MeshPart") then
				table.insert(out, d)
			end
		end
		if #out == 0 then
			return nil, "Root holds no MeshParts"
		end
		return out
	end

	-- Fall back to a place-wide search, but ONLY by the file's name. A bare
	-- "every MeshPart in Workspace" sweep would happily repaint the laser port.
	local out = {}
	for _, d in ipairs(game:GetService("Workspace"):GetDescendants()) do
		if d:IsA("MeshPart") and string.find(d.Name, CONFIG.NamePrefix, 1, true) == 1 then
			table.insert(out, d)
		end
	end
	if #out == 0 then
		return nil, "no MeshPart named " .. CONFIG.NamePrefix .. "* in Workspace"
	end
	return out, nil
end

-- ============================================================ matching

-- Signed relative distance from a row to a part, summed over the three axes after
-- dividing EACH by its own largest dimension. Both sides normalised is the point:
-- the score then depends only on proportions, and not at all on how big the import
-- came in.
local function shape(v)
	local m = math.max(v.X, v.Y, v.Z)
	if m <= 0 then
		return { 0, 0, 0 }
	end
	return { v.X / m, v.Y / m, v.Z / m }
end

local function distance(row, size)
	local got = shape(size)
	local want = row.ratios
	-- X, Y, Z -- row.ratios is built in that same order from row.size.
	local sum, n = 0, 0
	for i = 1, 3 do
		if want[i] > 1e-9 then
			sum = sum + math.abs(got[i] - want[i]) / want[i]
			n = n + 1
		end
	end
	return sum / math.max(n, 1)
end

-- Precompute each row's ratios once, and keep the row's own max so the report can
-- say what scale the table assumes.
for _, row in ipairs(DESIGN) do
	local m = math.max(row.size[1], row.size[2], row.size[3])
	row.ratios = { row.size[1] / m, row.size[2] / m, row.size[3] / m }
	row.max = m
end

local function matchPart(part)
	local scores = {}
	for i, row in ipairs(DESIGN) do
		table.insert(scores, { i = i, row = row, d = distance(row, part.Size) })
	end
	table.sort(scores, function(a, b)
		return a.d < b.d
	end)
	local best, second = scores[1], scores[2]
	if #scores > 1 then
		local margin = (second.d - best.d) / math.max(best.d, 1e-9)
		if margin < CONFIG.MinMargin then
			return nil, string.format("AMBIGUOUS (%s vs %s: %.4f vs %.4f)",
				best.row.mat, second.row.mat, best.d, second.d)
		end
	end
	-- And an absolute sanity gate: even an unambiguous best is only a match if it
	-- is actually close. With three rows, the winner is always one of them.
	if best.d > 0.15 then
		return nil, string.format("UNMATCHED (closest %s, score %.4f)", best.row.mat, best.d)
	end
	return best.row, nil
end

-- ============================================================ run

local parts, err = collect()
if not parts then
	warn("[chamberwall] " .. err .. " -- nothing painted")
	return
end

local widest = 0
for _, p in ipairs(parts) do
	widest = math.max(widest, p.Size.X, p.Size.Z)
end

print(string.format("[chamberwall] %d MeshPart(s), widest X/Z = %.3f studs "
	.. "(design 137.170, so the import factor is %.4f)",
	#parts, widest, widest / 137.170))
if CONFIG.AlwaysReportSizes then
	for _, p in ipairs(parts) do
		local s = shape(p.Size)
		print(string.format("    %-28s %8.3f x %7.3f x %8.3f   ratios (%.5f, %.5f)",
			p:GetFullName(), p.Size.X, p.Size.Y, p.Size.Z, s[1], s[2]))
	end
end

local painted, skipped = 0, 0
for _, p in ipairs(parts) do
	local row, why = matchPart(p)
	if not row then
		skipped = skipped + 1
		warn(string.format("[chamberwall] %s: %s -- left as it is", p:GetFullName(), why))
	else
		p.Material = row.material
		p.Color = row.color
		painted = painted + 1
		print(string.format("[chamberwall] %s -> %s %s   (%s)",
			p:GetFullName(), row.mat,
			tostring(row.color), row.note))
	end
end

print(string.format("[chamberwall] painted %d, skipped %d", painted, skipped))
if painted == 0 then
	warn("[chamberwall] nothing painted. If the sizes above are not the design "
		.. "sizes, the import scale is not what this table assumes -- fix the "
		.. "table, do not loosen the matcher.")
end
