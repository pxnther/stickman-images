"""Plane-fall Short editor: 3D shots + calm text + neon overlays. No punch-ins, no SFX."""
import sys, math, json, subprocess, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2
sys.path.insert(0, '/tmp/gv')
import edit as E
W, H, FPS = 1080, 1920, 30
CYN, YEL, RED, WHT, GO, GRN, BLU, ORA = E.CYN, E.YEL, E.RED, E.WHT, E.GO, E.GRN, E.BLU, E.ORA
ss, eout, lerp, cl = E.ss, E.eout, E.lerp, E.cl
TJ = json.load(open('/tmp/gv/plane/timing.json')); WORDS = TJ['words']
def wt(word, after=0.0):
    for w in WORDS:
        if w['start'] >= after - 1e-6 and w['word'].strip('.,?!').lower() == word.lower(): return w['start']
    raise KeyError(word)
END_T = 51.96; NF = int(round(END_T * FPS))
def GF(t): return int(round(t * FPS)) + 1
SHOT_T = [('S01a_exit', 0.0, 1.55), ('S01b_scale', 1.55, 3.00), ('S02_noparachute', 3.00, 4.24), ('S03_cold', 4.24, 6.74), ('S04_limp', 6.74, 10.40),
          ('S05_clouds', 10.40, 14.34), ('S06_skydive', 14.34, 17.44), ('S07_pov', 17.44, 20.12), ('S08_lake', 20.12, 23.58), ('S09a_trees', 23.58, 24.95),
          ('S09b_snowfield', 24.95, 26.10), ('S09c_slope', 26.10, 27.52), ('S10a_spread', 27.52, 29.20), ('S10b_landing', 29.20, 31.24),
          ('S12a_fuselage', 32.44, 35.20), ('S12b_fuselage_wide', 35.20, 38.46), ('S13_wreck', 38.46, 42.04), ('S14_seats_fall', 42.04, 46.26),
          ('S15_jungle_floor', 46.26, 50.00), ('S16_end', 50.00, 51.96)]
SHOTS = {n: (GF(a), GF(b) - 1) for n, a, b in SHOT_T}
SRC = os.environ.get('PF_SRC', '/tmp/gv/plane/shots')
SINGLE = False
class Reader:
    def __init__(s, path): s.path = path; s.p = None; s.i = -1; s.last = None
    def get(s, i):
        if s.p is None or i < s.i:
            if s.p: s.p.kill()
            s.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', s.path, '-vf', f'scale={W}:{H}:flags=bicubic', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                   stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL); s.i = -1
        while s.i < i:
            b = s.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            s.last = b; s.i += 1
        return Image.frombytes('RGB', (W, H), s.last)
READ = {}
def shot(name, t):
    a, b = SHOTS[name]; gf = max(a, min(b, GF(t))); i = gf - a; path = f'{SRC}/{name}.mp4'
    if SINGLE:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{i}),scale={W}:{H}', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, stdin=subprocess.DEVNULL).stdout
        return Image.frombytes('RGB', (W, H), raw[:W * H * 3]) if len(raw) >= W * H * 3 else Image.new('RGB', (W, H), (40, 40, 40))
    if name not in READ: READ[name] = Reader(path)
    return READ[name].get(i).copy()
def which(t):
    for n, a, b in SHOT_T:
        if a <= t < b: return n
    return None

# ---------------- shared looks ----------------
def calm_text(img, t, a, b, text, y=300, sz=96, hi=None, col=None, hicol=None):
    if t < a or t > b: return img
    k = ss((t - a) / 0.2) * ss((b - t) / 0.2)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); f = E.font(sz)
    lines = [text] if isinstance(text, str) else text
    rise = 12 * (1 - ss((t - a) / 0.2))
    for li, line in enumerate(lines):
        ws = line.split(' '); widths = [d.textbbox((0, 0), w, font=f, stroke_width=10)[2] for w in ws]
        sp = sz * 0.28; x = W / 2 - (sum(widths) + sp * (len(ws) - 1)) / 2; yy = y + li * sz * 1.12 + rise
        for w, ww in zip(ws, widths):
            c = ((hicol or YEL) if (hi and w.strip('?!.,:') in hi) else (col or WHT))
            d.text((x, yy), w, font=f, fill=c + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255)); x += ww + sp
    if k < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * k)))
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')
def dim_region(img, k, y0, y1, dim=0.45, blur=9):
    if k <= 0: return img
    a = np.asarray(img, np.float32); b = cv2.GaussianBlur(a, (0, 0), blur) * dim
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    m = (np.clip((yy - y0) / 120, 0, 1) * np.clip((y1 - yy) / 120, 0, 1)) * k
    return Image.fromarray(np.clip(a * (1 - m) + b * m, 0, 255).astype(np.uint8))
