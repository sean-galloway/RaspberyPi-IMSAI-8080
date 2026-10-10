// =====================================================================
// IMSAI-8080 (IMSPI 8080) rev5 — 10" rack 3U compute-bay case
//   front fascia (bezel) + tray (platform) + bolt-on side gussets
//   + centre gusset + Jetson AGX Orin pocket + Pi 5 / Pico standoffs
//   + cosmetic IMSAI-blue frame trim.
// For the DeskPi RackMate T2 (10" rack). 3D-printable (PETG/ASA recommended).
//
// PROVENANCE: recovered from jetson-marker-turret @ f57c7c1^
//   (turret-gimbal/cad/scad/rack_shelf.scad, the "IMSAI-8080 front panel as
//   the 3U compute bay face" merge) and updated for the rev5 PCB. The turret
//   repo stripped this file 2026-07-14 ("moving to its own repo"); this panel
//   repo is its home now (see TODO.md).
//
// REV5 UPDATE (2026-10-10): every board-facing feature re-derived from the
// measured imspi8080_rev5.kicad_pcb (bbox 204.1 x 112.1, origin top-left):
//   - LED grid:   8 data cols x=14.13+15k, 4 status cols x=147.13+15k (board-rel)
//                 rows y=64.13 / 76.13 / 88.13 (LEDs at the BOTTOM of the board)
//   - toggles:    12 voids, ctrs y=103.06 (8 data w=13.6 h=8.1, 4 cmd h=13.1)
//   - PCB holes:  (8.1/131.1/196.1) x (8.1/87.1)  -> all 6 bosses on the bezel
//   - vertical:   board top edge 0.6 mm below the face top (proven layout from
//                 hardware/faceplate/gen_faceplate_3d.py); board bottom z~19.3
//                 leaves ~15 mm under it for the gusset webs (was ~34 mm).
// Tray / Jetson pocket / Pi 5 / Pico / blue frame are board-independent and
// unchanged from the printed rev2-era case.
//
// SAFETY (per turret CLAUDE.md): this panel is a SOFT USB peripheral to the Pi.
// It is STATUS + soft-control ONLY. The hardware arming switch, E-stop, and the
// armed/safe LED stay on their own physical interlock lines and NEVER route
// through this board. Panel switches may *request* actions; they never fire.
//
// Render/export: open in OpenSCAD, F6, then export STL. CLI:
//   openscad -o case.stl  -D 'PART="case"'  rack_case.scad
//   openscad -o gusset.stl -D 'PART="gusset"' rack_case.scad   (print x2)
//   openscad -o frame.stl -D 'PART="frame"' rack_case.scad     (IMSAI blue)
// =====================================================================

// ---- Rack interface (10" 1U panel) — from the mfr mechanical drawing ----------
U              = 44;      // 1U panel height (drawing: 44 mm / 1.73 in)
shelf_U        = 3;       // case front-panel height in U
face_width     = 254;     // 10" panel outer width (drawing)
// (front-face thickness is bezel_th, set in the IMSAI bezel block below)
// Mounting: 4 horizontal OVAL slots 9.33w x 6.77h. Drawing gives hole center-to-
// center: 238 mm horizontal, 33 mm vertical (within 1U) -> slot centers 8 mm from
// each side edge, 5.5 mm from top/bottom edge. (Clear panel opening ~214 mm.)
slot_w         = 9.33;    // oval slot width (horizontal = side-to-side adjustment)
slot_h         = 6.77;    // oval slot height
rail_hole_dx   = 238;     // horizontal mounting-hole center-to-center (drawing)
hole_cc_v      = 33;      // vertical mounting-hole C-C within 1U (drawing)
slot_side_ctr  = (face_width - rail_hole_dx) / 2;   // = 8 mm from each side edge
slot_tb_ctr    = (U - hole_cc_v) / 2;               // = 5.5 mm from top/bottom edge

// ---- Tray (platform) --------------------------------------------------
usable_width   = 214;     // clear width between rails — set to the RackMate T2
                          // interior; 214 (= panel aperture) backs the full
                          // switch/LED span. Confirmed: rev5 board is 204.1 wide,
                          // so it drops in with ~5 mm/side at content_dx=-3.
