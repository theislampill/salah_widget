"""Apply bounded primary evidence to E packets; never writes outside workers/E."""
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
STATUS = 'PROPOSED_ONLY_NOT_RECONCILED_NOT_POSTED'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write_json(name, value):
    destination = ROOT / name
    assert destination.resolve().parent == ROOT.resolve()
    destination.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*arguments):
    return subprocess.check_output(['git', '-C', str(REPO), *arguments])

def receipt(name):
    path = AUDIT / name
    return {'path': str(path), 'sha256': digest(path)}

def link(path, start=1, end=None):
    end = start if end is None else end
    return {'path': path, 'start': start, 'end': end,
            'url': f'https://github.com/theislampill/salah_widget/blob/{SHA}/{path}#L{start}-L{end}'}

native = read_json(ROOT / 'native-rebind.json')
summary = read_json(ROOT / 'summary.json')
assessments = {n: read_json(ROOT / f'{n}-assessment.json') for n in ISSUES}
old_comments = {n: (ROOT / f'{n}-comment.md').read_text(encoding='utf-8') for n in ISSUES}
distribution = read_json(AUDIT / 'public-document-distribution.json')
settings = read_json(AUDIT / 'reviewer-model-settings.json')
run_rows = [json.loads(line) for line in (AUDIT / 'docs-contract-primary.json').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
run_summary = run_rows[-1]
assert run_summary['summary']['sourceRef'] == SHA
assert run_summary['summary'] == {'cases': 39, 'passed': 18, 'failed': 21, 'scope': 'source-and-docs',
                                  'sourceRef': SHA, 'browser': 'NOT_RUN', 'network': 'intercepted, no transmission'}
named_checks = {r['name']: r for r in run_rows[:-1]}
assert len(named_checks) == 39
assert collections.Counter(r['status'] for r in named_checks.values()) == {'PASS': 18, 'FAIL': 21}
assert git('status', '--short').decode().strip() == ''
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE
assert git('rev-parse', f'{SHA}^{{tree}}').decode().strip() == TREE

expected_files = {'install.sh', 'install.ps1', 'README.md', 'AGENTS.md', 'DESIGN.md', 'OPTICS.md', 'builder.html', 'config.js'}
assert len(distribution) == 16 and {r['file'] for r in distribution} == expected_files
source_hashes = {name: hashlib.sha256(git('show', f'{SHA}:{name}')).hexdigest() for name in expected_files}
for name in sorted(expected_files):
    matching = [r for r in distribution if r['file'] == name]
    assert len(matching) == 2
    assert {r['url'].split('/')[2] for r in matching} == {'raw.githubusercontent.com', 'theislampill.github.io'}
    assert all(r['status'] == 200 and r['match'] and r['expected'] == r['observed'] == source_hashes[name] for r in matching)
    assert all(f'?audit={SHA}' in r['url'] for r in matching)
    assert all(f'/{SHA}/{name}' in r['url'] for r in matching if 'raw.githubusercontent.com' in r['url'])
assert run_summary['fixtureSha256'] == hashlib.sha256(git('show', f'{SHA}:tests/rlgwo-docs-contract.cjs')).hexdigest()
assert all(run_summary['sha256'][name] == source_hashes[name] for name in expected_files if name in run_summary['sha256'])
for name in ('index.html', 'ARCHITECTURE.md', 'HANDOFF.md'):
    assert run_summary['sha256'][name] == hashlib.sha256(git('show', f'{SHA}:{name}')).hexdigest()

session = next(s for s in settings['sessions'] if s['session']['agent_path'] == '/root/rlgwo_e')
assert all(t['model'] == 'gpt-6.1-sol' and t['effort'] == 'max' for t in session['turnConfigurations'])
model_record = {**receipt('reviewer-model-settings.json'), 'confirmationKind': settings['confirmationKind'],
                'agentPath': '/root/rlgwo_e', 'sessionId': session['session']['id'],
                'turnConfigurations': session['turnConfigurations']}
public_record = {**receipt('public-document-distribution.json'), 'target': SHA, 'checks': distribution,
                 'scope': 'Primary executed HTTP acquisition; E read the complete record and independently compared exact Git bytes. E did not repeat HTTP.',
                 'limit': 'HTTP 200 plus SHA256 equality proves distributed bytes; it does not prove rendered legibility, a generated command interaction, or native platform execution.'}
source_record = {**receipt('docs-contract-primary.json'), 'format': 'JSONL despite .json extension',
                 'executedBy': 'primary', 'command': f'node tests/rlgwo-docs-contract.cjs . --ref={SHA}',
                 'exitCode': 1, 'summary': run_summary['summary'], 'fixtureSha256': run_summary['fixtureSha256'],
                 'sourceSha256': run_summary['sha256'],
                 'scope': 'Fresh primary controlled source/doc execution; E reviewed original assertions, all 39 result rows, and source/fixture hash identity. No browser or external request.'}

def update_authority(authority, issue=None):
    authority['actualBackendModel'] = 'NOT_INDEPENDENTLY_ATTESTED'
    authority['actualEffectiveReasoning'] = 'max (confirmed by client-recorded turn_context)'
    authority['clientRecordedModel'] = 'gpt-6.1-sol'
    authority['clientRecordedReasoning'] = 'max'
    authority['modelNote'] = 'The local client turn_context confirms gpt-6.1-sol/max for this reviewer; this is not independent hardware/backend attestation.'
    authority['modelConfigurationReceipt'] = model_record
    authority['testsExecuted'] = 'NONE by E; fresh primary docs-contract execution is separately attributed in the matching issue evidence.'
    if issue in (27, 28):
        authority['assumptions'] = [s for s in authority['assumptions'] if 'Apple' not in s and 'Native receipt reuse' not in s]
        note = 'Fresh primary controls prove only the exact source/document behavior exercised at their bound fixture/source hashes; browser rendering requires separate proof.'
        if note not in authority['assumptions']:
            authority['assumptions'].append(note)

update_authority(native['authority'])
update_authority(summary['authority'])
native['reconciledEvidenceAtUtc'] = NOW
native['documentDistributionReceipt'] = public_record
native['primarySourceControlsReceipt'] = source_record
native['modelConfigurationReceipt'] = model_record
if 'absentRequiredOwners' in native['primaryPublicReceipt']:
    native['primaryPublicReceipt']['ownersAbsentFromEarlierRuntimeReceiptNowCovered'] = native['primaryPublicReceipt'].pop('absentRequiredOwners')
if 'coverageAtOriginalCapture' in native['primaryPublicReceipt']:
    native['primaryPublicReceipt']['ownersAbsentFromEarlierRuntimeReceiptNowCovered'] = native['primaryPublicReceipt'].pop('coverageAtOriginalCapture')
native['primaryPublicReceipt']['limit'] = 'Earlier runtime receipt coverage only. All named script/document byte-distribution owners are now covered by documentDistributionReceipt; rendered/browser proof is separate.'

FILES = {19: ('install.sh', 'README.md', 'builder.html', 'config.js'),
         20: ('install.ps1', 'README.md', 'builder.html', 'config.js'),
         21: ('install.sh', 'README.md', 'builder.html', 'config.js'),
         22: ('install.sh', 'install.ps1', 'README.md', 'builder.html', 'config.js'),
         27: ('README.md', 'builder.html', 'config.js'),
         28: ('AGENTS.md', 'DESIGN.md', 'OPTICS.md')}

def distribution_row(issue, row):
    obligation = ('Bind the delivered public script/document and generated-command source bytes to the exact reviewed target.'
                  if issue in (19, 20, 21, 22) else
                  'Bind the public documentation and its verification-owner bytes to the exact reviewed target.')
    preserved = ('native, behavior, text and rendered' if issue in (19, 20, 21, 22) else 'behavior, text and rendered')
    native_note = (' The exact installer bytes reuse their existing native parser/consumer receipts.'
                   if issue in (19, 20, 21, 22) else '')
    row.update(obligation=obligation,
               status='satisfied',
               expected='Pinned raw and Pages acquisitions return HTTP 200 with exact target SHA256 for each named owner; preserve all separately mapped ' + preserved + ' obligations.',
               observed='Primary public-document-distribution.json records HTTP 200 and expected=observed SHA256 at both origins for ' + ', '.join(FILES[issue]) + '. E independently compared those expected hashes with immutable Git bytes.' + native_note + ' Byte identity settles distribution only; remaining cells retain their own gaps.',
               evidence_basis='Fresh primary public acquisition, independently rebound by E to exact Git source; no repeated HTTP or new native execution by E.',
               evidenceReceipt=receipt('public-document-distribution.json'))

for issue, row_id in ((19, '19-12'), (20, '20-12'), (21, '21-17'), (22, '22-14')):
    distribution_row(issue, next(r for r in assessments[issue]['requirementMatrix'] if r['id'] == row_id))
    assessments[issue]['matrixReconciliationNote'] = 'The former combined distribution row is narrowed to the demonstrated public-byte leg. Its native, behavior, documentation and closure legs remain in the other original matrix rows and the publication hold; none is waived.'

for issue, existing_id, new_id in ((27, '27-12', '27-14'), (28, '28-09', '28-11')):
    a = assessments[issue]
    row = next(r for r in a['requirementMatrix'] if r['id'] == existing_id)
    row['observed'] = ('Primary exact raw/Pages hashes now prove current public document bytes. E has no browser/rendered readback. '
                       'The missing required final text and rendered legibility/agreement remain separate, unsatisfied completion legs.')
    row['evidenceReceipt'] = receipt('public-document-distribution.json')
    if not any(r['id'] == new_id for r in a['requirementMatrix']):
        added = copy.deepcopy(row)
        added['id'] = new_id
        distribution_row(issue, added)
        added['authored_owner_and_delivered_consumer'] = [link(name) for name in FILES[issue]]
        added['discriminator'] = []
        a['requirementMatrix'].append(added)
    else:
        distribution_row(issue, next(r for r in a['requirementMatrix'] if r['id'] == new_id))
    a['matrixReconciliationNote'] = 'An existing composite public/rendered obligation is split into two rows to credit byte distribution while retaining missing text/rendered proof. This introduces no new requirement.'

CONTROL_NAMES_27 = [
    'source: exact M5V2T6 search recipients',
    'source: London has no Canadian request or digit bias',
    'source: trimmed short query sends nothing',
    'source: digit bias and prefix are actual triggers',
    'source caller: builder debounce and Enter',
    'source caller: builder reverse coordinates and disabled controls',
    'source: coarse URLs and fallback',
    'source: Reset key scope preserves unrelated caches',
]
CONTROL_NAMES_28 = [
    'source: complete fragment motion recipe and query negative',
    'source: six real force branches and unsupported-string mutant',
    'docs: AGENTS.md no positive query-only diagnostic recipe',
    'recipe: AGENTS.md:156: &debugMotion=1',
    'recipe: AGENTS.md:157: &motion=full',
    'recipe: AGENTS.md:160: &debugLayers=1',
    'recipe: AGENTS.md:160: &debugMoon=1',
    'recipe: AGENTS.md:160: &debugMotion=1',
    'docs: DESIGN.md no positive query-only diagnostic recipe',
    'docs: OPTICS.md no positive query-only diagnostic recipe',
    'docs: DESIGN enum matches executed force branches',
]
assert all(named_checks[name]['status'] == 'PASS' for name in CONTROL_NAMES_27)
assert named_checks[CONTROL_NAMES_28[1]] == {'name': CONTROL_NAMES_28[1], 'status': 'FAIL', 'error': '_pbrFailed is not defined'}

matrix27 = {r['id']: r for r in assessments[27]['requirementMatrix']}
for row_id, note in {
    '27-01': 'Fresh primary docs control FAIL: privacy missing Nominatim; independent complete prose inspection establishes the broader missing table/Reset boundary. Corrected builder privacy/details/host control PASS.',
    '27-02': 'Fresh primary source control PASS for exact GeoJS URL and controlled ipinfo fallback.',
    '27-03': 'Fresh primary source controls PASS for exact Nominatim q, conditional countrycodes, and actual builder debounce/Enter callers.',
    '27-04': 'Fresh primary source controls PASS for M5V2T6 -> /ca/M5V, London without Canadian request, and malformed matching prefix characterization.',
    '27-05': 'Fresh primary actual builder caller PASS for reverse latitude=51.5/longitude=-0.12/localityLanguage=en, both automatic controls disabled, and missing-coordinate negative.',
    '27-09': 'Fresh primary source Reset control PASS: only the configuration key is removed and both unrelated caches remain.',
    '27-10': 'Fresh primary builder recipient/details-link/embedding-host guidance control PASS.',
}.items():
    r = matrix27[row_id]
    r['observed'] = r['observed'].replace(' No fresh caller execution was credited here.', '').replace('These are construction claims, not recorded external transmission.', 'These are intercepted construction claims, not recorded external transmission.')
    if note not in r['observed']:
        r['observed'] += ' ' + note
    r['evidenceReceipt'] = receipt('docs-contract-primary.json')
    r['evidence_basis'] = 'Exact source/prose inspection plus fresh primary controlled execution, independently hash-bound by E; no external transmission.'
matrix27['27-11'].update(status='satisfied',
    observed='Fresh primary exact-target run passes all eight #27 source/caller controls: exact M5V2T6 URLs, London without Canadian request/digit bias, short-query no request, prefix/bias characterization, actual debounce/Enter, eligible reverse coordinates plus disabled/missing-coordinate negatives, coarse fallback, and Reset key/cache scope. All final table-row callsites/fields were read and recorded above. Fetch is intercepted, no transmission; this does not satisfy the missing README text or rendered legibility.',
    evidence_basis='Fresh primary execution at exact target/fixture bytes; E read all actual assertions and result rows, and verified hash identity.',
    evidenceReceipt=receipt('docs-contract-primary.json'))

matrix28 = {r['id']: r for r in assessments[28]['requirementMatrix']}
for row_id, note in {
    '28-01': 'Fresh primary checks independently fail on AGENTS:48, DESIGN:282 and OPTICS:99; five existing & append recipes pass and remain preserved.',
    '28-02': 'Fresh primary DESIGN enum comparison FAIL records exactly the omitted lunarhalo. Its force-execution control separately fails with _pbrFailed is not defined, so no fresh force execution PASS is claimed.',
}.items():
    if note not in matrix28[row_id]['observed']:
        matrix28[row_id]['observed'] += ' ' + note
matrix28['28-05']['observed'] = 'Fresh primary production-q/flag control PASS proves complete fragment DEBUGMOTION/MOTIONFULL activation and before-# negative failure. Five existing AGENTS & append literals also PASS. The six-force/unsupported-string execution control FAILS with _pbrFailed is not defined because the extracted eligibility region lacks that binding; this is incomplete fixture evidence, not a demonstrated runtime defect. Source inspection still identifies all six real branches and incorrect final document literals/enum. Missing corrected literal-by-literal and completed enum-negative execution proof remains unverified.'
for row_id in ('28-01', '28-02', '28-05'):
    matrix28[row_id]['evidenceReceipt'] = receipt('docs-contract-primary.json')
    matrix28[row_id]['evidence_basis'] = 'Exact source/prose inspection plus fresh primary issue-relevant controlled execution; missing fixture binding is preserved as a failed attempt, not product proof.'

GAPS = {
 19: ['Actual Apple /bin/bash 3.2/macOS detector and pipe/PTY entry proof is missing.',
      'The complete profile cardinality/backslash matrix and retained newline-path limitation are not fully demonstrated/disclosed.',
      'README lacks required terminal and same-attempt versus retired cross-run cache instructions.',
      'Current adversarial builder/config roundtrip remains unverified.'],
 20: ['README omits explicit Windows PowerShell 5.1/pwsh and the Windows reviewed download/-File route required by the capability contract.'],
 21: ['Actual macOS/Apple Bash 3.2 BSD-stat/mktemp/filesystem controls are missing.',
      'An isolated non-writable foreign-UID retained-parent initializer control is missing.',
      'README lacks retained bundle and cache lifetime instructions.'],
 22: ['Actual Apple Bash 3.2/macOS whole-entry matrix and native launch/staging prerequisites are missing.',
      'README lacks the offline no-effect/no-artifact/no-prompt policy and NoOpen distinction.'],
 27: ['README lacks the recipient/field table for all eight request groups, the local-versus-external introduction and Reset/cache/provider boundary, while unsupported no-tracking/server-retention wording remains.',
      'Rendered README/builder privacy text legibility and agreement remain unverified; source trigger/negative controls and public byte distribution are now demonstrated.'],
 28: ['AGENTS/DESIGN/OPTICS retain ignored positive query-only diagnostic recipes.',
      'DESIGN omits lunarhalo and overclaims forceability; the complete copyable examples, six-name/physical-input explanation and activation-versus-pixel statement are missing.',
      'Corrected literal-by-literal controls, complete enum/unsupported-string proof, actual browser debug/full-override readback and rendered corrected documents remain outstanding. The attempted force oracle fails with _pbrFailed is not defined; no product defect is inferred.'],
}
for n in ISSUES:
    a = assessments[n]
    update_authority(a['authority'], n)
    a['reconciledEvidenceAtUtc'] = NOW
    a['gaps'] = GAPS[n]
    a['proposedNextIncrement']['gaps'] = GAPS[n]
    a['publicationStatus'] = STATUS
    a['primaryReconciliation'] = 'Primary accepted the six LEAVE OPEN recommendations in principle; revised comments still require final individual reconciliation and delivered browser-baseline confirmation before any publication.'
    a['documentDistributionEvidence'] = {**receipt('public-document-distribution.json'),
        'checks': [r for r in distribution if r['file'] in FILES[n]],
        'scope': public_record['scope'], 'limit': public_record['limit']}
    a['residualLimits'] = [('No product/native/browser execution by E; exact source and independently rebound receipts only.'
                            if n in (19, 20, 21, 22) else 'No source-control or browser execution by E; fresh primary controls are explicitly attributed.'),
                          'Current raw/Pages byte equality is demonstrated. Rendered legibility and actual browser consumer behavior require their own evidence.']
    if n in (19, 21, 22):
        a['residualLimits'].append('Missing actual Apple proof is an unverified platform cell, not a demonstrated platform defect.')
    if n in (27, 28):
        a['evidenceSource'] = 'primaryFreshControls, documentDistributionEvidence and immutable target source/document/assertion links; necessary primary receipt results are inline in the proposed comment.'
        a['reuseBasis'] = 'Fresh primary source/document execution and public acquisitions are independently bound to exact Git bytes by E. Historical differing documentation PASS labels are not reused as corrected final text or browser evidence.'
        a['historicalCommands'] = []
        first = a['executedCommands'][0]
        first['command'] = 'git show <AUDIT_SHA>:<assigned source/doc/fixture>; git rev-parse <AUDIT_SHA>:<assigned path>; git status --short; Get-Content supplied primary receipts; Get-FileHash SHA256'
        first['expected'] = 'Exact immutable source/consumer/contract bytes and complete primary receipt contents; no source/control execution by E.'
        first['observed'] = 'Clean examined checkout at reviewed head 4bccdf43; target tree 35208181 matches delivered merge; assigned issue body hashes, public source/document hashes and fresh primary fixture hashes match exact target objects.'
        names = CONTROL_NAMES_27 + ['docs: README privacy names actual recipients and trigger fields', 'docs: builder privacy recipients, details link and host guidance'] if n == 27 else CONTROL_NAMES_28
        a['primaryFreshControls'] = {**source_record, 'issueRelevantChecks': [named_checks[name] for name in names]}
        a['executedCommands'] = [r for r in a['executedCommands'] if r.get('executedBy') != 'primary']
        a['executedCommands'].append({'command': source_record['command'], 'executedBy': 'primary',
            'environment': 'Controlled Node source/doc VM using exact Git ref; fixture/source hashes bound above; browser NOT_RUN; intercepted fetch, no transmission.',
            'expected': 'Original source-trigger, recipe and negative expectations; mandatory final text must match actual source.',
            'observed': '39 total, 18 PASS, 21 FAIL, exit1. Only issueRelevantChecks are credited; optional lexical/composed failures introduce no new obligation.',
            'receipt': receipt('docs-contract-primary.json')})
    a['negativeControls'] = [copy.deepcopy(r) for r in a['requirementMatrix'] if any(word in r['obligation'].lower() for word in ('negative', 'mutant', 'disabled', 'reject', 'refus'))]

assessments[19]['proposedNextIncrement']['steps'][-1] = 'Use the supplied exact current raw/Pages distribution receipt and retained native equivalence; do not repeat unchanged-byte checks. Bind any later changed source, fixtures or documentation to affected controls, then obtain independent primary reconciliation.'
assessments[20]['proposedNextIncrement']['scope'] = 'README Windows installer instructions; preserve qualified ASCII selector/entry source, exact distributed bytes and native fixtures.'
assessments[20]['proposedNextIncrement']['steps'] = [
 'State Windows PowerShell 5.1 and supported pwsh 7 explicitly and provide a quoted reviewed/downloaded -File route. Preserve irm|iex, encoded hash grammar and the manual dashboard boundary.',
 'Consume the supplied HTTP 200/raw/Pages SHA256 receipt: current install.ps1 bytes exactly equal the source already parsed on actual 5.1/7 and exercised through direct -File consumers. No repeat acquisition or parser run is needed for unchanged bytes; rebind any future changed file before claiming its distribution.',
 'Reuse the retained 18-case native suites and 24-case direct entry through exact source/fixture identity. Check the changed README against that capability and obtain final primary reconciliation; rerun affected controls only for changed inputs.',
]
row20 = next(r for r in assessments[20]['requirementMatrix'] if r['id'] == '20-11')
row20['obligation'] = 'Keep the qualified Windows selector/parser/entry interfaces joined with the actual #22 guards.'
row20['observed'] = 'Current source and fixtures equal the reviewed objects; retained native Windows helper and direct-entry controls exercise these guards without reintroducing encoding/binding failures or masking normal positives.'
assessments[20]['proposedNextIncrement']['acceptance'] = 'README states the actual floor, Windows file route and manual boundary; distributed bytes match qualified source or receive fresh affected native gates; every #20 obligation is satisfied.'
assessments[20]['proposedNextIncrement']['dependencies'] = ['#22 Windows guards use the same qualified source; evaluate that interface through the retained matching consumer controls.']
assessments[21]['proposedNextIncrement']['steps'][-1] = 'Reuse supplied current raw/Pages byte proof, then bind only later affected changes for independent security reconciliation. Preserve time-bounded owner-exit/fresh-consumer evidence and the later absent-fixture observation without inferring its cause.'
assessments[22]['proposedNextIncrement']['steps'][-1] = 'Credit the supplied current raw/Pages script/usage byte identities. After the missing native and README legs are addressed, reconcile affected integrated effects and final changed usage before primary decides closure.'
assessments[27]['proposedNextIncrement']['steps'][2] = 'Reuse the fresh primary eight-source-control receipt through exact fixture/config/builder identity; its intercepted positive/negative controls now demonstrate the triggers. Check the final written recipient table against the recorded callsite ledger, rerunning only controls affected by provider/field/trigger/Reset changes.'
assessments[27]['proposedNextIncrement']['steps'][3] = 'After the missing README text is authorized and corrected, read the rendered README/builder for legibility and agreement. Current public byte identity is already demonstrated; bind any later changed public version before claiming its published disclosure, then reconcile the individual comment with primary.'
assessments[28]['proposedNextIncrement']['steps'][2] = 'Reuse the demonstrated production-q/flag and existing & recipe controls. Validate every final changed literal and all six real branches/unsupported-corona negative; supply the actual eligibility dependencies to the contained force fixture so its _pbrFailed binding failure cannot be mistaken for a healthy negative or a runtime defect. Preserve the original expectations.'
assessments[28]['proposedNextIncrement']['steps'][3] = 'One browser owner reads the complete real-time fragment/debug overlay and full override under reduced-motion. Any visual claim additionally needs a real watch/delta/crop. Current raw/Pages document bytes are already matched; read rendered corrected docs and bind only later changed public text before primary reconciliation.'

def md(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def source_links(values):
    return '; '.join(f'[{p["path"]}:{p["start"]}-{p["end"]}]({p["url"]})' for p in values)

def public_block(n):
    lines = ['Current public byte-distribution proof (primary execution, independently rebound by E; both acquisitions return HTTP 200):', '',
             '| Owner | Acquisitions | Expected = observed SHA256 at both origins |', '|---|---|---|']
    for name in FILES[n]:
        matching = [r for r in distribution if r['file'] == name]
        raw = next(r['url'] for r in matching if 'raw.githubusercontent.com' in r['url'])
        pages = next(r['url'] for r in matching if 'theislampill.github.io' in r['url'])
        lines.append(f'| {name} | [pinned raw]({raw}); [Pages]({pages}) | `{source_hashes[name]}` |')
    explanation = ('These are the exact reviewed bytes. Existing exact-file native evidence remains applicable to identical installer bytes. This receipt does not establish the missing prose or separately required native/consumer behavior. No duplicate HTTP/native-parser check is requested.'
                   if n in (19, 20, 21, 22) else
                   'These are the exact reviewed document/verification-owner bytes. This receipt does not establish rendered legibility, actual browser readouts or the missing prose. No duplicate byte-acquisition check is requested.')
    lines.extend(['', explanation, ''])
    return lines

def fresh_block(n):
    if n not in (27, 28):
        return []
    a = assessments[n]
    lines = ['Fresh primary source/document controls, reviewed by E:', '',
             f'Command: `{source_record["command"]}`. Exact ref/fixture hashes above; intercepted fetch, no transmission; browser `NOT_RUN`. The complete run records 39 cases, 18 PASS, 21 FAIL, exit 1. Only the following original-contract checks affect this issue:', '',
             '| Check | Recorded result |', '|---|---|']
    for r in a['primaryFreshControls']['issueRelevantChecks']:
        observed = r['status'] + (': ' + r['error'] if 'error' in r else '')
        lines.append(f'| {md(r["name"])} | {md(observed)} |')
    lines.extend(['', f'Fixture SHA256: `{source_record["fixtureSha256"]}`; original JSONL result SHA256: `{source_record["sha256"]}`. Source and document hashes equal the immutable target. Lexical token failures alone are not added obligations; missing required prose is independently demonstrated in the matrix.', ''])
    return lines

def comment(n):
    a = assessments[n]
    target = a['target']
    acquisition = ('Reviewer E acquired source, assertions and receipts read-only. E ran no product/native suite, browser, installer or external mutation. Retained native results below are historical executions on identical source/fixture bytes. Any fresh primary controls are separately attributed.'
                   if n in (19, 20, 21, 22) else
                   'Reviewer E read the exact source, assertions and primary receipts. Fresh source controls below were executed by primary and independently hash-bound by E. E ran no source-control suite, browser or external mutation.')
    lines = [f'# RLGWO closure audit — {a["canonicalId"]} — REMAINS OPEN', '',
             '**Recommendation: LEAVE OPEN.** ' + ' '.join(a['gaps']), '',
             f'Audit date: 2026-10-08 (local). Repository: `theislampill/salah_widget`. Delivered target `{SHA}`, tree `{TREE}`; runtime SHA256 `{target["runtimeSha256"]}`, root index SHA256 `{target["indexSha256"]}`. Contract `{a["canonicalId"]}` / #{n}: original body SHA256 `{a["originalBodySha256"]}`, revision `{a["originalBodyRevision"]}`; complete body, comments and captured events examined.', '',
             acquisition + ' The local client turn_context confirms `gpt-6.1-sol/max`; this is not independent hardware/backend attestation.', '',
             'The primary accepted the LEAVE OPEN recommendation in principle. This revised comment remains proposed and unpublished pending final individual reconciliation and delivered browser-baseline confirmation.', '']
    lines += public_block(n)
    lines += ['The matrix preserves each binding obligation. “Unverified” means missing proof; “unmet” identifies a demonstrated gap. Public-byte proof and rendered/behavior/platform proof remain separate.', '',
              '| Obligation | Authored owner / delivered consumer | Discriminator; expected → observed | Status |', '|---|---|---|---|']
    for r in a['requirementMatrix']:
        tests = source_links(r['discriminator']) or 'Exact source/receipt readback with execution attribution above/below'
        observed = tests + '; EXPECTED: ' + r['expected'] + ' OBSERVED: ' + r['observed']
        lines.append('| ' + ' | '.join((md(r['id'] + ': ' + r['obligation']), source_links(r['authored_owner_and_delivered_consumer']), md(observed), r['status'].upper())) + ' |')
    lines.append('')
    if n in (19, 20, 21, 22):
        match = re.search(r'Retained(?: native)? receipt core.*?```json\n(.*?)\n```', old_comments[n], re.S)
        assert match, f'Original per-issue native receipt core missing: {n}'
        core = json.loads(match.group(1))
        if n in (19, 21):
            core['source'].pop('install_ps1', None)
        if n == 20:
            core['source'].pop('install_sh', None)
            core['limits'] = [s for s in core['limits'] if 'Apple' not in s]
        lines.extend(['Retained native receipt core (historical; exact-source reuse only):', '', '```json', json.dumps(core, indent=2), '```', ''])
        for c in a['historicalCommands']:
            lines.append(f'Recorded retained command: `{c["command"]}`. Environment: {c["environment"]}. Expected: {c["expected"]}. Observed: {c["observed"]}. E did not repeat it.')
        lines.append('')
    lines += fresh_block(n)
    proposed = a['proposedNextIncrement']
    lines.extend(['**Next RLGWO increment required for closure**', '', 'Semantic owner/scope: ' + proposed['scope'], '',
                  'Preserve completed source/consumer work and the original positive/negative expectations. This proposal is not authorization for production edits or publication.', ''])
    for i, step in enumerate(proposed['steps'], 1):
        lines.append(f'{i}. {step}')
    lines.extend(['', 'Acceptance and closure proof: ' + proposed['acceptance'], '',
                  'Dependencies/interfaces: ' + ' '.join(proposed['dependencies']), ''])
    if n in (19, 21, 22):
        lines.append('No new owner policy is required. The named Apple cells require an actual authorized macOS host; alternate shells/hosts remain insufficient. Preserve original retained evidence and source guards while that proof is unavailable.')
    elif n == 20:
        lines.append('No new host or asset-selection policy is required. Preserve the qualified Windows encoding, native parser/selector/direct-entry evidence and manual installation boundary while correcting the precise README usage gap.')
    else:
        lines.append('No new runtime, provider, consent, permission or retention policy is required. Correct only the named documentation after authorization; runtime remains a verification owner.')
    lines.extend(['', 'Containment/rollback: keep these proposed artifacts local and reversible. Preserve accepted source and immutable failed/retained receipts; revert only inaccurate documentation or fixture changes if a later authorized validation fails.', '',
                  'Primary Astra owns final independent reconciliation and any approved publication/closure. This issue-specific recommendation does not establish those external actions.', '',
                  f'<!-- RLGWO-AUDIT:{SHA}:{a["canonicalId"]}:2026-10-08 -->', ''])
    return '\n'.join(lines)

for n in ISSUES:
    write_json(f'{n}-assessment.json', assessments[n])
    (ROOT / f'{n}-comment.md').write_text(comment(n), encoding='utf-8')

summary['capturedAtUtc'] = NOW
summary['results'] = [{
    'issue': n, 'canonicalId': assessments[n]['canonicalId'], 'verdict': 'LEAVE OPEN',
    'assessment': f'{n}-assessment.json', 'comment': f'{n}-comment.md', 'gaps': GAPS[n],
    'mandatoryRows': len(assessments[n]['requirementMatrix']),
    'statusCounts': {status: sum(r['status'] == status for r in assessments[n]['requirementMatrix'])
                     for status in ('satisfied', 'validly superseded', 'unmet', 'unverified')}
} for n in ISSUES]
summary['exactMissingChecksRequested'] = [r for r in summary['exactMissingChecksRequested'] if r['scope'] not in ('Publiccapability', '#27/#28 exactsource/docsliterals')]
summary['exactMissingChecksRequested'].extend([
    {'scope': '#27 corrected text/rendered legibility',
     'command': 'Compare authorized corrected README table/Reset introduction to final callsite ledger; read rendered README/builder. Reuse fresh source control receipt unless provider/field/trigger/Reset bytes change.',
     'purpose': 'All eight source-trigger controls now pass. Current public bytes match; only missing mandatory prose and rendered legibility/agreement remain.'},
    {'scope': '#28 corrected literals/enum-negative fixture',
     'command': 'Validate actual final changed AGENTS/DESIGN/OPTICS literals; complete the contained force/unsupported-string oracle with actual eligibility dependencies. Reuse healthy production q and & controls; preserve the original expectations.',
     'purpose': 'Fresh production-q control passed. Force fixture records _pbrFailed is not defined, so unsupported-string proof is incomplete; required text/enum remain incorrect.'},
    {'scope': '#28 actual browser/readout and corrected rendered text',
     'command': 'One primary browser owner reads complete real-time fragment/debugMotion and motion=full under reduced-motion, then rendered corrected AGENTS/DESIGN/OPTICS; bind only later changed public text.',
     'purpose': 'Source parsing and public hash equality do not prove actual browser readouts or rendered documentation. No repeat current 16 HTTP/hash or identical native ParseFile check is requested.'}
])
summary['freshPrimaryEvidence'] = {'publicDistribution': public_record, 'sourceControls': source_record,
                                   'modelConfiguration': model_record}
summary['matrixReconciliationNote'] = '80 rows now express the same original obligations: two composite public/rendered rows were split to credit byte identity without waiving rendered proof. No added contract requirement.'
counterexample = {'issue': 28, 'source': 'docs-contract-primary.json:10',
    'observed': 'Attempted six-force/unsupported-string control FAIL: _pbrFailed is not defined. Fixture evidence is incomplete; no runtime defect or force-execution PASS is inferred.'}
if counterexample not in summary['materialCounterexamples']:
    summary['materialCounterexamples'].append(counterexample)
summary['crossIssueDependencies'] = {str(n): assessments[n]['proposedNextIncrement']['dependencies'] for n in ISSUES}
summary['publicationStatus'] = STATUS
summary['primaryReconciliation'] = 'Six LEAVE OPEN recommendations accepted in principle; updated comments await final individual reconciliation/browser-baseline confirmation and remain unpublished.'
write_json('summary.json', summary)
write_json('native-rebind.json', native)

# Verify serialized artifacts, public evidence custody and original native proof without rerunning product tests.
for n in ISSUES:
    a = read_json(ROOT / f'{n}-assessment.json')
    c = (ROOT / f'{n}-comment.md').read_text(encoding='utf-8')
    original = read_json(AUDIT / 'issues' / f'{n}.json')
    assert hashlib.sha256(original['issue']['body'].encode()).hexdigest() == a['originalBodySha256']
    assert a['verdict'] == 'LEAVE OPEN' and a['publicationStatus'] == STATUS
    assert a['target']['commit'] == SHA and a['target']['tree'] == TREE
    assert len({r['id'] for r in a['requirementMatrix']}) == len(a['requirementMatrix'])
    assert all(r['status'] in ('satisfied', 'validly superseded', 'unmet', 'unverified') for r in a['requirementMatrix'])
    assert c.count(f'<!-- RLGWO-AUDIT:{SHA}:{a["canonicalId"]}:2026-10-08 -->') == 1
    assert all(r['id'] + ': ' in c for r in a['requirementMatrix'])
    assert 'Next RLGWO increment required for closure' in c
    assert len(c) <= 65536
    assert 'client turn_context confirms `gpt-6.1-sol/max`' in c
    assert 'current raw-script/usage readback remain unverified' not in c
    if n in (27, 28):
        assert not any(s in c for s in ('macOS', 'Apple', 'Bash 3.2', 'N001', 'N002', 'N003', 'all-widget'))
assert all(digest(pathlib.Path(r['path'])) == r['sha256'] for r in native['retainedReceipts'])
for obj in native['sourceObjects']:
    assert hashlib.sha256(git('show', f'{SHA}:{obj["path"]}')).hexdigest() == obj['sha256']
    if 'reviewed_native_blob' in obj:
        assert git('rev-parse', f'{SHA}:{obj["path"]}').decode().strip() == obj['reviewed_native_blob']
direct = read_json(pathlib.Path(next(r['path'] for r in native['retainedReceipts'] if r['name'] == 'direct-native-final.json')))
assert len(direct['results']) == 24 and all(r['pass_'] for r in direct['results'])
peer = read_json(pathlib.Path(next(r['path'] for r in native['retainedReceipts'] if r['name'] == 'crossuid-nonlogin/result.json')))['peer']['result']
operations = peer['boundaries'] + peer['fileProbes'] + peer['positives']
assert len(operations) == 49 and all(r['pass'] for r in operations)
assert sum(r['outcome'] == 'denied' and r['errno'] == 13 for r in operations) == 30
assert sum(r['outcome'] == 'allowed' for r in operations) == 19
assert git('status', '--short').decode().strip() == ''
validation = {'scope': 'Local artifact/source/receipt consistency checks only; E did not run product/native/browser tests.',
              'validatedAtUtc': NOW, 'assignedIssues': list(ISSUES), 'issueArtifactsParse': True,
              'stableMarkersMatch': True, 'mandatoryRows': sum(r['mandatoryRows'] for r in summary['results']),
              'matrixCounts': {r['issue']: r['statusCounts'] for r in summary['results']},
              'originalBodyHashesMatch': True, 'nativeObjectEquivalence': True, 'retainedReceiptHashesMatch': True,
              'publicDistributionRows': 16, 'publicDistributionAllHttp200ExactGitSha256': True,
              'freshPrimarySourceCases': run_summary['summary'], 'modelConfigClientRecorded': 'gpt-6.1-sol/max',
              'modelHardwareBackendIndependentlyAttested': False,
              'retainedWindowsRows': 24, 'retainedLinuxDAC': {'total': 49, 'denied13': 30, 'allowed': 19},
              'sourceMutation': 'NONE', 'publication': 'NONE'}
assert validation['mandatoryRows'] == 80
write_json('artifact-validation.json', validation)
print(json.dumps(validation, ensure_ascii=False))
