#!/usr/bin/env python3
"""
Generate the IMSAI-8080 turret-HMI front-panel legend/silkscreen (SVG, to scale mm).

Grid = the SAME datum as the RaspberyPi-IMSAI-8080 PCB (place_leds.py): datum =
top-left of the board, +x right, +y DOWN. Lamp/switch meanings from the turret's
docs/Imsai_Panel_HMI.md.

**Aligned to the rev2 204 x 60 PCB** (grabbed from jetson-marker-turret). The LED
columns/rows below MUST match place_leds.py (GRID_X0=14, RIGHT_X0=147, rows 6/18/30)
so the window recesses sit over the real LEDs. The engraved legend text + window slots
are the paint recesses. If the PCB LED grid changes, update both together.

Output: hardware/faceplate/imspi_panel_front.svg
Render: rsvg-convert -w 1800 imspi_panel_front.svg -o imspi_panel_front.png
"""
from pathlib import Path

# ---- Face + aperture (mm) — matches rack_shelf.scad (U=44 -> 3U=132) ----------
FACE_W, FACE_H = 254.0, 132.0
AP_X, AP_Y     = 20.0, 5.0            # aperture inset within the face
AP_W, AP_H     = 214.0, 122.0

# ---- Grid (datum coords) — rev2 PCB, matches place_leds.py ---------------------
LEFT_COLS   = [14, 29, 44, 59, 74, 89, 104, 119]   # 8 data/addr cols, 15 mm pitch (GRID_X0=14)
STATUS_COLS = [147, 162, 177, 192]                 # 4 status cols (RIGHT_X0=147)
ROW_Y       = [6, 18, 30]                           # LED rows on the board (GRID_Y0=6, pitch 12)
STATUS_Y    = 18                                     # status row = middle row
TOP_BRAND_BAND = 33                                 # top band for branding (board drops this)
TOGGLE_Z    = 24                                    # toggle row center above fascia bottom (low)
WIN_H       = 6                                     # LED window slot height
LEFT_WIN    = (9, 124)                              # left window x-span (brackets 14..119)
STATUS_WIN  = (142, 197)                            # status window x-span (brackets 147..192)

# ---- Meanings (docs/Imsai_Panel_HMI.md) ---------------------------------------
NODES  = ["JET", "PI5", "PICO", "ZED", "LIDAR", "NET", "48V", "12V"]   # row1 b7..b0
STATUS = ["ARMED", "TRACK", "FAULT", "PWR"]
TOG_DATA = ["MODE", "TRACK", "LASER", "NIGHT", "REC", "VERB", "–", "–"]
TOG_CMD  = ["TEST", "PAGE", "HOME", "ARM"]
PAN_LIT, TILT_LIT = 5, 3     # demo bargraph fill (of 8)

# ---- Palette ------------------------------------------------------------------
C_FACE_A, C_FACE_B = "#20232b", "#161821"   # faceplate gradient
C_EDGE   = "#3a3f4d"
C_WIN    = "#0b0c10"
C_LAMP   = "#ff4d3d"       # diffused-red LEDs (true to hardware)
C_LAMP_OFF = "#3a2422"
C_TXT    = "#e6e8ee"
C_MUTE   = "#9aa0ad"
C_ACCENT = "#ffb02e"       # section accents / branding
C_SILVER_A, C_SILVER_B = "#e9edf3", "#8b93a3"
C_FRAME  = "#2f7fe6"       # IMSAI blue frame
C_FRAME_D = "#1d55a6"      # frame inner bevel (shadow)
C_BLUE   = "#2f6fe0"       # data paddle caps
C_RED    = "#e23a2e"       # command paddle caps
FRAME_W, FRAME_TOP = 6.0, 11.0

CONTENT_DX = -3    # centre the left-heavy block layout (match rack_shelf.scad content_dx)
def fx(xd): return AP_X + CONTENT_DX + xd
def fy(yd): return AP_Y + TOP_BRAND_BAND + yd    # board features drop below the branding band
TOG_CY = FACE_H - TOGGLE_Z                        # toggle row (placed low, independent of the board)

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text(x, y, s, size, fill=C_TXT, anchor="middle", weight="normal",
         ls="0", opacity="1"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}" '
            f'opacity="{opacity}" font-family="DejaVu Sans Mono, monospace">'
            f'{esc(s)}</text>')

