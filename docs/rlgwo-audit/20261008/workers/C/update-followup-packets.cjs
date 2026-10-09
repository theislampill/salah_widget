'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const out=__dirname,audit=path.dirname(path.dirname(out));
const load=name=>JSON.parse(fs.readFileSync(path.join(out,name),'utf8'));
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const save=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n');
const SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be';
const blob='https://github.com/theislampill/salah_widget/blob/'+SHA+'/';
const mutation=load('mutation-receipts.json'),reuse=load('historical-source-equivalence.json');
const release=JSON.parse(fs.readFileSync(path.join(audit,'release.json'),'utf8'));
const settingsFile=path.join(audit,'reviewer-model-settings.json'),settings=JSON.parse(fs.readFileSync(settingsFile,'utf8'));
const session=settings.sessions.find(s=>s.session.agent_path==='/root/rlgwo_c');
if(!session||session.turnConfigurations.some(c=>c.model!=='gpt-6.1-sol'||c.effort!=='max'))throw Error('Effective recorded client configuration mismatch');
if(release.status!=='DELIVERED_VERIFIED'||release.AUDIT_SHA!==SHA)throw Error('Public delivery baseline mismatch');
const config=load('config-confirmation.json');
config.effective={model:'gpt-6.1-sol',reasoningEffort:'max',confirmation:'CONFIRMED RECORDED CLIENT TURN CONFIGURATION',
 basis:'Supported spawn configuration and recorded local turn_context; not independent hardware/backend attestation',
 source:'reviewer-model-settings.json',sourceSha256:hash(fs.readFileSync(settingsFile)),agentPath:'/root/rlgwo_c',
 sessionId:session.session.id,turnIds:session.turnConfigurations.map(c=>c.turn_id)};
config.nextAction='Requested model and max effort confirmed at recorded client/session level; no further model lookup needed.';
save('config-confirmation.json',config);
const summary=load('summary.json');
const ids=[11,12,13,14,30,36],counts={};
const publicFirefox=JSON.parse(fs.readFileSync(path.join(audit,'public-firefox/root-iframe-cold/results.json'),'utf8'));
const live=publicFirefox.final.weather;
const publicBaseline={status:release.status,verifiedAt:release.verifiedAt,publicBrowserCases:release.publicBrowserCases,
 target:release.AUDIT_SHA,runtime:release.runtime,releaseSha256:hash(fs.readFileSync(path.join(audit,'release.json'))),
 exactPublicFirefox:{file:'public-firefox/root-iframe-cold/results.json',sha256:hash(fs.readFileSync(path.join(audit,'public-firefox/root-iframe-cold/results.json'))),
 status:publicFirefox.status,rawCode:live.rawCode,source:live.currentWeatherSource,model:live.model,visualPermissions:live.visualPermissions,
 directPresent:live.present,observedPresent:live.observedPresent,finalDataFx:live.finalDataFx,rawForecastCode:live.rawForecastCode},
 limits:'16 public cases establish delivered identity, ordinary1x entry and scoped terrain/replacement/geometry. They do not imply weather transport-negative, zero-axis or combined0dBZ proof. Current provider record is time-specific model estimate, not the owner historical site/incident.'};
const ep=(file,start,end)=>({file,start,end,url:blob+file+'#L'+start+'-L'+end});
const reuseEvidence={kind:'HISTORICAL_EXECUTED_BROWSER_REUSED_WITH_FRESH_SOURCE_EQUIVALENCE',receipt:'historical-source-equivalence.json',
 sha256:hash(fs.readFileSync(path.join(out,'historical-source-equivalence.json'))),
 publicBasis:ep('docs/real-sky/evidence/startup-cloud-20261007/final-v49/QUALIFICATION.json',15145,15215),
 oldRuntime:reuse.retainedBrowser.runtime,oldIndex:reuse.oldSource.sha256,currentIndex:reuse.currentSource.sha256,
 regions:reuse.regions,executedCurrentCases:reuse.retainedBrowser.cases,executedAvailability:reuse.retainedAvailability,
 limits:reuse.gaps};
