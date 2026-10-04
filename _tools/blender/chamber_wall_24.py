# An 18-sided platform rim grown OUTWARD into a 24-sided wall, the two joined by
# Bridge Edge Loops.
#
# WHY THIS IS A BLENDER JOB. A Roblox MeshPart is a finished triangle soup: there
# is no operator on that side that takes two closed rims of DIFFERENT vertex
# counts and sews them together -- the 42 triangles would have to be computed by
# hand and written into the file. This is the one shape the parts-based modeller
# cannot reach at all. Not "harder". Impossible. (docs/SNIPPETS.md 5.15; the same
# topology at toy scale is TransitionPillar.)
#
# THE JOIN IS THE DELIVERABLE. Radii, heights and the wall's thickness are free
# choices -- the user said "往外扩展为24边形墙壁，并且要正确衔接": expand it outward
# into a 24-sided wall AND join it correctly. So what must be exactly right is
# that the result is ONE closed manifold whose lower rim is the 18-gon that is
# ALREADY IN THE PLACE (same apothem, same phase) and whose upper rim is a
# 24-gon, with the band between them being 18 + 24 = 42 triangles per surface and
# no twist. Those numbers are ASSERTED here and then read back out of the exported
# FILE by chamber_wall_24_check.py -- this script's own printout is not evidence,
# for the same reason the Studio side reads instance state instead of module state
# (CLAUDE.md 0.2, and its Blender half, 0.6).

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

NAME = "ChamberWall24"
OUT_DIR = os.environ.get("CHAMBER_WALL_OUT",
                         r"D:\BlenderRobloxTestProjects\ChamberWall24")

# Mutations. A check nobody has ever watched go red is a check that measures
# nothing (DECISIONS 205), and every failure mode below is QUIET: an unbridged
# model is still a valid mesh, and a band joined to the wrong partners is still
# 84 triangles that pass every count test.
SKIP_BRIDGE = "--no-bridge" in sys.argv   # leave all four rims open
WRONG_PAIR = "--wrong-pair" in sys.argv   # outer18 -> inner24 and vice versa
CROSS = "--cross" in sys.argv             # hand-rolled band, half a ring out

# ---------------------------------------------------------------- design
#
# MEASURED IN THE PLACE, not chosen. Workspace.Folder.Folder.Folder.18 is an
# 18-sided rim; 720 inward raycasts from outside give r = 63.711 .. 64.695 with
# the profile breaking at 0, 20, 40 ... degrees. 63.711 is the APOTHEM (the side
# planes) and 64.695 = 63.712 / cos(10 deg) is the CIRCUMRADIUS (the corners), so
# the polygon has a VERTEX on +X rather than a side -- which is the one fact the
# join cannot get wrong. That rim is the input; it is not a knob.
A18 = 63.712                 # apothem of the existing rim  (== the join surface)
N18 = 18                     # sides it has
WALL = 4.00                  # wall thickness -> the inner face is A18 - WALL
#
# Everything below is a free choice. The 24-gon's apothem is 4.288 studs further
# out than the 18-gon's, which is what makes this "expand outward" rather than
# "replace"; the collar keeps the existing outline going for a moment before the
# flare starts, so the join reads as a deliberate shoulder rather than as a
# chamfer. Both are one number each if the operator wants a different proportion.
A24 = 68.000                 # apothem of the new 24-gon
N24 = 24
Z_COLLAR = 1.20              # top of the straight 18-sided collar
Z_BAND = 4.20                # top of the bridge == bottom of the 24-sided wall
Z_TOP = 13.20                # top of the wall

MAT_BASE, MAT_BAND, MAT_TOP = 0, 1, 2

# The phase is 0 for both polygons and that is not a coincidence to be relied on
# blindly: a vertex of the 18-gon sits every 20 deg, a vertex of the 24-gon every
# 15, and BOTH sets are invariant under a 180 deg rotation, so they are also
# invariant under the X-mirror the FBX importer applies (the mapping measured on
# the laser port was (bx,by,bz) -> (-bx,bz,by), i.e. Studio azimuth = 180 - b).
# A 24-gon offset by 7.5 deg would NOT be, and would need correcting after import.

