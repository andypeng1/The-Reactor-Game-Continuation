-- apply_laser_port_materials.luau
--
-- WHY THIS EXISTS. Roblox's 3D importer splits an imported mesh into one MeshPart
-- per material -- which is exactly the split we want -- but it throws the
-- materials away: every part comes in as Material.Plastic with a grey Color and an
-- empty TextureID. (Measured 2026-10-04: 11 parts, Material=Plastic, Color
-- 0.196/0.275/0.353 -- a per-NODE grey, not even per-material.)
--
-- The colours were never missing from the file. They are in there as glTF
-- `baseColorFactor` values, but a MeshPart has exactly ONE Color, ONE Material and
-- an optional TextureID -- there is no per-face slot for a material factor to land
-- in. So the only way a flat-colour mesh arrives coloured is if somebody sets the
-- properties afterwards. This is that somebody.
--
-- HOW IT FINDS THE RIGHT PART. Not by name order -- by SIZE. The importer's
-- naming (Foo, Foo2, Foo3 ...) happens to follow the primitive order today, but
-- that is the importer's business, not a promise. Each primitive's bounding box is
-- a design constant, so this matches every part against the design table by shape,
-- and REFUSES a match that is not clearly better than the runner-up. A silent
-- mis-pairing would paint the wrong colour on the wrong piece and look deliberate
-- (CLAUDE.md 0.18: a wrong measurement does not error, it just quietly gives you a
-- number).
--
-- COLOURS. Blender's base colours are LINEAR; Roblox's Color3 is sRGB. The RGB
-- triplets below are the linear values put through the sRGB transfer function --
-- copying the linear numbers straight across would have produced a part about a
-- third as bright as the render the operator approved.
--
-- Run from the Studio command bar, or via MCP. It only touches Color / Material on
-- MeshParts: it does not rename, reparent, move or delete anything (CLAUDE.md 6).

local CONFIG = {
	-- Recolouring an already-correct part is harmless, but the size check is the
	-- point, so leave this on.
	VerifySizes = true,
	-- A match must beat the second-best candidate by this relative margin, or the
	-- part is reported AMBIGUOUS and left alone.
	MinMargin = 0.02,
}

-- One row per glTF primitive, in the order the exporter wrote them. Sizes are in
-- the glTF frame (Y up) -- which is the frame Roblox reports -- taken from the
-- accessors in Laser{Emitter,Receiver}Port.glb.
local DESIGN = {
	Base = {
		{ mat = "PortMount", size = { 1.300, 1.600, 1.600 } },
		{ mat = "PortDark", size = { 0.170, 1.289, 1.289 } },
		{ mat = "PortCoolant", size = { 0.269, 0.269, 0.960 } },
	},
	Yoke = {
		{ mat = "PortMount", size = { 0.680, 0.930, 1.980 } },
		{ mat = "PortBody", size = { 0.680, 0.900, 1.760 } },
		{ mat = "PortDark", size = { 0.374, 0.380, 1.980 } },
	},
	EmitterHead = {
		{ mat = "PortMount", size = { 1.720, 1.360, 1.360 } },
		{ mat = "PortBody", size = { 0.820, 0.920, 0.920 } },
		{ mat = "PortDark", size = { 1.520, 1.360, 1.360 } },
		{ mat = "PortCoolant", size = { 0.321, 0.257, 1.090 } },
		{ mat = "PortLensEmit", size = { 0.100, 0.624, 0.624 } },
	},
	ReceiverHead = {
		{ mat = "PortMount", size = { 1.524, 1.542, 1.542 } },
		{ mat = "PortBody", size = { 0.660, 0.920, 0.920 } },
		{ mat = "PortDark", size = { 1.280, 1.542, 1.542 } },
		{ mat = "PortCoolant", size = { 0.313, 0.253, 1.083 } },
		{ mat = "PortLensRecv", size = { 0.120, 0.260, 0.260 } },
	},
}

-- Roblox Material + Color per named material. The four metals share one Roblox
-- Material and differ only in colour, which is what they were in Blender too (all
-- four had metallic 0.7-0.9 and no texture). The lenses are Neon: an emissive flat
-- colour is the one thing a Roblox Material cannot express, and a glowing port is
-- the whole point of the lens.
local LOOK = {
	PortMount = { material = Enum.Material.Metal, rgb = { 101, 105, 110 } },
	PortBody = { material = Enum.Material.Metal, rgb = { 173, 177, 182 } },
	PortDark = { material = Enum.Material.Metal, rgb = { 77, 80, 85 } },
	PortCoolant = { material = Enum.Material.Metal, rgb = { 200, 155, 108 } },
	PortLensEmit = { material = Enum.Material.Neon, rgb = { 249, 153, 89 } },
	PortLensRecv = { material = Enum.Material.Neon, rgb = { 111, 237, 173 } },
}

