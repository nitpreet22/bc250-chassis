"""Print files for the one-column test fit (node 1's parts), before the rest of the case, and the
same parts for columns 2 and 3 once they passed.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\column_test_parts.py
Output in cad/print/stl/ (PLA Matte, each file is one bed):
    col1_A_holders.stl     cradle, crossbar, blower holder and the four fan clips
    col1_B_fanplate_lower.stl
    col1_C_fanplate_upper.stl  with the two splice strips that join the halves
    col23_A_holders.stl    cradles, crossbars and blower holders for columns 2 and 3 (no clips:
                           they wait for the fan plate test)

What the test fit checks, with a board on the bench:
    cradle     the PCB's far edge sits in the slot and the far-end bracket drops into the pocket
    crossbar   the forks slide over both long PCB edges at the I/O end without touching anything
    holder     the BB7515 blower slides in and is held
    fan plate  both halves side by side: the fans push into the collar (crush ribs) and the clips hold
               them; laid on the heatsink, the opening lines up with the fins
"""
import os
import sys

PRINT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PRINT_DIR)
sys.path.insert(0, os.path.dirname(PRINT_DIR))
import export_stl  # noqa: E402
import v1_model as m  # noqa: E402

from export_stl import BED_GAP, UP_IS_MINUS_Y, UP_IS_PLUS_Y, UP_IS_Z, on_bed  # noqa: E402


def holders_plate(column):
    parts = [on_bed(m.cradle(column), UP_IS_Z, 0.0, 0.0)]
    parts.append(on_bed(m.crossbar(column), UP_IS_Z, 0.0, parts[-1].BoundBox.YMax + BED_GAP))
    holder_y = parts[-1].BoundBox.YMax + BED_GAP
    parts.append(on_bed(m.blower_holder(column), UP_IS_MINUS_Y, 0.0, holder_y))
    clip_x = parts[-1].BoundBox.XMax + BED_GAP
    for index, clip in enumerate(m.fan_clips(column)):
        parts.append(on_bed(clip, UP_IS_PLUS_Y, clip_x + (index % 2) * 20.0, holder_y + (index // 2) * 24.0))
    return parts


def board_holders_plate(columns):
    """Cradle and crossbar of every column stacked front to back, blower holders side by side behind
    them. The three columns' parts are the same shape; only their place in the case differs."""
    parts = []
    next_y = 0.0
    for column in columns:
        for shape in (m.cradle(column), m.crossbar(column)):
            parts.append(on_bed(shape, UP_IS_Z, 0.0, next_y))
            next_y = parts[-1].BoundBox.YMax + BED_GAP
    next_x = 0.0
    for column in columns:
        parts.append(on_bed(m.blower_holder(column), UP_IS_MINUS_Y, next_x, next_y))
        next_x = parts[-1].BoundBox.XMax + BED_GAP
    return parts


def main():
    column = m.COLUMNS[0]
    export_stl.export(holders_plate(column), "col1_A_holders.stl")
    export_stl.export(board_holders_plate(m.COLUMNS[1:]), "col23_A_holders.stl")
    lower, upper = m.fan_plate_halves(column)
    export_stl.export([on_bed(lower, UP_IS_PLUS_Y, 0.0, 0.0)], "col1_B_fanplate_lower.stl")
    upper_plate = [on_bed(upper, UP_IS_PLUS_Y, 0.0, 0.0)]
    strip_y = upper_plate[0].BoundBox.YMax + BED_GAP
    for index, strip in enumerate(m.splice_strips(column)):
        upper_plate.append(on_bed(strip, UP_IS_PLUS_Y, index * (m.SPLICE_STRIP[0] + BED_GAP), strip_y))
    export_stl.export(upper_plate, "col1_C_fanplate_upper.stl")


main()
