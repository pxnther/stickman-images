"""Ant-size Short: giant-scale sets (the hero stays 1.75 m; the world is built 500x bigger).
Collections: ANT_CAFE (table, takeaway cup, crumbs, pavement, pedestal), ANT_RAIN (raindrops, puddles, water blob, giant feet),
ANT_LAB (blue grid room), ANT_GRASS (giant grass at dusk). Worlds: W_CAFE, W_RAIN, W_GRASS, W_LAB."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, noise
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
K = 500.0                       # world scale factor
Z_T = 375.0                     # table top height (0.75 m x 500)
R_T = 175.0                     # table top radius (0.35 m x 500)
CUP = V(110.0, 0.0, Z_T)        # takeaway cup base centre
CUP_RB, CUP_RT, CUP_H = 15.5, 22.5, 60.0
LID_R, LID_H = 24.0, 6.0
A_DRIP = math.radians(-32)      # side of the lid where the drop forms
DRIP_TOP = CUP + V(math.cos(A_DRIP) * LID_R, math.sin(A_DRIP) * LID_R, CUP_H + 1.0)
DROP_LAND = V(DRIP_TOP.x, DRIP_TOP.y, Z_T)
_u = (V(DROP_LAND.x, DROP_LAND.y, 0) - V(CUP.x, CUP.y, 0)).normalized()
HERO1 = DROP_LAND + _u * 4.6 + V(-_u.y, _u.x, 0) * 0.8          # hero spot for the hook (drop lands beside him)
_e = V(HERO1.x, HERO1.y, 0).normalized()
EDGE = V(_e.x, _e.y, 0) * (R_T - 1.2) + V(0, 0, Z_T)              # where he jumps off
LAND = V(_e.x, _e.y, 0) * (R_T + 48.0)                              # landing spot on the pavement
RAIN0 = LAND + V(-_e.y, _e.x, 0) * 60.0 + V(_e.x, _e.y, 0) * 300.0  # rain scenes spot (well away from the table)
LAB0 = V(0.0, 30000.0, 0.0)
GR0 = V(30000.0, 0.0, 0.0)

def coll(name):
    c = D.collections.get(name)
    if c is None:
        c = D.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        if o.get('ant_gen'): D.objects.remove(o, do_unlink=True)
    return c
def obj(name, data, col):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    o = D.objects.new(name, data); col.objects.link(o); o['ant_gen'] = 1; return o
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
def to_object_coords(mat, scale):
    nt = mat.node_tree
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD'); mp = next(n for n in nt.nodes if n.type == 'MAPPING')
    for l in list(nt.links):
        if l.to_node == mp and l.to_socket.name == 'Vector': nt.links.remove(l)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); mp.inputs['Scale'].default_value = (scale, scale, scale)
def smooth(me):
    for p in me.polygons: p.use_smooth = True
def lathe(name, prof, nseg=64, col=None, mat=None, loc=(0, 0, 0)):
    """prof: list of (r, z); revolves around Z"""
    me = D.meshes.new(name); bm = bmesh.new(); rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / nseg), r * math.sin(2 * math.pi * i / nseg), z)) for i in range(nseg)])
    for a, b in zip(rings, rings[1:]):
        for i in range(nseg):
            j = (i + 1) % nseg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.to_mesh(me); bm.free(); smooth(me)
    o = obj(name, me, col); o.location = loc
    if mat: me.materials.append(mat)
    return o
def rock(bm, c, s, seed, flat=0.7):
    g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = V(seed * 3.7, seed * 1.3, seed * 2.1)
    for v in g['verts']:
        d = 1.0 + 0.35 * noise.noise(v.co * 1.6 + off) + 0.12 * noise.noise(v.co * 4.0 + off)
        v.co = V(v.co.x * s.x * d, v.co.y * s.y * d, v.co.z * s.z * d * flat) + c
    return g

# ================= materials =================
WOOD = D.materials['wood_table']; to_object_coords(WOOD, 1.0 / 150.0)
for _n in WOOD.node_tree.nodes:
    if _n.type == 'TEX_IMAGE': _n.projection = 'BOX'; _n.projection_blend = 0.25
PAVE = D.materials['asphalt_02_material_Road']; to_object_coords(PAVE, 1.0 / 20.0)
COFFEE = D.materials['FZ_Coffee']
CUPW = pbsdf('ANT_CupPaper', (0.93, 0.92, 0.89), rough=0.55)
SLEEVE = pbsdf('ANT_CupSleeve', (0.42, 0.24, 0.12), rough=0.8)
LIDM = pbsdf('ANT_Lid', (0.03, 0.03, 0.035), rough=0.25, coat=0.4)
METAL = pbsdf('ANT_TableMetal', (0.08, 0.085, 0.09), rough=0.35, metal=1.0)
CRUMB = pbsdf('ANT_Crumb', (0.78, 0.55, 0.28), rough=0.85)
SUGAR = pbsdf('ANT_Sugar', (0.97, 0.97, 0.96), rough=0.6, trans=0.15)
PEBBLE = pbsdf('ANT_Pebble', (0.16, 0.15, 0.14), rough=0.75)
CAPM = pbsdf('ANT_Cap', (0.75, 0.06, 0.05), rough=0.3, metal=0.8)
GREY = pbsdf('ANT_GiantGrey', (0.45, 0.45, 0.47), rough=0.6)
LEAFM = []
for i, c in enumerate([(0.62, 0.22, 0.05), (0.75, 0.42, 0.07), (0.45, 0.16, 0.06)]):
    LEAFM.append(pbsdf(f'ANT_Leaf{i}', c, rough=0.6))
# water with a keyable cyan fresnel rim (surface tension glow)
m, nt = nodes_mat('ANT_Water')
bs = N(nt, 'ShaderNodeBsdfPrincipled'); bs.inputs['Base Color'].default_value = (0.62, 0.78, 0.88, 1); bs.inputs['Roughness'].default_value = 0.04
bs.inputs['Transmission Weight'].default_value = 0.65; bs.inputs['IOR'].default_value = 1.33; bs.inputs['Coat Weight'].default_value = 0.6
lw = N(nt, 'ShaderNodeLayerWeight', i_Blend=0.25); em = N(nt, 'ShaderNodeEmission'); em.inputs[0].default_value = (0.25, 0.85, 1.0, 1)
mul = N(nt, 'ShaderNodeMath', operation='MULTIPLY', name='GLOW'); mul.inputs[1].default_value = 0.0
L(nt, lw.outputs['Fresnel'], mul.inputs[0]); L(nt, mul.outputs[0], em.inputs['Strength'])
ad = N(nt, 'ShaderNodeAddShader'); L(nt, bs.outputs[0], ad.inputs[0]); L(nt, em.outputs[0], ad.inputs[1])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, ad.outputs[0], out.inputs[0])
WATER = m; WATER_GLOW = mul
# grid-lab material: dark blue with glowing grid lines (object coords, 2 m cells, every 5th line brighter)
m, nt = nodes_mat('ANT_Grid')
tc = N(nt, 'ShaderNodeTexCoord'); sep = N(nt, 'ShaderNodeSeparateXYZ'); L(nt, tc.outputs['Object'], sep.inputs[0])
def lines(cell, width):
    outs = []
    for ax in (0, 1, 2):
        ofs = N(nt, 'ShaderNodeMath', operation='ADD'); ofs.inputs[1].default_value = 0.37 * cell; L(nt, sep.outputs[ax], ofs.inputs[0])
        dv = N(nt, 'ShaderNodeMath', operation='DIVIDE'); dv.inputs[1].default_value = cell; L(nt, ofs.outputs[0], dv.inputs[0])
        pp = N(nt, 'ShaderNodeMath', operation='PINGPONG'); pp.inputs[1].default_value = 0.5; L(nt, dv.outputs[0], pp.inputs[0])
        lt = N(nt, 'ShaderNodeMath', operation='LESS_THAN'); lt.inputs[1].default_value = width; L(nt, pp.outputs[0], lt.inputs[0])
        outs.append(lt.outputs[0])
    mx1 = N(nt, 'ShaderNodeMath', operation='MAXIMUM'); L(nt, outs[0], mx1.inputs[0]); L(nt, outs[1], mx1.inputs[1])
    mx2 = N(nt, 'ShaderNodeMath', operation='MAXIMUM'); L(nt, mx1.outputs[0], mx2.inputs[0]); L(nt, outs[2], mx2.inputs[1])
    return mx2.outputs[0]
g1 = lines(1.0, 0.012); g5 = lines(5.0, 0.004)
gsum = N(nt, 'ShaderNodeMath', operation='ADD'); gsum.inputs[0].default_value = 0; L(nt, g1, gsum.inputs[0]); L(nt, g5, gsum.inputs[1])
gm = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); gm.inputs[1].default_value = 3.0; L(nt, gsum.outputs[0], gm.inputs[0])
bsg = N(nt, 'ShaderNodeBsdfPrincipled'); bsg.inputs['Base Color'].default_value = (0.02, 0.07, 0.22, 1); bsg.inputs['Roughness'].default_value = 0.35
bsg.inputs['Emission Color'].default_value = (0.35, 0.75, 1.0, 1); L(nt, gm.outputs[0], bsg.inputs['Emission Strength'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bsg.outputs[0], out.inputs[0])
GRIDM = m
def emis_mat(name, col, st):
    m, nt = nodes_mat(name)
    e = N(nt, 'ShaderNodeEmission'); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = st
    o = N(nt, 'ShaderNodeOutputMaterial'); L(nt, e.outputs[0], o.inputs[0]); return m
RAYM = emis_mat('ANT_Ray', (1.0, 0.85, 0.45), 6.0)
HAIRM = pbsdf('ANT_Hair', (0.10, 0.06, 0.035), rough=0.35, coat=0.3)
RINGM = emis_mat('ANT_PupilRing', (0.3, 0.9, 1.0), 5.0)
# grass + soil
m, nt = nodes_mat('ANT_Grass')
bsg = N(nt, 'ShaderNodeBsdfPrincipled'); bsg.inputs['Roughness'].default_value = 0.45
tc = N(nt, 'ShaderNodeTexCoord'); nz_ = N(nt, 'ShaderNodeTexNoise', i_Scale=0.08, i_Detail=3.0); L(nt, tc.outputs['Object'], nz_.inputs['Vector'])
cr = N(nt, 'ShaderNodeValToRGB'); L(nt, nz_.outputs['Fac'], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.06, 0.20, 0.03, 1); cr.color_ramp.elements[1].color = (0.20, 0.38, 0.06, 1)
L(nt, cr.outputs[0], bsg.inputs['Base Color'])
tr = N(nt, 'ShaderNodeBsdfTranslucent'); tr.inputs[0].default_value = (0.25, 0.55, 0.08, 1)
mxs = N(nt, 'ShaderNodeMixShader'); mxs.inputs[0].default_value = 0.3; L(nt, bsg.outputs[0], mxs.inputs[1]); L(nt, tr.outputs[0], mxs.inputs[2])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, mxs.outputs[0], out.inputs[0])
GRASSM = m
m, nt = nodes_mat('ANT_Soil')
bsg = N(nt, 'ShaderNodeBsdfPrincipled'); bsg.inputs['Roughness'].default_value = 0.95
tc = N(nt, 'ShaderNodeTexCoord'); nz_ = N(nt, 'ShaderNodeTexNoise', i_Scale=0.15, i_Detail=8.0); L(nt, tc.outputs['Object'], nz_.inputs['Vector'])
cr = N(nt, 'ShaderNodeValToRGB'); L(nt, nz_.outputs['Fac'], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.035, 0.03, 0.012, 1); cr.color_ramp.elements[1].color = (0.11, 0.09, 0.04, 1)
L(nt, cr.outputs[0], bsg.inputs['Base Color'])
bp = N(nt, 'ShaderNodeBump', i_Strength=0.6); L(nt, nz_.outputs['Fac'], bp.inputs['Height']); L(nt, bp.outputs[0], bsg.inputs['Normal'])
out = N(nt, 'ShaderNodeOutputMaterial'); L(nt, bsg.outputs[0], out.inputs[0])
SOILM = m

# ================= CAFE: table, cup, crumbs, pavement =================
CAFE = coll('ANT_CAFE')
for n in ('ANT_TableTop', 'ANT_Floor'):
    o = D.objects.get(n)
    if o and not o.get('ant_gen'): D.objects.remove(o, do_unlink=True)
top = lathe('ANT_TableTop', [(0, Z_T), (R_T - 3, Z_T), (R_T, Z_T - 3), (R_T, Z_T - 9), (R_T - 3, Z_T - 12), (0, Z_T - 12)], 128, CAFE, WOOD)
lathe('ANT_Pedestal', [(0, 0), (100, 0), (100, 4), (60, 8), (16, 14), (13, 40), (13, Z_T - 40), (30, Z_T - 16), (40, Z_T - 12), (0, Z_T - 12)], 48, CAFE, METAL)
me = D.meshes.new('ANT_Floor'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6000); bm.to_mesh(me); bm.free()
fl = obj('ANT_Floor', me, CAFE); me.materials.append(PAVE)
# takeaway cup with sleeve and lid (local origin at the cup base)
lathe('ANT_Cup', [(0, 0.5), (CUP_RB - 1, 0), (CUP_RB, 1.5), (CUP_RT, CUP_H - 2.0), (CUP_RT - 0.6, CUP_H)], 96, CAFE, CUPW, CUP)
lathe('ANT_Sleeve', [(CUP_RB + 0.25 + (CUP_RT - CUP_RB) * 0.22, CUP_H * 0.22), (CUP_RB + 0.25 + (CUP_RT - CUP_RB) * 0.62, CUP_H * 0.62)], 96, CAFE, SLEEVE, CUP)
lathe('ANT_LidM', [(CUP_RT - 1.2, CUP_H - 1.5), (LID_R, CUP_H - 0.5), (LID_R, CUP_H + 1.0), (LID_R - 1.0, CUP_H + 1.6), (LID_R - 2.5, CUP_H + 2.0),
                   (LID_R - 4.0, CUP_H + LID_H), (8.0, CUP_H + LID_H + 0.3), (0, CUP_H + LID_H + 0.3)], 96, CAFE, LIDM, CUP)
# coffee drip trail down the lid edge + the hanging drop (metaball, animated in ant_anim)
mb = D.metaballs.get('ANT_Drop') or D.metaballs.new('ANT_Drop'); mb.elements.clear(); mb.resolution = 0.12; mb.render_resolution = 0.06
if mb.animation_data: mb.animation_data_clear()
if not mb.materials: mb.materials.append(COFFEE)
DROP = obj('ANT_Drop', mb, CAFE)
DROP_E = [mb.elements.new() for _ in range(3)]
for e in DROP_E: e.radius = 0.001
# splash crown (metaball, animated)
mb2 = D.metaballs.get('ANT_Splash') or D.metaballs.new('ANT_Splash'); mb2.elements.clear(); mb2.resolution = 0.15; mb2.render_resolution = 0.07
if mb2.animation_data: mb2.animation_data_clear()
if not mb2.materials: mb2.materials.append(COFFEE)
SPLASH = obj('ANT_Splash', mb2, CAFE); SPLASH.location = DROP_LAND
rs = random.Random(4); SPL = []
NRING = 64
for ring in range(0):
    for i in range(NRING):
        a = 2 * math.pi * (i + 0.5 * ring) / NRING
        SPL.append(dict(e=mb2.elements.new(), a=a, ring=ring, tip=False, v=rs.uniform(0.9, 1.1)))
for i in range(26):
    a = 2 * math.pi * i / 26 + rs.uniform(-0.08, 0.08)
    SPL.append(dict(e=mb2.elements.new(), a=a, ring=3, tip=True, v=rs.uniform(0.8, 1.25)))
SPL_POOL = mb2.elements.new()
# crown sheet as a mesh (thin flared wall with a spiky rim), scaled per frame in ant_anim
me = D.meshes.new('ANT_Crown'); bm = bmesh.new(); nseg = 96; rows = []
prof = [(1.0, 0.0), (1.02, 0.25), (1.08, 0.55), (1.18, 0.85), (1.26, 1.0)]
for j, (r, z) in enumerate(prof):
    ring = []
    for i in range(nseg):
        a = 2 * math.pi * i / nseg
        zz = z + (0.12 * max(0.0, math.sin(11 * a + 0.7)) ** 3 + 0.05 * math.sin(23 * a)) * (j == len(prof) - 1)
        ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), zz)))
    rows.append(ring)
for a_, b_ in zip(rows, rows[1:]):
    for i in range(nseg): bm.faces.new((a_[i], a_[(i + 1) % nseg], b_[(i + 1) % nseg], b_[i]))
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(COFFEE)
CROWN = obj('ANT_Crown', me, CAFE); CROWN.location = DROP_LAND; CROWN.scale = (0.001,) * 3
sol = CROWN.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.12; sol.offset = 0.0
for d in SPL: d['e'].radius = 0.001
SPL_POOL.radius = 0.001
# crumbs and a sugar cube on the table (kept out of the hero's paths)
rs = random.Random(11); me = D.meshes.new('ANT_Crumbs'); bm = bmesh.new(); k = 0
while k < 70:
    r = rs.uniform(30, R_T - 6); a = rs.uniform(-1.3, 0.9)
    c = V(r * math.cos(a), r * math.sin(a), Z_T)
    if (c - CUP).length < CUP_RT + 4 or (c - HERO1).length < 5 or (V(c.x, c.y, 0) - V(EDGE.x, EDGE.y, 0)).length < 6: continue
    if (c - DROP_LAND).length < 8: continue
    s = rs.uniform(0.25, 1.7); rock(bm, c + V(0, 0, s * 0.3), V(s, s * rs.uniform(0.6, 1.2), s), k, 0.6); k += 1
bm.to_mesh(me); bm.free(); smooth(me); obj('ANT_Crumbs', me, CAFE); me.materials.append(CRUMB)
me = D.meshes.new('ANT_Sugar'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=8.0)
bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=0.5, segments=2, affect='EDGES'); bm.to_mesh(me); bm.free()
sg = obj('ANT_Sugar', me, CAFE); me.materials.append(SUGAR)
sg.location = CUP + V(-34, -30, 4.0); sg.rotation_euler = (0, 0, 0.5)
# pavement clutter: pebbles, a bottle cap, autumn leaves around the landing / rain spots
rs = random.Random(21); me = D.meshes.new('ANT_Pebbles'); bm = bmesh.new()
for i in range(260):
    base = LAND if i % 2 else RAIN0
    a_ = rs.uniform(0, 2 * math.pi); d_ = rs.uniform(9, 40) if i < 140 else rs.uniform(40, 140)
    c = base + V(math.cos(a_) * d_, math.sin(a_) * d_, 0)
    if (V(c.x, c.y, 0) - V(LAND.x, LAND.y, 0)).length < 7 or (V(c.x, c.y, 0) - V(RAIN0.x, RAIN0.y, 0)).length < 9: continue
    s = rs.uniform(0.4, 2.6); rock(bm, c + V(0, 0, s * 0.25), V(s, s * rs.uniform(0.7, 1.2), s), i + 100, 0.55)
bm.to_mesh(me); bm.free(); smooth(me); obj('ANT_Pebbles', me, CAFE); me.materials.append(PEBBLE)
cap = lathe('ANT_Cap', [(0, 3.2), (7.4, 3.2), (8.0, 2.6), (8.2, 0.3), (8.6, 0.0), (7.6, 0.0), (7.4, 2.4), (0, 2.4)], 48, CAFE, CAPM, LAND + V(-22, 26, 0))
cap.rotation_euler = (0.08, 0.05, 0)
for i in range(9):
    me = D.meshes.new(f'ANT_Leaf{i}'); bm = bmesh.new(); n_ = 10
    ln = rs.uniform(18, 34); wd = ln * 0.42
    rows = []
    for j in range(n_ + 1):
        u = j / n_; w = wd * math.sin(math.pi * u) ** 0.8
        z = 0.15 * ln * (u - 0.5) ** 2 + rs.uniform(0, 0.3)
        rows.append([bm.verts.new((ln * u - ln / 2, -w / 2, z + 0.06 * ln * abs(-0.5) ** 2)), bm.verts.new((ln * u - ln / 2, 0, z - 0.4)), bm.verts.new((ln * u - ln / 2, w / 2, z + 0.06 * ln * 0.25))])
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], b[0], b[1], a[1])); bm.faces.new((a[1], b[1], b[2], a[2]))
    bm.to_mesh(me); bm.free(); smooth(me)
    lf = obj(f'ANT_Leaf{i}', me, CAFE); me.materials.append(LEAFM[i % 3])
    base = LAND if i < 5 else RAIN0
    ang = rs.uniform(0, 2 * math.pi); dist = rs.uniform(22, 80)
    lf.location = base + V(math.cos(ang) * dist, math.sin(ang) * dist, 1.2); lf.rotation_euler = (rs.uniform(-0.08, 0.08), rs.uniform(-0.08, 0.08), rs.uniform(0, 6.3))

# ================= RAIN: drops, puddle, sticky blob, giant feet =================
RAIN = coll('ANT_RAIN')
rs = random.Random(31); RAINDROPS = []
for i in range(46):
    me = D.meshes.new(f'ANT_Rain{i}'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(WATER)
    o = obj(f'ANT_Rain{i}', me, RAIN); o.scale = (0.001,) * 3
    RAINDROPS.append(dict(o=o, r=rs.uniform(0.9, 1.35), p=RAIN0 + V(rs.uniform(-70, 70), rs.uniform(-70, 70), 0), t=rs.uniform(0, 1)))
# small splash discs (flattened, expand where a drop lands)
SPLATS = []
for i in range(46):
    me = D.meshes.new(f'ANT_Splat{i}'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=10, radius=1.0)
    bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(WATER)
    o = obj(f'ANT_Splat{i}', me, RAIN); o.scale = (0.001,) * 3; SPLATS.append(o)
me = D.meshes.new('ANT_Puddle'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=1.0, segments=64)
for v in bm.verts:
    a = math.atan2(v.co.y, v.co.x); v.co *= 1.0 + 0.18 * math.sin(3 * a + 1) + 0.1 * math.sin(7 * a)
bm.to_mesh(me); bm.free(); me.materials.append(WATER)
PUD = obj('ANT_Puddle', me, RAIN); PUD.location = RAIN0 + V(-30, 18, 0.05); PUD.scale = (26, 18, 1)
mb3 = D.metaballs.get('ANT_Blob') or D.metaballs.new('ANT_Blob'); mb3.elements.clear(); mb3.resolution = 0.05; mb3.render_resolution = 0.025
if mb3.animation_data: mb3.animation_data_clear()
if not mb3.materials: mb3.materials.append(WATER)
BLOB = obj('ANT_Blob', mb3, RAIN)
BLOB_E = [mb3.elements.new() for _ in range(6)]
for e in BLOB_E: e.radius = 0.001
# giant grey stickman legs (a passer-by): two capsules + rounded feet, animated in ant_anim
GIANT = []
for s in ('L', 'R'):
    me = D.meshes.new('ANT_GLeg' + s); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=25.0, radius2=25.0, depth=420.0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 210 + 25))
    g = bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=25.0); bmesh.ops.translate(bm, verts=g['verts'], vec=(0, 0, 25))
    bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(GREY)
    o = obj('ANT_GLeg' + s, me, RAIN); o.location = (0, 0, -2000); GIANT.append(o)

# ================= LAB: blue grid room =================
LAB = coll('ANT_LAB')
me = D.meshes.new('ANT_LabRoom'); bm = bmesh.new()
# floor + curved cove up to a back wall (a cyclorama), 40 m wide
prof = [(y, 0.0) for y in (-20, -10, 0, 6)] + [(6 + 8 * math.sin(a), 8 - 8 * math.cos(a)) for a in [i * math.pi / 2 / 10 for i in range(1, 11)]] + [(14, 30.0)]
rows = []
for x in (-25, -12, 0, 12, 25):
    rows.append([bm.verts.new((x, y, z)) for y, z in prof])
for a, b in zip(rows, rows[1:]):
    for i in range(len(prof) - 1): bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(GRIDM)
lab = obj('ANT_LabRoom', me, LAB); lab.location = LAB0
me = D.meshes.new('ANT_LabHair'); bm = bmesh.new()
segs = 40; rr = 1.4; rings = []
for j in range(segs + 1):
    u = j / segs; c = V(-22 + 44 * u, 4.0 + 0.8 * math.sin(u * 3.0), 3.2 + 0.6 * math.sin(u * 5 + 1))
    rings.append([bm.verts.new(c + V(0, rr * math.cos(2 * math.pi * i / 20), rr * math.sin(2 * math.pi * i / 20))) for i in range(20)])
for a, b in zip(rings, rings[1:]):
    for i in range(20): bm.faces.new((a[i], a[(i + 1) % 20], b[(i + 1) % 20], b[i]))
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(HAIRM)
HAIR = obj('ANT_LabHair', me, LAB); HAIR.location = LAB0
me = D.meshes.new('ANT_LabPupil'); bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=0.16, radius2=0.16, depth=0.05)
bm.to_mesh(me); bm.free(); me.materials.append(RINGM)
PUPIL = obj('ANT_LabPupil', me, LAB); PUPIL.location = LAB0 + V(0, 1.0, 3.2); PUPIL.rotation_euler = (0, math.pi / 2, 0)
RAYS = []
for i in range(9):
    me = D.meshes.new(f'ANT_Ray{i}'); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.035, radius2=0.035, depth=1.0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.5)); bm.to_mesh(me); bm.free(); me.materials.append(RAYM)
    o = obj(f'ANT_Ray{i}', me, LAB); o.scale = (0.001,) * 3; RAYS.append(o)

# ================= GRASS at dusk =================
GR = coll('ANT_GRASS')
me = D.meshes.new('ANT_Soil'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=60, y_segments=60, size=600)
for v in bm.verts: v.co.z = 2.5 * noise.noise(V(v.co.x * 0.02, v.co.y * 0.02, 0.3)) + 0.6 * noise.noise(V(v.co.x * 0.1, v.co.y * 0.1, 1.7))
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(SOILM)
so = obj('ANT_Soil', me, GR); so.location = GR0 - V(0, 0, 0.4)
def blade(bm, base, h, w, ang, bend, lean):
    n = 9; rows = []
    d = V(math.cos(ang), math.sin(ang), 0); side = V(-d.y, d.x, 0)
    for j in range(n + 1):
        u = j / n; ww = w * (1 - u) ** 0.7 * (1.0 if j < n else 0.05)
        c = base + d * (bend * h * u * u + lean * h * u) + V(0, 0, h * u * (1 - 0.35 * bend * u))
        rows.append((bm.verts.new(c - side * ww / 2), bm.verts.new(c + V(0, 0, 0) + d * 0.08 * w), bm.verts.new(c + side * ww / 2)))
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], b[0], b[1], a[1])); bm.faces.new((a[1], b[1], b[2], a[2]))
rs = random.Random(41); me = D.meshes.new('ANT_GrassBlades'); bm = bmesh.new(); nb = 0
while nb < 520:
    p = V(rs.uniform(-160, 160), rs.uniform(-60, 220), 0)
    if p.length < 6: continue
    blade(bm, GR0 + p, rs.uniform(25, 90), rs.uniform(2.0, 4.5), rs.uniform(0, 2 * math.pi), rs.uniform(0.1, 0.7), rs.uniform(-0.05, 0.1)); nb += 1
# the blade that bends over the hero (shelter)
blade(bm, GR0 + V(-3.5, 2.0, 0), 22.0, 4.2, -0.3, 0.9, 0.05)
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(GRASSM)
obj('ANT_GrassBlades', me, GR)
me = D.meshes.new('ANT_GrassPebbles'); bm = bmesh.new()
for i in range(50):
    c = GR0 + V(rs.uniform(-60, 60), rs.uniform(-20, 120), 0)
    if (c - GR0).length < 5: continue
    s = rs.uniform(0.4, 2.2); rock(bm, c, V(s, s, s), i + 300, 0.6)
bm.to_mesh(me); bm.free(); smooth(me); obj('ANT_GrassPebbles', me, GR); me.materials.append(PEBBLE)

# ================= worlds =================
def world(name, img, strength=1.0, rot=0.0, tint=(1, 1, 1)):
    w = D.worlds.get(name) or D.worlds.new(name); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
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
def env_img(wname):
    w = D.worlds.get(wname)
    if not w: return None
    return next((n.image for n in w.node_tree.nodes if n.type == 'TEX_ENVIRONMENT'), None)
IMG_RAIN = env_img('W_RAIN') or D.images.get('urban_street_01_2k')
IMG_GRASS = env_img('W_GRASS') or D.images.get('sunset_fairway_2k')
world('W_CAFE', D.images.get('urban_street_04_4k'), 1.0, 0.0)
world('W_RAIN', IMG_RAIN, 0.75, 0.0, (0.85, 0.9, 1.0))
world('W_GRASS', IMG_GRASS, 1.0, 0.0)
world('W_LAB', None, 1.0, 0.0, (0.01, 0.025, 0.07))

SUN = D.objects.get('PF_SUN')
cam = D.objects['Cam']; cam.data.clip_start = 0.02; cam.data.clip_end = 60000
print('ant set ok', 'hero1', tuple(round(x, 2) for x in HERO1), 'edge', tuple(round(x, 1) for x in EDGE), 'land', tuple(round(x, 1) for x in LAND), 'rain', tuple(round(x, 1) for x in RAIN0))
