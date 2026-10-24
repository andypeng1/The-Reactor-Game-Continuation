# Why does the welded edge count disagree with the index count on the Body?
# The Body is the only part that fails it; Mount / Prongs / Core agree at 0.
import collections
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"D:\rblxTRGproject\_tools\blender")
import trg  # noqa: E402

trg.new_scene()
bpy.ops.import_scene.fbx(
    filepath=r"D:\BlenderRobloxTestProjects\CblLaserMk4\CblLaserMk4.fbx",
    global_scale=1.0)
obj = [o for o in bpy.context.scene.objects if o.name == "CblLaserMk4Body"][0]
mesh = obj.data
print("verts", len(mesh.vertices), "polys", len(mesh.polygons))

tol = 1e-4
key, ident = {}, []
for v in mesh.vertices:
    w = obj.matrix_world @ v.co
    k = (round(w.x / tol), round(w.y / tol), round(w.z / tol))
    ident.append(key.setdefault(k, len(key)))
print("distinct welded positions", len(key), "from", len(mesh.vertices), "verts")

use = collections.Counter()
where = {}
for poly in mesh.polygons:
    ids = [ident[i] for i in poly.vertices]
    for i in range(len(ids)):
        a, b = ids[i], ids[(i + 1) % len(ids)]
        if a == b:
            continue
        e = (a, b) if a < b else (b, a)
        use[e] += 1
        where.setdefault(e, []).append(poly.index)

hist = collections.Counter(use.values())
print("edge use histogram (count -> how many edges):", dict(sorted(hist.items())))

bad = [(e, c) for e, c in use.items() if c != 2]
print("non-2 edges:", len(bad))
for e, c in bad[:8]:
    print("  used %d times: welded verts %s  polys %s" % (c, e, where[e][:6]))

# How many WELD COLLISIONS are there -- distinct original vertices sharing one
# position? If that number is 0 the weld is a no-op and the count means what it
# says; if it is large, the weld is joining shells the index count kept apart.
dup = collections.Counter(ident)
print("positions shared by >1 original vertex:", sum(1 for c in dup.values() if c > 1))
print("max originals at one position:", max(dup.values()))

# And the index-based count, for comparison.
ek = collections.Counter()
for poly in mesh.polygons:
    for k in poly.edge_keys:
        ek[k] += 1
print("index edges:", len(ek), " non-2:", sum(1 for c in ek.values() if c != 2))

# Are the offending edges' endpoints also touched by faces at slightly different
# positions? Print the world position of one bad pair for eyeballing.
inv = {v: k for k, v in key.items()}
for e, c in bad[:6]:
    print("  BAD use=%d" % c, [tuple(round(x * 5.902, 3)
                                     for x in (Vector(inv[vid]) * tol))
                               for vid in e])
    print("      polys", where[e], "materials",
          [mesh.polygons[p].material_index for p in where[e]],
          "sizes", [len(mesh.polygons[p].vertices) for p in where[e]])
    for p in where[e]:
        poly = mesh.polygons[p]
        print("        poly %d verts %s pos %s" % (
            p, list(poly.vertices),
            [tuple(round(x * 5.902, 3) for x in (obj.matrix_world
                                                 @ mesh.vertices[i].co))
             for i in poly.vertices]))
