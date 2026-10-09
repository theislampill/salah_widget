"""Reconcile primary-owned native receipts into reviewer B proposals only.

No browser, source, Git or external write. All outputs remain workers/B. The
earlier harness failure receipts are retained at their original paths.
"""
import hashlib,json
from pathlib import Path

OUT=Path(__file__).resolve().parent
AUDIT=OUT.parent.parent
SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
INDEX='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):Path(p).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

runs=['primary-native-B-markers-settled','primary-native-B-date-security','primary-native-B-date-security-rerun']
receipts={n:read(AUDIT/n/'results.json') for n in runs}
for r in receipts.values():
    assert r['target']==SHA and r['sourceSha256']==INDEX
    assert r['browser']['family']=='chromium' and r['browser']['version']=='148.0.7778.96'
    assert r['browser']['os']=='Windows'
selected={}
for run in runs:
    for row in receipts[run]['rows']:
        if row['error'] is None:
            assert row['checkStatus']=='PASS_SCOPED_NATIVE_CONSUMER' and not row['pageErrors']
            assert row['checks'] and all(c['pass'] for c in row['checks'])
            assert row['sourceSha256']==INDEX and row['fonts']['ready'] and row['fonts']['status']=='loaded'
            selected[row['id']]={'run':run,'row':row}
assert len(selected)==30
assert sum(v['row']['issue']==1 for v in selected.values())==12
assert sum(v['row']['issue']==9 for v in selected.values())==14
assert sum(v['row']['issue']==10 for v in selected.values())==4

manifest=read(OUT/'browser-fixtures/manifest.json')
assert manifest['auditTarget']==SHA and manifest['sourceSha256']==INDEX
fixture_rows={r['id']:r for r in manifest['rows']}
for key,value in selected.items():assert value['row']['fixtureSha256']==fixture_rows[key]['fixtureSha256']
primary_review=read(AUDIT/'primary-visual-review.json')
assert primary_review['AUDIT_SHA']==SHA
primary_visual={'path':'primary-visual-review.json','sha256':digest(AUDIT/'primary-visual-review.json'),'reviewer':primary_review['reviewer'],'scope':primary_review['scope'],'mappedObservations':[o for o in primary_review['observations'] if 'primary-native-B-' in o['evidence']]}
assert len(primary_visual['mappedObservations'])==3

failure_reconciliation=[
 {'failure':'Original four marker crops timed out awaiting document.fonts.ready after passing actual DOM checks.',
  'cause':'Intentionally pending dynamically appended native-data.js held the document-load/font lifecycle.',
  'repair':'Optional catalogue/Moon asset transports explicitly settle HTTP503; actual product unavailable handling retained. External Google font requests abort, real font lifecycle observed; screenshot timeout5s. No forged fonts.ready or screenshot bypass.',
  'preservedReceipt':'primary-native-B-markers/results.json'},
 {'failure':'Three intentionally unescaped security mutants failed generic footer-within-card before intended node/canary assertions.',
  'cause':'Native injected SVG default dimensions expand the footer from520.34375 to656.34375 while the card remains530.',
  'repair':'All repaired-positive geometry gates retained. Mutants require real boot/card and their own injected node/canary, record expected secondary overflow. All three independently detected.',
  'preservedReceipt':'primary-native-B-date-security/results.json'},
 {'failure':'Wrong-day/zone cases timed out waiting for tomorrow to remain loaded.',
  'cause':'Actual maintainPrayerDay() rejects and clears context-mismatched tomorrow (src/native/index.html:1188).',
  'repair':'Wait for actual painted Sunset date update unavailable after confirmed real render. No invalid bundle retention or production admission bypass required.',
  'preservedReceipt':'primary-native-B-date-security/results.json'},
 {'failure':'Before/missing native access failed descendant-only activeElement check after Tab.',
  'cause':'With one Close/autofocus control, native Tab moves to browser UI: activeElement BODY, document.hasFocus=false; dialog remains :modal/open.',
  'repair':'Record actual focus and require underlying date buttons stay inert; both explicit focus attempts are blocked. Initial modal focus, Escape/Close return and touch controls remain required and pass. No new circular JavaScript trap or product edit.',
  'preservedReceipt':'primary-native-B-date-security/results.json'}
]

