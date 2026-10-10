#!/usr/bin/env python3
"""Build a flat imspi8080.kicad_sch from the SKiDL netlist.

Each component -> its proper KiCad symbol on a grid; every pin gets a global label
carrying its net name (global labels join by name -> full connectivity, ERC-valid,
matches the board). The 3 `extends` symbols are flattened into their base geometry.
Validated by exporting a netlist back out and comparing connectivity.
"""
import re, os, itertools

SYMDIR = "/usr/share/kicad/symbols"
NET = "imspi8080.net"
OUT = "imspi8080.kicad_sch"

# deterministic uuids (no Date/random)
_uc = itertools.count(1)
def uid():
    n = next(_uc)
    return f"00000000-0000-0000-0000-{n:012d}"

# ---------- S-expr reader ----------
def tokenize(s):
    return re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+', s)
def parse_all(s):
    toks = tokenize(s); pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            lst = []
            while toks[pos] != ')':
                lst.append(rd())
            pos += 1
            return lst
        if t.startswith('"'):
            return ('s', t[1:-1])
        return ('a', t)
    out = []
    while pos < len(toks):
        out.append(rd())
    return out
def kids(node, tag):
    return [x for x in node if isinstance(x, list) and x and x[0]==('a', tag)]
def kid(node, tag):
    a = kids(node, tag); return a[0] if a else None
def aval(node):
    return node[1][1] if node and len(node) >= 2 else None

# ---------- raw symbol block extractor ----------
_libcache = {}
def libtext(lib):
    if lib not in _libcache:
        _libcache[lib] = open(f"{SYMDIR}/{lib}.kicad_sym").read()
    return _libcache[lib]
