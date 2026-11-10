"""Invisible Short shots. The hero turns to glass via the GLASSMIX / GLASSBSDF nodes on StickWhite."""
import bpy, math, json, random
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
SETG = {'__name__': 'iset'}; SETG.update(IMGS)
exec(open(TEX + r"\invis_set_v1.py", encoding='utf-8').read(), SETG)
exec(open(TEX + r"\wf_common_v2.py", encoding='utf-8').read(), globals())
TJ = json.load(open(TEX + r"\invis_timing_v1.json"))
S = [s['start'] for s in TJ['scenes']]; END = TJ['duration']
def wt(word, after=0.0, default=None):
    for w in TJ['words']:
        if w['start'] >= after - 0.01 and w['word'].lower().strip('.,?!:') == word: return w['start']
    return default if default is not None else after
K0 = SETG['K0']
NT = D.materials['StickWhite'].node_tree; GMIX = NT.nodes['GLASSMIX']; GB = NT.nodes['GLASSBSDF']
for _n in ('StickBody', 'StickHead'):                    # no black outline on an invisible body
    _m = D.objects[_n].modifiers.get('Outline')
    if _m: _m.show_render = False; _m.show_viewport = False
if NT.animation_data: NT.animation_data_clear()
SW = D.objects['I_Sandwich']; CH = SETG['CHUNKS']; CR = SETG['CRUMBS']; DR = SETG['DROPS']; SP = SETG['SPLS']
for o in [SW] + CH + CR + DR + SP:
    if o.animation_data: o.animation_data_clear()
def glass(f, k=1.0, ior=1.33):
    GMIX.inputs[0].default_value = k; GB.inputs['IOR'].default_value = ior
    GMIX.inputs[0].keyframe_insert('default_value', frame=f); GB.inputs['IOR'].keyframe_insert('default_value', frame=f)
def eyes_glass(f, k):                                   # the eyes vanish with the body
    for e, s0 in zip(EYES, EYE0):
        s = max(0.0005, 1 - k); e.scale = (s0[0] * s, s0[1] * s, s0[2] * s); e.keyframe_insert('scale', frame=f)
HB = K0 + V(0.9, 1.0, 0.0); HH = -math.pi / 2 - 0.35        # hero spot by the table, facing the camera side
fwh, lfh = frame_vecs(HH)
def sandwich_at(f, p, rot=(0, 0, 0)):
    SW.location = p; SW.rotation_euler = rot; SW.keyframe_insert('location', frame=f); SW.keyframe_insert('rotation_euler', frame=f)
def crumbs(f, t, t0, src):
    rs = random.Random(4)
    for i, o in enumerate(CR):
        w = (t - t0 - i * 0.12) % 1.6
        if t < t0: hide(o, f); continue
        p = src + V(rs.uniform(-0.05, 0.05), rs.uniform(-0.04, 0.04), -0.5 * 9.81 * (w * 0.35) ** 2 * 3)
        if p.z < K0.z + 0.01: p.z = K0.z + 0.004
        show(o, f, p)
def chunks(f, t, a, b, C):
    for i, o in enumerate(CH):
        u = (t - a) / (b - a) - i * 0.06
        if t < a or u < 0 or u > 1.0: hide(o, f); continue
        top = C + V(0, 0, 0.62); stom = C + V(0.02 * math.sin(i), 0.0, 0.1 + 0.03 * (i % 3))
        p = top.lerp(stom, ss(min(1, u * 1.8))) + V(0.02 * math.sin(t * 2 + i), 0, 0)
        s = 1.0 - 0.75 * ss((u - 0.55) / 0.45); show(o, f, p, (s, s, s))
def hold(f, t, C, h, bite=0.0):
    fw, lf = frame_vecs(h)
    mouth = C + fw * 0.12 + V(0, 0, 0.68); rest = C + fw * 0.32 - lf * 0.12 + V(0, 0, 0.32)
    hand = rest.lerp(mouth + fw * 0.08, bite)
    return (C + lf * 0.25 + V(0, 0, -0.075), hand), hand
def stand_sandwich(f, t, bite=0.0, look=(0, 0, 0)):
    C = HB + V(0, 0, 0.845); hands, hand = hold(f, t, C, HH, bite)
    stand(f, HB, HH, hands=hands, head=look); sandwich_at(f, hand + V(0, 0, 0.03), (0.2, 0.15 * bite, HH)); return C, hand
