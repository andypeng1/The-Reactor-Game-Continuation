"""Prove that the transport probe's harness can FAIL, and for the right reason.

This file exists because the harness's FIRST version was green while the probe it
tested was wrong.  The probe handed every candidate `(url, body)` positionally;
the request family takes a request TABLE, so a real `syn.request` would have
raised and the probe would have reported a working transport as broken -- the
exact inversion of the question it was written to answer.  The harness missed it
because its stub accepted the string: `('http://..').Url` resolves to
`string.Url` = nil, so the stub recorded nothing and returned 200 anyway.

A stub that takes anything is not a test.  So every mutation below breaks the
shipped probe in a way that changes what it REPORTS, and the run must go red on
the check that guards that property -- not merely go red.  Each mutant is restored
from the bytes read at startup, so a crash cannot leave a mutated probe on disk.

    python _tools/selftest_transport_probe.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBE = ROOT / "transport_probe.luau"
TEST = ROOT / "transport_probe_test.lua"
LUA = r"D:\Lua\5.1\lua.exe"

# name, exact shipped text, replacement, the check that must be the one to go red,
# and why the mutation is the real bug and not a made-up one.
MUTATIONS = [
    (
        "the calling shape reverts to (url, body)",
        "local ok, res = pcall(send, {\n"
        "\t\tUrl = url, Method = 'POST', Body = body,\n"
        "\t\tHeaders = { ['Content-Type'] = 'text/plain' },\n"
        "\t})",
        "local ok, res = pcall(send, url, body)",
        "B every call to the transport is a request TABLE",
        "This is the bug the harness was written after. A positional call to "
        "syn.request raises, so every working transport reads as broken and the "
        "probe answers the opposite of what it was asked.",
    ),
    (
        "a non-2xx status counts as working",
        "\tif code < 200 or code > 299 then",
        "\tif false then",
        "C it is reported present and NOT working",
        "A transport that is present but refuses (a 500, or a blocked sink) would "
        "be named as the winner and the next run would be pointed at it.",
    ),
    (
        "a GET is allowed to win",
        "\tif works and winner == nil and kind == 'post' then winner = name end",
        "\tif works and winner == nil then winner = name end",
        "D and with no POST transport there is still no winner",
        "The sink writes nothing on a GET. Counting a reachable GET as a delivery "
        "channel is how 'the channel exists' gets mistaken for 'the bytes arrived'.",
    ),
    (
        "the failure reason is dropped",
        "\t\tlocal extra = res.Error or res.error or res.Body",
        "\t\tlocal extra = nil",
        "D and the raise is named rather than swallowed into \"status 0\"",
        "Without the reason the table says 'status 0' and the operator cannot tell "
        "a missing transport from a disabled HttpService -- which is the whole "
        "question this probe was injected to answer.",
    ),
]


def run(args):
    """rc, combined output. Never raises on a nonzero rc; that IS the datum."""
    p = subprocess.run(args, cwd=str(ROOT.parent), capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def fail_names(out):
    names = []
    for ln in out.splitlines():
        s = ln.strip()
        if s.startswith("FAIL "):
            names.append(s[5:].split("  -- ")[0].strip())
    return names


def main() -> int:
    original = PROBE.read_bytes()
    text = original.decode("utf-8")

    rc, out = run([LUA, str(TEST)])
    if rc != 0:
        print("the clean probe already fails; fix that before mutating anything")
        print(out)
        return 1
    print("baseline: rc=0, %s" % out.strip().splitlines()[-1])

    bad = 0
    try:
        for name, needle, replacement, want_fail, why in MUTATIONS:
            hits = text.count(needle)
            if hits != 1:
                print("SKIP %s -- the needle occurs %d times, expected 1" % (name, hits))
                print("     the probe moved; update this file rather than guessing")
                bad += 1
                continue

            PROBE.write_bytes(
                text.replace(needle, replacement, 1).encode("utf-8"))
            mrc, mout = run([LUA, str(TEST)])

            names = fail_names(mout)
            hit = any(want_fail in n for n in names)
            if mrc == 0:
                print("BAD  %s -- the suite stayed GREEN" % name)
                print("     %s" % why)
                bad += 1
            elif not hit:
                print("BAD  %s -- red, but not on %r" % (name, want_fail))
                for n in names:
                    print("     red: %s" % n)
                bad += 1
            else:
                print("OK   %s" % name)
                print("     caught by: %s" % want_fail)
                other = [n for n in names if want_fail not in n]
                if other:
                    print("     also red: %s" % "; ".join(other))
    finally:
        PROBE.write_bytes(original)

    rc, out = run([LUA, str(TEST)])
    if rc != 0:
        print("FAIL the probe did not come back clean after the mutations")
        print(out)
        return 1
    print("restored: rc=0, %s" % out.strip().splitlines()[-1])

    if bad:
        print("%d of %d mutations were not caught as specified" % (bad, len(MUTATIONS)))
        return 1
    print("all %d guards are load-bearing: breaking any one turns the harness red"
          " on the check that owns it" % len(MUTATIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
