#!/usr/bin/env python3
"""Generate a 3-D IMSPI 8080 faceplate (.scad) with INK-RECESS labels.

The legend text + IMSAI frame are cut as shallow **depressions** (RECESS mm deep) into
the front face — flood them with paint and wipe the surface flat, leaving filled labels.
Paint scheme: **branding = white, everything else = gold** (frame gold too). LED windows,
toggle-paddle holes, PCB standoff holes, and rack-ear slots are cut through.

Labels + grid come from the turret HMI (jetson-marker-turret), aligned to the rev2
204 x 60 PCB LED grid. Emits:
  faceplate_3d.scad     - manufacturable model (recesses cut) -> STL for print/CNC
  faceplate_paint.scad  - colour preview (dark panel + gold/white paint inlays)
"""
from pathlib import Path

# ---- panel + recess depths (mm) ------------------------------------------
FACE_W, FACE_H, TH = 254.0, 132.0, 4.0   # per ten-inch-rack-specs.md: 254 wide, 3U=132, printed face 4-5mm
RECESS   = 0.7
# faux frame = inset ring around the content; the ears (mounting slots) sit OUTSIDE it
FR_X0, FR_X1, FR_Y0, FR_Y1, FW = 27, 227, 16, 128, 3.0
TOG_D, LED_WIN_H = 6.2, 6.0   # 6.2 = MTS-123/223 bushing
# PCB mounts: standoff BOSSES on the BACK; screw from the PCB side into a BLIND hole.
# Front face stays solid (no visible screw holes).
STANDOFF   = 3.5     # boss height = faceplate-back-to-PCB gap (LEDs sit behind windows)
BOSS_OD    = 5.5     # standoff boss outer dia
SCREW_PILOT= 2.1     # M2.5 self-tapping pilot (use ~3.4 for a heat-set insert)
FRONT_WALL = 1.0     # solid panel left in front of the blind hole (no front breakthrough)
# paint colours
C_PANEL, C_GOLD, C_WHITE, C_BLUE = "#1a1c22", "#d4af37", "#f2f2ee", "#5b9fd4"

# ---- grid (matches gen_front_panel.py / place_leds.py rev2) ---------------
LEFT_COLS   = [14, 29, 44, 59, 74, 89, 104, 119]
STATUS_COLS = [147, 162, 177, 192]
ROW_Y, STATUS_Y = [64, 76, 88], 76   # rev3: LEDs at the BOTTOM of the board
LEFT_WIN, STATUS_WIN = (9, 124), (142, 197)
# rev3: board mounts LEDs-low; fx=25+bx (204 centered in 254), fy=6+by (board top near fascia top)
AP_X, CONTENT_DX, AP_Y, TOP_BAND, TOGGLE_Z = 25, 0, 6, 0, 19
fx = lambda xd: AP_X + CONTENT_DX + xd
fy = lambda yd: AP_Y + TOP_BAND + yd
TOG_CY = FACE_H - TOGGLE_Z

# ---- turret labels --------------------------------------------------------
NODES  = ["JET", "PI5", "PICO", "ZED", "LIDAR", "NET", "48V", "12V"]
STATUS = ["ARMED", "TRACK", "FAULT", "PWR"]
TOG_DATA = ["MODE", "TRACK", "LASER", "NIGHT", "REC", "VERB", "-", "-"]
TOG_CMD  = ["TEST", "PAGE", "HOME", "ARM"]

# ---- label list: (x, y_down, text, size, halign, bold, colour) ------------
T = []
def add(x, y, s, sz, ha, bold, col="gold"): T.append((x, y, s, sz, ha, bold, col))
for lbl, xd in zip(NODES, LEFT_COLS):     add(fx(xd), fy(ROW_Y[0])-5.0, lbl, 2.5, "center", False)
add((fx(STATUS_COLS[0])+fx(STATUS_COLS[-1]))/2, fy(STATUS_Y)-5.6, "- STATUS -", 2.4, "center", False)
for lbl, xd in zip(STATUS, STATUS_COLS):  add(fx(xd), fy(STATUS_Y)+7.0, lbl, 2.3, "center", False)
gap_cx = (fx(LEFT_WIN[1]) + fx(STATUS_WIN[0]))/2
for name, yc in zip(["NODES", "PAN", "TILT"], ROW_Y): add(gap_cx, fy(yc)+0.9, name, 2.4, "center", True)
add((fx(LEFT_COLS[0])+fx(LEFT_COLS[-1]))/2, TOG_CY-8.5, "- MODE / CONFIG -", 2.3, "center", False)
add((fx(STATUS_COLS[0])+fx(STATUS_COLS[-1]))/2, TOG_CY-8.5, "- COMMAND -", 2.3, "center", False)
for lbl, xd in zip(TOG_DATA, LEFT_COLS):  add(fx(xd), TOG_CY+8.6, lbl, 2.3, "center", False)
for lbl, xd in zip(TOG_CMD, STATUS_COLS): add(fx(xd), TOG_CY+8.6, lbl, 2.3, "center", lbl == "ARM")
add((fx(STATUS_COLS[0])+fx(STATUS_COLS[-1]))/2, TOG_CY+11.8, "soft . hw switch arms", 1.7, "center", False)
# rev3: large centered masthead filling the band above the LEDs (electronics hide behind it)
# two-column masthead: MARKER SENTRY (left) + IMSPI 8080 (right), taglines beneath
# brands aligned to the LED block edges (left window x=34, right window x=222)
add(34, 32, "MARKER SENTRY", 5.5, "left", True, "white")
add(222, 32, "IMSPI 8080", 7.0, "right", True, "white")
add(34, 43, "GROUND STATION . autonomous marker turret", 3.0, "left", False, "white")
add(222, 43, "SPX LABS . HMI", 3.0, "right", False, "white")

