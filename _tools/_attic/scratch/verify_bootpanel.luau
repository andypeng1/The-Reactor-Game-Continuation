-- BootPanel verification, run through rblx_execute_luau (datamodel_type "Edit").
--
-- Three runs. Each one requires CLONES of the real Config/Engine/BootPanel
-- (CLAUDE.md 0.15: a stale require hands back a table with the wrong keys, and
-- the error then lands in the consumer), drives a private Engine on a fake
-- clock, and reads back the REAL labels under Workspace.Monitors -- instance
-- state, not module state (CLAUDE.md 0.2).
--
-- RUN 1 is the shipped schedule. RUN 2 and RUN 3 are mutants: they exist to
-- prove the observation can see the thing it claims to check. A check that
-- cannot go red is not evidence.
--
-- No backslashes anywhere in this file (CLAUDE.md 0.10).
local SSS = game:GetService('ServerScriptService')
local backend = SSS:FindFirstChild('ReactorBackend')
local out = {}
local function p(s) table.insert(out, tostring(s)) end

local old = SSS:FindFirstChild('__BootPanelVerify')
if old then old:Destroy() end
local temp = Instance.new('Folder')
temp.Name = '__BootPanelVerify'
temp.Parent = SSS

local function fresh(name)
    local source = backend:FindFirstChild(name)
    if not source then error('missing module ' .. name) end
    local clone = source:Clone()
    clone.Parent = temp
    return require(clone)
end
local Config = fresh('Config')
local Engine = fresh('Engine')
local BootPanel = fresh('BootPanel')

-- ========== readback ==========

