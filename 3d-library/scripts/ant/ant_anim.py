"""Ant-size Short: every 3D shot keyed on one global timeline (frame = round(t*30)+1), constant interpolation.
The hero stays 1.75 m; the sets in ant_set are 500x bigger."""
import bpy, math, json, random
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene; D = bpy.data
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
G = {'__name__': 'antset'}
exec(open(TEX + r"\ant_set_v6.py", encoding='utf-8').read(), G)
V = G['V']; FPS = 30
def F(t): return int(round(t * FPS)) + 1
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = cl(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def ramp(t, a, b): return ss((t - a) / (b - a)) if b != a else (1.0 if t >= a else 0.0)
def eio(u): u = cl(u); return 0.5 - 0.5 * math.cos(math.pi * u)
END = 46.02
HERO = D.objects['StickRig']; P = HERO.pose.bones
cam = D.objects['Cam']; tgt = D.objects['CamTgt']; sc.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.sensor_fit = 'AUTO'; cam.data.sensor_width = 36
HERO.location = (0, 0, 0); HERO.rotation_euler = (0, 0, 0)
for pb in P: pb.rotation_mode = 'QUATERNION' if pb.name in ('hips', 'IK_foot.L', 'IK_foot.R') else 'XYZ'
EYES = [D.objects['Eye.L'], D.objects['Eye.R']]; EYE0 = [(0.03, 0.02, 0.052)] * 2
for o in [HERO, cam, tgt, cam.data] + EYES:
    if o.animation_data: o.animation_data_clear()
for e in EYES: e.scale = (0.03, 0.02, 0.052)

# ---------------- posing ----------------
def Rm(pitch=0.0, roll=0.0, yaw=0.0):
    return Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(pitch, 3, 'X') @ Matrix.Rotation(roll, 3, 'Y')
def setR(pb, pos, R): pb.matrix = Matrix.Translation(V(*pos)) @ (R @ pb.bone.matrix_local.to_3x3()).to_4x4()
def setT(pb, pos): pb.matrix = Matrix.Translation(V(*pos)) @ pb.bone.matrix_local.to_3x3().to_4x4()
def pose_w(f, C, R, hands, feet, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), foot_R=None):
    """hands/feet in WORLD coords; poles placed in the body frame (knees forward, elbows back/out)."""
    C = V(*C); W = lambda p: C + R @ V(*p)
    setR(P['hips'], C, R)
    for i, S in enumerate('LR'):
        sg = 1 if S == 'L' else -1
        fp = V(*feet[i]); setR(P['IK_foot.' + S], fp, foot_R or R)
        loc = R.transposed() @ (fp - C)
        setT(P['pole_knee.' + S], W((loc.x * 0.9 + sg * 0.03, -0.6, loc.z * 0.5)))
        setT(P['pole_elbow.' + S], W((sg * 0.55, 0.45, 0.05)))
        setT(P['IK_hand.' + S], V(*hands[i]))
    P['spine'].rotation_euler = spine; P['neck'].rotation_euler = neck; P['head'].rotation_euler = head
    for n in ('hips', 'IK_foot.L', 'IK_foot.R'):
        P[n].keyframe_insert('location', frame=f); P[n].keyframe_insert('rotation_quaternion', frame=f)
    for n in ('pole_knee.L', 'pole_knee.R', 'pole_elbow.L', 'pole_elbow.R', 'IK_hand.L', 'IK_hand.R'): P[n].keyframe_insert('location', frame=f)
    for n in ('spine', 'neck', 'head'): P[n].keyframe_insert('rotation_euler', frame=f)
def frame_vecs(h):
    return V(math.cos(h), math.sin(h), 0), V(-math.sin(h), math.cos(h), 0)   # forward, his left
def L_(C, R, p): return V(*C) + R @ V(*p)
def stand(f, base, h, hands=None, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), hipdz=0.0, lean=0.0, sway=0.0):
    b = V(*base); fw, lf = frame_vecs(h); R = Rm(pitch=lean, roll=sway, yaw=h + math.pi / 2)
    C = b + V(0, 0, 0.845 + hipdz)
    feet = (b + lf * 0.09 + V(0, 0, 0.055), b - lf * 0.09 + V(0, 0, 0.055))
    if hands is None: hands = (C + lf * 0.25 + fw * 0.03 + V(0, 0, -0.075), C - lf * 0.25 + fw * 0.03 + V(0, 0, -0.075))
    pose_w(f, C, R, hands, feet, spine, neck, head, foot_R=Rm(yaw=h + math.pi / 2)); return C
def walk(f, base, h, ph, stride=0.6, lean=0.07, arms=1.0, bz=0.0, head=(0, 0, 0), neck=(0, 0, 0), hands=None):
    c = math.cos(2 * math.pi * ph); s_ = math.sin(2 * math.pi * ph)
    b = V(*base); fw, lf = frame_vecs(h)
    feet = (b + fw * (0.5 * stride * c) + lf * 0.085 + V(0, 0, 0.055 + 0.10 * max(0.0, -s_)),
            b - fw * (0.5 * stride * c) - lf * 0.085 + V(0, 0, 0.055 + 0.10 * max(0.0, s_)))
    C = b + V(0, 0, 0.80 + 0.03 * abs(s_) + bz)
    if hands is None:
        hands = (C + fw * (0.04 - 0.17 * c * arms) + lf * 0.24 + V(0, 0, -0.08), C + fw * (0.04 + 0.17 * c * arms) - lf * 0.24 + V(0, 0, -0.08))
    yaw = 0.08 * c
    pose_w(f, C, Rm(pitch=lean, yaw=h + yaw + math.pi / 2), hands, feet, spine=(0, -yaw * 1.5, 0), neck=neck, head=head, foot_R=Rm(yaw=h + math.pi / 2))
    return C
