"""Version 1 case: layout numbers and the shapes of every part, in global coordinates.

Used by build_v1.py (the FreeCAD assembly) and by the print exporters in cad/print/.
Nothing here creates a document; every builder returns a Part shape.

Global frame (mm):
    X = width   (0 = case centre, + = right when looking at the front)
    Y = depth   (0 = outer face of the front rack frame, + = towards the back)
    Z = height  (0 = table; the frames, side walls and inner plates all stand on it)

V1 airflow, per node column (front to back):
    cold box -> fan plate holding two 120 mm fans -> stock heatsink (fin tops removed) -> board
    -> backplate -> blower zone -> the next column's divider.
    * Each cold box is closed at the top by a cap and fed through grilles in both side walls.
    * The fans push straight into the de-finned heatsink; the hot air leaves both ends of the
      fin channels, rises past the board and out through the roof grille.
    * A BB7515 blower hangs on the next divider, draws fresh air through a hole in it from the
      next cold box (the last one from a rear plenum) and blows up the backplate over the GDDR6.

Readings from the measurement sheet carry their ID (B1, R10, ...). EST marks a value read from
a photo or assumed; the frame test strip print checks the rack ones before the walls are printed.
"""
import os
import sys

import FreeCAD as App
import Import
import Part

CAD_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CAD_DIR, "print"))
import print_settings as fit  # noqa: E402  (needs the path above)

PROJECT_DIR = os.path.dirname(CAD_DIR)
BOARD_STEP = os.path.join(PROJECT_DIR, "reference", "BC250_Completeish_V1.step")

# ---------------------------------------------------------------------------------------------
# Rack frames, reused as the front and back of the case
# ---------------------------------------------------------------------------------------------
FRAME_WIDTH = 200.0               # R2
FRAME_HEIGHT = 469.5              # R1
UPRIGHT_FACE_WIDTH = 28.2         # R3: the face with the rack holes, along X
UPRIGHT_DEPTH = 29.0              # R4: along Y
TOP_BAND_HEIGHT = 29.0            # R8: logo plate; there is no bottom band (R9)
WINDOW_INSET = 3.3                # R6
WINDOW_THICKNESS = 4.5            # R5
RACK_HOLE_SIZE = 9.1              # R10
RACK_HOLE_FROM_SIDE = 7.2         # hole centre from the frame's outer side edge (photos; test strip fit 2026-10-15)
LOWEST_RACK_HOLE_Z = 35.0         # R11
RACK_UNIT = 44.45                 # standard EIA pattern, which the R10 photo shows
RACK_HOLE_OFFSETS_IN_UNIT = (6.35, 22.225, 38.1)
RACK_UNITS = 9                    # labels 01..09 on the frame
HANDLE_SIZE = (149.1, 17.3, 33.4)  # R12: length (X), depth (Y), height (Z)
HANDLE_SCREW_SPACING = 128.6      # R12, M4

# ---------------------------------------------------------------------------------------------
# BC-250 board in the coordinates of BC250_Completeish_V1.step ("board-local"):
#   local X = length (I/O end at -X), local Y = width (power connectors on the -Y edge),
#   local Z = thickness (PCB 0..1.6, heatsink on +Z, backplate on -Z).
# The model matches the readings: PCB 307.6 x 144 (B1 307.0, B2 144), heatsink 239.6 long
# (B4 240) and 20.9 from the far edge (B6 20), fin tops 26.1 above the PCB (S1 25.8).
# ---------------------------------------------------------------------------------------------
PCB_LOCAL_X = (-153.0, 154.6)
PCB_THICKNESS = 1.6
FIN_TIP_LOCAL_Z = 27.7
BACKPLATE_OUTER_LOCAL_Z = -3.9     # S4 reads 4.7 below the PCB; the extra 0.8 is kept as margin below
HEATSINK_LOCAL_X = (-105.9, 133.7)
HEATSINK_LOCAL_Y = (-49.5, 70.0)
BACKPLATE_LOCAL_X = (-135.9, 149.2)
PCB_TOP_EDGE_LOCAL_Y = (-50.4, 71.8)    # long edges at the I/O end (the board is 144 wide only at the power tab)
STEP_HEATSINK_OFFSET = App.Vector(0, -200.0, 0)   # the STEP shows the stock heatsink exploded +200 Y
STEP_BACKPLATE_OFFSET = App.Vector(0, 200.0, 0)   # ... and the backplate exploded -200 Y

# Brackets are not in the STEP. EST from the K4-K6 photos; the holders leave room around them.
IO_BRACKET_SCREWS_LOCAL_Y = (-40.7, 59.1)        # K4: 99.7 apart, match two PCB holes at x = -145.3
FAR_BRACKET_LOCAL_Y = (33.0, 66.0)               # K5/K6: by the coin cell, screws at y 43 / 53

# Where the board stands. Boards stand I/O end up, heatsink facing the front (-Y).
PCB_FAR_EDGE_Z = 40.0             # bottom edge of the PCB, resting in the cradle slot
POWER_EDGE_SHIFT_X = 6.2          # global X = local Y + this: power-connector edge at X -66


def board_z(local_x):
    return PCB_FAR_EDGE_Z + PCB_LOCAL_X[1] - local_x


def board_x(local_y):
    return local_y + POWER_EDGE_SHIFT_X


HEATSINK_Z = (board_z(HEATSINK_LOCAL_X[1]), board_z(HEATSINK_LOCAL_X[0]))     # 60.9 .. 300.5
HEATSINK_X = (board_x(HEATSINK_LOCAL_Y[0]), board_x(HEATSINK_LOCAL_Y[1]))     # -43.3 .. 76.2
HEATSINK_CENTRE_X = sum(HEATSINK_X) / 2
HEATSINK_CENTRE_Z = sum(HEATSINK_Z) / 2
PCB_TOP_EDGE_Z = board_z(PCB_LOCAL_X[0])                                     # 347.6
BACKPLATE_TOP_Z = board_z(BACKPLATE_LOCAL_X[0])                              # 330.5

# ---------------------------------------------------------------------------------------------
# Fans and blowers
# ---------------------------------------------------------------------------------------------
FAN_THICKNESS = 25.2              # F1
# Across the plate (X) the fans are modelled at the size the crush ribs squeeze them to, so the fit
# check sees the press fit as touching rather than as a clash.
FAN_SIZE = fit.FAN_GRIP_GAP - 2 * fit.FAN_GRIP_RIB_PROTRUSION
# Along the stack (Z) nothing squeezes them: each fan has its own slot, one per plate half.
# Bench test 2026-10-16: two fans in the first halves (119.4 mm slots) left a 1.8 mm gap at the split,
# so a frame is 120.3 mm along Z.
FAN_FRAME_LENGTH = 120.3
FAN_SLOT_CLEARANCE = 0.4
FAN_SLOT = FAN_FRAME_LENGTH + FAN_SLOT_CLEARANCE
FIN_GAP = 2.0                     # fan back face to the fin tips; set with a printed shim at assembly so small
                                  # position errors can't make the fans touch the fins (was 0.5)
BLOWER_SIZE = (75.3, 75.3, 15.4)  # F5, F6, F7: X, Z, thickness (Y)
BLOWER_INTAKE_DIAMETER = 50.0     # F10
BLOWER_OUTLET = (42.5, 12.0)      # F8: across X x thickness, on the top edge
BLOWER_BOTTOM_Z = 48.0            # outlet at 123 blows up across the GDDR6 (Z 130..222)
BLOWER_CENTRE_X = board_x(10.5)   # centre of the GDDR6 group

