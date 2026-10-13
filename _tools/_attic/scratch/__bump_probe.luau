-- Reproduce quota_policy_sim's own ordering: the set-and-forget block is issued on
-- the first LOOP iteration, which is 4 Update calls after the chain ends.
local fs = require('@lune/fs'); local luau = require('@lune/luau')
local function stubColor() local c={}; function c.fromRGB(r,g,b) return {r=r,g=g,b=b} end; function c.new(r,g,b) return {r=r,g=g,b=b} end; return c end
local env = {Color3=stubColor(), Vector3={new=function(x,y,z) return {x=x,y=y,z=z} end},
    string=string, math=math, table=table, setmetatable=setmetatable, ipairs=ipairs, pairs=pairs,
    pcall=pcall, tostring=tostring, tonumber=tonumber, type=type, print=print, warn=print,
    error=error, assert=assert, select=select, next=next, rawget=rawget, rawset=rawset}
local Config = luau.load(fs.readFile('src/ReactorBackend/Config.luau'), {debugName='Config', environment=env})()
local Engine = luau.load(fs.readFile('src/ReactorBackend/Engine.luau'), {debugName='Engine', environment=env})()
local function makeRng(seed) local st=seed; return function(lo,hi) st=(st*48271)%2147483647; return lo+math.floor((st-1)/2147483646*(hi-lo+1)) end end

local e = Engine.new(Config, makeRng(20261014))
local tick = 0
local function advance(n) for _ = 1, n do tick += 1; e:Update(1) end end
e:Command('monitor_power'); e:Command('shutters'); e:Command('boot')
advance(Config.Shift.BootSeconds)
e:Command('start')
advance(Config.Shift.StartupSeconds + 5)

local nP = 0; for _, p in ipairs(e.state.pumps) do if p.enabled then nP += 1 end end
print(string.format('at loop start: tick=%d phase=%s T=%d P=%d pumpsOn=%d', tick, e.state.phase, math.floor(e.state.temperature), math.floor(e.state.pressure), nP))
-- the four calls the sim spends between the chain ending and its set block
for _ = 1, 4 do tick += 1; e:Update(1) end
print(string.format('four calls later (still no coolant): T=%d P=%d', math.floor(e.state.temperature), math.floor(e.state.pressure)))
print(string.format('=> %.1f F/s with 3 CBLs at level 2 and zero cooling (3*65*0.4 = %.1f)', (e.state.temperature-9420)/5, 3*65*0.4))

-- and where the chain actually ends
local f = Engine.new(Config, makeRng(20261014))
local c = 0
local function step(n) for _ = 1, n do c += 1; f:Update(1) end end
f:Command('monitor_power'); f:Command('shutters'); f:Command('boot'); step(Config.Shift.BootSeconds)
f:Command('start')
local startC = c
while f.state.phase ~= 'Running' and c < 400 do c += 1; f:Update(1) end
print(string.format('chain: %d calls after start (StartupSeconds=%s), T at Running=%d P=%d',
    c - startC, tostring(Config.Shift.StartupSeconds), math.floor(f.state.temperature), math.floor(f.state.pressure)))
print(string.format('BOOT in the sim = %d + %s + 5 = %s', Config.Shift.BootSeconds, tostring(Config.Shift.StartupSeconds), tostring(Config.Shift.BootSeconds + Config.Shift.StartupSeconds + 5)))
