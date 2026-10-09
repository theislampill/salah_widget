"""Primary-reconciled text only; no commit or GitHub effect. Immutable SHA placeholder."""
import hashlib,json,pathlib
OUT=pathlib.Path(__file__).parent;AUDIT=OUT.parents[1]
BASE='https://github.com/theislampill/salah_widget/blob/AUDIT_EVIDENCE_COMMIT/docs/rlgwo-audit/20261008/'
def url(relative):return BASE+relative
def item(relative,title):return f'- [{title}]({url(relative)}).'
for n in [23,24,26,29,33,34,37]:
 p=OUT/f'{n}-assessment.json';a=json.loads(p.read_text(encoding='utf-8'))
 a['publication'].update(reconciledByPrimary=True,conclusionsApprovedByPrimary=True,approved=False,commentHashApproved=False,posted=False,publicEvidenceLinksPending=True,hold='Primary Astra reconciled all mandatory rows and conclusions. Substitute immutable evidence commit SHA, independently approve exact comment hash, publish comment then any approved closure. No GitHub effect yet.')
 a['publication']['evidenceBasePlaceholder']=BASE
 cpath=OUT/f'{n}-comment.md';c=cpath.read_text(encoding='utf-8')
 c=c.replace('Fresh local receipts/fixtures/crops above await the primary evidence-only commit and immutable public links; essential expected/observed results and hashes are included inline. This is a returned reviewer proposal, not a posted or approved comment. Primary must reconcile this issue individually and approve publication after evidence custody. No reviewer source/GitHub/commit/push effect occurred.', 'Primary Astra independently reconciled every mandatory row and this conclusion. This evidence comment precedes any approved closure action; it does not claim the issue was already closed. Reviewer F changed no runtime source or GitHub state.')
 c=c.replace('Full record/crop publication links await primary evidence-only custody; closure proposal is not posted or approved here.', 'Full records and crops are linked below. Primary Astra reconciled the exact-tree closure conclusion; this comment records proof before any closure action.')
 c=c.replace('The primary has not yet reconciled/approved it','Primary Astra reconciled it')
 # Remove implementation/publication-only plans for satisfied issues; the final public text is proof.
 if n in [26,29]:
  start=c.index('Every mandatory row is satisfied or validly superseded.')
  end=c.index('\nDependencies:',start)
  c=c[:start]+'Every mandatory row is satisfied or validly superseded. No runtime repair remains for this bounded issue.\n'+c[end:]
 c += '\nImmutable audit inputs and fresh receipts:\n\n'
 c += item(f'issues/{n}.json','Complete original contract, discussion and events')+'\n'
 c += item(f'workers/F/{n}-assessment.json','Full reconciled obligation/evidence matrix')+'\n'
 c += item('reviewer-model-settings.json','Recorded six-reviewer model/effort configuration')+'\n'
 c += item('release.json','Delivered target verification')+'\n'
 c += item('public-browser-summary.json','16 actual public root/V1 browser cases')+'\n'
 c += item('workers/F/followup-tests/receipt.json','Fresh lightweight current-source command receipts')+'\n'
 if n in [29,33,34,37]:c += item('workers/F/followup-tests/adaptation-receipt.json','Disclosed unchanged-assertion fixture adaptations')+'\n'
 if n in [29,33,34]:
  c += item('workers/F/followup-tests/replacement-receipt.json','Actual calendar/astronomical/current catalogue and opaque-composition replacements')+'\n'
  c += item('workers/F/lunar-interface-controls.cjs','Current interface and fade-leak negative control')+'\n'
 if n==26:
  for e in ['chromium','firefox']:
   c += item(f'primary-native-F2-{e}/results.json',e+' V2 healthy and both native mutation controls')+'\n'
   for size in ['mobile','desktop']:c += item(f'primary-native-F2-{e}/{size}-focus.png',e+' '+size+' native keyboard-focus crop')+'\n'
  c += item('workers/F/radio_keyboard_check_v2.py','Exact final native keyboard driver')+'\n'
  c += item('workers/F/native-radio-fixture-v2.cjs','Exact final contained current-builder fixture')+'\n'
 if n==29:
  c += item('primary-native-F-moon-debug/results.json','Actual public current-surface instrument and reversible error/bounds controls')+'\n'
  c += item('primary-native-F-moon-debug/debug-card.png','Actual opt-in card crop with current V5 calendar source')+'\n'
  c += item('primary-native-F-moon-debug/debug-readout.png','Raw300×300/R144 coordinate/luminance/alpha readout')+'\n'
  c += item('workers/F/moon_debug_probe.py','Exact primary native current-surface probe')+'\n'
  c += item('workers/F/r001d-diagnostics-current-surface.cjs','All21 original diagnostics assertions with disclosed current-surface input')+'\n'
  c += item('workers/F/r001d-mutations-current-surface.cjs','Six retained semantic fault controls')+'\n'
 if n==37:c += item('workers/F/followup-tests/cloud-mutants/receipt.json','Both healthy cloud suites and all six original cloud faults')+'\n'
 if (AUDIT/'primary-visual-review.json').is_file():c += item('primary-visual-review.json','Primary independent visual readback')+'\n'
 cpath.write_text(c,encoding='utf-8')
 a['publication']['preparedCommentSha256']=hashlib.sha256(c.encode('utf-8')).hexdigest()
 p.write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
summarypath=OUT/'summary.json';summary=json.loads(summarypath.read_text(encoding='utf-8'))
summary['publication']='Primary Astra reconciled all65 rows/conclusions. Exact comment hash approval remains false until immutable SHA substitution; publish comment before any approved closure; no GitHub effects yet.'
summary['publicationEvidenceBasePlaceholder']=BASE
summary['preparedCommentSha256']={str(n):json.loads((OUT/f'{n}-assessment.json').read_text(encoding='utf-8'))['publication']['preparedCommentSha256'] for n in [23,24,26,29,33,34,37]}
summarypath.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'primaryReconciled':True,'finalTextPrepared':7,'placeholder':'AUDIT_EVIDENCE_COMMIT','exactHashApproval':False,'GitHubEffects':False,'comments':summary['preparedCommentSha256']}))
