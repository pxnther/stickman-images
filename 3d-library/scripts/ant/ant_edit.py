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
TJ = json.load(open('/tmp/gv/ant/timing.json')); WORDS = TJ['words']
def wt(word, after=0.0):
    for w in WORDS:
        if w['start'] >= after - 1e-6 and w['word'].strip('.,?!').lower() == word.lower(): return w['start']
    raise KeyError(word)
END_T = 46.02; NF = int(round(END_T * FPS))
def GF(t): return int(round(t * FPS)) + 1
SHOT_T = [('A01_hook', 0.0, 2.48), ('A02_splash', 2.48, 6.48), ('A03_edge', 6.48, 8.56), ('A04_fall', 8.56, 11.92), ('A05_land', 11.92, 14.28),
          ('A06_rain', 14.28, 21.96), ('A08_blur', 21.96, 24.68), ('A09_lab', 24.68, 28.68), ('A10_shout', 28.68, 35.22), ('A12_cold', 35.22, 41.76),
          ('A14_back', 41.76, 46.02)]
SHOTS = {n: (GF(a), GF(b) - 1) for n, a, b in SHOT_T}
SRC = os.environ.get('ANT_SRC', '/tmp/gv/ant/shots')
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


# ---------------- neon overlays (ant size) ----------------
def big_hook(img, t):
    """frame-0 hook: 'ANT SIZE' on one line, fully visible from frame 0, above the falling drop"""
    if t > 2.4: return img
    k = ss((2.4 - t) / 0.25)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); f = E.font(170)
    parts = (('ANT', YEL), ('SIZE', WHT)); ws = [d.textbbox((0, 0), p, font=f, stroke_width=16)[2] for p, _ in parts]
    x = W / 2 - (sum(ws) + 40) / 2
    for (p, col), w in zip(parts, ws):
        d.text((x, 235), p, font=f, fill=col + (int(255 * k),), stroke_width=16, stroke_fill=(0, 0, 0, int(255 * k))); x += w + 40
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')
def stick_icon(d, x, y, s, col, al, w=None):
    """simple stickman icon, feet at (x, y), height s"""
    w = w or max(3, int(s / 14)); hr = s * 0.13
    d.ellipse((x - hr, y - s, x + hr, y - s + 2 * hr), outline=col + (al,), width=w)
    d.line((x, y - s + 2 * hr, x, y - s * 0.42), fill=col + (al,), width=w)
    d.line((x, y - s * 0.42, x - s * 0.16, y), fill=col + (al,), width=w); d.line((x, y - s * 0.42, x + s * 0.16, y), fill=col + (al,), width=w)
    d.line((x - s * 0.2, y - s * 0.62, x, y - s * 0.72), fill=col + (al,), width=w); d.line((x + s * 0.2, y - s * 0.62, x, y - s * 0.72), fill=col + (al,), width=w)
