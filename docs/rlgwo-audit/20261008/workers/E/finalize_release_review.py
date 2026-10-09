"""Finalize E review artifacts after the verified public baseline; publication stays held."""
import collections
import copy
import datetime
import hashlib
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
AUDIT = ROOT.parent.parent
REPO = pathlib.Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
SHA = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
TREE = '35208181eea714c17f5e77b2644e76434345db60'
ISSUES = (19, 20, 21, 22, 27, 28)
STATUS = 'READY_FOR_IMMUTABLE_EVIDENCE_AND_PER_FILE_APPROVAL_NOT_POSTED'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, value):
    path = ROOT / name
    assert path.resolve().parent == ROOT.resolve()
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])

def record(path):
    return {'path': str(path), 'sha256': sha(path)}

def immutable(path, start=1, end=None):
    end = start if end is None else end
    return {'path': path, 'start': start, 'end': end,
            'url': f'https://github.com/theislampill/salah_widget/blob/{SHA}/{path}#L{start}-L{end}'}

assert git('status', '--short').decode().strip() == ''
assert git('rev-parse', f'{SHA}^{{tree}}').decode().strip() == TREE
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE
release = read(AUDIT / 'release.json')
browser = read(AUDIT / 'public-browser-summary.json')
runtime = read(AUDIT / 'public-runtime.json')
distribution = read(AUDIT / 'public-document-distribution.json')
settings = read(AUDIT / 'reviewer-model-settings.json')
assert release['status'] == 'DELIVERED_VERIFIED'
assert release['AUDIT_SHA'] == release['main'] == release['mergeCommit'] == SHA
assert release['tree'] == TREE and release['publicBrowserCases'] == 16
assert release['pagesBuild']['commit'] == SHA and release['pagesBuild']['status'] == 'built'
assert browser['AUDIT_SHA'] == SHA and len(browser['cases']) == 16
assert collections.Counter(c['browser'] for c in browser['cases']) == {'chromium': 8, 'firefox': 8}
assert all(c['status'] == 'PASS' and all(v is True for v in c['checks'].values()) for c in browser['cases'])
assert len(runtime['checks']) == 139 and runtime['mergeCommit'] == SHA
assert runtime['pagesBuild']['commit'] == SHA and all(c['passed'] for c in runtime['checks'])
assert len(distribution) == 16 and all(r['status'] == 200 and r['expected'] == r['observed'] and r['match'] for r in distribution)
assert all(r['observed'] == hashlib.sha256(git('show', f'{SHA}:{r["file"]}')).hexdigest() for r in distribution)
session = next(s for s in settings['sessions'] if s['session']['agent_path'] == '/root/rlgwo_e')
assert all(t['model'] == 'gpt-6.1-sol' and t['effort'] == 'max' for t in session['turnConfigurations'])

baseline = {'status': 'DELIVERED_VERIFIED', 'target': SHA, 'tree': TREE, 'verifiedAt': release['verifiedAt'],
            'releaseReceipt': record(AUDIT / 'release.json'),
            'browserReceipt': record(AUDIT / 'public-browser-summary.json'),
            'runtimeReceipt': record(AUDIT / 'public-runtime.json'),
            'documentReceipt': record(AUDIT / 'public-document-distribution.json'),
            'pagesBuild': 1270547036, 'runtimeAndV1FilesMatched': 139, 'publicRawPagesDocumentsMatched': 16,
            'browserCases': 16, 'browserAllPass': True,
            'browserCaseChecks': [{k: c[k] for k in ('browser', 'name', 'status', 'checks', 'receipt')} for c in browser['cases']],
            'limits': browser['limits'],
            'scope': 'Primary established the exact public release baseline. E verified receipt/target identities and all recorded case checks read-only; this does not recertify every backlog/native/diagnostic/documentation obligation.'}
approval = {'status': 'HOLD', 'immutableEvidenceUrl': None, 'perCommentHashApproval': 'NOT_YET_GIVEN',
            'reason': 'Primary must bind the immutable evidence publication and approve each final comment hash before any GitHub write.',
            'sourceOrMainChange': 'NONE authorized here', 'newIssue33StartupScope': 'Separate owner increment; no alteration of these six issue contracts or requirement gaps.'}

