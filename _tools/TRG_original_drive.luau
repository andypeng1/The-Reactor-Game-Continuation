--[[
TRG_original_drive.luau   (tag d9)

WHAT THIS IS
  A command-driven driver for the ORIGINAL game.  It lives in the same executor
  VM as the state recorder (TRG_original_state.luau) and does the one thing the
  recorder deliberately does not: it PRESSES things.

WHY A COMMAND FILE AND NOT A HOTKEY OR A HARD-CODED SEQUENCE
  Three reasons, each one already paid for in this project:

    * RightAlt / RightControl / RightShift are owned by the recorder, the
      watcher and the boot recorder; a fourth binding collides silently;
    * a hard-coded sequence is a sequence I cannot stop -- the shift it starts
      runs for tens of minutes and I would be blind for all of it;
    * a command file is a DURABLE record of what was asked.  The MCP worker is
      currently unregistered (zero mcp.lua fetches in the bridge log), so the
      only channel that survives is the filesystem -- and a file works whether
      or not a worker is up.

  So: I write <seq> <verb> <args> into trg_cmd.txt; this module executes every
  seq it has not executed before and appends the outcome to trg_drive_log.txt.
  seq is monotonic and the last one is persisted, so a re-inject does not replay
  old commands.

UNC DOES THE CLICK, AND WHICH PATH RAN IS LOGGED
  fireclickdetector() is the usual way.  If it is absent this module falls back
  to cd.MouseClick:Fire(player) -- which is what most implementations of
  fireclickdetector do anyway.  The log records WHICH one ran, because a silent
  fallback and the real thing must not look alike afterwards.  This matters
  more here than usual: a local MouseClick fires the CLIENT's listeners only,
  while the game's logic runs on the SERVER, so the two methods can differ in
  effect while looking identical in the code.  That is why every fire is
  followed by a state read -- see BELOW.

WHY TELEPORT BEFORE FIRING
  fireclickdetector calls the signal; it does not move the character.  Any
  distance check therefore still sees the real position, and a click fired from
  across the map is rejected with no error anywhere.  So 'fire' pivots the
  character next to the part first, waits, then fires.  Teleporting is visible
  in the world, so it is logged before it happens.

EVERY FIRE IS FOLLOWED BY A MEASUREMENT
  After each fire the driver reads all ValueBase objects under Workspace.Stats
  and logs either 'fire CHANGED ...' or 'fire NOCHANGE ...'.  NOCHANGE is a
  real result: it says the click did not reach whatever writes the state, and it
  is the reading that separates the two click methods above.

LIVENESS
  trg_drive_loop.txt is REWRITTEN every poll with one line.  Its mtime is the
  liveness proof, and it is deliberately a separate file from the log: a writer
  with a 30 s heartbeat is a flat line in any window shorter than 30 s, so
  'quiet' and 'dead' must not be read from the log alone.

LINE FORMAT
      [HH:MM:SS] <rel-s> <text>
  one line per event in trg_drive_log.txt.  The census is a separate file, one
  record per line: KIND | fullPath | parent | parentClass | pos | mad | label.
  These shapes are frozen; new content goes in a new line or a new file.

USAGE
  loadstring(readfile('TRG_original_drive.luau'))()      -- starts the poll loop
  then write commands into trg_cmd.txt from outside.
  Stop with a 'stop' command, or _G.TRG_DRIVE_AUTORUN = false before injecting.
  No Studio edit path is involved in deploying this file, but the backslash rule
  is kept anyway: this file contains ZERO backslashes, newlines are built from
  string.char(10) and CR from string.char(13).

WHAT d2 ADDS, AND WHY EACH ONE
  * ANTI-IDLE.  Roblox drops a client after about 20 minutes with no input, and
    nothing in d1 was input: PivotTo moves the avatar, but the idle timer
    watches the USER.  The failure mode is silence -- later commands are simply
    never executed -- so the loop now produces input on its own.
  * A GUI HALF.  d1's census found 1019 ClickDetectors and not one of them
    starts a shift.  A ClickDetector handler runs on the SERVER and a local fire
    cannot reach it; a GUI button's handler is always a client LocalScript, so
    pressing one from here runs real code and its remote does reach the server.
  * caps / read / probe / listen / cf.  d1 could only see 32 ValueBases, which
    is why six fires all read NOCHANGE and proved nothing: in a parked world no
    ValueBase is written, so the sensor could not separate 'inert' from
    'unreached'.  caps says which executor routes exist; probe says what the
    game's own panels say; listen says whether anything is ticking at all; cf
    gives the mechanical half of a click test (only LeverUnion moved).

WHAT d4 ADDS, AND WHY
  * A FOURTH PRESS ROUTE, AND ON THIS EXECUTOR THE ONLY ONE.  d2 pressed a
    SIGNAL (firesignal / sig:Fire / getconnections); caps then read back
    firesignal=nil and getconnections=nil in the live client, and the built-in
    signal has no :Fire, so all three routes are dead there and press reported
    'no route worked'.  A button is not only a signal -- it is also a RECTANGLE
    at a known screen position, and VirtualInputManager can click a rectangle.
    Same family as the anti-idle's VirtualUser path: in-game synthetic input,
    not the operator's cursor.
  * Every attempt is still a reading.  The mouse route NAMES why it did not
    fire -- 'SKIP hidden' / 'SKIP zero size' / 'ERR SendMouseButtonEvent' --
    because a click that lands on something else is otherwise the same shape as
    a press that did nothing.
-- ==== d7..d9 (2026-10-10) ====
-- Three changes, each answering a measured failure rather than a hunch.
--
-- (1) A THIRD fire route, 'vim'.  d1..d6 could only press a window signal or a
--     GUI rectangle, and a ClickDetector's handler runs on the SERVER, so
--     neither can reach it -- which is why every determinate 'fire' in the log
--     reads NOCHANGE while the same control works when a mouse really goes
--     there.  The recipe below is the one that actually lit this reactor
--     (Phase 106/107), reproduced, not re-derived.
--
-- (2) The 58 px lesson, applied as a PRIMITIVE rather than as arithmetic.  The
--     move takes viewport coordinates and the button event takes whatever
--     UIS:GetMouseLocation() reports back afterwards; those are two different
--     spaces and the read-back is what absorbs the difference.  clickScreen()
--     is now the only place this file clicks a pixel.
--
-- (3) A seq floor kept in MEMORY as well as on disk.  The executor's read of
--     its own state file lagged -- the file held 203 while loadSeq() returned
--     0 -- and runCmds, seeing last = 0, re-ran the entire file, straight
--     through the 'stop' that should have ended the session and on into the
--     session-ender press.  Memory cannot lag.  The file's real protection is
--     still that it holds only PENDING commands.
--
--     d8 and d9 are that same floor, tightened.  d8 moved it into memory at all;
--     d9 (this file) raises it on EVERY pass, not only on the pass that had work
--     to run.  The difference is the whole protection: a pass that found every
--     command already done used to leave the floor unset, and then the only thing
--     between a laggy disk read and the top of the file was the laggy read.  A
--     floor written only when work was done is not a floor, it is a note about the
--     last time work was done.  S7 and the M-NOWORK mutant keep that raise honest.
]]