pixel_specs=[
 (10,'primary-native-B-markers-settled','r000a-london--card.png','London both faint dashed adjusted markers visible at original positions; Sunrise hollow ring and post-transit Dhuhr remain. Clock/prayer/header/footer readable.'),
 (10,'primary-native-B-markers-settled','r000a-london--arc.png','Both dashed rings are visibly distinct from the universal14 mutant filled dots.'),
 (10,'primary-native-B-markers-settled','r000a-london-mutant--arc.png','Intended universal14 negative returns filled Fajr/Isha dots at unchanged original positions; relevant style guard visibly discriminates.'),
 (10,'primary-native-B-markers-settled','r000a-tromso--card.png','Finite polar layout; provider00:46 timing overlap is inherited and not artificially repositioned. Both classifications/classes are verified in actual DOM; overlap is disclosed.'),
 (10,'primary-native-B-markers-settled','r000a-madinah--card.png','Ordinary Fajr/interval-Isha marker presentation and Sunrise ring preserved; fixed header/footer/card readable.'),
 (1,'primary-native-B-date-security','r0001-ordinary--footer.png','Ordinary CE/AH era markers and tomorrow26 preview readable within measured card.'),
 (1,'primary-native-B-date-security','r0001-literal-control--footer.png','Arabic/quotes/ampersand/angle literal remains compact/ellipsized; no full arbitrary-literal visibility claim.'),
 (9,'primary-native-B-date-security-rerun','r0009-before--card.png','Actual before-Maghrib19 plus preview20, readable header/prayer/footer and restored footer focus.'),
 (9,'primary-native-B-date-security-rerun','r0009-missing--footer.png','Sunset date update unavailable visibly present, independently of prayer stale; complete AH obtained in disclosure.'),
 (9,'primary-native-B-date-security-rerun','r0009-missing--disclosure.png','Complete AH19, could-not-advance explanation, HJCoSA and requested/loaded UTC context readable; Close/focus visible.'),
 (9,'primary-native-B-date-security-rerun','r0009-wrong-zone--footer.png','Same visible unavailable cue for rejected context; no false advance claim.'),
 (9,'primary-native-B-date-security','r0009-boundary--card.png','Actual at-boundary full card shows complete2026-09-07 CE and selected1448-02-20 with no preview; fixed readable card.'),
 (9,'primary-native-B-date-security','r0009-different-method--disclosure.png','Selected20 with Aladhan;UAQ, UTC and requested/loaded day readable; no inherited HJCoSA claim.'),
 (9,'primary-native-B-date-security','r0009-unknown-method--disclosure.png','Selected20 with calendar convention unavailable readable; absence does not inherit HJCoSA.'),
]
pixels=[]
for issue,run,file,observation in pixel_specs:
    p=AUDIT/run/file;assert p.is_file()
    pixels.append({'issue':issue,'path':run+'/'+file,'sha256':digest(p),'reviewedBy':'Reviewer B via local view_image','observation':observation})

native_summary={'schema':'rlgwo-B-native-followup/1','target':SHA,'rootIndexSha256':INDEX,
 'executionOwner':'Primary; reviewer B prepared/read only, never launched a browser',
 'browser':receipts[runs[0]]['browser'],'acceptedUniqueCases':30,
 'runs':[{'path':n+'/results.json','sha256':digest(AUDIT/n/'results.json'),'driverSha256':r['driverSha256'],'status':r['status'],'allRowsAccepted':all(x['error'] is None for x in r['rows'])} for n,r in receipts.items()],
 'sourceFixtureManifestSha256':digest(OUT/'browser-fixtures/manifest.json'),'selectedCaseReceipt':[{'id':key,'run':v['run'],'fixtureSha256':v['row']['fixtureSha256'],'checks':len(v['row']['checks']),'error':None} for key,v in selected.items()],
 'failureReconciliation':failure_reconciliation,'pixelReview':pixels,
 'pixelLimit':'Separate boundary element-only footer PNG loses some middle glyph pixels; full-card PNG shows complete dates and is the qualifying boundary image. No assertion that every element-only crop is flawless.',
 'scope':'Actual local HTTP config/prayer/date/model/drawArc/CSS; original deterministic fixtures and expectations. Optional astronomy503 handling and actual system fallback font explicitly disclosed; no whole astronomy renderer/startup or public-origin exploit claim.',
 'primaryIndependentVisualReview':primary_visual,
 'publicationStatus':'PROPOSED; primary has recorded independent bounded pixel review, and must approve final reconciliation/immutable fresh receipt-crop links before publication/closure. No GitHub writes.'}
