# chamber_grate.py -- headless Blender generator for the reactor chamber's outer
# grate shell.
#
# WHY THIS FILE EXISTS
#   In Studio the chamber shell came out as 72 ribs x 12 stacked segments of thin
#   plates -- 2002 separate Parts, because a part-based modeler has no way to make
#   a curved surface with thickness other than stacking boxes. This script builds
#   the same shape as ONE mesh, with real thickness and a real bevel, and hands it
#   back as .glb/.fbx. The number worth reading at the end is the instance count
#   (2002 -> 1) and the triangle count, not how it looks -- I cannot see the
#   render, the operator can.
#
# MEASURED vs CHOSEN
#   measured (counted off the original ChamberWalls in the Rebuild place):
#     RADIUS 100   the shell is a grate at r ~= 100, it is NOT a solid tube
#     TOP_Z  347   shell top; the inner tube runs ~156 higher, that is a separate part
#     N_RIBS 72, N_SEGMENTS 12
#   chosen (mine, not measured -- change freely, they are all at the top):
#     rib cross-section, SEG_GAP, BAND_H, ring thickness, BEVEL, BOTTOM_Z
#     N_BANDS: one per segment boundary. The original's band count I did not
#     count this session, so 13 is a guess wearing structure's clothes.
#
# UNVERIFIED (do not let anyone assume 1.0)
#   The Blender-unit -> stud factor through glTF/FBX. Roblox may import 1:1 or
#   through a scale. Import once, read the MeshPart Size in Studio, and that
#   gives the factor. Nothing here measures it.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python "D:\rblxTRGproject\_tools\blender_chamber_grate.py"

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- parameters
RADIUS = 100.0        # rib centreline radius
BOTTOM_Z = 0.0        # set to 0 on purpose: vertical placement is a Studio-side
TOP_Z = 347.0         # concern, and the base was not re-measured this session
N_RIBS = 72
N_SEGMENTS = 12
N_BANDS = N_SEGMENTS + 1   # one per segment boundary; chosen, see header

RIB_W = 3.2           # tangential width of a rib
RIB_D = 1.6           # radial thickness of a rib
SEG_GAP = 1.0         # gap between two stacked rib segments
BAND_H = 2.4          # band height, measured along Z
BAND_T = 1.8          # band radial thickness
BEVEL = 0.12          # edge bevel -- this is the thing a part-based build cannot do

OUT_DIR = r"D:\BlenderRobloxTestProjects"
NAME = "ChamberGrate"


# ---------------------------------------------------------------- helpers
def add_box(bm, centre, size, rot_z=0.0):
    """A box as 6 quads, placed by a single matrix so there is no ambiguity about
    the order of scale/rotate/translate (the mistake that produced a 15.6-stud
    error on the Studio side -- see CLAUDE.md 0.18)."""
    mat = (Matrix.Translation(centre)
           @ Matrix.Rotation(rot_z, 4, "Z")
           @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def add_ring(bm, radius, z_centre, height, thickness, n):
    """A closed annulus band: four loops of n verts -> 4n quads, closed around Z.
    Built by hand rather than as n boxes, because a band that is n boxes is a
    grate pretending to be a band."""
    ri, ro = radius - thickness / 2.0, radius + thickness / 2.0
    z0, z1 = z_centre - height / 2.0, z_centre + height / 2.0
    loops = []
    for r, z in ((ri, z0), (ro, z0), (ro, z1), (ri, z1)):
        loops.append([
            bm.verts.new((r * math.cos(2 * math.pi * i / n),
                          r * math.sin(2 * math.pi * i / n), z))
            for i in range(n)
        ])
    for a in range(4):
        loop_a, loop_b = loops[a], loops[(a + 1) % 4]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((loop_a[i], loop_a[j], loop_b[j], loop_b[i]))


# ---------------------------------------------------------------- build
bpy.ops.wm.read_factory_settings(use_empty=True)

span = TOP_Z - BOTTOM_Z
seg_h = (span - (N_SEGMENTS - 1) * SEG_GAP) / N_SEGMENTS
step = 2 * math.pi / N_RIBS

bm = bmesh.new()

for i in range(N_RIBS):
    ang = i * step
    cx, cy = RADIUS * math.cos(ang), RADIUS * math.sin(ang)
    for j in range(N_SEGMENTS):
        z0 = BOTTOM_Z + j * (seg_h + SEG_GAP)
        add_box(bm, (cx, cy, z0 + seg_h / 2.0), (RIB_D, RIB_W, seg_h), rot_z=ang)

# One band per segment boundary (13 for 12 segments), with the two end bands
# pulled inward by half a band height so the shell's span is exactly
# [BOTTOM_Z, TOP_Z] -- otherwise the end bands overhang the ribs and the bbox
# reads 349.4 instead of 347, which is a 2.4-stud lie about the height.
band_z = [BOTTOM_Z + j * (seg_h + SEG_GAP) for j in range(N_SEGMENTS)] + [TOP_Z]
band_z[0] += BAND_H / 2.0
band_z[-1] -= BAND_H / 2.0
for z in band_z:
    add_ring(bm, RADIUS, z, BAND_H, BAND_T, N_RIBS)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                offset=BEVEL, offset_type="OFFSET", segments=1, profile=0.5,
                affect="EDGES", clamp_overlap=True)

mesh = bpy.data.meshes.new(NAME)
bm.to_mesh(mesh)
bm.free()
obj = bpy.data.objects.new(NAME, mesh)
bpy.context.scene.collection.objects.link(obj)

# ---------------------------------------------------------------- measure
# Read the result back out instead of trusting the loop above. Same discipline as
# reading instance properties on the Studio side: the build code is not evidence.
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
xs = [v.x for v in corners]
ys = [v.y for v in corners]
zs = [v.z for v in corners]
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
# bpy.types.Mesh edges carry no link_faces (that is a bmesh thing) -- count how
# many faces each edge key appears in. 2 everywhere == closed solids.
edge_use = {}
for poly in mesh.polygons:
    for key in poly.edge_keys:
        edge_use[key] = edge_use.get(key, 0) + 1
open_edges = sum(1 for count in edge_use.values() if count != 2)
print("SUMMARY model=%s ribs=%d segments=%d bands=%d" % (NAME, N_RIBS, N_SEGMENTS, N_BANDS))
print("SUMMARY bbox_x=%.2f bbox_y=%.2f bbox_z=%.2f z_lo=%.2f z_hi=%.2f"
      % (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), min(zs), max(zs)))
print("SUMMARY verts=%d polys=%d tris=%d open_edges=%d"
      % (len(mesh.vertices), len(mesh.polygons), tris, open_edges))

# ---------------------------------------------------------------- export
os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, NAME + ".glb"),
                          export_format="GLB", use_selection=False)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT_DIR, NAME + ".fbx"),
                         use_selection=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, NAME + ".blend"))


# ---------------------------------------------------------------- renders
# For the operator, not for me: Workbench needs no lights and no GPU, and it is
# the only way anyone can judge the silhouette before it reaches Studio.
def render(path, loc):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 300.0
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector((0, 0, 170)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene = bpy.context.scene
    scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 800
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


render(os.path.join(OUT_DIR, NAME + "_side.png"), (0.0, -420.0, 173.0))
render(os.path.join(OUT_DIR, NAME + "_iso.png"), (300.0, -300.0, 300.0))
print("SUMMARY wrote %s" % OUT_DIR)
