"""Read-only verification of the returned r4 packet; outputs only this review receipt."""
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
from urllib.parse import parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')
O = Path(r'<evidence>')
C, D = O / 'cost', O / 'independent-review'
P = C / 'runs/chromium-passive-r4'
assert not (O / 'native-resource.lock').exists(), 'Native resource lease still present; do not run bulk verification'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
record = json.loads((P / 'RESULTS.json').read_bytes())
analysis = json.loads((P / 'ANALYSIS.json').read_bytes())
assert sha(P / 'RESULTS.json') == '766312e519a14e9badc9f3c40b2c75a007177bb08f757846a01e9f7ddf26506e'
assert sha(P / 'ANALYSIS.json') == '1b084157423cfda0009af7c5037961a332cbb6afd737e3cb087684aa50f46273'
sys.path.insert(0, str(C))
from analyse_cost_v3 import analyse
recomputed = analyse(P, record)
assert recomputed == analysis, 'Pinned analyzer recomputation differs'

def summary(values):
    if not values:
        return {'n': 0}
    ordered = sorted(values)
    return {'n': len(values), 'medianMs': statistics.median(values),
            'p95Ms': ordered[math.ceil(.95 * len(ordered)) - 1],
            'totalMs': sum(values), 'maxMs': max(values)}

def utf16slice(text, start, end):
    return text.encode('utf-16-le')[start * 2:end * 2].decode('utf-16-le')

source_map_path = C / 'instrumented-r3/SOURCE-MAP.json'
source_map = json.loads(source_map_path.read_bytes())
font_map = json.loads((C / 'fonts-r1/MANIFEST.json').read_bytes())['files']
slot_sides = {slot['id']: slot['side'] for slot in record['slots']}
served_counts = collections.Counter()
for served in record['requests']:
    assert slot_sides[served['slot']] == served['side']
    assert served['status'] == 200 and served['writeComplete'] is True
    parsed = urlparse(served['path'])
    if parsed.path == '/fixture':
        url = parse_qs(parsed.query)['url'][0]
        payload = record['payloads'][url]
        data = json.dumps(payload['body'], separators=(',', ':')).encode()
        assert hashlib.sha256(data).hexdigest() == payload['sha256'] == served['servedSha256']
        assert len(data) == served['bytes']
        served_counts['providerFixture'] += 1
    else:
        assert parsed.path.startswith('/salah_widget/')
        relative = parsed.path[len('/salah_widget/'):] or 'index.html'
        mapping = source_map['sides'][served['side']]['files'].get(relative)
        if mapping:
            expected_hash, expected_bytes = mapping['instrumentedSha256'], mapping['instrumentedBytes']
        else:
            entry = record['runtime'][served['side']]['files'][relative]
            expected_hash, expected_bytes = entry['sha256'], entry['bytes']
        assert served['servedSha256'] == expected_hash and served['bytes'] == expected_bytes
        served_counts['sourceOrAsset'] += 1
for slot in record['slots']:
    for delivered in slot['fontDeliveries']:
        assert delivered['sha256'] == font_map[delivered['url']]['sha256']
        served_counts['fontDelivery'] += 1
expected, function_checks, file_checks = {}, [], []
for side, mapping in source_map['sides'].items():
    expected[side] = set()
    for relative, file_map in mapping['files'].items():
        path = Path(mapping['root']) / relative
        assert sha(path) == file_map['originalSha256']
        text = path.read_bytes().decode('utf-8')
        file_checks.append({'side': side, 'path': str(path), 'sha256': sha(path)})
        bodies = []
        if relative.endswith('.html'):
            for match in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script\s*>', text, re.I):
                identity = re.search(r'\bid=[\"\']([^\"\']*)[\"\']', match.group(1), re.I)
                bodies.append((identity.group(1) if identity else '', match.group(2)))
        else:
            bodies = [('', text)]
        for part in file_map['parts']:
            for role in part['roles']:
                expected[side].add(role['role'])
                eligible = [body for identity, body in bodies if identity == part.get('scriptId', '')]
                matches = []
                for body in eligible:
                    if len(body.encode('utf-16-le')) < 2 * role['end']:
                        continue
                    candidate = utf16slice(body, role['start'], role['end'])
                    if hashlib.sha256(candidate.encode('utf-8')).hexdigest() == role['originalFunctionSha256']:
                        matches.append(True)
                assert len(matches) == 1, (side, relative, role['role'], len(matches))
                function_checks.append({'side': side, 'file': relative, 'role': role['role'],
                                        'sha256': role['originalFunctionSha256']})

