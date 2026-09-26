# -*- coding: utf-8 -*-
"""Add LaserFrame to README.md: the kit registry (both lists) and its own subsection.

Same four replacements are applied to the README ModuleScript by hand with multi_edit. Each
substitution here asserts exactly one occurrence, because a silent zero-match would leave the
disk mirror one edit behind the module and the verifier would then report a hash mismatch with
no clue which edit was missing.
"""
import io

P = r"D:\rblxTRGproject\README.md"

SUBS = [
    (b"GameCore.Rebuild holds six kits.",
     b"GameCore.Rebuild holds seven kits."),
    (b"  LaserKit         the three CBL lasers, refined in place\n",
     b"  LaserKit         the three CBL lasers, refined in place\n"
     b"  LaserFrame       the rectangular frame around those lasers; additive, no hull change\n"),
    (b"  LaserKit    -- the CBL laser refinish: three machines, colour plus accents\n",
     b"  LaserKit    -- the CBL laser refinish: three machines, colour plus accents\n"
     b"  LaserFrame  -- the CBL laser frame: 125 parts per machine, ribs, rails and ducts, additive\n"),
    (b"named after a control, so `ConsoleBinder` and `ControlVisuals` never see it.\n",
     b"named after a control, so `ConsoleBinder` and `ControlVisuals` never see it.\n"
     b"\n"
     b"### LaserFrame is a frame, not a second hull\n"
     b"\n"
     b"LaserKit fixed the lasers' colour and left their shape alone, so the machines stayed long\n"
     b"round barrels beside rectangular, bevelled, brass-banded Mk2 desks. The obvious fix is\n"
     b"wrong: a new hull is a delete plus a build, and there is no procedural replacement for 210\n"
     b"authored MeshParts. `LaserFrame` is therefore additive - 125 new parts per machine in one\n"
     b"folder, `Mk2Frame`, and nothing else.\n"
     b"\n"
     b"  Build        -- 7 octagonal rib stations, 4 brass bolts per rib, flank rails in 4 bays,\n"
     b"                  top and bottom ducting per bay, hazard bars on the end ribs, and a brass\n"
     b"                  title plate reading CBL-1 / CBL-2 / CBL-3\n"
     b"  Radii        -- cast, not guessed: every rib corner sits 1.70 studs outside the hull as\n"
     b"                  measured by LaserKit's own SurfaceScanner, swept at 16 points per station\n"
     b"  DeleteFrame  -- removes Mk2Frame from one machine; RevertAll does all three\n"
     b"  BuildAll     -- idempotent across all three, and each machine is built under pcall so one\n"
     b"                  failure does not stop the other two\n"
     b"\n"
     b"The coil bay and the muzzle bay carry no rails on purpose - a straight line across a\n"
     b"12.7-stud station would need radius 14 and would read as a hoop rather than a rail. The bay\n"
     b"test enforces that rather than trusting the comment: it casts the mid-span silhouette and\n"
     b"refuses any bay whose middle bulges more than 1.00 stud past its ends.\n"
     b"\n"
     b"The folder is built unparented and attached only when complete, so a mid-build throw leaves\n"
     b"the machine exactly as it was. No part is renamed, deleted or moved, no ClickDetector is\n"
     b"created, and every part is CanCollide / CanQuery / CanTouch false, so the frame cannot be\n"
     b"clicked or collided with and gameplay is untouched.\n"),
]


def main():
    raw = io.open(P, "rb").read()
    for old, new in SUBS:
        n = raw.count(old)
        if n != 1:
            raise SystemExit("*** %d occurrences of %r ***" % (n, old[:60]))
        raw = raw.replace(old, new)
    io.open(P, "wb").write(raw)

    h = 0
    for b in raw:
        h = (h * 31 + b) & 0x7FFFFFFF
    print("README.md now %d %08x" % (len(raw), h))


if __name__ == "__main__":
    main()