def sit(f, base, h, lean=-0.3, feet_fwd=0.75, hands_back=True, head=(0, 0, 0), neck=(0, 0, 0), knees_up=0.0, feet=None, hands=None, roll=0.0, hz=0.2):
    b = V(*base); fw, lf = frame_vecs(h); R = Rm(pitch=lean, roll=roll, yaw=h + math.pi / 2)
    C = b + V(0, 0, hz)
    if feet is None:
        ff = feet_fwd * (1 - 0.45 * knees_up)
        feet = (b + fw * ff + lf * 0.13 + V(0, 0, 0.05), b + fw * ff - lf * 0.13 + V(0, 0, 0.05))
    if hands is None:
        if hands_back: hands = (b - fw * 0.28 + lf * 0.3 + V(0, 0, 0.03), b - fw * 0.28 - lf * 0.3 + V(0, 0, 0.03))
        else: hands = (C + fw * 0.45 + lf * 0.12 + V(0, 0, 0.18), C + fw * 0.45 - lf * 0.12 + V(0, 0, 0.18))
    pose_w(f, C, R, hands, feet, spine=(0.1 * knees_up, 0, 0), neck=neck, head=head, foot_R=Rm(pitch=-0.6 * (1 - knees_up), yaw=h + math.pi / 2))
    return C
def eyes(f, open_=1.0, wide=1.0):
    for e, s0 in zip(EYES, EYE0):
        e.scale = (s0[0] * wide, s0[1] * wide, s0[2] * max(0.1, open_) * wide); e.keyframe_insert('scale', frame=f)
def blink(t, period=3.3, off=0.0):
    x = (t + off) % period
    return 0.1 if x < 0.12 else 1.0
def key_cam(f, cp, tp, lens, fstop=16.0):
    cam.location = cp; tgt.location = tp; cam.data.lens = lens; cam.data.dof.aperture_fstop = fstop
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f)
    cam.data.keyframe_insert('lens', frame=f); cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
def hide(o, f):
    o.scale = (0.001,) * 3; o.keyframe_insert('scale', frame=f)
def flail(t, k=1.0):
    s1, s2, s3 = math.sin(t * 7.1), math.sin(t * 6.3 + 1), math.sin(t * 5.2 + 2)
    hands = ((0.55, 0.05 + 0.12 * s1 * k, 0.32 + 0.18 * s2 * k), (-0.55, 0.05 - 0.12 * s2 * k, 0.32 + 0.18 * s1 * k))
    feet = ((0.17, 0.12 + 0.1 * s3 * k, -0.68 + 0.06 * s1 * k), (-0.17, 0.12 - 0.1 * s1 * k, -0.68 + 0.06 * s3 * k))
    return hands, feet
def pose_local(f, C, R, hands, feet, **kw):
    pose_w(f, C, R, [L_(C, R, h) for h in hands], [L_(C, R, p) for p in feet], **kw)

# ---------------- props ----------------
Z_T = G['Z_T']; CUP = G['CUP']; DRIP_TOP = G['DRIP_TOP']; DROP_LAND = G['DROP_LAND']
HERO1 = G['HERO1']; EDGE = G['EDGE']; LAND = G['LAND']; RAIN0 = G['RAIN0']; LAB0 = G['LAB0']; GR0 = G['GR0']
H1 = math.atan2(DROP_LAND.y - HERO1.y, DROP_LAND.x - HERO1.x)            # hero faces the landing spot / cup
DROP = G['DROP']; DE = G['DROP_E']; SPL = G['SPL']; POOL = G['SPL_POOL']; SPLASH = G['SPLASH']
for o in (DROP, SPLASH):
    if o.animation_data: o.animation_data_clear()
T_IMP = 2.9                     # coffee drop hits the table
D_TOP = Z_T + 60.5; D_A = 0.0714; D_S = 26.06    # slow-mo fall law: z = D_TOP - D_A * (t - t_rel)^2
def drop_z(t, t_rel): return D_TOP - D_A * max(0.0, t - t_rel) ** 2
def key_drop(f, t):
    DROP.location = (0, 0, 0); DROP.keyframe_insert('location', frame=f)
    x, y = DRIP_TOP.x, DRIP_TOP.y
    if t < T_IMP: z = drop_z(t, -D_S)
    elif t > 41.0: z = drop_z(t, END - D_S)
    else: z = None
    if z is None: st = [((x, y, -100), 0.001)] * 3
    else: st = [((x, y, z), 2.1), ((x, y, z + 0.9), 1.5), ((x, y, z + 1.5), 0.9)]
    for e, (p, r) in zip(DE, st):
        e.co = p; e.radius = max(0.001, r); e.keyframe_insert('co', frame=f); e.keyframe_insert('radius', frame=f)
CROWN = G['CROWN']
if CROWN.animation_data: CROWN.animation_data_clear()
def key_splash(f, t):
    """mesh crown rising and flaring, rim droplets flung out (metaballs), then collapsing into a flat pool"""
    SPLASH.location = DROP_LAND; SPLASH.keyframe_insert('location', frame=f)
    w = t - T_IMP; on = 0 < w and t < 41.0
    hc = 3.6 * math.sin(math.pi * cl(w / 1.3)) ** 0.7 if on else 0.0
    rA = 1.3 + 2.8 * (1 - math.exp(-3.0 * max(w, 0)))
    settle = ramp(w, 0.95, 1.6)
    if on and hc > 0.05 and settle < 0.999:
        CROWN.location = DROP_LAND; CROWN.scale = (rA, rA, max(0.05, hc * (1 - settle)))
    else:
        CROWN.location = DROP_LAND + V(0, 0, -50); CROWN.scale = (0.001,) * 3
    CROWN.keyframe_insert('location', frame=f); CROWN.keyframe_insert('scale', frame=f)
    for d in SPL:
        e = d['e']; a = d['a']
        if not on or w < 0.3: e.co = (0, 0, -50); e.radius = 0.001
        else:
            ww = (w - 0.3) * d['v']
            r = rA * 1.26 + 2.4 * ww; h = 3.6 + 2.8 * ww - 5.0 * ww * ww
            e.co = (math.cos(a) * r, math.sin(a) * r, max(0.3, h)); e.radius = 0.5 * (1 - settle)
        e.keyframe_insert('co', frame=f); e.keyframe_insert('radius', frame=f)
    POOL.type = 'ELLIPSOID'; POOL.size_x = POOL.size_y = 1.0; POOL.size_z = 0.1
    if not on: POOL.co = (0, 0, -50); POOL.radius = 0.001
    else: POOL.co = (0, 0, 0.05); POOL.radius = lerp(3.0, 7.0, ramp(w, 0.0, 1.6))
    POOL.keyframe_insert('co', frame=f); POOL.keyframe_insert('radius', frame=f)
