# IMSAI-8080 rev5 rack case (10" 3U)

3D-printable case for the DeskPi RackMate T2: front **fascia** (the IMSAI bezel
with LED windows + 12 toggle holes + 6 PCB bosses), **platform** (tray with
Jetson AGX Orin pocket + Pi 5 / Pico standoffs) and **side gussets**, all fused
into ONE print for strength, plus a
cosmetic IMSAI-blue frame trim.

## Provenance

Recovered from `jetson-marker-turret` git history (`f57c7c1^` :
`turret-gimbal/cad/scad/rack_shelf.scad`) — the turret repo stripped the IMSAI
panel work 2026-07-14 with the note that it was moving to this repo, but it never
landed here until now. The tray/Jetson/Pi/Pico geometry is unchanged from that
rev2-era case design; **every board-facing feature was re-derived from the
measured `hardware/imspi8080_rev5.kicad_pcb`** (2026-10-10):

| Feature | rev5 measured (board-rel) | Case value |
|---|---|---|
| LED data columns | x = 14.13 + 15k (8 cols) | LED windows [10.5, 123] |
| LED status columns | x = 147.13 + 15k (4 cols) | LED window [143.5, 196.5] |
| LED rows | y = 64.13 / 76.13 / 88.13 | window centers via `bd_z()` |
| Toggle voids | 8 data + 4 cmd, ctr y = 103.06 | `toggle_x_data/cmd`, `toggle_ry` |
| PCB holes H1–H6 | (8.1/131.1/196.1) × (8.1/87.1) | `pcb_holes`, 6 bosses |
| Board size | 204.1 × 112.1 | top edge 0.6 mm below face top |

Board-relative (x, y-down) maps to the bezel via `ap_x()` / `bd_z()`; world x on
the tray = board-rel x − 3 (content_dx = −3, same convention as the
rev2-era case design). The rev5 board is 204.1 mm wide → drops into the 214 mm tray
with ~5 mm/side; the board bottom edge sits at z≈19.3, so the gusset webs were
lowered to z≤16.

The standalone 4 mm faceplate variant (`hardware/faceplate/gen_faceplate_3d.py`)
shares the same rev5 grid and legend layout; this case is the 5 mm
tray-integrated version (the one to build).

## Printing

Nothing has been printed yet; the parts go to a print shop.

OpenSCAD 2021.01+ (`openscad` CLI works):

```
openscad -o case.stl  -D 'PART="case"'  rack_case.scad   # black PETG/ASA
openscad -o frame.stl -D 'PART="frame"' rack_case.scad   # IMSAI blue
openscad -o caps.stl -D 'MODE="tray"' imsai_paddle_cap.scad  # 12 toggle paddles
```

| File | Part | Size (mm) | Qty |
|---|---|---|---|
| `case.stl` | fascia + side gussets + centre gusset + tray + Jetson pocket + Pi 5/Pico standoffs, **one fused solid** | 254 × 205 × 139 | 1 |
| `frame.stl` | IMSAI-blue trim (glue/slip-on) | 254 × 4 × 132 | 1 |
| `caps.stl` | toggle paddle caps | small | 12 |

The side gussets are fused into the case (`gusset_fused = true`) so the fascia,
gussets and tray are one piece -- no floor bolts. The panel PCB screws from behind
to the 4 bezel bosses + the 2 gusset-carried corner standoffs (path: fascia → PCB
→ gusset → tray). `gusset_fused = false` restores the older bolt-on variant
(`PART="gusset"`, both sides in one file, M3 through the floor).

For the shop: the case is one large part with internal ribs, bosses and a vented
floor, so a support-free process (SLS/MJF nylon) avoids support scars in the
LED windows and toggle body pockets; for FDM it needs a ≥ 255 × 210 mm bed.

The toggles mount to the fascia, not the board: each body floats in its board
void, its front end nests in a 13.6 × 8.4 × 2.5 mm pocket on the fascia back
(keys it against rotation and squares it to the void), the bushing passes the
2.5 mm web and a nut clamps it from the front. The lugs are jumper-wired to the
SWD/SWC V/S/G pads. Fit the switches before the PCB goes on.

Before ordering verify in-hand (all fixed once printed):
- the LED standoff (`pcb_boss_h` = 5) against the board's LED height behind the windows;
- an MTS-102 body against the pocket (`tog_body_w` × `tog_body_h`), and its bushing
  thread against the 2.5 mm web plus nut and washer;
- with the body's long side horizontal (the only way it passes the board void),
  the bat throws up/down.
