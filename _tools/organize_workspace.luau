assert(game.PlaceId == 83752844701736, 'Wrong target place')
assert(not game:GetService('RunService'):IsRunning(), 'Edit mode required')
local ss = game:GetService('ServerStorage')
local backend = game.ServerScriptService:FindFirstChild('ReactorBackend')
assert(backend, 'Expected scaffold missing')
local base = ss:FindFirstChild('BackendBaseline20260925')
if not base then
    base = Instance.new('Folder')
    base.Name = 'BackendBaseline20260925'
    base.Parent = ss
    local clone = backend:Clone()
    clone.Name = 'OriginalScaffold'
    clone.Parent = base
end
local sources = {}
for _, node in ipairs(game:GetDescendants()) do
    if node:IsA('LuaSourceContainer') and not node:IsDescendantOf(ss) then
        table.insert(sources, node.Source)
    end
end
local generic = {Part=true, Line=true, Wedge=true, Union=true, MeshPart=true}
local safeChildren = {Decal=true, Texture=true, SpecialMesh=true, BlockMesh=true, CylinderMesh=true, SurfaceAppearance=true}
local candidates = {}
local skipped = 0
for _, node in ipairs(workspace:GetChildren()) do
    if node:IsA('BasePart') and node.Anchored and generic[node.Name] then
        local safe = #node:GetTags() == 0 and next(node:GetAttributes()) == nil
        for _, child in ipairs(node:GetDescendants()) do
            if not safeChildren[child.ClassName] then safe = false end
        end
        -- Broad name hits intentionally over-exclude: uncertain dependencies stay put.
        for _, source in ipairs(sources) do
            if string.find(source, '.' .. node.Name, 1, true)
                or string.find(source, "'" .. node.Name .. "'", 1, true)
                or string.find(source, string.char(34) .. node.Name .. string.char(34), 1, true) then
                safe = false
                break
            end
        end
        if safe then table.insert(candidates, node) else skipped += 1 end
    end
end
local geometry = workspace:FindFirstChild('Geometry')
if not geometry then geometry = Instance.new('Folder'); geometry.Name='Geometry'; geometry.Parent=workspace end
assert(geometry:IsA('Folder'), 'Geometry name collision')
local record = base:FindFirstChild('WorkspaceMoves')
if not record then record=Instance.new('Folder'); record.Name='WorkspaceMoves'; record.Parent=base end
local beforeParts, afterParts = 0, 0
for _, node in ipairs(workspace:GetDescendants()) do if node:IsA('BasePart') then beforeParts += 1 end end
local moved = 0
for _, node in ipairs(candidates) do
    local frame, size, color, material = node.CFrame, node.Size, node.Color, node.Material
    local reference = Instance.new('ObjectValue')
    reference.Name = string.format('Move_%04d', #record:GetChildren() + 1)
    reference.Value = node
    reference:SetAttribute('OriginalParent', 'Workspace')
    reference:SetAttribute('OriginalName', node.Name)
    reference:SetAttribute('OriginalCFrame', frame)
    reference:SetAttribute('OriginalSize', size)
    reference.Parent = record
    node.Parent = geometry
    assert(node.CFrame == frame and node.Size == size and node.Color == color and node.Material == material, 'Geometry drift')
    moved += 1
end
for _, node in ipairs(workspace:GetDescendants()) do if node:IsA('BasePart') then afterParts += 1 end end
assert(beforeParts == afterParts, 'Part count changed')
local body = 'Workspace organization 2026-09-25: moved ' .. moved .. ' verified unreferenced anchored decorative parts into Workspace.Geometry. '
    .. 'Skipped ' .. skipped .. ' uncertain candidates. BasePart count unchanged: ' .. beforeParts .. '. '
    .. 'All moved CFrames, sizes, colors and materials checked unchanged. '
    .. 'No names changed, nothing deleted, no functional objects moved. '
    .. 'Rollback: ServerStorage.BackendBaseline20260925.WorkspaceMoves ObjectValues retain each original parent and instance. '
    .. 'The existing shadow scaffold is not a finished gameplay backend.'
local progress = backend:FindFirstChild('PROGRESS') or Instance.new('ModuleScript')
progress.Name='PROGRESS'; progress.Source='return [==[' .. body .. ']==]'; progress.Parent=backend
local decisions = backend:FindFirstChild('DECISIONS') or Instance.new('ModuleScript')
decisions.Name='DECISIONS'; decisions.Source='return [==[This place has placeholder server scripts, not the historical GameCore described in root docs. Preserve historical documents separately. Only move unreferenced anchored decorative parts with inert descendants. Keep functional bindings untouched. Authored manual requires monitor power, shutters and monitor boot before startup; successful shutdown requires quota and temperature below 17000 F. Conflicting source constants require explicit provenance, not invented precision.]==]'; decisions.Parent=backend
local readme = backend:FindFirstChild('README') or Instance.new('ModuleScript')
readme.Name='README'; readme.Source='return [==[AIRemake rewrite in progress. ServerScriptService.ReactorBackend holds the replacement backend. ServerStorage.Data is preserved reference material, not executable gameplay. ServerStorage.BackendBaseline20260925 preserves the original scaffold and scene move references. Workspace.Geometry contains reorganized decorative parts. Completion requires runtime tests, not only successful installation.]==]'; readme.Parent=backend
local docs = {}
for _, name in ipairs({'PROGRESS','DECISIONS','README'}) do docs[name]=backend[name].Source end
return game:GetService('HttpService'):JSONEncode({moved=moved, skipped=skipped, beforeParts=beforeParts, afterParts=afterParts, docs=docs})