# climbing crumb for the loop shot
import bmesh
_me = D.meshes.new('ANT_ClimbCrumb'); _bm = bmesh.new()
G['rock'](_bm, V(0, 0, 0), V(2.4, 1.8, 1.25), 77, 1.0); _bm.to_mesh(_me); _bm.free(); G['smooth'](_me)
CRUMB_O = G['obj']('ANT_ClimbCrumb', _me, G['CAFE']); _me.materials.append(D.materials['ANT_Crumb'])
_away = (V(HERO1.x, HERO1.y, 0) - V(DROP_LAND.x, DROP_LAND.y, 0)).normalized()
CRUMB_P = HERO1 + _away * 1.8 + V(-_away.y, _away.x, 0) * 3.6
_cdir = (CRUMB_P - HERO1).normalized()
CRUMB_O.location = CRUMB_P + V(0, 0, -0.15); CRUMB_O.rotation_euler = (0, 0, math.atan2(_away.y, _away.x) + math.pi / 2)
def crumb_h(p):
    d = V(p.x - CRUMB_P.x, p.y - CRUMB_P.y, 0)
    loc = Matrix.Rotation(-CRUMB_O.rotation_euler.z, 3, 'Z') @ d
    q = (loc.x / 2.2) ** 2 + (loc.y / 1.7) ** 2
    return max(0.0, 1.05 * (1 - q)) if q < 1 else 0.0
# rain
RD = G['RAINDROPS']; SPLATS = G['SPLATS']; BLOB = G['BLOB']; BE = G['BLOB_E']; GL = G['GIANT']
for o in [d['o'] for d in RD] + SPLATS + [BLOB] + GL:
    if o.animation_data: o.animation_data_clear()
if BLOB.data.animation_data: BLOB.data.animation_data_clear()
BLOBM = D.materials['ANT_Water'].copy(); BLOBM.name = 'ANT_WaterBlob'; BLOB.data.materials.clear(); BLOB.data.materials.append(BLOBM)
BGLOW = next(n for n in BLOBM.node_tree.nodes if n.type == 'MATH')
if BLOBM.node_tree.animation_data: BLOBM.node_tree.animation_data_clear()
RAIN_START = 14.85; RP = 2.0
def key_rain(f, t):
    for k, d in enumerate(RD):
        o = d['o']; sp = SPLATS[k]
        ph = k * RP / len(RD); n = math.floor((t - RAIN_START - ph) / RP)
        best = None
        for nn in (n, n + 1):
            if nn < 0: continue
            tl = RAIN_START + ph + nn * RP
            rr = random.Random(k * 1000 + nn)
            a = rr.uniform(0, 2 * math.pi); dist = rr.uniform(10, 95)
            p = RAIN0 + V(math.cos(a) * dist, math.sin(a) * dist, 0)
            if best is None or tl > t: best = (tl, p) if tl > t else best
            if tl <= t: last = (tl, p)
        # falling drop: the next landing ahead
        if best and best[0] > t and best[0] - t < 2.4:
            tl, p = best; z = d['r'] + 70.0 * (tl - t)
            o.location = (p.x, p.y, z); s = d['r']; o.scale = (s * 0.92, s * 0.92, s * 1.05)
        else:
            o.location = (0, 0, -100); o.scale = (0.001,) * 3
        o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
        # splat from the most recent landing
        lastl = None
        if n >= 0:
            tl = RAIN_START + ph + n * RP; rr = random.Random(k * 1000 + n)
            a = rr.uniform(0, 2 * math.pi); dist = rr.uniform(10, 95); lastl = (tl, RAIN0 + V(math.cos(a) * dist, math.sin(a) * dist, 0))
        if lastl and 0 <= t - lastl[0] < 0.45:
            w = (t - lastl[0]) / 0.45; s = d['r']
            sp.location = lastl[1] + V(0, 0, 0.05); sp.scale = (s * lerp(1.0, 2.6, w ** 0.5), s * lerp(1.0, 2.6, w ** 0.5), s * lerp(0.6, 0.06, w))
        else:
            sp.location = (0, 0, -100); sp.scale = (0.001,) * 3
        sp.keyframe_insert('location', frame=f); sp.keyframe_insert('scale', frame=f)
# giant passer-by steps: (foot, t_down, t_up, position)
GDIR = (V(RAIN0.x, RAIN0.y, 0) - V(LAND.x, LAND.y, 0)).normalized(); GSIDE = V(-GDIR.y, GDIR.x, 0)
GSTEPS = [('L', 15.30, 16.10, RAIN0 + GSIDE * 62 - GDIR * 120), ('R', 15.95, 16.9, RAIN0 + GSIDE * 92 + GDIR * 140),
          ('L', 28.95, 29.85, RAIN0 + GSIDE * 48 - GDIR * 60), ('R', 29.6, 30.6, RAIN0 + GSIDE * 80 + GDIR * 190),
          ('L', 30.35, 31.35, RAIN0 + GSIDE * 52 + GDIR * 440), ('R', 31.1, 32.2, RAIN0 + GSIDE * 86 + GDIR * 700),
          ('L', 31.85, 32.9, RAIN0 + GSIDE * 50 + GDIR * 960), ('R', 32.6, 33.7, RAIN0 + GSIDE * 82 + GDIR * 1220),
          ('L', 33.35, 34.4, RAIN0 + GSIDE * 48 + GDIR * 1480), ('R', 34.1, 35.3, RAIN0 + GSIDE * 80 + GDIR * 1740)]
