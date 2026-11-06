import bpy, os, json, math
sc = bpy.context.scene; r = sc.render; D = bpy.data
OUT = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\renders\pf"
os.makedirs(OUT, exist_ok=True)
ALLSETS = ['PF_SKY', 'PF_PLANE', 'PF_PROPS', 'PF_LAKE', 'PF_SNOW', 'PF_JUNGLE', 'LIB_stickman_rig']
SUNS = {'W_SKY': ((math.radians(62), 0, math.radians(35)), 3.2, (1.0, 0.94, 0.84), 1.0),
        'W_NIGHT': ((math.radians(40), 0, math.radians(-60)), 0.45, (0.6, 0.7, 1.0), 0.28),
        'W_DUSK': ((math.radians(76), 0, math.radians(120)), 2.2, (1.0, 0.62, 0.38), 1.0),
        'W_JUNGLE': ((math.radians(40), 0, math.radians(20)), 4.2, (1.0, 0.93, 0.78), 0.8)}
def apply_job(j):
    for n in ALLSETS:
        c = D.collections.get(n)
        if c:
            on = n in j['sets']; c.hide_render = not on; c.hide_viewport = not on
    sc.world = D.worlds[j['world']]
    rot, st, col, wst = SUNS[j['world']]
    sun = D.objects['PF_SUN']; sun.rotation_euler = rot; sun.data.energy = st; sun.data.color = col
    for nd in sc.world.node_tree.nodes:
        if nd.type == 'BACKGROUND': nd.inputs[1].default_value = wst
    for i in range(3):
        m = D.materials.get(f'PF_Cloud{i}')
        if m:
            b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            b.inputs['Emission Strength'].default_value = 0.0 if j['world'] == 'W_NIGHT' else 0.22
            b.inputs['Base Color'].default_value = (0.35, 0.4, 0.5, 1) if j['world'] == 'W_NIGHT' else (0.95, 0.96, 1.0, 1)
    sc.eevee.taa_render_samples = j['samples']; sc.eevee.use_raytracing = j['rt']
    r.resolution_percentage = j['pct']
JOBS = json.loads(sc['pf_jobs'])
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
    open(os.path.join(OUT, 'progress.txt'), 'a').write(f"{j['name']} done\n")
    STATE['i'] = i + 1
    return 0.5
if globals().get('START', True):
    bpy.app.timers.register(step, first_interval=1.0); print('queued', [j['name'] for j in JOBS])
