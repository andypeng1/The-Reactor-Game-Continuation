--!strict
-- Drives lever pose and lamp colour from engine state.
--
-- This module is the only writer of lever CFrames and lamp colours. Engine
-- never touches a part, so there is exactly one writer per lever -- the same
-- single-writer rule the rest of the backend follows.
--
-- ===== MOTION CONTRACT: a console lever SLIDES, it does not rotate =====
--
-- The throw below comes out of this place's own art, not out of the airlock
-- rigs, which are a different asset family (see the note at the end).
--
-- Two sources were measured. The first is the detent stacks the original builder
-- laid out on each console: a click target per level along the line the lever
-- slides, with the union sitting on the first one. Written here as the offset
-- from the union along its own +LookVector, which is the same measurement the
-- note above wrote as local -Z:
--
--     C-Pump   CoolantControl1-3  3 targets:  0.001   0.799   1.599
--                                  step 0.800, span 1.599   PUMP_MAX_LEVEL = 3
--     CBL      CBL1-3Systems      5 targets:  0.000   0.400   0.800
--                                              1.203   1.603
--                                  step 0.400, span 1.603   CBL_MAX_LEVEL = 5
--     Extract  ExtractionLever    4 targets:  0.026   0.549   1.099   1.674
--                                  span 1.674              EXTRACT_MAX_LEVEL = 4
--     Start    StartUpBigLever    2 targets:  0.023   1.663   span 1.686
--
-- The second is ReplicatedStorage.Levers, the builder's own template library,
-- which was found after the paragraph that used to stand here. It holds four
-- lever families parked at the world origin: 2Level, 3Level, 5Level and
-- SmallLever. 2Level ships as Up and Down copies whose click targets are named
-- Shut and Start, so the two-stop family's authored stop is Shut and the throw
-- runs along +LookVector, which is where StartUpBigLever's 1.686 comes from.
--
-- SmallLever is the one that mattered. The console detent stacks say nothing
-- about fans, shutters, MASS or E-VENT: those four controls carry no per-level
-- click target on the console at all, and the paragraph that used to stand here
-- read that silence as the art giving no travel to read. The template gives it.
-- SmallLever.Up holds its union at x 88.225 and SmallLever.Down at 88.925, a
-- throw of 0.700 studs, and its ClickPart sits at x 88.475 in both copies -- so
-- the click target is fixed to the console and only the union slides. Twelve
-- live levers wear that rig: six CFLever, three E_VENTLever, ShuttersLever and
-- the two MASS PowerLevers. They were being thrown 1.600, which is 2.29 times
-- the distance the art authors.
--
-- The target count equals that control's level count in all four console
-- families. The rule they encode is that level 1 is the authored position and
-- each stop above it advances one step along the union's own LookVector. That
-- rule is what makes the small family's direction readable as well as its
-- length, and it is why the small family is the one family whose throw is signed
-- rather than always positive: see smallThrow below, which records the four
-- readings that decide the sign.
--
-- The 11 airlock/gateway LeverModel rigs under MovingParts.DecayFields and the
-- three gateway rooms are NOT a source for console levers: measured, every one
-- of them is an AirlockConsole/GatewayConsole door bar, and not one is a console
-- lever. They do carry 0.500 studs plus 60 degrees, which is exactly where this
-- module's previous version took its 60 degrees from -- generalising a door bar
-- to 23 console levers the art says slide. That is the defect this replaces.
--
-- LeverOrginPart is not a pivot and is not used here, but the claim that used to
-- stand here -- that it sits at exactly LeverUnion's position in all 7 console
-- levers that have one -- is a measurement of seven levers that all happened to
-- be parked on their first stop. The template contradicts it: in 3Level.Level1
-- the marker reads 0.001 from the union, in Level2 0.800, and in Level3 1.600.
-- The marker is fixed to the console and the union slides away from it, so it is
-- the level 1 origin marker. Anything turning about it would still only spin the
-- handle in place, which is why it stays unused.

local VisualFeedback = {}

-- Used by poseLever, which is the one place a lever is written. See the note
-- there for why the throw is animated here on the server rather than handed to
-- the client tween relay this place already carries.
local TweenService = game:GetService("TweenService")

