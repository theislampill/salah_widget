"""Prepare reconciled comments with primary-owned evidence SHA placeholders, then freeze."""
import datetime
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
AUDIT = ROOT.parent.parent
PREFIX = 'docs/rlgwo-audit/20261008'
BASE = f'https://github.com/theislampill/salah_widget/blob/AUDIT_EVIDENCE_COMMIT/{PREFIX}/'
ISSUES = (19, 20, 21, 22, 27, 28)
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
STATUS = 'PRIMARY_RECONCILED_EVIDENCE_URLS_PREPARED_FROZEN_FOR_SHA_BINDING_NOT_POSTED'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    path = ROOT / name
    assert path.resolve().parent == ROOT.resolve()
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

custody = read(ROOT / 'retained-install' / 'CUSTODY.json')
native = read(ROOT / 'native-rebind.json')
assert len(custody['receipts']) == 16
original_receipts = {r['name']: r for r in native['retainedReceipts']}
retained = {}
for r in custody['receipts']:
    published = pathlib.Path(r['publishedRelativePath'])
    assert published.parts[:3] == ('workers', 'E', 'retained-install')
    name = pathlib.PurePosixPath(r['publishedRelativePath']).relative_to('workers/E/retained-install').as_posix()
    copy_path = AUDIT / published
    source_path = pathlib.Path(r['source'])
    assert source_path.read_bytes() == copy_path.read_bytes()
    assert digest(copy_path) == r['sha256'] == original_receipts[name]['sha256']
    retained[name] = {**r, 'publicationUrl': BASE + r['publishedRelativePath']}

KEEP = {
 19: ('host-inventory-final.json', 'native-applicability-2fafcbf.json', 'bash-helper-archived-source.json',
      'bash-entry-archived-source.json', 'bash-mutations-archived-source.json'),
 20: ('host-inventory-final.json', 'final-r0014-ps51.txt', 'final-r0014-ps7.txt', 'direct-native-final.json',
      'r0014-mutant-encoding.txt', 'r0014-mutant-comma-corrected-ps51.txt', 'r0014-mutant-comma-corrected.txt',
      'ps51-mutations-qualified.json', 'ps7-mutations-final-source.json', 'direct-native-mutants.json'),
 21: ('host-inventory-final.json', 'native-applicability-2fafcbf.json', 'bash-helper-archived-source.json',
      'bash-mutations-archived-source.json', 'crossuid-nonlogin/result.json',
      'crossuid-nonlogin/post-run-native-readback-qualified.json'),
 22: ('host-inventory-final.json', 'native-applicability-2fafcbf.json', 'bash-helper-archived-source.json',
      'bash-entry-archived-source.json', 'bash-mutations-archived-source.json', 'final-r0014-ps51.txt',
      'final-r0014-ps7.txt', 'direct-native-final.json', 'ps51-mutations-qualified.json',
      'ps7-mutations-final-source.json', 'direct-native-mutants.json'),
 27: (), 28: (),
}
common = [('release.json', 'Primary verified release'),
          ('public-runtime.json', '139-file runtime and V1 readback'),
          ('public-browser-summary.json', '16-case public rollout summary'),
          ('public-document-distribution.json', 'Raw and Pages script/document bytes'),
          ('reviewer-model-settings.json', 'Client-recorded reviewer model and effort')]
maps = {}
for n in ISSUES:
    entries = [(f'issues/{n}.json', 'Original complete issue packet'),
               (f'workers/E/{n}-assessment.json', 'Full mandatory matrix and issue evidence'),
               ('workers/E/native-rebind.json', 'Exact source and receipt binding')] + common
    if n in (19, 20, 21, 22):
        entries.append(('workers/E/retained-install/CUSTODY.json', 'Retained receipt byte-custody manifest'))
        entries += [(retained[name]['publishedRelativePath'], name) for name in KEEP[n]]
    if n == 19:
        entries += [('workers/E/builder-config-rebind.json', 'Exact-ref builder/configuration rebind'),
                    ('workers/D/fresh-positive-receipts.json', 'Fresh D source-control receipt index'),
                    ('workers/D/r0010-preferences.stdout.log', 'Local/portable/export controls: 9/9'),
                    ('workers/D/r0012-clipboard.stdout.log', 'Builder command and hostile-label controls: 11/11')]
    if n in (27, 28):
        entries.append(('docs-contract-primary.json', 'Fresh primary source/document controls (original JSONL)'))
    for relative, _ in entries:
        assert (AUDIT / relative).is_file(), relative
    maps[n] = [{'relativePath': rel, 'label': label, 'urlTemplate': BASE + rel,
                'sourceSha256': digest(AUDIT / rel)} for rel, label in entries]

