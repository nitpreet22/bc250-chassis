"""Window panels for the V1 side walls (3 right + 3 left), printed in black PLA Matte.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\window_panels.py
Output: cad/print/stl/window_panel_right.stl and window_panel_left.stl, flat, one panel each.
Print 3 of each, one per bed, with the usual PLA Matte profile; fit them plate side out.
They were meant to be clear PCTG, but PCTG warped on the open A1 (2026-10-22), even as a solid
2 mm panel on a 90 °C bed.
Print ONE panel first and screw it on: the holes allow +-0.5 mm, and the export carries the
PLA Matte shrink correction (print_settings.XY_SCALE) like the walls.
"""
import os
import sys

import FreeCAD as App
import Part

PRINT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PRINT_DIR)
sys.path.insert(0, os.path.dirname(PRINT_DIR))
import export_stl  # noqa: E402
import v1_model as m  # noqa: E402


def panel(side):
    """Panel in print orientation: x = across the window (wall Y), y = up the window (wall Z),
    z = thickness. The holes come from the wall's window_screw_positions(), so they always match."""
    column = m.COLUMNS[0]
    width, height = m.window_sheet_size(column, side)
    (y0, _), (z0, _) = m.window_opening(column, side)
    origin_y, origin_z = y0 - m.WINDOW_SHEET_OVERLAP, z0 - m.WINDOW_SHEET_OVERLAP
    shape = Part.makeBox(width, height, m.WINDOW_SHEET_THICKNESS)
    holes = [Part.makeCylinder(m.WINDOW_PANEL_HOLE / 2, m.WINDOW_SHEET_THICKNESS,
                               App.Vector(y - origin_y, z - origin_z, 0))
             for y, z in m.window_screw_positions(column, side)]
    return m.cut_all(shape, holes)


def main():
    export_stl.export([panel(+1)], "window_panel_right.stl")
    export_stl.export([panel(-1)], "window_panel_left.stl")


main()