all_values = {side: collections.defaultdict(list) for side in expected}
all_inclusive = {side: collections.defaultdict(list) for side in expected}
blocks = {side: collections.defaultdict(lambda: collections.defaultdict(list)) for side in expected}
slot_receipts, topology, startup_head = [], collections.Counter(), {'A': [], 'B': []}
crossings = []
for slot in record['slots']:
    side = slot['side']
    raw_path = Path(slot['rawFile'])
    if not raw_path.is_absolute():
        raw_path = P / raw_path
    assert raw_path.resolve().is_relative_to(P.resolve())
    assert sha(raw_path) == slot['callsSha256']
    slot_path = raw_path.parent / 'SLOT.json'
    saved_slot = json.loads(slot_path.read_bytes())
    assert saved_slot == slot, ('Saved SLOT differs', slot['id'])
    calls = json.loads(raw_path.read_bytes())
    names, flat = calls['names'], calls['raw']
    assert len(flat) % 7 == 0 and not calls['errors'] and not calls['invalid']
    assert len(set(names)) == len(names)
    assert set(names) <= expected[side] | {'probe.empty', 'probe.parent', 'probe.child'}
    rows = [flat[i:i + 7] for i in range(0, len(flat), 7)]
    assert len(rows) < calls['capacity']
    completed = collections.defaultdict(list)
    prior_end, top_level, maximum_error = -math.inf, 0, 0.0
    steady_count, crossing_count = 0, 0
    start, end = slot['start']['at'], slot['start']['at'] + 5000
    steady_by_name, inclusive_by_name = collections.defaultdict(list), collections.defaultdict(list)
    crossing_by_name = collections.Counter()
    for row_number, row in enumerate(rows):
        scope_id, began, inclusive, exclusive, depth, exception, child_count = row
        assert all(math.isfinite(v) for v in row)
        assert scope_id == int(scope_id) and 0 <= scope_id < len(names)
        assert depth == int(depth) and 0 <= depth < 128 and exception == 0
        assert child_count == int(child_count) and child_count >= 0
        assert 0 <= exclusive <= inclusive and inclusive >= 0
        ended = began + inclusive
        assert ended + 1e-6 >= prior_end, ('Postorder end ordering', slot['id'], row_number)
        prior_end = ended
        depth = int(depth)
        assert not any(v for k, v in completed.items() if k > depth + 1)
        children = completed.pop(depth + 1, [])
        assert len(children) == child_count, ('Direct child count', slot['id'], row_number)
        for child in children:
            assert began - 1e-6 <= child[1] and child[1] + child[2] <= ended + 1e-6
            topology[(side, names[int(scope_id)], names[int(child[0])])] += 1
        error = abs(exclusive - max(0, inclusive - sum(c[2] for c in children)))
        maximum_error = max(maximum_error, error)
        assert error <= 1e-6, ('Exclusive reconstruction', slot['id'], row_number, error)
        if depth:
            completed[depth].append(row)
        else:
            top_level += 1
        name = names[int(scope_id)]
        if name == 'head.prepareNativeFirstPaint' and began < slot['warmStart']['at']:
            startup_head[side].append(inclusive)
        if name.startswith('probe.') or not start <= began < end:
            continue
        steady_count += 1
        if ended > end:
            crossing_count += 1
            crossing_by_name[name] += 1
            crossings.append({'slot': slot['id'], 'rawRow': row_number, 'scope': name,
                              'startMs': began, 'fullInclusiveMs': inclusive,
                              'fullExclusiveMs': exclusive, 'overBoundaryMs': ended - end})
        steady_by_name[name].append(exclusive)
        inclusive_by_name[name].append(inclusive)
        all_values[side][name].append(exclusive)
        all_inclusive[side][name].append(inclusive)
        blocks[side][slot['block']][name].append(exclusive)
    assert not any(completed.values()), ('Unfinished tree', slot['id'])
    for name in expected[side]:
        actual = analysis['perSlot'][slot['id']][name]
        assert actual['exclusive'] == summary(steady_by_name[name]), (slot['id'], name, 'exclusive')
        assert actual['inclusive'] == summary(inclusive_by_name[name]), (slot['id'], name, 'inclusive')
        assert actual['endCrossingCallsIncluded'] == crossing_by_name[name]
        assert actual['callsPerSecond'] == len(steady_by_name[name]) / 5
    slot_receipts.append({'id': slot['id'], 'callsFile': str(raw_path), 'callsSha256': sha(raw_path),
                          'slotFile': str(slot_path), 'slotSha256': sha(slot_path),
                          'rawRowsIncludingControls': len(rows), 'steadyRows': steady_count,
                          'endCrossingRows': crossing_count, 'rootRows': top_level,
                          'maximumExclusiveReconstructionErrorMs': maximum_error,
                          'timingNames': names, 'probeBufferBytes': calls['probeBufferBytes']})

