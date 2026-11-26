'use strict';
// Synthetic browser/namespace/clock/measurement doubles only. These controls
// replay real retained files through the production entry; no browser is started.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{createRequire}=require('node:module');
const {spawnSync}=require('node:child_process');
const S=require('./firefox_policy_source.cjs'),I=require('./r003f_preconnect_input.cjs');
const M=require('./r003f_preconnect_materialize.cjs'),iso=require('../r0033_isolation.cjs');
const ROOT=path.resolve(__dirname,'../../..'),ENTRY=path.join(__dirname,'r003f_diagnostic_replay.cjs');
const PIN='82c2d9874a4ac5a7f14d8d66b2c132be1ac3ec2fc0d5d41b476c72ea648c6dde';
const MATERIAL='c8c26bfdff9f20b38a5ece423db2759fc96339ca9d68cf2c68f7893d36930290';
if(process.argv[2]==='--replay-child'){
 // An actual child with no Node flags retains the leaf's injection guard.
 // Only its host snapshot is synthetic; all original file validation executes.
 const payload=JSON.parse(fs.readFileSync(0,'utf8')),readIsolation=S.readIsolation,readFile=fs.readFileSync;
 S.readIsolation=file=>readIsolation(file,payload.host);
 fs.readFileSync=(file,...rest)=>file===0?JSON.stringify(payload.x):readFile(file,...rest);
 require(ENTRY);process.exit(process.exitCode||0);
}
const {PNG}=require('pngjs');
const clone=value=>structuredClone(value),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function write(p,value){fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,Buffer.isBuffer(value)||typeof value==='string'?value:JSON.stringify(value));return p;}
function helpers(name,names){
 const file=path.join(__dirname,name),local=createRequire(file);
 // Read unchanged fixture functions without registering or executing leaf tests.
 const req=id=>id==='node:test'?()=>{}:local(id);
 return new Function('require','__dirname','__filename',fs.readFileSync(file,'utf8')+'\nreturn {'+names.join(',')+'};')(req,__dirname,file);
}
const FF=helpers('firefox_policy_controls.cjs',['fakeObservation','host','isolation']);
const UI=helpers('r003f_harness_controls.cjs',['state','receipt']);
function scope(mode){return {diagnosticMode:mode,
 nativeQualification:mode==='firefox-policy'?'MANAGED_POLICY_DIAGNOSTIC_ONLY':'ALTERED_INPUT_DIAGNOSTIC_ONLY',
 nativeProductAcceptance:'NOT_EVALUATED',humanAcceptance:'OUTSTANDING',originalFailedObservation:'UNCHANGED',
 boundaryEngine:'chromium',
 timingClass:mode==='firefox-policy'?'instrumented-managed-policy-dwell':'instrumented-altered-document-input'};}