KIT = ['I_KITCHEN', 'I_FOOD']; STREET = ['BLD_Row', 'Street', 'Props', 'Cars', 'FZ', 'I_RAIN', 'I_FOOD']
CAM0 = HB + V(0.2, -2.2, 1.35); TGT0 = HB + V(-0.15, 0.1, 1.05)
def rain_off(f):
    for o in DR + SP: hide(o, f)

@shot('I01_hook', 0.0, S[1], KIT, 'W_KITCHEN', rt=True)
def i01(t, f):
    key_hero_xform(f); glass(f, 1.0, 1.08); eyes_glass(f, 1.0); rain_off(f); chunks(f, -1, 0, 1, HB)
    C, hand = stand_sandwich(f, t, 0.0); crumbs(f, t, 0.0, hand)
    u = eio(t / S[1]); key_cam(f, CAM0 + V(0.1 * u, 0.25 * u, 0), TGT0, 32, 4.5)

@shot('I02_blind', S[1], S[2], KIT, 'W_KITCHEN', rt=True)
def i02(t, f):
    key_hero_xform(f); glass(f, 1.0, 1.08); eyes_glass(f, 1.0); rain_off(f); chunks(f, -1, 0, 1, HB)
    C, hand = stand_sandwich(f, t, 0.0, look=(0, 0, 0.3 * math.sin(t * 2))); crumbs(f, -1, 0, hand)
    face = C + V(0, 0, 0.72)
    if t < S[1] + 1.1:                                   # close on the (empty) glass face
        key_cam(f, face + fwh * 0.9 + lfh * 0.2 + V(0, 0, 0.05), face, 45, 3.0)
    else:                                                # his point of view (fades to black in the edit)
        key_cam(f, face + fwh * 0.2, face + fwh * 4 + V(0, 0, -0.2), 24, 8.0)

@shot('I03_plate', S[2], S[3], KIT, 'W_KITCHEN', rt=True)
def i03(t, f):
    key_hero_xform(f); glass(f, 1.0, 1.08); eyes_glass(f, 1.0); rain_off(f); chunks(f, -1, 0, 1, HB)
    stand_sandwich(f, t, 0.0); crumbs(f, -1, 0, HB)
    u = eio((t - S[2]) / (S[3] - S[2])); key_cam(f, K0 + V(lerp(-1.6, -1.2, u), -2.4, 1.5), HB + V(-0.5, 0.6, 1.0), 26, 8.0)

@shot('I04_glass', S[3], S[5], KIT, 'W_KITCHEN', rt=True)
def i04(t, f):
    key_hero_xform(f); rain_off(f); chunks(f, -1, 0, 1, HB)
    vis = ramp(t, S[3] + 0.2, S[3] + 1.0)
    glass(f, 1.0, lerp(1.08, 1.45, vis)); eyes_glass(f, 1.0)
    C, hand = stand_sandwich(f, t, 0.0, look=(0, 0, 0.2)); crumbs(f, -1, 0, hand)
    if t < S[4]:                                         # wide: a glassy figure, the kitchen warped through him
        u = eio((t - S[3]) / (S[4] - S[3])); key_cam(f, K0 + V(lerp(2.0, 1.6, u), -2.0, 1.3), HB + V(0, 0, 1.0), 28, 8.0)
    else:                                                # slow orbit close-up, the shimmer of the outline
        u = eio((t - S[4]) / (S[5] - S[4])); a = lerp(-0.5, 0.5, u)
        cp = HB + V(math.sin(a) * 1.6, -math.cos(a) * 1.6, 1.35); key_cam(f, cp, HB + V(0, 0, 1.15), 40, 4.0)

@shot('I06_air', S[5], S[6], KIT, 'W_KITCHEN', rt=True)
def i06(t, f):
    key_hero_xform(f); rain_off(f); chunks(f, -1, 0, 1, HB); eyes_glass(f, 1.0)
    k = ramp(t, wt('exactly', S[5], S[5] + 2.0), S[6] - 0.8)        # IOR slides to air: he disappears completely
    glass(f, 1.0, lerp(1.45, 1.0003, k))
    C, hand = stand_sandwich(f, t, 0.0); crumbs(f, -1, 0, hand)
    key_cam(f, K0 + V(1.9, -1.8, 1.3), HB + V(0, 0, 1.0), 32, 8.0)