-- ========== MOTION ==========
-- Slide in studs per family, measured from the art. A lever at its top stop has
-- moved this far along its own axis. Nothing about a lever rotates.
--
-- This used to be one number, 1.6, because the four console families agree at
-- 1.6 to 1.7 studs. The small family does not: it is 0.700, and the twelve
-- levers that wear that rig are listed in the note above.
local TRAVEL = {
    small = 0.700,   -- ReplicatedStorage.Levers.SmallLever, union x 88.225 to 88.925
    start = 1.686,   -- StartUpBigLever, Shut -0.023 to Start 1.663
    pump = 1.599,    -- CoolantControl1-3, PW1 0.001 to PW3 1.599
    cbl = 1.603,     -- CBL1-3Systems, PW1 0.000 to PW5 1.603
    extract = 1.674, -- ExtractionLever, PW1 0.026 to PW4 1.674
    -- HDEF and Overcharge are the two controls that really do declare no detents:
    -- HDEFGenerator.PowerLever carries one ClickPart and OverchargeLever.BigLever
    -- none, so there is no span to read and the console family average stands in.
    generic = 1.6,
}

-- How long a throw takes and how it is eased. The duration is read from
-- Config.Visual.LeverTweenSeconds in Initialize, because it belongs with the two
-- other timing values the visual layer already owns -- PulseSeconds and
-- RefreshSeconds. The number below is only the fallback for a Config that does
-- not carry the key yet, and Initialize warns when it is the one in use.
--
-- The easing is not in Config. It is not a number anyone tunes, it is the shape
-- of a mechanism: Quad/Out decelerates into the stop, which is what a
-- hand-thrown detent lever does. Sine/InOut -- the easing the shared tween
-- library in ReplicatedStorage.Functions uses for everything -- starts slowly
-- and reads as a motor rather than a lever.
local DEFAULT_LEVER_TWEEN_SECONDS = 0.3
local LEVER_EASING_STYLE = Enum.EasingStyle.Quad
local LEVER_EASING_DIRECTION = Enum.EasingDirection.Out
local leverTweenInfo = TweenInfo.new(DEFAULT_LEVER_TWEEN_SECONDS, LEVER_EASING_STYLE, LEVER_EASING_DIRECTION)
local warnedTweenSeconds = false

-- The two stops of the SmallLever rig, as the offset from the lever's own
-- ClickPart along the lever's own axis. d, defined below, reads 0.250 with the
-- union parked on Up and -0.450 with it parked on Down, and those two numbers
-- come straight off the template pair: its ClickPart sits at x 88.475 in both
-- copies while the union moves. A live rig is authored on one of the two stops,
-- and which one decides the sign of its throw, because level 1 is the authored
-- position and level 2 is the other stop.
local SMALL_STOP_UP = 0.250
local SMALL_STOP_DOWN = -0.450

-- Two-position controls use the same rule with two stops.
local TOGGLE_MAX_LEVEL = 2

-- Level selectors divide one throw across their stops rather than each level
-- getting a full throw, so the top level is one full THROW_TRAVEL.
local PUMP_MAX_LEVEL = 3
local CBL_MAX_LEVEL = 5
local EXTRACT_MAX_LEVEL = 4
local MASS_MAX_LEVEL = 2

-- HDEF has three lamps across the full integrity range, so each lamp covers one
-- third of it. The segment count is named here but the step is derived from Config,
-- because the literal 4 that used to sit here was a quarter of the old and wrong
-- maximum of 12; left alone it would have lit all three lamps on an almost-empty
-- generator the moment the scale was corrected.
local HDEF_LAMP_SEGMENTS = 3

-- pumps[].integrity runs 100 down to 0 and there is no fault flag on a pump, so
-- this threshold is what stands in for one.
--
-- The user named the quantity on 2026-09-26: this is the pump's STABILITY, and
-- the readout for it is the NET STABILITY gauge on the calibration console. The
-- value stays 25 and the engine field stays `pump.integrity`; what changed here
-- is only that the number is now labelled. A threshold that stands in for a
-- missing fault flag and a threshold that means a named physical quantity are
-- the same integer and not the same claim, so the old note -- "a chosen number,
-- awaiting the user's figure" -- is discharged rather than reworded.
--
-- The console that displays it is built and completely unwired, which is the
-- reason this could sit unlabelled for so long: PECScreen.SurfaceGui.
-- ProcessorFrame.StabilityFrame carries a TextLabel reading NET STABILITY and a
-- Bar fill behind it, on all three of Workspace.CRC1-3.ProcessorInterior.
-- CalibrationConsole, and nothing in this project references StabilityFrame or
-- CalibrationConsole at all. TRGWeb declares coolant_pump1_Stability at 100 per
-- pump and only ever displays it, never writes it, so the number below is the
-- first figure this gauge could be wired to when it is wired.
local PUMP_FAULT_INTEGRITY = 25

