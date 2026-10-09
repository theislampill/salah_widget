'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const out=__dirname,audit=path.dirname(path.dirname(out));
const read=p=>JSON.parse(fs.readFileSync(path.join(out,p),'utf8'));
const save=(p,x)=>fs.writeFileSync(path.join(out,p),JSON.stringify(x,null,2)+'\n');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be',blob='https://github.com/theislampill/salah_widget/blob/'+SHA+'/';
const q14=read('browser14-chromium-v2/results.json'),q30=read('browser30-chromium-v2/results.json'),reconcile=read('browser14-v2-semantic-reconciliation.json');
if(reconcile.status!=='MATCHES CORRECT QUANTITATIVE-EFFECT ORACLE'||q30.status!=='PASS'||q30.cases.length!==3||!q30.runtimeUnchanged)throw Error('Native evidence missing or nonconforming');
const reuse=read('historical-source-equivalence.json');if(reuse.regions.length!==8||reuse.regions.some(r=>!r.equal))throw Error('Scoped source equivalence missing');
const h8='C:/Users/theis/Documents/Codex/startup-cloud-hotfix-20261007/h8';
const movementPath=path.join(h8,'joined-v45-chromium-continuous-above-transitions/frames.jsonl');
const movement=fs.readFileSync(movementPath,'utf8').trim().split(/\r?\n/).map(s=>JSON.parse(s));
const before=movement[107],after=movement[120];
if(before.weather.rawCode!==63||after.weather.rawCode!==63||before.weather.modelPrecipMm!==2||after.weather.modelPrecipMm!==2||before.weather.cloudFieldSeed!==after.weather.cloudFieldSeed)throw Error('Motion scene identity changed');
const pixels=[];
for(const [issue,collection,ids]of [[14,'browser14-chromium-v2',['14-dry','14-wet']],[30,'browser30-chromium-v2',['30-equator','30-meridian','30-origin']]]){
 for(const id of ids)for(const kind of ['card','header','footer']){
  const relative='workers/C/'+collection+'/'+id+'/'+kind+'.png',p=path.join(audit,relative);
  pixels.push({issue,case:id,kind,path:relative,sha256:sha(fs.readFileSync(p)),
   inspection:kind==='card'?'C viewed actual whole-card crop: header/prayer/footer readable; dry14 has no rain; wet14 and all30 show falling model rain. No new optics/art PASS inferred.':'Capture exists with recorded SHA; whole-card review covers readability, no independent header/footer zoom judgment claimed.'});
 }
}
const retainedMotion={kind:'HISTORICAL_EXECUTED_PIXEL_MOTION_REUSE_WITH_EXACT_MOTION_AND_CLOUD_SOURCE_EQUIVALENCE',
 oldRuntime:reuse.retainedBrowser.runtime,deltaSeconds:(after.at-before.at)/1000,
 before:{path:'joined-v45-chromium-continuous-above-transitions/frame-0107.png',sha256:sha(fs.readFileSync(path.join(h8,'joined-v45-chromium-continuous-above-transitions/frame-0107.png'))),at:before.at},
 after:{path:'joined-v45-chromium-continuous-above-transitions/frame-0120.png',sha256:sha(fs.readFileSync(path.join(h8,'joined-v45-chromium-continuous-above-transitions/frame-0120.png'))),at:after.at},
 sameModel:{code:63,amountMm:2,generation:before.weather.target.generation,cloudSeed:before.weather.cloudFieldSeed,moonPhase:before.moon.phase},
 observerReview:'C viewed both pixels: cloud veil and cells visibly change over26.1401s with same model and lunar phase; header/footer readable and half-Moon retained. This is pixel motion evidence, never the qaState cloud hash.',
 equivalenceRegions:reuse.regions.filter(r=>['motion-policy','cloud-generator-motion','cloud-per-use-consumer'].includes(r.id)),
 publicBasis:blob+'docs/real-sky/evidence/startup-cloud-20261007/final-v49/QUALIFICATION.json#L15145-L15215',
 limits:'Historical explicit motion=full under no-preference; identical motion-policy source makes the no-reduction default equivalent in this admitted scene. Not fresh V2 clock/M0, not new all-phase Moon/optics acceptance. Existing final target public 16-case and H8 qualification remain separate.'};
