import bpy, os, json
R = {'__name__': 'wfr', 'START': False, 'CFG': CFG}
exec(open(r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex\wf_render_v1.py", encoding='utf-8').read(), R)
sc = bpy.context.scene; r = sc.render
OUTP = os.path.join(CFG['out'], 'prev'); os.makedirs(OUTP, exist_ok=True)
for f_ in os.listdir(OUTP):
    if f_.endswith('.jpg'): os.remove(os.path.join(OUTP, f_))
jobs = {j['name']: j for j in json.loads(sc[CFG['key']])}
for name, t in PREV:
    j = dict(jobs[name]); j['samples'] = 8; j['pct'] = 40
    R['apply_job'](j)
    r.image_settings.media_type = 'IMAGE'; r.image_settings.file_format = 'JPEG'; r.resolution_x, r.resolution_y = 1080, 1920
    sc.frame_set(int(round(t * 30)) + 1)
    r.filepath = os.path.join(OUTP, f'{name}_{t:05.2f}.jpg'); bpy.ops.render.render(write_still=True)
print('ok', sorted(os.listdir(OUTP)))
