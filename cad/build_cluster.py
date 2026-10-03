"""Build the FreeCAD assembly of a 3-node AMD BC-250 cluster in a Tecmojo 9U 10-inch rack.

Run with the FreeCAD GUI so colours are saved with the document:
    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecad.exe" cad\\build_cluster.py
`freecadcmd.exe cad\\build_cluster.py` also works; it produces the same geometry without colours.

Output: bc250_cluster.FCStd in the project root.

Global frame (mm), viewed from the front of the rack:
    X = width   (0 = rack centre, + = right)
    Y = depth   (0 = front face of the frame, + = towards the back)
    Z = height  (0 = bottom of the frame)

Layout (chosen with the user): three boards stand vertically, I/O end up, side by side across
the width; the PSU lies on the floor under them; the three radiators hang outside the rear rails.

Every object carries a `FitRole` property that check_fit.py uses:
    rack     - rack structure; nothing may overlap it
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
# Rack: Tecmojo 9U 10" mini rack (spec drawing) - values marked EST must be measured.
# ---------------------------------------------------------------------------------------------
FRAME_WIDTH = 280.0
FRAME_DEPTH = 200.0
FRAME_HEIGHT = 469.45
HANDLE_HEIGHT = 33.0              # 502.45 overall height minus the frame
UPRIGHT_INNER_X = 105.0           # 210 mm clear opening between the uprights
UPRIGHT_DEPTH = 20.0              # EST: front-to-back depth of each U-channel upright
SIDE_PANEL_INNER_X = 133.0        # EST: inner face of the acrylic side panels (266 mm clear)
SIDE_PANEL_THICKNESS = 4.0        # EST
TOP_PANEL_THICKNESS = 3.0
FLOOR_Z = 22.0                    # EST: top of the bottom tray
TOP_FASCIA_BOTTOM_Z = 432.0       # EST: the logo plate above the 9U rail zone
TEN_INCH_PANEL_WIDTH = 254.0      # standard 10" rack panel / ear width
ROOF_Z = FRAME_HEIGHT - TOP_PANEL_THICKNESS

# ---------------------------------------------------------------------------------------------
# BC-250 board, in the coordinates of BC250_Completeish_V1.step ("board-local"):
#   local X = board length (I/O end at -X), local Y = board width (power connectors at -Y edge),
#   local Z = thickness (PCB 0..1.6, APU and connectors on +Z, the "top side").
# ---------------------------------------------------------------------------------------------
BOARD_STEP = os.path.join(REFERENCE_DIR, "BC250_Completeish_V1.step")
# Only the bare board is used. The STEP also has the stock heatsink, its backplate and a
# "Cut Heatsink Parts" mod; all of these are replaced by the AIO + NexGen back brace.
BOARD_STEP_GROUP = "PCB"
BOARD_LOCAL_X_MAX = 154.6         # far end of the PCB (opposite the I/O)
BOARD_LOCAL_Y_MIN = -72.2         # power-connector edge
BOARD_WIDTH = 144.0
# Thickness of one board "slab" in local Z: from the bolt heads under the NexGen back brace
# to the top of the Teucer cold head (APU die top 4.0 + 58 mm cold head).
SLAB_LOCAL_Z_MIN = -14.0
SLAB_LOCAL_Z_MAX = 62.0

# NexGen3D mount (3MF frame): its Bottom part rests on the PCB top at Z = -1.1, which is
# local Z = 1.6. The mount is centred on the APU; its exact hole alignment is not modelled.
NEXGEN_DIR = os.path.join(REFERENCE_DIR, "nexgen3d_aio_mount")
NEXGEN_PARTS = ["AM4 - Generic Bottom.3mf", "AM4 - Generic Top.3mf", "Back Brace.3mf"]
NEXGEN_PCB_TOP_Z = -1.1

# Teucer AF-120 cold head: 83 x 78.6 x 58 (manual). Lower ring kept narrow to clear the bracket.
PUMP_LENGTH = 83.0                # along local X
PUMP_WIDTH = 78.6                 # along local Y
PUMP_HEIGHT = 58.0
PUMP_BASE_RADIUS = 30.0
PUMP_BASE_HEIGHT = 18.0
FITTING_RADIUS = 7.0
FITTING_LENGTH = 16.0
FITTING_LOCAL_Z = 30.0            # low on the cold head (just above the bracket) so the outer
                                  # nodes' tubes pass inside the 210 mm rear opening
FITTING_SPACING = 36.0            # between the two tube fittings, along local X
TUBE_RADIUS = 6.0                 # EST: braided FEP tube

# ---------------------------------------------------------------------------------------------
# Placement of the three boards.
# ---------------------------------------------------------------------------------------------
PSU_SIZE = (150.0, 150.0, 86.0)   # MSI PRO A1000PL: W x D x H
CARD_SHELF_THICKNESS = 3.0
BOARD_BOTTOM_Z = FLOOR_Z + PSU_SIZE[2] + 4.0          # 4 mm above the PSU: shelf + clearance
BOARD_FRONT_Y = 32.0              # leaves ~25 mm in front for the PCIe/Micro-Fit plugs
WALL_GAP = 4.0
# (name, pump side, slab min X). pump side +1: top side faces +X and power edge is at the front.
# pump side -1 is the same board rotated 180 deg about vertical: top faces -X, power edge at the back.
BOARD_LAYOUT = [
    ("Node1_Left", -1, -SIDE_PANEL_INNER_X + WALL_GAP),
    ("Node2_Middle", +1, -38.0),
    ("Node3_Right", +1, SIDE_PANEL_INNER_X - WALL_GAP - (SLAB_LOCAL_Z_MAX - SLAB_LOCAL_Z_MIN)),
]

# ---------------------------------------------------------------------------------------------
# Rear cooling: radiators outside the rear rails, Arctic P12 exhaust fans behind them.
# ---------------------------------------------------------------------------------------------
RADIATOR_CORE = 120.0
RADIATOR_TANK = 17.5              # EST: end tank length (155 mm overall)
RADIATOR_THICKNESS = 27.0
RADIATOR_FRONT_Y = 206.0          # 6 mm behind the frame for the printed mounting plate
RADIATOR_PLATE_Y = (200.5, 204.5)
RADIATOR_BOTTOMS_Z = [96.0, 220.0, 344.0]   # bottom, middle, top radiator
PORT_OFFSET_X = 68.0              # tube ports on the end tank, facing the rack
PORT_SPACING_Z = 50.0
FAN_SIZE = 120.0
FAN_THICKNESS = 25.0
# Tubes run straight back from the fittings to a vertical routing plane between the rear
# uprights, then: across to their own X "lane" -> up/down to the port height -> across to the
# port -> back into the port. Lanes are ordered so that no tube's horizontal leg crosses
# another tube's vertical run.
TUBE_PLANE_Y = 190.0
# node: (radiator index into RADIATOR_BOTTOMS_Z, end tank side -1 left / +1 right,
#        (lane X for the lower tube, lane X for the upper tube))
TUBE_ROUTES = {
    "Node1_Left": (2, -1, (-82.0, -97.0)),
    "Node2_Middle": (1, -1, (-54.0, -40.0)),
    "Node3_Right": (0, +1, (97.0, 82.0)),
}

# Colours (r, g, b) 0..1
PCB_GREEN = (0.10, 0.35, 0.18)
COMPONENT_GREY = (0.25, 0.25, 0.27)
CONNECTOR_BLACK = (0.08, 0.08, 0.08)
RACK_WHITE = (0.92, 0.92, 0.90)
ACRYLIC_SMOKE = (0.35, 0.35, 0.38)
STEEL_BLACK = (0.12, 0.12, 0.13)
PRINTED_ORANGE = (0.95, 0.45, 0.10)
PUMP_BLACK = (0.15, 0.15, 0.17)
FAN_GREY = (0.30, 0.30, 0.32)
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
    """Drop consecutive duplicates (a lane can coincide with the fitting's own X)."""
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
# Rack
# ---------------------------------------------------------------------------------------------
def build_rack(doc):
    rack = doc.addObject("App::Part", "Rack_Tecmojo_9U")
    half_width = FRAME_WIDTH / 2
    for side_name, side in (("L", -1), ("R", +1)):
        x_range = sorted((side * UPRIGHT_INNER_X, side * half_width))
        for end_name, y_range in (("Front", (0.0, UPRIGHT_DEPTH)),
                                  ("Rear", (FRAME_DEPTH - UPRIGHT_DEPTH, FRAME_DEPTH))):
            add_feature(doc, rack, f"Upright_{end_name}{side_name}",
                        box(x_range, y_range, (0.0, ROOF_Z)), RACK_WHITE, "rack")
        panel_x = sorted((side * SIDE_PANEL_INNER_X, side * (SIDE_PANEL_INNER_X + SIDE_PANEL_THICKNESS)))
        add_feature(doc, rack, f"SidePanel_{side_name}",
                    box(panel_x, (UPRIGHT_DEPTH, FRAME_DEPTH - UPRIGHT_DEPTH), (0.0, ROOF_Z)),
                    ACRYLIC_SMOKE, "rack", transparency=75)
        handle_x = sorted((side * 117.0, side * 133.0))
        handle = box(handle_x, (20.0, 180.0), (FRAME_HEIGHT + HANDLE_HEIGHT - 12, FRAME_HEIGHT + HANDLE_HEIGHT))
        for leg_y in ((20.0, 35.0), (165.0, 180.0)):
            handle = handle.fuse(box(handle_x, leg_y, (FRAME_HEIGHT, FRAME_HEIGHT + HANDLE_HEIGHT)))
        add_feature(doc, rack, f"Handle_{side_name}", handle.removeSplitter(), STEEL_BLACK, "rack")

    add_feature(doc, rack, "TopPanel",
                box((-half_width, half_width), (0.0, FRAME_DEPTH), (ROOF_Z, FRAME_HEIGHT)), STEEL_BLACK, "rack")
    add_feature(doc, rack, "TopFascia",
                box((-UPRIGHT_INNER_X, UPRIGHT_INNER_X), (0.0, 2.0), (TOP_FASCIA_BOTTOM_Z, ROOF_Z)),
                RACK_WHITE, "rack")
    add_feature(doc, rack, "BottomTray",
                box((-SIDE_PANEL_INNER_X, SIDE_PANEL_INNER_X), (0.0, FRAME_DEPTH), (FLOOR_Z - 4, FLOOR_Z)),
                STEEL_BLACK, "rack")
    return rack


# ---------------------------------------------------------------------------------------------
# BC-250 node: board + NexGen mount + Teucer cold head + VRM blower + USB 2.5G dongle
# ---------------------------------------------------------------------------------------------
def classify_board_part(label):
    if label == "SOLID001":
        return "pcb"
    connector_words = ("Port", "RJ45", "DisplayPort", "Power", "Molex", "Pin Header", "M.2", "CR2032")
    if any(word in label for word in connector_words):
        return "connectors"
    return "components"


def is_in_board_group(obj):
    parent = obj.getParentGeoFeatureGroup()
    while parent is not None:
        if parent.Label == BOARD_STEP_GROUP:
            return True
        parent = parent.getParentGeoFeatureGroup()
    return False


def load_board_shapes():
    """Return ({pcb|connectors|components: compound}, apu_centre, apu_top_z) in board-local coords."""
    temp_doc = App.newDocument("bc250_step_import")
    Import.insert(BOARD_STEP, temp_doc.Name)
    groups = {"pcb": [], "connectors": [], "components": []}
    apu_boxes = []
    for obj in temp_doc.Objects:
        if obj.TypeId != "Part::Feature" or obj.Shape.isNull() or not is_in_board_group(obj):
            continue
        shape = obj.Shape.copy()
        shape.Placement = obj.getGlobalPlacement()
        groups[classify_board_part(obj.Label)].append(shape)
        if obj.Label.startswith("APU"):
            apu_boxes.append(shape.BoundBox)
    App.closeDocument(temp_doc.Name)

    apu_box = apu_boxes[0]
    for other in apu_boxes[1:]:
        apu_box.add(other)
    apu_centre = App.Vector(apu_box.Center.x, apu_box.Center.y, 0)
    return {name: Part.makeCompound(shapes) for name, shapes in groups.items()}, apu_centre, apu_box.ZMax


def load_nexgen_meshes(apu_centre):
    """NexGen mount meshes moved into board-local coords (centred on the APU, seated on the PCB)."""
    meshes = {}
    for filename in NEXGEN_PARTS:
        meshes[filename] = Mesh.Mesh(os.path.join(NEXGEN_DIR, filename))
    bottom_box = meshes[NEXGEN_PARTS[0]].BoundBox
    offset = App.Vector(apu_centre.x - bottom_box.Center.x,
                        apu_centre.y - bottom_box.Center.y,
                        1.6 - NEXGEN_PCB_TOP_Z)
    for mesh in meshes.values():
        mesh.translate(offset.x, offset.y, offset.z)
    return meshes


def board_placement(pump_side, slab_min_x):
    """Board-local -> global. local X -> -Z (I/O up), local Y -> pump_side*Y, local Z -> pump_side*X."""
    if pump_side > 0:
        tx = slab_min_x - SLAB_LOCAL_Z_MIN
        ty = BOARD_FRONT_Y - BOARD_LOCAL_Y_MIN
    else:
        tx = slab_min_x + SLAB_LOCAL_Z_MAX
        ty = BOARD_FRONT_Y + BOARD_WIDTH + BOARD_LOCAL_Y_MIN
    tz = BOARD_BOTTOM_Z + BOARD_LOCAL_X_MAX
    s = float(pump_side)
    matrix = App.Matrix(0, 0, s, tx,
                        0, s, 0, ty,
                        -1, 0, 0, tz,
                        0, 0, 0, 1)
    return App.Placement(matrix)


def pump_shapes(apu_centre, die_top_z, pump_side):
    """Cold head body and its two tube fittings (board-local). Fittings point to the rack rear."""
    base = Part.makeCylinder(PUMP_BASE_RADIUS, PUMP_BASE_HEIGHT,
                             App.Vector(apu_centre.x, apu_centre.y, die_top_z))
    body_bottom = die_top_z + PUMP_BASE_HEIGHT
    body = centred_box((apu_centre.x, apu_centre.y, (body_bottom + die_top_z + PUMP_HEIGHT) / 2),
                       (PUMP_LENGTH, PUMP_WIDTH, die_top_z + PUMP_HEIGHT - body_bottom))
    body = body.makeFillet(8.0, [edge for edge in body.Edges
                                 if abs(edge.Vertexes[0].Z - edge.Vertexes[1].Z) > 1])
    # Local +Y is the rack rear for pump_side +1, local -Y for pump_side -1.
    rear_y = pump_side
    side_face_y = apu_centre.y + rear_y * PUMP_WIDTH / 2
    fittings, tips = [], []
    for offset in (-FITTING_SPACING / 2, FITTING_SPACING / 2):
        start = App.Vector(apu_centre.x + offset, side_face_y, FITTING_LOCAL_Z)
        fittings.append(Part.makeCylinder(FITTING_RADIUS, FITTING_LENGTH, start, App.Vector(0, rear_y, 0)))
        tips.append(start + App.Vector(0, rear_y * FITTING_LENGTH, 0))
    return base.fuse(body).removeSplitter(), Part.makeCompound(fittings), tips


def build_node(doc, name, pump_side, slab_min_x, board_shapes, apu_centre, die_top_z, nexgen_meshes):
    node = doc.addObject("App::Part", name)
    node.Placement = board_placement(pump_side, slab_min_x)

    add_feature(doc, node, f"{name}_PCB", board_shapes["pcb"].copy(), PCB_GREEN)
    add_feature(doc, node, f"{name}_Components", board_shapes["components"].copy(), COMPONENT_GREY)
    add_feature(doc, node, f"{name}_Connectors", board_shapes["connectors"].copy(), CONNECTOR_BLACK)
    for filename, mesh in nexgen_meshes.items():
        part_name = filename.replace(".3mf", "").replace(" - ", "_").replace(" ", "")
        add_mesh(doc, node, f"{name}_NexGen_{part_name}", mesh.copy(), PRINTED_ORANGE)

    pump, fittings, fitting_tips = pump_shapes(apu_centre, die_top_z, pump_side)
    add_feature(doc, node, f"{name}_TeucerPump", pump, PUMP_BLACK)
    add_feature(doc, node, f"{name}_PumpFittings", fittings, STEEL_BLACK)

    # BB7515 blower lying over the front VRM area, clear of the mount bracket.
    add_feature(doc, node, f"{name}_VRMBlower", box((76.0, 151.0), (-40.0, 35.0), (16.0, 31.0)), FAN_GREY)

    # USB 2.5G dongle: plug in the upper USB 3.0 port, body lying beside it above the board.
    add_feature(doc, node, f"{name}_USBPlug", box((-185.0, -157.2), (-13.0, 3.0), (9.5, 17.5)), CONNECTOR_BLACK)
    add_feature(doc, node, f"{name}_USB25GDongle", box((-183.0, -166.0), (8.0, 70.0), (2.0, 28.0)), CONNECTOR_BLACK)

    # Space for the PCIe 8-pin + 2x Micro-Fit plugs and their cable bends past the board edge.
    add_feature(doc, node, f"{name}_KO_PowerPlugs",
                box((70.0, 134.0), (BOARD_LOCAL_Y_MIN - 23.0, BOARD_LOCAL_Y_MIN), (-2.0, 14.0)),
                KEEPOUT_ORANGE, "keepout", transparency=70)

    global_tips = [node.Placement.multVec(tip) for tip in fitting_tips]
    return node, global_tips


# ---------------------------------------------------------------------------------------------
# PSU, card shelf, fan hubs, front fan, switch
# ---------------------------------------------------------------------------------------------
def build_power_and_misc(doc):
    group = doc.addObject("App::Part", "Power_And_Network")
    psu_x, psu_y = (-128.0, -128.0 + PSU_SIZE[0]), (30.0, 30.0 + PSU_SIZE[1])
    psu = box(psu_x, psu_y, (FLOOR_Z, FLOOR_Z + PSU_SIZE[2]))
    ac_inlet = box((-100.0, -72.0), (psu_y[1], psu_y[1] + 2.0), (40.0, 68.0))
    add_feature(doc, group, "PSU_MSI_A1000PL", psu.fuse(ac_inlet).removeSplitter(), STEEL_BLACK)
    add_feature(doc, group, "KO_PSU_ModularCables",
                box((-100.0, 15.0), (5.0, psu_y[0]), (FLOOR_Z + 3, FLOOR_Z + PSU_SIZE[2] - 3)),
                KEEPOUT_ORANGE, "keepout", transparency=70)
    add_feature(doc, group, "KO_PSU_ACCord",
                box((-100.0, -72.0), (psu_y[1] + 2.0, 215.0), (40.0, 68.0)),
                KEEPOUT_ORANGE, "keepout", transparency=70)

    shelf_z = (BOARD_BOTTOM_Z - CARD_SHELF_THICKNESS - 0.5, BOARD_BOTTOM_Z - 0.5)
    add_feature(doc, group, "CardShelf_Printed",
                box((-131.0, 131.0), (BOARD_FRONT_Y, BOARD_FRONT_Y + BOARD_WIDTH), shelf_z), PRINTED_ORANGE)

    for index, y_start in enumerate((40.0, 80.0), start=1):
        add_feature(doc, group, f"PWMFanHub_{index}",
                    box((35.0, 115.0), (y_start, y_start + 25.0), (FLOOR_Z, FLOOR_Z + 12.0)), PCB_GREEN)

    # Arctic P12 #4: front intake behind a printed 3U 10" fan panel on the front rails.
    fan_z = (300.0, 300.0 + FAN_SIZE)
    panel = box((-TEN_INCH_PANEL_WIDTH / 2, TEN_INCH_PANEL_WIDTH / 2), (-3.0, 0.0), (fan_z[0] - 6.7, fan_z[1] + 6.65))
    panel = panel.cut(Part.makeCylinder(58.0, 3.0, App.Vector(0, -3.0, sum(fan_z) / 2), App.Vector(0, 1, 0)))
    add_feature(doc, group, "FrontFanPanel_Printed", panel, PRINTED_ORANGE)
    add_feature(doc, group, "Fan_ArcticP12_FrontIntake",
                fan_shape((-60.0, 60.0), (0.5, 0.5 + FAN_THICKNESS), fan_z), FAN_GREY)

    # TL-SG105-M2 on the perforated top panel, between the handles.
    switch = box((-104.5, 104.5), (37.0, 163.0), (FRAME_HEIGHT + 2.0, FRAME_HEIGHT + 28.0))
    add_feature(doc, group, "Switch_TL-SG105-M2", switch, SWITCH_BLUE)
    return group


# ---------------------------------------------------------------------------------------------
# Rear radiators + fans + tubes
# ---------------------------------------------------------------------------------------------
def radiator_port_positions(radiator_index, tank_side):
    bottom = RADIATOR_BOTTOMS_Z[radiator_index]
    centre_z = bottom + RADIATOR_CORE / 2
    x = tank_side * PORT_OFFSET_X
    return [App.Vector(x, RADIATOR_FRONT_Y - 8.0, centre_z + dz)
            for dz in (-PORT_SPACING_Z / 2, PORT_SPACING_Z / 2)]


def build_rear_cooling(doc, fitting_tips_by_node):
    group = doc.addObject("App::Part", "Rear_Cooling")
    half_length = RADIATOR_CORE / 2 + RADIATOR_TANK
    radiator_y = (RADIATOR_FRONT_Y, RADIATOR_FRONT_Y + RADIATOR_THICKNESS)
    for index, bottom in enumerate(RADIATOR_BOTTOMS_Z):
        top = bottom + RADIATOR_CORE
        label = ("Bottom", "Middle", "Top")[index]
        plate = box((-TEN_INCH_PANEL_WIDTH / 2, TEN_INCH_PANEL_WIDTH / 2), RADIATOR_PLATE_Y, (bottom - 2.0, top + 2.0))
        plate = plate.cut(box((-76.0, 76.0), RADIATOR_PLATE_Y, (bottom + 1.0, top - 1.0)))
        add_feature(doc, group, f"RadiatorPlate_{label}_Printed", plate, PRINTED_ORANGE)

        radiator = box((-half_length, half_length), radiator_y, (bottom, top))
        add_feature(doc, group, f"Radiator_{label}", radiator, RADIATOR_SILVER)
        fan_y = (radiator_y[1] + 0.5, radiator_y[1] + 0.5 + FAN_THICKNESS)
        add_feature(doc, group, f"Fan_ArcticP12_{label}Exhaust",
                    fan_shape((-FAN_SIZE / 2, FAN_SIZE / 2), fan_y, (bottom, top)), FAN_GREY)

    for node_name, tips in fitting_tips_by_node.items():
        radiator_index, tank_side, lanes = TUBE_ROUTES[node_name]
        ports = radiator_port_positions(radiator_index, tank_side)
        port_parts = [Part.makeCylinder(TUBE_RADIUS, 8.0, port, App.Vector(0, 1, 0)) for port in ports]
        add_feature(doc, group, f"RadiatorPorts_{node_name}", Part.makeCompound(port_parts), STEEL_BLACK)
        # The lower fitting feeds the lower port, the upper fitting the upper port.
        lower_first_tips = sorted(tips, key=lambda v: v.z)
        for tube_index, (tip, port, lane_x) in enumerate(zip(lower_first_tips, ports, lanes)):
            route = [tip,
                     App.Vector(tip.x, TUBE_PLANE_Y, tip.z),
                     App.Vector(lane_x, TUBE_PLANE_Y, tip.z),
                     App.Vector(lane_x, TUBE_PLANE_Y, port.z),
                     App.Vector(port.x, TUBE_PLANE_Y, port.z),
                     port]
            route = remove_repeated_points(route)
            tube = tube_along(route, TUBE_RADIUS)
            feature = add_feature(doc, group, f"Tube_{node_name}_{tube_index + 1}", tube, TUBE_BLACK)
            feature.addProperty("App::PropertyLength", "PathLength", "Fit", "Centre-line length of the tube")
            feature.PathLength = sum((b - a).Length for a, b in zip(route, route[1:]))
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
    build_rack(doc)
    fitting_tips_by_node = {}
    for name, pump_side, slab_min_x in BOARD_LAYOUT:
        _, tips = build_node(doc, name, pump_side, slab_min_x, board_shapes, apu_centre, die_top_z, nexgen_meshes)
        fitting_tips_by_node[name] = tips
    build_power_and_misc(doc)
    build_rear_cooling(doc, fitting_tips_by_node)
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
