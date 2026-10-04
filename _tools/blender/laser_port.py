# laser_port.py -- a matched pair of steerable wall ports: one emits, one receives.
#
# The brief, first pass: "一个发射，一个接收". Second pass, after seeing it:
# "我希望是那种可以像摄像头那样动的激光发射、接收端口，现在这个版本只能往一个方向".
#
# WHY THE FIRST VERSION COULD NOT MOVE. Two reasons, and only one of them was
# geometric:
#
#   1. It was ONE mesh. A Roblox MeshPart is rigid -- no part of a mesh can turn
#      independently of the rest. Aiming needs at least two rigid bodies, so at
#      least two meshes.
#   2. The joint that was there was the wrong joint. The pin ran along Z, i.e.
#      vertically, through two arms that bracket the head from above and below.
#      Roof-and-floor arms joined by a vertical pin is a *pan* joint -- but the
#      head was welded to the yoke, so the pin aimed nothing. There was no tilt
#      joint at all.
#
# So this version is three bodies, and the geometry is arranged so each body's
# ORIGIN SITS ON ITS OWN AXIS OF ROTATION. That is the whole trick, and it is why
# the mesh data is authored in local coordinates and the object's `location` is
# used purely to show the assembly. In Roblox, a part turns about its own origin;
# if the origin is not on the pivot, setting CFrame swings the part through an arc
# instead of turning it in place.
#
#   LaserPortBase   fixed to the wall.  origin (0,0,0) = wall face centre.
#   LaserPortYoke   pans.  origin = on the vertical post at (PAN_X, 0, FLANGE_Z1),
#                   so it yaws about its own local Y after import.
#   LaserPort*Head  tilts. origin = on the pin at (PAN_X, 0, TILT_Z), so it
#                   pitches about its own local Z after import.
#
# Blender is Z-up and Roblox is Y-up; the FBX importer converts, so Blender's +Z
# (the pan post) becomes Roblox's +Y and Blender's +Y (the tilt pin) becomes
# Roblox's Z. Pan = rotate about local Y, tilt = rotate about local Z, and the
# optical axis stays on local X. Nothing needs re-deriving in Studio.
#
# TWO JOINTS, TWO PLUMBING PROBLEMS. The previous version ran rigid coolant tubes
# from the head all the way back to glands on the wall plate. That is a single
# rigid body spanning both pivots, so it would visibly tear the first time anyone
# aimed the thing. Coolant now stays INSIDE one body at a time: fittings on the
# base, a boss on the yoke, and a short visible stub on the head running from the
# barrel into its own trunnion. What happens *through* the joints is not modelled
# -- which is also how a real gimbal does it (hollow shaft), and it means nothing
# here deforms when the head turns.
#
# RANGES (see 81.3 in PROGRESS; do not take these as swept-volume proofs):
#   pan  about +-90 deg. The hard wall is the far tip of the hood: it sits 1.26
#        in front of the pan axis, so muzzle_x = 0.66 + 1.26*cos(a), and it stays
#        clear of the wall plane until a ~= 116 deg. 90 is chosen under that,
#        because the head is 0.68 wide and I did NOT sweep its corners.
#   tilt +-75 deg. This one is chosen, not derived -- nothing I checked stops it
#        short of ~120 deg, and a camera that points at the floor is not the
#        thing being built.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python "D:\rblxTRGproject\_tools\blender\laser_port.py"

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

NAME_E = "LaserEmitterPort"
NAME_R = "LaserReceiverPort"
OUT_DIR = r"D:\BlenderRobloxTestProjects\LaserPort"

# ---------------------------------------------------------------- base (fixed)
PLATE_T, PLATE_HALF = 0.22, 0.80      # 1.60 x 1.60 wall plate
BOLT_R, BOLT_HALF = 0.09, 0.56        # 0.15 clear of the plate edge
NECK_L, NECK_HALF = 0.46, 0.26        # standoff from the wall out to the post
PAN_X = 0.66                          # THE PAN AXIS: vertical, at (0.66, 0)
POST_R, POST_Z0, POST_Z1 = 0.27, -0.30, 0.02
FLANGE_R, FLANGE_Z0, FLANGE_Z1 = 0.42, 0.02, 0.12   # the turntable, fixed half
NECK_GX, NECK_GZ, FIT_R = 0.20, 0.00, 0.085         # coolant fittings on the neck

