--!strict
-- The end-of-shift handshake, both directions, and nothing else.
--
-- The legacy screen (StarterGui.ScreenGui.EndShiftHandler, 610 lines) has been
-- in this place since before the backend and has never once appeared, because
-- its two ends were never connected: nothing fired ReplicatedStorage.EndShift,
-- nothing listened to ReplicatedStorage.MiscEvent -- which is the remote that
-- screen actually fires -- and nothing fired ReplicatedStorage.ResetEvent. A
-- shift that reached Report or Failed therefore had no exit at all: Engine
-- refuses every other command with 'Shift ended' past the ending, and that
-- refusal is a warn on the server console, not anything a player can see. The
-- operator hit exactly this on 2026-10-13 and reported it as 'suddenly the
-- shift ended'.
--
-- This module is the missing transport. Every gate stays Engine's own: 'next'
-- and 'reset' are its commands with its phase checks, and the two flags the
-- screen already reads (Stats.NextShift, Stats.ResetShift) are published from
-- those same phases, so a client can only ask for a transition the engine is
-- already willing to make.
--
-- THE MONEY ON THE REPORT IS ZERO, AND THAT IS A TRUE STATEMENT. This build has
-- no economy: nothing pays out, so nothing is gained or lost. p1 (the per-stat
-- money lines) is therefore sent EMPTY rather than filled with zeros -- the
-- screen appends no stat row at all for an empty table (EndShiftHandler line
-- 505) -- and the screen has a designed zero-total state of its own (line 553:
-- grey money text and ' ... Good Job'), so a zeroed total lands on an authored
-- branch instead of being a payload shape the UI never considered. Every other
-- field on the report is the engine's real number: shift, quota, energy
-- produced, operating time, shutdown clock, and the reason the shift ended.
-- What the screen is genuinely missing is the economy it reports on; that is a
-- design decision and it belongs to the operator (QUESTIONS.md), not here.

local Players = game:GetService('Players')
local ReplicatedStorage = game:GetService('ReplicatedStorage')

local EndShiftBridge = {}

-- The one number an economy would move, named so that it has a single place to
-- be replaced when there is something to report. Until then it is the absence
-- of a payout, which is what this build actually does.
local NO_ECONOMY = 0

-- The screen prints the operating time into a label authored 'XX:XX.XXX'
-- (IntermissionFrame.AdditionFrame.TextFrame.OperationalLabel), so this is that
-- shape rather than a format of my choosing.
local function operatingTime(seconds: number): string
    local whole = math.max(0, math.floor(seconds))
    local millis = math.floor((seconds - whole) * 1000)
    return string.format('%02d:%02d.%03d',
        math.floor(whole / 3600), math.floor(whole % 3600 / 60), millis)
end

-- The six arguments EndShift.OnClientEvent is documented to carry, built from
-- engine state alone. Pure: it reads, it never fires, which is what lets the
-- numbers be checked without a screen or a player.
function EndShiftBridge.Payload(engine)
    local s = engine.state
    local now = os.date('*t')
    local hour = now.hour % 12
    if hour == 0 then hour = 12 end
    return {
        -- p1: per-stat money lines. Empty, because there are no money events to
        -- report and an empty table makes the screen show no row at all.
        lines = {},
        -- p2: the reason, and also the field that tells the screen the quota
        -- was met ('Quota' is the only string it compares against).
        reason = s.phase == 'Failed' and (s.failure or 'Failure') or 'Quota',
        total = NO_ECONOMY,
        shift = s.shift,
        session = {
            -- s.elapsed, not s.time: elapsed only accumulates while the reactor
            -- is Running, so it is operating time. s.time also counts the cold
            -- start-up, which is not time the plant operated.
            OT = operatingTime(s.elapsed),
            ST = {Hour = hour, Min = now.min,
                  Period = now.hour >= 12 and 'PM' or 'AM',
                  CurrentEnergy = math.floor(s.energy), TargetEnergy = s.quota},
            NG = NO_ECONOMY, NL = NO_ECONOMY,
        },
        -- p6: 2 or above is the screen's leave-the-label-alone branch, and that
        -- is the honest reading here -- this build models no METU failure, so
        -- the authored 'METU STATUS - FULLY OPERATIONAL' is not contradicted by
        -- anything and there is no other status to report.
        metu = 2,
    }
end

-- Sent once per ending PER PLAYER. Runtime calls Publish every second and the
-- screen is a two-second tween sequence, so an unconditional send would restart
-- it once a second. The key is per player rather than one module-wide flag so
-- that a player who joins while the shift is already over is still sent it.
--
-- The key is a UserId in an ORDINARY table, and that is a correction rather than
-- a style choice. This started as `setmetatable({}, {__mode = 'k'})` keyed by
-- the Player instance, on the assumption that the DataModel's own hold on the
-- player keeps the entry alive. It does not: measured live on 2026-10-13, with
-- one player in the game, an entry keyed by a Player that is still in Players
-- was collected on the 8th GC cycle of a purely allocating loop that held no
-- other Lua reference to it. The consequence was visible in the log -- the same
-- ending printed the report line TWICE, exactly 60 s apart, with no phase
-- change between them: the dedupe had lapsed because its key had been collected.
-- A number cannot be collected, so `player.UserId` is the key. A player who
-- leaves keeps one number until the ending ends, and the loop below is what
-- clears it.
local sentKey = {}

