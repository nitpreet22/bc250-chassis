"""Render PNG views of bc250_cluster.FCStd into cad/renders/ (needs the FreeCAD GUI).

    set BC250_EXIT_AFTER_RENDER=1
    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecad.exe" cad\\render_views.py
"""
import os

import FreeCAD as App
import FreeCADGui as Gui

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENT_PATH = os.path.join(PROJECT_DIR, "bc250_cluster.FCStd")
RENDER_DIR = os.path.join(PROJECT_DIR, "cad", "renders")
IMAGE_SIZE = (1600, 1200)
ISOMETRIC_CAMERA = App.Rotation(0.424708, 0.17592, 0.339851, 0.820473)  # FreeCAD's isometric view

CASE_SHELL = ("SideWall", "TopFascia", "TopGrille", "Handle")
PSU_BOX_SHELL = ("PSUBox_LeftWall", "PSUBox_RightWall", "PSUBox_RearWall", "PSUBox_Lid", "DeskPowerSupply")
# Objects hidden in the "internals" views so the boards, PSU and tubes are visible.
INTERNALS_HIDDEN_PREFIXES = CASE_SHELL + PSU_BOX_SHELL + ("FrontFrame_Window", "BackFrame_Window",
                                                             "ChannelCover", "ChannelFan", "Switch")
# Right-side cutaway: just the case's right wall and fascia off, looking at all three columns.
RIGHT_CUTAWAY_HIDDEN_PREFIXES = ("SideWall_R", "TopFascia_R")
# Left cutaway: channel cover, its fan and the PSU box shell off, looking at the cable path.
LEFT_CUTAWAY_HIDDEN_PREFIXES = ("ChannelCover", "ChannelFan", "PSUBox_LeftWall", "PSUBox_Lid", "DeskPowerSupply")


def set_visibility(doc, hidden_prefixes):
    for obj in doc.Objects:
        if obj.TypeId in ("Part::Feature", "Mesh::Feature"):
            obj.ViewObject.Visibility = not obj.Name.startswith(hidden_prefixes)


def save(view, filename):
    view.fitAll()
    view.saveImage(os.path.join(RENDER_DIR, filename), IMAGE_SIZE[0], IMAGE_SIZE[1], "White")


def main():
    os.makedirs(RENDER_DIR, exist_ok=True)
    # Camera animations would still be running when the image is saved.
    view_settings = App.ParamGet("User parameter:BaseApp/Preferences/View")
    animations_were_on = view_settings.GetBool("UseNavigationAnimations", True)
    view_settings.SetBool("UseNavigationAnimations", False)
    doc = App.openDocument(DOCUMENT_PATH)
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    view = Gui.ActiveDocument.ActiveView
    view.setAxisCross(False)

    set_visibility(doc, ())
    view.viewIsometric()
    save(view, "01_iso_front_right.png")
    view.viewFront()
    save(view, "02_front.png")
    view.viewRight()
    save(view, "03_right_side.png")
    view.viewTop()
    save(view, "04_top.png")
    # Isometric from the rear-left: the standard isometric camera turned 180 deg about Z.
    # (Uses the fixed quaternion: viewIsometric() animates, so reading the camera back is unreliable.)
    view.setCameraOrientation(App.Rotation(App.Vector(0, 0, 1), 180).multiply(ISOMETRIC_CAMERA))
    save(view, "05_iso_rear_left.png")

    set_visibility(doc, INTERNALS_HIDDEN_PREFIXES)
    view.viewIsometric()
    save(view, "06_iso_internals.png")
    set_visibility(doc, RIGHT_CUTAWAY_HIDDEN_PREFIXES)
    view.viewRight()
    save(view, "07_right_cutaway_columns.png")
    set_visibility(doc, LEFT_CUTAWAY_HIDDEN_PREFIXES)
    view.viewLeft()
    save(view, "08_left_cutaway_cable_channel.png")
    set_visibility(doc, ())
    view.viewRear()
    save(view, "09_rear_psu_box.png")

    App.closeDocument(doc.Name)
    view_settings.SetBool("UseNavigationAnimations", animations_were_on)
    if os.environ.get("BC250_EXIT_AFTER_RENDER"):
        os._exit(0)


main()
