local TOKEN = '__TOKEN__'
if _G.__tok == TOKEN then return { dup = true } end
_G.__tok = TOKEN

-- One reading: the live clock, the gate string, and the reactor's own flags.
-- Whether the shift can start without input is decided by whether this clock
-- advances, so it is the thing to sample repeatedly from outside.
local out = { tok = TOKEN, t = os.time() }

local mon = workspace:FindFirstChild('Monitors')
  and workspace.Monitors:FindFirstChild('QuotaControlRoomMonitor')
local tf = mon and mon:FindFirstChild('Screen')
  and mon.Screen:FindFirstChild('MonitorUI')
  and mon.Screen.MonitorUI:FindFirstChild('MainMonitorFrame')
  and mon.Screen.MonitorUI.MainMonitorFrame:FindFirstChild('TimeFrame')
local tl = tf and tf:FindFirstChild('TimeLabel')
out.clock = tl and tl.Text or 'not found'

local P = game:GetService('Players')
out.players = #P:GetPlayers()
local pg = P.LocalPlayer:FindFirstChild('PlayerGui')
local sg = pg and pg:FindFirstChild('ScreenGui')
local wf = sg and sg:FindFirstChild('WaitFrame')
local pl = wf and wf:FindFirstChild('PlayerLabel')
out.wait = pl and pl.Text or '?'
out.intermissionVisible = sg and sg:FindFirstChild('IntermissionFrame') ~= nil
  and sg.IntermissionFrame.Visible

local S = workspace:FindFirstChild('Stats')
if S then
  local a, b = S:FindFirstChild('GameStart'), S:FindFirstChild('GameActive')
  out.start, out.active = a and a.Value, b and b.Value
  local tv = S:FindFirstChild('Core') and S.Core:FindFirstChild('TemperatureVal')
  out.temp = tv and tv.Value
end
return out
