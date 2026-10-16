"""Print files for the whole Version 1 case (rail design), one bed per file, PLA Matte.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\case_parts.py
Output in cad/print/stl/case/:
    wall_R_strip1_lower.stl ... wall_L_strip3_upper.stl   12 side-wall pieces, inside face up
    fanplate_lower.stl, fanplate_upper.stl       print 3 of each (one per column); the upper bed also
                                                 carries that column's two joining strips
    divider_lower.stl, divider_upper.stl         print 2 of each (columns 2 and 3)
    backplate_lower.stl, backplate_upper.stl
    roof_front.stl, roof_back.stl                upside down, screw blocks up
    small_parts.stl                              3 lids (upside down), 8 wall splice bars, 2 gap shims
    crossbars_holddown.stl                       3 crossbars with the board hold-down lips (optional:
                                                 the crossbars already printed work without the lips)

Every part's shape comes from v1_model.py, so changing a number there and re-running this script
regenerates all the beds. Print the rail test piece (rail_test_parts.py) before the walls.
"""
import os
import sys

PRINT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PRINT_DIR)
sys.path.insert(0, os.path.dirname(PRINT_DIR))
import export_stl  # noqa: E402
import v1_model as m  # noqa: E402
from export_stl import (UP_IS_MINUS_X, UP_IS_MINUS_Z, UP_IS_PLUS_X, UP_IS_PLUS_Y, UP_IS_Z,  # noqa: E402
                        on_bed, row, stack)

SUBDIR = "case"


def export(parts, name):
    export_stl.export(parts, os.path.join(SUBDIR, name))


def walls():
    for side, letter, up in ((+1, "R", UP_IS_MINUS_X), (-1, "L", UP_IS_PLUS_X)):
        for name, piece in m.side_wall_pieces(side):
            export([on_bed(piece, up, 0.0, 0.0)], f"wall_{letter}_{name}.stl")


def plates():
    column = m.COLUMNS[0]          # the fan plates are the same in every column
    lower, upper = m.fan_plate_halves(column)
    export([on_bed(lower, UP_IS_PLUS_Y, 0.0, 0.0)], "fanplate_lower.stl")
    upper_bed = [on_bed(upper, UP_IS_PLUS_Y, 0.0, 0.0)]
    upper_bed += row([(strip, UP_IS_PLUS_Y) for strip in m.splice_strips(column)])
    for strip in upper_bed[1:]:
        strip.translate(export_stl.App.Vector(0, upper_bed[0].BoundBox.YMax + export_stl.BED_GAP, 0))
    export(upper_bed, "fanplate_upper.stl")

    column = m.COLUMNS[1]          # the two dividers are the same
    lower, upper = m.divider_halves(column.divider, m.blower_intake_centre(m.COLUMNS[0]), m.PLATE_TOP_Z,
                                    m.PLATE_SPLIT_Z)
    export([on_bed(lower, UP_IS_PLUS_Y, 0.0, 0.0)], "divider_lower.stl")
    export([on_bed(upper, UP_IS_PLUS_Y, 0.0, 0.0)], "divider_upper.stl")

    lower, upper = m.back_plate_halves()
    export([on_bed(lower, UP_IS_PLUS_Y, 0.0, 0.0)], "backplate_lower.stl")
    export([on_bed(upper, UP_IS_PLUS_Y, 0.0, 0.0)], "backplate_upper.stl")


def roof():
    front, back = m.roof_tiles()
    export([on_bed(front, UP_IS_MINUS_Z, 0.0, 0.0)], "roof_front.stl")
    export([on_bed(back, UP_IS_MINUS_Z, 0.0, 0.0)], "roof_back.stl")


def small_parts():
    parts = stack([(m.cold_box_cap(column), UP_IS_MINUS_Z) for column in m.COLUMNS])
    right_bars = [(bar, UP_IS_MINUS_X) for bar in m.wall_splice_bars(+1).Solids]
    left_bars = [(bar, UP_IS_PLUS_X) for bar in m.wall_splice_bars(-1).Solids]
    shims = [(m.gap_shim(), UP_IS_Z), (m.gap_shim(), UP_IS_Z)]
    for line in (right_bars, left_bars, shims):        # one row each, behind the lids
        next_y = max(part.BoundBox.YMax for part in parts) + export_stl.BED_GAP
        parts += row(line, start_y=next_y)
    export(parts, "small_parts.stl")


def crossbars():
    export(stack([(m.crossbar(column), UP_IS_Z) for column in m.COLUMNS]), "crossbars_holddown.stl")


def main():
    os.makedirs(os.path.join(export_stl.STL_DIR, SUBDIR), exist_ok=True)
    walls()
    plates()
    roof()
    small_parts()
    crossbars()


main()
