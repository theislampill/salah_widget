"""Reconcile supplied primary receipts; no browser/network/source/public mutation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
AUDIT = HERE.parents[1]
ROOT = Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
SHA = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


release = read(AUDIT / 'release.json')
browser = read(AUDIT / 'public-browser-summary.json')
distribution = read(AUDIT / 'public-document-distribution.json')
models = read(AUDIT / 'reviewer-model-settings.json')
assert release['status'] == 'DELIVERED_VERIFIED'
assert release['AUDIT_SHA'] == browser['AUDIT_SHA'] == release['mergeCommit'] == release['main'] == SHA
assert release['tree'] == '35208181eea714c17f5e77b2644e76434345db60'
assert release['runtime'] == 'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
assert release['pagesBuild']['commit'] == SHA and release['pagesBuild']['status'] == 'built'
assert len(browser['cases']) == release['publicBrowserCases'] == 16
assert all(case['status'] == 'PASS' and all(case['checks'].values()) for case in browser['cases'])
assert len(distribution) == 16 and all(row['status'] == 200 and row['match'] and row['expected'] == row['observed'] == digest(ROOT / row['file']) for row in distribution)
d = [item for item in models['sessions'] if item['session']['agent_path'] == '/root/rlgwo_d']
assert len(d) == 1
d = d[0]
actual_turns = []
with Path(d['sessionFile']).open(encoding='utf-8') as stream:
    for line in stream:
        event = json.loads(line)
        if event.get('type') == 'turn_context':
            payload = event['payload']
            if payload.get('turn_id') in {turn['turn_id'] for turn in d['turnConfigurations']}:
                item = {'turn_id': payload['turn_id'], 'model': payload['model'], 'effort': payload['effort'], 'collaboration_mode': payload.get('collaboration_mode')}
                if item not in actual_turns:
                    actual_turns.append(item)
assert actual_turns and actual_turns == d['turnConfigurations']
assert all(turn['model'] == 'gpt-6.1-sol' and turn['effort'] == 'max' and turn['collaboration_mode']['settings']['model'] == 'gpt-6.1-sol' and turn['collaboration_mode']['settings']['reasoning_effort'] == 'max' for turn in actual_turns)
validation = {'status': 'PASS_RECEIPT_AND_LOCAL_SOURCE_BINDING', 'target': SHA,
    'scope': 'D inspected supplied primary release/public receipts and verified internal consistency plus local target document hashes; did not repeat primary public browser/readback or claim independent backend hardware attestation.',
    'primaryArtifacts': {name: digest(AUDIT / name) for name in ['release.json', 'public-browser-summary.json', 'public-document-distribution.json', 'reviewer-model-settings.json']},
    'releaseStatus': release['status'], 'verifiedAt': release['verifiedAt'], 'pagesBuild': release['pagesBuild']['url'],
    'publicSmokeCases': len(browser['cases']), 'publicSmokeAllPass': True, 'publicDistribution': distribution,
    'reviewerSession': d['session'], 'recordedClientConfigurations': actual_turns,
    'limitations': browser['limits']}
(HERE / 'readbacks-validation.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')

script = HERE / 'write-assessments.py'
text = script.read_text(encoding='utf-8')


def replace(old, new):
    global text
    assert text.count(old) == 1, (old[:70], text.count(old))
    text = text.replace(old, new)


replace("    'effective': {'model': None, 'reasoningEffort': None, 'confirmation': 'UNVERIFIED_NOT_EXPOSED'},\n    'evidence': 'Worker tool/context surface does not expose effective backend model or reasoning effort. Requested route is not used as effective confirmation; primary may supply authoritative dispatch metadata.',",
"    'effective': {'model': 'gpt-6.1-sol', 'reasoningEffort': 'max', 'confirmation': 'CONFIRMED_RECORDED_CLIENT_CONFIGURATION'},\n    'evidence': 'Primary reviewer-model-settings.json and D independently inspected own session turn_context 01a11e26-77d9-7bc0-b18d-f4fb2ac3b10a: model gpt-6.1-sol, effort max and collaboration settings match. Supported spawn plus local client recording is confirmation; no independent hardware/backend attestation claimed.',\n    'sessionId': '01a11e26-76ef-7583-b53a-d9c4abeec9f0',\n    'verificationReceipt': 'readbacks-validation.json',")
replace(" 'publicBaseline':'Primary owns delivered public rollout smoke/readback; no assigned native/public interaction claim is inferred from its status.',",
" 'publicBaseline':{'status':'DELIVERED_VERIFIED','primaryReleaseReceipt':'release.json','inspectedByD':'readbacks-validation.json',\n    'verifiedAt':'" + release['verifiedAt'] + "','pagesBuild':1270547036,'publicRuntimeAndV1Files':139,'publicSmokeCases':16,'publicSmokeAllPass':True,\n    'rawAndPagesDocumentScriptMatches':16,'scope':'Primary provided current merge/runtime/V1/public smoke and public raw/Pages document/script readbacks; D verified receipt identities and local corresponding source hashes. Controlled race/storage/copy/native-stream negatives are separate.'},")
replace('Public delivery readback is separately owned by primary.', 'Primary delivery is DELIVERED_VERIFIED; Pages build1270547036 is bound to the exact merge and all16 public browser smoke cases passed. This does not replace the controlled consumer negatives below.')
replace("      'The implemented source work is preserved.", "      'Requested reviewer: gpt-6.1-sol/max. D recorded client configuration independently verified from its session turn_context: gpt-6.1-sol, effort max, matching collaboration settings. This is supported client configuration confirmation, not independent hardware/backend attestation.', '',\n      'The implemented source work is preserved.")
replace("    lines += ['', '**Fresh execution and controls**', '',", "    public_rows=json.loads((AUDIT/'public-document-distribution.json').read_text(encoding='utf-8-sig'))\n    lines += ['', '**Verified public delivery baseline**', '',\n      'Primary release receipt is DELIVERED_VERIFIED at `" + release['verifiedAt'] + "`; exact [Pages build1270547036](https://api.github.com/repos/theislampill/salah_widget/pages/builds/1270547036) is built for this merge. All139 runtime+V1 public files matched; all16 Chromium/Firefox direct/iframe cold/warm root/V1 smoke cases passed. D inspected these supplied primary receipts and their limits; D did not rerun public browsers. Current normal smoke confirms the card/prayer/date/settings consumers, while the race, denied storage, copy and native-body controls remain scoped separately.', '',\n      'The primary raw-at-merge and Pages readbacks below each returned HTTP200 and the same expected/observed SHA-256. D recomputed corresponding exact-target local source hashes. These confirm distribution of the documented content, including the specific documentation defects identified above.', '',\n      '| Public file | Expected = raw = Pages SHA-256 | Raw / Pages readback |',\n      '|---|---|---|']\n    for file in sorted({r['file'] for r in public_rows}):\n        pair=[r for r in public_rows if r['file']==file]\n        raw=next(r for r in pair if 'raw.githubusercontent.com' in r['url'])\n        pages=next(r for r in pair if 'github.io' in r['url'])\n        lines.append(f\"| `{file}` | `{raw['expected']}` | [raw]({raw['url']}) / [Pages]({pages['url']}) HTTP200, match |\")\n    lines += ['', '**Fresh execution and controls**', '',")
replace("      'Deployment/publication: primary owns the merged public-byte rollout/readback and any GitHub action. Issue reviewer D has inspected and proposed this disposition;", "      'Deployment/publication: primary release/public source/document/browser readbacks are verified and inspected as recorded above; primary owns any GitHub action. Issue reviewer D has inspected and proposed this disposition;")
replace("'unverified','actual browser-origin consumer/public claim'),", "'unverified','actual browser-origin selected-preference consumer; public baseline verified'),")
replace('Public rollout baseline belongs to primary.', 'Primary public rollout baseline and served builder/config/index/doc identity are verified; this controlled selected-preference browser-origin display is still distinct and unverified.')
replace('Source canonical output; T-18 current bytes; public baseline held by primary.', 'Source canonical output; T-18 current bytes; verified primary public distribution/rollout baseline.')
replace('Actual browser/public recovery proof remains missing above.', 'Public source distribution is verified; actual native recovery proof remains missing above.')
replace('No ready checked-in race browser driver was found; a bounded driver must be supplied/authored or an existing retained receipt located.', 'An isolated exact-six-anchor fixture and eleven-case caller driver are now prepared under workers/D for primary-exclusive execution; native results and visual review are not predeclared.')
replace("'not all first implemented by PR42", "'not all first implemented by PR42") if False else None
text = text.replace('primary challenge/publication pending; recommendation remains open for native bridge only.', 'primary challenge/publication pending; verified public distribution does not waive the native bridge; recommendation remains open for that bridge only.')
text = text.replace('no executed receipt.', 'prepared isolated six-anchor primary driver, no executed native receipt yet.')
text = text.replace('Prepared wrapper requires2 scripts; delivered root has6 and exact guard would throw Page script anchors changed before loading. This is evidence-fixture defect, not production metadata loss; browser itself was not run.', 'Checked-in wrapper requires2 scripts; delivered root has6 and its exact guard would throw Page script anchors changed. Isolated stronger hash/anchor/body-preserving adaptation is now prepared with current modules retained, plus serial caller/stream driver. No native execution by D; fixture defect is separate from production metadata.')
text = text.replace("'unmet','mandatory evidence fixture applicability and native proof'),", "'unverified','isolated applicable native fixture prepared; actual native proof pending'),")
script.write_text(text, encoding='utf-8')
print(json.dumps({'status': validation['status'], 'publicCases': 16, 'documentReadbacks': 16, 'clientConfigConfirmed': 'gpt-6.1-sol/max', 'generatorUpdated': True}))
