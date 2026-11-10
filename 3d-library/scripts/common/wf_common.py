"""Shared helpers for the What-If stickman Shorts: timing, posing (in the rig's own space), eyes, camera keys, build."""
import bpy, math, json, random
from mathutils import Vector, Matrix, Euler
sc = bpy.context.scene; D = bpy.data
def V(*a): return Vector(a)
FPS = 30
def F(t): return int(round(t * FPS)) + 1
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = cl(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def ramp(t, a, b): return ss((t - a) / (b - a)) if b != a else (1.0 if t >= a else 0.0)
def eio(u): u = cl(u); return 0.5 - 0.5 * math.cos(math.pi * u)
HERO = D.objects['StickRig']; P = HERO.pose.bones
cam = D.objects['Cam']; tgt = D.objects['CamTgt']; sc.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.sensor_fit = 'AUTO'; cam.data.sensor_width = 36
for pb in P: pb.rotation_mode = 'QUATERNION' if pb.name in ('hips', 'IK_foot.L', 'IK_foot.R') else 'XYZ'
EYES = [D.objects['Eye.L'], D.objects['Eye.R']]; EYE0 = [(0.03, 0.02, 0.052)] * 2
for o in [HERO, cam, tgt, cam.data] + EYES:
    if o.animation_data: o.animation_data_clear()
for e in EYES: e.scale = (0.03, 0.02, 0.052)
# reset the hero material (earlier videos keyed heat/age colours on it)
WHITE = D.materials.get('StickWhite')
if WHITE and WHITE.node_tree:
    if WHITE.node_tree.animation_data: WHITE.node_tree.animation_data_clear()
    _wb = next((n for n in WHITE.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if _wb:
        _wb.inputs['Base Color'].default_value = (1, 1, 1, 1); _wb.inputs['Emission Color'].default_value = (1, 1, 1, 1)
        _wb.inputs['Emission Strength'].default_value = 0.42
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
    LASTCAM['v'] = (tuple(cp), tuple(tp), lens)
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


def hide(o, f, far=(0, 0, -5000)):
    o.location = far; o.scale = (0.001,) * 3; o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
def show(o, f, loc, scale=(1, 1, 1), rot=None):
    o.location = loc; o.scale = scale; o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
def key_hero_xform(f, loc=(0, 0, 0), scale=1.0, rot_z=0.0):
    HERO.location = loc; HERO.scale = (scale,) * 3; HERO.rotation_euler = (0, 0, rot_z)
    HERO.keyframe_insert('location', frame=f); HERO.keyframe_insert('scale', frame=f); HERO.keyframe_insert('rotation_euler', frame=f)
SHOTS = []
def shot(name, t0, t1, sets, world, samples=32, rt=False, pct=100):
    def deco(fn): SHOTS.append(dict(name=name, t0=t0, t1=t1, fn=fn, sets=sets, world=world, samples=samples, rt=rt, pct=pct)); return fn
    return deco
TRACK = {}
LASTCAM = {}
def track(name, f, p):
    """screen position (0..1 from top-left) of world point p for the camera keyed at frame f (call after key_cam)"""
    cp, tp, lens = LASTCAM['v']
    fw = (V(*tp) - V(*cp)).normalized(); rt = fw.cross(V(0, 0, 1)).normalized(); up = rt.cross(fw)
    d = V(*p) - V(*cp); z = d.dot(fw)
    if z <= 0.01: TRACK.setdefault(name, {})[f] = None; return
    u = 0.5 + (d.dot(rt) / z) / (2 * 18 * (1080 / 1920) / lens); v = 0.5 - (d.dot(up) / z) / (2 * 18 / lens)
    TRACK.setdefault(name, {})[f] = (round(u, 4), round(v, 4))
def _fcurves(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for lay in act.layers:
            for strip in lay.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out
def build(end, key, names=None, track_out=None):
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
    sc.frame_start, sc.frame_end = 1, F(end) - 1
    sc[key] = json.dumps([dict(name=s['name'], a=F(s['t0']), b=F(s['t1']) - 1, sets=s['sets'], world=s['world'], samples=s['samples'], rt=s['rt'], pct=s['pct']) for s in SHOTS])
    if track_out and TRACK: open(track_out, 'w').write(json.dumps(TRACK))
    print('constant keys', n)
    return [(s['name'], F(s['t0']), F(s['t1']) - 1) for s in SHOTS]
