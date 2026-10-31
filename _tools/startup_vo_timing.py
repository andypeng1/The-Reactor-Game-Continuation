#!/usr/bin/env python
"""startup_vo_timing.py -- the startup voice-over's timecodes, derived from Config.

    python -X utf8 _tools/startup_vo_timing.py              # print the table
    python -X utf8 _tools/startup_vo_timing.py --check docs/VO_STARTUP.md

WHY THIS EXISTS.  `docs/VO_STARTUP.md` is a script somebody reads into a
microphone, and every one of its 16 timecodes is a number that a hand-copied
table can get wrong without anything turning red.  The startup chain lives in
`src/ReactorBackend/Config.luau` as `Shift.StartupSteps: {hold, kind, text}`;
`Engine:AdvanceStartup` logs step N when the accumulated dwell reaches the sum
of holds 1..N.  So the time of line N is `sum(hold[1..N])` -- arithmetic over
one table, and this file is that arithmetic, once.

The check compares the fenced block in the doc against what this file computes
and exits 1 on any difference.  It is a DRIFT check, not a measurement: it can
tell you the doc stopped matching Config, and it cannot tell you Config is
right.  What backs Config is five captures and their median (PROGRESS.md Phase
65) -- a reading, quoted in the doc, not reproducible from here.

WHAT IS AN ESTIMATE.  `est` is words / WPS.  WPS is an ASSUMPTION about reading
speed, not a measurement of anything in this repo: nothing has been recorded,
so the column says what a calm PA read would take, and it is marked as an
estimate everywhere it appears.  The `win` column is real (the next line's hold)
and the honest answer at three places is 0.0 -- see the doc.
"""

import os
import re
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "src", "ReactorBackend", "Config.luau")

WPS = 2.5            # words per second, a calm PA read.  AN ASSUMPTION.
BEGIN = "<!-- VO-TIMELINE:BEGIN -->"
END = "<!-- VO-TIMELINE:END -->"

ENTRY = re.compile(r"\{hold=([0-9.]+),\s*kind='([A-Z]+)',\s*text='([^']*)'\}")
TAG = re.compile(r"</?b>")
PREFIX = re.compile(r"^\[(?:ALERT|WARN|INFO)\]\s*-\s*")


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def parse_steps():
    """The StartupSteps table, in source order.  Fails loudly on anything else."""
    src = read_text(CONFIG)
    head = src.index("StartupSteps = {")
    tail = src.index("\n        },", head)
    body = src[head:tail]
    steps = []
    for m in ENTRY.finditer(body):
        steps.append({
            "hold": float(m.group(1)),
            "kind": m.group(2),
            "text": m.group(3),
        })
    if not steps:
        raise RuntimeError("no StartupSteps entries matched in %s" % CONFIG)
    # 16 is the measured trunk (PROGRESS.md Phase 65).  A different number means
    # the table changed shape, and the doc's rows are stale in a way the block
    # comparison would report as 16 diffs instead of one sentence.
    if len(steps) != 16:
        raise RuntimeError("expected 16 StartupSteps, parsed %d -- the chain "
                           "changed shape; re-read PROGRESS.md Phase 65 before "
                           "trusting any timecode" % len(steps))
    return steps


def spoken(text):
    """The line as a mouth says it: no rich-text markup, no severity tag."""
    s = TAG.sub("", text)
    s = PREFIX.sub("", s)
    return s.strip()


def timeline():
    steps = parse_steps()
    rows, t = [], 0.0
    for i, st in enumerate(steps):
        t += st["hold"]
        nxt = steps[i + 1] if i + 1 < len(steps) else None
        line = spoken(st["text"])
        words = len(line.split())
        rows.append({
            "n": i + 1,
            "t": t,
            "win": (nxt["hold"] if nxt else None),
            "kind": st["kind"],
            "words": words,
            "est": words / WPS,
            "line": line,
        })
    return rows


def groups(rows):
    """Rows that land on the same tick, with the air that follows the group.

    Three places in this chain write two or three lines in a single tick.  That
    is not a reading of how they were spoken -- the panel is a ticker, and the
    original may have written them all at once.  It matters here because a
    voice artist reading them as three separate beats is inventing something
    the machine never did; the useful shape is 'one burst, then a long tail',
    and each of the three groups does have a long tail."""
    out, cur = [], None
    for r in rows:
        if cur is None or abs(r["t"] - cur["t"]) > 1e-9:
            cur = {"t": r["t"], "lines": [], "est": 0.0}
            out.append(cur)
        cur["lines"].append(r["n"])
        cur["est"] += r["est"]
        cur["tail"] = r["win"]
    return [g for g in out if len(g["lines"]) > 1]


def render(rows):
    out = [BEGIN,
           "| # | t (s) | window (s) | kind | words | est. read (s) | spoken line |",
           "|---:|---:|---:|---|---:|---:|---|"]
    for r in rows:
        win = "--" if r["win"] is None else "%.1f" % r["win"]
        out.append("| %d | %.1f | %s | %s | %d | %.1f | %s |"
                   % (r["n"], r["t"], win, r["kind"], r["words"], r["est"], r["line"]))
    out.append("")
    out.append("Same-tick bursts (the order inside a burst is not in the captures -- see PROGRESS.md 65.2):")
    out.append("")
    out.append("| burst | t (s) | est. read (s) | air after (s) |")
    out.append("|---|---:|---:|---:|")
    for g in groups(rows):
        tail = "--" if g["tail"] is None else "%.1f" % g["tail"]
        out.append("| %s | %.1f | %.1f | %s |"
                   % ("+".join(str(n) for n in g["lines"]), g["t"], g["est"], tail))
    out.append(END)
    return out


def check(path):
    want = render(timeline())
    doc = read_text(path)
    if BEGIN not in doc or END not in doc:
        print("FAIL: %s has no %s / %s markers" % (path, BEGIN, END))
        return 1
    have = doc[doc.index(BEGIN):doc.index(END) + len(END)].splitlines()
    if have == want:
        print("OK: %d lines, doc block matches Config.Shift.StartupSteps" % (len(want) - 3))
        return 0
    print("FAIL: %s no longer matches %s" % (path, CONFIG))
    for i in range(max(len(have), len(want))):
        a = have[i] if i < len(have) else "<missing>"
        b = want[i] if i < len(want) else "<missing>"
        if a != b:
            print("  line %d" % (i + 1))
            print("    doc:    %s" % a)
            print("    config: %s" % b)
    return 1


def main(argv):
    if "--check" in argv:
        i = argv.index("--check")
        if i + 1 >= len(argv):
            print("usage: startup_vo_timing.py --check <doc.md>")
            return 2
        return check(argv[i + 1])
    rows = timeline()
    for line in render(rows):
        print(line)
    total = rows[-1]["t"] if rows else 0.0
    speech = sum(r["est"] for r in rows)
    print()
    print("%d lines, chain ends at %.1f s; estimated speech %.1f s (%.0f%% of the chain)"
          % (len(rows), total, speech, 100.0 * speech / total if total else 0.0))
    print("est uses %.1f words/s -- an ASSUMPTION, nothing in this repo has been recorded" % WPS)
    return 0


if __name__ == "__main__":
    # CLAUDE.md 0.6: Blender taught us that an uncaught exception and a clean
    # run are byte-identical at the shell.  The same guard is right here.
    try:
        code = main(sys.argv[1:])
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        traceback.print_exc()
        print("CRASHED -- this is a failure, not a pass")
        sys.exit(1)
    sys.exit(code)
