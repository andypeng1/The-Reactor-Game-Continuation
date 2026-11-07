# alarm_cone.py -- rebuild Workspace.OtherStuff.ReactorALARM["Meshes/Cone (2)"]
# as a mesh we own.
#
# WHY. Operator, 2026-11-07: "这个现在是别人的，我希望你把这个mesh在blender里面做出来".
# The part carries MeshId rbxassetid://5192208808 -- a marketplace mesh. The repo is
# public and the place ships it, so an asset that belongs to somebody else is a
# problem that does not go away by itself. This file is the replacement.
#
# THE SHAPE IS MEASURED, NOT INVENTED.
# `AssetService:CreateEditableMeshAsync` refuses the asset in Studio's assistant
# sandbox ("no permission to load asset"), so the geometry was read the other way:
# raycasts against the part itself, in the Edit data model. CollisionFidelity is
# Hull, so what the rays return is the convex hull; for a convex lamp lens that IS
# the outer surface, and the outer surface is the only one that shows.
#
#   down-rays, 0.005-stud radial grid  -> the silhouette
#   horizontal rays at 23 heights      -> confirms a body of revolution
#                                         (max X at a given height == max Z to 4 dp)
#   azimuthal sweep, 48 rays at y=0    -> round to 0.4%; the 16-fold ripple is
#                                         0.0036 studs on a 0.9-stud part, i.e. gone
#
# WHAT THE RAYS FOUND, AND WHAT v3 DOES WITH IT.
# The source silhouette is four straight bands with three hard creases in the flank
# (fitted slopes 7.327 / 2.489 / 0.480, turning 14 deg, then 42 deg, then 26 deg
# between neighbours). The operator's read of it, verbatim:
#   "原来那个侧边是一条直线到上面才开始收敛" -- the side runs STRAIGHT and only
#   closes in near the top.
# That is correct and it is the constraint: the 82.2 deg taper is nearly vertical,
# so the wall really is a straight, barely-tapering line, and everything that
# happens happens in the last 10% of the height.
#
# So the straight wall stays straight. Only the shoulder changes: where the source
# put THREE STRAIGHT BANDS (two creases), this puts ONE CIRCULAR ARC tangent to
# both the taper and the flat top. A circle is the roundest a shoulder can be, and
# constant curvature is exactly what "no crease" means -- a Bezier or a spline
# would still bunch curvature at its ends.
#
# v2 (an earlier pass this same day, in git) bowed the WHOLE flank instead. That
# was the wrong read of "把他侧边搞得更圆一些": it turned the straight side into a
# curve, which is not the part he was pointing at.
#
# The arc is also the only radius that can touch both tangents, so there is no
# free parameter left to tune: R comes out at 0.0611 studs. Its tangent point sits
# at (0.3446, 0.3597), i.e. the top 6% of the height for the straight run to end --
# "到上面才开始收敛", kept literally.
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/blender/alarm_cone.py
#
# Output: D:\BlenderRobloxTestProjects\AlarmCone\
#         ReactorAlarmCone.fbx  <- the operator imports THIS, dialog scale 5.902
#         ReactorAlarmCone.glb  <- 1.6943x on import; kept for reference only
#         ReactorAlarmCone.blend
#         three Workbench previews

import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

OUT = r"D:\BlenderRobloxTestProjects\AlarmCone"
NAME = "ReactorAlarmCone"

# ---------------------------------------------------------------- fixed points
# (radius, height) in studs in the PART's own frame. Identity rotation in Studio,
# so local Y is up; Blender is Z-up, so the profile runs along Z and the two axes
# line up after the FBX round trip.
Y_BOT, Y_TOP = -0.4125, 0.4125
R_BOT = 0.4500
R_TOP = 0.2841          # where the flat top ends and the flank begins

# The source flank's slope where it leaves the rim, from the ray table: 7.326
# studs of rise per stud of radius. 82.2 deg from horizontal.
TAPER = 7.326

ARC_SAMPLES = 24        # profile samples along the shoulder arc
SEGMENTS = 48           # around the axis


def flank():
    """Straight taper from the rim to the tangent point, then one circular arc.

    The taper is the line y = -TAPER*r + c, where c is fixed by the rim. The arc
    is the circle of radius R whose centre sits directly under the top tangent
    point (R_TOP, Y_TOP - R) -- that placement is what makes the arc meet the flat
    top horizontally. Requiring the same circle to be tangent to the taper gives
    one equation in R and one solution:

        (R + k) / sqrt(TAPER^2 + 1) = R,   k = c - TAPER*R_TOP - Y_TOP
        R = k / (sqrt(TAPER^2 + 1) - 1)                       = 0.0611 studs

    Nothing here is chosen. R is determined, the tangent point is the foot of the
    perpendicular from the centre, and the arc runs the last 82.2 deg up to the
    top -- the same angle the taper leaves the rim at, which is why this is the
    largest roundover the two tangents allow.
    """
    c = Y_BOT + TAPER * R_BOT                       # the taper line's intercept
    nrm = math.hypot(TAPER, 1.0)
    k = c - TAPER * R_TOP - Y_TOP
    rad = k / (nrm - 1.0)
    cx, cy = R_TOP, Y_TOP - rad

    # Foot of the perpendicular from the centre onto the taper line.
    d = k + rad
    tx = cx + d * TAPER / (TAPER * TAPER + 1.0)
    ty = cy + d / (TAPER * TAPER + 1.0)

    a0 = math.atan2(ty - cy, tx - cx)
    out = [(R_BOT, Y_BOT), (tx, ty)]
    for i in range(1, ARC_SAMPLES):
        a = a0 + (0.5 * math.pi - a0) * i / ARC_SAMPLES
        out.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    out.append((R_TOP, Y_TOP))   # exact, rather than cos(90 deg)'s 6e-17
    return out


