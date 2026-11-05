import bpy, math, random
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene
FPS = 30
def F(t): return int(round(t * FPS)) + 1
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = cl(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def ramp(t, a, b): return ss((t - a) / (b - a)) if b != a else (1.0 if t >= a else 0.0)
def V(*a): return Vector(a)

rig = bpy.data.objects['StickRig']; P = rig.pose.bones
rig.location = (0, 0, -0.016); rig.rotation_euler = (0, 0, 0)
cam = bpy.data.objects['Cam']; tgt = bpy.data.objects['CamTgt']
sc.camera = cam
for pb in P:
    pb.rotation_mode = 'QUATERNION' if pb.name in ('hips', 'IK_foot.L', 'IK_foot.R') else 'XYZ'

def setM(pb, pos, ang, tilt=(0.0, 0.0)):
    R0 = pb.bone.matrix_local.to_3x3()
    Rw = Matrix.Rotation(ang, 3, 'Z') @ Matrix.Rotation(tilt[0], 3, 'X') @ Matrix.Rotation(tilt[1], 3, 'Y')
    pb.matrix = Matrix.Translation(V(*pos) - rig.location) @ (Rw @ R0).to_4x4()
def setT(pb, pos):
    pb.matrix = Matrix.Translation(V(*pos) - rig.location) @ pb.bone.matrix_local.to_3x3().to_4x4()

def body(f, hip, h, feet, hands, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), tilt=(0.0, 0.0)):
    """hip: world pos of hips head; h: facing angle (rad, 0 = +X); feet: ((pos,h),(pos,h)) L,R; hands: (posL, posR)"""
    fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
    setM(P['hips'], hip, h + math.pi / 2, tilt)
    for S, (fp, fh) in zip('LR', feet):
        sg = 1 if S == 'L' else -1
        setM(P['IK_foot.' + S], fp, fh + math.pi / 2)
        kp = (V(*fp) + V(*hip)) / 2 + V(math.cos(fh), math.sin(fh), 0) * 0.9 + L * 0.05 * sg
        setT(P['pole_knee.' + S], (kp.x, kp.y, (fp[2] + hip[2]) / 2))
        ep = V(*hip) - fw * 0.7 + L * 0.4 * sg + V(0, 0, 0.15)
        setT(P['pole_elbow.' + S], ep)
    for S, hp in zip('LR', hands): setT(P['IK_hand.' + S], hp)
    P['spine'].rotation_euler = spine; P['neck'].rotation_euler = neck; P['head'].rotation_euler = head
    for n in ('hips', 'IK_foot.L', 'IK_foot.R'):
        P[n].keyframe_insert('location', frame=f); P[n].keyframe_insert('rotation_quaternion', frame=f)
    for n in ('pole_knee.L', 'pole_knee.R', 'pole_elbow.L', 'pole_elbow.R', 'IK_hand.L', 'IK_hand.R'):
        P[n].keyframe_insert('location', frame=f)
    for n in ('spine', 'neck', 'head'): P[n].keyframe_insert('rotation_euler', frame=f)

def local(hip, h, fwd, lat, z):
    fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
    return V(*hip) + fw * fwd + L * lat + V(0, 0, z)

def stand(f, base, h, lift=0.0, hands=None, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), hipdz=0.0):
    """standing (or hovering by `lift`) at base (ground point)"""
    b = V(*base) + V(0, 0, lift)
    hip = b + V(0, 0, 0.845 + hipdz)
    L = V(-math.sin(h), math.cos(h), 0)
    feet = ((b + L * 0.09 + V(0, 0, 0.055), h), (b - L * 0.09 + V(0, 0, 0.055), h))
    if hands is None: hands = (local(hip, h, 0.03, 0.25, -0.075), local(hip, h, 0.03, -0.25, -0.075))
    body(f, hip, h, feet, hands, spine, neck, head)

