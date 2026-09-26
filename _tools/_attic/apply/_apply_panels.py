"""Four additions to the recorder: the log, the forecast, the quota, and attribution.

WHY EACH ONE. The user asked for the reactor log, the subspace forecast and the
quota progress, and for the unattributed-change detector proposed after the
18:01 capture. They are one patch because three of the four are the same
problem seen on three different monitors.

  * THE LOG PANEL (LogControlRoomMonitor). The generic readout sweep already
    sees its rows -- they arrive as `x.TemplateLogFrame3 <b>[ALERT]</b> - ...`
    TEXT lines, and those lines are in the 18:01 file. What is missing is that a
    log row is not a value: three rows scroll, so the same key carries a
    different message every few seconds and the history has to be reassembled
    from the whole file by hand.

  * THE FORECAST PANEL (ForecastControlRoomMonitor). This is the panel an
    operator would actually act on -- future subspace energy fluctuations, the
    EFE and Equinox warnings -- and it is the one the sweep THROWS AWAY:
    `EVT1506 ANIM ...ScrollingFrame.TimeSliceTemplate.TimeLabel moved 5 times
    inside one poll; dropped as an animation`. Its rows are a ScrollingFrame of
    clones all named TimeSliceTemplate, so the rate arm condemns the key on the
    first poll. The panel that predicts the disaster was the thing discarded as
    noise.

  * THE QUOTA PANEL (QuotaControlRoomMonitor). Power delivered against the
    target and the time left to deliver it -- the shift's score. The sweep does
    catch QuotaFrame.PowerLabel, but as one number among eleven hundred.

THE ONE IDEA. A panel is ONE VALUE. Each panel is read as a single joined
snapshot, so it has exactly one key and can change at most once per poll no
matter how many of its rows moved. The rate arm cannot condemn it and the
chatter arm cannot either, and NEITHER GUARD HAD TO BE LOOSENED -- they are what
keeps the rest of the file readable.

The snapshot is sorted and the positional index is deliberately NOT included.
GetDescendants order is not guaranteed stable, so an index-free sorted list of
`name=text` pairs is a function of the multiset of the panel's contents and
nothing else -- it changes when the panel's content changes and is silent when
only the enumeration order moved. Including the row index would have made a
scrolling frame emit a change every poll, which is the exact flood the rate arm
was built to stop, reintroduced through the door marked "fix".

  * ATTRIBUTION. A control value that moved with no click behind it. The
    client-side ClickDetector hook sees only THIS client's presses, so a second
    operator in the server moves the plant invisibly -- the 18:01 capture holds
    four CBL level changes and not one CLICK event, and that absence is how a
    hand that was not ours was found at all, hours later, by hand. Recording
    rises to that: if a c.* key moves more than AttribWindowPolls after the last
    click this client saw, the file says so where it happened.
"""

import sys
from pathlib import Path

P = Path(__file__).resolve().parent / "TRG_original_recorder.luau"


def rep(src, old, new, tag):
    n = src.count(old)
    if n != 1:
        sys.exit("anchor %s matched %d times, wanted exactly 1" % (tag, n))
    return src.replace(old, new)


src = P.read_bytes().decode("utf-8")
before_bytes = len(src.encode("utf-8"))

# ------------------------------------------------------------- header ------
src = rep(src, """-- The Reactor Game -- ORIGINAL-GAME change recorder, v1.1
""", """-- The Reactor Game -- ORIGINAL-GAME change recorder, v1.2
""", "version")

src = rep(src, """--   Named keys in a batch: r.*=reactor readouts  m.*=monitor parsed
--   x.*=monitor unreadable text  c.*=controls  s.*=Stats ValueObjects
--   z.*=lamp matrices  t.*=discovered readout, decoded by its TMAP event
""", """--   Named keys in a batch: r.*=reactor readouts  m.*=monitor parsed
--   x.*=monitor unreadable text  c.*=controls  s.*=Stats ValueObjects
--   z.*=lamp matrices  t.*=discovered readout, decoded by its TMAP event
--
--   Panel snapshots are strings and so arrive as TEXT lines, not batch keys:
--   log.panel = the facility event log   fc.panel = the subspace forecast
--   q.panel   = quota progress. Each is one sorted snapshot of the whole panel,
--   emitted only when its contents change. See the PANELS section.
--
--   UNATTR is the fourth family and it is not a reading: it is an accusation.
--   `EVT<n> UNATTR c.cbl1Lvl 2->1 (last click 41 polls ago)` says a control
--   moved with no click this client could see. See the ATTRIBUTION section.
""", "legend")

