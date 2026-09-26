# -*- coding: utf-8 -*-
"""Round 7 doc updates: the control-room shell correction (DECISIONS 85 / PROGRESS Phase 30).

Disk side. The four .md files are PLAIN MARKDOWN -- there is no `return [==[` wrapper on
disk; the wrapper lives only in the Studio ModuleScript. The module's raw content is
NEWLINE + the disk bytes, because the module is authored as

    "return [==[" .. NL .. body .. "]==]" .. NL

and Lua skips the first newline after a long bracket, so the runtime value already agrees
with the disk.

CORRECTED 2026-09-22: the module source is `return [==[` + TWO newlines + the disk bytes
+ `]==]` + a newline. The first version of this file assumed ONE newline, so it prepended a
single newline when recomputing the module-side hash; every comparison came out MISMATCH and
the run read as a content divergence that did not exist.

The offset was re-derived rather than remembered: sub(Source, k, #Source - j) was swept over
k in 12..14 and j in 4..6 inside Studio and each candidate matched against the raw disk hash.
k=14, j=5 matched all four docs exactly. The comparison below therefore uses roll(disk), which
needs no offset at all -- a remembered offset is part of the contract and drifts silently, a
hash of the raw file cannot.

Byte counts are recorded for orientation only. Hashes are the judge.
"""
import io
import os
import sys

D = r"D:\rblxTRGproject"


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


DEC_NEW = """85. THE CONTROL-ROOM SHELL NEEDED A CORRECTION, NOT A REBUILD, AND THE AUDIT IS WHAT SAID SO.

    THE PLAN THAT DID NOT SURVIVE MEASUREMENT. The shell was assumed to be a bare box waiting for
    geometry, so the kit was written to lay a 182-part panel-and-rib field on all four walls and
    to add a perimeter ceiling bulkhead and a cove. Its own clash audit returned HARD=0 and
    SOFT=713. HARD=0 confirmed the rib-depth reasoning - 182 planned specs, zero clashes with any
    of the 561 light parts - but the 713 soft hits were the point, because they forced a
    structural dump of the walls, and the walls turned out to be fully dressed already.

      Wall (east)   Union 40.1 x 21.25 x 0.75 base plane, 10 vertical panels 0.125 thick, and
                    4 full-height ribs 1.5 x 21.25 x 0.75
      Wall (south)  lower panel field 7.95 x 9.95 x 0.1 and 7.75 x 9.75 x 1 (y 277.6..287.6),
                    upper panel 21.9 x 10.55 x 0.75 (y 287.6..298.1), slats 0.2 x 13.25 x 0.75
      Wall (north)  mirror of south
      FrontWall     no solid plane at all - a duct chase, 26.5 x 4 x 10 beams crossing from the
                    west wall to x = 108.3, fifteen studs inside the room

    The field would have laid a second panel layer over hand-authored work on all four walls, and
    two of its specs would have buried a security camera TextPart at (141.80, 295.85, -0.71).
    The plan was dropped in full: no panels, no ribs, no bulkhead, no cove, no accent line.
    Nothing in the kit builds anything.

    THE DEFECT THAT WAS ACTUALLY THERE. The room already runs a coherent tonal ladder. Across the
    shell's 1,379 parts the ceiling band (y_top above 296) reads 100 x 702 / 75 x 295 / 60 x 84 /
    50 x 23, and 16 wall parts already sat at 100. Two things fell outside that ladder:

      1. The ceiling slab (Geometry.Unions.Union, 55.58 x 1.00 x 74.03 at y 298.61) wore
         DiamondPlate plus FacilityFloorPlate at 160,160,160 - the same material AND the same
         variant the control-room floor wears. A floor texture on a ceiling. Sixteen wall parts
         wore it too.
      2. The walls were 160,160,160 and thirteen FrontWall parts were 205,205,205. RebuildKit's
         desk palette is hull 108 / post 86 / dark 75 / darker 60 and the deck runs 68..83, so
         every wall was brighter than the brightest large desk surface. The furniture read as
         dark shapes on a bright wall - ART_DIRECTION 2.1's red line, expressed tonally.

    Same class as DECISIONS 84: a legal material, in the wrong place, producing no error.

    THE NEAR MISS, WHICH IS WHY THIS ENTRY EXISTS. The first version of the rule was a blanket
    luminance threshold. The dry run showed it would have recoloured 25 of the room's own light
    plates - RebuildKit's light (163,162,165) Plastic, which the palette comment says MUST stay
    Plastic or it blows out to flat white - plus two amber signal lights at (226,155,64). Those
    are fittings, not surfaces. Greying them would have deleted the room's lighting in order to
    fix its walls. The gate was moved from the tone to the material variant: a part wearing
    FacilitySteelPanel or FacilityFloorPlate is structure, a part wearing no variant is a fitting
    and is left alone, and the luminance test then only chooses which outliers inside that
    structural set get pulled back.

    RESULT. recoloured 80, resteeled 25, failed 0, skipped 1,291 of 1,379. Verified from live
    instances: zero structural parts above luminance 120, zero FacilityFloorPlate left anywhere
    on the shell, all 27 fittings preserved, and 88 origin records - exactly 80 + 25 - 17 overlap.
    The shell now reads 100 x 813 / 75 x 301 / 60 x 87, so its brightest large surface is 100,
    below the desk hull at 108.

    APPEARANCE PROPERTIES ONLY - Color, Material, MaterialVariant. No part created, renamed,
    moved or destroyed, and CullFolder.ControlRoom holds zero ClickDetectors, so nothing in
    CLAUDE 6's binding table was reachable. Originals are recorded per part in a ShellKitOrigin
    attribute before the first write, so RestoreBase() is exact."""

