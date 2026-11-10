"""Generic build + preview kickoff, run inside a timer. Needs GO = dict(anim=, key=, cfg=, prev=[(name,t)], imgs={}, track=bool)."""
import bpy, os, json, traceback
TEX = r"C:\Users\Pxnther\Documents\WhatIFs\MOON TWICE AS CLOSE\blender\tex"
_GO = GO
def _go():
    out = _GO['cfg']['out']; os.makedirs(out, exist_ok=True)
    log = os.path.join(out, 'go.txt')
    try:
        open(log, 'w').write('start\n')
        G = {'__name__': 'anim', 'IMGS': _GO.get('imgs', {})}
        exec(open(TEX + '\\' + _GO['anim'], encoding='utf-8').read(), G)
        open(log, 'a').write('anim ok\n')
        res = G['build'](G['END'], _GO['key'], track_out=os.path.join(out, 'track.json'))
        open(os.path.join(out, 'shots.json'), 'w').write(json.dumps([(n, (a - 1) / 30.0, (b) / 30.0) for n, a, b in res]))
        bpy.context.scene[_GO['key'] + '_cfg'] = json.dumps(_GO['cfg'])
        open(log, 'a').write('build ok ' + json.dumps(res) + '\n')
        if _GO.get('prev'):
            exec(open(TEX + r"\wf_preview_v1.py", encoding='utf-8').read(), {'__name__': 'p', 'CFG': _GO['cfg'], 'PREV': _GO['prev']})
            open(log, 'a').write('preview ok\n')
        if _GO.get('render'):
            exec(open(TEX + r"\wf_render_v1.py", encoding='utf-8').read(), {'__name__': 'r', 'CFG': _GO['cfg'], 'ONLY': _GO.get('only')})
            open(log, 'a').write('render queued\n')
    except Exception:
        open(log, 'a').write(traceback.format_exc())
    return None
bpy.app.timers.register(_go, first_interval=0.5)
print('go registered')
