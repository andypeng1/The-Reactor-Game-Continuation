"""Close the false accept the 18:01 capture exposed, and correct one dead claim.

WHAT THE 18:01 RUN SHOWED. The driver went to press the shutdown switch at
t=73.43 with tempF=4895 -- eight seconds AFTER the core had already crossed
below the running threshold, and four seconds into a recovery it had nothing to
do with. It then reported `shut accepted after 0.2s`, because the accept
condition has an arm that says "the core is not running", and that arm was
already true when the window opened. A proof window that accepts a state the
press did not cause is not a proof; it is the appearance of one.

Two changes, one per direction of the same mistake:

  * press_shut refuses to press while the core is not running. "Shut" is a
    press whose only meaning is on a running core, and with one attempt there is
    nobody to spend a second one. It waits, says so once, and presses when the
    core is running again.
  * proving_shut records whether the core was running AT THE PRESS, and the
    "not running" arm only counts when it was. `fell` is unaffected: a 400 F
    drop is a consequence, not a state.

The start side gets the same field for the same reason, though it cannot
currently be wrong -- press_start returns early when the core is already lit.

AND ONE CORRECTION. `isRunning` is documented as "output above zero OR
temperature above the first threshold". The output arm has never fired: `m.out`
does not appear once in any of the four captures on disk, so `last['m.out']` is
always nil. The output exists -- it reads fine as the readout key
t.ReadingsFrame.OutputLabel -- but it is not where this line was looking, and
reviving the arm would BREAK the boundary rather than fix it: in the 18:01
capture the output never fell below 60, even at the bottom of the dip, so
`out > 0` would have held isRunning true throughout and DOWN would never have
fired. The boundary is temperature, and now it says so.
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

# ------------------------------------------------------ drive table fields --
src = rep(src, """	proofRef = nil,
	proofKind = nil,
	proofCd = nil,
""", """	proofRef = nil,
	proofKind = nil,
	proofCd = nil,
	-- What the core was doing at the instant of the press. The proof windows
	-- need it: "not running now" and "not running now AND running then" are two
	-- different facts, and only the second one is evidence about the press.
	proofRunning = nil,
	-- Set while press_shut is declining to press because the core is already
	-- down. It exists so the wait is announced once instead of on every poll.
	waitingRun = false,
""", "drive-fields")

# ------------------------------------------------------------- isRunning ----
src = rep(src, """	-- ---- flow boundary ----
	local tempF = last['m.temp']
	local out   = last['m.out']
	local isRunning = (out ~= nil and out > 0)
		or (tempF ~= nil and tempF >= Config.CoreThresholds[1])
""", """	-- ---- flow boundary ----
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
""", "isRunning")

# ------------------------------------------------- press_shut: needs a run --
src = rep(src, """	if drive.state == 'press_shut' then
		if tempF == nil then return end
""", """	if drive.state == 'press_shut' then
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
""", "press-shut-guard")

src = rep(src, """		drive.proofCd, drive.proofRef, drive.proofKind, drive.proofT =
			cd, tempF, 'shut', 0
""", """		drive.proofCd, drive.proofRef, drive.proofKind, drive.proofT =
			cd, tempF, 'shut', 0
		drive.proofRunning = isRunning
""", "shut-proof-field")

src = rep(src, """		emitEvt('DRIVE', 'press shut ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF))
""", """		emitEvt('DRIVE', 'press shut ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF) ..
			' running=' .. tostring(isRunning))
""", "shut-press-evt")

src = rep(src, """		if fell or (tempF ~= nil and not isRunning) then
""", """		-- `stillDown` carries proofRunning, and that is the whole fix. Without
		-- it, a core that was already down when the window opened satisfies the
		-- arm on the first poll and the press is credited with a shutdown it did
		-- not cause -- which is exactly what `shut accepted after 0.2s` was.
		local stillDown = (not isRunning) and drive.proofRunning == true
		if fell or stillDown then
""", "shut-accept")

# --------------------------------------------- press_start: same field in ----
src = rep(src, """		drive.proofCd, drive.proofRef, drive.proofKind, drive.proofT =
			cd, tempF, 'start', 0
""", """		drive.proofCd, drive.proofRef, drive.proofKind, drive.proofT =
			cd, tempF, 'start', 0
		drive.proofRunning = isRunning
""", "start-proof-field")

src = rep(src, """		emitEvt('DRIVE', 'press start ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF))
""", """		emitEvt('DRIVE', 'press start ' .. pathOf(cd) .. ' tempF=' .. tostring(tempF) ..
			' running=' .. tostring(isRunning))
""", "start-press-evt")

src = rep(src, """		if rose or (tempF ~= nil and isRunning) then
""", """		-- Mirrors `stillDown`. press_start already returns early when the core
		-- is lit, so proofRunning is false here by construction; the field is
		-- read rather than assumed because "cannot currently be wrong" is a
		-- claim about today s code and not about the field.
		local nowUp = isRunning and drive.proofRunning == false
		if rose or nowUp then
""", "start-accept")

raw = src.encode("utf-8")
P.write_bytes(raw)

print("wrote %s" % P)
print("  bytes %d -> %d" % (before, len(raw)))
print("  lines %d" % raw.count(b"\n"))
print("  backslash bytes %d  (must be 0)" % raw.count(0x5C))
print("  long-bracket close %d  (must be 0)" % raw.count(b"]==]"))
print("  CRLF %d  bare LF %d" % (raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")))
