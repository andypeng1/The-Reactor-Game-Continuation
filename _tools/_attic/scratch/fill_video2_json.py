"""Complete the second video's Information.json.

The user's standing instruction is that the folder's JSON should be filled in by
me, and that the structure they provide may be extended. This video shipped with
only a `Video` block; this script appends the measured media metadata and a
`Content` block matching the schema of video 1, so the two files can be compared
field-for-field by TotalSummary.

The user-supplied `Video` keys are never retyped -- they are read back from the
file and rewritten unchanged. Same rule as patch_information.py: retyping a quote
is how a quote stops being one.

Written as bytes, not text: on Windows text mode turns every \n into \r\n.

Run: python _tools/fill_video2_json.py
"""

import json
from pathlib import Path

DEST = Path(
    "D:/rblxTRGproject/Videos/"
    "Roblox The Reactor Guide The only(prob) Operators guide that youll ever need/"
    "Information.json"
)

# Measured with ffprobe on 2026-09-26, not copied from anywhere.
VIDEO_META = {
    "Duration_s": 339.754376,
    "Resolution": "640x360",
    "FPS": 30,
    "VideoCodec": "h264",
    "AudioCodec": "aac (128 kbps, 44100 Hz, stereo)",
}

# Everything below is read off frames by the glm-4.5v sidecar. `Verified` marks
# how many independent reads agreed; a claim that survived only one contact-sheet
# read and failed single-frame recheck is listed in Conflicts as spurious instead
# of being promoted into KeyFacts.
CONTENT = {
    "Language": "en (no narration — on-screen text only)",
    "Summary": (
        "A 5m40s silent, music-only visual walkthrough of the same reactor game. No narration "
        "exists on the audio track (verified: 0 segments with VAD disabled). All content comes "
        "from burned-in caption text and in-game UI read at 640x360. Highest-value material is the "
        "game's own in-game documentation screen, which states state 2 = high power state, "
        "18000F to 30000F, extraction rate 25%, difficulty medium, and state 3 = extreme power "
        "state, 30000F to 35000F, difficulty very hard. Also shows the PROCESSOR EMISSION "
        "CALIBRATOR minigame, the Equinox and EFE (Energy Fluctuation Event) events, and a live "
        "notice reading 'Note: Shift 3 is temporarily disabled for instability'."
    ),
    "Chapters": [
        {"At": "00:00", "Name": "Cold room", "Note": "PENDING REACTOR ACTIVATION; TURBINE CYCLE GROUP C9"},
        {"At": "00:30", "Name": "Console tour", "Note": "laser level switch / pressure purge button called out by arrows"},
        {"At": "01:15", "Name": "In-game documentation screen", "Note": "state 2 and state 3 ranges and difficulty"},
        {"At": "02:00", "Name": "Pressure control", "Note": "energy extractor, 'switch it down'"},
        {"At": "03:30", "Name": "PROCESSOR EMISSION CALIBRATOR", "Note": "HIGHER / LOWER minigame"},
        {"At": "04:30", "Name": "Equinox and EFE", "Note": "monitor readings under both events"},
    ],
    "KeyFacts": [
        "In-game doc screen: state 2 = high power state, temp range 18000F to 30000F, extraction rate 25%, difficulty medium.",
        "In-game doc screen: state 3 = extreme power state, temp range 30000F to 35000F, difficulty very hard, 'a mistake can lead to a meltdown in this state'.",
        "A live in-game notice reads 'Note: Shift 3 is temporarily disabled for instability'.",
        "Equinox is a real periodic in-game event — the monitor itself prints 'or Equinox:'.",
        "EFE (Energy Fluctuation Event) is a real periodic in-game event with its full name shown on screen.",
        "PROCESSOR EMISSION CALIBRATOR is a minigame, with PROCESSOR STATUSES and HIGHER / LOWER buttons.",
        "The audio track contains no speech. It is a loud, heavily clipped music track (mean -10.6 dB, 289876 samples at 0 dB).",
        "The player HUD exposes Client 100/100, Ping 0, Tick 64.0, FPS 100, Time 00:00:00, Players 1/20.",
        "Monitors read CORE TEMPERATURE, CORE TEMP FLUCTUATION, NET OUTPUT, EXTRACTION RATE, P.E.A STRESS, CHAMBER RADIATION, CHAMBER PRESSURE and H.O.E.F INTEGRITY.",
        "Console-side panel labels include MAIN REACTOR CONSOLE, EMERGENCY VENT 3, MASTER SWITCH, STARTUP CONTROLS, POWER EXTRACTION, MAIN ACCESS, ELECTRIFIED FLOOR PANELS.",
    ],
    "Numbers": [
        {"Value": "18000 F", "Meaning": "state 2 lower bound (in-game doc screen)", "Verified": "two independent reads"},
        {"Value": "30000 F", "Meaning": "state 2 upper bound (in-game doc screen)", "Verified": "two independent reads"},
        {"Value": "35000 F", "Meaning": "state 3 upper bound (in-game doc screen) — conflicts with 39000 elsewhere", "Verified": "two independent reads"},
        {"Value": "25%", "Meaning": "extraction rate of state 2, per the in-game doc screen", "Verified": "single read; matches Config.Sim.ExtractionFraction = 0.25"},
        {"Value": "1.4 kW", "Meaning": "Power ceiling on the inventory panel ('1 / 1.4 kW') — panel may not be this game, see Conflicts", "Verified": "single read"},
        {"Value": "64.0", "Meaning": "player HUD 'Tick:' reading", "Verified": "single read"},
        {"Value": "6668 PSI", "Meaning": "CHAMBER PRESSURE live reading", "Verified": "single read"},
        {"Value": "30152 F / 14807 F / 14851 F", "Meaning": "CORE TEMPERATURE live readings across the session", "Verified": "single reads"},
        {"Value": "64%", "Meaning": "P.E.A STRESS live reading", "Verified": "single read"},
        {"Value": "99% / 75%", "Meaning": "H.O.E.F INTEGRITY live readings", "Verified": "single reads"},
        {"Value": "592 R", "Meaning": "CHAMBER RADIATION live reading", "Verified": "single read"},
    ],
    "Procedures": [
        {
            "Name": "Processor emission calibration minigame",
            "Steps": [
                "Reach the PROCESSOR EMISSION CALIBRATOR panel.",
                "Read the PROCESSOR STATUSES readout.",
                "Press HIGHER or LOWER to bring each processor into range.",
            ],
        },
        {
            "Name": "Pressure control by the energy extractor",
            "Steps": [
                "Find the energy extractor (called out in the video as useful for reaching quota faster).",
                "Use the marked switch to adjust it.",
            ],
        },
    ],
    "UI_Text": [
        "MAIN REACTOR MONITORING", "REACTOR THERMALS", "REACTOR THERMAL MONITORING", "N LASER MONITORING",
        "BEAM THERMALS MONITORING", "REACTOR STRUCTURE & CHAMBERS", "EMERGENCY SYSTEMS", "EMERGENCY VENT 3",
        "MASTER SWITCH", "STARTUP CONTROLS", "SYSTEM ERROR", "PROCESSOR EMISSION CALIBRATOR",
        "PROCESSOR STATUSES", "HIGHER", "LOWER", "PENDING REACTOR ACTIVATION", "TURBINE CYCLE GROUP C9",
        "MAIN ACCESS", "ELECTRIFIED FLOOR PANELS", "FUSION REACTOR", "POWER EXTRACTION",
        "CAMOS ELECTRIC GRID MANUAL", "DANGER", "WARNING", "% OF STABILITY", "CHAMBER STATUS",
        "E & M ABSORPTION", "COOLANT INTEGRITY", "OIL PRESSURE", "CTRL-3 SYSTEMS", "CTRL-4 POWER",
        "MAINTENANCE FUNCTIONS", "MATTER/ENERGY FUNCTIONS", "Note: Shift 3 is temporarily disabled for instability",
    ],
    "Conflicts": [
        {
            "ProjectRef": "ServerStorage.Data.DataCollection vs this video's in-game doc screen",
            "ProjectSays": "CORE_STATE_THRESHOLDS = {5600, 17500, 29500, 39000}, so state 3 spans 29500 to 39000 F.",
            "VideoSays": "state 3 spans 30000F to 35000F, and 'a mistake can lead to a meltdown in this state'.",
            "At": "01:15",
            "Severity": "high",
            "Note": "Video 1 and TRGWeb both say 39000; this video's own documentation screen says 35000. Two independent reads agree on 35000.",
            "Status": "unresolved",
            "ResolvedBy": None,
            "Outcome": (
                "30000 is explicable as 29500 rounded up, but 35000 bears no rounding relationship to 39000. "
                "Either the game's own documentation text is stale relative to its code, or this video is a "
                "different build. Settle it with one live measurement: run the core between 35000 and 39000 F "
                "and observe whether it melts down. Not guessed."
            ),
        },
        {
            "ProjectRef": "ServerStorage.Data.DataCollection (internal)",
            "ProjectSays": "MELTDOWN_TEMP_F = 38000, but CORE_STATE_THRESHOLDS ends at 39000 and METU_FIRE_TEMP_F = 39000.",
            "VideoSays": "state 3 tops out at 35000 F, above which a mistake melts down.",
            "At": "01:15",
            "Severity": "medium",
            "Note": "Third distinct meltdown figure. The in-game doc screen does not name a number, only that state 3 can melt down.",
            "Status": "unresolved",
            "ResolvedBy": None,
            "Outcome": "Same measurement as the entry above would close both.",
        },
        {
            "ProjectRef": "none — suspected foreign UI",
            "ProjectSays": "The project has no inventory panel and no CTRL-3 / CTRL-4 system panels.",
            "VideoSays": "A panel shows Fuel / O2 / Water / Food / Medkits / Ammo / Batteries / Scrap, 'Power | 1 / 1.4 kW', and CTRL-3 SYSTEMS / CTRL-4 POWER / MAINTENANCE FUNCTIONS / MATTER-ENERGY FUNCTIONS.",
            "At": "00:30",
            "Severity": "medium",
            "Note": "This panel has no counterpart in video 1, in the AIRemake place, or in DataCollection's instance paths.",
            "Status": "unresolved — treated as not-this-game and excluded from evidence",
            "ResolvedBy": None,
            "Outcome": "Possibly another game or a mod appearing in the same video. Excluded from KeyFacts and from TotalSummary's fact tables; recorded here only so it is not silently dropped.",
        },
        {
            "ProjectRef": "spurious reading, retracted",
            "ProjectSays": "No such prompt exists in the project.",
            "VideoSays": "A 3x2 contact sheet read produced the string '[E] EJECT FUEL ROD (EMPTY)'.",
            "At": "00:00-01:15",
            "Severity": "low",
            "Note": "Single-frame recheck of f001..f006 (t = 0/15/30/45/60/75 s) found it in ZERO of the six frames.",
            "Status": "resolved — hallucinated by the low-resolution contact sheet",
            "ResolvedBy": "per-frame recheck with the same model",
            "Outcome": (
                "Judged spurious and not promoted to KeyFacts. Generalises to a rule now recorded in "
                "TotalSummary: any string read off a tiled contact sheet must be rechecked on the single "
                "frame before it is used."
            ),
        },
        {
            "ProjectRef": "video 1 vs video 2 — same meter, two readings",
            "ProjectSays": "workspace.Stats contains HDEF.IntegrityVal, i.e. the shipped meter is H.D.E.F.",
            "VideoSays": "This video reads 'H.O.E.F INTEGRITY'; video 1 read 'H.D.E.F INTEGRITY'.",
            "At": "04:30",
            "Severity": "low",
            "Note": "The shipped place's own ValueObject decides it.",
            "Status": "resolved",
            "ResolvedBy": "AIRemake workspace.Stats.HDEF.IntegrityVal",
            "Outcome": "H.D.E.F is the installed name; H.O.E.F is an OCR misread or an older build.",
        },
    ],
    "ASR_Corrections": [],
    "Notes": [
        "This video has NO narration. The audio track is a loud, heavily clipped music bed (mean -10.6 dB, peak 0.0 dB, 289876 samples at 0 dB).",
        "Proof of no speech is not the volume and not the VAD: faster-whisper medium with VAD produced a single segment ('You', 8.98-10.98 s) and, with VAD DISABLED on a 120 s slice, produced 0 segments. Language detection returned 'nn' at p=0.52, the low-confidence junk guess typically produced on music.",
        "ASR_Corrections is therefore empty by observation, not by omission.",
        "Because there is no narration, every string in this file is 640x360 OCR and carries lower confidence than video 1 (which had narration to cross-check the picture). TotalSummary ranks video 1 above video 2 for this reason.",
        "Stream furniture was excluded from all lists: 'Atmosphere Vent Button', '50 subscribers' and 'cre: 100' appear in nearly every frame at a fixed position and are a subscriber-goal overlay; 'KELLY MURPHY' is a player nameplate.",
        "Subtitles in this video are burned into the picture, not a separate track, so the caption text is not independent evidence of what the game shows.",
    ],
    "Artifacts": [
        "frames/f001..f023.jpg (one per 15 s)",
        "frames/sheets/sheet_01..04.jpg (3x2 tile contact sheets)",
        "frames/sheets/doc_2x2.jpg (documentation-screen detail sheet)",
        "frames/key_01..05.jpg (1920x1080 lanczos key frames)",
        "frames/notice_9s.jpg, frames/crop_chat.png",
        "videoplayback.txt / .srt / .json (whisper output; effectively empty, see Notes)",
    ],
    "Provenance": [
        "Audio: faster-whisper 1.2.1, medium and small, CPU int8, run both with and without Silero VAD as a control.",
        "Picture: ffmpeg frame grab, 3x lanczos upscale, glm-4.5v vision sidecar in OCR mode.",
        "Rule applied throughout: a string read off a tiled sheet is rechecked on its single frame before use.",
    ],
}


def main() -> int:
    data = json.loads(DEST.read_text(encoding="utf-8"))

    raw_video = data.get("Video")
    if not isinstance(raw_video, dict):
        raise SystemExit("refusing to run: no Video block to preserve")

    # Rewrite the user's block verbatim, then append only keys that are absent,
    # so re-running this script cannot overwrite a value the user set by hand.
    merged_video = dict(raw_video)
    added = []
    for key, value in VIDEO_META.items():
        if key not in merged_video:
            merged_video[key] = value
            added.append(key)

    if "Content" in data:
        raise SystemExit("refusing to run: a Content block already exists; edit it by hand")

    data["Video"] = merged_video
    data["Content"] = CONTENT

    out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    DEST.write_bytes(out.encode("utf-8"))

    print(f"Video keys added: {added}")
    for key in ("Video", "Content"):
        print(f"  {key}: {', '.join(data[key].keys())}")
    for key, value in CONTENT.items():
        print(f"    Content.{key} -> {len(value) if isinstance(value, (list, dict)) else repr(value)[:40]}")
    print(f"written {len(out.encode('utf-8'))} bytes to {DEST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