shelf_depth    = 200;     // tray depth (T2 interior ~260; leave room for cables)
floor_th       = 4;       // tray floor thickness (4 mm for the heavy Jetson)
side_wall_h    = 8;       // low stiffening rim along tray sides
rear_lip_h     = 10;      // rear retaining lip
vent_slot_w    = 9;       // Jetson intake-vent slot width (ribs between = support)
vent_rib       = 4;       // rib between vent slots — this is what carries the Jetson
floor_rib_h    = 7;       // underfloor stiffening-rib depth
// Integral CENTRE gusset (in the LED-block gap). Side gussets are separate
// bolt-on parts (see the bolt-on section below). All braces stay BELOW the PCB
// (rev5 board bottom edge z~19.3 -> brace tops z<=16).
gusset_t       = 4;       // centre-brace thickness
gusset_d       = 55;      // how far it reaches back along the tray
gusset_h_ctr   = 12.5;    // centre-brace height: top z~15.5, clears the board bottom
cable_slot_w   = 12;      // centre-gusset cable pass-through (y) for switch/board wiring
cable_slot_h   = 6;       // ... (z), slot spans z 7..13 inside the brace

// ---- Bolt-on SIDE gusset (separate part) ---------------------------------------
// Reuses the PCB's LOWER corner mount hole (H4 left / H6 right): the gusset CARRIES
// that standoff and the board screws into it FROM THE BACK — no new fascia hole, no
// screw near the front. Also bolted to the tray floor. Path: fascia->PCB->gusset->tray.
bg_web_t       = 4;       // web thickness (x)
bg_web_depth   = 50;      // web reach back along the tray (y)
bg_web_top     = 16;      // web top z (below the rev5 PCB bottom edge z~19.3)
bg_flange_t    = 2.5;     // flange plate thickness (sits in front of the board)
bg_foot_t      = 3;       // foot thickness (flat; bolts through the floor)
bg_foot_w      = 12;      // foot width (x)
bg_foot_d      = 16;      // foot depth (y)
bg_bolt_d      = 3.4;     // M3 clearance (floor bolts, nut underneath)
bg_bolt_l      = [[5, 6], [9, 12]];                   // LEFT floor-bolt positions (world x,y)
bg_bolt_r      = [[usable_width-5, 6], [usable_width-9, 12]];  // RIGHT

// ---- Jetson AGX Orin dev kit (drop-in pocket) ----------------------
jetson_xy      = 109;     // footprint (given)
jetson_h       = 75;      // height incl. feet (72 mm bare). tray floor + this
                          // = ~78 mm = ~1.75U -> shelf_U=3 leaves fan headroom.
jetson_clear   = 1.0;     // pocket clearance per side
jetson_wall    = 10;      // locating wall height (grips the base for transport)
jetson_vent    = 90;      // floor cutout (square) under the fan intake.
                          // FAN = BOTTOM INTAKE: this vent feeds it (feet give the
                          // ~3 mm gap). Keep the rack bay BELOW the shelf open so
                          // the fan has air to pull.

// ---- Raspberry Pi 5 (standoffs) ------------------------------------
pi5_hole_dx    = 58;      // hole rectangle X
pi5_hole_dy    = 49;      // hole rectangle Y
pi5_standoff_h = 5;
pi5_standoff_d = 6;
pi5_screw_d    = 2.6;     // M2.5 clearance

// ---- Pico ----------------------------------------------------------
pico_standoff_h = 4;
pico_dx        = 47;      // Pico mount-hole spacing X (board is 51x21)
pico_dy        = 11.4;    // Pico mount-hole spacing Y
pico_screw_d   = 2.2;     // M2 clearance

// ---- IMSAI-8080 bezel (front face) — mirror of the rev5 panel PCB ------
// Datum for board features = BOARD-RELATIVE coords (origin top-left of the
// 204.1 x 112.1 PCB, +x right, +y DOWN — measured from imspi8080_rev5.kicad_pcb).
// map_x/map_z convert board-rel (x,y) into this file's flange coords (origin at
// flange bottom-left, z up). The bezel face is 254 x 132 overall; the rack's
// clear aperture (214 x 122) is centred, but the rev5 content follows the board,
// not the aperture: the board top edge sits 0.6 mm below the face top and the
// masthead legend recesses over the board's top dead zone (same proven layout
// as hardware/faceplate/gen_faceplate_3d.py).
bezel_th       = 5;       // face thickness (rigid, backs the LED windows). The
                          // toggle holes are back-counterbored (below) so the
                          // ~6 mm MTS-1xx bushing still protrudes far enough to nut.
