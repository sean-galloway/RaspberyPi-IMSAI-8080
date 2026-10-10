// =====================================================================
// IMSAI-8080 paddle caps — slip over the mini-toggle bat handles to give the
// panel its signature wide flat paddle look & feel.
// For the 12 switches on the IMSAI-faced compute bay (hardware/case/rack_case.scad):
//   8 data toggles (latching) + 4 command toggles (momentary) — same cap.
// 3D-printable in PETG/ASA/PLA; prints collar-DOWN with NO supports.
//
// PROVENANCE: recovered from jetson-marker-turret @ f57c7c1^
//   (turret-gimbal/cad/scad/imsai_paddle_cap.scad) — this panel repo is the
//   single source of truth for all panel/case CAD now.
//
// >>> [MEASURE] bat_d + bore_depth against the ACTUAL toggles you buy. The bore
//     is a friction fit; print one, test on a spare bat, then run the tray.
//     Too tight -> bump bat_d +0.1; too loose -> enable grip_slit or a drop of CA. <<<
// Render a single cap: F5.  Print sheet: set MODE="tray", F6, export STL.
// =====================================================================

// ---- Fit to the toggle bat handle (Baomain MTS-123 / MTS-1xx family) --
bat_d        = 2.4;   // bat-handle dia (bore). MTS-1xx bat ~2.3 mm; [VERIFY w/ caliper,
                      //   not dimensioned on the datasheet]. Print holes run ~0.1-0.2
                      //   undersize -> 2.4 gives a snug slip fit; bump +0.1 if too tight.
bore_depth   = 9;     // exposed bat is 10 mm (datasheet) -> 9 mm leaves the paddle ~1 mm
                      //   off the bushing/nut so it can't rub
bore_chamfer = 0.8;   // lead-in chamfer at the bore mouth (eases start)
grip_slit    = false; // true = one side slit so the collar flexes onto a round bat

// ---- Paddle form (the IMSAI look — chunky flat wedge, ref: IMSPI 8080) ----
paddle_h     = 17;    // total cap height above the panel
paddle_w     = 12;    // side-to-side (the face you flick) — keep < 15 mm pitch
paddle_t     = 5.2;   // front-to-back thickness (chunky flat blade)
top_r        = 1.3;   // top corner rounding (small = squarer, more slab-like)
collar_d     = 6.0;   // base collar dia (sits just proud of the bezel)
collar_h     = 3.5;   // straight neck before the blade flares out
flare_z      = 0.42;  // fraction of height where the blade reaches full width
dish         = true;  // shallow concave thumb scoop on the front face
dish_r       = 30;    // scoop cylinder radius (bigger = shallower)

// ---- Print tray -----------------------------------------------------
MODE         = "single";   // "single" | "tray"
tray_cols    = 4;
tray_rows    = 3;          // 4 x 3 = 12 caps
tray_pitch_x = paddle_w + 6;
tray_pitch_y = paddle_t + 8;

eps = 0.01;
$fn = 64;

// rounded-rectangle cross-section (4 corner spheres) at height z
module _corners(z) {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx*(paddle_w/2 - top_r), sy*(paddle_t/2 - top_r), z])
            sphere(r = top_r);
}

module paddle_solid() {
    fz = paddle_h * flare_z;                       // where the blade reaches full width
    hull() { cylinder(d = collar_d, h = collar_h); _corners(fz); }   // neck flares out
    hull() { _corners(fz); _corners(paddle_h - top_r); }             // straight flat blade
}

module paddle_cap() {
    difference() {
        paddle_solid();
        // bore for the bat handle
        translate([0, 0, -eps]) cylinder(d = bat_d, h = bore_depth + eps);
        // bore-mouth chamfer
        translate([0, 0, -eps])
            cylinder(d1 = bat_d + 2*bore_chamfer, d2 = bat_d, h = bore_chamfer + eps);
        // concave thumb scoop on the front (+Y) face
        if (dish)
            translate([0, paddle_t/2 + dish_r - 1.1, paddle_h*0.62])
                rotate([0, 90, 0])
                    cylinder(r = dish_r, h = paddle_w + 4, center = true);
        // optional compliance slit (helps grip a smooth round bat)
        if (grip_slit)
            translate([-0.3, -paddle_t/2 - eps, -eps])
                cube([0.6, paddle_t + 2*eps, bore_depth]);
    }
}

module tray() {
    for (r = [0 : tray_rows-1])
        for (c = [0 : tray_cols-1])
            translate([c*tray_pitch_x, r*tray_pitch_y, 0])
                paddle_cap();
}

if (MODE == "tray") tray();
else                paddle_cap();
