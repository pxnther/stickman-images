"""Plane-fall Short: hero falling poses in any orientation, shots on one global timeline, per-shot render settings."""
import bpy, math, json, random
from mathutils import Vector, Matrix, Euler, Quaternion
sc = bpy.context.scene; D = bpy.data
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
G = {'__name__': 'pfset'}
exec(open(TEX + r"\pf_set_v7.py", encoding='utf-8').read(), G)
V = G['V']; FPS = 30
def F(t): return int(round(t * FPS)) + 1
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = cl(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def ramp(t, a, b): return ss((t - a) / (b - a))
def eio(u): u = cl(u); return 0.5 - 0.5 * math.cos(math.pi * u)
HERO = D.objects['StickRig']; P = HERO.pose.bones
cam = D.objects['Cam']; tgt = D.objects['CamTgt']; sc.camera = cam
cam.data.clip_start = 0.05; cam.data.clip_end = 150000
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt
HERO.location = (0, 0, 0); HERO.rotation_euler = (0, 0, 0)
for pb in P: pb.rotation_mode = 'QUATERNION' if pb.name in ('hips', 'IK_foot.L', 'IK_foot.R') else 'XYZ'
EYES = [D.objects['Eye.L'], D.objects['Eye.R']]; EYE0 = [tuple(e.scale) for e in EYES]
for o in [HERO, cam, tgt, cam.data] + EYES:
    if o.animation_data: o.animation_data_clear()

# ---------------- posing in a free body frame ----------------
def Rm(pitch=0.0, roll=0.0, yaw=0.0):
    """body orientation: yaw about world Z, then pitch (forward tilt, +90 = belly down), then roll"""
    return (Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(pitch, 3, 'X') @ Matrix.Rotation(roll, 3, 'Y'))
def setR(pb, pos, R):
    pb.matrix = Matrix.Translation(V(*pos)) @ (R @ pb.bone.matrix_local.to_3x3()).to_4x4()
def setT(pb, pos):
    pb.matrix = Matrix.Translation(V(*pos)) @ pb.bone.matrix_local.to_3x3().to_4x4()
def pose(f, C, R, hands, feet, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), knees=None, elbows=None):
    """hands/feet in hero-local coords relative to the hips (x = his left, y = his back, z = up)."""
    C = V(*C)
    W = lambda p: C + R @ V(*p)
    setR(P['hips'], C, R)
    for S, fp in zip('LR', feet):
        sg = 1 if S == 'L' else -1
        setR(P['IK_foot.' + S], W(fp), R)
        kn = knees[0 if S == 'L' else 1] if knees else (fp[0] * 0.9, -0.55, (fp[2]) * 0.5)
        setT(P['pole_knee.' + S], W(kn))
        eb = elbows[0 if S == 'L' else 1] if elbows else (sg * 0.55, 0.45, 0.05)
        setT(P['pole_elbow.' + S], W(eb))
    for S, hp in zip('LR', hands): setT(P['IK_hand.' + S], W(hp))
    P['spine'].rotation_euler = spine; P['neck'].rotation_euler = neck; P['head'].rotation_euler = head
    for n in ('hips', 'IK_foot.L', 'IK_foot.R'):
        P[n].keyframe_insert('location', frame=f); P[n].keyframe_insert('rotation_quaternion', frame=f)
    for n in ('pole_knee.L', 'pole_knee.R', 'pole_elbow.L', 'pole_elbow.R', 'IK_hand.L', 'IK_hand.R'): P[n].keyframe_insert('location', frame=f)
    for n in ('spine', 'neck', 'head'): P[n].keyframe_insert('rotation_euler', frame=f)
def eyes(f, open_=1.0, wide=1.0):
    for e, s0 in zip(EYES, EYE0):
        e.scale = (s0[0] * wide, s0[1] * wide, s0[2] * max(0.12, open_) * wide); e.keyframe_insert('scale', frame=f)
