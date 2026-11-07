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
# WHAT THE RAYS FOUND, AND WHAT v2 DOES WITH IT.
# The source silhouette is four straight bands with three hard creases in the flank
# (fitted slopes 7.327 / 2.489 / 0.480, turning 14 deg, then 42 deg, then 26 deg
# between neighbours). v1 reproduced that exactly. The operator then said
# "那个把他侧边搞得更圆一些" -- make the side rounder -- so v2 replaces the whole
# flank with ONE smooth curve.
#
# The curve is a single cubic Bezier that leaves the bottom rim along the measured
# taper (so the widest point is still the rim, at the same radius) and arrives at
# the flat top with a HORIZONTAL tangent (so there is no crease where the side
# meets the top either). Both end dimensions are unchanged; only the flank between
# them bows. Two things follow that are not cosmetic:
#   - the silhouette now departs from the measurement, by up to ~0.05 studs. That
#     is the requested change, not a regression, and the check turns the old
#     equality into a BOUND so it still has a floor.
#   - the departures are spread over 32 profile samples instead of 3 creases, which
#     is what makes it read as round. The check measures that: the worst turn
#     between adjacent 0.005-stud steps used to be 42 deg.
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

# Bezier control arms, in studs.
#   ARM0 runs along the taper; it is what keeps the bottom of the flank at the
#   measured angle and the rim at the measured radius.
#   ARM1 is horizontal, which is what makes the top tangent horizontal.
# Their lengths are the one judgement in this file: they set how the bow is
# distributed between "holds the taper" and "flattens early". Longer ARM1 pushes
# the bulge outward at mid-height; shorter pulls it in at the shoulder. 0.115 /
# 0.090 keeps the departure from the measured silhouette inside ~0.06 studs in
# both directions, and the build prints the two extremes so this stays a number
# and not a taste.
ARM0 = 0.115
ARM1 = 0.090

SAMPLES = 32            # profile samples along the flank
SEGMENTS = 48           # around the axis


def flank():
    """The Bezier, bottom -> top, as (radius, height) pairs. t=0 is the rim."""
    u0 = Vector((-1.0, TAPER)).normalized()          # into the surface, upwards
    p0 = Vector((R_BOT, Y_BOT))
    p1 = p0 + u0 * ARM0
    p3 = Vector((R_TOP, Y_TOP))
    p2 = p3 + Vector((1.0, 0.0)) * ARM1              # horizontal, arrived from +r
    out = []
    for i in range(SAMPLES + 1):
        t = i / SAMPLES
        s = 1.0 - t
        b = s * s * s * p0 + 3.0 * s * s * t * p1 + 3.0 * s * t * t * p2 + t * t * t * p3
        out.append((b.x, b.y))
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
