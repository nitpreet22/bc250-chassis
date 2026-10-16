"""Rail test piece: checks the slide-in rail fit before any side wall is printed (about 30 min).

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\rail_test_parts.py
Output: cad/print/stl/rail_test.stl (PLA Matte, one bed):
    wall section   a 60 mm tall piece of side wall with one rail pair and its bottom stop, made by the
                   same rail_pair() the side walls use
    plate offcut   a 3 mm plate end, the same thickness and end gap as the real plates
    nut block      a press-in nut block like the ones on the lids and roof tiles
    gap shim       the 2 mm shim that sets each board's fan gap

What to check:
    rail     the offcut slides down the channel by hand, all the way to the stop, without forcing,
             and doesn't flop more than about half a millimetre front to back
    nut      an M3 nut presses into the block's hex pocket and stays there when you turn it over;
             an M3 x 12 through the block's hole threads into it
    shim     slides between a fan frame and the heatsink fins with light contact
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
from export_stl import BED_GAP, UP_IS_MINUS_X, UP_IS_PLUS_Y, UP_IS_Z, on_bed  # noqa: E402

SECTION_HEIGHT = 60.0
PLATE_Y = (0.0, m.PLATE)
HALF = m.INTERIOR_HALF_WIDTH


def wall_section():
    """Side wall (4 mm) with one plate's rail pair and bottom stop, in wall coordinates."""
    margin = 12.0
    wall = m.box((HALF, HALF + m.SIDE_WALL), (PLATE_Y[0] - m.RAIL_REACH - margin, PLATE_Y[1] + m.RAIL_REACH + margin),
                 (0.0, SECTION_HEIGHT))
    return wall.fuse(m.rail_pair(HALF, PLATE_Y, SECTION_HEIGHT)).removeSplitter()


def plate_offcut():
    """The end of a plate as it sits in the rail: 30 mm wide, ending PLATE_END_GAP short of the wall."""
    return m.box((HALF - 30.0, m.PLATE_HALF_WIDTH), PLATE_Y, (m.RAIL_STOP_Z, SECTION_HEIGHT - 5.0))


def nut_block():
    """A pocket-style wall block on its own: M3 hole along X, hex pocket opening on the inner end."""
    depth = m.WALL_BLOCK_POCKET_DEPTH
    block_y = (0.0, m.WALL_BLOCK[1])
    z_range = (0.0, m.WALL_BLOCK[2])
    y_centre, z_centre = sum(block_y) / 2, sum(z_range) / 2
    block = m.box((HALF - depth, HALF), block_y, z_range)
    hole = Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, depth, App.Vector(HALF, y_centre, z_centre), App.Vector(-1, 0, 0))
    pocket = m.hex_prism_x(fit.M3_NUT_POCKET_FLATS, (HALF - m.WALL_BLOCK_NUT_X[1], HALF - m.WALL_BLOCK_NUT_X[0]),
                           y_centre, z_centre)
    return block.cut(hole).cut(pocket)


def main():
    parts = [on_bed(wall_section(), UP_IS_MINUS_X, 0.0, 0.0)]
    next_x = parts[-1].BoundBox.XMax + BED_GAP
    parts.append(on_bed(plate_offcut(), UP_IS_PLUS_Y, next_x, 0.0))
    next_x = parts[-1].BoundBox.XMax + BED_GAP
    parts.append(on_bed(nut_block(), UP_IS_Z, next_x, 0.0))
    parts.append(on_bed(m.gap_shim(), UP_IS_Z, next_x, parts[-1].BoundBox.YMax + BED_GAP))
    export_stl.export(parts, "rail_test.stl")


main()
