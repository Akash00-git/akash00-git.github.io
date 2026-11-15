"""Mil Mi-24V 'Hind-E' gunship - high-detail Blender build for the helicopter archive.

Run:  blender -b --factory-startup --python helicopter/blender/hind.py -- [--geo | --fast | --preview]
Frame: metres, nose +X, up +Z, port (left) = +Y, main rotor mast at X=0, wheels on Z=0.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

R = math.radians
C.reset()

KEYS = ('fuselage', 'cockpit', 'sensor', 'stubWing', 'weapons', 'engine', 'mainRotor', 'tailRotor', 'gear')
P = {k: C.part(k) for k in KEYS}

# ------------------------------------------------------------------ materials
TAN = (0.205, 0.160, 0.088)
GREEN = (0.056, 0.072, 0.030)
BROWN = (0.062, 0.040, 0.022)
BLUE = (0.25, 0.42, 0.56)


def under_split(mat, under, thr=-0.24, soft=0.02):
    """Soviet scheme: light-blue lower surfaces. Inserts a world-normal driven colour switch in front
    of the paint's mottling stage so grime, wear and panel lines still apply on top."""
    nt = mat.node_tree
    m1 = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeMix' and n.blend_type == 'MULTIPLY')
    src = m1.inputs[6].links[0].from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sep.inputs[0])
    f = C._math(nt, 'SUBTRACT', thr, sep.outputs[2])
    f = C._math(nt, 'MULTIPLY', f, 0.5 / soft)
    f = C._math(nt, 'ADD', f, 0.5, True)
    col = nt.nodes.new('ShaderNodeRGB')
    col.outputs[0].default_value = C._rgb(under)
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    nt.links.new(f, mix.inputs['Factor'])
    nt.links.new(src, mix.inputs[6])
    nt.links.new(col.outputs[0], mix.inputs[7])
    nt.links.new(mix.outputs[2], m1.inputs[6])
    return mat


M_HULL = under_split(C.paint('hind_camo', TAN, camo=[GREEN, BROWN], camo_scale=0.42, rough=0.62,
                             panel=(1.05, 0.62), panel_w=0.005, grime=0.5, wear=0.28), BLUE, thr=-0.36)
M_TOP = C.paint('hind_camo_top', TAN, camo=[GREEN, BROWN], camo_scale=0.42, rough=0.62,
                panel=(1.05, 0.62), panel_w=0.005, grime=0.5, wear=0.28)
M_PODS = C.paint('hind_stores', (0.060, 0.072, 0.045), panel=None, rough=0.6, grime=0.55, wear=0.35)
M_TUBE = C.paint('hind_atgm', (0.050, 0.068, 0.040), panel=None, rough=0.55, grime=0.4, wear=0.3)
M_BLADE = C.paint('hind_blade', (0.050, 0.054, 0.046), panel=None, rough=0.5, grime=0.18, wear=0.06)
M_GEARP = C.paint('hind_gearpaint', (0.075, 0.085, 0.055), panel=None, rough=0.55, grime=0.5, wear=0.12)
M_FRAME = C.simple('hind_frame', (0.070, 0.068, 0.046), 0.55)
M_SEAM = C.simple('hind_seam', (0.012, 0.012, 0.010), 0.75)
M_DARK = C.simple('hind_black', (0.016, 0.016, 0.015), 0.65)
M_SOOT = C.simple('hind_soot', (0.010, 0.009, 0.008), 0.9)
M_INT = C.simple('hind_interior', (0.050, 0.120, 0.105), 0.7)
M_INTD = C.simple('hind_interior_dark', (0.020, 0.024, 0.022), 0.6)
M_CUSH = C.simple('hind_cushion', (0.090, 0.060, 0.035), 0.85)
M_GLASS = C.glass('hind_canopy', tint=(0.50, 0.57, 0.56), rough=0.02)
M_RADOME = C.simple('hind_radome', (0.09, 0.10, 0.09), 0.45)
M_WIN = C.simple('hind_window', (0.008, 0.011, 0.012), 0.06, 0.0)
M_LENS = C.simple('hind_lens', (0.02, 0.025, 0.03), 0.05, 0.0)
M_METAL = C.metal('hind_metal', (0.42, 0.43, 0.44), 0.38)
M_DMETAL = C.metal('hind_darkmetal', (0.12, 0.12, 0.12), 0.45)
M_CHROME = C.metal('hind_chrome', (0.75, 0.76, 0.78), 0.12)
M_GUN = C.metal('hind_gunmetal', (0.07, 0.07, 0.075), 0.4)
M_RUB = C.rubber('hind_rubber')
M_RED = C.simple('hind_star_red', (0.42, 0.012, 0.010), 0.5)
M_WHITE = C.simple('hind_star_white', (0.72, 0.72, 0.68), 0.5)
M_YEL = C.simple('hind_bort_yellow', (0.75, 0.52, 0.04), 0.5)
M_TIPR = C.simple('hind_tip_red', (0.45, 0.015, 0.012), 0.45)
M_TIPW = C.simple('hind_tip_white', (0.70, 0.70, 0.66), 0.45)
M_BEACON = C.emit('emit_beacon', (1.0, 0.05, 0.02), 10.0)
M_NAVR = C.emit('emit_red', (1.0, 0.04, 0.02), 8.0)
M_NAVG = C.emit('emit_green', (0.05, 1.0, 0.25), 8.0)
M_NAVW = C.emit('emit_white', (1.0, 0.95, 0.85), 8.0)


# ------------------------------------------------------------------ local helpers
def _fill(st):
    s = dict(st)
    s.setdefault('zc', (s['zt'] + s['zb']) / 2)
    s.setdefault('n', 2.5)
    s.setdefault('nt', s['n'])
    s.setdefault('nb', s['n'])
    s.setdefault('y', 0.0)
    return s


def interp(stations, x):
    """Linear interpolation of loft station parameters at x."""
    sts = sorted((_fill(s) for s in stations), key=lambda s: s['x'])
    if x <= sts[0]['x']:
        return dict(sts[0], x=x)
    for a, b in zip(sts, sts[1:]):
        if a['x'] <= x <= b['x']:
            u = (x - a['x']) / (b['x'] - a['x'])
            return {k: a[k] + (b[k] - a[k]) * u for k in a}
    return dict(sts[-1], x=x)


def rpt(st, t):
    """Single point of C.ring's superellipse at angle t."""
    st = _fill(st)
    c, s = math.cos(t), math.sin(t)
    e = 2.0 / (st['nt'] if s >= 0 else st['nb'])
    y = st['y'] + st['w'] / 2 * C._sp(c, e)
    zr = C._sp(s, e)
    z = st['zc'] + zr * ((st['zt'] - st['zc']) if zr >= 0 else (st['zc'] - st['zb']))
    return Vector((st['x'], y, z))


def half_width(st, z):
    st = _fill(st)
    if z >= st['zc']:
        zr, n = (z - st['zc']) / (st['zt'] - st['zc']), st['nt']
    else:
        zr, n = (st['zc'] - z) / (st['zc'] - st['zb']), st['nb']
    zr = min(1.0, max(0.0, zr))
    return st['w'] / 2 * (1 - zr ** n) ** (1.0 / n)


