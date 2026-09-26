--!nocheck
-- ============================================================
-- Reactor Data Logger v7.0
-- JSONL output, Wiki-calibrated formulas, full telemetry
-- Monitors: ReactorMonitor, ThermalMonitor, PowerMonitor, LogControlRoomMonitor
-- ============================================================
-- Changelog:
--   v6.1  - coolant lamp Color3 compare fix
--   v7.0  - JSONL output (reactor_telemetry.jsonl)
--         - Wiki formulas: AVB, E-VENT, CBL, P.E.A stress, Equinox, METU, Haden
--         - Gravatron wakes/charge/overload, METU cells, M.A.S.S. systems
--         - LogControlRoomMonitor.LogsFrame child monitoring
--         - CBL power level clickers (PW1-5), Shutdown lever, M.A.S.S. buttons
--         - CoreState thresholds: 5600/17500/29500/39000F
--         - Shift quotas: S1 524GW, S2 1.048TW, S3 3.001TW
-- ============================================================

local MainData        = game.Workspace.Stats
local SAMPLE_INTERVAL = 0.5
local LOG_FILE        = "reactor_telemetry.jsonl"
local isRecording     = true

local HttpService = game:GetService("HttpService")

-- Wiki-calibrated constants (from The Reactor Game Wiki)
local WIKI = {
	CORE_STATE_THRESHOLDS = {5600, 17500, 29500, 39000},
	AVB_PSI_DROP = 3300,
	AVB_COOLDOWN = 26,
	AVB_MAX_PSI = 5500,
	AVB_STALLOUT_PSI = 2200,
	EVENT_TEMP_DROP = 4000,
	EVENT_COOLDOWN = 26,
	CBL_LEVELS = 5,
	CBL_PER_LEVEL = 0.25,
	CBL_MAX_POWER = 1.25,
	SHIFT_QUOTAS = {524, 1048, 3001},
	PEA_STRESS_BASE = 0.08,
	PEA_STRESS_S3_BONUS = 0.01,
	MELTDOWN_TEMP_F = 38000,
	METU_FIRE_TEMP_F = 39000,
	METU_CLAMP_TEMP_F = 20000,
	GRAVATRON_CHARGE_TIME = 6,
	GRAVATRON_OVERLOAD_WINDOW = 1.5,
	GRAVATRON_FAILURE_THRESHOLD = 80,
	EQUI_NOX_TIME = 40,
	EQUI_NOX_MULTIPLIER = 3.0,
	HADEN_MELTDOWNS = 2,
}

local function getCoreState(tempF)
	local t = WIKI.CORE_STATE_THRESHOLDS
	if tempF >= t[4] then return 4
	elseif tempF >= t[3] then return 3
	elseif tempF >= t[2] then return 2
	elseif tempF >= t[1] then return 1
	else return 0 end
end

local function getShift()
	local qpu = MainData:FindFirstChild("ActiveQPUs")
	local v = qpu and qpu.Value or 0
	if v >= 3 then return 3 elseif v >= 2 then return 2 else return 1 end
end

local function writeLogJSON(obj)
	if not isRecording then return end
	local ts = os.date("%Y-%m-%d %H:%M:%S")
	local entry = HttpService:JSONEncode({timestamp = ts, data = obj})
	pcall(function()
		local existing = readfile(LOG_FILE) or ""
		writefile(LOG_FILE, existing .. entry .. "\n")
	end)
end

local function writeLogEvent(eventType, payload)
	writeLogJSON({type = eventType, payload = payload})
end

-- ============================================================
-- 1. Monitor discovery
-- ============================================================
local function findReactorMonitor()
	local mf = game.Workspace:FindFirstChild("MonitorsFacility")
	if not mf then
		warn("[Logger] MonitorsFacility not found")
		return nil
	end
	for _, dm in pairs(mf:GetChildren()) do
		if dm:IsA("Model") and dm.Name:find("DisplayMonitor") then
			local monitor = dm:FindFirstChild("Monitor")
			local screen  = monitor and monitor:FindFirstChild("Screen")
			local rm      = screen and screen:FindFirstChild("ReactorMonitoring")
			local frame   = rm and rm:FindFirstChild("MainMonitorFrame")
			if frame then
				print("[Logger] reactor monitor:", dm:GetFullName())
				return frame
			end
		end
	end
	warn("[Logger] ReactorMonitoring screen not found")
	return nil