# local pose library (hips at origin)
STAND_H = ((0.25, -0.03, -0.075), (-0.25, -0.03, -0.075)); STAND_F = ((0.09, 0, -0.79), (-0.09, 0, -0.79))
def flail(t, k=1.0):
    s1, s2, s3 = math.sin(t * 7.1), math.sin(t * 6.3 + 1), math.sin(t * 5.2 + 2)
    hands = ((0.55, 0.05 + 0.12 * s1 * k, 0.32 + 0.18 * s2 * k), (-0.55, 0.05 - 0.12 * s2 * k, 0.32 + 0.18 * s1 * k))
    feet = ((0.17, 0.12 + 0.1 * s3 * k, -0.68 + 0.06 * s1 * k), (-0.17, 0.12 - 0.1 * s1 * k, -0.68 + 0.06 * s3 * k))
    return hands, feet
def limp(t):
    s = math.sin(t * 1.3)
    return ((0.42, 0.28 + 0.03 * s, 0.22), (-0.42, 0.30 - 0.03 * s, 0.20)), ((0.15, 0.30, -0.62), (-0.15, 0.32, -0.64))
def arch(t, k=1.0):
    """skydiver box position, written for a belly-down body (pitch +90)"""
    s = math.sin(t * 3.0) * 0.02
    hands = ((0.48, 0.10, 0.40 + s), (-0.48, 0.10, 0.40 - s))
    feet = ((0.2, 0.42 * k, -0.62), (-0.2, 0.42 * k, -0.62))
    return hands, feet
def spread(u):
    hands = ((lerp(0.48, 0.72, u), 0.05, lerp(0.40, 0.22, u)), (-lerp(0.48, 0.72, u), 0.05, lerp(0.40, 0.22, u)))
    feet = ((lerp(0.2, 0.36, u), lerp(0.42, 0.12, u), lerp(-0.62, -0.72, u)), (-lerp(0.2, 0.36, u), lerp(0.42, 0.12, u), lerp(-0.62, -0.72, u)))
    return hands, feet
def key_cam(f, cp, tp, lens, fstop=16.0):
    cam.location = cp; tgt.location = tp; cam.data.lens = lens; cam.data.dof.aperture_fstop = fstop
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f)
    cam.data.keyframe_insert('lens', frame=f); cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
def key_obj(o, f, loc, rot=None, scale=None):
    o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert('scale', frame=f)

# ---------------- props ----------------
AIR = G['AIRLINER']; FUS = D.objects['PF_fuselage']; SEATS = D.objects['PF_seats']
for o in (AIR, FUS, SEATS):
    if o and o.animation_data: o.animation_data_clear()
AIR_FWD = V(0, 1, 0)   # set after checking the model: +Y is the nose direction
HOME_Z = 10000.0
# night snowflakes field (falls with the fuselage shots)
import bmesh
fl_me = D.meshes.get('PF_flakes')
if fl_me is None:
    fl_me = D.meshes.new('PF_flakes'); bm = bmesh.new(); rr = random.Random(5)
    for i in range(3500):
        g_ = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rr.uniform(0.012, 0.03))
        bmesh.ops.translate(bm, verts=g_['verts'], vec=(rr.uniform(-25, 25), rr.uniform(-25, 25), rr.uniform(-260, 30)))
    bm.to_mesh(fl_me); bm.free(); fl_me.materials.append(G['pbsdf']('PF_Flake', (0.9, 0.95, 1.0), rough=0.6, emis=0.6))