assessments = {}
for n in ISSUES:
    a = read(ROOT / f'{n}-assessment.json')
    a['publicationStatus'] = STATUS
    a['primaryReconciliation'] = 'COMPLETED: Primary Astra independently reconciled the mandatory matrix and LEAVE OPEN conclusion. This evidence comment precedes any approved action and does not assert issue closure.'
    a['primaryReconciled'] = True
    # Keep content hashes in the external map: an assessment cannot bind its own hash.
    a['publicationLinks'] = [{k: r[k] for k in ('relativePath', 'label', 'urlTemplate')} for r in maps[n]]
    a['publicationApproval'] = {'shaPlaceholder': 'AUDIT_EVIDENCE_COMMIT', 'repoRelativePrefix': PREFIX,
                                'primaryReconciled': True, 'exactCommentHashApproval': False,
                                'externalEffects': 'NONE', 'proofBeforeAction': True}
    a['publicationWordingPreparedAtUtc'] = NOW
    write(f'{n}-assessment.json', a)
    assessments[n] = a
    text = (ROOT / f'{n}-comment.md').read_text(encoding='utf-8')
    text = text.replace('Primary Astra has reconciled this LEAVE OPEN requirement-gap recommendation in principle. Publication remains HOLD pending the immutable evidence URL and approval of this final comment hash; no comment has been posted.',
                        'Primary Astra independently reconciled the complete mandatory matrix and this LEAVE OPEN conclusion. This evidence comment precedes any approved action; it does not assert that the issue is closed.')
    text = text.replace('The corresponding primary receipts will be bound to the immutable evidence publication before GitHub posting.',
                        'The corresponding immutable evidence references are listed below.')
    text = text.replace('Primary Astra owns final independent reconciliation and any approved publication/closure. This issue-specific recommendation does not establish those external actions.',
                        'Primary Astra has completed independent reconciliation. The conclusion remains LEAVE OPEN for the individual gaps above; proof precedes any approved action. No issue closure or reviewer GitHub mutation is asserted.')
    text = text.replace('Containment/rollback: keep these proposed artifacts local and reversible. Preserve accepted source and immutable failed/retained receipts; revert only inaccurate documentation or fixture changes if a later authorized validation fails.',
                        'Containment/rollback for a later authorized increment: preserve accepted source and immutable failed/retained receipts; revert only inaccurate documentation or fixture changes if their validation fails.')
    text = re.sub(r'\nImmutable audit evidence references:.*?(?=\nThe delivered baseline is established:)', '', text, flags=re.S)
    links = ['Immutable audit evidence references:', '']
    links += [f'- [{r["label"]}]({r["urlTemplate"]})' for r in maps[n]]
    if KEEP[n]:
        links += ['', 'The retained-install files are byte-exact copies of the original historical receipts, verified against CUSTODY.json and the original sources. Copying them is not fresh native execution; their recorded host, fixture and time limits remain binding.']
    links += ['']
    anchor = 'The delivered baseline is established:'
    assert anchor in text
    text = text.replace(anchor, '\n'.join(links) + '\n' + anchor, 1)
    assert 'Publication remains HOLD' not in text and 'in principle' not in text
    assert 'AUDIT_EVIDENCE_COMMIT/' + PREFIX + '/' in text
    assert len(text) <= 65536
    assert all(r['id'] + ': ' in text for r in a['requirementMatrix'])
    assert sum(line.startswith('| ' + str(n) + '-') for line in text.splitlines()) == len(a['requirementMatrix'])
    assert text.count(f'<!-- RLGWO-AUDIT:18ff14860ff41c084b1db5f396bb62aa9c22b1be:{a["canonicalId"]}:2026-10-08 -->') == 1
    (ROOT / f'{n}-comment.md').write_text(text, encoding='utf-8')

