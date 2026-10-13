--!nocheck
-- Offline check of the end-of-shift report's numbers, with no Studio in the loop.
--
-- The report screen is 610 lines of authored choreography that CANNOT be
-- exercised offline -- it lives in StarterGui and runs on a client. What can be
-- exercised is the only thing the backend adds: the six values it sends. This
-- drives EndShiftBridge.Payload over the endings the engine can reach and
-- asserts every field the screen reads, so a wrong field is caught here instead
-- of on the operator's screen.
--
-- The module is loaded with an explicit environment rather than required: it is
-- a Roblox module and reads `game` at load time, and lune gives every required
-- file its own globals, so injecting a fake `game` through _G does not reach it.
--
--   luau-windows/lune.exe run _tools/endshift_payload_test.luau
--
-- A failure exits 1, and so does a crash -- a checker that dies must never look
-- like a checker that passed (CLAUDE.md 0.6). The check count is asserted too,
-- so a run that silently stops checking cannot pass (same file, second half:
-- an empty set says two false things).

local fs = require('@lune/fs')
local luau = require('@lune/luau')
local process = require('@lune/process')

local failures = 0
local checks = 0
local function check(name, got, want)
    checks += 1
    if got ~= want then
        failures += 1
        print(string.format('FAIL %s: got %s, want %s', name, tostring(got), tostring(want)))
    end
end

-- The clock is pinned so the time fields are asserted against a known hour
-- rather than whatever the run started at. os.date('*t') is the one call the
-- module makes that a test cannot afford to leave to the wall clock.
local clock = {hour = 13, min = 7}
-- The player list is a real (mutable) table rather than an empty one: the
-- dedupe below is per player, so an empty list would make every one of those
-- checks pass without touching the code they are about.
local fakePlayers = {}
local environment = {
    game = {GetService = function() return {GetPlayers = function() return fakePlayers end,
                                           FindFirstChild = function() return nil end} end},
    os = {date = function() return clock end},
    string = string, math = math, table = table, setmetatable = setmetatable,
    ipairs = ipairs, pairs = pairs, pcall = pcall, tostring = tostring,
    type = type, print = print, warn = print, error = error,
}
local source = fs.readFile('src/ReactorBackend/EndShiftBridge.luau')
local Bridge = luau.load(source, {debugName = 'EndShiftBridge', environment = environment})()
check('module loaded', type(Bridge), 'table')
check('module exports Payload', type(Bridge.Payload), 'function')
check('module exports Publish', type(Bridge.Publish), 'function')
check('module exports Request', type(Bridge.Request), 'function')
check('module exports Bind', type(Bridge.Bind), 'function')

local function engine(overrides)
    local s = {phase = 'Report', shift = 2, elapsed = 3725.25, energy = 640,
               quota = 1024, failure = nil}
    for k, v in pairs(overrides) do s[k] = v end
    return {state = s}
end

