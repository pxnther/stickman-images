"""Freeze-time Short: all 3D shots keyed on one global timeline (frame = round(t*30)+1, constant interpolation)."""
import bpy, math, json
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene; D = bpy.data
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
G = {'__name__': 'fzset'}
exec(open(TEX + r"\fz_set_v8.py", encoding='utf-8').read(), G)
V = G['V']
FPS = 30
def F(t): return int(round(t * FPS)) + 1
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = cl(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def ramp(t, a, b): return ss((t - a) / (b - a)) if b != a else (1.0 if t >= a else 0.0)
def eio(u): u = cl(u); return 0.5 - 0.5 * math.cos(math.pi * u)

prefs = bpy.context.preferences.edit; OLD_INTERP = prefs.keyframe_new_interpolation_type
prefs.keyframe_new_interpolation_type = 'CONSTANT'

HERO = D.objects['StickRig']; PEDS = G['PEDS']
cam = D.objects['Cam']; tgt = D.objects['CamTgt']; sc.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.sensor_fit = 'AUTO'; cam.data.sensor_width = 36
for rig in [HERO] + list(PEDS.values()):
    rig.location = (0, 0, -0.016); rig.rotation_euler = (0, 0, 0)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION' if pb.name in ('hips', 'IK_foot.L', 'IK_foot.R') else 'XYZ'

# ---------------- rig posing (any rig) ----------------
def setM(rig, pb, pos, ang, tilt=(0.0, 0.0)):
    R0 = pb.bone.matrix_local.to_3x3()
    Rw = Matrix.Rotation(ang, 3, 'Z') @ Matrix.Rotation(tilt[0], 3, 'X') @ Matrix.Rotation(tilt[1], 3, 'Y')
    pb.matrix = Matrix.Translation(V(*pos) - rig.location) @ (Rw @ R0).to_4x4()
def setT(rig, pb, pos):
    pb.matrix = Matrix.Translation(V(*pos) - rig.location) @ pb.bone.matrix_local.to_3x3().to_4x4()
def body(rig, f, hip, h, feet, hands, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), tilt=(0.0, 0.0), elbows=None):
    P = rig.pose.bones
    fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
    setM(rig, P['hips'], hip, h + math.pi / 2, tilt)
    for S, (fp, fh) in zip('LR', feet):
        sg = 1 if S == 'L' else -1
        setM(rig, P['IK_foot.' + S], fp, fh + math.pi / 2)
        kp = (V(*fp) + V(*hip)) / 2 + V(math.cos(fh), math.sin(fh), 0) * 0.9 + L * 0.05 * sg
        setT(rig, P['pole_knee.' + S], (kp.x, kp.y, (fp[2] + hip[2]) / 2))
        ep = V(*hip) - fw * 0.7 + L * 0.4 * sg + V(0, 0, 0.15) if not elbows else elbows[0 if S == 'L' else 1]
        setT(rig, P['pole_elbow.' + S], ep)
    for S, hp in zip('LR', hands): setT(rig, P['IK_hand.' + S], hp)
    P['spine'].rotation_euler = spine; P['neck'].rotation_euler = neck; P['head'].rotation_euler = head
    for n in ('hips', 'IK_foot.L', 'IK_foot.R'):
        P[n].keyframe_insert('location', frame=f); P[n].keyframe_insert('rotation_quaternion', frame=f)
    for n in ('pole_knee.L', 'pole_knee.R', 'pole_elbow.L', 'pole_elbow.R', 'IK_hand.L', 'IK_hand.R'):
        P[n].keyframe_insert('location', frame=f)
    for n in ('spine', 'neck', 'head'): P[n].keyframe_insert('rotation_euler', frame=f)
def local(hip, h, fwd, lat, z):
    fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
    return V(*hip) + fw * fwd + L * lat + V(0, 0, z)
def stand(rig, f, base, h, hands=None, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), hipdz=0.0, stance=0.09, tilt=(0.0, 0.0), feet_fwd=(0.0, 0.0)):
    b = V(*base); hip = b + V(0, 0, 0.845 + hipdz)
    L = V(-math.sin(h), math.cos(h), 0); fw = V(math.cos(h), math.sin(h), 0)
    feet = ((b + L * stance + fw * feet_fwd[0] + V(0, 0, 0.055), h), (b - L * stance + fw * feet_fwd[1] + V(0, 0, 0.055), h))
    if hands is None: hands = (local(hip, h, 0.03, 0.25, -0.075), local(hip, h, 0.03, -0.25, -0.075))
    body(rig, f, hip, h, feet, hands, spine, neck, head, tilt)
    return hip