local M = {}
M.TAG = 'd9'

local NL = string.char(10)
local CR = string.char(13)

-- ========== CONFIG ==========
local CFG = {
  -- ValueBases live here; resolved by NAME so a container rename elsewhere does
  -- not silently record nothing.  Same choice as the recorder, same reason.
  StatsName = 'Stats',

  CmdFile    = 'trg_cmd.txt',
  LogFile    = 'trg_drive_log.txt',
  CensusFile = 'trg_drive_census.txt',
  StateFile  = 'trg_drive_state.txt',
  LoopFile   = 'trg_drive_loop.txt',
  FatalFile  = 'trg_drive_FATAL.txt',

  -- Command poll period.  Fast enough to feel immediate, slow enough that a
  -- 1 s-append log is not mostly this.
  Poll = 0.5,

  -- Stand this far to the side and this far above the part before firing.
  DefaultStuds = 4,
  RiseStuds = 3,

  -- Census gives up after this many descendants -- and a COUNT gives up on
  -- output, not on time.  300000 descendants IS the wedge, so it is this pair
  -- together that bounds the walk.  Same reason as ProbeMs.
  CensusCap = 300000,
  CensusMs  = 8000,

  -- Wait after firing before reading the state back.  Long enough for a server
  -- round trip, short enough that a shift's first second is still visible.
  SettleSeconds = 1.2,

  -- Anti-idle.  Roblox drops a client after about 20 minutes with no input, so
  -- this must stay well under that; 240 s leaves room for several missed ticks.
  IdleSeconds = 240,

  -- Fallback jiggle height, in studs.  Small on purpose: it exists to prove the
  -- character is alive, not to relocate it.
  IdleJiggle = 0.5,

  GuiFile     = 'trg_drive_gui.txt',
  GuiCap      = 400,
  ProbeCap    = 400,

  -- A COUNT budget does not bound TIME.  ProbeCap caps how many labels a probe
  -- KEEPS; the walk still visits every descendant either way.  Measured
  -- 2026-10-10: the same probe returned in 7 s at 01:16:47 and then, three and
  -- a half minutes later, a probe issued at 01:20:10 still had not returned
  -- thirteen minutes on.  Because one pass is one synchronous runCmds
  -- iteration, that did not merely delay the probe -- it held the whole
  -- command loop hostage, and trg_drive_loop.txt froze at 01:08:46 for the
  -- duration.  doListen already bounds itself by os.clock(); these must too.
  ProbeMs     = 4000,

  -- Substring that identifies the control-room monitor trees.  The 7 screens
  -- carry the game's own words about its own state.
  MonitorHint = 'ControlRoomMonitor',
}

local T0 = os.clock()

-- ========== SMALL HELPERS ==========
local function now()
  return os.date('%H:%M:%S')
end

local function rel()
  return string.format('%.1f', os.clock() - T0)
end

local function exists(p)
  local ok, r = pcall(isfile, p)
  return ok and r == true
end

local function read(p)
  if not exists(p) then return '' end
  local ok, r = pcall(readfile, p)
  if ok and type(r) == 'string' then return r end
  return ''
end

local function write(p, s)
  local ok, err = pcall(writefile, p, s)
  if not ok then return false, tostring(err) end
  return true
end

local function append(p, s)
  local ok, err = pcall(appendfile, p, s)
  if not ok then return false, tostring(err) end
  return true
end

local function log(text)
  append(CFG.LogFile, '[' .. now() .. '] ' .. rel() .. ' ' .. text .. NL)
end

-- Strip anything that would break the one-line-per-event shape.  The panel text
-- this project has already captured contains embedded newlines, so this is not
-- hypothetical.
local function flat(s)
  s = tostring(s)
  s = string.gsub(s, '[' .. CR .. NL .. ']+', ' ')
  s = string.gsub(s, '|', '/')
  return s
end

