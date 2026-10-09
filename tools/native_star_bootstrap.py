"""Lossless first-scene subset of the pinned full catalogue; no new source data."""
import hashlib
import json

FIELDS = ['hygId', 'hip', 'raDeg', 'decDeg', 'epochJyear', 'vmag', 'bv',
          'pmRaCosDecMasYr', 'pmDecMasYr', 'distancePc', 'radialVelocityKmS',
          'spectralType', 'sed']


def star_bootstrap(source):
    manifest_raw = (source / 'data/registered-starlight/runtime-manifest.json').read_bytes()
    # Same independent manifest pin used by the scientific full-pack admission.
    pin_source = (source / 'src/diffuse-manifest-pin.mjs').read_text(encoding='utf-8')
    assert hashlib.sha256(manifest_raw).hexdigest() in pin_source, 'manifest drift'
    manifest = json.loads(manifest_raw)
    raw = (source / 'data/bright-stars.json').read_bytes()
    parent = hashlib.sha256(raw).hexdigest()
    assert parent == manifest['catalogue']['sha256'] and len(raw) == manifest['catalogue']['bytes']
    catalogue = json.loads(raw)
    selected = [s for s in catalogue['stars'] if s.get('emission', {}).get('enabled') is not False and s['vmag'] <= 4.5]
    body = dict(schema='salah-real-sky/bootstrap/1', parentSha256=parent,
                totalRecords=len(catalogue['stars']), maximumMagnitude=4.5,
                fields=FIELDS, rows=[[s.get(k) for k in FIELDS] for s in selected])
    text = json.dumps(body, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    data = text.encode('utf-8')
    assert len(data) < 130000
    pin = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), parentSha256=parent, records=len(selected))
    return text, pin