def walk_pose(rig, f, base, h, ph, stride=0.6, arms=1.0, lean=0.07, head=(0, 0, 0), hands=None, neck=(0, 0, 0)):
    c = math.cos(2 * math.pi * ph); s_ = math.sin(2 * math.pi * ph)
    b = V(*base); L = V(-math.sin(h), math.cos(h), 0); fw = V(math.cos(h), math.sin(h), 0)
    lf = b + fw * (0.5 * stride * c) + L * 0.085 + V(0, 0, 0.055 + 0.10 * max(0.0, -s_))
    rf = b - fw * (0.5 * stride * c) - L * 0.085 + V(0, 0, 0.055 + 0.10 * max(0.0, s_))
    hip = b + V(0, 0, 0.80 + 0.03 * abs(s_)) - L * 0.012 * c
    if hands is None:
        hands = (local(hip, h, 0.04 - 0.17 * c * arms, 0.24, -0.08 + 0.03 * abs(c)), local(hip, h, 0.04 + 0.17 * c * arms, -0.24, -0.08 + 0.03 * abs(c)))
    yaw = 0.08 * c
    body(rig, f, hip, h + yaw, ((lf, h), (rf, h)), hands, spine=(lean, -yaw * 1.5, 0), neck=neck, head=head)
    return hip

# ---------------- world state (as functions of world time tau; 0 = the freeze moment) ----------------
BIRDS = G['BIRDS']
def bird_at(b, tau):
    vz = b['v'].z; gz = 0.15 if b['p'].x < 3.15 else 0.0
    tg = -(b['p'].z - gz) / vz
    if tau < tg:
        return V(0, 0, -60), b['ph'], 0.0
    p = b['p'] + b['v'] * tau + (V(0, 0, 0.35 * tau * tau) if tau > 0 else V(0, 0, 0))
    return p, b['ph'] + b['fr'] * tau, b['pitch']
def key_birds(f, tau):
    for b in BIRDS:
        p, ph, pitch = bird_at(b, tau)
        r = b['root']; r.location = p; r.rotation_euler = (pitch, b['roll'] if pitch else 0.0, b['h'] - math.pi / 2)
        r.keyframe_insert('location', frame=f); r.keyframe_insert('rotation_euler', frame=f)
        G['flap_pose'](b['arm'], ph)
        for pb in b['arm'].pose.bones:
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('rotation_quaternion' if pb.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=f)
            pb.keyframe_insert('scale', frame=f)
PED_SPEC = {'FZ_ped1': (V(2.05, -0.6, 0.15), math.pi / 2, 1.15, 0.27),
            'FZ_ped2': (V(5.8, 1.7, 0.0), 0.0, 1.3, 0.62),
            'FZ_ped4': (V(2.3, -9.2, 0.15), math.pi / 2, 1.2, 0.05),
            'FZ_ped3': None}
CUP_P = G['CUP_P']; SPL_O = G['SPL_ORIGIN']
def key_peds(f, tau):
    for n, spec in PED_SPEC.items():
        rig = PEDS[n]
        if spec is None:   # ped3: standing at the cafe table, hand just let go of a sugar cube above the cup
            base = V(0.98, -4.3, 0.15); h = 0.0
            k = cl(tau + 0.6, 0, 3) if tau > 0 else 0.0
            hip = base + V(0, 0, 0.83)
            reach = local(hip, h, 0.40, -0.12, 0.28)
            hands = (local(hip, h, 0.05, 0.24, -0.06), reach.lerp(local(hip, h, 0.1, -0.24, -0.06), ss(k / 1.0)))
            stand(rig, f, base, h, hands=hands, spine=(0.32 * (1 - ss(k)), 0, 0), head=(0.35 * (1 - ss(k)), 0, 0), hipdz=-0.02)
            continue
        p0, h, sp, ph0 = spec
        fw = V(math.cos(h), math.sin(h), 0)
        walk_pose(rig, f, p0 + fw * sp * tau, h, ph0 + tau * sp / 1.2, head=(0.05, 0, 0))
TAXI = D.objects['CAR_Sedan']; P0 = V(8.8, -1.2, 0.0); PSI0 = -0.45; TSPD = 3.6
WHEELS = {n: D.objects[n] for n in ('Wheel_A', 'Wheel_A001', 'Wheel_A002', 'Wheel_A003')}
for w in WHEELS.values(): w.rotation_mode = 'XYZ'
def psi_at(tau): return PSI0 * math.exp(-1.1 * tau) if tau > 0 else PSI0 * max(0.0, 1 + 0.55 * tau)
def taxi_at(tau):
    n = int(abs(tau) * 60) + 1; dt = tau / n; p = P0.copy(); t = 0.0
    for i in range(n):
        ps = psi_at(t + dt / 2); p += V(math.sin(ps), -math.cos(ps), 0) * TSPD * dt; t += dt
    return p, psi_at(tau)
