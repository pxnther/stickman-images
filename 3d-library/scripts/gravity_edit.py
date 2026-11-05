"""What If Gravity Turned Off for 5 Seconds? - 9:16 Short editor (Blender 3D shots + neon pieces)."""
import json, math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageChops
import cv2

W, H, FPS = 1080, 1920, 30
T = json.load(open('/tmp/gv/timing.json'))
ST = {int(k): v for k, v in T['start'].items()}
WD = {int(k): v for k, v in T['words'].items()}
END_T = T['end'] + 0.5
NF = int(round(END_T * FPS))
PTS = {int(k): v for k, v in json.load(open('/tmp/gv/points.json')).items()}
FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
BG = (7, 9, 18)
CYN = (60, 220, 255); GO = (255, 196, 60); YEL = (255, 214, 0); RED = (255, 70, 70); ORA = (255, 140, 40)
GRN = (80, 255, 150); WHT = (255, 255, 255); BLU = (60, 150, 255)
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = cl(x); return x * x * (3 - 2 * x)
def eout(x): x = cl(x); return 1 - (1 - x) ** 3
def eback(x):
    c = 1.9; x = cl(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, u): return a + (b - a) * u
def wt(n, word, k=1):
    c = 0
    for w, t in WD[n]:
        if w == word:
            c += 1
            if c == k: return t
    raise KeyError((n, word))
FCACHE = {}
def font(sz):
    if sz not in FCACHE: FCACHE[sz] = ImageFont.truetype(FONT, int(sz))
    return FCACHE[sz]

# ---------------- grid + glow helpers ----------------
def _grid():
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    for x in range(30, W, 60):
        for y in range(30, H, 60): d.point((x, y), fill=(28, 34, 58))
    return im