# ---------------------------------------------------------------- yoke (pans)
# Local origin is (PAN_X, 0, FLANGE_Z1). Every z below is measured from there.
HUB_R, HUB_Z1 = 0.34, 0.16            # rotating half of the turntable
HUB_TOP_R, HUB_TOP_Z = 0.24, 0.22
BAR_CX, BAR_L, BAR_HY, BAR_CZ, BAR_H = 0.04, 0.48, 0.85, 0.18, 0.16
ARM_CX, ARM_L, ARM_TY, ARM_HY = 0.04, 0.48, 0.18, 0.76
ARM_CZ, ARM_H = 0.58, 0.64            # z 0.26..0.90, so it clears the bar and the pin
TILT_Z = 0.86                         # THE TILT AXIS, world z (local 0.74)
PIN_R, PIN_HALF = 0.15, 0.88
CAP_R, CAP_Y0, CAP_Y1 = 0.19, 0.85, 0.99

# ---------------------------------------------------------------- head (tilts)
# Local origin is (PAN_X, 0, TILT_Z) -- on the pin. Head-local x = 0 is the pivot,
# so the barrel reaches -0.46 back and +1.26 forward of it. The pivot sits 36% of
# the way along the barrel, which is what stops a 1.72-long head from looking
# nose-heavy when it tilts.
HEAD_R = 0.46                          # barrel radius; the trunnion must clear it
FIN_R, FIN_PITCH, FIN_T = 0.62, 0.105, 0.055
TRUN_R, TRUN_Y0, TRUN_Y1 = 0.26, 0.42, 0.66   # tilts with the head, ends at the arm
HEAD_COOL_R = 0.075

# new_scene() wipes the file, so it has to run before any datablock exists -- a
# Material made above this line is a dangling handle by the time finish() reads it.
trg.new_scene()

M_MOUNT, M_BODY, M_DARK, M_COOL, M_EMIT, M_RECV = range(6)
MATERIALS = [
    trg.material("PortMount", (0.13, 0.14, 0.155), metallic=0.70, roughness=0.55),
    trg.material("PortBody", (0.42, 0.44, 0.47), metallic=0.85, roughness=0.38),
    trg.material("PortDark", (0.075, 0.080, 0.090), metallic=0.75, roughness=0.48),
    trg.material("PortCoolant", (0.58, 0.33, 0.15), metallic=0.90, roughness=0.30),
    trg.material("PortLensEmit", (0.95, 0.32, 0.10), metallic=0.0, roughness=0.25,
                 emission=(0.95, 0.32, 0.10)),
    trg.material("PortLensRecv", (0.16, 0.85, 0.42), metallic=0.0, roughness=0.25,
                 emission=(0.16, 0.85, 0.42)),
]


def fins(x0, count):
    """Square-tooth heat-sink rings, as teeth in the lathe profile rather than as
    separate discs -- same silhouette for a fraction of the geometry, one
    continuous surface, no seam where a disc would meet the barrel."""
    out = []
    for i in range(count):
        x = x0 + i * FIN_PITCH
        out += [(FIN_R, x), (FIN_R, x + FIN_T), (HEAD_R, x + FIN_T),
                (HEAD_R, x + FIN_PITCH)]
    return out


# --- emitter: body, five fins, a flared hood, and a RECESSED dish inside it. The
# recess is the point -- an aperture flush with the rim reads as a hole, a sunken
# one reads as a source.
EMITTER_BACK = [(0.26, -0.46), (0.42, -0.38), (HEAD_R, -0.26), (HEAD_R, 0.36)]
EMITTER_FRONT = fins(0.30, 5) + [
    (0.52, 0.93), (0.52, 1.04), (0.68, 1.14), (0.68, 1.26),
    (0.50, 1.26), (0.50, 1.12), (0.32, 1.02), (0.00, 1.00),
]
EMITTER_LENS = [(0.00, 1.03), (0.30, 1.02), (0.32, 1.05), (0.30, 1.09), (0.00, 1.12)]