def key_taxi(f, tau):
    p, ps = taxi_at(tau)
    TAXI.location = p; TAXI.rotation_euler = (0, 0, ps)
    TAXI.keyframe_insert('location', frame=f); TAXI.keyframe_insert('rotation_euler', frame=f)
    spin = -TSPD * tau / 0.32
    steer = 0.55 * (psi_at(tau) - psi_at(tau + 0.1)) / 0.1 / 0.6 if True else 0
    for n, w in WHEELS.items():
        front = w.location.y < 0
        w.rotation_euler = (spin, 0, (steer if front else 0.0))
        w.keyframe_insert('rotation_euler', frame=f)
pud = D.objects['FZ_puddle']; wat = D.objects['FZ_water']
def place_puddle():
    p, ps = taxi_at(0.0); R = Matrix.Rotation(ps, 3, 'Z')
    c = p + R @ V(-0.95, -1.45, 0); pud.location = (c.x, c.y, 0.004); pud.rotation_euler = (0, 0, ps)
    wc = p + R @ V(-0.85, -1.4, 0); wat.location = wc; wat.rotation_euler = (0, 0, ps + math.pi); wat.scale = (1, -1, 1)
place_puddle()
def key_world(f, tau, spl=None, bird=None, ped=None, taxi=None, wtau=None):
    G['apply_splash'](G['TAU_F'] + (tau if spl is None else spl), f)
    key_birds(f, tau if bird is None else bird)
    key_peds(f, tau if ped is None else ped)
    key_taxi(f, tau if taxi is None else taxi)
    w = 0.2 + (tau if wtau is None else wtau); G['apply_water'](w, f)
# ---------------- holograms / effects ----------------
shock = D.objects['FZ_shock']; SHM = D.materials['FZ_Shock']
SH_MUL = next(n for n in SHM.node_tree.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
def key_shock(f, center, r, alpha):
    shock.location = center; shock.scale = (max(r, 0.001),) * 3; SH_MUL.inputs[1].default_value = alpha
    shock.keyframe_insert('location', frame=f); shock.keyframe_insert('scale', frame=f)
    SH_MUL.inputs[1].keyframe_insert('default_value', frame=f)
RING = D.objects['FZ_ring']; RARC = D.objects['FZ_ring_arc']; RNUM = G['RNUM']
def key_ring(f, loc, scale, n, frac=None, pulse=0.0):
    RING.location = loc; RING.scale = (max(scale, 0.001),) * 3
    RING.keyframe_insert('location', frame=f); RING.keyframe_insert('scale', frame=f)
    RARC.data.bevel_factor_end = max(0.001, n / 10 if frac is None else frac); RARC.data.keyframe_insert('bevel_factor_end', frame=f)
    for k, ob in RNUM.items():
        ob.scale = ((1.0 + pulse) if k == n else 0.001,) * 3; ob.keyframe_insert('scale', frame=f)
mol = D.objects['FZ_mol']; MOLE = next(n for n in D.materials['FZ_Mol'].node_tree.nodes if n.type == 'EMISSION')
def key_mol(f, loc, s, strength):
    mol.location = loc; mol.scale = (max(s, 0.001),) * 3; MOLE.inputs[1].default_value = strength
    mol.keyframe_insert('location', frame=f); mol.keyframe_insert('scale', frame=f); MOLE.inputs[1].keyframe_insert('default_value', frame=f)
glass = D.objects['FZ_glass']; GLM = next(n for n in D.materials['FZ_Glass'].node_tree.nodes if n.type == 'MATH')
GLE = next(n for n in D.materials['FZ_GlassEdge'].node_tree.nodes if n.type == 'EMISSION')
def key_glass(f, loc, dims, a):
    glass.location = loc; glass.scale = dims if a > 0.001 else (0.001,) * 3; GLM.inputs[1].default_value = 0.9 * a; GLE.inputs[1].default_value = 2.5 * a
    glass.keyframe_insert('location', frame=f); glass.keyframe_insert('scale', frame=f)
    GLM.inputs[1].keyframe_insert('default_value', frame=f); GLE.inputs[1].keyframe_insert('default_value', frame=f)
EYES = [D.objects['Eye.L'], D.objects['Eye.R']]
EYE_S0 = [tuple(e.scale) for e in EYES]
def key_eyes(f, k=1.0):
    for e, s0 in zip(EYES, EYE_S0):
        e.scale = (s0[0] * k, s0[1] * k, s0[2] * k); e.keyframe_insert('scale', frame=f)
def key_cam(f, cp, tp, lens, fstop=16.0):
    cam.location = cp; tgt.location = tp; cam.data.lens = lens; cam.data.dof.aperture_fstop = fstop
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f)
    cam.data.keyframe_insert('lens', frame=f); cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

