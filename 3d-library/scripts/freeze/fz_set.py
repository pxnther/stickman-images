"""Freeze-time set: cleans the story-test file and builds cafe, cup, splash, pigeons, pedestrians, taxi, holograms."""
import bpy, math, random, bmesh
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene
D = bpy.data
def V(*a): return Vector(a)

# ---------------- cleanup ----------------
for o in list(D.objects):
    if o.name.startswith('HOLO') or o.name.startswith('FZ_'):
        D.objects.remove(o, do_unlink=True)
for o in D.objects:
    if o.animation_data and not any(c.name == 'BirdSrc' for c in o.users_collection):
        o.animation_data_clear()
COL = D.collections.get('FZ') or D.collections.new('FZ')
if COL.name not in sc.collection.children: sc.collection.children.link(COL)
def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    COL.objects.link(o); return o

def emis(name, col, strength, alpha=None):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = strength
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    if alpha is None:
        nt.links.new(e.outputs[0], o.inputs[0])
    else:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
        m.surface_render_method = 'BLENDED'
    return m
def pbsdf(name, col, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emis_s=0.0, coat=0.0):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    b.inputs['Coat Weight'].default_value = coat
    if emis_s: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emis_s
    return m

sc.eevee.use_raytracing = True
try:
    sc.eevee.ray_tracing_options.resolution_scale = '2'
except Exception: pass

for d_ in [bpy.data.objects['Cam'].data] + [m for m in D.materials if m.name.startswith('FZ_') or m.name.startswith('Holo')] + [m.node_tree for m in D.materials if (m.name.startswith('FZ_') or m.name.startswith('Holo')) and m.node_tree]:
    if d_.animation_data: d_.animation_data_clear()
# ---------------- cafe corner ----------------
CAFE_P = V(1.55, -4.2, 0.15)
cafe = D.objects.new('FZ_cafe', None); COL.objects.link(cafe); cafe.location = CAFE_P; cafe.rotation_euler = (0, 0, 0)
for n in ('outdoor_table_chair_set_01_chair_01', 'outdoor_table_chair_set_01_table', 'outdoor_table_chair_set_01_chair_02'):
    o = D.objects[n]; o.parent = cafe; o.matrix_parent_inverse.identity()