-- Distance in studs to slide, along the lever's own LookVector, for a given
-- stop. Level 1 is the lever's authored position, and travel is signed, so a rig
-- authored on its far stop is carried back towards its near one instead of being
-- pushed further out of the range the art contains.
--
-- Level 0 is clamped onto the first stop instead of being given a stop of its
-- own: the art authors each union on its first click target and leaves no space
-- on the other side of it, so a stop below level 1 would float the handle off
-- the front of its console. What tells level 0 apart from level 1 is the lamp,
-- not the lever.
local function throwDistance(level: number, maxLevel: number, travel: number): number
    if maxLevel < 2 then return 0 end
    local clamped = math.clamp(level, 1, maxLevel)
    return (clamped - 1) / (maxLevel - 1) * travel
end

-- Signed throw for a SmallLever rig, in studs. Measured live, all twelve:
-- E_VENTLever1-3 read 0.250, MASS1-2.PowerLever 0.248, ShuttersLever -0.450 and
-- CFLever1-6 -0.408. The first five are authored on Up, the last seven on Down.
--
-- The arithmetic is the template's rather than a convention. The ClickPart is
-- fixed to the console and only the union slides, so moving the union by delta
-- moves d by -delta; going from the stop this rig sits on to the other stop is
-- therefore d minus that other stop's own offset. That is +0.700 for a rig on Up
-- and -0.700 for one on Down, and reading each rig's own d rather than writing
-- those two numbers down is what makes a rig parked slightly off its stop land
-- exactly on both: the CFLever read -0.408, 0.042 short of Down, so their throw
-- is -0.658 and they finish on Up instead of 0.042 past it.
local function smallThrow(part: BasePart): number
    local anchor: BasePart? = nil
    local holder = part.Parent
    if holder then
        local candidate = holder:FindFirstChild("ClickPart")
        if candidate and candidate:IsA("BasePart") then anchor = candidate end
    end
    if not anchor then return TRAVEL.small end
    local d = (anchor.Position - part.Position):Dot(part.CFrame.LookVector)
    if math.abs(d - SMALL_STOP_UP) <= math.abs(d - SMALL_STOP_DOWN) then
        return d - SMALL_STOP_DOWN
    end
    return d - SMALL_STOP_UP
end

-- ========== ADDRESSES ==========
-- Every path below was resolved in the live place. These are the authored
-- names, so they are read-only dependencies: never rename or delete them.
local A = {
    pumpLever = "Consoles.ThermalConsole.CoolantControl%d.BigLever.LeverUnion",
    pumpLamp = "Consoles.ThermalConsole.CoolantControl%d.Light%d.NeonPart",
    fanLever = "Consoles.ThermalConsole.CFLever%d.LeverUnion",
    fanLamp = "Consoles.ThermalConsole.CFLever%d.OfflineLight.NeonPart",
    cblLever = "Consoles.CBLaserConsole.CBL%dSystems.LargeLever.BigLever.LeverUnion",
    extract = "Consoles.ElectricGridConsole.ExtractionLever.BigLever.LeverUnion",
    massLever = "Consoles.ALTReactorConsole.MASS%dSystems.PowerLever.LeverUnion",
    massLamp = "Consoles.ALTReactorConsole.MASS%dSystems.PowerLever.Neon",
    shutters = "Consoles.ALTReactorConsole.ControlRoomSystems.ShuttersLever.LeverUnion",
    hdefLever = "Consoles.HDEFGenerator.PowerLever.BigLever.LeverUnion",
    hdefLamp = "Consoles.HDEFGenerator.PowerLever.BigLever.Neon%d",
    ventLever = "Consoles.MainReactorConsole.E_VENTLever%d.LeverUnion",
    startup = "Consoles.MainReactorConsole.StartUpBigLever.LeverUnion",
    -- Lamps added 2026-09-26. Every one of these was measured to exist before it
    -- was wired; three controls that might have been expected here were measured
    -- to carry no neon at all and are listed at the foot of Refresh instead.
    ventLamp = "Consoles.MainReactorConsole.E_VENTLever%d.OfflineLight.NeonPart",
    shutterLamp = "Consoles.ALTReactorConsole.ControlRoomSystems.ShuttersLever.OfflineLight.NeonPart",
    muteLamp = "Consoles.ALTReactorConsole.ControlRoomSystems.AlarmMuteButton.NeonPart",
    cblLamp = "Consoles.CBLaserConsole.CBL%dSystems.PressureButton.NeonPart",
    atmoLamp = "Consoles.MainReactorConsole.AtmosphereVentButton.NeonPart",
    -- A Model, not a part: the keyboard holds two NeonParts that share one name,
    -- so it is captured by walking its children (see Initialize) rather than by
    -- resolving a path, which would hand back the same part twice.
    samKeyboard = "Consoles.MainReactorConsole.SAMKeyboard",
    gravSwitchLamp = "Consoles.ElectricGridConsole.OverchargeLever.SwitchNeon",
    gravArmedLamp = "Consoles.ElectricGridConsole.OverloadButton.NeonPart",
}

