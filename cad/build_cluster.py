"""Build the FreeCAD assembly of a 3-node AMD BC-250 cluster case and its separate PSU box.

Run with the FreeCAD GUI so colours are saved with the document:
    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecad.exe" cad\\build_cluster.py
`freecadcmd.exe cad\\build_cluster.py` also works; it produces the same geometry without colours.

Output: bc250_cluster.FCStd in the project root.

Global frame (mm), viewed from the front window:
    X = width   (0 = case centre, + = right)
    Y = depth   (0 = outer face of the front frame, + = towards the back)
    Z = height  (0 = bottom of the frames; the case stands on 30 mm printed risers)

Case: the Tecmojo rack's two aluminium side frames (upright + upright + clear window) are turned
90 degrees and become the FRONT and BACK of the case. Printed side walls, top fascias, a top grille
and a floor join them; the original handles move to the new top.

Thermal layout: three airflow columns one behind the other, one per node. The stock BC-250 fins
run along the board length, so boards stand I/O-end-up and air flows bottom -> top through them:
    Arctic P12 intake (bottom) -> board (cut VRM heatsinks + AIO cold head facing the front,
    stock backplate + cut-out memory heatsink facing the back, blower firing into the memory fins)
    -> radiator with its Teucer fan pulling (top), exhausting through the top grille.

PSU box: separate, as-shallow-as-possible printed box behind the case, with the owner's desk power
supply on its lid. Every board's PCIe edge faces left, so the cables run from the box forward
along a printed channel on the outside of the left wall and enter each column through a slot.
The 4th Arctic blows into that channel, so fresh air also reaches each column at VRM height.
The switch stands on the outside of the right wall, ports forward.

Every object carries a `FitRole` property that check_fit.py uses:
    rack     - structure (frames + printed case + PSU box); nothing may overlap it
    hardware - physical parts; must not overlap each other
    keepout  - space reserved for cables that are not modelled
"""
import os

import FreeCAD as App
import Import
import Mesh
import Part

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_DIR = os.path.join(PROJECT_DIR, "reference")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "bc250_cluster.FCStd")

# ---------------------------------------------------------------------------------------------
# Rack side frames reused as the front and back of the case (Tecmojo spec drawing; the 266 mm
# clear width between side panels was confirmed, which puts the window 7 mm in from the outside).
# Each frame: two uprights (20 wide x 35 deep once turned) with a clear window between them.
# ---------------------------------------------------------------------------------------------
FRAME_WIDTH = 200.0               # the rack's depth becomes the case's width
FRAME_HEIGHT = 469.45
UPRIGHT_WIDTH = 20.0              # EST: was the upright's side flange
UPRIGHT_DEPTH = 35.0              # was the upright's front face (rail holes now face sideways)
WINDOW_OUTER, WINDOW_INNER = 3.0, 7.0      # window position measured in from the frame's outer face
HANDLE_HEIGHT = 33.0
TOP_THICKNESS = 3.0
ROOF_Z = FRAME_HEIGHT - TOP_THICKNESS
FLOOR_Z = 22.0                    # top of the printed floor (same height as the rack's old tray)
FASCIA_BOTTOM_Z = 432.0           # EST: the printed fascias replace the rack's logo plates
RISER_HEIGHT = 30.0               # printed feet: room under the floor for the intakes

# ---------------------------------------------------------------------------------------------
# Printed case: columns run front to back between the two windows.
# ---------------------------------------------------------------------------------------------
WALL = 3.0
DIVIDER = 2.0
COLUMN_PITCH = 123.0              # 120 mm fan/radiator + divider + 0.5 mm clearance each side
SIDE_WALL_INNER_X = FRAME_WIDTH / 2         # side walls bolt onto the uprights' outer rail faces
COLUMN_START_Y = WINDOW_INNER     # inner face of the front window
COLUMN_CENTERS_Y = [COLUMN_START_Y + COLUMN_PITCH * (i + 0.5) for i in range(3)]
CASE_DEPTH = COLUMN_START_Y + 3 * COLUMN_PITCH + WINDOW_INNER    # 386
UPRIGHT_INNER_X = FRAME_WIDTH / 2 - UPRIGHT_WIDTH                 # 80

# ---------------------------------------------------------------------------------------------
# BC-250 board, in the coordinates of BC250_Completeish_V1.step ("board-local"):
#   local X = board length (I/O end at -X), local Y = board width (power connectors at -Y edge),
#   local Z = thickness (PCB 0..1.6, APU on +Z = front, GDDR6 on -Z = back).
# ---------------------------------------------------------------------------------------------
BOARD_STEP = os.path.join(REFERENCE_DIR, "BC250_Completeish_V1.step")
BOARD_LOCAL_X_MAX = 154.6         # far end of the PCB (opposite the I/O)
BOARD_LOCAL_Y_MIN = -72.2         # power-connector edge
BOARD_WIDTH = 144.0
BOARD_POWER_EDGE_X = -66.0        # power edge faces the PSU box (left); plugs end 11 mm from the wall
# The STEP shows the stock backplate exploded 200 mm away along -Y; this puts it back in place.
BACKPLATE_EXPLODE_OFFSET = App.Vector(0, 200.0, 0)
# The cut-out centre section sits on the back. True = on top of the stock backplate (user's build):
# it must drop 2 mm from MandicReally's position, where it replaces the backplate.
MEMORY_HEATSINK_ON_STOCK_BACKPLATE = True
MEMORY_HEATSINK_DROP = -2.0
# Slab = everything attached to one board, in local Z: memory heatsink fins .. top of cold head.
SLAB_LOCAL_Z_MIN = -26.1 + (MEMORY_HEATSINK_DROP if MEMORY_HEATSINK_ON_STOCK_BACKPLATE else 0.0)
SLAB_LOCAL_Z_MAX = 62.0           # APU die top 4.0 + 58 mm Teucer cold head
SLAB_CENTER_LOCAL_Z = (SLAB_LOCAL_Z_MIN + SLAB_LOCAL_Z_MAX) / 2

