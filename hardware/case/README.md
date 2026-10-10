# IMSAI-8080 rev5 rack case (10" 3U)

3D-printable case for the DeskPi RackMate T2: front **fascia** (the IMSAI bezel
with LED windows + 12 toggle holes + 6 PCB bosses), **platform** (tray with
Jetson AGX Orin pocket + Pi 5 / Pico standoffs), bolt-on **side gussets**, and a
cosmetic IMSAI-blue frame trim.

## Provenance

Recovered from `jetson-marker-turret` git history (`f57c7c1^` :
`turret-gimbal/cad/scad/rack_shelf.scad`) — the turret repo stripped the IMSAI
panel work 2026-07-14 with the note that it was moving to this repo, but it never
landed here until now. The tray/Jetson/Pi/Pico geometry is unchanged from that
printed rev2-era case; **every board-facing feature was re-derived from the
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
the tray = board-rel x − 3 (content_dx = −3, same convention as the printed
rev2-era case). The rev5 board is 204.1 mm wide → drops into the 214 mm tray
with ~5 mm/side; the board bottom edge sits at z≈19.3, so the gusset webs were
lowered to z≤16.

The standalone 4 mm faceplate variant (`hardware/faceplate/gen_faceplate_3d.py`)
shares the same rev5 grid and legend layout; this case is the 5 mm
tray-integrated version that matches the printed parts.

## Printing

OpenSCAD 2021.01+ (`openscad` CLI works):

```
openscad -o case.stl   -D 'PART="case"'   rack_case.scad   # black PETG/ASA
openscad -o gusset.stl -D 'PART="gusset"' rack_case.scad   # print x2
openscad -o frame.stl  -D 'PART="frame"'  rack_case.scad   # IMSAI blue
openscad -o caps.stl -D 'MODE="tray"' imsai_paddle_cap.scad  # 12 toggle paddles
```

`case.stl` = tray + fascia + centre gusset + Jetson pocket + Pi 5/Pico
standoffs (one print). Side gussets bolt on with M3 screws through the tray
floor (nuts underneath). The panel PCB screws to the 4 bezel bosses + the 2
gusset-carried corner standoffs from behind (path: fascia → PCB → gusset → tray).

Before printing verify in-hand: LED dome standoff (`pcb_boss_h` = 5) and the
MTS toggle bushing length against `tog_cbore_dep` = 2.5 — both are set from the
printed rev2-era case but can't be fixed after print.
