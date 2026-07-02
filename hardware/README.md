# Hardware

KiCad project and mechanical files live here. Not yet committed — this documents
the intended structure and the constraints the board must satisfy.

## Planned files

```
hardware/
  imspi8080.kicad_pro
  imspi8080.kicad_sch      schematic: Pico + 2x TLC5947 + 2x 74HC165
  imspi8080.kicad_pcb      board outline = panel inner dim
  imspi8080-panel.step     bezel / case reference for alignment
  gerbers/                 fab output
```

## Schematic blocks

- RP2040 (Pico) — footprint on castellations or a socket
- 2x TLC5947 daisy-chained: SIN/SCLK from the Pico, XLAT, BLANK, GSCLK; one Iref
  resistor per device; 100 nF decoupling per device
- 2x 74HC165 daisy-chained: SH/LD, CLK, QH to the Pico; 10 kΩ pull network on the
  inputs; 100 nF decoupling per device
- 28x 3 mm red LED: anodes to LED rail, cathodes to TLC channels (constant-current
  sink -> no series resistors)
- 8x latching toggle + 4x momentary toggle to 74HC165 inputs
- single 3.3 V rail; 10 uF bulk

See `../docs/bom.md` for parts and `../docs/panel-layout.md` for the bezel grid.

## Layout constraints (the ones that bite)

1. Component origins locked to the bezel hole grid — design the hole pattern in the
   case CAD first, export positions, place footprints to that grid.
2. Board-mounted toggles + LEDs: the PCB-to-bezel standoff height must equal the
   toggle bushing length minus bezel thickness. Measure the toggles you actually
   buy, then set standoff height and bezel thickness to match. No fixing it post-fab.
3. Column pitch is set by toggle finger-clearance (~30 mm), not the LEDs. Left block
   8 columns, right block 4 columns, all inside ~220 mm.