aperture_w     = 214;     // clear aperture width (10" rack spec)
content_dx     = -3;      // shift the whole content (LEDs+toggles+bosses) left —
                          // same convention as the printed rev2-era case.

// LED windows: one diffuser-backed slot per lamp row. {x0, x1, y_center} in
// board-rel coords (measured: LED cols 14.13+15k / 147.13+15k, rows 64.13/76.13/88.13).
led_win_h      = 6;       // slot height; ~6 mm bezel rib between rows
led_windows    = [ [10.5, 123, 64.13],   // row 1 — addr-hi  -> subsystem heartbeat bits
                   [10.5, 123, 76.13],   // row 2 — addr-lo  -> pan bargraph
                   [10.5, 123, 88.13],   // row 3 — data     -> tilt / confidence
                   [143.5, 196.5, 76.13] ]; // status (4)    -> ARMED/TRACKING/FAULT/PWR

// Toggle cutouts: 8 data (left block) + 4 command (status block), 15 mm pitch.
// Centers = the 13.6 mm-wide board voids measured in Edge.Cuts (y=103.06); the
// switch bodies pass through bezel hole + board void, terminals solder to the
// SWD/SWC pads 10 mm above. [PANEL] set toggle_d to the bushing dia of the
// toggles you buy.
toggle_d       = 6.5;     // MTS bushing ~6 mm (1/4-40) -> 6.5 hole (same for both)
toggle_ry      = 103.06;  // board-rel y of the void row center
toggle_x_data  = [14.06, 29.06, 44.06, 59.06, 74.06, 89.06, 104.06, 119.06];
toggle_x_cmd   = [147.06, 162.06, 177.06, 192.06];
tog_cbore_d    = 9;       // back-side counterbore dia (clears the switch shoulder)
tog_cbore_dep  = 2.5;     // leaves bezel_th - this = 2.5 mm at the thread so the nut
                          // catches on a ~6 mm bushing regardless of its exact length

// Panel-PCB standoff bosses (all 6, measured H1..H6 on rev5), 5 mm off the bezel back.
pcb_boss_h     = 5;
pcb_boss_d     = 6;
pcb_screw_d    = 2.6;     // M2.5 clearance
pcb_holes      = [ [8.1, 8.1], [131.1, 8.1], [196.1, 8.1],
                   [8.1, 87.1], [131.1, 87.1], [196.1, 87.1] ]; // board-rel

// ---- IMSAI blue frame — COSMETIC front-fascia trim (visual only) -----
// A SEPARATE slip-/glue-on ⊓ border printed in IMSAI blue (ref: the built
// IMSPI 8080). Proud side bands + a top bar wrap the sides + top (open at the
// bottom where the tray is). NOT structural: the black fascia mounts to the rack
// on its own slots; the frame just overlays the front. 4 round reliefs let the
// mount screws/driver clear it. Print it separately, or as a 2nd colour on the
// same object (PART="all").
frame_face_w   = 6;       // how far the blue lip covers the front fascia (from edge)
frame_h        = 4;       // how far the frame stands proud of the fascia
frame_top      = 11;      // top-bar height — clears everything (top LED row z~70)
frame_relief   = 5;       // extra dia of clearance around each mount slot in the frame
PREVIEW        = false;   // true = colour the parts for the F5/preview image

PART           = "case";  // "case" (functional print) | "frame" (blue) | "gusset" | "all"
panel_h        = shelf_U * U;         // 3U face height, shared by fascia + frame
board_top_z    = panel_h - 0.6;       // rev5 board top edge, 0.6 below the face top
toggle_z_ctr   = board_top_z - toggle_ry;  // toggle-row centre in flange z (~28.3)

