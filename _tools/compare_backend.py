"""Diff a Studio-pulled source tree against the working tree, per file.

Phase 123 cost a whole Play session to a defect that was invisible from the disk
side: ten modules byte-identical, ONE of them (`Engine`) a version behind, and
the crash it caused landed in a different file (`Engine:273` reading a Config
field that had been retired). "I pushed it" is not falsifiable; a per-file
comparison is (DECISIONS_2 512). This is the standing half of that comparison --
the Studio half is the PostAsync loop in `docs/SNIPPETS.md` 5.31.

Usage:
    python _tools/compare_backend.py --pulled _tools/_pull/round124 \
                                     --disk src/ReactorBackend

Exit codes: 0 = every module identical, 1 = something differs or is missing.
A crash exits non-zero too, so a checker that died never looks like one that
passed (CLAUDE.md 0.6).

Comparison is by CONTENT HASH, never by length. Equal length with different
bytes is a thing that has actually happened here (CLAUDE.md 0.0).

The Studio instance name is the disk file's stem up to the first dot, so `X`
may be `X.luau` or `X.client.luau` / `X.server.luau` -- the suffix records run
context, and Lua itself assigns it no meaning. Two disk files can therefore
claim the same instance name (`VisualFeedback.luau` and
`VisualFeedback.client.luau` both do), so the mapping is resolved BY CONTENT:
the pulled bytes are equal to one candidate or they are not.
"""

import argparse
import hashlib
import sys
from pathlib import Path

# Files that live in this directory but are NOT instances of
# SSS.ReactorBackend, so their absence from a pull of that folder is correct
# rather than a finding. Listed explicitly because "on disk and never arrived"
# is exactly the signal this script exists to raise -- and a check that is
# always red is noise (CLAUDE.md 0.13).
#
# Both entries are LocalScripts deployed to StarterPlayer.StarterPlayerScripts,
# which is where they belong: they run on the client. Verified in the place
# 2026-10-13 by walking Game:GetDescendants -- VisualFeedback at 6510 B and
# EndShiftResume at 4245 B, each byte-equal to the disk file of the same name.
NOT_IN_FOLDER = {
    "VisualFeedback.client.luau":
        "the client reflector; deployed to StarterPlayer.StarterPlayerScripts",
    "EndShiftResume.client.luau":
        "the end-of-shift transport client; deployed to StarterPlayer.StarterPlayerScripts",
}

parser = argparse.ArgumentParser()
parser.add_argument("--pulled", required=True,
                    help="directory a Studio pull was written into")
parser.add_argument("--disk", default="src/ReactorBackend",
                    help="the working-tree directory to compare it against")
args = parser.parse_args()

PULLED = Path(args.pulled)
DISK = Path(args.disk)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def disk_candidates(name: str):
    """Every disk file whose Studio instance name could be `name`."""
    return sorted(set(DISK.glob(f"{name}.luau")) | set(DISK.glob(f"{name}.*.luau")))


pulled = sorted(p for p in PULLED.glob("*.luau"))
if not pulled:
    print(f"no .luau files in {PULLED} -- was the pull run?")
    sys.exit(1)

same, diff, unmatched = [], [], []
covered = set()
for src in pulled:
    candidates = disk_candidates(src.stem)
    if not candidates:
        unmatched.append(f"{src.name}: no disk file with that instance name")
        continue
    here = digest(src)
    hits = [c for c in candidates if digest(c) == here]
    if len(hits) == 1:
        same.append(hits[0].name)
        covered.add(hits[0].name)
        continue
    # Either every candidate differs (a real mismatch) or several are identical
    # to each other as well as to the pull (harmless). Both are reported the
    # same way: we could not pin it to ONE file, and saying which one is stale
    # is the whole point, so guessing would defeat the check.
    diff.append(f"{src.name}: matches {len(hits)} of {len(candidates)} candidates ("
                + ", ".join(f"{c.name}={c.stat().st_size}" for c in candidates) + ")")
    covered.update(c.name for c in candidates)

# A module that exists on disk and never arrived from Studio is the other half
# of the Phase 123 defect: it would mean the file is on disk but not in the place.
missing = sorted(p.name for p in DISK.glob("*.luau")
                 if p.name not in covered and p.name not in NOT_IN_FOLDER)

for name in same:
    print(f"SAME   {name}")
for line in diff:
    print(f"DIFF   {line}")
for line in unmatched:
    print(f"???    {line}")
for name in missing:
    print(f"ABSENT {name}: on disk, not in the pull")

print(f"\n{len(same)} same, {len(diff)} different, {len(unmatched)} unmatched, {len(missing)} absent")
sys.exit(1 if (diff or unmatched or missing) else 0)
