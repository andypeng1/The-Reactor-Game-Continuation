# trg.py -- shared helpers for the headless Blender pipeline.
#
# Two things live here that every asset script needs and neither should reinvent:
#
#   1. The stud scale. MEASURED, not assumed: the ChamberGrate mesh came out of
#      Blender at 201.79 x 201.79 x 347.00 and Studio reported the MeshPart as
#      1190.965 x 2048 x 1190.966. All three axes give the same ratio,
#      1190.965/201.79 = 2048/347.00 = 5.902, so it is a pure scale with no axis
#      swap. (The 2048 is Roblox's per-part ceiling and the height landed on it by
#      luck -- 347 * 5.902 = 2047.99 -- which is why this matters: the next asset
#      would have been clamped.) We export at 1/5.902 so the import lands 1:1.
#      CAVEAT: 5.902 may be the operator's import-dialog setting rather than a
#      property of the file. If a later import disagrees, this constant is wrong.
#
#   2. revolve() and sweep_arc(). A parts-based modeler stacks boxes because it
#      has nothing else; these two are the shapes it cannot reach -- an arbitrary
#      lathed profile (domed vessel heads, skirts, flanges) and a bent tube. If
#      the point of using Blender is real surfaces, these are where that shows.

import contextlib
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

STUDS_PER_UNIT = 5.902  # see header; 1190.965 / 201.79, 2026-10-04


# ---------------------------------------------------------------- scene
def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------- primitives
def revolve(bm, profile, n=48, centre=(0.0, 0.0), cap_bottom=True, cap_top=True):
    """Lathe a (r, z) profile about Z. profile runs bottom -> top.

    A point with r == 0 becomes a single pole vertex rather than a ring of
    coincident ones; that is what makes a domed head read as a dome instead of a
    very short cylinder with a pinched cap.
    """
    cx, cy = centre
    rings = []
    for r, z in profile:
        if r <= 1e-9:
            rings.append([bm.verts.new((cx, cy, z))])
        else:
            rings.append([
                bm.verts.new((cx + r * math.cos(2 * math.pi * i / n),
                              cy + r * math.sin(2 * math.pi * i / n), z))
                for i in range(n)
            ])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(n):
                bm.faces.new((a[0], b[i], b[(i + 1) % n]))
        elif len(b) == 1:
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[0]))
        else:
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_bottom and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return rings


def cylinder(bm, r, z0, z1, n=32, centre=(0.0, 0.0)):
    return revolve(bm, [(r, z0), (r, z1)], n=n, centre=centre)


def sweep_arc(bm, centre, major_r, minor_r, a0, a1, n_path=28, n_tube=18):
    """A bent tube: a circle of radius minor_r carried along an arc of radius
    major_r in the XZ plane. Path point at angle t is centre + major_r*(sin t,
    0, cos t), so t=270 deg sits below the centre and t=0 sits in front of it.

    This is the exhaust elbow. A stack of boxes can bend a duct, and it looks
    like a stack of boxes.
    """
    c = Vector(centre)
    rings = []
    for k in range(n_path + 1):
        t = a0 + (a1 - a0) * k / n_path
        radial = Vector((math.sin(t), 0.0, math.cos(t)))
        binormal = Vector((0.0, 1.0, 0.0))
        pc = c + radial * major_r
        rings.append([
            bm.verts.new(pc
                         + radial * (minor_r * math.cos(2 * math.pi * i / n_tube))
                         + binormal * (minor_r * math.sin(2 * math.pi * i / n_tube)))
            for i in range(n_tube)
        ])
    for a, b in zip(rings, rings[1:]):
        for i in range(n_tube):
            j = (i + 1) % n_tube
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return rings


