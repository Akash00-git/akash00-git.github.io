"""Boeing CH-47F Chinook (US Army) -- high-detail model for the helicopter archive.

Blender space: metres, nose +X, up +Z, port (left) = +Y, wheels on Z=0.
Fuselage 15.9 m (nose x=+7.95 .. tail x=-7.95), hubs at x=+/-5.95 (11.9 m apart),
rotor diameter 18.29 m -> 30.1 m overall with rotors turning.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R = math.radians
C.reset()

# ------------------------------------------------------------------ materials
M = dict(
    body=C.paint('ch_body', (0.072, 0.067, 0.037), panel=(0.62, 0.47), panel_w=0.0032, rough=0.6,
                 grime=0.42, wear=0.18),
    pylon=C.paint('ch_pylon', (0.070, 0.065, 0.036), panel=(0.55, 0.42), panel_w=0.0032, rough=0.6,
                  grime=0.5, wear=0.2),
    gearp=C.paint('ch_gearpaint', (0.060, 0.056, 0.032), panel=None, rivets=False, rough=0.55,
                  grime=0.6, wear=0.06),
    blade=C.paint('ch_blade', (0.019, 0.020, 0.019), panel=None, rivets=False, rough=0.62,
                  grime=0.12, wear=0.04),
    hub=C.paint('ch_hubpaint', (0.022, 0.023, 0.022), panel=None, rivets=False, rough=0.5,
                grime=0.55, wear=0.05),
    metal=C.metal('ch_metal', (0.52, 0.52, 0.54), 0.34),
    steel=C.metal('ch_steel_dark', (0.16, 0.16, 0.17), 0.45),
    chrome=C.metal('ch_chrome', (0.82, 0.82, 0.84), 0.12),
    exhaust=C.metal('ch_exhaust', (0.42, 0.31, 0.23), 0.4),
    le=C.metal('ch_blade_le', (0.38, 0.38, 0.39), 0.42),
    soot=C.simple('ch_soot', (0.011, 0.010, 0.009), 0.92),
    black=C.simple('ch_black', (0.014, 0.014, 0.015), 0.7),
    walk=C.simple('ch_walkway', (0.026, 0.029, 0.023), 0.97),
    trim=C.paint('ch_trim', (0.068, 0.063, 0.035), panel=None, rivets=False, rough=0.58, grime=0.3,
                 wear=0.03),
    rubber=C.rubber('ch_rubber'),
    glass=C.glass('ch_glass', tint=(0.52, 0.6, 0.58), rough=0.03),
    glass_dark=C.glass('ch_glass_dark', tint=(0.2, 0.24, 0.24), rough=0.05),
    interior=C.simple('ch_interior', (0.055, 0.058, 0.058), 0.75),
    seat=C.simple('ch_seat', (0.035, 0.04, 0.03), 0.85),
    display=C.simple('ch_display', (0.008, 0.01, 0.011), 0.12),
    stencil=C.simple('ch_stencil', (0.009, 0.009, 0.008), 0.65),
    sensor=C.simple('ch_sensor', (0.03, 0.03, 0.035), 0.15, 0.3),
    beacon=C.emit('emit_beacon', (1.0, 0.04, 0.02), 10.0),
    red=C.emit('emit_red', (1.0, 0.03, 0.02), 8.0),
    green=C.emit('emit_green', (0.02, 1.0, 0.15), 8.0),
    white=C.emit('emit_white', (1.0, 0.95, 0.85), 8.0),
)

KEYS = ('fuselage', 'cockpit', 'frontPylon', 'rearPylon', 'engine', 'ramp', 'sponson', 'gear',
        'frontRotor', 'rearRotor')
P = {k: C.part(k) for k in KEYS}

NOSE_X, TAIL_X = 7.95, -7.95
HUB_F = Vector((5.95, 0.0, 4.75))
HUB_R = Vector((-5.95, 0.0, 5.42))
TILT_F, TILT_R = R(6.0), R(3.0)


# ------------------------------------------------------------------ local helpers
def realize(o):
    """Apply modifiers in place (used for the hull so faces can be split off as glass)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    mats = list(o.data.materials)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    old = o.data
    o.modifiers.clear()
    o.data = me
    if not me.materials:
        for m in mats:
            me.materials.append(m)
    bpy.data.meshes.remove(old)
    return o


def bvh_of(o):
    mw = o.matrix_world
    vs = [mw @ v.co for v in o.data.vertices]
    return BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in o.data.polygons])


def tloft(name, stations, mat, parent, seg=48, levels=2):
    """C.loft with an extra per-station 'taper': the section narrows linearly above its widest
    line by that fraction at the top (trapezoid pylons with flat sloping sides)."""
    verts, faces = [], []
    for s in stations:
        zc = s.get('zc', (s['zt'] + s['zb']) / 2)
        tp = s.get('taper', 0.0)
        yo = s.get('y', 0.0)
        for (x, y, z) in C.ring(s, seg):
            k = max(0.0, (z - zc) / max(1e-6, s['zt'] - zc))
            verts.append((x, yo + (y - yo) * (1.0 - tp * k), z))
    ns = len(stations)
    for i in range(ns - 1):
        a, b = i * seg, (i + 1) * seg
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((a + j, b + j, b + k, a + k))
    for idx in (0, ns - 1):
        ring_ = list(range(idx * seg, idx * seg + seg))
        faces.append(tuple(ring_[::-1]) if idx == 0 else tuple(ring_))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    if levels:
        C.subsurf(o, levels)
    return o


DIRS = {'L': ((0, 12, 0), (0, -1, 0)), 'R': ((0, -12, 0), (0, 1, 0)),
        'F': ((30, 0, 0), (-1, 0, 0)), 'U': ((0, 0, -10), (0, 0, 1)), 'D': ((0, 0, 30), (0, 0, -1))}
XC = 6.55          # axis of the cylindrical 'C' projection used for the wrap-around cockpit glazing
KC = 0.021         # 'C' coordinates are azimuth-degrees * KC (~ metres of arc on the nose)


def to3(mode, a, b):
    """2D projection coords -> ray origin + direction. 'C': a = azimuth (deg, +Y = port) around a
    vertical axis at x=XC, b = height; the ray runs outward from inside the nose."""
    if mode == 'C':
        t = math.radians(a / KC)
        return Vector((XC, 0, b)), Vector((math.cos(t), math.sin(t), 0))
    o, d = DIRS[mode]
    if mode in 'LR':
        return Vector((a, o[1], b)), Vector(d)
    if mode == 'F':
        return Vector((o[0], a, b)), Vector(d)
    return Vector((a, b, o[2])), Vector(d)


def hit(bv, mode, a, b):
    """First hull hit for a projection point; normal returned pointing out of the hull."""
    org, d = to3(mode, a, b)
    loc, nrm, idx, dist = bv.ray_cast(org, d)
    if loc is None:
        return None, None
    if mode == 'C':
        if nrm.dot(d) < 0:
            nrm = -nrm
    elif nrm.dot(d) > 0:
        nrm = -nrm
    return loc, nrm


def inpoly(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def fillet(poly, r, n=5):
    out = []
    N = len(poly)
    for i in range(N):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % N])
        d1, d2 = p0 - p1, p2 - p1
        l1, l2 = d1.length, d2.length
        d1.normalize()
        d2.normalize()
        rr = min(r, l1 * 0.45, l2 * 0.45)
        a, b = p1 + d1 * rr, p1 + d2 * rr
        for k in range(n + 1):
            t = k / n
            q = (1 - t) ** 2 * a + 2 * (1 - t) * t * p1 + t * t * b
            out.append((q.x, q.y))
    return out


def densify(poly, step=0.03, closed=True):
    out = []
    N = len(poly)
    for i in range(N if closed else N - 1):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % N])
        k = max(1, int((b - a).length / step))
        for j in range(k):
            q = a.lerp(b, j / k)
            out.append((q.x, q.y))
    if not closed:
        out.append(tuple(poly[-1]))
    return out


