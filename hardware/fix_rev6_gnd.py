#!/usr/bin/env python3
"""Fix GND opens on imspi8080_rev6.kicad_pcb.

Adds short F.Cu (or pad-layer) tracks from isolated GND pads to new GND vias
that land in the B.Cu GND pour.
"""
import sys, math, importlib.util, io, contextlib
import pcbnew

BOARD = "/home/seang/github/RaspberyPi-IMSAI-8080/hardware/imspi8080_rev6.kicad_pcb"

# import check_opens helpers
spec = importlib.util.spec_from_file_location("check_opens", "/home/seang/github/RaspberyPi-IMSAI-8080/hardware/check_opens.py")
co = importlib.util.module_from_spec(spec)
spec.loader.exec_module(co)

TOL = co.TOL
ZSTEP = co.ZSTEP
pt_seg_dist = co.pt_seg_dist
pt_rect_dist = co.pt_rect_dist
segs_cross = co.segs_cross
seg_rect_touch = co.seg_rect_touch
pad_rect = co.pad_rect
via_radius = co.via_radius

TRACK_WIDTH = 250000
VIA_WIDTH = 600000
VIA_DRILL = 300000


class SpatialBins:
    """Uniform grid spatial index for fast bounding-box queries."""

    def __init__(self, items, size_nm=2000000):
        self.size = size_nm
        self.bins = {}
        for item, bbox in items:
            for key in self._keys(bbox):
                self.bins.setdefault(key, []).append((item, bbox))

    def _keys(self, bbox):
        minx, miny, maxx, maxy = bbox
        keys = []
        x = int(minx / self.size) * self.size
        while x <= maxx:
            y = int(miny / self.size) * self.size
            while y <= maxy:
                keys.append((x, y))
                y += self.size
            x += self.size
        return keys

    def query(self, bbox):
        result = []
        seen = set()
        for key in self._keys(bbox):
            for item, _ in self.bins.get(key, []):
                iid = id(item)
                if iid in seen:
                    continue
                seen.add(iid)
                result.append(item)
        return result


def pad_hits_fill(rect, fills, layers):
    """Copy of check_opens.pad_hits_fill (parameterized over fills)."""
    cx, cy, hw, hh = rect
    halfdiag = int((hw**2 + hh**2) ** 0.5)
    pts = []
    gx = cx - int(hw)
    while gx <= cx + int(hw):
        gy = cy - int(hh)
        while gy <= cy + int(hh):
            pts.append((gx, gy)); gy += ZSTEP
        gx += ZSTEP
    for r in (halfdiag + 60000, halfdiag + 160000, halfdiag + 260000,
              halfdiag + 360000, halfdiag + 460000, halfdiag + 560000):
        for k in range(16):
            pts.append((cx + int(r * math.cos(k * math.pi / 8)),
                        cy + int(r * math.sin(k * math.pi / 8))))
    for px, py in pts:
        pt = pcbnew.VECTOR2I(px, py)
        for L, ps in fills:
            if L in layers and ps.PointInside(pt):
                return True
    return False


