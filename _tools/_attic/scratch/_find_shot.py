# -*- coding: utf-8 -*-
"""Find where inline image payloads land on disk, so a text-only model can hand them to vision.

The screenshot tools return their PNG inline. A text-only model cannot see that, and the file is
never written anywhere -- which is the gap CLAUDE.md 3.4 records. But an inline tool result is
recorded verbatim in the session transcript, so the bytes DO reach disk; they are just wrapped in
base64 inside a JSONL line. This probes for them.

Nothing from the transcript is printed -- only shapes: media type and payload size per hit. The
transcript is a very large JSONL and has no business in a context window.
"""
import io
import json
import os
import sys

P = r"C:\Users\andypeng1NB\.claude\projects\D--rblxTRGproject\9e0bb201-b90b-4e0a-aa3f-804f2142b485.jsonl"


def walk(node, path, out):
    """Collect every {"type":"image","source":{...}} node, wherever it is nested."""
    if isinstance(node, dict):
        if node.get("type") == "image":
            src = node.get("source")
            if isinstance(src, dict):
                out.append((path, src.get("media_type"), src.get("type"), len(src.get("data") or "")))
        for k, v in node.items():
            walk(v, path + "." + k if path else k, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, "%s[%d]" % (path, i), out)


hits = []
with io.open(P, "r", encoding="utf-8", errors="replace") as f:
    for ln, line in enumerate(f, 1):
        if "image" not in line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        out = []
        walk(obj, "", out)
        if out:
            hits.append((ln, out))

print("transcript: %d bytes" % os.path.getsize(P))
print("lines carrying image payloads: %d" % len(hits))
for ln, out in hits[-12:]:
    for path, mt, enc, n in out:
        print("  line %-7d %-28s %s/%s base64=%d chars (~%d bytes raw)"
              % (ln, path[:28], mt, enc, n, n * 3 // 4))
if not hits:
    print("  (none -- inline images are not persisted here)")
sys.exit(0)
