# An 18-sided cylinder joined to a 24-sided one by Bridge Edge Loops.
#
# WHY THIS IS A BLENDER JOB AND NOT A STUDIO ONE. A Roblox MeshPart is a finished
# triangle soup: there is no operator on that side that takes two open rims of
# DIFFERENT vertex counts and sews them together -- you would have to compute the
# 42 triangles by hand and write them into the file. This is the one shape the
# parts-based modeller cannot reach at all. Not "harder". Impossible.
#
# THE TOPOLOGY IS THE DELIVERABLE; everything else here is decoration. Radii,
# heights and the bevel are free choices. What must be exactly right is that the
# result is ONE closed manifold, with an 18-gon rim and a 24-gon rim joined by
# exactly 18 + 24 = 42 triangles, and no twist in the band between them. So those
# numbers are ASSERTED here and then read back out of the exported FILE by
# transition_pillar_check.py -- this script's own printout is not evidence, for
# the same reason the Studio side reads instance state instead of module state
# (CLAUDE.md 0.2, and its Blender half, 0.6).
#
# Build loop, in the order the task was stated: two cylinders, delete the faces
# that face each other, Bridge Edge Loops across the gap.

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

NAME = "TransitionPillar"
OUT_DIR = os.environ.get("TRANSITION_PILLAR_OUT",
                         r"D:\BlenderRobloxTestProjects\TransitionPillar")
# The mutation run: skip the bridge and leave the rims open. A check nobody has
# ever watched go red is a check that measures nothing (DECISIONS 205), and the
# failure mode here is quiet -- an unbridged model is still a valid mesh, it is
# just not the model that was asked for.
SKIP_BRIDGE = "--no-bridge" in sys.argv
# The second mutation: flip the top cylinder's face winding before bridging, to
# try to make Bridge Edge Loops pair the two rims the long way round.
#
# MEASURED, AND THE ANSWER IS NO. The result is byte-identical to the correct
# build -- 126 verts, 128 polys, min band centroid radius 2.1837, to the digit.
# Two independent reasons, both of which have to be true for a winding mistake to
# reach the band: trg.finish recalculates face normals, which undoes the flip; and
# bridge_loops derives the correspondence from the geometry rather than from the
# loop order it was handed. So NO winding mistake can twist this bridge, and the
# twist guard is not against something this operator does. Kept because it is the
# cheap way to re-measure that whenever the pipeline changes -- and because a
# mutation that comes back green is a result, not a failure.
TWIST = "--twist" in sys.argv
# The third mutation, and the only one that can actually produce a crossed band:
# hand-roll the bridge with each vertex paired to the one OPPOSITE it instead of
# the one beside it. Keeps the face count (18 + 24 = 42), the triangle-ness and
# the edge coverage, so the count tests stay green and the band's own geometry is
# the only thing wrong -- which is the single claim the twist test makes. Measured
# first, believed second.
CROSS = "--cross" in sys.argv

# ---------------------------------------------------------------- design
#
# In STUDS, about the world Z axis. trg.export divides by STUDS_PER_UNIT on the
# way out so the import lands back on these numbers.
#
# The gap between BASE_Z1 and TOP_Z0 is not slack -- it IS the bridge. If the
# base's top face and the top cylinder's bottom face were coincident, the two
# rims would be coplanar, the bridged band would have zero height, and all 42
# triangles would be degenerate: zero area, invisible, and still "42 faces".
# An 0.8-stud band is what makes the transition something you can see.
BASE_SIDES, BASE_R, BASE_Z = 18, 2.40, (0.00, 1.60)
TOP_SIDES, TOP_R, TOP_Z = 24, 2.10, (2.40, 4.60)

MAT_BASE, MAT_BAND, MAT_TOP = 0, 1, 2