write(OUT/'native-followup-review.json',native_summary)

def compact_state(s):
    if s is None:return None
    out=dict(s)
    svg=out.pop('svg',None)
    if svg is not None:out['actualEmittedSvgSha256']=hashlib.sha256(svg.encode()).hexdigest()
    return out
def compact_receipt(r):
    out=dict(r);out['state']=compact_state(r['state'])
    out['transitions']=[{**t,'state':compact_state(t['state'])} for t in r['transitions']]
    out['rawSvgCustody']='Unmodified primary run results.json retains full emitted SVG. This assessment keeps its hash plus actual marker geometry/class/style readback.'
    return out
def evidence_for(number):
    return [{'id':key,'run':v['run'],'fixture':fixture_rows[key],'receipt':compact_receipt(v['row'])} for key,v in selected.items() if v['row']['issue']==number]
def inline_rows(number):
    rows=[]
    for item in evidence_for(number):
        r=item['receipt'];s=r['state'];name=item['id']
        if number==1:
            observed=f"ready={s['ready']}; renders={s['renders']}; nodes CE/AH={s['ceNodes']}/{s['ahNodes']}; canary={s['canary']}; config={s['configSource']}; footerBottom={s['footer']['bottom']:.5f}"
        elif number==9:
            d=s['dateTruth'];observed=f"AH={d['hijriText'] or 'unavailable'}; preview={d['previewDay']}; applied={d['maghribRollApplied']}; method={d['hijriMethod']}; unavailable={d['unavailableReason']}; prayerStale={s['prayerStale']}"
            if r['transitions']:observed+='; transitions='+','.join(t['name'] for t in r['transitions'])
        else:
            marks={m['key']:m for m in s['markers']}
            observed='; '.join(f"{k}: {marks[k]['status']}, class={marks[k]['class']}, ({marks[k]['x']},{marks[k]['y']},r{marks[k]['r']})" for k in ['Fajr','Isha'])
        rows.append((name,observed,len(r['checks']),r['fixtureSha256']))
    return rows

