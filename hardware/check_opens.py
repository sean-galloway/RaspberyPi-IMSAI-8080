#!/usr/bin/env python3
"""Open-net checker for IMSPI 8080 boards (pad-overlap copper flood-fill).

WHY THIS EXISTS: kicad-cli pcb drc (KiCad 10.0) does NOT report unconnected
nets on this board - verified 2026-10-10: two known opens (HC_QH, TLC_SCLK)
produce zero unconnected_items violations (not DRC exclusions, not severity-
gated, not the prl ratsnest flag). Don't trust kicad-cli for opens; run this
before fab and after every board edit.

Method: for every net, union-find over pads (rotated rects), tracks (segments)
and vias (annulus discs). Two items connect when their copper OVERLAPS on a
shared layer (not when anchors coincide): segment-in-rect, endpoint-on-segment
(<=10um tolerance for junction rounding), annulus-overlap for vias. Zone
connection is layer-aware: only items that exist on the zone's layer can join
the pour (pads: same layer or through-hole; vias: layer pair spanning it;
tracks: same layer). Nets with >1 copper island are reported with membership.
Intentional NC pads (no net) are ignored; documented assembly opens live in
ALLOWLIST.

Usage: python3 check_opens.py [board.kicad_pcb]
Exit code: 0 = all nets single-island (or only allow-listed opens), 1 = opens.
"""
import sys, math, pcbnew
from collections import defaultdict

ALLOWLIST = {
    # net: reason (documented assembly items, fab-rev5/README.txt)
    "HC_QH":    "assembly item 1: ~45mm 30AWG wire U1-12 -> U6-9 (no via possible in pin-12 cluster)",
    "TLC_SCLK": "assembly item 2: ~10mm wire, via (124.32,94.60) -> stub (124.64,102.34)",
    "USB_DP_CONN": "J1-A6 USB-C duplicate D+ pad intentionally NC (plug parallels A6/B6; D+ routed via B6) - rev4",
}
TOL = 10000    # 0.01 mm junction tolerance (board min clearance is 0.127 mm)
ZSTEP = 50000  # 0.05 mm zone probe grid


def pt_seg_dist(p, a, bb):
    dx, dy = bb[0]-a[0], bb[1]-a[1]
    L2 = dx*dx + dy*dy or 1
    t = max(0.0, min(1.0, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L2))
    return math.hypot(p[0]-(a[0]+t*dx), p[1]-(a[1]+t*dy))


def pt_rect_dist(p, rect):
    cx, cy, hw, hh = rect
    return math.hypot(max(abs(p[0]-cx)-hw, 0), max(abs(p[1]-cy)-hh, 0))


