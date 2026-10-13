--!strict
-- The reactor-alerts monitor's 27-row indicator grid, driven from engine state.
--
-- WHY THIS IS ITS OWN MODULE. RoomShell owns which FACE a monitor shows and
-- writes frame.Visible among them; MainMonitorFrame is that face for Starting
-- and Running, and AlertsFrame lives inside it. This module writes .Visible on
-- the inner colour frame of each AlertFrameN -- a property RoomShell never
-- touches -- so there is still exactly one writer per property, which is the
-- same division BootPanel is carved along.
--
-- WHAT THE GRID IS. Twenty-seven 100x100 tiles. Each tile is a grey chip with a
-- black label, and behind the label (ZIndex 0) sits a full-size Frame whose
-- BackgroundColor3 is that row's own category colour. Making that inner frame
-- Visible turns the chip to its colour with the label still readable on top --
-- that is the entire mechanism, and it is the only property the original's own
-- recordings ever write here. Every AlertFrameN line in Data/originalwatch is
-- '<path>.AlertFrameN.Frame.Visible'.
--
-- WHERE THE CONDITIONS COME FROM. Each row's meaning is the in-game manual's --
-- Workspace.Consoles.ElectricGridConsole.DRMScreen, whose AlertsFrame pages give
-- the prose for every row -- and each predicate below reads a field the engine
-- already computes. No engine gate, cost, timing or formula is touched: this is
-- a read-out adapter, and CLAUDE.md 1.4 #1 is why nothing here may invent a
-- mechanic the engine does not have.
--
-- WHAT IS DELIBERATELY NOT WIRED. Two rows have no counterpart in this engine
-- and are left dark rather than aliased onto a neighbour that would look right:
--   * POWER INTERRUPTION -- the facility has no modelled power feed to interrupt.
--   * ENERGY FLUCTUATION -- the manual's subspace (EFE) quantity. This engine's
--     s.fluctuation is a TEMPERATURE delta and already drives HIGH TEMP
--     FLUCTUATION one row down; pointing this row at it too would light two
--     unrelated alerts off one number.
-- Both are reported at Initialize, so the gap is visible in the console rather
-- than being something a reader has to notice for themselves (CLAUDE.md 0.13).

local AlertsPanel = {}

-- ========== ADDRESSES ==========
local MONITORS = 'Monitors'
local ALERTS_MONITOR = 'AlertsControlRoomMonitor'
local TILE_PREFIX = 'AlertFrame'
local GRID_PATH = 'Screen.MonitorUI.MainMonitorFrame.AlertsFrame'
-- The colour frame inside each tile. Named 'Frame' by the art; addressed by
-- name so a rename shows up as a missing node rather than as a row that simply
-- stopped lighting.
local PILL = 'Frame'

-- ========== CONDITIONS ==========
-- key -> function(state, config) -> boolean. A key absent from this table is
-- unwired by design (see the header) and reported once at Initialize.

local function anyOf(list, test)
    for _, item in ipairs(list) do
        if test(item) then return true end
    end
    return false
end

local function anyFan(state)
    for index = 1, #state.fans do
        if state.fans[index] then return true end
    end
    return false
end

