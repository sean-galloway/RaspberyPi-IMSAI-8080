"""Rev4 re-layout: 204x60, center-channel signal flow, J3/J4 as the switch interface.

Diagnosis this fixes (see git history + TODO): rev1/rev2 crammed U1/U8/U9/Y1/J2/J3/J4
and 40 passives into the bottom band y~42-57. That band is the toggle-bracket shadow
zone and the only switch-net highway, and the THT J3/J4 pads sat mid-band amid the
electronics -> 89/90 nets, ground routed as traces.

Placement principles here:
  * LED grid + mounting holes keep the rev2-aligned grids (fascia-fixed).
  * ALL electronics live in the center channel (x~121-146) or the side/bottom margins,
    in signal-flow order: flash/crystal/MCU top, TLC5947s mid (one per LED bank,
    channel edge nearest their LEDs), 74HC165s at channel bottom toward J3/J4.
  * J3/J4 (JST-XH, the toggle-bracket harness) sit at y~46 flanking the bottom-center
    USB pair, directly below their '165 -> switch nets < 30 mm, straight shots.
  * USB-C pair at bottom edge straddling H5; regulators near their USB input.
  * Nothing between the LED rows and the switch-net band except the power bus.
  * Passives: decoupling on B.Cu under their IC (via drops), the rest at their owner.

Run:  /usr/bin/python3 place_rev4.py     # writes imspi8080.kicad_pcb + report
"""
import pcbnew

SRC = "OLD/imspi8080_rev2.kicad_pcb"
DST = "imspi8080.kicad_pcb"
BW, BH = 204.0, 60.0

# ---------------------------------------------------------------- anchors (F.Cu)
# coords = BODY CENTER, board-rel mm, rot degrees
ANCHOR = {
    # --- digital core: RP2040 sits in the open bottom-left zone with THREE
    # --- open sides (N pocket to the LED grid, W, S to the board edge) - the
    # --- rev2-proven escape recipe. The center channel keeps only the TLCs
    # --- (feed the LED rows above) and the '165s (toward J3/J4 below).
    "J5":  ( 30.0, 46.5,  0),   # SWD 1x03, left of U1
    "Y1":  ( 40.0, 44.0,  0),   # 12 MHz crystal, west of U1
    "U1":  ( 50.0, 44.0,  0),   # RP2040 - open N/W/S escape
    "SW1": ( 41.0, 52.5,  0),   # BOOTSEL, south-west of U1
    "SW2": ( 58.0, 52.5,  0),   # RESET, south-east of U1
    "U2":  ( 61.85, 40.91,  0),   # QSPI flash, F.Cu, NE of U1; kept close so
                                  # the six QSPI dives keep short climbs
                                  # (204mm board: lanes 91.9-93.3 vs TLC/N$7)
    "U3":  (127.0, 31.5,  0),   # TLC5947 -> D1-24 (left bank)
    "U4":  (141.5, 30.5,  0),   # TLC5947 -> D25-28 (status bank)
    "U5":  (120.0, 41.0,  0),   # 74HC165 data bank, toward J3
    "U6":  (140.0, 41.0,  0),   # 74HC165 command bank, toward J4
    # --- bottom band: connectors + regulators only ---
    "J3":  ( 95.0, 46.0,  0),   # JST-XH 10P, data toggles harness (left)
    "J4":  (163.0, 45.0,  0),   # JST-XH 6P, command toggles harness (right)
    "J1":  (115.0, 54.0, 180),   # USB-C data, bottom edge left of H5
    "J2":  (145.0, 54.0, 180),   # USB-C power, bottom edge right of H5
    "U8":  ( 74.0, 49.5,  0),   # AMS1117 logic rail
    "U9":  (193.0, 38.0,  0),   # AMS1117 LED rail, right margin
    "U7":  (183.0, 52.0, 90),   # microSD, bottom-right (clear of status LEDs)
}

# NB: parts must NOT be side-flipped with raw SetLayer(B_Cu) - that leaves the
# footprint half-flipped (F.Cu pads at unmirrored coords overlapping neighbors,
# which both DRC and Freerouting rightly reject). Back-side passives below are
# natively authored on B.Cu by the source board, so they are safe.
ANCHOR_B = {
}

# ------------------------------------------------------- fixed grids (rev2-aligned)
GX0, GY0, CP, RP, RX0 = 14.0, 6.0, 15.0, 12.0, 147.0
def led_xy(n):
    if n <= 24:
        r, c = divmod(n - 1, 8)
        return GX0 + c * CP, GY0 + r * RP
    return RX0 + (n - 25) * CP, GY0 + RP
LEDS = {f"D{n}": (led_xy(n)[0], led_xy(n)[1], 0) for n in range(1, 29)}
HOLES = {"H1": (8, 7, 0), "H2": (131, 7, 0), "H3": (196, 7, 0),
         "H4": (8, 53, 0), "H5": (131, 53, 0), "H6": (196, 53, 0)}