FLAKES = D.objects.get('PF_flakes') or D.objects.new('PF_flakes', fl_me)
if FLAKES.name not in G['PROPS'].objects: G['PROPS'].objects.link(FLAKES)
# snow spray for the landing (metaball)
smb = D.metaballs.get('PF_spray') or D.metaballs.new('PF_spray'); smb.elements.clear(); smb.resolution = 0.03; smb.render_resolution = 0.015
if smb.animation_data: smb.animation_data_clear()
if not smb.materials: smb.materials.append(G['SNOWM'])
SPRAY = D.objects.get('PF_spray') or D.objects.new('PF_spray', smb)
if SPRAY.name not in G['SNOW'].objects: G['SNOW'].objects.link(SPRAY)
rs = random.Random(8); SPR = []
for i in range(170):
    a = rs.uniform(0, 2 * math.pi); sp = rs.uniform(0.8, 3.2)
    e = smb.elements.new(); e.radius = 0.001
    SPR.append(dict(e=e, v=V(math.cos(a) * sp, math.sin(a) * sp * 0.7, rs.uniform(1.0, 3.2)), r=rs.uniform(0.05, 0.12)))
def key_spray(f, w, base):
    SPRAY.location = base; SPRAY.keyframe_insert('location', frame=f)
    for d in SPR:
        e = d['e']
        if w <= 0: e.co = (0, 0, 0); e.radius = 0.001
        else:
            p = d['v'] * w + V(0, 0, -4.9 * w * w); p.z = max(p.z, -0.05)
            e.co = p; e.radius = max(0.001, d['r'] * min(1.0, w / 0.08) * (1 - cl((w - 0.45) / 0.55)))
        e.keyframe_insert('co', frame=f); e.keyframe_insert('radius', frame=f)

# ---------------- shots ----------------
SHOTS = []
def shot(name, t0, t1, sets, world, samples=32, rt=False, pct=100):
    def deco(fn): SHOTS.append(dict(name=name, t0=t0, t1=t1, fn=fn, sets=sets, world=world, samples=samples, rt=rt, pct=pct)); return fn
    return deco
SKY_SETS = ['PF_SKY', 'PF_PLANE', 'LIB_stickman_rig']
def hero_fall_pos(t, z0, vz=-55.0, drift=(0, 0)):
    return V(drift[0] * t, drift[1] * t, z0 + vz * t)

@shot('S01a_exit', 0.0, 1.55, SKY_SETS, 'W_SKY', 32)
def s01a(t, f):
    u = t / 1.55
    C = hero_fall_pos(t, HOME_Z - 6, vz=-18)
    R = Rm(pitch=0.6 + 1.8 * u, roll=0.4 * math.sin(t * 2), yaw=0.8 + 1.2 * u)
    h, ft = flail(t, 1.0); pose(f, C, R, h, ft, head=(0.2, 0, 0.1 * math.sin(t * 5))); eyes(f, 1, 1.15)
    ap = V(0, -12 + 22 * t, HOME_Z + 2) if AIR else None
    if AIR: key_obj(AIR, f, ap, (0, 0, 0))
    cp = C + V(2.6, -2.2, -1.3) + V(0.15 * math.sin(t * 9), 0, 0.1 * math.sin(t * 11))
    key_cam(f, cp, C + V(0, 0, 0.5) + (ap - C) * 0.04 if AIR else C, 24, 5.6)

@shot('S01b_scale', 1.55, 3.00, SKY_SETS, 'W_SKY', 32)
def s01b(t, f):
    tt = t; C = hero_fall_pos(tt, HOME_Z - 6, vz=-18)
    R = Rm(pitch=2.4 + 0.8 * (t - 1.55), roll=0.3, yaw=2.0 + 0.6 * (t - 1.55))
    h, ft = flail(t, 0.8); pose(f, C, R, h, ft); eyes(f, 1, 1.15)
    if AIR: key_obj(AIR, f, V(0, -12 + 22 * t, HOME_Z + 2), (0, 0, 0))
    u = eio((t - 1.55) / 1.45)
    cp = C + V(5.5, -8.5, -3.2).lerp(V(4.8, -7.5, -3.6), u)
    key_cam(f, cp, C + V(0, 3.5, 3.5), 28, 16)

