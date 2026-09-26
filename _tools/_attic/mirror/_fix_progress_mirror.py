# -*- coding: utf-8 -*-
"""Cut the one stray trailing byte off PROGRESS.md so it matches the module again.

The mirror rule, now measured rather than assumed (see DECISIONS 95): the disk file is the
module content with the single leading newline dropped, plus one trailing newline if it does
not already end with one. PROGRESS's content starts with "\\n" and ends with "\\n", so the disk
file is exactly content[2..] -- no byte added anywhere.

The previous round wrote `content + "\\n"` instead, which happens to agree with the rule for
CLAUDE (content starts '#', ends without a newline) and therefore passed its check -- the same
disk-versus-disk blind spot DECISIONS 89 records. For PROGRESS it left one extra byte.

Ground truth for the check is the ModuleScript's own report: it now prints
hash(c[2..]) = 624c01e9 over 107208 bytes, which is what this file must hash to.
"""
import io
import sys

P = r"D:\rblxTRGproject\PROGRESS.md"

WANT_LEN = 107208
WANT_HASH = "624c01e9"        # module: hash(content[2..]) -- read back, not derived from disk


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


raw = io.open(P, "rb").read()
print("before: len=%d hash=%s tail=%r" % (len(raw), roll(raw), raw[-6:]))
if raw.endswith(b"\n\n"):
    out = raw[:-1]
else:
    print("*** file does not end with a doubled newline -- nothing to undo -- ABORT ***")
    sys.exit(1)

print("after : len=%d hash=%s tail=%r" % (len(out), roll(out), out[-6:]))
ok = len(out) == WANT_LEN and roll(out) == WANT_HASH
print("CHECK  " + ("PASS" if ok else "*** FAIL ***  want len=%d hash=%s" % (WANT_LEN, WANT_HASH)))
if ok:
    io.open(P + ".bakphase33b", "wb").write(raw)
    io.open(P, "wb").write(out)
    print("PROGRESS.md written: %d -> %d" % (len(raw), len(out)))
else:
    print("not written")
