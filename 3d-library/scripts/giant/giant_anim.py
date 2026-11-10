"""Giant Short shots. Hero rig scaled 100x at the origin, so every pose is written in 'hero space' (world metres / 100)."""
import bpy, math, json
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
exec(open(TEX + r"\giant_set_v3.py", encoding='utf-8').read(), {'__name__': 'gset'})
exec(open(TEX + r"\wf_common_v2.py", encoding='utf-8').read(), globals())
TJ = json.load(open(TEX + r"\giant_timing_v1.json"))
S = [s['start'] for s in TJ['scenes']]; END = TJ['duration']
def wt(word, after=0.0):
    for w in TJ['words']:
        if w['start'] >= after - 0.01 and w['word'].lower().strip('.,?!:') == word: return w['start']
    return after
K = 100.0
def W(p): return V(p[0] * K, p[1] * K, p[2] * K)        # hero space -> world
SL = D.objects['G_Slab']; CU = D.objects['G_Cube']; SK = D.objects['G_SkinSlab']; HT = D.objects['G_HeatCube']
for o in (SL, CU, SK, HT):
    if o.animation_data: o.animation_data_clear()
LAB0 = V(0.0, 50000.0, 0.0)
H = -math.pi / 2                                        # facing -Y (down the street towards the taxi)
fw, lf = frame_vecs(H)
LFOOT = V(0.06, 0.42, 0.055)                             # planted foot (hero space)
RF_REST = V(0.11, 0.42, 0.055)
RF_LAND = V(0.10, 0.08, 0.055)
def rfoot(t):
    """right foot: loop cycle. S10: lifts from rest, swings forward/up; S1: comes down and lands at RF_LAND at T_LAND"""
    T_LAND = 1.1
    if t < T_LAND + 0.01:                                # frame 0 -> landing (continues the S10 swing)
        u = ss(t / T_LAND) * 0.6 + (t / T_LAND) * 0.4
        p0 = V(0.10, 0.22, 0.38); return p0.lerp(RF_LAND, u)
    if t < S[9] + 0.25: return RF_LAND
    return None
def stride_pose(f, rf, lean=0.12, head=(0.0, 0, 0), neck=(0, 0, 0), arms=0.0):
    mid = (LFOOT + V(rf.x, rf.y, 0.055)) * 0.5
    span = abs(LFOOT.y - rf.y)
    C = V(mid.x, mid.y, 0.86 - 0.18 * span + 0.25 * max(0.0, rf.z - 0.055) * 0.3)
    R = Rm(pitch=lean, yaw=H + math.pi / 2)
    hands = (C + lf * 0.25 + fw * (0.1 * arms) + V(0, 0, -0.08), C - lf * 0.25 - fw * (0.1 * arms) + V(0, 0, -0.08))
    pose_w(f, C, R, hands, (LFOOT, rf), neck=neck, head=head, foot_R=Rm(yaw=H + math.pi / 2)); return C
def stand_rest(f, t, look_up=0.0, hands=None, wide=1.0):
    C = V((LFOOT.x + RF_REST.x) / 2, 0.42, 0.845)
    if hands is None: hands = (C + lf * 0.25 + V(0, 0, -0.075), C - lf * 0.25 + V(0, 0, -0.075))
    pose_w(f, C, Rm(yaw=H + math.pi / 2), hands, (LFOOT, RF_REST), neck=(-0.2 * look_up, 0, 0), head=(-0.25 * look_up, 0, 0.05 * math.sin(t)),
           foot_R=Rm(yaw=H + math.pi / 2))
    eyes(f, blink(t, 3.4), wide); return C
def hero_city(f): key_hero_xform(f, (0, 0, 0), K)
def lab_hide_all(f):
    for o in (SL, CU, SK, HT): hide(o, f, far=LAB0 + V(0, 0, -100))
CAM0 = V(7.6, -10.0, 1.3); TGT0 = V(9.5, 16.0, 17.0)
CITY = ['G_CITY', 'BLD_Row', 'Street', 'Props', 'Cars', 'FZ']
LABS = ['G_LAB']

