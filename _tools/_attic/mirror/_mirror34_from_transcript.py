# -*- coding: utf-8 -*-
"""Close out the Phase-34 doc mirror without retyping a single byte of the deltas.

The hex deltas for PROGRESS and DECISIONS were emitted by the ModuleScripts themselves
(see DECISIONS 96: the disk mirror is derived from the artefact, never fitted to it).
They are recorded verbatim in the session transcript as an inline tool result, so the
reliable way to get them onto disk is to scrape the transcript, not to reproduce the
hex by hand -- a 8908-character transcription that is 99.9 percent correct is a mirror
that is silently wrong.

Refuses to write unless the finished file, minus its trailing newline, reproduces the
length AND hash the ModuleScript reported. Length alone is not enough: PROGRESS and
DECISIONS have each previously differed by exactly one character at equal length.

Usage:
    python _mirror34_from_transcript.py --dry     # decode and verify, write nothing
    python _mirror34_from_transcript.py           # apply
"""
import glob
import io
import os
import sys

DIR = r"C:\Users\andypeng1NB\.claude\projects\D--rblxTRGproject"
ROOT = r"D:\rblxTRGproject"

# (doc, marker the module's own read-back printed, expected image length, image hash,
#  expected disk-file length before the append, and a string that must appear exactly
#  once in the appended delta so a wrong pick cannot pass the length check by accident.)
#
# The pre-edit disk lengths are the EXPECT figures verify_docs.py already holds, and that is
# the point: the disk file IS the image, byte for byte, with no added newline. Measured this
# round when the first attempt refused -- 108391 on disk against an image of 108391, not the
# 108392 a `content + "\n"` rule would predict. CLAUDE confirms it independently: image 59431
# plus the 2524-byte disk-only section 0.0 equals its 61955 exactly, with no slack for a
# newline. The older "+1" reading in the superseded mirror scripts was fitted to four files
# that happened to look that way; see DECISIONS 96.
DOCS = [
    ("PROGRESS", "PROGRESS LEN=112845 HASH=0f581f5e DELTA=4454",
     112845, "0f581f5e", 108391, b"## Phase 34 - Reactor core rebuilt"),
    ("DECISIONS", "DECISIONS LEN=171835 HASH=1b1d9de7 DELTA=3614",
     171835, "1b1d9de7", 168221, b"97. A RAY CANNOT SEE A PART"),
]

HEXDIGITS = "0123456789abcdef"


def newest_transcript():
    """The session file being written right now -- picked by mtime, same as extract_shot.py.

    A resumed conversation keeps its name, but a fresh session gets a new one, so a
    hardcoded path goes stale exactly when a new session is the case that matters.
    """
    cands = glob.glob(os.path.join(DIR, "*.jsonl"))
    if not cands:
        sys.exit("no transcript found under %s" % DIR)
    return max(cands, key=os.path.getmtime)


def roll(bs):
    """The same 31-polynomial the ModuleScript and verify_docs.py use."""
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def scan(transcript, marker, want_delta):
    """Every hex payload that follows `marker` on one line, longest last.

    Requiring the marker and the payload to share a line is what keeps prose mentions
    of the marker from matching: a hex run has to actually start after it.
    """
    hits = []
    with io.open(transcript, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            i = line.find(marker)
            if i < 0:
                continue
            j = line.find("HEX ", i)
            if j < 0:
                continue
            k = j + 4
            while k < len(line) and line[k] in HEXDIGITS:
                k += 1
            hx = line[j + 4:k]
            if len(hx) == want_delta * 2:
                hits.append(hx)
    return hits


def main():
    dry = "--dry" in sys.argv

    # A line can carry the payload twice (message content and toolUseResult). Both copies
    # are identical, so dedupe by value rather than by position.
    ordered = []
    for name, marker, want_len, want_hash, base_len, sentinel in DOCS:
        ordered.append((name, want_len, want_hash, base_len, sentinel, marker))

    trans = newest_transcript()
    print("transcript: %s" % os.path.basename(trans))
    print()

    plan = []
    for name, want_len, want_hash, base_len, sentinel, marker in ordered:
        delta_len = int(marker.rsplit("DELTA=", 1)[1])
        hits = scan(trans, marker, delta_len)
        uniq = []
        for hx in hits:
            if hx not in uniq:
                uniq.append(hx)
        print("%-9s marker lines carrying a %d-byte payload: %d, distinct: %d"
              % (name, delta_len, len(hits), len(uniq)))
        if len(uniq) != 1:
            print("  *** expected exactly one distinct payload -- cannot choose, ABORT ***")
            return 1
        delta = bytes.fromhex(uniq[0])
        if len(delta) != delta_len:
            print("  *** decoded %d bytes, expected %d -- ABORT ***" % (len(delta), delta_len))
            return 1
        if sentinel not in delta:
            print("  *** payload does not contain %r -- wrong payload, ABORT ***" % sentinel)
            return 1

        path = os.path.join(ROOT, name + ".md")
        raw = io.open(path, "rb").read()
        print("  disk %-14s %d bytes  hash=%s" % (name + ".md", len(raw), roll(raw)))
        if len(raw) != base_len:
            print("  *** disk is %d, expected the pre-edit %d -- ABORT, file untouched ***"
                  % (len(raw), base_len))
            return 1
        if sentinel in raw:
            print("  *** delta already applied -- ABORT (idempotent) ***")
            return 1

        out = raw + delta
        body = out                            # the disk file is the image, byte for byte
        got_len, got_hash = len(body), roll(body)
        print("  -> derived image  len=%d hash=%s" % (got_len, got_hash))
        print("  -> module reports len=%d hash=%s" % (want_len, want_hash))
        ok = (got_len == want_len and got_hash == want_hash)
        print("  -> %s" % ("MATCH" if ok else "*** MISMATCH ***"))
        if not ok:
            print("  *** refusing to write %s ***" % (name + ".md"))
            return 1
        plan.append((name, path, raw, out, delta_len))
        print()

    if dry:
        print("dry run: all %d doc(s) verified, nothing written" % len(plan))
        return 0

    for name, path, raw, out, delta_len in plan:
        io.open(path + ".bak34", "wb").write(raw)
        io.open(path, "wb").write(out)
        print("wrote %s  %d -> %d (delta %+d, backup %s.bak34)"
              % (path, len(raw), len(out), len(out) - len(raw), name))
    return 0


sys.exit(main())
