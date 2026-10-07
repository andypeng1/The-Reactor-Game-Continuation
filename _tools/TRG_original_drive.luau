--[[
TRG_original_drive.luau   (tag d1)

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
]]

local M = {}
M.TAG = 'd1'

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
      parts[#parts + 1] = d.Name .. '=' .. tostring(ok and v or 'ERR')
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
