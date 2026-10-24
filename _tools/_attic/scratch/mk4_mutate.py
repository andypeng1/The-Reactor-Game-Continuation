# mk4_mutate.py -- re-export CblLaserMk4 from its own .blend with ONE defect
# injected, so cbl_laser_mk4_check.py can be shown to go red (CLAUDE.md 0.31:
# a check nobody has seen fail is decoration).
#
# It works from the delivered .blend rather than from hand-edited files on
# purpose: the mutation then travels through the SAME exporters that produced the
# real delivery, so a red line cannot be blamed on an odd file the harness built.
#
# MUTATION `none` IS THE CONTROL. It re-exports with no defect at all and must
# come back 86 ok / 0 failed. If the control reds, every mutant below is
# meaningless -- the harness, not the defect, is what the checker saw.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup --python \
#       mk4_mutate.py -- --mut shift --out D:\...\mk4_mutants\shift
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix

sys.path.insert(0, r"D:\rblxTRGproject\_tools\blender")
import trg  # noqa: E402

SRC = r"D:\BlenderRobloxTestProjects\CblLaserMk4\CblLaserMk4.blend"
NAME = "CblLaserMk4"


def pick(argv, flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


def meshes():
    return sorted([o for o in bpy.context.scene.objects if o.type == "MESH"],
                  key=lambda o: o.name)


def mut_shift():
    """One part 1.0 design stud too far forward (1.60 delivered -- 80x TOL)."""
    o = bpy.data.objects["CblLaserMk4Prongs"]
    o.data.transform(Matrix.Translation((1.0, 0.0, 0.0)))


def mut_scale1():
    """The 1.6943x glTF scale error, applied to the geometry so BOTH exporters
    carry it. This is the failure the 0.02-stud tolerance was sized against."""
    m = Matrix.Scale(10.0 / trg.STUDS_PER_UNIT, 4)
    for o in meshes():
        o.data.transform(m)


def mut_rename():
    """One node renamed -- what an exporter that suffixes, or a build that
    copy-pasted a part and forgot to rename it, hands back."""
    bpy.data.objects["CblLaserMk4Core"].name = "CblLaserMk4CoreMUT"


def mut_mat():
    """Every Cyan face on the Core repainted White. The material SET survives and
    the boxes of White/absent Cyan are what has to move: this is the defect the
    Studio material script would silently absorb, so the check must not."""
    o = bpy.data.objects["CblLaserMk4Core"]
    mesh = o.data
    names = [m.name if m else "" for m in mesh.materials]
    cyan = names.index("Mk4Cyan")
    white = names.index("Mk4White")
    n = 0
    for p in mesh.polygons:
        if p.material_index == cyan:
            p.material_index = white
            n += 1
    print("mut_mat: repainted %d faces" % n)


def mut_hole():
    """One face deleted from the Body. It opens exactly its own edges, which is
    what both watertight counts are for."""
    o = bpy.data.objects["CblLaserMk4Body"]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    # A big Hull face, so the deleted hole is not a 1e-9 sliver.
    victim = max(bm.faces, key=lambda f: f.calc_area())
    print("mut_hole: deleting face %d area %.4f" % (victim.index, victim.calc_area()))
    bmesh.ops.delete(bm, geom=[victim], context="FACES_ONLY")
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    which = pick(argv, "--mut", "none")
    out = os.path.abspath(pick(argv, "--out", r"D:\rblxTRGproject\_tools\_attic\scratch\mk4_mutants\none"))

    bpy.ops.wm.open_mainfile(filepath=SRC)
    objs = meshes()
    print("MUT %s  loaded %d meshes from %s" % (which, len(objs), SRC))
    for o in objs:
        print("   %-22s verts=%d polys=%d scale=%s" % (o.name, len(o.data.vertices),
                                                       len(o.data.polygons), tuple(o.scale)))
        if tuple(round(s, 9) for s in o.scale) != (1.0, 1.0, 1.0):
            print("   *** the .blend is NOT at authored scale -- the control would lie")

    fn = {"none": None, "shift": mut_shift, "scale1": mut_scale1,
          "rename": mut_rename, "mat": mut_mat, "hole": mut_hole,
          "split": None}.get(which)
    if which not in ("none", "shift", "scale1", "rename", "mat", "hole", "split"):
        raise SystemExit("unknown mutation %r" % which)
    if fn:
        fn()

    trg.export(objs, NAME, out, blend=False)
    if which == "split":
        # Only the FBX moves after the fact: the two formats then disagree with
        # each other, which is the one failure a single-format check cannot see.
        bpy.data.objects["CblLaserMk4Prongs"].data.transform(
            Matrix.Translation((0.5, 0.0, 0.0)))
        for o in bpy.context.scene.objects:
            o.select_set(False)
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.export_scene.fbx(filepath=os.path.join(out, NAME + ".fbx"),
                                 use_selection=True, global_scale=1.0 / trg.STUDS_PER_UNIT)
    print("MUT %s wrote %s" % (which, out))
    return 0


_rc = 1
try:
    _rc = main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    _rc = 1
sys.exit(_rc)