def run_check_opens(path):
    """Run check_opens.main() and parse open GND groups."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ret = co.main(path)
    out = buf.getvalue()
    groups = []
    in_gnd = False
    for line in out.splitlines():
        if line.startswith("GND "):
            in_gnd = True
            continue
        if in_gnd:
            if line.startswith("     "):
                txt = line.strip().replace(" ...", "")
                members = eval(txt)
                groups.append(members)
            elif line.strip() == "" or line.startswith("FAIL") or line.startswith("OK"):
                in_gnd = False
            elif not line.startswith("     "):
                in_gnd = False
    return groups, ret


def load_board():
    return pcbnew.LoadBoard(BOARD)


def _make_bins(idx):
    def track_bbox(t):
        x1, y1 = t.GetStart().x, t.GetStart().y
        x2, y2 = t.GetEnd().x, t.GetEnd().y
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    def via_bbox(v):
        r = via_radius(v)
        x, y = v.GetPosition().x, v.GetPosition().y
        return (x - r, y - r, x + r, y + r)
    def pad_bbox(pb):
        p, ref = pb
        cx, cy, hw, hh = pad_rect(p)
        return (cx - hw, cy - hh, cx + hw, cy + hh)
    idx["track_bins"] = SpatialBins([(t, track_bbox(t)) for t in idx["tracks"]])
    idx["via_bins"] = SpatialBins([(v, via_bbox(v)) for v in idx["vias"]])
    idx["pad_bins"] = SpatialBins([(pb, pad_bbox(pb)) for pb in idx["pads"]])


def build_index(b):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    pads = []
    for f in b.GetFootprints():
        for p in f.Pads():
            pads.append((p, f.GetReference()))
    tracks = []
    vias = []
    orig_gnd_via_positions = []
    for t in b.Tracks():
        if "VIA" in type(t).__name__:
            vias.append(t)
            if t.GetNetname() == "GND":
                orig_gnd_via_positions.append((t.GetPosition().x, t.GetPosition().y))
        else:
            tracks.append(t)
    zones = [(zn.GetLayer(), zn.GetFill(zn.GetLayer())) for zn in b.Zones()]
    bc_zone_ps = None
    for L, ps in zones:
        if L == pcbnew.B_Cu:
            bc_zone_ps = ps
            break
    main_component = compute_main_zone_component(bc_zone_ps, orig_gnd_via_positions)
    idx = {"fps": fps, "pads": pads, "tracks": tracks, "vias": vias,
           "zones": zones, "bc_zone_ps": bc_zone_ps,
           "main_component": main_component}
    _make_bins(idx)
    return idx


def compute_main_zone_component(bc_zone_ps, seed_positions, step=100000, margin=2000000):
    """Return a set of (x,y) grid points in the main B.Cu zone island.

    Flood-fill the B.Cu zone polygon from the original GND via positions.
    Board extents are inferred from seed positions plus margin (mm*1e6).
    """
    if bc_zone_ps is None or not seed_positions:
        return None
    # determine bounding box
    xs = [p[0] for p in seed_positions]
    ys = [p[1] for p in seed_positions]
    min_x, max_x = min(xs) - margin, max(xs) + margin
    min_y, max_y = min(ys) - margin, max(ys) + margin
    # quantize seeds to grid
    def q(v):
        return int(v / step) * step
    seeds = set()
    for x, y in seed_positions:
        gx, gy = q(x), q(y)
        if min_x <= gx <= max_x and min_y <= gy <= max_y:
            pt = pcbnew.VECTOR2I(gx, gy)
            if bc_zone_ps.PointInside(pt):
                seeds.add((gx, gy))
    if not seeds:
        return None
    component = set(seeds)
    stack = list(seeds)
    # pre-bound grid coordinates
    x_vals = list(range(int(min_x / step) * step, int(max_x / step) * step + 1, step))
    y_vals = list(range(int(min_y / step) * step, int(max_y / step) * step + 1, step))
    x_set = set(x_vals)
    y_set = set(y_vals)
    while stack:
        cx, cy = stack.pop()
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in component:
                continue
            if nx not in x_set or ny not in y_set:
                continue
            pt = pcbnew.VECTOR2I(nx, ny)
            if bc_zone_ps.PointInside(pt):
                component.add((nx, ny))
                stack.append((nx, ny))
    return component


def pad_is_pth(p):
    try:
        return p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
    except Exception:
        return False


def footprint_bbox_mm(f):
    bb = f.GetBoundingBox()
    return (bb.GetX()/1e6, bb.GetY()/1e6, bb.GetWidth()/1e6, bb.GetHeight()/1e6)


def bbox_contains_point(bbox, x, y, margin=0.0):
    bx, by, bw, bh = bbox
    return (bx - margin <= x <= bx + bw + margin) and (by - margin <= y <= by + bh + margin)


def track_distance_nm(x_nm, y_nm, tracks, layers=None):
    """Minimum distance from point (nm) to any track segment (nm)."""
    best = float('inf')
    for t in tracks:
        if layers is not None and t.GetLayer() not in layers:
            continue
        d = pt_seg_dist((x_nm, y_nm),
                        (t.GetStart().x, t.GetStart().y),
                        (t.GetEnd().x, t.GetEnd().y))
        if d < best:
            best = d
    return best


def segment_clear(p1_nm, p2_nm, own_pad, own_ref, pads, tracks, vias, fps,
                  pad_bins=None, track_bins=None, via_bins=None):
    """Check track segment p1->p2 doesn't violate clearance.

    Allows pads/tracks/vias that share an endpoint or that are on the same
    GND net. Checks the full segment, including the portion near the pad,
    because a thin stub can still short to a foreign track that passes near
    the pad edge.
    """
    endpoints = {p1_nm, p2_nm}
    layer = pad_copper_layer(own_pad)
    own_net = own_pad.GetNetname()
    seg = (p1_nm, p2_nm)

    def pad_iter():
        if pad_bins is not None:
            minx = min(seg[0][0], seg[1][0]) - 400000
            miny = min(seg[0][1], seg[1][1]) - 400000
            maxx = max(seg[0][0], seg[1][0]) + 400000
            maxy = max(seg[0][1], seg[1][1]) + 400000
            return pad_bins.query((minx, miny, maxx, maxy))
        return pads

    def track_iter():
        if track_bins is not None:
            minx = min(seg[0][0], seg[1][0]) - TRACK_WIDTH//2 - 300000
            miny = min(seg[0][1], seg[1][1]) - TRACK_WIDTH//2 - 300000
            maxx = max(seg[0][0], seg[1][0]) + TRACK_WIDTH//2 + 300000
            maxy = max(seg[0][1], seg[1][1]) + TRACK_WIDTH//2 + 300000
            return track_bins.query((minx, miny, maxx, maxy))
        return tracks

    def via_iter():
        if via_bins is not None:
            minx = min(seg[0][0], seg[1][0]) - VIA_WIDTH//2 - TRACK_WIDTH//2 - 300000
            miny = min(seg[0][1], seg[1][1]) - VIA_WIDTH//2 - TRACK_WIDTH//2 - 300000
            maxx = max(seg[0][0], seg[1][0]) + VIA_WIDTH//2 + TRACK_WIDTH//2 + 300000
            maxy = max(seg[0][1], seg[1][1]) + VIA_WIDTH//2 + TRACK_WIDTH//2 + 300000
            return via_bins.query((minx, miny, maxx, maxy))
        return vias

    # distance to other pads (only pads present on this layer)
    for p, ref in pad_iter():
        if ref == own_ref and p == own_pad:
            continue
        if not p.IsOnLayer(layer):
            continue
        if p.GetNetname() == own_net:
            continue
        rect = pad_rect(p)
        pc = (p.GetPosition().x, p.GetPosition().y)
        if pc in endpoints:
            continue
        if pt_rect_dist(seg[0], rect) <= TRACK_WIDTH//2 + 200000 or pt_rect_dist(seg[1], rect) <= TRACK_WIDTH//2 + 200000:
            return False
        inflated = (rect[0], rect[1], rect[2] + TRACK_WIDTH//2 + 200000, rect[3] + TRACK_WIDTH//2 + 200000)
        if seg_rect_touch(seg, inflated):
            return False
    # distance to tracks on the same layer
    for t in track_iter():
        if t.GetLayer() != layer:
            continue
        if t.GetNetname() == own_net:
            continue
        a = (t.GetStart().x, t.GetStart().y)
        bb = (t.GetEnd().x, t.GetEnd().y)
        if a in endpoints and bb in endpoints:
            continue
        # full segment-segment clearance check (catches mid-segment crossings)
        if segs_cross(seg[0], seg[1], a, bb):
            return False
        min_seg_dist = min(pt_seg_dist(a, seg[0], seg[1]),
                           pt_seg_dist(bb, seg[0], seg[1]),
                           pt_seg_dist(seg[0], a, bb),
                           pt_seg_dist(seg[1], a, bb))
        if min_seg_dist <= TRACK_WIDTH + 200000:
            return False
    # distance to vias (a through-hole via spans every copper layer)
    for v in via_iter():
        if v.GetNetname() == own_net:
            continue
        vc = (v.GetPosition().x, v.GetPosition().y)
        if vc in endpoints:
            continue
        vr = via_radius(v)
        # edge-to-edge clearance: via radius + track half-width + margin
        if pt_seg_dist(vc, seg[0], seg[1]) <= vr + TRACK_WIDTH//2 + 200000:
            return False
    return True


COPPER_LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

# Distance from an SMD pad edge to a new GND via centre.  The B.Cu GND zone
# keeps a 0.5 mm clearance hole around every pad and uses a 0.2 mm thermal
# gap around vias.  To leave room for thermal-relief spokes we must place the
# via outside that combined hole: 0.5 (zone clearance) + 0.3 (via radius) +
# 0.2 (thermal gap) + 0.1 mm margin.
SMD_PAD_TO_VIA_CENTER_NM = 1100000


def via_clear_ok(x_mm, y_mm, own_pad, own_ref, pads, tracks, vias, fps, bc_zone_ps,
                 pad_bins=None, track_bins=None, via_bins=None):
    """Check via placement clearance constraints and B.Cu pour membership.

    Clearances are edge-to-edge: pad edge >=0.35mm from via edge;
    track edge >=0.2mm from via edge; via edge >=0.5mm from other via edge.
    A through-hole via spans every copper layer, so we must clear tracks and
    pads on In1.Cu/In2.Cu as well as F.Cu/B.Cu.

    SMD pads (including same-net and the pad we are fixing) create a B.Cu
    zone clearance hole; the via must sit outside that hole or it will dangle.
    """
    x_nm, y_nm = int(x_mm * 1e6), int(y_mm * 1e6)
    via_r = VIA_WIDTH // 2
    # inside B.Cu pour
    if bc_zone_ps is not None:
        if not bc_zone_ps.PointInside(pcbnew.VECTOR2I(x_nm, y_nm)):
            return False
    own_net = own_pad.GetNetname() if own_pad is not None else "GND"

    def pad_is_smd(p):
        try:
            return p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
        except Exception:
            return False

    def pad_iter():
        if pad_bins is not None:
            return pad_bins.query((x_nm - SMD_PAD_TO_VIA_CENTER_NM - via_r,
                                   y_nm - SMD_PAD_TO_VIA_CENTER_NM - via_r,
                                   x_nm + SMD_PAD_TO_VIA_CENTER_NM + via_r,
                                   y_nm + SMD_PAD_TO_VIA_CENTER_NM + via_r))
        return pads

    def track_iter():
        if track_bins is not None:
            return track_bins.query((x_nm - via_r - 500000,
                                   y_nm - via_r - 500000,
                                   x_nm + via_r + 500000,
                                   y_nm + via_r + 500000))
        return tracks

    def via_iter():
        if via_bins is not None:
            return via_bins.query((x_nm - via_r - VIA_WIDTH - 500000,
                                   y_nm - via_r - VIA_WIDTH - 500000,
                                   x_nm + via_r + VIA_WIDTH + 500000,
                                   y_nm + via_r + VIA_WIDTH + 500000))
        return vias

    # All SMD pads (own, same-net, and foreign) create a B.Cu clearance hole.
    # Keep the via outside that hole so thermal spokes can reach it.
    check_pads = list(pad_iter())
    if own_pad is not None:
        check_pads.append((own_pad, own_ref))
    for p, ref in check_pads:
        if not pad_is_smd(p):
            continue
        if not any(p.IsOnLayer(L) for L in COPPER_LAYERS):
            continue
        rect = pad_rect(p)
        if pt_rect_dist((x_nm, y_nm), rect) < SMD_PAD_TO_VIA_CENTER_NM:
            return False

    # other pads: edge-to-edge >= 0.35 mm (any copper layer the via spans)
    for p, ref in pad_iter():
        if ref == own_ref and p == own_pad:
            continue
        if p.GetNetname() == own_net:
            continue
        if not any(p.IsOnLayer(L) for L in COPPER_LAYERS):
            continue
        rect = pad_rect(p)
        if pt_rect_dist((x_nm, y_nm), rect) <= via_r + 180000:
            return False
    # tracks: edge-to-edge >= ~0.18 mm on any copper layer
    if track_distance_nm(x_nm, y_nm,
                        [t for t in track_iter() if t.GetNetname() != own_net],
                        layers=set(COPPER_LAYERS)) <= via_r + 180000:
        return False
    # other vias: edge-to-edge >= 0.5 mm
    for v in via_iter():
        if v.GetNetname() == own_net:
            continue
        d = math.hypot(v.GetPosition().x - x_nm, v.GetPosition().y - y_nm)
        if d <= via_r + via_radius(v) + 500000:
            return False
    # not inside other footprint courtyard bbox
    for r, f in fps.items():
        if r == own_ref:
            continue
        bb = footprint_bbox_mm(f)
        if bbox_contains_point(bb, x_mm, y_mm):
            return False
    return True


def pad_long_axis(p):
    """Return unit vector along pad's long axis (pad coords, degrees 0/90/...)."""
    sz = p.GetSize()
    orient = int(p.GetOrientation().AsDegrees()) % 360
    if sz.x >= sz.y:
        rad = math.radians(orient)
    else:
        rad = math.radians((orient + 90) % 360)
    return (math.cos(rad), math.sin(rad))


