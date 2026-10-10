"""Import a Freerouting Specctra SES session back into the rev4 board."""
import os
import pcbnew

F = "imspi8080.kicad_pcb"
b = pcbnew.LoadBoard(F)
ok = pcbnew.ImportSpecctraSES(b, os.path.abspath("imspi8080.ses"))
if ok:
    b.Save(F)
print("ses import:", ok)
