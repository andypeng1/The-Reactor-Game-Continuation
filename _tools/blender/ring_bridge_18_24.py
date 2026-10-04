# Two coaxial polygon rings, bridged by 42 explicit triangles.
#
# ------------------------------------------------------------------ the spec
#
# The operator handed over a numbered list (2026-10-04). Items 1 and 2 did not
# reach me; items 3-6 did, and they are the whole build:
#
#   3. generate two coaxial polygon rings
#        small: 18 sides, radius 0.8, Z = 0
#        large: 24 sides, radius 1.2, Z = 1
#   4. both rings' END FACES are kept, as n-gons
#   5. bridge the two rings with a triangle scheme
#        18 and 24 split into 6 groups
#        each group takes 3 edges / 4 vertices from the small ring and
#        4 edges / 5 vertices from the large ring, and emits 7 triangles
#        6 groups -> 42 bridge triangles
#        the relations, verbatim:
#          A0-B0-B1   A0-A1-B2   A0-B2-B1   A1-A2-B3
#          A1-B3-B2   A2-A3-B4   A2-B4-B3
#   6. materials: both end faces blue; all bridge triangles red
#
# --------------------------------------------------------- how it is read
#
# "半径" is taken as the CIRCUMRADIUS (the distance to the vertices), because the
#   bridge is specified over vertices A0..A3 / B0..B4 and those live on it. The
#   other reading -- apothem, i.e. the face plane -- is printed as well, so the
#   choice is visible rather than buried. CLAUDE.md 0.18 face five: a word that
#   makes a choice for you is not a measurement.
#
# "端面保留，作为 n-gon" is read as: this is a CLOSED SOLID. An 18-gon cap at
#   Z=0, a 24-gon cap at Z=1, and the 42 triangles in between. Exactly two end
#   faces exist, which is what item 6 colours. V=42, E=84, F=44, chi=2.
#
# The 42 is not a choice. For an annulus with a and b boundary vertices the
# triangle count is FORCED to a+b by Euler: chi = V-E+F = (a+b) - (3F+a+b)/2 + F
# = 0 gives F = a+b = 18+24 = 42. The operator's count is the exact one.
#
# ----------------------------------------------------- one thing about winding
#
# The seven triples above are NOT consistently wound. Measured on group 0:
#   (A0,B0,B1) has an INWARD normal while (A0,A1,B2) and (A0,B2,B1) are outward.
# The TOPOLOGY is right -- every interior edge is used exactly twice, and 30 of
# them are used in OPPOSITE directions while 12 are used in the SAME direction,
# which is exactly what inconsistent winding looks like -- so a consistent
# outward orientation exists and trg.finish()'s recalc_face_normals finds it.
# The faces are created in the operator's literal order (faithful, and it is what
# the measurement above is about) and the checker then PROVES the shipped result
# is outward, by two independent volume computations plus a per-face test. The
# winding is reported, not silently repaired.
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/blender/ring_bridge_18_24.py
#
# Then, and only then, believe anything:
#   ... --python _tools/blender/ring_bridge_18_24_check.py

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

# ============================================================ SPEC (item 3)
# Every number the operator gave. Nothing below this block is his.
N_SMALL, N_LARGE = 18, 24          # sides
R_SMALL, R_LARGE = 0.8, 1.2        # circumradius, same units as Z
Z_SMALL, Z_LARGE = 0.0, 1.0        # the two ring planes
GROUPS = 6                         # item 5

# Phase: both rings get a vertex at azimuth 0. That is what makes the grouping
# line up -- A0 and B0 coincide in azimuth, so group k spans 60k..60(k+1) with
# A_3k+p at 60k + 20p and B_4k+q at 60k + 15q. A3 and B4 land on 60(k+1), which
# is the next group's A0/B0, so the groups share their seam vertices for free.
PHASE_A = 0.0
PHASE_B = 0.0

