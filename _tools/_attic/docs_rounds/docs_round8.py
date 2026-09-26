# -*- coding: utf-8 -*-
"""Round 8 doc updates: the reactor-chamber wall tone was suspected and refuted.

Disk side. The same fragments are spliced into the four mirrored ModuleScripts from Studio and
both sides are then compared by BODY HASH, never by byte count -- byte-neutral drift defeats
counting, which has now cost this project two rounds (see DECISIONS 83 / NIGHT_LOG round 5).

The comparison uses roll(disk) with no offset: the module source is
`return [==[` + TWO newlines + disk bytes + `]==]` + newline, and a REMEMBERED offset is part of
the contract and drifts silently (it cost round 7 a full false MISMATCH). CLAUDE is compared after
its disk-only 0.0 section is stripped with the established b[:327] + b[1653:] cut.

NO SCENE WRITE HAPPENED THIS ROUND. No kit was written. Nothing here records a change to the
place; it records a measurement that stopped a change.
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


DEC_ENTRY = """86. THE REACTOR CHAMBER'S WALLS ARE NOT A DEFECT, AND A TONE-DISTANCE TEST COULD NOT HAVE SAID SO.

    WHAT WAS SUSPECTED. ART_DIRECTION 3.6 records the research direction for the chamber - a
    near-black box lit by emissive accents - so a bright wall family reads as the thing standing
    between the room and its own art direction. The candidate was 230 wall parts at 200,205 (the
    census splits them Metal/FacilitySteelPanel 136 and CorrodedMetal/ReactorWallPlate 94), the
    largest bright family anywhere in the facility at 378,704 studs of face area, and 71 per cent
    of every large surface in the chamber. The chamber's own wall-panel family - same material,
    same variant, same role - sat at 96..127. Same material and same variant two octaves apart is
    exactly the DECISIONS 84/85 signature, so this looked like that defect again.

    WHAT KILLED IT. The full tone histogram of the wall subtrees - every non-Neon part, not just
    the large ones - as 16-wide luminance buckets:

        0-15 46 | 16-31 120 | 32-47 407 | 48-63 231 | 64-79 264 | 80-95 290 | 96-111 313
        112-127 523 | 128-143 234 | 160-175 234 | 192-207 1040 | 208-223 108 | 224-239 40
        240-255 229      (total 4,079)

    A continuous ladder across the whole range with its mode at 192-207, and 229 parts above the
    suspected family. The suspected tone IS the room's dominant tone. Nothing here is an outlier.

    WHY THE WRONG READING LOOKED SOLID. The first histogram was restricted to large faces, face
    >= 300 studs. Large-face statistics are not the room's tone, and inside the chamber the two
    diverge completely: 980 of the 1,138 non-Neon parts in the 190-223 band ARE the walls, so
    filtering to large faces keeps the walls and discards the ladder they live in. THE MEASUREMENT
    APERTURE DECIDED THE FINDING. That is the same failure as round 5's already-existing 278
    emitters and round 7's already-dressed shell: the todo list assumes the place is under-built,
    and the place is over-authored.

    THREE INDEPENDENT CONFIRMATIONS. (1) The band above 223 is 269 parts totalling 2,044 studs of
    face area - 0.5 per cent of the wall family - and ZERO of them reach face 300. Small bright
    fittings, not blown slabs. (2) The 267 FacilityFloorPlate and 12 bright Concrete parts inside
    the wall subtrees are all VERTICAL strips at thin 0.1-0.2, i.e. decorative detail segments,
    not floor material laid on a wall. (3) Mainframe's own 2,405-part family above 223 is 1,421
    Line plus 776 TextPart plus white fan parts, 7,719 studs of face in total: labels, line work,
    and a white fan.

    THE INSTRUMENT WAS WRONG, NOT JUST THE THRESHOLD. A second test was run facility-wide: per
    container, flag every large-surface family more than 64 luminance from that container's own
    large-surface mode. It flagged five containers, and CullFolder's 55 "detached" surfaces are
    simply ReactorChamber's walls against ControlRoom's corrected shell, because one container
    holds two rooms. A tone-distance rule cannot separate an authored interior from a mistake.
    Round 7 shipped that instrument once already, as a blanket luminance threshold that would have
    greyed 25 light plates and 2 amber signal lights.

    THE INSTRUMENT THAT WORKS is material-role mismatch, which is what actually found round 7's
    ceiling. Re-run facility-wide - a horizontal slab (thin axis Y) wearing FacilityFloorPlate in
    the top quarter of its container - it finds no recurrence. Its largest hit is 1,921 studs in
    QuantumMainframe, a container only 72 studs tall where an upper horizontal surface is a deck,
    against the 4,114-stud ceiling slab it was built to catch. It also has a structural limit worth
    recording: it compares against the CONTAINER's vertical span, so for a container holding two
    rooms the "top quarter" is not a ceiling at all.

    DECISION: NO SCENE WRITE, AND NO KIT. Nothing in the chamber's walls is wrong. A ChamberKit was
    considered the way ShellKit was written and then deliberately NOT written, because a kit whose
    own scan reports "nothing to fix" is a liability - it invites a later round to run it anyway
    and act on a report that was already refuted. The measurement queries are kept on disk in
    _tools/shell_audit.lua so the audit is repeatable rather than remembered.

    STANDING CONCLUSION for CLAUDE 3.1's shell item: the facility shell is not under-built and is
    not mis-toned. What remains there is decoration and hero assets, not correction."""

PROG_ENTRY = """## Phase 31 - Reactor-chamber wall tone: measured, refuted, no write  [DONE]

