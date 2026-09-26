--!strict
-- Compatibility adapter: the new engine owns state while legacy monitors keep
-- receiving the ValueObjects they already expect. No simulation formula lives here.
local StateBridge = {}
local function set(folder: Instance, name: string, value: any)
    local node=folder:FindFirstChild(name)
    if node and node:IsA('ValueBase') then node.Value=value end
end
function StateBridge.Publish(state: any)
    local stats=workspace:FindFirstChild('Stats')
    if not stats then return end
    local core=stats:FindFirstChild('Core'); if not core then return end
    set(core,'TemperatureVal',math.floor(state.temperature))
    set(core,'PressureVal',math.floor(state.pressure))
    set(core,'OutputVal',math.floor(state.output))
    set(core,'RadiationVal',math.floor(state.radiation))
    set(core,'HDEFVal',math.floor(state.hdef.integrity))
    set(core,'BreachVal',state.hdef.integrity<=0)

    -- Stats.HDEF.IntegrityVal, and not Core.HDEFVal, is the field the shipped game
    -- actually carried the generator's integrity in: its telemetry records that one
    -- over 12..99 while Core.HDEFVal stays 0 across all 477 ticks. Nothing in this
    -- place reads either field, so this aligns the value without changing a display.
    local hdef=stats:FindFirstChild('HDEF')
    if hdef then set(hdef,'IntegrityVal',math.floor(state.hdef.integrity)) end

    set(core,'EnergyVal',math.floor(state.energy))

    set(core,'QuotaVal',math.floor(state.quota))

    set(core,'StressVal',math.floor(state.peaStress))
    set(stats,'GameActive',state.phase=='Running' or state.phase=='Starting' or state.phase=='Stopping')
    set(stats,'GameStart',state.phase=='Cold' or state.phase=='Ready')
    set(stats,'GameFail',state.phase=='Failed')
    set(stats,'NextShift',state.phase=='Report' and state.shift < 3)
    set(stats,'ResetShift',state.phase=='Report' or state.phase=='Failed')
    set(stats,'ChamberGravity',state.grav.wakes>0)
    set(stats,'GravatronActive',state.grav.damage<80)
    set(stats,'DecayFields',state.radiation>0)
    set(stats,'ActiveQPUs',6)
    local cbls=state.cbl
    for i=1,3 do
        local folder=stats:FindFirstChild('CBL'..i)
        if folder then
            set(folder,'Active',cbls[i].active)
            set(folder,'TempVal',math.floor(state.temperature))
        end
    end
    local fans=stats:FindFirstChild('Fans')
    if fans then for i=1,6 do set(fans,'Fan'..i,state.fans[i]) end end
end
return StateBridge