# ============================================================ SPEC (item 5)
# Verbatim, as (ring, offset) triples. Offset 3 == 3g+3, i.e. the NEXT group's A0.
BRIDGE = [
    [("A", 0), ("B", 0), ("B", 1)],   # A0-B0-B1
    [("A", 0), ("A", 1), ("B", 2)],   # A0-A1-B2
    [("A", 0), ("B", 2), ("B", 1)],   # A0-B2-B1
    [("A", 1), ("A", 2), ("B", 3)],   # A1-A2-B3
    [("A", 1), ("B", 3), ("B", 2)],   # A1-B3-B2
    [("A", 2), ("A", 3), ("B", 4)],   # A2-A3-B4
    [("A", 2), ("B", 4), ("B", 3)],   # A2-B4-B3
]

# The mid-section walk: the same seven segments, each given as the (A,B) PAIR of
# offsets whose midpoint is one end. In boundary order -- see mid_polygon().
MID_CHAIN = [(0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)]

# ============================================================ SPEC (item 6)
M_CAP, M_BRIDGE = 0, 1             # slot 0 = the two end faces, slot 1 = bridge
CAP_RGB = (0.045, 0.13, 0.80)      # blue
BRIDGE_RGB = (0.80, 0.055, 0.045)  # red


def make_materials():
    """Made AFTER trg.new_scene(), not at import time.

    new_scene() is read_factory_settings(use_empty=True), which throws away the
    whole file -- including any material created before it ran. Measured: the
    first version made them at module level and died inside finish() with
    'ReferenceError: StructRNA of type Material has been removed'.
    """
    return [trg.material("RingCap", BRIDGE_RGB if MUT_SWAP_RGB else CAP_RGB,
                         metallic=0.0, roughness=0.62),
            trg.material("RingBridge", CAP_RGB if MUT_SWAP_RGB else BRIDGE_RGB,
                         metallic=0.0, roughness=0.62)]

NAME = "RingBridge18_24"
OUT_DIR = os.environ.get("RING_BRIDGE_OUT",
                         r"D:\BlenderRobloxTestProjects\RingBridge18_24")

# ============================================================ mutations
# Each one deviates from the spec in one named way, so that the checker's
# assertions can be shown to have teeth. An assertion that has never gone red is
# decoration (CLAUDE.md 0.13).
#
# Flags go AFTER `--`. With `--python s.py --flag` Blender treats the flag as a
# file to open, prints `ERROR Cannot read file`, and RUNS TO COMPLETION ANYWAY --
# so the mutation silently does not happen and the check passes. Measured.
FLAGS = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
LOOSE = "--loose" in FLAGS        # skip the build's own asserts so a mutated file
                                  # still gets written and the checker can judge
MUT_FAN = "--fan" in FLAGS        # bridge via bridge_loops instead of the spec
MUT_ONE_CAP = "--one-cap" in FLAGS
MUT_SWAP_MATS = "--swap-mats" in FLAGS
MUT_SWAP_RGB = "--swap-rgb" in FLAGS   # the colours trade places, faces keep their slots
MUT_RADIUS = "--radius" in FLAGS
MUT_ZSHIFT = "--zshift" in FLAGS

def expect(cond, msg):
    """The build's convenience asserts: on by default, off under --loose, because
    a mutation has to be able to emit a wrong file for the checker to judge."""
    if not LOOSE and not cond:
        raise AssertionError(msg)


def ring_pts(n, r, z, phase):
    """One regular n-gon in the plane z, vertices at azimuth phase + 360k/n."""
    out = []
    for k in range(n):
        a = phase + 2.0 * math.pi * k / n
        out.append((r * math.cos(a), r * math.sin(a), z))
    return out


if MUT_RADIUS:
    R_SMALL *= 1.08               # +8% on the 18-gon; the spec says 0.8
    print("MUTATED (--radius): 18-gon circumradius is %.4f, not %.4f"
          % (R_SMALL, R_SMALL / 1.08))
if MUT_ZSHIFT:
    Z_LARGE = 1.25                # the spec says 1.0
    print("MUTATED (--zshift): large ring sits at z=%.2f, not 1.00" % Z_LARGE)