def floaty(f, t, hip, h, flail=1.0, spine=(0, 0, 0), head=(0, 0, 0), tilt=(0.0, 0.0), armup=0.0):
    """floating: legs dangle, arms out, gentle flailing"""
    hip = V(*hip); L = V(-math.sin(h), math.cos(h), 0); fw = V(math.cos(h), math.sin(h), 0)
    s1 = math.sin(t * 2.3) * flail; s2 = math.sin(t * 2.9 + 1) * flail
    feet = ((hip + L * 0.11 + fw * (0.08 + 0.07 * s1) + V(0, 0, -0.70 + 0.04 * s2), h + 0.2),
            (hip - L * 0.11 + fw * (0.02 - 0.07 * s1) + V(0, 0, -0.72 - 0.04 * s2), h - 0.2))
    za = 0.38 + armup + 0.07 * s2
    hands = (local(hip, h, 0.10 + 0.06 * s1, 0.42, za), local(hip, h, 0.10 - 0.06 * s1, -0.42, za + 0.04 * s1))
    body(f, hip, h, feet, hands, spine, (0, 0, 0), head, tilt)

def key_obj(o, f, loc=None, rot=None):
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)

def key_cam(f, cp, tp, lens=None):
    cam.location = cp; tgt.location = tp
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f)
    if lens: cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)

# ---------- prop layout ----------
LAYOUT = {'BIN1': (2.95, 1.35, 0.15, 0.3), 'BIN2': (2.8, 2.05, 0.15, -0.4), 'BAG': (2.45, 1.75, 0.15, 0.8),
          'CAN': (2.05, 0.75, 0.183, 0.7), 'CONE1': (3.25, -1.05, 0.15, 0.0), 'CONE2': (4.25, 2.6, 0.0, 0.4), 'CONE3': (4.35, 3.6, 0.0, 0.8),
          'BENCH': (0.75, -2.6, 0.15, -1.5708), 'CAR_Hatchback': (11.3, -15.0, 0.0, 0.0), 'CAR_Compact': (11.3, 14.0, 0.0, 0.0), 'CAR_Wagon': (4.75, 27.0, 0.0, 3.1416)}
for n, (x, y, z, rz) in LAYOUT.items():
    o = bpy.data.objects.get(n)
    if o is None: continue
    o.animation_data_clear()
    if n == 'CAN': o.location = (x, y, z); o.rotation_euler = (1.5708, 0, rz)
    else: o.location = (x, y, z); o.rotation_euler = (0, 0, rz)
    o['rest'] = list(o.location) + list(o.rotation_euler)
# ---------- props registry (rest pose) ----------
PROPS = {}
for n in ['BIN1', 'BIN2', 'BENCH', 'BAG', 'CONE1', 'CONE2', 'CONE3', 'CAN', 'CAR_Sedan', 'CAR_Hatchback', 'CAR_Compact', 'CAR_Wagon', 'CAR_SUV', 'BIN1_LID'] + \
         [o.name for o in bpy.data.objects if o.name.startswith('LEAF')]:
    o = bpy.data.objects.get(n)
    if o is None: continue
    if 'rest' not in o: o['rest'] = list(o.location) + list(o.rotation_euler)
    PROPS[n] = o
def rest(o): r = o['rest']; return V(*r[:3]), Euler(r[3:])
rnd = random.Random(7)
SEED = {n: (rnd.uniform(0.6, 1.4), rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 6.28), rnd.uniform(0.5, 1.6)) for n in PROPS}

def drift_state(n, s):
    """state of a prop after s 'story seconds' without gravity (0..5): rise + tumble"""
    o = PROPS[n]; p0, r0 = rest(o); k, a, b, ph, sp = SEED[n]
    if n.startswith('CAR'):
        lift = 0.08 * s * s * 0.25 * k
        return p0 + V(0, 0, lift), Euler((r0.x + 0.01 * a * s, r0.y + 0.01 * b * s, r0.z))
    if n.startswith('LEAF'):
        lift = (0.15 + 0.5 * k) * s
        return p0 + V(0.25 * a * s, 0.25 * b * s, lift), Euler((r0.x + a * s * sp, r0.y + b * s * sp, r0.z + s * 0.6))
    lift = (0.06 + 0.10 * k) * s + (0.25 * k if n in ('BAG', 'CAN') else 0) * s
    tumble = 0.12 * s * sp
    return p0 + V(0.03 * a * s, 0.03 * b * s, lift), Euler((r0.x + a * tumble, r0.y + b * tumble, r0.z + 0.2 * s * a))

def props_at(f, s, only=None, extra=None):
    for n, o in PROPS.items():
        if only and not any(n.startswith(x) for x in only): continue
        p, r = drift_state(n, s)
        if extra and n in extra: p, r = extra[n](p, r)
        key_obj(o, f, p, r)

