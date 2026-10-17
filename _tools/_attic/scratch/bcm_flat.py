# A flat, evenly-lit orthographic top view. The Cycles render said "a tray";
# the node table says two large grey wedges sit on top of the black slab. Those
# two readings disagree, and a disagreement means one of them is the wrong
# instrument (CLAUDE.md 0.27 2). Workbench with MATERIAL colour, ortho, no
# shadows: it draws the materials in their own colours and nothing else.
import sys
import traceback

import bpy
from mathutils import Vector


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=r"D:/BlenderRobloxTestProjects/From_RBLX/BottomChamberMAchine.gltf")
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lo = Vector((1e18,) * 3)
    hi = Vector((-1e18,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    centre = (lo + hi) * 0.5
    span = max((hi - lo).x, (hi - lo).y)

    # Workbench's MATERIAL mode reads diffuse_color, and the glTF importer
    # leaves that at 0.8 grey while it writes the real colour into the node
    # tree. Copy it across, or every material is the same picture.
    # The importer leaves Base Color at 0.8 and hangs the real factor off a
    # multiply node, so read the factors out of the file itself instead.
    import json
    src = json.load(open(r"D:/BlenderRobloxTestProjects/From_RBLX/BottomChamberMAchine.gltf", encoding="utf-8"))
    for i, srcmat in enumerate(src["materials"]):
        f = srcmat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.8, 0.8, 0.8, 1.0])
        m = bpy.data.materials.get("Material_%d" % i)
        if m is None:
            continue
        m.diffuse_color = (f[0], f[1], f[2], f[3])
        print("mat %-12s rgb %.3f %.3f %.3f alpha %.3f tex %s" % (
            m.name, f[0], f[1], f[2], f[3],
            "yes" if "baseColorTexture" in srcmat.get("pbrMetallicRoughness", {}) else "no"))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "FLAT"
    sh.color_type = "TEXTURE"   # draw the decal too: MATERIAL hides it behind a flat colour
    sh.show_shadows = False
    sh.show_cavity = True
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800

    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = span * 1.15
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    for name, d, ortho, light in (
        ("flat_top", (0, 0, 1), True, "FLAT"),
        ("flat_bottom", (0, 0, -1), True, "FLAT"),
        ("tex_iso", (0.75, -0.9, 0.6), False, "STUDIO"),
    ):
        d = Vector(d).normalized()
        sh.light = light
        if ortho:
            cam_data.type = "ORTHO"
            cam_data.ortho_scale = span * 1.15
            cam.location = centre + d * span * 3
        else:
            cam_data.type = "PERSP"
            cam_data.lens = 60
            cam.location = centre + d * span * 1.9
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = "D:/rblxTRGproject/_tools/_attic/scratch/bcm_%s.png" % name
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)

    # Name the materials so the colours in the picture can be read back.
    for i, m in enumerate(bpy.data.materials):
        c = m.diffuse_color
        print("mat %d %-10s rgb %.3f %.3f %.3f" % (i, m.name, c[0], c[1], c[2]))


try:
    main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    sys.exit(1)
