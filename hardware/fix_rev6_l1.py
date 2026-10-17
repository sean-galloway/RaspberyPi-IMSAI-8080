"""Fix L1 for the SMNR4020-2.2UH (LCSC C135262) on imspi8080_rev6.

Why: JLCPCB flagged L1 (footprint mismatch). The board carried the
Bourns SRU5016 5.2x5.2mm footprint while the BOM/part is the SXN
SMNR4020 4.0x4.0x2.0mm (JLC "SMD,4x4mm" is correct; the "4020" in the
MFR part number does NOT mean 4.0x2.0). Land pattern per datasheet:
2 pads 3.3 x 0.95mm, center pitch 3.05mm, non-polarized.

Changes:
  1. L1 footprint replaced (embedded): new pads at local x = +/-1.525,
     size 0.95(x) x 3.3(y); silk/fab/courtyard redrawn for 4x4mm body;
     Bourns 3D model dropped.
  2. Track cleanup around L1 so every net keeps one robust junction.
     Freerouting left ~0.3um sliver stubs and true zero-length segments
     at the old pad centers; the real topology is:
       LX:  pad1 -> (140.74,87.23)->(140.74,88.31) -> via -> In2 -> U1-48
       VCORE: pad2 <- (136.80,87.34)->(137.29,87.83) -> via -> In1
     New pads: pad1 x[139.7626,140.7126] y[85.2039,88.5039],
               pad2 x[136.7126,137.6626] y[85.2039,88.5039]
     so the LX feed at x=140.74 misses pad1's east edge by 27um; moving
     it to x=140.68 puts it inside pad1 while staying on the via annulus.

Pad numbering is preserved (1 = VREG_LX east, 2 = VCORE west); the part
is non-polar so orientation is free.

SWIG note: KiCad 10's pcbnew python wrappers return unwrapped temporaries
for container methods (Tracks/Pads/GraphicalItems/Models) after ANY board
mutation. ALL reads are snapshotted immediately after load.

Gate after save: check_opens.py must report every net single-island.
"""
import sys
import pcbnew

BOARD = "imspi8080_rev6.kicad_pcb"
NEWFP = "L_SXNSMNR4020_4x4x2mm"
UM = 1_000_000

def near(a, b, tol=0.008):  # mm
    return abs(a - b) <= tol

def length_mm(t):
    s, e = t.GetStart(), t.GetEnd()
    return math.hypot((e.x - s.x) / UM, (e.y - s.y) / UM)

import math
b = pcbnew.LoadBoard(BOARD)

# ---- SNAPSHOT EVERYTHING (fresh load: wrappers behave) ---------------------
fp_l1 = None
for fp in b.Footprints():
    if fp.GetReference() == "L1":
        fp_l1 = fp
        break
assert fp_l1, "L1 not found"

tracks_all = list(b.Tracks())
pads_all = list(fp_l1.Pads())
graphics_all = [gi for gi in fp_l1.GraphicalItems() if isinstance(gi, pcbnew.PCB_SHAPE)]
models_vec = fp_l1.Models()
center = fp_l1.GetPosition()
rot = fp_l1.GetOrientation().AsDegrees()
assert near(rot, 180.0, 0.5), f"L1 rotation {rot}, script assumes 180"
cx, cy = center.x, center.y

nets = {}
layers = None
for p in pads_all:
    n = p.GetNumber()
    if n in ("1", "2"):
        nets[n] = p.GetNetCode()
    if layers is None:
        layers = p.GetLayerSet()
assert "1" in nets and "2" in nets, "pad nets not captured"

# ---- 1. track surgery (uses snapshot) ---------------------------------------
LX, VCORE = "VREG_LX", "VCORE"
kill, move = [], []

OLD_P1 = (141.1128, 86.8541)   # old pad-1 center area
OLD_P2 = (136.3126, 86.8539)   # old pad-2 center
SPLIVER = (136.8003, 87.3414)  # vcore junction sliver
LXFEED_X = 140.74
LX_VIA_PT = (140.74, 88.3066)
VCORE_VIA_PT = (137.2880, 87.8851)

for t in tracks_all:
    if isinstance(t, pcbnew.PCB_VIA):         # PCB_VIA is a PCB_TRACK subclass
        continue
    if not isinstance(t, pcbnew.PCB_TRACK):
        continue
    n = t.GetNetname()
    if n not in (LX, VCORE):
        continue
    s, e = t.GetStart(), t.GetEnd()
    smm = (s.x / UM, s.y / UM)
    emm = (e.x / UM, e.y / UM)
    L = length_mm(t)

    if n == LX:
        # slivers + true zero-lengths at the old pad-1 center
        if (near(smm[0], OLD_P1[0]) and near(smm[1], OLD_P1[1])
                and near(emm[0], OLD_P1[0]) and near(emm[1], OLD_P1[1])
                and L < 0.005):
            kill.append(("lx-sliver", t))
            continue
        # redundant stub old-pad-center -> feed start
        if near(smm[0], OLD_P1[0]) and near(smm[1], OLD_P1[1]) and L > 0.005:
            kill.append(("lx-stub", t))
            continue
        # the vertical feed: both ends at x=140.74, length > 10um
        if near(smm[0], LXFEED_X) and near(emm[0], LXFEED_X) and L > 0.01:
            move.append((t, 140.68))
            continue
    else:  # VCORE
        # sliver at the junction point
        if (near(smm[0], SPLIVER[0]) and near(smm[1], SPLIVER[1])
                and near(emm[0], SPLIVER[0]) and near(emm[1], SPLIVER[1])
                and L < 0.005):
            kill.append(("vcore-sliver", t))
            continue
        # stub ending at the old pad-2 center
        if (near(emm[0], OLD_P2[0]) and near(emm[1], OLD_P2[1])) or \
           (near(smm[0], OLD_P2[0]) and near(smm[1], OLD_P2[1])):
            kill.append(("vcore-stub", t))
            continue

