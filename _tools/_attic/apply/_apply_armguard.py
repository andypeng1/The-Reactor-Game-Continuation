"""The arm window must not time out on a core that is reading as RUNNING.

THE DEFECT THIS CLOSES, and it is one I introduced in the same session as the fix
it belongs to. Removing the upper clamp from the measured dt was right -- thirty
real seconds are thirty real seconds -- but it exposed an assumption the arm
window had been making without ever stating it: that no single poll is longer
than DriveArmSeconds.

The arming branch adds dt to armT and, the moment armT reaches 20, decides the
core is cold and goes inert. The debounce needs DebounceSamples polls of running
before flowArmed is true, so there is a window in which the core IS running and
the arm timer can already have expired. Under the old constant dt that window was
80 polls wide and nothing could cross it in one step. Under a measured dt it is
one step wide: the FIRST poll is the one with no measured predecessor and the
only one carrying the initial readout and lamp sweeps, and nothing bounds how
long it takes. A first poll of twenty seconds or more credits armT with twenty
seconds at once, `tempF` is not nil because the core is fine, and the driver
reports `cold-at-inject` and stops -- on a healthy running reactor, on the one
attempt that was available.

The fix is not a clamp, and it is not a bigger number. It is to notice that the
timeout is a claim about a COLD core, and a core reading as running is not that
claim's subject. `if isRunning then return end` keeps the timer honest and lets
the debounce finish, which is what the comment at the top of this branch has said
it wanted all along: twenty seconds of UNBROKEN COLD, not twenty seconds of
elapsed time that has not been checked against anything.

Scenario S8 covers it and is mutation-tested: with the guard removed it fails
with the driver inert on a core that was running the whole time.
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

src = rep(src, """				drive.verdict = 'no-temp-readout'
				return
			end
			-- It used to light the core here.""", """				drive.verdict = 'no-temp-readout'
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
			-- It used to light the core here.""", "arm-guard")

raw = src.encode("utf-8")
P.write_bytes(raw)

print("wrote %s" % P)
print("  bytes %d -> %d" % (before, len(raw)))
print("  lines %d" % raw.count(b"\n"))
print("  backslash bytes %d  (must be 0)" % raw.count(0x5C))
print("  long-bracket close %d  (must be 0)" % raw.count(b"]==]"))