GRID = _grid()
def glow_add(base, lay, strength=1.5, rad=16):
    """additive glow of RGBA layer onto RGB base"""
    sm = lay.resize((W // 3, H // 3), Image.BILINEAR).filter(ImageFilter.GaussianBlur(rad / 3)).resize((W, H), Image.BILINEAR)
    a = np.asarray(base, np.float32)
    g = np.asarray(sm, np.float32); l = np.asarray(lay, np.float32)
    a += g[..., :3] * (g[..., 3:4] / 255) * strength
    a = a * (1 - l[..., 3:4] / 255) + l[..., :3] * (l[..., 3:4] / 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def new_lay(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def text_center(d, xy, s, sz, fill, stroke=0, sfill=(0, 0, 0)):
    f = font(sz); bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text((xy[0] - w / 2 - bb[0], xy[1] - h / 2 - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return w, h
def wavy(d, x0, x1, y, col, p, width=9, amp=7):
    if p <= 0: return
    xe = x0 + (x1 - x0) * p; pts = []
    x = x0
    while x <= xe:
        pts.append((x, y + amp * math.sin((x - x0) / 26.0))); x += 6
    if len(pts) > 1: d.line(pts, fill=col + (255,), width=width, joint='curve')

# ---------------- video readers ----------------
SHOT_RANGE = {}
for f, p in PTS.items():
    s = p['shot']
    SHOT_RANGE.setdefault(s, [f, f]); SHOT_RANGE[s][0] = min(SHOT_RANGE[s][0], f); SHOT_RANGE[s][1] = max(SHOT_RANGE[s][1], f)
SRCDIR = '/tmp/gv/shots'
class Reader:
    def __init__(s, path): s.path = path; s.p = None; s.i = -1; s.last = None
    def get(s, i):
        if s.p is None or i < s.i:
            if s.p: s.p.kill()
            s.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', s.path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                   stdout=subprocess.PIPE, stdin=subprocess.DEVNULL); s.i = -1
        while s.i < i:
            b = s.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            s.last = b; s.i += 1
        return Image.frombytes('RGB', (W, H), s.last)
READ = {}; ONE = {}
SINGLE = False
def shot_frame(name, gf):
    """frame of a Blender shot at GLOBAL frame number gf (1-based)"""
    a, b = SHOT_RANGE[name]; gf = max(a, min(b, gf)); i = gf - a
    path = f'{SRCDIR}/{name}.mp4'
    if SINGLE and False:
        pass
    if SINGLE:
        k = (name, i)
        if k not in ONE:
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{i})', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                 capture_output=True, stdin=subprocess.DEVNULL).stdout
            ONE[k] = Image.frombytes('RGB', (W, H), raw[:W * H * 3]) if len(raw) >= W * H * 3 else Image.new('RGB', (W, H))
        return ONE[k].copy()
    key = name
    if key not in READ: READ[key] = Reader(path)
    return READ[key].get(i).copy()
def GF(t): return int(round(t * FPS)) + 1
MREAD = {}
def whiten(name, gf, img):
    """lift the stickman towards white using the Workbench mask render (body only, no outline, no eyes)"""
    path = f'{SRCDIR}/{name}_mask.mp4'
    if not os.path.exists(path): return img
    a, b = SHOT_RANGE[name]; gf = max(a, min(b, gf)); i = gf - a
    if SINGLE:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'select=eq(n\\,{i}),scale={W}:{H}', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                             capture_output=True, stdin=subprocess.DEVNULL).stdout
        if len(raw) < W * H: return img
        m = np.frombuffer(raw[:W * H], np.uint8).reshape(H, W)
    else:
        if name in MREAD and i < MREAD[name][1]:
            MREAD[name][0].kill(); del MREAD[name]
        if name not in MREAD:
            MREAD[name] = [subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                                            stdout=subprocess.PIPE, stdin=subprocess.DEVNULL), -1, None]
        r = MREAD[name]
        while r[1] < i:
            bb = r[0].stdout.read(W * H)
            if len(bb) < W * H: break
            r[2] = bb; r[1] += 1
        if r[2] is None: return img
        m = np.frombuffer(r[2], np.uint8).reshape(H, W)
    m = cv2.erode(m, np.ones((3, 3), np.uint8)).astype(np.float32) / 255.0
    m = np.clip((m - 0.35) / 0.4, 0, 1)[..., None]
    arr = np.asarray(img, np.float32)
    lum = arr.mean(axis=2, keepdims=True)
    lifted = 255 - (255 - lum) * 0.42                      # brighter, still shaded
    lifted = lifted * np.array([0.985, 0.99, 1.0])         # neutral cool white
    arr = arr * (1 - m * 0.92) + lifted * (m * 0.92)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
ZOOM = {'SH15_frozen': (1.32, 560, 760), 'SH17_drop': (1.38, 520, 720)}
def bframe(name, t):
    img = shot_frame(name, GF(t))
    if name != 'SH08_car': img = whiten(name, GF(t), img)
    if name in ZOOM:
        z, cx, cy = ZOOM[name]; w, h = W / z, H / z
        img = img.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((W, H), Image.LANCZOS)
    return img
def pt(t, key):
    f = GF(t)
    while f not in PTS and f > 1: f -= 1
    return PTS[f][key]

# ---------------- line art ----------------
def lineart(img, col=GO, fill=0.17, gain=1.0):
    g = np.asarray(ImageOps.autocontrast(img.convert('L'), cutoff=1), np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 2.2)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    e = np.clip((mag - 40) / 70, 0, 1) * 1.6; e = np.clip(e, 0, 1) ** 0.8 * gain
    lay = np.zeros((H, W, 4), np.float32); lay[..., :3] = col; lay[..., 3] = e * 255
    base = np.asarray(GRID, np.float32) * (1 - fill) + np.asarray(img, np.float32) * fill * np.array([0.6, 0.55, 0.5])
    return glow_add(Image.fromarray(base.astype(np.uint8)), Image.fromarray(lay.astype(np.uint8), 'RGBA'), 1.6, 14)

# ---------------- callouts ----------------
def callout(img, t, a, b, words, hi=None, y=330, sz=96, col_hi=YEL):
    """keyword callout: words pop in 0.12 s apart, float, shrink out at end"""
    if t < a or t > b: return img
    lay = new_lay(); d = ImageDraw.Draw(lay)
    lines = words if isinstance(words, list) else [words]
    out = cl((b - t) / 0.22)
    k = 0
    for li, line in enumerate(lines):
        ws = line.split(' '); f = font(sz)
        widths = [d.textbbox((0, 0), w, font=f, stroke_width=10)[2] for w in ws]
        sp = sz * 0.28; tot = sum(widths) + sp * (len(ws) - 1); x = W / 2 - tot / 2
        yy = y + li * sz * 1.12 + 6 * math.sin(t * 2.2)
        for w, ww in zip(ws, widths):
            p = eback((t - a - 0.12 * k) / 0.22) * out
            if p > 0.01:
                col = col_hi if (hi and w.strip('?!.,') in hi) else WHT
                tmp = new_lay(); td = ImageDraw.Draw(tmp)
                td.text((x, yy), w, font=f, fill=col + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255))
                if p != 1:
                    cx, cy = x + ww / 2, yy + sz / 2
                    tmp = tmp.resize((max(1, int(W * p)), max(1, int(H * p))))
                    off = (int(cx - cx * p), int(cy - cy * p)); lay.alpha_composite(tmp, off)
                else: lay.alpha_composite(tmp)
            x += ww + sp; k += 1
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')

# ---------------- neon pieces ----------------
def ring_piece(t, a, b, n, label, sub=None, col=CYN, from_pt=None, to_iris=None):
    """countdown ring for 'second n' (fills n/5)"""
    img = GRID.copy(); lay = new_lay(); d = ImageDraw.Draw(lay)
    u = t - a; cx, cy, R = 540, 860, 300
    if from_pt is not None and u < 0.4:
        k = eout(u / 0.4); cx = lerp(from_pt[0], 540, k); cy = lerp(from_pt[1], 860, k); R = lerp(60, 300, k)
    red = (n == 5)
    c = RED if red else col
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(40, 60, 90, 255), width=18)
    p0 = (n - 1) / 5; p1 = n / 5
    p = lerp(p0, p1, eout((u - 0.15) / 0.6))
    if p > 0: d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * p, fill=c + (255,), width=22)
    ang = math.radians(-90 + 360 * p); hx, hy = cx + R * math.cos(ang), cy + R * math.sin(ang)
    d.ellipse((hx - 16, hy - 16, hx + 16, hy + 16), fill=WHT + (255,))
    pop = eback((u - 0.1) / 0.3)
    if pop > 0.02:
        tmp = new_lay(); td = ImageDraw.Draw(tmp)
        text_center(td, (cx, cy - 10), str(n), 300, WHT + (255,))
        if pop != 1:
            tmp = tmp.resize((int(W * pop), int(H * pop))); lay.alpha_composite(tmp, (int(cx - cx * pop), int(cy - cy * pop)))
        else: lay.alpha_composite(tmp)
    lp = eback((u - 0.3) / 0.3)
    if lp > 0.02:
        text_center(d, (540, cy + R + 110), label, 92, WHT + (int(255 * cl(lp)),))
        if sub: text_center(d, (540, cy + R + 215), sub, 64, c + (int(255 * cl(lp)),))
        wavy(d, 330, 750, cy + R + 168, c, cl((u - 0.45) / 0.35))
    if red and u > 0.5:
        fl = 0.5 + 0.5 * math.sin(u * 25)
        d.ellipse((cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30), outline=RED + (int(120 * fl),), width=8)
    img = glow_add(img, lay, 1.7, 18)
    return img

