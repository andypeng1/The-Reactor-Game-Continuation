--!nocheck
-- Offline answer to the question the operator's own complaint asks:
--   "在 airemake 里面开机之后玩了一会之后，突然就是 shift ended 了"
--
-- The offline pilot in _tools/MCP_FlowCollector.luau already reaches the quota on
-- all three shifts, but it issues a command almost every tick: it purges at
-- pressure >= 60, retargets the CBLs and the pumps each tick, repairs on a
-- threshold, and runs a bang-bang fan controller against the chamber pressure. It
-- is a closed-loop controller, not a player. It answers "can the engine reach
-- Report" and says nothing about whether a HUMAN can.
--
-- So this file sweeps cheap, set-and-forget policies and counts EVERY command,
-- because the click count is the thing the operator has to perform. A policy that
-- reaches Report for 20 clicks over six minutes is playable. One that needs a
-- command every tick is not.
--
-- Run: luau-windows/lune.exe run _tools/quota_policy_sim.luau
--
-- A crash exits 1 and so does a failed assertion, because a checker that dies must
-- never look like a checker that passed (CLAUDE.md 0.6). This is a SIMULATION and
-- is labelled one throughout: it CANNOT close TODO 3.14 (1), which asks for the
-- live path. What it can do is say whether that live run is worth attempting, and
-- with what cadence.
--
-- WHY THE SECOND AXIS IS THE FAN COUNT. The first pass swept the fans as a binary
-- -- all six on or all six off -- and found exactly one winner, at 38 clicks. That
-- is a lot of clicks to ask of a person, and the reason is arithmetic rather than
-- difficulty: at T = 12000 the state-1 pressure line is worth
--
--     110 + 0.01 * 12000 = 230 PSI/tick
--
-- and the fans are worth a flat 60 each, so six of them remove 360 and none remove
-- 0. Both of those settings miss the line, one downward and one upward, and the
-- one that misses upward has to be held down with the atmosphere vent -- a 26 s
-- cooldown, so a nine-click bill across a 349 s shift. Four fans remove 240 and
-- miss by ten. The count is the axis the first pass could not see.

local fs = require('@lune/fs')
local luau = require('@lune/luau')
local process = require('@lune/process')

local failures = 0
local function check(name, got, want)
    if got ~= want then
        failures += 1
        print(string.format('FAIL %s: got %s, want %s', name, tostring(got), tostring(want)))
    end
end

-- ========== LOADING THE REAL MODULES ==========
-- Config reads only Color3 and Vector3 at load time (checked by grep, not
-- assumed). Engine reads no Roblox global at all, which is why it can be driven
-- here; its header names Engine.new(config, random) as the test seam for this.
local function stubColor()
    local c = {}
    function c.fromRGB(r, g, b) return {r = r, g = g, b = b} end
    function c.new(r, g, b) return {r = r, g = g, b = b} end
    return c
end
local environment = {
    Color3 = stubColor(), Vector3 = {new = function(x, y, z) return {x = x, y = y, z = z} end},
    string = string, math = math, table = table, setmetatable = setmetatable,
    ipairs = ipairs, pairs = pairs, pcall = pcall, tostring = tostring,
    tonumber = tonumber, type = type, print = print, warn = print, error = error,
    assert = assert, select = select, next = next, rawget = rawget, rawset = rawset,
}
local Config = luau.load(fs.readFile('src/ReactorBackend/Config.luau'),
    {debugName = 'Config', environment = environment})()
local Engine = luau.load(fs.readFile('src/ReactorBackend/Engine.luau'),
    {debugName = 'Engine', environment = environment})()

check('Config loaded', type(Config), 'table')
check('Engine exports new', type(Engine.new), 'function')

-- Deterministic on purpose, same Lehmer generator as the flow collector, so two
-- runs of this file are comparable line for line. Sweeping policies against one
-- noise stream compares the POLICIES; reseeding per policy would compare the noise.
local function makeRng(seed)
    local state = seed
    return function(lo, hi)
        state = (state * 48271) % 2147483647
        return lo + math.floor((state - 1) / 2147483646 * (hi - lo + 1))
    end
end

