# -*- coding: utf-8 -*-
"""Make the two just-written entries size-agnostic, because improving section 0.0 outdated them.

DECISIONS 96 and the PROGRESS note both froze "1326 bytes" / "offsets 327..1652". That was true
when written and stopped being true the moment section 0.0 -- which lives only on disk and is
meant to be improved -- grew. A number a future edit is guaranteed to invalidate is a liability,
so both now state the relation instead of the figure, and the verifier asserts the block length.

This is a substitution, not an append: the changed text sits inside the region appended a moment
ago, so the disk cannot just be extended. The old strings must occur exactly once each; the
finished file must then match the module's own report, which is the only thing that decides
whether the two authorings (this one and the Studio edit) agreed.
"""
import io
import sys

DOCS = [
    {
        "name": "PROGRESS",
        "path": r"D:\rblxTRGproject\PROGRESS.md",
        "base_len": 108275, "base_hash": "4b98fdc9",
        "want_len": 108391, "want_hash": "0b1a94af",
        "pairs": [
            ("disk hash. CLAUDE.md stays 1326 bytes longer\n",
             "disk hash. CLAUDE.md stays longer\n"),
            ("than its module on purpose -- section 0.0 exists only on disk, and dropping offsets\n"
             "  327..1652 inclusive reproduces the module hash exactly. See DECISIONS 96.\n",
             "than its module on purpose -- section 0.0 exists only on disk, and dropping the whole\n"
             "  block, heading to heading, reproduces the module hash exactly. The size is not written\n"
             "  down: section 0.0 is editable on disk, so a frozen figure rots the next time it improves.\n"
             "  See DECISIONS 96.\n"),
        ],
    },
    {
        "name": "DECISIONS",
        "path": r"D:\rblxTRGproject\DECISIONS.md",
        "base_len": 167916, "base_hash": "2c9df975",
        "want_len": 168221, "want_hash": "6fed1dae",
        "pairs": [
            ("    THE ONE PLACE THE DISK IS NOT A MIRROR. CLAUDE.md is 60757 bytes, 1326 more than the\n"
             "    module's 59431, because section 0.0 exists only on disk -- the section that says so\n"
             "    itself. Dropping offsets 327..1652 inclusive reproduces 0bc66b87 exactly. Any check has\n"
             "    to know this, and no other doc has a disk-only section.\n",
             "    THE ONE PLACE THE DISK IS NOT A MIRROR. CLAUDE.md is longer than its module's 59431\n"
             "    bytes, because section 0.0 exists only on disk -- the section that says so itself.\n"
             "    Dropping that whole block, heading to heading, reproduces 0bc66b87 exactly, and no other\n"
             "    doc has a disk-only section. The excess is deliberately not written down here: section\n"
             "    0.0 is editable on disk, so a figure frozen into this entry starts rotting the next time\n"
             "    somebody improves it. The check finds the block by its headings and asserts its length,\n"
             "    which catches a silent edit either way -- the assertion is the point, not the number.\n"),
        ],
    },
]


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


fail = 0
for d in DOCS:
    raw = io.open(d["path"], "rb").read()
    print("=== %s ===" % d["name"])
    print("  baseline %d %s" % (len(raw), roll(raw)))
    if len(raw) != d["base_len"] or roll(raw) != d["base_hash"]:
        print("  *** disk is not where the previous mirror left it -- ABORT ***")
        fail = 1
        continue
    out = raw
    bad = False
    for i, (old, new) in enumerate(d["pairs"], 1):
        n = out.count(old.encode("utf-8"))
        print("  pair %d: old occurs %d time(s), %d -> %d bytes"
              % (i, n, len(old.encode("utf-8")), len(new.encode("utf-8"))))
        if n != 1:
            print("  *** pair %d is not unique -- ABORT ***" % i)
            bad = True
            continue
        out = out.replace(old.encode("utf-8"), new.encode("utf-8"))
    if bad:
        fail = 1
        continue
    ok = len(out) == d["want_len"] and roll(out) == d["want_hash"]
    print("  candidate %d %s   (module says %d %s)  %s"
          % (len(out), roll(out), d["want_len"], d["want_hash"], "PASS" if ok else "*** FAIL ***"))
    if not ok:
        print("  the two authorings disagree -- nothing written")
        fail = 1
        continue
    io.open(d["path"] + ".baknum33", "wb").write(raw)
    io.open(d["path"], "wb").write(out)
    print("  written: %d -> %d (%+d)" % (len(raw), len(out), len(out) - len(raw)))

print()
print("NUMBERS MADE SIZE-AGNOSTIC: " + ("PASS" if not fail else "*** FAIL ***"))
sys.exit(fail)