def globe_lines(t, rot, R, cx, cy, tilt=math.radians(23.5)):
    """wireframe globe lines as list of (pts, front_mask)"""
    out = []
    def proj(lat, lon):
        x = math.cos(lat) * math.cos(lon + rot); y = math.sin(lat); z = math.cos(lat) * math.sin(lon + rot)
        y2 = y * math.cos(tilt) - z * math.sin(tilt); z2 = y * math.sin(tilt) + z * math.cos(tilt)
        return cx + R * x, cy - R * y2, z2
    for latd in range(-60, 61, 30):
        lat = math.radians(latd)
        out.append(([proj(lat, math.radians(l)) for l in range(0, 361, 6)], latd == 0))
    for lond in range(0, 360, 30):
        lon = math.radians(lond)
        out.append(([proj(math.radians(la), lon) for la in range(-90, 91, 6)], False))
    return out
def draw_globe(d, t, rot, R, cx, cy, col=BLU, alpha=1.0):
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=col + (int(200 * alpha),), width=5)
    for pts, eq in globe_lines(t, rot, R, cx, cy):
        for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
            fr = (z0 + z1) / 2 > 0
            c = (YEL if eq else col) + (int((235 if fr else 45) * alpha),)
            d.line((x0, y0, x1, y1), fill=c, width=4 if fr else 2)

def globe_speed(t, a, b):
    img = GRID.copy(); lay = new_lay(); d = ImageDraw.Draw(lay); u = t - a
    cx, cy, R = 540, 860, 330
    sp = 0.15 + 1.2 * ss(u / 1.6)
    draw_globe(d, t, u * sp, R * eback(u / 0.5), cx, cy)
    # speed streaks around the equator
    for i in range(14):
        ph = (u * 1.6 + i / 14) % 1
        y = cy - 40 + (i % 5 - 2) * 30
        x0 = cx - R - 120 + ph * (2 * R + 240)
        if abs(x0 - cx) < R * 0.96:
            d.line((x0, y, x0 + 70, y + 8), fill=CYN + (int(160 * math.sin(math.pi * ph)),), width=4)
    v = int(1670 * eout((u - 0.4) / 2.0))
    k = cl((u - 0.3) / 0.3)
    if k > 0:
        text_center(d, (540, 1360), f'{v:,}', 170, WHT + (int(255 * k),))
        text_center(d, (540, 1490), 'KM/H', 84, CYN + (int(255 * k),))
        wavy(d, 360, 720, 1550, YEL, cl((u - 2.4) / 0.4))
    text_center(d, (540, 380), 'EARTH STILL SPINS', 74, WHT + (int(255 * cl((u - 0.2) / 0.3)),))
    return glow_add(img, lay, 1.6, 16)

