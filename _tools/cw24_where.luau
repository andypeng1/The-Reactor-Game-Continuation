-- cw24_where.luau -- WHO ELSE is called ChamberWall24, and where does the world
-- actually have surfaces between the centre and rho 200?
--
-- Two things went wrong in the previous probe and both of them were mine:
--
--   1. The world scan reported a radius as (200 - hit.Distance) while advancing
--      the origin by (hit.Distance + 0.05) each step. That formula is only true
--      for the FIRST hit of each line; every radius after it is measured from the
--      wrong place. Reprinting it with an absolute x is the fix.
--
--   2. It found THREE things named ChamberWall24*. The build was written to create
--      one. Either it ran more than once, or those parts are not mine -- and the
--      answer changes what to do next, so it gets measured rather than guessed.
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

-- ============================================================ who is ChamberWall*

say("==== every instance named like ChamberWall ====")
local found = {}
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("BasePart") and string.find(d.Name, "ChamberWall") then
		found[#found + 1] = d
	end
end
table.sort(found, function(a, b)
	return a:GetFullName() < b:GetFullName()
end)
say("%d found", #found)
local contentOf = {}
for i, p in ipairs(found) do
	local cx = p:IsA("MeshPart") and tostring(p.MeshContent) or "-"
	contentOf[p] = cx
	local cf = p.CFrame
	say("%2d %-46s %-9s", i, p:GetFullName(), p.ClassName)
	say("     pos %10.4f %10.4f %10.4f   size %9.4f %8.4f %9.4f",
		p.Position.X, p.Position.Y, p.Position.Z, p.Size.X, p.Size.Y, p.Size.Z)
	say("     look %8.5f %8.5f %8.5f   up %8.5f %8.5f %8.5f   right %8.5f %8.5f %8.5f",
		cf.LookVector.X, cf.LookVector.Y, cf.LookVector.Z,
		cf.UpVector.X, cf.UpVector.Y, cf.UpVector.Z,
		cf.RightVector.X, cf.RightVector.Y, cf.RightVector.Z)
	say("     content %s", cx)
end
-- Same stored mesh, or three separate meshes? One shared Content means one mesh
-- placed three times; three different Contents mean three builds.
for i = 1, #found do
	for j = i + 1, #found do
		if contentOf[found[i]] == contentOf[found[j]] then
			say("SHARED MESH: %s and %s hold the same MeshContent", found[i].Name, found[j].Name)
		end
	end
end

-- Offset of each from the centre, in the plane. A copy placed from the same
-- constants sits at the same offset; one placed from different constants does not.
say("")
say("==== offsets from CENTRE ====")
for _, p in ipairs(found) do
	say("%-46s d %9.4f %9.4f %9.4f   |dxy| %9.4f",
		p:GetFullName(),
		p.Position.X - CENTRE.X, p.Position.Y - CENTRE.Y, p.Position.Z - CENTRE.Z,
		(Vector3.new(p.Position.X - CENTRE.X, 0, p.Position.Z - CENTRE.Z)).Magnitude)
end

-- ============================================================ world scan, done right

say("")
say("==== surfaces from rho 200 inward (absolute x) ====")
-- One ray per height, walked inward. x is tracked explicitly so every radius is
-- measured from the same origin.
local heights = { 46.0, 47.4, 48.6, 50.0, 51.6, 55.0, 60.6, 62.0 }
for _, y in ipairs(heights) do
	local x = CENTRE.X + 200
	local line = {}
	for _ = 1, 14 do
		local h = workspace:Raycast(Vector3.new(x, y, CENTRE.Z), Vector3.new(-400, 0, 0))
		if not h then
			break
		end
		local hitX = x - h.Distance
		line[#line + 1] = string.format("%.3f %s", hitX - CENTRE.X, h.Instance.Name)
		x = hitX - 0.05
		if x < CENTRE.X - 200 then
			break
		end
	end
	say("y=%6.2f  %s", y, table.concat(line, "  |  "))
end

-- ============================================================ what is the ring

say("")
say("==== any instance named exactly '18' ====")
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "18" and (d:IsA("Folder") or d:IsA("Model")) then
		local n = 0
		for _, c in ipairs(d:GetChildren()) do
			if c:IsA("BasePart") then
				n += 1
			end
		end
		say("%s  parts %d", d:GetFullName(), n)
	end
end

return table.concat(out, string.char(10))
