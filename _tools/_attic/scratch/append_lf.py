#!/usr/bin/env python
"""append_lf.py -- append a text file to another one, forcing LF endings.

    python -X utf8 _tools/_attic/scratch/append_lf.py SRC DST

Why this exists: the editing tool that writes SCRATCH files emits CRLF on this
machine, and `.gitattributes` pins `* text=auto eol=lf`.  Appending those bytes
straight into a doc leaves a file with mixed endings, which git then reports as
modified forever (the "phantom M" -- the diff is empty because the normaliser
eats it on every comparison).  So the appended bytes are normalised HERE, once,
and the docs stay pure LF.

SRC is left alone -- it is a scratch staging file, and deleting it is the
caller's business.
"""

import io
import sys


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    with io.open(src, encoding="utf-8", newline="") as handle:
        text = handle.read().replace("\r\n", "\n").replace("\r", "\n")
    with io.open(dst, "rb") as handle:
        before = handle.read()
    # The separator is the caller's: SRC is expected to start with its own
    # newlines.  Asserted rather than added, so a staging file that forgot them
    # is a red run and not two paragraphs run together.
    if not text.startswith("\n"):
        print("APPEND FAIL: %s does not start with a blank line" % src)
        return 1
    with io.open(dst, "ab") as handle:
        handle.write(text.encode("utf-8"))
    with io.open(dst, "rb") as handle:
        after = handle.read()
    if not after.startswith(before) or len(after) != len(before) + len(
            text.encode("utf-8")):
        print("APPEND FAIL: the write was not a pure append")
        return 1
    if b"\r" in after:
        print("APPEND FAIL: a carriage return made it into %s" % dst)
        return 1
    print("%s: +%d bytes, now %d, still LF"
          % (dst, len(text.encode("utf-8")), len(after)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:               # noqa: BLE001 -- CLAUDE.md 0.6
        import traceback
        traceback.print_exc()
        sys.exit(1)