def key_giant(f, t):
    for o, S in zip(GL, 'LR'):
        steps = [s for s in GSTEPS if s[0] == S]
        pos = V(0, 0, -3000); tilt = 0.0
        for i, (_, td, tu, p) in enumerate(steps):
            if td - 0.45 <= t <= tu + 0.45:
                if t < td:
                    u = (td - t) / 0.45; pos = p - GDIR * 120 * u + V(0, 0, 160 * u * u); tilt = -0.25 * u
                elif t <= tu: pos = p; tilt = 0.0
                else:
                    u = (t - tu) / 0.45; pos = p + GDIR * 140 * u + V(0, 0, 200 * u * u); tilt = 0.3 * u
                break
        o.location = pos; o.rotation_euler = (GSIDE.x * tilt, GSIDE.y * tilt, 0)
        o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_euler', frame=f)
# sticky blob: the drop that hits him, then a dome holding his left foot
T_HIT = 16.75
def key_blob(f, t, foot=None, pull=0.0):
    BLOB.location = (0, 0, 0); BLOB.keyframe_insert('location', frame=f)
    BGLOW.inputs[1].default_value = 1.6 * ramp(t, 18.0, 18.6) * (1 - ramp(t, 22.0, 22.3)); BGLOW.inputs[1].keyframe_insert('default_value', frame=f)
    hitp = RAIN0 + V(0.25, 0.1, 0)
    if t < 14.3 or t > 28.6: st = [((0, 0, -100), 0.001)] * 6
    elif t < T_HIT:
        z = 1.0 + 70.0 * (T_HIT - t); st = [((hitp.x, hitp.y, z), 1.5)] + [((0, 0, -100), 0.001)] * 5
    else:
        w = t - T_HIT; g = ramp(w, 0.0, 0.35)
        c = foot if foot is not None else hitp
        base = V(c.x, c.y, 0)
        st = [((base.x, base.y, lerp(1.0, 0.22, g)), lerp(1.5, 1.05, g))]
        for i in range(4):
            a = i * math.pi / 2 + 0.4
            st.append(((base.x + math.cos(a) * 0.55 * g, base.y + math.sin(a) * 0.55 * g, 0.12), 0.7 * g + 0.001))
        st.append(((base.x, base.y, 0.3 + 0.55 * pull), 0.6 * pull + 0.001))
    for e, (p, r) in zip(BE, st):
        e.co = p; e.radius = max(0.001, r); e.keyframe_insert('co', frame=f); e.keyframe_insert('radius', frame=f)
# lab rays
RAYS = G['RAYS']; PUPIL = G['PUPIL']
for o in RAYS:
    if o.animation_data: o.animation_data_clear()
def key_rays(f, t):
    pc = PUPIL.location.copy()
    for i, o in enumerate(RAYS):
        off = (i - 4) * 0.035
        g_in = ramp(t, 26.5 + 0.03 * i, 27.0 + 0.03 * i); g_out = ramp(t, 27.0 + 0.03 * i, 27.8 + 0.03 * i)
        if g_in <= 0: o.scale = (0.001,) * 3; o.location = pc
        elif g_out <= 0:   # incoming parallel ray along +X towards the pupil
            o.location = pc + V(-7.0, 0, off); o.rotation_euler = (0, math.pi / 2, 0); o.scale = (1, 1, 7.0 * g_in)
        else:              # fanned-out ray beyond the pupil (diffraction spread)
            ang = (i - 4) * 0.17
            d = V(math.cos(ang), 0, math.sin(ang))
            o.location = pc; o.rotation_euler = V(0, 0, 1).rotation_difference(d).to_euler(); o.scale = (1, 1, 9.0 * g_out + 0.001)
        o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_euler', frame=f); o.keyframe_insert('scale', frame=f)

# ---------------- shots ----------------
SHOTS = []
CAFE = ['ANT_CAFE', 'LIB_stickman_rig']; RAIN = ['ANT_CAFE', 'ANT_RAIN', 'LIB_stickman_rig']
def shot(name, t0, t1, sets, world, samples=32, rt=False, pct=100):
    def deco(fn): SHOTS.append(dict(name=name, t0=t0, t1=t1, fn=fn, sets=sets, world=world, samples=samples, rt=rt, pct=pct)); return fn
    return deco
fw1, lf1 = frame_vecs(H1)
CAM0 = HERO1 - fw1 * 4.4 - lf1 * 1.4 + V(0, 0, 0.5)              # frame-0 camera: low, behind-left of him, looking up
TGT0 = HERO1 + fw1 * 2.4 + V(0, 0, 4.6)
def hook_pose(f, t, look=1.0):
    head = (-0.35 * look, 0, 0.0); neck = (-0.3 * look, 0, 0)
    hands = None
    stand(f, HERO1, H1, neck=neck, head=head, lean=-0.05 * look)
    eyes(f, blink(t, 3.3, 1.0), 1.0 + 0.15 * look)

@shot('A01_hook', 0.0, 2.48, CAFE, 'W_CAFE')
def a01(t, f):
    key_drop(f, t); key_splash(f, t); key_rain(f, t); key_giant(f, t); key_blob(f, t)
    hook_pose(f, t)
    if t < 1.40:                      # 1a: low macro behind him, drop falling at him
        u = eio(t / 1.4); key_cam(f, CAM0 + fw1 * 0.6 * u, TGT0, 20, 5.6)
    else:                             # 1b: face close-up, eyes wide
        u = eio((t - 1.4) / 1.08); face = HERO1 + V(0, 0, 1.56)
        cp = face + fw1 * lerp(1.35, 1.05, u) + lf1 * 0.3 + V(0, 0, 0.12)
        key_cam(f, cp, face + V(0, 0, 0.08), 50, 2.0)

