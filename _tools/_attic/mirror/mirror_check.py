"""Canonical mirror checksum, for checking a disk doc against its Studio module.

The rule being enforced (project convention): a documentation ModuleScript's string
body, normalised by *stripping at most one trailing LF and appending exactly one*,
must be byte-identical to the disk file that mirrors it.

Definition -- the Luau side computes this identically:

    normalized = body, with at most one trailing LF removed, then one LF appended
    checksum   = "<len>|<sum>|<weighted>" over the BYTES of normalized
                   sum      = sum(byte)         mod 1000003
                   weighted = sum(i * byte)     mod 1000003      (i is 1-based)

Three numbers rather than one because the project has already lost a run to two
documents being the *same length* and different bytes. A length-only check passes
on that; the weighted sum is what catches it, since a byte that changes value
moves the weighted term by i*d, and a byte that only moves changes both sums.

Deliberately not a cryptographic hash: Luau has no sha library, so both sides must
be able to compute the same function. This is a drift detector and says so.

Usage:
    python _tools/mirror_check.py <file> [...]
    python _tools/mirror_check.py --selftest
"""

import sys
from pathlib import Path

MOD = 1000003


def canonical(data: bytes) -> bytes:
    """Normalise exactly the way the Luau side does."""
    if data.endswith(b"\n"):
        data = data[:-1]
    return data + b"\n"


def canonical_checksum(data: bytes) -> str:
    data = canonical(data)
    s = 0
    w = 0
    for i, byte in enumerate(data, start=1):
        s = (s + byte) % MOD
        w = (w + (i % MOD) * byte) % MOD
    return f"{len(data)}|{s}|{w}"


def selftest() -> int:
    """Prove the checksum detects the failure a length check misses.

    Not decoration: verify_docs for the GameCore documents shipped a length-only
    comparison and was green through a real one-character divergence. This asserts
    the property directly, so the tool cannot quietly stop having it.
    """
    a = b"hello world\n"
    b = b"hello worle\n"          # one byte different, same length
    assert len(a) == len(b)
    ca, cb = canonical_checksum(a), canonical_checksum(b)
    assert ca.split("|")[0] == cb.split("|")[0], "length must match for this to mean anything"
    assert ca != cb, "a same-length single-byte change MUST move the checksum"

    # Normalisation strips AT MOST ONE trailing LF, so it is a fixed point rather
    # than a collapse: b"x\n\n" is already canonical and must stay that way. The
    # first version of this assertion claimed the opposite and failed, which is
    # the assertion being wrong rather than the normaliser -- it is kept in this
    # corrected form because "strips at most one" is the whole reason a body that
    # genuinely ends in a blank line cannot be silently flattened into one that
    # does not.
    assert canonical(b"x") == b"x\n"
    assert canonical(b"x\n") == b"x\n"
    assert canonical(b"x\n\n") == b"x\n\n"
    assert canonical(canonical(a)) == canonical(a)

    print(f"selftest ok: same length {ca.split('|')[0]}, checksum {ca} -> {cb}")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    targets = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not targets:
        print(__doc__)
        return 2

    for arg in targets:
        p = Path(arg)
        raw = p.read_bytes()
        cr = raw.count(b"\r")
        note = f"  CR_BYTES={cr}" if cr else ""
        print(f"{canonical_checksum(raw)}  {p.name}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
