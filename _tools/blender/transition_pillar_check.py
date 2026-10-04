# Read the exported file back and check the TOPOLOGY, which is the whole point of
# this asset. The build loop is not evidence (CLAUDE.md 0.6): an unbridged model,
# a bridged-but-twisted model, and a correct model are all just "a mesh" as far
# as the build script's own printout goes.
#
# FOUR THINGS ONLY THIS CAN SEE:
#   - that the two rims still have 18 and 24 verts after the round trip, rather
#     than having been welded, duplicated or re-cut by the exporter
#   - that the band is 42 TRIANGLES and not, say, 42 quads whose diagonal the
#     importer would get to choose
#   - that the band is not TWISTED. A twisted bridge has the same face count, is
#     just as manifold and just as closed; it is only wrong when you look at
#     where the faces ARE
#   - that the solid is closed and in one piece
#
# BOTH FORMATS, and that is deliberate: two exporters writing the same scene are
# two independent witnesses. The .glb branch is the one that silently shipped
# broken for two rounds on the laser port while the .fbx branch passed (see
# trg.export).
#
# The constants below are TYPED from transition_pillar.py's design block, never
# read back out of an export -- comparing a file against itself is a tautology
# (DECISIONS 95).
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

# Overridable so this can be pointed at the --no-bridge mutation and shown to go
# red. A checker nobody has ever watched fail is a checker nobody has tested
# (DECISIONS 205).
OUT_DIR = os.environ.get("TRANSITION_PILLAR_OUT",
                         r"D:\BlenderRobloxTestProjects\TransitionPillar")
SPU = trg.STUDS_PER_UNIT

BASE_SIDES, BASE_R, BASE_Z = 18, 2.40, (0.00, 1.60)
TOP_SIDES, TOP_R, TOP_Z = 24, 2.10, (2.40, 4.60)
TOL = 1e-3

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

    MEASURED, and the reason this function exists: the FBX round trip hands back
    126 verts / 128 polys, the authored mesh corner for corner. The glTF round
    trip hands back 504 verts / 248 polys, because glTF has nowhere to put a
    polygon and therefore splits every vertex whose corner attributes differ (a
    normal at a bevel, a UV at a seam). Both files describe the SAME solid; only
    one of them still carries the topology in its indices. Asked directly, the
    glb reports 504 open edges and 128 shells -- a defect in the question, not in
    the file, and exactly the shape of CLAUDE.md 0.18: a wrong ruler does not
    error, it answers confidently.

    UNIT TRAP, hit once in the first draft: Blender scene coordinates are file
    units, and the file holds studs/5.902. Comparing a raw coordinate against a
    height typed in studs finds nothing at any height -- every rim came back with
    n=0, which reads like a broken export rather than a broken comparison.
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


for fmt, load in (("fbx", load_fbx), ("glb", load_glb)):
    path = os.path.join(OUT_DIR, "TransitionPillar.%s" % fmt)
    if not os.path.exists(path):
        FAILS.append(1)
        print("MISSING %s" % path)
        continue
    objs = load(path)
    if len(objs) != 1:
        FAILS.append(1)
        print("FILE TransitionPillar.%s  *** expected 1 object, got %d ***"
              % (fmt, len(objs)))
        continue
    obj = objs[0]
    raw = trg.measure(obj)
    pos, faces = welded(obj)
    use = edge_use(faces)
    open_edges = sum(1 for c in use.values() if c != 2)

    print("FILE TransitionPillar.%s" % fmt)
    print("  as stored: verts=%d polys=%d tris=%d   welded: verts=%d faces=%d"
          % (raw["verts"], raw["polys"], raw["tris"], len(pos), len(faces)))

    ok = tally(open_edges == 0)
    print("  closed manifold: open_edges=%d %s"
          % (open_edges, verdict(ok, "OK", "HOLES")))

    n_shell = shells(faces, len(pos))
    ok = tally(n_shell == 1)
    print("  single shell: components=%d %s"
          % (n_shell, verdict(ok, "OK", "SPLIT")))

    # The two rims, found by height. The bevel skips them on purpose -- the band
    # leans in only atan(0.30/0.80) = 20.6 deg against a 25 deg threshold -- so
    # they are still exactly 18 and 24 verts sitting at the design heights.
    rims = {}
    for sides, r, z, label in ((BASE_SIDES, BASE_R, BASE_Z[1], "lower"),
                               (TOP_SIDES, TOP_R, TOP_Z[0], "upper")):
        ring = [p for p in pos if abs(p[2] - z) < TOL]
        radii = [math.hypot(p[0], p[1]) for p in ring]
        rims[label] = ring
        ok_n = tally(len(ring) == sides)
        ok_r = tally(bool(radii) and (max(radii) - min(radii)) < 0.01
                     and abs(radii[0] - r) < 0.01)
        print("  rim %s: z=%.3f n=%d (want %d) %s | r=%.4f..%.4f (want %.2f) %s"
              % (label, z, len(ring), sides, verdict(ok_n, "OK", "WRONG COUNT"),
                 min(radii) if radii else -1, max(radii) if radii else -1, r,
                 verdict(ok_r, "OK", "WRONG RADIUS")))

    # The band: every face that touches both rims. Same predicate the build
    # script uses, so the two are measuring the same thing.
    band = [f for f in faces
            if min(pos[i][2] for i in f) <= BASE_Z[1] + TOL
            and max(pos[i][2] for i in f) >= TOP_Z[0] - TOL]
    want = BASE_SIDES + TOP_SIDES
    ok = tally(len(band) == want)
    print("  band faces=%d (want %d) %s"
          % (len(band), want, verdict(ok, "OK", "WRONG COUNT")))

    ok = tally(bool(band) and all(len(f) == 3 for f in band))
    print("  band all triangles: %d of %d %s"
          % (sum(1 for f in band if len(f) == 3), len(band),
             verdict(ok, "OK", "NOT ALL TRIANGLES")))

    # THE TWIST TEST. A twisted band has the same face count and the same
    # manifoldness; what it does not have is its faces out at the rim. Anything
    # reaching across the interior has a centroid near the axis, so centroid
    # radius separates them -- and the floor is a fraction of the SMALLER rim,
    # not a hand-picked number, so it survives a resize of the design.
    floor_r = 0.9 * min(BASE_R, TOP_R)
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

    # No zero-area faces. A coplanar bridge (both rims at the same height, which
    # is what happens if the joint faces are deleted and the cylinders are left
    # touching) is geometrically legal and completely invisible.
    def area(f):
        a, b, c = (pos[i] for i in f[:3])
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        return 0.5 * math.sqrt((u[1] * v[2] - u[2] * v[1]) ** 2
                               + (u[2] * v[0] - u[0] * v[2]) ** 2
                               + (u[0] * v[1] - u[1] * v[0]) ** 2)

    zero = sum(1 for f in faces if area(f) < 1e-6)
    ok = tally(zero == 0)
    print("  no degenerate faces: %d %s" % (zero, verdict(ok, "OK", "DEGENERATE")))

    xs, ys, zs = ([p[i] for p in pos] for i in range(3))
    zs = list(zs)
    print("  size_studs=%.2f x %.2f x %.2f  z=%.2f..%.2f"
          % (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs),
             min(zs), max(zs)))
    # What Studio should say. Blender is Z-up, Roblox is Y-up, so Y and Z swap.
    print("  expected_studio_size=%.2f x %.2f x %.2f (Roblox frame)"
          % (max(xs) - min(xs), max(zs) - min(zs), max(ys) - min(ys)))

done()