def stick_icon(d, x, y, s, col=WHT, a=255):
    """small neon stick figure standing with feet at (x,y)"""
    hr = 16 * s
    d.ellipse((x - hr, y - 95 * s - 2 * hr, x + hr, y - 95 * s), outline=col + (a,), width=int(5 * s) + 1)
    d.line((x, y - 95 * s, x, y - 45 * s), fill=col + (a,), width=int(5 * s) + 1)
    d.line((x, y - 45 * s, x - 18 * s, y), fill=col + (a,), width=int(5 * s) + 1)
    d.line((x, y - 45 * s, x + 18 * s, y), fill=col + (a,), width=int(5 * s) + 1)
    d.line((x - 26 * s, y - 70 * s, x, y - 82 * s, x + 26 * s, y - 70 * s), fill=col + (a,), width=int(5 * s) + 1)

def tangent_piece(t, a, b, t_away):
    """side view: Earth's curve, a straight arrow, the ground curving away under the figure"""
    img = GRID.copy(); lay = new_lay(); d = ImageDraw.Draw(lay); u = t - a
    Rc = 640; x0, ytop = 300, 1080; cx, cy = x0, ytop + Rc
    draw_in = eout(u / 0.6)
    d.arc((cx - Rc, cy - Rc, cx + Rc, cy + Rc), 270 - 60 * draw_in, 270 + 75 * draw_in, fill=BLU + (255,), width=12)
    g = ss((t - t_away) / 1.9) if t > t_away else 0.0
    fx = x0 + 470 * g; fy = ytop
    ap = eout((u - 0.6) / 0.8)
    if ap > 0:
        d.line((x0, ytop - 8, x0 + 640 * ap, ytop - 8), fill=CYN + (255,), width=10)
        xe = x0 + 640 * ap
        d.polygon([(xe + 36, ytop - 8), (xe - 4, ytop - 34), (xe - 4, ytop + 18)], fill=CYN + (255,))
        text_center(d, (x0 + 250, ytop - 300), 'STRAIGHT LINE', 58, CYN + (int(255 * ap),))
        d.line((x0 + 250, ytop - 260, x0 + 250, ytop - 30), fill=CYN + (int(120 * ap),), width=3)
    if g > 0:
        groundy = cy - math.sqrt(max(Rc * Rc - (fx - cx) ** 2, 0))
        d.line((fx, fy + 10, fx, groundy - 6), fill=YEL + (255,), width=9)
        d.line((fx - 22, groundy - 6, fx + 22, groundy - 6), fill=YEL + (255,), width=6)
        text_center(d, (fx + 120, (fy + groundy) / 2), 'GAP', 70, YEL + (int(255 * cl(g * 3)),))
        d.arc((cx - Rc, cy - Rc, cx + Rc, cy + Rc), 270, 270 + 47 * g, fill=YEL + (int(220 * g),), width=14)
    stick_icon(d, fx, fy - 12, 2.2, WHT)
    title = 'GOING STRAIGHT' if t < t_away + 0.2 else 'GROUND CURVES AWAY'
    k = cl((u - 0.2) / 0.3) if t < t_away else cl((t - t_away - 0.1) / 0.3)
    text_center(d, (510, 420), title, 72, WHT + (int(255 * k),))
    wavy(d, 300, 720, 480, CYN if t < t_away else YEL, cl(k * 1.3 - 0.3))
    return glow_add(img, lay, 1.6, 16)

