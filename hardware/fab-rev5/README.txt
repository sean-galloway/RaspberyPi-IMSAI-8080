IMSPI 8080 - rev5 fabrication package (ON-BOARD TOGGLES)
==========================================================

Board:  204.1 x 112.1 mm, 4-layer (SIG/GND-ish/SIG-ish/SIG - In1/In2 used
        as routed layers), FR4, 1 oz outer / 0.5 oz inner (std JLC/PCBWay 4L)
        min track 0.15 mm / min clearance 0.127 mm; via 0.6/0.3 (one 0.5/0.25
        blind pair - standard for any 4L fab)
        finish: any. No impedance requirements.

Works as-is with JLCPCB and PCBWay:
  - gerbers/  : all copper (4 layers) + mask/paste/silk + Edge.Cuts,
                Excellon drill split PTH/NPTH, .gbrjob
  - imspi8080-rev5-bom.csv (+ .xlsx): BOM, ONE ROW PER DESIGNATOR, 95 rows -
                exactly the 95 placements in the CPL, including the 12
                through-hole toggles (8x MTS-102 latching data SWD0-7,
                4x MTS-103-M momentary command SWC0-3; bushing center at the
                board-void center, Top side, rotation 0 = terminals toward
                the LED rows) and the J5 1x3 debug header (TH, top side).
                Only user-fitted parts: spare pull-ups R17/R18 (not placed).
                Upload the .csv or .xlsx at the BOM step.
  - imspi8080-rev5-cpl.csv : pick&place, 95 placements (JLCPCB columns, mm), incl. the 12 TH toggles;
                designators match the BOM 1:1. Also alone in jlcpcb-cpl/.
  - imspi8080_rev5.kicad_pcb / .kicad_pro / .kicad_sch : KiCad 8 source

WHAT'S NEW IN REV5 (vs rev4)
  - Full IMSAI-style toggle switch set ON the board: 12 SPDT toggles on
    SWPAD landing pads (36 pads), columns at 15 mm pitch directly under the
    LED rows, toggle bushings through the 12 board voids (Edge.Cuts).
    This is the "integrated switches" layout: no separate switch bracket,
    no J3/J4 harness - the panel plugs straight in.
  - Board height 112 mm (2U face) per docs/panel-layout.md.
  - 4-layer: 2-layer was attempted first (81/82 nets routed) and the last
    net (XOUT) was geometrically caged by its own neighbors; 4-layer was the
    pre-approved fallback and routed everything.

ASSEMBLY NOTES - THREE ITEMS (KiCad DRC: 0 errors, 3 documented items)
  Open-net check: kicad-cli drc does NOT report unconnected nets on this
  board (verified 2026-10-10 - no exclusions, not severity/prl gated).
  Before fab / after any edit run:  python3 check_opens.py
  It flood-fills copper (layer-aware, incl. the GND pour) and fails on any
  net that is not a single copper island, with an allow-list for the two
  assembly items below.
  1. HC_QH (U1 pin 12 -> U6 pin 9): add one 30 AWG wire, ~45 mm, at assembly.
     The pin-12 cluster admits no via; pads are both large and accessible.
  2. TLC_SCLK bridge: add one ~10 mm wire (a 0-ohm 0402 cannot span the
     gap) between the two TLC_SCLK islands, top copper:
       - U1-4 stub end: via at (124.32, 94.60)
       - chain stub:   (124.64, 102.34), via at (125.06, 102.76)
     Verified by direct copper trace 2026-10-10: island A = {U1-4 pad,
     2 tracks, via (124.32,94.60)}; island B = the U3-3 -> U4-3 chain
     (the 5.1 mm tail ending at (189.53,105.91) is a dead stub - ignore).
  3. GND pour has one isolated island pair (cosmetic; every GND pad is
     connected). Optional: one via anywhere in the pour stitches it.
  J1-A6 (USB-C duplicate D+ pad) is intentionally unconnected (plug
  parallels A6/B6; D+ routed via B6).

Gerbers regenerate with:
  kicad-cli pcb export gerbers --output gerbers/ \
    --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
    imspi8080_rev5.kicad_pcb
  kicad-cli pcb export drill --excellon-separate-th --output gerbers/ imspi8080_rev5.kicad_pcb
