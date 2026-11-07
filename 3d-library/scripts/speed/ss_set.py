"""Super-speed Short props on top of the Freeze Time street + Plane Fall lake: glass panes that burst, shock cone,
food mountain, lake bench + old-age props, lake spray. All objects named SS_*, rebuilt on every run."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
for o in list(D.objects):
    if o.name.startswith('SS_'): D.objects.remove(o, do_unlink=True)
def coll(name):
    c = D.collections.get(name) or D.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
SS = coll('SS_STREET'); SL = coll('SS_LAKE')
def pbsdf(name, col, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emis=0.0, coat=0.0):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat
    if emis: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emis
    return m
def mk(name, build, mats, col, loc=(0, 0, 0)):
    me = D.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    for m in (mats if isinstance(mats, list) else [mats]): me.materials.append(m)
    o = D.objects.new(name, me); col.objects.link(o); o.location = loc; return o

# ---------------- glass panes in the shopfronts, broken into shards ----------------
GLASS = pbsdf('SS_Glass', (0.85, 0.92, 0.95), rough=0.02, trans=0.85, ior=1.5, coat=1.0)
PANES = [(-11.6, -8.4), (-7.0, -4.6), (-1.6, 1.6), (3.2, 6.8)]
SHARDS = []          # dict(o, p0, v, w, pane, delay)
rs = random.Random(3)
for pi, (y0, y1) in enumerate(PANES):
    # Voronoi-ish shards: jittered grid triangles
    nx, nz = 7, 6; pts = {}
    for i in range(nx + 1):
        for k in range(nz + 1):
            jx = 0 if i in (0, nx) else rs.uniform(-0.3, 0.3); jz = 0 if k in (0, nz) else rs.uniform(-0.3, 0.3)
            pts[i, k] = V(0.06, y0 + (y1 - y0) * (i + jx) / nx, 0.35 + 2.2 * (k + jz) / nz)
    for i in range(nx):
        for k in range(nz):
            for tri in (((i, k), (i + 1, k), (i + 1, k + 1)), ((i, k), (i + 1, k + 1), (i, k + 1))):
                c = sum((pts[t] for t in tri), V(0, 0, 0)) / 3
                def build(bm, tri=tri, c=c):
                    vs = [bm.verts.new(pts[t] - c) for t in tri]; bm.faces.new(vs)
                o = mk(f'SS_shard{pi}_{i}_{k}_{tri[1][0]}', build, GLASS, SS, c)
                o.modifiers.new('th', 'SOLIDIFY').thickness = 0.012
                SHARDS.append(dict(o=o, p0=c.copy(), v=V(rs.uniform(2.5, 7.0), rs.uniform(-2.5, 2.5), rs.uniform(0.0, 3.0)),
                                   w=V(rs.uniform(-12, 12), rs.uniform(-12, 12), rs.uniform(-12, 12)), pane=pi))
def shard_state(d, w):
    """w: seconds since that pane burst (negative = intact)"""
    if w <= 0: return d['p0'], Euler((0, 0, 0))
    p = d['p0'] + d['v'] * w + V(0, 0, -4.9 * w * w)
    if p.z < 0.17:
        p.z = 0.17 if d['p0'].x + d['v'].x * w < 3.1 else 0.02
    return p, Euler(tuple(d['w'] * min(w, 1.2)))

# ---------------- shock cone around the hero (fresnel, transparent) ----------------
m = D.materials.get('SS_Shock') or D.materials.new('SS_Shock'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.15
pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.0
em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (0.92, 0.96, 1.0, 1); em.inputs[1].default_value = 3.0
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(lw.outputs['Facing'], pw.inputs[0]); nt.links.new(pw.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
m.surface_render_method = 'BLENDED'; m.use_backface_culling = False; SHOCKM = m; SHOCK_MUL = mul
def cone_bm(bm):
    # open cone pointing along -Y (the running direction), apex just ahead of the hero
    n = 48; rings = []
    for j in range(10):
        u = j / 9; y = 0.5 - 4.0 * u; r = 0.15 + 2.6 * u ** 0.85
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / n), -y, 0.9 + r * math.sin(2 * math.pi * i / n))) for i in range(n)])
    for j in range(9):
        for i in range(n): bm.faces.new((rings[j][i], rings[j][(i + 1) % n], rings[j + 1][(i + 1) % n], rings[j + 1][i]))
CONE = mk('SS_cone', cone_bm, SHOCKM, SS); CONE.scale = (0.001,) * 3
for p in CONE.data.polygons: p.use_smooth = True

# ---------------- food mountain on the cafe table ----------------
PLATE = pbsdf('SS_Plate', (0.92, 0.92, 0.9), rough=0.2, coat=0.6)
BUN = pbsdf('SS_Bun', (0.62, 0.33, 0.10), rough=0.55, coat=0.2)
PATTY = pbsdf('SS_Patty', (0.16, 0.07, 0.03), rough=0.8)
LETT = pbsdf('SS_Lettuce', (0.25, 0.55, 0.08), rough=0.6)
CHEESE = pbsdf('SS_Cheese', (0.95, 0.65, 0.08), rough=0.4)
BOX = pbsdf('SS_PizzaBox', (0.70, 0.55, 0.36), rough=0.9)
def disc(bm, r, h, z, seg=24, dome=0.0):
    g_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r * (1 - dome * 0.6), depth=h)
    for v in g_['verts']: v.co.z += z + h / 2
    return g_['verts']
def burger_bm(bm):
    disc(bm, 0.055, 0.02, 0.0); disc(bm, 0.058, 0.015, 0.02); disc(bm, 0.06, 0.006, 0.035); disc(bm, 0.057, 0.005, 0.041); disc(bm, 0.055, 0.035, 0.046, dome=1.0)
def matidx(me, idxs):
    for p, ix in zip(me.polygons, idxs): p.material_index = ix
FOOD = []
TC = None
tab = D.objects.get('outdoor_table_chair_set_01_table')
if tab:
    bpy.context.view_layer.update()
    bb = [tab.matrix_world @ V(*v) for v in tab.bound_box]
    TC = V(sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8, max(v.z for v in bb))
else:
    TC = V(1.55, -4.2, 0.876)
rf = random.Random(6)
for i in range(46):
    kind = 'plate' if i % 3 == 0 else ('box' if i % 5 == 0 else 'burger')
    me = D.meshes.new(f'SS_food{i}'); bm = bmesh.new()
    if kind == 'burger':
        burger_bm(bm); bm.to_mesh(me); bm.free()
        for m_ in (BUN, PATTY, LETT, CHEESE): me.materials.append(m_)
        n = len(me.polygons); per = n // 5
        for k, p in enumerate(me.polygons): p.material_index = [0, 1, 2, 3, 0][min(4, k // max(1, per))]
    elif kind == 'plate':
        disc(bm, 0.12, 0.012, 0.0, seg=32); bm.to_mesh(me); bm.free(); me.materials.append(PLATE)
    else:
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts: v.co = V(v.co.x * 0.33, v.co.y * 0.33, v.co.z * 0.045 + 0.0225)
        bm.to_mesh(me); bm.free(); me.materials.append(BOX)
    for p in me.polygons: p.use_smooth = True
    o = D.objects.new(f'SS_food{i}', me); SS.objects.link(o)
    # stack them into a growing mountain: layer by layer, centred on the table
    layer = int(math.sqrt(i) * 1.0); a = rf.uniform(0, 6.28); r = max(0.0, 0.26 - 0.045 * layer) * math.sqrt(rf.random())
    p = TC + V(r * math.cos(a), r * math.sin(a), 0.002 + 0.05 * layer + rf.uniform(0, 0.02))
    FOOD.append(dict(o=o, p=p, rot=Euler((rf.uniform(-0.15, 0.15), rf.uniform(-0.15, 0.15), rf.uniform(0, 6.28))), order=i))
    o.location = p; o.rotation_euler = FOOD[-1]['rot']; o.scale = (0.001,) * 3

# ---------------- lake: bench, friend spot, old-age props, spray ----------------
src = D.objects.get('BENCH')
BENCH_P = V(-2.0, -300.0, 0.0)
def shore_h(x, y):
    def nz(x, y, s=1.0):
        return (math.sin(x * 0.013 * s + 1.3) * math.cos(y * 0.011 * s + 0.4) + 0.5 * math.sin(x * 0.031 * s + y * 0.027 * s) + 0.25 * math.sin(x * 0.071 * s - y * 0.063 * s + 2.0))
    r = math.hypot(x, y); return max(-2.0, min(14.0, (r - 260) * 0.06 + 2.5 * nz(x, y, 3)))
BENCH_P.z = shore_h(BENCH_P.x, BENCH_P.y)
if src:
    def hier(o): return [o] + [x for c in o.children for x in hier(c)]
    mp = {}
    for o in hier(src):
        n = o.copy(); n.name = 'SS_bench_' + o.name; SL.objects.link(n); mp[o] = n
        if n.animation_data: n.animation_data_clear()
    for o, n in mp.items():
        if o.parent in mp: n.parent = mp[o.parent]
    BENCH = mp[src]; BENCH.location = BENCH_P + V(0, 0, 0.08); BENCH.rotation_euler = (0, 0, 0)
WHITE_BEARD = pbsdf('SS_Beard', (0.95, 0.95, 0.95), rough=0.8)
def beard_bm(bm):
    g_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.001, radius2=0.12, depth=0.42)
    for v in g_['verts']: v.co = V(v.co.x * 1.0, v.co.y * 0.6, v.co.z)
BEARD = mk('SS_beard', beard_bm, WHITE_BEARD, SL)
WEB = pbsdf('SS_Web', (0.9, 0.9, 0.9), rough=0.6, emis=0.3)
def web_bm(bm):
    rr = random.Random(2)
    for k in range(9):
        a = V(rr.uniform(-0.5, 0.5), rr.uniform(-0.15, 0.15), rr.uniform(0.2, 1.5)); b = a + V(rr.uniform(-0.6, 0.6), rr.uniform(-0.3, 0.3), rr.uniform(-0.6, 0.2))
        n = (b - a).normalized(); side = n.cross(V(0, 1, 0)).normalized() * 0.003
        vs = [bm.verts.new(a - side), bm.verts.new(a + side), bm.verts.new(b + side), bm.verts.new(b - side)]; bm.faces.new(vs)
WEBS = mk('SS_webs', web_bm, WEB, SL)
WEBS.location = BENCH_P + V(0, 0, 0.1); WEBS.scale = (0.001,) * 3
# lake spray (metaball water)
WATER = D.materials.get('PF_Water') or pbsdf('SS_WaterSpray', (0.8, 0.9, 0.95), rough=0.02, trans=0.9, ior=1.33)
SPRAYM = pbsdf('SS_Spray', (0.85, 0.92, 0.97), rough=0.03, trans=0.85, ior=1.33, coat=1.0)
smb = D.metaballs.get('SS_spray') or D.metaballs.new('SS_spray'); smb.elements.clear(); smb.resolution = 0.08; smb.render_resolution = 0.04
if smb.animation_data: smb.animation_data_clear()
if not smb.materials: smb.materials.append(SPRAYM)
SPRAY = D.objects.new('SS_spray', smb); SL.objects.link(SPRAY)
rw = random.Random(9); SPR = []
for i in range(150):
    side = 1 if i % 2 else -1
    e = smb.elements.new(); e.radius = 0.001; e.type = 'ELLIPSOID'
    SPR.append(dict(e=e, k=i // 2, side=side, v=V(side * rw.uniform(2.0, 5.0), rw.uniform(-1.0, 1.0), rw.uniform(2.5, 6.0)), r=rw.uniform(0.12, 0.28)))
print('ss set ok', len(SHARDS), 'shards', len(FOOD), 'food', 'bench', bool(src), 'table', tuple(round(v, 2) for v in TC))