def atmo_piece(t, a, b):
    img = GRID.copy(); lay = new_lay(); d = ImageDraw.Draw(lay); u = t - a
    cx, cy, R = 540, 980, 300
    draw_globe(d, t, u * 0.4, R * eback(u / 0.45), cx, cy)
    rr = random.Random(5)
    for i in range(140):
        ang = rr.uniform(0, 2 * math.pi); sp = rr.uniform(0.6, 1.4); ph = rr.uniform(0, 1)
        k = ((u * 0.45 * sp + ph) % 1.0) * cl((u - 0.3) / 0.5)
        r0 = R + 18 + k * 520
        x, y = cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)
        l = 18 + 40 * k
        d.line((x, y, x + l * math.cos(ang), y + l * math.sin(ang)), fill=(150, 210, 255, int(220 * (1 - k))), width=4)
    d.ellipse((cx - R - 22, cy - R - 22, cx + R + 22, cy + R + 22), outline=(120, 200, 255, int(200 * (1 - 0.6 * ss(u / 3)))), width=14)
    k = cl((u - 0.2) / 0.3)
    text_center(d, (540, 420), 'AIR LEAVING', 96, WHT + (int(255 * k),))
    wavy(d, 330, 750, 500, CYN, cl((u - 0.4) / 0.4))
    text_center(d, (540, 1430), 'INTO SPACE', 80, CYN + (int(255 * cl((u - 1.6) / 0.3)),))
    return glow_add(img, lay, 1.6, 18)

def twist_piece(t, a, b):
    img = GRID.copy(); lay = new_lay(); d = ImageDraw.Draw(lay); u = t - a
    t2 = wt(14, 'twist') - a
    if u < t2 - 0.25:
        p = eback(u / 0.25); text_center(d, (540, 900), 'BUT...', int(170 * max(p, 0.05)), WHT + (255,))
    else:
        v = u - (t2 - 0.25)
        fl = 1.0 if v > 0.3 else (0.3 + 0.7 * (int(v * 40) % 2))
        text_center(d, (540, 820), 'HERE\'S', 90, WHT + (int(255 * fl),))
        text_center(d, (540, 960), 'THE TWIST', 150, YEL + (int(255 * fl),))
        wavy(d, 200, 880, 1060, RED, cl((v - 0.15) / 0.35), width=11, amp=9)
        rr = random.Random(int(v * 30))
        if v < 0.6:
            for i in range(26):
                ang = rr.uniform(0, 6.28); r = 160 + v * 900 * rr.uniform(0.5, 1)
                x, y = 540 + r * math.cos(ang), 920 + r * 0.6 * math.sin(ang)
                d.line((x, y, x + 20 * math.cos(ang), y + 20 * math.sin(ang)), fill=YEL + (int(255 * (1 - v / 0.6)),), width=4)
    return glow_add(img, lay, 1.7, 18)

def stamp_piece(t, a, b):
    img = GRID.copy(); lay = new_lay(); d = ImageDraw.Draw(lay); u = t - a
    s = 1.7 - 0.7 * eout(u / 0.18)
    tmp = new_lay(); td = ImageDraw.Draw(tmp)
    td.rounded_rectangle((150, 760, 930, 1080), 40, outline=RED + (255,), width=16)
    text_center(td, (540, 880), 'GRAVITY:', 120, RED + (255,)); text_center(td, (540, 1000), 'ON', 140, WHT + (255,))
    tmp = tmp.rotate(-6, center=(540, 920), resample=Image.BICUBIC)
    if s != 1: tmp = tmp.resize((int(W * s), int(H * s))); off = (int(540 - 540 * s), int(920 - 920 * s)); lay.alpha_composite(tmp, off)
    else: lay.alpha_composite(tmp)
    text_center(d, (540, 1300), "IT'S COMING BACK", 70, WHT + (int(255 * cl((u - 0.45) / 0.3)),))
    img = glow_add(img, lay, 1.6, 16)
    if 0.18 < u < 0.32:
        a2 = 1 - (u - 0.18) / 0.14; img = Image.blend(img, Image.new('RGB', (W, H), (255, 240, 230)), 0.5 * a2)
    return img

# ---------------- overlays on 3D shots ----------------
def ruler_overlay(img, t, a, b):
    """neon ruler from the pavement to the stickman's feet with a cm counter"""
    lay = new_lay(); d = ImageDraw.Draw(lay)
    g = pt(t, 'ground'); f = pt(t, 'feet')
    k = cl((t - a - 0.2) / 0.3) * cl((b - t) / 0.25)
    if k <= 0: return img
    A = int(255 * k)
    x = f[0] + 95; y0 = g[1] + 6; y1 = min(f[1] - 8, y0 - 30)
    d.line((f[0] - 110, y0, f[0] + 130, y0), fill=CYN + (int(200 * k),), width=5)
    d.line((x, y0, x, y1), fill=YEL + (A,), width=9)
    d.line((x - 22, y1, x + 22, y1), fill=YEL + (A,), width=8)
    d.line((f[0] - 60, y1, x - 22, y1), fill=YEL + (int(140 * k),), width=3)
    cm = int(round(40 * cl((t - a - 0.2) / (b - a - 0.6))))
    text_center(d, (x + 120, (y0 + y1) / 2 - 10), f'{cm} CM', 100, WHT + (A,), stroke=9, sfill=(0, 0, 0, A))
    return glow_add(img, lay, 1.3, 12)