assert len(kill) == 6, f"expected 7 kills, got {len(kill)}: {[k[0] for k in kill]}"
assert len(move) == 1, f"expected 1 move, got {len(move)}"

for _, t in kill:
    b.Remove(t)
for t, nx in move:
    s, e = t.GetStart(), t.GetEnd()
    t.SetStart(pcbnew.VECTOR2I(int(nx * UM), s.y))
    t.SetEnd(pcbnew.VECTOR2I(int(nx * UM), e.y))
print(f"tracks: killed {len(kill)} {[k[0] for k in kill]}, moved feed x->140.68")

# ---- 2. footprint surgery ---------------------------------------------------
for p in pads_all:
    fp_l1.Remove(p)

def add_pad(number, lx, ly, sx, sy):
    p = pcbnew.PAD(fp_l1)
    p.SetNumber(number)
    p.SetSize(pcbnew.VECTOR2I(int(sx * UM), int(sy * UM)))
    if hasattr(pcbnew, "PAD_SHAPE_ROUNDRECT"):
        p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        if hasattr(p, "SetRoundRectRadiusRatio"):
            p.SetRoundRectRadiusRatio(0.25)
    else:
        p.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetLayerSet(layers)
    # local -> abs with rot 180: (lx,ly) -> (-lx,-ly)
    ax, ay = cx - lx * UM, cy - ly * UM
    p.SetPosition(pcbnew.VECTOR2I(int(round(ax)), int(round(ay))))
    p.SetOrientation(pcbnew.ANGLE_0)
    p.SetNetCode(nets[number])
    fp_l1.Add(p)

# local -x side = pad 1 (abs east = VREG_LX with rot 180)
add_pad("1", -1.525, 0.0, 0.95, 3.3)
add_pad("2", +1.525, 0.0, 0.95, 3.3)

for item in graphics_all:
    fp_l1.Remove(item)
print(f"footprint: removed {len(graphics_all)} old shapes, added 2 pads")

def seg(x1, y1, x2, y2, layer, width):
    s = pcbnew.PCB_SHAPE(fp_l1)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(int(x1 * UM), int(y1 * UM)))
    s.SetEnd(pcbnew.VECTOR2I(int(x2 * UM), int(y2 * UM)))
    s.SetLayer(layer)
    s.SetWidth(int(width * UM))
    fp_l1.Add(s)

def rect(hx, hy, layer, width):
    seg(-hx, -hy, hx, -hy, layer, width)
    seg(hx, -hy, hx, hy, layer, width)
    seg(hx, hy, -hx, hy, layer, width)
    seg(-hx, hy, -hx, -hy, layer, width)

# local coords; outline is symmetric so rot 180 is orientation-safe.
rect(2.0, 2.0, pcbnew.F_Fab, 0.10)                    # 4x4 body
seg(-2.0, -1.6, -1.6, -2.0, pcbnew.F_Fab, 0.10)       # pin-1 chamfer (pad 1 side)
rect(2.11, 2.11, pcbnew.F_SilkS, 0.12)
seg(-2.11, -1.7, -1.7, -2.11, pcbnew.F_SilkS, 0.12)
rect(2.30, 2.30, pcbnew.F_CrtYd, 0.05)

fp_l1.SetFPIDAsString(NEWFP)
fp_l1.SetLibDescription(
    "SXN SMNR4020 series shielded SMD power inductor 4.0x4.0x2.0mm "
    "(LCSC C135262) https://www.lcsc.com/product-detail/C135262.html")
fp_l1.SetKeywords("SMNR4020 SXN 4x4 inductor")

# models snapshot was taken pre-mutation; clear() works on it
models_vec.clear()

# ---- 3. save -----------------------------------------------------------------
out = BOARD if len(sys.argv) < 2 else sys.argv[1]
pcbnew.SaveBoard(out, b)
print(f"saved {out}")

# ---- 4. post-save text verification ------------------------------------------
txt = open(out, encoding="utf-8").read()
marker = '(uuid "ce360f33-d85b-4d71-af63-a4e12792c87b")'
mi = txt.find(marker)
assert mi != -1
block_start = txt.rfind('(footprint', 0, mi)
block_end = txt.find('\n\t(footprint', mi)
block = txt[block_start:block_end]

assert f'(footprint "{NEWFP}"' in block, "footprint rename missing"
assert '(model ' not in block, "stale 3D model present"
assert 'SRU5016' not in block, "stale Bourns text present"
assert '"VREG_LX"' in block and '"VCORE"' in block, "pad nets missing"
import re
sizes = re.findall(r'\(size ([0-9.]+) ([0-9.]+)\)', block)
assert ('0.95', '3.3') in sizes, f"pad sizes wrong: {sizes[:4]}"
print("post-save checks: name, nets, pads, no stale model - OK")

# junction vias must still exist (PCB_VIA is a PCB_TRACK subclass - the
# pre-save patterns must never have matched them)
b2 = pcbnew.LoadBoard(out)
via_hits = 0
for t in b2.Tracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = p.x / UM, p.y / UM
        if (near(x, 140.74) and near(y, 88.3066)) or (near(x, 137.288) and near(y, 87.8851)):
            via_hits += 1
assert via_hits == 2, f"junction vias missing: {via_hits}/2"
print("junction vias present: 2/2")
