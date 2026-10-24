# cbl_laser_mk4_check.py -- reopen the EXPORTED CblLaserMk4 files and measure them.
#
# The build loop is not evidence (CLAUDE.md 0.6 / 0.37): the numbers cbl_laser_mk4.py
# prints describe the scene it had in memory, and the thing that reaches Studio is
# the .fbx (or the .glb). Everything below reads the FILES.
#
# WHAT ONLY THIS CAN SEE
#   1. The scale survived the trip. The exporters write at 1/5.902; the glTF path
#      has no global_scale and is scaled by hand, which is where the 2026-10-04
#      defect lived (meshes scaled, spacing not). The assembly box below is the
#      anchor: it must land on 64.592 x 23.040 x 27.360 STUDs.
#   2. The four parts are still four nodes. An exporter that joins them hands
#      back one object, and in Studio that is one unweldable brick.
#   3. Every origin is still (0,0,0). All four parts are authored with their
#      origin ON the trunnion/barrel axis, which IS the pivot; an exporter that
#      bakes the transform into the geometry collapses the origin onto the
#      bounding-box centre and the part can never turn about the right line.
#   4. The per-material split survived -- measured as a BOX PER MATERIAL, which
#      is the same measurement _tools/apply_cbl_laser_mk4_materials.luau will use
#      in Studio. If the material names came through but face assignment did not,
#      this is where it shows.
#
# BOTH FORMATS, ON PURPOSE. Two exporters writing one scene are two independent
# witnesses; the .fbx branch passing says nothing about the .glb. The operator
# imports the .fbx, but the .glb is the archive copy.
#
# THE CONSTANTS ARE TYPED FROM cbl_laser_mk4.py's SOURCE, not read back out of an
# export -- comparing a file against itself is a tautology (DECISIONS 95).
#
# TOLERANCE. 0.02 studs on every box. Derivation, so this is not a knob turned
# until the light went green: the delivered bevels are 0.040 / 0.035 / 0.029 /
# 0.019 studs and a bevel cuts INWARD. Where a box edge is a PLANE (every one on
# this asset except the Core's +X) the bevel shrinks the face without moving the
# plane, and the measured diff is exactly 0.0000 -- see the run. Where the edge is
# a POINT ON A CURVE the bevel replaces that vertex with a face inside it: the
# Core's +X is the aperture torus at 16.95 + 0.11 and measures 0.0086 short, which
# is less than that part's 0.019 bevel. So the tolerance covers ONE bevel offset.
# The failures this must catch are 5.60 studs (the 1.6943x glTF scale error) and
# 5.90 studs (spacing left at 1.0) -- 280x the line.
#
# WATERTIGHTNESS IS ASKED TWICE, AND THE INDEX VERSION IS FBX-ONLY. open_edges is
# counted on edge_keys, which are VERTEX INDICES, and the glTF importer splits
# every vertex that carries more than one normal or one material slot -- so on the
# .glb every seam reads as a hole (35600 on the Body alone) while the surface is
# closed. That is a fact about the importer, not about the file (CLAUDE.md 0.18).
# The .glb gets the welded count instead: same question asked of positions rather
# than of indices. The welded count runs on BOTH, and it counts ODD edge uses --
# a closed surface has every edge used an even number of times, while an edge used
# four times is two surfaces landing on each other. See welded_edges() for the
# 48 measured faces that made the original "== 2" version lie.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python "D:\rblxTRGproject\_tools\blender\cbl_laser_mk4_check.py"
#
# Point it at a broken export to prove it goes red (CBL_MK4_OUT=<dir>).
import os
import re
import sys
import traceback

import bpy
from mathutils import Vector

sys.path.insert(0, r"D:\rblxTRGproject\_tools\blender")
import trg  # noqa: E402

OUT_DIR = os.environ.get("CBL_MK4_OUT", r"D:\BlenderRobloxTestProjects\CblLaserMk4")
SPU = trg.STUDS_PER_UNIT
S = 1.60                       # design studs -> delivered studs, from the build
NAME = "CblLaserMk4"
TOL = 0.02                     # studs; see the header for the derivation