# --- receiver: same body, three fins, a wide funnel. The funnel's inner wall is
# part of this lathe (the profile doubles back), so the mouth is a real cone
# instead of a disc glued on. Its fins start 0.10 further out than the emitter's:
# the arm ends at head-local 0.06, and 0.04 of clearance is a collision waiting
# for a float error.
RECEIVER_BACK = [(0.26, -0.46), (0.42, -0.38), (HEAD_R, -0.26), (HEAD_R, 0.20)]
RECEIVER_FRONT = fins(0.16, 3) + [
    (HEAD_R, 0.60), (0.72, 0.88), (0.78, 1.02),
    (0.64, 1.02), (0.60, 0.86), (0.30, 0.72), (0.00, 0.70),
]
RECEIVER_ABSORB = [(0.00, 0.72), (0.34, 0.86), (0.56, 1.02)]   # cap_top closes it
RECEIVER_TARGET = [(0.00, 0.96), (0.13, 0.98), (0.13, 1.06), (0.00, 1.08)]


def build_base():
    """Fixed to the wall. Local coords ARE world coords for this one."""
    bm = bmesh.new()
    with trg.layer(bm, M_MOUNT):
        trg.box(bm, (-PLATE_T / 2.0, 0.0, 0.0),
                (PLATE_T, 2 * PLATE_HALF, 2 * PLATE_HALF))
        trg.box(bm, (NECK_L / 2.0, 0.0, 0.0), (NECK_L, 2 * NECK_HALF, 2 * NECK_HALF))
        trg.cylinder(bm, POST_R, POST_Z0, POST_Z1, n=32, centre=(PAN_X, 0.0, 0.0))
        trg.cylinder(bm, FLANGE_R, FLANGE_Z0, FLANGE_Z1, n=48, centre=(PAN_X, 0.0, 0.0))
    with trg.layer(bm, M_DARK):
        for sy in (1.0, -1.0):
            for sz in (1.0, -1.0):
                trg.cylinder(bm, BOLT_R, -0.02, 0.15, n=12, axis="X",
                             centre=(0.0, BOLT_HALF * sy, BOLT_HALF * sz))
    # Coolant arrives here and stops here. The run through the post and up the
    # yoke is inside the parts, so it is not modelled (see the header).
    with trg.layer(bm, M_COOL):
        for sy in (1.0, -1.0):
            trg.cylinder(bm, FIT_R + 0.055, (NECK_HALF - 0.04) * sy,
                         (NECK_HALF + 0.05) * sy, n=12, axis="Y",
                         centre=(NECK_GX, 0.0, NECK_GZ))
            trg.cylinder(bm, FIT_R, (NECK_HALF + 0.03) * sy, (NECK_HALF + 0.22) * sy,
                         n=12, axis="Y", centre=(NECK_GX, 0.0, NECK_GZ))
    return bm


def build_yoke():
    """Pans. Origin = the pan axis at the top of the fixed flange."""
    bm = bmesh.new()
    with trg.layer(bm, M_BODY):
        trg.cylinder(bm, HUB_R, 0.0, HUB_Z1, n=48)
        trg.cylinder(bm, HUB_TOP_R, HUB_Z1, HUB_TOP_Z, n=32)
        # The bar is not decoration: the arms sit at y = +-0.76 and the hub only
        # reaches y = 0.34, so without it the two arms would float.
        trg.box(bm, (BAR_CX, 0.0, BAR_CZ), (BAR_L, 2 * BAR_HY, BAR_H))
        for sy in (1.0, -1.0):
            trg.box(bm, (ARM_CX, ARM_HY * sy, ARM_CZ), (ARM_L, ARM_TY, ARM_H))
        trg.cylinder(bm, PIN_R, -PIN_HALF, PIN_HALF, n=16, axis="Y",
                     centre=(0.0, 0.0, TILT_Z - FLANGE_Z1))
    with trg.layer(bm, M_DARK):
        # Cap bosses sit flush on the outside of each arm, so the joint reads as
        # a bearing even from the side.
        for sy in (1.0, -1.0):
            trg.cylinder(bm, CAP_R, CAP_Y0 * sy, CAP_Y1 * sy, n=18, axis="Y",
                         centre=(0.0, 0.0, TILT_Z - FLANGE_Z1))
    return bm


