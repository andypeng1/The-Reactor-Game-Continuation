--!strict
-- Numeric provenance is explicit because this place has no original server source.
-- Adjudication order for every number here: the SHIPPED GAME outranks the videos,
-- and the videos outrank TRGWeb. TRGWeb is a legacy HTML prototype and is
-- demonstrably stale -- it starts state 1 at 6000 and stalls the core below
-- 2250 psi, whereas the shipped telemetry script says 5600 and 2200. Nothing
-- here may be changed on TRGWeb's authority alone.
-- Where the authored AIRemake manual text and the telemetry logger disagree, the
-- manual text wins. Where neither has a value, the number is TRGWeb-derived and
-- carries no independent support.
local Config = {
    Version = '0.2.0',
    Sim = {ReferenceTick=2.5, Step=1, MaxCatchupSteps=10, Ambient=20,
        StartupTemperature=9420, StartupPressure=5000, CBLHeat=65, PumpCooling=120,
        -- FanPressure is 60, not 70: the wiki's Pressure page states that each vent
        -- removes 60 PSI per core tick. It is unadjudicable from the captures -- both
        -- have the fans off -- so the wiki is the only witness here, and the manual is
        -- silent, which puts it a tier down rather than in doubt.
        NoiseMin=-50, NoiseMax=49, FanPressure=60,
        -- Chamber pressure is a per-state LINE, not a divisor. The operator's two
        -- captures in Data/analyze are the original's own ground truth, and a per-state
        -- fit of dP = g + s*Tprev returns 356/0.006502 and 788/0.005458 (live) and
        -- 358/0.006423 and 791/0.005365 (arch) for states 2 and 3, both at R2 = 0.998.
        -- Those two lines are therefore corroborated by measurement rather than
        -- inherited from the prototype. State 1's own fit is NOT identifiable -- R2 is
        -- 0.37 live and 0.007 arch, the band is only 4,400 F wide, and dP inside it is
        -- quantised to an integer ramp -- and the two captures disagree there (g 36 vs
        -- 203, s 0.0142 vs 0.0042), so state 1 keeps calculation.luau's value.
        --
        -- This is the one place the adjudication order in the header was never carried
        -- out: floor(T/50) is TRGWeb's, and on both captures the engine built on it is
        -- the WORST of the three models -- pooled median |residual| 114.0 / 153.0,
        -- against calculation.luau's 11.4 / 14.3 and TRGWeb's 46.0 / 64.0. That is also
        -- what proves these captures are not this remake's own output.
        --
        -- State2Pressure and State3Pressure are retired with it. The escalation is the
        -- discontinuity between adjacent entries in the table below, and leaving the
        -- bumps in place would apply the same jump twice.
        StatePressure={110,350,800},      -- g[state], PSI per tick
        StateSlope={0.01,0.0075,0.005},   -- s[state], PSI per tick per degree F
        PressureBenefitPEA={0,0,75,150},  -- d[s.extraction]; extraction is validated 1..4
        -- State1 and StallPressure were 6000 and 2250: TRGWeb's numbers, replaced
        -- 2026-09-26 with the shipped game's. State2/State3/Meltdown already matched.
        State1=5600, State2=17500, State3=29500, StallPressure=2200,
        StallCooling=750,
        -- Both temperature effects below are PER TICK, not one-shot. Every step past the
        -- threshold stays elevated in BOTH captures -- all nine steps past T>29499 are
        -- high in each, and none decays back -- so the quantity the captures pin down
        -- is the level shift between contiguous regimes, and that is what these are.
        --
        -- HighPressure was 13500, a number with no support anywhere. The bracket the
        -- captures give is Pprev in (11258, 11470] and 11300 sits inside it. Its
        -- divisor is retired: the shift is flat, not floor(P/100) -- scanning the
        -- threshold from 10200 to 14000 leaves the residual sitting on the noise floor.
        -- This constant is also the PEA stress-bonus threshold in Engine:Step; one
        -- threshold with one meaning, so both readings move together.
        HighPressure=11300, HighPressureHeat=298,
        -- State3Heat was 700. Measured +457.3 F per tick (live) and +461.7 (arch).
        State3Heat=460,
        StallTemperature=2000, MeltdownTemperature=39000,
        OutputDivisors={250,160,120,45}, OutputOffsets={50,100,250,400},
        ExtractionFraction=0.25, QuotaDivisor=60,
        StressPerLevel=4, StressOutputDivisor=500, StressPumpRelief=1.5,
        StressPassiveRelief=6, StressPressureBonus=2},
    -- ShutdownSeconds below is still an unmoved presentation default.
    -- BootSeconds no longer is; see its own note.
    Shift = {Quotas={512,1024,3072}, ShutdownLimit=17000,
        -- MEASURED 2026-10-01, and the first time this number has been measured
        -- at all. Source: the operator's own boot-screen capture,
        -- Data/auxcollection/startup/ScreenChanges.txt, whose provenance --
        -- which click its t=0 actually is -- is written down in
        -- _tools/_attic/scratch/aux_boot_hook.luau.
        --
        -- t=0 in that file is the MONITOR BOOT BUTTON's
        -- ClickDetector.MouseClick, i.e. exactly the transition this phase
        -- machine calls Cold -> Booting, so the window is bounded at both ends
        -- by the same event the engine uses and no player latency is inside it.
        -- BootFrame's last content lands at t=8; its successor face,
        -- PreStartupFrame, is written Visible at t=14 on all seven monitors.
        -- The boot is therefore 14 s.
        --
        -- It was 3, a number this file used to admit was presentation rather
        -- than measurement. Two earlier attempts to measure it disagreed -- a
        -- 10-01 flow run read 21.8 s from MONITOR BOOT to the master lever
        -- being accepted, a 09-26 run read at most 11 -- and both were
        -- measuring a different span: the master lever requires s.booted AND
        -- s.monitorPower AND s.shuttersOpen, so that interval carries the
        -- player's own walk to the lever. The capture removes the player from
        -- the measurement rather than trying to subtract them afterwards.
        BootSeconds=14, ShutdownSeconds=5,
        -- The start-up is a staged message chain, not a duration. Every capture in
        -- Data/flow/original_* emits these messages in this order; only the pace
        -- varies, so this is a list of HOLDS (seconds since the previous message),
        -- not a timeline -- an absolute-offset table would bake one run's head
        -- into every later step.
        --
        -- These holds ARE the per-message medians, differenced. For each message
        -- the offset from SEQUENCE INITIATED was taken in every run that carried
        -- it, the median of those offsets was formed, and the hold is the step from
        -- one median to the next. They sum to 113.4 s, and that is also the median
        -- of the four complete runs' own totals (91.4 / 151.7 / 112.6 / 114.3 to
        -- the last line; median 113.45) -- two estimators that were derived
        -- separately and agree, rather than one tuned to the other. Totals measured
        -- to START-UP COMPLETED alone are 86.3 / 107.8 / 111.1 / 146.5.
        --
        -- Both sets are over FOUR runs, not five. 260930-200834 stopped at
        -- COMBUSTION LASERS FIRING and never reached the end of the chain, and
        -- 260926-183529 was injected after a start-up had already run, so it has no
        -- chain at all. A first pass at this table carried holds that were NOT
        -- these medians (24 where the median step is 29.4, 16.5 where it is 27.2)
        -- under a comment claiming they were; reprocessing the captures found it.
        -- The numbers are reproducible from _tools/_attic/scratch/startup_chain.py,
        -- and PROGRESS.md Phase 65 carries the per-message table.
        --
        -- The timestamps those medians come from are POLL-QUANTISED. The recorder
        -- writes a poll only when something changed, so one quiet stretch in the
        -- 10-01 run went 19.3 s with no poll at all and the per-message spacing
        -- inside a group is not recoverable. These are good to a couple of
        -- seconds and are not presented as exact. Derivation, the per-run table
        -- and the deltas this was reduced from: PROGRESS.md Phase 65.
        --
        -- The captures carry two message variants (EXCESSIVE ENERGY FLUCTUATION /
        -- COMPUTATIONAL BENCHMARKS UNSATISFIED / TESSERACT MAINFRAME OVERCLOCK on
        -- one side, ELECTROMAGNETIC ANOMALIES DETECTED / ANOMALY PROCEDURE
        -- OVERRIDEN on the other, plus a COMPLETE MAINFRAME CRASH tail). Neither
        -- is modelled: the branch between them was never measured, and the crash
        -- tail describes permanent damage ("IN FUTURE ACTIVATIONS"), which is a
        -- mechanic -- CLAUDE.md 1.4 #1. Only the trunk every run shares is here.
        --
        -- The text carries the game's own <b>[ALERT]</b> / <b>[WARN]</b> markup
        -- because the panel that renders it is RichText: the markup was recorded
        -- as payload, not decoration. kind is separate metadata for anything that
        -- wants to colour or filter a line without parsing one.
        StartupSteps = {
            {hold=0,    kind='ALERT', text='<b>[ALERT]</b> - SUBSPACE REACTOR START-UP SEQUENCE INITIATED'},
            {hold=0,    kind='WARN',  text='<b>[WARN]</b> - ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY'},
            {hold=0,    kind='WARN',  text='<b>[WARN]</b> - ACTIVATING POWER EXTRACTION ASSEMBLY'},
            {hold=29.4, kind='INFO',  text='PRIMING ISOTOPE E COOLANT NETWORK'},
            {hold=4,    kind='INFO',  text='CALIBRATING REACTOR SENSOR NETWORK'},
            {hold=0,    kind='INFO',  text='E-VENT STRUCTURES PRIMED'},
            {hold=0,    kind='WARN',  text='<b>[WARN]</b> - SUBSPACE RIFT ACTIVE, RADIATION WARNING'},
            {hold=11.7, kind='INFO',  text='PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM'},
            {hold=1.5,  kind='WARN',  text='<b>[WARN]</b> - INITIATING DEEP SCAN PROCEDURE'},
            {hold=8.8,  kind='INFO',  text='DEEP SCAN PROCEDURE COMPLETED'},
            {hold=14.2, kind='ALERT', text='<b>[ALERT]</b> - PRIMING ALL COMBUSTION LASERS'},
            {hold=1.5,  kind='INFO',  text='M.E.T.U DIAGNOSTICS ACCEPTABLE'},
            {hold=11.1, kind='ALERT', text='<b>[ALERT]</b> - ALL SYSTEMS READY, CORE IGNITION IMMINENT'},
            {hold=0,    kind='ALERT', text='<b>[ALERT]</b> - COMBUSTION LASERS FIRING'},
            {hold=27.2, kind='ALERT', text='<b>[ALERT]</b> - START-UP COMPLETED'},
            -- Not an invention and not a variant: every capture that reached
            -- START-UP COMPLETED carries this one line a few seconds later --
            -- +5.1, +5.2, +4.8 and +3.2 s in the four runs that got this far -- and
            -- it lives in the game's own shipped telemetry log
            -- (ServerStorage.Data.DataCollection.Log), which is where the string
            -- was confirmed to be the game's rather than the panel's. An earlier
            -- pass ended the trunk at START-UP COMPLETED and dropped it, which is
            -- exactly the kind of omission a hand-copied table makes. It is a STEP,
            -- not a message sent after the chain: the original still counts itself
            -- not-yet-active for 8.65 s past START-UP COMPLETED, and this line
            -- arrives inside that window. PROGRESS.md Phase 65 has the deltas.
            {hold=4,    kind='INFO',  text='PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS'},
        },
        -- DERIVED, never declared -- overwritten with the sum of the holds below
        -- so the two can never drift apart. It survives the removal of the old
        -- hand-written constant only because MCP_FlowCollector's phase trace still
        -- prints it; Engine no longer reads it, because the chain ends the phase
        -- now, not a clock. The zero here is a placeholder that the loop replaces,
        -- so it is not a second source of truth for anything.
        StartupSeconds=0},
    Vent = {AtmosphereDrop=3000, Cooldown=26, EmergencyDrop=7000},
    Grav = {ChargeSeconds=6, WindowSeconds=1.5, FailureDamage=80,
        -- Damage amounts are explicit reconstruction defaults pending calibration.
        SuccessDamage=5, MisfireDamage=25},
    Device = {
        -- Missing original device rate curves cannot be recovered from empty scripts.
        -- These configurable defaults preserve described directions, not exact balance.
        PumpWearPerLevel=0.06, CBLPressurePerLevel=0.6, CBLStressThreshold=75,
        CBLStressGain=0.4, CBLPurgeStressRelief=25, CBLPurgeCooldown=4,
        -- HDEF integrity is a 0-100 scale, confirmed by the user on 2026-09-26. It
        -- was 12, which is where the shipped telemetry's own floor sits, so the
        -- ceiling had been read off the floor. Evidence: ServerStorage.Data.
        -- DataCollection.Log records HDEF.IntegrityVal over 477 ticks as 99 (319),
        -- 12 (154), and 93, 76, 57, 31 once each, a band inside a 0-100 range.
        -- Side effect worth knowing: HDEFDecay and HDEFRecovery are per-second
        -- rates, so against the correct maximum they now move ten times slower in
        -- absolute terms than they did against 12.
        HDEFMaxIntegrity=100, HDEFHeatGain=1, HDEFHeatLoss=2,
        HDEFRecovery=0.2, HDEFDecay=0.025, RadiationPerState=120,
        MASSReductionPerLevel=0.2, MASSOutputCostPerLevel=0.025,
        RepairPerSecond=10, RepairRange=20,
        SAMRadiationLimit=600, SAMTargetLow=7000, SAMTargetHigh=14000},
    Events = {EquinoxSeconds=720, EquinoxMultiplier=3, EquinoxWearMultiplier=2},
    -- MaximumDistance was 32, a placeholder nothing read. Two independent
    -- measurements in this place agree on 6: MouseHandler paints a hovered
    -- target "TOO FAR" beyond 6 studs, and every console ClickDetector carries
    -- MaxActivationDistance = 6. Both live outside the backend (client script /
    -- per-detector property), so neither is a boundary the server owns. This
    -- value is the backend's copy of the same 6, read by ControlBinder.
    Interaction = {Cooldown=0.15, MaximumDistance=6},
    -- The outer tick gate, read by Runtime. Despite the name it gates LOGIC as
    -- well as visuals: there is one loop, and this is its period. The user asked
    -- for a one-second main loop. Logic cadence does not actually change with this
    -- number, because Engine:Update accumulates dt and steps only in Sim.Step = 1
    -- chunks, so at 0.2 the engine was still stepping once per second and merely
    -- driving the lamps five times a second. Setting 1.0 aligns the two: one
    -- accumulate, one step, one visual refresh, no residual carried.
    -- Colours are either measured off the part that wears them or named by the
    -- in-game manual; none is chosen by taste. Manual item 17 states the CBL
    -- status code in words -- Overload = Red, Integrity Loss = Purple, Reaction
    -- Loss (low chamber pressure) = Blue, High CBL Output = Yellow -- which is
    -- why those colours exist as keys of their own instead of being folded into
    -- Fault, and why the order they are tested in is the manual's own order.
    Visual = {LeverArcDegrees=50, PulseSeconds=0.6, RefreshSeconds=1,
        -- How long a console lever takes to slide from one stop to the next,
        -- read by VisualFeedback. It deliberately sits below RefreshSeconds:
        -- the throw has to finish inside one logic tick, because the refresh is
        -- signature-gated and a stop that is still being animated when the next
        -- pose arrives is a stop the union never rests on. 0.3 s is short enough
        -- that a click reads as answered and long enough to see the lever move.
        LeverTweenSeconds=0.3,
        Ready=Color3.fromRGB(235,235,235), Off=Color3.fromRGB(45,45,45),
        Pulse=Color3.fromRGB(90,255,120), Fault=Color3.fromRGB(255,70,40),
        -- Measured: the authored colour of AtmosphereVentButton.NeonPart and of
        -- CBL1-3Systems.PressureButton.NeonPart, both (137,255,147). It is the
        -- place's own "everything is fine" green, so it is reused wherever a
        -- lamp reports a healthy device rather than being picked again.
        Nominal=Color3.fromRGB(137,255,147),
        -- Measured: the amber accent inside ShuttersLever.OfflineLight,
        -- (255,128,1). Used for a device that is present but not in service.
        Amber=Color3.fromRGB(255,128,1),
        -- Measured: OverloadButton.NeonPart is authored (255,255,0), pure
        -- yellow, and manual item 89 says that button flashes yellow when the
        -- overcharge is ready to fire. The manual separately names Yellow as
        -- high CBL output, so one key serves both.
        Yellow=Color3.fromRGB(240,220,60),
        Purple=Color3.fromRGB(150,60,220),
        Blue=Color3.fromRGB(60,130,240)},
    -- The facility shell: what the Control Room Functions do to the ROOM, as
    -- opposed to what they do to a console. These are the only values the shell
    -- needs, and both pairs are measured off the place's own light art rather
    -- than picked here -- no script in the DataModel has ever named RoomLights,
    -- MonitorUI or PowerNeon, so the world side of the start-up chain was
    -- authored as art and left unwired.
    Shell = {
        -- Measured off the control room's own lit siblings: every cell in
        -- Workspace.RoomLights that is on -- SynthRoomLight and CRC1-3Lights --
        -- wears NeonPart at (248,248,248) with Transparency 0.25, next to a
        -- LightPart (Material Neon, Transparency 1, i.e. an invisible emitter)
        -- whose SurfaceLight is Enabled. ControlRoomLights is the one cell
        -- authored the other way: 20 NeonParts at (17,17,17) Transparency 0.50
        -- with all 8 SurfaceLights off. So these two pairs are the same art in
        -- its two authored positions. Brightness, Range and Face are
        -- deliberately absent: each cell keeps its own (ControlRoomLights
        -- authored 0.25/32, SynthRoomLight 0.25/30, Face Bottom), and
        -- overwriting them would be this module inventing light, not restoring
        -- it.
        RoomLightOn = {Color=Color3.fromRGB(248,248,248), Transparency=0.25},
        RoomLightOff = {Color=Color3.fromRGB(17,17,17), Transparency=0.50},
        -- Measured, and only ever checked, never written: all 64 emitter bodies
        -- across CRC1-3Lights, SynthRoomLight and RoomLights sit at exactly
        -- 1.000. A cell's emitter is an invisible housing for the SurfaceLight
        -- that actually lights the room, so its own colour and transparency are
        -- fixture design rather than lighting state -- which is why the lamps
        -- above are allowed to move and this is not. RoomShell reports a
        -- departure from it instead of restoring it.
        EmitterTransparency = 1,
        -- The shutter travel, in studs, DOWNWARD: the three control room window
        -- shutters retract by descending into the wall below the sill. Given by
        -- the operator on 2026-09-27, not guessed here -- and it is not a round
        -- number precisely because it is not a guess. 10.58 puts the top of the
        -- 10.650-tall Glass flush with the sill at 276.7, so it is the distance
        -- that actually stows the pane. An earlier pass recorded that this
        -- travel "cannot be measured" and declined to invent it; that was wrong
        -- in a way worth keeping in the record -- it looked for an opening
        -- ABOVE the glass, inside the glass's own frame, when the travel is
        -- INTO THE WALL BESIDE IT. The geometry was never missing; the search
        -- was pointed the wrong way.
        ShutterTravel = 10.58,
        -- How long the shutters take to travel that 10.58, read by RoomShell.
        -- Deliberately not the levers' 0.3: a shutter moves about 15 times the
        -- distance of a lever throw, so the same number would make the panel
        -- crawl. 0.6 s is 17.6 studs/s, which is what a powered door looks like
        -- -- and it is short enough that a double-toggle lands its second tween
        -- while the first is still on screen, which is why RoomShell cancels the
        -- live one before creating another instead of letting two share it.
        ShutterTweenSeconds = 0.6,
        -- Measured: all 7 Monitor.PowerNeon parts are authored (255,0,0).
        -- Restated here rather than captured at Initialize on purpose. A
        -- captured baseline is only correct on the first call: re-run
        -- Initialize after the monitors are already powered and it would
        -- capture the green as the "authored" red, permanently inverting the
        -- lamp. Restating it makes Initialize idempotent by construction, which
        -- is the same trap VisualFeedback's lever baselines were rebuilt to
        -- avoid. The ON colour is not restated -- it is Visual.Nominal above,
        -- the place's own healthy green, reused for the same reason it is
        -- reused everywhere else.
        MonitorPowerOff = Color3.fromRGB(255,0,0),
        -- The boot screen's reveal schedule, measured the same way and from the
        -- same capture as Shift.BootSeconds. Every entry below is a write the
        -- capture actually contains, at the second it contains it. BootFrame's
        -- ScrollingFrame holds 45 authored lines and they arrive 8 / 17 / 2 /
        -- 15 / 2 at a time over t=0..4; the LogFrame's six titles accumulate
        -- over t=1..5; the CompanyLogo is switched on at t=8.
        --
        -- Only VISIBILITY is modelled, and the limit is worth stating because
        -- it looks like an omission otherwise. The capture also carries
        -- Position, Size, Rotation and CanvasPosition churn on these same
        -- frames -- the diagnostic block grows, the log block grows, the logo
        -- spins in -- and none of that is reconstructible from it: the watcher
        -- writes a poll only when a value CHANGED, so what survives is about
        -- one sample per touched second. That is enough to say when something
        -- moved and not enough to say along which curve. The reveals below are
        -- booleans, and a boolean that flipped is the same fact however often
        -- it was sampled.
        --
        -- The same limit cuts the other way once, and it is recorded rather
        -- than smoothed over: the capture cannot distinguish a label authored
        -- hidden and then revealed from one authored visible and never touched.
        -- The remake's 45 are authored hidden, so this table drives them.
        -- Author them visible and this schedule silently becomes a schedule of
        -- hiding -- BootPanel measures that once at Initialize and says so,
        -- rather than letting it be a hole nobody can see.
        BootScreen = {
            -- at = WHOLE SECONDS after the boot began. A reveal is due AT its
            -- `at`, not after it, so the t=0 block is on screen in the same
            -- tick the boot switch is thrown rather than one tick later.
            --
            -- The two label blocks are addressed by each label's OWN number,
            -- never by sibling order: the ScrollingFrame's children are not in
            -- numeric order in the tree.
            Reveals = {
                {at=0, diagnostic={1, 8}},
                {at=1, diagnostic={9, 25}, log={1, 2}},
                {at=2, diagnostic={26, 27}, log={3, 3}},
                {at=3, diagnostic={28, 43}, log={4, 5}},
                {at=4, diagnostic={44, 45}},
                -- The odd entry, and the bytes are the only reason it is here:
                -- at t=5 every diagnostic line and the first five log titles
                -- are switched OFF, and TitleText6 -- the only one not yet
                -- shown -- is switched on. Nothing in the capture says why. It
                -- is kept as measured rather than smoothed into a shape that
                -- would read better and match worse.
                {at=5, clearDiagnostic=true, clearLog={1, 5}, log={6, 6}},
                {at=8, companyLogo=true},
            },
        },
    },
    -- ========== CASCADE (the start-up chain -> the world) ==========
    --
    -- The chain above is sixteen MESSAGES. This is what the same chain does to
    -- the plant, transcribed from a recorded run of the original game's own
    -- property changes (Data/originalwatch/261002-140021/changes.log): every
    -- value here was read out of that file, and the messages each write rides
    -- on were chosen to preserve the recording's ORDER.
    --
    -- The step numbers are OUR chain's, not the recording's. Ours is the same
    -- sixteen messages in the same order but runs 113.4 s where the original's
    -- ran about 66 s, so the recording supplies order and values and never
    -- seconds. Any duration that IS a measurement says so in its comment; the
    -- two that are not (the lamp fade and its stagger) say that too.
    --
    -- A path is read the way the recording writes it: the LAST segment is the
    -- property, and the segment before it may name several siblings at once.
    -- NeonStuff.MidNeon.Part.Color is one entry standing for twenty-four
    -- parts -- three lasers times twenty-four is the recording's own count of
    -- 72 -- and lighting only the first of them would leave two thirds of every
    -- CBL dark with nothing anywhere saying so.
    Cascade = {
        -- The four beats that need a TIME, not just an index. Everything else
        -- here is addressed by its step number directly.
        Beats = {
            Dim      = 2,   -- ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY
            Energise = 11,  -- PRIMING ALL COMBUSTION LASERS
            Fire     = 14,  -- COMBUSTION LASERS FIRING
            Ignite   = 16,  -- the step that finishes the chain; Engine turns Running here
        },

        -- The lamp waves, in the recording's order: clamp, then chamber, then
        -- the far rooms, then the control room. Groups this place already has
        -- at their authored look contribute no lamps and are reported as left
        -- alone rather than being turned off and back on.
        Zones = {
            {step = 4,  groups = {'ClampLights'}},
            {step = 8,  groups = {'ChamberLights', 'METULights', 'MaintFacilityLights'}},
            {step = 11, groups = {'LoungeLights', 'SubLoungeLights'}},
            {step = 14, groups = {'ControlRoomLowerLights'}},
        },
        -- NOT measurements. The recording polls the original's lamps and shows
        -- the fade is staggered, but one poll per touched second cannot
        -- describe a curve, so these three are what makes a wave read as a wave
        -- instead of a switch. The stagger is a hash of the lamp's own
        -- position, identical in every session, so two screenshots are
        -- comparable; it is not claimed to be the original's order.
        FadeSeconds = 1.6,
        StaggerSeconds = 0.9,
        FadeLevels = 24,
        ColdBaseline = false,
        -- The fallback chain for a lamp's ON colour is: its own Light, then its
        -- own Colour, then this table by part name, then DefaultLampColor.
        LampColors = {
            Neon = Color3.fromRGB(255, 255, 255),
            Light = Color3.fromRGB(255, 255, 255),
            LightPart = Color3.fromRGB(255, 255, 255),
        },
        DefaultLampColor = Color3.fromRGB(255, 255, 255),

        -- The non-lamp half. Each section names its ROOT, how to find its
        -- repeating UNITS inside that root ('*' is every child; anything else
        -- is a name prefix), and the moves that apply to each unit.
        --
        -- A move always names the PROPERTY as the last segment of its path and
        -- carries:
        --   To       the value to write.
        --   Step     the chain message it happens on.
        --   Delay    optional seconds after that message, instead of on it.
        --   Seconds  optional: the write is a BURST. A number is that many
        --            seconds; the string 'Charge' means the chain's own gap
        --            from the energise beat to the fire beat, so that
        --            everything belonging to charging stops when the lasers
        --            fire however the chain is later retimed.
        --   After    what a burst writes when it ends. Without it a burst
        --            reverts to what the art had, which is right for every
        --            burst here except the two that end in a new steady state.
        Sections = {
            -- The eight chamber alarms. The recording's very first act, before
            -- any lamp in the plant, is these STOPPING: AngularVelocity
            -- 2.5 -> 0 at t=65.4. The chamber is about to be evacuated and
            -- nothing in it should still be spinning. They flash back white for
            -- ten seconds when the lasers fire, and the rotors spin up again
            -- for exactly that long -- 0 -> 2.5 at t=87.73, back to 0 at
            -- t=98.63, which is 10.9 s.
            {
                Name = 'ChamberAlarms',
                Root = 'Alarms.ReactorChamber',
                Units = '*',
                Moves = {
                    {Path = 'MoterPart.HingeConstraint.AngularVelocity', To = 0, Step = 2},
                    {Path = 'MoterPart.HingeConstraint.AngularVelocity', To = 2.5,
                     Step = 14, Seconds = 10.9, After = 0},
                    {Path = 'SpinnyPart.Neon.Color', To = Color3.fromRGB(250, 250, 250),
                     Step = 14, Seconds = 10.9},
                    {Path = 'NeonLight.Color', To = Color3.fromRGB(250, 250, 250),
                     Step = 14, Seconds = 10.9},
                    {Path = 'NeonLight.IndustrialAlarmLight.Enabled', To = true,
                     Step = 14, Seconds = 10.9},
                    {Path = 'MainAlarmPart.IndustrialAlarmSound.Playing', To = true,
                     Step = 14, Seconds = 10.9},
                },
            },
            -- The three combustion lasers, per laser. Two beats: everything
            -- that CHARGES runs from the energise message to the fire message
            -- and stops there, and the beam itself comes on at the fire.
            --
            -- The recording's own charge is 21.3 s and splits 10.1 s of vent
            -- exhaust then 10.8 s of the firing sphere collapsing. Ours is the
            -- chain's own step 11 -> step 14 gap, so that split is not
            -- preservable and both halves run the whole window.
            {
                Name = 'CBL',
                Root = 'ReactorCBLs',
                Units = 'Reactor_Laser_Mk3_',
                Tweens = {
                    -- At rest this is a 30-stud transparent sphere; by the time
                    -- the lasers fire it is a point. The recording supplies both
                    -- ends (30 -> 0.001 and 1 -> 0 over t=89.04..99.86) and
                    -- nothing about the middle, so the path between them is
                    -- linear rather than fitted to polls that cannot describe
                    -- one.
                    {Path = 'Effects.FiringEffectPart.Size',
                     To = Vector3.new(0.001, 0.001, 0.001), Step = 11, Seconds = 'Charge'},
                    {Path = 'Effects.FiringEffectPart.Transparency',
                     To = 0, Step = 11, Seconds = 'Charge'},
                },
                Moves = {
                    -- the neon the recording lands on, per laser
                    {Path = 'NeonStuff.PillarNeon.Neon.Color',
                     To = Color3.fromRGB(100, 200, 255), Step = 11},
                    {Path = 'NeonStuff.GrateNeon.Grate.Color',
                     To = Color3.fromRGB(145, 245, 255), Step = 11},
                    {Path = 'NeonStuff.TankNeon.Part.Color',
                     To = Color3.fromRGB(255, 255, 255), Step = 11},
                    {Path = 'NeonStuff.MidNeon.Part.Color',
                     To = Color3.fromRGB(50, 255, 255), Step = 11},
                    {Path = 'NeonStuff.DetailNeon.Part.Color',
                     To = Color3.fromRGB(255, 255, 255), Step = 11},
                    {Path = 'NeonStuff.DetailNeon.Part2.Color',
                     To = Color3.fromRGB(255, 255, 255), Step = 11},
                    {Path = 'NeonStuff.DetailNeon.Part3.Color',
                     To = Color3.fromRGB(255, 255, 255), Step = 11},
                    -- the three rotors, 0 -> 1 and they stay there
                    {Path = 'Effects.SpinnyThingsFront.Moter.HingeConstraint.AngularVelocity',
                     To = 1, Step = 11},
                    {Path = 'Effects.SpinnyThingsBack.Moter.HingeConstraint.AngularVelocity',
                     To = 1, Step = 11},
                    {Path = 'Effects.SlightlyBetterSpinnyThing.Moter.HingeConstraint.AngularVelocity',
                     To = 1, Step = 11},
                    -- the hum is already PLAYING at pitch 0, i.e. silent; the
                    -- start-up raises its pitch rather than starting it.
                    {Path = 'Effects.SoundPart.AmbientHum.Pitch', To = 1, Step = 11},
                    -- charging: the twelve lightning emitters and the two in
                    -- Charge_Fire, on for the charge and off at the fire.
                    {Path = 'Effects.LightningParticles.Lightning.SmokeParticle.Enabled',
                     To = true, Step = 11, Seconds = 'Charge'},
                    {Path = 'Effects.LightningParticles.Lightning.TrailElectricityBlur.Enabled',
                     To = true, Step = 11, Seconds = 'Charge'},
                    {Path = 'Effects.LaserParticles.Charge_Fire.ParticleEmitter1.Enabled',
                     To = true, Step = 11, Seconds = 'Charge'},
                    {Path = 'Effects.LaserParticles.Charge_Fire.ParticleEmitter2.Enabled',
                     To = true, Step = 11, Seconds = 'Charge'},
                    {Path = 'Effects.VentParticalPart.ParticleEmitter.Enabled',
                     To = true, Step = 11, Seconds = 'Charge'},
                    {Path = 'Effects.SoundPart.LaserVentSFX.Playing',
                     To = true, Step = 11, Seconds = 'Charge'},
                    -- firing: the sustained beam emitter comes on where the
                    -- charge emitters stopped, and the beam itself becomes
                    -- visible -- Main fully, LaserPart left at 0.75 because
                    -- that is the value the recording leaves it holding.
                    {Path = 'Effects.LaserParticles.ParticleEmitter.Enabled',
                     To = true, Step = 14},
                    {Path = 'Effects.LaserParticles.Charge_Fire.DisplacedSmoke.Enabled',
                     To = true, Step = 14},
                    {Path = 'Laser.Main.Transparency', To = 0, Step = 14},
                    {Path = 'Laser.LaserPart.Transparency', To = 0.75, Step = 14},
                },
            },
            -- The core. Everything below happens on the LAST message of the
            -- chain, which is also where Engine sets phase = 'Running': the log
            -- panel finishing and the reactor coming up are one event here, as
            -- the engine's own comment says, so the ignition rides that step
            -- rather than a clock of its own.
            {
                Name = 'Core',
                Root = 'Core',
                Moves = {
                    -- The two CBL sounds live under Core in this rig rather than
                    -- under the lasers, so they are declared here and ride the
                    -- lasers' beats. The start-up sound runs for the charge
                    -- (t=76.72..86.92); the fire sound runs from there into the
                    -- core's settle, 21.4 s.
                    {Path = 'CORE.CBLStartUpSound.Playing', To = true,
                     Step = 11, Seconds = 'Charge'},
                    {Path = 'CORE.CBLFireSound.Playing', To = true, Step = 14, Seconds = 21.4},

                    -- latched at ignition
                    {Path = 'EFEParticlePart.AmbientParticles.Enabled', To = true, Step = 16},
                    {Path = 'CORE.Transparency', To = 0, Step = 16},
                    {Path = 'CORE.ProtoCoreLoop.Playing', To = true, Step = 16},
                    {Path = 'CORE.PointLight.Enabled', To = true, Step = 16},
                    {Path = 'ExplosiveCoreEffect.Size',
                     To = Vector3.new(120, 120, 120), Step = 16},
                    {Path = 'ForcefieldShockwave.Size',
                     To = Vector3.new(111.1917495727539, 111.1917495727539, 111.1917495727539),
                     Step = 16},
                    {Path = 'ForcefieldShockwave.Transparency',
                     To = 0.9259811043739319, Step = 16},

                    -- the bang: ten and a half seconds of emitters, then off
                    {Path = 'CORE.Effects.ExplosionParticle2.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.Effects.ExplosionParticle3.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.Effects.ExplosionParticle4.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.Effects.ExplosionParticle5.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.Effects.ExplosionParticle6.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.Effects.ExplosionSmoke.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.ExplosionLightning2.Enabled',
                     To = true, Step = 16, Seconds = 10.6},
                    {Path = 'CORE.IgnitonExplosion.Playing',
                     To = true, Step = 16, Seconds = 10.6},
                    -- The recording sets its volume to 0.475 before playing it
                    -- and to 0 when it stops, which is a second steady state
                    -- rather than a revert: at rest the sound sits at volume 1
                    -- without playing, so reverting would leave it armed loud.
                    {Path = 'CORE.IgnitonExplosion.Volume', To = 0.4751743674278259,
                     Step = 16, Seconds = 10.6, After = 0},
                    -- The one emitter that outlasts the bang by twice as long:
                    -- on at t=97.72, off at t=119.26, 21.5 s.
                    {Path = 'CORE.Effects.InstabilityParticle1.Enabled',
                     To = true, Step = 16, Seconds = 21.5},

                    -- the settle, 10.6 s after the ignition, which is where the
                    -- reactor stops moving and starts holding
                    {Path = 'CORE.Effects.CoreParticle.Enabled',
                     To = true, Step = 16, Delay = 10.6},
                    {Path = 'CORE.Effects.CoreParticle2.Enabled',
                     To = true, Step = 16, Delay = 10.6},
                    {Path = 'CORE.ProtoCoreLoop.Pitch', To = 0, Step = 16, Delay = 10.6},
                    {Path = 'ExplosiveCoreEffect.Size',
                     To = Vector3.new(80, 80, 80), Step = 16, Delay = 10.6},
                    {Path = 'ForcefieldShockwave.Size',
                     To = Vector3.new(120, 120, 120), Step = 16, Delay = 10.6},

                    -- and the long tail, another 11 s on: the running sound
                    {Path = 'CORE.Modified_Energy_Sound.Pitch', To = 2, Step = 16, Delay = 21.5},
                    {Path = 'CORE.Modified_Energy_Sound.Volume',
                     To = 1.25, Step = 16, Delay = 21.5},
                },
            },
        },
    },
    -- ========== ALERTS (the reactor-alerts monitor's 27 rows) ==========
    --
    -- Workspace.Monitors.AlertsControlRoomMonitor is a live 27-row indicator
    -- grid that no script in the place has ever written to: script_grep over
    -- the whole DataModel returns nothing for AlertsFrame, so the art was
    -- authored and left unwired -- the same shape of hole as the world half of
    -- the start-up chain (Shell above).
    --
    -- Each row is AlertFrameN: a grey 100x100 tile carrying a black label, and,
    -- at ZIndex 0 BEHIND that label, a full-size Frame whose BackgroundColor3 is
    -- the row's own category colour. Toggling THAT inner frame's Visible is the
    -- whole mechanism, and it is the only property the original's own recordings
    -- ever write here: every AlertFrameN write in Data/originalwatch is
    -- <path>.AlertFrameN.Frame.Visible. The colours are the art's, not ours --
    -- yellow for a running system, green for core active, orange for a moderate
    -- alert, red for a major one, purple for a malfunction -- so this module
    -- writes no colour at all.
    --
    -- Rows are numbered the way the art numbers them. `key` is resolved against
    -- an explicit table inside AlertsPanel, and a key with no entry there is
    -- REPORTED at Initialize and left dark, never quietly aliased onto a
    -- neighbour (CLAUDE.md 0.13: a missing owner looks exactly like a row the
    -- art meant to leave off).
    Alerts = {
        Rows = {
            -- `active` rows report on the start-up chain and the devices it
            -- brings up; they are the ones with something to say before
            -- ignition. Everything else is a condition on a RUNNING reactor and
            -- is forced dark until the chain finishes -- the Alerts grid only
            -- becomes visible when RoomShell shows MainMonitorFrame, which is
            -- Starting and Running, and a condition row lit during Starting
            -- would be reporting on a core that is still at ambient.
            {n=1,  key='rectActivation',      active=true},
            {n=2,  key='subspaceField',       active=true},
            {n=3,  key='cblActive',           active=true},
            {n=4,  key='coreActive',          active=true},
            {n=5,  key='pumpActive',          active=true},
            {n=6,  key='fanActive',           active=true},
            {n=7,  key='hdefActive',          active=true},
            {n=8,  key='gGateActive',         active=true},
            {n=9,  key='chamberRadiation',    active=true},
            {n=10, key='radiationBreach'},
            {n=11, key='powerInterruption'},
            {n=12, key='highEnergyOutput'},
            {n=13, key='excessiveTemperature'},
            {n=14, key='excessPeaStress'},
            {n=15, key='energyFluctuation'},
            {n=16, key='highTempFluctuation'},
            {n=17, key='eventsDepleted'},
            {n=18, key='hazardousRadiation'},
            {n=19, key='highPressure'},
            {n=20, key='highCblPower'},
            {n=21, key='highCblStress'},
            {n=22, key='peaMalfunction'},
            {n=23, key='pumpMalfunction'},
            {n=24, key='cblMalfunction'},
            {n=25, key='lowCoolant'},
            {n=26, key='coreDestabilization'},
            {n=27, key='stalloutPossibility'},
        },
        -- Thresholds. The four with a manual citation are the manual's own
        -- numbers, quoted from the pages under the DRMScreen below; the three
        -- marked ours are chosen because the manual is silent, and are said so
        -- rather than dressed up as measured.
        --
        -- The manual is Workspace.Consoles.ElectricGridConsole.DRMScreen.
        -- SurfaceGui.MainFrame, whose AlertsFrame.{General,Moderate,Major,
        -- Malfunctions}Frame pages give each row's prose.
        HighEnergyOutput = 400,        -- manual: output above 400 GW/H
        ExcessPeaStress = 75,          -- manual: P.E.A stress above 75%
        HighTempFluctuation = 400,     -- manual: above 400F fluctuation
        StalloutTemperature = 6000,    -- manual: core temp below ~6000F
        RadiationBreachIntegrity = 25, -- ours: 25 of the 0-100 HDEF scale
        HazardousCoreState = 3,        -- ours: radiation peaks in core state 3
        HighCblLevel = 4,              -- ours: the top two of the 1..5 ladder
        -- Filled in below the literal, from the one source each already has, so
        -- a threshold and its meaning can never drift into two numbers.
        ExcessiveTemperature = nil,
        HighPressure = nil,
        HighCblStress = nil,
    },
    -- ========== FORECAST (the subspace-forecast monitor) ==========
    --
    -- Workspace.Monitors.ForecastControlRoomMonitor carries the facility's
    -- subspace prediction: per its own manual page, EFE (Excessive Energy
    -- Fluctuation) events and Equinox. Like the Alerts grid it has never been
    -- written by any script -- script_grep returns nothing for TimeSliceTemplate
    -- -- so this is transcribed from the original's own capture rather than
    -- invented.
    --
    -- WHAT IS MODELLED, and what is not. The capture
    -- (Data/originalwatch/260930-200834, the only run that carries the sequence
    -- end to end) contains exactly the deep-scan announcement: the frame coming
    -- on, three sounds, a text that turns into a verdict, and the frame going
    -- off. It contains ZERO writes to TimeSliceTemplate, the ScrollingFrame,
    -- BoundryFrame or Intensity -- the timeline curve is simply not in the
    -- evidence, so it is not built. Inventing a curve would be the mistake
    -- DECISIONS 274/340 warns about: a plausible answer with no ground truth is
    -- a picked number, not a measured one.
    --
    -- The offsets and durations below ARE the capture's, in seconds from the
    -- announcement appearing.
    Forecast = {
        DeepScan = {
            -- The chain message this rides: Config.Shift.StartupSteps[9] is
            -- 'INITIATING DEEP SCAN PROCEDURE'. Anchoring on the message rather
            -- than on a clock is the same choice FacilityCascade makes, and it
            -- is what survives a retime of the chain.
            Step = 9,
            BeepAt = 3.35,
            VerdictAt = 5.04,
            PingOffAt = 9.37,
            EndAt = 12.89,
            TimelineOffAt = 14.63,
            Processing = 'PROCESSING DEEPSCAN TELEMETRY',
            -- Verdict phrasings, read off the captures. Both end in the facility
            -- clock at which the event is projected.
            Breach = 'HADEN THRESHOLD BREACH ~',
            Anomaly = 'ANOMALY DETECTED, MARGIN ~',
            -- The three colours are the capture's, all pure: idle green,
            -- breach red, anomaly yellow.
            IdleColor = Color3.new(0, 1, 0),
            BreachColor = Color3.new(1, 0, 0),
            AnomalyColor = Color3.new(1, 1, 0),
        },
        -- The all-monitors banner. The manual's own words are that when an EFE
        -- is about to occur, ALL monitors display a warning -- and the capture
        -- bears it out: EFEFrame.Visible goes true on all seven at once
        -- (261002-140021, t=373.82..373.89) and false together 10.25 s later.
        -- EFEFrame is the one face inside MonitorUI that RoomShell deliberately
        -- does not own, so this module is its only writer.
        BannerSeconds = 10.25,
        -- Ours, and said so. The deep scan has to decide between the two
        -- verdicts, and the only future subspace event this engine models is the
        -- Equinox (Engine:Step latches s.equinox at elapsed >= EquinoxSeconds).
        -- A margin inside this horizon is called a breach. It sits ABOVE
        -- EquinoxSeconds, so a normal run's deep scan genuinely forecasts the
        -- Equinox rather than always clearing -- but the comparison is real and
        -- a retuned EquinoxSeconds moves the verdict with it.
        BreachHorizonSeconds = 900,
        -- OURS, not measured: a SECONDS-TO-CLOCK map. The captures' verdicts name
        -- a wall clock (~3:00 AM, ~4:00 AM, ~12:00 AM) and the Quota monitor is
        -- authored at 11:52 PM, but nothing in the evidence fixes the rate. This
        -- is chosen so a full shift's Equinox lands near the 3 AM the verdicts
        -- name, and it is declared here for the same reason LampFadeSeconds is:
        -- a shape that has to be shown is better declared than faked.
        Clock = { StartHour = 23, MinutesPerSecond = 1 / 3 },
    },
}

