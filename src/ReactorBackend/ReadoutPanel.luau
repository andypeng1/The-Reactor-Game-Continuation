--!strict
-- The four monitors that carried only static art -- Main, Power, Thermal and
-- Quota -- driven from engine state.
--
-- WHY THIS IS ITS OWN MODULE. RoomShell owns which FACE a monitor shows and
-- writes frame.Visible among them; this module writes only the CONTENT of the
-- frames it does not own -- label Text, the three bar families' Size, and
-- EquinoxFrame's two colours. That is the same division AlertsPanel and
-- BootPanel are carved along: exactly one writer per property, and none of the
-- writers is here for a property another one already had.
--
-- WHAT WAS STATIC. Those four screens shipped with the author's placeholders
-- ('NIL F', '140 F', '100%', '0 GW/H', '11:50 PM', '524 GW', 'OFFLINE') and
-- nothing ever wrote them: the drivers the original used -- GraphDetailThingy --
-- are empty Scripts in this place, so the original's implementation is
-- genuinely unrecoverable. The format of each reading is therefore taken from
-- the ORIGINAL'S OWN RECORDINGS (Data/originalwatch/*/changes.log records every
-- label's observed value verbatim), and the few numbers the evidence does not
-- fix are declared in Config.Readouts rather than fudged.
--
-- WHAT IS DELIBERATELY NOT WIRED, and reported at Initialize so the gap is
-- visible in the console rather than being something a reader has to notice
-- (CLAUDE.md 0.13):
--   * The IMAGE and TEXT tints -- CBLImageLabel, CPumpImageLabel, FanImageLabel,
--     CoreImageLabel.ImageColor3, CoronaImageLabel.ImageColor3,
--     PowerLabel.TextColor3, FluctuationLabel.TextColor. The corpus carries
--     every colour exactly, but not the PREDICATE that chooses one, so wiring
--     them means inventing the rule that decides gold from cyan from white.
--     Numbers first; that is the next phase, and it is named here so it cannot
--     be mistaken for done.
--   * Main's CoreDiagramFrame.GraphFrame1 -- titled REACTOR ENERGY INTENSITY --
--     is a SECOND driven bar the corpus shows and this module does not do. Its
--     shape is the CBL graph's exactly ({2, 0}, {0, N}, integer N riding Y
--     Offset), so the mechanism is already built; what is missing is the map.
--     The corpus has three samples (75, 150, 250) and no clue which reactor
--     state produced any of them, so there is no ratio to divide by. Same
--     refusal as the flow graph below and for the same reason. Its three
--     WarnningImageLabel*.Visible lamps ride the same missing predicate as the
--     tints, and both CoreDiagramFrame graphs' GraphImageLabel.Visible is a
--     plain on/off the corpus never varies in a way this engine can name.
--   * CoreDiagramFrame.GraphFrame2 -- titled P. E. A. EXTRACTION -- is
--     VISIBILITY only in the corpus: not one Size write to its GraphImageLabel
--     anywhere, so there is no P. E. A. extraction bar to reproduce.
--   * ReadingsFrame.StressLabel IS wired, even though the ORIGINAL never drove
--     it -- there is not one StressLabel.Text write in the whole corpus. It is
--     a real engine field (s.peaStress) and the alternative is a label reading
--     the author's '0 %' for the life of the place.
--   * The Thermal screen's FanFrame.FanFrame.GraphFrame.GraphFrame.
--     GraphImageLabel -- titled NET C-PUMP FLOW RATE -- is the one bar the
--     corpus does drive and this module does not. Its values run 0..75 while
--     this engine's only flow quantity is the sum of the enabled pumps' levels,
--     0..9 (Engine:256), and nothing in the evidence fixes the map between them.
--     Scaling 9 onto 75 would be a picked number wearing a measured one's
--     clothes (CLAUDE.md 0.18), so it is left alone until the ratio is known.
--   * Main's ReactorDiagramFrame labels and CoreDiagramFrame's titles
--     (PEANameText, the three CBLNameText, the CoolantBlockFrame C1/C2/C3
--     blocks, both graph titles) are NAMES, not readings, and carry no data to
--     drive.
--
-- This is a read-out adapter and nothing else: it reads engine state and writes
-- display properties, and no engine gate, cost, timing or formula is touched
-- (CLAUDE.md 1.4 #1).

local ReadoutPanel = {}

-- ========== ADDRESSES ==========
local MONITORS = 'Monitors'
local GUI = 'Screen.MonitorUI.MainMonitorFrame'

local MAIN = 'MainControlRoomMonitor'
local POWER = 'PowerControlRoomMonitor'
local THERMAL = 'ThermalControlRoomMonitor'
local QUOTA = 'QuotaControlRoomMonitor'

-- ========== READINGS ==========
-- key -> function(state, config, index) -> number. index is the 1-based member
-- of a family that has three of a thing (the CBLs, the coolant pumps) and is
-- ignored by every reading that does not.

local READINGS = {}

READINGS.temperature = function(state) return state.temperature end
READINGS.stress = function(state) return state.peaStress end
READINGS.fluctuation = function(state) return state.fluctuation end
READINGS.pressure = function(state) return state.pressure end
-- The COMPOSED net (Engine:325): netOutput after the extraction fraction, the
-- gravitron mass cost and the equinox multiplier. netOutput (Engine:322) is the
-- pre-derating sibling and is deliberately not what is shown -- the label's own
-- word is NET, and the capture's '0 GW/H' at rest rules out the pre-derating
-- form, whose offsets alone would floor it at 50.
READINGS.output = function(state) return state.output end
READINGS.radiation = function(state) return state.radiation end
READINGS.hdef = function(state) return state.hdef.integrity end
-- A level, not a field: Engine:111 admits 1..4 and the label is a percentage of
-- that range. Config carries the divisor because the capture's '0 %' is off the
-- ladder this engine can be on.
READINGS.extraction = function(state, config)
    return state.extraction * 100 / config.Readouts.ExtractionMax
end
READINGS.cblStress = function(state, config, index) return state.cbl[index].stress end
READINGS.cblPower = function(state, config, index)
    return state.cbl[index].level * config.Readouts.LevelPercent
end
-- The CBL graph's own quantity: the screen's title is CBL PRESSURE, and the
-- capture's Size.Y.Offset runs 0..100, which is Engine:265's pressure exactly.
READINGS.cblPressure = function(state, config, index) return state.cbl[index].pressure end
-- The reservoir. This engine's C-pump has a discrete LEVEL (Engine:110 admits
-- 1..3) and a running flag, and nothing continuous: the capture's own curve is
-- analog (0.110325, 0.984333, ...), which no level can produce. So this is the
-- level over its range, and it is zeroed when the pump is off -- the capture's
-- empty state is the authored floor rather than a setting being displayed.
READINGS.reservoir = function(state, config, index)
    local pump = state.pumps[index]
    if not pump.enabled then return 0 end
    return pump.level / config.Readouts.PumpLevelMax
