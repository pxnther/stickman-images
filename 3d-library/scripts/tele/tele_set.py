"""Teleport Short: London = the Freeze Time street under an overcast London HDRI; LA = a sunny plaza (HDRI + paving);
Everest = a snowy ridge (HDRI + displaced snow). Props: takeaway cup, shockwave shell. Collections T_LA, T_EVEREST, T_FX."""
import bpy, bmesh, math, random
from mathutils import Vector, noise
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
LA0 = V(0.0, -20000.0, 0.0); EV0 = V(0.0, 20000.0, 0.0)
def coll(name):
    c = D.collections.get(name)
    if c is None: c = D.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        if o.get('t_gen'): D.objects.remove(o, do_unlink=True)
    return c
def obj(name, data, col):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    o = D.objects.new(name, data); col.objects.link(o); o['t_gen'] = 1; return o
def nodes_mat(name):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); return m, nt
def pbsdf(name, col, rough=0.5, emis=0.0, ecol=None):
    m, nt = nodes_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    if emis: b.inputs['Emission Color'].default_value = (*(ecol or col), 1); b.inputs['Emission Strength'].default_value = emis
    return m
def smooth(me):
    for p in me.polygons: p.use_smooth = True
for n in ('PF_LAKE', 'SS_LAKE', 'SS_STREET'):
    c = D.collections.get(n)
    if c: c.hide_render = True; c.hide_viewport = True
for o in [x for x in D.collections['FZ'].all_objects if x is not None]:
    if o.name and any(k in o.name for k in ('shock', 'ring', 'mol', 'glass', 'splash', 'water', 'puddle', 'coffee_surf')):
        o.hide_render = True; o.hide_viewport = True
LA = coll('T_LA'); EV = coll('T_EVEREST'); FX = coll('T_FX')
# LA plaza: warm paving + low planters, the palm HDRI does the rest
m, nt = nodes_mat('T_Paving')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.8
tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 0.9; br.inputs['Mortar Size'].default_value = 0.01
br.inputs['Color1'].default_value = (0.72, 0.62, 0.5, 1); br.inputs['Color2'].default_value = (0.8, 0.7, 0.58, 1); br.inputs['Mortar'].default_value = (0.45, 0.4, 0.33, 1)
nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o_.inputs[0])
me = D.meshes.new('T_LAground'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=60, segments=64); bm.to_mesh(me); bm.free(); me.materials.append(m)
g = obj('T_LAground', me, LA); g.location = LA0
PL = pbsdf('T_Planter', (0.85, 0.82, 0.76), rough=0.6); GR = pbsdf('T_Shrub', (0.12, 0.3, 0.08), rough=0.7)
for i, (x, y) in enumerate(((-5, 6), (5, 7), (-7, -3))):
    me = D.meshes.new(f'T_Planter{i}'); bm = bmesh.new(); gc = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(2.2, 2.2, 0.6), verts=gc['verts']); bmesh.ops.translate(bm, vec=(0, 0, 0.3), verts=gc['verts']); bm.to_mesh(me); bm.free(); me.materials.append(PL)
    o = obj(f'T_Planter{i}', me, LA); o.location = LA0 + V(x, y, 0)
    me = D.meshes.new(f'T_Shrub{i}'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.9); bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(GR)
    o = obj(f'T_Shrub{i}', me, LA); o.location = LA0 + V(x, y, 1.1); o.scale = (1.1, 1.1, 0.7)
# Everest: a displaced snow ridge falling away on both sides
m, nt = nodes_mat('T_Snow')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (0.92, 0.94, 0.98, 1); b.inputs['Roughness'].default_value = 0.55
b.inputs['Subsurface Weight'].default_value = 0.15
tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.5; nz.inputs['Detail'].default_value = 12
nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35
nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o_.inputs[0]); SNOW = m
me = D.meshes.new('T_Ridge'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=160, y_segments=160, size=120)
for v in bm.verts:
    x, y = v.co.x, v.co.y
    ridge = -0.035 * x * x * (1 + 0.3 * math.sin(y * 0.05))
    v.co.z = max(-160.0, ridge) + 2.0 * noise.noise(V(x * 0.08, y * 0.08, 0.5)) + 0.4 * noise.noise(V(x * 0.4, y * 0.4, 1.7)) - 0.004 * y * y * (y > 0)
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(SNOW)
r_ = obj('T_Ridge', me, EV); r_.location = EV0
ROCK = pbsdf('T_Rock', (0.18, 0.17, 0.17), rough=0.85)
rs = random.Random(3); me = D.meshes.new('T_Rocks'); bm = bmesh.new()
for i in range(40):
    c = V(rs.uniform(-40, 40), rs.uniform(-60, 60), 0); c.z = -0.035 * c.x * c.x - 0.4
    g_ = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rs.uniform(0.6, 2.5))
    for v in g_['verts']: v.co = v.co * (1 + 0.3 * noise.noise(v.co * 2 + V(i, 0, 0))) + c
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(ROCK)
rk = obj('T_Rocks', me, EV); rk.location = EV0
# FX: takeaway cup and the shockwave shell
CUPM = pbsdf('T_CupMat', (0.95, 0.94, 0.9), rough=0.5); LIDM = pbsdf('T_LidMat', (0.05, 0.05, 0.05), rough=0.3)
me = D.meshes.new('T_Cup'); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.032, radius2=0.045, depth=0.14)
bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(CUPM)
cup = obj('T_Cup', me, FX)
me = D.meshes.new('T_Lid'); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.047, radius2=0.04, depth=0.015)
bmesh.ops.translate(bm, vec=(0, 0, 0.075), verts=bm.verts); bm.to_mesh(me); bm.free(); me.materials.append(LIDM)
lid = obj('T_Lid', me, FX); lid.parent = cup
m, nt = nodes_mat('T_ShockMat')
lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.08
em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (0.75, 0.9, 1.0, 1)
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 4.0; mul.name = 'SHOCK'
nt.links.new(lw.outputs['Fresnel'], mul.inputs[0]); nt.links.new(mul.outputs[0], em.inputs['Strength'])
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(ad.outputs[0], o_.inputs[0])
try: m.surface_render_method = 'BLENDED'
except Exception: pass
me = D.meshes.new('T_Shock'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0); bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(m)
sh = obj('T_Shock', me, FX)
# worlds from HDRIs imported by name (see IMG_* below, filled by the import step)
def world(name, img, strength=1.0, rot=0.0):
    w = D.worlds.get(name) or D.worlds.new(name); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[1].default_value = strength
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, rot)
    et = nt.nodes.new('ShaderNodeTexEnvironment'); et.image = img
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], et.inputs['Vector']); nt.links.new(et.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0]); return w
for wn, key in (('W_LONDON', 'IMG_LONDON'), ('W_LA', 'IMG_LA'), ('W_EVEREST', 'IMG_EVEREST')):
    nm = globals().get(key)
    if nm and nm in D.images: world(wn, D.images[nm], 1.0, globals().get(key + '_ROT', 0.0))
cam = D.objects['Cam']; cam.data.clip_start = 0.02; cam.data.clip_end = 20000
print('tele set ok', [w.name for w in D.worlds])
