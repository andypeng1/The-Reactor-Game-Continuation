-- Read-only audit: retain exact source separately from summarized instance data.
assert(game.PlaceId == 83752844701736, 'Wrong target place')
local http = game:GetService('HttpService')
local out = {placeId = game.PlaceId, roots = {}, scripts = {}, controls = {}, manual = {}, stats = {}}
local counts = {}
for _, child in ipairs(workspace:GetChildren()) do
    local key = child.ClassName .. ':' .. child.Name
    counts[key] = (counts[key] or 0) + 1
end
out.roots = counts
for _, node in ipairs(game:GetDescendants()) do
    if node:IsA('LuaSourceContainer') and not node:IsDescendantOf(game.ServerStorage.Data) then
        local source = node.Source
        local placeholder = string.find(source, 'Server Scripts are IMPOSSIBLE to save', 1, true) ~= nil
        table.insert(out.scripts, {path=node:GetFullName(), class=node.ClassName, length=#source,
            placeholder=placeholder,
            disabled=node:IsA('BaseScript') and node.Disabled or nil})
    end
end
for _, node in ipairs(workspace.Consoles:GetDescendants()) do
    if node:IsA('ClickDetector') then
        local part = node.Parent
        local label = part:FindFirstChild('ClickPartText')
        local desc = part:FindFirstChild('DescriptionText')
        table.insert(out.controls, {path=part:GetFullName(), label=label and label.Value,
            description=desc and desc.Value, position=part:IsA('BasePart') and tostring(part.Position) or nil})
    end
end
local manual = nil -- Authored manual is exported separately to avoid the 100 KB tool ceiling.
if manual then
    for _, node in ipairs(manual:GetDescendants()) do
        if node:IsA('TextLabel') or node:IsA('TextButton') then
            if #node.Text > 35 then table.insert(out.manual, {path=node:GetFullName(), text=node.Text}) end
        end
    end
end
for _, node in ipairs(workspace.Stats:GetDescendants()) do
    if node:IsA('ValueBase') then out.stats[node:GetFullName()] = tostring(node.Value) end
end
return http:JSONEncode(out)