end
-- A fraction, not a level: the quota bar is a progress bar, and the capture has
-- it at 0.01 at rest and 1 when met.
READINGS.energy = function(state)
    -- max(quota, 1): a zero quota would divide by zero, and a bar that reports
    -- NaN is worse than one that reports empty.
    return state.energy / math.max(state.quota, 1)
end

-- ========== ROWS ==========
-- A row is a label, the format family it uses, and where its number comes from.
-- Every row is listed here, so a label with no row is a capture problem and not
-- a missing feature.

-- Main's eight readings, in the order the frame shows them.
local MAIN_ROWS = {
    {label = 'TempLabel',        kind = 'Temperature', read = READINGS.temperature},
    {label = 'StressLabel',      kind = 'Percent',     read = READINGS.stress},
    {label = 'FluctuationLabel', kind = 'Temperature', read = READINGS.fluctuation},
    {label = 'PressureLabel',    kind = 'Pressure',    read = READINGS.pressure},
    {label = 'OutputLabel',      kind = 'Output',      read = READINGS.output},
    {label = 'ExtractionLabel',  kind = 'Percent',     read = READINGS.extraction},
    {label = 'RadiationLabel',   kind = 'Radiation',   read = READINGS.radiation},
    {label = 'HDEFLabel',        kind = 'Percent',     read = READINGS.hdef},
}

