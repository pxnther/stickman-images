import os, sys
os.environ.setdefault('VID', 'space')
exec(open('/tmp/gv/wf_edit_base.py').read())
S = [s['start'] for s in TJ['scenes']]

def lungs(img, t, a, b, bg):
    """two lungs inflating past their outline, red tear lines appear"""
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    base = plate(bg, dim=0.4); img = Image.blend(img, base, k) if k < 1 else base
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    g = eout((t - a - 0.3) / 2.2); cx, cy = 540, 1000
    for sgn in (-1, 1):
        w0, h0 = 150, 300; w, h = w0 * (1 + 0.45 * g), h0 * (1 + 0.3 * g)
        x0 = cx + sgn * (40 + w / 2)
        d.ellipse((x0 - w / 2, cy - h / 2, x0 + w / 2, cy + h / 2), outline=WHT + (int(110 * k),), width=4)
        d.ellipse((x0 - w0 / 2, cy - h0 / 2, x0 + w0 / 2, cy + h0 / 2), outline=CYN + (al,), width=8)
        if g > 0.75:
            rs = random.Random(int(sgn + 5)); tk = int(255 * k * cl((g - 0.75) / 0.2))
            for i in range(4):
                yy = cy - h / 3 + i * h / 5; pts = [(x0 - w / 3, yy)]
                for s_ in range(4): pts.append((pts[-1][0] + w / 6, yy + rs.uniform(-25, 25)))
                d.line(pts, fill=RED + (tk,), width=6)
    d.line((cx, cy - 380, cx, cy - 170), fill=WHT + (al,), width=10)
    kt = ss((t - wt('hold', S[2], S[2] + 0.6)) / 0.3) * k
    E.text_center(d, (540, 330), "DON'T HOLD", 110, WHT + (int(255 * kt),)); E.text_center(d, (540, 460), 'YOUR BREATH', 110, RED + (int(255 * kt),))
    return E.glow_add(img, lay, 1.4, 14)
def countdown(img, t, a, b):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.55, 230, 760, dim=0.5)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    v = max(0, 15 - int(t - a))
    E.text_center(d, (540, 330), f'{v}', 260, (WHT if v > 5 else RED) + (al,))
    E.text_center(d, (540, 600), 'SECONDS', 90, YEL + (al,))
    cx, cy, R = 540, 460, 210; fr = cl((t - a) / 15.0)
    d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * (1 - fr), fill=CYN + (al,), width=10)
    return E.glow_add(img, lay, 1.5, 16)
def sun_flare(img, t, a, b):
    k = ss((t - a) / 0.4) * ss((b - t) / 0.3)
    if k <= 0: return img
    arr = np.asarray(img).astype(np.float32)
    warm = arr * np.array([1.12, 1.0, 0.86]) + 18 * k
    out = Image.fromarray(np.clip(arr * (1 - 0.6 * k) + warm * 0.6 * k, 0, 255).astype(np.uint8))
    lay = E.new_lay(); d = ImageDraw.Draw(lay)
    sx, sy = 160, 300
    for r, al in ((380, 40), (230, 70), (120, 140), (60, 255)):
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(255, 245, 220, int(al * k)))
    out = E.glow_add(out, lay, 1.0, 40)
    return calm_text(out, t, a + 0.6, b - 0.05, ['WORST SUNBURN', 'OF YOUR LIFE'], y=1180, sz=88, hi=['SUNBURN'], hicol=ORA)

def seg(t):
    n = which(t); img = shot(n, t)
    if n == 'SP01_hook': return hook_text(img, t, [('NO', WHT), ('SUIT', RED)], until=2.9)
    if n == 'SP02_noexplode':
        if t < S[2]: return calm_text(img, t, wt("don't", S[1], S[1] + 0.3) - 0.1, S[2] - 0.05, ["YOU DON'T", 'EXPLODE'], y=270, sz=110, hi=['EXPLODE'], hicol=CYN)
        return lungs(img, t, S[2], S[3] - 0.03, still('SP02_noexplode', S[2] + 0.6))
    if n == 'SP04_breathe':
        if t < S[4]:
            t15 = wt('fifteen', S[3], S[3] + 2.5) - 0.2
            return countdown(img, t, t15, S[4] - 0.03) if t >= t15 else img
        return calm_text(img, t, wt('boil', S[4], S[4] + 1.5) - 0.2, S[5] - 0.05, 'IT BOILS', y=300, sz=110, hi=['BOILS'], hicol=ORA)
    if n == 'SP06_heat':
        if t < S[6]:
            k = ss((t - (wt('freeze', S[5], S[5] + 0.8) - 0.1)) / 0.3) * ss((S[6] - t) / 0.2)
            img = thermal(img, k, 0.15 * ramp_(t, S[5], S[6]), top_cut=0.0, lo=200, sat=10)
            return calm_text(img, t, wt('slowly', S[5], S[6] - 1.0) - 0.3, S[6] - 0.05, 'HEAT LEAVES SLOWLY', y=1250, sz=76)
        return sun_flare(img, t, S[6], S[7] - 0.03)
    if n == 'SP08_pulled':
        return calm_text(img, t, wt('minute', S[7], S[7] + 1.5) - 0.3, S[8] - 0.05, ['BACK INSIDE IN', '~1 MINUTE'], y=270, sz=100, hi=['MINUTE'], hicol=GRN)
    return img
if __name__ == '__main__': main()
