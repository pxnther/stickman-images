"""Giant Short: the Freeze Time street becomes a full city (instanced rows + far procedural blocks), the hero is scaled 100x.
Collections: G_CITY (extra rows, ground, far blocks), G_LAB (grid room + demo shapes). World W_CITY (clear sky + haze)."""
import bpy, bmesh, math, random
from mathutils import Vector, noise
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
LAB0 = V(0.0, 50000.0, 0.0)
def coll(name):
    c = D.collections.get(name)
    if c is None: c = D.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        if o.get('g_gen'): D.objects.remove(o, do_unlink=True)
    return c
def obj(name, data, col):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    o = D.objects.new(name, data); col.objects.link(o); o['g_gen'] = 1; return o
def nodes_mat(name):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); return m, nt
def pbsdf(name, col, rough=0.5, emis=0.0, ecol=None, metal=0.0):
    m, nt = nodes_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emis: b.inputs['Emission Color'].default_value = (*(ecol or col), 1); b.inputs['Emission Strength'].default_value = emis
    return m
def smooth(me):
    for p in me.polygons: p.use_smooth = True

# hide the other videos' effects
for n in ('PF_LAKE', 'SS_LAKE', 'SS_STREET'):
    c = D.collections.get(n)
    if c: c.hide_render = True; c.hide_viewport = True
for o in [x for x in D.collections['FZ'].all_objects if x is not None]:
    if o.name and any(k in o.name for k in ('shock', 'ring', 'mol', 'glass', 'splash', 'water', 'puddle', 'bird', 'coffee_surf')):
        o.hide_render = True; o.hide_viewport = True

CITY = coll('G_CITY')
# more building rows (the existing street is the pair at x=0 / x=16.2, rows repeat every 60 m along Y)
BA, BB = D.objects['BLD_A'], D.objects['BLD_B']; row = BA.instance_collection
existing = {(0.0, -11.6), (0.0, 48.4), (0.0, -71.6), (16.2, 4.0), (16.2, 64.0), (16.2, -56.0)}
k = 0
for xo in (-48.0, 0.0, 48.0):
    for yi in range(-4, 3):
        for (bx, by, rz) in ((xo, -11.6 + 60 * yi, 0.0), (xo + 16.2, 4.0 + 60 * yi, math.pi)):
            if (round(bx, 1), round(by, 1)) in existing: continue
            e = obj(f'G_Row{k}', None, CITY); e.instance_type = 'COLLECTION'; e.instance_collection = row
            e.location = (bx, by, 0); e.rotation_euler = (0, 0, rz); k += 1
# ground beyond the street
road = D.materials.get('asphalt_02_material_Road')
me = D.meshes.new('G_Ground'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6000); bm.to_mesh(me); bm.free()
g = obj('G_Ground', me, CITY); g.location = (0, 0, -0.08)
gm = pbsdf('G_GroundMat', (0.16, 0.16, 0.17), rough=0.9); me.materials.append(gm)
# far city: a grid of blocks (48 x 60 m cells like the real rows) out to 2.6 km, facades fade into a sky-coloured haze with distance
def haze_mix(nt, color_out, target_socket):
    cd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 250.0; mr.inputs['From Max'].default_value = 2600.0; mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 0.85
    nt.links.new(cd.outputs['View Distance'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0.70, 0.74, 0.82, 1)
    nt.links.new(mr.outputs['Result'], mx.inputs[0]); nt.links.new(color_out, mx.inputs[6]); nt.links.new(mx.outputs[2], target_socket)
    return mr
m, nt = nodes_mat('G_Facade')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.8
tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick')
br.inputs['Scale'].default_value = 0.22; br.inputs['Mortar Size'].default_value = 0.3
br.inputs['Color1'].default_value = (0.10, 0.12, 0.15, 1); br.inputs['Color2'].default_value = (0.14, 0.16, 0.19, 1); br.inputs['Mortar'].default_value = (0.36, 0.30, 0.25, 1)
nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
oi = nt.nodes.new('ShaderNodeObjectInfo'); cr = nt.nodes.new('ShaderNodeValToRGB')
cr.color_ramp.elements[0].color = (0.55, 0.42, 0.34, 1); cr.color_ramp.elements[1].color = (0.75, 0.70, 0.64, 1)
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.004; nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], cr.inputs[0])
mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 0.6
nt.links.new(cr.outputs[0], mul.inputs[6]); nt.links.new(br.outputs['Color'], mul.inputs[7])
haze_mix(nt, mul.outputs[2], b.inputs['Base Color'])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o_.inputs[0])
FAC = m
rs = random.Random(5); me = D.meshes.new('G_FarCity'); bm = bmesh.new(); nblk = 0
for ix in range(-54, 55):
    for iy in range(-44, 45):
        x = 8 + ix * 48.0; y = 4 + iy * 60.0
        if -80 < x - 8 < 100 and -270 < y < 210: continue
        if (x - 8) ** 2 + y ** 2 > 2600 ** 2: continue
        w_, d_ = rs.uniform(30, 38), rs.uniform(40, 50); h = rs.uniform(9, 30) * (2.2 if rs.random() < 0.06 else 1.0)
        gc = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w_, d_, h), verts=gc['verts']); bmesh.ops.translate(bm, vec=(x, y, h / 2), verts=gc['verts']); nblk += 1
