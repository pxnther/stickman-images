import os, sys
os.environ.setdefault('VID', 'invis')
exec(open('/tmp/gv/wf_edit_base.py').read())
S = [s['start'] for s in TJ['scenes']]
T_INV = wt('invisible', S[2] + 2.0, S[2] + 3.0)          # "Invisible eyes let it pass..."
T_EX = wt('exactly', S[5], S[5] + 2.0)

def eye_diagram(img, t, a, b, bg):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.38); img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    cx, cy, R = 600, 1010, 250
    clear = ss((t - T_INV + 0.1) / 0.5)                       # 0 = normal eye, 1 = invisible eye
    ea = int(al * lerp(1.0, 0.35, clear))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=WHT + (ea,), width=8)
    lx = cx - R + 40                                          # lens
    d.ellipse((lx - 26, cy - 95, lx + 26, cy + 95), outline=CYN + (ea,), width=7)
    d.chord((cx - R, cy - R, cx + R, cy + R), -60, 60, outline=RED + (int(ea * (1 - clear)),), width=14)   # retina
    flow = ((t - a) * 1.4) % 1.0
    for i, dy in enumerate((-150, -75, 0, 75, 150)):
        y = cy + dy; d.line((40, y, lx, y), fill=YEL + (al,), width=6)
        hx, hy = cx + R - 8, cy                               # focus on the retina
        bx, by = lerp(lx, hx, 1.0), lerp(y, hy, 1.0)
        n_ = int(al * (1 - clear)); s_ = int(al * clear)
        if n_ > 0 and s_ == 0: d.line((lx, y, bx, by), fill=YEL + (n_,), width=6)
        s_ = int(al * clear)
        if s_ > 0: d.line((lx, y, 1060, y), fill=YEL + (s_,), width=6)
        px = lerp(40, lx, flow)                                # moving photon dots
        d.ellipse((px - 10, y - 10, px + 10, y + 10), fill=YEL + (al,))
    gk = int(al * (1 - clear) * (0.6 + 0.4 * math.sin(t * 9)))
    d.ellipse((cx + R - 34, cy - 26, cx + R + 18, cy + 26), fill=RED + (gk,))
    k1 = al if clear < 0.5 else 0; k2 = al if clear >= 0.5 else 0
    if k1 > 0:
        E.text_center(d, (540, 470), 'EYES CATCH LIGHT', 92, WHT + (k1,)); E.text_center(d, (540, 1380), 'RETINA', 60, RED + (k1,))
    if k2 > 0:
        E.text_center(d, (540, 430), 'INVISIBLE EYES', 92, CYN + (k2,)); E.text_center(d, (540, 545), 'LET IT PASS THROUGH', 80, WHT + (k2,))
        E.text_center(d, (540, 1380), 'NOTHING CAUGHT', 72, RED + (k2,))
    E.wavy(d, 290, 790, 1475, RED, cl((t - T_INV - 0.5) / 0.4) * k)
    return E.glow_add(img, lay, 1.4, 14)

def blind_pov(img, t, a, b):
    k = ss((t - a) / (b - a))
    img = blur_k(img, k * 0.8); img = to_black(img, k * 0.96)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * ss((t - a - 0.25) / 0.3))
    E.text_center(d, (540, 900), 'YOU', 110, WHT + (al,)); E.text_center(d, (540, 1030), "CAN'T SEE", 130, RED + (al,))
    return E.glow_add(img, lay, 1.3, 14)

def ior_meter(img, t, a, b, t0, t1):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.85, 180, 660, dim=0.35)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    u = ss((t - t0) / (t1 - t0)); v = lerp(1.45, 1.0003, u)
    E.text_center(d, (540, 250), 'LIGHT BENDING', 64, WHT + (al,), stroke=6, sfill=(0, 0, 0, al))
    x0, x1, y = 140, 940, 470
    d.line((x0, y, x1, y), fill=WHT + (al,), width=6)
    for xx, lab, col in ((x0, 'AIR', CYN), (x1, 'GLASS', YEL)):
        d.line((xx, y - 22, xx, y + 22), fill=col + (al,), width=6); E.text_center(d, (xx, y + 40), lab, 52, col + (al,))
    px = lerp(x1, x0, u) + (x1 - x0) * 0.0
    d.ellipse((px - 22, y - 22, px + 22, y + 22), fill=lerp_col(YEL, CYN, u) + (al,))
    E.text_center(d, (540, 330), f'{v:.4f}' if u > 0.98 else f'{v:.2f}', 110, lerp_col(YEL, CYN, u) + (al,))
    return E.glow_add(img, lay, 1.4, 14)
