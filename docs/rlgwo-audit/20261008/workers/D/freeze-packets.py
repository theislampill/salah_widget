"""Freeze reconciled publication packets. Structural serialization only, no tests."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
PUBLIC = 'https://github.com/theislampill/salah_widget/blob/AUDIT_EVIDENCE_COMMIT/docs/rlgwo-audit/20261008/'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


frozen = []
for number in [15, 16, 17, 18, 31, 35]:
    ap, cp = HERE / f'{number}-assessment.json', HERE / f'{number}-comment.md'
    data = read(ap)
    text = cp.read_text(encoding='utf-8')
    for row in data['requirementMatrix']:
        if number == 15 and row['id'] == 'R000F-O21':
            row['observed'] = 'Existing Enter/Shift+Enter description stays compatible; completed source/control/native/public evidence is preserved. Primary Astra reviewed all21 rows and exact native receipts/crops and accepted the closure conclusion; no production/source changes were made by D.'
        if number == 31 and row['id'] == 'R001F-O11':
            row['discriminator'] = 'Public T-31-STREAM helper reused by the isolated read-only audit server; six fresh primary native consumer cases with actual fetch/Response/AbortController and exact hash/anchor/body guards.'
        if number == 31 and row['id'] == 'R001F-O15':
            row['discriminator'] = 'D independent exact-target source/positive/mutation/native receipt inspection; verified public distribution and primary independent row/native/crop reconciliation.'
            row['observed'] = 'Fresh logic, behavioral mutations, six actual native body/caller controls and public distribution are verified. Primary Astra reviewed all16 rows, exact native receipts and recovery crops and accepted closure; no external human approval or unrun CI is claimed.'
        if number == 31 and row['id'] == 'R001F-O16':
            row['observed'] = 'No regression demonstrated by preserved source/logic controls and six current native cases. The evidence-only stream/caller increment is complete; timer/race/fallback containment remains coherent. No production mutation was authorized or made in this audit.'
        if number == 35 and 'Small real-browser integration proof' in row['obligation']:
            row['scope'] = 'native current form positive credited; full metadata/builder/iframe matrix remains unverified'
    if number == 35:
        data['gaps'][1] = 'The exact-six-script fixture applicability gap is repaired and qualified by current native widget cases, including form→apply→save→reopen25m/T. Remaining complete metadata saved/load/builder and iframe-policy proof is unverified; no native negative lifecycle/permission matrix is claimed.'
        data['boundedNextIncrement']['steps'][1] = 'Reuse the now-qualified exact-six-script isolated fixture/driver and publish its source/receipts; repair the old checked-in two-script fixture only in the later authorized evidence increment. Preserve all current modules/assets and original expectations.'
        data['boundedNextIncrement']['missingCheckRequest'] = 'After the concise mandatory documentation correction, use the qualified six-script native fixture for the remaining saved/load/builder metadata and iframe-policy bridge; current form/GPS25m/T and intent/reset cases are already credited and must not be replayed without reason.'
        text = text.replace('Checked-in R0023 native widget wrapper is inapplicable to six-script delivered root; minimum actual-form browser proof and iframe policy matrix are unverified.', data['gaps'][1])
        text = text.replace('Repair only the evidence wrapper/driver to retain all six final production scripts/assets and exact script bodies; bind source/config/runtime hashes and isolation hooks. Do not disable current runtime modules to manufacture a simpler source.', data['boundedNextIncrement']['steps'][1])
        text = text.replace('The exact-six-script isolated fixture and current form positive now exist; the remaining metadata lifecycle/builder and iframe-policy matrix needs its bounded next increment. Existing tests/r0023-native.html?page=widget requires2 scripts and cannot load this six-script root; builder count guard alone is not a successful native execution.', data['boundedNextIncrement']['missingCheckRequest'])
    for ev in data['evidenceSources']:
        if ev['id'] == 'T-31-STREAM':
            ev['purpose'] = 'Exact public finite/stalled native stream helper reused in six fresh primary browser caller cases'
    # Keep the public matrix identical to the JSON matrix for all six outcomes.
    start = text.index('| ID / original obligation |')
    end = text.index('\n**Verified public delivery baseline**', start)
    lines = ['| ID / original obligation | Authored owner → delivered consumer | Discriminator / expected → observed | Disposition |', '|---|---|---|---|']
    for row in data['requirementMatrix']:
        owner = ' '.join(f'[{key}][{key}]' for key in row['authoredOwnerRefs'])
        consumer = ' '.join(f'[{key}][{key}]' for key in row['deliveredConsumerRefs'])
        clean = lambda value: value.replace('|', '\\|').replace('\n', ' ')
        details = f"{row['discriminator']} Expected: {row['expected']} Observed: {row['observed']}"
        lines.append(f"| {row['id']}: {clean(row['obligation'])} | {owner} → {consumer} | {clean(details)} | **{row['status']}** ({row['scope']}) |")
    text = text[:start] + '\n'.join(lines) + '\n' + text[end:]
    text = text.replace('Prepared finite/stalled local native stream; not executed in this audit', 'Exact public finite/stalled stream helper reused in six fresh primary native caller cases')
    text = text.replace('Primary Astra owns final independent row reconciliation and publication.', 'Primary Astra reconciled the disposition using the exact source/consumer matrix, current native receipts and inspected crops; publication follows immutable evidence binding.')
    data['primaryReconciliation'] = {'status': 'ACCEPTED_BY_PRIMARY', 'basis': 'Primary explicitly reviewed and accepted all51 closure rows for15/18/31 plus exact native receipts/crops;16/17/35 retained open for conclusively verified specific documentation/remaining consumer gaps.', 'externalHumanApprovalClaimed': False}
    data['publicationStatus'] = 'FROZEN_PRIMARY_RECONCILED_AWAITING_IMMUTABLE_EVIDENCE_BINDING_AND_HASH_APPROVAL'
    # Public artifact URLs stay explicit placeholders until primary verifies them.
    data['publicEvidenceURLState'] = 'AUDIT_EVIDENCE_COMMIT_PLACEHOLDER_MUST_BE_REPLACED_BEFORE_PUBLICATION'
    write(ap, data)
    cp.write_text(text, encoding='utf-8')
    frozen.append({'issue': number, 'verdict': data['recommendation'], 'obligations': len(data['requirementMatrix']), 'assessmentSha256': hashlib.sha256(ap.read_bytes()).hexdigest(), 'commentSha256': hashlib.sha256(cp.read_bytes()).hexdigest(), 'commentBytes': len(cp.read_bytes())})

adaptation_path = HERE / 'native-fixture-adaptation.json'
adaptation = read(adaptation_path)
old = HERE / 'native-fixture-adaptation.pre-primary.json'
if not old.exists():
    old.write_bytes(adaptation_path.read_bytes())
adaptation['status'] = 'QUALIFIED_BY_PRIMARY_CURRENT_NATIVE_CASES'
adaptation['freshQualification'] = {'cases': 17, 'passed': 17, 'browser': 'Windows Chromium148.0.7778.96', 'receipt': 'native-reconciliation.json', 'executor': 'Primary; D no browser', 'originalFixtureSha256AndExpectedPagesUnchanged': True}
write(adaptation_path, adaptation)

summary = read(HERE / 'summary.json')
for item in summary['results']:
    item['gaps'] = read(HERE / f"{item['issueNumber']}-assessment.json")['gaps']
summary['primaryReconciliation'] = {'status': 'ACCEPTED_BY_PRIMARY', 'closureRowsReviewed': 51, 'closedRecommendations': [15, 18, 31], 'openRecommendations': [16, 17, 35]}
summary['publicationStatus'] = 'FROZEN_PRIMARY_RECONCILED_AWAITING_IMMUTABLE_EVIDENCE_BINDING_AND_HASH_APPROVAL'
summary['frozenOutputs'] = frozen
summary['nextAction'] = 'Primary substitutes verified immutable evidence commit in raw/crop links, approves resulting comment hashes, then performs authorized publication/readback. No more browser/testing/source work by D.'
write(HERE / 'summary.json', summary)
write(HERE / 'frozen-output-manifest.json', {'status': 'FROZEN_PRIMARY_RECONCILED', 'outputs': frozen, 'evidenceURLs': PUBLIC, 'sourceChanges': False, 'additionalTests': False})
print(json.dumps({'status': 'FROZEN_PRIMARY_RECONCILED', 'outputs': frozen}))
