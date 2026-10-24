# check_mk4_mat_table.py -- the two tables in apply_cbl_laser_mk4_materials.luau
# are TYPED, and typing is where a number drifts.
#
# It compares, in both directions:
#   1. every (part, material) SIZE in the Luau against the build's own
#      MATERIAL_TABLE print. The build log must be the one written by the same
#      run that produced the delivered .fbx -- pass it explicitly and the script
#      checks the file timestamps are not older than the export.
#   2. the colour table: the LINEAR values in cbl_laser_mk4.py's MATERIALS put
#      through the sRGB transfer function, against the integer triplets in the
#      Luau. A linear value copied straight across is the classic mistake here
#      and it looks plausible on a dark metal.
#
# No Blender, no Studio: this is a text-to-text check on the two files that ship.
# RUN
#   python -I _tools/check_mk4_mat_table.py [--log <build.log>]
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LUAU = os.path.join(HERE, "apply_cbl_laser_mk4_materials.luau")
BUILD = os.path.join(HERE, "blender", "cbl_laser_mk4.py")
DEFAULT_LOG = os.path.join(HERE, "_attic", "scratch", "mk4_build2.log")
DELIVERED = r"D:\BlenderRobloxTestProjects\CblLaserMk4\CblLaserMk4.fbx"

fails, checks = [], [0]


def check(ok, label, detail=""):
    checks[0] += 1
    if not ok:
        fails.append(label)
    print("  %-46s %s%s" % (label, "OK" if ok else "*** FAIL ***",
                            ("  " + detail) if detail else ""))


def parse_log(path):
    """Rows as printed by cbl_laser_mk4.py: part -> {mat: (x, z, y)}."""
    text = open(path, encoding="utf-8", errors="replace").read()
    block = text.split("MATERIAL_TABLE_BEGIN", 1)[1].split("MATERIAL_TABLE_END", 1)[0]
    out, part = {}, None
    for line in block.splitlines():
        m = re.match(r"\s*(CblLaserMk4\w+) = \{", line)
        if m:
            part = m.group(1).replace("CblLaserMk4", "")
            out[part] = {}
            continue
        m = re.match(r'\s*\{ mat = "(\w+)", size = \{ ([\d.]+), ([\d.]+), ([\d.]+) \} \}', line)
        if m and part:
            out[part][m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
    return out


def parse_luau(path):
    text = open(path, encoding="utf-8").read()
    # NOTE ON THE PATTERNS: every separator is \s* or \s+, never a single space.
    # The tables are column-aligned for reading, so `{  5.2800` and
    # `{ 191, 155,  91 }` carry double spaces -- and a regex that assumes one
    # space silently drops exactly those rows (MEASURED on the first run of this
    # check: 10 of 13 size rows and 2 of 7 colour rows were "missing", which
    # reads as a table defect and was a parser defect).
    rows = {}
    for m in re.finditer(
            r'\{ part = "(\w+)",\s*mat = "(\w+)",\s*size = \{\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\s*\}',
            text):
        rows[(m.group(1), m.group(2))] = tuple(float(m.group(i)) for i in (3, 4, 5))
    looks = {}
    for m in re.finditer(
            r"(\w+)\s*= \{ material = Enum\.Material\.(\w+),\s*rgb = \{\s*(\d+),\s*(\d+),\s*(\d+)\s*\}",
            text):
        looks[m.group(1)] = (m.group(2), tuple(int(m.group(i)) for i in (3, 4, 5)))
    return rows, looks


def parse_build_colours(path):
    """Linear rgb per material name, from trg.material(...) / glow(...) calls."""
    text = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'(?:trg\.material|glow)\("Mk4(\w+)",\s*\(([\d.]+),\s*([\d.]+),\s*([\d.]+)\)', text):
        out[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
    return out


def srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    args = ap.parse_args()

    if os.path.exists(DELIVERED) and os.path.getmtime(DELIVERED) > os.path.getmtime(args.log):
        check(False, "build log is from the delivered run",
              "log %s is OLDER than %s -- rerun the build and capture it"
              % (os.path.basename(args.log), os.path.basename(DELIVERED)))
    else:
        check(True, "build log is from the delivered run")

    log = parse_log(args.log)
    rows, looks = parse_luau(LUAU)
    print("  log rows=%d  luau rows=%d  look rows=%d"
          % (sum(len(v) for v in log.values()), len(rows), len(looks)))

    want = {(p, m): s for p, mats in log.items() for m, s in mats.items()}
    check(set(want) == set(rows), "same (part, material) set",
          "only-in-log=%s only-in-luau=%s"
          % (sorted(set(want) - set(rows)), sorted(set(rows) - set(want))))

    worst, worst_k = 0.0, None
    for k in sorted(set(want) & set(rows)):
        d = max(abs(a - b) for a, b in zip(want[k], rows[k]))
        if d > worst:
            worst, worst_k = d, k
        check(d <= 1e-3, "size %s/%s" % k,
              "log %s luau %s dmax %.5f" % (want[k], rows[k], d))
    if worst_k:
        print("  worst size disagreement: %s/%s  %.5f studs" % (worst_k[0], worst_k[1], worst))

    lin = parse_build_colours(BUILD)
    check(set(lin) == set(looks), "colour names match the build",
          "missing-look=%s missing-build=%s"
          % (sorted(set(lin) - set(looks)), sorted(set(looks) - set(lin))))
    for name in sorted(set(lin) & set(looks)):
        got_srgb = tuple(round(srgb(c) * 255) for c in lin[name])
        check(got_srgb == looks[name][1], "colour %s is linear->sRGB" % name,
              "linear %s -> %s, luau %s" % (lin[name], got_srgb, looks[name][1]))
        check(looks[name][0] in ("Metal", "SmoothPlastic", "Neon"),
              "material %s is a Roblox Material" % name, looks[name][0])

    print("CHECK %d ok, %d failed" % (checks[0] - len(fails), len(fails)))
    return 1 if fails else 0


sys.exit(main())
