"""Space-without-a-suit Short: procedural station module with an airlock, Earth below, starfield. Collections SP_SPACE, SP_INSIDE."""
import bpy, bmesh, math, random
from mathutils import Vector
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
def coll(name):
    c = D.collections.get(name)
    if c is None: c = D.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        if o.get('sp_gen'): D.objects.remove(o, do_unlink=True)
    return c
def obj(name, data, col):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    o = D.objects.new(name, data); col.objects.link(o); o['sp_gen'] = 1; return o
def nodes_mat(name):
    m = D.materials.get(name) or D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); return m, nt
def pbsdf(name, col, rough=0.5, metal=0.0, emis=0.0, ecol=None):
    m, nt = nodes_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emis: b.inputs['Emission Color'].default_value = (*(ecol or col), 1); b.inputs['Emission Strength'].default_value = emis
    return m
def smooth(me):
    for p in me.polygons: p.use_smooth = True
def mesh_obj(name, col, mat, build):
    me = D.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free(); me.materials.append(mat); return obj(name, me, col)

SP = coll('SP_SPACE'); IN = coll('SP_INSIDE')
HULL = pbsdf('SP_Hull', (0.82, 0.82, 0.80), rough=0.45, metal=0.3)
DARK = pbsdf('SP_Dark', (0.06, 0.06, 0.07), rough=0.4, metal=0.6)
GOLD = pbsdf('SP_Foil', (0.9, 0.62, 0.2), rough=0.25, metal=1.0)
LAMP = pbsdf('SP_Lamp', (1, 1, 1), emis=6.0, ecol=(1.0, 0.95, 0.85))
RED = pbsdf('SP_Warn', (0.8, 0.05, 0.04), rough=0.4, emis=1.5, ecol=(1.0, 0.1, 0.05))
m, nt = nodes_mat('SP_Panel')                      # solar panel: dark blue cells with a thin grid
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.2; b.inputs['Metallic'].default_value = 0.6
br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.5; br.inputs['Mortar Size'].default_value = 0.02
br.inputs['Color1'].default_value = (0.02, 0.05, 0.16, 1); br.inputs['Color2'].default_value = (0.03, 0.07, 0.2, 1); br.inputs['Mortar'].default_value = (0.6, 0.6, 0.65, 1)
tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o_.inputs[0]); PANEL = m

# station module: a long cylinder along X, the airlock hatch on its -Y side at the origin side
R_H = 4.5
def hull(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=R_H, radius2=R_H, depth=34.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'Y'))
h = mesh_obj('SP_Hull', SP, HULL, hull); h.location = (0, R_H + 1.2, 0); smooth(h.data)
for i, x in enumerate((-16.5, -6, 6, 16.5)):        # ribs
    def rib(bm, x=x):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=R_H + 0.25, radius2=R_H + 0.25, depth=0.6)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'Y'))
    r_ = mesh_obj(f'SP_Rib{i}', SP, DARK, rib); r_.location = (x, R_H + 1.2, 0)
def frame_(bm):                                     # hatch frame (square ring) on the hull's -Y face
    for (sx, sz, px, pz) in ((3.0, 0.35, 0, 1.45), (3.0, 0.35, 0, -1.45), (0.35, 3.25, 1.45, 0), (0.35, 3.25, -1.45, 0)):
        g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(sx, 0.6, sz), verts=g['verts']); bmesh.ops.translate(bm, vec=(px, 0, pz), verts=g['verts'])
fr = mesh_obj('SP_HatchFrame', SP, DARK, frame_); fr.location = (0, 1.2, 0)
def door(bm):
    g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(2.55, 0.25, 2.55), verts=g['verts']); bmesh.ops.translate(bm, vec=(1.275, 0, 0), verts=g['verts'])
DOOR = mesh_obj('SP_Door', SP, HULL, door); DOOR.location = (-1.27, 1.0, 0)     # hinged on its left edge; rotate Z to open
def handle(bm):
    g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.12, 0.25, 0.7), verts=g['verts']); bmesh.ops.translate(bm, vec=(2.15, -0.2, 0), verts=g['verts'])
hd = mesh_obj('SP_Handle', SP, RED, handle); hd.parent = DOOR
for i, (y0, sgn) in enumerate(((R_H + 1.2, 1), (R_H + 1.2, -1))):          # solar wings out along +/-Z
    def wing(bm, sgn=sgn):
        g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(26, 0.15, 11), verts=g['verts']); bmesh.ops.translate(bm, vec=(0, 0, sgn * 13.5), verts=g['verts'])
    w = mesh_obj(f'SP_Wing{i}', SP, PANEL, wing); w.location = (4, y0, sgn * (R_H + 1.5))
    def mast(bm, sgn=sgn):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.25, radius2=0.25, depth=6.0)
    ms = mesh_obj(f'SP_Mast{i}', SP, DARK, mast); ms.location = (4, y0, sgn * (R_H + 3.0))
