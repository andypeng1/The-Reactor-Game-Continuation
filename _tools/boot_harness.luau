-- ============================================================================
-- boot_harness.luau -- the test rig for TRG_original_boot.luau
-- ============================================================================
-- Runs the SHIPPED file under stubs and drives it, rather than testing a copy of
-- its logic.  Both facts matter and they are different facts:
--
--   * it loads the file that is actually served over 8766, so a change that is
--     not in that file cannot pass this;
--   * the clock is VIRTUAL (a scheduler, not task.wait), so "60 changes inside
--     one tick" is a thing this can express and a thing it can observe.
--
-- The scheduler is the one discipline Phase 64 paid for: a harness whose timeline
-- is advanced by real time is a coin flip, and a coin flip that passes is worse
-- than a test that fails, because it will be believed.
--
--   lua.exe _tools/boot_harness.luau [path-to-the-script] [scenario]
--
-- Scenarios: default | nobutton | noroot | nosink | rightcontrol
--     nobutton     no MonitorBootButton  -> the script must report its own death
--     noroot       no Workspace.Monitors -> ditto, from the other end
--     nosink       every POST is refused -> the disk fallback, and meta says so
--     rightcontrol the run ends on the hotkey instead of on the dial
--
-- Exit 0 only if every check passed.  Each check prints one line, PASS or FAIL
-- with the name first, so a mutation driver can grep for the name it expects to
-- have gone red instead of trusting an exit code.
-- ============================================================================

local NL = string.char(10)