def grip_overlay(img, t, a, b):
    lay = new_lay(); d = ImageDraw.Draw(lay)
    k = cl((t - a) / 0.25) * cl((b - t) / 0.25)
    if k <= 0: return img
    A = int(255 * k)
    p = 1 - ss((t - a - 0.35) / 1.2)
    col = GRN if p > 0.6 else (YEL if p > 0.25 else RED)
    x0, x1, y = 190, 890, 420
    d.rounded_rectangle((x0 - 14, y - 44, x1 + 14, y + 44), 40, outline=WHT + (A,), width=6, fill=(0, 0, 0, int(120 * k)))
    if p > 0.01: d.rounded_rectangle((x0, y - 30, x0 + (x1 - x0) * p, y + 30), 30, fill=col + (A,))
    text_center(d, (540, y - 115), 'TYRE GRIP', 80, WHT + (A,), stroke=8, sfill=(0, 0, 0, A))
    text_center(d, (540, y + 120), f'{int(round(p * 100))}%', 110, col + (A,), stroke=8, sfill=(0, 0, 0, A))
    return glow_add(img, lay, 1.2, 12)

def speed_overlay(img, t, a, b, vmax=36, t_hit=None):
    lay = new_lay(); d = ImageDraw.Draw(lay)
    k = cl((t - a) / 0.2) * cl((b - t) / 0.3)
    if k <= 0: return img
    A = int(255 * k)
    v = vmax * cl((t - a) / (t_hit - a)) if t_hit else vmax
    v = int(round(v))
    col = RED if v >= vmax else WHT
    text_center(d, (540, 380), f'{v} KM/H', 140, col + (A,), stroke=10, sfill=(0, 0, 0, A))
    wavy(d, 260, 820, 480, RED, cl((t - (t_hit or a)) / 0.35))
    return glow_add(img, lay, 1.2, 12)

def freeze(img, t, label, head):
    """freeze-frame styling: darker desaturated background, glowing outline on the stickman, leader line to a label"""
    a = np.asarray(img, np.float32)
    hsv = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2HSV)
    sat = hsv[..., 1].astype(np.float32); val = hsv[..., 2].astype(np.float32)
    m = ((sat < 40) & (val > 120)).astype(np.uint8)
    hx, hy = int(head[0]), int(head[1])
    box = np.zeros_like(m); box[max(0, hy - 140):min(H, hy + 560), max(0, hx - 300):min(W, hx + 300)] = 1
    m = m * box
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    seeds = set()
    for (sx, sy) in ((hx, hy), (hx, hy + 60), (hx, hy + 200), (hx, hy + 330)):
        for dx in range(-25, 26, 5):
            for dy in range(-25, 26, 5):
                x, y = sx + dx, sy + dy
                if 0 <= x < W and 0 <= y < H and lab[y, x] > 0: seeds.add(int(lab[y, x]))
    for i in seeds:
        if st[i, cv2.CC_STAT_AREA] > 300 and st[i, cv2.CC_STAT_WIDTH] < 520: keep[lab == i] = 1
    keep = cv2.dilate(keep, np.ones((5, 5), np.uint8))
    gray = a.mean(axis=2, keepdims=True)
    bg = (a * 0.45 + gray * 0.55) * 0.45
    out = bg * (1 - keep[..., None]) + a * keep[..., None]
    ring = cv2.dilate(keep, np.ones((21, 21), np.uint8)) - cv2.dilate(keep, np.ones((5, 5), np.uint8))
    img2 = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    lay = new_lay(); la = np.zeros((H, W, 4), np.uint8); la[..., 0] = CYN[0]; la[..., 1] = CYN[1]; la[..., 2] = CYN[2]; la[..., 3] = ring * 255
    lay = Image.fromarray(la, 'RGBA'); d = ImageDraw.Draw(lay)
    ly = 330
    d.line((hx, hy - 120, hx, ly + 60), fill=YEL + (255,), width=6)
    f = font(76); bb = d.textbbox((0, 0), label, font=f); w = bb[2] - bb[0]
    d.rounded_rectangle((540 - w / 2 - 36, ly - 60, 540 + w / 2 + 36, ly + 60), 40, fill=(10, 14, 28, 230), outline=YEL + (255,), width=5)
    text_center(d, (540, ly), label, 76, WHT + (255,))
    return glow_add(img2, lay, 1.4, 14)