if MUT_SWAP_RGB:
    print("MUTATED (--swap-rgb): the cap is painted red and the bridge blue; "
          "the slots themselves are unchanged")

A_PTS = ring_pts(N_SMALL, R_SMALL, Z_SMALL, PHASE_A)
B_PTS = ring_pts(N_LARGE, R_LARGE, Z_LARGE, PHASE_B)


def gid(ring, g, off):
    """Global vertex id: A occupies 0..N_SMALL-1, B the next N_LARGE."""
    if ring == "A":
        return (3 * g + off) % N_SMALL
    return N_SMALL + (4 * g + off) % N_LARGE


def bridge_tris():
    """The 42 triangles, as triples of global vertex ids, in the spec's order."""
    return [[gid(r, g, o) for (r, o) in tri] for g in range(GROUPS) for tri in BRIDGE]


def check_topology(tris):
    """The one thing winding cannot touch.

    A valid annulus uses every interior edge exactly twice. Winding shows up
    separately, as the direction those two uses run: consistent winding gives
    one (i,j) and one (j,i), inconsistent gives (i,j) twice. Both are counted and
    printed, because the second number is a fact about the operator's list.
    """
    directed = {}
    for t in tris:
        for k in range(3):
            e = (t[k], t[(k + 1) % 3])
            directed[e] = directed.get(e, 0) + 1
    undirected = {}
    same_dir = 0
    for (i, j), c in directed.items():
        key = frozenset((i, j))
        undirected[key] = undirected.get(key, 0) + c
        if c == 2:                      # one directed key used twice
            same_dir += 1
    once = sum(1 for c in undirected.values() if c == 1)
    twice = sum(1 for c in undirected.values() if c == 2)
    stray = sorted(c for c in undirected.values() if c not in (1, 2))
    print("bridge topology: %d edges -> %d interior (x2), %d boundary (x1)"
          % (len(undirected), twice, once))
    print("literal winding: %d interior edges run the same direction twice "
          "(0 == consistently wound)" % same_dir)
    expect(not stray, "an edge used 3+ times: %r" % (stray,))
    expect(once == N_SMALL + N_LARGE, "boundary edges %d, want %d" % (
        once, N_SMALL + N_LARGE))
    expect(twice == N_SMALL + N_LARGE, "interior edges %d, want %d" % (
        twice, N_SMALL + N_LARGE))
    expect(len(tris) == N_SMALL + N_LARGE, "triangles %d, want %d" % (
        len(tris), N_SMALL + N_LARGE))
    return same_dir


def build():
    bm = bmesh.new()
    A = [bm.verts.new(p) for p in A_PTS]
    B = [bm.verts.new(p) for p in B_PTS]
    bm.verts.ensure_lookup_table()
    allv = A + B

    cap_slot, bridge_slot = (M_BRIDGE, M_CAP) if MUT_SWAP_MATS else (M_CAP, M_BRIDGE)

    if MUT_FAN:
        # The defect this asset exists to not repeat: let bmesh decide the pairing.
        # It returns a valid 42-triangle annulus with a correspondence of its own.
        r1 = [bm.edges.new((A[i], A[(i + 1) % N_SMALL])) for i in range(N_SMALL)]
        r2 = [bm.edges.new((B[i], B[(i + 1) % N_LARGE])) for i in range(N_LARGE)]
        bmesh.ops.bridge_loops(bm, edges=r1 + r2)
        for f in bm.faces:
            f.material_index = bridge_slot
        print("MUTATED (--fan): band built by bridge_loops, not by the spec")
    else:
        tris = bridge_tris()
        check_topology(tris)
        for t in tris:
            f = bm.faces.new([allv[i] for i in t])
            f.material_index = bridge_slot

    # item 4: the two end faces, kept as n-gons. recalc settles the winding.
    caps = [bm.faces.new(list(reversed(B)))]
    if MUT_ONE_CAP:
        print("MUTATED (--one-cap): the 18-gon end face was never made")
    else:
        caps.append(bm.faces.new(A))
    for cap in caps:
        cap.material_index = cap_slot
    return bm


