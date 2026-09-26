# -*- coding: utf-8 -*-
"""Append the two new record blocks to the disk mirrors, refusing to run on a surprise.

WHY THIS EXISTS. The mirror rule (DECISIONS 96) is that the disk file is the ModuleScript's
string body with the newlines stripped from both ends and exactly one put back:

    diskImage = strip(body) + "\n"

So appending a block T to the body means the disk file becomes:

    new_disk = strip(old_body) + "\n\n" + T + "\n"

which is the same as rstripping the current disk file, adding one blank line, the block, and a
final newline. This script does exactly that, and it ASSERTS the file already hashes to what the
module reported before it appends -- because appending to a file that is already wrong produces a
longer wrong file, and the verifier would then be comparing two unknowns.

The same block text is sent to the Studio module by hand. If the two copies ever differ by one
byte, _tools/verify_docs.py goes red on that document, which is the point: this script is not the
proof, the verifier is.
"""
import io
import os
import sys

D = r"D:\rblxTRGproject"

# Same roll as verify_docs.py, deliberately duplicated rather than imported: a shared helper that
# drifted would make both sides wrong in the same direction.
def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


# name -> (expected length, expected hash, appended block file). Hashes are the ones the modules
# reported BEFORE this append; they are the guard against appending twice or to a stale file.
#
# PROGRESS 134670/3ae50c82 and DECISIONS 190172/12357c16 (the 115-121 block) were appended earlier
# in this same phase and are listed here as history; re-running would now refuse on both, correctly.
# The live job is entry 122, appended against the state those two left behind.
JOBS = [
    ("PROGRESS", 134670, "3ae50c82", "_append_progress.md", None),
    ("DECISIONS", 190172, "12357c16", "_append_decisions.md", None),
    ("DECISIONS", 200396, "26b2e6c0", "_append_decisions_122.md", None),
    # 115-122 are on disk and were never written to the module: Source is capped at 200000 bytes
    # and the module is already 190172 before them. See DECISIONS 123.
    ("DECISIONS", 202893, "755227ab", "_append_decisions_123.md", None),
    # DECISIONS.md has since been split at entry 75 by split_decisions.py; the two live jobs are
    # PROGRESS phase 41 (still one module below the cap) and nothing else.
    ("PROGRESS", 140880, "5fff5139", "_append_progress_41.md", None),
]


def main():
    rc = 0
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name, want_len, want_hash, block_file, live in JOBS:
        if only is not None and not live:
            continue
        path = os.path.join(D, name + ".md")
        raw = io.open(path, "rb").read()
        got_hash = roll(raw)
        if len(raw) != want_len or got_hash != want_hash:
            print("%-10s *** REFUSING: disk is %d/%s, module says %d/%s ***"
                  % (name, len(raw), got_hash, want_len, want_hash))
            rc = 1
            continue

        block_path = os.path.join(D, "_tools", block_file)
        block = io.open(block_path, "rb").read()
        # Trailing whitespace would end up inside the module body verbatim, and a trailing blank
        # line is exactly the kind of thing that differs between the two copies of an append.
        # Normalise it here, once, and say so when it happened rather than silently trimming.
        trimmed = block.rstrip(b"\r\n \t")
        if trimmed != block:
            print("%-10s note: trimmed %d trailing whitespace bytes from the block"
                  % (name, len(block) - len(trimmed)))
        block = trimmed
        if b"\\" in block:
            # Section 0.10: the edit layer decodes Lua escapes once. A backslash in a block that
            # is going into a long-bracket string is safe, but one in a block that ever gets
            # rewritten into a short string is not. Cheaper to forbid it outright.
            print("%-10s *** block contains a backslash (section 0.10) ***" % name)
            rc = 1
            continue
        if b"]==]" in block:
            print("%-10s *** block contains the module terminator ***" % name)
            rc = 1
            continue

        new = raw.rstrip(b"\r\n") + b"\n\n" + block + b"\n"
        io.open(path, "wb").write(new)
        print("%-10s %d -> %d, hash %s -> %s, appended %d bytes"
              % (name, len(raw), len(new), got_hash, roll(new), len(block)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