@shot('G01_hook', 0.0, S[1], CITY, 'W_CITY', samples=16)
def g01(t, f):
    hero_city(f); lab_hide_all(f)
    rf = rfoot(t); stride_pose(f, rf, lean=0.1, head=(0.35, 0, 0)); eyes(f, 1.0, 1.0)
    if t < 1.5:                                          # 1a: street level by the car, the giant foot coming down
        u = eio(t / 1.5); key_cam(f, CAM0 + V(0, 0.8 * u, 0), TGT0, 18, 11.0)
    else:                                                # 1b: from his heel, looking up the whole body to the face
        u = eio((t - 1.5) / (S[1] - 1.5))
        key_cam(f, V(9.5, 70, 1.3), V(8, 38, lerp(70, 115, u)), 16, 11.0)

@shot('G02_weight', S[1], S[2], CITY, 'W_CITY', samples=16)
def g02(t, f):
    hero_city(f); lab_hide_all(f); stand_rest(f, t, look_up=-0.3)
    u = eio((t - S[1]) / (S[2] - S[1]))                    # aerial three-quarter, slow orbit (plate for the Titanic scale after 4.6 s)
    a = math.radians(lerp(20, 55, u)); r = 330
    cp = V(8 + r * math.cos(a), 42 + r * math.sin(a) * -1, lerp(150, 175, u))
    key_cam(f, cp, V(8, 40, 85), 30, 16.0)

@shot('G03_bones', S[2], S[3], LABS, 'W_LAB', samples=16)
def g03(t, f):
    lab_hide_all(f)
    s = 1.0 + 2.2 * ramp(t, S[2] + 0.6, S[3] - 0.6)
    show(SL, f, LAB0 + V(-7, 0, 0), (2.0 * s, 2.0 * s, 0.25))
    show(CU, f, LAB0 + V(7, 0, 0), (2.0 * s, 2.0 * s, 2.0 * s))
    u = eio((t - S[2]) / (S[3] - S[2]))
    key_cam(f, LAB0 + V(0, lerp(-34, -40, u), lerp(9, 12, u)), LAB0 + V(0, 0, lerp(2.0, 3.6, u)), 30, 16.0)
    track('slab', f, LAB0 + V(-7, 0, 0.25)); track('cube', f, LAB0 + V(7, 0, 4.0 * s))

T_SNAP = wt('snaps', S[3])
SHIN = V(RF_LAND.x, RF_LAND.y + 0.03, 0.27)
@shot('G04_step', S[3], S[4], CITY, 'W_CITY', samples=16)
def g04(t, f):
    hero_city(f); lab_hide_all(f)
    # lifts the back (left) leg for the step; the planted right shin gives way at T_SNAP
    k = ramp(t, S[3] + 0.2, T_SNAP - 0.15)
    bk = ramp(t, T_SNAP, T_SNAP + 0.45)
    lfoot = LFOOT.lerp(V(0.06, 0.25, 0.35), k) if bk < 0.5 else V(0.06, 0.25, 0.35).lerp(V(0.07, 0.30, 0.06), ramp(t, T_SNAP + 0.1, T_SNAP + 0.6))
    rf = RF_LAND
    mid = (lfoot + rf) * 0.5
    C = V(mid.x, (lfoot.y + rf.y) / 2, 0.78 - 0.32 * bk)
    R = Rm(pitch=0.1 + 0.2 * bk, roll=0.12 * bk, yaw=H + math.pi / 2)
    hands = (C + lf * (0.25 + 0.2 * bk) + V(0, 0, 0.1 * bk), C - lf * (0.25 + 0.2 * bk) + V(0, 0, 0.1 * bk))
    pose_w(f, C, R, hands, (V(lfoot.x, lfoot.y, max(0.055, lfoot.z)), rf), head=(0.2 * bk, 0, 0), foot_R=Rm(yaw=H + math.pi / 2))
    eyes(f, blink(t, 3.1), 1.0 + 0.4 * bk)
    if t < T_SNAP - 0.4:                                 # 4a: low side view, the leg lifts over the rooftops
        u = eio((t - S[3]) / (T_SNAP - 0.4 - S[3]))
        key_cam(f, V(lerp(60, 70, u), -240, 55), V(8, 25, 55), 24, 16.0)
    elif t < T_SNAP + 1.0:                               # 4b: the planted shin (crack overlay in the edit)
        sh = W(SHIN)
        key_cam(f, sh + V(70, -55, 12), sh, 35, 11.0); track('shin', f, sh)
    else:                                                # 4c: face close-up, eyes wide
        face = W(C + R @ V(0, 0, 0.71))
        key_cam(f, face + V(48, -45, 18), face, 35, 8.0)

