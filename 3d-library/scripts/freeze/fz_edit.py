"""Freeze-time Short editor: 3D shots + calm text + neon pieces over animated plates. No punch-ins, no SFX."""
import sys, math, json, subprocess, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2
sys.path.insert(0, '/tmp/gv')
import edit as E
W, H, FPS = 1080, 1920, 30
CYN, YEL, RED, WHT, GO, BLU = E.CYN, E.YEL, E.RED, E.WHT, E.GO, E.BLU
ss, eout, lerp, cl = E.ss, E.eout, E.lerp, E.cl
TJ = json.load(open('/tmp/gv/freeze/timing.json'))
WORDS = TJ['words']
def wt(word, after=0.0):
    for w in WORDS:
        if w['start'] >= after and w['word'].strip('.,?!').lower() == word.lower(): return w['start']
    raise KeyError(word)
END_T = 63.40; NF = int(round(END_T * FPS))
SHOTS = {'S01_snap': (1, 34), 'S02_splash': (35, 107), 'S03_crane': (108, 180), 'S04_except': (181, 266), 'S05_pigeons': (267, 322),
         'S06_poke': (323, 391), 'S07_taxi': (392, 443), 'S08_orbit': (444, 587), 'BG1_plate': (588, 818), 'BG2_plate': (819, 1028),
         'S09_pov': (1029, 1119), 'S09b_grope': (1120, 1156), 'S09b_mask': (1120, 1156), 'S10_step': (1197, 1239), 'S11_molecules': (1240, 1354),
         'S12_glass': (1355, 1441), 'S13_face': (1442, 1527), 'S14_restart': (1670, 1726), 'S15_land': (1727, 1770), 'S16_flyoff': (1771, 1826),
         'S17_end': (1827, 1902)}
SRC = os.environ.get('FZ_SRC', '/tmp/gv/freeze/shots')
SINGLE = False
class Reader:
    def __init__(s, path): s.path = path; s.p = None; s.i = -1; s.last = None
    def get(s, i):
        if s.p is None or i < s.i:
            if s.p: s.p.kill()
            s.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', s.path, '-vf', f'scale={W}:{H}:flags=bicubic', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                   stdout=subprocess.PIPE, stdin=subprocess.DEVNULL); s.i = -1
        while s.i < i:
            b = s.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            s.last = b; s.i += 1
        return Image.frombytes('RGB', (W, H), s.last)
READ = {}
def GF(t): return int(round(t * FPS)) + 1
def shot(name, t=None, gf=None):
    a, b = SHOTS[name]; gf = GF(t) if gf is None else gf; gf = max(a, min(b, gf)); i = gf - a
    path = f'{SRC}/{name}.mp4'
    if SINGLE:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{i}),scale={W}:{H}', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, stdin=subprocess.DEVNULL).stdout
        return Image.frombytes('RGB', (W, H), raw[:W * H * 3]) if len(raw) >= W * H * 3 else Image.new('RGB', (W, H))
    if name not in READ: READ[name] = Reader(path)
    return READ[name].get(i).copy()

# ---------------- looks ----------------
T_FREEZE = 1.95; T_RESTART = 55.62
def frozen_grade(img, k):
    if k <= 0: return img
    a = np.asarray(img, np.float32); g = a.mean(axis=2, keepdims=True)
    a = a * (1 - 0.22 * k) + g * 0.22 * k
    a = a * (1 + k * (np.array([-0.05, -0.01, 0.06])))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2
    a = a * (1 - 0.28 * k * np.clip(v, 0, 1))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def calm_text(img, t, a, b, text, y=300, sz=96, hi=None, col=None):
    if t < a or t > b: return img
    k = ss((t - a) / 0.2) * ss((b - t) / 0.2)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); f = E.font(sz)
    lines = [text] if isinstance(text, str) else text
    rise = 12 * (1 - ss((t - a) / 0.2))
    for li, line in enumerate(lines):
        ws = line.split(' '); widths = [d.textbbox((0, 0), w, font=f, stroke_width=10)[2] for w in ws]
        sp = sz * 0.28; x = W / 2 - (sum(widths) + sp * (len(ws) - 1)) / 2; yy = y + li * sz * 1.12 + rise
        for w, ww in zip(ws, widths):
            c = (YEL if (hi and w.strip('?!.,:') in hi) else (col or WHT))
            d.text((x, yy), w, font=f, fill=c + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255)); x += ww + sp
    if k < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * k)))
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')
def plate(img, dim=0.36, blur=11):
    """animated 3D plate softened behind a full-frame neon graphic"""
    a = cv2.GaussianBlur(np.asarray(img, np.float32), (0, 0), blur) * dim
    g = np.asarray(E.GRID, np.float32)
    return Image.fromarray(np.clip(a * 0.85 + g * 0.6, 0, 255).astype(np.uint8))
