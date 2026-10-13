--!strict
-- The subspace-forecast monitor: the deep-scan announcement, and the
-- all-monitors EFE banner.
--
-- WHY THIS IS ITS OWN MODULE. It needs every frame rather than the one-second
-- logic gate: the announcement is three sounds and a text swap spread over
-- 14.63 s, and hanging that on the gate would land each one up to a second late
-- on a sequence whose own recorded gaps are 1.7 s apart. So it takes the same
-- shape FacilityCascade does -- Refresh on the gate to ARM, Step on every
-- Heartbeat to PLAY -- and Step is a public function rather than work hidden
-- inside a connection, for the reason in CLAUDE.md 0.19.
--
-- WHAT IT OWNS, AND WHAT IT MUST NOT. RoomShell owns which FACE a monitor shows,
-- and MonitorUI's own header names what it deliberately leaves alone: EFEFrame
-- among them. Nothing in the place has ever written EFEFrame or the deep-scan
-- announcement -- script_grep over the DataModel returns nothing for
-- TimeSliceTemplate, and before this module nothing returned for the
-- announcement either -- so there is no second writer to collide with.
--
-- ONE BANNER WAS MISSING AND WAS PUT BACK. Six of the seven monitors carry an
-- EFEFrame and AlertsControlRoomMonitor did not, so the manual's 'all monitors
-- will display a warning' would have skipped the alarms screen -- the one screen
-- where its absence is most conspicuous. The subtree is byte-identical on all
-- six (two black EventFrames carrying 'EFE IMMINENT' and 'BRACE FOR ENERGY
-- FLUCTUATION EVENT' in yellow), and only the root frame's own transform varies;
-- the Alerts monitor was given a copy of the full-width variant, which is what
-- its own MainMonitorFrame uses. This is a restoration of a symmetric element,
-- not a new one, and it is additive: nothing existing was moved or changed.
--
-- THE TRIGGER. The deep scan rides the chain's own message,
-- Config.Shift.StartupSteps[9] = 'INITIATING DEEP SCAN PROCEDURE', the same way
-- FacilityCascade rides its beats: the chain supplies WHEN, and the capture
-- supplies what happens once it has. Anchoring on the message rather than a
-- clock is what survives a retime of the twenty-nine seconds around it.
--
-- THE VERDICT IS A REAL FORECAST. The capture shows the text resolving into one
-- of two verdicts, both naming a clock. The only future subspace event this
-- engine models is the Equinox, and Engine:Step latches it at a known
-- elapsed -- so the deep scan projects that clock and says whether it lands
-- inside the facility's horizon. If EquinoxSeconds is ever retuned the verdict
-- follows it; nothing here is a fixed string.

local ForecastPanel = {}

-- ========== ADDRESSES ==========
local MONITORS = 'Monitors'
local MONITOR_SUFFIX = 'ControlRoomMonitor'
local FORECAST_MONITOR = 'ForecastControlRoomMonitor'
-- The announcement lives inside MainMonitorFrame, the face RoomShell shows for
-- Starting and Running. RoomShell writes that frame's own Visible; every write
-- here is on a child of it, so the two still never touch one property.
local ANNOUNCEMENT_PATH = 'Screen.MonitorUI.MainMonitorFrame.AnnouncementFrame'
local TEXT_NAME = 'AnnouncementText'
-- The three sounds sit on the monitor's Screen, not inside the UI.
local SOUND_NAMES = {'Beep', 'EFEPing', 'TimelineComplete'}
-- The banner is on EVERY monitor, which is the manual's own description
-- ('when an EFE is about to occur, all monitors will display a warning') and
-- exactly what the capture shows: all seven going true within 70 ms of each
-- other.
local BANNER_PATH = 'Screen.MonitorUI.EFEFrame'

-- ========== CAPTURE ==========
local cfg = nil
local ann = nil
local annText = nil
local sounds = nil
local banners = {}
-- The live announcement, or nil. {t = seconds since it began, breach, verdict,
-- color}. t is advanced by Step, so the offsets in Config are real seconds
-- rather than gate ticks.
local sequence = nil
-- The last chain step the deep scan was armed for. Zero means not armed, and it
-- returning to zero is how a rewound chain is noticed.
local lastArming = 0
-- The banner has a life of its own. The capture measures it at 10.25 s from the
-- verdict, and the announcement's timeline ends at 14.63 s -- only 9.59 s after
-- that verdict -- so bounding the banner by `sequence` would cut the recorded
-- 10.25 s short by 0.66 s. A constant the code does not honour is a number that
-- is quietly wrong (CLAUDE.md 0.18), so the banner is a countdown of its own.
-- Its other input, the Equinox, is far too slow to need every frame and is
-- latched by Refresh.
local equinoxOn = false
local bannerLeft = 0
local bannerOn: boolean? = nil

local function resolveFrom(inst, path)
    local node = inst
    for token in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

-- Seconds of facility time to a wall clock. `minutes` is the offset from
-- Clock.StartHour, and the wrap is a full day, so an event projected past
-- midnight reads as the morning hour the capture's verdicts name rather than as
-- a 25th hour.
local function formatClock(minutes, startHour)
    local total = math.floor(startHour * 60 + minutes) % 1440
    if total < 0 then total = total + 1440 end
    local hour = math.floor(total / 60) % 12
    if hour == 0 then hour = 12 end
    local minute = total % 60
    local suffix = total < 720 and 'AM' or 'PM'
    return string.format('%d:%02d %s', hour, minute, suffix)
end

function ForecastPanel.Initialize(config)
    cfg = config
    ann, annText, sounds, banners = nil, nil, nil, {}
    sequence = nil
    lastArming = 0
    equinoxOn = false
    bannerLeft = 0
    bannerOn = nil
    local f = config and config.Forecast
    if f == nil or f.DeepScan == nil then
        warn('[ForecastPanel] Config.Forecast.DeepScan is missing; the forecast monitor will not run')
        return 0
    end
    local folder = workspace:FindFirstChild(MONITORS)
    if folder == nil then
        warn('[ForecastPanel] missing Workspace.' .. MONITORS .. '; the forecast monitor will not run')
        return 0
    end
    local problems = {}
    local forecast = folder:FindFirstChild(FORECAST_MONITOR)
    if forecast == nil then
        problems[#problems + 1] = 'no ' .. FORECAST_MONITOR
    else
        ann = resolveFrom(forecast, ANNOUNCEMENT_PATH)
        if ann == nil then
            problems[#problems + 1] = FORECAST_MONITOR .. ' has no ' .. ANNOUNCEMENT_PATH
        else
            annText = ann:FindFirstChild(TEXT_NAME)
            if annText == nil then
                problems[#problems + 1] = ANNOUNCEMENT_PATH .. ' has no ' .. TEXT_NAME
            end
        end
        local screen = forecast:FindFirstChild('Screen')
        if screen == nil then
            problems[#problems + 1] = FORECAST_MONITOR .. ' has no Screen, so the deep-scan sounds are silent'
        else
            sounds = {}
            for _, name in ipairs(SOUND_NAMES) do
                local sound = screen:FindFirstChild(name)
                if sound == nil then
                    problems[#problems + 1] = 'Screen has no ' .. name .. ' sound'
                else
                    sounds[name] = sound
                end
            end
        end
    end
    -- The banner list is collected over ALL monitors, not just the forecast one,
    -- because that is where the capture puts it. Matched the way RoomShell
    -- matches its monitors so the two cannot disagree about what one is.
    for _, child in ipairs(folder:GetChildren()) do
        if string.sub(child.Name, -#MONITOR_SUFFIX) == MONITOR_SUFFIX then
            local banner = resolveFrom(child, BANNER_PATH)
            if banner == nil then
                problems[#problems + 1] = child.Name .. ' has no ' .. BANNER_PATH
            else
                banners[#banners + 1] = banner
            end
        end
    end
    if #problems > 0 then
        warn('[ForecastPanel] incomplete capture: ' .. table.concat(problems, '; '))
    end
    print(string.format('[ForecastPanel] captured the deep-scan announcement and %d EFE banners', #banners))
    return #banners
end

-- Puts the announcement back to its authored rest. Called on a rewound chain,
-- so a run that is reset mid-scan does not leave the next one's scan as a screen
-- that is already lit.
local function abort()
    sequence = nil
    bannerLeft = 0
    if ann then ann.Visible = false end
    if annText then annText.TextColor3 = cfg.Forecast.DeepScan.IdleColor end
    if sounds then
        for _, name in ipairs(SOUND_NAMES) do
            if sounds[name] then sounds[name].Playing = false end
        end
    end
end

local function begin(state, config)
    local d = config.Forecast.DeepScan
    -- Projected seconds to the Equinox. During Starting, elapsed is still zero
    -- -- it only advances in Running -- so the projection is the whole window
    -- rather than a remainder, which is correct: the scan fires well before the
    -- reactor is up.
    local untilEquinox = config.Events.EquinoxSeconds - state.elapsed
    if untilEquinox < 0 then untilEquinox = 0 end
    local breach = untilEquinox <= config.Forecast.BreachHorizonSeconds
    local clock = formatClock(
        (state.time + untilEquinox) * config.Forecast.Clock.MinutesPerSecond,
        config.Forecast.Clock.StartHour)
    sequence = {
        t = 0,
        breach = breach,
        verdict = (breach and d.Breach or d.Anomaly) .. clock,
        color = breach and d.BreachColor or d.AnomalyColor,
    }
    if ann then ann.Visible = true end
    if annText then
        annText.Text = d.Processing
        annText.TextColor3 = d.IdleColor
    end
    -- Armed silent, so the sequence's own first sound is the sequence's and not
    -- a leftover from the run before.
    if sounds then
        for _, name in ipairs(SOUND_NAMES) do
            if sounds[name] then sounds[name].Playing = false end
        end
    end
end

-- ========== REFRESH (the one-second gate) ==========
-- Arms the scan at the chain's deep-scan message, and latches the one slow input
-- the banner has. Everything with a sub-second edge -- the announcement's beats
-- and the banner's own 10.25 s -- is played by Step instead, which is also why
-- Refresh does not write the banner itself.
function ForecastPanel.Refresh(state, config)
    if config ~= nil then cfg = config end
    if cfg == nil or cfg.Forecast == nil then return end
    equinoxOn = state.equinox == true
    local d = cfg.Forecast.DeepScan
    if state.startupStep >= d.Step and lastArming < d.Step then
        lastArming = state.startupStep
        begin(state, cfg)
    elseif state.startupStep < d.Step and lastArming > 0 then
        -- The chain went backwards, which only a reset does. Drop the screen.
        lastArming = 0
        abort()
    end
end

-- ========== STEP (every Heartbeat) ==========
-- Plays one advance of the announcement. Each event fires on the frame its
-- offset is first crossed and never again, which is what `crossed` is: a strict
-- inequality against the previous t, so a long frame that jumps two offsets at
-- once still fires both in order instead of skipping the first.
function ForecastPanel.Step(dt)
    if cfg == nil then return end
    local d = cfg.Forecast.DeepScan
    if sequence ~= nil then
        local previous = sequence.t
        sequence.t = previous + dt
        local now = sequence.t
        local function crossed(at) return previous < at and now >= at end
        if crossed(d.BeepAt) and sounds and sounds.Beep then
            sounds.Beep.Playing = true
        end
        if crossed(d.VerdictAt) then
            if annText then
                annText.Text = sequence.verdict
                annText.TextColor3 = sequence.color
            end
            if sounds then
                -- The capture swaps the beep for the ping on the same poll as the
                -- verdict, so these three are one beat, not three.
                if sounds.Beep then sounds.Beep.Playing = false end
                if sounds.EFEPing then sounds.EFEPing.Playing = true end
            end
            -- The banner starts here -- on a breach verdict only -- and outlives
            -- the announcement it arrived with.
            if sequence.breach then bannerLeft = cfg.Forecast.BannerSeconds end
        end
        if crossed(d.PingOffAt) and sounds and sounds.EFEPing then
            sounds.EFEPing.Playing = false
        end
        if crossed(d.EndAt) then
            if ann then ann.Visible = false end
            if annText then annText.TextColor3 = d.IdleColor end
            if sounds and sounds.TimelineComplete then
                sounds.TimelineComplete.Playing = true
            end
        end
        if crossed(d.TimelineOffAt) then
            if sounds and sounds.TimelineComplete then
                sounds.TimelineComplete.Playing = false
            end
            sequence = nil
        end
    end
    -- The banner, after the announcement so it reflects this frame's verdict.
    -- Advanced here rather than on the one-second gate because its edges are the
    -- whole of it: a breach warning that arrives a second late is a warning that
    -- arrives with the event.
    if bannerLeft > 0 then
        bannerLeft = bannerLeft - dt
        if bannerLeft < 0 then bannerLeft = 0 end
    end
    local on = equinoxOn or bannerLeft > 0
    if on ~= bannerOn then
        bannerOn = on
        for _, banner in ipairs(banners) do
            if banner.Parent then banner.Visible = on end
        end
    end
end

return ForecastPanel