@shot('A02_splash', 2.48, 6.48, CAFE, 'W_CAFE')
def a02(t, f):
    key_drop(f, t); key_splash(f, t)
    w = t - T_IMP
    if w < 0.18: hook_pose(f, t)
    else:
        k = ramp(w, 0.18, 0.6)        # knocked back onto his bottom, sliding away from the splash
        away = -fw1
        base = HERO1 + away * (1.6 * k + 0.25 * ramp(w, 0.6, 1.2))
        if k < 1.0 and w < 0.6:
            C = (HERO1 + V(0, 0, 0.845)).lerp(base + V(0, 0, 0.2), k)
            R = Rm(pitch=lerp(-0.05, -0.55, k), yaw=H1 + math.pi / 2)
            hands = (C + lf1 * 0.4 + fw1 * 0.2 + V(0, 0, 0.35 * (1 - k)), C - lf1 * 0.4 + fw1 * 0.2 + V(0, 0, 0.35 * (1 - k)))
            feet = (HERO1 + lf1 * 0.1 + fw1 * 0.5 * k + V(0, 0, 0.055 + 0.3 * math.sin(math.pi * k)), HERO1 - lf1 * 0.1 + fw1 * 0.6 * k + V(0, 0, 0.055 + 0.25 * math.sin(math.pi * k)))
            pose_w(f, C, R, hands, feet, head=(-0.2, 0, 0))
        else:
            sit(f, base, H1, lean=lerp(-0.45, -0.25, ramp(w, 0.6, 1.4)), head=(lerp(-0.2, 0.05, ramp(w, 0.8, 1.6)), 0, 0.15 * math.sin(t * 2.0)))
        eyes(f, blink(t, 2.9), 1.3)
    if t < 4.6:                       # 2a: side macro, slow-mo impact
        u = eio((t - 2.48) / 2.12); side = lf1
        cp = DROP_LAND.lerp(HERO1, 0.6) + side * lerp(11.0, 10.0, u) - fw1 * 0.5 + V(0, 0, lerp(0.8, 1.0, u))
        key_cam(f, cp, DROP_LAND.lerp(HERO1, 0.6) + V(0, 0, lerp(2.4, 1.3, ramp(t, 2.6, 3.4))), 24, 3.5)
    else:                             # 2b plate: calm high three-quarter of him sitting by the coffee pool
        u = eio((t - 4.6) / 1.88)
        cp = HERO1 - fw1 * 6.5 + lf1 * 5.5 + V(0, 0, lerp(4.0, 4.6, u))
        key_cam(f, cp, HERO1.lerp(DROP_LAND, 0.4) + V(0, 0, 0.5), 28, 6.0)

HE = math.atan2(EDGE.y, EDGE.x)        # facing outwards over the edge
fwe, lfe = frame_vecs(HE)
T_JUMP = 8.12
def fall_C(t):
    u = cl((t - T_JUMP) / 4.13)
    hop = 1.3 * math.sin(math.pi * cl((t - T_JUMP) / 0.55))
    xy = V(EDGE.x, EDGE.y, 0).lerp(V(LAND.x, LAND.y, 0), 1 - (1 - u) ** 1.6)
    z = Z_T + 0.9 + hop - (Z_T + 0.9 - 0.95) * u ** 1.7
    return V(xy.x, xy.y, z)
@shot('A03_edge', 6.48, 8.56, CAFE, 'W_CAFE')
def a03(t, f):
    key_drop(f, t); key_splash(f, t)
    base = EDGE - fwe * 0.9
    if t < 7.55:                      # walks the last steps to the edge, peeks down
        u = ramp(t, 6.48, 7.2); b = (EDGE - fwe * 2.4).lerp(base, u)
        if u < 1: walk(f, b, HE, (t - 6.48) * 1.6, stride=0.45, head=(0.25, 0, 0))
        else: stand(f, base, HE, head=(0.45, 0, 0.1 * math.sin(t * 3)), neck=(0.2, 0, 0))
    elif t < T_JUMP:                  # crouch, arms back
        k = ramp(t, 7.55, 7.95)
        C = stand(f, base, HE, hipdz=-0.32 * k, lean=0.35 * k, head=(0.1, 0, 0),
                  hands=(base + V(0, 0, 0.845 - 0.32 * k) - fwe * 0.35 * k + lfe * 0.25 + V(0, 0, -0.1), base + V(0, 0, 0.845 - 0.32 * k) - fwe * 0.35 * k - lfe * 0.25 + V(0, 0, -0.1)))
    else:                             # leap out, arms up
        C = fall_C(t); R = Rm(pitch=0.25, yaw=HE + math.pi / 2)
        hands, feet = ((0.35, -0.15, 0.75), (-0.35, -0.15, 0.75)), ((0.15, 0.25, -0.65), (-0.15, 0.1, -0.75))
        pose_local(f, C, R, hands, feet, head=(0.2, 0, 0))
    eyes(f, blink(t, 3.1), 1.2)
    if t < 7.6:                       # 3a: behind and above him looking down the drop
        u = eio((t - 6.48) / 1.12)
        cp = EDGE - fwe * lerp(2.2, 1.6, u) + lfe * 0.5 + V(0, 0, lerp(3.0, 3.3, u))
        key_cam(f, cp, EDGE + fwe * 45 + V(0, 0, -Z_T), 22, 5.6)
    else:                             # 3b: side wide, he leaps off
        cp = EDGE + fwe * 7.5 + lfe * 4.0 + V(0, 0, 0.2)
        hc_ = fall_C(t) if t > T_JUMP else EDGE + V(0, 0, 0.7)
        key_cam(f, cp, hc_, 24, 4.0)