def props_rest(f):
    for n, o in PROPS.items():
        p, r = rest(o); key_obj(o, f, p, r)

HOME = V(2.3, 0.0, 0.15)
H_FACE = math.radians(-35)   # facing the street, slightly towards camera side (-Y)
SHOTS = {}
def shot(name, t0, t1):
    def deco(fn): SHOTS[name] = (t0, t1, fn); return fn
    return deco

# ---------------- SH1 hook: everything already floating up ----------------
@shot('SH01_hook', 0.0, 4.10)
def sh1(t, f):
    s = 1.2 + 0.35 * t           # story seconds since gravity off
    props_at(f, s)
    lift = 0.30 + 0.16 * t
    hip = HOME + V(0, 0, 0.845 + lift)
    floaty(f, t, hip, H_FACE, flail=1.0, head=(-0.15 + 0.05 * math.sin(t * 2), 0, 0.1 * math.sin(t * 1.3)),
           spine=(-0.05, 0, 0.06 * math.sin(t * 1.7)), tilt=(0.05 * math.sin(t * 1.1), 0.06 * math.sin(t * 0.9)), armup=0.08)
    u = ss(t / 4.1)
    key_cam(f, V(5.2, -0.75, 1.1).lerp(V(4.85, -0.6, 1.2), u), V(2.3, 0.1, 1.9).lerp(V(2.3, 0.1, 2.05), u), 24)

# ---------------- SH2 stomach drop close-up ----------------
@shot('SH02_stomach', 6.20, 8.26)
def sh2(t, f):
    props_at(f, 0.15 + 0.06 * t, only=['LEAF', 'CAN'])
    for n in ('BIN1', 'BIN2', 'BENCH', 'BAG', 'CONE1', 'CONE2', 'CONE3') + tuple(k for k in PROPS if k.startswith('CAR')):
        p, r = drift_state(n, 0.1 + 0.05 * t); key_obj(PROPS[n], f, p, r)
    lift = 0.01 + 0.02 * ramp(t, 0.2, 2.0)
    hip = HOME + V(0, 0, 0.845 + lift)
    h = H_FACE
    belly_l = local(hip, h, 0.11, 0.07, 0.17); belly_r = local(hip, h, 0.12, -0.06, 0.08)
    a = ramp(t, 0.0, 0.35)
    hl = local(hip, h, 0.03, 0.25, -0.075).lerp(belly_l, a); hr = local(hip, h, 0.03, -0.25, -0.075).lerp(belly_r, a)
    L = V(-math.sin(h), math.cos(h), 0); b = HOME + V(0, 0, lift)
    feet = ((b + L * 0.09 + V(0, 0, 0.055 + 0.01 * a), h), (b - L * 0.09 + V(0, 0, 0.055), h))
    body(f, hip - V(0, 0, 0.02 * a), h, feet, (hl, hr), spine=(0.18 * a, 0, 0), neck=(0.05 * a, 0, 0),
         head=(-0.25 * a + 0.03 * math.sin(t * 9), 0, 0))
    cp = HOME + V(2.3, -0.75, 1.3); tp = HOME + V(0, 0.05, 1.22 + 0.03 * t)
    key_cam(f, cp + V(-0.15 * t, 0.05 * t, 0), tp, 40)

# ---------------- SH3 shoe gap ----------------
@shot('SH03_gap', 8.26, 10.92)
def sh3(t, f):
    for n in PROPS:
        p, r = drift_state(n, 0.12 + 0.03 * t); key_obj(PROPS[n], f, p, r)
    lift = 0.022 + 0.004 * t
    h = H_FACE
    stand(f, HOME, h, lift=lift, head=(0.35 * ramp(t, 1.4, 2.2), 0, 0), spine=(0.06 * ramp(t, 1.4, 2.2), 0, 0))
    u = ss((t - 0.9) / 1.7)
    cp = HOME + V(1.35, -0.45, 0.07)
    tp = (HOME + V(0, 0.02, 0.10)).lerp(HOME + V(0, 0.02, 1.45), u)
    cp2 = cp.lerp(HOME + V(1.9, -0.6, 0.6), u)
    key_cam(f, cp2, tp, lerp(55, 34, u))

