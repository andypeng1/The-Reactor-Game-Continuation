-- __probeSampler -- a Play-session-only recorder, dropped into ServerScriptService.
--
-- WHY IT IS A SCRIPT AND NOT A TOOL CALL. CLAUDE 0.2: the command bar runs in its
-- own Luau VM, so `require`ing a backend module there hands back a fresh empty
-- copy and every reading taken through it is a false negative. The readings that
-- are true are the INSTANCE ones, and the only way to take them hundreds of times
-- across a six-minute shift is to have something doing it from inside the session.
--
-- WHAT IT RECORDS. Three streams, each line stamped with seconds since the sampler
-- came up:
--   * every `[ReactorBackend]` line the runtime prints, tapped from LogService
--     rather than scraped from the output window. This is where the control
--     DELIVERY oracle lives -- `[ReactorBackend][Control] <player> -> <LABEL>` is a
--     delivery, `... rejected: <err>` is a delivery the engine refused, and the
--     absence of both is a request that never arrived (DECISIONS_2 520). A
--     playtest's prints are otherwise unreadable from outside (CLAUDE 0.16), so
--     turning them into a StringValue is the whole point of this file.
--   * the reactor's own published numbers (workspace.Stats), a line per CHANGED
--     value so a quiet stretch costs nothing, and
--   * the phase attribute, which is the headline and is always written when it moves.
--
-- WHY EVERY LINE CARRIES A TIME. Phase 127's method is that two readings taken in
-- one session are not readings of the same instant (DECISIONS_2 537), and the only
-- defence is a stamp on each. The clock is `workspace:GetServerTimeNow()` and not a
-- frame counter: at 60 fps those agree, and during a hitch only one of them still
-- means seconds.
--
-- AND ITS OWN DEATH. CLAUDE 0.17: this runs in a thread nobody awaits, so "in
-- flight and idle" and "threw on the first frame and stopped" are byte-identical
-- from outside. Both the per-frame scan and the whole loop are wrapped, and a
-- throw writes SAMPLER DIED with the message, so a silent sampler can never be
-- read as a quiet one.
--
-- NO BACKSLASH ANYWHERE (CLAUDE 0.10). Newlines come from string.char(10).

local RunService = game:GetService('RunService')
local LogService = game:GetService('LogService')
local ws = game.Workspace
local backend = game.ServerScriptService:FindFirstChild('ReactorBackend')
local NL = string.char(10)

local report = ws:FindFirstChild('__probeReport')
if not report then
    report = Instance.new('StringValue')
    report.Name = '__probeReport'
    report.Parent = ws
end

local lines = {}
local t0 = ws:GetServerTimeNow()
local function push(text)
    lines[#lines + 1] = string.format('t=%.3f %s', ws:GetServerTimeNow() - t0, text)
    if #lines > 300 then table.remove(lines, 1) end
    report.Value = table.concat(lines, NL)
end

-- The tap. Wrapped, because a connection that throws is otherwise invisible
-- (CLAUDE 0.19: the plugin VM answers Wait but never runs a callback inside a
-- connection -- this is the same hazard one layer down).
LogService.MessageOut:Connect(function(message, kind)
    local ok, err = pcall(function()
        local text = tostring(message)
        if string.find(text, 'ReactorBackend', 1, true) or string.find(text, '[Control]', 1, true) then
            push(string.format('%s %s', tostring(kind), text))
        end
    end)
    if not ok then push('LOG TAP DIED: ' .. tostring(err)) end
end)

local last = {}
local lastPhase = 'unread'
local function scan()
    local phase = backend and tostring(backend:GetAttribute('RuntimePhase')) or 'none'
    if phase ~= lastPhase then
        lastPhase = phase
        push('phase=' .. phase)
    end
    local err = backend and backend:GetAttribute('RuntimeError')
    if err and err ~= '' and err ~= last.runtimeError then
        last.runtimeError = err
        push('RuntimeError=' .. tostring(err))
    end
    local stats = ws:FindFirstChild('Stats')
    if not stats then return end
    local order = {'TemperatureVal', 'PressureVal', 'StressVal', 'OutputVal', 'HDEFVal',
        'RadiationVal', 'EnergyVal', 'QuotaVal', 'ActiveQPUs'}
    local parts = {}
    for _, key in ipairs(order) do
        local v = stats:FindFirstChild(key)
        if v and v:IsA('ValueBase') then
            local value = v.Value
            if last[key] ~= value then
                last[key] = value
                parts[#parts + 1] = key .. '=' .. tostring(value)
            end
        end
    end
    if #parts > 0 then push(table.concat(parts, ' ')) end
end

local ok, err = pcall(function()
    push('SAMPLER UP phase=' .. tostring(backend and backend:GetAttribute('RuntimePhase')))
    local frames = 0
    while frames < 60 * 60 * 30 do
        frames += 1
        local fine, problem = pcall(scan)
        if not fine then
            push('SAMPLER DIED: ' .. tostring(problem))
            return
        end
        RunService.Heartbeat:Wait()
    end
    push('SAMPLER HIT ITS OWN FRAME LIMIT')
end)
if not ok then push('SAMPLER DIED OUTSIDE: ' .. tostring(err)) end