# NexGen3D mount, front parts only: the backplate + memory heatsink take the back brace's place.
# The Teucer block lists AM4/AM5 and LGA17xx hardware, matching the bracket's AM4/LGA1700 patterns.
NEXGEN_DIR = os.path.join(REFERENCE_DIR, "nexgen3d_aio_mount")
NEXGEN_PARTS = ["AM4 - Generic Bottom.3mf", "AM4 - Generic Top.3mf"]
NEXGEN_PCB_TOP_Z = -1.1           # in the 3MF frame the Bottom part rests on the PCB here

# Teucer AF-120 cold head: 83 x 78.6 x 58 (manual). Lower ring kept narrow to clear the bracket.
PUMP_LENGTH = 83.0                # along local X
PUMP_WIDTH = 78.6                 # along local Y
PUMP_HEIGHT = 58.0
PUMP_BASE_RADIUS = 30.0
PUMP_BASE_HEIGHT = 18.0
FITTING_RADIUS = 7.0
FITTING_LENGTH = 16.0
FITTING_LOCAL_Z = 45.0            # above the rear VRM heatsink (28.1) so tubes run over it
FITTING_SPACING = 30.0            # along local Y; fittings point up (towards the I/O end)
TUBE_RADIUS = 6.0                 # EST: braided FEP tube; the user's tubes are 300 mm long

# ---------------------------------------------------------------------------------------------
# Heights in each column
# ---------------------------------------------------------------------------------------------
FAN_SIZE = 120.0
FAN_THICKNESS = 25.0
INTAKE_FAN_Z = (FLOOR_Z + 0.5, FLOOR_Z + 0.5 + FAN_THICKNESS)
BOARD_BOTTOM_Z = 55.0             # 7.5 mm above the intake fan
RADIATOR_LENGTH = 155.0           # user: 155 x 120; runs across the case (X)
RADIATOR_CORE = 120.0             # along the column (Y)
RADIATOR_THICKNESS = 27.0         # EST: not given yet
RADIATOR_TOP_Z = ROOF_Z - 2.0 - FAN_THICKNESS - 0.5
RADIATOR_Z = (RADIATOR_TOP_Z - RADIATOR_THICKNESS, RADIATOR_TOP_Z)
PORT_X = RADIATOR_LENGTH / 2 - 8.75         # tube ports on the right-hand end tank, pointing down
PORT_OFFSET_Y = 16.0              # ports either side of the tube risers' row
PORT_LENGTH = 8.0
PLENUM_TUBE_Z = 397.0             # tubes cross over to the ports here, just under the port stubs

# ---------------------------------------------------------------------------------------------
# PSU cabling: a printed channel on the outside of the left wall (every board's PCIe edge faces
# left) runs back to the PSU box. The 4th Arctic blows into the channel, so fresh air also
# leaves through each cable slot into its column at front-VRM height.
# ---------------------------------------------------------------------------------------------
CABLE_SLOT_Z = (70.0, 145.0)      # covers the PCIe 8-pin + Micro-Fit plugs (Z 76-140)
CHANNEL_DEPTH = 17.0              # free width inside the channel (X)
CHANNEL_OUTER_X = -(SIDE_WALL_INNER_X + WALL + CHANNEL_DEPTH + WALL)     # -123: outer face of its cover
CHANNEL_Z = (30.0, 150.0)         # tall enough for the 120 mm fan opening
CHANNEL_FRONT_Y = 40.0
CHANNEL_FAN_Y = (COLUMN_START_Y + COLUMN_PITCH * 1.5 - FAN_SIZE / 2,
                 COLUMN_START_Y + COLUMN_PITCH * 1.5 + FAN_SIZE / 2)      # beside node 2

