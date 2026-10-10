IMSPI 8080 — design deliverables
================================
Clean copies of the finished design artifacts. (Working files + the archived PCB
effort live in ../ and ../OLD/.)

BILL OF MATERIALS
  bom.csv                         parts list (ref, value, footprint, MPN, notes)

SCHEMATIC
  imspi8080_skidl.py              schematic-as-code (SKiDL); emits the netlist.
                                  Consistent with bom.csv. NOTE: describes the
                                  original J3/J4 switch-header wiring.
  imspi8080.kicad_sch             KiCad schematic (open imspi8080.kicad_pro)
  imspi8080.kicad_pro / .kicad_prl  KiCad project files (double-click the .pro)
  imspi8080.net                   netlist (KiCad format)
  gen_schematic.py                regenerates imspi8080.kicad_sch from the netlist

FASCIA HOLE PATTERN (mechanical)
  imspi8080-holes.dxf             CAD geometry — layers: SWITCH_HOLES (6.2mm dia),
                                  LED_WINDOWS, LED_CENTRES, RACK_SLOTS, OUTLINE.
                                  mm; origin BOTTOM-LEFT; frame 254 x 132 (10" 3U).
  imspi8080-hole-positions.csv    every feature: type, ref, X, Y, dia/W, H
  imspi8080-holes-drawing.png     dimensioned reference view
  gen_holes.py                    regenerates the .dxf + .csv
                                  NOTE: switch-row Y is set for the void-design
                                  fascia; LED windows + all X-positions are fixed.

FASCIA 3D MODEL
  faceplate_3d.stl                printable 10" 3U fascia (recessed ink labels)
  faceplate_3d.scad               OpenSCAD source
  faceplate_preview.png           painted-color preview
