--!strict
--[[
FacilityCascade -- the WORLD's half of the start-up chain.

Until this module the start-up was an administrative event. Sixteen messages
appeared in the log, the seven monitors swapped to their main face and the
three shutters retracted; nothing in the plant itself moved. In the original
game the same chain is accompanied by the whole facility coming alive -- the
chamber lamps ramp on in four waves, the CBLs charge and fire, the chamber
alarms flash and the core goes critical -- and that gap is what this module
closes.

WHAT IT OWNS
  Workspace.Lights.<group>                     the lamp parts and their Lights
  Workspace.ReactorCBLs.Reactor_Laser_Mk3_*    the CBL neon, rotors and vents
  Workspace.Core.*                             the core, its emitters, shocks
  Workspace.Alarms.ReactorChamber              the eight chamber alarms

WHAT IT DELIBERATELY DOES NOT OWN
  Workspace.RoomLights, Workspace.Monitors     RoomShell's, by the same rule
  Workspace.Core.CORE.Laser1..15               the fifteen laser rigs. They are
      beams rather than lamps and the recording never shows a start-up
      switching one. Driving them would be this module inventing a mechanic,
      which is the one thing it must not do.
  Workspace.Alarms.<the other four>            Facility / Coolant / Rad /
      ControlRoom. In the recording only the eight in ReactorChamber stop and
      flash; the others keep spinning throughout and their CFrame churn is
      ambient. (The recording does darken one part of Coolant -- one
      NeonPart.Color, at the same beat as the eight -- and that single write is
      left out on purpose: a different panel, with nothing to say whether it is
      a fault clearing or the alarm standing down.)
  Every property not named in Config.Cascade. Systems that react to the
  start-up react to it on their own; this module only restores the world's
  authored look.

HOW IT IS DRIVEN
  Config.Cascade.Sections is a list of WRITES -- one per (path, property,
  value, step) -- and this module does three things with them:

    Refresh(state, config)   on Runtime's one-second logic gate. It reads
                             state.startupStep, the index of the last message
                             the engine has logged, and replays every write
                             whose step has been reached. That replay is the
                             whole of the step-driven half, and it is a pure
                             function of one number, so a reset and a lagged
                             frame both land in the right state.
    Step(dt)                 on EVERY Heartbeat frame. The lamp ramps, the
                             tweens and the bursts' expiry. It is a public
                             function rather than work hidden inside a
                             connection because nothing that lives only inside
                             a Connect callback can be measured from outside
                             the VM that owns it (CLAUDE.md section 0.19); the
                             connection in Runtime is one line that calls it.
    the crossing             a write carrying Seconds or Delay is an EVENT
                             rather than a state: it is armed when its step is
                             crossed and then runs on its own clock.

  A target written by an event is OWED to that event until it finishes, so the
  step replay skips it. Without that, the alarm rotors -- latched to 0 on the
  dim beat and spun back up to 2.5 by the flash burst -- would be written to 0
  again by the next step change, a second into their flash.

WHY A LAMP IS NEVER DIMMED
  This facility is the operator's world and all of it is rendering, so the one
  irreversible mistake this module could make is to darken a lamp the art left
  lit -- and it would be indistinguishable from "the art is like that". The
  rule is therefore structural rather than a promise: a lamp that is ALREADY at
  its authored look, or whose Light is already switched on, is dropped at
  capture, so no write list can contain it. That is also why M.E.T.U's
  thirty-two lamps -- all lit before any start-up ever runs -- contribute
  nothing here. Config.Cascade.ColdBaseline is the single opt-in exception and
  it is off.

  A lamp this module DID light is put back exactly where it found it when the
  chain rewinds, colour, brightness and Enabled all three, because otherwise
  the second shift of a session would have no lamp waves at all.

WHERE THE NUMBERS COME FROM
  Every value in Config.Cascade is transcribed from what the original game does
  to its own world during its own start-up, read out of a recorded run of its
  property changes (Data/originalwatch/261002-140021/changes.log). The STEP
  numbers are this project's own: our chain is the same sixteen messages in the
  same order but runs 113.4 s where the original's ran about 66 s, so what the
  recording supplies is the ORDER -- which thing comes on before which -- and
  the exact values, never the seconds.
]]

local FacilityCascade = {}

local LIGHTS_ROOT = 'Lights'

-- ========== ADDRESSING ==========