save('browser-pixel-review.json',{schema:'rlgwo-C-pixel-review-v1',target:SHA,browserExecutionBy:'primary',reviewer:'C',pixels,retainedMotion,
 sourceBoundCases:{R000E:{originalStatus:q14.status,reconciliation:reconcile.status,dryParticles:0,wetParticles:32},R001E:{originalStatus:q30.status,cases:3}},
 limitations:'Blocked external fonts and synthetic prayer/model fixtures are declared. No real-provider, prayer-provider zero-axis support, all-phase art approval or direct-observation claim.'});
function evidenceRef(file,description){return {file:'workers/C/'+file,start:null,end:null,url:null,description};}
const rows14={
 E07:'Primary executed actual dry raw95/0 current plus HTTP0dBZ tile. Native Image/canvas sampled49 returns (meanAlpha73/255); actual particles0, precip/lightning off, compatibility mm0 and no observed claim. H5 raw95 model icon/data-fx stays labelled; source lower effect gate reason is overcast.',
 E09:'Actual-source Chrome148 native two-scene acquisition/canvas/paint crop packet inspected: dry0 particles and wet2mm32particles; source-owned storage/clock/transport and body/image reads recorded. Original modelCondition oracle FAIL remains preserved; independently derived correct effect predicate matches all required quantities and permissions.',
 E12:'C inspected dry/wet native whole-card crops: header20°, card325×530 and complete footer; preserved source-equivalent26.1401s cloud-motion/half-Moon pixels plus final exact-runtime public entry/Moon/replacement qualification cover scoped preservation. No new renderer-art/all-phase optics PASS from the weather scalar fixture.',
 E13:'Both independent source barriers, direct numeric caller and diagnostic reachability reviewed; original RED and fresh source GREEN/mutant RED retained; exact source native acquisition/consumer pixels and corrected effect semantics linked. Complete proposed evidence comment prepared; primary approval/publication precedes manual closure.'
};
const rows30={
 '1E10':'Primary exact-source Chrome148 fixed-site native browser(0,30),(30,0),(0,0) each consumes actual Open-Meteo and exact radar manifest bodies, requests correct HTTP image tile(37,32),(32,26),(32,32), caches temp20 and amount2, paints model-thunder icon/data-fx and24/29/26 visible rain particles; none lightning or observation claim.',
 '1E11':'C inspected all3 native whole-card crops: card325×530, footer top502.40625/bottom520.34375, readable header/prayers/footer and structured rain/clouds. Source-equivalent26.1401s motion/half-Moon pixels plus final public normal1x Moon/replacement qualification preserve existing behavior; no new renderer-art PASS or M0 claim from fixed-clock scalar scenes.',
 '1E12':'Both actual guards/query/tile callers reviewed at final source; original RED counterexamples and two independent guard mutants each fail4zero cases while two nonzero controls pass; untouched6/6 GREEN and3 native browser consumer cases prove completion. Complete proposed evidence comment is ready for primary independent review, evidence binding and publication before manual closure.'
};
const esc=s=>String(s??'').replace(/\|/g,'\\|').replace(/\r?\n/g,'<br>');
const links=refs=>refs.map(r=>r.url?'['+r.file+(r.start?':'+r.start+'–'+r.end:'')+']('+r.url+')':esc(r.description||r.file)).join('<br>');
const row=r=>'| '+r.id+' | '+esc(r.obligation)+' | '+links([...r.authoredOwner,...r.deliveredConsumer])+' | '+esc(r.discriminator)+'; expected: '+esc(r.expected)+'<br>Observed: '+esc(r.observed)+'<br>'+links(r.evidence)+' | **'+r.status.toUpperCase()+'** |';
const summary=read('summary.json');
for(const issue of [14,30]){
 const a=read(issue+'-assessment.json'),updates=issue===14?rows14:rows30;
 for(const[id,observed]of Object.entries(updates)){
  const r=a.requirementMatrix.find(r=>r.id===id);if(!r)throw Error('Row missing '+id);
  r.status='satisfied';r.observed=observed;
  r.limitations='Scoped actual native input/consumer proof and explicitly retained source-equivalent preservation; final independent primary publication remains a separate authority/effect precondition.';
  r.evidence=r.evidence.filter(e=>!(e.file||'').startsWith('workers/C/'));
  r.evidence.push(evidenceRef(issue===14?'browser14-chromium-v2/results.json':'browser30-chromium-v2/results.json','Primary executed source-bound browser receipt; relative public evidence binding pending'));
  if(issue===14)r.evidence.push(evidenceRef('browser14-v2-semantic-reconciliation.json','Original FAIL retained; exact quantitative-effect semantic re-evaluation'));
  r.evidence.push(evidenceRef('browser-pixel-review.json','Actual crop SHA/inspection and source-equivalent26.1401s pixel motion custody'));
 }
 if(a.requirementMatrix.some(r=>r.status!=='satisfied'&&r.status!=='validly superseded'))throw Error('Mandatory row incomplete '+issue);
 a.verdict='CLOSE — SATISFIED';a.gaps=[];a.proposedNextRlgwoIncrement=null;
 a.substantiveClosureProof={allBindingRowsSatisfied:true,sourceBoundBrowser:'workers/C/'+(issue===14?'browser14-chromium-v2':'browser30-chromium-v2')+'/results.json',
  browserPixelReview:'workers/C/browser-pixel-review.json',preservedFailures:issue===14?['workers/C/browser14-chromium/results.json','workers/C/browser14-chromium-v2/results.json']:['workers/C/browser14-chromium/results.json'],
  semanticReconciliation:issue===14?'workers/C/browser14-v2-semantic-reconciliation.json':null,
  approval:'NOT APPROVED BY C; primary independent review and immutable evidence branch links required before external comment or closure',
  noProductionMutation:true};
 a.reusedEvidence=a.reusedEvidence.filter(r=>r.kind!=='HISTORICAL_EXECUTED_PIXEL_MOTION_REUSE_WITH_EXACT_MOTION_AND_CLOUD_SOURCE_EQUIVALENCE');a.reusedEvidence.push(retainedMotion);
 a.publication.publicEvidenceBinding='PENDING PRIMARY EVIDENCE BRANCH AND INDIVIDUAL APPROVAL';
 a.reviewerReconciliation='C independently read primary native receipts, inspected exact crops and reconciled every binding row. C recommends closure; primary must challenge/approve and attach immutable evidence links before external effects. C performed no browser launch or GitHub write.';
 save(issue+'-assessment.json',a);
 let md=fs.readFileSync(path.join(out,issue+'-comment.md'),'utf8');
 md=md.replace(/^# RLGWO closure audit.*$/m,'# RLGWO closure proof — '+a.canonicalId+' — '+a.title);
 const done=issue===14?'Actual radar alpha remains unitless at accessor/diagnostics, and numeric third-argument callers cannot restore quantitative storm authority. Exact dry/wet acquisition/paint controls and independent mutants prove the bounded correction under the owner’s current-model amendment.':'Both eligible acquisition owners preserve valid zero coordinates through actual weather query, radar tile and native consumer; direct-invalid, normalization, busy/SIM/cooldown and stale-context controls remain intact.';
 md=md.replace(/\*\*Recommendation: LEAVE OPEN\.\*\*[^\n]*/,'**Recommendation: CLOSE — SATISFIED.** '+done);
 md=md.replace('This is a proposed issue-specific audit, awaiting primary challenge/reconciliation and individual publication approval. It is not a posted closure or a new authorization to change production.','This is a proposed complete closure proof, awaiting primary independent challenge, immutable evidence binding and individual publication approval. It is not a posted comment or executed closure.');
 for(const r of a.requirementMatrix){const lines=md.split('\n'),i=lines.findIndex(s=>s.startsWith('| '+r.id+' |'));if(i<0)throw Error('Comment matrix missing '+r.id);lines[i]=row(r);md=lines.join('\n');}
 md=md.replaceAll('All six material weather regions match final delivered root bytes:','All eight material regions (six weather regions plus explicit motion policy/cloud generator) match final delivered root bytes:');
 const existingNative=md.indexOf('## Exact-source native consumer and pixel proof');
 const increment=existingNative>=0?existingNative:md.indexOf('## Next RLGWO increment required for closure'),mark=md.indexOf('<!-- RLGWO-AUDIT:');
 if(increment<0||mark<increment)throw Error('Missing closure footer');
 let native='## Exact-source native consumer and pixel proof\n\n';
 if(issue===14){
  native+='Primary executed the [two-scene native acquisition packet](workers/C/browser14-chromium-v2/results.json) with exact final source/runtime. Dry raw95/0mm plus actual uniform0dBZ Image/canvas has49 returns/meanAlpha73⁄255,0particles, precip/lightning off, radar compatibility0mm and `observedPresent=false`. Wet raw95/2mm has32visible particles, precip on, lightning off. C inspected the [dry card](workers/C/browser14-chromium-v2/14-dry/card.png) and [wet card](workers/C/browser14-chromium-v2/14-wet/card.png): header20°, readable prayers and complete footer,325×530.\n\n';
  native+='**Preserved failed oracle, separately corrected semantics:** original V2 result remains **FAIL** because the added assertion expected `qa.wxTruth.modelCondition==overcast`. [The offline re-evaluation receipt](workers/C/browser14-v2-semantic-reconciliation.json) quotes the exact failing assertion, original result SHA and all nine stronger effect/custody checks. [Native1629–1643]('+blob+'src/native/index.html#L1629-L1643) deliberately separates lower `effectCode` from raw live `modelCode` under H5/H8. Dry `modelGateReason` and `visualPermissions.quantitativeSupport` both say `thunder model code, interval precip0.00mm below model threshold → overcast`; no wet/strike permission or physical radar amount exists. Raw model WMO95 stays labelled thunder, as expressly allowed. All19other meaningful dry assertions and all19wet assertions passed. The original pure lower-gate3 requirement remains independently GREEN and becomes RED when direct numeric-radar influence is restored. No consumer was changed, no completed browser operation replayed, no original FAIL relabelled PASS, and no legitimate negative weakened.\n\n';
 }else{
  native+='Primary’s [exact-source native browser receipt](workers/C/browser30-chromium-v2/results.json) is PASS for all3 fixed-site cases,57assertions, Chromium148.0.7778.96/Windows. Each actual weather and exact manifest body was consumed before paint. Actual HTTP image tile requests were(0,30)→37/32, (30,0)→32/26, (0,0)→32/32. The actual chip is model-thunder20°, `data-fx=thunder`, amount2mm permits24/29/26visible model particles, and lightning stays off with no observation claim.\n\nC inspected all three whole-card crops: [equator](workers/C/browser30-chromium-v2/30-equator/card.png), [meridian](workers/C/browser30-chromium-v2/30-meridian/card.png), [origin](workers/C/browser30-chromium-v2/30-origin/card.png). The card is325×530; footer spans502.40625–520.34375, with readable header/prayers/footer. No epsilon or fallback location is introduced; target remains the captured numeric pair.\n\n';
 }
 native+='[Pixel review and custody](workers/C/browser-pixel-review.json) additionally records retained actual cloud-motion pixels26.1401s apart under the same WMO63/2mm model, source attempt/generation/cloud seed and half-Moon phase. C viewed visibly changing cloud veil/cells and retained Moon/header/footer. Exact motion-policy, cloud-generator and paint region equality permits narrow historical preservation reuse; the cloud hash is never used as motion proof. Final public normal1x Moon/replacement/geometry qualification remains separately bound to this exact delivered runtime. The new fixed-clock blocked-font fixtures qualify the input/consumer correction and readable composition, without claiming new optics, all-phase Moon, normal-live M0, real storm/coverage or prayer-provider zero-axis availability.\n\n';
 native+='The [V1 harness failure](workers/C/browser14-chromium/results.json) is preserved: CSP string evaluation and unseeded `local=1` coarse detection stopped before consumer proof. [V2 preparation disclosure](workers/C/browser-fixture-preparation-v2.json) uses direct function polling and explicit fixed-site hash mode, retaining product script-body/source/hook/owner identities and every substantive assertion. Original source script anchors were already compatible; no product function was rewritten. These are fixture corrections, not product repairs.\n\n';
 native+='## Primary reconciliation and publication preconditions\n\nAll mandatory rows are satisfied in the bounded contract. The source repair predates PR42 where attributed; the owner’s allowed model presentation is preserved. No direct observation, calibrated radar mm, live-provider coverage, all-phase art approval or independent prayer-provider support is claimed. Dependencies are satisfied by actual ownership/admission/age/lifetime interfaces and relevant controls; administratively open sibling issues are not blanket blockers.\n\nPrimary must independently approve this issue, publish the supplied receipts/crops under an immutable evidence ref and replace these relative evidence links before posting this proof and manually closing. C executed no external effect.\n\n';
 md=md.slice(0,increment)+native+md.slice(mark);
 fs.writeFileSync(path.join(out,issue+'-comment.md'),md);
 summary.results[issue].verdict=a.verdict;summary.results[issue].counts={satisfied:a.requirementMatrix.length};summary.results[issue].gap=null;
}
// Keep complete OPEN contracts and their precise remaining work; only refresh equivalence wording.
for(const issue of [11,12,13,36]){const p=path.join(out,issue+'-comment.md');let md=fs.readFileSync(p,'utf8');md=md.replaceAll('All six material weather regions match final delivered root bytes:','All eight material regions (six weather regions plus explicit motion policy/cloud generator) match final delivered root bytes:');fs.writeFileSync(p,md);}
summary.results[14].originalBrowserResult='FAIL preserved; incorrect raw-condition oracle separately reconciled, nine exact quantitative-effect/custody predicates true';
summary.results[30].nativeBrowserResult='3/3 PASS,57assertions; actual image/consumer/crops read independently';
summary.followup.historicalSourceEquivalence='Eight exact regions (six weather plus explicit motion policy/cloud generator); historical native current/expiry/retry/motion evidence scoped separately from fresh primary cases.';
summary.followup.sourceBoundBrowserReconciliation={R000E:'browser14-v2-semantic-reconciliation.json',R001E:'browser30-chromium-v2/results.json',pixelReview:'browser-pixel-review.json',browserExecutionByC:false};
summary.totals.verdicts={'CLOSE — SATISFIED':2,'LEAVE OPEN':4};
summary.totals.closable=2;summary.totals.leaveOpen=4;
summary.totals.matrixStatuses={satisfied:idsCount('satisfied'),'validly superseded':idsCount('validly superseded'),unmet:idsCount('unmet'),unverified:idsCount('unverified')};
function idsCount(status){return [11,12,13,14,30,36].reduce((n,issue)=>n+read(issue+'-assessment.json').requirementMatrix.filter(r=>r.status===status).length,0);}
summary.requiredMissingChecks=summary.requiredMissingChecks.filter(r=>![14,30].includes(r.issue));
summary.nextAction='Primary independently review/approve #14 and #30; bind supplied relative receipts/crops to immutable evidence branch before comment/closure. Four OPEN issues retain mandatory implementation/docs/evidence gaps. C publication authority remains none.';
summary.materialFindings=[
 'Actual admission, source/receipt expiry, body/Image deadline, ownership, radar exclusion and valid-zero guards are implemented; most predate PR42 in CP9 prerequisites.',
 'Explicit README unavailable/temporal/bounded-wait requirements keep #11/#12/#13 open. The original #14 documentation finding was overbroad and is withdrawn: README contains no alpha-mm/heavy-radar claim; public DESIGN/source/smoke correctly state supported semantics.',
 'R0024 H5/H8 amendment is applied narrowly: fresh quantitatively supported current model effects are allowed, direct observation is unavailable, model thunder does not grant lightning; original state/source/time/target distinctions survive.',
 'R0024 weatherHeader never reads spatial/horizon/forecast; fixtureC approaching information remains only in QA. That surviving presentation obligation remains unmet.',
 'Concrete eight-region source equivalence permits narrow historical V45 current/expiry/retry/motion reuse. Fresh primary #14/#30 native data and inspected crops fill their input-specific consumer gaps; no blanket old-runtime invalidation or generic smoke false-green.',
 'Original #14 V1 harness failure and V2 raw-condition oracle FAIL remain intact. Offline independent quantitative-effect predicates match exact source/amendment; no valid negative weakened, no native operation replayed, no consumer changed.',
 'Generated root includes builder acceptedElevation insertion, so native/root weather are traced separately; exact final delivered public baseline and recorded client gpt-6.1-sol/max configuration verified.'
];
summary.parentRequests=[
 {status:'AUTHORIZED_AND_EXECUTED',request:'Six existing lightweight Node suites serial;245pass/0fail/4TODO',receipt:'test-receipts.json'},
 {status:'AUTHORIZED_AND_EXECUTED',request:'Four isolated #14/#30 source mutations serial;22GREEN selected assertions,15expected mutant failures,7retained controls',receipt:'mutation-receipts.json'},
 {status:'DEFERRED_BY_PRIMARY_RESOURCE_RULE',request:'Additional #11/#12/#13 mutants',reason:'Independent explicit documentation defect already determines open; original required controls remain unverified, not waived'},
 {status:'PREPARED_BY_C_EXECUTED_BY_PRIMARY_REVIEWED_BY_C',request:'Exact-source native #14/#30 inputs/actualImage/consumer/pixels; V1 failure preserved and V2 interpreted by source/amendment',receipt:'browser-pixel-review.json'},
 {status:'NEEDS_BOUNDED_FUTURE_INCREMENT',request:'Remaining #11/#12/#13/#36 contract gaps',reason:'See each complete OPEN matrix; #12 browser modes are prepared but not executed while independent README gap determines disposition'}
];
save('summary.json',summary);
save('followup-reconciliation.json',{schema:'rlgwo-C-final-bounded-reconciliation-v1',target:SHA,results:summary.results,totals:summary.totals,
 receipts:{mutation:'workers/C/mutation-receipts.json',sourceEquivalence:'workers/C/historical-source-equivalence.json',R000E:'workers/C/browser14-v2-semantic-reconciliation.json',R001E:'workers/C/browser30-chromium-v2/results.json',pixels:'workers/C/browser-pixel-review.json',config:'workers/C/config-confirmation.json'},
 primaryApproval:'PENDING INDIVIDUAL INDEPENDENT REVIEW',publication:'NONE BY C',productionMutation:false,browserLaunchByC:false});
const needed=['mutation-receipts.json','run-isolated-mutations.cjs','historical-source-equivalence.json','browser14-v2-semantic-reconciliation.json','reconcile-browser14-oracle.cjs','browser-pixel-review.json','config-confirmation.json','browser-fixture-preparation.json','browser-fixture-preparation-v2.json','run_weather_browser.py','run_weather_browser_v2.py','browser-fixtures/widget-fixture.html','browser-fixtures/widget-fixture-v2.html','browser14-chromium/results.json','browser14-chromium-v2/results.json','browser30-chromium-v2/results.json',...pixels.map(p=>p.path.slice('workers/C/'.length)),...[11,12,13,14,30,36].flatMap(i=>[i+'-assessment.json',i+'-comment.md'])];
save('evidence-publication-map.json',{schema:'rlgwo-C-relative-evidence-publication-map-v1',target:SHA,
 sourceRef:SHA,evidenceRef:'PENDING_PRIMARY_IMMUTABLE_EVIDENCE_BRANCH',effectAuthority:'Primary alone; no effects performed by C',
 files:needed.map(relative=>{const b=fs.readFileSync(path.join(out,relative));return {relativePath:'workers/C/'+relative,sha256:sha(b),bytes:b.length};}),
 exclude:'No need to publish whole isolated mutated product copies, machine fonts, memory/session files or private profile state. Exact mutation patches/TAP receipts and pinned source make the control reconstructible.'});
console.log(JSON.stringify({results:summary.results,totals:summary.totals},null,2));