def candidate_positions(px_mm, py_mm, long_axis, max_mm=25.0):
    """Generate candidate via positions: long axis first, then dense radial sweep."""
    lx, ly = long_axis
    # long axis both directions (preferred)
    for d in [x/10.0 for x in range(5, int(max_mm*10)+1)]:
        yield (px_mm + d*lx, py_mm + d*ly)
        yield (px_mm - d*lx, py_mm - d*ly)
    # dense radial sweep
    for d in [x/10.0 for x in range(5, int(max_mm*10)+1)]:
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            dx, dy = math.cos(rad), math.sin(rad)
            yield (px_mm + d*dx, py_mm + d*dy)


def via_hits_existing_gnd(x_nm, y_nm, idx):
    """Return True if a via centred at (x_nm,y_nm) would touch existing GND copper.

    A new via must overlap an existing GND via, a GND track, or a GND PTH pad so
    that it actually connects after the zone is refilled.  Sitting inside the
    raw zone polygon is not enough; the refilled zone may leave the via dangling.
    """
    via_r = VIA_WIDTH // 2
    search_bbox = (x_nm - via_r - VIA_WIDTH, y_nm - via_r - VIA_WIDTH,
                   x_nm + via_r + VIA_WIDTH, y_nm + via_r + VIA_WIDTH)
    vias = idx.get("via_bins", None)
    tracks = idx.get("track_bins", None)
    pads = idx.get("pad_bins", None)
    # existing GND vias
    for v in (vias.query(search_bbox) if vias else idx["vias"]):
        if v.GetNetname() != "GND":
            continue
        vc = (v.GetPosition().x, v.GetPosition().y)
        vr = via_radius(v)
        if math.hypot(vc[0] - x_nm, vc[1] - y_nm) <= via_r + vr:
            return True
    # existing GND tracks
    for t in (tracks.query(search_bbox) if tracks else idx["tracks"]):
        if t.GetNetname() != "GND":
            continue
        a = (t.GetStart().x, t.GetStart().y)
        bb = (t.GetEnd().x, t.GetEnd().y)
        if pt_seg_dist((x_nm, y_nm), a, bb) <= via_r + t.GetWidth() // 2:
            return True
    # GND PTH pads
    for p, ref in (pads.query(search_bbox) if pads else idx["pads"]):
        if p.GetNetname() != "GND":
            continue
        try:
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                continue
        except Exception:
            continue
        rect = pad_rect(p)
        if pt_rect_dist((x_nm, y_nm), rect) <= via_r:
            return True
    return False


