"""Rev3 placement v2 — signal-flow layout (RP2040 center, one TLC per LED bank).

Plan: RP2040 center with flash+crystal adjacent; U3 over the main LED block (D1-24),
U4 over the status block (D25-28); 74HC165s toward their switch pads (U5->J3, U6->J4);
regulators by the USB-C inputs; connectors on the top edge; LEDs at the bottom.
Passives ride their nearest anchor. J3/J4 = bare solder-pad rows for the fascia switches.
"""
import pcbnew

SRC, DST = "OLD/imspi8080_rev2.kicad_pcb", "imspi8080_rev3.kicad_pcb"
BW, BH = 204.0, 95.0
PHLIB = "/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty"

ANCHOR = {
    # top-edge connectors (openings up)
    "J1": (60, 9, 180), "J2": (120, 9, 180), "U7": (185, 14, 180),
    # regulators near the USB-C power in
    "U8": (78, 24, 0), "U9": (140, 24, 0),
    # MCU cluster dead-center: crystal - RP2040 - flash
    "Y1": (86, 44, 0), "U1": (102, 44, 0), "U2": (117, 44, 0),
    # BOOTSEL / RESET / SWD to the right of the MCU
    "SW1": (150, 40, 0), "SW2": (158, 40, 0), "J5": (168, 45, 0),
    # shift registers toward their switch pads
    "U5": (42, 52, 0), "U6": (162, 52, 0),
    # one TLC per LED bank (short cathodes)
    "U3": (66, 57, 0), "U4": (176, 57, 0),
    # bare solder-pad rows at the bottom edge
    "J3": (45, 91, 90), "J4": (150, 91, 90),
}
GX0, GY0, CP, RP, RX0 = 14.0, 64.0, 15.0, 12.0, 147.0
def led_xy(n):
    if n <= 24:
        r, c = divmod(n-1, 8); return GX0+c*CP, GY0+r*RP
    return RX0+(n-25)*CP, GY0+RP
LEDS = {f"D{n}": (led_xy(n)[0], led_xy(n)[1], 0) for n in range(1, 29)}
HOLES = {"H1": (8,8,0), "H2": (131,8,0), "H3": (196,8,0), "H4": (8,87,0), "H5": (131,87,0), "H6": (196,87,0)}
FIXED = {**ANCHOR, **LEDS, **HOLES}

b = pcbnew.LoadBoard(SRC)
bb = b.GetBoardEdgesBoundingBox(); OX, OY = bb.GetX(), bb.GetY()
sheet = lambda x, y: pcbnew.VECTOR2I(OX+pcbnew.FromMM(x), OY+pcbnew.FromMM(y))
rel = lambda p: (pcbnew.ToMM(p.x-OX), pcbnew.ToMM(p.y-OY))
for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)
for ref, fp in (("J3","PinHeader_1x10_P2.54mm_Vertical"), ("J4","PinHeader_1x06_P2.54mm_Vertical")):
    old = b.FindFootprintByReference(ref); nets = {p.GetNumber(): p.GetNetCode() for p in old.Pads()}
    b.Remove(old); new = pcbnew.FootprintLoad(PHLIB, fp)
    b.Add(new); new.SetReference(ref); new.SetValue("SW_PADS")
    for p in new.Pads():
        if p.GetNumber() in nets: p.SetNetCode(nets[p.GetNumber()])
fps = {f.GetReference(): f for f in b.GetFootprints()}
old_rel = {r: rel(f.GetPosition()) for r, f in fps.items()}
anchor_old = {r: old_rel[r] for r in ANCHOR}
nearest = lambda x, y: min(anchor_old, key=lambda a: (anchor_old[a][0]-x)**2+(anchor_old[a][1]-y)**2)
for ref, f in fps.items():
    if ref in FIXED:
        nx, ny, rot = FIXED[ref]; f.SetPosition(sheet(nx, ny)); f.SetOrientationDegrees(rot)
    else:
        ox_, oy_ = old_rel[ref]; a = nearest(ox_, oy_); axo, ayo = anchor_old[a]; axn, ayn, _ = ANCHOR[a]
        f.SetPosition(sheet(axn+(ox_-axo), ayn+(oy_-ayo)))
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.Remove(d)
c = [(0,0),(BW,0),(BW,BH),(0,BH),(0,0)]
for (x1,y1),(x2,y2) in zip(c, c[1:]):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(sheet(x1,y1)); s.SetEnd(sheet(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
b.Save(DST)
print("saved", DST)
