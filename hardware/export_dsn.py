"""Export the placed rev4 board to a Specctra DSN for Freerouting."""
import os
import pcbnew

b = pcbnew.LoadBoard("imspi8080.kicad_pcb")
out = os.path.abspath("imspi8080.dsn")
ok = pcbnew.ExportSpecctraDSN(b, out)
print("dsn export:", ok, out)
