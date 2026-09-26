"""Hand the driver a MEASURED step, instead of the period the config assumes.

WHAT WAS WRONG. driveStep opened with

    local dt = Config.SampleInterval

and advanced every dwell in the function -- armT, holdT, coldT, proofT -- by that
constant. The 18:01 run is the measurement that condemns it: 283 samples over
83.78 s is 3.38 Hz, so the real step was 0.296 s while the constant says 0.25.
Every dwell therefore ran 18 per cent long, and `DriveHoldSeconds = 60` took
70.59 s to elapse -- which is exactly the gap between the log line that announced
"will switch it off in 60s" at t=2.84 and the press it describes at t=73.43.

That is the whole reason it was found: the file states a duration and the
timestamps beside it state a different one, and a person read both. Nothing else
in the run was wrong. The reactor was switched off correctly and on time by the
only clock that matters, which is the game s. What was false was the number the
recorder wrote down about itself.

WHY A PARAMETER AND NOT os.clock() INSIDE. driveStep is executed by
_tools/build_driver_test.py against a simulated core, and a function that reads
the wall clock internally can only be tested by waiting in real time -- which
turns a 300-second scenario into 300 seconds. The caller owns the clock; the
function is a pure step. That is also what makes the defect testable at all: the
harness can hand it a one-second step and assert that the dwell follows the step
rather than the constant, which is scenario S7.

os.clock IS the right clock, and that was measured rather than assumed: in this
engine os.clock() advanced by 2.0112 across a task.wait(2), so it counts wall
time and not CPU time. Had it counted CPU time, the loop beside this function
would have had the same defect for the same reason, and the fix would have had to
reach further than one parameter.
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
before = len(src.encode("utf-8"))

# ------------------------------------------------------- the shared clock ---
src = rep(src, """local lastPoll = t0
""", """local lastPoll = t0
-- How long the previous poll really took, measured by the loop rather than
-- assumed from Config.SampleInterval. The driver advances its dwell timers by
-- this, so that the seconds it announces are the seconds that elapsed: the 18:01
-- run announced 60 s and spent 70.59, because the loop ran at 3.38 Hz against a
-- configured 0.25 s and every dwell was 18 per cent long. Declared here with the
-- rest of the clock for the usual reason -- the loop below assigns it and
-- driveStep, compiled earlier than that assignment, has to see the same name.
local pollDt = Config.SampleInterval
""", "pollDt")

# --------------------------------------------------------- the signature ----
src = rep(src, """local function driveStep(tempF, isRunning)
	if not drive.on then return end
	if drive.state == 'inert' or drive.state == 'done' then return end
	local dt = Config.SampleInterval
""", """local function driveStep(tempF, isRunning, dt)
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
""", "signature")

# ------------------------------------------------------------ the call -----
src = rep(src, """	local okDrive, driveErr = pcall(driveStep, tempF, isRunning)
""", """	local okDrive, driveErr = pcall(driveStep, tempF, isRunning, pollDt)
""", "call")

# ------------------------------------------------------------ the loop -----
src = rep(src, """	while true do
		local ok, done = pcall(pollOnce)
""", """	while true do
		-- Opened before the poll and closed after the wait, so this covers the
		-- whole period and not just the part the poll took. A poll that took
		-- longer than the configured wait is not a poll that never happened.
		local iterStart = os.clock()
		local ok, done = pcall(pollOnce)
""", "loop-head")

src = rep(src, """		task.wait(Config.SampleInterval)
	end
end
""", """		task.wait(Config.SampleInterval)
		pollDt = os.clock() - iterStart
	end
end
""", "loop-tail")

raw = src.encode("utf-8")
P.write_bytes(raw)

print("wrote %s" % P)
print("  bytes %d -> %d" % (before, len(raw)))
print("  lines %d" % raw.count(b"\n"))
print("  backslash bytes %d  (must be 0)" % raw.count(0x5C))
print("  long-bracket close %d  (must be 0)" % raw.count(b"]==]"))
print("  CRLF %d  bare LF %d" % (raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")))