# ---------------------------------------------------------------------------------------------
# PSU box behind the case, as shallow as possible: the PSU stands on its side with its 86 mm
# dimension front-to-back. Fan breathes through the rear wall, modular cables leave on the left
# into the channel, AC socket through the right wall. A desk power supply sits on the lid.
# ---------------------------------------------------------------------------------------------
BOX_GAP = 1.0                     # between the case's back frame and the box
BOX_FRONT_Y = CASE_DEPTH + BOX_GAP
BOX_LEFT_X = CHANNEL_OUTER_X      # flush with the channel cover so the channel runs straight in
CABLE_LANE = 35.0                 # modular-cable bend space left of the PSU
PSU_SIZE_STANDING = (150.0, 86.0, 150.0)   # MSI PRO A1000PL on its side: X x Y x Z, fan facing +Y
PSU_X = (BOX_LEFT_X + WALL + CABLE_LANE, BOX_LEFT_X + WALL + CABLE_LANE + PSU_SIZE_STANDING[0])
BOX_RIGHT_X = PSU_X[1] + WALL     # right wall carries the AC cutout, so the AC plug is outside
PSU_Y = (BOX_FRONT_Y + WALL + 0.5, BOX_FRONT_Y + WALL + 0.5 + PSU_SIZE_STANDING[1])
BOX_REAR_Y = PSU_Y[1] + 3.0 + WALL          # 3 mm between the PSU fan and the rear grille
BOX_FLOOR_Z = -RISER_HEIGHT       # the box stands on the table
PSU_Z = (BOX_FLOOR_Z + WALL + 0.5, BOX_FLOOR_Z + WALL + 0.5 + PSU_SIZE_STANDING[2])
BOX_TOP_Z = CHANNEL_Z[1]          # the channel enters at full height; fan hubs sit on the PSU
DESK_PSU_SIZE = (140.0, 90.0, 40.0)         # user: 90 x 140 footprint; height is an estimate
SWITCH_SIZE = (26.0, 126.0, 209.0)          # TL-SG105-M2 standing on the case's right wall, ports forward

# Colours (r, g, b) 0..1
PCB_GREEN = (0.10, 0.35, 0.18)
COMPONENT_GREY = (0.25, 0.25, 0.27)
CONNECTOR_BLACK = (0.08, 0.08, 0.08)
HEATSINK_ALU = (0.78, 0.78, 0.80)
BACKPLATE_DARK = (0.30, 0.31, 0.33)
FRAME_ALU = (0.80, 0.81, 0.83)
WINDOW_CLEAR = (0.70, 0.80, 0.90)
STEEL_BLACK = (0.12, 0.12, 0.13)
PRINTED_ORANGE = (0.95, 0.45, 0.10)
PRINTED_GREY = (0.45, 0.47, 0.50)
PUMP_BLACK = (0.15, 0.15, 0.17)
FAN_GREY = (0.30, 0.30, 0.32)
BLOWER_BLUE = (0.20, 0.35, 0.60)
RADIATOR_SILVER = (0.55, 0.57, 0.60)
TUBE_BLACK = (0.05, 0.05, 0.05)
KEEPOUT_ORANGE = (1.00, 0.55, 0.00)
SWITCH_BLUE = (0.20, 0.30, 0.45)


# ---------------------------------------------------------------------------------------------
# Small geometry helpers
# ---------------------------------------------------------------------------------------------
def box(x_range, y_range, z_range):
    """Axis-aligned box given (min, max) ranges on each axis."""
    (x0, x1), (y0, y1), (z0, z1) = x_range, y_range, z_range
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0))


def centred_box(centre, size):
    """Box of size (sx, sy, sz) centred on `centre` (x, y, z)."""
    return box(*[(c - s / 2, c + s / 2) for c, s in zip(centre, size)])


def fan_shape(x_range, y_range, z_range):
    """Square axial fan: frame with a round opening, plus a hub. Airflow axis is the thinnest one."""
    frame = box(x_range, y_range, z_range)
    sizes = [hi - lo for lo, hi in (x_range, y_range, z_range)]
    axis_index = sizes.index(min(sizes))
    axis = App.Vector(*[1.0 if i == axis_index else 0.0 for i in range(3)])
    start = App.Vector(*[lo for lo, _ in (x_range, y_range, z_range)])
    centre = App.Vector(*[(lo + hi) / 2 for lo, hi in (x_range, y_range, z_range)])
    centre_on_face = centre + axis * (start.dot(axis) - centre.dot(axis))
    thickness = sizes[axis_index]
    opening = Part.makeCylinder(min(sizes[i] for i in range(3) if i != axis_index) / 2 - 2,
                                thickness, centre_on_face, axis)
    hub = Part.makeCylinder(20.0, thickness, centre_on_face, axis)
    return frame.cut(opening).fuse(hub)


def tube_along(points, radius):
    """Solid tube following a polyline (schematic bends: straight segments + spherical joints)."""
    pieces = []
    for start, end in zip(points, points[1:]):
        direction = end - start
        pieces.append(Part.makeCylinder(radius, direction.Length, start, direction))
    pieces += [Part.makeSphere(radius, joint) for joint in points[1:-1]]
    return pieces[0].multiFuse(pieces[1:]).removeSplitter()


def remove_repeated_points(points):
    """Drop consecutive duplicates (a port can line up with its riser)."""
    kept = [points[0]]
    for point in points[1:]:
        if (point - kept[-1]).Length > 1e-6:
            kept.append(point)
    return kept


def add_feature(doc, container, name, shape, color, role="hardware", transparency=0):
    feature = doc.addObject("Part::Feature", name)
    feature.Shape = shape
    tag_feature(feature, container, color, role, transparency)
    return feature


def add_mesh(doc, container, name, mesh, color):
    feature = doc.addObject("Mesh::Feature", name)
    feature.Mesh = mesh
    tag_feature(feature, container, color, "hardware", 0)
    return feature


def tag_feature(feature, container, color, role, transparency):
    feature.addProperty("App::PropertyString", "FitRole", "Fit", "rack | hardware | keepout")
    feature.FitRole = role
    container.addObject(feature)
    if App.GuiUp:
        feature.ViewObject.ShapeColor = color
        feature.ViewObject.Transparency = transparency


