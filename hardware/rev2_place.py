"""Rev2 re-layout: reposition every footprint onto the trimmed 204 x 60 board.

Strategy:
  * LEDs + mounting holes -> the new grids (place_leds.py / place_holes.py values).
  * 17 "anchor" parts (U1-9, J1-5, Y1, SW1-2) -> computed positions that pull the
    right column in (opens the side channels) and shift the electronics up (60 mm board).
  * 40 back-side passives ride their nearest anchor rigidly -> decoupling clusters preserved.
  * Front-vs-front and back-vs-back courtyard overlaps are the only ones that matter
    (passives are on B.Cu, under the front LEDs/ICs). Reports overlaps + off-board parts.

Run:  /usr/bin/python3 rev2_place.py            # writes imspi8080_rev2.kicad_pcb + report
"""
import pcbnew

SRC = "imspi8080.kicad_pcb"
DST = "imspi8080_rev2.kicad_pcb"
BW, BH = 204.0, 60.0                       # target board mm

# --- anchor positions (board-rel mm): ref -> (x, y, rot) --------------------
ANCHOR = {
    "U1": (138.1, 53.51, 0), "U2": (151.1, 54.48, 0),
    "U3": (67.86, 41.45, 0), "U4": (163.1, 29.45, 0),
    "U5": (50.71, 42.85, 0), "U6": (146.8, 29.35, 0),
    "U7": (188.0, 28.00, 90), "U8": (83.92, 45.5, 0), "U9": (21.07, 42.08, 0),
    "Y1": (125.0, 56.0, 0), "SW1": (111.53, 41.38, 0), "SW2": (119.53, 41.38, 0),
    "J1": (83.83, 55.00, 0), "J2": (115.89, 54.70, 0), "J3": (23.32, 49.8, 0),
    "J4": (172.30, 49.8, 0), "J5": (83.58, 32.0, 0),
}

# --- LED grid (mirror place_leds.py rev2 constants) -------------------------
GX0, GY0, CP, RP, RX0 = 14.0, 6.0, 15.0, 12.0, 147.0
def led_xy(n):
    if n <= 24:
        row, col = divmod(n - 1, 8)
        return GX0 + col * CP, GY0 + row * RP
    return RX0 + (n - 25) * CP, GY0 + RP
LEDS = {f"D{n}": (led_xy(n)[0], led_xy(n)[1], 0) for n in range(1, 29)}

# --- mounting holes (mirror place_holes.py rev2) ---------------------------
HOLES = {"H1": (8, 7, 0), "H2": (131, 7, 0), "H3": (196, 7, 0),
         "H4": (8, 53, 0), "H5": (131, 53, 0), "H6": (196, 53, 0)}

FIXED = {**ANCHOR, **LEDS, **HOLES}

board = pcbnew.LoadBoard(SRC)
bb = board.GetBoardEdgesBoundingBox()
OX, OY = bb.GetX(), bb.GetY()                     # datum = old edge top-left
def to_sheet(x, y): return pcbnew.VECTOR2I(OX + pcbnew.FromMM(x), OY + pcbnew.FromMM(y))
def rel(pos):     return (pcbnew.ToMM(pos.x - OX), pcbnew.ToMM(pos.y - OY))

fps = {f.GetReference(): f for f in board.GetFootprints()}

# old relative positions (for the passive-ride computation)
old_rel = {ref: rel(f.GetPosition()) for ref, f in fps.items()}
anchor_old = {r: old_rel[r] for r in ANCHOR}

def nearest_anchor(x, y):
    return min(anchor_old, key=lambda a: (anchor_old[a][0]-x)**2 + (anchor_old[a][1]-y)**2)

# compute final rel position for every footprint
new_rel = {}
for ref, f in fps.items():
    if ref in FIXED:
        nx, ny, rot = FIXED[ref]
        new_rel[ref] = (nx, ny, rot)
    else:                                          # back-side passive: ride nearest anchor
        ox_, oy_ = old_rel[ref]
        a = nearest_anchor(ox_, oy_)
        axo, ayo = anchor_old[a]; axn, ayn, _ = ANCHOR[a]
        new_rel[ref] = (axn + (ox_-axo), ayn + (oy_-ayo), f.GetOrientationDegrees())

# post-nudges: caps too tight after riding their anchor (courtyard clearance)
OVERRIDE = {"C21": (24.3, 44.2)}     # 0805 bulk on U9 — clear of C14 (0402)
for r, (x, y) in OVERRIDE.items():
    if r in new_rel:
        new_rel[r] = (x, y, new_rel[r][2])

# apply
for ref, f in fps.items():
    nx, ny, rot = new_rel[ref]
    f.SetPosition(to_sheet(nx, ny))
    if ref in FIXED:
        f.SetOrientationDegrees(rot)

# resize Edge.Cuts: drop old edge graphics, draw new rectangle
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
corners = [(0,0),(BW,0),(BW,BH),(0,BH),(0,0)]
for (x1,y1),(x2,y2) in zip(corners, corners[1:]):
    seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(to_sheet(x1,y1)); seg.SetEnd(to_sheet(x2,y2))
    seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(pcbnew.FromMM(0.1))
    board.Add(seg)

# rip up all routing + zones (everything must be re-routed)
for t in list(board.GetTracks()): board.Remove(t)
for z in list(board.Zones()):     board.Remove(z)

board.Save(DST)

# ---- report: off-board + front/front & back/back courtyard overlaps -------
def cbb(f):
    lay = pcbnew.B_CrtYd if f.GetLayer()==pcbnew.B_Cu else pcbnew.F_CrtYd
    cy = f.GetCourtyard(lay)
    b = cy.BBox() if (cy and cy.OutlineCount()>0) else f.GetBoundingBox(False,False)
    return (pcbnew.ToMM(b.GetLeft()-OX), pcbnew.ToMM(b.GetTop()-OY),
            pcbnew.ToMM(b.GetRight()-OX), pcbnew.ToMM(b.GetBottom()-OY))

boxes = {ref: (cbb(f), "B" if f.GetLayer()==pcbnew.B_Cu else "F") for ref,f in fps.items()}
MARG = 0.15
off = []
for ref,(bx,lay) in boxes.items():
    l,t,r,b_ = bx
    if l < -0.05 or t < -0.05 or r > BW+0.05 or b_ > BH+0.05:
        off.append((ref, round(l,1),round(t,1),round(r,1),round(b_,1)))
def overlap(a,b):
    return not (a[2]<=b[0]+MARG or b[2]<=a[0]+MARG or a[3]<=b[1]+MARG or b[3]<=a[1]+MARG)
refs=list(boxes); ov=[]
for i in range(len(refs)):
    for j in range(i+1,len(refs)):
        ra,rb=refs[i],refs[j]
        (ba,la),(bb2,lb)=boxes[ra],boxes[rb]
        if la==lb and overlap(ba,bb2):
            ov.append(tuple(sorted((ra,rb))))
print(f"saved {DST}  board {BW}x{BH}")
print(f"OFF-BOARD ({len(off)}):")
for o in off: print("   ", o)
print(f"OVERLAPS same-layer ({len(ov)}):")
for a,b in sorted(set(ov)): print(f"    {a:4} <-> {b:4}  [{boxes[a][1]}]")
