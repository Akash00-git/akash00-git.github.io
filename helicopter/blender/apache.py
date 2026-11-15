"""Boeing AH-64D Apache Longbow (US Army) - high-detail Blender build.

Blender space: metres, nose +X, up +Z, port (left) side +Y, wheels on Z=0.
Main rotor mast axis at X=0, Y=0.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import bpy, bmesh
from mathutils import Vector, Matrix

PI = math.pi
C.reset()

KEYS = ('fuselage', 'cockpit', 'sensors', 'cannon', 'stubWing', 'weapons', 'engine',
        'mainRotor', 'tailRotor', 'stabilator', 'gear')
P = {k: C.part(k) for k in KEYS}

# ------------------------------------------------------------------ materials
HELO_DRAB = (0.045, 0.048, 0.026)   # Helo Drab (FS 34031), linear
M = {}
M['body'] = C.paint('apache_paint', HELO_DRAB, panel=(0.62, 0.44), rough=0.62, grime=0.5,
                    wear=0.2, wear_color=(0.20, 0.21, 0.19), soot=0.12)
M['parts'] = C.paint('apache_paint_parts', HELO_DRAB, panel=None, rough=0.6, grime=0.3, wear=0.0)
M['blade'] = C.paint('apache_blade_paint', (0.022, 0.024, 0.021), panel=None, rough=0.5,
                     grime=0.12, wear=0.08, wear_color=(0.25, 0.25, 0.24))
M['olive'] = C.simple('olive_detail', (0.025, 0.030, 0.018), rough=0.62)
M['olive2'] = C.simple('olive_store', (0.030, 0.035, 0.021), rough=0.55)
M['frame'] = C.simple('canopy_frame', (0.024, 0.028, 0.018), rough=0.55)
M['glass'] = C.glass('canopy_glass', tint=(0.62, 0.68, 0.64), rough=0.03)
M['steel'] = C.metal('steel', (0.32, 0.32, 0.33), 0.38)
M['chrome'] = C.metal('oleo_chrome', (0.75, 0.75, 0.76), 0.12)
M['gun'] = C.metal('gunmetal', (0.07, 0.07, 0.075), 0.45)
M['rubber'] = C.rubber('tyre_rubber')
M['soot'] = C.simple('exhaust_soot', (0.010, 0.010, 0.010), rough=0.92)
M['black'] = C.simple('matte_black', (0.016, 0.016, 0.017), rough=0.7)
M['int'] = C.simple('cockpit_interior', (0.032, 0.034, 0.033), rough=0.78)
M['seat'] = C.simple('seat_cushion', (0.045, 0.042, 0.030), rough=0.9)
M['mfd'] = C.simple('mfd_screen', (0.006, 0.010, 0.008), rough=0.08)
M['sensor'] = C.simple('sensor_window', (0.020, 0.012, 0.035), rough=0.04, metallic=0.6)
M['lens'] = C.simple('sensor_lens_amber', (0.10, 0.06, 0.02), rough=0.05, metallic=0.5)
M['yellow'] = C.simple('hellfire_yellow', (0.45, 0.33, 0.03), rough=0.6)
M['brown'] = C.simple('hellfire_brown', (0.08, 0.045, 0.02), rough=0.6)
M['stencil'] = C.simple('stencil_black', (0.009, 0.009, 0.008), rough=0.65)
M['walk'] = C.simple('antislip_walkway', (0.018, 0.019, 0.017), rough=0.95)
M['beacon'] = C.emit('emit_beacon', (1.0, 0.05, 0.02), 10.0)
M['red'] = C.emit('emit_red', (1.0, 0.04, 0.02), 8.0)
M['green'] = C.emit('emit_green', (0.05, 1.0, 0.25), 8.0)
M['white'] = C.emit('emit_white', (1.0, 0.95, 0.85), 8.0)


# ------------------------------------------------------------------ local helpers
def lathe(name, prof, mat, parent=None, loc=(0, 0, 0), axis='Z', seg=32, sharp=40, rot=None, cap=True):
    """Surface of revolution about local Z. prof = [(radius, height), ...]; r=0 makes a pole."""
    verts, faces, rings = [], [], []
    for (r, h) in prof:
        if r < 1e-6:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, h))
        else:
            idx = []
            for i in range(seg):
                a = 2 * PI * i / seg
                idx.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), h))
            rings.append(idx)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        if len(A) == 1:
            for i in range(seg):
                faces.append((A[0], B[i], B[(i + 1) % seg]))
        elif len(B) == 1:
            for i in range(seg):
                faces.append((A[i], A[(i + 1) % seg], B[0]))
        else:
            for i in range(seg):
                faces.append((A[i], A[(i + 1) % seg], B[(i + 1) % seg], B[i]))
    if cap:
        if len(rings[0]) > 1:
            faces.append(tuple(rings[0][::-1]))
        if len(rings[-1]) > 1:
            faces.append(tuple(rings[-1]))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    C.place(o, loc, rot if rot is not None else C._AX[axis])
    C.smooth_by_angle(o, sharp)
    return o


def foil(name, secs, span='Y', mat=None, parent=None, n=14, sharp=42):
    """Lifting surface through airfoil sections. Each sec: s (span coord), le (x of leading edge),
    c (chord), h (offset of chord line: z for span='Y', y for span='Z'), t (thickness ratio)."""
    verts, faces = [], []
    m = 0
    for s in secs:
        prof = C.airfoil(n, s.get('t', 0.12))
        m = len(prof)
        for (px, pz) in prof:
            X = s['le'] - px * s['c']
            T = s['h'] + pz * s['c']
            verts.append((X, s['s'], T) if span == 'Y' else (X, T, s['s']))
    ns = len(secs)
    for i in range(ns - 1):
        a, b = i * m, (i + 1) * m
        for j in range(m):
            k = (j + 1) % m
            faces.append((a + j, a + k, b + k, b + j))
    faces.append(tuple(range(m))[::-1])
    faces.append(tuple(range((ns - 1) * m, ns * m)))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    C.smooth_by_angle(o, sharp)
    return o


def quads(name, rings, mat, parent, cap=True, smooth=False, skip=()):
    """Faceted solid through rings of equal-length point lists (e.g. canopy). `skip` = strip
    indices to leave open (e.g. the canopy floor)."""
    verts, faces = [], []
    m = len(rings[0])
    for r in rings:
        verts += [tuple(p) for p in r]
    for i in range(len(rings) - 1):
        a, b = i * m, (i + 1) * m
        for j in range(m):
            if j in skip:
                continue
            k = (j + 1) % m
            faces.append((a + j, a + k, b + k, b + j))
    if cap:
        faces.append(tuple(range(m))[::-1])
        faces.append(tuple(range((len(rings) - 1) * m, len(rings) * m)))
    o = C.mesh_obj(name, verts, faces, parent, mat, smooth=smooth)
    C._fix_normals(o)
    return o


def bar(name, p1, p2, r, mat, parent, verts=8):
    return C.strut(name, p1, p2, r, mat=mat, parent=parent, verts=verts)


def flatbar(name, a, b, n, w, t, mat, parent, over=0.6):
    """Flat frame member from a to b, wide face (w) lying across normal n, thickness t along n."""
    a, b, n = Vector(a), Vector(b), Vector(n)
    d = b - a
    L = d.length
    d.normalize()
    n = (n - d * n.dot(d)).normalized()
    s = n.cross(d)
    rot = Matrix((d, s, n)).transposed().to_euler()
    return C.box(name, (L + w * over, w, t), tuple((a + b) / 2), rot=tuple(rot), mat=mat, parent=parent, bev=0.006, seg=1)


def blade_ccw(name, *a, **k):
    """C.blade puts the leading edge at local -Y (clockwise rotors). The Apache rotors turn
    counter-clockwise (spin_dir=+1), so mirror the blade in local Y: leading edge -> +Y."""
    o = C.blade(name, *a, **k)
    o.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return o


def solidify(o, t):
    m = o.modifiers.new('solid', 'SOLIDIFY')
    m.thickness = t
    m.offset = -1
    return o


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def side_pairs():
    return ((1, ''), (-1, '_R'))


# ================================================================== FUSELAGE
fus = P['fuselage']
body = C.loft('body', [
    dict(x=5.24, w=0.46, zt=1.60, zb=1.06, n=3.0),
    dict(x=5.12, w=0.70, zt=1.66, zb=1.00, n=3.2),
    dict(x=4.90, w=0.88, zt=1.71, zb=0.96, n=3.4, nt=4),
    dict(x=4.55, w=0.98, zt=1.74, zb=0.94, n=3.4, nt=5),
    dict(x=3.80, w=1.02, zt=1.74, zb=0.92, n=3.4, nt=6),
    dict(x=2.60, w=1.03, zt=1.75, zb=0.92, n=3.4, nt=6),
    dict(x=1.05, w=1.03, zt=1.77, zb=0.93, n=3.4, nt=6),
    dict(x=0.82, w=1.01, zt=2.50, zb=0.94, n=3.4, nt=5),
    dict(x=0.58, w=0.99, zt=2.77, zb=0.95, n=3.6, nt=5),
    dict(x=0.00, w=0.98, zt=2.81, zb=0.97, n=3.8, nt=5),
    dict(x=-0.70, w=0.98, zt=2.80, zb=1.00, n=3.8, nt=5),
    dict(x=-1.40, w=0.94, zt=2.70, zb=1.04, n=3.6, nt=4),
    dict(x=-2.10, w=0.88, zt=2.48, zb=1.07, n=3.4, nt=3.5),
    dict(x=-2.90, w=0.80, zt=2.22, zb=1.10, n=3.2, nt=3),
    dict(x=-3.70, w=0.72, zt=2.06, zb=1.10, n=3.0),
    dict(x=-4.90, w=0.64, zt=1.97, zb=1.08, n=3.0),
    dict(x=-6.20, w=0.57, zt=1.89, zb=1.07, n=3.0),
    dict(x=-7.40, w=0.50, zt=1.84, zb=1.07, n=3.0),
    dict(x=-8.40, w=0.44, zt=1.80, zb=1.09, n=3.0),
    dict(x=-9.05, w=0.36, zt=1.76, zb=1.15, n=3.0),
    dict(x=-9.42, w=0.20, zt=1.66, zb=1.33, n=2.6),
    dict(x=-9.50, w=0.08, zt=1.56, zb=1.42, n=2.2),
], mat=M['body'], parent=fus, seg=48)

# forward avionics bays ("cheeks") - boxy sponsons from the cockpit to the wing root
cheeks = C.loft('avionics_bays', [
    dict(x=4.48, w=0.96, zt=1.42, zb=1.06, n=3.0),
    dict(x=4.20, w=1.48, zt=1.54, zb=0.99, n=5, nb=3.5),
    dict(x=3.80, w=1.80, zt=1.60, zb=0.96, n=8, nb=4),
    dict(x=2.20, w=1.88, zt=1.62, zb=0.96, n=8, nb=4),
    dict(x=0.60, w=1.88, zt=1.64, zb=0.98, n=8, nb=4),
    dict(x=-0.30, w=1.82, zt=1.64, zb=1.02, n=8, nb=4),
    dict(x=-0.90, w=1.36, zt=1.56, zb=1.10, n=5, nb=3.5),
    dict(x=-1.35, w=0.86, zt=1.46, zb=1.18, n=3.0),
], mat=M['body'], parent=fus, seg=48)

# tail-rotor drive-shaft fairing along the boom top
C.loft('driveshaft_cover', [
    dict(x=-2.95, w=0.10, zt=2.20, zb=2.08, n=2.5),
    dict(x=-3.30, w=0.24, zt=2.20, zb=1.98, n=3.0),
    dict(x=-5.00, w=0.22, zt=2.07, zb=1.88, n=3.0),
    dict(x=-7.20, w=0.20, zt=1.98, zb=1.80, n=3.0),
    dict(x=-7.90, w=0.16, zt=1.94, zb=1.76, n=3.0),
], mat=M['body'], parent=fus, seg=24)

# vertical fin (swept, thick) with dorsal root
fin = foil('vertical_fin', [
    dict(s=1.50, le=-7.20, c=2.12, h=0.0, t=0.13),
    dict(s=1.80, le=-7.62, c=1.72, h=0.0, t=0.14),
    dict(s=2.30, le=-8.02, c=1.32, h=0.0, t=0.155),
    dict(s=3.00, le=-8.38, c=1.02, h=0.0, t=0.165),
    dict(s=3.52, le=-8.55, c=0.88, h=0.0, t=0.17),
    dict(s=3.62, le=-8.60, c=0.80, h=0.0, t=0.15),
    dict(s=3.67, le=-8.66, c=0.68, h=0.0, t=0.08),
], span='Z', mat=M['body'], parent=fus, n=16)

# doghouse (transmission fairing) flat side panels with louvres
for sgn, sfx in side_pairs():
    C.box('doghouse_panel' + sfx, (1.9, 0.04, 0.42), (-0.15, sgn * 0.475, 2.47), mat=M['olive'], parent=fus, bev=0.015)
    for i in range(7):
        C.box('louvre%d%s' % (i, sfx), (0.05, 0.03, 0.22), (0.45 - i * 0.09, sgn * 0.497, 2.47),
              rot=(0, 0, sgn * 0.35), mat=M['black'], parent=fus, bev=0.004, seg=1)
    # equipment boxes either side of the mast base (as seen head-on in the references)
    C.box('mast_side_box' + sfx, (0.34, 0.16, 0.16), (0.30, sgn * 0.30, 2.86), mat=M['olive'], parent=fus, bev=0.02)
    C.box('mast_side_box_lid' + sfx, (0.30, 0.13, 0.02), (0.30, sgn * 0.30, 2.95), mat=M['black'], parent=fus, bev=0.005)
    # grab handles on the doghouse
    for j, xx in enumerate((0.55, -1.05)):
        hz = 2.30
        bar('handle%d%s_a' % (j, sfx), (xx, sgn * 0.49, hz), (xx, sgn * 0.55, hz), 0.012, M['steel'], fus, 6)
        bar('handle%d%s_b' % (j, sfx), (xx - 0.18, sgn * 0.49, hz), (xx - 0.18, sgn * 0.55, hz), 0.012, M['steel'], fus, 6)
        bar('handle%d%s_c' % (j, sfx), (xx, sgn * 0.55, hz), (xx - 0.18, sgn * 0.55, hz), 0.012, M['steel'], fus, 6)
    # fold-out boarding steps on the avionics bays
    for j, (xx, zz) in enumerate(((2.7, 1.20), (1.25, 1.28))):
        C.box('step%d%s' % (j, sfx), (0.20, 0.07, 0.03), (xx, sgn * 0.965, zz), mat=M['steel'], parent=fus, bev=0.006)
        C.box('step_plate%d%s' % (j, sfx), (0.24, 0.012, 0.10), (xx, sgn * 0.94, zz + 0.02), mat=M['olive'], parent=fus, bev=0.003)
    # avionics bay door hinges and latches
    for j in range(5):
        xx = 3.4 - j * 0.75
        C.box('bay_hinge%d%s' % (j, sfx), (0.12, 0.022, 0.025), (xx, sgn * 0.94, 1.585), mat=M['olive'], parent=fus, bev=0.006)
        C.box('bay_latch%d%s' % (j, sfx), (0.06, 0.015, 0.03), (xx + 0.3, sgn * 0.945, 1.08), mat=M['black'], parent=fus, bev=0.004)
    # chaff/flare dispenser on the boom side
    C.box('cm_dispenser' + sfx, (0.34, 0.07, 0.20), (-3.9, sgn * 0.38, 1.58), mat=M['olive'], parent=fus, bev=0.015)
    for k in range(6):
        C.box('cm_cell%d%s' % (k, sfx), (0.04, 0.012, 0.15), (-3.77 - k * 0.052, sgn * 0.418, 1.58), mat=M['black'], parent=fus, bev=0)
    # RWR antennas on the nose and on the tail
    C.cyl('rwr_nose' + sfx, 0.055, 0.04, loc=(4.95, sgn * 0.40, 1.42), rot=(0, PI / 2, sgn * 0.6),
          mat=M['olive'], parent=fus, verts=20, bev=0.008)
    C.cyl('rwr_tail' + sfx, 0.05, 0.04, loc=(-9.3, sgn * 0.12, 1.62), rot=(0, -PI / 2, -sgn * 0.5),
          mat=M['olive'], parent=fus, verts=20, bev=0.008)

# antennas
C.box('uhf_blade_top', (0.30, 0.025, 0.20), (-1.65, 0, 2.86), rot=(0, 0.25, 0), mat=M['olive'], parent=fus, bev=0.008)
C.box('vhf_blade_belly', (0.36, 0.025, 0.24), (-1.9, 0, 0.98), rot=(0, -0.3, 0), mat=M['olive'], parent=fus, bev=0.008)
C.box('blade_boom', (0.26, 0.022, 0.16), (-5.9, 0, 1.97), rot=(0, 0.3, 0), mat=M['olive'], parent=fus, bev=0.007)
C.box('blade_boom_low', (0.24, 0.022, 0.14), (-5.2, 0, 1.03), rot=(0, -0.3, 0), mat=M['olive'], parent=fus, bev=0.007)
C.cyl('gps_dome', 0.09, 0.05, loc=(-0.9, 0, 2.82), mat=M['olive'], parent=fus, verts=24, bev=0.02)
bar('fin_whip', (-9.05, 0, 3.66), (-9.12, 0, 4.30), 0.006, M['black'], fus, 6)
# ALQ-144 IR jammer on the aft doghouse
C.cyl('alq144_base', 0.12, 0.08, loc=(-1.95, 0, 2.66), mat=M['olive'], parent=fus, verts=24, bev=0.01)
lathe('alq144_head', [(0.0, 0.0), (0.11, 0.0), (0.12, 0.12), (0.105, 0.20), (0.0, 0.22)], M['black'],
      fus, loc=(-1.95, 0, 2.70), seg=24)
# upper (canopy) and lower (nose) wire cutters
C.box('wsps_upper_base', (0.22, 0.05, 0.05), (2.24, 0, 2.735), mat=M['steel'], parent=fus, bev=0.01)
C.box('wsps_upper_blade', (0.34, 0.016, 0.10), (2.32, 0, 2.81), rot=(0, 0.42, 0), mat=M['steel'], parent=fus, bev=0.004)
C.box('wsps_lower_blade', (0.34, 0.018, 0.10), (5.02, 0, 0.84), rot=(0, 0.75, 0), mat=M['steel'], parent=fus, bev=0.004)
C.box('wsps_lower_base', (0.22, 0.06, 0.05), (4.95, 0, 0.97), mat=M['olive'], parent=fus, bev=0.01)
# walkway anti-slip strips on the upper deck
C.box('walkway_L', (1.2, 0.18, 0.006), (-0.2, 0.25, 2.815), mat=M['walk'], parent=fus, bev=0)
C.box('walkway_R', (1.2, 0.18, 0.006), (-0.2, -0.25, 2.815), mat=M['walk'], parent=fus, bev=0)

# markings: low-visibility 'U.S. ARMY' on the boom, serial on the fin
C.stencil('mark_army_L', 'U.S. ARMY', body, (-5.45, 0.40, 1.52), rot=(PI / 2, 0, PI), size=0.26, mat=M['stencil'], parent=fus)
C.stencil('mark_army_R', 'U.S. ARMY', body, (-5.45, -0.40, 1.52), size=0.26, mat=M['stencil'], parent=fus)
C.stencil('mark_serial_L', '05-07012', fin, (-8.75, 0.20, 2.55), rot=(PI / 2, 0, PI), size=0.13, mat=M['stencil'], parent=fus)
C.stencil('mark_serial_R', '05-07012', fin, (-8.75, -0.20, 2.55), size=0.13, mat=M['stencil'], parent=fus)

# fin: tail-rotor drive-shaft fairing up the leading edge + intermediate gearbox bulge at the root
bar('fin_shaft_fairing', (-7.70, 0, 1.78), (-8.66, 0, 3.58), 0.075, M['body'], fus, 20)
C.sphere('intermediate_gearbox', 1.0, loc=(-7.62, 0, 1.84), scale=(0.34, 0.17, 0.15), mat=M['body'], parent=fus, seg=28, rings=14)
# formation-light strips (unlit) on fin and boom
M['strip'] = C.simple('formation_strip', (0.085, 0.10, 0.065), rough=0.4)
for sgn, sfx in side_pairs():
    C.box('strip_fin' + sfx, (0.05, 0.006, 0.42), (-8.92, sgn * 0.083, 2.75), rot=(0, -0.25, 0), mat=M['strip'], parent=fus, bev=0)
    C.box('strip_boom' + sfx, (0.42, 0.006, 0.05), (-6.9, sgn * 0.268, 1.47), mat=M['strip'], parent=fus, bev=0)
    # raised avionics-bay access doors
    for j, (xx, yy) in enumerate(((2.6, 0.942), (1.8, 0.942), (1.0, 0.942), (0.25, 0.935))):
        C.box('bay_door%d%s' % (j, sfx), (0.66, 0.012, 0.40), (xx, sgn * yy, 1.31), mat=M['parts'], parent=fus, bev=0.004, seg=1)

# lights: anti-collision beacons (fin top, belly), tail position light
C.cyl('beacon_fin_base', 0.05, 0.03, loc=(-8.98, 0, 3.675), mat=M['olive'], parent=fus, verts=16, bev=0)
C.sphere('beacon_top', 0.045, loc=(-8.98, 0, 3.71), scale=(1, 1, 0.8), mat=M['beacon'], parent=fus, seg=16, rings=8)
C.sphere('beacon_belly', 0.05, loc=(-0.9, 0, 0.99), scale=(1, 1, 0.7), mat=M['beacon'], parent=fus, seg=16, rings=8)
C.sphere('tail_light', 0.035, loc=(-9.50, 0, 1.49), mat=M['white'], parent=fus, seg=16, rings=8)

# ================================================================== COCKPIT
ck = P['cockpit']
# canopy rings: (bottom-left, top-left, top-right, bottom-right)


def cring(xb, yb, zb, xt, yt, zt):
    return [(xb, yb, zb), (xt, yt, zt), (xt, -yt, zt), (xb, -yb, zb)]


RA = cring(4.70, 0.40, 1.66, 4.27, 0.25, 2.22)   # CPG windscreen
RB = cring(3.24, 0.45, 1.68, 3.25, 0.27, 2.26)   # CPG rear / pilot windscreen base
RC = cring(3.20, 0.455, 1.68, 2.86, 0.28, 2.70)  # pilot windscreen top
RD = cring(1.18, 0.465, 1.72, 1.28, 0.29, 2.72)  # pilot canopy rear
cg = quads('canopy_glass', [RA, RB, RC, RD], M['glass'], ck, skip=(3,))

fr = M['frame']
bm = bmesh.new()
bm.from_mesh(cg.data)
bm.normal_update()
for i, e in enumerate(bm.edges):
    a, b = e.verts[0].co.copy(), e.verts[1].co.copy()
    if (a - b).length < 0.06 or not e.link_faces:
        continue
    n = Vector((0, 0, 0))
    for f in e.link_faces:
        n += f.normal
    flatbar('canopy_frame%d' % i, a, b, n, 0.075, 0.036, fr, ck)
bm.free()
# pilot side-door split frame + CPG door handle rail
for sgn in (1, -1):
    pb = lerp(RC[0 if sgn > 0 else 3], RD[0 if sgn > 0 else 3], 0.55)
    pt = lerp(RC[1 if sgn > 0 else 2], RD[1 if sgn > 0 else 2], 0.55)
    flatbar('pilot_door_split%s' % ('' if sgn > 0 else '_R'), pb, pt, (0, sgn, 0.3), 0.06, 0.03, fr, ck)
    cb = lerp(RA[0 if sgn > 0 else 3], RB[0 if sgn > 0 else 3], 0.5)
    ct = lerp(RA[1 if sgn > 0 else 2], RB[1 if sgn > 0 else 2], 0.5)
    hz = lerp(cb, ct, 0.35)
    C.box('cpg_door_handle%s' % ('' if sgn > 0 else '_R'), (0.16, 0.025, 0.03), (hz[0], hz[1] + sgn * 0.012, hz[2]),
          mat=M['black'], parent=ck, bev=0.005)
# canopy hinges on the starboard roof edge
for j, xx in enumerate((3.9, 3.5, 2.5, 1.9)):
    zz = 2.24 if xx > 3.2 else 2.715
    yy = 0.27 if xx > 3.2 else 0.285
    C.box('canopy_hinge%d' % j, (0.08, 0.04, 0.03), (xx, -yy - 0.01, zz), mat=M['steel'], parent=ck, bev=0.006)
# windscreen wipers
for nm, base, tip in (('wiper_cpg', (4.66, 0.05, 1.72), (4.42, 0.14, 2.03)),
                      ('wiper_pilot', (3.22, 0.04, 2.29), (3.03, 0.12, 2.50))):
    bar(nm, base, tip, 0.008, M['black'], ck, 6)
# blast shield between the crew stations
C.box('blast_shield', (0.02, 0.84, 0.50), (3.21, 0, 1.97), mat=M['glass'], parent=ck, bev=0.004)

# interior tub
C.box('cockpit_floor', (3.45, 0.84, 0.10), (2.90, 0, 1.70), mat=M['int'], parent=ck, bev=0.01)
for sgn in (1, -1):
    s = '' if sgn > 0 else '_R'
    C.box('cpg_console' + s, (0.70, 0.12, 0.16), (3.75, sgn * 0.36, 1.82), mat=M['int'], parent=ck, bev=0.01)
    C.box('plt_console' + s, (1.10, 0.12, 0.20), (2.10, sgn * 0.37, 1.84), mat=M['int'], parent=ck, bev=0.01)
# CPG station: panel with ORT sight, two MFDs, seat
C.box('cpg_panel', (0.12, 0.70, 0.36), (4.22, 0, 1.92), rot=(0, 0.25, 0), mat=M['int'], parent=ck, bev=0.01)
C.box('cpg_ort', (0.36, 0.26, 0.22), (4.02, 0, 2.00), mat=M['int'], parent=ck, bev=0.03)
C.box('cpg_ort_hood', (0.08, 0.22, 0.12), (3.83, 0, 2.03), mat=M['black'], parent=ck, bev=0.02)
for sgn in (1, -1):
    C.box('cpg_mfd%s' % ('' if sgn > 0 else '_R'), (0.012, 0.17, 0.17), (4.155, sgn * 0.23, 1.92), rot=(0, 0.25, 0),
          mat=M['mfd'], parent=ck, bev=0)
C.box('cpg_seat_pan', (0.42, 0.44, 0.08), (3.55, 0, 1.80), mat=M['seat'], parent=ck, bev=0.02)
C.box('cpg_seat_back', (0.10, 0.46, 0.46), (3.33, 0, 1.99), rot=(0, -0.12, 0), mat=M['seat'], parent=ck, bev=0.025)
C.box('cpg_headrest', (0.09, 0.24, 0.12), (3.30, 0, 2.13), rot=(0, -0.12, 0), mat=M['int'], parent=ck, bev=0.02)
bar('cpg_cyclic', (3.75, -0.24, 1.75), (3.77, -0.24, 1.98), 0.014, M['black'], ck)
bar('cpg_cyclic2', (3.75, 0.24, 1.75), (3.77, 0.24, 1.98), 0.014, M['black'], ck)
# pilot station: raised seat, panel, glareshield
C.box('plt_seat_riser', (0.40, 0.40, 0.22), (1.84, 0, 1.86), mat=M['int'], parent=ck, bev=0.02)
C.box('plt_seat_pan', (0.42, 0.44, 0.08), (1.84, 0, 2.01), mat=M['seat'], parent=ck, bev=0.02)
C.box('plt_seat_back', (0.10, 0.46, 0.56), (1.62, 0, 2.30), rot=(0, -0.12, 0), mat=M['seat'], parent=ck, bev=0.025)
C.box('plt_headrest', (0.09, 0.24, 0.14), (1.58, 0, 2.48), rot=(0, -0.12, 0), mat=M['int'], parent=ck, bev=0.02)
C.box('plt_panel', (0.12, 0.70, 0.40), (2.86, 0, 2.08), rot=(0, 0.2, 0), mat=M['int'], parent=ck, bev=0.01)
C.box('plt_glareshield', (0.30, 0.74, 0.05), (2.92, 0, 2.30), mat=M['black'], parent=ck, bev=0.02)
for sgn in (1, -1):
    C.box('plt_mfd%s' % ('' if sgn > 0 else '_R'), (0.012, 0.18, 0.18), (2.795, sgn * 0.20, 2.10), rot=(0, 0.2, 0),
          mat=M['mfd'], parent=ck, bev=0)
bar('plt_cyclic', (2.15, 0, 1.85), (2.17, 0, 2.14), 0.015, M['black'], ck)
bar('plt_collective', (2.02, 0.30, 1.92), (1.72, 0.32, 2.02), 0.015, M['black'], ck)
# crew-station coordinates above were authored 0.38 m forward of their true station;
# slide the whole cockpit aft so the pilot's canopy ends just ahead of the mast
CKX = -0.38
for o in ck.children:
    o.location.x += CKX

# ================================================================== SENSORS (TADS / PNVS)
sn = P['sensors']
# azimuth housing under the nose front
lathe('tads_housing', [(0.0, 1.62), (0.20, 1.62), (0.24, 1.55), (0.25, 1.30), (0.22, 1.10), (0.0, 1.06)],
      M['body'], sn, loc=(5.30, 0, 0), seg=32)
for sgn in (1, -1):
    s = '' if sgn > 0 else '_R'
    # elevation drums ("ears") either side
    C.cyl('tads_drum' + s, 0.27, 0.25, loc=(5.48, sgn * 0.285, 1.30), axis='Y', mat=M['body'], parent=sn, verts=40, bev=0.03)
    C.cyl('tads_drum_cap' + s, 0.22, 0.03, loc=(5.48, sgn * 0.42, 1.30), axis='Y', mat=M['olive'], parent=sn, verts=32, bev=0.008)
C.box('tads_centre', (0.46, 0.34, 0.44), (5.48, 0, 1.30), mat=M['body'], parent=sn, bev=0.07)
# port drum: large round FLIR window; starboard drum: day TV + laser windows
C.cyl('tads_flir_rim', 0.15, 0.05, loc=(5.735, 0.285, 1.30), axis='X', mat=M['black'], parent=sn, verts=32, bev=0.01)
C.cyl('tads_flir_window', 0.128, 0.02, loc=(5.762, 0.285, 1.30), axis='X', mat=M['sensor'], parent=sn, verts=32, bev=0)
C.box('tads_dtv_frame', (0.05, 0.22, 0.17), (5.73, -0.285, 1.35), mat=M['black'], parent=sn, bev=0.01)
C.box('tads_dtv_window', (0.02, 0.19, 0.14), (5.757, -0.285, 1.35), mat=M['sensor'], parent=sn, bev=0)
C.cyl('tads_laser_window', 0.045, 0.03, loc=(5.74, -0.285, 1.20), axis='X', mat=M['lens'], parent=sn, verts=20, bev=0)
C.box('tads_shroud', (0.34, 0.70, 0.06), (5.48, 0, 1.58), mat=M['olive'], parent=sn, bev=0.02)
# PNVS turret on top of the nose
lathe('pnvs_base', [(0.0, 1.62), (0.13, 1.62), (0.13, 1.68), (0.0, 1.68)], M['olive'], sn, loc=(5.30, 0, 0), seg=28)
C.box('pnvs_head', (0.26, 0.24, 0.20), (5.33, 0, 1.79), mat=M['body'], parent=sn, bev=0.06)
C.box('pnvs_window', (0.02, 0.15, 0.10), (5.465, 0, 1.79), mat=M['sensor'], parent=sn, bev=0)
C.box('pnvs_brow', (0.06, 0.24, 0.03), (5.44, 0, 1.87), mat=M['olive'], parent=sn, bev=0.008)

# ================================================================== CANNON (M230 turret)
cn = P['cannon']
GX, GZ = 3.35, 0.62
C.cyl('turret_ring', 0.25, 0.10, loc=(GX, 0, 0.88), mat=M['olive'], parent=cn, verts=36, bev=0.02)
C.cyl('turret_azimuth', 0.19, 0.08, loc=(GX, 0, 0.80), mat=M['gun'], parent=cn, verts=32, bev=0.015)
for sgn in (1, -1):
    s = '' if sgn > 0 else '_R'
    C.box('turret_arm' + s, (0.26, 0.05, 0.24), (GX, sgn * 0.14, 0.68), mat=M['olive'], parent=cn, bev=0.02)
    bar('turret_actuator' + s, (GX + 0.10, sgn * 0.11, 0.78), (GX + 0.26, sgn * 0.11, GZ + 0.03), 0.018, M['chrome'], cn)
C.cyl('turret_trunnion', 0.05, 0.34, loc=(GX, 0, GZ), axis='Y', mat=M['gun'], parent=cn, verts=20, bev=0.005)
C.box('gun_receiver', (0.62, 0.17, 0.18), (GX - 0.02, 0, GZ), mat=M['gun'], parent=cn, bev=0.015)
C.box('gun_feeder', (0.22, 0.10, 0.12), (GX - 0.05, 0.13, GZ + 0.03), mat=M['gun'], parent=cn, bev=0.01)
C.cyl('gun_recoil_sleeve', 0.065, 0.24, loc=(GX + 0.38, 0, GZ), axis='X', mat=M['gun'], parent=cn, verts=24, bev=0.01)
C.cyl('gun_barrel', 0.038, 1.02, loc=(GX + 1.0, 0, GZ), axis='X', mat=M['gun'], parent=cn, verts=20, bev=0)
C.cyl('gun_muzzle', 0.055, 0.14, loc=(GX + 1.56, 0, GZ), axis='X', mat=M['gun'], parent=cn, verts=20, bev=0.008)
C.cyl('gun_bore', 0.022, 0.02, loc=(GX + 1.63, 0, GZ), axis='X', mat=M['soot'], parent=cn, verts=16, bev=0)
# flexible ammunition chute up into the fuselage
prev = (GX - 0.05, 0.17, GZ + 0.08)
for k in range(7):
    t = (k + 1) / 7
    p = (GX - 0.05 - 0.55 * t, 0.17 + 0.05 * math.sin(t * PI), GZ + 0.08 + 0.26 * t ** 0.6)
    bar('ammo_chute%d' % k, prev, p, 0.045, M['black'], cn, 8)
    prev = p

# ================================================================== STUB WINGS
sw = P['stubWing']
WZ = 1.75
foil('stub_wing', [
    dict(s=-2.46, le=0.20, c=0.96, h=WZ - 0.02, t=0.15),
    dict(s=-1.40, le=0.24, c=1.04, h=WZ - 0.01, t=0.16),
    dict(s=-0.40, le=0.30, c=1.14, h=WZ, t=0.17),
    dict(s=0.40, le=0.30, c=1.14, h=WZ, t=0.17),
    dict(s=1.40, le=0.24, c=1.04, h=WZ - 0.01, t=0.16),
    dict(s=2.46, le=0.20, c=0.96, h=WZ - 0.02, t=0.15),
], span='Y', mat=M['body'], parent=sw, n=16)
PYL = (1.42, 2.13)
for sgn, s in side_pairs():
    # wingtip pods (countermeasure / light pods)
    lathe('wingtip_pod' + s, [(0.0, -0.42), (0.07, -0.40), (0.12, -0.32), (0.135, -0.15), (0.135, 0.22),
                              (0.12, 0.38), (0.07, 0.46), (0.0, 0.48)],
          M['body'], sw, loc=(-0.20, sgn * 2.52, WZ - 0.03), axis='X', seg=32)
    C.sphere('nav_light' + s, 0.034, loc=(0.24, sgn * 2.60, WZ + 0.01), mat=M['red'] if sgn > 0 else M['green'],
             parent=sw, seg=16, rings=8)
    C.box('wing_walk' + s, (0.6, 0.9, 0.005), (-0.15, sgn * 1.15, WZ + 0.087), mat=M['walk'], parent=sw, bev=0)
    for j, py in enumerate(PYL):
        C.box('pylon%d%s' % (j, s), (0.62, 0.12, 0.30), (-0.20, sgn * py, WZ - 0.21), mat=M['body'], parent=sw, bev=0.035)
        C.box('pylon_rack%d%s' % (j, s), (0.50, 0.15, 0.05), (-0.20, sgn * py, WZ - 0.37), mat=M['olive'], parent=sw, bev=0.01)
        for k in (-1, 1):
            bar('sway_brace%d%d%s' % (j, k, s), (-0.20 + k * 0.18, sgn * py, WZ - 0.38),
                (-0.20 + k * 0.18, sgn * (py + 0.09), WZ - 0.43), 0.012, M['steel'], sw, 6)
            bar('sway_brace%d%d%s_b' % (j, k, s), (-0.20 + k * 0.18, sgn * py, WZ - 0.38),
                (-0.20 + k * 0.18, sgn * (py - 0.09), WZ - 0.43), 0.012, M['steel'], sw, 6)

# ================================================================== WEAPONS
wp = P['weapons']
RACK_Z = WZ - 0.40   # bottom of pylon racks


def rocket_pod(name, y):
    zc = RACK_Z - 0.215
    lathe(name + '_shell', [(0.0, -0.80), (0.12, -0.80), (0.19, -0.74), (0.205, -0.62), (0.205, 0.70),
                            (0.212, 0.74), (0.212, 0.80), (0.195, 0.80)],
          M['olive2'], wp, loc=(-0.12, y, zc), axis='X', seg=40, cap=True)
    for k, xx in enumerate((0.45, -0.55)):
        C.cyl('%s_band%d' % (name, k), 0.212, 0.05, loc=(xx, y, zc), axis='X', mat=M['black'], parent=wp, verts=40, bev=0.004)
    C.box(name + '_lug', (0.5, 0.08, 0.05), (-0.20, y, RACK_Z - 0.015), mat=M['olive2'], parent=wp, bev=0.01)
    pts = [(0.0, 0.0)]
    d = 0.08
    for i in range(6):
        a = i * PI / 3
        pts.append((d * math.cos(a), d * math.sin(a)))
        pts.append((2 * d * math.cos(a), 2 * d * math.sin(a)))
        b = a + PI / 6
        pts.append((math.sqrt(3) * d * math.cos(b), math.sqrt(3) * d * math.sin(b)))
    for k, (py, pz) in enumerate(pts):
        C.torus('%s_tube%d' % (name, k), 0.034, 0.006, loc=(0.688, y + py, zc + pz), axis='X',
                mat=M['steel'], parent=wp, seg=16, cs=6)
        C.cyl('%s_hole%d' % (name, k), 0.031, 0.01, loc=(0.684, y + py, zc + pz), axis='X',
              mat=M['soot'], parent=wp, verts=16, bev=0)


def hellfire(name, x0, y, z):
    """AGM-114: nose at x0, body along -X."""
    L, R = 1.63, 0.089
    lathe(name + '_body', [(0.0, 0.0), (0.05, -0.012), (0.08, -0.045), (R, -0.10), (R, -L + 0.06), (0.075, -L + 0.01),
                           (0.05, -L)], M['olive2'], wp, loc=(x0, y, z), axis='X', seg=24)
    C.sphere(name + '_seeker', 0.062, loc=(x0 - 0.035, y, z), scale=(0.8, 1, 1), mat=M['sensor'], parent=wp, seg=20, rings=10)
    C.cyl(name + '_band_y', R + 0.002, 0.05, loc=(x0 - 0.42, y, z), axis='X', mat=M['yellow'], parent=wp, verts=24, bev=0)
    C.cyl(name + '_band_b', R + 0.002, 0.04, loc=(x0 - 0.80, y, z), axis='X', mat=M['brown'], parent=wp, verts=24, bev=0)
    for k in range(4):
        a = PI / 4 + k * PI / 2
        ca, sa = math.cos(a), math.sin(a)
        # mid wings (cropped delta) and tail control fins
        for nm, xc, ln, sp in (('wing', x0 - 0.98, 0.34, 0.075), ('fin', x0 - 1.52, 0.14, 0.072)):
            C.box('%s_%s%d' % (name, nm, k), (ln, 0.006, sp), (xc, y + ca * (R + sp / 2), z + sa * (R + sp / 2)),
                  rot=(a - PI / 2, 0, 0), mat=M['olive2'], parent=wp, bev=0.002, seg=1)


def m299(name, y):
    z_top, z_bot = RACK_Z - 0.06, RACK_Z - 0.43
    C.box(name + '_spine', (0.60, 0.08, 0.45), (-0.20, y, RACK_Z - 0.24), mat=M['olive2'], parent=wp, bev=0.015)
    for k, zz in enumerate((z_top, z_bot)):
        C.box('%s_arm%d' % (name, k), (1.05, 0.46, 0.055), (-0.15, y, zz), mat=M['olive2'], parent=wp, bev=0.012)
        for j, dy in enumerate((-0.19, 0.19)):
            C.box('%s_rail%d%d' % (name, k, j), (1.10, 0.05, 0.03), (-0.10, y + dy, zz - 0.04), mat=M['steel'], parent=wp, bev=0.006)
            hellfire('%s_hf%d%d' % (name, k, j), 0.70, y + dy, zz - 0.145)


for sgn, s in side_pairs():
    m299('hellfire_launcher' + s, sgn * PYL[0])
    rocket_pod('rocket_pod' + s, sgn * PYL[1])

# ================================================================== ENGINES (T700 nacelles + Black Hole IR suppressors)
en = P['engine']
NY, NZ = 0.97, 2.36
for sgn, s in side_pairs():
    y = sgn * NY
    C.loft('nacelle' + s, [
        dict(x=0.60, w=0.58, zt=NZ + 0.30, zb=NZ - 0.31, y=y, n=2.2),
        dict(x=0.52, w=0.68, zt=NZ + 0.36, zb=NZ - 0.38, y=y, n=2.3),
        dict(x=0.25, w=0.76, zt=NZ + 0.41, zb=NZ - 0.44, y=y, n=2.5, nb=2.8),
        dict(x=-0.40, w=0.78, zt=NZ + 0.42, zb=NZ - 0.46, y=y, n=2.6, nb=3.0),
        dict(x=-1.05, w=0.76, zt=NZ + 0.40, zb=NZ - 0.42, y=y, n=2.6, nb=2.8),
        dict(x=-1.42, w=0.68, zt=NZ + 0.34, zb=NZ - 0.33, y=y, n=2.6),
        dict(x=-1.56, w=0.60, zt=NZ + 0.30, zb=NZ - 0.29, y=y, n=2.6),
    ], mat=M['body'], parent=en, seg=40)
    # intake: lip, dark throat, inlet bullet
    C.torus('intake_lip' + s, 0.225, 0.048, loc=(0.60, y, NZ), axis='X', mat=M['olive'], parent=en, seg=40, cs=12)
    C.cyl('intake_throat' + s, 0.228, 0.03, loc=(0.585, y, NZ), axis='X', mat=M['soot'], parent=en, verts=40, bev=0)
    lathe('intake_bullet' + s, [(0.0, 0.0), (0.05, 0.03), (0.085, 0.10), (0.095, 0.20)], M['steel'], en,
          loc=(0.70, y, NZ), rot=(0, -PI / 2, 0), seg=24, cap=True)
    # engine-to-fuselage pylon fairing
    C.box('engine_pylon' + s, (1.5, 0.30, 0.30), (-0.45, sgn * 0.66, NZ + 0.06), mat=M['body'], parent=en, bev=0.07)
    # cowling hinge line + latches
    bar('cowl_hinge' + s, (0.30, sgn * (NY + 0.37), NZ + 0.10), (-1.10, sgn * (NY + 0.365), NZ + 0.10), 0.012, M['olive'], en, 6)
    for k in range(4):
        C.box('cowl_latch%d%s' % (k, s), (0.07, 0.02, 0.03), (0.05 - k * 0.35, sgn * (NY + 0.385), NZ - 0.12),
              mat=M['black'], parent=en, bev=0.004)
    # oil-cooler exhaust grille on the nacelle top
    C.box('cooler_grille' + s, (0.42, 0.24, 0.012), (-0.80, y, NZ + 0.415), mat=M['soot'], parent=en, bev=0)
    for k in range(7):
        C.box('cooler_slat%d%s' % (k, s), (0.025, 0.25, 0.022), (-0.98 + k * 0.06, y, NZ + 0.418),
              mat=M['olive'], parent=en, bev=0.003, seg=1)
    # Black Hole exhaust: squared duct turned outboard, open soot-black exit
    ex = C.empty('exhaust_frame' + s, en, (-1.44, y, NZ + 0.02), (0, 0, sgn * -0.42))
    duct = C.loft('bh_exhaust' + s, [
        dict(x=0.10, w=0.58, zt=0.29, zb=-0.29, n=2.6),
        dict(x=-0.20, w=0.56, zt=0.28, zb=-0.27, n=3.4),
        dict(x=-0.55, w=0.52, zt=0.27, zb=-0.25, n=4.2),
        dict(x=-0.85, w=0.50, zt=0.26, zb=-0.24, n=4.6),
    ], mat=M['body'], parent=ex, seg=40, cap=False)
    solidify(duct, 0.025)
    C.box('bh_exhaust_plug' + s, (0.08, 0.40, 0.42), (-0.50, 0, 0.01), mat=M['soot'], parent=ex, bev=0.03)
    # air-data sensor booms: stalk up from the nacelle, arm outboard, probe forward
    p0 = (0.10, sgn * 0.78, NZ + 0.36)
    p1 = (0.10, sgn * 0.78, NZ + 0.55)
    p2 = (0.22, sgn * 1.42, NZ + 0.58)
    p3 = (0.48, sgn * 1.44, NZ + 0.58)
    bar('ads_stalk' + s, p0, p1, 0.022, M['olive'], en, 10)
    bar('ads_arm' + s, p1, p2, 0.018, M['olive'], en, 10)
    bar('ads_probe' + s, p2, p3, 0.012, M['steel'], en, 10)
    C.box('ads_vane' + s, (0.06, 0.004, 0.08), (p2[0] - 0.02, p2[1], p2[2]), mat=M['black'], parent=en, bev=0)
    C.box('ads_vane2' + s, (0.06, 0.08, 0.004), (p2[0] - 0.02, p2[1], p2[2]), mat=M['black'], parent=en, bev=0)
# nacelles sit with the intakes just behind the mast: slide the engine group aft
ENX = -0.25
for o in en.children:
    o.location.x += ENX

# ================================================================== MAIN ROTOR
mr = P['mainRotor']
HZ = 3.62
# static: mast fairing, mast, stationary swashplate, FCR mast + Longbow radome
lathe('mast_fairing', [(0.30, 2.74), (0.27, 2.86), (0.19, 2.96), (0.15, 3.02)], M['body'], mr, seg=32, cap=False)
C.cyl('mast', 0.11, 0.80, loc=(0, 0, 3.12), mat=M['gun'], parent=mr, verts=24, bev=0)
C.cyl('swash_stationary', 0.30, 0.06, loc=(0, 0, 3.14), mat=M['olive'], parent=mr, verts=36, bev=0.012)
for k in range(3):
    a = k * 2 * PI / 3 + 0.3
    bar('swash_servo%d' % k, (0.22 * math.cos(a), 0.22 * math.sin(a), 2.88), (0.24 * math.cos(a), 0.24 * math.sin(a), 3.12),
        0.025, M['chrome'], mr, 10)
bar('swash_scissor_a', (0.24, 0.0, 2.98), (0.30, 0.0, 3.06), 0.02, M['olive'], mr, 6)
C.cyl('fcr_mast', 0.15, 0.56, loc=(0, 0, 4.04), mat=M['olive'], parent=mr, verts=28, bev=0.02)
lathe('fcr_radome', [(0.0, 4.30), (0.26, 4.30), (0.40, 4.34), (0.465, 4.42), (0.48, 4.55), (0.47, 4.68),
                     (0.43, 4.78), (0.33, 4.86), (0.18, 4.895), (0.0, 4.905)],
      M['body'], mr, seg=48, sharp=50)
C.cyl('fcr_band', 0.485, 0.05, loc=(0, 0, 4.42), mat=M['olive'], parent=mr, verts=48, bev=0.01)

spm = C.spinner('spin_main', mr, (0, 0, HZ), (0, 0, 0), 1)
C.cyl('hub_core', 0.24, 0.30, loc=(0, 0, 0), mat=M['olive'], parent=spm, verts=32, bev=0.03)
C.cyl('hub_cap', 0.17, 0.10, loc=(0, 0, 0.20), mat=M['olive'], parent=spm, verts=28, bev=0.02)
C.cyl('swash_rotating', 0.28, 0.05, loc=(0, 0, -0.42), mat=M['steel'], parent=spm, verts=36, bev=0.01)
for k in range(12):
    a = k * PI / 6
    C.cyl('hub_bolt%d' % k, 0.014, 0.03, loc=(0.20 * math.cos(a), 0.20 * math.sin(a), 0.165), mat=M['steel'],
          parent=spm, verts=8, bev=0)
for k in range(4):
    a = k * PI / 2
    arm = C.empty('mr_arm%d' % k, spm, (0, 0, 0), (0, 0, a))
    C.box('strap_pack%d' % k, (0.50, 0.26, 0.10), (0.42, 0, 0.0), mat=M['steel'], parent=arm, bev=0.02)
    C.cyl('pitch_housing%d' % k, 0.11, 0.50, loc=(0.54, 0, 0), axis='X', mat=M['olive'], parent=arm, verts=28, bev=0.02)
    C.cyl('elastomer%d' % k, 0.13, 0.08, loc=(0.30, 0, 0), axis='X', mat=M['black'], parent=arm, verts=28, bev=0.015)
    C.box('blade_cuff%d' % k, (0.34, 0.30, 0.09), (0.88, -0.04, 0), mat=M['olive'], parent=arm, bev=0.025)
    for j in (-1, 1):
        C.cyl('cuff_bolt%d%d' % (k, j), 0.022, 0.12, loc=(0.82, -0.04 + j * 0.08, 0), mat=M['steel'], parent=arm, verts=10, bev=0)
    C.box('pitch_horn%d' % k, (0.20, 0.05, 0.04), (0.42, 0.14, -0.03), mat=M['olive'], parent=arm, bev=0.01)
    bar('pitch_link%d' % k, (0.36, 0.16, -0.05), (0.27, 0.16, -0.40), 0.018, M['chrome'], arm, 10)
    bar('lag_damper%d' % k, (0.20, -0.17, 0.02), (0.70, -0.13, 0.02), 0.035, M['olive'], arm, 12)
    blade_ccw('main_blade%d' % k, 0.98, 7.315, 0.533, mat=M['blade'], parent=arm, twist=9, thick=0.105,
              tip_chord=0.30, sweep=0.17, sweep_start=0.935, droop=0.12, spans=40, n=18)
    C.box('blade_root_doubler%d' % k, (0.30, 0.50, 0.075), (1.10, -0.117, -0.004), mat=M['blade'], parent=arm, bev=0.02)

# ================================================================== TAIL ROTOR (scissor, port side of fin)
tr = P['tailRotor']
TX, TY, TZ = -8.95, 0.37, 3.27
C.sphere('tr_gearbox', 1.0, loc=(TX, 0.08, TZ + 0.02), scale=(0.30, 0.17, 0.25), mat=M['body'], parent=tr, seg=32, rings=16)
C.cyl('tr_output_housing', 0.075, 0.16, loc=(TX, 0.24, TZ), axis='Y', mat=M['olive'], parent=tr, verts=24, bev=0.01)
spt = C.spinner('spin_tail', tr, (TX, TY, TZ), (-PI / 2, 0, 0), 1)
C.cyl('tr_hub', 0.085, 0.26, loc=(0, 0, 0.05), mat=M['olive'], parent=spt, verts=24, bev=0.01)
lathe('tr_hub_cap', [(0.07, 0.0), (0.065, 0.05), (0.04, 0.09), (0.0, 0.10)], M['olive'], spt, loc=(0, 0, 0.18), seg=20)
for j, (zz, a0) in enumerate(((0.0, 0.0), (0.11, math.radians(55)))):
    st = C.empty('tr_set%d' % j, spt, (0, 0, zz), (0, 0, a0))
    C.box('tr_yoke%d' % j, (0.40, 0.09, 0.05), (0, 0, 0), mat=M['olive'], parent=st, bev=0.012)
    for b in range(2):
        ang = b * PI
        blade_ccw('tail_blade%d%d' % (j, b), 0.19, 1.395, 0.254, mat=M['blade'], parent=st, twist=8, thick=0.11,
                  spans=14, n=14, angle=ang)
        g = C.empty('tr_grip%d%d' % (j, b), st, (0, 0, 0), (0, 0, ang))
        C.box('tr_grip_box%d%d' % (j, b), (0.14, 0.10, 0.06), (0.20, 0.0, 0), mat=M['olive'], parent=g, bev=0.012)
        bar('tr_pitch_link%d%d' % (j, b), (0.17, 0.07, -0.02), (0.06, 0.07, -0.12), 0.01, M['chrome'], g, 8)

# ================================================================== STABILATOR
sb = P['stabilator']
SZ = 1.70
foil('stabilator', [
    dict(s=-1.70, le=-8.98, c=0.74, h=SZ, t=0.09),
    dict(s=-1.62, le=-8.94, c=0.82, h=SZ, t=0.11),
    dict(s=0.00, le=-8.82, c=0.98, h=SZ, t=0.12),
    dict(s=1.62, le=-8.94, c=0.82, h=SZ, t=0.11),
    dict(s=1.70, le=-8.98, c=0.74, h=SZ, t=0.09),
], span='Y', mat=M['body'], parent=sb, n=14)
C.cyl('stab_pivot', 0.07, 0.40, loc=(-9.15, 0, SZ), axis='Y', mat=M['olive'], parent=sb, verts=20, bev=0.01)
bar('stab_actuator', (-8.75, 0, 1.55), (-9.0, 0, SZ - 0.04), 0.02, M['chrome'], sb, 8)

# ================================================================== GEAR (tail-dragger)
gr = P['gear']
MW_R, MW_W = 0.29, 0.20
MW_Z = MW_R + 0.1 * MW_W
MWX = 1.45                      # main wheels; wheelbase to tail wheel ~10.6 m
for sgn, s in side_pairs():
    piv = (MWX + 0.58, sgn * 0.76, 0.99)
    axl = (MWX, sgn * 0.86, MW_Z)
    C.box('gear_pivot' + s, (0.20, 0.14, 0.12), (piv[0], piv[1], piv[2] + 0.02), mat=M['olive'], parent=gr, bev=0.02)
    bar('trailing_arm' + s, piv, axl, 0.055, M['olive'], gr, 14)
    top = (MWX - 0.18, sgn * 0.74, 1.07)
    mid = lerp(piv, axl, 0.55)
    oleo_mid = lerp(top, mid, 0.55)
    C.box('oleo_mount' + s, (0.16, 0.12, 0.10), (top[0], top[1], top[2] + 0.02), mat=M['olive'], parent=gr, bev=0.02)
    bar('oleo_cyl' + s, top, oleo_mid, 0.05, M['olive'], gr, 14)
    bar('oleo_piston' + s, oleo_mid, mid, 0.032, M['chrome'], gr, 14)
    bar('axle' + s, axl, (axl[0], sgn * 1.02, axl[2]), 0.04, M['steel'], gr, 12)
    bar('brake_line' + s, (piv[0], piv[1] + sgn * 0.05, piv[2] - 0.04), (axl[0] + 0.05, axl[1] + sgn * 0.05, axl[2] + 0.06),
        0.007, M['black'], gr, 6)
    C.wheel('main_wheel' + s, MW_R, MW_W, (MWX, sgn * 1.00, MW_Z), M['rubber'], M['olive'], parent=gr)
    C.cyl('brake_disc' + s, 0.13, 0.03, loc=(MWX, sgn * 0.89, MW_Z), axis='Y', mat=M['steel'], parent=gr, verts=24, bev=0)
    # strut wire cutter
    C.box('gear_cutter' + s, (0.16, 0.012, 0.05), (MWX + 0.35, sgn * 0.80, 0.78), rot=(0, 0.9, 0), mat=M['steel'], parent=gr, bev=0.003)

TW_R, TW_W = 0.16, 0.12
TW_Z = TW_R + 0.1 * TW_W
TWX = -9.12
C.box('tailgear_mount', (0.26, 0.20, 0.10), (-8.78, 0, 1.12), mat=M['olive'], parent=gr, bev=0.02)
bar('tailgear_leg', (-8.78, 0, 1.10), (-9.00, 0, 0.52), 0.05, M['olive'], gr, 14)
bar('tailgear_piston', (-9.00, 0, 0.52), (-9.04, 0, 0.38), 0.032, M['chrome'], gr, 12)
C.box('tailgear_fork_top', (0.12, 0.20, 0.05), (-9.05, 0, 0.36), mat=M['olive'], parent=gr, bev=0.015)
for sgn in (1, -1):
    bar('tailgear_fork%s' % ('' if sgn > 0 else '_R'), (-9.05, sgn * 0.085, 0.36), (TWX, sgn * 0.085, TW_Z), 0.022, M['olive'], gr, 10)
C.wheel('tail_wheel', TW_R, TW_W, (TWX, 0, TW_Z), M['rubber'], M['olive'], parent=gr)

C.finish('apache')
