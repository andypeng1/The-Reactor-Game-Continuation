--!strict
local backend=script.Parent
backend:SetAttribute('RuntimeBooted',true)
backend:SetAttribute('RuntimeError','')
local ok, err = xpcall(function()
    local RunService=game:GetService('RunService')
    local Config=require(backend.Config)
    local Engine=require(backend.Engine)
    local StateBridge=require(backend.StateBridge)
    local ControlBinder=require(backend.ControlBinder)
    local VisualFeedback=require(backend.VisualFeedback)
    local RoomShell=require(backend.RoomShell)
    local FacilityCascade=require(backend.FacilityCascade)
    local LogPanel=require(backend.LogPanel)
    local BootPanel=require(backend.BootPanel)
    local EndShiftBridge=require(backend.EndShiftBridge)
    local engine=Engine.new(Config)
    backend:SetAttribute('RuntimePhase',engine.state.phase)
    StateBridge.Publish(engine.state)
    -- Baselines are captured after the first publish and before anything has
    -- had a chance to move a lever, so they are the authored CFrames.
    VisualFeedback.Initialize(Config)
    VisualFeedback.Refresh(engine.state,Config)
    -- RoomShell is the facility half of the same two controls VisualFeedback
    -- poses on the console: the room lights, and the seven monitors' own power
    -- lamps and screens. It follows the identical capture-then-refresh shape,
    -- and the identical rule that only one module writes a given property.
    RoomShell.Initialize(Config)
    RoomShell.Refresh(engine.state,Config)
    -- FacilityCascade is the WORLD's half of the same chain RoomShell's monitors
    -- and the log panel narrate: the lamp waves, the CBLs energising and firing,
    -- the chamber alarms flashing and the core going critical. It is the one
    -- adapter here that also needs every frame rather than the one-second logic
    -- gate -- its ramps and bursts are continuous -- so its Step is driven from
    -- the Heartbeat connection directly (CLAUDE.md section 0.19: the same code
    -- reachable as a public function, never work hidden inside a connection).
    -- Its lamp capture must run after RoomShell's for the same reason
    -- BootPanel's does: they must never both believe they own a property.
    FacilityCascade.Initialize(Config)
    FacilityCascade.Refresh(engine.state,Config)
    -- BootPanel is the narrowest of the four adapters: it animates the lines
    -- INSIDE the boot face RoomShell has just chosen. It is initialized after
    -- RoomShell for that reason and no other -- the two write disjoint
    -- properties, so their order is a readability choice, not a dependency.
    BootPanel.Initialize(Config)
    BootPanel.Refresh(engine.state,Config)
    -- The log panel is an output adapter on the same terms as the other two: it
    -- owns no state and only reads the engine's own event list, which until this
    -- was written had no reader anywhere in the place.
    LogPanel.Refresh(engine)
    -- One closure, handed to every input path. A control arriving over a
    -- ClickDetector and one arriving over a remote are then indistinguishable
    -- downstream, and a shift restarted from the report screen repaints the same
    -- adapters as one restarted from the console.
    local function publish(state)
        backend:SetAttribute('RuntimePhase',state.phase)
        -- Refreshed before the publish so the lever and the monitor reading it
        -- caused are never one tick apart.
        VisualFeedback.Refresh(state,Config)
        RoomShell.Refresh(state,Config)
        FacilityCascade.Refresh(state,Config)
        BootPanel.Refresh(state,Config)
        LogPanel.Refresh(engine)
        StateBridge.Publish(state)
        -- The end-of-shift report is an output on the same terms as the log
        -- panel: it owns no state, it only reads the engine's phase, and it
        -- fires once per ending per player.
        EndShiftBridge.Publish(engine)
    end
    local bound = ControlBinder.Bind(engine,publish)
    backend:SetAttribute('BoundControls',bound)
    local accumulator=0
    RunService.Heartbeat:Connect(function(dt)
        -- Before the gate, and deliberately so. Everything the cascade does that
        -- is continuous -- the four lamp ramps, the CBL firing sphere's collapse,
        -- the ten-second alarm flash -- is driven from here, and behind a
        -- one-second accumulator a 1.6 s ramp would be two hard steps and a
        -- 10.9 s flash would be an eleven-second cliff at its end. dt is
        -- clamped inside the same step the accumulator uses, because a single
        -- Heartbeat after a long frame stall can carry several seconds and the
        -- cascade must not spend them all in one frame.
        FacilityCascade.Step(math.min(dt,0.5))
        accumulator+=math.min(dt,0.5)
        if accumulator<Config.Visual.RefreshSeconds then return end
        local step=accumulator; accumulator=0
        local updateOk,updateErr=pcall(function()
            -- The engine's own drift has to reach the levers too, not only the
            -- numbers: temperature, integrity and stress all move with no player
            -- input at all, and indicators must follow them. publish is the same
            -- closure the console clicks and the report screen's buttons go
            -- through, so there is one refresh order in the file, not three.
            engine:Update(step)
            publish(engine.state)
        end)
        if not updateOk then
            backend:SetAttribute('RuntimeError',tostring(updateErr))
            warn('[ReactorBackend] update failed: '..tostring(updateErr))
        end
    end)
    print(string.format('[ReactorBackend] runtime %s online: 62-control adapter, server-owned engine',Config.Version))
    -- The end-of-shift transport lives in its own module: it is the same shape
    -- as the other adapters (a public function over instance state, CLAUDE.md
    -- 0.19) and it is the missing half of a contract the legacy screen already
    -- states -- it waits on EndShift.OnClientEvent and fires MiscEvent, and
    -- until 2026-10-13 neither one had a counterpart on this side.
    backend:SetAttribute('ShiftTransport',EndShiftBridge.Bind(engine,publish))
end, debug.traceback)
if not ok then
    backend:SetAttribute('RuntimeError',tostring(err))
    warn('[ReactorBackend] boot failed: '..tostring(err))
end