bm.to_mesh(me); bm.free(); me.materials.append(FAC)
fc = obj('G_FarCity', me, CITY); fc.visible_shadow = False
# ground gets the same haze
gnt = gm.node_tree; gb = next(n for n in gnt.nodes if n.type == 'BSDF_PRINCIPLED')
rgb = gnt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (0.16, 0.16, 0.17, 1)
haze_mix(gnt, rgb.outputs[0], gb.inputs['Base Color'])
# lab (grid room copied from the ant Short) + demo shapes
LAB = coll('G_LAB')
LRM = next((m for m in D.meshes if m.name.startswith('ANT_LabRoom')), None)
if LRM is None:
    with D.libraries.load(r"C:\Users\Pxnther\Documents\WhatIFs\ANT SIZE\ant_size.blend") as (a, b_):
        b_.meshes = [n for n in a.meshes if n.startswith('ANT_LabRoom')][:1]
    LRM = next(m for m in D.meshes if m.name.startswith('ANT_LabRoom'))
lr = obj('G_LabRoom', LRM, LAB); lr.location = LAB0; lr.scale = (2, 2, 2)
SLAB = pbsdf('G_BoneMat', (0.85, 0.95, 1.0), rough=0.3, emis=0.6, ecol=(0.3, 0.85, 1.0))
CUBE = pbsdf('G_WeightMat', (1.0, 0.75, 0.2), rough=0.4, emis=0.8, ecol=(1.0, 0.6, 0.1))
SKIN = pbsdf('G_SkinMat', (1.0, 0.6, 0.55), rough=0.4, emis=0.5, ecol=(1.0, 0.4, 0.35))
HEAT = pbsdf('G_HeatMat', (1.0, 0.35, 0.08), rough=0.4, emis=2.5, ecol=(1.0, 0.3, 0.05))
def box(name, mat):
    me = D.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.02, segments=2, affect='EDGES'); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = obj(name, me, LAB); o.location = LAB0 + V(0, 0, -100); o.scale = (0.001,) * 3; return o
G_SLAB = box('G_Slab', SLAB); G_CUBE = box('G_Cube', CUBE); G_SKIN = box('G_SkinSlab', SKIN); G_HEAT = box('G_HeatCube', HEAT)

# world: clear sky with a light haze so the city fades into the distance
img = next((n.image for n in D.worlds['W_SKY'].node_tree.nodes if n.type == 'TEX_ENVIRONMENT'), None)
w = D.worlds.get('W_CITY') or D.worlds.new('W_CITY'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[1].default_value = 1.0
et = nt.nodes.new('ShaderNodeTexEnvironment'); et.image = img; nt.links.new(et.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs['Surface'])
wl = D.worlds.get('W_LAB') or D.worlds.new('W_LAB'); wl.use_nodes = True; nt = wl.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[0].default_value = (0.01, 0.025, 0.07, 1); nt.links.new(bg.outputs[0], out.inputs[0])
sc.eevee.volumetric_end = 4000.0
try: sc.eevee.volumetric_tile_size = '8'
except Exception: pass
cam = D.objects['Cam']; cam.data.clip_start = 0.05; cam.data.clip_end = 20000
print('giant set ok rows', k)
