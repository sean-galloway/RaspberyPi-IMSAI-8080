# IMSPI 8080 firmware (RP2040)

Owns LED refresh (2x TLC5947), switch scan + debounce (2x 74HC165), and the
serial protocol to the Pi over native USB CDC. Built with the Raspberry Pi
Pico SDK.

## Prerequisites

- CMake >= 3.13, GNU Arm toolchain, and the Pico SDK.
- Set `PICO_SDK_PATH` to your SDK checkout, e.g.:

```bash
git clone https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk && git submodule update --init && cd ..
export PICO_SDK_PATH=$PWD/pico-sdk
```

## Build

```bash
cd firmware
mkdir build && cd build
cmake ..
make -j
```

This produces `build/imspi8080.uf2`. Hold BOOTSEL on the Pico, plug it in, and
drag the `.uf2` onto the `RPI-RP2` drive.

## Wiring

Pin assignments are in `src/config.h` (RP2040 GPIO numbers). Defaults:

| Signal        | GPIO | To            |
|---------------|------|---------------|
| TLC SIN       | 3    | first TLC5947 SIN |
| TLC SCLK      | 2    | TLC5947 SCLK  |
| TLC XLAT      | 4    | TLC5947 XLAT  |
| TLC BLANK     | 5    | TLC5947 BLANK |
| TLC GSCLK     | 6    | TLC5947 GSCLK |
| HC165 SH/LD   | 10   | 74HC165 pin 1 |
| HC165 CLK     | 11   | 74HC165 pin 2 |
| HC165 QH      | 12   | last 74HC165 QH |

If the wrong LED chip lights up, flip `TLC_REVERSE_DEVICE_ORDER`. If switches map
backwards, flip `HC165_REVERSE_BITS`.

## Notes and things to verify against the datasheet

- The TLC5947 GSCLK is a free-running PWM (`TLC_GSCLK_HZ`, default 1 MHz) and
  BLANK is released after priming. For flicker-free updates you can additionally
  pulse BLANK once per 4096 GSCLK cycles to align the grayscale counter — not
  required for a front panel, but noted.
- Data shift is bit-banged for clarity. If you want more headroom, move SIN/SCLK
  onto a hardware SPI instance; the byte order in `tlc5947.c` stays the same.
- CRC-8 parameters must stay in sync with `host/imspi/crc8.py`.
