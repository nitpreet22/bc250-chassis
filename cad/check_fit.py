"""Check the BC-250 cluster assembly for clashes and report clearances.

Run headless after build_cluster.py:
    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad\\check_fit.py

Writes cad/fit_report.md and prints it. Rules, using each object's FitRole:
  * rack vs anything                -> clash (a part pokes through the rack structure)
  * hardware vs hardware            -> clash (two physical parts occupy the same space)
  * keepout vs hardware of another assembly -> clash (a part blocks space reserved for cables)
Overlaps smaller than VOLUME_TOLERANCE are treated as touching (e.g. the cold plate on the APU).
"""
import itertools
import os
import time

import FreeCAD as App
import Part

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENT_PATH = os.path.join(PROJECT_DIR, "bc250_cluster.FCStd")
REPORT_PATH = os.path.join(PROJECT_DIR, "cad", "fit_report.md")

VOLUME_TOLERANCE = 1.0            # mm^3
FRAME_BOX = App.BoundBox(-140.0, 0.0, 0.0, 140.0, 200.0, 469.45)

# Clearances worth knowing when assembling (object name patterns, min distance reported).
CLEARANCE_PAIRS = [
    ("Node1_Left_TeucerPump", "SidePanel_L"),
    ("Node3_Right_TeucerPump", "SidePanel_R"),
    ("Node1_Left_NexGen_BackBrace", "Node2_Middle_NexGen_BackBrace"),
    ("Node2_Middle_TeucerPump", "Node3_Right_NexGen_BackBrace"),
    ("Node2_Middle_USB25GDongle", "TopPanel"),
    ("Node1_Left_PCB", "CardShelf_Printed"),
    ("CardShelf_Printed", "PSU_MSI_A1000PL"),
    ("Node2_Middle_KO_PowerPlugs", "Upright_FrontL"),
    ("Node3_Right_KO_PowerPlugs", "Upright_FrontR"),
    ("Tube_Node1_Left_1", "Upright_RearL"),
    ("Tube_Node3_Right_2", "Upright_RearR"),
]


class FitObject:
    """One checked object, split into solids so booleans only run on pieces that can touch."""

    def __init__(self, obj):
        self.name = obj.Name
        self.role = obj.FitRole
        group = obj.getParentGeoFeatureGroup()
        self.owner = group.Name if group is not None else ""
        self.shape = global_shape(obj)
        self.box = self.shape.BoundBox
        self.solids = self.shape.Solids or [self.shape]


def global_shape(obj):
    placement = obj.getGlobalPlacement()
    if obj.TypeId == "Mesh::Feature":
        mesh = obj.Mesh.copy()
        mesh.Placement = placement
        shell = Part.Shape()
        shell.makeShapeFromMesh(mesh.Topology, 0.05)
        return Part.makeSolid(shell)  # much faster than Part.Solid(Part.Shell(faces))
    shape = obj.Shape.copy()
    shape.Placement = placement
    return shape


def is_checked_pair(a, b):
    roles = {a.role, b.role}
    if "rack" in roles:
        return roles != {"rack"}
    if roles == {"hardware"}:
        return True
    if roles == {"keepout", "hardware"}:
        return a.owner != b.owner
    return False  # keepout vs keepout: cables may share space


def overlap_volume(a, b):
    """Sum of overlaps between the solids of a and b whose bounding boxes intersect."""
    if not a.box.intersect(b.box):
        return 0.0
    total = 0.0
    for solid_a in a.solids:
        if not solid_a.BoundBox.intersect(b.box):
            continue
        for solid_b in b.solids:
            if solid_a.BoundBox.intersect(solid_b.BoundBox):
                total += solid_a.common(solid_b).Volume
    return total


def is_inside_source_board_model(a, b):
    """Overlaps between the PCB, components and connectors come from the downloaded STEP itself
    (e.g. through-hole pins modelled inside the PCB), not from our layout."""
    board_parts = ("_PCB", "_Components", "_Connectors")
    return a.owner == b.owner and a.name.endswith(board_parts) and b.name.endswith(board_parts)


# Clashes that were investigated; they stay in the report (they are real in the models) with context.
CLASH_NOTES = {
    ("_Components", "_NexGen_AM4_GenericBottom"):
        "Investigated: bracket is aligned to the 4 cooler holes (95.7 mm square) within 0.1 mm. "
        "Its flat underside sits on 0.4 mm SMD passives and one corner overlaps a 3.5 mm part "
        "next to the (-28.7, -37.2) hole by ~1.8 mm. Likely a board-model inaccuracy; check at test-fit.",
}


