"""Frame test strip: the first print with the PLA Matte profile, before any case wall.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\frame_test_strip.py
Output: cad/print/stl/frame_test_strip.stl (three pieces, already in print orientation).

1. Ear strip: the bottom 170 mm of a side wall's front-right ear, the part that bolts onto the
   frame's front face. Stand the frame and the strip on the table, the strip's lip against the
   upright's outer side and its keys towards the holes.
   - All four square keys drop into holes: the hole column position (RACK_HOLE_FROM_SIDE, EST from
     photos) and the hole heights (lowest hole R11 + the EIA pattern) are right.
   - Then bolt it on through the two slots with M6 screws and cage nuts, as the walls will be.
2. Fan gauge: the fan-plate collar fit (FAN_GRIP_GAP) with the Matte profile: a 120 mm fan should
   push in and stay when the gauge is turned over, like the coupon's one-notch gauge.
3. Nut block: an M3 nut should press into the pocket and an M3 screw slide through the hole.
"""
import os
import sys

import FreeCAD as App
import Part

PRINT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PRINT_DIR)
sys.path.insert(0, os.path.dirname(PRINT_DIR))
import export_stl  # noqa: E402
import print_settings as fit  # noqa: E402
import v1_model as m  # noqa: E402

STRIP_LENGTH = 170.0              # along the frame's height; covers rack holes 0..8
KEY_HOLE_INDICES = (0, 3, 5, 8)   # spread over 3.5 rack units, so a pitch error shows
SLOT_HOLE_INDICES = (1, 7)        # M6 + cage nut, as on the walls
KEY_HEIGHT = 2.0                  # into the frame's hole; the face sheet is thinner than this
LIP_HEIGHT = 18.0                 # along the upright's side face, measured from the strip's front
CAGE_NUT_RECESS = (14.0, 1.0)     # square x depth: room for the cage nut's flange on the frame face
LABEL_FONT = "C:/Windows/Fonts/arialbd.ttf"


def engraved_text(text, x, y, top_z, height=4.0, depth=0.6):
    faces = [Part.makeFace(wires, "Part::FaceMakerBullseye")
             for wires in Part.makeWireString(text, LABEL_FONT, height) if wires]
    label = Part.makeCompound(faces).extrude(App.Vector(0, 0, depth))
    label.translate(App.Vector(x, y, top_z - depth))
    return label


def ear_strip():
    """Print coordinates: x = height on the frame (0 = frame bottom), y = across the ear
    (0 = global X 85, 15 = the frame's outer side), z = 0 is the ear's front face."""
    ear_width = m.INTERIOR_HALF_WIDTH - m.EAR_INNER_X
    plate = Part.makeBox(STRIP_LENGTH, ear_width, m.EAR_THICKNESS)
    lip = Part.makeBox(STRIP_LENGTH, m.SIDE_WALL, LIP_HEIGHT, App.Vector(0, ear_width, 0))
    strip = plate.fuse(lip)
    hole_y = m.RACK_HOLE_X - m.EAR_INNER_X
    zs = m.rack_hole_zs()
    for index in KEY_HOLE_INDICES:
        key = fit.RACK_SQUARE_KEY
        strip = strip.fuse(Part.makeBox(key, key, KEY_HEIGHT,
                                        App.Vector(zs[index] - key / 2, hole_y - key / 2, m.EAR_THICKNESS)))
    slot_length = fit.M6_CLEARANCE_HOLE + 4.0
    for index in SLOT_HOLE_INDICES:
        slot = Part.makeBox(slot_length, fit.M6_CLEARANCE_HOLE, m.EAR_THICKNESS,
                            App.Vector(zs[index] - slot_length / 2, hole_y - fit.M6_CLEARANCE_HOLE / 2, 0))
        side, depth = CAGE_NUT_RECESS
        recess = Part.makeBox(side, side, depth,
                              App.Vector(zs[index] - side / 2, hole_y - side / 2, m.EAR_THICKNESS - depth))
        strip = strip.cut(slot).cut(recess)
    strip = strip.cut(engraved_text("BOTTOM", 8.0, 1.0, m.EAR_THICKNESS, height=3.5))
    return strip.removeSplitter()


def fan_gauge():
    lip_thickness = 3.0
    collar_depth = m.FAN_COLLAR_DEPTH
    length = fit.FAN_GRIP_GAP + 2 * lip_thickness
    bar = Part.makeBox(length, 8.0, 3.0)
    for lip_x in (0.0, length - lip_thickness):
        bar = bar.fuse(Part.makeBox(lip_thickness, 8.0, 3.0 + collar_depth, App.Vector(lip_x, 0, 0)))
    return bar.removeSplitter()


def nut_block():
    block = Part.makeBox(14.0, 14.0, 5.0)
    hole = Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, 5.0, App.Vector(7.0, 7.0, 0))
    radius = fit.M3_NUT_POCKET_FLATS / 2 / 0.8660254
    points = [App.Vector(7.0 + radius * c, 7.0 + radius * s, 5.0 - fit.M3_NUT_POCKET_DEPTH)
              for c, s in [(1, 0), (0.5, 0.8660254), (-0.5, 0.8660254), (-1, 0), (-0.5, -0.8660254), (0.5, -0.8660254)]]
    points.append(points[0])
    pocket = Part.Face(Part.makePolygon(points)).extrude(App.Vector(0, 0, fit.M3_NUT_POCKET_DEPTH))
    return block.cut(hole).cut(pocket)


def main():
    strip = ear_strip()
    gauge = fan_gauge()
    gauge.translate(App.Vector(0, 30.0, 0))
    nut = nut_block()
    nut.translate(App.Vector(STRIP_LENGTH - 14.0, 45.0, 0))
    export_stl.export([strip, gauge, nut], "frame_test_strip.stl")
    print("Rack hole heights used (mm):", ", ".join(f"{z:.1f}" for z in m.rack_hole_zs()[:9]), flush=True)


main()