def mid_polygon():
    """The z=0.5 cross-section, as the midpoints of the lateral edges.

    Not decoration: this is how the volume gets checked WITHOUT reusing the
    divergence sum that the mesh itself produces. Every lateral edge runs from
    z=0 to z=1, so it crosses z=0.5 at its own midpoint, and each lateral face
    contributes the segment between two of those midpoints. Walking the seven
    segments per group gives a closed 42-gon: 8 entries per group, one of which
    is the next group's first, so 6*7 = 42 distinct points.
    """
    chain = []
    for g in range(GROUPS):
        for (sa, sb) in MID_CHAIN:
            a = A_PTS[(3 * g + sa) % N_SMALL]
            b = B_PTS[(4 * g + sb) % N_LARGE]
            p = tuple((a[i] + b[i]) / 2.0 for i in range(3))
            if not chain or max(abs(p[i] - chain[-1][i]) for i in range(3)) > 1e-9:
                chain.append(p)
    # A consecutive-only de-dup misses exactly one pair: group 5's last entry IS
    # group 0's first (A_18 == A_0, B_24 == B_0), and the two sit at opposite ends
    # of the list. Left in, the polygon closes with a zero-length edge -- the area
    # is identical, so nothing looks wrong, and the count reads 43. It cost a run.
    if max(abs(chain[-1][i] - chain[0][i]) for i in range(3)) < 1e-9:
        chain.pop()
    return chain


def shoelace(pts):
    a = 0.0
    for k in range(len(pts)):
        p, q = pts[k], pts[(k + 1) % len(pts)]
        a += p[0] * q[1] - q[0] * p[1]
    return 0.5 * a


def ngon_area(n, r):
    return 0.5 * n * r * r * math.sin(2.0 * math.pi / n)


def divergence(mesh):
    """Volume straight out of the mesh's own winding, with stdlib arithmetic.

    mathutils.Vector would work, but this number has to be independent of the
    engine that may have just fixed the normals -- handing it to the engine to
    compute is how a check becomes a tautology.

    It is only meaningful on a CONSISTENTLY wound mesh. Run on the freshly built
    faces (the operator's literal order, 12 of 84 interior edges running the same
    way twice) it returns -0.367 for a solid whose volume is 3.111 -- a number
    that is wrong by more than the volume and looks like a geometry bug. So this
    is called after trg.finish(), on the mesh as it will ship.
    """
    v = 0.0
    vs, ps = mesh.vertices, mesh.polygons
    for f in ps:
        idx = f.vertices
        p = vs[idx[0]].co
        for k in range(1, len(idx) - 1):
            q, r = vs[idx[k]].co, vs[idx[k + 1]].co
            v += (p.x * (q.y * r.z - q.z * r.y)
                  - p.y * (q.x * r.z - q.z * r.x)
                  + p.z * (q.x * r.y - q.y * r.x)) / 6.0
    return v


def prismatoid_volume():
    A18 = ngon_area(N_SMALL, R_SMALL)
    A24 = ngon_area(N_LARGE, R_LARGE)
    Am = shoelace(mid_polygon())
    h = Z_LARGE - Z_SMALL
    return h * (A18 + 4.0 * Am + A24) / 6.0, A18, A24, Am


