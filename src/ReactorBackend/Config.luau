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
        FanPressure=70, PressureDivisor=50, NoiseMin=-50, NoiseMax=49,
        -- State1 and StallPressure were 6000 and 2250: TRGWeb's numbers, replaced
        -- 2026-09-26 with the shipped game's. State2/State3/Meltdown already matched.
        State1=5600, State2=17500, State3=29500, State3Heat=700,
        State2Pressure=200, State3Pressure=300, StallPressure=2200,
        StallCooling=750, HighPressure=13500, HighPressureDivisor=100,
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
}

-- The start-up chain's total, kept as one number for the phase trace.
local startupSeconds = 0
for _, step in ipairs(Config.Shift.StartupSteps) do startupSeconds += step.hold end
Config.Shift.StartupSeconds = startupSeconds

return Config