def find_via_pos(pad, idx):
    own_ref = pad.GetParentFootprint().GetReference()
    cx_mm = pad.GetPosition().x / 1e6
    cy_mm = pad.GetPosition().y / 1e6
    axis = pad_long_axis(pad)
    for x_mm, y_mm in candidate_positions(cx_mm, cy_mm, axis):
        x_nm, y_nm = int(x_mm*1e6), int(y_mm*1e6)
        if not via_clear_ok(x_mm, y_mm, pad, own_ref, idx["pads"], idx["tracks"],
                            idx["vias"], idx["fps"], idx["bc_zone_ps"],
                            pad_bins=idx.get("pad_bins"),
                            track_bins=idx.get("track_bins"),
                            via_bins=idx.get("via_bins")):
            continue
        # the via must actually connect to existing GND copper
        if not via_hits_existing_gnd(x_nm, y_nm, idx):
            continue
        # also verify the stub track is clear
        p1_nm = (pad.GetPosition().x, pad.GetPosition().y)
        if segment_clear(p1_nm, (x_nm, y_nm), pad, own_ref, idx["pads"], idx["tracks"],
                         idx["vias"], idx["fps"],
                         pad_bins=idx.get("pad_bins"),
                         track_bins=idx.get("track_bins"),
                         via_bins=idx.get("via_bins")):
            return (x_nm, y_nm)
    return None


