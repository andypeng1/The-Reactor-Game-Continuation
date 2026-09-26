# -*- coding: utf-8 -*-
"""Mirror the Phase 43 documentation additions onto the disk .md files.

WHY THIS FILE EXISTS. Section 0.0 requires that any change carry its documentation in the same
step, and that the game-side ModuleScripts stay the source of truth with the disk .md as a
mirror. The Phase 43 text was written into three ModuleScripts (PROGRESS, DECISIONS_2, README)
and now has to reach three disk files.

THE MIRROR RULE (DECISIONS 96), unchanged: the disk file is the module Source's string body with
the newlines stripped from both ends and exactly one put back. So a block appended to a module
body lands on disk as

    new_file = old_file + "\n" + BLOCK + "\n"

and nothing else about the file moves.

WHY THE HASH GATE. The blocks below are transcribed, and a transcription can differ from what
went into the module by a character without looking any different. The module reported its own
(len, hash) after the edit; this script computes the same pair for the file it is ABOUT to write
and refuses to write unless they agree. That is DECISIONS 96's rule applied in the direction that
catches a typo: the expectation comes from the module, never from disk. A comparison against a
number read off the disk would pass while both sides were wrong, which is DECISIONS 95.

Written to disk rather than piped through a shell heredoc on purpose: the shell layer eats
backslash escapes. These blocks contain no backslashes, but the instrument is the point.
"""
import hashlib
import io
import os
import sys

D = r"D:\rblxTRGproject"

# (path, module-reported image length, module-reported roll hash) -- read back out of Studio
# after the edits, by the snippet in verify_docs.py's docstring.
TARGETS = {
    "PROGRESS.md": (153546, "6034e896"),
    "DECISIONS_2.md": (112010, "25e3730f"),
    "README.md": (42546, "6a280f80"),
}

PROGRESS_BLOCK = u"""## Phase 43 - The facility is one skin again  [DONE]

Scope: appearance only. `PaletteKit` (new module, Rebuild) writes Color, Material and MaterialVariant
and nothing else. No part is created, renamed, moved or destroyed, so nothing in the CLAUDE 6 binding
table can be affected, and no gameplay mechanic changed.

WHAT WAS WRONG. Workspace held 129,578 BaseParts in 20 Material/Variant combos, and the two largest
differed in BASE MATERIAL at nearly equal size: Metal/FacilitySteelPanel 49,316 (38.1%) and
CorrodedMetal/ReactorWallPlate 47,167 (36.4%). Two skins over one ladder of tones. The Mk2 desks were
then built on a third skin (SmoothPlastic, body 50,50,50), so the rebuilt area matched neither half it
stood between. That is the operator's "the front and the back look different".

WHY THE MATERIAL IS THE WHOLE STORY, MEASURED RATHER THAN INFERRED. All three project
MaterialVariants carry NO ColorMap:

    FacilitySteelPanel   base=Metal          colorMap=(none)  studs=10
    ReactorWallPlate     base=CorrodedMetal  colorMap=(none)  studs=10
    FacilityFloorPlate   base=DiamondPlate   colorMap=(none)  studs=10

A variant with no ColorMap is a rename of its base material. What the player sees is therefore the
STOCK texture multiplied by the part Color, and nothing was overriding the rust.

WHAT WAS WRITTEN. 53,029 parts: 47,166 rust parts retired onto FacilitySteelPanel, plus 5,863
near-grey structural parts above luminance 120 pulled down to 100,100,100 - ShellKit's own threshold
and target, so the two kits agree by construction. Three classes were exempt, each measured rather
than assumed: lamps (1), content (5,218 - TextPart/FloorTextPart/Line at lum 248, plus anything
carrying a Decal or a Texture) and hue (10,103 - brass 194,150,68, hazard yellow 190,149,0, coolant
blue 110,153,202, violet 134,102,202 and the rest, which is the facility's coding). Floors keep
FacilityFloorPlate.

REVERSIBLE BY RECEIPT. Color, Material and MaterialVariant go into attribute PaletteKitOrigin before
the first write, so RestoreAll() is exact; 53,029 receipts were recorded during the run.
RestretchChunk exists because a single non-yielding pass over 96,483 parts freezes Studio - it slices
the work and is resumable without a cursor, because a part that already matches the palette falls out
of the pending set by itself.

THE FIRST APPLIED RESULT HAD A DEFECT, AND THE RENDER FOUND IT. The first rules retired rust even
under artwork, on a written claim that "a Decal is unaffected by the material underneath it". A
same-camera capture of the coolant deck showed CoolantReserviors.C1.Union - 178 by 1 by 80, carrying
a Texture - go from dark olive to BRIGHT YELLOW. A Texture tiles with transparency and composites
WITH the base material, so the skin shows through it. The claim was false, and RestoreFaced() put
back exactly the parts carrying authored artwork: 1,555 of them.

WHY 1,555 AND NOT 1,307. A child-count census had predicted 1,307 (858 with a Texture plus 449 with a
Decal). RestoreFaced selects with the SAME isContent() predicate the rule calls, and that predicate
also matches by NAME - 248 structural parts are named TextPart or Line. Using the rule's own
predicate is what makes the number trustworthy; a second hand-rolled test would have been a second
thing to be wrong. See DECISIONS 126.

VERIFIED BY READING INSTANCES, NOT THE RETURN VALUE. Census after: Metal/FacilitySteelPanel 96,482
from 49,316; ReactorWallPlate 1,556 = the 1,555 restored plus GravatronUnit.LightPart, which is a
lamp and was never touched. Receipts remaining 51,474 = 53,029 - 1,555. The exempt classes read
unchanged: TextPart still 248,248,248, Line still 163,162,165, ClickPart still 239,184,56, Neon still
7,424, Plastic plus SmoothPlastic still 12,030.

THE VISIBLE RESULT. Matched-camera captures from (180,320,80) toward the chamber walls: pale,
washed-out grey before, dark steel after - the Mk2 direction. The control-room deck, which is the
reference area and was already correct, is identical in both, which is the cross-check that the
rules did not disturb what was already right.

A PROBE THAT READ THE WRONG PART. The first verification pass reported C1.Union as DiamondPlate with
no children, contradicting the plate that had just been diagnosed. C1 has more than one child named
Union and FindFirstChild returns the first; the child count was the tell. Identity, not path - the
rule from DECISIONS 119, re-learned on a READ instead of a delete. See DECISIONS 127.

STILL OPEN. The per-unit parking of the original facility into ServerStorage is untouched by this
phase: PaletteKit changes appearance in place and moves nothing."""

