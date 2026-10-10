"""Rev3 switches (4-layer) — HOLES + 3 big pads per switch that tap the GND/3V3 planes.

Each switch: a body VOID (hole) to pass through, and 3 fat through-hole pads below it in
a [V, signal, G] row. The V pad drops onto the +3V3 inner plane and the G pad onto the GND
inner plane (no rail routing needed — the planes ARE the shared rails); the middle signal
pad routes on an outer layer to the switch's own shift-register input.

Solder the switch's 3 pins straight down: throw->V, common->signal, throw->G.
Runs after rev3_place2.py; rev3_4layer.py then converts the board to 4 layers + planes.
"""
import pcbnew

F = "imspi8080_rev3.kicad_pcb"
BW, BH = 204.0, 112.0
TPLIB  = "/usr/share/kicad/footprints/TestPoint.pretty"
PADMOD = "TestPoint_THTPad_2.5x2.5mm_Drill1.2mm"
PITCH  = 5.0
LEFT_COLS   = [14, 29, 44, 59, 74, 89, 104, 119]
STATUS_COLS = [147, 162, 177, 192]
# pads ABOVE the voids: signal traces route UP to the shift registers without crossing
# the void row (keeps the switch area routable); voids sit below toward the board edge.
PAD_Y  = 93.0
VOID_Y = 103.0

b = pcbnew.LoadBoard(F)
bb = b.GetBoardEdgesBoundingBox(); OX, OY = bb.GetX(), bb.GetY()
sheet = lambda x, y: pcbnew.VECTOR2I(OX+pcbnew.FromMM(x), OY+pcbnew.FromMM(y))
mm = pcbnew.FromMM

for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)
for r in ("J3", "J4"):
    f = b.FindFootprintByReference(r)
    if f: b.Remove(f)

def silk(x, y, txt, size=0.9):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.B_SilkS)
    t.SetPosition(sheet(x, y)); t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.14))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)

def one_pad(ref, x, y, net):
    fp = pcbnew.FootprintLoad(TPLIB, PADMOD)
    b.Add(fp); fp.SetReference(ref); fp.SetValue("SWPAD"); fp.SetPosition(sheet(x, y))
    for p in fp.Pads(): p.SetNet(b.FindNet(net))

def switch(base, x, sig_net, sig_lbl):
    for dx, (net, lbl) in zip((-PITCH, 0, PITCH),
                              [("+3V3", "V"), (sig_net, sig_lbl), ("GND", "G")]):
        one_pad(f"{base}{lbl}", x+dx, PAD_Y, net)
        silk(x+dx, PAD_Y-2.7, lbl)   # label above the pad row (between LEDs and pads)

def void(x, y, w, h):
    r = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_RECT)
    r.SetStart(sheet(x-w/2, y-h/2)); r.SetEnd(sheet(x+w/2, y+h/2))
    r.SetLayer(pcbnew.Edge_Cuts); r.SetWidth(mm(0.1)); b.Add(r)

for i, x in enumerate(LEFT_COLS):
    void(x, VOID_Y, 13.5, 8.0);  switch(f"SWD{i}", x, f"SW{i}",  f"S{i}")
for i, x in enumerate(STATUS_COLS):
    void(x, VOID_Y, 13.5, 13.0); switch(f"SWC{i}", x, f"CMD{i}", f"C{i}")

for d in list(b.GetDrawings()):
    if d.GetLayer()==pcbnew.Edge_Cuts and d.GetShape()==pcbnew.SHAPE_T_SEGMENT: b.Remove(d)
c = [(0,0),(BW,0),(BW,BH),(0,BH),(0,0)]
for (x1,y1),(x2,y2) in zip(c, c[1:]):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(sheet(x1,y1)); s.SetEnd(sheet(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
silk(102, 110.0, "Each switch: V=+3V3 plane   middle=signal (Sn/Cn)   G=GND plane.  Body thru void below.", 1.0)
b.Save(F)
print("saved", F, "with 12 voids + 12x[V,sig,G] pads; board", BW, "x", BH)