# ---------------------------------------------------------------------------------------------
# Printed case
# ---------------------------------------------------------------------------------------------
SIDE_WALL = 4.0                   # side wall frame: carries the case, holds the window screws' nuts
EAR_THICKNESS = 3.0               # side-wall ears that bolt to the front / back of the frames
EAR_INNER_X = 85.0                # ears cover the rack-hole column on each upright
PLATE = 3.0                       # dividers, fan plates, caps, back plate
FIRST_COLD_BOX_DEPTH = 28.0       # behind the front uprights; the frame opening adds more in front
COLD_BOX_DEPTH = 32.0
FAN_COLLAR_DEPTH = 17.0           # grips the fan frame over this depth from the cold face. Was 8: a fan in
                                  # a plate held flat slid out the hot side (2026-10-16). Nothing can stop it
                                  # there (fin tips 0.5 mm behind the fan), so the grip is longer instead. The
                                  # fan's last 8 mm stays clear for its cable exit.
BLOWER_GAP = 4.5                  # backplate to blower: keeps the PLA holder 3 mm off the metal
BLOWER_STANDOFF = 2.0             # blower intake face to the divider (holder plate)
REAR_PLENUM_DEPTH = 20.0          # feeds the last blower
COLD_BOX_TOP_Z = 308.0            # top of the lids, which sit on the fan plate and divider tops
CRADLE_SLOT_DEPTH = 2.4         # keeps the jaws 3 mm below the backplate, which stops 5.4 mm short of the PCB edge
CRADLE_JAW = 3.0                  # each side of the PCB in the cradle and the top crossbar forks
CROSSBAR_Z = (334.0, 345.0)       # above the backplate (330.5), below the PCB's I/O edge (347.6)
ROOF_THICKNESS = 3.0
GRILLE_SLOT = 6.0
GRILLE_PITCH = 10.0
INTERIOR_HALF_WIDTH = FRAME_WIDTH / 2     # side walls sit outside the frames' uprights

# Rails: the plates (fan plates, dividers, back plate) slide down channels formed by rib pairs on the
# side walls' inside faces and stand on a stop at the bottom. Nothing screws them in; a lid (or the
# roof) sits over their top edges. The play lets each wall be a millimetre or two off.
RAIL_CLEARANCE = 0.4              # each side of a plate in its channel
RAIL_CHANNEL = PLATE + 2 * RAIL_CLEARANCE
RAIL_RIB = (3.0, 4.0)             # rib thickness (Y), height in from the wall face (X)
RAIL_REACH = RAIL_CLEARANCE + RAIL_RIB[0]     # how far a rail reaches past a plate face
RAIL_STOP_Z = 8.0                 # plates stand on the stop; tall enough for a seam screw through it
PLATE_END_GAP = 1.0               # plate end to the wall face: walls can be 1 mm close or 2 mm far
PLATE_HALF_WIDTH = INTERIOR_HALF_WIDTH - PLATE_END_GAP
LID_GROOVE_DEPTH = 1.0            # groove under a lid / roof tile that takes a plate's top edge
PLATE_TOP_PLAY = 0.5              # plate top to the bottom of that groove
LID_Z = (COLD_BOX_TOP_Z - PLATE, COLD_BOX_TOP_Z)
PLATE_TOP_Z = LID_Z[0] + LID_GROOVE_DEPTH - PLATE_TOP_PLAY     # fan plates and dividers
# The tie parts (lids, cradles, crossbars, roof tiles) still screw to both walls, through slots.
TIE_SLOT_PLAY = 1.5               # +- along the slot: front-back for cradle / crossbar, up-down for lid / roof
GAP_SHIM = (40.0, 24.0)           # printed FIN_GAP-thick shim used to set each board's position
HOLD_DOWN_OVERLAP = 2.0           # crossbar lip over the PCB's top edge

# Side windows: clear printed PCTG panels screwed onto the outside of each side wall, over each
# column's hot zone (fan plate to next divider). The panels carry no load, so they can go on later;
# until then the openings are taped over so hot air can't leak out sideways.
WINDOW_MARGIN_Y = 5.0             # opening edge to the fan plate / divider faces
WINDOW_Z = (75.0, 292.0)          # most of the heatsink (60.9..300.5); the 233 mm panel stays 10 mm off the bed edges
LEFT_WINDOW_Z = (150.0, 292.0)    # the left wall keeps solid wall round the power-cable slots
WINDOW_SHEET_OVERLAP = 8.0        # panel past the opening on every side
WINDOW_SCREW_INSET = 4.0          # screw centre from the opening edge (4 mm from the panel's edge)
WINDOW_SHEET_THICKNESS = 2.0      # thin prints clearest; M3 x 8 screws reach the nuts
# The panel holes take M3 screws with room to spare: PCTG shrinks differently from the PLA the
# coupon measured, and +-0.5 mm over the 234 mm screw span keeps every screw on its nut.
WINDOW_PANEL_HOLE = 4.0

# Every inner part screws to both side walls through "wall blocks" at its ends: an M3 x 12 goes in
# from outside the wall, through the block, into a nut dropped into a slot in the block.
WALL_BLOCK = (10.0, 9.0, 12.0)    # depth from the wall (X), thickness (Y), height (Z)
WALL_BLOCK_NUT_X = (5.0, 5.0 + 2.6)   # nut slot / pocket, measured in from the wall's inside face
# Newer parts use "pocket" blocks: the block ends at the nut's far face and the nut presses into a
# hex pocket from that end, where it stays (coupon: the 5.7 mm pocket held a nut upside down).
WALL_BLOCK_POCKET_DEPTH = WALL_BLOCK_NUT_X[1]
# Plates taller than the 256 mm bed print in two halves that stack in their rails.
PLATE_SPLIT_Z = 180.7             # = the boundary between the two fans
BACK_PLATE_SPLIT_Z = 233.0
CRADLE_BLOCK_Z = 34.0
CAP_BLOCK_Z = COLD_BOX_TOP_Z - 6.0
# Side walls print in six pieces: three strips split at the dividers' rails, each in a lower and an
# upper piece. Y seams: screws front to back through the rail stop and through a post that fills the
# divider's channel above the lid. Z seam: a solid band across windows and grilles, joined by splice
# bars on the inside face of each cold box and the rear plenum.
WALL_SPLIT_Z = FRAME_HEIGHT / 2
WALL_SEAM_BAND = (WALL_SPLIT_Z - 12.0, WALL_SPLIT_Z + 12.0)
SEAM_POST_DEPTH = 8.0             # post / stop at a Y seam, in from the wall face; holds the screw's nut
SEAM_SCREW_ZS = (RAIL_STOP_Z / 2, 330.0, 440.0)
SPLICE_BAR_THICKNESS = 4.0
SPLICE_BAR_SCREW_Z_OFFSET = 6.0   # each side of WALL_SPLIT_Z
ROOF_BLOCK_Z = FRAME_HEIGHT - ROOF_THICKNESS - 6.0
CLIP_SCREW_INSET = 6.5            # fan clip screw from the opening edge, outside the collar
# Splice strips join the two fan plate halves across the split, on the hot face, one in each side
# margin beside the fans (clear of the collar and of the wall blocks at Z 150 / 215).
SPLICE_STRIP = (15.0, 34.0)       # width (X), length across the split (Z); thickness is PLATE
SPLICE_SCREW_FROM_SPLIT = 9.0     # one M3 x 10 each side of the split, nut on the strip
SPLICE_STRIP_CENTRE_XS = (-76.0, 87.6)    # clear of the collar and the hot-side rail rib