# Independently rebind the two fresh D controls through the actual exact-ref fixture/source loader.
d_receipts = read(AUDIT / 'workers' / 'D' / 'fresh-positive-receipts.json')
d_source = read(AUDIT / 'workers' / 'D' / 'source-identity.json')
assert d_source['target'] == SHA and d_source['tree'] == TREE
assert d_source['sourceBuilderSha256'] == d_source['deliveredBuilderSha256'] == hashlib.sha256(git('show', f'{SHA}:builder.html')).hexdigest()
assert d_source['sourceConfigSha256'] == d_source['deliveredConfigSha256'] == hashlib.sha256(git('show', f'{SHA}:config.js')).hexdigest()
matched = []
for name, count in (('r0010-preferences', 9), ('r0012-clipboard', 11)):
    r = next(r for r in d_receipts if r['name'] == name)
    assert r['target'] == SHA and r['expectedExitCode'] == r['observedExitCode'] == 0
    assert r['command'][-2:] == ['--ref', SHA]
    stdout = pathlib.Path(r['stdout'])
    stderr = pathlib.Path(r['stderr'])
    assert sha(stdout) == r['stdoutSha256'] and sha(stderr) == r['stderrSha256']
    lines = stdout.read_text(encoding='utf-8-sig').splitlines()
    last = json.loads(lines[-1])
    assert last == {'cases': count, 'passed': count, 'failed': 0, 'ref': SHA, 'mutant': None, 'native': 'NOT_RUN'}
    assert len([s for s in lines[:-1] if s.startswith('PASS ')]) == count and not stderr.read_bytes()
    matched.append({**r, 'allResultLines': lines[:-1], 'summary': last})
fixtures = ('tests/r0010-preferences.cjs', 'tests/r0012-clipboard.cjs', 'tests/r000f-fixture.cjs', 'tests/r0011-fixture.cjs')
fixture_records = [{'path': p, 'blob': git('rev-parse', f'{SHA}:{p}').decode().strip(),
                    'sha256': hashlib.sha256(git('show', f'{SHA}:{p}')).hexdigest()} for p in fixtures]
assert all((REPO / p['path']).read_bytes().replace(b'\r\n', b'\n') == git('show', f'{SHA}:{p["path"]}').replace(b'\r\n', b'\n') for p in fixture_records)
packet19 = read(AUDIT / 'issues' / '19.json')
canonical_literal = re.search(r'Malicious label literal `([^`]+)` through builder', packet19['issue']['body']).group(1)
builder_proof = {'executedBy': 'D', 'target': SHA,
                 'receiptIndex': record(AUDIT / 'workers' / 'D' / 'fresh-positive-receipts.json'),
                 'sourceIdentity': record(AUDIT / 'workers' / 'D' / 'source-identity.json'),
                 'fixtures': fixture_records, 'results': matched,
                 'binding': 'D executed unchanged checked-in fixtures with --ref at the exact audited commit; r000f-fixture loads actual config.js and complete builder script through git show. E read those assertions and the complete logs, then verified source and log hashes. No test was rerun by E.',
                 'canonicalLiteralNotation': canonical_literal,
                 'recordedHostileBuilderLabel': "O'Brien \"quoted\" & Madinah\nمدينة $(echo literal) `literal`",
                 'recordedPortableSerializerLabel': "A & B'#<>",
                 'inputRelevance': 'The combined exact-source controls demonstrate every character class of the original adversarial label, including quotes, ampersand, newline, Unicode, substitution/backticks and angle brackets, through the unchanged canonical URLSearchParams serializer and actual builder consumers. The record does not claim that the canonical combined literal was itself rerun.',
                 'limits': ['Contained source/DOM/provider/clipboard VM doubles; no actual shell execution, native browser installation, profile mutation or external transmission.',
                            'Apple native detector/terminal/filesystem obligations are separate and still unverified.',
                            'Rendered-document and special diagnostic browser proofs are separate from the verified public rollout.']}
write('builder-config-rebind.json', builder_proof)

