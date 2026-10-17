import sys, traceback
import bpy
from mathutils import Vector

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=r"D:/BlenderRobloxTestProjects/From_RBLX/BottomChamberMAchine.gltf")
    deps = bpy.context.evaluated_depsgraph_get()
    print("%-12s %-12s %8s %8s %8s  %8s %8s %8s  polys" % ("obj","mat","zmin","zmax","thick","xmin","xmax","ymin"))
    for ob in sorted([o for o in bpy.context.scene.objects if o.type=="MESH"], key=lambda o:o.name):
        zs=[]; xs=[]; ys=[]
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
        mi = sorted({p.material_index for p in ob.data.polygons})
        mats = ",".join(ob.data.materials[i].name for i in mi if i < len(ob.data.materials))
        print("%-12s %-12s %8.3f %8.3f %8.3f  %8.3f %8.3f %8.3f  %d" % (
            ob.name, mats, min(zs), max(zs), max(zs)-min(zs), min(xs), max(xs), min(ys), len(ob.data.polygons)))
    # exact centre probe, top-down
    lo = Vector((1e18,)*3); hi = Vector((-1e18,)*3)
    for ob in bpy.context.scene.objects:
        if ob.type!="MESH": continue
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            for i in range(3):
                lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
    cx, cy = (lo.x+hi.x)/2, (lo.y+hi.y)/2
    print("centre probe at %.3f %.3f" % (cx, cy))
    for d, z0, tag in ((Vector((0,0,-1)), hi.z+5, "down"), (Vector((0,0,1)), lo.z-5, "up")):
        ok, loc, nor, idx, obj, mat = bpy.context.scene.ray_cast(deps, Vector((cx,cy,z0)), d)
        print("  %-4s hit %s mat %s at z %.4f  normal %s" % (tag, obj.name if ok else "MISS", mat, loc.z if ok else 0, tuple(round(c,3) for c in nor)))

try:
    main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc(); sys.exit(1)
