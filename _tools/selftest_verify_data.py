"""Prove verify_data.py can actually fail.

A checker that has only ever printed PASS is indistinguishable from a checker
that prints PASS unconditionally. CLAUDE.md records exactly this trap being
walked into twice (DECISIONS 95), so the verifier gets its own verifier.

The corruption is a single BYTE SUBSTITUTION, never an insertion or deletion.
That is deliberate: the byte count stays identical, so a length-only checker
would stay green here. This script demonstrates the difference rather than
asserting it.

The target file is restored from memory, so a failure mid-run cannot leave the
mirror damaged. Any exception in the restore path is re-raised after the
original bytes are written back.

Run: python _tools/selftest_verify_data.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path("D:/rblxTRGproject")
TARGET = ROOT / "Data" / "TRGWeb.luau"
CHECKER = ROOT / "_tools" / "verify_data.py"


def run_checker() -> int:
    proc = subprocess.run(
        [sys.executable, str(CHECKER)],
        capture_output=True,
        text=True,
    )
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    print(f"    rc={proc.returncode}  last line: {tail!r}")
    return proc.returncode


def main() -> int:
    if not TARGET.exists():
        print(f"cannot run: {TARGET} does not exist")
        return 2

    original = TARGET.read_bytes()
    print(f"selftest target: {TARGET}  ({len(original)} bytes)")

    print("\n[1/3] baseline")
    rc_before = run_checker()

    # Flip one byte to a value it certainly was not, keeping the length exact.
    mutated = bytearray(original)
    victim = len(mutated) // 2
    mutated[victim] = (mutated[victim] + 1) % 256
    if bytes(mutated) == original:  # cannot happen, but never assume
        print("mutation was a no-op; aborting")
        return 2
    TARGET.write_bytes(bytes(mutated))

    print(f"\n[2/3] after flipping byte {victim}: {original[victim]:02x} -> {mutated[victim]:02x} "
          f"(length unchanged at {len(mutated)})")
    try:
        rc_during = run_checker()
    finally:
        TARGET.write_bytes(original)

    print("\n[3/3] restored")
    rc_after = run_checker()

    print()
    print(f"rc sequence: {rc_before} -> {rc_during} -> {rc_after}")
    expected = (0, 1, 0)
    if (rc_before, rc_during, rc_after) == expected:
        print("SELFTEST PASS - the checker distinguishes corrupted from intact")
        return 0
    print(f"SELFTEST FAIL - expected {expected}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
