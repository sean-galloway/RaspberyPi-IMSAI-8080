"""Place the 28 IMSPI 8080 LEDs on an exact grid in KiCad's PCB editor.

Answers "can I place LEDs exactly?" -> yes. Run from KiCad:
    Tools -> Scripting Console, then:
    exec(open('/path/to/place_leds.py').read())

Targets KiCad 8/9 (VECTOR2I / FromMM). For KiCad 6, swap VECTOR2I -> wxPoint.
Coordinates are mm relative to the board origin; shift GRID_X0/GRID_Y0 to line
the grid up with your board datum / bezel holes.
"""
import pcbnew

# --- grid definition (mm) --------------------------------------------------
GRID_X0   = 15.0   # x of the leftmost left-block column
GRID_Y0   = 10.0   # y of the top LED row
COL_PITCH = 15.0   # column spacing == switch pitch (LEDs sit over the toggles)
ROW_PITCH = 12.0   # row spacing
RIGHT_X0  = 160.0  # x of the first right-block (status) column
STATUS_Y  = GRID_Y0 + ROW_PITCH   # status row aligned to the middle row

# Reference-designator -> grid mapping (matches the TLC5947 channel map):
#   D1..D8   addr hi  A15..A8   row 0
#   D9..D16  addr lo  A7..A0    row 1
#   D17..D24 data     D7..D0    row 2
#   D25..D28 status             right block, status row
def led_xy(n):
    if n <= 24:
        row, col = divmod(n - 1, 8)
        return GRID_X0 + col * COL_PITCH, GRID_Y0 + row * ROW_PITCH
    return RIGHT_X0 + (n - 25) * COL_PITCH, STATUS_Y

board = pcbnew.GetBoard()
placed = 0
for n in range(1, 29):
    ref = f"D{n}"
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        print(f"  {ref} not found - skipping")
        continue
    x, y = led_xy(n)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientationDegrees(0)
    placed += 1

print(f"placed {placed}/28 LEDs")
pcbnew.Refresh()
