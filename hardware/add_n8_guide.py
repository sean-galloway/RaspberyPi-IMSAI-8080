#!/usr/bin/env python3
"""N$8 (USB_DM, U1-46) pad escape: jogged F.Cu stub + via at (87.60,93.55).
Clears pad 45 by 0.15/0.24 mm and the N$7 guide via by 1.04 mm centre
distance. Freerouting continues from the bottom layer.
"""
import pcbnew
from pcbnew import VECTOR2I

MM = 1_000_000
W = 150_000
b = pcbnew.LoadBoard("imspi8080.kicad_pcb")
net = None
for fp in b.Footprints():
    if fp.GetReference() == "U1":
        for pad in fp.Pads():
            if pad.GetNumber() == "46":
                net = pad.GetNetCode()
                assert str(pad.GetNetname()) == "N$8"
assert net is not None

def seg(x1,y1,x2,y2):
    tr = pcbnew.PCB_TRACK(b)
    tr.SetStart(VECTOR2I(int(x1*MM),int(y1*MM)))
    tr.SetEnd(VECTOR2I(int(x2*MM),int(y2*MM)))
    tr.SetWidth(W); tr.SetLayer(pcbnew.F_Cu); tr.SetNetCode(net)
    b.Add(tr)

def via(x,y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(VECTOR2I(int(x*MM),int(y*MM)))
    v.SetWidth(int(0.6*MM)); v.SetDrill(int(0.3*MM))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net)
    b.Add(v)

seg(86.9625, 94.4375, 86.9625, 93.78)
seg(86.9625, 93.78, 87.60, 93.78)
seg(87.60, 93.78, 87.60, 93.55)
via(87.60, 93.55)
b.Save("imspi8080.kicad_pcb")
print("N$8 guide placed")
