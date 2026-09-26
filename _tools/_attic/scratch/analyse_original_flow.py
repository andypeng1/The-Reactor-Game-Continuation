"""Read a recording produced by _tools/TRG_original_recorder.luau.

Why a file and not a heredoc: the numbers this prints get quoted back to the
user and into the docs, and a number nobody can re-derive is how a wrong one
gets shipped. Run it and the figures come back.

    python _tools/analyse_original_flow.py Data/flow/original_<stamp>
    python _tools/analyse_original_flow.py <run> --every 20
    python _tools/analyse_original_flow.py <run> --window 900 1000
    python _tools/analyse_original_flow.py <run> --key m.temp --key c.fanCount

The recorder writes ONLY changes -- that is its entire point -- so a raw line
dump is unreadable: most lines carry one or two keys and every other key on the
line is stale. So this carries the last known value forward per key and prints a
regular grid, which is the only way the shape of a run is visible without
plotting it.

Two things it deliberately does NOT do:

  * It does not treat a missing key as zero. `-` means the recorder has never
    reported that key. In this game an unreadable sensor is a state of its own
    (the recorder emits x.<key> = ERR for exactly that), so folding the absence
    into 0 would erase the distinction the recorder was built to preserve.

  * It does not compute a steady-state metric over the whole run. The run
    contains a controlled shutdown, so any average over it spans the transition
    and describes nothing -- the same mistake the sibling analyse_flow.py
    documents having made with the max-min span.
"""

import argparse
import collections
import re
from pathlib import Path


LINE_S = re.compile(r"^([SB]) (\d+) t=([\d.]+) dt=(\d+)(?: (.*))?$")
LINE_EVT = re.compile(r"^EVT(\d+) (\S+)(?: (.*))?$")
# PHASE is the one event kind with its own line prefix rather than an EVT<n>
# tag, because the flow boundary is meant to be greppable on its own. A parser
# that only knows EVT<n> silently drops every phase transition -- which is
# exactly the line a reader most needs, so it is matched explicitly here.
LINE_PHASE = re.compile(r"^PHASE(\d+) (\S+)(?: (.*))?$")
LINE_HDR = re.compile(r"^#")


def parse(path):
    """One pass. Returns (header lines, samples, events)."""
    header, samples, events = [], [], []
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for raw in text.split("\n"):
        if not raw:
            continue
        if LINE_HDR.match(raw):
            header.append(raw)
            continue
        m = LINE_S.match(raw)
        if m:
            kind, sid, t, dt, body = m.groups()
            kv = {}
            for tok in (body or "").split():
                k, _, v = tok.partition("=")
                if k:
                    kv[k] = v
            samples.append((kind, int(sid), float(t), int(dt), kv))
            continue
        m = LINE_PHASE.match(raw)
        if m:
            n, name, detail = m.groups()
            events.append((0, "PHASE", {"name": name}, "PHASE%s %s %s" % (n, name, detail or "")))
            continue
        m = LINE_EVT.match(raw)
        if m:
            eid, kind, detail = m.groups()
            ev = {}
            for tok in (detail or "").split():
                k, sep, v = tok.partition("=")
                if not k:
                    continue
                if sep:
                    ev[k] = v
                else:
                    # A bare token is how the recorder writes a click it CAN
                    # name: `EVT78 CLICK AVB`, not `label=AVB`. Dropping
                    # non-k=v tokens silently files every named click under
                    # "no path" and reports the name table as 100% missing --
                    # which is exactly the opposite of what the data says.
                    ev.setdefault("_bare", []).append(k)
            events.append((int(eid), kind, ev, detail or ""))
            continue
        if raw.startswith("## RECEIPT"):
            events.append((0, "RECEIPT", dict(re.findall(r"(\w+)=(\S+)", raw)), raw))
    return header, samples, events


def click_census(events):
    """Count clicks by resolved label, and by path where no label resolved.

    Both halves matter and neither is optional: a label means the recorder's
    name table knows this control, and an unlabeled path means it does not --
    which is the to-do list for the table, not a gap in the data. The path is
    still exact, so no click is lost; only its friendly name is.
    """
    named, unnamed = collections.Counter(), collections.Counter()
    for _, kind, ev, _ in events:
        if kind != "CLICK":
            continue
        if "_bare" in ev:
            for b in ev["_bare"]:
                named[b] += 1
        elif "label" in ev:
            named[ev["label"]] += 1
        elif "path" in ev:
            unnamed[ev["path"]] += 1
        else:
            named["<no name, no path>"] += 1
    return named, unnamed


