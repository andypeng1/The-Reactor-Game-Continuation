# -*- coding: utf-8 -*-
"""Round 6 doc updates: the material pass was 36% incomplete and was completed.

Disk side. The Studio side splices the same fragments into the four mirrored
ModuleScripts; both sides are then compared by body hash, never by byte count
(byte-neutral drift defeats counting - see DECISIONS 83 / NIGHT_LOG round 5).
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


TABLE_OLD = """| 名字 | BaseMaterial | 贴图 assetId | StudsPerTile | 应用数 |
|---|---|---|---|---|
| `FacilitySteelPanel` | Metal | `rbxassetid://113678561896495` | 8 | **49,758** |
| `FacilityFloorPlate` | DiamondPlate | `rbxassetid://99453180185807` | 14 | **5,906** |
| `ReactorWallPlate` | CorrodedMetal | `rbxassetid://132401913334608` | 18 | **44,456** |

**关键洞察：全场景 80.2%（100,120 个）部件都是同一个默认 `Metal` 材质。**
换掉这一层 = 换掉整个游戏的观感。"""

TABLE_NEW = """| 名字 | BaseMaterial | 贴图 assetId | StudsPerTile | 应用数（现测） |
|---|---|---|---|---|
| `FacilitySteelPanel` | Metal | `rbxassetid://113678561896495` | 8 | **48,983** |
| `FacilityFloorPlate` | DiamondPlate | `rbxassetid://99453180185807` | 14 | **9,103** |
| `ReactorWallPlate` | CorrodedMetal | `rbxassetid://132401913334608` | 18 | **46,951** |

**关键洞察：全场景 80.2%（100,120 个）部件都是同一个默认 `Metal` 材质。**
换掉这一层 = 换掉整个游戏的观感。

> **⚠️ 这三个数是「现在」实测，不是不变量。** 三种材质**全部带 variant、未打标 = 0**。
> 旧值 `49,758 / 5,906 / 44,456` 是首次遍扫当时的快照；之后控制台 / 监视器重建、
> 激光重做、LED 条都改过总数，**别拿旧数对账**（`DECISIONS` 84、`PROGRESS` Phase 29）。
>
> 那次遍扫**按材质名过滤（只处理 `Metal`）**，所以**本来就写成 `DiamondPlate` 的
> 3,194 个部件根本没进循环**，渲染成库存菱形板，紧挨着 5,907 个带
> `FacilityFloorPlate` 的同类件 —— **同一材质名、两种外观，而且永远不会报错**。
> 已补齐 3,545 件（只匹配 `BaseMaterial`，避免赋值顺带改写 `Material` 本身），失败 0。
>
> `MaterialService` 另有 3 个**空壳 variant**（`MaterialVariant` / `MaterialVariant1`
> base Plastic、`CoolantRepeatingTexture` base Concrete），**无 `Texture` 子节点、
> 0 引用**，形态同 §5.3 的 `generate_material` 空产物。**故意不删**（§1.4 / §6）。"""

CD_OLD_29 = "| ClickDetector 宿主 | **1,023** |"
CD_NEW_29 = "| ClickDetector 实例 | **941**（旧记 1,023，见 `DECISIONS` 84） |"

CD_OLD_6 = "| `ClickPart` | ClickDetector 宿主 | 1,023 |"
CD_NEW_6 = "| `ClickPart` | ClickDetector 宿主 | 941（旧记 1,023） |"

ZONE_OLD = """- [ ] 材质分区的细化（现在 `Facility`/`Geometry`/`CullFolder` 用的是
      「地板判定 + 其余钢面板」的通用启发式，可以更精细）"""

ZONE_NEW = """- [~] 材质分区的细化 —— **一致性已补齐，启发式本身仍待细化**（`DECISIONS` 84、
      `PROGRESS` Phase 29）。已做：把遍扫漏掉的 3,545 件补齐，三种材质现在
      **未打标 = 0**（`FacilitySteelPanel` 48,983 / `FacilityFloorPlate` 9,103 /
      `ReactorWallPlate` 46,951）。**未做：按几何角色重新分区。**
      顺手量了可行性 —— 对 `Facility`/`Geometry`/`CullFolder`/`Mainframe`/
      `MovingParts`/`ChamberWalls` 共 70,871 件按形状分类，结果是
      **FLOOR 9,797 / WALL 430 / CHUNK 60,644**：房间绝大部分是「块状」几何，
      **纯形状启发式没有多少可分配的空间**。真要细分得按「容器意图 + 形状」
      混合判定，而不是只看形状 —— 另外 `MovingParts`（9,206 件 `ReactorWallPlate`）
      与 `Mainframe`（14,016 件 `FacilitySteelPanel`）同属机械却拿了两种皮，
      这是按容器名分配的遗留不一致，**留待下一轮**。"""

DEC_ENTRY = """84. THE MATERIAL PASS SKIPPED A THIRD OF ITS OWN TARGETS, AND NOTHING COULD HAVE REPORTED IT.

    WHAT WAS WRONG. The pass that applied the three AI materials filtered on

        if d.Material == Enum.Material.Metal then

    That is a filter on the material NAME, and it has a blind spot the pass itself created: a
    part ALREADY authored as DiamondPlate or CorrodedMetal never entered the branch at all. It
    was neither converted nor tagged, and because the pass counted only what it touched, its
    summary line - steel 49,758 / wall 44,456 / floor 5,906 - described its own successes and
    said nothing at all about what it walked past.

    THE NUMBERS. Measured 2026-09-22 across every top-level container except GameCoreTests and
    _MCPVisualTracking:

        Metal          48,546 tagged    305 untagged
        DiamondPlate    5,907 tagged  3,194 untagged
        CorrodedMetal  44,456 tagged      0 untagged

    CorrodedMetal is clean for a reason worth recording: the HEAVY containers were explicitly SET
    to CorrodedMetal plus ReactorWallPlate rather than matched, so that family never depended on
    the filter. DiamondPlate had no such path, which is exactly why it is the one that broke -
    35 per cent of every DiamondPlate surface in the place rendered as stock diamond plate sitting
    directly beside 65 per cent carrying the custom floor texture. Same material name, two
    appearances, and no error anywhere, because both are perfectly valid materials.

    THE FIX. Tagged 3,545 parts: DiamondPlate to FacilityFloorPlate, Metal to FacilitySteelPanel.
    The assignment maps on Material and only assigns a variant whose BaseMaterial matches, so it
    can never silently rewrite the Material itself as a side effect. Result: tagged 3,545, failed
    0, untagged remaining 0. Totals are now Metal 48,983 / DiamondPlate 9,103 / CorrodedMetal
    46,951, all tagged.

    Those are not the old totals and should not be reconciled against them. The place has changed
    since the first pass - console rebuild, monitor rebuild, laser rebuild, LED bars - so CLAUDE
    2.8's table was a point-in-time snapshot being read as an invariant. It now says so.

    THREE EMPTY VARIANTS, DELIBERATELY LEFT ALONE. MaterialService holds MaterialVariant and
    MaterialVariant1 (both base Plastic) and CoolantRepeatingTexture (base Concrete). All three
    have NO Texture child and ZERO part references. The first two are shaped exactly like the
    empty output generate_material is documented to produce (CLAUDE 5.3), so they are probably
    debris from that step. They are not deleted: a variant nothing references is visually inert,
    so removing it buys nothing a player can see while stepping outside the appearance-property
    envelope this project stays inside. Recorded instead, so a later sweep does not read them as
    intent.

    SECONDARY CORRECTION. Workspace holds 941 ClickDetector instances, not the 1,023 that CLAUDE
    2.9 and 6 record; both are corrected. And the four containers the night log named as the
    facility shell are not the whole shell: MonitorsFacility, RoomLights, Alarms and Lights are
    ClickDetector-free as claimed, but Facility carries 16, MovingParts 30 and Geometry 1, so
    shell work is not uniformly binding-free."""

PROG_ENTRY = """## Phase 29 - The material pass skipped a third of its targets  [DONE]

