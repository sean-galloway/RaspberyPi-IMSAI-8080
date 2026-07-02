# Bill of materials

Quantities are for one panel. Part numbers are representative — substitute freely,
the design only assumes the interface (SPI-ish shift for the drivers, PISO for the
switches).

## Active

| Qty | Part                    | Role                                         | Notes |
|-----|-------------------------|----------------------------------------------|-------|
| 1   | Raspberry Pi Pico / Pico 2 | RP2040/RP2350 panel controller            | board-mount on castellations or socket |
| 2   | TLC5947                 | 24ch 12-bit PWM constant-current LED driver  | daisy-chained -> 48ch, 28 used |
| 2   | 74HC165                 | 8-bit parallel-in / serial-out shift register| daisy-chained -> 16 in, 12 used |

One TLC5947 covers the 24 data lamps; the second covers the 4 status lamps (20
channels spare — usable for per-lamp PWM effects). Alternatively drive the 4 status
LEDs from RP2040 GPIO + resistors and fit a single TLC5947, at the cost of
non-uniform firmware.

## Panel components

| Qty | Part                       | Role                    | Notes |
|-----|----------------------------|-------------------------|-------|
| 28  | 3 mm diffused red LED       | address/data/status     | 24 data + 4 status |
| 8   | SPDT mini/subminiature toggle, on-off or on-on | data toggles (latching) | subminiature bushing if pitch is tight |
| 4   | momentary toggle, `(on)-off` or `(on)-off-(on)` | command switches        | spring-return |
| 8+4 | 3D-printed paddle caps      | IMSAI look              | over the bat handles |

## Passives / glue

| Qty | Part                | Role |
|-----|---------------------|------|
| 2   | Iref resistor (~2.2–3 kΩ) | one per TLC5947; sets per-channel current (~15–25 mA) |
| ~6  | 100 nF ceramic       | one decoupling cap per IC |
| 1   | 10 µF ceramic/tant   | bulk on 3.3V rail |
| 2   | 10 kΩ resistor network (SIP) | pulls on the 74HC165 inputs |
| 1   | 4-pin header         | UART fallback (optional; USB CDC is primary) |

## Rails

Run RP2040, both TLC5947s, and both 74HC165s at **3.3 V** — no level shifters
anywhere. Red LED forward voltage (~1.8–2.0 V) is fine on a 3.3 V LED supply, and
the TLC5947 sets current independent of the logic rail.

## PCB order

- 2-layer, 1.6 mm, HASL is fine; ENIG if you want flat pads for hand-soldering the
  TSSOP TLC5947.
- Board outline = panel inner dimension; add standoff holes matched to the printed
  shell.
- **Board-mount the toggles and LEDs.** The critical mechanical number is the
  PCB-to-bezel standoff height: it must match the toggle bushing length and LED body
  length so bushings/domes protrude correctly through the printed face. Lock this in
  CAD before routing — see `docs/panel-layout.md`.
- Component origins locked to the bezel hole grid (LEDs under window holes, toggle
  cutouts under bushings). Design the bezel hole pattern first, export positions,
  then place footprints to that grid.
