# TODO

Open items for the IMSPI 8080 project.

## Mechanical — grab the final 3U 3D design
- [ ] Pull the **final 3-D design for the 10" rack 3U enclosure/panel** from the
      **jetson-marker-turret** project (that's where the enclosure CAD lives — this panel
      is its front face, housing an RPi 5 + Jetson Orin AGX 64GB).
- [ ] Reconcile it against [`hardware/design-spec.md`](hardware/design-spec.md): 214 × 70 mm
      board, 3U face, ~3–5 mm standoffs. Verify against the real model, not the estimated
      fit-check dimensions.
- [ ] Finalize: bezel LED windows (align to the LED grid), **standoff height** (must match
      the real toggle bushing length — can't fix after fab), and the **separate toggle
      bracket** wired to J3/J4.

## Rev1 bring-up (when the board arrives, ~mid/late July 2026)
- [ ] Flash firmware: hold **BOOTSEL (SW1)**, plug USB into J1, drag the `.uf2` (build from
      [`firmware/`](firmware/), Pico SDK).
- [ ] Bring-up with [`host/`](host/) Python driver + `examples/lamp_test.py` over `/dev/ttyACM0`.

## Future — 19" faithful build
- [ ] Build a full-size **19" 4U** fully-faithful IMSAI 8080 (~450 × 178 mm ≈ real IMSAI,
      ~40 LEDs / 16-bit switch set). Reuse this project's architecture, SKiDL generator,
      placement/routing scripts, and firmware at the larger size.

### Rev1 notes to carry into rev2
- Fine-pitch parts need **0.15 mm track / 0.13 mm clearance** rules (0.25/0.2 couldn't
  escape the RP2040 QFN-56 0.4 mm pitch).
- Ground is routed as **traces** (no solid plane on this dense 2-layer board).
- Flash (U2) ended up far from U1 — place it tight to the RP2040 next time.
