# preview_gltf.py -- render any glTF/GLB so the shape can be SEEN before it is measured.
#
# Why this exists: a structural dump of a .gltf gives counts and numbers, and a
# number that is wrong is quiet (CLAUDE.md 0.18). A picture that is wrong is loud
# (0.14b). The one thing this prints that a count cannot is whether the model is
# the shape anyone expected -- e.g. a "machine" that is 0.6 studs tall is a slab,
# and that reads as a machine in a node list and as a plate in a render.
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/blender/preview_gltf.py -- <in.gltf> <outdir> [tag]
#
# Deliberately uses --factory-startup and never touches a running Blender: the
# operator's own scene is theirs (the MCP addon drives the live one).
#
# Two things the last round got wrong and this keeps:
#   1. an uncaught exception in --background exits rc = 0, which looks exactly
#      like success (CLAUDE.md 0.6), so the body is wrapped and SystemExit is let
#      through;
#   2. Blender splits argv at a bare `--`; anything after it is ours. Written as
#      `--python s.py --flag` the flag is taken for a file to open (same entry).

import os
import sys
import traceback

import bpy
from mathutils import Vector


def bounds(objs):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for ob in objs:
        if ob.type != "MESH":
            continue
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def main(argv):
    if len(argv) < 2:
        print("usage: -- <in.gltf> <outdir> [tag]")
        return 2
    src, outdir = argv[0], argv[1]
    tag = argv[2] if len(argv) > 2 else "preview"

    # MEASURED 2026-10-17: under --background --factory-startup a RELATIVE output
    # path does not resolve against the process cwd, even though os.getcwd()
    # reports it -- it resolves against the drive root, so "renders/em_top.png"
    # was written to C:\renders\em_top.png (Blender created the directories) and
    # the "wrote" line below printed the relative path it was given. Three shots
    # were reported written and none of them were where I looked. Absolute
    # either way, at the one place that decides where bytes go.
    src = os.path.abspath(src)
    outdir = os.path.abspath(outdir)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    objs = list(bpy.context.scene.objects)
    meshes = [o for o in objs if o.type == "MESH"]

    lo, hi = bounds(objs)
    size = hi - lo
    centre = (lo + hi) * 0.5
    print("objects %d  meshes %d" % (len(objs), len(meshes)))
    print("bbox min %.4f %.4f %.4f" % (lo.x, lo.y, lo.z))
    print("bbox max %.4f %.4f %.4f" % (hi.x, hi.y, hi.z))
    print("bbox size %.4f %.4f %.4f" % (size.x, size.y, size.z))
    tris = 0
    for o in meshes:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    print("triangles %d" % tris)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.film_transparent = False

    # A neutral grey world: the parts are grey, so a coloured world is what
    # separates silhouette from background without pretending to be lighting.
    world = bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.06, 0.08, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    span = max(size.x, size.y, size.z)
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", type="SUN"))
    sun.data.energy = 4.0
    sun.rotation_euler = (0.9, 0.2, 0.6)
    scene.collection.objects.link(sun)

    def shoot(name, direction, up=(0, 0, 1)):
        d = Vector(direction).normalized()
        dist = span * 2.2
        cam.location = centre + d * dist
        # look at the centre: -Z of the camera points along +d
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(outdir, "%s_%s.png" % (tag, name))
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)

    shoot("top", (0.0, 0.0, 1.0))
    shoot("iso", (0.8, -0.9, 0.55))
    shoot("edge", (1.0, 0.0, 0.12))
    return 0


try:
    _argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    _rc = main(_argv)
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    _rc = 1
sys.exit(_rc)
