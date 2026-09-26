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
    local engine=Engine.new(Config)
    backend:SetAttribute('RuntimePhase',engine.state.phase)
    StateBridge.Publish(engine.state)
    local bound = ControlBinder.Bind(engine,function(state)
        backend:SetAttribute('RuntimePhase',state.phase)
        StateBridge.Publish(state)
    end)
    backend:SetAttribute('BoundControls',bound)
    local accumulator=0
    RunService.Heartbeat:Connect(function(dt)
        accumulator+=math.min(dt,0.5)
        if accumulator<Config.Visual.RefreshSeconds then return end
        local step=accumulator; accumulator=0
        local updateOk,updateErr=pcall(function()
            engine:Update(step)
            backend:SetAttribute('RuntimePhase',engine.state.phase)
            StateBridge.Publish(engine.state)
        end)
        if not updateOk then
            backend:SetAttribute('RuntimeError',tostring(updateErr))
            warn('[ReactorBackend] update failed: '..tostring(updateErr))
        end
    end)
    print(string.format('[ReactorBackend] runtime %s online: 62-control adapter, server-owned engine',Config.Version))
end, debug.traceback)
if not ok then
    backend:SetAttribute('RuntimeError',tostring(err))
    warn('[ReactorBackend] boot failed: '..tostring(err))
end
