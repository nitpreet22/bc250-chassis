"""Fan grip gauge v2: picks the fan-plate collar fit with the PLA Matte profile.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\fan_grip_gauge.py
Output: cad/print/stl/fan_grip_gauge.stl (two bars, in print orientation).

Why: the frame test strip's gauge (120.4, the coupon's winning size) was loose with the Matte
profile and its tall, thin lips flexed. These bars have stiff 5 mm lips like the real collar:
    1 notch:  coupon size 120.4 with crush ribs (two 0.35 mm ribs on each lip that squash as the
              fan goes in, so the fit tolerates a few tenths of print error)
    2 notches: plain coupon size 120.0
Push a 120 mm fan in, then turn the bar over: the one that holds the fan without forcing wins.
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

BAR_WIDTH = 10.0
BAR_THICKNESS = 5.0
LIP_THICKNESS = 5.0
LIP_HEIGHT = 8.0                  # the collar's grip depth (v1_model.FAN_COLLAR_DEPTH)
RIB_RADIUS = 0.8
RIB_PROTRUSION = 0.35


def gauge_bar(gap, ribs, notch_count):
    length = gap + 2 * LIP_THICKNESS
    total_height = BAR_THICKNESS + LIP_HEIGHT
    bar = Part.makeBox(length, BAR_WIDTH, BAR_THICKNESS)
    for lip_x in (0.0, length - LIP_THICKNESS):
        bar = bar.fuse(Part.makeBox(LIP_THICKNESS, BAR_WIDTH, total_height, App.Vector(lip_x, 0, 0)))
    if ribs:
        inner_faces = ((LIP_THICKNESS, +1), (length - LIP_THICKNESS, -1))
        for face_x, into_gap in inner_faces:
            rib_x = face_x + into_gap * (RIB_PROTRUSION - RIB_RADIUS)
            for rib_y in (BAR_WIDTH * 0.25, BAR_WIDTH * 0.75):
                bar = bar.fuse(Part.makeCylinder(RIB_RADIUS, total_height, App.Vector(rib_x, rib_y, 0)))
    for notch in range(notch_count):
        bar = bar.cut(Part.makeBox(2.0, 1.5, BAR_THICKNESS, App.Vector(length / 2 + notch * 5.0, 0, 0)))
    return bar.removeSplitter()


def main():
    ribbed = gauge_bar(fit.FAN_GRIP_GAP, ribs=True, notch_count=1)
    plain = gauge_bar(fit.coupon_fit(120.0), ribs=False, notch_count=2)
    plain.translate(App.Vector(0, BAR_WIDTH + 8.0, 0))
    export_stl.export([ribbed, plain], "fan_grip_gauge.stl")


main()