# ---------------- shot definitions ----------------
HS = V(2.95, -3.2, 0.15)                       # hero spot for the snap (cold open / loop)
CAMS1 = V(3.62, -1.05, 1.38)                    # snap close-up camera
H_SNAP = math.atan2(CAMS1.y - HS.y, CAMS1.x - HS.x) - 0.25
HB = V(5.5, -4.6, 0.0)                          # hero spot in the road (orbit, blind, stuck)
T_SNAP = 0.55
def snap_hand(hip, h, t):
    """right hand beside the face; a quick flick at T_SNAP"""
    up = ramp(t, -0.4, 0.35)
    flick = math.exp(-((t - T_SNAP) / 0.05) ** 2)
    base = local(hip, h, 0.03, -0.25, -0.075).lerp(local(hip, h, 0.10, -0.33, 0.52), up)
    return base + local(V(0, 0, 0), h, 0.04 * flick, 0.03 * flick, -0.05 * flick)
def hero_snap_pose(f, t, look_hand=1.0):
    hip = HS + V(0, 0, 0.845)
    hr = snap_hand(hip, H_SNAP, t)
    hl = local(hip, H_SNAP, 0.03, 0.25, -0.075)
    head = (lerp(0.05, -0.12, look_hand) + 0.02 * math.sin(t * 2), 0, lerp(0.0, -0.35, look_hand))
    stand(HERO, f, HS, H_SNAP, hands=(hl, hr), spine=(0.02, -0.08, 0), head=head)
    return hr
_tmp_hip = HS + V(0, 0, 0.845)
SHOCK_C = snap_hand(_tmp_hip, H_SNAP, T_SNAP + 0.2)
D_CUP = (CUP_P - SHOCK_C).length
def shock_r(t):
    if t < T_SNAP: return 0.0
    if t < 1.95: return D_CUP * (t - T_SNAP) / (1.95 - T_SNAP)
    return D_CUP + (t - 1.95) * 3.2
def shock_a(r): return 1.0 - ramp(r, 4.0, 12.0)

SHOTS = []
def shot(name, t0, t1, half=False):
    def deco(fn): SHOTS.append((name, t0, t1, fn, half)); return fn
    return deco

@shot('S01_snap', 0.0, 1.15)
def s01(t, f, first):
    key_world(f, t - 1.95)
    hr = hero_snap_pose(f, t, look_hand=1.0 - ramp(t, 0.7, 1.1) * 0.6)
    key_eyes(f)
    r = shock_r(t); key_shock(f, SHOCK_C, r, shock_a(r))
    key_ring(f, V(0, 0, -50), 0, 10); key_mol(f, V(0, 0, -50), 0, 0); key_glass(f, V(0, 0, -50), (1, 1, 1), 0)
    u = eio(t / 1.15)
    face = hip_face = HS + V(0, 0, 1.55)
    key_cam(f, CAMS1.lerp(CAMS1 + V(-0.10, -0.22, 0.0), u), face.lerp(hr, 0.4) + V(0, 0, -0.08), 50, 2.8)

@shot('S02_splash', 1.15, 3.58)
def s02(t, f, first):
    tau = (t - 1.95) * 0.25 if t < 1.95 else 0.0
    key_world(f, tau)
    hero_snap_pose(f, 1.15 + 0.0 * t, look_hand=0.4)
    key_eyes(f)
    if t < 1.95: r = D_CUP + (t - 1.95) * 0.35
    else: r = D_CUP + (t - 1.95) * 1.2
    key_shock(f, SHOCK_C, r, 1.0)
    u = eio((t - 1.15) / 2.43)
    a = math.radians(lerp(18, 52, u)); R = lerp(0.46, 0.38, u)
    c = SPL_O + V(0, 0, 0.07)
    key_cam(f, c + V(math.cos(a) * R, math.sin(a) * R, lerp(0.04, 0.09, u)), c, 65, 2.0)

@shot('S03_crane', 3.58, 6.00)
def s03(t, f, first):
    if first: key_world(f, 0.0)
    r = shock_r(t); key_shock(f, SHOCK_C, r, shock_a(r))
    u = eio((t - 3.58) / 2.42)
    key_ring(f, V(5.2, -3.6, 5.6), lerp(0.6, 1.25, ss((t - 3.9) / 0.7)), 10)
    h = lerp(math.pi / 2 + 0.7, -0.25, ss((t - 3.7) / 2.0))
    head = (-0.35 * ramp(t, 3.8, 4.6) + 0.25 * ramp(t, 5.0, 5.7), 0, 0.3 * math.sin((t - 3.58) * 2.2))
    stand(HERO, f, V(3.0, -2.9, 0.15), h, head=head, spine=(0.0, 0.0, 0.0))
    key_cam(f, V(9.0, -3.1, 1.1).lerp(V(12.2, -3.7, 7.6), u), V(3.0, -3.0, 1.5).lerp(V(3.0, -3.9, 3.3), u), lerp(24, 20, u))

