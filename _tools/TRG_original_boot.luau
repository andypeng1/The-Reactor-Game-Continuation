-- ============================================================================
-- TRG ORIGINAL -- THE START-UP SCREEN RECORDER   (build b3)
-- ============================================================================
-- WHAT THIS IS.  It replaces the operator's own recorder, the one that produced
-- Data/auxcollection/startup/ScreenChanges.txt -- 179,788,590 bytes, 1,162,737
-- lines, one 158 s window.  His script is a 4.9 KB file kept outside this repo;
-- this file keeps its ONE good idea (the line format below, which every reader
-- under _tools/_attic/scratch/aux_*.py already parses) and removes the four
-- things that made that capture cost a shift and answer almost nothing.
--
-- THE FORMAT IS UNCHANGED, AND THAT IS A FEATURE, NOT LAZINESS:
--
--     Time:[HH:MM:SS]<-O:[Workspace.Monitors.X.Screen.MonitorUI.Y]<-C:[Prop]<-V:[value]
--
-- Every aux_*.py compiles that whole shape as ONE regular expression, with every
-- square bracket escaped and a trailing dollar anchoring the end of the line --
-- so APPENDING A FIELD TO A LINE SILENTLY CORRUPTS IT: the
-- greedy (.*) would swallow the added text into the value.  A reader that used
-- to be right would start being wrong, with no error anywhere.  So the shape is
-- frozen, and everything this file adds is either a NEW LINE (never a longer
-- one) or a NEW FILE beside the log.  Comment lines start with # and no reader
-- matches them.
--
-- ---------------------------------------------------------------------------
-- WHAT WAS WRONG WITH THE CAPTURE, MEASURED (PROGRESS.md Phase 66)
-- ---------------------------------------------------------------------------
-- 1. 99.4% OF THE VOLUME IS ONE DECORATION.  The operator watched a fixed
--    property list per ClassName, and that list carries Position, Rotation and
--    Size for every Frame and ImageLabel in the monitor tree.  The monitors
--    contain a GlitchEffect with a GlitchFrame under it that jitters its own
--    Position and Size continuously -- so the file is overwhelmingly
--    GlitchFrame, and the thing the run was FOR (the boot screen revealing
--    itself) is the 0.2% underneath.  The head of that file is GlitchFrame
--    lines, and so is the tail.
--
--    Fixed by GeometrySkip: an instance whose path contains one of these
--    fragments is still watched for Visible / Text / the transparency and
--    colour family -- what a decoration can actually do that you might care
--    about -- but its Position / Size / Rotation are never hooked at all.
--
-- 2. THERE WAS NO RATE, ONLY EVENTS.  GetPropertyChangedSignal on Position fires
--    sixty times a second for a jittering frame.  Fixed by Coalescing: a change
--    only marks the key dirty, and a 4 Hz tick writes the CURRENT value at most
--    once per key.  A 60 Hz jitter now costs 4 lines a second instead of 60, and
--    a value that changes and changes back between two ticks costs nothing --
--    the right answer for a decoration, and the one thing an event-driven
--    recorder cannot say.
--    THE PRICE IS STATED HERE, NOT HIDDEN: the tick is the resolution, so a
--    change that reverts inside one tick is not recorded.  At 0.25 s that is
--    under the frame time of anything on this screen; the boot reveals are
--    seconds long.
--
-- 3. THE FILE HAD NO CEILING AND NEVER ENDED.  appendfile to a fixed path, a
--    stop rule that only fires at noon, and no bound at all: 1.14 MB per second,
--    and a second run would have appended to the first run's file.  Fixed by a
--    per-key write budget with a suppression LEDGER (a key that crosses it is
--    named in suppressed.txt and stops, rather than quietly eating the file), a
--    byte ceiling that seals the run and records why, and a run-stamped output
--    path so two runs cannot become one file.
--
-- 4. NOTHING OUTSIDE THE ORIGINAL DESCENDANT SET WAS EVER SEEN.  The connections
--    were built once, from GetDescendants at start.  Phase 66 and 67 both ran
--    into the consequence: rows for instances created DURING the run -- the
--    start-up steps' runtime clones -- are not in the capture at all, and a
--    monitor that reads a fixed descendant set cannot see them.  Fixed by
--    DescendantAdded, which registers new instances as they appear.
--
-- 5. REGISTERING A NEW INSTANCE IS NOT THE SAME AS SEEING IT.  Measured by the
--    first real run (PROGRESS.md Phase 71): the log panel builds each message by
--    cloning a frame, writing the text, and only THEN parenting it -- so the
--    instance first became visible to this file with its message already in
--    place, registration seeded that value as the baseline, and no later change
--    ever differed from it.  5156 lines carried the panel's fades and not one
--    character of the panel's text, which is the boot's own narration.  Fixed by
--    a BIRTH RECORD: an instance registered after t0 has its watched values
--    written as lines instead of only seeded.  See register().
--
-- 6. AND REGISTERING IT ONCE IS NOT THE SAME AS WATCHING THE PATH.  Measured by
--    the second real run (PROGRESS.md Phase 72): a key is a PATH, and the gate was
--    'have I ever seen this path'.  The log panel clones a FRESH row per message
--    onto three fixed names, so from the second message onwards the path was
--    already known, the new instance was skipped whole, and the connection that
--    stayed registered was aimed at a row the panel had since destroyed.  The
--    capture kept 3 messages out of a 428 s shift; the r60 recorder's capture of
--    the SAME shift holds 35 distinct ones, START-UP COMPLETED among them.  Fixed
--    by re-pointing the key at whatever occupies the path now.  See register()'s
--    second branch -- and note that the harness's clone test cloned a NEW path,
--    which is why it stayed green through this.
--
-- AND ONE THING THAT IS NOT A DEFECT BUT A COST: the product used to land in the
-- executor's own TRG/ folder, which is why getting the last one into this repo
-- was a 180 MB manual copy.  This file POSTs to the same localhost sink the
-- recorder and the watcher already use, so the bytes land in Data/ and never
-- travel through anyone's context.
--
-- ---------------------------------------------------------------------------
-- WHAT IT STILL DOES NOT DO
-- ---------------------------------------------------------------------------
-- It writes nothing about the reactor, the controls or the world: the scope is
-- Workspace.Monitors, exactly the operator's, because the question is what the
-- SCREENS did during the start-up.  TRG_original_recorder owns everything else.
-- It also does not press anything -- it waits for the operator to press the boot
-- button, because that press is the t=0 the whole capture is indexed from
-- (PROGRESS.md Phase 67), and the same press his own hook used.
--
-- ON BACKSLASHES: there are none in this file, on purpose (CLAUDE.md 0.10 -- text
-- written through the Studio edit tools is decoded once, so a two-character
-- backslash-n becomes a real newline and turns legal Lua into a syntax error).
-- Newlines are string.char(10) and every embedded string is single-quoted.
--
-- HOW IT IS RUN.  Both servers up (double-click start_services.bat), then in the
-- executor BEFORE pressing the boot button:
--
--   loadstring(game:HttpGet('http://127.0.0.1:8766/TRG_original_boot.luau'))()
--
-- Hotkeys: RightAlt = flush every artifact now; RightControl = seal and end.
-- They are the watcher's two keys, and the reason is that this file is meant to
-- be run INSTEAD of the watcher during a start-up capture, not beside it: both
-- walk the same monitors, and the watcher spends up to 30% of the client doing
-- it.  RightShift is the recorder's seal and this file must never take it --
-- boot_harness.luau has a check for that, the way watch_harness.luau guards the
-- same key on its side.
-- ============================================================================

