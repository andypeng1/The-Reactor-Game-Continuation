# -*- coding: utf-8 -*-
"""Apply the Phase-36 doc mirror, in the _mirror35.py shape.

Two kinds of change this round, and they need different carriers:

  * PROGRESS and DECISIONS were APPENDED to, so the payload is a contiguous tail. The modules
    emitted that tail as hex (DECISIONS 96: the disk mirror is derived from the artefact, never
    fitted to it), and it is recorded verbatim in the session transcript. Scraping it out is the
    only way to move 4 KB without a 99.9-percent-correct retyping, which is a mirror that is
    silently wrong.
  * README and CLAUDE were edited IN PLACE -- mid-file insertions, not appends -- so there is no
    tail to append. Their edits are also in the transcript, as the multi_edit tool inputs, and
    are replayed here.

Both carriers end at the same gate: the finished file must reproduce the length AND hash the
ModuleScript reported for its own disk image. Length alone is not enough -- PROGRESS and
DECISIONS have each previously differed by exactly one character at equal length.

Guards, in order, per document:
  * the module-reported marker for this document must be in the transcript;
  * appends: exactly one DISTINCT hex payload of the exact byte size, beginning on a fresh line,
    containing a sentinel only this payload contains;
  * in-place: the LAST multi_edit recorded for that module must be the set replayed, every anchor
    must occur exactly once, and a sentinel must land in the result;
  * in both cases the disk must still be the pre-edit length;
  * and the finished file must reproduce the module-reported length AND hash, or nothing is
    written. Any disagreement aborts with the file untouched.

The pre-edit lengths are the EXPECT figures verify_docs.py already held, and that agreement is
the point: it says the disk was in sync before this phase, so this phase is the only difference.

Usage:
    python _mirror36.py --dry     # decode and verify, write nothing
    python _mirror36.py           # apply
"""
import glob
import io
import json
import os
import sys

DIR = r"C:\Users\andypeng1NB\.claude\projects\D--rblxTRGproject"
ROOT = r"D:\rblxTRGproject"
HEXDIGITS = "0123456789abcdef"

# name, marker the module's read-back printed, image length, image hash, bytes appended,
# expected disk length before the append, a string only this payload contains.
APPENDS = [
    ("PROGRESS", "PROGRESS LEN=120392 HASH=75085461 DELTA=4112",
     120392, "75085461", 4112, 116280, b"## Phase 36 - The monitors get their content"),
    ("DECISIONS", "DECISIONS LEN=177159 HASH=08b72446 DELTA=2626",
     177159, "08b72446", 2626, 174533, b"104. A TITLE BAR SPANS THE FRAME"),
]

# name, image length, image hash, pre-edit image length, pre-edit image hash, module path
# suffix, a string that must be present only after the edits land.
#
# The comparison is on the IMAGE, not on the file. CLAUDE.md is 2524 bytes longer than its
# module's image because section 0.0 lives only on disk, so its file length is never the number
# the module reports -- reading 63678 against an expected 61154 is the guard doing its job on a
# unit mismatch, not a real drift. Both sides are therefore reduced to an image first, by the
# same heading-based strip verify_docs.py uses.
IN_PLACE = [
    ("README", 35125, "4975dff8", 33958, "5f08bf63", ".README", b"## Rebuild kits"),
    ("CLAUDE", 62580, "2b6be228", 61154, "7ea24694", ".CLAUDE", b"GameCoreTitleBar"),
]

# The one section that exists only on disk, found by heading and asserted by size -- see
# verify_docs.py, which owns this rule. (start, next_heading, expected block length)
DISK_ONLY = {
    "CLAUDE": (b"## 0.0 ", b"\n## 0. ", 2524),
}


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