def add_track_to_point(b, pad, end_nm):
    """Add a short track from pad center to end_nm on pad's copper layer."""
    return add_track_between(b, pad.GetNet(), pad_copper_layer(pad),
                             (pad.GetPosition().x, pad.GetPosition().y), end_nm)


def add_track_between(b, net, layer, start_nm, end_nm):
    """Add a track between two points on the given layer/net."""
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(start_nm[0], start_nm[1]))
    t.SetEnd(pcbnew.VECTOR2I(end_nm[0], end_nm[1]))
    t.SetWidth(TRACK_WIDTH)
    t.SetLayer(layer)
    t.SetNet(net)
    b.Add(t)
    return t


def try_connect_to_existing_gnd(pad, idx, max_mm=40.0):
    """Try to connect pad to an existing GND item with a clear routed track.

    Tries a straight track first, then L-shaped tracks through the two
    canonical corners.  Returns a list of points [pad_center, ..., target]
    if a route is found, else None.  Avoids creating dangling vias.
    """
    own_ref = pad.GetParentFootprint().GetReference()
    p1_nm = (pad.GetPosition().x, pad.GetPosition().y)
    layer = pad_copper_layer(pad)

    # collect candidate targets
    targets = []
    for v in idx["vias"]:
        if v.GetNetname() == "GND":
            targets.append(("via", (v.GetPosition().x, v.GetPosition().y)))
    for p, ref in idx["pads"]:
        if ref == own_ref and p == pad:
            continue
        if p.GetNetname() != "GND" or not p.IsOnLayer(layer):
            continue
        targets.append(("pad", (p.GetPosition().x, p.GetPosition().y)))
    for t in idx["tracks"]:
        if t.GetNetname() != "GND" or t.GetLayer() != layer:
            continue
        targets.append(("trk", (t.GetStart().x, t.GetStart().y)))
        targets.append(("trk", (t.GetEnd().x, t.GetEnd().y)))
    targets.sort(key=lambda x: math.hypot(x[1][0]-p1_nm[0], x[1][1]-p1_nm[1]))

    def route_len(pts):
        return sum(math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
                   for i in range(len(pts)-1))

    best = None
    best_len = float('inf')

    def record(pts):
        nonlocal best, best_len
        L = route_len(pts)
        if L > max_mm * 1e6 or L >= best_len:
            return
        # verify every segment is clear
        for i in range(len(pts)-1):
            if not segment_clear(pts[i], pts[i+1], pad, own_ref, idx["pads"],
                                 idx["tracks"], idx["vias"], idx["fps"],
                                 pad_bins=idx.get("pad_bins"),
                                 track_bins=idx.get("track_bins"),
                                 via_bins=idx.get("via_bins")):
                return
        best_len = L
        best = pts

    for _, end in targets[:30]:
        # direct
        record([p1_nm, end])
        if best is not None:
            return best
        # L-shaped via grid around canonical corners
        margin = 3000000
        step = 500000
        minx, maxx = min(p1_nm[0], end[0]) - margin, max(p1_nm[0], end[0]) + margin
        miny, maxy = min(p1_nm[1], end[1]) - margin, max(p1_nm[1], end[1]) + margin
        x = minx
        while x <= maxx:
            y = miny
            while y <= maxy:
                record([p1_nm, (int(x), end[1]), end])
                record([p1_nm, (end[0], int(y)), end])
                y += step
            x += step
        if best is not None:
            return best

    return best


def pad_copper_layer(pad):
    """Return the copper layer an SMD pad actually lives on.

    KiCad's pad.GetLayer() can lie for back-side SMD pads (reporting F.Cu
    when copper is really on B.Cu). Some footprints also place an SMD pad
    on the opposite side from the footprint itself (e.g. bottom thermal
    pad of a top-side QFN). We handle both cases.
    """
    if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
        return pad.GetLayer()
    fp_layer = pad.GetParentFootprint().GetLayer()
    pad_layer = pad.GetLayer()
    # Back-side flipped footprint workaround
    if fp_layer == pcbnew.B_Cu and pad_layer == pcbnew.F_Cu:
        return fp_layer
    # Trust the pad's actual layer set when it tells a different story
    for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        if pad.IsOnLayer(L):
            return L
    return pad_layer


