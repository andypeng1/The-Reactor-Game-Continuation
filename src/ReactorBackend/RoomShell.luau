--!strict
-- The facility shell: what the Control Room Functions do to the ROOM itself.
--
-- VisualFeedback owns every console lever and every console lamp, and says so.
-- This module owns the other half of the same controls -- the parts of the
-- world those consoles are pointed at -- and it is the only writer of each of
-- them, the same single-writer rule the rest of the backend follows:
--
--   ROOM LIGHT     Workspace.RoomLights.ControlRoomLights: the Color and
--                  Transparency of its 20 NeonParts, and the Enabled flag of
--                  the SurfaceLights on its 8 LightParts.
--   SHUTTERS       the three control room window shutters, which retract by
--                  moving DOWN by Config.Shell.ShutterTravel. Only each
--                  shutter's Frame is written: Glass is welded to it.
--   MONITOR POWER  per monitor: PowerNeon.Color, Screen.SurfaceLight.Enabled
--                  and Screen.MonitorUI.Enabled.
--   MONITOR BOOT   which of each monitor's authored faces is Visible.
--     + MASTER
--       START-UP
--
-- Why one control can own three things, and why the screens belong to the whole
-- chain rather than to the boot switch: a monitor that is powered but not yet
-- booted, one that is booted and waiting on the master lever, one whose reactor
-- is running and one whose shift has ended are four different faces the art
-- already draws, and the engine's phase is exactly the thing that chooses
-- between them.
--
-- Why this module exists: MonitorBootButton, MonitorPowerButton and
-- RoomLightButton were each measured to carry no NeonPart of their own
-- (recorded at the foot of VisualFeedback.Refresh), and no script anywhere in
-- ServerScriptService, ReplicatedStorage, StarterPlayer or StarterGui names
-- RoomLights, MonitorUI or PowerNeon. The world side of the start-up chain was
-- authored as art and left unwired. Nothing here is a new mechanic -- it is the
-- consequence the art was built for, which is why no gate, cost or timing in
-- Engine is touched to make it happen.
--
-- Deliberately NOT owned here:
--   * BootUI. Its BootUpText is authored empty, so it renders nothing in any
--     state; toggling it would change nothing visible, and writing text into it
--     would overlap BootFrame, whose own 'MS-1S DIAGNOSTIC MODE' is the
--     authored boot screen. Left exactly as the art has it.
--   * SmallLogo, EFEFrame, GlitchEffect, TransferIcon, ConnectionFrame,
--     DiagnosticFrame, ProtocolFrame and DetonationFrame -- other faces this
--     module has no phase to choose between.
--   * every cell of Workspace.RoomLights except ControlRoomLights. The manual
--     groups these controls as Control Room Functions and the place authors
--     every other room lit; this module lights the one room the art left dark.

local RoomShell = {}

-- ========== ADDRESSES ==========
-- Dot paths resolved from Workspace, spelled the way the place spells them so a
-- rename in Studio shows up here as a missing node rather than as silence.
local ROOM_LIGHTS = 'RoomLights.ControlRoomLights'
local MONITORS = 'Monitors'
-- The three control room windows. Each is a Model holding an anchored Frame
-- (the panel, and the parent of the weld) and an unanchored Glass welded to it,
-- so writing the Frame's CFrame is what moves both.
local SHUTTERS = {
    'MovingParts.ControlRoomLShutter',
    'MovingParts.ControlRoomMShutter',
    'MovingParts.ControlRoomRShutter',
}

-- The authored faces every control room monitor either has or does not. Kept as
-- a list so a monitor missing one is reported by name at Initialize instead of
-- quietly showing nothing.
local FACE_NAMES = {'BootFrame','PreStartupFrame','MainMonitorFrame','ShutdownFrame','ErrorFrame'}
-- The two shapes the idle face is authored in: the three large monitors draw a
-- full logo, the five small ones draw an icon plus a wordmark. SmallLogo also
-- exists on some monitors but was authored hidden on every one of them, so it
-- is not treated as a face.
local SPLASH_NAMES = {'Logo','BootIcon','CompanyLogo'}

local function resolve(path)
    local node = workspace
    for token in string.gmatch(path,'[^.]+') do
        if node == nil then return nil end
        node = node:FindFirstChild(token)
    end
    return node
end

-- ========== CAPTURE ==========
-- References only. No colour, transparency or Visible flag is baselined from
-- the world, because a baseline captured after the first Refresh would read the
-- module's own output back as if the art had authored it.
local lamps = {}
local emitters = {}
local monitors = {}
local shutters = {}
-- Unlike the three tables above, this latch is NOT cleared by Initialize. See
-- the capture block below for why.
local shuttersCaptured = false
local lastSignature: string? = nil

