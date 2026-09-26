# -*- coding: utf-8 -*-
"""Apply the Phase-35 doc mirror for the two APPEND documents.

The two payloads were emitted by the ModuleScripts themselves (DECISIONS 96: the disk mirror is
derived from the artefact, never fitted to it) and are recorded verbatim in the session
transcript as an inline tool result. Scraping them out is the only way to move them without a
3.5 KB retyping that would be 99.9 percent correct -- which is a mirror that is silently wrong.

README and CLAUDE are edited in place instead (their changes are mid-file insertions, not
appends) and are checked by verify_docs.py with refreshed EXPECT, exactly like these two.

Guards, in order, per document:
  * the marker line naming this document's own image length, hash and payload size must be in
    the transcript;
  * exactly one DISTINCT payload of that exact size may be found;
  * the decoded payload must contain a sentinel that only this payload contains;
  * the disk must still be the pre-edit length, and must not already carry the sentinel;
  * the finished file must reproduce the module-reported length AND hash, or nothing is written.

The pre-edit lengths are the EXPECT figures verify_docs.py already held, and that agreement is
the point: it says the disk was in sync before this phase, so the append is the only difference.

Usage:
    python _mirror35.py --dry     # decode and verify, write nothing
    python _mirror35.py           # apply
"""
import glob
import io
import os
import sys

DIR = r"C:\Users\andypeng1NB\.claude\projects\D--rblxTRGproject"
ROOT = r"D:\rblxTRGproject"
HEXDIGITS = "0123456789abcdef"

# name, marker the module's read-back printed, image length, image hash, payload bytes,
# expected disk length before the append, a string only this payload contains.
DOCS = [
    ("PROGRESS", "PROGRESS LEN=116280 HASH=1d12dc1f DELTA=3435",
     116280, "1d12dc1f", 3435, 112845, b"## Phase 35 - The core states its own condition"),
    ("DECISIONS", "DECISIONS LEN=174533 HASH=60f44acf DELTA=2698",
     174533, "60f44acf", 2698, 171835, b"101. AN EDIT THAT ANCHORS"),
]


def newest_transcript():
    """The session file being written right now -- picked by mtime, same as extract_shot.py."""
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


def scan_hex(transcript, want_bytes):
    """Every hex run of exactly want_bytes*2 characters that follows an `HEX ` marker.

    Keyed on size rather than on line position because the payload is the one thing here whose
    length is known independently of everything else.
    """
    want = want_bytes * 2
    hits = []
    with io.open(transcript, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            i = line.find("HEX ")
            while i >= 0:
                k = i + 4
                while k < len(line) and line[k] in HEXDIGITS:
                    k += 1
                hx = line[i + 4:k]
                if len(hx) == want:
                    hits.append(hx)
                i = line.find("HEX ", k)
    return hits


def main():
    dry = "--dry" in sys.argv

    trans = newest_transcript()
    print("transcript: %s" % os.path.basename(trans))
    with io.open(trans, "r", encoding="utf-8", errors="replace") as f:
        whole = f.read()

    print()
    plan = []
    for name, marker, want_len, want_hash, delta_len, base_len, sentinel in DOCS:
        print("%-9s marker in transcript: %s" % (name, "yes" if marker in whole else "NO"))
        if marker not in whole:
            print("  *** the module-reported marker is absent -- this is not the run that "
                  "produced these payloads, ABORT ***")
            return 1

        hits = scan_hex(trans, delta_len)
        uniq = []
        for hx in hits:
            if hx not in uniq:
                uniq.append(hx)
        print("  payloads of %d bytes: %d, distinct: %d" % (delta_len, len(hits), len(uniq)))
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
        if delta[0:1] != b"\n":
            print("  *** payload does not begin on a fresh line -- ABORT ***")
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
        got_len, got_hash = len(out), roll(out)
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
        print("dry run: both documents verified, nothing written")
        return 0

    for name, path, raw, out, delta_len in plan:
        io.open(path + ".bak35", "wb").write(raw)
        io.open(path, "wb").write(out)
        print("wrote %s  %d -> %d (delta %+d, backup %s.bak35)"
              % (path, len(raw), len(out), len(out) - len(raw), name))
    return 0


sys.exit(main())
