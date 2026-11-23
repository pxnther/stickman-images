"""Run one MuAPI job described by <dir>/job.json and save results next to it.

job.json: {"endpoint": "<path after /api/v1/>", "body": {...}}
          or {"endpoint": "discover", "match": ["edit", "video"]} to list matching API paths.
The key comes from the MUAPI_KEY env var (GitHub secret). Nothing secret is written to disk.
"""
import json, os, sys, time, urllib.request, urllib.error

BASE = 'https://api.muapi.ai'
KEY = os.environ.get('MUAPI_KEY', '')


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={'x-api-key': KEY, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors='replace')
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, {'raw': txt[:2000]}


def main(d):
    job = json.load(open(os.path.join(d, 'job.json')))
    log = []
    if job['endpoint'] == 'discover':
        with urllib.request.urlopen(BASE + '/openapi.json', timeout=120) as r:
            spec = json.loads(r.read().decode())
        words = [w.lower() for w in job.get('match', ['edit'])]
        out = []
        for p, ops in spec.get('paths', {}).items():
            if all(w in p.lower() for w in words):
                for m, op in ops.items():
                    out.append({'path': p, 'method': m, 'summary': op.get('summary'),
                                'body': op.get('requestBody')})
        json.dump({'count': len(out), 'paths': out, 'components': list(spec.get('components', {}).get('schemas', {}).keys())[:0]},
                  open(os.path.join(d, 'result.json'), 'w'), indent=1)
        # full schemas for matched bodies (resolve one level of $ref)
        schemas = spec.get('components', {}).get('schemas', {})
        refs = {}
        for o in out:
            s = json.dumps(o['body'] or {})
            for name in schemas:
                if f'/schemas/{name}"' in s:
                    refs[name] = schemas[name]
        json.dump(refs, open(os.path.join(d, 'schemas.json'), 'w'), indent=1)
        return
    if job['endpoint'] == 'poll':
        for n, rid in job['ids'].items():
            for _ in range(int(job.get('wait_min', 0) * 6) + 1):
                st, res = call('GET', f'/api/v1/predictions/{rid}/result')
                if str(res.get('status', '')).lower() not in ('processing', 'queued', 'pending'):
                    break
                time.sleep(10)
            log.append({'name': n, 'status': st, 'result': res})
            for i, u in enumerate(res.get('outputs') or []):
                ext = os.path.splitext(u.split('?')[0])[1] or '.mp4'
                urllib.request.urlretrieve(u, os.path.join(d, f'{n}_out{i + 1:02d}{ext}'))
        st, res = call('GET', '/api/v1/account/balance')
        log.append({'balance_status': st, 'balance': res})
        json.dump(log, open(os.path.join(d, 'result.json'), 'w'), indent=1)
        return
    if job['endpoint'] == 'estimate':
        for e in job['items']:
            st, res = call('POST', f"/api/v1/models/{e['name']}/estimate-cost", e['body'])
            log.append({'name': e['name'], 'status': st, 'estimate': res})
        st, res = call('GET', '/api/v1/account/balance')
        log.append({'balance_status': st, 'balance': res})
        json.dump(log, open(os.path.join(d, 'result.json'), 'w'), indent=1)
        return
    st, res = call('POST', '/api/v1/' + job['endpoint'].lstrip('/'), job['body'])
    log.append({'submit_status': st, 'submit': res})
    rid = res.get('request_id') or res.get('id') or (res.get('data') or {}).get('request_id')
    final = None
    if rid:
        for _ in range(180):                      # up to 30 min
            time.sleep(10)
            st, res = call('GET', f'/api/v1/predictions/{rid}/result')
            s = str(res.get('status') or (res.get('data') or {}).get('status') or '').lower()
            if s in ('completed', 'failed', 'cancelled', 'succeeded', 'error'):
                final = res
                break
        log.append({'final': final or res})
        outs = (final or {}).get('outputs') or ((final or {}).get('data') or {}).get('outputs') or []
        for i, u in enumerate(outs):
            ext = os.path.splitext(u.split('?')[0])[1] or '.mp4'
            urllib.request.urlretrieve(u, os.path.join(d, f'out{i + 1:02d}{ext}'))
    json.dump(log, open(os.path.join(d, 'result.json'), 'w'), indent=1)


if __name__ == '__main__':
    for d in sys.argv[1:]:
        main(d)
