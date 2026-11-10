"""Invisible Short: procedural kitchen (I_KITCHEN), glass hero material switch, sandwich + food chunks, rain props (I_RAIN)."""
import bpy, bmesh, math, random
from mathutils import Vector, noise
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
K0 = V(0.0, -30000.0, 0.0)
def coll(name):
    c = D.collections.get(name)
    if c is None: c = D.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        if o.get('i_gen'): D.objects.remove(o, do_unlink=True)
    return c
def obj(name, data, col):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    o = D.objects.new(name, data); col.objects.link(o); o['i_gen'] = 1; return o
def nodes_mat(name):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); return m, nt
def pbsdf(name, col, rough=0.5, metal=0.0, emis=0.0, ecol=None, trans=0.0, ior=1.45):
    m, nt = nodes_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    if emis: b.inputs['Emission Color'].default_value = (*(ecol or col), 1); b.inputs['Emission Strength'].default_value = emis
    return m
def smooth(me):
    for p in me.polygons: p.use_smooth = True
def box(name, col, mat, size, loc, bevel=0.0):
    me = D.meshes.new(name); bm = bmesh.new(); g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=g['verts'])
    if bevel: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=3, affect='EDGES')
    bm.to_mesh(me); bm.free(); me.materials.append(mat)
    if bevel: smooth(me)
    o = obj(name, me, col); o.location = loc; return o
for n in ('PF_LAKE', 'SS_LAKE', 'SS_STREET'):
    c = D.collections.get(n)
    if c: c.hide_render = True; c.hide_viewport = True
for o in [x for x in D.collections['FZ'].all_objects if x is not None]:
    if o.name and any(k in o.name for k in ('shock', 'ring', 'mol', 'glass', 'splash', 'water', 'puddle', 'coffee_surf')):
        o.hide_render = True; o.hide_viewport = True
KIT = coll('I_KITCHEN'); RAIN = coll('I_RAIN'); FOOD = coll('I_FOOD')
# ---- kitchen (6 x 5 m room, open towards -Y where the camera sits) ----
m, nt = nodes_mat('I_Floor')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.35
tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 1.2; wv.inputs['Distortion'].default_value = 6
nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.32, 0.18, 0.08, 1); cr.color_ramp.elements[1].color = (0.55, 0.34, 0.17, 1)
nt.links.new(wv.outputs['Fac'], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs['Base Color'])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o_.inputs[0]); FLOOR = m
m, nt = nodes_mat('I_Tiles')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.15
br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 6.0; br.inputs['Mortar Size'].default_value = 0.012; br.offset = 0.0
br.inputs['Color1'].default_value = (0.82, 0.86, 0.85, 1); br.inputs['Color2'].default_value = (0.78, 0.83, 0.82, 1); br.inputs['Mortar'].default_value = (0.45, 0.45, 0.43, 1)
tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o_.inputs[0]); TILES = m
WALLP = pbsdf('I_Paint', (0.86, 0.80, 0.70), rough=0.8)
CAB = pbsdf('I_Cabinet', (0.20, 0.32, 0.30), rough=0.5); TOP = pbsdf('I_Counter', (0.09, 0.09, 0.1), rough=0.25)
STEEL = pbsdf('I_Steel', (0.8, 0.8, 0.82), rough=0.25, metal=1.0); WOOD = pbsdf('I_TableWood', (0.55, 0.36, 0.2), rough=0.4)
WIN = pbsdf('I_Window', (1, 1, 1), emis=4.0, ecol=(0.85, 0.92, 1.0))
box('I_Floor', KIT, FLOOR, (6, 5, 0.1), K0 + V(0, 1.0, -0.05))
box('I_WallBack', KIT, TILES, (6, 0.1, 2.8), K0 + V(0, 3.5, 1.4))
box('I_WallL', KIT, WALLP, (0.1, 5, 2.8), K0 + V(-3.0, 1.0, 1.4))
box('I_WallR', KIT, WALLP, (0.1, 5, 2.8), K0 + V(3.0, 1.0, 1.4))
box('I_Ceil', KIT, WALLP, (6, 5, 0.1), K0 + V(0, 1.0, 2.85))
box('I_CounterBase', KIT, CAB, (4.2, 0.62, 0.86), K0 + V(-0.6, 3.15, 0.43), 0.01)
box('I_CounterTop', KIT, TOP, (4.3, 0.66, 0.04), K0 + V(-0.6, 3.13, 0.88), 0.005)
box('I_Upper', KIT, CAB, (3.2, 0.35, 0.7), K0 + V(-1.1, 3.27, 2.05), 0.01)
box('I_Fridge', KIT, STEEL, (0.8, 0.7, 1.9), K0 + V(2.35, 3.05, 0.95), 0.02)
box('I_Window', KIT, WIN, (0.04, 1.3, 1.1), K0 + V(-2.94, 1.3, 1.55))
box('I_Sink', KIT, STEEL, (0.6, 0.4, 0.05), K0 + V(-1.4, 3.1, 0.9))
box('I_TableTop', KIT, WOOD, (1.3, 0.8, 0.05), K0 + V(0.2, 1.4, 0.76), 0.01)
for i, (x, y) in enumerate(((-0.35, -0.3), (0.35, -0.3), (-0.35, 0.3), (0.35, 0.3))):
    box(f'I_TableLeg{i}', KIT, WOOD, (0.06, 0.06, 0.74), K0 + V(0.2 + x * 1.6, 1.4 + y, 0.37))