def scale_piece(img, t, a, b, bg):
    """balance scale: a single coffee drop slams its side down against the tiny stickman, '100X HEAVIER'"""
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.4)
    img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    cx, cy = 540, 1020
    tilt = math.radians(16) * eout((t - a - 0.35) / 0.7)
    # fulcrum
    d.polygon([(cx, cy), (cx - 90, cy + 300), (cx + 90, cy + 300)], outline=CYN + (al,), width=8)
    d.line((cx - 200, cy + 300, cx + 200, cy + 300), fill=CYN + (al,), width=8)
    L = 360
    lx, ly = cx - L * math.cos(tilt), cy - L * math.sin(tilt) * -1
    rx, ry = cx + L * math.cos(tilt), cy + L * math.sin(tilt) * -1
    lx, ly = cx - L * math.cos(tilt), cy + L * math.sin(tilt)
    rx, ry = cx + L * math.cos(tilt), cy - L * math.sin(tilt)
    d.line((lx, ly, rx, ry), fill=WHT + (al,), width=10)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=CYN + (al,))
    for px, py in ((lx, ly), (rx, ry)):
        d.line((px, py, px - 110, py + 170), fill=WHT + (al,), width=5); d.line((px, py, px + 110, py + 170), fill=WHT + (al,), width=5)
        d.arc((px - 130, py + 110, px + 130, py + 230), 0, 180, fill=WHT + (al,), width=8)
    # left pan (heavy, goes down): the coffee drop; right pan (light, goes up): the tiny stickman
    dr = 105; dx, dy = lx, ly + 170 - dr - 4
    d.ellipse((dx - dr, dy - dr * 0.95, dx + dr, dy + dr), fill=(120, 62, 22, al), outline=ORA + (al,), width=7)
    d.polygon([(dx - dr * 0.55, dy - dr * 0.75), (dx, dy - dr * 1.75), (dx + dr * 0.55, dy - dr * 0.75)], fill=(120, 62, 22, al))
    d.ellipse((dx - 45, dy - 50, dx - 15, dy - 20), fill=(255, 230, 200, int(200 * k)))
    stick_icon(d, rx, ry + 168, 46, WHT, al, 5)
    kt = ss((t - a - 0.8) / 0.3) * k
    E.text_center(d, (540, 520), '100X', 230, YEL + (int(255 * kt),))
    E.text_center(d, (540, 690), 'HEAVIER THAN YOU', 76, WHT + (int(255 * kt),))
    E.wavy(d, 300, 780, 760, YEL, cl((t - a - 1.0) / 0.4) * k)
    return E.glow_add(img, lay, 1.4, 14)
