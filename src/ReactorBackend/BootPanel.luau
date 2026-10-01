--!strict
-- The boot screen's own animation: which of BootFrame's authored lines are
-- visible, second by second, while the monitor boot runs.
--
-- WHY THIS IS NOT PART OF RoomShell. RoomShell owns which FACE a monitor shows
-- -- BootFrame.Visible among them -- and its whole contract is that one phase
-- change produces one write, which is why it is signature-gated on the engine's
-- phase. This needs a write per SECOND inside a phase that does not change for
-- 14 s. Folding it in would mean either breaking that gate or re-running
-- RoomShell's entire 7-monitor sweep once a second. The two do not collide:
-- RoomShell writes frame.Visible, this writes .Visible on labels INSIDE one of
-- those frames, so there is still exactly one writer per property.
--
-- WHAT THE SCREEN IS. Not a spinner and not a progress bar. It is a fixed block
-- of authored diagnostic lines that arrive in bursts and then clear, a six-line
-- log that accumulates beside it, and a company logo that arrives late. The
-- schedule lives in Config.Shell.BootScreen and the numbers in it are the
-- operator's own capture; that table's note carries the source and states the
-- one thing the capture cannot say.
--
-- WHAT IT DELIBERATELY DOES NOT DO. It does not animate Position, Size,
-- Rotation or CanvasPosition. Those all move in the capture and none of them is
-- recoverable from it -- see Config.Shell.BootScreen. A screen that reveals the
-- right lines in the right seconds and does not grow them is a smaller lie than
-- one that eases them along a curve nobody measured.

local BootPanel = {}

-- ========== ADDRESSES ==========
-- Dot paths resolved from each BootFrame, spelled the way the art spells them so
-- a rename shows up as a missing node rather than as a boot screen that stopped
-- half way through and never said why.
local MONITORS = 'Monitors'
local BOOT_FRAME = 'BootFrame'
local DIAGNOSTIC_PATH = 'DiagnosticFrame.ScrollingFrame'
local LOG_PATH = 'LogFrame'
local COMPANY_LOGO = 'CompanyLogo'
-- The two blocks are addressed as '<prefix><n>'. The capture names them
-- TextLabel1..45 and TitleText1..6, and the ScrollingFrame's children are NOT
-- in numeric order in the tree, so the number is parsed off the name rather
-- than assumed from the child index.
local DIAGNOSTIC_PREFIX = 'TextLabel'
local LOG_PREFIX = 'TitleText'

-- ========== CAPTURE ==========
-- References only. Nothing is baselined off the world here: the schedule says
-- what every label should be at every moment, so a captured "authored" state
-- would only be a second opinion from art this module is meant to overrule.
local monitors = {}
-- One signature for the whole panel. The schedule is the same on all seven
-- monitors and so is the second they are on, so there is nothing per-monitor to
-- gate on -- and gating on the step alone is what keeps a quiet tick from
-- writing 7 monitors x 51 labels.
local lastSignature: string? = nil

local function resolveFrom(inst, path)
    local node = inst
    for token in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