# ------------------------------------------------------ passives (B.Cu unless noted)
# explicit body-center coords; 'F' forces F.Cu
PASSIVE = {
    # RP2040 decoupling ring on B.Cu around the flash (U2 owns the U1 footprint).
    "C1": (44.0, 41.0), "C2": (56.0, 41.0), "C3": (44.0, 47.0),
    "C4": (56.0, 47.0), "C5": (50.0, 39.0), "C15": (44.0, 44.0),
    "C6":  (56.0, 44.0),         # ADC_AVDD
    "C16": (47.0, 49.0),         # VCORE
    "C17": (53.0, 49.0),         # VCORE
    "C11": (59.0, 47.5),         # U2 flash (B, beside it)
    # crystal load caps (B, under Y1)
    "C23": (36.5, 42.5), "C24": (36.5, 45.5),
    # per-IC decoupling (B, under owner)
    "C7": (127.0, 29.0),         # U3
    "C8": (141.5, 28.0),         # U4
    "C9": (120.0, 41.0),         # U5
    "C10": (144.5, 41.0),        # U6
    "C12": (184.0, 47.0),        # U7 SD
    "C13": (68.0, 49.5),         # U8 out
    "C14": (186.0, 38.0, "F"),   # U9 out (LED rail) - F, hug the rail north
    # bulk / local
    "C18": (178.0, 58.5),        # SD local bulk
    "C19": (148.5, 41.0),        # spare local bulk near U6
    "C20": (74.0, 44.0),         # 10u logic rail (B, under U8)
    "C21": (186.0, 32.0),        # 10u LED rail
    "C22": (103.0, 53.5),        # 10u VBUS (J1 side)
    # USB CC pulldowns + data series (F, hugging the connector top edge)
    "R1": (111.5, 48.6, "F"), "R2": (118.5, 48.6, "F"),
    "R3": (140.0, 48.6, "F"), "R4": (147.0, 48.6, "F"),
    "R5": (47.0, 35.5, "F"),
    # R6 = USB_DM series (N$8, U1 pin 46). Pin 46's north side is walled off by
    # the VCORE/N$7/QSPI escapes, so R6 sits south of U1 where pin 46 escapes
    # under the chip body (freerouting jogs it around the +3V3 stub).
    "R6": (51.4, 50.6, "F"),
    # TLC IREF (F, just below each TLC)
    "R7": (124.5, 37.9, "F"), "R8": (144.4, 37.4, "F"),
    # SD pullups (B, under U7)
    "R9": (176.0, 47.5), "R10": (176.0, 50.0), "R11": (176.0, 52.5), "R12": (176.0, 55.0),
    # command pullups (F, beside U6)
    "R13": (145.8, 38.8, "F"), "R14": (148.1, 38.8, "F"),
    "R15": (150.4, 38.8, "F"), "R16": (152.7, 38.8, "F"),
}
PASSIVE_LAYER = {r: v[2] if len(v) > 2 else "B" for r, v in PASSIVE.items()}
PASSIVE_POS = {r: (v[0], v[1]) for r, v in PASSIVE.items()}

FIXED = {**ANCHOR, **LEDS, **HOLES}

board = pcbnew.LoadBoard(SRC)
bb = board.GetBoardEdgesBoundingBox()
OX, OY = bb.GetX(), bb.GetY()
sheet = lambda x, y: pcbnew.VECTOR2I(OX + pcbnew.FromMM(x), OY + pcbnew.FromMM(y))
rel = lambda p: (pcbnew.ToMM(p.x - OX), pcbnew.ToMM(p.y - OY))

# rip all routing/zones - fresh start
for t in list(board.GetTracks()):
    board.Remove(t)
for z in list(board.Zones()):
    board.Remove(z)

fps = {f.GetReference(): f for f in board.GetFootprints()}

def place_body_center(f, x, y, rot=None):
    """Position so footprint BODY CENTER lands at board-rel (x, y)."""
    f.SetPosition(sheet(0, 0))
    f.SetOrientationDegrees(0)
    c = f.GetBoundingBox(False, False).GetCenter()
    cx, cy = pcbnew.ToMM(c.x - f.GetPosition().x), pcbnew.ToMM(c.y - f.GetPosition().y)
    f.SetPosition(sheet(x - cx, y - cy))
    if rot is not None:
        f.SetOrientationDegrees(rot)

for ref, f in fps.items():
    if ref in ANCHOR_B:
        x, y, rot = ANCHOR_B[ref]
        place_body_center(f, x, y, rot)
        f.SetLayer(pcbnew.B_Cu)
    elif ref in FIXED:
        x, y, rot = FIXED[ref]
        place_body_center(f, x, y, rot)
    elif ref in PASSIVE_POS:
        x, y = PASSIVE_POS[ref]
        place_body_center(f, x, y)
        f.SetLayer(pcbnew.F_Cu if PASSIVE_LAYER[ref] == "F" else pcbnew.B_Cu)
        f.SetOrientationDegrees(0)
    else:
        print("!! unplaced part:", ref)

# netclasses already correct in the rev2 source board (Default 0.15/0.127,
# Power 0.5/0.127) - verified. But its via geometry is UNSET (-1), which makes
# KiCad emit a bogus '-0.001 um' padstack into the DSN; pin real vias instead.
ncd = {str(k): v for k, v in board.GetAllNetClasses().items()}["Default"]
ncd.SetViaDiameter(pcbnew.FromMM(0.6))
ncd.SetViaDrill(pcbnew.FromMM(0.3))

# Edge.Cuts -> exact 204x60 rectangle (drop whatever came in)
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
corners = [(0, 0), (BW, 0), (BW, BH), (0, BH), (0, 0)]
for (x1, y1), (x2, y2) in zip(corners, corners[1:]):
    seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(sheet(x1, y1))
    seg.SetEnd(sheet(x2, y2))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(pcbnew.FromMM(0.1))
    board.Add(seg)

board.Save(DST)
print(f"saved {DST}  board {BW}x{BH}")
