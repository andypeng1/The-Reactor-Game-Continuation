import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"D:/BlenderRobloxTestProjects/From_RBLX/BottomChamberMAchine.gltf")
for o in sorted(bpy.context.scene.objects, key=lambda o: o.name):
    if o.type != "MESH":
        print("%-12s type %-8s" % (o.name, o.type)); continue
    print("%-12s scale %.4f %.4f %.4f  dims %.4f %.4f %.4f  rot %s" % (
        o.name, o.scale.x, o.scale.y, o.scale.z,
        o.dimensions.x, o.dimensions.y, o.dimensions.z,
        tuple(round(c,3) for c in o.rotation_euler)))