class Column:
    """Y positions of everything in one node column."""

    def __init__(self, index, front_y):
        self.index = index
        self.name = f"Node{index + 1}"
        y = front_y
        if index == 0:
            self.divider = None
            self.cold_box = (y, y + FIRST_COLD_BOX_DEPTH)
        else:
            self.divider = (y, y + PLATE)
            self.cold_box = (y + PLATE, y + PLATE + COLD_BOX_DEPTH)
        self.fan_plate = (self.cold_box[1], self.cold_box[1] + PLATE)
        self.fan = (self.cold_box[1], self.cold_box[1] + FAN_THICKNESS)    # front face flush with the plate
        self.fin_tips_y = self.fan[1] + FIN_GAP
        # local z -> global Y = board_y_origin - z
        self.board_y_origin = self.fin_tips_y + FIN_TIP_LOCAL_Z
        self.pcb_front_y = self.board_y_origin - PCB_THICKNESS
        self.pcb_back_y = self.board_y_origin
        self.backplate_outer_y = self.board_y_origin - BACKPLATE_OUTER_LOCAL_Z
        self.blower = (self.backplate_outer_y + BLOWER_GAP, self.backplate_outer_y + BLOWER_GAP + BLOWER_SIZE[2])
        self.back_y = self.blower[1] + BLOWER_STANDOFF       # front face of the next divider / back plate


def column_layout():
    columns = []
    front_y = UPRIGHT_DEPTH
    for index in range(3):
        column = Column(index, front_y)
        columns.append(column)
        front_y = column.back_y
    return columns


COLUMNS = column_layout()
BACK_PLATE_Y = (COLUMNS[-1].back_y, COLUMNS[-1].back_y + PLATE)
REAR_PLENUM_Y = (BACK_PLATE_Y[1], BACK_PLATE_Y[1] + REAR_PLENUM_DEPTH)
CASE_DEPTH = REAR_PLENUM_Y[1] + UPRIGHT_DEPTH
ROOF_Z = (FRAME_HEIGHT - ROOF_THICKNESS, FRAME_HEIGHT)


# ---------------------------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------------------------
def box(x_range, y_range, z_range):
    """Axis-aligned box from (min, max) ranges."""
    (x0, x1), (y0, y1), (z0, z1) = x_range, y_range, z_range
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0))


def cylinder_y(diameter, y_range, x, z):
    return Part.makeCylinder(diameter / 2, y_range[1] - y_range[0], App.Vector(x, y_range[0], z), App.Vector(0, 1, 0))


def cut_all(shape, cutters):
    return shape.cut(Part.makeCompound(cutters)) if cutters else shape


def mirror_x(shape):
    return shape.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))


def rack_hole_zs():
    """Centres of the frame's square holes, bottom to top: the lowest hole (R11) is the first hole of
    its rack unit. The frame test strip's keys dropped into holes 0, 3, 5 and 8 (2026-10-15)."""
    unit_start = LOWEST_RACK_HOLE_Z - RACK_HOLE_OFFSETS_IN_UNIT[0]
    return [unit_start + unit * RACK_UNIT + offset
            for unit in range(RACK_UNITS) for offset in RACK_HOLE_OFFSETS_IN_UNIT]


RACK_HOLE_X = FRAME_WIDTH / 2 - RACK_HOLE_FROM_SIDE
EAR_SCREW_HOLE_INDICES = (1, 8, 17, 25)     # which rack holes the side-wall ears bolt to (4 per ear)


# ---------------------------------------------------------------------------------------------
# Rack frames (reused, not printed)
# ---------------------------------------------------------------------------------------------
def frame_shapes(outer_y, inward):
    """Uprights with their square holes, top band and window of one frame."""
    half = FRAME_WIDTH / 2
    inner_x = half - UPRIGHT_FACE_WIDTH
    y_range = sorted((outer_y, outer_y + inward * UPRIGHT_DEPTH))
    face_y = sorted((outer_y, outer_y + inward * 1.5))
    holes = []
    for z in rack_hole_zs():
        for x in (-RACK_HOLE_X, RACK_HOLE_X):
            holes.append(box((x - RACK_HOLE_SIZE / 2, x + RACK_HOLE_SIZE / 2), face_y,
                             (z - RACK_HOLE_SIZE / 2, z + RACK_HOLE_SIZE / 2)))
    uprights = Part.makeCompound([box((inner_x, half), y_range, (0.0, FRAME_HEIGHT)),
                                  box((-half, -inner_x), y_range, (0.0, FRAME_HEIGHT))])
    uprights = uprights.cut(Part.makeCompound(holes))
    band = box((-inner_x, inner_x), y_range, (FRAME_HEIGHT - TOP_BAND_HEIGHT, FRAME_HEIGHT))
    window_y = sorted((outer_y + inward * WINDOW_INSET, outer_y + inward * (WINDOW_INSET + WINDOW_THICKNESS)))
    window = box((-inner_x, inner_x), window_y, (0.0, FRAME_HEIGHT - TOP_BAND_HEIGHT))
    handle_y = sorted((outer_y + inward * 6.0, outer_y + inward * (6.0 + HANDLE_SIZE[1])))
    handle = box((-HANDLE_SIZE[0] / 2, HANDLE_SIZE[0] / 2), handle_y,
                 (FRAME_HEIGHT + HANDLE_SIZE[2] - 8.0, FRAME_HEIGHT + HANDLE_SIZE[2]))
    for leg_x in (-HANDLE_SCREW_SPACING / 2, HANDLE_SCREW_SPACING / 2):
        handle = handle.fuse(box((leg_x - 8.0, leg_x + 8.0), handle_y, (FRAME_HEIGHT, FRAME_HEIGHT + HANDLE_SIZE[2])))
    return {"Uprights": uprights, "TopBand": band, "Window": window, "Handle": handle.removeSplitter()}


# ---------------------------------------------------------------------------------------------
# Printed parts
# ---------------------------------------------------------------------------------------------
def grille_slots(x_range, y_range, z_range):
    """Slots through a wall: each slot runs along Y (the wall's length), stacked in Z. They stop short
    of the rails at each end and skip the solid band at the wall seam."""
    inset = RAIL_REACH + 1.0
    slots = []
    z = z_range[0]
    while z + GRILLE_SLOT <= z_range[1]:
        in_band = z < WALL_SEAM_BAND[1] and z + GRILLE_SLOT > WALL_SEAM_BAND[0]
        if not in_band:
            slots.append(box(x_range, (y_range[0] + inset, y_range[1] - inset), (z, z + GRILLE_SLOT)))
        z += GRILLE_PITCH
    return slots


def cold_y_ranges():
    """Y ranges fed through the side-wall grilles: the three cold boxes and the rear plenum."""
    return [column.cold_box for column in COLUMNS] + [REAR_PLENUM_Y]


def window_opening(column, side):
    """((y0, y1), (z0, z1)) of the window opening over a column's hot zone."""
    y_range = (column.fan_plate[1] + WINDOW_MARGIN_Y, column.back_y - WINDOW_MARGIN_Y)
    return y_range, (LEFT_WINDOW_Z if side < 0 else WINDOW_Z)


def window_screw_positions(column, side):
    """(y, z) of the six M3 screws holding a window panel: three along its bottom edge and three
    along its top edge (the side edges are next to the rails)."""
    (y0, y1), (z0, z1) = window_opening(column, side)
    ys = (y0 + 6.0, (y0 + y1) / 2, y1 - 6.0)
    zs = (z0 - WINDOW_SCREW_INSET, z1 + WINDOW_SCREW_INSET)
    return [(y, z) for y in ys for z in zs]


