"""Rewrite the Conflicts block of the first video's Information.json.

Why: the original Conflicts entries were written before DataCollection was read,
so they could only say "the docs and the video disagree". DataCollection is the
script the game's own author wired to the live game, and it carries the real
constants plus the real instance paths. That turns four open disagreements into
adjudicated ones -- and two of them flip the conclusion I first reported.

The four existing entries keep their original quoted text verbatim: those fields
quote the project and the video, and retyping a quote is how a quote stops being
one. Only adjudication keys are appended.

Rule applied throughout: the shipped game outranks the video's narration, and
the video's narration outranks TRGWeb, which is a legacy HTML prototype that is
stale in at least three places.

Run: python _tools/patch_information.py
"""

import json
from pathlib import Path

DEST = Path("D:/rblxTRGproject/Videos/The Reactor – Complete Beginners Guide/Information.json")

# Keyed by the At/ProjectRef pair of the entry being adjudicated, so the original
# text is never touched.
VERDICTS = [
    {
        "Status": "resolved — the video is right; the docs under-describe",
        "ResolvedBy": "DataCollection (ServerStorage.Data telemetry script) and DataCollection.Log instance paths",
        "Outcome": (
            "The shipped game really does have more control surface than the docs' list of three. The log's "
            "own path list contains game.Workspace.Consoles.{MainReactorConsole, ThermalConsole, CBLaserConsole, "
            "HDEFGenerator, ALTReactorConsole, ElectricGridConsole} and game.Workspace.CFLever1..6 (six "
            "chamber-fan levers). CLAUDE.md 1.2's 'three control methods' is an abstraction of the three core "
            "LOOPS (pressure / CBL / coolant), not an inventory of the control SURFACE. No gameplay defect — "
            "but the docs should say so explicitly."
        ),
    },
    {
        "Status": "not a conflict — two independent axes, both real",
        "ResolvedBy": "DataCollection WIKI block and DataCollection.Log instance paths",
        "Outcome": (
            "DataCollection declares CBL_LEVELS = 5, CBL_PER_LEVEL = 0.25, CBL_MAX_POWER = 1.25, and the log "
            "names CBL1Systems / CBL2Systems / CBL3Systems each with a PressureButton, alongside PW1..5ClickPart "
            "(five power clickers). So there are THREE CBL systems, each set to one of FIVE levels. The project's "
            "'PW1..PW5' is the level axis; the video's 'three levers' is the system axis. Both are correct and "
            "neither contradicts the other. The original entry's premise — 'needs resolution against TRGWeb, "
            "which is the authority' — was also wrong about the authority: TRGWeb is the stale prototype."
        ),
    },
    {
        "Status": "compatible",
        "ResolvedBy": "DataCollection.Log payload",
        "Outcome": (
            "The log's payload.coolant.levels is a 3-element array, confirming three pumps. The per-pump off "
            "button the video shows is not contradicted anywhere."
        ),
    },
    {
        "Status": "resolved — all four devices exist; the video just reads the on-screen labels",
        "ResolvedBy": "DataCollection instance path list",
        "Outcome": (
            "The log names AtmosphereVentButton (AVB), E_VENTLever1..3 (the three emergency vents) and "
            "CFLever1..6 (the six chamber fans). The video's 'six chamber fans' are the docs' fans, and its "
            "'pressure purge' button is the docs' AVB — the video reads in-game button text, the docs use "
            "engineering abbreviations, and neither invents a device. The purge-to-stall mechanism is real "
            "gameplay behaviour that the docs do not describe; that gap is genuine."
        ),
    },
]

