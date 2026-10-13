-- What does the sim's tick counter actually count, and how long is the startup chain?
local fs = require('@lune/fs')
local luau = require('@lune/luau')
local function stubColor()
    local c = {}
    function c.fromRGB(r, g, b) return {r = r, g = g, b = b} end
    function c.new(r, g, b) return {r = r, g = g, b = b} end
    return c
end
local env = {
    Color3 = stubColor(), Vector3 = {new = function(x, y, z) return {x = x, y = y, z = z} end},
    string = string, math = math, table = table, setmetatable = setmetatable,
    ipairs = ipairs, pairs = pairs, pcall = pcall, tostring = tostring,
    tonumber = tonumber, type = type, print = print, warn = print, error = error,
    assert = assert, select = select, next = next, rawget = rawget, rawset = rawset,
}
local Config = luau.load(fs.readFile('src/ReactorBackend/Config.luau'), {debugName='Config', environment=env})()
local Engine = luau.load(fs.readFile('src/ReactorBackend/Engine.luau'), {debugName='Engine', environment=env})()

print(string.format('Sim.Step          = %s', tostring(Config.Sim.Step)))
print(string.format('MaxCatchupSteps   = %s', tostring(Config.Sim.MaxCatchupSteps)))
print(string.format('BootSeconds       = %s', tostring(Config.Shift.BootSeconds)))
print(string.format('StartupSeconds    = %s   <- DERIVED at config load', tostring(Config.Shift.StartupSeconds)))
print(string.format('ShutdownSeconds   = %s', tostring(Config.Shift.ShutdownSeconds)))
local sum = 0
for i, step in ipairs(Config.Shift.StartupSteps) do
    sum += step.hold
    print(string.format('  step %d hold=%-6s cumulative=%s', i, tostring(step.hold), tostring(sum)))
end
print(string.format('sum of holds      = %s', tostring(sum)))

local function makeRng(seed)
    local state = seed
    return function(lo, hi)
        state = (state * 48271) % 2147483647
        return lo + math.floor((state - 1) / 2147483646 * (hi - lo + 1))
    end
end

local e = Engine.new(Config, makeRng(20261014))
e:Command('monitor_power'); e:Command('shutters'); e:Command('boot')
local calls, steps, lastPhase = 0, 0, e.state.phase
print(string.format('%6s %10s %10s %-9s %8s', 'call', 'simTime_s', 'startupHold', 'phase', 'T/F'))
local function advance(n)
    for _ = 1, n do
        calls += 1
        local before = e.state.accumulator
        e:Update(1)
        if e.state.accumulator < before then steps += 1 end
        local s = e.state
        if s.phase ~= lastPhase then
            lastPhase = s.phase
            print(string.format('%6d %10.1f %10.1f %-9s %8d   <-- phase change',
                calls, calls - s.accumulator, s.startupHold, s.phase, math.floor(s.temperature)))
        end
    end
end
advance(Config.Shift.BootSeconds)
print(string.format('%6d %10.1f %10.1f %-9s %8d   <-- after boot advance',
    calls, calls - e.state.accumulator, e.state.startupHold, e.state.phase, math.floor(e.state.temperature)))
e:Command('start')
advance(Config.Shift.StartupSeconds + 5)
print(string.format('%6d %10.1f %10.1f %-9s %8d   <-- after startup advance',
    calls, calls - e.state.accumulator, e.state.startupHold, e.state.phase, math.floor(e.state.temperature)))
print(string.format('Update calls=%d  real Steps fired=%d  accumulator left over=%s',
    calls, steps, tostring(e.state.accumulator)))
print(string.format('real simulated seconds = steps * Step = %s', tostring(steps * Config.Sim.Step)))