def storey_counter(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.6, 260, 900, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    t0 = wt('hundred-storey', 10.0) - 0.15; u = eout((t - t0) / 1.0) if t > t0 else 0.0
    E.text_center(d, (540, 430), f'{int(round(100 * u))}', 220, WHT + (al,))
    E.text_center(d, (540, 600), 'STOREYS', 90, YEL + (al,))
    E.text_center(d, (540, 700), 'THAT\'S HOW HIGH THE TABLE IS TO YOU', 42, WHT + (int(230 * k * ss((t - t0 - 0.9) / 0.3)),))
    E.wavy(d, 360, 720, 655, YEL, cl((t - t0 - 0.8) / 0.4) * k)
    # little skyscraper outline growing on the right
    x0, yb = 900, 900; hgt = 520 * u
    if hgt > 4:
        d.rectangle((x0 - 55, yb - hgt, x0 + 55, yb), outline=CYN + (al,), width=6)
        for j in range(int(hgt // 26)):
            yy = yb - 14 - j * 26; d.line((x0 - 35, yy, x0 + 35, yy), fill=CYN + (int(120 * k),), width=3)
    return E.glow_add(img, lay, 1.5, 16)
def blur_pov(img, t, a, b):
    k = ss((t - a) / (b - a))
    if k <= 0: return img
    return img.filter(ImageFilter.GaussianBlur(2 + 26 * k))
def label(d, x, y, tx, ty, text, col, al, sz=54):
    d.line((x, y, tx, ty), fill=col + (al,), width=5); d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=col + (al,))
    f = E.font(sz); w = d.textbbox((0, 0), text, font=f, stroke_width=6)[2]
    bx = tx - w / 2 - 22; by = ty - 44 if ty < y else ty
    d.rounded_rectangle((bx, by - 6, bx + w + 44, by + sz + 22), 22, fill=(5, 10, 25, int(al * 0.8)), outline=col + (al,), width=4)
    d.text((bx + 22, by + 2), text, font=f, fill=WHT + (al,))
LAB_HAIR = (540, 820); LAB_PUPIL = (720, 980)       # measured on the lab render (set in measure step)
def lab_labels(img, t):
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    k1 = ss((t - (wt('hair', 26.0) - 0.35)) / 0.25) * ss((26.62 - t) / 0.2)
    if k1 > 0:
        al = int(255 * k1)
        px = lerp(760, 560, cl((t - 25.9) / 0.7))
        label(d, 300, 900, 400, 600, 'HAIR  70 µm', WHT, al)
        label(d, px, 975, 560, 1260, 'YOUR PUPIL  7 µm', CYN, al)
    return E.glow_add(img, lay, 1.2, 10)
def hearing_chart(img, t, a, b, bg):
    """log frequency bar: human hearing 20 Hz - 20 kHz, his voice as rings flying off the top at ~50-100 kHz"""
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.4)
    img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    x = 330; y0, y1 = 1400, 380                        # bottom = 10 Hz, top = 200 kHz (log)
    def fy(fz): return y0 + (y1 - y0) * (math.log10(fz) - 1) / (math.log10(200000) - 1)
    d.line((x, y0, x, y1), fill=WHT + (al,), width=6)
    for fz, lab in ((20, '20 Hz'), (200, '200 Hz'), (2000, '2 kHz'), (20000, '20 kHz'), (100000, '100 kHz')):
        yy = fy(fz); d.line((x - 18, yy, x + 18, yy), fill=WHT + (al,), width=5)
        d.text((x - 250, yy - 28), lab, font=E.font(46), fill=WHT + (al,))
    hk = ss((t - a - 0.2) / 0.5) * k
    d.rounded_rectangle((x + 40, fy(20000), x + 150, fy(20)), 24, fill=(40, 200, 120, int(90 * hk)), outline=GRN + (int(255 * hk),), width=6)
    d.text((x + 175, (fy(20) + fy(20000)) / 2 - 70), 'HUMANS', font=E.font(64), fill=GRN + (int(255 * hk),))
    d.text((x + 175, (fy(20) + fy(20000)) / 2 + 5), 'CAN HEAR', font=E.font(52), fill=WHT + (int(230 * hk),))
    # the voice: rings rising from the bottom of the chart up past the human band
    vk = ss((t - wt('voice', 32.8)) / 0.3) * k
    yv = fy(70000)
    for i in range(4):
        u = ((t - a) * 0.7 + i / 4) % 1
        r = 30 + 70 * u; cy_ = lerp(fy(400), yv, eout(cl((t - wt('voice', 32.8)) / 0.9)))
        d.ellipse((x + 95 - r, cy_ - r * 0.5, x + 95 + r, cy_ + r * 0.5), outline=CYN + (int(255 * vk * (1 - u)),), width=6)
    if vk > 0:
        d.text((x + 175, yv - 40), 'YOUR VOICE', font=E.font(60), fill=CYN + (int(255 * vk),))
    tk = ss((t - wt('high', 33.5)) / 0.3) * k
    E.text_center(d, (540, 1560), 'TOO HIGH TO HEAR', 88, YEL + (int(255 * tk),))
    E.wavy(d, 250, 830, 1625, YEL, cl((t - wt('high', 33.5) - 0.2) / 0.4) * k)
    return E.glow_add(img, lay, 1.4, 14)
def thermal(img, k, cool):
    """thermal-camera look; cool 0..1 drains the heat (hot white/orange -> blue)"""
    if k <= 0: return img
    arr = np.asarray(img).astype(np.int16)
    g = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    hero = ((arr.min(2) > 150) & ((arr.max(2) - arr.min(2)) < 40)).astype(np.float32)
    hero[:int(H * 0.4)] = 0
    hero = cv2.GaussianBlur(cv2.dilate(hero, np.ones((5, 5), np.uint8)), (0, 0), 3)
    bgv = 0.12 + 0.25 * g
    hv = lerp(0.95, 0.42, cool) - 0.12 * (1 - g)
    g = np.clip(bgv * (1 - hero) + hv * hero, 0, 1)
    cm = cv2.applyColorMap((g * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)[..., ::-1]
    out = Image.blend(img, Image.fromarray(cm), k)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    temp = lerp(37.0, 31.0, cool)
    d.text((70, 260), 'THERMAL', font=E.font(48), fill=WHT + (al,))
    tc = (int(lerp(255, 120, cool)), int(lerp(140, 200, cool)), int(lerp(40, 255, cool)), al)
    d.text((70, 320), f'{temp:.1f}°C', font=E.font(96), fill=tc)
    return E.glow_add(out, lay, 1.0, 8)

STILLS = {}
def still(name, t):
    if (name, t) not in STILLS:
        a, b = SHOTS[name]; i = max(a, min(b, GF(t))) - a; path = f'{SRC}/{name}.mp4'
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{i}),scale={W}:{H}', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, stdin=subprocess.DEVNULL).stdout
        STILLS[(name, t)] = Image.frombytes('RGB', (W, H), raw[:W * H * 3])
    return STILLS[(name, t)].copy()
# ---------------- timeline ----------------
def seg(t):
    n = which(t)
    img = shot(n, t)
    if n == 'A01_hook': return big_hook(img, t)
    if n == 'A02_splash':
        if t >= wt('hundred', 4.0) - 0.3: return scale_piece(img, t, wt('hundred', 4.0) - 0.3, 6.45, still('A02_splash', 5.4))
        return img
    if n == 'A04_fall': return storey_counter(img, t, wt('hundred-storey', 10.0) - 0.4, 11.9)
    if n == 'A06_rain': return calm_text(img, t, wt('sticky', 19.0) - 0.25, 21.92, ["WATER WON'T", 'LET GO'], y=270, sz=100, hi=['GO'], hicol=CYN)
    if n == 'A08_blur':
        if t < 23.4: return blur_pov(img, t, 22.3, 23.4)
        return img
    if n == 'A09_lab':
        img = lab_labels(img, t)
        img = calm_text(img, t, wt('thinner', 25.4) - 0.2, 26.6, ['THINNER', 'THAN A HAIR'], y=270, sz=100, hi=['HAIR'])
        return calm_text(img, t, wt('light', 27.0) - 0.15, 28.64, ["LIGHT CAN'T", 'FOCUS'], y=270, sz=100, hi=['FOCUS'], hicol=ORA)
    if n == 'A10_shout':
        if t >= 32.66: return hearing_chart(img, t, 32.62, 35.2, still('A10_shout', 33.5))
        return img
    if n == 'A12_cold':
        if t < 37.82:
            tk = ss((t - (wt('cold', 35.8) - 0.1)) / 0.3) * ss((37.8 - t) / 0.2)
            return thermal(img, tk, ramp_(t, 36.0, 37.6))
        img = calm_text(img, t, wt('nothing', 37.8) - 0.1, 41.72, ['NOTHING', 'WARM-BLOODED', 'IS THIS SMALL'], y=250, sz=92, hi=['SMALL'])
        return calm_text(img, t, wt('know', 40.5) - 0.6, 41.72, 'SMALLEST MAMMAL 1.8 g  •  YOU 0.0006 g', y=600, sz=42)
    return img
def ramp_(t, a, b): return ss((t - a) / (b - a))
F0 = None
LOOP = 0.35
def frame_at(i):
    global F0
    t = i / FPS; img = seg(t)
    if t > END_T - LOOP:
        if F0 is None: F0 = seg(0.0)
        img = Image.blend(img, F0, ss((t - (END_T - LOOP)) / LOOP))
    return img
if __name__ == '__main__':
    if sys.argv[1] == 'frames':
        SINGLE = True; globals()['SINGLE'] = True
        os.makedirs('/tmp/gv/ant/test', exist_ok=True)
        for s_ in sys.argv[2:]:
            t = float(s_); frame_at(int(round(t * FPS))).save(f'/tmp/gv/ant/test/f_{t:06.2f}.jpg', quality=85)
    else:
        i0, i1 = map(int, sys.argv[2].split('-')); i1 = min(i1, NF)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', sys.argv[3]], stdin=subprocess.PIPE)
        for i in range(i0, i1):
            p.stdin.write(frame_at(i).tobytes())
            if i % 60 == 0: print('frame', i, flush=True)
        p.stdin.close(); p.wait()
