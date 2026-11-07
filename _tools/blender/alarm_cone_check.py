# alarm_cone_check.py -- read the SHIPPED FILES back and compare them to what was
# measured in Studio.
#
# The build loop is not evidence (CLAUDE.md 0.6, and the Blender round of
# DECISIONS 261). What reaches Studio is the .fbx / .glb, and three things can
# only be seen from here:
#
#   - the scale survived BOTH exporters (they do not use the same mechanism --
#     FBX has global_scale, glTF does not, so the glTF branch is a separate claim)
#   - the axes did not get swapped on the way out (a body of revolution hides a
#     Z/Y swap in its SIZE; only the silhouette tells them apart)
#   - the shape is the one that was measured, at 45 radii, not just "about right"
#
# THE REFERENCE IS THE STUDIO RAYCAST TABLE BELOW, typed from the 2026-11-07
# sweep, NOT recomputed from alarm_cone.py's constants. A check that reads its
# expectations out of the thing it is checking is a tautology (DECISIONS 95).
# The two tables are two spellings of the same measurement, and they can disagree.
#
# Also checked here: the two radii just OUTSIDE the rim must MISS. Without those,
# a cone built 5% too wide passes every row of the table it is compared against.
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/blender/alarm_cone_check.py
#
# Exit 0 only if every check passes.

import os
import sys
import traceback

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

OUT = os.environ.get("ALARM_CONE_OUT", r"D:\BlenderRobloxTestProjects\AlarmCone")
NAME = "ReactorAlarmCone"
SPU = trg.STUDS_PER_UNIT

# ---- the part's own box, in studs, in Blender's frame (X, Y, Z) --------------
# Studio reported Size = 0.900000, 0.825000, 0.900000 with an identity CFrame.
# Blender is Z-up and the mesh is lathed about Z, so the 0.825 is Blender's Z.
WANT_SIZE = (0.900000, 0.900000, 0.825000)
WANT_MIN = (-0.450000, -0.450000, -0.412500)

# ---- the silhouette, read off the part with down-rays at 0.005-stud steps ----
# r (studs) -> height (studs). Bottom of the part is -0.4125, top +0.4125.
SILHOUETTE = [
    (0.445, -0.37588), (0.440, -0.33924), (0.435, -0.30262), (0.430, -0.26598),
    (0.425, -0.22933), (0.420, -0.19263), (0.415, -0.15607), (0.410, -0.11940),
    (0.405, -0.08281), (0.400, -0.04620), (0.395, -0.00957), (0.390, 0.02705),
    (0.385, 0.06367), (0.380, 0.10033), (0.375, 0.13693), (0.370, 0.17360),
    (0.365, 0.21019), (0.360, 0.24682), (0.355, 0.28345), (0.350, 0.32119),
    (0.345, 0.34487), (0.340, 0.35726), (0.335, 0.36965), (0.330, 0.38204),
    (0.325, 0.39283), (0.320, 0.39523), (0.315, 0.39762), (0.310, 0.40002),
    (0.305, 0.40241), (0.300, 0.40486), (0.295, 0.40726), (0.290, 0.40967),
    (0.285, 0.41201), (0.280, 0.41250), (0.275, 0.41250), (0.270, 0.41250),
    (0.265, 0.41250), (0.260, 0.41250), (0.255, 0.41250), (0.250, 0.41250),
    (0.245, 0.41250), (0.240, 0.41250), (0.235, 0.41250), (0.230, 0.41250),
]

# The source hull rounds the P1 corner by 0.00101 studs, which is the largest
# residual the four straight bands leave on the whole table. 0.002 is ~2x that and
# ~1/10 of the smallest band (0.02 studs), so a moved band joint cannot hide:
# nudging P1 by 0.005 moves the r=0.350 row by 0.037.
TOL_SHAPE = 0.002

# Just outside the rim. Both must miss, in both formats.
OUTSIDE = (0.4550, 0.4600)

CHECKS = []
FAILS = []


def check(label, ok):
    CHECKS.append((label, bool(ok)))
    if not ok:
        FAILS.append(label)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load_fbx(path):
    reset()
    # 5.902 is typed, not read out of the file: it is the number the operator
    # types into Studio's import dialog, and this undoes the export-side 1/5.902.
    bpy.ops.import_scene.fbx(filepath=path, global_scale=SPU)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"], 1.0


def load_glb(path):
    reset()
    # glTF has no global_scale; the exporter baked 1/5.902 into each node, so the
    # world coordinates are studs/5.902 and the reading has to be scaled back.
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"], SPU