# Design studs, from cbl_laser_mk4.py. Named after the source's own identifiers so
# a reader can check each one against the line that made it.
X_BACK, X_FRONT = -18.30, 22.00
X_SHROUD1 = 14.60
REAR_BOSS = 0.07               # dark boss at X_BACK - 0.07 is the rearmost point
PLATE_X0, PLATE_X1 = -8.0, 5.5
PLATE_HY = 7.2
PLATE_Z0 = -9.40
ARM_TOP = -1.20 + 7.00 / 2.0   # yoke arm: centre z -1.20, 7.00 tall
R_FIN_O = 5.25                 # fin stack outer radius = the widest hull ring
DRUM_Z1 = 7.70                 # capacitor drum top = the highest point
PRONG_X0 = 16.70               # arc_prong root
CORE_X0 = -9.70                # plasma tube rear cap
CORE_X1 = 16.95 + 0.11         # outermost aperture spoke, box half-width 0.11

# Per object: `edges` are (material, axis 0..2, 0=min|1=max, design studs).
#
# The OWNER of each edge is named, because "whichever material reaches furthest"
# is not the same question. On the Body, Hull's +X is X_SHROUD1 (14.60) while Dark
# reaches X_BELL1 (17.15) -- asking for the furthest material would compare Hull's
# constant against Dark's face and report a 2.55-stud error on a correct file.
PARTS = {
    "CblLaserMk4Mount": {
        "edges": [("Mk4Hull", 0, 0, PLATE_X0), ("Mk4Hull", 0, 1, PLATE_X1),
                  ("Mk4Hull", 1, 0, -PLATE_HY), ("Mk4Hull", 1, 1, PLATE_HY),
                  ("Mk4Hull", 2, 0, PLATE_Z0), ("Mk4Hull", 2, 1, ARM_TOP)],
        "mats": {"Mk4Hull", "Mk4Dark", "Mk4Brass", "Mk4Hazard"},
        "tris": 4532,
    },
    "CblLaserMk4Body": {
        "edges": [("Mk4Hull", 0, 0, X_BACK), ("Mk4Hull", 0, 1, X_SHROUD1),
                  ("Mk4Hull", 1, 0, -R_FIN_O), ("Mk4Hull", 1, 1, R_FIN_O),
                  ("Mk4Hull", 2, 0, -R_FIN_O), ("Mk4Hull", 2, 1, R_FIN_O)],
        "mats": {"Mk4Hull", "Mk4Dark", "Mk4Brass", "Mk4Hazard", "Mk4Cyan", "Mk4Amber"},
        "tris": 29328,
    },
    "CblLaserMk4Prongs": {
        "edges": [("Mk4Brass", 0, 0, PRONG_X0), ("Mk4Brass", 0, 1, X_FRONT)],
        "mats": {"Mk4Brass"},
        "tris": 1332,
    },
    "CblLaserMk4Core": {
        "edges": [("Mk4Cyan", 0, 0, CORE_X0), ("Mk4Cyan", 0, 1, CORE_X1)],
        "mats": {"Mk4Cyan", "Mk4White"},
        "tris": 38812,
    },
}
ASSEMBLY = ((X_BACK - REAR_BOSS, X_FRONT),
            (-PLATE_HY, PLATE_HY),
            (PLATE_Z0, DRUM_Z1))

FAILS = []
CHECKS = [0]


def tally(ok):
    CHECKS[0] += 1
    if not ok:
        FAILS.append(1)


def norm(name):
    """Material names come back with .001-style suffixes when the importer makes
    a new datablock instead of reusing one; the suffix is the importer's business,
    not the asset's."""
    return re.sub(r"\.\d+$", "", name or "")


def load_fbx(path):
    trg.new_scene()
    bpy.ops.import_scene.fbx(filepath=path, global_scale=1.0)
    return {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}