@shot('A04_fall', 8.56, 11.92, CAFE, 'W_CAFE')
def a04(t, f):
    C = fall_C(t); hands, feet = flail(t, 1.2)
    R = Rm(pitch=lerp(0.25, -0.2, ramp(t, 8.56, 9.4)), roll=0.15 * math.sin(t * 1.3), yaw=HE + math.pi / 2 + 0.35 * (t - 8.56))
    pose_local(f, C, R, hands, feet, head=(-0.15, 0, 0))
    eyes(f, 1.0, 1.35)
    u = eio((t - 8.56) / 3.36)       # camera falls with him, below-side, looking up past him at the table edge
    cp = C + lfe * lerp(4.5, 5.5, u) + fwe * lerp(2.0, 3.5, u) + V(0, 0, -lerp(2.2, 3.0, u))
    key_cam(f, cp, C + V(0, 0, 0.6), lerp(20, 24, u), 9.0)

@shot('A05_land', 11.92, 14.28, CAFE, 'W_CAFE')
def a05(t, f):
    T_L = 12.25
    if t < T_L:
        C = fall_C(t); hands, feet = flail(t, 0.6)
        pose_local(f, C, Rm(pitch=-0.05, yaw=HE + math.pi / 2), hands, feet, head=(0.1, 0, 0))
    elif t < 13.05:                   # lands softly, knees bend, stands, dusts off
        k = math.exp(-5 * (t - T_L)) * math.cos(9 * (t - T_L))
        dust = ramp(t, 12.55, 12.75) * (1 - ramp(t, 12.95, 13.05))
        hd = math.sin(t * 22) * 0.06 * dust
        stand(f, LAND, HE, hipdz=-0.3 * max(0, k), lean=0.2 * max(0, k),
              hands=None if dust < 0.05 else (LAND + V(0, 0, 0.75) + fwe * 0.15 + lfe * (0.18 + hd) , LAND + V(0, 0, 0.55) + fwe * 0.1 - lfe * (0.2 - hd)),
              head=(0.15 * dust, 0, 0))
    else:                             # shrug, then walks away towards the rain spot
        hw = math.atan2(RAIN0.y - LAND.y, RAIN0.x - LAND.x)
        u = (t - 13.05); b = LAND + V(math.cos(hw), math.sin(hw), 0) * (u * 1.25 * ramp(t, 13.2, 13.5))
        h = lerp(HE, hw, ramp(t, 13.05, 13.4))
        walk(f, b, h, u * 2.0 * ramp(t, 13.15, 13.4), stride=0.55 * ramp(t, 13.15, 13.4))
    eyes(f, blink(t, 3.0, 0.4), 1.0)
    if t < 13.0:                      # 5a: ground level, looking along the pavement at the landing
        cp = LAND - fwe * 3.2 + lfe * 4.2 + V(0, 0, 0.25)
        key_cam(f, cp, LAND + V(0, 0, lerp(3.5, 0.8, ramp(t, 11.92, 12.3))), 24, 2.2)
    else:                             # 5b: low tracking beside him, pebbles passing
        hw = math.atan2(RAIN0.y - LAND.y, RAIN0.x - LAND.x); fw_, lf_ = frame_vecs(hw)
        b = LAND + fw_ * ((t - 13.05) * 1.25)
        key_cam(f, b + lf_ * 3.0 + fw_ * 1.8 + V(0, 0, 0.35), b + V(0, 0, 0.8), 26, 2.0)

