"""Fail-closed CP9-N003 evidence join; a browser launch is never acceptance."""
import argparse, hashlib, json, re
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_CHECKS = ('entry', 'lifecycle', 'currentness', 'sourceFailure', 'material',
                   'composition', 'prayerCalendarSettings', 'providers', 'navigation', 'csp')
REQUIRED_TARGETS = {(engine, entry) for engine in ('chromium', 'firefox', 'webkit')
                    for entry in ('http', 'file')}

def collect(rows, expected_tree, evidence_root, nodes=None, review=None):
    root = Path(evidence_root).resolve()
    errors, seen, ids = [], set(), set()
    def artifact(record):
        try:
            name = record['evidence']
            path = (root / name).resolve()
            if Path(name).is_absolute() or not path.is_relative_to(root): return False
            return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
        except (KeyError, TypeError, OSError, ValueError): return False
    if not re.fullmatch(r'[0-9a-f]{64}', expected_tree or ''):
        errors.append('invalid expected runtime identity')
    for i, row in enumerate(rows):
        label = row.get('recordId', f'row-{i}')
        env, entry = row.get('environment', {}), row.get('entry', {})
        target = (env.get('family'), entry.get('form'))
        if label in ids or target in seen: errors.append(f'{label}: duplicate record or target')
        ids.add(label); seen.add(target)
        if row.get('schemaVersion') != 1 or row.get('runtimeTreeSha256') != expected_tree:
            errors.append(f'{label}: schema/runtime mismatch')
        if target not in REQUIRED_TARGETS: errors.append(f'{label}: unexpected target')
        requests = row.get('sourceRequests')
        if not isinstance(requests, list) or not requests or not all(isinstance(u, str) and urlparse(u).scheme in ('http', 'https', 'file', 'data', 'blob') for u in requests):
            errors.append(f'{label}: source request observations missing or malformed')
        if not all(env.get(k) for k in ('version', 'platform', 'executable')):
            errors.append(f'{label}: incomplete environment identity')
        if env.get('family') in ('chromium', 'firefox') and env.get('os') != 'Windows':
            errors.append(f'{label}: Windows target required')
        if env.get('family') == 'webkit' and env.get('os') not in ('Windows', 'Darwin', 'Linux'):
            errors.append(f'{label}: undocumented WebKit host')
        scheme = urlparse(entry.get('url', '')).scheme
        if scheme not in ({'http', 'https'} if entry.get('form') == 'http' else {'file'}):
            errors.append(f'{label}: entry URL does not match actual entry form')
        for name in REQUIRED_CHECKS:
            check = row.get('checks', {}).get(name, {})
            mode = 'live' if name == 'providers' else 'actual-navigation' if name == 'navigation' else 'actual-entry'
            if check.get('status') != 'PASS' or check.get('mode') != mode or not artifact(check):
                errors.append(f'{label}/{name}: missing, non-passing, wrong mode, or unbound evidence')
    if seen != REQUIRED_TARGETS: errors.append('incomplete required engine/entry matrix')
    prerequisites = {}
    for name in ('CP9-N001', 'CP9-N002'):
        node = (nodes or {}).get(name, {})
        prerequisites[name] = node.get('status') == 'PASS' and node.get('runtimeTreeSha256') == expected_tree and artifact(node)
    review = review or {}
    reviewed = review.get('status') == 'PASS' and review.get('independent') is True and review.get('runtimeTreeSha256') == expected_tree and artifact(review)
    platform_pass = not errors
    return {'schemaVersion': 1, 'runtimeTreeSha256': expected_tree,
            'platformEvidence': 'PASS' if platform_pass else 'INCOMPLETE',
            'status': 'PASS' if platform_pass and all(prerequisites.values()) and reviewed else 'PARTIAL',
            'prerequisites': prerequisites, 'independentReview': reviewed, 'errors': errors,
            'scope': 'Checks identity, completeness, declared observation mode and artifact integrity. Independent review must assess observation content; labels and hashes alone do not prove behavior.'}

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--records', type=Path, required=True); p.add_argument('--tree', required=True); p.add_argument('--output', type=Path, required=True)
    a=p.parse_args(); result=collect(json.loads(a.records.read_text(encoding='utf-8')), a.tree, a.records.parent)
    a.output.write_text(json.dumps(result, indent=2), encoding='utf-8'); print(json.dumps(result, indent=2))
