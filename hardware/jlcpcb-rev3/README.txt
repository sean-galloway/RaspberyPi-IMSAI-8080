IMSPI 8080 rev3 — JLCPCB upload package
=======================================
Board: 204 x 99.7 mm, 2-layer, 1.6 mm FR-4, HASL. 83 SMT parts.
Fully routed, DRC-clean (0 unconnected, 0 errors).

WHAT'S DIFFERENT FROM REV1/REV2
- The panel switches are NOT on a separate bracket wired through JST connectors
  (rev1/rev2 J3/J4). Instead each switch has its own labeled solder LANDING-PAD
  cluster along the board's BOTTOM EDGE:
    SWD0..7 : 1x3 pads [V=+3V3, Sn=data common, G=GND]  (MTS-123 SPDT data toggles)
    SWC0..3 : 2x3 pads [Cn=cmd common, G=GND, +4 spare]  (MTS-223 DPDT command toggles)
  The switches mount on the fascia just below the board and jumper straight up to
  these pads. Back-silk labels every pad. These pads are BARE — hand-soldered — so
  they are excluded from the CPL/BoM (JLCPCB places nothing there).

UPLOAD ORDER
1. jlcpcb.com -> Add Gerber -> upload  imspi8080-rev3-gerbers.zip
   (auto-detects 2-layer, 204 x 99.7 mm)
2. Enable SMT Assembly -> "Assemble both sides".
3. Placement file (CPL):  imspi8080-rev3-cpl.csv   (Designator, Mid X, Mid Y, Layer, Rotation)
4. BOM:                   imspi8080-rev3-bom.csv   (83 placed parts)
5. Step through part matching; confirm each turns green. U2 flash must be the 3.3 V
   part (W25Q128JVSIQ, not the 1.8 V JW). Verify pin-1 rotations in the preview.

NOTES
- Ground is routed as traces (no plane) - fine for this low-speed panel.
- Mounting holes H1-H6 are NPTH and excluded from the CPL (correct).
- The 12 switch landing pads (SWD0-7, SWC0-3) are hand-jumpered to fascia toggles
  and are intentionally absent from the CPL/BoM.