tab = D.objects['outdoor_table_chair_set_01_table']
zs = [ (tab.matrix_world @ V(*v)).z for v in tab.bound_box ]
bpy.context.view_layer.update()
zs = [(tab.matrix_world @ V(*v)).z for v in tab.bound_box]
xs = [(tab.matrix_world @ V(*v)).x for v in tab.bound_box]; ys = [(tab.matrix_world @ V(*v)).y for v in tab.bound_box]
TOP = max(zs); TC = V((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, TOP)
CUP_P = TC + V(0.12, 0.06, 0.0)

# cup + saucer + coffee surface
WHITE_CER = pbsdf('FZ_Ceramic', (0.92, 0.9, 0.86), rough=0.18, coat=0.6)
COFFEE = pbsdf('FZ_Coffee', (0.10, 0.038, 0.01), rough=0.015, trans=0.55, ior=1.34, coat=1.0)
def add_mesh(name, build, mat, loc):
    me = D.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    o = D.objects.new(name, me); COL.objects.link(o); o.location = loc; me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    return o
def cup_bm(bm):
    # lathe profile: outer wall + inner wall
    prof = [(0.0, 0.0), (0.030, 0.0), (0.036, 0.004), (0.041, 0.03), (0.045, 0.085), (0.046, 0.09), (0.042, 0.09), (0.039, 0.03), (0.030, 0.008), (0.0, 0.008)]
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=40, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
cup = add_mesh('FZ_cup', cup_bm, WHITE_CER, CUP_P + V(0, 0, 0.012))
def handle_bm(bm):
    bmesh.ops.create_circle(bm, cap_ends=False, radius=0.006, segments=8)
cu = D.curves.new('FZ_handle', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0055; cu.bevel_resolution = 3
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
for bp, co in zip(sp.bezier_points, [(0.042, 0, 0.075), (0.072, 0, 0.05), (0.04, 0, 0.022)]):
    bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
hob = D.objects.new('FZ_handle', cu); COL.objects.link(hob); hob.parent = cup; cu.materials.append(WHITE_CER)
def saucer_bm(bm):
    prof = [(0.0, 0.0), (0.05, 0.0), (0.07, 0.008), (0.075, 0.012), (0.07, 0.013), (0.05, 0.006), (0.0, 0.006)]
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=40)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
add_mesh('FZ_saucer', saucer_bm, WHITE_CER, CUP_P)
def disc_bm(bm): bmesh.ops.create_circle(bm, cap_ends=True, radius=0.039, segments=32)
surf = add_mesh('FZ_coffee_surf', disc_bm, COFFEE, CUP_P + V(0, 0, 0.012 + 0.072))
# a second cup + a small plate for set dressing
c2 = cup.copy(); COL.objects.link(c2); c2.name = 'FZ_cup2'; c2.location = TC + V(-0.17, -0.14, 0.012); c2.rotation_euler = (0, 0, 2.2)
h2 = hob.copy(); COL.objects.link(h2); h2.parent = c2

# ---------------- coffee splash (metaball crown + Worthington jet, state = f(tau)) ----------------
rnd = random.Random(11)
SPL_ORIGIN = CUP_P + V(0, 0, 0.012 + 0.072)
mbd = D.metaballs.get('FZ_splash') or D.metaballs.new('FZ_splash')
mbd.elements.clear(); mbd.resolution = 0.006; mbd.render_resolution = 0.0028; mbd.threshold = 0.6
if mbd.animation_data: mbd.animation_data_clear()
spl_ob = D.objects.new('FZ_splash', mbd); COL.objects.link(spl_ob); spl_ob.location = SPL_ORIGIN
if not mbd.materials: mbd.materials.append(COFFEE)
SPL = []   # each: launch pos (local), velocity, radius, kind
NJ = 26
for k in range(NJ):                       # central jet: fastest fluid leaves first and ends up on top
    u = k / (NJ - 1)
    vz = 1.75 * (1 - u) ** 0.8 + 0.12 + (0.12 if k == 0 else 0)
    SPL.append(dict(p0=V(0.002 * math.sin(k), 0.002 * math.cos(k), -0.01), v=V(0.03, -0.02, vz), r=0.0105 + 0.006 * u + (0.004 if k == 0 else 0), kind='jet'))
NS = 18
for s_ in range(NS):                      # short crown spikes on the rim, each ending in a droplet
    a = 2 * math.pi * s_ / NS + rnd.uniform(-0.1, 0.1); hk = rnd.uniform(0.85, 1.12)
    for j in range(6):
        u = j / 5
        vr = 0.12 + 0.07 * u
        vz = (0.74 + 0.28 * u) * hk + (0.10 if j == 5 else 0.0)
        SPL.append(dict(p0=V(math.cos(a) * 0.044, math.sin(a) * 0.044, 0.017), v=V(math.cos(a) * vr, math.sin(a) * vr, vz),
                        r=(0.0068 - 0.0012 * u) if j < 5 else 0.0072, kind='crown'))
for row, vz in ((0, 0.70), (1, 0.79)):     # crown wall (thin sheet standing on the rim)
    for s_ in range(40):
        a = 2 * math.pi * (s_ + 0.5 * row) / 40
        SPL.append(dict(p0=V(math.cos(a) * 0.044, math.sin(a) * 0.044, 0.016), v=V(math.cos(a) * 0.09, math.sin(a) * 0.09, vz), r=0.0088, kind='wall'))
SPL.append(dict(p0=V(0, 0, -0.012), v=V(0, 0, 0), r=0.05, kind='pool'))
for d in SPL:
    e = mbd.elements.new(); e.radius = d['r']; e.co = d['p0']
    if d['kind'] == 'pool': e.type = 'ELLIPSOID'; e.size_x = 0.75; e.size_y = 0.75; e.size_z = 0.12
    d['e'] = e
    if d['kind'] != 'pool': e.type = 'ELLIPSOID'; e.size_x = e.size_y = e.size_z = 1.0
TABLE_Z = TOP + 0.003
CUP_TOP = 0.102 - 0.084           # rim height above the coffee surface (local)
def splash_state(tau):
    """list of (co, radius) in splash-local space; tau = seconds since the drop hit the coffee"""
    g = 9.81; out = []
    tz = TABLE_Z - SPL_ORIGIN.z
    for d in SPL:
        if d['kind'] == 'pool': out.append((d['p0'], d['r'], 1.0)); continue
        if tau <= 0: out.append((d['p0'], 0.0, 1.0)); continue
        p = d['p0'] + d['v'] * tau + V(0, 0, -0.5 * g * tau * tau)
        grow = min(1.0, tau / 0.04)
        r = d['r'] * grow; flat = 1.0
        rr = p.xy.length
        if p.z < d['p0'].z - 0.002 and rr < 0.04:            # fell back into the cup
            r = 0.0
        elif rr >= 0.04 and p.z < tz + 0.004:                 # landed on the table/saucer: splat
            p = V(p.x, p.y, tz + 0.002); r = d['r'] * 1.5; flat = 0.22
        out.append((p, r, flat))
    return out
TAU_F = 0.15
def apply_splash(tau, f=None):
    for d, (p, r, flat) in zip(SPL, splash_state(tau)):
        e = d['e']; e.co = p; e.radius = max(r, 0.0001)
        if d['kind'] != 'pool':
            e.size_x = e.size_y = 1.0 / max(flat, 0.2) ** 0.5; e.size_z = flat
        if f is not None:
            e.keyframe_insert('co', frame=f); e.keyframe_insert('radius', frame=f)
            if d['kind'] != 'pool':
                for k in ('size_x', 'size_y', 'size_z'): e.keyframe_insert(k, frame=f)

# ---------------- hero material check ----------------
WHITE = D.materials['StickWhite']

# ---------------- pigeons (re-coloured low-poly gull rig, CC-BY simonaskLDE) ----------------
for mn, col in (('Seagull_Base_Material', (0.30, 0.32, 0.37)), ('Seagul_DarkEyeTail', (0.06, 0.06, 0.07)),
                ('Seagull_Yellow', (0.42, 0.20, 0.22)), ('Seagull_Red', (0.9, 0.35, 0.05))):
    m = D.materials.get(mn)
    if m and m.use_nodes:
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b:
            for l in list(b.inputs['Base Color'].links): m.node_tree.links.remove(l)
            b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.6
bird_root = D.objects.get('BIRDSRC') or D.objects['Sketchfab_model.002']
def hier(o): return [o] + [x for c in o.children for x in hier(c)]
SRC = hier(bird_root)
BC = D.collections.get('BirdSrc') or D.collections.new('BirdSrc')
if BC.name not in sc.collection.children: sc.collection.children.link(BC)
for o in SRC:
    if o.name not in BC.objects:
        for c in o.users_collection: c.objects.unlink(o)
        BC.objects.link(o)
bird_root.name = 'BIRDSRC'; bird_root.location = (0, 0, -50)
def copy_bird(i):
    mp = {}
    for o in SRC:
        n = o.copy(); mp[o] = n; COL.objects.link(n); n.name = f'FZ_bird{i:02d}_{o.type[:3]}'
    for o, n in mp.items():
        if o.parent in mp: n.parent = mp[o.parent]
        for m in n.modifiers:
            if m.type == 'ARMATURE' and m.object in mp: m.object = mp[m.object]
        if n.type == 'ARMATURE' or (n.animation_data and n.animation_data.action):
            pass
    root = mp[bird_root]; arm = next(n for o, n in mp.items() if o.type == 'ARMATURE')
    for n in mp.values():
        if n.animation_data: n.animation_data_clear()
    arm.data = arm.data  # shared armature data is fine; pose is per object
    return root, arm
SRC_ARM = next(o for o in SRC if o.type == 'ARMATURE')
ACT = D.actions.get('ArmatureAction'); ACT.use_fake_user = True
# flap pose sampler: evaluate the source action's fcurves at a phase (0..1)
def _fcurves(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for lay in act.layers:
            for strip in lay.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out
FC = _fcurves(ACT)
def flap_pose(arm, ph):
    fr = 0.5 + 19.5 * (ph % 1.0)
    vals = {}
    for fc in FC:
        vals.setdefault(fc.data_path, {})[fc.array_index] = fc.evaluate(fr)
    for path, comps in vals.items():
        try:
            pb_name = path.split('"')[1]; prop = path.split('.')[-1]
            pb = arm.pose.bones[pb_name]; cur = list(getattr(pb, prop))
            for k, v in comps.items(): cur[k] = v
            setattr(pb, prop, cur)
        except Exception: pass
rb = random.Random(5)
BIRDS = []
# frozen flock above the cafe / hero area, mostly climbing away from the street (startled by the cup)
spots = [(2.2, -3.0, 2.0), (2.9, -4.6, 2.6), (1.7, -5.6, 3.1), (3.6, -2.4, 3.0), (2.5, -1.4, 3.6), (4.2, -5.2, 2.2),
         (3.3, -6.6, 3.8), (1.9, -2.2, 4.3), (4.6, -3.6, 4.6), (3.0, -7.4, 2.5), (5.2, -1.6, 3.4), (2.4, -4.0, 5.0),
         (3.4, -3.3, 2.4), (2.6, -3.9, 3.9), (3.9, -4.6, 3.3), (2.2, -5.0, 4.6), (3.2, -5.8, 5.2), (4.4, -3.0, 4.0), (1.8, -3.4, 2.9), (3.7, -6.6, 4.4)]
for i, (x, y, z) in enumerate(spots):
    root, arm = copy_bird(i)
    root.scale = bird_root.scale * rb.uniform(0.9, 1.1)
    h = rb.uniform(-2.4, -0.9)        # heading (rad) roughly towards -y / +x (away from the cafe)
    BIRDS.append(dict(root=root, arm=arm, p=V(x, y, z), h=h, pitch=rb.uniform(0.15, 0.45), roll=rb.uniform(-0.3, 0.3),
                      ph=rb.uniform(0, 1), fr=rb.uniform(2.6, 3.4), v=V(math.cos(h), math.sin(h), 0) * rb.uniform(2.0, 3.0) + V(0, 0, rb.uniform(1.2, 2.2))))
def bird_state(b, tau_b):
    """tau_b: seconds relative to the freeze moment (negative = before, positive = after time restarts)"""
    p = b['p'] + b['v'] * tau_b + V(0, 0, 0.35 * tau_b * abs(tau_b))
    ph = b['ph'] + b['fr'] * tau_b
    return p, ph
# ---------------- frozen pedestrians (grey copies of the stick rig) ----------------
HERO = D.objects['StickRig']
FROZ = pbsdf('FZ_StickFrozen', (0.55, 0.58, 0.63), rough=0.55)
def copy_rig(name):
    kids = [c for c in HERO.children]
    r = HERO.copy(); r.name = name; COL.objects.link(r)
    if r.animation_data: r.animation_data_clear()
    for c in kids:
        n = c.copy(); n.name = name + '_' + c.name; COL.objects.link(n); n.parent = r
        n.parent_type = c.parent_type; n.parent_bone = c.parent_bone; n.matrix_parent_inverse = c.matrix_parent_inverse.copy()
        for m in n.modifiers:
            if m.type == 'ARMATURE': m.object = r
        for s in n.material_slots:
            if s.material and s.material.name == 'StickWhite':
                s.link = 'OBJECT'; s.material = FROZ
    return r
PEDS = {}
for nm in ('FZ_ped1', 'FZ_ped2', 'FZ_ped3', 'FZ_ped4'):
    PEDS[nm] = copy_rig(nm)
# ---------------- taxi ----------------
taxi = D.objects['CAR_Sedan']; taxi.animation_data_clear()
body = D.objects['Sedan Body_Body_0']
ym = pbsdf('FZ_TaxiYellow', (0.95, 0.62, 0.02), rough=0.25, coat=1.0)
body.material_slots[0].link = 'OBJECT'; body.material_slots[0].material = ym
sign = D.objects.new('FZ_taxisign', D.meshes.new('FZ_taxisign')); COL.objects.link(sign)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(sign.data); bm.free()
sign.parent = taxi; sign.scale = (0.5, 0.16, 0.12); sign.data.materials.append(pbsdf('FZ_TaxiSign', (1.0, 0.85, 0.4), rough=0.4, emis_s=2.0))
bpy.context.view_layer.update()
bz = max((body.matrix_world @ V(*v)).z for v in body.bound_box) - taxi.matrix_world.translation.z
sign.location = (0, 0.15, bz + 0.05)
# puddle + water splash by the front tyre
WATER = pbsdf('FZ_Water', (0.8, 0.88, 0.95), rough=0.02, trans=0.9, ior=1.33, coat=1.0)
PUD = pbsdf('FZ_Puddle', (0.02, 0.025, 0.03), rough=0.03, coat=1.0)
pud = D.objects.new('FZ_puddle', D.meshes.new('FZ_puddle')); COL.objects.link(pud)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=1.0, segments=40)
for v in bm.verts:
    a = math.atan2(v.co.y, v.co.x); v.co.x *= 1.0 + 0.25 * math.sin(3 * a); v.co.y *= 0.6 + 0.15 * math.cos(2 * a)
bm.to_mesh(pud.data); bm.free(); pud.data.materials.append(PUD); pud.scale = (1.1, 1.1, 1)
wmb = D.metaballs.get('FZ_water') or D.metaballs.new('FZ_water')
wmb.elements.clear(); wmb.animation_data_clear(); wmb.resolution = 0.02; wmb.render_resolution = 0.007; wmb.threshold = 0.6
if not wmb.materials: wmb.materials.append(WATER)
wat_ob = D.objects.new('FZ_water', wmb); COL.objects.link(wat_ob)
WAT = []
rw = random.Random(3)
for i in range(120):                       # local frame: x = outwards from the tyre, y = along the car, z = up
    a = rw.uniform(-0.8, 0.8); sp_ = rw.uniform(1.8, 4.2)
    WAT.append(dict(p0=V(0.05, rw.uniform(-0.2, 0.2), 0.03), v=V(sp_ * math.cos(a), sp_ * 0.55 * math.sin(a), rw.uniform(1.2, 3.0)),
                    r=rw.uniform(0.03, 0.055)))
for d in WAT:
    e = wmb.elements.new(); e.radius = d['r']; e.co = d['p0']; e.type = 'ELLIPSOID'; d['e'] = e
def apply_water(w, f=None):
    g = 9.81
    for d in WAT:
        e = d['e']
        if w <= 0: e.co = d['p0']; e.radius = 0.0001
        else:
            p = d['p0'] + d['v'] * w + V(0, 0, -0.5 * g * w * w)
            vel = d['v'] + V(0, 0, -g * w)
            r = d['r'] * min(1.0, w / 0.05)
            if p.z < 0.0: p.z = 0.0; r *= 0.6
            e.co = p; e.radius = max(r, 0.0001)
            st = 1 + min(1.5, vel.length * 0.35)
            e.size_x = st; e.size_y = 1 / st ** 0.5; e.size_z = 1 / st ** 0.5
            e.rotation = vel.to_track_quat('X', 'Z') if vel.length > 1e-3 else e.rotation
        if f is not None:
            for k in ('co', 'radius', 'size_x', 'size_y', 'size_z', 'rotation'): e.keyframe_insert(k, frame=f)
# ---------------- holograms ----------------
CY = emis('HoloCyan', (0.25, 0.85, 1.0), 9.0); DIM = emis('HoloDim', (0.15, 0.3, 0.45), 2.0); WH = emis('HoloWhite', (0.85, 0.97, 1.0), 7.0)
SHOCKM = D.materials.get('FZ_Shock') or D.materials.new('FZ_Shock'); SHOCKM.use_nodes = True; nt = SHOCKM.node_tree; nt.nodes.clear()
lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.08
pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 1.0
em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (0.35, 0.9, 1.0, 1); em.inputs[1].default_value = 14
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(lw.outputs['Facing'], pw.inputs[0]); nt.links.new(pw.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
SHOCKM.surface_render_method = 'BLENDED'; SHOCKM.use_backface_culling = False
shock = D.objects.new('FZ_shock', D.meshes.new('FZ_shock')); COL.objects.link(shock)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0); bm.to_mesh(shock.data); bm.free()
for p in shock.data.polygons: p.use_smooth = True
shock.data.materials.append(SHOCKM); shock.scale = (0.001,) * 3
# sky countdown ring
ring_root = D.objects.new('FZ_ring', None); COL.objects.link(ring_root)
def curve_circle(name, r, mat, depth, parent):
    cu = D.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = depth; cu.bevel_resolution = 4
    sp = cu.splines.new('NURBS'); n = 72; sp.points.add(n - 1)
    for i in range(n):
        a = math.pi / 2 - 2 * math.pi * i / n
        sp.points[i].co = (0, r * math.cos(a), r * math.sin(a), 1)
    sp.use_endpoint_u = True; sp.order_u = 3
    ob = D.objects.new(name, cu); COL.objects.link(ob); cu.materials.append(mat); ob.parent = parent; return ob
rtrack = curve_circle('FZ_ring_track', 1.0, DIM, 0.025, ring_root); rtrack.data.splines[0].use_cyclic_u = True
rarc = curve_circle('FZ_ring_arc', 1.0, CY, 0.05, ring_root)
RNUM = {}
for n in range(0, 11):
    td = D.curves.new(f'FZ_rnum{n}', 'FONT'); td.body = str(n); td.align_x = 'CENTER'; td.align_y = 'CENTER'; td.size = 0.95; td.extrude = 0.02
    ob = D.objects.new(f'FZ_rnum{n}', td); COL.objects.link(ob); td.materials.append(WH); ob.parent = ring_root
    ob.rotation_euler = (math.pi / 2, 0, math.pi / 2); ob.scale = (0.001,) * 3; RNUM[n] = ob
lab = D.curves.new('FZ_rlab', 'FONT'); lab.body = 'SECONDS LEFT'; lab.align_x = 'CENTER'; lab.size = 0.22
lob = D.objects.new('FZ_rlab', lab); COL.objects.link(lob); lab.materials.append(CY); lob.parent = ring_root
lob.rotation_euler = (math.pi / 2, 0, math.pi / 2); lob.location = (0, 0, -1.35)
ring_root.scale = (0.001,) * 3
# air-molecule grid (around the hero's hand, placed per shot)
MOLM = emis('FZ_Mol', (0.4, 0.9, 1.0), 6.0)
mol = D.objects.new('FZ_mol', D.meshes.new('FZ_mol')); COL.objects.link(mol)
bm = bmesh.new(); sp_ = 0.062; R = 0.38; n = int(R / sp_)
for i in range(-n, n + 1):
    for j in range(-n, n + 1):
        for k in range(-n, n + 1):
            c = V(i, j, k) * sp_
            jit = V(math.sin(i * 12.9 + j * 78.2 + k * 3.1), math.sin(i * 39.3 + j * 11.1 + k * 7.7), math.sin(i * 5.3 + j * 3.9 + k * 41.7)) * 0.012
            if c.length < R:
                g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0026 * (1.0 - 0.4 * c.length / R))
                bmesh.ops.translate(bm, verts=g['verts'], vec=c + jit)
