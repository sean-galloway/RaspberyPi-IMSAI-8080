IMSPI 8080 - rev4 fabrication package
=====================================

Board:  204.1 x 60.1 mm, 2-layer, FR4, 1 oz copper
        min track 0.15 mm / min clearance 0.127 mm (6/5 mil class)
        min hole 0.3 mm (via), 0.8 mm (mounting), NPTH connector holes separate
        finish: any (HASL or ENIG). No impedance, no controlled dielectric.

Works as-is with JLCPCB and PCBWay:
  - gerbers/  : all copper/mask/paste/silk/edge layers + Excellon drill,
                separated PTH/NPTH, plus the KiCad .gbrjob
  - imspi8080-rev4-bom.csv : BOM (Comment/Designator/Footprint/Qty/MPN/Notes);
                lines with "U3;U4"-style designators are one line per value,
                expand per the fab's importer if needed
  - imspi8080-rev4-cpl.csv : pick&place, JLCPCB column layout
                (Designator,Val,Package,Mid X,Mid Y,Rotation,Layer), mm,
                bottom-left origin. Verify rotation of D-pack/LED and the
                USB-C connector in the fab's placement preview.
  - imspi8080.kicad_pcb/.kicad_pro/.kicad_sch : KiCad 8 source

Assembly notes:
  - Mostly 0402 passives; 0.5 mm-pitch QFN-56 (RP2040) and HTSSOP-32 (TLC5947).
    Fine for basic/standard assembly service.
  - J1-A6 (USB-C duplicate D+ pad) is intentionally unconnected; D+ is routed
    via B6. The plug parallels A6/B6 - not a defect.
  - J4 pin 6 (SW_SPARE) is a deliberate no-connect spare.
  - Bottom-side parts exist (decoupling, several passives): the board is
    double-sided load; CPL "Layer" column carries the side.

Gerbers regenerate with:
  kicad-cli pcb export gerbers --output gerbers/ \
    --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
    imspi8080.kicad_pcb
  kicad-cli pcb export drill --excellon-separate-th --output gerbers/ imspi8080.kicad_pcb
