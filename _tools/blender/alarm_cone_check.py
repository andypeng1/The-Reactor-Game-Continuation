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
#   - the wall is a CURVE, not the three straight bands of v1
#
# THE REFERENCE IS THE STUDIO RAYCAST TABLE BELOW, typed from the 2026-11-07
# sweep, NOT recomputed from alarm_cone.py's constants. A check that reads its
# expectations out of the thing it is checking is a tautology (DECISIONS 95).
# The two tables are two spellings of the same measurement, and they can disagree.
#
# WHAT CHANGED IN v2, AND WHY THE TABLE IS NO LONGER COMPARED FOR EQUALITY.
# v1 asserted "the rebuild EQUALS the source" at 44 radii, tol 0.002. The operator
# then asked for a rounder side ("那个把他侧边搞得更圆一些"), so the flank is now one
# Bezier instead of four straight bands and it deliberately departs from the
# measurement -- up to a few hundredths of a stud, in the middle.
#
# Loosening the tolerance until it went green would have been noise (CLAUDE.md
# 0.31). Instead the table keeps a job and changes tense: it becomes a BOUND --
# the new wall must stay within DEV_MAX of the source everywhere, so "rounder"
# cannot quietly become "a different object". The thing that actually has to be
# true of the new wall -- it is smooth -- gets its own measurement, and that one
# goes RED on v1's 42-degree crease. Both numbers are printed, not just asserted.
#
# Also checked here: the two radii just OUTSIDE the rim must MISS. Without those,
# a cone built 5% too wide passes every row of the table it is compared against.
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/blender/alarm_cone_check.py
#
# Exit 0 only if every check passes.

import math
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

# v1 compared for EQUALITY here at 0.002 (the source hull rounds its own P1 corner
# by 0.00101, so 0.002 was ~2x the noise floor). v2 changes the shape on purpose,
# so this is now the half-width of the band the new wall is allowed to wander in.
#
# MEASURED AS PERPENDICULAR DISTANCE, not as "height at the same radius". The wall
# is nearly vertical over most of its height, so a 0.02-stud radial error shows up
# as 0.16 studs of height difference down there -- the first version of this check
# reported 0.164 of "deviation" for a wall that had moved 0.025. That is CLAUDE.md
# 0.18's family again: the number was loud and meant something else. Distance from
# the source point to the rebuilt POLYLINE is scale-free and is what "the wall
# moved this far" actually means.
#
# 0.09 studs is a design bound, not a fitted one: 10% of the part's diameter. The
# measured value is printed every run; it is ~0.02-0.03, so the bound has 3-4x of
# room and only fires if the shape wandered somewhere else entirely.
DEV_MAX = 0.090

# Smoothness. Walk the silhouette in 0.005-stud radial steps and ask how far the
# surface turns between one step and the next.
#
#   v1 (four straight bands)  ->  42.5 deg at the P2 joint
#   v2 (the Bezier, shipped)  ->  12.8 deg at r=0.300
#
# 12.8 is not noise: the Bezier eases into the flat top, so its curvature is
# highest there. It is still a curve -- the turn is spread over neighbouring steps
# and the surface has no straight run -- which is why the threshold sits above it.
# 20 deg keeps 1.6x of headroom over the shipped curve and rejects v1's 42.5 deg
# by 2.1x. Those two numbers are printed on every run so the threshold can be
# re-argued from measurements instead of from taste.
STEP_TURN_DEG = 20.0
STEP_R = 0.005
SCAN = (0.440, 0.290)   # from just inside the rim down to the flat top

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


def wall_polyline(ob, k, r0=0.4495, r1=0.0500, step=0.002):
    """The rebuilt cross-section from the rim to the middle of the flat top."""
    pts = []
    n = int(round((r0 - r1) / step))
    for i in range(n + 1):
        r = r0 - i * step
        y = ray_down(ob, r, k)
        if y is not None:
            pts.append((r, y))
    return pts


def point_to_poly(px, py, poly):
    """Distance from a point to a polyline, in the (r, height) plane."""
    best = 1e18
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0.0 if L == 0.0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
        best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return best


def _angle(a, b):
    try:
        return math.degrees(a.angle(b))
    except ValueError:
        return 0.0