@shot('S04_except', 6.00, 8.88)
def s04(t, f, first):
    if first: key_world(f, 0.0); key_ring(f, V(5.2, -3.6, 5.6), 1.25, 9); key_shock(f, SHOCK_C, 0, 0)
    x = 2.66
    if t < 7.1:
        ph = (t - 6.0) / 1.0 * 0.85; y = lerp(0.9, -0.35, (t - 6.0) / 1.1)
        hip = walk_pose(HERO, f, V(x, y, 0.15), -math.pi / 2, ph, head=(0, 0, 0.5 * ramp(t, 6.4, 6.9)))
    elif t < 8.2:
        u = ramp(t, 7.1, 7.35); h = lerp(-math.pi / 2, -math.pi + 0.15, u)
        hip = V(x, -0.35, 0.15 + 0.845)
        wave = math.sin((t - 7.3) * 2 * math.pi * 2.6) * ramp(t, 7.3, 7.45) * (1 - ramp(t, 7.95, 8.15))
        hr = local(hip, h, 0.03, -0.25, -0.075).lerp(local(hip, h, 0.42, -0.06 + 0.13 * wave, 0.56), ramp(t, 7.2, 7.45) * (1 - ramp(t, 7.95, 8.2)))
        stand(HERO, f, V(x, -0.35, 0.15), h, hands=(local(hip, h, 0.03, 0.25, -0.075), hr), head=(-0.08, 0, 0.12 * wave), spine=(0.08, 0, 0))
    else:
        ph = 0.85 + (t - 8.2) * 0.85; y = lerp(-0.35, -0.95, (t - 8.2) / 0.7)
        walk_pose(HERO, f, V(x, y, 0.15), -math.pi / 2, ph, head=(0, 0, 0.25))
    yc = lerp(0.6, -0.75, eio((t - 6.0) / 2.88))
    key_cam(f, V(6.3, yc - 0.2, 1.25), V(2.4, yc - 0.1, 1.15), 30, 5.6)

@shot('S05_pigeons', 8.88, 10.72)
def s05(t, f, first):
    if first: key_world(f, 0.0); key_ring(f, V(0, 0, -50), 0, 9)
    stand(HERO, f, HB, -2.2, head=(-0.4, 0, 0))
    u = eio((t - 8.88) / 1.84)
    key_cam(f, V(4.05, -1.75, 0.7).lerp(V(3.75, -3.0, 0.8), u), V(2.9, -4.3, 3.2).lerp(V(2.6, -5.2, 3.6), u), 17, 16)

P_POKE = None
@shot('S06_poke', 10.72, 13.02)
def s06(t, f, first):
    global P_POKE
    if first:
        key_world(f, 0.0)
        top = G['SPL'][0]['e'].co.copy(); P_POKE = G['SPL_ORIGIN'] + top
    base = V(2.17, -3.86, 0.15); h = math.pi + 0.45
    hip = base + V(0, 0, 0.845)
    reach = ramp(t, 10.8, 11.55)
    tap = math.exp(-((t - 11.75) / 0.06) ** 2) + math.exp(-((t - 12.15) / 0.06) ** 2)
    touch = P_POKE + V(0.035, 0.035, 0.01) + V(-0.012, -0.012, 0) * tap
    hl = local(hip, h, 0.03, 0.25, -0.075).lerp(touch, reach)
    hl = hl.lerp(touch + V(0.05, 0.05, 0.03), ramp(t, 12.5, 13.0))
    stand(HERO, f, base, h, hands=(hl, local(hip, h, 0.03, -0.25, -0.075)), spine=(0.38 * reach, 0.0, 0), head=(0.35 * reach, 0, 0.15 * reach), hipdz=-0.05 * reach)
    u = eio((t - 10.72) / 2.3)
    c = P_POKE + V(0, 0, -0.05)
    key_cam(f, c + V(0.80, -0.62, 0.10).lerp(V(0.70, -0.52, 0.08), u), c + V(0.0, 0.03, 0.02), 50, 3.2)

