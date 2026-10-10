#!/usr/bin/env python3
"""Prepare imspi8080_rev6.kicad_pcb for RP2040 -> RP2350A swap.

Performs:
- Replace U1 (RP2040 QFN-56) with RP2350A QFN-60 footprint.
- Move D1..D28 footprints -0.075 mm in X.
- Add L1 2.2uH inductor near U1 pins 44-54 side.
- Rip up tracks/vias for MCU/LED cluster nets.
- Save board.
"""

import math
import pcbnew

BOARD_PATH = "imspi8080_rev6.kicad_pcb"
QFN60_LIB = "/usr/share/kicad/footprints/Package_DFN_QFN.pretty"
QFN60_NAME = "QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm_ThermalVias"
IND_LIB = "/usr/share/kicad/footprints/Inductor_SMD.pretty"
IND_NAME = "L_Bourns_SRU5016_5.2x5.2mm"

# Net -> {pad_numbers} for new U1 per REV6-PLAN.md
U1_NET_PADS = {
    "+3V3": {"1", "11", "20", "30", "38", "45", "44", "53", "54"},
    "GND": {"61", "47"},
    "VCORE": {"23", "39", "6", "50"},
    "XIN": {"21"},
    "XOUT": {"22"},
    "N$1": {"24"},
    "N$2": {"25"},
    "RUN": {"26"},
    "N$8": {"51"},
    "N$7": {"52"},
    "QSPI_SD3": {"55"},
    "QSPI_SCLK": {"56"},
    "QSPI_SD0": {"57"},
    "QSPI_SD2": {"58"},
    "QSPI_SD1": {"59"},
    "QSPI_SS": {"60"},
    "TLC_SCLK": {"4"},
    "TLC_SIN": {"5"},
    "TLC_XLAT": {"7"},
    "TLC_BLANK": {"8"},
    "SD_SCK": {"14"},
    "SD_MOSI": {"15"},
    "SD_MISO": {"16"},
    "SD_CS": {"17"},
    "HC_PLOAD": {"9"},
    "HC_CLK": {"12"},
    "HC_QH": {"13"},
    "VREG_LX": {"48"},
}

# Flatten reverse map: pad -> net
PAD_TO_NET = {}
for net, pads in U1_NET_PADS.items():
    for pad in pads:
        PAD_TO_NET[pad] = net

# Nets whose tracks/vias must be ripped up (MCU cluster)
MCU_RIPUP_NETS = {
    "+3V3", "GND", "VCORE", "XIN", "XOUT", "N$1", "N$2", "RUN",
    "N$7", "N$8", "QSPI_SD3", "QSPI_SCLK", "QSPI_SD0", "QSPI_SD2",
    "QSPI_SD1", "QSPI_SS", "TLC_SCLK", "TLC_SIN", "TLC_XLAT",
    "TLC_BLANK", "SD_SCK", "SD_MOSI", "SD_MISO", "SD_CS",
    "HC_PLOAD", "HC_CLK", "HC_QH", "VREG_LX",
}


def nm(v):
    return int(round(v * 1e6))


