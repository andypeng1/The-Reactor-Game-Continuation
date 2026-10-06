local task = require("@lune/task")
local current = {
    Temperature = 5600,
    Pressure = 6000,
    ActiveFan = 0,
    PEALevel = 1,
    State = 1
}
local PressureBenefitPreTemp = {
    [1] = 0.01,
    [2] = 0.0075,
    [3] = 0.005
}
local PressureBenefitPEA = {
    [1] = 0,
    [2] = 0,
    [3] = 75,
    [4] = 150
}
local PressureBenefitState = {
    [1] = 110,
    [2] = 350,
    [3] = 800
}
-- p=g_{n}\left[b\right]-60n+s_{n}\left[b\right]t+d_{n}\left[q\right]
function MainLoop()
    if current.Temperature >= 5600 and current.Temperature < 17500 then
        current.State = 1
    elseif current.Temperature >= 17500 and current.Temperature <= 29499 then
        current.State = 2
    elseif current.Temperature > 29499 then
        current.State = 3
    end
    current.Pressure += PressureBenefitState[current.State] + PressureBenefitPreTemp[current.State] * current.Temperature + PressureBenefitPEA[current.PEALevel] - 60 * current.ActiveFan
    print("Pressure: " .. current.Pressure)
end

while true do
    MainLoop()
    task.wait(1)
end