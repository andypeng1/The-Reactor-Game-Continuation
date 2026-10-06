--!nonstrict
-- MCP_FlowCollector -- a temporary measurement instrument. Nothing here is gameplay.
--
-- WHY A PRIVATE ENGINE. CLAUDE 0.2: requiring a backend module from the command bar
-- returns a fresh copy, so the only way to watch the real state machine is to run its
-- own code against its own instance. Engine's header documents Engine.new(config, random)
-- as the test seam for exactly this. This file builds a private engine, drives it with
-- the real Command action names, and never touches Runtime, the place, or any shipped
-- value. No geometry, no lamps, no ValueObjects: this measures the SIMULATION, and the
-- lamp matrix is already proven separately by ServerScriptService.MCP_LampProbe.
--
-- THE RULE THIS FILE EXISTS TO HONOUR, verbatim from the user:
--   "保存到文件时候一定是有变化才计入，没变化不要收集"
-- Every tick line is a DIFF against the previous tick, and a tick whose diff is empty
-- emits nothing at all. No sampling, no truncation, no rotating window. The only writes
-- into the engine that the engine did not produce itself are marked ASSIST and printed
-- with the value they replaced, so the file can never be read as if the physics had
-- produced them.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10): the Studio edit layer decodes escapes once, so a
-- two-character backslash-n would arrive as a real newline and break the string it sits
-- in. Newlines come from string.char(10), and no inner double quote is ever needed.
--
-- HOW IT LEAVES STUDIO. Studio cannot write files. _tools/receive.py stands up a
-- localhost sink and this script POSTs to it, so the bytes go straight to disk and never
-- pass through a model context. See that file's own docstring.

local HttpService = game:GetService("HttpService")
local Backend = game.ServerScriptService.ReactorBackend
local Config = require(Backend.Config)
local Engine = require(Backend.Engine)

local SINK = "http://127.0.0.1:8765/"
local LABEL = "flow/reactor_flow"
local NL = string.char(10)
local SEED = 20260926
-- Long enough for shift 3 to reach its quota on its own. That shift runs past
-- Events.EquinoxSeconds 720 and needs roughly 790 Running ticks even with the
-- closed-loop pilot, so a budget that merely spans shifts 1 and 2 would fire the
-- ASSIST fallback and mislabel a pilot failure as an engine property.
local RUN_BUDGET = 2000

-- Deterministic on purpose: a Lehmer generator, so two runs of this file are comparable
-- line for line. The engine takes its noise source as a parameter precisely so this is
-- possible. 48271 keeps the product under 2^53, where a larger multiplier would silently
-- lose low bits to double rounding and still look random.
local rngState = SEED
local function rng(lo, hi)
    rngState = (rngState * 48271) % 2147483647
    return lo + math.floor((rngState - 1) / 2147483646 * (hi - lo + 1))
end

-- ========== CANONICAL TEXT ==========

local function fmt(v)
    local t = type(v)
    if t == "number" then
        if v % 1 == 0 then return string.format("%d", v) end
        return string.format("%.4f", v)
    elseif t == "boolean" then
        if v then return "true" else return "false" end
    elseif t == "string" then
        return v
    end
    return tostring(v)
end