def foil(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=R_H * 0.9, radius2=R_H * 0.6, depth=5.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'Y'))
fo = mesh_obj('SP_Foil', SP, GOLD, foil); fo.location = (19.5, R_H + 1.2, 0)
for i, x in enumerate((-3.5, 3.5)):                 # lights beside the hatch
    def lb(bm):
        g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.5, 0.2, 0.25), verts=g['verts'])
    l_ = mesh_obj(f'SP_Light{i}', SP, LAMP, lb); l_.location = (x, 0.95, 1.9)
# airlock interior: a small lit room behind the hatch
def room(bm):
    g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(4.0, 4.0, 3.6), verts=g['verts'])
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
rm = mesh_obj('SP_Room', IN, pbsdf('SP_RoomMat', (0.75, 0.77, 0.8), rough=0.5), room); rm.location = (0, 3.3, 0)
for i, z in enumerate((1.7,)):
    def ceil(bm):
        g = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(2.6, 0.6, 0.05), verts=g['verts'])
    c_ = mesh_obj('SP_RoomLamp', IN, LAMP, ceil); c_.location = (0, 3.3, z)
ld = D.lights.get('SP_RoomPoint') or D.lights.new('SP_RoomPoint', 'POINT'); ld.energy = 250; ld.color = (1.0, 0.95, 0.88)
lo = obj('SP_RoomPoint', ld, IN); lo.location = (0, 3.3, 1.3)
# Earth: big procedural globe far below (continents, clouds, thin atmosphere glow)
ER = 6000.0; EC = V(0, 1500, -6900)
m, nt = nodes_mat('SP_Earth')
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.6
tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 8.0
nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
land = nt.nodes.new('ShaderNodeValToRGB'); land.color_ramp.interpolation = 'CONSTANT'
land.color_ramp.elements[0].color = (0.01, 0.06, 0.2, 1); land.color_ramp.elements[1].position = 0.56; land.color_ramp.elements[1].color = (0.14, 0.22, 0.08, 1)
el = land.color_ramp.elements.new(0.64); el.color = (0.35, 0.3, 0.18, 1)
nt.links.new(nz.outputs['Fac'], land.inputs[0])
cn = nt.nodes.new('ShaderNodeTexNoise'); cn.inputs['Scale'].default_value = 5.0; cn.inputs['Detail'].default_value = 10.0; cn.inputs['Distortion'].default_value = 1.5
nt.links.new(tc.outputs['Object'], cn.inputs['Vector'])
cr = nt.nodes.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.5; cr.inputs['From Max'].default_value = 0.7
nt.links.new(cn.outputs['Fac'], cr.inputs['Value'])
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0.95, 0.95, 0.97, 1)
nt.links.new(cr.outputs['Result'], mx.inputs[0]); nt.links.new(land.outputs[0], mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.15
em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (0.3, 0.6, 1.0, 1)
mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 3.0
nt.links.new(lw.outputs['Facing'], mu.inputs[0]); nt.links.new(mu.outputs[0], em.inputs['Strength'])
ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(b.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(ad.outputs[0], o_.inputs[0]); EARTHM = m
def sphere(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=64, radius=1.0)
ea = mesh_obj('SP_Earth', SP, EARTHM, sphere); ea.location = EC; ea.scale = (ER,) * 3; smooth(ea.data)
# world: black with stars
w = D.worlds.get('W_SPACE') or D.worlds.new('W_SPACE'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 220.0
nt.links.new(tc.outputs['Generated'], vo.inputs['Vector'])
st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['From Min'].default_value = 0.035; st.inputs['From Max'].default_value = 0.0
st.inputs['To Min'].default_value = 0.0; st.inputs['To Max'].default_value = 3.0; st.clamp = True
nt.links.new(vo.outputs['Distance'], st.inputs['Value'])
gate = nt.nodes.new('ShaderNodeMath'); gate.operation = 'GREATER_THAN'; gate.inputs[1].default_value = 0.82
nt.links.new(vo.outputs['Color'], gate.inputs[0])
mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(st.outputs['Result'], mm.inputs[0]); nt.links.new(gate.outputs[0], mm.inputs[1])
bg.inputs[0].default_value = (1, 1, 1, 1); nt.links.new(mm.outputs[0], bg.inputs['Strength']); nt.links.new(bg.outputs[0], out.inputs[0])
cam = D.objects['Cam']; cam.data.clip_start = 0.02; cam.data.clip_end = 40000
print('space set ok')