# ---------------- segment functions ----------------
def hook_frame(t):
    img = bframe('SH01_hook', t)
    if t < 0.62:
        la = lineart(img, GO, 0.12)
        sy = int(H * cl(t / 0.5))
        if t < 0.5:
            arr = np.asarray(la).copy(); scan = np.zeros((H, W), np.float32)
            scan[max(0, sy - 6):sy + 6] = 1
            arr = np.clip(arr + scan[..., None] * np.array([255, 230, 160]) * 0.8, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
        else:
            k = (t - 0.5) / 0.12
            img = Image.blend(Image.blend(la, Image.new('RGB', (W, H), (255, 250, 235)), 0.6 * (1 - k)), img, k)
    return callout(img, max(t, 0.0) + 0.6, 0.0, 3.85 + 0.6, ['GRAVITY: OFF'], hi=['OFF'], y=300, sz=118)

SEGS = []
def seg(a, b, fn): SEGS.append((a, b, fn))
S = ST
seg(0.0, S[2], lambda t: hook_frame(t))
seg(S[2], 6.20, lambda t: ring_piece(t, S[2], 6.20, 1, 'SECOND 1', from_pt=pt(4.0, 'head')))
seg(6.20, S[3], lambda t: callout(bframe('SH02_stomach', t), t, 6.25, S[3] - 0.3, ['STOMACH', 'DROP'], hi=['DROP'], y=300))
seg(S[3], S[4], lambda t: callout(bframe('SH03_gap', t), t, S[3] + 0.05, S[4] - 0.3, ['NOT YET'], hi=['YET'], y=300))
seg(S[4], S[5], lambda t: globe_speed(t, S[4], S[5]))
seg(S[5], S[7], lambda t: tangent_piece(t, S[5], S[7], wt(6, 'curves') - 0.2))
seg(S[7], S[8], lambda t: callout(ruler_overlay(bframe('SH07_drift', t), t, S[7] + 0.4, S[8] - 0.1), t, S[7] + 0.05, S[7] + 1.5, ['YOU DRIFT UP'], hi=['UP'], y=300))
seg(S[8], 27.40, lambda t: ring_piece(t, S[8], 27.40, 2, 'SECOND 2', sub='NO BRAKES'))
seg(27.40, S[10], lambda t: grip_overlay(callout(bframe('SH08_car', t), t, 27.45, 28.95, ['NO BRAKES'], hi=['BRAKES'], y=330), t, wt(9, 'no') - 0.1, S[10] - 0.15))
seg(S[10], 34.10, lambda t: ring_piece(t, S[10], 34.10, 3, 'SECOND 3', sub='A TINY HOP'))
T_FRZ = wt(11, 'windows') + 0.05
seg(34.10, T_FRZ, lambda t: callout(bframe('SH10_hop', t), t, wt(11, 'bad') - 0.05, wt(11, 'two') + 0.3, ['BAD IDEA'], hi=['BAD'], y=330))
seg(T_FRZ, S[12], lambda t: freeze(bframe('SH10_hop', T_FRZ), t, 'STILL GOING UP', pt(T_FRZ, 'head')))
T_ATMO = wt(12, 'the') - 0.1
seg(S[12], T_ATMO, lambda t: ring_piece(t, S[12], T_ATMO, 4, 'SECOND 4'))
seg(T_ATMO, S[13], lambda t: atmo_piece(t, T_ATMO, S[13]))
seg(S[13], S[14], lambda t: ring_piece(t, S[13], S[14], 5, 'SECOND 5', sub='GRAVITY RETURNS'))
seg(S[14], S[15], lambda t: twist_piece(t, S[14], S[15]))
seg(S[15], S[16], lambda t: callout(bframe('SH15_frozen', t), t, S[15] + 0.1, S[16] - 0.3, ['NOT THE', 'DANGER'], hi=['DANGER'], y=300))
seg(S[16], 53.30, lambda t: stamp_piece(t, S[16], 53.30))
seg(53.30, S[18], lambda t: callout(bframe('SH17_drop', t), t, wt(17, 'at') - 0.05, S[18] - 0.25, ['AT ONCE'], hi=['ONCE'], y=330))
T_HIT = 59.72 + math.sqrt(2 * 5.05 / 9.8)
seg(S[18], S[20], lambda t: speed_overlay(callout(bframe('SH18_fall', t), t, wt(18, 'five') - 0.05, 59.7, ['5 METRES', 'UP'], hi=['5', 'METRES'], y=300),
                                           t, 59.75, S[20] - 0.1, 36, T_HIT))
def ending(t):
    a, b = S[20], wt(21, 'hold') - 0.15
    img = bframe('SH20_lamp', t)
    if t < b:
        img = lineart(img, GO, 0.15)
        lay = new_lay(); d = ImageDraw.Draw(lay); u = t - a
        text_center(d, (540, 330), 'RIGHT NOW?', 120, WHT + (int(255 * cl(u / 0.3)),), stroke=10, sfill=(0, 0, 0, int(255 * cl(u / 0.3))))
        wavy(d, 240, 840, 420, YEL, cl((u - 0.4) / 0.4))
        img = glow_add(img, lay, 1.5, 16)
    elif t < b + 0.5:
        k = ss((t - b) / 0.5)
        la = lineart(img, GO, 0.15)
        yy, xx = np.mgrid[0:H, 0:W]
        c = pt(t, 'head'); r = k * 2300
        m = (np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) < r).astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 25)[..., None]
        img = Image.fromarray((np.asarray(img) * m + np.asarray(la) * (1 - m)).astype(np.uint8))
    img = callout(img, t, b + 0.1, END_T - 0.4, ['HOLD ON', 'OR JUMP?'], hi=['JUMP?'], y=300)
    return img
