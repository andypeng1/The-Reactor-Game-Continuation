# Re-import what chamber_wall_24.py exported and measure IT -- not the bmesh that
# built it.
#
# WHY A SEPARATE PASS. The build loop is not evidence. Everything the build script
# prints is a statement about the objects it holds in memory, and an export that
# bakes transforms into geometry, or a node that lands at the wrong scale, or a
# half-step rotation applied on the way out, are all invisible from there: the
# numbers print identically. This file opens the SHIPPED BYTES, welds them, and
# measures the result. Same rule as CLAUDE.md 0.2, on the Blender side.
#
# Both formats are checked because they do not agree. Measured on the laser port:
# the FBX path lands at design size and the glTF path lands 1.6943x. Two formats,
# two answers -- so each one gets asked.
#
# ============================================================ one trap in here
#
# THE TWO FORMATS DO NOT SHIP THE SAME FACES. glTF has no polygons, so it
# triangulates; FBX keeps quads on the way out and the importer rebuilds them, or
# not, depending on the mesh. So nothing below counts FACES. Everything is counted
# in vertices and in triangles-per-surface, because those survive the round trip
# in both formats. (This cost a whole run: a check that counted "42 outer faces"
# read 84 from one file and 126 from the other, and both numbers were about the
# file format rather than about the wall.)
#
# ============================================================ what is asserted
#
# GEOMETRY      1 object per side; wall closed + single shell; ring 19 shells
#               (18 loose panels + the plate -- the reference is loose parts on
#               purpose); the four joint circles [18, 18, 24, 24] at their radii
#
# THE JOIN, which is the entire point of the asset:
#   J1  the wall's inner foot IS the ring's outline -- all 18 of its vertices
#       coincide with the plate's top corners, measured as points in one frame
#   J2  the wall's 24-gon inner face plane == the 18-gon's CORNER radius
#       (64.6951, its outermost). This is the assertion the operator's complaint
#       is about: base the wall on the ring's FACE radius instead and J2 and J3
#       both go red.
#   J3  containment -- no ring vertex lies inside the wall's material
#   J4  the 4/3 rule, counted from the corner rings: 3 ring faces and 4 wall faces
#       per 60 deg sector, and 6 of the ring's 18 corners carry a wall corner
#
# THE BAND       all 84 faces are triangles; 42 inner + 42 outer; every face spans
#                < 1.0 stud radially (the correct band spans 0.53 / 0.56 -- a
#                crossed pairing spans 3.5 / 4.6, so the margin is sixfold); no
#                face wraps more than 40 deg of azimuth; no degenerate faces
#
# Mutations, each named with the assertion it must turn red:
#   --no-bridge          -> open edges (four rims left open)
#   --wrong-pair         -> band radial span
#   --inner-at-face      -> J2 and J3  (the operator's exact complaint)
#   --wall-phase-half    -> J4's corner coincidence, 6 -> 0

import math
import os
import sys
import traceback

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

OUT_DIR = os.environ.get("CHAMBER_WALL_OUT",
                         r"D:\BlenderRobloxTestProjects\ChamberWall24")
NAME = "ChamberWall24"
SPU = trg.STUDS_PER_UNIT
TOL = 2e-3

# Same constants as the build. Restated rather than imported: if the build script
# is edited and this one is not, the two disagree out loud instead of the check
# quietly moving its own goalposts.
N18, N24 = 18, 24
RING_A = 63.7114        # 18-gon face plane   (measured in the place)
RING_R = 64.6951        # 18-gon corner radius (measured) == "its outermost"
WALL = 4.00
Z_BAND = 3.00
Z_TOP = 13.20
PLATE_T = 0.65
PANEL_FACE_AZ = 10.0
A24_IN_EXPECTED = RING_R
A18_OUT = RING_A + WALL
A24_OUT = A24_IN_EXPECTED + WALL
R_18OUT = A18_OUT / math.cos(math.pi / N18)
R_18IN = RING_R
R_24OUT = A24_OUT / math.cos(math.pi / N24)
R_24IN_EXPECTED = A24_IN_EXPECTED / math.cos(math.pi / N24)

FAILS = []
LINES = []


def ok(label, good, detail=""):
    LINES.append("  %-46s %s %s" % (label, "ok  " if good else "FAIL", detail))
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

    Two separate jobs. The units: every number in this file is a stud and the file
    is not, so the scale is applied here, once, rather than at each comparison.
    The welding: glTF has nowhere to put a polygon and splits a vertex whenever a
    corner's attributes differ per face, so the shipped .glb reports hundreds of
    open edges -- every one of them an artefact of the question. Weld by position
    and both formats answer the same way.
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
        faces.append(tuple(idx))
    return pts, faces