// ---- Debossed legend (recess + wipe paint into the grooves) -----------
// Cut into the fascia FRONT using the same board-rel mapping as the holes, so
// text lands on the grid by construction. Mirrors hardware/faceplate/
// gen_faceplate_3d.py (its layout has a verified faceplate_preview.png).
legend_on      = true;
deboss_d       = 0.5;     // legend recess depth (0.4-0.6 typical for paint-fill)
lf             = "DejaVu Sans Mono";
lf_b           = "DejaVu Sans Mono:style=Bold";
node_lbl   = ["JET", "PI5", "PICO", "ZED", "LIDAR", "NET", "48V", "12V"];
status_lbl = ["ARMED", "TRACK", "FAULT", "PWR"];
data_lbl   = ["MODE", "TRACK", "LASER", "NIGHT", "REC", "VERB", "-", "-"];
cmd_lbl    = ["TEST", "PAGE", "HOME", "ARM"];

eps = 0.01;
$fn = 32;

// ---------------------------------------------------------------------
// board-rel x -> flange-local x (the bezel face is offset (usable_width-
// face_width)/2 = -20 when placed on the tray, so world x = board-rel x - 3)
function ap_x(x)  = (face_width - aperture_w)/2 + content_dx + x;
// board-rel y (DOWN) -> flange-local z (UP); board top edge at board_top_z
function bd_z(ry) = board_top_z - ry;

module standoff(h, od, id) {
    difference() {
        cylinder(h=h, d=od);
        translate([0,0,-eps]) cylinder(h=h+2*eps, d=id);
    }
}

// Ribbed intake vent: slots along depth with ribs between, so a device rests on a
// continuous support grid (weight on the ribs) instead of a single open hole.
module ribbed_vent(w, d, x0, y0) {
    pitch = vent_slot_w + vent_rib;
    for (sx = [x0 : pitch : x0 + w - vent_slot_w])
        translate([sx, y0, -eps])
            cube([vent_slot_w, d, floor_th + 2*eps]);
}

module tray() {
    // Jetson vent footprint (centred under the pocket, at the rear)
    jvx = 6 + (jetson_xy - jetson_vent)/2;
    jvy = shelf_depth - 10 - jetson_xy + (jetson_xy - jetson_vent)/2;
    difference() {
        union() {
            cube([usable_width, shelf_depth, floor_th]);                          // floor
            cube([usable_width, 3, side_wall_h]);                                 // front rim
            translate([0, shelf_depth-3, 0]) cube([usable_width, 3, rear_lip_h]); // rear lip
            // (side rims dropped — the bolt-on side gussets stiffen the edges instead)
            // underfloor stiffening ribs so the 4 mm floor can't sag under load:
            for (ry = [8, jvy - 8])                       // front + just ahead of the vent
                translate([3, ry, -floor_rib_h]) cube([usable_width-6, 4, floor_rib_h+eps]);
            translate([usable_width/2-2, 3, -floor_rib_h])// centre spine (front to vent)
                cube([4, jvy-6, floor_rib_h+eps]);
            translate([usable_width-40, jvy-8, -floor_rib_h])  // rib under the Pi 5 zone
                cube([4, shelf_depth-3-(jvy-8), floor_rib_h+eps]);
        }
        ribbed_vent(jetson_vent, jetson_vent, jvx, jvy);   // Jetson bottom intake (supported)
        for (cx = [30 : 40 : usable_width-30])             // rear cable slots
            translate([cx, shelf_depth-3-eps, rear_lip_h-6])
                cube([18, 4+2*eps, 8]);
        // through-holes for the bolt-on side-gusset feet (M3, nut under the tray)
        for (b = concat(bg_bolt_l, bg_bolt_r))
            translate([b[0], b[1], -eps]) cylinder(h = floor_th + 2*eps, d = bg_bolt_d);
    }
}

// Jetson locating pocket (open-bottom walls) — back-left of tray
module jetson_pocket() {
    jx = 6;                              // left inset
    jy = shelf_depth - 10 - jetson_xy;   // toward rear
    pkt = jetson_xy + 2*jetson_clear;
    translate([jx, jy, floor_th-eps])
    difference() {
        cube([pkt, pkt, jetson_wall]);
        translate([2, 2, -eps]) cube([pkt-4, pkt-4, jetson_wall+2*eps]);
        // open front edge for cabling/insertion
        translate([pkt/2-20, -eps, -eps]) cube([40, 4, jetson_wall+2*eps]);
    }
}

