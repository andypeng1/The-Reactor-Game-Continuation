-- room_watch.luau -- a read-only census and change log for the control room and
-- the reactor chamber.
--
-- WHY THIS EXISTS.  The start-up chain in the backend is gated in Engine, and
-- the world half of it was rebuilt by hand twice on a reading of the art rather
-- than on a measurement of the art.  The second rebuild was wrong in a way that
-- is invisible from the source: it looked for the shutters' travel ABOVE the
-- glass, inside the glass's own frame, when the travel is DOWN into the wall
-- below the sill.  Nothing in the codebase could have told us that.  Only the
-- world can, and the world only says it while it is moving.  So this watches the
-- world instead of the source.
--
-- WHAT IT IS NOT.  It writes nothing back: every read is a property get, there
-- is no `=` to a watched instance anywhere in this file.  It does not require
-- ReactorBackend, Config or Engine, so it can be dropped into a place that has
-- none of them, and it cannot be fooled by a stale require handing it the wrong
-- module.  It is not a gameplay system and nothing in the game reads it.
--
-- HOW IT REPORTS.  Four files, pushed to a local HTTP sink rather than returned
-- through a tool call, because the whole point is that these bytes never have to
-- pass through a context window to be useful:
--
--   rooms.txt      once.  Coverage: which roots were found, and what each one
--                  holds, by class.  This is the answer to "what did you watch".
--   inventory.txt  once.  Every watched instance, its class, its path, and the
--                  property names this file reads off that class.
--   summary.txt    rewritten whenever anything changed.  One line per property
--                  that has changed SINCE START, holding its current value, the
--                  value it had at start, and how many times it moved.
--   changes.log    appended.  The timeline: one line per change, in order, with
--                  both a tick-relative clock and a wall clock so the operator
--                  can line it up against what they did.
--   suppressed.txt rewritten whenever the judged set changes.  The disclosure
--                  that makes changes.log's silence honest: every key this run
--                  decided was decoration is named here with the count that got
--                  it there.  Without it, "this key never moved" and "this key
--                  was dropped from the timeline" would look the same.
--
-- WHAT "SUPPRESSED" MEANS.  This place has both clocks and events in it, and the
-- difference is not visible in any single line -- a spinning antenna writes a
-- line that is indistinguishable from a lever being thrown.  So a key's recent
-- moves are held back, un-written, in a ring of at most NoisyAfter lines.  A key
-- that fills the ring has moved more times in a row than any operator action
-- produces and is ambient: the ring is dropped and the key is named in
-- suppressed.txt.  A key that instead goes quiet for QuietScans is an event: the
-- ring is written out in order, and its next moves are held again.  Nothing is
-- ever un-written, and nothing is lost either: summary.txt keeps every moved
-- key's current value, its start value and its full change count whether or not
-- its timeline survived.  What is dropped is repetition.
--
-- The rule from the recorder applies here too and it is the reason summary.txt
-- is not simply a state dump: 保存到文件时候一定是有变化的才计入，没变化不要收集.
-- An instance that never moves appears in inventory.txt (coverage) and never
-- appears in summary.txt (state).  That is deliberate -- it is what makes
-- summary.txt readable at a glance after a start-up, when a few hundred things
-- out of twenty thousand have moved and the other nineteen thousand have not.

local HttpService = game:GetService('HttpService')

