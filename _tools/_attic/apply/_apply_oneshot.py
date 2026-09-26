"""One-shot rewrite of the recorder's driver.

The user reported on 2026-09-26 that the core can be switched off and on ONCE.
That is a constraint on the DRIVER, not on the recorder, and it invalidates two
things the driver used to do:

  1. it walked down a candidate list, pressing the next switch when one proved
     inert. A second press is a second spent action.
  2. on a cold core it lit the core first, which spends the startup on the
     opening of the run and leaves none for the half the run exists to capture.

Both are removed, the arm step becomes a human button press, and the proof
windows are widened because there is no longer a retry behind them.

Byte level, with assertions, because every one of these has to land exactly:
a partial application would leave a state machine whose states disagree about
which ones are reachable, and the file still has to parse.
"""

import sys
from pathlib import Path

P = Path(__file__).resolve().parent / "TRG_original_recorder.luau"

T = "\t"


def rep(src, old, new, tag):
    n = src.count(old)
    if n != 1:
        sys.exit("anchor %s matched %d times, wanted exactly 1" % (tag, n))
    return src.replace(old, new)


src = P.read_bytes().decode("utf-8")
before_bytes = len(src.encode("utf-8"))

# ---------------------------------------------------------------- header ----
src = rep(src, """-- OPERATING ITSELF: the DRIVER section presses the switches, so a complete flow
--   can be captured with nobody at the console. It needs one thing the rest of
--   this file does not: the injector s `fireclickdetector`. Without it the
--   driver disarms itself, says so in the receipt and on the panel, and the run
--   falls back to exactly the manual recorder it was before. With it, the run
--   is: inject while the core is hot (or cold, it will light it), and wait --
--   the recorder seals itself when the flow completes.
""", """-- OPERATING ITSELF: the DRIVER section presses the switches, so a complete flow
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
""", "header")

# ---------------------------------------------------------------- config ----
src = rep(src, """	AutoDrive        = true,   -- press the switches itself; the panel can disarm
	DriveArmSeconds  = 20,     -- still cold this long after inject -> light it
	DriveHoldSeconds = 60,     -- run this long before switching it off
	DriveProveSeconds = 25,    -- a press has this long to move the core
	DriveProveF      = 400,    -- ...by this many Fahrenheit degrees, or it is inert
	DriveColdSeconds = 10,     -- stay down this long before lighting it again
""", """	-- AutoDrive is FALSE, and the default is the point rather than a safe
	-- setting. An action that can be spent once is not one a recorder takes the
	-- instant it is injected; the DRIVER button is the gate, and the human at
	-- the console is who decides when the single attempt begins. Everything
	-- AFTER that press is unattended, which is the part that needed a machine:
	-- nobody can hit a lever at the right second for three minutes running.
	AutoDrive        = false,  -- arm by hand; the button spends the attempt
	DriveArmSeconds  = 20,     -- still cold this long after inject -> the core was cold
	DriveHoldSeconds = 60,     -- run this long before switching it off
	-- The prove windows are wide on purpose. A press that works proves itself in
	-- seconds and waits for nothing; a press that does not now costs a wait
	-- instead of a second attempt, because with one attempt there is no retry to
	-- fall back on. A window that expires early would end the run with a wrong
	-- verdict and nothing left to spend on a right one.
	DriveProveSeconds = 40,    -- a press has this long to move the core
	DriveProveF      = 400,    -- ...by this many Fahrenheit degrees, or it is inert
	DriveColdSeconds = 30,     -- stay down this long before lighting it again
""", "config")

# ------------------------------------------------------- on / verdict / -----
src = rep(src, """drive.on = Config.AutoDrive and fireClick ~= nil
drive.verdict = drive.on and 'unsupported' or 'off-no-fireclickdetector'
""", """drive.on = Config.AutoDrive and fireClick ~= nil
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
""", "drive-on")

# ---------------------------------------------- arming: refuse a cold core ----
src = rep(src, """			emitEvt('DRIVE', 'core cold after ' .. tostring(Config.DriveArmSeconds) ..
				's; lighting it first tempF=' .. tostring(tempF))
			drive.state = 'press_start'
""", """			-- It used to light the core here. That is now refused, and the
			-- reason is arithmetic rather than caution: the target flow is one
			-- shutdown followed by one startup, so a run that spends its startup
			-- on the opening arrives at the end with none left. Refusing costs
			-- nothing a human cannot fix in one action -- start the core by
			-- hand and press DRIVER, and the driver joins the flow at `holding`
			-- exactly as if it had been injected later.
			emitEvt('DRIVE', 'REFUSED core cold at inject after ' ..
				tostring(Config.DriveArmSeconds) .. 's tempF=' .. tostring(tempF))
			print('[rec] DRIVER: the core is cold, and it will not start it --')
			print('[rec] DRIVER: the core switches once. Start it yourself, then')
			print('[rec] DRIVER: press the DRIVER button and leave it alone.')
			drive.state = 'inert'
			drive.verdict = 'cold-at-inject'
""", "arming-cold")

# ------------------------------------------------- press_shut: index 1 only --
src = rep(src, """		local cd = shutCandidates[drive.shutIdx]
		if cd == nil then
			drive.state = 'inert'
			drive.verdict = 'all-shut-inert'
			emitEvt('DRIVE', 'INERT-ALL no shutdown candidate moved the core')
			print('[rec] DRIVER: nothing switched the core off. Seal by hand when ready.')
			return
		end
""", """		-- Index 1 and only index 1. The list can hold more than one name for
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
""", "shut-pick")

