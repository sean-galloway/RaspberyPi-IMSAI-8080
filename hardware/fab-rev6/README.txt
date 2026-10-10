IMSPI 8080 - rev6 fabrication package (RP2350A REWORK)
=======================================================
Board:  204.1 x 112.1 mm, 4-layer (F/In1/In2/B), FR4, 1 oz outer /
        0.5 oz inner, min track 0.15 mm / min clearance 0.127 mm,
        via 0.6/0.3 (0.45/0.2 on some GND pad vias; U1 thermal vias
        0.2 drill - min through-drill for the board is 0.20 mm).
        No impedance requirements. NO assembly wires - this rev routes
        every net (verified: hardware/check_opens.py = single island
        per net, allow-list empty).

WHAT CHANGED vs rev5
  - MCU: RP2040 -> RP2350A (QFN-60 7x7, thermal-via footprint).
    Fixes the RP2040 stock shortage (LCSC/JLCPCB C42411118, ~7.8k stock).
  - NEW L1 2.2uH power inductor (Bourns SRU5016 5.2x5.2 or equiv):
    RP2350 core rail is a DC-DC (VREG_LX -> VREG_FB = VCORE). REQUIRED.
  - USB D+/D- moved to RP2350 pins 51/52 (was 46/47); QSPI moved to
    55-60; all other functions keep their GPIO numbers (firmware port
    is a pin-header change, logic unchanged).
  - Both rev5 assembly wires ELIMINATED (HC_QH, TLC_SCLK now routed).
  - LED grid aligned to switch-pad columns (-0.075 mm).
  - Firmware: firmware/imspi8080-rp2350.uf2 (RP2350, 52KB,
    UF2 family 0xe48bff56; also fixes the stale HC165 pin map 10/11/12
    -> 7/8/9 that rev5 shipped with). Build: PICO_BOARD=pico2,
    pico-sdk >= 2.0 (see firmware/README.md).

VERIFY BEFORE ORDERING (RP2350 bring-up checklist)
  - W25Q128JVSIQ on Raspberry Pi's RP2350 boot-ROM supported-flash list
    (else pick a listed 16MB part - BOM change only).
  - Crystal load caps C23/C24 (15pF for the 12MHz/20pF crystal) against
    the RP2350 hardware design guide.
  - Flash: hold BOOTSEL (SW1), plug USB into J1, drag
    firmware/imspi8080-rp2350.uf2.

CONTENTS (JLCPCB flow: upload gerbers zip at the board step; BOM + CPL
at the assembly steps - same flow as fab-rev5, same LCSC part numbers,
plus U1=C42411118; pick L1 2.2uH 5.2x5.2 shielded in the tool)
  gerbers/                        14 files + drill PTH/NPTH + gbrjob
  imspi8080-rev6-bom.csv (+xlsx)  96 rows, one per designator,
                                  LCSC Part # column included
  imspi8080-rev6-cpl.csv          96 placements, JLCPCB columns, mm
  imspi8080_rev6.kicad_pcb/.pro   KiCad 10 source (schematic:
  ../../imspi8080.kicad_sch = regenerated from the rev6 netlist)

J1-A6 (USB-C duplicate D+ pad) is intentionally unconnected (plug
parallels A6/B6). Toggles mount through the 12 board voids; terminals
to the SWD*/SWC* V/S/G pads. Same case + faceplate as rev5.