# ---------------------------------------------------------------------------------------------
# Reused rack parts: the two side frames (now front and back) and the two handles
# ---------------------------------------------------------------------------------------------
def build_rack_frames(doc):
    group = doc.addObject("App::Part", "Rack_Frames_Reused")
    half = FRAME_WIDTH / 2
    for name, outer_y, inward in (("Front", 0.0, +1), ("Back", CASE_DEPTH, -1)):
        upright_y = sorted((outer_y, outer_y + inward * UPRIGHT_DEPTH))
        window_y = sorted((outer_y + inward * WINDOW_OUTER, outer_y + inward * WINDOW_INNER))
        for side_name, x_range in (("L", (-half, -UPRIGHT_INNER_X)), ("R", (UPRIGHT_INNER_X, half))):
            add_feature(doc, group, f"{name}Frame_Upright{side_name}",
                        box(x_range, upright_y, (0.0, ROOF_Z)), FRAME_ALU, "rack")
        add_feature(doc, group, f"{name}Frame_Window",
                    box((-UPRIGHT_INNER_X, UPRIGHT_INNER_X), window_y, (0.0, ROOF_Z)),
                    WINDOW_CLEAR, "rack", transparency=80)

    # The original handles, now across the front and back ends of the printed top.
    for name, y_range in (("Front", (10.0, 26.0)), ("Back", (CASE_DEPTH - 26.0, CASE_DEPTH - 10.0))):
        handle = box((-80.0, 80.0), y_range, (FRAME_HEIGHT + HANDLE_HEIGHT - 12, FRAME_HEIGHT + HANDLE_HEIGHT))
        for leg_x in ((-80.0, -65.0), (65.0, 80.0)):
            handle = handle.fuse(box(leg_x, y_range, (FRAME_HEIGHT, FRAME_HEIGHT + HANDLE_HEIGHT)))
        add_feature(doc, group, f"Handle_{name}", handle.removeSplitter(), STEEL_BLACK, "rack")
    return group


# ---------------------------------------------------------------------------------------------
# Printed case parts: side walls, fascias, top grille, floor, dividers, risers, cable slots
# ---------------------------------------------------------------------------------------------
def cable_slot_boxes(wall_x_range):
    """One slot per node in a wall, where that node's PCIe/Micro-Fit plugs sit."""
    slots = []
    for centre_y in COLUMN_CENTERS_Y:
        slots.append(box(wall_x_range, (centre_y - 20.0, centre_y + 30.0), CABLE_SLOT_Z))
    return slots


def build_case(doc):
    group = doc.addObject("App::Part", "Printed_Case")
    half = SIDE_WALL_INNER_X
    full_depth = (0.0, CASE_DEPTH)

    left_x, right_x = (-half - WALL, -half), (half, half + WALL)
    left_wall = box(left_x, full_depth, (0.0, FASCIA_BOTTOM_Z))
    for slot in cable_slot_boxes(left_x):
        left_wall = left_wall.cut(slot)
    add_feature(doc, group, "SideWall_L_CableSlots", left_wall, PRINTED_GREY, "rack", transparency=30)
    add_feature(doc, group, "SideWall_R", box(right_x, full_depth, (0.0, FASCIA_BOTTOM_Z)),
                PRINTED_GREY, "rack", transparency=30)
    for side_name, x_range in (("L", left_x), ("R", right_x)):
        add_feature(doc, group, f"TopFascia_{side_name}", box(x_range, full_depth, (FASCIA_BOTTOM_Z, ROOF_Z)),
                    PRINTED_ORANGE, "rack")

    top = box((-half - WALL, half + WALL), full_depth, (ROOF_Z, FRAME_HEIGHT))
    for centre_y in COLUMN_CENTERS_Y:
        top = top.cut(box((-62.0, 62.0), (centre_y - 58.0, centre_y + 58.0), (ROOF_Z, FRAME_HEIGHT)))
    add_feature(doc, group, "TopGrille", top, PRINTED_GREY, "rack")

    # Full width between the uprights' depth, narrower where it passes between each frame's uprights.
    floor_z = (FLOOR_Z - 4.0, FLOOR_Z)
    floor = box((-half, half), (UPRIGHT_DEPTH, CASE_DEPTH - UPRIGHT_DEPTH), floor_z)
    floor = floor.fuse([box((-UPRIGHT_INNER_X, UPRIGHT_INNER_X), (COLUMN_START_Y, UPRIGHT_DEPTH), floor_z),
                        box((-UPRIGHT_INNER_X, UPRIGHT_INNER_X), (CASE_DEPTH - UPRIGHT_DEPTH,
                                                                   CASE_DEPTH - WINDOW_INNER), floor_z)])
    for centre_y in COLUMN_CENTERS_Y:
        floor = floor.cut(box((-59.0, 59.0), (centre_y - 59.0, centre_y + 59.0), (FLOOR_Z - 4.0, FLOOR_Z)))
    add_feature(doc, group, "Floor_IntakeGrilles", floor, PRINTED_GREY, "rack")

    for index in (1, 2):
        y = COLUMN_START_Y + COLUMN_PITCH * index
        add_feature(doc, group, f"ColumnDivider_{index}",
                    box((-half, half), (y - DIVIDER / 2, y + DIVIDER / 2), (INTAKE_FAN_Z[0], ROOF_Z)),
                    PRINTED_GREY, "rack", transparency=40)

    for x_range in ((-half, -UPRIGHT_INNER_X), (UPRIGHT_INNER_X, half)):
        for y_range in ((0.0, UPRIGHT_DEPTH), (CASE_DEPTH - UPRIGHT_DEPTH, CASE_DEPTH)):
            add_feature(doc, group, f"Riser_{int(x_range[0])}_{int(y_range[0])}",
                        box(x_range, y_range, (-RISER_HEIGHT, 0.0)), PRINTED_GREY, "rack")
    return group


