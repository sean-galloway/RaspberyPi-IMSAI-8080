# Hardware

IMSPI 8080 front-panel PCB + 3D-printed fascia for the 10" rack.

## ⬆️ To send to the fab, upload ONE folder: `jlcpcb-rev3/`

That is the only current, DRC-clean package. Everything superseded lives in `OLD/`.

```
jlcpcb-rev3/
  imspi8080-rev3-gerbers.zip   <- upload this (copper/mask/silk/paste + PTH & NPTH drill)
  imspi8080-rev3-cpl.csv       <- placement (83 SMT parts)
  imspi8080-rev3-bom.csv       <- BoM (electronics only; switches are hand-jumpered)
  README.txt                   <- step-by-step upload order + gotchas
```

Board: **204 × 99.7 mm**, 2-layer, 1.6 mm FR-4. Fully routed, 0 unconnected, 0 DRC errors.

## Current rev3 source (the design behind that package)

| File | What it is |
|---|---|
| `imspi8080_rev3.kicad_pcb` | the board (+ `.dsn`/`.ses` routing, `.kicad_pro`/`.prl`) |
| `rev3_place2.py` → `rev3_pads.py` | build chain: signal-flow placement, then bottom-edge switch landing pads |
| `rev3_routed.png` | routed board render |
| `faceplate/` | 3D-printed fascia — `gen_faceplate_3d.py` → `faceplate_3d.scad`/`.stl`, `faceplate_preview.png` |
| `design-spec.md`, `bom.csv`, `imspi8080_skidl.py` | design notes / schematic source |

**Switch scheme (rev3):** panel toggles mount on the fascia just below the board's
bottom edge and jumper straight up to a labeled solder landing-pad cluster each
(`SWD0-7` data 1×3, `SWC0-3` command 2×3; back-silk `V/Sn/G`, `Cn/G`). No connectors,
no cables, no board cutouts. The switch pads are bare/hand-soldered, so they are
excluded from the CPL/BoM.

## `OLD/` — superseded, do NOT upload

- `jlcpcb-rev1/`, `jlcpcb-rev2/` — earlier fab packages (rev1 is the one already ordered)
- `imspi8080_rev2.*`, `imspi8080.*` — earlier boards
- `rev3_voids.py`, `rev3_back.png` — the abandoned "switch-through-void" design
- earlier placement scripts, logs, notes