def load_glb(path):
    # No global_scale -- glTF has none. That is exactly why this branch exists.
    trg.new_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    return {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}


def mat_boxes(obj):
    """Per-material world-space box and face count. The box is the fact the Studio
    material script matches on, so measuring it here measures that script's input."""
    mesh = obj.data
    per = {}
    for poly in mesh.polygons:
        slot = mesh.materials[poly.material_index] if poly.material_index < len(mesh.materials) else None
        key = norm(slot.name) if slot else "<no-slot>"
        entry = per.setdefault(key, [Vector((1e18,) * 3), Vector((-1e18,) * 3), 0])
        entry[2] += 1
        for vi in poly.vertices:
            co = obj.matrix_world @ mesh.vertices[vi].co
            for i in range(3):
                entry[0][i] = min(entry[0][i], co[i])
                entry[1][i] = max(entry[1][i], co[i])
    return per


def welded_edges(obj, tol=1e-4):
    """Edge-use counts on welded POSITIONS instead of on vertex indices.

    The glTF importer duplicates a vertex once per (normal, material) pair, so an
    index-based count reports every hard edge as a hole. Collapsing positions
    first asks the question the index count was meant to ask. `tol` is in file
    units; 1e-4 of a file unit is 0.0006 studs, far below any real gap on this
    asset and far above float32 noise.

    Returns (open, doubled). A surface is closed iff every edge is used an EVEN
    number of times, so `open` counts ODD uses and `doubled` counts edges used
    more than twice.

    MEASURED 2026-10-24, and the reason the criterion is parity rather than
    "== 2": the first version of this function counted every non-2 as open and
    reported 48 holes on the Body that were not holes. All 48 sat at x = 23.36
    (design X_SHROUD1), and each was used 4 times -- by a 48-gon Hull cap AND a
    48-gon Dark cap at the same station and radius, i.e. the shroud lathe's
    cap_top and the aperture bell lathe's cap_bottom land on top of each other.
    Face to face, opposite windings, interior, invisible. "Used twice more than
    it should be" and "used once" are different failures and only the second one
    is a hole.
    """
    mesh = obj.data
    key = {}
    ident = []
    for v in mesh.vertices:
        w = obj.matrix_world @ v.co
        k = (round(w.x / tol), round(w.y / tol), round(w.z / tol))
        ident.append(key.setdefault(k, len(key)))
    use = {}
    for poly in mesh.polygons:
        ids = [ident[i] for i in poly.vertices]
        for i in range(len(ids)):
            a, b = ids[i], ids[(i + 1) % len(ids)]
            if a == b:
                continue
            e = (a, b) if a < b else (b, a)
            use[e] = use.get(e, 0) + 1
    return (sum(1 for c in use.values() if c % 2 == 1),
            sum(1 for c in use.values() if c > 2))


def box_of(objs):
    lo = Vector((1e18,) * 3)
    hi = Vector((-1e18,) * 3)
    for o in objs.values():
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo * SPU, hi * SPU


def check_end(ok, label, detail=""):
    tally(ok)
    print("  %-34s %s%s" % (label, "OK" if ok else "*** FAIL ***",
                            ("  " + detail) if detail else ""))