def plate(img, dim=0.36, blur=11):
    a = cv2.GaussianBlur(np.asarray(img, np.float32), (0, 0), blur) * dim
    return Image.fromarray(np.clip(a * 0.85 + np.asarray(E.GRID, np.float32) * 0.6, 0, 255).astype(np.uint8))
def vignette(img, k):
    if k <= 0: return img
    a = np.asarray(img, np.float32); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    m = np.clip((1.6 * (1 - k) + 0.1 - r) / 0.45, 0, 1)
    return Image.fromarray((a * m[..., None]).astype(np.uint8))
def flash(img, k, col=(255, 255, 255)):
    return img if k <= 0 else Image.blend(img, Image.new('RGB', (W, H), col), cl(k))
def stamp(img, t, a, b, l1, l2=None, col=RED, rot=-5, cy=1330):
    if t < a or t > b: return img
    u = t - a; k = ss(u / 0.12) * ss((b - t) / 0.2); s_ = lerp(1.12, 1.0, ss(u / 0.15)); cx = 540
    lay = E.new_lay(); d = ImageDraw.Draw(lay); hh = 150 if l2 else 95
    d.rounded_rectangle((cx - 390 * s_, cy - hh * s_, cx + 390 * s_, cy + hh * s_), int(34 * s_), outline=col + (255,), width=14, fill=(15, 0, 0, 130) if col == RED else (0, 15, 5, 130))
    if l2:
        E.text_center(d, (cx, cy - 52 * s_), l1, int(100 * s_), col + (255,)); E.text_center(d, (cx, cy + 60 * s_), l2, int(100 * s_), WHT + (255,))
    else:
        E.text_center(d, (cx, cy), l1, int(110 * s_), col + (255,))
    lay = lay.rotate(rot, center=(cx, cy), resample=Image.BICUBIC)
    if k < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * k)))
    return E.glow_add(img, lay, 1.2, 14)
def hook_scan(img, t):
    if t >= 0.55: return img
    la = E.lineart(img, CYN, 0.10)
    if t >= 0.45: return Image.blend(la, img, ss((t - 0.45) / 0.1))
    sy = int(H * cl(t / 0.45)); arr = np.asarray(la).copy(); top = np.asarray(img)
    arr[:max(0, sy - 6)] = (arr[:max(0, sy - 6)] * 0.25 + top[:max(0, sy - 6)] * 0.75).astype(np.uint8)
    arr[max(0, sy - 6):sy + 6] = np.clip(arr[max(0, sy - 6):sy + 6].astype(np.int32) + np.array([140, 230, 255]), 0, 255)
    return Image.fromarray(arr)

# ---------------- neon overlays ----------------
def thermometer(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.25)
    if k <= 0: return img
    img = dim_region(img, k * 0.8, 260, 1480, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    x, y0, y1 = 830, 420, 1180
    d.rounded_rectangle((x - 34, y0, x + 34, y1), 34, outline=WHT + (al,), width=8)
    d.ellipse((x - 62, y1 - 30, x + 62, y1 + 94), outline=WHT + (al,), width=8)
    T0, T1 = 20, -48; tm = wt('minus', 4.5); u = eout((t - tm) / (wt('degrees', 5.5) - tm + 0.3)) if t > a else 0
    temp = lerp(T0, T1, u)
    fill = cl((temp - (-60)) / 90.0)
    col = tuple(int(lerp(c1, c2, 1 - fill)) for c1, c2 in zip((255, 90, 60), (80, 200, 255)))
    d.ellipse((x - 46, y1 - 14, x + 46, y1 + 78), fill=col + (al,))
    yl = y1 - (y1 - y0 - 30) * fill
    d.rounded_rectangle((x - 18, yl, x + 18, y1 + 10), 18, fill=col + (al,))
    for i, v in enumerate(range(20, -61, -20)):
        yy = y1 - (y1 - y0 - 30) * ((v + 60) / 90.0)
        d.line((x - 70, yy, x - 46, yy), fill=WHT + (al,), width=5)
        E.text_center(d, (x - 130, yy), f'{v}', 40, WHT + (int(200 * k),))
    E.text_center(d, (x - 20, y1 + 170), f'{int(round(temp))}°C', 110, CYN + (al,))
    img = E.glow_add(img, lay, 1.5, 16)
    # frost creeping in from the edges
    fk = ss((t - tm) / 1.6) * k
    if fk > 0:
        rr = random.Random(7); fl = E.new_lay(); fd = ImageDraw.Draw(fl)
        for i in range(260):
            ex = rr.random(); side = rr.randrange(4); dd = rr.random() ** 2.2 * 260 * fk
            px, py = [(ex * W, dd), (ex * W, H - dd), (dd, ex * H), (W - dd, ex * H)][side]
            s_ = rr.uniform(3, 9)
            for ang in (0, 60, 120):
                ca, sa = math.cos(math.radians(ang)) * s_, math.sin(math.radians(ang)) * s_
                fd.line((px - ca, py - sa, px + ca, py + sa), fill=(220, 240, 255, int(220 * fk)), width=2)
        img = E.glow_add(img, fl, 1.2, 8)
    return img
def air_ring(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.85, 200, 1050, dim=0.5)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    cx, cy, R = 540, 640, 230
    t0 = wt('thirty', 8.0) - 0.4; t1 = 10.2
    n = 30 if t < t0 else max(0, int(math.ceil(30 * (1 - cl((t - t0) / (t1 - t0))))))
    frac = n / 30
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(40, 60, 90, al), width=16)
    col = tuple(int(lerp(r, c, frac)) for r, c in zip(RED, CYN))
    if frac > 0: d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * frac, fill=col + (al,), width=20)
    E.text_center(d, (cx, cy - 10), f'{n}', 210, WHT + (al,))
    E.text_center(d, (cx, cy + R + 60), 'SECONDS OF AIR', 52, col + (al,))
    return E.glow_add(img, lay, 1.5, 16)