def add_track_via(b, pad, via_pos_nm):
    # use the pad's net object directly; GND is the only net we ever add
    net = pad.GetNet()
    layer = pad_copper_layer(pad)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pad.GetPosition())
    t.SetEnd(pcbnew.VECTOR2I(via_pos_nm[0], via_pos_nm[1]))
    t.SetWidth(TRACK_WIDTH)
    t.SetLayer(layer)
    t.SetNet(net)
    b.Add(t)
    v = pcbnew.PCB_VIA(b)
    v.SetWidth(VIA_WIDTH)
    v.SetDrill(VIA_DRILL)
    v.SetPosition(pcbnew.VECTOR2I(via_pos_nm[0], via_pos_nm[1]))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    b.Add(v)
    return t, v


def find_bridge_via_pos(secondary_via_pos_nm, idx, max_mm=20.0):
    """Find a clear via position in the main B.Cu island for a bridge.

    Search radially around the secondary-island via toward the closest
    original/main-island GND via anchor.
    """
    sx, sy = secondary_via_pos_nm[0] / 1e6, secondary_via_pos_nm[1] / 1e6
    # anchors: original GND via positions (in main island)
    anchors = []
    for t in idx["vias"]:
        if t.GetNetname() == "GND":
            anchors.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6))
    if not anchors:
        return None
    # pick closest anchor
    anchors.sort(key=lambda a: math.hypot(a[0]-sx, a[1]-sy))
    ax, ay = anchors[0]
    # search along rays toward anchor and around it
    dx, dy = ax - sx, ay - sy
    base_len = math.hypot(dx, dy) or 1
    ux, uy = dx / base_len, dy / base_len
    candidates = []
    # radial steps toward anchor
    for r in [x/10.0 for x in range(5, int(max_mm*10)+1)]:
        candidates.append((sx + r*ux, sy + r*uy))
    # compass directions
    for d in [x/10.0 for x in range(5, int(max_mm*10)+1)]:
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            candidates.append((sx + d*math.cos(rad), sy + d*math.sin(rad)))
    main_comp = idx.get("main_component")
    for x_mm, y_mm in candidates:
        x_nm, y_nm = int(x_mm*1e6), int(y_mm*1e6)
        # must be in main B.Cu island
        if idx["bc_zone_ps"] is not None:
            if not idx["bc_zone_ps"].PointInside(pcbnew.VECTOR2I(x_nm, y_nm)):
                continue
        if main_comp is not None:
            step = 100000
            qx = int(x_nm/step)*step
            qy = int(y_nm/step)*step
            if (qx, qy) not in main_comp:
                continue
        # clearance (use a dummy own_pad/ref since we don't own a pad here)
        if not via_clear_ok(x_mm, y_mm, None, "", idx["pads"], idx["tracks"],
                            idx["vias"], idx["fps"], idx["bc_zone_ps"],
                            pad_bins=idx.get("pad_bins"),
                            track_bins=idx.get("track_bins"),
                            via_bins=idx.get("via_bins")):
            continue
        return (x_nm, y_nm)
    return None


def add_bridge(b, from_via_pos_nm, to_via_pos_nm):
    """Add a F.Cu track between two via tops."""
    net = b.FindNet("GND")
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(from_via_pos_nm[0], from_via_pos_nm[1]))
    t.SetEnd(pcbnew.VECTOR2I(to_via_pos_nm[0], to_via_pos_nm[1]))
    t.SetWidth(TRACK_WIDTH)
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(net)
    b.Add(t)
    v = pcbnew.PCB_VIA(b)
    v.SetWidth(VIA_WIDTH)
    v.SetDrill(VIA_DRILL)
    v.SetPosition(pcbnew.VECTOR2I(to_via_pos_nm[0], to_via_pos_nm[1]))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    b.Add(v)
    return t, v