-- A CBL's gauge ramps at CBLPressurePerLevel 0.6 per tick from zero and is only
-- read for harm above CBLStressThreshold 75, so the threshold is the ONE number
-- here that trades clicks for margin directly: a purge every 75/0.6 = 125 s is
-- two purges in a 349 s shift, a purge every 60/0.6 = 100 s is three. The sweep
-- below runs both, because "how much margin" is a number this file should pick by
-- measurement rather than by taste.
local SHUTDOWN_COOL = 16500  -- the command refuses at ShutdownLimit 17000; leave margin
-- The atmosphere vent is a one-shot -3000 on a 26 s cooldown. It is charged as a
-- click even when the engine's own cooldown refuses it, so a policy that spams it
-- is not a cheap policy and must not look like one in the table.
local AVB_AT = 10500

-- ========== ONE POLICY, ONE SHIFT ==========
-- opts.pumps: 0..3, the coolant level every pump is parked at (0 = leave them off)
-- opts.fansOn: 0..6, how many of the six outtake fans are left RUNNING
-- opts.cbl:   nil = leave the boot default (level 2), else the level to park at
-- opts.purgeAt: the CBL gauge at which every device over it is purged
--
-- A pump's boot level is already 1 (Engine.new's own default), so parking it at
-- level 1 is ONE click -- the ON button -- and the level button is only charged
-- when the policy asks for a different level. The first pass charged both and
-- over-counted every row by three.
local function plan(seed, opts, trace)
    local commands = 0
    local e = Engine.new(Config, makeRng(seed))
    local function must(action, index, value)
        commands += 1
        local ok, err = e:Command(action, index, value)
        assert(ok, string.format('%s refused: %s', action, tostring(err)))
    end
    -- The set-and-forget block is applied ONCE, on the first Running tick, and the
    -- clicks it costs are charged to the policy -- a policy that has to re-touch a
    -- control every tick is exactly what the sweep is looking for.
    local tick = 0
    local function advance(n) for _ = 1, n do tick += 1; e:Update(1) end end
    must('monitor_power'); must('shutters'); must('boot')
    advance(Config.Shift.BootSeconds)
    must('start')
    -- THE SET-AND-FORGET BLOCK GOES HERE, DURING THE CHAIN, AND THAT PLACEMENT IS
    -- THE WHOLE POINT OF THIS PARAGRAPH.
    --
    -- It used to run on the first LOOP iteration instead, i.e. after
    -- `advance(StartupSeconds + 5)`. The chain is 113.4 s long and the advance is
    -- 118 s, so the phase is already `Running` for the last four of those calls --
    -- with no coolant in the machine and three CBLs at level 2, because the pumps
    -- are only switched on by this block. Measured (not reasoned): 3 devices at
    -- level 2 make heat 6, so the entry temperature line runs at
    -- 6 * CBLHeat 65 * scale 0.4 = 156 F/s for those four seconds, which is 615 F.
    --
    -- The whole trajectory then enters Running about 615 F hot, and at
    -- temperatures near 10000 the state-1 line is worth StateSlope 0.01 per degree,
    -- so 615 F is worth about 0.004 * 615 = +2.5 PSI/s on a shift that spends
    -- 350 s below the line. That is ~800 PSI of margin the machine never had.
    -- This file's headline numbers were therefore ~650 PSI optimistic (its floor
    -- read Pmin 3226 where the live shift reached 2804), and the live run is what
    -- caught it -- which is the reason a live run is worth doing at all.
    --
    -- Nothing here needed a phase gate lifted to move the block up: `fan`,
    -- `cbl`, `pump_on` and `pump_level` carry no phase gate (Engine:Command's only
    -- global gate is Failed/Report), and a player throwing these five clicks during
    -- a 113 s chain is exactly what the live run did.
    for i = 1, 6 - opts.fansOn do must('fan', i) end
    if opts.cbl then for i = 1, 3 do must('cbl', i, opts.cbl) end end
    if opts.pumps > 0 then
        for i = 1, 3 do
            must('pump_on', i)
            if opts.pumps ~= 1 then must('pump_level', i, opts.pumps) end
        end
    end
    advance(Config.Shift.StartupSeconds + 5)
    if e.state.phase ~= 'Running' then return {phase = e.state.phase, tick = tick, commands = commands} end

    local purges, vents, maxTemp, minTemp = 0, 0, e.state.temperature, e.state.temperature
    local minPressure = e.state.pressure
    local quotaAt, shutdownAt, refusals = nil, nil, 0
    for _ = 1, 9000 do
        tick += 1
        e:Update(1)
        local s = e.state
        if s.phase ~= 'Running' then break end
        maxTemp = math.max(maxTemp, s.temperature)
        minTemp = math.min(minTemp, s.temperature)
        minPressure = math.min(minPressure, s.pressure)
        if trace then
            trace[#trace + 1] = string.format('t=%4d phase=%-8s T=%6d P=%6d stress=%5.1f energy=%5.1f state=%d fans=%d',
                tick, s.phase, math.floor(s.temperature), math.floor(s.pressure),
                s.peaStress, s.energy, s.pressureState, (function() local n = 0
                    for _, on in ipairs(s.fans) do if on then n += 1 end end return n end)())
        end
        -- Purging only the device that is actually over its gauge, rather than all
        -- three on the worst one: the first pass paid three clicks for one device's
        -- problem, and the click count is the whole subject of this file.
        for i = 1, 3 do
            if s.cbl[i].pressure >= opts.purgeAt then purges += 1; must('cbl_purge', i) end
        end
        if s.pressure >= AVB_AT then
            commands += 1
            local ok, err = e:Command('atmosphere_vent')
            if ok then vents += 1 elseif err ~= 'Atmosphere vent cooling down' then error(err) end
        end
        if not quotaAt and s.energy >= s.quota then quotaAt = tick end
        if s.energy >= s.quota and s.temperature < SHUTDOWN_COOL then
            commands += 1
            local ok = e:Command('shutdown')
            if ok then shutdownAt = tick; break else refusals += 1 end
        end
    end
    if shutdownAt then advance(Config.Shift.ShutdownSeconds + 2) end
    return {phase = e.state.phase, failure = e.state.failure, tick = tick, commands = commands,
        purges = purges, vents = vents, quotaAt = quotaAt, shutdownAt = shutdownAt, refusals = refusals,
        maxTemp = maxTemp, minTemp = minTemp, minPressure = minPressure,
        energy = e.state.energy, quota = e.state.quota}