local function resolve(path: string): Instance?
    local node: Instance? = workspace
    for segment in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(segment)
    end
    return node
end

local function walk(from: Instance, path: string): Instance?
    if path == '' then return from end
    local node: Instance? = from
    for segment in string.gmatch(path, '[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(segment)
    end
    return node
end

-- Split a dot path into (everything before the last segment, last segment).
-- The recording's own convention, kept here: the LAST segment is the PROPERTY
-- and the one before it may name several siblings at once. A single entry
-- NeonStuff.MidNeon.Part.Color therefore stands for twenty-four parts -- and
-- three lasers times twenty-four is the recording's own count of 72. Reading
-- only the first of them would light a third of one CBL and nothing anywhere
-- would say so.
local function splitLeaf(path: string): (string, string)
    local at: number? = nil
    -- Plain find, not a pattern: the escape for a literal dot is a backslash,
    -- and this file is delivered through an editing layer that decodes a
    -- backslash once on the way in (CLAUDE.md section 0.10). Plain find has no
    -- escape to decode and no way to be quietly rewritten.
    local index = string.find(path, '.', 1, true)
    while index do
        at = index
        index = string.find(path, '.', index + 1, true)
    end
    if at == nil then return '', path end
    return string.sub(path, 1, at - 1), string.sub(path, at + 1)
end

-- Every node a write addresses, relative to one unit: the instance path's own
-- leaf is expanded across all its same-named siblings. Returns them plus the
-- property name, which is the path's last segment.
local function targetsIn(unit: Instance, path: string): ({Instance}, string)
    local instancePath, prop = splitLeaf(path)
    local parentPath, leaf = splitLeaf(instancePath)
    local out: {Instance} = {}
    local parent = walk(unit, parentPath)
    if parent == nil then return out, prop end
    for _, child in ipairs(parent:GetChildren()) do
        if child.Name == leaf then out[#out+1] = child end
    end
    return out, prop
end

-- The single member access that is deliberately untyped. Every write below is
-- addressed by the NAME the recording used, and going through the name is what
-- makes a wrong property name loud: it throws here, in this module, instead of
-- quietly leaving a lamp dark for the rest of the shift.
local function write(instance, prop: string, value: any)
    (instance :: any)[prop] = value
end

-- ========== CAPTURE ==========
-- A "lamp" is a part in Workspace.Lights that either glows by material or owns
-- a Light. A part that owns a Light at Transparency 1 is its group's emitter --
-- invisible, with the SurfaceLight doing the actual lighting -- and it is
-- captured the same way rather than separated out, because the recording
-- drives both halves of that pair: it writes the part's Color AND its
-- SurfaceLight's Brightness.
local function isLamp(part: BasePart): boolean
    if part.Material == Enum.Material.Neon then return true end
    return part:FindFirstChildWhichIsA('Light') ~= nil
end

-- Which lamp sits at which point of its group's stagger. The recording shows
-- the original's lamps do NOT come on together -- inside one group its fading
-- lamps sit anywhere from 0.05 to 0.50 of their authored value in the same
-- scan -- but it does not show in what ORDER, and this module will not claim
-- one. Hashing the lamp's own position gives a fixed scatter that is identical
-- in every session, so a screenshot taken on Tuesday still explains the one
-- taken on Monday, without pretending to be the original's order.
local function staggerSeed(part: BasePart): number
    local p = part.Position
    -- Three co-prime multipliers rather than the usual xor-shift. The xor form
    -- was written first and does not parse here: this engine's Luau rejects the
    -- binary `~` outright (Expected identifier when parsing expression, got
    -- '~'), so a hash built out of it is a module that never loads at all. Sum
    -- and modulo are ordinary arithmetic and cannot go missing.
    --
    -- Floor to a quarter-stud first: positions are world coordinates out to
    -- hundreds of studs, and the multipliers keep the sum under 2^53, so the
    -- arithmetic below is EXACT in a double and this is a real hash rather than
    -- a slowly drifting one.
    local n = math.floor(p.X * 4) * 73856093
        + math.floor(p.Y * 4) * 19349663
        + math.floor(p.Z * 4) * 83492791
    return (n % 1000003) / 1000003
end

-- The authored colour of a lamp, in the priority order Config.Cascade
-- documents: its own Light, then its own colour, then the config table by name,
-- then the flat default. Every recorded on-colour is reachable through the
-- first two rules in this place; the table exists only for the groups that were
-- blacked out when the place was copied, where the Light speaks for them or
-- there is no Light at all.
local function authoredColour(part: BasePart, config): Color3
    local light = part:FindFirstChildWhichIsA('Light')
    if light and light:IsA('Light') then return light.Color end
    if part.Color.R + part.Color.G + part.Color.B > 0 then return part.Color end
    local named = config.Cascade.LampColors[part.Name]
    if named ~= nil then return named end
    return config.Cascade.DefaultLampColor
end

-- ========== STATE ==========

-- One recorded write. `seconds` makes it a burst, `delay` makes it a one-shot;
-- both of those are EVENTS, armed when their step is crossed. A write with
-- neither is a STATE and is replayed by every step change.
type Write = {
    step: number,
    value: any,
    seconds: number?,
    delay: number?,
    after: any?,
}

-- One property, everything written to it, and what the art had there before
-- this module ever ran. The authored value is read at Initialize rather than
-- restated in Config: it is the world's own number, and a copy of it in Config
-- would be a second source of truth for the same thing.
type Target = {
    instance: any,
    prop: string,
    authored: any,
    -- A burst that ended in a NEW steady state rather than a return to the
    -- art's (Config's `After`), or nil. It has to live outside `authored`
    -- because the two answer different questions: `held` is what this chain
    -- leaves behind, `authored` is what the NEXT chain starts from. The alarm
    -- rotors are the case that makes the difference visible -- they end at 0,
    -- but a second shift must find them spinning at 2.5 again.
    held: any?,
    writes: {Write},
    owned: boolean,
}

type Lamp = {
    part: BasePart,
    light: any,
    off: Color3,
    on: Color3,
    brightness: number,
    lit: boolean,
    delay: number,
    applied: number,
}

type Zone = {
    name: string,
    step: number,
    lamps: {Lamp},
    target: number,
    elapsed: number,
    done: boolean,
}

type Tween = {
    target: Target,
    step: number,
    to: any,
    seconds: number,
}
type Run = {target: Target, from: any, to: any, start: number, seconds: number}
type Timer = {due: number, run: () -> ()}

local zones: {Zone} = {}
local targets: {Target} = {}
local byInstance: {[any]: {[string]: Target}} = {}
local tweens: {Tween} = {}
local runs: {Run} = {}
local timers: {Timer} = {}
local clock = 0
local lastStep: number? = nil
local activeConfig: any = nil
local warnedStep = false

-- ========== WRITERS ==========

-- A time-domain write: the event owns this property until it is done with it.
local function take(target: Target, value: any)
    target.owned = true
    if (target.instance :: Instance).Parent ~= nil then
        write(target.instance, target.prop, value)
    end
end

-- The event is finished. Handing the property back is a separate act from
-- writing it, because the two together are what let a later step change find
-- the property unowned and replay it.
local function release(target: Target, value: any)
    target.owned = false
    if (target.instance :: Instance).Parent ~= nil then
        write(target.instance, target.prop, value)
    end
end

local function restore(target: Target)
    target.owned = false
    target.held = nil
    if (target.instance :: Instance).Parent ~= nil then
        write(target.instance, target.prop, target.authored)
    end
end

-- The value a property rests at if no step has written it: whatever a finished
-- burst left behind, else what the art had.
local function resting(target: Target): any
    if target.held ~= nil then return target.held end
    return target.authored
end

-- Armed, never fired here: only a write carrying `Seconds` or `Delay` comes
-- this way. A plain state write is the replay's business, and routing one
-- through here would TAKE the property -- so every later step change would skip
-- it for the rest of the session, and the property would freeze at the value of
-- whichever step happened to be crossed last. `arm` is therefore only ever
-- called for the two event kinds, and says so at the top rather than carrying
-- an else branch that is wrong wherever it is reached.
local function arm(target: Target, entry: Write)
    if entry.seconds ~= nil then
        take(target, entry.value)
        timers[#timers+1] = {due = clock + entry.seconds, run = function()
            -- If a later write took the property in the meantime, the burst's
            -- end must not undo it: the recording hands the alarm rotors from
            -- one writer to another and only the last one owns them.
            if target.owned then
                -- A burst that names what it ends ON has just defined a new
                -- resting value for this chain, and `resting` keeps it. Without
                -- that, the next step change -- step 15, twenty-seven seconds
                -- later -- would replay the art's value over it, which for the
                -- ignition sound means volume 1 on a sound that is not playing.
                if entry.after ~= nil then target.held = entry.after end
                release(target, resting(target))
            end
        end}
    else
        timers[#timers+1] = {due = clock + entry.delay, run = function()
            take(target, entry.value)
        end}
    end
end

local function lerpValue(from: any, to: any, k: number): any
    if typeof(from) == 'number' and typeof(to) == 'number' then
        return from + (to - from) * k
    end
    if typeof(from) == 'Vector3' and typeof(to) == 'Vector3' then
        return (from :: Vector3):Lerp(to :: Vector3, k)
    end
    if typeof(from) == 'Color3' and typeof(to) == 'Color3' then
        return (from :: Color3):Lerp(to :: Color3, k)
    end
    return if k >= 1 then to else from
end

local function applyLamp(lamp: Lamp, level: number)
    local part = lamp.part
    if part.Parent == nil then return end
    -- One scalar on BOTH halves, which is the mechanism the recording shows:
    -- its lamps move Color to 0.403922,0.403922,0.403922 while the same lamp's
    -- SurfaceLight moves Brightness 1.00 -> 0.05, i.e. the same factor.
    part.Color = lamp.off:Lerp(lamp.on, level)
    local light = lamp.light
    if light ~= nil and (light :: Instance).Parent ~= nil then
        light.Brightness = lamp.brightness * level
        light.Enabled = level > 0
    end
end

local function restoreLamp(lamp: Lamp)
    applyLamp(lamp, 0)
    -- Held in a local rather than re-cast at each use. `(x :: T).y = 1` is a
    -- statement that BEGINS with a parenthesis, and Lua reads a leading
    -- parenthesis after an expression as an argument list -- so two of them in
    -- a row is "Ambiguous syntax: use ';' to separate statements", a parse
    -- error pointing at perfectly ordinary code (§0.20's family: the compiler
    -- is answering a question about the line break, not about the logic).
    local light: any = lamp.light
    if light ~= nil and (light :: Instance).Parent ~= nil then
        -- Brightness by hand, not through applyLamp: that helper writes
        -- brightness * level, so ramping a captured lamp down to level 0 leaves
        -- a zero behind rather than the value the art had. A rewound lamp must
        -- come back exactly as it was found, or a second shift's wave starts
        -- from a lamp that has been quietly flattened.
        light.Brightness = lamp.brightness
        light.Enabled = lamp.lit
    end
    lamp.applied = -1
end

-- ========== INITIALIZE ==========

-- The chain's own timeline, folded out of the holds. `hold` is the dwell of a
-- step, so step N ends -- and its message is logged -- at the sum of holds 1..N.
-- That is the same walk Engine:AdvanceStartup does, and reading it here rather
-- than declaring a second copy is what keeps the two from drifting apart when
-- the chain is retimed.
local function stepTime(config, index: number): number
    local total = 0
    for i = 1, index do
        local step = config.Shift.StartupSteps[i]
        if step == nil then break end
        total += step.hold
    end
    return total
end

local function targetFor(instance: any, prop: string, problems: {string}, label: string): Target?
    local per = byInstance[instance]
    if per == nil then
        per = {}
        byInstance[instance] = per
    end
    local target = per[prop]
    if target ~= nil then return target end
    -- Read BEFORE anything is written, and it is the ART's value rather than a
    -- value from Config: it is what a rewind puts back. A property that cannot
    -- be READ is reported here rather than throwing: this is the one place the
    -- module can still say which path was wrong.
    local ok, authored = pcall(function() return (instance :: any)[prop] end)
    if not ok then
        problems[#problems+1] = label..': no property '..prop
        return nil
    end
    target = {instance = instance, prop = prop, authored = authored,
              held = nil, writes = {}, owned = false}
    per[prop] = target
    targets[#targets+1] = target
    return target
end

function FacilityCascade.Initialize(config)
    -- Emptied rather than appended to, so a re-run is a real re-resolve (the
    -- RoomShell rule): after an art change, calling Initialize again must
    -- rebuild the lists, not double them.
    zones = {}
    targets = {}
    byInstance = {}
    tweens = {}
    runs = {}
    timers = {}
    clock = 0
    lastStep = nil
    warnedStep = false
    activeConfig = config
    local problems: {string} = {}
    local cascade = config.Cascade

    -- ---------- the lamps ----------
    local root = resolve(LIGHTS_ROOT)
    if root == nil then
        problems[#problems+1] = 'missing '..LIGHTS_ROOT
    else
        -- The zone table is built by walking the CONFIG, then the world is
        -- matched into it, so that a group the world no longer has AND a group
        -- the config does not mention are both reported. Walking the world
        -- alone would silently leave an unnamed group dark for ever.
        local byName: {[string]: Zone} = {}
        for _, entry in ipairs(cascade.Zones) do
            local zone: Zone = {
                name = table.concat(entry.groups, '+'),
                step = entry.step,
                lamps = {},
                target = 0,
                elapsed = 0,
                done = false,
            }
            zones[#zones+1] = zone
            for _, name in ipairs(entry.groups) do byName[name] = zone end
        end
        local counted: {[string]: number} = {}
        local lit: {[string]: number} = {}
        local present: {[string]: boolean} = {}
        local unmatched = 0
        for _, group in ipairs(root:GetChildren()) do
            local zone = byName[group.Name]
            if zone == nil then
                unmatched += 1
                problems[#problems+1] = LIGHTS_ROOT..'.'..group.Name..' belongs to no beat'
            else
                present[group.Name] = true
                for _, descendant in ipairs(group:GetDescendants()) do
                    if descendant:IsA('BasePart') and isLamp(descendant) then
                        local light = descendant:FindFirstChildWhichIsA('Light')
                        local on = authoredColour(descendant, config)
                        -- Already at its authored look, or already emitting:
                        -- dropped here, so that no later code path can reach it.
                        -- Both halves matter. A lamp whose Light is on but whose
                        -- Color is black is M.E.T.U's whole wall, and it would
                        -- otherwise pass the colour test and then be ramped from
                        -- zero -- dimming a lamp that was already burning, which
                        -- is the exact mistake this rule exists to prevent.
                        local alreadyLit = light ~= nil and (light :: any).Enabled == true
                        if cascade.ColdBaseline == true or (not alreadyLit and descendant.Color ~= on) then
                            zone.lamps[#zone.lamps+1] = {
                                part = descendant,
                                light = light,
                                off = descendant.Color,
                                on = on,
                                brightness = if light ~= nil then (light :: any).Brightness else 0,
                                lit = if light ~= nil then (light :: any).Enabled else false,
                                delay = staggerSeed(descendant) * cascade.StaggerSeconds,
                                applied = -1,
                            }
                            counted[group.Name] = (counted[group.Name] or 0) + 1
                        else
                            lit[group.Name] = (lit[group.Name] or 0) + 1
                        end
                    end
                end
            end
        end
        for index, entry in ipairs(cascade.Zones) do
            for _, name in ipairs(entry.groups) do
                if counted[name] ~= nil then
                    print(string.format('[FacilityCascade] %-22s %4d lamp(s) on message %d',
                        name, counted[name], entry.step))
                elseif lit[name] ~= nil then
                    -- Said out loud rather than skipped quietly, because "this
                    -- group is already on" and "this group is missing" look
                    -- identical in the world and want opposite responses.
                    print(string.format('[FacilityCascade] %-22s %4d lamp(s) already on, left alone',
                        name, lit[name]))
                elseif present[name] then
                    -- Present and empty: a real group this place has nothing in.
                    -- Reported as a line rather than a problem, because that is
                    -- true of the world as it stands and warning about it every
                    -- boot would be a siren nobody can act on -- which is how a
                    -- genuine problem elsewhere stops being read (§0.13).
                    print(string.format('[FacilityCascade] %-22s %s', name,
                        'empty; nothing to bring on'))
                else
                    problems[#problems+1] = LIGHTS_ROOT..'.'..name..' is not in the world'
                end
            end
            local zone = zones[index]
            if cascade.ColdBaseline == true then
                -- The one mode where this module may write a lamp darker than
                -- the art made it. Done once, here, so the world is cold before
                -- the first beat rather than darkening in the middle of a fade.
                for _, lamp in ipairs(zone.lamps) do restoreLamp(lamp) end
            end
        end
        if unmatched > 0 then
            print(string.format('[FacilityCascade] %d %s group(s) belong to no beat and are left alone',
                unmatched, LIGHTS_ROOT))
        end
    end

    -- ---------- the writes ----------
    -- The one value that is derived rather than declared: the chain's own gap
    -- from the energise beat to the fire beat. Everything belonging to charging
    -- stops when the lasers fire, so expressing that as a number here would be
    -- a second copy of the chain's timeline that could only ever drift from it.
    local charge = stepTime(config, cascade.Beats.Fire) - stepTime(config, cascade.Beats.Energise)
    for _, section in ipairs(cascade.Sections) do
        local sectionRoot = resolve(section.Root)
        if sectionRoot == nil then
            problems[#problems+1] = 'missing '..section.Root
        else
            local units: {Instance} = {}
            if section.Units == '*' then
                for _, child in ipairs(sectionRoot:GetChildren()) do units[#units+1] = child end
            elseif section.Units ~= nil then
                for _, child in ipairs(sectionRoot:GetChildren()) do
                    if string.sub(child.Name, 1, #section.Units) == section.Units then
                        units[#units+1] = child
                    end
                end
            else
                units[1] = sectionRoot
            end
            if #units == 0 then
                problems[#problems+1] = section.Name..': nothing under '..section.Root
            end
            local writes = 0
            for _, unit in ipairs(units) do
                local label = section.Name..'/'..unit.Name
                for _, move in ipairs(section.Moves or {}) do
                    local instances, prop = targetsIn(unit, move.Path)
                    if #instances == 0 then
                        problems[#problems+1] = label..': missing '..move.Path
                    end
                    for _, instance in ipairs(instances) do
                        local target = targetFor(instance, prop, problems, label)
                        if target ~= nil then
                            local seconds = move.Seconds
                            if seconds == 'Charge' then seconds = charge end
                            target.writes[#target.writes+1] = {
                                step = move.Step, value = move.To,
                                seconds = seconds, delay = move.Delay, after = move.After,
                            }
                            writes += 1
                        end
                    end
                end
                for _, spec in ipairs(section.Tweens or {}) do
                    local instances, prop = targetsIn(unit, spec.Path)
                    if #instances == 0 then
                        problems[#problems+1] = label..': missing '..spec.Path
                    end
                    for _, instance in ipairs(instances) do
                        local target = targetFor(instance, prop, problems, label)
                        if target ~= nil then
                            local seconds = spec.Seconds
                            if seconds == 'Charge' then seconds = charge end
                            tweens[#tweens+1] = {target = target, step = spec.Step,
                                                 to = spec.To, seconds = seconds}
                            -- And the ramp's END as an ordinary state write at
                            -- the same step. A tween is a SHAPE, not a state: on
                            -- its own it leaves the property reverting to the
                            -- art's value as soon as the run is released, and
                            -- the firing sphere would snap back to its full
                            -- thirty studs an instant after collapsing into the
                            -- laser. The recording is explicit about this -- the
                            -- collapse ends at 0.001 and stays there -- so the
                            -- end value is declared as the state it is, and the
                            -- run only decides how it gets there.
                            target.writes[#target.writes+1] = {step = spec.Step, value = spec.To}
                            writes += 1
                        end
                    end
                end
            end
            print(string.format('[FacilityCascade] %-22s %4d unit(s) / %4d write(s)',
                section.Name, #units, writes))
        end
    end

    if #problems > 0 then
        -- Reported rather than skipped. A silent miss here would look exactly
        -- like art that is simply switched off, which is the one failure this
        -- module can produce that nobody would notice.
        warn('[FacilityCascade] incomplete capture: '..table.concat(problems, '; '))
    end
    local lampTotal = 0
    for _, zone in ipairs(zones) do lampTotal += #zone.lamps end
    -- and/or rather than an if-expression: `if ... then ... else ... end` as a
    -- bare function argument does not parse here (Expected ')' -- to close '('
    -- at the line above -- got 'end'), and the two are the same value.
    print(string.format('[FacilityCascade] ready: %d zone(s) / %d lamp(s) / %d propert%s',
        #zones, lampTotal, #targets, #targets == 1 and 'y' or 'ies'))
    return #zones, lampTotal, #targets
end

-- ========== REFRESH ==========
-- Signature-gated on the start-up index alone, for the same reason RoomShell is
-- gated: a quiet tick must not walk the whole facility to write values it
-- already holds. The index is also the ONLY input -- every write is a pure
-- function of it plus its own armed events -- which is what makes the mapping
-- in Config.Cascade checkable against the recording by reading one table.
--
-- WHICH PHASES THE INDEX MEANS ANYTHING IN. The chain runs during Starting and
-- its result stands through Running, Stopping and Report: the lights do not go
-- out because the shift ended, there is no recorded beat for that, and this
-- module will not invent one. Cold, Booting and Ready are before a chain ever
-- ran, and Failed is after one was cut short: in all four the index is stale --
-- it is whatever the last chain left behind, NOT zero -- so it is forced to 0
-- and the world is put back the way the art has it.
local function stepMatters(phase: string): boolean
    return phase == 'Starting' or phase == 'Running'
        or phase == 'Stopping' or phase == 'Report'
end

-- The step-driven half: put every property back to authored and then re-apply
-- the writes whose step has been reached. A replay rather than a diff, because
-- a rewind is always to the beginning (a new shift resets startupStep to 0) and
-- a replay lands in the right state whatever the jump was.
local function replay(step: number)
    for _, target in ipairs(targets) do
        if not target.owned then
            local value = resting(target)
            for _, entry in ipairs(target.writes) do
                if entry.seconds == nil and entry.delay == nil and entry.step <= step then
                    value = entry.value
                end
            end
            if (target.instance :: Instance).Parent ~= nil then
                write(target.instance, target.prop, value)
            end
        end
    end
end

-- The same walk with the DELAYED writes folded in, for a module that has booted
-- into a chain already in the past. A delayed write is a state that is simply
-- late, so it belongs in the result; a burst is not, and a burst that had
-- already finished must not be replayed or it would fire the core's explosion
-- over a reactor that has been critical for an hour. A BURST'S END IS already
-- safe by the same rule -- whatever it holds is in the table as a state write
-- at its own step, which is why the tween half of this function is a plain
-- state write at Initialize rather than a second loop here.
local function replaySteady(step: number)
    for _, target in ipairs(targets) do
        local value = resting(target)
        for _, entry in ipairs(target.writes) do
            if entry.seconds == nil and entry.step <= step then value = entry.value end
        end
        target.owned = false
        if (target.instance :: Instance).Parent ~= nil then
            write(target.instance, target.prop, value)
        end
    end
end

local function rewind()
    timers = {}
    runs = {}
    for _, target in ipairs(targets) do restore(target) end
    for _, zone in ipairs(zones) do
        zone.elapsed = 0
        zone.done = false
        -- And the WANT put back too. Restoring the lamps without clearing the
        -- zone's target leaves it still asking to ramp, so Step would light
        -- everything back up on the very next frame and the rewind would be
        -- invisible -- the world would look right for one frame and wrong for
        -- the rest of the session, which is the worst way for a bug to look.
        zone.target = 0
        for _, lamp in ipairs(zone.lamps) do
            -- A lamp this module lit goes back to exactly where it was found,
            -- all three properties. Skipped while the facility has never been
            -- touched, so a rewind that wrote nothing does not write anything.
            if lamp.applied ~= -1 then restoreLamp(lamp) end
        end
    end
    if activeConfig ~= nil and activeConfig.Cascade.ColdBaseline == true then
        for _, zone in ipairs(zones) do
            for _, lamp in ipairs(zone.lamps) do restoreLamp(lamp) end
        end
    end
end

-- The event half: anything whose step falls inside the step change is armed
-- now. Armed rather than fired, because a burst's length is on its own clock
-- and a lagged frame that crosses three steps must still run the last one's
-- burst for its full length.
local function armCrossed(previous: number, step: number)
    for _, target in ipairs(targets) do
        for _, entry in ipairs(target.writes) do
            if previous < entry.step and step >= entry.step then
                -- Only the two event kinds. A plain state write was replayed by
                -- the same Refresh that brought us here, and `arm` has no branch
                -- for it on purpose.
                if entry.seconds ~= nil or entry.delay ~= nil then arm(target, entry) end
            end
        end
    end
    for _, tween in ipairs(tweens) do
        if previous < tween.step and step >= tween.step then
            -- Ownership is claimed here, not on the first Step frame. The
            -- tween's END value is also a state write at its own step (see the
            -- Tweens loop in Initialize), so replay has just written the firing
            -- sphere's collapsed size in the same call that arms this ramp;
            -- without claiming on the spot the sphere would sit collapsed for a
            -- frame and then pop back open to begin collapsing again.
            tween.target.owned = true
            runs[#runs+1] = {target = tween.target, from = tween.target.authored,
                             to = tween.to, start = clock, seconds = tween.seconds}
        end
    end
end

function FacilityCascade.Refresh(state, config)
    local step = state.startupStep
    if type(step) ~= 'number' then step = 0 end
    if not stepMatters(tostring(state.phase)) then step = 0 end

    local previous = lastStep
    if previous == nil then
        lastStep = step
        for _, zone in ipairs(zones) do
            if step >= zone.step then zone.target = 1 end
        end
        -- First sight, and the two cases are not the same thing. step == 0 is a
        -- cold facility: put the world back where the art had it, which is a
        -- no-op in the ordinary boot and the whole of the repair after a
        -- failed shift. step > 0 is a server that booted into a running shift:
        -- every beat is already in the past and firing them would run the
        -- whole start-up chain, alarms and explosion included, over a reactor
        -- that is already critical.
        if step == 0 then rewind() else replaySteady(step) end
        return
    end

    lastStep = step
    if step < previous then rewind() end
    for _, zone in ipairs(zones) do
        if step >= zone.step then zone.target = 1 end
    end
    replay(step)
    armCrossed(previous, step)
end

-- ========== STEP ==========
-- Every frame, and ungated on purpose: the ramps, the tweens and the bursts'
-- expiry are the only part of this that is not a once-a-second logic tick, and
-- putting them behind Config.Visual.RefreshSeconds would turn a ramp into a
-- once-a-second stutter and stretch a 10.6 s burst into eleven seconds of dead
-- time.
local function stepInner(dt: number)
    local config = activeConfig
    clock += dt
    local levels = config.Cascade.FadeLevels
    local fade = config.Cascade.FadeSeconds

    for _, zone in ipairs(zones) do
        if zone.target > 0 and not zone.done then
            zone.elapsed += dt
            local settled = true
            for _, lamp in ipairs(zone.lamps) do
                local progress = (zone.elapsed - lamp.delay) / fade
                if progress > 1 then progress = 1 end
                -- Clamped at BOTH ends. A lamp whose stagger has not started yet
                -- has a negative progress, and left alone that reaches
                -- applyLamp as a negative level: the colour extrapolates past
                -- the art's with a negative Lerp, and the Light's Brightness is
                -- written as a negative number. Clamped, an unstarted lamp is
                -- simply still at zero, which is where it already is.
                if progress < 0 then progress = 0 end
                if progress < 1 then settled = false end
                local level = math.floor(progress * levels + 0.5) / levels
                if level ~= lamp.applied then
                    lamp.applied = level
                    applyLamp(lamp, level)
                end
            end
            -- A settled zone costs nothing for the rest of the session, and the
            -- levels are quantised for the same reason: unquantised, a group of
            -- several hundred lamps would be rewritten on every frame of its
            -- ramp.
            if settled then zone.done = true end
        end
    end

    -- Quantised for the same reason the lamps are, and it matters more here:
    -- an unquantised tween would write a MeshPart's Size on every frame for
    -- twelve seconds, which is a replicated property change and a physics
    -- invalidation six hundred times over.
    for index = #runs, 1, -1 do
        local run = runs[index]
        local progress = (clock - run.start) / run.seconds
        if progress >= 1 then
            release(run.target, run.to)
            table.remove(runs, index)
        else
            local level = math.floor(progress * levels) / levels
            local from = run.from
            local to = run.to
            local stepped = if typeof(from) == 'number' then from + (to - from) * level
                else lerpValue(from, to, level)
            take(run.target, stepped)
        end
    end

    -- Removed before it runs, so that a write inside one timer cannot be
    -- expired a second time by the loop that is already walking the list.
    for index = #timers, 1, -1 do
        if clock >= timers[index].due then
            local run = timers[index].run
            table.remove(timers, index)
            run()
        end
    end
end

function FacilityCascade.Step(dt: number)
    if activeConfig == nil then return end
    local ok, err = pcall(stepInner, dt)
    if not ok and not warnedStep then
        -- Warned once rather than every frame: a per-frame warn on a failing
        -- step is a console flood, and the flood is what hides the first
        -- message. The step is small and idempotent, so one lost frame is not
        -- worth losing the reason for.
        warnedStep = true
        warn('[FacilityCascade] step failed: '..tostring(err))
    end
end

return FacilityCascade
