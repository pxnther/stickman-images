import os, sys
os.environ.setdefault('VID', 'giant')
exec(open('/tmp/gv/wf_edit_base.py').read())
S = [s['start'] for s in TJ['scenes']]
T_SNAP = wt('snaps', S[3]); T_HIT = S[5] - 0.45

def titanic_scale(img, t, a, b, bg):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.4); img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    cx, cy = 540, 1060; tilt = math.radians(14) * eout((t - a - 0.35) / 0.7)
    d.polygon([(cx, cy), (cx - 90, cy + 300), (cx + 90, cy + 300)], outline=CYN + (al,), width=8)
    d.line((cx - 200, cy + 300, cx + 200, cy + 300), fill=CYN + (al,), width=8)
    L = 360; lx, ly = cx - L * math.cos(tilt), cy + L * math.sin(tilt); rx, ry = cx + L * math.cos(tilt), cy - L * math.sin(tilt)
    d.line((lx, ly, rx, ry), fill=WHT + (al,), width=10); d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=CYN + (al,))
    for px, py in ((lx, ly), (rx, ry)):
        d.line((px, py, px - 110, py + 170), fill=WHT + (al,), width=5); d.line((px, py, px + 110, py + 170), fill=WHT + (al,), width=5)
        d.arc((px - 130, py + 110, px + 130, py + 230), 0, 180, fill=WHT + (al,), width=8)
    stick_icon(d, lx, ly + 168, 150, WHT, al, 8)                      # the giant (heavier side, down)
    sx, sy = rx, ry + 165                                               # Titanic silhouette (lighter side, up)
    d.polygon([(sx - 120, sy - 40), (sx + 125, sy - 40), (sx + 100, sy), (sx - 100, sy)], fill=(150, 160, 175, al))
    d.rectangle((sx - 80, sy - 62, sx + 70, sy - 40), fill=(220, 220, 225, al))
    for i in range(4): d.rectangle((sx - 60 + i * 34, sy - 100, sx - 44 + i * 34, sy - 62), fill=(230, 150, 40, al))
    kt = ss((t - a - 0.7) / 0.3) * k
    E.text_center(d, (540, 470), '70,000 TONNES', 120, YEL + (int(255 * kt),))
    E.text_center(d, (540, 610), 'TITANIC: 52,000 T', 64, WHT + (int(255 * kt),))
    E.wavy(d, 300, 780, 700, YEL, cl((t - a - 0.9) / 0.4) * k)
    return E.glow_add(img, lay, 1.4, 14)
def lab_labels(img, t, a, b, names, texts, cols):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.25)
    if k <= 0: return img
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    for nm, tx, col, dy in zip(names, texts, cols, (-330, -420)):
        x, y = trk(nm, t); label(d, x, y, x, y + dy, tx, col, al, 50)
    return E.glow_add(img, lay, 1.2, 10)
def cracks(img, t, t0, b):
    k = ss((b - t) / 0.2)
    if t < t0 or k <= 0: return img
    g = cl((t - t0) / 0.35); x0, y0 = trk('shin', t)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); rs = random.Random(3)
    for i in range(7):
        a = rs.uniform(0, 2 * math.pi); x, y = x0, y0; pts = [(x, y)]
        for s_ in range(6):
            a += rs.uniform(-0.7, 0.7); ln = rs.uniform(30, 60) * g
            x += math.cos(a) * ln; y += math.sin(a) * ln; pts.append((x, y))
        d.line(pts, fill=RED + (int(255 * k),), width=7, joint='curve')
    return E.glow_add(img, lay, 2.0, 14)
def blood_column(img, t, a, b, bg):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.35); img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    x, yf, s = 540, 1700, 1250
    stick_icon(d, x, yf, s, WHT, al, 10)
    yhead = yf - s + s * 0.13; yheart = yf - s * 0.62
    d.ellipse((x - 26, yheart - 26, x + 26, yheart + 26), fill=RED + (al,))
    reach = lerp(0, 0.62, eout((t - a - 0.3) / 1.4)) + 0.03 * math.sin(t * 7) * ss((t - a - 1.6) / 0.3)
    ytop = yheart - (yheart - yhead) * reach
    d.rounded_rectangle((x - 14, ytop, x + 14, yheart), 10, fill=RED + (al,))
    bx = x + 170; d.line((bx, yhead, bx, yheart), fill=YEL + (al,), width=6)
    d.line((bx - 24, yhead, bx + 24, yhead), fill=YEL + (al,), width=6); d.line((bx - 24, yheart, bx + 24, yheart), fill=YEL + (al,), width=6)
    E.text_center(d, (bx + 120, (yhead + yheart) / 2 - 50), '40 M', 90, YEL + (al,))
    kt = ss((t - a - 0.4) / 0.3) * k
    E.text_center(d, (540, 250), "YOUR HEART", 92, WHT + (int(255 * kt),)); E.text_center(d, (540, 355), "CAN'T REACH IT", 92, RED + (int(255 * kt),))
    return E.glow_add(img, lay, 1.4, 14)
