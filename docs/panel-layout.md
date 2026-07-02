# Panel layout

See `panel-layout.svg` for the drawing. This documents the dimensions behind it.

## Width budget

A 10" rack aperture gives roughly **220 mm** of usable panel width. The binding
constraint is toggle finger-clearance, not the electronics — the LEDs are trivial.

## Blocks

Left block (8 columns):

| Row | Lamps                | Element     |
|-----|----------------------|-------------|
| 1   | 8 — address high A15..A8 | 3 mm LED |
| 2   | 8 — address low  A7..A0  | 3 mm LED |
| 3   | 8 — data          D7..D0 | 3 mm LED |
| —   | 8 — data toggles         | latching toggle |

Right block (4 columns):

| Row | Lamps            | Element |
|-----|------------------|---------|
| 1   | 4 — status       | 3 mm LED |
| —   | 4 — command      | momentary toggle |

## Pitch math (fits 220 mm)

Columns must align vertically (LEDs sit above toggles), so toggle pitch governs
each block's column spacing.

- toggle pitch: ~15 mm center-to-center (fits 8 + 4 toggles in the 10" width;
  MTS mini-toggle bodies clear at this pitch)
- left block, 8 columns: 7 x 15 mm = **105 mm** span
- right block, 4 columns: 3 x 15 mm = **45 mm** span
- remaining for center gap + two side margins: 220 - 105 - 45 = **70 mm**

Comfortable fit. LED rows use ~8 mm vertical pitch; three rows plus a toggle row
makes this a ~2U face in a 10" rack (not 1U).

## Mechanical: the standoff stack

The one dimension to get right before fabbing the PCB:

```
printed bezel  ─┐
                │  toggle bushing length  +  panel thickness
PCB (toggles) ──┘  must equal the PCB-to-bezel standoff height
```

Board-mounted toggles solder to the PCB; their threaded bushings pass through the
bezel. If the standoff height doesn't match the bushing length (minus bezel
thickness), the bushings either don't reach the front face or protrude too far.
LED body length sets the same constraint for the LED domes. Measure the exact
bushing length and paddle-cap depth of the toggles you buy, then set the standoff
height and bezel thickness to suit — there is no fixing this after fab.

## Bezel windows + diffuser film

Rather than 28 individual holes, cut one horizontal window slot per LED row and
back it with smoked/diffuser film — the lamps read as glowing dots and the film
hides the PCB, unlit LEDs, and traces when off ("black glass until lit").

Slot centers align with the LED rows, so they inherit the 15 mm grid. Coordinates
in mm on the shared datum (LED rows at y = 10 / 22 / 34; left block x = 15..120,
status block x = 160..205):

| Window        | X span      | Y center | Size (W × H)   |
|---------------|-------------|----------|----------------|
| Row 1 addr hi | 10 – 125    | 10       | ~115 × 6 mm    |
| Row 2 addr lo | 10 – 125    | 22       | ~115 × 6 mm    |
| Row 3 data    | 10 – 125    | 34       | ~115 × 6 mm    |
| Status        | 155 – 210   | 22       | ~55 × 6 mm     |

- 6 mm slot height leaves ~6 mm of bezel between rows (12 mm row pitch) — enough
  material to stay rigid on a printed face.
- Film: dark-tinted diffusing acrylic/polycarbonate or LED diffusion sheet,
  0.5–1 mm, cut ~5 mm oversize per window and bonded to the **back** of the bezel.
- Tint eats brightness — plan to lower the TLC5947 IREF resistor a little to push
  more per-LED current (free on the dedicated LED rail). Swatch-test tint darkness
  against a lit LED before committing: too dark = weak lamps, too light = board
  shows when off.
- Alternative: one big 115 × 30 mm window over all three left-block rows backed by
  film — simplest cut, but less rigid and loses the segmented IMSAI slot look.