def build_head(kind):
    """Tilts. Origin = the pin, at (PAN_X, 0, TILT_Z)."""
    bm = bmesh.new()
    lamp = M_EMIT if kind == "emitter" else M_RECV

    with trg.layer(bm, M_BODY):
        trg.revolve(bm, EMITTER_BACK if kind == "emitter" else RECEIVER_BACK,
                    n=48, axis="X")
    with trg.layer(bm, M_DARK):
        trg.revolve(bm, EMITTER_FRONT if kind == "emitter" else RECEIVER_FRONT,
                    n=48, axis="X")
        if kind != "emitter":
            trg.revolve(bm, RECEIVER_ABSORB, n=48, axis="X")
        # Trunnions: coaxially with the pin, so they are invisible where they are
        # inside the barrel and a boss where they are not. They turn WITH the
        # head, which is what makes them read as the tilt bearing.
        for sy in (1.0, -1.0):
            trg.cylinder(bm, TRUN_R, TRUN_Y0 * sy, TRUN_Y1 * sy, n=24, axis="Y")
    with trg.layer(bm, M_COOL):
        for sy in (1.0, -1.0):
            trg.tube(bm, (-0.30, 0.28 * sy, -0.26), (-0.06, 0.50 * sy, -0.12),
                     HEAD_COOL_R, n=10)
    with trg.layer(bm, lamp):
        trg.revolve(bm, EMITTER_LENS if kind == "emitter" else RECEIVER_TARGET,
                    n=32 if kind == "emitter" else 16, axis="X")
    return bm


PAN_PIVOT = Vector((PAN_X, 0.0, FLANGE_Z1))
TILT_PIVOT = Vector((PAN_X, 0.0, TILT_Z))


def aim(yoke, head, pan_deg, tilt_deg, outer=None):
    """Pose one assembly. Pan is about the vertical post, tilt about the head's
    own pin -- the same two rotations the operator will drive in Studio, applied
    here only so the render shows what the joints are for."""
    pan, tilt = math.radians(pan_deg), math.radians(tilt_deg)
    yaw = Matrix.Translation(PAN_PIVOT) @ Matrix.Rotation(pan, 4, "Z")
    reach = Matrix.Translation(TILT_PIVOT - PAN_PIVOT) @ Matrix.Rotation(tilt, 4, "Y")
    if outer is not None:
        yaw, reach = outer @ yaw, outer @ reach
    yoke.matrix_world = yaw
    head.matrix_world = yaw @ reach
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- build
base = trg.finish(build_base(), "LaserPortBase", MATERIALS, bevel=0.03)
yoke = trg.finish(build_yoke(), "LaserPortYoke", MATERIALS, bevel=0.03)
head_e = trg.finish(build_head("emitter"), "LaserEmitterHead", MATERIALS, bevel=0.03)
head_r = trg.finish(build_head("receiver"), "LaserReceiverHead", MATERIALS, bevel=0.03)

# Measure BEFORE the assembly offsets go on: these are local sizes, and the whole
# point of the three-body split is that the local frame is the one Roblox sees.
# Same discipline as reading instance properties in Studio -- the build loop is
# not evidence.
STATS = {}
for obj in (base, yoke, head_e, head_r):
    STATS[obj.name] = trg.measure(obj)

STATS[base.name]["pivot"] = (0.0, 0.0, 0.0)
STATS[yoke.name]["pivot"] = tuple(PAN_PIVOT)
STATS[head_e.name]["pivot"] = tuple(TILT_PIVOT)
STATS[head_r.name]["pivot"] = tuple(TILT_PIVOT)
yoke.location = PAN_PIVOT
head_e.location = TILT_PIVOT
head_r.location = TILT_PIVOT
bpy.context.view_layer.update()

# `design_pivot` is the one number on this line that is NOT read back out of the
# mesh -- it is where the source code MEANT the origin to be. It is worth printing
# next to measured numbers only because the export/import round trip is what
# decides whether the intent survived; on its own it is not evidence of anything.
# The check on it is the FBX round-trip, not this line.
for name in ("LaserPortBase", "LaserPortYoke", "LaserEmitterHead", "LaserReceiverHead"):
    st = STATS[name]
    print("SUMMARY part=%s size=%.2f x %.2f x %.2f  tris=%d open_edges=%d "
          "design_pivot=(%.2f, %.2f, %.2f)"
          % (name, st["size"][0], st["size"][1], st["size"][2], st["tris"],
             st["open_edges"], st["pivot"][0], st["pivot"][1], st["pivot"][2]))

