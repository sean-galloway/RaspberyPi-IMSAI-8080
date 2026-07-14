"""Rev3: reorganize the board into 3 bands on a taller 204 x 95 outline.

Architecture (top -> bottom): connectors at the top edge, digital cluster, TLC
drivers, LED field at the BOTTOM. Switches are fascia-mounted + wired, so J3/J4
become bare through-hole solder-pad rows (no JST housing). Short standoffs.

Loads the rev2 board (reuses all footprints + nets), repositions everything,
swaps J3/J4 footprints to pin-header pads, rips up routing. -> imspi8080_rev3.kicad_pcb
Run:  /usr/bin/python3 rev3_build.py
"""
import pcbnew

SRC, DST = "OLD/imspi8080_rev2.kicad_pcb", "imspi8080_rev3.kicad_pcb"   # rev2 archived in OLD/
BW, BH = 204.0, 95.0
PHLIB = "/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty"

# anchor positions (board-rel mm): ref -> (x, y, rot)
ANCHOR = {
    # top-edge connectors (openings face up -> rot 180 / microSD slot up)
    "J1": (72, 9, 180), "J2": (112, 9, 180), "U7": (182, 13, 180),
    # digital band
    "U5": (33, 28, 0), "U6": (168, 28, 0), "SW1": (128, 22, 0), "SW2": (136, 22, 0),
    "U1": (98, 34, 0), "U2": (113, 34, 0), "Y1": (86, 34, 0),
    "U8": (54, 42, 0), "U9": (24, 42, 0), "J5": (150, 40, 0),
    # TLC drivers just above the LEDs
    "U3": (62, 54, 0), "U4": (142, 54, 0),
    # J3/J4 -> bare solder-pad rows at the bottom edge (rot 90 = horizontal row)
    "J3": (40, 91, 90), "J4": (150, 91, 90),
}
OVERRIDE = {"R12": (196, 22)}   # SD pull-up rode U7 off the top-right corner
# LED grid (rev3: rows LOW on the board)
GX0, GY0, CP, RP, RX0 = 14.0, 64.0, 15.0, 12.0, 147.0
def led_xy(n):
    if n <= 24:
        row, col = divmod(n - 1, 8); return GX0 + col*CP, GY0 + row*RP
    return RX0 + (n - 25)*CP, GY0 + RP
LEDS = {f"D{n}": (led_xy(n)[0], led_xy(n)[1], 0) for n in range(1, 29)}
HOLES = {"H1": (8, 8, 0), "H2": (131, 8, 0), "H3": (196, 8, 0),
         "H4": (8, 87, 0), "H5": (131, 87, 0), "H6": (196, 87, 0)}
FIXED = {**ANCHOR, **LEDS, **HOLES}

b = pcbnew.LoadBoard(SRC)
bb = b.GetBoardEdgesBoundingBox(); OX, OY = bb.GetX(), bb.GetY()
def to_sheet(x, y): return pcbnew.VECTOR2I(OX + pcbnew.FromMM(x), OY + pcbnew.FromMM(y))
def rel(p): return (pcbnew.ToMM(p.x - OX), pcbnew.ToMM(p.y - OY))

# rip up routing FIRST (pcbnew dislikes track access after footprint swaps)
for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)

# --- swap J3/J4 footprints to bare pin-header pads, preserving nets ---
for ref, fp in (("J3", "PinHeader_1x10_P2.54mm_Vertical"), ("J4", "PinHeader_1x06_P2.54mm_Vertical")):
    old = b.FindFootprintByReference(ref)
    nets = {p.GetNumber(): p.GetNetCode() for p in old.Pads()}
    b.Remove(old)
    new = pcbnew.FootprintLoad(PHLIB, fp)
    b.Add(new); new.SetReference(ref); new.SetValue("SW_PADS")
    for p in new.Pads():
        if p.GetNumber() in nets: p.SetNetCode(nets[p.GetNumber()])

fps = {f.GetReference(): f for f in b.GetFootprints()}
old_rel = {r: rel(f.GetPosition()) for r, f in fps.items()}
anchor_old = {r: old_rel[r] for r in ANCHOR}
def nearest(x, y): return min(anchor_old, key=lambda a: (anchor_old[a][0]-x)**2 + (anchor_old[a][1]-y)**2)

for ref, f in fps.items():
    if ref in FIXED:
        nx, ny, rot = FIXED[ref]; f.SetPosition(to_sheet(nx, ny)); f.SetOrientationDegrees(rot)
    elif ref in OVERRIDE:
        f.SetPosition(to_sheet(*OVERRIDE[ref]))
    else:  # passive rides nearest anchor
        ox_, oy_ = old_rel[ref]; a = nearest(ox_, oy_); axo, ayo = anchor_old[a]; axn, ayn, _ = ANCHOR[a]
        f.SetPosition(to_sheet(axn + (ox_-axo), ayn + (oy_-ayo)))

# resize Edge.Cuts
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.Remove(d)
c = [(0,0),(BW,0),(BW,BH),(0,BH),(0,0)]
for (x1,y1),(x2,y2) in zip(c, c[1:]):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(to_sheet(x1,y1)); s.SetEnd(to_sheet(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
b.Save(DST)
print(f"saved {DST}  {BW}x{BH}  (J3/J4 -> pad rows)")
