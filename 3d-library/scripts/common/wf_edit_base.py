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
VID = os.environ.get('VID', 'giant'); VD = f'/tmp/gv/{VID}'
TJ = json.load(open(f'{VD}/timing.json')); WORDS = TJ['words']
def wt(word, after=0.0, default=None):
    for w in WORDS:
        if w['start'] >= after - 1e-6 and w['word'].strip('.,?!:').lower() == word.lower(): return w['start']
    if default is not None: return default
    raise KeyError(word)
END_T = TJ['duration']; NF = int(round(END_T * FPS))
def GF(t): return int(round(t * FPS)) + 1
SHOT_T = [tuple(x) for x in json.load(open(f'{VD}/shots.json'))]
SHOTS = {n: (GF(a), GF(b) - 1) for n, a, b in SHOT_T}
SRC = os.environ.get('SRC', f'{VD}/shots')
TRK = json.load(open(f'{VD}/track.json')) if os.path.exists(f'{VD}/track.json') else {}
def trk(name, t, default=(0.5, 0.5)):
    d = TRK.get(name, {}); f = str(GF(t))
    if f in d and d[f]: return (d[f][0] * W, d[f][1] * H)
    ks = sorted(int(k) for k in d if d[k])
    if not ks: return (default[0] * W, default[1] * H)
    k = min(ks, key=lambda x: abs(x - GF(t))); return (d[str(k)][0] * W, d[str(k)][1] * H)
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

def stick_icon(d, x, y, s, col, al, w=None):
    """simple stickman icon, feet at (x, y), height s"""
    w = w or max(3, int(s / 14)); hr = s * 0.13
    d.ellipse((x - hr, y - s, x + hr, y - s + 2 * hr), outline=col + (al,), width=w)
    d.line((x, y - s + 2 * hr, x, y - s * 0.42), fill=col + (al,), width=w)
    d.line((x, y - s * 0.42, x - s * 0.16, y), fill=col + (al,), width=w); d.line((x, y - s * 0.42, x + s * 0.16, y), fill=col + (al,), width=w)
    d.line((x - s * 0.2, y - s * 0.62, x, y - s * 0.72), fill=col + (al,), width=w); d.line((x + s * 0.2, y - s * 0.62, x, y - s * 0.72), fill=col + (al,), width=w)
def label(d, x, y, tx, ty, text, col, al, sz=54):
    d.line((x, y, tx, ty), fill=col + (al,), width=5); d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=col + (al,))
    f = E.font(sz); w = d.textbbox((0, 0), text, font=f, stroke_width=6)[2]
    bx = tx - w / 2 - 22; by = ty - 44 if ty < y else ty
    d.rounded_rectangle((bx, by - 6, bx + w + 44, by + sz + 22), 22, fill=(5, 10, 25, int(al * 0.8)), outline=col + (al,), width=4)
    d.text((bx + 22, by + 2), text, font=f, fill=WHT + (al,))
def thermal(img, k, cool, top_cut=0.4, label=True, lo=150, sat=40):
    """thermal-camera look; cool 0..1 drains the heat (hot white/orange -> blue)"""
    if k <= 0: return img
    arr = np.asarray(img).astype(np.int16)
    g = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    hero = ((arr.min(2) > lo) & ((arr.max(2) - arr.min(2)) < sat)).astype(np.float32)
    hero[:int(H * top_cut)] = 0
    hero = cv2.GaussianBlur(cv2.dilate(hero, np.ones((5, 5), np.uint8)), (0, 0), 3)
    bgv = 0.12 + 0.25 * g
    hv = lerp(0.95, 0.42, cool) - 0.12 * (1 - g)
    g = np.clip(bgv * (1 - hero) + hv * hero, 0, 1)
    cm = cv2.applyColorMap((g * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)[..., ::-1]
    out = Image.blend(img, Image.fromarray(cm), k)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    temp = lerp(37.0, 31.0, cool)
    if label: d.text((70, 260), 'THERMAL', font=E.font(48), fill=WHT + (al,))
    tc = (int(lerp(255, 120, cool)), int(lerp(140, 200, cool)), int(lerp(40, 255, cool)), al)
    if label: d.text((70, 320), f'{temp:.1f}°C', font=E.font(96), fill=tc)
    return E.glow_add(out, lay, 1.0, 8)

STILLS = {}
def still(name, t):
    if (name, t) not in STILLS:
        a, b = SHOTS[name]; i = max(a, min(b, GF(t))) - a; path = f'{SRC}/{name}.mp4'
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{i}),scale={W}:{H}', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, stdin=subprocess.DEVNULL).stdout
        STILLS[(name, t)] = Image.frombytes('RGB', (W, H), raw[:W * H * 3])
    return STILLS[(name, t)].copy()
def ramp_(t, a, b): return ss((t - a) / (b - a))
def blur_k(img, k):
    return img if k <= 0 else img.filter(ImageFilter.GaussianBlur(2 + 26 * k))
def to_black(img, k):
    return img if k <= 0 else Image.blend(img, Image.new('RGB', (W, H), (0, 0, 0)), cl(k))
def counter_big(img, t, a, b, t0, t1, v1, unit, sub=None, y=430, col=None):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.6, y - 170, y + 330, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    u = eout((t - t0) / max(0.01, t1 - t0)) if t > t0 else 0.0
    E.text_center(d, (540, y), f'{int(round(v1 * u)):,}', 210, WHT + (al,))
    E.text_center(d, (540, y + 165), unit, 86, (col or YEL) + (al,))
    if sub: E.text_center(d, (540, y + 265), sub, 44, WHT + (int(230 * k * ss((t - t1) / 0.3)),))
    return E.glow_add(img, lay, 1.5, 16)
def hook_text(img, t, parts, y=235, sz=170, until=2.4):
    if t > until: return img
    k = ss((until - t) / 0.25)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); f = E.font(sz)
    ws = [d.textbbox((0, 0), p, font=f, stroke_width=16)[2] for p, _ in parts]
    x = W / 2 - (sum(ws) + 40 * (len(parts) - 1)) / 2
    for (p, col), w in zip(parts, ws):
        d.text((x, y), p, font=f, fill=col + (int(255 * k),), stroke_width=16, stroke_fill=(0, 0, 0, int(255 * k))); x += w + 40
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')
LOOP = 0.35; F0 = None
def frame_at(i):
    global F0
    t = i / FPS; img = seg(t)
    if t > END_T - LOOP:
        if F0 is None: F0 = seg(0.0)
        img = Image.blend(img, F0, ss((t - (END_T - LOOP)) / LOOP))
    return img
def main():
    global SINGLE
    if sys.argv[1] == 'frames':
        SINGLE = True; globals()['SINGLE'] = True
        os.makedirs(f'{VD}/test', exist_ok=True)
        for s_ in sys.argv[2:]:
            t = float(s_); frame_at(int(round(t * FPS))).save(f'{VD}/test/f_{t:06.2f}.jpg', quality=85)
    else:
        i0, i1 = map(int, sys.argv[2].split('-')); i1 = min(i1, NF)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', sys.argv[3]], stdin=subprocess.PIPE)
        for i in range(i0, i1):
            p.stdin.write(frame_at(i).tobytes())
            if i % 60 == 0: print('frame', i, flush=True)
        p.stdin.close(); p.wait()