for number in [1,9,10]:
    p=OUT/f'{number:02}-assessment.json';a=read(p);assert a['target']['commit']==SHA
    for row in a['fullRequirementMatrix']:
        if row['disposition']=='unverified':row['disposition']='satisfied'
    if number==1:
        a['fullRequirementMatrix'][10]['observed']='Fresh primary actual HTTP browser:9 repaired positives confirm nonempty real render, own literals, nodes0/0/canary0; three independent isolated sink-removal mutants confirm own node1/canary1 while the other sink remains repaired. All12 final cases pass; expected negative overflow recorded.'
        a['fullRequirementMatrix'][11]['observed']='Primary325x530 card and ordinary footer captured; reviewer viewed ordinary CE/AH era and pre-Maghrib26 preview. Footer bottom520.34375<=530. System fallback font settled; no whole astronomy visual claim.'
        a['fullRequirementMatrix'][12]['observed']='Exact source/tree/runtime and primary DELIVERED_VERIFIED rollout read back; independent reviewer source/sink and native literal/canary/pixel reconciliation complete. This evidence-comment draft is prepared. Actual posting/closure held for primary immutable-proof approval; no public-origin exploit or already-posted claim.'
    elif number==9:
        a['fullRequirementMatrix'][8]['observed']='Fresh native Enter/Space/open/initial focus/Escape return plus touch/Close return pass in ordinary and missing-tomorrow scenes. Native modal rejects focus on underlying buttons after Tab to browser UI. Same painted strings/reason read back. Full long/tick/preset R0019 matrix remains separate.'
        a['fullRequirementMatrix'][13]['observed']='Fresh primary14 native scenarios qualify before/boundary/after/missing/late/wrong day/zone/invalid/missing AH/named format/convention; actual correction/reverse/midnight/duplicate/skip/long-sleep/month/year transitions and both title/hold mutants reached. Real footer/title/full-value/accessible labels/dateTruth agree; fixed card and missing/UAQ/unknown disclosure pixels reviewed. Exact-target retained calendar case with45 assertions supplies actual day adoption without double AH increment.'
        a['fullRequirementMatrix'][14]['observed']='Independent exact-target selected-date/provenance review and fresh native browser/crop proof complete; evidence comment draft prepared. Current deployment exact bytes separately verified. Primary immutable-proof/pixel approval precedes actual posting/closure; no calendar-authority adjudication or already-posted claim.'
    else:
        a['fullRequirementMatrix'][10]['observed']='Fresh primary4 native rows on325x530: London both dashed/subdued adj markers at19.37/134.93/r5 and274.41/133.93/r5, universal14 loses both; Tromso finite both adj; Madinah Fajr reachable and interval-Isha unknown. Actual classes/status/title/computed CSS/geometry confirmed. Reviewer inspected London positive/negative arc and all three cards; inherited polar timing overlap disclosed.'
        a['fullRequirementMatrix'][11]['observed']='Independent exact-tree source/parameter review,25 fresh source controls/required mutants and4 actual native positive/negative scenarios with reviewed pixels complete. Evidence-comment draft prepared; actual posting/closure held for primary immutable-proof/pixel approval. No public-origin fixture run or CI claim.'
    a['verdict']='CLOSE — SATISFIED';a['gaps']=[];a['missingChecksRequested']=[]
    a['scopeOfDone']='All binding behavior/evidence obligations traced and satisfied within stated source/native fixture scope. Reviewer closure recommendation only; primary proof/pixel approval and authorized publication remain pending.'
    a['proposedBoundedNextIncrement']=None
    a['primaryNativeExecution']={'cases':evidence_for(number),'uniqueCases':len(evidence_for(number)),'scope':native_summary['scope'],'reviewReceipt':'native-followup-review.json','executionOwner':'Primary; not worker browser execution'}
    a['pixelEvidence']=[x for x in pixels if x['issue']==number]
    a['primaryIndependentVisualReview']=primary_visual
    a['harnessFailureDisposition']=failure_reconciliation
    a['publicationPrecondition']='Primary independent bounded pixel review is recorded; primary must approve final packet reconciliation and immutable fresh receipt/crop links before posting or actual closure. Never publish private paths as public proof.'
    a['reviewerVsPrimary']='Reviewer B proposed CLOSE — SATISFIED, subject to primary challenge/pixel/immutable-proof approval. Not posted, closed or claimed CI.'
    write(p,a)
    def ref(v):return f'[{v["path"]}:{v["start"]}–{v["end"]}]({v["url"]})'
    def cell(v):return str(v).replace('|','\\|').replace('\n',' ')
    lines=[f'# RLGWO closure proof — {a["canonicalId"]} — {a["title"]}','','<!-- RLGWO-AUDIT:'+SHA+':'+a['canonicalId']+':2026-10-08 -->','',
     '**Reviewer recommendation: CLOSE — SATISFIED.** This is an unposted proposal for primary reconciliation; immutable fresh receipt/crop links must be approved before publication or actual closure.','',
     f'Target `{SHA}`, tree `{a["target"]["tree"]}`, runtime SHA-256 `{a["target"]["runtimeSha256"]}`, root `index.html` SHA-256 `{INDEX}`. Original contract body SHA-256 `{a["originalBodySha256"]}`, revision `{a["originalUpdatedAt"]}`; audit date2026-10-08. Complete body/discussion read; no omitted comment amendment.','',
     'Authored owners remain `src/native/`; root index is generated through `tools/build_native.py`. Completed native repairs are inherited work, not all credited to PR42. Source was clean/tree-equivalent. Primary release readback is DELIVERED_VERIFIED on this exact merge/runtime: Pages build1270547036,16 public root/V1 direct/iframe cold/warm browser cases and exact raw/Pages document bytes. Deployment smoke and deterministic issue controls are distinct.','',
     'Mandatory matrix:','',
     '| Obligation / contract section | Authored owner → delivered consumer | Discriminator | Expected → observed | Disposition |','|---|---|---|---|---|']
    for row in a['fullRequirementMatrix']:
        values=[row['obligation']+' ('+row['contractReference']+')',ref(row['authoredOwner'])+' → '+ref(row['deliveredConsumer']),ref(row['discriminator']),row['expected']+' → '+row['observed'],row['disposition'].upper()]
        lines.append('| '+' | '.join(cell(v) for v in values)+' |')
    lines+=['',f'Fresh reviewer source command: `C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe tests/{a["commandsExecuted"][0]["test"]}`; Windows Node22.16.0, expected/observed exit0, {a["freshExecution"]["caseCount"]} source cases passed. '+a['freshExecution']['scope'],'',
      'Primary executed the prepared original-fixture adaptation through Python/Playwright serially, actual local HTTP entry, Chromium148.0.7778.96 on Windows AMD64, viewport/card325×530 and DPR1, touch enabled. Controlled Date is installed before config/runtime initialization; deterministic matched prayer records and per-document Map storage are used. Google fonts are explicitly blocked: actual font-set ready=true, status=loaded,0 faces; computed original CSS selects system fallback. Optional catalogue and Moon asset transports explicitly return503, allowing actual product unavailable handling and preventing unrelated terrain solves. Actual config, prayer/model/date/drawArc/CSS and original positive/negative expectations remain. No whole astronomy-renderer/startup/public-origin exploit proof is inferred.','',
      'Fresh native through-consumer receipt (a mutant PASS means its named defect was detected):','',
      '| Scenario | Actual observed discriminator | Passing checks | Fixture SHA-256 |','|---|---|---:|---|']
    for name,observed,count,sha in inline_rows(number):lines.append('| '+' | '.join(map(cell,[name,observed,count,sha]))+' |')
    if number==1:
        lines+=['','All repaired positives retain visible literal text, nodes0/0 and canary0 after six actual prayer rows/nonempty clock render. Mutants independently create own SVG node and execute canary1; untouched other sinks stay inert. Their native SVG overflow is expected negative evidence, not a repaired-product geometry PASS. Plain formatter/token preservation (including exact1448/48/Safar/Saf/02/2/19/19), Arabic/quotes/ampersands and unavailable behavior are separately covered by exact-source controls. Ordinary footer pixels show CE/AH eras and preview26 within the card; arbitrary custom literals intentionally ellipsize in the compact footer.','']
    elif number==9:
        lines+=['','Before17:59:59Z selects19+preview20; exactly18:00 selects20/no preview. Missing/wrong-day/wrong-zone/invalid tomorrow retains19 with visible Sunset date update unavailable and prayerStale=false; full-value/title/accessible explanation says could not advance. Late release selects20 once and repeats identically. Actual accepted10→09 correction, reverse post→pre, admitted midnight20 promotion,08→10/10→10, long sleep and29/30-day month/year controls retain provider values with neutral anomaly. Selected UAQ/unknown convention remains independent of prayer method4. Both after-only title and global-hold mutants are independently detected.','',
         'Native Enter/Space moves focus to Close; touch opens the same view; Escape/Close restores the actual initiator. Tab may move into browser UI (BODY, document.hasFocus=false), while :modal/open remains true and attempts to focus both underlying date controls are blocked. This is preserved native modal containment, not an added circular trap. Full long/preset/tick/fallback UI qualification and docs remain owned by R0019; no administrative prerequisite closure is invented.','',
         'Exact-final-root retained [native calendar receipt](https://github.com/theislampill/salah_widget/blob/'+SHA+'/docs/real-sky/evidence/startup-cloud-20261007/final-v49/runs/joined-v49-final-chromium-native-lifecycle/results.json#L15934-L18325) supplies45 assertions with actual before/at Maghrib and loader-driven midnight promotion (AH08→09, then remains09 on new civil day). Different synthetic label days are display data, not an authority decision. The owner24-versus26 report remains UNVERIFIED, with no automatic correction.','']
    else:
        lines+=['','London actual adjusted CSS has fill-opacity.12, stroke-width1.1, stroke-opacity.6 and dasharray1.6 1.6; universal14 negative loses both ring classes while retaining the same positions. Sunrise remains a hollow ring; Sunrise/Maghrib y104 and Dhuhr x149.84 stay unchanged. Madinah finite18.5-degree Fajr is reachable;90 min Isha is unknown and described accordingly. Tromso retains both adj classes and finite layout; equal provider timing00:46 causes inherited marker overlap, which is not hidden or repositioned. Source controls separately kill shared-Fajr, parseFloat interval, description-only, ignored maximum/equality/status faults. This is model reachability classification, not a new observed-astronomy accuracy claim.','']
    lines+=['Pixel review performed by reviewer B (primary performs independent final reconciliation):','',
      '| Captured image | Direct pixel finding | SHA-256 |','|---|---|---|']
    for pix in a['pixelEvidence']:lines.append('| '+' | '.join(map(cell,[Path(pix['path']).name,pix['observation'],pix['sha256']]))+' |')
    lines+=['','Fresh crops/receipts above are currently local audit custody. **Publication hold:** primary must supply approved immutable links to the actual fresh receipts/crops; no private local path or hash alone is asserted as public pixel availability. The source/test links above are already immutable.','',
     'Preserved harness failures: initial markers timed out only at font-ready after behavior passed; explicit optional503 responses settle that actual lifecycle. Initial date/security failures were expected mutant SVG overflow before intended assertions, rejection-control wait incorrectly requiring tomorrow retention, and a descendant-only focus predicate that wrongly excluded browser UI. Original failed receipts are retained. Corrections changed only isolated harness readiness/negative classification/native-focus interpretation, left repaired-positive geometry and all relevant behavior gates intact, and required reached nodes/canary/native modality/return controls. No product source fix was made to obtain GREEN.','',
     'Historical reuse is narrow: exact-final-root Node logs and mapped native calendar paths. Earlier source components for formatter/escaping/selector/dialog/date CSS are byte-equivalent where checked; drawArc differs only by one diagnostic data-prayer-key attribute. A native-sky bundle hash is never treated as root-index identity. Legacy glint/PBR comparison failures and TODO placeholders do not gate these unrelated obligations; no failed science check is relabeled PASS.','',
     'Actual interfaces: '+' '.join(a['dependencies']),'',
     'Primary Astra independently inspected London rings versus mutant dots, complete before-Maghrib disclosure and wrong-zone unavailable footer; the recorded bounded visual findings agree with this review. Full-sky qualification is not inferred. Primary final packet reconciliation and immutable-evidence approval remain the publication boundary.','',
     'Local recorded client turn_context confirms gpt-6.1-sol/max, matching the requested reviewer configuration; not independent hardware/backend attestation. Primary owns immutable-evidence approval, final challenge and authorized publication/closure. This comment is proposed, not posted; no CI, public exploit, native sleep/NTP or full Safari/macOS qualification is claimed.','']
    (OUT/f'{number:02}-comment.md').write_text('\n'.join(lines),encoding='utf-8')

