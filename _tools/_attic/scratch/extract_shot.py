# -*- coding: utf-8 -*-
"""Pull an inline image out of the session transcript and write it as a real file.

Why this exists: the Studio screenshot tools return their PNG inline, which a text-only model
cannot see, and they never write it anywhere -- the gap CLAUDE.md 3.4 records. The bytes do reach
disk though: an inline tool result is recorded verbatim in the session JSONL as base64. So the fix
is a decode, not a new capture path.

Usage:
    python extract_shot.py                # latest PNG in the transcript
    python extract_shot.py --line 5168    # the image on that transcript line
    python extract_shot.py --list         # just show what is in there, write nothing

Output goes to .ai/inbox/ so the vision sidecar can read it by path. The transcript is 46 MB of
JSONL and is never printed -- only per-image shapes.
"""
import base64
import io
import json
import os
import sys

DIR = r"C:\Users\andypeng1NB\.claude\projects\D--rblxTRGproject"
OUTDIR = r"D:\rblxTRGproject\.ai\inbox"


def newest_transcript():
    """The session file this harness is writing to right now.

    A long conversation gets compacted and resumed in place, so the transcript can keep the same
    name -- but a brand new session gets a new one. Hardcoding a name therefore goes stale exactly
    when a fresh session is the case where you most need it, so pick by mtime and keep a fallback.
    """
    import glob
    cands = glob.glob(os.path.join(DIR, "*.jsonl"))
    if not cands:
        return os.path.join(DIR, "9e0bb201-b90b-4e0a-aa3f-804f2142b485.jsonl")
    return max(cands, key=os.path.getmtime)


P = newest_transcript()
if os.path.isfile(P):
    print("transcript: %s" % os.path.basename(P))

MAGIC = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpeg", b"GIF8": "gif"}


def walk(node, path, out):
    if isinstance(node, dict):
        if node.get("type") == "image":
            src = node.get("source")
            if isinstance(src, dict) and src.get("data"):
                out.append((path, src.get("media_type"), src["data"]))
        for k, v in node.items():
            walk(v, path + "." + k if path else k, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, "%s[%d]" % (path, i), out)


def sniff(raw):
    for m, name in MAGIC.items():
        if raw.startswith(m):
            return name
    return "??"


found = []                      # (line, path, media_type, base64 str)
with io.open(P, "r", encoding="utf-8", errors="replace") as f:
    for ln, line in enumerate(f, 1):
        if '"image"' not in line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        out = []
        walk(obj, "", out)
        # the payload appears twice per line (message content and toolUseResult); keep one
        seen = set()
        for path, mt, data in out:
            if data in seen:
                continue
            seen.add(data)
            found.append((ln, path, mt, data))

mode = sys.argv[1] if len(sys.argv) > 1 else ""
arg = sys.argv[2] if len(sys.argv) > 2 else ""

print("images in transcript: %d" % len(found))
for ln, path, mt, data in found:
    raw = base64.b64decode(data)
    print("  line %-7d %-10s %8d bytes  %-4s  %s"
          % (ln, (mt or "?").split("/")[-1], len(raw), sniff(raw), path[:40]))

if mode == "--list":
    sys.exit(0)

pick = None
if mode == "--line":
    for rec in found:
        if str(rec[0]) == arg:
            pick = rec
else:
    for rec in reversed(found):
        if (rec[2] or "").endswith("png"):
            pick = rec
            break
    if pick is None and found:
        pick = found[-1]

if pick is None:
    print("nothing to write")
    sys.exit(1)

ln, path, mt, data = pick
raw = base64.b64decode(data)
ext = sniff(raw)
if ext == "??":
    print("*** decoded bytes are not a known image format -- ABORT ***")
    sys.exit(1)

if not os.path.isdir(OUTDIR):
    os.makedirs(OUTDIR)
name = "shot_line%d.%s" % (ln, ext)
dest = os.path.join(OUTDIR, name)
io.open(dest, "wb").write(raw)
print()
print("wrote %s  (%d bytes, %s, from line %d)" % (dest, len(raw), ext, ln))
