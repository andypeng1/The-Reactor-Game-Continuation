--[[
	shell_audit.lua -- the repeatable version of the facility-shell measurement.

	Run through GameCore's command-bar bus or straight into rblx_execute_luau (Edit data model).
	It writes nothing. It exists because round 8's decisive query was the only thing that stopped a
	378,704-stud "correction" of a wall family that turned out to be the room's dominant tone, and a
	query that lives only in a transcript is a query the next round will re-invent wrongly.

	THE THREE INSTRUMENTS, in the order they are worth trusting:

	  1. TONE HISTOGRAM, FULL RANGE. Every non-Neon part in a subtree, 16-wide luminance buckets.
	     This is the honest one. A room whose ladder runs continuously 0..255 with the mass at its
	     mode is authored; a room with a clear ladder and two things outside it has a defect.

	  2. LARGE-FACE HISTOGRAM. Same thing restricted to face >= 300.
	     THIS IS THE ONE THAT LIES, and it is the one everybody reaches for first, because a big
	     bright surface is what the eye notices. Inside the reactor chamber the two histograms
	     disagree completely: 980 of the 1,138 non-Neon parts in the 190-223 band ARE the walls, so
	     filtering to large faces keeps the walls and hides the ladder they sit in. If you only run
	     this one you will conclude the modal tone of the room is an outlier. Run both.

	  3. MATERIAL-ROLE MISMATCH. A horizontal slab (thin axis Y) wearing FacilityFloorPlate in the
	     top quarter of its container -- floor material overhead. This is the instrument that found
	     round 7's ceiling, and it is the only one of the three that has ever found a real defect.
	     Note its structural limit: it compares against the CONTAINER's vertical span, so for a
	     container holding two rooms (CullFolder spans 0..506) "top quarter" is not a ceiling.

	A TONE-DISTANCE RULE IS NOT AN INSTRUMENT. Flagging every large-surface family more than 64
	luminance from its container's own large-surface mode flags CullFolder's two rooms against each
	other and nothing else. Round 7 shipped that mistake once already, as a blanket luminance
	threshold that would have greyed 25 light plates and 2 amber signal lights.

	Whatever it reports, confirm before writing: compare against the room's own ladder, and check
	that the offending parts are not fittings, not detail trim, and not text.
]]

local LUM = function(c) return (c.R * 0.299 + c.G * 0.587 + c.B * 0.114) * 255 end

local function faceAreaAndThin(part)
	local s = part.Size
	local a, b, c = s.X, s.Y, s.Z
	if b > a then a, b = b, a end
	if c > b then b, c = c, b end
	return a * b, c
end

-- Container names are matched on the way UP from the part, so a part is "in wall scope" when any
-- ancestor's name contains the word. That is what keeps the effect hosts that share the wall tone
-- (METU's VentParticle, the CoolantReserviors processors) out of reach.
local function namedScope(part, word)
	local node = part
	while node and node ~= workspace do
		if string.find(string.lower(node.Name), word, 1, true) then return true end
		node = node.Parent
	end
	return false
end

local function resolve(path)
	local node = workspace
	for seg in string.gmatch(path, "[^%.]+") do
		node = node and node:FindFirstChild(seg)
	end
	return node
end

local function histogram(node, opts)
	local all, big = {}, {}
	local total, nBig, seen = 0, 0, {}
	for _, d in ipairs(node:GetDescendants()) do
		if d:IsA("BasePart") and not seen[d] then
			seen[d] = true
			if d.Material ~= Enum.Material.Neon then
				if not opts.scopeWord or namedScope(d, opts.scopeWord) then
					local L = LUM(d.Color)
					local face, thin = faceAreaAndThin(d)
					if not opts.maxThin or thin <= opts.maxThin then
						total = total + 1
						local k = math.floor(L / 16) * 16
						all[k] = (all[k] or 0) + 1
						if face >= 300 then
							nBig = nBig + 1
							big[k] = (big[k] or 0) + 1
						end
					end
				end
			end
		end
	end
	return all, big, total, nBig
end

local function render(h, total)
	local a = {}
	for k, v in pairs(h) do a[#a+1] = { k, v } end
	table.sort(a, function(x, y) return tonumber(x[1]) < tonumber(y[1]) end)
	local s = {}
	for _, e in ipairs(a) do s[#s+1] = string.format("%d-%d=%d", e[1], e[1] + 15, e[2]) end
	return string.format("n=%d  %s", total, table.concat(s, "  "))
end

-- ========== REPORT ==========
local out = {}
local TARGETS = {
	{ label = "reactor-chamber wall subtrees", containers = { "ChamberWalls", "CullFolder.ReactorChamber", "Mainframe" }, scopeWord = "wall" },
}

for _, t in ipairs(TARGETS) do
	out[#out+1] = "== " .. t.label .. " =="
	for _, path in ipairs(t.containers) do
		local node = resolve(path)
		if node then
			local all, big, total, nBig = histogram(node, { scopeWord = t.scopeWord, maxThin = 20 })
			out[#out+1] = "  " .. path .. " FULL  " .. render(all, total)
			out[#out+1] = "  " .. path .. " BIG   " .. render(big, nBig)
		else
			out[#out+1] = "  " .. path .. " -> NOT FOUND"
		end
	end
	out[#out+1] = ""
end

-- Per-top-level-container overview: total, Neon, large-face count, and the modes of both ladders.
local SKIP = { GameCoreTests = true, _MCPVisualTracking = true }
out[#out+1] = "== per container =="
local rows = {}
for _, top in ipairs(workspace:GetChildren()) do
	if (top:IsA("Model") or top:IsA("Folder")) and not SKIP[top.Name] then
		local all, big, total, nBig = histogram(top, { maxThin = 20 })
		local function mode(h)
			local best, bm = 0, nil
			for k, v in pairs(h) do if v > best then best, bm = v, k end end
			return bm, best
		end
		local am, ac = mode(all)
		local bm, bc = mode(big)
		rows[#rows+1] = string.format("  %-24s total=%6d big=%4d  allMode=%s(%d)  bigMode=%s(%d)",
			top.Name, total, nBig,
			am and tostring(am) or "-", ac, bm and tostring(bm) or "-", bc)
	end
end
table.sort(rows)
for _, r in ipairs(rows) do out[#out+1] = r end

return table.concat(out, string.char(10))
