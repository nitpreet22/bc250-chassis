"""Write printable STLs: shapes already in print orientation (flat face on Z = 0), scaled in X and Y
by print_settings.XY_SCALE so the A1 + PLA Matte shrink is cancelled, and centred on the bed.

The STL coordinates are bed coordinates: slice with arrange off so the plate stays centred."""
import os

import FreeCAD as App
import Mesh

import print_settings

STL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")

# Which global direction faces up on the bed.
UP_IS_Z = App.Rotation()
UP_IS_PLUS_Y = App.Rotation(App.Vector(1, 0, 0), 90)     # +Y -> +Z
UP_IS_MINUS_Y = App.Rotation(App.Vector(1, 0, 0), -90)   # -Y -> +Z
UP_IS_MINUS_X = App.Rotation(App.Vector(0, 1, 0), 90)    # -X -> +Z: right side-wall pieces, inside face up
UP_IS_PLUS_X = App.Rotation(App.Vector(0, 1, 0), -90)    # +X -> +Z: left side-wall pieces
UP_IS_MINUS_Z = App.Rotation(App.Vector(1, 0, 0), 180)   # upside down: lids and roof tiles, blocks up
BED_GAP = 6.0


def on_bed(shape, rotation, x, y):
    """Rotate the part into print orientation and put its bounding box corner at (x, y, 0)."""
    part = shape.copy()
    part.rotate(App.Vector(0, 0, 0), rotation.Axis, rotation.Angle * 180.0 / 3.141592653589793)
    box = part.BoundBox
    part.translate(App.Vector(x - box.XMin, y - box.YMin, -box.ZMin))
    return part


def row(shapes_and_rotations, start_y=0.0):
    """Lay parts side by side along X, BED_GAP apart; returns them in print orientation."""
    parts = []
    x = 0.0
    for shape, rotation in shapes_and_rotations:
        parts.append(on_bed(shape, rotation, x, start_y))
        x = parts[-1].BoundBox.XMax + BED_GAP
    return parts


def stack(shapes_and_rotations, start_x=0.0):
    """Lay parts one behind the other along Y, BED_GAP apart; returns them in print orientation."""
    parts = []
    y = 0.0
    for shape, rotation in shapes_and_rotations:
        parts.append(on_bed(shape, rotation, start_x, y))
        y = parts[-1].BoundBox.YMax + BED_GAP
    return parts


def export(shapes, filename):
    """Tessellate, scale and save. Returns the scaled mesh's bounding box."""
    os.makedirs(STL_DIR, exist_ok=True)
    mesh = Mesh.Mesh()
    for shape in shapes:
        assert shape.isValid(), f"invalid solid in {filename}"
        mesh.addMesh(Mesh.Mesh(shape.tessellate(0.05)))
    scale = App.Matrix()
    scale.scale(print_settings.XY_SCALE, print_settings.XY_SCALE, print_settings.Z_SCALE)
    mesh.transform(scale)
    box = mesh.BoundBox
    usable = print_settings.BED_SIZE - 2 * print_settings.BED_EDGE_MARGIN
    if box.XLength > usable or box.YLength > usable:
        raise ValueError(f"{filename}: {box.XLength:.1f} x {box.YLength:.1f} mm does not fit the "
                         f"{usable:.0f} mm square away from the bed edges")
    # Sit the plate on the bed with its footprint centred.
    centre = print_settings.BED_SIZE / 2
    mesh.translate(centre - (box.XMin + box.XMax) / 2, centre - (box.YMin + box.YMax) / 2, -box.ZMin)
    path = os.path.join(STL_DIR, filename)
    mesh.write(path)
    box = mesh.BoundBox
    print(f"Wrote {path}: {box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm, "
          f"{sum(shape.Volume for shape in shapes) / 1000:.1f} cm3", flush=True)
    return box