def phases(events):
    """The flow state machine's own boundaries, with the elapsed time."""
    out = []
    for _, kind, ev, detail in events:
        if kind == "PHASE":
            out.append(detail)
        elif kind == "SEAL":
            out.append("SEAL " + detail)
    return out


def sample_state(samples):
    """Carry-forward table: sample id -> (t, merged key/value dict)."""
    state, out = {}, []
    for kind, sid, t, dt, kv in samples:
        state.update(kv)
        out.append((sid, t, dict(state)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--every", type=int, default=0,
                    help="print a grid row every N polled samples (default: 40)")
    ap.add_argument("--window", type=int, nargs=2, metavar=("FROM", "TO"),
                    help="print EVERY reported sample whose id is in this range")
    ap.add_argument("--key", action="append", default=[],
                    help="extra key to show in the grid (repeatable)")
    args = ap.parse_args()

    header, samples, events = parse(args.path)
    if not samples:
        print("no sample lines in %s -- is this a recorder output?" % args.path)
        return 1
    states = sample_state(samples)
    last = states[-1][2]

    print("=== file ===")
    for h in header:
        print("  " + h)
    print("  polls reported: %d   first t=%.1f  last t=%.1f"
          % (len(samples), samples[0][2], samples[-1][2]))

    print()
    print("=== flow boundaries ===")
    for p in phases(events):
        print("  " + p)

    print()
    named, unnamed = click_census(events)
    print("=== clicks: %d named, %d unnamed (the name table's gap) ==="
          % (sum(named.values()), sum(unnamed.values())))
    for k, v in named.most_common(20):
        print("   %-30s %d" % (k, v))
    if unnamed:
        print("   -- unnamed, by exact path --")
        for k, v in unnamed.most_common(30):
            print("   %-58s %d" % (k.replace("Workspace.Consoles.", ""), v))
        if len(unnamed) > 30:
            print("   ... %d distinct paths total" % len(unnamed))

    print()
    print("=== keys the recorder ever reported (%d) ===" % len(last))
    spans = collections.Counter()
    for _, _, st in states:
        for k in st:
            spans[k] += 1
    for k, v in sorted(spans.items(), key=lambda x: -x[1]):
        print("   %-24s %5d samples   last=%s" % (k, v, last.get(k, "-")))

    # ---- grid ----
    # The state flags belong in the default grid, not behind --key: a run can
    # end in a meltdown rather than a shutdown, and a reader who cannot see
    # s.MainframeMeltdown flip has no way to tell those two endings apart.
    grid_cols = ["m.temp", "m.press", "m.fluct",
                 "s.Core.PressureVal", "s.Core.RadiationVal",
                 "s.Core.OutputVal", "s.HDEF.IntegrityVal",
                 "c.fanCount", "c.cbl1Pct", "c.coolSum",
                 "s.MainframeMeltdown", "s.GameActive", "s.ActiveQPUs"]
    for k in args.key:
        if k not in grid_cols:
            grid_cols.append(k)
    every = args.every or 40
    print()
    print("=== grid, one row per ~%d reported samples (carry-forward) ===" % every)
    print("   %7s %8s  %s" % ("sample", "t", "  ".join("%-13s" % c for c in grid_cols)))
    for i, (sid, t, st) in enumerate(states):
        if i % every:
            continue
        print("   %7d %8.1f  %s" % (sid, t, "  ".join("%-13s" % st.get(c, "-") for c in grid_cols)))

    # ---- window ----
    if args.window:
        lo, hi = args.window
        print()
        print("=== every reported sample with id in [%d, %d] ===" % (lo, hi))
        print("   %7s %8s %6s  %s" % ("sample", "t", "dt", "changes"))
        for kind, sid, t, dt, kv in samples:
            if lo <= sid <= hi:
                body = " ".join("%s=%s" % (k, v) for k, v in sorted(kv.items()))
                print("   %7d %8.2f %6d %s %s" % (sid, t, dt, kind, body))
        # Event ids that fall in the same window, by sample position.
        print("   -- events between those samples --")
        idx = {}
        for i, (kind, sid, t, dt, kv) in enumerate(samples):
            idx[i] = sid
        prev = 0
        for eid, kind, ev, detail in events:
            if kind == "RECEIPT":
                continue
            print("   EVT%-5d %-9s %s" % (eid, kind, detail[:110]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