The pass that applied the three AI materials filtered on Material == Metal, so parts already
authored as DiamondPlate or CorrodedMetal never entered the loop and were neither converted nor
tagged. Its own summary counted only what it touched, so it could not report the gap.

Measured: Metal 48,546 tagged / 305 untagged, DiamondPlate 5,907 tagged / 3,194 untagged,
CorrodedMetal 44,456 tagged / 0 untagged. CorrodedMetal survived only because the HEAVY
containers set it explicitly instead of matching it.

Fixed by tagging 3,545 parts - DiamondPlate to FacilityFloorPlate, Metal to FacilitySteelPanel -
mapping on Material and assigning only variants whose BaseMaterial matches, so the Material
itself can never be rewritten as a side effect. Tagged 3,545, failed 0, untagged remaining 0.
Totals are now Metal 48,983 / DiamondPlate 9,103 / CorrodedMetal 46,951, all tagged.

CLAUDE 2.8's counts were a snapshot of the first pass, not an invariant; they are updated and
labelled as such. The night log's claim that the facility shell is ClickDetector-free holds for
the four containers it named but not for the shell as a whole - Facility has 16, MovingParts 30,
Geometry 1 - and CLAUDE 2.9's ClickDetector total is 941, not 1,023.

Three empty MaterialVariants (MaterialVariant, MaterialVariant1, CoolantRepeatingTexture) have no
Texture child and zero references; left in place deliberately and recorded rather than deleted.

DECISIONS 84."""

INSERTS = [TABLE_NEW, CD_NEW_29, CD_NEW_6, ZONE_NEW, DEC_ENTRY, PROG_ENTRY]
for frag in INSERTS:
    assert "]==]" not in frag, "insert would terminate the doc long-string"


def patch(name, pairs):
    p = os.path.join(D, name)
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8")
    for old, new in pairs:
        n = text.count(old)
        if n != 1:
            print("ABORT %s: anchor count %d for %r" % (name, n, old[:60]))
            sys.exit(1)
    io.open(p + ".bak7", "wb").write(raw)
    for old, new in pairs:
        text = text.replace(old, new)
    out = text.encode("utf-8")
    io.open(p, "wb").write(out)
    print("%-14s %d -> %d (delta %+d)" % (name, len(raw), len(out), len(out) - len(raw)))
    return out


def append(name, entry):
    p = os.path.join(D, name)
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8").rstrip("\n")
    io.open(p + ".bak7", "wb").write(raw)
    out = (text + "\n\n" + entry + "\n").encode("utf-8")
    io.open(p, "wb").write(out)
    print("%-14s %d -> %d (delta %+d)" % (name, len(raw), len(out), len(out) - len(raw)))
    return out


if __name__ == "__main__":
    claude = patch("CLAUDE.md", [
        (TABLE_OLD, TABLE_NEW),
        (CD_OLD_29, CD_NEW_29),
        (CD_OLD_6, CD_NEW_6),
        (ZONE_OLD, ZONE_NEW),
    ])
    decisions = append("DECISIONS.md", DEC_ENTRY)
    progress = append("PROGRESS.md", PROG_ENTRY)

    print()
    for name, out in (("DECISIONS.md", decisions), ("PROGRESS.md", progress)):
        print("%-14s body=%d hash=%s" % (name, len(out), roll(out)))
    trimmed = claude[:327] + claude[1653:]
    print("CLAUDE.md      raw=%d  body=%d hash=%s" % (len(claude), len(trimmed), roll(trimmed)))