-- Turns one container's '<prefix><n>' children into a table keyed by n and
-- returns how far the numbering runs. Duplicates are reported rather than
-- resolved: the schedule drives labels BY NUMBER, so two labels claiming one
-- number means one of them can never be revealed -- and that would look exactly
-- like art that was authored wrong.
local function numbered(container, prefix, sink, problems)
    local highest = 0
    for _, child in ipairs(container:GetChildren()) do
        local digits = string.match(child.Name, '^' .. prefix .. '(%d+)$')
        if digits then
            local n = tonumber(digits)
            if n == nil then
                problems[#problems + 1] = container:GetFullName() .. '.' .. child.Name .. ' is not a number'
            elseif sink[n] ~= nil then
                problems[#problems + 1] = string.format('%s has two labels numbered %d (%s and %s)',
                    container:GetFullName(), n, sink[n].Name, child.Name)
            else
                sink[n] = child
                if n > highest then highest = n end
            end
        end
    end
    return highest
end

-- How many labels the schedule actually reaches for, derived from the ranges
-- rather than declared next to them: a declared count beside a range is two
-- places to change, and only one of them is obviously wrong when they drift.
local function reach(schedule)
    local diagnostic, log = 0, 0
    for _, reveal in ipairs(schedule.Reveals) do
        if reveal.diagnostic and reveal.diagnostic[2] > diagnostic then diagnostic = reveal.diagnostic[2] end
        if reveal.log and reveal.log[2] > log then log = reveal.log[2] end
        if reveal.clearLog and reveal.clearLog[2] > log then log = reveal.clearLog[2] end
    end
    return diagnostic, log
end

function BootPanel.Initialize(config)
    -- Emptied rather than appended to, for the reason RoomShell empties its own:
    -- a re-run must be a real re-resolve, not a doubled list that quietly does
    -- twice the work for the rest of the session.
    monitors = {}
    -- Cleared, unlike RoomShell's shutter latch: nothing here is captured off the
    -- world, so a re-Initialize can safely re-apply a step it had already
    -- applied. Keeping the old signature would make the second Initialize a
    -- no-op for whatever step happened to be on screen at the time.
    lastSignature = nil
    local schedule = config and config.Shell and config.Shell.BootScreen
    if schedule == nil then
        -- Not a fallback. The schedule IS this module, so defaulting it would be
        -- inventing a boot screen, which is the one thing it must not do.
        warn('[BootPanel] Config.Shell.BootScreen is missing; the boot screen will not animate')
        return 0
    end
    local folder = workspace:FindFirstChild(MONITORS)
    if folder == nil then
        warn('[BootPanel] missing Workspace.' .. MONITORS .. '; the boot screen will not animate')
        return 0
    end
    local problems = {}
    -- Ordered is not optional: stepFor stops at the first reveal that is not yet
    -- due, so a table that is not ascending by `at` would drop every entry after
    -- the first out-of-order one, on every monitor, silently. Checked here once.
    local previous = -1
    for index, reveal in ipairs(schedule.Reveals) do
        if type(reveal.at) ~= 'number' or reveal.at < previous then
            problems[#problems + 1] = string.format(
                'Reveals[%d].at is %s, after %s; the schedule must ascend', index, tostring(reveal.at), tostring(previous))
        else
            previous = reveal.at
        end
    end
    local needDiagnostic, needLog = reach(schedule)
    -- What the art is authored as. See the blind-spot note further down.
    local authoredVisible = 0
    for _, child in ipairs(folder:GetChildren()) do
        -- Matched exactly the way RoomShell matches its monitors, so the two
        -- modules cannot disagree about what a control room monitor is.
        if string.sub(child.Name, -18) == 'ControlRoomMonitor' then
            local screen = child:FindFirstChild('Screen')
            local ui = screen and screen:FindFirstChild('MonitorUI')
            local boot = ui and ui:FindFirstChild(BOOT_FRAME)
            -- Four of the seven monitors have no BootFrame and never did. The
            -- capture writes BootFrame on exactly the three that have one here,
            -- so a monitor without it is the art, not a defect, and is skipped
            -- rather than reported.
            if boot then
                local entry = {name = child.Name, boot = boot, diagnostic = {}, log = {}, companyLogo = nil}
                local diagnosticRoot = resolveFrom(boot, DIAGNOSTIC_PATH)
                if diagnosticRoot == nil then
                    problems[#problems + 1] = child.Name .. ' has no ' .. BOOT_FRAME .. '.' .. DIAGNOSTIC_PATH
                else
                    local highest = numbered(diagnosticRoot, DIAGNOSTIC_PREFIX, entry.diagnostic, problems)
                    if highest < needDiagnostic then
                        problems[#problems + 1] = string.format('%s has %d %s labels but the schedule drives %d',
                            child.Name, highest, DIAGNOSTIC_PREFIX, needDiagnostic)
                    end
                end
                local logRoot = resolveFrom(boot, LOG_PATH)
                if logRoot == nil then
                    problems[#problems + 1] = child.Name .. ' has no ' .. BOOT_FRAME .. '.' .. LOG_PATH
                else
                    local highest = numbered(logRoot, LOG_PREFIX, entry.log, problems)
                    if highest < needLog then
                        problems[#problems + 1] = string.format('%s has %d %s labels but the schedule drives %d',
                            child.Name, highest, LOG_PREFIX, needLog)
                    end
                end
                entry.companyLogo = boot:FindFirstChild(COMPANY_LOGO)
                if entry.companyLogo == nil then
                    problems[#problems + 1] = child.Name .. ' has no ' .. BOOT_FRAME .. '.' .. COMPANY_LOGO
                end
                for _, label in pairs(entry.diagnostic) do
                    if label.Visible then authoredVisible += 1 end
                end
                for _, label in pairs(entry.log) do
                    if label.Visible then authoredVisible += 1 end
                end
                if entry.companyLogo and entry.companyLogo.Visible then authoredVisible += 1 end
                monitors[#monitors + 1] = entry
            end
        end
    end
    if #monitors == 0 then
        problems[#problems + 1] = MONITORS .. ' has no monitor carrying a ' .. BOOT_FRAME
    end
    -- A KNOWN BLIND SPOT, written down instead of left as a hole. Leaving the
    -- boot takes the schedule back to step 0, which writes Visible=false on
    -- every label -- and that is only "restoring the art" while the art authors
    -- all of them hidden. If it ever does not, this module hides a label the art
    -- meant to show and nothing else in the place would report it. So it is
    -- measured once, here, and turned into a warning rather than an assumption.
    if authoredVisible > 0 then
        problems[#problems + 1] = string.format(
            '%d boot-screen labels are authored Visible; this module drives them from hidden and will hide them',
            authoredVisible)
    end
    if #problems > 0 then
        warn('[BootPanel] incomplete capture: ' .. table.concat(problems, '; '))
    end
    print(string.format('[BootPanel] captured %d boot screens, %d diagnostic and %d log labels at most, %d reveals',
        #monitors, needDiagnostic, needLog, #schedule.Reveals))
    return #monitors
end

-- ========== SCHEDULE ==========
-- How many reveals have come due at `seconds`. Due AT `at`, not after it, so the
-- t=0 block lands on the same tick as the boot command rather than a tick later.
local function stepFor(seconds, schedule)
    local step = 0
    for index, reveal in ipairs(schedule.Reveals) do
        if reveal.at <= seconds then step = index else break end
    end
    return step
end

-- Which labels the schedule wants visible after `step` reveals. Returned as two
-- sparse tables plus one boolean rather than as a list of instructions, so the
-- caller can set EVERY label rather than only the ones this step mentions: the
-- t=5 entry CLEARS the diagnostics, and a caller driven by instructions would
-- have to reconstruct that absence from a missing entry.
local function wanted(step, schedule)
    local diagnostic, log = {}, {}
    local logo = false
    for index, reveal in ipairs(schedule.Reveals) do
        if index > step then break end
        if reveal.clearDiagnostic then diagnostic = {} end
        if reveal.diagnostic then
            for n = reveal.diagnostic[1], reveal.diagnostic[2] do diagnostic[n] = true end
        end
        if reveal.clearLog then
            for n = reveal.clearLog[1], reveal.clearLog[2] do log[n] = nil end
        end
        if reveal.log then
            for n = reveal.log[1], reveal.log[2] do log[n] = true end
        end
        if reveal.companyLogo then logo = true end
    end
    return diagnostic, log, logo
end

-- ========== REFRESH ==========
-- Step-gated, not phase-gated: within one Booting phase this writes about seven
-- times, once per second the schedule says something, and not on the ticks in
-- between. Leaving the phase is its own signature rather than a step number, so
-- it always produces the one write that puts the screen back and re-entering the
-- phase can never be mistaken for a step already applied.
function BootPanel.Refresh(state, config)
    local schedule = config.Shell.BootScreen
    local booting = state.phase == 'Booting'
    local step = booting and stepFor(state.phaseTime, schedule) or 0
    local signature = booting and ('Booting:' .. step) or 'idle'
    if signature == lastSignature then return end
    lastSignature = signature
    local diagnostic, log, logo = wanted(step, schedule)
    for _, mon in ipairs(monitors) do
        if mon.boot.Parent then
            for n, label in pairs(mon.diagnostic) do
                label.Visible = diagnostic[n] == true
            end
            for n, label in pairs(mon.log) do
                label.Visible = log[n] == true
            end
            if mon.companyLogo then mon.companyLogo.Visible = logo end
        end
    end
end

-- The engine's phase is the whole input, and the boot screen is its only
-- consumer, so there is no separate Reset: leaving Booting is the reset, and it
-- is driven by the same signature the animation uses.
return BootPanel
