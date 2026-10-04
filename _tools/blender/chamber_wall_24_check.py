# Read the exported file back and check the JOIN, which is the whole point of
# this asset. The build loop is not evidence (CLAUDE.md 0.6): an unbridged model,
# a band joined to the wrong partners, and a correct model are all just "a mesh"
# as far as the build script's own printout goes.
#
# FOUR THINGS ONLY THIS CAN SEE:
#   - that the four rims survived the round trip at their designed counts and
#     radii, rather than having been welded, duplicated or re-cut by the exporter
#   - that the band is 84 TRIANGLES (42 per surface) and not, say, 84 quads whose
#     diagonal the importer would get to choose
#   - that each band triangle spans the two rims ON THE SAME SIDE -- an outer rim
#     joined to an inner one is 84 triangles that pass every count test and are
#     still not the shape that was asked for
#   - that the band is not TWISTED. A twisted bridge has the same face count, is
#     just as manifold and just as closed; it is only wrong when you look at
#     WHERE the faces are
#
# BOTH FORMATS, and that is deliberate: two exporters writing the same scene are
# two independent witnesses. The .glb branch is the one that silently shipped
# broken for two rounds on the laser port while the .fbx branch passed (see
# trg.export).
#
# The constants below are TYPED from chamber_wall_24.py's design block, never read
# back out of an export -- comparing a file against itself is a tautology
# (DECISIONS 95).
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

# Overridable so this can be pointed at a mutation's output and shown to go red.
# A checker nobody has ever watched fail is a checker nobody has tested
# (DECISIONS 205).
OUT_DIR = os.environ.get("CHAMBER_WALL_OUT",
                         r"D:\BlenderRobloxTestProjects\ChamberWall24")
SPU = trg.STUDS_PER_UNIT

N18, A18, N24, A24, WALL = 18, 63.712, 24, 68.000, 4.00
Z_COLLAR, Z_BAND, Z_TOP = 1.20, 4.20, 13.20
TOL = 2e-3

RIM = {
    "18out": (N18, A18 / math.cos(math.pi / N18), Z_COLLAR),
    "18in": (N18, (A18 - WALL) / math.cos(math.pi / N18), Z_COLLAR),
    "24out": (N24, A24 / math.cos(math.pi / N24), Z_BAND),
    "24in": (N24, (A24 - WALL) / math.cos(math.pi / N24), Z_BAND),
}

FAILS = []
CHECKS = [0]


def tally(ok):
    CHECKS[0] += 1
    if not ok:
        FAILS.append(1)
    return ok


def verdict(ok, good, bad):
    """Report the FAILURE, not the success. The first draft of this file passed
    "OK" into both slots and printed `*** OK ***` on every red line -- a checker
    whose output cannot be read at a glance is a checker that gets skimmed."""
    return good if ok else ("*** " + bad + " ***")


def done():
    print("CHECK %d ok, %d failed" % (CHECKS[0] - len(FAILS), len(FAILS)))
    sys.exit(1 if FAILS else 0)


def load_fbx(path):
    trg.new_scene()
    bpy.ops.import_scene.fbx(filepath=path, global_scale=1.0)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def load_glb(path):
    # No global_scale: glTF has no such option, which is exactly why the exporter
    # has to get the scale right on its own and why this branch exists.
    trg.new_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def welded(obj):
    """Position-keyed vertices, in STUDS, so both files get asked the SAME
    question.

    The FBX round trip hands back the authored mesh corner for corner; the glTF
    one splits every vertex whose corner attributes differ, because glTF has
    nowhere to put a polygon. Asked directly the .glb reports hundreds of open
    edges and as many shells -- a defect in the QUESTION, not in the file, and
    exactly the shape of CLAUDE.md 0.18: a wrong ruler does not error, it answers
    confidently.

    The 5.902 here is not a formality. Blender scene coordinates are FILE units
    and the file holds studs/5.902; comparing a raw coordinate against an apothem
    typed in studs finds nothing at any height, and reads like a broken export.
    """
    key_of, pos, index = {}, [], []
    for v in obj.data.vertices:
        w = obj.matrix_world @ v.co
        k = (round(w.x, 5), round(w.y, 5), round(w.z, 5))
        if k not in key_of:
            key_of[k] = len(pos)
            pos.append((w.x * SPU, w.y * SPU, w.z * SPU))
        index.append(key_of[k])
    faces = [tuple(index[i] for i in p.vertices) for p in obj.data.polygons]
    return pos, faces