def window_openings(column, side):
    """The window opening as cut in the wall: split by the solid band at the wall seam."""
    y_range, (z0, z1) = window_opening(column, side)
    pieces = []
    for low, high in ((z0, min(z1, WALL_SEAM_BAND[0])), (max(z0, WALL_SEAM_BAND[1]), z1)):
        if high > low:
            pieces.append((y_range, (low, high)))
    return pieces


def window_sheet_size(column, side):
    (y0, y1), (z0, z1) = window_opening(column, side)
    return (y1 - y0 + 2 * WINDOW_SHEET_OVERLAP, z1 - z0 + 2 * WINDOW_SHEET_OVERLAP)


def hex_prism_x(across_flats, x_range, y, z):
    """Hexagonal nut pocket whose axis runs along X."""
    radius = across_flats / 2 / 0.8660254
    corners = [(1, 0), (0.5, 0.8660254), (-0.5, 0.8660254), (-1, 0), (-0.5, -0.8660254), (0.5, -0.8660254)]
    points = [App.Vector(x_range[0], y + radius * c, z + radius * s) for c, s in corners]
    points.append(points[0])
    return Part.Face(Part.makePolygon(points)).extrude(App.Vector(x_range[1] - x_range[0], 0, 0))


def hex_prism_y(across_flats, y_range, x, z):
    """Hexagonal nut pocket whose axis runs along Y."""
    radius = across_flats / 2 / 0.8660254
    corners = [(1, 0), (0.5, 0.8660254), (-0.5, 0.8660254), (-1, 0), (-0.5, -0.8660254), (0.5, -0.8660254)]
    points = [App.Vector(x + radius * c, y_range[0], z + radius * s) for c, s in corners]
    points.append(points[0])
    return Part.Face(Part.makePolygon(points)).extrude(App.Vector(0, y_range[1] - y_range[0], 0))


def slot_x(diameter, x_range, y, z, axis, half_length):
    """Slotted hole through a wall (along X), elongated along `axis` ("y" or "z") by +-half_length."""
    def centre(offset):
        return (y + offset, z) if axis == "y" else (y, z + offset)
    ends = [Part.makeCylinder(diameter / 2, x_range[1] - x_range[0], App.Vector(x_range[0], *centre(d)),
                              App.Vector(1, 0, 0)) for d in (-half_length, half_length)]
    if axis == "y":
        middle = box(x_range, (y - half_length, y + half_length), (z - diameter / 2, z + diameter / 2))
    else:
        middle = box(x_range, (y - diameter / 2, y + diameter / 2), (z - half_length, z + half_length))
    return middle.fuse(ends)


def add_wall_blocks(shape, block_y_range, z_centre, nut_from, height=WALL_BLOCK[2], nut_style="slot"):
    """Fuse a wall block onto each X end of `shape` and cut its screw hole and nut holder.
    nut_style "slot": a slot opening on the block's +Y / -Y face (nut_from = +1 / -1), as on the parts
    already printed. "pocket": the block is shorter and the nut presses into a hex pocket in its inner
    end, where it stays. `height` must stay within the part where it prints standing on that face."""
    half = INTERIOR_HALF_WIDTH
    depth = WALL_BLOCK[0] if nut_style == "slot" else WALL_BLOCK_POCKET_DEPTH
    y_centre = sum(block_y_range) / 2
    z_range = (z_centre - height / 2, z_centre + height / 2)
    flats = fit.M3_NUT_POCKET_FLATS
    blocks, cuts = [], []
    for sign in (+1, -1):
        def x_span(near, far):
            """X range from `near` to `far` mm in from this end's wall face."""
            return tuple(sorted((sign * (half - near), sign * (half - far))))
        blocks.append(box(x_span(0.0, depth), block_y_range, z_range))
        hole_length = depth - 1.0 if nut_style == "slot" else depth
        cuts.append(Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, hole_length,
                                      App.Vector(sign * half, y_centre, z_centre), App.Vector(-sign, 0, 0)))
        if nut_style == "slot":
            slot_y = (y_centre - flats / 2, block_y_range[1]) if nut_from > 0 else (block_y_range[0], y_centre + flats / 2)
            cuts.append(box(x_span(*WALL_BLOCK_NUT_X), slot_y, (z_centre - flats / 2, z_centre + flats / 2)))
        else:
            cuts.append(hex_prism_x(flats, x_span(*WALL_BLOCK_NUT_X), y_centre, z_centre))
    return cut_all(shape.fuse(blocks), cuts).removeSplitter()


def wall_screw_points():
    """(y, z, slot axis) of every M3 screw that holds a tie part to a side wall (same on both walls).
    The wall hole is a slot along that axis, so the part can sit where the plates put it."""
    points = []
    for column in COLUMNS:
        points.append((cap_block_y(column), CAP_BLOCK_Z, "z"))
        points.append((sum(cradle_y(column)) / 2, CRADLE_BLOCK_Z, "y"))
        points.append((sum(crossbar_y(column)) / 2, sum(CROSSBAR_Z) / 2, "y"))
    points += [(y, ROOF_BLOCK_Z, "z") for y in roof_block_ys()]
    return points


def rails():
    """(plate y_range, top z) of every plate that slides down a rail pair."""
    plates = [(column.fan_plate, LID_Z[0]) for column in COLUMNS]
    plates += [(column.divider, LID_Z[0]) for column in COLUMNS if column.divider is not None]
    plates.append((BACK_PLATE_Y, ROOF_Z[0]))
    return plates


def wall_seam_ys():
    """Y of the vertical seams between side-wall strips: the middle of each divider's channel."""
    return [sum(column.divider) / 2 for column in COLUMNS if column.divider is not None]


def seam_screw_x():
    return INTERIOR_HALF_WIDTH - SEAM_POST_DEPTH / 2


def rail_pair(half, plate_y, top_z):
    """The two ribs and the bottom stop of one plate's rail on the +X wall's inside face (wall face at
    X = half). Also used by the rail test piece."""
    (y0, y1) = plate_y
    rib_x = (half - RAIL_RIB[1], half)
    return [box(rib_x, (y0 - RAIL_REACH, y0 - RAIL_CLEARANCE), (0.0, top_z)),
            box(rib_x, (y1 + RAIL_CLEARANCE, y1 + RAIL_REACH), (0.0, top_z)),
            box(rib_x, (y0 - RAIL_REACH, y1 + RAIL_REACH), (0.0, RAIL_STOP_Z))]


def rail_ribs(half):
    """Rib pairs, bottom stops and seam posts on the +X wall's inside face."""
    shapes = []
    for plate_y, top_z in rails():
        shapes += rail_pair(half, plate_y, top_z)
    post_x = (half - SEAM_POST_DEPTH, half)
    width = RAIL_CHANNEL / 2 + RAIL_RIB[0]
    for seam_y in wall_seam_ys():
        shapes.append(box(post_x, (seam_y - width, seam_y + width), (0.0, RAIL_STOP_Z)))
        shapes.append(box(post_x, (seam_y - width, seam_y + width), (COLD_BOX_TOP_Z, ROOF_Z[0])))
    return shapes


def seam_screw_cuts():
    """Front-to-back M3 x 10 holes through each Y seam's stop and post, nut pocket on the back face."""
    cuts = []
    width = RAIL_CHANNEL / 2 + RAIL_RIB[0]
    x = seam_screw_x()
    for seam_y in wall_seam_ys():
        y_range = (seam_y - width, seam_y + width)
        for z in SEAM_SCREW_ZS:
            cuts.append(Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, y_range[1] - y_range[0],
                                          App.Vector(x, y_range[0], z), App.Vector(0, 1, 0)))
            cuts.append(hex_prism_y(fit.M3_NUT_POCKET_FLATS, (y_range[1] - fit.M3_NUT_POCKET_DEPTH, y_range[1]), x, z))
    return cuts