-- Power's three, repeated per CBL frame. The fourth label of that group --
-- StateLabel -- is a word, not a number, and is written by cblState below.
local POWER_ROWS = {
    {label = 'TempLabel',   kind = 'Temperature', read = READINGS.temperature},
    {label = 'StressLabel', kind = 'Percent',     read = READINGS.cblStress},
    {label = 'PowerLabel',  kind = 'Percent',     read = READINGS.cblPower},
}

-- Thermal's three reservoir bars, one per C-pump frame.
local RESERVOIR_FRAMES = { 'C1Frame', 'C2Frame', 'C3Frame' }
local RESERVOIR_PATH = 'GraphFrame.BarFrame'

-- Thermal's six chamber fans.
local FAN_COUNT = 6
local FAN_PATH = 'FanFrame.FanFrame%d.StatusLabel'

-- Quota's two text readings and its two bars.
local QUOTA_TIME = 'TimeFrame.TimeLabel'
local QUOTA_TARGET = 'QuotaFrame.PowerLabel'
local QUOTA_ENERGY = 'QuotaFrame.EnergyProgressFrame.BarFrame'
local QUOTA_EQUINOX = 'EquinoxFrame'
local EQUINOX_TEXT = 'TextLabel'

-- ========== CAPTURE ==========
local function resolveFrom(inst, path)
    local node = inst
    for token in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

-- The monitors, resolved once. Each entry is the monitor instance or nil, and
-- every nil is reported at Initialize.
local monitors = {}
-- Text rows: {node, kind, read, index}.
local textRows = {}
-- Bar rows: {node, axis, displayFull, read, index, base}.
local barRows = {}
local stateRows = {}
local fanLabels = {}
local quotaTime = nil
local quotaTarget = nil
local quotaEquinox = nil
local quotaEquinoxText = nil
local lastSignature = nil
-- How many readings Initialize actually captured. Refresh returns early on zero,
-- which is the difference between "this engine has nothing to show" and "the
-- screens are not there" -- the second is a warn from Initialize, not a silent
-- no-op here.
local captured = 0