def outline_from_mask(img, col=CYN, gain=1.0):
    """neon outline of the hero from the hero-only render (black background)"""
    g = np.asarray(img.convert('L'), np.float32)
    m = (g > 18).astype(np.uint8)
    edge = cv2.dilate(m, np.ones((7, 7), np.uint8)) - cv2.erode(m, np.ones((3, 3), np.uint8))
    lay = np.zeros((H, W, 4), np.uint8); lay[..., :3] = col; lay[..., 3] = (edge * 255 * gain).astype(np.uint8)
    return Image.fromarray(lay, 'RGBA')
def flash(img, k, col=(235, 250, 255)):
    if k <= 0: return img
    return Image.blend(img, Image.new('RGB', (W, H), col), cl(k))

# ---------------- neon: light diagram ----------------
SUN = (250, 470); PIG = (560, 880); EYE = (790, 1370)
def bird_icon(d, x, y, s, col, a=255):
    pts = [(x - 95 * s, y - 40 * s), (x - 40 * s, y - 5 * s), (x, y + 10 * s), (x + 40 * s, y - 5 * s), (x + 95 * s, y - 40 * s)]
    d.line(pts, fill=col + (a,), width=int(9 * s), joint='curve')
    d.ellipse((x - 22 * s, y - 8 * s, x + 22 * s, y + 30 * s), outline=col + (a,), width=int(7 * s))
def eye_icon(d, x, y, s, col, iris, a=255, dark=0.0):
    w, h = 170 * s, 95 * s
    top = [(x - w + 2 * w * i / 40, y - h * math.sin(math.pi * i / 40)) for i in range(41)]
    bot = [(x - w + 2 * w * i / 40, y + h * math.sin(math.pi * i / 40)) for i in range(41)]
    d.line(top, fill=col + (a,), width=int(10 * s), joint='curve'); d.line(bot, fill=col + (a,), width=int(10 * s), joint='curve')
    r = 62 * s; ic = tuple(int(lerp(c, 40, dark)) for c in iris)
    d.ellipse((x - r, y - r, x + r, y + r), outline=ic + (a,), width=int(12 * s))
    d.ellipse((x - r * 0.42, y - r * 0.42, x + r * 0.42, y + r * 0.42), fill=(int(lerp(220, 20, dark)),) * 3 + (a,))
def sun_icon(d, x, y, t, a=255):
    R = 88; d.ellipse((x - R, y - R, x + R, y + R), fill=YEL + (a,))
    for i in range(12):
        ang = i * math.pi / 6 + t * 0.4
        d.line((x + math.cos(ang) * (R + 22), y + math.sin(ang) * (R + 22), x + math.cos(ang) * (R + 58), y + math.sin(ang) * (R + 58)), fill=YEL + (a,), width=9)
def photons(d, p0, p1, t, k, frozen_at=None, col=YEL, n=7, speed=0.9, flick=False):
    for i in range(n):
        tt = t if frozen_at is None else min(t, frozen_at)
        u = (tt * speed + i / n) % 1.0
        x = lerp(p0[0], p1[0], u); y = lerp(p0[1], p1[1], u)
        a = 255 * k * ((0.6 + 0.4 * math.sin(t * 40 + i * 2.1)) if flick else 1.0)
        r = 13
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(max(0, min(255, a))),))
def dashed(d, p0, p1, col, a, w=4, seg=26):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = int(L / seg)
    for i in range(0, n, 2):
        u0, u1 = i / n, min(1, (i + 1) / n)
        d.line((lerp(p0[0], p1[0], u0), lerp(p0[1], p1[1], u0), lerp(p0[0], p1[0], u1), lerp(p0[1], p1[1], u1)), fill=col + (a,), width=w)