def splice_bar_spans():
    """Y range of the splice bar in each cold region (cold boxes and rear plenum), clear of the rails."""
    return [(y0 + RAIL_REACH + 0.5, y1 - RAIL_REACH - 0.5) for y0, y1 in cold_y_ranges()]


def splice_bar_screws():
    """(y, z) of the screws through the wall into the splice bars: two each side of the seam."""
    points = []
    for y0, y1 in splice_bar_spans():
        ys = (y0 + 5.0, y1 - 5.0) if y1 - y0 >= 20.0 else ((y0 + y1) / 2,)      # the plenum's bar is short
        for y in ys:
            for dz in (-SPLICE_BAR_SCREW_Z_OFFSET, SPLICE_BAR_SCREW_Z_OFFSET):
                points.append((y, WALL_SPLIT_Z + dz))
    return points


def wall_splice_bars(side):
    """Bars on the inside face across the Z seam; M3 x 8 from outside the wall into a pressed-in nut."""
    half = INTERIOR_HALF_WIDTH
    bar_x = (half - SPLICE_BAR_THICKNESS, half)
    bars = []
    for y_range in splice_bar_spans():
        bar = box(bar_x, y_range, WALL_SEAM_BAND)
        holes = []
        for y, z in splice_bar_screws():
            if y_range[0] < y < y_range[1]:
                holes.append(Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, SPLICE_BAR_THICKNESS,
                                               App.Vector(bar_x[0], y, z), App.Vector(1, 0, 0)))
                holes.append(hex_prism_x(fit.M3_NUT_POCKET_FLATS, (bar_x[0], bar_x[0] + fit.M3_NUT_POCKET_DEPTH), y, z))
        bars.append(cut_all(bar, holes))
    compound = Part.makeCompound(bars)
    return compound if side > 0 else mirror_x(compound)


def side_wall_whole(side):
    """One side wall in one piece (side = -1 left, +1 right): front and back ears, rails, cold-box
    grilles, a window opening per column with the nut pockets for its panel, slotted holes for the
    tie parts, the seam screws and, on the left, a cable slot per node. Built at +X, mirrored for the left."""
    half = INTERIOR_HALF_WIDTH
    wall_x = (half, half + SIDE_WALL)
    wall = box(wall_x, (-EAR_THICKNESS, CASE_DEPTH + EAR_THICKNESS), (0.0, FRAME_HEIGHT))
    ears = [box((EAR_INNER_X, half), (-EAR_THICKNESS, 0.0), (0.0, FRAME_HEIGHT)),
            box((EAR_INNER_X, half), (CASE_DEPTH, CASE_DEPTH + EAR_THICKNESS), (0.0, FRAME_HEIGHT))]
    wall = wall.fuse(ears + rail_ribs(half))
    cuts = []
    for y_range in cold_y_ranges():
        cuts += grille_slots(wall_x, y_range, (15.0, COLD_BOX_TOP_Z - 15.0))
    nut_x = (half, half + fit.M3_NUT_POCKET_DEPTH)       # pockets open on the inside face
    for column in COLUMNS:
        for y_range, z_range in window_openings(column, side):
            cuts.append(box(wall_x, y_range, z_range))
        for y, z in window_screw_positions(column, side):
            cuts.append(Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, SIDE_WALL, App.Vector(half, y, z), App.Vector(1, 0, 0)))
            cuts.append(hex_prism_x(fit.M3_NUT_POCKET_FLATS, nut_x, y, z))
    zs = rack_hole_zs()
    slot_length = fit.M6_CLEARANCE_HOLE + 4.0       # +-2 mm in Z for the rack-hole phase
    for index in EAR_SCREW_HOLE_INDICES:
        for y_range in ((-EAR_THICKNESS, 0.0), (CASE_DEPTH, CASE_DEPTH + EAR_THICKNESS)):
            cuts.append(box((RACK_HOLE_X - fit.M6_CLEARANCE_HOLE / 2, RACK_HOLE_X + fit.M6_CLEARANCE_HOLE / 2),
                            y_range, (zs[index] - slot_length / 2, zs[index] + slot_length / 2)))
    for y, z, axis in wall_screw_points():
        cuts.append(slot_x(fit.M3_CLEARANCE_HOLE, wall_x, y, z, axis, TIE_SLOT_PLAY))
    for y, z in splice_bar_screws():
        cuts.append(Part.makeCylinder(fit.M3_CLEARANCE_HOLE / 2, SIDE_WALL, App.Vector(half, y, z), App.Vector(1, 0, 0)))
    cuts += seam_screw_cuts()
    if side < 0:
        for column in COLUMNS:
            cuts.append(box(wall_x, (column.fan_plate[1] + 10.0, column.pcb_front_y), (60.0, 140.0)))
    wall = cut_all(wall.removeSplitter(), cuts)
    return wall if side > 0 else mirror_x(wall)


def side_wall_pieces(side):
    """The six printed pieces of a side wall: [(name, shape)], strips front to back, lower then upper."""
    whole = side_wall_whole(side)
    y_cuts = [-EAR_THICKNESS - 1.0] + wall_seam_ys() + [CASE_DEPTH + EAR_THICKNESS + 1.0]
    x_range = (-INTERIOR_HALF_WIDTH - SIDE_WALL - 1.0, INTERIOR_HALF_WIDTH + SIDE_WALL + 1.0)
    pieces = []
    for strip in range(len(y_cuts) - 1):
        for level, z_range in (("lower", (-1.0, WALL_SPLIT_Z)), ("upper", (WALL_SPLIT_Z, FRAME_HEIGHT + 1.0))):
            piece = whole.common(box(x_range, (y_cuts[strip], y_cuts[strip + 1]), z_range))
            pieces.append((f"strip{strip + 1}_{level}", piece.removeSplitter()))
    return pieces


def side_wall(side):
    return Part.makeCompound([shape for _, shape in side_wall_pieces(side)])


def window_sheets(side):
    """The PCTG window panels on one side wall's outside face, with their screw holes."""
    sheet_x = (INTERIOR_HALF_WIDTH + SIDE_WALL, INTERIOR_HALF_WIDTH + SIDE_WALL + WINDOW_SHEET_THICKNESS)
    sheets = []
    for column in COLUMNS:
        (y0, y1), (z0, z1) = window_opening(column, side)
        overlap = WINDOW_SHEET_OVERLAP
        sheet = box(sheet_x, (y0 - overlap, y1 + overlap), (z0 - overlap, z1 + overlap))
        holes = [Part.makeCylinder(WINDOW_PANEL_HOLE / 2, WINDOW_SHEET_THICKNESS,
                                   App.Vector(sheet_x[0], y, z), App.Vector(1, 0, 0))
                 for y, z in window_screw_positions(column, side)]
        sheets.append(cut_all(sheet, holes))
    compound = Part.makeCompound(sheets)
    return compound if side > 0 else mirror_x(compound)


def fan_opening_x():
    return (HEATSINK_CENTRE_X - fit.FAN_GRIP_GAP / 2, HEATSINK_CENTRE_X + fit.FAN_GRIP_GAP / 2)


def fan_slots():
    """(bottom, top) of the lower and upper fan's slot in the plate opening; they meet at the plate
    split, which is the middle of the heatsink length."""
    return [(HEATSINK_CENTRE_Z - FAN_SLOT, HEATSINK_CENTRE_Z), (HEATSINK_CENTRE_Z, HEATSINK_CENTRE_Z + FAN_SLOT)]


def fan_zs():
    """(bottom, top) of the lower and upper fan frame, centred in its slot."""
    margin = FAN_SLOT_CLEARANCE / 2
    return [(bottom + margin, top - margin) for bottom, top in fan_slots()]


