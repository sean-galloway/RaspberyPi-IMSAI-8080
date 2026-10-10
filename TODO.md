# TODO

Open items for the IMSPI 8080 project.

## Mechanical — 3U 3D case (done 2026-10-10)
- [x] Pulled the **final 3-D design for the 10" rack 3U enclosure/panel** from
      **jetson-marker-turret** git history (`f57c7c1^` — it had been stripped from the
      working tree in the move to this repo). Now lives at
      [`hardware/case/rack_case.scad`](hardware/case/rack_case.scad) (fascia + tray +
      side gussets + blue frame).
- [x] Reconciled against the **measured rev5 PCB** (`imspi8080_rev5.kicad_pcb`,
      204.1 × 112.1): LED windows, 12 toggle holes, and all 6 PCB bosses re-aligned to
      the rev5 grid; gusset webs lowered (board bottom z≈19.3). See
      [`hardware/case/README.md`](hardware/case/README.md) for the mapping table.
- [x] LED windows + standoff layout finalized from the measured grid. The rev2-era
      **separate toggle bracket (J3/J4)** is obsolete — rev5 switches mount through the
      board voids (see `hardware/imspi8080_rev5.kicad_pcb` + fab-rev5 notes).
      **Remaining in-hand check:** LED dome depth vs `pcb_boss_h=5` and MTS bushing
      length vs `tog_cbore_dep=2.5` before printing (can't fix after print).

## Rev1 bring-up (when the board arrives, ~mid/late July 2026)
- [ ] Flash firmware: hold **BOOTSEL (SW1)**, plug USB into J1, drag the `.uf2` (build from
      [`firmware/`](firmware/), Pico SDK).
- [ ] Bring-up with [`host/`](host/) Python driver + `examples/lamp_test.py` over `/dev/ttyACM0`.

## Future — 19" faithful build
- [ ] Build a full-size **19" 4U** fully-faithful IMSAI 8080 (~450 × 178 mm ≈ real IMSAI,
      ~40 LEDs / 16-bit switch set). Reuse this project's architecture, SKiDL generator,
      placement/routing scripts, and firmware at the larger size.

### Rev1 notes to carry into rev2
- **Trim board to 204 × 60 mm (−10 mm each axis) — structural, not cosmetic.** The carrier-
  plate side flanges, front L-gussets, and rail-mount hardware all run down the side margins;
  the current full-width 214 mm PCB (mounting holes only 7 mm from each edge) leaves no room
  for them. Pulling the board in ~5 mm/side opens the clearance channels the rigidity scheme
  needs; trimming height frees the band below the LEDs for the front flange + toggle bracket.
  This is a **re-layout, not an outline crop**: the LED grid (currently x = 15–205 mm) must
  pull inward and the edge holes/connectors move with it. See the carrier-plate rigidity plan.
- Fine-pitch parts need **0.15 mm track / 0.13 mm clearance** rules (0.25/0.2 couldn't
  escape the RP2040 QFN-56 0.4 mm pitch).
- Ground is routed as **traces** (no solid plane on this dense 2-layer board).
- Flash (U2) ended up far from U1 — place it tight to the RP2040 next time.