@shot('S02_noparachute', 3.00, 4.24, SKY_SETS, 'W_SKY', 32)
def s02(t, f):
    C = V(0, 0, HOME_Z - 300)
    R = Rm(pitch=1.45, roll=0.1 * math.sin(t * 2), yaw=0.0)
    h, ft = arch(t, 0.8)
    pat = ramp(t, 3.25, 3.55) * (1 - ramp(t, 3.95, 4.2))
    hr = V(*h[1]).lerp(V(-0.12, 0.18 + 0.03 * math.sin(t * 30), 0.25), pat)
    pose(f, C, R, (h[0], tuple(hr)), ft, neck=(0, 0, 0), head=(-0.5, 0.0, 0.6 * ramp(t, 3.3, 3.7)))
    eyes(f, 1, 1.2)
    cp = C + R @ V(0.3, 1.9, 0.9); key_cam(f, cp, C + R @ V(0, 0.05, 0.25), 32, 4.0)

@shot('S03_cold', 4.24, 6.74, SKY_SETS, 'W_SKY', 32)
def s03(t, f):
    C = V(0, 0, HOME_Z - 500)
    R = Rm(pitch=1.0, roll=0.15 * math.sin(t), yaw=0.3)
    h, ft = flail(t * 0.5, 0.4); pose(f, C, R, h, ft, head=(-0.2, 0, 0.1 * math.sin(t * 1.5))); eyes(f, 1, 1.1)
    head = C + R @ V(0, -0.05, 0.75)
    u = eio((t - 4.24) / 2.5)
    key_cam(f, head + (R @ V(0.35, -1.0, 0.0)).lerp(R @ V(0.22, -0.72, 0.05), u), head, 50, 2.4)

@shot('S04_limp', 6.74, 10.40, SKY_SETS, 'W_SKY', 32)
def s04(t, f):
    C = V(0, 0, HOME_Z - 800)
    k = ramp(t, 7.9, 8.8)
    R = Rm(pitch=1.0 + 2.2 * k + 0.25 * (t - 6.74), roll=0.4 * k * math.sin(t * 0.9), yaw=0.3 + 0.5 * (t - 6.74))
    h1, f1 = flail(t * 0.5, 0.3); h2, f2 = limp(t)
    hands = tuple(tuple(lerp(a, b, k) for a, b in zip(p, q)) for p, q in zip(h1, h2)); feet = tuple(tuple(lerp(a, b, k) for a, b in zip(p, q)) for p, q in zip(f1, f2))
    pose(f, C, R, hands, feet, head=(lerp(-0.2, 0.55, k), 0, 0.25 * k), spine=(0.15 * k, 0, 0))
    eyes(f, 1 - ramp(t, 8.3, 8.9))
    a = 0.6 + 0.35 * (t - 6.74); cp = C + V(math.cos(a) * 3.4, math.sin(a) * 3.4, 0.8)
    key_cam(f, cp, C + V(0, 0, 0.2), 30, 5.6)

@shot('S05_clouds', 10.40, 14.34, SKY_SETS, 'W_SKY', 32)
def s05(t, f):
    C = V(0, 0, 3080 - 55 * (t - 10.40))
    wake = ramp(t, 13.05, 13.35)
    R = Rm(pitch=2.6 - 1.3 * wake + 0.2 * (t - 10.4), roll=0.3 * math.sin(t), yaw=0.4 * t)
    h1, f1 = limp(t); h2, f2 = flail(t, 1.3)
    hands = tuple(tuple(lerp(a, b, wake) for a, b in zip(p, q)) for p, q in zip(h1, h2)); feet = tuple(tuple(lerp(a, b, wake) for a, b in zip(p, q)) for p, q in zip(f1, f2))
    pose(f, C, R, hands, feet, head=(lerp(0.55, -0.1, wake), 0, 0))
    eyes(f, wake, lerp(1.0, 1.3, wake))
    cp = C + V(1.2, -2.0, 3.6) + V(0.1 * math.sin(t * 7), 0, 0)
    key_cam(f, cp, C, 26, 8)