def edge_use(faces):
    use = {}
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            k = (a, b) if a < b else (b, a)
            use[k] = use.get(k, 0) + 1
    return use


def shells(faces, nverts):
    parent = list(range(nverts))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    return len({find(i) for i in range(nverts)})


def classify(p):
    """Which rim a point belongs to, or None for everything else.

    Height first, radius second: the two Z heights are unambiguous, while on the
    24 side the inner rim (64.55) and the 18-gon's outer rim (64.69) are a wall
    thickness apart in radius and would otherwise be confusable.
    """
    r, z = math.hypot(p[0], p[1]), p[2]
    for tag, (n, rad, zz) in RIM.items():
        if abs(z - zz) < TOL and abs(r - rad) < TOL:
            return tag
    return None


def apothem(points, n):
    """The apothem of a regular n-gon with a corner on +X, fitted to `points`.

    The largest distance from the axis to any of the n side planes. For the real
    polygon each side plane touches exactly its own two corners, so this returns
    the apothem exactly; for a wrong polygon it returns something else, which is
    the whole test -- `n` corners at some radius is NOT the same claim as "the
    sides sit where the neighbour's sides sit".
    """
    best = 0.0
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        ca, sa = math.cos(a), math.sin(a)
        best = max(best, max(p[0] * ca + p[1] * sa for p in points))
    return best


def area(p, f):
    a, b, c = (p[i] for i in f[:3])
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return 0.5 * math.sqrt((u[1] * v[2] - u[2] * v[1]) ** 2
                           + (u[2] * v[0] - u[0] * v[2]) ** 2
                           + (u[0] * v[1] - u[1] * v[0]) ** 2)


