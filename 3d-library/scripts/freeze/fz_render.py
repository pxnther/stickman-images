import bpy, os
sc = bpy.context.scene
OUT = r"C:\Users\Pxnther\Documents\WhatIFs\FREEZE TIME\renders"
os.makedirs(OUT, exist_ok=True)
JOBS = [('S01_snap', 1, 34, 100), ('S02_splash', 35, 107, 100), ('S03_crane', 108, 180, 100), ('S04_except', 181, 266, 100),
        ('S05_pigeons', 267, 322, 100), ('S06_poke', 323, 391, 100), ('S07_taxi', 392, 443, 100), ('S08_orbit', 444, 587, 100),
        ('S09_pov', 1029, 1119, 100), ('S09b_grope', 1120, 1156, 100), ('S10_step', 1197, 1239, 100), ('S11_molecules', 1240, 1354, 100),
        ('S12_glass', 1355, 1441, 100), ('S13_face', 1442, 1527, 100), ('S14_restart', 1670, 1726, 100), ('S15_land', 1727, 1770, 100),
        ('S16_flyoff', 1771, 1826, 100), ('S17_end', 1827, 1902, 100), ('BG1_plate', 588, 818, 50), ('BG2_plate', 819, 1028, 50),
        ('S09b_mask', 1120, 1156, 100)]
ONLY = globals().get('ONLY')
if ONLY: JOBS = [j for j in JOBS if j[0] in ONLY]
r = sc.render
r.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 32
r.resolution_x, r.resolution_y = 1080, 1920
r.image_settings.media_type = 'VIDEO'; r.image_settings.file_format = 'FFMPEG'; r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'
r.ffmpeg.constant_rate_factor = 'PERC_LOSSLESS'; r.fps = 30
sc.render.use_motion_blur = False
STATE = {'i': 0}
def _mask(on):
    keep = set()
    rig = bpy.data.objects['StickRig']
    keep.add(rig.name); keep.update(c.name for c in rig.children)
    for o in sc.objects:
        if o.name in keep or o.type in ('CAMERA', 'LIGHT', 'EMPTY', 'ARMATURE'): continue
        if on:
            o['_hr'] = o.hide_render; o.hide_render = True
        elif '_hr' in o:
            o.hide_render = o['_hr']; del o['_hr']
    r.film_transparent = on
def step():
    i = STATE['i']
    if i >= len(JOBS):
        r.resolution_percentage = 100; print('QUEUE DONE'); return None
    name, a, b, pct = JOBS[i]
    sc.frame_start, sc.frame_end = a, b; r.resolution_percentage = pct
    r.filepath = os.path.join(OUT, name + '_')
    if name.endswith('_mask'): _mask(True)
    bpy.ops.render.render(animation=True)
    if name.endswith('_mask'): _mask(False)
    open(os.path.join(OUT, 'progress.txt'), 'a').write(f'{name} done\n')
    STATE['i'] = i + 1
    return 0.5
bpy.app.timers.register(step, first_interval=1.0)
print('queued', [j[0] for j in JOBS])