# ------------------------------------------------------------- config ------
src = rep(src, """	MaxLampParts    = 20000,   -- refuse to scan an absurd Consoles tree
""", """	MaxLampParts    = 20000,   -- refuse to scan an absurd Consoles tree
	-- Panel snapshots. The cap is on the number of rows first and on characters
	-- second, and both are there because a snapshot is written as ONE line: an
	-- honest `<14 more>` beats a line nobody can read, and a panel that grew a
	-- thousand rows is worth being told about rather than worth writing out.
	MaxPanelLabels  = 200,
	MaxPanelChars   = 1200,
	-- How long after a click a control change still counts as attributed. Four
	-- polls is one game tick: the game applies a click on its own 1 Hz step, so
	-- a change that lands further out than that was not caused by the click this
	-- client saw. Eight is one tick plus slack for the poll straddling it.
	AttribWindowPolls = 8,
""", "config")

# --------------------------------------------------- change tracker state ---
src = rep(src, """local last = {}
local changed = {}
""", """local last = {}
local changed = {}

-- The control changes of the poll just finished, with the value each came FROM,
-- and the poll at which this client last saw a click. Both feed the attribution
-- pass; both are cleared once per poll, in pollOnce, beside `changed`.
local changedCtrl = {}
local clickPoll = nil
""", "tracker-state")

src = rep(src, """	if last[key] == value then return end
	last[key] = value
	changed[#changed + 1] = key .. '=' .. tostring(value)
end
""", """	if last[key] == value then return end
	-- Recorded with the value it came FROM, because `c.cbl1Lvl 2->1` is what an
	-- attribution report has to say and `c.cbl1Lvl=1` is not. Read before the
	-- assignment below, which is the only place the old value still exists.
	if string.sub(key, 1, 2) == 'c.' then
		changedCtrl[#changedCtrl + 1] = { key = key, from = last[key], to = value }
	end
	last[key] = value
	changed[#changed + 1] = key .. '=' .. tostring(value)
end
""", "put")

# --------------------------------------------------------- click stamping ---
src = rep(src, """		inst.MouseClick:Connect(function()
			emitEvt('CLICK', name or ('path=' .. ((host and host:GetFullName()) or 'nil')))
		end)
""", """		inst.MouseClick:Connect(function()
			-- Stamp the poll, not the clock. The stamp is compared against the
			-- poll counter, and a wall-clock stamp in a 4 Hz loop would drift
			-- against it for the same reason the driver s dwell timers did.
			clickPoll = sample
			emitEvt('CLICK', name or ('path=' .. ((host and host:GetFullName()) or 'nil')))
		end)
""", "click-stamp")

src = rep(src, """		inst.Triggered:Connect(function()
			emitEvt('PROMPT', inst:GetFullName())
		end)
""", """		inst.Triggered:Connect(function()
			clickPoll = sample
			emitEvt('PROMPT', inst:GetFullName())
		end)
""", "prompt-stamp")