FRUIT = pbsdf('I_Fruit', (0.85, 0.35, 0.05), rough=0.4)
for i in range(3):
    me = D.meshes.new(f'I_Orange{i}'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.045); bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(FRUIT)
    o = obj(f'I_Orange{i}', me, KIT); o.location = K0 + V(-0.1 + 0.09 * i, 1.55, 0.83)
ld = D.lights.get('I_CeilLight') or D.lights.new('I_CeilLight', 'AREA'); ld.energy = 260; ld.size = 2.0; ld.color = (1.0, 0.94, 0.85)
lo = obj('I_CeilLight', ld, KIT); lo.location = K0 + V(0, 1.2, 2.75)
lw = D.lights.get('I_WinLight') or D.lights.new('I_WinLight', 'AREA'); lw.energy = 400; lw.size = 1.3; lw.color = (0.85, 0.92, 1.0)
lwo = obj('I_WinLight', lw, KIT); lwo.location = K0 + V(-2.85, 1.3, 1.55); lwo.rotation_euler = (0, -math.pi / 2, 0)
# ---- glass switch on the hero material: Mix(original, glass) keyed by GLASSMIX, glass IOR keyed by GLASSIOR ----
WHITE = D.materials['StickWhite']; nt = WHITE.node_tree
for n in [n for n in nt.nodes if n.name in ('GLASSMIX', 'GLASSBSDF')]: nt.nodes.remove(n)
out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); orig = out.inputs['Surface'].links[0].from_socket
gl = nt.nodes.new('ShaderNodeBsdfPrincipled'); gl.name = 'GLASSBSDF'
gl.inputs['Base Color'].default_value = (1, 1, 1, 1); gl.inputs['Roughness'].default_value = 0.02; gl.inputs['Transmission Weight'].default_value = 1.0; gl.inputs['IOR'].default_value = 1.33
mx = nt.nodes.new('ShaderNodeMixShader'); mx.name = 'GLASSMIX'; mx.inputs[0].default_value = 0.0
nt.links.new(orig, mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
try:
    WHITE.surface_render_method = 'DITHERED'; WHITE.use_raytrace_refraction = True
except Exception: pass
# ---- sandwich (parent empty), crumbs, food chunks ----
BREAD = pbsdf('I_Bread', (0.86, 0.66, 0.38), rough=0.8); CRUST = pbsdf('I_Crust', (0.55, 0.32, 0.12), rough=0.8)
LET = pbsdf('I_Lettuce', (0.3, 0.6, 0.12), rough=0.5); TOM = pbsdf('I_Tomato', (0.8, 0.1, 0.05), rough=0.3); CHE = pbsdf('I_Cheese', (0.95, 0.75, 0.15), rough=0.4)
emp = obj('I_Sandwich', None, FOOD); emp.empty_display_size = 0.1; emp.location = K0
def slab(name, mat, size, z, bevel=0.012):
    o = box(name, FOOD, mat, size, V(0, 0, z), bevel); o.parent = emp; return o
slab('I_BreadBot', BREAD, (0.12, 0.11, 0.022), -0.022); slab('I_BreadTop', BREAD, (0.12, 0.11, 0.022), 0.03)
slab('I_Lettuce', LET, (0.135, 0.125, 0.006), -0.007, 0.002); slab('I_Cheese', CHE, (0.118, 0.108, 0.005), 0.003, 0.001)
slab('I_Tomato', TOM, (0.11, 0.1, 0.008), 0.011, 0.003)
CHUNKS = []
for i, mat in enumerate((BREAD, LET, TOM, BREAD, CHE, BREAD, LET, BREAD)):
    me = D.meshes.new(f'I_Chunk{i}'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.022)
    for v in bm.verts: v.co *= 1 + 0.3 * noise.noise(v.co * 60 + V(i, 0, 0))
    bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(mat)
    o = obj(f'I_Chunk{i}', me, FOOD); o.location = K0 + V(0, 0, -50); CHUNKS.append(o)
CRUMBS = []
for i in range(10):
    o = box(f'I_Crumb{i}', FOOD, BREAD, (0.01, 0.008, 0.006), K0 + V(0, 0, -50)); CRUMBS.append(o)
# ---- rain props ----
WATER = pbsdf('I_Water', (0.75, 0.85, 0.92), rough=0.03, trans=0.7, ior=1.33)
DROPS = []; SPLS = []
for i in range(40):
    me = D.meshes.new(f'I_Drop{i}'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0); bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(WATER)
    o = obj(f'I_Drop{i}', me, RAIN); o.scale = (0.001,) * 3; DROPS.append(o)
    me = D.meshes.new(f'I_Spl{i}'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=1.0); bm.to_mesh(me); bm.free(); smooth(me); me.materials.append(WATER)
    o = obj(f'I_Spl{i}', me, RAIN); o.scale = (0.001,) * 3; SPLS.append(o)
# ---- worlds ----
w = D.worlds.get('W_KITCHEN') or D.worlds.new('W_KITCHEN'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
o_ = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[0].default_value = (0.55, 0.6, 0.68, 1); bg.inputs[1].default_value = 0.6
nt.links.new(bg.outputs[0], o_.inputs[0])
img = globals().get('IMG_RAIN')
if img and img in D.images:
    w = D.worlds.get('W_RAIN') or D.worlds.new('W_RAIN'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[1].default_value = 0.8
    et = nt.nodes.new('ShaderNodeTexEnvironment'); et.image = D.images[img]; nt.links.new(et.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], o_.inputs[0])
cam = D.objects['Cam']; cam.data.clip_start = 0.01; cam.data.clip_end = 5000
print('invis set ok')
