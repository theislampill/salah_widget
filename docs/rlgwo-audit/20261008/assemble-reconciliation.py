"""Assemble the primary's issue-specific decisions, preserving worker attribution."""
from pathlib import Path
import datetime, hashlib, json

R = Path(__file__).resolve().parent
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
expected_close = {1,5,9,10,14,15,18,26,29,30,31}
inventory = json.loads((R/'initial-inventory.json').read_text(encoding='utf-8'))
rows = []
for worker, numbers in inventory['partition'].items():
    for n in numbers:
        path = R/f'workers/{worker}/{n:02d}-assessment.json'
        a = json.loads(path.read_text(encoding='utf-8'))
        verdict = a.get('verdict', a.get('recommendation'))
        assert verdict.startswith('CLOSE') == (n in expected_close), (n, verdict)
        matrix = a.get('requirementMatrix', a.get('fullRequirementMatrix'))
        assert matrix and (not a.get('gaps') if n in expected_close else a.get('gaps')), n
        packet = json.loads((R/f'issues/{n:02d}.json').read_text(encoding='utf-8'))
        rows.append({'number':n, 'canonicalId':a['canonicalId'], 'title':packet['issue']['title'],
                     'reviewer':worker, 'AUDIT_SHA':TARGET, 'disposition':verdict,
                     'matrixRows':len(matrix), 'assessment':str(path.relative_to(R)).replace('\\','/'),
                     'assessmentSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'gaps':a.get('gaps',[]),
                     'remainingIncrement':a.get('proposedNextIncrement', a.get('proposedBoundedNextIncrement',
                        a.get('proposedNextRlgwoIncrement', a.get('boundedNextIncrement')))),
                     'primaryReconciliation':'Every mandatory row reviewed; exact-target source, consumer bridge, negative controls, historical applicability and public evidence scope reconciled. No extra criteria invented.'})
rows.sort(key=lambda x:x['number'])
assert [x['number'] for x in rows] == list(range(1,38))
result = {'AUDIT_SHA':TARGET, 'primary':'Astra', 'date':'2026-10-08',
          'primaryRecordedConfiguration':{'model':'gpt-6-astra','reasoningEffort':'max','turnId':'01a11e3f-9134-7732-933d-b76ec938a9b9',
              'confirmation':'Local recorded turn_context; not hardware/backend attestation'},
          'issuesReviewed':37, 'obligations':sum(x['matrixRows'] for x in rows),
          'closeRecommendations':len(expected_close), 'openRecommendations':37-len(expected_close),
          'published':False, 'issues':rows,
          'reconciliationCorrections':[
              '#3 inert captured-cache-key mutation was source-equivalent under the generation guard, not an undetected required bug.',
              '#14 dry model thunder identity is retained under the owner H5 amendment; unsupported precipitation effects downgrade independently. The original incorrect-label oracle failure remains preserved.',
              '#14 does not require inventing a new README section where its contract required correction of a claim that is already absent.',
              '#24 subdued elapsed hierarchy and full-information readability are compatible; no fabricated owner conflict blocks a bounded repair.',
              '#34 physical Moonlight and subordinate below-horizon calendar presentation have distinct amended ownership; no blanket zero-atmosphere requirement.',
              '#33 remains open for original cost obligations and the separately authorized first-complete-celestial-scene successor. V1 growing-Moon captures are excluded from root defect evidence.',
              'CSP, idless-focus, CSS-uppercase, modal browser-chrome focus, delayed font capture and stale-label harness failures are retained and distinguished from runtime defects.'
          ],
          'boundaries':['No new runtime implementation during this audit.','N001/N002 PARTIAL and N003 BLOCKED remain scoped to their actual obligations.',
                        'Native Apple Bash3.2/macOS receipts were not substituted with Linux or disabled-builtin tests.',
                        'All historical reuse is explicitly source/input/consumer bound; no blanket all-tests-pass closure.',
                        'Public rollout permits documented initial acquisition and proves unchanged-scene normal1x replacement; it does not close the new immediate celestial startup requirement.']}
(R/'primary-reconciliation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['issuesReviewed','obligations','closeRecommendations','openRecommendations']}))