@shot('S07_taxi', 13.02, 14.78)
def s07(t, f, first):
    if first: key_world(f, 0.0)
    p, ps = taxi_at(0.0); R = Matrix.Rotation(ps, 3, 'Z')
    wheel = p + R @ V(-0.9, -1.4, 0.0)
    ph = (t - 13.02) * 0.85
    hx = lerp(p.x - 2.6, p.x - 6.0, (t - 13.02) / 1.76)
    walk_pose(HERO, f, V(hx, p.y + 6.5, 0.0), math.pi, ph, head=(0, 0, 0.5))
    u = eio((t - 13.02) / 1.76)
    cp = wheel + R @ V(-1.5, -1.6, 0.0) + V(0, 0, 0.22)
    key_cam(f, cp.lerp(wheel + R @ V(-1.35, -1.25, 0.0) + V(0, 0, 0.2), u), wheel + R @ V(0.3, 1.6, 0.0) + V(0, 0, 0.35), 20, 8)

@shot('S08_orbit', 14.78, 19.56)
def s08(t, f, first):
    if first: key_world(f, 0.0); key_ring(f, V(0, 0, -50), 0, 8)
    k = ramp(t, 14.8, 15.4)
    hip = HB + V(0, 0, 0.845)
    arms = (local(hip, 0.0, 0.05, 0.25, -0.075).lerp(local(hip, 0.0, 0.05, 0.55, 0.42), k),
            local(hip, 0.0, 0.05, -0.25, -0.075).lerp(local(hip, 0.0, 0.05, -0.55, 0.42), k))
    stand(HERO, f, HB, 0.0, hands=arms, head=(-0.25 * k + 0.05 * math.sin(t), 0, 0.25 * math.sin((t - 14.78) * 1.3)), spine=(-0.06 * k, 0, 0), stance=0.13)
    u = eio((t - 14.78) / 4.78)
    a = math.radians(lerp(-8, 168, u)); R = 3.1
    c = HB + V(0, 0, 1.15)
    key_cam(f, c + V(math.cos(a) * R, math.sin(a) * R, lerp(-0.2, 0.45, u)), c + V(0, 0, 0.05), 26, 5.6)

@shot('BG1_plate', 19.56, 27.26, half=True)
def bg1(t, f, first):
    if first: key_world(f, 0.0); key_ring(f, V(5.2, -3.6, 5.6), 1.25, 7)
    stand(HERO, f, HB, -2.6, head=(-0.3, 0, 0.3 * math.sin(t * 0.7)))
    u = eio((t - 19.56) / 7.7)
    key_cam(f, V(9.0, 3.5, 2.4).lerp(V(8.6, -7.5, 2.8), u), V(3.0, -1.0, 2.6).lerp(V(3.0, -5.5, 3.0), u), 24, 16)

@shot('BG2_plate', 27.26, 34.26, half=True)
def bg2(t, f, first):
    if first: key_world(f, 0.0); key_ring(f, V(0, 0, -50), 0, 6)
    stand(HERO, f, HB, -2.6, head=(-0.3, 0, 0))
    u = eio((t - 27.26) / 7.0)
    a = math.radians(lerp(70, 125, u)); R = 0.55
    c = SPL_O + V(0, 0, 0.08)
    key_cam(f, c + V(math.cos(a) * R, math.sin(a) * R, 0.12), c, 45, 2.8)

@shot('S09_pov', 34.26, 37.30)
def s09(t, f, first):
    if first: key_world(f, 0.0)
    stand(HERO, f, V(0, 0, -30), 0.0)
    u = eio((t - 34.26) / 3.04)
    eye = HB + V(-0.05, 0, 1.62) + V(0, 0.03 * math.sin(t * 1.4), 0.01 * math.sin(t * 2.1))
    key_cam(f, eye, eye + V(-3.0, 0.35 - 0.6 * u, 0.55 + 0.15 * u), 24, 16)

@shot('S09b_grope', 37.30, 38.52)
def s09b(t, f, first):
    if first: key_world(f, 0.0)
    hip = HB + V(0, 0, 0.845)
    sw = math.sin((t - 37.3) * 3.2)
    hands = (local(hip, 0.0, 0.45, 0.2 + 0.08 * sw, 0.35), local(hip, 0.0, 0.48, -0.2 + 0.08 * sw, 0.33))
    stand(HERO, f, HB, 0.0, hands=hands, head=(0.1, 0, 0.45 * sw), spine=(0.12, 0.1 * sw, 0))
    key_cam(f, HB + V(3.2, 0.05, 1.25), HB + V(0, 0, 1.0), 35, 16)

