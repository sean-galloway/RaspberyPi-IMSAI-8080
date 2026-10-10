# IMSAI-8080 front panel → turret HMI mapping

> Provenance: recovered from jetson-marker-turret @ `f57c7c1^`
> (`turret-gimbal/docs/Imsai_Panel_HMI.md`). This repo is the single source of
> truth for the panel — the turret repo references this doc rather than hosting it.

How the **RaspberyPi-IMSAI-8080** smart panel is repurposed as the turret ground
station's status/control head. The panel is the front face of the 3U compute bay
(BOM #61; CAD `hardware/case/rack_case.scad`). PCBs are on order.

## Role & safety boundary (read first)

The panel is a **soft USB peripheral** to the Pi 5 (its RP2040 talks register-mapped
frames over USB CDC — see the sub-project's `docs/protocol.md`). Per the turret
safety posture (`CLAUDE.md`), it is **status + soft-control ONLY**:

- It **mirrors** state (e.g. shows ARMED) but does not create it.
- Its switches may **request** soft actions (mode, page, lamp test, arm-request);
  they are advisory to the Pi state machine.
- The hardware arming switch (#3), E-stop (#54), 48 V cutoff solenoid (#64), and the
  hardware-tied armed/safe LED (#9) stay on their own physical interlock lines and
  **never route through this board**. A dead/hung panel must not affect the firing
  path or the ability to disarm.

## Link

```
Pi 5 (supervisor, USB host) ──USB CDC──► RP2040 (panel) ──► 28 LEDs / 12 switches
```

- Host → panel `0x01` LED update writes all lamps in one frame:
  `ADDR_HI, ADDR_LO, DATA, STATUS, BRIGHT`.
- Panel → host `0x81` switch report on any change + heartbeat.
- No hardware change vs. the stock panel — the `STATUS` bits are firmware-configurable
  and the three 8-bit rows are just relabelled. Only meaning changes.

## Front-panel legend

![IMSAI-8080 turret HMI front panel](assets/imsai_panel_front.svg)

To-scale (254 × 132 mm, 3U) artwork, generated from the same grid as the CAD by
`cad/panel/gen_front_panel.py` → `assets/imsai_panel_front.svg`. Edit meanings in
that script (they mirror the tables below) and re-run. Lamps are drawn red (the
panel uses diffused-red LEDs), so meaning is carried by the labels, not colour.

### How the legend gets onto the fascia — deboss + paint-fill

The legend is **debossed into the fascia** (recessed text/lines), then white paint
is wiped into the grooves — a monolithic panel, no stickers. It is built into the
functional print: `_legend_cuts()` in `rack_shelf.scad` cuts the text using the
**same `ap_x`/`ap_z` as the holes**, so it registers on the grid by construction
(`legend_on`, `deboss_d` = 0.5 mm).

Workflow:
1. Print the fascia black (`PART="shelf"`) — the recessed legend prints with it.
2. Skim white paint (or a paint pen / acrylic) across the surface so it fills the
   recesses; wipe the flat surface clean before it sets (or sand lightly after).
3. Print the blue frame (`PART="frame"`) and fit it over the front.

Notes: strokes get thin below ~2 mm text — the "soft · hw switch arms" note is the
smallest at 1.8 mm; a 0.4 mm nozzle handles it but a 0.2–0.3 mm nozzle is crisper.
Deepen `deboss_d` for a bolder fill. The artwork SVG stays as the full-colour
reference (and a fallback if you ever want a printed overlay instead).

## LED map (28 lamps)

The frame's four bytes carry turret telemetry instead of a CPU bus:

| Frame field | Lamps | IMSAI meaning | Turret meaning |
|-------------|-------|---------------|----------------|
| `STATUS` b0..b3 | 4 status | RUN / WAIT / HLDA / INT | **ARMED · TRACKING · FAULT · PWR-OK** |
| `ADDR_HI` b7..b0 | row 1 (8) | A15..A8 | **Subsystem heartbeat/OK bits** |
| `ADDR_LO` b7..b0 | row 2 (8) | A7..A0 | **Pan angle** (8-seg bargraph) |
| `DATA` b7..b0 | row 3 (8) | D7..D0 | **Tilt angle** (bargraph) / target confidence |

Status lamps (default):

| bit | lamp | source |
|-----|------|--------|
| 0 | ARMED | mirrors the hardware armed rail sense (read-only) |
| 1 | TRACKING | Jetson has a locked target |
| 2 | FAULT | any node fault / heartbeat loss / limit trip |
| 3 | PWR-OK | 48 V + 12 V rails present |

Row 1 subsystem bits (default, one lamp = one node alive/OK):

| bit | node | bit | node |
|-----|------|-----|------|
| 7 | Jetson | 3 | lidar (TF03) |
| 6 | Pi 5 | 2 | net switch / uplink |
| 5 | Pico (turret) | 1 | 48 V rail |
| 4 | ZED 2i | 0 | 12 V rail |

Rows 2/3 render pan/tilt as a lit-up-to-N bargraph over the axis' travel (the
90°/180° sweep limits map cleanly to 8 segments). `BRIGHT` sets global dimming
(dark-room ops). Diffuser film behind the windows gives the "black-glass-until-lit"
look; the sub-project's `docs/panel-layout.md` covers film + IREF.

## Switch map (12 switches)

Reported in the `0x81` frame. All **soft** — advisory to the Pi state machine.

> **Switch hardware (confirmed).** 8 data toggles = **DPDT maintained** (Baomain
> MTS-2xx, e.g. MTS-202 on-on) — they latch, so mode/config holds with no firmware
> trickery. 4 command switches = **SPDT momentary** MTS-123 (ON)-OFF-(ON),
> spring-return. All share the MTS ~6 mm bushing + bat, so the paddle caps and
> bezel holes are identical for all 12. The panel reads them soft via the 74HC165s;
> the spare DPDT pole is free (leave it, or use it for a hard-wired indication).
> Note: a DPDT body is deeper/wider than SPDT — verify it clears its neighbour at
> the 15 mm pitch and doesn't foul the PCB behind the fascia.

8 data toggles (DPDT, maintained) — mode/config:

| # | function | # | function |
|---|----------|---|----------|
| 1 | Mode: PATROL / MANUAL | 5 | Video record on/off |
| 2 | Mode: TRACK enable | 6 | Telemetry verbose |
| 3 | Laser sight on/off | 7 | (spare) |
| 4 | NIGHT — dim (drives low `BRIGHT`) | 8 | (spare) |

4 command momentaries:

| # | function |
|---|----------|
| 1 | **LAMP TEST** (drives panel `0x02`; boot self-test) |
| 2 | **PAGE** — cycle what rows 1–3 show (heartbeat / pan-tilt / target) |
| 3 | **HOME** — request homing routine (Pi → Pico) |
| 4 | **ARM-REQUEST** — soft arm intent; still gated by the hardware arming switch #3 |

> ARM-REQUEST never energises anything. It only tells the Pi "operator wants to
> arm"; firing remains impossible unless the physical #3 switch is closed.

## Implementation

- **Panel firmware** (sub-project): keep the protocol as-is; only the default
  `STATUS` labels and the boot self-test copy change. No new commands needed.
- **Pi host**: a small turret-side task maps state-machine fields → the `0x01`
  frame at the panel refresh rate, and consumes `0x81` switch reports into the
  state machine as soft requests. Reuse the sub-project's `host/imspi` driver.
- **Placement**: Pi 5 sits directly behind the bezel → short USB pigtail to the
  panel's USB-C. Panel's second USB-C (LED rail) can share the bay's 5 V.

## Mechanical (locked after the PCB arrives)

The bezel grid in `rack_shelf.scad` mirrors the sub-project's `panel-layout.md`
(LED rows at datum y=10/22/34; toggles at 15 mm pitch) and `design-spec.md`
(6× M2.5 PCB bosses H1..H6). Re-verify these `[PANEL]` numbers against the real
boards/parts before printing:

- `bezel_th` = 5 mm face; the toggle holes are **back-counterbored** (`tog_cbore_dep`)
  to ~2.5 mm at the thread so the ~6 mm MTS-1xx bushing always protrudes enough to nut.
- `pcb_boss_h` must equal the LED body length minus dome protrusion, so the 3 mm
  domes sit just behind the windows (the one dimension with no fix after fab).
- `toggle_d` = 6.5 mm for the MTS-1xx ~6 mm bushing (verify the bushing thread).
- **Vertical balance** (ref build): `top_brand_band` (=27 mm) drops the whole LED
  board below a top branding band; `toggle_z_ctr` (=30 mm) places the toggle row
  low. The CAD holes and the silkscreen share these numbers, so they stay aligned —
  change them in one place and re-run `gen_front_panel.py`.
- Jetson AGX Orin dev kit = **bottom intake** (confirmed) → the CAD floor vent
  under the pocket feeds it directly; keep the bay below this shelf open so the
  fan has air to pull, and keep the rear clear for exhaust.
- **Tray support:** the Jetson vent is a **ribbed grid** (`vent_slot_w`/`vent_rib`),
  so the module rests on ribs across its whole footprint, not a thin hole-border;
  4 mm floor + underfloor stiffening ribs resist sag.
- **Fascia-to-tray gussets:**
  - **Side gussets — separate bolt-on parts** (`PART="gusset"`). Each **carries the
    PCB's lower corner standoff** (H4 left / H6 right) at the top of its flange — the
    board screws into it **from the back**, reusing the board's own mount hole, so
    there are **no new fascia holes and no screw near the front face**. Below that: a
    **diagonal web** capped under the PCB (z35) and a flat **foot bolted through the
    tray floor** (M3 + nut). Load path: fascia → PCB → gusset → tray. The right flange
    has a notch for the end command switch (the board's right hole sits behind it);
    the left hole clears its switch. `panel_pcb_bosses()` therefore builds only the
    other 4 PCB bosses. **Assembly order:** bolt the gussets to the tray first (they
    provide 2 of the 6 PCB standoffs), then mount the PCB. They replace the old rims.
  - **Centre gusset** stays integral to the tray, in the block gap, with a **cable
    pass-through** for the switch→74HC165 wiring, also capped below the PCB.
- Add a strap/hold-down over the Jetson for transport if you move the rack.
- **Side margins:** the block layout is left-heavy (8 data + 4 command), so
  `content_dx = -3` re-centres the whole content (LEDs + toggles + bosses) to equal
  ~12 mm margins in the aperture. The tray is widened to `usable_width = 214`
  (= aperture) so it backs the full span with ~12 mm each side — confirm against the
  real RackMate T2 interior (still a `[MEASURE]`). The windowed side braces sit at
  the tray edges, clear of the end switches.

## Blue frame (cosmetic front trim)

The signature IMSAI blue frame (ref: the built IMSPI 8080) is a **separate,
visual-only** part in `rack_shelf.scad` — a proud ⊓ border that wraps the sides +
top of the fascia (open at the bottom, over the tray). It is **not structural**:
the black fascia bolts to the rack on its own slots; the frame just overlays the
front, with round reliefs so the 4 rack screws clear it.

- Print it separately in blue: `openscad -D 'PART="frame"'` → its own STL.
- Print the fascia (black) with the default `PART="shelf"`; `PART="all"` +
  `PREVIEW=true` renders the assembled two-colour preview.
- Tunables: `frame_face_w` (lip width), `frame_h` (proud depth), `frame_top`
  (top-bar height, clears the top LED window), `frame_relief` (screw clearance).

## Paddle caps (the IMSAI look & feel)

The 12 toggles get printed paddle caps for the signature IMSAI chunky flat-blade
handle — `cad/scad/imsai_paddle_cap.scad` (parametric; same cap for all 12). Fitted
to the **Baomain MTS-1xx** bat: `bat_d` 2.4 mm bore, `bore_depth` 9 mm (10 mm bat).

- **Colourway** (ref build): print the 8 data paddles **blue**, the 4 command
  paddles **red** — two print runs of the same STL, or a filament swap.
- Chunky wedge: a narrow neck flares into a 12 mm-wide flat blade with a shallow
  thumb dish; clears the 15 mm toggle pitch.
- Prints **collar-down, no supports**; set `MODE="tray"` for a 4×3 sheet of all 12.
- Friction-fit bore with a lead-in chamfer; `grip_slit` or a drop of CA if loose.
- **[VERIFY]**: `bat_d` isn't dimensioned on the datasheet — caliper one bat, print
  a single cap, test the fit, then run the tray.
