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
#   down-rays, 0.005-stud radial grid  -> the silhouette below
#   horizontal rays at 23 heights      -> confirms a body of revolution
#                                         (max X at a given height == max Z to 4 dp)
#   azimuthal sweep, 48 rays at y=0    -> round to 0.4% (0.3937 at a vertex,
#                                         0.3920 between); the 16-fold ripple is
#                                         0.0036 studs on a 0.9-stud part, i.e. gone
#
# The silhouette is FOUR STRAIGHT BANDS, not a curve. That is what a low-poly lathe
# looks like when you measure it, and it is reproduced here as measured -- no bevel,
# no smoothing. A "nicer" curve would be a different shape.
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

import os
import sys
import traceback

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

OUT = r"D:\BlenderRobloxTestProjects\AlarmCone"
NAME = "ReactorAlarmCone"

# ---------------------------------------------------------------- measurements
# (radius, height) in studs in the PART's own frame. Identity rotation in Studio,
# so local Y is up; Blender is Z-up, so the profile runs along Z and the two axes
# line up after the FBX round trip.
#
# Values typed from the 2026-11-07 raycast sweep -- never read back out of an
# export (DECISIONS 95: comparing a file to itself is a tautology).
Y_BOT, Y_TOP = -0.4125, 0.4125
R_BOT = 0.4500

# Band joints, each the intersection of two neighbouring straight runs fitted to
# the ray table. The fitted slopes were 7.327 / 2.489 / 0.480 studs of rise per
# stud of radius, which is why the part reads as a bell rather than a cone.
P1 = (0.3475, 0.3385)   # the long taper meets the shoulder
P2 = (0.3258, 0.3925)   # the shoulder meets the top chamfer
P3 = (0.2841, 0.4125)   # the chamfer meets the flat top

SEGMENTS = 48

PROFILE = [
    (0.0000, Y_BOT),    # bottom centre
    (R_BOT, Y_BOT),     # bottom rim -- the widest point of the part
    P1,
    P2,
    P3,
    (0.0000, Y_TOP),    # top centre
]


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


def build():
    trg.new_scene()
    bm = bmesh.new()
    trg.revolve(bm, PROFILE, n=SEGMENTS, axis="Z")
    # bevel=0 on purpose: the profile above IS the measured silhouette, and a
    # bevel would move it. trg.finish still recalculates normals.
    obj = trg.finish(bm, NAME, [lens_material()], bevel=0.0)

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
