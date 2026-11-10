"""Teleport Short shots (hero normal scale)."""
import bpy, math, json, random
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
SETG = {'__name__': 'tset'}
SETG.update(IMGS)
exec(open(TEX + r"\tele_set_v1.py", encoding='utf-8').read(), SETG)
exec(open(TEX + r"\wf_common_v2.py", encoding='utf-8').read(), globals())
TJ = json.load(open(TEX + r"\tele_timing_v1.json"))
S = [s['start'] for s in TJ['scenes']]; END = TJ['duration']
def wt(word, after=0.0, default=None):
    for w in TJ['words']:
        if w['start'] >= after - 0.01 and w['word'].lower().strip('.,?!:') == word: return w['start']
    return default if default is not None else after
LA0 = SETG['LA0']; EV0 = SETG['EV0']
CUP = D.objects['T_Cup']; SHOCK = D.objects['T_Shock']
for o in (CUP, SHOCK):
    if o.animation_data: o.animation_data_clear()
WALL_X = 1.15; ROAD = V(8.0, 10.0, 0.0)
LONDON = ['BLD_Row', 'Street', 'Props', 'Cars', 'FZ', 'T_FX']; LA = ['T_LA', 'T_FX']; EVR = ['T_EVEREST', 'T_FX']
def hero_on(f, scale=1.0): key_hero_xform(f, (0, 0, 0), max(0.001, scale))
def pop(t, t_on, dur=0.14):                 # appear: 0 -> 1
    return ss((t - t_on) / dur)
def cup_at(f, p, rot=(0, 0, 0)):
    CUP.location = p; CUP.rotation_euler = rot; CUP.scale = (1, 1, 1)
    CUP.keyframe_insert('location', frame=f); CUP.keyframe_insert('rotation_euler', frame=f); CUP.keyframe_insert('scale', frame=f)
def cup_hide(f): hide(CUP, f)
def shock(f, t, t0, p, rmax=16.0):
    u = (t - t0) / 0.7
    if 0 <= u <= 1:
        r = 0.3 + rmax * (1 - (1 - u) ** 2.5); show(SHOCK, f, p, (r, r, r * 0.8))
    else: hide(SHOCK, f)
def hold_cup(f, C, h, sip=0.0):
    fw, lf = frame_vecs(h)
    hand = C + fw * (0.22 + 0.05 * sip) - lf * 0.12 + V(0, 0, 0.25 + 0.42 * sip)
    hands = (C + lf * 0.25 + V(0, 0, -0.075), hand)
    return hands, hand
def stand_cup(f, t, base, h, sip=0.0, look=(0, 0, 0)):
    C = V(*base) + V(0, 0, 0.845)
    hands, hand = hold_cup(f, C, h, sip)
    stand(f, base, h, hands=hands, head=look); cup_at(f, hand + V(0, 0, 0.02), (0, 0.4 * sip, 0)); eyes(f, blink(t, 3.2), 1.0)
def fling(f, t, t0, base=ROAD, cup_fly=True):
    """appears at t0 in the road and is thrown sideways (-X) into the wall, then slumps against it"""
    u = (t - t0) / 0.45; H = 0.0                        # facing +X (back to the wall it flies into)
    fw, lf = frame_vecs(H)
    x = lerp(base.x, WALL_X + 0.35, 1 - (1 - cl(u)) ** 2.2); z = 0.35 * math.sin(math.pi * cl(u))
    if u < 1.0:
        C = V(x, base.y, 0.85 + z); R = Rm(pitch=-0.25 * cl(u), roll=-0.35 * cl(u), yaw=H + math.pi / 2)
        hl, fl = flail(t * 1.5, 1.4); pose_local(f, C, R, hl, fl, head=(-0.3, 0, 0)); eyes(f, 1.0, 1.4)
    else:                                               # slumped against the wall
        k = ss((t - t0 - 0.45) / 0.5)
        b = V(WALL_X + 0.35, base.y, 0)
        sit(f, b, H, lean=lerp(-0.1, -0.35, k), hands_back=False, head=(0.25 * k, 0, 0.2), knees_up=0.3, hz=lerp(0.85, 0.22, k),
            feet=(b + fw * 0.7 + lf * 0.15 + V(0, 0, 0.05), b + fw * 0.6 - lf * 0.15 + V(0, 0, 0.05)),
            hands=(b + lf * 0.32 + V(0, 0, 0.05), b - lf * 0.32 + V(0, 0, 0.05)))
        eyes(f, lerp(1.0, 0.3, k) if t - t0 < 1.5 else blink(t, 2.0) * 0.6, 1.0)
    if cup_fly:                                         # the coffee keeps going: arcs away and lands
        w = t - t0
        if w < 0: cup_hide(f)
        else:
            p = V(lerp(base.x - 0.2, 3.8, cl(w / 0.9)), base.y + 1.6 * cl(w / 0.9), max(0.07, 1.2 + 2.2 * w - 4.9 * w * w))
            cup_at(f, p, (5.0 * min(w, 0.9), 2.0 * min(w, 0.9), 0))
    return u