ART_DIRECTION 3.6 wants the chamber to read as a near-black box, so 230 wall parts at 200,205 -
the largest bright family in the facility at 378,704 studs of face, 71 per cent of the chamber's
large surface, wearing the same material and the same variant as the room's own 96..127 panel
family - looked like the DECISIONS 84/85 defect class repeating.

The FULL non-Neon tone histogram of the wall subtrees refuted it: a continuous ladder 0 through
255, mode 192-207 at 1,040 of 4,079, with 229 parts above the suspected family. The suspected tone
is the room's dominant tone.

The wrong reading came from restricting that histogram to large faces. Large-face statistics are
not the room's tone, and here they diverge completely - 980 of the 1,138 non-Neon parts in the
190-223 band ARE the walls, so the filter keeps the walls and hides the ladder they sit in. The
aperture decided the finding.

Confirmed three ways: the band above 223 is 269 parts and 2,044 studs of face with zero parts at
face 300 or more; the 267 FacilityFloorPlate and 12 bright Concrete parts in wall scope are
vertical strips at thin 0.1-0.2, i.e. detail trim; Mainframe's 2,405-part bright family is labels
and line work at 7,719 studs in total.

A tone-distance outlier test was also tried facility-wide and is the wrong instrument - it flags
CullFolder's 55 surfaces that are only the chamber's walls against the control room's shell. The
instrument that works is material-role mismatch, and re-running round 7's ceiling test finds no
recurrence.

No scene write. No kit, deliberately. Queries kept in _tools/shell_audit.lua.

