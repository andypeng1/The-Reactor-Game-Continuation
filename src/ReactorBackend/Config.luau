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
    Shift = {Quotas={512,1024,3072}, ShutdownLimit=17000,
        -- Durations below are reconstruction presentation defaults, not measured rules.
        BootSeconds=3, StartupSeconds=8, ShutdownSeconds=5},
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
    },
}
return Config