"""Build the Version 1 FreeCAD assembly: three BC-250 boards with their stock heatsinks in a case
made from the rack's two frames and printed PLA parts. Layout and part shapes: v1_model.py.

Run with the FreeCAD GUI so colours are saved with the document:
    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecad.exe" cad\\build_v1.py
`freecadcmd.exe cad\\build_v1.py` gives the same geometry without colours.

Output: bc250_v1.FCStd in the project root. Check it with
    set BC250_DOCUMENT=bc250_v1.FCStd
    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\check_fit.py

Every object carries a FitRole for check_fit.py: rack (frames and printed parts), hardware,
keepout (cable space).
"""
import os
import sys

import FreeCAD as App
import Part

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1_model as m  # noqa: E402

OUTPUT_PATH = os.path.join(m.PROJECT_DIR, "bc250_v1.FCStd")

PCB_GREEN = (0.10, 0.35, 0.18)
COMPONENT_GREY = (0.25, 0.25, 0.27)
CONNECTOR_BLACK = (0.08, 0.08, 0.08)
HEATSINK_ALU = (0.78, 0.78, 0.80)
BACKPLATE_DARK = (0.30, 0.31, 0.33)
FRAME_WHITE = (0.92, 0.92, 0.90)
WINDOW_CLEAR = (0.70, 0.80, 0.90)
STEEL_BLACK = (0.12, 0.12, 0.13)
PRINTED_WHITE = (0.96, 0.95, 0.90)
PRINTED_BLACK = (0.22, 0.22, 0.24)
FAN_GREY = (0.30, 0.30, 0.32)
BLOWER_BLUE = (0.20, 0.35, 0.60)
KEEPOUT_ORANGE = (1.00, 0.55, 0.00)


def add_feature(doc, container, name, shape, color, role="hardware", transparency=0):
    feature = doc.addObject("Part::Feature", name)
    feature.Shape = shape
    feature.addProperty("App::PropertyString", "FitRole", "Fit", "rack | hardware | keepout")
    feature.FitRole = role
    container.addObject(feature)
    if App.GuiUp:
        feature.ViewObject.ShapeColor = color
        feature.ViewObject.Transparency = transparency
    return feature


def build_frames(doc):
    group = doc.addObject("App::Part", "Rack_Frames_Reused")
    for name, outer_y, inward in (("Front", 0.0, +1), ("Back", m.CASE_DEPTH, -1)):
        shapes = m.frame_shapes(outer_y, inward)
        add_feature(doc, group, f"{name}Frame_Uprights", shapes["Uprights"], FRAME_WHITE, "rack")
        add_feature(doc, group, f"{name}Frame_TopBand", shapes["TopBand"], FRAME_WHITE, "rack")
        add_feature(doc, group, f"{name}Frame_Window", shapes["Window"], WINDOW_CLEAR, "rack", transparency=80)
        add_feature(doc, group, f"{name}Frame_Handle", shapes["Handle"], STEEL_BLACK, "rack")
    return group