def shading_stats(ob, k):
    """(median spread of corner normals within a face, max spread at a POSITION).

    THIS IS THE MEASUREMENT THAT DECIDES WHETHER "ROUNDER" SHIPS. A 48-segment
    lathe is geometrically round to 0.001 studs; what the eye reads as round or
    faceted is the SHADING. Smooth-shaded, the corner normals of one wall facet
    differ by one facet's worth of turn (~7.5 deg). Flat-shaded, they are all the
    face normal and the spread is 0 -- and the part looks like a 48-gon in Studio
    even though every size and silhouette check above is green.

    It is exported that matters: FBX has a `mesh_smooth_type` switch whose default
    is "off", so the guard has to be here, on the re-imported file, or the change
    is invisible to the operator while every other row passes (CLAUDE.md 0.31).

    The second number is the bottom rim. It must NOT be smoothed -- a lens with a
    melted lower edge is a different object -- so the sharpest place in the mesh
    should still be near the 98 deg dihedral of that rim.

    MEASURED AT A POSITION, NOT AT A VERTEX INDEX. glTF duplicates a vertex
    wherever the normal is discontinuous, so on that side every vertex carries one
    normal and the per-index spread is 0.0 for EVERY mesh -- it answers "which
    file format is this", not "is the edge sharp" (CLAUDE.md 0.20, and DECISIONS
    681 from the watertightness check, which needed the identical fix). Welding by
    position puts a normal-split edge back together and both formats then report
    the same 97.3 deg.
    """
    me = ob.data
    try:
        ns = [tuple(c.vector) for c in me.corner_normals]
    except AttributeError:                      # pre-4.1
        me.calc_normals_split()
        ns = [tuple(lp.normal) for lp in me.loops]
    inv = ob.matrix_world.inverted().to_3x3().transposed()

    def pos_key(vi):
        co = (ob.matrix_world @ me.vertices[vi].co) * k
        return (round(co.x / 1e-5), round(co.y / 1e-5), round(co.z / 1e-5))

    per_face, per_pos = [], {}
    for p in me.polygons:
        idxs = list(range(p.loop_start, p.loop_start + p.loop_total))
        vs = [Vector(ns[i]) for i in idxs]
        s = 0.0
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                s = max(s, _angle(vs[i], vs[j]))
        per_face.append(s)
        for li in idxs:
            key = pos_key(me.loops[li].vertex_index)
            per_pos.setdefault(key, []).append((inv @ Vector(ns[li])).normalized())

    per_face.sort()
    median = per_face[len(per_face) // 2] if per_face else 0.0
    worst = 0.0
    for normals in per_pos.values():
        for i in range(len(normals)):
            for j in range(i + 1, len(normals)):
                worst = max(worst, _angle(normals[i], normals[j]))
    return median, worst


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
    missing = [r for r, _y in SILHOUETTE if ray_down(ob, r, k) is None]
    check("%s silhouette hits at all %d radii (missed %d)"
          % (tag, len(SILHOUETTE), len(missing)), not missing)
    if missing:
        print("  missed radii: %s" % " ".join("%.3f" % r for r in missing))

    poly = wall_polyline(ob, k)
    check("%s the wall is continuous from the rim to the flat top (%d rays)"
          % (tag, len(poly)), len(poly) >= 195)
    if len(poly) >= 2:
        worst_r, worst_d = None, -1.0
        for r, want in SILHOUETTE:
            d = point_to_poly(r, want, poly)
            if d > worst_d:
                worst_r, worst_d = r, d
        check("%s stays within %.3f of the source wall -- worst %.5f studs at r=%.3f"
              % (tag, DEV_MAX, worst_d, worst_r), worst_d < DEV_MAX)

    # --- the thing v2 is actually for: no crease anywhere on the wall ----------
    # Walk the silhouette and measure the turn between consecutive chords. A
    # piecewise-linear flank turns 42 deg at a joint; a curve spreads the same
    # total turn over every step. Sampling at the mesh's own facet spacing would
    # hide the difference, so the step is fixed in studs (= the Studio sweep's
    # grid) and the numbers are printed.
    rs = []
    r0, r1 = SCAN
    n = int(round((r0 - r1) / STEP_R))
    for i in range(n + 1):
        r = r0 - i * STEP_R
        y = ray_down(ob, r, k)
        if y is None:
            rs.append((r, None))
        else:
            rs.append((r, y))
    hits = [(r, y) for r, y in rs if y is not None]
    check("%s the whole wall is present along r %.3f..%.3f (%d of %d rays hit)"
          % (tag, r1, r0, len(hits), len(rs)), len(hits) == len(rs))
    if len(hits) == len(rs) and len(rs) > 3:
        angs = []
        for (ra, ya), (rb, yb) in zip(rs, rs[1:]):
            angs.append(math.degrees(math.atan2(abs(yb - ya), abs(rb - ra))))
        turns = [abs(b - a) for a, b in zip(angs, angs[1:])]
        worst_turn = max(turns)
        at = rs[turns.index(worst_turn) + 1][0]
        check("%s the wall is smooth -- worst turn %.2f deg between %.3f-stud steps "
              "(max %.1f, v1 was 42.5)"
              % (tag, worst_turn, STEP_R, STEP_TURN_DEG), worst_turn < STEP_TURN_DEG)
        # A guard, not the discriminator: "smooth" must not be reachable by
        # flattening the wall into the top plane and turning nowhere at all.
        # 50 rather than 60 because the shipped curve leaves the rim at the
        # measured 82 deg and has already eased to ~24 deg by r=0.44; v1 scored
        # ~70 here and passed too, so this row has never separated anything. It
        # is here to stop a degenerate shape, and it says so.
        total = angs[0] - angs[-1]
        check("%s the wall still turns %.1f deg from rim to shoulder (guard, want > 50)"
              % (tag, total), total > 50.0)
        print("  %-3s wall: worst turn %.2f deg at r=%.3f, total %.1f deg"
              % (tag, worst_turn, at, total))

    # --- the two dimensions that must NOT move, where the eye can see them -----
    rim = ray_down(ob, 0.4499, k)
    check("%s is solid just inside the rim (r=0.4499 -> %s)"
          % (tag, "miss" if rim is None else "%.5f" % rim), rim is not None)
    stray = [r for r in OUTSIDE if ray_down(ob, r, k) is not None]
    check("%s stops at the rim -- nothing at r in %s (hit: %s)"
          % (tag, OUTSIDE, stray), not stray)
    for r in (0.280, 0.200, 0.100):
        y = ray_down(ob, r, k)
        check("%s the top is still flat at r=%.3f (%s -> want 0.41250)"
              % (tag, r, "miss" if y is None else "%.5f" % y),
              y is not None and abs(y - 0.412500) < 5e-4)

    check("%s gives the part a material" % tag,
          all(len(o.data.materials) > 0 for o in objs))
    # Roblox splits a mesh into one MeshPart per material, so a stray material
    # index shows up in Studio as a second, grey part -- not as a wrong colour.
    check("%s uses exactly one material slot" % tag,
          all(len(o.data.materials) == 1 for o in objs))

    median_spread, rim_spread = shading_stats(ob, k)
    check("%s ships SMOOTH shading -- median corner-normal spread %.2f deg in a face "
          "(flat would be 0, one 48-gon facet is 7.5)"
          % (tag, median_spread), median_spread > 3.0)
    check("%s keeps the bottom rim a crease -- worst vertex spread %.1f deg (want > 60)"
          % (tag, rim_spread), rim_spread > 60.0)
    print("  %-3s shading: median face spread %.2f deg, worst vertex spread %.1f deg"
          % (tag, median_spread, rim_spread))

    st = trg.measure(ob)
    open_e, welded = welded_open_edges(ob, k)
    check("%s is watertight (open_edges=%d, %d corner positions)"
          % (tag, open_e, welded), open_e == 0)
    # 1586 = 1 bottom pole + 33 rings of 48 + 1 top pole (v1 was 194: 2 poles and
    # 4 rings). Typed from the build's own report, which is a count of what the
    # lathe emits -- not read back from here.
    check("%s welds down to the 1586 vertices the lathe emitted (got %d)"
          % (tag, welded), welded == 1586)
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
