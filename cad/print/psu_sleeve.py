"""PSU sleeve: an open-ended printed case for the MSI A1000PL standing on its side beside the case.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\psu_sleeve.py
Output: cad/print/stl/psu_sleeve.stl, standing on its cable end.

The PSU (owner's measurement 2026-10-26: 150 x 150 x 86.5 mm) lies on one of its narrow faces, so
it is 86.5 mm wide, 150 mm tall and 150 mm long, and its fan looks sideways. The sleeve is four
walls around it:
  * Both ends stay open. The AC end is where the PSU blows its exhaust out and where the switch and
    plug are; the other end gives the modular plugs and their bend 80 mm of room (owner's choice).
  * Both tall side walls carry a fan grille, so the sleeve works with the fan facing either way.
  * Four small corner stops at the socket face keep the PSU from sliding into the cable room
    when a cable is pulled. They only cover the face's corners (7 mm), clear of the sockets.

Model coordinates: X across (the fan's axis), Y along the sleeve from the AC end (Y = 0) to the
cable end, Z up as it sits on the desk.

Printed standing on the cable end, every wall is vertical: the grille slots run up the print so
only their 4 mm tops bridge, and the stops' sloped undersides need no support.
"""
import os
import sys

import FreeCAD as App
import Part

PRINT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PRINT_DIR)
import export_stl  # noqa: E402

PSU_WIDTH = 86.5                  # standing on its side: the fan face to the opposite face
PSU_HEIGHT = 150.0
PSU_LENGTH = 150.0                # AC end to modular-socket face
CABLE_ROOM = 80.0                 # past the socket face, for the plugs and the cable bend
SLIDE_CLEARANCE = 0.5             # each side, so the PSU slides in without forcing
WALL = 3.0

INSIDE_WIDTH = PSU_WIDTH + 2 * SLIDE_CLEARANCE
INSIDE_HEIGHT = PSU_HEIGHT + 2 * SLIDE_CLEARANCE
SLEEVE_LENGTH = PSU_LENGTH + SLIDE_CLEARANCE + CABLE_ROOM
STOP_Y = PSU_LENGTH + SLIDE_CLEARANCE   # the stops' flat faces, just past the PSU's socket face
STOP_LEG = 8.0                    # along each inside wall from the corner

FAN_GRILLE_DIAMETER = 136.0       # the PSU's 135 mm fan, centred on its 150 x 150 face
SLOT_WIDTH = 4.0
SLOT_PITCH = 6.5                  # 2.5 mm ribs between slots
CROSS_BAR_WIDTH = 3.0
CROSS_BAR_PITCH = 34.0            # bars across the slots so the ribs don't flex

A1_MAX_PRINT_HEIGHT = 256.0


def box(x_range, y_range, z_range):
    return Part.makeBox(x_range[1] - x_range[0], y_range[1] - y_range[0], z_range[1] - z_range[0],
                        App.Vector(x_range[0], y_range[0], z_range[0]))


def fan_grille_cutter():
    """Slots running along the sleeve (up the print), clipped to the fan circle and split by
    cross bars. Cuts through both side walls at once."""
    centre_y = PSU_LENGTH / 2
    centre_z = WALL + INSIDE_HEIGHT / 2
    radius = FAN_GRILLE_DIAMETER / 2
    through_x = (-1.0, INSIDE_WIDTH + 2 * WALL + 1.0)
    slots = []
    slot_count = int(FAN_GRILLE_DIAMETER // SLOT_PITCH)
    first_slot_z = centre_z - (slot_count - 1) * SLOT_PITCH / 2
    for index in range(slot_count):
        slot_z = first_slot_z + index * SLOT_PITCH
        slots.append(box(through_x, (centre_y - radius, centre_y + radius),
                         (slot_z - SLOT_WIDTH / 2, slot_z + SLOT_WIDTH / 2)))
    circle = Part.makeCylinder(radius, through_x[1] - through_x[0],
                               App.Vector(through_x[0], centre_y, centre_z), App.Vector(1, 0, 0))
    grille = Part.makeCompound(slots).common(circle)
    for bar_offset in (-1.5, -0.5, 0.5, 1.5):
        bar_y = centre_y + bar_offset * CROSS_BAR_PITCH
        bar = box(through_x, (bar_y - CROSS_BAR_WIDTH / 2, bar_y + CROSS_BAR_WIDTH / 2),
                  (centre_z - radius, centre_z + radius))
        grille = grille.cut(bar)
    return grille


def corner_stop(corner_x, corner_z, x_direction, z_direction):
    """A tetrahedron in one inside corner: a right triangle (legs STOP_LEG along the two walls) at
    STOP_Y, shrinking to the corner STOP_LEG further on. The flat face stops the PSU; the sloped
    face is the print's underside, about 35 degrees off vertical."""
    corner = App.Vector(corner_x, STOP_Y, corner_z)
    along_x = corner + App.Vector(x_direction * STOP_LEG, 0, 0)
    along_z = corner + App.Vector(0, 0, z_direction * STOP_LEG)
    along_y = corner + App.Vector(0, STOP_LEG, 0)
    faces = [Part.Face(Part.makePolygon([a, b, c, a]))
             for a, b, c in ((corner, along_x, along_z), (corner, along_x, along_y),
                             (corner, along_z, along_y), (along_x, along_z, along_y))]
    return Part.Solid(Part.Shell(faces))


def sleeve():
    outside = box((0, INSIDE_WIDTH + 2 * WALL), (0, SLEEVE_LENGTH), (0, INSIDE_HEIGHT + 2 * WALL))
    inside = box((WALL, WALL + INSIDE_WIDTH), (-1.0, SLEEVE_LENGTH + 1.0), (WALL, WALL + INSIDE_HEIGHT))
    shape = outside.cut(inside).cut(fan_grille_cutter())
    inside_x = (WALL, WALL + INSIDE_WIDTH)
    inside_z = (WALL, WALL + INSIDE_HEIGHT)
    for corner_x, x_direction in ((inside_x[0], +1), (inside_x[1], -1)):
        for corner_z, z_direction in ((inside_z[0], +1), (inside_z[1], -1)):
            shape = shape.fuse(corner_stop(corner_x, corner_z, x_direction, z_direction))
    return shape.removeSplitter()


def main():
    shape = sleeve()
    assert len(shape.Solids) == 1, "the sleeve came out in pieces"
    assert SLEEVE_LENGTH <= A1_MAX_PRINT_HEIGHT, "too tall to print standing on its end"
    print(f"inside {INSIDE_WIDTH:.1f} x {INSIDE_HEIGHT:.1f} mm, length {SLEEVE_LENGTH:.1f} mm "
          f"(PSU {PSU_LENGTH:.0f} + cable room {CABLE_ROOM:.0f})", flush=True)
    # Cable end down: -Y (the AC end) faces up.
    placed = export_stl.stack([(shape, export_stl.UP_IS_MINUS_Y)])
    export_stl.export(placed, "psu_sleeve.stl")


main()