local function axis(v, i)
	return (i == 1 and v.X) or (i == 2 and v.Y) or v.Z
end

-- Best-fitting row of `table_` for an observed Size. The scale is fitted per
-- candidate (an imported model has no promise of any particular scale), so the
-- comparison is shape-only. Returns row, scale, and the relative error.
local function bestRow(size, table_)
	local best, bestErr, secondErr, bestScale
	for _, row in ipairs(table_) do
		local k = 0
		for i = 1, 3 do
			k = k + axis(size, i) / row.size[i]
		end
		k = k / 3
		local err = 0
		for i = 1, 3 do
			local d = axis(size, i) / (row.size[i] * k) - 1
			err = err + d * d
		end
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

local function colourPort(root)
	local report, painted, skipped = {}, 0, 0
	for _, node in ipairs(root:GetDescendants()) do
		if not node:IsA("Model") or not node.Name:match("_Node$") then
			continue
		end
		local kind = nodeKind(node.Name)
		if not kind then
			table.insert(report, ("  %-28s skipped: no design table for this name"):format(node.Name))
			continue
		end
		local scales = {}
		for _, part in ipairs(node:GetChildren()) do
			if part:IsA("MeshPart") then
				local row, k, err, second = bestRow(part.Size, DESIGN[kind])
				local margin = (second and (second - err)) or 1
				if CONFIG.VerifySizes and margin < CONFIG.MinMargin then
					table.insert(report, ("  %-28s AMBIGUOUS (err %.4f vs %.4f) -- left untouched")
						:format(part.Name, err, second or -1))
					skipped = skipped + 1
				else
					local look = LOOK[row.mat]
					part.Material = look.material
					part.Color = Color3.fromRGB(look.rgb[1], look.rgb[2], look.rgb[3])
					table.insert(scales, k)
					table.insert(report, ("  %-28s -> %-13s %-8s rgb(%d,%d,%d)  scale=%.4f err=%.4f")
						:format(part.Name, row.mat, look.material.Name,
							look.rgb[1], look.rgb[2], look.rgb[3], k, err))
					painted = painted + 1
				end
			end
		end
		-- Every part of one node comes from one exported node, so one import scale.
		-- A spread here means the matching is wrong even though each row "fitted".
		if #scales > 1 then
			local lo, hi = scales[1], scales[1]
			for _, k in ipairs(scales) do
				lo, hi = math.min(lo, k), math.max(hi, k)
			end
			if hi / lo - 1 > 0.01 then
				table.insert(report, ("  *** %s: parts disagree on the import scale (%.4f..%.4f) ***")
					:format(node.Name, lo, hi))
			end
		end
	end
	return report, painted, skipped
end

local targets = {}
for _, obj in ipairs(workspace:GetDescendants()) do
	if obj:IsA("Model") and obj.Name:match("_Node$") then
		-- Two nodes sharing a parent are one imported assembly; colour the parent.
		local p = obj.Parent
		if p and not targets[p] then
			targets[p] = true
		end
	end
end

local lines, total, skippedAll = {}, 0, 0
for root in pairs(targets) do
	table.insert(lines, ("== %s"):format(root:GetFullName()))
	local rep, painted, skipped = colourPort(root)
	for _, line in ipairs(rep) do
		table.insert(lines, line)
	end
	total, skippedAll = total + painted, skippedAll + skipped
end
if total == 0 and skippedAll == 0 then
	table.insert(lines, "no *_Node models found under Workspace -- import the model first")
end
table.insert(lines, ("painted %d part(s), %d skipped"):format(total, skippedAll))

-- Both channels, because neither is guaranteed: the MCP tool returns the chunk's
-- value, the console carries the prints. Same rule as CLAUDE.md 0.17 -- the two
-- toolchains each carry half, and a silent empty return is indistinguishable from
-- "nothing to do". The separator is built by concatenation, not an escape: text
-- pushed through the Studio tool layer is decoded once (CLAUDE.md 0.10), so a
-- literal backslash-n in this file would become a real newline inside the
-- string literal and break the parse.
local SEP = string.char(10)
for _, line in ipairs(lines) do
	print(line)
end
return table.concat(lines, SEP)