def main():
    trg.new_scene()     # --factory-startup leaves the default cube in the scene,
                        # and it renders: the first pass was one grey box with the
                        # asset inside it, which is exactly the kind of thing the
                        # numbers cannot tell you (CLAUDE.md 0.14b).
    if FLAGS:
        print("MUTATION FLAGS: %s   (LOOSE=%s)" % (", ".join(sorted(FLAGS)), LOOSE))
    bm = build()

    v_prism, A18, A24, Am = prismatoid_volume()
    print("spec: %d-gon r=%.4f z=%.2f | %d-gon r=%.4f z=%.2f | %d groups"
          % (N_SMALL, R_SMALL, Z_SMALL, N_LARGE, R_LARGE, Z_LARGE, GROUPS))
    print("apothem (the other reading of 'radius'): %.6f / %.6f"
          % (R_SMALL * math.cos(math.pi / N_SMALL),
             R_LARGE * math.cos(math.pi / N_LARGE)))
    print("areas: A18=%.6f  A24=%.6f  mid-section(%d-gon)=%.6f"
          % (A18, A24, len(mid_polygon()), Am))

    obj = trg.finish(bm, NAME, make_materials(), bevel=0.0)
    m = trg.measure(obj)
    # Keyed by (vertex count, material index) because item 6 is a statement about
    # which faces wear which colour, and a face census that ignores the slot says
    # nothing about it. The first pass left every face on slot 0 -- 44 blue faces,
    # no red anywhere -- and the census here would have agreed with itself.
    census = {}
    for p in obj.data.polygons:
        k = (len(p.vertices), p.material_index)
        census[k] = census.get(k, 0) + 1
    n18 = census.get((N_SMALL, M_CAP), 0)
    n24 = census.get((N_LARGE, M_CAP), 0)
    ntri = census.get((3, M_BRIDGE), 0)
    print("face census (verts, material slot) -> count: %s"
          % "  ".join("%dx slot%d=%d" % (k[0], k[1], v)
                      for k, v in sorted(census.items())))

    # Two genuinely different routes to one number: a mid-section polygon through
    # the prismatoid formula, and a surface integral over the 44 faces as wound.
    # Agreement means the winding is OUTWARD (the integral is unsigned-sensitive)
    # and the geometry is the solid the spec describes.
    v_div = divergence(obj.data)
    print("volume: prismatoid=%.9f  divergence=%.9f  delta=%.2e (%.1e relative)"
          % (v_prism, v_div, abs(v_prism - v_div),
             abs(v_prism - v_div) / v_prism))
    # RELATIVE, and loose on purpose: Blender stores mesh vertex coordinates as
    # float32, so a volume read back out of mesh.vertices cannot be better than
    # ~1e-7 relative. Measured here: 4.5e-08. A 1e-9 tolerance does not test the
    # geometry, it tests the storage format, and it fails.
    expect(abs(v_div - v_prism) < 1e-6 * v_prism, "winding or geometry is wrong")

    print("mesh: verts=%d polys=%d tris=%d open_edges=%d" % (
        m["verts"], m["polys"], m["tris"], m["open_edges"]))
    print("caps kept as n-gons: %d x %d-gon + %d x %d-gon ; bridge: %d triangles"
          % (n18, N_SMALL, n24, N_LARGE, ntri))
    print("material slots: %s" % ", ".join(
        "%d=%s" % (i, m.name) for i, m in enumerate(obj.data.materials)))
    expect((n18, n24, ntri) == (1, 1, N_SMALL + N_LARGE), "face census is wrong")
    expect(m["open_edges"] == 0, "the solid is not closed")
    # Euler for a sphere: V - E + F = 2. Measured from the shipped mesh.
    E = (3 * ntri + N_SMALL + N_LARGE) // 2
    expect(m["verts"] - E + m["polys"] == 2, "not a closed 2-manifold")

    print("size=%.6f x %.6f x %.6f  z=%.6f..%.6f" % (
        m["size"][0], m["size"][1], m["size"][2], m["z"][0], m["z"][1]))
    # Export divides by STUDS_PER_UNIT and a Roblox import multiplies it back, so
    # the radii and the height land in Studio as the numbers item 3 asked for.
    print("expected_studio_size=%s" % (
        " x ".join("%.4f" % (d * trg.STUDS_PER_UNIT) for d in m["size"]),))
    trg.export([obj], NAME, OUT_DIR)
    trg.render(NAME, OUT_DIR,
               [("iso", (3.0, -3.6, 2.6)), ("side", (0.0, -5.0, 0.5)),
                ("plan", (0.0, 0.01, 5.0))],
               (0.0, 0.0, 0.5), 3.6)


main()
