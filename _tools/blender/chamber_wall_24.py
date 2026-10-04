# An 18-sided platform rim grown OUTWARD into a 24-sided wall, the two joined by
# Bridge Edge Loops. The 18-gon is modelled here too, because the join is only
# legible next to the thing being joined.
#
# WHY THIS IS A BLENDER JOB. A Roblox MeshPart is a finished triangle soup: there
# is no operator on that side that takes two closed rims of DIFFERENT vertex
# counts and sews them together -- the 42 triangles would have to be computed by
# hand and written into the file. This is the one shape the parts-based modeller
# cannot reach at all. Not "harder". Impossible. (docs/SNIPPETS.md 5.15; the same
# topology at toy scale is TransitionPillar.)
#
# ============================================================ THE RULE
#
# THE 18-GON is not a choice. Measured in the place (Workspace.Folder.Folder.
# Folder.18, 1440 inward rays at the platform's own height, ZERO misses):
#
#     corner radius 64.6951      <- its OUTERMOST
#     face  radius 63.7114       <- and 64.6951 = 63.7114 / cos(pi/18)
#     corners on azimuth 0 + 20k, exactly (offGrid 0.000 on all 18)
#     panel faces on azimuth 10 + 20k
#
# One polygon, two radii: 63.7114 is where its flat sides are, 64.6951 is where
# its corners are. Which of the two "the 18 part's outermost" means is the whole
# of this round's correction -- and it is the corners.
#
# (The panels are 20.705 long, which is 18.458 deg of the 20 deg step: they leave
# a 1.54 deg notch at every corner. The PLATE is what fills it. Modelled here as
# measured rather than as drawn, because a reference that has been tidied up is a
# reference that no longer matches the place.)
#
# THE 24-GON: corners on 0 + 15k, faces on 7.5 + 15k, and its INNER face plane is
# 64.6951 -- the 18-gon's corner radius. That is the correction. A 24-gon of
# inradius R contains an 18-gon of circumradius R' only if R >= R', and 64.6951 is
# the smallest value that works, so the wall touches the ring's corners and stands
# off it by at most 0.984 studs at the ring's face planes, and never crosses it.
# Basing the wall on 63.7114 instead -- the ring's FACE radius, which is what the
# previous build did -- puts the wall's own inner corners at 64.1514 and lets all
# 18 of the ring's corners pierce straight through it. `--inner-at-face` builds
# that version on purpose so the check can be watched going red.
#
# THE 4/3 RULE (the operator's own statement of the join, 2026-10-04):
#     3 * 20 deg = 4 * 15 deg = 60 deg
# three ring panels and four wall panels span the same sector, and 6 of the ring's
# 18 corners are also wall corners. Asserted, not assumed -- see J4 in the check.
#
# WHAT IS FREE: the wall's thickness (4.00), how tall the flare takes (Z_BAND) and
# how tall the wall is (Z_TOP). One number each.

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

NAME_WALL = "ChamberWall24"
NAME_RING = "ChamberRing18_ref"
OUT_DIR = os.environ.get("CHAMBER_WALL_OUT",
                         r"D:\BlenderRobloxTestProjects\ChamberWall24")

# Mutations. A check nobody has ever watched go red is a check that measures
# nothing (DECISIONS 205), and every failure mode below is QUIET: an unbridged
# model is still a valid mesh, and a band joined to the wrong partners is still
# 84 triangles that pass every count test.
SKIP_BRIDGE = "--no-bridge" in sys.argv     # leave all four rims open
WRONG_PAIR = "--wrong-pair" in sys.argv     # outer18 -> inner24, and vice versa
INNER_AT_FACE = "--inner-at-face" in sys.argv   # == the bug this asset fixes
WALL_PHASE = "--wall-phase-half" in sys.argv     # 24-gon rotated half a step

