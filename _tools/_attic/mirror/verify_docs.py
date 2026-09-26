# -*- coding: utf-8 -*-
"""Check the disk mirrors against the hashes read back out of the Studio modules.

THE RULE (DECISIONS 96), measured rather than assumed: the disk file is the ModuleScript
Source's string body with the newlines stripped from both ends and exactly one put back.

    local function diskImage(src)
      local _, b = string.find(src, "[==[", 1, true)
      local e = string.find(src, "]==]", #src - 12, true)
      local body = string.sub(src, b + 1, e - 1)
      local txt = string.gsub(body, "^\n+", "")
      txt = string.gsub(txt, "\n+$", "")
      return txt .. "\n"
    end

EXPECT IS MODULE-DERIVED, NOT DISK-DERIVED. That distinction is the whole point of this file.
An earlier version carried hashes read off the disk, so it compared the disk against itself and
passed while both sides were wrong -- the blind spot DECISIONS 89 records. The values below come
from the modules. To refresh them, run this in the Studio command bar (Edit data model) and
paste the output:

    local GS = game.ServerScriptService.GameCore
    local function roll(s) local h=0
      for i=1,#s do h=(h*31+string.byte(s,i))%2147483648 end
      return string.format("%08x",h) end
    for _,n in ipairs({"CLAUDE","PROGRESS","DECISIONS","README"}) do
      local src = GS:FindFirstChild(n).Source
      local _, b = string.find(src, "[==[", 1, true)
      local e = string.find(src, "]==]", #src - 12, true)
      local body = string.sub(src, b + 1, e - 1)
      local txt = string.gsub(body, "^\n+", "")
      txt = string.gsub(txt, "\n+$", "")
      local img = txt .. "\n"
      print(string.format("%s %d %s", n, #img, roll(img)))
    end

CLAUDE IS NOW FOUR FILES (2026-09-23). The module image is recovered by taking every '## N.'
block out of all four disk files, sorting them by N, and stitching them back together -- the
section number IS the module order, which is what makes the merge well-defined without any
marker lines polluting the body. Length and hash are then compared against the module's own
numbers, same as the other three docs. Nothing is loosened: a per-file comparison would miss
the case of two files edited in compensating ways, and this cannot.

Disk-only content, stripped before hashing (lengths asserted so a silent edit cannot slip past):
  * CLAUDE.md's '## 0.0 ' block -- section 0.0 lives only on disk, and says so itself.
  * the preamble at the top of each docs/*.md -- an H1 title plus provenance, same deal.
Note what is NOT stripped: the 327 bytes of title and handover blurb before '## 0.0 ' in
CLAUDE.md. That IS module content. An early version of the splitter dropped it and still passed
its own losslessness check, because that check compared two sides that had each lost the same
bytes -- the tautology this file exists to prevent, wearing a different hat.

Written to disk rather than piped through a shell heredoc on purpose: the shell layer eats
backslash escapes, which turned a one-line inline check into a SyntaxError twice now.
"""
import io
import os
import re
import sys

D = r"D:\rblxTRGproject"

# (length, hash) as reported by the ModuleScripts themselves -- see the docstring for how to
# re-read them. Lengths are included because a substitution can preserve the hash's absence
# only by changing the length, and vice versa; two independent numbers cannot both be wrong.
EXPECT = {
    "PROGRESS":    (158059, "6f178d29"),
    "DECISIONS":   (103355, "2e994db6"),
    "DECISIONS_2": (115574, "0e2ab947"),
    "CLAUDE":      (70268, "5b9489f9"),
    "README":      (43911, "36bf7b8b"),
}

# DECISIONS IS TWO MODULES NOW (2026-09-23). ModuleScript.Source is capped at 200000 bytes by the
# engine, and the record passed it -- the write was REFUSED, not truncated. Unlike the CLAUDE split,
# which is one module spread over four disk files, this is two modules with two disk files, so each
# file is compared against its own module AND the seam between them is asserted: part 1 must end at
# entry 74 and part 2 must begin at 75 and run contiguously. That is what makes the boundary a fact
# about the document rather than a byte offset someone typed. See DECISIONS 123.
DECISIONS_SPLIT = 75

# The four disk files that together mirror the CLAUDE module, in reading order.
CLAUDE_PARTS = ("CLAUDE.md", "docs/SYSTEMS.md", "docs/TODO.md", "docs/SNIPPETS.md")

# Disk-only blocks, per file. Lengths are asserted, not tolerances.
SEC00_LEN = 6071
PREAMBLE_LEN = {"docs/SYSTEMS.md": 501, "docs/TODO.md": 525, "docs/SNIPPETS.md": 513}

SEC = re.compile(rb"(?m)^## (\d+)\.\s")
HEAD = re.compile(rb"(?m)^## ")


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def claude_pieces(raw):
    """(prefix, rest, note) for CLAUDE.md; drops ONLY the '## 0.0 ' block."""
    i = raw.find(b"## 0.0 ")
    j = raw.find(b"\n## 0. ", i) if i >= 0 else -1
    if i < 0 or j < 0:
        return None, None, "*** section 0.0 headings not found ***"
    block = j + 1 - i
    if block != SEC00_LEN:
        return None, None, "*** section 0.0 is %d bytes, expected %d ***" % (block, SEC00_LEN)
    return raw[:i], raw[j + 1:], "section 0.0 (%d bytes) stripped" % block


