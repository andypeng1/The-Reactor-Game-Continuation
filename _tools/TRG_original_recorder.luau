--!nocheck
-- ===========================================================================
-- The Reactor Game -- ORIGINAL-GAME change recorder, v1.2
--
-- WHERE THIS RUNS: under an executor (injector) attached to the ORIGINAL game.
-- WHAT IT DOES NOT NEED: anything of ours. No ReactorBackend, no Config, no
--   Engine. Every line below either reads instances out of the live DataModel
--   or is plain Roblox API, so it runs in the original unmodified place too.
--
-- THE CONSTRAINT THIS FILE EXISTS TO SATISFY -- user, verbatim:
--   "保存到文件时候一定是有变化才计入，没变化不要收集"
--   A key is written only when its value differs from the last value written
--   for that key. There is deliberately no heartbeat line. A quiet file is the
--   correct output of a quiet reactor, so a thousand samples with nothing
--   happening cost zero bytes.
--
-- It also fixes the two defects of the predecessor sitting on disk as
-- Data/DataCollection.luau, both of which break that same constraint:
--   1. SAMPLE_INTERVAL = 0.5 emitted a full record every half second whether or
--      not anything had changed.
--   2. It appended with  readfile(whole file) .. entry  then  writefile(whole),
--      which is O(n^2) in the number of lines -- a run long enough to be worth
--      recording is a run that gets slow, and then loses data.
--   Here the sink is an in-memory buffer flushed as numbered POST segments, and
--   the no-HTTP fallback writes one file per segment, so no single write is
--   ever proportional to the whole recording.
--
-- SCOPE: exactly one shutdown -> startup flow, then the file is sealed and the
--   collector stops. The boundary is detected automatically from the core state
--   (see the FLOW section), with a manual seal key and an on-screen button.
--
-- OPERATING ITSELF: the DRIVER section presses the switches, so a complete flow
--   can be captured with nobody at the console. It needs one thing the rest of
--   this file does not: the injector s `fireclickdetector`. Without it the
--   driver is off from the first poll and says so on the panel, in the receipt
--   and in the candidate line, and the run falls back to exactly the manual
--   recorder it was before.
--
-- THE ATTEMPT IS SPENT BY HAND, AND IT IS SPENT ONCE: the user reported on
--   2026-09-26 that the core can be switched off and on ONCE. So AutoDrive is
--   false, the driver waits for the panel s DRIVER button, and after that press
--   it never presses a second time -- one shutdown candidate, one startup
--   candidate, one press each, and a press that proves inert ends the run
--   naming the control instead of trying another. Inject while the core is
--   RUNNING: a cold core is refused rather than lit, because the target flow is
--   one shutdown followed by one startup, and a run that spends its startup on
--   the opening has none left for the half it was injected to capture.
--
-- ON BACKSLASHES: there are none in this file, on purpose. Text passing through
--   certain editing tools gets its escape sequences decoded once, which turns a
--   newline escape inside a string literal into a real newline and breaks the
--   syntax with an error that points at the string, not at the tool. So
--   newlines are built with string.char(10) and any string needing a double
--   quote uses single-quote Lua syntax. Same convention as ControlTrigger.
--
-- LINE FORMAT (space separated, one record per line, newline terminated):
--   #  <header / legend, ignored by the reader>
--   B  <sample> <elapsed> <base key=value ...>     -- the one baseline batch
--   S  <sample> <elapsed> <dt> <key=value ...>     -- a change batch
--   EVT<n> <KIND> <rest...>                        -- discrete event, rest is free text
--   PHASE<n> <NAME> t=<elapsed>                    -- flow boundary
--   ##  RECEIPT ...                                -- last line; seal + integrity
--
--   `sample` is this collector s own counter, one per poll, and it is strictly
--   increasing in a clean file. It is NOT gap free: a poll with nothing to
--   report emits no line, which is the entire point. The gap free oracle in
--   this format is the EVT id, which never skips.
--
--   Named keys in a batch: r.*=reactor readouts  m.*=monitor parsed
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
-- ===========================================================================

-- ========================== CONFIG ========================================
-- Every magic number lives here, so no literal appears in the logic.
local Config = {
	-- Four polls per second. The game itself ticks at 1 Hz, so polling at 1 Hz
	-- would occasionally straddle a tick and lose one outright, while the change
	-- filter means over-polling costs CPU and not one byte of output.
	-- Over-polling is free; under-polling is data loss. Hence 4 Hz, not 1 Hz.
	SampleInterval  = 0.25,
	FlushBytes      = 48 * 1024,
	FlushSeconds    = 2,       -- max seconds of real data at risk in the buffer
	MaxBufferBytes  = 512 * 1024,
	MaxPostFails    = 12,      -- consecutive; after this the sink falls to disk
	MaxRetryWait    = 0.5,     -- ceiling on the retry backoff, in seconds
	MaxPairsPerLine = 240,     -- a mass change is split across lines, never cut
	SettleSamples   = 24,      -- keep recording this long after the restart
	DebounceSamples = 3,       -- a state must hold this many polls to count
	MaxSamples      = 14400,   -- hard cap, one hour at 4 Hz
	MaxLampParts    = 20000,   -- refuse to scan an absurd Consoles tree
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
	-- Readout-chatter guard, two arms, both judged EARLY.
	--
	-- A label that changes on almost every poll is not a readout, it is an
	-- animation, and left alone it destroys the property that makes this file
	-- readable at all. The threshold is not a taste: the game ticks at 1 Hz and
	-- the poll runs at 4 Hz, so a value that is really a value can change on at
	-- most ~25% of polls. 50% therefore has a factor of two of headroom over the
	-- fastest legitimate readout and still condemns an animation on sight.
	--
	-- The first version judged once, after 240 polls (a full minute), and the
	-- minute cost 39,975 TEXT events and 8 MB -- one GlitchFrame label alone
	-- accounting for 1.1 MB -- before it said a word. Worse, it never said a
	-- word at all: see the note on readoutStats for why the counter it tested
	-- could not move. 8 polls is 2 seconds.
	ChatterPolls    = 8,
	ChatterPercent  = 50,
	-- The rate arm. A key that emits more than this within ONE poll is not a
	-- value moving, it is a screen either animating or being rebuilt: measured on
	-- the first readout-sweep run at 29.5 emissions in a single poll from one
	-- key, which no downstream deduplication can undo because the reads sit
	-- either side of a yield and see different text.
	AnimChangesPerPoll = 4,
	Port            = 8765,
	NamePrefix      = 'flow/original_',
	CoreThresholds  = {5600, 17500, 29500, 39000},  -- the game s own, Fahrenheit
	-- The two temperature lines that END a shift, both reported by the operator
	-- and neither one guessed.
	--
	-- LowTripF is the cold trip: below it the core shuts itself down. That is
	-- why a shift has a floor to stay off, and why a control that RAISES
	-- temperature is the thing most likely to end a run early.
	-- MeltdownF is the hot trip, and the operator is explicit that it is the ONLY
	-- meltdown condition: no time limit, no second cause. It coincides with the
	-- top of CoreThresholds above, which is the game s own boundary and not a
	-- coincidence -- the game announces the band, this is the line inside it.
	--
	-- MeltdownF IS ABOUT THE CORE, AND `s.MainframeMeltdown` IS NOT. These were
	-- conflated in this file until the operator separated them: that flag is the
	-- MACHINE ROOM s meltdown and says nothing about the core. The 18:35 run is
	-- the measurement that makes the difference visible -- the flag went true at
	-- t=719.86 while the monitor temperature read about 13000 F, which is nowhere
	-- near this line. Under the old label the file claimed a 39000-degree core
	-- meltdown it had never seen. So the flag now seals as what it is (see
	-- endReason) and the core rule here is read from the temperature itself,
	-- which is the only thing that can witness it.
	LowTripF        = 2000,
	MeltdownF       = 39000,
	NeonOn          = {240, 240, 240},              -- lamp lit, per the wiki
	SealKey         = Enum.KeyCode.RightShift,

	-- ---- driver -------------------------------------------------------------
	-- See the DRIVER section for what these mean and why the driver exists at
	-- all. The numbers are judgements, so they are here where they can be
	-- changed without touching logic.
	-- AutoDrive is FALSE, and the default is the point rather than a safe
	-- setting. An action that can be spent once is not one a recorder takes the
	-- instant it is injected; the DRIVER button is the gate, and the human at
	-- the console is who decides when the single attempt begins. Everything
	-- AFTER that press is unattended, which is the part that needed a machine:
	-- nobody can hit a lever at the right second for three minutes running.
	AutoDrive        = false,  -- arm by hand; the button spends the attempt
	-- ---- the driver presses NOTHING ----------------------------------------
	-- THE OPERATOR DRIVES, THE DRIVER WATCHES AND NARRATES. This is the flag
	-- that says so, and it is the live setting.
	--
	-- `D7: 我自己手动关` -- the shutdown is the operator s own press. The
	-- startup is his too: the recorder is injected on a COLD core before the
	-- shift has begun, and `A1` has the operator lighting it himself and arming
	-- the driver only once it is up. So the driver is handed no control to
	-- press, and a press it does not need is a press it must not invent.
	--
	-- What is left is the half that actually needed a machine, and it is not a
	-- small half: noticing WHICH poll the operator s press landed in, and
	-- recording the game s own reaction to it, is what makes the two halves of
	-- the experiment comparable in one file. The operator s press is already
	-- stamped by the CLICK hook; what this state adds is the state transition
	-- and the verdict, so the file says "the operator shut it down and here is
	-- when" rather than leaving a reader to infer it from a click line.
	--
	-- The press path is NOT deleted -- §1.4 forbids deleting a capability
	-- without a replacement, and there is no replacement for a press this file
	-- may one day be asked to make. It stays behind this flag, reachable by
	-- changing one constant, and the harness exercises it in both positions.
	DrivePressControls = false, -- false: the operator presses, the driver watches
	DriveArmSeconds  = 20,     -- still cold this long after inject -> the core was cold
	DriveHoldSeconds = 60,     -- run this long before switching it off
	-- THE SHUT HAS NO PROOF WINDOW, BECAUSE IT NEEDS NONE. The operator is
	-- explicit that pressing the shutdown lever shuts the core down AT ONCE --
	-- there is no cold state to wait for -- so the press IS the shutdown and the
	-- driver acts on it in the same poll. `DriveProveF` used to sit here and is
	-- gone; see the PROVING section for the measurement that killed it.
	--
	-- The start keeps a window, because there the state change is the core
	-- ARRIVING, and arriving at a threshold is something the readout can be asked
	-- about. `DriveProveSeconds` is that window and it is wide on purpose: a core
	-- that lights proves itself in seconds, and a window that expires early would
	-- end the run with a wrong verdict and nothing left to spend on a right one.
	DriveProveSeconds = 40,    -- a start press has this long to light the core
	DriveColdSeconds = 30,     -- stay down this long before lighting it again

	-- ---- end of shift -------------------------------------------------------
	-- A shift ends the moment the core goes down. The operator is explicit: a
	-- shutdown ends the shift whether the quota was met or not, and the session
	-- cannot be continued afterwards. Two consequences, and both are structural
	-- rather than cosmetic.
	--
	-- First, there is nothing after the shutdown to record, so the driver has no
	-- reason to light the core again -- and it must not, because it would spend
	-- the one switch that exists on a world action nobody asked for, seconds
	-- before the client is killed. ShutdownEndsShift stops the driver at
	-- shut_down, the very poll its press lands in, and the recorder s own
	-- end-of-shift rule is what seals the file.
	--
	-- That the press ends it immediately is the operator s answer and not an
	-- inference: pressing the shutdown lever shuts the core down at once, and
	-- there is no cold state that has to arrive first. So the driver has nothing
	-- to wait for between the press and the end, and it does not wait for one.
	--
	-- Note what this does NOT do. It does not remove the driver s ability to
	-- light a core; the operator asked for that ability explicitly, and it is
	-- now entered from `arming` when the core reads cold. What it removes is
	-- only the RELIGHT -- the second startup, after the shutdown, which in this
	-- game is a startup that happens after the shift has already ended.
	--
	-- Second, THE FILE MUST BE SEALED BY SOMETHING THAT NOTICES THE END, because
	-- the client does not wait to be told. The 18:35 run is the measurement:
	-- s.GameActive went false on the very last sample the script ever took, the
	-- loop had no rule that looked at it, and the task.wait that followed never
	-- returned. 1.4 MB of good data with no receipt, lost to a missing if.
	ShutdownEndsShift = true,
	-- Seal targets, in polls at the configured rate. GameActive false gets no
	-- dwell at all: it is checked first, in the same iteration that saw it, and
	-- it is checked by EDGE so a session that starts with the flag already false
	-- cannot seal itself at inject. The others are backstops, and both are gated
	-- on the core having RUN: a shift opens with the core cold, and a cold core
	-- sits below LowTripF by definition -- without that gate the cold-trip rule
	-- would fire on the first two seconds of every run and seal a file that had
	-- not recorded anything yet.
	SealColdSamples   = 8,     -- 2 s under LowTripF, after the core has run
	-- The hot arm, and the dwell is not a taste either. It is the core meltdown
	-- rule the operator gave (`A2`: over MeltdownF and nothing else), and it now
	-- has to be read from the temperature because the flag that used to stand in
	-- for it is the machine room s. The core is the one thing in this plant that
	-- cannot be got wrong cheaply, so the arm waits two seconds before declaring
	-- it -- long enough that a single bad readout is not a verdict, short enough
	-- that it costs nothing on a real meltdown.
	SealHotSamples    = 8,     -- 2 s over MeltdownF, after the core has run
	SealDownSamples   = 40,    -- 10 s held down with no end signal: last resort
	SealDeadSamples   = 40,    -- 10 s of GameActive false with no edge seen
	-- Panel snapshots are coalesced to at most one per this many polls. A panel
	-- is emitted on change, and one of them changes on almost every poll because
	-- a news ticker in it is revealed one character at a time: 728 of 2490 polls
	-- in the 18:35 run, 29 per cent of the file, for text that is identical
	-- whenever it finishes arriving. This does not DROP the suppressed changes --
	-- the comparison is against the last snapshot that was actually emitted, so
	-- a change held back stays pending and goes out the moment the gap allows,
	-- and the text as it finally settles is always the last thing written.
	PanelMinGapPolls  = 8,     -- 2 s
}

-- Palette for the compact lamp code string: one character per lamp state, so a
-- whole console subsystem of lamps is one short token on one line. It encodes
-- the colour rather than a lit/unlit bit on purpose -- a lamp that gains a third
-- colour later (amber, red) must not silently fold into "unlit".
local PALETTE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

local NL          = string.char(10)
local Players     = game:GetService('Players')
local Workspace   = game:GetService('Workspace')
local HttpService = game:GetService('HttpService')

-- ========================== RUNTIME CLOCK =================================
-- Declared here, above everything that reads them. Lua resolves a free name at
-- the point the function is COMPILED, so a local declared further down the file
-- is not visible to a function above it -- that name would silently become a
-- global reading nil, and the two halves of the file would be using different
-- variables while looking identical. Each of these was exactly that bug once.
local t0 = os.clock()
local now = t0
local lastPoll = t0
-- How long the previous poll really took, measured by the loop rather than
-- assumed from Config.SampleInterval. The driver advances its dwell timers by
-- this, so that the seconds it announces are the seconds that elapsed: the 18:01
-- run announced 60 s and spent 70.59, because the loop ran at 3.38 Hz against a
-- configured 0.25 s and every dwell was 18 per cent long. Declared here with the
-- rest of the clock for the usual reason -- the loop below assigns it and
-- driveStep, compiled earlier than that assignment, has to see the same name.
local pollDt = Config.SampleInterval
local sample = 0
local sawDown = false
local flowArmed = false
local buoy = {}          -- shared with the seal key and the on-screen button

