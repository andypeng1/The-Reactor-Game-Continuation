# cbl_laser_mk4.py -- a "Mk4" chemical-pump laser: the CBL's design language
# pushed one step further.
#
# THE BRIEF. 2026-10-24, verbatim: "那个仿照CBL做个更帅的激光（blender".
# Same machine family as Workspace.ReactorCBLs.Reactor_Laser_Mk3_* (measured in
# Phase 23: 98.0 x 36.7 x 36.7 studs, grey industrial hull, brass collars, cyan
# accents, hazard plates, a lit cyan aperture at +X), but the silhouette and the
# light should be better. Three things change, all of them about what a laser
# looks like rather than what it measures:
#
#   1. A CLOSED TUBE BECOMES AN OPEN ONE. The Mk3 is a pale tube; a tube has no
#      interior. Here the mid-hull is two cowlings with open windows on +Z and
#      -Z (up and down), crossed by six ribs. Through them you see a ribbed
#      plasma tube wrapped in three white helices -- and that whole core is a
#      separate object on the barrel axis, so it can spin in Studio.
#   2. A MUZZLE BECOMES A CLAW. Three brass prongs arc forward around a recessed
#      lens and two floating emissive rings. The beam leaves through the claw
#      rather than out of a flat disc.
#   3. THE BACK GETS A POWER STACK. Three capacitor drums on the breech, each
#      with a cyan charge band, so the machine has a silhouette at both ends
#      instead of tapering into nothing.
#
# The windows face +/-Z and the trunnion arms sit at +/-Y on purpose: the yoke
# must cover solid cowling, not the opening. The first draft had the windows on
# +/-Y and the arms right across them -- a design that reads fine in a part list
# and is obviously wrong the moment anyone stands beside it.
#
# PARTS AND PIVOTS (Roblox reads Y as up; Blender here is Z up and the FBX
# importer converts):
#
#   CblLaserMk4Mount   fixed. origin (0,0,0) = the trunnion pivot.
#   CblLaserMk4Body     the machine; same pivot, can pitch.
#   CblLaserMk4Prongs   the muzzle claw; same pivot, kept separate so it can be
#                       welded or animated on its own.
#   CblLaserMk4Core     plasma tube + helices + lens + aperture rings. Origin is
#                       ON THE BARREL AXIS, so rotating it about its local X
#                       spins the energy without moving the machine.
#
# Vertices are authored in world coordinates with every object origin at
# (0,0,0) -- which IS the pivot. Same rule as laser_port.py: a part turns about
# its own origin, so the origin has to sit on the axis of rotation.
#
# SCALE. Design numbers below are in studs; S makes the finished machine
# Mk3-sized (hull diameter 16.8 vs the Mk3's 16.2). Authored at S = 1 the same
# file would be a 40-stud gun.
#
# DELIVERY. trg.export writes at 1/5.902. Import the .fbx and type 5.902 in the
# dialog. The .glb path arrives 1.6943x too big (10 / 5.902) -- measured, see
# D:\BlenderRobloxTestProjects\README.md.
#
# Materials do NOT survive Roblox's importer; _tools/apply_cbl_laser_mk4_materials.luau
# re-applies them by SIZE. This run prints that size table between
# MATERIAL_TABLE_BEGIN / END.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python "D:\rblxTRGproject\_tools\blender\cbl_laser_mk4.py"

import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

# MEASURED 2026-10-24: under --background an uncaught exception exits rc = 0
# (CLAUDE.md 0.6), so "the build crashed" and "the build finished" are the same
# bytes to a shell. preview_gltf.py wraps its body in try/except; this script is
# top-level from end to end, so the guard goes on the interpreter instead --
# same effect, no reindent of 300 lines. Proven by raising on purpose: the
# traceback printed and rc was 1.
sys.excepthook = lambda t, v, tb: (sys.__excepthook__(t, v, tb),
                                   sys.stdout.flush(), os._exit(1))

NAME = "CblLaserMk4"
OUT_DIR = r"D:\BlenderRobloxTestProjects\CblLaserMk4"
S = 1.60                 # design studs -> delivered studs

# Blender splits argv at a bare `--`; anything after it is ours. Written as
# `--python s.py --flag` the flag is taken for a file to open (CLAUDE.md 0.6).
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NORENDER = "--norender" in ARGV
NOBEVEL = "--nobevel" in ARGV
BEVEL_ON = True          # flipped off for the control build; see finish()