end

local MonitorFrame = findReactorMonitor()
if not MonitorFrame then
	error("[Logger] cannot find reactor monitor, stopped.")
end

local ThermalConsole = game.Workspace.Consoles.ThermalConsole

local FanFrame, PowerMonitor, LogFrame
do
	local t = game.Workspace.Monitors:FindFirstChild("ThermalControlRoomMonitor")
	FanFrame = t and t.Screen.MonitorUI.MainMonitorFrame.FanFrame or nil

	local p = game.Workspace.Monitors:FindFirstChild("PowerControlRoomMonitor")
	PowerMonitor = p and p.Screen.MonitorUI.MainMonitorFrame or nil
end

local logRoom = game.Workspace.Monitors:FindFirstChild("LogControlRoomMonitor")
if logRoom then
	LogFrame = logRoom.Screen.MonitorUI.MainMonitorFrame:FindFirstChild("LogsFrame")
end

local knownLogChildren = {}
if LogFrame then
	for _, child in ipairs(LogFrame:GetChildren()) do
		knownLogChildren[child] = true
	end
end

-- ============================================================
-- 2. Logging (JSONL)
-- ============================================================
local function writeLogJSON(obj)
	if not isRecording then return end
	local ts = os.date("%Y-%m-%d %H:%M:%S")
	local entry = HttpService:JSONEncode({timestamp = ts, data = obj})
	pcall(function()
		local existing = readfile(LOG_FILE) or ""
		writefile(LOG_FILE, existing .. entry .. "\n")
	end)
end

local function writeLogEvent(eventType, payload)
	writeLogJSON({type = eventType, payload = payload})
end

-- ============================================================
-- 3. Parsing helpers
-- ============================================================
local function parseValue(label)
	if not label then return 0 end
	local text = label.Text or ""
	if text:find("ERR") or text == "" then return 0 end
	local num = text:match("([+-]?%d+%.?%d*)")
	return tonumber(num) or 0
end

local function parseFrom(parent, name)
	if not parent then return 0 end
	return parseValue(parent:FindFirstChild(name))
end

-- ============================================================
-- 4. Coolant level (v6.1 - fixed)
-- ============================================================
local ON_COLOR = Color3.fromRGB(240, 240, 240)

local function getCoolantLevel(pumpIndex)
	local pump = ThermalConsole:FindFirstChild("CoolantControl" .. pumpIndex)
	if not pump then return 0 end

	local lit = 0
	for i = 1, 3 do
		local light = pump:FindFirstChild("Light" .. i)
		local neon  = light and light:FindFirstChild("NeonPart")
		if neon and neon.Color == ON_COLOR then
			lit += 1
		end
	end
	return lit
end

local function cblPercentToLevel(percent, active)
	if not active or percent <= 0 then return 0 end
	local level = math.floor(percent / 25)
	return math.clamp(level, 1, 5)
end

-- ============================================================
-- 5. Stats snapshot (ValueObjects under Workspace.Stats)
-- ============================================================
local function snapshotStats()
	local snap = {}
	local function scan(inst, prefix)
		for _, d in ipairs(inst:GetChildren()) do
			local path = prefix .. d.Name
			if d:IsA("ValueBase") then
				snap[path] = d.Value
			end
			if #d:GetChildren() > 0 then
				scan(d, path .. ".")
			end
		end
	end
	scan(MainData, "")
	return snap
end

-- ============================================================
-- 6. Main sampling loop (JSONL output)
-- ============================================================
local lastSample = nil
local lastStats = nil

