-- watch_harness.luau -- drives the SHIPPED _tools/TRG_original_watch.luau against
-- a synthetic Workspace, under a stub of the Roblox API, on plain Lua 5.1.
--
-- WHY THIS EXISTS.  The watcher cannot be run in Studio: it is written for the
-- ORIGINAL game, it is injected by Solara, and the one thing it is for -- a
-- start-up -- can only be performed once per shift by a human hand.  So the
-- failure mode it has to be protected against is not "it crashes", it is "it
-- crashes or silently does nothing AFTER the operator has thrown the lever", when
-- the run is gone and the next opportunity is a whole shift away.
--
-- A parse gate does not cover that.  Three bugs found by hand in this file before
-- it ever ran -- a `local function` called above its own definition, twice, and
-- `Workspace:GetChildren()` where the global is lowercase `workspace` -- all three
-- parse perfectly.  Two of them would have raised, and the third (the forward
-- declarations) would have raised only on the first flush, i.e. after tree.txt
-- had already been written, so the symptom would have been "the census arrived and
-- then nothing did" -- which reads as a watcher that ran and found a still room.
--
-- WHAT IT DOES NOT COVER, and this is the whole caveat.  These are stubs.  A green
-- run proves the file's own logic -- registration, the hold ring, the quiet
-- release, the census and its budget, the audio tally, the forward-declaration
-- order, the summary cursor walk -- and it proves NOTHING about whether
-- Sound.Played exists in the original game, whether the console paths are real, or
-- whether the client can even reach the sink.  It is a test of this file, not of
-- that game.
--
-- It loads the SHIPPED file by path.  There is no copy of the watcher's logic here
-- that could drift from the one that gets injected; the only thing written twice
-- is the API surface, which is the thing under test's dependency and not its
-- subject.
--
--   lua5.1 _tools/watch_harness.luau
--
-- Prints one line per check and exits 1 if any failed.

-- Arguments come through the mutation runner, which points the harness at a
-- deliberately broken copy of the watcher and checks that a SPECIFIC assertion is
-- the one that turns red.  A check nobody has ever seen fail is not a check.
--   <path>   watch a copy other than the shipped one
--   --dump   write the captured sink to _tools/_harness_out/
--   --boom   make a property read throw, and assert the watcher writes its own
--            error.txt.  Its own scenario, because the main one's claim is that
--            error.txt is ABSENT.
--   --boot   make the CENSUS throw, and assert that a start-up death is still
--            readable from the sink: hello.txt present, error.txt present and
--            naming the start-up, tree.txt absent.  Its own scenario for the same
--            reason as --boom, and it is the one that models the run the operator
--            actually lost -- a shift with a watcher that produced nothing at all.
--   --nolever  the start-up lever resolves, but the instance it resolves to carries
--            no ClickDetector, and the game's own flag still goes true.  The window
--            must open on the FALLBACK and window.txt must say so -- the reading a
--            reader needs when the timeline is right but starts at the wrong moment.
--            It is the wrong-CLASS branch: the path is fine, the shape is not.
--   --nopath  the start-up lever's part is not there at all, and the flag still goes
--            true.  Same fallback, different miss: "the path does not resolve" is the
--            other half of "why is there no lever hook", and the two are repaired
--            differently -- one by looking at the part, one by looking at the path.
--   --nowindow the lever cannot be resolved AND the flag never goes true: nothing
--            opens the window.  The timeline must still reach the sink, under a
--            marker that says the window never opened, because the alternative is a
--            whole shift that reads as "nothing happened".
--   --closewin the dial reaches 12:00 with the window open.  The run must end on its
--            own -- that is half of the operator's rule -- and end with a CLOSE
--            marker rather than with a stop.
--            Four scenarios and not one because the failures they model are the same
--            reading from the far end -- a timeline that starts in the wrong place,
--            or does not arrive -- and the operator gets one shift.
local ARGS = arg or {}
local WATCHER = '_tools/TRG_original_watch.luau'
local DUMP, BOOM, BOOT = false, false, false
local NOLEVER, NOPATH, NOWINDOW, CLOSEWIN = false, false, false, false
local DUMPDIR = '_tools/_harness_out'
for _, a in ipairs(ARGS) do
    if a == '--dump' then DUMP = true
    elseif a == '--boom' then BOOM = true
    elseif a == '--boot' then BOOT = true
    elseif a == '--nolever' then NOLEVER = true
    elseif a == '--nopath' then NOPATH = true
    elseif a == '--nowindow' then NOPATH, NOWINDOW = true, true
    elseif a == '--closewin' then CLOSEWIN = true
    elseif string.sub(a, 1, 6) == '--out=' then DUMPDIR = string.sub(a, 7) DUMP = true
    elseif string.sub(a, 1, 1) ~= '-' then WATCHER = a end
end

local NL = string.char(10)

-- ========== A STUB OF THE ROBLOX API ==========
-- Only what the watcher touches.  Kept deliberately small: every name here is
-- either an API the watcher uses or a class it asks IsA about, and anything else
-- should blow up loudly rather than be quietly absent.

local ANCESTRY = {
    Instance        = {'Instance'},
    Folder          = {'Folder', 'Instance'},
    Model           = {'Model', 'PVInstance', 'Instance'},
    Part            = {'Part', 'BasePart', 'PVInstance', 'Instance'},
    ClickDetector   = {'ClickDetector', 'Instance'},
    BoolValue       = {'BoolValue', 'ValueBase', 'Instance'},
    NumberValue     = {'NumberValue', 'ValueBase', 'Instance'},
    StringValue     = {'StringValue', 'ValueBase', 'Instance'},
    ObjectValue     = {'ObjectValue', 'ValueBase', 'Instance'},
    Sound           = {'Sound', 'Instance'},
    SoundGroup      = {'SoundGroup', 'Instance'},
    SoundEffect     = {'SoundEffect', 'Instance'},
    ReverbSoundEffect = {'ReverbSoundEffect', 'SoundEffect', 'Instance'},
    ParticleEmitter = {'ParticleEmitter', 'Instance'},
    PointLight      = {'PointLight', 'Light', 'Instance'},
    Fire            = {'Fire', 'Instance'},
    Highlight       = {'Highlight', 'Instance'},
    TextLabel       = {'TextLabel', 'GuiObject', 'GuiBase2d', 'Instance'},
    ScreenGui       = {'ScreenGui', 'LayerCollector', 'GuiBase2d', 'Instance'},
}

local function typeof(v)
    if type(v) == 'table' then return v.__typeof or 'Instance' end
    return type(v)
end