const marker=id=>'<!-- RLGWO-AUDIT:'+SHA+':'+id+':2026-10-08 -->';
const esc=text=>String(text??'').replace(/\|/g,'\\|').replace(/\r?\n/g,'<br>');
function links(refs){return refs.map(r=>r.url?'['+r.file+(r.start?':'+r.start+'–'+r.end:'')+']('+r.url+')':esc(r.description||r.file||'Inline audit receipt')).join('<br>');}
function rowMarkdown(r){return '| '+r.id+' | '+esc(r.obligation)+' | '+links([...r.authoredOwner,...r.deliveredConsumer])+' | '+esc(r.discriminator)+'; expected: '+esc(r.expected)+'<br>Observed: '+esc(r.observed)+'<br>'+links(r.evidence)+' | **'+r.status.toUpperCase()+'** |';}
function mutationSection(issue){
 const relevant=mutation.receipts.filter(r=>r.id.startsWith(issue===14?'R000E':'R001E'));
 if(issue===36)return '\nNo further mutation campaign was launched for R0024: the independent surviving presentation obligation remains unmet. The approved current-model effect amendment is preserved.\n';
 if(![14,30].includes(issue))return '\nExtra mutation runs were deliberately deferred after the independent mandatory documentation defect already determined LEAVE OPEN. Existing required mutants remain unverified; no waived expectation or production mutation is implied.\n';
 let md='\nFresh isolated audit mutation proof (product and shared assertions unchanged):\n\n| Mutant / selected source fixture | Expected GREEN / RED | Observed GREEN / RED | TAP SHA-256 GREEN / RED |\n|---|---|---|---|\n';
 for(const g of relevant.filter(r=>r.kind==='green')){const m=relevant.find(r=>r.id===g.id&&r.kind==='mutant');md+='| '+g.id+'; '+esc(g.command.args.join(' '))+' | '+g.expected.pass+' pass; '+m.expected.fail+' fail / '+m.expected.pass+' retained pass | '+g.observed.pass+' pass; '+m.observed.fail+' fail / '+m.observed.pass+' retained pass | `'+g.tapSha256+'` / `'+m.tapSha256+'` |\n';}
 md+='\nEach run used Node v22.16.0 on Windows, serial `--test-concurrency=1`, actual generated source '+summary.rootIndexSha256+' and unchanged `tests/r000c-weather.test.cjs`. `SALAH_WEATHER_SOURCE` alone selected an isolated changed copy for RED, while `SALAH_CONFIG_SOURCE` selected unchanged config. Restored snippets are disclosed here:\n\n';
 for(const m of relevant.filter(r=>r.kind==='mutant'))md+='- '+m.id+': `'+m.mutation.from+'` → `'+m.mutation.to+'`. '+m.discriminator+'.\n';
 return md+'\nThese are expected failing audit copies. They are not product failures, discarded cases, or passing TODOs.\n';
}
const regionMd=reuse.regions.map(r=>'| '+r.id+' | [final '+r.current.startLine+'–'+r.current.endLine+']('+blob+'index.html#L'+r.current.startLine+'-L'+r.current.endLine+') | `'+r.current.sha256+'` | '+(r.equal?'IDENTICAL':'DIFFERENT')+' |').join('\n');
const commonFollowup='\n## Bounded follow-up evidence and corrections\n\nDelivered baseline is **DELIVERED_VERIFIED** at '+release.verifiedAt+', exact target/runtime above, with16 public Chrome/Firefox root/V1 cold/warm direct/iframe cases. This establishes public identity and the stated entry, geometry and terrain/replacement scope; it does not supply the missing input-specific transport/zero-axis proof. Recorded client/session turn contexts confirm reviewer C at **gpt-6.1-sol / max**; this is not independent backend hardware attestation.\n\nFresh retained-source comparison resolves the blanket runtime-mismatch concern: historical V45 root bytes `'+reuse.oldSource.sha256+'` match the executed V45 browser receipt at runtime `'+reuse.retainedBrowser.runtime+'`. Only CRLF→LF normalization was used for these explicit regions; both complete original file hashes remain recorded. All six material weather regions match final delivered root bytes:\n\n| Region | Final source lines | Region SHA-256 | Comparison |\n|---|---|---|---|\n'+regionMd+'\n\nThe [public qualification record]('+blob+'docs/real-sky/evidence/startup-cloud-20261007/final-v49/QUALIFICATION.json#L15145-L15215) and all three [V46→V47]('+blob+'docs/real-sky/evidence/startup-cloud-20261007/final-v49/receipts/v46-v47-reuse.json), [V47→V48]('+blob+'docs/real-sky/evidence/startup-cloud-20261007/final-v49/receipts/v47-v48-reuse.json), [V48→V49]('+blob+'docs/real-sky/evidence/startup-cloud-20261007/final-v49/receipts/v48-v49-reuse.json) retain their identities and limits. The actual executed Chrome148.0.7778.96 current-boundaries fixture contains14 cases: rain2mm has31 visible particles; code63/0mm and code63/missing amount each have0 particles, retained model condition, disclosed uncertainty and no lightning. Those are historical unchanged-weather controls, not new final-runtime screenshots.\n\nThe executed V45 availability sequence uses an actual near-expiry quarter-hour input and real1x elapsed time: unavailable at9.281s with dash/empty temperature/effects off; actual HTTP503 at90.125s was consumed; a subsequent actual native retry recovered rain/header24° at149.266s. It has136 sampled frames over153.937s, all recorded checks true, no page errors and unchanged runtime. Reviewer C viewed initial/expired/recovered crops (frame00000,00008,00135) and found the header/footer readable. Source-equivalent admission/owner/per-use paint paths justify narrow historical reuse. They do not prove all-phase Moon opacity, default M0 or an input absent from the fixture.\n\nFresh public Firefox final consumer readback independently records current WMO'+live.rawCode+', '+live.model.quantity.value+'mm preceding-interval MODEL drizzle, `observedPresent=false`, actual final `data-fx='+live.finalDataFx+'`, model rain permission true and lightning false; direct present adapter remains unavailable. Hourly forecast code'+live.rawForecastCode+' remains separate. The owner historical weather is not reconstructed or contradicted.\n';
for(const issue of ids){
 const name=issue+'-assessment.json',a=load(name);
 a.delivery={status:'DELIVERED_VERIFIED',primaryReported:'Read release.json and 16-case public-browser-summary.json plus actual public Firefox consumer receipt',evidence:publicBaseline,limits:publicBaseline.limits};
 a.reusedEvidence=a.reusedEvidence.filter(r=>r.kind!=='HISTORICAL_EXECUTED_BROWSER_REUSED_WITH_FRESH_SOURCE_EQUIVALENCE');a.reusedEvidence.push(reuseEvidence);
 const freshReuse={kind:'FRESH_SOURCE_EQUIVALENCE_COMPARISON',receipt:'historical-source-equivalence.json',regions:reuse.regions};
 if(Array.isArray(a.freshEvidence))a.freshEvidence.push(freshReuse);else a.freshEvidence.followupSourceEquivalence=freshReuse;
 a.followup={authorizedBy:'Primary bounded mutation/resource and fixture-preparation messages',mutationReceipt:'mutation-receipts.json',browserPreparation:'browser-fixture-preparation-v2.json',
 browserDriver:'run_weather_browser_v2.py',browserExecutionByC:false,originalFailure:'browser14-chromium/results.json (V1 harness failure, retained; not product counterexample)',
 sourceMutation:false,effectiveConfig:config.effective};
 if(issue===11){const r=a.requirementMatrix.find(r=>r.id==='B15');r.status='satisfied';r.observed='Executed V45 actual1x source expiry→consumed HTTP503→new native network retry recovery,136 frames; initial/expired/recovered pixels inspected. All material weather owner/admission/paint regions byte-equivalent to final root; historical reuse separately scoped.';r.evidence.push(reuseEvidence.publicBasis);r.limitations='Historical browser execution plus fresh source comparison; no new browser by C. Not an all-phase Moon/default-M0 claim.';
  a.proposedNextRlgwoIncrement.gap='README temporal/unavailable contract remains unmet. Required hostile metadata and independent mutants remain unverified; actual1x expiry/outage/retry sequence now covered by source-equivalent historical browser evidence.';
  a.proposedNextRlgwoIncrement.steps[2]='Retain and reconcile executed V45 actual-expiry→consumed503→native-network-retry browser evidence with the fresh source equivalence; rerun only affected evidence if semantic source/consumer changes.';
 }
 if(issue===14){
  const r=a.requirementMatrix.find(r=>r.id==='E08');r.status='satisfied';r.observed='Fresh independent accessor mutant fails4/5 actual palette cases (transparent control passes); direct-gate mutant fails3/5 (model2 and rawclear controls pass). Both unchanged-source controls are5/5 GREEN. Exact TAP and isolated-copy hashes retained and quoted in proposed comment.';r.limitations='Node source-executing fixture; not browser pixels; no production/shared-fixture mutation.';
  const d=a.requirementMatrix.find(r=>r.id==='E10');d.status='satisfied';d.observed='Corrected interpretation: original requirement corrects misleading alpha-mm/heavy-radar claims, which README does not contain. DESIGN244–267, actual source sampler/accessor/gate/QA comments and smoke331–335 disclose unsupported radar and model quantity rules. No additional README radar section is mandated.';d.limitations='The initial review added an unsupported blanket README obligation; this follow-up withdraws that finding explicitly.';
  a.proposedNextRlgwoIncrement.gap='Required combined actual0dBZ+model-dry/wet browser acquisition/paint/pixel proof and final primary review remain unverified. No mandatory documentation defect now established for R000E.';
  a.proposedNextRlgwoIncrement.steps=['Execute prepared isolated V2 actual fetchWeather+manifest+HTTP0dBZ Image/canvas dry raw95/0 and fresh wet raw95/2 cases; capture chip/title/data-fx, independent precipitation/lightning permissions and pixels.','Reconcile the preserved GREEN/mutant RED source receipts and relevant geometry/Moon/motion evidence with these input-specific browser results.'];
  a.proposedNextRlgwoIncrement.semanticOwner='Existing src/native/index.html radar/gate/QA semantic owners; only isolated qualification fixtures and evidence reconciliation in this increment, no runtime/docs repair inferred.';
 }
 if(issue===30){const r=a.requirementMatrix.find(r=>r.id==='1E09');r.status='satisfied';r.observed='Fresh independent weather truthiness and radar truthiness copies each fail4/6 actual dispatch/query/Image cases: equator,meridian,bothzero,negativezero fail; tiny-nonzero and ordinary coordinates remain GREEN. Unchanged source is6/6 GREEN for each copy.';r.limitations='Node actual source logic, not zero-axis browser pixels; no production/shared assertion changed.';
  a.proposedNextRlgwoIncrement.gap='Independent weather/radar mutants are now proven. Actual zero-axis native browser admission/header/data-fx and separate HTTP tile/geometry/crop evidence remain unverified.';
  a.proposedNextRlgwoIncrement.steps=a.proposedNextRlgwoIncrement.steps.filter(s=>!s.toLowerCase().includes('mutation'));
  a.proposedNextRlgwoIncrement.steps.unshift('Execute prepared V2 fixed-site browser cases(0,30),(30,0),(0,0); require actual weather+manifest body consumption and correct image tiles before header/data-fx/crop qualification.');
 }
 if([14,30].includes(issue)){
  const relevant=mutation.receipts.filter(r=>r.id.startsWith(issue===14?'R000E':'R001E'));
  a.executedCommands=a.executedCommands.filter(r=>r.receipt!=='mutation-receipts.json');
  a.executedCommands.push(...relevant.map(r=>({...r,execution:'FRESH_ISOLATED_AUDIT_COPY_OR_UNCHANGED_SOURCE_CONTROL',receipt:'mutation-receipts.json'})));
  const n=Array.isArray(a.negativeControls)?a.negativeControls[0]:a.negativeControls;
  n.requiredUnexecutedMutations=[];n.mutationStatus='EXECUTED: independent unchanged-source GREEN and isolated regression RED; product/shared test expectations untouched';n.executedMutations=relevant;
 }
 a.gaps=a.requirementMatrix.filter(r=>r.status==='unmet'||r.status==='unverified').map(r=>({obligation:r.id,status:r.status,gap:r.observed,limitation:r.limitations}));
 counts[issue]=a.requirementMatrix.reduce((c,r)=>(c[r.status]=(c[r.status]||0)+1,c),{});
 a.reviewerReconciliation='C bounded follow-up corrects radar documentation overreach and establishes concrete historical source reuse; individual primary review/publication remains pending. No automatic closure based on aggregate PASS or source-only pixels.';
 save(name,a);
 let comment=fs.readFileSync(path.join(out,issue+'-comment.md'),'utf8');
 comment=comment.replace(/\*\*Recommendation: LEAVE OPEN\.\*\*[^\n]*/, '**Recommendation: LEAVE OPEN.** '+a.proposedNextRlgwoIncrement.gap);
 for(const r of a.requirementMatrix){const lines=comment.split('\n'),i=lines.findIndex(s=>s.startsWith('| '+r.id+' |'));if(i<0)throw Error('Missing comment row '+r.id);lines[i]=rowMarkdown(r);comment=lines.join('\n');}
 const already=comment.indexOf('## Bounded follow-up evidence and corrections');
 const start=already>=0?already:comment.indexOf('## Next RLGWO increment required for closure'),finish=comment.indexOf(marker(a.canonicalId));
 if(start<0||finish<=start)throw Error('Missing next increment/marker');
 let next='## Next RLGWO increment required for closure\n\n**Semantic owner/scope:** '+a.proposedNextRlgwoIncrement.semanticOwner+'\n\n**Preserve completed work:** '+a.proposedNextRlgwoIncrement.preserved+'\n\n';
 next+=a.proposedNextRlgwoIncrement.steps.map((s,i)=>(i+1)+'. '+s).join('\n')+'\n\n';
 const n=Array.isArray(a.negativeControls)?a.negativeControls[0]:a.negativeControls;
 const unexecuted=n.requiredUnexecutedMutations||[];
 if(unexecuted.length)next+='Required original mutations remain unverified (deferred once independent documentation defect determines open):\n\n'+unexecuted.map(s=>'- '+s).join('\n')+'\n\n';
 next+='**Acceptance and closure proof:** '+a.proposedNextRlgwoIncrement.acceptance+' Every binding row must be satisfied or validly superseded; source-equivalence reuse retains original environment/inputs/limits. Primary must reconcile and publish the evidence before manual closure.\n\n**Invariants/non-goals and containment:** '+a.proposedNextRlgwoIncrement.nonGoals+' No new owner amendment inferred, and no production work or GitHub mutation was performed by C.\n\n';
 comment=comment.slice(0,start)+commonFollowup+mutationSection(issue)+'\n'+next+comment.slice(finish);
 comment=comment.replace('Primary reports 139 public runtime/V1 hashes and scoped root Chrome cold/warm normal-1x rollout smoke passed; it explicitly does not supply weather transport-negative proof.','Primary delivery is now DELIVERED_VERIFIED with16 public Chrome/Firefox cases; source-bound transport/input-specific gaps remain independently mapped below.');
 fs.writeFileSync(path.join(out,issue+'-comment.md'),comment);
 summary.results[issue].counts=counts[issue];summary.results[issue].gap=a.proposedNextRlgwoIncrement.gap;
}
summary.delivery={status:'DELIVERED_VERIFIED',evidence:publicBaseline,limits:publicBaseline.limits};
summary.requestedEffectiveConfigStatus=config.effective.confirmation;
summary.followup={mutationControls:4,selectedGreenAssertions:22,expectedMutantFailures:15,retainedPassingMutantControls:7,
 radarDocumentationCorrection:'E10 initial unmet finding withdrawn as overbroad; no README alpha-mm claim exists.',
 historicalSourceEquivalence:'Six material regions identical between exact executed V45 source and final root; 14 current cases and actual1x expiry/503/retry now reused narrowly.',
 requiredBrowserExecution:'V2 driver prepared, static AST and JS parse; not run by C. V1 primary run retained as harness failure, not a runtime defect.',
 receipt:'mutation-receipts.json',sourceEquivalence:'historical-source-equivalence.json',browserPreparation:'browser-fixture-preparation-v2.json'};
summary.requiredMissingChecks=ids.map(issue=>{const a=load(issue+'-assessment.json');return {issue,gaps:a.gaps,preparedBrowser:([12,14,30].includes(issue)?'run_weather_browser_v2.py --issue '+issue:null),disposition:a.verdict};});
summary.nextAction='Primary execute/reconcile prepared input-specific V2 fixtures if useful for disposition; review revised six issue packets individually. No publication/closure by C.';
summary.totals.matrixStatuses=Object.values(counts).reduce((acc,c)=>{for(const[k,v]of Object.entries(c))acc[k]=(acc[k]||0)+v;return acc;},{});
save('summary.json',summary);
save('followup-reconciliation.json',{schema:'rlgwo-C-bounded-followup-v1',target:SHA,changes:summary.followup,results:summary.results,config:config.effective,publication:'NOT APPROVED OR POSTED BY C',browserExecutionByC:false});
console.log(JSON.stringify({updated:ids,counts,effectiveConfig:config.effective.confirmation,baseline:release.status},null,2));