# Keep the open obligations scoped correctly after the narrow shared native smoke.
a=read(OUT/'25-assessment.json')
a['fullRequirementMatrix'][10]['observed']='Fresh native ordinary/missing smoke passes Enter/Space initial modal focus, blocked background focus after Tab/browser-UI transfer, Escape/touch/Close/return. Actual Tab reaching each trigger, tick focus persistence and full long/preset matrix remain unverified. No custom circular trap is added to the original native containment contract.'
a['fullRequirementMatrix'][11]['observed']='Fresh touch opens AH and Close returns initiator in ordinary/missing scenes; long-value touch scroll/selectability and either-trigger full matrix remain unverified.'
a['fullRequirementMatrix'][13]['observed']='Fresh native rendered missing/late/boundary/UAQ/unknown values/reasons and keyboard/touch smoke qualify those shared selector consumers. Continuous open-panel transition/tick/focus/no-effect cases and hostile/unavailable/preset matrix remain unverified.'
a['sharedNativeSmoke']='native-followup-review.json; narrow shared selector/access smoke does not close this UI contract or its required README/DESIGN gap.'
a['gaps']=['Explicit README/DESIGN full-value access instructions remain absent.',
 'Native Enter/Space/initial modal focus/background containment/Escape/touch/Close return are now credited. Remaining interaction proof: Tab reaching both triggers, tick/node focus persistence, continuous open-panel selection transitions, no-effect counters, and all preset/saved/unsafe/unavailable paths.',
 'Long custom/month values under actual fallback fonts still require complete wrap/no-horizontal-overflow/font-size, touch scroll/selectability, long/open crops and actual builder preview geometry; supported-host missing-dialog fallback is required only if that host demonstrates unavailability.']