src = rep(src, """		press(cd)
		emitEvt('DRIVE', 'press shut#' .. tostring(drive.shutIdx) .. ' ' ..
			pathOf(cd) .. ' tempF=' .. tostring(tempF))
		drive.state = 'proving_shut'
""", """		press(cd)
		-- The counters are the panel s, not the driver s: the panel prints
		-- `shut <shutIdx - 1>/<#candidates>`, so advancing it here is what makes
		-- the panel say one press was spent rather than none.
		drive.shutIdx = 2
		emitEvt('DRIVE', 'press shut ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF))
		drive.state = 'proving_shut'
""", "shut-press")

src = rep(src, """		if drive.proofT >= Config.DriveProveSeconds then
			emitEvt('DRIVE', 'shut INERT ' .. pathOf(drive.proofCd) .. ' after ' ..
				tostring(Config.DriveProveSeconds) .. 's tempF=' .. tostring(tempF))
			print('[rec] DRIVER: ' .. pathOf(drive.proofCd) .. ' did nothing')
			drive.shutIdx = drive.shutIdx + 1
			drive.state = 'press_shut'
		end
""", """		if drive.proofT >= Config.DriveProveSeconds then
			-- Terminal, not a step to the next candidate. The verdict stays one
			-- token because the receipt carries it as a space separated field;
			-- the path, which can contain spaces of its own, goes to the EVT line
			-- and to the file, where a reader can still see which control it was.
			emitEvt('DRIVE', 'shut INERT ' .. pathOf(drive.proofCd) .. ' after ' ..
				tostring(Config.DriveProveSeconds) .. 's tempF=' .. tostring(tempF))
			print('[rec] DRIVER: ' .. pathOf(drive.proofCd) .. ' did nothing.')
			print('[rec] DRIVER: no second press -- the core switches once.')
			drive.state = 'inert'
			drive.verdict = 'shut-inert'
		end
""", "shut-inert")

# ------------------------------------------------- press_start: index 1 only -
src = rep(src, """		local cd = startCandidates[drive.startIdx]
		if cd == nil then
			drive.state = 'inert'
			drive.verdict = 'all-start-inert'
			emitEvt('DRIVE', 'INERT-ALL no startup candidate lit the core')
			print('[rec] DRIVER: nothing lit the core again. Seal by hand when ready.')
			return
		end
""", """		local cd = startCandidates[1]
		if cd == nil then
			drive.state = 'inert'
			drive.verdict = 'no-start-control'
			emitEvt('DRIVE', 'no startup control found, nothing pressed')
			print('[rec] DRIVER: found no startup control. Nothing was pressed.')
			return
		end
""", "start-pick")

src = rep(src, """		press(cd)
		emitEvt('DRIVE', 'press start#' .. tostring(drive.startIdx) .. ' ' ..
			pathOf(cd) .. ' tempF=' .. tostring(tempF))
		drive.state = 'proving_start'
""", """		press(cd)
		drive.startIdx = 2   -- display only, for the same reason as shutIdx
		emitEvt('DRIVE', 'press start ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF))
		drive.state = 'proving_start'
""", "start-press")

src = rep(src, """			drive.verdict = 'start-accepted'
			if drive.shutDone then
				drive.state = 'waiting_up'
			else
				-- The core was cold when this was injected, so this startup is
				-- the run s opening, not its second half. Go back and hold, so
				-- the file gets the shutdown half too instead of stopping here.
				drive.holdT = 0
				drive.state = 'holding'
				drive.verdict = 'lit-cold-core'
			end
			return
""", """			drive.verdict = 'start-accepted'
			-- Always the second half now. The branch that looped back to
			-- `holding` was for a startup that OPENED the run, and that startup
			-- no longer exists -- a cold core is refused at `arming`. Keeping it
			-- would leave a state the machine can no longer reach, and an
			-- unreachable branch is a claim about the machine that nothing tests.
			drive.state = 'waiting_up'
			return
""", "start-accept")

src = rep(src, """		if drive.proofT >= Config.DriveProveSeconds then
			emitEvt('DRIVE', 'start INERT ' .. pathOf(drive.proofCd) .. ' after ' ..
				tostring(Config.DriveProveSeconds) .. 's tempF=' .. tostring(tempF))
			print('[rec] DRIVER: ' .. pathOf(drive.proofCd) .. ' did nothing')
			drive.startIdx = drive.startIdx + 1
			drive.state = 'press_start'
		end
""", """		if drive.proofT >= Config.DriveProveSeconds then
			emitEvt('DRIVE', 'start INERT ' .. pathOf(drive.proofCd) .. ' after ' ..
				tostring(Config.DriveProveSeconds) .. 's tempF=' .. tostring(tempF))
			print('[rec] DRIVER: ' .. pathOf(drive.proofCd) .. ' did nothing.')
			print('[rec] DRIVER: no second press. The core is down; seal when ready.')
			drive.state = 'inert'
			drive.verdict = 'start-inert'
		end
""", "start-inert")

raw = src.encode("utf-8")
P.write_bytes(raw)

print("wrote %s" % P)
print("  bytes %d -> %d" % (before_bytes, len(raw)))
print("  lines %d" % raw.count(b"\n"))
print("  backslash bytes %d  (must be 0)" % raw.count(0x5C))
print("  long-bracket close %d  (must be 0)" % raw.count(b"]==]"))
print("  CRLF %d  bare LF %d" % (raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")))