# ----------------------------------------------------- PANELS + ATTRIBUTION -
src = rep(src, """-- ========================== THE ONE LOOP ==================================
""", """-- ========================== PANELS ========================================
-- The three monitors the generic readout sweep cannot report properly: the log,
-- which it reports as an unreadable stream of x.* rows; the forecast, which it
-- DROPS as an animation; and the quota, which it reports as one number among
-- eleven hundred. Read the section header of _tools/_apply_panels.py for the
-- measurement behind each of those, including the ANIM event that names the
-- forecast panel by path.
--
-- A PANEL IS ONE VALUE. One joined snapshot, one key, at most one change per
-- poll -- so the rate arm and the chatter arm both leave it alone, and neither
-- of them had to be weakened to make room.
local function panelRoot(...)
	local ok, r = pcall(child, Workspace, ...)
	if ok then return r end
	return nil
end

local LogPanel   = panelRoot('Monitors', 'LogControlRoomMonitor', 'Screen', 'MonitorUI', 'MainMonitorFrame')
local FcPanel    = panelRoot('Monitors', 'ForecastControlRoomMonitor', 'Screen', 'MonitorUI', 'MainMonitorFrame')
local QuotaPanel = panelRoot('Monitors', 'QuotaControlRoomMonitor', 'Screen', 'MonitorUI', 'MainMonitorFrame')

-- Sorted, and WITHOUT the row index. Sorting makes the string a function of the
-- panel s contents rather than of GetDescendants enumeration order, which is not
-- guaranteed stable -- an unsorted snapshot would emit a change every poll for
-- no reason at all. Leaving the index out is the second half of the same idea:
-- with the index in, a ScrollingFrame that scrolls shifts every row and emits
-- every poll, which is exactly the flood the rate arm exists to stop. Sorted and
-- index-free, the snapshot changes when the panel s CONTENT changes and is
-- silent when only the order moved; and the file is a time series, so the order
-- is recoverable from the sequence of snapshots anyway.
local function snapshot(root)
	if root == nil then return nil end
	local rows = {}
	local ok = pcall(function()
		for _, d in ipairs(root:GetDescendants()) do
			if d:IsA('TextLabel') then
				local t = d.Text
				if type(t) == 'string' and t ~= '' then
					rows[#rows + 1] = d.Name .. '=' .. (t:gsub('%s+', ' '))
				end
			end
		end
	end)
	if not ok then return '<unreadable>' end
	if #rows == 0 then return '<no text>' end
	table.sort(rows)
	local n, out, total = #rows, {}, 0
	for i = 1, n do
		if i > Config.MaxPanelLabels then
			out[#out + 1] = '<' .. tostring(n - Config.MaxPanelLabels) .. ' more>'
			break
		end
		total = total + #rows[i] + 1
		if total > Config.MaxPanelChars then
			out[#out + 1] = '<truncated>'
			break
		end
		out[#out + 1] = rows[i]
	end
	return table.concat(out, '|')
end

-- putText, not put: a snapshot is a string, and the batch-line rule is that no
-- string can ever enter one. Missing panels cost nothing -- putText returns on
-- nil -- so a place whose monitor tree differs records the rest and says not a
-- word about the part it could not find.
local function readPanels()
	putText('log.panel', snapshot(LogPanel))
	putText('fc.panel',  snapshot(FcPanel))
	putText('q.panel',   snapshot(QuotaPanel))
end

-- ========================== ATTRIBUTION ===================================
-- A control that moved with no click behind it. The click hook is client-side
-- and sees only this client s presses, so a second operator in the server moves
-- the plant invisibly: the 18:01 capture holds four CBL level changes and not
-- one CLICK event. That absence is real evidence -- the same hook and the same
-- labels caught twenty CBL clicks in the 15:12 capture -- but it took hours and
-- a reconstruction of the control timeline to find, and it should not.
--
-- The rule is deliberately weak in one direction: a change within
-- AttribWindowPolls of a click this client saw is reported as nothing, because
-- the game applies a click on its own 1 Hz step and a control that moved is
-- most likely the click we already logged. Attribution is only claimed for what
-- cannot be explained that way.
local function reportUnattributed()
	for i = 1, #changedCtrl do
		local rec = changedCtrl[i]
		-- Derived aggregates are skipped: fanCount is the sum of the six fans
		-- that are each already reported, so it would double every fan change
		-- and call one cause two.
		if string.sub(rec.key, -5) ~= 'Count' and string.sub(rec.key, -3) ~= 'Sum' then
			local since = (clickPoll == nil) and nil or (sample - clickPoll)
			if since == nil or since > Config.AttribWindowPolls then
				local how = (since == nil) and 'no click seen yet'
					or ('last click ' .. tostring(since) .. ' polls ago')
				emitEvt('UNATTR', rec.key .. ' ' .. tostring(rec.from) .. '->' ..
					tostring(rec.to) .. ' (' .. how .. ')')
			end
		end
	end
end

-- ========================== THE ONE LOOP ==================================
""", "panels")

# ------------------------------------------------------------ pollOnce -----
src = rep(src, """	if lampDirty then scanLamps() end
	changed = {}
""", """	if lampDirty then scanLamps() end
	changed = {}
	changedCtrl = {}
""", "poll-reset")

src = rep(src, """	readStats()
	readReadouts()
	readLamps()
""", """	readStats()
	readReadouts()
	readLamps()
	readPanels()
""", "poll-readpanels")

src = rep(src, """	lastPoll = now

	-- ---- flow boundary ----
""", """	-- After the batch line, so the change is on the page before the accusation
	-- about it is. The pass reads the list the readers above filled.
	reportUnattributed()

	lastPoll = now

	-- ---- flow boundary ----
""", "poll-attrib")

raw = src.encode("utf-8")
P.write_bytes(raw)

print("wrote %s" % P)
print("  bytes %d -> %d" % (before_bytes, len(raw)))
print("  lines %d" % raw.count(b"\n"))
print("  backslash bytes %d  (must be 0)" % raw.count(0x5C))
print("  long-bracket close %d  (must be 0)" % raw.count(b"]==]"))
print("  CRLF %d  bare LF %d" % (raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")))