# ---------------------------------------------------------------- derived
R_OUT18 = A18 / math.cos(math.pi / N18)      # 64.6946  (matches the place)
R_IN18 = (A18 - WALL) / math.cos(math.pi / N18)
R_OUT24 = A24 / math.cos(math.pi / N24)
R_IN24 = (A24 - WALL) / math.cos(math.pi / N24)

RIMS = {"18out": (N18, R_OUT18, Z_COLLAR), "18in": (N18, R_IN18, Z_COLLAR),
        "24out": (N24, R_OUT24, Z_BAND), "24in": (N24, R_IN24, Z_BAND)}


# ---------------------------------------------------------------- helpers
def ring(bm, n, apothem, z):
    """One regular n-gon of verts, corners at azimuth 0, 360/n, 720/n, ...

    Radius is derived from the APOTHEM rather than the other way round, so that
    the sides -- which are what the neighbour in the place actually touches --
    land on the number that was measured off it.
    """
    r = apothem / math.cos(math.pi / n)
    return [bm.verts.new((r * math.cos(2 * math.pi * k / n),
                          r * math.sin(2 * math.pi * k / n), z))
            for k in range(n)]


def annulus(bm, n, a_out, a_in, z0, z1):
    """A closed n-sided tube: outer wall, inner wall, and a ring at each end.

    Built by hand rather than with trg.revolve, for two reasons. revolve lathes
    an OPEN profile and caps each end with ONE n-gon, and an annulus end is a
    ring -- a face with a hole, which no single n-gon can be. And building the end
    as n quads is what makes "delete the end" a well defined operation that leaves
    TWO boundary loops (the outer rim and the inner rim), which is exactly what
    the bridge wants to be handed.
    """
    o0, o1 = ring(bm, n, a_out, z0), ring(bm, n, a_out, z1)
    i0, i1 = ring(bm, n, a_in, z0), ring(bm, n, a_in, z1)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))    # outer wall
        bm.faces.new((i0[k], i0[j], i1[j], i1[k]))    # inner wall
        bm.faces.new((i0[k], i0[j], o0[j], o0[k]))    # ring at z0
        bm.faces.new((i1[k], i1[j], o1[j], o1[k]))    # ring at z1


def end_faces(bm, z, tol=1e-6):
    """The ring faces at exactly this height.

    ALL verts at the height, not any: the side walls also touch z0 and z1 at their
    ends. Selecting by "any" would take the walls too, and the failure -- a model
    with no walls -- reads as something else entirely.
    """
    return [f for f in bm.faces if all(abs(v.co.z - z) < tol for v in f.verts)]


def rim_loops(bm):
    """Every boundary edge, walked into rings. Returns a list of ordered verts.

    This runs BEFORE the bridge, as a precondition. Bridge Edge Loops decides
    what to connect from the geometry it is handed; hand it two rims from
    different pairs and it will still produce a mesh, just not this one. Counting
    the rims first is what turns that into a refusal.
    """
    adj = {}
    for e in bm.edges:
        if len(e.link_faces) != 1:
            continue
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [], None, start
        while cur is not None and cur not in seen:
            loop.append(cur)
            seen.add(cur)
            nxt = [v for v in adj[cur] if v is not prev]
            prev, cur = cur, (nxt[0] if nxt else None)
        loops.append(loop)
    return loops


def mean(loop, f):
    return sum(f(v) for v in loop) / len(loop)


def edges_of(bm, *loops):
    want = set()
    for loop in loops:
        want.update(loop)
    return [e for e in bm.edges
            if len(e.link_faces) == 1 and e.verts[0] in want and e.verts[1] in want]


def axis_radius(v):
    return math.hypot(v.co.x, v.co.y)


