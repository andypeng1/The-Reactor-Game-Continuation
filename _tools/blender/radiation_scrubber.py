# radiation_scrubber.py -- RadiationScrubberUnit, designed from the operator's
# brief "按照你自己的理解" (your own understanding).
#
# This is the experiment I predicted the outcome of earlier and now get to run:
# make something with no original to match, and see whether the result is
# actually better in Blender or just different. My own prediction, on the record
# before building: "系统对、外观素" -- everything justifiable, silhouette dull.
#
# DESIGN DECISIONS (these are mine, not measured from anything)
#
#   1. A vertical pressure vessel, not a box cabinet. The Studio version
#      (PROGRESS Phase 78) is an open frame with plate sides. I went the other
#      way on purpose: a scrubber is a vessel, the filter bed is inside it, and a
#      cylinder with a domed head is what that object actually is. It is also the
#      only shape here a parts-based build cannot reach without faking it.
#   2. One mechanism, not ten details. A bolted split at mid-height with a real
#      bolt circle is the single gesture that says "this opens, the cartridge
#      comes out". A second mechanism would have diluted it. My failure mode is
#      over-detailing, so the count of decorative elements is deliberately low.
#   3. The duct bends. sweep_arc for a 90-degree elbow, because a straight stack
#      is what a stack of boxes looks like, and the bend is free here.
#   4. Asymmetry. Intake on +Y, operator side on -Y, exhaust leaves toward +X.
#      A symmetric machine reads as an unbuilt one.
#   5. Panels are curved slabs (panel_arc), not flat boxes stuck on -- on a 2.62
#      radius a flat panel misses the surface by about a quarter stud at its
#      edges, which is visible.
#
# WHAT I CANNOT DO: judge it. Renders go next to the model; the silhouette call
# is the operator's. See PROGRESS Phase 80.
#
# RUN
#   "D:\Blender 5.1\blender.exe" --background --factory-startup \
#       --python "D:\rblxTRGproject\_tools\blender\radiation_scrubber.py"

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trg  # noqa: E402

NAME = "RadiationScrubberUnit"
OUT_DIR = r"D:\BlenderRobloxTestProjects"

# ---------------------------------------------------------------- dimensions (studs)
FLOOR_R = 3.30          # base flange outer radius
SKIRT_R = 2.90
BODY_R = 2.62
MID_FLANGE_R = 2.86
MID_Z0, MID_Z1 = 3.00, 3.34
DOME_Z0 = 5.55
NECK_R = 0.85
NECK_TOP = 7.35
DOME_H = 1.42           # dome rise, so the head is a dome and not a lid
DUCT_R = 0.90

# read_factory_settings wipes the file, so it has to happen before any datablock
# exists -- a Material created above this line is a dangling handle by the time
# finish() tries to read it ("StructRNA of type Material has been removed").
trg.new_scene()

# ---------------------------------------------------------------- materials
M_BODY, M_DARK, M_PANEL, M_GRADE, M_AMBER, M_GREEN, M_RED, M_DUCT = range(8)
MATERIALS = [
    trg.material("ScrubberBody", (0.34, 0.36, 0.39), metallic=0.85, roughness=0.42),
    trg.material("ScrubberDark", (0.11, 0.115, 0.125), metallic=0.80, roughness=0.50),
    trg.material("ScrubberPanel", (0.055, 0.060, 0.070), metallic=0.30, roughness=0.62),
    trg.material("ScrubberGrade", (0.12, 0.34, 0.85), metallic=0.0, roughness=0.35,
                 emission=(0.12, 0.34, 0.85)),
    trg.material("ScrubberLampAmber", (0.95, 0.55, 0.08), metallic=0.0, roughness=0.30,
                 emission=(0.95, 0.55, 0.08)),
    trg.material("ScrubberLampGreen", (0.18, 0.80, 0.32), metallic=0.0, roughness=0.30,
                 emission=(0.18, 0.80, 0.32)),
    trg.material("ScrubberLampRed", (0.85, 0.14, 0.11), metallic=0.0, roughness=0.30,
                 emission=(0.85, 0.14, 0.11)),
    trg.material("ScrubberDuct", (0.48, 0.49, 0.52), metallic=0.85, roughness=0.40),
]


def sector(deg_centre, deg_half):
    return (math.radians(deg_centre - deg_half), math.radians(deg_centre + deg_half))


def radial(angle_deg, z, r0, r1, radius, n=14):
    """A stub pointing outward from the axis -- lamps and the control knob."""
    a = math.radians(angle_deg)
    d = Vector((math.cos(a), math.sin(a), 0.0))
    trg.tube(bm, Vector((0.0, 0.0, z)) + d * r0, Vector((0.0, 0.0, z)) + d * r1,
             radius, n=n)


# ---------------------------------------------------------------- build
bm = bmesh.new()

# --- the vessel shell: skirt -> body -> mid flange -> body -> domed head -> neck.
# One continuous lathe, which is the point: there is no seam anywhere on it.
dome = []
theta_max = math.acos(NECK_R / BODY_R)
for k in range(0, 11):
    th = theta_max * k / 10.0
    dome.append((BODY_R * math.cos(th), DOME_Z0 + DOME_H * math.sin(th)))

