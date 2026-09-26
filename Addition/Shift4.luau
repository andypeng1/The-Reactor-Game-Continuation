--[[ me and my friend tried to maek a concept of what could shift 4 be, we just took stuff from our imagination. This is called in-game modding using code injection, the same way "doors" people did mods of the game because no update was coming out.

credits:

*second EFE: larpgod
*mainframe destabilization as a result of second EFE, needing to keep  *core temp around a specific range: larpgod
*mainframe destabilization gui: larpgod
*shift 4 appearing in lobby: me (but rescripted by larpgod)
*custom quota: me (needed to do the following: code my own quota bar, code my own power system (net output), code my own P.E.A system, make sure server couldn't blink the lever LED and make it beep by replacing both assets with my own. After all those replacements and recodes are done, remove all old assets locally.
*auto-coolant repair upgrade (S.A.M.O.S does things to recalibrate coolant processor): me

as a result you might see (bugs):
*inconsistent net output (i tried my best to make an approximation of how does the game handle net output, i tried.)
*the upgrades panel doing weird shit
*the final shift results saying "shift 3" instead of "shift 4"

warning: nothing is modified serversidedly, and everything is modified locally with code injection. There is a limit to what can be done in the client however. If the game had to be fully customized, we would most likely just saveinstance it and recode it from scratch, which is 100x harder and more time-wasting.

we tried our best!! we're not the developers of the game, just modders. ]]

identifyexecutor = identifyexecutor or function(...)
	return "shitlora","-1.0.0"
end

firesignal = firesignal or function(...)
	warn("yo executor doesnt support firesignal..")
	warn("lock innn..")
	warn("although what should i have expected from "..identifyexecutor())
end

fireclickdetector = fireclickdetector or function()
	warn("no way ur executor actually doesnt support this bro")
end



local corefolder = Instance.new("Folder")
local values = Instance.new("Folder")
--local scriptAlreadyRan = values:FindFirstChild("ScriptAlreadyRan")

--[[ if not scriptAlreadyRan then
	scriptAlreadyRan = Instance.new("BoolValue")
	scriptAlreadyRan.Name = "ScriptAlreadyRan"
	scriptAlreadyRan.Value = true
	scriptAlreadyRan.Parent = values
else
	if scriptAlreadyRan.Value then
		print("You know... i have done all previous checks, but this specific check has failed. The script is already running bitch why do you want to run it twice?")
		return
	end

	scriptAlreadyRan.Value = true
end ]]

if getgenv().scriptAlreadyRan then
  print("You know... i have done all previous checks, but this specific check has failed. The script is already running bitch why do you want to run it twice?")
  return false
else
  getgenv().scriptAlreadyRan=true
 end



local assets = game:GetObjects(getcustomasset("assets.rbxm"))[1]

assets.Meltdown:Clone().Parent=workspace.Monitors.ThermalControlRoomMonitor.Screen
assets.Meltdown:Clone().Parent=workspace.Monitors.PowerControlRoomMonitor.Screen
assets.Meltdown.Parent=workspace.Monitors.MainControlRoomMonitor.Screen

assets.ou_shi_electricity_go_brrrr.Parent=workspace.SoundBlocks.ControlRoomSound

local monitors = workspace.Monitors
local soundblocks = workspace.SoundBlocks
local controls = workspace.Consoles
local coreinfo = game.Workspace.Stats
local corestats = game.Workspace.Stats.Core
local peaLevel = game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.ExtractionLabel
local leverLED = game.Workspace.Consoles.MainReactorConsole.SwitchNeon:Clone()
local readysound = game.Workspace.Consoles.MainReactorConsole.SoundBlock.ReadySound:Clone()
local leverisdoingthing = false
readysound.Name = "yeah"
local efe2multiplier = 1


-- quota complete color in rgb 85, 170, 255

local quota = 6002000000000
local currentlygenerated = 0
local tempval = game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.TempLabel

-- Gui to Lua
-- Version: 3.2

-- Instances:

local EnergyProgressFrame = Instance.new("Frame")
local yeah = Instance.new("Frame")
local Background = Instance.new("ImageLabel")

--Properties:

EnergyProgressFrame.Name = "próggresse of enigri frame rayrahrahrharh"
EnergyProgressFrame.Parent = game.Workspace.Monitors.QuotaControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.QuotaFrame
EnergyProgressFrame.BackgroundColor3 = Color3.fromRGB(27, 18, 0)
EnergyProgressFrame.BorderColor3 = Color3.fromRGB(50, 48, 31)
EnergyProgressFrame.BorderSizePixel = 5
EnergyProgressFrame.Position = UDim2.new(0, 0, 1, 15)
EnergyProgressFrame.Size = UDim2.new(1, -2, 0, 30)

yeah.Name = "bár of frame"
yeah.Parent = EnergyProgressFrame
yeah.AnchorPoint = Vector2.new(0, 1)
yeah.BackgroundColor3 = Color3.fromRGB(255, 255, 0)
yeah.BackgroundTransparency = 0.500
yeah.BorderColor3 = Color3.fromRGB(0, 0, 0)
yeah.BorderSizePixel = 0
yeah.Position = UDim2.new(0, 0, 1, 0)
yeah.Size = UDim2.new(0.00999999978, 0, 1, 0)
yeah.ZIndex = 3

Background.Name = "Background"
Background.Parent = EnergyProgressFrame
Background.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
Background.BackgroundTransparency = 1.000
Background.BorderColor3 = Color3.fromRGB(0, 0, 0)
Background.BorderSizePixel = 0
Background.Size = UDim2.new(1, 0, 1, 0)
Background.Image = "rbxassetid://7142136429"
Background.ImageTransparency = 0.500
Background.ScaleType = Enum.ScaleType.Tile
Background.TileSize = UDim2.new(0, 10, 0, 10)
monitors.QuotaControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.QuotaFrame.EnergyProgressFrame:Destroy()

local outputtext = workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.OutputLabel:Clone()
outputtext.Parent = workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame
workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.OutputLabel:Destroy()
local quotatext = game.Workspace.Monitors.QuotaControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.QuotaFrame.PowerLabel
quotatext.Name = "text of quota"
outputtext.Name = "output of text"


corefolder.Parent = game.ReplicatedStorage
values.Parent = corefolder
local netoutput = Instance.new("NumberValue")
netoutput.Parent = values

local MainScreen_emergency_mode_ui = workspace.Monitors.MainControlRoomMonitor.Screen.Meltdown["E.MODE"]
local ThermalScreen_emergency_mode_ui = workspace.Monitors.ThermalControlRoomMonitor.Screen.Meltdown["E.MODE"]
local CBLScreen_emergency_mode_ui = workspace.Monitors.PowerControlRoomMonitor.Screen.Meltdown["E.MODE"]

local EMERGENCY_MODE = false

--<< THE EMERGENCY MODE UI HANDLER
local flux = 0

workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.TempLabel.Changed:Connect(function()
	local temp_text = workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.TempLabel.Text
	local temp_num = tonumber(string.split(temp_text," ")[1])
	if temp_num==nil then temp_num=1 end
	cur_temp=temp_num
	--flux
	MainScreen_emergency_mode_ui.ShutdownTimer.Frame.flux.Text=workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.FluctuationLabel.Text

	--temp
	local frame = monitors.MainControlRoomMonitor.Screen.Meltdown["E.MODE"].ShutdownTimer.Frame.Scale
	frame.Temp.Text = temp_text

	local min = 23500
	local max = 31500

	local alpha = math.clamp((temp_num - min) / (max - min), 0, 0.894)
	frame.Size = UDim2.new(alpha, 0, 0.08, 0)

	--chamber pressure
	MainScreen_emergency_mode_ui.ShutdownTimer.Frame.psi.Text=workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.PressureLabel.Text

	--hdef
	MainScreen_emergency_mode_ui.ShutdownTimer.Frame.hdef_integ.Text=workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ReadingsFrame.HDEFLabel.Text
end)

--the meltdown ui thingy disappears when rip mainframe fully or quota reached and core shutdown (to prevent overlapping shi)
game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.ErrorFrame.Changed:Connect(function()
	local visibility = game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.ErrorFrame.Visible
	if visibility then
		MainScreen_emergency_mode_ui.Parent.Enabled=false
		ThermalScreen_emergency_mode_ui.Parent.Enabled=false
		CBLScreen_emergency_mode_ui.Parent.Enabled=false
	elseif not visibility and EMERGENCY_MODE then
		MainScreen_emergency_mode_ui.Parent.Enabled=true
		ThermalScreen_emergency_mode_ui.Parent.Enabled=true
		CBLScreen_emergency_mode_ui.Parent.Enabled=true
	end
end)
game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.ShutdownFrame.Changed:Connect(function()
	local visibility = game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI.ShutdownFrame.Visible
	if visibility then
		MainScreen_emergency_mode_ui.Parent.Enabled=false
		ThermalScreen_emergency_mode_ui.Parent.Enabled=false
		CBLScreen_emergency_mode_ui.Parent.Enabled=false
	elseif not visibility and EMERGENCY_MODE then
		MainScreen_emergency_mode_ui.Parent.Enabled=true
		ThermalScreen_emergency_mode_ui.Parent.Enabled=true
		CBLScreen_emergency_mode_ui.Parent.Enabled=true
	end
end)

--fake efe and etc

function detectchangeofgamestate()
if getgenv().alreadyreplaced then
  print("i tried to replace an led and soundblock that was already replaced. Luckily i aborted the process before i did!!!!")
  return false
else
if alreadydone == true then return end
if coreinfo.GameActive.Value == true then
readysound.Parent = game.Workspace.Consoles.MainReactorConsole.SoundBlock
leverLED.Parent = game.Workspace.Consoles.MainReactorConsole
game.Workspace.Consoles.MainReactorConsole.SoundBlock.ReadySound:Destroy()
game.Workspace.Consoles.MainReactorConsole.SwitchNeon:Destroy()
end
getgenv().alreadyreplaced=true
alreadydone = true
end
end

function monitor(Speed, AvoidCompanyLogo, ScreenAtEnd,Monitor)
	task.spawn(function()
		local Screen = Monitor.Screen
		local UI = Screen.MonitorUI
		local BootFrame = UI:FindFirstChild "BootFrame"
		if BootFrame then
			game.TweenService:Create(
				BootFrame.DiagnosticFrame,
				TweenInfo.new(Speed * .35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
				{Size = UDim2.new(0.5, -100, 1, -50)}
			):Play()
			game.TweenService:Create(
				BootFrame.LogFrame,
				TweenInfo.new(Speed * .35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
				{Size = UDim2.new(0.6, -100, 1, -50)}
			):Play()
			BootFrame.DiagnosticFrame.UIStroke.Transparency = 0
			BootFrame.DiagnosticFrame.BorderFrame.UIStroke.Transparency = 0
			BootFrame.DiagnosticFrame.ScrollingFrame.BackgroundTransparency = 0
			BootFrame.DiagnosticFrame.TitleText.BackgroundTransparency = 0
			BootFrame.DiagnosticFrame.TitleText.Text.TextTransparency = 0
			BootFrame.DiagnosticFrame.TitleText.Text.ImageLabel1.ImageTransparency = 0
			BootFrame.DiagnosticFrame.TitleText.Text.ImageLabel2.ImageTransparency = 0
			BootFrame.LogFrame.UIStroke.Transparency = 0
			BootFrame.LogFrame.BorderFrame.UIStroke.Transparency = 0
			BootFrame.LogFrame.TitleText.BackgroundTransparency = 0
			BootFrame.LogFrame.TitleText.Text.TextTransparency = 0
			BootFrame.LogFrame.TitleText.Text.ImageLabel1.ImageTransparency = 0
			BootFrame.LogFrame.TitleText.Text.ImageLabel2.ImageTransparency = 0
			BootFrame.LogFrame.TitleText1.TextTransparency = 0
			BootFrame.LogFrame.TitleText2.TextTransparency = 0
			BootFrame.LogFrame.TitleText3.TextTransparency = 0
			BootFrame.LogFrame.TitleText4.TextTransparency = 0
			BootFrame.LogFrame.TitleText5.TextTransparency = 0
			BootFrame.LogFrame.TitleText6.TextTransparency = 0
			task.spawn(function() --WHY
				BootFrame.LogFrame.TitleText1.Visible = true
				task.wait(Speed * .8)
				BootFrame.LogFrame.TitleText2.Visible = true
				task.wait(Speed * 1.2)
				BootFrame.LogFrame.TitleText3.Visible = true
				task.wait(Speed * 0.9)
				BootFrame.LogFrame.TitleText4.Visible = true
				task.wait(Speed * .9)
				BootFrame.LogFrame.TitleText5.Visible = true
				task.wait(Speed * 1.1)
				BootFrame.LogFrame.TitleText6.Visible = true
			end)
			local ScrollingFrame: ScrollingFrame = BootFrame.DiagnosticFrame.ScrollingFrame
			for i = 1, 45 do
				ScrollingFrame['TextLabel' .. i].TextTransparency = 0
				ScrollingFrame['TextLabel' .. i].Visible = true
				ScrollingFrame.CanvasPosition = Vector2.new(0, ScrollingFrame.AbsoluteCanvasSize.Y - ScrollingFrame.AbsoluteWindowSize.Y)
				if i > 40 then
					task.wait(Speed * 0.5)
				else
					task.wait(Speed * 0.085)
				end
			end
			task.wait(1)
			game.TweenService:Create(
				BootFrame.DiagnosticFrame,
				TweenInfo.new(Speed * .5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
				{Size = UDim2.new(0.5, 0, 1, 0)}
			):Play()
			game.TweenService:Create(
				BootFrame.LogFrame,
				TweenInfo.new(Speed * .5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
				{Size = UDim2.new(0.6, 40, 1, 0)}
			):Play()
			for _, Obj in BootFrame:GetDescendants() do
				if Obj:IsA("TextLabel") then
					game.TweenService:Create(Obj, TweenInfo.new(Speed * .5), {TextTransparency = 1}):Play()
				elseif Obj:IsA('Frame') or Obj:IsA('ScrollingFrame') then
					game.TweenService:Create(Obj, TweenInfo.new(Speed * .5), {BackgroundTransparency = 1}):Play()
				elseif Obj:IsA('ImageLabel') then
					game.TweenService:Create(Obj, TweenInfo.new(Speed * .5), {ImageTransparency = 1}):Play()
				elseif Obj:IsA('UIStroke') then
					game.TweenService:Create(Obj, TweenInfo.new(Speed * .5), {Transparency = 1}):Play()
				end
			end
			for i = 1, 45 do
				ScrollingFrame['TextLabel' .. i].Visible = false
				ScrollingFrame.CanvasPosition = Vector2.zero
			end
			workspace.SoundBlocks.ControlRoomSound.ControlRoomBootUp:Stop()
			task.wait(Speed * 2) --the screen is supposed to go black for a bit of time
			if not AvoidCompanyLogo then
				BootFrame.CompanyLogo.Visible = true
				BootFrame.CompanyLogo.Size = UDim2.fromScale(.75, .75)
				BootFrame.CompanyLogo.Position = UDim2.fromScale(.5, .5)
				game.TweenService:Create(BootFrame.CompanyLogo, TweenInfo.new(Speed * .3), {ImageTransparency = 0})
				task.wait(Speed * .3)
				workspace.SoundBlocks.ControlRoomSound.MonitorChime:Play()
				game.TweenService:Create(
					BootFrame.CompanyLogo,
					TweenInfo.new(Speed * .3, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
					{Size = UDim2.fromScale(.55, .55)}
				)
				task.wait(Speed * .3)
				game.TweenService:Create(
					BootFrame.CompanyLogo,
					TweenInfo.new(Speed * 1, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
					{Rotation = 0, Position = UDim2.fromScale(0.2, 0.5)}
				)
				task.wait(Speed * .3)
				game.TweenService:Create(
					BootFrame.BottomCompanyText,
					TweenInfo.new(Speed * 1),
					{TextTransparency = 0}
				)
				game.TweenService:Create(
					BootFrame.TopCompanyText,
					TweenInfo.new(Speed * 1),
					{TextTransparency = 0}
				)
				task.wait(Speed * 3.5)
				game.TweenService:Create(
					BootFrame.CompanyLogo,
					TweenInfo.new(Speed * .7, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
					{ImageTransparency = 1}
				)
				game.TweenService:Create(
					BootFrame.BottomCompanyText,
					TweenInfo.new(Speed * .7, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
					{TextTransparency = 1}
				)
				game.TweenService:Create(
					BootFrame.TopCompanyText,
					TweenInfo.new(Speed * .7, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
					{TextTransparency = 1}
				)
				task.wait(Speed * .9)
			end
		else
			UI.BootIcon.ImageTransparency = 0
			UI.BootIcon.TextLabel.TextTransparency = 0
			UI.BootIcon.UIStroke.Transparency = 0
			task.wait(not AvoidCompanyLogo and Speed * 11 or Speed * 10)
			game.TweenService:Create(
				UI.BootIcon.UIStroke,
				TweenInfo.new(Speed * .3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
				{Transparency = 1}
			):Play()
			game.TweenService:Create(
				UI.BootIcon,
				TweenInfo.new(Speed * .3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
				{ImageTransparency = 1, Size = UDim2.fromOffset(360, 360)}
			):Play()
			game.TweenService:Create(
				UI.BootIcon.TextLabel,
				TweenInfo.new(Speed * .3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
				{TextTransparency = 1}
			):Play()
			task.wait(not AvoidCompanyLogo and Speed * 1.74 or 0)
		end
	end)
end


function OppositeShockwave()
	local clone = workspace.Core.ForcefieldShockwave:Clone()
	clone.Parent=workspace
	clone.Size=Vector3.new(120,120,120)
	game.TweenService:Create(clone,TweenInfo.new(1.3,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Transparency=-1}):Play()
	game.TweenService:Create(clone,TweenInfo.new(1,Enum.EasingStyle.Sine,Enum.EasingDirection.In),{Size=Vector3.new(4,4,4)}):Play()
	game.Debris:AddItem(clone,5)
end

function SelectRandom(model:Model)
	local _2chosefrom = 0
	for i,v:Part in pairs(model:GetChildren()) do
		if v.Name:match("PW") and v.Name:match("ClickPart") then
			_2chosefrom+=1
		end
	end
	return model:FindFirstChild("PW"..math.random(1,_2chosefrom).."ClickPart"):FindFirstChildOfClass("ClickDetector")
end

function BoomEffect()
	local clone = workspace.Core.ForcefieldShockwave:Clone()
	clone.Parent=workspace
	clone.Size=Vector3.new(0,0,0)
	clone.Transparency=-5
	game.TweenService:Create(clone,TweenInfo.new(.2,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Size=Vector3.new(400,400,400)}):Play()
	game.TweenService:Create(game.Lighting,TweenInfo.new(.2,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{ExposureCompensation=15}):Play()
	task.delay(.4,function()
		game.TweenService:Create(game.Lighting,TweenInfo.new(5,Enum.EasingStyle.Linear,Enum.EasingDirection.InOut),{ExposureCompensation=0}):Play()
	end)

	game.Debris:AddItem(clone,1)
end

function EFE()
	local regulatedtemp_time = 0 --time where temp was in the 27000-29000 zone
	local totaltime = 150 --how much time u got to maintain temp in specifix range
	local warntime=10
	soundblocks.ControlRoomSound.EFEAlarm:Play()
	workspace.Core.CORE.Effects.EFEParticle1.Enabled=true
	workspace.Core.CORE.Effects.EFEParticle2.Enabled=true
	--workspace.Core.CORE.Effects.EFEParticle3.Enabled=true
	for i,v in pairs(monitors:GetChildren()) do
		if v:FindFirstChild("EFEFrame",true) then
			v:FindFirstChild("EFEFrame",true).Visible=true
			v:FindFirstChild("EFESurfaceLight",true).Enabled=true
			local keep = true
			local colorchange = task.spawn(function()
				while keep do
					for i,v in pairs(v:FindFirstChild("EFEFrame",true):GetChildren()) do
						v.BorderColor3=Color3.new(0,0,0)
						v.BackgroundColor3=Color3.new(1,1,0)

						v.TextLabel.TextColor3=Color3.new(0,0,0)
					end
					task.wait(.5)
					for i,v in pairs(v:FindFirstChild("EFEFrame",true):GetChildren()) do
						v.BorderColor3=Color3.new(1,1,0)
						v.BackgroundColor3=Color3.new(0,0,0)

						v.TextLabel.TextColor3=Color3.new(1,1,0)
					end
					task.wait(.5)
				end
			end)
			task.delay(warntime,function()
				keep=false
				colorchange=nil
				v:FindFirstChild("EFEFrame",true).Visible=false
				v:FindFirstChild("EFESurfaceLight",true).Enabled=false
			end)
		end
	end
	task.wait(warntime)
	soundblocks.ControlRoomSound.EFEAlarm:Stop()
	task.wait(2)
	task.spawn(function()
		for i=1,10 do
			OppositeShockwave()
			task.wait(0.8)
		end
	end)
	workspace.Core.CORE.Effects.EFEParticle1.Enabled=false
	workspace.Core.CORE.Effects.EFEParticle2.Enabled=false
	workspace.Core.EFEParticlePart.OuterParticles.Enabled=true
	workspace.Core.CORE.Effects.EFEParticle3.Enabled=true
	firesignal(game.ReplicatedStorage.CameraShakeEvent.OnClientEvent,0, 0, 0.8, 4, 0, 0)
	workspace.Core.CORE.EFESoundStart:Play()
	task.wait(5)
	workspace.Core.EFEParticlePart.OuterParticles.Enabled=false
	workspace.Core.CORE.Effects.EFEParticle3.Enabled=false
	task.wait(5.5)
	efe2multiplier = 3000
	workspace.Core.CORE.Boom.Volume=2
	workspace.Core.CORE.Boom:Play()
	BoomEffect()
	firesignal(game.ReplicatedStorage.CameraShakeEvent.OnClientEvent,0, 0, 0.9, 2, 0, 0)
	task.wait(.1)
	local thatsSHOCKING = true
	task.spawn(function()
		while thatsSHOCKING do
			task.wait(tonumber("0."..math.random(0,4)))
			--COOLANT SHENANIGANS
			for i=1,3 do
				fireclickdetector(SelectRandom(game.Workspace.Consoles.ThermalConsole["CoolantControl"..i]))
				if math.random(1,2)==2 then
					fireclickdetector(game.Workspace.Consoles.ThermalConsole["CoolantControl"..i].OnButton.ClickPart:FindFirstChildOfClass("ClickDetector"))
				else
					fireclickdetector(game.Workspace.Consoles.ThermalConsole["CoolantControl"..i].OffButton.ClickPart:FindFirstChildOfClass("ClickDetector"))
				end
			end
			--CBL
			for i=1,3 do
				fireclickdetector(SelectRandom(game.Workspace.Consoles.CBLaserConsole["CBL"..i.."Systems"]))
			end
			--PEA (im sure ur gonna ENJOY the debt)
			fireclickdetector(SelectRandom(game.Workspace.Consoles.ElectricGridConsole.ExtractionLever))
		end
	end)
	soundblocks.ControlRoomSound.ou_shi_electricity_go_brrrr:Play()
	for i,v in pairs(controls:GetDescendants()) do
		if v.Name=="EquinoxLightning" and v:IsA("ParticleEmitter") then
			v.Enabled=true
		end
	end
	task.wait(.5)
	firesignal(game.ReplicatedStorage.CameraShakeEvent.OnClientEvent,0, 0, 0.8, 4, 0, 0)
	for i,v in pairs(workspace.DebrisEffects:GetDescendants()) do
		if v:IsA("ParticleEmitter") then
			v:Emit(50)
		end
	end
	for i,v in pairs(monitors:GetChildren()) do
		if v:FindFirstChild("MainMonitorFrame",true) then
			v:FindFirstChild("MainMonitorFrame",true).Visible=false
		end
	end
	for i,v in pairs(workspace.Core.CORE.Effects:GetChildren()) do
		if v.Name:match("EFEParticle") or v.Name:match("ExplosionParticle") then
			v:Emit(167)
			v.Enabled=true
		end
	end
	task.delay(1.5,function()
		for i,v in pairs(workspace.Core.CORE.Effects:GetChildren()) do
			if v.Name:match("EFEParticle") or v.Name:match("ExplosionParticle") then
				v.Enabled=false
			end
		end
	end)
	task.wait(7)
	monitor(1,true,false,monitors.MainControlRoomMonitor)
	monitor(1,true,false,monitors.PowerControlRoomMonitor)
	monitor(1,true,false,monitors.ThermalControlRoomMonitor)
	soundblocks.ControlRoomSound.ControlRoomBootUp:Play()
	task.delay(8.5,function()
		soundblocks.ControlRoomSound.ControlRoomBootUp:Stop()
	end)
	task.delay(11,function()
		thatsSHOCKING=false
		soundblocks.ControlRoomSound.ou_shi_electricity_go_brrrr:Stop()
		for i,v in pairs(controls:GetDescendants()) do
			if v.Name=="EquinoxLightning" and v:IsA("ParticleEmitter") then
				v.Enabled=false
			end
		end
	end)
	efe2multiplier = 1
	task.wait(9.5)
	--MAIN SCREEN
	EMERGENCY_MODE=true
	game.Workspace.Monitors.MainControlRoomMonitor.Screen.Meltdown.StartupUnused:Play()
	monitors.MainControlRoomMonitor.Screen.Meltdown.Enabled=true
	MainScreen_emergency_mode_ui.UIScale.Scale=1.5
	game.TweenService:Create(MainScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=0}):Play()
	game.TweenService:Create(MainScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1}):Play()

	--LASER SCREEN
	monitors.PowerControlRoomMonitor.Screen.Meltdown.Enabled=true
	CBLScreen_emergency_mode_ui.UIScale.Scale=1.5
	game.TweenService:Create(CBLScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=0}):Play()
	game.TweenService:Create(CBLScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1}):Play()

	--COOLANT SCREEN
	monitors.ThermalControlRoomMonitor.Screen.Meltdown.Enabled=true
	ThermalScreen_emergency_mode_ui.UIScale.Scale=1.5
	game.TweenService:Create(ThermalScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=0}):Play()
	game.TweenService:Create(ThermalScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1}):Play()

	task.wait(2)
	--MAIN SCREEN
	MainScreen_emergency_mode_ui.ShutdownTimer.UIScale.Scale=1.5
	game.TweenService:Create(MainScreen_emergency_mode_ui.ShutdownTimer,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=0}):Play()
	game.TweenService:Create(MainScreen_emergency_mode_ui.ShutdownTimer.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1}):Play()

	--LASER SCREEN
	CBLScreen_emergency_mode_ui.Alert.UIScale.Scale=1.5
	game.TweenService:Create(CBLScreen_emergency_mode_ui.Alert,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=0}):Play()
	game.TweenService:Create(CBLScreen_emergency_mode_ui.Alert.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1}):Play()

	--COOLANT SCREEN
	ThermalScreen_emergency_mode_ui.Alert.UIScale.Scale=1.5
	game.TweenService:Create(ThermalScreen_emergency_mode_ui.Alert,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=0}):Play()
	game.TweenService:Create(ThermalScreen_emergency_mode_ui.Alert.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1}):Play()

	local brokie = true
	task.spawn(function()
		while brokie do
			task.wait(math.random(1,15)) --buff cuz it does too little and should be a bit more chaotic, prob will force to get a second guy.
			local rnd = math.random(1,3)

			if rnd==1 then
				--COOLANT SHENANIGANS
				local idk_randomm = math.random(1,2)
				if idk_randomm==1 then
					for i=1,3 do
						fireclickdetector(SelectRandom(game.Workspace.Consoles.ThermalConsole["CoolantControl"..i]))
						if math.random(1,2)==2 then
							fireclickdetector(game.Workspace.Consoles.ThermalConsole["CoolantControl"..i].OnButton.ClickPart:FindFirstChildOfClass("ClickDetector"))
						else
							fireclickdetector(game.Workspace.Consoles.ThermalConsole["CoolantControl"..i].OffButton.ClickPart:FindFirstChildOfClass("ClickDetector"))
						end
					end
				else
					fireclickdetector(SelectRandom(game.Workspace.Consoles.ThermalConsole["CoolantControl"..math.random(1,3)]))
					fireclickdetector(game.Workspace.Consoles.ThermalConsole["CoolantControl"..math.random(1,3)].OnButton.ClickPart:FindFirstChildOfClass("ClickDetector"))
					fireclickdetector(game.Workspace.Consoles.ThermalConsole["CoolantControl"..math.random(1,3)].OffButton.ClickPart:FindFirstChildOfClass("ClickDetector"))
				end
			elseif rnd==2 then
				--CBL
				local idk_randomm = math.random(1,3)
				if idk_randomm==1 or idk_randomm==2 then
					fireclickdetector(SelectRandom(game.Workspace.Consoles.CBLaserConsole["CBL"..math.random(1,3).."Systems"]))
				else
					for i=1,3 do
						fireclickdetector(SelectRandom(game.Workspace.Consoles.CBLaserConsole["CBL"..i.."Systems"]))
					end
				end
			elseif rnd==3 then
				--PEA (im sure ur gonna ENJOY the debt)
				fireclickdetector(SelectRandom(game.Workspace.Consoles.ElectricGridConsole.ExtractionLever))
			end
		end
	end)

	local miniquota_met = false
	local time = totaltime
	local required_reg_time = totaltime*0.6
	MainScreen_emergency_mode_ui.Parent.Countdown:Play()
	for i=1,totaltime do
		local mins = math.floor(time/60)
		local seconds = (time-60*mins)<10 and tostring("0"..time-60*mins) or tostring(time-60*mins)

		MainScreen_emergency_mode_ui.ShutdownTimer.Frame.Time.Time.Text=string.format("%s:%0s",mins,seconds)
		MainScreen_emergency_mode_ui.ShutdownTimer.Frame.Time.Scale.Time.Text=string.format("%s:%0s",mins,seconds)
		local alpha = math.clamp(time / totaltime, 0, 0.994)
		MainScreen_emergency_mode_ui.ShutdownTimer.Frame.Time.Scale.Size = UDim2.new(alpha, 0, 0.8, 0)

		if cur_temp>27000 and cur_temp<29000 then
			regulatedtemp_time+=1
		end

		time-=1
		task.wait(1)
		if regulatedtemp_time>=required_reg_time then
			miniquota_met=true
			break
		end
	end
	MainScreen_emergency_mode_ui.Parent.Countdown:Stop()
	if miniquota_met then
		MainScreen_emergency_mode_ui.ShutdownTimer.Frame.RegulatedTempQuotaMet.Visible=true
		brokie=false
		task.wait(5)
		--MAIN SCREEN
		game.TweenService:Create(MainScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=1}):Play()
		game.TweenService:Create(MainScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1.5}):Play()

		--LASER SCREEN
		game.TweenService:Create(CBLScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=1}):Play()
		game.TweenService:Create(CBLScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1.5}):Play()

		--COOLANT SCREEN
		game.TweenService:Create(ThermalScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=1}):Play()
		game.TweenService:Create(ThermalScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1.5}):Play()
		task.wait(3)
		MainScreen_emergency_mode_ui.Parent.Enabled=false
		CBLScreen_emergency_mode_ui.Parent.Enabled=false
		ThermalScreen_emergency_mode_ui.Parent.Enabled=false
		EMERGENCY_MODE=false
		task.wait(6)
		monitor(1,true,false,monitors.MainControlRoomMonitor)
		monitor(1,true,false,monitors.PowerControlRoomMonitor)
		monitor(1,true,false,monitors.ThermalControlRoomMonitor)
		soundblocks.ControlRoomSound.ControlRoomBootUp:Play()
		task.delay(8.5,function()
			soundblocks.ControlRoomSound.ControlRoomBootUp:Stop()
		end)
		for i,v in pairs(monitors:GetChildren()) do
			if v:FindFirstChild("BootIcon",true) then
				v:FindFirstChild("BootIcon",true).Visible=true
				v:FindFirstChild("BootIcon",true).ImageLabel.ImageTransparency=0
				v:FindFirstChild("BootIcon",true).TextLabel.TextTransparency=0
				v:FindFirstChild("BootIcon",true).UIStroke.Transparency=0
			end
		end
		task.wait(9.5)
		for i,v in pairs(monitors:GetChildren()) do
			if v:FindFirstChild("MainMonitorFrame",true) then
				v:FindFirstChild("MainMonitorFrame",true).Visible=true
			end
		end
		for i,v in pairs(monitors:GetChildren()) do
			if v:FindFirstChild("BootIcon",true) then
				v:FindFirstChild("BootIcon",true).Visible=false
				v:FindFirstChild("BootIcon",true).ImageLabel.ImageTransparency=1
				v:FindFirstChild("BootIcon",true).TextLabel.TextTransparency=1
				v:FindFirstChild("BootIcon",true).UIStroke.Transparency=1
			end
		end
	else
		MainScreen_emergency_mode_ui.ShutdownTimer.Frame.RegulatedTempQuotaMet.Visible=true
		MainScreen_emergency_mode_ui.ShutdownTimer.Frame.RegulatedTempQuotaMet.Status.Text="RESTABILIZATION FAILED. LOADING INTO MAIN OS"
		task.wait(5)
		--MAIN SCREEN
		game.TweenService:Create(MainScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=1}):Play()
		game.TweenService:Create(MainScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1.5}):Play()

		--LASER SCREEN
		game.TweenService:Create(CBLScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=1}):Play()
		game.TweenService:Create(CBLScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1.5}):Play()

		--COOLANT SCREEN
		game.TweenService:Create(ThermalScreen_emergency_mode_ui,TweenInfo.new(.35,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{GroupTransparency=1}):Play()
		game.TweenService:Create(ThermalScreen_emergency_mode_ui.UIScale,TweenInfo.new(.4,Enum.EasingStyle.Sine,Enum.EasingDirection.InOut),{Scale=1.5}):Play()
		task.wait(3)
		MainScreen_emergency_mode_ui.Parent.Enabled=false
		CBLScreen_emergency_mode_ui.Parent.Enabled=false
		ThermalScreen_emergency_mode_ui.Parent.Enabled=false
		EMERGENCY_MODE=false
		task.wait(6)
		monitor(1,true,false,monitors.MainControlRoomMonitor)
		monitor(1,true,false,monitors.PowerControlRoomMonitor)
		monitor(1,true,false,monitors.ThermalControlRoomMonitor)
		soundblocks.ControlRoomSound.ControlRoomBootUp:Play()
		task.delay(8.5,function()
			soundblocks.ControlRoomSound.ControlRoomBootUp:Stop()
		end)
		for i,v in pairs(monitors:GetChildren()) do
			if v:FindFirstChild("BootIcon",true) then
				v:FindFirstChild("BootIcon",true).Visible=true
				v:FindFirstChild("BootIcon",true).ImageLabel.ImageTransparency=0
				v:FindFirstChild("BootIcon",true).TextLabel.TextTransparency=0
				v:FindFirstChild("BootIcon",true).UIStroke.Transparency=0
			end
		end
		task.wait(9.5)
		for i,v in pairs(monitors:GetChildren()) do
			if v:FindFirstChild("MainMonitorFrame",true) then
				v:FindFirstChild("MainMonitorFrame",true).Visible=true
			end
		end
		for i,v in pairs(monitors:GetChildren()) do
			if v:FindFirstChild("BootIcon",true) then
				v:FindFirstChild("BootIcon",true).Visible=false
				v:FindFirstChild("BootIcon",true).ImageLabel.ImageTransparency=1
				v:FindFirstChild("BootIcon",true).TextLabel.TextTransparency=1
				v:FindFirstChild("BootIcon",true).UIStroke.Transparency=1
			end
		end
	end

end


function ForecastRead(timeslice:Frame)
	if timeslice:FindFirstChild("TimeLabel") and timeslice:FindFirstChild("Intensity") then
		if timeslice:FindFirstChild("Bar",true).ImageColor3~=Color3.fromRGB(0,255,255) then
			warn("found efe timezone.")
			return {Time=timeslice:FindFirstChild("TimeLabel").Text,isEFE=true}
		else
			return {Time=timeslice:FindFirstChild("TimeLabel").Text,isEFE=false}
		end
	end
	return nil
end

local EFE_Occurance = nil
local Occurance_4_2nd_EFE = nil
local Added_2nd_EFE = false
task.spawn(function ()
	repeat
		for i,v in pairs(monitors.ForecastControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.ScrollingFrame:GetChildren()) do
			if v:IsA('Frame') and ForecastRead(v) then
				local info = ForecastRead(v)
				local hour,mins = string.split(info.Time,":")[1],string.split(info.Time,":")[2]
				if not hour or not mins then return end
				if info.isEFE==true and EFE_Occurance==nil then
					EFE_Occurance=info.Time
					Occurance_4_2nd_EFE=hour~="06" and tostring(tonumber(hour)+2)..":00" or tostring(tonumber(hour)+1)..":20"
					print(Occurance_4_2nd_EFE)
				elseif Occurance_4_2nd_EFE and info.Time:match(Occurance_4_2nd_EFE) then
					v:FindFirstChild("Bar",true).ImageColor3=Color3.new(1,1,0)
					v:FindFirstChild("Bar",true).Size=UDim2.fromScale(1, 1)
					local copei = game.Workspace.Monitors.ForecastControlRoomMonitor.Screen.EFEPing:Clone()
					copei.Parent = game.Workspace.Monitors.ForecastControlRoomMonitor.Screen
					copei.TimePosition=0
					copei:Play()
					game.Debris:AddItem(copei,5)
					Added_2nd_EFE=true
				end
			end
		end
		task.wait(.1)
	until Added_2nd_EFE
	print("gosh ts so ahh")
end)

getgenv().EFE = EFE

monitors.QuotaControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.TimeFrame.TimeLabel:GetPropertyChangedSignal("Text"):Connect(function()
	local txt = monitors.QuotaControlRoomMonitor.Screen.MonitorUI.MainMonitorFrame.TimeFrame.TimeLabel.Text
	if Occurance_4_2nd_EFE and txt:match(Occurance_4_2nd_EFE) then
		EFE()
	end
end)

function leverdothing()
if leverisdoingthing == true then return end
task.spawn(function() --please no
while task.wait(1) do
if value > 18000 then leverisdoingthing = false break end
if currentlygenerated >= quota then
leverLED.Color = Color3.fromRGB(255, 255, 0)
readysound:Play()
task.wait(1)
leverLED.Color = Color3.fromRGB(0, 0, 0)
task.wait(1)
end
end
end)
end

function updatespecificthingies()
-- values

--qutoa of monitor
if quota >= 1000000000000000000 then
	quotatext.Text = quota / 1000000000000000000 .. " yeah"
elseif quota >= 1000000000000000 then
	quotatext.Text = quota / 1000000000000000 .. " PW"
elseif quota >= 1000000000000 then
	quotatext.Text = quota / 1000000000000 .. " TW"
elseif quota >= 1000000000 then
	quotatext.Text = quota / 1000000000 .. " GW"
elseif quota >= 1000000 then
	quotatext.Text = quota / 1000000 .. " MW"
elseif quota >= 1000 then
	quotatext.Text = quota / 1000 .. " kW"
else
	quotatext.Text = quota .. " W"
end

if currentlygenerated >= quota then
yeah.BackgroundColor3 = Color3.fromRGB(85, 170, 255)
leverdothing()
leverisdoingthing = true
else
yeah.Size = UDim2.new(currentlygenerated / quota,0, 1,0)
yeah.BackgroundColor3 = Color3.fromRGB(255, 255, 0)
end

if coreinfo.GameActive.Value == true then

local value = tonumber(tempval.Text:match("%d+"))

if not value then
	return
end

if value > 30000 then
	netoutput.Value = value * 1500000000 * efe2multiplier / 5999
elseif value > 18000 then
	netoutput.Value = value * 1500000000 * efe2multiplier / 7050
elseif value > 9000 then
	netoutput.Value = value * 1500000000 * efe2multiplier / 7495
end

currentlygenerated = currentlygenerated + netoutput.Value * (tonumber(peaLevel.Text:match("%d+")) or 0)/160
print(peaLevel.Text)
print(currentlygenerated)
print(yeah.Size)

-- monitor of main
outputtext.Text = math.floor(netoutput.Value / 10000000) .. " GW/H"
end
end

coreinfo.GameActive.Changed:Connect(function()
detectchangeofgamestate()
end)

print("script by totallybestnameever and papi192404!!!!")
print("script loaded with no errors successfully")
print('plz dont cry that sum stuff doesnt work the intended way cuz u have a shitty exploit')

while task.wait(1) do
updatespecificthingies()
end