# ---------------------------------------------------------------------------------------------
# BC-250 node
# ---------------------------------------------------------------------------------------------
def classify_pcb_part(label):
    if label == "SOLID001":
        return "pcb"
    connector_words = ("Port", "RJ45", "DisplayPort", "Power", "Molex", "Pin Header", "M.2", "CR2032")
    if any(word in label for word in connector_words):
        return "connectors"
    return "components"


def group_chain(obj):
    labels = []
    parent = obj.getParentGeoFeatureGroup()
    while parent is not None:
        labels.append(parent.Label)
        parent = parent.getParentGeoFeatureGroup()
    return labels


def classify_step_part(obj):
    """Which part of the node a STEP body belongs to, or None for the unused stock heatsink."""
    chain = group_chain(obj)
    if "PCB" in chain:
        return classify_pcb_part(obj.Label)
    if any("Backside Memory" in label for label in chain):
        return "memory_heatsink"
    if any("Front VRM" in label for label in chain):
        return "front_vrm_heatsink"
    if any("Rear VRM" in label for label in chain):
        return "rear_vrm_heatsink"
    if "Backplate" in chain:
        return "backplate"
    return None


def load_board_shapes():
    """Return ({part name: compound}, apu_centre, apu_top_z), all in board-local coords."""
    temp_doc = App.newDocument("bc250_step_import")
    Import.insert(BOARD_STEP, temp_doc.Name)
    groups = {}
    apu_boxes = []
    for obj in temp_doc.Objects:
        if obj.TypeId != "Part::Feature" or obj.Shape.isNull():
            continue
        part_name = classify_step_part(obj)
        if part_name is None:
            continue
        shape = obj.Shape.copy()
        shape.Placement = obj.getGlobalPlacement()
        if part_name == "backplate":
            shape.translate(BACKPLATE_EXPLODE_OFFSET)
        if part_name == "memory_heatsink" and MEMORY_HEATSINK_ON_STOCK_BACKPLATE:
            shape.translate(App.Vector(0, 0, MEMORY_HEATSINK_DROP))
        groups.setdefault(part_name, []).append(shape)
        if obj.Label.startswith("APU"):
            apu_boxes.append(shape.BoundBox)
    App.closeDocument(temp_doc.Name)
    if not MEMORY_HEATSINK_ON_STOCK_BACKPLATE:
        groups.pop("backplate")

    apu_box = apu_boxes[0]
    for other in apu_boxes[1:]:
        apu_box.add(other)
    apu_centre = App.Vector(apu_box.Center.x, apu_box.Center.y, 0)
    return {name: Part.makeCompound(shapes) for name, shapes in groups.items()}, apu_centre, apu_box.ZMax


def load_nexgen_meshes(apu_centre):
    """NexGen mount meshes moved into board-local coords (centred on the APU, seated on the PCB)."""
    meshes = {filename: Mesh.Mesh(os.path.join(NEXGEN_DIR, filename)) for filename in NEXGEN_PARTS}
    bottom_box = meshes[NEXGEN_PARTS[0]].BoundBox
    offset = App.Vector(apu_centre.x - bottom_box.Center.x,
                        apu_centre.y - bottom_box.Center.y,
                        1.6 - NEXGEN_PCB_TOP_Z)
    for mesh in meshes.values():
        mesh.translate(offset.x, offset.y, offset.z)
    return meshes


def board_placement(column_centre_y):
    """Board-local -> global: local X -> -Z (I/O up), local Y -> +X (power edge on the left,
    towards the PSU box), local Z -> -Y (cold head faces the front window).
    The slab is centred in its column."""
    tx = BOARD_POWER_EDGE_X - BOARD_LOCAL_Y_MIN
    ty = column_centre_y + SLAB_CENTER_LOCAL_Z
    tz = BOARD_BOTTOM_Z + BOARD_LOCAL_X_MAX
    matrix = App.Matrix(0, 1, 0, tx,
                        0, 0, -1, ty,
                        -1, 0, 0, tz,
                        0, 0, 0, 1)
    return App.Placement(matrix)


def pump_shapes(apu_centre, die_top_z):
    """Cold head body and its two tube fittings (board-local). Fittings point to the I/O end (up)."""
    base = Part.makeCylinder(PUMP_BASE_RADIUS, PUMP_BASE_HEIGHT,
                             App.Vector(apu_centre.x, apu_centre.y, die_top_z))
    body_bottom = die_top_z + PUMP_BASE_HEIGHT
    body = centred_box((apu_centre.x, apu_centre.y, (body_bottom + die_top_z + PUMP_HEIGHT) / 2),
                       (PUMP_LENGTH, PUMP_WIDTH, die_top_z + PUMP_HEIGHT - body_bottom))
    body = body.makeFillet(8.0, [edge for edge in body.Edges
                                 if abs(edge.Vertexes[0].Z - edge.Vertexes[1].Z) > 1])
    face_x = apu_centre.x - PUMP_LENGTH / 2
    fittings, tips = [], []
    for offset in (-FITTING_SPACING / 2, FITTING_SPACING / 2):
        start = App.Vector(face_x, apu_centre.y + offset, FITTING_LOCAL_Z)
        fittings.append(Part.makeCylinder(FITTING_RADIUS, FITTING_LENGTH, start, App.Vector(-1, 0, 0)))
        tips.append(start + App.Vector(-FITTING_LENGTH, 0, 0))
    return base.fuse(body).removeSplitter(), Part.makeCompound(fittings), tips


