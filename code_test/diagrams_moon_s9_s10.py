"""Animated diagram layer (RGBA PNG frames, 4K) for scenes 9 and 10 of the Moon video."""
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SC = 3; W, H = 3840, 2160; FPS = 30
S = {int(k): v for k, v in json.load(open('/tmp/ov/timing.json'))['start'].items()}
TR = json.load(open('/tmp/dg/track.json'))
INK = (12, 12, 16, 255); WHITE = (255, 255, 255, 255); YEL = (255, 214, 0, 255)
OUT = '/tmp/dg/fr'; os.makedirs(OUT, exist_ok=True)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def easeout(x): x = clamp(x); return 1 - (1 - x) ** 3
def easeinout(x): x = clamp(x); return x * x * (3 - 2 * x)

def glow_sprite(r, col, power=2.2):
    n = int(r * 2)
    y, x = np.mgrid[0:n, 0:n]
    d = np.sqrt((x - r) ** 2 + (y - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** power
    im = np.zeros((n, n, 4), np.uint8)
    im[..., 0], im[..., 1], im[..., 2] = col
    im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im, 'RGBA')
GLOW_Y = glow_sprite(46 * SC, (255, 220, 90))
GLOW_W = glow_sprite(16 * SC, (255, 255, 240), 1.4)
GLOW_S = glow_sprite(10 * SC, (255, 230, 120), 1.6)

def put(fr, spr, x, y, a=1.0, s=1.0):
    if a <= 0.01 or s <= 0.02: return
    sp = spr if s == 1.0 else spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))))
    if a < 1:
        al = sp.getchannel('A').point(lambda v: int(v * a)); sp = sp.copy(); sp.putalpha(al)
    fr.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))

def pos(n, t, key):
    i = int(clamp((t - S[n]) * FPS, 0, len(TR[str(n)][key]) - 1))
    x, y, r = TR[str(n)][key][i]
    return x * SC, y * SC, r * SC

def scene_alpha(n, t, fade=0.25):
    return clamp((S[n + 1] - 0.05 - t) / fade)

# ---------- scene 9: measuring line Earth -> Moon ----------
D9 = 30.866; L9 = 1.0
def draw9(fr, t):
    if t < D9 - 0.15: return
    A = scene_alpha(9, t)
    ex, ey, er = pos(9, t, 'earth'); mx, my, mr = pos(9, t, 'moon')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    off = 95 * SC
    x0 = ex + er * 0.92 + 10 * SC; x1 = mx - mr * 0.92 - 10 * SC
    y0 = (ey + my) / 2 + off
    e = easeinout((t - D9) / L9)
    xh = x0 + (x1 - x0) * e
    lw = 8 * SC; ow = 4 * SC
    # end bar left (pops in)
    bh = 34 * SC * easeout((t - D9 + 0.15) / 0.2)
    def bar(x, h):
        d.line([(x, y0 - h / 2), (x, y0 + h / 2)], fill=INK, width=lw + 2 * ow)
        d.line([(x, y0 - h / 2), (x, y0 + h / 2)], fill=WHITE, width=lw)
    if xh > x0 + 2:
        d.line([(x0, y0), (xh, y0)], fill=INK, width=lw + 2 * ow)
        d.line([(x0, y0), (xh, y0)], fill=WHITE, width=lw)
        for k in range(1, 10):
            xt = x0 + (x1 - x0) * k / 10
            if xt <= xh:
                th = (20 if k == 5 else 13) * SC
                d.line([(xt, y0 - th), (xt, y0)], fill=INK, width=6 * SC)
                d.line([(xt, y0 - th + 2 * SC), (xt, y0 - 2 * SC)], fill=YEL, width=3 * SC)
    if bh > 1: bar(x0, bh)
    done = t - (D9 + L9)
    if done > 0:
        bar(x1, 34 * SC * easeout(done / 0.2))
        # arrowheads both ends
        s = 24 * SC * easeout(done / 0.25)
        for (xa, dirn) in ((x0, 1), (x1, -1)):
            pts = [(xa, y0), (xa + dirn * s, y0 - s * 0.6), (xa + dirn * s, y0 + s * 0.6)]
            d.polygon(pts, fill=YEL, outline=INK)
    # dashed guides up to Earth / Moon centre line
    for xg in (x0, x1):
        if (xg == x0 and e > 0) or (xg == x1 and done > 0):
            yy = y0 - 18 * SC
            while yy > (ey + my) / 2 + 30 * SC:
                d.line([(xg, yy), (xg, yy - 8 * SC)], fill=(255, 255, 255, 150), width=2 * SC); yy -= 16 * SC
    # glowing head while drawing, flash when done
    if 0 < e < 1:
        put(lay, GLOW_Y, xh, y0, 0.55, 0.6); put(lay, GLOW_W, xh, y0, 1.0)
    if 0 < done < 0.6:
        f = 1 - done / 0.6
        put(lay, GLOW_Y, x1, y0, 0.7 * f, 0.8); put(lay, GLOW_Y, x0, y0, 0.5 * f, 0.6)
    if A < 1:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * A)))
    fr.alpha_composite(lay)

