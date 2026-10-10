"""Rev3 -> 4 layers with inner power planes.

Stackup: F.Cu (signals) / In1.Cu = GND plane / In2.Cu = +3V3 plane / B.Cu (signals).
Every GND / +3V3 pad (switch V/G pads and the electronics) taps its plane, so the planes
carry the rails and Freerouting only has to route signals on the two outer layers.
Run after rev3_voids2.py; export the DSN afterwards.
"""
import pcbnew

F = "imspi8080_rev3.kicad_pcb"
b = pcbnew.LoadBoard(F)
b.SetCopperLayerCount(4)

bb = b.GetBoardEdgesBoundingBox()
ins = pcbnew.FromMM(0.4)
CORNERS = [(bb.GetX()+ins, bb.GetY()+ins), (bb.GetRight()-ins, bb.GetY()+ins),
           (bb.GetRight()-ins, bb.GetBottom()-ins), (bb.GetX()+ins, bb.GetBottom()-ins)]

def plane(layer, net):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(b.FindNet(net))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)   # thermal relief -> hand-solderable pads
    z.SetMinThickness(pcbnew.FromMM(0.2))
    o = z.Outline(); o.NewOutline()
    for px, py in CORNERS: o.Append(px, py)
    b.Add(z)

plane(pcbnew.In1_Cu, "GND")
plane(pcbnew.In2_Cu, "+3V3")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(F)
print("set 4 copper layers; In1.Cu=GND plane, In2.Cu=+3V3 plane; zones poured")