def light_diagram(img, t, a, b, mode):
    """mode 'see' (light flows sun->pigeon->eye), 'frozen' (photons stop), 'dark' (eye dark + red X)"""
    k = ss((t - a) / 0.35) * (ss((b - t) / 0.3) if mode != 'dark' else 1.0)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); u = t - a
    al = int(255 * k)
    sun_icon(d, *SUN, t, al)
    bird_icon(d, *PIG, 1.25, WHT, al)
    T_FR = wt('frozen', 29.0) + 0.1
    fz = T_FR if mode in ('frozen', 'dark') else None
    dark = ss((t - wt('single', 32.0)) / 0.6) if mode == 'dark' else 0.0
    eye_icon(d, *EYE, 1.15, WHT, CYN, al, dark)
    dashed(d, SUN, PIG, (120, 100, 40), int(160 * k)); dashed(d, PIG, EYE, (40, 90, 120), int(160 * k))
    pc = YEL if fz is None or t < fz else (170, 230, 255)
    reach = ss((u - 0.25) / 0.5)
    if reach > 0:
        photons(d, SUN, PIG, t - 20, k * reach, frozen_at=None if fz is None else fz - 20, col=pc, flick=fz is not None and t > fz)
        p_end = (lerp(PIG[0], EYE[0], 0.86), lerp(PIG[1], EYE[1], 0.86))
        photons(d, PIG, p_end if fz else EYE, t - 20.3, k * reach, frozen_at=None if fz is None else fz - 20.3, col=pc, flick=fz is not None and t > fz)
    for txt, (x, y) in (('SUN', (SUN[0], SUN[1] + 170)), ('PIGEON', (PIG[0] + 10, PIG[1] + 95)), ('YOUR EYE', (EYE[0], EYE[1] + 160))):
        E.text_center(d, (x, y), txt, 46, (200, 215, 235, int(220 * k)))
    if mode == 'see':
        hit = 0.5 + 0.5 * math.sin(t * 9)
        d.ellipse((EYE[0] - 120, EYE[1] - 120, EYE[0] + 120, EYE[1] + 120), outline=CYN + (int(90 * k * hit * reach),), width=6)
    if mode == 'dark':
        xk = ss((t - wt('reaches', 33.0)) / 0.25)
        if xk > 0:
            s = 115
            for (x0, y0, x1, y1) in ((EYE[0] - s, EYE[1] - s, EYE[0] + s, EYE[1] + s), (EYE[0] - s, EYE[1] + s, EYE[0] + s, EYE[1] - s)):
                d.line((x0, y0, x1, y1), fill=RED + (int(255 * xk),), width=26)
    img = E.glow_add(img, lay, 1.5, 16)
    return img
# ---------------- neon: speed of light counter ----------------
def counter_piece(img, t, a, b):
    k = ss((t - a) / 0.35) * ss((b - t) / 0.3)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); u = t - a
    y = 880
    d.line((60, y, 1020, y), fill=(255, 230, 140, int(90 * k)), width=6)
    for i in range(3):
        ph = (u * 1.4 + i / 3) % 1; x = lerp(60, 1020, ph)
        for j in range(14):
            xx = x - j * 14
            if xx > 60: d.ellipse((xx - 12 + j * 0.6, y - 12 + j * 0.6, xx + 12 - j * 0.6, y + 12 - j * 0.6), fill=(255, 240, 170, int(220 * k * (1 - j / 14))))
    E.text_center(d, (540, 700), 'SPEED OF LIGHT', 64, CYN + (int(255 * k),))
    t0 = wt('three', 23.0); t1 = wt('kilometres', 24.0) + 0.4
    v = int(3_000_000 * eout((t - t0) / (t1 - t0))) if t > t0 else 0
    E.text_center(d, (540, 1060), f'{v:,}', 150, WHT + (int(255 * k),))
    E.text_center(d, (540, 1190), 'KILOMETRES', 70, YEL + (int(255 * k),))
    tk = ss((t - wt('ten', 25.5)) / 0.3)
    E.text_center(d, (540, 1330), 'IN 10 SECONDS', 70, WHT + (int(255 * k * tk),))
    E.wavy(d, 330, 750, 1395, CYN, cl((t - wt('ten', 25.5) - 0.2) / 0.4) * k)
    return E.glow_add(img, lay, 1.5, 16)
