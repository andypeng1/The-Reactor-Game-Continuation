# probe_bevel_faces.py -- what does bmesh.ops.bevel hand back?
#
# The material-repair question is: can the new faces be identified EXACTLY,
# instead of guessed by position? A position guess already failed once on
# CblLaserMk4 (a 21.6 x 23 plate's corner strip is 8 units from its own face
# centroid, so "nearest centroid" picked a different material's face).
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/_attic/scratch/probe_bevel_faces.py

import bmesh
import bpy

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
print("PROBE faces before      =", len(bm.faces))
print("PROBE edges before      =", len(bm.edges))

res = bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.1, offset_type="OFFSET",
                      segments=1, profile=0.5, affect="EDGES",
                      clamp_overlap=True)
print("PROBE returned keys     =", sorted(res.keys()))
print("PROBE len(res['faces']) =", len(res["faces"]))
print("PROBE faces after       =", len(bm.faces))
print("PROBE every face is in  =",
      all(f in set(bm.faces) for f in res.get("faces", [])))

# And does the operator's own `material` argument do anything? Documented as
# "material for bevel faces (-1 means use adjacent faces)".
bm2 = bmesh.new()
bmesh.ops.create_cube(bm2, size=2.0)
for f in bm2.faces:
    f.material_index = 3
res2 = bmesh.ops.bevel(bm2, geom=bm2.edges[:], offset=0.1, offset_type="OFFSET",
                       segments=1, profile=0.5, affect="EDGES",
                       clamp_overlap=True, material=-1)
print("PROBE default-index after bevel, material=-1:",
      sorted({f.material_index for f in bm2.faces}))

bm3 = bmesh.new()
bmesh.ops.create_cube(bm3, size=2.0)
for f in bm3.faces:
    f.material_index = 3
res3 = bmesh.ops.bevel(bm3, geom=bm3.edges[:], offset=0.1, offset_type="OFFSET",
                       segments=1, profile=0.5, affect="EDGES",
                       clamp_overlap=True)
print("PROBE same but material omitted (its default):",
      sorted({f.material_index for f in bm3.faces}))

bm4 = bmesh.new()
bmesh.ops.create_cube(bm4, size=2.0)
for f in bm4.faces:
    f.material_index = 3
res4 = bmesh.ops.bevel(bm4, geom=bm4.edges[:], offset=0.1, offset_type="OFFSET",
                       segments=1, profile=0.5, affect="EDGES",
                       clamp_overlap=True, material=3)
print("PROBE same but material=3:",
      sorted({f.material_index for f in bm4.faces}))