def altimeter(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    x, y0, y1 = 150, 470, 1250
    d.line((x, y0, x, y1), fill=WHT + (int(180 * k),), width=6)
    for i in range(11):
        yy = y0 + (y1 - y0) * i / 10; d.line((x - 18, yy, x + 18, yy), fill=WHT + (int(160 * k),), width=4)
    alt = lerp(9000, 3000, eout((t - a) / (b - a - 0.4)))
    yy = y1 - (y1 - y0) * alt / 10000
    d.polygon([(x + 26, yy), (x + 62, yy - 20), (x + 62, yy + 20)], fill=CYN + (al,))
    d.text((x + 76, yy - 34), f'{int(alt):,} M', font=E.font(58), fill=CYN + (al,), stroke_width=6, stroke_fill=(0, 0, 0, al))
    d.text((x - 40, y0 - 90), 'ALTITUDE', font=E.font(44), fill=WHT + (int(220 * k),), stroke_width=5, stroke_fill=(0, 0, 0, al))
    return E.glow_add(img, lay, 1.4, 14)
def speed_counter(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    rr = random.Random(int(t * 30)); lay = E.new_lay(); d = ImageDraw.Draw(lay)
    for i in range(22):    # wind streaks rushing upward
        x = rr.uniform(0, W); y = rr.uniform(0, H); L_ = rr.uniform(120, 340)
        d.line((x, y, x, y - L_), fill=(220, 240, 255, int(110 * k)), width=rr.choice((2, 3, 4)))
    t0 = wt('two', 15.0) - 0.2; v = int(200 * eout((t - t0) / 1.4)) if t > t0 else 0
    E.text_center(d, (540, 470), f'{v}', 220, WHT + (int(255 * k),))
    E.text_center(d, (540, 620), 'KM/H', 84, YEL + (int(255 * k),))
    E.wavy(d, 400, 680, 690, YEL, cl((t - t0 - 1.0) / 0.4) * k)
    return E.glow_add(img, lay, 1.5, 16)
def timer_ring(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.6, 260, 1100, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    cx, cy, R = 540, 680, 250
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(40, 60, 90, al), width=16)
    dr = ss((t - a) / 0.6)
    d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * dr, fill=CYN + (al,), width=20)
    E.text_center(d, (cx, cy - 10), '3:00', 170, WHT + (al,))
    E.text_center(d, (cx, cy + R + 60), 'TO PICK YOUR SPOT', 50, CYN + (al,))
    return E.glow_add(img, lay, 1.5, 16)
def checklist(img, t, items):
    lay = E.new_lay(); d = ImageDraw.Draw(lay); vis = False
    for i, (ti, label) in enumerate(items):
        k = ss((t - ti) / 0.2)
        if k <= 0: continue
        vis = True; y = 1080 + i * 120; x = 250
        d.rounded_rectangle((x - 30, y - 50, x + 590, y + 50), 26, fill=(5, 10, 20, int(170 * k)), outline=GRN + (int(220 * k),), width=5)
        d.line([(x, y), (x + 22, y + 24), (x + 62, y - 26)], fill=GRN + (int(255 * k),), width=12, joint='curve')
        d.text((x + 100, y - 38), label, font=E.font(64), fill=WHT + (int(255 * k),))
    return E.glow_add(img, lay, 1.2, 12) if vis else img
def drag_arrows(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    for i, x in enumerate((260, 400, 540, 680, 820)):
        ph = (t * 1.6 + i * 0.23) % 1; y = 1300 - ph * 380
        a_ = int(255 * k * math.sin(math.pi * ph))
        d.line((x, y + 90, x, y), fill=CYN + (a_,), width=10); d.polygon([(x - 26, y + 10), (x + 26, y + 10), (x, y - 30)], fill=CYN + (a_,))
    E.text_center(d, (540, 1460), 'AIR PUSHES BACK', 56, CYN + (int(230 * k),))
    return E.glow_add(img, lay, 1.4, 14)
def record_bars(img, t, a, b, two):
    k = ss((t - a) / 0.35) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.75, 380, 1500, dim=0.45)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    base = 1330; top = 520; maxv = 10160
    bars = [(330 if two else 540, 10160, 'VESNA', '1972', GO)]
    if two: bars.append((750, 3000, 'JULIANE', '1971', GRN))
    for j, (x, v, name, yr, col) in enumerate(bars):
        g = ss((t - a - 0.15 - 0.35 * j) / 0.8) if (two and j == 1) or not two else 1.0
        hgt = (base - top) * v / maxv * g
        d.rounded_rectangle((x - 95, base - hgt, x + 95, base), 22, fill=col + (int(200 * k),), outline=WHT + (int(180 * k),), width=4)
        E.text_center(d, (x, base - hgt - 60), f'{int(v * g):,} M', 72, WHT + (al,))
        E.text_center(d, (x, base + 60), name, 56, col + (al,)); E.text_center(d, (x, base + 120), yr, 46, WHT + (int(200 * k),))
    return E.glow_add(img, lay, 1.4, 16)
def days_counter(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.5, 260, 900, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    t0 = wt('eleven', 47.5) - 0.3; n = int(11 * eout((t - t0) / 0.9)) if t > t0 else 0
    E.text_center(d, (540, 520), f'{n}', 230, WHT + (al,))
    E.text_center(d, (540, 690), 'DAYS ALONE', 80, GRN + (al,))
    E.wavy(d, 330, 750, 760, GRN, cl((t - t0 - 0.9) / 0.4) * k)
    return E.glow_add(img, lay, 1.5, 16)
def light_rays(img, t):
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    for i, (x, w_) in enumerate(((260, 70), (470, 110), (690, 60), (860, 90))):
        a_ = int(55 + 25 * math.sin(t * 0.8 + i))
        d.polygon([(x, 0), (x + w_, 0), (x + w_ + 260, H), (x + 160, H)], fill=(255, 240, 190, a_))
    lay = lay.filter(ImageFilter.GaussianBlur(30))
    return E.glow_add(img, lay, 1.0, 4)

# ---------------- timeline ----------------
T_PASS = wt('pass', 8.0); T_WAKE = wt('wake', 12.5)
def seg(t):
    n = which(t)
    if n is None:   # 'Sounds impossible?' (31.24 - 32.44): kinetic words over the blurred landing frame
        img = plate(shot('S10b_landing', 31.2), dim=0.35)
        img = calm_text(img, t, 31.26, 32.42, 'SOUNDS', y=780, sz=110)
        return calm_text(img, t, wt('impossible', 31.4) - 0.05, 32.42, 'IMPOSSIBLE?', y=920, sz=150, hi=['IMPOSSIBLE?'])
    img = shot(n, t)
    if n == 'S01a_exit':
        img = hook_scan(img, t)
        return calm_text(img, t, 0.0, 2.95, ['10 KM UP', 'NO PARACHUTE?'], y=250, sz=96, hi=['10', 'KM', 'NO'])
    if n == 'S01b_scale':
        return calm_text(img, t, 0.0, 2.95, ['10 KM UP', 'NO PARACHUTE?'], y=250, sz=96, hi=['10', 'KM', 'NO'])
    if n == 'S02_noparachute': return calm_text(img, t, 3.12, 4.2, 'NO PARACHUTE', y=280, sz=104, hi=['NO'], hicol=RED)
    if n == 'S03_cold': return thermometer(img, t, 4.24, 6.74)
    if n == 'S04_limp':
        img = air_ring(img, t, 6.86, 10.25)
        return vignette(img, ss((t - 9.4) / 0.9))
    if n == 'S05_clouds':
        img = vignette(img, 1 - ss((t - 10.4) / 0.8))
        img = altimeter(img, t, 10.6, 14.3)
        img = flash(img, 0.35 * math.exp(-max(0, t - T_WAKE) / 0.12) if t > T_WAKE else 0)
        return calm_text(img, t, T_WAKE - 0.1, 14.3, 'AWAKE AGAIN', y=280, sz=100, hi=['AWAKE'])
    if n == 'S06_skydive': return speed_counter(img, t, 14.34, 17.44)
    if n == 'S07_pov': return timer_ring(img, t, 17.5, 20.1)
    if n == 'S08_lake':
        img = calm_text(img, t, wt('not', 20.0) - 0.05, 21.4, 'NOT WATER', y=280, sz=110, hi=['NOT'], hicol=RED)
        return stamp(img, t, wt('concrete', 22.5) - 0.25, 23.56, 'WATER =', 'CONCRETE')
    if n in ('S09a_trees', 'S09b_snowfield', 'S09c_slope'):
        return checklist(img, t, [(wt('trees', 24.0) - 0.1, 'TREES'), (wt('snow', 25.0) - 0.1, 'DEEP SNOW'), (wt('steep', 26.0) - 0.1, 'STEEP SLOPE')])
    if n == 'S10a_spread':
        img = drag_arrows(img, t, 27.9, 29.2)
        return calm_text(img, t, 27.6, 29.15, 'SPREAD OUT', y=280, sz=104, hi=['SPREAD'])
    if n == 'S10b_landing': return calm_text(img, t, wt('feet', 29.5) - 0.2, 31.2, 'FEET FIRST', y=280, sz=110, hi=['FEET'])
    if n == 'S12a_fuselage': return calm_text(img, t, wt('1972', 32.5) - 0.1, 35.15, ['1972', 'VESNA VULOVIĆ'], y=260, sz=92, hi=['1972'])
    if n == 'S12b_fuselage_wide': return record_bars(img, t, 35.2, 38.46, False)
    if n == 'S13_wreck':
        T_S = wt('survived', 40.5) - 0.1
        if t > T_S:
            la = E.lineart(img, GO, 0.18); p = ss((t - T_S) / 0.5); sy = int(H * p)
            arr = np.asarray(img).copy(); arr[:sy] = np.asarray(la)[:sy]
            if p < 1: arr[max(0, sy - 5):sy + 5] = np.clip(arr[max(0, sy - 5):sy + 5].astype(np.int32) + np.array([255, 210, 120]), 0, 255)
            img = Image.fromarray(arr)
        img = calm_text(img, t, wt('snowy', 38.8) - 0.1, 40.6, 'SNOWY, WOODED SLOPE', y=280, sz=80, hi=['SNOWY,', 'SNOWY'])
        return stamp(img, t, T_S + 0.1, 42.0, 'SURVIVED', col=GRN, rot=-4, cy=1320)
    if n == 'S14_seats_fall':
        img = calm_text(img, t, 42.1, 44.4, ['1971', 'JULIANE KOEPCKE'], y=260, sz=92, hi=['1971'])
        return record_bars(img, t, 44.3, 46.24, True)
    if n == 'S15_jungle_floor': return days_counter(light_rays(img, t), t, 46.4, 49.98)
    if n == 'S16_end': return calm_text(img, t, 50.05, END_T - 0.3, ['WHERE WOULD', 'YOU LAND?'], y=260, sz=100, hi=['LAND?'])
    return img
F0 = None
def frame_at(i):
    global F0
    t = i / FPS; img = seg(t)
    if t > END_T - 0.3:
        if F0 is None: F0 = seg(0.0)
        img = Image.blend(img, F0, ss((t - (END_T - 0.3)) / 0.3))
    return img
if __name__ == '__main__':
    if sys.argv[1] == 'frames':
        SINGLE = True; globals()['SINGLE'] = True
        os.makedirs('/tmp/gv/plane/test', exist_ok=True)
        for s_ in sys.argv[2:]:
            t = float(s_); frame_at(int(round(t * FPS))).save(f'/tmp/gv/plane/test/f_{t:06.2f}.jpg', quality=85)
    else:
        i0, i1 = map(int, sys.argv[2].split('-')); i1 = min(i1, NF)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', sys.argv[3]], stdin=subprocess.PIPE)
        for i in range(i0, i1):
            p.stdin.write(frame_at(i).tobytes())
            if i % 60 == 0: print('frame', i, flush=True)
        p.stdin.close(); p.wait()
