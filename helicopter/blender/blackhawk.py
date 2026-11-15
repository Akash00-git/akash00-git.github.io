"""Sikorsky UH-60M Black Hawk (US Army) -- high-detail Blender build.

Blender space: metres, nose +X, up +Z, port (left) = +Y, wheels on Z=0.
Run:  blender -b --factory-startup --python helicopter/blender/blackhawk.py -- [--geo|--fast|--preview]
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

R = math.radians
MODEL = 'blackhawk'
C.reset()

# ----------------------------------------------------------------- key stations (metres)
XN = 7.63                         # nose tip
MAST = Vector((2.74, 0.0, 3.82))  # main rotor hub centre
MAST_TILT = R(3.0)                # shaft tilted forward
MW_X, MW_Y = 4.00, 1.36           # main wheels
TW_X = MW_X - 8.83                # tail wheel (wheelbase 8.83 m)
TR_HUB = Vector((-7.33, -0.42, 3.15))
TR_CANT = R(20.0)


def X(d):
    return XN - d


# ----------------------------------------------------------------- materials
OD = (0.074, 0.067, 0.036)   # US Army olive drab (FS 34088), linear; reads olive-brown like the reference photos
m_paint = C.paint('bh_paint', OD, rough=0.62, panel=(0.82, 0.47), panel_w=0.0035, grime=0.42, wear=0.18,
                  wear_color=(0.20, 0.21, 0.19))
m_paint_np = C.paint('bh_paint_parts', OD, rough=0.6, panel=None, grime=0.4, wear=0.22,
                     wear_color=(0.22, 0.22, 0.20))
m_hot = C.paint('bh_paint_hot', (0.046, 0.043, 0.026), rough=0.7, panel=(0.6, 0.4), grime=0.65, wear=0.2,
                wear_color=(0.2, 0.2, 0.19), soot=0.9)
m_blade = C.paint('bh_blade', (0.024, 0.025, 0.024), rough=0.5, panel=None, grime=0.15, wear=0.08,
                  wear_color=(0.25, 0.25, 0.25))
m_liner = C.simple('bh_liner', (0.085, 0.090, 0.075), 0.85)
m_floor = C.simple('bh_floor', (0.050, 0.050, 0.047), 0.75)
m_seat = C.simple('bh_seat', (0.075, 0.080, 0.058), 0.9)
m_black = C.simple('bh_black', (0.010, 0.010, 0.010), 0.55)
m_soot = C.simple('bh_soot', (0.008, 0.007, 0.006), 0.95)
m_hub = C.simple('bh_hub', (0.050, 0.052, 0.050), 0.45, 0.4)
m_steel = C.metal('bh_steel', (0.40, 0.40, 0.41), 0.28)
m_alu = C.metal('bh_alu', (0.30, 0.30, 0.31), 0.4)
m_gearpaint = C.simple('bh_gear_paint', (0.046, 0.047, 0.030), 0.55)
m_wheel = C.simple('bh_wheel_hub', (0.085, 0.086, 0.080), 0.45, 0.3)
m_gun = C.simple('bh_gun', (0.016, 0.016, 0.016), 0.4, 0.6)
m_ammo = C.simple('bh_ammo', (0.040, 0.050, 0.030), 0.7)
m_rubber = C.rubber('bh_rubber')
m_glass = C.glass('bh_glass', tint=(0.50, 0.56, 0.55), rough=0.03)
m_lens = C.simple('bh_lens', (0.004, 0.006, 0.008), 0.05, 0.0)
m_screen = C.simple('bh_mfd', (0.006, 0.012, 0.010), 0.12)
m_mark = C.simple('bh_marking', (0.010, 0.010, 0.010), 0.62)
m_beacon = C.emit('emit_beacon', (1.0, 0.05, 0.02), 10)
m_red = C.emit('emit_red', (1.0, 0.04, 0.02), 8)
m_green = C.emit('emit_green', (0.05, 1.0, 0.25), 8)
m_white = C.emit('emit_white', (1.0, 0.95, 0.85), 8)

P = {k: C.part(k) for k in ('fuselage', 'cockpit', 'sensor', 'engine', 'mainRotor', 'tailRotor',
                             'stabilator', 'gear')}
FUS, CPT, SEN, ENG, MRO, TRO, STB, GEAR = (P[k] for k in ('fuselage', 'cockpit', 'sensor', 'engine',
                                                          'mainRotor', 'tailRotor', 'stabilator', 'gear'))


# ----------------------------------------------------------------- local helpers
def update():
    bpy.context.view_layer.update()


def apply_mods(o):
    """Freeze the modifier stack into real geometry (booleans, subsurf ...)."""
    update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = o.data
    o.modifiers.clear()
    o.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def remove(o):
    me = o.data if o.type == 'MESH' else None
    bpy.data.objects.remove(o)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)


def boolean(o, cutter, op):
    m = o.modifiers.new('bool', 'BOOLEAN')
    m.operation = op
    m.operand_type = 'OBJECT'
    m.object = cutter
    m.solver = 'EXACT'
    m.use_self = True
    m.use_hole_tolerant = True
    m.material_mode = 'TRANSFER'
    return m


def displace(o, dist):
    m = o.modifiers.new('disp', 'DISPLACE')
    m.strength = dist
    m.mid_level = 0.0
    m.direction = 'NORMAL'
    return m


def solidify(o, t, offset, mat_off=0):
    m = o.modifiers.new('solid', 'SOLIDIFY')
    m.thickness = t
    m.offset = offset
    m.use_rim = True
    m.use_even_offset = True
    m.material_offset = mat_off
    m.material_offset_rim = mat_off
    return m


def flip_y(o):
    """Mirror a mesh in its local Y (used to fix C.blade leading-edge side)."""
    o.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return o


def rotor_blade(name, parent, r0, R_, chord, twist, **kw):
    """C.blade builds the leading edge on local -Y; for CCW (spin_dir=+1) rotation the blade moves
    toward +Y, so mirror it.  Positive `twist` then gives proper wash-out after the mirror."""
    o = C.blade(name, r0, R_, chord, parent=parent, twist=twist, **kw)
    flip_y(o)
    o.rotation_euler = (0, 0, 0)
    return o


def sloft(name, sts, mat=None, parent=None, seg=32, levels=2, cap=(True, True)):
    """Loft through arbitrarily oriented rings. Station keys: o (centre), u (width axis), v (height axis)
    plus C.ring keys (w, zt, zb, zc, n, nt, nb) measured along u / v from o."""
    verts, faces = [], []
    for st in sts:
        o = Vector(st['o'])
        u = Vector(st.get('u', (0, 1, 0))).normalized()
        v = Vector(st.get('v', (0, 0, 1))).normalized()
        d = dict(st)
        d['x'] = 0.0
        for (_, y, z) in C.ring(d, seg):
            verts.append(o + u * y + v * z)
    ns = len(sts)
    for i in range(ns - 1):
        a, b = i * seg, (i + 1) * seg
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((a + j, b + j, b + k, a + k))
    for idx, on in ((0, cap[0]), (ns - 1, cap[1])):
        if not on:
            continue
        ring_ = verts[idx * seg:(idx + 1) * seg]
        c = sum(ring_, Vector()) / seg
        ci = len(verts)
        verts.append(c)
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((ci, idx * seg + j, idx * seg + k))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    if levels:
        C.subsurf(o, levels)
    return o


def tube(name, pts, r, mat, parent, closed=False, res=2, caps=True):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = caps
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1.0)
    sp.use_cyclic_u = closed
    tmp = bpy.data.objects.new(name + '_tmp', cu)
    C.link(tmp)
    update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    o = bpy.data.objects.new(name, me)
    C.link(o, parent)
    me.materials.clear()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


def orient(o, direction, up=(0, 0, 1)):
    """Point local +Z of o along direction."""
    o.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
    return o


def ext_poly(name, pts2, depth, plane='XZ', offset=0.0, mat=None, parent=None, bev=0.004):
    """Flat 2D profile extruded symmetrically. plane XZ: pts (x,z), thickness along Y centred on offset."""
    n = len(pts2)
    verts = []
    for s in (-depth / 2, depth / 2):
        for (a, b) in pts2:
            if plane == 'XZ':
                verts.append((a, offset + s, b))
            elif plane == 'XY':
                verts.append((a, b, offset + s))
            else:  # YZ
                verts.append((offset + s, a, b))
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    o = C.mesh_obj(name, verts, faces, parent, mat, smooth=False)
    C._fix_normals(o)
    if bev:
        C.bevel(o, bev, 2, 30)
    return o


# ---- window prisms (planar outlines projected along a direction)
def _basis(d):
    d = Vector(d).normalized()
    ref = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    e1 = (ref - d * ref.dot(d)).normalized()
    e2 = d.cross(e1).normalized()
    return d, e1, e2


def _fillet(poly, r, n=5):
    out = []
    N = len(poly)
    for i in range(N):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % N])
        a, b = p0 - p1, p2 - p1
        rr = min(r, a.length * 0.45, b.length * 0.45)
        a.normalize()
        b.normalize()
        s, e = p1 + a * rr, p1 + b * rr
        for k in range(n + 1):
            t = k / n
            out.append((1 - t) ** 2 * s + 2 * (1 - t) * t * p1 + t * t * e)
    return out


def _area(poly):
    return sum(poly[i - 1].x * poly[i].y - poly[i].x * poly[i - 1].y for i in range(len(poly))) / 2


def _grow(poly, g):
    sg = 1 if _area(poly) > 0 else -1
    out = []
    N = len(poly)
    for i in range(N):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % N]
        e0, e1 = (p1 - p0), (p2 - p1)
        if e0.length < 1e-7 or e1.length < 1e-7:
            continue
        e0.normalize()
        e1.normalize()
        n0 = Vector((e0.y, -e0.x)) * sg
        n1 = Vector((e1.y, -e1.x)) * sg
        m = n0 + n1
        if m.length < 1e-6:
            m = n0
        m.normalize()
        out.append(p1 + m * (g / max(m.dot(n0), 0.35)))
    return out


class Win:
    def __init__(self, name, pts, d, inner=0.5, outer=0.6, r=0.06, grow=0.04, glass=True, frame=True,
                 group='cockpit', mirror=True, hole=True):
        self.name, self.pts, self.d = name, [Vector(p) for p in pts], Vector(d).normalized()
        self.inner, self.outer, self.r, self.g = inner, outer, r, grow
        self.glass, self.frame, self.group, self.mirror, self.hole = glass, frame, group, mirror, hole

    def sides(self):
        yield self.name, self.pts, self.d
        if self.mirror:
            yield (self.name + '_R', [Vector((p.x, -p.y, p.z)) for p in self.pts],
                   Vector((self.d.x, -self.d.y, self.d.z)))

    def prisms(self, grow=0.0, extra=0.0):
        out = []
        for nm, pts, d in self.sides():
            d, e1, e2 = _basis(d)
            poly = [Vector((p.dot(e1), p.dot(e2))) for p in pts]
            poly = _fillet(poly, self.r)
            if grow:
                poly = _grow(poly, grow)
            dep = sum(p.dot(d) for p in pts) / len(pts)
            out.append((poly, d, e1, e2, dep - self.inner - extra, dep + self.outer + extra))
        return out


def prism_mesh(name, prisms, mat, shift=(0, 0, 0)):
    verts, faces = [], []
    sh = Vector(shift)
    for (poly, d, e1, e2, lo, hi) in prisms:
        b = len(verts)
        N = len(poly)
        for k in (lo, hi):
            for q in poly:
                verts.append(e1 * q.x + e2 * q.y + d * k + sh)
        faces.append(tuple(b + i for i in range(N))[::-1])
        faces.append(tuple(b + N + i for i in range(N)))
        faces += [(b + i, b + (i + 1) % N, b + N + (i + 1) % N, b + N + i) for i in range(N)]
    o = C.mesh_obj(name, verts, faces, None, mat, smooth=False)
    C._fix_normals(o)
    return o


def split_material(o, idx, name, mat, parent):
    """Move faces with material index idx of o into a new object with single material mat."""
    me2 = o.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me2)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != idx], context='FACES')
    for f in bm.faces:
        f.material_index = 0
    bm.to_mesh(me2)
    bm.free()
    me2.materials.clear()
    me2.materials.append(mat)
    o2 = bpy.data.objects.new(name, me2)
    C.link(o2, parent)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == idx], context='FACES')
    bm.to_mesh(o.data)
    bm.free()
    return o2


def keep_material(o, mat):
    """Reassign every face of o to one material (drops other slots)."""
    o.data.materials.clear()
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.material_index = 0


# ================================================================= FUSELAGE HULL
# (d from nose, full width, top z, bottom z, widest z, top squareness, bottom squareness)
HULL = [
    (0.00, 0.10, 1.24, 1.12, 1.18, 2.0, 2.0),
    (0.05, 0.46, 1.36, 0.98, 1.18, 2.1, 2.1),
    (0.16, 0.83, 1.46, 0.885, 1.17, 2.2, 2.2),
    (0.34, 1.19, 1.59, 0.805, 1.16, 2.3, 2.3),
    (0.60, 1.52, 1.76, 0.73, 1.16, 2.4, 2.4),
    (0.92, 1.82, 1.94, 0.665, 1.17, 2.5, 2.6),
    (1.15, 2.00, 2.12, 0.625, 1.18, 2.6, 2.7),
    (1.40, 2.12, 2.29, 0.59, 1.19, 2.75, 2.85),
    (1.70, 2.22, 2.39, 0.55, 1.20, 2.9, 3.0),
    (2.10, 2.30, 2.435, 0.51, 1.22, 3.0, 3.2),
    (2.60, 2.35, 2.44, 0.49, 1.25, 3.1, 3.3),
    (3.20, 2.36, 2.44, 0.48, 1.25, 3.1, 3.4),
    (3.60, 2.36, 2.44, 0.48, 1.25, 3.1, 3.4),
    (5.00, 2.36, 2.44, 0.48, 1.25, 3.1, 3.4),
    (6.50, 2.36, 2.44, 0.48, 1.25, 3.1, 3.4),
    (7.60, 2.35, 2.43, 0.48, 1.25, 3.1, 3.4),
    (8.20, 2.22, 2.31, 0.488, 1.24, 3.0, 3.3),
    (8.90, 1.88, 2.09, 0.50, 1.22, 2.8, 3.1),
    (9.70, 1.46, 1.87, 0.515, 1.18, 2.6, 2.9),
    (10.60, 1.14, 1.67, 0.53, 1.12, 2.6, 2.8),
    (11.60, 0.94, 1.48, 0.55, 1.04, 2.6, 2.7),
    (12.60, 0.80, 1.34, 0.57, 0.97, 2.6, 2.7),
    (13.30, 0.66, 1.26, 0.585, 0.93, 2.5, 2.6),
    (13.90, 0.46, 1.18, 0.60, 0.90, 2.4, 2.5),
]


def hull_loft(name, mat, parent=None):
    sts = [dict(x=X(d), w=w, zt=zt, zb=zb, zc=zc, nt=nt, nb=nb) for (d, w, zt, zb, zc, nt, nb) in HULL]
    return C.loft(name, sts, mat=mat, parent=parent, seg=56, levels=2)


def hull_top(x):
    """Approximate centreline top z of the hull (for fairings)."""
    ds = XN - x
    for i in range(len(HULL) - 1):
        a, b = HULL[i], HULL[i + 1]
        if a[0] <= ds <= b[0]:
            t = (ds - a[0]) / (b[0] - a[0])
            return a[2] + (b[2] - a[2]) * t
    return HULL[-1][2]


# ---- window layout (port side; mirrored to starboard)
WS_N = Vector((0.50, 0, 0.87))      # windscreen projection normal
CORNER_N = Vector((0.30, 0.86, 0.42))
SIDE = Vector((0, 1, 0))
TOP = Vector((0, 0, 1))
WINDOWS = [
    Win('ws_centre', [(6.60, -0.20, 1.99), (6.60, 0.20, 1.99), (6.00, 0.21, 2.37), (6.00, -0.21, 2.37)],
        WS_N, inner=0.35, outer=0.5, r=0.05, grow=0.045, mirror=False),
    Win('ws_front', [(6.62, 0.28, 1.98), (6.57, 0.84, 1.92), (6.04, 0.88, 2.30), (6.00, 0.28, 2.37)],
        WS_N, inner=0.35, outer=0.5, r=0.07, grow=0.045),
    Win('ws_corner', [(6.04, 1.00, 2.28), (6.52, 0.96, 1.90), (6.47, 1.02, 1.62), (5.92, 1.14, 1.50),
                      (5.88, 1.10, 2.16)], CORNER_N, inner=0.3, outer=0.5, r=0.07, grow=0.045),
    Win('ws_chin', [(6.60, 1.0, 1.50), (6.55, 1.0, 0.98), (5.92, 1.0, 0.90), (5.90, 1.0, 1.46)],
        SIDE, inner=0.45, outer=1.2, r=0.18, grow=0.035, glass=False),
    Win('door_cpt', [(5.76, 1, 1.44), (5.76, 1, 2.18), (4.84, 1, 2.20), (4.84, 1, 1.42)],
        SIDE, inner=0.4, outer=1.2, r=0.09, grow=0.035),
    Win('overhead', [(5.52, 0.12, 2.4), (5.52, 0.70, 2.4), (5.00, 0.72, 2.4), (5.00, 0.12, 2.4)],
        TOP, inner=0.25, outer=0.6, r=0.06, grow=0.03),
    Win('gunner', [(4.42, 1, 1.36), (4.42, 1, 2.04), (3.82, 1, 2.04), (3.82, 1, 1.36)],
        SIDE, inner=0.4, outer=1.2, r=0.07, grow=0.035, glass=False, group='cabin'),
    Win('cabin_door', [(3.42, 1, 0.70), (3.42, 1, 2.02), (1.72, 1, 2.02), (1.72, 1, 0.70)],
        SIDE, inner=0.4, outer=1.2, r=0.06, grow=0.04, glass=False, group='cabin', mirror=False),
    Win('door_win_a_R', [(3.25, -1, 1.38), (3.25, -1, 1.92), (2.68, -1, 1.92), (2.68, -1, 1.38)],
        -SIDE, inner=0.4, outer=1.2, r=0.07, grow=0.03, group='cabin', mirror=False),
    Win('door_win_b_R', [(2.42, -1, 1.38), (2.42, -1, 1.92), (1.85, -1, 1.92), (1.85, -1, 1.50)],
        -SIDE, inner=0.4, outer=1.2, r=0.07, grow=0.03, group='cabin', mirror=False),
]
DOOR_SLIDE = -1.86
DOOR_PANEL = Win('door_panel', [(3.50, 1, 0.66), (3.50, 1, 2.06), (1.64, 1, 2.06), (1.64, 1, 0.66)],
                 SIDE, inner=0.4, outer=1.2, r=0.06, mirror=False)
DOOR_WINS = [Win('dw_a', [(3.25, 1, 1.38), (3.25, 1, 1.92), (2.68, 1, 1.92), (2.68, 1, 1.38)],
                 SIDE, inner=0.4, outer=1.2, r=0.07, mirror=False),
             Win('dw_b', [(2.42, 1, 1.38), (2.42, 1, 1.92), (1.85, 1, 1.92), (1.85, 1, 1.50)],
                 SIDE, inner=0.4, outer=1.2, r=0.07, mirror=False)]


def build_hull():
    hull = hull_loft('hull', m_paint, FUS)
    hull.data.materials.append(m_liner)
    solidify(hull, 0.03, -1.0, 1)
    cut = prism_mesh('cut_hull', [p for w in WINDOWS if w.hole for p in w.prisms()], m_liner)
    boolean(hull, cut, 'DIFFERENCE')
    apply_mods(hull)
    remove(cut)
    split_material(hull, 1, 'hull_liner', m_liner, FUS)
    keep_material(hull, m_paint)
    C.smooth_by_angle(hull, 40)

    for grp, part in (('cockpit', CPT), ('cabin', FUS)):
        ws = [w for w in WINDOWS if w.group == grp]
        # glass panes sit 12 mm inside the skin
        gw = [w for w in ws if w.glass]
        if gw:
            g = hull_loft('glass_' + grp, m_glass, part)
            displace(g, -0.012)
            solidify(g, 0.006, -1.0)
            cut = prism_mesh('cut_g', [p for w in gw for p in w.prisms()], m_glass)
            boolean(g, cut, 'INTERSECT')
            apply_mods(g)
            remove(cut)
            keep_material(g, m_glass)
        # raised painted frames / seals around every opening
        fw = [w for w in ws if w.frame]
        f = hull_loft('frames_' + grp, m_paint_np, part)
        solidify(f, 0.010, 1.0)
        gr = prism_mesh('cut_fg', [p for w in fw for p in w.prisms(grow=w.g)], m_paint_np)
        hole = prism_mesh('cut_fh', [p for w in fw for p in w.prisms(extra=0.05)], m_paint_np)
        boolean(f, gr, 'INTERSECT')
        boolean(f, hole, 'DIFFERENCE')
        apply_mods(f)
        remove(gr)
        remove(hole)
        keep_material(f, m_paint_np)
        C.smooth_by_angle(f, 40)

    # sliding cabin door (port side, slid aft on its rails)
    dp = hull_loft('cabin_door_L', m_paint, FUS)
    displace(dp, 0.016)
    solidify(dp, 0.028, 1.0)
    pc = prism_mesh('cut_dp', DOOR_PANEL.prisms(), m_paint)
    wc = prism_mesh('cut_dw', [p for w in DOOR_WINS for p in w.prisms(extra=0.05)], m_liner)
    boolean(dp, pc, 'INTERSECT')
    boolean(dp, wc, 'DIFFERENCE')
    apply_mods(dp)
    remove(pc)
    remove(wc)
    keep_material(dp, m_paint)
    C.smooth_by_angle(dp, 40)
    dp.location.x = DOOR_SLIDE
    dg_ = hull_loft('cabin_door_L_glass', m_glass, FUS)
    displace(dg_, 0.028)
    solidify(dg_, 0.006, 1.0)
    wc = prism_mesh('cut_dwg', [p for w in DOOR_WINS for p in w.prisms()], m_glass)
    boolean(dg_, wc, 'INTERSECT')
    apply_mods(dg_)
    remove(wc)
    keep_material(dg_, m_glass)
    dg_.location.x = DOOR_SLIDE
    return hull, dp


hull, door_L = build_hull()
# placement raycasts use an uncut copy of the skin so openings never swallow a ray
_ref = hull_loft('_hull_ref', None)
update()
BVH = BVHTree.FromObject(_ref, bpy.context.evaluated_depsgraph_get())
remove(_ref)


def hit(origin, direction):
    loc, nor, _, _ = BVH.ray_cast(Vector(origin), Vector(direction).normalized(), 20.0)
    return loc, nor


def side_pt(x, z, s=1):
    loc, nor = hit((x, s * 3.0, z), (0, -s, 0))
    if loc is None:
        return Vector((x, s * 1.1, z)), Vector((0, s, 0))
    return loc, nor


def top_pt(x, y=0.0):
    loc, nor = hit((x, y, 6.0), (0, 0, -1))
    return loc, nor


def bot_pt(x, y=0.0):
    loc, nor = hit((x, y, -1.0), (0, 0, 1))
    return loc, nor


def seam(name, xz, s, parent=FUS, r=0.0045, closed=True):
    """Dark panel/door gap following the hull surface through (x, z) side points."""
    pts = []
    xz = list(xz)
    dense = []
    n = len(xz)
    for i in range(n if closed else n - 1):
        a, b = Vector(xz[i]), Vector(xz[(i + 1) % n])
        k = max(2, int((b - a).length / 0.05))
        for j in range(k):
            dense.append(a.lerp(b, j / k))
    if not closed:
        dense.append(Vector(xz[-1]))
    for q in dense:
        p, nrm = side_pt(q.x, q.y, s)
        pts.append(p + nrm * 0.0005)
    return tube(name, pts, r, m_black, parent, closed=closed, res=1)


# ================================================================= UPPER DECK / DOGHOUSE
def build_doghouse():
    sts = []
    for (x, w, zt, nt) in [(5.02, 0.46, 2.43, 2.2), (4.65, 0.88, 2.57, 2.6), (4.15, 1.04, 2.79, 3.0),
                           (3.55, 1.10, 2.95, 3.2), (2.20, 1.12, 3.00, 3.2), (1.00, 1.12, 2.99, 3.2),
                           (0.25, 1.16, 2.90, 3.0), (-0.55, 1.10, 2.72, 2.8), (-1.30, 0.94, 2.45, 2.6),
                           (-1.95, 0.72, 2.16, 2.5), (-2.50, 0.44, 1.93, 2.4)]:
        zb = hull_top(x) - 0.30
        sts.append(dict(x=x, w=w, zt=zt, zb=zb, zc=zb + 0.25, nt=nt, nb=2.0))
    dh = C.loft('doghouse', sts, mat=m_paint, parent=FUS, seg=40, levels=2)
    # access-panel seams on the doghouse sides
    for s in (1, -1):
        for (x0, x1) in ((3.9, 3.1), (2.4, 1.3)):
            pts = [(x0, s * 0.53, 2.62), (x0, s * 0.56, 2.86), (x1, s * 0.56, 2.86), (x1, s * 0.53, 2.62)]
            tube('dh_seam', pts, 0.004, m_black, FUS, closed=True, res=1)
        # oil-cooler / ventilation grille on the aft hump
        for i in range(7):
            C.box('dh_grille', (0.32, 0.012, 0.022), (-0.15, s * 0.585, 2.55 + i * 0.045),
                  (R(-8 * s), 0, 0), m_black, FUS, bev=0)
    # mast base fairing (cuff)
    C.cyl('mast_cuff', 0.30, 0.10, (MAST.x - 0.04, 0, 3.02), mat=m_paint_np, parent=FUS, r2=0.22, verts=40)
    return dh


doghouse = build_doghouse()


# ================================================================= PYLON / TAIL
def build_pylon():
    sl = [(0.56, -5.50, -6.72, 0.20), (0.62, -5.40, -6.90, 0.44), (0.95, -5.40, -7.02, 0.50),
          (1.28, -5.62, -7.00, 0.46), (1.82, -6.10, -7.18, 0.38), (2.36, -6.58, -7.42, 0.33),
          (2.82, -6.94, -7.62, 0.30), (3.08, -7.12, -7.70, 0.27), (3.18, -7.21, -7.66, 0.16)]
    sts = []
    for (z, le, te, t) in sl:
        ch = le - te
        sts.append(dict(o=(le, 0, z), u=(0, 1, 0), v=(-1, 0, 0), w=t, zt=ch, zb=0.0, zc=0.32 * ch,
                        nt=1.7, nb=2.0))
    py = sloft('pylon', sts, m_paint, FUS, seg=36, levels=2)
    # boom drive-shaft fairing along the tail boom top
    pts = []
    for i in range(14):
        x = -1.9 - i * 0.30
        pts.append((x, 0, hull_top(x) + 0.03))
    tube('boom_shaft_cover', pts, 0.085, m_paint_np, FUS, res=3)
    # intermediate gearbox fairing at the pylon root
    C.sphere('igb_fairing', 0.26, (-5.78, 0, 1.36), (1.45, 0.75, 0.75), m_paint_np, FUS)
    # tail bumper / skid under pylon
    C.box('tail_bumper', (0.55, 0.10, 0.08), (-6.45, 0, 0.53), (0, R(-8), 0), m_paint_np, FUS, bev=0.02)
    return py


pylon = build_pylon()


# ================================================================= COCKPIT INTERIOR
def build_cockpit():
    p = CPT
    C.box('cpt_floor', (2.1, 2.0, 0.04), (5.55, 0, 0.74), mat=m_floor, parent=p, bev=0.005)
    # instrument panel + glareshield
    ip = C.box('instr_panel', (0.10, 1.80, 0.52), (6.28, 0, 1.40), (0, R(-14), 0), m_black, p, bev=0.01)
    C.box('glareshield', (0.42, 1.86, 0.06), (6.30, 0, 1.69), (0, R(6), 0), m_black, p, bev=0.02)
    for i, y in enumerate((-0.68, -0.27, 0.27, 0.68)):
        C.box('mfd%d' % i, (0.02, 0.26, 0.22), (6.22, y, 1.45), (0, R(-14), 0), m_screen, p, bev=0.003)
        C.box('mfd_bezel%d' % i, (0.025, 0.31, 0.27), (6.235, y, 1.45), (0, R(-14), 0), m_gun, p, bev=0.004)
    C.box('console', (1.05, 0.34, 0.36), (5.65, 0, 0.93), (0, R(-6), 0), m_black, p, bev=0.015)
    C.box('ovh_console', (0.55, 0.22, 0.08), (5.25, 0, 2.30), mat=m_black, parent=p, bev=0.01)
    for s in (1, -1):
        y = s * 0.55
        # armoured crew seat
        C.box('seat_pan', (0.50, 0.50, 0.10), (5.18, y, 0.98), (0, R(4), 0), m_seat, p, bev=0.03)
        C.box('seat_back', (0.10, 0.52, 0.78), (4.88, y, 1.40), (0, R(-12), 0), m_seat, p, bev=0.03)
        C.box('seat_head', (0.10, 0.30, 0.20), (4.80, y, 1.90), (0, R(-12), 0), m_seat, p, bev=0.03)
        C.box('seat_armor', (0.62, 0.05, 0.62), (5.00, y + s * 0.30, 1.22), mat=m_gun, parent=p, bev=0.02)
        C.box('seat_armor_b', (0.07, 0.64, 0.88), (4.78, y, 1.32), (0, R(-12), 0), m_gun, p, bev=0.02)
        C.box('seat_base', (0.40, 0.44, 0.24), (5.15, y, 0.82), mat=m_gun, parent=p, bev=0.01)
        # harness straps
        C.box('strap', (0.012, 0.05, 0.60), (4.95, y - 0.12, 1.42), (0, R(-12), 0), m_hub, p, bev=0)
        C.box('strap', (0.012, 0.05, 0.60), (4.95, y + 0.12, 1.42), (0, R(-12), 0), m_hub, p, bev=0)
        # cyclic, collective, pedals
        C.strut('cyclic', (5.62, y, 0.76), (5.55, y, 1.20), 0.016, m_gun, p)
        C.cyl('cyclic_grip', 0.026, 0.13, (5.545, y, 1.24), mat=m_rubber, parent=p, verts=12, bev=0)
        C.strut('collective', (5.00, y + s * 0.30, 0.95), (5.45, y + s * 0.32, 1.05), 0.018, m_gun, p)
        C.cyl('coll_grip', 0.03, 0.14, (5.46, y + s * 0.32, 1.06), axis='X', mat=m_rubber, parent=p,
              verts=12, bev=0)
        for k in (-1, 1):
            C.box('pedal', (0.04, 0.10, 0.20), (6.05, y + k * 0.15, 0.88), (0, R(-30), 0), m_gun, p, bev=0.005)
    # cockpit / cabin bulkhead with walk-through
    for s in (1, -1):
        C.box('bulkhead', (0.04, 0.62, 1.55), (4.58, s * 0.82, 1.48), mat=m_liner, parent=p, bev=0.01)
    C.box('bulkhead_top', (0.04, 1.0, 0.34), (4.58, 0, 2.12), mat=m_liner, parent=p, bev=0.01)
    # windscreen wipers
    for y in (0.62, -0.62):
        C.strut('wiper', (6.66, y, 2.0), (6.35, y * 0.85, 2.24), 0.008, m_black, p)
    # wire-strike deflector on the windscreen centre post
    for y in (0.235, -0.235):
        tube('ws_deflector', [(6.68, y, 1.99), (6.35, y, 2.22), (6.00, y, 2.39), (5.70, y, 2.455)], 0.012,
             m_steel, p)
    # bulged chin windows (lower nose side)
    for s in (1, -1):
        loc, nrm = side_pt(6.25, 1.20, s)
        g = C.sphere('chin_window', 1.0, loc - nrm * 0.02, (1, 1, 1), m_glass, p, seg=32, rings=16)
        # local Z along the skin normal, local X up, local Y fore-aft
        g.rotation_mode = 'QUATERNION'
        g.rotation_quaternion = nrm.to_track_quat('Z', 'X')
        g.scale = (0.30, 0.345, 0.055)


build_cockpit()


# ================================================================= CABIN INTERIOR + DOOR GUNS
def build_cabin():
    p = FUS
    C.box('cabin_floor', (4.9, 2.18, 0.05), (2.05, 0, 0.69), mat=m_floor, parent=p, bev=0.005)
    for i in range(10):
        C.box('tie_down', (0.03, 1.9, 0.006), (4.2 - i * 0.45, 0, 0.717), mat=m_alu, parent=p, bev=0)
    C.box('rear_bulkhead', (0.05, 2.1, 1.65), (-0.25, 0, 1.50), mat=m_liner, parent=p, bev=0.01)
    # troop seats: back-to-back row at the cabin centre + rear row facing forward
    def seat_row(x0, facing, n=4, y0=-0.78, pitch=0.52):
        for i in range(n):
            y = y0 + i * pitch
            C.box('troop_pan', (0.44, 0.44, 0.04), (x0 + facing * 0.22, y, 1.08), mat=m_seat, parent=p, bev=0.01)
            C.box('troop_back', (0.04, 0.44, 0.62), (x0 - facing * 0.01, y, 1.42), mat=m_seat, parent=p, bev=0.01)
            C.strut('troop_leg', (x0 + facing * 0.40, y + 0.18, 0.72), (x0 + facing * 0.40, y + 0.18, 1.07),
                    0.012, m_alu, p)
            C.strut('troop_leg', (x0 + facing * 0.40, y - 0.18, 0.72), (x0 + facing * 0.40, y - 0.18, 1.07),
                    0.012, m_alu, p)
        C.strut('troop_rail', (x0, y0 - 0.25, 1.75), (x0, y0 + (n - 1) * pitch + 0.25, 1.75), 0.018, m_alu, p)
        C.strut('troop_rail', (x0 + facing * 0.42, y0 - 0.25, 1.08),
                (x0 + facing * 0.42, y0 + (n - 1) * pitch + 0.25, 1.08), 0.015, m_alu, p)
    seat_row(2.55, 1)
    seat_row(2.47, -1)
    seat_row(0.0, 1)
    for y in (-0.62, 0.62):
        C.strut('stanchion', (2.51, y, 0.72), (2.51, y, 2.30), 0.025, m_alu, p)
    # gunner seats facing outboard
    for s in (1, -1):
        C.box('gunner_seat', (0.42, 0.42, 0.06), (4.1, s * 0.62, 1.05), mat=m_seat, parent=p, bev=0.01)
        C.box('gunner_back', (0.42, 0.05, 0.6), (4.1, s * 0.40, 1.38), mat=m_seat, parent=p, bev=0.01)
    # soundproofing quilt on the inner walls (kept clear of the open port door and gunner windows)
    for s in (1, -1):
        for i in range(5):
            xq = 3.95 - i * 0.80
            if s > 0 and 1.5 < xq < 3.6:
                continue
            C.box('quilt', (0.70, 0.02, 1.15), (xq, s * 1.10, 1.40), mat=m_seat, parent=p, bev=0.01)


def m240(name, loc, yaw, pitch, parent):
    e = C.empty(name, parent, loc, (0, pitch, yaw))
    C.box(name + '_recv', (0.42, 0.075, 0.13), (0, 0, 0), mat=m_gun, parent=e, bev=0.008)
    C.box(name + '_cover', (0.30, 0.08, 0.035), (0.04, 0, 0.08), mat=m_gun, parent=e, bev=0.006)
    C.cyl(name + '_barrel', 0.018, 0.62, (0.52, 0, 0.02), axis='X', mat=m_gun, parent=e, verts=12, bev=0)
    C.cyl(name + '_shroud', 0.03, 0.20, (0.30, 0, 0.02), axis='X', mat=m_gun, parent=e, verts=12, bev=0.003)
    C.cyl(name + '_flash', 0.026, 0.09, (0.86, 0, 0.02), axis='X', mat=m_gun, parent=e, verts=12, bev=0.003)
    C.cyl(name + '_gas', 0.014, 0.40, (0.42, 0, -0.035), axis='X', mat=m_gun, parent=e, verts=10, bev=0)
    C.box(name + '_sight', (0.03, 0.012, 0.06), (0.17, 0, 0.12), mat=m_gun, parent=e, bev=0)
    # spade grips + trigger
    C.box(name + '_spade', (0.04, 0.20, 0.03), (-0.25, 0, 0.0), mat=m_gun, parent=e, bev=0.005)
    for s in (1, -1):
        C.cyl(name + '_grip', 0.018, 0.14, (-0.27, s * 0.09, -0.05), mat=m_rubber, parent=e, verts=10, bev=0)
    C.box(name + '_can', (0.16, 0.10, 0.20), (0.0, 0.11, -0.12), mat=m_ammo, parent=e, bev=0.008)
    tube(name + '_belt', [(0.0, 0.08, -0.02), (0.0, 0.05, 0.03), (0.0, 0.03, 0.04)], 0.012, m_steel, e)
    # pintle arm back into the window frame
    C.box(name + '_pintle', (0.06, 0.06, 0.24), (-0.02, 0, -0.16), mat=m_gun, parent=e, bev=0.006)
    return e


build_cabin()
for s in (1, -1):
    m240('m240_' + ('L' if s > 0 else 'R'), (4.12, s * 1.23, 1.62), s * R(62), R(14), FUS)
    C.strut('pintle_post', (4.12, s * 1.05, 1.30), (4.12, s * 1.22, 1.46), 0.025, m_gun, FUS)


# ================================================================= EXTERIOR FUSELAGE DETAILS
def build_fuselage_details():
    p = FUS
    for s in (1, -1):
        # cockpit door outline, gunner panel, nose access panels
        seam('seam_cptdoor', [(5.90, 0.80), (5.90, 2.26), (4.60, 2.28), (4.60, 0.80)], s)
        seam('seam_gunner', [(4.52, 1.26), (4.52, 2.14), (3.72, 2.14), (3.72, 1.26)], s)
        seam('seam_nose', [(7.18, 0.88), (7.18, 1.40), (6.66, 1.52), (6.66, 0.80)], s)
        seam('seam_aft', [(-0.40, 0.62), (-0.40, 2.05)], s, closed=False)
        seam('seam_boom', [(-1.80, 0.60), (-1.80, 1.85)], s, closed=False)
        seam('seam_boom2', [(-4.20, 0.58), (-4.20, 1.40)], s, closed=False)
        # door handle / hinges on cockpit door
        loc, n = side_pt(4.72, 1.30, s)
        C.box('cpt_handle', (0.16, 0.025, 0.03), loc + n * 0.012, mat=m_steel, parent=p, bev=0.006)
        for z in (1.0, 1.95):
            loc, n = side_pt(5.88, z, s)
            C.box('cpt_hinge', (0.08, 0.03, 0.10), loc + n * 0.01, mat=m_paint_np, parent=p, bev=0.008)
        # kick-in steps and fold-out step
        for (x, z) in ((5.25, 0.95), (4.30, 0.98)):
            loc, n = side_pt(x, z, s)
            C.box('kick_step', (0.16, 0.03, 0.06), loc - n * 0.004, mat=m_black, parent=p, bev=0.004)
        loc, n = side_pt(5.10, 0.62, s)
        C.box('step_bar', (0.42, 0.10, 0.03), loc + n * 0.05 - Vector((0, 0, 0.03)), mat=m_alu, parent=p,
              bev=0.006)
        for dx in (-0.18, 0.18):
            C.strut('step_bracket', loc + Vector((dx, 0, 0.06)), loc + n * 0.08 + Vector((dx, 0, -0.03)), 0.012,
                    m_alu, p)
        # grab handles
        for (x0, z0, z1) in ((3.55, 1.05, 1.75), (4.52, 0.95, 1.20)):
            a, n = side_pt(x0, z0, s)
            b, _ = side_pt(x0, z1, s)
            tube('grab', [a, a + n * 0.06, b + n * 0.06, b], 0.011, m_steel, p, res=1)
        # cabin door rails (upper / lower) running aft to the slid-door stop
        top = [side_pt(x, 2.075, s)[0] + side_pt(x, 2.075, s)[1] * 0.03 for x in (3.6, 2.4, 1.2, 0.0, -0.45)]
        tube('door_rail_up', top, 0.022, m_paint_np, p, res=1)
        low = [side_pt(x, 0.64, s)[0] + side_pt(x, 0.64, s)[1] * 0.03 for x in (3.55, 2.4, 1.2, 0.0, -0.40)]
        tube('door_rail_low', low, 0.02, m_paint_np, p, res=1)
        # missile-warning sensors (CMWS) and flare dispensers
        loc, n = side_pt(7.05, 1.30, s)
        C.sphere('cmws_fwd', 0.07, loc, (1, 1, 1), m_lens, p, 16, 8)
        loc, n = side_pt(-5.05, 1.05, s)
        C.sphere('cmws_aft', 0.06, loc, (1, 1, 1), m_lens, p, 16, 8)
        loc, n = bot_pt(-1.55, s * 0.40)
        C.box('flare_disp', (0.42, 0.20, 0.10), loc + Vector((0, 0, -0.035)), mat=m_paint_np, parent=p, bev=0.01)
        # main gear attach fittings on the cabin side
        loc, n = side_pt(4.06, 1.10, s)
        C.box('mlg_fitting', (0.36, 0.10, 0.26), loc + n * 0.03, mat=m_paint_np, parent=p, bev=0.02)
        # nav light (red port / green starboard) on the upper cabin shoulder
        loc, n = side_pt(0.55, 2.15, s)
        C.box('nav_base', (0.12, 0.05, 0.07), loc + n * 0.01, mat=m_paint_np, parent=p, bev=0.01)
        C.sphere('nav_light', 0.035, loc + n * 0.04, (1.6, 1, 1), m_red if s > 0 else m_green, p, 16, 8)
        # pitot tubes on the forward roof
        loc, n = top_pt(5.42, s * 0.62)
        C.strut('pitot_mast', loc, loc + Vector((0.10, s * 0.10, 0.17)), 0.016, m_paint_np, p)
        C.strut('pitot_tube', loc + Vector((0.08, s * 0.10, 0.17)), loc + Vector((0.42, s * 0.10, 0.17)),
                0.012, m_steel, p)
    # starboard (closed) cabin door outline + handle
    seam('seam_cabdoor_R', [(3.52, 0.66), (3.52, 2.06), (1.62, 2.06), (1.62, 0.66)], -1)
    loc, n = side_pt(3.30, 1.25, -1)
    C.box('cab_handle', (0.18, 0.025, 0.035), loc - Vector((0, 0.012, 0)), mat=m_steel, parent=p, bev=0.006)
    # port door opening sill
    loc, n = side_pt(2.57, 0.72, 1)
    C.box('door_sill', (1.72, 0.08, 0.035), (2.57, 1.12, 0.70), mat=m_alu, parent=p, bev=0.006)
    # slid door: handle + rollers
    C.box('door_L_handle', (0.18, 0.025, 0.035), (3.30 + DOOR_SLIDE, 1.24, 1.25), mat=m_steel, parent=p, bev=0.006)

    # upper wire-strike cutter (roof above the windscreen) and lower cutter (belly behind nose)
    top = hull_top(5.75)
    ext_poly('wsps_upper', [(5.45, top - 0.02), (5.85, top - 0.02), (6.10, top + 0.24), (5.98, top + 0.27),
                            (5.56, top + 0.08)], 0.03, mat=m_hub, parent=p)
    ext_poly('wsps_upper_base', [(5.35, top - 0.03), (5.90, top - 0.03), (5.78, top + 0.06), (5.45, top + 0.06)],
             0.09, mat=m_paint_np, parent=p)
    ext_poly('wsps_lower', [(5.70, 0.52), (6.20, 0.52), (6.42, 0.30), (6.32, 0.28), (5.90, 0.44)], 0.03,
             mat=m_hub, parent=p)
    # antennas: VHF-FM whips, blades, towel bar, ADF loop, belly whip
    loc, n = top_pt(0.6, -0.35)
    C.strut('whip_1', loc, loc + Vector((-0.45, -0.05, 1.25)), 0.010, m_black, p, r2=0.004)
    C.cyl('whip_base_1', 0.045, 0.06, loc, mat=m_black, parent=p, verts=12)
    loc, n = top_pt(-0.9, 0.0)
    C.strut('whip_2', loc, loc + Vector((-0.55, 0.0, 0.95)), 0.009, m_black, p, r2=0.004)
    C.cyl('whip_base_2', 0.04, 0.06, loc, mat=m_black, parent=p, verts=12)
    for (x, h) in ((-3.0, 0.24), (-4.4, 0.20)):
        loc, n = top_pt(x, 0.0)
        ext_poly('blade_ant', [(x + 0.12, loc.z + 0.05), (x - 0.12, loc.z + 0.05), (x - 0.18, loc.z + h),
                               (x - 0.06, loc.z + h)], 0.018, offset=0.0, mat=m_black, parent=p)
    loc, n = top_pt(-3.7, 0.0)
    for dx in (0.0, 0.5):
        C.strut('towel_post', (loc.x + dx, 0, loc.z + 0.05), (loc.x + dx - 0.03, 0, loc.z + 0.20), 0.008, m_black, p)
    C.strut('towel_bar', (loc.x - 0.03, 0, loc.z + 0.20), (loc.x + 0.47, 0, loc.z + 0.20), 0.008, m_black, p)
    loc, n = bot_pt(0.4, 0.0)
    C.sphere('adf_loop', 0.30, loc, (1.0, 0.45, 0.10), m_black, p, 24, 10)
    loc, n = bot_pt(-2.6, 0.0)
    C.strut('belly_whip', loc, loc + Vector((-0.75, 0.0, -0.12)), 0.008, m_black, p, r2=0.004)
    loc, n = bot_pt(5.3, 0.0)
    C.sphere('belly_blade', 0.12, loc, (1.0, 0.25, 0.6), m_black, p, 16, 8)
    # anti-collision beacons (top front of doghouse, belly)
    C.cyl('beacon_base_t', 0.07, 0.05, (3.45, 0, 2.985), mat=m_paint_np, parent=p, verts=20)
    C.sphere('beacon_top', 0.062, (3.45, 0, 3.03), (1, 1, 0.9), m_beacon, p, 20, 10)
    loc, n = bot_pt(1.40, 0.0)
    C.cyl('beacon_base_b', 0.07, 0.04, loc, mat=m_paint_np, parent=p, verts=20)
    C.sphere('beacon_bot', 0.06, loc - Vector((0, 0, 0.03)), (1, 1, 0.9), m_beacon, p, 20, 10)
    # tail position light (white) on the aft tail-rotor gearbox fairing
    C.sphere('tail_light', 0.04, (TR_HUB.x - 0.47, 0, TR_HUB.z - 0.14), (1.3, 1, 1), m_white, P['tailRotor'], 16, 8)
    # tail-boom markings (low-vis black) and serial on the pylon
    for s in (1, -1):
        rot = (math.pi / 2, 0, math.pi) if s > 0 else (math.pi / 2, 0, 0)
        loc, n = side_pt(-2.55, 1.18, s)
        C.stencil('mark_army', 'U.S. ARMY', hull, loc + n * 0.02, rot, 0.30, m_mark, p)
        C.stencil('mark_serial', '20116', pylon, (-6.72, s * 0.30, 1.95), rot, 0.17, m_mark, p)
        loc, n = side_pt(4.95, 2.05, s)
        C.stencil('mark_rescue', 'RESCUE', hull, side_pt(4.10, 0.95, s)[0] + n * 0.02, rot, 0.07, m_mark, p)
        C.stencil('mark_nose', '20116', hull, side_pt(6.95, 1.05, s)[0] + side_pt(6.95, 1.05, s)[1] * 0.02,
                  rot, 0.08, m_mark, p)
    # fuel-filler / vents
    for s in (1, -1):
        loc, n = side_pt(-0.95, 1.55, s)
        C.cyl('vent', 0.06, 0.02, loc, mat=m_black, parent=p, verts=16, bev=0).rotation_euler = \
            n.to_track_quat('Z', 'Y').to_euler()


build_fuselage_details()


# ================================================================= SENSOR (nose FLIR turret)
def build_sensor():
    p = SEN
    loc, n = bot_pt(7.02, 0.0)
    C.cyl('flir_mount', 0.10, 0.10, loc - Vector((0, 0, 0.03)), mat=m_paint_np, parent=p, verts=24, bev=0.01)
    C.cyl('flir_azimuth', 0.15, 0.08, loc - Vector((0, 0, 0.10)), mat=m_paint_np, parent=p, verts=32, bev=0.012)
    c = loc - Vector((0, 0, 0.32))
    C.sphere('flir_ball', 0.19, c, (1, 1, 1), m_paint_np, p, 48, 24)
    for s in (1, -1):
        C.cyl('flir_trunnion', 0.07, 0.04, c + Vector((0, s * 0.19, 0)), axis='Y', mat=m_hub, parent=p, verts=20,
              bev=0.006)
    for (dy, dz, r) in ((0.065, 0.035, 0.05), (-0.055, 0.04, 0.038), (0.0, -0.07, 0.032)):
        C.cyl('flir_window', r, 0.02, c + Vector((0.183, dy, dz)), axis='X', mat=m_lens, parent=p, verts=24, bev=0)


build_sensor()


# ================================================================= ENGINES (T700 nacelles + HIRSS)
def build_engines():
    p = ENG
    for s in (1, -1):
        yc, zc = s * 0.80, 2.62
        sts = []
        for (x, r) in ((3.10, 0.300), (3.02, 0.335), (2.80, 0.360), (2.20, 0.372), (1.40, 0.372),
                       (0.90, 0.355), (0.62, 0.330)):
            sts.append(dict(o=(x, yc, zc), u=(0, 1, 0), v=(0, 0, 1), w=2 * r, zt=r, zb=-r, zc=0, n=2.2))
        nac = sloft('nacelle', sts, m_paint, p, seg=40, levels=2, cap=(False, True))
        # intake lip, dark duct, inlet face
        C.torus('intake_lip', 0.298, 0.032, (3.10, yc, zc), 'X', m_paint_np, p, 48, 12)
        C.cyl('intake_duct', 0.285, 0.30, (2.95, yc, zc), axis='X', mat=m_soot, parent=p, verts=40, bev=0, cap=False)
        C.cyl('inlet_face', 0.20, 0.03, (2.82, yc, zc), axis='X', mat=m_hub, parent=p, verts=32, bev=0)
        C.cyl('inlet_bullet', 0.10, 0.10, (2.86, yc, zc), axis='X', mat=m_hub, parent=p, verts=24, r2=0.03, bev=0)
        # cowling hinge line, latches, panel seams
        tube('cowl_hinge', [(3.0, yc + s * 0.25, zc + 0.255), (0.75, yc + s * 0.24, zc + 0.25)], 0.008,
             m_paint_np, p, res=1)
        for x in (2.6, 2.0, 1.4):
            tube('cowl_seam', [(x, yc + s * (0.372 * math.cos(a)), zc + 0.372 * math.sin(a)) for a in
                               [R(t) for t in range(-60, 181, 10)]], 0.004, m_black, p, res=1)
            C.box('cowl_latch', (0.08, 0.02, 0.03), (x - 0.25, yc + s * 0.372, zc - 0.02), mat=m_hub,
                  parent=p, bev=0.004)
        # HIRSS infrared suppressor: duct turning aft/outboard, flattening toward its exit
        path = [((0.66, yc, zc), 0.66, 0.62), ((0.15, s * 0.92, 2.60), 0.76, 0.50),
                ((-0.40, s * 1.12, 2.57), 0.92, 0.36), ((-0.92, s * 1.36, 2.54), 1.02, 0.25),
                ((-1.10, s * 1.45, 2.53), 1.04, 0.22)]
        hs = []
        for i, (pt, w, h) in enumerate(path):
            a = Vector(path[max(i - 1, 0)][0])
            b = Vector(path[min(i + 1, len(path) - 1)][0])
            t = (b - a).normalized()
            u = Vector((0, 0, 1)).cross(t).normalized()
            hs.append(dict(o=pt, u=u, v=(0, 0, 1), w=w, zt=h / 2, zb=-h / 2, zc=0, n=3.2))
        sloft('hirss', hs, m_hot, p, seg=40, levels=2, cap=(True, False))
        # sooty exit face slightly recessed
        e = hs[-1]
        o = Vector(e['o'])
        tdir = (Vector(path[-1][0]) - Vector(path[-2][0])).normalized()
        ex = C.box('hirss_exit', (0.03, 0.90, 0.24), o - tdir * 0.05, mat=m_soot, parent=p, bev=0)
        ex.rotation_euler = (0, 0, math.atan2(tdir.y, tdir.x))
        # louvres on HIRSS outboard top
        for i in range(5):
            C.box('hirss_louvre', (0.06, 0.40, 0.012), (-0.25 - i * 0.16, s * 1.02, 2.79 - i * 0.03),
                  (0, 0, R(-s * 18)), m_soot, p, bev=0)
    # engine/APU exhaust soot trails on the boom top are in bh_paint_hot via 'soot'


build_engines()


# ================================================================= MAIN ROTOR
def build_main_rotor():
    p = MRO
    axis = Vector((math.sin(MAST_TILT), 0, math.cos(MAST_TILT)))
    base = MAST - axis * 0.80
    C.strut('mast', base, MAST - axis * 0.08, 0.13, m_hub, p, verts=24)
    # stationary swashplate + servos
    sw = MAST - axis * 0.52
    s0 = C.cyl('swash_fixed', 0.36, 0.06, sw - axis * 0.05, mat=m_alu, parent=p, verts=40, bev=0.01)
    s0.rotation_euler = (0, MAST_TILT, 0)
    for a in (R(0), R(120), R(240)):
        q = Vector((math.cos(a) * 0.30, math.sin(a) * 0.30, 0))
        top = sw - axis * 0.08 + q
        C.strut('servo', top, Vector((top.x - 0.02, top.y, 2.98)), 0.035, m_steel, p, verts=12)
    C.strut('scissors_fixed', sw + Vector((0.0, 0.32, -0.08)), Vector((2.60, 0.30, 3.0)), 0.02, m_alu, p)
    spin = C.spinner('spin_main', p, tuple(MAST), (0, MAST_TILT, 0), 1)
    # rotating hub (in hub-local frame)
    C.cyl('hub_core', 0.22, 0.36, (0, 0, 0.0), mat=m_hub, parent=spin, verts=32, bev=0.02)
    C.cyl('hub_nut', 0.12, 0.12, (0, 0, 0.22), mat=m_steel, parent=spin, verts=20, bev=0.01)
    C.cyl('swash_rot', 0.33, 0.05, (0, 0, -0.47), mat=m_alu, parent=spin, verts=40, bev=0.008)
    for i in range(4):
        a = i * math.pi / 2
        arm = C.empty('mr_arm%d' % i, spin, (0, 0, 0), (0, 0, a))
        C.box('hub_plate', (0.55, 0.36, 0.08), (0.30, 0, 0.12), mat=m_hub, parent=arm, bev=0.02)
        C.box('hub_plate', (0.55, 0.36, 0.08), (0.30, 0, -0.12), mat=m_hub, parent=arm, bev=0.02)
        # elastomeric bearing: alternating rubber / metal laminates
        for k in range(5):
            C.cyl('elasto', 0.13 if k % 2 == 0 else 0.135, 0.035, (0.36 + k * 0.035, 0, 0), axis='X',
                  mat=m_rubber if k % 2 == 0 else m_alu, parent=arm, verts=24, bev=0.004)
        # spindle / blade cuff
        cuff = sloft('cuff', [dict(o=(0.52, 0, 0), u=(0, 1, 0), v=(0, 0, 1), w=0.20, zt=0.07, zb=-0.07, n=2.6),
                              dict(o=(0.78, 0, 0), u=(0, 1, 0), v=(0, 0, 1), w=0.26, zt=0.06, zb=-0.06, n=2.8),
                              dict(o=(1.05, 0, 0), u=(0, 1, 0), v=(0, 0, 1), w=0.42, zt=0.05, zb=-0.05, n=3.0)],
                     m_hub, arm, seg=24, levels=1)
        for k in range(3):
            C.cyl('cuff_bolt', 0.018, 0.13, (0.98, -0.12 + k * 0.12, 0), mat=m_steel, parent=arm, verts=10, bev=0)
        # lag damper on the trailing side, pitch horn / link on the leading side (+Y)
        C.strut('damper', (0.16, -0.24, 0.02), (0.82, -0.16, 0.01), 0.04, m_steel, arm, verts=14)
        C.strut('damper_rod', (0.16, -0.24, 0.02), (0.45, -0.21, 0.02), 0.046, m_hub, arm, verts=14)
        C.box('pitch_horn', (0.10, 0.22, 0.04), (0.60, 0.17, -0.06), mat=m_hub, parent=arm, bev=0.01)
        C.strut('pitch_link', (0.62, 0.26, -0.07), (0.31, 0.24, -0.45), 0.02, m_steel, arm, verts=10)
        C.box('droop_stop', (0.08, 0.10, 0.06), (0.26, 0, -0.17), mat=m_steel, parent=arm, bev=0.01)
        # blade: 0.53 m chord, -18 deg twist (wash-out), 20 deg swept tip, static droop
        b = rotor_blade('mr_blade%d' % i, arm, 0.98, 8.18, 0.53, 16.0, mat=m_blade, thick=0.095, tip_chord=0.36,
                        sweep=0.17, sweep_start=0.94, droop=0.30, anhedral=0.03, n=16, spans=48)
        b.rotation_euler = (R(7), 0, 0)
        # rotating scissors
        if i == 0:
            C.strut('scissors_rot', (0.0, -0.20, -0.20), (0.0, -0.30, -0.44), 0.02, m_alu, arm)
    # bifilar vibration absorber on top of the hub
    C.cyl('bifilar_hub', 0.13, 0.10, (0, 0, 0.29), mat=m_hub, parent=spin, verts=24, bev=0.01)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        arm = C.empty('bif_arm%d' % i, spin, (0, 0, 0), (0, 0, a))
        C.box('bif_arm', (0.42, 0.08, 0.05), (0.26, 0, 0.29), mat=m_hub, parent=arm, bev=0.012)
        C.cyl('bif_mass', 0.10, 0.09, (0.48, 0, 0.29), axis='Y', mat=m_hub, parent=arm, verts=28, bev=0.012)
        C.cyl('bif_pin', 0.025, 0.12, (0.48, 0, 0.29), axis='Y', mat=m_steel, parent=arm, verts=12, bev=0)
    return spin


build_main_rotor()


# ================================================================= TAIL ROTOR + GEARBOX
def build_tail_rotor():
    p = TRO
    a = Vector((0, -math.cos(TR_CANT), math.sin(TR_CANT)))
    g = TR_HUB - a * 0.447
    C.sphere('tgb_fairing', 1.0, (g.x - 0.05, 0.0, g.z + 0.02), (0.50, 0.21, 0.26), m_paint_np, p, 40, 20)
    C.sphere('tgb_tail', 1.0, (g.x - 0.40, 0.0, g.z - 0.05), (0.32, 0.12, 0.14), m_paint_np, p, 24, 12)
    C.strut('tr_shaft_housing', g, TR_HUB - a * 0.10, 0.11, m_paint_np, p, verts=24, r2=0.08)
    spin = C.spinner('spin_tail', p, tuple(TR_HUB), (R(90) - TR_CANT, 0, 0), 1)
    C.cyl('tr_hub', 0.085, 0.16, (0, 0, 0.0), mat=m_hub, parent=spin, verts=24, bev=0.01)
    C.cyl('tr_cap', 0.075, 0.10, (0, 0, 0.12), mat=m_hub, parent=spin, verts=20, r2=0.03, bev=0.005)
    for i in range(4):
        arm = C.empty('tr_arm%d' % i, spin, (0, 0, 0), (0, 0, i * math.pi / 2))
        C.box('tr_beam', (0.30, 0.10, 0.04), (0.16, 0, (0.025 if i % 2 else -0.025)), mat=m_hub, parent=arm,
              bev=0.01)
        C.box('tr_horn', (0.05, 0.10, 0.03), (0.20, 0.08, 0.05), mat=m_hub, parent=arm, bev=0.006)
        C.strut('tr_link', (0.20, 0.12, 0.05), (0.05, 0.10, -0.08), 0.01, m_steel, arm, verts=8)
        b = rotor_blade('tr_blade%d' % i, arm, 0.26, 1.675, 0.245, 10.0, mat=m_blade, thick=0.11, tip_chord=0.20,
                        sweep_start=0.9, n=12, spans=16)
        b.location.z = 0.025 if i % 2 else -0.025
        b.rotation_euler = (R(8), 0, 0)
    return spin


build_tail_rotor()


# ================================================================= STABILATOR
def build_stab():
    p = STB
    ch = 1.0
    le = -6.50
    half = rotor_blade('stab_L', p, 0.0, 2.19, ch, 0.0, mat=m_paint, thick=0.13, tip_chord=0.70, sweep_start=0.86,
                       n=14, spans=24)
    # after the mirror the LE sits on local +Y; Rz(-90) sends span -> -Y and LE -> +X, Rx(+4) = LE up
    half.rotation_euler = (R(4), 0, R(-90))
    half.location = (le - 0.28 * ch, 0.0, 0.98)
    C.mirror_y(half, 'stab_R', p)
    for s in (1, -1):
        C.box('stab_tipcap', (0.70, 0.03, 0.08), (le - 0.40, s * 2.19, 0.97), mat=m_paint_np, parent=p,
              bev=0.015)
        C.box('stab_hinge', (0.22, 0.10, 0.10), (le - 0.30, s * 0.27, 0.98), mat=m_paint_np, parent=p,
              bev=0.02)
    C.strut('stab_actuator', (le - 0.25, 0.0, 0.70), (le - 0.25, 0.0, 0.95), 0.03, m_steel, p)


build_stab()


# ================================================================= LANDING GEAR
def build_gear():
    p = GEAR
    wr, ww = 0.31, 0.24
    zc = wr + 0.1 * ww
    for s in (1, -1):
        wc = Vector((MW_X, s * MW_Y, zc))
        C.wheel('mlg_wheel_' + ('L' if s > 0 else 'R'), wr, ww, tuple(wc), m_rubber, m_wheel, p)
        C.cyl('mlg_brake', 0.17, 0.06, wc - Vector((0, s * 0.12, 0)), axis='Y', mat=m_steel, parent=p, verts=24)
        ax = wc - Vector((0, s * 0.17, 0))
        C.strut('mlg_axle', wc, ax, 0.055, m_steel, p, verts=16)
        # long trailing drag beam forward/inboard to the belly pivot
        piv = Vector((MW_X + 0.95, s * 0.66, 0.52))
        C.strut('mlg_drag_beam', ax, piv, 0.075, m_gearpaint, p, verts=20, r2=0.06)
        C.cyl('mlg_pivot', 0.08, 0.14, piv, axis='Y', mat=m_steel, parent=p, verts=16)
        # two-stage oleo up to the cabin-side fitting
        top, n = side_pt(MW_X + 0.06, 1.12, s)
        top = top + n * 0.10
        mid = ax.lerp(top, 0.45)
        C.strut('mlg_oleo_outer', mid, top, 0.07, m_gearpaint, p, verts=20)
        C.strut('mlg_oleo_piston', ax + Vector((0, 0, 0.04)), mid, 0.045, m_steel, p, verts=16)
        C.strut('mlg_torque_arm', ax + Vector((-0.10, 0, 0.06)), mid + Vector((-0.10, 0, -0.04)), 0.02, m_alu, p)
        C.cyl('mlg_top_pin', 0.06, 0.16, top, axis='X', mat=m_steel, parent=p, verts=14)
        tube('mlg_brake_line', [ax + Vector((0, 0, 0.05)), mid + Vector((0.06, 0, 0)), top + Vector((0.06, 0, -0.05))],
             0.007, m_black, p, res=1)
    # tail wheel: trailing fork + oleo
    twr, tww = 0.175, 0.13
    tz = twr + 0.1 * tww
    tw = Vector((TW_X, 0, tz))
    C.wheel('tlg_wheel', twr, tww, tuple(tw), m_rubber, m_wheel, p)
    loc, n = bot_pt(TW_X + 0.32, 0.0)
    crown = Vector((TW_X + 0.12, 0, 0.42))
    for s in (1, -1):
        C.strut('tlg_fork', tw + Vector((0, s * 0.09, 0)), crown + Vector((0, s * 0.09, 0)), 0.025, m_gearpaint, p)
        C.cyl('tlg_axle_end', 0.035, 0.03, tw + Vector((0, s * 0.10, 0)), axis='Y', mat=m_steel, parent=p,
              verts=12)
    C.box('tlg_crown', (0.12, 0.22, 0.06), crown, mat=m_gearpaint, parent=p, bev=0.012)
    C.strut('tlg_oleo', crown, loc + Vector((0, 0, 0.05)), 0.05, m_steel, p, verts=16)
    C.strut('tlg_oleo_outer', crown.lerp(loc, 0.45), loc + Vector((0, 0, 0.05)), 0.065, m_gearpaint, p, verts=16)
    C.strut('tlg_drag', crown + Vector((0.0, 0, 0.02)), Vector((TW_X + 0.95, 0, loc.z + 0.05)), 0.03, m_gearpaint, p)
    C.box('tlg_fitting', (0.40, 0.20, 0.10), loc + Vector((0.2, 0, 0.02)), mat=m_gearpaint, parent=p, bev=0.02)


build_gear()

C.finish(MODEL)