def build():
    e = []
    # defs: gradients + lamp glow
    e.append(f'''<defs>
      <linearGradient id="face" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{C_FACE_A}"/><stop offset="1" stop-color="{C_FACE_B}"/>
      </linearGradient>
      <radialGradient id="knob" cx="0.35" cy="0.30" r="0.75">
        <stop offset="0" stop-color="{C_SILVER_A}"/><stop offset="1" stop-color="{C_SILVER_B}"/>
      </radialGradient>
      <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
        <feGaussianBlur stdDeviation="0.7" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>''')

    # faceplate + subtle inner border
    e.append(f'<rect x="0" y="0" width="{FACE_W}" height="{FACE_H}" rx="4" '
             f'fill="url(#face)" stroke="{C_EDGE}" stroke-width="0.6"/>')
    e.append(f'<rect x="3" y="3" width="{FACE_W-6}" height="{FACE_H-6}" rx="3" '
             f'fill="none" stroke="{C_EDGE}" stroke-width="0.3" opacity="0.6"/>')

    # IMSAI blue ⊓ frame — proud border wrapping the sides + top (open bottom)
    for x0 in (0, FACE_W - FRAME_W):
        e.append(f'<rect x="{x0}" y="0" width="{FRAME_W}" height="{FACE_H}" '
                 f'fill="{C_FRAME}"/>')
    e.append(f'<rect x="{FRAME_W}" y="0" width="{FACE_W-2*FRAME_W}" '
             f'height="{FRAME_TOP}" fill="{C_FRAME}"/>')
    # inner bevel (shadow) so the frame reads as proud
    e.append(f'<rect x="{FRAME_W}" y="{FRAME_TOP}" width="{FACE_W-2*FRAME_W}" '
             f'height="0.7" fill="{C_FRAME_D}"/>')
    for x0 in (FRAME_W-0.7, FACE_W-FRAME_W):
        e.append(f'<rect x="{x0}" y="{FRAME_TOP}" width="0.7" '
                 f'height="{FACE_H-FRAME_TOP}" fill="{C_FRAME_D}"/>')

    # rack-mount oval slots (4 corners) — with a relief in the blue frame
    sw, sh = 9.33, 6.77
    for cx in (8, FACE_W - 8):
        for cy in (5.5, FACE_H - 5.5):
            e.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{C_FACE_B}"/>')   # relief
            e.append(f'<rect x="{cx-sw/2:.2f}" y="{cy-sh/2:.2f}" width="{sw}" '
                     f'height="{sh}" rx="{sh/2:.2f}" fill="{C_WIN}" '
                     f'stroke="{C_EDGE}" stroke-width="0.3"/>')

    # ---- LED windows (diffuser slots) ----
    def window(x0, x1, yc):
        e.append(f'<rect x="{fx(x0):.2f}" y="{fy(yc)-WIN_H/2:.2f}" '
                 f'width="{fx(x1)-fx(x0):.2f}" height="{WIN_H}" rx="1.4" '
                 f'fill="{C_WIN}" stroke="{C_ACCENT}" stroke-width="0.25" opacity="0.98"/>')
    for yc in ROW_Y:
        window(*LEFT_WIN, yc)
    window(*STATUS_WIN, STATUS_Y)

    def lamp(xd, yc, lit=True):
        col = C_LAMP if lit else C_LAMP_OFF
        filt = ' filter="url(#glow)"' if lit else ''
        e.append(f'<circle cx="{fx(xd):.2f}" cy="{fy(yc):.2f}" r="1.5" '
                 f'fill="{col}"{filt}/>')

    # row1 nodes (all lit as legend), row2 pan bargraph, row3 tilt bargraph
    for i, xd in enumerate(LEFT_COLS):
        lamp(xd, ROW_Y[0], True)
        lamp(xd, ROW_Y[1], i < PAN_LIT)
        lamp(xd, ROW_Y[2], i < TILT_LIT)
    for xd in STATUS_COLS:
        lamp(xd, STATUS_Y, True)

    # ---- labels: row1 node bits (above row1 window) ----
    for lbl, xd in zip(NODES, LEFT_COLS):
        e.append(text(fx(xd), fy(ROW_Y[0]) - 5.0, lbl, 2.5, C_MUTE))
    # status labels (above status window)
    e.append(text((fx(STATUS_COLS[0])+fx(STATUS_COLS[-1]))/2, fy(STATUS_Y)-5.6,
                  "— STATUS —", 2.4, C_ACCENT, ls="0.4"))
    for lbl, xd in zip(STATUS, STATUS_COLS):   # below the window, clear of the lamps
        e.append(text(fx(xd), fy(STATUS_Y) + 7.0, lbl, 2.3, C_TXT))
    # center-gap row names
    gap_cx = (fx(LEFT_WIN[1]) + fx(STATUS_WIN[0])) / 2
    for name, yc in zip(["NODES", "PAN", "TILT"], ROW_Y):
        e.append(text(gap_cx, fy(yc) + 0.9, name, 2.4, C_ACCENT, weight="bold"))

    # ---- toggles: chunky IMSAI paddle caps, blue (data) / red (command) ----
    def toggle(xd, color, momentary=False):
        cx, cy = fx(xd), TOG_CY
        e.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3.4" fill="#0e0f13" '
                 f'stroke="{C_EDGE}" stroke-width="0.3"/>')          # bushing
        pw, ph = 5.0, 8.5
        e.append(f'<rect x="{cx-pw/2:.2f}" y="{cy-ph+2:.2f}" width="{pw}" '
                 f'height="{ph}" rx="1.6" fill="{color}" '
                 f'stroke="#00000055" stroke-width="0.3"/>')          # blade
        e.append(f'<rect x="{cx-pw/2+0.7:.2f}" y="{cy-ph+2.6:.2f}" width="{pw-2.6:.2f}" '
                 f'height="{ph-3:.2f}" rx="1" fill="#ffffff26"/>')     # highlight
        if momentary:
            e.append(f'<circle cx="{cx:.2f}" cy="{cy+1.6:.2f}" r="0.9" fill="#00000066"/>')

    # group headers
    e.append(text((fx(LEFT_COLS[0])+fx(LEFT_COLS[-1]))/2, TOG_CY-8.5,
                  "— MODE / CONFIG (latching) —", 2.3, C_ACCENT, ls="0.3"))
    e.append(text((fx(STATUS_COLS[0])+fx(STATUS_COLS[-1]))/2, TOG_CY-8.5,
                  "— COMMAND —", 2.3, C_ACCENT, ls="0.3"))
    # data toggles — blue paddles
    for lbl, xd in zip(TOG_DATA, LEFT_COLS):
        on = lbl not in ("–",)
        toggle(xd, C_BLUE if on else "#454b57")
        e.append(text(fx(xd), TOG_CY + 8.6, lbl, 2.3,
                      C_TXT if on else C_MUTE))
    # command momentaries — red paddles
    for lbl, xd in zip(TOG_CMD, STATUS_COLS):
        toggle(xd, C_RED, momentary=True)
        e.append(text(fx(xd), TOG_CY + 8.6, lbl, 2.3,
                      C_TXT, weight="bold" if lbl == "ARM" else "normal"))
    e.append(text(fx(STATUS_COLS[-1]), TOG_CY + 11.8,
                  "soft · hw switch arms", 1.7, C_MUTE))

    # ---- branding band (TOP, ref: IMSPI 8080) — centered in the top band ----
    bc = (FRAME_TOP + (fy(ROW_Y[0]) - 8)) / 2       # vertical center of the top band
    e.append(text(14, bc - 1.5, "PAINTBALL SENTRY", 3.6,
                  C_TXT, anchor="start", weight="bold", ls="0.5"))
    e.append(text(14, bc + 4.0, "GROUND STATION · autonomous marker turret", 2.3,
                  C_MUTE, anchor="start"))
    e.append(text(FACE_W - 14, bc + 0.5, "IMSPI 8080", 6.0, C_ACCENT,
                  anchor="end", weight="bold", ls="0.5"))
    e.append(f'<line x1="{FACE_W-64:.1f}" y1="{bc+2.8:.1f}" x2="{FACE_W-14:.1f}" '
             f'y2="{bc+2.8:.1f}" stroke="{C_ACCENT}" stroke-width="0.6"/>')
    e.append(text(FACE_W - 14, bc + 7.5, "SPX LABS · HMI", 2.6,
                  C_MUTE, anchor="end", ls="0.6"))

    body = "\n  ".join(e)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{FACE_W}mm" height="{FACE_H}mm" '
            f'viewBox="0 0 {FACE_W} {FACE_H}">\n  {body}\n</svg>\n')

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "imspi_panel_front.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build())
    print(f"wrote {out}")