# ---------------------------------------------------------------- measured
#
# Everything here was read off Workspace.Folder.Folder.Folder.18 in The Reactor
# [Rebuild]. None of it is a knob; the build refuses to run if the plate is not
# the 18-gon the sweep says it is.
N18 = 18
RING_A = 63.7114        # face-plane radius (the sweep's rmin)
RING_R = 64.6951        # corner radius (the sweep's rmax) == RING_A / cos(pi/18)
PLATE_T = 0.65          # the plate spans z -0.65 .. 0  (place: y 46.750 .. 47.400)
PANEL_W = 20.7055       # chord; the 18 measured values span 20.7041 .. 20.7074
PANEL_D = 5.00          # radial depth -- its outer face IS RING_A
PANEL_H = 0.65
PANEL_R = RING_A - PANEL_D * 0.5     # 61.2114; the place reads 61.2114 .. 61.2122
PANEL_FACE_AZ = 10.0    # face centres; corners are therefore on 0 + 20k

# ---------------------------------------------------------------- free
WALL = 4.00             # wall thickness, horizontal
Z_BAND = 3.00           # height the 18 -> 24 flare finishes at
Z_TOP = 13.20           # top of the wall

# ---------------------------------------------------------------- derived
N24 = 24
A18_OUT = RING_A + WALL                     # 67.7114 -- the collar's outer apothem
A24_IN = RING_A if INNER_AT_FACE else RING_R    # 64.6951 by the rule
A24_OUT = A24_IN + WALL                     # 68.6951
WALL24_PHASE = (math.pi / 24) if WALL_PHASE else 0.0

R_18OUT = A18_OUT / math.cos(math.pi / N18)     # 68.7564
R_18IN = RING_R                                 # 64.6951
R_24OUT = A24_OUT / math.cos(math.pi / N24)     # 69.2880
R_24IN = A24_IN / math.cos(math.pi / N24)       # 65.2536


# ---------------------------------------------------------------- helpers
def ngon(bm, n, apothem, z, phase=0.0):
    """One regular n-gon of verts, corners on `phase` + 360/n.

    Radius is derived from the APOTHEM rather than the other way round, so that
    the sides -- which are what the neighbour actually touches -- land on the
    number that was measured off it.
    """
    r = apothem / math.cos(math.pi / n)
    return [bm.verts.new((r * math.cos(phase + 2 * math.pi * k / n),
                          r * math.sin(phase + 2 * math.pi * k / n), z))
            for k in range(n)]


def annulus(bm, n, a_out, a_in, z0, z1, phase=0.0):
    """A closed n-sided tube: outer wall, inner wall, and a ring at each end.

    Built by hand rather than with trg.revolve, for two reasons. revolve lathes
    an OPEN profile and caps each end with ONE n-gon, and an annulus end is a
    ring -- a face with a hole, which no single n-gon can be. And building the end
    as n quads is what makes "delete the end" a well defined operation that leaves
    TWO boundary loops (the outer rim and the inner rim), which is exactly what
    the bridge wants to be handed.
    """
    o0, o1 = ngon(bm, n, a_out, z0, phase), ngon(bm, n, a_out, z1, phase)
    i0, i1 = ngon(bm, n, a_in, z0, phase), ngon(bm, n, a_in, z1, phase)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))    # outer wall
        bm.faces.new((i0[k], i0[j], i1[j], i1[k]))    # inner wall
        bm.faces.new((i0[k], i0[j], o0[j], o0[k]))    # ring at z0
        bm.faces.new((i1[k], i1[j], o1[j], o1[k]))    # ring at z1


def prism(bm, n, apothem, z0, z1, phase=0.0):
    """A closed n-gon prism: the plate. One n-gon cap at each end."""
    b0, b1 = ngon(bm, n, apothem, z0, phase), ngon(bm, n, apothem, z1, phase)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((b0[k], b0[j], b1[j], b1[k]))
    bm.faces.new(list(reversed(b0)))
    bm.faces.new(b1)


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


# ================================================================ the wall
bm = bmesh.new()

# Two annuli, in the order the task was stated: the existing outline carried up a
# little, then the flare. The joint rings are the two faces the task says to
# delete.
with trg.layer(bm, 0):
    annulus(bm, N18, A18_OUT, RING_A, 0.00, Z_BAND)
with trg.layer(bm, 2):
    annulus(bm, N24, A24_OUT, A24_IN, Z_BAND, Z_TOP, phase=WALL24_PHASE)

# Delete them with FACES_ONLY, not the default. The default takes the edges and
# verts with the face, which is the whole rim -- there would be nothing left to
# bridge, and the failure would look like "Bridge Edge Loops did nothing".
doomed = end_faces(bm, Z_BAND)
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

