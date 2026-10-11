local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Every synthesizer so far accepted the call and changed nothing, and "accepted
-- and did nothing" is exactly the shape of a function that is not wired to
-- anything.  One reading separates that from "it worked but the coordinates were
-- wrong": the mouse's own position.  If SendMouseMoveEvent moves the mouse,
-- the family is live and the fault is in where I aimed.  If the mouse does not
-- move, the family is inert here and no amount of aiming will help.
local P = game:GetService('Players')
local lp = P.LocalPlayer
local hrp = lp.Character and lp.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local UIS = game:GetService('UserInputService')
local vim = game:GetService('VirtualInputManager')
local mouse = lp:GetMouse()

local function where()
  local m = UIS:GetMouseLocation()
  return string.format('UIS=(%.0f,%.0f) mouse=(%s,%s) hit=%s', m.X, m.Y,
    tostring(mouse.X), tostring(mouse.Y), tostring(mouse.Target and mouse.Target.Name))
end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.0)
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
cam.CFrame = CFrame.lookAt(start.Position + Vector3.new(0, 2.2, 3.2), start.Position)
task.wait(0.5)

local rec = { 'mode=' .. tostring(UIS.MouseBehavior) .. '  ' .. where() }

-- move the mouse somewhere obviously different from wherever it is now
local targetX, targetY = 300, 500
pcall(function() vim:SendMouseMoveEvent(targetX, targetY, false) end)
task.wait(0.4)
rec[#rec+1] = 'after SendMouseMoveEvent(' .. targetX .. ',' .. targetY .. '): ' .. where()

-- second form: some builds take the processed flag in a different slot
pcall(function() vim:SendMouseMoveEvent(targetX, targetY, true) end)
task.wait(0.3)
rec[#rec+1] = 'after SendMouseMoveEvent(...,true): ' .. where()

return { tok = TOKEN, rec = rec }
