"""Verify that the Data/ mirrors are byte-identical to ServerStorage.Data.

The baseline numbers below were read from Studio with the *same* 32-bit fold the
checker uses, which is the whole point: comparing disk against a hash that disk
produced would be circular, and comparing by length alone is known to pass on
real corruption -- CLAUDE.md records two separate incidents where two files had
identical byte counts and different contents.

The fold is  h = (h * 31 + byte) mod 2**32, computed identically on both sides.
It is not crc32; it is what a Luau loop can compute without a library.

To re-establish the baseline after a deliberate edit, run this in Studio's Edit
datamodel and paste the output into BASELINE below:

    local d = game.ServerStorage.Data
    for _, n in ipairs({"DataCollection","Summary01","TRGWeb","BackendRewritePlan"}) do
        local t = d[n].Source
        local h = 0
        for k = 1, #t do h = (h * 31 + string.byte(t, k)) % 4294967296 end
        print(n, #t, string.format("%08x", h))
    end
    local t = d.DataCollection.Log.Source
    local h = 0
    for k = 1, #t do h = (h * 31 + string.byte(t, k)) % 4294967296 end
    print("DataCollection.Log", #t, string.format("%08x", h))

Run: python _tools/verify_data.py
"""

import sys
from pathlib import Path

DATA = Path("D:/rblxTRGproject/Data")

# (bytes, fold) as reported by Studio on 2026-09-26.
BASELINE = {
    "DataCollection.luau": (16817, 0x500548A2),
    "Summary01.luau": (6248, 0x7175E0E6),
    "TRGWeb.luau": (14810, 0x112021DC),
    "BackendRewritePlan.luau": (655, 0xDB409219),
    "DataCollection.Log": (602762, 0xD754A8E3),
}


def fold32(data: bytes) -> int:
    h = 0
    for byte in data:
        h = (h * 31 + byte) % 4294967296
    return h


def main() -> int:
    failures = 0
    for name, (want_bytes, want_fold) in BASELINE.items():
        path = DATA / name
        if not path.exists():
            print(f"MISSING  {name}")
            failures += 1
            continue

        raw = path.read_bytes()
        got_fold = fold32(raw)

        # Hash is the verdict; length is reported so a mismatch is readable.
        ok = got_fold == want_fold
        mark = "ok  " if ok else "FAIL"
        detail = "" if ok else f"   (want {want_bytes} {want_fold:08x})"
        print(f"{mark} {name:<26} {len(raw):>7} {got_fold:08x}{detail}")
        failures += 0 if ok else 1

    print()
    print("PASS" if not failures else f"FAIL ({failures} of {len(BASELINE)})")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