NEW_ENTRIES = [
    {
        "ProjectRef": "TRGWeb (ServerStorage.Data.TRGWeb) vs the shipped game",
        "ProjectSays": "TRGWeb uses core-state thresholds of <6000 / >=6000 / >17500 / >29500, a stall below 2000, and a stall psi below 2250.",
        "VideoSays": "5600 F top of stage 0; 17500 F top of stage 1; 'around 17000' bottom of stage 2; 29000 F top of stage 2; 39000 F top of stage 3; stall below 2200 psi.",
        "At": "03:17-04:20",
        "Severity": "high",
        "Note": "Corrects an earlier entry in this file, which asserted that the video's 5600 and 2200 were wrong and that TRGWeb's 6000 and 2250 were authoritative. That was backwards.",
        "Status": "resolved — the video is right, TRGWeb is the outlier",
        "ResolvedBy": "DataCollection WIKI block, which is wired to the live game",
        "Outcome": (
            "DataCollection declares CORE_STATE_THRESHOLDS = {5600, 17500, 29500, 39000} and AVB_STALLOUT_PSI "
            "= 2200. The video's 5600 and 2200 match the shipped game exactly; TRGWeb's 6000 and 2250 are stale. "
            "The video's spoken '17000' and '29000' are loose narration of 17500 and 29500. Both of these are "
            "core-loop constants, so TRGWeb must not be treated as the authority for numbers."
        ),
    },
    {
        "ProjectRef": "internal to DataCollection",
        "ProjectSays": "DataCollection declares MELTDOWN_TEMP_F = 38000 but also CORE_STATE_THRESHOLDS = {..., 39000} and METU_FIRE_TEMP_F = 39000.",
        "VideoSays": "Stage 4 above 39000 F is meltdown.",
        "At": "03:30",
        "Severity": "low",
        "Note": "Open. The shipped script contradicts itself by 1000 F about which temperature destroys the reactor.",
        "Status": "unresolved — one live measurement would settle it",
        "ResolvedBy": None,
        "Outcome": (
            "Either the 38000 constant is unused, or CORE_STATE_THRESHOLDS' last entry is the top of stage 3 "
            "rather than the meltdown line. The video sides with 39000. Not enough evidence yet; flagged rather "
            "than guessed."
        ),
    },
]

# Only the numbers the shipped game confirms outright get annotated. The rest of
# Numbers stays as the video's literal claims, because that is what that block is
# for: what the video says, not what is true.
CORROBORATED = {
    "5600 F": "DataCollection CORE_STATE_THRESHOLDS[1] == 5600. The shipped game agrees with the video; TRGWeb's 6000 is stale.",
    "17500 F": "DataCollection CORE_STATE_THRESHOLDS[2] == 17500.",
    "39000 F": "DataCollection CORE_STATE_THRESHOLDS[4] == 39000 and METU_FIRE_TEMP_F == 39000 — but see MELTDOWN_TEMP_F = 38000 in Conflicts.",
    "2200 psi": "DataCollection AVB_STALLOUT_PSI == 2200. The shipped game agrees with the video; TRGWeb's 2250 is stale.",
}

data = json.loads(DEST.read_text(encoding="utf-8"))
content = data["Content"]

if len(content["Conflicts"]) != len(VERDICTS):
    raise SystemExit(
        f"expected {len(VERDICTS)} existing Conflicts entries, found {len(content['Conflicts'])}; "
        "refusing to guess which verdict belongs to which entry"
    )

for entry, verdict in zip(content["Conflicts"], VERDICTS):
    entry.update(verdict)

content["Conflicts"].extend(NEW_ENTRIES)

for entry in content["Numbers"]:
    note = CORROBORATED.get(entry.get("Value"))
    if note:
        entry["Corroboration"] = note

content["Notes"].append(
    "Adjudication rule for this file: the SHIPPED GAME outranks the video's narration, and the video's "
    "narration outranks TRGWeb. DataCollection (ServerStorage.Data) is a telemetry script wired to the live "
    "game, so its constants and its instance paths are first-hand evidence; TRGWeb is a legacy HTML prototype "
    "that is stale in at least three places. An earlier draft of this file inverted that order and reported "
    "the video's 5600 F and 2200 psi as errors, which was wrong. See Conflicts for the corrected entries."
)

# Write bytes, not text: on Windows text mode would turn every \n into \r\n, and
# the file has to round-trip byte-for-byte through other readers.
out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
DEST.write_bytes(out.encode("utf-8"))

print(f"Conflicts entries: 4 -> {len(content['Conflicts'])}")
print(f"Numbers entries carrying a Corroboration: {sum(1 for e in content['Numbers'] if 'Corroboration' in e)}")
print(f"Notes entries: {len(content['Notes'])}")
print(f"written {len(out.encode('utf-8'))} bytes to {DEST}")
