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
-- line that is indistinguishable from a lever being thrown.  So a key's first
-- moves are held back, unjudged, for HoldScans; if by then it has moved more
-- than NoisyAfter times it is decoration and its held lines are discarded, and
-- if it has not it is an event and those lines plus every later one are written.
-- Nothing is ever un-written, and nothing is lost either: summary.txt keeps
-- every moved key's current value, its start value and its full change count
-- whether or not its timeline survived.  What is dropped is repetition.
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
    -- A key that has moved more than this many times during the run is not
    -- reporting an operator action, it is reporting ambient motion.  Measured on
    -- the first live run: 40 spinning antenna parts produced 66,425 of 66,884
    -- lines while the 56 keys that carried actual events produced the other 459.
    -- Such a key never reaches changes.log at all: its lines are held back while
    -- it is being judged and dropped if it turns out to be ambient, and it is
    -- named in suppressed.txt instead.  Its value and its change count stay live
    -- in summary.txt.  If it then goes quiet for
    -- QuietScans it is announced as RESUMED, logged normally again, and can be
    -- judged again on what it does next.  A spinner that stops is an event; a
    -- spinner that is still spinning is not.
    --
    -- The count is LIFETIME, not consecutive, and that is a measured choice
    -- rather than an assumption.  Consecutive looks like the honest test for "is
    -- this a clock" and is not: this place moves in bursts.  Measured on the
    -- third live run, ~1,940 keys -- the whole CoreAntenna structure -- wrote a
    -- line on each of ticks 4, 8, 27, 28, 29, 30, 32, 33 and no others, so a
    -- run-length test never reached nine anywhere and suppressed three keys out
    -- of 1,952 while the log stayed at 7.88 MB.  Two earlier versions failed on
    -- the same question from opposite sides: counting lifetime changes but
    -- re-arming after one quiet tick produced 2,211 announce/resume pairs on
    -- keys that were not clocks at all, and counting consecutive scans found no
    -- clocks at all.  Neither of those is detectable by reading the code -- both
    -- look correct -- which is why the number is here rather than defended in
    -- prose.
    NoisyAfter = 8,
    -- A key is judged once, this many scans after its first move: by then it has
    -- either already moved more than NoisyAfter times (ambient, and it is
    -- discarded) or it has not (discrete, and every move it has made is written
    -- out and every later move is written live).  Its lines are HELD in memory
    -- until then, which is the whole trick -- see record() for why holding is
    -- the only thing that works.
    HoldScans = 12,
    -- How many consecutive quiet scans an ambient key must show before it is
    -- announced as RESUMED.  Without a band, a key that moves on every OTHER
    -- scan re-arms on the quiet tick between two moves and toggles forever at
    -- two lines per cycle: measured on the second live run, 2,211 announce
    -- pairs against 1,942 keys that were not clocks at all.  Five is chosen
    -- against the measured tick of this place, where the genuinely intermittent
    -- spinners leave gaps of one to three scans and operator-driven keys are
    -- quiet for far longer than five.
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
-- j -> the lines this key has written that have NOT been written out yet.  A key
-- that has not been judged keeps its lines here rather than in logLines, because
-- the only way to un-write a line is to never have written it: the sink appends,
-- so a line that reaches it is there for good.  See record().
local held = {}
-- j -> 'discrete' once a key has been judged an event, or 'ambient' once it has
-- been judged decoration.  Absent means "not judged yet, and its lines are in
-- held".  A key is never re-judged except by the resume rule in record().
local judged = {}
-- j -> the tick of this key's first move, which is when its clock starts.
local firstTick = {}
-- j -> {ent, i, tick, first} for every key currently judged ambient.  These do
-- NOT go into changes.log: a line per ambient key would be ~1,900 lines of
-- "nothing happened here", which is the same noise it replaced.  They are the
-- whole content of suppressed.txt, rewritten on the summary throttle.
local ambient = {}
local suppressedDirty = false
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
    out[#out+1] = string.format('# %d key(s) judged ambient: moved more than %d times within %d scans of their first move (t=%.1fs)',
        #list, CONFIG.NoisyAfter, CONFIG.HoldScans, now() - startedAt)
    out[#out+1] = '# Their current values and change counts are still in summary.txt.'
    out[#out+1] = '# A \'discrete\' key in changes.log was judged the other way: it had not'
    out[#out+1] = '# moved that many times by the end of its hold, so it is logged in full.'
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
    local state = judged[j]
    if state == nil then
        -- ===== THE HEART OF IT: HOLD, DO NOT WRITE-THEN-ERASE =====
        -- The first design wrote every line immediately and tried to take the
        -- ambient ones back once a key had moved enough times to prove what it
        -- was.  That cannot work, and the measurement is unambiguous: the sink
        -- APPENDS, so by the time the ninth move trips the rule, ticks one
        -- through eight have already been flushed to disk.  Run four recorded
        -- 1,891 keys as "8 line(s) erased" while the file still held every one
        -- of those lines -- the erasure was real in memory and invisible on
        -- disk.  A line has to be withheld BEFORE it is written, not removed
        -- after, which is why this branch exists at all.
        --
        -- The judgement is by COUNT, not by consecutive scans, and that is also
        -- measured rather than assumed.  This place moves in bursts: on run
        -- three, ~1,940 keys -- the whole CoreAntenna structure -- wrote a line
        -- on each of ticks 4, 8, 27, 28, 29, 30, 32 and 33 and no others, so a
        -- run-length test never reached nine anywhere and judged three keys out
        -- of 1,952 while the log stayed at 7.88 MB.
        --
        -- So: hold every line this key writes.  If it has moved more than
        -- NoisyAfter times by the end of its hold it is decoration, its held
        -- lines are dropped, and it is named in suppressed.txt.  Otherwise it is
        -- an event, its held lines are written in order, and every later move is
        -- written the moment it happens.  Nothing is ever un-written, so nothing
        -- can be lost -- the only cost is that a discrete key's first moves
        -- reach the log HoldScans later than they happened, together.
        local list = held[j]
        list[#list+1] = line
        summaryDirty = true
        if hits[j] > CONFIG.NoisyAfter then
            judged[j] = 'ambient'
            held[j] = nil
            ambient[j] = {ent = ent, i = i, tick = tick, first = firstTick[j]}
            suppressedDirty = true
        elseif tick - firstTick[j] >= CONFIG.HoldScans then
            judged[j] = 'discrete'
            held[j] = nil
            for k = 1, #list do logLines[#logLines+1] = list[k] end
        end
        return
    elseif state == 'ambient' then
        -- Quiet ticks between the last move and this one.  tick - prev is the
        -- distance between moves, so a gap of one scan means zero quiet scans --
        -- which is why the band is compared against this and not against
        -- tick - prev.  Without it a key that moves on every OTHER scan re-arms
        -- on the quiet tick between two moves: measured on run two, 2,211
        -- announce pairs against 1,942 keys that were not clocks at all.
        local quietTicks = tick - prev - 1
        if quietTicks < CONFIG.QuietScans then
            -- Deliberately no summaryDirty here: while a spinner spins there is
            -- nothing new to say, and marking it dirty would rewrite the whole
            -- summary every second to say it.
            return
        end
        judged[j] = 'discrete'
        ambient[j] = nil
        logLines[#logLines+1] = string.format(
            '%s | %-9s | %s | RESUMED after %d quiet scan(s) | %s',
            stampText, ent.group, label, quietTicks, fmt(new))
        summaryDirty = true
        return
    end
    logLines[#logLines+1] = line
    summaryDirty = true
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
    scanMs = (os.clock() - t0) * 1000
end

-- Writes out the held lines of every key that never got judged, and clears the
-- hold table.  A key is judged HoldScans after its first move, so this only
-- matters for keys that first moved within the last HoldScans of the run -- but
-- those are exactly the keys near the END of a shift, and losing them would lose
-- the most interesting part of the timeline to a bookkeeping detail.  Called at
-- Stop and Report, and safe to call twice: the second call finds `held` empty.
local function drainHeld()
    local pending = {}
    for j, list in pairs(held) do
        if #list > 0 then pending[#pending+1] = list end
        held[j] = {}
    end
    -- Sorted by the tick of each key's first line rather than left in pairs()
    -- order, because a hold that is drained at the end has no better ordering
    -- information and unordered output would read as if the moves were
    -- simultaneous.  Every line already carries its own stamp, so this is
    -- cosmetic -- but it is the difference between a file that parses as a
    -- timeline and one that has to be sorted before it can be read.
    table.sort(pending, function(a, b) return a[1] < b[1] end)
    for _, list in ipairs(pending) do
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
            scan()
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
                -- Nothing else has to be told.  The dropped lines were already
                -- judged discrete, so no hold or ambient record points into this
                -- table any more -- which is the reason holding pays for itself
                -- twice: it is what makes suppression possible at all, and it is
                -- what makes a truncated queue safe.  `held` cannot grow without
                -- bound in exchange, because a held key is judged on a clock.
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
    return string.format('running=%s tick=%d watched=%d props=%d moved=%d ambient=%d queued=%d dropped=%d scan=%.0fms sink=%s',
        tostring(running), tick, #ents, totalProps, movedKeys, suppressedCount(), #logLines, dropped,
        scanMs, sinkDown and 'DOWN' or 'ok')
end

return RoomWatch