PROFILE = [(0.0000, Y_BOT)] + flank() + [(0.0000, Y_TOP)]


def lens_material():
    """One material, so the mesh lands in Studio as ONE MeshPart.

    Looked up by node TYPE, not by name: on a non-English Blender UI the node is
    not called "Principled BSDF" and the by-name lookup returns None (that is the
    Blender MCP's own standing instruction, and trg.material predates it).

    The colour is a placeholder. Roblox drives the look from the PART -- Material
    Glass, Color (1, 0.690196, 0), Transparency 0.75 -- and a part can only carry
    one material set, so nothing here reaches the player.
    """
    mat = bpy.data.materials.new("Lens")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (1.0, 0.690196, 0.0, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.08
    mat.diffuse_color = (1.0, 0.690196, 0.0, 1.0)  # Workbench previews read this
    return mat


def shade_smooth_by_angle(obj, deg):
    """Smooth the wall, keep the bottom rim sharp.

    A 48-segment lathe is a 48-gon: geometrically round to 0.001 studs, but with
    flat shading every facet is its own plane and the eye reads 48 stripes. That
    is what the first preview looked like, and it is exported -- FBX carries the
    normals, so Roblox shows the same stripes.

    The threshold is a dihedral angle, not a "smooth everything" switch: adjacent
    wall facets are 7.5 deg apart and get merged; the bottom rim is ~98 deg and
    stays a crease. The top edge is 0 deg apart by construction (the profile meets
    the flat top with a horizontal tangent), so it disappears by itself, which is
    the point of the Bezier.

    Blender 4.1 replaced auto-smooth with this operator; the plain shade_smooth is
    the fallback for an older build, and it says so rather than pretending the rim
    is still sharp.
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))
    except (AttributeError, TypeError):
        bpy.ops.object.shade_smooth()
        print("NOTE: shade_smooth_by_angle unavailable; the bottom rim is smooth "
              "too -- re-check before shipping")


def build():
    trg.new_scene()
    bm = bmesh.new()
    trg.revolve(bm, PROFILE, n=SEGMENTS, axis="Z")
    # bevel=0: the profile is already a curve, and a bevel would move the rim that
    # has to stay at exactly 0.4500 -- that radius is what makes this a drop-in
    # replacement. trg.finish still recalculates normals.
    obj = trg.finish(bm, NAME, [lens_material()], bevel=0.0)
    shade_smooth_by_angle(obj, 40.0)

    st = trg.measure(obj)
    print("BUILD verts=%d polys=%d tris=%d open_edges=%d"
          % (st["verts"], st["polys"], st["tris"], st["open_edges"]))
    # Blender XYZ -> Studio XYZ is a swap of the last two: the mesh is built about
    # Z, and Roblox is Y-up.
    print("expected_studio_size %.6f %.6f %.6f"
          % (st["size"][0], st["size"][2], st["size"][1]))
    print("expected_studio_centre_offset %.6f %.6f %.6f"
          % (0.0, (st["z"][0] + st["z"][1]) / 2.0, 0.0))

    trg.export([obj], NAME, OUT)
    print("wrote %s" % os.path.abspath(os.path.join(OUT, NAME + ".fbx")))
    print("wrote %s" % os.path.abspath(os.path.join(OUT, NAME + ".glb")))
    print("wrote %s" % os.path.abspath(os.path.join(OUT, NAME + ".blend")))

    trg.render(NAME, OUT,
               [("front", (2.2, -2.2, 1.4)),
                ("side", (2.6, 0.0, 0.35)),
                ("top", (0.001, 0.0, 2.6))],
               target=(0.0, 0.0, 0.0), ortho=1.30)
    print("operator: drag the .fbx into Studio and type 5.902 in the import "
          "dialog. The .glb route lands 1.6943x too big.")
    return 0


if __name__ == "__main__":
    # The Blender lesson (CLAUDE.md 0.6): an uncaught exception exits 0, so a
    # crashed build and a clean build look identical to the shell.
    try:
        rc = build()
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        print("CRASHED -- this is a failure, not a pass")
        rc = 1
    sys.exit(rc)