def main():
    seen = {}
    for fmt, load in (("fbx", load_fbx), ("glb", load_glb)):
        path = os.path.join(OUT_DIR, "%s.%s" % (NAME, fmt))
        if not os.path.exists(path):
            tally(False)
            print("MISSING %s" % path)
            continue
        objs = load(path)
        print("FILE %s.%s  nodes=%d  (%s)"
              % (NAME, fmt, len(objs), ", ".join(sorted(objs)) or "none"))

        check_end(set(objs) == set(PARTS), "node names == the four parts",
                  "missing=%s extra=%s" % (sorted(set(PARTS) - set(objs)),
                                           sorted(set(objs) - set(PARTS))))

        lo, hi = box_of(objs)
        for i, axis in enumerate("xyz"):
            for end, want, got in ((0, ASSEMBLY[i][0] * S, lo[i]),
                                   (1, ASSEMBLY[i][1] * S, hi[i])):
                d = abs(want - got)
                check_end(d <= TOL, "assembly %s %s" % (axis, "min" if end == 0 else "max"),
                          "want %9.4f got %9.4f diff %.4f" % (want, got, d))

        for name in sorted(PARTS):
            spec = PARTS[name]
            if name not in objs:
                continue
            o = objs[name]
            st = trg.measure(o)
            # trg.measure reads the MESH in the object's own frame. All origins are
            # at the world origin here, but say so rather than assume it.
            loc = o.matrix_world.translation * SPU
            check_end(loc.length <= 1e-3, "%s origin at (0,0,0)" % name,
                      "at (%.4f,%.4f,%.4f)" % tuple(loc))

            mb = mat_boxes(o)
            got_mats = set(mb)
            check_end(got_mats == spec["mats"], "%s materials" % name,
                      "missing=%s extra=%s" % (sorted(spec["mats"] - got_mats),
                                               sorted(got_mats - spec["mats"])))

            for mat, axis, end, design in spec["edges"]:
                want = design * S
                if mat not in mb:
                    check_end(False, "%s %s %s %s" % (name, mat, "xyz"[axis],
                                                      "min" if end == 0 else "max"),
                              "*** material absent ***")
                    continue
                got = mb[mat][end][axis] * SPU
                d = abs(want - got)
                check_end(d <= TOL, "%s %s %s %s" % (name, mat, "xyz"[axis],
                                                      "min" if end == 0 else "max"),
                          "want %9.4f got %9.4f diff %.4f" % (want, got, d))

            d = abs(st["tris"] - spec["tris"])
            check_end(d == 0, "%s triangles" % name,
                      "want %d got %d" % (spec["tris"], st["tris"]))
            w_open, w_doubled = welded_edges(o)
            if fmt == "fbx":
                check_end(st["open_edges"] == 0, "%s watertight (indices)" % name,
                          "open_edges=%d" % st["open_edges"])
            check_end(w_open == 0, "%s watertight (welded)" % name,
                      "welded open=%d doubled=%d  (index count: %d)"
                      % (w_open, w_doubled, st["open_edges"]))

            # The cross-format comparison needs the WORLD box, not just the local
            # size: a part that is translated in one exporter keeps both its size
            # and its triangle count, so size+tris alone let the `split` mutation
            # through untouched (measured 2026-10-24 -- 6 red lines, none of them
            # this row). The world box of an untranslated part still costs nothing
            # to carry, and it is the pair of numbers the operator's Studio
            # placement depends on.
            wlo, whi = box_of({name: o})
            seen.setdefault(name, {})[fmt] = (
                tuple(round(x * SPU, 4) for x in st["size"]), st["tris"],
                tuple(round(x, 4) for x in tuple(wlo) + tuple(whi)))

    # The two exporters must agree with each other as well as with the constants.
    # This needs no typed number at all, so nothing above can have tuned it.
    for name in sorted(set(PARTS) & set(seen)):
        got = seen[name]
        if "fbx" not in got or "glb" not in got:
            tally(False)
            print("  %-34s *** one format is missing ***" % name)
            continue
        (sf, tf, bf), (sg, tg, bg) = got["fbx"], got["glb"]
        d = max(abs(a - b) for a, b in zip(sf, sg))
        db = max(abs(a - b) for a, b in zip(bf, bg))
        check_end(d <= TOL and db <= TOL and tf == tg, "fbx vs glb %s" % name,
                  "dmax size %.4f  box %.4f studs  tris %d vs %d"
                  % (d, db, tf, tg))

    print("CHECK %d ok, %d failed" % (CHECKS[0] - len(FAILS), len(FAILS)))
    return 1 if FAILS else 0


_rc = 1
try:
    _rc = main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    _rc = 1
sys.exit(_rc)
