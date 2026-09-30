-- transport_probe_test.lua -- the probe, run against stubbed executors.
--
-- The probe's whole product is a table of "present / works" per transport, and it
-- runs in the one environment I cannot test from here.  So the thing worth
-- testing is not "does Solara have syn.request" -- it is "does the probe report
-- what it was given, and does it report a FAILURE as a failure".  A probe that
-- answers "works" for everything would send the next run down the wrong
-- transport, which is the bug it exists to find.
--
-- Four executors, each a different shape of the same question:
--   A  nothing at all          -> every candidate absent, no winner, no crash
--   B  request only            -> request works, it is the winner, 2 files out
--   C  request answers 500     -> present but NOT working, and no winner
--   D  HttpService only, raises-> present, not working, and the raise is NAMED
--
-- Run: /d/Lua/5.1/lua.exe _tools/transport_probe_test.lua

local NL = string.char(10)
local SOURCE = '_tools/transport_probe.luau'

local fh = assert(io.open(SOURCE, 'r'))
local src = fh:read('*a')
fh:close()

-- Printed as it goes, and the exit code carries the verdict -- the same shape as
-- watch_harness.luau, so the runner treats both the same way.  A harness that only
-- reports at the end hides which scenario was running when it died, and every
-- scenario here is a different executor.
local pass, fail = 0, 0
local function check(name, cond, why)
    if cond then
        pass = pass + 1
        print('  ok   ' .. name)
    else
        fail = fail + 1
        print('  FAIL ' .. name .. '  -- ' .. tostring(why))
    end
end