def card_guide_shapes():
    """Printed rails gripping both long PCB edges (board-local). The front rail skips the
    PCIe 8-pin + Micro-Fit connectors."""
    def rail(x_range, outer_y, edge_y, inner_y):
        spine = box(x_range, sorted((outer_y, edge_y)), (-1.5, 3.1))
        back_lip = box(x_range, sorted((edge_y, inner_y)), (-1.5, 0.0))
        front_lip = box(x_range, sorted((edge_y, inner_y)), (1.6, 3.1))
        return spine.fuse([back_lip, front_lip]).removeSplitter()

    front_edge, rear_edge = BOARD_LOCAL_Y_MIN - 1.0, BOARD_LOCAL_Y_MIN + BOARD_WIDTH + 1.0
    rails = [rail((-150.0, 65.0), front_edge - 4.8, front_edge, front_edge + 3.0),
             rail((138.0, 152.0), front_edge - 4.8, front_edge, front_edge + 3.0),
             rail((-150.0, 152.0), rear_edge + 4.8, rear_edge, rear_edge - 3.0)]
    return Part.makeCompound(rails)


def build_node(doc, index, board_shapes, apu_centre, die_top_z, nexgen_meshes):
    name = f"Node{index + 1}"
    column_y = COLUMN_CENTERS_Y[index]
    node = doc.addObject("App::Part", name)
    board = doc.addObject("App::Part", f"{name}_Board")
    node.addObject(board)
    board.Placement = board_placement(column_y)

    add_feature(doc, board, f"{name}_PCB", board_shapes["pcb"].copy(), PCB_GREEN)
    add_feature(doc, board, f"{name}_Components", board_shapes["components"].copy(), COMPONENT_GREY)
    add_feature(doc, board, f"{name}_Connectors", board_shapes["connectors"].copy(), CONNECTOR_BLACK)
    if "backplate" in board_shapes:
        add_feature(doc, board, f"{name}_StockBackplate", board_shapes["backplate"].copy(), BACKPLATE_DARK)
    add_feature(doc, board, f"{name}_MemoryHeatsink_CutCentre", board_shapes["memory_heatsink"].copy(), HEATSINK_ALU)
    add_feature(doc, board, f"{name}_VRMHeatsink_Front", board_shapes["front_vrm_heatsink"].copy(), HEATSINK_ALU)
    add_feature(doc, board, f"{name}_VRMHeatsink_Rear", board_shapes["rear_vrm_heatsink"].copy(), HEATSINK_ALU)
    for filename, mesh in nexgen_meshes.items():
        part_name = filename.replace(".3mf", "").replace(" - ", "_").replace(" ", "")
        add_mesh(doc, board, f"{name}_NexGen_{part_name}", mesh.copy(), PRINTED_ORANGE)

    pump, fittings, fitting_tips = pump_shapes(apu_centre, die_top_z)
    add_feature(doc, board, f"{name}_TeucerPump", pump, PUMP_BLACK)
    add_feature(doc, board, f"{name}_PumpFittings", fittings, STEEL_BLACK)

    # BB7515 blower on the back, below the memory heatsink, firing up into its fins.
    add_feature(doc, board, f"{name}_MemoryBlower", box((79.0, 154.0), (-37.0, 38.0), (-20.0, -5.0)), BLOWER_BLUE)
    add_feature(doc, board, f"{name}_CardGuides", card_guide_shapes(), PRINTED_ORANGE)

    # USB 2.5G dongle: plug in the upper USB 3.0 port, body lying beside it above the board on the
    # power-edge side, away from the tubes.
    add_feature(doc, board, f"{name}_USBPlug", box((-185.0, -157.2), (-13.0, 3.0), (9.5, 17.5)), CONNECTOR_BLACK)
    add_feature(doc, board, f"{name}_USB25GDongle", box((-183.0, -166.0), (-75.0, -15.0), (2.0, 28.0)), CONNECTOR_BLACK)
    add_feature(doc, board, f"{name}_KO_PowerPlugs",
                box((70.0, 134.0), (BOARD_LOCAL_Y_MIN - 23.0, BOARD_LOCAL_Y_MIN), (-2.0, 14.0)),
                KEEPOUT_ORANGE, "keepout", transparency=70)

    # Column hardware in global coordinates.
    fan_y = (column_y - FAN_SIZE / 2, column_y + FAN_SIZE / 2)
    add_feature(doc, node, f"{name}_IntakeFan_ArcticP12",
                fan_shape((-FAN_SIZE / 2, FAN_SIZE / 2), fan_y, INTAKE_FAN_Z), FAN_GREY)
    radiator_y = (column_y - RADIATOR_CORE / 2, column_y + RADIATOR_CORE / 2)
    add_feature(doc, node, f"{name}_Radiator",
                box((-RADIATOR_LENGTH / 2, RADIATOR_LENGTH / 2), radiator_y, RADIATOR_Z), RADIATOR_SILVER)
    add_feature(doc, node, f"{name}_RadiatorFan_Teucer",
                fan_shape((-FAN_SIZE / 2, FAN_SIZE / 2), fan_y,
                          (RADIATOR_Z[1] + 0.5, RADIATOR_Z[1] + 0.5 + FAN_THICKNESS)), FAN_GREY)

    # The two fittings sit side by side across the case (X). The fitting nearer the port side
    # feeds the front port; the other steps back first, so their runs never cross.
    tips = sorted((board.Placement.multVec(tip) for tip in fitting_tips), key=lambda v: v.x, reverse=True)
    port_bottom_z = RADIATOR_Z[0] - PORT_LENGTH
    ports = [App.Vector(PORT_X, tips[0].y - PORT_OFFSET_Y, port_bottom_z),
             App.Vector(PORT_X, tips[0].y + PORT_OFFSET_Y, port_bottom_z)]
    add_feature(doc, node, f"{name}_RadiatorPorts",
                Part.makeCompound([Part.makeCylinder(TUBE_RADIUS, PORT_LENGTH, p, App.Vector(0, 0, 1)) for p in ports]),
                STEEL_BLACK)
    for tube_index, (tip, port) in enumerate(zip(tips, ports)):
        route = remove_repeated_points([tip,
                                        App.Vector(tip.x, tip.y, PLENUM_TUBE_Z),
                                        App.Vector(tip.x, port.y, PLENUM_TUBE_Z),
                                        App.Vector(port.x, port.y, PLENUM_TUBE_Z),
                                        port])
        feature = add_feature(doc, node, f"{name}_Tube_{tube_index + 1}", tube_along(route, TUBE_RADIUS), TUBE_BLACK)
        feature.addProperty("App::PropertyLength", "PathLength", "Fit", "Centre-line length of the tube")
        feature.PathLength = sum((b - a).Length for a, b in zip(route, route[1:]))
    return node