-- The driver s state, forward declared for the same reason as the clock above:
-- seal() writes the driver s verdict into the receipt line, and seal() is
-- compiled before the DRIVER section exists. Filling this table later is fine;
-- reading a name that is not yet a local is not.
local drive = {
	on      = false,   -- turned on by the DRIVER section if the injector can fire
	state   = 'arming',
	verdict = 'not-started',
	holdT   = 0,
	coldT   = 0,
	armT    = 0,
	proofT  = 0,
	proofCd = nil,
	-- What the core was doing at the instant of the press, and the START proof is
	-- the only thing left that needs it: "not running now" and "not running now
	-- AND running then" are two different facts, and only the second one is
	-- evidence about the press. The shutdown proof that also used it is gone --
	-- see PROVING for why it could not have been evidence about anything.
	proofRunning = nil,
	-- Set while press_shut is declining to press because the core is already
	-- down. It exists so the wait is announced once instead of on every poll.
	waitingRun = false,
	-- The same latch for the other configuration: armed on a cold core with no
	-- licence to press, the driver has nothing to do but wait for the operator,
	-- and it has to say so once rather than on every poll.
	waitingCold = false,
	-- The end-of-shift signal that has already been written down, as the exact
	-- text the file carries for it. It is what stops the confirmation in
	-- `shut_down` from naming the same signal twice: `watching` fires on the
	-- FIRST signal it sees, and `shut_down` then goes looking again, so without
	-- this the very signal that ended `watching` would be reported a second time
	-- one poll later as if it were the game s answer to something.
	--
	-- The two states search in DIFFERENT orders on purpose, and that is what
	-- makes this work rather than merely dedupe: `watching` puts the operator s
	-- own press screen first (`v.shutdown`, the one `B3` named), while
	-- `shut_down` puts the game s formal flags first. So a signal that arrives
	-- later always outranks its way to the front and is found, while the signal
	-- that already fired is found only if nothing else has appeared -- which is
	-- exactly the test for whether there is anything new to say.
	shutSaid = '',
	shutIdx = 1,
	startIdx = 1,
	-- Whether THIS driver ever switched the core off. It is the only thing that
	-- distinguishes the two ways a run can reach a lit core: one where the
	-- driver shut it down and is waiting for the flow to close, and one where
	-- the core was cold at inject and the driver only lit it. Without this,
	-- the cold path parks in `waiting_up` waiting for a `sawDown` that is never
	-- going to come, and the run records a healthy reactor until the sample cap.
	shutDone = false,
}

-- ========================== SINK ==========================================
-- The one place bytes leave this script. Everything that lands on disk or on
-- the wire is produced by emit(), so the running hash and the counters cannot
-- drift away from the payload the way they can when two paths both write.
local buf, bufBytes, bufLines = {}, 0, 0
local segNo, postFails, spilled, dropped = 0, 0, 0, 0
local lines, evtNo, phaseNo = 0, 0, 0
local kinds = {}
local hash = 5381
local diskFallback = false

local stamp = os.date('%y%m%d-%H%M%S')
do
	local ok, res = pcall(os.date, '%y%m%d-%H%M%S')
	if ok and type(res) == 'string' then stamp = res end
end
local NAME = Config.NamePrefix .. stamp

-- djb2 over a string. Kept in the 32 bit domain by reducing after every step:
-- the largest intermediate is 2^32 * 33 + 255, far below 2^53, so doubles hold
-- it exactly and the result is identical to the same loop in Python. Compared
-- by hash and never by length -- this project has already had two payloads of
-- identical length and different content, and a length check called both fine.
local function djb2(h, s)
	for i = 1, #s do
		h = (h * 33 + string.byte(s, i)) % 4294967296
	end
	return h
end

local function hex8(n)
	return string.format('%08x', n)
end

-- Executor HTTP is not a Roblox API and every executor names it differently.
-- The candidates are stored as thunks, not as values in an array: a table
-- literal holding nils would stop ipairs at the first nil and silently skip
-- every candidate behind it.
local function pickHttp()
	local cands = {
		function() return syn and syn.request end,
		function() return http_request end,
		function() return request end,
		function() return http and http.request end,
		function() return fluxus and fluxus.request end,
		function() return krnl and krnl.request end,
		function() return getgenv and getgenv().request end,
		-- Last, and deliberately so. HttpService:PostAsync is not an executor
		-- function and a plain client is not allowed to call it -- it raises at
		-- once, the pcall turns that into a failed send, and the sink falls
		-- through to the disk path. It is in the list because a server side
		-- executor, and the probes this project already uses to move bytes out
		-- of Studio, do have it and nothing else. It takes positional arguments,
		-- so it is wrapped into the same request-table shape as the rest.
		function()
			if HttpService == nil or HttpService.PostAsync == nil then return nil end
			return function(req)
				local ok = pcall(HttpService.PostAsync, HttpService, req.Url, req.Body)
				if ok then return { StatusCode = 200 } end
				return { StatusCode = 0 }
			end
		end,
	}
	for _, get in ipairs(cands) do
		local ok, f = pcall(get)
		if ok and type(f) == 'function' then return f end
	end
	return nil
end
local httpFn = pickHttp()

local function haveWritefile()
	return type(writefile) == 'function'
end

-- One segment, sent. True only on a 2xx, because the caller keeps the bytes on
-- anything else -- an unconfirmed send is not a send.
local function postSegment(text)
	if not httpFn then return false end
	local url = 'http://127.0.0.1:' .. tostring(Config.Port) .. '/' .. NAME .. '?mode=a'
	local ok, res = pcall(httpFn, {
		Url = url, Method = 'POST', Body = text,
		Headers = { ['Content-Type'] = 'text/plain' },
	})
	if not ok or type(res) ~= 'table' then return false end
	local code = res.StatusCode or res.Status or res.statusCode
	return code == 200 or code == 201 or code == 204
end

-- Fallback sink: one file per segment. Each write is O(this segment), never
-- O(everything so far) -- that is the defect that sank the predecessor.
local function diskSegment(text)
	if not haveWritefile() then return false end
	segNo = segNo + 1
	local ok = pcall(writefile, NAME .. '.' .. tostring(segNo) .. '.part', text)
	if ok then return true end
	-- Some executors refuse a path whose directory does not exist yet.
	local ok2 = pcall(writefile, stamp .. '.' .. tostring(segNo) .. '.part', text)
	return ok2
end

-- One POST in flight, ever. flush() yields inside postSegment, and emit() is
-- reachable from a ClickDetector callback -- which Roblox runs on its own
-- event thread, not on the poll coroutine -- so a second flush can start while
-- the first is still in the air. The sink is a ThreadingTCPServer that appends
-- each body as it arrives, so two bodies in flight are written in COMPLETION
-- order, which is not send order.
--
-- Measured 2026-09-26 on run original_260926-155619. The click on
-- HDEF-PowerLever was emitted as EVT2147 while the poll coroutine sat yielded
-- inside the flush carrying EVT2146; its own 30 byte segment overtook the
-- poll's, and one adjacent pair arrived swapped. Not a byte was lost -- 2222
-- events, 2222 distinct ids, 0 repeated -- but the byte ORDER differed, so the
-- recorder's own djb2 no longer matched the file and a recording that is
-- complete failed its integrity check over a transposition. The guard costs a
-- boolean and makes the wire order the buffer order.
--
-- `waitForTurn` is for the seal path only: a receipt left in the buffer because
-- a flush happened to be in flight is a recording with no RECEIPT line, which
-- reads exactly like a truncated file. Bounded, because waiting forever on an
-- unbudgeable sink is worse than sealing late.
local flushing = false

