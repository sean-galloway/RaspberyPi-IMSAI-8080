# REV6 — RP2350A rework plan (approved 2026-10-10)

Decisions: RP2350A (QFN-60 7x7, 30 GPIO) — same body size as RP2040.
Scope: MCU swap + eliminate the two rev5 assembly wires (HC_QH, TLC_SCLK)
+ align LED columns to switch pads (0.075 mm). Everything else identical.

## Pin map (verified against KiCad MCU_RaspberryPi symbols)

| net                | RP2040 (pad = GPIO)      | RP2350A (pad = GPIO)     |
|--------------------|--------------------------|--------------------------|
| +3V3               | 1,10,22,33,42,43,44,48,49 (IOVDD/USB_VDD) | 1,11,20,30,38,45 (IOVDD) + 44 (ADC_AVDD) + 53 (USB_OTP_VDD) + 54 (QSPI_IOVDD) |
| GND                | 19*,57 + EP (*TESTEN-gnd) | EP(61) + 47 (VREG_PGND)  |
| VCORE (DVDD)       | 23,45,50 (DVDD)          | 23,39 (DVDD) + 50 (VREG_FB) |
| XIN / XOUT         | 20 / 21                  | 21 / 22                  |
| SWCLK / SWDIO (J5) | 24 / 25                  | 24 / 25 (unchanged)      |
| RUN (SW2)          | 26                       | 26 (unchanged)           |
| USB_DM / USB_DP    | 46 / 47 (via R6/R5)      | 51 / 52 (via R6/R5)      |
| QSPI_SD3/SCLK/SD0/SD2/SD1/SS | 51/52/53/54/55/56 | 55/56/57/58/59/60  |
| TLC_SCLK/SIN/XLAT/BLANK | GPIO2/3/4/5 (pads 4/5/6/7) | GPIO2/3/4/5 (pads 4/5/7/8) |
| SD_SCK/MOSI/MISO/CS| GPIO10/11/12/13 (13-16)  | GPIO10/11/12/13 (14-17)  |
| HC_PLOAD/HC_CLK/HC_QH | GPIO7/8/9 (pads 9/11/12) | GPIO7/8/9 (pads 9/12/13) |

NC on RP2350A: GPIO24/25 (pads 36/37, were NC on rev5 too), and ALL others.
CAUTION: RP2040 pad 19 = TESTEN (tied GND on rev5); RP2350A pad 19 =
GPIO15 — leave NC, do NOT ground.

## NEW: RP2350 VREG DC-DC needs an external inductor (RP2040's was LDO)

- L1 2.2uH, >=1.5A, shielded SMD power inductor (~5.5x5.3mm, e.g.
  Murata LQH5BPB2R2NT0L class). VREG_VIN(49)+VREG_AVDD(46) -> +3V3;
  VREG_LX(48) --L1--> VREG_FB(50)=VCORE net (feeds DVDD 23/39).
- VCORE decoupling already on board (C16-19 1uF) - keep.

## Firmware (firmware/): config.h is STALE vs even rev5 hardware

Discovered while mapping: rev5 board has HC_PLOAD/CLK/QH on GPIO 7/8/9,
but firmware/src/config.h says 10/11/12 — rev5 firmware as committed
would NOT drive the switch chain. rev6 fixes this for real:
- PIN_HC_PLOAD=7, PIN_HC_CLK=8, PIN_HC_DATA=9
- TLC unchanged: SIN=3, SCLK=2, XLAT=4, BLANK=5
- DROP PIN_TLC_GSCLK + its PWM init: TLC5947 has an internal grayscale
  oscillator; rev5 never wired GSCLK (pad 8 GPIO5=B... wait GPIO5=BLANK).
  GSCLK PWM is dead code — remove.
- SD on GPIO10-13 (SPI1); USB native (tinyusb) — RP2350 target, PICO_BOARD=pico2
- J5 = SWD (SWCLK 24 / SWDIO 25); RUN 26.

## Checklist before fab

- [ ] W25Q128JVSIQ on Raspberry Pi RP2350 boot-ROM supported-flash list
      (else pick a listed 16MB part — BOM change only)
- [ ] Crystal load caps (C23/C24 15pF) vs RP2350 hardware design guide for
      12MHz/20pF
- [ ] Current Pico SDK (>=2.0, RP2350 errata fixes)
- [ ] check_opens.py ALLOWLIST must end EMPTY (both assembly wires gone)

## LED/switch alignment

LED grid moves 49.400 -> 49.325 + 15k (x) to match switch-pad/void columns
(0.075 mm). Bezel windows unaffected (<0.1 mm). Faceplate unaffected.
