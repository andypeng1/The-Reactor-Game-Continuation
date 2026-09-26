## Phase 41 - The documentation hit the engine's own ceiling  [DONE]

Scope: close out the section 0.0 step for Phase 40. It turned into a structural change.

The disk halves landed first -- PROGRESS +6208 bytes, DECISIONS +12717 for entries 115-123 -- and then
writing DECISIONS into its ModuleScript was REFUSED outright: Source is capped at 200000 bytes and the
image is 202893. For the first time in this project the divergence ran the other way, with the DISK
ahead and the MODULE stale, and no amount of care would have made it fit. This is not the 40.0K
CLAUDE.md warning, which was a soft context-budget complaint about a perfectly representable file.

DECISIONS is now two modules, cut at ENTRY 75:

    DECISIONS    103355 bytes  roll 2e994db6   entries 1..74
    DECISIONS_2  102387 bytes  roll 191bd85e   entries 75..123

The boundary is an entry number, not a byte offset, so it is a fact about the document rather than
about its length on the day it was cut -- the same reasoning the CLAUDE.md split used when it ordered
itself by section number. verify_docs.py now checks each file against its own module AND asserts the
seam: part 1 must end at 74, part 2 must run contiguously from 75. Two hashes alone would not have
said where the cut was.

The two module halves were built INSIDE Studio, from the module's own existing text plus the new
blocks, and deliberately never transmitted. DECISIONS.md contains two backslashes, both in early
entries quoting Lua code, and section 0.10's escape decoding would have turned them into real
newlines on the way in. The splitter reports which parts carry backslashes so the writer knows which
ones must be moved rather than sent. That is a constraint on the write path, not a defect in the
document, and it is now written down as one.

PROGRESS is at 140880 of the same 200000 -- roughly five phases of headroom at this phase's 12.7K.
Recorded so the next session watches it instead of discovering it the way this one did.

Also updated: README (the module list plus why DECISIONS is two), section 0.0's mapping table, and
docs/TODO.md section 3 -- the console second pass checked off, with new entries for the
StreamingEnabled/spawn finding and for the Source ceiling. verify_docs.py is rc=0 against all five
modules.