// Pi 5 standoffs — right side of tray
module pi5_mounts() {
    px = usable_width - 6 - 56;   // 56mm board width region (right side)
    py = shelf_depth - 10 - 85;   // 85mm board length region (rear)
    // four holes on 58 x 49 rectangle (origin at first standoff)
    for (dx = [0, pi5_hole_dx])
        for (dy = [0, pi5_hole_dy])
            translate([px+dx - (pi5_hole_dx-49)/2, py+dy, floor_th-eps])
                standoff(pi5_standoff_h, pi5_standoff_d, pi5_screw_d);
}

// Pico standoffs — front-center
module pico_mounts() {
    cx = usable_width/2 - pico_dx/2;
    cy = 16;
    for (dx = [0, pico_dx])
        for (dy = [0, pico_dy])
            translate([cx+dx, cy+dy, floor_th-eps])
                standoff(pico_standoff_h, 4, pico_screw_d);
}

// One horizontal oval mounting slot (9.33w x 6.77h), cut through the fascia (Y).
module oval_slot() {
    off = (slot_w - slot_h) / 2;   // circle-center offset for a horizontal oval
    hull()
        for (dx = [-off, off])
            translate([dx, -eps, 0]) rotate([-90, 0, 0])
                cylinder(h = bezel_th + 2*eps, d = slot_h);
}

// through-face features (LED windows + toggle holes/counterbores)
module _face_cuts() {
    for (w = led_windows)
        translate([ap_x(w[0]), -eps, bd_z(w[2]) - led_win_h/2])
            cube([ap_x(w[1]) - ap_x(w[0]), bezel_th + 2*eps, led_win_h]);
    for (xd = concat(toggle_x_data, toggle_x_cmd)) {
        translate([ap_x(xd), -eps, toggle_z_ctr])
            rotate([-90, 0, 0]) cylinder(h = bezel_th + 2*eps, d = toggle_d);
        translate([ap_x(xd), bezel_th - tog_cbore_dep, toggle_z_ctr])
            rotate([-90, 0, 0]) cylinder(h = tog_cbore_dep + eps, d = tog_cbore_d);
    }
}

// the 4 rack-mount oval slots (RackMate pattern) — through the fascia
module _slot_cuts() {
    for (sx = [slot_side_ctr, face_width - slot_side_ctr])
        for (sz = [slot_tb_ctr, panel_h - slot_tb_ctr])
            translate([sx, 0, sz]) oval_slot();
}

// one debossed label on the fascia front (front face = local y=0; cuts into +y)
module _dbt(x, z, s, sz, ha="center", bold=false) {
    if (s != "")
        translate([x, deboss_d, z]) rotate([90, 0, 0])
            linear_extrude(deboss_d + eps)
                text(s, size=sz, halign=ha, valign="baseline",
                     font = bold ? lf_b : lf, $fn=20);
}

// full debossed legend (paint-fill), positioned on the same grid as the holes.
// x = flange-local (via ap_x), z per the rev5 vertical layout.
module _legend_cuts() {
    // node bit labels (above the row-1 window; window top edge z~70.3)
    for (i = [0:len(node_lbl)-1])
        _dbt(ap_x(14.13 + 15*i), 72.4, node_lbl[i], 2.5);
    // centre-gap row names (between the data + status windows, gap ctr rel 133.25)
    for (i = [0:2])
        _dbt(ap_x(133.25), 66.5 - 12*i, ["NODES","PAN","TILT"][i], 2.4, "center", true);
    // status block
    _dbt(ap_x(169.63), 61.0, "- STATUS -", 2.4);
    for (i = [0:len(status_lbl)-1])
        _dbt(ap_x(147.13 + 15*i), 48.4, status_lbl[i], 2.3);
    // toggle bands (toggle row ctr z~28.3; headers above, per-switch labels below)
    _dbt(ap_x(66.59), 36.9, "- MODE / CONFIG (latching) -", 2.3);
    _dbt(ap_x(169.63), 36.9, "- COMMAND -", 2.3);
    for (i = [0:len(data_lbl)-1])
        _dbt(ap_x(14.13 + 15*i), 19.8, data_lbl[i], 2.3);
    for (i = [0:len(cmd_lbl)-1])
        _dbt(ap_x(147.13 + 15*i), 19.8, cmd_lbl[i], 2.3, "center", cmd_lbl[i] == "ARM");
    _dbt(ap_x(192.13), 16.6, "soft . hw switch arms", 1.7);
    // masthead over the board's top dead zone (electronics behind it)
    _dbt(23,  100, "MARKER SENTRY", 5.5, "left", true);
    _dbt(211, 100, "IMSPI 8080", 7.0, "right", true);
    _dbt(23,  89,  "GROUND STATION . autonomous marker turret", 3.0, "left");
    _dbt(211, 89,  "Gib Systems . HMI", 3.0, "right");
}

