# IMSPI 8080 serial protocol

Version 0.1.0

The Pi (host) and the panel (RP2040) exchange fixed, byte-oriented frames over the
RP2040's native USB CDC (or a 4-pin UART fallback). Baud is nominal over CDC.
The panel is treated as a register-mapped peripheral: the host writes lamp
registers, the panel reports switch registers.

## Framing

Every frame is:

```
[SOF] [CMD] [payload ...] [CRC8]
```

- `SOF` — start-of-frame, direction-specific (lets each side resync)
  - host -> panel: `0xA5`
  - panel -> host: `0x5A`
- `CMD` — command/response byte (see tables)
- `CRC8` — over every byte in the frame *except* the CRC byte itself
  (i.e. from `SOF` through the last payload byte)

Frame length is fixed per `CMD`, so a receiver reads `SOF`, then `CMD`, then the
known number of remaining bytes. On CRC failure or unknown `CMD`, discard bytes
until the next valid `SOF`.

### CRC8

CRC-8, polynomial `0x07`, init `0x00`, no input/output reflection, no final XOR
(the classic "CRC-8/SMBUS" parameters). Reference implementations:
`firmware/src/crc8.c` and `host/imspi/crc8.py` — they are byte-for-byte identical.

## Host -> panel commands

### `0x01` LED update (8 bytes)

Writes the full lamp state in one frame.

| Byte | Field     | Meaning                                    |
|------|-----------|--------------------------------------------|
| 0    | `0xA5`    | SOF                                        |
| 1    | `0x01`    | CMD                                        |
| 2    | `ADDR_HI` | address bus A15..A8 (bit7 = A15)           |
| 3    | `ADDR_LO` | address bus A7..A0                         |
| 4    | `DATA`    | data bus D7..D0                            |
| 5    | `STATUS`  | status lamps, bits 0..3 used (see below)   |
| 6    | `BRIGHT`  | global brightness 0..255 (maps to 12-bit)  |
| 7    | `CRC8`    |                                            |

`STATUS` bit assignment (default, firmware-configurable):

| bit | lamp   |
|-----|--------|
| 0   | RUN    |
| 1   | WAIT   |
| 2   | HLDA   |
| 3   | INT/PWR|

### `0x02` lamp test (4 bytes)

`[0xA5][0x02][ON][CRC8]` — `ON != 0` drives all lamps full on; `0` returns to the
last LED-update state. Useful for bring-up and a boot self-test.

### `0x03` set brightness (4 bytes)

`[0xA5][0x03][LEVEL][CRC8]` — global brightness 0..255 without changing lamp state.

### `0x7F` ping (3 bytes)

`[0xA5][0x7F][CRC8]` — panel replies with `0xC0` version.

## Panel -> host responses

### `0x81` switch report (6 bytes)

Sent on any switch change and on a periodic heartbeat.

| Byte | Field     | Meaning                                       |
|------|-----------|-----------------------------------------------|
| 0    | `0x5A`    | SOF                                           |
| 1    | `0x81`    | CMD                                           |
| 2    | `SW_DATA` | 8 data toggle levels (bit i = toggle i)       |
| 3    | `SW_CMD`  | 4 command switch levels, bits 0..3            |
| 4    | `EVENTS`  | latched rising edges on command switches 0..3 |
| 5    | `CRC8`    |                                               |

`SW_DATA` are latching toggles, reported as levels. The 4 command switches are
momentary (spring-return); their *levels* are in `SW_CMD`, but the important field
is `EVENTS`: a bit set means that command switch saw a press (rising edge) since
the last report. The panel latches edges so a fast press between two host polls is
never lost, then clears them once reported.

Default command-switch map (firmware-configurable):

| bit | switch      | action                          |
|-----|-------------|---------------------------------|
| 0   | RUN / STOP  | toggle run state                |
| 1   | SINGLE STEP | advance one instruction         |
| 2   | EXAMINE     | load address from data toggles  |
| 3   | DEPOSIT     | store data toggles at address   |

Four physical command switches give four momentary actions. The classic 8-function
IMSAI set (EXAMINE/EXAMINE-NEXT, DEPOSIT/DEPOSIT-NEXT, RESET, etc.) can be layered
by treating a held toggle as a modifier, or by wiring 3-position `(on)-off-(on)`
momentaries to two `74HC165` inputs each. That is host/firmware policy — the wire
protocol just carries levels + edges.

### `0xC0` version (5 bytes)

`[0x5A][0xC0][VER_MAJ][VER_MIN][CRC8]` — reply to ping.

## Byte-wise address entry

Only 8 data toggles exist, so a 16-bit EXAMINE address is entered in two gestures.
Suggested host convention:

1. set the 8 data toggles to the high byte, pulse EXAMINE with the RUN/STOP toggle
   held (modifier) -> host loads A15..A8
2. set the low byte, pulse EXAMINE normally -> host loads A7..A0 and examines

All 16 address lamps still display the full latched address, so the panel *reads*
exactly like a real IMSAI even though entry is byte-wise.