# ---------------- SH7 drifting up (ruler) ----------------
@shot('SH07_drift', 21.94, 25.83)
def sh7(t, f):
    s = 1.0 + 0.9 * t
    for n in PROPS: p, r = drift_state(n, s); key_obj(PROPS[n], f, p, r)
    lift = 0.06 + 0.34 * ss(t / 3.89)
    hip = HOME + V(0, 0, 0.845 + lift)
    floaty(f, t, hip, H_FACE, flail=0.6 * ramp(t, 0.3, 1.5), head=(0.25, 0, 0.05 * math.sin(t * 2)), armup=-0.15)
    cp = V(6.7, -0.9, 0.95) + V(-0.3, 0.1, 0.15) * ss(t / 3.89)
    key_cam(f, cp, HOME + V(0.3, 0.1, 0.8 + 0.15 * ss(t / 3.89)), 28)

# ---------------- SH8-9 car with no grip ----------------
@shot('SH08_car', 27.40, 32.48)
def sh8(t, f):
    for n in PROPS:
        if n == 'CAR_Sedan': continue
        p, r = drift_state(n, 1.5 + 0.3 * t); key_obj(PROPS[n], f, p, r)
    car = PROPS['CAR_Sedan']
    y = -16.0 + 6.0 * t
    T_S, T_K = 2.7, 3.85                         # steer, kerb
    x = 6.1; z = 0.07 * ss(t / 2.5)
    rot = [0, 0, math.pi]
    if t > T_S: x = 6.1 - 1.45 * ss((t - T_S) / (T_K - T_S))
    if t > T_K:
        k = t - T_K
        z += 0.75 * k + 0.25 * (1 - math.exp(-k * 6)); rot[0] = -0.30 * k; rot[1] = 0.22 * k
    key_obj(car, f, V(x, y, z), Euler(rot))
    stand(f, HOME + V(-0.3, 0, 0), math.radians(-60), lift=0.15 + 0.03 * t,
          head=(0.1, 0, 0), neck=(0, -0.3 + 0.6 * ss(t / 4.5), 0))
    tc = min(t, T_K) + (1 - math.exp(-max(t - T_K, 0) * 2.0)) / 2.0   # camera dollies with the car, eases to a stop after the kerb
    yc = -16.0 + 6.0 * tc
    cp = V(12.3, yc - 1.2, 1.25)
    tp = V(lerp(x, 4.0, 0.25), yc + 0.6, 0.85 + z * 0.7)
    key_cam(f, cp, tp, 26)

# ---------------- SH10-11 the hop ----------------
T_HOP = 34.62
@shot('SH10_hop', 34.10, 40.04)
def sh10(tt, f):
    t = tt + 34.10
    s = 2.0 + 0.25 * tt
    for n in PROPS:
        if n == 'CAR_Sedan': continue
        p, r = drift_state(n, s); key_obj(PROPS[n], f, p, r)
    h = H_FACE
    if t < T_HOP:
        c = ramp(t, 34.18, 34.52)                # crouch
        stand(f, HOME, h, lift=0.035, hipdz=-0.16 * c, spine=(0.25 * c, 0, 0), head=(-0.15 * c, 0, 0),
              hands=(local(HOME + V(0, 0, 0.8), h, -0.12 * c, 0.27, -0.05 + 0.1 * c), local(HOME + V(0, 0, 0.8), h, -0.12 * c, -0.27, -0.05 + 0.1 * c)))
        zc = 0.0
    else:
        k = t - T_HOP
        zc = 1.05 * k + 0.25 * (1 - math.exp(-k * 3))    # launch then steady rise
        hip = HOME + V(0, 0, 0.845 + 0.035 + zc)
        floaty(f, k, hip, h, flail=lerp(0.3, 1.4, ramp(k, 0.5, 2.0)), head=(lerp(-0.2, 0.45, ramp(k, 1.0, 3.5)), 0, 0.12 * math.sin(k * 2)),
               spine=(0.1 * math.sin(k), 0, 0), tilt=(0.06 * math.sin(k * 1.4), 0.08 * math.sin(k)), armup=0.15 * ramp(k, 0.3, 1.0))
    camz = 1.05 + max(0.0, zc) * 0.95
    cp = V(7.3, -0.9, camz); tp = HOME + V(0.0, 0.1, 0.95 + zc * 0.98)
    key_cam(f, cp, tp, 24)

