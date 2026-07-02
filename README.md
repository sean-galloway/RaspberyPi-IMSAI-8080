# IMSPI 8080

A smart front panel for a 10" rack, styled after the IMSAI 8080, driven by a
Raspberry Pi (running an 8080/Z80 emulator such as z80pack or SIMH) over a single
USB link. An on-panel RP2040 owns all LED refresh and switch debounce and exposes
the panel to the Pi as a small register-mapped serial peripheral.

## Why a smart panel

The naive build wires every LED and switch straight back to the Pi header with
flying leads — which does not scale past ~60 I/O and turns into a harness. Instead
the panel carries its own microcontroller and driver silicon, and the Pi talks to
it the way a CPU talks to memory-mapped I/O: write the lamp registers, read the
switch registers. This decouples the panel's real-time refresh from whatever else
the Pi is doing, moves debounce and PWM off the Pi, and keeps a single 3.3V rail
with no level shifters.

## Panel layout

Matched to the physical panel (see `docs/panel-layout.svg`):

- Left block: three rows of 8 LEDs over 8 toggles
  - row 1 — address high (A15..A8)
  - row 2 — address low  (A7..A0)
  - row 3 — data          (D7..D0)
  - 8 data toggles (latching) below
- Right block: one row of 4 status LEDs over 4 command switches (momentary)

28 LEDs, 12 switches, sized to the ~220 mm usable width of a 10" rack aperture.
Because all 16 address bits are displayed even though only 8 data toggles exist,
EXAMINE looks fully authentic; address entry is byte-wise (see `docs/protocol.md`).

## Architecture

```
  Raspberry Pi 5 ── USB CDC ── RP2040 (Pico) ─┬─ SPI ──▶ 2x TLC5947  ─▶ 28 LEDs
   (emulator)                                  └─ GPIO ─▶ 2x 74HC165 ◀─ 12 switches
```

- MCU: RP2040 (Raspberry Pi Pico / Pico 2)
- LED driver: 2x TLC5947 (24ch, 12-bit PWM, constant current) daisy-chained -> 48ch, 28 used
- Switch input: 2x 74HC165 (parallel-in serial-out) daisy-chained -> 16 in, 12 used
- Link: RP2040 native USB CDC (`/dev/ttyACM0`); 4-pin UART is the wired fallback

See `docs/bom.md` for the parts list and `docs/panel-layout.md` for the bezel grid
and pitch math.

## Repo layout

```
docs/        protocol spec, BOM, panel layout + drawing
firmware/    RP2040 firmware (Pico SDK, C)
host/        Python driver + examples for the Pi side
hardware/    KiCad / mechanical notes
```

## Quick start

Firmware: see `firmware/README.md` (Pico SDK build -> drag `imspi8080.uf2` to the
Pico in BOOTSEL mode).

Host: see `host/README.md`.

```bash
cd host
pip install -e .
python examples/lamp_test.py /dev/ttyACM0
```

## Emulator integration

The panel is a clean memory-mapped-I/O seam. On each emulated CPU step, write the
LED frame (address bus, data bus, status flags) and consume any latched switch
events. z80pack and SIMH both expose CPU state and an I/O hook you can bridge to
`host/imspi`; `examples/panel_demo.py` drives the panel with a synthetic bus so you
can validate the hardware end-to-end before wiring the emulator.

## License

MIT — see `LICENSE`.