def hearing_deep(img, t, a, b, bg):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.4); img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    x = 330; y0, y1 = 1450, 380                                      # bottom = 0.1 Hz, top = 100 kHz (log)
    def fy(fz): return y0 + (y1 - y0) * (math.log10(fz) + 1) / 6.0
    d.line((x, y0, x, y1), fill=WHT + (al,), width=6)
    for fz, lab in ((1, '1 Hz'), (20, '20 Hz'), (200, '200 Hz'), (2000, '2 kHz'), (20000, '20 kHz')):
        yy = fy(fz); d.line((x - 18, yy, x + 18, yy), fill=WHT + (al,), width=5); d.text((x - 250, yy - 28), lab, font=E.font(46), fill=WHT + (al,))
    hk = ss((t - a - 0.2) / 0.5) * k
    d.rounded_rectangle((x + 40, fy(20000), x + 150, fy(20)), 24, fill=(40, 200, 120, int(90 * hk)), outline=GRN + (int(255 * hk),), width=6)
    d.text((x + 175, (fy(20) + fy(20000)) / 2 - 70), 'HUMANS', font=E.font(64), fill=GRN + (int(255 * hk),))
    d.text((x + 175, (fy(20) + fy(20000)) / 2 + 5), 'CAN HEAR', font=E.font(52), fill=WHT + (int(230 * hk),))
    tv = wt('voice', S[8], S[8] + 1.5); vk = ss((t - tv) / 0.3) * k
    yv = fy(1.0)
    for i in range(4):
        u = ((t - a) * 0.6 + i / 4) % 1; r = 30 + 80 * u
        cy_ = lerp(fy(200), yv, eout(cl((t - tv) / 1.0)))
        d.ellipse((x + 95 - r, cy_ - r * 0.5, x + 95 + r, cy_ + r * 0.5), outline=CYN + (int(255 * vk * (1 - u)),), width=6)
    if vk > 0: d.text((x + 175, yv - 40), 'YOUR VOICE', font=E.font(60), fill=CYN + (int(255 * vk),))
    tk = ss((t - wt('deep', S[8], S[8] + 2.5)) / 0.3) * k
    E.text_center(d, (540, 1600), 'TOO DEEP TO HEAR', 88, YEL + (int(255 * tk),))
    E.wavy(d, 250, 830, 1665, YEL, cl((t - wt('deep', S[8], S[8] + 2.5) - 0.2) / 0.4) * k)
    return E.glow_add(img, lay, 1.4, 14)
def heat_label(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.2)
    if k <= 0: return img
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    temp = lerp(37.0, 45.0, cl((t - a) / (b - a)))
    d.text((70, 260), 'BODY TEMP', font=E.font(48), fill=WHT + (al,))
    d.text((70, 320), f'{temp:.1f}°C', font=E.font(110), fill=(255, int(lerp(170, 60, cl((t - a) / (b - a)))), 40, al))
    return E.glow_add(img, lay, 1.3, 10)

def seg(t):
    n = which(t); img = shot(n, t + (1 / 30 if GF(t) == 46 else 0))   # skip one glitched render frame at the hook cut
    if n == 'G01_hook': return hook_text(img, t, [('100X', YEL), ('TALLER', WHT)], sz=132)
    if n == 'G02_weight':
        a = wt('more', S[1], S[1] + 2.0) - 0.25
        if t < a: return calm_text(img, t, wt('seventy', S[1], S[1] + 0.8) - 0.15, a + 0.05, '70,000 TONNES', y=270, sz=120, hi=['70,000'])
        return titanic_scale(img, t, a, S[2] - 0.05, still('G02_weight', S[2] - 0.5))
    if n == 'G03_bones':
        return lab_labels(img, t, S[2] + 0.5, S[3] - 0.05, ('slab', 'cube'), ('BONES  ×10,000', 'WEIGHT  ×1,000,000'), (CYN, YEL))
    if n == 'G04_step': return cracks(img, t, T_SNAP, T_SNAP + 1.0)
    if n == 'G05_fall':
        img = counter_big(img, t, S[4] + 1.9, S[5] - 0.05, S[4] + 1.9, T_HIT, 260, 'KM/H', y=330)
        return calm_text(img, t, T_HIT, S[5] - 0.05, 'AS FAST AS A RACE CAR', y=560, sz=60, hi=['RACE', 'CAR'])
    if n == 'G06_heart':
        if t < S[6]: return blood_column(img, t, S[5], S[6] - 0.02, still('G06_heart', S[5] + 1.0))
        return to_black(img, 0.95 * ss((t - (S[6] + 0.2)) / (S[7] - S[6] - 0.35)))
    if n == 'G08_heat':
        if t < S[7] + 2.75:
            k = ss((t - S[7]) / 0.3) * ss((S[7] + 2.75 - t) / 0.2)
            img = thermal(img, k, 0.0, top_cut=0.0, label=False, lo=196, sat=12)
            return heat_label(img, t, S[7], S[7] + 2.73)
        return lab_labels(img, t, S[7] + 3.1, S[8] - 0.05, ('skin', 'heat'), ('SKIN  ×10,000', 'HEAT  ×1,000,000'), ((255, 140, 130), ORA))
    if n == 'G09_shout':
        tv = wt('voice', S[8], S[8] + 1.5) - 0.3
        if t >= tv: return hearing_deep(img, t, tv, S[9] - 0.03, still('G09_shout', S[8] + 1.5))
        return img
    return img
if __name__ == '__main__': main()