function EndShiftBridge.Send(engine, player): boolean
    local remote = ReplicatedStorage:FindFirstChild('EndShift')
    if not (remote and remote:IsA('RemoteEvent')) then
        warn('[ReactorBackend] EndShift missing; the end-of-shift report cannot be shown')
        return false
    end
    local p = EndShiftBridge.Payload(engine)
    remote:FireClient(player, p.lines, p.reason, p.total, p.shift, p.session, p.metu)
    return true
end

function EndShiftBridge.Publish(engine)
    local s = engine.state
    if s.phase ~= 'Report' and s.phase ~= 'Failed' then
        -- Leaving the ending closes the window: the next one is a new ending
        -- even at the same shift number, and must be sent again.
        for userId in pairs(sentKey) do sentKey[userId] = nil end
        return
    end
    local key = s.shift .. ':' .. s.phase
    for _, player in ipairs(Players:GetPlayers()) do
        if sentKey[player.UserId] ~= key then
            sentKey[player.UserId] = key
            if EndShiftBridge.Send(engine, player) then
                print(string.format('[ReactorBackend] end-of-shift report: shift %d %s -> %s',
                    s.shift, s.phase, player.Name))
            end
        end
    end
end

-- The reply the screen parses. p1[1] is the mode on an accepted transition and
-- false on a refused one: the legacy screen matches on that first field, so
-- false leaves its buttons alone, while EndShiftResume reads the refusal and
-- puts the report back in front of the player instead of leaving them on an
-- intermission that is not going anywhere.
local function reply(misc, player, mode, engine, err)
    if not (player and misc) then return end
    misc:FireClient(player, {mode, engine.state.shift,
        mode and 'Accepted' or 'Refused', err})
end

-- The screen's own three words routed onto the engine's own two commands. The
-- decision is here and the wiring is in Bind, so this can be driven from a test
-- with no remote in the picture at all.
function EndShiftBridge.Request(engine, player, mode): boolean
    local misc = ReplicatedStorage:FindFirstChild('MiscEvent')
    if misc and not misc:IsA('RemoteEvent') then misc = nil end
    local action = mode == 'Next' and 'next' or (mode == 'Reset' and 'reset' or nil)
    if mode == 'Lobby' then
        -- 'Lobby' is the mode the screen holds when nobody has chosen one of the
        -- three buttons, so it is the DEFAULT path -- whatever it does is what a
        -- player gets for holding the acknowledge button, and it must not be a
        -- dead end. The original's lobby is where the intermission happens and
        -- where the next shift is bought; this place has no lobby flow at all
        -- (no TeleportService call exists anywhere in it) and no economy, so
        -- there is nothing to send a player to. The one transition this build
        -- does have is the engine's own reset. Refusing instead would answer the
        -- operator's actual complaint ('the shift ended and there is no way out')
        -- with a console line and no exit.
        --
        -- The request is rewritten to 'Reset' rather than carried through as
        -- 'Lobby', because the request word is also what the screen is told on
        -- the way back: its reply handler greys out CONTINUE and RESTART and
        -- leaves the button reading 'L' for a lobby reply, and reads 'R' -- the
        -- shift is being replayed -- only for a Reset one. A print rather than a
        -- warn, because this is now the ordinary path and not a fault.
        print('[ReactorBackend] no lobby flow in this place: the acknowledge button replays the shift')
        mode = 'Reset'
        action = 'reset'
    end
    if not action then
        -- Anything else is a mode this place has no meaning for, and guessing
        -- which transition it wanted is worse than saying so.
        warn('[ReactorBackend] post-shift request ' .. tostring(mode) ..
            ' has no destination in this place')
        reply(misc, player, false, engine, 'Unknown post-shift request')
        return false
    end
    local ok, err = engine:Command(action)
    if not ok then
        warn('[ReactorBackend] shift transition refused: ' .. tostring(err))
        reply(misc, player, false, engine, err)
        return false
    end
    reply(misc, player, mode, engine, nil)
    print(string.format('[ReactorBackend] shift transition %s -> shift %d', mode, engine.state.shift))
    return true
end

-- Bind returns the remote names it actually bound rather than nothing: a
-- transport that silently failed to attach looks exactly like one with nothing
-- to report, and Runtime publishes this string as an attribute so the live
-- check has something to read that is not a print (CLAUDE.md 0.19).
function EndShiftBridge.Bind(engine, publish): string
    local bound = {}
    local misc = ReplicatedStorage:FindFirstChild('MiscEvent')
    if misc and misc:IsA('RemoteEvent') then
        table.insert(bound, 'MiscEvent')
        misc.OnServerEvent:Connect(function(player, mode)
            if EndShiftBridge.Request(engine, player, mode) and publish then
                -- Published straight away rather than waiting for the next tick:
                -- a shift that restarts must repaint the console and the seven
                -- monitors on the frame the player let go of the button, not up
                -- to a second later while every lever still reads as dead.
                publish(engine.state)
            end
        end)
    else
        warn('[ReactorBackend] MiscEvent missing; the report screen has no way to ask for a transition')
    end
    -- ResetEvent is the pre-backend remote. Its binding is kept because it is
    -- the name the original used and a future caller should find it live; it
    -- carries a bare mode string and has no reply channel, so nothing this
    -- screen does can come back through it.
    local reset = ReplicatedStorage:FindFirstChild('ResetEvent')
    if reset and reset:IsA('RemoteEvent') then
        table.insert(bound, 'ResetEvent')
        reset.OnServerEvent:Connect(function(_, mode)
            local ok, err = engine:Command(mode == 'next' and 'next' or 'reset')
            if not ok then warn('[ReactorBackend] shift transition refused: ' .. tostring(err)) end
            if publish then publish(engine.state) end
        end)
    end
    return table.concat(bound, '+')
end

return EndShiftBridge
