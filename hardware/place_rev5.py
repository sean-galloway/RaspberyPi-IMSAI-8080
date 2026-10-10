#!/usr/bin/env python3
"""Place rev5: rev3's proven 204x112 2U placement + rev4's hard-won fixes.

Rev5 keeps everything rev3 established (panel-aligned LED grid, 12-toggle
SWPAD array at y=147, toggle voids, TLC/HC165/LDO/USB placement) and applies
what rev4's routing fight taught us:

1. R5/R6 (USB 27R series, nets N$7/N$8) move from north of U1 to the open
   band south of it - the rev4 root-cause fix for the boxed-in pin 46/47.
2. C15 vacates (139.2,94.8) for the N$8 guide column.
3. N$7/N$8 B.Cu birth-guides (rev4 geometry shifted +51.84 in x for U1 at
   137.4,97.9): stub up the pad's own column, via, freerouting continues.
4. All rev3 tracks/zones wiped for a fresh route.

Output: imspi8080_rev5.kicad_pcb (rev4 files untouched).
"""
import os
import pcbnew
from pcbnew import VECTOR2I

MM = 1_000_000
W = 150_000
SRC = "OLD/imspi8080_rev3.kicad_pcb"
DST = "imspi8080_rev5.kicad_pcb"
DX = 137.4 - 85.56  # U1 x shift rev4 -> rev5

b = pcbnew.LoadBoard(SRC)
FPS = {fp.GetReference(): fp for fp in b.Footprints()}  # snapshot before Remove()
n7 = b.FindNet("N$7").GetNetCode()
n8 = b.FindNet("N$8").GetNetCode()

# --- wipe all tracks and zones ----------------------------------------------
n = 0
for t in list(b.Tracks()):
    b.Remove(t)
    n += 1
for z in list(b.Zones()):
    try:
        b.Remove(z)
    except AttributeError:
        pass
print(f"wiped {n} tracks")

def setpos(ref, x, y, rot=0):
    fp = FPS[ref]
    fp.SetPosition(VECTOR2I(int(x * MM), int(y * MM)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    return fp

# --- rev4 fixes ---------------------------------------------------------------
setpos("R5", 132.5, 105.5)
setpos("R6", 137.5, 105.5)
setpos("C15", 148.5, 103.9)  # vacate the N$8 guide corridor
print("moved R5/R6 south of U1, C15 east")

# --- N$7/N$8 birth guides (rev4 coords + DX) -----------------------------------
def seg(x1, y1, x2, y2, net):
    tr = pcbnew.PCB_TRACK(b)
    tr.SetStart(VECTOR2I(int(round(x1 * MM)), int(round(y1 * MM))))
    tr.SetEnd(VECTOR2I(int(round(x2 * MM)), int(round(y2 * MM))))
    tr.SetWidth(W)
    tr.SetLayer(pcbnew.F_Cu)
    tr.SetNetCode(net)
    b.Add(tr)

def via(x, y, net):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(VECTOR2I(int(round(x * MM)), int(round(y * MM))))
    v.SetWidth(int(0.6 * MM))
    v.SetDrill(int(0.3 * MM))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(net)
    b.Add(v)

seg(86.5625 + DX, 94.4375, 86.5625 + DX, 93.55, n7)
seg(86.5625 + DX, 93.55, 86.42 + DX, 93.55, n7)
via(86.42 + DX, 93.55, n7)
seg(86.9625 + DX, 94.4375, 86.9625 + DX, 93.78, n8)
seg(86.9625 + DX, 93.78, 87.60 + DX, 93.78, n8)
seg(87.60 + DX, 93.78, 87.60 + DX, 93.55, n8)
via(87.60 + DX, 93.55, n8)
print("N$7/N$8 guides placed")

b.Save(DST)
bb = b.GetBoardEdgesBoundingBox()
print(f"saved {DST}  board {mm_w := (bb.GetRight()-bb.GetX())/1e6:.1f}x{(bb.GetBottom()-bb.GetY())/1e6:.1f}")
