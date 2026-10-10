$fn=48; FACE_W=254.0; FACE_H=132.0; TH=4.0; RECESS=0.7; eps=0.05;
STANDOFF=3.5; BOSS_OD=5.5; SCREW_PILOT=2.1; FRONT_WALL=1.0;
mounts=[[33.00,123.40],[156.00,123.40],[221.00,123.40],[33.00,44.40],[156.00,44.40],[221.00,44.40]];
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
  label(39.00,72.40,"JET",2.5,"center",false);
  label(54.00,72.40,"PI5",2.5,"center",false);
  label(69.00,72.40,"PICO",2.5,"center",false);
  label(84.00,72.40,"ZED",2.5,"center",false);
  label(99.00,72.40,"LIDAR",2.5,"center",false);
  label(114.00,72.40,"NET",2.5,"center",false);
  label(129.00,72.40,"48V",2.5,"center",false);
  label(144.00,72.40,"12V",2.5,"center",false);
  label(194.50,61.00,"- STATUS -",2.4,"center",false);
  label(172.00,48.40,"ARMED",2.3,"center",false);
  label(187.00,48.40,"TRACK",2.3,"center",false);
  label(202.00,48.40,"FAULT",2.3,"center",false);
  label(217.00,48.40,"PWR",2.3,"center",false);
  label(158.00,66.50,"NODES",2.4,"center",true);
  label(158.00,54.50,"PAN",2.4,"center",true);
  label(158.00,42.50,"TILT",2.4,"center",true);
  label(91.50,36.90,"- MODE / CONFIG -",2.3,"center",false);
  label(194.50,36.90,"- COMMAND -",2.3,"center",false);
  label(39.00,19.80,"MODE",2.3,"center",false);
  label(54.00,19.80,"TRACK",2.3,"center",false);
  label(69.00,19.80,"LASER",2.3,"center",false);
  label(84.00,19.80,"NIGHT",2.3,"center",false);
  label(99.00,19.80,"REC",2.3,"center",false);
  label(114.00,19.80,"VERB",2.3,"center",false);
  label(129.00,19.80,"-",2.3,"center",false);
  label(144.00,19.80,"-",2.3,"center",false);
  label(172.00,19.80,"TEST",2.3,"center",false);
  label(187.00,19.80,"PAGE",2.3,"center",false);
  label(202.00,19.80,"HOME",2.3,"center",false);
  label(217.00,19.80,"ARM",2.3,"center",true);
  label(194.50,16.60,"soft . hw switch arms",1.7,"center",false);
  label(34.00,100.00,"MARKER SENTRY",5.5,"left",true);
  label(222.00,100.00,"IMSPI 8080",7.0,"right",true);
  label(34.00,89.00,"GROUND STATION . autonomous marker turret",3.0,"left",false);
  label(222.00,89.00,"Gib Systems . HMI",3.0,"right",false);
  // LED windows (through)
  thru_rrect(92.75,67.40,112.50,6.0,1.4);
  thru_rrect(92.75,55.40,112.50,6.0,1.4);
  thru_rrect(92.75,43.40,112.50,6.0,1.4);
  thru_rrect(194.50,55.40,55.00,6.0,1.4);
  // toggle holes + ear slots (through) — mounts are BACK bosses, not here
  thru_circ(39.00,28.40,6.2);
  thru_circ(54.00,28.40,6.2);
  thru_circ(69.00,28.40,6.2);
  thru_circ(84.00,28.40,6.2);
  thru_circ(99.00,28.40,6.2);
  thru_circ(114.00,28.40,6.2);
  thru_circ(129.00,28.40,6.2);
  thru_circ(144.00,28.40,6.2);
  thru_circ(172.00,28.40,6.2);
  thru_circ(187.00,28.40,6.2);
  thru_circ(202.00,28.40,6.2);
  thru_circ(217.00,28.40,6.2);
  thru_rrect(8.00,5.50,9.33,6.77,3.3);
  thru_rrect(8.00,126.50,9.33,6.77,3.3);
  thru_rrect(246.00,5.50,9.33,6.77,3.3);
  thru_rrect(246.00,126.50,9.33,6.77,3.3);
} }
difference(){ union(){ cube([FACE_W,FACE_H,TH]); bosses(); } cuts(); screw_blind(); }
