# laser_port.py -- a matched pair of wall ports: one emits, one receives.
#
# The brief: "一个发射，一个接收" -- an emitter and a receiver. Both are wall-mounted
# heads whose optical axis points out along +X, so a pair is placed by putting the
# two plates on facing walls. Set the receiver's CFrame to (GAP, y, z) with a 180
# degree yaw and the two mouths look at each other down the gap; the beam itself is
# a Roblox part, not geometry (it has to stretch to whatever distance the operator
# picks, and a mesh cannot do that without being scaled).
#
# WHY THEY ARE A PAIR AND NOT TWO MODELS: the family resemblance has to do the work
# of saying "these belong together", with no label. So everything structural is
# shared and built by one function -- the plate, the four bolts, the stepped hub,
# the two yoke arms, the pivot pin and its caps. Only the head differs. That is
# also why the two heads are near-mirror in length: an emitter that is visibly
# longer than its receiver reads as a mistake, not as a difference.
#
# WHAT IS CHOSEN vs MEASURED: all of it is chosen. There is no original to match --
# that is the entire point of this asset (see PROGRESS Phase 81). The size is picked
# to sit next to the scrubber of Phase 80: a 1.9-stud plate that fits on a console
# face, a 2.2-2.4 stud overall length, a head small enough to be one of several.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python "D:\rblxTRGproject\_tools\blender\laser_port.py"

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

NAME_E = "LaserEmitterPort"
NAME_R = "LaserReceiverPort"
OUT_DIR = r"D:\BlenderRobloxTestProjects\LaserPort"

# ---------------------------------------------------------------- mount (shared)
# Every number in this block is used by both heads. If one of them stops being
# shared, the pair stops reading as a pair.
PLATE_T = 0.22          # plate thickness, along the optical axis
PLATE_HALF = 0.94       # plate half-extent in y and z
BOLT_R = 0.10
BOLT_HALF = 0.66        # bolt centre offset -- 0.28 clear of the plate edge
HUB = [(0.62, 0.02), (0.62, 0.16), (0.44, 0.34), (0.44, 0.54)]
ARM_CX, ARM_L, ARM_W, ARM_T = 0.80, 0.80, 0.32, 0.22
ARM_Z = 0.60            # arm centre; inner face at 0.49, so the head nests inside
PIN_X, PIN_R, PIN_HALF = 1.06, 0.14, 0.86
CAP_R, CAP_T = 0.21, 0.12

# ---------------------------------------------------------------- head
HEAD_R = 0.47           # must stay under the arms' inner face (0.49)
HEAD_X0 = 0.44          # back of the head; sits inside the hub, so the joint is hidden
FIN_R, FIN_PITCH, FIN_T = 0.66, 0.105, 0.055

COOL_R, COOL_Y, COOL_Z = 0.075, 0.62, 0.34   # coolant stubs, mirrored on +/-Y
LAMP_Y, LAMP_Z = 0.0, 0.78                   # pilot lamp, on the plate above the hub
LENS_X = 1.93