bm.to_mesh(mol.data); bm.free(); mol.data.materials.append(MOLM); mol.scale = (0.001,) * 3
# glass block of frozen air
GL = D.materials.get('FZ_Glass') or D.materials.new('FZ_Glass'); GL.use_nodes = True; nt = GL.node_tree; nt.nodes.clear()
lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.25
gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.02; gl.inputs['Color'].default_value = (0.8, 0.95, 1.0, 1)
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs[0].default_value = (0.86, 0.95, 1.0, 1)
mx = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes.new('ShaderNodeOutputMaterial')
mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 0.9
nt.links.new(lw.outputs['Fresnel'], mm.inputs[0]); nt.links.new(mm.outputs[0], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
GL.surface_render_method = 'BLENDED'; GL.use_backface_culling = False
glass = D.objects.new('FZ_glass', D.meshes.new('FZ_glass')); COL.objects.link(glass)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.04, segments=3, affect='EDGES')
bm.to_mesh(glass.data); bm.free(); glass.data.materials.append(GL); glass.scale = (0.001,) * 3
edges = D.objects.new('FZ_glass_edges', glass.data.copy()); COL.objects.link(edges); edges.parent = glass
wm = edges.modifiers.new('wire', 'WIREFRAME'); wm.thickness = 0.008; edges.data.materials.clear(); edges.data.materials.append(emis('FZ_GlassEdge', (0.5, 0.85, 1.0), 2.5))
print('set ok', 'table top', round(TOP, 3), 'cup', tuple(round(v, 2) for v in CUP_P), 'birds', len(BIRDS), 'act', ACT.name if ACT else None, 'fc', len(FC))