local NL = string.char(10)

local CONFIG = {
    Build = 'b3',

    -- The tick.  See (2) above: this is the resolution of the whole capture, so
    -- it is the one number here that trades fidelity for volume.  The recorder
    -- polls at 4 Hz for the same reason ("over-polling is free; under-polling is
    -- data loss") -- but over-polling is NOT free here, because every poll of
    -- every dirty key is a line in a file, so 4 Hz is chosen rather than inherited.
    SampleInterval = 0.25,

    -- A key may write this many lines and no more.  Chosen against the measured
    -- numbers, not against a feeling: the boot screen's own frames change on the
    -- order of seconds and land in the hundreds, while the glitch decoration
    -- reaches 2000 in a few hundred seconds.  So this separates them, and a key
    -- that crosses it is NAMED in suppressed.txt instead of being silently cut.
    MaxWritesPerKey = 2000,

    -- The ceiling for the whole run.  24 MB is roughly a seventh of the capture
    -- this replaces, and at the ~190 bytes a line measured in the watcher it is
    -- some 130,000 lines -- ample for a start-up and for a long shift of a
    -- settled screen.  Reaching it SEALS the run and writes the reason into
    -- meta.txt: a truncated log that does not say it was truncated is worse than
    -- no log at all.
    MaxBytes = 24 * 1024 * 1024,

    -- Flush cadence.  The operator's script buffered two seconds and then wrote;
    -- that is kept, with a byte trigger added, because two seconds is also the
    -- amount of the run that is lost if the game dies without sealing.
    FlushSeconds = 2,
    FlushBytes = 64 * 1024,

    -- Lines held before a forced flush.  Bounded so that a sink outage cannot
    -- grow the buffer without bound.
    MaxPendingLines = 20000,

    -- HttpService:PostAsync refuses a body over 1024 KB, so artifacts are split
    -- on LINE boundaries under this.  A split inside a UTF-8 sequence produces a
    -- file that is not the text that was sent.
    Chunk = 900000,

    Sink = 'http://127.0.0.1:8765/',
    -- The sink's --dir is Data/, so this lands in Data/originalboot/<stamp>/ and
    -- sits beside originalwatch/ and flow/ without colliding with either.
    Prefix = 'originalboot/',

    -- Where the bytes go when the sink is not there.  The operator's own folder,
    -- so the habit does not change -- but the name carries the stamp now, which
    -- is what stops run two appending to run one.
    LocalDir = 'TRG/',

    -- The subtree the operator scoped to, by name, and the honest default for a
    -- place whose tree has been dumped (Phase 66: exactly those seven monitors).
    RootName = 'Monitors',

    -- Paths containing any of these fragments do not get geometry watched.  The
    -- fragment is the measured one: the head, the tail and the distribution of
    -- the 180 MB capture all say GlitchEffect.GlitchFrame.  This is a MEASUREMENT
    -- entered as config, not a guess about what looks decorative.
    GeometrySkip = { '.GlitchEffect' },

    -- The operator's own two paths, kept verbatim: the boot button whose press is
    -- t=0, and the dial the run ends on.
    BootButtonPath = { 'Consoles', 'MainReactorConsole', 'MonitorBootButton',
                       'ClickPart', 'ClickDetector' },
    ClockPath = { 'QuotaControlRoomMonitor', 'Screen', 'MonitorUI',
                  'MainMonitorFrame', 'TimeFrame', 'TimeLabel' },
}

-- Geometry properties.  They are the ones a decoration churns and the only ones
-- GeometrySkip can remove, so the set lives here rather than being spelled out
-- again inside the filter.
local GEOMETRY = {
    Position = true, Size = true, Rotation = true,
    CanvasPosition = true, CanvasSize = true,
}

-- THE PROPERTY TABLE.  The operator's, kept as it was, with the properties that
-- were missing from it added -- his table records that a label became visible
-- and what it says, but not that it faded in (TextTransparency), that its image
-- swapped (Image, ImageColor3, ImageTransparency), or what colour it turned
-- (BackgroundColor3, TextColor3).  Adding to the whitelist cannot flood anything
-- on its own: every key is coalesced and budgeted below.
--
-- ScrollingFrame keeps CanvasPosition and CanvasSize -- they are geometry, and
-- the filter above is what decides whether a given instance may have them.
local WatchProperties = {
    Frame = { 'Visible', 'BackgroundTransparency', 'BackgroundColor3',
              'Position', 'Rotation', 'Size', 'ZIndex' },
    TextLabel = { 'Visible', 'Text', 'BackgroundTransparency', 'BackgroundColor3',
                  'TextTransparency', 'TextColor3', 'TextScaled', 'ZIndex' },
    TextButton = { 'Visible', 'Text', 'BackgroundTransparency', 'BackgroundColor3',
                   'TextTransparency', 'TextColor3', 'ZIndex' },
    TextBox = { 'Visible', 'Text', 'BackgroundTransparency', 'BackgroundColor3',
                'TextTransparency', 'TextColor3', 'ZIndex' },
    ImageLabel = { 'Visible', 'BackgroundTransparency', 'BackgroundColor3',
                   'Image', 'ImageColor3', 'ImageTransparency',
                   'Position', 'Rotation', 'Size', 'ZIndex' },
    ImageButton = { 'Visible', 'BackgroundTransparency', 'BackgroundColor3',
                    'Image', 'ImageColor3', 'ImageTransparency',
                    'Position', 'Rotation', 'Size', 'ZIndex' },
    ScrollingFrame = { 'Visible', 'CanvasPosition', 'CanvasSize',
                       'BackgroundTransparency', 'Size', 'ZIndex' },
}

-- ========== SMALL THINGS ==========
local HttpService = nil
pcall(function() HttpService = game:GetService('HttpService') end)

local function now()
    local ok, t = pcall(function() return workspace:GetServerTimeNow() end)
    if ok and type(t) == 'number' then return t end
    return os.time()
end

local function wallClock()
    local ok, d = pcall(os.date, '%H:%M:%S')
    if ok and type(d) == 'string' then return d end
    return '??:??:??'
end

-- Every artifact carries this, computed once at load: a prefix that changed
-- mid-run would split one run across two directories and make the set of files
-- look incomplete.
local STAMP = (function()
    local ok, d = pcall(os.date, '%y%m%d-%H%M%S')
    if ok and type(d) == 'string' then return d end
    return tostring(os.time())
end)()
local PREFIX = CONFIG.Prefix .. STAMP .. '/'

-- Newlines are stripped, and that is an INVARIANT rather than a precaution: the
-- whole capture is line-oriented, so one value whose tostring contains a newline
-- would inject a fragment that reads as a separate, malformed event.  A TextLabel
-- whose Text is multi-line is the candidate, and the operator's own recorder had
-- no guard here -- a second, quieter way its file could have been read wrong.
local function fmt(v)
    if v == nil then return 'nil' end
    local ok, s = pcall(tostring, v)
    if not ok then return '<unprintable>' end
    s = string.gsub(s, NL, ' ')
    return (string.gsub(s, string.char(13), ' '))
end

-- Walks a path of child names, tolerating a missing branch anywhere along it.
-- The operator's script chained WaitForChild with `and`, which is correct but
-- unreadable and repeats the whole path in every term; this says the same thing
-- once.
local function descend(root, path, timeout)
    local node = root
    for _, seg in ipairs(path) do
        if node == nil then return nil end
        local ok, child = pcall(function() return node:WaitForChild(seg, timeout) end)
        if not ok then return nil end
        node = child
    end
    return node
end

-- ========== TRANSPORT ==========
-- The recorder's ladder, in the recorder's order, because the two scripts
-- disagreeing about the same call is what cost the operator a whole shift on
-- 2026-09-27 (nothing arrived from the watcher while the recorder delivered a
-- complete file).  The executor's request family first, PostAsync last -- a plain
-- client is not allowed to call PostAsync and it raises at once.
--
-- THE CALLING SHAPE IS A REQUEST TABLE.  syn.request and its siblings take one;
-- the PostAsync wrapper below adapts to that shape.  Handing them a positional
-- url raises, and a probe built that way reported every working transport as
-- broken.
local TRANSPORT = 'none'
local httpFn = nil
do
    local cands = {
        { 'syn.request', function() return syn and syn.request end },
        { 'http_request', function() return http_request end },
        { 'request', function() return request end },
        { 'http.request', function() return http and http.request end },
        { 'fluxus.request', function() return fluxus and fluxus.request end },
        { 'krnl.request', function() return krnl and krnl.request end },
        { 'getgenv().request', function()
            if getgenv == nil then return nil end
            local ok, env = pcall(getgenv)
            if not ok or env == nil then return nil end
            return env.request
        end },
        { 'HttpService:PostAsync', function()
            if HttpService == nil or HttpService.PostAsync == nil then return nil end
            return function(req)
                local ok, res = pcall(HttpService.PostAsync, HttpService, req.Url, req.Body)
                if ok then return { StatusCode = 200, Body = res } end
                return { StatusCode = 0, Error = tostring(res) }
            end
        end },
    }
    -- A thunk per candidate, not the callable: a table holding nils would stop
    -- ipairs at the first missing one and silently skip every candidate after it
    -- -- which on this ladder is PostAsync, the only one a plain client has.
    for _, cand in ipairs(cands) do
        local ok, f = pcall(cand[2])
        if ok and type(f) == 'function' then
            httpFn = f
            TRANSPORT = cand[1]
            break
        end
    end
end

local function sendOnce(req)
    if httpFn == nil then
        return false, 'no HTTP transport in this executor: neither the request family' ..
            ' nor HttpService:PostAsync is present'
    end
    local ok, res = pcall(httpFn, req)
    if not ok then return false, TRANSPORT .. ' raised: ' .. tostring(res) end
    if type(res) ~= 'table' then return false, TRANSPORT .. ' returned no result table' end
    local code = tonumber(res.StatusCode) or tonumber(res.Status) or
        tonumber(res.statusCode) or tonumber(res.status) or tonumber(res.code)
    local extra = res.Error or res.error
    if code == nil then return false, TRANSPORT .. ' returned no status code' end
    if code < 200 or code > 299 then
        return false, TRANSPORT .. ' status ' .. tostring(code) ..
            (extra and (' (' .. tostring(extra) .. ')') or '')
    end
    return true, nil
end

-- ========== WHERE A FALLBACK LANDS ==========
-- The local name for an artifact is derived from the artifact's OWN name, so a
-- fallback copy of meta.txt can never land in the capture's file.  ScreenChanges
-- keeps the operator's familiar filename; the stamp, which is what stops run two
-- appending to run one, is on every one of them.
local localWritten = {}
local function localNameFor(name)
    local base = string.match(name, '([^/]*)$') or name
    base = string.gsub(base, '%.txt$', '')
    return CONFIG.LocalDir .. base .. '_' .. STAMP .. '.txt'
end

local function writeLocal(name, body)
    if type(writefile) ~= 'function' then return false end
    local path = localNameFor(name)
    -- Some executors refuse a path whose directory does not exist, and then take
    -- a bare filename in their own working directory.
    local dir = string.gsub(CONFIG.LocalDir, '/$', '')
    pcall(function()
        if type(isfolder) == 'function' and type(makefolder) == 'function' then
            if not isfolder(dir) then makefolder(dir) end
        end
    end)
    -- The FIRST write of a run resets and every later one appends, so a name
    -- collision cannot silently concatenate two runs into one file.
    local fn
    if not localWritten[path] then
        fn = writefile
    elseif type(appendfile) == 'function' then
        fn = appendfile
    else
        fn = writefile
    end
    local ok = pcall(fn, path, body)
    if not ok then ok = pcall(writefile, path, body) end
    if ok then localWritten[path] = true end
    return ok
end

local sinkChunks, sinkBytes = 0, 0
local localChunks, localBytes = 0, 0
local dropped = 0
local sinkError = nil

local function splitLines(body)
    local chunks, buf = {}, {}
    local size, pos = 0, 1
    while pos <= #body do
        local cut = string.find(body, NL, pos, true)
        local line
        if cut == nil then
            line = string.sub(body, pos)
            pos = #body + 1
        else
            line = string.sub(body, pos, cut)
            pos = cut + 1
        end
        if size + #line > CONFIG.Chunk and #buf > 0 then
            chunks[#chunks+1] = table.concat(buf)
            buf, size = {}, 0
        end
        buf[#buf+1] = line
        size = size + #line
    end
    if #buf > 0 then chunks[#chunks+1] = table.concat(buf) end
    if #chunks == 0 then chunks[1] = '' end
    return chunks
end

-- One artifact, split on line boundaries, through the sink.  THE DISK IS A
-- FALLBACK AND NOT A MIRROR: the case it exists for is exactly the case where the
-- sink takes nothing, and writing two copies of everything would be one more
-- thing to reconcile.  WHICH ONE WAS USED IS RECORDED (meta.txt carries
-- sink_chunks / local_chunks), because a file that exists in only one of the two
-- places has to say why.
local function post(name, body, append)
    if body == nil or #body == 0 then return true end
    local chunks = splitLines(body)
    for i = 1, #chunks do
        local ok, err = sendOnce({
            Url = CONFIG.Sink .. name .. (append and '?mode=a' or ''),
            Method = 'POST', Body = chunks[i],
            Headers = { ['Content-Type'] = 'text/plain' },
        })
        if not ok then
            sinkError = err
            -- Everything from this chunk on goes to the disk instead.  The run is
            -- not lost and it is not silent.
            for j = i, #chunks do
                if writeLocal(name, chunks[j]) then
                    localChunks = localChunks + 1
                    localBytes = localBytes + #chunks[j]
                else
                    dropped = dropped + 1
                end
            end
            return false
        end
        sinkChunks = sinkChunks + 1
        sinkBytes = sinkBytes + #chunks[i]
    end
    return true
end

-- ========== THE ALIVE BEACON ==========
-- The operator's rule is that a reactor start-up happens once, so a reading that
-- costs him another shift is worth one HTTP round trip to remove.  Two beacons,
-- because this script has two waiting states that look identical from outside:
--
--   nothing at all             the script never ran as far as this line
--   alive.txt only             it loaded and died in the module body below
--   alive.txt + hello.txt      the hook is armed and it is waiting for the click
--
-- A THIRD READING IS DELIBERATELY MISSING: if the operator injects and never
-- presses the button, the sink holds exactly what 'armed and waiting' holds --
-- because that is what it is.  The press is the t=0 the capture is indexed from,
-- so there is nothing to record before it and nothing to say.
local function beacon(name, lines)
    local body = table.concat(lines, NL) .. NL
    local sent, err = sendOnce({
        Url = CONFIG.Sink .. PREFIX .. name, Method = 'POST', Body = body,
        Headers = { ['Content-Type'] = 'text/plain' },
    })
    if not sent then
        -- The beacon is the one thing that must survive a dead sink, since 'the
        -- sink is down' is exactly the thing it would otherwise be reporting.
        writeLocal(name, body .. '# sink failed: ' .. tostring(err) .. NL)
    end
end

beacon('alive.txt', {
    '# the boot screen recorder is loaded and reached its transport (build ' ..
        CONFIG.Build .. ')',
    'build=' .. CONFIG.Build,
    'transport=' .. TRANSPORT,
    'sink=' .. CONFIG.Sink,
    'prefix=' .. PREFIX,
    'place=' .. tostring(game and game.PlaceId or '?'),
    'hotkeys=RightAlt flushes every artifact now; RightControl seals and ends',
    'note=hello.txt follows within a fraction of a second. If this is the only' ..
        ' file you have, the script loaded and died in its module body.',
})

-- ========== THE WATCH SET ==========
local SEALED = false          -- one flag, set first, read everywhere
local keys = {}               -- key -> true, the set of live keys
local dirty = {}              -- the pending batch, in arrival order
local dirtySet = {}           -- key -> true, so a mark is O(1) and happens once
local suppressed = {}         -- the ledger: one line per key that crossed a budget
local connections = {}        -- everything that must be disconnected on seal
local writes = {}             -- key -> lines this key has produced
local lastValue = {}          -- key -> the last value WRITTEN (not the last seen)
local ownerOf = {}            -- key -> the instance that currently occupies it
local connOf = {}             -- key -> that instance's live connection
local entryOf = {}            -- key -> the one queued entry for that key

local seal                    -- forward: the tick reports its own death through it
local emit                    -- forward: the tick writes through it
local flush                   -- forward: the hotkey flushes through it

local function keyOf(full, prop) return full .. '|' .. prop end

-- GetFullName is computed ONCE per key, at registration, and not once per line.
-- The operator's formatter called it inside the signal handler -- at 1.16 million
-- lines that is 1.16 million string builds of the same seven paths.
local function geometrySkipped(full, prop)
    if not GEOMETRY[prop] then return false end
    for _, frag in ipairs(CONFIG.GeometrySkip) do
        if string.find(full, frag, 1, true) then return true end
    end
    return false
end

-- One mark per key per tick, and the queue entry for a key is REUSED rather than
-- re-pushed.  That is what makes a re-point safe: a key whose instance was
-- replaced between the mark and the tick is read from the replacement, and not
-- from the corpse the entry was queued with.
local function mark(key, obj, full, prop)
    local entry = entryOf[key]
    if entry == nil then
        entry = { obj = obj, full = full, prop = prop, key = key }
        entryOf[key] = entry
    else
        entry.obj = obj
    end
    if not dirtySet[key] then
        dirtySet[key] = true
        dirty[#dirty+1] = entry
    end
end

local function watch(obj, full, prop, key)
    local okSig, signal = pcall(function() return obj:GetPropertyChangedSignal(prop) end)
    if not okSig or signal == nil or signal.Connect == nil then return false end
    local okConn, conn = pcall(function()
        return signal:Connect(function()
            if SEALED or keys[key] == nil then return end
            -- THE COALESCER.  A change costs one table lookup and one mark, not a
            -- formatted line: 60 Hz of jitter becomes one entry in one batch, and
            -- the tick decides whether the value was worth anything.
            mark(key, obj, full, prop)
        end)
    end)
    if not okConn or conn == nil then return false end
    connections[#connections+1] = conn
    connOf[key] = conn
    return true
end

-- A value no formatted property can ever equal, so 'not written yet' is a state
-- the tick can recognise.  A NUL is impossible inside fmt()'s output -- that
-- output goes into a line of a text file -- which is why it is this and not ''.
local BIRTH = string.char(0)

-- `born` is true only for an instance that DescendantAdded handed us, i.e. one
-- that came into being AFTER the boot press.  The initial walk leaves it false.
local function register(obj, born)
    local props = WatchProperties[obj.ClassName]
    if props == nil then return end
    local okName, full = pcall(function() return obj:GetFullName() end)
    if not okName or type(full) ~= 'string' then return end
    for _, prop in ipairs(props) do
        local key = keyOf(full, prop)
        if not geometrySkipped(full, prop) then
            if keys[key] == nil then
                if watch(obj, full, prop, key) then
                    keys[key] = true
                    ownerOf[key] = obj
                    if born then
                        -- BORN DURING THE RUN: its CURRENT values are data, not a
                        -- baseline.  Phase 71 -- the game writes a cloned log frame's
                        -- message BEFORE it parents the frame, so seeding here is
                        -- exactly what swallowed the boot screen's own narration.
                        -- The seed becomes 'never written', and the next tick writes
                        -- what the instance actually holds, through the same one-line-
                        -- per-key path and against the same write budget as every
                        -- other line.  The cost, stated: a subtree cloned mid-run now
                        -- contributes its watched values once, and a value that
                        -- changes between birth and the next tick is reported at its
                        -- tick value -- the same 0.25 s quantisation every other line
                        -- already has.
                        lastValue[key] = BIRTH
                        mark(key, obj, full, prop)
                    else
                        -- SEEDED WITH THE VALUE AT REGISTRATION, and this is the whole
                        -- of the change-and-revert rule.  Comparing against nil
                        -- instead would mean that a value which flickered and came
                        -- back still got one line, because the final reading would
                        -- differ from 'never seen' -- the noise this file exists to
                        -- remove, arriving by the back door.  One property read per
                        -- key, once, at registration.
                        local okV, v = pcall(function() return obj[prop] end)
                        lastValue[key] = okV and fmt(v) or '<read failed>'
                    end
                end
            elseif born and ownerOf[key] ~= obj then
                -- A PATH IS NOT AN OBJECT.  Phase 72: the log panel clones a FRESH
                -- row per message onto three fixed names, so this path is born and
                -- destroyed once per message for the whole shift.  While the key
                -- was gated on 'have I ever seen this path', the second message
                -- onwards was dropped whole -- the old instance's connection stayed
                -- aimed at a corpse, and the run's own narration stopped after its
                -- first three lines (3 lines here against 35 distinct messages in
                -- the r60 capture of the same shift, START-UP COMPLETED among the
                -- missing).  Re-point the key at the instance that actually
                -- occupies the path now: drop the corpse's connection, watch the
                -- replacement, and let the birth record say what it was born
                -- holding.  keys[key] and writes[key] deliberately survive: the
                -- budget is per PATH, because that is what suppressed.txt names.
                local stale = connOf[key]
                if stale ~= nil then
                    pcall(function() stale:Disconnect() end)
                    connOf[key] = nil
                end
                if watch(obj, full, prop, key) then
                    ownerOf[key] = obj
                    lastValue[key] = BIRTH
                    mark(key, obj, full, prop)
                end
            end
        end
    end
end

-- ========== THE TICK ==========
-- One pass over everything marked dirty since the last one.  At most one line per
-- key, and only if the value actually differs from the last one written -- the
-- operator's own rule ('no change, no line') applied at the tick instead of at
-- the event, which is the wrong place for a 60 Hz property.
local busy = false
local function tick()
    if SEALED or busy then return end
    busy = true
    -- An error inside the walk must not be silent: the scan is the only thing
    -- producing the artifact, and 'it was running but nothing happened' and 'it
    -- died on the first tick' look identical from outside.
    local ok, err = pcall(function()
        local batch = dirty
        dirty = {}
        dirtySet = {}
        for _, d in ipairs(batch) do
            if not SEALED then
                local n = writes[d.key] or 0
                if n >= CONFIG.MaxWritesPerKey then
                    -- Named, not silently cut.  A budget with no ledger is a
                    -- truncation that does not say it was a truncation.
                    if n == CONFIG.MaxWritesPerKey then
                        writes[d.key] = n + 1
                        suppressed[#suppressed+1] = d.full .. '|' .. d.prop ..
                            '|' .. tostring(CONFIG.MaxWritesPerKey) .. '|' .. wallClock()
                        emit('# SUPPRESSED ' .. d.full .. '|' .. d.prop .. ' after ' ..
                            tostring(CONFIG.MaxWritesPerKey) ..
                            ' writes -- see suppressed.txt')
                    end
                else
                    local okV, v = pcall(function() return d.obj[d.prop] end)
                    local text = okV and fmt(v) or '<read failed>'
                    if text ~= lastValue[d.key] then
                        lastValue[d.key] = text
                        writes[d.key] = n + 1
                        emit(string.format('Time:[%s]<-O:[%s]<-C:[%s]<-V:[%s]',
                            wallClock(), d.full, d.prop, text))
                    end
                end
            end
        end
    end)
    busy = false
    if not ok then
        local why = 'the tick failed: ' .. tostring(err)
        pcall(function() warn(why) end)
        seal('error', why)
    end
end

-- ========== THE BUFFER ==========
local buffer = {}
local bufferedBytes = 0
local linesOut = 0
local bytesOut = 0
local startedAt = nil

emit = function(lineText)
    if SEALED then return end
    buffer[#buffer+1] = lineText .. NL
    bufferedBytes = bufferedBytes + #lineText + 1
    linesOut = linesOut + 1
    bytesOut = bytesOut + #lineText + 1
    if bytesOut >= CONFIG.MaxBytes then
        seal('ceiling', 'the byte ceiling was reached: ' .. tostring(CONFIG.MaxBytes))
    end
end

flush = function()
    if #buffer == 0 then return end
    local body = table.concat(buffer)
    buffer = {}
    bufferedBytes = 0
    post(PREFIX .. 'ScreenChanges.txt', body, true)
end

-- ========== SEALING ==========
seal = function(reason, detail)
    if SEALED then return end
    SEALED = true
    local elapsed = startedAt and (now() - startedAt) or 0
    for _, conn in ipairs(connections) do
        pcall(function() if conn.Connected then conn:Disconnect() end end)
    end
    connections = {}
    keys = {}
    dirtySet = {}
    dirty = {}
    -- The buffer goes out BEFORE meta.txt, so a reader that has meta.txt has the
    -- whole capture: the seal record must never arrive ahead of the data it
    -- describes.
    flush()
    post(PREFIX .. 'meta.txt', table.concat({
        '# the boot screen recorder has sealed (build ' .. CONFIG.Build .. ')',
        'build=' .. CONFIG.Build,
        'reason=' .. tostring(reason),
        'detail=' .. tostring(detail or ''),
        'stamp=' .. STAMP,
        'transport=' .. TRANSPORT,
        'prefix=' .. PREFIX,
        'started_at=' .. tostring(startedAt),
        'elapsed_s=' .. string.format('%.2f', elapsed),
        'lines=' .. tostring(linesOut),
        'bytes=' .. tostring(bytesOut),
        'sink_chunks=' .. tostring(sinkChunks),
        'sink_bytes=' .. tostring(sinkBytes),
        'local_chunks=' .. tostring(localChunks),
        'local_bytes=' .. tostring(localBytes),
        'dropped_chunks=' .. tostring(dropped),
        'suppressed_keys=' .. tostring(#suppressed),
        'sink_error=' .. tostring(sinkError or 'none'),
        'note=ScreenChanges.txt carries the capture. LINES ARE WRITTEN ONLY WHEN A' ..
            ' VALUE CHANGED AT THE TICK (4 Hz), so a change that reverted inside one' ..
            ' tick is not in the file. suppressed.txt names every key that crossed' ..
            ' its write budget.',
    }, NL) .. NL, false)
    if #suppressed > 0 then
        post(PREFIX .. 'suppressed.txt', table.concat(suppressed, NL) .. NL, false)
    end
end

-- ========== THE RECORDING WINDOW ==========
-- The operator starts it by pressing the boot button, and that press is the t=0
-- of the whole capture: it is the same event his own hook used, and every anchor
-- derived from the last capture is relative to it.  So the hook is armed at
-- injection and nothing at all is recorded until the click.
local function arm()
    local Monitors = workspace:FindFirstChild(CONFIG.RootName)
    if Monitors == nil then
        seal('error', 'there is no Workspace.' .. CONFIG.RootName)
        return false
    end
    for _, obj in ipairs(Monitors:GetDescendants()) do
        register(obj)
    end
    -- Instances created DURING the run belong to it, and they belong to it with
    -- the values they were born with -- which is why this is the one call site
    -- that says born.  Phase 66 and 67 both hit the consequence of not having the
    -- hook at all: the start-up steps clone their UI at runtime, and a recorder
    -- built from a fixed descendant set cannot see them.  Phase 71 hit the
    -- consequence of having the hook without the birth record.
    pcall(function()
        connections[#connections+1] = Monitors.DescendantAdded:Connect(function(obj)
            if not SEALED then register(obj, true) end
        end)
    end)
    return true
end

local function startRecording()
    if startedAt ~= nil then return end
    startedAt = now()
    -- arm() FIRST, and the header only once the run is real.  Written the other way
    -- round, a press on a world with no root produced a capture file containing
    -- nothing but its own header -- a run that looks started and a file that looks
    -- like data.  A failed arm now leaves ScreenChanges.txt untouched, and the
    -- death is in meta.txt where it belongs.
    if not arm() then return end
    -- A header, so the artifact says what it is without needing meta.txt.  It is
    -- a comment line and no reader matches it.
    emit('# build=' .. CONFIG.Build .. ' start=' .. wallClock() ..
        ' root=' .. CONFIG.RootName .. ' tick=' .. tostring(CONFIG.SampleInterval) ..
        ' transport=' .. TRANSPORT)
    beacon('boot.txt', {
        '# the boot button was pressed (build ' .. CONFIG.Build .. ')',
        'build=' .. CONFIG.Build,
        't0=' .. wallClock(),
        'note=ScreenChanges.txt is indexed from this press',
    })
end

-- ========== THE CLOCK ==========
-- ONE seal rule, and the midnight wrap is NOT it.  Measured, not reasoned.
--
-- The operator's rule seals on 12:00 AM or 12:00 PM.  The first draft kept both
-- and disarmed the AM arm until the dial had been seen OFF midnight, on the
-- assumption -- written down as an assumption in PROGRESS.md Phase 62 -- that the
-- dial OPENS at 12:00 AM.  The first real run says otherwise: the press landed at
-- 11:51 PM, so the very first reading armed the wrap, and midnight, 89 s later,
-- sealed the run.  That is the moment the core lit (temp 248 -> 9478 F, output
-- 0 -> 146 GW/H, HDEF 5 -> 99 %, and the thermal monitor showing AUTO
-- RECALIBRATION IN PROGRESS), and the start-up chain's own START-UP COMPLETED
-- lands at 86..146 s over four measured runs.  The capture was cut by a rule that
-- fired at the shift's START.
--
-- So midnight is recorded and the run continues: the dial's own crossing is the
-- anchor the boot chain should be read against, and losing it would be its own
-- defect.  Noon still ends the run, because that is the operator's own spec for
-- the listening window (PROGRESS.md Phase 62: start at the press, end at 12 PM).
-- The mark is a COMMENT line, so it stays inside the frozen line format -- the
-- archived readers skip '#' lines by construction, and appending a field to a data
-- line is what is forbidden (DECISIONS_2 237).
local function watchClock()
    local label = descend(workspace:FindFirstChild(CONFIG.RootName), CONFIG.ClockPath, 30)
    if label == nil then
        -- Not fatal: the byte ceiling still ends the run and the operator still
        -- has the hotkey.  Said out loud rather than swallowed.
        beacon('notice.txt', {
            '# the noon seal is unavailable (build ' .. CONFIG.Build .. ')',
            'build=' .. CONFIG.Build,
            'note=no TimeLabel at ' .. CONFIG.RootName .. '.' ..
                table.concat(CONFIG.ClockPath, '.'),
        })
        return
    end
    local okConn, conn = pcall(function()
        return label:GetPropertyChangedSignal('Text'):Connect(function()
            if SEALED or startedAt == nil then return end
            local text = label.Text
            if text == '12:00 PM' then
                seal('noon', 'the dial reached 12:00 PM')
            elseif text == '12:00 AM' then
                emit('# MARK midnight at ' .. wallClock() ..
                    ' -- the dial crossed 12:00 AM, which on this world is the' ..
                    ' shift START and not its end; the run continues')
            end
        end)
    end)
    if okConn and conn ~= nil then connections[#connections+1] = conn end
end

-- ========== HOTKEYS ==========
-- RightAlt flushes, RightControl seals.  Two keys the operator already knows from
-- the watcher, and the reason is that this file is meant to be run INSTEAD of the
-- watcher during a start-up capture, not beside it.  RightShift is the recorder's
-- seal and this file must never take it -- boot_harness.luau has a check for that,
-- the same way watch_harness.luau guards that key on its side.
local function bindHotkeys()
    local ok, UIS = pcall(function() return game:GetService('UserInputService') end)
    if not ok or UIS == nil or UIS.InputBegan == nil then return end
    pcall(function()
        UIS.InputBegan:Connect(function(input, processed)
            if processed then return end
            local okCode, code = pcall(function() return input.KeyCode end)
            if not okCode then return end
            local name = tostring(code)
            if name == 'Enum.KeyCode.RightAlt' then
                flush()
            elseif name == 'Enum.KeyCode.RightControl' then
                seal('hotkey', 'RightControl')
            end
        end)
    end)
end

-- ========== START ==========
local function start()
    -- Whether the world is there YET, answered at injection and not at the press.
    -- The run itself still resolves nothing until the button, because under
    -- StreamingEnabled a root that is missing at injection is usually merely
    -- late, and killing a run for that would be a false alarm.  But the operator
    -- needs to know which of the two it was, and only this line can say it.
    local okRoot, rootAtInject = pcall(function()
        return workspace:FindFirstChild(CONFIG.RootName)
    end)
    beacon('hello.txt', {
        '# the boot screen recorder is armed (build ' .. CONFIG.Build .. ')',
        'build=' .. CONFIG.Build,
        'transport=' .. TRANSPORT,
        'root_visible_at_inject=' .. tostring(okRoot and rootAtInject ~= nil),
        'waiting_for=Workspace.Consoles.MainReactorConsole.MonitorBootButton',
        'hotkeys=RightAlt flushes now; RightControl seals',
        'note=inject this BEFORE pressing the boot button. The capture is indexed' ..
            ' from the press, so a run that starts after it has no t=0.',
    })
    bindHotkeys()

    task.spawn(function()
        local det = descend(workspace, CONFIG.BootButtonPath, 60)
        if det == nil or det.MouseClick == nil then
            seal('error', 'there is no boot button ClickDetector at ' ..
                table.concat(CONFIG.BootButtonPath, '.'))
            return
        end
        det.MouseClick:Connect(function()
            startRecording()
            watchClock()
        end)
    end)

    -- The tick loop.  It does NOT tick before the boot button: nothing is
    -- registered yet, so there would be nothing to write, and an empty pass per
    -- 0.25 s for however long the operator takes to press is work with no output.
    task.spawn(function()
        while not SEALED do
            task.wait(CONFIG.SampleInterval)
            pcall(tick)
            if startedAt ~= nil and not SEALED then
                if bufferedBytes >= CONFIG.FlushBytes or #buffer >= CONFIG.MaxPendingLines then
                    pcall(flush)
                end
            end
        end
    end)

    task.spawn(function()
        while not SEALED do
            task.wait(CONFIG.FlushSeconds)
            if startedAt ~= nil then pcall(flush) end
        end
    end)
end

start()