seg(S[20], END_T + 0.1, ending)

TX_GLITCH = [b for (a, b, f) in SEGS[:-1]]
PUNCH = [2.32, 5.52, 15.0, wt(5, 'straight'), wt(6, 'away'), wt(7, 'forty'), wt(8, 'brake'), wt(9, 'grip'), wt(10, 'hop'),
         wt(12, 'space'), wt(13, 'five'), wt(15, 'never'), wt(16, 'back'), wt(17, 'once'), wt(18, 'five'), wt(19, 'thirtysix'), wt(21, 'jump')]

def seg_at(t):
    for a, b, fn in SEGS:
        if a - 1e-6 <= t < b: return fn(t)
    return SEGS[-1][2](t)

def glitch(img, k):
    a = np.asarray(img); o = a.copy(); s = int(18 * k)
    o[..., 0] = np.roll(a[..., 0], s, axis=1); o[..., 2] = np.roll(a[..., 2], -s, axis=1)
    rr = random.Random(int(k * 100))
    for i in range(5):
        y = rr.randint(0, H - 40); h = rr.randint(8, 40); o[y:y + h] = np.roll(o[y:y + h], rr.randint(-60, 60), axis=1)
    return Image.fromarray(o)

def punch(img, t):
    z = 0.0
    for p in PUNCH:
        if any(abs(p - c) < 0.5 for c in TX_GLITCH): continue
        dt = t - p
        if -0.06 < dt < 0.28: z = max(z, 0.07 * (cl((dt + 0.06) / 0.06) if dt < 0 else math.exp(-dt / 0.09)))
    if z <= 0.002: return img
    s = 1 + z; w, h = int(W * s), int(H * s)
    im = img.resize((w, h), Image.BILINEAR); x, y = (w - W) // 2, (h - H) // 2
    return im.crop((x, y, x + W, y + H))

def frame_at(i):
    t = i / FPS
    img = seg_at(t)
    img = punch(img, t)
    for c in TX_GLITCH:
        if 0 <= t - c < 0.07: img = glitch(img, 1 - (t - c) / 0.07)
    # seamless loop: last 0.35 s whip-blend into frame 0
    if t > END_T - 0.35:
        k = ss((t - (END_T - 0.35)) / 0.35)
        f0 = hook_frame(0.0)
        a = np.asarray(img, np.float32); b = np.asarray(f0, np.float32)
        sh = int(k * 220)
        a = np.roll(a, -sh, axis=1); b = np.roll(b, int((1 - k) * 220), axis=1)
        img = Image.fromarray((a * (1 - k) + b * k).astype(np.uint8)).filter(ImageFilter.BoxBlur(int(8 * math.sin(math.pi * k)) or 0))
    return img

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'frames':
        SINGLE = True
        globals()['SINGLE'] = True
        for s in sys.argv[2:]:
            t = float(s); frame_at(int(round(t * FPS))).save(f'/tmp/gv/test/f_{t:06.2f}.jpg', quality=88)
    elif mode == 'out':
        i0, i1 = map(int, sys.argv[2].split('-')); i1 = min(i1, NF)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', sys.argv[3]], stdin=subprocess.PIPE)
        for i in range(i0, i1):
            p.stdin.write(frame_at(i).tobytes())
            if i % 50 == 0: print('frame', i, flush=True)
        p.stdin.close(); p.wait()