-- Takes the buffer, hands it to whichever sink is live, and puts the bytes back
-- if the send did not confirm. The buffer is swapped out before any yield, so
-- the sampler keeps filling a fresh table while the POST is in flight: nothing
-- is lost.
--
-- It does NOT follow that nothing is sent twice. A POST that the sink received
-- but whose response was lost looks identical to a failed send, so the bytes go
-- back into the buffer and go out again, and the file holds them twice. Nothing
-- in this protocol can prevent that, because the bodies carry no sequence
-- number for the sink to dedupe on -- so it is DETECTED instead of prevented:
-- every event carries an id from one counter, and _tools/verify_original_flow.py
-- reports repeated ids by name. Trust a recording because the audit says
-- missing=0 repeated=0, not because the sender believed it succeeded.
local function flush(waitForTurn)
	if flushing then
		if not waitForTurn then return end
		local waited = 0
		while flushing and waited < 5 do
			task.wait(0.05)
			waited = waited + 0.05
		end
		if flushing then return end
	end
	local text = table.concat(buf)
	if #text == 0 then return end
	local swappedLines = bufLines
	buf, bufBytes, bufLines = {}, 0, 0

	flushing = true
	local sent = false
	if not diskFallback then
		sent = postSegment(text)
		if sent then
			postFails = 0
		else
			postFails = postFails + 1
			if haveWritefile() and postFails >= Config.MaxPostFails then
				diskFallback = true
				print('[rec] HTTP refused ' .. tostring(postFails) ..
					' times in a row; sinking to files from here on')
			end
		end
	end
	if not sent then sent = diskSegment(text) end
	flushing = false

	if sent then
		-- Counted here, on BOTH paths. It used to be incremented only inside
		-- diskSegment, so a run that sent everything over HTTP reported
		-- segments=0 in its own receipt -- a counter that disagrees with the
		-- receiver's log is a counter that cannot be used to check anything.
		--
		-- The number in the receipt is therefore ONE LESS than the sink logs,
		-- every time, because the receipt states it before the flush that
		-- carries the receipt itself. Measured on both 2026-09-26 runs: the
		-- receipts say 144 and 20, the sink logged 145 and 21.
		segNo = segNo + 1
		print('[rec] SEG ' .. tostring(segNo) .. ' ' .. tostring(#text) ..
			' ' .. hex8(djb2(5381, text)))
		return
	end

	-- Nothing took those bytes. Re-insert WITHOUT recomputing the hash: they
	-- were hashed when they were emitted, and hashing them twice would break
	-- the receipt comparison. Re-inserting keeps the change filter honest too,
	-- since last[key] already records these values as written.
	table.insert(buf, 1, text)
	bufBytes = bufBytes + #text
	bufLines = bufLines + swappedLines

	-- Yield, with backoff, before the next attempt. flush() is called
	-- synchronously from emit(), so without this the retry fires in the same
	-- instant the send failed -- in a burst, thousands of times -- and a sink
	-- that merely fell behind for a moment never gets the gap it needs to catch
	-- up. At that point the refusals stop being a symptom of the backlog and
	-- become the cause of it. Measured on the first readout-sweep run: 849
	-- segments delivered, then 2123 consecutive refusals, while the sink
	-- answered 20/20 posts in 0.35 s the moment the storm stopped.
	--
	-- postFails is the CONSECUTIVE-failure counter (it is reset on every
	-- success), so it is exactly the right exponent here, and the cap keeps one
	-- unbudgeable sink from stalling the sampler behind it.
	task.wait(math.min(0.05 * math.max(postFails, 1), Config.MaxRetryWait))

	if bufBytes > Config.MaxBufferBytes then
		local spill = table.concat(buf)
		buf, bufBytes, bufLines = {}, 0, 0
		if diskSegment(spill) then
			spilled = spilled + 1
		else
			-- Nothing anywhere accepted these bytes. Say so, do not pretend.
			dropped = dropped + #spill
		end
	end
end

-- The single writer. Every byte of the recording passes through here, so the
-- running hash always describes exactly what the file will contain.
-- `total` counts every byte hashed, exactly once. It is not the same as
-- bufBytes: a segment that fails to send is re-inserted into the buffer, so its
-- bytes are buffered twice and hashed once. The receipt publishes `total` next
-- to the hash so the coverage of the hash is stated rather than assumed.
local total = 0
local function emit(line)
	local rec = line .. NL
	lines = lines + 1
	total = total + #rec
	hash = djb2(hash, rec)
	buf[#buf + 1] = rec
	bufBytes = bufBytes + #rec
	bufLines = bufLines + 1
	if bufBytes >= Config.FlushBytes then flush() end
end

-- Rate limiter for forced flushes, keyed on the poll counter rather than a
-- clock: `sample` advances once per poll and a poll is one game tick (1 gt =
-- 1 s), so it is already the cadence this whole file is written in. That makes
-- the rule exact -- at most one forced flush per tick -- and it costs no clock
-- call. `now` would have worked, but only because it happens to be declared
-- above this point; a limiter whose correctness depends on a declaration ORDER
-- is one edit away from reading nil, so it does not use `now`.
local lastForcedSample = -1

-- Discrete event with a free-text tail. The tail is everything after the fixed
-- tokens, so it may contain spaces and needs no escaping.
local function emitEvt(kind, rest)
	evtNo = evtNo + 1
	kinds[kind] = (kinds[kind] or 0) + 1
	if rest == nil then
		emit('EVT' .. tostring(evtNo) .. ' ' .. kind)
	else
		emit('EVT' .. tostring(evtNo) .. ' ' .. kind .. ' ' .. tostring(rest))
	end
	-- An event is the thing a reader most wants to see promptly, so an event
	-- asks for a flush -- but at most once per poll. Forcing one every time was
	-- measurably wrong: the baseline sweep emits one TMAP per discovered
	-- readout, so a 1115-label console tree became 1115 one-line POSTs fired
	-- back to back before the game had done anything at all. No bytes were lost
	-- (a send that does not confirm is put back in the buffer and merged into
	-- the next one), but the run spent its opening minutes draining a manifest
	-- one line at a time, and the receipt read postfails=2123 -- which looks
	-- like a dead sink and was really just this.
	--
	-- The rest of the burst is not abandoned: emit() flushes on FlushBytes, so
	-- it leaves as a handful of full segments instead of a thousand stubs.
	if lastForcedSample ~= sample then
		lastForcedSample = sample
		flush()
	end
end

local function emitPhase(name, note)
	phaseNo = phaseNo + 1
	kinds['PHASE'] = (kinds['PHASE'] or 0) + 1
	emit('PHASE' .. tostring(phaseNo) .. ' ' .. name ..
		' t=' .. string.format('%.2f', now - t0) ..
		( note and (' ' .. note) or ''))
	flush()
end

-- A handle, published so the tool can be driven without editing it. An injector
-- script whose only way out is a keypress is a script that gets stopped by
-- closing the executor, and stopping it that way loses whatever is still in the
-- buffer. This also gives the tool a control surface for a probe or a test rig.
local REC = {
	seal   = function() buoy.unseal = true end,
	flush  = function() flush(true) end,
	setName = function(n) NAME = tostring(n) end,
	setPort = function(p) Config.Port = tonumber(p) or Config.Port end,
	status = function()
		return {
			name = NAME, sample = sample, lines = lines, segments = segNo,
			bytes = bufBytes, postFails = postFails, spilled = spilled,
			dropped = dropped, events = evtNo,
			phase = (not flowArmed) and 'pre' or (sawDown and 'down' or 'run'),
			transport = (httpFn ~= nil) and 'http' or (haveWritefile() and 'file' or 'none'),
		}
	end,
}
do
	local ok, pub = pcall(function()
		return (type(getgenv) == 'function') and getgenv() or _G
	end)
	if ok and type(pub) == 'table' then pub.TRGRec = REC end
end

-- ========================== CHANGE TRACKER ================================
-- last[key] holds the last value WRITTEN for that key, not the last value seen.
-- The difference matters after a failed send: those values are still sitting in
-- the buffer, so they already count as recorded and must not be re-emitted.
local last = {}
local changed = {}

-- The control changes of the poll just finished, with the value each came FROM,
-- and the poll at which this client last saw a click. Both feed the attribution
-- pass; both are cleared once per poll, in pollOnce, beside `changed`.
local changedCtrl = {}
local clickPoll = nil

-- Numbers and booleans only. A batch line is space separated, and a string with
-- a space in it would silently become two tokens, so strings are routed to
-- putText and land as their own line where the tail is free text. This is a
-- structural guarantee rather than a convention: no code path can put a string
-- into a batch line.
local function put(key, value)
	if value == nil then return end
	local t = type(value)
	if t ~= 'number' and t ~= 'boolean' then return end
	if last[key] == value then return end
	-- Recorded with the value it came FROM, because `c.cbl1Lvl 2->1` is what an
	-- attribution report has to say and `c.cbl1Lvl=1` is not. Read before the
	-- assignment below, which is the only place the old value still exists.
	if string.sub(key, 1, 2) == 'c.' then
		changedCtrl[#changedCtrl + 1] = { key = key, from = last[key], to = value }
	end
	last[key] = value
	changed[#changed + 1] = key .. '=' .. tostring(value)
end

local function putText(key, text)
	if text == nil then return end
	if last[key] == text then return end
	last[key] = text
	emitEvt('TEXT', key .. ' ' .. tostring(text))
end

-- ========================== DISCOVERY =====================================
-- Every lookup is tolerant. The predecessor did
--   listenClick(game.Workspace.Consoles.MainReactorConsole.AtmosphereVentButton.ClickPart, ...)
-- and so would die at load time on one renamed button, recording nothing at all
-- for the rest of the session. A recorder that stops on a name change is worse
-- than one that records a path where it wanted a label.
local function child(parent, ...)
	local cur = parent
	for i = 1, select('#', ...) do
		if cur == nil then return nil end
		cur = cur:FindFirstChild((select(i, ...)))
	end
	return cur
end

local ReactorFrame
do
	local mf = Workspace:FindFirstChild('MonitorsFacility')
	if mf then
		for _, dm in ipairs(mf:GetChildren()) do
			if dm.Name:find('DisplayMonitor') then
				local frame = child(dm, 'Monitor', 'Screen', 'ReactorMonitoring', 'MainMonitorFrame')
				if frame then ReactorFrame = frame break end
			end
		end
	end
end

local ThermalConsole = child(Workspace, 'Consoles', 'ThermalConsole')
local MainConsole    = child(Workspace, 'Consoles', 'MainReactorConsole')
local CBLConsoles    = child(Workspace, 'Consoles', 'CBLaserConsole')
local FanFrame       = child(Workspace, 'Monitors', 'ThermalControlRoomMonitor',
	'Screen', 'MonitorUI', 'MainMonitorFrame', 'FanFrame')
local PowerFrame     = child(Workspace, 'Monitors', 'PowerControlRoomMonitor',
	'Screen', 'MonitorUI', 'MainMonitorFrame')
local LogsFrame      = child(Workspace, 'Monitors', 'LogControlRoomMonitor',
	'Screen', 'MonitorUI', 'MainMonitorFrame', 'LogsFrame')
local MainData       = Workspace:FindFirstChild('Stats')

-- ========================== READERS =======================================
local function readLabel(key, parent, name)
	local label = parent and parent:FindFirstChild(name)
	if label == nil then return end
	local raw = label.Text
	if type(raw) ~= 'string' then return end

	local num = nil
	if raw ~= '' then num = tonumber(raw:match('([+-]?%d+%.?%d*)')) end

	local tkey = 'x.' .. key
	if num ~= nil then
		put('m.' .. key, num)
		-- Leave the unreadable state behind without emitting anything: `last`
		-- going nil means "unknown", so the next unreadable sample reports.
		last[tkey] = nil
	else
		-- Unreadable: ERR, blank, a placeholder. That is a state the number
		-- cannot express -- ERR and a real zero are different things -- and the
		-- sensors in this game are documented as tending to fault, so it is
		-- recorded in its own right, once per transition rather than per tick.
		putText(tkey, raw == '' and '<empty>' or (raw:gsub('%s+', ' ')))
	end
end

-- ==================== READOUT DISCOVERY ==================================
-- The names in readReactor below were read off the remake, and seven of the ten
-- are simply not what the original calls its labels: TempLabel, PressureLabel
-- and FluctuationLabel resolve, while OutputLabel, RadiationLabel, HDEFLabel,
-- StressLabel, ExtractionLabel, IntegrityLabel and StabilityLabel do not. Most
-- of those quantities are covered by Workspace.Stats anyway -- but not the one
-- that matters most, the stability readout on the calibration console, and
-- there is no way to learn a name from outside the game except by reading it
-- out of the game.
--
-- So this does not guess a second time. It walks every TextLabel under the
-- monitors, and every *Label under the consoles (a console is otherwise full of
-- static button captions, and the game names its readouts ...Label), and keys
-- each one by its own name. The key -> full path mapping ships as a TMAP event
-- the first time a key is seen, the same way LAMPMAP does for the lamps, so a
-- change line stays short and the file is still decodable on its own.
--
-- The explicit reads are deliberately kept for the labels that DO resolve:
-- m.temp keeps this recording comparable with the first one, t.<key> reveals
-- the real vocabulary. Two aliases of one label is not two writers -- nothing
-- in this block writes game state.
local readouts = {}
local readoutKeys = {}
local readoutDirty = true
local readoutCount = 0
local readoutDistinct = 0

-- Guard state lives HERE, keyed by the readout's own key -- deliberately not on
-- the record object, which is where it started and where it was useless. The
-- monitors implement their glitch animation by destroying and recreating the
-- screen's labels, so every rebuild sets readoutDirty, every rebuild builds
-- FRESH records, and a fresh record begins at polls=0, changes=0, dead=false.
-- The guard's verdict therefore needed an unbroken run of polls, and the
-- animation reset its clock several times a second: measured at 424 polls with
-- the file growing at 543 lines a second and not one NOISY event emitted, i.e.
-- the guard was working perfectly on a counter that was being wiped from
-- underneath it. A statistic about a key belongs to the key, not to whichever
-- table cell happens to hold a reference to it this second.
--
-- There was a second and independent reason it could never fire, and it is the
-- one this file already warns about in its own notes on the `segments` counter:
-- `polls` was incremented inside the numeric branch only. A label whose text is
-- not a number -- which is every animation in the list -- therefore left `polls`
-- at 0 forever and could never equal the threshold. A counter incremented on one
-- of two paths is a counter that reports zero.
local readoutStats = {}

local function keyForLabel(label, seen)
	-- Try the shortest suffix of the ancestry that is unique: parent.Name alone
	-- first, then grandparent, and so on. Two consoles can both own a TempLabel
	-- and dropping one of them silently would be the exact failure this block
	-- exists to prevent, so the walk deepens until the key is free.
	for depth = 2, 7 do
		local node, parts = label, {}
		for _ = 1, depth do
			if node == nil then break end
			table.insert(parts, 1, node.Name)
			node = node.Parent
		end
		local k = table.concat(parts, '.')
		if not seen[k] then return k end
	end
	return label:GetFullName()
end

local function buildReadouts()
	local seen, seenLabel, out = {}, {}, {}
	local function add(label)
		-- One label, one record. Both walks below are flat GetDescendants passes
		-- and cannot reach the same label twice, so this is a guard rather than a
		-- fix -- but the same label arriving through two different roots WOULD
		-- arrive twice, and a duplicate is not a harmless extra line: each copy
		-- holds its own dedup state, so a duplicate re-emits a change the first
		-- copy already reported.
		if seenLabel[label] then return end
		seenLabel[label] = true
		local key = keyForLabel(label, seen)
		seen[key] = true
		out[#out + 1] = { key = key, label = label }
	end
	local mf = Workspace:FindFirstChild('MonitorsFacility')
	if mf then
		for _, d in ipairs(mf:GetDescendants()) do
			if d:IsA('TextLabel') then add(d) end
		end
	end
	local mon = Workspace:FindFirstChild('Monitors')
	if mon then
		for _, d in ipairs(mon:GetDescendants()) do
			if d:IsA('TextLabel') then add(d) end
		end
	end
	local consoles = Workspace:FindFirstChild('Consoles')
	if consoles then
		for _, d in ipairs(consoles:GetDescendants()) do
			if d:IsA('TextLabel') and string.sub(d.Name, -5) == 'Label' then add(d) end
		end
	end
	readouts = out
	readoutCount = #out
	-- Records and distinct keys are counted separately and both reported, because
	-- "1115 records over 1115 keys" and "1115 records over 1086 keys" are
	-- different findings -- the second says something is adding the same label
	-- twice, and that is not visible from the record count alone.
	local nextKeys, distinct = {}, 0
	for _, rec in ipairs(readouts) do
		if not nextKeys[rec.key] then distinct = distinct + 1 end
		nextKeys[rec.key] = true
	end
	readoutDistinct = distinct
	-- A manifest line per key, once. Emitted before the first sample that uses
	-- the key, because a key that appears in a change line with no manifest
	-- anywhere in the file is a number nobody can attribute.
	for _, rec in ipairs(readouts) do
		if not readoutKeys[rec.key] then
			emitEvt('TMAP', rec.key .. ' ' .. rec.label:GetFullName())
		end
	end
	readoutKeys = nextKeys
	readoutDirty = false
end

local function readReadouts()
	if readoutDirty then buildReadouts() end
	for _, rec in ipairs(readouts) do
		local st = readoutStats[rec.key]
		if st == nil then
			st = { polls = 0, changes = 0, thisPoll = 0, dead = false }
			readoutStats[rec.key] = st
		end
		if not st.dead then
			-- Read once and reuse. A second read is not a second opinion: this
			-- loop yields inside flush, the game writes these labels from its own
			-- frame loop, so reading again after the yield returns a value the
			-- first read never saw -- which is how one key came to emit 29.5
			-- times in a single poll.
			local raw = rec.label.Text
			if type(raw) == 'string' then
				local num = nil
				if raw ~= '' then num = tonumber(raw:match('([+-]?%d+%.?%d*)')) end
				local key = (num ~= nil) and ('t.' .. rec.key) or ('x.' .. rec.key)
				local clean = raw == '' and '<empty>' or (raw:gsub('%s+', ' '))
				local shown = (num ~= nil) and num or clean

				st.polls = st.polls + 1
				st.thisPoll = st.thisPoll + 1
				if last[key] ~= shown then st.changes = st.changes + 1 end

				-- The rate arm goes first because it is the arm that bounds the
				-- damage: it costs this key at most AnimChangesPerPoll lines and
				-- then the key is gone, inside the same poll that caught it.
				if st.thisPoll > Config.AnimChangesPerPoll then
					st.dead = true
					emitEvt('ANIM', rec.key .. ' moved ' .. tostring(st.thisPoll) ..
						' times inside one poll; dropped as an animation')
				else
					if num ~= nil then
						put('t.' .. rec.key, num)
						last['x.' .. rec.key] = nil
					else
						putText('x.' .. rec.key, clean)
					end
					-- The persistence arm, and judged exactly once, so a label
					-- that happened to be busy during a meltdown is not condemned
					-- by it for the rest of the run. 50% is not a taste: the game
					-- ticks at 1 Hz and the poll runs at 4 Hz, so a real value
					-- cannot change on more than ~25% of polls.
					if st.polls == Config.ChatterPolls
						and st.changes * 100 > st.polls * Config.ChatterPercent then
						st.dead = true
						emitEvt('NOISY', rec.key .. ' changed ' .. tostring(st.changes) ..
							' times in ' .. tostring(st.polls) .. ' polls')
					end
				end
			end
		end
	end
	-- The poll is over. Cleared here, once, rather than at the top of each record,
	-- so a record is judged against the poll it just finished and not against a
	-- mixture of this poll and the previous one.
	for _, rec in ipairs(readouts) do
		local st = readoutStats[rec.key]
		if st ~= nil then st.thisPoll = 0 end
	end
end

local function readReactor()
	if ReactorFrame == nil then return end
	readLabel('temp',      ReactorFrame, 'TempLabel')
	readLabel('press',     ReactorFrame, 'PressureLabel')
	readLabel('rad',       ReactorFrame, 'RadiationLabel')
	readLabel('out',       ReactorFrame, 'OutputLabel')
	readLabel('hdef',      ReactorFrame, 'HDEFLabel')
	readLabel('stress',    ReactorFrame, 'StressLabel')
	readLabel('fluct',     ReactorFrame, 'FluctuationLabel')
	readLabel('extract',   ReactorFrame, 'ExtractionLabel')
	readLabel('integrity', ReactorFrame, 'IntegrityLabel')
	readLabel('stab',      ReactorFrame, 'StabilityLabel')
end

local function readFans()
	if FanFrame == nil then return end
	local count = 0
	for i = 1, 6 do
		local f = FanFrame:FindFirstChild('FanFrame' .. i)
		local s = f and f:FindFirstChild('StatusLabel')
		local on = (s ~= nil and s.Text == 'ON')
		if on then count = count + 1 end
		-- Per fan as well as the total. The total alone cannot tell "fan 3
		-- swapped for fan 5" from "nothing happened", and the six outtake fans
		-- are the one control that reverses chamber pressure.
		put('c.fan' .. i, on and 1 or 0)
	end
	put('c.fanCount', count)
end

local function readCBL()
	for i = 1, 3 do
		local frame = PowerFrame and PowerFrame:FindFirstChild('CBL' .. i .. 'Frame')
		local pct = nil
		if frame then
			local lbl = frame:FindFirstChild('PowerLabel')
			if lbl and type(lbl.Text) == 'string' and lbl.Text ~= '' then
				pct = tonumber(lbl.Text:match('([+-]?%d+%.?%d*)'))
			end
		end
		if pct ~= nil then put('c.cbl' .. i .. 'Pct', pct) end

		local active = child(MainData, 'CBL' .. i, 'Active')
		if active ~= nil then
			local a = active.Value and 1 or 0
			put('c.cbl' .. i .. 'On', a)
			-- The derived level sits next to the raw percent so a reader can see
			-- where the quantisation happens instead of having to infer it.
			local lvl = 0
			if a == 1 and pct and pct > 0 then
				lvl = math.clamp(math.floor(pct / 25), 1, 5)
			end
			put('c.cbl' .. i .. 'Lvl', lvl)
		end
	end
end

local function readCoolant()
	if ThermalConsole == nil then return end
	local sum = 0
	for i = 1, 3 do
		local pump = ThermalConsole:FindFirstChild('CoolantControl' .. i)
		local lit = 0
		if pump then
			for j = 1, 3 do
				local neon = child(pump, 'Light' .. j, 'NeonPart')
				if neon then
					local c = neon.Color
					local on = math.abs(c.R * 255 - Config.NeonOn[1]) < 4
						and math.abs(c.G * 255 - Config.NeonOn[2]) < 4
						and math.abs(c.B * 255 - Config.NeonOn[3]) < 4
					if on then lit = lit + 1 end
				end
			end
		end
		put('c.cool' .. i, lit)
		sum = sum + lit
	end
	put('c.coolSum', sum)
end

-- ========================== STATS SCAN ====================================
-- Workspace.Stats is the game s own bookkeeping (ActiveQPUs and friends). It is
-- read generically and recursively, so a value we never heard of is still
-- recorded, and its comings and goings are events in their own right.
local statsSeen = {}
local function readStats()
	if MainData == nil then MainData = Workspace:FindFirstChild('Stats') end
	if MainData == nil then return end
	local seen = {}
	local function scan(inst, prefix)
		for _, d in ipairs(inst:GetChildren()) do
			local path = prefix .. d.Name
			seen[path] = true
			if d:IsA('ValueBase') then
				local v = d.Value
				local t = type(v)
				if t == 'number' or t == 'boolean' then
					put('s.' .. path, v)
				elseif v ~= nil then
					-- A StringValue, or a type with no space-free rendering.
					putText('s.' .. path, tostring(v))
				end
			end
			if #d:GetChildren() > 0 then scan(d, path .. '.') end
		end
	end
	scan(MainData, '')
	for path in pairs(statsSeen) do
		if not seen[path] then
			emitEvt('STATDEL', path)
			last['s.' .. path] = nil
			last['x.s.' .. path] = nil
		end
	end
	for path in pairs(seen) do
		if not statsSeen[path] then emitEvt('STATADD', path) end
	end
	statsSeen = seen
end

-- ========================== LAMP MATRIX ===================================
-- The lamps ARE the control-surface state: a lamp that is lit is a control that
-- is thrown. There are about a thousand of them and they are all NeonParts, so
-- one key per part would make a long line for every change. Instead each
-- subsystem is one token of one character per lamp, in a stable sorted order,
-- against a palette that ships alongside. A whole subsystem changing is then a
-- handful of bytes.
local lampSystems = {}
local palette, colorChar = {}, {}
local lampParts, lampDirty = 0, true

local function charForColor(c)
	local k = tostring(math.floor(c.R * 255 + 0.5)) .. ',' ..
		tostring(math.floor(c.G * 255 + 0.5)) .. ',' ..
		tostring(math.floor(c.B * 255 + 0.5))
	local ch = colorChar[k]
	if ch then return ch end
	local n = 0
	for _ in pairs(palette) do n = n + 1 end
	if n >= #PALETTE then return '?' end
	ch = string.sub(PALETTE, n + 1, n + 1)
	colorChar[k] = ch
	palette[k] = ch
	-- The legend ships as its own line the first time a colour appears, so every
	-- code in the file can be decoded from the file alone.
	emitEvt('LAMPPAL', ch .. '=' .. k)
	return ch
end

local function scanLamps()
	local consoles = Workspace:FindFirstChild('Consoles')
	if consoles == nil then return end
	local found, n = {}, 0

	local function walk(inst, systemKey, rel)
		for _, d in ipairs(inst:GetChildren()) do
			if d.Name == 'NeonPart' then
				n = n + 1
				if n > Config.MaxLampParts then return end
				local key = (systemKey ~= '') and systemKey or rel
				local rec = found[key]
				if rec == nil then rec = {} found[key] = rec end
				rec[#rec + 1] = { part = d, order = rel .. '.' .. d.Name }
			elseif #d:GetChildren() > 0 then
				-- A subsystem is a direct child of a console; anything deeper
				-- folds into it, which keeps the key count and the order
				-- manifest small.
				walk(d, (systemKey == '') and d.Name or systemKey, rel .. '.' .. d.Name)
			end
		end
	end
	for _, console in ipairs(consoles:GetChildren()) do
		walk(console, '', console.Name)
	end

	local nextSystems = {}
	for key, rec in pairs(found) do
		table.sort(rec, function(a, b) return a.order < b.order end)
		local old = lampSystems[key]
		local parts = {}
		for i = 1, #rec do parts[i] = rec[i].part end
		local sameManifest = (old ~= nil and #old.parts == #parts)
		if sameManifest then
			for i = 1, #parts do
				if old.parts[i] ~= parts[i] then sameManifest = false break end
			end
		end
		nextSystems[key] = { parts = parts, codes = old and old.codes or nil }
		if not sameManifest then
			local names = {}
			for i = 1, #rec do names[i] = rec[i].order end
			emitEvt('LAMPMAP', key .. ' ' .. table.concat(names, '|'))
			nextSystems[key].codes = nil
		end
	end
	lampSystems = nextSystems
	lampParts = n
	lampDirty = false
end

local function readLamps()
	local count = 0
	for key, rec in pairs(lampSystems) do
		local codes = {}
		for i = 1, #rec.parts do
			codes[i] = charForColor(rec.parts[i].Color)
		end
		local s = table.concat(codes)
		if rec.codes ~= s then
			rec.codes = s
			put('z.' .. key, s)
		end
		count = count + 1
	end
	put('z.systems', count)
	put('z.parts', lampParts)
end

-- ========================== FLOW ==========================================
-- One shutdown then one startup, then seal. The state is the game s own: tempF
-- against the authored thresholds, plus the output readout as a second opinion,
-- because temperature alone reads low both for a core that is off and for one
-- that has only just been lit.
local running, lowRun, lowDown, settle = false, 0, 0, 0

-- Seals the file. The hash and its coverage are captured BEFORE the receipt
-- line is emitted, and `over` states how many bytes the hash covers -- which is
-- everything above the receipt and not one byte of the receipt itself. Getting
-- that boundary wrong is not a cosmetic error: a verifier that hashes the whole
-- file against a hash taken before the last line can never match, and the
-- mismatch looks exactly like data corruption in transit.
local function seal(reason)
	emitEvt('SEAL', reason)
	local parts = {}
	for k, v in pairs(kinds) do
		parts[#parts + 1] = k .. '=' .. tostring(v)
	end
	table.sort(parts)
	local pre, h = total, hash
	emit('## RECEIPT name=' .. NAME ..
		' samples=' .. tostring(sample) ..
		' lines=' .. tostring(lines) ..
		' events=' .. tostring(evtNo) ..
		' segments=' .. tostring(segNo) ..
		' postfails=' .. tostring(postFails) ..
		' spilled=' .. tostring(spilled) ..
		' dropped=' .. tostring(dropped) ..
		' flow=' .. tostring(sawDown) ..
		-- The driver s verdict belongs in the receipt, not only in an EVT line
		-- among two thousand: whether a human or the driver operated the
		-- switches is the first thing a reader of an unattended run needs, and
		-- whether a control turned out to be inert is the answer to "why is
		-- there no flow in this file".
		' drive=' .. tostring(drive.state) .. '/' .. tostring(drive.verdict) ..
		' readouts=' .. tostring(readoutCount) ..
		' hash=' .. hex8(h) ..
		' over=' .. tostring(pre) ..
		' kinds ' .. table.concat(parts, ' '))
	-- waitForTurn: the receipt must not be left sitting in the buffer because a
	-- poll flush happened to be in flight when the seal fired.
	flush(true)
end

-- ========================== CONTROL HOOKS =================================
-- Labels for the controls we know by name, so a click reads as a control name
-- rather than a path. Anything not in here is still recorded, by path -- a
-- name change loses a label, never a click.
local labels = {}
local function labelPart(part, name)
	if part then labels[part:GetFullName()] = name end
end

if MainConsole then
	labelPart(child(MainConsole, 'AtmosphereVentButton', 'ClickPart'), 'AVB')
	for i = 1, 3 do
		labelPart(child(MainConsole, 'E_VENTLever' .. i, 'ClickPart'), 'E-VENT' .. i)
	end
	labelPart(child(MainConsole, 'StartUpBigLever', 'StartClickPart'), 'StartUpLever')
	labelPart(child(MainConsole, 'StartUpBigLever', 'ShutClickPart'), 'ShutdownLever')
end
if ThermalConsole then
	for i = 1, 3 do
		local pump = ThermalConsole:FindFirstChild('CoolantControl' .. i)
		if pump then
			labelPart(child(pump, 'OnButton', 'ClickPart'), 'Coolant' .. i .. '-ON')
			labelPart(child(pump, 'OffButton', 'ClickPart'), 'Coolant' .. i .. '-OFF')
		end
	end
	for i = 1, 6 do
		labelPart(child(ThermalConsole, 'CFLever' .. i, 'ClickPart'), 'Fan' .. i)
	end
end
if CBLConsoles then
	for i = 1, 3 do
		local sys = CBLConsoles:FindFirstChild('CBL' .. i .. 'Systems')
		if sys then
			labelPart(child(sys, 'PressureButton', 'ClickPart'), 'CBL' .. i .. '-PURGE')
			for j = 1, 5 do
				labelPart(sys:FindFirstChild('PW' .. j .. 'ClickPart'),
					'CBL' .. i .. '-PW' .. j)
			end
		end
	end
end

-- Everything below was read off the first recording, which is why it is here:
-- 82 of its 224 clicks came back path-only, and every path named in this block
-- is one that actually appeared. These are measured, not guessed -- the point
-- of the block above is that a guess costs you a label, and the click is still
-- recorded either way.
local AltConsole  = child(Workspace, 'Consoles', 'ALTReactorConsole')
local GridConsole = child(Workspace, 'Consoles', 'ElectricGridConsole')
local HDEFConsole = child(Workspace, 'Consoles', 'HDEFGenerator')
if AltConsole then
	local systems = child(AltConsole, 'ControlRoomSystems')
	if systems then
		labelPart(child(systems, 'ShuttersLever', 'ClickPart'), 'Shutters')
		labelPart(child(systems, 'RoomLightButton', 'ClickPart'), 'RoomLight')
		labelPart(child(systems, 'MonitorPowerButton', 'ClickPart'), 'MonitorPower')
	end
	for i = 1, 4 do
		local mass = AltConsole:FindFirstChild('MASS' .. i .. 'Systems')
		if mass then
			labelPart(child(mass, 'ActivationButton', 'ClickPart'), 'MASS' .. i .. '-Activate')
			labelPart(child(mass, 'PowerLever', 'ClickPart'), 'MASS' .. i .. '-Power')
		end
	end
end
if MainConsole then
	labelPart(child(MainConsole, 'MonitorBootButton', 'ClickPart'), 'MonitorBoot')
end
if GridConsole then
	labelPart(child(GridConsole, 'OverloadButton', 'ClickPart'), 'Overload')
	local ex = child(GridConsole, 'ExtractionLever')
	if ex then
		for j = 1, 5 do
			labelPart(ex:FindFirstChild('PW' .. j .. 'ClickPart'), 'Extraction-PW' .. j)
		end
	end
end
if HDEFConsole then
	labelPart(child(HDEFConsole, 'PowerLever', 'ClickPart'), 'HDEF-PowerLever')
end
if ThermalConsole then
	for i = 1, 3 do
		local pump = ThermalConsole:FindFirstChild('CoolantControl' .. i)
		if pump then
			for j = 1, 5 do
				labelPart(pump:FindFirstChild('PW' .. j .. 'ClickPart'),
					'Coolant' .. i .. '-PW' .. j)
			end
		end
	end
end

-- ========================== DRIVER ========================================
-- Autonomous operation of the two switches this flow is made of, so one
-- complete shutdown -> startup can be captured without a hand on the console.
--
-- WHY IT EXISTS: the recorder has made three attempts at this flow and none of
-- them contains both halves. original_260926-151207 holds a shutdown that was
-- not a shutdown -- the core was already cooling on its own from t=462 (6792 F
-- at t=462.4, 5394 F at t=467.7) and the ShutdownLever press at t=480 arrived
-- twelve seconds after the boundary had been crossed. ...-155513 never armed at
-- all, and ...-155619 is the startup half by itself. The missing ingredient was
-- never the recorder; it was a person pressing the right control at the right
-- moment, and a person cannot be a dependency of an unattended measurement.
--
-- HOW A PRESS REACHES THE GAME: `fireclickdetector` is an EXECUTOR global, not
-- Roblox API -- plain Luau has no way to make a ClickDetector press reach the
-- server. The evidence that it works in THIS game is Addition/Shift4.luau, a
-- client-side mod of this same place whose coolant, CBL and extraction consoles
-- are all driven as `fireclickdetector(<ClickDetector>)`; those systems are
-- server-side, so the call must be reaching the server. That file s own source
-- only warns when the global is absent, which is the whole dependency: if the
-- injector does not provide it, this driver turns itself off and says so,
-- rather than sitting in RUN looking like a recorder with nothing to record.
--
-- CONTROL BY CANDIDATE, NOT BY ASSUMPTION: `StartUpBigLever` carries two click
-- parts, `StartClickPart` and `ShutClickPart`, and both names were read off the
-- live game. But a control that is named correctly and wired to nothing is
-- indistinguishable from one that works until you press it and watch. So every
-- press opens a PROOF WINDOW, and a press that does not move the core the way
-- it was supposed to is reported INERT by path and the next candidate is tried.
-- A run therefore ends with either a captured flow or a named dead control --
-- never with a recorder that merely appears idle.
local fireClick = nil
do
	-- pcall, because reading an undefined global is fine but an executor that
	-- defines this name as a non-function is not, and this is the one place in
	-- the file that depends on the injector rather than on the game.
	local ok, fn = pcall(function() return fireclickdetector end)
	if ok and type(fn) == 'function' then fireClick = fn end
end

local function pathOf(cd)
	if cd == nil then return 'nil' end
	local ok, p = pcall(function() return cd.Parent and cd.Parent:GetFullName() end)
	if ok and type(p) == 'string' then return p end
	return 'unresolved'
end

local function press(cd)
	local ok, err = pcall(fireClick, cd)
	if not ok then emitEvt('DRIVE', 'press FAILED ' .. tostring(err)) end
	return ok
end

local function detectorOf(part)
	if part == nil then return nil end
	local ok, cd = pcall(function() return part:FindFirstChildOfClass('ClickDetector') end)
	if ok then return cd end
	return nil
end

-- Match on the host part s name OR the detector s own name, so a control the
-- game renames from ShutClickPart to ShutPart is still found. `pattern` is a
-- Lua pattern and the callers only pass plain anchored words.
local function detectorsMatching(root, pattern)
	local out = {}
	if root == nil then return out end
	pcall(function()
		for _, d in ipairs(root:GetDescendants()) do
			if d:IsA('ClickDetector') then
				local host = d.Parent
				local hostName = host and host.Name or ''
				if string.find(hostName, pattern) or string.find(d.Name, pattern) then
					out[#out + 1] = d
				end
			end
		end
	end)
	return out
end

local shutCandidates, startCandidates = {}, {}
local function addCandidate(list, cd)
	if cd == nil then return end
	for i = 1, #list do
		if list[i] == cd then return end
	end
	list[#list + 1] = cd
end

do
	local bigLever = MainConsole and child(MainConsole, 'StartUpBigLever')
	addCandidate(shutCandidates,  detectorOf(child(bigLever, 'ShutClickPart')))
	addCandidate(startCandidates, detectorOf(child(bigLever, 'StartClickPart')))
	for _, d in ipairs(detectorsMatching(bigLever, '^Shut')) do addCandidate(shutCandidates, d) end
	for _, d in ipairs(detectorsMatching(bigLever, '^Start')) do addCandidate(startCandidates, d) end
	-- Widen to the whole console ONLY when the lever itself offered nothing. The
	-- wider net can catch an unrelated button, and a wrong press on a live
	-- reactor is a change to the world, not a probe.
	if #shutCandidates == 0 then
		for _, d in ipairs(detectorsMatching(MainConsole, 'Shut')) do addCandidate(shutCandidates, d) end
	end
	if #startCandidates == 0 then
		for _, d in ipairs(detectorsMatching(MainConsole, 'Start')) do addCandidate(startCandidates, d) end
	end
end

drive.on = Config.AutoDrive and fireClick ~= nil
-- Three ways the driver can be off, and they want three different answers: no
-- injector function means this run cannot be driven at all; AutoDrive false
-- means the attempt has not been spent yet; on means it is ready to spend. One
-- verdict covering all three would send the reader looking for a missing
-- executor feature when the real answer is a button nobody has pressed.
drive.verdict = (fireClick == nil) and 'off-no-fireclickdetector'
	or ((not Config.AutoDrive) and 'off-waiting-arm' or 'unsupported')

local function pathsOf(list)
	if #list == 0 then return '(none)' end
	local out = {}
	for i = 1, #list do out[i] = pathOf(list[i]) end
	return table.concat(out, ' | ')
end

-- What the driver found, written BEFORE it presses anything and written even by
-- a run that never presses. If the single attempt goes to the wrong control,
-- this line is what says which control that was and what else was on offer, and
-- it lands in the file rather than only on screen -- a console scrolls away.
emitEvt('DRIVE', 'candidates shut=' .. pathsOf(shutCandidates) ..
	' start=' .. pathsOf(startCandidates) ..
	' fireclickdetector=' .. (fireClick and 'yes' or 'NO'))

-- One step per poll, fed the same tempF and isRunning the flow boundary uses.
-- Every state that can wait also has a way out that is not waiting forever: an
-- unattended recorder that hangs is indistinguishable from one that is simply
-- recording a quiet reactor, and that is the failure this whole file exists to
-- make impossible.
local function driveStep(tempF, isRunning, dt)
	if not drive.on then return end
	if drive.state == 'inert' or drive.state == 'done' then return end

	-- dt is the caller s MEASUREMENT of the poll just finished, not the poll
	-- period this file configures. A configured constant is a claim about the
	-- loop; only the loop can report what the loop did. The 18:01 run is why that
	-- distinction is worth a parameter: the constant said 0.25 s, the loop ran at
	-- 3.38 Hz, and every dwell below came out 18 per cent long -- so the receipt
	-- said the core was switched off 60 s after the driver decided to, and the
	-- timestamps said 70.59.
	--
	-- Deliberately no upper clamp. If the client stalls for thirty seconds then
	-- thirty seconds passed, and the reactor spent them running; crediting thirty
	-- is the measurement, and clamping it would be a second assumption of exactly
	-- the kind this parameter removes. Only a value that cannot be a duration --
	-- absent, negative, or not a number at all -- falls back to the constant, so
	-- that a harness with no clock can still call this.
	if type(dt) ~= 'number' or dt ~= dt or dt <= 0 then
		dt = Config.SampleInterval
	end

	if drive.state == 'arming' then
		-- The core may already be lit when this is injected, or it may be cold.
		-- Arming is the wait that tells those two apart without a rule that can
		-- disagree with the game: flowArmed is the recorder s own confirmation
		-- that the core is running, and DriveArmSeconds of unbroken cold is the
		-- point at which it is not going to light itself.
		if flowArmed then
			-- WHERE THE CORE BEING UP LEADS DEPENDS ON WHO PRESSES. With the
			-- driver holding the controls, a running core means hold, then shut.
			-- With the operator holding them -- the live setting -- the same
			-- fact means the run has begun and the driver s job is to watch for
			-- his press. Splitting here rather than inside `holding` keeps every
			-- state readable as a statement about who acts next.
			if Config.DrivePressControls then
				drive.state = 'holding'
				drive.verdict = 'holding'
				emitEvt('DRIVE', 'armed, core already running; will switch it off in ' ..
					tostring(Config.DriveHoldSeconds) .. 's')
			else
				drive.state = 'watching'
				drive.verdict = 'watching'
				emitEvt('DRIVE', 'armed, core running; the driver presses nothing -- ' ..
					'press the shutdown lever when the shift should end')
				print('[rec] DRIVER: watching. Press the shutdown lever yourself;')
				print('[rec] DRIVER: the recorder will note the press and the reply.')
			end
			return
		end
		drive.armT = drive.armT + dt
		if drive.armT >= Config.DriveArmSeconds then
			if tempF == nil then
				-- Nothing to judge the core by, so nothing is pressed. Pressing
				-- blind on a live reactor is the one action here that cannot be
				-- undone, and "the readout is missing" is not "the core is off".
				drive.verdict = 'no-temp-readout'
				return
			end
			-- The timer has expired, but the core is READING AS RUNNING, so this
			-- is not the core the timeout is about. It is the debounce catching
			-- up: flowArmed needs DebounceSamples polls and this is still an
			-- early one. Wait for it rather than refusing.
			--
			-- This guard is what makes the measured dt safe. The first poll is
			-- the only one with no measured predecessor, and it is the one
			-- carrying the initial readout and lamp sweeps, so nothing bounds
			-- how long it takes. With dt measured, a first poll of twenty
			-- seconds or more would credit armT with twenty seconds in a single
			-- step and a driver injected on a perfectly healthy running core
			-- would report cold-at-inject and go inert -- on the run that has
			-- exactly one attempt. Under the old constant dt the debounce window
			-- was eighty polls wide and could not be crossed in one step.
			if isRunning then return end
			-- A COLD CORE IS NOT AN ERROR WHEN THE OPERATOR DRIVES, IT IS THE
			-- SCHEDULE. The recorder is injected before the shift begins and
			-- `A1` has the operator light the core himself, so a cold core at the
			-- end of the arm window is the expected opening rather than a state
			-- to act on. Nothing is pressed; the wait is announced once and the
			-- state machine stays in `arming`, which is the one state that goes on
			-- watching for `flowArmed`. The operator lighting the core is
			-- therefore not a special case -- it is the same edge that carries
			-- every other run into `watching`.
			if not Config.DrivePressControls then
				if not drive.waitingCold then
					drive.waitingCold = true
					emitEvt('DRIVE', 'core is cold after ' ..
						tostring(Config.DriveArmSeconds) .. 's tempF=' ..
						tostring(tempF) .. ' -- waiting for the operator to light it')
					print('[rec] DRIVER: the core is cold. Light it when you are ready;')
					print('[rec] DRIVER: nothing is pressed and nothing is spent.')
				end
				return
			end
			-- THE BUTTON IS THE AUTHORISATION, SO THE DRIVER LIGHTS IT.
			--
			-- This branch used to refuse, on the arithmetic that a flow needs one
			-- startup and one shutdown and that spending the startup on the
			-- opening leaves the end with none. The operator overruled that, and
			-- the reasoning is better than the arithmetic: pressing DRIVER is a
			-- person deciding that THIS attempt is the one to spend, and the
			-- driver declining to act on a decision it was handed is not caution
			-- -- it is the attempt spent on nothing.
			--
			-- What replaces the veto is a choice the driver can make from the
			-- plant instead of from an assumption. `arming` is the only state
			-- that does not know whether the core is up, and it answers that
			-- question by looking: running sends it to `holding` (switch it off),
			-- cold sends it here (switch it on). Neither mode needs the operator
			-- to declare which one he wanted, so neither can be declared wrong.
			emitEvt('DRIVE', 'armed cold after ' ..
				tostring(Config.DriveArmSeconds) .. 's tempF=' .. tostring(tempF) ..
				' -- lighting the core')
			print('[rec] DRIVER: the core is cold; lighting it.')
			print('[rec] DRIVER: one attempt, hands off the console.')
			drive.state = 'press_start'
			drive.verdict = 'arming-cold'
		end
		return
	end

	if drive.state == 'watching' then
		-- THE LIVE STATE. The core is up, the driver is holding no controls, and
		-- the only thing left to record is the operator s own shutdown and the
		-- game s answer to it.
		--
		-- The evidence is the same set of signals `shut_down` confirms from, read
		-- as a LEVEL rather than as an edge, because this is a report about the
		-- state of the world and not a trigger. The verdict doubles as the latch.
		--
		-- `v.shutdown` is first, and it is the one the operator named for the
		-- press itself (`B3`): pressing the shutdown lever puts
		-- `MonitorUI.ShutdownFrame` on screen. That is a screen appearing in the
		-- same second as the press, which is the closest thing to a direct read
		-- of the press that does not depend on a click line arriving. The end
		-- flags follow as fallbacks: a shift that ended some other way -- a cold
		-- trip, a machine-room meltdown -- is still a shift whose shutdown the
		-- driver should name rather than leave the file to explain.
		--
		-- No press is made here under any arm, including the flags. A machine
		-- that has ended the shift by itself is not one to hand a startup to --
		-- and with the driver unarmed that decision is not even reachable.
		if drive.verdict == 'watching' then
			local said
			if last['v.shutdown'] == true then
				said = 'the shutdown screen is up'
			elseif last['s.GameActive'] == false then
				said = 's.GameActive=false'
			elseif last['s.MainframeMeltdown'] == true then
				said = 's.MainframeMeltdown=true'
			elseif last['s.GameFail'] == true then
				said = 's.GameFail=true'
			end
			if said ~= nil then
				-- The wording follows the FLAG, because only the first flag is an
				-- operator action. The other three are the machine ending the
				-- shift by itself, and the comment above already says so -- but
				-- the sentence said `the operator shut it down` for all four, so
				-- it contradicted its own `said` field in the one line that
				-- records the seal. Seen 2026-09-26 in
				-- Data/flow/original_260926-230049: `the operator shut it down:
				-- s.MainframeMeltdown=true`, in a file with no shutdown-lever
				-- click anywhere -- 124 CLICK events, 0 of them on
				-- StartUpBigLever.ShutClickPart, and no v.shutdown either.
				--
				-- THE VERDICT IS LEFT ALONE. `user-shut` answers "who pressed",
				-- and "not the driver" is the honest answer for a meltdown too;
				-- renaming it would move the receipt field, the HOWTO table and
				-- four mutation proofs to say the same thing less precisely.
				local pressed = last['v.shutdown'] == true
				drive.shutDone = true
				drive.shutSaid = said
				drive.verdict = 'user-shut'
				emitEvt('DRIVE', (pressed and 'the operator shut it down: '
					or 'the shift ended: ') .. said .. ' tempF=' .. tostring(tempF))
				drive.state = 'shut_down'
			end
		end
		return
	end

	if drive.state == 'holding' then
		-- Real time before the switch-off, so the file contains steady state and
		-- not only two transients. It costs almost nothing: a steady reactor
		-- changes nothing, and nothing is what gets written.
		drive.holdT = drive.holdT + dt
		if drive.holdT >= Config.DriveHoldSeconds then drive.state = 'press_shut' end
		return
	end

	if drive.state == 'press_shut' then
		if tempF == nil then return end
		if not isRunning then
			-- Refuse. Pressing a shutdown switch on a core that is already down
			-- cannot be shown to have done anything, and the 18:01 run is the
			-- measured case: the hold expired at t=64, the core had crossed the
			-- threshold at t=65, and the press went out at t=73 on a reactor
			-- that was on its way back up. Wait for it to be running, then the
			-- press means what it says.
			if not drive.waitingRun then
				drive.waitingRun = true
				emitEvt('DRIVE', 'core is down before the shut press; waiting for a run')
			end
			return
		end
		drive.waitingRun = false
		-- Index 1 and only index 1. The list can hold more than one name for
		-- the same control, and the driver used to walk down it whenever a press
		-- proved inert. With one attempt there is no walking: the best evidenced
		-- candidate is pressed once, and a press that does nothing ends the run
		-- naming the control rather than spending a second attempt on a guess.
		local cd = shutCandidates[1]
		if cd == nil then
			drive.state = 'inert'
			drive.verdict = 'no-shut-control'
			emitEvt('DRIVE', 'no shutdown control found, nothing pressed')
			print('[rec] DRIVER: found no shutdown control. Nothing was pressed.')
			return
		end
		press(cd)
		-- The counters are the panel s, not the driver s: the panel prints
		-- `shut <shutIdx - 1>/<#candidates>`, so advancing it here is what makes
		-- the panel say one press was spent rather than none.
		drive.shutIdx = 2
		emitEvt('DRIVE', 'press shut ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF) ..
			' running=' .. tostring(isRunning))
		-- THE PRESS IS THE SHUTDOWN, AND THE DRIVER BELIEVES IT IMMEDIATELY.
		--
		-- The operator is emphatic that pressing this lever shuts the core down
		-- at once and that there is no cold state to wait for. So there is no
		-- cooldown to watch and nothing to prove: this does not open a window, it
		-- declares the end in the same poll that it pressed.
		--
		-- What stood here was a forty-second window that accepted the press once
		-- the monitor temperature had fallen DriveProveF degrees below where it
		-- was at the press. On the 18:35 run that reported `shut accepted after
		-- 8.7s` at t=335.37, and the verdict was manufactured by its own
		-- threshold: m.fluct in that same file has p5 = -218 F, p95 = +253 F, and
		-- extremes past -1700 F, so a 431 F move in 8.7 s is inside the plant s
		-- ordinary wobble. The core had not gone down. s.GameActive stayed true
		-- for 414 seconds after the press, and the temperature ROSE from 10713 to
		-- 11838 in the thirty seconds that followed it. The proof did not measure
		-- a shutdown; it measured the noise and answered yes.
		--
		-- The price of believing the press is that an inert press is no longer
		-- named HERE. It is named by the thing that actually knows -- the game s
		-- own end-of-shift statement, watched in `shut_down` below. That is a
		-- stricter test than the old one rather than a looser one: a flag the game
		-- sets about itself cannot be satisfied by a sensor wobble.
		drive.shutDone = true
		drive.verdict = 'shut-accepted'
		if Config.ShutdownEndsShift then
			drive.state = 'shut_down'
		else
			drive.state = 'waiting_down'
		end
		return
	end

	if drive.state == 'shut_down' then
		-- A shutdown has already been declared -- by this driver s press, or by
		-- the operator s -- and it ended the shift. This state presses nothing and
		-- waits for nothing; it exists to WATCH, and only to watch.
		--
		-- The one thing worth having after the press is whether the game agreed
		-- with it. The 18:35 run is why. The driver pressed at t=326.71 and the
		-- plant showed no reaction for 414 seconds, so that file cannot say
		-- whether the shutdown lever works when an executor presses it -- which is
		-- the single most valuable thing the next run should answer. Recording
		-- the game s own statement separates "the press did not land" from "it
		-- landed and the shift runs on regardless", and it costs one line.
		--
		-- These are the same signals endReason trusts, and they are read as a
		-- LEVEL here rather than as an edge, because this is a report about the
		-- state of the world and not a trigger.
		--
		-- Two verdicts reach this state, and both mean "a shutdown was declared
		-- and nothing has been heard back about it yet": `shut-accepted` is this
		-- driver s own press, `user-shut` is the operator s. They are kept apart
		-- rather than collapsed into one, because they are the two answers to the
		-- question the run exists to ask -- does an executor s press land, and
		-- does the operator s -- and a file that merged them could not answer it.
		--
		-- SO `user-shut` IS NEVER OVERWRITTEN HERE, and that is a correction, not
		-- a preference. The first version of this block ran for both verdicts and
		-- set `shut-confirmed` on whatever it found -- which, for the operator s
		-- press, was the very signal that had just ended `watching`. The receipt
		-- therefore read `shut-confirmed` on a run where this driver never pressed
		-- anything, one poll after the file had said `user-shut`. The word means
		-- "the executor s press landed"; handing it to a press the executor did
		-- not make destroys the one distinction the live run exists to record.
		-- So the verdict is an answer to WHO PRESSED and only the press path
		-- changes it.
		--
		-- What the operator s run does still get is any signal that arrives AFTER
		-- the one that ended `watching` -- `v.shutdown` goes up with the press, and
		-- the game s formal `s.GameActive=false` can land 400 seconds later, and
		-- that second statement is news rather than an echo. `shutSaid` is what
		-- tells them apart: the signal already written down never fires again, and
		-- a different one always does. The two states search in different orders
		-- (see the field s own comment), so a later signal outranks its way to the
		-- front and the earlier one is found only when nothing else has come.
		local said
		if last['s.GameActive'] == false then
			said = 's.GameActive=false'
		elseif last['s.MainframeMeltdown'] == true then
			said = 's.MainframeMeltdown=true'
		elseif last['s.GameFail'] == true then
			said = 's.GameFail=true'
		elseif last['v.shutdown'] == true then
			said = 'the shutdown screen is up'
		end
		if said ~= nil and said ~= drive.shutSaid then
			drive.shutSaid = said
			if drive.verdict == 'shut-accepted' then
				drive.verdict = 'shut-confirmed'
			end
			emitEvt('DRIVE', 'the game confirms the shutdown: ' .. said ..
				' tempF=' .. tostring(tempF))
		end
		return
	end

	if drive.state == 'waiting_down' then
		-- REACHED ONLY WHEN A SHUTDOWN DOES NOT END THE SHIFT. The live
		-- configuration ends the run at the press itself -- press_shut goes
		-- straight to shut_down -- so what is left here is the other
		-- configuration s wait: the core has been told to stop, and the driver
		-- must not relight it until it actually has.
		--
		-- The gate is sawDown, the recorder s own DOWN edge, rather than a second
		-- opinion computed here. That is the point the whole PROVING section makes:
		-- a private temperature test is a second opinion about a plant the
		-- recorder is already reading, and when the two disagree there is nothing
		-- in the file that can settle which one was right.
		if sawDown and not isRunning then
			drive.coldT = 0
			drive.state = 'dwell_cold'
		end
		return
	end

	if drive.state == 'dwell_cold' then
		drive.coldT = drive.coldT + dt
		if drive.coldT >= Config.DriveColdSeconds then
			drive.state = 'press_start'
		end
		return
	end

	if drive.state == 'press_start' then
		if tempF == nil then return end
		if isRunning then
			drive.state = 'done'
			drive.verdict = 'relit-itself'
			emitEvt('DRIVE', 'core lit again without the driver')
			return
		end
		local cd = startCandidates[1]
		if cd == nil then
			drive.state = 'inert'
			drive.verdict = 'no-start-control'
			emitEvt('DRIVE', 'no startup control found, nothing pressed')
			print('[rec] DRIVER: found no startup control. Nothing was pressed.')
			return
		end
		drive.proofCd, drive.proofT = cd, 0
		drive.proofRunning = isRunning
		press(cd)
		drive.startIdx = 2   -- display only, for the same reason as shutIdx
		emitEvt('DRIVE', 'press start ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF) ..
			' running=' .. tostring(isRunning))
		drive.state = 'proving_start'
		return
	end

	if drive.state == 'proving_start' then
		drive.proofT = drive.proofT + dt
		-- A START IS PROVED BY ARRIVAL, NOT BY A DELTA, for the same reason the
		-- shut is no longer proved at all. `rose` -- which accepted the press once
		-- the temperature had climbed DriveProveF degrees above where it stood at
		-- the press -- is gone with `fell`. They were the same test, and the same
		-- measurement disproved both.
		--
		-- The readout crossing the running threshold IS the state change, and it
		-- cannot be reached by wobble: the threshold sits thousands of degrees
		-- above a cold core, so nothing the noise does can fake this arrival.
		--
		-- press_start already returns early when the core is lit, so proofRunning
		-- is false here by construction; the field is read rather than assumed
		-- because "cannot currently be wrong" is a claim about today s code and
		-- not about the field.
		local nowUp = isRunning and drive.proofRunning == false
		if nowUp then
			emitEvt('DRIVE', 'start accepted after ' ..
				string.format('%.1f', drive.proofT) .. 's tempF=' .. tostring(tempF))
			drive.verdict = 'start-accepted'
			-- The core is up, so the driver goes back to `holding` and later
			-- switches it off. That makes the two ways in symmetric -- armed on
			-- a running core it shuts down, armed on a cold core it starts and
			-- THEN shuts down -- and both end in the same complete flow. It is
			-- also why `arming` does not have to be told which mode is wanted.
			--
			-- This branch was previously cut, on the argument that a startup
			-- opening the run left the end with no startup to spend and that a
			-- cold core was therefore refused. The refusal is gone (the operator
			-- made the button the authorisation), so the branch it was built
			-- against is reachable again and has to exist. `waiting_up` and its
			-- `flow-complete` verdict stay for the other configuration, where a
			-- shutdown does not end the shift and the recording is meant to
			-- close on the core coming back up.
			if Config.ShutdownEndsShift then
				drive.state = 'holding'
				drive.holdT = 0
			else
				drive.state = 'waiting_up'
			end
			return
		end
		if drive.proofT >= Config.DriveProveSeconds then
			emitEvt('DRIVE', 'start INERT ' .. pathOf(drive.proofCd) .. ' after ' ..
				tostring(Config.DriveProveSeconds) .. 's tempF=' .. tostring(tempF))
			print('[rec] DRIVER: ' .. pathOf(drive.proofCd) .. ' did nothing.')
			print('[rec] DRIVER: no second press. The core is down; seal when ready.')
			drive.state = 'inert'
			drive.verdict = 'start-inert'
		end
		return
	end

	if drive.state == 'waiting_up' then
		-- The recorder owns the rest: RUN -> DOWN -> UP, then it seals itself.
		if sawDown and isRunning then
			drive.state = 'done'
			drive.verdict = 'flow-complete'
			emitEvt('DRIVE', 'flow complete; the recorder will seal on its own')
		end
		return
	end
end

-- The user s own clicks are half of the experiment; the reactor s response is
-- the other half. Every ClickDetector and ProximityPrompt in the workspace is
-- hooked, whether or not we know its name, so a control family that has never
-- been tested still produces a labelled-in-path record of every press.
local hooked = 0
local hookedSet = {}
local function hook(inst)
	if hookedSet[inst] then return end
	hookedSet[inst] = true
	if inst:IsA('ClickDetector') then
		local host = inst.Parent
		local name = host and labels[host:GetFullName()] or nil
		inst.MouseClick:Connect(function()
			-- Stamp the poll, not the clock. The stamp is compared against the
			-- poll counter, and a wall-clock stamp in a 4 Hz loop would drift
			-- against it for the same reason the driver s dwell timers did.
			clickPoll = sample
			emitEvt('CLICK', name or ('path=' .. ((host and host:GetFullName()) or 'nil')))
		end)
		hooked = hooked + 1
	elseif inst:IsA('ProximityPrompt') then
		inst.Triggered:Connect(function()
			clickPoll = sample
			emitEvt('PROMPT', inst:GetFullName())
		end)
		hooked = hooked + 1
	end
end

local function hookAll()
	local ok, err = pcall(function()
		for _, d in ipairs(Workspace:GetDescendants()) do pcall(hook, d) end
	end)
	-- Late arrivals (a model that streams in, a console that gets rebuilt).
	pcall(function()
		Workspace.DescendantAdded:Connect(function(d) pcall(hook, d) end)
	end)
	-- Never fatal. A missing control hook costs us the label on a click; it must
	-- not cost us the reactor data, which is the other half of the recording.
	if not ok then print('[rec] hook sweep failed: ' .. tostring(err)) end
end

-- ========================== PANELS ========================================
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

-- The three panel roots used to be resolved HERE, once, at module load -- and
-- that is the defect the 18:35 capture is evidence of, so the constants are
-- gone. The forecast panel emitted exactly one snapshot in 740 seconds
-- (`AnnouncementText=HADEN THRESHOLD BREACH`) while the same subtree had labels
-- moving inside a single poll, which the rate arm reported as `EVT1503 ANIM
-- ...ForecastControlRoomMonitor.ScrollingFrame.TimeSliceTemplate.TimeLabel moved
-- 5 times inside one poll`. A root cached at t=0 while the monitors were still
-- booting produces that, and so does a cache that landed on a different
-- same-named MainMonitorFrame; this capture cannot tell those apart, so the fix
-- stops needing to. See readPanel below.

-- Sorted, and WITHOUT the row index. Sorting makes the string a function of the
-- panel s contents rather than of GetDescendants enumeration order, which is not
-- guaranteed stable -- an unsorted snapshot would emit a change every poll for
-- no reason at all. Leaving the index out is the second half of the same idea:
-- with the index in, a ScrollingFrame that scrolls shifts every row and emits
-- every poll, which is exactly the flood the rate arm exists to stop. Sorted and
-- index-free, the snapshot changes when the panel s CONTENT changes and is
-- silent when only the order moved; and the file is a time series, so the order
-- is recoverable from the sequence of snapshots anyway.
-- Returns the snapshot AND its row count. The count is a second return rather
-- than a second walk because the walk is the expensive part and the number is
-- already in hand; callers that only want the string are unaffected, which is
-- what keeps the panel harness valid without being rewritten.
local function snapshot(root)
	if root == nil then return nil, 0 end
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
	if not ok then return '<unreadable>', 0 end
	if #rows == 0 then return '<no text>', 0 end
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
	return table.concat(out, '|'), n
end

-- putText, not put: a snapshot is a string, and the batch-line rule is that no
-- string can ever enter one. Missing panels cost nothing -- putText returns on
-- nil -- so a place whose monitor tree differs records the rest and says not a
-- word about the part it could not find.
-- Resolved per poll, coalesced per panel, and self-describing once a minute.
--
-- THREE SEPARATE DECISIONS IN ONE FUNCTION, so they are named rather than left
-- to be read out of the code:
--
-- 1. THE ROOT IS RESOLVED EVERY POLL. A FindFirstChild chain is nothing beside
--    the GetDescendants walk that follows it, and it cannot go stale. This is
--    the fix for the forecast panel that emitted one snapshot in 740 seconds.
--
-- 2. EMISSIONS ARE COALESCED, and compared against the last snapshot EMITTED
--    rather than the last one seen. That distinction is the whole reason this
--    is not a filter that loses data: a change held back is still a difference
--    from `last[key]`, so it stays pending and goes out the moment the gap
--    allows, and a panel that has settled is always written as it settled. The
--    18:35 run had 728 of its 2490 polls -- 29 per cent of the file -- produced
--    by one news ticker being revealed a character at a time.
--
-- 3. THE SIGNATURE IS EMITTED. EVT PANEL names the resolved path, its
--    descendant count and its row count, on the first read and whenever that
--    signature changes. It is what will settle the 18:35 question on the next
--    run, and it is worth having anyway: a monitor that rebuilds itself
--    mid-shift is exactly what makes a panel go quiet for no visible reason.
local panelSig, panelEmit = {}, {}
local function readPanel(key, monitor)
	local root = panelRoot('Monitors', monitor, 'Screen', 'MonitorUI', 'MainMonitorFrame')
	local s, rows = snapshot(root)
	if s == nil then return end
	local path = root and root:GetFullName() or '<nil>'
	if panelSig[key] == nil or sample % 240 == 0 then
		local n = 0
		if root ~= nil then
			local okc, c = pcall(function() return #root:GetDescendants() end)
			if okc then n = c end
		end
		local sig = path .. '#' .. tostring(n)
		if panelSig[key] ~= sig then
			panelSig[key] = sig
			emitEvt('PANEL', key .. ' root=' .. path ..
				' descendants=' .. tostring(n) .. ' rows=' .. tostring(rows))
		end
	end
	if last[key] == s then return end
	if sample - (panelEmit[key] or 0) < Config.PanelMinGapPolls then return end
	panelEmit[key] = sample
	putText(key, s)
end

local function readPanels()
	readPanel('log.panel', 'LogControlRoomMonitor')
	readPanel('fc.panel',  'ForecastControlRoomMonitor')
	readPanel('q.panel',   'QuotaControlRoomMonitor')
end

-- ========================== SHIFT SIGNALS =================================
-- Two states the recorder must not have to be TOLD about, both given by path.
--
-- SAM IS THE AUTOMATIC OPERATOR. It is recorded rather than reasoned about, and
-- the reason is a story this file used to tell that the operator has since
-- retracted. The old version of this comment said the 18:35 run was SAM fighting
-- the shutdown: coolant pumps going off after the press, forty unattributed
-- coolant changes, a core that refused to go down for 408 seconds.
--
-- What the file actually shows is that the press produced no shutdown for 414
-- seconds, and it does not say why. A causality was hung on that gap and the
-- operator has removed its premise from both ends (`D8`): SAM is OFF by default,
-- it is his to switch, and it is not a condition the driver has to account for.
-- With the machine off, the coolant changes cannot be its work.
--
-- So the causal claim is gone and the measurement stays. Nothing here is a
-- hypothesis about why the core stayed up; that question is open, and a log that
-- answers it by assumption is worse than one that leaves it open.
--
-- BOTH signals the operator gave are
-- recorded, because they can disagree and neither is declared authoritative:
-- the frame is the panel s own statement about itself, the lamp is the
-- console s, and a disagreement is a fact worth having in the file rather than a
-- fact worth guessing about. `sam.on` is the one key to read, derived with the
-- frame winning where it exists and the lamp standing in where it does not.
local function readSam()
	local kb = child(MainConsole, 'SAMKeyboard')
	local lamp = kb and child(kb, 'Light1', 'NeonPart')
	if lamp ~= nil then
		local c = lamp.Color
		local r = math.floor(c.R * 255 + 0.5)
		local g = math.floor(c.G * 255 + 0.5)
		local b = math.floor(c.B * 255 + 0.5)
		putText('sam.lamp', r .. ',' .. g .. ',' .. b)
		-- A SHAPE, not an equality. The operator reports the lamp is green when
		-- SAM is on and could not name the shade, so an equality against one
		-- green would answer "unknown" for every other green -- and the useful
		-- question is not which green, it is whether this lamp is lit at all.
		put('sam.lampGreen', g > 60 and g > r + 30 and g > b + 30)
	end
	local frame = child(Workspace, 'Monitors', 'MainControlRoomMonitor', 'Screen',
		'MonitorUI', 'MainMonitorFrame', 'SAMFrame')
	if frame ~= nil then put('sam.frame', frame.Visible == true) end
	local derived
	if last['sam.frame'] ~= nil then
		derived = last['sam.frame']
	elseif last['sam.lampGreen'] ~= nil then
		derived = last['sam.lampGreen']
	end
	put('sam.on', derived)
end

-- ========================== THE SCREENS THAT ANNOUNCE THE END ==============
-- The operator says pressing the shutdown lever shuts the core down AT ONCE.
-- If that is true there is a signal for it, and the recorder has to be able to
-- see it -- and until now it could not.
--
-- Everything mapped in this file is a TEXT property, plus exactly one Visible
-- (`sam.frame`). A screen that is SHOWN by flipping Visible on a frame whose
-- text was written earlier is therefore invisible to the whole recorder. The
-- 18:35 run shows the shape of that trap: the initial enumeration dumped
-- `ShutdownFrame.ShutdownText = ENERGY QUOTA MET` onto a hidden frame, and that
-- string sat there from before the first sample until t=740.33. Read as text it
-- looks like a shutdown that happened at t=0. Read as a frame it was not on
-- screen at all, and the only thing that changed at the end was the string.
--
-- So the state screens are read by Visible, which is the property that says
-- whether anybody can see them. These are the four the game already uses for
-- begin, end and failure, plus the two the capture shows sharing the same UI.
-- Each is one key, written only when it changes, so a quiet run pays nothing.
--
-- Note which key is NOT here: there is no `v.<anything>` for a frame that does
-- not resolve. A monitor that lacks one of these writes no key at all rather
-- than writing false, because "this monitor has no such screen" and "this screen
-- is hidden" are different facts and a false would conflate them.
local SCREEN_FRAMES = {
	{ 'v.shutdown',    'ShutdownFrame' },
	{ 'v.detonation',  'DetonationFrame' },
	{ 'v.boot',        'BootFrame' },
	{ 'v.error',       'ErrorFrame' },
	{ 'v.malfunction', 'MalfunctionFrame' },
	{ 'v.revive',      'ReviveFrame' },
}
local function readEndScreens()
	local ui = child(Workspace, 'Monitors', 'MainControlRoomMonitor', 'Screen',
		'MonitorUI')
	if ui == nil then return end
	for _, spec in ipairs(SCREEN_FRAMES) do
		local f = child(ui, spec[2])
		-- Two levels, because the capture shows these frames split between the
		-- monitor s own UI and its inner MainMonitorFrame and does not say which
		-- belongs where. Trying both is cheaper than being wrong about one.
		--
		-- For ShutdownFrame the operator has since named the level (`B3`:
		-- game.Workspace.Monitors.MainControlRoomMonitor.Screen.MonitorUI
		-- .ShutdownFrame), which is the DIRECT child -- the first of the two
		-- probes below, and the one that answers. The second probe is left in
		-- place for the other five frames, where the question is still open.
		if f == nil then f = child(ui, 'MainMonitorFrame', spec[2]) end
		if f ~= nil then put(spec[1], f.Visible == true) end
	end
end

-- The shift s objective, recorded because the ending needs it: a shift that ends
-- on a shutdown has either met the quota or failed it, and the shutdown screen
-- says which only in words. Size.X.Scale is 1 at full.
--
-- Two decimals, and that is a decision rather than a display choice. The bar is a
-- SMOOTH ANIMATION, so its exact scale changes on nearly every poll; recorded
-- raw it would be a second typewriter, and the file already has one. Two
-- decimals is one per cent of the bar, which is finer than any decision an
-- operator makes with it and coarse enough to be silent for tens of seconds at a
-- time -- and `q.panel` still carries the panel as it is drawn.
--
-- The colour is recorded as raw RGB and not matched against a constant, for the
-- same reason as the SAM lamp: the operator reports the bar turns blue when full
-- and says it is not a pure blue, which is a statement that a constant would get
-- wrong. `q.scale` reaching 1.0000 is the fact; the colour is the corroboration.
local function readQuota()
	local bar = child(Workspace, 'Monitors', 'QuotaControlRoomMonitor', 'Screen',
		'MonitorUI', 'MainMonitorFrame', 'QuotaFrame', 'EnergyProgressFrame', 'BarFrame')
	if bar == nil then return end
	putText('q.scale', string.format('%.2f', bar.Size.X.Scale))
	local c = bar.BackgroundColor3
	putText('q.barColor', math.floor(c.R * 255 + 0.5) .. ',' ..
		math.floor(c.G * 255 + 0.5) .. ',' .. math.floor(c.B * 255 + 0.5))

	-- ---- the shift clock, which is how the operator knows the core is UP ----
	-- `B1`: 看 TimeLabel，如果时间 > 12:00PM 就说明开机了. This matters because the
	-- recorder is injected on a cold core and the run opens with no shift in
	-- progress: "the core is up" and "the shift has started" are the same event
	-- here, and this label is the operator s own instrument for it.
	--
	-- THE TEXT IS THE FACT AND THE NUMBER IS THE READING. Nothing about the
	-- format is assumed: the raw string goes out every time it changes, and the
	-- derived values are written only when the string actually parses. A clock
	-- that reads `12:00PM` with no space and one that reads `12:00 PM` with one
	-- both parse; a clock whose format this file has never seen degrades to the
	-- raw text alone, which still answers the question by eye and can be
	-- re-derived from the file later without spending another run.
	--
	-- The number is MINUTES PAST 12:00PM, walked forward around the 12-hour dial:
	-- 12:00PM is 0, 1:00PM is 60, 11:00PM is 660, 12:00AM is 720, 11:59AM is
	-- 1439. That is the one ordering in which the operator s rule is a simple
	-- comparison -- `q.up` is `q.clock > 0`, i.e. later than 12:00PM -- and a
	-- 12-hour dial cannot give that ordering without being told which noon the
	-- shift opened on. If the dial is ever seen wrapping, the raw text is what
	-- says so, and this comment is what has to change.
	local clock = child(Workspace, 'Monitors', 'QuotaControlRoomMonitor', 'Screen',
		'MonitorUI', 'MainMonitorFrame', 'TimeFrame', 'TimeLabel')
	if clock ~= nil then
		local raw = clock.Text
		if type(raw) == 'string' and raw ~= '' then
			local text = raw:gsub('%s+', ' ')
			putText('q.timeText', text)
			local hh, mm, ap = string.match(text, '(%d+):(%d+)%s*(%a%a)')
			if hh ~= nil then
				local h, m = tonumber(hh), tonumber(mm)
				local pm = string.upper(ap) == 'PM'
				local mins
				if pm and h == 12 then mins = m
				elseif pm then mins = h * 60 + m
				elseif h == 12 then mins = 720 + m
				else mins = 720 + h * 60 + m
				end
				put('q.clock', mins)
				put('q.up', mins > 0)
			end
		end
	end
end

-- Said once, out loud, in the log and on the console, because it is the one
-- condition that has already cost a whole run and there is no way to notice it
-- from inside a file that is being written correctly.
local samAnnounced = false
local function announceSam()
	if samAnnounced or last['sam.on'] == nil then return end
	samAnnounced = true
	if last['sam.on'] == true then
		-- Stated, not advised. The old line told the operator to turn SAM off
		-- before arming the driver, and the operator has since said SAM is off by
		-- default, is his to control, and is not the driver s business (`D8`).
		-- An instruction inside a recorder is a claim that the recorder knows
		-- better than the person reading it, and here it did not.
		emitEvt('SAM', 'SAM IS ON at inject')
		print('[rec] NOTE: SAM is ON at inject. It is off by default and the')
		print('[rec] NOTE: operator controls it; the recorder only records it.')
	else
		emitEvt('SAM', 'SAM is off at inject')
	end
end

-- The shift clock s crossings, said once each. `q.clock` is already written on
-- change by readQuota; what this adds is a NAME for the moment the shift starts,
-- because that moment is buried in a number otherwise. The recorder is injected
-- before the shift begins, so the crossing of 12:00PM is the boundary between
-- "waiting" and "the run is live" -- the thing a reader of the file has to
-- locate by hand to line the recording up against the operator s own memory.
--
-- The first read is reported as a state and not as an arrival: injected
-- mid-shift, the clock is already past 12:00PM, and saying "it just passed"
-- would be inventing a crossing that happened before the script existed.
local clockSeen, clockUp, clockStartedUp = false, false, false
local function announceClock()
	local up = last['q.up']
	if up == nil then return end
	if not clockSeen then
		clockSeen, clockUp, clockStartedUp = true, up, up
		if up then
			emitEvt('CLOCK', 'the clock already reads past 12:00PM at inject; the core is up')
		else
			emitEvt('CLOCK', 'the clock reads ' .. tostring(last['q.timeText']) ..
				' at inject; the core is not up yet')
		end
		return
	end
	-- A dial that was already past noon at inject has to travel the whole 12-hour
	-- circle before it reads past noon again, so every later transition is the
	-- DIAL MOVING and not the boundary this recorder was built to announce. What
	-- is actually at 12:00PM is the place speaking about itself, not an
	-- inference: `12PM marks the beginning of the Equinox Event`
	-- (`INGAME_MANUAL` 114 and 148), against a shift of 6:00 AM to 6:00 PM
	-- (`DECISIONS` 28). Noon is mid-shift, so a shift start there is wrong.
	--
	-- It was wrong out loud on 2026-09-26: a file injected with the core up
	-- (`Data/flow/original_260926-230049`) emitted `the clock is back at
	-- 12:00 PM` and then `the clock passed 12:00PM: the shift has started`, 60 s
	-- apart, in the middle of a shift, and `m.temp` held 12865 -> 12979 F across
	-- both. The second line is indistinguishable from the real crossing because
	-- it IS the real crossing -- the inject state is the whole difference between
	-- a shift start and a wrap, which is why the first read is kept.
	--
	-- The observation is not dropped, only the claim. The raw text still goes out
	-- and readQuota still writes q.clock / q.up, so the moment stays in the file
	-- and can be re-read later. Refusing to over-interpret a reading is not the
	-- same as discarding it.
	if clockStartedUp then
		if up ~= clockUp then
			clockUp = up
			emitEvt('CLOCK', 'the clock moved to ' .. tostring(last['q.timeText']) ..
				' -- the dial, not a shift boundary: the core was already up at inject')
		end
		return
	end
	if up and not clockUp then
		clockUp = true
		emitEvt('CLOCK', 'the clock passed 12:00PM: the shift has started')
		print('[rec] CLOCK: the core is up; the shift has started.')
	elseif not up and clockUp then
		clockUp = false
		emitEvt('CLOCK', 'the clock is back at ' .. tostring(last['q.timeText']))
	end
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
			-- Written as an if, not as `and nil or`. That idiom returns its
			-- middle operand only when the middle is truthy, so with nil in the
			-- middle it can never yield nil -- and yielding nil is the whole
			-- point here, because "this client has never seen a click" is the
			-- 18:01 case this section exists for. The compact form evaluated
			-- `sample - nil` and threw on the first call.
			local since = nil
			if clickPoll ~= nil then since = sample - clickPoll end
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
-- There is exactly one reader and exactly one writer. This project has lost
-- real runs to a second dispatcher that looked like the first and disagreed
-- with it, so nothing here reads state or emits a line outside this function.
local function pollOnce()
	now = os.clock()
	sample = sample + 1

	if lampDirty then scanLamps() end
	changed = {}
	changedCtrl = {}

	readReactor()
	readFans()
	readCBL()
	readCoolant()
	readStats()
	readReadouts()
	readLamps()
	readPanels()
	readSam()
	readEndScreens()
	readQuota()
	announceSam()
	announceClock()

	if #changed > 0 then
		local head = 'S ' .. tostring(sample) ..
			' t=' .. string.format('%.2f', now - t0) ..
			' dt=' .. tostring(math.floor((now - lastPoll) * 1000 + 0.5))
		local per = Config.MaxPairsPerLine
		for i = 1, #changed, per do
			local chunk = {}
			for j = i, math.min(i + per - 1, #changed) do
				chunk[#chunk + 1] = changed[j]
			end
			emit(head .. ' ' .. table.concat(chunk, ' '))
		end
	end
	-- After the batch line, so the change is on the page before the accusation
	-- about it is. The pass reads the list the readers above filled.
	reportUnattributed()

	lastPoll = now

	-- ---- flow boundary ----
	-- Temperature and nothing else, which is a measurement rather than a
	-- simplification. This line used to read `(out ~= nil and out > 0) or ...`
	-- with out taken from `last['m.out']`, and that arm has never once fired:
	-- `m.out` does not appear in a single one of the captures on disk, so
	-- last['m.out'] is always nil. The output does exist -- it reads fine as the
	-- readout key t.ReadingsFrame.OutputLabel -- but it is not where this was
	-- looking, and wiring the arm up would BREAK the boundary instead of
	-- repairing it: in the 18:01 capture the output never fell below 60 even at
	-- the bottom of the dip, so `out > 0` would have held isRunning true the
	-- whole way through and DOWN would never have fired at all. A reactor that
	-- never reads as down is a reactor with no flow to record.
	local tempF = last['m.temp']
	local isRunning = (tempF ~= nil and tempF >= Config.CoreThresholds[1])

	-- The driver reads the same two numbers the boundary does, computed once
	-- above rather than twice. A second copy of isRunning is a second opinion,
	-- and two opinions about whether the core is lit is how this project once
	-- spent a day on a reactor that had been running the whole time.
	local okDrive, driveErr = pcall(driveStep, tempF, isRunning, pollDt)
	if not okDrive then
		emitEvt('DRIVEERR', tostring(driveErr))
		drive.on = false
		drive.verdict = 'errored'
	end

	if not flowArmed then
		if isRunning then
			lowRun = lowRun + 1
			if lowRun >= Config.DebounceSamples then
				flowArmed = true
				emitPhase('RUN', 'armed')
			end
		else
			lowRun = 0
		end
		return false
	end

	if isRunning then
		lowDown = 0
		if sawDown and settle == 0 then
			lowRun = lowRun + 1
			if lowRun >= Config.DebounceSamples then
				emitPhase('UP')
				settle = Config.SettleSamples
				lowRun = 0
			end
		end
		if settle > 0 then
			settle = settle - 1
			if settle == 0 then return true end
		end
	else
		if not sawDown then
			lowDown = lowDown + 1
			if lowDown >= Config.DebounceSamples then
				sawDown = true
				emitPhase('DOWN')
			end
		end
	end
	return false
end

-- ========================== END OF SHIFT ==================================
-- The file has to be sealed by something that NOTICES the shift ending, and the
-- 18:35 run is the measurement that says so: s.GameActive went false on the very
-- last sample the script ever took, no rule looked at it, and the client was
-- killed during the task.wait that followed. 1.4 MB of good data, and no receipt.
--
-- The signals are read in order of how much they can be trusted rather than in
-- order of how early they fire, because sealing early is the one way this
-- function can lose data:
--
--   * s.GameActive true -> false is checked first and seals with no dwell. It
--     is the game s own statement that the session is over, and the 18:35 tail
--     shows it arriving in the same poll as the shutdown screen and the final
--     temperature -- so acting on it costs the file nothing.
--   * s.GameFail is the same statement from a narrower cause, and
--     s.MainframeMeltdown is NOT the same statement at all -- it is the machine
--     room, not the core, and it is named as such below.
--   * The temperature is a PREDICTION of the end and not the end, so it waits;
--     it only ever fires if the flags above never do. Both directions are read
--     now: the cold arm was always here, and the hot arm is the core meltdown
--     rule the operator gave, which the machine-room flag had been standing in
--     for by mistake.
--
-- Every flag is read as an EDGE, never as a level, and `everRan` closes the same
-- hole for the temperature arms. The reason is the shift this recorder is now
-- aimed at: a NEW SHIFT OPENS WITH THE CORE COLD. A cold core is below the
-- cold-trip line by definition and might open with the session flags unset, so a
-- level test would seal the file two seconds after inject with nothing recorded.
-- "Tripped down" is a claim about a core that was up, and only a core that has
-- been up can make it.
local everRan = false
local coldPolls, hotPolls, downPolls, deadPolls = 0, 0, 0, 0
local flagWas = {}
local function flagEdge(key, from, to)
	local v = last[key]
	if v == nil then return false end
	local was = flagWas[key]
	flagWas[key] = v
	if was == nil then return false end
	return was == from and v == to
end

local function endReason()
	local t = last['m.temp']
	if type(t) == 'number' and t >= Config.CoreThresholds[1] then everRan = true end

	if flagEdge('s.GameActive', true, false) then
		return 'shift over (GameActive true to false)'
	end
	if flagEdge('s.GameFail', false, true) then
		return 'shift failed (GameFail false to true)'
	end
	-- The machine room s meltdown, and it is named as that. The operator
	-- separated the two (`D9`: "MainframeMeltdown 是机房熔毁又不是核心熔毁"), and the
	-- separation is not pedantry -- the 18:35 run is the measurement. That flag
	-- went true at t=719.86 with the monitor reading about 13000 F, and the old
	-- label turned it into a 39000-degree core meltdown the file had never seen.
	-- A wrong cause in a receipt is worse than no cause: it is the one line a
	-- reader trusts when they are not going to re-derive the run.
	if flagEdge('s.MainframeMeltdown', false, true) then
		return 'machine room meltdown (MainframeMeltdown false to true)'
	end
	-- Nothing below this line can fire on a core that never ran, which is what
	-- keeps a cold opening from sealing itself.
	if not everRan then return nil end

	if type(t) == 'number' and t < Config.LowTripF then
		coldPolls = coldPolls + 1
		if coldPolls >= Config.SealColdSamples then
			return 'cold trip (under ' .. tostring(Config.LowTripF) .. ' F for ' ..
				tostring(coldPolls) .. ' polls)'
		end
	else
		coldPolls = 0
	end
	-- The core meltdown rule, and the only arm here that reads the hot end of
	-- the scale. `everRan` is above it and does not help this arm distinguish
	-- anything -- a core that never ran cannot read 39000 -- so the dwell is what
	-- keeps it honest: one bad readout is not a verdict.
	if type(t) == 'number' and t > Config.MeltdownF then
		hotPolls = hotPolls + 1
		if hotPolls >= Config.SealHotSamples then
			return 'core meltdown (over ' .. tostring(Config.MeltdownF) .. ' F for ' ..
				tostring(hotPolls) .. ' polls)'
		end
	else
		hotPolls = 0
	end
	if sawDown then
		downPolls = downPolls + 1
		if downPolls >= Config.SealDownSamples then
			return 'held down ' .. tostring(downPolls) .. ' polls with no end signal'
		end
	else
		downPolls = 0
	end
	-- The only arm that does not need an edge, for a session that was already
	-- over when the script arrived and so can never produce one. `everRan` is
	-- still required, so it cannot fire on a cold start; a cold start that never
	-- lights up is sealed by the button, which is the one ending a human is
	-- always present for.
	if last['s.GameActive'] == false then
		deadPolls = deadPolls + 1
		if deadPolls >= Config.SealDeadSamples then
			return 'GameActive false for ' .. tostring(deadPolls) .. ' polls'
		end
	else
		deadPolls = 0
	end
	return nil
end

local function main()
	emit('# The Reactor Game -- original-game change recorder v1.0')
	emit('# constraint: only changed values are written; no heartbeat')
	local player = Players.LocalPlayer
	emit('# session ' .. stamp ..
		' placeId=' .. tostring(game.PlaceId) ..
		' jobId=' .. tostring(game.JobId) ..
		' player=' .. ((player and player.Name) or 'nil') ..
		' transport=' .. (httpFn and ('http' .. tostring(Config.Port))
			or (haveWritefile() and 'writefile' or 'NONE')))
	emit('# keys r=reactor m=monitor x=unreadable c=control s=stats z=lamp t=readout')
	emitEvt('START', 'reactorFrame=' .. tostring(ReactorFrame ~= nil) ..
		' thermal=' .. tostring(ThermalConsole ~= nil) ..
		' cbl=' .. tostring(CBLConsoles ~= nil) ..
		' power=' .. tostring(PowerFrame ~= nil) ..
		' stats=' .. tostring(MainData ~= nil) ..
		' logs=' .. tostring(LogsFrame ~= nil) ..
		' hooks=' .. tostring(hooked))
	-- `readouts` is the count the TMAP manifest will expand to. It is in the
	-- receipt too, because "the sweep found 0 labels" and "the sweep found 90
	-- labels and none of them ever changed" are different results and a bare
	-- absence of t.* lines cannot tell them apart.
	readoutDirty = true
	buildReadouts()
	emitEvt('READOUTS', 'found=' .. tostring(readoutCount) ..
		' distinct=' .. tostring(readoutDistinct) ..
		' monitors=yes consoles=*Label')

	local consoles = Workspace:FindFirstChild('Consoles')
	if consoles then
		consoles.DescendantAdded:Connect(function() lampDirty = true readoutDirty = true end)
		consoles.DescendantRemoving:Connect(function() lampDirty = true readoutDirty = true end)
	end
	-- The monitors rebuild too -- the whole point of MonitorBootButton is that
	-- the screen is not there until it is switched on, and a cached readout list
	-- taken before boot would leave every screen label unread for the run.
	for _, name in ipairs({'Monitors', 'MonitorsFacility'}) do
		local root = Workspace:FindFirstChild(name)
		if root then
			root.DescendantAdded:Connect(function() readoutDirty = true end)
			root.DescendantRemoving:Connect(function() readoutDirty = true end)
		end
	end

	-- In-game log messages: new children of the log monitor, never re-read.
	if LogsFrame then
		local known = {}
		for _, c in ipairs(LogsFrame:GetChildren()) do known[c] = true end
		LogsFrame.ChildAdded:Connect(function(c)
			local t = child(c, 'TextLabel') or c:FindFirstChildWhichIsA('TextLabel')
			local txt = t and t.Text
			if type(txt) == 'string' and txt ~= '' then
				emitEvt('LOG', txt:gsub('%s+', ' '))
			end
		end)
	end

	-- The baseline. Every key is new here, so this is the one large batch in the
	-- file; every line after it is a difference.
	lampDirty = true
	now = os.clock()
	lastPoll = now
	sample = sample + 1
	changed = {}
	scanLamps()
	readoutDirty = true
	readReactor(); readFans(); readCBL(); readCoolant(); readStats(); readReadouts(); readLamps()

	local base = {}
	for i = 1, #changed do base[i] = changed[i] end
	local per = Config.MaxPairsPerLine
	for i = 1, #base, per do
		local chunk = {}
		for j = i, math.min(i + per - 1, #base) do
			chunk[#chunk + 1] = base[j]
		end
		emit('B ' .. tostring(sample) .. ' t=' .. string.format('%.2f', now - t0) ..
			' ' .. table.concat(chunk, ' '))
	end
	flush()

	-- A slow safety rescan of the lamp manifest, in case a rebuild slipped past
	-- the change signals. Only differences are emitted, so this is free.
	local lastRescan = 0
	local lastFlush = os.clock()

	while true do
		-- Opened before the poll and closed after the wait, so this covers the
		-- whole period and not just the part the poll took. A poll that took
		-- longer than the configured wait is not a poll that never happened.
		local iterStart = os.clock()
		local ok, done = pcall(pollOnce)
		if not ok then emitEvt('POLLERR', tostring(done)) end

		-- Ahead of every other check, and in the same iteration that saw the
		-- signal: the client does not wait for the next poll, and the whole
		-- reason this exists is that the 18:35 run died in the task.wait below.
		local ended = endReason()
		if ended then seal(ended) return end

		if done then seal('flow complete') return end
		if sample >= Config.MaxSamples then
			seal('sample cap reached, down=' .. tostring(sawDown)) return
		end
		if buoy.unseal then seal('user seal') return end

		if sample - lastRescan >= 240 then
			lastRescan = sample
			lampDirty = true
			readoutDirty = true
		end
		if os.clock() - lastFlush >= Config.FlushSeconds then
			lastFlush = os.clock()
			flush()
		end
		task.wait(Config.SampleInterval)
		pollDt = os.clock() - iterStart
	end
end

-- ========================== UI ============================================
-- The user has to know when the flow has been captured, because the whole point
-- of the run is that it ends. The panel shows the phase and the counters live
-- and the button seals on demand.
local function buildUi()
	local player = Players.LocalPlayer
	if player == nil then
		player = Players:GetPropertyChangedSignal('LocalPlayer') and nil
	end
	if player == nil then return end
	local pg = player:WaitForChild('PlayerGui', 15)
	if pg == nil then return end

	local gui = Instance.new('ScreenGui')
	gui.Name = 'TRGRecorder'
	gui.ResetOnSpawn = false
	gui.Parent = pg

	local panel = Instance.new('Frame')
	panel.Size = UDim2.new(0, 274, 0, 92)
	panel.Position = UDim2.new(0.01, 0, 0.01, 0)
	panel.BackgroundColor3 = Color3.fromRGB(16, 18, 22)
	panel.BackgroundTransparency = 0.15
	panel.Parent = gui
	local corner = Instance.new('UICorner')
	corner.CornerRadius = UDim.new(0, 5)
	corner.Parent = panel

	local text = Instance.new('TextLabel')
	text.Size = UDim2.new(1, -10, 1, -10)
	text.Position = UDim2.new(0, 5, 0, 5)
	text.BackgroundTransparency = 1
	text.Font = Enum.Font.Code
	text.TextSize = 12
	text.TextXAlignment = Enum.TextXAlignment.Left
	text.TextYAlignment = Enum.TextYAlignment.Top
	text.TextColor3 = Color3.fromRGB(220, 228, 236)
	text.Text = 'rec: starting'
	text.Parent = panel

	local btn = Instance.new('TextButton')
	btn.Size = UDim2.new(0, 150, 0, 30)
	btn.Position = UDim2.new(0.01, 0, 0.01, 82)
	btn.Text = 'SEAL NOW'
	btn.TextColor3 = Color3.new(1, 1, 1)
	btn.BackgroundColor3 = Color3.fromRGB(160, 34, 34)
	btn.Font = Enum.Font.GothamMedium
	btn.TextSize = 14
	btn.Parent = gui
	local c2 = Instance.new('UICorner')
	c2.CornerRadius = UDim.new(0, 4)
	c2.Parent = btn
	btn.MouseButton1Click:Connect(function()
		buoy.unseal = true
		btn.Text = 'SEALING'
	end)

	-- The driver switches a live reactor off by itself, which is a real change to
	-- the world and not something to leave with no way out. Disarming only stops
	-- FUTURE presses: a press already in flight has already happened, and the
	-- proof window it opened is what tells the reader whether it did anything.
	local drvBtn = Instance.new('TextButton')
	drvBtn.Size = UDim2.new(0, 116, 0, 30)
	drvBtn.Position = UDim2.new(0, 160, 0.01, 82)
	drvBtn.Text = 'DRIVER: ' .. (drive.on and 'ON' or 'OFF')
	drvBtn.TextColor3 = Color3.new(1, 1, 1)
	drvBtn.BackgroundColor3 = drive.on and Color3.fromRGB(34, 96, 160)
		or Color3.fromRGB(60, 60, 60)
	drvBtn.Font = Enum.Font.GothamMedium
	drvBtn.TextSize = 14
	drvBtn.Parent = gui
	local c3 = Instance.new('UICorner')
	c3.CornerRadius = UDim.new(0, 4)
	c3.Parent = drvBtn
	drvBtn.MouseButton1Click:Connect(function()
		drive.on = not drive.on
		if not drive.on then
			drive.verdict = 'disarmed-by-user'
		elseif drive.state == 'inert' then
			-- Resuming an inert driver would press the same dead controls again.
			drive.state = 'arming'
			drive.armT = 0
			drive.verdict = 'rearmed'
		end
		drvBtn.Text = 'DRIVER: ' .. (drive.on and 'ON' or 'OFF')
		drvBtn.BackgroundColor3 = drive.on and Color3.fromRGB(34, 96, 160)
			or Color3.fromRGB(60, 60, 60)
		emitEvt('DRIVE', 'user ' .. (drive.on and 're-armed' or 'disarmed'))
	end)

	buoy.text = text
	buoy.btn = btn
	buoy.drvBtn = drvBtn
end

local function buildHotkey()
	task.spawn(function()
		local ok = pcall(function()
			local uis = game:GetService('UserInputService')
			uis.InputBegan:Connect(function(input)
				if input.KeyCode == Config.SealKey then
					buoy.unseal = true
					print('[rec] seal key pressed')
				end
			end)
		end)
		if not ok then print('[rec] hotkey unavailable, use the button') end
	end)
end

local function refreshLoop()
	while true do
		if buoy.text and buoy.text.Parent then
			local phaseName = 'PRE'
			if flowArmed then phaseName = sawDown and (settle > 0 and 'UP' or 'DOWN/UP') or 'RUN' end
			buoy.text.Text = string.format(
				'phase %s  sample %d  lines %d'
				.. string.char(10) ..
				'seg %d  buf %d B  fails %d'
				.. string.char(10) ..
				'drop %d  spill %d  evt %d'
				.. string.char(10) ..
				'drv %s %s  shut %d/%d start %d/%d',
				phaseName, sample, lines, segNo, bufBytes, postFails,
				dropped, spilled, evtNo,
				drive.state, drive.verdict,
				drive.shutIdx - 1, #shutCandidates,
				drive.startIdx - 1, #startCandidates)
		end
		task.wait(0.25)
	end
end

-- ========================== GO ============================================
-- The whole startup runs inside one pcall whose failure path reports, emits and
-- seals. An injector script that dies between "loaded" and "recording" looks
-- exactly like a script that is recording nothing, and there is no console to
-- read afterwards -- so a silent death here is the one outcome that must not be
-- possible. Anything that throws gets named in the file it was supposed to fill.
task.spawn(function()
	local ok, err = pcall(function()
		pcall(buildUi)
		task.spawn(buildHotkey)
		task.spawn(refreshLoop)

		hookAll()
		print('[rec] hooked ' .. tostring(hooked) .. ' detectors -> ' .. NAME)

		main()
	end)
	if not ok then
		print('[rec] STARTUP FAILED: ' .. tostring(err))
		pcall(function() emitEvt('FATAL', tostring(err)) end)
		pcall(function() seal('startup failed: ' .. tostring(err)) end)
	end

	if buoy.text then
		buoy.text.Text = 'SEALED  samples ' .. tostring(sample) ..
			'  lines ' .. tostring(lines) .. '  seg ' .. tostring(segNo)
	end
	if buoy.btn then
		buoy.btn.Text = 'SEALED'
		buoy.btn.BackgroundColor3 = Color3.fromRGB(38, 128, 48)
	end
	print('[rec] done. samples ' .. tostring(sample) .. ' lines ' .. tostring(lines) ..
		' segments ' .. tostring(segNo) .. ' dropped ' .. tostring(dropped))
end)