assessments = {n: read(ROOT / f'{n}-assessment.json') for n in ISSUES}
comments = {n: (ROOT / f'{n}-comment.md').read_text(encoding='utf-8') for n in ISSUES}
summary = read(ROOT / 'summary.json')
native = read(ROOT / 'native-rebind.json')
row19 = next(r for r in assessments[19]['requirementMatrix'] if r['id'] == '19-08')
row19.update(status='satisfied',
    expected='Actual delivered builder/canonical serializer preserve an encoded shell value and exact hostile-label decode, local coordinate omission and the existing permission/card contracts.',
    observed='Fresh D r0010-preferences 9/9 and r0012-clipboard 11/11 at the exact ref demonstrate actual local/portable hash, snippet/preview/command carry-through, omitted local coordinates, existing permission prose, and hostile label exact decode with %27/%0A; a separate portable serializer control verifies #/angle-bracket encoding and exact decode. The combined input-relevant controls exercise all original adversarial character classes through unchanged actual source; recorded payloads differ from the canonical combined literal, which was not rerun. Generated Windows/Bash strings match expected grammar; no shell or browser installation was executed. Immutable authored/delivered builder/config blobs and supplied public byte hashes match; preserved card/permission policy is mapped in 19-11.',
    evidence_basis='Fresh independently source-bound D executions, assertion and complete-log review plus exact source/fixture hash verification by E; no new execution by E.',
    evidenceReceipt={'path': str(ROOT / 'builder-config-rebind.json'), 'sha256': sha(ROOT / 'builder-config-rebind.json')})
row19['discriminator'] = [immutable('tests/r0010-preferences.cjs', 17, 52), immutable('tests/r0012-clipboard.cjs', 49, 65),
                         immutable('tests/r0012-clipboard.cjs', 93, 98), immutable('tests/r000f-fixture.cjs', 9, 11),
                         immutable('tests/r000f-fixture.cjs', 96, 125)]
assessments[19]['builderConfigurationEvidence'] = builder_proof
assessments[19]['gaps'] = [s for s in assessments[19]['gaps'] if s != 'Current adversarial builder/config roundtrip remains unverified.']
assessments[19]['proposedNextIncrement']['gaps'] = assessments[19]['gaps']
assessments[19]['proposedNextIncrement']['scope'] = 'README installer usage and uncovered native detector/PTY controls; preserve the qualified installer and builder/configuration source and their source-bound positive/negative evidence.'
assessments[19]['proposedNextIncrement']['steps'][1] = 'Complete uncovered both-family zero/one/multiple/backslash and empty-array cases. Reuse the demonstrated exact-source builder/configuration controls; requalify only changed serializer or generated-command inputs. Preserve existing negative and mutation expectations.'
assessments[19]['executedCommands'] = [c for c in assessments[19]['executedCommands'] if c.get('executedBy') != 'D']
for r in matched:
    assessments[19]['executedCommands'].append({'command': r['command'], 'executedBy': 'D', 'startedAtUtc': r['startedAtUtc'],
        'environment': 'Exact-ref Node source/DOM/provider/clipboard VM; native NOT_RUN; no installation or transmission.',
        'expected': 'Original local/export/literal and actual builder/copy consumer contracts discriminate output and recovery.',
        'observed': r['summary'], 'stdoutSha256': r['stdoutSha256'], 'stderrSha256': r['stderrSha256']})
row28 = next(r for r in assessments[28]['requirementMatrix'] if r['id'] == '28-06')
row28['observed'] = 'The delivered baseline is now verified: 16 public Chromium/Firefox root/V1 direct/iframe cold/warm rollout cases PASS. That smoke checks the normal 1x card/prayer/assets/terrain/replacement baseline; it does not record the complete production diagnostic fragment q/debugMotion overlay or motion=full under reduced-motion required by this cell. E did not launch a browser. These specific diagnostic readbacks remain unverified; baseline availability is no longer a gap.'
row28['evidenceReceipt'] = record(AUDIT / 'public-browser-summary.json')