custody_binding = {'path': str(ROOT / 'retained-install' / 'CUSTODY.json'),
    'sha256': digest(ROOT / 'retained-install' / 'CUSTODY.json'), 'copies': 16, 'sourceAndCopyBytesEqual': True,
    'scope': 'Historical receipt copying only; no fresh native execution.'}
native['publicationStatus'] = STATUS
native['retainedInstallPublication'] = custody_binding
native['primaryReconciled'] = True
write('native-rebind.json', native)
# Refresh link hashes after the referenced artifacts have their final publication metadata.
for n, entries in maps.items():
    for r in entries:
        r['sourceSha256'] = digest(AUDIT / r['relativePath'])
write('evidence-publication-map.json', {'worker': 'E', 'repoRelativePrefix': PREFIX,
    'shaPlaceholder': 'AUDIT_EVIDENCE_COMMIT', 'primaryReconciled': True,
    'issues': {str(n): entries for n, entries in maps.items()},
    'custodySha256': digest(ROOT / 'retained-install' / 'CUSTODY.json'),
    'retainedReceiptCopies': 16, 'allSourceAndCopyBytesEqual': True})
comment_hashes = {f'{n}-comment.md': digest(ROOT / f'{n}-comment.md') for n in ISSUES}
summary = read(ROOT / 'summary.json')
summary['publicationStatus'] = STATUS
summary['primaryReconciled'] = True
summary['primaryReconciliation'] = 'COMPLETED for all six mandatory matrices and LEAVE OPEN conclusions; proof precedes any approved action.'
summary['publicationApproval'] = {'shaPlaceholder': 'AUDIT_EVIDENCE_COMMIT', 'repoRelativePrefix': PREFIX,
    'primaryReconciled': True, 'exactCommentHashApproval': False, 'externalEffects': 'NONE', 'proofBeforeAction': True}
summary['preparedCommentSha256'] = comment_hashes
summary['frozenForPrimaryShaBinding'] = True
summary['publicationMap'] = {'path': str(ROOT / 'evidence-publication-map.json'), 'sha256': digest(ROOT / 'evidence-publication-map.json')}
summary['retainedInstallCustody'] = custody_binding
summary['stoppedAt'] = 'Publication wording and SHA-placeholder links finalized. E files frozen for primary immutable SHA binding and exact-comment approval; no additional worker edits or effects.'
write('summary.json', summary)

ready = read(ROOT / 'publication-ready.json')
ready['status'] = STATUS
ready['primaryReconciled'] = True
ready['frozenForPrimaryShaBinding'] = True
ready['approval'] = summary['publicationApproval']
ready['publicationMap'] = summary['publicationMap']
ready['preparedAtUtc'] = NOW
for r in ready['files']:
    path = pathlib.Path(r['path'])
    r['sha256'] = digest(path)
    r['bytes'] = path.stat().st_size
    r['approvedForPosting'] = False
ready['receiptSourcesForPrimaryPublication'] = [
    {'name': name, 'path': str(AUDIT / r['publishedRelativePath']), 'sha256': r['sha256'],
     'publishedRelativePath': r['publishedRelativePath'], 'publicationUrl': r['publicationUrl'], 'provenance': r['provenance']}
    for name, r in retained.items()] + [r for r in ready['receiptSourcesForPrimaryPublication'] if 'name' not in r]
write('publication-ready.json', ready)
validation = read(ROOT / 'artifact-validation.json')
validation['publicationStatus'] = STATUS
validation['primaryReconciled'] = True
validation['publicationWordingValidatedAtUtc'] = NOW
validation['retainedInstallCopiesByteExact'] = 16
validation['allMandatoryRowsPreserved'] = 80
validation['frozenForPrimaryShaBinding'] = True
validation['readyFileHashes'] = {pathlib.Path(r['path']).name: r['sha256'] for r in ready['files']}
write('artifact-validation.json', validation)
assert all(digest(pathlib.Path(r['path'])) == r['sha256'] for r in ready['files'])
assert all(digest(AUDIT / r['relativePath']) == r['sourceSha256'] for entries in maps.values() for r in entries)
print(json.dumps({'primaryReconciled': True, 'mandatoryRowsPreserved': 80,
    'retainedInstallCopiesByteExact': 16, 'shaPlaceholder': 'AUDIT_EVIDENCE_COMMIT',
    'frozenForPrimaryShaBinding': True, 'githubEffects': 'NONE', 'commentSha256': comment_hashes}))
