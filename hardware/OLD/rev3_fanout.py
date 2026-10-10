"""Rev3 power fanout (post-route): give the RP2040 power a real path to the planes.

Autorouters never via a QFN exposed pad or fan out decoupling caps, so on a 4-layer
board GND-under-the-chip and the +3V3 decoupling islands strand from the planes. This
adds, relative to footprint geometry (so placement is clean, not blind):
  - a 2x2 thermal-via grid in U1's exposed GND pad (pin 57)
  - one fanout via just OUTSIDE each RP2040 decoupling cap's power pad (outward from the
    cap centre, where the spread placement leaves room), tying it to its plane.
Run after importing the routed SES; re-pour zones afterwards. DRC must stay 0/0.
"""
import pcbnew, math

F = "imspi8080_rev3.kicad_pcb"
DECAP = ["C1", "C2", "C3", "C4", "C5", "C6"]   # spread RP2040 +3V3 decouplers
POWER = ("GND", "+3V3")

b = pcbnew.LoadBoard(F)
mm = pcbnew.FromMM; tomm = pcbnew.ToMM

def via(x, y, net, drill=0.2, w=0.4):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
    v.SetDrill(mm(drill)); v.SetWidth(mm(w)); v.SetNet(b.FindNet(net))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)

added = 0
# 1) EP thermal-via grid (U1 pin 57 = 3.2mm GND pad); ±0.6mm clears the 0.4mm-pitch pins
u1 = b.FindFootprintByReference("U1")
ep = next(p for p in u1.Pads() if p.GetNumber() == "57")
ex, ey = ep.GetPosition().x, ep.GetPosition().y
for dx in (-0.6, 0.6):
    for dy in (-0.6, 0.6):
        via(ex + mm(dx), ey + mm(dy), "GND"); added += 1

# 2) one fanout via just outside each decap's power pad, offset outward from the cap centre
for ref in DECAP:
    f = b.FindFootprintByReference(ref)
    if not f: continue
    cx, cy = f.GetPosition().x, f.GetPosition().y
    for p in f.Pads():
        net = p.GetNetname()
        if net not in POWER: continue
        px, py = p.GetPosition().x, p.GetPosition().y
        dx, dy = px - cx, py - cy
        d = math.hypot(dx, dy) or 1
        vx = px + dx / d * mm(0.85); vy = py + dy / d * mm(0.85)
        via(vx, vy, net); added += 1

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(F)
print("added", added, "fanout vias (EP + decaps), re-poured")