T_FALL0 = S[4] + 0.2; T_HIT = S[5] - 0.45
def fall_theta(t): return (math.pi / 2 - 0.04) * cl((t - T_FALL0) / (T_HIT - T_FALL0)) ** 2.2
@shot('G05_fall', S[4], S[5], CITY, 'W_CITY', samples=16)
def g05(t, f):
    hero_city(f); lab_hide_all(f)
    th = fall_theta(t); piv = V(0.085, 0.20, 0.0)
    R = Rm(pitch=th, yaw=H + math.pi / 2); C = piv + R @ V(0, 0, 0.82)
    hands = (C + R @ V(0.55, -0.15, 0.35), C + R @ V(-0.55, -0.15, 0.35))
    feet = (piv + lf * 0.06 + V(0, 0, 0.055), piv - lf * 0.06 + V(0, 0, 0.055))
    pose_w(f, C, R, hands, feet, head=(-0.3, 0, 0), foot_R=Rm(yaw=H + math.pi / 2))
    eyes(f, 1.0, 1.35)
    head = W(C + R @ V(0, 0, 0.71))
    if t < S[4] + 1.9:                                   # 5a: wide side view, he topples like a tree
        u = eio((t - S[4]) / 1.9); key_cam(f, V(300, lerp(-70, -50, u), 150), V(8, -40, 60), 24, 16.0)
    else:                                                # 5b: camera rides down beside his head
        key_cam(f, head + V(70, 45, 20), head, 28, 11.0)

LIE_C = V(0.085, 0.20, 0.0) + Rm(pitch=math.pi / 2 - 0.04, yaw=H + math.pi / 2) @ V(0, 0, 0.82)
def lying(f, t, eyes_open=1.0):
    R = Rm(pitch=math.pi / 2 - 0.04, yaw=H + math.pi / 2); piv = V(0.085, 0.20, 0.0)
    pose_w(f, LIE_C, R, (LIE_C + R @ V(0.55, -0.15, 0.35), LIE_C + R @ V(-0.55, -0.15, 0.35)),
           (piv + lf * 0.06 + V(0, 0, 0.055), piv - lf * 0.06 + V(0, 0, 0.055)), head=(-0.3, 0, 0), foot_R=Rm(yaw=H + math.pi / 2))
    eyes(f, eyes_open, 1.0)
    return W(LIE_C + R @ V(0, 0, 0.71))
@shot('G06_heart', S[5], S[7], CITY, 'W_CITY', samples=16)
def g06(t, f):
    hero_city(f); lab_hide_all(f)
    close = lerp(1.0, 0.1, ramp(t, S[6] + 0.1, S[7] - 0.25)) if t >= S[6] else 1.0
    head = lying(f, t, close if t >= S[6] else blink(t, 2.6))
    if t < S[6]:                                         # 6 plate: high aerial of him lying across the street (blood-column neon on top)
        u = eio((t - S[5]) / (S[6] - S[5])); key_cam(f, V(lerp(-160, -140, u), -40, 260), V(8, -50, 0), 26, 16.0)
    else:                                                # 7: his face from above, eyes closing (fade to black in the edit)
        key_cam(f, head + V(0, -25, 80), head, 26, 8.0)