PROG_NEW = """## Phase 30 - Control-room shell: corrected, not rebuilt  [DONE]

The shell was assumed bare and was going to get a 182-part panel-and-rib field plus a ceiling
bulkhead and a cove. The kit's own clash audit returned HARD=0 / SOFT=713, and the 713 soft hits
forced a structural dump that refuted the premise: all four walls already carry panel fields,
vertical slats and ribs, and the west side is a duct chase with 26.5 x 4 x 10 beams crossing
fifteen studs into the room. Two of the planned specs would also have buried a security camera
TextPart. The plan was dropped whole, and the kit builds nothing.

What the shell actually needed was a correction. The room already runs a 100/75/60/50 ladder and
two things sat outside it: the ceiling slab plus 16 wall parts wearing DiamondPlate and
FacilityFloorPlate - the floor's material and the floor's variant - at 160, and 13 FrontWall
parts at 205. Every wall was brighter than the desk hull at 108.

The first rule was a blanket luminance threshold, and the dry run caught it recolouring 25 light
plates and 2 amber signal lights. Fittings, not surfaces. The gate moved from the tone to the
material variant.

Applied: recoloured 80, resteeled 25, failed 0, skipped 1,291 of 1,379. Verified live - zero
structural parts above luminance 120, zero FacilityFloorPlate on the shell, all 27 fittings
preserved, 88 origin records. The shell's brightest large surface is now 100, below the desk
hull, so ART_DIRECTION 2.1's red line holds numerically. Appearance properties only;
ControlRoom holds zero ClickDetectors.

DECISIONS 85."""

CLAUDE_OLD = "- [ ] 设施外壳 / 房间内部 —— `MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` 仍是原版"

