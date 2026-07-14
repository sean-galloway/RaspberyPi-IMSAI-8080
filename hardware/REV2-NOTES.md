# IMSPI 8080 — rev2 (204 × 60) re-layout

Rev2 trims the board 10 mm on each axis (rev1 was 214 × 70) to open the structural
side channels the computer-carrier-plate flanges/gussets need — see `design-spec.md`
and `../TODO.md`. **Rev1 is already fabricated/ordered; these are the rev2 files.**

## What's ready (generated headless)
| File | State |
|------|-------|
| `imspi8080_rev2.kicad_pcb` | Board re-placed to 204 × 60 + **89/90 nets routed** |
| `rev2_place.py` | The placement driver (reproducible): resizes the outline, positions every footprint, rips up old routing. Run with `/usr/bin/python3 rev2_place.py` |
| `rev2_check.py` | Overlap / off-board checker (0 / 0 on the current board) |
| `imspi8080_rev2.dsn` / `.ses` | Specctra export + Freerouting result |
| `jlcpcb-rev2/imspi8080-rev2-cpl.csv` | Pick-and-place, 85 parts (45 top / 40 bottom), holes excluded |
| `jlcpcb-rev2/imspi8080-rev2-bom.csv` | BOM — **same 85 parts as rev1** (resize changes positions, not parts) |
| `place_leds.py`, `place_holes.py` | Updated to the rev2 grid (LEDs 14–119 / status 147–192, rows 6/18/30; holes 8/196) |

How it was built: `SKiDL netlist → rev2_place.py (placement) → Specctra DSN →
Freerouting 1.9.0 (headless, 0.15/0.13 mm rules) → SES import`. Placement is 0 overlaps,
0 off-board. Everything fits inside 204 × 60 with ~10 mm side channels.

## What YOU finish in KiCad (2 quick touch-ups, like rev1)
Open `imspi8080_rev2.kicad_pcb` in pcbnew, then:

1. **Route one trace** — the USB D− hop Freerouting couldn't thread through the RP2040's
   0.4 mm-pitch escape: **R6 pad 2 → U1 pad 46** (net `N$8`). Use the interactive router;
   it needs one via (R6 is on the back, U1.46 on the front). ~1 minute.
2. **Nudge one via** — the `SD_MISO` via near the bottom-right corner sits 0.18 mm from the
   board edge (rule is 0.3 mm). Drag it ~0.2 mm inward (KiCad will drag its tracks with it).
3. **DRC** → should be clean (Tools → DRC).
4. **Export fab**: Plot all copper + mask + silk + Edge.Cuts, Generate Drill Files, zip →
   Gerbers. Fabrication Outputs → Component Placement (.pos) → or just reuse
   `jlcpcb-rev2/imspi8080-rev2-cpl.csv`. BOM = `jlcpcb-rev2/imspi8080-rev2-bom.csv`.
5. **JLCPCB**: same as rev1 — **Standard PCBA, double-sided** (45 top + 40 back caps).

## BOM note (parts unchanged, but sync your JLCPCB swaps)
Resizing does **not** change the parts list. The rev2 BOM is the rev1 BOM. Separately,
the repo BOM still shows the *original* parts — it never got the JLCPCB replace-parts
swaps (SW1/SW2 → HX 3×4×2 tactile, U2 flash confirm, J5 DNP). Tell me your final choices
and I'll reconcile `bom.csv` + both fab BOMs.

## Faceplate (signage recesses)
`faceplate/gen_front_panel.py` (grabbed from jetson-marker-turret) regenerates
`faceplate/imspi_panel_front.svg` — the engraved legend + LED window slots (the paint
recesses), now **aligned to the rev2 LED grid**. Regenerate: `python3 gen_front_panel.py`.
The LED field is left-of-center after the trim (status block pulled in) — re-center by
adjusting `CONTENT_DX` if wanted (keep it in sync with the turret `rack_shelf.scad` mount).