def sym_block(lib, name):
    txt = libtext(lib); key = f'(symbol "{name}"'
    i = txt.find(key)
    if i < 0: return None
    d = 0; j = i
    while j < len(txt):
        c = txt[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return txt[i:j+1]
        j += 1
    return None

# ---------- pins + flattened lib_symbol for a lib:name ----------
def concrete(lib, name):
    """Follow (extends ...) to the symbol that actually holds sub-symbols/pins."""
    seen = set()
    while True:
        blk = sym_block(lib, name)
        node = parse_all(blk)[0]
        ext = kid(node, "extends")
        if not ext or name in seen:
            return blk, name
        seen.add(name); name = aval(ext)

def pins_and_defs(lib, part):
    """Return (pins [(num,x,y,rot)], [raw '(symbol "lib:part" ...)']). Flattens extends."""
    blk, cname = concrete(lib, part)
    node = parse_all(blk)[0]
    pins = list(_walk_pins(node))
    raw = blk.replace(f'(symbol "{cname}"', f'(symbol "{lib}:{part}"', 1)
    if cname != part:                       # rename base sub-symbols base_u_v -> part_u_v
        raw = raw.replace(f'"{cname}_', f'"{part}_')
    return pins, [raw]

def _walk_pins(node):
    for x in node:
        if isinstance(x, list) and x:
            if x[0] == ('a', 'pin'):
                at = kid(x, 'at'); num = kid(x, 'number')
                if at and num:
                    px = float(at[1][1]); py = float(at[2][1]); rot = int(float(at[3][1]))
                    yield (aval(num) if num[1][0]=='s' else num[1][1], px, py, rot)
            else:
                yield from _walk_pins(x)

def _graft(derived_blk, dname, bname, base_blk):
    """Make a self-contained (symbol "lib:dname" ...) using base graphics/pins + derived props."""
    # take base sub-symbols (the "bname_u_v" graphic/pin blocks), rename bname->dname
    subs = re.findall(r'\(symbol "'+re.escape(bname)+r'_\d+_\d+".*?\n\t\t\)', base_blk, re.S)
    if not subs:  # fallback: grab by brace matching
        subs = _extract_subsymbols(base_blk, bname)
    subs_renamed = [s.replace(f'"{bname}_', f'"{dname}_') for s in subs]
    # derived top-level props (everything before first sub-symbol or extends removed)
    props = re.findall(r'\(property "[^"]+" "[^"]*"[^)]*\([^)]*\)[^)]*\)', derived_blk)
    inner = "\n".join(props + subs_renamed)
    return f'(symbol "{dname if ":" in dname else dname}"\n{inner}\n)'.replace(
        f'(symbol "{dname}"', f'(symbol "LIBPLACEHOLDER:{dname}"', 1)

def _extract_subsymbols(blk, base):
    out = []; key = f'(symbol "{base}_'
    i = 0
    while True:
        i = blk.find(key, i)
        if i < 0: break
        d = 0; j = i
        while j < len(blk):
            if blk[j] == '(': d += 1
            elif blk[j] == ')':
                d -= 1
                if d == 0: out.append(blk[i:j+1]); i = j+1; break
            j += 1
    return out

# ---------- parse netlist ----------
tree = parse_all(open(NET).read())[0]
csec = kid(tree, "components"); nsec = kid(tree, "nets")
comps = []
for c in kids(csec, "comp"):
    ls = kid(c, "libsource")
    comps.append(dict(ref=aval(kid(c,"ref")), value=aval(kid(c,"value")) or "",
                      fp=aval(kid(c,"footprint")) or "",
                      lib=aval(kid(ls,"lib")), part=aval(kid(ls,"part"))))
pin2net = {}
for n in kids(nsec, "net"):
    nm = aval(kid(n, "name"))
    for nd in kids(n, "node"):
        pin2net[(aval(kid(nd,"ref")), aval(kid(nd,"pin")))] = nm

# ---------- gather symbol geometry ----------
sym_pins = {}; sym_defs = {}
for c in comps:
    lid = f"{c['lib']}:{c['part']}"
    if lid not in sym_pins:
        p, d = pins_and_defs(c['lib'], c['part'])
        sym_pins[lid] = p
        sym_defs[lid] = d[0].replace("LIBPLACEHOLDER", c['lib'])

def refnum(r):
    m = re.match(r'([A-Za-z]+)(\d+)', r); return (m.group(1), int(m.group(2))) if m else (r,0)
comps.sort(key=lambda c: refnum(c['ref']))

# PWR_FLAG symbol so ERC sees GND / VBUS_* as driven
PF_PINS, PF_DEF = pins_and_defs("power", "PWR_FLAG")
sym_defs["power:PWR_FLAG"] = PF_DEF[0]
PWR_NETS = ["GND", "VBUS_LOGIC", "VBUS_LED"]

# ---------- layout: big ICs up top, passives in a dense grid below (all on 1.27mm grid) ----------
G = 1.27
snap = lambda v: round(v / G) * G
X0, Y0 = 25.4, 30.48
big   = [c for c in comps if len(sym_pins[f"{c['lib']}:{c['part']}"]) > 4]
small = [c for c in comps if len(sym_pins[f"{c['lib']}:{c['part']}"]) <= 4]
pos = {}
CWB, CHB, COLB = 109.22, 165.1, 5
for i, c in enumerate(big):
    pos[c['ref']] = (snap(X0 + (i % COLB)*CWB), snap(Y0 + (i // COLB)*CHB))
ybase = snap(Y0 + ((len(big)+COLB-1)//COLB)*CHB + 20.32)
CWS, CHS, COLS = 35.56, 45.72, 13
for i, c in enumerate(small):
    pos[c['ref']] = (snap(X0 + (i % COLS)*CWS), snap(ybase + (i // COLS)*CHS))
PAP_W = max(COLB*CWB, COLS*CWS) + 50
PAP_H = ybase + ((len(small)+COLS-1)//COLS)*CHS + 40

# ---------- emit ----------
lab_ang = {0:0, 90:270, 180:180, 270:90}
def esc(s): return s.replace('\\','\\\\').replace('"','\\"')
out = []
out.append('(kicad_sch (version 20231120) (generator "skidl_flat") (generator_version "8.0")')
out.append(f'  (uuid "{uid()}")')
out.append(f'  (paper "User" {PAP_W:.1f} {PAP_H:.1f})')
out.append('  (lib_symbols')
for lid, d in sym_defs.items():
    out.append(d)
out.append('  )')

# PWR_FLAGs along the bottom margin
for k, net in enumerate(PWR_NETS):
    fx, fy = snap(X0 + k*38.1), snap(PAP_H - 12.7)
    out.append(f'  (symbol (lib_id "power:PWR_FLAG") (at {fx:.2f} {fy:.2f} 0) (unit 1)')
    out.append(f'    (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{uid()}")')
    out.append(f'    (property "Reference" "#FLG{k}" (at {fx:.2f} {fy-3:.2f} 0) (effects (font (size 1.0 1.0)) hide))')
    out.append(f'    (property "Value" "PWR_FLAG" (at {fx:.2f} {fy-6:.2f} 0) (effects (font (size 1.0 1.0)) hide))')
    out.append(f'    (pin "1" (uuid "{uid()}"))')
    out.append(f'    (instances (project "imspi8080" (path "/" (reference "#FLG{k}") (unit 1))))')
    out.append('  )')
    out.append(f'  (global_label "{net}" (shape output) (at {fx:.2f} {fy:.2f} 90)')
    out.append(f'    (effects (font (size 1.0 1.0)) (justify left)) (uuid "{uid()}"))')

for c in comps:
    lid = f"{c['lib']}:{c['part']}"
    sx, sy = pos[c['ref']]
    su = uid()
    out.append(f'  (symbol (lib_id "{lid}") (at {sx:.2f} {sy:.2f} 0) (unit 1)')
    out.append('    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
    out.append(f'    (uuid "{su}")')
    out.append(f'    (property "Reference" "{esc(c["ref"])}" (at {sx:.2f} {sy-2.54:.2f} 0))')
    out.append(f'    (property "Value" "{esc(c["value"])}" (at {sx:.2f} {sy+2.54:.2f} 0))')
    out.append(f'    (property "Footprint" "{esc(c["fp"])}" (at {sx:.2f} {sy:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
    for (num, px, py, rot) in sym_pins[lid]:
        out.append(f'    (pin "{num}" (uuid "{uid()}"))')
    out.append(f'    (instances (project "imspi8080" (path "/" (reference "{esc(c["ref"])}") (unit 1))))')
    out.append('  )')
    # global labels at pins
    for (num, px, py, rot) in sym_pins[lid]:
        net = pin2net.get((c['ref'], num))
        ax, ay = sx + px, sy - py
        if net is None:
            out.append(f'  (no_connect (at {ax:.2f} {ay:.2f}) (uuid "{uid()}"))')
        else:
            out.append(f'  (global_label "{esc(net)}" (shape input) (at {ax:.2f} {ay:.2f} {lab_ang.get(rot,0)})')
            out.append(f'    (effects (font (size 1.0 1.0)) (justify left)) (uuid "{uid()}"))')

out.append(')')
open(OUT, "w").write("\n".join(out))
print("wrote", OUT, "-", len(comps), "symbols,", len(pin2net), "pin-connections")