@shot('S06_skydive', 14.34, 17.44, SKY_SETS, 'W_SKY', 32)
def s06(t, f):
    C = V(0, 0, 1500 - 55 * (t - 14.34))
    R = Rm(pitch=math.pi / 2, roll=0.06 * math.sin(t * 1.7), yaw=0.2 + 0.05 * math.sin(t))
    h, ft = arch(t); pose(f, C, R, h, ft, head=(-0.75, 0, 0.1 * math.sin(t * 1.3)), spine=(-0.25, 0, 0)); eyes(f, 1, 1.15)
    u = eio((t - 14.34) / 3.1)
    cp = C + V(lerp(2.6, 2.0, u), lerp(-2.4, -1.6, u), lerp(0.9, 1.4, u)) + V(0.04 * math.sin(t * 13), 0, 0.03 * math.sin(t * 17))
    key_cam(f, cp, C + V(0, 0, -0.6), 22, 16)

@shot('S07_pov', 17.44, 20.12, SKY_SETS, 'W_SKY', 32)
def s07(t, f):
    C = V(0, 0, 1330 - 55 * (t - 17.44))
    pose(f, V(0, 0, -5000), Rm(), STAND_H, STAND_F)
    a = 0.15 * math.sin(t * 0.9)
    key_cam(f, C, C + V(0.6 * math.sin(a) + 0.25, -0.35, -1.0) * 100, 20, 16)

@shot('S08_lake', 20.12, 23.58, ['PF_LAKE', 'LIB_stickman_rig'], 'W_SKY', 32, rt=True)
def s08(t, f):
    u = (t - 20.12) / 3.46
    C = V(8, -6, lerp(240, 28, u ** 0.9))
    R = Rm(pitch=math.pi / 2, roll=0.05 * math.sin(t * 2), yaw=0.3)
    h, ft = arch(t); pose(f, C, R, h, ft, head=(-0.75, 0, 0)); eyes(f, 1, 1.3)
    key_cam(f, C + V(0.9, 1.6, 3.4), C + V(0, -0.6, -6), 24, 16)

@shot('S09a_trees', 23.58, 24.95, ['PF_SNOW'], 'W_SKY', 16)
def s09a(t, f):
    u = eio((t - 23.58) / 1.37)
    cp = V(-40, 40, G['slope_h'](-40, 40) + lerp(95, 55, u))
    key_cam(f, cp, cp + V(18, -10, -60), 24, 16)
    pose(f, V(0, 0, -5000), Rm(), STAND_H, STAND_F)

@shot('S09b_snowfield', 24.95, 26.10, ['PF_SNOW'], 'W_SKY', 32)
def s09b(t, f):
    u = (t - 24.95) / 1.15
    x = lerp(-14, -6, u); y = 2.0
    cp = V(x, y, G['slope_h'](x, y) + 0.45)
    key_cam(f, cp, V(x + 8, y - 1.5, G['slope_h'](x + 8, y - 1.5) + 0.2), 28, 4.0)

@shot('S09c_slope', 26.10, 27.52, ['PF_SNOW'], 'W_SKY', 16)
def s09c(t, f):
    u = eio((t - 26.10) / 1.42)
    cp = V(lerp(-10, 10, u), -70, G['slope_h'](0, -70) + 4)
    key_cam(f, cp, V(cp.x, 0, G['slope_h'](cp.x, 0) + 2), 30, 16)

@shot('S10a_spread', 27.52, 29.20, SKY_SETS, 'W_SKY', 32)
def s10a(t, f):
    C = V(0, 0, 1100 - 55 * (t - 27.52))
    R = Rm(pitch=math.pi / 2, roll=0.04 * math.sin(t * 2), yaw=0.0)
    k = ramp(t, 27.66, 28.3); h, ft = spread(k)
    pose(f, C, R, h, ft, head=(-0.6, 0, 0)); eyes(f, 1, 1.1)
    key_cam(f, C + V(0.4, -1.2, -4.2), C + V(0, 0, 0.2), 20, 16)