// Front rack fascia = the IMSAI-8080 bezel (black). Functional; frame is separate.
module imsai_face() {
    translate([(usable_width-face_width)/2, -bezel_th, 0])
    difference() {
        cube([face_width, bezel_th, panel_h]);
        _face_cuts(); _slot_cuts();
        if (legend_on) _legend_cuts();
    }
}

// Cosmetic blue ⊓ trim that overlays the front fascia (VISUAL ONLY, prints
// separately in blue). Side bands + a top bar wrap the sides + top and stand
// proud; round reliefs at the 4 mount slots keep the screws/driver clear.
module blue_frame() {
    translate([(usable_width-face_width)/2, -bezel_th, 0])
    difference() {
        union() {
            translate([0, -frame_h, 0]) cube([frame_face_w, frame_h, panel_h]);       // left
            translate([face_width-frame_face_w, -frame_h, 0])
                cube([frame_face_w, frame_h, panel_h]);                               // right
            translate([frame_face_w, -frame_h, panel_h-frame_top])
                cube([face_width-2*frame_face_w, frame_h, frame_top]);                // top
        }
        for (sx = [slot_side_ctr, face_width - slot_side_ctr])       // screw reliefs
            for (sz = [slot_tb_ctr, panel_h - slot_tb_ctr])
                translate([sx, -frame_h - eps, sz]) rotate([-90, 0, 0])
                    cylinder(h = frame_h + 2*eps, d = slot_w + frame_relief);
    }
}

// 6 bosses on the BACK of the bezel that stand the panel PCB off the face
// (heat-set M2.5 inserts, or self-tapping). Height must match the LED body length
// so the 3 mm domes sit just behind the windows — see design-spec.
module panel_pcb_bosses() {
    fx = (usable_width - face_width) / 2;
    for (h = pcb_holes)
        // H4 (8.1,87.1) and H6 (196.1,87.1) are carried by the bolt-on side
        // gussets instead (their standoffs are part of the gusset part)
        if (!(abs(h[1] - 87.1) < 0.2 && (abs(h[0] - 8.1) < 0.2 || abs(h[0] - 196.1) < 0.2)))
            translate([fx + ap_x(h[0]), 0, bd_z(h[1])])
                rotate([-90, 0, 0])      // grow into the bay from the bezel back (y=0)
                    standoff(pcb_boss_h, pcb_boss_d, pcb_screw_d);
}

// Triangular brace tying the fascia (y≈0) to the tray floor. Right triangle in the
// Y-Z plane, extruded gusset_t in X; overlaps both so it fuses into one print.
module gusset(x0, h) {
    translate([x0, -1, floor_th - 1])
        rotate([90, 0, 90])
            linear_extrude(gusset_t)
                polygon([[0, 0], [gusset_d, 0], [0, h]]);
}

