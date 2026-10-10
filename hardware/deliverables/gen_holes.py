#!/usr/bin/env python3
"""Emit the LED + switch (+ mount) hole pattern of the IMSPI 8080 fascia as CAD data.

Coordinates match gen_faceplate_3d.py exactly. Physical frame: 254 x 132 mm (10" 3U),
origin BOTTOM-LEFT, X right, Y up (standard mechanical convention). Outputs:
  imspi8080-holes.dxf            geometry (circles = holes, polylines = slots/windows)
  imspi8080-hole-positions.csv   every feature: type, ref, X, Y, W/dia, H
  imspi8080-holes.svg            dimensioned reference drawing
"""
import csv

FACE_W, FACE_H = 254.0, 132.0
AP_X, AP_Y = 25.0, 10.0
fx = lambda b: AP_X + b                 # board-x -> fascia-x
pd = lambda dy: FACE_H - (AP_Y + dy)    # board/design-y -> physical-y (Y up)

LEFT_COLS   = [14, 29, 44, 59, 74, 89, 104, 119]
STATUS_COLS = [147, 162, 177, 192]
ROW_Y = [64, 76, 88]                    # LED rows (board y)
STATUS_Y = 76
LEFT_WIN, STATUS_WIN = (9, 124), (142, 197)
LED_WIN_H = 6.0
TOG_D = 6.2                             # MTS-123/223 bushing hole
TOG_ROW_DY = 103                        # switch row (board y, over the voids)  [void design]
LED_MARK_D = 1.6                        # 1206 LED body reference mark

feat = []   # (kind, ref, x, y, w, h)  kind: hole|slot|ledmark|mount
# LED windows (fascia openings — one slot per row)
for r, by in enumerate(ROW_Y):
    x0, x1 = fx(LEFT_WIN[0]), fx(LEFT_WIN[1])
    feat.append(("slot", f"LEDWIN_L{r}", (x0+x1)/2, pd(by), x1-x0, LED_WIN_H))
sx0, sx1 = fx(STATUS_WIN[0]), fx(STATUS_WIN[1])
feat.append(("slot", "LEDWIN_STATUS", (sx0+sx1)/2, pd(STATUS_Y), sx1-sx0, LED_WIN_H))
# individual LED centres (reference marks): 24 main + 4 status
n = 1
for r, by in enumerate(ROW_Y):
    for c, bx in enumerate(LEFT_COLS):
        feat.append(("ledmark", f"D{n}", fx(bx), pd(by), LED_MARK_D, LED_MARK_D)); n += 1
for i, bx in enumerate(STATUS_COLS):
    feat.append(("ledmark", f"D{25+i}", fx(bx), pd(STATUS_Y), LED_MARK_D, LED_MARK_D))
# switch bushing holes
for i, bx in enumerate(LEFT_COLS):
    feat.append(("hole", f"SW_DATA{i}", fx(bx), pd(TOG_ROW_DY), TOG_D, TOG_D))
for i, bx in enumerate(STATUS_COLS):
    feat.append(("hole", f"SW_CMD{i}", fx(bx), pd(TOG_ROW_DY), TOG_D, TOG_D))
# 4 corner rack-mount slots (oval 9.33 x 6.77)
for cx in (8, FACE_W-8):
    for cy in (5.5, FACE_H-5.5):
        feat.append(("mount", f"MNT", cx, cy, 9.33, 6.77))

# ---- CSV ----
with open("imspi8080-hole-positions.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["type", "ref", "X_mm", "Y_mm", "W_or_dia_mm", "H_mm", "note"])
    notes = {"slot":"LED window (thru)","ledmark":"LED centre (1206, ref only)","hole":"switch bushing hole (thru)","mount":"rack slot (oval, thru)"}
    for k, ref, x, y, ww, hh in feat:
        w.writerow([k, ref, f"{x:.2f}", f"{y:.2f}", f"{ww:.2f}", f"{hh:.2f}" if k!="hole" else "", notes[k]])

# ---- DXF (R12 ASCII) ----
def circle(l, x, y, r): return f"0\nCIRCLE\n8\n{l}\n10\n{x:.3f}\n20\n{y:.3f}\n40\n{r:.3f}\n"
def line(l, x1, y1, x2, y2): return f"0\nLINE\n8\n{l}\n10\n{x1:.3f}\n20\n{y1:.3f}\n11\n{x2:.3f}\n21\n{y2:.3f}\n"
def rect(l, x, y, w, h):
    a,b,c,d = x-w/2, y-h/2, x+w/2, y+h/2
    return line(l,a,b,c,b)+line(l,c,b,c,d)+line(l,c,d,a,d)+line(l,a,d,a,b)
def slot(l, x, y, w, h):   # oval: two arcs approximated by end-circles + side lines
    r=h/2; a,b=x-(w-h)/2, x+(w-h)/2
    return circle(l,a,y,r)+circle(l,b,y,r)+line(l,a,y-r,b,y-r)+line(l,a,y+r,b,y+r)
body = ["0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n",
        "0\nSECTION\n2\nENTITIES\n"]
body.append(rect("OUTLINE", FACE_W/2, FACE_H/2, FACE_W, FACE_H))
for k, ref, x, y, ww, hh in feat:
    if k == "hole":   body.append(circle("SWITCH_HOLES", x, y, ww/2))
    elif k == "ledmark": body.append(circle("LED_CENTRES", x, y, ww/2))
    elif k == "slot": body.append(slot("LED_WINDOWS", x, y, ww, hh))
    elif k == "mount": body.append(slot("RACK_SLOTS", x, y, ww, hh))
body.append("0\nENDSEC\n0\nEOF\n")
open("imspi8080-holes.dxf", "w").write("".join(body))
print("wrote imspi8080-holes.dxf, imspi8080-hole-positions.csv (",
      sum(1 for f in feat if f[0]=='hole'), "switch holes,",
      sum(1 for f in feat if f[0]=='ledmark'), "LED marks,",
      sum(1 for f in feat if f[0]=='slot'), "LED windows )")