# ---------------------------------------------------------------------------------------------
# Cable channel on the left wall, with the 4th Arctic blowing into it
# ---------------------------------------------------------------------------------------------
CHANNEL_INNER_X = (CHANNEL_OUTER_X + WALL, -SIDE_WALL_INNER_X - WALL)      # free space inside


def build_cable_channel(doc):
    group = doc.addObject("App::Part", "Cable_Channel")
    shell_z = (CHANNEL_Z[0] - WALL, CHANNEL_Z[1] + WALL)
    channel_y = (CHANNEL_FRONT_Y, BOX_FRONT_Y)

    cover = box((CHANNEL_OUTER_X, CHANNEL_OUTER_X + WALL), (CHANNEL_FRONT_Y - WALL, BOX_FRONT_Y), shell_z)
    fan_centre = App.Vector(CHANNEL_OUTER_X, sum(CHANNEL_FAN_Y) / 2, sum(CHANNEL_Z) / 2)
    cover = cover.cut(Part.makeCylinder(FAN_SIZE / 2 - 2.0, WALL, fan_centre, App.Vector(1, 0, 0)))
    add_feature(doc, group, "ChannelCover_FanOpening", cover, PRINTED_ORANGE, "rack", transparency=30)
    caps = [box(CHANNEL_INNER_X, channel_y, (shell_z[0], CHANNEL_Z[0])),
            box(CHANNEL_INNER_X, channel_y, (CHANNEL_Z[1], shell_z[1])),
            box(CHANNEL_INNER_X, (CHANNEL_FRONT_Y - WALL, CHANNEL_FRONT_Y), shell_z)]
    add_feature(doc, group, "ChannelCaps", Part.makeCompound(caps), PRINTED_ORANGE, "rack")

    fan_x = (CHANNEL_OUTER_X - 0.5 - FAN_THICKNESS, CHANNEL_OUTER_X - 0.5)
    add_feature(doc, group, "ChannelFan_ArcticP12", fan_shape(fan_x, CHANNEL_FAN_Y, CHANNEL_Z), FAN_GREY)
    return group