local levers: {[string]: {part: BasePart, baseline: CFrame, travel: number, tween: Tween?}} = {}
local lamps: {[string]: {part: BasePart, baseline: Color3}} = {}
local lastSignature: string? = nil

local function resolve(path: string): Instance?
    local node: Instance? = workspace
    for token in string.gmatch(path, "[^.]+") do
        if not node then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

-- ========== WRITERS ==========
-- One lever pose, animated. The union SLIDES along its own axis (see the motion
-- contract at the top of the file), and it is tweened to the stop it was asked
-- for rather than assigned to it, so a throw reads as a hand working a detent
-- lever instead of a teleport. Nothing about the geometry changes: the stop
-- tweened to is the same CFrame this function used to assign, so the pose a
-- lever rests on is bit for bit what it always was. Only the way it gets there
-- is new.
--
-- The tween is created HERE, on the server. Delegating it to the client relay
-- the place already carries -- ReplicatedStorage.TweeningEvent, played by
-- ReplicatedFirst.ClientTweenReplicatedFirst -- would hand the write to every
-- client, and a client write is not overwritten until the server next changes
-- that property. That is the defect that retired the old
-- StarterPlayerScripts.VisualFeedback reflector, whose superseded header records
-- a C-Pump 3 lever reading 1.6 studs apart on the two sides and so appearing not
-- to move when it was clicked. Animating on this side of the wire keeps this
-- module the only writer of lever CFrames, which is the rule the backend follows.
local function poseLever(key: string, level: number, maxLevel: number)
    local entry = levers[key]
    if not entry then return end
    local part = entry.part
    -- A lever that streamed out from under us is skipped rather than recreated;
    -- the baseline is the authored CFrame and cannot be recovered from a nil.
    if not part.Parent then return end
    -- Translation only, along the lever's own baseline LookVector, so every
    -- lever slides on its own axis: the HDEF lever's LookVector is straight
    -- down and it has to travel straight down, not along world Y by accident.
    local goal = entry.baseline + entry.baseline.LookVector * throwDistance(level, maxLevel, entry.travel)
    -- Cancel before creating. Two live tweens on one CFrame both write it every
    -- frame and the winner is decided per frame, so a fast click-click could
    -- leave the union resting on a stop that is neither of the two that were
    -- asked for. Cancel leaves the union wherever it had reached and the new
    -- tween starts from there, which is also what makes an interrupted throw
    -- continue instead of jumping back to the stop it last finished on.
    if entry.tween then entry.tween:Cancel() end
    local tween = TweenService:Create(part, leverTweenInfo, {CFrame = goal})
    entry.tween = tween
    tween:Play()
end

-- A two-position control: level 1 is the authored position, level 2 is one
-- full throw away.
local function poseToggle(key: string, on: boolean)
    poseLever(key, on and 2 or 1, TOGGLE_MAX_LEVEL)
end

local function lightLamp(key: string, mode: string, config: any)
    local entry = lamps[key]
    if not entry then return end
    local part = entry.part
    if not part.Parent then return end
    local visual = config.Visual
    -- One branch per colour the consoles actually speak. `nominal`, `amber`,
    -- `yellow`, `purple` and `blue` were added on 2026-09-26 for the CBL status
    -- code and the offline lights; the first four modes predate them.
    -- An unknown mode falls through to Off rather than erroring, so a typo
    -- darkens one lamp instead of aborting the whole Refresh.
    local target = visual.Off
    if mode == "ready" then target = visual.Ready
    elseif mode == "nominal" then target = visual.Nominal
    elseif mode == "pulse" then target = visual.Pulse
    elseif mode == "amber" then target = visual.Amber
    elseif mode == "yellow" then target = visual.Yellow
    elseif mode == "purple" then target = visual.Purple
    elseif mode == "blue" then target = visual.Blue
    elseif mode == "fault" then target = visual.Fault
    end
    part.Color = target
end