DECISIONS2_BLOCK = u"""125. A MATERIAL SKIN UNDER AUTHORED ARTWORK CANNOT BE SWAPPED FREELY - AN OVERLAY COMPOSITES WITH ITS BASE.

    WHAT HAPPENED. PaletteKit's first rules retired the rust skin on every structural part,
    including the ones carrying content, on a claim written into the module header: "a Decal is
    unaffected by the material underneath it". A same-camera capture of the coolant deck showed the
    opposite. CoolantReserviors.C1.Union, a 178 by 1 by 80 plate carrying a Texture, went from dark
    olive under CorrodedMetal to bright yellow under Metal.

    WHY THE CLAIM WAS FALSE. A Decal and a Texture are not the same object with different settings. A
    Texture tiles across a face with transparency, so it composites WITH the base material and the
    skin shows through the gaps; a Decal covers more of the face. "Covers more" is not "cannot
    show", and nothing had been measured that says a Decal is immune. The reason the claim survived
    review is that it was plausible and it was written down - and a plausible claim in a header
    comment reads exactly like a measured one.

    THE DETECTION WAS THE RENDER, NOT THE SCAN. Scan() reported the touched content set as a count,
    and a count of 5,218 against 96,483 structural parts reads as a detail. It took a matched-camera
    capture of the applied result to make the defect obvious. A dry run can confirm that a rule
    fires; it cannot tell you whether firing was right.

    THE FIX IS A CONSTRAINT, NOT A PATCH. Both Decal and Texture now block Rule 1 as well as Rule 2,
    so a part carrying authored artwork is left exactly as it was found. The cost is bounded and
    known: 1,555 parts, 1.0% of the facility, traded against repainting art that PaletteKit cannot
    regenerate. See DECISIONS 126.

126. AN EXEMPTION MUST USE THE SAME PREDICATE AS THE RULE IT EXEMPTS.

    WHAT HAPPENED. Restoring the content parts touched before the exemption existed needed a
    selector. A child-count census predicted 1,307 of them - 858 carrying a Texture plus 449 carrying
    a Decal. RestoreFaced() actually restored 1,555. The 248-part difference is not drift: the census
    counted CHILDREN, while the rule's isContent() also matches by NAME, and 248 structural parts are
    named TextPart or Line without carrying a face of their own.

    WHY THIS IS THE POINT AND NOT A CURIOSITY. The census looked like a measurement of the right set
    but was taken with a different test than the one that mattered. RestoreFaced selects with
    isContent() - the same function decide() calls - so the two cannot disagree about which parts are
    content. Had the restore used the census instead, 248 parts would have kept a skin the rule had
    already been corrected to leave alone, and the inconsistency would have been invisible: both
    numbers are internally consistent, and only their difference is evidence.

    THE GENERAL FORM. When a rule gains an exemption, the exemption is part of the rule.
    Re-deriving it elsewhere guarantees two definitions of "content" that will diverge at the next
    edit.

127. A READ BY PATH IS NOT A READ BY IDENTITY.

    WHAT HAPPENED. Verifying the PaletteKit run, a probe of CoolantReserviors.C1.Union reported
    DiamondPlate/FacilityFloorPlate with no children - the opposite of the plate that had just been
    diagnosed as Metal/FacilitySteelPanel carrying a Texture. Nothing had gone wrong with the write.
    C1 has more than one child named Union, and FindFirstChild returns the first match. The child
    count was what gave it away.

    WHY THIS IS A SEPARATE ENTRY FROM 119. 119 is about DELETING by index and says identity must be
    used instead. This is the same failure on a READ, where it is more dangerous rather than less: a
    delete by the wrong identity destroys something and is usually noticed, while a read by the wrong
    identity returns a confident, well-formed answer about a different object and is believed. The
    probe here produced a contradiction that looked like a bug in the code under test.

    THE RULE. When a result is surprising, suspect the selector before the subject. Get the instance
    from a query that returns the real set, and confirm identity against a property the diagnosis
    itself recorded - here the size and the child list, not the name."""