# ---------------------------------------------------------------------------------------------
# PSU box behind the case, with the desk power supply on its lid
# ---------------------------------------------------------------------------------------------
def build_psu_box(doc):
    group = doc.addObject("App::Part", "PSU_Box")
    wall_z = (BOX_FLOOR_Z, BOX_TOP_Z)
    box_y = (BOX_FRONT_Y, BOX_REAR_Y)
    between_x = (BOX_LEFT_X + WALL, BOX_RIGHT_X - WALL)
    between_y = (BOX_FRONT_Y + WALL, BOX_REAR_Y - WALL)
    ac_y = (PSU_Y[0] + 28.0, PSU_Y[0] + 58.0)
    ac_z = (PSU_Z[1] - 40.0, PSU_Z[1] - 10.0)

    add_feature(doc, group, "PSUBox_LeftWall", box((BOX_LEFT_X, BOX_LEFT_X + WALL), box_y, wall_z),
                PRINTED_GREY, "rack", transparency=30)
    right_wall = box((BOX_RIGHT_X - WALL, BOX_RIGHT_X), box_y, wall_z)
    right_wall = right_wall.cut(box((BOX_RIGHT_X - WALL, BOX_RIGHT_X), ac_y, ac_z))
    add_feature(doc, group, "PSUBox_RightWall_ACCutout", right_wall, PRINTED_GREY, "rack", transparency=30)
    front_wall = box(between_x, (BOX_FRONT_Y, BOX_FRONT_Y + WALL), wall_z)
    front_wall = front_wall.cut(box(CHANNEL_INNER_X, (BOX_FRONT_Y, BOX_FRONT_Y + WALL), CHANNEL_Z))
    add_feature(doc, group, "PSUBox_FrontWall_ChannelOpening", front_wall, PRINTED_GREY, "rack", transparency=30)
    rear_wall = box(between_x, (BOX_REAR_Y - WALL, BOX_REAR_Y), wall_z)
    psu_fan_centre = App.Vector(sum(PSU_X) / 2, BOX_REAR_Y - WALL, sum(PSU_Z) / 2)
    rear_wall = rear_wall.cut(Part.makeCylinder(65.0, WALL, psu_fan_centre, App.Vector(0, 1, 0)))
    add_feature(doc, group, "PSUBox_RearWall_FanGrille", rear_wall, PRINTED_GREY, "rack", transparency=30)
    add_feature(doc, group, "PSUBox_Floor", box(between_x, between_y, (BOX_FLOOR_Z, BOX_FLOOR_Z + WALL)),
                PRINTED_GREY, "rack")
    add_feature(doc, group, "PSUBox_Lid", box((BOX_LEFT_X, BOX_RIGHT_X), box_y, (BOX_TOP_Z, BOX_TOP_Z + WALL)),
                PRINTED_GREY, "rack", transparency=30)

    psu = box(PSU_X, PSU_Y, PSU_Z)
    ac_inlet = box((PSU_X[1], PSU_X[1] + 2.0), ac_y, ac_z)
    add_feature(doc, group, "PSU_MSI_A1000PL", psu.fuse(ac_inlet).removeSplitter(), STEEL_BLACK)
    add_feature(doc, group, "KO_PSU_ModularCables",
                box((PSU_X[0] - 26.0, PSU_X[0]), (PSU_Y[0] + 3, PSU_Y[1] - 3), (PSU_Z[0] + 3, PSU_Z[1] - 3)),
                KEEPOUT_ORANGE, "keepout", transparency=70)
    add_feature(doc, group, "KO_PSU_ACCord", box((PSU_X[1] + 2.0, PSU_X[1] + 40.0), ac_y, ac_z),
                KEEPOUT_ORANGE, "keepout", transparency=70)

    hub_z = (PSU_Z[1] + 0.5, PSU_Z[1] + 12.5)
    for index, y_offset in enumerate((5.0, 35.0), start=1):
        add_feature(doc, group, f"PWMFanHub_{index}",
                    box((PSU_X[0] + 5.0, PSU_X[0] + 85.0), (PSU_Y[0] + y_offset, PSU_Y[0] + y_offset + 25.0), hub_z),
                    PCB_GREEN)

    desk_x = ((BOX_LEFT_X + BOX_RIGHT_X - DESK_PSU_SIZE[0]) / 2, (BOX_LEFT_X + BOX_RIGHT_X + DESK_PSU_SIZE[0]) / 2)
    desk_y = ((BOX_FRONT_Y + BOX_REAR_Y - DESK_PSU_SIZE[1]) / 2, (BOX_FRONT_Y + BOX_REAR_Y + DESK_PSU_SIZE[1]) / 2)
    lid_top = BOX_TOP_Z + WALL
    add_feature(doc, group, "DeskPowerSupply_OnLid", box(desk_x, desk_y, (lid_top, lid_top + DESK_PSU_SIZE[2])),
                SWITCH_BLUE)
    return group


def build_switch(doc):
    """TL-SG105-M2 standing on the outside of the case's right wall, ports facing forward."""
    group = doc.addObject("App::Part", "Network")
    x0 = SIDE_WALL_INNER_X + WALL + 0.5
    add_feature(doc, group, "Switch_TL-SG105-M2",
                box((x0, x0 + SWITCH_SIZE[0]), (15.0, 15.0 + SWITCH_SIZE[1]), (150.0, 150.0 + SWITCH_SIZE[2])),
                SWITCH_BLUE)
    return group


# ---------------------------------------------------------------------------------------------
def main():
    if App.GuiUp:
        import FreeCADGui
    for open_doc in list(App.listDocuments().values()):
        if open_doc.FileName == OUTPUT_PATH:
            App.closeDocument(open_doc.Name)

    board_shapes, apu_centre, die_top_z = load_board_shapes()
    nexgen_meshes = load_nexgen_meshes(apu_centre)

    doc = App.newDocument("bc250_cluster")
    build_rack_frames(doc)
    build_case(doc)
    for index in range(3):
        build_node(doc, index, board_shapes, apu_centre, die_top_z, nexgen_meshes)
    build_cable_channel(doc)
    build_psu_box(doc)
    build_switch(doc)
    doc.recompute()
    doc.saveAs(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH} with {len(doc.Objects)} objects")
    if App.GuiUp:
        FreeCADGui.SendMsgToActiveView("ViewFit")
        FreeCADGui.activeDocument().activeView().viewIsometric()
    # Unattended builds (e.g. from a terminal) set this to close FreeCAD when done.
    if os.environ.get("BC250_EXIT_AFTER_BUILD"):
        os._exit(0)


main()
