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

