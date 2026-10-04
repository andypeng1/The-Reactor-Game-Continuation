# Re-import what ring_bridge_18_24.py exported and measure IT -- not the bmesh
# that built it.
#
# WHY A SEPARATE PASS. The build loop is not evidence (CLAUDE.md 0.2, Blender
# side). Everything ring_bridge_18_24.py prints is a statement about objects it
# holds in memory; an export that bakes transforms into geometry, drops a
# material slot, or welds away the very vertices the spec indexes by is invisible
# from there. This file opens the SHIPPED BYTES and measures them.
#
# ================================================= what is asserted, and why
#
# THE SPEC is six statements, and each one gets an assertion that can go red on
# its own:
#   3. two coaxial rings       -- 18 verts at radius 0.8 / z 0, 24 at 1.2 / z 1
#   4. end faces kept as the n-gons the spec named -- in the .blend that is one
#      18-gon and one 24-gon face, asserted there. MEASURED, and it is not what
#      this file first assumed: the FBX holds the polygons too (its importer
#      rebuilds 1 + 1 face), and only glTF triangulates them (16 + 22). So the
#      export side asserts the format-independent half of the same claim -- the
#      cap spans all 18 (resp. 24) corners and has the ring's full area -- and
#      prints the shipped face count instead of asserting the format's answer
#   5. the 42 triangles ARE the operator's list -- not merely 42 of them. The
#      check rebuilds his seven relations per group and looks for each one as a
#      face; a bridge_loops-style pairing that produced a valid 42 would fail here.
#      Bridge faces are identified by MATERIAL SLOT, never by side count: in the
#      glTF the 38 triangulated cap faces are triangles too and "count the
#      triangles" then answers 80
#   6. both caps one material, all 42 triangles another -- asserted as the two
#      colours read back OUT of the file, since the classification above defines
#      the slots and restating that would assert the definition
#
# THE JOIN is one vertex set: every bridge triangle's corners must be one of the
# 42 ring vertices -- nothing invented, nothing left over.
#
# ORIENTATION is proven, not assumed. trg.finish() runs recalc_face_normals, and
# "the engine fixed it" is not a measurement. Two independent routes compute the
# volume: the prismatoid formula from the z=0.5 mid-section, and a divergence sum
# over the shipped faces. A mixed winding makes the second one wrong by more than
# the volume (measured on the pre-recalc mesh: -0.367 against 3.111).
#
# Mutations, each named with the assertion it must turn red:
#   --flip-one     one triangle wound the other way   -> the volumes disagree
#   --wrong-apex   one relation retargeted to a distant vertex -> the relation list
#   --fan          the naive A0-only fan instead of the spec's 7 -> the relation list
#   --one-cap      drop the bottom cap                -> closed / Euler / cap count
#   --swap-mats    put the caps on the red slot       -> the material census

import math
import os
import sys
import traceback

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

OUT_DIR = os.environ.get("RING_BRIDGE_OUT",
                         r"D:\BlenderRobloxTestProjects\RingBridge18_24")
NAME = "RingBridge18_24"
SPU = trg.STUDS_PER_UNIT
TOL = 2e-3

# Same constants as the build, restated rather than imported: if the build is
# edited and this is not, the two disagree out loud instead of the check quietly
# moving its own goalposts. (This is also why the twelve spec numbers are here in
# the spec's own units -- studs, after the round trip multiplies by SPU.)
N_SMALL, N_LARGE = 18, 24
R_SMALL, R_LARGE = 0.8, 1.2
Z_SMALL, Z_LARGE = 0.0, 1.0
GROUPS = 6

# The relations, verbatim (item 5). Offset 3 is the next group's A0.
BRIDGE = [
    [("A", 0), ("B", 0), ("B", 1)],
    [("A", 0), ("A", 1), ("B", 2)],
    [("A", 0), ("B", 2), ("B", 1)],
    [("A", 1), ("A", 2), ("B", 3)],
    [("A", 1), ("B", 3), ("B", 2)],
    [("A", 2), ("A", 3), ("B", 4)],
    [("A", 2), ("B", 4), ("B", 3)],
]

