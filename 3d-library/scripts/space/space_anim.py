"""Space-without-a-suit shots (hero at normal scale, station hatch at the origin, Earth below)."""
import bpy, bmesh, math, json, random
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
exec(open(TEX + r"\space_set_v1.py", encoding='utf-8').read(), {'__name__': 'spset'})
exec(open(TEX + r"\wf_common_v2.py", encoding='utf-8').read(), globals())
TJ = json.load(open(TEX + r"\space_timing_v1.json"))
S = [s['start'] for s in TJ['scenes']]; END = TJ['duration']
def wt(word, after=0.0, default=None):
    for w in TJ['words']:
        if w['start'] >= after - 0.01 and w['word'].lower().strip('.,?!:') == word: return w['start']
    return default if default is not None else after
SPC = D.collections['SP_SPACE']; INC = D.collections['SP_INSIDE']
def _keep(o):
    if any(c.name.startswith('SP_') for c in o.users_collection): return True
    p = o
    while p:
        if p.name in ('StickRig', 'Cam', 'CamTgt', 'SUN') or p.name.startswith('Eye'): return True
        p = p.parent
    return False
for _o in D.objects:
    if not _keep(_o): _o.hide_render = True; _o.hide_viewport = True
DOOR = D.objects['SP_Door']
# small extra props: bubbles, breath puff, tether
def ensure(name, build, mat):
    o = D.objects.get(name)
    if o: D.objects.remove(o, do_unlink=True)
    me = D.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    o = D.objects.new(name, me); SPC.objects.link(o); o['sp_gen'] = 1; return o
BUBM = D.materials.get('SP_Bubble') or D.materials.new('SP_Bubble'); BUBM.use_nodes = True
bb = BUBM.node_tree.nodes.get('Principled BSDF')
if bb: bb.inputs['Base Color'].default_value = (0.85, 0.93, 1.0, 1); bb.inputs['Roughness'].default_value = 0.15; bb.inputs['Transmission Weight'].default_value = 0.0; bb.inputs['Emission Color'].default_value = (0.8, 0.9, 1.0, 1); bb.inputs['Emission Strength'].default_value = 0.6
PUFM = D.materials.get('SP_PuffMat') or D.materials.new('SP_PuffMat'); PUFM.use_nodes = True
pb_ = PUFM.node_tree.nodes.get('Principled BSDF')
if pb_: pb_.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1); pb_.inputs['Roughness'].default_value = 0.9; pb_.inputs['Emission Color'].default_value = (1, 1, 1, 1); pb_.inputs['Emission Strength'].default_value = 0.3
TETM = D.materials.get('SP_Dark')
BUB = [ensure(f'SP_Bub{i}', lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0), BUBM) for i in range(18)]
PUFF = [ensure(f'SP_Puff{i}', lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0), PUFM) for i in range(10)]
def tet(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.025, radius2=0.025, depth=1.0); bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
TETHER = ensure('SP_Tether', tet, TETM)
for o in BUB + PUFF + [TETHER, DOOR]:
    if o.animation_data: o.animation_data_clear()
key_hero_xform(1, (0, 0, 0), 1.0)
HATCH = V(0, 0.6, 0)
def hero_pos(t):
    if t < S[7] + 0.3: return HATCH + V(0.22 * t, -0.75 * t - 0.4, 0.05 * t)
    p1 = hero_pos(S[7] + 0.29)
    return p1.lerp(HATCH + V(0, -0.9, 0), eio((t - S[7] - 0.3) / (S[8] - S[7] - 0.4)))
def hero_R(t, spin=1.0):
    return Rm(pitch=0.35 * math.sin(0.45 * t) + 0.25 * t * spin * 0.12, roll=0.3 * math.sin(0.33 * t + 1), yaw=0.2 * t * spin + 0.5)
def float_pose(f, t, k=1.0, hands=None, head=(0, 0, 0)):
    C = hero_pos(t); R = hero_R(t)
    hl, fl = flail(t * 0.6, k)
    if hands is not None: hl = hands
    pose_local(f, C, R, hl, fl, head=head); return C, R
def face_of(C, R): return C + R @ V(0, -0.02, 0.72)
def key_door(f, open_):
    DOOR.rotation_euler = (0, 0, -1.9 * open_); DOOR.keyframe_insert('rotation_euler', frame=f)
def key_bubbles(f, t, on, face, fwd):
    rs = random.Random(9)
    for i, o in enumerate(BUB):
        ph = (t * 0.9 + i / len(BUB)) % 1.0
        if not on: hide(o, f); continue
        off = V(rs.uniform(-0.05, 0.05), 0, rs.uniform(-0.04, 0.02))
        p = face + fwd * (0.15 + 0.12 * ph) + off + V(0, 0, 0.08 * ph)
        r = 0.006 + 0.012 * math.sin(math.pi * ph)
        show(o, f, p, (r, r, r))
def key_puff(f, t, t0, face, fwd):
    for i, o in enumerate(PUFF):
        u = (t - t0 - i * 0.04) / 1.6
        if u <= 0 or u >= 1: hide(o, f); continue
        p = face + fwd * (0.2 + 0.9 * u) + V(math.sin(i * 2.1) * 0.15 * u, 0, math.cos(i * 1.7) * 0.12 * u)
        r = (0.05 + 0.18 * u) * (1 - u) * 1.6; show(o, f, p, (r, r, r))
def key_tether(f, on, a, b):
    if not on: hide(TETHER, f); return
    d = b - a; TETHER.location = a; TETHER.rotation_euler = V(0, 0, 1).rotation_difference(d.normalized()).to_euler()
    TETHER.scale = (1, 1, d.length)
    TETHER.keyframe_insert('location', frame=f); TETHER.keyframe_insert('rotation_euler', frame=f); TETHER.keyframe_insert('scale', frame=f)