def segs_cross(p1, p2, p3, p4):
    def o(a, c, d):
        return (d[0]-c[0])*(a[1]-c[1]) - (d[1]-c[1])*(a[0]-c[0])
    d1, d2 = o(p3, p1, p2), o(p4, p1, p2)
    d3, d4 = o(p1, p3, p4), o(p2, p3, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def seg_rect_touch(seg, rect):
    a, bb = seg
    if pt_rect_dist(a, rect) == 0 or pt_rect_dist(bb, rect) == 0:
        return True
    cx, cy, hw, hh = rect
    corners = [(cx-hw, cy-hh), (cx+hw, cy-hh), (cx+hw, cy+hh), (cx-hw, cy+hh)]
    return any(segs_cross(a, bb, e1, e2) for e1, e2 in zip(corners, corners[1:]+corners[:1]))


def pad_rect(p):
    sz = p.GetSize()
    hw, hh = sz.x/2, sz.y/2
    if int(p.GetOrientation().AsDegrees()) % 180 != 0:
        hw, hh = hh, hw
    return (p.GetPosition().x, p.GetPosition().y, hw, hh)


def via_radius(v):
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
        try:
            w = v.GetWidth(layer)
            if w > 0:
                return w/2
        except Exception:
            pass
    try:
        return v.GetDrillValue()/2 + 100000  # fallback: ring around drill
    except Exception:
        return 150000  # 0.15 mm default annulus radius


def main(path):
    b = pcbnew.LoadBoard(path)
    fills = [(zn.GetLayer(), zn.GetFill(zn.GetLayer())) for zn in b.Zones()]
    zone_layers = {L for L, _ in fills}

    net_items = defaultdict(lambda: {"pads": [], "vias": [], "segs": []})
    for f in b.GetFootprints():
        for p in f.Pads():
            net_items[p.GetNetname()]["pads"].append((p, f"{f.GetReference()}-{p.GetNumber()}"))
    for t in b.Tracks():
        nn = t.GetNetname() if hasattr(t, "GetNetname") else t.GetNetName()
        if "VIA" in type(t).__name__:
            net_items[nn]["vias"].append((t, f"via@({t.GetPosition().x/1e6:.2f},{t.GetPosition().y/1e6:.2f})"))
        else:
            net_items[nn]["segs"].append((t, "trk"))

    def pad_is_pth(p):
        try:
            return p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        except Exception:
            return False

    def pad_hits_fill(rect, layers):
        cx, cy, hw, hh = rect
        gx = cx - int(hw)
        while gx <= cx + int(hw):
            gy = cy - int(hh)
            while gy <= cy + int(hh):
                pt = pcbnew.VECTOR2I(gx, gy)
                for L, ps in fills:
                    if L in layers and ps.PointInside(pt):
                        return True
                gy += ZSTEP
            gx += ZSTEP
        return False

    found = {}
    for net, d in sorted(net_items.items()):
        if net == "":
            continue
        nodes = []
        for p, lbl in d["pads"]:
            nodes.append(("pad", {"rect": pad_rect(p), "pad": p}, lbl))
        for v, lbl in d["vias"]:
            nodes.append(("via", {"c": (v.GetPosition().x, v.GetPosition().y),
                                  "r": via_radius(v),
                                  "top": v.TopLayer(), "bot": v.BottomLayer()}, lbl))
        for t, lbl in d["segs"]:
            nodes.append(("seg", {"a": (t.GetStart().x, t.GetStart().y),
                                  "b": (t.GetEnd().x, t.GetEnd().y),
                                  "layer": t.GetLayer()}, lbl))
        n = len(nodes)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def connects(i, j):
            ki, kj = nodes[i][0], nodes[j][0]
            if ki == "seg" and kj == "seg":
                g, h = nodes[i][1], nodes[j][1]
                if g["layer"] != h["layer"]:
                    return False
                s1, e1, s2, e2 = g["a"], g["b"], h["a"], h["b"]
                return (segs_cross(s1, e1, s2, e2)
                        or pt_seg_dist(s1, s2, e2) <= TOL or pt_seg_dist(e1, s2, e2) <= TOL
                        or pt_seg_dist(s2, s1, e1) <= TOL or pt_seg_dist(e2, s1, e1) <= TOL)
            if ki == "seg" and kj == "pad":
                g = nodes[i][1]
                return seg_rect_touch((g["a"], g["b"]), nodes[j][1]["rect"])
            if ki == "pad" and kj == "seg":
                g = nodes[j][1]
                return seg_rect_touch((g["a"], g["b"]), nodes[i][1]["rect"])
            if ki == "seg" and kj == "via":
                return pt_seg_dist(nodes[j][1]["c"], nodes[i][1]["a"], nodes[i][1]["b"]) <= nodes[j][1]["r"]
            if ki == "via" and kj == "seg":
                return pt_seg_dist(nodes[i][1]["c"], nodes[j][1]["a"], nodes[j][1]["b"]) <= nodes[i][1]["r"]
            if ki == "via" and kj == "via":
                c1, r1 = nodes[i][1]["c"], nodes[i][1]["r"]
                c2, r2 = nodes[j][1]["c"], nodes[j][1]["r"]
                return math.hypot(c1[0]-c2[0], c1[1]-c2[1]) <= r1 + r2
            if ki == "via" and kj == "pad":
                return pt_rect_dist(nodes[i][1]["c"], nodes[j][1]["rect"]) <= nodes[i][1]["r"]
            if ki == "pad" and kj == "via":
                return pt_rect_dist(nodes[j][1]["c"], nodes[i][1]["rect"]) <= nodes[j][1]["r"]
            return False

        for i in range(n):
            for j in range(i+1, n):
                if connects(i, j):
                    parent[find(i)] = find(j)

        # zone (pour) membership -- layer-aware
        pour = []
        for i, (k, g, _) in enumerate(nodes):
            hit = False
            if k == "pad":
                p = g["pad"]
                layers = set(zone_layers) if pad_is_pth(p) else ({p.GetLayer()} & zone_layers)
                hit = bool(layers) and pad_hits_fill(g["rect"], layers)
            elif k == "via":
                c = g["c"]
                lo, hi = min(g["top"], g["bot"]), max(g["top"], g["bot"])
                for L, ps in fills:
                    if lo <= L <= hi and ps.PointInside(pcbnew.VECTOR2I(c[0], c[1])):
                        hit = True
                        break
            else:
                if g["layer"] in zone_layers:
                    pt1 = pcbnew.VECTOR2I(g["a"][0], g["a"][1])
                    pt2 = pcbnew.VECTOR2I(g["b"][0], g["b"][1])
                    for L, ps in fills:
                        if L == g["layer"] and (ps.PointInside(pt1) or ps.PointInside(pt2)):
                            hit = True
                            break
            if hit:
                pour.append(i)
        for a in pour:
            for c in pour:
                parent[find(a)] = find(c)

        groups = defaultdict(list)
        for i in range(n):
            groups[find(i)].append(nodes[i][2])
        if len(groups) > 1:
            found[net] = [sorted(set(g)) for g in groups.values()]

    unexpected = {k: v for k, v in found.items() if k not in ALLOWLIST}
    print(f"{'net':14s} islands  detail")
    for net, groups in found.items():
        tag = "(allow-listed: %s)" % ALLOWLIST[net] if net in ALLOWLIST else "<-- UNEXPECTED OPEN"
        print(f"{net:14s} {len(groups):4d}     {tag}")
        for g in groups:
            print("    ", g[:8], "..." if len(g) > 8 else "")
    if not found:
        print("OK: every net is a single copper island")
        return 0
    if unexpected:
        print(f"\nFAIL: {len(unexpected)} unexpected open net(s): {', '.join(unexpected)}")
        return 1
    print(f"\nOK: {len(found)} open net(s), all documented in ALLOWLIST")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "imspi8080_rev5.kicad_pcb"))
