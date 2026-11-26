'use strict';
// Shared retained-byte intake. No browser is launched by this entry.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{isDeepStrictEqual:same}=require('util');
const x=JSON.parse(fs.readFileSync(0,'utf8')),S=require(path.join(x.here,'firefox_policy_source.cjs')),need=S.need;
function matching(p,value){const b=S.read(p);need(same(b,value),'actual retained '+path.basename(p)+' differs');return S.record(p);}
function boundedFile(p){S.safe(p);need(fs.statSync(p).size<=8*1024*1024,'bounded terminal artifact required');return fs.readFileSync(p);}
function isolationFailure(message){const e=Error(message);e.isolation=true;throw e;}
try {
 need(process.execPath===x.runtime.node,'final actual Node differs from acquisition');
 let currentIsolation;
 try {
  need(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT===x.isolation,'current explicit diagnostic namespace binding differs');
  currentIsolation=S.readIsolation(x.isolation);
 } catch(error) { error.isolation=true;throw error; }
 const currentSource=S.packet(x.firefoxPins);
 need(same(currentSource,x.source.source),'final current original source differs');
 const report=S.read(x.file),observed={};
 if(x.mode==='firefox-policy'){
  const P=require(path.join(x.here,'firefox_policy_probe.cjs'));
  const options={task:x.task,out:x.output,isolation:x.isolation,'pins-sha256':x.firefoxPins};
  const current=P.preflight(options),body=S.read(path.join(x.output,'result.json'));
  const child=S.read(path.join(x.output,'process.json')),input=S.read(path.join(x.output,'entry-input.json'));
  need(report.protocol==='firefox-policy-entry/1'&&report.status==='OBSERVED_FIREFOX_POLICY'&&report.exitCode===0&&
   report.stopAll===false&&report.intakeError===null&&report.nativeProductAcceptance==='NOT_EVALUATED'&&
   report.originalFailedObservation==='UNCHANGED','actual Firefox parent result is incomplete or foreign');
  need(same(report.process,S.record(path.join(x.output,'process.json')))&&
   same(report.report,S.record(path.join(x.output,'result.json'))),'actual Firefox child/report bytes differ');
  need(child.protocol==='firefox-policy-child-process/1'&&Number.isInteger(child.returncode)&&child.returncode===0&&
   child.timedOut===false&&child.signal===null&&child.error===null&&child.timeoutSeconds===270&&
   child.cwd===x.here&&Number.isInteger(child.pid)&&child.pid>0&&Number.isFinite(child.elapsedSeconds)&&
   child.elapsedSeconds>=60&&child.elapsedSeconds<=274&&child.groupTerminationRequested===false,
   'actual Firefox child completion, dwell allocation or bound differs');
  need(same(child.argv,[x.runtime.node,path.join(x.here,'firefox_policy_probe.cjs'),'--internal-child',...x.argv.slice(2)]),
   'actual internal Firefox child command differs');
  for(const key of ['stdout','stderr'])need(same(child[key],S.record(path.join(x.output,'child.'+key))), 'actual internal child stream differs');
  need(input.protocol==='firefox-policy-entry-input/1'&&same(input.options,options)&&same(input.budget,S.BUDGET)&&
   same(input.admission.source,current.source)&&same(input.admission.acquired,current.acquired)&&
   same(input.admission.isolation.receipt,current.isolation.receipt),'actual Firefox entry input or admission differs');
  need(same(current.source,report.source)&&same(body.source,current.source)&&same(body.acquired,current.acquired)&&
   same(current.acquired,x.source.acquired)&&same(body.isolation.receipt,currentIsolation.receipt),
   'Firefox current source, acquired population or namespace differs');
  S.validateIsolation(body.isolation.body,body.isolation.host);
  need(body.isolation.host.pid===child.pid,'Firefox child and namespace owner differ');
  S.admitPolicy(current.acquired,body.policy);
  matching(path.join(x.output,'policy-preparation.json'),body.policy);
  matching(path.join(x.output,'initial-policy.json'),body.initial);matching(path.join(x.output,'final-policy.json'),body.final);
  matching(path.join(x.output,'launch-request.json'),body.launch);
  matching(path.join(x.output,'browser-start.json'),{launch:body.launch,processes:body.processes,browserVersion:body.browserVersion});
  for(const key of ['before','started','final'])matching(path.join(x.output,'process-census-'+key+'.json'),body.processCensuses[key]);
  need(S.censusRows(body.processCensuses.before).length===0,'prelaunch installation was not empty');
  const started=S.ownedProcesses(body.processCensuses.started,body.isolation.host,child.pid);
  const final=S.ownedProcesses(body.processCensuses.final,body.isolation.host,child.pid);
  need(same(started,body.processes)&&same(final,body.finalProcesses)&&started.root.pid===final.root.pid&&
   started.root.startTicks===final.root.startTicks,'actual observed Firefox ownership changed');
  need([...started.observed,...final.observed].every(row=>!S.sameLive(row)),'tracked Firefox process is still live');
  const network=S.read(path.join(x.output,'network.json'));
  need(same(network.ledger,body.ledger)&&same(network.nodeGuard,body.nodeGuard),'actual Firefox ledger/Node guard bytes differ');
  const verdict=require(path.join(x.here,'../r0033_isolation.cjs')).verdict(network.ledger,network.nodeGuard.refused);
  if(!verdict.ok)isolationFailure('unchanged strict Firefox ledger refused an operation');
  need(same(verdict,network.verdict)&&same(verdict,body.network),'original strict Firefox verdict differs');
  need(S.resultCode(body)===0&&same(P.outerDisposition(child,body),{status:'OBSERVED_FIREFOX_POLICY',exitCode:0,stopAll:false}),
   'complete original Firefox policy/DOM/dwell/lifecycle predicate failed');
  Object.assign(observed,{entry:S.record(x.file),child:S.record(path.join(x.output,'process.json')),
   report:S.record(path.join(x.output,'result.json')),policy:S.record(body.policy.policy.path),
   network:S.record(path.join(x.output,'network.json')),historicalFirstStartup:'NOT_ESTABLISHED',refinedCapture:'NOT_OBSERVED'});
 }else{
  const I=require(path.join(x.here,'r003f_preconnect_input.cjs'));
  const closure=I.admitClosure(x.sourceRoot,x.materialization);
  need(same(closure,x.source.materialization),'current full WebKit derived closure differs');
  I.deriveIndex(boundedFile(path.join(x.runtimeRoot,'index.html')));
  need(report.protocol==='R003F/P1/B0-preconnect-input/1'&&report.status==='OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC'&&
   report.originalRecipeStatus==='MEASURED'&&report.qualification==='ALTERED_INPUT_DIAGNOSTIC_ONLY'&&
   report.nativeAcceptance==='NOT_EVALUATED'&&report.humanAcceptance==='OUTSTANDING'&&report.engine==='webkit'&&
   Number.isInteger(report.dpr)&&report.dpr===1&&!report.error&&same(report.harness,x.source.harness)&&
   report.indexSha256===I.ORIGINAL_SHA,'foreign or incomplete original WebKit diagnostic report');
  const documents=I.admitEvidence(report.servedDocument,x.output);
  const iso=require(path.join(x.sourceRoot,'tools/qa/r0033_isolation.cjs')),network=report.isolation;
  need(network&&network.ok===true&&same(network.escapes,[]),'original strict WebKit isolation is incomplete');
  for(const key of ['seen','continued','fulfilled','aborted','websockets','fileUnrouted','allowedOffLoopback','refusedAtProxy','refusedByNodeGuard'])
   need(Number.isInteger(network[key])&&network[key]>=0,'original strict WebKit verdict count differs');
  if(network.allowedOffLoopback||network.refusedAtProxy||network.refusedByNodeGuard)isolationFailure('original WebKit proxy or Node refusal remains a failure');
  const requests=boundedFile(path.join(x.output,'network.jsonl')).toString('utf8').split('\n').filter(Boolean).map(JSON.parse);
  for(let n=0;n<requests.length;n++){
   const row=requests[n];need(row.n===n&&['continue','fulfill','abort'].includes(row.action),'original retained request ordering differs');
   if(row.action==='continue'&&row.host&&!iso.isLoopbackHost(row.host))isolationFailure('retained WebKit request continued off loopback');
  }
  need(network.seen===requests.length&&['continue','fulfill','abort'].every((k,i)=>
   network[['continued','fulfilled','aborted'][i]]===requests.filter(r=>r.action===k).length)&&
   same(network.abortedHosts,[...new Set(requests.filter(r=>r.action==='abort'&&r.host).map(r=>r.host))]),
   'original retained request census differs');
  need(requests.some(r=>r.action==='fulfill'&&r.host==='api.aladhan.com'),'original prayer fixture consumption missing');
  const p1=require(path.join(x.sourceRoot,'tools/qa/r003f_p1.cjs')),ui=require(path.join(x.sourceRoot,'tools/qa/hosted-native/r003f_ui.cjs'));
  const {PNG}=require(x.runtime.pngjs),tags=['offset','b0','b0-repeat','reference'],captures=report.captures,pixels={};
  need(captures&&same(Object.keys(captures).sort(),[...tags].sort()),'complete original capture population required');
  need(report.epoch==='2026-11-15T09:42:00.000Z'&&report.zone==='America/New_York'&&
   report.hash==='#lat=28.54&lon=-81.38&label=Orlando&method=2&tz=America%2FNew_York&seed=1&qa=1','original fixed scene differs');
  for(const tag of tags){
   const row=captures[tag],state=row.state,raw=boundedFile(path.join(x.output,tag+'.png'));
   need(S.sha(raw)===row.sha256&&raw.length>=24&&raw.readUInt32BE(16)===325&&raw.readUInt32BE(20)===530,'actual retained PNG identity or dimensions differ');
   const png=PNG.sync.read(raw,{checkCRC:true});need(png.width===325&&png.height===530,'decoded original card dimensions differ');pixels[tag]=png.data;
   const light=p1.calendarLightVerdict(state);if(light==='FAIL'){const e=Error('original calendar-light Andon');e.andon=true;throw e;}
   need(light==='PASS'&&row.lightVerdict===light,'original calendar-light observation incomplete');p1.assertOwnerScene(tag,state);
   need(same(state.card,[325,530])&&state.now===report.epoch&&state.motionReduced===true&&state.ready===true&&state.composed===true&&
    state.quality==='empirical-adaptive'&&state.source==='refined-terrain'&&state.weatherCode===0&&state.prayerLoaded===true,'original refined scene predicate differs');
   ui.assertNativeUi(state.nativeUi);ui.assertNativeUi(row.nativeUiAfter);
  }
  need(captures.offset.state.weatherFixtureReads+captures.b0.state.weatherFixtureReads>0,'original weather fixture consumption missing');
  for(const tag of ['offset','b0-repeat','reference'])assert.deepEqual(captures[tag].state.disc,captures.b0.state.disc);
  for(const tag of ['b0-repeat','reference'])assert.equal(captures[tag].state.acceptedFraction,captures.b0.state.acceptedFraction);
  p1.assertOwnerMeasurement(report.metrics);p1.assertOwnerMeasurement(report.repeatMetrics);
  const repeat=p1.compareCards(1,captures.b0.state.disc,pixels.b0,pixels['b0-repeat']);
  need(same(report.repeatEnvelope,{changedPixels:repeat.changedPixels,outside106R:repeat.outside.length,maxChannelCode:repeat.maxChannelCode}),
   'actual B0 repeat envelope differs');
  // The unchanged report does not retain the full UI mask or proxy ledger.
  // Do not synthesize them or advertise complete-eight matrix verification.
  Object.assign(observed,{report:S.record(x.file),documents,network:S.record(path.join(x.output,'network.jsonl')),
   captures:Object.fromEntries(tags.map(tag=>[tag,S.record(path.join(x.output,tag+'.png'))])),originalRecipeStatus:'MEASURED',
   measurementScope:'Original recorded completeness predicates and raw capture identity; full UI mask is not retained.'});
 }
 process.stdout.write(JSON.stringify({protocol:x.protocol,status:x.status,...x.scope,
  sourceAdmission:x.sourceAdmission,entryProcess:S.record(x.entryProcess),isolation:currentIsolation.receipt,observed}));
}catch(error){process.stderr.write(JSON.stringify({error:String(error.message),isolation:error.isolation===true,andon:error.andon===true})+'\n');
 process.exitCode=error.isolation?86:error.andon?4:2;}