for name, observed in analysis['scopes'].items():
    for side in expected:
        assert observed[side] == summary(all_values[side][name]), (name, side)
        assert observed['inclusive'][side] == summary(all_inclusive[side][name]), (name, side, 'inclusive')
        for block in range(4):
            candidate = summary(blocks[side][block][name])
            actual = observed['blocks'][side].get(str(block), {'n': 0})
            assert actual == candidate, (name, side, block)

old_failures = []
for engine, result_hash, analysis_hash in [
    ('chromium', '795ccc8a488dc22e711f02b17989c3ba3c655ca2ef32d4b925ef36a414d2fc66', '6364e517bf8c66674853c5a50a939a04019bea0ad3c6e77afa89c56fd4dd818d'),
    ('firefox', 'd6f4586873ae845aaa9f66f401e3bbc2ae06f6d26d48749ff977845a5fc3fb19', '959f9c77ee11e52aceb7d764be891502aea0102667c03ec10f4485e0076af7c1'),
]:
    prior = C / 'runs' / f'{engine}-passive-r3'
    assert sha(prior / 'RESULTS.json') == result_hash
    assert sha(prior / 'ANALYSIS.json') == analysis_hash
    old_failures.append({'engine': engine, 'resultsSha256': result_hash, 'analysisSha256': analysis_hash})

receipt = {'schema': 'r0021-independent-measured-cost-verification/v1',
           'sourceResultsSha256': sha(P / 'RESULTS.json'), 'sourceAnalysisSha256': sha(P / 'ANALYSIS.json'),
           'verificationScriptSha256': sha(__file__), 'analyzerRecomputationEqual': True,
           'rawTreeAndStatisticsIndependentlyReconstructed': True,
           'servedSourceAssetAndFixtureRowsVerified': dict(served_counts),
           'scopeVerdicts': dict(collections.Counter(x['status'] for x in analysis['scopes'].values())),
           'sourceMapSha256': sha(source_map_path), 'sourceFiles': file_checks,
           'sourceFunctionChecks': function_checks, 'slots': slot_receipts, 'endCrossings': crossings,
           'callTreeEdges': [{'side': a, 'parent': b, 'child': c, 'countAllSegments': n}
                            for (a, b, c), n in sorted(topology.items())],
           'startupHeadDescriptiveOnly': {s: summary(v) for s, v in startup_head.items()},
           'oldFailuresUnchanged': old_failures,
           'limits': 'Offline readback only, not independent acquisition or new performance evidence. No CPU self-time, presentation, heap-wide allocation/GC, S1/S7 or whole-cost PASS.'}
path = D / 'cost-measured-r4-verification.json'
with path.open('x', encoding='utf-8') as f:
    json.dump(receipt, f, indent=2)
    f.write('\n')
print(json.dumps({'output': str(path), 'sha256': sha(path), 'rawRows': sum(s['rawRowsIncludingControls'] for s in slot_receipts),
                  'steadyRows': sum(s['steadyRows'] for s in slot_receipts), 'endCrossings': len(crossings),
                  'scopeVerdicts': receipt['scopeVerdicts'], 'sourceFunctionChecks': len(function_checks),
                  'startupHeadDescriptiveOnly': receipt['startupHeadDescriptiveOnly']}))
