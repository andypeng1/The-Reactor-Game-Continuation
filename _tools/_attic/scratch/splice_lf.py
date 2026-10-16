#!/usr/bin/env python
"""splice_lf.py -- insert a text file into another one, ahead of an anchor line.

    python -X utf8 _tools/_attic/scratch/splice_lf.py SRC DST ANCHOR

The middle-of-file sibling of append_lf.py, and it exists for the same reason:
the tool that writes scratch files emits CRLF on this machine, and
`.gitattributes` pins `* text=auto eol=lf`.  The inserted bytes are normalised
HERE, once, so the doc stays pure LF.

ANCHOR is matched against the START of a line, and it must match EXACTLY ONE
line -- asserted, not hoped for (CLAUDE.md 0.13: an anchor that matches in the
wrong place edits the wrong block and says nothing).

SRC is left alone -- it is a scratch staging file.
"""

import io
import sys


def main():
    if len(sys.argv) != 4:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    src, dst, anchor = sys.argv[1], sys.argv[2], sys.argv[3]
    with io.open(src, encoding="utf-8", newline="") as handle:
        text = handle.read().replace("\r\n", "\n").replace("\r", "\n")
    with io.open(dst, encoding="utf-8", newline="") as handle:
        doc = handle.read().replace("\r\n", "\n").replace("\r", "\n")
    lines = doc.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(anchor)]
    if len(hits) != 1:
        print("SPLICE FAIL: anchor %r matches %d line(s) in %s"
              % (anchor, len(hits), dst))
        return 1
    if not text.endswith("\n"):
        text += "\n"
    if not text.startswith("\n"):
        print("SPLICE FAIL: %s does not start with a blank line" % src)
        return 1
    at = hits[0]
    out = "\n".join(lines[:at]) + "\n" + text + "\n".join(lines[at:])
    if "\r" in out:
        print("SPLICE FAIL: a carriage return made it into %s" % dst)
        return 1
    if out.count(anchor) != doc.count(anchor):
        print("SPLICE FAIL: the anchor count changed -- this was not a pure "
              "insert")
        return 1
    with io.open(dst, "wb") as handle:
        handle.write(out.encode("utf-8"))
    print("%s: +%d bytes, now %d, still LF (inserted at line %d)"
          % (dst, len(out.encode("utf-8")) - len(doc.encode("utf-8")),
             len(out.encode("utf-8")), at + 1))
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
