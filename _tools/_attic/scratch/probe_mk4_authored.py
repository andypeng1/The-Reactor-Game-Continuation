# Does the Body leave the BUILD with coincident vertices, or does the round trip
# create them? Same question the welded edge count is silently asking.
import collections
import importlib.util
import sys

import bpy

spec = importlib.util.spec_from_file_location(
    "mk4", r"D:\rblxTRGproject\_tools\blender\cbl_laser_mk4.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except SystemExit:
    # cbl_laser_mk4.py ends with sys.exit(0) under --norender; the scene it built
    # is still there afterwards, which is all this probe wants.
    pass

for obj in mod.OBJS:
    mesh = obj.data
    pos = collections.Counter((round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))
                              for v in mesh.vertices)
    dup = sum(1 for c in pos.values() if c > 1)
    print("AUTHORED %-20s verts=%6d polys=%6d distinct_pos=%6d shared_pos=%5d max=%d"
          % (obj.name, len(mesh.vertices), len(mesh.polygons), len(pos), dup,
             max(pos.values())))

# And where are they? Print the faces of the two shells that share the first
# duplicated position on the Body, so the coincidence can be named.
body = [o for o in mod.OBJS if o.name == "CblLaserMk4Body"][0]
mesh = body.data
pos = collections.Counter((round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))
                          for v in mesh.vertices)
first = next(k for k, c in pos.items() if c > 1)
print("first shared position:", first)
owners = collections.Counter()
for poly in mesh.polygons:
    for vi in poly.vertices:
        v = mesh.vertices[vi].co
        if (round(v.x, 6), round(v.y, 6), round(v.z, 6)) == first:
            owners[poly.material_index] += 1
print("materials using that position:", dict(owners))

# Zero-area faces are the shape a clamped bevel leaves behind. Count them, and
# say where -- a number without a location cannot be acted on.
tiny = []
for poly in mesh.polygons:
    if poly.area < 1e-9:
        c = poly.center
        tiny.append((poly.material_index, poly.index, poly.area,
                     (round(c.x, 3), round(c.y, 3), round(c.z, 3))))
print("zero-area faces: %d of %d" % (len(tiny), len(mesh.polygons)))
for row in tiny[:6]:
    print("   mat=%d poly=%d area=%.3e centre=%s" % row)
mt = collections.Counter(r[0] for r in tiny)
print("zero-area faces by material:", dict(sorted(mt.items())))
