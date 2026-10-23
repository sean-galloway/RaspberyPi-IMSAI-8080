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
  - NEW L1 2.2uH power inductor (SXN SMNR4020-2.2UH, LCSC C135262,
    4.0x4.0x2.0mm): RP2350 core rail is a DC-DC (VREG_LX -> VREG_FB =
    VCORE). REQUIRED. Footprint on board = L_SXNSMNR4020_4x4x2mm
    (rev6 L1-fix: pads 3.3x0.95, pitch 3.05, per SXN datasheet).
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
  - U2 FLASH PACKAGE (learned 2026-10-22): the board pads are SOIC-8
    150mil (3.9x4.9mm). Almost all 128Mbit SPI NOR parts JLCPCB/LCSC
    stock are 208mil (incl. C97521 "W25Q128JVSIQ" - our old pin, and
    GD25Q128ESIG C2758105). 150mil 128Mbit parts exist but must be
    hand-sourced (DigiKey/Mouser): e.g. Infineon S25FL128LAGMFI010,
    ISSI IS25LP128-JBLE. Whichever you fit, check it against Raspberry
    Pi's RP2350 boot-ROM supported-flash list.
  - CRYSTAL (resolved per the RP2350 hardware design guide): Y1 must be
    12 MHz, 3225, CL=10pF (ABM8-272-T3 class) with the 15pF C23/C24
    load caps already on the BOM. A 20pF-load crystal (rev5's part) runs
    off-tune with 15pF caps - do not substitute.
  - L1 ORIENTATION: N/A for the SMNR4020 - it is non-polarized (no
    dot/marking). Any rotation mounts correctly.
  - Flash: hold BOOTSEL (SW1), plug USB into J1, drag
    firmware/imspi8080-rp2350.uf2.

REV6.1 (2026-10-15, post-JLCPCB-review fixes, this drop)
  - L1 footprint corrected: board carried the Bourns SRU5016 5.2x5.2mm
    land pattern while the part is the SXN SMNR4020 4.0x4.0x2.0mm
    (C135262). New embedded footprint L_SXNSMNR4020_4x4x2mm: pads
    3.3x0.95mm, pitch 3.05mm per SXN datasheet (see fix_rev6_l1.py).
  - GND opens fixed: isolated GND pads/islands (incl. U1-61 thermal
    pads) connected with stub tracks + vias + F.Cu bridges; zones
    refilled (see fix_rev6_gnd.py).
  - Re-verified after fixes: check_opens.py = every net single copper
    island; kicad-cli drc = no electrical violations (cosmetic only).

ORDERING ROUND 2 (2026-10-21, JLCPCB BOM upload): all rows auto-matched
except two, both expected:
  - J5: was deliberately unpinned (any 1x3 2.54mm TH header works);
    now pinned C49257 (BOOMELE 2.54-1*3P straight, 3A).
  - U7: C114218 is in JLCPCB's library as an Extended part and their
    auto-matcher skipped it; fix = click Search next to U7, enter
    "C114218" (Hirose DM3AT-SF-PEJM5), select manually. Do NOT accept
    TF-01A/C91145 as a substitute (wrong footprint). If you'd rather
    not pay Extended-part handling, drop U7 from the assembly and
    hand-solder the socket (optional part; DigiKey/Mouser ~$3).

ORDERING ROUND 3 (2026-10-22, JLCPCB pre-assembly review email):
  - Toggles SWD0-7/SWC0-3: JLCPCB asked for a placement image (TH
    toggles on SMD pads is unusual). Answered with
    placement-toggles-full.png + placement-toggles-zoom.png (annotated
    renders: circle = the 3 SMD pads SWD{n}V/S/G or SWC{n}V/C/G; the
    rectangular edge notch below = the bushing void at the CPL x,y).
    Toggle bushing fits the edge notch; its 3 lugs bend onto the
    circled pads and are soldered there.
  - U2: REAL MISMATCH, our BOM error (carried since rev5): C97521 is
    SOIC-8 208mil (JLCPCB part page + Winbond datasheet), board pads
    are 150mil - the leads cannot land. Chose option B: U2 left
    unpopulated, refunded; flash hand-soldered later (BOOTSEL UF2
    drag-and-drop programming still works with an empty/missing
    flash). rev7 fix: change U2 footprint to SOIC-8 208mil (de-facto
    standard for 128Mbit NOR) - see TODO.md.

CONTENTS (JLCPCB flow: upload gerbers zip at the board step; BOM + CPL
at the assembly steps - same flow as fab-rev5, same LCSC part numbers,
plus U1=C42411118; L1 pinned C135262 SMNR4020 4.0x4.0x2.0mm, no
in-tool substitution needed)
  gerbers/                        14 files + drill PTH/NPTH + gbrjob
  imspi8080-rev6-bom.csv (+xlsx)  96 rows, one per designator,
                                  LCSC Part # column included; exact
                                  parts pinned for the parts JLCPCB
                                  flagged: U7=C114218 (Hirose
                                  DM3AT-SF-PEJM5), SW1/SW2=C269272
                                  (C&K KMR221NGLFS), L1=C135262,
                                  Y1=C20625731, J5=C49257 (BOOMELE
                                  2.54-1*3P header). U2 LCSC cell left
                                  BLANK on purpose (see round-3 note
                                  above - no 150mil 128Mbit flash in
                                  JLCPCB's library).
  placement-toggles-full.png      annotated top render: 12 toggle
  placement-toggles-zoom.png      positions (circles=pads, notch=bushing
                                  void); sent to JLCPCB 2026-10-22
  imspi8080-rev6-cpl.csv          96 placements, JLCPCB columns, mm
  imspi8080_rev6.kicad_pcb/.pro   KiCad 10 source (schematic:
  ../../imspi8080.kicad_sch = regenerated from the rev6 netlist)

J1-A6 (USB-C duplicate D+ pad) is intentionally unconnected (plug
parallels A6/B6). Toggles mount through the 12 board voids; terminals
to the SWD*/SWC* V/S/G pads. Same case + faceplate as rev5.