reconciliation_text = 'Primary Astra has reconciled all six LEAVE OPEN requirement-gap recommendations in principle and established the delivered baseline. Final immutable evidence URL and individual comment-hash approval remain required before publication.'
for n, a in assessments.items():
    a['finalizedAtUtc'] = NOW
    a['publicBaseline'] = baseline
    a['publicationStatus'] = STATUS
    a['publicationApproval'] = approval
    a['primaryReconciliation'] = reconciliation_text
    a['authority']['doneWhen'] = 'Ready final six-packet return and per-file hashes; primary evidence publication and individual comment approval remain separate.'
    assert a['authority']['clientRecordedModel'] == 'gpt-6.1-sol' and a['authority']['clientRecordedReasoning'] == 'max'
    a['authority']['modelConfigurationReceipt'] = {**record(AUDIT / 'reviewer-model-settings.json'),
        'confirmationKind': settings['confirmationKind'], 'agentPath': '/root/rlgwo_e',
        'sessionId': session['session']['id'], 'turnConfigurations': session['turnConfigurations']}
    a['negativeControls'] = [copy.deepcopy(r) for r in a['requirementMatrix'] if any(w in r['obligation'].lower() for w in ('negative', 'mutant', 'disabled', 'reject', 'refus'))]
    write(f'{n}-assessment.json', a)