# ---------- scene 10: pulse of light Moon -> Earth in 1.3 s ----------
D10 = 33.8; L10 = 1.3
TRAIL = 16
def p10(t, u):
    ex, ey, er = pos(10, t, 'earth'); mx, my, mr = pos(10, t, 'moon')
    sx, sy = mx - mr * 0.95, my; tx, ty = ex + er * 0.95, ey
    # slight arc so it reads as travelling through space
    x = sx + (tx - sx) * u; y = sy + (ty - sy) * u
    return x, y
BLUE = (170, 215, 255)
GLOW_B = glow_sprite(60 * SC, BLUE, 2.0)
def draw10(fr, t):
    if t < D10 - 0.4: return
    A = scene_alpha(10, t)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ex, ey, er = pos(10, t, 'earth'); mx, my, mr = pos(10, t, 'moon')
    pre = t - (D10 - 0.4)
    if 0 < pre < 0.5:   # moon charges up
        put(lay, GLOW_B, mx, my, 0.8 * math.sin(math.pi * pre / 0.5), mr * 2.6 / GLOW_B.width)
        rr = mr * (1.0 + 0.4 * pre / 0.5); al = int(230 * (1 - pre / 0.5))
        d.ellipse([mx - rr, my - rr, mx + rr, my + rr], outline=(200, 230, 255, al), width=6 * SC)
    u = (t - D10) / L10
    arr = t - (D10 + L10)
    if u >= 0:
        uh = clamp(u)
        tail = max(0.0, uh - 0.45) if arr <= 0 else clamp(arr / 0.35) * 1.0 + (uh - 0.45) * (1 - clamp(arr / 0.35))
        # soft wide glow (quarter res + blur)
        q = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0)); dq = ImageDraw.Draw(q)
        segs = 40
        for k in range(segs):
            u0 = tail + (uh - tail) * k / segs; u1 = tail + (uh - tail) * (k + 1) / segs
            if u1 <= u0: continue
            x0, y0 = p10(t, u0); x1, y1 = p10(t, u1); f = (k + 1) / segs
            dq.line([(x0 / 4, y0 / 4), (x1 / 4, y1 / 4)], fill=(120, 190, 255) + (int(255 * f),), width=int(14 * SC / 4 * 3))
        q = q.filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
        lay.alpha_composite(q)
        # crisp white core, fading toward the tail
        for k in range(segs):
            u0 = tail + (uh - tail) * k / segs; u1 = tail + (uh - tail) * (k + 1) / segs
            if u1 <= u0: continue
            x0, y0 = p10(t, u0); x1, y1 = p10(t, u1); f = (k + 1) / segs
            d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, int(255 * f)), width=int(9 * SC * (0.4 + 0.6 * f)))
        if arr <= 0:
            x, y = p10(t, uh)
            put(lay, GLOW_B, x, y, 1.0, 1.3 + 0.1 * math.sin(t * 40)); put(lay, GLOW_W, x, y, 1.0, 2.2)
    if arr > 0:
        if arr < 0.5: put(lay, GLOW_B, ex + er * 0.8, ey, 0.95 * (1 - arr / 0.5), 1.8)
        for dl in (0.0, 0.18):
            a2 = arr - dl
            if 0 < a2 < 0.7:
                rr = er * (1.02 + 0.8 * easeout(a2 / 0.7)); al = int(255 * (1 - a2 / 0.7))
                d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], outline=(210, 235, 255, al), width=max(2, int(7 * SC * (1 - a2 / 0.7))))
        put(lay, GLOW_B, ex, ey, 0.35 * clamp(arr / 0.3), er * 2.6 / GLOW_B.width)
    if A < 1:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * A)))
    fr.alpha_composite(lay)

T0, T1 = S[9], S[11]
N0, N1 = round(T0 * FPS), round(T1 * FPS)
only = [float(a) for a in sys.argv[1:]]
ts = only if only else [i / FPS for i in range(N0, N1)]
for i, t in enumerate(ts):
    fr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if S[9] <= t < S[10]: draw9(fr, t)
    if S[10] <= t < S[11]: draw10(fr, t)
    name = f'{OUT}/t{t:07.2f}.png' if only else f'{OUT}/{i:04d}.png'
    fr.save(name, compress_level=1)
print('frames', len(ts), 'start_frame', N0)