@shot('S10_step', 39.88, 41.31)
def s10(t, f, first):
    if first: key_world(f, 0.0); key_ring(f, V(0, 0, -50), 0, 4)
    h = -math.pi / 2; base = HB; hip = base + V(0, 0, 0.82)
    jit = 0.004 * math.sin(t * 61) + 0.003 * math.sin(t * 37)
    k = ramp(t, 39.95, 40.5)
    push = 0.06 * ramp(t, 40.3, 41.2)
    fw = V(math.cos(h), math.sin(h), 0); L = V(-math.sin(h), math.cos(h), 0)
    lf = base + L * 0.09 - fw * 0.18 * k + V(0, 0, 0.055)
    rf = base - L * 0.09 + fw * (0.10 + push + jit) * k + V(0, 0, 0.055 + 0.07 * k)
    hipp = hip + fw * (0.05 * k + jit) - V(0, 0, 0.03 * k)
    hands = (local(hipp, h, 0.38 * k, 0.22, 0.32 * k), local(hipp, h, 0.40 * k + jit, -0.22, 0.30 * k))
    body(HERO, f, hipp, h, ((lf, h), (rf, h)), hands, spine=(0.32 * k, 0, 0), head=(0.1 * k, 0, 0), tilt=(0.0, 0.0))
    key_cam(f, HB + V(2.7, -0.55, 0.75), HB + V(0, -0.3, 0.78), 35, 5.6)

@shot('S11_molecules', 41.31, 45.12)
def s11(t, f, first):
    if first: key_world(f, 0.0)
    h = -math.pi / 2; base = HB; hip = base + V(0, 0, 0.83)
    jit = 0.003 * math.sin(t * 57)
    hand = local(hip, h, 0.50 + 0.035 * ramp(t, 41.6, 42.6) + jit, -0.18, 0.42)
    stand(HERO, f, base, h, hands=(local(hip, h, 0.03, 0.25, -0.075), hand), spine=(0.22, 0, 0), head=(0.05, 0, 0), feet_fwd=(0.0, 0.12))
    mc = local(hip, h, 0.50 + 0.035 + 0.23, -0.18, 0.42)
    key_mol(f, mc, 1.0 * ramp(t, 41.45, 42.1) + 0.001, 3.5 * ramp(t, 41.45, 42.3) * (1 + 0.15 * math.sin(t * 9)))
    u = eio((t - 41.31) / 3.81)
    key_cam(f, hand + V(1.25, 0.45, 0.16).lerp(V(1.05, 0.15, 0.12), u), hand + V(0, -0.16, 0), 55, 2.8)

@shot('S12_glass', 45.12, 48.02)
def s12(t, f, first):
    if first: key_world(f, 0.0); key_mol(f, V(0, 0, -50), 0, 0)
    a = ramp(t, 45.2, 45.9)
    key_glass(f, HB + V(0, 0, 1.12), (1.15, 1.15, 2.25), a)
    h = 0.0; hip = HB + V(0, 0, 0.845)
    jit = 0.004 * math.sin(t * 53)
    hands = (local(hip, h, 0.12, 0.44 + jit, 0.40), local(hip, h, 0.12, -0.44 - jit, 0.40))
    stand(HERO, f, HB, h, hands=hands, head=(-0.1, 0, 0.1 * math.sin(t * 1.7)), stance=0.12)
    u = eio((t - 45.12) / 2.9)
    key_cam(f, HB + V(2.6, 0.15, 1.2).lerp(V(6.4, 0.5, 2.3), u), (HB + V(0, 0, 1.05)).lerp(HB + V(0, 0, 1.2), u), lerp(32, 28, u), 16)

@shot('S13_face', 48.02, 50.90)
def s13(t, f, first):
    if first: key_world(f, 0.0)
    key_glass(f, HB + V(0, 0, 1.12), (1.15, 1.15, 2.25), 0.6)
    h = 0.0; hip = HB + V(0, 0, 0.845)
    jit = 0.003 * math.sin(t * 61)
    hands = (local(hip, h, 0.12, 0.44 + jit, 0.40), local(hip, h, 0.12, -0.44 - jit, 0.40))
    stand(HERO, f, HB, h, hands=hands, head=(-0.05 + 0.01 * math.sin(t * 47), 0, 0.006 * math.sin(t * 33)), stance=0.12)
    key_eyes(f, lerp(1.0, 1.3, ramp(t, 49.2, 49.6)))
    u = eio((t - 48.02) / 2.88)
    key_cam(f, HB + V(2.4, 0.1, 1.35).lerp(V(0.95, 0.03, 1.62), u), HB + V(0, 0, lerp(1.25, 1.6, u)), lerp(35, 42, u), 4.0)