def clip_screw_xs():
    opening_x = fan_opening_x()
    return (opening_x[0] - CLIP_SCREW_INSET, opening_x[1] + CLIP_SCREW_INSET)


def clip_screw_zs():
    return [(bottom + top) / 2 for bottom, top in fan_zs()]


def fan_plate_halves(column):
    """Plate between the cold box and the hot side, printed as a lower and an upper half that meet at
    the fan boundary and stack in the fan plate's rails. Each fan pushes into its own half's part of the opening from the cold side until it
    is flush with the cold face; the collar grips their frames (FAN_GRIP_GAP, with crush ribs on both sides)."""
    half = PLATE_HALF_WIDTH
    opening_x = fan_opening_x()
    opening_z = (fan_slots()[0][0], fan_slots()[1][1])
    plate = box((-half, half), column.fan_plate, (RAIL_STOP_Z, PLATE_TOP_Z))
    collar_y = (column.fan_plate[0], column.fan_plate[0] + FAN_COLLAR_DEPTH)
    collar = box((opening_x[0] - PLATE, opening_x[1] + PLATE), collar_y, (opening_z[0] - PLATE, opening_z[1] + PLATE))
    plate = plate.fuse(collar).cut(box(opening_x, collar_y, opening_z))
    ribs = []
    for edge_x, into_gap in ((opening_x[0], +1), (opening_x[1], -1)):
        rib_x = edge_x + into_gap * (fit.FAN_GRIP_RIB_PROTRUSION - fit.FAN_GRIP_RIB_RADIUS)
        for fan_bottom, fan_top in fan_zs():
            for fraction in (0.2, 0.8):
                rib_z = fan_bottom + fraction * (fan_top - fan_bottom)
                ribs.append(Part.makeCylinder(fit.FAN_GRIP_RIB_RADIUS, FAN_COLLAR_DEPTH,
                                              App.Vector(rib_x, collar_y[0], rib_z), App.Vector(0, 1, 0)))
    plate = plate.fuse(ribs)
    plate = cut_all(plate, [cylinder_y(fit.M3_CLEARANCE_HOLE, column.fan_plate, x, z)
                            for x in clip_screw_xs() for z in clip_screw_zs()])
    plate = cut_all(plate, [cylinder_y(fit.M3_CLEARANCE_HOLE, column.fan_plate, x, z)
                            for x, z in splice_screw_points()])
    halves = []
    for z_range in ((RAIL_STOP_Z, PLATE_SPLIT_Z), (PLATE_SPLIT_Z, PLATE_TOP_Z)):
        piece = plate.common(box((-half - 1, half + 1), (column.fan_plate[0] - 1, collar_y[1] + 1), z_range))
        halves.append(piece.removeSplitter())
    return halves


def splice_screw_points():
    """(x, z) of the four M3 screws that join the fan plate halves through the splice strips."""
    return [(x, PLATE_SPLIT_Z + side * SPLICE_SCREW_FROM_SPLIT)
            for x in SPLICE_STRIP_CENTRE_XS for side in (-1, +1)]


def splice_strips(column):
    """Two flat strips on the fan plate's hot face, each bridging the split with one screw into
    each half. Screw heads on the cold face, nuts on the strip."""
    strip_y = (column.fan_plate[1], column.fan_plate[1] + PLATE)
    strips = []
    for centre_x in SPLICE_STRIP_CENTRE_XS:
        x_range = (centre_x - SPLICE_STRIP[0] / 2, centre_x + SPLICE_STRIP[0] / 2)
        z_range = (PLATE_SPLIT_Z - SPLICE_STRIP[1] / 2, PLATE_SPLIT_Z + SPLICE_STRIP[1] / 2)
        strip = box(x_range, strip_y, z_range)
        strips.append(cut_all(strip, [cylinder_y(fit.M3_CLEARANCE_HOLE, strip_y, x, z)
                                      for x, z in splice_screw_points() if x == centre_x]))
    return strips


def fan_plate(column):
    return Part.makeCompound(fan_plate_halves(column))


def fan_clips(column):
    """Clips on the cold side that stop the fans sliding forward out of the collar. Each takes an
    M3 x 10 through the fan plate, with the nut on the hot side outside the collar."""
    opening_x = fan_opening_x()
    screw_xs = clip_screw_xs()
    clip_y = (column.fan_plate[0] - PLATE, column.fan_plate[0])
    clips = []
    for centre_z in clip_screw_zs():
        for edge_x, inward, screw_x in ((opening_x[0], +1, screw_xs[0]), (opening_x[1], -1, screw_xs[1])):
            x_range = sorted((edge_x - inward * (CLIP_SCREW_INSET + 4.0), edge_x + inward * 3.0))
            clip = box(x_range, clip_y, (centre_z - 8.0, centre_z + 8.0))
            clips.append(clip.cut(cylinder_y(fit.M3_CLEARANCE_HOLE, clip_y, screw_x, centre_z)))
    return clips


def cold_box_front_y(column):
    return UPRIGHT_DEPTH if column.divider is None else column.divider[1]


def cap_block_y(column):
    return (cold_box_front_y(column) + column.fan_plate[0]) / 2


def lid_y(column):
    """The lid spans the cold box and the tops of the plates either side of it."""
    front = UPRIGHT_DEPTH if column.divider is None else column.divider[0]
    return (front, column.fan_plate[1])


def top_edge_groove(plate_y, half_width, z_bottom):
    """Groove in the underside of a lid or roof tile that takes a plate's top edge."""
    return box((-half_width - 0.5, half_width + 0.5), (plate_y[0] - RAIL_CLEARANCE, plate_y[1] + RAIL_CLEARANCE),
               (z_bottom, z_bottom + LID_GROOVE_DEPTH))


def cold_box_cap(column):
    """Lid of the cold box. It sits over the top edges of the column's fan plate and divider, which
    stops them lifting out of their rails, and screws to each wall through a slot (pressed-in nuts)."""
    lid = box((-INTERIOR_HALF_WIDTH, INTERIOR_HALF_WIDTH), lid_y(column), LID_Z)
    plates = [column.fan_plate] + ([column.divider] if column.divider is not None else [])
    lid = cut_all(lid, [top_edge_groove(plate_y, PLATE_HALF_WIDTH, LID_Z[0]) for plate_y in plates])
    y = cap_block_y(column)
    return add_wall_blocks(lid, (y - WALL_BLOCK[1] / 2, y + WALL_BLOCK[1] / 2), CAP_BLOCK_Z, nut_from=+1,
                           nut_style="pocket")


def blower_intake_centre(column):
    """(x, z) of the blower's intake; the intake is centred on the blower body (EST, F9 photo)."""
    return BLOWER_CENTRE_X, BLOWER_BOTTOM_Z + BLOWER_SIZE[1] / 2


def blower_holder_screws():
    """(x, z) of the four M3 screws holding a blower holder to the wall behind it."""
    x0 = BLOWER_CENTRE_X - BLOWER_SIZE[0] / 2 - 0.3 - 2.4 - 4.5
    x1 = BLOWER_CENTRE_X + BLOWER_SIZE[0] / 2 + 0.3 + 2.4 + 4.5
    zs = (BLOWER_BOTTOM_Z + 5.0, BLOWER_BOTTOM_Z + BLOWER_SIZE[1] - 15.0)
    return [(x, z) for x in (x0, x1) for z in zs]


