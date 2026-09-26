"""Compare reactor_flow runs collected by MCP_FlowCollector.

Why a file and not a heredoc: the numbers this prints are quoted in the comments of
MCP_FlowCollector.luau and _flow_sim.py, and a number nobody can re-derive is how a
wrong one gets shipped. Run it and the quoted figures come back.

    python _tools/analyse_flow.py Data/flow/reactor_flow Data/flow/<another>

Each argument is one run; the first is the reference the others are diffed against.

The steady-state metric is mean |dTemp| per tick over every tick where the core is
above 19000, pooled across all three shifts. It deliberately is NOT the max-min
span: the span is ~4300 for every controller ever tried, because it is dominated by
the DESIGNED setpoint moves (20000 -> 16000 at endgame, 15500 in the equinox). The
span gave a bad controller a clean bill of health once; the per-tick mean did not.

The EVT ids are used as the seam oracle. They are monotonic and gap-free within a
run, so a dropped byte (which would sever a line and lose an id) or a duplicated
segment boundary (which would repeat one) shows up as a non-consecutive step --
which is a stronger check than comparing lengths, because the five segments are
concatenated by the file system and a length check cannot see a seam at all.
"""

import re
import sys
from pathlib import Path


def analyse(path):
    txt = Path(path).read_text()
    ticks = len(re.findall(r"^T\d+", txt, re.M))

    ids = [int(i) for i in re.findall(r"^EVT\s+(\d+)", txt, re.M)]
    seams = sum(1 for a, b in zip(ids, ids[1:]) if b != a + 1)

    kinds = {}
    for m in re.finditer(r"^EVT\s+\d+\s+(\S+)", txt, re.M):
        kinds[m.group(1)] = kinds.get(m.group(1), 0) + 1

    cmds = {}
    for m in re.finditer(r"^CMD\s+(\S+)", txt, re.M):
        cmds[m.group(1)] = cmds.get(m.group(1), 0) + 1

    temp = prev = None
    dsum, dn = 0.0, 0
    for m in re.finditer(r"^T\d+\s+(.*)$", txt, re.M):
        for kv in m.group(1).split():
            if kv.startswith("s.temperature="):
                temp = float(kv.split("=", 1)[1])
        # `temp >= 19000` on BOTH ends of the pair: the first post-ramp sample has
        # no valid predecessor and pairing it with a ramp value would count the
        # 9572 -> 20000 climb as one enormous step.
        if temp is not None and temp >= 19000 and prev is not None and prev >= 19000:
            dsum += abs(temp - prev)
            dn += 1
        if temp is not None:
            prev = temp

    return {
        "path": path,
        "ticks": ticks,
        "lines": txt.count("\n") + 1,
        "evt": len(ids),
        "seams": seams,
        "kinds": kinds,
        "cmds": cmds,
        "dtemp": dsum / max(1, dn),
        "dn": dn,
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    runs = [analyse(p) for p in argv[1:]]
    ref = runs[0]

    print("%-34s %6s %6s %6s %6s %6s %6s %8s %8s %6s" %
          ("run", "ticks", "lines", "cbl", "EVTctl", "INFO", "WARN", "ctx", "|dTemp|", "seams"))
    for a in runs:
        print("%-34s %6d %6d %6d %6d %6d %6d %8.2f %8.2f %6s" %
              (Path(a["path"]).name, a["ticks"], a["lines"],
               a["cmds"].get("cbl", 0), a["kinds"].get("CONTROL", 0),
               a["kinds"].get("INFO", 0), a["kinds"].get("WARN", 0),
               a["cmds"].get("extraction", 0),
               a["dtemp"],
               "clean" if a["seams"] == 0 else "%d BAD" % a["seams"]))

    if len(runs) > 1:
        print()
        print("CMD census, %s -> %s:" %
              (Path(ref["path"]).name, Path(runs[1]["path"]).name))
        for name in sorted(set(ref["cmds"]) | set(runs[1]["cmds"])):
            print("   %-18s %5d -> %5d" %
                  (name, ref["cmds"].get(name, 0), runs[1]["cmds"].get(name, 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