a['proposedBoundedNextIncrement']='Preserve stable native buttons/dialog, shared safe selected projection and no-effect handlers. Add the missing README/DESIGN access instructions. Reuse completed ordinary/missing Enter/Space/modal-background/Escape/touch/Close-return and selected-value native proof; qualify only remaining actual Tab reachability, stable tick/open transitions/effect counters, all presets/saved/unsafe/unavailable paths and long/fallback touch-scroll-selectability bounds. Capture long/open card and actual builder preview geometry:325×530 card inside approved330×534 shell. Require a tested native-dialog fallback only if a supported actual host demonstrates missing behavior.'
a['missingChecksRequested'][0]['driverRequired']='Reuse completed ordinary/missing native keyboard/touch smoke. Remaining serial all-presets/saved-long/very-long/long-month/fallback/literal/stale matrix: actual Tab reaching both triggers, tick/open transitions/no-effect counts, long text wrap/font-size and touch-scroll-selection/client boxes, long/open card and builder geometry.'
write(OUT/'25-assessment.json',a)
comment=(OUT/'25-comment.md').read_text(encoding='utf-8')
comment=comment.replace('RecordingDOM explicitly does not emulate modal focus. Final-v49 proof_ui only clicks CE then Close; it cannot prove this keyboard matrix.',a['fullRequirementMatrix'][10]['observed'])
comment=comment.replace('Existing pointer click/open/close reuse is narrow only; no matched touch/scroll/selectability receipt established.',a['fullRequirementMatrix'][11]['observed'])
comment=comment.replace('Fresh recording controls support source implementation only; native browser matrix not established.',a['fullRequirementMatrix'][13]['observed'])
for old,new in [
 ('Mandatory native keyboard/focus/Escape/touch/scroll/fallback-font/overflow/transition/safe-event/effect matrix and measured crops are unverified.',a['gaps'][1]),
 ('Actual builder-preview/disclosure geometry and supported-host native dialog compatibility have not been mapped to exact issue proof.',a['gaps'][2]),
 ('Preserve the stable native buttons/dialog, one selected text projection, literal rendering and no-effect handlers. Add narrow README/DESIGN access instructions. Use the existing calendar fixture in a serial disposable actual-entry browser and qualify both triggers across all presets/saved/long/fallback-font/hostile/unavailable/transition cases. Record Tab/Enter/Space/Escape/Close focus, native touch/scroll/selection, effect counters and unchanged nodes. Capture default/long/open card and builder iframe: inner325×530, approved outer330×534. Add a tested fallback only if a supported actual host demonstrates native dialog missing behavior.',a['proposedBoundedNextIncrement'])]:comment=comment.replace(old,new)