def bounds(objs, k):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for ob in objs:
        for v in ob.data.vertices:
            w = (ob.matrix_world @ v.co) * k
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def welded_open_edges(ob, k, q=1e-5):
    """(edges not used exactly twice, distinct corner positions), after merging
    vertices that sit at the same point.

    Counting shared vertex INDICES says "672 open edges" on a closed solid,
    because glTF splits a vertex per face whenever the normals differ -- 674
    vertices for this 194-vertex mesh, 0 of them shared. That is a property of
    the FORMAT; the FBX keeps the 194 and reports 0. Two formats, two answers,
    because the question was about the format (CLAUDE.md 0.20). Welding by
    position asks the question about the shape instead, so both branches get the
    same question and a real hole would still turn up.
    """
    def key(co):
        return (round(co.x / q), round(co.y / q), round(co.z / q))

    idx, remap = {}, []
    for v in ob.data.vertices:
        kk = key((ob.matrix_world @ v.co) * k)
        if kk not in idx:
            idx[kk] = len(idx)
        remap.append(idx[kk])
    use = {}
    for poly in ob.data.polygons:
        vs = [remap[i] for i in poly.vertices]
        for a, b in zip(vs, vs[1:] + vs[:1]):
            e = (a, b) if a < b else (b, a)
            use[e] = use.get(e, 0) + 1
    return sum(1 for c in use.values() if c != 2), len(idx)


def ray_down(ob, r, k, z0=0.6):
    """Straight down at horizontal radius r; the height of the first hit, in studs.

    The transform is undone rather than assumed: an importer is free to hand back
    a rotated or scaled object, and reading its vertices as if it were identity is
    exactly the kind of ruler that does not error (CLAUDE.md 0.18).
    """
    inv = ob.matrix_world.inverted()
    origin = inv @ (Vector((r, 0.0, z0)) / k)
    direction = (inv.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    hit, loc, _nrm, _idx = ob.ray_cast(origin, direction)
    if not hit:
        return None
    return (ob.matrix_world @ loc).z * k


def read(tag, objs, k, tol_size):
    check("%s delivers exactly one mesh part (got %d)" % (tag, len(objs)), len(objs) == 1)
    if not objs:
        return
    lo, hi = bounds(objs, k)
    got = hi - lo
    for i, axis in enumerate("XYZ"):
        check("%s size %s = %.4f (want %.4f)"
              % (tag, axis, got[i], WANT_SIZE[i]),
              abs(got[i] - WANT_SIZE[i]) < tol_size)
        check("%s min  %s = %.4f (want %.4f)"
              % (tag, axis, lo[i], WANT_MIN[i]),
              abs(lo[i] - WANT_MIN[i]) < tol_size)

    ob = objs[0]
    worst_r, worst_d = None, -1.0
    missing = []
    for r, want in SILHOUETTE:
        got_y = ray_down(ob, r, k)
        if got_y is None:
            missing.append(r)
            continue
        d = abs(got_y - want)
        if d > worst_d:
            worst_r, worst_d = r, d
    check("%s silhouette hits at all %d radii (missed %d)"
          % (tag, len(SILHOUETTE), len(missing)), not missing)
    if missing:
        print("  missed radii: %s" % " ".join("%.3f" % r for r in missing))
    if worst_r is not None:
        check("%s silhouette worst residual %.5f studs at r=%.3f (tol %.3f)"
              % (tag, worst_d, worst_r, TOL_SHAPE), worst_d < TOL_SHAPE)

    rim = ray_down(ob, 0.4499, k)
    check("%s is solid just inside the rim (r=0.4499 -> %s)"
          % (tag, "miss" if rim is None else "%.5f" % rim), rim is not None)
    stray = [r for r in OUTSIDE if ray_down(ob, r, k) is not None]
    check("%s stops at the rim -- nothing at r in %s (hit: %s)"
          % (tag, OUTSIDE, stray), not stray)

    check("%s gives the part a material" % tag,
          all(len(o.data.materials) > 0 for o in objs))
    # Roblox splits a mesh into one MeshPart per material, so a stray material
    # index shows up in Studio as a second, grey part -- not as a wrong colour.
    check("%s uses exactly one material slot" % tag,
          all(len(o.data.materials) == 1 for o in objs))

    st = trg.measure(ob)
    open_e, welded = welded_open_edges(ob, k)
    check("%s is watertight (open_edges=%d, %d corner positions)"
          % (tag, open_e, welded), open_e == 0)
    # 194 = 1 bottom pole + 4 rings of 48 + 1 top pole. Typed from the build's own
    # report, which is a count of what the lathe emits -- not read back from here.
    check("%s welds down to the 194 vertices the lathe emitted (got %d)"
          % (tag, welded), welded == 194)
    print("  %-3s size %.4f %.4f %.4f  min %.4f %.4f %.4f  verts %d tris %d"
          % ((tag,) + tuple(got) + tuple(lo) + (st["verts"], st["tris"])))


def build():
    fbx = os.path.join(OUT, NAME + ".fbx")
    glb = os.path.join(OUT, NAME + ".glb")
    for p in (fbx, glb):
        if not os.path.exists(p):
            check("MISSING %s" % os.path.abspath(p), False)
    if FAILS:
        return

    objs, k = load_fbx(fbx)
    read("fbx", objs, k, 1e-2)
    objs, k = load_glb(glb)
    read("glb", objs, k, 1e-3)

    ok = len(CHECKS) - len(FAILS)
    for label, good in CHECKS:
        print("%s %s" % ("PASS" if good else "FAIL", label))
    print("CHECK %d ok, %d failed" % (ok, len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    try:
        rc = build()
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        print("CRASHED -- this is a failure, not a pass")
        rc = 1
    sys.exit(rc)