# Name them BY VERTEX COUNT first and radius second, and that order is not
# cosmetic: all four rims are at the same height here (Z_BAND), and sorted by
# radius alone they come out 64.6951, 65.2536, 68.7564, 69.2880 -- the two 18-gon
# rims straddle the two 24-gon ones. Splitting "lower two / upper two" would pair
# the 18-inner with the 24-inner and call it a day. The count cannot be confused.
by_n = {N18: [], N24: []}
for loop in loops:
    z = round(mean(loop, lambda v: v.co.z), 6)
    if z != round(Z_BAND, 6):
        raise SystemExit("a rim is at z=%r, which is not the joint height %r"
                         % (z, Z_BAND))
    by_n[len(loop)].append(loop)
pairs = {}
for n, (lo, hi) in ((N18, ("18in", "18out")), (N24, ("24in", "24out"))):
    if len(by_n[n]) != 2:
        raise SystemExit("expected 2 rims of %d verts, got %d" % (n, len(by_n[n])))
    a, b = sorted(by_n[n], key=lambda l: mean(l, axis_radius))
    pairs[lo], pairs[hi] = a, b
if abs(mean(pairs["18in"], axis_radius) - R_18IN) > 1e-3:
    raise SystemExit("the rim I called 18in is not at r=%.4f" % R_18IN)
if abs(mean(pairs["24in"], axis_radius) - R_24IN) > 1e-3:
    raise SystemExit("the rim I called 24in is not at r=%.4f" % R_24IN)

# Bridge Edge Loops. This is the bmesh form of the UI operator of the same name
# (the operator is a thin wrapper over it), chosen because it needs no edit-mode
# context and therefore runs identically headless and interactively. Unequal loop
# counts are what force a triangle fan instead of quads: 18 + 24 = 42 faces.
if SKIP_BRIDGE:
    print("MUTATION: bridges skipped on purpose, four rims left open")
else:
    pairing = ([("18out", "24in"), ("18in", "24out")] if WRONG_PAIR
               else [("18out", "24out"), ("18in", "24in")])
    with trg.layer(bm, 1):
        for a, b in pairing:
            res = bmesh.ops.bridge_loops(bm, edges=edges_of(bm, pairs[a], pairs[b]))
            made = len(res.get("faces", []))
            if made != N18 + N24:
                raise SystemExit("bridge %s->%s made %d faces, expected %d"
                                 % (a, b, made, N18 + N24))
    if WRONG_PAIR:
        print("MUTATION: outer joined to inner, and inner to outer")

wall = trg.finish(bm, NAME_WALL, [
    trg.material("WallBase", (0.36, 0.38, 0.41), metallic=0.80, roughness=0.42),
    # The band is deliberately a different colour. The topology is the point of
    # this asset and 84 triangles wrapped round a 65-stud ring are not something
    # the eye finds by itself -- a brass band is what makes the join legible.
    trg.material("WallBand", (0.72, 0.55, 0.30), metallic=0.90, roughness=0.30),
    trg.material("WallTop", (0.58, 0.61, 0.64), metallic=0.80, roughness=0.42),
], bevel=0.0)
# NO BEVEL, and that is a decision rather than an omission. finish()'s bevel is
# angle-filtered at 25 deg and the band leans out by atan(0.984 / 3.00) = 18.2
# deg, so the filter would take some band edges and not others -- 42 fan
# triangles of three different shapes would come back 42 triangles of three
# different shapes with 25 of them rounded. The join IS the subject here; a
# chamfer that lands unevenly on it is noise, not finish.

# ================================================================ the ring
#
# Modelled as measured, not as drawn -- including the 1.54 deg notch the panels
# leave at each corner, which the plate fills. A tidied-up reference is a
# reference that no longer matches the place it is supposed to be a reference
# FOR.
bm2 = bmesh.new()
with trg.layer(bm2, 0):
    prism(bm2, N18, RING_A, -PLATE_T, 0.0)