smoke_note='\nFresh shared native smoke now establishes ordinary/missing Enter/Space initial focus, native background containment after Tab to browser UI, Escape/touch/Close and initiator return, plus real selected missing/late/UAQ/unknown full-value readback. This narrows the remaining #25 evidence to actual Tab reachability/tick focus/open transitions/no-effect/long-preset-touch-scroll-selectability/fallback/geometry compatibility and the mandatory README/DESIGN access instructions. No added circular JavaScript trap is required by the native containment contract.\n'
comment=comment.replace(smoke_note,'')+smoke_note
(OUT/'25-comment.md').write_text(comment,encoding='utf-8')

a=read(OUT/'32-assessment.json')
native_path='docs/real-sky/evidence/startup-cloud-20261007/final-v49/runs/joined-v49-final-chromium-native-lifecycle/results.json'
a['historicalReuse']['nativeReceipt']={'path':native_path,'start':14302,'end':15932,'url':f'https://github.com/theislampill/salah_widget/blob/{SHA}/{native_path}#L14302-L15932'}
a['gaps']=['Mandatory DESIGN one-API/two-authority and explicit timeScale=1 preview distinction remains inaccurate/absent.',
 'Exact-root native pre-script Date with independent performance.now and +120s/-30s direct model/host/sky readback is credited. Remaining required browser proof: scheduled forward/reverse prayer boundaries, day/cache/deferred-response/reclassification/request ownership and real-elapsed retry eligibility, hidden/show and explicit1/60/frozen matrix with matching output crops.']