# ---------------- neon: eight trips to the Moon ----------------
def moon_piece(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); u = t - a
    ex, mx, y = 240, 860, 960
    E.draw_globe(d, t, u * 0.8, 120, ex, y, alpha=k)
    d.ellipse((mx - 50, y - 50, mx + 50, y + 50), fill=(190, 195, 205, int(255 * k)))
    for cx, cy, r in ((mx - 15, y - 12, 11), (mx + 18, y + 14, 8), (mx + 6, y - 24, 6)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(150, 155, 165, int(255 * k)))
    dashed(d, (ex + 125, y), (mx - 55, y), (120, 110, 60), int(150 * k))
    E.text_center(d, (550, y + 75), '384,400 KM', 44, (200, 215, 235, int(220 * k)))
    E.text_center(d, (ex, y + 175), 'EARTH', 46, (200, 215, 235, int(220 * k))); E.text_center(d, (mx, y + 110), 'MOON', 46, (200, 215, 235, int(220 * k)))
    s0, s1 = 27.55, 29.25
    trips = 0
    if t > s0:
        q = min(8.0, (t - s0) / (s1 - s0) * 8.0); trips = int(q)
        ph = q - trips
        if q < 8:
            x = lerp(ex + 125, mx - 55, ph * 2 if ph < 0.5 else 2 - ph * 2)
            for j in range(10):
                xx = x - j * 10 * (1 if ph < 0.5 else -1)
                d.ellipse((xx - 14 + j, y - 14 + j, xx + 14 - j, y + 14 - j), fill=(255, 240, 170, int(230 * k * (1 - j / 10))))
    E.text_center(d, (540, 1330), f'TRIPS: {trips}', 96, YEL + (int(255 * k),))
    return E.glow_add(img, lay, 1.5, 16)
# ---------------- neon: countdown ring in the dark ----------------
def ring_dark(t):
    img = Image.new('RGB', (W, H), (4, 5, 10))
    g = np.asarray(E.GRID, np.float32) * 0.35; img = Image.fromarray(g.astype(np.uint8))
    ol = outline_from_mask(shot('S09b_mask', gf=SHOTS['S09b_mask'][1]), (60, 120, 160), 0.35)
    img = img.convert('RGBA'); img.alpha_composite(ol); img = img.convert('RGB')
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    k = ss((t - 50.9) / 0.4)
    cx, cy, R = 540, 820, 270
    ticks = [(wt('just', 53.0), 3), (wt('silent', 53.5), 2), (wt('seconds', 54.0) + 0.25, 1)]
    n = 4; t_last = 50.9
    for tt, nn in ticks:
        if t >= tt: n = nn; t_last = tt
    frac = n / 10 - 0.1 * ss((t - t_last) / 0.6) * (0 if t < ticks[0][0] else 0)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(40, 60, 90, int(255 * k)), width=18)
    d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * frac, fill=CYN + (int(255 * k),), width=22)
    pop = ss((t - t_last) / 0.2) if t_last > 51 else 1.0
    E.text_center(d, (cx, cy - 10), str(n), 280, WHT + (int(255 * k * pop),))
    E.text_center(d, (cx, cy + R + 70), 'SECONDS LEFT', 50, CYN + (int(200 * k),))
    img = E.glow_add(img, lay, 1.6, 18)
    img = calm_text(img, t, wt('no', 50.5) - 0.05, wt('no', 51.8) - 0.1, 'NO LIGHT.', y=1330, sz=84)
    img = calm_text(img, t, wt('no', 51.8) - 0.05, wt('just', 53.0) - 0.15, 'NO SOUND.', y=1330, sz=84)
    img = calm_text(img, t, wt('just', 53.0), 55.55, ['10 SILENT', 'SECONDS'], y=1330, sz=84, hi=['SILENT'])
    return img
def stamp(img, t, a, b, l1, l2):
    if t < a or t > b: return img
    u = t - a; k = ss(u / 0.12) * ss((b - t) / 0.2)
    sc_ = lerp(1.12, 1.0, ss(u / 0.15)); cx, cy = 540, 1380
    tmp = E.new_lay(); td = ImageDraw.Draw(tmp)
    td.rounded_rectangle((cx - 370 * sc_, cy - 150 * sc_, cx + 370 * sc_, cy + 150 * sc_), int(36 * sc_), outline=RED + (255,), width=14, fill=(20, 0, 0, 120))
    E.text_center(td, (cx, cy - 52 * sc_), l1, int(104 * sc_), RED + (255,)); E.text_center(td, (cx, cy + 60 * sc_), l2, int(104 * sc_), WHT + (255,))
    tmp = tmp.rotate(-5, center=(cx, cy), resample=Image.BICUBIC)
    if k < 1: tmp.putalpha(tmp.getchannel('A').point(lambda v: int(v * k)))
    return E.glow_add(img, tmp, 1.2, 14)