-- ========== CAPTURE ==========
function VisualFeedback.Initialize(config: any)
    -- `levers` and `lamps` are deliberately NOT emptied here, and that is the fix
    -- for a real defect rather than tidiness. A SmallLever throw SIGN is measured
    -- from the union CURRENT position (see smallThrow): level 1 is whichever stop
    -- the rig is found on and level 2 is the other one. Refresh moves those
    -- unions, so any second call to Initialize taken after a Refresh reads the rig
    -- standing on its FAR stop and inverts its travel for the rest of the
    -- session -- the lever still moves on a click, it just moves the wrong way and
    -- lands on a pose the art does not contain, which looks correct from every
    -- other angle. It happened for real: in one playtest Initialize ran twice and
    -- the six fans measured -0.658 first and +0.700 second, and only the first of
    -- those is a measurement of the rig. A lever already captured with its part
    -- still parented is therefore left exactly as it was, which also keeps the
    -- captured count comparable between calls.
    lastSignature = nil

    -- The throw duration is read from Config rather than fixed here, and it is
    -- deliberately not required. This project has already spent a shift on a
    -- stale copy of a script whose only symptom was a field the Config module
    -- did not have yet, so a missing number must not take the levers down with
    -- it: it falls back to the module's own default and says which one it used.
    -- A lever that throws at the wrong speed is a much smaller failure than a
    -- lever that does not throw at all, and a silent fallback would be
    -- indistinguishable from the value having been read.
    local seconds = config and config.Visual and config.Visual.LeverTweenSeconds
    if typeof(seconds) == "number" and seconds > 0 then
        leverTweenInfo = TweenInfo.new(seconds, LEVER_EASING_STYLE, LEVER_EASING_DIRECTION)
    elseif not warnedTweenSeconds then
        warnedTweenSeconds = true
        warn(string.format(
            "[ReactorBackend][Visual] Config.Visual.LeverTweenSeconds is %s, not a positive number, so levers throw in the module's own %.2f s. The stops themselves are unaffected.",
            tostring(seconds), DEFAULT_LEVER_TWEEN_SECONDS))
    end

    local captured, missing = 0, {}

    -- `travel` is the family's measured span. `fromStop` marks the SmallLever
    -- family, whose sign is read per rig off the art because the same rig is
    -- authored on Up on some consoles and on Down on others.
    local function grabLever(key: string, path: string, travel: number, fromStop: boolean?)
        local known = levers[key]
        if known and known.part.Parent then
            captured += 1
            return
        end
        local part = resolve(path)
        if part and part:IsA("BasePart") then
            -- A union can be lost and re-resolved while it is midway through a
            -- throw, and a throw is now animated, so part.CFrame is not
            -- necessarily the pose the art authored. Re-measuring from it would
            -- capture a position between two stops, and smallThrow would then
            -- read the SIGN of the throw off that position -- the same invisible
            -- inversion the note at the top of Initialize describes. When the
            -- same instance came back there is nothing to measure: the entry we
            -- already hold records the authored CFrame and the throw that was
            -- measured from it, and both are still exact.
            if known and known.part == part then
                -- Its tween may still be running. Cancelling and dropping the
                -- handle is what stops the next pose from putting a second tween
                -- on the same CFrame; the union keeps the pose it had reached,
                -- and the Refresh that follows re-poses it from the baseline
                -- carried here.
                if known.tween then known.tween:Cancel() end
                levers[key] = {part = part, baseline = known.baseline, travel = known.travel}
            else
                local amount = travel
                if fromStop then amount = smallThrow(part) end
                levers[key] = {part = part, baseline = part.CFrame, travel = amount}
            end
            captured += 1
        else
            table.insert(missing, path)
        end
    end

    local function grabLamp(key: string, path: string)
        -- Same rule as grabLever and for the same reason: a second capture would
        -- record a colour this module had just painted rather than the authored
        -- one. Only a lamp whose part has gone is replaced.
        local known = lamps[key]
        if known and known.part.Parent then
            captured += 1
            return
        end
        local part = resolve(path)
        if part and part:IsA("BasePart") then
            lamps[key] = {part = part, baseline = part.Color}
            captured += 1
        else
            table.insert(missing, path)
        end
    end

    for i = 1, 3 do
        grabLever("pump" .. i, string.format(A.pumpLever, i), TRAVEL.pump, false)
        grabLever("cbl" .. i, string.format(A.cblLever, i), TRAVEL.cbl, false)
        grabLever("vent" .. i, string.format(A.ventLever, i), TRAVEL.small, true)
        for level = 1, 3 do
            grabLamp("pump" .. i .. "Lamp" .. level, string.format(A.pumpLamp, i, level))
        end
    end
    for i = 1, 6 do
        grabLever("fan" .. i, string.format(A.fanLever, i), TRAVEL.small, true)
        grabLamp("fan" .. i .. "Lamp", string.format(A.fanLamp, i))
    end
    for i = 1, 2 do
        grabLever("mass" .. i, string.format(A.massLever, i), TRAVEL.small, true)
        grabLamp("mass" .. i .. "Lamp", string.format(A.massLamp, i))
    end
    for level = 1, 3 do
        grabLamp("hdefLamp" .. level, string.format(A.hdefLamp, level))
    end
    grabLever("extract", A.extract, TRAVEL.extract, false)
    grabLever("shutters", A.shutters, TRAVEL.small, true)
    grabLever("hdef", A.hdefLever, TRAVEL.generic, false)
    grabLever("startup", A.startup, TRAVEL.start, false)

    -- ---- lamps wired 2026-09-26 ----
    for i = 1, 3 do
        grabLamp("vent" .. i .. "Lamp", string.format(A.ventLamp, i))
        grabLamp("cbl" .. i .. "Lamp", string.format(A.cblLamp, i))
    end
    grabLamp("shutterLamp", A.shutterLamp)
    grabLamp("muteLamp", A.muteLamp)
    grabLamp("atmoLamp", A.atmoLamp)
    grabLamp("gravSwitchLamp", A.gravSwitchLamp)
    grabLamp("gravArmedLamp", A.gravArmedLamp)
    -- SAMKeyboard is the one lamp that cannot go through grabLamp: its two
    -- NeonParts sit two levels down inside a button, not directly under the
    -- model, so resolve() -- which stops at the first match -- would have missed
    -- them entirely and both keys would have been handed nothing. They are
    -- walked over the whole subtree instead. GetDescendants and not GetChildren:
    -- a first version of this used GetChildren, found zero, and reported the
    -- keyboard missing, which is how the nesting was found.
    do
        local keyboard = resolve(A.samKeyboard)
        local found = 0
        if keyboard then
            for _, child in ipairs(keyboard:GetDescendants()) do
                if child:IsA("BasePart") and child.Name == "NeonPart" then
                    found += 1
                    local key = "samLamp" .. found
                    local known = lamps[key]
                    if not (known and known.part.Parent) then
                        lamps[key] = {part = child, baseline = child.Color}
                    end
                    -- Counted whether or not the entry was REPLACED, so the
                    -- printed total reads 54 on a repeat call as well as on the
                    -- first. It read 52 against 54 while this increment sat
                    -- inside the branch, which made the one number an operator
                    -- watches for a lost capture the one number that moved on
                    -- its own.
                    captured += 1
                end
            end
        end
        -- Reported through the same `missing` list as every other address, so a
        -- renamed keyboard is not the one failure that stays silent.
        if found == 0 then table.insert(missing, A.samKeyboard) end
    end

    -- Every lever's signed throw, printed once at boot. The sign is read per rig
    -- off the art and a wrong read is invisible in every other way: the lever
    -- still moves on click, it just moves to a pose the art does not contain.
    local roster = {}
    for key, entry in pairs(levers) do
        roster[#roster + 1] = string.format("%s=%+.3f", key, entry.travel)
    end
    table.sort(roster)
    print("[ReactorBackend][Visual] throws: " .. table.concat(roster, " "))

    -- Counted explicitly. The previous version printed #leverBaselines, and #
    -- on an Instance-keyed table is always 0, so it reported "captured 0" no
    -- matter how many it had actually captured.
    print(string.format("[ReactorBackend][Visual] captured %d baselines (%d levers, %d lamps)",
        captured, (function() local n = 0 for _ in pairs(levers) do n += 1 end return n end)(),
        (function() local n = 0 for _ in pairs(lamps) do n += 1 end return n end)()))
    if #missing > 0 then
        warn(string.format("[ReactorBackend][Visual] %d addresses did not resolve: %s",
            #missing, table.concat(missing, ", ")))
    end
end

-- ========== REFRESH ==========
function VisualFeedback.Refresh(state: any, config: any)
    -- Reaction loss is a property of the CHAMBER, not of any one CBL: manual
    -- item 18 says a CBL's maximum output is lowered when chamber pressure falls
    -- below roughly 2300 PSI, and Engine already demotes every CBL's level on
    -- exactly this comparison. Computed once here so the signature and the lamp
    -- cannot disagree about it.
    local reactionLoss = state.pressure < config.Sim.StallPressure
    -- The vent lamp reports availability, so the cooldown boundary enters the
    -- signature as a boolean. Using `state.ventUntil` itself would work too, but
    -- it is a raw clock: the boolean flips exactly once when the cooldown ends,
    -- which is the only moment the lamp has anything new to say.
    local ventReady = state.phase == "Running" and state.time >= state.ventUntil

    -- Cheap change detection: pose is only rewritten when an input it depends on
    -- actually moved, so the module does no CFrame work on a quiet tick.
    local inputs = {
        tostring(state.phase),
        tostring(state.monitorPower),
        tostring(state.shuttersOpen),
        tostring(state.extraction),
        tostring(state.hdef.enabled),
        tostring(math.floor(state.hdef.integrity)),
        tostring(state.mute),
        tostring(state.sam),
        tostring(state.grav.phase),
        tostring(ventReady),
        tostring(reactionLoss),
    }
    for i = 1, 3 do
        local pump = state.pumps[i]
        local cbl = state.cbl[i]
        table.insert(inputs, tostring(pump.enabled) .. pump.level .. tostring(math.floor(pump.integrity)))
        -- `stress > 0` and not `stress`: the lamp distinguishes "some integrity
        -- has been lost" from "none has", and a raw float would repaint the lamp
        -- on every tick of a slow accumulation without changing its colour.
        table.insert(inputs, tostring(cbl.active) .. cbl.level .. tostring(cbl.fault)
            .. tostring(cbl.stress > 0))
    end
    for i = 1, 6 do table.insert(inputs, tostring(state.fans[i])) end
    for i = 1, 2 do
        local mass = state.mass[i]
        table.insert(inputs, tostring(mass.enabled) .. mass.level)
    end
    local signature = table.concat(inputs, "|")
    if signature == lastSignature then return end
    lastSignature = signature

    -- ---- pumps: level selector 0..3, plus one lamp per level ----
    for i = 1, 3 do
        local pump = state.pumps[i]
        -- The lever is a detented selector: it holds the level that was chosen
        -- even while the pump is switched off. The engine draws exactly this
        -- line itself -- pump_level writes level alone, and cooling += pump.level
        -- happens only when enabled and integrity > 0 -- so the lever carries the
        -- selection and the lamps carry the effective contribution.
        poseLever("pump" .. i, pump.level, PUMP_MAX_LEVEL)
        local faulted = pump.integrity <= PUMP_FAULT_INTEGRITY
        for level = 1, 3 do
            local mode = "off"
            if pump.enabled and pump.level >= level then
                mode = faulted and "fault" or "ready"
            end
            lightLamp("pump" .. i .. "Lamp" .. level, mode, config)
        end
    end

    -- ---- cooling fans: binary, six of them ----
    for i = 1, 6 do
        local on = state.fans[i]
        poseToggle("fan" .. i, on)
        -- The authored name is OfflineLight, so it is lit when the fan is NOT
        -- running. Read from the name, not from the old code, which had it
        -- backwards and lit it while the fan was on.
        lightLamp("fan" .. i .. "Lamp", on and "off" or "fault", config)
    end

    -- ---- CBL: level selector 0..5, active only while the reactor runs ----
    for i = 1, 3 do
        local cbl = state.cbl[i]
        -- Same detent rule as the pumps. cbl.active is not a player control: the
        -- shift lifecycle sets it on entering Ready and clears it on shutdown.
        poseLever("cbl" .. i, cbl.level, CBL_MAX_LEVEL)
    end

    -- ---- extraction: level selector 1..4 ----
    poseLever("extract", state.extraction, EXTRACT_MAX_LEVEL)

    -- ---- MASS: the lever is the POWER LEVEL switch, and mass_level is a
    -- two-position toggle between level 1 and level 2, not a setter. The
    -- activation button is the separate on/off, so the lever carries the tap
    -- that is selected and the lamp reports whether the unit is enabled.
    for i = 1, 2 do
        local mass = state.mass[i]
        poseLever("mass" .. i, mass.level, MASS_MAX_LEVEL)
        lightLamp("mass" .. i .. "Lamp", mass.enabled and "ready" or "off", config)
    end

    -- ---- shutters, HDEF power, and the master start-up lever ----
    poseToggle("shutters", state.shuttersOpen)
    poseToggle("hdef", state.hdef.enabled)
    -- The start-up lever is thrown when the reactor has actually been started.
    -- It used to be posed from `booted`, which is a different thing and a
    -- prerequisite: pressing MONITOR BOOT set booted, which threw the MASTER
    -- START-UP lever by itself before anyone had pulled it. The two authored
    -- ClickParts are the two ends of this one lever -- ShutClickPart and
    -- StartClickPart -- so it must rest at Shut until start and return there
    -- when the shift ends or fails, which is what the phase list below says.
    -- This is a display correction only: no engine value is read differently.
    local started = state.phase == "Starting" or state.phase == "Running"
        or state.phase == "Stopping"
    poseToggle("startup", started)

    -- ---- HDEF integrity bar: three lamps, each one third of the range ----
    local hdefLampStep = config.Device.HDEFMaxIntegrity / HDEF_LAMP_SEGMENTS
    for level = 1, 3 do
        -- Lamp n covers the nth third of the range: all three are lit at full
        -- integrity and one stays lit all the way down to 1.
        -- `enabled` decides whether a lamp is lit at all, and `fault` only picks
        -- the colour of a lamp that is already lit. That is the same split the
        -- pump lamps use above, and it is not an arbitrary choice: `fault` is a
        -- separate engine field (hdef={enabled, integrity, heat, fault}), so
        -- folding the two together gave it no visual consequence of its own.
        -- This used to read `enabled and not fault`, which painted a merely
        -- switched-off HDEF red -- three faults reported on a healthy generator,
        -- which is exactly the reading an operator must never be given.
        local mode = "off"
        if state.hdef.enabled and state.hdef.integrity > (level - 1) * hdefLampStep then
            mode = state.hdef.fault and "fault" or "ready"
        end
        lightLamp("hdefLamp" .. level, mode, config)
    end

    -- ---- E-VENT: one shot each, so the lever latches once used ----
    for i = 1, 3 do
        local spent = state.emergencyUsed[i]
        poseToggle("vent" .. i, spent)
        -- The authored name is OfflineLight, the convention the fans already use:
        -- lit means the device is out of service. Here that reading is forced
        -- rather than chosen, because the lever latches on the very same field
        -- and the two must not be given different meanings.
        lightLamp("vent" .. i .. "Lamp", spent and "fault" or "off", config)
    end

    -- ---- shutters: OfflineLight again, and a shutter's service state is being
    -- OPEN, so closed is the condition that reads as lit ----
    lightLamp("shutterLamp", state.shuttersOpen and "off" or "amber", config)

    -- ---- alarm mute: lit while the alarm is silenced ----
    -- Authored (255,0,0), pure red, so the lamp already wore the colour it
    -- wanted and this only decides when it shows.
    lightLamp("muteLamp", state.mute and "fault" or "off", config)

    -- ---- atmosphere vent: the button is AVAILABLE, not active ----
    lightLamp("atmoLamp", ventReady and "nominal" or "off", config)

    -- ---- SAMOS: the keyboard's two lamps move together ----
    -- The engine carries one SAM boolean, so lighting both is the only
    -- indication the state can support; inventing a difference between the two
    -- lamps would be inventing state.
    for i = 1, 2 do
        lightLamp("samLamp" .. i, state.sam and "nominal" or "off", config)
    end

    -- ---- CBL status code, on each CBL's own pressure-purge button ----
    -- Manual item 17 states this code in words, so it is transcribed and not
    -- invented: Overload = Red, Integrity Loss = Purple, Reaction Loss = Blue,
    -- High CBL Output = Yellow. The test order below is that same order, which
    -- is descending severity as the manual lists it, so where two conditions
    -- hold at once the more severe one is the one shown. The gate is `active`,
    -- matching the rule the pump and HDEF blocks already use: a device that is
    -- switched off has no status to report. This is also the visual home that
    -- cbl.active was missing -- nothing else on the console ever showed it.
    for i = 1, 3 do
        local cbl = state.cbl[i]
        local mode = "off"
        if cbl.active then
            if cbl.fault then mode = "fault"
            elseif cbl.stress > 0 then mode = "purple"
            elseif reactionLoss then mode = "blue"
            elseif cbl.level >= CBL_MAX_LEVEL then mode = "yellow"
            else mode = "nominal"
            end
        end
        lightLamp("cbl" .. i .. "Lamp", mode, config)
    end

    -- ---- gravatron: charging on the lever's switch lamp, armed on the button ----
    -- Manual item 89: "When the button flashes yellow rapidly, that is when the
    -- overcharge is ready to be fired." OverloadButton.NeonPart is authored
    -- (255,255,0), pure yellow, and it is that button -- so the armed indication
    -- belongs there and not on the lever, which is where the earlier note had
    -- placed it before the part was measured. The rapid flash itself is not
    -- modelled, because Refresh is signature-gated at one second and an animation
    -- would need a timer this module does not have. Steady yellow is the same
    -- distinction without the animation; that is a known simplification and is
    -- recorded as one rather than passed off as the manual's behaviour.
    local charging = state.grav.phase ~= "Idle"
    lightLamp("gravSwitchLamp", charging and "ready" or "off", config)
    lightLamp("gravArmedLamp", state.grav.phase == "Armed" and "yellow" or "off", config)

    -- ========== MEASURED: NO LAMP EXISTS ==========
    -- Four controls carry no neon part at all, so they cannot be given a lamp
    -- without adding geometry, and adding geometry is out of scope. Each was
    -- measured rather than assumed:
    --   MainReactorConsole.MonitorBootButton                 no NeonPart
    --   MainReactorConsole.MonitorPowerButton                no NeonPart
    --   ALTReactorConsole.ControlRoomSystems.RoomLightButton no NeonPart
    --   ElectricGridConsole.ExtractionLever      no lamp anywhere in the model
    -- so `boot`, `monitor_power`, `lights` and the extraction selector stay
    -- lever-only by omission of the art, not by a decision taken here.
end

return VisualFeedback
