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
TJ = json.load(open('/tmp/gv/ss/timing.json')); WORDS = TJ['words']
def wt(word, after=0.0):
    for w in WORDS:
        if w['start'] >= after - 1e-6 and w['word'].strip('.,?!').lower() == word.lower(): return w['start']
    raise KeyError(word)
END_T = 50.83; NF = int(round(END_T * FPS))
def GF(t): return int(round(t * FPS)) + 1
SHOT_T = [('S01_hook', 0.0, 3.46), ('S02_stops', 3.46, 6.24), ('S03_see', 6.24, 11.00), ('S04_step', 11.00, 12.50), ('S05_accel', 12.50, 19.56),
          ('S07_wall', 19.56, 21.62), ('S08_heat', 21.62, 24.16), ('S09_boom', 24.16, 27.74), ('S10_lake', 27.74, 31.12), ('S11_starving', 31.12, 32.90),
          ('S12_food', 32.90, 39.51), ('S15_bench', 40.58, 50.83)]
SHOTS = {n: (GF(a), GF(b) - 1) for n, a, b in SHOT_T}
SRC = os.environ.get('SS_SRC', '/tmp/gv/ss/shots')
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


# ---------------- neon overlays (super speed) ----------------
def streaks(img, t, k, n=26, vertical=False):
    if k <= 0: return img
    rr = random.Random(int(t * 30)); lay = E.new_lay(); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = rr.uniform(0, W); y = rr.uniform(0, H); L_ = rr.uniform(160, 420)
        if vertical: d.line((x, y, x, y - L_), fill=(230, 245, 255, int(110 * k)), width=rr.choice((2, 3, 4)))
        else: d.line((x, y, x + L_, y + L_ * 0.05), fill=(230, 245, 255, int(110 * k)), width=rr.choice((2, 3, 4)))
    return E.glow_add(img, lay, 1.0, 6)
def big_hook(img, t):
    """frame-0 hook: two huge words, fully visible from frame 0, settle slightly"""
    if t > 3.4: return img
    k = ss((3.4 - t) / 0.25)
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    for txt, y, sz, col in (('1000X', 230, 240, YEL), ('FASTER', 470, 150, WHT)):
        f = E.font(sz); w = d.textbbox((0, 0), txt, font=f, stroke_width=14)[2]
        d.text((W / 2 - w / 2, y), txt, font=f, fill=col + (int(255 * k),), stroke_width=14, stroke_fill=(0, 0, 0, int(255 * k)))
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')
SUN_P = (230, 560); EYE_P = (820, 560)
def light_check(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.8, 300, 900, dim=0.5)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    R = 80; d.ellipse((SUN_P[0] - R, SUN_P[1] - R, SUN_P[0] + R, SUN_P[1] + R), fill=YEL + (al,))
    for i in range(12):
        ang = i * math.pi / 6 + t * 0.4
        d.line((SUN_P[0] + math.cos(ang) * (R + 18), SUN_P[1] + math.sin(ang) * (R + 18), SUN_P[0] + math.cos(ang) * (R + 50), SUN_P[1] + math.sin(ang) * (R + 50)), fill=YEL + (al,), width=8)
    x, y = EYE_P; w_, h_ = 140, 80
    top = [(x - w_ + 2 * w_ * i / 40, y - h_ * math.sin(math.pi * i / 40)) for i in range(41)]
    bot = [(x - w_ + 2 * w_ * i / 40, y + h_ * math.sin(math.pi * i / 40)) for i in range(41)]
    d.line(top, fill=WHT + (al,), width=9, joint='curve'); d.line(bot, fill=WHT + (al,), width=9, joint='curve')
    d.ellipse((x - 52, y - 52, x + 52, y + 52), outline=CYN + (al,), width=11); d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(230, 230, 230, al))
    for i in range(7):
        u = ((t - a) * 0.9 + i / 7) % 1
        px = lerp(SUN_P[0] + 100, x - w_ - 10, u); py = SUN_P[1]
        d.ellipse((px - 12, py - 12, px + 12, py + 12), fill=YEL + (al,))
    tk = ss((t - wt('see', 9.5)) / 0.25) * k
    if tk > 0:
        cx, cy = 540, 800
        d.line([(cx - 60, cy), (cx - 15, cy + 45), (cx + 70, cy - 55)], fill=GRN + (int(255 * tk),), width=24, joint='curve')
    return E.glow_add(img, lay, 1.5, 16)