@shot('G08_heat', S[7], S[8], CITY + LABS, 'W_CITY', samples=16)
def g08(t, f):
    T_LAB = S[7] + 2.75
    if t < T_LAB:                                        # 8a: thermal aerial (look added in the edit)
        hero_city(f); lab_hide_all(f); lying(f, t, 0.15)
        u = eio((t - S[7]) / 2.75); key_cam(f, V(lerp(200, 170, u), lerp(-180, -150, u), 230), V(8, -50, 10), 24, 16.0)
    else:                                                # 8b: lab, heat cube (x1,000,000) vs skin slab (x10,000)
        key_hero_xform(f, (0, 0, -5000), K); lab_hide_all(f)
        s = 1.0 + 2.2 * ramp(t, T_LAB + 0.5, S[8] - 0.5)
        show(SK, f, LAB0 + V(-7, 0, 0), (2.0 * s, 2.0 * s, 0.25)); show(HT, f, LAB0 + V(7, 0, 0), (2.0 * s, 2.0 * s, 2.0 * s))
        u = eio((t - T_LAB) / (S[8] - T_LAB))
        key_cam(f, LAB0 + V(0, lerp(-34, -40, u), lerp(9, 12, u)), LAB0 + V(0, 0, lerp(2.0, 3.6, u)), 30, 16.0)
        track('skin', f, LAB0 + V(-7, 0, 0.25)); track('heat', f, LAB0 + V(7, 0, 4.0 * s))

@shot('G09_shout', S[8], S[9], CITY, 'W_CITY', samples=16)
def g09(t, f):
    hero_city(f); lab_hide_all(f)
    sh = ramp(t, S[8] + 0.1, S[8] + 0.4) * (1 - ramp(t, S[9] - 0.5, S[9] - 0.1))
    C = V((LFOOT.x + RF_REST.x) / 2, 0.42, 0.845)
    hands = None if sh < 0.05 else (C + fw * 0.18 + lf * 0.08 + V(0, 0, 0.66 * sh), C + fw * 0.18 - lf * 0.08 + V(0, 0, 0.66 * sh))
    stand_rest(f, t, look_up=0.3 * sh, hands=hands, wide=1.0 + 0.2 * sh)
    u = eio((t - S[8]) / (S[9] - S[8]))                  # street level looking up at him shouting (plate for the hearing chart later)
    key_cam(f, V(lerp(14, 18, u), -55, 1.4), V(8, 42, lerp(140, 150, u)), 17, 16.0)

@shot('G10_loop', S[9], END, CITY, 'W_CITY', samples=16)
def g10(t, f):
    hero_city(f); lab_hide_all(f)
    t_up = S[9] + 0.25; t_top = S[9] + 1.6
    if t < t_up: rf = RF_REST
    elif t < t_top: rf = RF_REST.lerp(V(0.10, 0.30, 0.70), eio((t - t_up) / (t_top - t_up)))
    else:                                                # swing forward and start down; at END reaches the frame-0 foot position
        u = eio((t - t_top) / (END - t_top)); rf = V(0.10, 0.30, 0.70).lerp(V(0.10, 0.22, 0.38), u)
    stride_pose(f, rf, lean=0.1, head=(0.35 * ramp(t, t_up, END), 0, 0)); eyes(f, blink(t, 3.0), 1.0)
    if t < t_top:                                        # 10a: street level, the foot lifting above the rooftops
        u = eio((t - S[9]) / (t_top - S[9])); key_cam(f, V(7.0, -8.0, 1.3), V(9, 25, lerp(25, 45, u)), 18, 11.0)
    else:                                                # 10b: settles onto the exact frame-0 camera
        u = eio((t - t_top) / (END - t_top - 0.2))
        key_cam(f, V(7.0, -8.0, 1.3).lerp(CAM0, u), V(9, 25, 45).lerp(TGT0, u), 18, 11.0)