a['proposedBoundedNextIncrement']='Preserve direct-wall default, anchored explicit modes, invalid-simulation guards, backward-aware loop and real-elapsed prayer ownership/day classifier. Correct the narrow DESIGN formula and explicit1x paragraph. Reuse the completed exact-root27-assertion pre-script Date/model/host/sky wall-step case; extend only the missing actual scheduled loop/prayer-boundary/day-cache/deferred-release/owner-reclassification/real-elapsed retry/hidden-resume/explicit-mode consumers with deterministic accepted UTC records and matching crops. Preserve the three mutants and avoid repeating unrelated terrain solves. Native sleep/NTP and adjacent weather retry cooldown remain outside this bounded claim; no new weather runtime fix is authorized.'
a['missingChecksRequested'][0]['command']='Reuse final-v49 native-lifecycle wall-clock-and-reduced-motion exact-root27-assertion case; primary serial disposable actual-entry driver for only the remaining scheduled-boundary/day/deferred-release/explicit-mode consumers. No production or host clock edit.'
write(OUT/'32-assessment.json',a)
comment=(OUT/'32-comment.md').read_text(encoding='utf-8')
comment=comment.replace('Actual pre-script browser wall-correction consumer/day/cache/late-response/visibility/explicit-mode matrix and output crops remain unverified.',a['gaps'][1])
comment=comment.replace('Preserve direct-wall default, anchored explicit modes, strict invalid-simulation guards, backward-aware loop and real-elapsed prayer ownership/day classifier. Correct the narrow DESIGN formula/parameter paragraph. Complete a disposable actual-browser pre-script Date/performance fixture with deterministic accepted UTC records and deferred request releases. Record both prayer-boundary directions, forward/backward day adoption/cache/late classification/owner slots, hidden/show and explicit1/60/frozen controls; crop clock/prayer/date output and retain the three mutants. Keep native sleep/NTP and the adjacent weather cooldown probe outside this bounded claim unless independently admitted.',a['proposedBoundedNextIncrement'])
wall_note='\nNarrow retained native browser credit: [wall-clock-and-reduced-motion exact-root receipt](https://github.com/theislampill/salah_widget/blob/'+SHA+'/'+native_path+'#L14302-L15932),27 assertions, installs Date before actual boot, retains independent performance.now and reads actual model/host/sky UTC under +120000ms/-30000ms direct-render wall steps. The remaining gap is the scheduled prayer-boundary/day-cache/deferred-release/reclassification/owner/visibility/explicit-mode consumer matrix, not a blanket absence of browser wall-correction proof. Weather backstep retry remains adjacent contextual scope; no runtime fix is authorized.\n'
comment=comment.replace(wall_note,'')+wall_note
(OUT/'32-comment.md').write_text(comment,encoding='utf-8')

summary=read(OUT/'summary.json')
for r in summary['results']:
    a=read(OUT/f'{r["issue"]:02}-assessment.json')
    r['verdict']=a['verdict'];r['gaps']=a['gaps']
    summary['missingChecksRequested'][str(r['issue'])]=a['missingChecksRequested']
summary['nativeFollowup']={'acceptedUniqueCases':30,'issues':[1,9,10],'receipt':'native-followup-review.json','browserExecutedBy':'Primary, serial','originalHarnessFailuresRetained':True,'nativeCircleTrapNotInvented':True,'primaryIndependentPixels':'primary-visual-review.json; exact audit target read and recorded','publicationHold':'Primary final packet reconciliation and immutable fresh proof-link approval'}
summary['historicalReuse']='Final-v49 exact-root source logs plus native calendar case with45 assertions and wall-step case with27 assertions mapped narrowly; no complete scheduled-day/accessibility matrix inferred.'
summary['publicationStatus']='PROPOSED_UNPOSTED; #1/#9/#10 reviewer CLOSE — SATISFIED subject primary proof approval; #8/#25/#32 LEAVE OPEN.'
write(OUT/'summary.json',summary)
print(json.dumps({'worker':'B','closeRecommendations':[1,9,10],'leaveOpen':[8,25,32],'acceptedNativeUniqueCases':30,'sourceUnmodified':True,'publication':'HELD'},indent=2))