-- The probe prints its table; it is the only channel it has when nothing works,
-- so the test reads it rather than reaching into the probe's internals.
local function run_probe(setup)
    -- A fresh global environment per scenario.  Without this the previous
    -- scenario's stubs stay visible and every test would measure scenario A plus
    -- whatever ran before it -- which is exactly the "green for the wrong reason"
    -- this file is supposed to catch.
    local env = { print = function() end, tostring = tostring, type = type,
        ipairs = ipairs, pcall = pcall, os = os, string = string, table = table,
        math = math, select = select, error = error, tonumber = tonumber }
    env._G = env
    setup(env)
    local printed = {}
    env.print = function(s) printed[#printed + 1] = tostring(s) end
    local chunk = assert(loadstring(src, SOURCE))
    setfenv(chunk, env)
    local ok, err = pcall(chunk)
    return ok, err, table.concat(printed, NL), env
end

local function line_for(out, name)
    for line in string.gmatch(out, '[^' .. NL .. ']+') do
        if string.find(line, '%[probe%] ' .. name .. ' ', 1) then return line end
    end
    return nil
end

-- ---------------------------------------------------------------- A: nothing --
local okA, errA, outA = run_probe(function() end)
check('A the probe survives an executor with no transports', okA, errA)
check('A every candidate is reported absent',
    line_for(outA, 'syn') and string.find(line_for(outA, 'syn'), 'present=false', 1, true) ~= nil,
    line_for(outA, 'syn'))
check('A it says so in words when nothing worked',
    string.find(outA, 'NO transport worked', 1, true) ~= nil, outA)

-- ------------------------------------------------------------ B: request only --
-- The stub is deliberately strict about the CALLING SHAPE.  The first version of
-- this probe handed every candidate (url, body) positionally; a real syn.request
-- takes a request table and would have rejected that, but a permissive stub
-- accepted the string and the probe reported a working transport as broken.  So
-- the shape is recorded and asserted here -- a stub that takes anything is how
-- that bug stayed invisible.
local sentB, shapesB, methodsB = {}, {}, {}
local okB, errB, outB = run_probe(function(env)
    env.request = function(req)
        shapesB[#shapesB + 1] = type(req)
        if type(req) == 'table' then
            methodsB[#methodsB + 1] = tostring(req.Method)
            sentB[#sentB + 1] = req.Url
        end
        return { StatusCode = 200 }
    end
end)
check('B the probe survives an executor with one transport', okB, errB)
check('B every call to the transport is a request TABLE, not (url, body)',
    shapesB[1] == 'table' and shapesB[2] == 'table',
    'shapes seen: ' .. table.concat(shapesB, ','))
check('B the call is a POST with the url inside the table',
    methodsB[1] == 'POST' and sentB[1] ~= nil,
    'method=' .. tostring(methodsB[1]) .. ' url=' .. tostring(sentB[1]))
check('B the one that exists is reported present',
    line_for(outB, 'request') and string.find(line_for(outB, 'request'), 'present=true', 1, true) ~= nil,
    line_for(outB, 'request'))
check('B and it is reported WORKING',
    line_for(outB, 'request') and string.find(line_for(outB, 'request'), 'works=true', 1, true) ~= nil,
    line_for(outB, 'request'))
check('B the transport that is not there is still reported working=false',
    line_for(outB, 'httpservice') and
        string.find(line_for(outB, 'httpservice'), 'works=false', 1, true) ~= nil,
    line_for(outB, 'httpservice'))
check('B two files were posted: the candidate and the summary', #sentB == 2, #sentB)
check('B the first is the candidate file', sentB[1] and
    string.find(sentB[1], 'request.txt', 1, true) ~= nil, sentB[1])
check('B the second is the summary', sentB[2] and
    string.find(sentB[2], 'summary.txt', 1, true) ~= nil, sentB[2])
check('B the summary goes out through the transport that worked',
    string.find(outB, 'summary via request', 1, true) ~= nil, outB)

-- ------------------------------------------------------- C: present, but 500 --
local postC = 0
local okC, errC, outC = run_probe(function(env)
    env.request = function() postC = postC + 1; return { StatusCode = 500 } end
end)
check('C a present-but-failing transport is not a winner', okC, errC)
check('C it is reported present and NOT working',
    line_for(outC, 'request') and string.find(line_for(outC, 'request'), 'present=true', 1, true) ~= nil
    and string.find(line_for(outC, 'request'), 'works=false', 1, true) ~= nil,
    line_for(outC, 'request'))
check('C the status is named in the detail',
    line_for(outC, 'request') and string.find(line_for(outC, 'request'), 'status 500', 1, true) ~= nil,
    line_for(outC, 'request'))
check('C no summary is written, because no transport could carry it',
    string.find(outC, 'NO transport worked', 1, true) ~= nil, outC)
check('C it tried exactly once, and did not retry into a loop', postC == 1, postC)

-- -------------------------------------------- D: HttpService, but it raises --
-- The executor that matters most: no `request` anywhere, HttpService raises, and
-- the only channel that answers is the GET used to fetch the script.  That is the
-- shape that would leave the watcher silent AND silent about being silent, so it
-- gets its own scenario rather than being folded into C.
local okD, errD, outD = run_probe(function(env)
    env.game = { PlaceId = 17596243941,
        HttpGet = function() return 'receiver up' end,
        GetService = function(_, name)
            if name ~= 'HttpService' then error('unexpected service ' .. name) end
            return { PostAsync = function() error('Http requests are not enabled') end }
        end }
end)
check('D the probe survives a client HttpService', okD, errD)
check('D HttpService is reported present and not working',
    line_for(outD, 'httpservice') and
        string.find(line_for(outD, 'httpservice'), 'works=false', 1, true) ~= nil,
    line_for(outD, 'httpservice'))
check('D and the raise is named rather than swallowed into "status 0"',
    line_for(outD, 'httpservice') and
        string.find(line_for(outD, 'httpservice'), 'Http requests are not enabled', 1, true) ~= nil,
    line_for(outD, 'httpservice'))
check('D a GET channel is read as reachable-and-worthless, not as a winner',
    line_for(outD, 'httpget') and
        string.find(line_for(outD, 'httpget'), 'works=true', 1, true) ~= nil,
    line_for(outD, 'httpget'))
check('D and with no POST transport there is still no winner',
    string.find(outD, 'NO transport worked', 1, true) ~= nil, outD)

print(string.format('transport_probe: %d PASS, %d FAIL', pass, fail))
if fail > 0 then os.exit(1) end
