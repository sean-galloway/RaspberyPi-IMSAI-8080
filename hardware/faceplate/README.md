# Standalone 4 mm faceplate + fascia hole-map docs

This directory holds the **standalone faceplate variant** (a self-contained
4 mm printed fascia with its own standoff bosses — no tray) plus the **2D
hole-map fabrication docs**. It shares the exact rev5 grid used by the
printable case in [`../case/`](../case/) — verified against
`../imspi8080_rev5.kicad_pcb` on 2026-10-10.

| File | Role |
|---|---|
| `gen_faceplate_3d.py` | generator → `faceplate_3d.scad` (manufacturable, ink-recess labels) + `faceplate_paint.scad` (colour preview) |
| `faceplate_3d.stl` / `faceplate_preview.png` | rendered printable + preview |
| `gen_holes.py` | generator → the fascia hole-map docs below |
| `imspi8080-holes.dxf`, `imspi8080-hole-positions.csv`, `imspi8080-holes-drawing.png/.svg` | fab hole map: SWITCH_HOLES (6.2 mm), LED_WINDOWS, LED_CENTRES, RACK_SLOTS, OUTLINE (254×132 frame, mm, origin bottom-left) |
| `gen_front_panel.py`, `imspi_panel_front.svg/.png` | legacy 2D panel graphic (rev2-era grid, superseded by the 3D faceplate previews) |
| `ten-inch-rack-specs.md` | 10" rack panel + mounting-slot spec (DeskPi RackMate T2) |

Legend text, lamp meanings, and the safety boundary come from
[`../../docs/Imsai_Panel_HMI.md`](../../docs/Imsai_Panel_HMI.md) — single source
of truth, in this repo (recovered from jetson-marker-turret history).

For the actual rack build print the case in [`../case/`](../case/) instead
(5 mm tray-integrated bezel, side gussets, Jetson/Pi mounts, blue frame) —
`rack_case.scad` is the canonical mechanical model; this directory is the
standalone-fascia variant + fab documentation.