HR = math.atan2(LAND.y - RAIN0.y, LAND.x - RAIN0.x) + 2.2    # hero heading in the rain scenes
fwr, lfr = frame_vecs(HR)
@shot('A06_rain', 14.28, 21.96, RAIN, 'W_RAIN')
def a06(t, f):
    key_rain(f, t); key_giant(f, t)
    foot = None; pull = 0.0
    if t < T_HIT - 0.05:              # stands looking up at the first drops
        look = ramp(t, 14.5, 15.0)
        stand(f, RAIN0, HR, neck=(-0.3 * look, 0, 0), head=(-0.35 * look, 0, 0.2 * math.sin(t * 1.5) * look))
        eyes(f, blink(t, 3.2), 1.0 + 0.3 * look)
    elif t < 17.9:                    # knocked flat on his back
        k = ramp(t, T_HIT - 0.05, T_HIT + 0.2)
        C = (RAIN0 + V(0, 0, 0.845)).lerp(RAIN0 - fwr * 0.7 + V(0, 0, 0.14), k)
        R = Rm(pitch=lerp(0.0, -1.5, k), yaw=HR + math.pi / 2)
        hands = (C + lfr * 0.6 + V(0, 0, 0.0), C - lfr * 0.6 + V(0, 0, 0.0))
        feet = (RAIN0 + lfr * 0.12 + fwr * 0.15 * k + V(0, 0, 0.06), RAIN0 - lfr * 0.12 + fwr * 0.1 * k + V(0, 0, 0.06))
        pose_w(f, C, R, hands, feet, head=(0.3 * k, 0, 0))
        foot = RAIN0 + lfr * 0.12 + fwr * 0.15
        eyes(f, 1.0 if t < T_HIT + 0.3 else blink(t, 1.4), 1.0)
    else:                             # sits up, pulls the stuck left leg, it won't come free
        foot = RAIN0 + lfr * 0.12 + fwr * 0.15
        cyc = (t - 17.9) % 1.25; pull = math.sin(math.pi * cl(cyc / 0.9)) ** 2 if t < 21.0 else 0.6 + 0.3 * math.sin(t * 9)
        base = RAIN0 - fwr * (0.62 + 0.18 * pull)
        sit(f, base, HR, lean=lerp(-0.5, -0.15, ramp(t, 17.9, 18.4)) - 0.25 * pull, hands_back=False,
            feet=(foot + V(0, 0, 0.05 + 0.25 * pull), base + fwr * 0.45 - lfr * 0.15 + V(0, 0, 0.05)),
            hands=(foot.lerp(base, 0.35) + V(0, 0, 0.35 + 0.1 * pull), foot.lerp(base, 0.4) + V(0, 0, 0.32 + 0.1 * pull) - lfr * 0.12),
            head=(0.2 - 0.25 * pull, 0, 0.12 * math.sin(t * 11) * pull), knees_up=0.4)
        eyes(f, blink(t, 2.6), 1.0 + 0.3 * pull)
    key_blob(f, t, foot, pull * 0.6 if t >= 17.9 else 0.0)
    if t < 15.2:                      # 6a: ground-level wide looking up, first drops falling
        u = eio((t - 14.28) / 0.92)
        cp = RAIN0 + fwr * 5.0 - lfr * 3.0 + V(0, 0, 0.3)
        key_cam(f, cp, RAIN0 + V(0, 0, lerp(8, 18, u)) - fwr * 4, 16, 9.0)
    elif t < 16.03:                   # 6b: low behind him, giant foot slams down
        cp = RAIN0 - fwr * 4.5 + lfr * 2.5 + V(0, 0, 0.5)
        key_cam(f, cp, RAIN0 + (GSTEPS[0][3] - RAIN0) * 0.5 + V(0, 0, 18), 18, 11.0)
    elif t < 17.9:                    # 7a: top-down, the drop hits and flattens him
        u = eio((t - 16.03) / 1.87)
        cp = RAIN0 + V(0, 0, lerp(6.0, 4.6, u)) + fwr * 0.8 + lfr * 0.6
        key_cam(f, cp, RAIN0 - fwr * 0.3, 26, 6.0)
    elif t < 20.4:                    # 7b: macro on the stuck leg, glowing water film
        u = eio((t - 17.9) / 2.5)
        cp = foot + lfr * lerp(2.4, 1.8, u) + fwr * 0.9 + V(0, 0, 0.6)
        key_cam(f, cp, foot.lerp(RAIN0 - fwr * 0.6, 0.35) + V(0, 0, 0.35), 32, 2.4)
    else:                             # 7c: close-up of his straining face
        u = eio((t - 20.4) / 1.56); face = RAIN0 - fwr * 0.75 + V(0, 0, 0.95)
        key_cam(f, face - lfr * lerp(1.4, 1.15, u) + fwr * 0.55 + V(0, 0, 0.12), face + V(0, 0, 0.05), 50, 2.2)

@shot('A08_blur', 21.96, 24.68, RAIN, 'W_RAIN')
def a08(t, f):
    key_rain(f, t); key_giant(f, t); key_blob(f, t)
    base = RAIN0 + fwr * 0.8
    look = ramp(t, 22.0, 22.5)
    stand(f, base, HR, neck=(-0.3 * look, 0, 0), head=(-0.3 * look, 0, 0.1 * math.sin(t)))
    eyes(f, blink(t, 2.8), 1.0)
    face = base + V(0, 0, 1.56)
    if t < 23.4:                      # 8a: his POV, looking up into the rain (blurred in the edit)
        u = eio((t - 21.96) / 1.44)
        cp = face + fwr * 0.3 + V(0, 0, 0.05)
        key_cam(f, cp, face + fwr * 6 + V(0, 0, lerp(8, 14, u)), 18, 16.0)
    else:                             # 8b: extreme close-up of his eye, pushing in
        u = eio((t - 23.4) / 1.28); eye = EYES[0].matrix_world.translation.copy()
        eye_w = face + fwr * 0.19 + lfr * 0.072 + V(0, 0, 0.03)
        key_cam(f, eye_w + fwr * lerp(0.6, 0.36, u) + V(0, 0, -0.02), eye_w, 60, 4.0)

@shot('A09_lab', 24.68, 28.68, ['ANT_LAB', 'LIB_stickman_rig'], 'W_LAB')
def a09(t, f):
    key_rays(f, t)
    hp = LAB0 + V(3.0, -2.5, 0); hh = math.atan2(-1.0, -1.0)
    stand(f, hp, hh, hands=(hp + V(0, 0, 0.8) + V(-0.4, 0.35, 0.35), None) if False else None, head=(-0.1, 0, 0.3))
    eyes(f, blink(t, 3.0), 1.0)
    pc = PUPIL.location
    if t < 26.6:                      # 9a: dolly along the giant hair to the tiny glowing pupil
        u = eio((t - 24.68) / 1.92)
        cp = LAB0 + V(lerp(-9.0, -1.5, u), -7.0, lerp(4.2, 3.5, u))
        key_cam(f, cp, LAB0 + V(lerp(-5.0, 0.0, u), 2.0, 3.2), 28, 8.0)
    else:                             # 9b: side view of rays going in straight and fanning out
        u = eio((t - 26.6) / 2.08)
        cp = pc + V(lerp(1.0, 2.0, u), -9.0, 0.3)
        key_cam(f, cp, pc + V(lerp(1.0, 2.0, u), 0, 0), 30, 11.0)