def bridge_remaining_islands(b, idx, added, save_path):
    """After first pass, add F.Cu bridges from secondary GND islands to main."""
    # save current state and run check_opens
    pcbnew.SaveBoard(save_path, b)
    import subprocess
    subprocess.run([
        "kicad-cli", "pcb", "drc",
        "--format", "json",
        "--output", "/tmp/rev6-drc.json",
        "--save-board", "--refill-zones",
        save_path
    ], check=True, capture_output=True)
    groups, ret = run_check_opens(save_path)
    if ret == 0:
        return [], []
    # identify main island = largest group
    main_idx = max(range(len(groups)), key=lambda i: len(groups[i]))
    main_group = groups[main_idx]
    # map from via position label to actual nm position from added list
    added_by_label = {lbl: pos for lbl, pos in added}
    bridges = []
    failed = []
    for gi, g in enumerate(groups):
        if gi == main_idx:
            continue
        _make_bins(idx)
        # find a via member in this group
        via_label = None
        for m in g:
            if m.startswith("via@("):
                via_label = m
                break
        if via_label is None:
            # no via in group; find a pad and add a fresh via
            pad_label = None
            for m in g:
                if "-" in m and "via@" not in m and "trk" not in m:
                    pad_label = m
                    break
            if pad_label is None:
                failed.append(g)
                continue
            ref, num = pad_label.rsplit("-", 1)
            fp = idx["fps"].get(ref)
            if fp is None:
                failed.append(g)
                continue
            p = fp.FindPadByNumber(num)
            if p is None:
                failed.append(g)
                continue
            via_pos = find_via_pos(p, idx)
            if via_pos is not None:
                t, v = add_track_via(b, p, via_pos)
                idx["tracks"].append(t)
                idx["vias"].append(v)
                via_label = f"via@({v.GetPosition().x/1e6:.2f},{v.GetPosition().y/1e6:.2f})"
                bridges.append((pad_label, via_label))
            else:
                # fallback: connect pad to an existing GND item
                route = try_connect_to_existing_gnd(p, idx)
                if route is None:
                    failed.append(g)
                    continue
                for i in range(len(route)-1):
                    t = add_track_between(b, p.GetNet(), pad_copper_layer(p), route[i], route[i+1])
                    idx["tracks"].append(t)
                bridges.append((pad_label, (route[-1][0]/1e6, route[-1][1]/1e6)))
                pts_str = " -> ".join(f"({x/1e6:.2f},{y/1e6:.2f})" for x, y in route[1:])
                print(f"  bridge-fallback {pad_label} -> {pts_str}")
                continue
        # get via position
        if via_label in added_by_label:
            sec_pos = added_by_label[via_label]
        else:
            # parse via@ label
            try:
                coords = via_label[5:-1]
                x, y = coords.split(",")
                sec_pos = (int(float(x)*1e6), int(float(y)*1e6))
            except Exception:
                failed.append(g)
                continue
        # find bridge position in main island
        bridge_pos = find_bridge_via_pos(sec_pos, idx)
        if bridge_pos is None:
            failed.append(g)
            continue
        t, v = add_bridge(b, sec_pos, bridge_pos)
        idx["tracks"].append(t)
        idx["vias"].append(v)
        bridges.append((via_label, (bridge_pos[0]/1e6, bridge_pos[1]/1e6)))
        print(f"  bridge {via_label} -> ({bridge_pos[0]/1e6:.2f},{bridge_pos[1]/1e6:.2f})")
    return bridges, failed


def inspect_u1_61(b):
    """Print details of U1 pads numbered 61."""
    u1 = None
    for f in b.GetFootprints():
        if f.GetReference() == "U1":
            u1 = f
            break
    if u1 is None:
        print("U1 not found")
        return []
    pads61 = []
    for p in u1.Pads():
        if p.GetNumber() == "61":
            pads61.append(p)
            print(f"U1-61: shape={p.GetShape()} layer={p.GetLayer()} attr={p.GetAttribute()} "
                  f"size=({p.GetSize().x/1e6:.3f},{p.GetSize().y/1e6:.3f}) "
                  f"drill={getattr(p,'GetDrillSize',lambda:('?','?'))()} "
                  f"pos=({p.GetPosition().x/1e6:.2f},{p.GetPosition().y/1e6:.2f})")
    return pads61


def pick_representative_pad(group, idx):
    """Return pcbnew pad object for a group member (prefer non-U1-61)."""
    fps = idx["fps"]
    pad_labels = [m for m in group if "-" in m and "via@" not in m]
    # prefer non-U1-61
    non61 = [m for m in pad_labels if not m.startswith("U1-")]
    if non61:
        pad_labels = non61
    for lbl in pad_labels:
        ref, num = lbl.rsplit("-", 1)
        if ref not in fps:
            continue
        fp = fps[ref]
        p = fp.FindPadByNumber(num)
        if p is not None:
            return p
    return None


def u1_thermal_pads(u1):
    """Return the large SMD thermal pads of U1 (top and bottom)."""
    smd = []
    pth = []
    for p in u1.Pads():
        if p.GetNumber() != "61":
            continue
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            sz = p.GetSize()
            # large thermal pad (3.4 mm) vs small SMD stubs
            if sz.x >= 1500000 and sz.y >= 1500000:
                smd.append(p)
        else:
            pth.append(p)
    return smd, pth


def nearest_pad(target, candidates):
    """Return candidate pad closest to target pad center."""
    tx, ty = target.GetPosition().x, target.GetPosition().y
    best = None
    best_d = float('inf')
    for c in candidates:
        cx, cy = c.GetPosition().x, c.GetPosition().y
        d = math.hypot(cx - tx, cy - ty)
        if d < best_d:
            best_d = d
            best = c
    return best, best_d


def add_pad_to_pad_track(b, from_pad, to_pad):
    """Add a short track between two pads on from_pad's copper layer."""
    net = from_pad.GetNet()
    layer = pad_copper_layer(from_pad)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(from_pad.GetPosition())
    t.SetEnd(to_pad.GetPosition())
    t.SetWidth(TRACK_WIDTH)
    t.SetLayer(layer)
    t.SetNet(net)
    b.Add(t)
    return t


