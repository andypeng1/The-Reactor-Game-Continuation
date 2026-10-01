-- TRG_original_watch.luau -- a read-only census, change log and audio log for the
-- ORIGINAL game (placeId 17596243941), injected with Solara V3.
--
-- WHY THIS IS NOT room_watch.luau.  room_watch.luau is a ModuleScript pair that
-- runs inside OUR place and watches two rooms whose paths I wrote myself.  This
-- file is the same idea in the opposite situation in every respect:
--
--   * It runs in a place I have never seen the tree of.  The only paths I have
--     are the ones the recorder has already proved exist --
--     Workspace.Consoles.MainReactorConsole.StartUpBigLever.{Start,Shut}ClickPart,
--     Workspace.Monitors*, Workspace.MonitorsFacility*, Workspace.Stats.* -- and
--     none of them is the reactor chamber, whose name I do not know.
--   * So it does NOT start from a list of roots.  It starts from a CENSUS: every
--     direct child of Workspace is named, classed and counted into tree.txt
--     before a single property is watched, and the roots it does watch are chosen
--     out of that census by a rule that is printed in rooms.txt next to the
--     result.  The first injection is expected to TEACH us the tree; the second
--     can pin the two rooms by name in CONFIG.Pinned and cost a fraction of the
--     instances.  Guessing the root names now would produce a watcher that
--     reports a quiet room and looks healthy -- the exact failure this file is
--     written to avoid.
--   * It has to fit in one file with no require, because there is nothing over
--     there to require.  It does not touch ReactorBackend, Config or Engine.
--
-- WHAT IT IS FOR.  The start-up chain is the one thing we cannot reproduce from
-- our own source: the operator throws one lever and ninety seconds later the
-- machine has configured itself -- pumps, CBLs, fans, in an order, with sounds --
-- and that order exists in no file of ours.  The recorder gives the readings at
-- four samples a second; this gives the ROOM and the AUDIO, which is where the
-- order is actually visible.  Two files, two questions, both read-only.
--
-- WHAT IT IS NOT.  There is no property assignment to a watched instance
-- anywhere below.  Everything is a property get or a signal connection.  The only
-- thing it creates is its own HTTP requests -- it used to build a ScreenGui too,
-- and that is gone: the operator's instruction, 2026-09-27, was that nothing
-- should be shown on screen or printed to the developer console, and that
-- everything it has to say goes to a file.  health.txt is where all of it went.
--
-- WHERE THE DATA GOES.  Same sink as the recorder -- receive.py on 8765, whose
-- directory is D:/rblxTRGproject/Data -- under its own name prefix, so one
-- terminal serves both and the two products stay separable by filename alone:
--
--   Data/originalwatch/<stamp>/tree.txt         once.  The census of Workspace,
--                                               largest root first, plus the
--                                               children of anything too big to
--                                               watch.  THIS is what answers
--                                               "where is the control room".
--   Data/originalwatch/<stamp>/rooms.txt        once.  Which roots were chosen,
--                                               by what rule, what each holds by
--                                               class, and what was refused.
--   Data/originalwatch/<stamp>/inventory.txt    once.  Every watched instance and
--                                               the property names read off it.
--   Data/originalwatch/<stamp>/summary.txt      rewritten.  One line per property
--                                               that has moved since start.
--   Data/originalwatch/<stamp>/changes.log      appended.  The timeline.
--   Data/originalwatch/<stamp>/suppressed.txt   rewritten.  Everything judged
--                                               ambient, with the count that got
--                                               it there.  This is the file that
--                                               makes changes.log's silence
--                                               honest rather than ambiguous.
--   Data/originalwatch/<stamp>/audio.txt        appended.  Playback events.
--   Data/originalwatch/<stamp>/audio_tally.txt  rewritten.  One line per sound
--                                               that has actually been audible.
--   Data/originalwatch/<stamp>/health.txt       rewritten every ReportEvery
--                                               scans.  Is it still watching, and
--                                               is the sink still taking it.  This
--                                               is the file that replaced the
--                                               on-screen panel and every print:
--                                               t= advancing between two copies is
--                                               the liveness signal, and
--                                               sink_error= is the reason a silent
--                                               run is silent.  Same information
--                                               the console used to get, written
--                                               where it survives the session.
--   Data/originalwatch/<stamp>/window.txt       rewritten.  WHEN this run was
--                                               being recorded, and what was not.
--                                               The operator's rule: 「我进控制室
--                                               之后，按下开机拉杆开始记录，游戏
--                                               时间到12：00结束记录」 -- so
--                                               changes.log and audio.txt are
--                                               withheld until the start-up lever
--                                               is clicked and stop when the shift
--                                               dial reads 12:00.  This file is
--                                               OUTSIDE that gate (it is the file
--                                               that explains the gate), and it
--                                               records whether the lever hook
--                                               actually took -- the one thing
--                                               that cannot be repaired after the
--                                               shift.  Two WINDOW lines also go
--                                               into changes.log itself, so the
--                                               timeline says where it starts
--                                               meaning without a second file
--                                               having to be opened.
--   Data/originalwatch/<stamp>/hello.txt        once, and BEFORE the census.
--                                               The only artifact that exists
--                                               before anything has been walked,
--                                               so "was it even injected" is
--                                               answered by bytes and not by a
--                                               guess.  See the note at Start.
--   Data/originalwatch/<stamp>/error.txt        ONLY if the watcher died, and
--                                               its absence is therefore a claim.
--                                               Its first line says WHICH walk
--                                               died -- the start-up or a scan --
--                                               because those are two different
--                                               diagnoses off one file.
--
-- HOW TO RUN IT.  Two servers (the recorder's own, unchanged):
--
--   python _tools/receive.py --port 8765 --dir D:/rblxTRGproject/Data
--   python -m http.server 8766 --bind 127.0.0.1 --directory _tools
--
-- then in the original game, on the CLIENT after you have joined a shift:
--
--   loadstring(game:HttpGet('http://127.0.0.1:8766/TRG_original_watch.luau'))()
--
-- Re-injecting is safe: a second injection stops the first one instead of
-- running two watchers against one sink.
--
-- HOTKEYS, while it runs:  RightAlt = write every file out now.
--                          RightControl = stop.
--   NOT RightShift.  The recorder binds that one to SEAL, i.e. to ending its own
--   run, and both scripts run together on an attempt the operator gets once.
--
-- THE ONE RULE THAT CARRIES OVER FROM THE RECORDER.  Only changed values are
-- written; an instance that never moves appears in inventory.txt (coverage) and
-- never in summary.txt (state).  That is what makes summary.txt readable after a
-- start-up, when a few hundred things out of twenty thousand have moved.

local HttpService = game:GetService('HttpService')
-- Players was here for the panel's PlayerGui.  With the panel gone it is not asked
-- for at all, which is also one fewer service a stub has to provide.
local UserInputService = game:GetService('UserInputService')

local CONFIG = {
    -- WHICH BUILD THIS IS, and it is printed into every artifact that names the run.
    --
    -- The operator's 2026-09-27 report was made with a copy of this file OLDER than
    -- the fixes it was being read as testing: his capture is 12:41:40 and the
    -- shipped watcher's mtime was 13:54:07, so the Phase 57 window and boundary work
    -- had never run in the original game at all, while the silence it produces looks
    -- exactly like the silence of a watcher that was never injected.  A byte count
    -- cannot settle that -- the file the operator holds is a copy I cannot read --
    -- so the tag settles it instead: the artifacts say which build wrote them, and
    -- 'the tag in your file is not the tag I gave you' is answerable at the reading
    -- end, by the operator, without me.
    -- w59: the lever hook is attached before the census instead of after it (it was
    -- arriving 28 s late and the window never opened), and MaxQueue went 4000 -> 20000
    -- because the first real run dropped 794 lines of its own start-up.
    -- w60: the window now closes on the 12:00 PM HANDOVER -- the dial falling from
    -- 1439 to 0 -- instead of on a threshold at midnight, which was the wrong end of
    -- the shift; and the two monitor containers are pinned, so 「所有监视器的GUI也要！」
    -- is a guarantee instead of a near miss on the root budget.
    -- w61: the lag fix.  The first run to watch the whole original place measured
    -- scan_ms=2197 against Interval=1 -- ~70% of the client -- and the operator
    -- reported the game as unplayable.  Three walks now yield every MaxBlockMs of
    -- solid work, and the loop sleeps until its share of the wall clock is at most
    -- DutyTarget.  health.txt reports scan_ms / sleep_ms / duty / yields so the cure
    -- is measurable on the machine that complained rather than asserted here.
    Build = 'w61',
    -- The recorder's sink.  receive.py's --dir is Data/, so a name of
    -- 'originalwatch/<stamp>/rooms.txt' lands in Data/originalwatch/<stamp>/.
    Sink = 'http://127.0.0.1:8765/',
    -- Seconds between scans.  Measured on the room watcher in our own place: 112
    -- ms for 30,219 instances / 235,553 properties, so the budget below is set to
    -- keep a scan near 300 ms -- a diagnostic that eats a third of a heartbeat is
    -- tolerable, one that eats all of it is a second game.
    Interval = 1,
    -- ---- THE LAG FIX (2026-10-01) ----
    -- The operator's report after the first run that watched the whole original
    -- place: 「我注入之后游戏贼卡」.  The numbers behind it, from that run's own
    -- health.txt: scan_ms=2197 for 71587 instances / 559942 properties, against
    -- Interval=1 -- so the loop was asking for two and a fifth seconds of solid work
    -- every three and a fifth seconds.  About 70% of the client went into this
    -- watcher, and the recorder beside it measured ITSELF at cpu_pct=10.9, so the
    -- split is not a guess about which half to fix.
    --
    -- The comment above Interval says the budget is "set to keep a scan near
    -- 300 ms".  That was calibrated on OUR place (30219 instances / 235553
    -- properties, 112 ms); the original has three times that and the same budget
    -- admits 80000 of it.  The claim was not wrong when it was written, it was
    -- wrong about this place -- which is why the two knobs below are measured
    -- rather than chosen, and why health.txt reports what they actually did.
    --
    -- TWO KNOBS, because there are two different harms here and they need different
    -- remedies.
    --
    -- MaxBlockMs bounds the LONGEST uninterrupted slice.  The scan yields to the
    -- scheduler once the current slice has run this long, so input and rendering get
    -- a frame: the 2.2 s freeze becomes ~90 short ones.  That is the harm the
    -- operator feels as a stutter, and it costs wall time, because every yield waits
    -- for a frame.  It is a time budget and not a count of instances on purpose: a
    -- slice's cost depends on the machine and on the class mix, and the same file
    -- also runs in the fixture, where a whole scan is under a millisecond.
    --
    -- DutyTarget caps the fraction of the wall clock the watcher may occupy at all.
    -- Yielding alone CANNOT fix a 70% duty cycle -- the same two seconds of work
    -- still has to happen, and spreading it over more frames spreads the hurt
    -- rather than removing it.  So the loop sleeps until scan/(scan+sleep) is at
    -- most this, derived from the measured scan rather than from a constant: a fixed
    -- sleep is invisible on a small place and useless on one twice this size.
    --
    -- 0.30 leaves the game two thirds of the client.  The price is resolution and it
    -- is paid in public: the measured period lands in health.txt as scan_ms,
    -- sleep_ms, duty and yields, so the next run states what it cost instead of this
    -- comment claiming it.  Raising DutyTarget buys resolution back and buys the
    -- stutter with it; that trade is the operator's, not this file's.
    MaxBlockMs = 25,
    DutyTarget = 0.30,
    -- HttpService:PostAsync refuses a body over 1024 KB, so every artifact is
    -- split on line boundaries under this.  Line boundaries and not byte offsets:
    -- a split inside a UTF-8 sequence produces a file that is not the text sent.
    Chunk = 900000,
    -- Bounded so a sink outage cannot grow a queue without bound, and counted
    -- rather than silently dropped -- a truncated log that does not say it was
    -- truncated is worse than no log.
    --
    -- RAISED FROM 4000 on 2026-09-30, because 4000 turned out to be smaller than a
    -- single tick of the thing this watcher exists to watch.  The first real run
    -- (originalwatch/260930-200834) reported `dropped=794` over one start-up, and the
    -- BOUND ONLY BITES WHEN THE WINDOW IS SHUT -- flush() posts nothing while
    -- windowState is 'waiting', so the queue grows instead of draining and the cap
    -- truncates a stream that was never going to be posted.  The truncation is
    -- oldest-first, so what went was the front of the run.  The new number is the
    -- measured worst case with room over it: 10439 lines in 46 s, of which 6463
    -- landed in one 10 s bin around the CBL firing, i.e. a power-up's peak is
    -- thousands of lines in a few ticks and a queue that holds only 4000 loses the
    -- beginning of every one of them.  20000 lines is ~4 MB at the observed 190
    -- bytes per line, against a place that already holds 557548 watched properties.
    MaxQueue = 20000,
    ReportEvery = 30,
    -- THE WHOLE TEST: a key may hold this many of its lines back at once, and a
    -- key that fills the ring has moved more times in a row than any single
    -- operator action produces.  Overflowing IS the proof; there is no clock and
    -- no second threshold to go wrong.  See record().
    NoisyAfter = 8,
    -- How many quiet scans before held lines are written out.  Not a clock on the
    -- key's age: a lever animates and then stops, so "it stopped" is exactly the
    -- evidence that it was an operator action, and that evidence only exists
    -- afterwards.
    QuietScans = 5,
    SummaryEvery = 10,
    -- ---- ROOT SELECTION ----
    -- Watch these by name even if the census rule would not have.  Empty means
    -- pure discovery, which is the correct setting for the FIRST injection into a
    -- place whose tree nobody has dumped.  After tree.txt is read, names belong
    -- here and the budget below stops mattering.
    --
    -- `Alarms` is pinned on the OPERATOR's word, not on a guess: he read the path
    -- off the original himself.  Our own copy of that place holds it as a Folder
    -- with 2,334 descendants under eight room-named children -- Rad,
    -- ReactorChamber, ControlRoom, Coolant, Facility, ReactorLounge, Gravatron,
    -- Mainframe -- plus one loose Sound, and 99 Sounds with 213 SoundEffects
    -- inside.  That is a census-sized root, not a giant; but Workspace as a whole
    -- is ~92,000 instances against a TotalBudget of 80,000, so the budget WILL run
    -- out somewhere in the smallest-first order, and whether it runs out before or
    -- after this root is not something the one injection the operator gets should
    -- have to gamble on.  Pinning does not shortcut the census: tree.txt still
    -- lists every direct child, and rooms.txt prints this list under "pinned by
    -- name", so the exemption is stated in the product rather than implied by it.
    --
    -- The two MONITOR containers are pinned on the same argument and for a stronger
    -- reason: on 2026-09-30 the operator asked for 「所有监视器的GUI也要！」, and a
    -- requirement that is met only when the budget happens to reach it is not met.
    -- Both names were READ OFF the live place rather than guessed -- the 2026-09-30
    -- run's rooms.txt carries `## Monitors (Folder) -- 1754 descendants, 1648 watched
    -- instances` and `## MonitorsFacility (Folder) -- 3578 descendants, 3429 watched`
    -- -- and both were inside the budget on that run, so pinning them changes nothing
    -- today.  That is the point: it makes the coverage independent of how many small
    -- roots the place happens to have next time.  The screens ARE the power-up, so
    -- they are the one thing in this watch set that must not be a near miss: that run
    -- logged 176 monitor changes, from `...TimeFrame.TimeLabel.Text 11:51 PM -> 11:52
    -- PM` to six of the seven `StatusLabel`s flipping OFF -> ON together.
    --
    -- Note what is NOT here: the three roots the 2026-09-30 run actually skipped
    -- (`CullFolder` 29529, `MovingParts` 25790, `QuantumMainframe` 12611, all "no
    -- budget left").  Pinning is free for a root that already fits and expensive for
    -- one that does not, so the giants stay a decision rather than an assumption --
    -- rooms.txt names them every run, which is what that section is for.
    Pinned = {'Alarms', 'Monitors', 'MonitorsFacility'},
    -- Never walk these, whatever else says to.  A refused root is REPORTED in
    -- rooms.txt, never silently skipped: an absent root and an empty root look
    -- identical from the outside, and only one of them is a bug.
    Deny = {},
    -- A direct child of Workspace with more descendants than this is not watched;
    -- it is reported, with its own direct children counted, so the next injection
    -- can go one level deeper instead of guessing.
    PerRootBudget = 30000,
    -- Ceiling on the whole watch set.  Roots are considered SMALLEST FIRST, so
    -- the budget is spent on the many small things and the SKIPPED list is the
    -- few giants -- which is the way round that makes the skip list readable.
    TotalBudget = 80000,
    -- A root with no descendants is still watched: it costs nothing, and a script
    -- that populates it later is exactly what DescendantAdded is for.
    WatchEmptyRoots = true,
    -- Depth of the child breakdown printed for a root that was too big to watch.
    DrillDepth = 1,
    -- ---- THE RECORDING WINDOW ----
    -- The operator's own rule, 2026-09-27, in answer to "何时记录？何时结束记录？":
    -- 「我进控制室之后，按下开机拉杆开始记录，游戏时间到12：00结束记录」
    --
    -- So the timeline does not run from injection to the stop key any more.  It runs
    -- from the start-up lever to the clock reaching 12:00 -- and "12:00" is NOON, the
    -- 11:59 AM -> 12:00 PM handover the dial shows as 1439 -> 0.  The 2026-09-30
    -- statement 「何时结束？：时钟到达12PM时结束」 settles the one thing 「12：00」
    -- could not by itself: 12:00 AM (midnight, dial 720) is the START of the shift --
    -- it is where `Stats.GameActive` goes true -- so a window ending there would end
    -- ten dial minutes after the lever, before anything had happened.  Noon is the
    -- other end of the same shift.  The part before the lever is not recorded as a
    -- timeline at all.  What is NOT lost by that: the
    -- state files (summary.txt, inventory.txt, audio_tally.txt) are not gated, so
    -- every property that moved before the lever is still there with its count and
    -- its current value -- only the pre-window TIMELINE goes, and that is exactly
    -- the part the operator said he did not want.  The count of what was withheld
    -- is in window.txt, so a reader can tell "nothing happened before the lever"
    -- from "a lot happened and was withheld" without another injection.
    Window = {
        Enabled = true,
        -- THE HANDOVER IS THE DIAL WRAPPING, NOT A THRESHOLD.  12:00PM maps to 0 and
        -- the dial counts up to 11:59AM at 1439, so the end of the interval the
        -- operator asked to record (「按下开机拉杆开始记录，游戏时间到12：00结束记录」,
         -- and on 2026-09-30: 「何时结束？：时钟到达12PM时结束」) is the moment the
        -- label goes 11:59 AM -> 12:00 PM and the number FALLS from 1439 to 0.  A
        -- threshold cannot express that: `mins >= 0` is true on every scan of every
        -- run.  What is stored here is therefore the size of the fall that counts as
        -- the handover, not a value to compare against.
        --
        -- 60 is chosen so that nothing but the wrap can produce it.  The dial is
        -- MONOTONIC inside a shift -- 710 at t=6.5 to 717 at t=92.4 in the watcher's
        -- own run, and 710 to 0 at t=828.87 in the recorder's 260926-230049 -- so the
        -- only decrease in a shift is the 1439 -> 0 wrap itself, a fall of 1439.  A
        -- guard in dial minutes rather than in "the new reading is under 5" is what
        -- makes this survive a STARVED poll: the watcher's own scan measured 1089 ms
        -- against a 1.6 Hz loop, and once the shift is live the dial runs at about
        -- ONE DIAL MINUTE PER REAL SECOND (720 dial minutes from t=98.47 to t=828.87),
        -- so a six-second stall lands the first post-wrap reading at 12:06 PM.  Any
        -- fixed "near zero" window would miss it and the run would never close.
        WrapDropMins = 60,
        -- The falling reading has to be seen this many scans in a row.  A run is one
        -- attempt and the end of the window is the one action that cannot be undone
        -- from inside the game, so a single mis-parse must not be able to spend it.
        -- The reset is the part that makes the count mean something: a reading back
        -- at or above the pre-fall value clears the latch, and since the dial cannot
        -- go backwards the poll after a mis-parse always reads HIGHER than the value
        -- the mis-parse was compared against.  So a one-poll glitch costs a poll, and
        -- only a fall that stays fallen is the handover.
        EndPolls = 2,
        -- `Workspace.` is prepended by the resolver; these are the two paths the
        -- recorder has already PROVED exist in the original, plus the fallback
        -- evidence below.  Nothing here is a guess about the room's layout.
        --
        -- LeverPath ends at the PART, not at the ClickDetector: the detector is a
        -- child of it, and the recorder's own `CLICK StartUpLever` lines are what
        -- proves the nesting.  See attachWindow.
        LeverPath = {'Consoles', 'MainReactorConsole', 'StartUpBigLever', 'StartClickPart'},
        ClockPath = {'Monitors', 'QuotaControlRoomMonitor', 'Screen', 'MonitorUI',
                     'MainMonitorFrame', 'TimeFrame', 'TimeLabel'},
        -- The game's own flag for the same event, used only if the lever's
        -- ClickDetector cannot be resolved: the window then opens on this edge and
        -- window.txt says it was the fallback that opened it.  A window that never
        -- opens records nothing, and losing a whole run to a renamed part is the
        -- failure this exists to prevent.
        OpenFlagPath = {'Stats', 'GameActive'},
    },
}

-- ========== WHAT IS LISTENED TO ==========
-- Playback, not properties -- and unlike our own place this is not a bounded
-- guess: the original game's sound library could be anywhere.  ReplicatedStorage
-- and ReplicatedFirst are in the list because a place that clones its effects
-- keeps the templates there, and a template that is cloned into the room is then
-- caught by the room's own DescendantAdded walk anyway.  SoundService is the
-- mixer.  Workspace is walked for the loose sounds and for anything the census
-- put inside a watched root.
--
-- Note that walking ReplicatedStorage does NOT put its parts into the property
-- watch: attachAudioOnly only registers SoundGroup and SoundEffect instances, so
-- a template tree cannot turn into twenty thousand watched keys.
local AUDIO_ROOTS = {
    {service = 'SoundService',      path = '',       label = 'SoundService'},
    {service = 'Workspace',         path = '',       label = 'Workspace'},
    {service = 'ReplicatedStorage', path = '',       label = 'ReplicatedStorage'},
    {service = 'ReplicatedFirst',   path = '',       label = 'ReplicatedFirst'},
}

-- ========== WHICH PROPERTIES, PER CLASS ==========
-- Chosen by asking what a script could plausibly drive during a start-up, not by
-- listing every property a class has: watching Part.Shape or Part.Name would put
-- twenty thousand keys in the log that no start-up can ever change.  The IsA
-- order matters where classes overlap -- a TextButton is both a GuiObject and a
-- GuiButton, so the text properties are added only for the classes that have
-- them -- and the first branch that matches wins.
--
-- Sound.TimePosition is deliberately absent.  It changes every tick while a sound
-- plays, so watching it would drown the timeline in the one thing that carries no
-- information: that a sound is still playing.  Playing is watched.
local function propsFor(inst)
    if inst:IsA('BasePart') then
        return {'CFrame', 'Size', 'Color', 'Material', 'Transparency',
                'Anchored', 'CanCollide', 'Reflectance', 'CastShadow'}
    elseif inst:IsA('Light') then
        return {'Enabled', 'Brightness', 'Color', 'Range', 'Shadows'}
    elseif inst:IsA('ParticleEmitter') then
        return {'Enabled', 'Rate', 'Color', 'Size', 'Transparency', 'Lifetime',
                'Speed', 'LightEmission', 'LightInfluence'}
    elseif inst:IsA('Fire') or inst:IsA('Smoke') or inst:IsA('Sparkles') then
        -- The three legacy effect instances.  They are not ParticleEmitters, so
        -- without this branch a burning core would be watched for nothing but its
        -- parents' positions.
        local p = {'Enabled', 'Color', 'SecondaryColor'}
        if inst:IsA('Fire') then
            p[#p+1] = 'Size'; p[#p+1] = 'Heat'; p[#p+1] = 'TimeScale'
        elseif inst:IsA('Smoke') then
            p[#p+1] = 'Size'; p[#p+1] = 'RiseVelocity'; p[#p+1] = 'Opacity'
        else
            p[#p+1] = 'SparkleColor'; p[#p+1] = 'TimeScale'
        end
        return p
    elseif inst:IsA('Beam') then
        return {'Enabled', 'Color', 'Transparency', 'Width0', 'Width1',
                'Brightness', 'LightEmission'}
    elseif inst:IsA('Trail') then
        return {'Enabled', 'Color', 'Transparency', 'Brightness', 'Lifetime'}
    elseif inst:IsA('Highlight') then
        -- A start-up that says "this device is now live" has to say it somewhere,
        -- and Highlight is one of the places a place does that.
        return {'Enabled', 'FillColor', 'OutlineColor', 'FillTransparency',
                'OutlineTransparency', 'DepthMode'}
    elseif inst:IsA('SoundEffect') then
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
        -- SoundGroup is the bus, and the bus is the game's own classification of
        -- what a sound is FOR -- an alarm, a footstep, a machine -- which is the
        -- cheap way to tell one from another without listening to it.
        return {'Playing', 'Volume', 'Pitch', 'SoundId', 'Looped', 'SoundGroup'}
    elseif inst:IsA('SoundGroup') then
        -- Volume is the one property on a bus that can silence everything routed
        -- through it, and it is the only thing in the audio chain whose state the
        -- Sound rows cannot see: every member Sound would still read Playing=true.
        -- A mixer pulled to zero therefore reads as a room full of sound.
        return {'Volume'}
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
        -- Workspace.Stats is made of these, and the recorder has already shown
        -- that it is the game's own bookkeeping -- GameActive, MainframeMeltdown,
        -- ChamberGravity are all there.  It is the highest-yield class in the set.
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
        return {'Length', 'Visible', 'Thickness'}
    elseif inst:IsA('HingeConstraint') then
        return {'Enabled', 'AngularVelocity', 'TargetAngle', 'MotorMaxTorque'}
    elseif inst:IsA('BaseScript') then
        return {'Enabled'}
    end
    return nil
end

-- ========== STATE ==========
local ents = {}        -- {inst, path, group, props, base, live}
local vals = {}        -- flat: the value last seen, stride = #props
local org = {}         -- flat: the value at start, never overwritten
local hits = {}        -- flat: how many times this key has moved, over the whole run
local seen = {}        -- inst -> true, so a child added twice is registered once
local connections = {}
local running = false
local totalProps = 0
local report = {found = {}, missing = {}, skipped = {}, byGroup = {}, classTotal = {}}
local logLines = {}
local dropped = 0
local sinkDown = false
local tick = 0
local startedAt = 0
local scanMs = 0
-- How many times the scan handed the frame back during its last pass, and how long
-- the loop then slept to keep its share of the clock under DutyTarget.  Both are
-- reported in health.txt: the lag fix is a claim about this machine's numbers, and
-- a claim that is not written down where the next run can be compared against it is
-- the kind of claim this project has already paid for twice.
local blockYields = 0
local sleepMs = 0
local movedKeys = 0
local summaryDirty = false
local lastTick = {}    -- j -> the tick this key last moved
local held = {}        -- j -> lines moved but not yet written, capped at NoisyAfter
local judged = {}      -- j -> 'discrete' once a key's lines have been written once
local firstTick = {}   -- j -> the tick of this key's first move (suppressed.txt only)
local ambient = {}     -- j -> {ent, i, tick, first} for keys judged ambient
local suppressedDirty = false
local fatal = nil
local usedPaths = {}
local collisions = 0
-- Sink health, and the reason it is a FILE rather than an output.
-- The operator's instruction, 2026-09-27: 「你不用在屏幕顶端专门搞个显示日志的，
-- 也不用打印到developerconcole，直接写入文件就行」.  Both of the things this
-- watcher used to say out loud -- "the sink is unreachable" when it happened, and a
-- status line every ReportEvery scans -- were diagnostics that existed for one
-- moment in a window nobody was reading, and then were gone.  The whole reason this
-- file writes to a sink in the first place is that the run cannot be repeated, so a
-- one-moment diagnostic is the wrong shape for all of them.  health.txt is the same
-- information with a lifetime: rewritten whenever the state changes, or on the SAME
-- ReportEvery interval the removed status line had -- same information, same
-- cadence, different destination.  That is deliberate rather than incidental: it
-- keeps the knob load-bearing instead of leaving a config value that nothing reads.
local healthDirty = false
-- Why a DOWN flag is not enough to report an outage: the file that would carry it
-- has to travel through the thing that is down.  See the transition block in post().
local sinkOutages = 0     -- completed + current, so it stays true after recovery
local sinkDownTotal = 0   -- seconds spent unreachable, summed over every outage
local sinkLastError = nil -- the reason from the most recent outage
local sinkLastAt = nil    -- elapsed t at which the most recent outage began

-- ---- the recording window ----
-- waiting -> open -> closed, and the only two things that move it are the lever and
-- the shift dial.  See CONFIG.Window for the rule and why it exists.
local windowState = 'waiting'
local windowDirty = false
local windowWhy = nil         -- how it opened, in the operator's terms
local windowOpenedAt = nil    -- elapsed t
local windowClosedAt = nil
local windowClosedWhy = nil
local windowWithheldLog = 0   -- timeline lines not recorded because the lever had
local windowWithheldAudio = 0 -- not been thrown yet
local clockMins = nil         -- the shift dial, minutes past 12:00PM (recorder map)
local clockText = nil         -- the raw label, which is the fact and not the reading
local clockEndPolls = 0
-- The handover latch.  `prevClockMins` is the last reading that PARSED (a nil read
-- leaves it alone, because a missing reading is not a reading), and `wrapFrom` is the
-- pre-fall value once a fall big enough to be the wrap has been seen.  Both live here
-- rather than inside windowStep so window.txt can print what the close rule was
-- actually weighing -- a run that did not end has to be diagnosable from its product
-- instead of from another attempt.
local prevClockMins = nil
local wrapFrom = nil
local leverHooked = false     -- whether the ClickDetector was found at all
local leverMiss = nil         -- why not, when it was not
local flagOpened = false      -- the window was opened by the fallback, not the lever
local recordedLines = 0       -- timeline lines actually posted (windows marks included)
local sinkError = nil
local sinkSince = nil

-- ---- audio ----
local audioLines = {}
local audioOnly = {}   -- Sound entries outside the property watch, polled for Playing
local bySound = {}     -- audio ent -> {plays, stops, ends, id, bus, last, ...}
local audioSeen = {}
local hookedSounds = 0
local audioHooks = 0
local audioRefused = 0
local audioEvents = 0
local audioPollOnly = 0
local audioDropped = 0
local audioPreexisting = 0
local audioError = nil
local audioDirty = false
local soundTotal = 0   -- every Sound found anywhere in the audio scope
local groupTotal = 0   -- every SoundGroup found anywhere in the audio scope

local NL = string.char(10)

-- Nothing below writes a backslash into a string literal.  Two reasons, and the
-- second one is the real one: this file is edited by tools that decode Lua
-- escapes once on the way in (our own project notes call it out), and a decoded
-- escape turns a legal Lua string into a syntax error that is reported against
-- the string rather than against the tool that broke it.  Newlines come from
-- NL = string.char(10), and every string that needs to contain a double quote is
-- written with single quotes.

local function now()
    local ok, t = pcall(function() return workspace:GetServerTimeNow() end)
    return ok and t or os.time()
end

local function stamp()
    -- Both clocks on purpose.  The relative one answers "how far into the run",
    -- the wall one answers "what was I doing at that moment" -- and the operator
    -- is the only one who can answer the second.
    --
    -- The relative clock is ZERO-PADDED TO A FIXED WIDTH, which looks fussy and is
    -- load-bearing.  Held lines are written when their key goes quiet, not when
    -- they happen, so changes.log is in release order and can carry a t=1 line
    -- after a t=2 one -- measured, not theorised: the fixture's own log has
    -- TemperatureVal's t=1.00 line below two t=2.00 lines from other keys.  With a
    -- fixed width the timestamp is the first field and sorts lexically, so
    -- `sort changes.log` recovers the true order exactly.  With %.2f it does not:
    -- 't=10.20' sorts before 't=9.50', so a plain sort would silently scramble the
    -- file rather than fix it, which is worse than leaving it alone.
    local ok, d = pcall(os.date, '%H:%M:%S')
    return string.format('t=%010.2f %s', now() - startedAt, ok and d or '??:??:??')
end

-- Newlines are stripped, and this is an INVARIANT of every artifact rather than a
-- precaution.  The whole log is line-oriented -- one change per line, split on
-- newlines by the sink -- and a single value whose tostring contains one would
-- inject a fragment that reads as a separate, malformed event.  CFrame is the
-- candidate (twelve numbers, and Roblox formats it generously), and rather than
-- assert what tostring does to a CFrame I make the assumption unnecessary: after
-- this, no formatted value can contain the delimiter no matter what it was.
local function fmt(v)
    if v == nil then return 'nil' end
    local ok, s = pcall(tostring, v)
    if not ok then return '<unprintable>' end
    return string.gsub(string.gsub(s, NL, ' '), string.char(13), ' ')
end

-- Every artifact carries this prefix, so the sink's directory -- which the
-- recorder also writes into -- stays separable by name alone.  Computed once, at
-- load, not per request: a prefix that changed mid-run would split one run across
-- two directories and make the set of files look incomplete.
local STAMP = (function()
    local ok, d = pcall(os.date, '%y%m%d-%H%M%S')
    return ok and d or tostring(os.time())
end)()
local PREFIX = 'originalwatch/' .. STAMP .. '/'

-- ========== TRANSPORT ==========
-- WHICH HTTP CALL ACTUALLY LEAVES THIS EXECUTOR.
--
-- On the operator's 2026-09-27 run the sink received a COMPLETE recording from the
-- recorder and NOTHING AT ALL from this watcher -- no originalwatch/ directory for a
-- whole shift, in the same session, through the same port, with both servers
-- verified up before it started.  The two scripts differed in exactly one structural
-- way: the recorder tried the executor's own request functions first and fell back
-- to HttpService:PostAsync last, while this file called PostAsync and nothing else.
-- The recorder's own comment says why that ordering is what it is -- a plain client
-- is not allowed to call PostAsync and it raises at once -- so the two files were
-- assuming OPPOSITE things about the same call, and the run where they disagreed is
-- the run that produced no bytes.
--
-- So the ladder is the recorder's, in the recorder's order: the executor's request
-- family first, PostAsync last.  Whichever one wins is TRANSPORT, and it is named in
-- health.txt, hello.txt and alive.txt -- so a run that delivers nothing says, in the
-- one file it does deliver, which call it was delivering nothing on.
--
-- THE CALLING SHAPE IS A REQUEST TABLE, not (url, body).  syn.request and its
-- siblings take a table, and the PostAsync wrapper below adapts to that same shape.
-- Handing them a positional url raises, and a probe built that way reported every
-- working transport as broken -- which is the mistake this comment exists to stop
-- being repeated.
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
        { 'getgenv().request', function() return getgenv and getgenv().request end },
        { 'HttpService:PostAsync', function()
            if HttpService == nil or HttpService.PostAsync == nil then return nil end
            return function(req)
                local ok, err = pcall(HttpService.PostAsync, HttpService, req.Url, req.Body)
                if ok then return { StatusCode = 200 } end
                -- The raise is KEPT, where the recorder's wrapper discards it for a
                -- bare StatusCode 0.  The recorder only needs to know whether to fall
                -- through to its disk sink; this file's health.txt is read hours later
                -- by someone deciding what to repair, and 'status 0' is not a repair.
                return { StatusCode = 0, Error = tostring(err) }
            end
        end },
    }
    -- A thunk per candidate, not the callable: a table holding nils would stop
    -- ipairs at the first missing one and silently skip every candidate after it,
    -- which on this ladder is PostAsync -- the only one a plain client has.
    for _, cand in ipairs(cands) do
        local ok, f = pcall(cand[2])
        if ok and type(f) == 'function' then
            httpFn = f
            TRANSPORT = cand[1]
            break
        end
    end
end

-- One POST, in the one calling shape.  Returns ok, detail -- and the detail names
-- the reason, because "the sink is unreachable" and "this executor has no POST
-- transport at all" are different repairs, and health.txt is where the difference
-- has to survive the run.
local function sendOnce(req)
    if httpFn == nil then
        return false, 'no HTTP transport in this executor: the request family and' ..
            ' HttpService:PostAsync are both absent'
    end
    local ok, res = pcall(httpFn, req)
    if not ok then return false, TRANSPORT .. ' raised: ' .. tostring(res) end
    if type(res) ~= 'table' then return false, TRANSPORT .. ' returned no result table' end
    local code = tonumber(res.StatusCode) or tonumber(res.Status) or
        tonumber(res.statusCode) or tonumber(res.status) or tonumber(res.code)
    local extra = res.Error or res.error or res.Body
    if code == nil then
        return false, TRANSPORT .. ' returned no status code' ..
            (extra and (' (' .. tostring(extra) .. ')') or '')
    end
    if code < 200 or code > 299 then
        return false, TRANSPORT .. ' status ' .. tostring(code) ..
            (extra and (' (' .. tostring(extra) .. ')') or '')
    end
    return true, nil
end

-- ========== THE ALIVE BEACON ==========
-- The first thing this file does once it can send at all, and it is here rather than
-- in Start deliberately.
--
-- hello.txt answers "was this injected".  It is posted inside Start, so a file that
-- dies at LOAD -- anywhere in the two thousand lines above -- sends nothing, and
-- "died at load" and "never injected" arrive as the same reading: an empty sink.
-- The operator's rule is that a reactor start-up happens ONCE, so a reading that
-- costs him another shift is worth one HTTP round trip to remove.  With this file
-- there are three readings instead of two:
--
--   nothing at all            the script never ran as far as this line
--   alive.txt, no hello.txt   it loaded and died in the module body below
--   both                      Start ran; the census is the only thing left to fail,
--                             and tree.txt / error.txt separate those two
--
-- IT DOES NOT GO THROUGH post(), AND THAT IS THE POINT.  post() keeps the sink
-- outage counters in the run's clock, and the run's clock does not exist yet --
-- startedAt is 0 until Start re-bases it -- so folding this send into that
-- bookkeeping would charge the outage a duration measured from the wrong origin and
-- write a large negative sink_down_total into a file read hours later to decide
-- repairs.  A beacon that corrupts the health fields it exists to make readable is
-- worse than no beacon.  Its failure is not silent either: the very next send is
-- hello.txt, a fraction of a second later through the same transport, and that one
-- IS counted.
--
-- THE SECOND CHANNEL IS THE LOCAL DISK, because the case the beacon is for is
-- exactly the case where the sink gets nothing: if the executor has writefile and no
-- POST transport, a sink-only beacon is worthless when it is needed most.  writefile
-- is the recorder's own fallback for the same reason, and it needs the same two-step
-- (some executors refuse a path whose directory does not exist yet, and then take a
-- bare filename in their own working directory).  Both channels carry the same body,
-- so whichever one arrives carries the same build tag and the same transport.
pcall(function()
    local body = table.concat({
        '# the watcher is loaded and reached its transport (build ' .. CONFIG.Build .. ')',
        'build=' .. CONFIG.Build,
        'transport=' .. TRANSPORT,
        'sink=' .. CONFIG.Sink,
        'prefix=' .. PREFIX,
        'place=' .. tostring(game and game.PlaceId or '?'),
        'hotkeys=RightAlt writes every file out now; RightControl stops',
        'note=hello.txt follows within a fraction of a second, from inside Start. If' ..
            ' this is the only file you have, the watcher loaded and died in its' ..
            ' module body -- nothing below this point had run, so the console error' ..
            ' is the whole of the diagnosis.',
        '',
    }, NL)
    -- One send, not the chunked path: this body is a few hundred bytes against a
    -- CONFIG.Chunk of 900000, and the beacon must not depend on the splitter.
    local sent = sendOnce({
        Url = CONFIG.Sink .. PREFIX .. 'alive.txt',
        Method = 'POST', Body = body,
        Headers = { ['Content-Type'] = 'text/plain' },
    })
    -- Written to disk only when the sink did not take it.  Two copies of the same
    -- beacon would be one more thing to reconcile, and the sink is the channel every
    -- other artifact uses.
    if not sent and type(writefile) == 'function' then
        local okw = pcall(writefile, 'originalwatch/' .. STAMP .. '/alive.txt', body)
        if not okw then pcall(writefile, 'TRG_watch_' .. STAMP .. '_alive.txt', body) end
    end
end)

-- ========== THE SINK ==========
local function post(name, body, append)
    local ok, err = pcall(function()
        -- Split on newline boundaries rather than byte offsets.  A split inside a
        -- UTF-8 sequence produces a file that is not the text that was sent, and
        -- every artifact here is line-structured anyway.
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
            local url = CONFIG.Sink .. PREFIX .. name
            -- In append mode every chunk appends.  In write mode the first chunk
            -- truncates and the rest append, which is the only way to get an
            -- atomic-looking file out of a sink that has no rename.
            if append or not first then url = url .. '?mode=a' end
            first = false
            local sent, detail = sendOnce({
                Url = url, Method = 'POST', Body = chunk,
                Headers = { ['Content-Type'] = 'text/plain' },
            })
            -- error(..., 0) so the detail reaches the health fields VERBATIM: pcall's
            -- own position prefix would name a line in this file, and the wording --
            -- which transport, and what it said -- is the part the reader needs.
            if not sent then error(detail, 0) end
        end
    end)
    -- The transition is recorded, not announced.  Both edges mark health.txt dirty,
    -- and unlike a print it is still there afterwards -- which matters most for the
    -- DOWN edge, because the next thing that happens if the sink stays down is that
    -- the operator finds a truncated log and no statement anywhere that it is
    -- truncated.  A queued line is still queued (see flush and the MaxQueue bound),
    -- so nothing is lost by staying quiet at the moment it happens.
    --
    -- AND THE OUTAGE SURVIVES ITS OWN END.  A DOWN/ok flag alone cannot report an
    -- outage, for a reason that is structural rather than a bug in the flag: the
    -- one artifact that would carry "the sink is down" is posted to the sink, so it
    -- fails with everything else, and the first post that succeeds is the same post
    -- that clears the flag.  An outage is therefore never written down at all -- the
    -- reader gets a gap in changes.log and no file that mentions it.  The four
    -- cumulative fields below fix exactly that: they are updated while the sink is
    -- unreachable and they are still true afterwards, so the NEXT successful
    -- health.txt says "there were two outages, 12.4 s in total, the last one at
    -- t=88.1 with this error" -- which is the difference between a silent run and a
    -- run that was never being taken.
    if ok then
        if sinkDown then
            sinkDownTotal = sinkDownTotal + ((now() - startedAt) - (sinkSince or 0))
            sinkDown = false
            sinkError = nil
            sinkSince = nil
            healthDirty = true
        end
    elseif not sinkDown then
        sinkDown = true
        sinkOutages = sinkOutages + 1
        sinkError = tostring(err)
        sinkLastError = tostring(err)
        sinkSince = now() - startedAt
        sinkLastAt = sinkSince
        healthDirty = true
    end
    return ok
end

-- ========== REGISTRATION ==========
-- A path is an instance's identity in every artifact this file writes, and
-- GetFullName does not guarantee one: a place built from repeated prefabs has
-- twenty lamps whose chains all read LightCell.LightModel.NeonPart, and on the
-- first live run of the room watcher all twenty were logged under a single path
-- and the log announced "Transparency changed 40 times" about what were really
-- twenty lamps changing twice.  A colliding path therefore gets a suffix.  For a
-- part that suffix is its world position -- unique here, and the thing the
-- operator can go and look at.  Collisions are counted and reported in rooms.txt,
-- because a silent disambiguation is a silent chance to mislabel.
local function uniquePath(inst)
    local path = string.gsub(inst:GetFullName(), '^Workspace%.', '')
    -- Also strip the place's other service prefixes: a sound in ReplicatedStorage
    -- would otherwise carry a 20-character service name on every line it writes.
    path = string.gsub(path, '^game%.', '')
    if usedPaths[path] == nil then
        usedPaths[path] = true
        return path
    end
    collisions = collisions + 1
    local suffix = ''
    local okp, pos = pcall(function() return inst.Position end)
    if okp and typeof(pos) == 'Vector3' then
        suffix = string.format(' ~(%.1f, %.1f, %.1f)', pos.X, pos.Y, pos.Z)
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

-- ========== AUDIO ==========
-- One line per playback event, written straight out with no ring in front of it.
-- Held and suppressed are the right treatment for a property that is POLLED: a
-- key that moves every scan has to be judged before it is believed.  A hook is
-- not polled -- Played fires once per :Play() call -- so there is nothing to
-- judge, and putting a real alarm through the ambient filter would be exactly the
-- mistake the filter exists to prevent.
local function audioEvent(ent, kind)
    local inst = ent.inst
    -- Guarded, because this runs inside a signal handler and an error there does
    -- not stop the loop, it just fires again on the next event.  The first error
    -- is kept so Status() and rooms.txt can say the audio half is unsound instead
    -- of quietly logging half a timeline.
    local ok, err = pcall(function()
        local rec = bySound[ent]
        if rec == nil then
            rec = {plays = 0, stops = 0, ends = 0}
            bySound[ent] = rec
        end
        audioEvents = audioEvents + 1
        if kind == 'PLAYED' then rec.plays = rec.plays + 1
        elseif kind == 'STOPPED' then rec.stops = rec.stops + 1
        else rec.ends = rec.ends + 1 end
        local t = stamp()
        rec.last = t
        -- Read the bus and the asset at PLAY time rather than caching them at
        -- registration: a sound can be re-routed or re-assigned between plays, and
        -- recording the value it had when the watcher started would attribute the
        -- current alarm to the asset of an earlier one.
        if kind == 'PLAYED' then
            rec.id = fmt(inst.SoundId)
            local bus = inst.SoundGroup
            rec.bus = bus and bus.Name or '(none)'
            rec.hookPlay = true
        end
        audioLines[#audioLines+1] = string.format(
            '%s | %-18s | %s | %-9s | bus=%s | id=%s | vol=%.2f pitch=%.2f looped=%s',
            t, ent.group, ent.path, kind, rec.bus or '(none)', rec.id or '(none)',
            inst.Volume, inst.Pitch, fmt(inst.Looped))
        audioDirty = true
    end)
    if not ok and audioError == nil then
        -- Recorded, and marked dirty so it reaches health.txt on the next scan.
        -- This was a warn(), which is one line in a window nobody is watching
        -- during a run that cannot be repeated -- the same argument that moved
        -- the sink state out of the console.  It is the one error that makes the
        -- audio half silently empty while everything else still looks healthy,
        -- so it needs to be in a file that outlives the session.
        audioError = 'audio handler: ' .. tostring(err)
        healthDirty = true
    end
end

-- Events are attached one at a time and each attach is checked, because the cost
-- of being wrong about an event name is asymmetric: a silent no-attach produces a
-- watcher that looks healthy and hears nothing, and no amount of reading this
-- file would reveal it.  audioRefused is reported in rooms.txt for that reason.
local function attachAudio(ent)
    local inst = ent.inst
    local specs = {{'Played', 'PLAYED'}, {'Stopped', 'STOPPED'}, {'Ended', 'ENDED'}}
    for _, spec in ipairs(specs) do
        local name, kind = spec[1], spec[2]
        local got, sig = pcall(function() return inst[name] end)
        if not got or typeof(sig) ~= 'RBXScriptSignal' then
            audioRefused = audioRefused + 1
        else
            connections[#connections+1] = sig:Connect(function()
                audioEvent(ent, kind)
            end)
            audioHooks = audioHooks + 1
        end
    end
    -- A hook sees TRANSITIONS, so a sound that was already playing when the
    -- watcher attached can never produce a PLAYED line.  That is not hypothetical:
    -- the first live audio run in our own place had 23 sounds audible from t=0 --
    -- the entire ambient floor of both rooms -- and not one of them could have
    -- reported itself.  So the state is read once at attach time and written out
    -- as its own event under its own word: ALREADY-PLAYING, not PLAYED, because
    -- it is a different fact and a reader has to be able to tell them apart.
    local ok, playing = pcall(function() return inst.Playing end)
    if ok and playing then
        local rec = bySound[ent]
        if rec == nil then
            rec = {plays = 0, stops = 0, ends = 0}
            bySound[ent] = rec
        end
        local t = stamp()
        rec.playing = true
        rec.hookPlay = true
        rec.preexisting = true
        rec.last = t
        rec.id = fmt(inst.SoundId)
        local bus = inst.SoundGroup
        rec.bus = bus and bus.Name or '(none)'
        audioPreexisting = audioPreexisting + 1
        audioLines[#audioLines+1] = string.format(
            '%s | %-18s | %s | ALREADY-PLAYING | audible before the watcher attached, so no Played event can exist for it | bus=%s | id=%s | vol=%.2f pitch=%.2f looped=%s',
            t, ent.group, ent.path, rec.bus, rec.id, inst.Volume, inst.Pitch, fmt(inst.Looped))
        audioDirty = true
    end
end

-- register is defined far below, next to what it does, but the audio walk needs
-- it for the mixer, so it is forward-declared here.  A `local function` is not in
-- scope above its own definition, and the failure would be a nil-call at Start
-- rather than anything the parser could catch.
local register

-- A Sound outside the watched rooms: hooked and polled, but not registered for
-- the property watch, because a library of templates has nothing that moves --
-- only playback.  SoundGroup and SoundEffect are the exception: the mixer IS the
-- thing whose state the Sound rows cannot see, and an effect being reshaped in
-- place is how a running reactor is made to sound different from a stopped one.
--
-- The narrow test is what makes it safe to walk ReplicatedStorage, which is
-- mostly parts and GUI.  A wider test here -- "anything propsFor knows" -- would
-- have put every template in the storage into the property watch, which is
-- twenty thousand keys about a tree nothing drives.
local function attachAudioOnly(inst)
    if audioSeen[inst] then return end
    if not inst:IsA('Sound') then
        if inst:IsA('SoundGroup') or inst:IsA('SoundEffect') then
            register(inst, 'Audio')
        end
        return
    end
    audioSeen[inst] = true
    hookedSounds = hookedSounds + 1
    local ent = {inst = inst, path = uniquePath(inst), group = 'Audio'}
    audioOnly[#audioOnly+1] = ent
    attachAudio(ent)
end

-- The fallback half of the audio watch, and the reason it can be trusted.  These
-- sounds have no property entry, so if a hook failed to attach nothing else would
-- ever notice.  Playing is therefore also read directly, once per episode, and a
-- play the hooks did not report is written out as a disagreement rather than
-- swallowed.  Latched on the transition, not on the value: a sound that plays for
-- ten seconds must produce one line, not ten.
local function pollAudio()
    for _, ent in ipairs(audioOnly) do
        local inst = ent.inst
        local ok, playing = pcall(function() return inst.Playing end)
        if ok then
            local rec = bySound[ent]
            local was = rec and rec.playing or false
            if playing and not was then
                local seenIt = rec and rec.hookPlay
                if rec == nil then
                    rec = {plays = 0, stops = 0, ends = 0}
                    bySound[ent] = rec
                end
                rec.playing = true
                rec.hookPlay = false
                if not seenIt then
                    -- Counted as a play, because it is one -- the tally would be
                    -- lying if a sound it lists as never played appeared in the
                    -- header's "audible" count.  audioPollOnly is the separate
                    -- number that says the hooks missed it.
                    local t = stamp()
                    rec.plays = (rec.plays or 0) + 1
                    rec.last = t
                    rec.id = fmt(inst.SoundId)
                    local bus = inst.SoundGroup
                    rec.bus = bus and bus.Name or '(none)'
                    audioPollOnly = audioPollOnly + 1
                    audioLines[#audioLines+1] = string.format(
                        '%s | %-18s | %s | PLAYS-POLL-ONLY | the Sound is Playing but no Played event was seen | id=%s',
                        t, ent.group, ent.path, rec.id)
                    audioDirty = true
                end
            elseif not playing and was then
                rec.playing = false
                rec.hookPlay = false
            end
        end
    end
end

-- Rewritten rather than appended, and it is the file that stays readable after an
-- hour: audio.txt is the timeline and can run long, but this is one line per sound
-- that has actually been heard, plus a roll-up by bus.  Only sounds that played
-- appear, so the header count is what makes "nothing was audible" a statement
-- with a source instead of an empty file.
local function audioTally()
    local out = {}
    local buses = {}
    local rows = {}
    local audible = 0
    for ent, rec in pairs(bySound) do
        -- "Has a row" is the honest test for "was audible", not "has plays".  A
        -- sound that was ALREADY playing at attach time has no event of any kind
        -- behind it, so a plays>0 test excludes exactly the sounds that were
        -- audible from t=0 -- in our own place that was 23 of them, the whole
        -- ambient floor, and the bus roll-up read a single bus while the room was
        -- full of sound.  plays/stops/ends are left as they are, so a row with
        -- plays=0 is itself the evidence that the hook missed it.
        if (rec.plays or 0) > 0 or (rec.stops or 0) > 0 or (rec.ends or 0) > 0
            or rec.preexisting then
            audible = audible + 1
            local bus = rec.bus or '(unknown)'
            buses[bus] = (buses[bus] or 0) + 1
            rows[#rows+1] = string.format(
                '%-18s %s | plays=%d stops=%d ends=%d%s | bus=%s | id=%s | last %s',
                ent.group, ent.path, rec.plays or 0, rec.stops or 0, rec.ends or 0,
                rec.preexisting and ' [ALREADY PLAYING AT t=0]' or '',
                bus, rec.id or '(none)', rec.last or '(never)')
        end
    end
    -- Hooks and Sounds are three to one, so both numbers are here: printing the
    -- hook count under the word "Sound" is how a place with 507 Sounds reports
    -- 1,521 of them.
    out[#out+1] = string.format(
        '# %d Sound(s) hooked; %d hook(s) attached, %d refused; %d play/stop/end event(s) seen',
        hookedSounds, audioHooks, audioRefused, audioEvents)
    out[#out+1] = string.format(
        '# %d of them have been audible; %d play(s) were caught by the poll and NOT by a hook',
        audible, audioPollOnly)
    if audioPreexisting > 0 then
        out[#out+1] = string.format(
            '# %d were ALREADY playing when the watcher attached -- a hook cannot see those, and',
            audioPreexisting)
        out[#out+1] = '# their asset and bus were read off the instance instead of off a Played event'
    end
    if audioDropped > 0 then
        out[#out+1] = string.format(
            '# %d audio line(s) were DROPPED from audio.txt: the sink was down and the queue overflowed',
            audioDropped)
    end
    if audioError ~= nil then
        out[#out+1] = '# AUDIO IS UNSOUND: ' .. audioError
    end
    local busNames = {}
    for k in pairs(buses) do busNames[#busNames+1] = k end
    table.sort(busNames, function(a, b) return buses[a] > buses[b] end)
    if #busNames > 0 then
        local parts = {}
        for _, k in ipairs(busNames) do parts[#parts+1] = string.format('%s=%d', k, buses[k]) end
        out[#out+1] = '# audible by bus: ' .. table.concat(parts, '  ')
    end
    out[#out+1] = ''
    table.sort(rows)
    for _, r in ipairs(rows) do out[#out+1] = r end
    return table.concat(out, NL) .. NL
end

-- Not `local function`: attachAudioOnly above forward-declares this name, so the
-- assignment here has to land in THAT local rather than create a second one the
-- audio walk never sees.
function register(inst, group)
    if seen[inst] then return end
    local props = propsFor(inst)
    if props == nil then return end
    seen[inst] = true
    local path = uniquePath(inst)
    local ent = {inst = inst, path = path, group = group, props = props,
                 base = totalProps, live = true}
    ents[#ents+1] = ent
    for i = 1, #props do
        local j = totalProps + i
        local v = inst[props[i]]
        vals[j] = v
        org[j] = v
        hits[j] = 0
        -- Emptied rather than left absent so record() can append without a nil
        -- check on the first move of every key in the run.
        held[j] = {}
        judged[j] = nil
        firstTick[j] = nil
        ambient[j] = nil
        lastTick[j] = nil
    end
    totalProps = totalProps + #props
    -- A Sound inside a watched root gets a property entry AND hooks: the property
    -- is the poll-side cross-check on the hook, and the hook is what catches a
    -- sound too short to be seen by the poll.
    if inst:IsA('Sound') and not audioSeen[inst] then
        audioSeen[inst] = true
        hookedSounds = hookedSounds + 1
        attachAudio(ent)
    end
    local counts = report.byGroup[group]
    if counts then
        counts[inst.ClassName] = (counts[inst.ClassName] or 0) + 1
    end
    report.classTotal[inst.ClassName] = (report.classTotal[inst.ClassName] or 0) + 1
end

-- ========== STAYING OUT OF THE GAME'S WAY ==========
-- The scheduler half of the lag fix (the other half is the duty sleep in the main
-- loop; the numbers are on MaxBlockMs).  Every long walk in this file calls this
-- every SLICE_CHECK iterations: it returns nil while the current slice is still
-- cheap, and the fresh clock after yielding for a frame when it is not.
--
-- A function rather than an inline test because all three walks need it and they
-- need the same rule -- the census walk, the index build and the scan -- and three
-- copies of a threshold is three places for the numbers to drift apart.  It takes
-- the slice's start as an argument instead of remembering it, so a caller cannot
-- hold a stale slice by forgetting to update it: the value it passes back in is the
-- one it was handed.
--
-- SLICE_CHECK is 64 because the check itself costs an os.clock call and the thing
-- it is guarding costs ~500 property reads -- 64 instances is about two
-- milliseconds on the measured 3.9 microseconds per read, so the budget is honoured
-- to within a frame of itself and the check is under 1% of the work it bounds.
local SLICE_CHECK = 64
local function breathe(sliceAt)
    if (os.clock() - sliceAt) * 1000 < CONFIG.MaxBlockMs then return nil end
    blockYields = blockYields + 1
    task.wait()
    return os.clock()
end

-- ========== DISCOVERY ==========
-- The first thing that runs, and the reason this file can be pointed at a place
-- nobody has dumped.  Two levels deep: every direct child of Workspace with its
-- descendant count, and then -- for anything too big to watch -- that root's own
-- children with theirs.  Which is exactly the information needed to go one level
-- further without another guess.

local function safeDescendants(node)
    local ok, list = pcall(function() return node:GetDescendants() end)
    if ok and type(list) == 'table' then return list end
    return {}
end

local function census()
    local rows = {}
    local total = 0
    -- workspace, lowercase: `Workspace` is not a global in Roblox and this file is
    -- never compiled by a Luau parser before it is injected, so the mistake would
    -- not have surfaced until the census ran in the game -- after the operator had
    -- already thrown the lever, which is the one moment the run cannot be redone.
    local children = workspace:GetChildren()
    -- Sliced like the scan, because this is the other long walk and it runs at the
    -- worst possible moment: injection, while the operator is walking to the console
    -- to throw the lever.  On the measured place the census is 48 s of solid work
    -- (the first changes.log line of the run before last was at t=47.93), and a
    -- frozen client for that minute is the same complaint as the per-scan freeze --
    -- the operator cannot move while it happens.  No stamp here: the census writes
    -- no timeline, so there is nothing for a slice boundary to be wrong about.
    local sliceAt = os.clock()
    for _, c in ipairs(children) do
        local d = safeDescendants(c)
        local parts = 0
        for i = 1, #d do
            if d[i]:IsA('BasePart') then parts = parts + 1 end
            if i % SLICE_CHECK == 0 then
                local fresh = breathe(sliceAt)
                if fresh ~= nil then sliceAt = fresh end
            end
        end
        rows[#rows+1] = {node = c, name = c.Name, class = c.ClassName,
                         n = #d, parts = parts, kids = d}
        total = total + #d
    end
    -- Largest first for the REPORT: the reader wants to know what the giants are
    -- before anything else.
    table.sort(rows, function(a, b)
        if a.n ~= b.n then return a.n > b.n end
        return a.name < b.name
    end)
    return rows, total, #children
end

local function censusReport(rows, total, nChildren, picked, skipped)
    local out = {}
    out[#out+1] = '# census -- every direct child of Workspace, largest first'
    out[#out+1] = string.format(
        '# %d instance(s) under Workspace, in %d direct children; %d root(s) selected for watching',
        total, nChildren, #picked)
    out[#out+1] = string.format('# budget: at most %d instances per root, %d in total; smallest roots are taken first',
        CONFIG.PerRootBudget, CONFIG.TotalBudget)
    out[#out+1] = ''
    out[#out+1] = '## direct children'
    for _, r in ipairs(rows) do
        local verdict = 'WATCHED'
        if r.skipped then verdict = 'SKIPPED ' .. r.skipped end
        out[#out+1] = string.format('   %-12s %-34s %8d desc %8d parts   %s',
            verdict, r.name, r.n, r.parts, r.class)
    end
    -- The drill-down.  A root that was too big to watch is the one case where the
    -- census has to go one level deeper, because "Workspace.Facility has 400,000
    -- instances" is not actionable and "Workspace.Facility.ControlRoom has 5,000"
    -- is.  Printed for skipped roots only: for a watched root the drill-down is
    -- inventory.txt's job.
    if #skipped > 0 then
        out[#out+1] = ''
        out[#out+1] = '## children of the roots that were too big to watch'
        for _, name in ipairs(skipped) do
            local node = nil
            for _, r in ipairs(rows) do
                if r.name == name then node = r.node break end
            end
            if node then
                local kids = {}
                for _, k in ipairs(node:GetChildren()) do
                    kids[#kids+1] = {name = k.Name, class = k.ClassName, n = #safeDescendants(k)}
                end
                table.sort(kids, function(a, b)
                    if a.n ~= b.n then return a.n > b.n end
                    return a.name < b.name
                end)
                out[#out+1] = string.format('   -- %s (%d children)', name, #kids)
                for _, k in ipairs(kids) do
                    out[#out+1] = string.format('      %-40s %8d desc  %s', k.name, k.n, k.class)
                end
            end
        end
    end
    return table.concat(out, NL) .. NL
end

-- The selection rule, in one place and stated in rooms.txt next to its result, so
-- that a wrong pick is visible as a wrong pick rather than as a quiet room.
local function selectRoots(rows)
    local pinned, denied = {}, {}
    for _, n in ipairs(CONFIG.Pinned) do pinned[n] = true end
    for _, n in ipairs(CONFIG.Deny) do denied[n] = true end
    local picked, skipped = {}, {}
    local budget = CONFIG.TotalBudget
    -- Smallest first, so the budget is spent on the many small things and the
    -- SKIPPED list is the few giants.  A giant at the top of the list is a name
    -- somebody can act on; a giant at the bottom would only ever be a surprise.
    local ascending = {}
    for _, r in ipairs(rows) do ascending[#ascending+1] = r end
    table.sort(ascending, function(a, b)
        if a.n ~= b.n then return a.n < b.n end
        return a.name < b.name
    end)
    for _, r in ipairs(ascending) do
        if denied[r.name] then
            r.skipped = 'denied by CONFIG.Deny'
            skipped[#skipped+1] = r.name
        elseif r.n > CONFIG.PerRootBudget and not pinned[r.name] then
            r.skipped = string.format('over PerRootBudget (%d)', CONFIG.PerRootBudget)
            skipped[#skipped+1] = r.name
        elseif r.n > budget and not pinned[r.name] then
            r.skipped = 'no budget left'
            skipped[#skipped+1] = r.name
        elseif r.n == 0 and not CONFIG.WatchEmptyRoots then
            r.skipped = 'empty and WatchEmptyRoots is off'
            skipped[#skipped+1] = r.name
        else
            r.skipped = nil
            picked[#picked+1] = r
            budget = budget - r.n
        end
    end
    return picked, skipped
end

-- buildAudioIndex is defined after buildIndex because it reads better next to
-- what it does, but buildIndex calls it, so it has to be declared first: a
-- `local function` is not in scope above its own definition, and the failure
-- would be a nil-call at Start rather than anything the parser could catch.
-- (The same trap as `register` above, twice in one file, which is why it is
-- called out in both places rather than trusted to memory.)
local buildAudioIndex

local function buildIndex(rows, picked)
    report = {found = {}, missing = {}, skipped = {}, byGroup = {}, classTotal = {}}
    usedPaths = {}
    collisions = 0
    for _, r in ipairs(picked) do
        local node = r.node
        report.byGroup[r.name] = {}
        report.found[#report.found+1] = {
            group = r.name, path = r.name, class = node.ClassName,
            count = r.n, parts = r.parts,
        }
        register(node, r.name)
        -- The heaviest walk in the file per instance, because register() resolves a
        -- class, picks the watched property list and builds a UNIQUE PATH STRING for
        -- every instance.  It is also the walk that runs while the operator is still
        -- moving: the census measured 48 s, and the lever hook is the only thing
        -- that has to beat him to the console (it is installed synchronously in
        -- Start, above), so everything here may be slow as long as it is not a
        -- freeze.  Sliced for exactly that reason: slow is survivable, blocked is
        -- not.
        local sliceAt = os.clock()
        for i = 1, #r.kids do
            register(r.kids[i], r.name)
            if i % SLICE_CHECK == 0 then
                local fresh = breathe(sliceAt)
                if fresh ~= nil then sliceAt = fresh end
            end
        end
        -- Connected after the walk, never before: a connection made first would
        -- fire for every descendant during the walk and register each one twice,
        -- and `seen` would only hide that, not the ordering bug behind it.
        connections[#connections+1] = node.DescendantAdded:Connect(function(d)
            register(d, r.name)
        end)
    end
    buildAudioIndex()
end

-- The audio scope, walked once: every Sound anywhere under the four roots gets
-- three playback hooks, and every SoundGroup and SoundEffect gets a property
-- entry.  A root that is missing is reported, not skipped, for the same reason as
-- the rooms -- an absent library would otherwise read as a silent game.
function buildAudioIndex()
    report.audio = {found = {}, missing = {}}
    -- The audio walk registers the mixer through the ordinary property watch and
    -- register() files its class counts under report.byGroup[group], so the key
    -- has to exist here or those classes count in classTotal while their group
    -- reports nothing -- which is how "77 more instances than last time" reads as
    -- unexplained.
    report.byGroup['Audio'] = {}
    for _, spec in ipairs(AUDIO_ROOTS) do
        local ok, svc = pcall(function() return game:GetService(spec.service) end)
        local node = ok and svc or nil
        if node ~= nil and spec.path ~= '' then
            for token in string.gmatch(spec.path, '[^.]+') do
                if node == nil then break end
                node = node:FindFirstChild(token)
            end
        end
        if node == nil then
            report.audio.missing[#report.audio.missing+1] = spec.label
        else
            -- Two different numbers, and reporting one under the other's label is
            -- how a coverage claim becomes a lie: SoundService has eight
            -- descendants and ONE Sound in it, so "8 Sounds hooked" would have
            -- been wrong by 8x on the very root whose product is a mixer.  `count`
            -- is what is under the root; `sounds` is what was actually hooked.
            local hooked = 0
            -- Walked once, not twice.  GetDescendants allocates a fresh array of
            -- every descendant, and Workspace here holds the whole facility: the
            -- earlier version called it both to iterate and again for the count,
            -- which on a large place is a second full copy of the tree built for
            -- one integer.
            local desc = safeDescendants(node)
            attachAudioOnly(node)
            if node:IsA('Sound') then hooked = hooked + 1 end
            for _, d in ipairs(desc) do
                attachAudioOnly(d)
                if d:IsA('Sound') then hooked = hooked + 1 end
            end
            report.audio.found[#report.audio.found+1] = {
                label = spec.label, class = node.ClassName,
                count = #desc, sounds = hooked,
            }
            connections[#connections+1] = node.DescendantAdded:Connect(attachAudioOnly)
        end
    end
end

-- ========== REPORTING ==========
local function coverageReport(rows, total, nChildren, picked, skipped)
    local out = {}
    out[#out+1] = '# coverage -- what this watcher has in front of it'
    -- Counted from the `skipped` ARGUMENT, not from report.skipped.  Nothing ever
    -- writes to report.skipped, so the header read "0 root(s) skipped" on a run
    -- whose own body listed a skipped root two screens further down -- a summary
    -- line contradicting the detail under it, which is the worst possible place for
    -- a wrong number because it is the one line a reader trusts instead of checking.
    out[#out+1] = string.format('# %d instances, %d watched properties, %d roots watched, %d root(s) skipped',
        #ents, totalProps, #report.found, #skipped)
    out[#out+1] = string.format('# %d instance(s) needed a path suffix: their GetFullName was not unique',
        collisions)
    out[#out+1] = ''
    out[#out+1] = '## how the roots were chosen'
    out[#out+1] = string.format('# pinned by name: %s',
        #CONFIG.Pinned > 0 and table.concat(CONFIG.Pinned, ', ') or '(none -- pure discovery)')
    out[#out+1] = string.format('# denied by name: %s',
        #CONFIG.Deny > 0 and table.concat(CONFIG.Deny, ', ') or '(none)')
    out[#out+1] = string.format('# a root is watched when its descendant count is <= %d, unless it is',
        CONFIG.PerRootBudget)
    out[#out+1] = string.format('#   pinned; roots are taken SMALLEST FIRST until %d instances are',
        CONFIG.TotalBudget)
    out[#out+1] = '#   spoken for.  Anything else is listed as SKIPPED with its reason.'
    out[#out+1] = ''
    for _, r in ipairs(picked) do
        local counts = report.byGroup[r.name] or {}
        local keys = {}
        local n = 0
        for k, v in pairs(counts) do keys[#keys+1] = k; n = n + v end
        table.sort(keys, function(a, b)
            if counts[a] ~= counts[b] then return counts[a] > counts[b] end
            return a < b
        end)
        out[#out+1] = string.format('## %s (%s) -- %d descendants, %d watched instances',
            r.name, r.class, r.n, n)
        for _, k in ipairs(keys) do
            out[#out+1] = string.format('   %-24s %d', k, counts[k])
        end
        out[#out+1] = ''
    end
    -- The audio walk registers the mixer through the ordinary property watch, and
    -- the loop above prints one block per WATCHED ROOT, so those class counts
    -- would land in the header total while their breakdown printed nowhere.  So
    -- the Audio tally is printed here, and only when there is one.
    local audioCounts = report.byGroup['Audio']
    if audioCounts then
        local keys, n = {}, 0
        for k, v in pairs(audioCounts) do keys[#keys+1] = k; n = n + v end
        if n > 0 then
            table.sort(keys, function(a, b)
                if audioCounts[a] ~= audioCounts[b] then return audioCounts[a] > audioCounts[b] end
                return a < b
            end)
            out[#out+1] = string.format(
                '## Audio -- %d instance(s) OUTSIDE the watched roots, kept as properties', n)
            for _, k in ipairs(keys) do
                out[#out+1] = string.format('   %-24s %d', k, audioCounts[k])
            end
            out[#out+1] = ''
        end
    end
    if #report.missing > 0 then
        out[#out+1] = '## roots NOT found -- the watch is under-covered if this is not empty'
        for _, p in ipairs(report.missing) do out[#out+1] = '   MISSING ' .. p end
        out[#out+1] = ''
    end
    if #skipped > 0 then
        out[#out+1] = '## roots NOT watched, and why -- read this before believing a quiet room'
        for _, r in ipairs(rows) do
            if r.skipped then
                out[#out+1] = string.format('   %-34s %8d desc | %s', r.name, r.n, r.skipped)
            end
        end
        out[#out+1] = ''
    end
    local audio = report.audio or {found = {}, missing = {}}
    local inRoomSounds = 0
    for _, ent in ipairs(ents) do
        if ent.inst:IsA('Sound') then inRoomSounds = inRoomSounds + 1 end
    end
    out[#out+1] = string.format(
        '## audio-only scope -- playback hooks, plus a property watch on the mixer only (%d hook(s) attached, %d refused)',
        audioHooks, audioRefused)
    out[#out+1] = string.format('   %-24s %d', 'Sounds inside the watched roots', inRoomSounds)
    for _, r in ipairs(audio.found) do
        out[#out+1] = string.format('   %-24s %s, %d descendant(s), %d Sound(s) hooked',
            r.label, r.class, r.count, r.sounds or 0)
    end
    for _, m in ipairs(audio.missing) do
        out[#out+1] = '   MISSING ' .. m
    end
    -- The decomposition is printed next to the total rather than instead of it,
    -- because those two numbers come from different counters -- one counted as
    -- instances were hooked, the other by walking `ents` after the fact -- and a
    -- disagreement between them is a bug in one of the two.  Shown side by side,
    -- it is visible; summed into one number, it is not.
    out[#out+1] = string.format('   %-24s %d   (roots %d + audio-only %d)',
        'TOTAL Sounds hooked', hookedSounds, inRoomSounds, #audioOnly)
    out[#out+1] = ''
    out[#out+1] = string.format('## roots watched (%d)', #report.found)
    for _, r in ipairs(report.found) do
        out[#out+1] = string.format('   %-34s %-12s %8d descendants %8d parts',
            r.path, r.class, r.count, r.parts or 0)
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
    -- Sorted by the flat index, which is base + i: because entries were appended
    -- in registration order their bases are ascending, so sorting on j sorts by
    -- root-then-path without ever building a path string to sort on.
    local keys = {}
    for _, ent in ipairs(ents) do
        if ent.live ~= false then
            for i = 1, #ent.props do
                local j = ent.base + i
                if hits[j] > 0 then keys[#keys+1] = j end
            end
        end
    end
    table.sort(keys)
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
        out[#out+1] = string.format('%-18s %s.%s = %s   [was %s, %d change(s)]',
            ent.group, ent.path, ent.props[i], fmt(vals[j]), fmt(org[j]), hits[j])
    end
    return table.concat(out, NL) .. NL
end

-- Everything judged ambient, and the count that got it there.  Kept separate
-- from changes.log on purpose: the point of dropping those keys is to stop them
-- filling the timeline, and a line per key announcing "still ambient" would
-- refill it with the same noise.  This file is the disclosure that makes the drop
-- honest rather than silent -- a key that is not in changes.log is named here, so
-- "absent from the log" and "never moved" can never be confused.
-- Forward-declared for the fourth time in this file, and the harness caught this
-- one on its first run after the change rather than at 3am in the original game:
-- judgedCount is defined BELOW suppressedReport, so a `local function` down there
-- left the call above it resolving to a GLOBAL -- nil -- and the report raised on
-- the first tick it was asked for.  Adding a helper next to the others is exactly
-- how this happens; the definition below therefore drops its `local`.
local judgedCount

local function suppressedReport()
    local list = {}
    for j, s in pairs(ambient) do
        list[#list+1] = string.format('%-18s %s.%s   [%d change(s) by t=%.1fs, first move t=%.1fs]',
            s.ent.group, s.ent.path, s.ent.props[s.i], hits[j], s.tick, s.first)
    end
    table.sort(list)
    local out = {}
    out[#out+1] = string.format('# %d key(s) judged ambient: moved more than %d times without going quiet for %d scans (t=%.1fs)',
        #list, CONFIG.NoisyAfter, CONFIG.QuietScans, now() - startedAt)
    out[#out+1] = '# Their current values and change counts are still in summary.txt.'
    out[#out+1] = string.format(
        '# %d key(s) judged discrete: went quiet for %d scans without filling the ring, so',
        judgedCount(), CONFIG.QuietScans)
    out[#out+1] = '# their held lines were written out and logging them is not a guess. A key that'
    out[#out+1] = '# IS in changes.log and is NOT counted here was released by the report drain.'
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

-- How many keys were released as EVENTS -- quiet long enough that their held
-- lines went out -- that are NOT also ambient.  The `not ambient` half is the
-- whole point: a key can be tagged 'discrete' by the RESUMED branch while still
-- being suppressed (an ambient spinner that stops for a while is still ambient),
-- and counting those would make this number say "logged" about keys the reader
-- cannot find in changes.log.  The number has to match the sentence next to it.
--
-- This is what makes releaseQuiet() observable at all.  Until it existed, `judged`
-- was written in two places and read in none, so deleting the entire quiet-release
-- rule left every artifact byte-identical and the mutation suite green -- the
-- release only shortened how long a line waited for the next Watch.Report() drain,
-- and nothing on disk recorded the difference.
function judgedCount()
    local n = 0
    for j, v in pairs(judged) do
        if v == 'discrete' and not ambient[j] then n = n + 1 end
    end
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
    -- Set here rather than down at the hold, because an ambient key can `return`
    -- below without ever reaching the line that used to set it.  It would still
    -- count its moves and still update vals[j], so summary.txt was never WRONG --
    -- it was just left stale for as long as the only things moving were the noisy
    -- ones, which during a start-up is exactly the stretch a reader is watching.
    summaryDirty = true
    local label = string.format('%s.%s', ent.path, ent.props[i])
    local line = string.format('%s | %-18s | %s | %s | %s',
        stampText, ent.group, label, fmt(old), fmt(new))
    if ambient[j] then
        -- Quiet ticks between the last move and this one.  tick - prev is the
        -- distance between moves, so a gap of one scan means zero quiet scans --
        -- which is why the band is compared against this and not against
        -- tick - prev.  Without it a key that moves on every OTHER scan re-arms on
        -- the quiet tick between two moves and would have its ring dropped and
        -- rebuilt forever, reporting a spinner that never stopped as one event per
        -- cycle: measured on run two of the room watcher, 2,211 announce pairs
        -- against 1,942 keys that were not clocks at all.
        local quietTicks = tick - prev - 1
        if quietTicks < CONFIG.QuietScans then
            return
        end
        -- It went quiet for long enough to count as stopped.  A spinner that stops
        -- is an event, so the resume is announced, the key is logged normally
        -- again, and a fresh ring starts with this very move.
        judged[j] = 'discrete'
        held[j] = {}
        logLines[#logLines+1] = string.format(
            '%s | %-18s | %s | RESUMED after %d quiet scan(s) | %s',
            stampText, ent.group, label, quietTicks, fmt(new))
    end
    -- ===== THE HEART OF IT: HOLD, DO NOT WRITE-THEN-ERASE =====
    -- The first design wrote every line immediately and tried to take the ambient
    -- ones back once a key had moved enough times to prove what it was.  That
    -- cannot work, and the measurement is unambiguous: the sink APPENDS, so by the
    -- time the ninth move tripped the rule, moves one through eight had already
    -- been flushed to disk.  Run four of the room watcher recorded 1,891 keys as
    -- "8 line(s) erased" while the file still held every one of those lines -- the
    -- erasure was real in memory and invisible on disk.  A line has to be withheld
    -- BEFORE it is written, not removed after, which is why this ring exists.
    --
    -- Overflowing the ring is the entire test, and there is no clock on it.  An
    -- earlier version promoted a key to "an event" a fixed number of scans after
    -- its first move if it had not overflowed by then, and that is wrong for
    -- exactly the keys this exists to catch: run three left 1,045 lines behind,
    -- led by two chamber fans at 47 and 46 lines each whose first move was
    -- followed by a 32-second gap.  They were certified as events before they had
    -- shown what they were.  Age is not evidence; the ring filling is.
    local list = held[j]
    -- The tick travels with the line, not just with the text.  A ring is released
    -- several scans after the moves that filled it, and a scan can hold many keys
    -- at once, so without this the batch would be written in pairs() order --
    -- arbitrary -- and a start-up cascade would reach the log shuffled.  That is
    -- not a cosmetic problem for THIS file: the order of the cascade is the answer
    -- it was built to produce.
    list[#list+1] = {tick = tick, text = line}
    if #list > CONFIG.NoisyAfter then
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
-- A full pass over `held` every scan is affordable because `held` only ever holds
-- keys with un-written lines: a ring is released on quiet and dropped on overflow,
-- so what is in here is at most the keys that moved in the last QuietScans scans.
--
-- The released lines are MERGED AND SORTED, not appended key by key.  A scan can
-- release a dozen keys at once, and appending them as pairs() produces them makes
-- the batch's internal order arbitrary -- so the log would show the cascade in an
-- order that never happened.  Sorting by tick puts the whole batch back in move
-- order; ties are broken by the key index, which is stable and gives one
-- deterministic file for two runs of the same input.
local function releaseQuiet()
    local batch = {}
    for j, list in pairs(held) do
        -- The empty check comes FIRST and it is not an optimisation: `held` has an
        -- entry for every registered key, most of them empty, and a key that has
        -- never moved has no lastTick to subtract from -- so testing the age
        -- before testing the list is an arithmetic-on-nil error on the very first
        -- scan, inside a spawned thread, where nothing catches it and the whole
        -- loop dies without writing another byte.  Measured: that is exactly what
        -- happened on the first run of this design in our own place, which stopped
        -- after rooms.txt and inventory.txt and never produced a timeline at all.
        if #list > 0 and lastTick[j] and tick - lastTick[j] > CONFIG.QuietScans then
            for k = 1, #list do
                batch[#batch+1] = {tick = list[k].tick, key = j, text = list[k].text}
            end
            -- Emptied in place rather than replaced: register() only builds this
            -- table once per key, and a table per release would be one allocation
            -- per key per burst for the whole run.
            for k = #list, 1, -1 do list[k] = nil end
            judged[j] = 'discrete'
        end
    end
    table.sort(batch, function(a, b)
        if a.tick ~= b.tick then return a.tick < b.tick end
        return a.key < b.key
    end)
    for _, item in ipairs(batch) do logLines[#logLines+1] = item.text end
    return #batch
end

-- ========== THE SCAN ==========
local function scan()
    local t0 = os.clock()
    -- Per scan, not cumulative: the number a reader wants is what the LAST pass cost
    -- and how many frames it took, since that is the pair the duty sleep is derived
    -- from.  A cumulative count would only ever grow and would say nothing about the
    -- scan being reported beside it.
    blockYields = 0
    -- The clock is read once per scan, not once per change.  A single tick can move
    -- thousands of properties, and stamping each one separately would both cost a
    -- syscall each and report them as spread over a second in which they all moved
    -- together -- which reads as a timeline and is not one.
    local st = stamp()
    -- The slice this scan is currently in, and its position in the walk.  The stamp
    -- is re-taken after every yield, and that is not bookkeeping: the comment above
    -- says the clock is read once per scan so that everything which moved together
    -- carries one time.  A scan that now spans several frames would make that claim
    -- false in the other direction -- changes seconds apart stamped as one instant --
    -- so the unit of "together" becomes the slice, which is still the truth.
    local sliceAt = os.clock()
    local walked = 0
    for _, ent in ipairs(ents) do
        walked = walked + 1
        if walked % SLICE_CHECK == 0 then
            local fresh = breathe(sliceAt)
            if fresh ~= nil then
                sliceAt = fresh
                st = stamp()
            end
        end
        local inst = ent.inst
        -- Reading a property off a destroyed instance is fine; its Parent just
        -- goes nil.  Reported once and then the entry is retired, so a part that
        -- is rebuilt mid-run does not read as a silent no-op forever.
        if inst.Parent == nil and ent.live then
            ent.live = false
            logLines[#logLines+1] = string.format('%s | %-18s | %s | DESTROYED',
                st, ent.group, ent.path)
            summaryDirty = true
        elseif ent.live then
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
    -- after every move and slow the whole log down by a tick.
    releaseQuiet()
    -- After the walk, and cheap.  Its job is not to catch sounds -- the hooks do
    -- that -- but to catch a hook that did not attach.
    pollAudio()
    scanMs = (os.clock() - t0) * 1000
end

-- Writes out whatever is still held at the end of a run.  Normally a key's ring is
-- released by releaseQuiet a few scans after it stops moving, so this only catches
-- keys that were still moving when the run ended -- but those are exactly the keys
-- near the END of a start-up, and losing them would lose the most interesting part
-- of the timeline to a bookkeeping detail.  Safe to call twice.
local function drainHeld()
    local pending = {}
    for j, list in pairs(held) do
        for k = 1, #list do
            pending[#pending+1] = {tick = list[k].tick, key = j, text = list[k].text}
        end
        held[j] = {}
    end
    -- Per LINE, not per key.  Sorting whole rings by their first move -- which is
    -- what this did at first -- keeps each key's ring intact but interleaves the
    -- keys wrongly: every line of an early-starting key lands before every line of
    -- a later one, even the lines that happened after it.  The tick is carried by
    -- each line precisely so this can be exact.
    table.sort(pending, function(a, b)
        if a.tick ~= b.tick then return a.tick < b.tick end
        return a.key < b.key
    end)
    for _, item in ipairs(pending) do logLines[#logLines+1] = item.text end
end

-- ========== THE RECORDING WINDOW ==========
-- The timeline is the part of this watcher the operator asked for and the part he
-- then bounded: 「我进控制室之后，按下开机拉杆开始记录，游戏时间到12：00结束记录」.
-- Everything below is that sentence, and the two design decisions in it are worth
-- stating because both are load-bearing:
--
-- 1. THE WINDOW GATES RECORDING, NOT WATCHING.  The scan, the property watch, the
--    counters, the ambient judgement and the audio hooks all keep running while the
--    window is shut.  Only the two TIMELINE files are withheld (changes.log and
--    audio.txt).  That is deliberate: a watcher that only STARTED looking at the
--    lever would have no baseline, so its first post-lever line would describe a
--    move from a value it never read -- and the state files, which are not gated,
--    stay complete so nothing that moved before the lever is unaccounted for.
--
-- 2. A WINDOW THAT NEVER OPENS MUST NOT EAT THE RUN.  The operator gets one shift.
--    So the lever is not the only way in: the game's own `Stats.GameActive` is the
--    same event read off a different instance, and if the ClickDetector cannot be
--    resolved (renamed part, no ClickDetector, streaming not arrived) the flag opens
--    the window and window.txt names the fallback.  And if BOTH fail, the withheld
--    timeline is still written out when the run ends, under a marker that says the
--    window never opened -- a diagnosis, not an empty directory.
--
--    NOT "when the dial reaches 12:00", which is what this said until it was read
--    against the code.  The dial is the window's CLOSE rule and closeWindow refuses a
--    window that was never open, so a run whose window never opened can never be
--    ended by the dial -- it ends the way every run ends, the loop stopping.  The
--    wrong version was not harmless: it described a trigger that cannot fire, so
--    anyone reading only this paragraph would have believed a --nowindow run had a
--    clock-based exit and never gone looking for one.  The scenario that tests it
--    (`--nowindow`) presses the operator's RightControl instead, precisely because
--    nothing else can end that run.
-- workspace, lowercase, for the same reason the census uses it: `Workspace` capital
-- is NOT a global in Roblox and this file is never compiled by a Luau parser before
-- it is injected.  Written as `Workspace` at first, and the harness caught it --
-- resolvePath returned nil for every path, which in the game would have meant no
-- lever hook, no clock, no fallback flag, and a window that never opens at all.  That
-- failure is silent by construction: the watcher would have watched normally and
-- withheld the whole shift, and window.txt would have said "the path does not
-- resolve" about three paths that each exist.
local function resolvePath(tokens)
    local node = workspace
    for _, token in ipairs(tokens) do
        if node == nil then return nil end
        local ok, nxt = pcall(function() return node:FindFirstChild(token) end)
        if not ok then return nil end
        node = nxt
    end
    return node
end

-- The shift dial, parsed with the recorder's mapping on purpose -- 12:00PM is 0,
-- 1:00PM is 60, 12:00AM is 720, 11:59AM is 1439 -- because the two scripts describe
-- one shift and must not disagree about what time it was.  The RAW TEXT is kept
-- beside the number and is what window.txt prints: a dial whose format this file
-- has never seen must degrade to the string that is really on the screen rather
-- than to a number that is quietly wrong.
local function readClock()
    local label = resolvePath(CONFIG.Window.ClockPath)
    if label == nil then return nil end
    local ok, raw = pcall(function() return label.Text end)
    if not ok or type(raw) ~= 'string' or raw == '' then return nil end
    local text = string.gsub(raw, '%s+', ' ')
    local hh, mm, ap = string.match(text, '(%d+):(%d+)%s*(%a%a)')
    if hh == nil then
        clockText = text
        return nil
    end
    local h, m = tonumber(hh), tonumber(mm)
    local pm = string.upper(ap) == 'PM'
    local mins
    if pm and h == 12 then mins = m
    elseif pm then mins = h * 60 + m
    elseif h == 12 then mins = 720 + m
    else mins = 720 + h * 60 + m
    end
    clockText, clockMins = text, mins
    return mins
end

-- One line into the timeline itself.  The window's edges belong in changes.log and
-- not only in window.txt: a reader scanning the timeline for "when did it start"
-- must not have to open a second file to learn where the file starts meaning.
local function windowMark(what, note)
    logLines[#logLines+1] = string.format(
        't=%010.2f | %-18s | %s | %s', now() - startedAt, 'WINDOW', what, note)
    -- Deliberately NOT behind the window gate: these two lines are the boundary and
    -- are written even by the closing path that fires when the window never opened.
    return true
end

local function openWindow(why)
    if windowState ~= 'waiting' then return false end
    windowState = 'open'
    windowOpenedAt = now() - startedAt
    windowWhy = why
    -- The withheld lines are counted and DROPPED here rather than written out: this
    -- is the instruction.  `WindowWithheld*` is what keeps the drop honest, and the
    -- state files are ungated, so the pre-lever room is still described -- by
    -- summary.txt, which lists every property that has moved with its count and its
    -- current value.
    --
    -- AND THE HELD RINGS, which are the same pre-window evidence wearing a different
    -- hat.  A key that was still moving when the lever was thrown has its lines in a
    -- ring, not in logLines -- releaseQuiet writes them out scans later, long after
    -- this ran -- so counting only logLines reported `withheld=0 line(s)` on top of a
    -- timeline that then went on to contain t=1 lines ABOVE its own t=3 OPEN marker.
    -- A count that denies what the file beneath it plainly shows is worse than no
    -- count, and the harness read exactly that pair on the first run of this wiring.
    -- The operator's rule is about what gets RECORDED, so the rings go the same way
    -- as everything else: into the count, out of the file.
    local ringed = 0
    for j, list in pairs(held) do
        ringed = ringed + #list
        held[j] = {}
    end
    windowWithheldLog = windowWithheldLog + #logLines + ringed
    windowWithheldAudio = windowWithheldAudio + #audioLines
    logLines, audioLines = {}, {}
    windowMark('OPEN', string.format(
        'recording begins: %s | %d line(s) before this were withheld by the rule',
        why, windowWithheldLog))
    windowDirty = true
    healthDirty = true
    return true
end

local function closeWindow(why)
    if windowState ~= 'open' then return false end
    windowState = 'closed'
    windowClosedAt = now() - startedAt
    windowClosedWhy = why
    windowMark('CLOSE', string.format(
        'recording ends: %s | %d line(s) recorded over %.1fs',
        why, recordedLines, windowClosedAt - (windowOpenedAt or 0)))
    windowDirty = true
    healthDirty = true
    return true
end

local function windowReport()
    local out = {}
    out[#out+1] = '# the recording window -- when this run was being recorded, and what was not'
    out[#out+1] = string.format('# rule: %s', CONFIG.Window.Enabled
        and 'from the start-up lever to the shift dial wrapping past 12:00 PM'
        or 'DISABLED in CONFIG -- the timeline runs from injection to the stop key')
    out[#out+1] = string.format('state=%s', windowState)
    out[#out+1] = string.format('opened_at=%s why=%s',
        windowOpenedAt and string.format('%.2f', windowOpenedAt) or 'not yet',
        windowWhy or '(nothing has opened it)')
    out[#out+1] = string.format('closed_at=%s why=%s',
        windowClosedAt and string.format('%.2f', windowClosedAt) or 'not yet',
        windowClosedWhy or '(still open, or never opened)')
    out[#out+1] = string.format('withheld_before_open=%d line(s), plus %d audio line(s)',
        windowWithheldLog, windowWithheldAudio)
    out[#out+1] = string.format('recorded=%d line(s)', recordedLines)
    -- The lever half, including the failure, because "it opened on the fallback" and
    -- "it never opened" are the two readings a reader has to be able to tell apart
    -- from a directory that has a timeline in it either way.
    out[#out+1] = string.format('lever_path=%s',
        table.concat(CONFIG.Window.LeverPath, '.'))
    out[#out+1] = string.format('lever_hooked=%s%s', tostring(leverHooked),
        leverHooked and '' or ('  reason=' .. (leverMiss or 'not looked for yet')))
    out[#out+1] = string.format('opened_by_fallback_flag=%s', tostring(flagOpened))
    -- The dial half.  clockText is printed even when it did not parse, so a run that
    -- ended on the wrong reading (or did not end at all) is diagnosable from the
    -- product instead of from another attempt.
    out[#out+1] = string.format('clock_path=%s', table.concat(CONFIG.Window.ClockPath, '.'))
    out[#out+1] = string.format('clock_text=%s', clockText or '(never read)')
    out[#out+1] = string.format(
        'clock_mins=%s  (the close rule is the dial FALLING by >= %d minutes, %d poll(s) in a row)',
        clockMins and tostring(clockMins) or '(did not parse)', CONFIG.Window.WrapDropMins,
        CONFIG.Window.EndPolls)
    -- What the close rule was actually weighing, printed whether or not it fired.  A
    -- run that did not end has to say why from inside its own product: "the dial never
    -- fell" and "the dial fell and the polls reset it" are the same silence otherwise.
    out[#out+1] = string.format('dial_previous_mins=%s', prevClockMins and tostring(prevClockMins) or '(never read)')
    out[#out+1] = string.format('wrap_latched_from=%s  (set when the fall was seen; cleared if the dial came back up)',
        wrapFrom and tostring(wrapFrom) or '(not latched)')
    out[#out+1] = string.format('wrap_polls=%d of %d', clockEndPolls, CONFIG.Window.EndPolls)
    out[#out+1] = ''
    return table.concat(out, NL)
end

-- Called once per scan, before the flush, so a marker written here leaves in the
-- same flush as the tick that caused it.
local function windowStep()
    if not CONFIG.Window.Enabled then
        if windowState == 'waiting' then openWindow('the window is DISABLED, so it opened at injection') end
        return
    end
    -- The fallback flag is read every scan whether or not the lever was found: a
    -- ClickDetector that exists but never fires (a click the game routed elsewhere,
    -- a part behind something) is a failure the hook cannot see, and the flag can.
    if windowState == 'waiting' then
        local flag = resolvePath(CONFIG.Window.OpenFlagPath)
        if flag ~= nil then
            local ok, v = pcall(function() return flag.Value end)
            if ok and v == true then
                flagOpened = true
                openWindow('Stats.GameActive went true (the start-up lever was thrown)')
            end
        end
    end
    local mins = readClock()
    -- A read that did not parse changes nothing: it neither arms the latch nor
    -- counts toward it nor clears it.  Returning here is what keeps `prevClockMins`
    -- meaning "the last reading", so a monitor that blanks for a poll does not look
    -- like a dial that fell.
    if mins == nil then return end
    -- THE LATCH: the dial is monotonic inside a shift, so a fall this big is the
    -- handover and nothing else can be.  Each poll is compared against the previous
    -- poll rather than against a constant, which is why this needs no knowledge of
    -- when the shift started or how far in this run is.
    if prevClockMins ~= nil and (prevClockMins - mins) >= CONFIG.Window.WrapDropMins then
        wrapFrom = prevClockMins
    end
    prevClockMins = mins
    if windowState ~= 'open' then
        -- The close rule is a rule about an OPEN window; a window that has not opened
        -- (or has already closed) must not be counting toward one.  Nothing is cleared
        -- here: a latch taken before the lever would still be the dial's own history.
        clockEndPolls = 0
        return
    end
    if wrapFrom ~= nil and mins < wrapFrom then
        clockEndPolls = clockEndPolls + 1
        if clockEndPolls >= CONFIG.Window.EndPolls then
            closeWindow(string.format('the shift dial wrapped past 12:00 PM (fell from %s to %s)',
                tostring(wrapFrom), clockText or tostring(mins)))
            -- Ending the recording ends the run.  The loop notices `running` on its
            -- next pass, drains the held rings and does the final flush -- so this
            -- is not a kill, it is the same orderly exit the stop key produces.
            running = false
        end
    else
        -- The COUNT is the protection: any poll whose reading is not below the
        -- pre-fall value resets it, and since the dial cannot go backwards, the poll
        -- after a mis-parse always reads higher than the value that mis-parse was
        -- compared against.  So one bad poll costs one poll.
        clockEndPolls = 0
        -- Clearing the latch here is DIAGNOSTIC HYGIENE, NOT A GUARD, and saying so
        -- is the point.  It changes no outcome: a poll that reaches this branch has
        -- already zeroed the counter, and a stale latch can only be re-satisfied by a
        -- reading below the old pre-fall value, which the dial can only produce at a
        -- real wrap -- where wrapping the same number again is the correct answer.
        -- Every state reachable from here behaves identically with or without it, so
        -- the value is not that it prevents something; it is that window.txt's
        -- `wrap_latched_from` must not keep pointing at a fall that was refuted.
        wrapFrom = nil
    end
end

-- The lever.  MouseClick and not a property change on the part: the click is the
-- operator's action, and it is the same event the recorder already labels
-- `StartUpLever` off this exact part -- so the two scripts agree about which press
-- opened the window.  Read-only: a connection is not an assignment.
--
-- WHY THE PATH RESOLVES TO A PART AND THE DETECTOR IS FOUND UNDER IT.  That is not a
-- guess about how the original is built; it is the shape the recorder's own live
-- output proves.  `CLICK StartUpLever` is printed only when
-- `labels[detector.Parent:GetFullName()]` hits, and that label was assigned to
-- `...StartUpBigLever.StartClickPart` -- so the detector's PARENT is the part
-- `StartClickPart`.  A flat tree (the detector itself named StartClickPart) would
-- have printed `path=Workspace.Consoles...` on every press instead, and the runs
-- that produced `CLICK StartUpLever` say which of those happened.
--
-- So there is ONE shape here and not a hedge between two.  A branch for a layout the
-- evidence rules out is the `pcall`-as-a-licence mistake in a different costume: it
-- would be unreachable, untested, and it would hide the real answer -- which is that
-- the game puts the detector under the part.  The miss below names the CLASS it
-- actually found, so if that ever turns out to be wrong the reading is a line in
-- window.txt and not a silent shift.
local function attachWindow()
    local part = resolvePath(CONFIG.Window.LeverPath)
    if part == nil then
        -- Names the path it failed on.  "the path does not resolve" is a state; the
        -- string below is the repair, and this is the only place the operator can find
        -- out WHICH path was looked for -- the config that holds it is injected code
        -- and there is no console in this run to print it to.
        leverMiss = 'the path does not resolve: ' .. table.concat(CONFIG.Window.LeverPath, '.')
    else
        local ok, cd = pcall(function() return part:FindFirstChildOfClass('ClickDetector') end)
        if not ok then
            leverMiss = string.format('the resolved instance could not be asked for a ClickDetector (%s)',
                tostring(cd))
        elseif cd == nil then
            local what = 'an instance whose class could not be read'
            pcall(function() what = part.ClassName .. ' ' .. part.Name end)
            leverMiss = 'the path resolves to ' .. what .. ', which carries no ClickDetector'
        else
            local connected = pcall(function()
                connections[#connections+1] = cd.MouseClick:Connect(function()
                    openWindow('the start-up lever was clicked at ' .. part:GetFullName())
                end)
            end)
            if connected then leverHooked = true else leverMiss = 'MouseClick could not be connected' end
        end
    end
    windowDirty = true
end


-- ========== HEALTH, AND WHY IT IS A FILE ==========
-- The two things this watcher used to say out loud -- "the sink is unreachable",
-- at the moment it happened, and a status line every ReportEvery scans -- were
-- diagnostics with a lifetime of one moment, in a window nobody is reading, on a
-- run that cannot be repeated.  health.txt is the same information with a
-- lifetime, and it is also the file that answers "is it still watching" without
-- anyone having to press a key: it is rewritten every ReportEvery scans, so a
-- health.txt whose t= has stopped advancing is itself the diagnosis.
--
-- sink_error is carried rather than just the DOWN flag.  "The sink is down" without
-- the reason is the finding that costs another round: PostAsync fails for a refused
-- connection, a wrong port, and a body the sink rejected, and those are three
-- different repairs.
local function health()
    local out = {}
    out[#out+1] = string.format(
        '# watcher health, rewritten every %d scans', CONFIG.ReportEvery)
    out[#out+1] = string.format(
        't=%010.2f tick=%d running=%s', now() - startedAt, tick, tostring(running))
    -- The window line sits high because it changes how the two files below are read.
    -- `queued=` on a run whose window never opened is a queue being held, not a lag,
    -- and `window=` is the only field that says which -- so a reader who stops after
    -- the first four lines has to have it.  window.txt carries the why; this is the
    -- one word, on the file that is rewritten every ReportEvery scans.
    out[#out+1] = string.format(
        'window=%s recorded=%d withheld=%d clock=%s',
        windowState, recordedLines, windowWithheldLog,
        clockMins and tostring(clockMins) or (clockText or 'unread'))
    out[#out+1] = string.format(
        'watched=%d props=%d moved=%d ambient=%d', #ents, totalProps, movedKeys,
        suppressedCount())
    -- scan_ms / sleep_ms / duty / yields are the lag fix's own report, and they are
    -- on this line rather than in a comment because the fix is a claim about a
    -- MACHINE: 2197 ms against a 1 s interval was measured on the operator's, and
    -- the only way to know whether the cure worked there is for the cured version to
    -- print the same four numbers.
    --
    -- WHAT scan_ms MEASURES, because it is not the whole cycle and reading it as one
    -- would make `duty` look like a wall-clock share when it is not.  scan_ms comes
    -- from os.clock(), which is CPU time -- it does not advance while the walk is
    -- yielded waiting for a frame.  So scan_ms is the Lua work in the last scan, and
    -- the frames that work was spread across are NOT in it.  duty is therefore that
    -- work against the wall-clock period, and it is the number to compare against
    -- DutyTarget: too high means the loop could not afford to sleep as long as the
    -- rule asked, which is a different failure from a scan that got slower.
    --
    -- The bias runs the safe way.  The true period is longer than
    -- scan_ms + Interval + sleep_ms by the frames the walk handed back, so the real
    -- share is at or below the printed duty -- a run that prints at or under the
    -- target has not exceeded it, and a run that prints over has earned a second
    -- look rather than a verdict.  The frames handed back are the game's, which is
    -- the point of handing them back, so counting them as a cost to the watcher
    -- would be counting the cure as the disease.
    local periodMs = scanMs + CONFIG.Interval * 1000 + sleepMs
    out[#out+1] = string.format(
        'queued=%d dropped=%d scan_ms=%.0f sleep_ms=%.0f duty=%.2f yields=%d (block_ms=%d target=%.2f)',
        #logLines, dropped, scanMs, sleepMs,
        periodMs > 0 and scanMs / periodMs or 0, blockYields,
        CONFIG.MaxBlockMs, CONFIG.DutyTarget)
    out[#out+1] = string.format(
        'sink=%s%s', sinkDown and 'DOWN' or 'ok',
        sinkDown and string.format(' since t=%.2f', sinkSince or -1) or '')
    out[#out+1] = 'sink_error=' .. (sinkError or 'none')
    -- Named here because the sink fields above are meaningless without it.  A run
    -- whose sink never confirmed anything has exactly two candidates -- the sink was
    -- unreachable, or this executor has no POST transport -- and TRANSPORT is the
    -- half of that answer which is knowable from inside the game.
    out[#out+1] = 'transport=' .. TRANSPORT
    -- The cumulative half, and the reason it is separate from the two lines above:
    -- `sink=` is a state and these are a history.  A run that was never taken writes
    -- sink_outages=0; a run that was taken late writes a non-zero total and the
    -- error text from the last refusal, and both of those are readable from a
    -- directory that was pulled up hours after the game closed.
    out[#out+1] = string.format(
        'sink_outages=%d sink_down_total=%.2fs sink_last_at=%s sink_last_error=%s',
        sinkOutages, sinkDownTotal,
        sinkLastAt and string.format('%.2f', sinkLastAt) or 'never',
        sinkLastError or 'none')
    out[#out+1] = string.format(
        'audio_hooks=%d refused=%d events=%d poll_only=%d dropped=%d err=%s',
        audioHooks, audioRefused, audioEvents, audioPollOnly, audioDropped,
        audioError or 'none')
    out[#out+1] = 'fatal=' .. (fatal or 'none')
    out[#out+1] = 'prefix=' .. PREFIX
    out[#out+1] = ''
    return table.concat(out, NL)
end

local function flush(force)
    -- THE WINDOW GATE, and it is one branch for both timeline files on purpose.  While
    -- the window is shut nothing is posted to changes.log or audio.txt -- but the
    -- lines are KEPT, not thrown away here, because there are two ways this can go:
    -- normally the lever opens the window and openWindow() counts and drops them, and
    -- if the window never opens the loop's exit path writes them out under a marker
    -- that says so.  A watcher that dropped them here would have no way to tell those
    -- two apart, and the second one costs the whole shift.
    local recording = (windowState == 'open') or (windowState == 'closed')
        or (not CONFIG.Window.Enabled)
    if recording and #logLines > 0 then
        post('changes.log', table.concat(logLines, NL) .. NL, true)
        recordedLines = recordedLines + #logLines
        logLines = {}
    end
    -- Audio goes out on the same tick it happened, not on the summary throttle.  A
    -- playback event is the whole point of the audio half and holding it for up to
    -- ten scans would put it out of order against changes.log, which is the one
    -- thing a timeline must not be.
    if recording and #audioLines > 0 then
        post('audio.txt', table.concat(audioLines, NL) .. NL, true)
        audioLines = {}
    end
    -- The last three files on the same throttle, each with its own dirty flag: a
    -- key that trips calls for a new suppressed.txt, but rewriting several large
    -- files every second is the sort of cost that shows up as jitter in the very
    -- timings this watcher exists to measure.
    local due = force or (tick % CONFIG.SummaryEvery == 0)
    if summaryDirty and due then
        summaryDirty = false
        post('summary.txt', summary(), false)
    end
    if suppressedDirty and due then
        suppressedDirty = false
        post('suppressed.txt', suppressedReport(), false)
    end
    if audioDirty and due then
        audioDirty = false
        post('audio_tally.txt', audioTally(), false)
    end
    -- window.txt is a state file, so it is NOT behind the gate above: it is the file
    -- that explains the gate, and a reader must be able to learn that the timeline
    -- was withheld by a rule rather than never produced.
    if windowDirty and due then
        windowDirty = false
        post('window.txt', windowReport(), false)
    end
    -- ReportEvery, not the `due` above.  `due` is the summary throttle that a forced
    -- report and the SummaryEvery counter share; health is on the interval the
    -- status line it replaced used, and folding it into `due` would have quietly
    -- made it three times more frequent than the thing it is standing in for.
    -- A sink transition sets the flag and waits for the next multiple of
    -- ReportEvery rather than writing immediately -- the transition is also the
    -- case where the post is most likely to fail, and a health.txt written on every
    -- failing tick would be the watcher hammering a sink that is already refusing
    -- it.  The flag is not lost, only the retry is paced.
    if healthDirty and (force or tick % CONFIG.ReportEvery == 0) then
        healthDirty = false
        post('health.txt', health(), false)
    end
end

-- ========== PUBLIC ==========
local Watch = {}

function Watch.Stop()
    running = false
    for _, c in ipairs(connections) do
        pcall(function() c:Disconnect() end)
    end
    connections = {}
    -- The ScreenGui this used to destroy is gone with the rest of the panel, so
    -- there is nothing to tear down but the connections above.  The flag below is
    -- what replaced it: the loop notices `running` on its next pass and then runs
    -- drainHeld() + flush(true), and health.txt is the file that has to come out of
    -- that -- `running=false` with a t= is how a reader tells "the operator stopped
    -- it" apart from "it died", which until now was two readings with the same shape
    -- (both are "the files stopped growing").
    healthDirty = true
    return true
end

function Watch.Report()
    drainHeld()
    summaryDirty = true
    suppressedDirty = true
    audioDirty = true
    -- healthDirty too, and this is the one that has to be here rather than merely
    -- set somewhere upstream: RightAlt is the key the operator presses when they
    -- want the state of the world on disk NOW, and "is it still watching, and is the
    -- sink still taking it" is the first question they are asking when they press
    -- it.  Without this line, Report() on a run that never touched the sink would
    -- write seven files and no health.txt.
    healthDirty = true
    -- And window.txt, for the same reason as health.txt and one more of its own:
    -- the lever hook is attached once, at the start, and this is the only way the
    -- operator can learn -- WHILE THE SHIFT IS STILL RUNNING AND STILL SAVEABLE --
    -- that the hook did not take.  It is a state file and therefore ungated, so it
    -- also answers "is what I am seeing in changes.log being withheld" without
    -- waiting for the close.
    windowDirty = true
    flush(true)
    return #ents, totalProps, movedKeys, suppressedCount()
end

function Watch.Status()
    return string.format(
        'running=%s tick=%d watched=%d props=%d moved=%d ambient=%d queued=%d dropped=%d scan=%.0fms sink=%s audio_hooks=%d/%d audio_events=%d poll_only=%d audio_dropped=%d audio_err=%s fatal=%s prefix=%s',
        tostring(running), tick, #ents, totalProps, movedKeys, suppressedCount(),
        #logLines, dropped, scanMs, sinkDown and 'DOWN' or 'ok',
        audioHooks, audioHooks + audioRefused, audioEvents, audioPollOnly,
        audioDropped, audioError or 'none', fatal or 'none', PREFIX)
        .. string.format(' audio_pre=%d sounds=%d groups=%d', audioPreexisting, soundTotal, groupTotal)
end

-- ========== THE BOOT LINE ==========
-- Written by Start before it spawns anything, and it is the only artifact that
-- exists before a single instance has been walked.
--
-- WHY IT HAS TO EXIST.  On the operator's 2026-09-27 run the sink received
-- NOTHING from this watcher for a whole shift -- no originalwatch/ directory at
-- all -- and from the reading end that is one reading with three causes that
-- cannot be told apart afterwards:
--
--   1. the script was never injected, or died at load, before Start;
--   2. it was injected and died inside the census;
--   3. it was injected and was still censusing when the shift ended.
--
-- The run cannot be repeated to find out -- the operator's own rule is that
-- starting and stopping the reactor happens ONCE -- so the ambiguity has to be
-- removed before the walk rather than diagnosed after it.  With this file: no
-- hello.txt means case 1 and nothing else; hello.txt with no tree.txt narrows it
-- to 2 and 3; and error.txt then separates those, because the walk below is
-- guarded and names its own phase when it dies.  Three readings, three artefacts.
--
-- AND WHY IT IS SYNCHRONOUS.  Start is called from the loading thread, so a post
-- here has already completed when the injection call returns, whereas the same
-- post inside the spawn would leave the "was it even injected" window open for
-- exactly as long as the census it is meant to bracket -- which is the whole
-- window that matters.  The cost is one HTTP round trip on that thread, and the
-- sink is on localhost.  The harness cannot see this difference (its `task.spawn`
-- runs the body immediately), so this is a documented choice, not a tested one.
local function bootReport()
    return string.format(
        '# the watcher was injected and is starting its census (build %s)' .. NL ..
        'build=%s' .. NL ..
        'transport=%s' .. NL ..
        'prefix=%s' .. NL ..
        'sink=%s' .. NL ..
        't=%s' .. NL ..
        'hotkeys=RightAlt writes every file out now; RightControl stops' .. NL ..
        'note=tree.txt is written after the census finishes.  If this is the only' ..
        ' file you have, the watcher was injected but never finished starting --' ..
        ' read error.txt for a start-up death, and give the census longer before' ..
        ' assuming either.' .. NL,
        CONFIG.Build, CONFIG.Build, TRANSPORT, PREFIX, CONFIG.Sink, stamp())
end

-- Everything the watcher does before it has one instance registered: the census,
-- the root selection, and the four artifacts that describe what it decided.  It is
-- a NAMED function rather than a block inside Start for one reason -- it is the
-- unit that has to be guarded, and a guard around an anonymous function cannot be
-- pointed at by a test, so the guard itself would be untestable.
--
-- The census comes first, and it is written out BEFORE anything is registered, so
-- that even if the walk below dies the reader still has the tree.  A watcher that
-- fails after its census has still answered the question it was injected for.
local function bootWalk()
    local rows, total, nChildren = census()
    local picked, skipped = selectRoots(rows)
    post('tree.txt', censusReport(rows, total, nChildren, picked, skipped), false)

    buildIndex(rows, picked)
    soundTotal = hookedSounds
    groupTotal = 0
    for _, ent in ipairs(ents) do
        if ent.inst:IsA('SoundGroup') then groupTotal = groupTotal + 1 end
    end
    post('rooms.txt', coverageReport(rows, total, nChildren, picked, skipped), false)
    post('inventory.txt', inventory(), false)
    -- Written up front even though they are empty, so a reader who finds no
    -- suppressed.txt or no audio_tally.txt learns "nothing was suppressed" and
    -- "nothing was audible" from a file rather than from its absence.
    post('suppressed.txt', suppressedReport(), false)
    post('audio_tally.txt', audioTally(), false)
end

function Watch.Start()
    if running then return false, 'already running' end
    running = true
    startedAt = now()
    post('hello.txt', bootReport(), false)

    -- THE LEVER HOOK GOES ON FIRST, BEFORE THE CENSUS, AND THE MEASUREMENT IS WHY.
    -- This call used to sit after `pcall(bootWalk)` and the comment defending that
    -- order said "the census finishes in seconds".  It does not.  On the original
    -- place the census is 71236 instances and 557548 watched properties, and the
    -- first run that ever executed this file put its first changes.log line at
    -- t=47.93s -- so the hook, which is the ONLY thing that opens the recording
    -- window, arrived 48 seconds late.  The operator throws the lever at about
    -- t=20s: the recorder's own timeline brackets `CLICK StartUpLever` between
    -- `S 40 t=18.11` and `S 67 t=27.03`, and the walk from the spawn to the console
    -- it was supposed to give cover for takes fifteen of those seconds, not forty.
    --
    -- The failure that produced was the worst shape a failure can have here: the
    -- lever resolved, the ClickDetector was found, the connection took, and
    -- window.txt still said `lever_hooked=true` *next to* `opened_at=not yet` --
    -- "nothing opened it" -- which is also exactly what a typo in LeverPath says.
    -- A correct hook that is 28 seconds too late is indistinguishable, in the
    -- artifacts, from a hook that was never made.
    --
    -- And the cost is not a line of data.  The window runs from the lever (thrown at
    -- about 11:50 PM) to the noon handover, which is 730 dial minutes -- roughly
    -- thirteen real minutes at the measured one dial minute per real second -- so
    -- missing the lever means the recording never starts, and the
    -- operator can spend that power-up ONCE -- 「我没办法随便开关机，开机/关机只能一次」
    -- -- so the price of the ordering was the whole run.
    --
    -- Moving it is safe because it depends on nothing the census produces:
    -- resolvePath walks down from `workspace` with FindFirstChild and never
    -- consults `ents`, the root selection, or the budgets.  The clock and the
    -- fallback flag are resolved the same way and on the same tick.  window.txt
    -- still records whether the hook took, so the reading above is unchanged --
    -- only the moment it takes has moved.
    attachWindow()

    task.spawn(function()
        -- GUARDED, AND THE GUARD NAMES ITS PHASE.  The scan loop below has been
        -- guarded since it was written, for the reason its own comment gives: a
        -- diagnostic that dies from its own bug is worse than no diagnostic, and
        -- the death is silent by construction because nothing awaits a spawned
        -- thread.  That argument applies to the walk that runs BEFORE the loop, and
        -- applies with more force -- a death here registers nothing, so there is no
        -- loop left to notice -- and this half was left unguarded.  Both halves now
        -- write the same error.txt with a different first line, so the two deaths
        -- are not one reading: whichever file you are holding, its opening tells you
        -- which walk it was.
        local booted, bootErr = pcall(bootWalk)
        if not booted then
            fatal = tostring(bootErr)
            post('error.txt', string.format(
                '# the watcher died during its start-up, before anything was watched' ..
                ' (t=%.1fs)' .. NL .. '%s', now() - startedAt, fatal), false)
            running = false
            return
        end

        -- One line here so health.txt exists from the first flush, on a run that
        -- never changes the sink state and would otherwise not write it until its
        -- first SummaryEvery.
        healthDirty = true
        -- attachWindow() is NOT here any more -- it is called synchronously in
        -- Start(), above, and the comment there carries the measurement that moved
        -- it.  Nothing about the census is needed to take the hook; leaving the call
        -- in this thread is what made it late by however long the walk took.
        if UserInputService then
            connections[#connections+1] = UserInputService.InputBegan:Connect(function(input, processed)
                if processed then return end
                -- RightAlt, NOT RightShift, and the reason is not taste.
                -- TRG_original_recorder.luau binds RightShift to SEAL: pressing it
                -- ends that recording and stops the collector.  Both scripts are
                -- meant to run side by side in the same session, on an attempt the
                -- operator can spend only ONCE -- so a key shared with the recorder
                -- is a key that destroys the other half of the run when someone
                -- presses it meaning "flush the watcher now".  The watcher is the
                -- one that can move, because its key is a convenience and the
                -- recorder's is a commitment.  RightControl stays as the stop,
                -- since neither script used it.
                if input.KeyCode == Enum.KeyCode.RightAlt then
                    Watch.Report()
                elseif input.KeyCode == Enum.KeyCode.RightControl then
                    Watch.Stop()
                end
            end)
        end

        while running do
            task.wait(CONFIG.Interval)
            tick = tick + 1
            -- Guarded, and the guard writes a file.  A diagnostic that dies from
            -- its own bug is worse than no diagnostic, and the failure mode is
            -- silent by construction: the loop lives in a spawned thread, so
            -- nothing awaits it, nothing catches it, and the only symptom is that
            -- the files stop growing -- which looks identical to a watcher that is
            -- running and finding nothing.  So the error goes to the sink, where it
            -- survives the session.
            local walked, walkErr = pcall(scan)
            if not walked then
                fatal = tostring(walkErr)
                post('error.txt', string.format(
                    '# the watcher stopped on tick %d (t=%.1fs)' .. NL .. '%s', tick,
                    now() - startedAt, fatal), false)
                -- No console line: error.txt was just written and carries the same
                -- text.  The loop is about to exit, so the flush below is what gets
                -- health.txt out with fatal= set, which is how a reader holding the
                -- directory -- and not a console that closed with the session --
                -- learns the last tick before the death.
                healthDirty = true
                running = false
                break
            end
            -- THE DUTY CAP.  The other half of the lag fix, and the half that can be
            -- derived rather than chosen (MaxBlockMs carries the measurement and the
            -- reasoning).  Yielding inside the scan fixes the freeze; it cannot fix
            -- the SHARE, because the same work still has to happen.
            --
            -- `scanMs` and not os.clock() around the call: scan() measures itself
            -- from the clock, and it already accounts for the frames its own yields
            -- spent waiting -- so the sleep is derived from what the pass actually
            -- cost the game, which is the quantity the duty ratio is about.  A pass
            -- that measured its own work without the yields would under-sleep by
            -- exactly the amount it had already taken in frames.
            --
            -- Emitted only when it exceeds Interval, so the ordinary case (a small
            -- place, a fast machine) is bit-for-bit the loop it was: the top of this
            -- loop still waits Interval, and this adds the remainder.  That is also
            -- what keeps the fixture honest, where a whole scan is under a
            -- millisecond and this branch is never taken.
            local work = scanMs / 1000
            local idle = work * (1 - CONFIG.DutyTarget) / CONFIG.DutyTarget
            sleepMs = idle > CONFIG.Interval and (idle - CONFIG.Interval) * 1000 or 0
            if sleepMs > 0 then task.wait(sleepMs / 1000) end
            -- Bounded queues.  Audio needs its own bound: it is flushed every tick
            -- so it can only grow while the sink is down -- but "only while the
            -- sink is down" is exactly the case the queue exists for, and a sound
            -- a script re-plays every tick would otherwise grow this table for the
            -- whole outage.  Sound names are in audio_tally.txt, which is bounded
            -- by the number of Sounds, so a dropped audio line is still accounted
            -- for somewhere.
            if #audioLines > CONFIG.MaxQueue then
                local keep = {}
                for k = #audioLines - CONFIG.MaxQueue + 1, #audioLines do
                    keep[#keep+1] = audioLines[k]
                end
                audioDropped = audioDropped + (#audioLines - #keep)
                audioLines = keep
            end
            if #logLines > CONFIG.MaxQueue then
                -- table.remove(_, 1) is O(n) and would turn a bounded queue into a
                -- quadratic stall exactly when the sink is down and the queue is
                -- longest, so the overflow is dropped by rebuilding once.
                local keep = {}
                for k = #logLines - CONFIG.MaxQueue + 1, #logLines do
                    keep[#keep+1] = logLines[k]
                end
                dropped = dropped + (#logLines - #keep)
                logLines = keep
            end
            -- Before the flush, so the OPEN/CLOSE marker written by this tick leaves
            -- in the same tick's post.  A window edge one flush late is a boundary
            -- that is wrong by one scan in a file whose whole purpose is telling the
            -- reader where the boundary is.
            windowStep()
            flush(false)
            -- The per-ReportEvery status line that used to be printed here is now a
            -- health.txt on that same interval, and it carries strictly more: the
            -- same counters plus the sink error text, the audio error, and the one
            -- field a console line could never have -- t=, which a reader compares
            -- against the previous health.txt to see whether the watcher is still
            -- alive.  Nothing here reads ReportEvery because flush(false) already
            -- does; the number did not change, only where it is reported.
        end
        -- THE WINDOW NEVER OPENED.  The rule is that recording starts at the lever,
        -- so a run where nothing opened the window would post an EMPTY changes.log
        -- and the whole shift would read as "nothing happened" -- which is the same
        -- reading as "the watcher was never injected" minus the one file that
        -- separates them.  The withheld lines are therefore written out under a
        -- marker that names them for what they are.
        --
        -- This is not a softening of the rule.  The rule decides what the window
        -- MEANS; it cannot decide that a reader gets a truncated file with no note.
        -- window.txt still reports state=closed with why="the window never opened",
        -- so the boundary question is answered by the same pair of files either way
        -- -- and the pre-lever baseline, which is the thing the scans kept running
        -- for, survives to be compared against.
        -- drainHeld FIRST, so the count the marker reports is the count the file
        -- actually gets.  The other way round the still-held rings would land after
        -- the marker and the arithmetic in the line would be short by however many
        -- keys were still moving when the run ended -- which is exactly the tail of
        -- a start-up, the part most worth counting.
        drainHeld()
        if windowState == 'waiting' then
            windowMark('NO WINDOW', string.format(
                'nothing opened the window -- the %d line(s) before this are the whole run, not a window',
                #logLines + #audioLines))
            windowClosedAt = now() - startedAt
            windowClosedWhy = 'the window never opened; the timeline is the whole run'
            -- Set to 'closed' rather than left 'waiting': the final flush below gates
            -- on exactly that state, and the run IS over.  Not closeWindow(), which
            -- requires 'open' and would correctly refuse this.
            windowState = 'closed'
            windowDirty = true
            healthDirty = true
        end
        flush(true)
    end)
    return true
end

-- The re-inject guard.  Solara has no unload, and a second injection would
-- otherwise leave two watchers scanning the same instances and writing two
-- overlapping timelines into the same prefix -- which reads as one run with every
-- move duplicated, and is far harder to notice than a restart.
if _G.TRG_ORIGINAL_WATCH then
    -- Silent on purpose.  This whole tail used to print four lines, and all four
    -- said something the directory already says once it has been written: hello.txt
    -- carries the prefix, the sink and the hotkeys, error.txt carries a start-up
    -- death, and "a previous watcher was stopped" is a fact about a script the
    -- operator deliberately re-injected.  The one thing worth keeping is the ORDER
    -- -- a re-injection must stop the old watcher BEFORE the new one starts, or two
    -- watchers scan the same instances and interleave into one prefix -- and that
    -- order is the statements below, not a line about them.
    pcall(function() _G.TRG_ORIGINAL_WATCH.Stop() end)
end
_G.TRG_ORIGINAL_WATCH = Watch

-- The return value is deliberately discarded.  `not okStart` used to warn, but the
-- only way Start fails is `already running` -- which the Stop above has just made
-- impossible -- and a start-up that dies in the census now writes error.txt from
-- inside the spawn.  Assigning it to a local nobody reads would be the same dead
-- code with a friendlier spelling, so it is not assigned at all.
Watch.Start()
