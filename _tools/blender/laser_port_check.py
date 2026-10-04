# Round-trip the two exported FBX files back through an importer and read them.
# The build loop is not evidence; this reads the FILE, which is what reaches
# Studio. Three things can only be seen from here:
#   - that the parts really are three separate nodes (not merged on export)
#   - that each node's ORIGIN survived the trip -- a gimbal whose origins got
#     baked to the bounding-box centre is a gimbal that cannot move
#   - that posing the yoke about its own axis actually carries the head, and that
#     the head lands where the arithmetic says
#
# AXES: this runs in Blender, so here pan is about Z and tilt is about Y. After
# import into Studio those become pan about Y and tilt about Z. Same joints.
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, r"D:\rblxTRGproject\_tools\blender")
import trg  # noqa: E402

OUT_DIR = r"D:\BlenderRobloxTestProjects\LaserPort"
SPU = trg.STUDS_PER_UNIT

# Design pivots, Blender frame -- typed from laser_port.py's source, NOT read back
# out of the export. The comparison between the two is the check.
#
# UNIT TRAP, hit once already: the FBX was written with global_scale = 1/5.902, so
# the FILE holds studs/5.902. Import at global_scale=1.0 and every raw number is in
# file units, not studs. Comparing a raw translation against a pivot typed in studs
# reports a 5.9x error that is entirely my own arithmetic -- the first run of this
# script said "*** BAKED ***" on two parts that were in fact exact. Convert, or die
# by a ruler that does not error. Same trap as CLAUDE.md 0.18.
def u(v):
    """studs -> file units, the frame the re-imported objects live in."""
    return Vector(v) / SPU


# A check that cannot go red is decoration (DECISIONS 205), so every comparison
# below reports through here and the script exits non-zero on any failure.
FAILS = []


def mark(ok, label):
    return label if ok else ("*** " + label + " ***")


def done():
    print("CHECK %d ok, %d failed" % (CHECKS[0] - len(FAILS), len(FAILS)))
    sys.exit(1 if FAILS else 0)


CHECKS = [0]


def tally(ok):
    CHECKS[0] += 1
    if not ok:
        FAILS.append(1)


PAN_PIVOT = Vector((0.66, 0.00, 0.12))
TILT_PIVOT = Vector((0.66, 0.00, 0.86))


def load(path):
    trg.new_scene()
    bpy.ops.import_scene.fbx(filepath=path, global_scale=1.0)
    return {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}


def pivot_about(pivot, angle, axis):
    return (Matrix.Translation(pivot) @ Matrix.Rotation(angle, 4, axis)
            @ Matrix.Translation(-pivot))