local function requireMonitor(name, problems)
    local folder = workspace:FindFirstChild(MONITORS)
    local monitor = folder and folder:FindFirstChild(name)
    if monitor == nil then
        problems[#problems + 1] = 'no Workspace.' .. MONITORS .. '.' .. name
    end
    return monitor
end

-- Collects one family of labels under one monitor. Reports each missing node by
-- name, because a label that was renamed and a reading that was never wired
-- look identical on screen and only one of them is a bug.
local function collectText(monitor, containerPath, rows, index, problems, where)
    if monitor == nil then return end
    local container = resolveFrom(monitor, containerPath)
    if container == nil then
        problems[#problems + 1] = where .. ' has no ' .. containerPath
        return
    end
    for _, row in ipairs(rows) do
        local node = container:FindFirstChild(row.label)
        if node == nil then
            problems[#problems + 1] = where .. '.' .. containerPath .. ' has no ' .. row.label
        else
            textRows[#textRows + 1] = {node = node, kind = row.kind, read = row.read, index = index}
        end
    end
end

-- Captures a bar's authored Size. Only one axis of it is ever driven, so the
-- other two components are carried through untouched from here.
local function collectBar(monitor, path, spec, read, index, problems, where)
    if monitor == nil then return end
    local node = resolveFrom(monitor, path)
    if node == nil then
        problems[#problems + 1] = where .. ' has no ' .. path
        return
    end
    barRows[#barRows + 1] = {node = node, component = spec.Component,
        displayFull = spec.DisplayFull, read = read, index = index, base = node.Size}
end

function ReadoutPanel.Initialize(config)
    monitors = {}
    textRows = {}
    barRows = {}
    stateRows = {}
    fanLabels = {}
    quotaTime = nil
    quotaTarget = nil
    quotaEquinox = nil
    quotaEquinoxText = nil
    -- Cleared rather than kept: nothing here is baselined off the world, so a
    -- re-Initialize must re-apply its readings instead of treating the last
    -- screen it drew as already correct.
    lastSignature = nil
    captured = 0

    local readouts = config and config.Readouts
    if readouts == nil then
        warn('[ReadoutPanel] Config.Readouts is missing; the four readout screens will not run')
        return 0
    end

    local problems = {}
    monitors.main = requireMonitor(MAIN, problems)
    monitors.power = requireMonitor(POWER, problems)
    monitors.thermal = requireMonitor(THERMAL, problems)
    monitors.quota = requireMonitor(QUOTA, problems)

    collectText(monitors.main, 'Screen.MonitorUI.MainMonitorFrame.ReadingsFrame',
        MAIN_ROWS, nil, problems, MAIN)

    for index = 1, 3 do
        local frame = 'CBL' .. index .. 'Frame'
        collectText(monitors.power, GUI .. '.' .. frame, POWER_ROWS, index, problems, POWER)
        -- The state word. It is not a number, so it is not a textRow; it is
        -- written by cblState below and lives in stateRows so that the signature
        -- still covers it.
        local node = monitors.power and resolveFrom(monitors.power, GUI .. '.' .. frame .. '.StateLabel')
        if node ~= nil then
            stateRows[#stateRows + 1] = {node = node, index = index}
        elseif monitors.power ~= nil then
            problems[#problems + 1] = POWER .. '.' .. frame .. ' has no StateLabel'
        end
        collectBar(monitors.power, GUI .. '.' .. frame .. '.GraphFrame.GraphFrame.GraphImageLabel',
            readouts.Bars.CblGraph, READINGS.cblPressure, index, problems, POWER)
    end

    for index, frame in ipairs(RESERVOIR_FRAMES) do
        collectBar(monitors.thermal, GUI .. '.' .. frame .. '.' .. RESERVOIR_PATH,
            readouts.Bars.Reservoir, READINGS.reservoir, index, problems, THERMAL)
    end

    if monitors.thermal ~= nil then
        for index = 1, FAN_COUNT do
            local node = resolveFrom(monitors.thermal, GUI .. '.' .. string.format(FAN_PATH, index))
            if node == nil then
                problems[#problems + 1] = THERMAL .. ' has no FanFrame.FanFrame' .. index .. '.StatusLabel'
            else
                fanLabels[#fanLabels + 1] = node
            end
        end
    end

    if monitors.quota ~= nil then
        quotaTime = resolveFrom(monitors.quota, GUI .. '.' .. QUOTA_TIME)
        quotaTarget = resolveFrom(monitors.quota, GUI .. '.' .. QUOTA_TARGET)
        collectBar(monitors.quota, GUI .. '.' .. QUOTA_ENERGY,
            readouts.Bars.Energy, READINGS.energy, nil, problems, QUOTA)
        quotaEquinox = resolveFrom(monitors.quota, GUI .. '.' .. QUOTA_EQUINOX)
        quotaEquinoxText = quotaEquinox and quotaEquinox:FindFirstChild(EQUINOX_TEXT)
        if quotaTime == nil then problems[#problems + 1] = QUOTA .. ' has no ' .. QUOTA_TIME end
        if quotaTarget == nil then problems[#problems + 1] = QUOTA .. ' has no ' .. QUOTA_TARGET end
        if quotaEquinox == nil then
            problems[#problems + 1] = QUOTA .. ' has no ' .. QUOTA_EQUINOX
        elseif quotaEquinoxText == nil then
            problems[#problems + 1] = QUOTA .. '.' .. QUOTA_EQUINOX .. ' has no ' .. EQUINOX_TEXT
        end
    end

    if #problems > 0 then
        warn('[ReadoutPanel] incomplete capture: ' .. table.concat(problems, '; '))
    end
    captured = #textRows + #barRows + #stateRows + #fanLabels
        + (quotaTime and 1 or 0) + (quotaTarget and 1 or 0) + (quotaEquinox and 1 or 0)
    local total = captured
    if total == 0 then
        warn('[ReadoutPanel] nothing captured; the four readout screens will not run')
        return 0
    end
    -- Printed, not warned: these are the readings this engine has no source for,
    -- and a reading that is missing and one that is deliberately absent look
    -- identical on screen.
    print('[ReadoutPanel] tints left alone this phase, no predicate in the evidence: '
        .. 'CBLImageLabel, CPumpImageLabel, FanImageLabel, CoreImageLabel, '
        .. 'CoronaImageLabel, PowerLabel.TextColor3, FluctuationLabel.TextColor')
    print('[ReadoutPanel] driven bars left alone this phase, no map in the evidence: '
        .. 'FanFrame NET C-PUMP FLOW RATE (corpus 0..75, engine 0..9), '
        .. 'CoreDiagramFrame.GraphFrame1 REACTOR ENERGY INTENSITY (corpus 75/150/250)')
    print(string.format('[ReadoutPanel] captured %d readings on %s/%s/%s/%s',
        total, MAIN, POWER, THERMAL, QUOTA))
    return total
end

-- ========== FORMATTERS ==========

-- The shift clock. Config.Readouts.Clock counts minutes since NOON, so hour 12
-- of a 24-hour face is noon: 710 -> 23:50 -> 11:50 PM and 795 -> 13:15 ->
-- 1:15 AM, both of which are in the corpus. The day and half-day constants live
-- here rather than in Config, matching ForecastPanel.formatClock.
local function formatClock(seconds, config)
    local clock = config.Readouts.Clock
    local total = math.floor(clock.StartMinute + seconds * clock.MinutesPerSecond)
    local hour24 = (math.floor(total / 60) + 12) % 24
    local hour = hour24 % 12
    if hour == 0 then hour = 12 end
    local minute = total % 60
    local suffix = hour24 < 12 and 'AM' or 'PM'
    return string.format('%d:%02d %s', hour, minute, suffix)
end

-- The quota target. The capture crosses into TW, so this does too, at the
-- declared threshold. Config.Target.SIDecimals is interpolated rather than
-- written as a literal format so the two can never disagree.
local function formatTarget(gw, config)
    local target = config.Readouts.Target
    if gw >= target.SIThreshold then
        return string.format('%.' .. target.SIDecimals .. 'f TW', gw / target.SIDivisor)
    end
    return string.format('%.0f GW', gw)
end

-- The CBL state word.
local function cblState(state, config, index)
    local words = config.Readouts.CblState
    local device = state.cbl[index]
    -- A faulted laser is OFFLINE by the engine's own definition: Engine:154
    -- refuses every command on it until it has been repaired.
    if device.fault then return words.Offline end
    if state.phase == 'Starting' then
        -- The start-up chain is this engine's only ignition, so both transients
        -- ride its cursor. Config.Shift.StartupSteps[11] is 'PRIMING ALL
        -- COMBUSTION LASERS' and [14] is 'COMBUSTION LASERS FIRING'.
        if state.startupStep >= config.Readouts.CblFiringStep then return words.Firing end
        if state.startupStep >= config.Readouts.CblPrimingStep then return words.Powering end
        return words.Offline
    end
    if not device.active then return words.Offline end
    -- LOW OUTPUT is the capture's last state before its two failure logs, and in
    -- this engine the derating has both a name and a threshold: Engine:262 drops
    -- an active laser to level 1 whenever chamber pressure is under
    -- StallPressure, which is exactly the low-output regime.
    if state.pressure < config.Sim.StallPressure then return words.LowOutput end
    return words.Active
end

-- Builds the driven Size for a bar. value is a fraction 0..1; DisplayFull says
-- what 1 means in the driven component's own units.
--
-- BOTH halves of the driven axis are written, not just the one carrying the
-- number. The corpus shows the original doing exactly that: the CBL graph's
-- AUTHORED Size is {2,0},{0.75,0} -- a full-height bar -- while every driven
-- value is {2,0},{0,N}, i.e. Y.Scale forced back to 0. Carrying a stale Scale
-- beside a live Offset would scale the bar by a number nobody maintains.
--
-- The OTHER axis is preserved whole, which is what makes a re-Initialize safe to
-- capture from: this module never writes the component it preserves.
--
-- Offset is an integer in Roblox and truncates on assignment, so a quantity that
-- needs sub-pixel resolution -- the reservoir's own 0.441554189 -- can only ride
-- Scale. That is why the component is declared per bar in Config rather than
-- inferred from the axis.
local function barSize(base, component, value, displayFull)
    local f = math.clamp(value, 0, 1) * displayFull
    if component == 'XScale' then
        return UDim2.new(f, 0, base.Y.Scale, base.Y.Offset)
    elseif component == 'YScale' then
        return UDim2.new(base.X.Scale, base.X.Offset, f, 0)
    end
    return UDim2.new(base.X.Scale, base.X.Offset, 0, f)
end

-- ========== REFRESH ==========
-- Signature-gated on the rendered values, not on the clock: the engine drifts
-- every second but the signature must not be a summary of that drift, so it is
-- the concatenated strings themselves. Two different states can then never
-- collide on it, and a tick that moved nothing writes nothing.
function ReadoutPanel.Refresh(state, config)
    if captured == 0 then return end
    local readouts = config.Readouts
    local formats = readouts.Format
    local parts = {}

    for _, row in ipairs(textRows) do
        parts[#parts + 1] = string.format(formats[row.kind], row.read(state, config, row.index))
    end
    for _, row in ipairs(stateRows) do
        parts[#parts + 1] = cblState(state, config, row.index)
    end
    -- The fan labels are captured flat but read by index, because the status
    -- word is the fan's own boolean and not a property of the label.
    for index = 1, #fanLabels do
        parts[#parts + 1] = state.fans[index] and readouts.FanOn or readouts.FanOff
    end
    for _, row in ipairs(barRows) do
        parts[#parts + 1] = tostring(barSize(row.base, row.component, row.read(state, config, row.index), row.displayFull))
    end
    if quotaTime ~= nil then parts[#parts + 1] = formatClock(state.time, config) end
    if quotaTarget ~= nil then parts[#parts + 1] = formatTarget(state.quota, config) end
    if quotaEquinox ~= nil then
        parts[#parts + 1] = state.equinox and 'alarm' or 'idle'
    end

    local key = table.concat(parts, '|')
    if key == lastSignature then return end
    lastSignature = key

    -- One writer per property, and this module writes Text, Size and two
    -- Colors and nothing else. Parent is checked because an adapter that
    -- survives a fresh shift can also survive the screen being torn down under
    -- it, and a write to a destroyed instance throws.
    local cursor = 0
    for _, row in ipairs(textRows) do
        cursor = cursor + 1
        if row.node.Parent then row.node.Text = parts[cursor] end
    end
    for _, row in ipairs(stateRows) do
        cursor = cursor + 1
        if row.node.Parent then row.node.Text = parts[cursor] end
    end
    for index, label in ipairs(fanLabels) do
        cursor = cursor + 1
        if label.Parent then label.Text = parts[cursor] end
    end
    for _, row in ipairs(barRows) do
        cursor = cursor + 1
        if row.node.Parent then
            row.node.Size = barSize(row.base, row.component,
                row.read(state, config, row.index), row.displayFull)
        end
    end
    if quotaTime ~= nil then
        cursor = cursor + 1
        if quotaTime.Parent then quotaTime.Text = parts[cursor] end
    end
    if quotaTarget ~= nil then
        cursor = cursor + 1
        if quotaTarget.Parent then quotaTarget.Text = parts[cursor] end
    end
    if quotaEquinox ~= nil and quotaEquinox.Parent then
        local alarm = state.equinox
        quotaEquinox.BackgroundColor3 =
            alarm and readouts.Equinox.AlarmBackground or readouts.Equinox.IdleBackground
        if quotaEquinoxText ~= nil then
            quotaEquinoxText.TextColor3 =
                alarm and readouts.Equinox.AlarmText or readouts.Equinox.IdleText
        end
    end
end

-- Every reading here is a pure function of engine state, which Reset replaces
-- wholesale, and the signature is rebuilt from scratch each Refresh -- so
-- leaving a run needs no separate reset: the next Refresh simply recomputes.
-- Kept as a note so the absence is not read as an omission.
return ReadoutPanel
