"""Generic render queue. Needs CFG = dict(out=..., key=..., sets=[all toggled collections], suns={world: (rot, energy, color, world_strength)}, sun='SUN')"""
import bpy, os, json
sc = bpy.context.scene; r = sc.render; D = bpy.data
C = CFG; OUT = C['out']; os.makedirs(OUT, exist_ok=True)
def apply_job(j):
    for n in C['sets']:
        c = D.collections.get(n)
        if c:
            on = n in j['sets']; c.hide_render = not on; c.hide_viewport = not on
    sc.world = D.worlds[j['world']]
    if j['world'] in C['suns']:
        rot, st, col, wst = C['suns'][j['world']]
        sun = D.objects[C.get('sun', 'SUN')]; sun.rotation_euler = rot; sun.data.energy = st; sun.data.color = col
        for nd in sc.world.node_tree.nodes:
            if nd.type == 'BACKGROUND': nd.inputs[1].default_value = wst
    sc.eevee.taa_render_samples = j['samples']; sc.eevee.use_raytracing = j['rt']; r.resolution_percentage = j['pct']
JOBS = json.loads(sc[C['key']])
ONLY = globals().get('ONLY')
if ONLY: JOBS = [j for j in JOBS if j['name'] in ONLY]
STATE = {'i': 0}
def step():
    i = STATE['i']
    if i >= len(JOBS):
        r.resolution_percentage = 100; open(os.path.join(OUT, 'progress.txt'), 'a').write("QUEUE DONE\n"); return None
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
