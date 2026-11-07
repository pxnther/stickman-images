import bpy, os, json
sc = bpy.context.scene; r = sc.render; D = bpy.data
OUT = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\renders\ss"
os.makedirs(OUT, exist_ok=True)
STREET = ['BLD_Row', 'Cars', 'Props', 'Street', 'FZ', 'SS_STREET']
LAKE = ['PF_LAKE', 'SS_LAKE']
def apply_job(j):
    lake = j['kind'] == 'lake'
    for n in STREET + LAKE:
        c = D.collections.get(n)
        if c:
            on = (n in LAKE) if lake else (n in STREET)
            c.hide_render = not on; c.hide_viewport = not on
    if lake:   # the friend on the bench comes from the street collection: keep only ped3 visible
        fz = D.collections['FZ']; fz.hide_render = False; fz.hide_viewport = False
        for o in fz.objects:
            keep = o.name.startswith('FZ_ped3')
            o.hide_render = not keep; o.hide_viewport = not keep
    else:
        for o in D.collections['FZ'].objects:
            o.hide_render = False; o.hide_viewport = False
    sc.world = D.worlds['W_SKY'] if lake else D.worlds['PolyHaven urban_street_04']
    sc.eevee.taa_render_samples = j['samples']; sc.eevee.use_raytracing = j['rt']
    r.resolution_percentage = j['pct']
JOBS = json.loads(sc['ss_jobs'])
ONLY = globals().get('ONLY')
if ONLY: JOBS = [j for j in JOBS if j['name'] in ONLY]
STATE = {'i': 0}
def step():
    i = STATE['i']
    if i >= len(JOBS):
        r.resolution_percentage = 100; print('QUEUE DONE'); return None
    j = JOBS[i]; apply_job(j)
    sc.frame_start, sc.frame_end = j['a'], j['b']
    r.image_settings.media_type = 'VIDEO'; r.image_settings.file_format = 'FFMPEG'; r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'PERC_LOSSLESS'; r.fps = 30; r.resolution_x, r.resolution_y = 1080, 1920
    r.filepath = os.path.join(OUT, j['name'] + '_')
    bpy.ops.render.render(animation=True)
    open(os.path.join(OUT, 'progress.txt'), 'a').write(j['name'] + ' done\n')
    STATE['i'] = i + 1
    return 0.5
if globals().get('START', True):
    bpy.app.timers.register(step, first_interval=1.0); print('queued', [j['name'] for j in JOBS])
