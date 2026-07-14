IMSPI 8080 — JLCPCB upload package
==================================
Board: 214 x 70 mm, 2-layer, 1.6 mm FR-4, HASL. 85 SMT parts (45 top, 40 bottom).

UPLOAD ORDER
1. jlcpcb.com -> Order Now / Add Gerber -> upload  imspi8080-gerbers.zip
   (auto-detects 2-layer, 214 x 70 mm)
2. Enable SMT Assembly -> "Assemble both sides".
3. Placement file (CPL):  imspi8080-cpl.csv   (Designator, Mid X, Mid Y, Layer, Rotation)
4. BOM:                   imspi8080-bom.csv
5. Step through part matching; confirm each turns green. Watch for any LED/socket
   flagged "Standard Only". Verify pin-1 rotations in the preview before paying.

NOTES
- Ground is routed as traces (no plane) - fine for this low-speed panel.
- Mounting holes H1-H6 are NPTH and excluded from the CPL (correct).
- Mechanical: mounts in a 3U 10" face; toggles go on a separate bracket wired to J3/J4.