function boundary(task){
 const file=path.join(task,'capture/isolation/diagnostic/receipt.json'),body=FF.isolation(),host={...FF.host(),pid:process.pid};
 write(file,body);write(path.join(path.dirname(file),'browser.json'),body.browserControl);
 write(path.join(path.dirname(file),'browser.stdout'),'synthetic boundary stdout\n');write(path.join(path.dirname(file),'browser.stderr'),'');
 return {file,body,host,admission:S.readIsolation(file,host)};
}
function common(task,mode,runtime,b){
 const output=mode==='firefox-policy'?path.join(task,'capture/firefox-policy'):path.join(task,'capture/lanes/r003f-webkit-preconnect-input');
 const entryProcess=write(path.join(task,'capture/lanes/entry-process.json'),{synthetic:'explicit subprocess completion double'});
 return {mode,task,here:__dirname,runtime,firefoxPins:PIN,isolation:b.file,output,entryProcess,
  file:path.join(output,mode==='firefox-policy'?'entry-result.json':'summary.json'),
  protocol:'R003F/diagnostic-final-intake/1',status:mode==='firefox-policy'?'OBSERVED_FIREFOX_POLICY':'OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC',
  scope:scope(mode),sourceAdmission:{synthetic:'explicit prior source admission double'}};
}
function replay(f){
 const env={...process.env,SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT:f.x.isolation,NODE_PATH:f.x.runtime.modules,
  PLAYWRIGHT_BROWSERS_PATH:path.join(f.x.task,'node-browsers')};
 const result=spawnSync(process.execPath,[__filename,'--replay-child'],
  {input:JSON.stringify({x:f.x,host:f.b.host}),env,encoding:'utf8',timeout:10000});
 assert.equal(result.error,undefined);assert.equal(result.signal,null);
 return {code:result.status,stdout:result.stdout,stderr:result.stderr,body:result.stdout?JSON.parse(result.stdout):null};
}
async function firefox(t){
 const f=FF.fakeObservation(t),b=boundary(f.f.task);f.admission.source=S.packet(PIN);f.admission.isolation=b.admission;
 const observed=await f.run();assert.equal(observed.exitCode,0,'synthetic leaf fixture must first pass its unchanged predicate');
 const x=common(f.f.task,'firefox-policy',f.f.runtime,b),options={task:x.task,out:x.output,isolation:x.isolation,'pins-sha256':PIN};
 x.argv=[process.execPath,path.join(__dirname,'firefox_policy_probe.cjs'),...Object.entries(options).flatMap(([k,v])=>['--'+k,v])];
 x.source={source:f.admission.source,acquired:f.admission.acquired};
 for(const name of ['stdout','stderr'])write(path.join(x.output,'child.'+name),'synthetic actual-byte '+name+'\n');
 const child={protocol:'firefox-policy-child-process/1',argv:[x.argv[0],x.argv[1],'--internal-child',...x.argv.slice(2)],
  cwd:__dirname,pid:process.pid,timeoutSeconds:270,returncode:0,signal:null,timedOut:false,elapsedSeconds:60,
  groupTerminationRequested:false,error:null,stdout:S.record(path.join(x.output,'child.stdout')),stderr:S.record(path.join(x.output,'child.stderr'))};
 write(path.join(x.output,'process.json'),child);
 write(path.join(x.output,'entry-input.json'),{protocol:'firefox-policy-entry-input/1',options,admission:f.admission,budget:S.BUDGET});
 const entry={protocol:'firefox-policy-entry/1',status:'OBSERVED_FIREFOX_POLICY',exitCode:0,stopAll:false,
  intakeError:null,source:f.admission.source,nativeProductAcceptance:'NOT_EVALUATED',originalFailedObservation:'UNCHANGED'};
 const refresh=()=>{entry.process=S.record(path.join(x.output,'process.json'));entry.report=S.record(path.join(x.output,'result.json'));write(x.file,entry);};refresh();
 return {x,b,entry,child,body:observed.report,refresh,save(){write(path.join(x.output,'result.json'),this.body);refresh();}};
}
async function webkit(t){
 const task=fs.mkdtempSync(path.join(os.tmpdir(),'r003f-central-webkit-'));t.after(()=>fs.rmSync(task,{recursive:true,force:true}));
 const b=boundary(task),runtime={node:process.execPath,pngjs:require.resolve('pngjs'),modules:'/synthetic/packages',engine:'webkit'};
 const x=common(task,'preconnect-input',runtime,b);fs.mkdirSync(x.output,{recursive:true});
 x.sourceRoot=path.join(task,'source');x.runtimeRoot=ROOT;x.materialization=MATERIAL;
 const materialization=M.materialize({source:ROOT,runtime:ROOT,out:x.sourceRoot});assert.equal(S.record(path.join(x.sourceRoot,'materialization.json')).sha256,MATERIAL);
 const outputs=Object.fromEntries(materialization.outputFiles.map(r=>[r.path,r.sha256]));
 const harness={protocol:'R003F/preconnect-input-harness/1',kind:'two exact preconnect spans omitted from served index before parsing',
  materializationSha256:MATERIAL,driverSha256:outputs['tools/qa/r003f_owner_baseline.cjs'],captureHelperSha256:outputs['tools/qa/r003f_capture.cjs'],
  uiHelperSha256:outputs['tools/qa/hosted-native/r003f_ui.cjs'],inputHelperSha256:outputs['tools/qa/hosted-native/r003f_preconnect_input.cjs']};
 x.source={source:S.packet(PIN),materialization:I.admitClosure(x.sourceRoot,MATERIAL),harness};
 const input=I.createInput({root:ROOT,out:x.output}),url='http://127.0.0.1:12345/index.html';
 for(let n=0;n<2;n++){const raw=input.indexFor('B0');await input.recordResponse({url:()=>url,status:()=>200,headers:()=>({'content-type':'text/html'}),body:async()=>raw},url);}
 input.assertComplete();
 const ledger=iso.newLedger();ledger.requests.push({n:0,url:'https://api.aladhan.com/v1/timings',host:'api.aladhan.com',type:'fetch',action:'fulfill',why:'provider-fixture'});ledger.fulfilled=1;
 write(path.join(x.output,'network.jsonl'),ledger.requests.map(r=>JSON.stringify(r)).join('\n')+'\n');
 const png=new PNG({width:325,height:530});for(let i=3;i<png.data.length;i+=4)png.data[i]=255;
 const bytes=PNG.sync.write(png),captures={};
 for(const tag of ['offset','b0','b0-repeat','reference']){
  const state={...UI.state(),disc:{cx:160,cy:160,r:40},weatherFixtureReads:1};
  if(tag==='offset'){state.nativeFraction=.01;state.acceptedFraction=.0101;}if(tag==='reference')state.profile='unboosted-v5-01';
  captures[tag]={state,sha256:S.sha(bytes),lightVerdict:'PASS',nativeUiAfter:UI.receipt()};write(path.join(x.output,tag+'.png'),bytes);
 }
 const metrics={referenceP95:1,litPixels:1,darkPixels:1,maskOverlapPixels:0,deltaLitSkyL:0,deltaPhysicalCandidateL:0};
 const body={protocol:'R003F/P1/B0-preconnect-input/1',status:x.status,originalRecipeStatus:'MEASURED',qualification:'ALTERED_INPUT_DIAGNOSTIC_ONLY',
  nativeAcceptance:'NOT_EVALUATED',humanAcceptance:'OUTSTANDING',engine:'webkit',dpr:1,harness,indexSha256:I.ORIGINAL_SHA,
  epoch:'2026-11-15T09:42:00.000Z',zone:'America/New_York',hash:'#lat=28.54&lon=-81.38&label=Orlando&method=2&tz=America%2FNew_York&seed=1&qa=1',
  servedDocument:input.evidence,isolation:iso.verdict(ledger,[]),captures,metrics,repeatMetrics:clone(metrics),repeatEnvelope:{changedPixels:0,outside106R:0,maxChannelCode:0}};
 write(x.file,body);return {x,b,body,save(){write(x.file,this.body);}};
}

