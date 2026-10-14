"""Independent offline custody/currentness review; no browser or source writes."""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SOURCE = EVIDENCE.parent / 'salah_widget'
AUDIT = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
BASE = 'c431733c57f76e2b441ee8f8cd85a1fa6675de55'
SPEC = '21e7a84365fae37a86cae5c7d5e41008c0adc53f'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def digest_file(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            value.update(block)
    return value.hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE)

def main():
    out = {'schema': 'r0006-independent-bindings/v1', 'sourceBase': BASE,
           'head': git('rev-parse', 'HEAD').decode().strip(),
           'workingStatus': git('status', '--short').decode(), 'failures': []}
    failures = out['failures']
    def check(condition, label):
        if not condition:
            failures.append(label)
        return bool(condition)

    issue = read(EVIDENCE / 'authority/issue.json')
    comments = read(EVIDENCE / 'authority/comments.json')
    audit_comment = next(c for c in comments if c['id'] == 6073060055)
    canonical = git('show', SPEC + ':docs/rlgwo-execution/20261008/REMAINING_RLGWOs/R0006.md')
    out['authority'] = {
        'issueBodySha256': digest(issue['body'].encode()),
        'auditBodySha256': digest(audit_comment['body'].encode()),
        'specSha256': digest(canonical),
        'specCopyEqual': check(canonical == (EVIDENCE / 'authority/R0006-spec.md').read_bytes(), 'spec copy drift'),
        'commentIds': [c['id'] for c in comments],
    }
    check(out['authority']['issueBodySha256'] == '5c79e956277dbc358a0d57071f629518044fe4119f7f0a3c2cbb0797c5febb1e', 'issue body drift')
    check(out['authority']['auditBodySha256'] == '58f1219bef6e5a10133a9cff73ce858098421882e33515b55d55f1c6b2e7843f', 'audit comment drift')

    assessment = read(EVIDENCE / 'authority/accepted-assessment.json')
    original = git('show', AUDIT + ':src/native/index.html').decode().replace('\r\n', '\n').splitlines(keepends=True)
    current = (SOURCE / 'src/native/index.html').read_text(encoding='utf-8')
    consumers = {p: (SOURCE / p).read_text(encoding='utf-8') for p in ['index.html', 'offline.html']}
    spans = {}
    for row in assessment['requirementMatrix']:
        for owner in row['sourceOwners']:
            if owner['path'] == 'src/native/index.html':
                spans.setdefault((owner['lineStart'], owner['lineEnd']), []).append(row['id'])
    out['originalOwnerSpans'] = []
    for (start, end), ids in sorted(spans.items()):
        text = ''.join(original[start - 1:end])
        count = current.count(text)
        consumer_counts = {p: body.count(text) for p, body in consumers.items()}
        check(count == 1, f'authored original owner drift {start}-{end}')
        for p, n in consumer_counts.items():
            check(n == 1, f'generated original owner drift {p}:{start}-{end}')
        out['originalOwnerSpans'].append({'auditStart': start, 'auditEnd': end,
            'rows': ids, 'sha256Normalized': digest(text.encode()),
            'authoredMatchCount': count, 'generatedMatchCounts': consumer_counts})

    out['sourceTests'] = []
    for name in ['r0006-recovery.test.cjs', 'r0003-ownership.test.cjs', 'r0005-adoption.test.cjs', 'r0005-day-return.test.cjs', 'r0004-boot-day.test.cjs']:
        p = 'tests/' + name
        raw = (SOURCE / p).read_bytes()
        old = git('show', AUDIT + ':' + p)
        same = raw.replace(b'\r\n', b'\n') == old.replace(b'\r\n', b'\n')
        check(same, 'original source fixture changed ' + p)
        out['sourceTests'].append({'path': p, 'sha256': digest(raw), 'originalEqualNormalized': same})
    tap = (EVIDENCE / 'source-tests.tap').read_bytes()
    out['retainedCurrentSourceTap'] = {'sha256': digest(tap),
        'summary': tap.decode('utf-8-sig').split('1..72')[-1].strip()}

    declared = read(EVIDENCE / 'currentness.json')
    runtime_rows = []
    for p, v in declared['runtimeFiles'].items():
        sha = digest((SOURCE / p).read_bytes())
        check(sha == v['sha256'], 'runtime receipt drift ' + p)
        check((SOURCE / p).read_bytes() == git('show', BASE + ':' + p), 'runtime changed from base ' + p)
        runtime_rows.append((p, sha))
    aggregate = ''.join(sha + '  ' + p + '\n' for p, sha in sorted(runtime_rows))
    out['runtime'] = {'count': len(runtime_rows), 'aggregateSha256': digest(aggregate.encode())}

    packet = read(SOURCE / 'tests/rlgwo/R0006-cases.json')
    out['candidateFiles'] = {p: digest((SOURCE / p).read_bytes()) for p in ['README.md', 'tests/rlgwo/R0006-cases.json', 'tests/rlgwo/R0006-promotion-polling.json', 'tools/cp9/r0006_verify.py', 'tools/cp9/r0007_browser.py']}
    out['packetSourcePins'] = {}
    for p, expected in packet['sourceFiles'].items():
        sha = digest((SOURCE / p).read_bytes())
        out['packetSourcePins'][p] = {'sha256': sha, 'matches': check(sha == expected, 'packet source pin drift ' + p)}
    fixture = SOURCE / 'tests/rlgwo/prayer-browser-fixture.cjs'
    selected = {c['caseId']: [c] for c in packet['cases']}
    separate = read(SOURCE/'tests/rlgwo/R0006-promotion-polling.json')
    for c in separate['cases']:
        selected[c['caseId']].append(c)
    selection=read(EVIDENCE/'selection.json')
    out['selectionSha256']=digest_file(EVIDENCE/'selection.json')
    out['selectedCount']=len([r for r in selection if r['status'].startswith('SELECTED')])
    check(out['selectedCount']==20,'selected native count differs from20')
    out['completedNativeBindings'] = []
    for item in selection:
        case_root=EVIDENCE/item['source']
        trace=case_root/'trace.json'
        case_path = case_root / 'case-input.json'
        case = read(case_path)
        doc = read(case_root / 'document-hashes.json')
        observed = subprocess.check_output(['node', str(fixture), str(SOURCE / case['entry']), str(case_path)])
        same = check(digest(observed) == doc['observed'], 'observed native HTML drift ' + str(trace))
        check(digest_file(fixture)==doc['fixture'],'fixture bytes differ '+item['source'])
        check(digest_file(SOURCE/case['entry'])==doc['source'],'original consumer bytes differ '+item['source'])
        exact_input = case in selected[case['caseId']]
        if item['status'].startswith('SELECTED'):
            check(exact_input,'selected acquisition input differs from canonical/separate packet '+item['source'])
        trace_status=None
        if trace.exists():
            with trace.open(encoding='utf-8') as stream:
                import re
                trace_status=re.search(r'"status"\s*:\s*"([^"]+)"',stream.read(1024)).group(1)
        out['completedNativeBindings'].append({'path': str(trace.relative_to(EVIDENCE)), 'caseId': case['caseId'],
            'selectionStatus':item['status'],'status':trace_status,'caseSha256': digest(case_path.read_bytes()), 'traceSha256': digest_file(trace) if trace.exists() else None,
            'observedSha256': digest(observed), 'exactObservedHtml': same, 'exactSelectedInput': exact_input,
            'destination':item['destination']})

    reuse = read(EVIDENCE / 'preservation-reuse.json')
    out['preservation'] = []
    verified_files = {}
    for c in reuse['controls']:
        p = SOURCE / c['path']
        case_path = p / 'case-input.json'
        case = read(case_path)
        doc = read(p / 'document-hashes.json')
        observed = subprocess.check_output(['node', str(fixture), str(SOURCE / case['entry']), str(case_path)])
        same = check(digest(observed) == doc['observed'], 'preservation observed HTML drift ' + c['path'])
        check(digest(case_path.read_bytes()) == c['inputSha256'], 'preservation input drift ' + c['path'])
        for f, expected in c['files'].items():
            actual = digest((SOURCE / f).read_bytes())
            verified_files[f] = actual
            check(actual == expected, 'preservation file drift ' + f)
        out['preservation'].append({'path': c['path'], 'caseId': case['caseId'], 'engine': c['engine'],
            'exactObservedHtml': same, 'observedSha256': digest(observed), 'inputSha256': digest(case_path.read_bytes()),
            'filesVerified': len(c['files']), 'recordingMode': c['recording']})
    out['preservationFileCount'] = len(verified_files)
    out['scope'] = 'Read-only custody/currentness; no native or pixel qualification inferred from equality.'
    (ROOT / 'bindings.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'runtime': out['runtime'], 'ownerSpans': len(out['originalOwnerSpans']),
        'nativeCompleted': len(out['completedNativeBindings']), 'preservationControls': len(out['preservation']),
        'preservationFiles': out['preservationFileCount'], 'failures': failures}, indent=2))
    return bool(failures)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
