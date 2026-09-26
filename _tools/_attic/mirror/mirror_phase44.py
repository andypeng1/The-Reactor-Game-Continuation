# -*- coding: utf-8 -*-
"""Mirror the Phase 44 documentation additions onto the disk .md files.

WHY THIS FILE EXISTS. Section 0.0 requires that any change carry its documentation in the same
step, and that the game-side ModuleScripts stay the source of truth with the disk .md as a
mirror. The Phase 44 text was written into three ModuleScripts (PROGRESS, DECISIONS_2, README)
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

PHASE 44 NOTE. DECISIONS and CLAUDE are absent from TARGETS on purpose: Phase 44 edited three
modules, and the module-reported pairs for the other two are unchanged from Phase 43. A missing
entry here would silently mean "not checked", so check.py asserts the target set instead.
"""
import io
import os
import sys

D = r"D:\rblxTRGproject"

# (path, module-reported image length, module-reported roll hash) -- read back out of Studio
# after the edits, by the snippet in verify_docs.py's docstring.
TARGETS = {
    "PROGRESS.md": (158059, "6f178d29"),
    "DECISIONS_2.md": (115574, "0e2ab947"),
    "README.md": (43911, "36bf7b8b"),
}

PROGRESS_BLOCK = """## Phase 44 - The first unit is parked, and the warning is the ledger  [DONE]

Scope: data. One model changed parent and name; nothing inside it was created, renamed, deleted or
altered, so no gameplay mechanic moved and no name in the CLAUDE 6 binding table is involved.

WHAT MOVED. Workspace.MedicalDispenser -> ServerStorage.GameCoreBaseline.Originals_facility,
renamed ORIG_MedicalDispenser. 483 BaseParts, 625 descendants, ExtentsSize 7.1 by 11.8 by 5.8,
pivot 249.039581, 281.426758, 52.893997.

WHY THIS UNIT WAS THE PILOT, MEASURED RATHER THAN ASSUMED. The operator picked it on the strength
of a reference graph of one line. That claim was then tested two more ways. First, the sole
executable hit is FacilityBridge:24, a ROOT_MAP entry, and nothing anywhere reads
FacilityBridge.Resolved.MedicalDispenser - the bridge's only consumers are CacheLights (RoomLights,
Lights) and CacheAlarmSounds (Alarms), and FacilityBridge.Get is called by no one. Second, the
unit's only trigger host, TriggerPart, appears in ZERO scripts, and the sole live Touched:Connect
in the project is GatewaySystem:51 bound to one named box, not a workspace sweep. So in this build
the medical station is decorative: it renders and nothing drives it.

THE LEDGER IS COPIED, NOT INVENTED. Four attributes, in the format the shipped entries already use:

    GameCoreParkedName     string   MedicalDispenser
    GameCoreParkedFrom     string   Workspace.MedicalDispenser
    GameCoreParkedPivot    CFrame   249.039581, 281.426758, 52.8939972, 1, 0, 0, 0, 1, 0, 0, 0, 1
    GameCoreArchivedFrom   string   ServerStorage.GameCoreBaseline.Originals_facility

GameCoreArchivedFrom names the BAY, not the source. Both shipped examples settle it:
ORIG_MainReactorConsole carries ParkedFrom = Workspace.Consoles.MainReactorConsole and
ArchivedFrom = Workspace.Rebuild.Originals. Writing the source path there would have duplicated
ParkedFrom and carried no information - a field that looks populated and says nothing.

WHY A NEW GROUP. GameCoreBaseline held three: Originals_consoles_and_monitors, ReactorCBLs_original
and Superseded_Mk2_preLEDBar. None of them is a home for a standalone facility unit, so
Originals_facility was created. Note that RebuildKit.PlaceReference probes only
Originals_consoles_and_monitors and Originals by name, so Originals_facility is NOT yet visible to
that helper - registering it belongs to the install machinery that does not exist yet, and saying
otherwise would be a convention nothing reads.

VERIFIED BY READING INSTANCES BACK. Before and after: parts 483, descendants 625, pivot delta
0.000000 studs. Workspace no longer holds the name; the parked node is at
ServerStorage.GameCoreBaseline.Originals_facility.ORIG_MedicalDispenser with all four attributes
present and typed as listed above.

VERIFIED BY PLAYTEST, NOT BY READING THE CODE. Workspace.GameCoreTests.GameCoreSelfTest was run
with the model already parked. It reports finalStatus PASS, ok true, and bridgeResolved 17. The map
holds 18 entries and 17 of those names exist in Workspace, so the before value was 18: the count
dropped by exactly the one unit parked, and the whole system chain still runs. The log carries
exactly one new line, [FacilityBridge] missing workspace model: MedicalDispenser. The 118 error
lines are the known sound-authorization spam and none of them is new.

THE ONE WARNING IS THE POINT, NOT NOISE. Parking a mapped unit makes the bridge warn once per boot,
and the tempting fix is to let it fall back to the archive. That would be worse than the warning:
for the units whose descendants the bridge actually drives - RoomLights, Lights, Alarms - a
fallback would hand back a ServerStorage instance, and Light.Enabled or Sound:Play on it would
succeed and do nothing. That is the silent failure CLAUDE 0.13 names, and it would be
indistinguishable from success. The warning is emitted exactly while a parked unit has no Mk2 at its
old path, and it clears itself when the Mk2 is installed under the original's own name - which is
the pairing the operator asked for. The warning is the ledger.

STILL OPEN. No Mk2 exists for this unit, so the world is one medical station poorer until one is
built, and nothing on the bench or in RebuildKit supplies it. The remaining units are untouched.
And a repeatable install still does not exist: MK2PREV_, GameCoreBench and Install each appear ZERO
times in RebuildKit's 1796 lines, so the superseded-Mk2 archive and the install step were both done
by one-off scripts."""