-- The start-up chain's total, kept as one number for the phase trace.
local startupSeconds = 0
for _, step in ipairs(Config.Shift.StartupSteps) do startupSeconds += step.hold end
Config.Shift.StartupSeconds = startupSeconds

-- The alert rows' thresholds that already exist elsewhere in this file, wired to
-- their single source. Assigned here rather than written twice above, because a
-- threshold and its meaning drifting apart is exactly the failure the two-value
-- StartupSeconds above exists to prevent.
Config.Alerts.ExcessiveTemperature = Config.Shift.ShutdownLimit
Config.Alerts.HighPressure = Config.Sim.HighPressure
Config.Alerts.HighCblStress = Config.Device.CBLStressThreshold

-- ========== MONITOR READOUTS (Phase 130) ==========
-- Four of the seven monitors shipped carrying only the author's static art --
-- 'NIL F', '140 F', '100%', '0 GW/H', '11:50 PM', '524 GW', 'OFFLINE' -- and
-- nothing ever wrote them, because the drivers the original used
-- (GraphDetailThingy) are empty Scripts in this place. ReadoutPanel fills them
-- from engine state, and the SHAPE of every reading below is recovered from the
-- original rather than invented: Data/originalwatch/*/changes.log records each
-- label's observed value set verbatim ('5683 F', '-847 F', '1108 PSI',
-- '120 GW/H', '25 %', '360 R', '3.001 TW', '11:50 PM').
Config.Readouts = {
    -- THE SHIFT CLOCK, and this one is MEASURED. Data/flow/original_* carry the
    -- recorder's q.clock channel -- minutes since noon -- and across five
    -- independent recordings it starts at 710 every time (which is also the
    -- Quota screen's authored TimeLabel, 11:50 PM) and advances 0.977..0.990
    -- minutes per second of wall time in steady state (74 min in 76.01 s;
    -- 260927-111843 0.990; -123212 0.990; 261001-125206 0.988; 261002-140019
    -- 0.989; 261011-074137 0.977). So the rate is 1 and the origin is 710, and
    -- the channel closes its own loop: 710 reads 11:50 PM, 795 reads 1:15 AM,
    -- and both are in the corpus.
    --
    -- This is NOT Forecast.Clock above, and the two stay separate on purpose.
    -- That one is a FORECAST AXIS -- the deep scan's projection grid -- and it
    -- is fitted so the verdict lands on the 3:00 AM the captures name: since
    -- time + untilEquinox = EquinoxSeconds at every scan, 720 x 1/3 minutes past
    -- 23:00 IS 3:00 AM, which is what fixes it. This one is the facility's wall
    -- clock. Merging them would dress one fitted number up as a measured one.
    Clock = { StartMinute = 710, MinutesPerSecond = 1 },

    -- The label formats, one entry per reading family, all the capture's. They
    -- are '%.0f' rather than '%d' because the corpus contains a negative
    -- reading ('-847 F') and '%.0f' rounds it the way the capture shows it.
    Format = {
        Temperature = '%.0f F',
        Percent = '%.0f %%',
        Pressure = '%.0f PSI',
        Output = '%.0f GW/H',
        Radiation = '%.0f R',
    },

    -- The Quota target crosses into TW in the capture ('524 GW', then
    -- '3.001 TW'). Ours divides exactly where the original's rounded, so a
    -- 3072 GW quota reads '3.072 TW' here. Recorded divergence, not a
    -- reconciliation: the engine's quota is an integer number of GW and the
    -- label must not round it into a number the engine is not at.
    Target = { SIThreshold = 1000, SIDivisor = 1000, SIDecimals = 3 },

    -- The CBL state word ladder, verbatim from docs/ORIGINAL_UI_TEXT.md section
    -- 5, in the capture's own measured order: OFFLINE at t=1841, POWERING 3319,
    -- FIRING 3345, ACTIVE 3364, LOW OUTPUT 3508, and then the two failure logs.
    CblState = { Offline = 'OFFLINE', Powering = 'POWERING', Firing = 'FIRING',
        Active = 'ACTIVE', LowOutput = 'LOW OUTPUT' },
    -- POWERING and FIRING are ignition transients, and this engine's only
    -- ignition is the start-up chain, so both are anchored on its cursor rather
    -- than on a clock. That is the same choice FacilityCascade and
    -- ForecastPanel's DeepScan.Step make, and it is the one that survives a
    -- retime of the chain: StartupSteps[11] is 'PRIMING ALL COMBUSTION LASERS'
    -- and [14] is 'COMBUSTION LASERS FIRING'. startupStep counts COMPLETED
    -- steps, so it rests on 14 for the whole 27.2 s hold of message 15 -- which
    -- is why FIRING is a state a one-second refresh can actually sample.
    CblPrimingStep = 11,
    CblFiringStep = 14,

    -- Levels read as a percentage of their own range. Two declared divergences
    -- from the capture: it shows a CBL power of '10 %', which no integer level
    -- produces over this engine's 1..5 ladder (Engine:109), and an extraction of
    -- '0 %' where this engine's ladder starts at 1 (Engine:111). Neither is bent
    -- to match; the label reports the level the engine is actually at.
    LevelPercent = 25,
    ExtractionMax = 4,
    PumpLevelMax = 3,

    -- The three bar families. Each names the UDim2 COMPONENT it drives, not just
    -- an axis, and Full says what a fraction of 1 means in that component's own
    -- units. Read verbatim out of the capture's Size writes:
    --   CblGraph   {2,0},{0,N}    N integer 0..100   the title is CBL PRESSURE
    --   Reservoir  {1,0},{f,0}    f 0..1
    --   Energy     {f,0},{1,0}    f 0..1             the driven axis is X here
    -- Component matters because Roblox stores Offset as an INTEGER and truncates
    -- on assignment: the reservoir's own 0.441554189 can only ride Scale, and the
    -- CBL graph's 0..100 can only ride Offset. Reading "replace the Y" without
    -- asking which half of Y would have made the reservoir a bar that never moved
    -- -- which is exactly what the first pass did, and it is silent, because a
    -- truncated 0 and an unwritten 0 are the same number.
    --
    -- DisplayFull is declared rather than read because the authored Size is a
    -- FLOOR, not a range: the reservoir's authored 0.01 is its EMPTY state, so
    -- the authored value cannot tell you what full is.
    Bars = {
        CblGraph = { Component = 'YOffset', DisplayFull = 100 },
        Reservoir = { Component = 'YScale', DisplayFull = 1 },
        Energy = { Component = 'XScale', DisplayFull = 1 },
    },

    -- The Quota screen's equinox alarm: an exact colour inversion on
    -- EquinoxFrame, both values the capture's own (1,0,0 and 0,0,0).
    Equinox = {
        AlarmBackground = Color3.fromRGB(255, 0, 0),
        IdleBackground = Color3.fromRGB(0, 0, 0),
        AlarmText = Color3.fromRGB(0, 0, 0),
        IdleText = Color3.fromRGB(255, 0, 0),
    },

    -- The fan status words, the capture's.
    FanOn = 'ON',
    FanOff = 'OFF',
}

return Config