end

-- Two clocks: `tick` counts from the first command of the boot chain, and the
-- Running clock is the part the click rate is about, since the boot chain is a
-- fixed four clicks that cost nothing to spread out.
local BOOT = Config.Shift.BootSeconds + Config.Shift.StartupSeconds + 5
local function run(seed, opts, trace)
    local r = plan(seed, opts, trace)
    r.pumps, r.fansOn = opts.pumps, opts.fansOn
    r.cbl = opts.cbl or 2
    r.purgeAt = opts.purgeAt
    r.seconds = r.tick - BOOT
    r.perClick = r.seconds / math.max(r.commands, 1)
    return r
end

-- ========== THE SWEEP ==========
-- 0 pumps is the untouched boot default and the first row exists to name it: with
-- all six fans still running the chamber loses 360 PSI per tick against a state-1
-- line worth about 210 at 10000 F, so pressure falls through StallPressure 2200,
-- the stall cooling takes 750 F per tick back out, and the shift dies of
-- `Reactor stallout` -- with the pumps off it dies of P.E.A overload instead,
-- which is what Phase 127 measured live at 143 s.
print('pumps fans purge | end        failure                          ticks  clicks  purge  vent  peak')
local rows = {}
for _, pumps in ipairs({0, 1, 2}) do
    for _, purgeAt in ipairs({60, 70, 74}) do
        for fansOn = 0, 6 do
            local r = run(20261014, {pumps = pumps, fansOn = fansOn, purgeAt = purgeAt})
            rows[#rows + 1] = r
            print(string.format('  %d    %d    %2d  | %-9s  %-30s %5d  %5d  %5d  %5d  %5d',
                pumps, fansOn, purgeAt, r.phase, tostring(r.failure or ''), r.tick, r.commands,
                r.purges, r.vents, math.floor(r.maxTemp or 0)))
        end
    end
end

-- The assertion is not "some policy wins" -- that would pass on a policy needing a
-- click per tick. It is that a policy reaching Report exists inside a click budget
-- a person can actually pay.
local winners, best = {}, nil
for _, r in ipairs(rows) do
    if r.phase == 'Report' then
        winners[#winners + 1] = r
        if not best or r.commands < best.commands then best = r end
    end
end
print('')
for _, r in ipairs(winners) do
    print(string.format('REACHED REPORT  pumps=%d fans=%d cbl=%d purgeAt=%d  %d clicks over %d s (one per %.1f s), %d purges, %d vents',
        r.pumps, r.fansOn, r.cbl, r.purgeAt, r.commands, r.seconds, r.perClick, r.purges, r.vents))
end
check('at least one set-and-forget policy reaches Report', #winners > 0, true)
if best then
    print(string.format('cheapest: %d clicks, %d s, temp ran %d..%d, pressure floor %d (limit 2200), energy %d/%d',
        best.commands, best.seconds, math.floor(best.minTemp), math.floor(best.maxTemp),
        math.floor(best.minPressure), math.floor(best.energy), best.quota))
    check('the cheapest winner is inside a human click rate (one per 5 s)', best.perClick >= 5, true)
    local trace = {}
    local again = run(20261014, {pumps = best.pumps, fansOn = best.fansOn, purgeAt = best.purgeAt}, trace)
    check('the replayed winner reproduces', again.commands, best.commands)
    check('the replayed winner reaches Report', again.phase, 'Report')
    print('')
    print('TRACE of the cheapest winner (every 20th tick):')
    for i = 1, #trace, 20 do print('  ' .. trace[i]) end
    print('  ' .. trace[#trace])
end

-- ========== IS THE WINNER A LUCKY WALK? ==========
-- The engine adds noise of -50..+49 F every tick, so ONE seed winning says the
-- policy is not hopeless and says nothing about margin. The live run will get a
-- noise stream nobody has seen. Everything above is swept against a single
-- generator so that the POLICIES are compared and not the noise; this last block
-- is where the noise is finally varied, and it is the block whose numbers decide
-- whether a live attempt has anywhere to go wrong.
print('')
print('ROBUSTNESS of the cheapest winner across independent noise streams:')
local worstLowP, worstHighT, worstClicks = math.huge, 0, 0
-- The rate is per RUN and not per 349 s: `seconds` moves with the noise stream (it
-- is however long that stream needed to reach the quota), so dividing by the
-- winner's own length would be measuring the wrong shift.
local worstRate = 0
local wins = 0
for seed = 1, 12 do
    local r = run(seed * 7919, {pumps = best.pumps, fansOn = best.fansOn, purgeAt = best.purgeAt})
    if r.phase == 'Report' then wins += 1 end
    worstLowP = math.min(worstLowP, r.minPressure or 0)
    worstHighT = math.max(worstHighT, r.maxTemp or 0)
    worstClicks = math.max(worstClicks, r.commands)
    worstRate = math.max(worstRate, r.commands / math.max(r.seconds, 1))
    print(string.format('  seed %2d  %-8s %-30s clicks %2d  T %5d..%5d  Pmin %5d',
        seed, r.phase, tostring(r.failure or ''), r.commands,
        math.floor(r.minTemp or 0), math.floor(r.maxTemp or 0), math.floor(r.minPressure or 0)))
end
check('every noise stream reaches Report', wins, 12)
check('the dearest of those runs is still one click per 5 s', worstRate <= 0.2, true)
-- The two margins that matter live: how close the pressure ever came to the
-- 2200 stall floor, and how close the temperature ever came to the 17000 limit
-- the shutdown command refuses past.
--
-- The pressure floor is now >2400 rather than >2700. That is not a relaxation, it
-- is the corrected number: the pre-fix file measured the same policies against a
-- trajectory that entered Running 615 F hot (see the note on the set-and-forget
-- block), and 615 F is worth roughly 800 PSI of state-1 line. The live shift is
-- what puts the real floor at 2804, and this check has to sit under that.
check('pressure never came within 200 of the stall floor', worstLowP > 2400, true)
check('temperature never came within 2000 of the shutdown limit', worstHighT < 15000, true)
print(string.format('worst across 12 seeds: Pmin %d (floor 2200), Tmax %d (limit 17000), %d clicks',
    math.floor(worstLowP), math.floor(worstHighT), worstClicks))

print(failures == 0 and 'OK all checks passed' or string.format('%d FAILURES', failures))
process.exit(failures == 0 and 0 or 1)
