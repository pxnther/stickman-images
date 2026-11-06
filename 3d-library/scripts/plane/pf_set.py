"""Plane-fall Short: procedural sets (sky column, lake, snow slope, jungle), props (fuselage piece, seat row), worlds.
Every set sits at the origin in its own collection; the render queue shows one set per shot."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)

def coll(name):
    c = D.collections.get(name)
    if c is None:
        c = D.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        if o.get('pf_gen'): D.objects.remove(o, do_unlink=True)
    return c
def obj(name, me, col):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    o = D.objects.new(name, me); col.objects.link(o); o['pf_gen'] = 1; return o
def nodes_mat(name):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); return m, nt
def N(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k.startswith('in') and k[2:].isdigit(): n.inputs[int(k[2:])].default_value = v
        elif k.startswith('i_'): n.inputs[k[2:].replace('_', ' ')].default_value = v
        else: setattr(n, k, v)
    return n
def L(nt, a, b): nt.links.new(a, b)
def pbsdf(name, col, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emis=0.0, coat=0.0, ecol=None):
    m, nt = nodes_mat(name)
    b = N(nt, 'ShaderNodeBsdfPrincipled'); o = N(nt, 'ShaderNodeOutputMaterial'); L(nt, b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat
    if emis: b.inputs['Emission Color'].default_value = (*(ecol or col), 1); b.inputs['Emission Strength'].default_value = emis
    return m
def grid_mesh(name, sx, sy, nx, ny, hf=None):
    me = D.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=1.0)
    for v in bm.verts:
        v.co.x *= sx / 2; v.co.y *= sy / 2
        if hf: v.co.z = hf(v.co.x, v.co.y)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me
def nz(x, y, s=1.0):
    return (math.sin(x * 0.013 * s + 1.3) * math.cos(y * 0.011 * s + 0.4) + 0.5 * math.sin(x * 0.031 * s + y * 0.027 * s) + 0.25 * math.sin(x * 0.071 * s - y * 0.063 * s + 2.0))

# ================= SKY COLUMN (ground far below, cloud carpet, wisps) =================
SKY = coll('PF_SKY')
m, nt = nodes_mat('PF_Ground')
tc = N(nt, 'ShaderNodeTexCoord'); out = N(nt, 'ShaderNodeOutputMaterial'); bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=0.9)
sep = N(nt, 'ShaderNodeSeparateXYZ'); L(nt, tc.outputs['Object'], sep.inputs[0])
def cell(scx, scy, rot, seed):
    # field cells: floor(rotated coords / size) -> white noise -> random 0..1
    vr = N(nt, 'ShaderNodeVectorRotate', rotation_type='Z_AXIS'); vr.inputs['Angle'].default_value = rot
    L(nt, tc.outputs['Object'], vr.inputs['Vector'])
    mp = N(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scx, 1 / scy, 1); L(nt, vr.outputs[0], mp.inputs['Vector'])
    fl = N(nt, 'ShaderNodeVectorMath', operation='FLOOR'); L(nt, mp.outputs[0], fl.inputs[0])
    wn = N(nt, 'ShaderNodeTexWhiteNoise', noise_dimensions='3D')
    ad = N(nt, 'ShaderNodeVectorMath', operation='ADD'); ad.inputs[1].default_value = (seed, seed * 2, 0); L(nt, fl.outputs[0], ad.inputs[0])
    L(nt, ad.outputs[0], wn.inputs['Vector'])
    return wn.outputs['Value']
c1 = cell(180, 260, 0.3, 3.0); c2 = cell(140, 200, 1.1, 7.0)
big = N(nt, 'ShaderNodeTexNoise', i_Scale=0.00025, i_Detail=4.0); L(nt, tc.outputs['Object'], big.inputs['Vector'])
mixc = N(nt, 'ShaderNodeMix', data_type='FLOAT'); L(nt, big.outputs['Fac'], mixc.inputs['Factor']); L(nt, c1, mixc.inputs[2]); L(nt, c2, mixc.inputs[3])
ramp = N(nt, 'ShaderNodeValToRGB'); L(nt, mixc.outputs[0], ramp.inputs[0])
els = ramp.color_ramp.elements; ramp.color_ramp.interpolation = 'CONSTANT'
cols = [(0.0, (0.16, 0.24, 0.07)), (0.18, (0.30, 0.36, 0.12)), (0.33, (0.52, 0.47, 0.22)), (0.48, (0.22, 0.30, 0.10)),
        (0.62, (0.36, 0.27, 0.16)), (0.74, (0.45, 0.42, 0.18)), (0.86, (0.20, 0.28, 0.09))]
els[0].position, els[0].color = cols[0][0], (*cols[0][1], 1); els[1].position, els[1].color = cols[1][0], (*cols[1][1], 1)
for p, c in cols[2:]:
    e = els.new(p); e.color = (*c, 1)
# forest patches (dark, bumpy) and snowy hills (white) via big noise masks
fn = N(nt, 'ShaderNodeTexNoise', i_Scale=0.0006, i_Detail=6.0); L(nt, tc.outputs['Object'], fn.inputs['Vector'])
fr = N(nt, 'ShaderNodeMapRange', i_From_Min=0.56, i_From_Max=0.6); L(nt, fn.outputs['Fac'], fr.inputs[0])
fine = N(nt, 'ShaderNodeTexNoise', i_Scale=0.05, i_Detail=4.0); L(nt, tc.outputs['Object'], fine.inputs['Vector'])
fcol = N(nt, 'ShaderNodeMix', data_type='RGBA'); fcol.inputs[6].default_value = (0.04, 0.09, 0.03, 1); fcol.inputs[7].default_value = (0.09, 0.15, 0.05, 1)
L(nt, fine.outputs['Fac'], fcol.inputs[0])
m1 = N(nt, 'ShaderNodeMix', data_type='RGBA'); L(nt, fr.outputs[0], m1.inputs[0]); L(nt, ramp.outputs[0], m1.inputs[6]); L(nt, fcol.outputs[2], m1.inputs[7])
sn = N(nt, 'ShaderNodeTexNoise', i_Scale=0.00018, i_Detail=5.0); L(nt, tc.outputs['Object'], sn.inputs['Vector'])
grad = N(nt, 'ShaderNodeMapRange', i_From_Min=0.62, i_From_Max=0.68); L(nt, sn.outputs['Fac'], grad.inputs[0])
m2 = N(nt, 'ShaderNodeMix', data_type='RGBA'); m2.inputs[7].default_value = (0.85, 0.88, 0.93, 1); L(nt, grad.outputs[0], m2.inputs[0]); L(nt, m1.outputs[2], m2.inputs[6])
# aerial haze by distance
cd = N(nt, 'ShaderNodeCameraData'); hz = N(nt, 'ShaderNodeMath', operation='MULTIPLY', in1=-1 / 9000.0)
L(nt, cd.outputs['View Distance'], hz.inputs[0]); ex = N(nt, 'ShaderNodeMath', operation='EXPONENT'); L(nt, hz.outputs[0], ex.inputs[0])
inv = N(nt, 'ShaderNodeMath', operation='SUBTRACT', in0=1.0); L(nt, ex.outputs[0], inv.inputs[1])
hzm = N(nt, 'ShaderNodeMix', data_type='RGBA'); hzm.inputs[7].default_value = (0.55, 0.66, 0.82, 1); L(nt, inv.outputs[0], hzm.inputs[0]); L(nt, m2.outputs[2], hzm.inputs[6])
L(nt, hzm.outputs[2], bs.inputs['Base Color']); L(nt, bs.outputs[0], out.inputs[0])
em = N(nt, 'ShaderNodeEmission'); L(nt, hzm.outputs[2], em.inputs[0])
GROUND_MAT = m
g = obj('PF_ground', grid_mesh('PF_ground', 24000, 24000, 4, 4), SKY); g.data.materials.append(m)
# lake disc on the ground, seen from altitude
lake_far = obj('PF_lake_far', D.meshes.new('PF_lake_far'), SKY)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=1.0, segments=64)
for v in bm.verts:
    a = math.atan2(v.co.y, v.co.x); v.co.x *= 520 * (1 + 0.18 * math.sin(3 * a)); v.co.y *= 340 * (1 + 0.12 * math.cos(5 * a + 1))
bm.to_mesh(lake_far.data); bm.free(); lake_far.location = (650, -420, 0.5)
lake_far.data.materials.append(pbsdf('PF_LakeFar', (0.03, 0.07, 0.10), rough=0.08, coat=1.0))
# cloud carpet
def cloud_mat(name, scale, cov, dens=1.0):
    m, nt = nodes_mat(name)
    tc = N(nt, 'ShaderNodeTexCoord'); n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=scale, i_Detail=10.0, i_Roughness=0.62)
    L(nt, tc.outputs['Object'], n1.inputs['Vector'])
    mr = N(nt, 'ShaderNodeMapRange', i_From_Min=cov, i_From_Max=cov + 0.16); L(nt, n1.outputs['Fac'], mr.inputs[0])
    bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=1.0); bs.inputs['Base Color'].default_value = (0.95, 0.96, 1.0, 1)
    bs.inputs['Emission Color'].default_value = (0.75, 0.82, 0.95, 1); bs.inputs['Emission Strength'].default_value = 0.22
    bump = N(nt, 'ShaderNodeBump', i_Strength=0.9, i_Distance=40.0); L(nt, n1.outputs['Fac'], bump.inputs['Height']); L(nt, bump.outputs[0], bs.inputs['Normal'])
    tr = N(nt, 'ShaderNodeBsdfTransparent'); mx = N(nt, 'ShaderNodeMixShader'); out = N(nt, 'ShaderNodeOutputMaterial')
    mul = N(nt, 'ShaderNodeMath', operation='MULTIPLY', in1=dens); L(nt, mr.outputs[0], mul.inputs[0])
    L(nt, mul.outputs[0], mx.inputs[0]); L(nt, tr.outputs[0], mx.inputs[1]); L(nt, bs.outputs[0], mx.inputs[2]); L(nt, mx.outputs[0], out.inputs[0])
    m.surface_render_method = 'DITHERED'
    return m
for i, (z, sc_, cov) in enumerate(((2800, 0.00035, 0.42), (2650, 0.0005, 0.47), (2950, 0.0007, 0.55))):
    o = obj(f'PF_cloud{i}', grid_mesh(f'PF_cloud{i}', 120000, 120000, 1, 1), SKY); o.location = (0, 0, z)
    o.data.materials.append(cloud_mat(f'PF_Cloud{i}', sc_, cov)); o.visible_shadow = False
# wisps to fall through (camera-facing billboards)
WISP = D.materials.get('PF_Wisp')
m, nt = nodes_mat('PF_Wisp')
tc = N(nt, 'ShaderNodeTexCoord'); gr = N(nt, 'ShaderNodeTexGradient', gradient_type='SPHERICAL'); mp = N(nt, 'ShaderNodeMapping')
mp.inputs['Scale'].default_value = (2, 2, 2); L(nt, tc.outputs['Generated'], mp.inputs['Vector'])
sub = N(nt, 'ShaderNodeVectorMath', operation='SUBTRACT'); sub.inputs[1].default_value = (1, 1, 1); L(nt, mp.outputs[0], sub.inputs[0]); L(nt, sub.outputs[0], gr.inputs[0])
n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=3.0, i_Detail=8.0); L(nt, tc.outputs['Generated'], n1.inputs['Vector'])
mu = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); L(nt, gr.outputs['Fac'], mu.inputs[0]); L(nt, n1.outputs['Fac'], mu.inputs[1])
mr = N(nt, 'ShaderNodeMapRange', i_From_Min=0.08, i_From_Max=0.45, i_To_Max=0.85); L(nt, mu.outputs[0], mr.inputs[0])
e = N(nt, 'ShaderNodeEmission', i_Strength=1.1); e.inputs[0].default_value = (0.92, 0.94, 0.98, 1)
tr = N(nt, 'ShaderNodeBsdfTransparent'); mx = N(nt, 'ShaderNodeMixShader'); out = N(nt, 'ShaderNodeOutputMaterial')
L(nt, mr.outputs[0], mx.inputs[0]); L(nt, tr.outputs[0], mx.inputs[1]); L(nt, e.outputs[0], mx.inputs[2]); L(nt, mx.outputs[0], out.inputs[0])
m.surface_render_method = 'BLENDED'; m.use_backface_culling = False; WISP = m
WISPS = []
rw = random.Random(4)
wme = grid_mesh('PF_wisp', 1, 1, 1, 1); wme.materials.append(WISP)
for i in range(70):
    o = obj(f'PF_wisp{i:02d}', wme, SKY)
    o.location = (rw.uniform(-70, 70), rw.uniform(-70, 70), rw.uniform(2560, 3060)); s = rw.uniform(40, 130); o.scale = (s, s * rw.uniform(0.5, 0.9), 1)
    o.visible_shadow = False; WISPS.append(o)

# ================= AIRLINER (procedural, nose along +Y) =================
PLANE = coll('PF_PLANE')
WHITEP = pbsdf('PF_PlaneWhite', (0.88, 0.89, 0.9), rough=0.28, coat=0.5)
BELLY = pbsdf('PF_PlaneBelly', (0.55, 0.57, 0.6), rough=0.35, metal=0.3)
DARK = pbsdf('PF_PlaneDark', (0.05, 0.06, 0.07), rough=0.2, coat=1.0)
TAILC = pbsdf('PF_PlaneTail', (0.05, 0.25, 0.55), rough=0.3, coat=0.5)
def loft(bm, prof, nseg=32, squash=1.0):
    """prof: list of (y, radius, zoff); circular sections along +Y"""
    rings = []
    for y, r, zo in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / nseg), y, zo + r * squash * math.sin(2 * math.pi * i / nseg))) for i in range(nseg)]
        rings.append(ring)
    for j in range(len(rings) - 1):
        for i in range(nseg):
            bm.faces.new((rings[j][i], rings[j][(i + 1) % nseg], rings[j + 1][(i + 1) % nseg], rings[j + 1][i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
def wing(bm, root_y, root_c, tip_y, tip_c, span, z, sweep, th, side, dihedral=0.06, vertical=False):
    pts = []
    for (x, y0, c) in ((0.0, root_y, root_c), (span, tip_y, tip_c)):
        yy = y0 - sweep * x / span
        zz = z + (0 if vertical else dihedral * x)
        pts.append((x, yy, zz, c))
    verts = []
    for (x, yy, zz, c) in pts:
        t = th * c
        for (dy, dz) in ((0, 0), (-c * 0.3, t), (-c, 0), (-c * 0.3, -t)):
            if vertical: verts.append(bm.verts.new((dz * side, yy + dy, zz + x)))
            else: verts.append(bm.verts.new((side * x, yy + dy, zz + dz)))
    for i in range(4): bm.faces.new((verts[i], verts[(i + 1) % 4], verts[4 + (i + 1) % 4], verts[4 + i]))
    bm.faces.new(verts[0:4][::-1]); bm.faces.new(verts[4:8])
AIRLINER = D.objects.get('PF_airliner')
if AIRLINER: D.objects.remove(AIRLINER, do_unlink=True)
me = D.meshes.new('PF_airliner'); bm = bmesh.new()
R_ = 1.95
prof = [(17.2, 0.05, -0.35), (16.9, 0.75, -0.25), (16.2, 1.45, -0.1), (15.0, 1.85, 0.0), (13.5, R_, 0.0)]
prof += [(y, R_, 0.0) for y in (8.0, 0.0, -6.0)]
prof += [(-9.0, 1.7, 0.25), (-12.5, 1.05, 0.65), (-15.2, 0.35, 1.0), (-15.6, 0.08, 1.05)]
loft(bm, prof, 40)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True; p.material_index = 0 if p.center.z > -0.6 else 1
me.materials.append(WHITEP); me.materials.append(BELLY)
AIRLINER = obj('PF_airliner', me, PLANE)
sm = AIRLINER.modifiers.new('sub', 'SUBSURF'); sm.levels = 1; sm.render_levels = 2
def part(name, build, mat, parent):
    me = D.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = obj(name, me, PLANE); o.parent = parent; return o
part('PF_wings', lambda bm: [wing(bm, 3.5, 6.2, -2.5, 1.6, 14.4, -0.9, 6.0, 0.06, sd) for sd in (1, -1)], WHITEP, AIRLINER)
part('PF_htail', lambda bm: [wing(bm, -11.8, 3.2, -14.3, 1.2, 6.2, 0.75, 2.6, 0.06, sd, 0.12) for sd in (1, -1)], WHITEP, AIRLINER)
part('PF_vtail', lambda bm: wing(bm, -10.0, 5.2, -14.4, 1.8, 6.8, 1.4, 4.6, 0.05, 1, vertical=True), TAILC, AIRLINER)
def engines(bm):
    for sd in (1, -1):
        g_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.95, radius2=0.8, depth=3.6)
        for v in g_['verts']: v.co = Matrix.Rotation(math.radians(-90), 3, 'X') @ v.co + V(sd * 5.0, 3.6, -1.75)
part('PF_engines', engines, BELLY, AIRLINER)
def windows(bm):
    for sd in (1, -1):
        for k in range(26):
            y = 11.5 - k * 0.78
            if abs(y - 3.0) < 0.5: continue
            g_ = bmesh.ops.create_circle(bm, cap_ends=True, radius=0.14, segments=12)
            for v in g_['verts']: v.co = V(sd * (R_ + 0.015), y + v.co.x * 0.8, 0.45 + v.co.y * 1.15)
        g_ = bmesh.ops.create_circle(bm, cap_ends=True, radius=0.5, segments=4)   # cockpit window band
    for sd in (1, -1):
        for k in range(3):
            q = [V(sd * (1.25 - 0.18 * k), 15.75 - 0.32 * k, 0.55), V(sd * (1.12 - 0.18 * k), 15.45 - 0.32 * k, 0.55), V(sd * (1.06 - 0.18 * k), 15.45 - 0.32 * k, 0.85), V(sd * (1.18 - 0.18 * k), 15.75 - 0.32 * k, 0.85)]
            bm.faces.new([bm.verts.new(p) for p in q])
part('PF_planewin', windows, DARK, AIRLINER)
# ================= PROPS: fuselage piece + seat row =================
PROPS = coll('PF_PROPS')
PAINT = WHITEP
INNER = pbsdf('PF_Inner', (0.42, 0.42, 0.44), rough=0.7)
WINM = pbsdf('PF_Window', (0.02, 0.025, 0.03), rough=0.05, coat=1.0)
FAB = pbsdf('PF_Fabric', (0.06, 0.12, 0.30), rough=0.9)
METAL = pbsdf('PF_Metal', (0.55, 0.56, 0.58), rough=0.35, metal=1.0)
HEADC = pbsdf('PF_Headrest', (0.85, 0.85, 0.82), rough=0.8)
rf = random.Random(9)
me = D.meshes.new('PF_fuselage'); bm = bmesh.new()
R0 = 1.88; LEN = 6.0; NA = 48; NL = 14
rings = []
for j in range(NL + 1):
    ring = []
    for i in range(NA):
        a = 2 * math.pi * i / NA
        x = -LEN / 2 + LEN * j / NL
        if j == 0: x -= rf.uniform(0, 0.9)
        if j == NL: x += rf.uniform(0, 0.9)
        ring.append(bm.verts.new((x, R0 * math.cos(a), R0 * math.sin(a))))
    rings.append(ring)
for j in range(NL):
    for i in range(NA):
        bm.faces.new((rings[j][i], rings[j][(i + 1) % NA], rings[j + 1][(i + 1) % NA], rings[j + 1][i]))
bm.normal_update(); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
fus = obj('PF_fuselage', me, PROPS); me.materials.append(PAINT); me.materials.append(INNER)
sol = fus.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.09; sol.material_offset = 1; sol.use_flip_normals = False
wme = D.meshes.new('PF_windows'); bm = bmesh.new()
for side in (1, -1):
    for k in range(9):
        x = -2.6 + k * 0.62
        a = math.radians(14) * side
        c = V(x, side * (R0 + 0.006) * math.cos(math.radians(14)), (R0 + 0.006) * math.sin(math.radians(14)))
        g_ = bmesh.ops.create_circle(bm, cap_ends=True, radius=0.13, segments=16)
        for v in g_['verts']:
            v.co = V(v.co.x * 0.8, 0, v.co.y * 1.2)
            v.co = Matrix.Rotation(-a if side > 0 else -a, 3, 'X') @ v.co + c
bm.to_mesh(wme); bm.free(); wins = obj('PF_windows', wme, PROPS); wme.materials.append(WINM); wins.parent = fus
def box(bm, c, s, rot=0.0):
    g_ = bmesh.ops.create_cube(bm, size=1.0)
    for v in g_['verts']:
        v.co = V(v.co.x * s[0], v.co.y * s[1], v.co.z * s[2]); v.co = Matrix.Rotation(rot, 3, 'X') @ v.co + V(*c)
def seat_row(name, col):
    root = D.objects.get(name)
    if root: D.objects.remove(root, do_unlink=True)
    root = D.objects.new(name, None); col.objects.link(root); root['pf_gen'] = 1
    parts = {'fab': FAB, 'met': METAL, 'head': HEADC}
    for key, mat in parts.items():
        me = D.meshes.new(name + '_' + key); bm = bmesh.new()
        for k in range(3):
            x = (k - 1) * 0.5
            if key == 'fab':
                box(bm, (x, 0.0, 0.47), (0.46, 0.5, 0.12)); box(bm, (x, 0.24, 0.85), (0.46, 0.1, 0.68), rot=-0.18)
            if key == 'head':
                box(bm, (x, 0.29, 1.08), (0.40, 0.11, 0.18), rot=-0.18)
            if key == 'met':
                box(bm, (x - 0.25, 0.0, 0.58), (0.05, 0.48, 0.05)); box(bm, (x + 0.25, 0.0, 0.58), (0.05, 0.48, 0.05))
        if key == 'met':
            box(bm, (0, 0.0, 0.36), (1.5, 0.06, 0.06)); box(bm, (-0.55, 0.0, 0.18), (0.05, 0.4, 0.36)); box(bm, (0.55, 0.0, 0.18), (0.05, 0.4, 0.36))
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.015, segments=2, affect='EDGES')
        bm.to_mesh(me); bm.free(); me.materials.append(mat)
        o = obj(name + '_' + key, me, col); o.parent = root
    return root
SEATS = seat_row('PF_seats', PROPS)
inner_seats = seat_row('PF_seats_in', PROPS); inner_seats.parent = fus; inner_seats.location = (0.6, -0.5, -1.15); inner_seats.rotation_euler = (0, 0, math.pi / 2)

# ================= LAKE (pocket set) =================
LAKE = coll('PF_LAKE')
m, nt = nodes_mat('PF_Water')
bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=0.03); bs.inputs['Base Color'].default_value = (0.02, 0.06, 0.07, 1); bs.inputs['Coat Weight'].default_value = 1.0
tc = N(nt, 'ShaderNodeTexCoord'); w1 = N(nt, 'ShaderNodeTexWave', wave_type='BANDS', i_Scale=0.35, i_Distortion=6.0, i_Detail=4.0)
n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=1.8, i_Detail=6.0)
L(nt, tc.outputs['Object'], w1.inputs['Vector']); L(nt, tc.outputs['Object'], n1.inputs['Vector'])
ad = N(nt, 'ShaderNodeMath', operation='ADD'); L(nt, w1.outputs['Fac'], ad.inputs[0]); L(nt, n1.outputs['Fac'], ad.inputs[1])
bump = N(nt, 'ShaderNodeBump', i_Strength=0.25, i_Distance=0.15); L(nt, ad.outputs[0], bump.inputs['Height']); L(nt, bump.outputs[0], bs.inputs['Normal'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bs.outputs[0], out.inputs[0])
water = obj('PF_water', grid_mesh('PF_water', 900, 900, 1, 1), LAKE); water.data.materials.append(m)
GRASS = pbsdf('PF_Grass', (0.12, 0.2, 0.06), rough=0.95)
def shore(x, y):
    r = math.hypot(x, y); return max(-2.0, min(14.0, (r - 260) * 0.06 + 2.5 * nz(x, y, 3)))
sh = obj('PF_shore', grid_mesh('PF_shore', 1600, 1600, 120, 120, shore), LAKE); sh.data.materials.append(GRASS)

# ================= SNOW SLOPE =================
SNOW = coll('PF_SNOW')
m, nt = nodes_mat('PF_Snow')
bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=0.55); bs.inputs['Base Color'].default_value = (0.90, 0.93, 0.98, 1)
bs.inputs['Subsurface Weight'].default_value = 0.25; bs.inputs['Subsurface Radius'].default_value = (0.4, 0.6, 1.0)
tc = N(nt, 'ShaderNodeTexCoord'); n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=0.8, i_Detail=8.0); L(nt, tc.outputs['Object'], n1.inputs['Vector'])
n2 = N(nt, 'ShaderNodeTexNoise', i_Scale=60.0, i_Detail=2.0); L(nt, tc.outputs['Object'], n2.inputs['Vector'])
ad = N(nt, 'ShaderNodeMath', operation='ADD'); L(nt, n1.outputs['Fac'], ad.inputs[0]); L(nt, n2.outputs['Fac'], ad.inputs[1])
bump = N(nt, 'ShaderNodeBump', i_Strength=0.35, i_Distance=0.05); L(nt, ad.outputs[0], bump.inputs['Height']); L(nt, bump.outputs[0], bs.inputs['Normal'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bs.outputs[0], out.inputs[0])
SNOWM = m
SLOPE = math.radians(26)
def slope_h(x, y):
    return -math.tan(SLOPE) * x + 1.8 * nz(x, y, 4) + 0.4 * nz(x * 3, y * 3, 6)
sl = obj('PF_slope', grid_mesh('PF_slope', 700, 700, 160, 160, slope_h), SNOW); sl.data.materials.append(SNOWM)
# procedural snowy fir trees (Poly Haven geometry-node trees crash Blender on this PC)
m, nt = nodes_mat('PF_FirNeedle')
bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=0.85)
tc = N(nt, 'ShaderNodeTexCoord'); n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=6.0, i_Detail=8.0); L(nt, tc.outputs['Object'], n1.inputs['Vector'])
rp = N(nt, 'ShaderNodeValToRGB'); L(nt, n1.outputs['Fac'], rp.inputs[0])
rp.color_ramp.elements[0].color = (0.02, 0.06, 0.03, 1); rp.color_ramp.elements[1].color = (0.07, 0.16, 0.07, 1)
geo = N(nt, 'ShaderNodeNewGeometry'); sz = N(nt, 'ShaderNodeSeparateXYZ'); L(nt, geo.outputs['Normal'], sz.inputs[0])
n2 = N(nt, 'ShaderNodeTexNoise', i_Scale=3.0, i_Detail=4.0); L(nt, tc.outputs['Object'], n2.inputs['Vector'])
ad = N(nt, 'ShaderNodeMath', operation='ADD'); L(nt, sz.outputs['Z'], ad.inputs[0]); L(nt, n2.outputs['Fac'], ad.inputs[1])
mr = N(nt, 'ShaderNodeMapRange', i_From_Min=0.95, i_From_Max=1.15); L(nt, ad.outputs[0], mr.inputs[0])
mx = N(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs[7].default_value = (0.88, 0.92, 0.97, 1); L(nt, mr.outputs[0], mx.inputs[0]); L(nt, rp.outputs[0], mx.inputs[6])
L(nt, mx.outputs[2], bs.inputs['Base Color'])
bump = N(nt, 'ShaderNodeBump', i_Strength=0.7, i_Distance=0.2); L(nt, n1.outputs['Fac'], bump.inputs['Height']); L(nt, bump.outputs[0], bs.inputs['Normal'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bs.outputs[0], out.inputs[0])
FIRM = m; BARK = pbsdf('PF_Bark', (0.12, 0.08, 0.05), rough=0.9)
def fir_mesh(name, H_, R_, tiers, seed):
    rr = random.Random(seed); me = D.meshes.new(name); bm = bmesh.new()
    g_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.22 * H_ / 14, radius2=0.05, depth=H_)
    for v in g_['verts']: v.co.z += H_ / 2
    for f_ in {f for v in g_['verts'] for f in v.link_faces}: f_.material_index = 1
    for k in range(tiers):
        u = k / (tiers - 1)
        z0 = H_ * (0.18 + 0.78 * u); r = R_ * (1 - u) ** 0.9 + 0.25; hgt = H_ * 0.26 * (1 - 0.5 * u) + 0.6
        nseg = 18; top = bm.verts.new((0, 0, z0 + hgt)); ring = []
        for i in range(nseg):
            a = 2 * math.pi * i / nseg + rr.uniform(-0.08, 0.08)
            rad = r * (1.0 if i % 2 == 0 else 0.72) * rr.uniform(0.85, 1.1)
            ring.append(bm.verts.new((rad * math.cos(a), rad * math.sin(a), z0 - (0.35 if i % 2 == 0 else 0.0) * r * 0.5)))
        inner = [bm.verts.new((v.co.x * 0.35, v.co.y * 0.35, v.co.z + 0.25)) for v in ring]
        for i in range(nseg):
            bm.faces.new((top, ring[i], ring[(i + 1) % nseg]))
            bm.faces.new((ring[(i + 1) % nseg], ring[i], inner[i], inner[(i + 1) % nseg]))
    bm.to_mesh(me); bm.free(); me.materials.append(FIRM); me.materials.append(BARK)
    return me
FIRS = [fir_mesh(f'PF_firmesh{i}', h_, r_, t_, i) for i, (h_, r_, t_) in enumerate(((16, 3.6, 7), (12, 3.0, 6), (19, 4.0, 8)))]
rt = random.Random(12); k = 0
for i in range(520):
    x, y = rt.uniform(-300, 300), rt.uniform(-300, 300)
    if math.hypot(x, y) < 22 or (abs(y) < 7 and -45 < x < 45): continue
    if math.hypot(x - 14, y + 30) < 11: continue
    o = obj(f'PF_fir{k:03d}', FIRS[k % 3], SNOW)
    o.location = (x, y, slope_h(x, y) - 0.3); o.rotation_euler = (0, 0, rt.uniform(0, 6.28)); s_ = rt.uniform(0.75, 1.2); o.scale = (s_, s_, s_)
    k += 1

# ================= JUNGLE =================
JUNG = coll('PF_JUNGLE')
m, nt = nodes_mat('PF_Litter')
bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=0.9)
tc = N(nt, 'ShaderNodeTexCoord'); vo = N(nt, 'ShaderNodeTexVoronoi', i_Scale=6.0); L(nt, tc.outputs['Object'], vo.inputs['Vector'])
rp = N(nt, 'ShaderNodeValToRGB'); L(nt, vo.outputs['Distance'], rp.inputs[0])
rp.color_ramp.elements[0].color = (0.10, 0.06, 0.03, 1); rp.color_ramp.elements[1].color = (0.25, 0.17, 0.07, 1)
n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=0.3, i_Detail=5.0); L(nt, tc.outputs['Object'], n1.inputs['Vector'])
mx = N(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs[7].default_value = (0.05, 0.08, 0.03, 1); L(nt, n1.outputs['Fac'], mx.inputs[0]); L(nt, rp.outputs[0], mx.inputs[6])
L(nt, mx.outputs[2], bs.inputs['Base Color'])
bump = N(nt, 'ShaderNodeBump', i_Strength=0.6, i_Distance=0.03); L(nt, vo.outputs['Distance'], bump.inputs['Height']); L(nt, bump.outputs[0], bs.inputs['Normal'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bs.outputs[0], out.inputs[0])
fl = obj('PF_floor', grid_mesh('PF_floor', 500, 500, 80, 80, lambda x, y: 1.2 * nz(x, y, 6)), JUNG); fl.data.materials.append(m)
def variants(colname):
    """split a Poly Haven collection (variants placed side by side) into one hidden collection per variant at the origin"""
    c = D.collections.get(colname); out = []
    if not c: return out
    groups = {}
    for o in c.objects:
        if o.parent is None: groups.setdefault((round(o.location.x, 1), round(o.location.y, 1)), []).append(o)
    for i, (key, objs) in enumerate(sorted(groups.items())):
        vc = D.collections.get(f'V_{colname}_{i}') or D.collections.new(f'V_{colname}_{i}')
        for o in objs:
            if o.name not in vc.objects: vc.objects.link(o)
        vc.instance_offset = (key[0], key[1], 0); out.append(vc)
    if c.name in sc.collection.children: sc.collection.children.unlink(c)
    return out
LEAF = D.materials.get('PF_Leaf')
m, nt = nodes_mat('PF_Leaf')
bs = N(nt, 'ShaderNodeBsdfPrincipled', i_Roughness=0.6)
tc = N(nt, 'ShaderNodeTexCoord'); vo = N(nt, 'ShaderNodeTexVoronoi', i_Scale=3.0); L(nt, tc.outputs['Object'], vo.inputs['Vector'])
n1 = N(nt, 'ShaderNodeTexNoise', i_Scale=1.2, i_Detail=6.0); L(nt, tc.outputs['Object'], n1.inputs['Vector'])
rp = N(nt, 'ShaderNodeValToRGB'); L(nt, n1.outputs['Fac'], rp.inputs[0])
rp.color_ramp.elements[0].color = (0.03, 0.10, 0.02, 1); rp.color_ramp.elements[1].color = (0.16, 0.30, 0.05, 1)
L(nt, rp.outputs[0], bs.inputs['Base Color'])
bump = N(nt, 'ShaderNodeBump', i_Strength=1.0, i_Distance=0.4); L(nt, vo.outputs['Distance'], bump.inputs['Height']); L(nt, bump.outputs[0], bs.inputs['Normal'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bs.outputs[0], out.inputs[0]); LEAF = m
def canopy_tree(name, H_, R_, seed):
    rr = random.Random(seed); me = D.meshes.new(name); bm = bmesh.new()
    g_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.5 * H_ / 25, radius2=0.25, depth=H_)
    for v in g_['verts']: v.co.z += H_ / 2
    for f_ in {f for v in g_['verts'] for f in v.link_faces}: f_.material_index = 1
    for k in range(9):
        a = rr.uniform(0, 6.28); d = rr.uniform(0, R_ * 0.6); r = rr.uniform(R_ * 0.35, R_ * 0.6)
        g_ = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
        c = V(d * math.cos(a), d * math.sin(a), H_ - r * 0.3 + rr.uniform(-1.5, 1.5))
        for v in g_['verts']:
            n = v.co.normalized(); jit = 1 + 0.18 * math.sin(n.x * 9 + seed) * math.sin(n.y * 7) + 0.12 * math.sin(n.z * 13 + k)
            v.co = V(v.co.x * jit, v.co.y * jit, v.co.z * jit * 0.65) + c
    bm.to_mesh(me); bm.free(); me.materials.append(LEAF); me.materials.append(BARK)
    for p in me.polygons: p.use_smooth = True
    return me
CANOPY = [canopy_tree(f'PF_canopy{i}', h_, r_, 30 + i) for i, (h_, r_) in enumerate(((24, 9), (20, 7.5), (28, 11)))]
SEAT_SPOT = V(3.0, -2.0, 0)
rj = random.Random(21); nj = 0
for i in range(520):
    a = rj.uniform(0, 6.28); r = math.sqrt(rj.uniform(0, 160 * 160)); x, y = r * math.cos(a), r * math.sin(a)
    if math.hypot(x - SEAT_SPOT.x, y - SEAT_SPOT.y) < 8 or (abs(y - SEAT_SPOT.y) < 3 and SEAT_SPOT.x < x < SEAT_SPOT.x + 14): continue
    o = obj(f'PF_jtree{nj:03d}', CANOPY[nj % 3], JUNG); o.location = (x, y, 1.2 * nz(x, y, 6) - 0.2)
    o.rotation_euler = (0, 0, rj.uniform(0, 6.28)); s_ = rj.uniform(0.8, 1.25); o.scale = (s_, s_, s_); nj += 1
def scatter(cols, n, rng_, r0, r1, smin, smax, prefix, avoid=None):
    if not cols: return 0
    rr = random.Random(rng_); k = 0
    for i in range(n):
        a = rr.uniform(0, 2 * math.pi); r = math.sqrt(rr.uniform(r0 * r0, r1 * r1)); x, y = SEAT_SPOT.x + r * math.cos(a), SEAT_SPOT.y + r * math.sin(a)
        if avoid and avoid(x, y): continue
        o = D.objects.new(f'{prefix}{k:03d}', None); JUNG.objects.link(o); o['pf_gen'] = 1
        o.instance_type = 'COLLECTION'; o.instance_collection = cols[k % len(cols)]
        o.location = (x, y, 1.2 * nz(x, y, 6) - 0.05); o.rotation_euler = (0, 0, rr.uniform(0, 6.28)); s_ = rr.uniform(smin, smax); o.scale = (s_, s_, s_); k += 1
    return k
avoid_spot = lambda x, y: math.hypot(x - SEAT_SPOT.x, y - SEAT_SPOT.y) < 2.4 or (abs(y - SEAT_SPOT.y) < 0.55 and SEAT_SPOT.x < x < SEAT_SPOT.x + 14)
VF = variants('fern_02'); VA = variants('anthurium_botany_01'); VP = variants('pachira_aquatica_01')
for vc in VF + VA + VP: vc.hide_render = False
nf = scatter(VF, 1400, 22, 1.2, 50, 1.2, 2.4, 'PF_fern', avoid_spot)
na = scatter(VA, 900, 23, 1.0, 30, 1.6, 3.0, 'PF_anth', avoid_spot)
npc = scatter(VP, 420, 24, 2.5, 60, 2.2, 4.5, 'PF_pach', avoid_spot)
# footprints leading away from the seat row
FOOT = pbsdf('PF_Foot', (0.05, 0.03, 0.015), rough=0.95)
fme = D.meshes.new('PF_footprints'); bm = bmesh.new()
for k in range(16):
    x = SEAT_SPOT.x + 1.6 + k * 0.62; y = SEAT_SPOT.y + (0.09 if k % 2 else -0.09) + 0.25 * math.sin(k * 0.4)
    g_ = bmesh.ops.create_circle(bm, cap_ends=True, radius=0.07, segments=12)
    for v in g_['verts']: v.co = V(v.co.x * 1.7 + x, v.co.y + y, 1.2 * nz(x, y, 6) + 0.02)
bm.to_mesh(fme); bm.free(); fp = obj('PF_footprints', fme, JUNG); fme.materials.append(FOOT)

# ================= HERO collection =================
HERO_C = D.collections.get('LIB_stickman_rig')

# ================= worlds =================
def world(name, img_name, strength=1.0, rot=0.0, tint=(1, 1, 1)):
    w = D.worlds.get(name) or D.worlds.new(name); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    img = D.images.get(img_name)
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[1].default_value = strength
    if img:
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, rot)
        et = nt.nodes.new('ShaderNodeTexEnvironment'); et.image = img
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0; mx.inputs[7].default_value = (*tint, 1)
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], et.inputs['Vector'])
        nt.links.new(et.outputs[0], mx.inputs[6]); nt.links.new(mx.outputs[2], bg.inputs[0])
    else:
        bg.inputs[0].default_value = (*tint, 1)
    nt.links.new(bg.outputs[0], out.inputs[0]); return w
print('set ok', 'airliner', bool(AIRLINER), 'firs', k, 'jungle', nj, nf, na, npc)
SUN = D.objects.get('PF_SUN')
if SUN is None:
    SUN = D.objects.new('PF_SUN', D.lights.new('PF_SUN', 'SUN')); sc.collection.objects.link(SUN)
SUN.data.angle = math.radians(1.5)