local function collectFaces(ui, names)
    local out = {}
    for _, name in ipairs(names) do
        local frame = ui:FindFirstChild(name)
        if frame and frame:IsA('GuiObject') then out[#out+1] = frame end
    end
    return out
end

function RoomShell.Initialize(config)
    -- Emptied rather than appended to. capture is the only thing here that can
    -- be run twice, and if it were additive a re-run would double every write
    -- list -- harmless to look at, because the writes are all idempotent, but it
    -- would mean the module quietly does twice the work for the rest of the
    -- session. Clearing it also makes re-running Initialize a real re-resolve,
    -- which is what you want after an art change.
    lamps = {}
    emitters = {}
    monitors = {}
    local problems = {}
    local root = resolve(ROOM_LIGHTS)
    if root == nil then
        problems[#problems+1] = 'missing '..ROOM_LIGHTS
    else
        -- A cell is two kinds of part, told apart structurally rather than by
        -- name: the lamp you can see, and the emitter you cannot -- a part at
        -- Transparency 1 whose SurfaceLight does the actual lighting. All 64
        -- emitters in this place's other light cells are authored that way, in
        -- colours as arbitrary as (255,255,0), which is the tell that an
        -- emitter's own appearance is fixture design and not lighting state.
        -- Writing this module's lamp transparency onto one would take it from
        -- invisible to visible, so they are separated here instead of being
        -- swept up together. The emitter bodies are checked rather than written:
        -- if one drifts, that is the art being edited, and this module says so.
        for _, descendant in ipairs(root:GetDescendants()) do
            if descendant:IsA('BasePart') and descendant.Material == Enum.Material.Neon then
                if descendant:FindFirstChildWhichIsA('SurfaceLight') then
                    if math.abs(descendant.Transparency - config.Shell.EmitterTransparency) > 0.001 then
                        problems[#problems+1] = string.format(
                            '%s is an emitter at Transparency %.2f, not %.2f',
                            descendant.Name, descendant.Transparency, config.Shell.EmitterTransparency)
                    end
                else
                    lamps[#lamps+1] = descendant
                end
            elseif descendant:IsA('SurfaceLight') then
                emitters[#emitters+1] = descendant
            end
        end
        if #lamps == 0 then problems[#problems+1] = ROOM_LIGHTS..' has no lit parts' end
        if #emitters == 0 then problems[#problems+1] = ROOM_LIGHTS..' has no surface lights' end
    end
    local folder = resolve(MONITORS)
    if folder == nil then
        problems[#problems+1] = 'missing '..MONITORS
    else
        for _, child in ipairs(folder:GetChildren()) do
            if string.sub(child.Name,-18) == 'ControlRoomMonitor' then
                local screen = child:FindFirstChild('Screen')
                local ui = screen and screen:FindFirstChild('MonitorUI')
                if ui == nil or not ui:IsA('SurfaceGui') then
                    problems[#problems+1] = child.Name..' has no Screen.MonitorUI'
                else
                    local owned = collectFaces(ui, FACE_NAMES)
                    local splash = collectFaces(ui, SPLASH_NAMES)
                    if #splash == 0 then problems[#problems+1] = child.Name..' has no idle face' end
                    if #owned == 0 then problems[#problems+1] = child.Name..' has no operational faces' end
                    for _, frame in ipairs(splash) do owned[#owned+1] = frame end
                    monitors[#monitors+1] = {
                        name = child.Name,
                        powerNeon = child:FindFirstChild('PowerNeon'),
                        screenLight = screen and screen:FindFirstChild('SurfaceLight'),
                        ui = ui,
                        splash = splash,
                        owned = owned,
                        boot = ui:FindFirstChild('BootFrame'),
                        preStartup = ui:FindFirstChild('PreStartupFrame'),
                        main = ui:FindFirstChild('MainMonitorFrame'),
                        shutdown = ui:FindFirstChild('ShutdownFrame'),
                        errorFrame = ui:FindFirstChild('ErrorFrame'),
                    }
                end
            end
        end
        if #monitors == 0 then problems[#problems+1] = MONITORS..' has no control room monitors' end
    end
    -- Read once and never again, which is why the latch is not cleared above.
    -- A shutter's open position is the closed one minus the travel, so the
    -- authored (closed) CFrame is the only thing that has to come off the world
    -- -- and reading it a second time, after a Refresh has already lowered the
    -- panel, would capture the OPEN position as the authored one and invert the
    -- switch, exactly the trap Config.Shell.MonitorPowerOff warns about.
    -- Restating three world CFrames in Config would dodge the read but would
    -- put the art's coordinates in a config file; a latch keeps the read and
    -- still makes a re-run a no-op.
    if not shuttersCaptured then
        for _, path in ipairs(SHUTTERS) do
            local model = resolve(path)
            if model == nil then
                problems[#problems+1] = 'missing '..path
            else
                local frame = model:FindFirstChild('Frame')
                if frame == nil or not frame:IsA('BasePart') then
                    problems[#problems+1] = path..' has no Frame part to move'
                else
                    shutters[#shutters+1] = {path = path, frame = frame, closed = frame.CFrame}
                end
            end
        end
        -- Latched only on a complete read, so a partial capture is retried by
        -- the next Initialize instead of being frozen in half-built.
        shuttersCaptured = #shutters == #SHUTTERS
    end
    if #problems > 0 then
        -- Reported rather than skipped. A silent miss here would look exactly
        -- like a monitor that is simply switched off, which is the one failure
        -- this module can produce that nobody would notice.
        warn('[RoomShell] incomplete capture: '..table.concat(problems,'; '))
    end
    print(string.format('[RoomShell] captured %d room lamps, %d room lights, %d monitors, %d shutters',
        #lamps, #emitters, #monitors, #shutters))
    return #lamps, #emitters, #monitors, #shutters
end

-- ========== WRITERS ==========
local function applyLights(on, config)
    local shell = config.Shell
    local colour = on and shell.RoomLightOn.Color or shell.RoomLightOff.Color
    local alpha = on and shell.RoomLightOn.Transparency or shell.RoomLightOff.Transparency
    for _, lamp in ipairs(lamps) do
        if lamp.Parent then
            lamp.Color = colour
            lamp.Transparency = alpha
        end
    end
    for _, light in ipairs(emitters) do
        if light.Parent then light.Enabled = on end
    end
end

-- Which authored face a monitor shows in a given phase. Falling back to the idle
-- face rather than to nothing means a monitor can never be powered and blank:
-- every branch returns something unless the art itself is missing.
local function faceFor(mon, state)
    local phase = state.phase
    if phase == 'Booting' then
        -- The three large monitors have the authored diagnostic screen; the
        -- five small ones were built without it, so for them the boot shows as
        -- the lit idle face instead.
        if mon.boot then return {mon.boot} end
    elseif phase == 'Ready' then
        -- Powered and booted, waiting on the master lever. PreStartupFrame is
        -- authored as a full-width strip along the bottom rather than as a full
        -- screen, so it reads as a banner over the idle face -- which is what
        -- 'PENDING REACTOR ACTIVATION' is for.
        local out = {}
        for _, frame in ipairs(mon.splash) do out[#out+1] = frame end
        if mon.preStartup then out[#out+1] = mon.preStartup end
        return out
    elseif phase == 'Starting' or phase == 'Running' then
        if mon.main then return {mon.main} end
    elseif phase == 'Stopping' or phase == 'Report' then
        if mon.shutdown then return {mon.shutdown} end
    elseif phase == 'Failed' then
        if mon.errorFrame then return {mon.errorFrame} end
    end
    return mon.splash
end

local function applyMonitors(state, config)
    local powered = state.monitorPower == true
    -- Same measured green the place uses for any healthy device. The off colour
    -- is Config's, not a captured baseline -- see the note in Config.Shell.
    local onColour = config.Visual.Nominal
    local offColour = config.Shell.MonitorPowerOff
    for _, mon in ipairs(monitors) do
        if mon.powerNeon and mon.powerNeon.Parent then
            mon.powerNeon.Color = powered and onColour or offColour
        end
        if mon.screenLight and mon.screenLight.Parent then
            mon.screenLight.Enabled = powered
        end
        if mon.ui and mon.ui.Parent then
            mon.ui.Enabled = powered
        end
        -- Faces are set on both branches, not only the powered one. Leaving them
        -- alone while unpowered made the world depend on what a monitor happened
        -- to be showing before it lost power, so one engine state could leave two
        -- different worlds behind -- and it did: the place was found with five
        -- monitors holding an idle face and three holding BootFrame, on monitors
        -- the art otherwise builds identically. An unpowered monitor shows
        -- nothing, which is both the truth and the same answer every time.
        for _, frame in ipairs(mon.owned) do
            if frame.Parent then frame.Visible = false end
        end
        if powered then
            for _, frame in ipairs(faceFor(mon, state)) do
                if frame.Parent then frame.Visible = true end
            end
        end
    end
end

-- Open is closed MINUS the travel, and the subtraction is a world vector rather
-- than a rotation: the shutters slide down in world space. That matters for the
-- middle one -- its Frame is rotated 90 degrees about Y, so writing
-- `closed * CFrame.new(0,-travel,0)` would move it along its own local Y, which
-- is still up, but there is no reason to depend on the rotation being harmless.
-- Subtracting a Vector3 from a CFrame is the engine's own "translate in world
-- space" and is the same operation the operator described: descend 10.58.
local function applyShutters(open, config)
    local travel = Vector3.new(0, config.Shell.ShutterTravel, 0)
    for _, shutter in ipairs(shutters) do
        if shutter.frame.Parent then
            shutter.frame.CFrame = open and (shutter.closed - travel) or shutter.closed
        end
    end
end

-- ========== REFRESH ==========
-- Signature-gated for the same reason VisualFeedback is: a quiet tick must not
-- walk 7 monitors, 28 light instances and 3 shutters to write the values they
-- already hold. The shutter state belongs in the signature for the same reason
-- the others do -- without it, the one tick that opens the shutters would be
-- swallowed as a no-op by a signature that had not changed.
function RoomShell.Refresh(state, config)
    local signature = table.concat({
        tostring(state.lights), tostring(state.monitorPower),
        tostring(state.booted), tostring(state.phase),
        tostring(state.shuttersOpen)}, '|')
    if signature == lastSignature then return end
    lastSignature = signature
    applyLights(state.lights == true, config)
    applyShutters(state.shuttersOpen == true, config)
    applyMonitors(state, config)
end

return RoomShell
