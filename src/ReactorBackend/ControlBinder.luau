--!strict
-- All physical console input is translated into validated Engine commands.
-- Labels are the stable authored contract; control geometry is never moved.
--
-- The two gates in Bind are the server half of a contract that already exists
-- elsewhere in this place: MouseHandler paints a hovered target "TOO FAR" past
-- 6 studs, and every console ClickDetector carries MaxActivationDistance = 6.
-- Both of those live on the client or in the engine's click filter, so neither
-- is a boundary the server can rely on. This file's copy is the only one that
-- actually rejects a forged request, which is why Config.Interaction is read
-- here rather than left as the unread placeholder it used to be.
local ControlBinder={}
local function split(s:string): {string}
    local out={}; for token in string.gmatch(s,'[^%s%-]+') do table.insert(out,token) end; return out
end
local function commandFrom(label:string): (string, number?, number?)
    local u=string.upper(label)
    local n=tonumber(string.match(u,'(%d+)'))
    if string.find(u,'C%-PUMP') then
        if string.find(u,'OFF') then return 'pump_off',n end
        if string.find(u,'ON') then return 'pump_on',n end
        return 'pump_level',n,tonumber(string.match(u,'LEVEL%s+(%d+)'))
    elseif string.find(u,'CBL') then
        if string.find(u,'PURGE') then return 'cbl_purge',n end
        return 'cbl',n,tonumber(string.match(u,'LEVEL%s+(%d+)'))
    elseif string.find(u,'COOLING FAN') then return 'fan',n
    elseif string.find(u,'PEA EXTRACTION') then return 'extraction',nil,tonumber(string.match(u,'LEVEL%s+(%d+)'))
    elseif string.find(u,'ATMOSPHERE VENT') then return 'atmosphere_vent'
    elseif string.find(u,'E%-VENT') then return 'emergency_vent',n
    elseif string.find(u,'HDEF') then return 'hdef'
    elseif string.find(u,'MASTER START') then return 'start'
    elseif string.find(u,'MASTER SHUTDOWN') then return 'shutdown'
    elseif string.find(u,'MONITOR BOOT') then return 'boot'
    elseif string.find(u,'MONITOR POWER') then return 'monitor_power'
    elseif string.find(u,'SHUTTERS') then return 'shutters'
    elseif string.find(u,'ROOM LIGHT') then return 'lights'
    elseif string.find(u,'ALARM MUTE') then return 'mute'
    elseif string.find(u,'SAMOS') then return 'sam'
    elseif string.find(u,'MASS') and string.find(u,'ACTIVATION') then return 'mass_toggle',n
    elseif string.find(u,'MASS') and string.find(u,'POWER') then return 'mass_level',n
    elseif string.find(u,'GRAVATRON OVERCHARGE') then return 'grav_charge'
    elseif string.find(u,'GRAVATRON OVERLOAD') then return 'grav_fire'
    end
    return '',nil,nil
end
-- Measured from the character root, not the camera: a player leaning back from a
-- console would otherwise gain reach for free, and the camera can be detached
-- from the body entirely by a client that wants to.
local function reach(player: Player, part: Instance): number
    local character=player.Character
    local root=character and character:FindFirstChild('HumanoidRootPart')
    if not root or not root:IsA('BasePart') then return math.huge end
    if not part:IsA('BasePart') then return math.huge end
    return (root.Position-part.Position).Magnitude
end
function ControlBinder.Bind(engine:any, publish:(any)->())
    local count=0
    local seen={}
    -- Gate counters exist so a refused click is never invisible, but they are
    -- reported on a timer rather than per event: a client can call
    -- FireClickDetector in a loop, and a warn per refusal would let it bury the
    -- real log under its own noise.
    local gates={range=0,rate=0,lastWarn=0}
    local function noteGate(reason,label)
        gates[reason]+=1
        local now=os.clock()
        if now-gates.lastWarn<5 then return end
        gates.lastWarn=now
        warn(string.format('[ReactorBackend][Gate] refused %d out-of-range and %d rate-limited clicks (last: %s %s)',
            gates.range,gates.rate,reason,label))
    end
    -- Weak keys so a player who leaves does not stay pinned by this table.
    local lastUse=setmetatable({},{__mode='k'})
    local maximumDistance=engine.config.Interaction.MaximumDistance
    local cooldown=engine.config.Interaction.Cooldown
    for _, detector in ipairs(workspace.Consoles:GetDescendants()) do
        if detector:IsA('ClickDetector') and not seen[detector] then
            seen[detector]=true
            local part=detector.Parent
            local labelValue=part:FindFirstChild('ClickPartText')
            local label=labelValue and labelValue:IsA('StringValue') and labelValue.Value or part.Name
            local action,index,value=commandFrom(label)
            if action~='' then
                count+=1
                detector.MouseClick:Connect(function(player)
                    -- Range first: a click from across the map is not a gameplay
                    -- mistake to be tolerated, it is a request the server refuses.
                    if reach(player,part)>maximumDistance then noteGate('range',label); return end
                    local now=os.clock()
                    if lastUse[player] and now-lastUse[player]<cooldown then noteGate('rate',label); return end
                    lastUse[player]=now
                    local ok,err=engine:Command(action,index,value)
                    if not ok then warn('[ReactorBackend][Control] '..label..' rejected: '..tostring(err)) end
                    publish(engine.state)
                    print(string.format('[ReactorBackend][Control] %s -> %s',player.Name,label))
                end)
            end
        end
    end
    print(string.format('[ReactorBackend][Control] bound %d labelled controls at range %s, cooldown %s',
        count,tostring(maximumDistance),tostring(cooldown)))
    return count
end
return ControlBinder