README_BLOCK = u"""### PaletteKit - the facility skin

`ServerScriptService.GameCore.Rebuild.PaletteKit` is the facility-wide appearance pass that
follows ShellKit. ShellKit restyled the control-room shell; PaletteKit restyled everything
else. They deliberately share a threshold (luminance 120) and a target (100,100,100), so
they cannot fight over a part.

The rules: retire the ReactorWallPlate skin onto FacilitySteelPanel, and pull near-grey
structural tones above 120 down to 100,100,100. Exempt are Neon, the lamp names
(`NeonPart`/`Indicator`/`Lamp`/`Glow`/`Light`/`LightPart`), content (`TextPart`,
`FloorTextPart`, `Line`, `Text` by name, or any part carrying a Decal or a Texture) and
anything with hue. Floors keep `FacilityFloorPlate`.

`PaletteKitOrigin` holds `r,g,b|tostring of Material|MaterialVariant` on every part the kit
writes, so `RestoreAll()` is exact and `RestoreFaced()` can undo just the content subset.
`RestretchChunk(limit)` is the entry point for a live run: a single pass over 96,483 parts
freezes Studio, and the chunked form needs no cursor because a part already inside the
palette returns nil from `decide`.

Two facts this module records because they cost real time. A MaterialVariant with no
ColorMap is only a rename of its base material, so retiring a skin is a real visual change.
And artwork does not protect itself from the skin underneath it, because a Texture
composites with the base. See DECISIONS 125 to 127."""

BLOCKS = {
    "PROGRESS.md": PROGRESS_BLOCK,
    "DECISIONS_2.md": DECISIONS2_BLOCK,
    "README.md": README_BLOCK,
}


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def main():
    dry = "check" in sys.argv
    rc = 0
    for name in ("PROGRESS.md", "DECISIONS_2.md", "README.md"):
        path = os.path.join(D, name)
        raw = io.open(path, "rb").read()
        block = BLOCKS[name].encode("utf-8")
        out = raw + b"\n" + block + b"\n"
        want_len, want_hash = TARGETS[name]
        got_hash = roll(out)
        ok = len(out) == want_len and got_hash == want_hash
        print("%-16s %d -> %d  hash %s  want %d/%s  %s"
              % (name, len(raw), len(out), got_hash, want_len, want_hash,
                 "MATCH" if ok else "*** MODULE DISAGREES, NOT WRITING ***"))
        if not ok:
            rc = 1
            continue
        if not dry:
            io.open(path, "wb").write(out)
    if rc:
        print("*** at least one file does not reproduce the module image ***")
    elif dry:
        print("(dry run: nothing written)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
