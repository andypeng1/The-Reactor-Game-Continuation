# floor_vent_em.py -- turn the exported floor vent (BottomChamberMAchine.gltf)
# into an electromagnetic one, WITHOUT moving a single edge of its outer shell.
#
# The operator's constraint is the whole job: "大小不能变". So the build does not
# start from a size and try to match -- it imports the shipped file, keeps every
# part's transform untouched, deletes exactly one object (the flat X decal) and
# puts the new geometry inside the volume that was already there. The invariant
# is then checked, not assumed: the exported GLB is re-imported and its bbox is
# compared against the ORIGINAL FILE's bbox to 1e-4. A rebuild that is 0.01
# studs too tall fails here and the script exits 1.
#
# Coordinates are authored in the BLACK BASE PLATE's own frame, in studs, with
# that plate's centre at the origin. Two things are read rather than assumed:
#   - which way is "up"   -> asked of the old decal, which sat on the face
#   - how high the rim is -> the highest existing vertex on that side
# The first version of this script authored in glTF node space and came out
# 2.37 studs too tall because it guessed the axis; the check is what caught it.
#
# Run:
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python _tools/blender/floor_vent_em.py
#
# Output: D:\BlenderRobloxTestProjects\FloorVentEM\

import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix, Vector

SRC = r"D:/BlenderRobloxTestProjects/From_RBLX/BottomChamberMAchine.gltf"
OUT = r"D:/BlenderRobloxTestProjects/FloorVentEM"
NAME = "FloorVent_EM"

X_IN = 4.025      # inner face of the end panels     (node: x = +/-4.025)
Z_IN = 1.5375     # inner face of the side boxes     (node z = +/-1.6625, 0.25 thick)


def world_bounds(objs):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for ob in objs:
        if ob.type != "MESH":
            continue
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def emissive_material(name, rgb, strength, metallic=0.0, roughness=0.35):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    for key in ("Emission Color", "Emission"):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = (*rgb, 1.0)
            break
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = strength
    mat.diffuse_color = (*rgb, 1.0)   # Workbench reads this, not the nodes
    return mat