# ---------------- timeline ----------------
def seg(t):
    fk = ss((t - T_FREEZE) / 0.25) if t < T_RESTART else 0.0
    if t < 1.15:
        img = shot('S01_snap', t)
        if t < 0.55:
            la = E.lineart(img, CYN, 0.10); sy = int(H * cl(t / 0.45))
            if t < 0.45:
                arr = np.asarray(la).copy(); arr[max(0, sy - 6):sy + 6] = np.clip(arr[max(0, sy - 6):sy + 6].astype(np.int32) + np.array([140, 230, 255]), 0, 255)
                top = np.asarray(img); arr[:max(0, sy - 6)] = (arr[:max(0, sy - 6)] * 0.25 + top[:max(0, sy - 6)] * 0.75).astype(np.uint8)
                img = Image.fromarray(arr)
            else:
                img = Image.blend(la, img, ss((t - 0.45) / 0.1))
        return calm_text(img, t, 0.0, 1.12, ['FREEZE TIME', 'FOR 10 SECONDS?'], y=260, sz=92, hi=['TIME', '10'])
    if t < 3.58:
        img = frozen_grade(shot('S02_splash', t), fk)
        img = flash(img, 0.35 * math.exp(-max(0, t - T_FREEZE) / 0.08) if t > T_FREEZE else 0, (200, 240, 255))
        return calm_text(img, t, 2.05, 3.5, 'TIME: STOPPED', y=280, sz=100, hi=['STOPPED'])
    if t < 6.00: return frozen_grade(shot('S03_crane', t), 1)
    if t < 8.88: return calm_text(frozen_grade(shot('S04_except', t), 1), t, wt('except', 7.0) - 0.05, 8.82, 'EXCEPT YOU', y=280, sz=100, hi=['YOU'])
    if t < 10.72: return calm_text(frozen_grade(shot('S05_pigeons', t), 1), t, wt('mid-air', 9.0) - 0.3, 10.66, 'MID-AIR', y=300, sz=110, hi=['MID-AIR'])
    if t < 13.02: return calm_text(frozen_grade(shot('S06_poke', t), 1), t, wt('glass', 11.0) - 0.45, 12.96, 'TURNS TO GLASS', y=280, sz=96, hi=['GLASS'])
    if t < 14.78: return calm_text(frozen_grade(shot('S07_taxi', t), 1), t, wt('mid-turn', 13.0) - 0.3, 14.72, 'MID-TURN', y=300, sz=110, hi=['MID-TURN'])
    if t < 19.56:
        img = frozen_grade(shot('S08_orbit', t), 1)
        T_W = 16.69
        if t > T_W:
            la = E.lineart(img, GO, 0.14)
            p = ss((t - T_W) / 0.55); sy = int(H * p)
            arr = np.asarray(img).copy(); la_a = np.asarray(la)
            arr[:sy] = la_a[:sy]
            if p < 1: arr[max(0, sy - 5):sy + 5] = np.clip(arr[max(0, sy - 5):sy + 5].astype(np.int32) + np.array([255, 210, 120]), 0, 255)
            img = Image.fromarray(arr)
        img = calm_text(img, t, wt('problem', 17.0) - 0.3, 19.5, 'THE PROBLEM', y=300, sz=112, hi=['PROBLEM'])
        return calm_text(img, t, wt('nobody', 17.5) - 0.1, 19.5, 'NOBODY TALKS ABOUT', y=440, sz=66)
    if t < 22.54:
        img = plate(frozen_grade(shot('BG1_plate', t), 1))
        img = light_diagram(img, t, 19.56, 22.54, 'see')
        return calm_text(img, t, wt('light', 20.5) - 0.1, 22.45, ['LIGHT HAS TO', 'REACH YOUR EYES'], y=170, sz=74, hi=['EYES'])
    if t < 27.26: return counter_piece(plate(frozen_grade(shot('BG1_plate', t), 1)), t, 22.54, 27.26)
    if t < 29.42:
        img = moon_piece(plate(frozen_grade(shot('BG2_plate', t), 1)), t, 27.26, 29.42)
        return calm_text(img, t, wt('eight', 27.5) - 0.1, 29.36, '8X TO THE MOON', y=300, sz=100, hi=['8X'])
    if t < 32.24:
        img = light_diagram(plate(frozen_grade(shot('BG2_plate', t), 1)), t, 29.42, 32.30, 'frozen')
        return calm_text(img, t, wt('frozen', 30.0) - 0.15, 32.2, 'LIGHT: FROZEN', y=170, sz=96, hi=['FROZEN'])
    if t < 34.26:
        img = light_diagram(plate(frozen_grade(shot('BG2_plate', t), 1), dim=0.3), t, 32.24 - 0.35, 99, 'dark')
        return calm_text(img, t, wt('reaches', 33.0) - 0.2, 34.2, 'ZERO LIGHT ARRIVES', y=170, sz=80, hi=['ZERO'])
    if t < 37.30:
        img = frozen_grade(shot('S09_pov', t), 1)
        k = ss((t - 35.2) / (wt('blind', 37.0) - 35.2))
        a = np.asarray(img, np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        edge = 1.6 * (1 - k)
        m = np.clip((edge - r) / 0.35, 0, 1)
        return Image.fromarray((a * m[..., None]).astype(np.uint8))
    if t < 38.52:
        img = Image.fromarray((np.asarray(E.GRID, np.float32) * 0.25).astype(np.uint8))
        ol = outline_from_mask(shot('S09b_mask', t), CYN, ss((t - 37.3) / 0.3))
        img = E.glow_add(img, ol, 1.6, 14)
        return calm_text(img, t, wt('blind', 37.0) - 0.05, 38.46, 'BLIND', y=300, sz=130, hi=['BLIND'])
    if t < 39.88:
        img = Image.fromarray((np.asarray(E.GRID, np.float32) * 0.5).astype(np.uint8))
        img = calm_text(img, t, wt('and', 38.5) - 0.05, 39.85, 'AND IT GETS', y=760, sz=96)
        return calm_text(img, t, wt('worse', 38.9) - 0.05, 39.85, 'WORSE', y=900, sz=200, hi=['WORSE'])
    if t < 41.31: return calm_text(frozen_grade(shot('S10_step', t), 1), t, wt('step', 40.5) - 0.35, 41.26, 'ONE STEP...', y=300, sz=100)
    if t < 45.12: return calm_text(frozen_grade(shot('S11_molecules', t), 1), t, wt('air', 41.8) - 0.1, 45.05, 'AIR: FROZEN', y=280, sz=104, hi=['FROZEN'])
    if t < 48.02: return calm_text(frozen_grade(shot('S12_glass', t), 1), t, wt('solid', 46.0) - 0.1, 47.96, 'SOLID GLASS', y=280, sz=110, hi=['GLASS'])
    if t < 50.90:
        img = frozen_grade(shot('S13_face', t), 1)
        img = calm_text(img, t, wt('walk', 48.3) - 0.3, 49.4, "CAN'T WALK", y=280, sz=100)
        return stamp(img, t, wt('breathe', 49.8) - 0.05, 50.86, "CAN'T", 'BREATHE')
    if t < T_RESTART: return ring_dark(t)
    if t < 57.54:
        img = shot('S14_restart', t)
        return flash(img, 0.9 * math.exp(-(t - T_RESTART) / 0.12), (255, 255, 255))
    if t < 59.00: return shot('S15_land', t)
    if t < 60.86: return shot('S16_flyoff', t)
    img = shot('S17_end', t)
    return calm_text(img, t, wt('would', 61.0) - 0.25, END_T - 0.32, ['WOULD YOU STILL', 'HIT PAUSE?'], y=260, sz=96, hi=['PAUSE?', 'PAUSE'])
F0 = None
def frame_at(i):
    global F0
    t = i / FPS
    img = seg(t)
    if t > END_T - 0.3:
        if F0 is None: F0 = seg(0.0)
        img = Image.blend(img, F0, ss((t - (END_T - 0.3)) / 0.3))
    return img
if __name__ == '__main__':
    if sys.argv[1] == 'frames':
        SINGLE = True; globals()['SINGLE'] = True
        os.makedirs('/tmp/gv/freeze/test', exist_ok=True)
        for s in sys.argv[2:]:
            t = float(s); frame_at(int(round(t * FPS))).save(f'/tmp/gv/freeze/test/f_{t:06.2f}.jpg', quality=85)
    else:
        i0, i1 = map(int, sys.argv[2].split('-')); i1 = min(i1, NF)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', sys.argv[3]], stdin=subprocess.PIPE)
        for i in range(i0, i1):
            p.stdin.write(frame_at(i).tobytes())
            if i % 60 == 0: print('frame', i, flush=True)
        p.stdin.close(); p.wait()