def tube(name, pts, r, mat=None, parent=None, seg=10, cap=True, r_end=None):
    """Swept round tube along a polyline (parallel-transport frames)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tans = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = tans[0].cross(ref).normalized()
    verts, faces = [], []
    for i, p in enumerate(pts):
        if i:
            nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
        bn = tans[i].cross(nrm)
        rr = r if r_end is None else r + (r_end - r) * i / (n - 1)
        for j in range(seg):
            a = 2 * math.pi * j / seg
            verts.append(p + (nrm * math.cos(a) + bn * math.sin(a)) * rr)
    for i in range(n - 1):
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((i * seg + j, i * seg + k, (i + 1) * seg + k, (i + 1) * seg + j))
    if cap:
        faces.append(tuple(range(seg))[::-1])
        faces.append(tuple(range((n - 1) * seg, n * seg)))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    C.smooth_by_angle(o, 50)
    return o


def foil(name, secs, mat=None, parent=None, vertical=False, n=16, sharp=40):
    """Lofted airfoil surface. secs: (x_le, y, z, chord, thickness_ratio); chord runs aft (-X),
    thickness along Z (wings) or Y (vertical=True, fins)."""
    prof = C.airfoil(n, 1.0)
    m = len(prof)
    verts, faces = [], []
    for (xl, y, z, ch, t) in secs:
        for (px, pz) in prof:
            off = pz * t * ch
            verts.append((xl - px * ch, y + off, z) if vertical else (xl - px * ch, y, z + off))
    for s in range(len(secs) - 1):
        for j in range(m):
            k = (j + 1) % m
            faces.append((s * m + j, s * m + k, (s + 1) * m + k, (s + 1) * m + j))
    faces.append(tuple(range(m))[::-1])
    faces.append(tuple(range((len(secs) - 1) * m, len(secs) * m)))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    C.smooth_by_angle(o, sharp)
    return o


def look_rot(direction):
    """Euler rotating local +Z onto direction."""
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_euler()


def cyl_between(name, p1, p2, r, mat=None, parent=None, verts=16, r2=None, bev=0.0):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    o = C.cyl(name, r, d.length, loc=(p1 + p2) / 2, mat=mat, parent=parent, verts=verts, r2=r2, bev=bev)
    o.rotation_euler = look_rot(d)
    return o


def mirror(o, parent=None):
    return C.mirror_tree(o, parent)


_bvh = {}


def bvh(obj):
    if obj.name not in _bvh:
        dg = bpy.context.evaluated_depsgraph_get()
        _bvh[obj.name] = BVHTree.FromObject(obj, dg)
    return _bvh[obj.name]


def hit(obj, origin, direction):
    loc, nrm, idx, dist = bvh(obj).ray_cast(Vector(origin), Vector(direction).normalized())
    return loc, nrm


def side_hit(obj, x, z, side):
    return hit(obj, (x, side * 4.0, z), (0, -side, 0))


def on_surface(name, obj, x, z, side, size, mat, parent, lift=0.0, bev=0.01, rot_extra=0.0):
    """Box (size: along-x, along-up, thickness) seated on a hull side, oriented to the surface normal."""
    loc, nrm = side_hit(obj, x, z, side)
    o = C.box(name, size, mat=mat, parent=parent, bev=bev)
    q = Vector((0, 0, 1)).rotation_difference(nrm)
    o.rotation_euler = q.to_euler()
    # keep the box 'x' edge along fuselage X
    o.rotation_mode = 'QUATERNION'
    xa = q @ Vector((1, 0, 0))
    tw = math.atan2(xa.cross(Vector((1, 0, 0))).dot(nrm), xa.dot(Vector((1, 0, 0))))
    q2 = Matrix.Rotation(tw + rot_extra, 4, nrm).to_quaternion() @ q
    o.rotation_quaternion = q2
    o.location = loc + nrm * (size[2] * 0.5 + lift)
    return o, loc, nrm


def strip_rect(name, target, x0, x1, z0, z1, side, mat, parent, w=0.012, step=0.05, offset=0.0025):
    """Thin panel-seam outline (door / hatch) wrapped onto the hull."""
    pts = []
    def edge(a, b):
        n = max(2, int((b - a).length / step))
        return [a.lerp(b, i / n) for i in range(n)]
    c = [Vector((x0, z0)), Vector((x1, z0)), Vector((x1, z1)), Vector((x0, z1))]
    for i in range(4):
        pts += edge(c[i], c[(i + 1) % 4])
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    verts, faces = [], []
    for p in pts:
        d = Vector((p.x - cx, p.y - cz))
        sx = 1 if d.x > 0 else -1
        sz = 1 if d.y > 0 else -1
        # inner point pulled toward centre by w on the dominant axes of the rectangle edge
        q = Vector((p.x - sx * w if abs(abs(p.x - cx) - (x1 - x0) / 2) < 1e-6 else p.x,
                    p.y - sz * w if abs(abs(p.y - cz) - (z1 - z0) / 2) < 1e-6 else p.y))
        verts.append((p.x, side * 1.5, p.y))
        verts.append((q.x, side * 1.5, q.y))
    n = len(pts)
    for i in range(n):
        k = (i + 1) % n
        f = (2 * i, 2 * k, 2 * k + 1, 2 * i + 1)
        faces.append(f if side < 0 else f[::-1])
    o = C.mesh_obj(name, verts, faces, parent, mat, smooth=False)
    sw = o.modifiers.new('wrap', 'SHRINKWRAP')
    sw.target = target
    sw.wrap_method = 'PROJECT'
    sw.use_project_y = True
    sw.use_negative_direction = True
    sw.use_positive_direction = True
    sw.wrap_mode = 'OUTSIDE_SURFACE'
    sw.offset = offset
    return o


def strip_line(name, target, pts2d, side, mat, parent, w=0.012, offset=0.0025, step=0.05):
    """Thin seam along a polyline given as (x, z) points, projected onto the hull side."""
    pts = []
    for a, b in zip(pts2d, pts2d[1:]):
        a, b = Vector(a), Vector(b)
        n = max(2, int((b - a).length / step))
        pts += [a.lerp(b, i / n) for i in range(n)]
    pts.append(Vector(pts2d[-1]))
    verts, faces = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        d = (b - a).normalized()
        nn = Vector((-d.y, d.x)) * (w / 2)
        verts.append((p.x + nn.x, side * 1.5, p.y + nn.y))
        verts.append((p.x - nn.x, side * 1.5, p.y - nn.y))
    for i in range(len(pts) - 1):
        f = (2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1)
        faces.append(f if side > 0 else f[::-1])
    o = C.mesh_obj(name, verts, faces, parent, mat, smooth=False)
    C._fix_normals(o)
    sw = o.modifiers.new('wrap', 'SHRINKWRAP')
    sw.target = target
    sw.wrap_method = 'PROJECT'
    sw.use_project_y = True
    sw.use_negative_direction = True
    sw.use_positive_direction = True
    sw.wrap_mode = 'OUTSIDE_SURFACE'
    sw.offset = offset
    return o


def subdiv_mesh(o, cuts=3):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()


def red_star(name, r, loc, side, target, parent):
    """Soviet star: red with white and thin red outline, wrapped onto the hull."""
    rot = (math.pi / 2, 0, math.pi) if side > 0 else (math.pi / 2, 0, 0)
    out = []
    for nm, rr, mat, off in (('o', r * 1.24, M_RED, 0.003), ('w', r * 1.15, M_WHITE, 0.006), ('r', r, M_RED, 0.009)):
        s = C.star_mesh('%s_%s' % (name, nm), rr, loc, rot, target, mat, parent, offset=off, inner=0.40)
        subdiv_mesh(s, 4)
        s.modifiers['wrap'].wrap_method = 'PROJECT'
        s.modifiers['wrap'].use_project_z = True
        s.modifiers['wrap'].use_negative_direction = True
        s.modifiers['wrap'].use_positive_direction = True
        out.append(s)
    return out


def text_mark(name, text, loc, side, target, mat, parent, size=0.42):
    rot = (math.pi / 2, 0, math.pi) if side > 0 else (math.pi / 2, 0, 0)
    o = C.stencil(name, text, target, loc, rot=rot, size=size, mat=mat, parent=parent, offset=0.005)
    subdiv_mesh(o, 2)
    m = o.modifiers['wrap']
    m.wrap_method = 'PROJECT'
    m.use_project_z = True
    m.use_negative_direction = True
    m.use_positive_direction = True
    return o


def ring_pts(st, sill, push=0.0, segs=36):
    """Points of a station ring above z=sill (arc over the top, +Y side first)."""
    st = _fill(st)
    if sill >= st['zc']:
        ratio = (sill - st['zc']) / (st['zt'] - st['zc'])
        e = 2.0 / st['nt']
        t0 = math.asin(min(1.0, ratio) ** (1.0 / e))
    else:
        ratio = (st['zc'] - sill) / (st['zc'] - st['zb'])
        e = 2.0 / st['nb']
        t0 = -math.asin(min(1.0, ratio) ** (1.0 / e))
    pts = []
    for i in range(segs + 1):
        t = t0 + (math.pi - 2 * t0) * i / segs
        p = rpt(st, t)
        if push:
            d = Vector((0, p.y - st['y'], p.z - st['zc']))
            p = p + d.normalized() * push
        pts.append(p)
    return pts


# ------------------------------------------------------------------ FUSELAGE
FUS = [
    dict(x=6.22, w=0.36, zt=1.40, zb=1.12, zc=1.28, n=2.2),
    dict(x=6.13, w=0.86, zt=1.55, zb=0.98, zc=1.28, nt=2.6, nb=2.3),
    dict(x=5.93, w=1.16, zt=1.64, zb=0.90, zc=1.26, nt=3.6, nb=2.5),
    dict(x=5.55, w=1.32, zt=1.67, zb=0.87, zc=1.25, nt=4.4, nb=2.6),
    dict(x=5.05, w=1.40, zt=1.68, zb=0.84, zc=1.24, nt=4.6, nb=2.7),
    dict(x=4.62, w=1.46, zt=1.70, zb=0.80, zc=1.24, nt=4.6, nb=2.8),
    dict(x=4.32, w=1.50, zt=1.98, zb=0.77, zc=1.32, nt=4.4, nb=2.9),
    dict(x=4.05, w=1.56, zt=2.23, zb=0.75, zc=1.42, nt=4.5, nb=3.0),
    dict(x=3.55, w=1.62, zt=2.24, zb=0.75, zc=1.47, nt=4.6, nb=3.1),
    dict(x=3.12, w=1.68, zt=2.28, zb=0.75, zc=1.55, nt=4.4, nb=3.2),
    dict(x=2.88, w=1.72, zt=2.84, zb=0.75, zc=1.75, nt=3.0, nb=3.2),
    dict(x=2.55, w=1.75, zt=2.95, zb=0.75, zc=1.80, nt=3.1, nb=3.3),
    dict(x=1.40, w=1.76, zt=2.96, zb=0.75, zc=1.80, nt=3.1, nb=3.4),
    dict(x=0.00, w=1.76, zt=2.97, zb=0.75, zc=1.80, nt=3.1, nb=3.4),
    dict(x=-1.40, w=1.74, zt=2.98, zb=0.77, zc=1.82, nt=3.1, nb=3.3),
    dict(x=-2.10, w=1.66, zt=3.00, zb=0.93, zc=1.90, nt=3.0, nb=3.0),
    dict(x=-2.80, w=1.50, zt=3.02, zb=1.24, zc=2.05, nt=2.9, nb=2.8),
    dict(x=-3.55, w=1.30, zt=3.05, zb=1.56, zc=2.25, nt=2.7, nb=2.6),
    dict(x=-4.35, w=1.10, zt=3.07, zb=1.80, zc=2.42, nt=2.5, nb=2.4),
    dict(x=-5.25, w=0.94, zt=3.08, zb=1.97, zc=2.52, nt=2.4, nb=2.3),
    dict(x=-6.30, w=0.80, zt=3.09, zb=2.14, zc=2.62, n=2.3),
    dict(x=-7.40, w=0.68, zt=3.10, zb=2.34, zc=2.72, n=2.2),
    dict(x=-8.55, w=0.56, zt=3.10, zb=2.52, zc=2.81, n=2.2),
    dict(x=-9.55, w=0.46, zt=3.08, zb=2.62, zc=2.85, n=2.2),
    dict(x=-10.40, w=0.36, zt=3.03, zb=2.70, zc=2.86, n=2.2),
    dict(x=-10.85, w=0.16, zt=2.96, zb=2.80, zc=2.88, n=2.0),
]
PF = P['fuselage']
hull = C.loft('hull', FUS, M_HULL, PF, seg=48, levels=2)

# central gearbox / oil-cooler fairing ("doghouse") between and behind the engines
DOG = [
    dict(x=2.62, w=0.30, zt=3.22, zb=2.80, zc=3.0, n=2.4),
    dict(x=2.40, w=0.58, zt=3.55, zb=2.80, zc=3.1, nt=2.4, nb=3),
    dict(x=1.60, w=0.86, zt=3.82, zb=2.80, zc=3.2, nt=2.6, nb=3),
    dict(x=0.60, w=0.98, zt=3.93, zb=2.80, zc=3.2, nt=2.7, nb=3),
    dict(x=-0.50, w=1.02, zt=3.92, zb=2.80, zc=3.2, nt=2.7, nb=3),
    dict(x=-1.40, w=0.98, zt=3.76, zb=2.82, zc=3.2, nt=2.7, nb=3),
    dict(x=-2.30, w=0.86, zt=3.52, zb=2.84, zc=3.2, nt=2.6, nb=3),
    dict(x=-3.30, w=0.70, zt=3.30, zb=2.86, zc=3.1, nt=2.5, nb=3),
    dict(x=-4.60, w=0.48, zt=3.14, zb=2.88, zc=3.0, n=2.4),
]
dog = C.loft('doghouse', DOG, M_HULL, PF, seg=40, levels=2)

# fan intake on the doghouse nose (oil cooler) and the rear APU exhaust
C.cyl('oilcooler_lip', 0.17, 0.08, loc=(2.50, 0, 3.30), axis='X', mat=M_HULL, parent=PF, verts=28, bev=0.01)
C.cyl('oilcooler_mesh', 0.145, 0.02, loc=(2.545, 0, 3.30), axis='X', mat=M_DARK, parent=PF, verts=28, bev=0)
for i in range(7):
    C.box('oilcooler_vane%d' % i, (0.012, 0.28, 0.012), loc=(2.552, 0, 3.18 + i * 0.04), mat=M_DMETAL, parent=PF, bev=0)
apu = C.cyl('apu_exhaust', 0.11, 0.30, loc=(-1.75, -0.32, 3.62), axis='Z', mat=M_DMETAL, parent=PF, verts=20, bev=0.01)
apu.rotation_euler = (R(25), 0, 0)
C.cyl('apu_exhaust_in', 0.085, 0.31, loc=(-1.75, -0.32, 3.63), axis='Z', mat=M_SOOT, parent=PF, verts=20, bev=0).rotation_euler = (R(25), 0, 0)
# fan grille slots on the doghouse sides
for s in (1, -1):
    for i in range(6):
        on_surface('dog_louver_%d_%d' % (i, s), dog, 1.55 - i * 0.12, 3.45, s, (0.07, 0.30, 0.02), M_DARK, PF, lift=-0.008, bev=0.004)

# Lipa (L-166V) IR jammer on top of the rear fairing
C.cyl('lipa_base', 0.16, 0.10, loc=(-2.85, 0, 3.42), mat=M_HULL, parent=PF, verts=32, bev=0.01)
C.cyl('lipa_body', 0.20, 0.34, loc=(-2.85, 0, 3.63), mat=M_DMETAL, parent=PF, verts=32, bev=0.015)
C.cyl('lipa_lens', 0.185, 0.30, loc=(-2.85, 0, 3.64), mat=M_LENS, parent=PF, verts=32, bev=0.0)
C.sphere('lipa_cap', 0.20, loc=(-2.85, 0, 3.80), scale=(1, 1, 0.35), mat=M_DMETAL, parent=PF, seg=32, rings=12)

# beacon lights (top on the rear fairing, bottom under the cabin)
C.cyl('beacon_top_base', 0.07, 0.05, loc=(-3.75, 0, 3.24), mat=M_DMETAL, parent=PF, verts=20, bev=0.005)
C.sphere('beacon_top', 0.065, loc=(-3.75, 0, 3.29), scale=(1, 1, 0.9), mat=M_BEACON, parent=PF, seg=20, rings=10)
C.cyl('beacon_bot_base', 0.07, 0.05, loc=(-0.9, 0, 0.745), mat=M_DMETAL, parent=PF, verts=20, bev=0.005)
C.sphere('beacon_bot', 0.065, loc=(-0.9, 0, 0.71), scale=(1, 1, 0.9), mat=M_BEACON, parent=PF, seg=20, rings=10)

# tail fin (swept, thick section) and horizontal stabiliser
fin = foil('fin', [(-8.05, 0.0, 2.78, 2.45, 0.13), (-8.30, 0.0, 2.98, 2.20, 0.13), (-8.95, 0.0, 3.55, 1.75, 0.13),
                   (-9.75, 0.0, 4.35, 1.20, 0.13), (-10.05, 0.0, 4.80, 0.98, 0.12)],
           M_HULL, PF, vertical=True, n=24)
C.sphere('fin_tipcap', 0.07, loc=(-10.50, 0, 4.80), scale=(6.8, 0.85, 0.35), mat=M_HULL, parent=PF, seg=24, rings=10)
stab = foil('stabiliser_L', [(-8.62, 0.15, 2.80, 0.95, 0.12), (-8.70, 0.60, 2.80, 0.89, 0.115), (-8.80, 1.10, 2.80, 0.81, 0.11),
                             (-8.98, 1.68, 2.80, 0.66, 0.10)], M_HULL, PF, n=24)
mirror(stab)
for s in (1, -1):
    C.box('stab_endcap_%d' % s, (0.62, 0.02, 0.07), loc=(-9.30, s * 1.69, 2.80), mat=M_HULL, parent=PF, bev=0.008)
# tail light at the boom end
C.sphere('tail_light', 0.045, loc=(-10.86, 0, 2.88), scale=(1.2, 1, 1), mat=M_NAVW, parent=PF, seg=16, rings=8)
# tail bumper skid (V strut)
for s in (1, -1):
    tube('skid_strut_%d' % s, [(-8.90, s * 0.16, 2.66), (-9.40, s * 0.05, 2.05)], 0.035, M_GEARP, PF, seg=10)
tube('skid_strut_rear', [(-9.70, 0, 2.70), (-9.42, 0, 2.03)], 0.032, M_GEARP, PF, seg=10)
C.box('skid_shoe', (0.32, 0.10, 0.05), loc=(-9.45, 0, 1.99), mat=M_DMETAL, parent=PF, bev=0.015)

# ASO-2V chaff/flare dispensers under the tail boom
for s in (1, -1):
    for i in range(3):
        x = -4.90 - i * 0.55
        o, loc, nrm = on_surface('aso2v_%d_%d' % (i, s), hull, x, 2.25 + i * 0.07, s, (0.42, 0.22, 0.08), M_PODS, PF, bev=0.012)
        for k in range(4):
            for j in range(2):
                p = Vector(loc) + nrm * 0.083 + Vector((-0.15 + k * 0.1, 0, -0.05 + j * 0.1))
                C.cyl('aso2v_cell_%d_%d_%d_%d' % (i, s, k, j), 0.028, 0.012, loc=p, mat=M_SOOT, parent=PF, verts=10, bev=0).rotation_euler = look_rot(nrm)

# antennas: whips on the boom, blade antennas, wire antenna fin -> fairing
for i, x in enumerate((-4.95, -5.95)):
    tube('whip_%d' % i, [(x, 0, 3.07), (x - 0.10, 0, 3.55)], 0.012, M_DARK, PF, seg=6, r_end=0.004)
    C.box('whip_base_%d' % i, (0.10, 0.05, 0.03), loc=(x, 0, 3.08), mat=M_DARK, parent=PF, bev=0.008)
C.box('blade_ant_top', (0.32, 0.02, 0.20), loc=(-6.9, 0, 3.18), rot=(0, R(-12), 0), mat=M_DARK, parent=PF, bev=0.008)
C.box('blade_ant_belly', (0.26, 0.02, 0.18), loc=(1.60, 0, 0.68), rot=(0, R(10), 0), mat=M_DARK, parent=PF, bev=0.008)
C.box('blade_ant_belly2', (0.22, 0.02, 0.16), loc=(-3.0, 0, 1.24), rot=(0, R(14), 0), mat=M_DARK, parent=PF, bev=0.008)
for s in (1, -1):
    tube('iff_rod_%d' % s, [(-1.6, s * 0.6, 0.86), (-1.75, s * 0.68, 0.62)], 0.008, M_DARK, PF, seg=6)
tube('wire_antenna', [(-9.30, 0, 4.10), (-3.10, 0, 3.86)], 0.0045, M_DARK, PF, seg=5, cap=False)
C.box('wire_mast', (0.06, 0.03, 0.42), loc=(-3.10, 0, 3.62), rot=(0, R(-10), 0), mat=M_DARK, parent=PF, bev=0.006)

# cabin windows + troop doors (split horizontally) + seams
for s in (1, -1):
    for i, x in enumerate((2.18, 1.12, -0.05, -0.70)):
        o, loc, nrm = on_surface('win_frame_%d_%d' % (i, s), hull, x, 2.30, s, (0.34, 0.36, 0.025), M_HULL, PF, bev=0.012)
        g, loc, nrm = on_surface('win_%d_%d' % (i, s), hull, x, 2.30, s, (0.27, 0.29, 0.03), M_WIN, PF, bev=0.03)
    # door: x 1.62 .. 0.62, upper half 1.62..2.62 m, lower half 0.86..1.60
    strip_rect('door_up_%d' % s, hull, 0.60, 1.62, 1.60, 2.62, s, M_SEAM, PF)
    strip_rect('door_lo_%d' % s, hull, 0.60, 1.62, 0.86, 1.58, s, M_SEAM, PF)
    for z in (1.25, 2.05):
        on_surface('door_handle_%d_%d' % (int(z * 10), s), hull, 1.48, z, s, (0.14, 0.035, 0.03), M_DMETAL, PF, bev=0.01)
    for z in (2.52, 1.70):
        on_surface('door_hinge_%d_%d' % (int(z * 10), s), hull, 1.10, z, s, (0.80, 0.03, 0.02), M_DMETAL, PF, bev=0.006)
    # access panels / hatches along the hull
    strip_rect('hatch_nose_%d' % s, hull, 4.70, 5.45, 1.05, 1.50, s, M_SEAM, PF, w=0.008)
    strip_rect('hatch_aft_%d' % s, hull, -1.70, -0.95, 1.10, 1.70, s, M_SEAM, PF, w=0.008)
    strip_rect('hatch_boom_%d' % s, hull, -5.60, -4.80, 2.55, 2.90, s, M_SEAM, PF, w=0.008)
    strip_line('seam_frame_%d' % s, hull, [(2.70, 0.80), (2.70, 2.90)], s, M_SEAM, PF, w=0.008)
    strip_line('seam_rear_%d' % s, hull, [(-1.95, 0.95), (-1.95, 2.95)], s, M_SEAM, PF, w=0.008)
    strip_line('seam_boomjoint_%d' % s, hull, [(-4.45, 1.85), (-4.45, 3.05)], s, M_SEAM, PF, w=0.010)
    # boarding steps and grab handles
    for i, (x, z) in enumerate(((1.15, 0.80), (3.60, 1.05), (3.40, 1.60), (5.20, 1.05))):
        o, loc, nrm = on_surface('step_%d_%d' % (i, s), hull, x, z, s, (0.22, 0.04, 0.10), M_DMETAL, PF, bev=0.01)
    for i, (x, z) in enumerate(((0.55, 2.1), (2.55, 2.4), (4.40, 1.62))):
        loc, nrm = side_hit(hull, x, z, s)
        tube('grab_%d_%d' % (i, s), [loc + Vector((0, 0, -0.12)), loc + nrm * 0.06 + Vector((0, 0, -0.1)),
                                     loc + nrm * 0.06 + Vector((0, 0, 0.1)), loc + Vector((0, 0, 0.12))], 0.012, M_DMETAL, PF, seg=8)
    # small vents / intakes
    for i, (x, z) in enumerate(((-2.35, 2.55), (2.35, 1.10), (-0.40, 2.75))):
        on_surface('vent_%d_%d' % (i, s), hull, x, z, s, (0.20, 0.12, 0.03), M_DARK, PF, bev=0.012)

# national markings and bort number
for s in (1, -1):
    red_star('star_boom_%d' % s, 0.30, (-6.85, s * 0.5, 2.66), s, hull, PF)
    red_star('star_fin_%d' % s, 0.24, (-9.98, s * 0.3, 3.78), s, fin, PF)
    text_mark('bort_%d' % s, '37', (3.55, s * 0.95, 1.55), s, hull, M_YEL, PF, size=0.46)

# ------------------------------------------------------------------ COCKPIT (tandem bubble canopies)
PC = P['cockpit']
GUN_CAN = [
    dict(x=6.04, w=0.80, zt=1.94, zb=1.35, zc=1.55, nt=3.4, nb=3.0),
    dict(x=5.95, w=1.02, zt=2.05, zb=1.35, zc=1.60, nt=2.4, nb=3.0),
    dict(x=5.65, w=1.20, zt=2.14, zb=1.35, zc=1.63, nt=2.2, nb=3.0),
    dict(x=5.20, w=1.26, zt=2.18, zb=1.35, zc=1.64, nt=2.2, nb=3.0),
    dict(x=4.80, w=1.22, zt=2.13, zb=1.35, zc=1.64, nt=2.2, nb=3.0),
    dict(x=4.56, w=1.08, zt=2.00, zb=1.35, zc=1.64, nt=2.2, nb=3.0),
    dict(x=4.40, w=0.86, zt=1.84, zb=1.35, zc=1.62, nt=2.2, nb=3.0),
]
PIL_CAN = [
    dict(x=4.36, w=0.92, zt=2.46, zb=1.95, zc=2.20, nt=3.4, nb=3.0),
    dict(x=4.27, w=1.12, zt=2.58, zb=1.95, zc=2.24, nt=2.4, nb=3.0),
    dict(x=4.00, w=1.26, zt=2.82, zb=1.95, zc=2.26, nt=2.2, nb=3.0),
    dict(x=3.60, w=1.30, zt=2.90, zb=1.95, zc=2.27, nt=2.2, nb=3.0),
    dict(x=3.20, w=1.28, zt=2.89, zb=1.95, zc=2.27, nt=2.2, nb=3.0),
    dict(x=2.96, w=1.14, zt=2.82, zb=1.95, zc=2.27, nt=2.2, nb=3.0),
    dict(x=2.82, w=0.90, zt=2.70, zb=1.95, zc=2.25, nt=2.2, nb=3.0),
]


def make_shear(x0, x1, k, zbase):
    def f(p):
        w = min(1.0, max(0.0, (p.x - x0) / (x1 - x0)))
        return Vector((p.x - k * w * (p.z - zbase), p.y, p.z))
    return f


SH_G = make_shear(5.55, 5.93, 0.80, 1.60)
SH_P = make_shear(3.70, 4.27, 0.60, 2.22)


def canopy(name, stations, shear, sill, sill_x, arches, parent):
    o = C.loft(name, stations, M_GLASS, parent, seg=56, levels=0)
    for v in o.data.vertices:
        v.co = shear(v.co)
    C.smooth_by_angle(o, 30)
    # frame arches
    for i, x in enumerate(arches):
        st = interp(stations, x)
        pts = [shear(p) for p in ring_pts(st, sill, push=0.006)]
        tube('%s_arch%d' % (name, i), pts, 0.024 if i == 0 else 0.018, M_FRAME, parent, seg=8)
    # sill rails
    for s in (1, -1):
        pts = []
        for j in range(25):
            x = sill_x[0] + (sill_x[1] - sill_x[0]) * j / 24
            st = interp(stations, x)
            pts.append(shear(Vector((x, s * (half_width(st, sill) + 0.006), sill))))
        tube('%s_sill_%d' % (name, s), pts, 0.028, M_FRAME, parent, seg=8)
    return o


gcan = canopy('canopy_gunner', GUN_CAN, SH_G, 1.62, (4.44, 6.02), (6.04, 5.86, 5.20, 4.50), PC)
pcan = canopy('canopy_pilot', PIL_CAN, SH_P, 2.18, (2.84, 4.34), (4.36, 4.10, 3.70, 2.92), PC)
# top spine of the pilot canopy and side door frame (starboard pilot door)
tube('pcan_spine', [SH_P(Vector((x, 0, interp(PIL_CAN, x)['zt'] + 0.006))) for x in (4.18, 3.95, 3.6, 3.2, 2.92)], 0.016, M_FRAME, PC, seg=8)
tube('gcan_spine', [SH_G(Vector((x, 0, interp(GUN_CAN, x)['zt'] + 0.006))) for x in (5.86, 5.6, 5.2, 4.8, 4.5)], 0.014, M_FRAME, PC, seg=8)
# windscreen wiper on the pilot screen, rear-view mirrors
tube('wiper', [SH_P(Vector((4.36, 0.10, 2.32))), SH_P(Vector((4.36, -0.12, 2.48)))], 0.008, M_DARK, PC, seg=6)
tube('wiper_g', [SH_G(Vector((6.03, 0.08, 1.70))), SH_G(Vector((6.03, -0.10, 1.86)))], 0.008, M_DARK, PC, seg=6)
for s in (1, -1):
    base = SH_P(Vector((4.20, s * 0.50, 2.50)))
    tube('mirror_stalk_%d' % s, [base, base + Vector((0.10, s * 0.14, 0.06))], 0.010, M_DARK, PC, seg=6)
    C.box('mirror_%d' % s, (0.03, 0.12, 0.08), loc=base + Vector((0.11, s * 0.16, 0.07)), rot=(0, 0, s * R(20)), mat=M_DMETAL, parent=PC, bev=0.008)

# cockpit tubs (turquoise Soviet interior) and crew stations
C.box('tub_gunner', (1.23, 0.92, 0.03), loc=(5.235, 0, 1.70), mat=M_INT, parent=PC, bev=0.01)
C.box('tub_pilot', (1.10, 1.00, 0.03), loc=(3.60, 0, 2.28), mat=M_INT, parent=PC, bev=0.01)


def seat(name, x, zf, parent):
    C.box(name + '_pan', (0.46, 0.46, 0.10), loc=(x, 0, zf + 0.05), mat=M_INTD, parent=parent, bev=0.02)
    C.box(name + '_cush', (0.40, 0.40, 0.06), loc=(x + 0.02, 0, zf + 0.12), mat=M_CUSH, parent=parent, bev=0.025)
    C.box(name + '_back', (0.09, 0.46, 0.70), loc=(x - 0.24, 0, zf + 0.45), rot=(0, R(-12), 0), mat=M_INTD, parent=parent, bev=0.02)
    C.box(name + '_backcush', (0.06, 0.38, 0.55), loc=(x - 0.19, 0, zf + 0.45), rot=(0, R(-12), 0), mat=M_CUSH, parent=parent, bev=0.025)
    C.box(name + '_head', (0.10, 0.30, 0.20), loc=(x - 0.33, 0, zf + 0.86), rot=(0, R(-12), 0), mat=M_INTD, parent=parent, bev=0.03)
    for s in (1, -1):
        C.box(name + '_armour_%d' % s, (0.50, 0.03, 0.55), loc=(x - 0.12, s * 0.27, zf + 0.42), mat=M_INT, parent=parent, bev=0.01)
        tube(name + '_harness_%d' % s, [(x - 0.19, s * 0.12, zf + 0.75), (x - 0.10, s * 0.08, zf + 0.45), (x - 0.02, s * 0.05, zf + 0.20)], 0.012, M_CUSH, parent, seg=6)


seat('seat_gunner', 4.95, 1.00, PC)
seat('seat_pilot', 3.40, 1.75, PC)
# gunner station: sight console with hand grips
C.box('gunner_console', (0.30, 0.62, 0.26), loc=(5.58, 0, 1.84), rot=(0, R(-20), 0), mat=M_INTD, parent=PC, bev=0.03)
C.box('gunner_sight', (0.24, 0.20, 0.18), loc=(5.46, 0, 1.94), rot=(0, R(-10), 0), mat=M_DARK, parent=PC, bev=0.03)
C.cyl('gunner_sight_eye', 0.05, 0.10, loc=(5.31, 0, 1.97), axis='X', mat=M_DMETAL, parent=PC, verts=12, bev=0.005)
for s in (1, -1):
    tube('gunner_grip_%d' % s, [(5.50, s * 0.24, 1.70), (5.44, s * 0.24, 1.90)], 0.022, M_DARK, PC, seg=8)
    C.box('gunner_sidepanel_%d' % s, (0.60, 0.05, 0.12), loc=(5.15, s * 0.40, 1.74), mat=M_INTD, parent=PC, bev=0.01)
# pilot station: instrument panel, coaming, ASP-17 gunsight, stick
C.box('pilot_panel', (0.10, 0.88, 0.30), loc=(3.96, 0, 2.42), rot=(0, R(-18), 0), mat=M_INTD, parent=PC, bev=0.02)
C.box('pilot_coaming', (0.22, 0.92, 0.06), loc=(3.92, 0, 2.56), mat=M_DARK, parent=PC, bev=0.02)
for i in range(6):
    for j in range(2):
        C.cyl('pilot_gauge_%d_%d' % (i, j), 0.035, 0.02, loc=(3.90 - j * 0.03, -0.30 + i * 0.12, 2.36 + j * 0.10),
              axis='X', mat=M_LENS, parent=PC, verts=12, bev=0).rotation_euler = (0, R(90 - 18), 0)
C.box('asp17_body', (0.16, 0.13, 0.12), loc=(3.86, 0.0, 2.64), mat=M_DARK, parent=PC, bev=0.015)
C.box('asp17_glass', (0.01, 0.12, 0.10), loc=(3.81, 0.0, 2.73), rot=(0, R(-30), 0), mat=M_LENS, parent=PC, bev=0)
tube('pilot_stick', [(3.66, 0, 2.20), (3.62, 0, 2.50)], 0.018, M_DARK, PC, seg=8)
C.box('pilot_stick_grip', (0.06, 0.05, 0.10), loc=(3.61, 0, 2.54), mat=M_DARK, parent=PC, bev=0.015)
for s in (1, -1):
    C.box('pilot_console_%d' % s, (0.70, 0.12, 0.10), loc=(3.50, s * 0.46, 2.32), mat=M_INTD, parent=PC, bev=0.01)

# ------------------------------------------------------------------ SENSOR (chin turret, guidance pods, air-data boom)
PS = P['sensor']
C.sphere('turret_ball', 0.34, loc=(5.62, 0, 0.98), scale=(1.05, 1, 0.75), mat=M_HULL, parent=PS, seg=40, rings=20)
C.cyl('turret_ring', 0.36, 0.06, loc=(5.62, 0, 1.0), mat=M_DMETAL, parent=PS, verts=40, bev=0.01)
C.box('turret_slot', (0.30, 0.09, 0.40), loc=(5.86, 0, 0.88), rot=(0, R(10), 0), mat=M_DARK, parent=PS, bev=0.02)
# YakB-12.7 four-barrel gun
gun_ax = Vector((1, 0, -0.06)).normalized()
g0 = Vector((5.80, 0, 0.82))
cyl_between('gun_body', g0 - gun_ax * 0.10, g0 + gun_ax * 0.38, 0.075, M_GUN, PS, verts=20)
cyl_between('gun_shroud', g0 + gun_ax * 0.38, g0 + gun_ax * 0.52, 0.065, M_GUN, PS, verts=20)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    off = Vector((0, math.cos(a), math.sin(a))) * 0.032
    cyl_between('gun_barrel_%d' % k, g0 + gun_ax * 0.50 + off, g0 + gun_ax * 1.02 + off, 0.016, M_GUN, PS, verts=10)
cyl_between('gun_clamp', g0 + gun_ax * 0.80, g0 + gun_ax * 0.84, 0.058, M_GUN, PS, verts=16)
cyl_between('gun_muzzle', g0 + gun_ax * 0.98, g0 + gun_ax * 1.06, 0.060, M_GUN, PS, verts=16)
C.cyl('gun_muzzle_hole', 0.045, 0.02, loc=g0 + gun_ax * 1.065, mat=M_SOOT, parent=PS, verts=12, bev=0).rotation_euler = look_rot(gun_ax)
# Raduga-F guidance/sensor pod: port chin
RAD = [dict(x=5.98, w=0.10, zt=1.03, zb=0.93, y=0.47), dict(x=5.90, w=0.30, zt=1.11, zb=0.82, y=0.47),
       dict(x=5.70, w=0.38, zt=1.16, zb=0.77, y=0.47), dict(x=5.10, w=0.40, zt=1.18, zb=0.78, y=0.47),
       dict(x=4.65, w=0.34, zt=1.18, zb=0.86, y=0.45), dict(x=4.40, w=0.16, zt=1.15, zb=1.0, y=0.42)]
C.loft('raduga_pod', RAD, M_HULL, PS, seg=28, levels=2)
C.sphere('raduga_window', 0.135, loc=(5.89, 0.47, 0.97), scale=(0.55, 1, 1), mat=M_LENS, parent=PS, seg=24, rings=12)
C.cyl('raduga_window_ring', 0.15, 0.03, loc=(5.84, 0.47, 0.97), axis='X', mat=M_DMETAL, parent=PS, verts=24, bev=0.006)
# radio-command (Raduga-Sh link) antenna pod: starboard chin
ANT = [dict(x=6.18, w=0.02, zt=1.03, zb=1.01, y=-0.50), dict(x=5.95, w=0.16, zt=1.10, zb=0.94, y=-0.50),
       dict(x=5.70, w=0.24, zt=1.14, zb=0.90, y=-0.50), dict(x=5.00, w=0.25, zt=1.15, zb=0.90, y=-0.49),
       dict(x=4.70, w=0.12, zt=1.12, zb=0.98, y=-0.47)]
C.loft('rc_antenna_pod', ANT, M_HULL, PS, seg=24, levels=2)
C.loft('rc_antenna_radome', [dict(x=6.19, w=0.02, zt=1.03, zb=1.01, y=-0.50), dict(x=6.00, w=0.15, zt=1.095, zb=0.945, y=-0.50),
                             dict(x=5.92, w=0.17, zt=1.105, zb=0.935, y=-0.50)], M_RADOME, PS, seg=24, levels=1)
# DUAS-V air data boom (starboard gunner canopy) with vanes; port pitot
d0 = SH_G(Vector((5.86, -0.38, 2.02)))
tube('duas_boom', [d0, d0 + Vector((0.55, -0.06, 0.03)), d0 + Vector((1.30, -0.12, 0.06))], 0.028, M_FRAME, PS, seg=10, r_end=0.016)
tube('duas_probe', [d0 + Vector((1.30, -0.12, 0.06)), d0 + Vector((1.58, -0.13, 0.07))], 0.010, M_METAL, PS, seg=8)
for k, rot in enumerate(((0, 0, 0), (R(90), 0, 0))):
    C.box('duas_vane_%d' % k, (0.10, 0.004, 0.09), loc=d0 + Vector((1.12, -0.11, 0.055)), rot=rot, mat=M_DARK, parent=PS, bev=0)
C.box('duas_root', (0.20, 0.10, 0.08), loc=d0 + Vector((0.05, 0.0, -0.02)), mat=M_FRAME, parent=PS, bev=0.02)
tube('pitot_port', [(6.00, 0.40, 1.50), (6.55, 0.44, 1.48)], 0.014, M_METAL, PS, seg=8, r_end=0.008)
tube('pitot_port_mast', [(5.92, 0.38, 1.50), (6.05, 0.41, 1.50)], 0.03, M_FRAME, PS, seg=8)
# landing / search lights under the nose
for k, (x, y) in enumerate(((4.85, 0.22), (4.85, -0.22))):
    C.cyl('ldg_light_house_%d' % k, 0.11, 0.08, loc=(x, y, 0.80), mat=M_DMETAL, parent=PS, verts=20, bev=0.01).rotation_euler = (0, R(-55), 0)
    C.cyl('ldg_light_lens_%d' % k, 0.085, 0.02, loc=(x + 0.035, y, 0.775), mat=M_LENS, parent=PS, verts=20, bev=0).rotation_euler = (0, R(-55), 0)
    C.cyl('ldg_light_bulb_%d' % k, 0.03, 0.025, loc=(x + 0.036, y, 0.774), mat=M_CHROME, parent=PS, verts=12, bev=0).rotation_euler = (0, R(-55), 0)

# ------------------------------------------------------------------ ENGINES (TV3-117 nacelles, PZU domes, exhausts)
PE = P['engine']
NAC = [
    dict(x=2.36, w=0.80, zt=3.73, zb=2.84, zc=3.30, nt=2.3, nb=2.6, y=0.47),
    dict(x=2.00, w=0.86, zt=3.79, zb=2.66, zc=3.28, nt=2.4, nb=3.4, y=0.48),
    dict(x=1.20, w=0.88, zt=3.82, zb=2.52, zc=3.26, nt=2.5, nb=4.0, y=0.49),
    dict(x=0.70, w=0.86, zt=3.78, zb=2.52, zc=3.24, nt=2.5, nb=4.0, y=0.50),
    dict(x=0.22, w=0.74, zt=3.66, zb=2.62, zc=3.22, nt=2.4, nb=3.4, y=0.48),
    dict(x=-0.15, w=0.48, zt=3.48, zb=2.80, zc=3.18, nt=2.2, nb=2.8, y=0.44),
]
nac = C.loft('nacelle_L', NAC, M_TOP, PE, seg=40, levels=2)
# PZU dust-protection device: drum + dome + centre bullet + annular gap
pz = Vector((2.36, 0.47, 3.30))
C.cyl('pzu_gap_L', 0.395, 0.06, loc=pz + Vector((0.02, 0, 0)), axis='X', mat=M_SOOT, parent=PE, verts=48, bev=0)
C.cyl('pzu_drum_L', 0.405, 0.46, loc=pz + Vector((0.28, 0, 0)), axis='X', mat=M_TOP, parent=PE, verts=48, bev=0.02)
C.torus('pzu_lip_L', 0.395, 0.022, loc=pz + Vector((0.51, 0, 0)), axis='X', mat=M_TOP, parent=PE, seg=48, cs=10)
C.sphere('pzu_dome_L', 0.39, loc=pz + Vector((0.51, 0, 0)), scale=(0.42, 1, 1), mat=M_TOP, parent=PE, seg=48, rings=20)
C.sphere('pzu_bullet_L', 0.11, loc=pz + Vector((0.66, 0, 0)), scale=(0.9, 1, 1), mat=M_DMETAL, parent=PE, seg=20, rings=10)
for k in range(12):
    a = 2 * math.pi * k / 12
    C.box('pzu_slot_%d_L' % k, (0.30, 0.02, 0.05), loc=pz + Vector((0.28, 0.408 * math.cos(a), 0.408 * math.sin(a))),
          rot=(a, 0, 0), mat=M_DARK, parent=PE, bev=0)
strip_rect('pzu_band_L', nac, 2.10, 2.24, 3.05, 3.55, 1, M_SEAM, PE, w=0.006)
# cowling hinge lines & latches
for k, x in enumerate((1.75, 1.15, 0.55)):
    on_surface('cowl_latch_%d_L' % k, nac, x, 3.10, 1, (0.12, 0.05, 0.02), M_DMETAL, PE, bev=0.006)
strip_line('cowl_seam_L', nac, [(2.25, 3.02), (0.05, 3.02)], 1, M_SEAM, PE, w=0.008)
strip_line('cowl_seam2_L', nac, [(1.40, 3.02), (1.40, 3.70)], 1, M_SEAM, PE, w=0.008)
# exhaust: duct turning outboard, nozzle, lip, dark interior
ex_ax = Vector((-0.42, 1.0, -0.14)).normalized()
ex_c = Vector((0.22, 0.98, 3.22))
cyl_between('exhaust_duct_L', Vector((0.55, 0.62, 3.26)), ex_c - ex_ax * 0.05, 0.31, M_TOP, PE, verts=36, r2=0.30)
cyl_between('exhaust_nozzle_L', ex_c - ex_ax * 0.06, ex_c + ex_ax * 0.10, 0.30, M_DMETAL, PE, verts=40)
lip = C.torus('exhaust_lip_L', 0.29, 0.025, loc=ex_c + ex_ax * 0.10, mat=M_DMETAL, parent=PE, seg=40, cs=10)
lip.rotation_euler = look_rot(ex_ax)
C.cyl('exhaust_hole_L', 0.27, 0.05, loc=ex_c + ex_ax * 0.08, mat=M_SOOT, parent=PE, verts=36, bev=0).rotation_euler = look_rot(ex_ax)
C.cyl('exhaust_cone_L', 0.12, 0.25, loc=ex_c, r2=0.03, mat=M_DMETAL, parent=PE, verts=20, bev=0).rotation_euler = look_rot(ex_ax)
for o in list(PE.children):
    if o.name.endswith('_L'):
        mirror(o).name = o.name[:-2] + '_R'

# ------------------------------------------------------------------ STUB WINGS (drooped, end-plates, pylons)
PW = P['stubWing']
ANH = R(12.5)
def wing_z(y):
    return 2.86 - max(0.0, y - 0.85) * math.tan(ANH)

def wing_le(y):
    return -0.15 - (y - 0.45) * 0.08

def wing_ch(y):
    return 1.55 - (y - 0.45) * 0.13

wsecs = [(wing_le(y), y, wing_z(y), wing_ch(y), 0.15 - 0.012 * (y - 0.45)) for y in (0.45, 0.85, 1.6, 2.4, 3.22)]
wing = foil('wing_L', wsecs, M_HULL, PW, n=24)
TIP_Y = 3.24
zt_ = wing_z(TIP_Y)
endp = foil('endplate_L', [(wing_le(TIP_Y) - 0.02, TIP_Y, zt_ + 0.05, wing_ch(TIP_Y) - 0.05, 0.10),
                           (wing_le(TIP_Y) - 0.10, TIP_Y, zt_ - 0.55, wing_ch(TIP_Y) - 0.20, 0.10)],
            M_HULL, PW, vertical=True, n=14)
rail_z = zt_ - 0.60
C.box('tip_rail_L', (1.50, 0.16, 0.08), loc=(wing_le(TIP_Y) - 0.62, TIP_Y, rail_z), mat=M_PODS, parent=PW, bev=0.015)
C.box('tip_rail_beam_L', (1.10, 0.06, 0.06), loc=(wing_le(TIP_Y) - 0.62, TIP_Y, rail_z + 0.06), mat=M_DMETAL, parent=PW, bev=0.01)
C.sphere('nav_L', 0.045, loc=(wing_le(TIP_Y) - 0.15, TIP_Y + 0.05, zt_ - 0.05), scale=(1.5, 0.7, 0.9), mat=M_NAVR, parent=PW, seg=16, rings=8)
C.cyl('nav_L_house', 0.05, 0.03, loc=(wing_le(TIP_Y) - 0.15, TIP_Y + 0.03, zt_ - 0.05), axis='Y', mat=M_DMETAL, parent=PW, verts=14, bev=0.004)
PY = (1.35, 2.20)
for k, y in enumerate(PY):
    zw = wing_z(y) - 0.11
    foil('pylon_%d_L' % k, [(wing_le(y) + 0.02, y, zw + 0.06, 1.05, 0.11), (wing_le(y) - 0.06, y, zw - 0.20, 0.92, 0.11)],
         M_HULL, PW, vertical=True, n=12)
    for s in (-1, 1):
        cyl_between('sway_%d_%d_L' % (k, s), (wing_le(y) - 0.38 + s * 0.28, y, zw - 0.18), (wing_le(y) - 0.38 + s * 0.30, y, zw - 0.26), 0.014, M_DMETAL, PW, verts=8)
# wing root fillet
C.loft('wing_root_fillet_L', [dict(x=0.15, w=0.10, zt=2.98, zb=2.80, y=0.80), dict(x=-0.20, w=0.30, zt=3.02, zb=2.70, y=0.86),
                              dict(x=-1.40, w=0.30, zt=2.98, zb=2.66, y=0.86), dict(x=-1.85, w=0.10, zt=2.90, zb=2.74, y=0.82)],
       M_HULL, PW, seg=24, levels=2)
for o in list(PW.children):
    if o.name.endswith('_L'):
        m = mirror(o)
        m.name = o.name[:-2] + '_R'
        if o.name == 'nav_L':
            m.data.materials.clear()
            m.data.materials.append(M_NAVG)

# ------------------------------------------------------------------ WEAPONS (UB-32 pods + 9M114 Shturm tubes)
PWP = P['weapons']


def ub32(name, y, zc, parent):
    xf, xr = 0.30, -1.38
    C.cyl(name + '_body', 0.205, xf - xr, loc=((xf + xr) / 2, y, zc), axis='X', mat=M_PODS, parent=parent, verts=40, bev=0.02)
    C.cyl(name + '_tail', 0.205, 0.40, loc=(xr - 0.20, y, zc), axis='X', r2=0.205, mat=M_PODS, parent=parent, verts=40, bev=0)
    o = C.cyl(name + '_cone', 0.205, 0.36, loc=(xr - 0.40 - 0.18, y, zc), axis='X', r2=0.10, mat=M_PODS, parent=parent, verts=40, bev=0.01)
    o.rotation_euler = (0, -math.pi / 2, 0)
    C.cyl(name + '_end', 0.09, 0.06, loc=(xr - 0.78, y, zc), axis='X', mat=M_SOOT, parent=parent, verts=20, bev=0)
    C.torus(name + '_lip', 0.195, 0.016, loc=(xf, y, zc), axis='X', mat=M_PODS, parent=parent, seg=40, cs=8)
    C.cyl(name + '_face', 0.19, 0.02, loc=(xf - 0.005, y, zc), axis='X', mat=M_DMETAL, parent=parent, verts=40, bev=0)
    holes = [(0, 0)] + [(0.062, 2 * math.pi * i / 7) for i in range(7)] + [(0.122, 2 * math.pi * i / 11 + 0.2) for i in range(11)] \
            + [(0.165, 2 * math.pi * i / 13 + 0.1) for i in range(13)]
    for i, (rr, a) in enumerate(holes):
        C.cyl('%s_tube%d' % (name, i), 0.026, 0.02, loc=(xf + 0.002, y + rr * math.cos(a), zc + rr * math.sin(a)), axis='X',
              mat=M_SOOT, parent=parent, verts=10, bev=0)
    for k, x in enumerate((-0.15, -0.95)):
        C.torus('%s_band%d' % (name, k), 0.207, 0.008, loc=(x, y, zc), axis='X', mat=M_DMETAL, parent=parent, seg=40, cs=6)
    C.box(name + '_lug', (0.9, 0.06, 0.05), loc=(-0.48, y, zc + 0.21), mat=M_DMETAL, parent=parent, bev=0.01)


for k, y in enumerate(PY):
    zc = wing_z(y) - 0.11 - 0.25 - 0.205
    ub32('ub32_%d_L' % k, y, zc, PWP)


def shturm(name, y, z, parent):
    xf, xr = 0.12, -1.71
    C.cyl(name + '_tube', 0.072, xf - xr, loc=((xf + xr) / 2, y, z), axis='X', mat=M_TUBE, parent=parent, verts=24, bev=0.008)
    for k, x in enumerate((xf - 0.03, xr + 0.03, -0.55, -1.10)):
        C.torus('%s_ring%d' % (name, k), 0.074, 0.008, loc=(x, y, z), axis='X', mat=M_DARK if k < 2 else M_TUBE, parent=parent, seg=24, cs=6)
    C.cyl(name + '_cap', 0.064, 0.02, loc=(xf + 0.002, y, z), axis='X', mat=M_DARK, parent=parent, verts=24, bev=0)
    C.cyl(name + '_rcap', 0.064, 0.02, loc=(xr - 0.002, y, z), axis='X', mat=M_SOOT, parent=parent, verts=24, bev=0)


for k, dy in enumerate((-0.09, 0.09)):
    shturm('shturm_%d_L' % k, TIP_Y + dy, rail_z - 0.115, PWP)
for o in list(PWP.children):
    if o.name.endswith('_L'):
        mirror(o).name = o.name[:-2] + '_R'

# ------------------------------------------------------------------ MAIN ROTOR
PM = P['mainRotor']
TILT = R(4.5)
HUB = Vector((0.0 + 0.48 * math.sin(TILT), 0, 4.43))
mast_frame = C.empty('mast_static', PM, (0, 0, 3.95), (0, TILT, 0))
C.cyl('mast_fairing', 0.30, 0.12, loc=(0, 0, 0.0), mat=M_HULL, parent=mast_frame, verts=36, bev=0.02)
C.cyl('mast_lower', 0.13, 0.30, loc=(0, 0, 0.12), mat=M_DMETAL, parent=mast_frame, verts=24, bev=0.01)
C.cyl('swash_static', 0.40, 0.06, loc=(0, 0, 0.17), mat=M_METAL, parent=mast_frame, verts=36, bev=0.01)
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.4
    tube('servo_rod_%d' % k, [(0.36 * math.cos(a), 0.36 * math.sin(a), -0.02), (0.36 * math.cos(a), 0.36 * math.sin(a), 0.16)], 0.022, M_CHROME, mast_frame, seg=8)
tube('scissor_static', [(0.0, 0.18, 0.05), (0.0, 0.30, 0.13)], 0.018, M_DMETAL, mast_frame, seg=6)

sp = C.spinner('spin_main', PM, HUB, (0, TILT, 0), spin_dir=-1)
C.cyl('mast_upper', 0.12, 0.40, loc=(0, 0, -0.20), mat=M_DMETAL, parent=sp, verts=24, bev=0.01)
C.cyl('swash_rot', 0.36, 0.05, loc=(0, 0, -0.27), mat=M_METAL, parent=sp, verts=36, bev=0.01)
C.cyl('hub_body', 0.30, 0.26, loc=(0, 0, 0.0), mat=M_DMETAL, parent=sp, verts=40, bev=0.03)
C.cyl('hub_flange', 0.34, 0.05, loc=(0, 0, -0.13), mat=M_METAL, parent=sp, verts=40, bev=0.01)
C.cyl('hub_top', 0.14, 0.18, loc=(0, 0, 0.21), mat=M_PODS, parent=sp, verts=32, bev=0.02)
C.sphere('hub_dome', 0.15, loc=(0, 0, 0.30), scale=(1, 1, 0.75), mat=M_PODS, parent=sp, seg=32, rings=12)
NB = 5
for i in range(NB):
    a = 2 * math.pi * i / NB
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-math.sin(a), math.cos(a), 0))   # direction of travel is -t (clockwise from above)
    C.box('hinge_yoke_%d' % i, (0.42, 0.26, 0.20), loc=d * 0.46, rot=(0, 0, a), mat=M_DMETAL, parent=sp, bev=0.03)
    C.cyl('hinge_pin_%d' % i, 0.05, 0.32, loc=d * 0.58, rot=(math.pi / 2, 0, a), mat=M_METAL, parent=sp, verts=12, bev=0.005)
    c = C.cyl('blade_sleeve_%d' % i, 0.11, 0.55, loc=d * 0.92, rot=(0, math.pi / 2, a), mat=M_DMETAL, parent=sp, verts=24, bev=0.015)
    C.cyl('sleeve_collar_%d' % i, 0.125, 0.06, loc=d * 0.70, rot=(0, math.pi / 2, a), mat=M_METAL, parent=sp, verts=24, bev=0.008)
    # hydraulic lag damper (trailing side)
    cyl_between('lag_damper_%d' % i, d * 0.30 + t * 0.20 + Vector((0, 0, 0.06)), d * 0.98 + t * 0.12 + Vector((0, 0, 0.06)), 0.045, M_CHROME, sp, verts=12)
    cyl_between('lag_damper_body_%d' % i, d * 0.30 + t * 0.20 + Vector((0, 0, 0.06)), d * 0.62 + t * 0.17 + Vector((0, 0, 0.06)), 0.058, M_DMETAL, sp, verts=12)
    # pitch horn and pitch link (leading side)
    horn = d * 0.80 - t * 0.20 + Vector((0, 0, -0.08))
    C.box('pitch_horn_%d' % i, (0.10, 0.22, 0.05), loc=d * 0.80 - t * 0.12 + Vector((0, 0, -0.07)), rot=(0, 0, a), mat=M_DMETAL, parent=sp, bev=0.01)
    cyl_between('pitch_link_%d' % i, horn, d * 0.34 - t * 0.18 + Vector((0, 0, -0.26)), 0.020, M_CHROME, sp, verts=8)
    # blade root fitting + blade
    C.box('blade_root_%d' % i, (0.40, 0.30, 0.12), loc=d * 1.32, rot=(0, 0, a), mat=M_DMETAL, parent=sp, bev=0.02)
    b = C.blade('blade_%d' % i, 1.30, 8.65, 0.58, mat=M_BLADE, parent=sp, twist=8.0, thick=0.11, droop=0.42, angle=a, n=14, spans=30)
    b.rotation_euler = (R(-3.0), 0, a)
    # trim tab and tip cap
    tab = C.box('blade_tab_%d' % i, (0.45, 0.07, 0.006), loc=(6.30, 0.58 * 0.72 + 0.03, -0.42 * ((6.30 - 1.30) / 7.35) ** 2), mat=M_BLADE, parent=b, bev=0)
    C.box('blade_tip_%d' % i, (0.03, 0.56, 0.05), loc=(8.66, 0.58 * 0.22, -0.42), mat=M_DMETAL, parent=b, bev=0.01)

# ------------------------------------------------------------------ TAIL ROTOR (port side of the fin)
PT = P['tailRotor']
TR = Vector((-10.38, 0.40, 4.52))
C.sphere('tr_gearbox', 0.22, loc=(-10.40, 0.05, 4.55), scale=(1.4, 0.7, 1.0), mat=M_TOP, parent=PT, seg=28, rings=14)
C.cyl('tr_output', 0.13, 0.26, loc=(-10.38, 0.22, 4.52), axis='Y', mat=M_DMETAL, parent=PT, verts=24, bev=0.01)
C.cyl('tr_gearbox_r', 0.16, 0.12, loc=(-10.40, -0.10, 4.55), axis='Y', mat=M_TOP, parent=PT, verts=24, bev=0.02)
spt = C.spinner('spin_tail', PT, TR, (-math.pi / 2, 0, 0), spin_dir=-1)
C.cyl('tr_hub', 0.13, 0.18, loc=(0, 0, 0.0), mat=M_DMETAL, parent=spt, verts=24, bev=0.015)
C.sphere('tr_cap', 0.10, loc=(0, 0, 0.10), scale=(1, 1, 0.7), mat=M_DMETAL, parent=spt, seg=20, rings=10)
for i in range(3):
    a = 2 * math.pi * i / 3 + math.pi / 6
    d = Vector((math.cos(a), math.sin(a), 0))
    C.cyl('tr_sleeve_%d' % i, 0.055, 0.22, loc=d * 0.20, rot=(0, math.pi / 2, a), mat=M_DMETAL, parent=spt, verts=16, bev=0.008)
    cyl_between('tr_pitchlink_%d' % i, d * 0.18 + Vector((-d.y, d.x, 0)) * 0.08 + Vector((0, 0, -0.06)), Vector((0, 0, -0.16)) + d * 0.06, 0.012, M_CHROME, spt, verts=6)
    for nm, r0, r1, mat in (('', 0.30, 1.56, M_BLADE), ('_w', 1.56, 1.76, M_TIPW), ('_r', 1.76, 1.955, M_TIPR)):
        bb = C.blade('tr_blade%s_%d' % (nm, i), r0, r1, 0.26, mat=mat, parent=spt, twist=0.0, thick=0.10, angle=a, n=12, spans=6 if nm else 12)
        bb.rotation_euler = (R(-6), 0, a)

# ------------------------------------------------------------------ GEAR
PG = P['gear']
# main-gear sponson fairings (retracted wheel housings)
SPON = [dict(x=0.10, w=0.12, zt=1.30, zb=0.95, y=0.80), dict(x=-0.30, w=0.40, zt=1.50, zb=0.84, y=0.86),
        dict(x=-1.40, w=0.46, zt=1.55, zb=0.86, y=0.88), dict(x=-2.30, w=0.40, zt=1.58, zb=1.06, y=0.82),
        dict(x=-2.90, w=0.12, zt=1.62, zb=1.40, y=0.72)]
spon = C.loft('sponson_L', SPON, M_HULL, PG, seg=28, levels=2)
WR, WW = 0.34, 0.24      # main wheel 720 x 320 class
AX = Vector((-0.42, 1.50, WR + 0.1 * WW))
C.wheel('mainwheel_L', WR, WW, AX, M_RUB, M_GEARP, PG)
C.cyl('mainaxle_L', 0.045, 0.32, loc=AX + Vector((0, -0.16, 0)), axis='Y', mat=M_METAL, parent=PG, verts=12, bev=0)
pivot = Vector((-0.10, 1.00, 1.18))
tube('main_arm_L', [pivot, AX + Vector((0, -0.20, 0.02))], 0.060, M_GEARP, PG, seg=14)
oleo_top = Vector((-0.85, 1.02, 1.62))
mid = AX + Vector((0, -0.16, 0.05)) + (oleo_top - AX - Vector((0, -0.16, 0.05))) * 0.5
cyl_between('main_oleo_cyl_L', mid, oleo_top, 0.070, M_GEARP, PG, verts=18)
cyl_between('main_oleo_rod_L', AX + Vector((0, -0.16, 0.05)), mid, 0.045, M_CHROME, PG, verts=14)
tube('main_brace_L', [Vector((-1.10, 0.95, 1.10)), AX + Vector((0, -0.18, 0.06))], 0.035, M_GEARP, PG, seg=10)
C.box('main_fitting_L', (0.30, 0.10, 0.18), loc=(-0.85, 0.93, 1.64), mat=M_DMETAL, parent=PG, bev=0.02)
C.box('main_pivot_L', (0.24, 0.12, 0.16), loc=pivot, mat=M_DMETAL, parent=PG, bev=0.02)
tube('brake_line_L', [AX + Vector((0, -0.12, 0.1)), pivot + Vector((0, 0, -0.05))], 0.008, M_DARK, PG, seg=6)
for o in list(PG.children):
    if o.name.endswith('_L'):
        mirror(o).name = o.name[:-2] + '_R'
# nose gear: twin wheels on a raked oleo, bay doors
NWR, NWW = 0.23, 0.18
NAX = Vector((4.02, 0, NWR + 0.1 * NWW))
for s in (1, -1):
    C.wheel('nosewheel_%d' % s, NWR, NWW, NAX + Vector((0, s * 0.17, 0)), M_RUB, M_GEARP, PG)
C.cyl('nose_axle', 0.035, 0.38, loc=NAX, axis='Y', mat=M_METAL, parent=PG, verts=12, bev=0)
ntop = Vector((4.18, 0, 1.05))
nmid = NAX + (ntop - NAX) * 0.45
cyl_between('nose_oleo_rod', NAX + Vector((0, 0, 0.03)), nmid, 0.042, M_CHROME, PG, verts=14)
cyl_between('nose_oleo_cyl', nmid, ntop, 0.062, M_GEARP, PG, verts=16)
C.box('nose_fork', (0.12, 0.20, 0.10), loc=NAX + Vector((0.02, 0, 0.06)), mat=M_GEARP, parent=PG, bev=0.02)
tube('nose_drag', [Vector((3.55, 0, 0.92)), nmid + Vector((0, 0, 0.05))], 0.03, M_GEARP, PG, seg=10)
tube('nose_torque', [NAX + Vector((-0.08, 0, 0.12)), nmid + Vector((-0.10, 0, 0.05)), nmid + Vector((0, 0, 0.08))], 0.014, M_DMETAL, PG, seg=6)
for s in (1, -1):
    C.box('nose_door_%d' % s, (0.80, 0.02, 0.26), loc=(4.05, s * 0.24, 0.66), rot=(R(-s * 8), 0, 0), mat=M_HULL, parent=PG, bev=0.006)

C.finish('hind')