def satellite_body(raw, rel):
    """(rest, note) for a docs/*.md part; drops the disk-only preamble."""
    m = HEAD.search(raw)
    if not m:
        return None, "*** no '## ' heading ***"
    pre = m.start()
    want = PREAMBLE_LEN[rel]
    if pre != want:
        return None, "*** preamble is %d bytes, expected %d ***" % (pre, want)
    return raw[m.start():], "preamble (%d bytes) stripped" % pre


def split_blocks(raw):
    """(head, [(n, block)]). Any text before the first '## N.' heading is returned as head."""
    ms = list(SEC.finditer(raw))
    if not ms:
        return raw, []
    head = raw[:ms[0].start()]
    out = []
    for k, m in enumerate(ms):
        a = m.start()
        b = ms[k + 1].start() if k + 1 < len(ms) else len(raw)
        out.append((int(m.group(1)), raw[a:b]))
    return head, out


def assemble_claude():
    """Rebuild the CLAUDE module image from its four disk files. Returns (body, notes) or
    (None, [error])."""
    prefix = b""
    sections = []
    notes = []
    for rel in CLAUDE_PARTS:
        path = os.path.join(D, rel.replace("/", os.sep))
        if not os.path.exists(path):
            return None, ["*** %s is missing ***" % rel]
        raw = io.open(path, "rb").read()
        if rel == "CLAUDE.md":
            prefix, rest, note = claude_pieces(raw)
            if prefix is None:
                return None, [note]
        else:
            rest, note = satellite_body(raw, rel)
            if rest is None:
                return None, ["*** %s: %s ***" % (rel, note)]
        head, blks = split_blocks(rest)
        if head:
            return None, ["*** %s: %d bytes before the first section ***" % (rel, len(head))]
        sections += blks
        notes.append("%s: %s + %d sections" % (rel, note, len(blks)))

    nums = sorted(n for n, _ in sections)
    if nums != list(range(9)):
        missing = [n for n in range(9) if n not in nums]
        dupes = sorted({n for n in nums if nums.count(n) > 1})
        return None, ["*** CLAUDE sections are not 0..8 once each (missing %s, duplicated %s) ***"
                      % (missing, dupes)]
    return prefix + b"".join(t for _, t in sorted(sections, key=lambda kv: kv[0])), notes


def decisions_seam(part1, part2):
    """(note, ok) for the DECISIONS/DECISIONS_2 boundary. The entry number IS the order."""
    tail = [int(n) for n in re.findall(rb"(?m)^(\d+)\. ", part1)]
    head = [int(n) for n in re.findall(rb"(?m)^(\d+)\. ", part2)]
    if not tail or not head:
        return "*** a part has no numbered entries ***", False
    if tail[0] != 1 or tail[-1] != DECISIONS_SPLIT - 1:
        return ("*** part 1 holds entries %d..%d, expected 1..%d ***"
                % (tail[0], tail[-1], DECISIONS_SPLIT - 1)), False
    if tail != list(range(1, tail[-1] + 1)):
        return "*** part 1's entries are not contiguous ***", False
    if head[0] != DECISIONS_SPLIT or head != list(range(DECISIONS_SPLIT, head[-1] + 1)):
        return "*** part 2 starts at %d, expected %d, or is not contiguous ***" % (
            head[0], DECISIONS_SPLIT), False
    return ("seam: part 1 ends at %d, part 2 runs %d..%d, contiguous"
            % (tail[-1], head[0], head[-1])), True


if __name__ == "__main__":
    ok = True
    for name in ("PROGRESS", "DECISIONS", "DECISIONS_2", "CLAUDE", "README"):
        want_len, want_hash = EXPECT[name]
        if name == "CLAUDE":
            body, notes = assemble_claude()
            if body is None:
                for n in notes:
                    print("%-10s %s" % (name, n))
                ok = False
                continue
            label = " (= %d disk files)" % len(CLAUDE_PARTS)
        else:
            body = io.open(os.path.join(D, name + ".md"), "rb").read()
            notes = []
            label = ""
        if body is None:
            ok = False
            continue
        h = roll(body)
        good = len(body) == want_len and h == want_hash
        ok = ok and good
        print("%-10s body=%-8d hash=%s  %s%s"
              % (name, len(body), h,
                 "MATCH" if good else "*** MISMATCH, module says %d/%s ***" % (want_len, want_hash),
                 label))
        for n in notes:
            print("%-10s   %s" % ("", n))

    seam_note, seam_ok = decisions_seam(
        io.open(os.path.join(D, "DECISIONS.md"), "rb").read(),
        io.open(os.path.join(D, "DECISIONS_2.md"), "rb").read())
    ok = ok and seam_ok
    print("%-10s %s" % ("", ("    " + seam_note) if seam_ok else seam_note))

    print("ALL DOCUMENTS MATCH THE MODULES" if ok else "*** MISMATCH ***")
    sys.exit(0 if ok else 1)
