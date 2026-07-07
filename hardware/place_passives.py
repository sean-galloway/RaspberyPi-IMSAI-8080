"""Place the 40 decoupling caps / resistors on the BACK side (B.Cu) at precomputed,
collision-free positions near their owner IC.

Positions were solved offline against the real board geometry (this exact layout):
each passive is packed as close to its owner as possible while clearing the board
edge, the 6 mounting-hole keepouts, and the through-hole parts (J1/J2 USB-C, J3/J4
JST, J5 SWD, U7 microSD), and staying >=2.8 mm from every other passive. The back
side is otherwise empty, so decoupling is short and GND pads land in the B.Cu plane.

Re-runnable: flips a passive to the back only if it's still on the front, then sets
its position. If you move the ICs, re-solve (ask) rather than editing by hand.

Run from a FRESH KiCad Scripting Console (Tools -> Scripting Console), flush to >>>:
    exec(open('/mnt/data/github/RaspberyPi-IMSAI-8080/hardware/place_passives.py').read())
"""
import pcbnew

# ref -> (x, y) in mm, board coordinates (collision-free by construction)
POS = {
    'C1': (135.1, 101.44), 'C2': (137.9, 101.44), 'C3': (136.5, 103.865),
    'C4': (133.7, 103.865), 'C5': (132.675, 100.04), 'C6': (136.5, 99.015),
    'C15': (140.524, 102.833), 'C16': (138.101, 106.168), 'C17': (134.051, 106.941),
    'R5': (130.57, 104.732), 'R6': (129.544, 100.738),
    'C11': (132.98, 69.91), 'C19': (135.78, 69.91),
    'C7': (103.29, 103.38), 'R7': (105.715, 104.78),
    'C8': (204.71, 89.38), 'R8': (207.135, 90.78),
    'C9': (86.14, 104.78),
    'C10': (186.14, 89.28), 'R13': (188.94, 89.28), 'R14': (187.54, 91.705),
    'R15': (183.715, 90.68), 'R16': (183.715, 87.88),
    'C12': (238.401, 99.002), 'C18': (229.652, 90.785), 'R9': (229.3, 88.0),
    'R10': (229.652, 85.215), 'R11': (237.039, 77.348), 'R12': (239.797, 76.822),
    'C13': (119.35, 109.5), 'C20': (122.15, 109.5), 'C22': (120.75, 111.925),
    'R1': (116.925, 110.9), 'R2': (116.925, 108.1),
    'C14': (56.5, 104.0), 'C21': (58.925, 105.4), 'R3': (55.1, 106.425), 'R4': (54.075, 102.6),
    'C23': (133.6, 83.35), 'C24': (136.4, 83.35),
}

board = pcbnew.GetBoard()
_by_ref = {f.GetReference(): f for f in board.GetFootprints()}

placed, missing = 0, []
for ref, (x, y) in POS.items():
    f = _by_ref.get(ref)
    if f is None:
        missing.append(ref)
        continue
    if f.GetLayer() != pcbnew.B_Cu:          # move to back only if still on front
        f.Flip(f.GetPosition(), False)
    f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    placed += 1

print(f"placed {placed}/40 back-side passives" +
      (f" | missing: {', '.join(missing)}" if missing else ""))
pcbnew.Refresh()
