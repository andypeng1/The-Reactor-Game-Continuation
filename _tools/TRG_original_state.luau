--[[
TRG_original_state.luau   (tag s2)

WHAT THIS IS
  A recorder for the ORIGINAL game's machine-readable reactor state.  It hangs
  one GetPropertyChangedSignal('Value') on every ValueBase under
  Workspace.Stats and appends one line per actual write.

WHY A HOOK AND NOT A POLL
  The hotkey captures read a RENDERED PANEL.  Two consequences, both already
  paid for in this project:

    * a value written and re-written between two samples leaves no trace, so
      that record cannot separate 'held' from 'written twice';
    * the panel rounds -- it prints NIL F when TemperatureVal is 0, and on at
      least one build it disagreed with the state outright (RadiationLabel 40 R
      while Core.RadiationVal was 0).

  GetPropertyChangedSignal fires once per real write and is silent on a
  same-value write.  Measured, not assumed: three writes (true, true, false)
  gave fires=2 with seen=[true, false].  So the ABSENCE of a line is evidence
  here, which is exactly what a 1 Hz poll cannot give.

WHAT THIS CANNOT SEE -- and it is not a defect, it is a boundary
  Measured on this client: of 24445 attributes, ZERO mention coolant, pump, pea,
  cbl, stress, fluct or qpu, and there is no such ValueBase either.  Those
  quantities never reach the client; they arrive only as text the server has
  already rendered.  So the panel snapshot is the route to them, and it carries
  the panel's rounding with it -- 'NIL F' for a temperature of 0 is the panel's
  word, not the state's.

  The panel's TEXT is also not the alarm state, which an earlier build of this
  file claimed it was.  Measured: AlertsControlRoomMonitor carries 39 captions
  and all 39 read Visible=true at TextTransparency=0.00 whether their alarm is
  firing or not -- they are permanent labels.  The state is a separate Frame
  behind each one.  See alertLamps.  The general shape is worth keeping: one
  screenful can render a quantity accurately and a state inaccurately at the
  same time.

LINE FORMAT -- FROZEN
  Every record line is
      [HH:MM:SS] <rel-s> <path> <old> -> <new>
  and every meta line starts with '#'.  Two snapshot shapes, one per clock:
      [HH:MM:SS] <rel-s> = <path>=<value> ...            (the ValueBase set)
      [HH:MM:SS] <rel-s> ~ <Monitor>{...} ... <AlertsLamps.n/m{...}>
  Nothing gets appended to any of these shapes later; new content goes in a new
  '#' line or a new file.  This is the rule the boot recorder paid for: the
  reader is greedy and anchored, so a longer line is not a backwards-compatible
  line.  s2 adds the trailing AlertsLamps segment -- permissible only because no
  real capture was ever taken under s1, so there is no file in the world whose
  reader would break.  From the first real capture on, this shape is closed.

TIME BASE
  Two clocks per line, on purpose.  <HH:MM:SS> is the CLIENT'S LOCAL time and is
  what the operator's own hotkey captures are stamped with, so the two files can
  be lined up by eye.  <rel-s> is os.clock() since injection, monotonic, for
  intervals.  Server time is UTC and this client is UTC+8 -- do not compare a
  server stamp to a capture stamp.

NO HOTKEY
  Deliberately.  RightAlt / RightControl / RightShift are already taken by the
  recorder, the watcher and the boot recorder; a fourth binding would collide
  silently.  Re-inject for a new session and a new file appears.

USAGE
  loadstring(readfile('TRG_original_state.luau'))()
  Files land in the executor workspace next to the script.
]]

local M = {}
M.TAG = 's2'