# ---------------------------------------------------------------- helpers
def cap_face(bm, ring):
    """The face that is exactly this ring of verts.

    Both caps are the same polygon count, so `len(f.verts) == n` cannot tell the
    top cap from the bottom one. Matching the vertex SET can, and it fails loudly
    (None) instead of silently deleting the wrong end -- which would leave the
    two rims at the far ends of the model, 4.6 studs apart, for Bridge Edge Loops
    to join into a barrel that swallows the whole pillar.
    """
    want = set(ring)
    for f in bm.faces:
        if len(f.verts) == len(ring) and set(f.verts) == want:
            return f
    return None


def rim_loops(bm):
    """Every boundary edge, walked into rings. Returns a list of ordered verts.

    This runs BEFORE the bridge, as a precondition. Bridge Edge Loops decides
    what to connect from the geometry it is handed; hand it four open rims
    instead of two and it will still produce a mesh, just not this one. Counting
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


def band_faces(mesh, z_lo, z_hi, tol=1e-6):
    """The bridge, identified by GEOMETRY rather than by creation order.

    A face is in the band iff it touches both rims. That survives the bevel and
    it survives re-import, where face order and vertex indices do not -- and it
    is the same predicate transition_pillar_check.py uses on the exported file,
    so the two are measuring the same thing rather than two different guesses.

    Takes a Mesh, not a bmesh: this is asked AFTER trg.finish(), because the
    question it answers is whether the bevel touched the band, and before finish
    there is no bevel yet. (Mesh has .polygons; .faces was removed.)
    """
    out = []
    for p in mesh.polygons:
        zs = [mesh.vertices[i].co.z for i in p.vertices]
        if min(zs) <= z_lo + tol and max(zs) >= z_hi - tol:
            out.append(p)
    return out


# ---------------------------------------------------------------- build
bm = bmesh.new()

# Two cylinders. Each keeps its far cap and starts with a cap at the joint too;
# the joint caps are the two faces the task says to delete.
with trg.layer(bm, MAT_BASE):
    base_rings = trg.revolve(bm, [(BASE_R, BASE_Z[0]), (BASE_R, BASE_Z[1])],
                             n=BASE_SIDES)
with trg.layer(bm, MAT_TOP):
    top_rings = trg.revolve(bm, [(TOP_R, TOP_Z[0]), (TOP_R, TOP_Z[1])],
                            n=TOP_SIDES)

if TWIST:
    bmesh.ops.reverse_faces(
        bm, faces=[f for f in bm.faces if f.material_index == MAT_TOP])

# Delete them with FACES_ONLY, not the default. The default takes the edges and
# verts with the face, which is the whole rim -- there would be nothing left to
# bridge, and the failure would look like "Bridge Edge Loops did nothing".
doomed = [cap_face(bm, base_rings[-1]), cap_face(bm, top_rings[0])]
if None in doomed:
    raise SystemExit("could not find the two joint caps; refusing to guess")
bmesh.ops.delete(bm, geom=doomed, context="FACES_ONLY")

# The precondition check. Two rims, 18 and 24 verts, or stop.
sizes = sorted(len(l) for l in rim_loops(bm))
if sizes != [BASE_SIDES, TOP_SIDES]:
    raise SystemExit("expected rims %s, got %s -- refusing to bridge"
                     % ([BASE_SIDES, TOP_SIDES], sizes))

# Bridge Edge Loops. This is the bmesh form of the UI operator of the same name
# (the operator is a thin wrapper over it), chosen because it needs no edit-mode
# context and therefore runs identically headless and interactively. Unequal loop
# counts are what force a triangle fan instead of quads: 18 + 24 = 42 faces.
if SKIP_BRIDGE:
    print("MUTATION: bridge skipped on purpose, rims left open")
elif CROSS:
    lo = sorted([v for v in bm.verts if abs(v.co.z - BASE_Z[1]) < 1e-4],
                key=lambda v: math.atan2(v.co.y, v.co.x))
    hi = sorted([v for v in bm.verts if abs(v.co.z - TOP_Z[0]) < 1e-4],
                key=lambda v: math.atan2(v.co.y, v.co.x))
    with trg.layer(bm, MAT_BAND):
        # One triangle per rim EDGE, so 18 + 24 = 42 -- the same count the real
        # bridge makes -- but each one reaches to the far side of the other rim.
        for i in range(BASE_SIDES):
            j = int(round((i + 0.5) * TOP_SIDES / BASE_SIDES)) + TOP_SIDES // 2
            bm.faces.new((lo[i], lo[(i + 1) % BASE_SIDES], hi[j % TOP_SIDES]))
        for k in range(TOP_SIDES):
            m = int(round((k + 0.5) * BASE_SIDES / TOP_SIDES)) + BASE_SIDES // 2
            bm.faces.new((hi[k], hi[(k + 1) % TOP_SIDES], lo[m % BASE_SIDES]))
    print("MUTATION: band hand-rolled with the correspondence half a ring out")
else:
    with trg.layer(bm, MAT_BAND):
        res = bmesh.ops.bridge_loops(
            bm, edges=[e for e in bm.edges if len(e.link_faces) == 1])
    made = len(res.get("faces", []))
    if made != BASE_SIDES + TOP_SIDES:
        raise SystemExit("bridge made %d faces, expected %d"
                         % (made, BASE_SIDES + TOP_SIDES))

mats = [
    trg.material("PillarBase", (0.36, 0.38, 0.41), metallic=0.80, roughness=0.42),
    # The band is deliberately a different colour. The topology is the point of
    # this asset and 42 triangles on a 2.4-stud radius are not something the eye
    # finds by itself -- a brass band is what makes the transition legible in the
    # render instead of a thing you have to be told to look for.
    trg.material("PillarBand", (0.72, 0.55, 0.30), metallic=0.90, roughness=0.30),
    trg.material("PillarTop", (0.58, 0.61, 0.64), metallic=0.80, roughness=0.42),
]
# The bevel is switched off for the crossed mutation on purpose. Its filter is a
# 25 deg face angle, and a correct band leans in only 20.6 deg, so the bevel
# skips the band -- but a CROSSED band is steep, so the bevel fires on it, chops
# every band triangle and drags the rims off their design heights. That is a real
# property worth writing down (the bevel's own filter depends on the band being
# right), but it buries the one thing this mutation exists to measure.
obj = trg.finish(bm, NAME, mats, bevel=0.0 if CROSS else 0.06)

# ---------------------------------------------------------------- read back
stats = trg.measure(obj)
band = band_faces(obj.data, BASE_Z[1], TOP_Z[0]) if not SKIP_BRIDGE else []
tri_band = [f for f in band if len(f.vertices) == 3]
print("SUMMARY model=%s" % NAME)
print("SUMMARY size=%.2f x %.2f x %.2f  z=%.2f..%.2f"
      % (stats["size"][0], stats["size"][1], stats["size"][2],
         stats["z"][0], stats["z"][1]))
print("SUMMARY verts=%d polys=%d tris=%d open_edges=%d"
      % (stats["verts"], stats["polys"], stats["tris"], stats["open_edges"]))
# The bevel is angle-filtered, so it should have skipped both joint rims: the
# wall is vertical and the band leans in by atan(0.30/0.80) = 20.6 deg, under the
# 25 deg threshold. If it did not skip them the band would be re-cut and this
# count would move -- which is why it is printed rather than assumed.
print("SUMMARY band_faces=%d all_triangles=%s" % (len(band), len(band) == len(tri_band)))
# What Studio should say after import, at the measured 5.902. Blender here is
# Z-up and Roblox is Y-up, so the Y and Z of this line swap on the way in.
print("SUMMARY expected_studio_size=%.2f x %.2f x %.2f (Roblox frame)"
      % (stats["size"][0], stats["size"][2], stats["size"][1]))

trg.export(obj, NAME, OUT_DIR)
trg.render(NAME, OUT_DIR,
           [("iso", (6.0, -7.0, 5.0)), ("side", (0.0, -10.0, 2.30))],
           (0.0, 0.0, 2.30), 7.0)
print("WROTE %s" % OUT_DIR)