LAND = V(0, 0, 0); LAND.z = G['slope_h'](0, 0)
T_LAND = 29.90
@shot('S10b_landing', 29.20, 31.24, ['PF_SNOW', 'LIB_stickman_rig'], 'W_SKY', 32)
def s10b(t, f):
    gz = G['slope_h']
    if t < T_LAND:
        w = T_LAND - t
        C = LAND + V(-9 * w, 0, 0.84 + 11 * w)
        R = Rm(pitch=-0.15, yaw=-math.pi / 2)
        hands = ((0.4, 0.0, 0.25), (-0.4, 0.0, 0.25)); feet = ((0.12, -0.08, -0.8), (-0.12, -0.08, -0.8))
        pose(f, C, R, hands, feet, head=(0.15, 0, 0)); eyes(f, 1, 1.3)
    else:
        w = t - T_LAND
        slide = 1.8 * (1 - math.exp(-w * 3))
        x = slide; base = V(x, 0, gz(x, 0))
        sq = math.exp(-w * 4) * math.sin(w * 18) * 0.05
        sit = ramp(t, 30.25, 30.6)
        hipz = lerp(0.45 - sq, 0.28, sit)
        C = base + V(0, 0, hipz - 0.25)   # buried a little in the snow
        R = Rm(pitch=lerp(0.25, -0.15, sit), yaw=-math.pi / 2)
        thumbs = ramp(t, 30.75, 30.95)
        hands = ((0.35, -0.2, lerp(0.1, 0.0, sit)), (-0.3, -0.25 - 0.15 * thumbs, lerp(0.1, 0.45, thumbs)))
        feet = ((0.12, -0.35, -0.4), (-0.12, -0.38, -0.4))
        pose(f, C, R, hands, feet, head=(-0.1 * thumbs, 0, 0.3 * thumbs), spine=(0.25 * (1 - sit), 0, 0)); eyes(f, 1, lerp(1.3, 1.0, thumbs))
    key_spray(f, t - T_LAND, LAND + V(0, 0, -0.1))
    u = eio((t - 29.20) / 2.04)
    cp = LAND + V(lerp(2.0, 2.8, u), lerp(-5.2, -4.4, u), 1.2)
    key_cam(f, cp, LAND + V(lerp(-1.0, 1.0, u), 0, lerp(2.2, 0.6, ramp(t, 29.5, 30.1))), 32, 5.6)

FUS_SPOT = V(14, -30, 0); FUS_SPOT.z = G['slope_h'](14, -30)
@shot('S12a_fuselage', 32.44, 35.20, ['PF_PROPS'], 'W_NIGHT', 32)
def s12a(t, f):
    u = t - 32.44
    C = V(0, 0, 400 - 30 * u)
    key_obj(FUS, f, C, (0.3 + 0.35 * u, 0.2 * u, 0.5 + 0.15 * u))
    key_obj(SEATS, f, V(0, 0, -9000)); key_obj(FLAKES, f, V(0, 0, 360 - 30 * u * 0.2))
    key_cam(f, C + V(7.5, -9.5, 2.5), C, 26, 8)
    pose(f, V(0, 0, -5000), Rm(), STAND_H, STAND_F)

@shot('S12b_fuselage_wide', 35.20, 38.46, ['PF_PROPS', 'PF_SKY'], 'W_NIGHT', 16)
def s12b(t, f):
    u = t - 35.20
    C = V(0, 0, 5200 - 60 * u)
    key_obj(FUS, f, C, (1.2 + 0.35 * u, 0.6 + 0.2 * u, 0.9 + 0.15 * u))
    key_obj(FLAKES, f, C + V(0, 0, 40 - 30 * u * 0.2))
    key_cam(f, C + V(30, -40, 18 + 3 * u), C + V(0, 0, -4), 40, 16)

