"""Clear PCTG window panels for the V1 side walls (3 right + 3 left).

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\window_panels.py
Output: cad/print/stl/window_panel_right.stl and window_panel_left.stl, flat, one panel each.
Print 3 of each with the "Generic PCTG @BBL A1" filament profile.

For the clearest panels:
  * dry the PCTG first, 100 % infill with the infill lines in one direction, slow outer walls;
  * the face on the plate copies the plate's surface: the textured PEI gives a frosted pattern,
    a smooth plate gives a glossy face. Fit the panel with the plate side out.
Print ONE right panel first and screw it on: the holes allow +-0.5 mm, and PCTG's shrink has not
been measured (the export uses the PLA Matte figure, print_settings.XY_SCALE).
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
