#!/usr/bin/env python3
"""Final post-route fixups for the rev4 IMSPI 8080 board (U2 x=61.85).

Run: attempt.sh 61.85 && post_route.py && fixup_final.py

1. VBUS_LOGIC edge via (138.325,113.434): +0.9 mm north with F stub.
2. VBUS_LED edge via (214.023,113.434): shifted to (214.65,112.50), F.Cu
   feed extended, B.Cu diagonal re-anchored.
3. Freerouting remapped the VBUS_LOGIC east feed into a diagonal that sags
   to 0.063 mm of J1-A12; its west end is restored to (138.325,113.434).
4. +3V3_LED west anode rail: freerouting left the D9 column link dangling
   13 mm short of the y=70.795 rail with N$19 in the way. A 4-segment
   detour closes it: down the west gap, under N$19's block, up column
   x=65.795 from D2 to the rail (corridor verified clear of F.Cu).

J1-A6 (USB-C D+ duplicate pad) is intentionally unconnected: the plug
parallels A6/B6; D+ is routed via B6. KiCad lists it as the sole
"unconnected" item.
"""
import pcbnew
from pcbnew import VECTOR2I

MM = 1_000_000
F = "imspi8080.kicad_pcb"
b = pcbnew.LoadBoard(F)
ALL = list(b.Tracks())

def mm(v):
    return v / MM

def seg(x1, y1, x2, y2, layer, net):
    tr = pcbnew.PCB_TRACK(b)
    tr.SetStart(VECTOR2I(int(round(x1 * MM)), int(round(y1 * MM))))
    tr.SetEnd(VECTOR2I(int(round(x2 * MM)), int(round(y2 * MM))))
    tr.SetWidth(int(0.15 * MM))
    tr.SetLayer(layer)
    tr.SetNetCode(net)
    b.Add(tr)

# --- 1. VBUS_LOGIC via -------------------------------------------------------
vl = b.FindNet("VBUS_LOGIC").GetNetCode()
for t in ALL:
    if t.GetClass() == "PCB_VIA" and t.GetNetCode() == vl and abs(mm(t.GetPosition().y) - 113.434) < 0.01:
        old = VECTOR2I(t.GetPosition().x, t.GetPosition().y)
        new = VECTOR2I(old.x, old.y - int(0.9 * MM))
        t.SetPosition(new)
        for tr in ALL:
            if tr.GetClass() == "PCB_TRACK" and tr.GetNetCode() == vl:
                if tr.GetStart() == old:
                    tr.SetStart(new)
                if tr.GetEnd() == old:
                    tr.SetEnd(new)
        seg(mm(new.x), mm(new.y), mm(new.x), 113.434, pcbnew.F_Cu, vl)
        print("1. VBUS_LOGIC via moved")

# --- 2. VBUS_LED via ----------------------------------------------------------
vled = b.FindNet("VBUS_LED").GetNetCode()
via = fc = bc = None
for t in ALL:
    if t.GetClass() == "PCB_VIA" and t.GetNetCode() == vled and abs(mm(t.GetPosition().y) - 113.434) < 0.01:
        via = t
    if t.GetClass() == "PCB_TRACK" and t.GetNetCode() == vled:
        a, c = t.GetStart(), t.GetEnd()
        if t.GetLayer() == pcbnew.F_Cu and abs(mm(a.y) - 113.434) < 0.01 and abs(mm(c.y) - 113.434) < 0.01:
            fc = t
        if t.GetLayer() == pcbnew.B_Cu and mm(abs(c.x - a.x)) > 5:
            bc = t
assert via and fc and bc
newv = VECTOR2I(int(214.65 * MM), int(112.50 * MM))
via.SetPosition(newv)
a, c = fc.GetStart(), fc.GetEnd()
if mm(a.x) > mm(c.x):
    fc.SetStart(VECTOR2I(int(214.65 * MM), int(113.434 * MM)))
else:
    fc.SetEnd(VECTOR2I(int(214.65 * MM), int(113.434 * MM)))
seg(214.65, 113.434, 214.65, 112.50, pcbnew.F_Cu, vled)
if abs(mm(bc.GetStart().y) - 113.434) < 0.01:
    bc.SetStart(newv)
else:
    bc.SetEnd(newv)
print("2. VBUS_LED via shifted")

# --- 3. straighten VBUS_LOGIC east feed ---------------------------------------
for t in ALL:
    if t.GetClass() == "PCB_TRACK" and t.GetNetCode() == vl and t.GetLayer() == pcbnew.F_Cu:
        a, c = t.GetStart(), t.GetEnd()
        if abs(mm(a.x) - 138.325) < 0.01 and abs(mm(a.y) - 112.534) < 0.01 \
                and abs(mm(c.x) - 147.925) < 0.01 and abs(mm(c.y) - 113.434) < 0.01:
            t.SetStart(VECTOR2I(int(138.325 * MM), int(113.434 * MM)))
            print("3. VBUS_LOGIC feed straightened")

# --- 4. +3V3_LED west anode link ----------------------------------------------
v3 = b.FindNet("+3V3_LED").GetNetCode()
seg(52.153, 70.517, 58.0, 70.35, pcbnew.F_Cu, v3)
seg(58.0, 70.35, 64.2, 70.42, pcbnew.F_Cu, v3)
seg(64.2, 70.42, 65.795, 70.795, pcbnew.F_Cu, v3)
seg(65.795, 59.875, 65.795, 70.795, pcbnew.F_Cu, v3)
print("4. +3V3_LED west link closed")

b.Save(F)
b2 = pcbnew.LoadBoard(F)
pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
b2.Save(F)
print("saved + refilled")