def lerp_col(a, b, u): return tuple(int(lerp(x, y, u)) for x, y in zip(a, b))

def digest_bar(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.85, 180, 580, dim=0.35)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    E.text_center(d, (540, 250), 'DIGESTING', 92, WHT + (al,), stroke=8, sfill=(0, 0, 0, al))
    u = cl((t - a) / (b - a))
    d.rounded_rectangle((170, 400, 910, 460), 28, outline=GRN + (al,), width=6)
    d.rounded_rectangle((180, 410, 180 + 720 * u, 450), 20, fill=GRN + (al,))
    E.text_center(d, (540, 510), 'IN FULL VIEW', 56, YEL + (al,), stroke=6, sfill=(0, 0, 0, al))
    return E.glow_add(img, lay, 1.3, 12)

def rain_fx(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    lay = E.new_lay(); d = ImageDraw.Draw(lay); rs = random.Random(11)
    for i in range(140):
        x0 = rs.uniform(0, W); sp = rs.uniform(1800, 2600); ph = rs.uniform(0, 1); ln = rs.uniform(40, 90)
        y = ((t * sp / H + ph) % 1.0) * (H + 200) - 100; x = x0 - 0.12 * y
        d.line((x, y, x - 0.12 * ln, y + ln), fill=(200, 225, 255, int(130 * k)), width=3)
    for i in range(10):                                          # splashes on the head and shoulders
        cx, cy = 540 + rs.uniform(-110, 110), rs.choice((640, 690, 860)); ph = ((t * 1.7 + i * 0.37) % 1.0)
        if ph < 0.35:
            r = 10 + 70 * ph; al = int(200 * k * (1 - ph / 0.35))
            d.arc((cx - r, cy - r * 0.45, cx + r, cy + r * 0.45), 180, 360, fill=(220, 240, 255, al), width=4)
    img = img.convert('RGBA'); img.alpha_composite(lay); return img.convert('RGB')

def seg(t):
    n = which(t); img = shot(n, t)
    if n == 'I01_hook': return hook_text(img, t, [('INVISIBLE', CYN)], sz=150)
    if n == 'I02_blind':
        tb = S[1] + 1.1
        if t < tb: return calm_text(img, t, S[1] + 0.1, tb + 0.1, 'FIRST PROBLEM', y=280, sz=100, hi=['PROBLEM'], hicol=RED)
        return blind_pov(img, t, tb, S[2] - 0.15)
    if n == 'I03_plate': return eye_diagram(img, t, S[2], S[3] - 0.03, still('I03_plate', S[2] + 1.0))
    if n == 'I04_glass':
        if t < S[4]: return calm_text(img, t, wt('not', S[3], S[3] + 1.2) - 0.1, S[4] - 0.05, ['NOT REALLY', 'INVISIBLE'], y=250, sz=104, hi=['NOT'], hicol=RED)
        return calm_text(img, t, wt('glass', S[4], S[4] + 1.5) - 0.4, S[5] - 0.1, ['BENDS LIGHT', 'LIKE GLASS'], y=250, sz=104, hi=['GLASS'], hicol=CYN)
    if n == 'I06_air': return ior_meter(img, t, S[5] + 0.3, S[6] - 0.05, T_EX, S[6] - 0.8)
    if n == 'I07_food':
        if t < S[7]: return calm_text(img, t, wt('sandwich', S[6], S[6] + 0.7) - 0.1, S[7] - 0.05, ['FLOATING', 'SANDWICH'], y=250, sz=110, hi=['SANDWICH'], hicol=YEL)
        return digest_bar(img, t, wt('digested', S[7], S[7] + 2.5) - 0.3, S[8] - 0.05)
    if n == 'I09_rain': img = rain_fx(img, t, S[8], S[9]); return calm_text(img, t, wt('splashes', S[8], S[8] + 2.5) - 0.3, S[9] - 0.1, ['EVERY DROP', 'SPLASHES'], y=250, sz=110, hi=['SPLASHES'], hicol=CYN)
    return img
if __name__ == '__main__': main()