-- Flatten a state table into path=value strings. Keys are sorted rather than taken in
-- pairs() order, because pairs() order is not stable between runs and a diff against an
-- unstable key order would report phantom changes.
local function walk(v, path, out)
    if type(v) == "table" then
        local names = {}
        for k in pairs(v) do names[#names + 1] = k end
        table.sort(names, function(a, b) return tostring(a) < tostring(b) end)
        for _, k in ipairs(names) do
            local key
            if type(k) == "number" then
                key = path .. "[" .. k .. "]"
            else
                key = path .. "." .. k
            end
            walk(v[k], key, out)
        end
    else
        out[path] = fmt(v)
    end
end

local function snapshot(state)
    local out = {}
    walk(state, "s", out)
    return out
end

local KEYS = nil

local function ensureKeys(state)
    if KEYS then return end
    local map = snapshot(state)
    KEYS = {}
    for k in pairs(map) do KEYS[#KEYS + 1] = k end
    table.sort(KEYS)
end

local function pairLine(t)
    local names = {}
    for k in pairs(t) do names[#names + 1] = k end
    table.sort(names)
    if #names == 0 then return "-" end
    local out = {}
    for _, k in ipairs(names) do out[#out + 1] = k .. "=" .. fmt(t[k]) end
    return table.concat(out, " ")
end

-- ========== THE SINK ==========

local buf = {}
local bufBytes = 0
local segNo, posted, postFailed = 0, 0, 0
local SEG_MAX = 700000
local flush

local lines = 0

local function emit(s)
    buf[#buf + 1] = s
    bufBytes += #s + 1
    lines += 1
    -- HttpService:PostAsync refuses a body over 1024 KB, and it refuses it as a
    -- FAILED POST rather than a truncation -- so an oversized run leaves the
    -- last good segment on disk and loses everything after it silently. The
    -- first version of this file did exactly that at 10467 KB. Streaming the
    -- file out in segments keeps every byte under the cap.
    if bufBytes >= SEG_MAX then flush() end
end

local function configDigest()
    local flat = {}
    local function w(v, path)
        if type(v) == "table" then
            local names = {}
            for k in pairs(v) do names[#names + 1] = k end
            table.sort(names, function(a, b) return tostring(a) < tostring(b) end)
            for _, k in ipairs(names) do w(v[k], path .. "." .. tostring(k)) end
        else
            flat[#flat + 1] = path .. "=" .. fmt(v)
        end
    end
    w(Config, "Config")
    return table.concat(flat, " ")
end

local function header()
    local t = {}
    t[#t + 1] = "# FlowCollector -- the whole control-room shutdown-to-startup chain, three shifts."
    t[#t + 1] = "# Every tick line is a CHANGE. A tick whose diff is empty emits nothing. ASSIST marks a"
    t[#t + 1] = "# value this instrument wrote into its own private engine; no other line is anything but"
    t[#t + 1] = "# the engine's own arithmetic. GATE/SET/DELT is the command table taken exhaustively."
    t[#t + 1] = "# Ticks were stepped at full speed, one tick = one Engine:Step(Config.Sim.Step) = 1s."
    t[#t + 1] = "# rng: Lehmer, seed " .. SEED .. ". Keys tracked: " .. tostring(KEYS and #KEYS or 0) .. "."
    t[#t + 1] = "# config: " .. configDigest()
    t[#t + 1] = "#"
    return table.concat(t, NL) .. NL
end

-- One segment per call. Segment 1 truncates the target and carries the header;
-- every later segment appends, so the header is written exactly once and the
-- file never grows a second copy of itself. flush() is NOT idempotent any more:
-- it consumes the buffer, which is what lets a run of any length fit.
flush = function(final)
    if #buf == 0 and not final then return end
    segNo += 1
    local text
    if segNo == 1 then
        text = header() .. table.concat(buf, NL)
    else
        text = table.concat(buf, NL)
    end
    if #buf > 0 or final then text = text .. NL end
    local url = SINK .. LABEL
    if segNo > 1 then url = url .. "?mode=a" end
    local sent = bufBytes
    local ok, err = pcall(function()
        HttpService:PostAsync(url, text)
    end)
    if ok then
        posted += 1
        buf = {}
        bufBytes = 0
    else
        postFailed += 1
        -- A rejected POST writes nothing, so the buffer is kept AND the segment
        -- index is given back: the retry re-sends the same segment under the same
        -- mode instead of appending a duplicate of it.
        segNo -= 1
        if postFailed <= 3 then
            warn("FlowCollector POST failed after " .. tostring(sent) .. " bytes: " .. tostring(err))
        end
    end
end

-- ========== THE FLOW ENGINE ==========

local e = nil
local last = nil
local tickNo = 0
local seenEvent = 0

local function drainEvents()
    for _, ev in ipairs(e.events) do
        if ev.id > seenEvent then
            seenEvent = ev.id
            emit(string.format("EVT  %-5d %-7s %s", ev.id, ev.kind, ev.message))
        end
    end
end

-- One tick's worth of output, or nothing at all. A phase change is the one event that
-- earns a full snapshot, because a diff is unreadable without an anchor to hang it on,
-- and the phase boundary is exactly where an anchor is worth its bytes.
local function tickLine()
    local cur = snapshot(e.state)
    local changed = {}
    for _, k in ipairs(KEYS) do
        if last[k] ~= cur[k] then
            changed[#changed + 1] = k .. "=" .. tostring(cur[k])
        end
    end
    if cur["s.phase"] ~= last["s.phase"] then
        emit(string.format("T%-6d PHASE %s", tickNo, tostring(cur["s.phase"])))
        local all = {}
        for _, k in ipairs(KEYS) do all[#all + 1] = k .. "=" .. tostring(cur[k]) end
        emit("SNAP " .. table.concat(all, " "))
    elseif #changed > 0 then
        emit(string.format("T%-6d %s", tickNo, table.concat(changed, " ")))
    end
    last = cur
end

local function adv(n)
    for _ = 1, (n or 1) do
        e:Step(Config.Sim.Step)
        tickNo += 1
        tickLine()
        if e.state.phase == "Failed" then return false end
    end
    return true
end

local function act(action, index, value)
    local ok, msg = e:Command(action, index, value)
    local tail
    if ok then
        tail = "OK"
    else
        tail = "DENY " .. tostring(msg)
    end
    emit(string.format("CMD  %-16s %-4s %-5s %s", action,
        index and tostring(index) or "-", value and tostring(value) or "-", tail))
    drainEvents()
    return ok
end

-- Engine:Repair is NOT reachable through Engine:Command. Command's own `limits`
-- table advertises repair_pump and repair_cbl, so the index is validated -- and
-- then the call falls through to `Unknown control`, because Command has no
-- branch for either name. Repair is the only door, and this is measured rather
-- than read: runGates() records the fall-through for both names.
--
-- It matters because pump integrity is a FINITE per-shift resource. Wear is
-- Device.PumpWearPerLevel * level per second, doubled in equinox, so 100
-- integrity buys ~830s of level-2 cooling and then the pump switches ITSELF off
-- -- and pump_on refuses at integrity 0. Cooling that disappears mid-shift turns
-- H=15 into +390 C/s, which is an instant meltdown. A shift long enough to reach
-- the equinox does not survive without an operator spending attention here.
local function repair(kind, index)
    local r = e:Repair(kind, index, 1)
    emit(string.format("CMD  %-16s %-4s %-5s %s", "repair_" .. kind,
        tostring(index), "1", r and "OK" or "DENY rejected"))
    drainEvents()
    return r
end

-- ========== THE AUTOPILOT ==========
--
-- dTemp/dt is exactly (Config.Sim.CBLHeat * H - Config.Sim.PumpCooling * K + noise) * dt / 2.5
-- = 26*H - 48*K C/s, where H is the SUM of the three CBL levels (3..15) and K the SUM of
-- the three pump levels (0..9). That is a linear plant in two integers, so this is a
-- CLOSED-LOOP controller and not a ladder: choose the pair whose slope is nearest the slope
-- we want, preferring the hotter pair on a tie because heat is output.
--
-- A static ladder of temperature bands was tried first and it died, which is why the loop
-- is worth the explanation. Under a constant +49 noise bias the band that holds at noise 0
-- (H=11,K=6, a nominal -2 C/s) becomes +17.6 C/s, the core drifts 24000 -> 29000 over 400
-- ticks, and above HighPressure 11300 the engine's own over-pressure heat term
-- (`temp += 298*scale`, flat, per tick) feeds back and runs away to meltdown. Closing the loop on the measured temperature
-- absorbs any bias; a table of bands cannot.
--
-- The shift has two halves and they are NOT mirror images, which is the complexity worth
-- collecting: once the quota is met the reactor must be brought BELOW Shift.ShutdownLimit
-- 17000 before `shutdown` will accept, so the endgame is a deliberate cool-down. The rate
-- is CLAMPED at -45 C/s, and that clamp is the non-obvious part: the fastest pair available
-- is -354 C/s (H=3, K=9), which sails past 17000 and stalls the core at StallTemperature
-- 2000 long before shutdown can be called. Cooling is cheap in both halves -- it is the HEAT
-- that keeps the descent survivable.
--
-- The equinox is the third regime and it is a trap with one exit. Engine:Step guards its
-- whole `pressure += (floor(temp/50) - fans*70)*scale` line with `if not equinox`, AND
-- atmosphere_vent refuses during the equinox -- so the only surviving pressure term is
-- `temp > State2 -> +200*scale`, a pure +80 C/s-of-pressure ratchet with no sink, which then
-- drives the high-pressure heat term and compounds into meltdown. That ratchet is gated on
-- the temperature as well, so below State2 17500 the pressure during the equinox is EXACTLY
-- frozen -- and below 17000 shutdown is already legal. The equinox is therefore not a hotter
-- shift, it is a colder one. The design is telling the operator to get under 17500 and leave.
-- E-VENT is the only pressure instrument that still works, and it is spent when the AVB
-- cannot keep up.

local function clamp(v, lo, hi)
    if v < lo then return lo end
    if v > hi then return hi end
    return v
end

-- Slope table, computed once. Index is the pair index 1..117 (H in 3..15, K in 0..9).
local SLOPE = {}
do
    local n = 0
    for h = 3, 15 do
        for k = 0, 9 do
            n += 1
            SLOPE[n] = { h = h, k = k, rate = 26 * h - 48 * k }
        end
    end
end

-- Split an integer total across three devices, balanced and clamped.
-- Balanced on purpose: equal levels keep the three device pressures equal, so the purges
-- stay together and a purge never chases one outlying device.
local function split(total, lo, hi)
    local base = math.floor(total / 3)
    local extra = total - base * 3
    local out = {}
    for i = 1, 3 do
        local v = base
        if i <= extra then v += 1 end
        if v < lo then v = lo end
        if v > hi then v = hi end
        out[i] = v
    end
    return out
end

local function policy()
    local s = e.state
    local t = s.temperature
    local endgame = s.energy >= s.quota
    local target
    if s.equinox then
        target = 15500
    elseif endgame then
        target = 16000
    else
        target = 20000
    end
    -- The gain is 0.03, not 0.4, and that is a MEASURED choice -- see the sweep in
    -- _tools/_flow_sim.py (run: `python _flow_sim.py --ab`).
    --
    -- The demand is a rate, and the clamp below is a rate limit, so the ratio is a
    -- POSITION dead zone: clamp(err*gain, +/-200)/gain means the core can drift
    -- +/-200/gain C before this asks for a reversal. At gain 0.4 that is +/-500 C and
    -- the pilot then corrects at full slope, so it sawtooths the zone. Lowering the
    -- gain narrows the zone and lets the 2 C/tick quantisation do the work: on 54
    -- cases (18 seeds x 3 shifts) gain 0.4 -> 0.1 -> 0.03 moves cbl/tick
    -- 1.382 -> 0.478 -> 0.349 while mean |dTemp| per tick falls 19.96 -> 18.68 ->
    -- 17.76. Quieter AND steadier, which is the pair that has to move together: the
    -- first attempt at this cut commands 2.8x on the real engine and made the core
    -- 4.7x less steady (63.63 vs 15.43 |dTemp|), because the band it added demanded
    -- exactly the size of the big pairs at the band edge and rode them.
    --
    -- Below this the margin goes: the cliff is between 0.015 and 0.012, where the
    -- constant +49-noise cases start timing out and gain 0.01 melts the core at tick
    -- 1235. 0.03 keeps a 2x margin over that cliff. There is deliberately no
    -- hysteresis band: swept against no band at equal gain, the band was worse on
    -- BOTH axes, because a 2 C/tick regulator fighting the engine's own +/-20 C/tick
    -- of noise has to re-decide in order to correct -- the commands ARE the control,
    -- and a deadband only removes correction.
    --
    -- Measured on the real engine at this gain: CBL 2093 -> 737, pump_level
    -- 1330 -> 342, extraction 249 -> 35, INFO/WARN events unchanged at 12/4, and
    -- |dTemp| 15.43 -> 13.62. See Data/flow/ for the three runs.
    local want = clamp((target - t) * 0.03, endgame and -45 or -200, 200)
    local H, K = 3, 9
    local bestScore, bestH
    for i = 1, #SLOPE do
        local c = SLOPE[i]
        local score = math.abs(c.rate - want)
        if bestScore == nil or score < bestScore or (score == bestScore and c.h > bestH) then
            bestScore, bestH, H, K = score, c.h, c.h, c.k
        end
    end
    -- Stress accrues as (extraction*4 + floor(output/500) - floor(cooling*1.5) - 6)
    -- per second, so high extraction is only safe on top of high cooling.
    local ex = 2
    if K >= 8 then ex = 3 end
    local cblTarget = split(H, 1, 5)
    local pumpTarget = split(K, 0, 3)
    for i = 1, 3 do
        local d = s.cbl[i]
        if not d.fault then
            if d.level ~= cblTarget[i] then act("cbl", i, cblTarget[i]) end
            if d.pressure >= 60 then act("cbl_purge", i) end
        end
        local p = s.pumps[i]
        local pw = pumpTarget[i]
        if pw == 0 then
            if p.enabled then act("pump_off", i) end
        elseif p.integrity > 0 then
            if not p.enabled then act("pump_on", i) end
            if p.level ~= pw then act("pump_level", i, pw) end
            -- Repair before the pump can reach zero, not after: at integrity 0 the
            -- engine flips `enabled` off itself and pump_on then refuses, so a pump
            -- left to die is dead for the rest of the shift.
            if p.integrity < 60 then repair("pump", i) end
        end
    end
    local fanTarget = nil
    if s.pressure > 11000 then
        fanTarget = true
    elseif s.pressure < 8000 then
        fanTarget = false
    end
    if fanTarget ~= nil then
        for i = 1, 6 do
            if s.fans[i] ~= fanTarget then act("fan", i) end
        end
    end
    if s.pressure > 12000 then act("atmosphere_vent") end
    -- Above HighPressure 11300 the engine adds a flat 298*scale of HEAT back into the
    -- core every tick, so an E-VENT here is not merely relief, it is the only way to break
    -- a runaway the AVB cannot break alone -- and during the equinox it is the only
    -- instrument left at all. The 12000/13000 gates below are this collector's own policy
    -- and not the engine's constant; both now sit past the engine's threshold, which is
    -- exactly the relationship the old 12000/13000 pair assumed of 13500.
    if s.pressure > 13000 then
        for i = 1, 3 do
            if not s.emergencyUsed[i] then
                act("emergency_vent", i)
                break
            end
        end
    end
    if s.extraction ~= ex then act("extraction", nil, ex) end
end

-- ========== SECTION 2: THE FLOW ==========

-- Walk a phase forward with a step budget, reporting how many ticks it took.
local function settle(phase, budget)
    local guard = 0
    while e.state.phase == phase and guard < budget do
        adv()
        guard += 1
    end
    return guard
end

-- The pre-flight, from whatever state the engine is in. `reset` and `next` BOTH
-- wipe monitorPower, booted, lights, shuttersOpen and mute, so this cannot be
-- hoisted out of the shift loop and reused -- the whole chain below is re-walked
-- every shift, and again after every reset.
local function preflight()
    act("monitor_power")
    act("shutters")
    act("lights")
    act("lights")
    act("mute")
    act("mute")
    act("boot")
    local g = settle("Booting", 30)
    emit(string.format("PHASE %s at tick %d after %d ticks (BootSeconds %d)",
        e.state.phase, tickNo, g, Config.Shift.BootSeconds))
    act("start")
    g = settle("Starting", 30)
    emit(string.format("PHASE %s at tick %d after %d ticks (StartupSeconds %d) temp %s pressure %s",
        e.state.phase, tickNo, g, Config.Shift.StartupSeconds,
        fmt(e.state.temperature), fmt(e.state.pressure)))
end

local function runShift(shift, quota)
    emit(string.format("SHIFT %d quota %d at tick %d", shift, quota, tickNo))
    preflight()
    act("hdef")
    act("extraction", nil, 2)
    local steps, assisted = 0, false
    while e.state.phase == "Running" do
        policy()
        if not adv() then break end
        steps += 1
        -- Leave as soon as the engine will ACCEPT a shutdown, instead of running out the
        -- budget. Without this the loop has no exit at all on a pilot that survives: the
        -- first working version of this collector ran every shift to the hard stop, which
        -- is where the 18048 ticks and the 10 MB POST came from. `shutdown` itself is
        -- still the thing that ends the shift -- this only stops asking for more of them.
        if e.state.energy >= e.state.quota
            and e.state.temperature < Config.Shift.ShutdownLimit then
            break
        end
        if steps >= RUN_BUDGET and not assisted then
            assisted = true
            emit(string.format("ASSIST energy %s -> %s at tick %d (the policy could not reach the quota)",
                fmt(e.state.energy), fmt(e.state.quota), tickNo))
            e.state.energy = e.state.quota
        end
        if steps >= RUN_BUDGET * 3 then
            emit(string.format("BUDGET exhausted at tick %d phase %s", tickNo, e.state.phase))
            break
        end
    end
    if e.state.phase == "Running" then
        act("shutdown")
        local g = settle("Stopping", 30)
        emit(string.format("PHASE %s at tick %d after %d ticks (ShutdownSeconds %d)",
            e.state.phase, tickNo, g, Config.Shift.ShutdownSeconds))
    end
    emit(string.format("SHIFT %d END phase %s failure %s runningTicks %d assisted %s",
        shift, e.state.phase, tostring(e.state.failure), steps, tostring(assisted)))
    return steps
end

local function runFlow()
    e = Engine.new(Config, rng)
    last = snapshot(e.state)
    ensureKeys(e.state)
    tickNo = 0
    seenEvent = 0
    emit("## SECTION 2 -- the flow. shift 1 boots from Cold and each later shift is reached")
    emit("## through Report > next; a Failed shift is retried through Failed > reset, which")
    emit("## restarts the SAME shift number. Both commands wipe monitorPower and booted, so")
    emit("## the whole chain below is re-walked every time rather than reused.")
    local t0 = {}
    for _, k in ipairs(KEYS) do t0[#t0 + 1] = k .. "=" .. tostring(last[k]) end
    emit("SNAP " .. table.concat(t0, " "))
    drainEvents()
    flush()

    local shifts = #Config.Shift.Quotas
    for shift = 1, shifts do
        local quota = Config.Shift.Quotas[shift]
        runShift(shift, quota)
        -- Recover a Failed shift instead of marching on. `next` is gated on
        -- phase == Report, so a Failed engine leaves every later shift recording
        -- runningTicks 0 -- which is exactly what the first run of this collector
        -- did for shifts 2 and 3, and the `## RECEIPT ticks` line proved it.
        local retries = 0
        while e.state.phase == "Failed" and retries < 2 do
            retries += 1
            emit(string.format("RECOVER shift %d attempt %d after failure %s at tick %d",
                shift, retries, tostring(e.state.failure), tickNo))
            act("reset")
            if e.state.phase == "Failed" then break end
            runShift(shift, quota)
        end
        if e.state.phase == "Report" and shift < shifts then
            act("next")
        end
        drainEvents()
        flush()
    end
end

-- ========== SECTION 1: THE COMMAND TABLE ==========
--
-- Exhaustive rather than sampled: every branch of Engine:Command gets a case, and each
-- case records the delta the command caused, not a description of it. The setup returns
-- the fields it wrote by hand, so SET is an exact precondition and never an inference.

local function idle(s) return {} end

local function powered(s)
    s.monitorPower = true
    return { monitorPower = true }
end

local function armed(s)
    s.monitorPower = true
    s.shuttersOpen = true
    return { monitorPower = true, shuttersOpen = true }
end

local function ready(s)
    s.monitorPower = true
    s.shuttersOpen = true
    s.booted = true
    s.phase = "Ready"
    return { monitorPower = true, shuttersOpen = true, booted = true, phase = "Ready" }
end

local function running(s)
    local set = ready(s)
    s.phase = "Running"
    s.temperature = Config.Sim.StartupTemperature
    s.pressure = Config.Sim.StartupPressure
    for _, d in ipairs(s.cbl) do d.active = true end
    set.phase = "Running"
    set.temperature = s.temperature
    set.pressure = s.pressure
    set["cbl[1..3].active"] = true
    return set
end

local function phaseOf(name)
    return function(s)
        local set = armed(s)
        s.phase = name
        set.phase = name
        return set
    end
end

local function runningAt(phase, extra)
    return function(s)
        local set = running(s)
        s.phase = phase
        set.phase = phase
        if extra then
            for k, v in pairs(extra) do set[k] = v end
        end
        return set
    end
end

local GATES = {
    { name = "boot, monitor power off", setup = idle, action = "boot" },
    { name = "boot, shutters closed", setup = powered, action = "boot" },
    { name = "boot accepted", setup = armed, action = "boot" },
    { name = "boot while Booting", setup = phaseOf("Booting"), action = "boot" },
    { name = "boot while Running", setup = running, action = "boot" },
    { name = "monitor_power off from Cold", setup = powered, action = "monitor_power" },
    { name = "monitor_power off while Booting", setup = phaseOf("Booting"), action = "monitor_power" },
    { name = "monitor_power off while Ready", setup = ready, action = "monitor_power" },
    { name = "monitor_power off while Running", setup = running, action = "monitor_power" },
    { name = "start, nothing booted", setup = idle, action = "start" },
    { name = "start at Ready", setup = ready, action = "start" },
    { name = "shutters toggle from Cold", setup = idle, action = "shutters" },
    { name = "lights toggle from Cold", setup = idle, action = "lights" },
    { name = "mute toggle from Cold", setup = idle, action = "mute" },
    { name = "shutdown while Cold", setup = idle, action = "shutdown" },
    { name = "shutdown while Starting", setup = phaseOf("Starting"), action = "shutdown" },
    { name = "shutdown, quota unmet", setup = running, action = "shutdown" },
    { name = "shutdown, core exactly at the limit", setup = function(s)
        local set = running(s)
        s.energy = s.quota
        s.temperature = Config.Shift.ShutdownLimit
        set.energy = s.energy
        set.temperature = s.temperature
        return set
    end, action = "shutdown" },
    { name = "shutdown, core one degree under", setup = function(s)
        local set = running(s)
        s.energy = s.quota
        s.temperature = Config.Shift.ShutdownLimit - 1
        set.energy = s.energy
        set.temperature = s.temperature
        return set
    end, action = "shutdown" },
    { name = "shutdown accepted", setup = function(s)
        local set = running(s)
        s.energy = s.quota
        s.temperature = 12000
        s.sam = true
        set.energy = s.energy
        set.temperature = s.temperature
        set.sam = true
        return set
    end, action = "shutdown" },
    { name = "next while Running", setup = running, action = "next" },
    { name = "next at Report, shift 1 of 3", setup = runningAt("Report"), action = "next" },
    { name = "next at Report, shift 3 of 3", shift = 3, setup = runningAt("Report"), action = "next" },
    { name = "reset at Report", shift = 2, setup = runningAt("Report"), action = "reset" },
    { name = "reset while Failed", setup = function(s)
        local set = running(s)
        s.phase = "Failed"
        s.failure = "probe"
        set.phase = "Failed"
        set.failure = "probe"
        return set
    end, action = "reset" },
    { name = "reset while Running", setup = running, action = "reset" },
    { name = "fan while Report", setup = runningAt("Report"), action = "fan", index = 1 },
    { name = "fan while Failed", setup = runningAt("Failed"), action = "fan", index = 1 },
    { name = "fan index 0", setup = running, action = "fan", index = 0 },
    { name = "fan index 7", setup = running, action = "fan", index = 7 },
    { name = "fan index 1.5", setup = running, action = "fan", index = 1.5 },
    { name = "cbl level 0", setup = running, action = "cbl", index = 1, value = 0 },
    { name = "cbl level 6", setup = running, action = "cbl", index = 1, value = 6 },
    { name = "cbl level 5", setup = running, action = "cbl", index = 1, value = 5 },
    { name = "cbl on a faulted device", setup = function(s)
        local set = running(s)
        s.cbl[1].fault = true
        set["cbl[1].fault"] = true
        return set
    end, action = "cbl", index = 1, value = 3 },
    { name = "pump_level 4", setup = running, action = "pump_level", index = 1, value = 4 },
    { name = "pump_level 2", setup = running, action = "pump_level", index = 1, value = 2 },
    { name = "pump_on, intact", setup = running, action = "pump_on", index = 1 },
    { name = "pump_on, depleted", setup = function(s)
        local set = running(s)
        s.pumps[1].integrity = 0
        set["pumps[1].integrity"] = 0
        return set
    end, action = "pump_on", index = 1 },
    { name = "pump_off", setup = function(s)
        local set = running(s)
        s.pumps[1].enabled = true
        set["pumps[1].enabled"] = true
        return set
    end, action = "pump_off", index = 1 },
    { name = "extraction 5", setup = running, action = "extraction", value = 5 },
    { name = "extraction 4", setup = running, action = "extraction", value = 4 },
    { name = "cbl_purge", setup = function(s)
        local set = running(s)
        s.cbl[1].pressure = 50
        s.cbl[1].stress = 30
        set["cbl[1].pressure"] = 50
        set["cbl[1].stress"] = 30
        return set
    end, action = "cbl_purge", index = 1 },
    { name = "cbl_purge in cooldown", setup = function(s)
        local set = running(s)
        s.cbl[1].purgeUntil = s.time + 10
        set["cbl[1].purgeUntil"] = "time+10"
        return set
    end, action = "cbl_purge", index = 1 },
    { name = "hdef on", setup = running, action = "hdef" },
    { name = "hdef on a faulted generator", setup = function(s)
        local set = running(s)
        s.hdef.fault = true
        set["hdef.fault"] = true
        return set
    end, action = "hdef" },
    { name = "mass_toggle 1", setup = running, action = "mass_toggle", index = 1 },
    { name = "mass_level 1", setup = running, action = "mass_level", index = 1 },
    { name = "sam while Cold", setup = idle, action = "sam" },
    { name = "sam while Running", setup = running, action = "sam" },
    { name = "sam, radiation at the limit", setup = function(s)
        local set = running(s)
        s.radiation = Config.Device.SAMRadiationLimit
        set.radiation = s.radiation
        return set
    end, action = "sam" },
    { name = "atmosphere_vent while Cold", setup = idle, action = "atmosphere_vent" },
    { name = "atmosphere_vent while Running", setup = running, action = "atmosphere_vent" },
    { name = "atmosphere_vent during Equinox", setup = function(s)
        local set = running(s)
        s.equinox = true
        set.equinox = true
        return set
    end, action = "atmosphere_vent" },
    { name = "atmosphere_vent in cooldown", setup = function(s)
        local set = running(s)
        s.ventUntil = s.time + 10
        set.ventUntil = "time+10"
        return set
    end, action = "atmosphere_vent" },
    { name = "emergency_vent", setup = running, action = "emergency_vent", index = 1 },
    { name = "emergency_vent, already spent", setup = function(s)
        local set = running(s)
        s.emergencyUsed[1] = true
        set["emergencyUsed[1]"] = true
        return set
    end, action = "emergency_vent", index = 1 },
    { name = "emergency_vent index 4", setup = running, action = "emergency_vent", index = 4 },
    { name = "grav_charge in shift 1", setup = running, action = "grav_charge" },
    { name = "grav_charge in shift 3", shift = 3, setup = running, action = "grav_charge" },
    { name = "grav_charge while Charging", shift = 3, setup = function(s)
        local set = running(s)
        s.grav.phase = "Charging"
        set["grav.phase"] = "Charging"
        return set
    end, action = "grav_charge" },
    { name = "grav_fire while Idle", shift = 3, setup = running, action = "grav_fire" },
    { name = "grav_fire inside the window", shift = 3, setup = function(s)
        local set = running(s)
        s.grav.phase = "Armed"
        s.grav.charge = 7
        set["grav.phase"] = "Armed"
        set["grav.charge"] = 7
        return set
    end, action = "grav_fire" },
    { name = "repair_pump through Command", setup = running, action = "repair_pump", index = 1 },
    { name = "unknown action", setup = running, action = "widget" },
}

-- Repairs are NOT in the Command vocabulary even though its limits table carries
-- repair_pump and repair_cbl: an index is validated and then the action falls through to
-- the unknown-control branch. Recording that as a measurement rather than a remark.
local REPAIRS = {
    { name = "repair pump", kind = "pump", index = 1, seconds = 1, setup = function(s)
        local set = running(s)
        s.pumps[1].integrity = 40
        set["pumps[1].integrity"] = 40
        return set
    end },
    { name = "repair pump, seconds 0", kind = "pump", index = 1, seconds = 0, setup = function(s)
        local set = running(s)
        s.pumps[1].integrity = 40
        set["pumps[1].integrity"] = 40
        return set
    end },
    { name = "repair pump, seconds 2", kind = "pump", index = 1, seconds = 2, setup = function(s)
        local set = running(s)
        s.pumps[1].integrity = 40
        set["pumps[1].integrity"] = 40
        return set
    end },
    { name = "repair pump, index 4", kind = "pump", index = 4, seconds = 1, setup = running },
    { name = "repair cbl clears the fault", kind = "cbl", index = 1, seconds = 1, setup = function(s)
        local set = running(s)
        s.cbl[1].stress = 10
        s.cbl[1].fault = true
        s.cbl[1].active = false
        set["cbl[1].stress"] = 10
        set["cbl[1].fault"] = true
        set["cbl[1].active"] = false
        return set
    end },
    { name = "repair grav", kind = "grav", seconds = 1, setup = function(s)
        local set = running(s)
        s.grav.damage = 30
        set["grav.damage"] = 30
        return set
    end },
    { name = "repair hdef clears the fault", kind = "hdef", seconds = 1, setup = function(s)
        local set = running(s)
        s.hdef.heat = 5
        s.hdef.fault = true
        set["hdef.heat"] = 5
        set["hdef.fault"] = true
        return set
    end },
    { name = "repair unknown kind", kind = "widget", seconds = 1, setup = running },
}

local function renderCase(tag, seq, name, set, ok, msg, before, after)
    emit(string.format("%s %-3d %-40s %s", tag, seq, name,
        ok and "OK" or ("DENY " .. tostring(msg or "rejected"))))
    emit("SET  " .. pairLine(set))
    local delta = {}
    for _, k in ipairs(KEYS) do
        if before[k] ~= after[k] then
            delta[#delta + 1] = k .. ":" .. tostring(before[k]) .. ">" .. tostring(after[k])
        end
    end
    if #delta == 0 then
        emit("DELT -")
    else
        emit("DELT " .. table.concat(delta, " "))
    end
end

local function runGates()
    emit("## SECTION 1 -- every branch of Engine:Command, and every Repair kind, taken")
    emit("## exhaustively. SET is the precondition written by hand; DELT is what the call")
    emit("## itself changed. A DENY with an empty DELT is a refusal that mutates nothing.")
    local seq = 0
    for _, case in ipairs(GATES) do
        seq += 1
        local eng = Engine.new(Config, rng)
        if case.shift and case.shift > 1 then eng:Reset(case.shift) end
        local s = eng.state
        local set = case.setup(s)
        local before = snapshot(s)
        local ok, msg = eng:Command(case.action, case.index, case.value)
        renderCase("GATE", seq, case.name, set, ok, msg, before, snapshot(s))
    end
    for _, case in ipairs(REPAIRS) do
        seq += 1
        local eng = Engine.new(Config, rng)
        local s = eng.state
        local set = case.setup(s)
        local before = snapshot(s)
        local ok = eng:Repair(case.kind, case.index, case.seconds)
        renderCase("REP ", seq, case.name, set, ok, nil, before, snapshot(s))
    end
end

-- ========== DRIVER ==========

local function main()
    -- The key list has to exist before the gate table renders, and it is built from a
    -- throwaway engine rather than from the flow engine so both sections share one list.
    local probe = Engine.new(Config, rng)
    ensureKeys(probe.state)
    runGates()
    flush()
    runFlow()
    -- `lines` is the running total, not #buf: flush() consumes the buffer now, so
    -- #buf would report only the tail segment and understate the file by ~100x.
    emit(string.format("## RECEIPT ticks %d lines %d segments %d posts %d postfail %d",
        tickNo, lines, segNo, posted, postFailed))
    flush(true)
    print(string.format("FlowCollector done: ticks %d lines %d segments %d posts %d postfail %d",
        tickNo, lines, segNo, posted, postFailed))
end

main()