DECISIONS 86."""

CLAUDE_OLD = "- [ ] \u8bbe\u65bd\u5916\u58f3 / \u623f\u95f4\u5185\u90e8\uff08**\u63a7\u5236\u5ba4\u5df2\u5b8c\u6210**\uff09\u2014\u2014 `MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` \u4ecd\u662f\u539f\u7248"

CLAUDE_NEW = """- [ ] \u8bbe\u65bd\u5916\u58f3 / \u623f\u95f4\u5185\u90e8 \u2014\u2014 **\u63a7\u5236\u5ba4\u5df2\u5b8c\u6210\uff1b\u53cd\u5e94\u5806\u8231\u5df2\u5b9e\u6d4b\uff0c\u65e0\u9700\u6539\u52a8**
      \uff08`PROGRESS` Phase 31 / `DECISIONS` 86\uff09\u3002**\u5269\u4e0b\u7684\u4e0d\u662f\u300c\u4fee\u6b63\u300d\u800c\u662f\u300c\u88c5\u9970 + \u82f1\u96c4\u8d44\u4ea7\u300d\u3002**
      \u5b9e\u6d4b\u7ed3\u8bba\uff1a\u8231\u58c1\u90a3 230 \u4ef6 `200,205`\uff08\u5168\u573a\u6700\u4eae\u5927\u9762\u65cf\uff0c378,704 studs\u00b2\uff09**\u4e0d\u662f\u79bb\u7fa4\u503c**
      \u2014\u2014 \u8be5\u5b50\u6811\u7684**\u5b8c\u6574**\u975e Neon \u8272\u8c03\u9636\u68af\u662f **0 \u2192 255 \u8fde\u7eed\u5206\u5e03\uff0c\u4f17\u6570\u5c31\u5728 192\u2013207\uff081,040/4,079\uff09**\uff0c
      \u4e0a\u65b9\u8fd8\u6709 229 \u4ef6\u5728 240\u2013255\u3002**\u90a3\u6b21\u8bef\u5224\u7684\u6839\u56e0\u662f\u53ea\u7edf\u8ba1\u5927\u9762\uff08face \u2265 300\uff09**
      \u2014\u2014 \u5927\u9762\u7edf\u8ba1 \u2260 \u623f\u95f4\u8272\u8c03\uff1a\u8231\u91cc 1,138 \u4ef6 190\u2013223 \u7684\u975e Neon \u4ef6\u6709 980 \u4ef6**\u5c31\u662f\u5899\u672c\u8eab**\uff0c
      \u8fc7\u6ee4\u6389\u5c0f\u4ef6\u7b49\u4e8e\u628a\u5899\u7559\u5728\u4e00\u4e2a\u88ab\u62bd\u7a7a\u7684\u5206\u5e03\u91cc\u770b\u3002**\u53e3\u5f84\u51b3\u5b9a\u7ed3\u8bba\u3002**
      \u4e09\u6761\u72ec\u7acb\u590d\u6838\uff1a>223 \u7684 269 \u4ef6\u603b\u9762\u79ef\u4ec5 2,044 studs\u00b2\uff08\u5360\u5899\u65cf 0.5%\uff09\uff0c
      **face \u2265 300 \u7684 0 \u4ef6**\uff1b\u5899\u5b50\u6811\u91cc\u7684 267 \u4ef6 `FacilityFloorPlate` + 12 \u4ef6\u4eae `Concrete`
      **\u5168\u662f\u7ad6\u76f4\u8584\u6761**\uff08thin 0.1\u20130.2\uff09\uff0c\u662f\u88c5\u9970\u5d4c\u6761\uff1b`Mainframe` \u90a3 2,405 \u4ef6\u4eae\u4ef6\u662f
      `Line` 1,421 + `TextPart` 776 + \u767d\u98ce\u6247\uff0c\u5171 7,719 studs\u00b2\u3002
      **\u5224\u636e\u672c\u8eab\u4e5f\u8bb0\u4e00\u7b14**\uff1a\u6309\u300c\u8272\u8c03\u8ddd\u79bb\u300d\u627e\u79bb\u7fa4\u662f\u9519\u7684\u4eea\u5668 \u2014\u2014 \u5b83\u628a `CullFolder` \u91cc
      \u300c\u8231\u58c1 vs \u63a7\u5236\u5ba4\u65b0\u58f3\u300d\u62a5\u6210 55 \u4ef6\u79bb\u7fa4\uff1b\u771f\u6b63\u7ba1\u7528\u7684\u662f**\u6750\u6599\u89d2\u8272\u9519\u914d**\uff0c\u800c\u7b2c\u4e03\u8f6e\u90a3\u4e2a
      \u300c\u5730\u677f\u6750\u8d28+variant \u88c5\u5728\u5929\u82b1\u677f\u300d\u7684\u5168\u573a\u590d\u6d4b**\u65e0\u590d\u53d1**\u3002
      **\u672c\u8f6e\u96f6\u573a\u666f\u5199\u5165**\uff0c\u4e5f**\u6545\u610f\u6ca1\u5199 kit**\uff08\u4e00\u4e2a scan \u62a5\u300c\u65e0\u9700\u4fee\u6b63\u300d\u7684 kit \u662f\u8d1f\u503a\uff09\u3002
      `MonitorsFacility` / `RoomLights` / `Alarms` / `Lights` \u4ecd\u662f\u539f\u7248\uff08\u5b9e\u6d4b\u4e3a\u706f\u5177/\u76d1\u89c6\u5668\u88c5\u7f6e\uff0c\u975e\u5efa\u7b51\u5916\u58f3\uff09\u3002"""

for _frag in (DEC_ENTRY, PROG_ENTRY, CLAUDE_NEW):
    assert "]==]" not in _frag, "fragment would terminate the doc long-string"


def append(name, entry):
    p = os.path.join(D, name + ".md")
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8").rstrip("\n")
    io.open(p + ".bak8", "wb").write(raw)
    out = (text + "\n\n" + entry + "\n").encode("utf-8")
    io.open(p, "wb").write(out)
    print("%-14s %d -> %d (delta %+d)" % (name + ".md", len(raw), len(out), len(out) - len(raw)))
    return out


def patch(name, old, new):
    p = os.path.join(D, name + ".md")
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8")
    n = text.count(old)
    if n != 1:
        print("ABORT %s: anchor count %d" % (name, n))
        sys.exit(1)
    io.open(p + ".bak8", "wb").write(raw)
    out = text.replace(old, new).encode("utf-8")
    io.open(p, "wb").write(out)
    print("%-14s %d -> %d (delta %+d)" % (name + ".md", len(raw), len(out), len(out) - len(raw)))
    return out


if __name__ == "__main__":
    decisions = append("DECISIONS", DEC_ENTRY)
    progress = append("PROGRESS", PROG_ENTRY)
    claude = patch("CLAUDE", CLAUDE_OLD, CLAUDE_NEW)
    trimmed = claude[:327] + claude[1653:]
    print()
    print("EXPECT = {")
    print('    "PROGRESS": "%s",' % roll(progress))
    print('    "DECISIONS": "%s",' % roll(decisions))
    print('    "CLAUDE": "%s",' % roll(trimmed))
    print("}")
