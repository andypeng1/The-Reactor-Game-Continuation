"""Verify a recording produced by _tools/TRG_original_recorder.luau.

Why this exists: the recorder streams its output to the localhost sink in
numbered POST segments, and the receiver appends them to one file. Nothing in
that path guarantees the file equals what the script produced -- a dropped
segment, a doubled retry, or a truncated POST all still produce a plausible
looking file. So the recorder keeps a djb2 hash of every byte it emits, as it
emits it, and writes that hash into its final RECEIPT line. This script
recomputes the same hash over the bytes on disk and compares.

That comparison is the whole point: the hash is computed incrementally on the
producer side (segment by segment, as bytes are handed to the sink) and in one
pass here. If they agree, no byte was lost, duplicated or reordered anywhere in
between -- which a length check cannot show, and which this project has already
been burned by twice.

Usage:
    python _tools/verify_original_flow.py Data/flow/original_<stamp>

Exit code 0 = the file is self-consistent. 1 = it is not, and the reason is
printed. Run it on any recording before trusting a number taken from it.
"""

import collections
import re
import sys
from pathlib import Path


def djb2(b: bytes) -> int:
    h = 5381
    for c in b:
        h = (h * 33 + c) % 4294967296
    return h


def verify(path: str) -> int:
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8", errors="replace")
    problems = []

    # ---- receipt ----
    m = re.search(r"^## RECEIPT (.*)$", text, re.M)
    if not m:
        print("FAIL no RECEIPT line: the recording was never sealed")
        return 1
    if not text.endswith("\n"):
        problems.append("file does not end with a newline")
    receipt = m.group(1)
    if text.rstrip("\n").split("\n")[-1][:2] != "##":
        problems.append("RECEIPT is not the last line")

    fields = dict(re.findall(r"(\w+)=(\S+)", receipt))
    claimed = int(fields.get("hash", "0"), 16)

    # The receipt states its own coverage (`over=`), and the hash covers the
    # bytes ABOVE the receipt line and none of the receipt itself. Comparing a
    # whole-file hash against a hash taken before the last line never matches,
    # and the mismatch is indistinguishable from corruption -- so the boundary
    # is asserted here rather than assumed.
    over = int(fields.get("over", "0"))
    if over != m.start():
        problems.append(
            "receipt says the hash covers %d bytes but the receipt line starts "
            "at byte %d -- the file has bytes the hash does not describe"
            % (over, m.start())
        )
    actual = djb2(raw[:over])
    if claimed != actual:
        problems.append(
            "HASH MISMATCH: receipt says %08x over %d bytes, disk is %08x "
            "-- bytes were lost, duplicated or reordered in transit"
            % (claimed, over, actual)
        )

    # ---- EVT ids: completeness and ORDER are different claims ----
    # A dropped byte severs a line and loses an id; a doubled segment repeats
    # one; two POSTs in flight can land in either order and swap two ids while
    # losing nothing at all. Three different defects with three different
    # consequences -- and the first version of this file reported all three as
    # "ids not consecutive", which on 2026-09-26 filed a real transposition
    # under the loss case it does not resemble. Classified instead.
    ids = [int(i) for i in re.findall(r"^EVT(\d+) ", text, re.M)]
    missing = sorted(set(range(1, max(ids) + 1)) - set(ids)) if ids else []
    doubled = sorted(k for k, v in collections.Counter(ids).items() if v > 1)
    swapped = [(a, b) for a, b in zip(ids, ids[1:]) if b < a]
    if ids and ids[0] != 1:
        problems.append("EVT ids start at %d, not 1" % ids[0])
    if missing:
        problems.append("EVT ids missing (%d): %r -- bytes were LOST"
                        % (len(missing), missing[:5]))
    if doubled:
        problems.append("EVT ids repeated (%d): %r -- a segment was appended twice"
                        % (len(doubled), doubled[:5]))
    if swapped:
        problems.append("EVT ids out of order (%d pair(s)): %r -- every byte is "
                        "present, they arrived in the wrong sequence"
                        % (len(swapped), swapped[:5]))
    if ids and str(len(ids)) != fields.get("events"):
        problems.append("receipt events=%s but %d EVT lines found"
                        % (fields.get("events"), len(ids)))

    # ---- sample ids: non-decreasing, gappy by design ----
    # Gappy is the point (a poll with no change emits no line). Two things are
    # legal and both look like a repeat: one poll's change set is SPLIT across
    # lines by MaxPairsPerLine and every continuation line repeats the same
    # `S <id>` head, and the opening baseline is emitted as `B <id>`. So the
    # unit is the head, and a repeat is legal only when the head is identical --
    # which is what `density` counts. Demanding that the raw id list be strictly
    # increasing, as this file first did, fails every recording whose first poll
    # changes more than 240 keys: measured 2026-09-26, original_260926-155619
    # reported "1 then 1" and those two lines were one baseline split in two.
    heads = []
    for pre, sid in re.findall(r"^([BS]) (\d+) ", text, re.M):
        if not heads or heads[-1] != (pre, int(sid)):
            heads.append((pre, int(sid)))
    for (pa, a), (pb, b) in zip(heads, heads[1:]):
        if b < a:
            problems.append("sample ids went backwards: %s %d then %s %d"
                            % (pa, a, pb, b))
            break
        if b == a and pa != pb:
            problems.append("sample id %d appears under both B and S" % a)
            break

    # ---- phase ids ----
    ph = [int(i) for i in re.findall(r"^PHASE(\d+) ", text, re.M)]
    for a, b in zip(ph, ph[1:]):
        if b != a + 1:
            problems.append("PHASE ids not consecutive")
            break

    # ---- counters ----
    for key in ("dropped", "spilled", "postfails"):
        v = int(fields.get(key, "0") or 0)
        if v:
            problems.append("receipt reports %s=%d -- not all data was delivered"
                            % (key, v))

    kinds = {}
    for k in re.findall(r"^EVT\d+ (\S+)", text, re.M):
        kinds[k] = kinds.get(k, 0) + 1

    # ---- report ----
    print("file        %s" % path)
    print("bytes       %d" % len(raw))
    print("lines       %d" % text.count("\n"))
    print("samples     %s polled, %d reported (B baseline + S change batches)"
          % (fields.get("samples", "?"), len(heads)))
    print("events      %d  %s" % (len(ids), kinds))
    print("id audit    missing=%d repeated=%d out-of-order=%d"
          % (len(missing), len(doubled), len(swapped)))
    print("phases      %s" % re.findall(r"^PHASE\d+ (\S+)", text, re.M))
    print("segments    %s" % fields.get("segments"))
    print("transport   n/a (sink chosen at runtime)")
    print("hash        receipt %08x  disk %08x  %s"
          % (claimed, actual, "MATCH" if claimed == actual else "MISMATCH"))

    # Counted by HEAD, not by line: a batch split across continuation lines is
    # one batch, and counting its lines inflates the density it is meant to
    # measure -- the same mistake as calling a whole-file line count poll
    # matched, which this project has already made once in a print statement.
    batches = sum(1 for pre, _ in heads if pre == "S")
    polls = int(fields.get("samples", "0") or 0)
    if batches:
        print("density     %d change batches over %d polls (%.3f per poll)"
              % (batches, polls, batches / max(1, polls)))

    if problems:
        print()
        for p in problems:
            print("FAIL " + p)
        return 1
    print()
    print("OK  self-consistent: no byte lost, no id skipped, nothing dropped")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(verify(sys.argv[1]))
