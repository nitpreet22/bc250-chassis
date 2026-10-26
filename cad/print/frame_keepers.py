"""Frame keepers: four brackets that stop the frames lifting out from between the side walls.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\frame_keepers.py
Output: cad/print/stl/frame_keepers.stl, all four on one bed, top face down.

Why: the model first put the frame's square holes on its front face, under the walls' ears. On the real
frame they are on the outer side face, against the wall's inside face, so the ears' M6 slots face
plain steel. Rather than drill the walls, each keeper hooks over the top of one upright (and the
ear in front of it) and screws to the wall through the roof tile's existing screw slot nearest that
frame. Lifting the case by a frame's handle then pulls the walls up with it.

Each keeper is an L: a top tab over the upright, the ear and the wall's top edge, and a leg down
the wall's outside face to the roof screw. The roof screw goes through the leg, so it needs to be
an M3 x 16 instead of the M3 x 12 (the leg is 4 mm thick). The leg's hole is a slot (+-2 mm up and
down), so the tab can sit on the frame top even if the frame and the wall tops differ a little.
The roof tiles and lids keep the walls from spreading; the ears keep the frames from moving out.
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

LABEL_FONT = "C:/Windows/Fonts/arialbd.ttf"
LABEL_DEPTH = 0.6


def label_on_leg(text, side, y_start, z_base):
    """Text cut into the leg's inside face (the face against the wall), reading normally when
    you look at that face."""
    faces = [Part.makeFace(wires, "Part::FaceMakerBullseye")
             for wires in Part.makeWireString(text, LABEL_FONT, 5.0) if wires]
    letters = Part.makeCompound(faces).extrude(App.Vector(0, 0, LABEL_DEPTH))
    # Text X runs along the face (-Y on the right wall, +Y on the left), text Y goes up (+Z), and the
    # letters are cut from the face into the leg (+X on the right, -X on the left).
    placement = App.Matrix(0, 0, side, 0,
                           -side, 0, 0, 0,
                           0, 1, 0, 0,
                           0, 0, 0, 1)
    letters = letters.transformGeometry(placement)
    face_x = side * (m.INTERIOR_HALF_WIDTH + m.SIDE_WALL)
    letters.translate(App.Vector(face_x, y_start, z_base))
    return letters


def labelled(side, end):
    """The model's keeper (v1_model.frame_keeper, case coordinates) with its corner cut into the leg."""
    shape = m.frame_keeper(side, end)
    text = ("FRONT " if end == "front" else "BACK ") + ("R" if side > 0 else "L")
    box = shape.BoundBox
    # On the right wall the text reads towards -Y, so it starts at the leg's high-Y end.
    start_y = box.YMax - 3.0 if side > 0 else box.YMin + 3.0
    return shape.cut(label_on_leg(text, side, start_y, box.ZMin + 2.0))


def main():
    parts = [labelled(side, end) for end in ("front", "back") for side in (+1, -1)]
    for part in parts:
        assert len(part.Solids) == 1, "a keeper came out in pieces"
    print(f"front screw gap {m.keeper_screw_gap('front'):.1f} mm, back {m.keeper_screw_gap('back'):.1f} mm",
          flush=True)
    # Print top face down: the tab and the wall cap lie flat, the leg stands up.
    placed = export_stl.row([(part, export_stl.UP_IS_MINUS_Z) for part in parts])
    export_stl.export(placed, "frame_keepers.stl")


main()