-- ========== CONFIG ==========
local CFG = {
  -- ValueObjects live here.  Resolved by NAME, not by path, so a container
  -- rename elsewhere does not silently record nothing.
  StatsName = 'Stats',

  -- Snapshot the whole world every this many seconds.  This is what proves the
  -- recorder was alive through a stretch where nothing was written -- without
  -- it, 'quiet' and 'dead' are the same file.
  Heartbeat = 30,

  -- Buffer flush period.  One appendfile per second, not one per line.
  Flush = 1,

  -- Stop after this many record lines so a forgotten session cannot fill the
  -- disk.  ~1.2 lines/s in steady state, so this is days.
  MaxLines = 2000000,

  -- Bounded wait for Workspace.Stats.  A client can be injected before the
  -- place finishes replicating, but an unbounded wait is the failure mode this
  -- project has paid for most often.
  BiasWait = 60,

  Prefix = 'trg_state_',
  IndexFile = 'trg_state_index.txt',
  FatalFile = 'trg_state_FATAL.txt',
}

local NL = string.char(10)

-- ========== CLOCK ==========
local t0 = os.clock()
local function rel()
  return string.format('%.3f', os.clock() - t0)
end
local function hms()
  return os.date('%H:%M:%S')
end

-- ========== THE HOOK ==========
-- Walks a tree, hangs a change hook on every ValueBase, and calls
-- sink('write', path, old, new) on each actual write.
--
-- The selector is ValueBase and NOT ValueObject.  'ValueObject' is not a class
-- in this engine: IsA returns FALSE for it and raises nothing, so the first
-- build of this file hooked 0 of 32 objects and wrote a file that reads exactly
-- like a quiet shift.  Measured on the live client: IntValue:IsA('ValueBase')
-- = true, IntValue:IsA('ValueObject') = false, and a sweep of Workspace.Stats
-- counts 32 ValueBase / 0 ValueObject descendants.  A wrong name here is the
-- one failure this file exists to make visible, so it must not also be a silent
-- one -- M.start() therefore refuses to exit quietly on hooked == 0.
--
-- Exposed so a self-test can drive THIS function rather than a copy of it: a
-- duplicate of the hooking logic passing its own test proves nothing about the
-- bytes that ship.
--
-- Returns hooked (count) and seen (instance -> relative path), the latter so the
-- caller can snapshot the tracked set without walking again.
function M.attach(root, sink)
  local prev, seen, hooked = {}, {}, 0

  local function relpath(inst)
    local parts, d = {}, inst
    while d and d ~= root do
      parts[#parts + 1] = d.Name
      d = d.Parent
    end
    if d ~= root then return nil end
    local fwd = {}
    for i = #parts, 1, -1 do fwd[#fwd + 1] = parts[i] end
    return table.concat(fwd, '.')
  end

  local function hookOne(inst)
    if not inst:IsA('ValueBase') then return end
    -- Keyed by INSTANCE, not by path.  A path-keyed map would skip a re-created
    -- object that lands on a path it already recorded, and the surviving
    -- connection would then point at a destroyed instance -- the exact defect
    -- that cost the boot recorder a run.
    if seen[inst] ~= nil then return end
    local p = relpath(inst)
    if not p or p == '' then return end
    seen[inst] = p
    prev[inst] = inst.Value

    local ok, sig = pcall(function()
      return inst:GetPropertyChangedSignal('Value')
    end)
    if not ok or not sig then
      sink('dead', p, tostring(inst.ClassName), '')
      return
    end
    local ok2 = pcall(function()
      sig:Connect(function()
        local new = inst.Value
        local old = prev[inst]
        prev[inst] = new
        sink('write', p, old, new)
      end)
    end)
    if ok2 then
      hooked = hooked + 1
    else
      sink('dead', p, tostring(inst.ClassName), '')
    end
  end

  for _, inst in ipairs(root:GetDescendants()) do
    hookOne(inst)
  end

  -- Late arrivals.  The boot recorder learned that DescendantAdded alone is not
  -- enough (values present at birth get played as a baseline and lost); here it
  -- is the SUPPLEMENT to a full sweep, which is the safe order.
  pcall(function()
    root.DescendantAdded:Connect(hookOne)
  end)

  return hooked, seen
end

-- ========== THE WRITER ==========
local state = {
  buf = {},
  lines = 0,
  path = nil,
  errpath = nil,
  stopped = false,
  drops = 0,
  seen = nil,
  lastBeat = 0,
}

local function emit(s)
  state.buf[#state.buf + 1] = s
end

local function sink(kind, a, b, c)
  if kind == 'write' then
    emit(string.format('[%s] %s %s %s -> %s',
      hms(), rel(), a, tostring(b), tostring(c)))
    state.lines = state.lines + 1
  elseif kind == 'dead' then
    emit(string.format('[%s] %s ! %s (%s) could not be hooked',
      hms(), rel(), a, b))
  end
end

local function flush()
  if #state.buf == 0 then return true end
  local chunk = table.concat(state.buf, NL) .. NL
  state.buf = {}
  local ok = pcall(appendfile, state.path, chunk)
  if ok then return true end
  -- A transport failure must not be silent: it would look exactly like 'no
  -- writes', which is the one thing this file exists to make visible.
  state.drops = state.drops + 1
  if state.drops > 10 then
    state.stopped = true
    pcall(writefile, state.errpath,
      'appendfile failed ' .. state.drops .. ' times at ' .. hms() .. NL)
  end
  return false
end

-- Alarm lamps.  MEASURED on the live client: each of the 27 alarm captions on
-- AlertsControlRoomMonitor has exactly one sibling Frame of the IDENTICAL rect
-- (same AbsolutePosition and AbsoluteSize), and the 12 captions that have no
-- such sibling are exactly the non-alarm ones -- company text, mainframe OS, the
-- three big status words (27 + 12 = 39, reconciles).  The caption is permanent
-- black text; the frame is the lamp behind it and carries that alarm's own
-- severity colour: 255,0,0 severe / 170,0,255 malfunction / 255,255,0 active /
-- 255,85,0 caution / 104,255,34 core active / 255,85,255 destabilisation /
-- 0,170,255 stallout.  On a shut-down reactor ALL 27 lamps read Visible=false
-- while all 27 captions read Visible=true.
--
-- HYPOTHESIS, and it is labelled one: a lamp turning Visible is how the game
-- says 'this alarm is firing'.  That fits every reading above and is the
-- standard annunciator design, but no lamp has been watched transitioning, so it
-- is not a measurement yet.  The test is one line -- start the reactor and see
-- whether CBL ACTIVE / PUMP ACTIVE light.  What is NOT in doubt is the negative:
-- the captions are static, so a snapshot of the TEXT ALONE cannot say which
-- alarm fired.  An earlier build of this file claimed the opposite.
--
-- Defined before panelLines because it is a local, and a local declared after
-- its reader is a nil upvalue, i.e. a call that fails at the first heartbeat.
local function alertLamps(root)
  local A = root:FindFirstChild('AlertsControlRoomMonitor')
  if not A then return 'AlertsLamps.0/0{no monitor}' end

  local function rect(o)
    return string.format('%.0f,%.0f,%.0f,%.0f',
      o.AbsolutePosition.X, o.AbsolutePosition.Y,
      o.AbsoluteSize.X, o.AbsoluteSize.Y)
  end

  -- Index plates by rect and keep the multiplicity, so a caption whose rect is
  -- shared by two frames is dropped as ambiguous rather than paired by luck.
  local plate = {}
  for _, d in ipairs(A:GetDescendants()) do
    if (d:IsA('Frame') or d:IsA('ImageLabel')) and d.AbsoluteSize.X > 4 then
      local k = rect(d)
      local e = plate[k]
      if e then e[2] = e[2] + 1 else plate[k] = { d, 1 } end
    end
  end

  local lit, total = {}, 0
  for _, d in ipairs(A:GetDescendants()) do
    if d:IsA('TextLabel') and d.Text ~= '' then
      local e = plate[rect(d)]
      if e and e[2] == 1 then
        total = total + 1
        local f = e[1]
        if f.Visible then
          local c = f.BackgroundColor3
          lit[#lit + 1] = string.format('%s=%d,%d,%d', d.Text,
            c.R * 255 + 0.5, c.G * 255 + 0.5, c.B * 255 + 0.5)
        end
      end
    end
  end
  table.sort(lit)
  return string.format('AlertsLamps.%d/%d{%s}', #lit, total,
    #lit == 0 and 'none visible' or table.concat(lit, '; '))
end

-- Panel snapshot.  Long, but it is the only route to the quantities the client
-- does not hold as a ValueBase -- coolant pump levels, PEA stress, CBL body
-- temperatures -- and it puts them on the same clock as the state line so the
-- two can be compared without a join.
--
-- No truncation.  An earlier build kept only the first four labels
-- alphabetically once a monitor had more than twelve lit, on the stated theory
-- that 'for a monitor that lists its alarms [the first few are] enough to see
-- which fired'.  Both halves of that were wrong and both were measured wrong:
-- the alarms are not in the text at all (see alertLamps), and the cap was
-- dropping precisely the payoff -- MainControlRoomMonitor is 81 lit, so 77 went
-- and with them PressureLabel / StressLabel / TempLabel / PEANameText, while
-- ThermalControlRoomMonitor lost Title=NET C-PUMP FLOW RATE and its PUMP C1..C3
-- and CHAMBER FAN 1..6 roster.
local function panelLines()
  local out = {}
  local root = workspace:FindFirstChild('Monitors')
  if not root then
    -- Plain string, no format specifiers: this line is emitted verbatim, so a
    -- stray %s here would be printed as a literal '%%s' in the record.
    out[#out + 1] = '(no Workspace.Monitors)'
    return out
  end
  for _, mon in ipairs(root:GetChildren()) do
    -- Two counts on purpose.  nlit is how many labels are drawn -- the number a
    -- reader compares run to run, and the number the old cap acted on.  body is
    -- deduplicated by Name=Text, which loses nothing (identical strings carry no
    -- extra information) while keeping the multiplicity as xN, because three
    -- identical 'StressLabel=0 %' lines on PowerControlRoomMonitor mean three
    -- CBL channels, not one.  Measured duplicates: 21 Main / 13 Thermal / 18
    -- Power, out of 81 / 58 / 59 lit.
    local order, count, nlit, total = {}, {}, 0, 0
    for _, d in ipairs(mon:GetDescendants()) do
      if d:IsA('TextLabel') then
        local t = d.Text
        if t and t ~= '' then
          total = total + 1
          if d.Visible then
            nlit = nlit + 1
            local k = d.Name .. '=' .. t:gsub('%s+', ' ')
            if count[k] then
              count[k] = count[k] + 1
            else
              count[k] = 1
              order[#order + 1] = k
            end
          end
        end
      end
    end
    table.sort(order)
    local body = {}
    for _, k in ipairs(order) do
      body[#body + 1] = count[k] > 1 and (k .. ' x' .. count[k]) or k
    end
    out[#out + 1] = string.format('%s.%d/%d{%s}', mon.Name, nlit, total,
      #body == 0 and 'none' or table.concat(body, '; '))
  end
  out[#out + 1] = alertLamps(root)
  return out
end

local function snap()
  local ks = {}
  for inst, p in pairs(state.seen or {}) do
    if inst.Parent ~= nil then
      ks[#ks + 1] = string.format('%s=%s', p, tostring(inst.Value))
    end
  end
  table.sort(ks)
  emit(string.format('[%s] %s = %s', hms(), rel(), table.concat(ks, ' ')))
  emit(string.format('[%s] %s ~ %s', hms(), rel(),
    table.concat(panelLines(), ' ')))
end

-- ========== START ==========
function M.start()
  local S = workspace:FindFirstChild(CFG.StatsName)
  local deadline = os.clock() + CFG.BiasWait
  while not S and os.clock() < deadline do
    task.wait(0.5)
    S = workspace:FindFirstChild(CFG.StatsName)
  end
  if not S then
    error('Workspace.' .. CFG.StatsName .. ' never appeared within '
      .. CFG.BiasWait .. 's')
  end

  local stamp = os.date('%y%m%d-%H%M%S')
  state.path = CFG.Prefix .. stamp .. '.txt'
  state.errpath = state.path .. '.err'

  local exec = '?'
  pcall(function()
    if identifyexecutor then exec = tostring(identifyexecutor()) end
  end)

  -- Truncate rather than append: a session must start from a known byte 0, or
  -- the index line and the data disagree about where this run begins.
  local head = table.concat({
    string.format('# TRG_original_state build=%s executor=%s', M.TAG, exec),
    string.format('# place=%s started=%s', tostring(game.PlaceId),
      os.date('%Y-%m-%d %H:%M:%S')),
    '# record: [HH:MM:SS] <rel-s> <path> <old> -> <new>',
    '# snap:   [HH:MM:SS] <rel-s> = <path>=<value> ...',
    '# panel:  [HH:MM:SS] <rel-s> ~ <Monitor>{<Label>=<Text>; ...}'
      .. ' <AlertsLamps.n/m{TEXT=255,0,0; ...}>',
    '# panel labels are deduplicated, multiplicity kept as xN; n/m is lit/total',
    '# AlertsLamps counts the alarm plates that read Visible.  The captions are',
    '#   permanent text and do not change, so the lamps, not the text, carry state.',
    '# a MISSING record line is evidence: the hook is silent on a same-value write',
  }, NL) .. NL
  local okw = pcall(writefile, state.path, head)
  if not okw then error('cannot write ' .. state.path) end
  pcall(appendfile, CFG.IndexFile,
    state.path .. ' ' .. os.date('%Y-%m-%d %H:%M:%S') .. NL)

  local descended = #S:GetDescendants()
  local hooked, seen = M.attach(S, sink)
  state.seen = seen
  state.lastBeat = os.clock()
  emit(string.format('# hooked %d ValueBase objects under %s (of %d descendants)',
    hooked, S:GetFullName(), descended))
  snap()
  flush()

  if hooked == 0 then
    -- Fail loudly.  A recorder that hooked nothing writes a file whose first
    -- lines are a header and a heartbeat and whose body is empty -- byte-shape
    -- identical to a shift where the reactor simply never changed.  That is the
    -- one confusion this file was built to remove, so exit non-zero instead of
    -- handing back a plausible-looking empty log.  This is not hypothetical:
    -- an IsA('ValueObject') typo did exactly this on the first self-test.
    error(string.format(
      'hooked 0 of %d descendants under %s -- the selector is wrong, not the tree',
      descended, S:GetFullName()))
  end

  task.spawn(function()
    while not state.stopped do
      task.wait(CFG.Flush)
      if os.clock() - state.lastBeat >= CFG.Heartbeat then
        state.lastBeat = os.clock()
        snap()
      end
      if state.lines > CFG.MaxLines then
        emit('# STOP line cap reached')
        state.stopped = true
      end
      pcall(flush)
    end
    pcall(flush)
  end)

  return state.path
end

function M.stop()
  state.stopped = true
  pcall(flush)
end

-- ========== AUTORUN ==========
-- The guard exists so a self-test can load these bytes WITHOUT starting a
-- recording: it is the delivered file, not a re-implementation of it.
if _G.TRG_STATE_AUTORUN ~= false then
  local ok, err = pcall(M.start)
  if not ok then
    -- Report our own death.  Top-level code that throws before the first write
    -- is byte-identical to a script that was never injected, and this project
    -- has lost measurements to exactly that.
    pcall(writefile, CFG.FatalFile,
      tostring(err) .. NL .. tostring(debug.traceback()) .. NL)
  end
end

return M
