local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- Argument positions, measured instead of reasoned about.  Two error strings
-- disagreed about which position wants an Object and which wants an int, and the
-- disagreement is the signal: the conversions are not reported in the order the
-- parameters are written.  So walk a grid and let each result name its own type.
--
-- (The first cut of this used '...' inside the nested pcall closure, which is the
-- inner function's varargs and not the outer's -- it died before reaching any
-- call.  Explicit tables instead.)
local P = game:GetService('Players')
local hrp = P.LocalPlayer and P.LocalPlayer.Character and P.LocalPlayer.Character:FindFirstChild('HumanoidRootPart')
if hrp == nil then return { tok = TOKEN, err = 'no character' } end

local big = workspace.Consoles.MainReactorConsole.StartUpBigLever
local start = big:FindFirstChild('StartClickPart')
hrp.CFrame = CFrame.new(110.4, 284.0, 1.5)
task.wait(2.0)
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
cam.CFrame = CFrame.lookAt(start.Position + Vector3.new(0, 2.2, 3.2), start.Position)
task.wait(0.4)

local vim = game:GetService('VirtualInputManager')
local inset = game:GetService('GuiService'):GetGuiInset()
local vp3 = cam:WorldToViewportPoint(start.Position)
local X, Y = vp3.X, vp3.Y + inset.Y

local grid = {}
local function t(label, args)
  local ok, err = pcall(function() vim:SendMouseButtonEvent(table.unpack(args)) end)
  grid[#grid+1] = label .. ' -> ' .. (ok and 'ACCEPTED' or tostring(err))
end

t('x,y,0,T,F,0', { X, Y, 0, true, false, 0 })
t('x,y,0,T,F,1', { X, Y, 0, true, false, 1 })
t('x,y,0,T,F,true', { X, Y, 0, true, false, true })
t('x,y,0,T,F,F', { X, Y, 0, true, false, false })
t('x,y,0,T,game,1', { X, Y, 0, true, game, 1 })
t('x,y,0,T,game,0', { X, Y, 0, true, game, 0 })
t('x,y,0,T,cam,1', { X, Y, 0, true, cam, 1 })
t('x,y,0,T,1,1', { X, Y, 0, true, 1, 1 })
t('x,y,0,F,game,1', { X, Y, 0, false, game, 1 })
t('x,y,1,T,game,1', { X, Y, 1, true, game, 1 })
t('x,y,0,T,game (5 args)', { X, Y, 0, true, game })
t('x,y,0,T,false,game,1', { X, Y, 0, true, false, game, 1 })

return { tok = TOKEN, grid = grid, X = X, Y = Y }