@shot('A10_shout', 28.68, 35.22, RAIN, 'W_RAIN')
def a10(t, f):
    key_rain(f, t); key_giant(f, t); key_blob(f, t)
    base = RAIN0 + fwr * 2.0; hs = math.atan2(GSTEPS[2][3].y - base.y, GSTEPS[2][3].x - base.x)
    fws, lfs = frame_vecs(hs); C = base + V(0, 0, 0.845)
    sh = ramp(t, 28.8, 29.1) * (1 - ramp(t, 32.0, 32.4))
    pump = 0.04 * math.sin(t * 14) * sh
    hands = (C + fws * 0.18 + lfs * 0.08 + V(0, 0, 0.66 * sh + pump), C + fws * 0.18 - lfs * 0.08 + V(0, 0, 0.66 * sh + pump))
    if sh < 0.05: hands = None
    stand(f, base, hs, hands=hands, neck=(-0.35 * sh, 0, 0), head=(-0.3 * sh, 0, 0), lean=-0.08 * sh)
    eyes(f, blink(t, 3.1), 1.0 + 0.25 * sh)
    if t < 30.6:                      # 10a: low behind him shouting up at the passing giant
        u = eio((t - 28.68) / 1.92)
        cp = base - fws * 3.6 + lfs * 1.6 + V(0, 0, 0.3)
        key_cam(f, cp, base + fws * 40 + V(0, 0, lerp(20, 30, u)), 16, 10.0)
    else:                             # 10b/11 plate: high and wide, a tiny white dot nobody notices
        u = eio((t - 30.6) / 4.62)
        cp = base - fws * 14 + lfs * 12 + V(0, 0, lerp(38, 60, u))
        key_cam(f, cp, base, 35, 16.0)

@shot('A12_cold', 35.22, 41.76, ['ANT_GRASS', 'LIB_stickman_rig'], 'W_GRASS')
def a12(t, f):
    hb = GR0 + V(0, 0, 0.05); hh = -math.pi / 2 - 0.4
    fwg, lfg = frame_vecs(hh)
    shv = 0.035 * math.sin(t * 38) * ramp(t, 35.4, 36.0)
    C0 = hb + V(0, 0, 0.22)
    sit(f, hb, hh, lean=0.25, hands_back=False, knees_up=1.0, roll=shv,
        hands=(C0 + fwg * 0.32 + lfg * (0.1 + shv) + V(0, 0, 0.3), C0 + fwg * 0.32 - lfg * (0.1 - shv) + V(0, 0, 0.3)),
        head=(0.25, 0, 0.05 * math.sin(t * 1.3)), hz=0.22)
    eyes(f, blink(t, 2.4) * lerp(1.0, 0.55, ramp(t, 37.8, 39.5)), 0.95)
    if t < 37.82:                     # 12: medium shot under the bent grass blade
        u = eio((t - 35.22) / 2.6)
        cp = hb + fwg * lerp(5.5, 4.8, u) + lfg * 2.2 + V(0, 0, 1.0)
        key_cam(f, cp, hb + V(0, 0, 0.75), 30, 3.2)
    else:                             # 13: slow push-in on him curled up
        u = eio((t - 37.82) / 3.94)
        cp = hb + fwg * lerp(3.2, 1.9, u) - lfg * 1.0 + V(0, 0, 0.8)
        key_cam(f, cp, hb + V(0, 0, 0.7), 40, 2.4)

@shot('A14_back', 41.76, END, CAFE, 'W_CAFE')
def a14(t, f):
    key_drop(f, t); key_splash(f, t)
    h_in = math.atan2(-_cdir.y, -_cdir.x)
    if t < 43.55:                     # climbs over the crumb towards the cup
        u = ramp(t, 41.76, 43.5)
        start = CRUMB_P + _cdir * 3.4; b = start.lerp(HERO1, u)
        hgt = crumb_h(b)
        walk(f, b + V(0, 0, hgt), h_in, (t - 41.76) * 1.7, stride=0.5, lean=0.25 if hgt > 0.2 else 0.08, bz=0.0,
             hands=None if hgt < 0.25 else (b + V(0, 0, hgt + 0.9) + fw1 * 0.45 + lf1 * 0.25, b + V(0, 0, hgt + 0.7) + fw1 * 0.5 - lf1 * 0.25))
        eyes(f, blink(t, 3.0), 1.0)
    else:                             # stops at the hook spot and looks up as the drop forms (flows into frame 0)
        look = ramp(t, 43.55, 44.3)
        stand(f, HERO1, lerp(h_in, H1, ramp(t, 43.55, 43.95)), neck=(-0.3 * look, 0, 0), head=(-0.35 * look, 0, 0.0), lean=-0.05 * look)
        eyes(f, blink(t, 3.3, 1.0), 1.0 + 0.15 * look)
    if t < 43.6:                      # 14a: low side tracking shot, cup towering ahead
        u = eio((t - 41.76) / 1.84)
        b = (CRUMB_P + _cdir * 3.4).lerp(HERO1, ramp(t, 41.76, 43.5)); hb_ = b + V(0, 0, crumb_h(b) + 0.9)
        key_cam(f, hb_ - fw1 * 4.6 - lf1 * 0.8 + V(0, 0, 0.2), hb_ + fw1 * 0.5, 24, 2.8)
    else:                             # 14b: swings round to the exact frame-0 camera
        u = eio((t - 43.6) / (END - 43.6 - 0.25))
        start = HERO1 + lf1 * 4.0 + fw1 * 0.5 + V(0, 0, 0.9)
        key_cam(f, start.lerp(CAM0, u), (HERO1 + V(0, 0, 1.4)).lerp(TGT0, u), lerp(26, 22, u), lerp(4.5, 4.0, u))

def _fcurves(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for lay in act.layers:
            for strip in lay.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out
def build(names=None):
    for s in SHOTS:
        if names and s['name'] not in names: continue
        for fr in range(F(s['t0']), F(s['t1'])):
            s['fn']((fr - 1) / FPS, fr)
    n = 0
    ids = list(D.objects) + list(D.metaballs) + list(D.cameras) + [m.node_tree for m in D.materials if m.node_tree]
    for idb in ids:
        ad = idb.animation_data
        if not ad or not ad.action: continue
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'; n += 1
    sc.frame_start, sc.frame_end = 1, F(END) - 1
    sc['ant_jobs'] = json.dumps([dict(name=s['name'], a=F(s['t0']), b=F(s['t1']) - 1, sets=s['sets'], world=s['world'], samples=s['samples'], rt=s['rt'], pct=s['pct']) for s in SHOTS])
    print('constant keys', n)
    return [(s['name'], F(s['t0']), F(s['t1']) - 1) for s in SHOTS]