def build_case(doc):
    group = doc.addObject("App::Part", "Printed_Case")
    add_feature(doc, group, "SideWall_L_CableSlots", m.side_wall(-1), PRINTED_BLACK, "rack", transparency=30)
    add_feature(doc, group, "SideWall_R", m.side_wall(+1), PRINTED_BLACK, "rack", transparency=30)
    add_feature(doc, group, "SideWindows_L_PCTG", m.window_sheets(-1), WINDOW_CLEAR, "rack", transparency=75)
    add_feature(doc, group, "SideWindows_R_PCTG", m.window_sheets(+1), WINDOW_CLEAR, "rack", transparency=75)
    add_feature(doc, group, "SideWall_L_SpliceBars", m.wall_splice_bars(-1), PRINTED_BLACK, "rack")
    add_feature(doc, group, "SideWall_R_SpliceBars", m.wall_splice_bars(+1), PRINTED_BLACK, "rack")
    add_feature(doc, group, "RoofGrille", m.roof(), PRINTED_BLACK, "rack")
    add_feature(doc, group, "BackPlate", m.back_plate(), PRINTED_WHITE, "rack")
    for column in m.COLUMNS:
        prefix = f"Col{column.index + 1}"
        if column.divider is not None:
            add_feature(doc, group, f"{prefix}_Divider",
                        m.divider(column.divider, m.blower_intake_centre(m.COLUMNS[column.index - 1])),
                        PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_FanPlate", m.fan_plate(column), PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_FanClips", Part.makeCompound(m.fan_clips(column)), PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_SpliceStrips", Part.makeCompound(m.splice_strips(column)),
                    PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_Lid", m.cold_box_cap(column), PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_BlowerHolder", m.blower_holder(column), PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_Cradle", m.cradle(column), PRINTED_WHITE, "rack")
        add_feature(doc, group, f"{prefix}_Crossbar", m.crossbar(column), PRINTED_WHITE, "rack")
    return group


def build_node(doc, column, board_shapes, brackets, keepouts):
    node = doc.addObject("App::Part", column.name)
    board = doc.addObject("App::Part", f"{column.name}_Board")
    node.addObject(board)
    board.Placement = m.board_placement(column)
    name = column.name
    add_feature(doc, board, f"{name}_PCB", board_shapes["pcb"].copy(), PCB_GREEN)
    add_feature(doc, board, f"{name}_Components", board_shapes["components"].copy(), COMPONENT_GREY)
    add_feature(doc, board, f"{name}_Connectors", board_shapes["connectors"].copy(), CONNECTOR_BLACK)
    add_feature(doc, board, f"{name}_StockHeatsink", board_shapes["heatsink"].copy(), HEATSINK_ALU)
    add_feature(doc, board, f"{name}_Backplate", board_shapes["backplate"].copy(), BACKPLATE_DARK)
    io_bracket, far_bracket = brackets
    add_feature(doc, board, f"{name}_IOBracket_EST", io_bracket.copy(), HEATSINK_ALU)
    add_feature(doc, board, f"{name}_FarBracket_EST", far_bracket.copy(), HEATSINK_ALU)
    power_plugs, network_adapter = keepouts
    add_feature(doc, board, f"{name}_KO_PowerPlugs", power_plugs.copy(), KEEPOUT_ORANGE, "keepout", 70)
    add_feature(doc, board, f"{name}_KO_NetworkAdapter", network_adapter.copy(), KEEPOUT_ORANGE, "keepout", 70)

    lower_fan, upper_fan = m.fan_shapes(column)
    add_feature(doc, node, f"{name}_Fan_Lower", lower_fan, FAN_GREY)
    add_feature(doc, node, f"{name}_Fan_Upper", upper_fan, FAN_GREY)
    add_feature(doc, node, f"{name}_Blower", m.blower_shape(column), BLOWER_BLUE)
    add_feature(doc, node, f"{name}_KO_BlowerOutlet", m.blower_outlet_keepout(column), KEEPOUT_ORANGE, "keepout", 70)
    return node


def main():
    if App.GuiUp:
        import FreeCADGui
    for open_doc in list(App.listDocuments().values()):
        if open_doc.FileName == OUTPUT_PATH:
            App.closeDocument(open_doc.Name)

    board_shapes = m.load_board_shapes()
    brackets = m.bracket_shapes_local()
    keepouts = m.keepouts_local()
    doc = App.newDocument("bc250_v1")
    build_frames(doc)
    build_case(doc)
    for column in m.COLUMNS:
        build_node(doc, column, board_shapes, brackets, keepouts)
    doc.recompute()
    doc.saveAs(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH} with {len(doc.Objects)} objects; case depth {m.CASE_DEPTH:.1f} mm", flush=True)
    for side, name in ((+1, "right"), (-1, "left")):
        width, height = m.window_sheet_size(m.COLUMNS[0], side)
        print(f"  {name} window panels: 3 x {width:.1f} x {height:.1f} mm; screw holes "
              f"{m.WINDOW_SHEET_OVERLAP - m.WINDOW_SCREW_INSET:.1f} mm in from each edge, "
              f"corners + mid-sides", flush=True)
    for column in m.COLUMNS:
        print(f"  {column.name}: cold box {column.cold_box[0]:.1f}..{column.cold_box[1]:.1f}, "
              f"fan {column.fan[0]:.1f}..{column.fan[1]:.1f}, PCB front {column.pcb_front_y:.1f}, "
              f"blower {column.blower[0]:.1f}..{column.blower[1]:.1f}, next wall {column.back_y:.1f}", flush=True)
    if App.GuiUp:
        FreeCADGui.SendMsgToActiveView("ViewFit")
        FreeCADGui.activeDocument().activeView().viewIsometric()
    if os.environ.get("BC250_EXIT_AFTER_BUILD"):
        os._exit(0)


main()