@shot('S13_wreck', 38.46, 42.04, ['PF_SNOW', 'PF_PROPS'], 'W_DUSK', 32)
def s13(t, f):
    key_obj(FUS, f, FUS_SPOT + V(0, 0, 0.6), (0.18, -0.12, 0.6))
    key_obj(FLAKES, f, V(0, 0, -9000)); key_obj(SEATS, f, V(0, 0, -9000))
    u = eio((t - 38.46) / 3.58)
    cp = FUS_SPOT + V(lerp(16, 11, u), lerp(-9, -6, u), lerp(3.0, 2.2, u))
    key_cam(f, cp, FUS_SPOT + V(0, 0, 1.2), 30, 8)

SEAT_SPOT = G['SEAT_SPOT']
@shot('S14_seats_fall', 42.04, 46.26, ['PF_JUNGLE', 'PF_PROPS'], 'W_JUNGLE', 16)
def s14(t, f):
    u = (t - 42.04) / 4.22
    C = SEAT_SPOT + V(0, 0, lerp(75, 26, u))
    key_obj(SEATS, f, C, (0.6 + 2.2 * u, 0.4 * u, 1.0 + 3.0 * u))
    key_obj(FUS, f, V(0, 0, -9000)); key_obj(FLAKES, f, V(0, 0, -9000))
    key_cam(f, C + V(4.0, -5.0, 6.5), C + V(0, 0, -6), 24, 16)

@shot('S15_jungle_floor', 46.26, 50.00, ['PF_JUNGLE', 'PF_PROPS'], 'W_JUNGLE', 32)
def s15(t, f):
    gz = 1.2 * G['nz'](SEAT_SPOT.x, SEAT_SPOT.y, 6)
    key_obj(SEATS, f, SEAT_SPOT + V(0, 0, gz + 0.05), (0.15, -1.2, 0.4))
    u = eio((t - 46.26) / 3.74)
    cp = SEAT_SPOT + V(lerp(-2.5, 4.5, u), lerp(-3.4, -2.9, u), gz + lerp(1.3, 0.9, u))
    key_cam(f, cp, SEAT_SPOT + V(lerp(0.5, 8.0, u), 0, gz + 0.3), 26, 5.6)

@shot('S16_end', 50.00, 51.96, SKY_SETS, 'W_SKY', 32)
def s16(t, f):
    C = V(0, 0, 6000 - 55 * (t - 50.0))
    R = Rm(pitch=math.pi / 2 - 0.5, roll=0.05 * math.sin(t), yaw=0.0)
    h, ft = arch(t); pose(f, C, R, h, ft, head=(-0.95, 0, 0.0)); eyes(f, 1, 1.0)
    if AIR: key_obj(AIR, f, V(0, -400, HOME_Z + 2))
    u = eio((t - 50.0) / 1.96)
    key_cam(f, C + V(0.2, lerp(-2.6, -2.0, u), lerp(0.4, 0.6, u)), C + V(0, 0, 0.35), 32, 4.0)

def build(names=None):
    for s in SHOTS:
        if names and s['name'] not in names: continue
        for fr in range(F(s['t0']), F(s['t1'])):
            s['fn']((fr - 1) / FPS, fr)
    n = 0
    for idb in list(D.objects) + list(D.metaballs) + list(D.cameras):
        ad = idb.animation_data
        if not ad or not ad.action: continue
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'; n += 1
    sc.frame_start, sc.frame_end = 1, F(51.96)
    sc['pf_jobs'] = json.dumps([dict(name=s['name'], a=F(s['t0']), b=F(s['t1']) - 1, sets=s['sets'], world=s['world'], samples=s['samples'], rt=s['rt'], pct=s['pct']) for s in SHOTS])
    print('constant keys', n)
    return [(s['name'], F(s['t0']), F(s['t1']) - 1, s['sets'], s['world'], s['samples'], s['rt'], s['pct']) for s in SHOTS]
def _fcurves(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for lay in act.layers:
            for strip in lay.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out