local function ranges(nums)
    if #nums == 0 then return '-' end
    local parts, a, b = {}, nums[1], nums[1]
    for i = 2, #nums do
        if nums[i] == b + 1 then
            b = nums[i]
        else
            parts[#parts + 1] = (a == b) and tostring(a) or (tostring(a) .. '-' .. tostring(b))
            a, b = nums[i], nums[i]
        end
    end
    parts[#parts + 1] = (a == b) and tostring(a) or (tostring(a) .. '-' .. tostring(b))
    return table.concat(parts, ',')
end

local function findBoot()
    local mon = workspace.Monitors:FindFirstChild('MainControlRoomMonitor')
    if not mon then return nil end
    return mon:FindFirstChild('BootFrame', true)
end

local function scan()
    local bf = findBoot()
    if not bf then return {}, {}, 0 end
    local diag, log = {}, {}
    for _, child in ipairs(bf.DiagnosticFrame.ScrollingFrame:GetChildren()) do
        local n = tonumber(string.match(child.Name, '^TextLabel(%d+)$'))
        if n and child.Visible then diag[#diag + 1] = n end
    end
    for _, child in ipairs(bf.LogFrame:GetChildren()) do
        local n = tonumber(string.match(child.Name, '^TitleText(%d+)$'))
        if n and child.Visible then log[#log + 1] = n end
    end
    table.sort(diag)
    table.sort(log)
    local logo = 0
    if bf.CompanyLogo and bf.CompanyLogo.Visible then logo = 1 end
    return diag, log, logo
end

local function line(state)
    local diag, log, logo = scan()
    return string.format('phase=%-8s pt=%-3s diag=%-9s log=%-4s logo=%s',
        tostring(state.phase), tostring(math.floor(state.phaseTime)),
        ranges(diag), ranges(log), tostring(logo))
end

local function allHidden()
    local diag, log, logo = scan()
    return #diag == 0 and #log == 0 and logo == 0
end

-- ========== the world as authored ==========

p('BootSeconds=' .. tostring(Config.Shift.BootSeconds)
    .. '  reveals=' .. tostring(#Config.Shell.BootScreen.Reveals))

local names = {}
for _, mon in ipairs(workspace.Monitors:GetChildren()) do
    if string.sub(mon.Name, -18) == 'ControlRoomMonitor' then
        names[#names + 1] = mon.Name .. (mon:FindFirstChild('BootFrame', true) and '+boot' or '-boot')
    end
end
table.sort(names)
p('monitors: ' .. table.concat(names, ' '))

local authored = 0
for _, child in ipairs(findBoot().DiagnosticFrame.ScrollingFrame:GetChildren()) do
    if child:IsA('TextLabel') and child.Visible then authored += 1 end
end
for _, child in ipairs(findBoot().LogFrame:GetChildren()) do
    if child:IsA('TextLabel') and child.Visible then authored += 1 end
end
if findBoot().CompanyLogo and findBoot().CompanyLogo.Visible then authored += 1 end
p('authored-visible among the driven labels: ' .. tostring(authored)
    .. '  (nonzero means the capture cannot tell shown from never-hidden)')

p('before any refresh, main control room: ' .. line({phase = 'unset', phaseTime = 0}))

-- ========== the drives ==========

local function drive(bootSeconds, patch)
    if bootSeconds then Config.Shift.BootSeconds = bootSeconds end
    if patch then patch(Config.Shell.BootScreen.Reveals) end
    local engine = Engine.new(Config, function() return 0 end)
    engine:Command('monitor_power')
    engine:Command('shutters')
    local ok, why = engine:Command('boot')
    local rows = {}
    local function snap(label) rows[#rows + 1] = label .. ' ' .. line(engine.state) end
    -- Runtime refreshes inside the publish callback that runs on the same tick
    -- as the command, so t=0 has to be sampled AFTER a refresh. Sampling it
    -- before one reports the pre-click screen and calls it the boot screen.
    BootPanel.Refresh(engine.state, Config)
    snap('cmd ')
    for i = 1, 22 do
        engine:Update(1)
        BootPanel.Refresh(engine.state, Config)
        snap(string.format('%02d  ', i))
    end
    if not ok then p('WARNING boot refused: ' .. tostring(why)) end
    return rows, engine
end

BootPanel.Initialize(Config)

local run1 = drive(nil, nil)
p('')
p('== RUN 1  as shipped (t = whole seconds after the boot command) ==')
for i, row in ipairs(run1) do p('  t=' .. tostring(i - 1) .. ' ' .. row) end

-- Mutant A: drop the blanket clear at t=5. The diagnostics must then stay up.
-- Found by searching the table, not by assuming the index: the schedule's
-- positions are the thing under test, so reading position 5 by eye is exactly
-- the kind of assumption this run exists to catch.
local atFive
for i, entry in ipairs(Config.Shell.BootScreen.Reveals) do
    if entry.at == 5 then atFive = i end
end
if not atFive then error('no reveal is due at t=5') end
p('the reveal due at t=5 is entry ' .. tostring(atFive))

local run2 = drive(nil, function(reveals) reveals[atFive].clearDiagnostic = nil end)
Config.Shell.BootScreen.Reveals[atFive].clearDiagnostic = true
-- Mutant B: a longer boot. The phase flip must move from t=14 to t=20.
local run3 = drive(20, nil)

local movedA, movedB = {}, {}
for i = 1, #run1 do
    if run1[i] ~= run2[i] then movedA[#movedA + 1] = i - 1 end
    if run1[i] ~= run3[i] then movedB[#movedB + 1] = i - 1 end
end

p('')
p('== mutant A  clearDiagnostic removed from the t=5 entry ==')
p('  differs from RUN 1 at t = ' .. ranges(movedA) .. '   (must be non-empty)')
p('  t=6 as shipped: ' .. run1[7])
p('  t=6 mutant   : ' .. run2[7])
p('')
p('== mutant B  BootSeconds 14 -> 20 ==')
p('  differs from RUN 1 at t = ' .. ranges(movedB) .. '   (must be non-empty)')
p('  t=14 as shipped: ' .. run1[15])
p('  t=14 mutant   : ' .. run3[15])
p('')
p('mutant A caught=' .. tostring(#movedA > 0) .. '  mutant B caught=' .. tostring(#movedB > 0))

-- ========== put the world back ==========

Config.Shift.BootSeconds = 14
local cleaner = Engine.new(Config, function() return 0 end)
BootPanel.Refresh(cleaner.state, Config)
p('')
p('after cleanup, all driven labels hidden: ' .. tostring(allHidden()))

temp:Destroy()
-- string.char(10) rather than a backslash escape: CLAUDE.md 0.10, the edit layer
-- decodes escapes once and a decoded escape is a syntax error pointing at the
-- tool's output rather than at the tool.
return table.concat(out, string.char(10))