def boxes_object(name, boxes, mat, frame):
    """One object holding several axis-aligned boxes, authored in `frame`
    (studs, origin at the base plate's centre, z along the plate's thickness)."""
    bm = bmesh.new()
    for centre, size in boxes:
        m = (Matrix.Translation(centre)
             @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = frame
    ob.data.polygons.foreach_set("use_smooth", [False] * len(ob.data.polygons))
    return ob


def build():
    ################################################################ source pass
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    objs = list(bpy.context.scene.objects)
    src_lo, src_hi = world_bounds(objs)
    src_size = src_hi - src_lo
    print("source bbox min %.4f %.4f %.4f" % tuple(src_lo))
    print("source bbox max %.4f %.4f %.4f" % tuple(src_hi))
    print("source size     %.4f %.4f %.4f" % tuple(src_size))

    # The black base plate is the frame everything is measured against. It is
    # picked by its own size (8.075 x 3.075 x 0.35) rather than by name: the
    # source names five different parts "Part".
    plates = [o for o in objs if o.type == "MESH"
              and abs(o.scale.x - 8.075) < 1e-3
              and abs(o.scale.y - 3.075) < 1e-3
              and abs(o.scale.z - 0.35) < 1e-3]
    if len(plates) != 1:
        raise RuntimeError("expected one 8.075 x 3.075 x 0.35 plate, found %d"
                           % len(plates))
    plate = plates[0]
    sx, sy, sz = plate.scale

    # matrix_world carries the scale, so dividing it back out leaves
    # translation + rotation: 1 unit = 1 stud, origin at the plate's centre.
    F = plate.matrix_world @ Matrix.Diagonal((1.0 / sx, 1.0 / sy, 1.0 / sz, 1.0))
    Finv = F.inverted()

    # Which side is the one you look at? The X decal sat on it -- ask the decal
    # instead of trusting a sign in the node table.
    decal = next(o for o in objs if o.type == "MESH" and o.name.startswith("Texture"))
    up = 1.0 if (Finv @ decal.matrix_world.translation).z > 0 else -1.0

    # How high may anything go? The highest existing vertex on the visible side.
    ceiling = -1e9
    for ob in objs:
        if ob.type != "MESH" or ob is decal:
            continue
        for v in ob.data.vertices:
            ceiling = max(ceiling, (Finv @ (ob.matrix_world @ v.co)).z * up)
    print("plate %.4f x %.4f x %.4f, up %+d, existing top %.4f studs above centre"
          % (sx, sy, sz, up, ceiling))
    if ceiling < 0.30:
        raise RuntimeError("the rim came out %.4f -- that is not the shape this "
                           "script was written against" % ceiling)

    def U(z):
        """A height above the plate's centre, flipped onto the visible side."""
        return z * up

    ################################################################ materials
    metal = emissive_material("EM_Housing", (0.16, 0.18, 0.20), 0.0,
                              metallic=0.85, roughness=0.35)
    glow = emissive_material("EM_Field", (0.10, 0.80, 1.00), 6.0)
    hot = emissive_material("EM_Coil", (0.70, 0.95, 1.00), 9.0)

    # The two olive strips at the ends become the aperture glow.
    for ob in objs:
        if ob.type == "MESH" and ob.name.startswith("Neon"):
            ob.data.materials.clear()
            ob.data.materials.append(glow)

    # The flat X decal is the only thing that goes away. Nothing else is
    # deleted -- the shell, the rim and the base are the size guarantee.
    bpy.data.objects.remove(decal, do_unlink=True)

    ################################################################ new parts
    FACE = 0.175            # the base plate's top: the grate face
    made = []

    # Field blades across the opening.
    blades = []
    for i in range(13):
        x = -3.50 + 7.00 * i / 12.0
        blades.append(((x, 0.0, U(FACE + 0.055)), (0.08, 2.85, 0.08)))
    made.append(boxes_object("EM_FieldBlades", blades, glow, F))

    # Thin rails down both long sides: they close the field onto the frame.
    made.append(boxes_object(
        "EM_SideRails",
        [((0.0, Z_IN - 0.075, U(FACE + 0.055)), (7.25, 0.07, 0.06)),
         ((0.0, -(Z_IN - 0.075), U(FACE + 0.055)), (7.25, 0.07, 0.06))],
        glow, F))

    # Coil housings at the two ends of the cavity. They sink 0.025 into the
    # black plate, so the field reads as coming out of something solid.
    made.append(boxes_object(
        "EM_CoilHousing",
        [((X_IN - 0.30, 0.0, U(0.28)), (0.34, 2.90, 0.26)),
         ((-(X_IN - 0.30), 0.0, U(0.28)), (0.34, 2.90, 0.26))],
        metal, F))

    # Three glowing rings banding each housing.
    rings = []
    for sign in (1, -1):
        for h in (0.365, 0.28, 0.195):
            rings.append(((sign * (X_IN - 0.30), 0.0, U(h)), (0.40, 2.70, 0.035)))
    made.append(boxes_object("EM_CoilRings", rings, hot, F))

    for ob in made:
        zs = [v.co.z for v in ob.data.vertices]
        print("  %-14s z %.4f .. %.4f   (allowed %.4f .. %.4f)"
              % (ob.name, min(zs), max(zs), U(-FACE), U(ceiling)))

    ################################################################ export
    os.makedirs(OUT, exist_ok=True)

    # The glTF importer shares ONE mesh datablock between nodes that came from
    # the same source mesh, and those nodes carry different material slots. The
    # FBX exporter cannot register a material index through a shared datablock
    # and quietly drops it -- it warned about nine objects on the first run.
    # Giving each object its own copy is geometry-neutral, so the size
    # invariant below still means what it says.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.make_single_user(object=True, obdata=True, material=True,
                                    animation=False, obdata_animation=False)
    bpy.ops.object.select_all(action="SELECT")

    glb = os.path.join(OUT, NAME + ".glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB",
                              use_selection=False)
    print("wrote", glb)
    print("  NOTE: this .glb is 1:1 in Blender units. It is NOT 1:1 in Studio:")
    print("  the glTF import path lands 1.6943x (10 / 5.902, measured Phase 83)")
    print("  -- import the .fbx with 5.902, not this file.")

    # trg.py: the operator's FBX import dialog multiplies by 5.902, so the FBX
    # is written at 1/5.902 and lands 1:1. FBX has a global_scale argument and
    # it scales the whole hierarchy -- use it and touch nothing. (The first
    # version scaled every object's location and scale by hand instead, and the
    # parts are PARENTED to the Model empty, so each one got scaled twice by a
    # different amount: the result was anisotropic, 7.83 x 7.23 x 0.34 instead
    # of 8.87 x 8.25 x 0.63. The check below is what said so.)
    SCALE = 1.0 / 5.902
    fbx = os.path.join(OUT, NAME + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True,
                             global_scale=SCALE)
    print("wrote", fbx)

    blend = os.path.join(OUT, NAME + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("wrote", blend)

    ################################################################ verify
    # The build loop is not evidence (CLAUDE.md 0.6, Phase 82): read the SHIPPED
    # files back and compare them against the file that came out of Roblox.
    checks = []

    def check(label, ok):
        checks.append((label, ok))

    def reread(path, factor, importer):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        importer(filepath=path)
        lo, hi = world_bounds(list(bpy.context.scene.objects))
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        return lo * factor, hi * factor, meshes

    glb_lo, glb_hi, parts = reread(glb, 1.0, bpy.ops.import_scene.gltf)
    for tag, lo, hi, objs in (("glb", glb_lo, glb_hi, parts),):
        got_size = hi - lo
        for axis, name in enumerate("XYZ"):
            check("%s size %s unchanged (%.6f vs %.6f, d=%.2e)"
                  % (tag, name, got_size[axis], src_size[axis],
                     abs(got_size[axis] - src_size[axis])),
                  abs(got_size[axis] - src_size[axis]) < 1e-4)
        for axis, name in enumerate("XYZ"):
            check("%s min %s unchanged (%.6f vs %.6f)"
                  % (tag, name, lo[axis], src_lo[axis]),
                  abs(lo[axis] - src_lo[axis]) < 1e-4)
        names = [o.name for o in objs]
        check("%s keeps the whole shell (%d mesh parts)" % (tag, len(names)),
              len(names) >= 18)
        check("%s has no Texture object" % tag,
              not any(n.startswith("Texture") for n in names))
        check("%s gives every part a material" % tag,
              all(len(o.data.materials) > 0 for o in objs))
        tri = 0
        for o in objs:
            o.data.calc_loop_triangles()
            tri += len(o.data.loop_triangles)
        check("%s triangle count %d < 6000" % (tag, tri), tri < 6000)
        print("  %s size %.4f %.4f %.4f  min %.4f %.4f %.4f  tris %d  parts %d"
              % ((tag,) + tuple(got_size) + tuple(lo) + (tri, len(names))))
        for o in sorted(objs, key=lambda o: o.name):
            mats = ",".join(m.name for m in o.data.materials)
            print("    %-20s %s" % (o.name, mats))

    # The FBX is written at 1/5.902 for the operator's import dialog, so the
    # number to compare is what his dialog will hand back to him.
    fbx_lo, fbx_hi, fbx_parts = reread(fbx, 5.902, bpy.ops.import_scene.fbx)
    fbx_size = fbx_hi - fbx_lo
    for axis, name in enumerate("XYZ"):
        check("fbx size %s x5.902 matches (%.6f vs %.6f, d=%.2e)"
              % (name, fbx_size[axis], src_size[axis],
                 abs(fbx_size[axis] - src_size[axis])),
              abs(fbx_size[axis] - src_size[axis]) < 1e-2)
    check("fbx gives every part a material",
          all(len(o.data.materials) > 0 for o in fbx_parts))
    print("  fbx size x5.902 %.4f %.4f %.4f  parts %d"
          % (tuple(fbx_size) + (len(fbx_parts),)))
    for o in sorted(fbx_parts, key=lambda o: o.name):
        mats = ",".join(m.name for m in o.data.materials)
        print("    %-20s %s" % (o.name, mats))

    ok = sum(1 for _, good in checks if good)
    for label, good in checks:
        print("%s %s" % ("PASS" if good else "FAIL", label))
    print("%d ok, %d failed" % (ok, len(checks) - ok))
    return 0 if ok == len(checks) else 1


try:
    rc = build()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    rc = 1
sys.exit(rc)