def tube(name, pts, r, mat, parent, nrms=None, sides=8, closed=False, flat=1.0):
    """Sweep an (optionally flattened) round section along a polyline. nrms = surface normals
    give a stable frame (flat<1 squashes the section along the normal)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    verts, faces = [], []
    prev = None
    for i, p in enumerate(pts):
        if closed:
            a, b = pts[i - 1], pts[(i + 1) % n]
        else:
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        t = (b - a).normalized()
        if nrms is not None:
            nv = Vector(nrms[i])
            nv = (nv - t * nv.dot(t)).normalized()
        elif prev is None:
            up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            nv = t.cross(up).normalized()
        else:
            nv = (prev - t * prev.dot(t)).normalized()
        prev = nv
        bn = t.cross(nv)
        for k in range(sides):
            a_ = 2 * math.pi * (k + 0.5) / sides
            verts.append(p + nv * (math.cos(a_) * r * flat) + bn * (math.sin(a_) * r))
    m = n if closed else n - 1
    for i in range(m):
        j = (i + 1) % n
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((i * sides + k, j * sides + k, j * sides + k2, i * sides + k2))
    if not closed:
        faces.append(tuple(range(sides))[::-1])
        faces.append(tuple(range((n - 1) * sides, n * sides)))
    o = C.mesh_obj(name, verts, faces, parent, mat)
    C._fix_normals(o)
    C.smooth_by_angle(o, 60)
    return o


def frame_on(bv, mode, poly, name, r, mat, parent, lift=0.004, flat=0.55, step=0.03):
    pts, nrms = [], []
    for (a, b) in densify(poly, step):
        loc, nrm = hit(bv, mode, a, b)
        if loc is None:
            continue
        pts.append(loc + nrm * lift)
        nrms.append(nrm)
    if len(pts) < 3:
        return None
    return tube(name, pts, r, mat, parent, nrms=nrms, closed=True, flat=flat)


def line_on(bv, mode, pts2, name, r, mat, parent, lift=0.004, flat=0.55, step=0.03):
    pts, nrms = [], []
    for (a, b) in densify(pts2, step, closed=False):
        loc, nrm = hit(bv, mode, a, b)
        if loc is None:
            continue
        pts.append(loc + nrm * lift)
        nrms.append(nrm)
    if len(pts) < 2:
        return None
    return tube(name, pts, r, mat, parent, nrms=nrms, closed=False, flat=flat)


def split_faces(src, pred, name, mat, parent):
    """Move faces of `src` that satisfy pred(center, normal) into a new object."""
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.faces.ensure_lookup_table()
    sel = {f.index for f in bm.faces if pred(f.calc_center_median(), f.normal)}
    if not sel:
        bm.free()
        return None
    bm2 = bm.copy()
    bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in sel], context='FACES')
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in sel], context='FACES')
    bm.to_mesh(src.data)
    bm.free()
    me = bpy.data.meshes.new(name)
    bm2.to_mesh(me)
    bm2.free()
    o = bpy.data.objects.new(name, me)
    C.link(o, parent)
    me.materials.clear()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


def patch(name, bv, mode, u0, u1, v0, v1, mat, parent, nu=24, nv=24, lift=0.006, thick=0.012,
          corner=0.06, bev=0.004):
    """Raised panel conforming to the hull (doors, hatches, ramp). Rounded-rect outline in the
    projection plane, rays cast onto the hull, then solidified."""
    verts, faces = [], []
    grid = []
    for i in range(nu + 1):
        row = []
        for j in range(nv + 1):
            a = u0 + (u1 - u0) * i / nu
            b = v0 + (v1 - v0) * j / nv
            # pull grid points that sit in a corner square onto the corner arc
            ca = min(max(a, u0 + corner), u1 - corner)
            cb = min(max(b, v0 + corner), v1 - corner)
            d = Vector((a - ca, b - cb))
            if d.length > corner:
                d = d.normalized() * corner
                a, b = ca + d.x, cb + d.y
            loc, nrm = hit(bv, mode, a, b)
            if loc is None:
                row.append(None)
                continue
            row.append(len(verts))
            verts.append(loc + nrm * lift)
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            q = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            if None not in q:
                faces.append(q)
    o = C.mesh_obj(name, verts, faces, parent, mat)
    # make normals point away from the hull (toward the ray origin)
    org, d = to3(mode, (u0 + u1) / 2, (v0 + v1) / 2)
    me = o.data
    if len(me.polygons) and me.polygons[len(me.polygons) // 2].normal.dot(d) > 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    if thick:
        s = o.modifiers.new('solid', 'SOLIDIFY')
        s.thickness = thick
        s.offset = -1.0
        if bev:
            b = o.modifiers.new('bevel', 'BEVEL')
            b.width = bev
            b.segments = 2
            b.limit_method = 'ANGLE'
            b.angle_limit = R(50)
        # apply now: SOLIDIFY copies the UVs onto the hidden inner shell, so an unapplied modifier
        # would bake the occluded inner side over the same texels (black panels)
        realize(o)
    C.smooth_by_angle(o, 50)
    return o


def stamp(name, bv, mode, a, b, mesh_fn, parent, out=0.0):
    """Place an object (built at origin with its +Z as the outward normal) on the hull."""
    loc, nrm = hit(bv, mode, a, b)
    o = mesh_fn(name)
    o.parent = parent
    o.location = loc + nrm * out
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(nrm).to_euler()
    return o


def rblade(name, parent, angle, le_sign, r0=0.95, Rt=9.144, chord=0.81, pitch0=7.0, twist=-12.0,
           thick=0.115, droop=0.62, cone=-0.012, n=22, spans=34):
    """CH-47 style blade in hub-local frame: span +X, leading edge toward le_sign*Y (direction of
    travel), thickness Z. Returns blade, leading-edge strip and tip cap objects."""
    prof = C.airfoil(n, thick)
    m = len(prof)

    def chord_at(r):
        t = min(1.0, max(0.0, (r - r0) / 0.75))
        t = t * t * (3 - 2 * t)
        return 0.42 + (chord - 0.42) * t

    def point(r, px, pz, scale=1.0):
        u = (r - r0) / (Rt - r0)
        c = chord_at(r)
        if r > Rt - 0.35:
            # slightly tapered, rounded tip
            k = (r - (Rt - 0.35)) / 0.35
            c *= 1.0 - 0.18 * k * k
        s = (0.27 - px) * c * scale
        z = pz * c * scale
        th = R(pitch0 + twist * u)
        s2 = s * math.cos(th) - z * math.sin(th)
        z2 = s * math.sin(th) + z * math.cos(th)
        dz = -droop * u * u + cone * (r - r0)
        return Vector((r, le_sign * s2, z2 + dz))

    def build(nm, mat, ra, rb, idxs, scale, closed_ring, end_caps, nsp):
        verts, faces = [], []
        k = len(idxs)
        for si in range(nsp + 1):
            r = ra + (rb - ra) * si / nsp
            for i in idxs:
                px, pz = prof[i]
                verts.append(point(r, px, pz, scale))
        rng = k if closed_ring else k - 1
        for si in range(nsp):
            a, b = si * k, (si + 1) * k
            for j in range(rng):
                j2 = (j + 1) % k
                faces.append((a + j, a + j2, b + j2, b + j))
        if end_caps:
            faces.append(tuple(range(k))[::-1])
            faces.append(tuple(range(nsp * k, nsp * k + k)))
        o = C.mesh_obj(nm, verts, faces, parent, mat)
        C._fix_normals(o)
        o.rotation_euler = (0, 0, angle)
        C.smooth_by_angle(o, 50)
        return o

    allidx = list(range(m))
    b = build(name, M['blade'], r0, Rt - 0.3, allidx, 1.0, True, True, spans)
    le_idx = [i for i in range(m) if prof[i][0] < 0.09]
    # prof runs TE->LE (upper) then LE->TE (lower): the LE run is contiguous in index order
    s = build(name + '_le', M['le'], r0 + 1.3, Rt - 0.3, le_idx, 1.012, False, False, spans - 6)
    t = build(name + '_tip', M['steel'], Rt - 0.3, Rt, allidx, 1.0, True, True, 4)
    return b, s, t


# ================================================================== FUSELAGE HULL
def st(x, w, zt, zb, zc=None, nt=3.0, nb=5.0, n=None):
    d = dict(x=x, w=w, zt=zt, zb=zb, nt=nt, nb=nb)
    if zc is not None:
        d['zc'] = zc
    return d


ZB, ZT, ZC, W = 0.62, 3.05, 1.50, 2.62
hull_st = [
    st(8.02, 0.50, 1.50, 1.20, 1.35, 2.2, 2.2),
    st(7.98, 1.20, 1.72, 1.00, 1.36, 2.3, 2.4),
    st(7.90, 1.66, 1.86, 0.84, 1.38, 2.4, 2.6),
    st(7.78, 1.98, 1.99, 0.74, 1.40, 2.5, 2.9),
    st(7.62, 2.24, 2.14, 0.68, 1.42, 2.6, 3.3),
    st(7.44, 2.42, 2.33, 0.65, 1.45, 2.7, 3.8),
    st(7.24, 2.52, 2.53, 0.63, 1.47, 2.8, 4.3),
    st(7.02, 2.58, 2.73, 0.62, 1.49, 2.9, 4.7),
    st(6.80, 2.61, 2.89, ZB, ZC, 3.0, 5.0),
    st(6.55, W, 2.99, ZB, ZC, 3.0, 5.0),
    st(6.25, W, 3.04, ZB, ZC, 3.0, 5.0),
    st(5.90, W, ZT, ZB, ZC, 3.0, 5.0),
]
for x in (5.4, 4.6, 3.6, 2.4, 1.2, 0.0, -1.2, -2.4, -3.4):
    hull_st.append(st(x, W, ZT, ZB, ZC))
hull_st += [
    st(-4.10, W, ZT, 0.63, ZC),
    st(-4.60, W, ZT, 0.70, ZC + 0.02),
    st(-5.20, 2.61, ZT, 0.88, ZC + 0.08, 3.0, 4.8),
    st(-5.85, 2.59, ZT, 1.12, ZC + 0.2, 3.0, 4.6),
    st(-6.50, 2.56, 3.04, 1.38, ZC + 0.34, 3.0, 4.4),
    st(-7.10, 2.53, 3.03, 1.64, ZC + 0.52, 3.0, 4.2),
    st(-7.55, 2.50, 3.02, 1.86, ZC + 0.68, 3.0, 4.0),
    st(-7.82, 2.44, 3.00, 2.02, ZC + 0.8, 3.0, 3.8),
    st(-7.93, 2.34, 2.96, 2.10, ZC + 0.85, 2.9, 3.5),
    st(-7.99, 2.10, 2.90, 2.18, ZC + 0.88, 2.8, 3.0),
]
hull_st.reverse()          # ascending X
hull = C.loft('hull', hull_st, M['body'], P['fuselage'], seg=72, levels=2)
realize(hull)
BV = bvh_of(hull)          # hull before windows are cut: used for every projection

# --- cockpit glazing: faces are split off the hull so the interior is visible -------------
# 'C' polygons are (azimuth deg * KC, z) around the nose axis (wrap-around windscreen / chin);
# 'L' polygons are (x, z) seen from port.  Mirrored for starboard.


def cpoly(pts, r):
    return fillet([(a * KC, z) for a, z in pts], r)


WS_C = cpoly([(1.6, 1.95), (37.5, 1.95), (37.5, 2.80), (1.6, 2.80)], 0.08)          # main pane
CORNER_C = cpoly([(41.5, 1.97), (68.0, 1.97), (68.0, 2.70), (41.5, 2.76)], 0.07)     # corner pane
CHIN_C = cpoly([(4.0, 0.96), (40.0, 0.96), (40.0, 1.76), (4.0, 1.76)], 0.12)         # chin window
CHINS_C = cpoly([(46.0, 1.02), (70.0, 1.02), (70.0, 1.74), (46.0, 1.74)], 0.09)      # lower side
SIDE_L = fillet([(6.86, 1.94), (6.86, 2.70), (6.14, 2.70), (6.14, 1.94)], 0.07)      # sliding

GLASS = []   # (mode, poly)
for sgn, sm in ((1, 'L'), (-1, 'R')):
    for poly in (WS_C, CORNER_C, CHIN_C, CHINS_C):
        GLASS.append(('C', [(sgn * a, b) for a, b in poly]))
    GLASS.append((sm, SIDE_L))


def glass_pred(c, n):
    if c.x < 5.9:
        return False
    for mode, poly in GLASS:
        if mode == 'C':
            dx = c.x - XC
            if dx < 0.05:
                continue
            rad = Vector((dx, c.y, 0)).normalized()
            phi = math.degrees(math.atan2(c.y, dx)) * KC
            if n.dot(rad) > 0.15 and inpoly((phi, c.z), poly):
                return True
        elif mode == 'L':
            if c.y > 0 and n.y > 0.35 and n.x < 0.9 and inpoly((c.x, c.z), poly):
                return True
        else:
            if c.y < 0 and n.y < -0.35 and n.x < 0.9 and inpoly((c.x, c.z), poly):
                return True
    return False


# interior liner = nose skin pushed inward, also with the windows removed
liner = hull.copy()
liner.data = hull.data.copy()
liner.name = 'ck_liner'
C.link(liner, P['cockpit'])
bm = bmesh.new()
bm.from_mesh(liner.data)
bm.normal_update()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x < 5.75
                           or glass_pred(f.calc_center_median(), f.normal)], context='FACES')
bm.normal_update()
for v in bm.verts:
    v.co -= v.normal * 0.035
bm.to_mesh(liner.data)
bm.free()
liner.data.materials.clear()
liner.data.materials.append(M['interior'])

canopy = split_faces(hull, glass_pred, 'ck_glass', M['glass'], P['cockpit'])

# window frames (painted bars over the cut edges)
fr = 0
for mode, poly in GLASS:
    frame_on(BV, mode, poly, 'ck_frame_%d' % fr, 0.03, M['trim'], P['cockpit'], step=0.025)
    fr += 1
# centre windscreen / chin posts
line_on(BV, 'C', [(0.0, 1.9), (0.0, 2.86)], 'ck_post_c', 0.035, M['trim'], P['cockpit'], flat=0.6)
line_on(BV, 'C', [(0.0, 0.92), (0.0, 1.8)], 'ck_post_chin', 0.035, M['trim'], P['cockpit'], flat=0.6)
# windscreen wipers (parked along the lower frame)
for sgn in (1, -1):
    loc, nrm = hit(BV, 'C', sgn * 30 * KC, 1.99)
    base = loc + nrm * 0.025
    tip, n2 = hit(BV, 'C', sgn * 12 * KC, 2.05)
    tip = tip + n2 * 0.03
    C.strut('ck_wiper_arm%d' % sgn, base, tip, 0.008, M['black'], P['cockpit'], verts=6)
    t2, n3 = hit(BV, 'C', sgn * 3 * KC, 2.0)
    t3, n4 = hit(BV, 'C', sgn * 21 * KC, 2.1)
    C.strut('ck_wiper_blade%d' % sgn, t2 + n3 * 0.02, t3 + n4 * 0.02, 0.01, M['rubber'], P['cockpit'], verts=6)
    C.sphere('ck_wiper_hub%d' % sgn, 0.025, base, (1, 1, 1), M['black'], P['cockpit'], 12, 6)

# --- cockpit interior ----------------------------------------------------------------------
CK = P['cockpit']
C.box('ck_floor', (1.75, 2.3, 0.05), (6.65, 0, 0.93), mat=M['interior'], parent=CK, bev=0.005)
# rear cockpit bulkhead shaped to the hull section, with a dark doorway into the cabin
bh = C.ring(dict(x=5.80, w=W - 0.12, zt=ZT - 0.08, zb=ZB + 0.06, zc=ZC, nt=3.0, nb=5.0), 64)
C.mesh_obj('ck_bulkhead', bh, [tuple(range(64))], CK, M['interior'], smooth=False)
C.box('ck_doorway', (0.04, 0.62, 1.75), (5.82, 0, 1.82), mat=M['black'], parent=CK, bev=0.004)
# instrument panel, glare shield, consoles
C.box('ck_panel', (0.08, 1.95, 0.62), (7.18, 0, 1.62), rot=(0, R(-14), 0), mat=M['interior'], parent=CK, bev=0.01)
C.box('ck_glare', (0.38, 2.0, 0.05), (7.17, 0, 1.97), rot=(0, R(4), 0), mat=M['black'], parent=CK, bev=0.012)
for i, y in enumerate((-0.86, -0.52, -0.18, 0.18, 0.52, 0.86)):
    C.box('ck_mfd%d' % i, (0.02, 0.26, 0.22), (7.13, y, 1.66), rot=(0, R(-14), 0), mat=M['display'],
          parent=CK, bev=0.004)
C.box('ck_console', (0.75, 0.38, 0.42), (6.72, 0, 1.15), mat=M['interior'], parent=CK, bev=0.02)
C.box('ck_console_top', (0.6, 0.3, 0.02), (6.72, 0, 1.37), mat=M['display'], parent=CK, bev=0.003)
C.box('ck_overhead', (0.55, 0.42, 0.12), (6.55, 0, 2.92), rot=(0, R(10), 0), mat=M['interior'], parent=CK, bev=0.02)
for sgn in (1, -1):
    y = 0.62 * sgn
    seat = C.empty('ck_seat_%d' % sgn, CK, (6.15, y, 0.95))
    C.box('ck_seat_pan%d' % sgn, (0.52, 0.52, 0.12), (0.05, 0, 0.42), mat=M['seat'], parent=seat, bev=0.035)
    C.box('ck_seat_back%d' % sgn, (0.13, 0.52, 0.8), (-0.22, 0, 0.88), rot=(0, R(-12), 0), mat=M['seat'],
          parent=seat, bev=0.04)
    C.box('ck_seat_head%d' % sgn, (0.12, 0.34, 0.2), (-0.32, 0, 1.36), rot=(0, R(-12), 0), mat=M['seat'],
          parent=seat, bev=0.04)
    C.box('ck_seat_frame%d' % sgn, (0.4, 0.46, 0.36), (0.0, 0, 0.18), mat=M['steel'], parent=seat, bev=0.02)
    for s2 in (1, -1):
        C.box('ck_seat_side%d%d' % (sgn, s2), (0.5, 0.05, 0.2), (0.0, s2 * 0.28, 0.5), mat=M['steel'],
              parent=seat, bev=0.01)
    C.strut('ck_cyclic%d' % sgn, (6.72, y, 0.96), (6.66, y, 1.58), 0.018, M['black'], CK, verts=8)
    C.sphere('ck_cyclic_grip%d' % sgn, 0.035, (6.66, y, 1.62), (1, 1, 1.6), M['black'], CK, 12, 8)
    C.strut('ck_collective%d' % sgn, (6.05, y + sgn * 0.33, 1.1), (6.5, y + sgn * 0.33, 1.38), 0.02,
            M['black'], CK, verts=8)
    for k in range(2):
        C.box('ck_pedal%d%d' % (sgn, k), (0.06, 0.1, 0.18), (7.25, y + (k - 0.5) * 0.24, 1.08),
              rot=(0, R(-30), 0), mat=M['black'], parent=CK, bev=0.01)

# --- crew door (right side, -Y) -----------------------------------------------------------
door = patch('ck_door', BV, 'R', 4.86, 5.66, 0.84, 2.56, M['body'], CK, nu=12, nv=24, lift=0.005,
             thick=0.014, corner=0.07)
patch('ck_door_win', BV, 'R', 5.02, 5.50, 1.92, 2.42, M['glass_dark'], CK, nu=8, nv=8, lift=0.022,
      thick=0, corner=0.06)
frame_on(BV, 'R', fillet([(5.02, 1.92), (5.5, 1.92), (5.5, 2.42), (5.02, 2.42)], 0.06), 'ck_door_winframe',
         0.022, M['trim'], CK, lift=0.022, flat=0.8)
line_on(BV, 'R', [(4.87, 1.72), (5.65, 1.72)], 'ck_door_split', 0.008, M['black'], CK, lift=0.02)
line_on(BV, 'R', [(5.62, 0.9), (5.62, 2.5)], 'ck_door_hinge', 0.014, M['trim'], CK, lift=0.016, flat=1)
for z in (1.3, 2.05):
    loc, nrm = hit(BV, 'R', 4.95, z)
    C.box('ck_door_handle%d' % int(z * 10), (0.04, 0.03, 0.16), loc + nrm * 0.03, mat=M['steel'], parent=CK,
          bev=0.008)
# grab handles beside the crew door and a fold-down boarding step below it
for k, (z0, z1) in enumerate(((1.15, 1.55), (1.8, 2.2))):
    a, na = hit(BV, 'R', 4.76, z0)
    b, nb_ = hit(BV, 'R', 4.76, z1)
    pa, pb = a + na * 0.06, b + nb_ * 0.06
    C.strut('ck_grab%d' % k, pa, pb, 0.012, M['steel'], CK, verts=8)
    C.strut('ck_grab%da' % k, a, pa, 0.012, M['steel'], CK, verts=8)
    C.strut('ck_grab%db' % k, b, pb, 0.012, M['steel'], CK, verts=8)
loc, nrm = hit(BV, 'R', 5.26, 0.75)
C.box('ck_door_step', (0.5, 0.2, 0.03), loc + Vector((0, -0.09, -0.03)), mat=M['trim'], parent=CK, bev=0.008)
for sx in (-0.2, 0.2):
    C.strut('ck_door_step_arm%d' % int(sx * 10), loc + Vector((sx, -0.17, -0.03)), loc + Vector((sx, 0, 0.12)),
            0.01, M['steel'], CK, verts=6)
# hoist above the crew door
C.box('fu_hoist_base', (0.6, 0.22, 0.24), (5.25, -1.18, 2.85), rot=(R(-18), 0, 0), mat=M['trim'],
      parent=P['fuselage'], bev=0.04)
C.strut('fu_hoist_boom', (5.25, -1.25, 2.85), (5.25, -1.65, 2.78), 0.045, M['trim'], P['fuselage'])
C.cyl('fu_hoist_drum', 0.09, 0.32, loc=(5.25, -1.62, 2.72), axis='X', mat=M['steel'], parent=P['fuselage'],
      verts=16, bev=0.01)

# ================================================================== FUSELAGE details
FU = P['fuselage']
# round cabin windows (portholes): frame ring, recess and bulged glass
PORT_L = (4.05, 2.85, 1.65, 0.45, -0.75, -1.95)
PORT_R = (4.05, 2.85, 1.65, 0.45, -0.75, -1.95)
for side, xs in ((1, PORT_L), (-1, PORT_R)):
    mode = 'L' if side > 0 else 'R'
    for i, x in enumerate(xs):
        if side < 0 and x > 4.5:
            continue
        loc, nrm = hit(BV, mode, x, 2.2)
        rot = Vector((0, 0, 1)).rotation_difference(nrm).to_euler()
        g = C.empty('fu_port_%s%d' % (mode, i), FU, loc, rot)
        C.torus('fu_port_ring_%s%d' % (mode, i), 0.225, 0.028, mat=M['trim'], parent=g, seg=40, cs=10)
        C.cyl('fu_port_back_%s%d' % (mode, i), 0.215, 0.012, loc=(0, 0, 0.0), mat=M['black'], parent=g,
              verts=32, bev=0)
        gl = C.sphere('fu_port_glass_%s%d' % (mode, i), 0.215, (0, 0, -0.006), (1, 1, 0.12), M['glass_dark'], g,
                      32, 12)

# escape window, left side behind the cockpit
patch('fu_hatch_win', BV, 'L', 5.0, 5.55, 1.8, 2.45, M['glass_dark'], FU, nu=8, nv=8, lift=0.01, thick=0,
      corner=0.05)
frame_on(BV, 'L', fillet([(5.0, 1.8), (5.55, 1.8), (5.55, 2.45), (5.0, 2.45)], 0.05), 'fu_hatch_frame',
         0.03, M['trim'], FU, lift=0.01, flat=0.7)
patch('fu_hatch_L', BV, 'L', 4.92, 5.63, 0.95, 2.53, M['body'], FU, nu=10, nv=18, lift=0.003, thick=0.008,
      corner=0.05)
# rescue/escape hatches further aft
for side, mode in ((1, 'L'), (-1, 'R')):
    patch('fu_aft_hatch_' + mode, BV, mode, -3.25, -2.55, 1.6, 2.5, M['body'], FU, nu=8, nv=10, lift=0.003,
          thick=0.008, corner=0.05)
    # upper fuselage rail with brackets (as on the reference)
    line_on(BV, mode, [(4.3, 2.62), (-3.6, 2.62)], 'fu_rail_' + mode, 0.016, M['steel'], FU, lift=0.03, flat=1)
    for k, x in enumerate([4.0 - 0.95 * i for i in range(9)]):
        loc, nrm = hit(BV, mode, x, 2.62)
        C.box('fu_rail_brk_%s%d' % (mode, k), (0.05, 0.05, 0.08), loc + nrm * 0.015, mat=M['steel'], parent=FU,
              bev=0.006)
    # steps / hand holds near the forward pylon
    for k in range(4):
        loc, nrm = hit(BV, mode, 6.3 - 0.06 * k, 1.1 + 0.42 * k)
        C.box('fu_step_%s%d' % (mode, k), (0.16, 0.03, 0.06), loc + nrm * 0.005, mat=M['black'], parent=FU, bev=0.006)
    # CMWS missile-warning sensors (nose sides and aft)
    for k, (x, z) in enumerate(((7.32, 0.86), (-6.95, 2.55))):
        loc, nrm = hit(BV, mode, x, z)
        s = C.sphere('fu_cmws_%s%d' % (mode, k), 0.07, loc + nrm * 0.015, (1, 1, 1), M['sensor'], FU, 16, 8)
        C.cyl('fu_cmws_base_%s%d' % (mode, k), 0.085, 0.03, loc=loc, axis='Y', mat=M['trim'], parent=FU,
              verts=16, bev=0.006)
    # aft flare dispensers
    loc, nrm = hit(BV, mode, -6.1, 1.9)
    C.box('fu_flares_' + mode, (0.48, 0.07, 0.3), loc + nrm * 0.03, mat=M['black'], parent=FU, bev=0.012)

# nose: radar/nose cap seam and pitot tubes on the forward pylon face (built later), mirrors
loc, nrm = hit(BV, 'F', 0.0, 1.32)
C.torus('fu_nosecap_seam', 0.34, 0.008, loc=loc + Vector((-0.06, 0, 0)), axis='X', mat=M['black'], parent=FU,
        seg=48, cs=6)

# dorsal drive-shaft tunnel with walkway
dorsal = C.loft('fu_dorsal', [
    st(5.25, 0.8, 3.18, 2.75, 2.95, 4, 2), st(4.95, 1.18, 3.36, 2.75, 2.95, 4, 2),
    st(4.4, 1.26, 3.43, 2.75, 2.95, 4, 2), st(0.0, 1.26, 3.43, 2.75, 2.95, 4, 2),
    st(-2.6, 1.26, 3.43, 2.75, 2.95, 4, 2), st(-3.2, 1.2, 3.40, 2.75, 2.95, 4, 2),
], M['body'], FU, seg=48, levels=2)
for k, (x0, x1) in enumerate(((4.3, 2.0), (1.6, -0.9), (-1.3, -2.8))):
    C.box('fu_walk%d' % k, (x0 - x1, 0.6, 0.012), ((x0 + x1) / 2, 0, 3.434), mat=M['walk'], parent=FU, bev=0.004)
# dorsal access panels and vents
for k, x in enumerate((3.2, 0.3, -2.2)):
    for sgn in (1, -1):
        for j in range(6):
            C.box('fu_vent%d%d_%d' % (k, j, sgn), (0.035, 0.02, 0.12), (x + j * 0.07, sgn * 0.6, 3.25),
                  rot=(sgn * R(38), 0, 0), mat=M['black'], parent=FU, bev=0.004)
# antennas
C.box('fu_ant_blade1', (0.32, 0.02, 0.24), (2.4, 0, 3.55), rot=(0, R(-8), 0), mat=M['black'], parent=FU, bev=0.008)
C.box('fu_ant_blade2', (0.26, 0.02, 0.2), (-1.0, 0, 3.53), rot=(0, R(-8), 0), mat=M['black'], parent=FU, bev=0.008)
C.strut('fu_ant_whip', (1.3, 0.3, 3.42), (0.7, 0.3, 4.3), 0.006, M['black'], FU, verts=6)
C.cyl('fu_gps', 0.08, 0.035, loc=(4.0, 0, 3.45), mat=M['black'], parent=FU, verts=20, bev=0.012)
for k, x in enumerate((2.6, -1.8)):
    C.box('fu_ant_belly%d' % k, (0.3, 0.02, 0.2), (x, 0.25, 0.52), rot=(0, R(-8), 0), mat=M['black'], parent=FU,
          bev=0.008)
for k, x in enumerate((1.0, 0.6)):
    C.cyl('fu_radalt%d' % k, 0.09, 0.02, loc=(x, -0.3, 0.615), mat=M['black'], parent=FU, verts=20, bev=0.005)
# anti-collision beacons (top on dorsal, bottom under belly)
C.cyl('fu_beacon_top_base', 0.075, 0.04, loc=(-1.7, 0, 3.45), mat=M['black'], parent=FU, verts=20, bev=0.005)
C.sphere('fu_beacon_top', 0.06, (-1.7, 0, 3.49), (1, 1, 0.8), M['beacon'], FU, 20, 10)
C.cyl('fu_beacon_bot_base', 0.075, 0.04, loc=(-0.8, 0, 0.60), mat=M['black'], parent=FU, verts=20, bev=0.005)
C.sphere('fu_beacon_bot', 0.06, (-0.8, 0, 0.56), (1, 1, 0.8), M['beacon'], FU, 20, 10)
# cargo hooks (forward, centre, aft)
for k, x in enumerate((1.8, 0.0, -1.8)):
    big = k == 1
    C.box('fu_hook_frame%d' % k, (0.5 if big else 0.32, 0.3 if big else 0.2, 0.08), (x, 0, 0.58), mat=M['steel'],
          parent=FU, bev=0.015)
    C.box('fu_hook%d' % k, (0.06, 0.12, 0.22 if big else 0.14), (x, 0, 0.47 if big else 0.5), mat=M['metal'],
          parent=FU, bev=0.012)

# ================================================================== FORWARD PYLON
FP = P['frontPylon']


def pst(x, w, zt, tp, nt=3.6, zb=2.5, zc=2.85):
    return dict(x=x, w=w, zt=zt, zb=zb, zc=zc, nt=nt, nb=2.0, taper=tp)


fpyl = tloft('fp_pylon', [
    pst(6.92, 0.90, 2.92, 0.18, 3.0),
    pst(6.86, 1.40, 3.45, 0.20),
    pst(6.76, 1.56, 3.92, 0.24),
    pst(6.60, 1.62, 4.12, 0.27),
    pst(6.30, 1.64, 4.20, 0.28),
    pst(5.60, 1.64, 4.21, 0.28),
    pst(5.20, 1.58, 4.10, 0.27),
    pst(4.80, 1.46, 3.80, 0.22),
    pst(4.40, 1.32, 3.50, 0.12, 4.0),
    pst(4.10, 1.26, 3.43, 0.05, 4.0, 2.75, 2.95),
], M['pylon'], FP, seg=56, levels=2)
FPB = bvh_of(realize(fpyl))
# louvred cooling grilles on both sides of the forward pylon
for mode, sgn in (('L', 1), ('R', -1)):
    for j in range(7):
        x = 5.75 - j * 0.085
        loc, nrm = hit(FPB, mode, x, 3.72)
        C.box('fp_louvre_%s%d' % (mode, j), (0.04, 0.025, 0.34), loc + nrm * 0.006,
              rot=(0, 0, 0), mat=M['black'], parent=FP, bev=0.006)
    patch('fp_panel_' + mode, FPB, mode, 5.15, 6.55, 3.15, 4.02, M['pylon'], FP, nu=10, nv=8, lift=0.002,
          thick=0.006, corner=0.05)
    # pitot tubes on the pylon front face
    loc, nrm = hit(FPB, 'F', sgn * 0.32, 3.7)
    C.strut('fp_pitot_mast_' + mode, loc - nrm * 0.03, loc + Vector((0.2, 0, 0.03)), 0.018, M['trim'], FP, verts=10)
    C.strut('fp_pitot_' + mode, loc + Vector((0.18, 0, 0.03)), loc + Vector((0.5, 0, 0.03)), 0.012, M['metal'], FP,
            verts=10, r2=0.008)
# pylon top ring and static mast/swashplate (tilted with the shaft)
fpf = C.empty('fp_shaft_frame', FP, HUB_F, (0, TILT_F, 0))
C.cyl('fp_top_ring', 0.62, 0.08, loc=(0, 0, -0.5), mat=M['pylon'], parent=fpf, verts=40, bev=0.015)
C.cyl('fp_mast', 0.17, 0.62, loc=(0, 0, -0.32), mat=M['steel'], parent=fpf, verts=24, bev=0.01)
C.cyl('fp_boot', 0.26, 0.12, loc=(0, 0, -0.42), mat=M['rubber'], parent=fpf, verts=24, bev=0.02, r2=0.2)
C.cyl('fp_swash_static', 0.46, 0.065, loc=(0, 0, -0.30), mat=M['hub'], parent=fpf, verts=40, bev=0.012)
for k in range(3):
    a = R(30 + 120 * k)
    C.strut('fp_servo%d' % k, (0.4 * math.cos(a), 0.4 * math.sin(a), -0.6),
            (0.42 * math.cos(a), 0.42 * math.sin(a), -0.31), 0.03, M['chrome'], fpf, verts=10)
C.box('fp_antitorque_link', (0.06, 0.05, 0.2), (0.0, 0.48, -0.42), mat=M['steel'], parent=fpf, bev=0.01)

# ================================================================== AFT PYLON
RP = P['rearPylon']
rpyl = tloft('rp_pylon', [
    pst(-2.30, 1.20, 3.40, 0.05, 4.0, 2.75, 2.95),
    pst(-2.90, 1.44, 3.64, 0.12, 3.8),
    pst(-3.50, 1.64, 3.98, 0.20),
    pst(-4.10, 1.76, 4.38, 0.25),
    pst(-4.70, 1.80, 4.72, 0.28),
    pst(-5.25, 1.80, 4.92, 0.30),
    pst(-5.90, 1.78, 5.00, 0.30),
    pst(-6.55, 1.74, 4.96, 0.30),
    pst(-7.10, 1.68, 4.82, 0.28),
    pst(-7.50, 1.60, 4.52, 0.25),
    pst(-7.74, 1.50, 4.14, 0.22, 3.4),
    pst(-7.88, 1.30, 3.80, 0.18, 3.0, 2.6, 2.9),
], M['pylon'], RP, seg=56, levels=2)
RPB = bvh_of(realize(rpyl))
for mode, sgn in (('L', 1), ('R', -1)):
    patch('rp_panel_' + mode, RPB, mode, -6.7, -4.9, 3.5, 4.05, M['pylon'], RP, nu=12, nv=6, lift=0.002,
          thick=0.006, corner=0.05)
    patch('rp_panel2_' + mode, RPB, mode, -7.45, -6.85, 3.2, 4.3, M['pylon'], RP, nu=6, nv=8, lift=0.002,
          thick=0.006, corner=0.04)
    for j in range(8):
        loc, nrm = hit(RPB, mode, -4.4 - j * 0.08, 4.25 - j * 0.03)
        C.box('rp_louvre_%s%d' % (mode, j), (0.04, 0.025, 0.3), loc + nrm * 0.006, mat=M['black'], parent=RP,
              bev=0.006)
# oil-cooler exhaust grille at the top-aft of the pylon
for j in range(9):
    C.box('rp_cooler%d' % j, (0.05, 0.9, 0.02), (-6.6 - j * 0.07, 0, 4.955 - j * 0.012), mat=M['black'],
          parent=RP, bev=0.004)
# tail (position) light on the trailing edge
C.box('rp_tail_light_base', (0.06, 0.1, 0.16), (-7.88, 0, 3.95), mat=M['black'], parent=RP, bev=0.01)
C.sphere('rp_tail_light', 0.032, (-7.91, 0, 3.95), (0.7, 1, 1.2), M['white'], RP, 16, 8)
rpf = C.empty('rp_shaft_frame', RP, HUB_R, (0, TILT_R, 0))
C.cyl('rp_top_ring', 0.62, 0.08, loc=(0, 0, -0.46), mat=M['pylon'], parent=rpf, verts=40, bev=0.015)
C.cyl('rp_mast', 0.17, 0.6, loc=(0, 0, -0.3), mat=M['steel'], parent=rpf, verts=24, bev=0.01)
C.cyl('rp_boot', 0.26, 0.12, loc=(0, 0, -0.38), mat=M['rubber'], parent=rpf, verts=24, bev=0.02, r2=0.2)
C.cyl('rp_swash_static', 0.46, 0.065, loc=(0, 0, -0.28), mat=M['hub'], parent=rpf, verts=40, bev=0.012)
for k in range(3):
    a = R(30 + 120 * k)
    C.strut('rp_servo%d' % k, (0.4 * math.cos(a), 0.4 * math.sin(a), -0.56),
            (0.42 * math.cos(a), 0.42 * math.sin(a), -0.29), 0.03, M['chrome'], rpf, verts=10)

# ================================================================== ENGINES (T55 pods)
EN = P['engine']
EY, EZ = 1.42, 3.46
eng = C.empty('en_L', EN)
C.loft('en_nacelle_L', [
    dict(x=-4.02, w=0.84, zt=EZ + 0.42, zb=EZ - 0.42, y=EY, n=2),
    dict(x=-4.10, w=0.93, zt=EZ + 0.465, zb=EZ - 0.465, y=EY, n=2),
    dict(x=-4.35, w=0.96, zt=EZ + 0.48, zb=EZ - 0.48, y=EY, n=2),
    dict(x=-5.30, w=0.96, zt=EZ + 0.48, zb=EZ - 0.48, y=EY, n=2),
    dict(x=-6.05, w=0.92, zt=EZ + 0.46, zb=EZ - 0.46, y=EY, n=2),
    dict(x=-6.45, w=0.84, zt=EZ + 0.42, zb=EZ - 0.42, y=EY, n=2),
    dict(x=-6.58, w=0.78, zt=EZ + 0.39, zb=EZ - 0.39, y=EY, n=2),
], M['body'], eng, seg=48, levels=2, cap=True)
C.torus('en_lip_L', 0.415, 0.045, loc=(-4.02, EY, EZ), axis='X', mat=M['trim'], parent=eng, seg=48, cs=12)
C.cyl('en_intake_back_L', 0.40, 0.02, loc=(-4.06, EY, EZ), axis='X', mat=M['soot'], parent=eng, verts=40, bev=0)
C.cyl('en_spinner_L', 0.16, 0.28, loc=(-3.98, EY, EZ), axis='X', mat=M['steel'], parent=eng, verts=24, bev=0,
      r2=0.04)
# domed inlet screen built as a real wire mesh
bmd = bmesh.new()
bmesh.ops.create_uvsphere(bmd, u_segments=28, v_segments=14, radius=1.0)
bmesh.ops.delete(bmd, geom=[v for v in bmd.verts if v.co.z < -0.02], context='VERTS')
me = bpy.data.meshes.new('en_screen_L')
bmd.to_mesh(me)
bmd.free()
scr = bpy.data.objects.new('en_screen_L', me)
C.link(scr, eng)
scr.location = (-4.03, EY, EZ)
scr.rotation_euler = (0, R(90), 0)
scr.scale = (0.42, 0.42, 0.3)
me.materials.append(M['metal'])
wf = scr.modifiers.new('wire', 'WIREFRAME')
wf.thickness = 0.03
wf.use_even_offset = True
# exhaust nozzle and soot
C.cyl('en_exh_L', 0.335, 0.62, loc=(-6.82, EY, EZ), axis='X', mat=M['exhaust'], parent=eng, verts=40, bev=0.01,
      r2=0.36, cap=False)
C.cyl('en_exh_in_L', 0.32, 0.6, loc=(-6.8, EY, EZ), axis='X', mat=M['soot'], parent=eng, verts=40, bev=0,
      r2=0.34, cap=False)
C.cyl('en_exh_core_L', 0.14, 0.3, loc=(-6.62, EY, EZ), axis='X', mat=M['soot'], parent=eng, verts=24, bev=0, r2=0.05)
C.torus('en_exh_lip_L', 0.36, 0.014, loc=(-7.13, EY, EZ), axis='X', mat=M['exhaust'], parent=eng, seg=40, cs=8)
C.torus('en_exh_flange_L', 0.4, 0.03, loc=(-6.53, EY, EZ), axis='X', mat=M['steel'], parent=eng, seg=40, cs=8)
# mounting fairing + forward drive-shaft housing to the combining transmission
C.box('en_mount_L', (1.7, 0.42, 0.42), (-5.25, 0.86, EZ), mat=M['pylon'], parent=eng, bev=0.12, seg=4)
C.cyl('en_driveshaft_L', 0.13, 0.62, loc=(-4.32, 0.98, EZ + 0.05), axis='Y', mat=M['pylon'], parent=eng,
      verts=24, bev=0.02)
for k in range(5):
    # cowling latches along the outboard split line
    C.box('en_cowl_latch_L%d' % k, (0.12, 0.03, 0.04), (-4.55 - 0.36 * k, EY + 0.478, EZ + 0.06), mat=M['steel'],
          parent=eng, bev=0.006)
# lower cooling louvres
for j in range(6):
    C.box('en_louvre_L%d' % j, (0.05, 0.12, 0.02), (-5.0 - j * 0.09, EY + 0.18, EZ - 0.47), rot=(R(-20), 0, 0),
          mat=M['black'], parent=eng, bev=0.004)
C.mirror_tree(eng, parent=EN)

# ================================================================== SPONSONS
SP = P['sponson']
SY = 1.52


def sponson(name, y):
    return C.loft(name, [
        dict(x=4.84, w=0.26, zt=1.56, zb=1.22, y=y, nt=2.2, nb=2.4),
        dict(x=4.76, w=0.56, zt=1.74, zb=1.06, y=y, nt=2.2, nb=2.6),
        dict(x=4.56, w=0.74, zt=1.86, zb=0.98, y=y, nt=2.3, nb=2.8),
        dict(x=4.22, w=0.80, zt=1.90, zb=0.95, y=y, nt=2.4, nb=3.0),
        dict(x=2.0, w=0.80, zt=1.90, zb=0.95, y=y, nt=2.4, nb=3.0),
        dict(x=-1.0, w=0.80, zt=1.90, zb=0.95, y=y, nt=2.4, nb=3.0),
        dict(x=-3.35, w=0.80, zt=1.90, zb=0.95, y=y, nt=2.4, nb=3.0),
        dict(x=-3.75, w=0.74, zt=1.86, zb=0.99, y=y, nt=2.3, nb=2.8),
        dict(x=-4.02, w=0.54, zt=1.74, zb=1.10, y=y, nt=2.2, nb=2.5),
        dict(x=-4.14, w=0.24, zt=1.58, zb=1.26, y=y, nt=2.2, nb=2.2),
    ], M['body'], SP, seg=48, levels=2)


spL = sponson('sp_sponson_L', SY)
spR = sponson('sp_sponson_R', -SY)
for so, sgn, mode in ((spL, 1, 'L'), (spR, -1, 'R')):
    sb = bvh_of(realize(so))
    # fuel filler caps, access panels, step recesses
    for k, x in enumerate((1.4, -1.6)):
        loc, nrm = hit(sb, mode, x, 1.7)
        C.cyl('sp_fuelcap_%s%d' % (mode, k), 0.07, 0.02, loc=loc, mat=M['steel'], parent=SP, verts=20,
              rot=Vector((0, 0, 1)).rotation_difference(nrm).to_euler(), bev=0.005)
    for k, (x0, x1) in enumerate(((3.9, 2.9), (2.0, 1.1), (-2.4, -3.2))):
        patch('sp_panel_%s%d' % (mode, k), sb, mode, x1, x0, 1.14, 1.62, M['body'], SP, nu=8, nv=5, lift=0.002,
              thick=0.005, corner=0.05)
    for k, x in enumerate((4.45, 3.3)):
        loc, nrm = hit(sb, mode, x, 1.18)
        C.box('sp_step_%s%d' % (mode, k), (0.22, 0.04, 0.05), loc + nrm * 0.01, mat=M['black'], parent=SP,
              bev=0.006)
    # position light on the forward sponson nose
    loc, nrm = hit(sb, mode, 4.6, 1.62)
    C.box('sp_navbase_' + mode, (0.12, 0.06, 0.08), loc + nrm * 0.015, mat=M['black'], parent=SP, bev=0.01)
    C.sphere('sp_nav_' + mode, 0.04, loc + nrm * 0.05, (1.3, 0.8, 0.9), M['red'] if sgn > 0 else M['green'],
             SP, 16, 8)
    C.stencil('sp_text_' + mode, 'UNITED STATES ARMY', so, (-0.6, sgn * 1.97, 1.45),
              rot=(R(90), 0, R(180) if sgn > 0 else 0), size=0.2, mat=M['stencil'], parent=SP)

# ================================================================== RAMP
RA = P['ramp']
HX = -4.32
ramp = patch('ra_ramp', BV, 'U', -7.97, HX, -1.12, 1.12, M['body'], RA, nu=34, nv=24, lift=0.008, thick=0.02,
             corner=0.03, bev=0.005)
loc, nrm = hit(BV, 'U', HX, 0.0)
C.cyl('ra_hinge', 0.03, 1.9, loc=(HX + 0.01, 0, loc.z + 0.012), axis='Y', mat=M['steel'], parent=RA, verts=16,
      bev=0.004)
for k in range(6):
    y = -0.85 + k * 0.34
    C.box('ra_knuckle%d' % k, (0.1, 0.09, 0.05), (HX + 0.03, y, loc.z + 0.005), mat=M['trim'], parent=RA,
          bev=0.012)
# side seal lines and aft edge of the closed ramp
for sgn in (1, -1):
    line_on(BV, 'U', [(HX - 0.08, sgn * 1.13), (-7.9, sgn * 1.13)], 'ra_seal%d' % sgn, 0.018, M['trim'], RA,
            lift=0.012, flat=0.5)
line_on(BV, 'U', [(-7.9, -1.1), (-7.9, 1.1)], 'ra_aft_edge', 0.03, M['trim'], RA, lift=0.012, flat=0.6)

# ================================================================== LANDING GEAR
GE = P['gear']


def wheel_r(r, w):
    return r + 0.1 * w           # outer tyre radius of C.wheel


FRW_R, FRW_W = 0.36, 0.2
RRW_R, RRW_W = 0.38, 0.24
FX, FYC = 3.90, 1.60
RX, RYC = -3.15, 1.70
SB = 0.97                       # sponson underside height (gear attachment)
for sgn, sfx in ((1, 'L'), (-1, 'R')):
    yc = sgn * FYC
    az = wheel_r(FRW_R, FRW_W)
    for k, dy in enumerate((-0.155, 0.155)):
        C.wheel('ge_fw_%s%d' % (sfx, k), FRW_R, FRW_W, (FX, yc + dy, az), M['rubber'], M['gearp'], GE)
    C.cyl('ge_faxle_' + sfx, 0.05, 0.42, loc=(FX, yc, az), axis='Y', mat=M['steel'], parent=GE, verts=16, bev=0.005)
    C.box('ge_fyoke_' + sfx, (0.17, 0.15, 0.16), (FX, yc, az + 0.07), mat=M['gearp'], parent=GE, bev=0.03)
    C.strut('ge_fpiston_' + sfx, (FX, yc, az + 0.1), (FX, yc, az + 0.36), 0.052, M['chrome'], GE, verts=16)
    C.strut('ge_foleo_' + sfx, (FX, yc, az + 0.3), (FX, yc, SB), 0.08, M['gearp'], GE, verts=20)
    C.box('ge_fmount_' + sfx, (0.42, 0.24, 0.1), (FX, yc, SB + 0.02), mat=M['gearp'], parent=GE, bev=0.03)
    # torque links (scissors)
    C.box('ge_ftl1_' + sfx, (0.14, 0.03, 0.03), (FX + 0.08, yc, az + 0.3), rot=(0, R(35), 0), mat=M['steel'],
          parent=GE, bev=0.005)
    C.box('ge_ftl2_' + sfx, (0.14, 0.03, 0.03), (FX + 0.08, yc, az + 0.18), rot=(0, R(-35), 0), mat=M['steel'],
          parent=GE, bev=0.005)
    # drag brace and side brace into the fuselage
    C.strut('ge_fdrag_' + sfx, (FX, yc, az + 0.42), (FX + 0.7, sgn * 1.28, 0.8), 0.032, M['gearp'], GE)
    C.strut('ge_fside_' + sfx, (FX, yc, az + 0.4), (FX - 0.05, sgn * 1.24, 0.75), 0.028, M['gearp'], GE)
    C.strut('ge_fbrake_' + sfx, (FX + 0.03, yc + 0.07 * sgn, SB), (FX + 0.03, yc + 0.11 * sgn, az + 0.04),
            0.008, M['black'], GE, verts=6)
    # rear (single, castoring) gear: oleo, swivel, trailing fork
    ry = sgn * RYC
    raz = wheel_r(RRW_R, RRW_W)
    wx = RX - 0.2
    C.wheel('ge_rw_' + sfx, RRW_R, RRW_W, (wx, ry, raz), M['rubber'], M['gearp'], GE)
    for s2 in (1, -1):
        C.strut('ge_rfork_%s%d' % (sfx, s2), (RX, ry + s2 * 0.19, raz + 0.24), (wx, ry + s2 * 0.19, raz), 0.035,
                M['gearp'], GE, verts=12)
    C.cyl('ge_raxle_' + sfx, 0.045, 0.4, loc=(wx, ry, raz), axis='Y', mat=M['steel'], parent=GE, verts=16,
          bev=0.005)
    C.box('ge_rcrown_' + sfx, (0.16, 0.42, 0.09), (RX, ry, raz + 0.26), mat=M['gearp'], parent=GE, bev=0.03)
    C.strut('ge_rpiston_' + sfx, (RX, ry, raz + 0.28), (RX, ry, raz + 0.42), 0.055, M['chrome'], GE, verts=16)
    C.strut('ge_roleo_' + sfx, (RX, ry, raz + 0.4), (RX, ry, SB), 0.082, M['gearp'], GE, verts=20)
    C.cyl('ge_rswivel_' + sfx, 0.11, 0.05, loc=(RX, ry, raz + 0.44), mat=M['steel'], parent=GE, verts=20, bev=0.01)
    C.box('ge_rmount_' + sfx, (0.42, 0.26, 0.1), (RX, ry, SB + 0.02), mat=M['gearp'], parent=GE, bev=0.03)
    C.strut('ge_rdamper_' + sfx, (RX + 0.1, ry + 0.1 * sgn, SB - 0.02), (RX + 0.05, ry + 0.12 * sgn, raz + 0.3),
            0.02, M['chrome'], GE, verts=10)
    C.strut('ge_rbrace_' + sfx, (RX, ry, raz + 0.45), (RX + 0.3, sgn * 1.26, 0.8), 0.03, M['gearp'], GE)

# ================================================================== ROTORS


def rotor(part, name, hub, tilt, spin, angles):
    sp = C.spinner(name, part, tuple(hub), (0, tilt, 0), spin)
    pre = 'fr' if spin > 0 else 'rr'
    C.cyl(pre + '_hub_core', 0.27, 0.36, loc=(0, 0, 0), mat=M['hub'], parent=sp, verts=32, bev=0.03)
    C.cyl(pre + '_hub_flange', 0.36, 0.06, loc=(0, 0, -0.17), mat=M['hub'], parent=sp, verts=36, bev=0.01)
    C.sphere(pre + '_hub_cap', 0.26, (0, 0, 0.17), (1, 1, 0.42), M['hub'], sp, 32, 12)
    C.cyl(pre + '_swash_rot', 0.42, 0.06, loc=(0, 0, -0.38), mat=M['hub'], parent=sp, verts=36, bev=0.012)
    C.box(pre + '_scissor', (0.22, 0.05, 0.04), (0.18, 0.3, -0.27), rot=(0, R(-40), 0), mat=M['steel'], parent=sp,
          bev=0.006)
    for i, a in enumerate(angles):
        arm = C.empty('%s_arm%d' % (pre, i), sp, (0, 0, 0), (0, 0, a))
        C.box('%s_flap%d' % (pre, i), (0.26, 0.30, 0.22), (0.36, 0, 0), mat=M['hub'], parent=arm, bev=0.04)
        C.cyl('%s_flappin%d' % (pre, i), 0.045, 0.38, loc=(0.4, 0, 0), axis='Y', mat=M['metal'], parent=arm,
              verts=12, bev=0.004)
        C.cyl('%s_lagpin%d' % (pre, i), 0.06, 0.3, loc=(0.56, 0, 0), mat=M['metal'], parent=arm, verts=14, bev=0.005)
        C.cyl('%s_pitchhouse%d' % (pre, i), 0.13, 0.62, loc=(0.9, 0, 0), axis='X', mat=M['hub'], parent=arm,
              verts=24, bev=0.02, r2=0.11)
        C.box('%s_cuff%d' % (pre, i), (0.34, 0.36, 0.11), (1.2, 0, 0.0), mat=M['hub'], parent=arm, bev=0.03)
        for s2 in (1, -1):
            C.cyl('%s_bolt%d%d' % (pre, i, s2), 0.025, 0.16, loc=(1.2, s2 * 0.11, 0), mat=M['metal'], parent=arm,
                  verts=8, bev=0)
        le = spin                     # leading edge side (+Y for CCW)
        C.strut('%s_damper%d' % (pre, i), (0.3, le * -0.2, 0.06), (0.95, le * -0.16, 0.05), 0.04, M['steel'],
                arm, verts=12)
        C.strut('%s_dampercyl%d' % (pre, i), (0.3, le * -0.2, 0.06), (0.62, le * -0.18, 0.055), 0.055, M['hub'],
                arm, verts=12)
        C.box('%s_horn%d' % (pre, i), (0.2, 0.08, 0.06), (0.72, le * 0.2, -0.06), mat=M['hub'], parent=arm,
              bev=0.015)
        C.strut('%s_plink%d' % (pre, i), (0.78, le * 0.27, -0.08), (0.38, le * 0.24, -0.36), 0.022, M['metal'],
                arm, verts=10)
        C.box('%s_droopstop%d' % (pre, i), (0.08, 0.12, 0.06), (0.28, 0, -0.14), mat=M['steel'], parent=arm,
              bev=0.01)
        rblade('%s_blade%d' % (pre, i), sp, a, le)
    return sp


rotor(P['frontRotor'], 'spin_main', HUB_F, TILT_F, 1, [R(0), R(120), R(240)])
rotor(P['rearRotor'], 'spin_main_rear', HUB_R, TILT_R, -1, [R(60), R(180), R(300)])

# ================================================================== MARKINGS
for mode, sgn in (('L', 1), ('R', -1)):
    C.stencil('rp_text_army_' + mode, 'U.S. ARMY', rpyl, (-6.15, sgn * 0.85, 4.45),
              rot=(R(90), 0, R(180) if sgn > 0 else 0), size=0.2, mat=M['stencil'], parent=RP)
    C.stencil('rp_text_serial_' + mode, '15-08143', rpyl, (-6.15, sgn * 0.85, 4.2),
              rot=(R(90), 0, R(180) if sgn > 0 else 0), size=0.16, mat=M['stencil'], parent=RP)
    C.stencil('fu_text_noste_' + mode, 'NO STEP', dorsal, (2.0, sgn * 0.66, 3.3),
              rot=(R(90), 0, R(180) if sgn > 0 else 0), size=0.05, mat=M['stencil'], parent=FU)
C.stencil('fu_text_belly', 'ARMY', hull, (0.0, 0, 0.55), rot=(R(180), 0, R(90)), size=0.5,
          mat=M['stencil'], parent=FU)

C.finish('chinook')