@shot('T01_hook', 0.0, S[1], LONDON, 'W_LONDON')
def t01(t, f):
    hero_on(f); hide(SHOCK, f)
    fling(f, t, -0.16)                                  # frame 0: already mid-air, the cup leaving his hand
    key_cam(f, V(6.5, 5.0, 1.3), V(2.6, 10.2, 1.1), 30, 5.5)

T_LDN = wt('london', S[1], S[1] + 1.8); T_SLAM = wt('slam', S[1], S[1] + 3.5)
@shot('T02a_la', S[1], T_LDN + 0.15, LA, 'W_LA')
def t02a(t, f):                                         # LA: sipping coffee in the sun, then gone
    hide(SHOCK, f)
    g = 1 - ss((t - T_LDN) / 0.14)
    hero_on(f, max(0.001, g)); stand_cup(f, t, LA0, -math.pi / 2, sip=0.6 * ramp(t, S[1] + 0.3, S[1] + 1.0) * (1 - ramp(t, T_LDN - 0.4, T_LDN)))
    if g < 0.05: cup_hide(f)
    key_cam(f, LA0 + V(1.6, -3.2, 1.3), LA0 + V(0, 0, 1.15), 32, 4.0)

@shot('T02b_london', T_LDN + 0.15, S[2], LONDON, 'W_LONDON')
def t02b(t, f):                                         # London: appears in the road, slams sideways into the wall
    hide(SHOCK, f); t0 = T_SLAM - 0.3
    if t < t0:
        g = pop(t, T_LDN + 0.2); hero_on(f, max(0.001, g)); stand_cup(f, t, ROAD, 0.0, look=(0, 0, 0.3))
    else:
        hero_on(f); fling(f, t, t0)
    key_cam(f, V(10.5, 4.0, 1.5), V(6.0, 10.0, 1.0), 26, 7.0)

@shot('T04_fly', S[3], S[4], LONDON, 'W_LONDON')
def t04(t, f):
    hide(SHOCK, f); cup_hide(f); hero_on(f)
    u = (t - S[3]); y = -70 + 26.0 * u; C = V(8.0, y, 1.2 + 0.15 * math.sin(t * 3))
    R = Rm(pitch=1.35, roll=0.2 * math.sin(t * 2), yaw=math.pi)          # body horizontal, flying along +Y
    hl, fl = flail(t * 2.0, 1.0); pose_local(f, C, R, hl, fl, head=(-0.6, 0, 0)); eyes(f, 1.0, 1.4)
    key_cam(f, C + V(3.6, -1.2, 0.4), C + V(0, 0.8, 0), 24, 5.0)

T_CLAP = wt('thunderclap', S[4], S[4] + 3.0)
@shot('T05_clap', S[4], S[5], LONDON + ['T_FX'], 'W_LONDON')
def t05(t, f):
    cup_hide(f)
    t_on = T_CLAP - 0.25
    g = pop(t, t_on, 0.1) if t > t_on - 0.01 else 0.0
    hero_on(f, g if g > 0 else 0.001)
    stand(f, ROAD + V(0, 6, 0), math.pi / 2 + 0.6, head=(0.0, 0, 0.3 * math.sin(t * 2) * g)); eyes(f, blink(t, 2.5), 1.3)
    shock(f, t, t_on, ROAD + V(0, 6, 1.0))
    u = eio((t - S[4]) / (S[5] - S[4]))
    key_cam(f, V(lerp(12.5, 12.0, u), 8.0, 1.3), ROAD + V(0, 6, 1.6), 22, 9.0)