SPACE = ['SP_SPACE']; INSIDE = ['SP_INSIDE', 'SP_SPACE']
EYEW = 1.3
def common(f, t, door=1.0, bubbles=False, face=None, fwd=None, puff_t0=None, tether=False):
    key_door(f, door); key_bubbles(f, t, bubbles, face or V(0, 0, 0), fwd or V(0, -1, 0))
    key_puff(f, t, puff_t0 if puff_t0 is not None else -100, face or V(0, 0, 0), fwd or V(0, -1, 0))
    key_tether(f, tether, HATCH + V(0.2, 0.3, 0.2), hero_pos(t) + V(0, 0, 0.85) if tether else V(0, 0, 0))

@shot('SP01_hook', 0.0, S[1], SPACE, 'W_SPACE')
def sp01(t, f):
    C, R = float_pose(f, t, 1.3, head=(-0.2, 0, 0)); eyes(f, 1.0, EYEW); common(f, t)
    if t < 1.6:                      # outside the station: he tumbles out of the open hatch, Earth below
        u = eio(t / 1.6); key_cam(f, V(lerp(5.5, 5.0, u), -7.5, lerp(-1.8, -1.5, u)), C + V(0, 0.8, 0.4), 22, 11.0)
    else:                            # 1b: close on his face as he spins
        fc = face_of(C, R); key_cam(f, fc + V(0.6, -1.1, 0.2), fc, 45, 4.0)

@shot('SP02_noexplode', S[1], S[3], SPACE, 'W_SPACE')
def sp02(t, f):
    C, R = float_pose(f, t, 0.9); eyes(f, blink(t, 2.4), EYEW); common(f, t)
    u = eio((t - S[1]) / (S[3] - S[1]))                    # slow orbit, Earth filling the background (also the lung-neon plate)
    a = lerp(-0.6, 0.4, u); cp = C + V(math.sin(a) * 5.5, -math.cos(a) * 5.5, lerp(1.6, 2.2, u))
    key_cam(f, cp, C + V(0, 0, 0.7), 30, 8.0)

@shot('SP04_breathe', S[3], S[5], SPACE, 'W_SPACE')
def sp04(t, f):
    C, R = float_pose(f, t, 0.6); fwd = (R @ V(0, -1, 0)).normalized(); fc = face_of(C, R)
    tb = wt('breathe', S[3], S[3] + 0.1)
    eyes(f, blink(t, 2.2), EYEW)
    bub = t >= S[4]
    common(f, t, bubbles=bub, face=fc, fwd=fwd, puff_t0=tb)
    if t < S[4]:                     # medium: he breathes out a cloud of mist (countdown neon in the edit)
        u = eio((t - S[3]) / (S[4] - S[3])); key_cam(f, fc + fwd * 2.4 + V(0.8, 0, 0.3) + V(0, 0, 0.3 * u), fc + fwd * 0.4, 32, 5.0)
    else:                            # 5: face macro, tiny bubbles where his tongue would be
        key_cam(f, fc + fwd * 0.75 + V(0.25, 0, 0.05), fc + fwd * 0.15, 55, 2.8)

@shot('SP06_heat', S[5], S[7], SPACE, 'W_SPACE')
def sp06(t, f):
    C, R = float_pose(f, t, 0.5); eyes(f, blink(t, 2.8), EYEW); common(f, t)
    if t < S[6]:                     # 6: wide, a tiny warm figure against black space (thermal look in the edit)
        u = eio((t - S[5]) / (S[6] - S[5])); key_cam(f, C + V(-6, -9, lerp(3, 4, u)), C + V(0, 0, 0.6), 30, 11.0)
    else:                            # 7: into the sun: hard light on him (flare in the edit)
        u = eio((t - S[6]) / (S[7] - S[6])); key_cam(f, C + V(-3.2, -2.0, 1.0 + 0.3 * u), C + V(0, 0, 0.8), 35, 6.0)

@shot('SP08_pulled', S[7], S[8], SPACE, 'W_SPACE')
def sp08(t, f):
    C, R = float_pose(f, t, 0.3); eyes(f, lerp(1.0, 0.25, ramp(t, S[7], S[7] + 1.2)), 1.0)
    common(f, t, door=1.0, tether=True)
    u = eio((t - S[7]) / (S[8] - S[7]))                    # wide: the tether reels him back to the hatch
    key_cam(f, V(lerp(9, 8, u), lerp(-10, -9, u), 3.0), V(0, -3.5 * (1 - u), 0.8), 26, 11.0)

@shot('SP09_loop', S[8], END, INSIDE, 'W_SPACE')
def sp09(t, f):
    # inside the airlock: he floats to the door and reaches for the handle (flows into frame 0)
    tl = (t - S[8]) / (END - S[8])
    C = V(0.2, 3.4, -0.6).lerp(V(0.4, 2.6, -0.85), eio(tl)); R = Rm(pitch=0.25, yaw=math.pi + 0.15)
    hand = V(0.9, 1.45, 0.0)
    reach = eio(cl(tl * 1.4))
    hl = [L_(C, R, (0.25, -0.03, -0.075)).lerp(hand, reach), L_(C, R, (-0.3, 0.05, -0.1))]
    pose_w(f, C, R, hl, [L_(C, R, (0.12, 0.15, -0.7)), L_(C, R, (-0.12, 0.05, -0.75))], head=(0.1, 0, 0))
    eyes(f, blink(t, 2.5), 1.0); common(f, t, door=0.0)
    key_cam(f, V(-1.4, 4.9, 0.3), V(0.5, 2.2, -0.2), 20, 8.0)