MAT_CAP, MAT_BRIDGE = 0, 1
CAP_TRIS = (N_SMALL - 2, N_LARGE - 2)     # 16 + 22, what a triangulated n-gon ships
# Item 6's two colours, also restated here rather than imported. Blue end faces, red
# bridge -- deliberately far apart on purpose, so a swapped-material mutation cannot be
# rescued by two similar colours.
CAP_RGB = (0.045, 0.13, 0.80)
BRIDGE_RGB = (0.80, 0.055, 0.045)

FAILS = []
LINES = []


def ok(label, good, detail=""):
    LINES.append("  %-52s %s %s" % (label, "ok  " if good else "FAIL", detail))
    if not good:
        FAILS.append(label)
    return good


def need(label, good, detail=""):
    """ok(), but a failure here invalidates everything downstream."""
    if not ok(label, good, detail):
        print("\n".join(LINES))
        print("CHECK aborted: %s" % label)
        sys.exit(1)


def done():
    print("\n".join(LINES))
    print("CHECK %d ok, %d failed" % (len(LINES) - len(FAILS), len(FAILS)))
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
    sys.exit(1 if FAILS else 0)


# ---------------------------------------------------------------- loaders
def load_fbx(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, global_scale=1.0)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def load_glb(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def welded(obj):
    """Vertex positions in STUDs, coincident ones merged, plus faces.

    Two jobs. The units: every number below is a stud and the file is not, so the
    scale is applied here once, rather than at each comparison. The welding: glTF
    has nowhere to put a polygon and splits a vertex wherever a corner's
    attributes differ per face, so the shipped .glb reports open edges that are
    artefacts of the question. Weld by position and both formats answer the same.
    """
    mw = obj.matrix_world
    pts, key_of, faces = [], {}, []
    for p in obj.data.polygons:
        idx = []
        for vi in p.vertices:
            w = mw @ obj.data.vertices[vi].co
            k = (round(w.x * SPU, 5), round(w.y * SPU, 5), round(w.z * SPU, 5))
            if k not in key_of:
                key_of[k] = len(pts)
                pts.append(k)
            idx.append(key_of[k])
        faces.append((tuple(idx), p.material_index))
    return pts, faces


# ---------------------------------------------------------------- geometry
def rad(p):
    return math.hypot(p[0], p[1])


def azim(p):
    return math.degrees(math.atan2(p[1], p[0])) % 360.0


def ngon_area(n, r):
    return 0.5 * n * r * r * math.sin(2.0 * math.pi / n)


def slot_rgb(mat):
    """The colour the FILE carries, read back from the imported material.

    Prefers the Principled BSDF's Base Color -- that is the input both exporters write --
    and only falls back to `diffuse_color`, which is the viewport field a Workbench
    render reads. Reading just the latter would pass a material that renders correctly
    and exports white, which is the failure the picture could never show.
    """
    if mat.use_nodes and mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED" and "Base Color" in n.inputs:
                c = n.inputs["Base Color"].default_value
                return (c[0], c[1], c[2])
    c = mat.diffuse_color
    return (c[0], c[1], c[2])


def planar_area(pts, faces):
    """Total 2D area of a set of faces that all lie in ONE Z plane.

    Shoelace per face, in the XY plane. A single 18-gon and the 16 triangles that
    triangulate it give the same number -- which is the whole point: this is how the
    cap can be asserted without asserting anything about the file format.
    """
    total = 0.0
    for f in faces:
        s = 0.0
        for k in range(len(f)):
            x1, y1 = pts[f[k]][0], pts[f[k]][1]
            x2, y2 = pts[f[(k + 1) % len(f)]][0], pts[f[(k + 1) % len(f)]][1]
            s += x1 * y2 - x2 * y1
        total += abs(s) * 0.5
    return total


def prismatoid_volume():
    """The volume the SPEC describes, from the z=0.5 mid-section.

    Exact for this solid: every vertex lies in one of two parallel planes. The
    mid-section is the 42-gon through the lateral edges' midpoints, walked in the
    same boundary order the build uses.
    """
    A = [(R_SMALL * math.cos(2 * math.pi * k / N_SMALL),
          R_SMALL * math.sin(2 * math.pi * k / N_SMALL), Z_SMALL)
         for k in range(N_SMALL)]
    B = [(R_LARGE * math.cos(2 * math.pi * k / N_LARGE),
          R_LARGE * math.sin(2 * math.pi * k / N_LARGE), Z_LARGE)
         for k in range(N_LARGE)]
    chain = [(0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)]
    mids = []
    for g in range(GROUPS):
        for (sa, sb) in chain:
            a, b = A[(3 * g + sa) % N_SMALL], B[(4 * g + sb) % N_LARGE]
            p = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
            if not mids or max(abs(p[i] - mids[-1][i]) for i in range(3)) > 1e-9:
                mids.append(p)
    if max(abs(mids[-1][i] - mids[0][i]) for i in range(3)) < 1e-9:
        mids.pop()
    area = 0.0
    for k in range(len(mids)):            # shoelace
        p, q = mids[k], mids[(k + 1) % len(mids)]
        area += p[0] * q[1] - q[0] * p[1]
    area *= 0.5
    h = Z_LARGE - Z_SMALL
    return h * (ngon_area(N_SMALL, R_SMALL) + 4.0 * area
                + ngon_area(N_LARGE, R_LARGE)) / 6.0, area


def divergence(pts, faces):
    """Unsigned-volume-sensitive: only a consistently OUTWARD mesh gives +V."""
    v = 0.0
    for f, _ in faces:
        p = pts[f[0]]
        for k in range(1, len(f) - 1):
            q, r = pts[f[k]], pts[f[k + 1]]
            v += (p[0] * (q[1] * r[2] - q[2] * r[1])
                  - p[1] * (q[0] * r[2] - q[2] * r[0])
                  + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
    return v


# ---------------------------------------------------------------- the check
def check(tag, path, loader):
    print("\n==== %s ====" % tag)
    need("%s: file exists" % tag, os.path.exists(path), path)
    objs = loader(path)
    need("%s: exactly one mesh object" % tag, len(objs) == 1,
         "%d objects" % len(objs))
    obj = objs[0]
    pts, faces = welded(obj)

    # ---- 3. two coaxial rings ------------------------------------------------
    need("%s: 42 unique vertices (18 + 24)" % tag, len(pts) == N_SMALL + N_LARGE,
         "%d" % len(pts))
    lo = [p for p in pts if abs(p[2] - Z_SMALL) < TOL]
    hi = [p for p in pts if abs(p[2] - Z_LARGE) < TOL]
    need("%s: vertices split across exactly the two ring planes" % tag,
         len(lo) == N_SMALL and len(hi) == N_LARGE,
         "z=0 -> %d, z=1 -> %d" % (len(lo), len(hi)))
    rlo = sorted(rad(p) for p in lo)
    rhi = sorted(rad(p) for p in hi)
    ok("%s: 18-gon circumradius == %.4f" % (tag, R_SMALL),
       abs(rlo[0] - R_SMALL) < TOL and abs(rlo[-1] - R_SMALL) < TOL,
       "measured %.6f..%.6f" % (rlo[0], rlo[-1]))
    ok("%s: 24-gon circumradius == %.4f" % (tag, R_LARGE),
       abs(rhi[0] - R_LARGE) < TOL and abs(rhi[-1] - R_LARGE) < TOL,
       "measured %.6f..%.6f" % (rhi[0], rhi[-1]))
    # Coaxial: both rings share the axis, i.e. their centroids coincide at x=y=0.
    ok("%s: coaxial (both centroids on the Z axis)" % tag,
       max(abs(sum(p[i] for p in lo) / len(lo)) for i in (0, 1)) < TOL
       and max(abs(sum(p[i] for p in hi) / len(hi)) for i in (0, 1)) < TOL)

    # ---- 5. the 42 triangles ARE the operator's seven relations --------------
    # Rebuild each relation as a vertex POSITION SET, then look for a face with
    # exactly that set. Position-based on purpose: the weld renumbers everything,
    # so index arithmetic here would be measuring the weld, not the bridge.
    def pos_of(ring, g, off):
        if ring == "A":
            z, r, n, base = Z_SMALL, R_SMALL, N_SMALL, 3 * g
        else:
            z, r, n, base = Z_LARGE, R_LARGE, N_LARGE, 4 * g
        a = 2.0 * math.pi * ((base + off) % n) / n
        return (round(r * math.cos(a), 5), round(r * math.sin(a), 5), round(z, 5))

    lookup = {}
    for i, p in enumerate(pts):
        lookup[(round(p[0], 5), round(p[1], 5), round(p[2], 5))] = i

    missing, misplaced = [], 0
    for g in range(GROUPS):
        for rel in BRIDGE:
            want = set()
            for (ring, off) in rel:
                key = pos_of(ring, g, off)
                if key not in lookup:
                    missing.append("%s%d" % (ring, off))
                    continue
                want.add(lookup[key])
            if len(want) != 3:
                continue
            if not any(set(f) == want and len(f) == 3 for f, _ in faces):
                misplaced += 1
    ok("%s: all 42 of the operator's relations are faces" % tag,
       not missing and misplaced == 0,
       "missing verts %d, relations with no matching face %d"
       % (len(missing), misplaced))

    # ---- classify by MATERIAL, never by side count ---------------------------
    # MEASURED (this is why the first version of this file failed 9 lines): the two
    # files do NOT ship the same faces. The FBX has a polygon type, so the importer
    # rebuilds each end face as ONE 18-gon and ONE 24-gon; glTF has none, so it ships
    # 16 + 22 triangles in their place. Counting triangles therefore answers a question
    # about the FILE FORMAT -- `len(f) == 3` picked up the 38 cap triangles glTF
    # synthesises and read "80 bridge triangles". The material slot is the same in both
    # files, and slot is also literally what item 6 coloured.
    cap_faces = [f for f, m in faces if m == MAT_CAP]
    br_faces = [f for f, m in faces if m == MAT_BRIDGE]
    need("%s: every face carries one of the two slots" % tag,
         bool(faces) and len(cap_faces) + len(br_faces) == len(faces),
         "%d cap + %d bridge of %d" % (len(cap_faces), len(br_faces), len(faces)))

    # ---- 5, restated on the material ----------------------------------------
    ok("%s: exactly 42 bridge faces, every one a triangle" % tag,
       len(br_faces) == N_SMALL + N_LARGE and all(len(f) == 3 for f in br_faces),
       "%d faces, %d of them triangles" % (len(br_faces),
                                           sum(1 for f in br_faces if len(f) == 3)))
    # Every triangle's corners are ring vertices -- the bridge invents nothing.
    ok("%s: every bridge triangle uses only the 42 ring vertices" % tag,
       all(0 <= i < len(pts) for f in br_faces for i in f))
    # The 3:4 rule: group g takes small corners 3g, 3g+1, 3g+2 and large corners
    # 4g..4g+3. Asked of the CORNER INDEX, which is first recovered by snapping the
    # azimuth to the nearest exact corner angle -- a bare `azim(p) // 60` cannot answer
    # this. MEASURED, twice: the corners sit exactly ON the 60-deg boundaries (the
    # 24-gon's 15-deg spacing divides 60 four ways), atan2 returns 59.999999 for a corner
    # scheduled at 60, and Python's round() is banker's rounding -- round(1.5) == 2 --
    # so the partition read [3, 4, 5, 3, 5, 4]. Snapping to the ring's own spacing leaves
    # ~10 deg of margin against a float error of ~1e-5.
    def corner(n, p):
        return int(round(azim(p) / (360.0 / n))) % n

    per_group = [
        (sorted(corner(N_SMALL, p) for p in lo if corner(N_SMALL, p) * GROUPS // N_SMALL == g),
         sorted(corner(N_LARGE, p) for p in hi if corner(N_LARGE, p) * GROUPS // N_LARGE == g))
        for g in range(GROUPS)]
    ok("%s: group g is small 3g..3g+2 and large 4g..4g+3, for all six g" % tag,
       per_group == [([3 * g, 3 * g + 1, 3 * g + 2],
                      [4 * g, 4 * g + 1, 4 * g + 2, 4 * g + 3])
                     for g in range(GROUPS)],
       "%s" % (per_group,))

    # ---- 4. the end faces ----------------------------------------------------
    # Item 4 says both end faces are KEPT as n-gons. Only the .blend can hold a
    # polygon, so that is asserted against the .blend (n_gon_caps_in_blend below).
    # What the exports can be asked is the format-independent half of the same claim:
    #   * the cap is the WHOLE ring -- its boundary is all 18 (resp. 24) corners and it
    #     has the ring's full area. A partial fan would still be "a cap face" by
    #     material, and a face count would not have caught it;
    #   * each cap face is planar, i.e. every corner of it lies in one Z plane.
    # The shipped face count is printed (1 + 1 for FBX, 16 + 22 for glTF) because it is
    # a fact about the file, and asserting it would be asserting the format.
    cap_lo = [f for f in cap_faces if all(abs(pts[i][2] - Z_SMALL) < TOL for i in f)]
    cap_hi = [f for f in cap_faces if all(abs(pts[i][2] - Z_LARGE) < TOL for i in f)]
    ok("%s: each end face is planar (every cap face in one Z plane)" % tag,
       bool(cap_faces) and len(cap_lo) + len(cap_hi) == len(cap_faces),
       "%d faces at z=0, %d at z=1, of %d" % (len(cap_lo), len(cap_hi), len(cap_faces)))
    print("  [%s] cap shipped as %d + %d faces" % (tag, len(cap_lo), len(cap_hi)))

    ring_lo = {lookup[k] for k in (pos_of("A", 0, o) for o in range(N_SMALL))
               if k in lookup}
    ring_hi = {lookup[k] for k in (pos_of("B", 0, o) for o in range(N_LARGE))
               if k in lookup}
    used_lo = {i for f in cap_lo for i in f}
    used_hi = {i for f in cap_hi for i in f}
    ok("%s: the z=0 end face spans all 18 corners of the small ring" % tag,
       used_lo == ring_lo and len(ring_lo) == N_SMALL,
       "%d of %d" % (len(used_lo), len(ring_lo)))
    ok("%s: the z=1 end face spans all 24 corners of the large ring" % tag,
       used_hi == ring_hi and len(ring_hi) == N_LARGE,
       "%d of %d" % (len(used_hi), len(ring_hi)))
    a_lo, a_hi = planar_area(pts, cap_lo), planar_area(pts, cap_hi)
    want_lo, want_hi = ngon_area(N_SMALL, R_SMALL), ngon_area(N_LARGE, R_LARGE)
    ok("%s: the z=0 end face has the 18-gon's area" % tag,
       abs(a_lo - want_lo) < 1e-4 * want_lo,
       "%.6f vs %.6f" % (a_lo, want_lo))
    ok("%s: the z=1 end face has the 24-gon's area" % tag,
       abs(a_hi - want_hi) < 1e-4 * want_hi,
       "%.6f vs %.6f" % (a_hi, want_hi))

    # ---- 6. materials --------------------------------------------------------
    # NOT "the bridge faces are slot 1": the classification above DEFINED br_faces that
    # way, so restating it asserts the definition, not the asset. What is worth asking is
    # whether the two slots carry the two COLOURS item 6 named -- blue end faces, red
    # bridge -- read back out of the file. The Workbench render cannot stand in for this:
    # it reads `diffuse_color`, while what the exporters write is the Principled BSDF's
    # Base Color, and the two are separate fields.
    slots = obj.data.materials
    ok("%s: two material slots shipped" % tag, slots is not None and len(slots) == 2,
       ", ".join("%d=%s" % (i, m.name) for i, m in enumerate(slots or [])))
    ok("%s: the two slots are distinct" % tag,
       MAT_CAP != MAT_BRIDGE and len(slots or []) > max(MAT_CAP, MAT_BRIDGE))
    errs = []
    for idx, want, label in ((MAT_CAP, CAP_RGB, "cap"), (MAT_BRIDGE, BRIDGE_RGB, "bridge")):
        if idx >= len(slots or []):
            errs.append("no slot %d for the %s" % (idx, label))
            continue
        got = slot_rgb(slots[idx])
        if max(abs(got[k] - want[k]) for k in range(3)) > 0.02:
            errs.append("%s slot %d: got %s, want %s" % (
                label, idx, ["%.3f" % v for v in got], ["%.3f" % v for v in want]))
        else:
            print("  [%s] %s = slot %d %s" % (
                tag, label, idx, ["%.3f" % v for v in got]))
    ok("%s: slot %d is blue and slot %d is red, as stored in the file" % (
        tag, MAT_CAP, MAT_BRIDGE), not errs, "; ".join(errs))

    # ---- orientation + geometry, by two routes -------------------------------
    v_p, am = prismatoid_volume()
    v_d = divergence(pts, faces)
    ok("%s: volume from the mid-section matches the solid" % tag,
       abs(v_d - v_p) < 1e-4 * v_p,
       "spec %.6f, divergence %.6f, delta %.2e" % (v_p, v_d, abs(v_d - v_p)))
    # Closed, stated so both formats can answer it: triangulate every face (n-2 each) and
    # count, because "how many faces" is the format question that broke this file --
    # FBX ships 44 faces that make 80 triangles, glTF ships 80 already-triangular faces.
    ntri_total = sum(len(f) - 2 for f, _ in faces)
    ok("%s: the solid is closed (42 + 16 + 22 triangles)" % tag,
       ntri_total == (N_SMALL + N_LARGE) + CAP_TRIS[0] + CAP_TRIS[1],
       "%d faces -> %d triangles" % (len(faces), ntri_total))
    # Euler: V - E + F = 2. E from the shipped face list, not from the build.
    ecount = len({tuple(sorted((f[k], f[(k + 1) % len(f)])))
                  for f, _ in faces for k in range(len(f))})
    ok("%s: Euler characteristic 2 (closed 2-manifold)" % tag,
       len(pts) - ecount + len(faces) == 2,
       "V=%d E=%d F=%d -> %d" % (len(pts), ecount, len(faces),
                                 len(pts) - ecount + len(faces)))
    # A bounding box of 2.4 x 2.4 x 1.0 is the spec in one line.
    dx = max(p[0] for p in pts) - min(p[0] for p in pts)
    dy = max(p[1] for p in pts) - min(p[1] for p in pts)
    dz = max(p[2] for p in pts) - min(p[2] for p in pts)
    ok("%s: bounding box 2.4000 x 2.4000 x 1.0000" % tag,
       abs(dx - 2 * R_LARGE) < TOL and abs(dy - 2 * R_LARGE) < TOL
       and abs(dz - (Z_LARGE - Z_SMALL)) < TOL,
       "%.4f x %.4f x %.4f" % (dx, dy, dz))
    print("  [%s] prismatoid %.6f, mid-section area %.6f" % (tag, v_p, am))


def n_gon_caps_in_blend():
    """Item 4 says the end faces are KEPT as n-gons. Both Blender files can hold a
    polygon -- the FBX can and does (measured: its importer rebuilds 1 + 1 face), only
    the glTF cannot. The .blend is the authoring artifact, so it is where the claim is
    asked in its original form; the exports answer it through area and corners, which
    survive triangulation."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, NAME + ".blend"))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    need("blend: one mesh object", len(objs) == 1, "%d" % len(objs))
    polys = objs[0].data.polygons
    n18 = sum(1 for p in polys if len(p.vertices) == N_SMALL)
    n24 = sum(1 for p in polys if len(p.vertices) == N_LARGE)
    ntri = sum(1 for p in polys if len(p.vertices) == 3)
    ok("blend: the 18-gon end face is ONE face", n18 == 1, "%d" % n18)
    ok("blend: the 24-gon end face is ONE face", n24 == 1, "%d" % n24)
    ok("blend: 42 bridge triangles", ntri == N_SMALL + N_LARGE, "%d" % ntri)
    ok("blend: 44 faces total, no bevel added", len(polys) == 2 + N_SMALL + N_LARGE,
       "%d" % len(polys))


def main():
    for tag, fname, loader in (("FBX", NAME + ".fbx", load_fbx),
                               ("GLB", NAME + ".glb", load_glb)):
        check(tag, os.path.join(OUT_DIR, fname), loader)
    n_gon_caps_in_blend()
    done()


# The try/except is load-bearing, and it is not about this file being fragile.
# MEASURED on this Blender (5.1.2): a script run with `--background
# --factory-startup --python` that RAISES exits with status 0. sys.exit(1) and
# os._exit(1) both exit 1; an ordinary exception does not. Without this guard a
# crash and a pass are byte-identical at the shell.
try:
    main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    print("\n".join(LINES))
    print("CHECK CRASHED -- treated as a failure (see the traceback above)")
    sys.exit(1)
