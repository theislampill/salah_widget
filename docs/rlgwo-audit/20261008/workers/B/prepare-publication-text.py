"""Produce primary-reconciled text; bind only after the primary supplies a SHA.

Writes workers/B only. AUDIT_EVIDENCE_COMMIT is an intentional literal stand-in,
not an assertion that an evidence commit or GitHub publication already exists.
"""
import hashlib,json,re
from pathlib import Path

OUT=Path(__file__).resolve().parent
AUDIT=OUT.parent.parent
SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
BASE='https://github.com/theislampill/salah_widget/blob/AUDIT_EVIDENCE_COMMIT/docs/rlgwo-audit/20261008/'
NUMBERS=[1,8,9,10,25,32]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def proof(label,path):
    assert (AUDIT/path).is_file(),path
    return f'[{label}]({BASE+path})'

release=read(AUDIT/'release.json')
assert release['AUDIT_SHA']==SHA and release['status']=='DELIVERED_VERIFIED'
native=read(OUT/'native-followup-review.json')
assert native['target']==SHA and native['acceptedUniqueCases']==30
links=[]

closure_observed={
 1:'Exact source/tree/runtime and DELIVERED_VERIFIED rollout are read back. Reviewer B and primary Astra reconciled the mandatory source/sink, native literal/canary and pixel controls. The immutable linked proof precedes manual closure; no public-origin exploit or CI claim.',
 9:'Reviewer B and primary Astra reconciled exact-target selected-date/provenance behavior, fresh native controls and crops, and delivered byte identity. The linked proof precedes manual closure; no calendar-authority adjudication or automatic correction.',
 10:'Reviewer B and primary Astra reconciled exact-tree parameter interpretation,25 fresh source controls/required mutants and4 native positive/negative scenarios with inspected pixels. The linked proof precedes manual closure; no public-origin fixture or CI claim.'
}
for number in NUMBERS:
    path=OUT/f'{number:02}-assessment.json';a=read(path)
    assert a['target']['commit']==SHA
    expected='CLOSE — SATISFIED' if number in closure_observed else 'LEAVE OPEN'
    assert a['verdict']==expected
    comment_path=OUT/f'{number:02}-comment.md'
    s=comment_path.read_text(encoding='utf-8')
    if number in closure_observed:
        row=a['fullRequirementMatrix'][-1]
        old=row['observed'];row['observed']=closure_observed[number]
        s=s.replace(old,cell_new:=row['observed'])
        s=s.replace('**Reviewer recommendation: CLOSE — SATISFIED.** This is an unposted proposal for primary reconciliation; immutable fresh receipt/crop links must be approved before publication or actual closure.',
          '**CLOSE — SATISFIED.** Primary Astra reconciled the complete mandatory contract, source and native evidence. This proof precedes manual closure.')
        s=s.replace('Pixel review performed by reviewer B (primary performs independent final reconciliation):',
          'Reviewer B pixel findings, independently reconciled by primary Astra:')
        s=s.replace('Fresh crops/receipts above are currently local audit custody. **Publication hold:** primary must supply approved immutable links to the actual fresh receipts/crops; no private local path or hash alone is asserted as public pixel availability. The source/test links above are already immutable.',
          'The linked raw receipts and captured images support these findings; their SHA-256 values are retained above and in the evidence packet. Source/test links separately identify the delivered implementation.')
        s=s.replace('Primary Astra independently inspected London rings versus mutant dots, complete before-Maghrib disclosure and wrong-zone unavailable footer; the recorded bounded visual findings agree with this review. Full-sky qualification is not inferred. Primary final packet reconciliation and immutable-evidence approval remain the publication boundary.',
          'Primary Astra independently inspected the London rings/mutant dots, complete before-Maghrib disclosure and wrong-zone unavailable cue, read every mandatory row and reconciled the closure conclusions. These observations remain bounded to the stated native controls; they do not certify the complete sky renderer.')
        s=s.replace('Local recorded client turn_context confirms gpt-6.1-sol/max, matching the requested reviewer configuration; not independent hardware/backend attestation. Primary owns immutable-evidence approval, final challenge and authorized publication/closure. This comment is proposed, not posted; no CI, public exploit, native sleep/NTP or full Safari/macOS qualification is claimed.',
          'Reviewer configuration: gpt-6.1-sol/max, confirmed by local recorded turn_context. Primary Astra reconciled this proof and controls its publication and subsequent manual closure. No CI, public exploit, native sleep/NTP or full Safari/macOS qualification is claimed.')
        for pixel in a['pixelEvidence']:
            name=Path(pixel['path']).name
            s=s.replace('| '+name+' |','| '+proof(name,pixel['path'])+' |')
    else:
        old='This is reviewer B’s proposed assessment and comment, not yet primary-reconciled or posted. Primary Astra owns final challenge and publication approval. Requested routing is Sol 6.1/max; local client recorded turn_context confirms gpt-6.1-sol and max for this reviewer session. That is a client configuration receipt, not independent hardware/backend attestation. Native sleep/NTP, full Safari/macOS compatibility and unrelated real-sky gate closure are outside this bounded evidence.'
        s=s.replace(old,'Primary Astra read the complete mandatory matrix and reconciled the LEAVE OPEN conclusion and precise next increment. Reviewer configuration gpt-6.1-sol/max is confirmed by local recorded turn_context. Existing deployment and shared native proof are credited above; only the identified obligations remain open. Native sleep/NTP, full Safari/macOS compatibility and unrelated real-sky gate closure remain outside this evidence.')
    assert 'unposted proposal' not in s and 'not yet primary-reconciled' not in s and 'This comment is proposed' not in s
    a['reviewerVsPrimary']='Reviewer B findings and complete mandatory matrix reconciled and approved by primary Astra; close1/9/10, leave8/25/32 open. This worker makes no GitHub writes.'
    a['scopeOfDone']='Exact-target source and executed/reused evidence reviewed; primary Astra reconciled every binding row and the stated verdict. Completed native controls remain scoped; open gaps are retained precisely.'
    a['primaryReconciliation']={'status':'APPROVED','reviewer':'primary Astra','authority':'Parent explicitly confirmed full-contract and native-proof review; independent visual observations retained in primary-visual-review.json','approvedVerdict':expected}
    a['publicationPrecondition']='Primary must replace AUDIT_EVIDENCE_COMMIT with the approved immutable evidence SHA, verify linked file hashes/readback, publish the evidence comment before any manual closure. No publication performed by reviewer B.'
    a['publicationTextStatus']='PRIMARY_RECONCILED_AWAITING_IMMUTABLE_SHA_BINDING'
    case_links=[]
    if number in closure_observed:
        for case in a['primaryNativeExecution']['cases']:
            raw=case['run']+'/results.json'
            s=s.replace('| '+case['id']+' |','| '+proof(case['id'],raw)+' |')
            if raw not in case_links:case_links.append(raw)
        relevant_images=[p['path'] for p in a['pixelEvidence']]
    elif number==25:
        case_links=['primary-native-B-date-security/results.json','primary-native-B-date-security-rerun/results.json']
        relevant_images=['primary-native-B-date-security-rerun/r0009-before--disclosure.png','primary-native-B-date-security-rerun/r0009-missing--disclosure.png']
    else:
        relevant_images=[]
    a['immutableFreshEvidenceLinks']={
      'assessment':BASE+f'workers/B/{number:02}-assessment.json',
      'sourceReceipts':BASE+'workers/B/fresh-test-receipts.json',
      'sourceLog':BASE+'workers/B/'+a['commandsExecuted'][0]['test']+'.log',
      'rawNativeReceipts':[BASE+p for p in case_links],
      'capturedImages':[BASE+p for p in relevant_images],
      'reconciliation':BASE+'workers/B/native-followup-review.json' if case_links else None,
      'shaBinding':'AUDIT_EVIDENCE_COMMIT literal to be replaced by primary after immutable SHA/hash approval'}
    write(path,a)
    section=['','Fresh evidence and reconciliation:','',
      '- '+proof('Complete obligation assessment',f'workers/B/{number:02}-assessment.json')+', '+proof('fresh source test receipts','workers/B/fresh-test-receipts.json')+', '+proof('source log','workers/B/'+a['commandsExecuted'][0]['test']+'.log')+'.',
      '- '+proof('Delivered baseline','release.json')+', '+proof('public browser rollout','public-browser-summary.json')+', '+proof('exact raw/Pages document distribution','public-document-distribution.json')+'.']
    if case_links:
        section+=['- '+', '.join(proof('raw native receipt '+str(i+1),p) for i,p in enumerate(case_links))+'.',
          '- '+proof('Original fixture manifest','workers/B/browser-fixtures/manifest.json')+', '+proof('isolated preparation','workers/B/prepare-native-fixtures.cjs')+', '+proof('serial native driver','workers/B/run-native-evidence.py')+', '+proof('preserved failures and source-backed reconciliation','workers/B/native-followup-review.json')+', '+proof('primary independent pixel review','primary-visual-review.json')+'.']
        if number in closure_observed:
            section+=['- '+proof('Original marker capture failure','primary-native-B-markers/results.json')+' and '+proof('original date/security run including expected mutant and readiness/focus failures','primary-native-B-date-security/results.json')+' remain preserved; the corresponding minimal corrected run is linked above.']
        elif relevant_images:
            section+=['- '+', '.join(proof(Path(p).name,p) for p in relevant_images)+': these establish the credited short-value shared smoke, not the remaining long/preset/tick/no-effect matrix.']
    if number==32:
        section+=['- '+proof('Adjacent weather wall-step probe','workers/B/weather-wall-step-probe.json')+' and '+proof('read-only actual-wrapper probe','workers/B/weather-wall-step-probe.cjs')+': contextual weather cooldown finding, outside automatic R0020 runtime-fix authority.']
    s+='\n'.join(section)+'\n'
    comment_path.write_text(s,encoding='utf-8')
    links.append({'issue':number,'comment':str(comment_path),'verdict':expected,'evidencePlaceholderCount':s.count('AUDIT_EVIDENCE_COMMIT'),'mandatoryRows':len(a['fullRequirementMatrix'])})

summary=read(OUT/'summary.json')
summary['publicationStatus']='PRIMARY_RECONCILED; publication text ready for approved immutable evidence SHA/hash binding. No reviewer GitHub writes.'
summary['primaryReconciliation']={'status':'APPROVED','reviewer':'primary Astra','close':[1,9,10],'leaveOpen':[8,25,32],'fullMandatoryMatricesRetained':True,'failureReconciliationRetained':True}
summary['publicationText']='Six NN-comment.md files; AUDIT_EVIDENCE_COMMIT is an intentional unresolved literal until primary approves immutable SHA/hash binding.'
write(OUT/'summary.json',summary)
write(OUT/'publication-text-receipt.json',{'schema':'rlgwo-B-publication-text/1','target':SHA,'primaryReconciled':True,'files':links,'noGitHubWrites':True,'sourceUnmodified':True,'shaBindingPending':'AUDIT_EVIDENCE_COMMIT'})
print(json.dumps({'primaryReconciled':True,'comments':6,'mandatoryRows':sum(x['mandatoryRows'] for x in links),'closedConclusions':[1,9,10],'openConclusions':[8,25,32],'noGitHubWrites':True,'evidenceShaBindingPending':True},indent=2))
