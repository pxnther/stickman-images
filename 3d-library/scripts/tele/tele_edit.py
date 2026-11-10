import os, sys
os.environ.setdefault('VID', 'tele')
exec(open('/tmp/gv/wf_edit_base.py').read())
S = [s['start'] for s in TJ['scenes']]
T_LDN = wt('london', S[1], S[1] + 1.8); T_SLAM = wt('slam', S[1], S[1] + 3.5)
T_LA = wt('la', S[2], S[2] + 1.5); T_LON2 = wt('london', S[2] + 2, S[3] - 2)
T_OVER = wt('over', S[3], S[3] + 3.0); T_CLAP = wt('thunderclap', S[4], S[4] + 3.0)
T_THIN = wt('thin', S[5], S[5] + 2.5); T_TWO = wt('two', S[5] + 2, S[6] - 0.8)
TILT = math.radians(23.5)

def gproj(lat, lon, rot, R, cx, cy):
    lat, lon = math.radians(lat), math.radians(lon)
    x = math.cos(lat) * math.cos(lon + rot); y = math.sin(lat); z = math.cos(lat) * math.sin(lon + rot)
    y2 = y * math.cos(TILT) - z * math.sin(TILT); z2 = y * math.sin(TILT) + z * math.cos(TILT)
    return cx - R * x, cy - R * y2, z2
def arrow(d, x0, y0, x1, y1, col, al, w=10):
    d.line((x0, y0, x1, y1), fill=col + (al,), width=w)
    a = math.atan2(y1 - y0, x1 - x0); h = 34
    d.polygon([(x1 + math.cos(a) * 10, y1 + math.sin(a) * 10), (x1 - h * math.cos(a - 0.5), y1 - h * math.sin(a - 0.5)),
               (x1 - h * math.cos(a + 0.5), y1 - h * math.sin(a + 0.5))], fill=col + (al,))
def spin_piece(t, a, b):
    """neon globe: Earth spins, LA's speed, London's slower speed in another direction"""
    img = E.GRID.copy(); lay = E.new_lay(); d = ImageDraw.Draw(lay); u = t - a
    k = ss(u / 0.3) * ss((b - t) / 0.3); al = int(255 * k)
    cx, cy, R = 540, 930, 360
    rot_end = math.radians(150)
    rot = rot_end - 1.6 * (1 - eout(cl((t - a) / max(0.1, T_LA - a))))      # spins, then settles with both cities in front
    E.draw_globe(d, t, rot, R, cx, cy, alpha=k)
    E.text_center(d, (540, 380), 'EARTH SPINS', 92, WHT + (int(255 * k * ss((u - 0.1) / 0.3)),))
    for lat, lon, name, sp, col, t0, ylab in ((34.0, -118.2, 'LA', 1400, YEL, T_LA - 0.2, 1440), (51.5, -0.1, 'LONDON', 1040, CYN, T_LON2 - 0.2, 1600)):
        kk = ss((t - t0) / 0.35) * k
        if kk <= 0: continue
        x, y, z = gproj(lat, lon, rot, R, cx, cy); x2, y2, _ = gproj(lat, lon + 2, rot, R, cx, cy)
        dx, dy = x2 - x, y2 - y; n = math.hypot(dx, dy) or 1; L = sp / 1400 * 230 * eout((t - t0) / 0.6)
        ka = int(255 * kk)
        d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=col + (ka,))
        d.text((x - 30, y - 80), name, font=E.font(52), fill=col + (ka,), stroke_width=6, stroke_fill=(0, 0, 0, ka))
        if L > 20: arrow(d, x, y, x + dx / n * L, y + dy / n * L, col, ka)
        v = int(round(sp * eout((t - t0) / 1.2) / 10) * 10)
        E.text_center(d, (540, ylab), f'{name}  {v:,} KM/H', 76, col + (ka,))
    if t > T_LON2 + 1.2:
        kd = ss((t - T_LON2 - 1.2) / 0.3) * k
        E.text_center(d, (540, 1730), 'DIFFERENT DIRECTION', 66, WHT + (int(255 * kd),))
        E.wavy(d, 230, 850, 1790, YEL, cl((t - T_LON2 - 1.4) / 0.4) * k)
    return E.glow_add(img, lay, 1.5, 16)

def countdown(img, t, a, b, t0):
    k = ss((t - a) / 0.3) * ss((b - t) / 0.3)
    if k <= 0: return img
    img = dim_region(img, k * 0.6, 200, 620, dim=0.55)
    lay = E.new_lay(); d = ImageDraw.Draw(lay); al = int(255 * k)
    s_ = max(0, 120 - int(max(0, t - t0) * 1.0)); col = RED if (t > t0 and int(t * 2) % 2 == 0) else WHT
    E.text_center(d, (540, 380), f'{s_ // 60}:{s_ % 60:02d}', 200, col + (al,))
    E.text_center(d, (540, 540), 'UNTIL YOU PASS OUT', 60, YEL + (al,))
    return E.glow_add(img, lay, 1.4, 14)

def seg(t):
    n = which(t)
    if n is None: return spin_piece(t, S[2], S[3])
    img = shot(n, t)
    if n == 'T01_hook': return hook_text(img, t, [('TELEPORT', CYN)], sz=150)
    if n == 'T02a_la': return calm_text(img, t, S[1] + 0.2, T_LDN + 0.15, 'LOS ANGELES', y=280, sz=110, hi=['LOS', 'ANGELES'])
    if n == 'T02b_london':
        img = calm_text(img, t, T_LDN + 0.15, T_SLAM - 0.1, 'LONDON', y=280, sz=120, hi=['LONDON'], hicol=CYN)
        return calm_text(img, t, T_SLAM - 0.1, S[2] - 0.05, 'SLAM', y=280, sz=150, hi=['SLAM'], hicol=RED)
    if n == 'T04_fly':
        if t < T_OVER - 0.1: return calm_text(img, t, S[3] + 0.2, T_OVER - 0.1, ["STILL MOVING", "AT LA SPEED"], y=260, sz=96, hi=['LA'])
        return counter_big(img, t, T_OVER - 0.1, S[4] - 0.05, T_OVER, T_OVER + 1.4, 2090, 'KM/H', sub='SIDEWAYS', y=400)
    if n == 'T05_clap':
        img = calm_text(img, t, wt('air', S[4], S[4] + 1.5) - 0.1, T_CLAP - 0.1, 'AIR SHOVED ASIDE', y=280, sz=92, hi=['AIR'], hicol=CYN)
        return stamp(img, t, T_CLAP - 0.05, S[5] - 0.1, 'BOOM', cy=420, rot=-4)
    if n == 'T06_everest':
        if t < T_TWO - 0.4:
            img = calm_text(img, t, S[5] + 0.3, T_THIN - 0.15, 'TOP OF EVEREST', y=280, sz=100, hi=['EVEREST'], hicol=CYN)
            return calm_text(img, t, T_THIN - 0.15, T_TWO - 0.4, 'AIR TOO THIN', y=280, sz=110, hi=['THIN'], hicol=RED)
        return countdown(img, t, T_TWO - 0.4, S[6] - 0.05, T_TWO)
    if n == 'T07_short': return calm_text(img, t, wt('short', S[6], S[6] + 2.0) - 0.4, S[7] - 0.1, 'SHORT JUMPS ONLY', y=280, sz=100, hi=['SHORT'], hicol=GRN)
    return img
if __name__ == '__main__': main()