local function expect(e, reason)
    local p = Bridge.Payload(e)
    check(reason .. ' lines is empty', #p.lines, 0)
    check(reason .. ' reason', p.reason, reason)
    check(reason .. ' total', p.total, 0)
    check(reason .. ' shift', p.shift, e.state.shift)
    check(reason .. ' metu', p.metu, 2)
    check(reason .. ' OT', p.session.OT, '01:02.250')
    check(reason .. ' ST.Hour', p.session.ST.Hour, 1)
    check(reason .. ' ST.Min', p.session.ST.Min, 7)
    check(reason .. ' ST.Period', p.session.ST.Period, 'PM')
    check(reason .. ' ST.CurrentEnergy', p.session.ST.CurrentEnergy, 640)
    check(reason .. ' ST.TargetEnergy', p.session.ST.TargetEnergy, 1024)
    check(reason .. ' NG', p.session.NG, 0)
    check(reason .. ' NL', p.session.NL, 0)
end

expect(engine({phase = 'Report'}), 'Quota')
expect(engine({phase = 'Failed', failure = 'Power extraction assembly overload'}),
    'Power extraction assembly overload')
-- A failure with no reason recorded must still produce a string: the screen
-- compares p2 against one literal, so a nil would reach it as nil.
expect(engine({phase = 'Failed', failure = nil}), 'Failure')
-- Midnight is the one hour where the 12-hour clock wraps to 12 rather than 0.
clock = {hour = 0, min = 0}
local midnight = Bridge.Payload(engine({elapsed = 0}))
check('midnight ST.Hour', midnight.session.ST.Hour, 12)
check('midnight ST.Period', midnight.session.ST.Period, 'AM')
check('zero OT', midnight.session.OT, '00:00.000')
clock = {hour = 13, min = 7}
-- Over an hour of operating time rolls into the hour field rather than into the
-- minutes, which is the only way this formatter can be wrong.
check('long OT', Bridge.Payload(engine({elapsed = 7325})).session.OT, '02:02.000')

-- Publish is called once a second for the whole shift, so the live-phase path
-- has to be a no-op with no players and no remote -- it must not throw.
local okLive = pcall(Bridge.Publish, engine({phase = 'Running'}))
check('publish during Running does not throw', okLive, true)
local okEnd = pcall(Bridge.Publish, engine({phase = 'Failed', failure = 'x'}))
check('publish during Failed does not throw with no remote', okEnd, true)
-- The dedupe itself, which is where this went wrong live. The key used to be
-- the Player instance in a weak table, and the entry was collected out from
-- under it -- so the SAME ending was sent twice, 60 s apart. The key is a
-- UserId in an ordinary table now, and these checks are what says so: the
-- player list is real here (the fake service returns it) because with no
-- players every dedupe check would pass vacuously.
local sentCount = 0
local realSend = Bridge.Send
Bridge.Send = function() sentCount += 1 return true end
fakePlayers[1] = {UserId = 7194488150, Name = 'operator'}
Bridge.Publish(engine({phase = 'Failed', failure = 'x'}))
check('first ending is sent', sentCount, 1)
Bridge.Publish(engine({phase = 'Failed', failure = 'x'}))
Bridge.Publish(engine({phase = 'Failed', failure = 'y'}))
check('the same ending is never sent twice', sentCount, 1)
Bridge.Publish(engine({phase = 'Report'}))
check('a different ending at the same shift is sent', sentCount, 2)
Bridge.Publish(engine({phase = 'Running'}))
check('a live phase sends nothing', sentCount, 2)
Bridge.Publish(engine({phase = 'Failed', failure = 'x'}))
check('leaving the ending re-arms it', sentCount, 3)
Bridge.Send = realSend

-- The three screen words, routed onto the engine's two commands.
local function fakeEngine(failNext)
    local e2 = {state = {phase = 'Failed', shift = 2, quota = 512,
                         elapsed = 0, energy = 0}, calls = {}}
    function e2:Command(action)
        table.insert(e2.calls, action)
        if failNext then return false, 'No next shift available' end
        return true
    end
    return e2
end
local function lastCall(e2)
    return e2.calls[#e2.calls] or 'none'
end
local e3 = fakeEngine(false)
check('Reset accepted', Bridge.Request(e3, nil, 'Reset'), true)
check('Reset maps to reset', lastCall(e3), 'reset')
local e4 = fakeEngine(false)
check('Next accepted', Bridge.Request(e4, nil, 'Next'), true)
check('Next maps to next', lastCall(e4), 'next')
local e5 = fakeEngine(false)
check('Lobby accepted (no lobby here)', Bridge.Request(e5, nil, 'Lobby'), true)
check('Lobby maps to reset, not to a dead end', lastCall(e5), 'reset')
local e6 = fakeEngine(false)
check('unknown mode refused', Bridge.Request(e6, nil, 'Teleport'), false)
check('unknown mode commands nothing', #e6.calls, 0)
local e7 = fakeEngine(true)
check('engine refusal is passed through', Bridge.Request(e7, nil, 'Next'), false)
check('engine refusal still asked once', #e7.calls, 1)

check('cases ran', checks >= 45, true)
print(string.format('%d checks, %d failed', checks, failures))
process.exit(failures == 0 and 0 or 1)