local function signal()
    local s = {__typeof = 'RBXScriptSignal', handlers = {}}
    function s:Connect(fn)
        self.handlers[#self.handlers+1] = fn
        local conn = {__typeof = 'RBXScriptConnection'}
        function conn:Disconnect() end
        return conn
    end
    return s
end

local function fire(s, ...)
    if s == nil then return 0 end
    for _, h in ipairs(s.handlers) do h(...) end
    return #s.handlers
end

local function vector(x, y, z)
    return {__typeof = 'Vector3', X = x, Y = y, Z = z}
end

local function mk(class, name, parent, extra)
    local t = {
        __isa = ANCESTRY[class] or {class, 'Instance'},
        __kids = {},
        __typeof = 'Instance',
        ClassName = class,
        Name = name,
        -- Every Instance has this in Roblox, and the watcher connects it on every
        -- root it watches.  Built into mk rather than passed per instance, because
        -- the first version of this fixture gave it to Workspace alone and the walk
        -- then died on a nil at the first root -- which is a fixture bug that would
        -- have looked exactly like a watcher bug.
        DescendantAdded = signal(),
    }
    for k, v in pairs(extra or {}) do t[k] = v end
    if parent then
        t.Parent = parent
        parent.__kids[#parent.__kids+1] = t
    end
    return setmetatable(t, {
        __index = function(self, k)
            -- --boom: the fixture makes one property read throw.  It has to be a
            -- property the instance does NOT already hold as a field, or __index
            -- never runs and the boom is never armed -- and it has to be one the
            -- watcher actually reads, or the throw lands nowhere.
            if rawget(self, '__boomOn') == k then
                error('fixture: property read was made to fail')
            end
            if k == 'IsA' then
                return function(s, c)
                    for _, n in ipairs(s.__isa) do if n == c then return true end end
                    return false
                end
            elseif k == 'GetChildren' then
                return function(s)
                    local out = {}
                    for i, c in ipairs(s.__kids) do out[i] = c end
                    return out
                end
            elseif k == 'GetDescendants' then
                return function(s)
                    local out = {}
                    local function walk(n)
                        for _, c in ipairs(n.__kids) do
                            out[#out+1] = c
                            walk(c)
                        end
                    end
                    walk(s)
                    return out
                end
            elseif k == 'FindFirstChild' then
                return function(s, n)
                    for _, c in ipairs(s.__kids) do if c.Name == n then return c end end
                    return nil
                end
            elseif k == 'FindFirstChildOfClass' then
                -- Exact class match, like Roblox's.  Only the window needs it, and it
                -- needs it on the LEVER: the detector is a child of the click part,
                -- which is the shape the recorder's own `CLICK StartUpLever` output
                -- proves.  See attachWindow in the watcher.
                return function(s, cls)
                    for _, c in ipairs(s.__kids) do if c.ClassName == cls then return c end end
                    return nil
                end
            elseif k == 'GetFullName' then
                return function(s)
                    local parts, cur = {}, s
                    while cur do
                        table.insert(parts, 1, cur.Name)
                        cur = cur.Parent
                    end
                    return table.concat(parts, '.')
                end
            elseif k == 'WaitForChild' then
                return function(s, n) return s:FindFirstChild(n) end
            elseif k == 'Destroy' then
                return function(s)
                    if s.Parent then
                        for i, c in ipairs(s.Parent.__kids) do
                            if c == s then table.remove(s.Parent.__kids, i) break end
                        end
                    end
                    s.Parent = nil
                end
            end
            return nil
        end,
    })
end

-- ========== THE SYNTHETIC TREE ==========
-- Modelled on what the recorder has already PROVED is there, plus one of every
-- shape the watcher has a branch for.  Nothing here is a guess about the original
-- game's layout; it is a fixture.
local workspace = mk('Instance', 'Workspace', nil, {
    GetServerTimeNow = function() return CLOCK end,
})

CLOCK = 1000
local function tick() CLOCK = CLOCK + 1 end

if BOOT then
    -- The very first thing the watcher's start-up does, made to fail.  A raw field
    -- so the metamethod is never consulted: this is the census's own call, and the
    -- fixture's generic GetChildren is what it would otherwise get.
    workspace.GetChildren = function()
        error('fixture: the census was made to fail')
    end
end

-- Consoles: the one path the recorder has actually clicked.
--
-- THE SHAPE OF THE LEVER IS THE ONE THING THE RECORDING WINDOW DEPENDS ON, and it is
-- modelled here as the recorder's own output proves it: `StartClickPart` is a PART
-- and the ClickDetector hangs off it.  The recorder prints `CLICK StartUpLever` only
-- when `labels[detector.Parent:GetFullName()]` hits, and that label was assigned to
-- `...StartUpBigLever.StartClickPart` -- so the detector's parent IS the part.  A flat
-- tree would have printed `path=Workspace.Consoles...` on every press instead.
-- The two ways the lever can be unreachable, and they are NOT the same repair -- so
-- they are two scenarios and not one flag.  `--nolever` keeps the part and drops the
-- ClickDetector: the path is right and the SHAPE is wrong, and window.txt has to name
-- the part it found so the reader can go and look at it.  `--nopath` removes the part,
-- so the path itself fails and the message is about the path.  A single "the lever is
-- gone" flag would collapse two different diagnoses into one and leave the other
-- branch of the miss unexercised -- which is precisely the branch whose wording the
-- operator would be reading at 3am.
local consoles = mk('Folder', 'Consoles', workspace)
local mrc = mk('Folder', 'MainReactorConsole', consoles)
local lever = mk('Folder', 'StartUpBigLever', mrc)
-- Written as an if and not as `NOPATH and nil or mk(...)`: that idiom returns the
-- mk() branch whenever the middle value is nil, which is exactly the case here, so the
-- one-line version would have built the part in the scenario whose whole point is that
-- it is absent -- and the suite would have gone green on a fixture that never tested it.
local startClick, startDet = nil, nil
if not NOPATH then
    startClick = mk('Part', 'StartClickPart', lever,
        {Anchored = true, Size = vector(2, 1, 0.4), CFrame = vector(0, 0, 0)})
    if not NOLEVER then
        startDet = mk('ClickDetector', 'ClickDetector', startClick,
            {MaxActivationDistance = 32, MouseClick = signal()})
    end
end
local shutClick = mk('Part', 'ShutClickPart', lever,
    {Anchored = true, Size = vector(2, 1, 0.4), CFrame = vector(0, 0, 2)})
local shutDet = mk('ClickDetector', 'ClickDetector', shutClick,
    {MaxActivationDistance = 32, MouseClick = signal()})
for i = 1, 20 do mk('Part', 'Panel' .. i, mrc, {CFrame = vector(i, 0, 0), Anchored = true,
    Size = vector(4, 1, 0.2), Color = 1000, Material = 'Metal'}) end
-- Two more parts, for two beats with nothing to do with the console: one destroyed
-- before the lever (see STEPS[2]) and two whose rings are still open when the run ends
-- (see STEPS[116]).
local preGone = mk('Part', 'PreLeverGone', workspace, {Anchored = true,
    Size = vector(1, 1, 1), CFrame = vector(3, 0, 0)})
local lateA = mk('Part', 'LateA', workspace, {Anchored = true, Transparency = 0,
    Size = vector(1, 1, 1), CFrame = vector(4, 0, 0)})
local lateB = mk('Part', 'LateB', workspace, {Anchored = true, Transparency = 0,
    Size = vector(1, 1, 1), CFrame = vector(5, 0, 0)})

-- Stats: the game's own bookkeeping, and the highest-yield class in the set.
local stats = mk('Folder', 'Stats', workspace)
local vActive = mk('BoolValue', 'GameActive', stats, {Value = false})
local vTemp = mk('NumberValue', 'Core.TemperatureVal', stats, {Value = 0})
local vGrav = mk('BoolValue', 'ChamberGravity', stats, {Value = false})
local vMelt = mk('BoolValue', 'MainframeMeltdown', stats, {Value = false})

-- A core with a light, an effect, and a part that will move.
local core = mk('Folder', 'Core', workspace)
local corePart = mk('Part', 'ReactorCore', core, {CFrame = vector(0, 10, 0), Anchored = true,
    Size = vector(8, 8, 8), Color = 200, Material = 'Metal', Transparency = 0})
local neon = mk('Part', 'NeonPart', core, {Color = 300, Material = 'Neon', Transparency = 0})
-- Named fireFx, not fire: a local called `fire` here would shadow the `fire()`
-- signal helper declared above for every closure defined below it, and the symptom
-- is `attempt to call upvalue 'fire' (a table value)` from inside a step.
local fireFx = mk('Fire', 'Fire', core, {Enabled = false, Size = 5, Heat = 1, Color = 0})
local light = mk('PointLight', 'PointLight', core, {Enabled = false, Brightness = 1, Range = 8})

-- A monitor with text on it, which is how the game talks.
local monitors = mk('Folder', 'Monitors', workspace)
local mon = mk('Folder', 'MainControlRoomMonitor', monitors)
local screen = mk('Folder', 'Screen', mon)
local ui = mk('Folder', 'MonitorUI', screen)
local title = mk('TextLabel', 'TitleText', ui, {Text = '', Visible = false})

-- The shift dial, at the exact path the recorder reads it from, and with the exact
-- format the recorder's own flow file shows it in (`q.timeText 11:50 PM` -- 12-hour,
-- zero-padded, one space).  Both scripts parse this with the same mapping on purpose.
-- 11:55 PM is 715, ten dial minutes after the lever and 725 short of the noon wrap
-- (1439 -> 0), which is the close rule, so the main scenario leaves
-- the window OPEN for the whole run and the closing path gets its own scenario.
local quota = mk('Folder', 'QuotaControlRoomMonitor', monitors)
local qScreen = mk('Folder', 'Screen', quota)
local qUi = mk('Folder', 'MonitorUI', qScreen)
local qMain = mk('Folder', 'MainMonitorFrame', qUi)
local qTime = mk('Folder', 'TimeFrame', qMain)
local clockLabel = mk('TextLabel', 'TimeLabel', qTime, {Text = '11:55 PM'})

-- Two roots with a repeated internal name, to force the path-suffix branch.
-- Roblox would not allow this; the fixture does, because uniquePath's collision
-- branch is otherwise unreachable and it is the branch that decides whether a log
-- line names the thing the operator should go and look at.
-- Position as well as CFrame: uniquePath prefers the world position as its
-- disambiguator, and Position is the property it actually reads.
local repA = mk('Folder', 'Repeated', workspace)
local repB = mk('Folder', 'Repeated', workspace)
mk('Part', 'Lamp', repA, {CFrame = vector(1, 1, 1), Position = vector(1, 1, 1),
    Anchored = true, Size = vector(1,1,1)})
mk('Part', 'Lamp', repB, {CFrame = vector(2, 2, 2), Position = vector(2, 2, 2),
    Anchored = true, Size = vector(1,1,1)})

-- Sounds inside the watched set.  `already` is Playing before the watcher loads,
-- which is the case no hook can ever report.
local soundsFolder = mk('Folder', 'Sounds', workspace)
local sAlready = mk('Sound', 'AmbientHum', soundsFolder, {
    Playing = true, Volume = 0.3, Pitch = 1, Looped = true,
    SoundId = 'rbxassetid://111', Played = signal(), Stopped = signal(), Ended = signal()})
local sAlarm = mk('Sound', 'Alarm', soundsFolder, {
    Playing = false, Volume = 0.8, Pitch = 1, Looped = false,
    SoundId = 'rbxassetid://222', Played = signal(), Stopped = signal(), Ended = signal()})

-- The giant: over PerRootBudget, so it must be SKIPPED and drilled into.  It also
-- holds the two audio edge cases, because a skipped root is the only place a Sound
-- can sit outside the property watch.
local facility = mk('Folder', 'Facility', workspace)
local fRoom = mk('Folder', 'MachineHall', facility)
for i = 1, 40000 do mk('Part', 'Pipe' .. i, fRoom, {Anchored = true, Size = vector(1,1,1)}) end
-- No Played signal at all, so the hook cannot attach and the poll is the only
-- thing that can see it.  `audioRefused` must count it.
local sBlind = mk('Sound', 'BlindBlip', facility, {
    Playing = false, Volume = 0.5, Pitch = 0.7, Looped = false, SoundId = 'rbxassetid://333'})
-- Preexisting, as in already playing from t=0, same as `already` but unwatched.
local sBed = mk('Sound', 'PlantFloorBed', facility, {
    Playing = true, Volume = 0.2, Pitch = 1, Looped = true,
    SoundId = 'rbxassetid://444', Played = signal(), Stopped = signal(), Ended = signal()})

-- A part that will be destroyed mid-run, to exercise the DESTROYED line.
local tempPart = mk('Part', 'Scaffold', core, {Anchored = true, Size = vector(2,2,2),
    CFrame = vector(5, 5, 5)})

-- ========== SERVICES ==========
local SINK = {}
-- The key of every accepted post, in arrival order, with the fixture clock at the
-- moment it was accepted.  The order is a claim the watcher makes and not a detail
-- of the fixture: hello.txt exists to be written BEFORE the census, so a harness
-- that only checked "it was written" would pass a watcher that wrote it last --
-- which is the same information the reader already had from tree.txt, and therefore
-- no answer to "was it even injected".
--
-- THE CLOCK IS THE OTHER HALF, and it is what makes "streamed" checkable at all.  A
-- watcher that held every change in memory and dumped them all in Report() would
-- satisfy every substring check in this file -- the same lines, in the same order,
-- in the same file -- while producing a log that says nothing about WHEN anything
-- happened, which is the entire product.  Arrival order cannot tell those apart; the
-- clock can, and it is captured here rather than reconstructed because the fixture
-- is the only thing that knows when a post was accepted.
local ORDER = {}
local postFail = false
local playerGui = mk('Instance', 'PlayerGui', nil)

local HttpService = {
    PostAsync = function(self, url, body)
        if postFail then error('sink is down (fixture)') end
        local path = string.gsub(url, '%?.*$', '')
        local key = string.match(path, '8765/(.+)$')
        if key == nil then error('fixture got an unexpected URL: ' .. url) end
        ORDER[#ORDER+1] = {key = key, clock = CLOCK}
        if string.find(url, 'mode=a', 1, true) then
            SINK[key] = (SINK[key] or '') .. body
        else
            SINK[key] = body
        end
    end,
}

local Players = {LocalPlayer = {WaitForChild = function(self, n) return playerGui end}}

local UIS = {InputBegan = signal()}

local soundGroup = mk('SoundGroup', 'SpecialSounds', nil, {Volume = 1})
local soundService = mk('Instance', 'SoundService', nil, {})
soundGroup.Parent = soundService
soundService.__kids[1] = soundGroup
sAlready.SoundGroup = soundGroup
sAlarm.SoundGroup = soundGroup
sBlind.SoundGroup = soundGroup
sBed.SoundGroup = soundGroup

local replicatedStorage = mk('Instance', 'ReplicatedStorage', nil, {})
-- A template in storage: it must be walked for SOUNDS and must NOT turn into a
-- watched key.  This is the assertion behind narrowing attachAudioOnly.
local template = mk('Part', 'PartTemplate', replicatedStorage, {Anchored = true, Size = vector(1,1,1)})

local SERVICES = {
    HttpService = HttpService,
    Players = Players,
    UserInputService = UIS,
    SoundService = soundService,
    ReplicatedStorage = replicatedStorage,
    ReplicatedFirst = mk('Instance', 'ReplicatedFirst', nil, {}),
    Workspace = workspace,
}

local game_ = {GetService = function(self, n)
    if SERVICES[n] == nil then error('fixture has no service ' .. n) end
    return SERVICES[n]
end}

-- ========== THE REST OF THE GLOBALS ==========
_G.game = game_
_G.workspace = workspace
_G.typeof = typeof
_G.warn = function(...) end   -- Roblox-only global; Lua 5.1 has no warn
_G.Enum = setmetatable({}, {__index = function() return setmetatable({}, {
    __index = function(_, k) return k end}) end})
_G.Color3 = {fromRGB = function(r, g, b) return {R = r, G = g, B = b} end}
_G.UDim2 = {new = function(...) return {} end}
_G.Vector3 = {new = function(x, y, z) return vector(x, y, z) end}
_G.Instance = {new = function(class) return mk(class, 'New' .. class, nil) end}

-- The loop driver.  The watcher's main loop lives in task.spawn and waits on the
-- clock, so the fixture advances time from INSIDE task.wait: the mutations run
-- between scans, which is the only way to drive a synchronous loop from outside
-- it.  HARNESS_STOP unwinds the loop without being treated as a crash.
--
-- ONLY TIMED WAITS ADVANCE THE SHIFT.  A bare task.wait() -- a long walk breaking
-- itself into slices so one census cannot freeze the client -- is not a step of the
-- timeline and is deliberately not counted.  It used to be, and that made this
-- fixture FLAKY: the sliced walks yield on a real clock, so how many bare waits fell
-- before STEPS[3] (the lever) depended on machine load, and the same unmodified
-- watcher passed and failed between runs.  A fixture whose verdict depends on how
-- fast the machine is cannot tell a broken watcher from a busy one.
--
-- The property this rests on -- that slicing changes WHEN the watcher works but not
-- WHAT it records -- is not asserted here; run_tests.sh measures it, by running the
-- shipped file against a copy with MaxBlockMs forced to 0 and requiring the two
-- change logs to agree line for line once the wall clock is stripped.
local STEPS = {}
local waits = 0
local bareWaits = 0
-- Past STEPS[60] with room for the quiet release and the final drain to settle.
local WAIT_LIMIT = 120
_G.task = {
    spawn = function(fn)
        local ok, err = pcall(fn)
        if not ok and tostring(err) ~= 'HARNESS_STOP' then
            error('the watcher raised inside task.spawn: ' .. tostring(err), 0)
        end
    end,
    wait = function(t)
        if t == nil then bareWaits = bareWaits + 1 return end
        waits = waits + 1
        tick()
        local step = STEPS[waits]
        if step then step() end
        if waits > WAIT_LIMIT then error('HARNESS_STOP', 0) end
    end,
}

-- ========== THE MUTATION TIMELINE ==========
-- Everything the watcher is supposed to notice, in the order a start-up would
-- produce it: discrete moves first, then the ones that keep going, then the ones
-- that are not properties at all.
STEPS[1] = function()
    -- A start-up beat: the levers, the stats, the light, the effect.  Note what is NOT
    -- here any more -- the game's own `GameActive` flag.  It goes true with the lever
    -- at STEPS[3] instead, because the whole point of the window is that the flag and
    -- the press are the same event, and the fixture would prove nothing about that if
    -- it flipped the flag three scans earlier than the click.
    if startDet then startDet.MaxActivationDistance = 40 end
    vTemp.Value = 510
    light.Enabled = true
    fireFx.Enabled = true
end

STEPS[2] = function()
    -- A DESTRUCTION BEFORE THE LEVER, and it is here for a check that would otherwise
    -- be vacuous.  Every other pre-lever beat below is a NUMBER change, and a number
    -- change goes into a hold ring -- so at the moment the window opens, `logLines`
    -- itself is empty in this fixture and "the pre-window lines were dropped" would
    -- have nothing in it to drop.  A destroyed instance is written straight into
    -- logLines with no ring, so this is the one beat that makes the DROP observable:
    -- with the drop removed, this line survives into the timeline stamped t=2, under
    -- an OPEN marker stamped t=3.
    preGone:Destroy()
    -- PRE-LEVER, AND THAT IS THE TEST.  These three land before the window opens, so
    -- they must be counted as withheld and must NOT be in changes.log -- while
    -- summary.txt, which is ungated, still carries both the title text and the
    -- temperature.  `QUICK BOOT UP INITIALIZED` is therefore a string that appears in
    -- one file and not the other, which is how the harness tells "withheld by the
    -- rule" from "never noticed".
    vTemp.Value = 3200
    corePart.Transparency = 0.3
    title.Text = 'QUICK BOOT UP INITIALIZED'
    title.Visible = true
end

STEPS[3] = function()
    -- A DescendantAdded the census could not have seen.  This is the ChamberGravity
    -- beat the recorder caught at t=83, and it is the single most valuable thing
    -- this watcher can produce, so the fixture must produce it too.
    local v = mk('BoolValue', 'CoolantLoopSealed', stats, {Value = false})
    fire(stats.DescendantAdded, v)
    v.Value = true
    -- THE OPERATOR THROWS THE LEVER, which is where the recording window opens.  The
    -- detector is fired rather than the part being poked, because a connection is the
    -- only thing the watcher takes and MouseClick is the signal it takes it on.
    -- In --nolever and --nopath this fires at nothing (no detector was ever built, so
    -- no handler was attached) and that is the point of those scenarios, not a defect
    -- in this one.
    if startDet then fire(startDet.MouseClick) end
    -- The game's own flag for the same event, and it flips at the same moment -- which
    -- is what makes it a legitimate fallback rather than a second guess.  Not set at
    -- all in --nowindow: that scenario is the one where NOTHING opens the window.
    if not NOWINDOW then vActive.Value = true end
end

STEPS[4] = function()
    -- A held key that stops: 3 moves, then quiet.  releaseQuiet must write these
    -- out once QuietScans have passed, and they must be IN changes.log.
    neon.Transparency = 0.5
    -- POST-LEVER, and deliberately so: `TitleText.Text` has to have a change inside
    -- the window as well as one outside it, or "a monitor line reached changes.log"
    -- would only be a check on the withheld half.
    title.Text = 'REACTOR ONLINE'
end
STEPS[5] = function() neon.Transparency = 1 end
STEPS[6] = function() neon.Transparency = 0 end

-- From here the noisy key moves on every single scan, forever.  It must overflow
-- the ring and land in suppressed.txt, and NOT in changes.log.
for i = 7, 60 do
    local n = i
    STEPS[n] = function() corePart.CFrame = vector(n, 10, 0) end
end

STEPS[10] = function()
    -- Audio: a play and an end, both long after attach.  The hooks must catch it.
    sAlarm.Playing = true
    fire(sAlarm.Played)
end
STEPS[11] = function()
    sAlarm.Playing = false
    fire(sAlarm.Ended)
end

STEPS[12] = function()
    -- The blind sound: no hooks, so only the poll can see it.  It must land in
    -- audio.txt as PLAYS-POLL-ONLY, and the poll must not repeat itself on the
    -- scans where it is still playing.
    sBlind.Playing = true
end

STEPS[20] = function()
    -- Destroyed mid-run.
    tempPart:Destroy()
end

STEPS[45] = function()
    -- A value whose tostring contains a newline.  CFrame is the realistic
    -- candidate -- twelve numbers, and Roblox formats it generously -- and the
    -- point is not to guess what tostring does to a CFrame but to make the guess
    -- unnecessary: fmt() must not let ANY value split a line, and this is a value
    -- that definitely would.
    vGrav.Value = setmetatable({}, {__tostring = function()
        return 'LINEA' .. NL .. 'INJECTED'
    end})
end

if BOOM then
    -- Overwrites a normal step.  This scenario needs the watcher alive just long
    -- enough to have written something first, so that "the timeline survived the
    -- death" is a real question and not an empty one.
    STEPS[5] = function() corePart.__boomOn = 'Reflectance' end
end

if NOWINDOW then
    -- THE OPERATOR STOPS THE RUN, because in this scenario nothing else can.  A window
    -- that never opened has no close rule to fire -- closeWindow correctly refuses a
    -- window that is not open -- so the run ends the way it would end in the game: the
    -- man at the console gives up and presses RightControl.  That is also the only way
    -- to reach the tail of the watcher's loop from inside this fixture at all, since
    -- the harness's own WAIT_LIMIT unwind raises out of task.wait and the code after
    -- the loop never runs -- which is why this scenario reported "changes.log was never
    -- written at all" until the stop key was wired in.
    STEPS[50] = function()
        fire(UIS.InputBegan, {KeyCode = Enum.KeyCode.RightControl}, false)
    end
end

if CLOSEWIN then
    -- The dial reaches 12:00 with the window open: the second half of the operator's
    -- rule, and the only action in this file that ENDS the run from inside it.  At
    -- step 9 rather than later so the close lands while the noisy loop is still moving
    -- -- a timeline with something on both sides of the boundary -- and the run has to
    -- stop by itself, which is what `waits` in the check below measures.
    --
    -- TWO STEPS, NOT ONE, because the rule being tested is a FALL and not a value.  The
    -- fixture's dial starts at 11:55 PM and only this scenario ever moves it, so a
    -- single assignment to '12:00 PM' would model the handover as a 715-minute drop
    -- from a dial that had never reached noon.  Going through 11:59 AM first makes it
    -- the real thing: 1439 -> 0, exactly the fall the game produces, with `prevClockMins`
    -- carrying 1439 across the step.
    STEPS[9]  = function() clockLabel.Text = '11:59 AM' end
    STEPS[14] = function() clockLabel.Text = '12:00 PM' end
end

-- WHY THESE TWO PAIRS EXIST, AND WHY THERE ARE TWO OF THEM.  There are two sorts in
-- the watcher -- releaseQuiet's `batch` and drainHeld's `pending` -- and a sort is
-- invisible unless ONE of those drains has more than one key's ring in it.  By the end
-- of this fixture every other key has gone quiet and been released on its own, so
-- without these beats both sorts are unobservable and their mutations come back
-- NOT DETECTED.  Each pair feeds a different sort, and that is the whole reason there
-- are two: the first attempt fed only the 116..119 pair and then reported the
-- releaseQuiet mutation as undetected, because lines still sitting in a ring at the
-- end of the run are drained by drainHeld, which the mutation never touched.
--
--   * 100..102 -- released by releaseQuiet on the SAME scan, so they land in one
--     batch.  A moves at 100 and 102, B at 101 and 102: the third beat sets BOTH, so
--     the two rings share a last move.  That sharing is load-bearing, and the first
--     attempt at this pair got it wrong -- A's last was 102 and B's 103, the test is
--     the STRICT `tick - last > 5` with QuietScans 5, so A released at 108 and B at
--     109 and the two lines went out in two separate batches, each already in order.
--     Equal last ticks release at 108 together.  The lines reach changes.log there,
--     mid-run, through the streaming flush.
--   * 116..119 -- still in their rings when the loop unwinds, so they are drained by
--     drainHeld when the harness calls Report().
--
-- IN BOTH PAIRS THE TICKS INTERLEAVE (A at 100 and 102, B at 101 and 102; A at 116
-- and 118, B at 117 and 119), which is what makes the difference show: two rings with
-- non-overlapping ticks come out in the right order under either arrangement, and the
-- mutation would pass by accident.
--
-- Both mutations (selftest_watch.py, `the held lines are appended without being
-- sorted` and `the end-of-run drain is appended without being sorted`) are checked
-- DIFFERENTIALLY, by comparing this file against the baseline, because there is no
-- absolute invariant to grep for here: a line released late legitimately carries an old
-- tick, so "changes.log is non-decreasing in t=" is not a property of the watcher and
-- asserting it would be asserting a fixture.
STEPS[100] = function() lateA.Transparency = 0.91 end
STEPS[101] = function() lateB.Transparency = 0.41 end
STEPS[102] = function()
    lateA.Transparency = 0.92
    lateB.Transparency = 0.42
end
STEPS[116] = function() lateA.Transparency = 0.93 end
STEPS[117] = function() lateB.Transparency = 0.43 end
STEPS[118] = function() lateA.Transparency = 0.94 end
STEPS[119] = function() lateB.Transparency = 0.44 end
STEPS[30] = function()
    -- The sink goes down and comes back: the queue must cap, count the drops, and
    -- then deliver everything after it.
    postFail = true
end
STEPS[40] = function() postFail = false end

-- ========== LOAD THE SHIPPED WATCHER ==========
-- By path, so there is no second copy of its logic to drift.
local chunk, loadErr = loadfile(WATCHER)
if chunk == nil then
    io.stderr:write('cannot load ' .. WATCHER .. ': ' .. tostring(loadErr) .. NL)
    os.exit(1)
end
local okRun, runErr = pcall(chunk)
if not okRun then
    if BOOT then
        -- --boot EXPECTS this when the guard is missing: the census throws inside
        -- task.spawn, which this fixture runs under pcall and re-raises, so it comes
        -- out here as a load error.  Swallowed rather than fatal, because the
        -- question -- "what reached the sink?" -- is answerable from SINK alone, and
        -- exiting would turn a missing artefact into a crashed harness, which is the
        -- exact confusion between "died" and "never ran" this scenario exists to
        -- remove.  `_G.TRG_ORIGINAL_WATCH` is published before Start is called, so
        -- the checks below still have a table to read.
        print('  note: the watcher raised while starting: ' .. tostring(runErr))
    else
        io.stderr:write('the watcher raised at load: ' .. tostring(runErr) .. NL)
        os.exit(1)
    end
end

local Watch = _G.TRG_ORIGINAL_WATCH
if Watch == nil then
    io.stderr:write('the watcher did not publish _G.TRG_ORIGINAL_WATCH' .. NL)
    os.exit(1)
end

-- THE RUN IS OVER AT THIS LINE, and it has to be read HERE rather than after the
-- Report() below.  Report() calls drainHeld(), which is the end-of-run dump path:
-- every post it makes carries the clock of the moment Report was called, so a
-- watcher that never streamed anything and only flushed on Report would have its
-- changes.log stamped the same as the baseline's LAST post and be indistinguishable
-- from it.  Taking the clock before Report is what makes "written during the run"
-- a claim this harness can actually check.
local endClock = CLOCK

-- The loop has run to WAIT_LIMIT and unwound.  Ask for the last files explicitly,
-- the same way an operator would press RightAlt.
local okRep, repErr = pcall(Watch.Report)
if not okRep then
    io.stderr:write('Report() raised: ' .. tostring(repErr) .. NL)
    os.exit(1)
end

-- ========== CHECKS ==========
local pass, fail = 0, 0
local function check(name, cond, detail)
    if cond then
        pass = pass + 1
        print(string.format('  ok   %s', name))
    else
        fail = fail + 1
        print(string.format('  FAIL %s%s', name, detail and ('  -- ' .. detail) or ''))
    end
end

local stamp
for k in pairs(SINK) do stamp = string.match(k, '^originalwatch/([^/]+)/') break end
local function get(name)
    if stamp == nil then return nil end
    return SINK['originalwatch/' .. stamp .. '/' .. name]
end

print('')
print('watch harness -- sink captured ' .. tostring(stamp))
print(string.format('  scans=%d  bare_waits=%d  status=%s', waits, bareWaits,
    tostring(Watch.Status()):sub(1, 110)))
print('')

local tree = get('tree.txt')
local rooms = get('rooms.txt')
local inv = get('inventory.txt')
local changes = get('changes.log')
local summary = get('summary.txt')
local supp = get('suppressed.txt')
local audio = get('audio.txt')
local tally = get('audio_tally.txt')
local errfile = get('error.txt')
local hello = get('hello.txt')

-- Where a given artifact landed in the arrival order, 1-based, or 0 if it never
-- arrived.  0 rather than nil so the comparisons below cannot error on a missing
-- file and turn "absent" into a crashed check.
local function arrival(name)
    for i, e in ipairs(ORDER) do
        if string.sub(e.key, -(#name + 1)) == '/' .. name then return i end
    end
    return 0
end

-- How many times a name was posted, and the fixture clock when it first was -- 0
-- posts reports first as nil.  This is the pair the streaming checks need: a file
-- written once at the very end of the run and a file written every scan look
-- identical to every substring check below, and `first < endClock` is the only
-- reading in this harness that separates "it was being written as the shift went on"
-- from "it was assembled afterwards".
local function writes(name)
    local n, first = 0, nil
    for _, e in ipairs(ORDER) do
        if string.sub(e.key, -(#name + 1)) == '/' .. name then
            n = n + 1
            if first == nil then first = e.clock end
        end
    end
    return n, first
end

-- The watcher's build tag, READ OUT OF THE SHIPPED FILE rather than typed here.
-- A typed copy would keep matching after the shipped tag moved, which is the exact
-- failure the tag exists to expose: a harness agreeing with itself about a string
-- neither the script nor the operator is using any more.  Fatal rather than skipped,
-- because a missing tag is not a check that becomes vacuous -- it is the check that
-- makes a stale copy visible going away, and that is the failure the operator has
-- already paid for once.
local CONFIG_BUILD = (function()
    local fh = io.open(WATCHER, 'r')
    if fh == nil then return nil end
    local src = fh:read('*a')
    fh:close()
    return string.match(src, "Build%s*=%s*'w(%d+)'")
end)()
if CONFIG_BUILD == nil then
    io.stderr:write('the shipped watcher has no Build tag (Build = w<digits>) --'
        .. ' refusing to run: the stale-copy check would have nothing to compare'
        .. ' against' .. NL)
    os.exit(1)
end

-- The start-up-death scenario.  The operator lost a whole shift to a watcher that
-- left nothing behind, and "left nothing behind" has three causes that are one
-- reading: never injected, died in the census, still censusing.  This makes the
-- census die on purpose and requires all three to separate -- hello.txt present
-- (so it WAS injected), error.txt present and naming the start-up (so it DIED, and
-- which walk), tree.txt absent (so "no tree" is not read as "no roots").
if BOOT then
    local booterr = get('error.txt')
    check('hello.txt WAS written even though the census threw', hello ~= nil)
    check('hello.txt arrived before the failure, not after it',
        arrival('hello.txt') > 0, 'hello.txt never reached the sink')
    check('tree.txt was NOT written, so a missing tree is not a missing world',
        get('tree.txt') == nil)
    check('error.txt WAS written when the census threw', booterr ~= nil)
    check('error.txt names the START-UP as the phase it died in',
        booterr and string.find(booterr, 'start-up', 1, true) ~= nil, booterr)
    check('the start-up error.txt is not the scan one',
        booterr and string.find(booterr, 'tick', 1, true) == nil, booterr)
    check('error.txt carries the census error itself',
        booterr and string.find(booterr, 'made to fail', 1, true) ~= nil, booterr)
    -- THE LEVER HOOK MUST NOT DEPEND ON THE CENSUS.  It did, and the price was a
    -- whole power-up: the census runs 48 s on the original place, the operator
    -- throws the lever at ~20 s, and a hook attached after the walk is a hook that
    -- takes a correct connection to a click that already happened -- which in the
    -- files reads exactly like a typo in LeverPath.  This scenario is the load-
    -- bearing witness because the census here THROWS, so a hook that survives it
    -- provably took before the walk rather than during it.  The handler count is
    -- the proxy: window.txt cannot be the witness in this scenario, because the
    -- loop that posts it is the thing the death prevents.
    check('the lever hook was taken even though the census threw',
        startDet ~= nil and #startDet.MouseClick.handlers == 1,
        startDet ~= nil and ('handlers=' .. #startDet.MouseClick.handlers)
            or 'no ClickDetector was built, so this scenario cannot judge')
    print('')
    print(string.format('watch(boot): %d PASS, %d FAIL', pass, fail))
    if fail > 0 then os.exit(1) end
    os.exit(0)
end

-- The self-report scenario.  A diagnostic that dies from its own bug is worse than
-- no diagnostic, and the failure is silent by construction: the loop lives in a
-- spawned thread, nothing awaits it, nothing catches it, and the only symptom is
-- that the files stop growing -- which looks exactly like a watcher running and
-- finding a still room.  So the error has to reach the sink, and this is the test
-- that it does.
if BOOM then
    check('error.txt WAS written when a property read threw', errfile ~= nil)
    check('error.txt names the tick it died on',
        errfile and string.find(errfile, 'tick', 1, true) ~= nil)
    check('error.txt carries the error itself',
        errfile and string.find(errfile, 'made to fail', 1, true) ~= nil)
    -- The two deaths share one filename, so the only thing keeping them apart is
    -- the first line.  Without this, rewording the start-up message to the scan
    -- message would make a boot death read as a scan death, and the reader would
    -- go looking for a timeline that was never written.
    check('error.txt does not claim the start-up phase',
        errfile and string.find(errfile, 'start-up', 1, true) == nil, errfile)
    check('the pre-death timeline survived',
        changes ~= nil and string.find(changes, 'GameActive.Value', 1, true) ~= nil)
    print('')
    print(string.format('watch(boom): %d PASS, %d FAIL', pass, fail))
    if fail > 0 then os.exit(1) end
    os.exit(0)
end

-- -------------------------------------------------------- the four window scenarios
local win = get('window.txt')

-- The detector is missing, so the lever is never hooked -- and the game's own flag
-- still flips.  This is the reading the reader is in when the timeline starts at the
-- right moment for the WRONG reason, and the two are only distinguishable from
-- window.txt.  `lever_hooked=false` plus `opened_by_fallback_flag=true` says the
-- boundary is the flag's edge, not the press -- which matters because the flag is the
-- game's bookkeeping and nobody has established that it flips on the press rather
-- than a second later.
if NOLEVER then
    check('the window opened even though the lever could not be resolved',
        win ~= nil and string.find(win, 'state=open', 1, true) ~= nil, win)
    check('window.txt says the FALLBACK opened it',
        win ~= nil and string.find(win, 'opened_by_fallback_flag=true', 1, true) ~= nil, win)
    check('window.txt says the lever hook did NOT take',
        win ~= nil and string.find(win, 'lever_hooked=false', 1, true) ~= nil, win)
    -- The reason has to be specific.  "not hooked" is a state; "resolves to Part
    -- StartClickPart, which carries no ClickDetector" is the repair.
    check('window.txt names the part the path resolved to',
        win ~= nil and string.find(win, 'Part StartClickPart', 1, true) ~= nil, win)
    check('the timeline reached the sink anyway',
        changes ~= nil and string.find(changes, 'recording begins', 1, true) ~= nil)
    local withheld = win and tonumber(string.match(win, 'withheld_before_open=(%d+)'))
    check('the pre-window lines were withheld and counted',
        withheld ~= nil and withheld > 0, win)
    print('')
    print(string.format('watch(nolever): %d PASS, %d FAIL', pass, fail))
    if fail > 0 then os.exit(1) end
    os.exit(0)
end

-- The part is not there at all.  Same fallback, different miss, and the difference is
-- the whole reason this scenario exists: the two failures are repaired in different
-- places -- "which instance is that path landing on" against "why is a path that was
-- right yesterday resolving to nothing" -- and a single message for both would send the
-- reader to fix the wrong one.  The path itself therefore has to be in window.txt;
-- there is nowhere else it is written down.
if NOPATH and not NOWINDOW then
    check('the window opened on the fallback with the lever gone',
        win ~= nil and string.find(win, 'state=open', 1, true) ~= nil, win)
    check('window.txt says the lever hook did NOT take',
        win ~= nil and string.find(win, 'lever_hooked=false', 1, true) ~= nil, win)
    check('window.txt names the PATH that did not resolve, not just that it failed',
        win ~= nil and string.find(win, 'StartUpBigLever.StartClickPart', 1, true) ~= nil, win)
    check('the miss names the path and not a part it never found',
        win ~= nil and string.find(win, 'does not resolve', 1, true) ~= nil
            and string.find(win, 'carries no ClickDetector', 1, true) == nil, win)
    local withheld = win and tonumber(string.match(win, 'withheld_before_open=(%d+)'))
    check('the pre-window lines were withheld and counted',
        withheld ~= nil and withheld > 0, win)
    print('')
    print(string.format('watch(nopath): %d PASS, %d FAIL', pass, fail))
    if fail > 0 then os.exit(1) end
    os.exit(0)
end

-- NOTHING opened the window: the lever cannot be resolved and the flag never flips.
-- The instruction was that recording starts at the lever, and a literal reading of
-- that would post an empty changes.log -- which is the same reading as "the watcher
-- was never injected", minus the one file that tells them apart.  The timeline is
-- written out under a marker instead, and this is the check that it is.
if NOWINDOW then
    check('the timeline reached the sink even though the window never opened',
        changes ~= nil, 'changes.log was never written at all')
    check('the timeline says the window never opened',
        changes ~= nil and string.find(changes, 'NO WINDOW', 1, true) ~= nil, changes)
    check('and the pre-lever lines are IN it, not dropped',
        changes ~= nil and string.find(changes, 'QUICK BOOT UP INITIALIZED', 1, true) ~= nil,
        changes)
    check('window.txt reports the window as closed, not as still waiting',
        win ~= nil and string.find(win, 'state=closed', 1, true) ~= nil, win)
    check('window.txt says why it closed',
        win ~= nil and string.find(win, 'never opened', 1, true) ~= nil, win)
    check('window.txt records that neither the lever nor the flag opened it',
        win ~= nil and string.find(win, 'lever_hooked=false', 1, true) ~= nil
            and string.find(win, 'opened_by_fallback_flag=false', 1, true) ~= nil, win)
    print('')
    print(string.format('watch(nowindow): %d PASS, %d FAIL', pass, fail))
    if fail > 0 then os.exit(1) end
    os.exit(0)
end

-- The dial reaches 12:00 with the window open.  This is the half of the rule that
-- ENDS the run, and the thing to pin is that it ends without being told to: `waits`
-- is how many task.wait calls the loop made before it returned, and a run that needed
-- the harness's own WAIT_LIMIT unwind would report 120 here.  The second claim is
-- that nothing landed in the timeline after the boundary -- the drains at exit still
-- run, and every line they release has to be a line that happened BEFORE the close.
if CLOSEWIN then
    check('the run ended by itself when the dial reached 12:00', waits < 30,
        string.format('the loop made %d task.wait calls', waits))
    check('window.txt reports the window closed',
        win ~= nil and string.find(win, 'state=closed', 1, true) ~= nil, win)
    check('window.txt says WHEN it closed, not just that it did',
        win ~= nil and not string.find(win, 'closed_at=not yet', 1, true), win)
    check('window.txt names the dial as what closed it',
        win ~= nil and string.find(win, '12:00 PM', 1, true) ~= nil, win)
    -- The latch has to carry the reading the dial fell FROM, not the one it fell to.
    -- 1439 is 11:59 AM; the closing reading is 0.  A rule that stored the wrong end of
    -- the fall would still close here -- `0 < 0` is false, so it would in fact close
    -- on nothing at all -- and this is the only check that tells the two apart.
    check('the latch holds the PRE-fall reading',
        win ~= nil and string.find(win, 'wrap_latched_from=1439', 1, true) ~= nil, win)
    check('the timeline carries the CLOSE marker',
        changes ~= nil and string.find(changes, 'recording ends', 1, true) ~= nil, changes)
    -- The boundary has to be a boundary.  Lines may still follow it -- the drains at
    -- exit release whatever rings were still moving -- but every one of them carries a
    -- t= EARLIER than the close, because they are evidence from before the boundary
    -- that was written late rather than recording that continued past it.
    local closeAt, late = nil, nil
    if changes then
        for ln in string.gmatch(changes, '[^\n]+') do
            local tt = tonumber(string.match(ln, '^t=([0-9.]+)'))
            if string.find(ln, '| CLOSE', 1, true) then
                closeAt = tt
            elseif closeAt and tt and tt > closeAt then
                late = ln
            end
        end
    end
    check('nothing was RECORDED after the close', late == nil,
        tostring(late))
    -- A control that has to survive this scenario whatever happens to the close rule.
    -- The check above goes green VACUOUSLY when there is no CLOSE marker to compare
    -- against, so a mutation that kills the rule outright would leave nothing in this
    -- block standing -- and a mutation whose every witness is vacuous proves nothing.
    check('the closewin run still produced a timeline',
        changes ~= nil and string.find(changes, 'recording begins', 1, true) ~= nil, changes)
    print('')
    print(string.format('watch(closewin): %d PASS, %d FAIL', pass, fail))
    if fail > 0 then os.exit(1) end
    os.exit(0)
end

-- The boot line, in the run where nothing goes wrong.  It is the reader's answer
-- to "was it even injected", so WHERE it lands is the whole of its value: a
-- hello.txt written after the census carries no information the tree does not.
-- `ORDER[1]` cannot be interpolated directly any more: an entry is a table now, and
-- concatenating it would raise inside the FAILURE path -- so a check that went red
-- would crash the harness instead of reporting, which is the one place in this file
-- where being wrong is invisible (the run just stops with no FAIL line).
local firstArrival = ORDER[1] and ORDER[1].key or '(nothing arrived)'
local alive = get('alive.txt')

-- THE BEACON IS FIRST, AND THAT IS THE WHOLE OF ITS VALUE.  hello.txt is posted
-- from inside Start, so it answers "was this injected" only for a file that got as
-- far as Start: a load-time death sends nothing and reads exactly like a script that
-- was never injected -- one reading, two causes, on a shift the operator gets once.
-- alive.txt is posted at load, before the module body below it, so the two separate.
-- Hence the FIRST-arrival check moved to alive.txt and hello.txt's own claim is now
-- the weaker one it can actually support: it came second, before the census.
check('alive.txt was written', alive ~= nil)
check('alive.txt was the FIRST thing at the sink',
    arrival('alive.txt') == 1, firstArrival)
check('alive.txt arrived before hello.txt, so it brackets the load',
    arrival('alive.txt') > 0 and arrival('alive.txt') < arrival('hello.txt'),
    firstArrival)
check('alive.txt carries the build tag, so a stale copy is visible as stale',
    alive ~= nil and string.find(alive, 'build=w' .. CONFIG_BUILD, 1, true) ~= nil, alive)
check('alive.txt names the transport that was actually picked',
    alive ~= nil and string.find(alive, 'transport=', 1, true) ~= nil, alive)
check('alive.txt names its own prefix, so a stray copy is traceable',
    alive ~= nil and stamp ~= nil
        and string.find(alive, 'originalwatch/' .. stamp, 1, true) ~= nil)

check('hello.txt was written', hello ~= nil)
check('hello.txt arrived before tree.txt',
    arrival('hello.txt') > 0 and arrival('hello.txt') < arrival('tree.txt'),
    firstArrival)
check('hello.txt names its own prefix, so a stray copy is traceable',
    hello ~= nil and stamp ~= nil
        and string.find(hello, 'originalwatch/' .. stamp, 1, true) ~= nil)
check('hello.txt names the transport too, not only the sink',
    hello ~= nil and string.find(hello, 'transport=', 1, true) ~= nil, hello)

check('tree.txt was written', tree ~= nil)
check('rooms.txt was written', rooms ~= nil)
check('inventory.txt was written', inv ~= nil)
check('changes.log was written', changes ~= nil)

-- ------------------------------------------------- streamed, or dumped? ---------
-- Every other check in this file reads the FINAL body of a file, and a body cannot
-- tell a log that was written while the shift went on from one assembled at the end
-- -- same lines, same order, same file.  That distinction is the product: the
-- operator's complaint that started this work was 「你不写入开机流程你怎么知道？」
-- and a timeline that arrives after the run has no timestamps in it worth having.
-- So it is asserted two ways, both from the arrival clock rather than from the text:
-- changes.log was already being posted BEFORE the run ended, and it was posted more
-- than once, which a single flush cannot be.
local nLog, firstLog = writes('changes.log')
check('changes.log was written to while the run was still going',
    nLog > 0 and firstLog ~= nil and firstLog < endClock,
    string.format('posts=%d first=%s end=%s', nLog, tostring(firstLog), tostring(endClock)))
check('changes.log was appended to more than once, not assembled at the end',
    nLog > 1, string.format('posts=%d', nLog))
-- audio.txt gets the same treatment and for a stronger reason: a playback event held
-- until the end would be written out of order against changes.log, and the audio
-- track is the one artifact where the ORDER is the finding.
local nAudio, firstAudio = writes('audio.txt')
check('audio.txt was streamed rather than held to the end',
    nAudio > 0 and firstAudio ~= nil and firstAudio < endClock,
    string.format('posts=%d first=%s end=%s', nAudio, tostring(firstAudio), tostring(endClock)))
check('summary.txt was written', summary ~= nil)
check('suppressed.txt was written', supp ~= nil)
check('audio.txt was written', audio ~= nil)
check('audio_tally.txt was written', tally ~= nil)
check('error.txt was NOT written', errfile == nil, errfile)

-- The census: the giant must be skipped WITH A REASON, and drilled into.
check('census counted the giant', tree and string.find(tree, 'Facility', 1, true) ~= nil)
check('census names the skip reason',
    tree and string.find(tree, 'over PerRootBudget', 1, true) ~= nil)
check('census drilled into the skipped root',
    tree and string.find(tree, 'MachineHall', 1, true) ~= nil)
check('the giant is absent from the watch',
    rooms and string.find(rooms, 'roots NOT watched', 1, true) ~= nil)
check('the smaller roots were taken',
    rooms and string.find(rooms, '## Consoles', 1, true) ~= nil
        and string.find(rooms, '## Stats', 1, true) ~= nil)
-- The pin is a claim about the RUN, not about the fixture, and a root that went
-- unwatched because the budget ran out looks exactly like a root that is not
-- there.  So rooms.txt has to SAY on its face that the pin was read.  What the
-- pin then BUYS -- exemption from the two ceilings -- is checked by mutation
-- instead, against the giant that is already in this fixture: a purpose-built
-- root over PerRootBudget would cost the suite 30,001 mock instances to prove
-- what Pinned = {'Facility'} proves for nothing.
check('rooms.txt names the root pinned by name',
    rooms and string.find(rooms, '# pinned by name: Alarms', 1, true) ~= nil,
    rooms)

-- The collision branch, which is otherwise unreachable.
check('a duplicate GetFullName got a path suffix',
    inv and string.find(inv, 'Repeated.Lamp ~', 1, true) ~= nil,
    inv and (string.find(inv, 'Repeated.Lamp', 1, true) and 'no suffix' or 'Lamp not registered'))

-- The property watch.
check('the click detector is watched', inv and string.find(inv, 'MaxActivationDistance', 1, true) ~= nil)
check('the stats values are watched', inv and string.find(inv, 'GameActive', 1, true) ~= nil)
check('the text label is watched', inv and string.find(inv, 'TitleText', 1, true) ~= nil)
check('the fire is watched', inv and string.find(inv, 'Core.Fire', 1, true) ~= nil)
check('the sound group is watched as a bus',
    inv and string.find(inv, 'SpecialSounds', 1, true) ~= nil)
-- The narrowing that makes it safe to walk ReplicatedStorage at all.  If this
-- fails, walking storage for sounds has quietly turned every template in it into
-- a watched key, which is the whole reason attachAudioOnly tests for SoundGroup
-- and SoundEffect instead of for "anything propsFor knows".
check('a template in ReplicatedStorage did NOT become a watched key',
    inv ~= nil and string.find(inv, 'PartTemplate', 1, true) == nil)

-- The discrete key: 3 moves, then quiet, then RELEASED into the log.
check('the discrete key reached changes.log', changes and string.find(changes, 'NeonPart.Transparency', 1, true) ~= nil)
check('changes.log carries the values as well as the name',
    changes and string.find(changes, 'NeonPart.Transparency | 0 | 0.5', 1, true) ~= nil)
check('the stats flip reached changes.log', changes and string.find(changes, 'GameActive.Value', 1, true) ~= nil)
check('a monitor line reached changes.log', changes and string.find(changes, 'TitleText.Text', 1, true) ~= nil)

-- ------------------------------------------------- the recording window --------
-- 「我进控制室之后，按下开机拉杆开始记录，游戏时间到12：00结束记录」.  The dial is at
-- 11:55 PM in this scenario, so the window opens at the lever and never closes, and
-- what is pinned here is the OPENING half: that the LEVER is what opened it (not the
-- fallback, which is a different boundary and a different reading), and that the
-- pre-lever timeline was withheld AND COUNTED -- because a timeline that starts late
-- and a timeline whose first half was dropped look identical from changes.log alone.
-- The closing half has its own scenario (--closewin).
check('the lever opened the recording window',
    win ~= nil and string.find(win, 'state=open', 1, true) ~= nil, win)
check('window.txt says the lever hook took',
    win ~= nil and string.find(win, 'lever_hooked=true', 1, true) ~= nil, win)
check('window.txt says the FALLBACK did not open it',
    win ~= nil and string.find(win, 'opened_by_fallback_flag=false', 1, true) ~= nil, win)
check('window.txt names the lever as the opener',
    win ~= nil and string.find(win, 'the start-up lever was clicked', 1, true) ~= nil, win)
local withheld = win and tonumber(string.match(win, 'withheld_before_open=(%d+)'))
check('the pre-lever lines were withheld and counted',
    withheld ~= nil and withheld > 0, win)
-- ...and nothing stamped before the marker got in, which is the invariant underneath
-- the whole rule rather than one string that happens to witness it.  The first
-- version of this check searched for the pre-lever VALUE and was wrong twice over:
-- the move AFTER the window quotes the pre-window value as its `from`, so
-- `QUICK BOOT UP INITIALIZED` sits in the timeline as context on a line that is
-- legitimately recorded, and the check went red on a file that was correct in every
-- respect it meant to test.  Comparing stamps cannot make that mistake, and it covers
-- every pre-lever line instead of the one this fixture happens to move.
local openT = nil
if changes then
    for line in string.gmatch(changes, '[^' .. NL .. ']+') do
        if string.find(line, '| OPEN |', 1, true) then
            openT = tonumber(string.match(line, '^t=(%d+%.%d+)'))
            break
        end
    end
end
local earlyLine = nil
if changes and openT then
    for line in string.gmatch(changes, '[^' .. NL .. ']+') do
        local t = tonumber(string.match(line, '^t=(%d+%.%d+)'))
        if t ~= nil and t < openT then earlyLine = line break end
    end
end
check('no recorded line is stamped before the OPEN marker',
    openT ~= nil and earlyLine == nil,
    earlyLine or ('the OPEN marker was never found (openT=' .. tostring(openT) .. ')'))
-- ...and they are not LOST either.  This is the pair that makes the withholding a
-- decision rather than a hole: the ungated state files still describe the pre-lever
-- room, so "nothing happened before the lever" and "a lot happened and was withheld"
-- stay two readings.  summary.txt is written from the change cursor, not from the
-- window, which is exactly why it can answer this.
check('the ungated state file still names what moved before the lever',
    summary ~= nil and string.find(summary, 'TitleText.Text', 1, true) ~= nil, summary)
check('the timeline marks where it starts meaning',
    changes ~= nil and string.find(changes, 'recording begins', 1, true) ~= nil, changes)
check('the dial was read off the real label, not a guess',
    win ~= nil and string.find(win, '11:55 PM', 1, true) ~= nil, win)

-- WHEN it was released, not just that it was.  Watch.Report() calls drainHeld()
-- every ReportEvery scans, which writes out ANY ring still held -- so "the line is
-- in changes.log" is satisfied even if the quiet-release rule never fires once.
-- The two are told apart by the counter in suppressed.txt, which counts the keys
-- released on quiet and not also ambient.  Without this, releaseQuiet() could be
-- deleted outright and every other check here would stay green.
check('suppressed.txt counts the keys released on quiet',
    supp and string.match(supp, '# (%d+) key%(s%) judged discrete') ~= nil
        and tonumber(string.match(supp, '# (%d+) key%(s%) judged discrete')) > 0)

-- The DescendantAdded beat, which is the point of the whole exercise.
local addedOk = false
if changes then
    for line in string.gmatch(changes, '[^' .. NL .. ']+') do
        if string.find(line, 'CoolantLoopSealed', 1, true) then addedOk = true end
    end
end
check('a ValueBase ADDED mid-run is watched', addedOk)

-- The noisy key: held, overflowed, and disclosed rather than silently dropped.
check('the noisy key was judged ambient', supp and string.find(supp, 'ReactorCore.CFrame', 1, true) ~= nil)
check('suppressed.txt states the rule that judged it',
    supp and string.find(supp, 'judged ambient', 1, true) ~= nil)
check('the noisy key was counted, not erased',
    supp and string.find(supp, 'change(s) by t=', 1, true) ~= nil)
check('the ambient key kept its change count in summary.txt',
    summary and string.find(summary, 'ReactorCore.CFrame', 1, true) ~= nil)

-- The destroyed instance.
check('a destroyed instance is reported', changes and string.find(changes, 'DESTROYED', 1, true) ~= nil)

-- Line integrity.  A newline inside a formatted value must not become a line
-- break, or changes.log gains fragments that read as separate malformed events --
-- and the value that arrives in the log would no longer be the value that was
-- read.  Asserted on the FRAGMENT, not on the whole value: with the guard in place
-- the text is still present, just on one line, so searching for the value proves
-- nothing.  What must not exist is a line that STARTS with the second half.
check('a newline inside a value did not split the log line',
    changes ~= nil and string.find(changes, NL .. 'INJECTED', 1, true) == nil)
check('that value still reached the log, on one line',
    changes ~= nil and string.find(changes, 'LINEA INJECTED', 1, true) ~= nil)

-- Audio.
--
-- READ OFF THE INSTANCE, and now read off the TALLY.  The line this used to look for
-- in audio.txt is written during the boot walk -- a sound already playing when the
-- watcher attaches is read from the Sound, since no hook can see a Played that
-- happened before it -- so it is a t=0 line, and the window opens at the lever.  It
-- is therefore withheld from audio.txt like every other pre-lever line, and the file
-- that still answers the question is the ungated tally.  Same reasoning as
-- summary.txt on the property side: the baseline is not lost, it is just not part of
-- the recording.  Looking for it in audio.txt would now be a check that passes only
-- if the window is broken.
check('ALREADY-PLAYING was read off the instance',
    tally and string.find(tally, '[ALREADY PLAYING AT t=0]', 1, true) ~= nil, tally)
check('the pre-window audio was withheld and counted, not lost',
    win and tonumber(string.match(win, 'plus (%d+) audio line')) ~= nil
        and tonumber(string.match(win, 'plus (%d+) audio line')) > 0
        and audio ~= nil and string.find(audio, 'ALREADY-PLAYING', 1, true) == nil, win)
check('a hooked play was caught', audio and string.find(audio, 'PLAYED', 1, true) ~= nil)
check('a hooked end was caught', audio and string.find(audio, 'ENDED', 1, true) ~= nil)
check('an unhookable sound was caught by the poll',
    audio and string.find(audio, 'PLAYS-POLL-ONLY', 1, true) ~= nil)
check('the poll did not repeat itself while it stayed playing',
    audio and select(2, string.gsub(audio or '', 'PLAYS%-POLL%-ONLY', '')) == 1)
check('the refused hook was counted', tally and string.find(tally, 'refused', 1, true) ~= nil)
check('the tally reports audible-by-bus', tally and string.find(tally, 'audible by bus', 1, true) ~= nil)
check('a preexisting sound is counted even with zero events',
    tally and string.find(tally, 'ALREADY PLAYING AT t=0', 1, true) ~= nil)

-- The queue cap, which must count what it drops rather than lose it in silence.
check('a sink outage did not kill the watcher', errfile == nil and summary ~= nil)

-- ------------------------------------------------- health.txt -------------------
-- The file that replaced the on-screen panel and every print.  Its claims are
-- checkable, and the third one is the point of the whole file: the fixture makes
-- the sink refuse everything between two ticks and take it again afterwards, and a
-- health.txt that only had a DOWN/ok flag would read `sink=ok` and
-- `sink_error=none` at the end -- having never written the outage down anywhere,
-- because the only file that could carry it has to travel through the sink that is
-- down.  So the outage is asserted as a HISTORY: it happened once, it cost time,
-- and the fixture's own error text is still in the file after the sink came back.
local health = get('health.txt')
check('health.txt was written', health ~= nil)
check('health.txt says when it was written, so a stale copy is visible as stale',
    health ~= nil and string.find(health, 't=', 1, true) ~= nil
        and string.find(health, 'tick=', 1, true) ~= nil)
check('health.txt names the sink it is writing to',
    health ~= nil and string.find(health, 'sink=', 1, true) ~= nil)
check('health.txt records the outage that is over by the time it is read',
    health ~= nil and string.find(health, 'sink_outages=1', 1, true) ~= nil,
    health and string.match(health, 'sink_outages=[^\n]*') or 'no health.txt')
check('health.txt still carries the reason the sink refused',
    health ~= nil and string.find(health, 'sink is down (fixture)', 1, true) ~= nil)
check('health.txt reports the final state as recovered, not as down',
    health ~= nil and string.find(health, 'sink=ok', 1, true) ~= nil,
    health and string.match(health, 'sink=[^\n]*') or 'no health.txt')

-- THE HOTKEY MUST NOT COLLIDE WITH THE RECORDER'S SEAL KEY.
--
-- This reads the SOURCE rather than exercising the watcher, and it is the one
-- check here that is about a different file -- both are deliberate.  The collision
-- it guards against cannot be observed from inside this harness at all: nothing
-- happens until a human presses the key, and what happens then is that the OTHER
-- script ends its run.  TRG_original_recorder.luau binds RightShift to seal, and
-- both scripts are injected into the same session on an attempt the operator can
-- only spend once -- so a shared key turns "flush the watcher now" into "discard
-- the recording".  It was in the shipped file until this check was written.
check('the watcher does not steal the recorder\'s seal key',
    (function()
        local fh = io.open(WATCHER, 'r')
        if not fh then return false end
        local src = fh:read('*a')
        fh:close()
        return string.find(src, 'KeyCode%.RightShift') == nil
    end)())

print('')
print(string.format('watch: %d PASS, %d FAIL', pass, fail))

-- The substrings above prove the files contain the RIGHT WORDS.  That is not the
-- same as the files being right, and this is a watcher whose whole product is text
-- nobody has read yet, so --dump writes the captured sink out for a human.  Off by
-- default because a test that litters is a test people stop running.
if DUMP then
    -- Tested DUMP, not arg[1], and the difference is not cosmetic: with a path
    -- argument the old `arg[1] == '--dump'` was false, so every `lua
    -- watch_harness.luau <mutant> --dump` silently dumped NOTHING and the empty
    -- directory read as "the mutant produces no output" rather than "the flag was
    -- ignored".  Caught while trying to diff a mutant's artifacts against the
    -- baseline -- the diff tool reported every file as different because one side
    -- did not exist.
    local dir = DUMPDIR
    -- cmd.exe, not bash: this lua.exe is a native Windows binary, so a POSIX
    -- redirect here is a syntax error that kills the whole mkdir rather than
    -- redirecting its output.
    os.execute('mkdir "' .. dir .. '"')
    local n = 0
    for k, body in pairs(SINK) do
        local name = string.match(k, '/([^/]+)$')
        local fh = io.open(dir .. '/' .. name, 'w')
        if fh then
            fh:write(body)
            fh:close()
            n = n + 1
        end
    end
    print(string.format('dumped %d file(s) to %s', n, dir))
end

if fail > 0 then os.exit(1) end