WINDOWS = [(LEFT_WIN[0], LEFT_WIN[1], yc) for yc in ROW_Y] + [(STATUS_WIN[0], STATUS_WIN[1], STATUS_Y)]
TOGGLES = [(fx(xd), TOG_CY) for xd in LEFT_COLS] + [(fx(xd), TOG_CY) for xd in STATUS_COLS]
MOUNTS  = [(fx(hx), fy(hy)) for hx, hy in [(8,8),(131,8),(196,8),(8,87),(131,87),(196,87)]]  # rev3 holes

def Y(yd): return FACE_H - yd

MOUNTS_SCAD = ",".join(f"[{mx:.2f},{FACE_H-my:.2f}]" for mx, my in MOUNTS)
HEAD = f"""$fn=48; FACE_W={FACE_W}; FACE_H={FACE_H}; TH={TH}; RECESS={RECESS}; eps=0.05;
STANDOFF={STANDOFF}; BOSS_OD={BOSS_OD}; SCREW_PILOT={SCREW_PILOT}; FRONT_WALL={FRONT_WALL};
mounts=[{MOUNTS_SCAD}];
module bosses(){{ for(m=mounts) translate([m[0],m[1],-STANDOFF]) cylinder(h=STANDOFF+eps,d=BOSS_OD); }}
module screw_blind(){{ for(m=mounts) translate([m[0],m[1],-STANDOFF-1]) cylinder(h=STANDOFF+1+TH-FRONT_WALL,d=SCREW_PILOT); }}
module rrect(w,h,r){{ hull() for(sx=[-1,1],sy=[-1,1]) translate([sx*(w/2-r),sy*(h/2-r)]) circle(r); }}
module label(x,y,s,sz,ha,bold){{ translate([x,y,TH-RECESS]) linear_extrude(RECESS+eps)
  text(s,size=sz,halign=ha,valign="baseline",font=bold?"DejaVu Sans Mono:style=Bold":"DejaVu Sans Mono"); }}
module thru_rrect(x,y,w,h,r){{ translate([x,y,-1]) linear_extrude(TH+2) rrect(w,h,r); }}
module thru_circ(x,y,d){{ translate([x,y,-1]) linear_extrude(TH+2) circle(d/2); }}
module frame_recess(){{ translate([0,0,TH-RECESS]) linear_extrude(RECESS+eps) union(){{
    translate([{FR_X0},{FACE_H-FR_Y1}]) square([{FW},{FR_Y1-FR_Y0}]);            // left bar
    translate([{FR_X1-FW},{FACE_H-FR_Y1}]) square([{FW},{FR_Y1-FR_Y0}]);         // right bar
    translate([{FR_X0},{FACE_H-FR_Y0-FW}]) square([{FR_X1-FR_X0},{FW}]); }} }}    // top bar (open bottom)
"""

def labels_scad(only=None):
    out = []
    for x, yd, txt, sz, ha, bold, col in T:
        if only and col != only: continue
        out.append(f'  label({x:.2f},{Y(yd):.2f},"{txt}",{sz},"{ha}",{str(bold).lower()});')
    return "\n".join(out)

def cuts_scad():
    s = ["module cuts(){ union(){", "  frame_recess();", labels_scad()]
    s.append("  // LED windows (through)")
    for x0, x1, yc in WINDOWS:
        cx, w = (fx(x0)+fx(x1))/2, (fx(x1)-fx(x0))
        s.append(f"  thru_rrect({cx:.2f},{Y(fy(yc)):.2f},{w:.2f},{LED_WIN_H},1.4);")
    s.append("  // toggle holes + ear slots (through) — mounts are BACK bosses, not here")
    for x, yd in TOGGLES: s.append(f"  thru_circ({x:.2f},{Y(yd):.2f},{TOG_D});")
    for cx in (8, FACE_W-8):
        for cy in (5.5, FACE_H-5.5): s.append(f"  thru_rrect({cx:.2f},{cy:.2f},9.33,6.77,3.3);")
    s.append("} }")
    return "\n".join(s)

def scad_fab():
    return HEAD + cuts_scad() + "\ndifference(){ union(){ cube([FACE_W,FACE_H,TH]); bosses(); } cuts(); screw_blind(); }\n"

def scad_paint():
    return (HEAD + cuts_scad() + f"""
color("{C_PANEL}") difference(){{ union(){{ cube([FACE_W,FACE_H,TH]); bosses(); }} cuts(); screw_blind(); }}
color("{C_BLUE}") frame_recess();
color("{C_GOLD}") {{
{labels_scad('gold')}
}}
color("{C_WHITE}") {{
{labels_scad('white')}
}}
""")

if __name__ == "__main__":
    d = Path(__file__).resolve().parent
    (d/"faceplate_3d.scad").write_text(scad_fab())
    (d/"faceplate_paint.scad").write_text(scad_paint())
    ng = sum(1 for t in T if t[6] == "gold"); nw = len(T) - ng
    print(f"wrote faceplate_3d.scad + faceplate_paint.scad  ({nw} white / {ng} gold labels)")
