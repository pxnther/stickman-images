"""Super-speed Short: shots keyed on one global timeline. Reuses the Freeze Time library (fz_anim) + ss_set props."""
import bpy, math, json, random
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene; D = bpy.data
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
A = {'__name__': 'fzanim'}
exec(open(TEX + r"\fz_anim_v5.py", encoding='utf-8').read(), A)
S = {'__name__': 'ssset'}
exec(open(TEX + r"\ss_set_v2.py", encoding='utf-8').read(), S)
T = json.load(open(TEX + r"\ss_timing_v1.json"))
SC = [(s['start'], s['end']) for s in T['scenes']]          # scene 1..17 -> SC[0..16]
END = T['duration']
V = A['V']; F = A['F']; ss = A['ss']; lerp = A['lerp']; ramp = A['ramp']; eio = A['eio']; cl = A['cl']
HERO = A['HERO']; stand = A['stand']; walk_pose = A['walk_pose']; body = A['body']; local = A['local']
key_cam = A['key_cam']; key_world = A['key_world']; key_eyes = A['key_eyes']; PEDS = A['PEDS']
cam = A['cam']
# hide the Freeze Time holograms for this video (keyed once at frame 1)
A['key_shock'](1, V(0, 0, -50), 0, 0); A['key_ring'](1, V(0, 0, -50), 0, 10); A['key_mol'](1, V(0, 0, -50), 0, 0); A['key_glass'](1, V(0, 0, -50), (1, 1, 1), 0)
WHITE = D.materials['StickWhite']; WB = next(n for n in WHITE.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
def key_hero_mat(f, heat=0.0, age=0.0):
    c_heat = (1.0, 0.22, 0.03); c_age = (0.62, 0.60, 0.56)
    base = tuple(lerp(lerp(1.0, c, heat), a, age) for c, a in zip(c_heat, c_age))
    WB.inputs['Base Color'].default_value = (*base, 1)
    WB.inputs['Emission Color'].default_value = (*tuple(lerp(lerp(1.0, c, heat), a, age) for c, a in zip(c_heat, c_age)), 1)
    WB.inputs['Emission Strength'].default_value = lerp(lerp(0.42, 2.2, heat), 0.08, age)
    WB.inputs['Base Color'].keyframe_insert('default_value', frame=f); WB.inputs['Emission Color'].keyframe_insert('default_value', frame=f)
    WB.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
CONE = S['CONE']; SHOCK_MUL = S['SHOCK_MUL']
def key_cone(f, pos, a, length=1.0):
    CONE.location = pos; CONE.scale = (1, length, 1) if a > 0.001 else (0.001,) * 3; SHOCK_MUL.inputs[1].default_value = a
    CONE.keyframe_insert('location', frame=f); CONE.keyframe_insert('scale', frame=f); SHOCK_MUL.inputs[1].keyframe_insert('default_value', frame=f)
SHARDS = S['SHARDS']; PANES = S['PANES']
def key_shards(f, burst):
    """burst: list of burst times per pane (video seconds), t = current time"""
    t = (f - 1) / 30
    for d in SHARDS:
        w = t - burst[d['pane']]
        p, r = S['shard_state'](d, w)
        d['o'].location = p; d['o'].rotation_euler = r; d['o'].scale = (1, 1, 1) if w > -0.04 else (0.001,) * 3
        d['o'].keyframe_insert('location', frame=f); d['o'].keyframe_insert('rotation_euler', frame=f); d['o'].keyframe_insert('scale', frame=f)
FOOD = S['FOOD']
def key_food(f, k):
    n = len(FOOD)
    for d in FOOD:
        g = ss((k * n - d['order']) / 2.0)
        d['o'].scale = (max(g, 0.001),) * 3; d['o'].location = d['p'] + V(0, 0, 0.25 * (1 - g))
        d['o'].keyframe_insert('scale', frame=f); d['o'].keyframe_insert('location', frame=f)
BEARD = S['BEARD']; WEBS = S['WEBS']; SPR = S['SPR']; SPRAY = S['SPRAY']
BEARD.parent = None
def key_age(f, k, pos=None):
    BEARD.location = pos if pos is not None else V(0, 0, -50); BEARD.rotation_euler = (math.pi, 0, 0)
    BEARD.scale = (max(k, 0.001),) * 3; BEARD.keyframe_insert('location', frame=f); BEARD.keyframe_insert('scale', frame=f); BEARD.keyframe_insert('rotation_euler', frame=f)
    WEBS.scale = (max(k, 0.001),) * 3; WEBS.keyframe_insert('scale', frame=f)
def key_spray(f, x_hero, y_hero, t_run):
    SPRAY.location = (0, 0, 0); SPRAY.keyframe_insert('location', frame=f)
    for d in SPR:
        w = t_run - d['k'] * 0.03
        e = d['e']
        if w <= 0 or w > 0.75: e.co = (x_hero, y_hero, -1); e.radius = 0.001
        else:
            y0 = y_hero + 14.0 * (d['k'] * 0.03)   # emitted where his feet were
            vv = V(d['v'].x * 0.5, d['v'].y * 0.5, d['v'].z * 0.45)
            p = V(x_hero, y0, 0.0) + vv * w + V(0, 0, -9.81 * 0.5 * w * w)
            e.co = p if p.z > -0.1 else V(p.x, p.y, -0.1); e.radius = d['r'] * min(1, w / 0.05) * (1 - cl((w - 0.45) / 0.3))
        e.keyframe_insert('co', frame=f); e.keyframe_insert('radius', frame=f)
def sprint(f, base, h, ph, lean=0.45, arms=1.4):
    """fast run: big stride, deep lean"""
    c = math.cos(2 * math.pi * ph); s_ = math.sin(2 * math.pi * ph)
    b = V(*base); L = V(-math.sin(h), math.cos(h), 0); fw = V(math.cos(h), math.sin(h), 0)
    lf = b + fw * (0.55 * c) + L * 0.08 + V(0, 0, 0.055 + 0.28 * max(0.0, -s_))
    rf = b - fw * (0.55 * c) - L * 0.08 + V(0, 0, 0.055 + 0.28 * max(0.0, s_))
    hip = b + V(0, 0, 0.74 + 0.05 * abs(s_)) + fw * 0.12
    hands = (local(hip, h, 0.10 - 0.32 * c * arms / 1.4, 0.22, 0.10 + 0.14 * abs(c)), local(hip, h, 0.10 + 0.32 * c * arms / 1.4, -0.22, 0.10 + 0.14 * abs(c)))
    body(HERO, f, hip, h, ((lf, h), (rf, h)), hands, spine=(lean, 0.1 * c, 0), head=(-lean * 0.7, 0, 0))
    return hip
JOBS = []
def shot(name, a, b, kind='street', samples=32, rt=False, pct=100):
    def deco(fn): JOBS.append(dict(name=name, t0=a, t1=b, fn=fn, kind=kind, samples=samples, rt=rt, pct=pct)); return fn
    return deco
def sc_(i): return SC[i - 1]
ROAD_X = 3.9
PANE_Y = [(y0 + y1) / 2 for y0, y1 in PANES]

# 1: hook sprint (full colour from frame 0)
a, b = 0.0, sc_(2)[0]
HOOK_Y0, HOOK_V = 14.0, -9.5
def burst_times(t0, y0, vy):
    return [t0 + (py - y0) / vy + 0.05 for py in PANE_Y]
BURST1 = burst_times(a, HOOK_Y0, HOOK_V)
@shot('S01_hook', a, b)
def s01(t, f, first, a=a, b=b):
    if first: key_world(f, 0.0)
    y = HOOK_Y0 + HOOK_V * (t - 0.0)
    sprint(f, V(ROAD_X, y, 0.0), -math.pi / 2, t * 2.6); key_eyes(f, 1.15); key_hero_mat(f, 0.15)
    key_cone(f, V(ROAD_X, y, 0.0), 0.6, 1.0)
    key_shards(f, BURST1)
    key_cam(f, V(ROAD_X + 2.7, y - 1.6, 0.55), V(ROAD_X - 0.6, y - 0.4, 1.05), 22, 8)
# 2: world almost stops
a, b = sc_(2)
@shot('S02_stops', a, b)
def s02(t, f, first, a=a, b=b):
    key_world(f, 0.02 * (t - a))
    if first: key_cone(f, V(0, 0, -50), 0); key_shards(f, [999] * 4); key_hero_mat(f, 0.0); key_food(f, 0); key_age(f, 0)
    u = eio((t - a) / (b - a))
    stand(HERO, f, V(2.9, -2.7, 0.15), lerp(math.pi / 2 + 0.8, -0.2, u), head=(-0.3 * u, 0, 0.25 * math.sin((t - a) * 2)))
    key_eyes(f, 1.15)
    key_cam(f, V(6.4, -3.6, 1.0).lerp(V(7.6, -4.4, 2.6), u), V(2.9, -3.2, 1.5).lerp(V(2.6, -4.2, 2.8), u), 22, 8)
# 3: light still reaches you (wave at a frozen pedestrian)
a, b = sc_(3)
@shot('S03_see', a, b)
def s03(t, f, first, a=a, b=b):
    key_world(f, 0.02 * (t - SC[1][0]))
    x = 2.66; h = -math.pi + 0.15; hip = V(x, -0.35, 0.15 + 0.845)
    wave = math.sin((t - a) * 2 * math.pi * 2.4) * ramp(t, a + 0.2, a + 0.4)
    hr = local(hip, h, 0.03, -0.25, -0.075).lerp(local(hip, h, 0.42, -0.06 + 0.13 * wave, 0.56), ramp(t, a + 0.1, a + 0.4))
    stand(HERO, f, V(x, -0.35, 0.15), h, hands=(local(hip, h, 0.03, 0.25, -0.075), hr), head=(-0.08, 0, 0.12 * wave), spine=(0.08, 0, 0))
    key_cam(f, V(6.0, -0.6, 1.3), V(2.35, -0.45, 1.25), 30, 5.6)
# 4: take a step (close on the foot)
a, b = sc_(4)
@shot('S04_step', a, b)
def s04(t, f, first, a=a, b=b):
    u = ramp(t, a + 0.15, b - 0.05)
    base = V(5.6, 6.0, 0.0); h = -math.pi / 2
    fw = V(0, -1, 0); L = V(1, 0, 0)
    lf = base + L * 0.09 + V(0, 0, 0.055); rf = base - L * 0.09 + fw * 0.35 * u + V(0, 0, 0.055 + 0.18 * math.sin(math.pi * u))
    hip = base + V(0, 0, 0.82) + fw * 0.08 * u
    body(HERO, f, hip, h, ((lf, h), (rf, h)), (local(hip, h, 0.1, 0.24, -0.05), local(hip, h, -0.1, -0.24, -0.05)), spine=(0.2 * u, 0, 0))
    key_cam(f, base + V(1.1, -0.9, 0.22), base + V(0, -0.2, 0.25), 32, 2.8)
# 5-6: accelerate, cone forms
a, b = sc_(5)[0], sc_(6)[1]
@shot('S05_accel', a, b)
def s05(t, f, first, a=a, b=b):
    u = (t - a) / (b - a)
    y = 3.0 - 2.0 * (t - a) - 5.0 * (t - a) ** 2 * 0.3
    sprint(f, V(ROAD_X, y, 0.0), -math.pi / 2, (t - a) * lerp(1.4, 3.0, u), lean=lerp(0.25, 0.5, u))
    key_cone(f, V(ROAD_X, y, 0.0), 0.95 * ramp(t, sc_(6)[0] - 0.2, sc_(6)[0] + 0.3), lerp(0.5, 1.0, u))
    key_cam(f, V(ROAD_X + 2.8, y - 1.0, 1.0), V(ROAD_X, y - 0.3, 0.95), 24, 8)
# 7: the air hits you like a wall (slow motion, from ahead)
a, b = sc_(7)
@shot('S07_wall', a, b)
def s07(t, f, first, a=a, b=b):
    y = -8.0 - 0.6 * (t - a)
    hip = V(ROAD_X, y, 0.78); h = -math.pi / 2
    jit = 0.01 * math.sin(t * 40)
    hands = (local(hip, h, 0.42, 0.25, 0.42 + jit), local(hip, h, 0.42, -0.25, 0.42 - jit))
    feet = ((V(ROAD_X + 0.1, y + 0.45, 0.055), h), (V(ROAD_X - 0.1, y - 0.25, 0.1), h))
    body(HERO, f, hip, h, feet, hands, spine=(0.65, 0, 0), head=(-0.5, 0, 0.04 * math.sin(t * 23)))
    key_cone(f, V(ROAD_X, y, 0.0), 1.0, 0.9)
    key_cam(f, V(ROAD_X + 1.4, y - 3.0, 1.2), V(ROAD_X, y, 1.0), 30, 5.6)
# 8: skin heats up
a, b = sc_(8)
@shot('S08_heat', a, b)
def s08(t, f, first, a=a, b=b):
    y = -9.0 - 0.5 * (t - a)
    sprint(f, V(ROAD_X, y, 0.0), -math.pi / 2, (t - a) * 0.6, lean=0.55)
    key_hero_mat(f, ramp(t, a + 0.1, b - 0.3)); key_eyes(f, 1.2)
    key_cone(f, V(ROAD_X, y, 0.0), 1.0, 1.0)
    key_cam(f, V(ROAD_X + 2.0, y - 1.8, 1.3), V(ROAD_X, y, 1.15), 35, 4.0)
# 9: sonic booms shatter the windows (wide, frontal)
a, b = sc_(9)
Y9, V9 = 9.0, -11.0
BURST9 = burst_times(a, Y9, V9)
@shot('S09_boom', a, b)
def s09(t, f, first, a=a, b=b):
    if first: key_hero_mat(f, 0.0)
    y = Y9 + V9 * (t - a)
    sprint(f, V(ROAD_X, y, 0.0), -math.pi / 2, (t - a) * 2.8)
    key_cone(f, V(ROAD_X, y, 0.0), 0.9, 1.0)
    key_shards(f, BURST9)
    key_cam(f, V(12.5, 8.0, 2.2), V(2.0, -3.0, 1.4), 18, 16)
# 10: sprint across the lake
a, b = sc_(10)
LX = -30.0
@shot('S10_lake', a, b, kind='lake', rt=True)
def s10(t, f, first, a=a, b=b):
    if first: key_shards(f, [999] * 4); key_cone(f, V(0, 0, -50), 0)
    y = 40.0 - 14.0 * (t - a)
    sprint(f, V(LX, y, -0.03), -math.pi / 2, (t - a) * 2.6)
    key_spray(f, LX, y, (t - a))
    key_cam(f, V(LX + 2.8, y - 2.4, 0.8), V(LX, y - 0.6, 0.75), 28, 8)
# 11: starving (lake shore)
a, b = sc_(11)
BP = S['BENCH_P']
@shot('S11_starving', a, b, kind='lake')
def s11(t, f, first, a=a, b=b):
    key_spray(f, LX, -500, -1)
    base = BP + V(3.0, 2.0, 0.0); h = math.pi * 0.85
    hip = base + V(0, 0, 0.8)
    k = ramp(t, a + 0.1, a + 0.5)
    hands = (hip + V(0.05, -0.12, 0.12 * k), hip + V(-0.05, -0.12, 0.08 * k))
    stand(HERO, f, base, h, hands=(local(hip, h, 0.2 * k + 0.03, 0.1 + 0.15 * (1 - k), 0.1 * k - 0.07), local(hip, h, 0.2 * k + 0.03, -0.1 - 0.15 * (1 - k), 0.05 * k - 0.07)),
          spine=(0.45 * k, 0, 0), head=(0.3 * k, 0, 0), hipdz=-0.06 * k)
    key_cam(f, base + V(math.cos(h) * 2.4 + 0.6, math.sin(h) * 2.4 + 0.3, 1.3), base + V(0, 0, 1.0), 32, 5.6)
# 12-13: the food mountain
a, b = sc_(12)[0], sc_(13)[1]
TC = S['TC']
@shot('S12_food', a, b)
def s12(t, f, first, a=a, b=b):
    if first: key_world(f, 0.0)
    u = (t - a) / (b - a)
    key_food(f, cl(u * 1.15))
    base = V(TC.x + 0.75, TC.y + 0.15, 0.15); h = math.pi; hip = base + V(0, 0, 0.845)
    chew = 0.5 + 0.5 * math.sin(t * 9)
    hands = (local(hip, h, 0.3, 0.18, 0.45 + 0.08 * chew), local(hip, h, 0.25, -0.2, 0.15 + 0.3 * (1 - chew)))
    stand(HERO, f, base, h, hands=hands, spine=(0.1, 0, 0), head=(0.1 * chew, 0, 0))
    key_cam(f, TC + V(0.2, 2.2, 0.85).lerp(V(0.15, 1.9, 1.0), eio(u)), TC + V(0.2, 0, 0.3), 28, 5.6)
# 15-17: the bench by the lake, the friend blinks, he grows old, looks at the camera
a, b = sc_(15)[0], END
FR = PEDS['FZ_ped3']
FR_EYES = [D.objects.get('FZ_ped3_Eye.L'), D.objects.get('FZ_ped3_Eye.R')]
FR_E0 = [tuple(e.scale) if e else None for e in FR_EYES]
def sit(rig, f, seat, h, hands=None, spine=(0, 0, 0), head=(0, 0, 0), hipdz=0.0):
    L = V(-math.sin(h), math.cos(h), 0); fw = V(math.cos(h), math.sin(h), 0)
    hip = seat + V(0, 0, 0.12 + hipdz)
    feet = ((seat + fw * 0.42 + L * 0.12 + V(0, 0, -0.38), h), (seat + fw * 0.42 - L * 0.12 + V(0, 0, -0.38), h))
    if hands is None: hands = (hip + fw * 0.3 + L * 0.18 + V(0, 0, 0.12), hip + fw * 0.3 - L * 0.18 + V(0, 0, 0.12))
    body(rig, f, hip, h, feet, hands, spine=spine, head=head)
@shot('S15_bench', a, b, kind='lake')
def s15(t, f, first, a=a, b=b):
    seat_z = BP.z + 0.5
    hb = -math.pi / 2 + math.pi   # benches face +y (towards the lake)
    hb = -math.pi / 2
    s1 = V(BP.x + 0.45, BP.y + 0.05, seat_z); s2 = V(BP.x - 0.45, BP.y + 0.05, seat_z)
    sit(FR, f, s2, hb, head=(0.05, 0, 0.3))
    blink = ramp(t, sc_(16)[0] + 0.1, sc_(16)[0] + 0.9) * (1 - ramp(t, sc_(16)[1] - 0.5, sc_(16)[1]))
    for e, s0 in zip(FR_EYES, FR_E0):
        if e: e.scale = (s0[0], s0[1], s0[2] * max(0.1, 1 - blink)); e.keyframe_insert('scale', frame=f)
    age = ramp(t, sc_(16)[0] + 0.3, sc_(16)[1] - 0.2)
    look = ramp(t, sc_(17)[0], sc_(17)[0] + 0.5)
    sit(HERO, f, s1, hb, spine=(0.45 * age, 0, 0), head=(0.25 * age - 0.15 * look, 0, -0.45 * look), hipdz=-0.03 * age)
    hipw = s1 + V(0, 0, 0.12 - 0.03 * age); fwv = V(math.cos(hb), math.sin(hb), 0)
    key_hero_mat(f, 0.0, age); key_age(f, age, hipw + fwv * (0.16 + 0.22 * age) + V(0, 0, 0.62 - 0.12 * age)); key_eyes(f, lerp(1.0, 0.85, age))
    u = eio((t - a) / (b - a))
    key_cam(f, BP + V(lerp(-1.0, -0.4, u), lerp(-3.6, -2.6, u), lerp(1.2, 1.1, u)), BP + V(0.2, 0, 0.95), lerp(30, 38, u), 4.0)

def build():
    for j in JOBS:
        f0, f1 = F(j['t0']), F(j['t1']) - 1
        for f in range(f0, f1 + 1):
            j['fn']((f - 1) / 30, f, f == f0)
    A['prefs'].keyframe_new_interpolation_type = 'BEZIER'
    ids = list(D.objects) + list(D.metaballs) + list(D.curves) + list(D.cameras) + [m.node_tree for m in D.materials if m.node_tree]
    n = 0
    for idb in ids:
        ad = idb.animation_data
        if not ad or not ad.action: continue
        for fc in A['G']['_fcurves'](ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'; n += 1
    sc.frame_start, sc.frame_end = 1, F(END)
    sc['ss_jobs'] = json.dumps([dict(name=j['name'], a=F(j['t0']), b=F(j['t1']) - 1, kind=j['kind'], samples=j['samples'], rt=j['rt'], pct=j['pct']) for j in JOBS])
    print('constant keys', n)
    return [(j['name'], F(j['t0']), F(j['t1']) - 1) for j in JOBS]
