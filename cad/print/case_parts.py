"""Print files for the whole Version 1 case (rail design), one bed per file, PLA Matte.

Each bed holds as much as fits, but only parts of one colour share a bed (white outside, black
inside; see BUILD.md). The plates are about 200 mm wide, so no two plates fit one bed. Instead, the
small black parts fill the space behind or beside the black plates.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\case_parts.py
Output in cad/print/stl/case/:
  white
    wall_R_strip{1,2,3}_{lower,upper}.stl, wall_L_...   12 side-wall pieces, inside face up, one per
                                                 bed (two middle pieces on one bed printed poorly)
    roof_front.stl, roof_back.stl                upside down, screw blocks up
    fanplate_upper.stl                           column 1 (also printed black for columns 2 and 3);
                                                 carries that column's two joining strips
  black
    fanplate_lower.stl, fanplate_upper.stl       columns 2 and 3 (column 1's are white)
    divider_lower.stl                            print 2 (columns 2 and 3)
    divider_upper_lids_a.stl                     a divider upper half, lids 1 and 2, crossbar 1
    divider_upper_lids_b.stl                     the other divider upper half, lid 3, crossbars 2 and 3
    backplate_lower.stl                          with the 8 wall splice bars beside it
    backplate_upper.stl                          with the 2 gap shims beside it
  The crossbars carry the board hold-down lips; the crossbars already printed work without them.

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


SHIM_LENGTHWAYS = export_stl.App.Rotation(export_stl.App.Vector(0, 0, 1), 90)    # 55 mm along Y


def export(parts, name):
    export_stl.export(parts, os.path.join(SUBDIR, name))


def behind(parts, shapes_and_rotations):
    """Stack more parts along Y, starting behind the parts already on the bed."""
    start_y = max(part.BoundBox.YMax for part in parts) + export_stl.BED_GAP
    return stack(shapes_and_rotations, start_y=start_y)


def beside(parts, shapes_and_rotations):
    """Stack more parts along Y in a column to the right of the parts already on the bed."""
    start_x = max(part.BoundBox.XMax for part in parts) + export_stl.BED_GAP
    return stack(shapes_and_rotations, start_x=start_x)


def walls():
    for side, letter, up in ((+1, "R", UP_IS_MINUS_X), (-1, "L", UP_IS_PLUS_X)):
        pieces = dict(m.side_wall_pieces(side))
        for name, piece in pieces.items():
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
    # The upper half leaves about 100 mm of the bed free: the lids (upside down) and crossbars go there.
    lids = [(m.cold_box_cap(column), UP_IS_MINUS_Z) for column in m.COLUMNS]
    crossbars = [(m.crossbar(column), UP_IS_Z) for column in m.COLUMNS]
    divider_bed = [on_bed(upper, UP_IS_PLUS_Y, 0.0, 0.0)]
    export(divider_bed + behind(divider_bed, [lids[0], lids[1], crossbars[0]]), "divider_upper_lids_a.stl")
    export(divider_bed + behind(divider_bed, [lids[2], crossbars[1], crossbars[2]]), "divider_upper_lids_b.stl")

    # The back plate halves leave a 30 mm column free at the side: splice bars on one, shims on the other.
    lower, upper = m.back_plate_halves()
    splice_bars = [(bar, UP_IS_MINUS_X) for bar in m.wall_splice_bars(+1).Solids]
    splice_bars += [(bar, UP_IS_PLUS_X) for bar in m.wall_splice_bars(-1).Solids]
    lower_bed = [on_bed(lower, UP_IS_PLUS_Y, 0.0, 0.0)]
    export(lower_bed + beside(lower_bed, splice_bars), "backplate_lower.stl")
    upper_bed = [on_bed(upper, UP_IS_PLUS_Y, 0.0, 0.0)]
    shims = [(m.gap_shim(), SHIM_LENGTHWAYS), (m.gap_shim(), SHIM_LENGTHWAYS)]
    export(upper_bed + beside(upper_bed, shims), "backplate_upper.stl")


def roof():
    front, back = m.roof_tiles()
    export([on_bed(front, UP_IS_MINUS_Z, 0.0, 0.0)], "roof_front.stl")
    export([on_bed(back, UP_IS_MINUS_Z, 0.0, 0.0)], "roof_back.stl")


def main():
    os.makedirs(os.path.join(export_stl.STL_DIR, SUBDIR), exist_ok=True)
    walls()
    plates()
    roof()


main()