def divider_halves(y_range, intake_centre, top_z, split_z):
    """Wall at the front of a cold box (or the back plate), in two halves that stack in its rails, with
    the hole the blower in front of it breathes through and the holes for that blower's holder."""
    half = PLATE_HALF_WIDTH
    plate = box((-half, half), y_range, (RAIL_STOP_Z, top_z))
    x, z = intake_centre
    plate = plate.cut(cylinder_y(BLOWER_INTAKE_DIAMETER + 2.0, y_range, x, z))
    plate = cut_all(plate, [cylinder_y(fit.M3_CLEARANCE_HOLE, y_range, hx, hz) for hx, hz in blower_holder_screws()])
    halves = []
    for z_range in ((RAIL_STOP_Z, split_z), (split_z, top_z)):
        piece = plate.common(box((-half, half), y_range, z_range))
        halves.append(piece.removeSplitter())
    return halves


def divider(y_range, intake_centre):
    return Part.makeCompound(divider_halves(y_range, intake_centre, PLATE_TOP_Z, PLATE_SPLIT_Z))


def blower_holder(column):
    """U-shaped holder screwed to the wall behind the blower: back plate (the standoff), two sides,
    a bottom, front lips and four screw tabs. Top left open for the outlet."""
    x0 = BLOWER_CENTRE_X - BLOWER_SIZE[0] / 2 - 0.3
    x1 = BLOWER_CENTRE_X + BLOWER_SIZE[0] / 2 + 0.3
    z0 = BLOWER_BOTTOM_Z - 0.3
    z1 = BLOWER_BOTTOM_Z + BLOWER_SIZE[1] - 10.0
    wall = 2.4
    lip = 1.5
    back_y = (column.blower[1], column.back_y)
    body_y = (column.blower[0] - lip, column.back_y)
    outer = box((x0 - wall, x1 + wall), body_y, (z0 - wall, z1))
    inner = box((x0, x1), (column.blower[0], column.blower[1]), (z0, z1))
    front_window = box((x0 + 2.5, x1 - 2.5), (column.blower[0] - lip, column.blower[0]), (z0 + 2.5, z1))    # 2.5 mm lips print without support
    holder = outer.cut(inner).cut(front_window)
    tabs = [box((hx - 4.5, hx + 4.5), back_y, (hz - 4.5, hz + 4.5)) for hx, hz in blower_holder_screws()]
    holder = holder.fuse(tabs)
    x, z = blower_intake_centre(column)
    holder = holder.cut(cylinder_y(BLOWER_INTAKE_DIAMETER, back_y, x, z))
    holder = cut_all(holder, [cylinder_y(fit.M3_CLEARANCE_HOLE, back_y, hx, hz) for hx, hz in blower_holder_screws()])
    return holder.removeSplitter()


def cradle_y(column):
    slot_y = (column.pcb_front_y - 0.15, column.pcb_back_y + 0.15)
    return (slot_y[0] - CRADLE_JAW, slot_y[1] + CRADLE_JAW)


def cradle(column):
    """Bar in the board's plane that the PCB's far edge stands in. The slot skips the far-end
    bracket, which drops into a pocket."""
    half = INTERIOR_HALF_WIDTH
    slot_y = (column.pcb_front_y - 0.15, column.pcb_back_y + 0.15)
    jaws_y = cradle_y(column)
    foot_y = (jaws_y[0] - 8.0, jaws_y[1] + 8.0)
    bar = box((-half, half), jaws_y, (0.0, PCB_FAR_EDGE_Z))
    foot = box((-half, half), foot_y, (0.0, 6.0))
    slot_x = (board_x(-68.0), board_x(22.0))
    jaws = box(slot_x, jaws_y, (PCB_FAR_EDGE_Z, PCB_FAR_EDGE_Z + CRADLE_SLOT_DEPTH))
    shape = bar.fuse([foot, jaws])
    shape = shape.cut(box(slot_x, slot_y, (PCB_FAR_EDGE_Z, PCB_FAR_EDGE_Z + CRADLE_SLOT_DEPTH)))
    pocket = box((board_x(FAR_BRACKET_LOCAL_Y[0] - 8.0), board_x(PCB_TOP_EDGE_LOCAL_Y[1] + 3.0)),
                 (column.pcb_front_y - 20.0, column.pcb_back_y + 4.0), (22.0, PCB_FAR_EDGE_Z))
    shape = shape.cut(pocket)
    y = sum(jaws_y) / 2
    return add_wall_blocks(shape, (y - WALL_BLOCK[1] / 2, y + WALL_BLOCK[1] / 2), CRADLE_BLOCK_Z, nut_from=+1)


def crossbar_y(column):
    return (column.pcb_back_y + 3.0, column.pcb_back_y + 11.0)    # clears the I/O bracket strip (K3: 2)


def crossbar(column):
    """Bar behind the board's I/O end with a fork round each long PCB edge; keeps the top upright. A lip
    on each fork sits just over the PCB's top edge so a tipped case can't lift the board out of its
    cradle; unscrew the crossbar to lift a board out."""
    half = INTERIOR_HALF_WIDTH
    bar_y = crossbar_y(column)
    bar = box((-half, half), bar_y, CROSSBAR_Z)
    forks = []
    for edge_local_y, outward in ((PCB_TOP_EDGE_LOCAL_Y[0], -1), (PCB_TOP_EDGE_LOCAL_Y[1], +1)):
        edge_x = board_x(edge_local_y)
        # fork body: from 6 mm outside the edge to 3 mm over the PCB, front jaw to the bar
        x_range = sorted((edge_x + outward * 6.0, edge_x - outward * CRADLE_JAW))
        fork = box(x_range, (column.pcb_front_y - CRADLE_JAW, bar_y[0]), CROSSBAR_Z)
        slot = box(sorted((edge_x + outward * 3.0, edge_x - outward * CRADLE_JAW)),
                   (column.pcb_front_y - 0.15, column.pcb_back_y + 0.15), CROSSBAR_Z)
        forks.append(fork.cut(slot))
        lip_z = (PCB_TOP_EDGE_Z + 0.5, PCB_TOP_EDGE_Z + 2.5)
        lip_y = (column.pcb_front_y - CRADLE_JAW, bar_y[0])
        riser = box(sorted((edge_x + outward * 0.5, edge_x + outward * 6.0)), lip_y, (CROSSBAR_Z[1], lip_z[1]))
        lip = box(sorted((edge_x - outward * HOLD_DOWN_OVERLAP, edge_x + outward * 6.0)), lip_y, lip_z)
        forks += [riser, lip]
    shape = bar.fuse(forks)
    y = sum(bar_y) / 2
    return add_wall_blocks(shape, (y - WALL_BLOCK[1] / 2, y + WALL_BLOCK[1] / 2), sum(CROSSBAR_Z) / 2, nut_from=+1,
                           height=CROSSBAR_Z[1] - CROSSBAR_Z[0])     # flush with the bar, which prints on its bottom


def gap_shim():
    """FIN_GAP-thick shim with a finger tab: slipped between a fan and the heatsink fins while the
    board's cradle and crossbar are tightened, then pulled out."""
    blade = box((0.0, GAP_SHIM[0]), (0.0, GAP_SHIM[1]), (0.0, FIN_GAP))
    tab = box((GAP_SHIM[0], GAP_SHIM[0] + 15.0), (0.0, GAP_SHIM[1]), (0.0, 4.0))
    return blade.fuse(tab).removeSplitter()


def back_plate_halves():
    top_z = ROOF_Z[0] + LID_GROOVE_DEPTH - PLATE_TOP_PLAY      # into the roof's groove
    return divider_halves(BACK_PLATE_Y, blower_intake_centre(COLUMNS[-1]), top_z, BACK_PLATE_SPLIT_Z)


def back_plate():
    return Part.makeCompound(back_plate_halves())