# ================================================================ dimensions
# Barrel axis = +X, muzzle at high X, Z up. Design studs (multiplied by S).
X_BACK = -18.30          # rear face
X_BLOCK0, X_BLOCK1 = -17.00, -10.50
X_BARREL0, X_BARREL1 = -9.80, 6.80   # the open cowling section
X_FINS0, X_FINS1 = 6.80, 10.52
X_SHROUD1 = 14.60
X_BELL1 = 17.15
X_FRONT = 22.00

R_RIB = 5.00
R_HULL_O, R_HULL_I = 4.90, 4.20
R_TUBE = 2.95

PLATE_X0, PLATE_X1 = -8.0, 5.5
PLATE_HY = 7.2
PLATE_Z0, PLATE_Z1 = -9.40, -8.60
PED_CX = -1.50
YOKE_Y = 5.55
BOSS_R = 1.65
BOSS_Y0, BOSS_Y1 = 5.00, 6.02


# ================================================================ helpers
def shell_x(bm, r_in, r_out, a0, a1, x0, x1, n=24):
    """A curved slab around the X axis: radii r_in..r_out, angles a0..a1,
    stations x0..x1. Theta is measured from +Y toward +Z, which is exactly
    trg.revolve's axis="X" frame -- so a shell's angular range lines up with a
    lathe's rings instead of being off by a quarter turn.

    This is panel_arc, rotated into the barrel frame. It is the shape a box
    cannot make: a cowling that sits ON a cylinder without sinking into it at
    the middle or floating at the edges.
    """
    v = {}
    for j in range(n + 1):
        a = a0 + (a1 - a0) * j / n
        ca, sa = math.cos(a), math.sin(a)
        for rk, r in (("i", r_in), ("o", r_out)):
            for xk, x in (("0", x0), ("1", x1)):
                v[(rk, xk, j)] = bm.verts.new((x, r * ca, r * sa))
    for j in range(n):
        for rk in ("i", "o"):
            bm.faces.new((v[(rk, "0", j)], v[(rk, "0", j + 1)],
                          v[(rk, "1", j + 1)], v[(rk, "1", j)]))
        bm.faces.new((v[("i", "0", j)], v[("o", "0", j)],
                      v[("o", "0", j + 1)], v[("i", "0", j + 1)]))
        bm.faces.new((v[("i", "1", j)], v[("o", "1", j)],
                      v[("o", "1", j + 1)], v[("i", "1", j + 1)]))
    for j in (0, n):
        bm.faces.new((v[("i", "0", j)], v[("i", "1", j)],
                      v[("o", "1", j)], v[("o", "0", j)]))


def torus_x(bm, x0, major_r, minor_r, n_major=36, n_minor=10):
    """A ring in the YZ plane at station x0. A thin cylinder would read as a
    disc edge; a torus reads as a ring with a shadow under it -- which is the
    whole point of a floating aperture ring."""
    rings = []
    for i in range(n_major):
        a = 2 * math.pi * i / n_major
        ca, sa = math.cos(a), math.sin(a)
        rings.append([
            bm.verts.new((x0 + minor_r * math.sin(2 * math.pi * k / n_minor),
                          (major_r + minor_r * math.cos(2 * math.pi * k / n_minor)) * ca,
                          (major_r + minor_r * math.cos(2 * math.pi * k / n_minor)) * sa))
            for k in range(n_minor)
        ])
    for i in range(n_major):
        j = (i + 1) % n_major
        for k in range(n_minor):
            l = (k + 1) % n_minor
            bm.faces.new((rings[i][k], rings[i][l], rings[j][l], rings[j][k]))


