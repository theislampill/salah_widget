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
    # Explicit raises, never `assert` (removed by python -O; R0029).
    if hashlib.sha256(manifest_raw).hexdigest() not in pin_source:
        raise ValueError('native_star_bootstrap: manifest drift: runtime-manifest.json SHA-256 is not the '
                         'pin in vendor/real-sky/src/diffuse-manifest-pin.mjs')
    manifest = json.loads(manifest_raw)
    raw = (source / 'data/bright-stars.json').read_bytes()
    parent = hashlib.sha256(raw).hexdigest()
    if parent != manifest['catalogue']['sha256'] or len(raw) != manifest['catalogue']['bytes']:
        raise ValueError('native_star_bootstrap: catalogue identity: data/bright-stars.json does not match '
                         'runtime-manifest.json catalogue sha256/bytes')
    catalogue = json.loads(raw)
    selected = [s for s in catalogue['stars'] if s.get('emission', {}).get('enabled') is not False and s['vmag'] <= 4.5]
    body = dict(schema='salah-real-sky/bootstrap/1', parentSha256=parent,
                totalRecords=len(catalogue['stars']), maximumMagnitude=4.5,
                fields=FIELDS, rows=[[s.get(k) for k in FIELDS] for s in selected])
    text = json.dumps(body, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    data = text.encode('utf-8')
    if len(data) >= 130000:
        raise ValueError(f'native_star_bootstrap: bootstrap size bound: {len(data)} bytes, expected < 130000')
    pin = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), parentSha256=parent, records=len(selected))
    return text, pin
