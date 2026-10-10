-- ==== GravityLens client boot ====
--
-- Why the lens is built by a CLIENT script and not by a server one (Phase 110).
--
-- A MeshPart whose MeshContent is an EditableMesh OBJECT does not carry that mesh
-- across the network. The object lives in the process that made it. Measured on
-- 2026-10-10, same instance, same call:
--     Edit process   CreateEditableMeshAsync(part.MeshContent) -> 9728 verts,
--                    bounds (-46 -46 -11) .. (46 46 -0.70)      <- the lens
--     Play client    the identical call                         -> 1536 verts,
--                    bounds (0 0 0) .. (1 1 1)                  <- a unit cube
-- The client is never told "no". It is handed a default block, so every client
-- drew a one-stud cube exactly where the 92-stud sheet should be. That is the
-- small block the operator saw after entering Play.
--
-- The cure is not to ship the mesh, it is to build it where it is drawn. The
-- server keeps Workspace.GravityLens as the authored PLACEMENT; this script reads
-- that placement, builds the real mesh in the client process, animates it there,
-- and then removes the replicated frame that would otherwise remain a cube.
--
-- If the mesh API is refused the module says so once and leaves nothing standing
-- -- nothing is more honest than a block pretending to be a lens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local mod = ReplicatedStorage:WaitForChild("GravityLens", 30)
if mod == nil then
	warn("[GravityLens] boot: ReplicatedStorage.GravityLens never arrived")
else
	local ok, err = pcall(function()
		require(mod).start()
	end)
	if not ok then
		warn("[GravityLens] boot failed: " .. tostring(err))
	end
end