T_EVR = wt('everest', S[5], S[5] + 1.5)
@shot('T06_everest', S[5], S[6], EVR, 'W_EVEREST')
def t06(t, f):
    cup_hide(f); hide(SHOCK, f)
    g = pop(t, T_EVR); hero_on(f, g if g > 0 else 0.001)
    base = EV0 + V(0, 0, 0.0); h = -math.pi / 2 + 0.4; fw, lf = frame_vecs(h)
    k = ramp(t, T_EVR + 0.6, T_EVR + 1.6); sitk = ramp(t, S[6] - 1.6, S[6] - 0.4)
    breath = 0.04 * math.sin(t * 9.0) * k
    if sitk < 0.5:                                      # hands on knees, heaving for breath
        C = base + V(0, 0, 0.845 - 0.25 * k + breath)
        hands = (base + fw * 0.12 + lf * 0.12 + V(0, 0, 0.5 - 0.05 * k), base + fw * 0.12 - lf * 0.12 + V(0, 0, 0.5 - 0.05 * k)) if k > 0.2 else None
        stand(f, base, h, hands=hands, hipdz=-0.25 * k + breath, lean=0.55 * k, head=(-0.3 * k, 0, 0))
    else:                                               # slumps down into the snow
        sit(f, base, h, lean=-0.2, hands_back=True, head=(0.4, 0, 0.15))
    eyes(f, lerp(1.0, 0.35, sitk) * blink(t, 1.9), 1.0)
    if t < S[5] + 2.6:                                  # wide: the summit ridge, him tiny on top
        u = eio((t - S[5]) / 2.6); key_cam(f, base + V(lerp(9, 7.5, u), -12, lerp(-1.5, -1.0, u)), base + V(0, 0, 1.2), 24, 11.0)
    else:                                               # close: gasping
        key_cam(f, base + fw * 2.6 + lf * 1.0 + V(0, 0, 1.1), base + V(0, 0, 0.9), 35, 4.0)

T_HOP = [S[6] + 0.5, S[6] + 1.5]
@shot('T07_short', S[6], S[7], LONDON, 'W_LONDON')
def t07(t, f):
    cup_hide(f); hide(SHOCK, f)
    pos = [ROAD + V(0, -2, 0), ROAD + V(0, 2.5, 0), ROAD + V(0, 7, 0)]
    i = sum(1 for th in T_HOP if t >= th + 0.07)
    nearest = min(abs(t - th) for th in T_HOP)
    g = ss(nearest / 0.07) if nearest < 0.07 else 1.0
    hero_on(f, max(0.001, g)); stand(f, pos[i], math.pi / 2, head=(0, 0, 0.2)); eyes(f, blink(t, 3.0), 1.0)
    tg = ROAD + V(0, lerp(-2.0, 7.0, ramp(t, S[6] + 0.3, S[7] - 0.3)), 1.0); key_cam(f, tg + V(6.0, -1.5, 0.4), tg, 26, 6.2)

T_GO = wt('teleport', S[7], S[7] + 2.5)
@shot('T08_loop', S[7], END, LA + ['T_FX'], 'W_LA')
def t08(t, f):
    hide(SHOCK, f)
    g = 1 - ss((t - T_GO - 0.1) / 0.12) if t > T_GO + 0.1 else 1.0
    hero_on(f, g)
    stand_cup(f, t, LA0, -math.pi / 2, sip=0.5 * ramp(t, S[7] + 0.3, S[7] + 1.2) * (1 - ramp(t, S[7] + 2.0, S[7] + 2.6)), look=(0, 0, 0.0))
    if g < 0.05: cup_hide(f)
    u = eio((t - S[7]) / (END - S[7]))
    key_cam(f, LA0 + V(lerp(1.8, 1.4, u), lerp(-3.6, -3.0, u), 1.3), LA0 + V(0, 0, 1.15), 32, 4.0)