local passed, failed = 0, 0
local fails = {}
local function check(name, cond, detail)
    if cond then
        passed = passed + 1
        print('PASS ' .. name)
    else
        failed = failed + 1
        fails[#fails+1] = name
        print('FAIL ' .. name .. '  -- ' .. tostring(detail or ''))
    end
end

local PATH = arg and arg[1] or '_tools/TRG_original_boot.luau'
local SCENARIO = arg and arg[2] or 'default'

-- ========== THE VIRTUAL FILESYSTEM ==========
local FS = {}
local function writefile(p, body) FS[p] = body end
local function appendfile(p, body) FS[p] = (FS[p] or '') .. body end
local function isfolder(p)
    for k in pairs(FS) do
        if string.sub(k, 1, #p + 1) == p .. '/' then return true end
    end
    return false
end
local function makefolder(p) FS[p .. '/'] = true end

-- ========== THE SINK ==========
local POSTS = {}
-- nosink means the sink refuses EVERYTHING, beacons included.  It used to mean
-- nothing at all: the flag was declared and never lowered, so the scenario ran the
-- happy path and the four fallback checks failed against a sink that had quietly
-- been working the whole time.  A scenario that does not change the input is not a
-- scenario, it is four red lines.
local SINK_UP = (SCENARIO ~= 'nosink')
_G.http_request = function(req)
    if not SINK_UP then return { StatusCode = 503, Error = 'refused' } end
    POSTS[#POSTS+1] = { url = req.Url, body = req.Body }
    return { StatusCode = 200, Body = 'RECV' }
end

-- Every body sent for one artifact, concatenated in arrival order.  The append
-- URL carries ?mode=a, so the match is on the artifact's path, not the raw URL.
local function capture(suffix)
    local out = {}
    for _, p in ipairs(POSTS) do
        local base = string.match(p.url, '^([^?]*)') or p.url
        if string.sub(base, -#suffix) == suffix then out[#out+1] = p.body end
    end
    return table.concat(out)
end
local function sentCount(suffix)
    local n = 0
    for _, p in ipairs(POSTS) do
        local base = string.match(p.url, '^([^?]*)') or p.url
        if string.sub(base, -#suffix) == suffix then n = n + 1 end
    end
    return n
end
local function localFile(tag)
    for k, v in pairs(FS) do
        if string.find(k, tag, 1, true) then return v end
    end
    return nil
end
-- The artifact, wherever the transport put it: the sink if it took it, the disk if
-- it did not.  Reading only POSTS would score a working fallback as a total loss.
local function artifact(name)
    local posted = capture('/' .. name)
    if #posted > 0 then return posted end
    return localFile((string.gsub(name, '%.txt$', '')) .. '_') or ''
end

local skipped = 0
local function skip(name, why)
    skipped = skipped + 1
    print('SKIP ' .. name .. '  -- ' .. tostring(why or ''))
end

-- ========== THE SCHEDULER ==========
local SCHED = { now = 0, queue = {} }
_G.task = {
    spawn = function(fn) SCHED.queue[#SCHED.queue+1] = { t = SCHED.now, co = coroutine.create(fn) } end,
    wait = function(sec) coroutine.yield(sec or 0) end,
    defer = function(fn) SCHED.queue[#SCHED.queue+1] = { t = SCHED.now, co = coroutine.create(fn) } end,
}

local function pump(untilT)
    while true do
        local bestI, bestT = nil, nil
        for i, e in ipairs(SCHED.queue) do
            if e.t <= untilT and (bestT == nil or e.t < bestT) then bestI, bestT = i, e.t end
        end
        if bestI == nil then break end
        local e = table.remove(SCHED.queue, bestI)
        SCHED.now = e.t
        local ok, delay = coroutine.resume(e.co)
        if not ok then
            failed = failed + 1
            fails[#fails+1] = 'the script threw inside a coroutine'
            print('FAIL the script threw inside a coroutine  -- ' .. tostring(delay))
        elseif coroutine.status(e.co) == 'suspended' then
            SCHED.queue[#SCHED.queue+1] = { t = SCHED.now + (tonumber(delay) or 0), co = e.co }
        end
    end
    if untilT > SCHED.now then SCHED.now = untilT end
end
local function idle() pump(SCHED.now + 0.001) end
local function advance(sec) pump(SCHED.now + sec) end

-- ========== THE INSTANCE STUB ==========
local CONN = {}
local function Signal()
    local s = { fns = {} }
    function s:Connect(fn)
        local conn = { Connected = true }
        -- Disconnect has to EXIST, or the stub cannot express the one state the
        -- recorder now depends on: a key whose instance was replaced, whose old
        -- connection is aimed at a corpse.  Without it the script's own
        -- pcall(conn:Disconnect) fails silently and the ghost test below reports
        -- the shipped file as broken -- a stub's missing method blaming the code
        -- under test (the same failure mode the DescendantAdded line in MT.__index
        -- carries a warning about).
        conn.Disconnect = function(self)
            self.Connected = false
            CONN[self] = nil
        end
        CONN[conn] = fn
        self.fns[#self.fns+1] = conn
        return conn
    end
    function s:Fire(...)
        local snapshot = {}
        for i, c in ipairs(self.fns) do snapshot[i] = c end
        for _, c in ipairs(snapshot) do
            if c.Connected and CONN[c] then CONN[c](...) end
        end
    end
    return s
end

local MT = {}
MT.__index = function(self, k)
    -- DescendantAdded is the one name the stub keeps under an underscore, so it
    -- has to be mapped back.  Without this line the signal reads as nil, the
    -- script's own pcall around the connection swallows it, and the harness
    -- reports "a label created during the run is watched" as a failure of the
    -- SHIPPED FILE -- a stubbed-out signal blaming the code under test.
    if k == 'DescendantAdded' then return rawget(self, '_added') end
    local p = rawget(self, '_props')
    if p ~= nil and p[k] ~= nil then return p[k] end
    return rawget(self, k) or MT[k]
end
MT.__newindex = function(self, k, v)
    if k == 'Parent' then
        local old = rawget(self, '_parent')
        local kids = old and rawget(old, '_children') or nil
        if kids then
            for i = #kids, 1, -1 do if kids[i] == self then table.remove(kids, i) end end
        end
        rawset(self, '_parent', v)
        if v then
            local vk = rawget(v, '_children')
            vk[#vk+1] = self
            -- DescendantAdded fires on EVERY ancestor, not only on the parent: a
            -- label created three levels down is still a new descendant of
            -- Monitors, and a stub that fires only the immediate parent would let
            -- a broken script pass this rig.
            local n = v
            while n ~= nil do
                local sig = rawget(n, '_added')
                if sig then sig:Fire(self) end
                n = rawget(n, '_parent')
            end
        end
        return
    end
    local p = rawget(self, '_props')
    if p[k] ~= v then
        p[k] = v
        local sigs = rawget(self, '_signals')
        local sig = sigs[k]
        if sig then sig:Fire() end
    end
end

MT.GetPropertyChangedSignal = function(self, prop)
    local sigs = rawget(self, '_signals')
    if sigs[prop] == nil then sigs[prop] = Signal() end
    return sigs[prop]
end
MT.FindFirstChild = function(self, name)
    for _, c in ipairs(rawget(self, '_children')) do
        if c.Name == name then return c end
    end
    return nil
end
MT.WaitForChild = function(self, name) return self:FindFirstChild(name) end
MT.GetChildren = function(self)
    local out = {}
    for i, c in ipairs(rawget(self, '_children')) do out[i] = c end
    return out
end
MT.GetDescendants = function(self)
    local out = {}
    local function walk(n)
        for _, c in ipairs(rawget(n, '_children')) do
            out[#out+1] = c
            walk(c)
        end
    end
    walk(self)
    return out
end
MT.GetFullName = function(self)
    local parts, n = {}, self
    while n ~= nil do
        table.insert(parts, 1, n.Name)
        n = rawget(n, '_parent')
    end
    return table.concat(parts, '.')
end

local function inst(class, name, props, parent)
    local o = { _props = { ClassName = class, Name = name }, _children = {},
                _signals = {}, _added = Signal(), _parent = nil }
    if props then for k, v in pairs(props) do o._props[k] = v end end
    setmetatable(o, MT)
    if parent then o.Parent = parent end
    return o
end

-- ========== THE FIXTURE ==========
-- Two monitors, because one monitor cannot show that the scope was followed
-- rather than a name hard-coded.  A GlitchEffect under each, because that is the
-- measured decoration.  A boot frame that is a plain Frame, so the 60 Hz test
-- has a key the geometry filter does NOT remove -- otherwise the coalescing test
-- and the exclusion test would be the same test.
local workspace = inst('Workspace', 'Workspace')
workspace.GetServerTimeNow = function() return SCHED.now end
_G.workspace = workspace

local Monitors = inst('Model', 'Monitors', {}, workspace)
local function monitor(name)
    local m = inst('Model', name, {}, Monitors)
    local screen = inst('Model', 'Screen', {}, m)
    local ui = inst('Model', 'MonitorUI', {}, screen)
    -- NESTED, not a sibling: the path the filter is measured against is
    -- ...MonitorUI.GlitchEffect.GlitchFrame, and a GlitchFrame parented straight to
    -- ui would have a path with no '.GlitchEffect' in it at all -- so the exclusion
    -- check would have passed for the wrong reason and stopped measuring anything.
    local ge = inst('Frame', 'GlitchEffect', { Position = '0,0', Size = '0,0' }, ui)
    local glitch = inst('Frame', 'GlitchFrame',
        { Position = '0,0', Size = '0,0', Visible = true, BackgroundTransparency = 0 }, ge)
    local main = inst('Frame', 'MainMonitorFrame', { Visible = true, Size = '1,1' }, ui)
    inst('TextLabel', 'TitleText', { Text = name, Visible = true }, main)
    local tf = inst('Frame', 'TimeFrame', {}, main)
    local label = inst('TextLabel', 'TimeLabel', { Text = '12:00 AM', Visible = true }, tf)
    return m, ui, glitch, label
end
local _, UI1, GLITCH1, LABEL = monitor('QuotaControlRoomMonitor')
monitor('ForecastControlRoomMonitor')
local LOGUI = select(2, monitor('LogControlRoomMonitor'))

-- The SYSTEM LOGS panel: it exists from the start (so the census sees it) and is
-- EMPTY, because the messages are cloned into it at runtime -- one fresh row per
-- message, reusing the same three names.  Section 5b uses it: a path is not an
-- object, and this is the panel where that stops being academic.
local LOGS = inst('Frame', 'LogsFrame', {}, LOGUI)

-- A boot frame: Visible false, and a plain Frame so its geometry IS watched.
local BOOT = inst('Frame', 'BootFrame',
    { Visible = false, Position = '0,0', Size = '1,1', BackgroundTransparency = 1 }, UI1)
local BOOTLABEL = inst('TextLabel', 'TitleText1',
    { Text = 'STANDARD BOOT UP INITIALIZED', Visible = false }, BOOT)

-- Not under Monitors at all: a control-room frame the scope must ignore.
local OUTSIDE = inst('Frame', 'SomeOtherFrame', { Visible = false, Position = '0,0' }, workspace)

local Consoles = inst('Model', 'Consoles', {}, workspace)
local console = inst('Model', 'MainReactorConsole', {}, Consoles)
local button = inst('Model', 'MonitorBootButton', {}, console)
local clickPart = inst('Frame', 'ClickPart', {}, button)
local DETECTOR = nil
if SCENARIO ~= 'nobutton' then
    DETECTOR = inst('Frame', 'ClickDetector', { MouseClick = Signal() }, clickPart)
end

local ROOT = Monitors
if SCENARIO == 'noroot' then
    Monitors.Parent = nil
    ROOT = nil
end

-- ========== SERVICES ==========
local INPUT = Signal()
local SERVICES = {
    HttpService = { PostAsync = nil },
    UserInputService = { InputBegan = INPUT },
}
_G.game = {
    PlaceId = 17596243941,
    GetService = function(_, name) return SERVICES[name] end,
}
_G.warn = function(msg) end
_G.writefile, _G.appendfile, _G.isfolder, _G.makefolder =
    writefile, appendfile, isfolder, makefolder

-- ========== LOAD AND RUN THE SHIPPED FILE ==========
local chunk, err = loadfile(PATH)
if chunk == nil then
    print('FAIL the script does not compile  -- ' .. tostring(err))
    os.exit(1)
end
local okRun, errRun = pcall(chunk)
if not okRun then
    print('FAIL the module body threw  -- ' .. tostring(errRun))
    os.exit(1)
end

idle()   -- let the spawns at load time reach their first wait

-- ========== THE LINE READER ==========
-- This checks the same SHAPE the archived readers check, in Lua's pattern
-- language rather than Python's -- and those two are not the same language, which
-- is the mistake this block carries a warning about.  Lua escapes with PERCENT,
-- not backslash: a backslash is a literal character and a bare ] closes the set,
-- so a Python regex pasted into string.match matches nothing at all and every
-- line reads as malformed.  Percent-escapes below, and the '-' must be escaped
-- too because '<-' would otherwise parse as a lazy quantifier on '<'.
--
-- The AUTHORITATIVE check is the Python one in run_tests.sh
-- (verify_boot_capture.py), which uses the readers' own pattern, extracted from
-- their own source file.  This one is here so a malformed line can go red inside
-- the harness, where the number of lines that failed is visible.
local LINE_RX = '^Time:%[([0-9:]+)%]<%-O:%[([^%]]*)%]<%-C:%[([^%]]*)%]<%-V:%[(.*)%]$'

local function isDataLine(l)
    return string.match(l, LINE_RX) ~= nil
end
local function captureLines()
    local acc = {}
    for l in string.gmatch(artifact('ScreenChanges.txt') .. NL, '([^' .. NL .. ']*)' .. NL) do
        acc[#acc+1] = l
    end
    return acc
end
local function countFor(keyFragment)
    local n = 0
    for _, l in ipairs(captureLines()) do
        if string.find(l, keyFragment, 1, true) then n = n + 1 end
    end
    return n
end

-- A line exists in two places before it reaches the sink: the script's buffer and
-- the wire.  countFor sees only the wire, so a measurement taken while a line sits
-- in the 2 s buffer reads zero and the verdict depends on where the timer happens
-- to land -- the coin flip Phase 64 already paid for once.  Every measurement below
-- therefore starts with an explicit flush.  RightAlt's handler runs synchronously
-- inside the signal, so the flush is complete when this returns and no time has
-- passed: nothing but the key can be the cause of what appears.
local function key(name)
    INPUT:Fire({ KeyCode = 'Enum.KeyCode.' .. name }, false)
end
local function flushNow() key('RightAlt') end

-- The build string is read OFF THE SHIPPED FILE, not written here a second time.
-- A literal in the harness is a copy of the one number that changes every build,
-- and a stale copy fails against a correct file -- which is how the check that the
-- capture names its own build turned red for a reason that had nothing to do with
-- the capture.  Anchored on the CONFIG assignment, so a 'b3' in a comment above it
-- cannot satisfy the match.  Under the mutation suite PATH is the mutant, which
-- carries the same line, and that is the copy the mutant is being asked about.
local SRC_BUILD = (function()
    local fh = io.open(PATH, 'r')
    if fh == nil then return nil end
    local body = fh:read('*a')
    fh:close()
    return string.match(body, "Build%s*=%s*'([^']+)'")
end)()

-- ========== 1. THE BEACONS ==========
check('the beacon names the transport it actually selected',
    string.find(artifact('alive.txt'), 'transport=http_request', 1, true) ~= nil,
    artifact('alive.txt'))
check('the beacon says whether the root was there when it was injected',
    string.find(artifact('hello.txt'), 'root_visible_at_inject=' .. tostring(SCENARIO ~= 'noroot'), 1, true) ~= nil,
    artifact('hello.txt'))
if SCENARIO == 'nosink' then
    check('a refused sink sends the beacon to the disk instead',
        sentCount('/alive.txt') == 0 and localFile('alive_') ~= nil, 'alive.txt')
else
    check('the armed beacon is posted without any boot press',
        sentCount('/hello.txt') == 1, sentCount('/hello.txt'))
end
check('no capture line is posted before the boot press',
    sentCount('/ScreenChanges.txt') == 0, sentCount('/ScreenChanges.txt'))

if SCENARIO == 'noroot' then
    -- Nothing about the world is resolved until the press, and that is deliberate:
    -- it is what "inject BEFORE pressing the button" means, and it is the safe
    -- order under StreamingEnabled, where Workspace.Monitors may not have
    -- replicated at injection.  A load-time death would then be a false alarm on a
    -- world that was merely late -- so the check the harness used to make
    -- ("reported without waiting for a press") was the wrong contract, and the
    -- beacon field above is what answers "was I too early" instead.
    DETECTOR.MouseClick:Fire()
    idle()
    check("a missing Workspace.Monitors is reported as the script's own death",
        string.find(artifact('meta.txt'), 'reason=error', 1, true) ~= nil and
        string.find(artifact('meta.txt'), 'there is no Workspace.Monitors', 1, true) ~= nil,
        artifact('meta.txt'))
    check('the death costs no capture line',
        sentCount('/ScreenChanges.txt') == 0, sentCount('/ScreenChanges.txt'))
    print(string.format('%d PASS / %d FAIL / %d SKIP', passed, failed, skipped))
    os.exit(failed == 0 and 0 or 1)
end

-- ========== 2. THE PRESS ==========
advance(1.0)
check('still nothing is captured one second after load',
    sentCount('/ScreenChanges.txt') == 0, sentCount('/ScreenChanges.txt'))

if SCENARIO == 'nobutton' then
    check("a missing boot button is reported as the script's own death",
        string.find(artifact('meta.txt'), 'reason=error', 1, true) ~= nil and
        string.find(artifact('meta.txt'), 'ClickDetector', 1, true) ~= nil,
        artifact('meta.txt'))
    print(string.format('%d PASS / %d FAIL / %d SKIP', passed, failed, skipped))
    os.exit(failed == 0 and 0 or 1)
end

DETECTOR.MouseClick:Fire()
idle()
check('the press posts t0',
    string.find(artifact('boot.txt'), 't0=', 1, true) ~= nil, artifact('boot.txt'))

local BOOTKEY = 'BootFrame]<-C:[Position]'
advance(0.6)   -- let the run's tick get its bearings before measuring

-- ========== 3. THE COALESCER ==========
-- Sixty changes inside one tick is what a 60 Hz property does.  The operator's
-- recorder wrote sixty lines; this must write one.
flushNow()
local before = countFor(BOOTKEY)
for i = 1, 60 do
    BOOT.Position = '{0.' .. tostring(i) .. ',0}, {0,0}'
end
advance(0.6)
flushNow()
local afterSixty = countFor(BOOTKEY)
check('sixty changes inside one tick become at most one line',
    afterSixty - before <= 1 and afterSixty - before >= 1,
    tostring(afterSixty - before) .. ' lines for 60 changes')

-- A value that changed and changed back between two ticks is not a change.
flushNow()
local beforeRevert = countFor('BootFrame]<-C:[Visible]')
BOOT.Visible = true
BOOT.Visible = false
advance(0.6)
flushNow()
check('a value that changed and reverted inside one tick is not recorded',
    countFor('BootFrame]<-C:[Visible]') == beforeRevert,
    tostring(countFor('BootFrame]<-C:[Visible]') - beforeRevert) .. ' lines')

-- And an unchanged value is silent no matter how long the run is.
advance(3.0)
flushNow()
local beforeSteady = #captureLines()
advance(3.0)
check('a value that does not change produces nothing',
    #captureLines() == beforeSteady,
    tostring(#captureLines() - beforeSteady) .. ' lines while nothing changed')

-- ========== 4. THE DECORATION IS EXCLUDED, AND ONLY ITS GEOMETRY ==========
for i = 1, 30 do
    GLITCH1.Position = '{0.' .. tostring(i) .. ',0}, {0.' .. tostring(i) .. ',0}'
    GLITCH1.Size = '{0.0' .. tostring(i) .. ',0}, {0,3}'
end
advance(0.6)
flushNow()
local glitchLines = 0
for _, l in ipairs(captureLines()) do
    if string.find(l, 'GlitchFrame', 1, true) then glitchLines = glitchLines + 1 end
end
check('the decoration produces no line at all for its geometry', glitchLines == 0,
    tostring(glitchLines) .. ' lines mention the glitch frame')

GLITCH1.Visible = false
advance(0.6)
flushNow()
check('the decoration is still watched for what is not geometry',
    countFor('GlitchFrame]<-C:[Visible]') == 1,
    tostring(countFor('GlitchFrame]<-C:[Visible]')) .. ' lines')

check('a frame outside Workspace.Monitors is never watched',
    countFor('SomeOtherFrame') == 0, tostring(countFor('SomeOtherFrame')) .. ' lines')

-- ========== 5. DESCENDANT ADDED ==========
-- The blind spot Phase 66 and 67 both hit: an instance created during the run.
-- The label is built the way the live game builds a log frame -- text set BEFORE
-- the instance is parented (PROGRESS.md Phase 71) -- because that ordering is the
-- whole reason this scenario exists twice over.
local late = inst('TextLabel', 'LateTitle', { Text = 'RESUMING NORMAL OPERATION', Visible = false }, BOOT)
advance(0.3)
late.Visible = true
advance(0.6)
flushNow()
check('a label created during the run is watched',
    countFor('LateTitle]<-C:[Visible]') == 2,
    tostring(countFor('LateTitle]<-C:[Visible]')) .. ' lines')
check('a label born during the run is written with the text it was born with',
    countFor('LateTitle]<-C:[Text]<-V:[RESUMING NORMAL OPERATION]') == 1,
    tostring(countFor('LateTitle]<-C:[Text]')) .. ' Text lines')
check('and its birth does not replace the later change',
    countFor('LateTitle]<-C:[Visible]<-V:[true]') == 1,
    tostring(countFor('LateTitle]<-C:[Visible]<-V:[true]')) .. ' true lines')

-- ========== 5b. THE SAME PATH, TWICE ==========
-- A PATH IS NOT AN OBJECT, and the log panel is where that stops being academic.
-- Every message is a FRESH row cloned onto one of three names, so
-- ...LogsFrame.TemplateLogFrame1.TextLabel is born, fades, is destroyed and is
-- born again for the rest of the shift.  Phase 72 measured what a register() that
-- stops at 'this key already exists' costs: the recorder kept three messages out
-- of a 428 s shift while the r60 capture of the SAME shift holds 35 distinct ones
-- -- the whole narration after the first three lines, including START-UP
-- COMPLETED.  The instance set is a fixed descendant set only until something
-- clones; the KEY set was a fixed descendant set for the entire run.
--
-- The row is built the way the live game builds it -- the text is set BEFORE the
-- row is parented -- because that ordering is what makes the birth record the
-- only thing that can see the message at all.
local function logMessage(name, text)
    local row = inst('Frame', name, { Visible = true, Position = '0,0', Size = '1,0' }, LOGS)
    local lbl = inst('TextLabel', 'TextLabel', { Text = text, Visible = true }, row)
    -- Both are returned: the row is what the panel re-parents away between two
    -- messages, the label is what carries the message and what must go quiet once
    -- a different instance occupies the path.
    return row, lbl
end

local FIRST = 'PRIMING ISOTOPE E COOLANT NETWORK'
local SECOND = 'DEEP SCAN PROCEDURE COMPLETED'
local firstPath = 'TemplateLogFrame1.TextLabel]<-C:[Text]<-V:['

local row1, lbl1 = logMessage('TemplateLogFrame1', FIRST)
advance(0.3)
flushNow()
check('the first instance on a path is recorded with the text it was born with',
    countFor(firstPath .. FIRST .. ']') == 1,
    tostring(countFor('TemplateLogFrame1.TextLabel]<-C:[Text]')) .. ' Text lines')

-- The row fades and the panel destroys it; re-parenting the whole row away leaves
-- exactly the state the panel leaves behind between two messages: the path is
-- free, the name is unchanged, and the next message is a different object.
row1.Parent = nil
advance(0.3)

local _, lbl2 = logMessage('TemplateLogFrame1', SECOND)
advance(0.3)
flushNow()
check('a second instance on the same path is recorded too, so a path is not an object',
    countFor(firstPath .. SECOND .. ']') == 1,
    tostring(countFor(firstPath .. SECOND .. ']')) .. ' lines for the second message')

-- And the instance that was replaced must stop writing.  Its property signal is
-- still live unless the key was re-pointed, and a key that was never re-pointed
-- keeps a connection aimed at a corpse -- so the artifact would report a message
-- this panel never showed, on a path the corpse no longer occupies.
lbl1.Text = 'GHOST OF THE REPLACED ROW'
advance(0.3)
flushNow()
check('the replaced instance is disconnected, so its later writes do not reach the path',
    countFor(firstPath .. 'GHOST OF THE REPLACED ROW]') == 0,
    tostring(countFor(firstPath .. 'GHOST OF THE REPLACED ROW]')) .. ' ghost lines')
lbl2.Visible = false
advance(0.3)
flushNow()
check('and the live instance on that path still writes',
    countFor('TemplateLogFrame1.TextLabel]<-C:[Visible]<-V:[false]') == 1,
    'the live row wrote ' ..
    tostring(countFor('TemplateLogFrame1.TextLabel]<-C:[Visible]<-V:[false]')) ..
    ' false line(s) after the re-point')

-- ========== 6. THE HOTKEYS ==========
-- The key must deliver what the timer has not.  Establishing that is a timing
-- question, and Phase 64 paid for one of those already: a verdict that depends on
-- where a clock happens to land is a coin flip that reads as a test.  So the timer
-- is used, not raced -- one line is put in the buffer, the loop advances in small
-- steps until the timer takes it, and the next fire is then a full FlushSeconds
-- away.  The change below provably fits inside that window.
BOOT.BackgroundColor3 = '1,0,0'
-- Measured by the artifact's SIZE, not by the number of POSTs: under nosink the
-- wire is refused and the artifact grows on the disk instead, and a probe that
-- watched only the wire would report the timer as unobservable and skip the very
-- check that proves the fallback carries the same data.
local n0 = #artifact('ScreenChanges.txt')
local probed = false
for _ = 1, 80 do
    advance(0.05)
    if #artifact('ScreenChanges.txt') > n0 then probed = true break end
end
check('the 2 s flush timer is observable, so a key can be measured against it',
    probed, 'the timer did not fire within 4 s of a non-empty buffer')

local MARK = 'BootFrame]<-C:[BackgroundTransparency]'
local beforeKey = countFor(MARK)
BOOT.BackgroundTransparency = 0.5
advance(0.3)  -- one tick writes the line into the buffer; the timer is not due
check('one tick put the change in the buffer and the timer has not taken it',
    countFor(MARK) == beforeKey,
    tostring(countFor(MARK) - beforeKey) .. ' lines had already gone out')

key('RightAlt')   -- synchronous: the handler runs before this call returns
check('RightAlt flushes without waiting for the timer and without sealing',
    countFor(MARK) == beforeKey + 1 and #artifact('meta.txt') == 0,
    tostring(countFor(MARK) - beforeKey) .. ' lines after the key, ' ..
    tostring(#artifact('meta.txt')) .. ' meta bytes')

key('RightShift')
idle()
check("the recorder's seal key is not bound here",
    #artifact('meta.txt') == 0, 'RightShift sealed the run')

-- ========== 7. THE BUDGET AND ITS LEDGER ==========
-- Cross the per-key budget with one key.  Each tick can contribute at most one
-- line, so this is also a second, slower proof of the coalescer.
for i = 1, 2100 do
    BOOTLABEL.Text = 'STEP ' .. tostring(i)
    advance(0.26)
end
flushNow()
-- Exactly the budget, not "about" it: each advance is more than one tick and less
-- than two, so each change is seen by exactly one tick, and the 2100th change is
-- past a 2000-line ceiling by 100 -- a ceiling that quietly rounded up would hide
-- a key that never stopped.
check('a key that crossed its budget stops writing at exactly the budget',
    countFor('TitleText1]<-C:[Text]') == 2000,
    tostring(countFor('TitleText1]<-C:[Text]')) .. ' lines for 2100 changes')
check('the crossing is announced once, in the capture',
    (function()
        local n = 0
        for _, l in ipairs(captureLines()) do
            if string.find(l, 'SUPPRESSED', 1, true) then n = n + 1 end
        end
        return n
    end)() <= 1, 'more than one announcement')

-- ========== 8. SEALING ==========
if SCENARIO == 'rightcontrol' then
    key('RightControl')
    idle()
    check('RightControl seals the run',
        string.find(artifact('meta.txt'), 'reason=hotkey', 1, true) ~= nil,
        artifact('meta.txt'))
else
    LABEL.Text = '12:00 AM'
    idle()
    check('the opening 12:00 AM does not end the run',
        #artifact('meta.txt') == 0, "the dial's opening value sealed the run")

    -- THE MEASURED SHAPE OF A REAL RUN (Phase 71).  The press lands at 11:51 PM, so
    -- the dial is off midnight from the first reading, and midnight arrives about
    -- 89 s later, in the middle of the core's ignition ramp.  The first draft
    -- sealed there, which is the defect this sequence exists to keep dead: a
    -- scenario that only ever sets 12:00 AM as the OPENING value cannot see a rule
    -- that fires on the way back to it.
    LABEL.Text = '11:51 PM'
    idle()
    LABEL.Text = '11:59 PM'
    idle()
    LABEL.Text = '12:00 AM'
    idle()
    check('midnight does not end the run -- on this world it is the shift START',
        #artifact('meta.txt') == 0, 'the midnight crossing sealed the run')
    flushNow()
    check('the midnight crossing is recorded as a mark in the capture',
        countFor('# MARK midnight') == 1,
        tostring(countFor('# MARK midnight')) .. ' marks')

    LABEL.Text = '12:01 AM'
    idle()
    LABEL.Text = '12:00 PM'
    idle()
    check('the 12:00 PM handoff seals the run',
        string.find(artifact('meta.txt'), 'reason=noon', 1, true) ~= nil,
        artifact('meta.txt'))
end

check('the seal names the suppression ledger it wrote',
    string.find(artifact('meta.txt'), 'suppressed_keys=', 1, true) ~= nil,
    artifact('meta.txt'))
-- The ledger line is path|prop|count|wallclock and the announcement is
-- '# SUPPRESSED path|prop after count writes', so the shared part is path|prop:
-- the announcement must not be a different key from the one the ledger names.
check('every key in the ledger was also named in the capture',
    (function()
        local led = artifact('suppressed.txt')
        if led == '' then return true end
        local first = string.match(led, '([^' .. NL .. ']+)')
        local fullprop = string.match(first or '', '^([^' .. NL .. ']-)|%d')
        return fullprop ~= nil and
            string.find(artifact('ScreenChanges.txt'), 'SUPPRESSED ' .. fullprop, 1, true) ~= nil
    end)(), 'the ledger has an entry the capture never mentions')

-- ========== 9. THE CAPTURE IS STILL READABLE ==========
local all = captureLines()
local dataLines, badLines = 0, 0
for idx, l in ipairs(all) do
    if idx == #all and l == '' then
        -- captureLines appends NL before splitting, so a body that already ends in
        -- one yields a final empty match.  That is this helper's artifact, not a
        -- byte the recorder wrote -- and counting it reported a phantom failure.
        -- Only the LAST one is exempt: a blank line in the middle is a defect.
    elseif string.sub(l, 1, 1) == '#' then
        -- a comment line, which no reader matches and every reader skips
    else
        dataLines = dataLines + 1
        if not isDataLine(l) then badLines = badLines + 1 end
    end
end
check("every data line matches the archived readers' pattern exactly",
    badLines == 0, tostring(badLines) .. ' of ' .. tostring(dataLines) .. ' lines do not')
check('the capture is not empty', dataLines > 100, tostring(dataLines) .. ' data lines')
check('the capture opens with a header naming the build',
    SRC_BUILD ~= nil and
    string.find(captureLines()[1] or '', 'build=' .. SRC_BUILD, 1, true) ~= nil,
    tostring(captureLines()[1]) .. '  (source says ' .. tostring(SRC_BUILD) .. ')')

-- ========== 10. THE TWO OUTPUT PATHS ==========
if SCENARIO == 'nosink' then
    check('a refused sink sends every chunk to the disk instead',
        string.find(artifact('meta.txt'), 'sink_chunks=0', 1, true) ~= nil and
        tonumber(string.match(artifact('meta.txt'), 'local_chunks=(%d+)')) > 0,
        artifact('meta.txt'))
    check('the reason the sink was abandoned is recorded',
        string.find(artifact('meta.txt'), 'sink_error=none', 1, true) == nil,
        artifact('meta.txt'))
    check("the disk copy is the operator's own filename, stamped",
        localFile('ScreenChanges_') ~= nil, 'no local ScreenChanges file')
    check('the disk copy opens with the capture header, not with metadata',
        string.sub(localFile('ScreenChanges_') or '', 1, #'# build=') == '# build=',
        'the local file does not look like the capture')
else
    check('a working sink writes no local ScreenChanges file',
        localFile('ScreenChanges_') == nil, 'a local capture exists anyway')
    check('everything went through the sink',
        string.find(artifact('meta.txt'), 'sink_error=none', 1, true) ~= nil and
        tonumber(string.match(artifact('meta.txt'), 'local_chunks=(%d+)')) == 0,
        artifact('meta.txt'))
end

if SCENARIO == 'nosink' then
    -- With the sink refusing every POST there is no wire order to read, and the
    -- disk path is a single dict keyed by path -- so the ordering guarantee is
    -- simply not measurable in this scenario.  Said out loud rather than scored as
    -- a pass, because "not measured" and "measured and fine" are different facts.
    skip('the seal record arrives after the data it describes',
        'nothing reached the wire, so there is no arrival order to read')
else
    check('the seal record arrives after the data it describes',
        (function()
            local lastData, metaAt = 0, 0
            for i, p in ipairs(POSTS) do
                local base = string.match(p.url, '^([^?]*)') or p.url
                if string.sub(base, -17) == '/ScreenChanges.txt' then lastData = i end
                if string.sub(base, -9) == '/meta.txt' then metaAt = i end
            end
            return metaAt > lastData and metaAt > 0
        end)(), 'meta.txt went out before the capture it describes')
end

-- ========== HAND THE CAPTURE TO THE PYTHON READER ==========
-- The authoritative compatibility check runs in Python against the readers' own
-- pattern, so the bytes have to leave this process.  Line endings are forced to
-- LF: this is Windows, and a CRLF file would make the readers' trailing dollar
-- anchor fail on every line -- a harness that passes by writing a file its
-- readers cannot open is not a harness.
local function dump(tag, body)
    local f = io.open('_tools/_harness_out/boot_' .. SCENARIO .. '_' .. tag .. '.txt', 'wb')
    if f == nil then return end
    -- The parentheses are load-bearing: string.gsub returns (text, count), and
    -- f:write takes a variadic list -- without them the substitution count is
    -- written into the file as a line of its own, which the readers' anchored
    -- pattern then rejects.  A one-character bug that shows up as data corruption.
    f:write((string.gsub(body, string.char(13) .. NL, NL)))
    f:close()
end
local body = artifact('ScreenChanges.txt')

dump('ScreenChanges', body)
dump('meta', artifact('meta.txt'))
dump('suppressed', artifact('suppressed.txt'))

print(string.format('%d PASS / %d FAIL / %d SKIP', passed, failed, skipped))
os.exit(failed == 0 and 0 or 1)
