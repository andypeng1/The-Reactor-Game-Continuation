--[[
TRG_original_drive.luau   (tag d4)

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
]]

local M = {}
M.TAG = 'd4'

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

  -- Census gives up after this many descendants so a forgotten walk cannot
  -- wedge the thread.
  CensusCap = 300000,

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
  local ok, all = pcall(function() return game:GetDescendants() end)
  if not ok then
    log('census ERROR GetDescendants ' .. flat(all))
    return 'census ERROR'
  end
  for _, d in ipairs(all) do
    seen = seen + 1
    if seen > CFG.CensusCap then break end
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
    '  ProximityPrompt=' .. tostring(nPP)
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
  if method == 'signal' then
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

local function guiCensus()
  local pg = guiRoot()
  if pg == nil then
    log('gui FAIL no PlayerGui')
    return
  end
  local out = {}
  out[#out + 1] = '# gui at ' .. now() .. ' rel ' .. rel()
  out[#out + 1] = '# KIND | fullPath | visible | text | absPos'
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
          out[#out + 1] = cn .. ' | ' .. c:GetFullName() .. ' | ' ..
            visStr .. ' | ' .. flat(txt) .. ' | ' .. pos
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
-- Two ways for this to lie, so both are checked and both are NAMED: a hidden
-- button and a zero-size button are clicked straight through to whatever is
-- really at those pixels, and that outcome is indistinguishable from a press
-- that did nothing.  A route that cannot say why it did not fire is the silent
-- kind, so this one returns a reason instead of just nil.
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
  local okp, ap = pcall(function() return btn.AbsolutePosition end)
  local oks, as = pcall(function() return btn.AbsoluteSize end)
  if not okp or not oks or ap == nil or as == nil then return nil, 'SKIP no rect' end
  if as.X < 1 or as.Y < 1 then return nil, 'SKIP zero size' end
  local x = math.floor(ap.X + as.X / 2)
  local y = math.floor(ap.Y + as.Y / 2)
  local vim = game:GetService('VirtualInputManager')
  pcall(function() vim:SendMouseMoveEvent(x, y, game) end)
  local ok = pcall(function() vim:SendMouseButtonEvent(x, y, 0, true, game, 0) end)
  task.wait(0.05)
  ok = pcall(function() vim:SendMouseButtonEvent(x, y, 0, false, game, 0) end) and ok
  if not ok then return nil, 'ERR SendMouseButtonEvent' end
  return 'mouse@' .. x .. ',' .. y
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
  for _, d in ipairs(game:GetDescendants()) do
    if found >= CFG.ProbeCap then break end
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
  log('probe labels=' .. tostring(found))
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
end

-- Every command whose seq is greater than the last one executed.  The file is
-- never truncated: it is the durable record of what was asked, and a lost
-- command would be invisible if it were cleared after reading.
local function runCmds()
  local text = read(CFG.CmdFile)
  if text == '' then return 0 end
  local last = loadSeq()
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
    ' seq=' .. tostring(loadSeq()) .. ' cmds=' .. tostring(n) .. NL)
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
  append(CFG.LogFile, '# ' .. M.TAG .. ' start ' .. now() .. NL)
  log('drive start ' .. statline())

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

return M