for tag in ("LaserEmitterPort", "LaserReceiverPort"):
    head_name = "LaserEmitterHead" if tag == "LaserEmitterPort" else "LaserReceiverHead"
    objs = load(os.path.join(OUT_DIR, tag + ".fbx"))
    print("FILE %s  nodes=%d  (%s)" % (tag, len(objs), ", ".join(sorted(objs))))
    for n, o in sorted(objs.items()):
        st = trg.measure(o)
        loc = o.matrix_world.translation * SPU
        print("  %-20s origin_studs=(%7.3f,%7.3f,%7.3f)  size_studs=%.2f x %.2f x %.2f  tris=%d"
              % (n, loc.x, loc.y, loc.z, st["size"][0] * SPU, st["size"][1] * SPU,
                 st["size"][2] * SPU, st["tris"]))
    for n, want in (("LaserPortBase", Vector((0.0, 0.0, 0.0))),
                    ("LaserPortYoke", PAN_PIVOT), (head_name, TILT_PIVOT)):
        if n in objs:
            d = (objs[n].matrix_world.translation - u(want)).length * SPU
            ok = d < 0.01
            tally(ok)
            print("  origin_gap_vs_design  %-18s %.4f studs %s"
                  % (n, d, mark(ok, "OK") if ok else mark(ok, "BAKED")))

    if head_name not in objs or "LaserPortYoke" not in objs:
        continue

    # --- pose, as a rigid chain about the pivots (the same recipe the README
    # gives the operator). Deliberately NOT via parenting: the check is that two
    # independent bodies, each rotated about its own origin, still form a joint.
    #
    # NOTE: do NOT check the head's ORIGIN here. Both pivots sit on the pan axis
    # (they differ only in Z), so panning leaves the origin exactly where it was --
    # correct, and useless as a test. What moves is a point ON the head away from
    # the axis, so this tracks the muzzle vertex.
    #
    # The two joints are checked in SEPARATE STAGES, because they have different
    # invariants. Tilt turns the head about a pin that is itself moved by the pan,
    # so measuring the muzzle's distance to the pin *after* the pan is measuring
    # against a pin that has swung away -- it would report a rigid motion as broken.
    # Tilt first (its invariant holds while the pin is still where it started),
    # then pan.
    yoke, head = objs["LaserPortYoke"], objs[head_name]
    pan_deg, tilt_deg = 40.0, 25.0
    pan, tilt = math.radians(pan_deg), math.radians(tilt_deg)
    pan_p, tilt_p = u(PAN_PIVOT), u(TILT_PIVOT)
    before = head.matrix_basis.copy()
    yoke_before = yoke.matrix_basis.copy()
    orb = max(range(len(head.data.vertices)), key=lambda i: head.data.vertices[i].co.x)
    local = head.data.vertices[orb].co.copy()
    p0 = (before @ local) * SPU


    def perp(vec, piv, keep):
        """Distance to the line through piv along the third axis, measured in the
        plane spanned by `keep`. A rotation about that line leaves this fixed."""
        d = Vector(vec) - Vector(piv)
        return Vector((d[keep[0]], d[keep[1]], 0.0)).length


    def rot_rel(now, then):
        return now.to_3x3() @ then.to_3x3().inverted()


    def off_by(got, want):
        return max(abs(a - b) for ra, rb in zip(got, want) for a, b in zip(ra, rb))


    print("  posing pan=%.0f tilt=%.0f deg, reading the transform back each stage:"
          % (pan_deg, tilt_deg))
    print("    origin_studs=(%7.3f,%7.3f,%7.3f)  (unchanged is CORRECT -- both pivots sit on the pan axis)"
          % tuple(x * SPU for x in before.translation))

    # STAGE 1 -- tilt alone, about the pin's own Y line.
    head.matrix_world = pivot_about(tilt_p, tilt, "Y") @ head.matrix_world
    bpy.context.view_layer.update()
    t1 = head.matrix_basis
    p1 = (t1 @ local) * SPU
    err = off_by(rot_rel(t1, before), Matrix.Rotation(tilt, 3, "Y"))
    d_pin_0, d_pin_1 = perp(p0, TILT_PIVOT, (0, 2)), perp(p1, TILT_PIVOT, (0, 2))
    r_ok, d_ok = err < 1e-4, abs(d_pin_0 - d_pin_1) < 1e-3
    tally(r_ok), tally(d_ok)
    print("    tilt: rot_vs_Ry(tilt) err=%.6f %s | muzzle %s -> %s | dist_to_pin_XZ %.4f -> %.4f %s"
          % (err, mark(r_ok, "OK") if r_ok else mark(r_ok, "WRONG AXIS"),
             "(%.3f,%.3f,%.3f)" % (p0.x, p0.y, p0.z), "(%.3f,%.3f,%.3f)" % (p1.x, p1.y, p1.z),
             d_pin_0, d_pin_1, mark(d_ok, "OK") if d_ok else mark(d_ok, "NOT RIGID")))

    # STAGE 2 -- pan, about the plate's vertical line. Measured from p1, NOT from p0:
    # the tilt has already changed the muzzle's distance to the pan axis (it lifts
    # the muzzle out of the plane), and blaming the pan for that would be measuring
    # the tilt twice. The pin travels with the pan, so only the pan invariant is
    # asked for here.
    yoke.matrix_world = pivot_about(pan_p, pan, "Z") @ yoke_before
    head.matrix_world = pivot_about(pan_p, pan, "Z") @ t1
    bpy.context.view_layer.update()
    t2 = head.matrix_basis
    p2 = (t2 @ local) * SPU
    err = off_by(rot_rel(t2, before), Matrix.Rotation(pan, 3, "Z") @ Matrix.Rotation(tilt, 3, "Y"))
    d_ax_1, d_ax_2 = perp(p1, PAN_PIVOT, (0, 1)), perp(p2, PAN_PIVOT, (0, 1))
    r_ok, d_ok = err < 1e-4, abs(d_ax_1 - d_ax_2) < 1e-3
    tally(r_ok), tally(d_ok)
    print("    pan:  rot_vs_Rz(pan)*Ry(tilt) err=%.6f %s | muzzle -> %s | dist_to_pan_axis_XY %.4f -> %.4f %s"
          % (err, mark(r_ok, "OK") if r_ok else mark(r_ok, "WRONG AXES"),
             "(%.3f,%.3f,%.3f)" % (p2.x, p2.y, p2.z),
             d_ax_1, d_ax_2, mark(d_ok, "OK") if d_ok else mark(d_ok, "NOT RIGID")))
    print("    muzzle swung %.3f studs total; the beam now leaves in a different direction."
          % (p0 - p2).length)

done()
