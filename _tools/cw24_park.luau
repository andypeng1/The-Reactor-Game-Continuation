-- cw24_park.luau -- move the imported Wall24 aside, and prove the world agrees.
--
-- Operator's call, asked before touching Workspace because a visible part leaving
-- Workspace IS a change to the world (CLAUDE.md 0.12 note 3): park it, do not
-- delete it. ServerStorage is where this project parks things -- the parts stop
-- rendering and stop simulating, and nothing is lost.
--
-- The guard matters more than the move: a script that relocates whatever it finds
-- under a name is a script that will one day relocate the wrong thing. This one
-- asserts the shape it expects, and refuses if the name resolves to something
-- else.
local NAME = "Wall24"
local DEST = "Wall24_import_20261004"
local CENTRE = Vector3.new(-12.1999, 47.4000, -85.3624)

local out = {}
local function say(fmt, ...)
	out[#out + 1] = select("#", ...) > 0 and string.format(fmt, ...) or fmt
end

-- The service globals are not all present in every VM this runs in; asking for
-- them by name costs nothing and removes the guess.
local ServerStorage = game:GetService("ServerStorage")
local workspace = game:GetService("Workspace")

local src = workspace:FindFirstChild(NAME)
if not src then
	return "nothing named " .. NAME .. " under Workspace -- refusing to guess"
end

-- Count what is being moved, so the record says what left the world rather than
-- merely that something did.
--
-- The offset printed per part is the distance from the RING'S axis to that part's
-- own pivot -- i.e. the placement error, not the ring's radius. The rings sit at
-- 67.74..74.73 (measured by a 360-ray sweep in cw24_import.luau); the pivots are
-- what carry the 0.873 offset, and those are two different numbers that a single
-- radial figure would happily merge into one wrong one (CLAUDE.md 0.18).
local parts = {}
for _, d in ipairs(src:GetDescendants()) do
	if d:IsA("BasePart") then
		parts[#parts + 1] = d
	end
end
if #parts == 0 then
	return NAME .. " holds no parts -- refusing to move an empty container blind"
end
say("about to park %s: %d parts", src:GetFullName(), #parts)
for _, p in ipairs(parts) do
	say("  %-34s %-9s pivotOffset %8.4f  y %8.4f  Anchored %s  CanCollide %s  size %s",
		p.Name, p.ClassName,
		(Vector3.new(p.Position.X - CENTRE.X, 0, p.Position.Z - CENTRE.Z)).Magnitude,
		p.Position.Y, tostring(p.Anchored), tostring(p.CanCollide), tostring(p.Size))
end

-- ============================================================ move

local dest = ServerStorage:FindFirstChild(DEST)
if dest then
	return "ServerStorage already has " .. DEST .. " -- refusing to overwrite it"
end

local ok, err = pcall(function()
	src.Parent = ServerStorage
end)
if not ok then
	return "move failed: " .. tostring(err)
end

local moved = ServerStorage:FindFirstChild(NAME)
if not moved then
	return "the container is neither in Workspace nor in ServerStorage -- investigate"
end
local okName, errName = pcall(function()
	moved.Name = DEST
end)
if not okName then
	say("warning: could not rename to %s (%s); it is parked under its old name", DEST, tostring(errName))
end
say("parked as %s", moved:GetFullName())

-- ============================================================ prove it

say("")
say("---- the world after ----")
local left = 0
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("MeshPart") and string.find(d.Name, "ChamberWall") then
		left += 1
		say("  %s   CanCollide %s  CanQuery %s", d:GetFullName(),
			tostring(d.CanCollide), tostring(d.CanQuery))
	end
end
say("MeshParts named ChamberWall* still under Workspace: %d  (was 4, want 1)", left)

-- The one thing that must still be true: the built wall is there, and the three
-- rings that were 3 studs proud of the joint are not.
local built = workspace:FindFirstChild("ChamberWall24", true)
say("built wall present under Workspace: %s", tostring(built ~= nil))
if built then
	say("  %s  position %s", built:GetFullName(), tostring(built.Position))
end

return table.concat(out, string.char(10))
