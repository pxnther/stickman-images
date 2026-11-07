import bpy, os, json
R = {'__name__': 'ssr', 'START': False}
exec(open(r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex\ss_render_v1.py", encoding='utf-8').read(), R)
sc = bpy.context.scene; r = sc.render
OUTP = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\renders\ss\prev"
os.makedirs(OUTP, exist_ok=True)
jobs = {j['name']: j for j in json.loads(sc['ss_jobs'])}
for name, fr in PREV:
    j = dict(jobs[name]); j['samples'] = 8; j['pct'] = 40
    R['apply_job'](j)
    r.image_settings.media_type = 'IMAGE'; r.image_settings.file_format = 'JPEG'; r.resolution_x, r.resolution_y = 1080, 1920
    sc.frame_set(fr if fr else (j['a'] + j['b']) // 2)
    r.filepath = os.path.join(OUTP, f'{name}.jpg'); bpy.ops.render.render(write_still=True)
print('ok')
