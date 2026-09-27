-- Starts the room watcher.  Deleting this instance, or removing the runner
-- from ServerScriptService, stops the watcher from running on server start.
-- The watcher itself is MCP_RoomWatch next to this script and it writes
-- nothing back into the world: every read it makes is a property get.
local ok, err = pcall(function()
    require(script.Parent.MCP_RoomWatch).Start()
end)
if not ok then
    warn('[RoomWatch] failed to start: ' .. tostring(err))
end