-- ========== PATH / GEOMETRY ==========
-- Paths come from GetFullName(), which is rooted at 'game' but does not print
-- it.  Walk segment by segment so a failure names the segment that failed --
-- 'missing' with no location is the reading that costs an hour.
local function resolve(path)
  if type(path) ~= 'string' or path == '' then return nil, 'empty path' end
  local segs = {}
  for s in string.gmatch(path, '[^%.]+') do segs[#segs + 1] = s end
  if #segs == 0 then return nil, 'no segments' end
  local node = game
  local i = 1
  if segs[1] == 'game' then i = 2 end
  for k = i, #segs do
    local nxt = node:FindFirstChild(segs[k])
    if nxt == nil then
      return nil, 'missing segment ' .. tostring(k) .. ' = ' .. segs[k] ..
        ' under ' .. node:GetFullName()
    end
    node = nxt
  end
  return node
end

local function worldPos(inst)
  if inst == nil then return nil end
  if inst:IsA('BasePart') then return inst.Position end
  if inst:IsA('Model') then
    local ok, cf = pcall(function() return inst:GetPivot() end)
    if ok and cf ~= nil then return cf.Position end
  end
  return nil
end

local function fmtPos(p)
  if p == nil then return '-' end
  return string.format('%.1f,%.1f,%.1f', p.X, p.Y, p.Z)
end

-- The label on a button is how a control gets identified by a human.  Bounded
-- depth on purpose: a Part's descendants can include a whole SurfaceGui tree.
local function labelUnder(inst, depth)
  if inst == nil or depth <= 0 then return nil end
  for _, c in ipairs(inst:GetChildren()) do
    local cn = c.ClassName
    if cn == 'TextLabel' or cn == 'TextButton' then
      local ok, t = pcall(function() return c.Text end)
      if ok and type(t) == 'string' and t ~= '' then return t end
    end
    local got = labelUnder(c, depth - 1)
    if got ~= nil then return got end
  end
  return nil
end

-- ========== STATE READBACK ==========
-- One line holding every ValueBase under Stats.  This is the driver's own
-- before/after, independent of the recorder, so a fire can be judged without
-- waiting for the recorder's next 30 s snapshot.
local function statline()
  local root = workspace:FindFirstChild(CFG.StatsName)
  if root == nil then return 'Stats missing' end
  local parts = {}
  for _, d in ipairs(root:GetDescendants()) do
    if d:IsA('ValueBase') then
      local ok, v = pcall(function() return d.Value end)
      -- 'ok and v or ERR' renders a FALSE BoolValue as ERR, so every genuinely
      -- false flag read as unreadable and the whole dump looked broken.  Render
      -- by type: only a real pcall failure says ERR.
      local shown
      if not ok then
        shown = 'ERR'
      elseif type(v) == 'boolean' then
        shown = tostring(v)
      else
        shown = flat(v)
      end
      parts[#parts + 1] = d.Name .. '=' .. shown
    end
  end
  parts[#parts + 1] = 'n=' .. tostring(#parts)
  return table.concat(parts, ' ')
end

local function localPlayer()
  return game:GetService('Players').LocalPlayer
end

local function charPos()
  local lp = localPlayer()
  local c = lp and lp.Character
  local hrp = c and c:FindFirstChild('HumanoidRootPart')
  if hrp == nil then return 'no character' end
  return fmtPos(hrp.Position)
end

local function teleportTo(pos, studs)
  local lp = localPlayer()
  local c = lp and lp.Character
  if c == nil then
    log('teleport FAIL no character')
    return false
  end
  local target = CFrame.new(pos + Vector3.new(studs, CFG.RiseStuds, 0))
  log('teleport ' .. charPos() .. ' -> ' .. fmtPos(target.Position))
  local ok, err = pcall(function() c:PivotTo(target) end)
  if not ok then
    log('teleport ERROR ' .. flat(err))
    return false
  end
  task.wait(0.3)
  return true
end

-- ========== CENSUS ==========
-- Which things in this world can be pressed, where they are, and what they say
-- on themselves.  Run this BEFORE firing anything: the original game's control
-- names are not assumed here, they are read.
local function census()
  local t0 = os.clock()
  local out = {}
  out[#out + 1] = '# census at ' .. now() .. ' rel ' .. rel()
  out[#out + 1] = '# KIND | fullPath | parent | parentClass | pos | mad | label'
  local nCD, nPP, seen = 0, 0, 0
  local cut = nil
  local ok, all = pcall(function() return game:GetDescendants() end)
  if not ok then
    log('census ERROR GetDescendants ' .. flat(all))
    return 'census ERROR'
  end
  for _, d in ipairs(all) do
    seen = seen + 1
    if seen > CFG.CensusCap then cut = 'countcap' break end
    if os.clock() - t0 > CFG.CensusMs / 1000 then cut = 'timecap' break end
    local cn = d.ClassName
    if cn == 'ClickDetector' or cn == 'ProximityPrompt' then
      local p = d.Parent
      local mad = '-'
      if cn == 'ClickDetector' then
        local o, v = pcall(function() return d.MaxActivationDistance end)
        if o then mad = tostring(v) end
        nCD = nCD + 1
      else
        local o, v = pcall(function() return d.ActionText end)
        if o and v ~= nil then mad = tostring(v) end
        nPP = nPP + 1
      end
      local lab = labelUnder(p, 3)
      out[#out + 1] = cn .. ' | ' .. d:GetFullName() .. ' | ' ..
        (p and p.Name or '-') .. ' | ' .. (p and p.ClassName or '-') .. ' | ' ..
        fmtPos(worldPos(p)) .. ' | ' .. flat(mad) .. ' | ' .. flat(lab or '-')
    end
  end
  local head = '# done in ' .. string.format('%.2f', os.clock() - t0) ..
    's  descendants=' .. tostring(seen) ..
    '  ClickDetector=' .. tostring(nCD) ..
    '  ProximityPrompt=' .. tostring(nPP) ..
    '  stopped=' .. tostring(cut or 'end')
  out[#out + 1] = head
  write(CFG.CensusFile, table.concat(out, NL) .. NL)
  log(head)
  return head
end

-- ========== ACTIONS ==========
local function doLs(path)
  local node, err
  if path == nil or path == '' then
    node = game
  else
    node, err = resolve(path)
  end
  if node == nil then
    log('ls FAIL ' .. flat(err))
    return
  end
  local kids = node:GetChildren()
  local names = {}
  for i = 1, math.min(#kids, 60) do
    names[#names + 1] = kids[i].Name .. '(' .. kids[i].ClassName .. ')'
  end
  log('ls ' .. node:GetFullName() .. ' n=' .. tostring(#kids) ..
    ' :: ' .. table.concat(names, ' '))
end

-- One primitive for every press this file makes.  The argument is a GUESS in
-- the space the MOVE takes; the CLICK is given whatever point the engine
-- reports back afterwards.  Those are not the same space -- that difference is
-- the whole 58 px -- and the recipe that actually lit this reactor never
-- resolved it arithmetically: it moved, read GetMouseLocation(), and clicked at
-- THAT.  Reproduced, not re-derived.
local function clickScreen(gx, gy)
  local vim = game:GetService('VirtualInputManager')
  local uis = game:GetService('UserInputService')
  local okMove = pcall(function() vim:SendMouseMoveEvent(gx, gy, game) end)
  if not okMove then return nil, 'ERR SendMouseMoveEvent' end
  -- The queue is not instant: reading the location in the same call as the move
  -- gives the PREVIOUS position.  So: move, wait, then read.
  task.wait(0.35)
  local cur = nil
  local okRead = pcall(function() cur = uis:GetMouseLocation() end)
  if not okRead or cur == nil then return nil, 'ERR GetMouseLocation' end
  local x, y = math.floor(cur.X), math.floor(cur.Y)
  local okA = pcall(function() vim:SendMouseButtonEvent(x, y, 0, true, game, 0) end)
  task.wait(0.2)
  local okB = pcall(function() vim:SendMouseButtonEvent(x, y, 0, false, game, 0) end)
  if not okA or not okB then return nil, 'ERR SendMouseButtonEvent' end
  return 'mouse@' .. x .. ',' .. y
end

-- The 3D route, and the reason this file has one at all: a ClickDetector's
-- handler runs on the SERVER, so fireclickdetector -- which fires the
-- client-side signal -- cannot reach it.  Synthetic input at the point the
-- camera projects the ClickPart onto is the same family as the anti-idle's
-- VirtualUser path: in-game input, never the operator's cursor.
--
-- Every step that can silently do nothing is named in the returned string: the
-- screen point actually clicked, the hit distance against the detector's own
-- MaxActivationDistance, what the mouse is over, and how many times the
-- detector's own MouseClick fired (a LOCAL counter, so it reads 0 even when the
-- server acted -- judge by Workspace.Stats, not by this).
local function click3d(cp)
  local lp = localPlayer()
  if lp == nil then return nil, 'no local player' end
  local ch = lp.Character
  local hrp = ch and ch:FindFirstChild('HumanoidRootPart')
  if hrp == nil then return nil, 'no HumanoidRootPart' end
  local cam = workspace.CurrentCamera
  if cam == nil then return nil, 'no camera' end
  local cd = cp:FindFirstChildOfClass('ClickDetector')
  local t = cp.Position

  local wasType = cam.CameraType
  cam.CameraType = Enum.CameraType.Scriptable
  cam.CFrame = CFrame.lookAt(t + Vector3.new(0, 3, 5), t, Vector3.new(0, 0, 1))
  pcall(function() hrp.CFrame = CFrame.new(t + Vector3.new(0, 3.2, 5)) end)
  task.wait(CFG.SettleSeconds)

  -- The layer collectors must be OFF.  With a ScreenGui over the viewport the
  -- move lands on the overlay, mouse.Target is the overlay, and the symptom is
  -- NOTHING -- the same shape as a press that missed.  This is the one step of
  -- the boot chain the world itself cannot tell you about.
  local hidden = {}
  local pg = lp:FindFirstChildOfClass('PlayerGui')
  if pg ~= nil then
    for _, lc in ipairs(pg:GetDescendants()) do
      if lc:IsA('LayerCollector') then
        local okv, v = pcall(function() return lc.Enabled end)
        if okv and v == true then
          hidden[#hidden + 1] = lc
          pcall(function() lc.Enabled = false end)
        end
      end
    end
  end
  task.wait(0.3)

  local hits = 0
  local conn = nil
  if cd ~= nil then
    pcall(function() conn = cd.MouseClick:Connect(function() hits = hits + 1 end) end)
  end
  local pv = cam:WorldToViewportPoint(t)
  local how, err = clickScreen(pv.X, pv.Y)
  task.wait(0.6)

  local dist = (hrp.Position - t).Magnitude
  local maxd = 0
  if cd ~= nil then
    local okd, v = pcall(function() return cd.MaxActivationDistance end)
    if okd and v ~= nil then maxd = v end
  end
  local target = 'nil'
  local mouse = lp:GetMouse()
  if mouse ~= nil then
    local okt, tg = pcall(function() return mouse.Target end)
    if okt and tg ~= nil then target = tg.Name end
  end

  if conn ~= nil then pcall(function() conn:Disconnect() end) end
  for _, lc in ipairs(hidden) do pcall(function() lc.Enabled = true end) end
  cam.CameraType = wasType

  local note = (how or ('ERR ' .. tostring(err))) ..
    ' vp=' .. string.format('%.0f,%.0f', pv.X, pv.Y) ..
    ' d=' .. string.format('%.2f', dist) .. ' of ' .. string.format('%.1f', maxd) ..
    ' tgt=' .. target .. ' cdFired=' .. tostring(hits)
  if maxd > 0 and dist > maxd then note = note .. ' OUT-OF-RANGE' end
  return note
end

local function doFire(path, method, studs)
  local node, err = resolve(path)
  if node == nil then
    log('fire FAIL resolve :: ' .. flat(err))
    return
  end
  local cd = node
  if cd.ClassName ~= 'ClickDetector' then
    cd = node:FindFirstChildOfClass('ClickDetector')
  end
  if cd == nil then
    log('fire FAIL no ClickDetector under ' .. path)
    return
  end

  local n = tonumber(studs)
  if n == nil then n = CFG.DefaultStuds end
  if n > 0 then
    local pos = worldPos(cd.Parent)
    if pos ~= nil then teleportTo(pos, n) end
  end

  local lp = localPlayer()
  local before = statline()
  local how
  if method == 'vim' or method == 'world' then
    local res, e = click3d(cd.Parent)
    how = res ~= nil and ('vim ' .. res) or ('vim FAIL ' .. tostring(e))
  elseif method == 'signal' then
    local ok, e = pcall(function() cd.MouseClick:Fire(lp) end)
    how = ok and 'MouseClick:Fire' or ('MouseClick:Fire ERROR ' .. flat(e))
  else
    local f = fireclickdetector
    if type(f) == 'function' then
      local ok, e = pcall(f, cd)
      how = ok and 'fireclickdetector' or ('fireclickdetector ERROR ' .. flat(e))
    else
      local ok, e = pcall(function() cd.MouseClick:Fire(lp) end)
      how = ok and 'MouseClick:Fire (fireclickdetector ABSENT)'
        or ('MouseClick:Fire ERROR ' .. flat(e))
    end
  end
  log('fire ' .. cd:GetFullName() .. ' via ' .. how)

  task.wait(CFG.SettleSeconds)
  local after = statline()
  if after == before then
    log('fire NOCHANGE ' .. after)
  else
    log('fire CHANGED ' .. after)
  end
end

local function doFireAll(path)
  local node, err = resolve(path)
  if node == nil then
    log('fireall FAIL resolve :: ' .. flat(err))
    return
  end
  local n = 0
  for _, d in ipairs(node:GetDescendants()) do
    if d.ClassName == 'ClickDetector' then
      n = n + 1
      doFire(d:GetFullName(), 'auto', nil)
    end
  end
  log('fireall done under ' .. node:GetFullName() .. ' n=' .. tostring(n))
end

local function doNear(path, studs)
  local node, err = resolve(path)
  if node == nil then
    log('near FAIL ' .. flat(err))
    return
  end
  local pos = worldPos(node)
  if pos == nil then
    log('near FAIL no world position for ' .. path)
    return
  end
  teleportTo(pos, tonumber(studs) or CFG.DefaultStuds)
end

-- ========== ANTI-IDLE ==========
-- Roblox drops a client after about 20 minutes with no input.  Nothing in d1 was
-- input: PivotTo moves the avatar, but the idle timer watches the USER, so a
-- long shift would end with the session gone -- and the failure is silence, not
-- an error.  Later commands would simply never be executed.
--
-- Route 1 is the classic executor anti-idle, VirtualUser:CaptureController()
-- then ClickButton2().  That is IN-GAME virtual input; it never touches the
-- operator's real cursor.  Route 2, a small PivotTo, is the fallback.  Which one
-- ran is logged, for the same reason 'fire' logs which click path ran: a silent
-- fallback and the real thing must not look alike afterwards.
local lastInput = os.clock()

local function idleRoute()
  local ok, vu = pcall(function() return game:GetService('VirtualUser') end)
  if ok and vu ~= nil then
    local ok2 = pcall(function()
      vu:CaptureController()
      vu:ClickButton2(Vector2.new())
    end)
    if ok2 then return 'VirtualUser' end
  end
  local lp = localPlayer()
  local c = lp and lp.Character
  if c ~= nil then
    local ok3 = pcall(function()
      c:PivotTo(c:GetPivot() * CFrame.new(0, CFG.IdleJiggle, 0))
    end)
    if ok3 then return 'jiggle' end
  end
  return nil
end

-- force=true means 'do it now and say so' (the Idled hook and the 'idle' verb).
-- force=false is the periodic timer; it also logs, so 'the anti-idle is running'
-- is a reading rather than a hope.
local function antiIdle(force, why)
  if not force and os.clock() - lastInput < CFG.IdleSeconds then return end
  local how = idleRoute()
  lastInput = os.clock()
  -- 'why' names the caller.  The periodic timer and the Idled hook are
  -- different mechanisms that used to print the same line, and with the
  -- lines identical 'which one fired' is unreadable -- the same trap as a
  -- build whose TAG does not move.
  log('antiidle ' .. tostring(how) .. ' via ' ..
    tostring(why or (force and 'forced' or 'timer')) .. ' at rel ' .. rel())
end

-- ========== EXECUTOR CAPABILITIES ==========
-- Which routes this executor actually has.  d1 learned the hard way that
-- guessing costs a round trip: MouseClick:Fire died with 'Fire is not a valid
-- member of RBXScriptSignal', and that error names the signal, not the executor.
local function globalOf(n)
  local ok, g = pcall(function() return _G[n] end)
  if ok and g ~= nil then return g end
  local okg, genv = pcall(function() return getgenv() end)
  if okg and type(genv) == 'table' then
    local ok2, v = pcall(function() return genv[n] end)
    if ok2 and v ~= nil then return v end
  end
  return nil
end

local function caps()
  local names = {'fireclickdetector','firesignal','firetouchinterest','fireproximityprompt',
    'getconnections','hookfunction','hookmetamethod','getrawmetatable','setreadonly',
    'isreadonly','getgenv','getgc','loadstring','readfile','writefile','isfile',
    'identifyexecutor','getnamecallmethod','checkcaller','newcclosure','cloneref',
    'request','http_request','setclipboard','getcustomasset','decompile','queue_on_teleport'}
  local out = {}
  for _, n in ipairs(names) do
    out[#out + 1] = n .. '=' .. type(globalOf(n))
  end
  log('caps ' .. table.concat(out, ' '))
end

-- ========== GUI (the client-side half of the control surface) ==========
-- Why this exists: the census found 1019 ClickDetectors and NOT ONE of them
-- starts a shift.  A ClickDetector's handler runs on the SERVER, and a fire from
-- this VM only reaches the client's own listeners.  A GUI button is the
-- opposite: its handler is always a client LocalScript, so pressing one from
-- here runs real code and whatever remote it sends does reach the server.  A
-- game parked on a menu is therefore far more likely to be waiting here.
local function fmtVec2(p)
  if p == nil then return '-' end
  return string.format('%.0f,%.0f', p.X, p.Y)
end

local function guiRoot()
  local lp = localPlayer()
  if lp == nil then return nil end
  return lp:FindFirstChildOfClass('PlayerGui')
end

-- The one conversion this file needs and used to get wrong: AbsolutePosition is
-- CoreUISafe space -- its y is measured from below the topbar -- while
-- VirtualInputManager and UserInputService:GetMouseLocation() are SCREEN space,
-- whose y counts from the physical top of the viewport.  On this client those
-- two differ by 58 px in y, and that 58 is why every synthetic press before
-- this version landed, silently, on empty pixels.
--
-- THE INSET IS ADDED FOR EVERY ScreenGui DESCENDANT, and that is a measurement,
-- not a style.  d5 branched on IgnoreGuiInset, reading the reference's
-- "true => ScreenInsets is DeviceSafeInsets" as "those children are already in
-- screen space".  That is not what the property does.  IgnoreGuiInset moves the
-- ScreenGui's own RECT -- this game's reads abs=0,-58 1151x714 against Roblox's
-- own MouseGui at 0,0 1151x656, same bottom edge, 58 apart at the top -- while
-- the space a child's AbsolutePosition is expressed in is CoreUISafe either way.
--
-- Swept in the live client with PlayerGui:GetGuiObjectsAtPosition, an oracle
-- that synthesizes no input and so cannot be perturbed by a pointer already
-- resting somewhere.  It goes empty at y=656 and resumes at y=-58, and it has
-- the button present for y in 594..636.  AbsolutePosition puts that button at
-- 1088.3,593.5 42.9x42.9, so 593.5 and 636.4 are its edges -- all four readings
-- land on CoreUISafe space and none of them on screen space.  Its true screen
-- centre is therefore 673, and d4 and d5 both computed 614.
--
-- Both halves are still READ, never hardwired: the inset comes from GuiService,
-- so a different topbar cannot put the bug back.  The flag is still read, but
-- only into the NAME, where it is a diagnostic -- it does not branch.
--
-- A SurfaceGui or BillboardGui is a THIRD case and is not a screen space at all:
-- a child there is positioned in the surface's own layout, and no screen
-- coordinate reaches it.  That case is still computed and still NAMED rather
-- than refused, because a route that is silently wrong and a route that is
-- silently absent are both worse than one that says which it is -- but the
-- label is the disclosure: a point whose name starts 'layout/' is not a screen
-- coordinate and pressing it lands somewhere unintended.
--
-- Returns the point, the inset used, and a NAME for which case ran.  The name
-- is the point: an unknown space that silently reads as 0 is the same defect
-- wearing a hat, so 'nospace' is a value that gets logged, not a fallback.
local function clickPoint(btn)
  local okp, ap = pcall(function() return btn.AbsolutePosition end)
  local oks, as = pcall(function() return btn.AbsoluteSize end)
  if not okp or not oks or ap == nil or as == nil then return nil, nil, 'norect' end
  local inset = Vector2.new(0, 0)
  local space = 'nospace'
  local okl, lc = pcall(function() return btn:FindFirstAncestorWhichIsA('LayerCollector') end)
  if okl and lc ~= nil then
    if lc:IsA('ScreenGui') then
      local okg, gi = pcall(function() return game:GetService('GuiService'):GetGuiInset() end)
      if okg and gi ~= nil then
        inset = Vector2.new(gi.X, gi.Y)
        space = 'inset+' .. string.format('%.0f,%.0f', inset.X, inset.Y)
        -- Diagnostic only.  Set on BOTH sides of the flag, deliberately: the
        -- suffix appearing must never be read as "the point changed", because
        -- the whole defect d5 shipped was that reading.
        local okf, flag = pcall(function() return lc.IgnoreGuiInset end)
        if okf and flag == true then space = space .. '/ignoreinset' end
      end
    else
      space = 'layout/' .. lc.ClassName
    end
  end
  local p = ap + inset + as / 2
  return Vector2.new(math.floor(p.X), math.floor(p.Y)), inset, space
end

local function guiCensus()
  local pg = guiRoot()
  if pg == nil then
    log('gui FAIL no PlayerGui')
    return
  end
  local out = {}
  out[#out + 1] = '# gui at ' .. now() .. ' rel ' .. rel()
  out[#out + 1] = '# KIND | fullPath | visible | text | absPos | clickPoint'
  local n = 0
  local function walk(node, depth)
    if depth > 8 then return end
    for _, c in ipairs(node:GetChildren()) do
      local cn = c.ClassName
      if cn == 'TextButton' or cn == 'ImageButton' then
        n = n + 1
        if n <= CFG.GuiCap then
          local okv, vis = pcall(function() return c.Visible end)
          local okt, t = pcall(function() return c.Text end)
          local okp, ap = pcall(function() return c.AbsolutePosition end)
          -- No 'and/or': Visible is a boolean and false is a real answer here.
          local visStr = '?'
          if okv then visStr = tostring(vis) end
          local txt = ''
          if okt and type(t) == 'string' then txt = t end
          local pos = '-'
          if okp and ap ~= nil then pos = fmtVec2(ap) end
          -- The click-space point, not just the rect.  A rect in GUI space is
          -- not a coordinate anyone can press with, and reading one and pressing
          -- with it is exactly the 58 px miss this file used to have -- so the
          -- census and pressAt both go through clickPoint() and agree by
          -- construction rather than by my remembering to add the same number.
          local cp, _, space = clickPoint(c)
          local click = 'norect'
          if cp ~= nil then click = fmtVec2(cp) .. ' ' .. tostring(space) end
          out[#out + 1] = cn .. ' | ' .. c:GetFullName() .. ' | ' ..
            visStr .. ' | ' .. flat(txt) .. ' | ' .. pos .. ' | ' .. click
        end
      end
      walk(c, depth + 1)
    end
  end
  walk(pg, 0)
  out[#out + 1] = '# done buttons=' .. tostring(n)
  write(CFG.GuiFile, table.concat(out, NL) .. NL)
  log('gui done buttons=' .. tostring(n))
end

-- Three routes to fire one signal, tried in order and the winner LOGGED.  In
-- this executor the built-in signal has no :Fire, so the order matters and a
-- silence would be indistinguishable from a completed press.
local function pressSignal(sig)
  local fs = globalOf('firesignal')
  if type(fs) == 'function' then
    local ok = pcall(fs, sig)
    if ok then return 'firesignal' end
  end
  local okFire = pcall(function() sig:Fire() end)
  if okFire then return 'sig:Fire' end
  local gc = globalOf('getconnections')
  if type(gc) == 'function' then
    local ok, conns = pcall(gc, sig)
    if ok and type(conns) == 'table' and #conns > 0 then
      local n = 0
      for _, c in ipairs(conns) do
        local fn = c.Function
        if fn == nil then fn = c.func end
        if type(fn) == 'function' then
          local o = pcall(fn)
          if o then n = n + 1 end
        end
      end
      if n > 0 then return 'getconnections x' .. tostring(n) end
    end
  end
  return nil
end

-- The fourth route, and in THIS executor the only one.  The chain above presses
-- a SIGNAL; this presses a RECTANGLE.  Both matter: with firesignal and
-- getconnections nil and no :Fire on the signal, a signal-only chain has nothing
-- left, while the button is still a rectangle on the screen and this VM can
-- click that (same family as the anti-idle's VirtualUser path -- in-game input,
-- not the operator's cursor).
--
-- Three ways for this to lie, so all three are checked and all three are NAMED:
-- a hidden button, a zero-size button, and -- the one that actually bit -- a
-- coordinate in the wrong space.  The first two are clicked straight through to
-- whatever is really at those pixels; the third is the same failure one layer
-- down, because a GUI-space point is 58 px off in y and lands on whatever is
-- there instead.  All three are indistinguishable from a press that did nothing,
-- so this returns a reason (or the space it used) instead of just nil.  A route
-- that cannot say why it did not fire is the silent kind.
local function pressAt(btn)
  local vis, node = true, btn
  while node ~= nil and node ~= game do
    local okv, v = pcall(function() return node.Visible end)
    if okv and v == false then
      vis = false
      break
    end
    node = node.Parent
  end
  if not vis then return nil, 'SKIP hidden' end
  local oks, as = pcall(function() return btn.AbsoluteSize end)
  if not oks or as == nil then return nil, 'SKIP no rect' end
  if as.X < 1 or as.Y < 1 then return nil, 'SKIP zero size' end
  -- GUI space -> screen space.  See clickPoint: this used to be the whole bug.
  local pt, _, space = clickPoint(btn)
  if pt == nil then return nil, 'SKIP no rect' end
  -- clickPoint gives a GUESS; clickScreen gives the point the button event is
  -- actually handed.  Both are reported, because a press that used 'nospace' is
  -- a press at a guessed coordinate and must not read later like one that used
  -- a measured inset -- and neither of those may read like the read-back point.
  local how, e = clickScreen(pt.X, pt.Y)
  if how == nil then return nil, tostring(e) end
  return 'guess@' .. pt.X .. ',' .. pt.Y .. ' ' .. tostring(space) .. ' -> ' .. how
end

local function doPress(path, method)
  local node, err = resolve(path)
  if node == nil then
    log('press FAIL resolve :: ' .. flat(err))
    return
  end
  local btn = node
  if btn.ClassName ~= 'TextButton' and btn.ClassName ~= 'ImageButton' then
    btn = node:FindFirstChildOfClass('TextButton')
    if btn == nil then btn = node:FindFirstChildOfClass('ImageButton') end
  end
  if btn == nil then
    log('press FAIL no button under ' .. path)
    return
  end
  local m = string.lower(method or 'activated')
  local order
  if m == 'click' then order = {'click', 'activated'} else order = {'activated', 'click'} end
  local before = statline()
  local how = nil
  for _, which in ipairs(order) do
    local sig
    if which == 'click' then sig = btn.MouseButton1Click else sig = btn.Activated end
    local got = pressSignal(sig)
    log('press try ' .. which .. ' -> ' .. tostring(got))
    if got ~= nil then
      how = got .. ' on ' .. which
      break
    end
  end
  if how == nil then
    local at, why = pressAt(btn)
    log('press try mouse -> ' .. tostring(at or why))
    how = at
  end
  if how == nil then
    log('press FAIL no route worked for ' .. btn:GetFullName())
    return
  end
  log('press ' .. btn:GetFullName() .. ' via ' .. how)
  task.wait(CFG.SettleSeconds)
  local after = statline()
  if after == before then
    log('press NOCHANGE ' .. after)
  else
    log('press CHANGED ' .. after)
  end
end

-- Every readable property of one node that actually exists.  pcall per name, so
-- an absent member is skipped rather than fatal -- and only a real failure
-- reads ERR.
local function doRead(path)
  local node, err = resolve(path)
  if node == nil then
    log('read FAIL ' .. flat(err))
    return
  end
  local want = {'Text','Visible','Enabled','Active','Value','Position','CFrame',
    'Size','Color','Material','Transparency','Image','BackgroundColor3',
    'TextColor3','AbsolutePosition','AbsoluteSize','Orientation'}
  local out = {}
  for _, k in ipairs(want) do
    local ok, v = pcall(function() return node[k] end)
    if ok and v ~= nil then out[#out + 1] = k .. '=' .. flat(v) end
  end
  log('read ' .. node:GetFullName() .. ' (' .. node.ClassName .. ') :: ' ..
    table.concat(out, ' | '))
end

-- The game's own HUD, in the game's own words.  Phase 99 read it through the s2
-- recorder; this is the same read on demand, so a press can be judged against
-- what the panels SAY and not only against 32 ValueBases.
local function doProbe()
  local found = 0
  local seen = 0
  local t0 = os.clock()
  local why = nil
  for _, d in ipairs(game:GetDescendants()) do
    if found >= CFG.ProbeCap then why = 'labelcap' break end
    if os.clock() - t0 > CFG.ProbeMs / 1000 then why = 'timecap' break end
    seen = seen + 1
    -- Yield on a COUNT, not on a clock: the reason to hand the frame back does
    -- not depend on how fast this machine is.
    if seen % 500 == 0 then task.wait() end
    if d:IsA('TextLabel') or d:IsA('TextButton') then
      local p, depth, hit = d, 0, false
      while p ~= nil and depth < 6 do
        if string.find(p.Name, CFG.MonitorHint, 1, true) ~= nil then
          hit = true
          break
        end
        p = p.Parent
        depth = depth + 1
      end
      if hit then
        local okt, t = pcall(function() return d.Text end)
        if okt and type(t) == 'string' and t ~= '' then
          found = found + 1
          log('P ' .. d:GetFullName() .. ' :: ' .. flat(t))
        end
      end
    end
  end
  -- `why` is on the line on purpose: a probe cut short and a probe that ran to
  -- the end look identical otherwise, and the short one's silence would read
  -- as "the panels say nothing".
  log('probe labels=' .. tostring(found) .. ' seen=' .. tostring(seen) ..
    ' ms=' .. string.format('%.0f', (os.clock() - t0) * 1000) ..
    ' stopped=' .. tostring(why or 'end'))
end

-- Answers 'is anything ticking'.  One before/after read cannot tell a frozen
-- world from a slow one, and a 30 s heartbeat is a flat line in any shorter
-- window -- the same lesson as trg_drive_loop.txt.  Samples Stats at 4 Hz and
-- logs ONLY the changes, so a quiet run costs two lines.
local function doListen(secs)
  local n = tonumber(secs) or 10
  if n < 1 then n = 1 end
  if n > 60 then n = 60 end
  local prev = statline()
  local t0 = os.clock()
  local changes = 0
  log('listen begin ' .. tostring(n) .. 's')
  while os.clock() - t0 < n do
    task.wait(0.25)
    local cur = statline()
    if cur ~= prev then
      changes = changes + 1
      log('L ' .. string.format('%.2f', os.clock() - t0) .. ' ' .. cur)
      prev = cur
    end
  end
  log('listen end changes=' .. tostring(changes))
end

-- Positions, for the mechanical half of a click test: 'only LeverUnion moved'.
local function doCf(path)
  local node, err = resolve(path)
  if node == nil then
    log('cf FAIL ' .. flat(err))
    return
  end
  local targets = {}
  if node:IsA('BasePart') then targets[#targets + 1] = node end
  for _, c in ipairs(node:GetChildren()) do
    if c:IsA('BasePart') then targets[#targets + 1] = c end
  end
  if #targets == 0 then
    log('cf NOPARTS ' .. node:GetFullName())
    return
  end
  for i = 1, math.min(#targets, 40) do
    local t = targets[i]
    local okp, pos = pcall(function() return t.Position end)
    local oks, siz = pcall(function() return t.Size end)
    local pStr, sStr = 'ERR', 'ERR'
    if okp then pStr = fmtPos(pos) end
    if oks then sStr = fmtPos(siz) end
    log('C ' .. t:GetFullName() .. ' pos=' .. pStr .. ' size=' .. sStr)
  end
end

-- ========== COMMAND DISPATCH ==========
local function splitArgs(s)
  local t = {}
  for w in string.gmatch(s, '%S+') do t[#t + 1] = w end
  return t
end

local function execute(seq, rest)
  local a = splitArgs(rest)
  local verb = string.lower(a[1] or '')
  log('#' .. tostring(seq) .. ' ' .. verb .. ' ' .. table.concat(a, ' ', 2))
  if verb == 'census' then
    log(census())
  elseif verb == 'stats' then
    log('stats ' .. statline())
  elseif verb == 'fire' then
    doFire(a[2], a[3], a[4])
  elseif verb == 'fireall' then
    doFireAll(a[2])
  elseif verb == 'near' then
    doNear(a[2], a[3])
  elseif verb == 'ls' then
    doLs(a[2])
  elseif verb == 'pos' then
    log('pos ' .. charPos())
  elseif verb == 'gui' then
    guiCensus()
  elseif verb == 'press' then
    doPress(a[2], a[3])
  elseif verb == 'read' then
    doRead(a[2])
  elseif verb == 'probe' then
    doProbe()
  elseif verb == 'listen' then
    doListen(a[2])
  elseif verb == 'cf' then
    doCf(a[2])
  elseif verb == 'caps' then
    caps()
  elseif verb == 'idle' then
    antiIdle(true, 'verb')
  elseif verb == 'stop' then
    M.stop()
  elseif verb == '' then
    -- blank line, nothing to do
  else
    log('unknown verb ' .. flat(verb))
  end
end

local function loadSeq()
  local s = read(CFG.StateFile)
  local n = tonumber(string.match(s, '^(%d+)') or '')
  return n or 0
end

local function saveSeq(n)
  write(CFG.StateFile, tostring(n) .. NL)
  -- Read-after-write lag, measured 2026-10-10: this file held 203 while the very
  -- next loadSeq() in the same pass returned 0.  On disk the seq is only as good
  -- as the executor's flush; in memory it cannot lag, so the floor is kept in
  -- both places and the higher one wins.  Without this, one empty read re-runs
  -- the whole file -- and a file that contains 'stop' replays 'stop'.
  if n > (M._seq or 0) then M._seq = n end
end

-- Every command whose seq is greater than the last one executed.  The file is
-- never truncated: it is the durable record of what was asked, and a lost
-- command would be invisible if it were cleared after reading.
local function runCmds()
  local text = read(CFG.CmdFile)
  if text == '' then return 0 end
  local last = loadSeq()
  if (M._seq or 0) > last then last = M._seq end
  local maxSeq = last
  local n = 0
  for line in string.gmatch(text, '[^' .. CR .. NL .. ']+') do
    local seq, rest = string.match(line, '^(%d+)%s+(.*)$')
    if seq ~= nil then
      seq = tonumber(seq)
      if seq ~= nil and seq > last then
        if seq > maxSeq then maxSeq = seq end
        n = n + 1
        execute(seq, rest)
      end
    end
  end
  -- Raised UNCONDITIONALLY, and that adverb is the fix.  This used to happen
  -- only inside saveSeq, which is reached ONLY when the pass had something new
  -- to run -- so the pass that found every command already done left M._seq
  -- nil.  That is precisely the pass that arms the next one to replay: with
  -- the memory floor unset, the sole thing between a laggy disk read and the
  -- top of the file is that read itself.  A floor written only when work was
  -- done is not a floor, it is a note about the last time work was done.
  if maxSeq > (M._seq or 0) then M._seq = maxSeq end
  if maxSeq ~= last then saveSeq(maxSeq) end
  return n
end

-- ========== PUBLIC ==========
M.running = false

-- One poll iteration.  Public on purpose: the loop below is a one-line caller,
-- so the thing that gets tested is the same code that runs.  A loop whose body
-- lives only inside a connection cannot be driven from outside it.
function M.step()
  local n = runCmds()
  antiIdle(false, 'timer')
  write(CFG.LoopFile, now() .. ' rel=' .. rel() ..
    ' seq=' .. tostring(M._seq or 0) .. ' cmds=' .. tostring(n) .. NL)
  return n
end

function M.stop()
  M.running = false
  log('stop requested')
end

function M.start()
  if M.running then
    log('already running')
    return true
  end
  M.running = true
  -- Seed the floor from disk once, so a fresh injection does not replay a file
  -- whose already-executed lines the executor only forgot to flush.
  local seeded = loadSeq()
  if seeded > (M._seq or 0) then M._seq = seeded end
  append(CFG.LogFile, '# ' .. M.TAG .. ' start ' .. now() .. NL)
  log('drive start ' .. statline() .. ' seqfloor=' .. tostring(M._seq))

  -- Cancel a pending idle kick the moment it is announced.  Event-driven, so it
  -- costs nothing until the client is actually about to be dropped; the periodic
  -- timer in M.step covers the case where the event never arrives.
  local lp0 = localPlayer()
  if lp0 ~= nil then
    local okHook = pcall(function()
      lp0.Idled:Connect(function() antiIdle(true, 'idled') end)
    end)
    if not okHook then log('idled hook FAIL') end
  end

  task.spawn(function()
    while M.running do
      local ok, err = pcall(M.step)
      if not ok then
        append(CFG.FatalFile,
          '[' .. now() .. '] step error: ' .. flat(err) .. NL)
      end
      task.wait(CFG.Poll)
    end
    log('drive loop exited')
  end)
  return true
end

-- ========== AUTORUN ==========
-- Same gate shape as the recorder, different global: setting
-- _G.TRG_DRIVE_AUTORUN = false before injecting gives a loaded module that
-- does nothing until M.start() is called by hand.
if _G.TRG_DRIVE_AUTORUN == nil then
  _G.TRG_DRIVE_AUTORUN = true
end
if _G.TRG_DRIVE_AUTORUN then
  M.start()
end

-- The autoexec stub asks THIS whether a loop is already alive before it loads
-- and starts another one.  A stub that guards on "have I ever loaded" instead
-- makes the only recovery route -- injecting again -- a silent no-op.
pcall(function()
  local g = getgenv()
  if type(g) == 'table' then g.TRG_DRIVE = M end
end)

return M