# ---------------- SH15 frozen mid-air (calm before) ----------------
UP = 5.05
@shot('SH15_frozen', 48.80, 51.43)
def sh15(t, f):
    s = 4.6 + 0.08 * t
    extra = {'CAR_Sedan': lambda p, r: (V(6.4, -3.6, 1.45 + 0.03 * t), Euler((-0.45, 0.3, math.pi + 0.1)))}
    props_at(f, s, extra=extra)
    hip = HOME + V(0.15, 0.2, 0.845 + UP)
    floaty(f, t, hip, H_FACE, flail=0.35, head=(0.5, 0, 0), armup=0.1)
    u = ss(t / 2.63)
    key_cam(f, V(13.0, -1.3, 2.4).lerp(V(12.4, -1.1, 2.55), u), V(2.8, -0.4, 2.75), 18)

# ---------------- SH17 everything comes down ----------------
T_DROP = 55.05
def fall(p_air, ground_z, t, k=1.0, bounce=0.18):
    """free fall from p_air.z to ground_z starting t>=0, with small bounces"""
    h = p_air.z - ground_z; g = 9.8 * k
    tf = math.sqrt(2 * max(h, 0.001) / g)
    if t < tf: return p_air.z - 0.5 * g * t * t, False
    tb = t - tf; v = g * tf * bounce; tb2 = 2 * v / g
    if tb < tb2: return ground_z + v * tb - 0.5 * g * tb * tb, True
    return ground_z, True
@shot('SH17_drop', 53.30, 57.54)
def sh17(tt, f):
    t = tt + 53.30
    s_air = 4.75
    for n, o in PROPS.items():
        p_air, r_air = drift_state(n, s_air)
        if n == 'CAR_Sedan': p_air, r_air = V(6.4, -3.6, 1.55), Euler((-0.45, 0.3, math.pi + 0.1))
        p0, r0 = rest(o)
        if t < T_DROP:
            key_obj(o, f, p_air + (p_air - p0) * 0.01 * (t - 53.3), r_air); continue
        k = t - T_DROP
        if n.startswith('LEAF'):
            z = max(p0.z, p_air.z - 0.9 * k); rr = Euler((r_air.x + k * 2, r_air.y + k * 1.5, r_air.z))
            if z <= p0.z + 1e-3: rr = r0
            key_obj(o, f, V(p_air.x + 0.2 * math.sin(k * 3 + SEED[n][3]), p_air.y, z), rr); continue
        z, landed = fall(p_air, p0.z, k)
        sett = ramp(k, math.sqrt(2 * max(p_air.z - p0.z, 0.01) / 9.8), math.sqrt(2 * max(p_air.z - p0.z, 0.01) / 9.8) + 0.35)
        rr = Euler((lerp(r_air.x, r0.x, sett), lerp(r_air.y, r0.y, sett), lerp(r_air.z, r0.z + 0.3 * SEED[n][1], sett)))
        if n == 'CAR_Sedan':
            rr = Euler((lerp(r_air.x, 0, sett), lerp(r_air.y, 0, sett), r_air.z))
        if n in ('BIN1', 'BIN2', 'CONE1', 'CONE2', 'CONE3', 'CAN') and landed:
            tip = ramp(k, 0.55, 0.9) * (1.45 if n != 'CAN' else 0)
            rr = Euler((r0.x + tip * SEED[n][1], r0.y + tip * SEED[n][2], rr.z))
            if tip: z = p0.z + (0.28 if n.startswith('BIN') else 0.12) * ss(tip / 1.45)
        key_obj(o, f, V(p_air.x, p_air.y, z), rr)
    hip = HOME + V(0.15, 0.2, 0.845 + UP)
    floaty(f, tt, hip, H_FACE, flail=0.35, head=(0.5, 0, 0))
    shake = 0.0
    if t > T_DROP + 0.35: shake = 0.05 * math.exp(-(t - T_DROP - 0.35) * 3) * math.sin(t * 70)
    key_cam(f, V(12.2, -1.0, 1.6 + shake), V(3.4, -0.6, 1.0 + shake), 20)