def helix(bm, x0, x1, helix_r, wire_r, turns, phase, n_path=150, n_tube=8):
    """A wire wound around the barrel axis. The frame comes from the helix's own
    radial direction rather than from parallel transport: on this path the
    tangent is never parallel to the radial, so the simple frame is exact and
    there is no accumulated twist to get wrong."""
    rings = []
    dx = x1 - x0
    for i in range(n_path + 1):
        t = i / n_path
        x = x0 + dx * t
        a = phase + 2 * math.pi * turns * t
        ca, sa = math.cos(a), math.sin(a)
        tang = Vector((dx, -helix_r * 2 * math.pi * turns * sa,
                       helix_r * 2 * math.pi * turns * ca)).normalized()
        radial = Vector((0.0, ca, sa))
        radial = (radial - tang * radial.dot(tang)).normalized()
        binorm = tang.cross(radial).normalized()
        c = Vector((x, helix_r * ca, helix_r * sa))
        rings.append([
            bm.verts.new(c + radial * (wire_r * math.cos(2 * math.pi * k / n_tube))
                         + binorm * (wire_r * math.sin(2 * math.pi * k / n_tube)))
            for k in range(n_tube)
        ])
    for a, b in zip(rings, rings[1:]):
        for k in range(n_tube):
            l = (k + 1) % n_tube
            bm.faces.new((a[k], a[l], b[l], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def x_box(bm, x, r, angle, size):
    """A box in the barrel's cylindrical frame: x along the axis, r outward at
    `angle`, size = (along X, radial, tangential). trg.box only rotates about Z,
    which is the wrong axis for anything bolted to the side of a horizontal
    barrel."""
    mat = (Matrix.Translation(Vector((x, r * math.cos(angle), r * math.sin(angle))))
           @ Matrix.Rotation(angle, 4, "X")
           @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def arc_prong(bm, angle, x0, x1, r0, r1, w0, w1, h0, h1, bulge, n=26):
    """One curved claw: a rectangular cross-section swept along a path in the
    (x, r) plane, then placed at `angle` around the barrel. The `bulge` term
    makes the prong bow OUT before it turns in -- a straight taper reads as a
    spike, and a spike does not say 'focusing element'."""
    rings = []
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        r = r0 + (r1 - r0) * t + bulge * math.sin(math.pi * t)
        w = w0 + (w1 - w0) * t
        h = h0 + (h1 - h0) * t
        ring = []
        for dr, ds in ((-h / 2, -w / 2), (h / 2, -w / 2),
                       (h / 2, w / 2), (-h / 2, w / 2)):
            rr, s = r + dr, ds
            ring.append(bm.verts.new((x, rr * ca - s * sa, rr * sa + s * ca)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            l = (k + 1) % 4
            bm.faces.new((a[k], a[l], b[l], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


# ================================================================ scene
trg.new_scene()

M_HULL, M_DARK, M_BRASS, M_HAZARD, M_CYAN, M_AMBER, M_WHITE = range(7)


def glow(name, rgb, strength):
    """trg.material writes an emission colour at strength 3. A lens at 3 and a
    hull at 0 read as the same surface in a render, so emissive parts get their
    own strength. Nodes are found by TYPE: node names are localized in a
    non-English Blender (MCP server guidance)."""
    mat = trg.material(name, rgb, metallic=0.0, roughness=0.28, emission=rgb)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


MATERIALS = [
    trg.material("Mk4Hull", (0.235, 0.255, 0.285), metallic=0.82, roughness=0.44),
    trg.material("Mk4Dark", (0.045, 0.050, 0.058), metallic=0.70, roughness=0.52),
    trg.material("Mk4Brass", (0.520, 0.330, 0.105), metallic=1.00, roughness=0.33),
    trg.material("Mk4Hazard", (0.820, 0.560, 0.030), metallic=0.15, roughness=0.58),
    glow("Mk4Cyan", (0.055, 0.780, 1.000), 5.0),
    glow("Mk4Amber", (1.000, 0.360, 0.035), 4.0),
    glow("Mk4White", (0.780, 0.960, 1.000), 9.0),
]


def finish(bm, name, bevel):
    """Scale design studs to delivered studs, then hand over to trg.finish.
    Scaling the verts before the bevel keeps the bevel proportional instead of
    quietly becoming 1.6x finer than the number written here.

    BEVEL_ON is turned off for the control build below. With the bevel off every
    face carries the index its builder gave it, so the two material tables can be
    compared: a bevel cannot move a per-material bounding box further than its
    own offset, so any material that moves further had faces handed to the wrong
    material. That control is the ONLY check on the bevel's material inheritance
    -- in Blender a bevel with the wrong index looks perfect, and the symptom
    (a grey duplicate shell) appears only after Roblox splits the mesh."""
    for v in bm.verts:
        v.co *= S
    return trg.finish(bm, name, MATERIALS,
                      bevel=bevel * S if (BEVEL_ON and not NOBEVEL) else 0.0)


# ================================================================ mount
def build_mount():
    bm = bmesh.new()
    with trg.layer(bm, M_HULL):
        trg.box(bm, ((PLATE_X0 + PLATE_X1) / 2.0, 0.0,
                     (PLATE_Z0 + PLATE_Z1) / 2.0),
                (PLATE_X1 - PLATE_X0, 2 * PLATE_HY, PLATE_Z1 - PLATE_Z0))
        # Round pedestal, not a box: a trunnion's load path is the one place on
        # this machine where a round section is the honest one.
        trg.revolve(bm, [(4.60, -8.60), (4.60, -8.30), (4.15, -7.95),
                         (3.35, -7.45), (2.90, -6.85), (2.90, -4.30)],
                    n=40, centre=(PED_CX, 0.0), axis="Z")
        trg.box(bm, (0.0, 0.0, -4.60), (2.40, 2 * YOKE_Y, 1.20))
        # The arms are 1.70 thick, not 0.90, and centred at 5.15 rather than at
        # YOKE_Y. At 0.90 thick with its inner face at 5.10 the arm misses the
        # barrel's 4.90 outer radius by 0.20 studs and touches it only through
        # the trunnion boss -- mechanically defensible, and it reads in a render
        # as a bracket hovering next to the machine (Round 1 of the previews said
        # exactly that). 4.30 sinks the inner face into the cowling across most
        # of the arm's height, so it clamps.
        for sy in (1.0, -1.0):
            trg.box(bm, (0.0, 5.15 * sy, -1.20), (2.20, 1.70, 7.00))
    with trg.layer(bm, M_BRASS):
        for sy in (1.0, -1.0):
            y0, y1 = BOSS_Y0 * sy, BOSS_Y1 * sy
            trg.cylinder(bm, BOSS_R, min(y0, y1), max(y0, y1), n=32, axis="Y")
    with trg.layer(bm, M_DARK):
        for sy in (1.0, -1.0):
            for i in range(8):
                a = 2 * math.pi * i / 8 + math.pi / 8
                y0 = (BOSS_Y1 + 0.005) * sy
                y1 = (BOSS_Y1 + 0.13) * sy
                trg.cylinder(bm, 0.12, min(y0, y1), max(y0, y1), n=10, axis="Y",
                             centre=(1.15 * math.cos(a), 0.0, 1.15 * math.sin(a)))
    # hazard band around the pedestal foot: 20 segments, alternating
    step = 2 * math.pi / 20
    for i in range(20):
        with trg.layer(bm, M_HAZARD if i % 2 == 0 else M_DARK):
            trg.panel_arc(bm, 4.63, 4.72, -8.56, -7.98,
                          i * step + 0.012, (i + 1) * step - 0.012, n=2)
    return bm


# ================================================================ body
def build_body():
    bm = bmesh.new()

    with trg.layer(bm, M_HULL):
        # breech block, rear cone, square-to-round flange
        trg.box(bm, ((X_BLOCK0 + X_BLOCK1) / 2.0, 0.0, 0.0),
                (X_BLOCK1 - X_BLOCK0, 9.40, 9.40))
        trg.revolve(bm, [(0.0, X_BACK), (1.60, X_BACK), (2.60, X_BACK + 0.18),
                         (3.55, X_BACK + 0.55), (3.80, X_BACK + 1.02),
                         (3.80, X_BLOCK0)],
                    n=40, axis="X")
        trg.box(bm, (-10.28, 0.0, 0.0), (0.55, 10.40, 10.40))
        trg.cylinder(bm, R_HULL_O, -10.00, X_BARREL0 + 0.02, n=48, axis="X")

        # Two cowlings on +/-Y, leaving a window on +Z and on -Z. The window is
        # the point: the core is what the machine is doing.
        for a0, a1 in ((-45.0, 45.0), (135.0, 225.0)):
            shell_x(bm, R_HULL_I, R_HULL_O, math.radians(a0), math.radians(a1),
                    X_BARREL0, X_BARREL1, n=24)
        for xr in (-9.80, -6.40, -3.00, 0.40, 3.80, 6.80):
            trg.cylinder(bm, R_RIB, xr - 0.275, xr + 0.275, n=48, axis="X")

        # fin stack: a square wave in the profile, so one lathe owns the fins
        prof = [(4.40, X_FINS0)]
        x = X_FINS0
        while x + 0.62 <= X_FINS1 + 1e-9:
            prof += [(5.25, x), (5.25, x + 0.30), (4.40, x + 0.30),
                     (4.40, x + 0.62)]
            x += 0.62
        prof += [(4.40, X_FINS1)]
        trg.revolve(bm, prof, n=48, axis="X")

        # Shroud taper, and the hazard collar it carries.
        # The taper is stepped here rather than a clean cone: between the fin
        # stack and the muzzle bell this is the largest uninterrupted surface
        # on the machine, and in the first previews it read as empty. Two
        # raised bands cost one lathe each and give the eye a scale reference.
        # Both bands sit clear of the hazard collar's 11.40..12.50 so nothing
        # is coplanar with it.
        trg.revolve(bm, [(4.38, X_FINS0), (4.32, 9.90),
                         (4.46, 9.95), (4.46, 10.55), (4.335, 10.60),
                         (4.14, 12.90),
                         (4.26, 12.95), (4.26, 13.55), (4.14, 13.60),
                         (4.05, 14.20), (3.95, X_SHROUD1)], n=48, axis="X")
        trg.cylinder(bm, 4.34, 11.40, 12.50, n=48, axis="X")
        # end rings of the open section, so the core is anchored, not floating
        for xe in (X_BARREL0 - 0.10, X_BARREL1 + 0.10):
            trg.cylinder(bm, 3.82, xe - 0.07, xe + 0.07, n=40, axis="X")
        # side access panels
        for sx in (1.0, -1.0):
            trg.box(bm, (-12.30, 4.76 * sx, 0.0), (3.10, 0.14, 3.70))

    with trg.layer(bm, M_DARK):
        trg.cylinder(bm, 1.20, X_BACK - 0.07, X_BACK + 0.01, n=24, axis="X")
        trg.box(bm, (-13.60, 0.0, 4.66), (5.60, 3.20, 0.30))
        # hex vent bosses on both cheeks, each with a glowing inset
        for sx in (1.0, -1.0):
            for xh in (-16.30, -14.90):
                for zh in (-2.10, 2.10):
                    y0, y1 = 4.68 * sx, 4.90 * sx
                    trg.revolve(bm, [(1.05, min(y0, y1)), (1.05, max(y0, y1))],
                                n=6, axis="Y", centre=(xh, 0.0, zh))
                    y0, y1 = 4.90 * sx, 4.95 * sx
                    trg.revolve(bm, [(0.72, min(y0, y1)), (0.72, max(y0, y1))],
                                n=6, axis="Y", centre=(xh, 0.0, zh))
        # panel bolts, on the raised panel face
        for sx in (1.0, -1.0):
            for xb in (-13.55, -11.05):
                for zb in (-1.55, 1.55):
                    y0, y1 = 4.80 * sx, 4.94 * sx
                    trg.cylinder(bm, 0.13, min(y0, y1), max(y0, y1), n=10,
                                 axis="Y", centre=(xb, 0.0, zb))
        # flange bolts
        for i in range(12):
            a = 2 * math.pi * i / 12
            trg.cylinder(bm, 0.14, -10.05, -9.90, n=10, axis="X",
                         centre=(0.0, 4.62 * math.cos(a), 4.62 * math.sin(a)))
        # lamp sockets on the flange's top face
        for yl in (-0.90, 0.0, 0.90):
            trg.cylinder(bm, 0.30, 5.16, 5.30, n=16, centre=(-10.90, yl))

    with trg.layer(bm, M_BRASS):
        for xr in (-9.80, -6.40, -3.00, 0.40, 3.80, 6.80):
            for dx in (-0.31, 0.31):
                trg.cylinder(bm, 5.04, xr + dx - 0.04, xr + dx + 0.04, n=48,
                             axis="X")
        trg.cylinder(bm, 4.62, 10.70, 11.10, n=48, axis="X")
        # Bearing caps at the trunnion. The yoke arms run out to |y| 6.00 and
        # are 7 studs tall, so in a side view they are a slab laid over the
        # barrel -- the previews said "a plate standing next to it", which is
        # the honest reading of a flat face with nothing wrapping. These two
        # arc segments stand 0.38 proud of the cowling and are taller (to
        # |z| 4.16) than the arms (2.30), so they break the slab's outline and
        # read as the barrel sitting in a bearing.
        for a0, a1 in ((-52.0, 52.0), (128.0, 232.0)):
            shell_x(bm, 4.88, 5.28, math.radians(a0), math.radians(a1),
                    -1.30, 1.30, n=18)
        for xd in (-15.60, -13.60, -11.60):
            trg.cylinder(bm, 1.20, 4.70, 7.70, n=24, centre=(xd, 0.0))
            trg.cylinder(bm, 1.30, 4.95, 5.10, n=24, centre=(xd, 0.0))
            trg.cylinder(bm, 1.30, 7.40, 7.58, n=24, centre=(xd, 0.0))

    # Power manifold for the capacitor drums. Round 1 of the previews read the
    # drums as "placed on top" rather than built in, and they were right: they
    # stood on the block's top face with nothing joining them to anything. A
    # rail per side with a stub into each drum and a canted drop into the block
    # is twelve tubes and turns three separate cylinders into one power bank.
    DRUM_X = (-15.60, -13.60, -11.60)
    with trg.layer(bm, M_DARK):
        for sy in (1.0, -1.0):
            trg.tube(bm, (-16.95, 1.55 * sy, 5.35), (-10.55, 1.55 * sy, 5.35),
                     0.20, n=16)
            for xd in DRUM_X:
                trg.tube(bm, (xd, 1.20 * sy, 5.35), (xd, 1.55 * sy, 5.35),
                         0.13, n=12)
            for xe in (-16.95, -10.55):
                trg.tube(bm, (xe, 1.55 * sy, 5.35), (xe, 2.10 * sy, 4.42),
                         0.16, n=14)
                trg.cylinder(bm, 0.34, 4.55, 4.86, n=16,
                             centre=(xe, 2.10 * sy))

    with trg.layer(bm, M_CYAN):
        # inlay strips on the outward faces of the two cowlings
        # 0.06 thick, not 0.035: the bevel is 0.022 design, so on a 0.035 strip
        # clamp_overlap has to collapse the thickness to nothing and the strip
        # comes back as zero-area faces (8 of them, measured 2026-10-24 -- the
        # last degenerates left on this part). 0.06 studs of extra stand-off is
        # invisible and leaves the bevel room to work.
        for ang in (-20.0, 20.0, 160.0, 200.0):
            shell_x(bm, R_HULL_O, R_HULL_O + 0.06,
                    math.radians(ang - 1.2), math.radians(ang + 1.2),
                    -8.80, 5.80, n=2)
        for xd in (-15.60, -13.60, -11.60):
            trg.cylinder(bm, 1.235, 6.55, 6.85, n=24, centre=(xd, 0.0))

    # hazard band on the shroud: 18 segments, yellow / dark
    step = 2 * math.pi / 18
    for i in range(18):
        with trg.layer(bm, M_HAZARD if i % 2 == 0 else M_DARK):
            shell_x(bm, 4.35, 4.42, i * step + 0.02, (i + 1) * step - 0.02,
                    11.55, 12.35, n=2)

    with trg.layer(bm, M_AMBER):
        for yl in (-0.90, 0.0, 0.90):
            trg.cylinder(bm, 0.21, 5.28, 5.48, n=16, centre=(-10.90, yl))

    with trg.layer(bm, M_DARK):
        # aperture bell last, so its dark material is not overwritten
        trg.revolve(bm, [(3.95, X_SHROUD1), (4.35, 15.60), (4.60, 16.40),
                         (4.60, 16.90), (4.25, X_BELL1), (3.90, X_BELL1),
                         (3.60, 16.70), (3.00, 16.00), (2.20, 15.55),
                         (2.00, 15.25), (0.0, 15.15)],
                    n=48, axis="X")
    return bm


# ================================================================ prongs
def build_prongs():
    bm = bmesh.new()
    with trg.layer(bm, M_BRASS):
        for ang in (90.0, 210.0, 330.0):
            arc_prong(bm, math.radians(ang), 16.70, X_FRONT,
                      4.35, 2.35, 0.90, 0.38, 0.62, 0.26, bulge=0.55, n=26)
    return bm


# ================================================================ core
def build_core():
    bm = bmesh.new()
    with trg.layer(bm, M_CYAN):
        prof = [(0.0, -9.70), (2.20, -9.70), (R_TUBE, -9.40)]
        x = -9.00
        while x < 13.55:
            prof += [(3.05, x), (3.05, x + 0.35), (2.75, x + 0.35),
                     (2.75, x + 0.90)]
            x += 0.90
        prof += [(R_TUBE, 14.30), (2.20, 14.40), (0.0, 14.45)]
        trg.revolve(bm, prof, n=48, axis="X")

        # two aperture rings, each on three spokes that reach the bell wall
        for xr, rr, rsp in ((16.72, 2.15, 3.65), (16.95, 2.75, 4.55)):
            torus_x(bm, xr, rr, 0.11)
            for i in range(3):
                a = math.radians(i * 120.0 + 30.0)
                r0 = rr + 0.11
                x_box(bm, xr, (r0 + rsp) / 2.0, a, (0.11, rsp - r0, 0.11))

    with trg.layer(bm, M_WHITE):
        for i in range(3):
            helix(bm, -9.20, 14.00, 3.55, 0.17, 3.0,
                  phase=i * 2 * math.pi / 3.0)
        # lens dome, inside the bell mouth
        trg.revolve(bm, [(0.0, 15.15), (0.90, 15.20), (1.50, 15.45),
                         (1.70, 15.90), (1.55, 16.25), (1.00, 16.40),
                         (0.0, 16.45)], n=40, axis="X")
    return bm


# ================================================================ build
# One list, built twice: once for delivery and once with the bevel off as the
# control for the material table. The bevel width is per part because a 0.025
# on the mount's 0.2-stud hazard segments is already a big fraction of them.
PARTS = [
    ("CblLaserMk4Mount", build_mount, 0.025),
    ("CblLaserMk4Body", build_body, 0.022),
    ("CblLaserMk4Prongs", build_prongs, 0.018),
    ("CblLaserMk4Core", build_core, 0.012),
]
OBJS = [finish(builder(), name, bev) for name, builder, bev in PARTS]


def mat_table(mesh):
    """Per-material bounding box and face count, in the mesh's own (already
    delivered-stud) frame. Face counts are diagnostic only; the box is what the
    material re-apply script matches on in Studio."""
    per = {}
    for poly in mesh.polygons:
        entry = per.setdefault(poly.material_index,
                               [Vector((1e18,) * 3), Vector((-1e18,) * 3), 0])
        entry[2] += 1
        for vi in poly.vertices:
            co = mesh.vertices[vi].co
            for i in range(3):
                entry[0][i] = min(entry[0][i], co[i])
                entry[1][i] = max(entry[1][i], co[i])
    return per

# The build loop is not evidence (CLAUDE.md 0.2); read the meshes back.
STATS = {o.name: trg.measure(o) for o in OBJS}
for o in OBJS:
    st = STATS[o.name]
    print("SUMMARY part=%s size=%.3f x %.3f x %.3f  verts=%d  tris=%d  open_edges=%d"
          % (o.name, st["size"][0], st["size"][1], st["size"][2],
             st["verts"], st["tris"], st["open_edges"]))

world = [o.matrix_world @ v.co for o in OBJS for v in o.data.vertices]
lo = Vector((min(v.x for v in world), min(v.y for v in world), min(v.z for v in world)))
hi = Vector((max(v.x for v in world), max(v.y for v in world), max(v.z for v in world)))
size = hi - lo
centre = (lo + hi) * 0.5
print("SUMMARY assembly size=%.3f x %.3f x %.3f  min=(%.3f, %.3f, %.3f)  max=(%.3f, %.3f, %.3f)"
      % (size.x, size.y, size.z, lo.x, lo.y, lo.z, hi.x, hi.y, hi.z))
# FBX importer maps Blender +Z -> Studio +Y and +Y -> Studio +Z.
print("SUMMARY expected_studio_size=%.3f x %.3f x %.3f"
      % (size.x, size.z, size.y))
print("SUMMARY tris_total=%d" % sum(STATS[o.name]["tris"] for o in OBJS))

# Per-material bounding boxes in DELIVERED studs, in the frame Roblox reports
# after an FBX import at 5.902 (X, Y-up, Z). This is what the material re-apply
# script matches on, so it is printed ready to paste: a table retyped from a
# screenshot is a table that drifts.
print("MATERIAL_TABLE_BEGIN")
for o in OBJS:
    per = mat_table(o.data)
    print("  %s = {" % o.name)
    for key in sorted(per):
        lo_i, hi_i, n_faces = per[key]
        s = hi_i - lo_i
        print("    { mat = \"%s\", size = { %.4f, %.4f, %.4f } },"
              % (MATERIALS[key].name.replace("Mk4", ""), s.x, s.z, s.y))
        # Diagnostics only -- the size above is what Roblox splits on. The
        # face count and the raw Blender-frame extents are here because a
        # material whose bbox is larger than its geometry should be says some
        # face got the wrong index, and the bbox alone cannot show WHICH end.
        print("    --  %s n=%d  x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]"
              % (MATERIALS[key].name.replace("Mk4", ""), n_faces,
                 lo_i.x, hi_i.x, lo_i.y, hi_i.y, lo_i.z, hi_i.z))
    print("  },")
print("MATERIAL_TABLE_END")

# ---------------------------------------------------------------- control
# Rebuild the same four parts with the bevel OFF and compare the material
# tables. This is the only place that can catch a bevel handing faces to the
# wrong material: Blender renders a mis-indexed bevel perfectly, and the damage
# (Roblox splitting the mesh into a grey duplicate shell) shows up only after
# the operator imports it. MEASURED 2026-10-24: omitting bmesh.ops.bevel's
# `material` argument does not give the documented -1, it gives 0, and every
# bevel face joins material 0 -- the first material, which on this asset is
# Hull. The failure signature was a per-material box that grew to reach parts
# of the machine that material was never built on.
BEVEL_ON = False
CTRL = [finish(builder(), name, bev) for name, builder, bev in PARTS]
BEVEL_ON = True

_ctrl_ok = 0
_ctrl_bad = 0
for i, (name, _, bev) in enumerate(PARTS):
    got = mat_table(CTRL[i].data)
    want = mat_table(OBJS[i].data)
    tol = bev * S + 1e-4
    for key in sorted(set(got) | set(want)):
        if key not in got or key not in want:
            print("CONTROL FAIL %s material %d present in only one run"
                  % (name, key))
            _ctrl_bad += 1
            continue
        for axis in range(3):
            for end in (0, 1):
                d = abs(got[key][end][axis] - want[key][end][axis])
                if d > tol:
                    print("CONTROL FAIL %s material %d axis %d end %d: "
                          "no-bevel %.4f vs bevel %.4f (limit %.4f)"
                          % (name, key, axis, end,
                             got[key][end][axis], want[key][end][axis], tol))
                    _ctrl_bad += 1
                else:
                    _ctrl_ok += 1
for o in CTRL:
    bpy.data.objects.remove(o, do_unlink=True)
print("CONTROL_MATERIALS %d ok, %d failed" % (_ctrl_ok, _ctrl_bad))
if _ctrl_bad:
    print("CONTROL_MATERIALS the bevel moved faces between materials")
    sys.exit(1)

# ================================================================ export
trg.export(OBJS, NAME, OUT_DIR, blend=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, NAME + ".blend"))
print("SUMMARY wrote %s" % OUT_DIR)

if NORENDER:
    print("SUMMARY skipped the preview renders (--norender)")
    sys.exit(0)

# ================================================================ presentation
# Render-only geometry: the beam and a floor. Neither is in OBJS and neither is
# selected, so none of it reaches the .fbx / .glb / .blend. The beam is the
# payoff the shape is built around; building it in the render also answers the
# one question the part list cannot -- does the claw frame the light or fight it.
beam_mat = glow("PreviewBeamCore", (0.95, 1.00, 1.00), 14.0)
beam_haze = glow("PreviewBeamHaze", (0.10, 0.75, 1.00), 2.2)
floor_mat = trg.material("PreviewFloor", (0.035, 0.040, 0.050),
                         metallic=0.1, roughness=0.75)

bm = bmesh.new()
trg.revolve(bm, [(0.0, 16.40), (0.28, 16.40), (0.28, 70.0), (0.0, 70.0)],
            n=20, axis="X")
for v in bm.verts:
    v.co *= S
beam = trg.finish(bm, "PreviewBeam", [beam_mat], bevel=0.0)
bm = bmesh.new()
trg.revolve(bm, [(0.0, 16.40), (0.85, 16.55), (0.85, 70.0), (0.0, 70.0)],
            n=20, axis="X")
for v in bm.verts:
    v.co *= S
haze = trg.finish(bm, "PreviewHaze", [beam_haze], bevel=0.0)
bm = bmesh.new()
trg.box(bm, (0.0, 0.0, -9.52), (400.0, 400.0, 0.12))
floor = trg.finish(bm, "PreviewFloor", [floor_mat], bevel=0.0)

scene = bpy.context.scene
try:
    scene.render.engine = "CYCLES"
except TypeError:
    pass
scene.cycles.samples = 32
try:
    scene.cycles.use_denoising = True
except Exception:
    pass
scene.render.resolution_x = 900
scene.render.resolution_y = 620
fmts = [i.identifier for i in
        scene.render.image_settings.bl_rna.properties["file_format"].enum_items]
if "PNG" in fmts:
    scene.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("PreviewWorld")
scene.world = world
world.use_nodes = True
wbg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
wbg.inputs[0].default_value = (0.012, 0.015, 0.022, 1.0)
wbg.inputs[1].default_value = 1.0


def area(name, loc, energy, colour, size, target=(0.0, 0.0, 0.0)):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = colour
    data.size = size
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


area("Key", (26.0, -46.0, 50.0), 42000.0, (1.0, 0.96, 0.90), 36.0,
     target=(3.0, 0.0, -2.0))
area("Fill", (-48.0, -36.0, 12.0), 12000.0, (0.55, 0.75, 1.0), 30.0,
     target=(0.0, 0.0, -2.0))
area("Rim", (-4.0, 42.0, 36.0), 26000.0, (0.55, 0.80, 1.0), 26.0,
     target=(-5.0, 0.0, 2.0))

span = max(size.x, size.y, size.z)


def shoot(tag, direction, dist, target, lens=50.0):
    cam_data = bpy.data.cameras.new("Cam_" + tag)
    cam_data.lens = lens
    cam = bpy.data.objects.new("Cam_" + tag, cam_data)
    scene.collection.objects.link(cam)
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.abspath(
        os.path.join(OUT_DIR, "%s_%s.png" % (NAME, tag)))
    bpy.ops.render.render(write_still=True)
    print("SUMMARY wrote %s" % scene.render.filepath)
    bpy.data.objects.remove(cam, do_unlink=True)


shoot("hero", (0.62, -0.72, 0.32), span * 1.30, centre)
shoot("side", (0.0, -1.0, 0.10), span * 1.25, (centre.x, 0.0, centre.z))
shoot("muzzle", (0.74, -0.52, 0.24), span * 0.62, (centre.x + span * 0.30, 0.0, centre.z))
shoot("rear", (-0.80, -0.52, 0.28), span * 0.80, (centre.x - span * 0.22, 0.0, centre.z))
