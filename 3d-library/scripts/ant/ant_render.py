import bpy, os, json, math
sc = bpy.context.scene; r = sc.render; D = bpy.data
OUT = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\renders\ant"
os.makedirs(OUT, exist_ok=True)
ANTSETS = ['ANT_CAFE', 'ANT_RAIN', 'ANT_LAB', 'ANT_GRASS', 'LIB_stickman_rig']
SUNS = {'W_CAFE': ((math.radians(52), 0, math.radians(-130)), 3.6, (1.0, 0.95, 0.86), 1.0),
        'W_RAIN': ((math.radians(35), 0, math.radians(-40)), 0.6, (0.85, 0.9, 1.0), 0.8),
        'W_GRASS': ((math.radians(80), 0, math.radians(-95)), 2.2, (1.0, 0.58, 0.32), 0.55),
        'W_LAB': ((math.radians(40), 0, math.radians(30)), 0.12, (0.7, 0.85, 1.0), 1.0)}
def apply_job(j):
    for c in D.collections:
        if c.name.startswith('PF_') or c.name.startswith('V_'): c.hide_render = True; c.hide_viewport = True
    for n in ANTSETS:
        c = D.collections.get(n)
        if c:
            on = n in j['sets']; c.hide_render = not on; c.hide_viewport = not on
    sc.world = D.worlds[j['world']]
    rot, st, col, wst = SUNS[j['world']]
    sun = D.objects['PF_SUN']; sun.rotation_euler = rot; sun.data.energy = st; sun.data.color = col
    for nd in sc.world.node_tree.nodes:
        if nd.type == 'BACKGROUND': nd.inputs[1].default_value = wst * (0.75 if j['world'] == 'W_RAIN' else 1.0)
    sc.eevee.taa_render_samples = j['samples']; sc.eevee.use_raytracing = j['rt']
    r.resolution_percentage = j['pct']
JOBS = json.loads(sc['ant_jobs'])
ONLY = globals().get('ONLY')
if ONLY: JOBS = [j for j in JOBS if j['name'] in ONLY]
STATE = {'i': 0}
def step():
    i = STATE['i']
    if i >= len(JOBS):
        r.resolution_percentage = 100; print('QUEUE DONE'); open(os.path.join(OUT, 'progress.txt'), 'a').write("QUEUE DONE\n"); return None
    j = JOBS[i]; apply_job(j)
    sc.frame_start, sc.frame_end = j['a'], j['b']
    r.image_settings.media_type = 'VIDEO'; r.image_settings.file_format = 'FFMPEG'; r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'PERC_LOSSLESS'; r.fps = 30; r.resolution_x, r.resolution_y = 1080, 1920
    r.filepath = os.path.join(OUT, j['name'] + '_')
    bpy.ops.render.render(animation=True)
    open(os.path.join(OUT, 'progress.txt'), 'a').write(f"{j['name']} done\n")
    STATE['i'] = i + 1
    return 0.5
if globals().get('START', True):
    bpy.app.timers.register(step, first_interval=1.0); print('queued', [j['name'] for j in JOBS])