DECISIONS2_BLOCK = """128. A NAME SEARCH DOES NOT MEASURE WHETHER SOMETHING IS DRIVEN.

    WHAT HAPPENED. The operator proposed MedicalDispenser as the parking pilot because its reference
    graph came to a single grep hit. That was checked two further ways before anything moved: the
    hit is a ROOT_MAP table entry and no code reads the entry it produces, and the unit's only
    trigger host has zero matches in any script.

    WHY THE FIRST HIT WAS NOT ENOUGH. A grep tells you where a NAME is written. It cannot tell you
    that the thing those names name is ever dereferenced, called or driven, and an entry added to a
    table is only a name written down. The pilot was safe because of the second and third
    measurements, not the first.

    THE INSTRUMENT HAS LIMITS AND THEY WERE STATED. Zero matches for TriggerPart proves nobody binds
    by that name. It does not prove nothing binds by CLASS or by REGION, so the search for a driver
    was widened to every Touched:Connect in the project - one exists, on a single named box. A
    conclusion is only as strong as the search that produced it, and the honest form of the claim is
    that no driver was found by name or by class, not that there is no driver.

129. THE ARCHIVE LEDGER IS COPIED FROM THE SHIPPED ENTRIES, NOT INVENTED.

    WHAT HAPPENED. Parking MedicalDispenser needed the provenance attributes, and the project
    already had them on ORIG_MainReactorConsole and on the legacy Workspace.Rebuild.Models.AB_REF.
    They were read first and then reproduced: GameCoreParkedName, GameCoreParkedFrom,
    GameCoreParkedPivot (a real CFrame) and GameCoreArchivedFrom.

    WHY READING FIRST MATTERED. GameCoreArchivedFrom names the BAY, not the source. Both shipped
    examples agree - ParkedFrom is Workspace.Consoles.MainReactorConsole while ArchivedFrom is
    Workspace.Rebuild.Originals. A self-consistent guess the other way round would have written the
    source path into both fields: every attribute present, every type correct, and one of them
    carrying no information at all. Nothing would have failed, because nothing reads these fields
    automatically.

    THE GENERAL FORM. A provenance record is a format, and a format described only in prose is
    guessable. Where an example exists, the example is the specification.

130. A BOOT-TIME WARNING CAN BE THE CORRECT SIGNAL RATHER THAN NOISE TO BE SILENCED.

    WHAT HAPPENED. Parking a unit that FacilityBridge maps makes it warn once per boot: missing
    workspace model. The obvious tidying is a fallback that resolves the name out of the archive,
    so the warning disappears.

    WHY THAT WOULD BE WORSE. Not every mapped unit is inert. For the ones whose descendants the
    bridge actually drives, CacheLights and CacheAlarmSounds walk RoomLights, Lights and Alarms and
    assign Light.Enabled or call Sound:Play. A ServerStorage fallback would hand back instances that
    accept those writes and do nothing, so the bridge would report success while the facility
    stayed dark and silent - the failure CLAUDE 0.13 describes, where the error path and the success
    path have the same shape.

    WHAT THE WARNING ACTUALLY IS. It is emitted exactly while a parked unit has no Mk2 at its old
    path, and it stops by itself when the Mk2 is installed under the original's own name. It is a
    per-unit statement of what the parking pass still owes, which is the pairing the operator asked
    for. The self-test's bridgeResolved count says the same thing numerically: 18 entries, 17
    resolved, one unit waiting."""

README_BLOCK = """### Parking an original facility unit

An original leaves Workspace for `ServerStorage.GameCoreBaseline.Originals_facility` and is renamed
`ORIG_<Name>`. Four attributes are copied from the shipped entries rather than invented, and the
park is only complete when they are written: `GameCoreParkedName` (the original leaf name),
`GameCoreParkedFrom` (the original full path), `GameCoreParkedPivot` (the original pivot, as a real
CFrame attribute) and `GameCoreArchivedFrom` (the archive bay it landed in - the bay, not the
source; both shipped examples settle this).

`ORIG_MedicalDispenser` is the first entry, parked in Phase 44. The archive holds the original; the
live path holds nothing until an Mk2 is installed under the original's own name, which is how the
consoles and monitors were replaced.

Two things to know before parking the next unit. `RebuildKit.PlaceReference` probes only
`Originals_consoles_and_monitors` and `Originals`, so `Originals_facility` is not yet visible to it.
And `FacilityBridge` will warn once per boot for a mapped unit that is parked - that warning is the
per-unit list of what still needs an Mk2, and it clears when the Mk2 lands. Do not add an archive
fallback to silence it: for a unit the bridge actually drives, a ServerStorage instance accepts
`Light.Enabled` and `Sound:Play` and does nothing. See DECISIONS 128 to 130."""

BLOCKS = {
    "PROGRESS.md": PROGRESS_BLOCK,
    "DECISIONS_2.md": DECISIONS2_BLOCK,
    "README.md": README_BLOCK,
}

# Every file the mirror is responsible for. check.py asserts TARGETS equals this set, so a target
# silently dropping out of TARGETS is an error rather than an unchecked file.
COVERS = ("PROGRESS.md", "DECISIONS_2.md", "README.md")


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def main():
    if "check" in sys.argv and set(TARGETS) != set(COVERS):
        print("*** TARGETS != COVERS: %s ***" % (set(TARGETS) ^ set(COVERS)))
        return 1
    dry = "check" in sys.argv
    rc = 0
    for name in COVERS:
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