asm = [base, yoke, head_e]   # the emitter assembly; the receiver differs only in its head
w = [o.matrix_world @ v.co for o in asm for v in o.data.vertices]
print("SUMMARY emitter_assembly size=%.2f x %.2f x %.2f  x=%.2f..%.2f  y=%.2f..%.2f z=%.2f..%.2f"
      % (max(v.x for v in w) - min(v.x for v in w),
         max(v.y for v in w) - min(v.y for v in w),
         max(v.z for v in w) - min(v.z for v in w),
         min(v.x for v in w), max(v.x for v in w),
         min(v.y for v in w), max(v.y for v in w),
         min(v.z for v in w), max(v.z for v in w)))
print("SUMMARY expected_studio_size=%.2f x %.2f x %.2f (same numbers, Roblox's Y-up)"
      % (max(v.x for v in w) - min(v.x for v in w),
         max(v.z for v in w) - min(v.z for v in w),
         max(v.y for v in w) - min(v.y for v in w)))
# Named in ROBLOX's frame, because that is the frame the operator will rotate in
# (The FBX importer maps Blender +Z -> Studio +Y and Blender +Y ->
# Studio +Z). In HERE the same two joints are Z-then-Y, which is what aim() below
# uses -- the two lines differing is the mapping, not an inconsistency.
print("SUMMARY joints (Roblox frame): pan about local Y +-90 deg "
      "(wall clearance allows ~116); tilt about local Z +-75 deg (chosen)")

# One file per assembly, so the three parts arrive already in their relative
# positions with their origins on the pivots. If the importer flattens them
# instead, the `origin=` column above is where each part goes.
trg.export([base, yoke, head_e], NAME_E, OUT_DIR, blend=False)
trg.export([base, yoke, head_r], NAME_R, OUT_DIR, blend=False)
# One .blend for the whole thing: it holds all four parts either way, so saving it
# once per assembly would hand over two identical files wearing different names.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "LaserPort.blend"))

trg.render(NAME_E, OUT_DIR, [("iso", (5.4, -5.2, 4.4))], target=(0.85, 0.0, 0.80),
           ortho=4.4)
trg.render(NAME_R, OUT_DIR, [("iso", (5.2, -5.2, 4.4))], target=(0.80, 0.0, 0.80),
           ortho=4.2)

# ---------------------------------------------------------------- the pair
# A 180 deg yaw sends the receiver's nose to -X while its up stays +Z, so both
# axes keep their meaning and the mirrored pan/tilt below is a real mirror.
GAP = 9.0
REFLECT = Matrix.Translation((GAP, 0.0, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z")

beam_bm = bmesh.new()
trg.revolve(beam_bm, [(0.085, 1.26), (0.085, GAP - 1.26)], n=12, axis="X")
beam = trg.finish(beam_bm, "Beam",
                  [trg.material("Beam", (1.0, 0.30, 0.08), metallic=0.0, roughness=0.4,
                                emission=(1.0, 0.30, 0.08))], bevel=0.0)

aim(yoke, head_e, 0.0, 0.0)
aim(yoke, head_r, 0.0, 0.0, outer=REFLECT)
trg.render("LaserPortPair", OUT_DIR, [("iso", (GAP / 2.0 + 4.0, -12.0, 7.0))],
           target=(GAP / 2.0, 0.0, 0.85), ortho=12.5)

# Aimed: emitter up and right, receiver up and right in its own frame (which the
# 180 yaw turns into the mirror image, so they are still pointed at each other in
# the sense that matters). The beam is gone, correctly -- an aimed pair does not
# have one, and the point of the shot is that the joints are doing something.
bpy.data.objects.remove(beam, do_unlink=True)
aim(yoke, head_e, 32.0, 22.0)
aim(yoke, head_r, 32.0, 22.0, outer=REFLECT)
trg.render("LaserPortAimed", OUT_DIR, [("iso", (GAP / 2.0 + 5.0, -11.0, 8.5))],
           target=(GAP / 2.0, 0.0, 1.0), ortho=12.5)
print("SUMMARY wrote %s" % OUT_DIR)
