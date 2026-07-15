"""Rev3 switch landing pads (no voids): switches are fascia-mounted BELOW the board;
their pins jumper straight up to a labeled landing-pad cluster per switch at the board's
bottom edge. Board stays close to the fascia (crisp LEDs). Runs after rev3_place2.py.

Data land  (MTS-123): 1x03 header [+3V3, SWi, GND]
Cmd  land  (MTS-223): 2x03 header [CMDi, GND, + 4 spare for pole 2 / ARM]
"""
import pcbnew

F = "imspi8080_rev3.kicad_pcb"
BW, BH = 204.0, 99.7   # bottom edge clears the 2x03 command lands' lowest row (pad edge y~99)
PHLIB = "/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty"
LEFT_COLS   = [14, 29, 44, 59, 74, 89, 104, 119]
STATUS_COLS = [147, 162, 177, 192]
PAD_Y = 93.0

b = pcbnew.LoadBoard(F)
bb = b.GetBoardEdgesBoundingBox(); OX, OY = bb.GetX(), bb.GetY()
sheet = lambda x, y: pcbnew.VECTOR2I(OX+pcbnew.FromMM(x), OY+pcbnew.FromMM(y))
mm = pcbnew.FromMM
rel = lambda p: (pcbnew.ToMM(p.x-OX), pcbnew.ToMM(p.y-OY))

for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)
for r in ("J3", "J4"):
    f = b.FindFootprintByReference(r)
    if f: b.Remove(f)

LBL = {"+3V3": "V", "GND": "G"}
def silk(x, y, txt, size=0.85):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.B_SilkS)
    t.SetPosition(sheet(x, y)); t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.13))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)

def land(ref, x, y, fpname, padnets, rot=0):
    fp = pcbnew.FootprintLoad(PHLIB, fpname)
    b.Add(fp); fp.SetReference(ref); fp.SetValue("SW_LAND")
    fp.SetPosition(sheet(x, y)); fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        i = int(p.GetNumber()) - 1
        nn = padnets[i] if i < len(padnets) else None
        if nn:
            p.SetNet(b.FindNet(nn))
            rx, ry = rel(p.GetPosition())
            silk(rx, ry - 2.4, LBL.get(nn) or nn.replace("SW", "S").replace("CMD", "C"))

for i, x in enumerate(LEFT_COLS):
    land(f"SWD{i}", x, PAD_Y, "PinHeader_1x03_P2.54mm_Vertical", ["+3V3", f"SW{i}", "GND"], rot=90)
for i, x in enumerate(STATUS_COLS):
    land(f"SWC{i}", x, PAD_Y, "PinHeader_2x03_P2.54mm_Vertical", [f"CMD{i}", "GND", None, None, None, None])

for d in list(b.GetDrawings()):
    if d.GetLayer()==pcbnew.Edge_Cuts: b.Remove(d)
c = [(0,0),(BW,0),(BW,BH),(0,BH),(0,0)]
for (x1,y1),(x2,y2) in zip(c, c[1:]):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(sheet(x1,y1)); s.SetEnd(sheet(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
silk(102, 96.5, "SWITCH LANDS (below-board)  V=+3V3  G=GND (bussed)  Sn=data common  Cn=cmd common", 1.1)
b.Save(F)
print("saved", F, "with 12 bottom-edge switch lands (no voids); board", BW, "x", BH)