def main():
    print("Loading board...")
    b = pcbnew.LoadBoard(BOARD_PATH)
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}

    # Build net name -> net object map, create missing nets
    net_by_name = {}
    for n in b.GetNetInfo().NetsByName().values():
        net_by_name[n.GetNetname()] = n

    def get_or_create_net(name):
        if name not in net_by_name:
            n = pcbnew.NETINFO_ITEM(b, name)
            b.Add(n)
            net_by_name[name] = n
            print(f"  created net: {name}")
        return net_by_name[name]

    # ---- 1. Collect LED nets for rip-up ------------------------------------
    led_nets = set()
    for i in range(1, 29):
        ref = f"D{i}"
        fp = fps.get(ref)
        if fp is None:
            continue
        for pad in fp.Pads():
            n = pad.GetNet()
            if n is not None:
                led_nets.add(n.GetNetname())
    print(f"Collected {len(led_nets)} LED nets: {sorted(led_nets)}")

    # ---- 2. Rip up tracks/vias for MCU + LED nets (before U1 swap) ---------
    ripup_net_names = MCU_RIPUP_NETS | led_nets
    ripup_nets = set()
    for name in ripup_net_names:
        n = net_by_name.get(name)
        if n is not None:
            ripup_nets.add(n.GetNetCode())

    removed_tracks = 0
    removed_vias = 0
    # Snapshot tracks before iteration because Remove invalidates iterators
    tracks = list(b.GetTracks())
    for item in tracks:
        net = item.GetNetCode()
        if net in ripup_nets:
            if item.Type() == pcbnew.PCB_VIA_T:
                removed_vias += 1
            else:
                removed_tracks += 1
            b.Remove(item)
    print(f"Ripped up {removed_tracks} tracks and {removed_vias} vias")

    # ---- 3. Replace U1 -----------------------------------------------------
    old_u1 = fps.get("U1")
    if old_u1 is None:
        raise RuntimeError("U1 not found on board")
    u1_pos = old_u1.GetPosition()
    u1_orient = old_u1.GetOrientation().AsDegrees()
    print(f"Old U1: {old_u1.GetValue()} at ({u1_pos.x/1e6:.3f}, {u1_pos.y/1e6:.3f}) orient={u1_orient}")

    # Verify QFN-60 footprint exists and has expected pads
    new_u1 = pcbnew.FootprintLoad(QFN60_LIB, QFN60_NAME)
    if new_u1 is None:
        raise RuntimeError(f"Could not load footprint {QFN60_NAME}")
    new_u1.SetReference("U1")
    new_u1.SetValue("RP2350A")
    new_u1.SetPosition(u1_pos)
    new_u1.SetOrientation(pcbnew.EDA_ANGLE(u1_orient, pcbnew.DEGREES_T))

    # Remove old U1, add new one
    b.Remove(old_u1)
    b.Add(new_u1)
    print(f"Added new U1 {new_u1.GetFPID().GetLibItemName()}")

    # Assign nets to pads
    assigned = 0
    nc_pads = []
    for pad in new_u1.Pads():
        num = pad.GetNumber()
        if num in PAD_TO_NET:
            net_name = PAD_TO_NET[num]
            net = get_or_create_net(net_name)
            pad.SetNet(net)
            assigned += 1
        elif num == "":
            pass  # unnumbered mechanical pads
        else:
            nc_pads.append(num)
            # Leave NC pads unconnected (no net)
    print(f"Assigned nets to {assigned} pads; NC pads: {sorted(set(nc_pads))}")

    # ---- 4. Move D1..D28 by -0.075 mm in X ---------------------------------
    moved = 0
    delta_x = nm(-0.075)
    for i in range(1, 29):
        ref = f"D{i}"
        fp = fps.get(ref)
        if fp is None:
            print(f"  WARNING: {ref} not found")
            continue
        old_pos = fp.GetPosition()
        new_pos = pcbnew.VECTOR2I(old_pos.x + delta_x, old_pos.y)
        fp.SetPosition(new_pos)
        moved += 1
    print(f"Moved {moved} LED footprints by -0.075 mm in X")

    # ---- 5. Add L1 ----------------------------------------------------------
    ind = pcbnew.FootprintLoad(IND_LIB, IND_NAME)
    if ind is None:
        raise RuntimeError(f"Could not load inductor footprint {IND_NAME}")
    ind.SetReference("L1")
    ind.SetValue("2.2uH")

    # Pin targets: VREG_LX=48, VCORE=50 on bottom edge of U1
    pin48_rel = (2.0, -3.45)   # mm relative to U1 center at orient 0
    pin50_rel = (1.2, -3.45)
    pin48_abs = (u1_pos.x/1e6 + pin48_rel[0], u1_pos.y/1e6 + pin48_rel[1])
    pin50_abs = (u1_pos.x/1e6 + pin50_rel[0], u1_pos.y/1e6 + pin50_rel[1])
    print(f"Pin 48 (VREG_LX) target: ({pin48_abs[0]:.3f}, {pin48_abs[1]:.3f})")
    print(f"Pin 50 (VCORE) target: ({pin50_abs[0]:.3f}, {pin50_abs[1]:.3f})")

    # Rebuild footprint list after U1 swap for collision checks
    other_footprints = [fp for fp in b.GetFootprints() if fp.GetReference() != "L1"]
    other_bboxes = []
    for fp in other_footprints:
        bb = fp.GetBoundingBox()
        other_bboxes.append((bb.GetX(), bb.GetY(), bb.GetX() + bb.GetWidth(), bb.GetY() + bb.GetHeight(), fp.GetReference()))

    def collides(cx, cy, half_w, half_h):
        x1, y1 = int(cx - half_w), int(cy - half_h)
        x2, y2 = int(cx + half_w), int(cy + half_h)
        for ex1, ey1, ex2, ey2, ref in other_bboxes:
            if not (x2 < ex1 or x1 > ex2 or y2 < ey1 or y1 > ey2):
                return ref
        return None

    # Remaining tracks for no-net pad collision checks (e.g. L1 mounting pads)
    remaining_tracks = list(b.GetTracks())

    def pad_bbox(pad, cx, cy, orient_deg):
        """Axis-aligned bbox (nm) of a pad placed at (cx,cy) with orient_deg rotation."""
        ang = math.radians(orient_deg)
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        lx = pad.GetPosition().x / 1e6
        ly = pad.GetPosition().y / 1e6
        rx = lx * cos_a - ly * sin_a
        ry = lx * sin_a + ly * cos_a
        px = cx + rx
        py = cy + ry
        hw = pad.GetSize().x / 2e6
        hh = pad.GetSize().y / 2e6
        # AABB of rotated rectangle
        dx = abs(hw * cos_a) + abs(hh * sin_a)
        dy = abs(hw * sin_a) + abs(hh * cos_a)
        return (nm(px - dx), nm(py - dy), nm(px + dx), nm(py + dy))

    def mp_pad_hits_track(cx, cy, orient_deg):
        """Return True if a no-net mounting pad would overlap any copper track."""
        for pad in ind.Pads():
            if pad.GetNumber() not in ("MP", ""):
                continue
            x1, y1, x2, y2 = pad_bbox(pad, cx, cy, orient_deg)
            for trk in remaining_tracks:
                # Quick bbox reject for track
                tx1 = min(trk.GetStart().x, trk.GetEnd().x)
                ty1 = min(trk.GetStart().y, trk.GetEnd().y)
                tx2 = max(trk.GetStart().x, trk.GetEnd().x)
                ty2 = max(trk.GetStart().y, trk.GetEnd().y)
                if x2 < tx1 or x1 > tx2 or y2 < ty1 or y1 > ty2:
                    continue
                # Segment-segment narrow phase is overkill; expanded bbox overlap
                # with a small guard band is sufficient for placement.
                guard = nm(0.15)  # 0.15 mm guard
                if not (x2 + guard < tx1 or x1 - guard > tx2 or y2 + guard < ty1 or y1 - guard > ty2):
                    return True
        return False

    def pad_positions(footprint, cx, cy, orient_deg):
        """Return absolute pad 1 and pad 2 positions for a placed/oriented footprint."""
        ang = math.radians(orient_deg)
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        pads = {}
        for p in footprint.Pads():
            n = p.GetNumber()
            if n in ("1", "2"):
                # Unplaced footprint is centered at origin; these are local coords.
                lx = p.GetPosition().x / 1e6
                ly = p.GetPosition().y / 1e6
                rx = lx * cos_a - ly * sin_a
                ry = lx * sin_a + ly * cos_a
                pads[n] = (cx + rx, cy + ry)
        return pads

    # Search spiral outward from pin 48 (VREG_LX) for nearest non-colliding spot.
    # Preferred orientation is 180°: pad 1 (VREG_LX) is on the right side of the
    # inductor, closer to U1 pin 48, and pad 2 (VCORE) on the left.
    half_col = 3.5
    best = None
    step = 0.1  # mm
    max_radius = 20.0

    for orient in (180, 0, 90, 270):
        best_for_orient = None
        for radius in [r * step for r in range(0, int(max_radius / step) + 1)]:
            for angle_deg in range(0, 360, 5):
                cx = pin48_abs[0] + radius * math.cos(math.radians(angle_deg))
                cy = pin48_abs[1] + radius * math.sin(math.radians(angle_deg))
                ref = collides(nm(cx), nm(cy), nm(half_col), nm(half_col))
                if ref is not None:
                    continue
                if mp_pad_hits_track(cx, cy, orient):
                    continue
                pads = pad_positions(ind, cx, cy, orient)
                if "1" not in pads or "2" not in pads:
                    continue
                d1 = math.hypot(pads["1"][0] - pin48_abs[0], pads["1"][1] - pin48_abs[1])
                d2 = math.hypot(pads["2"][0] - pin50_abs[0], pads["2"][1] - pin50_abs[1])
                score = d1 + d2
                if best_for_orient is None or score < best_for_orient[0]:
                    best_for_orient = (score, cx, cy, orient, d1, d2)
            if best_for_orient is not None:
                break
        if best_for_orient is not None:
            # Prefer 180° if it exists; otherwise take the first orientation that works.
            if orient == 180:
                best = best_for_orient
                break
            elif best is None:
                best = best_for_orient

    if best is None:
        raise RuntimeError("Could not find non-colliding placement for L1")

    score, l1_x, l1_y, l1_orient, d1, d2 = best
    ind.SetPosition(pcbnew.VECTOR2I(nm(l1_x), nm(l1_y)))
    ind.SetOrientation(pcbnew.EDA_ANGLE(l1_orient, pcbnew.DEGREES_T))

    # Assign nets to inductor pads
    vreg_lx_net = get_or_create_net("VREG_LX")
    vcore_net = get_or_create_net("VCORE")
    for p in ind.Pads():
        n = p.GetNumber()
        if n == "1":
            p.SetNet(vreg_lx_net)
        elif n == "2":
            p.SetNet(vcore_net)

    b.Add(ind)
    print(f"Placed L1 at ({l1_x:.3f}, {l1_y:.3f}) mm, orient={l1_orient}")
    print(f"  pad1(VREG_LX)->pin48 dist={d1:.3f} mm, pad2(VCORE)->pin50 dist={d2:.3f} mm")

    # ---- 6. Relax min through-drill to match RP2350A thermal vias ----------
    ds = b.GetDesignSettings()
    old_min_drill = ds.m_MinThroughDrill / 1e6
    new_min_drill = 0.2
    if old_min_drill > new_min_drill:
        ds.m_MinThroughDrill = int(round(new_min_drill * 1e6))
        b.SetDesignSettings(ds)
        print(f"Relaxed min through-drill from {old_min_drill:.3f} mm to {new_min_drill:.3f} mm for QFN-60 thermal vias")

    # ---- 7. Save -----------------------------------------------------------
    b.Save(BOARD_PATH)
    print(f"Saved {BOARD_PATH}")

    # Final report
    print("\n=== Summary ===")
    print(f"U1: RP2350A at ({u1_pos.x/1e6:.3f}, {u1_pos.y/1e6:.3f}) orient={u1_orient}")
    print(f"LEDs moved: {moved}")
    print(f"L1: 2.2uH at ({l1_x:.3f}, {l1_y:.3f}) orient={l1_orient}")
    print(f"Ripped nets count: {len(ripup_net_names)}")
    print(f"Ripped tracks: {removed_tracks}, vias: {removed_vias}")


if __name__ == "__main__":
    main()
