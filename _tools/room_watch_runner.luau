-- Starts the room watcher.  Deleting this instance, or removing the runner
-- from ServerScriptService, stops the watcher from running on server start.
-- The watcher itself is MCP_RoomWatch next to this script and it writes
-- nothing back into the world: every read it makes is a property get.
--
-- NOT INSTALLED AS OF 2026-09-27 (QUESTIONS.md D11:B).  Both this and
-- MCP_RoomWatch were deleted from the AIRemake place, because the monitoring
-- the operator actually asked for is of the ORIGINAL game and this place is
-- not it -- see PROGRESS.md Phase 54.  Nothing here is stale: this file and
-- MCP_RoomWatch are kept as the way to put the watcher back, and the sink it
-- posts to is port 8771, NOT the 8765 the original-game scripts use.
local ok, err = pcall(function()
    require(script.Parent.MCP_RoomWatch).Start()
end)
if not ok then
    warn('[RoomWatch] failed to start: ' .. tostring(err))
end
