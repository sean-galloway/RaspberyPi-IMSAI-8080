"""Place the 6 M2.5 NPTH mounting holes relative to the board outline.

Board-relative by design: it finds the Edge.Cuts bounding box and offsets each
hole from its top-left corner, so it works no matter where the board has been
moved on the sheet (unlike absolute-coordinate placement).

Run from KiCad's PCB editor:
    Tools -> Scripting Console, then:
    exec(open('/mnt/data/github/RaspberyPi-IMSAI-8080/hardware/place_holes.py').read())

Idempotent: re-running removes the old H1..H6 first, so you can tweak and re-run.
The holes are isolated NPTH (no copper), excluded from BOM and the pick-and-place
file so the JLCPCB CPL stays clean.
"""
import pcbnew

FP_LIB  = "/usr/share/kicad/footprints/MountingHole.pretty"
FP_NAME = "MountingHole_2.7mm_M2.5"        # 2.7 mm isolated NPTH for M2.5

# (ref, x, y) in mm from the board's top-left datum, for the 214 x 55 board.
# H3/H6 pulled in to x=207 (7 mm from the 214 mm right edge; was 213 on the old
# 220 mm board). H2/H5 sit in the 120..160 inter-block gap.
HOLES = [
    ("H1",   7,  7),
    ("H2", 140,  7),
    ("H3", 207,  7),
    ("H4",   7, 48),
    ("H5", 140, 48),
    ("H6", 207, 48),
]

board = pcbnew.GetBoard()

# Datum = top-left corner of the Edge.Cuts bounding box (wherever it sits now).
bbox = board.GetBoardEdgesBoundingBox()
ox, oy = bbox.GetX(), bbox.GetY()

# Remove any previous H1..H6 so re-running is safe.
refs = {r for r, _, _ in HOLES}
for fp in list(board.GetFootprints()):
    if fp.GetReference() in refs:
        board.Remove(fp)

placed = 0
for ref, x, y in HOLES:
    fp = pcbnew.FootprintLoad(FP_LIB, FP_NAME)
    if fp is None:
        print(f"  could not load {FP_NAME} from {FP_LIB}")
        break
    board.Add(fp)
    fp.SetReference(ref)
    fp.SetValue("MountingHole")
    fp.SetPosition(pcbnew.VECTOR2I(ox + pcbnew.FromMM(x), oy + pcbnew.FromMM(y)))
    try:
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    except AttributeError:
        pass          # older API: set these by hand in Footprint Properties
    placed += 1

print(f"placed {placed}/6 mounting holes "
      f"(datum @ {pcbnew.ToMM(ox):.1f},{pcbnew.ToMM(oy):.1f} mm)")
pcbnew.Refresh()
