"""Post-route pass: solid GND pour on B.Cu (replaces "ground as traces").

Keeps every Freerouting track; the pour merges with the same-net GND copper.
If DRC is clean afterwards, optionally strip redundant B.Cu GND segments with
--strip-gnd-segments (every GND via then lands in the pour instead).

Run:  /usr/bin/python3 post_route.py [--strip-gnd-segments]
"""
import sys
import pcbnew

F = "imspi8080.kicad_pcb"
STRIP = "--strip-gnd-segments" in sys.argv

b = pcbnew.LoadBoard(F)
bb = b.GetBoardEdgesBoundingBox()
ins = pcbnew.FromMM(0.4)
x0, y0 = bb.GetX() + ins, bb.GetY() + ins
x1, y1 = bb.GetRight() - ins, bb.GetBottom() - ins

gnd = b.FindNet("GND")
z = pcbnew.ZONE(b)
z.SetLayer(pcbnew.B_Cu)
z.SetNet(gnd)
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
z.SetThermalReliefGap(pcbnew.FromMM(0.2))
z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.3))
z.SetMinThickness(pcbnew.FromMM(0.2))
o = z.Outline()
o.NewOutline()
for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
    o.Append(px, py)
b.Add(z)

if STRIP:
    n = 0
    for t in list(b.GetTracks()):
        if (t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.B_Cu
                and t.GetNetCode() == gnd.GetNetCode()):
            b.Remove(t)
            n += 1
    print(f"stripped {n} B.Cu GND segments")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(F)
print("poured GND on B.Cu, saved", F)