def box(bm, centre, size, rot_z=0.0):
    """One matrix for scale/rotate/translate, so the order is not a judgement
    call -- see CLAUDE.md 0.18 for what getting that order wrong cost."""
    mat = (Matrix.Translation(centre)
           @ Matrix.Rotation(rot_z, 4, "Z")
           @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def bolt_circle(bm, r, z0, z1, count, bolt_r=0.13, phase=0.0, n=12):
    for i in range(count):
        a = phase + 2 * math.pi * i / count
        cylinder(bm, bolt_r, z0, z1, n=n,
                 centre=(r * math.cos(a), r * math.sin(a)))


# ---------------------------------------------------------------- materials
@contextlib.contextmanager
def layer(bm, index):
    """Everything built inside the block gets material_index = index. Snapshot
    diff rather than tracking return values, because revolve/sweep_arc return
    vert rings, not faces."""
    before = set(bm.faces)
    yield
    for f in bm.faces:
        if f not in before:
            f.material_index = index


def material(name, rgb, metallic=0.75, roughness=0.45, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = (*emission, 1.0)
                break
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 3.0
    mat.diffuse_color = (*rgb, 1.0)  # Workbench render reads this, not the nodes
    return mat


# ---------------------------------------------------------------- finish
def finish(bm, name, materials, bevel=0.07, bevel_angle_deg=25.0):
    """Bevel only edges that are actually corners.

    Beveling every edge (what the first grate script did) adds geometry to the
    smooth parts of a lathe that do not have an edge to soften -- 48 facets
    around a cylinder are not 48 corners. Filtering by face angle keeps the cost
    on the silhouette, where it shows.
    """
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bevel > 0:
        hard = [e for e in bm.edges
                if len(e.link_faces) == 2
                and e.calc_face_angle(0.0) > math.radians(bevel_angle_deg)]
        if hard:
            bmesh.ops.bevel(bm, geom=hard, offset=bevel, offset_type="OFFSET",
                            segments=1, profile=0.5, affect="EDGES",
                            clamp_overlap=True)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mat in materials:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def measure(obj):
    """Read the mesh back out. The build loop is not evidence -- same rule as
    reading instance properties instead of module state on the Studio side."""
    mesh = obj.data
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [v.x for v in corners]
    ys = [v.y for v in corners]
    zs = [v.z for v in corners]
    edge_use = {}
    for poly in mesh.polygons:
        for key in poly.edge_keys:
            edge_use[key] = edge_use.get(key, 0) + 1
    return {
        "size": (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)),
        "z": (min(zs), max(zs)),
        "verts": len(mesh.vertices),
        "polys": len(mesh.polygons),
        "tris": sum(len(p.vertices) - 2 for p in mesh.polygons),
        "open_edges": sum(1 for c in edge_use.values() if c != 2),
    }


def export(obj, name, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    scale = 1.0 / STUDS_PER_UNIT
    bpy.ops.export_scene.fbx(filepath=os.path.join(out_dir, name + ".fbx"),
                             use_selection=False, global_scale=scale)
    obj.scale = (scale, scale, scale)  # glTF has no scale argument, so bake it here
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"),
                              export_format="GLB", use_selection=False)
    obj.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, name + ".blend"))


def render(name, out_dir, views, target, ortho):
    """Workbench only: no lights, no GPU, and it is the operator's eyes, not
    mine -- nothing here can tell whether the result is any good."""
    for label, loc in views:
        cam_data = bpy.data.cameras.new("Cam")
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho
        cam = bpy.data.objects.new("Cam", cam_data)
        bpy.context.scene.collection.objects.link(cam)
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene = bpy.context.scene
        scene.camera = cam
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = 720
        scene.render.resolution_y = 720
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.join(out_dir, "%s_%s.png" % (name, label))
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)


def tube(bm, p0, p1, r, n=20):
    """A straight tube between two arbitrary points.

    Built by hand rather than with bmesh.ops.create_cone: create_cone's radius
    arguments have been renamed between Blender versions (diameter1/2 -> radius1/2),
    and a silently-wrong radius produces a shape that looks deliberate.
    """
    p0, p1 = Vector(p0), Vector(p1)
    axis = (p1 - p0).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(axis.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u).normalized()
    rings = [
        [bm.verts.new(p + u * (r * math.cos(2 * math.pi * i / n))
                        + v * (r * math.sin(2 * math.pi * i / n)))
         for i in range(n)]
        for p in (p0, p1)
    ]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[1])
    return rings


def panel_arc(bm, r_in, r_out, z0, z1, a0, a1, n=16):
    """A curved slab: the piece of an annulus between two radii, two angles and two
    heights. This is how a panel sits ON a cylinder -- a flat box either floats off
    the surface at its edges or sinks into it at the middle, and on a 2.6 radius
    that mismatch is about a quarter of a stud, which is visible.

    Winding is not argued about here; finish() runs recalc_face_normals over the
    whole mesh, and second-guessing it locally is how you get one flipped face.
    """
    vs = {}
    for j in range(n + 1):
        a = a0 + (a1 - a0) * j / n
        ca, sa = math.cos(a), math.sin(a)
        for r, rk in ((r_in, "i"), (r_out, "o")):
            for z, zk in ((z0, "0"), (z1, "1")):
                vs[(rk, zk, j)] = bm.verts.new((r * ca, r * sa, z))
    for j in range(n):
        bm.faces.new((vs[("o", "0", j)], vs[("o", "0", j + 1)],
                      vs[("o", "1", j + 1)], vs[("o", "1", j)]))
        bm.faces.new((vs[("i", "0", j)], vs[("i", "0", j + 1)],
                      vs[("i", "1", j + 1)], vs[("i", "1", j)]))
        bm.faces.new((vs[("i", "1", j)], vs[("i", "1", j + 1)],
                      vs[("o", "1", j + 1)], vs[("o", "1", j)]))
        bm.faces.new((vs[("i", "0", j)], vs[("i", "0", j + 1)],
                      vs[("o", "0", j + 1)], vs[("o", "0", j)]))
    for j in (0, n):
        bm.faces.new((vs[("i", "0", j)], vs[("i", "1", j)],
                      vs[("o", "1", j)], vs[("o", "0", j)]))
