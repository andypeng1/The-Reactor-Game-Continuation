--!strict
-- Pure server state machine. Every state mutation, including control requests,
-- enters here; monitors and ValueObjects are output adapters, never state owners.
-- Tests inject a deterministic random source instead of modifying live gameplay.
local Engine = {}
Engine.__index = Engine

local function integer(value, lo, hi)
    return type(value) == 'number' and value == value and value % 1 == 0 and value >= lo and value <= hi
end
local function array(count, build)
    local values = {}
    for index = 1, count do values[index] = build(index) end
    return values
end

function Engine.new(config, random)
    local self = setmetatable({config=config, random=random or math.random, sequence=0, events={}}, Engine)
    self:Reset(1)
    return self
end

function Engine:Log(kind, message)
    self.sequence += 1
    table.insert(self.events, {id=self.sequence, time=self.state.time, kind=kind, message=message})
    if #self.events > 100 then table.remove(self.events, 1) end
end

function Engine:Reset(shift)
    assert(integer(shift, 1, #self.config.Shift.Quotas), 'Invalid shift')
    local c = self.config
    -- Replace the entire state, forcing every service to fetch the current reference.
    self.state = {
        time=0, phase='Cold', phaseTime=0, shift=shift, elapsed=0,
        -- The start-up chain's cursor. It lives in state rather than on the engine
        -- so Engine:Reset clears it with everything else: a shift reset midway
        -- through a start-up must not resume the old chain at the step it had
        -- reached, and Reset replaces this whole table for exactly that reason.
        startupStep=0, startupHold=0,
        energy=0, quota=c.Shift.Quotas[shift], accumulator=0, failure=nil,
        -- lights was true. It is false because the cold state is authored dark in
        -- two independent places and lit in none: the place saves
        -- Workspace.RoomLights.ControlRoomLights with all 20 lamps at (17,17,17)
        -- and all 8 SurfaceLights off while every sibling light cell is lit, and
        -- the shipped recording's first action after entering the control room is
        -- CLICK RoomLight (EVT2060) followed by LAMPPAL g=0,0,0. A true here made
        -- that first click turn the room OFF. No gate, cost or formula moves --
        -- this is the initial value of a presentation switch, and RoomShell is
        -- what gives it a consequence.
        monitorPower=false, booted=false, shuttersOpen=false, lights=false, mute=false, sam=false,
        temperature=c.Sim.Ambient, pressure=c.Sim.Ambient, output=0, netOutput=0,
        fluctuation=0, radiation=0, coreState=0, extraction=2, peaStress=0,
        fans=array(6, function() return true end),
        cbl=array(3, function() return {level=2, pressure=0, stress=0, active=false, purgeUntil=0, fault=false} end),
        pumps=array(3, function() return {level=1, enabled=false, integrity=100} end),
        emergencyUsed={false,false,false}, ventUntil=0,
        mass=array(2, function() return {enabled=false, level=1} end),
        hdef={enabled=false, integrity=c.Device.HDEFMaxIntegrity, heat=0, fault=false},
        grav={phase='Idle', charge=0, damage=0, wakes=0}, equinox=false,
    }
    self:Log('INFO', 'Shift ' .. shift .. ' ready for control room boot')
end

-- Walks Config.Shift.StartupSteps, which is a list of holds rather than a
-- timeline. The cursor advances as far as the accumulated hold allows and every
-- step crossed is logged, so a late frame emits the whole backlog in order
-- instead of jumping to the newest: the log panel is the only progress the
-- player gets during a start-up, and a dropped line reads as a machine that did
-- something unexplained.
function Engine:AdvanceStartup()
    local s, c = self.state, self.config
    local steps = c.Shift.StartupSteps
    while s.startupStep < #steps do
        local step = steps[s.startupStep + 1]
        if step.hold > s.startupHold then break end
        s.startupHold -= step.hold
        s.startupStep += 1
        self:Log(step.kind, step.text)
    end
    if s.startupStep < #steps then return end
    -- Running is entered by FINISHING THE CHAIN, not by a clock of its own. The
    -- code this replaces compared phaseTime against a single StartupSeconds
    -- constant, which is the exact shape of bug this change exists to remove: a
    -- duration chosen at the keyboard rather than measured off the machine. The
    -- CBLs and the start-up temperature land on that same step as the last
    -- message for the same reason -- the log panel finishing and the reactor
    -- coming up are one event, not two that happen to be close together.
    s.temperature = c.Sim.StartupTemperature
    s.pressure = c.Sim.StartupPressure
    s.phase = 'Running'
    s.phaseTime = 0
    for _, device in ipairs(s.cbl) do device.active = not device.fault end
end

function Engine:Fail(reason)
    local s=self.state
    if s.phase == 'Failed' or s.phase == 'Report' then return end
    s.phase='Failed'; s.failure=reason; s.output=0; s.sam=false
    for _, device in ipairs(s.cbl) do device.active=false end
    self:Log('ERROR', reason)
end

function Engine:Command(action, index, value)
    local s, c = self.state, self.config
    -- Index and value validation happens before any mutation, even for internal callers.
    local limits = {fan=6,cbl=3,cbl_purge=3,pump_on=3,pump_off=3,pump_level=3,
        emergency_vent=3,mass_toggle=2,mass_level=2,repair_pump=3,repair_cbl=3}
    if limits[action] and not integer(index,1,limits[action]) then return false,'Invalid device index' end
    if action=='cbl' and not integer(value,1,5) then return false,'Invalid CBL level' end
    if action=='pump_level' and not integer(value,1,3) then return false,'Invalid coolant level' end
    if action=='extraction' and not integer(value,1,4) then return false,'Invalid extraction level' end
    if action=='next' then
        if s.phase~='Report' or s.shift>=#c.Shift.Quotas then return false,'No next shift available' end
        self:Reset(s.shift+1); return true
    elseif action=='reset' then
        if s.phase~='Report' and s.phase~='Failed' then return false,'Cannot reset an active shift' end
        self:Reset(s.shift); return true
    end
    if s.phase=='Failed' or s.phase=='Report' then return false,'Shift ended' end
    if action=='monitor_power' then
        s.monitorPower=not s.monitorPower
        if not s.monitorPower then
            s.booted=false
            if s.phase=='Booting' or s.phase=='Ready' then s.phase='Cold'; s.phaseTime=0 end
        end
    elseif action=='shutters' then s.shuttersOpen=not s.shuttersOpen
    elseif action=='lights' then s.lights=not s.lights
    elseif action=='mute' then s.mute=not s.mute
    elseif action=='boot' then
        if not s.monitorPower or not s.shuttersOpen then return false,'Power monitors and open shutters first' end
        if s.phase~='Cold' and s.phase~='Ready' then return false,'Boot already running or reactor active' end
        s.phase='Booting'; s.phaseTime=0
    elseif action=='start' then
        if s.phase~='Ready' or not s.booted or not s.monitorPower or not s.shuttersOpen then return false,'Complete control room boot first' end
        s.phase='Starting'; s.phaseTime=0; s.startupStep=0; s.startupHold=0
        -- Emitted here rather than waiting for the next Step, so the three
        -- hold=0 messages go out on the tick the switch is thrown. A start-up
        -- whose first line arrives up to RefreshSeconds later reads as a switch
        -- that did nothing, which is precisely the complaint this is answering.
        self:AdvanceStartup()
    elseif action=='shutdown' then
        if s.phase~='Running' then return false,'Reactor is not running' end
        if s.energy<s.quota then return false,'Energy quota not yet met' end
        if s.temperature>=c.Shift.ShutdownLimit then return false,'Cool reactor below 17000 F first' end
        s.phase='Stopping'; s.phaseTime=0; s.sam=false
        for _, device in ipairs(s.cbl) do device.active=false end
    elseif action=='fan' then s.fans[index]=not s.fans[index]
    elseif action=='pump_on' then
        if s.pumps[index].integrity<=0 then return false,'Coolant pump requires repair' end
        s.pumps[index].enabled=true
    elseif action=='pump_off' then s.pumps[index].enabled=false
    elseif action=='pump_level' then s.pumps[index].level=value
    elseif action=='cbl' then
        if s.cbl[index].fault then return false,'CBL requires repair' end
        s.cbl[index].level=value
    elseif action=='cbl_purge' then
        local device=s.cbl[index]
        if s.time<device.purgeUntil then return false,'CBL purge cooling down' end
        device.pressure=0; device.stress=math.max(0,device.stress-c.Device.CBLPurgeStressRelief)
        device.purgeUntil=s.time+c.Device.CBLPurgeCooldown
    elseif action=='extraction' then s.extraction=value
    elseif action=='atmosphere_vent' then
        if s.phase~='Running' then return false,'Reactor is not running' end
        if s.equinox then return false,'Pressure control unavailable during Equinox' end
        if s.time<s.ventUntil then return false,'Atmosphere vent cooling down' end
        s.pressure=math.max(0,s.pressure-c.Vent.AtmosphereDrop); s.ventUntil=s.time+c.Vent.Cooldown
    elseif action=='emergency_vent' then
        if s.phase~='Running' then return false,'Reactor is not running' end
        if s.emergencyUsed[index] then return false,'Emergency vent depleted for this shift' end
        s.emergencyUsed[index]=true
        local before=s.temperature
        s.temperature=math.max(c.Sim.Ambient,s.temperature-c.Vent.EmergencyDrop)
        s.fluctuation=s.temperature-before
    elseif action=='hdef' then
        if s.hdef.fault then return false,'HDEF requires repair' end
        s.hdef.enabled=not s.hdef.enabled
    elseif action=='mass_toggle' then s.mass[index].enabled=not s.mass[index].enabled
    elseif action=='mass_level' then s.mass[index].level=s.mass[index].level==1 and 2 or 1
    elseif action=='sam' then
        if s.phase~='Running' or s.radiation>c.Device.SAMRadiationLimit then return false,'SAM unavailable' end
        s.sam=not s.sam
    elseif action=='grav_charge' then
        if s.shift<3 or s.phase~='Running' then return false,'Gravatron overcharge requires shift 3 operation' end
        if s.grav.damage>=c.Grav.FailureDamage then return false,'Gravatron requires repair' end
        if s.grav.phase~='Idle' then return false,'Overcharge already in progress' end
        s.grav.phase='Charging'; s.grav.charge=0
    elseif action=='grav_fire' then
        if s.grav.phase~='Charging' and s.grav.phase~='Armed' then return false,'Gravatron not charging' end
        local success=s.grav.phase=='Armed'
        s.grav.damage=math.min(100,s.grav.damage+(success and c.Grav.SuccessDamage or c.Grav.MisfireDamage))
        if success then s.grav.wakes=0 end
        s.grav.phase='Idle'; s.grav.charge=0
        self:Log(success and 'INFO' or 'WARN',success and 'Gravatron overload succeeded' or 'Gravatron misfire')
    else return false,'Unknown control: '..tostring(action) end
    self:Log('CONTROL',action..(index and ' '..index or ''))
    return true
end

function Engine:Repair(kind,index,seconds)
    if type(seconds)~='number' or seconds~=seconds or seconds<=0 or seconds>1 then return false end
    local s=self.state
    local amount=self.config.Device.RepairPerSecond*seconds
    if kind=='pump' and integer(index,1,3) then s.pumps[index].integrity=math.min(100,s.pumps[index].integrity+amount)
    elseif kind=='cbl' and integer(index,1,3) then
        local d=s.cbl[index]; d.stress=math.max(0,d.stress-amount)
        if d.stress==0 then d.fault=false; d.active=s.phase=='Running' end
    elseif kind=='grav' then s.grav.damage=math.max(0,s.grav.damage-amount)
    elseif kind=='hdef' then
        s.hdef.heat=math.max(0,s.hdef.heat-amount)
        if s.hdef.heat==0 then s.hdef.fault=false end
    else return false end
    return true
end

function Engine:Step(dt)
    local s,c=self.state,self.config
    s.time+=dt; s.phaseTime+=dt
    if s.phase=='Booting' and s.phaseTime>=c.Shift.BootSeconds then
        s.booted=true; s.phase='Ready'; s.phaseTime=0; self:Log('INFO','Control room ready')
    elseif s.phase=='Starting' then
        s.startupHold+=dt
        self:AdvanceStartup()
    elseif s.phase=='Stopping' and s.phaseTime>=c.Shift.ShutdownSeconds then
        s.phase='Report'; s.phaseTime=0; s.output=0; self:Log('INFO','Quota achieved and reactor shut down safely')
    end
    local h=s.hdef
    if h.enabled and not h.fault then
        h.integrity=math.min(c.Device.HDEFMaxIntegrity,h.integrity+c.Device.HDEFRecovery*dt)
        if s.phase=='Running' then h.heat=math.min(100,h.heat+c.Device.HDEFHeatGain*dt) end
        if h.heat>=100 then h.fault=true; h.enabled=false; self:Log('WARN','HDEF generator overheated') end
    else h.heat=math.max(0,h.heat-c.Device.HDEFHeatLoss*dt) end
    if s.phase~='Running' then return end
    s.elapsed+=dt
    if not s.equinox and s.elapsed>=c.Events.EquinoxSeconds then s.equinox=true; self:Log('WARN','Equinox active until shutdown') end
    local grav=s.grav
    if grav.phase~='Idle' then
        grav.charge+=dt
        if grav.charge>c.Grav.ChargeSeconds+c.Grav.WindowSeconds then
            grav.damage=math.min(100,grav.damage+c.Grav.MisfireDamage); grav.phase='Idle'; grav.charge=0
            self:Log('WARN','Gravatron firing window missed')
        elseif grav.charge>=c.Grav.ChargeSeconds then grav.phase='Armed' end
    end
    if s.sam then
        if s.radiation>c.Device.SAMRadiationLimit then s.sam=false
        else
            local level=s.temperature>c.Device.SAMTargetHigh and 1 or (s.temperature<c.Device.SAMTargetLow and 3 or 2)
            for _, device in ipairs(s.cbl) do device.level=level end
            for _, pump in ipairs(s.pumps) do pump.enabled=pump.integrity>0; pump.level=1 end
            for i=1,6 do s.fans[i]=s.pressure>c.Sim.StartupPressure end
        end
    end
    local heat,cooling,fans=0,0,0
    local scale=dt/c.Sim.ReferenceTick
    for _, pump in ipairs(s.pumps) do
        if pump.enabled and pump.integrity>0 then
            cooling+=pump.level
            pump.integrity=math.max(0,pump.integrity-c.Device.PumpWearPerLevel*pump.level*dt*(s.equinox and c.Events.EquinoxWearMultiplier or 1))
            if pump.integrity==0 then pump.enabled=false; self:Log('WARN','Coolant pump failed') end
        end
    end
    for _, device in ipairs(s.cbl) do
        if device.active and not device.fault then
            local level=s.pressure<c.Sim.StallPressure and 1 or device.level
            heat+=level
            device.pressure=math.clamp(device.pressure+(level-1)*c.Device.CBLPressurePerLevel*dt,0,100)
            if device.pressure>=c.Device.CBLStressThreshold then device.stress=math.min(100,device.stress+c.Device.CBLStressGain*dt) end
            if device.stress>=100 then device.fault=true; device.active=false; self:Log('WARN','CBL overloaded') end
        end
    end
    for _, on in ipairs(s.fans) do if on then fans+=1 end end
    local before=s.temperature
    s.temperature+=(heat*c.Sim.CBLHeat-cooling*c.Sim.PumpCooling+self.random(c.Sim.NoiseMin,c.Sim.NoiseMax))*scale
    if not s.equinox then s.pressure+=(math.floor(s.temperature/c.Sim.PressureDivisor)-fans*c.Sim.FanPressure)*scale end
    if s.temperature>c.Sim.State2 then s.pressure+=c.Sim.State2Pressure*scale end
    if s.temperature>c.Sim.State3 then s.temperature+=c.Sim.State3Heat*scale; s.pressure+=c.Sim.State3Pressure*scale end
    if s.pressure<c.Sim.StallPressure then s.temperature-=c.Sim.StallCooling*scale end
    if s.pressure>c.Sim.HighPressure then s.temperature+=math.floor(s.pressure/c.Sim.HighPressureDivisor)*scale end
    s.temperature=math.max(c.Sim.Ambient,s.temperature); s.pressure=math.max(0,s.pressure)
    s.fluctuation=s.temperature-before
    s.coreState=s.temperature>c.Sim.State3 and 3 or (s.temperature>c.Sim.State2 and 2 or (s.temperature>=c.Sim.State1 and 1 or 0))
    local n=s.coreState+1
    s.netOutput=math.floor(s.temperature/c.Sim.OutputDivisors[n])+c.Sim.OutputOffsets[n]
    local mass=0
    for _, device in ipairs(s.mass) do if device.enabled then mass+=device.level end end
    s.output=s.netOutput*s.extraction*c.Sim.ExtractionFraction*(1-mass*c.Device.MASSOutputCostPerLevel)*(s.equinox and c.Events.EquinoxMultiplier or 1)
    s.energy=math.min(s.quota,s.energy+s.output*dt/c.Sim.QuotaDivisor)
    s.peaStress=math.clamp(s.peaStress+(s.extraction*c.Sim.StressPerLevel+math.floor(s.output/c.Sim.StressOutputDivisor)-math.floor(cooling*c.Sim.StressPumpRelief)-c.Sim.StressPassiveRelief+(s.pressure>c.Sim.HighPressure and c.Sim.StressPressureBonus or 0))*scale,0,100)
    s.radiation=c.Device.RadiationPerState*(s.coreState+1)*math.max(0,1-mass*c.Device.MASSReductionPerLevel)
    h.integrity=math.max(0,h.integrity-c.Device.HDEFDecay*s.coreState*dt)
    if s.temperature>=c.Sim.MeltdownTemperature then self:Fail('Reactor meltdown')
    elseif s.temperature<c.Sim.StallTemperature then self:Fail('Reactor stallout')
    elseif s.peaStress>=100 then self:Fail('Power extraction assembly overload') end
end

function Engine:Update(dt)
    if type(dt)~='number' or dt~=dt or dt<0 or dt==math.huge then return end
    self.state.accumulator+=dt
    local steps=0
    while self.state.accumulator>=self.config.Sim.Step and steps<self.config.Sim.MaxCatchupSteps do
        self.state.accumulator-=self.config.Sim.Step
        self:Step(self.config.Sim.Step)
        steps+=1
    end
    -- Keep residual time instead of silently dropping lagged simulation time.
end
return Engine