test('normal tracked final entry preserves Firefox no-executable-injection preflight',()=>{
 const source=fs.readFileSync(path.join(__dirname,'r003f_diagnostics.py'),'utf8');
 assert.ok(source.includes("[runtime['node'],str(NODE_FINAL_PATH)]"));assert.ok(!source.includes("'-e',NODE_FINAL"));
 assert.ok(fs.readFileSync(path.join(__dirname,'firefox_policy_probe.cjs'),'utf8').includes('process.execArgv.length===0'));
});
test('complete explicit synthetic Firefox retained bytes replay as diagnostic only',async t=>{
 const f=await firefox(t),r=replay(f);assert.equal(r.code,0,r.stderr);assert.equal(r.body.status,'OBSERVED_FIREFOX_POLICY');
 assert.equal(r.body.observed.historicalFirstStartup,'NOT_ESTABLISHED');assert.equal(r.body.nativeProductAcceptance,'NOT_EVALUATED');
});
for(const [label,mutate] of [
 ['short child completion',f=>{f.child.elapsedSeconds=59;write(path.join(f.x.output,'process.json'),f.child);f.refresh();}],
 ['boolean child zero',f=>{f.child.returncode=false;write(path.join(f.x.output,'process.json'),f.child);f.refresh();}],
 ['foreign child executable',f=>{f.child.argv[0]='/synthetic/untrusted-node';write(path.join(f.x.output,'process.json'),f.child);f.refresh();}],
 ['child timeout',f=>{f.child.timedOut=true;write(path.join(f.x.output,'process.json'),f.child);f.refresh();}],
 ['changed child stream',f=>fs.appendFileSync(path.join(f.x.output,'child.stdout'),'drift')],
 ['changed policy file',f=>fs.appendFileSync(f.body.policy.policy.path,' ')],
 ['missing policy DOM bytes',f=>fs.unlinkSync(path.join(f.x.output,'initial-policy.json'))],
 ['coherent false effective policy',f=>{f.body.initial.dom.activeRows[0][1]='false';write(path.join(f.x.output,'initial-policy.json'),f.body.initial);f.save();}],
 ['short ordinary-clock dwell',f=>{f.body.dwell.endedNs='1';f.save();}],
 ['late lifecycle fault',f=>{f.body.lifecycle[2].faults.push({event:'page-crash'});f.save();}],
 ['incomplete process census',f=>{f.body.processCensuses.final.readFailures.push({code:'EACCES'});write(path.join(f.x.output,'process-census-final.json'),f.body.processCensuses.final);f.save();}],
 ['foreign native acceptance',f=>{f.body.nativeProductAcceptance='PASS';f.save();}],
 ['invented historical startup',f=>{f.body.historicalFirstStartup='PROVEN';f.save();}],
 ['copied source identity',f=>{f.x.source.source={synthetic:'foreign source record'};}],
 ['symlinked retained report',f=>{const p=path.join(f.x.output,'result.json');fs.renameSync(p,p+'.real');fs.symlinkSync(p+'.real',p);}],
])test('Firefox replay refuses '+label,async t=>{const f=await firefox(t);mutate(f);const r=replay(f);assert.equal(r.code,2,r.stderr);assert.equal(r.stdout,'');});
test('Firefox retained original proxy refusal remains isolation failure',async t=>{
 const f=await firefox(t);f.body.ledger.proxyRefused.push({target:'synthetic.invalid:443'});f.body.network=iso.verdict(f.body.ledger,f.body.nodeGuard.refused);
 write(path.join(f.x.output,'network.json'),{ledger:f.body.ledger,nodeGuard:f.body.nodeGuard,verdict:f.body.network});f.save();assert.equal(replay(f).code,86);
});
test('current namespace mismatch remains isolation failure',async t=>{const f=await firefox(t);f.b.host.netns='net:[999]';assert.equal(replay(f).code,86);});
test('complete explicit synthetic WebKit bytes retain altered-input-only qualification',async t=>{
 const f=await webkit(t),r=replay(f);assert.equal(r.code,0,r.stderr);assert.equal(r.body.status,'OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC');
 assert.equal(r.body.nativeQualification,'ALTERED_INPUT_DIAGNOSTIC_ONLY');assert.match(r.body.observed.measurementScope,/full UI mask is not retained/);
});
for(const [label,mutate] of [
 ['original success alias',f=>{f.body.status='PASS';f.save();}],
 ['foreign engine',f=>{f.body.engine='chromium';f.save();}],
 ['foreign native acceptance',f=>{f.body.nativeAcceptance='PASS';f.save();}],
 ['missing raw document',f=>fs.unlinkSync(path.join(f.x.output,f.body.servedDocument.responses[0].body.path))],
 ['changed raw document',f=>fs.appendFileSync(path.join(f.x.output,f.body.servedDocument.responses[0].body.path),' ')],
 ['missing document member',f=>{f.body.servedDocument.responses.pop();f.save();}],
 ['changed derived guard',f=>fs.appendFileSync(path.join(f.x.sourceRoot,'tools/qa/r0033_isolation.cjs'),' ')],
 ['undeclared derived member',f=>write(path.join(f.x.sourceRoot,'unexpected.txt'),'drift')],
 ['changed original runtime index',f=>{f.x.runtimeRoot=path.join(f.x.task,'changed-runtime');write(path.join(f.x.runtimeRoot,'index.html'),Buffer.concat([fs.readFileSync(path.join(ROOT,'index.html')),Buffer.from(' ')]));}],
 ['missing raw capture',f=>fs.unlinkSync(path.join(f.x.output,'reference.png'))],
 ['changed raw capture',f=>fs.appendFileSync(path.join(f.x.output,'b0.png'),'drift')],
 ['coherently rehashed wrong capture dimensions',f=>{const bytes=PNG.sync.write(new PNG({width:1,height:1}));write(path.join(f.x.output,'b0.png'),bytes);f.body.captures.b0.sha256=S.sha(bytes);f.save();}],
 ['coherently rehashed repeat drift',f=>{const p=path.join(f.x.output,'b0-repeat.png'),png=PNG.sync.read(fs.readFileSync(p));png.data[0]=25;const bytes=PNG.sync.write(png);write(p,bytes);f.body.captures['b0-repeat'].sha256=S.sha(bytes);f.save();}],
 ['incomplete native UI',f=>{f.body.captures.b0.nativeUiAfter.status='INCOMPLETE';f.save();}],
 ['incomplete original measurement',f=>{f.body.metrics.litPixels=0;f.save();}],
 ['foreign owner scene',f=>{f.body.captures.b0.state.profile='foreign';f.save();}],
 ['absent weather fixture',f=>{f.body.captures.offset.state.weatherFixtureReads=0;f.body.captures.b0.state.weatherFixtureReads=0;f.save();}],
 ['changed retained request census',f=>write(path.join(f.x.output,'network.jsonl'),'')],
])test('WebKit replay refuses '+label,async t=>{const f=await webkit(t);mutate(f);const r=replay(f);assert.equal(r.code,2,r.stderr);assert.equal(r.stdout,'');});
test('WebKit original calendar-light fault stays Andon',async t=>{const f=await webkit(t);f.body.captures.b0.state.light.beam=1;f.save();assert.equal(replay(f).code,4);});
test('WebKit original strict refusal stays isolation failure',async t=>{const f=await webkit(t);f.body.isolation.refusedAtProxy=1;f.save();assert.equal(replay(f).code,86);});
test('WebKit raw off-loopback continuation stays isolation failure',async t=>{
 const f=await webkit(t);write(path.join(f.x.output,'network.jsonl'),JSON.stringify({n:0,action:'continue',host:'synthetic.invalid'})+'\n');assert.equal(replay(f).code,86);
});