# ---------------------------------------------------------------- build
bm = bmesh.new()

# Two annuli, in the order the task was stated: the existing outline carried up a
# little, then the flare. The joint rings are the two faces the task says to
# delete.
with trg.layer(bm, MAT_BASE):
    annulus(bm, N18, A18, A18 - WALL, 0.00, Z_COLLAR)
with trg.layer(bm, MAT_TOP):
    annulus(bm, N24, A24, A24 - WALL, Z_BAND, Z_TOP)

# Delete them with FACES_ONLY, not the default. The default takes the edges and
# verts with the face, which is the whole rim -- there would be nothing left to
# bridge, and the failure would look like "Bridge Edge Loops did nothing".
doomed = end_faces(bm, Z_COLLAR) + end_faces(bm, Z_BAND)
if len(doomed) != N18 + N24:
    raise SystemExit("expected %d joint ring faces, found %d; refusing to guess"
                     % (N18 + N24, len(doomed)))
bmesh.ops.delete(bm, geom=doomed, context="FACES_ONLY")

# The precondition. FOUR rims, [18, 18, 24, 24], or stop. This is the check that
# DECISIONS 267 says a bridge script has to have: bridge_loops will happily pair
# the wrong two loops and hand back a valid mesh.
loops = rim_loops(bm)
sizes = sorted(len(l) for l in loops)
if sizes != sorted([N18, N18, N24, N24]):
    raise SystemExit("expected rims [18, 18, 24, 24], got %s -- refusing to bridge"
                     % sizes)

# Name them. Height first, because that is unambiguous; then radius within the
# pair. Radius alone would be tight on the 24 side (64.55 inner vs 64.69 for the
# 18-gon's OUTER rim -- a wall thickness and 0.14 studs apart), and a
# mis-identified rim here is silent.
by_z = {Z_COLLAR: [], Z_BAND: []}
for loop in loops:
    z = round(mean(loop, lambda v: v.co.z), 6)
    if z not in by_z:
        raise SystemExit("a rim is at z=%r, which is neither joint height" % z)
    by_z[z].append(loop)
pairs = {}
for z, (lo, hi) in ((Z_COLLAR, ("18in", "18out")), (Z_BAND, ("24in", "24out"))):
    if len(by_z[z]) != 2:
        raise SystemExit("expected 2 rims at z=%.2f, got %d" % (z, len(by_z[z])))
    a, b = sorted(by_z[z], key=lambda l: mean(l, axis_radius))
    pairs[lo], pairs[hi] = a, b
if abs(mean(pairs["18out"], axis_radius) - R_OUT18) > 1e-3:
    raise SystemExit("the rim I called 18out is not at r=%.4f" % R_OUT18)

# Bridge Edge Loops. This is the bmesh form of the UI operator of the same name
# (the operator is a thin wrapper over it), chosen because it needs no edit-mode
# context and therefore runs identically headless and interactively. Unequal loop
# counts are what force a triangle fan instead of quads: 18 + 24 = 42 faces.
if SKIP_BRIDGE:
    print("MUTATION: bridges skipped on purpose, four rims left open")
elif CROSS:
    lo = sorted(pairs["18out"], key=lambda v: math.atan2(v.co.y, v.co.x))
    hi = sorted(pairs["24out"], key=lambda v: math.atan2(v.co.y, v.co.x))
    with trg.layer(bm, MAT_BAND):
        # One triangle per rim EDGE, so 18 + 24 = 42 -- the same count the real
        # bridge makes -- but each one reaches half a ring round the other side.
        for i in range(N18):
            j = int(round((i + 0.5) * N24 / N18)) + N24 // 2
            bm.faces.new((lo[i], lo[(i + 1) % N18], hi[j % N24]))
        for k in range(N24):
            m = int(round((k + 0.5) * N18 / N24)) + N18 // 2
            bm.faces.new((hi[k], hi[(k + 1) % N24], lo[m % N18]))
        # The inner band is left unbridged on purpose: the mutation exists to turn
        # ONE check red, and leaving it otherwise correct is what makes the red
        # line readable (DECISIONS 270 -- ten red lines say the mutation was too
        # blunt to tell you which assertion fired).
    print("MUTATION: outer band hand-rolled with the correspondence half a ring out")