def lines(transcript):
    with io.open(transcript, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line


def scan_hex(transcript, want_bytes):
    """Every hex run of exactly want_bytes*2 characters that follows an `HEX ` marker.

    Keyed on size rather than on line position because the payload is the one thing here whose
    length is known independently of everything else.
    """
    want = want_bytes * 2
    hits = []
    for line in lines(transcript):
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


def collect_edits(node, found):
    """Every multi_edit tool input in the transcript, in order, as (file_path, edits)."""
    if isinstance(node, dict):
        if isinstance(node.get("input"), dict) and isinstance(node.get("name"), str):
            if "multi_edit" in node["name"] and "file_path" in node["input"]:
                found.append((node["input"]["file_path"], node["input"].get("edits") or []))
        for v in node.values():
            collect_edits(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_edits(v, found)


def replay(raw, edits):
    """Apply the edits in order. Every anchor must occur exactly once, or this is not the run."""
    for e in edits:
        if e.get("replace_all"):
            return None, "replace_all not handled"
        old = (e.get("old_string") or "").encode("utf-8")
        new = (e.get("new_string") or "").encode("utf-8")
        n = raw.count(old)
        if n != 1:
            return None, "anchor occurs %d times: %r" % (n, old[:70])
        raw = raw.replace(old, new, 1)
    return raw, ""


def to_image(name, raw):
    """Reduce a disk file to the module's image. Returns (body, note)."""
    if name not in DISK_ONLY:
        return raw, ""
    start, nxt, want = DISK_ONLY[name]
    i = raw.find(start)
    j = raw.find(nxt, i)
    if i < 0 or j < 0:
        return None, "section 0.0 headings not found"
    block = j + 1 - i
    if block != want:
        return None, "section 0.0 is %d bytes, expected %d" % (block, want)
    return raw[:i] + raw[j + 1:], "section 0.0 (%d bytes) stripped" % block


def main():
    dry = "--dry" in sys.argv

    trans = newest_transcript()
    print("transcript: %s" % os.path.basename(trans))
    whole = io.open(trans, "r", encoding="utf-8", errors="replace").read()

    edits_by_path = []
    for line in lines(trans):
        if "multi_edit" not in line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        found = []
        collect_edits(obj, found)
        edits_by_path.extend(found)

    print("multi_edit inputs in transcript: %d" % len(edits_by_path))
    for path, edits in edits_by_path:
        print("  %-52s %d edit(s)" % (path, len(edits)))
    print()

    plan = []
    for name, marker, want_len, want_hash, delta_len, base_len, sentinel in APPENDS:
        print("%-9s marker in transcript: %s" % (name, "yes" if marker in whole else "NO"))
        if marker not in whole:
            print("  *** the module-reported marker is absent -- this is not the run that "
                  "produced these payloads, ABORT ***")
            return 1

        uniq = []
        for hx in scan_hex(trans, delta_len):
            if hx not in uniq:
                uniq.append(hx)
        print("  payloads of %d bytes: %d distinct" % (delta_len, len(uniq)))
        if len(uniq) != 1:
            print("  *** expected exactly one distinct payload -- cannot choose, ABORT ***")
            return 1

        delta = bytes.fromhex(uniq[0])
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
        plan.append((name, path, raw, out))
        print()

    for name, want_len, want_hash, base_len, base_hash, suffix, sentinel in IN_PLACE:
        cands = [(p, e) for p, e in edits_by_path if p.endswith(suffix) and e]
        print("%-9s multi_edit inputs for %s: %d" % (name, suffix, len(cands)))
        if not cands:
            print("  *** no multi_edit found for this module -- ABORT ***")
            return 1

        path = os.path.join(ROOT, name + ".md")
        raw = io.open(path, "rb").read()
        body, note = to_image(name, raw)
        if body is None:
            print("  *** %s -- ABORT ***" % note)
            return 1
        print("  disk %-14s %d bytes  image %d bytes  hash=%s%s"
              % (name + ".md", len(raw), len(body), roll(body),
                 ("  [" + note + "]") if note else ""))
        if len(body) != base_len or roll(body) != base_hash:
            print("  *** disk image is %d/%s, expected the pre-edit %d/%s -- ABORT, untouched ***"
                  % (len(body), roll(body), base_len, base_hash))
            return 1
        if sentinel in raw:
            print("  *** edits already applied -- ABORT (idempotent) ***")
            return 1

        # The LAST set that reproduces the module's current image is the one replayed. Trying
        # candidates in reverse keeps this a check rather than a search, and the hash gate is
        # what makes picking wrong harmless rather than silent.
        tried = []
        out = None
        for p, edits in reversed(cands):
            key = json.dumps(edits, sort_keys=True)
            if key in tried:
                continue
            tried.append(key)
            res, why = replay(raw, edits)
            if res is None:
                print("  candidate (%d edits): rejected -- %s" % (len(edits), why))
                continue
            img, why = to_image(name, res)
            good = img is not None and len(img) == want_len and roll(img) == want_hash
            print("  candidate (%d edits): image len=%d hash=%s  %s"
                  % (len(edits), len(img) if img is not None else -1,
                     roll(img) if img is not None else "-", "MATCH" if good else "no"))
            if good:
                out = res
                break
        if out is None:
            print("  *** no candidate reproduced len=%d hash=%s -- ABORT, file untouched ***"
                  % (want_len, want_hash))
            return 1
        if sentinel not in out:
            print("  *** sentinel %r absent from the result -- ABORT ***" % sentinel)
            return 1
        plan.append((name, path, raw, out))
        print("  -> MATCH, %d -> %d" % (len(raw), len(out)))
        print()

    if dry:
        print("dry run: %d document(s) verified, nothing written" % len(plan))
        return 0

    for name, path, raw, out in plan:
        io.open(path + ".bak36", "wb").write(raw)
        io.open(path, "wb").write(out)
        print("wrote %s  %d -> %d (delta %+d, backup %s.bak36)"
              % (path, len(raw), len(out), len(out) - len(raw), name))
    return 0


sys.exit(main())