local CONDITIONS = {
    -- -- the start-up chain and the devices it brings up ----------------
    -- RECT ACTIVATION is read as the deep-scan sweep. It is the one reading the
    -- evidence supports: in Data/originalwatch/261002-140021 the row is switched
    -- on and off on the same two polls as the forecast monitor's own deep-scan
    -- announcement (64.95 / 77.22 against 64.90 / 77.17), which is the whole of
    -- what the captures say about what this row tracks.
    rectActivation = function(state, config)
        local d = config.Forecast.DeepScan
        return state.startupStep >= d.Step and state.startupStep < d.Step + 2
    end,
    -- SUBSPACE FIELD ACTIVE rides the chain's own message: StartupSteps[7] is
    -- 'SUBSPACE RIFT ACTIVE, RADIATION WARNING'.
    subspaceField = function(state)
        return state.startupStep >= 7
    end,
    cblActive = function(state)
        return anyOf(state.cbl, function(d) return d.active end)
    end,
    coreActive = function(state)
        return state.coreState > 0
    end,
    pumpActive = function(state)
        return anyOf(state.pumps, function(p) return p.enabled and p.integrity > 0 end)
    end,
    fanActive = function(state)
        return anyFan(state)
    end,
    hdefActive = function(state)
        return state.hdef.enabled
    end,
    -- G-GATE is read as the Gravatron's gate, this rig's one subspace device: it
    -- is active for the charge and the firing window and Idle the rest of the
    -- time, which is the shape the row's own on/off captures have.
    gGateActive = function(state)
        return state.grav.phase ~= 'Idle'
    end,
    chamberRadiation = function(state)
        return state.radiation > 0
    end,
    -- -- conditions on a running reactor ---------------------------------
    -- Manual: RADIATION BREACH is a low H.D.E.F. Integrity. The threshold is
    -- ours; the field is the engine's own 0-100 HDEF integrity.
    radiationBreach = function(state, config)
        return state.hdef.integrity < config.Alerts.RadiationBreachIntegrity
    end,
    -- Manual: output above 400 GW/H.
    highEnergyOutput = function(state, config)
        return state.output > config.Alerts.HighEnergyOutput
    end,
    -- Ours, on the engine's own shutdown limit: 17000 F is where the manual says
    -- the reactor must be cooled below before it can be shut down, which makes
    -- it the facility's own excessive-temperature line.
    excessiveTemperature = function(state, config)
        return state.temperature > config.Alerts.ExcessiveTemperature
    end,
    -- Manual: P.E.A stress above 75%. s.peaStress is 0-100 and the engine fails
    -- the reactor at 100.
    excessPeaStress = function(state, config)
        return state.peaStress > config.Alerts.ExcessPeaStress
    end,
    -- Manual: above a 400F fluctuation. s.fluctuation is the per-step temperature
    -- delta, so its magnitude is the quantity the manual names.
    highTempFluctuation = function(state, config)
        return math.abs(state.fluctuation) > config.Alerts.HighTempFluctuation
    end,
    -- Manual: all E-VENTs used up. The engine carries three booleans.
    eventsDepleted = function(state)
        return state.emergencyUsed[1] and state.emergencyUsed[2] and state.emergencyUsed[3]
    end,
    -- Ours, on the engine's own radiation formula: s.radiation is
    -- RadiationPerState * (coreState + 1) * a mass factor, so it is a function
    -- of the core state alone and its top band is state 3. Reading the state
    -- rather than re-deriving a radiation threshold keeps one source for it.
    hazardousRadiation = function(state, config)
        return state.coreState >= config.Alerts.HazardousCoreState
    end,
    -- The engine's own over-pressure line, which is also the PEA stress-bonus
    -- threshold -- one number with one meaning.
    highPressure = function(state, config)
        return state.pressure > config.Alerts.HighPressure
    end,
    -- Ours: the top two rungs of the CBL's 1..5 ladder.
    highCblPower = function(state, config)
        return anyOf(state.cbl, function(d) return d.level >= config.Alerts.HighCblLevel end)
    end,
    -- The engine's own stress threshold, CBLStressThreshold = 75 -- the same
    -- number at which the engines raise d.stress. Manual: a pressure purge is
    -- what clears it.
    highCblStress = function(state, config)
        return anyOf(state.cbl, function(d) return d.stress > config.Alerts.HighCblStress end)
    end,
    -- Manual: the P.E.A goes offline from excessive stress. 100 is the engine's
    -- own overload point, where it fails the reactor.
    peaMalfunction = function(state)
        return state.peaStress >= 100
    end,
    pumpMalfunction = function(state)
        return anyOf(state.pumps, function(p) return p.integrity <= 0 end)
    end,
    -- Manual: a CBL disabled or the reactor pressure too low. d.fault is the
    -- engine's own overload latch.
    cblMalfunction = function(state)
        return anyOf(state.cbl, function(d) return d.fault end)
    end,
    -- Manual: the C-Pumps are offline. The complement of pumpActive, which is
    -- why the two are one predicate apart rather than two readings of one field.
    lowCoolant = function(state)
        return not anyOf(state.pumps, function(p) return p.enabled and p.integrity > 0 end)
    end,
    -- Manual: an EFE or Equinox active. The Equinox is the only subspace event
    -- this engine models (s.equinox), so it is the whole condition here.
    coreDestabilization = function(state)
        return state.equinox
    end,
    -- Manual: core temp below ~6000F. The engine's own stallout fail is at
    -- Sim.StallTemperature = 2000, and 6000 is the manual's warning line above
    -- it -- a possibility, which is what the row is called.
    stalloutPossibility = function(state, config)
        return state.temperature < config.Alerts.StalloutTemperature
    end,
}

-- ========== CAPTURE ==========
local tiles = {}
local lastSignature: string? = nil