else:
    pairing = ([("18out", "24in"), ("18in", "24out")] if WRONG_PAIR
               else [("18out", "24out"), ("18in", "24in")])
    with trg.layer(bm, MAT_BAND):
        for a, b in pairing:
            res = bmesh.ops.bridge_loops(bm, edges=edges_of(bm, pairs[a], pairs[b]))
            made = len(res.get("faces", []))
            if made != N18 + N24:
                raise SystemExit("bridge %s->%s made %d faces, expected %d"
                                 % (a, b, made, N18 + N24))
    if WRONG_PAIR:
        print("MUTATION: outer joined to inner, and inner to outer")

mats = [
    trg.material("WallBase", (0.36, 0.38, 0.41), metallic=0.80, roughness=0.42),
    # The band is deliberately a different colour. The topology is the point of
    # this asset and 84 triangles wrapped round a 65-stud ring are not something
    # the eye finds by itself -- a brass band is what makes the join legible.
    trg.material("WallBand", (0.72, 0.55, 0.30), metallic=0.90, roughness=0.30),
    trg.material("WallTop", (0.58, 0.61, 0.64), metallic=0.80, roughness=0.42),
]
# NO BEVEL, and that is a decision rather than an omission. finish()'s bevel is
# angle-filtered at 25 deg, and this band leans out by atan(4.288 / 3.0) = 55 deg
# -- well past the filter -- so the bevel would fire on all 84 band triangles and
# chop them. That is a real property of the pipeline (the filter's "angle" is
# really "is the shape right"; DECISIONS 269), so the honest move is to leave the
# chamfer off rather than to pick an offset small enough to hide the damage.
obj = trg.finish(bm, NAME, mats, bevel=0.0)

# ---------------------------------------------------------------- read back
stats = trg.measure(obj)
print("SUMMARY model=%s" % NAME)
print("SUMMARY 18-gon apothem=%.3f (rim in the place: %.3f)  corners r=%.4f"
      % (A18, 63.712, R_OUT18))
print("SUMMARY 24-gon apothem=%.3f  corners r=%.4f  <- %.3f studs further out"
      % (A24, R_OUT24, A24 - A18))
print("SUMMARY z=%.2f..%.2f  wall thickness=%.2f" % (stats["z"][0], stats["z"][1], WALL))
print("SUMMARY verts=%d polys=%d tris=%d open_edges=%d"
      % (stats["verts"], stats["polys"], stats["tris"], stats["open_edges"]))
# What Studio should say after import, at the measured 5.902. Blender here is
# Z-up and Roblox is Y-up, so the Y and Z of this line swap on the way in.
print("SUMMARY expected_studio_size=%.2f x %.2f x %.2f (Roblox frame)"
      % (stats["size"][0], stats["size"][2], stats["size"][1]))
# Where it goes: the mesh is authored about the axis with z=0 at its base, so the
# base plane's CENTRE is the object origin. The place's 18-gon centre is at
# (-12.200, -, -85.362) and the platform's top surface is y=47.400 (measured by
# dropping probes through this folder pair).
print("SUMMARY place_base_centre=(-12.200, 47.400, -85.362)")
print("SUMMARY place_bbox_centre=(-12.200, %.3f, -85.362)"
      % (47.400 + (stats["z"][1] - stats["z"][0]) / 2.0))

trg.export(obj, NAME, OUT_DIR)
trg.render(NAME, OUT_DIR,
           [("iso", (150.0, -190.0, 120.0)), ("side", (0.0, -260.0, 70.0))],
           (0.0, 0.0, 6.60), 200.0)
print("WROTE %s" % OUT_DIR)
