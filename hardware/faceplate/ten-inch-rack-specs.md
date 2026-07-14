# 10″ Rack — Panel & Mounting-Hole Specs

Reference for any front panel that mounts in the ground-station rack
(DeskPi RackMate T2, BOM #52). Use these numbers for rack-mount faces —
the compute shelf (#61), blank/vent panels (#59), and the IMSAI/IMSPI
fascia (built in the separate panel repo).

**Source:** manufacturer mechanical drawing, cross-checked against a real
10″ 12-port keystone patch panel (254 mm overall, 238 mm mount-hole span,
214 mm aperture). Confirm against your own rails before cutting — the oval
slots absorb small differences.

## Panel envelope

| Dimension | Value |
|---|---|
| Panel outer width | **254 mm** |
| 1U height | **44 mm** (1.73 in) |
| N-U panel height | **N × 44 mm** (2U = 88, 3U = 132) |
| Front-face thickness (printed) | 4–5 mm typical |

## Mounting-hole geometry

| Dimension | Value | Notes |
|---|---|---|
| Hole horizontal center-to-center | **238 mm** | across the panel |
| Hole inset from each **side** edge | **8 mm** | = (254 − 238) / 2 |
| Hole vertical center-to-center, **within 1U** | **33 mm** | |
| Hole inset from **top/bottom** of a 1U | **5.5 mm** | = (44 − 33) / 2 |
| Slot shape | **horizontal oval**, **9.33 W × 6.77 H mm** | oval = side-to-side rail-fit adjustment |

- Holes/slots come in a **column at x = 8 mm and x = 246 mm** (both side edges).
- Vertically they repeat per 1U: each 1U has a pair at **5.5 mm** from its top
  and bottom edges (33 mm apart).

## Clear aperture (usable opening)

| Face | Usable width | Usable height |
|---|---|---|
| any | **214 mm** | 1U ≈ 33 mm · 2U ≈ 77 mm · 3U ≈ 122 mm |

Width is set by the mounting-hole span, not the electronics.

## Worked example — a 3U face (132 mm tall)

Four corner mounting slots (what the compute-bay design uses):

| Slot | x (from left) | z (from bottom) |
|---|---|---|
| top-left | 8 | 126.5 |
| top-right | 246 | 126.5 |
| bottom-left | 8 | 5.5 |
| bottom-right | 246 | 5.5 |

(z = 5.5 from the bottom edge, and 132 − 5.5 = 126.5 from it for the top.)
If your rails are tapped at every U, you may add mid-height slots on the
same 33-mm-in-1U pattern; 4 corners is sufficient for a printed compute bay.

## OpenSCAD reference

```scad
// 10" rack mounting geometry
face_width    = 254;
U             = 44;
rail_hole_dx  = 238;                       // horizontal C-C
hole_cc_v     = 33;                         // vertical C-C within 1U
slot_w        = 9.33;                       // oval slot W
slot_h        = 6.77;                       // oval slot H
slot_side_ctr = (face_width - rail_hole_dx)/2;   // 8 mm
slot_tb_ctr   = (U - hole_cc_v)/2;               // 5.5 mm

// one horizontal oval slot, cut through a face of thickness `th` (bore along +Y)
module rack_slot(th, eps = 0.01) {
    off = (slot_w - slot_h)/2;
    hull() for (dx = [-off, off])
        translate([dx, -eps, 0]) rotate([-90,0,0])
            cylinder(h = th + 2*eps, d = slot_h, $fn = 48);
}

// 4 corner slots for a panel `panel_U` high, thickness `th`
module rack_slots_4corner(panel_U, th) {
    panel_h = panel_U * U;
    for (sx = [slot_side_ctr, face_width - slot_side_ctr])
        for (sz = [slot_tb_ctr, panel_h - slot_tb_ctr])
            translate([sx, 0, sz]) rack_slot(th);
}
```

## Notes

- **Oval, not round:** the horizontal ovals let the panel slide ±~1.5 mm to
  line up with imperfect rails — orient the long axis horizontal.
- **Fasteners:** M6 rack screws (with cage/clip nuts) are typical for these
  10″ racks; confirm your rack's thread/cage-nut style.
- **RackMate T2 interior depth:** ~260 mm (≈10.23″) — leave room behind the
  face for cabling/service loops.