def counter(img, t, a, b, t0, t1, v1, unit, sub=None, y=470, col=YEL, fmt='{:,}'):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.55, 300, 820, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    v = int(v1 * eout((t - t0) / (t1 - t0))) if t > t0 else 0
    E.text_center(d, (540, y), fmt.format(v), 190, WHT + (int(255 * k),))
    E.text_center(d, (540, y + 150), unit, 84, col + (int(255 * k),))
    if sub: E.text_center(d, (540, y + 240), sub, 52, WHT + (int(220 * k * ss((t - t1) / 0.3)),))
    E.wavy(d, 380, 700, y + 205, col, cl((t - t1) / 0.4) * k)
    return E.glow_add(img, lay, 1.5, 16)
def thermo(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.25)
    if k <= 0: return img
    img = dim_region(img, k * 0.7, 300, 1350, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    x, y0, y1 = 860, 420, 1180
    d.rounded_rectangle((x - 34, y0, x + 34, y1), 34, outline=WHT + (al,), width=8)
    d.ellipse((x - 62, y1 - 30, x + 62, y1 + 94), outline=WHT + (al,), width=8)
    t0 = wt('heats', 21.8); temp = lerp(20, 600, eout((t - t0) / 1.6)) if t > t0 else 20
    fill = cl(temp / 700.0)
    col = tuple(int(lerp(c1, c2, fill)) for c1, c2 in zip((255, 200, 80), (255, 60, 30)))
    d.ellipse((x - 46, y1 - 14, x + 46, y1 + 78), fill=col + (al,))
    yl = y1 - (y1 - y0 - 30) * fill; d.rounded_rectangle((x - 18, yl, x + 18, y1 + 10), 18, fill=col + (al,))
    yo = y1 - (y1 - y0 - 30) * (250 / 700.0)
    d.line((x - 300, yo, x - 46, yo), fill=CYN + (al,), width=6)
    d.text((x - 330, yo - 70), 'OVEN 250°C', font=E.font(48), fill=CYN + (al,), stroke_width=5, stroke_fill=(0, 0, 0, al))
    E.text_center(d, (x - 40, y1 + 170), f'{int(temp)}°C', 110, ORA + (al,))
    return E.glow_add(img, lay, 1.5, 16)
def day_icons(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.6, 300, 900, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    t0 = wt('eight', 36.6)
    for i in range(8):
        kk = ss((t - t0 - i * 0.12) / 0.2) * k
        if kk <= 0: continue
        cx = 180 + (i % 4) * 240; cy = 480 + (i // 4) * 230
        d.rounded_rectangle((cx - 85, cy - 80, cx + 85, cy + 80), 18, outline=YEL + (int(255 * kk),), width=7, fill=(20, 15, 0, int(120 * kk)))
        d.rectangle((cx - 85, cy - 80, cx + 85, cy - 45), fill=RED + (int(220 * kk),))
        E.text_center(d, (cx, cy + 18), str(i + 1), 80, WHT + (int(255 * kk),))
    E.text_center(d, (540, 900), 'DAYS OF FOOD', 80, YEL + (int(255 * k * ss((t - t0 - 1.0) / 0.3)),))
    return E.glow_add(img, lay, 1.4, 14)
def year_ring(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.7, 250, 1150, dim=0.5)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    cx, cy, R = 540, 640, 250
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(40, 60, 90, al), width=16)
    t0 = wt('three', 43.0) - 0.4; u = eout((t - t0) / 1.2) if t > t0 else 0
    d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * u, fill=CYN + (al,), width=20)
    E.text_center(d, (cx, cy - 30), f'{2.7 * u:.1f}', 190, WHT + (al,))
    E.text_center(d, (cx, cy + 105), 'YEARS', 70, CYN + (al,))
    E.text_center(d, (cx, cy - R - 70), '1 DAY FOR THEM =', 64, WHT + (al,))
    return E.glow_add(img, lay, 1.5, 16)

# ---------------- timeline ----------------
def seg(t):
    n = which(t)
    if n is None:   # 'And it gets worse' (39.51 - 40.58)
        img = plate(shot('S12_food', 39.4), dim=0.35)
        img = calm_text(img, t, 39.53, 40.56, 'AND IT GETS', y=760, sz=100)
        return calm_text(img, t, wt('worse', 40.0) - 0.05, 40.56, 'WORSE', y=900, sz=200, hi=['WORSE'])
    img = shot(n, t)
    if n == 'S01_hook': return big_hook(streaks(img, t, 0.8), t)
    if n == 'S02_stops': return calm_text(img, t, wt('world', 4.0) - 0.2, 6.2, ['THE WORLD', 'ALMOST STOPS'], y=260, sz=96, hi=['STOPS'])
    if n == 'S03_see':
        img = calm_text(img, t, 6.3, 8.25, ['UNLIKE', 'FROZEN TIME...'], y=260, sz=96, hi=['FROZEN'])
        img = light_check(img, t, 8.25, 10.96)
        return calm_text(img, t, wt('see', 9.8) - 0.1, 10.96, 'YOU CAN SEE', y=930, sz=100, hi=['SEE'], hicol=GRN)
    if n == 'S04_step': return img
    if n == 'S05_accel':
        img = streaks(img, t, ss((t - 13.5) / 1.5) * 0.9)
        if t < 17.48: return counter(img, t, 12.6, 17.45, wt('five', 15.0) - 0.2, wt('kilometres', 16.0) + 0.3, 5000, 'KM/H')
        img = calm_text(img, t, 17.5, 19.5, 'MACH 4', y=320, sz=190, hi=['4'])
        return calm_text(img, t, 17.75, 19.5, '4X THE SPEED OF SOUND', y=560, sz=60)
    if n == 'S07_wall': return calm_text(streaks(img, t, 0.6), t, wt('air', 19.7) - 0.1, 21.58, 'AIR = WALL', y=290, sz=120, hi=['WALL'])
    if n == 'S08_heat': return thermo(img, t, 21.66, 24.12)
    if n == 'S09_boom': return stamp(img, t, wt('sonic', 25.0) - 0.15, 27.7, 'SONIC', 'BOOM', cy=1250)
    if n == 'S10_lake': return calm_text(img, t, wt('without', 29.5) - 0.2, 31.08, 'NO SINKING', y=290, sz=110, hi=['NO'])
    if n == 'S11_starving': return calm_text(img, t, wt('starving', 31.5) - 0.2, 32.86, 'STARVING', y=290, sz=130, hi=['STARVING'], hicol=RED)
    if n == 'S12_food':
        if t < 36.34: return counter(img, t, 33.0, 36.3, wt('sixteen', 34.0) - 0.2, wt('calories', 35.0) + 0.2, 16000, 'CALORIES', y=420, col=ORA)
        return day_icons(img, t, 36.36, 39.48)
    if n == 'S15_bench':
        if t < 45.24: return year_ring(img, t, 40.62, 45.2)
        if t < 48.20:
            img = calm_text(img, t, wt('blinks', 45.5) - 0.1, 47.1, 'ONE BLINK...', y=280, sz=100)
            return calm_text(img, t, wt('old', 47.0) - 0.1, 48.16, 'OLD.', y=280, sz=170, hi=['OLD.'])
        return calm_text(img, t, 48.25, END_T - 0.3, ['STILL WANT', 'SUPER SPEED?'], y=260, sz=100, hi=['SPEED?'])
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
        os.makedirs('/tmp/gv/ss/test', exist_ok=True)
        for s_ in sys.argv[2:]:
            t = float(s_); frame_at(int(round(t * FPS))).save(f'/tmp/gv/ss/test/f_{t:06.2f}.jpg', quality=85)
    else:
        i0, i1 = map(int, sys.argv[2].split('-')); i1 = min(i1, NF)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', sys.argv[3]], stdin=subprocess.PIPE)
        for i in range(i0, i1):
            p.stdin.write(frame_at(i).tobytes())
            if i % 60 == 0: print('frame', i, flush=True)
        p.stdin.close(); p.wait()