local function resolveFrom(inst, path)
    local node = inst
    for token in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

function AlertsPanel.Initialize(config)
    tiles = {}
    -- Cleared rather than kept: nothing here is baselined off the world, so a
    -- re-Initialize must re-apply its rows instead of treating the last screen
    -- it drew as already correct.
    lastSignature = nil
    local alerts = config and config.Alerts
    if alerts == nil or alerts.Rows == nil then
        warn('[AlertsPanel] Config.Alerts.Rows is missing; the alerts grid will not run')
        return 0
    end
    local folder = workspace:FindFirstChild(MONITORS)
    local monitor = folder and folder:FindFirstChild(ALERTS_MONITOR)
    if monitor == nil then
        warn('[AlertsPanel] missing Workspace.' .. MONITORS .. '.' .. ALERTS_MONITOR .. '; the alerts grid will not run')
        return 0
    end
    local grid = resolveFrom(monitor, GRID_PATH)
    if grid == nil then
        warn('[AlertsPanel] ' .. ALERTS_MONITOR .. ' has no ' .. GRID_PATH .. '; the alerts grid will not run')
        return 0
    end
    local problems = {}
    local unwired = {}
    for _, row in ipairs(alerts.Rows) do
        local tile = grid:FindFirstChild(TILE_PREFIX .. row.n)
        if tile == nil then
            problems[#problems + 1] = string.format('no %s%d tile', TILE_PREFIX, row.n)
        else
            local pill = tile:FindFirstChild(PILL)
            if pill == nil then
                problems[#problems + 1] = string.format('%s%d has no %s child', TILE_PREFIX, row.n, PILL)
            else
                -- A row whose key has no predicate is recorded, not errored: it
                -- is a row this engine has nothing to say about (the header
                -- names two), and leaving it dark is the honest state.
                if CONDITIONS[row.key] == nil then
                    unwired[#unwired + 1] = string.format('%d %s', row.n, row.key)
                end
                tiles[#tiles + 1] = {n = row.n, key = row.key, active = row.active == true, pill = pill}
            end
        end
    end
    if #tiles == 0 then
        problems[#problems + 1] = 'no alert tiles found under ' .. ALERTS_MONITOR .. '.' .. GRID_PATH
    end
    if #problems > 0 then
        warn('[AlertsPanel] incomplete capture: ' .. table.concat(problems, '; '))
    end
    if #unwired > 0 then
        -- Not a failure. Printed because a row that never lights and a row with
        -- no predicate look identical on screen, and only one of them is a bug.
        print('[AlertsPanel] rows with no engine counterpart, left dark: ' .. table.concat(unwired, ', '))
    end
    print(string.format('[AlertsPanel] captured %d alert rows on %s', #tiles, ALERTS_MONITOR))
    return #tiles
end

-- ========== REFRESH ==========
-- Signature-gated on the LIT SET, not on the clock: the engine drifts every
-- second but the grid only changes when a row crosses, so a quiet tick must not
-- write 27 booleans. The signature is the vector itself, so two different states
-- can never collide on a summary of it.
function AlertsPanel.Refresh(state, config)
    if #tiles == 0 then return end
    local alerts = config.Alerts
    -- The condition rows describe a RUNNING reactor (see Config.Alerts.Rows).
    -- Stopping is included so the last readings do not blink out the instant the
    -- reactor is commanded down; Report is not, because by then it is shut down.
    local live = state.phase == 'Running' or state.phase == 'Stopping'
    local lit = {}
    local signature = {}
    for index, row in ipairs(tiles) do
        local on = false
        local predicate = CONDITIONS[row.key]
        if predicate ~= nil and (row.active or live) then
            -- pcall would be wrong here: a predicate that throws is a bug in
            -- this table, and a row that silently stays dark is indistinguishable
            -- from one the engine has nothing to say about (CLAUDE.md 0.13).
            on = predicate(state, config) == true
        end
        lit[index] = on
        signature[index] = on and '1' or '0'
    end
    local key = table.concat(signature)
    if key == lastSignature then return end
    lastSignature = key
    for index, row in ipairs(tiles) do
        if row.pill.Parent then
            row.pill.Visible = lit[index]
        end
    end
end

-- Every row's predicate reads engine state, which Reset replaces wholesale, and
-- the signature is rebuilt from scratch each Refresh -- so leaving a run needs no
-- separate reset: the next Refresh simply recomputes. Kept as a note so the
-- absence is not read as an omission.
return AlertsPanel
