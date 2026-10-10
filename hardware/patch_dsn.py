"""Patch the KiCad-emitted Specctra DSN for Freerouting.

KiCad 10.0.4's exporter emits a bogus via padstack (netclass via geometry is
unset: '-0.001 um') and the flow's fine rules never make it into the DSN.
Freerouting would guess via sizes and route at 0.25/0.2 - which CANNOT escape
the RP2040's 0.4 mm-pitch QFN (the documented rev1 failure). Fix both:

  * via padstack -> Via[0-1]_600:300_um (0.6 mm dia / 0.3 mm drill; KiCad's
    SES importer parses dia:drill back out of the padstack name)
  * class rule  -> width 150 um / clearance 127 um (rev2-proven at JLC)

Run:  /usr/bin/python3 patch_dsn.py     # edits imspi8080.dsn in place
"""
import re

F = "imspi8080.dsn"
s = open(F).read()

# via padstack: rename everywhere + give it a real shape
s = s.replace("Via[0-1]_-0.001:-0.001_um", "Via[0-1]_600:300_um")
s = s.replace("(shape (circle F.Cu -0.001))", "(shape (circle F.Cu 600))")
s = s.replace("(shape (circle B.Cu -0.001))", "(shape (circle B.Cu 600))")

# rules: only the two '(rule ...)' blocks carry these exact lines.
# NB: the lines are INDENTED - the sub patterns must allow leading whitespace
# (a previous version missed this and every route ran at 0.25/0.2).
n_w = len(re.findall(r"^\s*\(width 250\)\s*$", s, re.M))
n_c = len(re.findall(r"^\s*\(clearance 200\)\s*$", s, re.M))
s = re.sub(r"^(\s*)\(width 250\)(\s*)$", r"\1(width 150)\2", s, flags=re.M)
s = re.sub(r"^(\s*)\(clearance 200\)(\s*)$", r"\1(clearance 127)\2", s, flags=re.M)
n_s = len(re.findall(r"^\s*\(clearance 50 \(type smd_smd\)\)\s*$", s, re.M))
s = re.sub(r"^(\s*)\(clearance 50 \(type smd_smd\)\)(\s*)$",
           r"\1(clearance 31.75 (type smd_smd))\2", s, flags=re.M)

open(F, "w").write(s)
print(f"patched {F}: {n_w} width + {n_c} clearance + {n_s} smd_smd lines, via padstack fixed")
# verify
s2 = open(F).read()
assert "(width 150)" in s2 and "(clearance 127)" in s2, "PATCH DID NOT STICK"
assert "Via[0-1]_600:300_um" in s2
print("verified: 150/127 rules + Via[0-1]_600:300_um present")
