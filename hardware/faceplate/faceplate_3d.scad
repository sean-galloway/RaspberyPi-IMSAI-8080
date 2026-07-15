$fn=48; FACE_W=254.0; FACE_H=132.0; TH=4.0; RECESS=0.7; eps=0.05;
STANDOFF=3.5; BOSS_OD=5.5; SCREW_PILOT=2.1; FRONT_WALL=1.0;
mounts=[[33.00,113.00],[156.00,113.00],[221.00,113.00],[33.00,34.00],[156.00,34.00],[221.00,34.00]];
module bosses(){ for(m=mounts) translate([m[0],m[1],-STANDOFF]) cylinder(h=STANDOFF+eps,d=BOSS_OD); }
module screw_blind(){ for(m=mounts) translate([m[0],m[1],-STANDOFF-1]) cylinder(h=STANDOFF+1+TH-FRONT_WALL,d=SCREW_PILOT); }
module rrect(w,h,r){ hull() for(sx=[-1,1],sy=[-1,1]) translate([sx*(w/2-r),sy*(h/2-r)]) circle(r); }
module label(x,y,s,sz,ha,bold){ translate([x,y,TH-RECESS]) linear_extrude(RECESS+eps)
  text(s,size=sz,halign=ha,valign="baseline",font=bold?"DejaVu Sans Mono:style=Bold":"DejaVu Sans Mono"); }
module thru_rrect(x,y,w,h,r){ translate([x,y,-1]) linear_extrude(TH+2) rrect(w,h,r); }
module thru_circ(x,y,d){ translate([x,y,-1]) linear_extrude(TH+2) circle(d/2); }
module frame_recess(){ translate([0,0,TH-RECESS]) linear_extrude(RECESS+eps) union(){
    translate([27,4.0]) square([3.0,112]);            // left bar
    translate([224.0,4.0]) square([3.0,112]);         // right bar
    translate([27,113.0]) square([200,3.0]); } }    // top bar (open bottom)
module cuts(){ union(){
  frame_recess();
  label(39.00,62.00,"JET",2.5,"center",false);
  label(54.00,62.00,"PI5",2.5,"center",false);
  label(69.00,62.00,"PICO",2.5,"center",false);
  label(84.00,62.00,"ZED",2.5,"center",false);
  label(99.00,62.00,"LIDAR",2.5,"center",false);
  label(114.00,62.00,"NET",2.5,"center",false);
  label(129.00,62.00,"48V",2.5,"center",false);
  label(144.00,62.00,"12V",2.5,"center",false);
  label(194.50,50.60,"- STATUS -",2.4,"center",false);
  label(172.00,38.00,"ARMED",2.3,"center",false);
  label(187.00,38.00,"TRACK",2.3,"center",false);
  label(202.00,38.00,"FAULT",2.3,"center",false);
  label(217.00,38.00,"PWR",2.3,"center",false);
  label(158.00,56.10,"NODES",2.4,"center",true);
  label(158.00,44.10,"PAN",2.4,"center",true);
  label(158.00,32.10,"TILT",2.4,"center",true);
  label(91.50,25.50,"- MODE / CONFIG -",2.3,"center",false);
  label(194.50,25.50,"- COMMAND -",2.3,"center",false);
  label(39.00,8.40,"MODE",2.3,"center",false);
  label(54.00,8.40,"TRACK",2.3,"center",false);
  label(69.00,8.40,"LASER",2.3,"center",false);
  label(84.00,8.40,"NIGHT",2.3,"center",false);
  label(99.00,8.40,"REC",2.3,"center",false);
  label(114.00,8.40,"VERB",2.3,"center",false);
  label(129.00,8.40,"-",2.3,"center",false);
  label(144.00,8.40,"-",2.3,"center",false);
  label(172.00,8.40,"TEST",2.3,"center",false);
  label(187.00,8.40,"PAGE",2.3,"center",false);
  label(202.00,8.40,"HOME",2.3,"center",false);
  label(217.00,8.40,"ARM",2.3,"center",true);
  label(194.50,5.20,"soft . hw switch arms",1.7,"center",false);
  label(34.00,100.00,"MARKER SENTRY",5.5,"left",true);
  label(222.00,100.00,"IMSPI 8080",7.0,"right",true);
  label(34.00,89.00,"GROUND STATION . autonomous marker turret",3.0,"left",false);
  label(222.00,89.00,"SPX LABS . HMI",3.0,"right",false);
  // LED windows (through)
  thru_rrect(91.50,57.00,115.00,6.0,1.4);
  thru_rrect(91.50,45.00,115.00,6.0,1.4);
  thru_rrect(91.50,33.00,115.00,6.0,1.4);
  thru_rrect(194.50,45.00,55.00,6.0,1.4);
  // toggle holes + ear slots (through) — mounts are BACK bosses, not here
  thru_circ(39.00,17.00,6.2);
  thru_circ(54.00,17.00,6.2);
  thru_circ(69.00,17.00,6.2);
  thru_circ(84.00,17.00,6.2);
  thru_circ(99.00,17.00,6.2);
  thru_circ(114.00,17.00,6.2);
  thru_circ(129.00,17.00,6.2);
  thru_circ(144.00,17.00,6.2);
  thru_circ(172.00,17.00,6.2);
  thru_circ(187.00,17.00,6.2);
  thru_circ(202.00,17.00,6.2);
  thru_circ(217.00,17.00,6.2);
  thru_rrect(8.00,5.50,9.33,6.77,3.3);
  thru_rrect(8.00,126.50,9.33,6.77,3.3);
  thru_rrect(246.00,5.50,9.33,6.77,3.3);
  thru_rrect(246.00,126.50,9.33,6.77,3.3);
} }
difference(){ union(){ cube([FACE_W,FACE_H,TH]); bosses(); } cuts(); screw_blind(); }