ROOF_Y = (UPRIGHT_DEPTH, CASE_DEPTH - UPRIGHT_DEPTH)
ROOF_SPLIT_Y = sum(ROOF_Y) / 2


def roof_block_ys():
    """Two wall blocks per roof tile, near its ends; the last clears the back plate."""
    return [ROOF_Y[0] + 15.0, ROOF_SPLIT_Y - 15.0, ROOF_SPLIT_Y + 15.0,
            BACK_PLATE_Y[1] + RAIL_REACH + WALL_BLOCK[1] / 2 + 1.0]


def roof_tiles():
    """Roof between the frames, in a front and a back tile: grille over the hot zones, solid over
    the rear plenum. Wall blocks hang below it."""
    half = INTERIOR_HALF_WIDTH
    plate = box((-half, half), ROOF_Y, ROOF_Z)
    slots = []
    x = -half + 14.0
    while x + GRILLE_SLOT <= half - 14.0:
        for y_range in ((ROOF_Y[0] + 6.0, ROOF_SPLIT_Y - 6.0), (ROOF_SPLIT_Y + 6.0, BACK_PLATE_Y[0] - 3.0)):
            slots.append(box((x, x + GRILLE_SLOT), y_range, ROOF_Z))
        x += GRILLE_PITCH
    plate = cut_all(plate, slots)
    plate = plate.cut(top_edge_groove(BACK_PLATE_Y, PLATE_HALF_WIDTH, ROOF_Z[0]))     # holds the back plate down
    tiles = []
    for y_range in ((ROOF_Y[0], ROOF_SPLIT_Y), (ROOF_SPLIT_Y, ROOF_Y[1])):
        tile = plate.common(box((-half, half), y_range, ROOF_Z))
        for y in roof_block_ys():
            if y_range[0] < y < y_range[1]:
                tile = add_wall_blocks(tile, (y - WALL_BLOCK[1] / 2, y + WALL_BLOCK[1] / 2), ROOF_BLOCK_Z, nut_from=+1,
                                       nut_style="pocket")
        tiles.append(tile.removeSplitter())
    return tiles


def roof():
    return Part.makeCompound(roof_tiles())


# ---------------------------------------------------------------------------------------------
# Hardware that is not in the board STEP
# ---------------------------------------------------------------------------------------------
def fan_shapes(column):
    fans = []
    x_range = (HEATSINK_CENTRE_X - FAN_SIZE / 2, HEATSINK_CENTRE_X + FAN_SIZE / 2)
    for fan_bottom, fan_top in fan_zs():
        frame = box(x_range, column.fan, (fan_bottom, fan_top))
        centre_x, centre_z = HEATSINK_CENTRE_X, (fan_bottom + fan_top) / 2
        opening = cylinder_y(FAN_SIZE - 4.0, column.fan, centre_x, centre_z)
        hub = cylinder_y(40.0, column.fan, centre_x, centre_z)
        fans.append(frame.cut(opening).fuse(hub))
    return fans


def blower_shape(column):
    x0 = BLOWER_CENTRE_X - BLOWER_SIZE[0] / 2
    body = box((x0, x0 + BLOWER_SIZE[0]), column.blower, (BLOWER_BOTTOM_Z, BLOWER_BOTTOM_Z + BLOWER_SIZE[1]))
    return body


def blower_outlet_keepout(column):
    """With the intake facing the divider, the outlet is on the -X (power edge) half of the top
    edge: test-fit photo, 2026-10-16."""
    x0 = BLOWER_CENTRE_X - BLOWER_SIZE[0] / 2 + 2.0
    top = BLOWER_BOTTOM_Z + BLOWER_SIZE[1]
    return box((x0, x0 + BLOWER_OUTLET[0]), (column.blower[0] + 1.5, column.blower[0] + 1.5 + BLOWER_OUTLET[1]),
               (top, top + 60.0))


def bracket_shapes_local():
    """EST shapes of the two metal brackets in board-local coordinates (K1-K6 photos)."""
    io_y = (sum(IO_BRACKET_SCREWS_LOCAL_Y) / 2 - 56.4, sum(IO_BRACKET_SCREWS_LOCAL_Y) / 2 + 56.4)   # K1 112.8
    io_strip = box((-153.0, -142.0), (IO_BRACKET_SCREWS_LOCAL_Y[0] - 3.0, IO_BRACKET_SCREWS_LOCAL_Y[1] + 3.0),
                   (-2.0, 0.0))
    io_plate = box((-158.5, -157.5), io_y, (-2.0, PCB_THICKNESS + 27.0))      # K2 27 front, K3 2 back
    far_base = box((138.0, PCB_LOCAL_X[1]), FAR_BRACKET_LOCAL_Y, (PCB_THICKNESS, PCB_THICKNESS + 1.0))
    far_tab = box((PCB_LOCAL_X[1], PCB_LOCAL_X[1] + 1.0), FAR_BRACKET_LOCAL_Y, (PCB_THICKNESS, PCB_THICKNESS + 15.7))
    return Part.makeCompound([io_strip, io_plate]), far_base.fuse(far_tab)


def keepouts_local():
    """Space for cables in board-local coordinates."""
    power_plugs = box((70.0, 134.0), (-72.2 - 21.0, -54.0), (-2.0, PCB_THICKNESS + 10.5))    # C2 21, C4 10.5
    network_adapter = box((-158.5 - 54.0, -158.5), (-47.0, 66.0), (-2.0, PCB_THICKNESS + 27.0))   # C5 54
    return power_plugs, network_adapter


# ---------------------------------------------------------------------------------------------
# The board from the STEP
# ---------------------------------------------------------------------------------------------
def classify_step_part(obj, chain):
    if "PCB" in chain:
        if obj.Label == "SOLID001":
            return "pcb"
        connector_words = ("Port", "RJ45", "DisplayPort", "Power", "Molex", "Pin Header", "M.2", "CR2032")
        return "connectors" if any(word in obj.Label for word in connector_words) else "components"
    if "Heatsink" in chain:          # the stock heatsink (the cut one is "Cut Heatsink Parts")
        return "heatsink"
    if "Backplate" in chain:
        return "backplate"
    return None


def load_board_shapes():
    """{part name: compound} in board-local coordinates."""
    temp_doc = App.newDocument("bc250_step_import")
    Import.insert(BOARD_STEP, temp_doc.Name)
    groups = {}
    for obj in temp_doc.Objects:
        if obj.TypeId != "Part::Feature" or obj.Shape.isNull():
            continue
        chain = []
        parent = obj.getParentGeoFeatureGroup()
        while parent is not None:
            chain.append(parent.Label)
            parent = parent.getParentGeoFeatureGroup()
        part_name = classify_step_part(obj, chain)
        if part_name is None:
            continue
        shape = obj.Shape.copy()
        shape.Placement = obj.getGlobalPlacement()
        if part_name == "heatsink":
            shape.translate(STEP_HEATSINK_OFFSET)
        if part_name == "backplate":
            shape.translate(STEP_BACKPLATE_OFFSET)
        groups.setdefault(part_name, []).append(shape)
    App.closeDocument(temp_doc.Name)
    return {name: Part.makeCompound(shapes) for name, shapes in groups.items()}


def board_placement(column):
    """Board-local -> global: local X -> -Z (I/O end up), local Y -> +X, local Z -> -Y (heatsink
    faces the front)."""
    matrix = App.Matrix(0, 1, 0, POWER_EDGE_SHIFT_X,
                        0, 0, -1, column.board_y_origin,
                        -1, 0, 0, PCB_FAR_EDGE_Z + PCB_LOCAL_X[1],
                        0, 0, 0, 1)
    return App.Placement(matrix)