@shot('I07_food', S[6], S[8], KIT, 'W_KITCHEN', rt=True)
def i07(t, f):
    key_hero_xform(f); rain_off(f); eyes_glass(f, 1.0)
    glass(f, 1.0, lerp(1.0003, 1.12, ramp(t, S[6], S[6] + 0.5)))
    bite = ramp(t, S[6] + 0.2, S[6] + 0.8) * (1 - ramp(t, S[6] + 1.2, S[6] + 1.7))
    C, hand = stand_sandwich(f, t, bite); crumbs(f, t, S[6] + 0.8, hand)
    chunks(f, t, S[7] + 0.1, S[8] - 0.2, C)
    if t < S[7]:                                         # 7: the floating sandwich, close
        key_cam(f, hand + fwh * 0.6 + lfh * 0.25 + V(0, 0, 0.1), hand, 50, 2.8)
    else:                                                # 8: the torso: the food sliding down into the stomach
        u = eio((t - S[7]) / (S[8] - S[7])); key_cam(f, C + fwh * 1.5 + lfh * 0.3 + V(0, 0, lerp(0.55, 0.25, u)), C + V(0, 0, lerp(0.5, 0.15, u)), 40, 4.0)

RAIN_P = V(8.0, 4.0, 0.0); RH = -math.pi / 2 + 0.3
def key_rain(f, t):
    C = RAIN_P + V(0, 0, 0.845); rs = random.Random(7)
    pts = [C + V(0, 0, 0.71) + V(rs.uniform(-0.1, 0.1), rs.uniform(-0.1, 0.1), 0.13) for _ in range(14)] + \
          [C + V(rs.choice((-1, 1)) * 0.18, rs.uniform(-0.05, 0.05), 0.48) for _ in range(10)] + \
          [RAIN_P + V(rs.uniform(-3, 3), rs.uniform(-3, 3), 0) for _ in range(16)]
    for i, (dr, sp) in enumerate(zip(DR, SP)):
        per = 0.9 + 0.3 * (i % 4); ph = (t * 1.0 + i * 0.137) % per
        tgt = pts[i % len(pts)]; fall = 0.45
        if ph < fall:
            p = tgt + V(0, 0, (fall - ph) * 9.0); show(dr, f, p, (0.012, 0.012, 0.018)); hide(sp, f)
        elif ph < fall + 0.25:
            w = (ph - fall) / 0.25; hide(dr, f); show(sp, f, tgt, (0.02 + 0.05 * w, 0.02 + 0.05 * w, 0.01 * (1 - w) + 0.002))
        else: hide(dr, f); hide(sp, f)
@shot('I09_rain', S[8], S[9], STREET, 'W_RAIN', rt=True)
def i09(t, f):
    key_hero_xform(f); glass(f, 1.0, 1.06); eyes_glass(f, 1.0); chunks(f, -1, 0, 1, HB); crumbs(f, -1, 0, HB); sandwich_at(f, K0 + V(0, 0, -50))
    stand(f, RAIN_P, RH, head=(-0.15, 0, 0.1 * math.sin(t))); key_rain(f, t)
    u = eio((t - S[8]) / (S[9] - S[8])); key_cam(f, RAIN_P + V(lerp(2.2, 1.8, u), -2.2, 1.3), RAIN_P + V(0, 0, 1.15), 35, 5.0)

T_BITE = wt('bite', S[9], END - 0.6)
@shot('I10_loop', S[9], END, KIT, 'W_KITCHEN', rt=True)
def i10(t, f):
    key_hero_xform(f); rain_off(f); chunks(f, -1, 0, 1, HB); eyes_glass(f, 1.0)
    glass(f, 1.0, lerp(1.06, 1.08, ramp(t, S[9], S[9] + 0.5)))
    bite = ramp(t, T_BITE - 0.6, T_BITE) * (1 - ramp(t, T_BITE + 0.2, END - 0.1))
    C, hand = stand_sandwich(f, t, bite); crumbs(f, t, T_BITE, hand)
    u = eio((t - S[9]) / (END - S[9] - 0.2))
    key_cam(f, (HB + V(1.3, -1.6, 1.25)).lerp(CAM0, u), (HB + V(0, 0, 1.1)).lerp(TGT0, u), 32, 4.5)