with trg.layer(bm2, 1):
    for k in range(N18):
        az = math.radians(PANEL_FACE_AZ) + 2 * math.pi * k / N18
        trg.box(bm2, (PANEL_R * math.cos(az), PANEL_R * math.sin(az), -PLATE_T * 0.5),
                (PANEL_W, PANEL_D, PANEL_H),
                rot_z=az + math.pi * 0.5)   # +X -> the tangential direction
        # trg.box rotates about Z only: +X lands on (cos, sin), so the long axis
        # is tangential when rot_z = azimuth + 90 deg. Getting this wrong is
        # silent -- a box rotated 90 deg off is still a box, still 20.7 x 5, and
        # the ring still closes; it is only wrong where the panels meet.
ring = trg.finish(bm2, NAME_RING, [
    trg.material("RingPlate", (0.30, 0.31, 0.33), metallic=0.65, roughness=0.55),
    trg.material("RingPanel", (0.44, 0.47, 0.50), metallic=0.75, roughness=0.45),
], bevel=0.0)
# NO BEVEL on the reference either, and here it is not a style choice. The plate's
# top Edge is the thing being joined to, and beveling it insets the cap by 0.05 --
# the measured corner radius then reads 64.6435 instead of 64.6943, and the join
# check would be comparing the wall's foot against an edge that no longer exists.
# The instrument is not allowed to round off what it measures.

# ---------------------------------------------------------------- read back
stats = trg.measure(wall)
rstat = trg.measure(ring)
print("SUMMARY model=%s" % NAME_WALL)
print("SUMMARY 18-gon: faces %.4f  corners %.4f (MEASURED in the place)"
      % (RING_A, RING_R))
print("SUMMARY 24-gon: faces %.4f  corners %.4f  <- inner face ON the 18-gon's corners"
      % (A24_IN, R_24IN))
print("SUMMARY   wall touches the ring's 18 corners; worst standoff %.4f studs at its"
      % (A24_IN - RING_A))
print("SUMMARY   own face planes.  %s" % ("(INNER-AT-FACE MUTATION)"
                                          if INNER_AT_FACE else ""))
print("SUMMARY flare %.0f -> %.0f over %.2f studs, then vertical to %.2f"
      % (A18_OUT, A24_OUT, Z_BAND, Z_TOP))
print("SUMMARY wall  verts=%d polys=%d tris=%d open_edges=%d"
      % (stats["verts"], stats["polys"], stats["tris"], stats["open_edges"]))
print("SUMMARY ring  verts=%d polys=%d tris=%d (18 panels + the plate, loose parts)"
      % (rstat["verts"], rstat["polys"], rstat["tris"]))
# What Studio should say after import, at the measured 5.902. Blender here is
# Z-up and Roblox is Y-up, so the Y and Z of this line swap on the way in.
print("SUMMARY expected_studio_size=%.2f x %.2f x %.2f (Roblox frame)"
      % (2 * R_24OUT, Z_TOP + PLATE_T, 2 * R_24OUT))
# Where it goes: authored about the axis with z=0 at the platform top, so the
# origin IS the platform-top centre. The place's 18-gon axis is at
# (-12.200, -, -85.362) and the platform top surface is y = 47.400.
print("SUMMARY place_origin=(-12.200, 47.400, -85.362)   scale 1.0   no rotation")
# A vertex of the 18-gon's corner set lands on azimuth 0 and every 20 deg after,
# and the 24-gon's corner set on 0 and every 15 -- and BOTH sets are invariant
# under a 180 deg rotation, so they are also invariant under the X-mirror the
# FBX importer applies (measured on the laser port: (bx,by,bz) -> (-bx,bz,by),
# i.e. Studio azimuth = 180 - b). A 24-gon offset by 7.5 deg would NOT be, and
# would need correcting after import.

trg.export([wall, ring], NAME_WALL, OUT_DIR)
trg.render(NAME_WALL, OUT_DIR,
           [("iso", (185.0, -235.0, 150.0)),
            ("side", (0.0, -300.0, 45.0)),
            # The join is a PLAN property -- three ring faces against four wall
            # faces is a statement about azimuths, and no eye-level view can show
            # it. This is the one camera that can.
            ("plan", (0.0, 0.01, 300.0))],
           (0.0, 0.0, 6.00), 200.0)
print("WROTE %s" % OUT_DIR)