CLAUDE_NEW = """- [x] **控制室外壳 —— 修正而非重建**（`PROGRESS` Phase 30 / `DECISIONS` 85）——
      `Rebuild.ShellKit`，**新建 0 件**。原计划是四面墙 182 件板/肋 + 天花板压顶 + 凹槽，
      被它自己的碰撞审计推翻（`HARD=0 SOFT=713`）：四面墙**本来就做满了** ——
      东墙 = `Union 40.1×21.25×0.75` 底板 + 10 片 0.125 薄竖板 + 4 根通高肋；
      南北墙 = 下部板场 + 上部大板 + `0.2×13.25` 竖格栅；西侧 `FrontWall`
      **根本没有整片墙面**，是跨进房间 15 studs 的管道井。
      而且那 182 件里有 2 件会埋掉一个摄像头 `TextPart`（(141.80, 295.85, −0.71)）。
      **真正的缺陷**：天花板板与 16 件墙件戴着 `DiamondPlate` + `FacilityFloorPlate`
      （**地板自己的材质和 variant**）@160，`FrontWall` 另有 13 件 @205 ——
      全都**亮过控制台 hull 的 108**，于是家具成了亮墙上的暗块。
      房间本来就有 `100/75/60/50` 阶梯（1,379 件里 702 件在 100）。
      改：重着色 80 + 换材质 25，失败 0，**27 件灯具/信号灯全保**，壳面最亮大面降到 **100**。
      **差点改坏的**：第一版判据是「亮度 > 120」，干跑显示它会**把 25 件灯板和 2 盏琥珀信号灯
      改成灰色** —— 判据因此从「亮度」换成「材质 variant」：戴 `FacilitySteelPanel` /
      `FacilityFloorPlate` 的是结构，没戴 variant 的是灯具，一律不碰。
      纯外观属性，未增删改移任何部件；`ControlRoom` 下 ClickDetector = 0。
- [ ] 设施外壳 / 房间内部（**控制室已完成**）—— `MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` 仍是原版"""

README_ANCHOR = "  LaserKit    -- the CBL laser refinish: three machines, colour plus accents"
README_ADD = (README_ANCHOR + "\n"
              + "  ShellKit    -- the control-room shell CORRECTION: recolour plus material fix, builds nothing\n"
              + "  ControlRoomKit -- the control-room floor deck (88 pieces) and its cyan walkway accent")

# Module-side hash of sub(Source, 14, #Source - 5), read out of Studio after the splice, which
# is byte-identical to the disk file. CLAUDE is compared after its disk-only 0.0 section is
# stripped with the established b[:327] + b[1653:] cut.
EXPECT = {
    "PROGRESS": "59a40029",
    "DECISIONS": "3dc6be87",
    "README": "74dd612d",
    "CLAUDE": "746e9237",
}


def edit(name, mode, old, new):
    p = os.path.join(D, name + ".md")
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8")
    if mode == "replace":
        n = text.count(old)
        if n != 1:
            print("ABORT %s: anchor count %d" % (name, n))
            sys.exit(1)
        text = text.replace(old, new)
    else:
        text = text + new + "\n"
    out = text.encode("utf-8")
    io.open(p + ".bak7", "wb").write(raw)
    io.open(p, "wb").write(out)
    return out


if __name__ == "__main__":
    results = {
        "PROGRESS": edit("PROGRESS", "append", None, PROG_NEW),
        "DECISIONS": edit("DECISIONS", "append", None, DEC_NEW),
        "README": edit("README", "replace", README_ANCHOR, README_ADD),
        "CLAUDE": edit("CLAUDE", "replace", CLAUDE_OLD, CLAUDE_NEW),
    }
    print("%-10s %-9s %-9s %-9s %s" % ("doc", "disk", "module", "delta", "verdict"))
    ok = True
    for name in ("PROGRESS", "DECISIONS", "README", "CLAUDE"):
        out = results[name]
        if name == "CLAUDE":
            out = out[:327] + out[1653:]
        module_len = len(out)
        module_hash = roll(out)
        good = module_hash == EXPECT[name]
        ok = ok and good
        print("%-10s %-9d %-9d %-9s %s" % (name, len(out), module_len, module_hash,
                                           "MATCH" if good else "MISMATCH (expect " + EXPECT[name] + ")"))
    print("ALL FOUR MATCH" if ok else "*** MISMATCH ***")