def explain_clash(name_a, name_b):
    for (suffix_a, suffix_b), note in CLASH_NOTES.items():
        if name_a.endswith(suffix_a) and name_b.endswith(suffix_b):
            return note
    return ""


def find_clashes(objects):
    """Return clashes as a list of (name_a, name_b, overlap volume)."""
    clashes = []
    for a, b in itertools.combinations(objects, 2):
        if not is_checked_pair(a, b) or is_inside_source_board_model(a, b):
            continue
        started = time.time()
        volume = overlap_volume(a, b)
        if time.time() - started > 5:
            print(f"  slow pair: {a.name} / {b.name} {time.time() - started:.0f}s", flush=True)
        if volume > VOLUME_TOLERANCE:
            clashes.append((a.name, b.name, volume))
    return clashes


def outside_frame(objects):
    rows = []
    for item in objects:
        if item.role == "rack":
            continue
        b = item.box
        overhang = {
            "left": FRAME_BOX.XMin - b.XMin, "right": b.XMax - FRAME_BOX.XMax,
            "front": FRAME_BOX.YMin - b.YMin, "rear": b.YMax - FRAME_BOX.YMax,
            "below": FRAME_BOX.ZMin - b.ZMin, "above": b.ZMax - FRAME_BOX.ZMax,
        }
        sticking_out = {side: round(v, 1) for side, v in overhang.items() if v > 0.05}
        if sticking_out:
            rows.append((item.name, sticking_out))
    return rows


def main():
    doc = App.openDocument(DOCUMENT_PATH)
    objects = [FitObject(obj) for obj in doc.Objects
               if hasattr(obj, "FitRole") and obj.TypeId in ("Part::Feature", "Mesh::Feature")]
    by_name = {item.name: item for item in objects}

    clashes = find_clashes(objects)
    overhangs = outside_frame(objects)

    overall = objects[0].box
    for item in objects[1:]:
        overall.add(item.box)

    lines = ["# BC-250 cluster fit report", "",
             f"Document: `{os.path.basename(DOCUMENT_PATH)}` - {len(objects)} checked objects", ""]
    lines.append(f"## Clashes ({len(clashes)})")
    lines.append("")
    if clashes:
        lines += ["| Object A | Object B | Overlap (mm^3) | Note |", "|---|---|---|---|"]
        lines += [f"| {a} | {b} | {v:.1f} | {explain_clash(a, b)} |"
                  for a, b, v in sorted(clashes, key=lambda c: -c[2])]
    else:
        lines.append("None: no hardware overlaps, nothing passes through the rack, keep-outs are clear.")
    lines += ["", "Not checked: overlaps between a board's own PCB / components / connectors "
                  "(they come from the downloaded STEP, e.g. pins modelled inside the PCB)."]
    lines += ["", "## Clearances (minimum distance)", "", "| Between | And | mm |", "|---|---|---|"]
    for name_a, name_b in CLEARANCE_PAIRS:
        distance = by_name[name_a].shape.distToShape(by_name[name_b].shape)[0]
        lines.append(f"| {name_a} | {name_b} | {distance:.1f} |")

    lines += ["", "## Parts outside the rack frame (280 x 200 x 469.45)", "",
              "| Object | Sticks out by (mm) |", "|---|---|"]
    lines += [f"| {name} | {', '.join(f'{k} {v}' for k, v in sides.items())} |" for name, sides in overhangs]

    lines += ["", "## Tube centre-line lengths", "", "| Tube | mm |", "|---|---|"]
    for obj in doc.Objects:
        if hasattr(obj, "PathLength"):
            lines.append(f"| {obj.Name} | {obj.PathLength.Value:.0f} |")

    lines += ["", "## Overall envelope including external parts", "",
              f"X {overall.XMin:.1f} .. {overall.XMax:.1f} ({overall.XLength:.1f} wide), "
              f"Y {overall.YMin:.1f} .. {overall.YMax:.1f} ({overall.YLength:.1f} deep), "
              f"Z {overall.ZMin:.1f} .. {overall.ZMax:.1f} ({overall.ZLength:.1f} tall)"]

    report = "\n".join(lines) + "\n"
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(report)
    print(report)


main()
