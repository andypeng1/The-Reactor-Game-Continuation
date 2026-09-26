assert(game.PlaceId == 83752844701736, 'Wrong target place')
local out = {manual={}, sources={}, references={}}
local manual = workspace.Consoles.ElectricGridConsole.DRMScreen
for _, node in ipairs(manual:GetDescendants()) do
    if node:IsA('TextLabel') then
        local path = node:GetFullName()
        if string.find(path, 'BasicsFrame', 1, true) or string.find(path, 'MainConsFrame', 1, true)
            or string.find(path, 'ThermalConsFrame', 1, true) then
            table.insert(out.manual, {path=path, text=node.Text})
        end
    end
end
for _, node in ipairs(game:GetDescendants()) do
    if node:IsA('LuaSourceContainer') and not node:IsDescendantOf(game.ServerStorage.Data) then
        if node.Name == 'EndShiftHandler' then out.sources[node:GetFullName()] = node.Source end
        for _, pattern in ipairs({'workspace:GetChildren', 'Workspace:GetChildren', 'workspace.Part', 'Workspace.Part', 'workspace.Model', 'Workspace.Model', 'CulledParts'}) do
            if string.find(node.Source, pattern, 1, true) then
                table.insert(out.references, {path=node:GetFullName(), pattern=pattern})
            end
        end
    end
end
return game:GetService('HttpService'):JSONEncode(out)