for fmt, load in (("fbx", load_fbx), ("glb", load_glb)):
    path = os.path.join(OUT_DIR, "ChamberWall24.%s" % fmt)
    if not os.path.exists(path):
        FAILS.append(1)
        print("MISSING %s" % path)
        continue
    objs = load(path)
    if len(objs) != 1:
        FAILS.append(1)
        print("FILE ChamberWall24.%s  *** expected 1 object, got %d ***"
              % (fmt, len(objs)))
        continue
    obj = objs[0]
    raw = trg.measure(obj)
    pos, faces = welded(obj)
    use = edge_use(faces)
    open_edges = sum(1 for c in use.values() if c != 2)
    tags = [classify(p) for p in pos]

    print("FILE ChamberWall24.%s" % fmt)
    print("  as stored: verts=%d polys=%d tris=%d   welded: verts=%d faces=%d"
          % (raw["verts"], raw["polys"], raw["tris"], len(pos), len(faces)))

    ok = tally(open_edges == 0)
    print("  closed manifold: open_edges=%d %s"
          % (open_edges, verdict(ok, "OK", "HOLES")))

    n_shell = shells(faces, len(pos))
    ok = tally(n_shell == 1)
    print("  single shell: components=%d %s"
          % (n_shell, verdict(ok, "OK", "SPLIT")))

    # The four rims. Every vertex of the mesh is either on one of them or at the
    # base (z=0) or the top (z=Z_TOP); anything unclassified at a joint height is
    # a vertex the bridge invented.
    counts = {t: sum(1 for x in tags if x == t) for t in RIM}
    for tag in ("18out", "18in", "24out", "24in"):
        n, rad, zz = RIM[tag]
        ok = tally(counts[tag] == n)
        print("  rim %-5s z=%.2f n=%d (want %d) r=%.4f (want %.4f) %s"
              % (tag, zz, counts[tag], n, rad, rad, verdict(ok, "OK", "WRONG")))

    stray = sum(1 for p, t in zip(pos, tags)
                if t is None and abs(p[2]) > TOL and abs(p[2] - Z_TOP) > TOL)
    ok = tally(stray == 0)
    print("  no stray joint verts: %d %s" % (stray, verdict(ok, "OK", "STRAY")))

    # The two polygons' SHAPE, not just their corner count. The 18-gon's apothem
    # is the number measured off the place, so this is the assertion that the join
    # actually lands on the neighbour's surface.
    for tag, want in (("18out", A18), ("24out", A24)):
        pts = [p for p, t in zip(pos, tags) if t == tag]
        got = apothem(pts, RIM[tag][0]) if pts else -1
        ok = tally(abs(got - want) < TOL)
        print("  %s apothem=%.3f (want %.3f) %s"
              % (tag, got, want, verdict(ok, "OK", "WRONG POLYGON")))

    # The band: every face with a vertex on a joint rim and none anywhere else.
    band = [f for f in faces if all(tags[i] is not None for i in f)]
    want_faces = 2 * (N18 + N24)
    ok = tally(len(band) == want_faces)
    print("  band faces=%d (want %d) %s"
          % (len(band), want_faces, verdict(ok, "OK", "WRONG COUNT")))

    ok = tally(bool(band) and all(len(f) == 3 for f in band))
    print("  band all triangles: %d of %d %s"
          % (sum(1 for f in band if len(f) == 3), len(band),
             verdict(ok, "OK", "NOT ALL TRIANGLES")))

    # THE PAIRING TEST. Each band triangle must reach from an 18-gon rim to a
    # 24-gon rim ON THE SAME SIDE. Bridge the outer rim to the inner and every
    # count above still passes -- 84 triangles, all spanning two rims, all closed.
    bad, per_side = 0, {"out": 0, "in": 0}
    for f in band:
        ts = [tags[i] for i in f]
        e18 = [t for t in ts if t.startswith("18")]
        e24 = [t for t in ts if t.startswith("24")]
        if len(e18) + len(e24) != 3 or not e18 or not e24:
            bad += 1
        elif (e18[0][2:] != e24[0][2:]):
            bad += 1
        else:
            per_side[e18[0][2:]] += 1
    ok = tally(bad == 0)
    print("  band spans matching rims: %d bad %s"
          % (bad, verdict(ok, "OK", "CROSSED PAIRING")))
    ok = tally(per_side["out"] == N18 + N24 and per_side["in"] == N18 + N24)
    print("  band split out/in: %d / %d (want %d each) %s"
          % (per_side["out"], per_side["in"], N18 + N24,
             verdict(ok, "OK", "WRONG SPLIT")))

    # THE TWIST TEST. A twisted band has the same face count and the same
    # manifoldness; what it does not have is its faces out at the rim. Anything
    # reaching across the interior has a centroid near the axis, so centroid
    # radius separates them -- and the floor is a fraction of the SMALLEST rim,
    # not a hand-picked number, so it survives a resize of the design.
    floor_r = 0.9 * min(r for (_, r, _) in RIM.values())
    worst = None
    for f in band:
        cx = sum(pos[i][0] for i in f) / len(f)
        cy = sum(pos[i][1] for i in f) / len(f)
        rad = math.hypot(cx, cy)
        worst = rad if worst is None else min(worst, rad)
    ok = tally(worst is not None and worst > floor_r)
    print("  band not twisted: min centroid radius=%.4f (floor %.4f) %s"
          % (worst if worst is not None else -1, floor_r,
             verdict(ok, "OK", "TWISTED")))

    # No zero-area faces. Two rims at the same height bridge into a fan that is
    # geometrically legal, closed, 84 triangles -- and completely invisible.
    zero = sum(1 for f in faces if area(pos, f) < 1e-6)
    ok = tally(zero == 0)
    print("  no degenerate faces: %d %s" % (zero, verdict(ok, "OK", "DEGENERATE")))

    xs = [p[0] for p in pos]
    ys = [p[1] for p in pos]
    zs = [p[2] for p in pos]
    ok = tally(abs(min(zs)) < TOL and abs(max(zs) - Z_TOP) < TOL)
    print("  height: z=%.3f..%.3f (want 0.00..%.2f) %s"
          % (min(zs), max(zs), Z_TOP, verdict(ok, "OK", "WRONG HEIGHT")))
    print("  size_studs=%.2f x %.2f x %.2f"
          % (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    # What Studio should say. Blender is Z-up, Roblox is Y-up, so Y and Z swap.
    print("  expected_studio_size=%.2f x %.2f x %.2f (Roblox frame)"
          % (max(xs) - min(xs), max(zs) - min(zs), max(ys) - min(ys)))

done()