local CONFIG = {
    -- Where the artifacts go.  Point this at _tools/receive.py; the port is
    -- deliberately not 8765 or 8767, because receive.py sets allow_reuse_address
    -- and on Windows a second process can then bind a port that is already
    -- served while reporting success -- so a shared port silently writes into
    -- whichever process bound first.
    Sink = 'http://127.0.0.1:8771/',
    -- Seconds between scans.  One full scan of the current watch set is about
    -- 19 ms with three properties read per instance and about 60 ms with the
    -- full set, so this is roughly a 6% duty cycle on one server thread of a
    -- ~1000 ms heartbeat.  It is a diagnostic, not a shipping system.
    Interval = 1,
    -- HttpService:PostAsync refuses a body over 1024 KB, so every artifact is
    -- split on line boundaries under this.  Line boundaries and not byte
    -- offsets: a split inside a UTF-8 sequence produces a file that is not the
    -- text that was sent.
    Chunk = 900000,
    -- Changes are queued and flushed once per tick.  If the sink is down the
    -- queue would grow without bound, so it is capped and the overflow is
    -- counted rather than silently dropped -- a truncated log that does not say
    -- it was truncated is worse than no log.
    MaxQueue = 4000,
    -- Console output every N ticks, so a long run does not spam the output log.
    ReportEvery = 30,
    -- THE WHOLE TEST: a key may hold this many of its lines back at once, and a
    -- key that fills the ring has moved more times in a row than any single
    -- operator action produces.  Overflowing IS the proof -- there is no clock
    -- and no separate threshold to go wrong -- and a key that overflows never
    -- reaches changes.log at all: its ring is dropped, and it is named in
    -- suppressed.txt instead.  Its value and its change count stay live in
    -- summary.txt, so a suppressed key is disclosed, not hidden.
    --
    -- Measured on the first live run: 40 spinning antenna parts produced 66,425
    -- of 66,884 lines while the 56 keys that carried actual events produced the
    -- other 459.  Measured on the runs that got this wrong: an earlier version
    -- judged a key once, a fixed number of scans after its first move, and
    -- promoted it to "an event" if it had not overflowed by then.  That reads
    -- well and is wrong for anything that moves slowly -- the third run left
    -- 1,045 lines behind, led by two chamber fans at 47 and 46 lines each, whose
    -- first move was followed by a 32-second gap.  They were judged events
    -- before they had a chance to show what they were.  Counting lifetime
    -- changes but re-arming after one quiet tick instead produced 2,211
    -- announce/resume pairs on keys that were not clocks at all, and counting
    -- consecutive scans found three clocks out of 1,952.  None of those three is
    -- visible by reading the code -- all three look correct -- which is why the
    -- number is here rather than defended in prose.
    NoisyAfter = 8,
    -- How many quiet scans a key must show before its held lines are written
    -- out.  This is the other half of the test and it is deliberately not a
    -- clock on the key's AGE: a lever animates and then stops, so "it stopped"
    -- is exactly the evidence that it was an operator action, and the evidence
    -- only exists afterwards.  Five is measured against this place's tick, where
    -- the intermittent spinners leave gaps of one to three scans and anything
    -- the operator drove is quiet for far longer than five.
    QuietScans = 5,
    -- summary.txt is rewritten only on a tick that is a multiple of this.  It is
    -- one line per moved key with two full values on it, so on a busy reactor it
    -- runs to most of a megabyte, and rewriting it every second would be the
    -- largest thing this file does.  Stop() and Report() force one regardless.
    SummaryEvery = 10,
}

-- ========== WHAT IS WATCHED ==========
-- The roots are spelled as the place spells them, and a root that is missing is
-- REPORTED rather than skipped, because a silently absent root looks exactly
-- like a room where nothing ever happens.  rooms.txt carries the found/missing
-- verdict for every one of them.
--
-- The boundary is the two rooms the operator named and their fixtures.  The
-- reactor chamber is taken to include the things mounted in and on it -- the
-- walls, the core, the three CBLs, the blast door, the six fans, the six
-- clamps, the three E-VENTs, the six METU spires, the decay fields, the coolant
-- pipes and their particle hosts, the Isotope E particle hosts and the core
-- antenna.  Deliberately NOT in: the HDEF, the Gravatron, the Mainframe, the
-- MES units, the Lounge and the coolant chambers CRC1-3.  Those are other rooms
-- and other systems one path away, and adding one is a one-line edit here.
local GROUPS = {
    {name = 'ControlRoom', roots = {
        'Consoles',
        'Monitors',
        'RoomLights.ControlRoomLights',
        'MovingParts.ControlRoomLShutter',
        'MovingParts.ControlRoomMShutter',
        'MovingParts.ControlRoomRShutter',
        'MovingParts.ControlRoomMAPLeft',
        'MovingParts.ControlRoomMAPRight',
    }},
    {name = 'Chamber', roots = {
        'Core',
        'ChamberWalls',
        'ReactorCBLs',
        'CHMBRBlastDoor',
        'ChamberCoolantPipe1',
        'ChamberCoolantPipe2',
        'ChamberCoolantPipe3',
        'MovingParts.ChamberFan1', 'MovingParts.ChamberFan2',
        'MovingParts.ChamberFan3', 'MovingParts.ChamberFan4',
        'MovingParts.ChamberFan5', 'MovingParts.ChamberFan6',
        'MovingParts.ReactorClamps1', 'MovingParts.ReactorClamps2',
        'MovingParts.ReactorClamps3', 'MovingParts.ReactorClamps4',
        'MovingParts.ReactorClamps5', 'MovingParts.ReactorClamps6',
        'MovingParts.E_VENT1', 'MovingParts.E_VENT2', 'MovingParts.E_VENT3',
        'MovingParts.METUSpire1', 'MovingParts.METUSpire2',
        'MovingParts.METUSpire3', 'MovingParts.METUSpire4',
        'MovingParts.METUSpire5', 'MovingParts.METUSpire6',
        'MovingParts.FanTriggerParts',
        'MovingParts.DecayFields',
        'MovingParts.CoolantPipes',
        'MovingParts.CoolantParticleParts',
        'MovingParts.ISEParticleParts',
        'MovingParts.ISEParticleParts2',
        'MovingParts.CoreAntenna',
    }},
}

