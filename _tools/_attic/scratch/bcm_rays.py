# What is actually on top? Two renders disagreed about the top surface (Cycles
# said black, Workbench said grey), and a disagreement means one instrument is
# lying (CLAUDE.md 0.27 2). Rays do not care about normals or shading models:
# they report which object a point is standing on.
#
# Prints an ASCII map of the topmost object per grid cell, from above and from
# below, plus each object's own name so the map can be read back.
import sys
import traceback

import bpy
from mathutils import Vector

NX, NY = 32, 30


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=r"D:/BlenderRobloxTestProjects/From_RBLX/BottomChamberMAchine.gltf")
    deps = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lo = Vector((1e18,) * 3)
    hi = Vector((-1e18,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])

    # Name each mesh object by the material its faces carry, since the glTF
    # node names repeat ("Part" seven times) and cannot tell them apart.
    labels = {}
    for ob in objs:
        mats = sorted({p.material_index for p in ob.data.polygons})
        names = sorted({ob.data.materials[i].name for i in mats if i < len(ob.data.materials)})
        labels[ob.name] = "%s/%s" % (ob.name, ",".join(names))
    for k in sorted(labels):
        print("  %-28s %s" % (k, labels[k]))

    def shoot(direction, z0):
        grid = []
        for j in range(NY):
            row = []
            for i in range(NX):
                x = lo.x + (hi.x - lo.x) * (i + 0.5) / NX
                y = lo.y + (hi.y - lo.y) * (j + 0.5) / NY
                origin = Vector((x, y, z0))
                ok, loc, nor, idx, obj, mat = bpy.context.scene.ray_cast(
                    deps, origin, direction)
                row.append(labels.get(obj.name, "?").split("/")[0] if ok else ".")
            grid.append(row)
        return grid

    for title, direction, z0 in (
        ("TOP (rays going down)", Vector((0, 0, -1)), hi.z + 5),
        ("BOTTOM (rays going up)", Vector((0, 0, 1)), lo.z - 5),
    ):
        print()
        print(title)
        grid = shoot(direction, z0)
        used = sorted({c for row in grid for c in row})
        sym = {c: " .:-=+*#%@"[k] for k, c in enumerate(used)}
        print("   " + "".join(sym[c] for c in used))
        for j in range(NY - 1, -1, -1):
            print("   " + "".join(sym[c] for c in grid[j]))
        counts = {}
        for row in grid:
            for c in row:
                counts[c] = counts.get(c, 0) + 1
        for c in used:
            print("   %s %-6d %s" % (sym[c], counts[c], c))


try:
    main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    sys.exit(1)
