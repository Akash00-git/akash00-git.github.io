"""Shared Blender toolkit for the helicopter archive.

Run a model script with:
  blender -b --factory-startup --python helicopter/blender/<model>.py -- [--geo | --fast | --preview]
    --geo      shape check only: no bake/export, 3 small procedural-material renders (~1 min)
    --fast     low-res bake + export + previews (pipeline check)
    --preview  full-quality bake + export + full-size previews (final)

Coordinate contract (Blender space): metres, nose toward +X, up +Z, left/right along Y,
aircraft centred on Y=0, wheels touching Z=0. glTF export converts to Y-up, so Blender
local +Z of every node becomes glTF local +Y.

Scene contract for the web viewer:
  * one EMPTY per clickable part named  part_<key>; every mesh is parented under exactly one.
  * spinning rotor assemblies are EMPTIES named spin_main / spin_main_rear / spin_tail whose
    local +Z is the shaft axis; custom prop  spin_dir  = +1 (CCW seen from +Z) or -1.
  * emissive light materials are named emit_beacon (blinks), emit_red, emit_green, emit_white.
"""
import bpy, bmesh, math, os, sys, fcntl, functools
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.expanduser('~/Downloads/heli_blender')
OUT = os.path.join(HERE, '..', 'assets', 'models')
HDRI = os.path.join(WORK, 'hdri', 'approaching_storm.hdr')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GEO = '--geo' in ARGS            # geometry iteration: skip bake/export, small quick renders
FAST = '--fast' in ARGS          # quick iteration: low bake res / samples
PREVIEW = '--preview' in ARGS or FAST or GEO
os.makedirs(os.path.join(WORK, 'renders'), exist_ok=True)
os.makedirs(os.path.join(WORK, 'bake'), exist_ok=True)
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            sc.cycles.device = 'GPU'
            break
        except Exception:
            continue
    return sc


def link(obj, parent=None):
    if obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.3
    e.location = loc
    e.rotation_euler = rot
    return link(e, parent)


_parts = {}


def part(key):
    """Clickable part root (empty at world origin)."""
    if key not in _parts:
        _parts[key] = empty('part_' + key)
    return _parts[key]


def spinner(name, parent, loc, rot=(0, 0, 0), spin_dir=1):
    """Rotor spin empty; local +Z is the shaft axis. Build blades in its local XY plane."""
    e = empty(name, parent, loc, rot)
    e['spin_dir'] = spin_dir
    return e


def mesh_obj(name, verts, faces, parent=None, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    o = bpy.data.objects.new(name, me)
    link(o, parent)
    if mat is not None:
        o.data.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return o


def smooth_by_angle(o, deg=35):
    me = o.data
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(deg))
    except Exception:
        pass
    return o