def fix_u1_61_thermal_pads(b, idx):
    """Connect isolated U1-61 large SMD thermal pads to the PTH via array."""
    u1 = idx["fps"].get("U1")
    if u1 is None:
        return []
    smd_pads, pth_pads = u1_thermal_pads(u1)
    if not pth_pads:
        return []
    added = []
    for p in smd_pads:
        # Avoid zero-length tracks: don't pick a PTH via whose center is
        # coincident with the SMD pad center (they are separate objects).
        candidates = [c for c in pth_pads
                      if math.hypot(c.GetPosition().x - p.GetPosition().x,
                                    c.GetPosition().y - p.GetPosition().y) > 100000]
        nearest, dist = nearest_pad(p, candidates)
        if nearest is None:
            continue
        # Skip if a track already links them on this layer
        layer = pad_copper_layer(p)
        ppos = (p.GetPosition().x, p.GetPosition().y)
        npos = (nearest.GetPosition().x, nearest.GetPosition().y)
        existing = False
        for t in b.Tracks():
            if "VIA" in type(t).__name__:
                continue
            if t.GetLayer() != layer:
                continue
            if t.GetNetname() != "GND":
                continue
            ep = {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}
            if ppos in ep and npos in ep:
                existing = True
                break
        if existing:
            continue
        t = add_pad_to_pad_track(b, p, nearest)
        idx["tracks"].append(t)
        lbl = f"U1-61_{'top' if layer == pcbnew.F_Cu else 'bot'}_thermal"
        print(f"  U1-61 thermal track {lbl}: ({p.GetPosition().x/1e6:.2f},{p.GetPosition().y/1e6:.2f}) -> "
              f"({nearest.GetPosition().x/1e6:.2f},{nearest.GetPosition().y/1e6:.2f}) on layer {layer}")
        added.append((lbl, t))
    return added


def fix_board(save_path=None):
    b = load_board()
    idx = build_index(b)

    # U1-61 inspection first
    print("=== U1-61 thermal via pads ===")
    inspect_u1_61(b)

    groups, ret = run_check_opens(BOARD)
    print(f"\ncheck_opens exit={ret} GND groups={len(groups)}")

    # filter out U1-61-only groups for first pass
    normal_groups = [g for g in groups if not all(m.startswith("U1-") for m in g)]
    u61_groups = [g for g in groups if all(m.startswith("U1-") for m in g)]
    print(f"normal open groups: {len(normal_groups)}; U1-61-only groups: {len(u61_groups)}")

    added = []
    failed = []
    for g in normal_groups:
        _make_bins(idx)
        p = pick_representative_pad(g, idx)
        if p is None:
            print(f"  no pad found for group {g}")
            failed.append(g)
            continue
        lbl = f"{p.GetParentFootprint().GetReference()}-{p.GetNumber()}"
        via_pos = find_via_pos(p, idx)
        if via_pos is not None:
            print(f"  fixing {lbl} via=({via_pos[0]/1e6:.2f},{via_pos[1]/1e6:.2f})")
            t, v = add_track_via(b, p, via_pos)
            idx["tracks"].append(t)
            idx["vias"].append(v)
            added.append((lbl, via_pos))
            continue
        # fallback: connect pad to an existing GND item with a clear routed track
        route = try_connect_to_existing_gnd(p, idx)
        if route is not None:
            pts_str = " -> ".join(f"({x/1e6:.2f},{y/1e6:.2f})" for x, y in route[1:])
            print(f"  fixing {lbl} track={pts_str}")
            for i in range(len(route)-1):
                t = add_track_between(b, p.GetNet(), pad_copper_layer(p), route[i], route[i+1])
                idx["tracks"].append(t)
            added.append((lbl, route[-1]))
            continue
        print(f"  no connection for {lbl}")
        failed.append(g)

    if save_path is None:
        save_path = BOARD

    # Explicitly connect U1-61 large SMD thermal pads to the PTH via array.
    # check_opens doesn't model pad-to-pad copper overlap, so these show as
    # isolated GND islands even though they sit on top of the thermal vias.
    print("\n=== U1-61 thermal pad tracks ===")
    fix_u1_61_thermal_pads(b, idx)

    # Second pass: bridge any secondary GND islands to the main island.
    bridges, bridge_failed = bridge_remaining_islands(b, idx, added, save_path)

    # Refill zones with kicad-cli so new vias connect to the GND pour.
    import subprocess
    subprocess.run([
        "kicad-cli", "pcb", "drc",
        "--format", "json",
        "--output", "/tmp/rev6-drc.json",
        "--save-board", "--refill-zones",
        save_path
    ], check=True, capture_output=True)
    print(f"\nSaved {save_path}: added {len(added)} pad-vias + {len(bridges)} bridges")
    if failed:
        print(f"FAILED first-pass groups: {failed}")
    if bridge_failed:
        print(f"FAILED bridge groups: {bridge_failed}")
    return added, failed, bridges, bridge_failed


def main():
    fix_board(BOARD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
