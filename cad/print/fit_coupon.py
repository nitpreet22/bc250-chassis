"""Fit coupon: print this first to measure how the A1 + PLA Basic reproduces the case's joints.

Run:  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\print\\fit_coupon.py
Output: cad/print/stl/fit_coupon.stl (plate + two fan-width gauges, already in print orientation).

What each test answers (the sizes are engraved next to each feature):
    Row 1  M3 clearance holes 3.2 / 3.4 / 3.6, M4 4.5, M5 5.5, M6 6.5 - which one an M3 slides
           through without wobble, and which one the rack's own screws fit.
    Row 2  M3 nut pockets 5.6 / 5.7 / 5.8 across flats - which one holds a nut without falling out.
    Row 3  Square keys 8.6 / 8.8 / 9.0 - which one drops into the frame's 9.1 mm square holes snugly.
    Bars   Fan gauges with 120.4 and 120.8 mm between the lips - which one grips a 120 mm fan
           firmly without forcing it (this sets the fan cups on the fan walls).
"""
import os

import FreeCAD as App
import Mesh
import Part

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl", "fit_coupon.stl")
FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"

PLATE_SIZE = (112.0, 66.0, 4.0)
LABEL_HEIGHT = 3.5
LABEL_DEPTH = 0.6

CLEARANCE_HOLES = [3.2, 3.4, 3.6, 4.5, 5.5, 6.5]
NUT_POCKET_FLATS = [5.6, 5.7, 5.8]
NUT_POCKET_DEPTH = 2.6            # M3 nut is 2.4 thick
SQUARE_KEYS = [8.6, 8.8, 9.0]
SQUARE_KEY_HEIGHT = 3.0           # taller than the frame's sheet, so the key fully engages

FAN_GAUGE_INNER = [120.4, 120.8]
FAN_GAUGE_BAR = (8.0, 3.0)        # width, thickness
FAN_GAUGE_LIP = (3.0, 7.0)        # thickness along the bar, height above the bar


def engraved_label(text, x, y):
    """Text cut LABEL_DEPTH into the plate's top face, left edge at (x, y)."""
    glyphs = Part.makeWireString(text, FONT_PATH, LABEL_HEIGHT)
    faces = []
    for glyph_wires in glyphs:
        if glyph_wires:
            faces.append(Part.makeFace(glyph_wires, "Part::FaceMakerBullseye"))
    label = Part.makeCompound(faces).extrude(App.Vector(0, 0, LABEL_DEPTH))
    label.translate(App.Vector(x, y, PLATE_SIZE[2] - LABEL_DEPTH))
    return label


def hex_prism(across_flats, height, centre):
    """Hexagonal pocket with two flats parallel to X."""
    radius = across_flats / 2 / 0.8660254
    points = [App.Vector(radius * cos_sin[0], radius * cos_sin[1], 0) for cos_sin in
              [(1, 0), (0.5, 0.8660254), (-0.5, 0.8660254), (-1, 0), (-0.5, -0.8660254), (0.5, -0.8660254)]]
    points.append(points[0])
    prism = Part.Face(Part.makePolygon(points)).extrude(App.Vector(0, 0, height))
    prism.translate(centre)
    return prism


def build_plate():
    width, depth, thickness = PLATE_SIZE
    plate = Part.makeBox(width, depth, thickness)
    cuts = []

    # Row 1: clearance holes.
    for index, diameter in enumerate(CLEARANCE_HOLES):
        x = 9.0 + index * 18.5
        cuts.append(Part.makeCylinder(diameter / 2, thickness, App.Vector(x, 13.0, 0)))
        cuts.append(engraved_label(f"{diameter:.1f}", x - 4.5, 3.0))

    # Row 2: nut pockets from the top, with a 3.4 mm hole through for the screw.
    for index, flats in enumerate(NUT_POCKET_FLATS):
        x = 14.0 + index * 34.0
        cuts.append(hex_prism(flats, NUT_POCKET_DEPTH, App.Vector(x, 33.0, thickness - NUT_POCKET_DEPTH)))
        cuts.append(Part.makeCylinder(1.7, thickness, App.Vector(x, 33.0, 0)))
        cuts.append(engraved_label(f"{flats:.1f}", x + 5.0, 31.0))

    for cut in cuts:
        plate = plate.cut(cut)

    # Row 3: square keys standing on the top face.
    for index, side in enumerate(SQUARE_KEYS):
        x = 14.0 + index * 34.0
        key = Part.makeBox(side, side, SQUARE_KEY_HEIGHT,
                           App.Vector(x - side / 2, 52.0 - side / 2, thickness))
        plate = plate.fuse(key)
        plate = plate.cut(engraved_label(f"{side:.1f}", x + 6.0, 50.0))
    return plate.removeSplitter()


def build_fan_gauge(inner_gap, y_offset):
    """Flat bar with a lip at each end; the fan frame should slide between the lips."""
    bar_width, bar_thickness = FAN_GAUGE_BAR
    lip_thickness, lip_height = FAN_GAUGE_LIP
    length = inner_gap + 2 * lip_thickness
    bar = Part.makeBox(length, bar_width, bar_thickness)
    for lip_x in (0.0, length - lip_thickness):
        bar = bar.fuse(Part.makeBox(lip_thickness, bar_width, lip_height,
                                    App.Vector(lip_x, 0, bar_thickness)))
    # Notches on the bar's side mark which gauge is which: 1 notch = narrow, 2 = wide.
    notch_count = FAN_GAUGE_INNER.index(inner_gap) + 1
    for notch in range(notch_count):
        bar = bar.cut(Part.makeBox(2.0, 1.5, bar_thickness, App.Vector(length / 2 + notch * 5.0, 0, 0)))
    bar.translate(App.Vector(0, y_offset, 0))
    return bar.removeSplitter()


def main():
    shapes = [build_plate()]
    for index, gap in enumerate(FAN_GAUGE_INNER):
        shapes.append(build_fan_gauge(gap, PLATE_SIZE[1] + 6.0 + index * (FAN_GAUGE_BAR[0] + 6.0)))
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    mesh = Mesh.Mesh()
    for shape in shapes:
        assert shape.isValid(), "invalid solid"
        mesh.addMesh(Mesh.Mesh(shape.tessellate(0.05)))
    mesh.write(OUTPUT_PATH)
    box = mesh.BoundBox
    print(f"Wrote {OUTPUT_PATH}: {box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm, "
          f"{sum(shape.Volume for shape in shapes) / 1000:.1f} cm3")


main()
