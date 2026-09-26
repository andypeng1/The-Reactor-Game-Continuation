# -*- coding: utf-8 -*-
"""One-shot: cut DECISIONS.md into DECISIONS.md + DECISIONS_2.md at an entry boundary.

WHY. ModuleScript.Source is capped at 200000 bytes (DECISIONS 123). DECISIONS reached 205743, so it
cannot be represented as one script any more. This is the CLAUDE.md split's little brother, and it
borrows its shape: the boundary is a fact about the DOCUMENT -- an entry number -- not a byte offset
into today's rendering. Entry 1..74 stay under the name every existing reference already uses;
entries 75.. onwards become DECISIONS_2.

THE LOSSLESSNESS CLAIM, AND WHY IT IS WRITTEN THIS WAY. The tempting proof is "part1 + part2 == the
original", which is true by construction and therefore proves nothing -- the slice could have dropped
a byte at the seam and still passed if the reconstruction dropped it the same way. Section 0.0 records
this exact failure twice (DECISIONS 95, and the splitter that lost its own 327-byte prefix). So the
claim made here is the one that can FAIL:

    raw[:cut].rstrip(b"\\n") + b"\\n\\n" + raw[cut:]  ==  raw

i.e. the blank line at the seam is rebuilt from the mirror rule rather than copied, and the equality
is against the ORIGINAL bytes read before anything was written. If the entries were separated by one
newline there, or three, this goes red instead of quietly producing two plausible files.

The disk files are valid images in their own right: no leading newline, exactly one trailing newline,
because that is what strip(body) + "\\n" produces and the verifier will check it.
"""
import io
import os
import re
import sys

D = r"D:\rblxTRGproject"
CUT_BEFORE = 75  # first entry of part 2


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def main():
    path = os.path.join(D, "DECISIONS.md")
    raw = io.open(path, "rb").read()
    ms = list(re.finditer(rb"(?m)^(\d+)\. ", raw))
    nums = [int(m.group(1)) for m in ms]
    if nums != list(range(1, len(nums) + 1)):
        print("*** entries are not contiguous 1..%d ***" % len(nums))
        return 1
    if CUT_BEFORE not in nums:
        print("*** entry %d is not present ***" % CUT_BEFORE)
        return 1
    cut = ms[nums.index(CUT_BEFORE)].start()

    part1 = raw[:cut].rstrip(b"\n") + b"\n"
    part2 = raw[cut:]

    # The claim that can fail: the seam's blank line is RECONSTRUCTED, not copied.
    rebuilt = part1.rstrip(b"\n") + b"\n\n" + part2
    if rebuilt != raw:
        i = next(k for k in range(min(len(rebuilt), len(raw))) if rebuilt[k] != raw[k])
        print("*** seam does not rebuild: first difference at byte %d ***" % i)
        print("    raw     %r" % raw[max(0, i - 40):i + 40])
        print("    rebuilt %r" % rebuilt[max(0, i - 40):i + 40])
        return 1
    if len(rebuilt) != len(raw):
        print("*** seam rebuilds to %d bytes, original is %d ***" % (len(rebuilt), len(raw)))
        return 1

    for name, bs in (("DECISIONS.md", part1), ("DECISIONS_2.md", part2)):
        if bs.startswith(b"\n") or not bs.endswith(b"\n") or bs.endswith(b"\n\n"):
            print("*** %s is not a valid mirror image at its ends ***" % name)
            return 1
        if b"]==]" in bs:
            print("*** %s contains the module terminator ***" % name)
            return 1
        # Backslashes are REPORTED, not refused. Section 0.10's rule protects the WRITE PATH into
        # Studio -- the edit layer decodes escapes once, so a transmitted backslash-n arrives as a
        # real newline. Content already inside the modules got there by other means and some of it
        # is Lua code samples that legitimately contain the two characters backslash and n. The
        # consequence is a constraint on HOW these files get written, not on whether they may exist:
        # a part containing a backslash must be moved inside Studio from text already there, and
        # never sent through a tool call. Reported here so the writer knows which parts those are.
        if b"\\" in bs:
            print("%s contains %d backslash(es): must be written in-Studio, not transmitted"
                  % (name, bs.count(b"\\")))

    io.open(path, "wb").write(part1)
    io.open(os.path.join(D, "DECISIONS_2.md"), "wb").write(part2)
    print("seam rebuilds exactly: yes (%d bytes)" % len(raw))
    print("DECISIONS    %d roll %s  entries 1..%d" % (len(part1), roll(part1), CUT_BEFORE - 1))
    print("DECISIONS_2  %d roll %s  entries %d..%d" % (len(part2), roll(part2), CUT_BEFORE, nums[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
