"""Floor spacers: two plain bars, one under the front frame and one under the back, filling the gap
between the floor and the frame.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\floor_spacer.py
Output: cad/print/stl/floor_spacers.stl, both bars lying flat on one bed.

Sizes come from the owner's measurement of the gap (2026-10-25): 205 x 29 x 4.5 mm. 29 mm is the
frame upright's depth (UPRIGHT_DEPTH). The model puts the walls' inner faces 200 mm apart, so a 205 mm
gap means the walls have spread at the floor; the bars are 0.5 mm short of the gap so they slide in.
"""
import os
import sys

import Part

PRINT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PRINT_DIR)
import export_stl  # noqa: E402

MEASURED_GAP_LENGTH = 205.0
SLIDE_CLEARANCE = 0.5
LENGTH = MEASURED_GAP_LENGTH - SLIDE_CLEARANCE
WIDTH = 29.0
THICKNESS = 4.5
COUNT = 2                         # front frame and back frame


def main():
    bars = [Part.makeBox(LENGTH, WIDTH, THICKNESS) for _ in range(COUNT)]
    placed = export_stl.stack([(bar, export_stl.UP_IS_Z) for bar in bars])
    export_stl.export(placed, "floor_spacers.stl")


main()