-- ========== WHICH PROPERTIES, PER CLASS ==========
-- Chosen by asking what a script could plausibly drive, not by listing every
-- property a class has: Watching `Part.Shape` or `Part.Name` would put twenty
-- thousand keys in the log that no start-up can ever change.  The `IsA` order
-- matters where classes overlap -- Beam is not a GuiObject and SurfaceGui is not
-- a GuiObject either, but a TextButton is both a GuiObject and a GuiButton, and
-- the text properties are added only for the classes that actually have them.
--
-- Sound.TimePosition is deliberately absent.  It changes every tick while a
-- sound plays, so watching it would drown the timeline in the one thing that
-- carries no information: that a sound is still playing.  Playing is watched.
local function propsFor(inst)
    if inst:IsA('BasePart') then
        return {'CFrame', 'Size', 'Color', 'Material', 'Transparency',
                'Anchored', 'CanCollide', 'Reflectance', 'CastShadow'}
    elseif inst:IsA('Light') then
        return {'Enabled', 'Brightness', 'Color', 'Range', 'Shadows'}
    elseif inst:IsA('ParticleEmitter') then
        return {'Enabled', 'Rate', 'Color', 'Size', 'Transparency', 'Lifetime',
                'Speed', 'LightEmission', 'LightInfluence'}
    elseif inst:IsA('Beam') then
        return {'Enabled', 'Color', 'Transparency', 'Width0', 'Width1',
                'Brightness', 'LightEmission'}
    elseif inst:IsA('Trail') then
        return {'Enabled', 'Color', 'Transparency', 'Brightness', 'Lifetime'}
    elseif inst:IsA('SoundEffect') then
        -- The generic flag every effect has, plus the parameters of the four
        -- kinds this place actually uses.  Enabled alone would miss a sound
        -- being reshaped in place, which is how a running reactor is made to
        -- sound different from a stopped one.
        local p = {'Enabled'}
        if inst:IsA('EqualizerSoundEffect') then
            p[#p+1] = 'LowGain'; p[#p+1] = 'MidGain'; p[#p+1] = 'HighGain'
        elseif inst:IsA('DistortionSoundEffect') then
            p[#p+1] = 'Level'
        elseif inst:IsA('PitchShiftSoundEffect') then
            p[#p+1] = 'Octave'
        elseif inst:IsA('ReverbSoundEffect') then
            p[#p+1] = 'DecayTime'; p[#p+1] = 'WetLevel'; p[#p+1] = 'DryLevel'
            p[#p+1] = 'Density'; p[#p+1] = 'Diffusion'
        end
        return p
    elseif inst:IsA('Sound') then
        return {'Playing', 'Volume', 'Pitch', 'SoundId', 'Looped'}
    elseif inst:IsA('GuiObject') then
        local p = {'Visible', 'BackgroundColor3', 'BackgroundTransparency',
                   'Size', 'Position', 'ZIndex'}
        if inst:IsA('TextLabel') or inst:IsA('TextButton') or inst:IsA('TextBox') then
            p[#p+1] = 'Text'; p[#p+1] = 'TextColor3'; p[#p+1] = 'TextTransparency'
        end
        if inst:IsA('ImageLabel') or inst:IsA('ImageButton') then
            p[#p+1] = 'Image'; p[#p+1] = 'ImageColor3'; p[#p+1] = 'ImageTransparency'
        end
        return p
    elseif inst:IsA('LayerCollector') then
        return {'Enabled', 'Brightness', 'LightInfluence', 'MaxDistance',
                'AlwaysOnTop'}
    elseif inst:IsA('ValueBase') then
        -- The console StringValues are label text, so this is one of the
        -- highest-yield classes in the whole set: it is where a device writes
        -- what it wants to say.
        return {'Value'}
    elseif inst:IsA('ClickDetector') then
        return {'MaxActivationDistance'}
    elseif inst:IsA('ProximityPrompt') then
        return {'Enabled', 'ActionText', 'ObjectText', 'HoldDuration'}
    elseif inst:IsA('DataModelMesh') then
        return {'Scale', 'Offset', 'VertexColor'}
    elseif inst:IsA('Decal') then
        return {'Texture', 'Transparency', 'Color3'}
    elseif inst:IsA('Attachment') then
        return {'CFrame'}
    elseif inst:IsA('RopeConstraint') then
        -- The hanging cables in the chamber walls swing, and RopeConstraint is
        -- the only place the swing is recorded as a number.
        return {'Length', 'Visible', 'Thickness'}
    elseif inst:IsA('HingeConstraint') then
        return {'Enabled', 'AngularVelocity', 'TargetAngle', 'MotorMaxTorque'}
    elseif inst:IsA('BaseScript') then
        return {'Enabled'}
    end
    return nil
end

-- ========== STATE ==========
local ents = {}        -- {inst, path, group, props}
local vals = {}        -- flat: the value last seen, stride = #props
local org = {}         -- flat: the value at start, never overwritten
local hits = {}        -- flat: how many times this key has moved, over the whole run
local seen = {}        -- inst -> true, so a child added twice is registered once
local connections = {}
local running = false
local totalProps = 0
local report = {found = {}, missing = {}, byGroup = {}, classTotal = {}}
local logLines = {}
local dropped = 0
local sinkDown = false
local tick = 0
local startedAt = 0
local scanMs = 0
local movedKeys = 0
local summaryDirty = false
local lastTick = {}    -- j -> the tick this key last moved
-- j -> the lines this key has moved but has NOT written out yet, capped at
-- NoisyAfter.  Every key keeps this, always -- a key that has already proven
-- itself an event keeps it too, because the proof is only ever provisional and
-- the ring is how a key that turns into a spinner later is caught.  The only way
-- to un-write a line is to never have written it: the sink appends, so a line
-- that reaches it is there for good.  See record().
local held = {}
-- j -> 'discrete' once a key's lines have been written out at least once, which
-- is what turns the RESUMED announcement on and off.  Absent means "never yet
-- flushed".  This is NOT a verdict and nothing is decided by it.
local judged = {}
-- j -> the tick of this key's first move.  Kept for suppressed.txt only.
local firstTick = {}
-- j -> {ent, i, tick, first} for every key currently judged ambient.  These do
-- NOT go into changes.log: a line per ambient key would be ~1,900 lines of
-- "nothing happened here", which is the same noise it replaced.  They are the
-- whole content of suppressed.txt, rewritten on the summary throttle.
local ambient = {}
local suppressedDirty = false
-- Set to the error text if the scan loop ever dies, so Status() can say so
-- rather than reporting a tick count that has stopped advancing.
local fatal = nil
local usedPaths = {}   -- path -> how many instances have claimed it
local collisions = 0   -- how many instances needed disambiguating

local NL = string.char(10)

local function now()
    local ok, t = pcall(function() return workspace:GetServerTimeNow() end)
    return ok and t or os.time()
end

local function stamp()
    -- Both clocks on purpose.  The relative one answers "how far into the run",
    -- the wall one answers "what was I doing at that moment" -- and the operator
    -- is the only one who knows the second answer.
    local ok, d = pcall(os.date, '%H:%M:%S')
    return string.format('t=%.2f %s', now() - startedAt, ok and d or '??:??:??')
end

local function fmt(v)
    if v == nil then return 'nil' end
    local ok, s = pcall(tostring, v)
    return ok and s or '<unprintable>'
end

-- ========== THE SINK ==========
local function post(name, body, append)
    local ok, err = pcall(function()
        -- Split on newline boundaries rather than byte offsets.  A split inside
        -- a UTF-8 sequence produces a file that is not the text that was sent,
        -- and every artifact here is line-structured anyway, so there is nothing
        -- to gain by pretending otherwise.
        local chunks = {}
        local buf = {}
        local size = 0
        local pos = 1
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
                buf = {}
                size = 0
            end
            buf[#buf+1] = line
            size = size + #line
        end
        if #buf > 0 then chunks[#chunks+1] = table.concat(buf) end
        local first = true
        for _, chunk in ipairs(chunks) do
            local url = CONFIG.Sink .. name
            -- In append mode every chunk appends.  In write mode the first chunk
            -- truncates and the rest append, which is the only way to get an
            -- atomic-looking file out of a sink that has no rename.
            if append or not first then url = url .. '?mode=a' end
            first = false
            HttpService:PostAsync(url, chunk)
        end
    end)
    if ok then
        if sinkDown then
            sinkDown = false
            print('[RoomWatch] sink is back: ' .. CONFIG.Sink)
        end
    elseif not sinkDown then
        sinkDown = true
        print('[RoomWatch] sink unreachable at ' .. CONFIG.Sink .. ' (' ..
              tostring(err) .. ') -- still watching, changes are being queued')
    end
    return ok
end

-- ========== REGISTRATION ==========
-- A path is an instance's identity in every artifact this file writes, and
-- GetFullName does not guarantee one.  This place has twenty separate light
-- cells whose descendant chains all read `LightCell.LightModel.NeonPart`, so on
-- the first live run all twenty lamps were logged under a single path and the
-- log announced "Transparency changed 40 times" about what were really twenty
-- lamps changing twice.  A colliding path therefore gets a suffix.  For a part
-- that suffix is its world position -- unique here, and the thing the operator
-- can actually go and look at.  Collisions are counted and reported in
-- rooms.txt, because a silent disambiguation is a silent chance to mislabel.
local function uniquePath(inst)
    local path = string.gsub(inst:GetFullName(), '^Workspace%.', '')
    if usedPaths[path] == nil then
        usedPaths[path] = true
        return path
    end
    collisions = collisions + 1
    local suffix = ''
    if inst:IsA('BasePart') then
        local p = inst.Position
        suffix = string.format(' ~(%.1f, %.1f, %.1f)', p.X, p.Y, p.Z)
    end
    local candidate = path .. suffix
    local n = 1
    while usedPaths[candidate] ~= nil do
        n = n + 1
        candidate = path .. suffix .. ' #' .. n
    end
    usedPaths[candidate] = true
    return candidate
end

local function register(inst, group)
    if seen[inst] then return end
    local props = propsFor(inst)
    if props == nil then return end
    seen[inst] = true
    local path = uniquePath(inst)
    local ent = {inst = inst, path = path, group = group, props = props,
                 base = totalProps}
    ents[#ents+1] = ent
    for i = 1, #props do
        local j = totalProps + i
        local v = inst[props[i]]
        vals[j] = v
        org[j] = v
        hits[j] = 0
        -- Emptied rather than left absent so that record() can append without a
        -- nil check on the first move of every key in the run.  buildIndex()
        -- re-registers everything from scratch, so this is also what makes a
        -- re-run start clean instead of inheriting the previous run's holds.
        held[j] = {}
        judged[j] = nil
        firstTick[j] = nil
        ambient[j] = nil
        lastTick[j] = nil
    end
    totalProps = totalProps + #props
    local counts = report.byGroup[group]
    if counts then
        counts[inst.ClassName] = (counts[inst.ClassName] or 0) + 1
    end
    report.classTotal[inst.ClassName] = (report.classTotal[inst.ClassName] or 0) + 1
end

local function resolve(path)
    local node = workspace
    for token in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

local function buildIndex()
    report = {found = {}, missing = {}, byGroup = {}, classTotal = {}}
    usedPaths = {}
    collisions = 0
    for _, group in ipairs(GROUPS) do
        report.byGroup[group.name] = {}
        for _, root in ipairs(group.roots) do
            local node = resolve(root)
            if node == nil then
                report.missing[#report.missing+1] = group.name .. '/' .. root
            else
                report.found[#report.found+1] = {
                    group = group.name, path = root,
                    class = node.ClassName,
                    count = #node:GetDescendants(),
                }
                register(node, group.name)
                for _, d in ipairs(node:GetDescendants()) do
                    register(d, group.name)
                end
                -- Connected after the walk, never before: a connection made
                -- first would fire for every descendant during the walk and
                -- register each one twice, and `seen` would only hide that,
                -- not the ordering bug behind it.
                connections[#connections+1] = node.DescendantAdded:Connect(function(d)
                    register(d, group.name)
                end)
            end
        end
    end
end

-- ========== REPORTING ==========
local function coverageReport()
    local out = {}
    out[#out+1] = '# coverage -- what this watcher has in front of it'
    out[#out+1] = string.format('# %d instances, %d watched properties, %d roots found, %d roots missing',
        #ents, totalProps, #report.found, #report.missing)
    out[#out+1] = string.format('# %d instance(s) needed a path suffix: their GetFullName was not unique',
        collisions)
    out[#out+1] = ''
    for _, group in ipairs(GROUPS) do
        local counts = report.byGroup[group.name] or {}
        local keys = {}
        local total = 0
        for k, v in pairs(counts) do keys[#keys+1] = k; total = total + v end
        table.sort(keys, function(a, b)
            if counts[a] ~= counts[b] then return counts[a] > counts[b] end
            return a < b
        end)
        out[#out+1] = string.format('## %s -- %d watched instances', group.name, total)
        for _, k in ipairs(keys) do
            out[#out+1] = string.format('   %-24s %d', k, counts[k])
        end
        out[#out+1] = ''
    end
    if #report.missing > 0 then
        out[#out+1] = '## roots NOT found -- the room is under-covered if this is not empty'
        for _, p in ipairs(report.missing) do out[#out+1] = '   MISSING ' .. p end
        out[#out+1] = ''
    end
    out[#out+1] = '## roots found'
    for _, r in ipairs(report.found) do
        out[#out+1] = string.format('   %-12s %-42s %-12s %d descendants',
            r.group, r.path, r.class, r.count)
    end
    return table.concat(out, NL) .. NL
end

local function inventory()
    local out = {}
    for _, ent in ipairs(ents) do
        out[#out+1] = string.format('%s | %s | %s | %s',
            ent.group, ent.inst.ClassName, ent.path, table.concat(ent.props, ' '))
    end
    return table.concat(out, NL) .. NL
end

local function summary()
    -- Sorted by the flat index, which is base + i - 1: because entries were
    -- appended in registration order their bases are ascending, so sorting on j
    -- sorts by room-then-path without ever building a path string to sort on.
    local keys = {}
    for _, ent in ipairs(ents) do
        for i = 1, #ent.props do
            local j = ent.base + i
            if hits[j] > 0 then keys[#keys+1] = j end
        end
    end
    table.sort(keys)
    -- base is zero-offset and the flat arrays are one-offset, so the entry
    -- owning j is the one whose base is the largest <= (j - 1).
    local order = {}
    for _, ent in ipairs(ents) do order[#order+1] = ent end
    table.sort(order, function(a, b) return a.base < b.base end)
    local out = {}
    out[#out+1] = string.format('# %d of %d watched properties have moved since start (t=%.1fs, scan %.0f ms)',
        #keys, totalProps, now() - startedAt, scanMs)
    if sinkDown then out[#out+1] = '# WARNING: the sink was unreachable at the last flush' end
    if dropped > 0 then out[#out+1] = string.format('# WARNING: %d queued change(s) were dropped', dropped) end
    out[#out+1] = ''
    local cursor = 0
    for _, j in ipairs(keys) do
        local target = j - 1
        while order[cursor + 1] and order[cursor + 1].base <= target do
            cursor = cursor + 1
        end
        local ent = order[cursor]
        local i = j - ent.base
        out[#out+1] = string.format('%-9s %s.%s = %s   [was %s, %d change(s)]',
            ent.group, ent.path, ent.props[i], fmt(vals[j]), fmt(org[j]), hits[j])
    end
    return table.concat(out, NL) .. NL
end

-- Everything judged ambient, and the count that got it there.  Kept separate
-- from changes.log on purpose: the point of dropping those keys is to stop them
-- filling the timeline, and a line per key announcing "still ambient" would
-- refill it with the same noise.  This file is the disclosure that makes the
-- drop honest rather than silent -- a key that is not in changes.log is named
-- here, so "absent from the log" and "never moved" can never be confused.
local function suppressedReport()
    local list = {}
    for j, s in pairs(ambient) do
        list[#list+1] = string.format('%-9s %s.%s   [%d change(s) by t=%.1fs, first move t=%.1fs]',
            s.ent.group, s.ent.path, s.ent.props[s.i], hits[j], s.tick, s.first)
    end
    table.sort(list)
    local out = {}
    out[#out+1] = string.format('# %d key(s) judged ambient: moved more than %d times without going quiet for %d scans (t=%.1fs)',
        #list, CONFIG.NoisyAfter, CONFIG.QuietScans, now() - startedAt)
    out[#out+1] = '# Their current values and change counts are still in summary.txt.'
    out[#out+1] = '# A key that IS in changes.log was judged the other way: it went quiet long'
    out[#out+1] = '# enough for its held lines to be written out, so logging it is not a guess.'
    out[#out+1] = ''
    for _, line in ipairs(list) do out[#out+1] = line end
    return table.concat(out, NL) .. NL
end

-- ambient is keyed by property index, not positioned, so # is meaningless on it
-- and has to be counted.
local function suppressedCount()
    local n = 0
    for _ in pairs(ambient) do n = n + 1 end
    return n
end

local function record(ent, i, old, new, stampText)
    local j = ent.base + i
    if hits[j] == 0 then
        movedKeys = movedKeys + 1
        firstTick[j] = tick
    end
    hits[j] = hits[j] + 1
    local prev = lastTick[j]
    lastTick[j] = tick
    local label = string.format('%s.%s', ent.path, ent.props[i])
    local line = string.format('%s | %-9s | %s | %s | %s',
        stampText, ent.group, label, fmt(old), fmt(new))
    if ambient[j] then
        -- Quiet ticks between the last move and this one.  tick - prev is the
        -- distance between moves, so a gap of one scan means zero quiet scans --
        -- which is why the band is compared against this and not against
        -- tick - prev.  Without it a key that moves on every OTHER scan re-arms
        -- on the quiet tick between two moves and would have its ring dropped
        -- and rebuilt forever, reporting a spinner that never stopped as one
        -- event per cycle: measured on run two, 2,211 announce pairs against
        -- 1,942 keys that were not clocks at all.
        local quietTicks = tick - prev - 1
        if quietTicks < CONFIG.QuietScans then
            -- Deliberately no summaryDirty here and nothing appended: while a
            -- spinner spins there is nothing new to say, and the ring has
            -- already been dropped, so this line is discarded on purpose.
            return
        end
        -- It went quiet for long enough to count as stopped.  A spinner that
        -- stops is an event, so the resume is announced, the key is logged
        -- normally again, and a fresh ring starts with this very move.
        judged[j] = 'discrete'
        held[j] = {}
        logLines[#logLines+1] = string.format(
            '%s | %-9s | %s | RESUMED after %d quiet scan(s) | %s',
            stampText, ent.group, label, quietTicks, fmt(new))
    end
    -- ===== THE HEART OF IT: HOLD, DO NOT WRITE-THEN-ERASE =====
    -- The first design wrote every line immediately and tried to take the
    -- ambient ones back once a key had moved enough times to prove what it was.
    -- That cannot work, and the measurement is unambiguous: the sink APPENDS, so
    -- by the time the ninth move tripped the rule, moves one through eight had
    -- already been flushed to disk.  Run four recorded 1,891 keys as "8 line(s)
    -- erased" while the file still held every one of those lines -- the erasure
    -- was real in memory and invisible on disk.  A line has to be withheld
    -- BEFORE it is written, not removed after, which is why this ring exists.
    --
    -- Overflowing the ring is the entire test, and there is no clock on it.  An
    -- earlier version promoted a key to "an event" a fixed number of scans after
    -- its first move if it had not overflowed by then, and that is wrong for
    -- exactly the keys this exists to catch: run three left 1,045 lines behind,
    -- led by two chamber fans at 47 and 46 lines each whose first move was
    -- followed by a 32-second gap.  They were certified as events before they
    -- had shown what they were.  Age is not evidence; the ring filling is.
    local list = held[j]
    list[#list+1] = line
    summaryDirty = true
    if #list > CONFIG.NoisyAfter then
        -- Named and dropped.  Nothing was written, so nothing has to be taken
        -- back -- the whole reason for holding.
        ambient[j] = {ent = ent, i = i, tick = tick, first = firstTick[j]}
        held[j] = nil
        suppressedDirty = true
    end
end

-- Writes out the held lines of every key that has gone quiet, which is the only
-- evidence there is that a run of moves was a thing that HAPPENED rather than a
-- thing that keeps happening.  Called once per scan, before the flush, so a key's
-- lines reach changes.log on the same tick they are released.
--
-- A full pass over `held` every scan is affordable because `held` only ever
-- holds keys with un-written lines: a key's ring is released on quiet and
-- dropped on overflow, so what is in here is at most the keys that moved in the
-- last QuietScans scans.
local function releaseQuiet()
    local released = 0
    for j, list in pairs(held) do
        -- The empty check comes FIRST and it is not an optimisation: `held` has
        -- an entry for every registered key, most of them empty, and a key that
        -- has never moved has no lastTick to subtract from -- so testing the age
        -- before testing the list is an arithmetic-on-nil error on the very first
        -- scan, inside a spawned thread, where nothing catches it and the whole
        -- loop dies without writing another byte.  Measured: that is exactly what
        -- happened on the first run of this design, which stopped after rooms.txt
        -- and inventory.txt and never produced a summary or a timeline at all.
        if #list > 0 and lastTick[j] and tick - lastTick[j] > CONFIG.QuietScans then
            for k = 1, #list do logLines[#logLines+1] = list[k] end
            -- Emptied in place rather than replaced: register() only builds this
            -- table once per key, and a table per release would be one
            -- allocation per key per burst for the whole run.
            for k = #list, 1, -1 do list[k] = nil end
            judged[j] = 'discrete'
            released = released + 1
        end
    end
    return released
end

-- ========== THE SCAN ==========
local function scan()
    local t0 = os.clock()
    local st = stamp()
    for _, ent in ipairs(ents) do
        local inst = ent.inst
        -- Reading a property off a destroyed instance is fine; its Parent just
        -- goes nil.  Reported once and then the entry is retired, so a part that
        -- is rebuilt mid-run does not read as a silent no-op forever.
        if inst.Parent == nil and ent.live ~= false then
            ent.live = false
            logLines[#logLines+1] = string.format('%s | %-9s | %s | DESTROYED',
                st, ent.group, ent.path)
            summaryDirty = true
        elseif ent.live ~= false then
            local props = ent.props
            local base = ent.base
            for i = 1, #props do
                local v = inst[props[i]]
                local j = base + i
                if v ~= vals[j] then
                    record(ent, i, vals[j], v, st)
                    vals[j] = v
                end
            end
        end
    end
    -- After the walk, not before: a key that moved on this very scan has
    -- lastTick = tick, so releasing first would leave it held for one extra scan
    -- after every move and slow the whole log down by a tick.  Releasing here
    -- means the ring of a key whose last move was QuietScans ago goes out on the
    -- scan that makes it quiet -- the earliest scan at which it is true.
    releaseQuiet()
    scanMs = (os.clock() - t0) * 1000
end

-- Writes out whatever is still held at the end of a run.  Normally a key's ring
-- is released by releaseQuiet a few scans after it stops moving, so this only
-- catches keys that were still moving when the run ended -- but those are exactly
-- the keys near the END of a shift, and losing them would lose the most
-- interesting part of the timeline to a bookkeeping detail.  Called at Stop and
-- Report, and safe to call twice: the second call finds `held` empty.
local function drainHeld()
    local pending = {}
    for j, list in pairs(held) do
        if #list > 0 then pending[#pending+1] = {tick = firstTick[j], list = list} end
        held[j] = {}
    end
    -- Sorted by each key's first move rather than left in pairs() order, because
    -- a drain has no better ordering information and unordered output would read
    -- as if the moves were simultaneous.  Sorted on the tick NUMBER and not on
    -- the stamp text inside the lines: the stamp is a string, and 't=9.5' sorts
    -- after 't=10.2' lexically.  The order within one key's ring is already
    -- correct, so it is left alone.
    table.sort(pending, function(a, b) return (a.tick or 0) < (b.tick or 0) end)
    for _, item in ipairs(pending) do
        local list = item.list
        for k = 1, #list do logLines[#logLines+1] = list[k] end
    end
end

-- The clock is read once per scan, not once per change.  A single tick can move
-- thousands of properties, and stamping each one separately would both cost a
-- syscall each and report them as spread over a second in which they all moved
-- together -- which reads as a timeline and is not one.
local function flush(force)
    if #logLines > 0 then
        post('changes.log', table.concat(logLines, NL) .. NL, true)
        logLines = {}
    end
    -- Both files on the same throttle, each with its own dirty flag: a key that
    -- trips calls for a new suppressed.txt, but rewriting two large files every
    -- second is the sort of cost that shows up as jitter in the very timings
    -- this watcher exists to measure.
    local due = force or (tick % CONFIG.SummaryEvery == 0)
    if summaryDirty and due then
        summaryDirty = false
        post('summary.txt', summary(), false)
    end
    if suppressedDirty and due then
        suppressedDirty = false
        post('suppressed.txt', suppressedReport(), false)
    end
end

-- ========== PUBLIC ==========
local RoomWatch = {}

-- One census, no loop.  Written so that "what is in these two rooms" can be
-- answered in Edit mode, where no server script runs at all and the only way in
-- is to require this module and call this.
function RoomWatch.Snapshot()
    startedAt = now()
    buildIndex()
    local rooms = coverageReport()
    local inv = inventory()
    post('rooms.txt', rooms, false)
    post('inventory.txt', inv, false)
    return string.format('watched=%d props=%d roots=%d missing=%d rooms=%d bytes inv=%d bytes',
        #ents, totalProps, #report.found, #report.missing, #rooms, #inv)
end

-- Force the summary out now, whether or not anything has moved since the last
-- one.  This is what Stop() calls, and it is the difference between a summary
-- that is current and a summary that is merely the last time something happened.
function RoomWatch.Report()
    -- Everything this run is still holding goes out first, then one forced
    -- flush writes all three files.  Both dirty flags are set by hand because a
    -- forced flush only skips the throttle, not the "has anything changed"
    -- question -- and the point of a Report is to answer that question with a
    -- file that is current rather than with one that is merely the last time
    -- something happened.
    drainHeld()
    summaryDirty = true
    suppressedDirty = true
    flush(true)
    return #ents, totalProps, movedKeys, suppressedCount()
end

function RoomWatch.Start()
    if running then return false, 'already running' end
    running = true
    startedAt = now()
    task.spawn(function()
        buildIndex()
        print(string.format('[RoomWatch] watching %d instances / %d properties across %d roots (%d missing)',
            #ents, totalProps, #report.found, #report.missing))
        post('rooms.txt', coverageReport(), false)
        post('inventory.txt', inventory(), false)
        -- Written up front even though it is empty, so that a reader who finds
        -- no suppressed.txt learns "nothing was suppressed" from a file rather
        -- than from its absence.
        post('suppressed.txt', suppressedReport(), false)
        while running do
            task.wait(CONFIG.Interval)
            tick = tick + 1
            -- Guarded, and the guard writes a file.  A diagnostic that dies from
            -- its own bug is worse than no diagnostic, and the failure mode is
            -- silent by construction: the loop lives in a spawned thread, so
            -- nothing awaits it, nothing catches it, and the only symptom is that
            -- the files stop growing.  That is unattributable from outside -- it
            -- looks identical to a watcher that is running and finding nothing --
            -- and it is exactly how this file behaved on the first run of the ring
            -- design, when an arithmetic-on-nil in releaseQuiet killed the loop
            -- after two files and I could only tell by the absence of a third.
            -- So the error goes to the sink, where it survives the session.
            local walked, walkErr = pcall(scan)
            if not walked then
                fatal = tostring(walkErr)
                post('error.txt', string.format(
                    '# the watcher stopped on tick %d (t=%.1fs)' .. NL .. '%s', tick,
                    now() - startedAt, fatal), false)
                warn('[RoomWatch] scan failed on tick ' .. tick .. ': ' .. fatal)
                running = false
                break
            end
            if #logLines > CONFIG.MaxQueue then
                -- table.remove(_, 1) is O(n) and would turn a bounded queue into
                -- a quadratic stall exactly when the sink is down and the queue
                -- is longest, so the overflow is dropped by rebuilding once.
                local keep = {}
                for k = #logLines - CONFIG.MaxQueue + 1, #logLines do
                    keep[#keep+1] = logLines[k]
                end
                dropped = dropped + (#logLines - #keep)
                logLines = keep
                -- Nothing else has to be told.  Only a released ring ever reaches
                -- logLines, and a released ring is emptied as it is written, so
                -- no hold points into this table -- which is the reason holding
                -- pays for itself twice: it is what makes suppression possible at
                -- all, and it is what makes a truncated queue safe.  `held`
                -- cannot grow without bound in exchange: a ring is capped at
                -- NoisyAfter lines, so the worst case is 8 per key no matter how
                -- long the sink stays down.
            end
            flush(false)
            if tick % CONFIG.ReportEvery == 0 then
                print(string.format('[RoomWatch] t=%.0fs tick=%d scan=%.0fms moved=%d ambient=%d queued=%d dropped=%d sink=%s',
                    now() - startedAt, tick, scanMs, movedKeys, suppressedCount(), #logLines, dropped,
                    sinkDown and 'DOWN' or 'ok'))
            end
        end
        -- Last thing the loop does, in this order: whatever is still being held
        -- becomes a line, and then one forced flush writes it out with the rest.
        drainHeld()
        flush(true)
    end)
    return true
end

function RoomWatch.Stop()
    running = false
    for _, c in ipairs(connections) do c:Disconnect() end
    connections = {}
    return true
end

-- Cheap enough to call every tick and the only way to tell a watcher that is
-- watching from a watcher that is merely loaded.
function RoomWatch.Status()
    return string.format('running=%s tick=%d watched=%d props=%d moved=%d ambient=%d queued=%d dropped=%d scan=%.0fms sink=%s fatal=%s',
        tostring(running), tick, #ents, totalProps, movedKeys, suppressedCount(), #logLines, dropped,
        scanMs, sinkDown and 'DOWN' or 'ok', fatal or 'none')
end

return RoomWatch