# new_scene() wipes the file, so it has to run before any datablock exists -- a
# Material made above this line is a dangling handle by the time finish() reads it
# ("StructRNA of type Material has been removed").
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
    separate discs. Same silhouette for a fraction of the geometry, one continuous
    surface, and no seam where a disc would meet the barrel."""
    out = []
    for i in range(count):
        x = x0 + i * FIN_PITCH
        out += [(FIN_R, x), (FIN_R, x + FIN_T), (HEAD_R, x + FIN_T),
                (HEAD_R, x + FIN_PITCH)]
    return out


# --- emitter head: body, five fins, then a flared hood around a recessed dish. The
# dish exists so the lens sits *inside* the hood -- an aperture flush with the mouth
# reads as a hole, a recessed one reads as a source.
EMITTER_BACK = [(0.26, HEAD_X0), (0.42, 0.52), (HEAD_R, 0.64), (HEAD_R, 1.26)]
EMITTER_FRONT = fins(1.20, 5) + [
    (0.52, 1.83), (0.52, 1.94), (0.68, 2.04), (0.68, 2.16),
    (0.50, 2.16), (0.50, 2.02), (0.32, 1.92), (0.00, 1.90),
]
EMITTER_LENS = [(0.00, LENS_X), (0.30, 1.92), (0.32, 1.95), (0.30, 1.99), (0.00, 2.02)]

# --- receiver head: same body, three fins, then a wide funnel. The funnel's inner
# wall is part of this lathe (the profile doubles back), so the mouth is a real
# cone rather than a disc glued on.
RECEIVER_BACK = [(0.26, HEAD_X0), (0.42, 0.52), (HEAD_R, 0.64), (HEAD_R, 1.04)]
RECEIVER_FRONT = fins(1.00, 3) + [
    (HEAD_R, 1.44), (0.72, 1.72), (0.78, 1.86),
    (0.64, 1.86), (0.60, 1.70), (0.30, 1.56), (0.00, 1.54),
]
# A solid cone filling the funnel's throat -- the thing that actually absorbs. Its
# front face is closed by cap_top, so it is a disc down there rather than a hole.
RECEIVER_ABSORB = [(0.00, 1.56), (0.34, 1.70), (0.56, 1.86)]
# The sensor nub, proud of the absorber by 0.06 so it is visible looking straight in.
RECEIVER_TARGET = [(0.00, 1.80), (0.13, 1.82), (0.13, 1.90), (0.00, 1.92)]


def build(kind):
    bm = bmesh.new()
    lamp = M_EMIT if kind == "emitter" else M_RECV

    # ---- mount ---------------------------------------------------------------
    with trg.layer(bm, M_MOUNT):
        trg.box(bm, (-PLATE_T / 2.0, 0.0, 0.0),
                (PLATE_T, 2 * PLATE_HALF, 2 * PLATE_HALF))
        trg.revolve(bm, HUB, n=48, axis="X")

    with trg.layer(bm, M_DARK):
        for sy in (1.0, -1.0):
            for sz in (1.0, -1.0):
                trg.cylinder(bm, BOLT_R, -0.02, 0.15, n=12, axis="X",
                             centre=(0.0, BOLT_HALF * sy, BOLT_HALF * sz))
        for sz in (1.0, -1.0):
            trg.cylinder(bm, CAP_R, PIN_HALF * sz, (PIN_HALF + CAP_T) * sz, n=16,
                         centre=(PIN_X, 0.0, 0.0))
        trg.cylinder(bm, 0.175, 0.0, 0.09, n=14, centre=(0.0, LAMP_Y, LAMP_Z), axis="X")

    # ---- yoke ----------------------------------------------------------------
    # The arms are the only aiming geometry: a pin through both of them is what
    # says "this head tilts", so nothing else here needs to move to say it.
    with trg.layer(bm, M_BODY):
        for sz in (1.0, -1.0):
            trg.box(bm, (ARM_CX, 0.0, ARM_Z * sz), (ARM_L, ARM_W, ARM_T))
        trg.cylinder(bm, PIN_R, -PIN_HALF, PIN_HALF, n=16, centre=(PIN_X, 0.0, 0.0))
        trg.revolve(bm, EMITTER_BACK if kind == "emitter" else RECEIVER_BACK,
                    n=48, axis="X")

    with trg.layer(bm, M_DARK):
        trg.revolve(bm, EMITTER_FRONT if kind == "emitter" else RECEIVER_FRONT,
                    n=48, axis="X")
        if kind != "emitter":
            trg.revolve(bm, RECEIVER_ABSORB, n=48, axis="X")

    # ---- coolant: two stubs out of the head, back along the barrel, into glands
    # on the plate. They take the +Y/-Y lanes because those are the only two
    # directions the arms do not occupy.
    with trg.layer(bm, M_COOL):
        for sy in (1.0, -1.0):
            trg.tube(bm, (0.86, 0.30 * sy, COOL_Z), (0.86, COOL_Y * sy, COOL_Z),
                     COOL_R, n=10)
            trg.tube(bm, (0.86, COOL_Y * sy, COOL_Z), (0.13, COOL_Y * sy, COOL_Z),
                     COOL_R, n=10)
            trg.cylinder(bm, COOL_R + 0.055, 0.0, 0.20, n=12, axis="X",
                         centre=(0.0, COOL_Y * sy, COOL_Z))

    # ---- the part that says which of the two this is ---------------------------
    with trg.layer(bm, lamp):
        trg.cylinder(bm, 0.12, 0.02, 0.14, n=14, centre=(0.0, LAMP_Y, LAMP_Z), axis="X")
        trg.revolve(bm, EMITTER_LENS if kind == "emitter" else RECEIVER_TARGET,
                    n=32 if kind == "emitter" else 16, axis="X")

    return bm


def report(label, stats):
    print("SUMMARY model=%s size=%.2f x %.2f x %.2f  x=%.2f..%.2f  y=%.2f..%.2f"
          % (label, stats["size"][0], stats["size"][1], stats["size"][2],
             stats["x"][0], stats["x"][1], stats["y"][0], stats["y"][1]))
    print("SUMMARY verts=%d polys=%d tris=%d open_edges=%d"
          % (stats["verts"], stats["polys"], stats["tris"], stats["open_edges"]))


# ---------------------------------------------------------------- build + export
emitter = trg.finish(build("emitter"), NAME_E, MATERIALS, bevel=0.03)
receiver = trg.finish(build("receiver"), NAME_R, MATERIALS, bevel=0.03)

# `measure` only reads z today; the emitter and receiver differ along X, so the
# size alone would not tell them apart. Read x and y too rather than eyeball it.
for obj, label in ((emitter, NAME_E), (receiver, NAME_R)):
    st = trg.measure(obj)
    corners = [obj.matrix_world @ __import__("mathutils").Vector(c) for c in obj.bound_box]
    st["x"] = (min(v.x for v in corners), max(v.x for v in corners))
    st["y"] = (min(v.y for v in corners), max(v.y for v in corners))
    report(label, st)

trg.export(emitter, NAME_E, OUT_DIR)
trg.export(receiver, NAME_R, OUT_DIR)

trg.render(NAME_E, OUT_DIR, [("iso", (4.6, -4.8, 3.4))], target=(0.97, 0.0, 0.0),
           ortho=4.0)
trg.render(NAME_R, OUT_DIR, [("iso", (4.4, -4.8, 3.4))], target=(0.82, 0.0, 0.0),
           ortho=3.8)

# ---------------------------------------------------------------- the pair, shown
# Rendered after the exports so neither file carries the display offset: what ships
# is two heads at the origin, authored in the frame they will be used in.
GAP = 9.0
receiver.location = (GAP, 0.0, 0.0)
receiver.rotation_euler = (0.0, 0.0, math.pi)   # 180 about Z flips the nose to -X
bpy.context.view_layer.update()

# Not part of either mesh: the beam has to stretch to whatever gap the operator
# puts them at, so in Roblox it is a part, and this one only exists for the render.
beam_bm = bmesh.new()
trg.revolve(beam_bm, [(0.085, 2.16), (0.085, GAP - 1.86)], n=12, axis="X")
beam = trg.finish(beam_bm, "Beam", [trg.material("Beam", (1.0, 0.30, 0.08),
                                                 metallic=0.0, roughness=0.4,
                                                 emission=(1.0, 0.30, 0.08))],
                  bevel=0.0)

trg.render("LaserPortPair", OUT_DIR,
           [("side", (GAP / 2.0, -14.0, 0.6)), ("iso", (GAP / 2.0 + 5.0, -10.0, 6.5))],
           target=(GAP / 2.0, 0.0, 0.0), ortho=13.0)
print("SUMMARY wrote %s" % OUT_DIR)
