--!strict
-- Numeric provenance is explicit because this place has no original server source.
-- TRGWeb supplies the simulation tick and heat/pressure equations. Authored
-- AIRemake manual text wins over the older telemetry logger for vent strength.
local Config = {
    Version = '0.2.0',
    Sim = {ReferenceTick=2.5, Step=1, MaxCatchupSteps=10, Ambient=20,
        StartupTemperature=9420, StartupPressure=5000, CBLHeat=65, PumpCooling=120,
        FanPressure=70, PressureDivisor=50, NoiseMin=-50, NoiseMax=49,
        State1=6000, State2=17500, State3=29500, State3Heat=700,
        State2Pressure=200, State3Pressure=300, StallPressure=2250,
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
        HDEFMaxIntegrity=12, HDEFHeatGain=1, HDEFHeatLoss=2,
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
    Visual = {LeverArcDegrees=50, PulseSeconds=0.6, RefreshSeconds=0.2,
        Ready=Color3.fromRGB(235,235,235), Off=Color3.fromRGB(45,45,45),
        Pulse=Color3.fromRGB(90,255,120), Fault=Color3.fromRGB(255,70,40)},
}
return Config