@shot('S14_restart', 55.62, 57.54)
def s14(t, f, first):
    tau = t - 55.62
    key_world(f, tau)
    if first: key_glass(f, V(0, 0, -50), (1, 1, 1), 0); key_eyes(f, 1.0)
    gasp = ramp(t, 55.65, 55.95) * (1 - 0.5 * ramp(t, 56.6, 57.4))
    hip = HB + V(0, 0, 0.845)
    hands = (local(hip, 0.0, 0.28 * gasp, 0.2, -0.32 * gasp - 0.075), local(hip, 0.0, 0.28 * gasp, -0.2, -0.32 * gasp - 0.075))
    stand(HERO, f, HB, 0.0, hands=hands, spine=(0.55 * gasp, 0, 0), head=(-0.3 * gasp, 0, 0), hipdz=-0.1 * gasp, stance=0.13)
    u = eio(tau / 1.92)
    key_cam(f, V(13.6, -3.4, 2.4).lerp(V(13.1, -3.7, 2.6), u), V(4.0, -3.8, 2.2), 20, 16)

@shot('S15_land', 57.54, 59.00)
def s15(t, f, first):
    tau = t - 55.62
    key_world(f, tau, spl=(t - 57.54) * 0.55)
    stand(HERO, f, HB, 0.0)
    u = eio((t - 57.54) / 1.46)
    a = math.radians(lerp(40, 58, u)); R = 0.48
    c = SPL_O + V(0, 0, 0.03)
    key_cam(f, c + V(math.cos(a) * R, math.sin(a) * R, 0.07), c + V(0, 0, -0.02), 60, 2.4)

@shot('S16_flyoff', 59.00, 60.86)
def s16(t, f, first):
    tau = t - 55.62
    key_world(f, tau, bird=(t - 59.0) * 1.05)
    stand(HERO, f, V(3.0, -2.6, 0.15), -2.2, head=(-0.5, 0, 0))
    u = eio((t - 59.0) / 1.86)
    key_cam(f, V(4.0, -1.9, 0.75), V(2.9, -4.4, 3.0).lerp(V(3.0, -6.0, 8.5), u), 17, 16)

@shot('S17_end', 60.86, 63.40)
def s17(t, f, first):
    tau = t - 55.62
    key_world(f, tau, bird=8.0, spl=2.0)
    hip = HS + V(0, 0, 0.845)
    # looks at his own hand, then at the camera, then raises it for another snap (matches S01 frame 0)
    lookh = ramp(t, 61.0, 61.5) * (1 - ramp(t, 62.0, 62.4))
    up1 = ramp(t, 60.95, 61.5) * (1 - ramp(t, 61.9, 62.3))
    hr_look = local(hip, H_SNAP, 0.32, -0.12, 0.30)
    hr_end = snap_hand(hip, H_SNAP, -0.4 + 0.75 * ramp(t, 62.45, 63.38))
    hr = local(hip, H_SNAP, 0.03, -0.25, -0.075).lerp(hr_look, up1)
    hr = hr.lerp(hr_end, ramp(t, 62.3, 62.6)) if t > 62.3 else hr
    head = (lerp(0.05, 0.3, lookh) + 0.02 * math.sin(t * 2), 0, lerp(0.0, -0.35, lookh))
    head = (lerp(head[0], -0.12 + 0.02 * math.sin(t * 2), ramp(t, 62.45, 63.38)), 0, lerp(head[2], -0.35 * 1.0, ramp(t, 62.45, 63.38)))
    stand(HERO, f, HS, H_SNAP, hands=(local(hip, H_SNAP, 0.03, 0.25, -0.075), hr), spine=(0.02, -0.08, 0), head=head)
    u = eio((t - 60.86) / 2.54)
    face = HS + V(0, 0, 1.55)
    c0 = CAMS1 + (CAMS1 - face).normalized() * 1.3 + V(0, 0, 0.1)
    hr0 = snap_hand(hip, H_SNAP, 0.0)
    key_cam(f, c0.lerp(CAMS1, u), (HS + V(0, 0, 1.2)).lerp(face.lerp(hr0, 0.4) + V(0, 0, -0.08), u), lerp(38, 50, u), lerp(5.6, 2.8, u))

def build(names=None):
    for name, t0, t1, fn, half in SHOTS:
        if names and name not in names: continue
        f0, f1 = F(t0), F(t1) - 1
        for f in range(f0, f1 + 1):
            fn((f - 1) / FPS, f, f == f0)
    prefs.keyframe_new_interpolation_type = 'BEZIER'
    ids = list(D.objects) + list(D.metaballs) + list(D.curves) + list(D.cameras) + [m.node_tree for m in D.materials if m.node_tree]
    n = 0
    for idb in ids:
        ad = idb.animation_data
        if not ad or not ad.action: continue
        for fc in G['_fcurves'](ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'; n += 1
    print('constant keys', n)
    sc.frame_start, sc.frame_end = 1, F(63.40)
    return [(n, F(a), F(b) - 1, half) for n, a, b, _, half in SHOTS]