def escaped(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def links(items):
    return '; '.join(f'[{p["path"]}:{p["start"]}-{p["end"]}]({p["url"]})' for p in items)

baseline_paragraph = ('The delivered baseline is established: primary release `DELIVERED_VERIFIED`, exact Pages build `1270547036`, '
                     '139 runtime/V1 file hashes and 16 raw/Pages document/script readbacks match the audited commit. '
                     'All 16 public Chromium/Firefox root/V1 direct/iframe cold/warm rollout cases pass. '
                     'Full terrain and explicit replacement at the unchanged normal 1x scene are recorded in both browsers’ root iframe cold/warm cases. '
                     'This is a bounded release baseline; it does not assert every native, diagnostic, documentation or scientific gate passed.')
baseline_hashes = ('Baseline receipt SHA256: release `' + sha(AUDIT / 'release.json') + '`, browser summary `' + sha(AUDIT / 'public-browser-summary.json')
                   + '`, 139-file runtime readback `' + sha(AUDIT / 'public-runtime.json') + '`, document/script readback `'
                   + sha(AUDIT / 'public-document-distribution.json') + '`. The corresponding primary receipts will be bound to the immutable evidence publication before GitHub posting.')
for n, text in comments.items():
    a = assessments[n]
    text = re.sub(r'\*\*Recommendation: LEAVE OPEN\.\*\*[^\n]*', '**Recommendation: LEAVE OPEN.** ' + ' '.join(a['gaps']), text, count=1)
    text = text.replace('The primary accepted the LEAVE OPEN recommendation in principle. This revised comment remains proposed and unpublished pending final individual reconciliation and delivered browser-baseline confirmation.',
                        'Primary Astra has reconciled this LEAVE OPEN requirement-gap recommendation in principle. Publication remains HOLD pending the immutable evidence URL and approval of this final comment hash; no comment has been posted.')
    # Replace a prior baseline block on rerun while preserving all existing proof tables.
    text = re.sub(r'\nThe delivered baseline is established:.*?\n\nBaseline receipt SHA256:.*?\n', '', text, flags=re.S)
    anchor = 'Current public byte-distribution proof'
    assert anchor in text
    text = text.replace(anchor, baseline_paragraph + '\n\n' + baseline_hashes + '\n\n' + anchor, 1)
    matrix = ['| Obligation | Authored owner / delivered consumer | Discriminator; expected → observed | Status |', '|---|---|---|---|']
    for r in a['requirementMatrix']:
        discriminator = links(r['discriminator']) or 'Exact source/receipt readback with execution attribution above/below'
        matrix.append('| ' + ' | '.join((escaped(r['id'] + ': ' + r['obligation']), links(r['authored_owner_and_delivered_consumer']),
                        escaped(discriminator + '; EXPECTED: ' + r['expected'] + ' OBSERVED: ' + r['observed']), r['status'].upper())) + ' |')
    pattern = r'\| Obligation \| Authored owner / delivered consumer \| Discriminator; expected → observed \| Status \|\n\|---\|---\|---\|---\|\n(?:\|[^\n]*\n)+'
    text, changed = re.subn(pattern, lambda _: '\n'.join(matrix) + '\n', text, count=1)
    assert changed == 1
    if n == 19:
        text = re.sub(r'\nFresh D builder/configuration receipt core:.*?\n```\n', '', text, flags=re.S)
        core = {'target': SHA, 'executedBy': 'D', 'reboundBy': 'E',
                'controls': [{'name': r['name'], 'startedAtUtc': r['startedAtUtc'], 'summary': r['summary'],
                              'stdoutSha256': r['stdoutSha256'], 'stderrSha256': r['stderrSha256']} for r in matched],
                'canonicalLiteralNotation': canonical_literal,
                'recordedHostileBuilderLabel': builder_proof['recordedHostileBuilderLabel'],
                'recordedPortableSerializerLabel': builder_proof['recordedPortableSerializerLabel'],
                'inputRelevance': builder_proof['inputRelevance'], 'limits': builder_proof['limits']}
        insert = 'Fresh D builder/configuration receipt core:\n\n```json\n' + json.dumps(core, indent=2, ensure_ascii=False) + '\n```\n\n'
        text = text.replace('**Next RLGWO increment required for closure**', insert + '**Next RLGWO increment required for closure**', 1)
        section = '**Next RLGWO increment required for closure**\n\nSemantic owner/scope: ' + a['proposedNextIncrement']['scope'] + '\n\n'
        section += 'Preserve completed source/consumer work and the original positive/negative expectations. This proposal is not authorization for production edits or publication.\n\n'
        section += '\n'.join(f'{i}. {step}' for i, step in enumerate(a['proposedNextIncrement']['steps'], 1)) + '\n\n'
        text = re.sub(r'\*\*Next RLGWO increment required for closure\*\*.*?(?=Acceptance and closure proof:)', lambda _: section, text, flags=re.S, count=1)
    assert 'pending final individual reconciliation and delivered browser-baseline confirmation' not in text
    assert 'Primarysmokereceiptwasnotyetavailable' not in text
    assert 'Primary smoke receipt was not available at assembly' not in text
    assert 'Publication remains HOLD pending the immutable evidence URL' in text
    assert len(text) <= 65536
    (ROOT / f'{n}-comment.md').write_text(text, encoding='utf-8')

summary['capturedAtUtc'] = NOW
summary['finalizedAtUtc'] = NOW
summary['publicBaseline'] = baseline
summary['publicationStatus'] = STATUS
summary['publicationApproval'] = approval
summary['primaryReconciliation'] = reconciliation_text
summary['results'] = [{'issue': n, 'canonicalId': a['canonicalId'], 'verdict': 'LEAVE OPEN',
    'assessment': f'{n}-assessment.json', 'comment': f'{n}-comment.md', 'gaps': a['gaps'],
    'mandatoryRows': len(a['requirementMatrix']),
    'statusCounts': {status: sum(r['status'] == status for r in a['requirementMatrix'])
                   for status in ('satisfied', 'validly superseded', 'unmet', 'unverified')}} for n, a in assessments.items()]
summary['exactMissingChecksRequested'] = [r for r in summary['exactMissingChecksRequested'] if r['scope'] != '#19 maliciousbuilder']
summary['qualifiedBuilderConfiguration'] = {'path': str(ROOT / 'builder-config-rebind.json'), 'sha256': sha(ROOT / 'builder-config-rebind.json'),
    'scope': builder_proof['inputRelevance'], 'executions': [r['summary'] for r in matched]}
summary['stoppedAt'] = 'Final six proposed comments and assessments ready with per-file hashes. Await immutable evidence URL and primary per-comment approval; no extra browser/test campaign or external write.'
write('summary.json', summary)
native['publicBaseline'] = baseline
native['publicationStatus'] = STATUS
native['builderConfigurationReceipt'] = {'path': str(ROOT / 'builder-config-rebind.json'), 'sha256': sha(ROOT / 'builder-config-rebind.json')}
native['authority']['modelConfigurationReceipt'] = summary['authority']['modelConfigurationReceipt'] = assessments[19]['authority']['modelConfigurationReceipt']
native['modelConfigurationReceipt'] = assessments[19]['authority']['modelConfigurationReceipt']
summary['freshPrimaryEvidence']['modelConfiguration'] = assessments[19]['authority']['modelConfigurationReceipt']
native['authority']['doneWhen'] = summary['authority']['doneWhen'] = 'Final six-packet return and per-file hash manifest; publication remains a separate primary action.'
write('native-rebind.json', native)
write('summary.json', summary)

# Custody manifest gives primary concrete files to publish and approve without moving or replaying receipts.
ready_files = []
for n in ISSUES:
    a = read(ROOT / f'{n}-assessment.json')
    c = (ROOT / f'{n}-comment.md').read_text(encoding='utf-8')
    original = read(AUDIT / 'issues' / f'{n}.json')
    assert hashlib.sha256(original['issue']['body'].encode()).hexdigest() == a['originalBodySha256']
    assert a['verdict'] == 'LEAVE OPEN' and a['publicationStatus'] == STATUS
    assert c.count(f'<!-- RLGWO-AUDIT:{SHA}:{a["canonicalId"]}:2026-10-08 -->') == 1
    assert all(r['id'] + ': ' in c for r in a['requirementMatrix'])
    assert 'delivered browser-baseline confirmation' not in c
    assert 'client turn_context confirms `gpt-6.1-sol/max`' in c
    assert a['publicBaseline']['status'] == 'DELIVERED_VERIFIED'
    for suffix in ('assessment.json', 'comment.md'):
        path = ROOT / f'{n}-{suffix}'
        ready_files.append({'issue': n, 'canonicalId': a['canonicalId'], 'kind': suffix, 'path': str(path),
                            'sha256': sha(path), 'bytes': path.stat().st_size, 'approvedForPosting': False})
assert next(r for r in assessments[19]['requirementMatrix'] if r['id'] == '19-08')['status'] == 'satisfied'
assert next(r for r in assessments[28]['requirementMatrix'] if r['id'] == '28-06')['status'] == 'unverified'
assert all(sha(pathlib.Path(r['path'])) == r['sha256'] for r in native['retainedReceipts'])
assert git('status', '--short').decode().strip() == ''
copy_sources = list(native['retainedReceipts']) + [record(AUDIT / name) for name in
    ('release.json', 'public-browser-summary.json', 'public-runtime.json', 'public-document-distribution.json',
     'reviewer-model-settings.json', 'docs-contract-primary.json')]
copy_sources += [record(pathlib.Path(r[key])) for r in matched for key in ('stdout', 'stderr')]
write('publication-ready.json', {'worker': 'E', 'target': SHA, 'preparedAtUtc': NOW,
    'status': STATUS, 'approval': approval, 'files': ready_files, 'receiptSourcesForPrimaryPublication': copy_sources,
    'limits': ['These hashes bind current comment contents only. Any later evidence URL or text change requires recomputed per-file hashes and primary approval.',
               'No publication, issue closure, production/source/main mutation or additional test/browser execution by E.']})
validation = read(ROOT / 'artifact-validation.json')
validation['validatedAtUtc'] = NOW
validation['publicBaselineStatus'] = 'DELIVERED_VERIFIED'
validation['publicBrowserCasesVerifiedFromPrimary'] = 16
validation['runtimeAndV1FileHashesVerifiedFromPrimary'] = 139
validation['builderConfigurationExactRefDResults'] = [r['summary'] for r in matched]
validation['mandatoryRows'] = sum(r['mandatoryRows'] for r in summary['results'])
validation['matrixCounts'] = {r['issue']: r['statusCounts'] for r in summary['results']}
validation['publicationStatus'] = STATUS
validation['readyFileHashes'] = {pathlib.Path(r['path']).name: r['sha256'] for r in ready_files}
assert validation['mandatoryRows'] == 80
write('artifact-validation.json', validation)
print(json.dumps({'status': STATUS, 'sourceMutation': 'NONE', 'publication': 'NONE',
                  'matrixRows': 80, 'matrixCounts': validation['matrixCounts'],
                  'publicBaseline': 'DELIVERED_VERIFIED', 'publicBrowserCases': 16,
                  'builderDControls': [r['summary'] for r in matched],
                  'commentSha256': {pathlib.Path(r['path']).name: r['sha256'] for r in ready_files if r['kind'] == 'comment.md'}}, ensure_ascii=False))