# ---------------- SH18-19 at the window, then the fall ----------------
T_FALL = 59.72; T_IMPACT = T_FALL + math.sqrt(2 * UP / 9.8)
@shot('SH18_fall', 57.54, 63.44)
def sh18(tt, f):
    t = tt + 57.54
    for n, o in PROPS.items():
        p0, r0 = rest(o)
        if n == 'CAR_Sedan': key_obj(o, f, V(6.4, -3.6, 0.0), Euler((0, 0, math.pi + 0.1))); continue
        key_obj(o, f, p0, r0)
    h = H_FACE
    if t < T_FALL:
        hip = HOME + V(0.15, 0.2, 0.845 + UP)
        look = ramp(t, 57.7, 58.3)
        floaty(f, tt, hip, h, flail=0.3 + 0.8 * ramp(t, 58.9, 59.6), head=(0.75 * look, 0, 0), armup=0.0)
        zc = UP
        cp = HOME + V(3.6, -0.8, UP + 0.9); tp = hip + V(0, 0, 0.3)
    elif t < T_IMPACT:
        k = t - T_FALL; zc = UP - 0.5 * 9.8 * k * k
        hip = HOME + V(0.15 * (1 - k), 0.2, 0.845 + zc)
        floaty(f, tt, hip, h, flail=1.6, head=(-0.4, 0, 0), armup=0.35)
        cp = HOME + V(3.6, -0.8, max(0.6, zc + 0.9 - 0.3 * k)); tp = hip + V(0, 0, 0.2)
    else:
        k = t - T_IMPACT; zc = 0.0
        sq = math.exp(-k * 7) * math.cos(k * 22)
        sit = ramp(k, 0.0, 0.08)
        b = HOME
        hip = b + V(0, 0, 0.30 + 0.05 * sq)
        fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
        feet = ((b + fw * 0.55 + L * 0.16 + V(0, 0, 0.05), h + 0.3), (b + fw * 0.5 - L * 0.16 + V(0, 0, 0.05), h - 0.3))
        dz = 0.12 * math.sin(k * 5)
        hands = (local(hip, h, -0.15, 0.32, -0.20), local(hip, h, -0.15, -0.32, -0.20))
        body(f, hip, h, feet, hands, spine=(-0.25 + 0.1 * sq, 0, 0.08 * math.sin(k * 6)),
             head=(0.1 * math.sin(k * 5), 0.25 * math.sin(k * 4.5), 0.25 * math.sin(k * 6)))
        cp = HOME + V(3.6, -0.8, 0.6) + V(0, 0, 0.02 * sq); tp = HOME + V(0.1, 0.1, 0.55)
    key_cam(f, cp, tp, 26)

# ---------------- SH20-21 hold on to the lamp post ----------------
LAMP = V(3.15, -5.5, 0.15)
@shot('SH20_lamp', 63.30, 68.40)
def sh20(tt, f):
    t = tt + 63.30
    s = 1.0 + 0.2 * tt
    for n in PROPS:
        p, r = drift_state(n, s); key_obj(PROPS[n], f, p, r)
    base = LAMP + V(0.12, -0.5, 0)
    h = 0.0
    lift = 0.06 + 0.04 * tt
    hip = base + V(0, 0, 0.845 + lift)
    fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
    grip = LAMP + V(-0.06, 0.0, 1.55)
    look = ramp(t, 66.35, 66.75)
    feet = ((base + L * 0.1 + V(0, 0, 0.055 + lift + 0.05 * math.sin(tt * 2)), h), (base - L * 0.1 + fw * 0.05 + V(0, 0, 0.055 + lift), h))
    hands = (grip, local(hip, h, 0.05, -0.3, 0.05 + 0.05 * math.sin(tt * 2.3)))
    body(f, hip, h, feet, hands, spine=(0.0, 0, 0.10), neck=(0, 0.35 * (1 - look), 0), head=(-0.05, 0.45 * (1 - look), 0.06 * look))
    u = ss(tt / 5.1)
    key_cam(f, V(7.4, -6.4, 1.3).lerp(V(6.8, -6.2, 1.35), u), V(2.85, -5.5, 1.4), 30)

def build(names=None):
    for n, (t0, t1, fn) in SHOTS.items():
        if names and n not in names: continue
        for f in range(F(t0), F(t1) + 1):
            fn((f - 1) / FPS - t0, f)
    print('built', names or list(SHOTS))
