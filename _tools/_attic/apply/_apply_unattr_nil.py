"""Fix the `and nil or` idiom in reportUnattributed -- caught by the harness.

WHAT WAS WRONG. The line read

    local since = (clickPoll == nil) and nil or (sample - clickPoll)

which is the classic Lua idiom with its middle case removed. `X and Y or Z`
returns Y only when Y is TRUTHY; with Y = nil the expression is
`(false) or Z` or `(nil) or Z`, and both fall through to Z. So the branch that
was supposed to yield nil -- the one guarding the whole case of "this client has
never seen a click", which is the 18:01 case the section was written for --
evaluated `sample - nil` instead and threw.

It threw on the FIRST call, in a harness, which is the only reason it is not a
line that would have run inside the one attempt available: the error surfaces in
reportUnattributed, whose caller is not pcall-wrapped, so the poll would have
died and the recording with it.

The idiom is fine everywhere else in this file where it is used -- the three-way
DRIVE verdict has a non-nil string in the middle -- which is exactly why this one
read as correct. An idiom that works in six places and is wrong in the seventh
is not a mistake a reader catches; it is a mistake a test catches.
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

src = rep(src, """			local since = (clickPoll == nil) and nil or (sample - clickPoll)
""", """			-- Written as an if, not as `and nil or`. That idiom returns its
			-- middle operand only when the middle is truthy, so with nil in the
			-- middle it can never yield nil -- and yielding nil is the whole
			-- point here, because "this client has never seen a click" is the
			-- 18:01 case this section exists for. The compact form evaluated
			-- `sample - nil` and threw on the first call.
			local since = nil
			if clickPoll ~= nil then since = sample - clickPoll end
""", "since-nil")

raw = src.encode("utf-8")
P.write_bytes(raw)

print("wrote %s" % P)
print("  bytes %d -> %d" % (before, len(raw)))
print("  lines %d" % raw.count(b"\n"))
print("  backslash bytes %d  (must be 0)" % raw.count(0x5C))
print("  long-bracket close %d  (must be 0)" % raw.count(b"]==]"))