profile = [
    (FLOOR_R, 0.00), (FLOOR_R, 0.18),
    (SKIRT_R, 0.18), (SKIRT_R, 0.70),
    (BODY_R, 0.70),
    (BODY_R, MID_Z0), (MID_FLANGE_R, MID_Z0), (MID_FLANGE_R, MID_Z1), (BODY_R, MID_Z1),
    (BODY_R, DOME_Z0),
]
profile += dome[1:]
profile += [(NECK_R, NECK_TOP)]

with trg.layer(bm, M_BODY):
    trg.revolve(bm, profile, n=64)

# --- bolts: 8 on the floor flange, 12 on the split. The bolt circle is the whole
# reason the split reads as a mechanism rather than a decorative ring.
with trg.layer(bm, M_DARK):
    trg.bolt_circle(bm, 3.05, -0.02, 0.22, 8, bolt_r=0.15)
    trg.bolt_circle(bm, 2.74, MID_Z0 - 0.03, MID_Z1 + 0.03, 12, bolt_r=0.12)

# --- intake grille, +Y, lower body. Curved frame + 5 curved slats.
with trg.layer(bm, M_DARK):
    a0, a1 = sector(90.0, 22.0)
    trg.panel_arc(bm, BODY_R - 0.04, BODY_R + 0.20, 1.20, 2.85, a0, a1, n=14)
    for i in range(5):
        z = 1.42 + i * 0.28
        trg.panel_arc(bm, BODY_R + 0.02, BODY_R + 0.30, z - 0.07, z + 0.07,
                      *sector(90.0, 19.0), n=14)

# --- operator side, -Y: curved panel, grade plate, one knob, three lamps.
with trg.layer(bm, M_PANEL):
    trg.panel_arc(bm, BODY_R - 0.04, BODY_R + 0.26, 1.35, 2.95,
                  *sector(270.0, 26.0), n=16)
with trg.layer(bm, M_GRADE):
    trg.panel_arc(bm, BODY_R - 0.04, BODY_R + 0.16, 0.95, 1.25,
                  *sector(270.0, 15.0), n=10)
with trg.layer(bm, M_DARK):
    radial(270.0, 1.78, BODY_R + 0.20, BODY_R + 0.52, 0.26)   # knob
with trg.layer(bm, M_AMBER):
    radial(258.0, 2.55, BODY_R + 0.20, BODY_R + 0.44, 0.115)
with trg.layer(bm, M_GREEN):
    radial(270.0, 2.55, BODY_R + 0.20, BODY_R + 0.44, 0.115)
with trg.layer(bm, M_RED):
    radial(282.0, 2.55, BODY_R + 0.20, BODY_R + 0.44, 0.115)

# --- exhaust: 90-degree elbow off the neck, horizontal run, end flange.
# sweep_arc starts at t=270deg (directly below its centre) with an upward tangent
# and ends at t=0 with a +X tangent, so the neck-to-horizontal bend is one call.
with trg.layer(bm, M_DUCT):
    ELBOW_R = 1.30
    elbow_top_z = NECK_TOP - 0.15 + ELBOW_R      # 8.50
    trg.sweep_arc(bm, (ELBOW_R, 0.0, NECK_TOP - 0.15), ELBOW_R, DUCT_R,
                  math.radians(270.0), math.radians(360.0))
    trg.tube(bm, (ELBOW_R, 0.0, elbow_top_z), (3.40, 0.0, elbow_top_z), DUCT_R, n=20)
    trg.tube(bm, (3.40, 0.0, elbow_top_z), (3.62, 0.0, elbow_top_z), DUCT_R + 0.25, n=20)

obj = trg.finish(bm, NAME, MATERIALS, bevel=0.07)

# ---------------------------------------------------------------- report
stats = trg.measure(obj)
print("SUMMARY model=%s" % NAME)
print("SUMMARY size=%.2f x %.2f x %.2f  z=%.2f..%.2f"
      % (stats["size"][0], stats["size"][1], stats["size"][2], stats["z"][0], stats["z"][1]))
print("SUMMARY verts=%d polys=%d tris=%d open_edges=%d"
      % (stats["verts"], stats["polys"], stats["tris"], stats["open_edges"]))
# What Studio should say after import, at the measured 5.902. If it does not say
# this, 5.902 is wrong and every asset exported through here is the wrong size.
print("SUMMARY expected_studio_size=%.2f x %.2f x %.2f"
      % (stats["size"][0], stats["size"][1], stats["size"][2]))

trg.export(obj, NAME, OUT_DIR)
trg.render(NAME, OUT_DIR,
           [("front", (0.0, -16.0, 4.8)), ("side", (16.0, 0.0, 4.8)),
            ("iso", (11.0, -11.0, 9.0))],
           target=(0.6, 0.0, 4.8), ortho=12.0)
print("SUMMARY wrote %s" % OUT_DIR)