// BOLT-ON side gusset (SEPARATE part, one per side). Built per-side because the
// rev5 corner-hole surroundings are asymmetric. Each = flange plate on the fascia
// back that carries the PCB corner standoff (board screws into it from behind) +
// a diagonal web below the PCB + a flat foot bolted through the tray floor.
//
//   ex   = tray edge x (0 left, usable_width right)
//   sgn  = +1 left / -1 right (body extends inward)
//   bx   = board-corner-hole world x (gusset carries this standoff)
//   bolts= floor-bolt positions
//   notch= [z0, h] switch-body clearance notch in the flange, or [] for none
module bolt_gusset_side(ex, sgn, bx, bolts, notch) {
    bz  = bd_z(87.1);                        // corner-hole height (H4/H6) z~44.3
    fw  = abs(bx - ex) - 0.4;                // flange ends 0.4 mm shy of the boss
    fx0 = min(ex, ex + sgn*fw);              // flange x-start
    difference() {
        union() {
            // web (diagonal, tall at the fascia, tapering back); shape same both sides
            translate([min(ex, ex + sgn*bg_web_t), -1, floor_th - 1])
                rotate([90, 0, 90]) linear_extrude(bg_web_t)
                    polygon([[0,0], [bg_web_depth,0], [0, bg_web_top - (floor_th-1)]]);
            // flange plate on the fascia back (in front of the board), edge -> boss
            translate([fx0, 0, floor_th]) cube([fw, bg_flange_t, (bz + 5) - floor_th]);
            // PCB corner standoff the board screws into from the back
            translate([bx, 0, bz]) rotate([-90, 0, 0])
                standoff(pcb_boss_h, pcb_boss_d, pcb_screw_d);
            // flat foot bolted to the floor
            translate([min(ex, ex + sgn*bg_foot_w), 0, floor_th])
                cube([bg_foot_w, bg_foot_d, bg_foot_t]);
        }
        // switch-body clearance notch (spans the whole flange in x)
        if (len(notch) > 0) {
            n0 = min(fx0, ex + sgn*5);
            n1 = max(fx0, ex + sgn*5);
            translate([n0, -1, notch[0]]) cube([n1 - n0, bg_flange_t + 2, notch[1]]);
        }
        // floor bolt clearances
        for (b = bolts)
            translate([b[0], b[1], floor_th - eps]) cylinder(h = bg_foot_t + 2*eps, d = bg_bolt_d);
    }
}
module bolt_gusset() {
    lbx = ap_x(8.1)   + (usable_width - face_width)/2;   // H4 world x (left,  ≈ 5.1)
    rbx = ap_x(196.1) + (usable_width - face_width)/2;   // H6 world x (right, ≈ 193.1)
    bolt_gusset_side(0,            +1, lbx, bg_bolt_l, []);          // left: clear of SWD1 body
    bolt_gusset_side(usable_width, -1, rbx, bg_bolt_r, [15, 20]);    // right: notch clears SWC3/4 bodies
}

// CENTRE gusset (under the PCB, in the LED-block gap) with a cable pass-through so the
// switch wiring can cross it. Internal window keeps it one connected piece.
module centre_gusset(x0) {
    difference() {
        gusset(x0, gusset_h_ctr);
        translate([x0 - 1, 2, floor_th + 3])
            cube([gusset_t + 2, cable_slot_w, cable_slot_h]);
    }
}

module rack_case() {           // functional print (black PETG/ASA)
    tray();
    jetson_pocket();
    pi5_mounts();
    pico_mounts();        // OPTIONAL: panel RP2040 is on the IMSAI PCB; motion Pico
                          // lives on the turret. Keep only for a spare/bench Pico.
    imsai_face();
    panel_pcb_bosses();
    // integral centre gusset in the true LED-block gap (rel ctr 133.25); side gussets bolt on
    centre_gusset(ap_x(133.25) + (usable_width - face_width)/2 - gusset_t/2);
}

// PART selector — each printable part on its own:
//   "case" (tray+fascia, black)  "frame" (blue trim)  "gusset" (2 side gussets)  "all"
if (PART == "frame")       blue_frame();
else if (PART == "gusset") bolt_gusset();
else if (PART == "all") {
    if (PREVIEW) { color("Gainsboro") rack_case(); color("DodgerBlue") blue_frame();
                   color("Tomato") bolt_gusset(); }
    else         { rack_case(); blue_frame(); bolt_gusset(); }
}
else {
    if (PREVIEW) color("Gainsboro") rack_case();
    else         rack_case();
}