def subsurf(o, levels=2):
    m = o.modifiers.new('subsurf', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    m.uv_smooth = 'PRESERVE_BOUNDARIES'
    return o


def bevel(o, width=0.02, segments=3, angle=35):
    m = o.modifiers.new('bevel', 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    smooth_by_angle(o, angle)
    return o


def place(o, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    o.location = loc
    o.rotation_euler = rot
    if parent is not None:
        o.parent = parent
    return o


# ------------------------------------------------------------------ lofting
def _sp(v, e):
    return math.copysign(abs(v) ** e, v)


def ring(st, seg):
    """Superellipse cross-section. st keys: x, w (full width), zt (top), zb (bottom),
    optional zc (widest height, default mid), n (squareness 2=ellipse, 4+=boxy),
    nt / nb (top / bottom squareness), y (lateral offset, default 0)."""
    x, w = st['x'], st['w']
    zt, zb = st['zt'], st['zb']
    zc = st.get('zc', (zt + zb) / 2)
    n = st.get('n', 2.5)
    nt, nb = st.get('nt', n), st.get('nb', n)
    yo = st.get('y', 0.0)
    pts = []
    for i in range(seg):
        t = 2 * math.pi * i / seg
        c, s = math.cos(t), math.sin(t)
        e = 2.0 / (nt if s >= 0 else nb)
        y = yo + (w / 2) * _sp(c, e)
        zr = _sp(s, e)
        z = zc + zr * ((zt - zc) if zr >= 0 else (zc - zb))
        pts.append((x, y, z))
    return pts


def loft(name, stations, mat=None, parent=None, seg=40, levels=2, cap=True):
    """Smooth fuselage-style shell through cross-section stations ordered along X."""
    verts, faces = [], []
    for st in stations:
        verts += ring(st, seg)
    ns = len(stations)
    for i in range(ns - 1):
        a, b = i * seg, (i + 1) * seg
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((a + j, b + j, b + k, a + k))
    if cap:
        for idx, rev in ((0, True), (ns - 1, False)):
            cx = sum(v[0] for v in verts[idx * seg:(idx + 1) * seg]) / seg
            cy = sum(v[1] for v in verts[idx * seg:(idx + 1) * seg]) / seg
            cz = sum(v[2] for v in verts[idx * seg:(idx + 1) * seg]) / seg
            c = len(verts)
            verts.append((cx, cy, cz))
            for j in range(seg):
                k = (j + 1) % seg
                f = (c, idx * seg + k, idx * seg + j) if rev else (c, idx * seg + j, idx * seg + k)
                faces.append(f)
    o = mesh_obj(name, verts, faces, parent, mat)
    _fix_normals(o)
    if levels:
        subsurf(o, levels)
    return o


def _fix_normals(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


# ------------------------------------------------------------------ primitives
def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, bev=0.02, seg=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    link(o, parent)
    place(o, loc, rot)
    if mat is not None:
        me.materials.append(mat)
    if bev:
        bevel(o, bev, seg)
    return o


_AX = {'X': (0, math.pi / 2, 0), 'Y': (-math.pi / 2, 0, 0), 'Z': (0, 0, 0)}


def cyl(name, r, depth, loc=(0, 0, 0), axis='Z', rot=None, mat=None, parent=None, verts=32, r2=None, bev=0.01, cap=True):
    """Cylinder / cone along an axis. r2 = end radius (taper) at +axis end."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=verts,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    link(o, parent)
    place(o, loc, rot if rot is not None else _AX[axis])
    if mat is not None:
        me.materials.append(mat)
    if bev:
        bevel(o, bev, 2, 40)
    else:
        smooth_by_angle(o, 40)
    return o


def sphere(name, r, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, parent=None, seg=32, rings=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    link(o, parent)
    o.location = loc
    o.scale = scale
    if mat is not None:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


def strut(name, p1, p2, r, mat=None, parent=None, verts=16, r2=None):
    """Cylinder between two world points."""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    o = cyl(name, r, d.length, loc=(p1 + p2) / 2, mat=mat, parent=parent, verts=verts, r2=r2, bev=0)
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return o


def torus(name, R, r, loc=(0, 0, 0), axis='Z', mat=None, parent=None, seg=48, cs=16):
    verts, faces = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(cs):
            b = 2 * math.pi * j / cs
            rr = R + r * math.cos(b)
            verts.append((rr * math.cos(a), rr * math.sin(a), r * math.sin(b)))
    for i in range(seg):
        for j in range(cs):
            a, b = i * cs + j, ((i + 1) % seg) * cs + j
            c, d = ((i + 1) % seg) * cs + (j + 1) % cs, i * cs + (j + 1) % cs
            faces.append((a, b, c, d))
    o = mesh_obj(name, verts, faces, parent, mat)
    place(o, loc, _AX[axis])
    return o


def wheel(name, r, width, loc, mat_tyre, mat_hub, parent=None, axis='Y'):
    """Tyre (torus-ish profile) + hub, axle along `axis`."""
    g = empty(name, parent, loc, _AX[axis])
    t = torus(name + '_tyre', r - width * 0.32, width * 0.42, mat=mat_tyre, parent=g)
    t.scale = (1, 1, 1.15)
    t.location = (0, 0, 0)
    t.rotation_euler = (0, 0, 0)
    cyl(name + '_hub', r * 0.55, width * 0.9, mat=mat_hub, parent=g, verts=24, bev=0.01)
    cyl(name + '_cap', r * 0.22, width * 1.05, mat=mat_hub, parent=g, verts=16, bev=0.005)
    return g


def airfoil(n=14, t=0.12):
    """NACA-00xx closed profile, chord 0..1 along +X, thickness along Z (returns list of (x,z))."""
    up, lo = [], []
    for i in range(n + 1):
        x = (1 - math.cos(math.pi * i / n)) / 2
        z = 5 * t * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        up.append((x, z))
        lo.append((x, -z))
    return up[::-1] + lo[1:-1]


def blade(name, r0, R, chord, mat=None, parent=None, twist=-8, thick=0.11, tip_chord=None,
          sweep=0.0, sweep_start=0.93, droop=0.0, angle=0.0, n=14, spans=18, anhedral=0.0):
    """Rotor blade in the spinner's local frame: span along local +X from r0 to R, chord along Y
    (leading edge toward -Y when spinning CCW), thickness along Z. `angle` rotates the blade
    about Z (radians) so you can place N blades. sweep (m) = tip trailing sweep, droop (m) = static
    tip droop, anhedral (m) extra tip drop over the swept part."""
    prof = airfoil(n, thick)
    m = len(prof)
    verts, faces = [], []
    tc = chord if tip_chord is None else tip_chord
    for s in range(spans + 1):
        u = s / spans
        r = r0 + (R - r0) * u
        c = chord + (tc - chord) * max(0.0, (u - sweep_start) / (1 - sweep_start)) if tip_chord else chord
        tw = math.radians(twist) * u
        sw = sweep * max(0.0, (u - sweep_start) / (1 - sweep_start)) ** 2
        dz = -droop * u ** 2 - anhedral * max(0.0, (u - sweep_start) / (1 - sweep_start)) ** 2
        for (px, pz) in prof:
            yy = (px - 0.28) * c
            zz = pz * c
            y2 = yy * math.cos(tw) - zz * math.sin(tw)
            z2 = yy * math.sin(tw) + zz * math.cos(tw)
            verts.append((r, y2 + sw, z2 + dz))
    for s in range(spans):
        for j in range(m):
            k = (j + 1) % m
            a, b = s * m, (s + 1) * m
            faces.append((a + j, a + k, b + k, b + j))
    for idx, rev in ((0, True), (spans, False)):
        ring_ = list(range(idx * m, idx * m + m))
        faces.append(tuple(ring_[::-1]) if rev else tuple(ring_))
    o = mesh_obj(name, verts, faces, parent, mat)
    _fix_normals(o)
    o.rotation_euler = (0, 0, angle)
    smooth_by_angle(o, 50)
    return o


# ------------------------------------------------------------------ mirroring
def mirror_y(o, name=None, parent=None):
    """Return a mirrored copy across the aircraft centreline (Y -> -Y). Children are not copied."""
    c = o.copy()
    c.data = o.data.copy()
    c.name = name or (o.name + '_R')
    S = Matrix.Scale(-1, 4, (0, 1, 0))
    c.data.transform(S)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(c.data)
    bm.free()
    c.location = (o.location.x, -o.location.y, o.location.z)
    e = o.rotation_euler
    c.rotation_euler = Euler((-e.x, e.y, -e.z), 'XYZ')
    link(c, parent if parent is not None else o.parent)
    return c


def mirror_tree(root, parent=None, suffix='_R'):
    """Mirror an object and its whole child hierarchy across Y (expects root parent at origin)."""
    if root.type == 'EMPTY':
        c = bpy.data.objects.new(root.name + suffix, None)
        link(c, parent if parent is not None else root.parent)
        c.location = (root.location.x, -root.location.y, root.location.z)
        e = root.rotation_euler
        c.rotation_euler = Euler((-e.x, e.y, -e.z), 'XYZ')
        c.scale = root.scale.copy()
        for k in root.keys():
            c[k] = root[k]
    else:
        c = mirror_y(root, root.name + suffix, parent if parent is not None else root.parent)
    for ch in list(root.children):
        _mirror_child(ch, c, suffix)
    return c


def _mirror_child(ch, new_parent, suffix):
    # children live in parent-local space; mirroring the parent already flips the frame, so a child
    # just needs its local transform mirrored the same way.
    if ch.type == 'EMPTY':
        c = bpy.data.objects.new(ch.name + suffix, None)
    else:
        c = ch.copy()
        c.data = ch.data.copy()
        c.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
        bm = bmesh.new()
        bm.from_mesh(c.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(c.data)
        bm.free()
        c.name = ch.name + suffix
    link(c, new_parent)
    c.location = (ch.location.x, -ch.location.y, ch.location.z)
    e = ch.rotation_euler
    c.rotation_euler = Euler((-e.x, e.y, -e.z), 'XYZ')
    c.scale = ch.scale.copy()
    for g in list(ch.children):
        _mirror_child(g, c, suffix)
    return c


# ------------------------------------------------------------------ decals / stencils
def stencil(name, text, target, loc, rot=(math.pi / 2, 0, 0), size=0.35, mat=None, parent=None, offset=0.004):
    """Painted marking: text mesh shrink-wrapped onto `target` surface (e.g. 'U.S. ARMY').
    loc/rot place the flat text near the surface; rot default stands it up facing -Y."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = text
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.extrude = 0.0
    tmp = bpy.data.objects.new(name + '_c', cu)
    link(tmp)
    tmp.location = loc
    tmp.rotation_euler = rot
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    o = bpy.data.objects.new(name, me)
    link(o, parent)
    o.matrix_world = tmp.matrix_world.copy()
    bpy.data.objects.remove(tmp)
    if mat is not None:
        me.materials.append(mat)
    # subdivide so it can follow curvature
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    sw = o.modifiers.new('wrap', 'SHRINKWRAP')
    sw.target = target
    sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'OUTSIDE_SURFACE'
    sw.offset = offset
    return o


def star_mesh(name, r, loc, rot, target, mat, parent=None, offset=0.004, points=5, inner=0.38):
    """Flat star insignia (e.g. Soviet red star) wrapped onto target."""
    verts = [(0, 0, 0)]
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        rr = r if i % 2 == 0 else r * inner
        verts.append((rr * math.cos(a), rr * math.sin(a), 0))
    faces = [(0, 1 + i, 1 + (i + 1) % (points * 2)) for i in range(points * 2)]
    o = mesh_obj(name, verts, faces, parent, mat, smooth=False)
    o.location = loc
    o.rotation_euler = rot
    sw = o.modifiers.new('wrap', 'SHRINKWRAP')
    sw.target = target
    sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sw.wrap_mode = 'OUTSIDE_SURFACE'
    sw.offset = offset
    return o


# ------------------------------------------------------------------ materials
def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return nt, bsdf


def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _lines(nt, coord, spacing, width):
    """1 on a thin line every `spacing` metres of a scalar coordinate, else 0."""
    f = _math(nt, 'DIVIDE', coord, spacing)
    f = _math(nt, 'ADD', f, 0.5)
    f = _math(nt, 'FRACT', f)
    f = _math(nt, 'SUBTRACT', f, 0.5)
    f = _math(nt, 'ABSOLUTE', f)
    f = _math(nt, 'MULTIPLY', f, spacing)          # distance (m) to nearest line
    return _math(nt, 'LESS_THAN', f, width)


def _rgb(c):
    return (c[0], c[1], c[2], 1.0)


def paint(name, color, camo=None, camo_scale=0.35, rough=0.55, metallic=0.0, panel=(0.9, 0.55),
          panel_w=0.004, rivets=True, grime=0.45, wear=0.25, wear_color=(0.42, 0.42, 0.40),
          soot=0.0, clearcoat=0.0):
    """Baked military paint. color = base sRGB-ish linear tuple; camo = list of extra colours
    for a disruptive pattern; panel = (spacing along X, spacing along Z) metres."""
    mat = bpy.data.materials.new(name)
    mat['bake'] = 1
    mat['metallic'] = metallic
    nt, bsdf = _nodes(mat)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    X, Y, Z = sep.outputs[0], sep.outputs[1], sep.outputs[2]

    # base / camo colour
    col = nt.nodes.new('ShaderNodeRGB')
    col.outputs[0].default_value = _rgb(color)
    base = col.outputs[0]
    if camo:
        for i, cc in enumerate(camo):
            nz = nt.nodes.new('ShaderNodeTexNoise')
            nz.inputs['Scale'].default_value = camo_scale * (1 + 0.35 * i)
            nz.inputs['Detail'].default_value = 3.0
            nz.inputs['Roughness'].default_value = 0.55
            nz.noise_dimensions = '4D'
            nz.inputs['W'].default_value = 3.1 * (i + 1)
            nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.interpolation = 'CONSTANT'
            ramp.color_ramp.elements[0].position = 0.0
            ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
            ramp.color_ramp.elements[1].position = 0.56 + 0.03 * i
            ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
            nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
            c2 = nt.nodes.new('ShaderNodeRGB')
            c2.outputs[0].default_value = _rgb(cc)
            mix = nt.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            nt.links.new(ramp.outputs['Color'], mix.inputs['Factor'])
            nt.links.new(base, mix.inputs[6])
            nt.links.new(c2.outputs[0], mix.inputs[7])
            base = mix.outputs[2]

    # subtle paint mottling (faded, touched-up panels)
    mot = nt.nodes.new('ShaderNodeTexNoise')
    mot.inputs['Scale'].default_value = 2.2
    mot.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], mot.inputs['Vector'])
    motf = _math(nt, 'ADD', _math(nt, 'MULTIPLY', mot.outputs['Fac'], 0.22), 0.89)
    m1 = nt.nodes.new('ShaderNodeMix')
    m1.data_type = 'RGBA'
    m1.blend_type = 'MULTIPLY'
    m1.inputs['Factor'].default_value = 1.0
    nt.links.new(base, m1.inputs[6])
    cvec = nt.nodes.new('ShaderNodeCombineColor')
    for i in range(3):
        nt.links.new(motf, cvec.inputs[i])
    nt.links.new(cvec.outputs[0], m1.inputs[7])
    base = m1.outputs[2]

    # grime: AO-driven dirt + streaks running down (Z) and aft (-X)
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
    ao.samples = 8
    ao.inputs['Distance'].default_value = 0.6
    streak = nt.nodes.new('ShaderNodeTexNoise')
    streak.inputs['Scale'].default_value = 6.0
    streak.inputs['Detail'].default_value = 8.0
    mapn = nt.nodes.new('ShaderNodeMapping')
    mapn.inputs['Scale'].default_value = (0.35, 1.0, 5.0)
    nt.links.new(tc.outputs['Object'], mapn.inputs['Vector'])
    nt.links.new(mapn.outputs[0], streak.inputs['Vector'])
    dirt = _math(nt, 'SUBTRACT', 1.0, ao.outputs['AO'])
    dirt = _math(nt, 'MULTIPLY', dirt, 1.6)
    dirt = _math(nt, 'ADD', dirt, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', streak.outputs['Fac'], 0.45, True), 0.9), True)
    dirt = _math(nt, 'MULTIPLY', dirt, grime, True)
    dcol = nt.nodes.new('ShaderNodeRGB')
    dcol.outputs[0].default_value = (0.045, 0.040, 0.032, 1)
    m2 = nt.nodes.new('ShaderNodeMix')
    m2.data_type = 'RGBA'
    nt.links.new(dirt, m2.inputs['Factor'])
    nt.links.new(base, m2.inputs[6])
    nt.links.new(dcol.outputs[0], m2.inputs[7])
    base = m2.outputs[2]

    # edge wear: convex edges (pointiness) chipped with noise
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    chip = nt.nodes.new('ShaderNodeTexNoise')
    chip.inputs['Scale'].default_value = 28.0
    chip.inputs['Detail'].default_value = 10.0
    nt.links.new(tc.outputs['Object'], chip.inputs['Vector'])
    edge = _math(nt, 'SUBTRACT', geo.outputs['Pointiness'], 0.53)
    edge = _math(nt, 'MULTIPLY', edge, 14.0, True)
    edge = _math(nt, 'MULTIPLY', edge, _math(nt, 'GREATER_THAN', chip.outputs['Fac'], 0.52))
    edge = _math(nt, 'MULTIPLY', edge, wear, True)
    wcol = nt.nodes.new('ShaderNodeRGB')
    wcol.outputs[0].default_value = _rgb(wear_color)
    m3 = nt.nodes.new('ShaderNodeMix')
    m3.data_type = 'RGBA'
    nt.links.new(edge, m3.inputs['Factor'])
    nt.links.new(base, m3.inputs[6])
    nt.links.new(wcol.outputs[0], m3.inputs[7])
    base = m3.outputs[2]

    # exhaust soot toward the tail-top (optional)
    if soot:
        sz = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 0.0, X), 0.12, True)
        sz = _math(nt, 'MULTIPLY', sz, soot, True)
        m4 = nt.nodes.new('ShaderNodeMix')
        m4.data_type = 'RGBA'
        nt.links.new(sz, m4.inputs['Factor'])
        nt.links.new(base, m4.inputs[6])
        sc = nt.nodes.new('ShaderNodeRGB')
        sc.outputs[0].default_value = (0.02, 0.02, 0.02, 1)
        nt.links.new(sc.outputs[0], m4.inputs[7])
        base = m4.outputs[2]

    # panel lines + rivets -> darkened colour and bump
    lines = None
    if panel:
        lx = _lines(nt, X, panel[0], panel_w)
        lz = _lines(nt, Z, panel[1], panel_w)
        lines = _math(nt, 'MAXIMUM', lx, lz)
        if rivets:
            # rivet rows just beside each panel line, pitch 4.5 cm
            rx = _math(nt, 'MULTIPLY', _lines(nt, _math(nt, 'ADD', X, 0.018), panel[0], 0.0045),
                       _lines(nt, Z, 0.045, 0.0045))
            rz = _math(nt, 'MULTIPLY', _lines(nt, _math(nt, 'ADD', Z, 0.018), panel[1], 0.0045),
                       _lines(nt, X, 0.045, 0.0045))
            riv = _math(nt, 'MAXIMUM', rx, rz)
        else:
            riv = None
        m5 = nt.nodes.new('ShaderNodeMix')
        m5.data_type = 'RGBA'
        nt.links.new(_math(nt, 'MULTIPLY', lines, 0.55), m5.inputs['Factor'])
        nt.links.new(base, m5.inputs[6])
        lc = nt.nodes.new('ShaderNodeRGB')
        lc.outputs[0].default_value = (0.02, 0.02, 0.018, 1)
        nt.links.new(lc.outputs[0], m5.inputs[7])
        base = m5.outputs[2]
        height = _math(nt, 'MULTIPLY', lines, -1.0)
        if riv is not None:
            height = _math(nt, 'ADD', height, _math(nt, 'MULTIPLY', riv, 0.6))
    else:
        height = None

    # micro surface (orange-peel paint) + bump
    micro = nt.nodes.new('ShaderNodeTexNoise')
    micro.inputs['Scale'].default_value = 180.0
    micro.inputs['Detail'].default_value = 4.0
    nt.links.new(tc.outputs['Object'], micro.inputs['Vector'])
    h = _math(nt, 'MULTIPLY', micro.outputs['Fac'], 0.08)
    if height is not None:
        h = _math(nt, 'ADD', h, height)
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.65
    bump.inputs['Distance'].default_value = 0.0015
    nt.links.new(h, bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    # roughness: base + dirt raises it, worn edges polish it
    r = _math(nt, 'ADD', rough, _math(nt, 'MULTIPLY', dirt, 0.25))
    r = _math(nt, 'SUBTRACT', r, _math(nt, 'MULTIPLY', edge, 0.3))
    r = _math(nt, 'ADD', r, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', mot.outputs['Fac'], 0.5), 0.12), True)
    nt.links.new(r, bsdf.inputs['Roughness'])
    nt.links.new(base, bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value = metallic
    if clearcoat:
        bsdf.inputs['Coat Weight'].default_value = clearcoat
    return mat


def simple(name, color, rough=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    nt, b = _nodes(mat)
    b.inputs['Base Color'].default_value = _rgb(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    return mat


def metal(name, color=(0.55, 0.56, 0.58), rough=0.32):
    return simple(name, color, rough, 1.0)


def rubber(name='rubber'):
    return simple(name, (0.018, 0.018, 0.018), 0.88, 0.0)


def glass(name='glass', tint=(0.55, 0.62, 0.6), rough=0.04):
    mat = bpy.data.materials.new(name)
    nt, b = _nodes(mat)
    b.inputs['Base Color'].default_value = _rgb(tint)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.5
    return mat


def emit(name, color, strength=8.0):
    """Light lens. Name must be emit_beacon / emit_red / emit_green / emit_white."""
    mat = bpy.data.materials.new(name)
    nt, b = _nodes(mat)
    b.inputs['Base Color'].default_value = _rgb(color)
    b.inputs['Emission Color'].default_value = _rgb(color)
    b.inputs['Emission Strength'].default_value = strength
    b.inputs['Roughness'].default_value = 0.2
    return mat


# ------------------------------------------------------------------ baking + export

def _mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def _baked_objects():
    out = []
    for o in _mesh_objects():
        if any(s.material and s.material.get('bake') for s in o.material_slots):
            out.append(o)
    return out


def _check_contract():
    bad = []
    for o in _mesh_objects():
        p = o
        while p.parent is not None:
            p = p.parent
        if not p.name.startswith('part_'):
            bad.append(o.name)
    if bad:
        raise RuntimeError('Meshes not under a part_<key> empty: %s' % bad[:20])


def unwrap(objs):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    # AABB packing without rotation: the concave/rotating packer stalls for hours on thousands of islands
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=False, shape_method='AABB', margin=0.0035)
    bpy.ops.object.mode_set(mode='OBJECT')


def _gpu(fn):
    """Serialise GPU-heavy work across concurrent Blender processes (laptop GPU has 4 GB VRAM)."""
    @functools.wraps(fn)
    def run(*a, **k):
        with open(os.path.join(WORK, 'gpu.lock'), 'w') as f:
            print('[gpu] waiting for lock:', fn.__name__, flush=True)
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                return fn(*a, **k)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    return run


def _bake_proxy(objs, mats):
    """One merged, modifier-applied copy of every paint object. Cycles re-syncs the whole scene for
    every selected object in every bake pass; baking one proxy turns ~600 syncs into 4. Each vertex
    keeps its original object-space position in attribute 'objco' and the paint shaders are re-pointed
    at it, so procedural camo / panel lines / rivets bake exactly as authored."""
    dg = bpy.context.evaluated_depsgraph_get()
    temps = []
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        co = [0.0] * (len(me.vertices) * 3)
        me.vertices.foreach_get('co', co)
        me.attributes.new('objco', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co)
        me.transform(o.matrix_world)
        t = bpy.data.objects.new('_bake_' + o.name, me)
        bpy.context.scene.collection.objects.link(t)
        temps.append(t)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for t in temps:
        t.select_set(True)
    bpy.context.view_layer.objects.active = temps[0]
    bpy.ops.object.join()
    proxy = bpy.context.view_layer.objects.active
    for m in mats:
        nt = m.node_tree
        for tc in [n for n in nt.nodes if n.type == 'TEX_COORD']:
            outs = [l.to_socket for l in nt.links if l.from_socket == tc.outputs['Object']]
            if not outs:
                continue
            at = nt.nodes.new('ShaderNodeAttribute')
            at.attribute_type = 'GEOMETRY'
            at.attribute_name = 'objco'
            for s in outs:
                nt.links.new(at.outputs['Vector'], s)
    for o in objs:
        o.hide_render = True
    return proxy


@_gpu
def bake(model, res=4096, samples=32):
    """UV-atlas every paint object, bake colour/roughness/normal/AO, rebuild export materials."""
    sc = bpy.context.scene
    objs = _baked_objects()
    if not objs:
        return
    if FAST:
        res, samples = 1024, 8
    unwrap(objs)
    sc.cycles.samples = samples
    sc.render.bake.margin = 6
    imgs = {}
    for kind in ('color', 'rough', 'normal', 'ao'):
        im = bpy.data.images.new('%s_%s' % (model, kind), res, res, alpha=False, float_buffer=False)
        im.colorspace_settings.name = 'sRGB' if kind == 'color' else 'Non-Color'
        imgs[kind] = im
    mats = sorted({s.material for o in objs for s in o.material_slots if s.material and s.material.get('bake')},
                  key=lambda m: m.name)
    nodes = {}
    for m in mats:
        n = m.node_tree.nodes.new('ShaderNodeTexImage')
        nodes[m.name] = n
    proxy = _bake_proxy(objs, mats)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    proxy.select_set(True)
    bpy.context.view_layer.objects.active = proxy
    for kind, btype, extra in (('color', 'DIFFUSE', {'pass_filter': {'COLOR'}}),
                               ('rough', 'ROUGHNESS', {}),
                               ('normal', 'NORMAL', {'normal_space': 'TANGENT'}),
                               ('ao', 'AO', {})):
        for m in mats:
            nodes[m.name].image = imgs[kind]
            m.node_tree.nodes.active = nodes[m.name]
        print('[bake]', model, kind, res, flush=True)
        bpy.ops.object.bake(type=btype, use_clear=True, margin=6, **extra)
    pme = proxy.data
    bpy.data.objects.remove(proxy)
    bpy.data.meshes.remove(pme)
    for o in objs:
        o.hide_render = False
    # multiply AO into albedo (contact shadows that survive any lighting)
    import numpy as np
    n = res * res * 4
    c = np.empty(n, dtype=np.float32); imgs['color'].pixels.foreach_get(c); c = c.reshape(-1, 4)
    a = np.empty(n, dtype=np.float32); imgs['ao'].pixels.foreach_get(a); a = a.reshape(-1, 4)[:, :1]
    c[:, :3] *= (0.25 + 0.75 * a)
    imgs['color'].pixels.foreach_set(c.ravel())
    for kind, im in imgs.items():
        if kind == 'ao':
            continue
        path = os.path.join(WORK, 'bake', '%s_%s.png' % (model, kind))
        im.filepath_raw = path
        im.file_format = 'PNG'
        im.save()
    # swap every baked material to a plain image-driven Principled BSDF
    for m in mats:
        metal_v = float(m.get('metallic', 0.0))
        nt, b = _nodes(m)
        tc = nt.nodes.new('ShaderNodeTexImage')
        tc.image = imgs['color']
        tr = nt.nodes.new('ShaderNodeTexImage')
        tr.image = imgs['rough']
        tn = nt.nodes.new('ShaderNodeTexImage')
        tn.image = imgs['normal']
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tc.outputs['Color'], b.inputs['Base Color'])
        nt.links.new(tr.outputs['Color'], b.inputs['Roughness'])
        nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
        b.inputs['Metallic'].default_value = metal_v
    for im in (imgs['ao'],):
        bpy.data.images.remove(im)


def world(hdri=HDRI, strength=1.0, rot_z=0.0):
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new('World')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(hdri, check_existing=True)
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, rot_z)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs['Surface'])


def bounds():
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    dg = bpy.context.evaluated_depsgraph_get()
    for o in _mesh_objects():
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
    return lo, hi


VIEWS = {
    'front34': (math.radians(35), math.radians(12)),
    'side': (math.radians(90), math.radians(4)),
    'rear34': (math.radians(145), math.radians(14)),
    'front': (math.radians(0), math.radians(6)),
    'top34': (math.radians(55), math.radians(42)),
}


@_gpu
def preview(model, views=('front34', 'side', 'rear34', 'front', 'top34'), res=(1280, 720), samples=64):
    """Cycles stills from standard angles (azimuth measured from the nose, +Y side)."""
    sc = bpy.context.scene
    if GEO:
        views, res, samples = ('front34', 'side', 'rear34'), (800, 450), 16
    elif FAST:
        samples = 24
    world()
    lo, hi = bounds()
    ctr = (lo + hi) / 2
    size = (hi - lo).length
    gp = bpy.data.meshes.new('ground')
    gp.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('_ground', gp)
    sc.collection.objects.link(g)
    g.is_shadow_catcher = True
    cam_d = bpy.data.cameras.new('cam')
    cam_d.lens = 50
    cam = bpy.data.objects.new('_cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    paths = []
    for v in views:
        az, el = VIEWS[v]
        d = size * 0.95
        pos = ctr + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * d
        pos.z = max(pos.z, 0.6)
        cam.location = pos
        cam.rotation_euler = (ctr - pos).to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(WORK, 'renders', '%s_%s.png' % (model, v))
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
        print('[preview]', p, flush=True)
    bpy.data.objects.remove(g)
    bpy.data.objects.remove(cam)
    return paths


def export(model):
    _check_contract()
    path = os.path.abspath(os.path.join(OUT, model + '.glb'))
    for o in bpy.context.scene.objects:
        o.select_set(o.name[:1] != '_')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
              export_yup=True, export_extras=True, export_lights=False, export_cameras=False,
              export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
              export_draco_position_quantization=14, export_draco_normal_quantization=10,
              export_draco_texcoord_quantization=14, export_tangents=False,
              export_image_quality=92)   # default 75 smears panel lines / rivets at 4096
    try:
        bpy.ops.export_scene.gltf(export_image_format='WEBP', **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(export_image_format='JPEG', **kw)
    print('[export]', path, os.path.getsize(path) // 1024, 'KB', flush=True)
    return path


def stats():
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for o in _mesh_objects():
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    lo, hi = bounds()
    print('[stats] meshes=%d tris=%d size=%.2fx%.2fx%.2f m' % (len(_mesh_objects()), tris, *(hi - lo)), flush=True)


def finish(model):
    """Standard end of every model script: stats, bake, export, optional preview renders."""
    stats()
    if not GEO:
        bake(model)
        export(model)
    if PREVIEW:
        preview(model)