# ---------------------------------------------------------------- geometry
def rad(p):
    return math.hypot(p[0], p[1])


def azim(p):
    return math.degrees(math.atan2(p[1], p[0])) % 360.0


def centroid(pts, f):
    n = len(f)
    return tuple(sum(pts[i][k] for i in f) / n for k in range(3))


def area(pts, f):
    a = 0.0
    for k in range(len(f)):
        p, q = pts[f[k]], pts[f[(k + 1) % len(f)]]
        a += (p[0] * q[1] - q[0] * p[1]) + (p[1] * q[2] - q[1] * p[2]) \
            + (p[2] * q[0] - q[2] * p[0])
    return 0.5 * math.sqrt(a * a)


def open_edges(faces):
    use = {}
    for f in faces:
        for k in range(len(f)):
            e = tuple(sorted((f[k], f[(k + 1) % len(f)])))
            use[e] = use.get(e, 0) + 1
    return [e for e, c in use.items() if c != 2]


def shell_sets(pts, faces):
    """Connected components as {"v": vertex index set, "f": [face index]}."""
    parent = list(range(len(pts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for f in faces:
        for k in range(1, len(f)):
            a, b = find(f[0]), find(f[k])
            if a != b:
                parent[a] = b
    comp = {}
    for fi, f in enumerate(faces):
        root = find(f[0])
        comp.setdefault(root, {"v": set(), "f": []})
        comp[root]["v"].update(f)
        comp[root]["f"].append(fi)
    return list(comp.values())


def apothem(points, n, corner_phase=0.0):
    """Distance from the axis to the polygon's sides, fitted from its corners.

    The normals are HALF A STEP OFF the corners -- a regular n-gon has its corners
    at phase + 360k/n and its side normals at phase + 180/n + 360k/n, and asking
    for the largest projection along the corner directions returns the
    CIRCUMRADIUS instead. Which is how a first draft of this file reported the
    18-gon's apothem as 68.7560 when it is 67.7114: the number was not wrong about
    the geometry, it was the answer to a different question (CLAUDE.md 0.18).
    """
    vals = []
    for k in range(n):
        a = math.radians(corner_phase + 180.0 / n + 360.0 * k / n)
        vals.append(max(p[0] * math.cos(a) + p[1] * math.sin(a) for p in points))
    return sum(vals) / len(vals), max(vals) - min(vals)


def off_grid(deg, step):
    r = deg % step
    return r - step if r > step * 0.5 else r


def ring_at(pts, z, r, n):
    """The n vertices of one corner ring: at this height, at this radius."""
    sel = [p for p in pts if abs(p[2] - z) < TOL and abs(rad(p) - r) < 0.05]
    return sorted(sel, key=azim) if len(sel) == n else None


def mean_r(ring):
    return sum(rad(p) for p in ring) / len(ring)


def phase_of(ring, n):
    """How far this polygon's corners sit off the world lattice, in degrees.

    The mean of each corner's distance to the nearest multiple of 360/n. Zero means
    the corners are on the lattice; 360/2n means the ring is rotated exactly half a
    step -- and a half step is invisible to every radius, chord, area and silhouette
    measurement there is. It is only visible as an angle.
    """
    return sum(off_grid(azim(p), 360.0 / n) for p in ring) / len(ring)


def fit_apothem(ring, n):
    """(apothem, spread, phase), with the fit anchored to the ring's OWN phase.

    Deliberately phase-free. A fit pinned to the world lattice answers "the
    circumradius" when the ring is rotated half a step -- a loud answer to a
    question nobody asked (CLAUDE.md 0.18). The apothem is a radius and the phase
    is an angle; they are checked by different assertions, and each one is anchored
    where it means something.
    """
    ph = phase_of(ring, n)
    a, spread = apothem(ring, n, corner_phase=ph)
    return a, spread, ph


def face_centres(ring):
    """Where a polygon's sides face, given its corners in azimuth order.

    Taken from consecutive corners rather than from face centroids, because face
    centroids do not survive triangulation: a quad split into two triangles has
    two centroids at neither the quad's centre nor on the lattice. Corners exist
    identically in both formats.
    """
    n = len(ring)
    out = []
    for k in range(n):
        a, b = azim(ring[k]), azim(ring[(k + 1) % n])
        d = (b - a) % 360.0
        out.append((a + d * 0.5) % 360.0)
    return out


# ================================================================ one format
def check(tag, path, loader):
    LINES.append("")
    LINES.append("---- %s ----" % tag)
    if not os.path.exists(path):
        ok("%s exists" % tag, False, path)
        return
    objs = loader(path)
    if not ok("two objects", len(objs) == 2,
              "got %d: %s" % (len(objs), [o.name for o in objs])):
        return
    wall_obj = max(objs, key=lambda o: max((o.matrix_world @ v.co).z
                                           for v in o.data.vertices)
                   - min((o.matrix_world @ v.co).z for v in o.data.vertices))
    ring_obj = [o for o in objs if o is not wall_obj][0]
    LINES.append("  wall = %s   ring = %s" % (wall_obj.name, ring_obj.name))
    wpts, wfaces = welded(wall_obj)
    rpts, rfaces = welded(ring_obj)
    LINES.append("  wall %d verts / %d faces, ring %d verts / %d faces"
                 % (len(wpts), len(wfaces), len(rpts), len(rfaces)))

    # ---------------------------------------------------------- the wall
    oed = open_edges(wfaces)
    ok("wall: closed manifold", not oed, "%d open edges" % len(oed))
    wshells = shell_sets(wpts, wfaces)
    ok("wall: one shell", len(wshells) == 1, "%d shells" % len(wshells))

    zmin, zmax = min(p[2] for p in wpts), max(p[2] for p in wpts)
    ok("wall: height %.2f..%.2f" % (zmin, zmax),
       abs(zmin) < TOL and abs(zmax - Z_TOP) < TOL)

    # The joint: every wall vertex at the joint height. Four circles, split by
    # vertex COUNT before anything else is asked of them. Not cosmetic -- the two
    # 18-gon circles straddle the two 24-gon ones in radius (64.6951 < 65.2536 <
    # 68.7560 < 69.2879), and the --inner-at-face mutation swaps which of the two
    # is lower still, so "the inner two" is not a category that exists. A count is.
    joint = [p for p in wpts if abs(p[2] - Z_BAND) < TOL]
    buckets = {}
    for p in joint:
        buckets.setdefault(round(rad(p) / 0.05), []).append(p)
    by_n = {}
    for v in buckets.values():
        by_n.setdefault(len(v), []).append(sorted(v, key=azim))
    need("wall: two circles of 18 verts and two of 24",
         len(by_n.get(N18, [])) == 2 and len(by_n.get(N24, [])) == 2,
         "%s (%d verts at the joint)"
         % (sorted((len(v) for v in buckets.values())), len(joint)))
    c18_in, c18_out = sorted(by_n[N18], key=mean_r)
    c24_in, c24_out = sorted(by_n[N24], key=mean_r)
    LINES.append("  joint radii: " + "  ".join(
        "%.4f(n=%d)" % (mean_r(v), len(v))
        for v in (c18_in, c24_in, c18_out, c24_out)))

    # Which radius is where. The two that carry the join are named in J1/J2 below;
    # these two say the wall's own outer surfaces are where the design put them.
    ok("wall: collar outer radius %.4f" % R_18OUT,
       abs(mean_r(c18_out) - R_18OUT) < TOL, "%.4f" % mean_r(c18_out))
    ok("wall: wall outer radius %.4f" % R_24OUT,
       abs(mean_r(c24_out) - R_24OUT) < TOL, "%.4f" % mean_r(c24_out))

    # The face planes, fitted from their own corner rings at their own phase.
    for label, ring, n, expect in (("collar outer", c18_out, N18, A18_OUT),
                                   ("wall outer", c24_out, N24, A24_OUT)):
        a, spread, ph = fit_apothem(ring, n)
        ok("wall: %s apothem (want %.4f)" % (label, expect),
           abs(a - expect) < TOL and spread < 0.02,
           "measured %.4f, spread %.4f, phase %+.3f deg" % (a, spread, ph))

    # The outer surfaces, counted in TRIANGLES so both formats agree: 18 quads on
    # the collar and 24 on the wall = 36 + 48 triangles. The outer band is excluded
    # by requiring every vertex to sit on ONE of the two corner radii.
    def tris_at(r):
        return sum(len(f) - 2 for f in wfaces
                   if all(abs(rad(wpts[i]) - r) < 0.05 for i in f))
    ok("wall: collar outer surface = 36 triangles", tris_at(R_18OUT) == 36,
       "%d" % tris_at(R_18OUT))
    ok("wall: wall outer surface = 48 triangles", tris_at(R_24OUT) == 48,
       "%d" % tris_at(R_24OUT))

    # ---------------------------------------------------------- the reference
    #
    # The reference's shells, worked out ONCE. shell_sets() returns fresh dicts on
    # every call, so naming the plate in one call and the panels in another gives
    # two disjoint sets that each contain the plate -- which is exactly how this
    # line read "19 panels" including a 36-vertex one.
    rshells = shell_sets(rpts, rfaces)
    plate = max(rshells, key=lambda s: len(s["v"]))
    plate_top = [rpts[i] for i in plate["v"] if abs(rpts[i][2]) < TOL]
    need("ring: plate top edge has 18 corners", len(plate_top) == N18,
         "%d" % len(plate_top))
    plate_top.sort(key=azim)
    ok("ring: 19 shells (18 panels + the plate)", len(rshells) == 19,
       "%d" % len(rshells))
    panels = [s for s in rshells if s is not plate]
    ok("ring: 18 loose panels of 8 verts",
       len(panels) == 18 and all(len(s["v"]) == 8 for s in panels),
       "%d panels, vert counts %s" % (len(panels),
                                      sorted(len(s["v"]) for s in panels)))
    pa, ps, pph = fit_apothem(plate_top, N18)
    ok("ring: plate apothem (want %.4f)" % RING_A,
       abs(pa - RING_A) < TOL and ps < 0.02,
       "measured %.4f, spread %.4f" % (pa, ps))

    # ---- everything below is anchored to the RING, and that is the whole point ----
    #
    # The ring is what already exists in the place; the wall is what has to fit it.
    # Anchor a check to the wall's own lattice and it agrees with itself no matter
    # where the wall is -- and a rotation by half a step passes every
    # self-referential check there is, because it leaves the apothem, the chord,
    # the area and the silhouette radius untouched (see _tools/cw24_phase.luau).
    ring_ph = pph            # the ring's corner phase, measured
    ring_face_ph = ring_ph + 180.0 / N18
    start = azim(plate_top[0])
    LINES.append("  ring: corners at %+.4f deg off the lattice, faces at %.4f deg"
                 % (ring_ph, (start + 180.0 / N18) % 360.0))

    def on_lattice(ring, n, phase):
        return max(abs(off_grid(azim(p) - phase, 360.0 / n)) for p in ring)

    ok("wall: collar corners coincide with the ring's (0 + 20)",
       on_lattice(c18_out, N18, ring_ph) < 0.02,
       "worst %.4f deg" % on_lattice(c18_out, N18, ring_ph))
    ok("wall: wall corners land on the ring's lattice (0 + 15)",
       on_lattice(c24_out, N24, ring_ph) < 0.02,
       "worst %.4f deg" % on_lattice(c24_out, N24, ring_ph))

    # ---------------------------------------------------------- J1
    foot = ring_at(wpts, 0.0, R_18IN, N18)
    need("wall: inner foot ring found (18 verts at z=0)", foot is not None)
    gaps = [min(math.dist(p, q) for q in plate_top) for p in foot]
    ok("J1 wall's inner foot IS the ring's outline",
       max(gaps) < TOL, "worst vertex gap %.5f studs" % max(gaps))

    # ---------------------------------------------------------- J2 and J3
    a24_in, _, _ = fit_apothem(c24_in, N24)
    ok("J2 wall inner face == ring's OUTERMOST (%.4f)" % RING_R,
       abs(a24_in - RING_R) < TOL, "measured %.4f" % a24_in)
    LINES.append("  J2 standoff at the ring's face planes: %.4f studs"
                 % (a24_in - RING_A))

    # Containment. The wall's hole is bounded by 24 planes at distance a24_in, so a
    # point is in the hole iff r*cos(delta) <= a24_in for every plane, and the
    # binding one is the nearest. Every vertex of the ring must survive it; if any
    # does not, the ring is buried in the wall. Measured against the WALL's own
    # normals -- this asks "does it fit", and J4 separately asks "does it line up".
    w24_ph = phase_of(c24_in, N24) + 180.0 / N24      # the wall's face normals
    worst = max(rad(p) * math.cos(math.radians(
        abs(off_grid(azim(p) - w24_ph, 360.0 / N24)))) for p in rpts)
    ok("J3 no ring vertex inside the wall", worst <= a24_in + TOL,
       "worst r*cos = %.4f vs %.4f" % (worst, a24_in))

    # ---------------------------------------------------------- J4
    ring_centres = face_centres(plate_top)
    collar_centres = face_centres(c18_out)
    wall_centres = face_centres(c24_out)
    ok("J4 collar faces on the ring's faces (18 of them)",
       len(collar_centres) == N18 and
       max(abs(off_grid(a - ring_face_ph, 360.0 / N18))
           for a in collar_centres) < 0.02,
       "worst %.4f deg" % max(abs(off_grid(a - ring_face_ph, 360.0 / N18))
                              for a in collar_centres))
    ok("J4 wall faces on 7.5 + 15k off the ring (24 of them)",
       len(wall_centres) == N24 and
       max(abs(off_grid(a - (ring_ph + 180.0 / N24), 360.0 / N24))
           for a in wall_centres) < 0.02,
       "worst %.4f deg" % max(abs(off_grid(a - (ring_ph + 180.0 / N24),
                                           360.0 / N24)) for a in wall_centres))
    LINES.append("  J4 one 60 deg sector from %.4f deg: ring %d, collar %d"
                 " (3 by the rule), wall %d (4 by the rule)"
                 % (start,
                    sum(1 for a in ring_centres if (a - start) % 360.0 < 60.0),
                    sum(1 for a in collar_centres if (a - start) % 360.0 < 60.0),
                    sum(1 for a in wall_centres if (a - start) % 360.0 < 60.0)))

    carried = sum(1 for a in c24_in
                  if min(abs(off_grid(azim(a) - azim(p), 360.0 / N18))
                         for p in plate_top) < 0.02)
    ok("J4 6 of the ring's 18 corners carry a wall corner", carried == 6,
       "%d carried (3*20 = 4*15 = 60)" % carried)

    # ---------------------------------------------------------- the band
    band = [f for f in wfaces if all(abs(wpts[i][2] - Z_BAND) < TOL for i in f)]
    ok("band: 84 faces at the joint height", len(band) == 2 * (N18 + N24),
       "%d" % len(band))
    ok("band: all triangles", bool(band) and all(len(f) == 3 for f in band))
    spans = [max(rad(wpts[i]) for i in f) - min(rad(wpts[i]) for i in f)
             for f in band]
    ok("band: every face spans < 1.0 stud radially",
       bool(spans) and max(spans) < 1.0,
       "worst %.4f" % (max(spans) if spans else -1))
    inner = sum(1 for f in band if max(rad(wpts[i]) for i in f) < 67.0)
    ok("band: inner/outer split 42/42", inner == 42 and len(band) - inner == 42,
       "%d / %d" % (inner, len(band) - inner))
    # A face spanning a large azimuth is a face joined to the wrong partner; the
    # band's own vertices are never more than one lattice step apart.
    def wrap(f):
        a = [azim(wpts[i]) for i in f]
        return max(min(abs(x - y) % 360.0, 360.0 - abs(x - y) % 360.0)
                   for x in a for y in a)
    # Every tally below is guarded by `bool(band)` first, and that is not defensive
    # padding. An unbridged mesh has NO band faces at all, and an empty subject is
    # where a check lies twice: `all([])` is True (so "all triangles" passes
    # vacuously) and `max(())` raises (so the run dies). Both were live here.
    worst_wrap = max((wrap(f) for f in band), default=-1.0)
    ok("band: no face wraps more than 40 deg of azimuth",
       bool(band) and worst_wrap < 40.0, "worst %.2f deg" % worst_wrap)
    degen = [f for f in band if area(wpts, f) < 1e-6]
    ok("band: no degenerate faces", bool(band) and not degen, "%d" % len(degen))

    # ---------------------------------------------------------- the report
    print("SUMMARY %s wall %d verts %d faces (%d tris) | ring %d verts %d faces"
          % (tag, len(wpts), len(wfaces), sum(len(f) - 2 for f in wfaces),
             len(rpts), len(rfaces)))
    print("SUMMARY %s expected_studio_size %.2f x %.2f x %.2f (Roblox frame;"
          " Y and Z swap on import)"
          % (tag, 2 * R_24OUT, Z_TOP + PLATE_T, 2 * R_24OUT))


# ================================================================ main
#
# The try/except is load-bearing, and it is not about this file being fragile.
# MEASURED on this Blender (5.1.2, 2026-10-04): a script run with
# `--background --factory-startup --python` that RAISES exits with status 0.
# sys.exit(1) and os._exit(1) both exit 1; an ordinary exception does not.
# So an uncaught crash in a checker reports exactly what a pass reports, and the
# only reason the four mutations above looked correct is that this file happened
# to reach its own sys.exit(1). One empty sequence away from a silent green.
# Anything that escapes is converted here, loudly, into the same rc as a failure.
try:
    for tag, name, loader in (("FBX", NAME + ".fbx", load_fbx),
                              ("GLB", NAME + ".glb", load_glb)):
        check(tag, os.path.join(OUT_DIR, name), loader)
    done()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    print("\n".join(LINES))
    print("CHECK CRASHED -- treated as a failure (see the traceback above)")
    sys.exit(1)