local function statsDiff(now, prev)
	if not prev then return "" end
	local changed = {}
	for k, v in pairs(now) do
		if prev[k] ~= v then
			changed[#changed + 1] = string.format("%s=%s", k, tostring(v))
		end
	end
	if #changed == 0 then return "" end
	return " | STATS d: " .. table.concat(changed, ", ")
end

task.spawn(function()
	while isRecording do
		local temp       = parseFrom(MonitorFrame, "TempLabel")
		local press      = parseFrom(MonitorFrame, "PressureLabel")
		local rad        = parseFrom(MonitorFrame, "RadiationLabel")
		local output     = parseFrom(MonitorFrame, "OutputLabel")
		local hdef       = parseFrom(MonitorFrame, "HDEFLabel")
		local stress     = parseFrom(MonitorFrame, "StressLabel")
		local fluct      = parseFrom(MonitorFrame, "FluctuationLabel")
		local peaExtract = parseFrom(MonitorFrame, "ExtractionLabel")

		-- CBL power readouts
		local cblPower = {0, 0, 0}
		if PowerMonitor then
			for i = 1, 3 do
				local frame = PowerMonitor:FindFirstChild("CBL" .. i .. "Frame")
				cblPower[i] = parseFrom(frame, "PowerLabel")
			end
		end

		-- CBL active flags from Stats
		local cblActive = {false, false, false}
		for i = 1, 3 do
			local cbl = MainData:FindFirstChild("CBL" .. i)
			local a = cbl and cbl:FindFirstChild("Active")
			cblActive[i] = a and a.Value or false
		end

		local cLevel = {getCoolantLevel(1), getCoolantLevel(2), getCoolantLevel(3)}

		-- Cooling fans
		local fanCount = 0
		if FanFrame then
			for i = 1, 6 do
				local f = FanFrame:FindFirstChild("FanFrame" .. i)
				local s = f and f:FindFirstChild("StatusLabel")
				if s and s.Text == "ON" then fanCount += 1 end
			end
		end

		local cblLevel = {
			cblPercentToLevel(cblPower[1], cblActive[1]),
			cblPercentToLevel(cblPower[2], cblActive[2]),
			cblPercentToLevel(cblPower[3], cblActive[3]),
		}
		local sumCBL     = cblLevel[1] + cblLevel[2] + cblLevel[3]
		local sumCoolant = cLevel[1] + cLevel[2] + cLevel[3]

		-- candidate model (still unverified - log both sides)
		local tickRatio = 0.5 / 2.5
		local predDT = (sumCBL * 65 - sumCoolant * 120) * tickRatio
		local predDP = (math.floor(temp / 50) - fanCount * 70) * tickRatio

		local actDT, actDP, actDOUT = 0, 0, 0
		if lastSample then
			actDT   = temp - lastSample.temp
			actDP   = press - lastSample.press
			actDOUT = output - lastSample.output
		end
		lastSample = {temp = temp, press = press, output = output}

		local statsNow = snapshotStats()
		local statsDelta = statsDiff(statsNow, lastStats)
		lastStats = statsNow

		-- Core state & shift
		local coreState = getCoreState(temp)
		local shift = getShift()
		local quota = WIKI.SHIFT_QUOTAS[shift] or 0
		local quotaPct = quota > 0 and (output / quota * 100) or 0

		-- P.E.A stress rate (wiki: 8% base + 1% in state 3 at max extract + no coolant)
		local peaStressRate = WIKI.PEA_STRESS_BASE
		if coreState >= 3 then peaStressRate += WIKI.PEA_STRESS_S3_BONUS end

		-- Build JSON payload
		local payload = {
			reactor = {
				tempF = temp,
				tempC = math.floor((temp - 32) * 5/9),
				pressure = press,
				radiation = rad,
				outputGW = output,
				hdef = hdef,
				stress = stress,
				fluctuation = fluct,
				peaExtraction = peaExtract,
				coreState = coreState,
				shift = shift,
				quotaGW = quota,
				quotaPct = math.floor(quotaPct * 100) / 100,
			},
			cbl = {
				power = cblPower,
				active = cblActive,
				level = cblLevel,
				sumLevel = sumCBL,
			},
			coolant = {
				levels = cLevel,
				sumLevel = sumCoolant,
			},
			fans = {count = fanCount, max = 6},
			predictions = {
				predDT = predDT,
				predDP = predDP,
				actDT = actDT,
				actDP = actDP,
				diffDT = actDT - predDT,
				diffDP = actDP - predDP,
			},
			actuals = {actDT = actDT, actDP = actDP, actDOUT = actDOUT},
			pea = {stressRate = peaStressRate},
			stats = statsNow,
			statsDelta = statsDelta ~= "" and statsDelta or nil,
			activeQPUs = (MainData:FindFirstChild("ActiveQPUs") and MainData.ActiveQPUs.Value or 0),
		}

		writeLogJSON({type = "tick", payload = payload})

		-- Check LogFrame for new children (log entries)
		if LogFrame then
			for _, child in ipairs(LogFrame:GetChildren()) do
				if not knownLogChildren[child] then
					knownLogChildren[child] = true
					local textLabel = child:FindFirstChild("TextLabel")
					if textLabel and textLabel.Text and textLabel.Text ~= "" then
						writeLogEvent("log_entry", {text = textLabel.Text})
					end
				end
			end
		end

		task.wait(SAMPLE_INTERVAL)
	end
end)

-- ============================================================
-- 7. Console click listeners (JSON events)
-- ============================================================
local function listenClick(obj, label, extra)
	if not obj then return end
	if obj:IsA("ClickDetector") then
		obj.MouseClick:Connect(function()
			writeLogEvent("click", {control = label, extra = extra})
		end)
	elseif obj:IsA("BasePart") then
		local cd = obj:FindFirstChildOfClass("ClickDetector")
		if cd then
			cd.MouseClick:Connect(function()
				writeLogEvent("click", {control = label, extra = extra})
			end)
		end
	end
end

-- Main Reactor Console
listenClick(game.Workspace.Consoles.MainReactorConsole.AtmosphereVentButton.ClickPart, "AVB")
for i = 1, 3 do
	listenClick(game.Workspace.Consoles.MainReactorConsole["E_VENTLever" .. i].ClickPart, "E-Vent" .. i)
	listenClick(game.Workspace.Consoles.ThermalConsole["CoolantControl" .. i].OnButton.ClickPart, "Coolant" .. i .. "-ON")
	listenClick(game.Workspace.Consoles.ThermalConsole["CoolantControl" .. i].OffButton.ClickPart, "Coolant" .. i .. "-OFF")
	listenClick(game.Workspace.Consoles.CBLaserConsole["CBL" .. i .. "Systems"].PressureButton.ClickPart, "CBL-Purge" .. i)
	-- CBL Power Level clickers (PW1-PW5)
	local cblSys = game.Workspace.Consoles.CBLaserConsole["CBL" .. i .. "Systems"]
	if cblSys then
		for j = 1, 5 do
			local btn = cblSys:FindFirstChild("PW" .. j .. "ClickPart")
			if btn then listenClick(btn, "CBL" .. i .. "-PW" .. j) end
		end
	end
end

-- Thermal Console fans
for i = 1, 6 do
	listenClick(game.Workspace.Consoles.ThermalConsole["CFLever" .. i].ClickPart, "Fan" .. i)
end

-- HDEF Generator
listenClick(game.Workspace.Consoles.HDEFGenerator.PowerLever.ClickPart, "HDEF-Power")

-- Startup lever (start)
listenClick(game.Workspace.Consoles.MainReactorConsole.StartUpBigLever.StartClickPart, "StartUpLever")

-- Startup lever (shutdown)
local shutdownPart = game.Workspace.Consoles.MainReactorConsole.StartUpBigLever:FindFirstChild("ShutClickPart")
if shutdownPart then listenClick(shutdownPart, "ShutdownLever") end

-- Alt Reactor Console: M.A.S.S. systems
local altConsole = game.Workspace.Consoles:FindFirstChild("ALTReactorConsole")
if altConsole then
	-- M.A.S.S. 1 & 2 activation + power levels
	for mass = 1, 2 do
		local massSys = altConsole:FindFirstChild("M.A.S.S " .. mass .. " SYSTEMS") or altConsole:FindFirstChild("MASS" .. mass .. "Systems")
		if massSys then
			local actBtn = massSys:FindFirstChild("ActivationButton") or massSys:FindFirstChild("ActivateButton")
			if actBtn then listenClick(actBtn.ClickPart or actBtn, "MASS" .. mass .. "-Activate") end
			-- Power level switch (min/max)
			local pwrSwitch = massSys:FindFirstChild("PowerLevelSwitch") or massSys:FindFirstChild("PowerSwitch")
			if pwrSwitch then listenClick(pwrSwitch.ClickPart or pwrSwitch, "MASS" .. mass .. "-Power") end
		end
	end
	-- Control room functions
	local ctrlRoom = altConsole:FindFirstChild("ControlRoomFunctions") or altConsole:FindFirstChild("ControlRoom")
	if ctrlRoom then
		local monBtn = ctrlRoom:FindFirstChild("MonitorBootButton")
		if monBtn then listenClick(monBtn.ClickPart or monBtn, "AltConsole-MonitorBoot") end
		local lightBtn = ctrlRoom:FindFirstChild("LightButton") or ctrlRoom:FindFirstChild("RoomLightButton")
		if lightBtn then listenClick(lightBtn.ClickPart or lightBtn, "AltConsole-Lights") end
		local shutterBtn = ctrlRoom:FindFirstChild("ShutterButton") or altConsole:FindFirstChild("ControlRoomShutters")
		if shutterBtn then listenClick(shutterBtn.ClickPart or shutterBtn, "AltConsole-Shutters") end
	end
end

-- Electric Grid Console: PEA extraction + Gravatron
local gridConsole = game.Workspace.Consoles:FindFirstChild("ElectricGridConsole")
if gridConsole then
	local peaSwitch = gridConsole:FindFirstChild("PEASwitch") or gridConsole:FindFirstChild("PowerExtractionSwitch")
	if peaSwitch then listenClick(peaSwitch.ClickPart or peaSwitch, "PEA-Extraction") end
	local gravBtn = gridConsole:FindFirstChild("GravatronButton") or gridConsole:FindFirstChild("GravatronOvercharge")
	if gravBtn then listenClick(gravBtn.ClickPart or gravBtn, "Gravatron-Overcharge") end
end

-- ============================================================
-- 8. Stop button
-- ============================================================
task.spawn(function()
	local player = game.Players.LocalPlayer or game.Players:WaitForChild("LocalPlayer")
	local gui = Instance.new("ScreenGui")
	gui.Name = "ReactorLoggerGui"
	gui.Parent = player:WaitForChild("PlayerGui")

	local btn = Instance.new("TextButton")
	btn.Size = UDim2.new(0, 150, 0, 38)
	btn.Position = UDim2.new(0.01, 0, 0.01, 0)
	btn.Text = "STOP LOGGING"
	btn.TextColor3 = Color3.new(1, 1, 1)
	btn.BackgroundColor3 = Color3.fromRGB(178, 26, 26)
	btn.Font = Enum.Font.GothamMedium
	btn.TextSize = 14
	btn.Parent = gui
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, 4)
	c.Parent = btn

	btn.MouseButton1Click:Connect(function()
		if not isRecording then return end
		isRecording = false
		pcall(function()
			local existing = readfile(LOG_FILE) or ""
			writefile(LOG_FILE, existing .. HttpService:JSONEncode({timestamp = os.date("%Y-%m-%d %H:%M:%S"), data = {type = "stop", payload = {message = "recording stopped"}}}) .. "\n")
		end)
		btn.Text = "STOPPED"
		btn.BackgroundColor3 = Color3.fromRGB(51, 153, 51)
		btn.Active = false
		task.delay(2, function() gui:Destroy() end)
	end)
end)

print("[Logger] v7.0 started -> " .. LOG_FILE)
