'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const {EventEmitter}=require('node:events'),{createHash}=require('node:crypto');
const M=require('./r0040_mechanism.cjs'),P=require('./r0040_passive.cjs'),D=require('./r0040_dateonly.cjs');
const B=require('./r0040_mechanism_bracket.cjs'),N=require('./r0040_mechanism_network.cjs'),U=require('./r0040_passive_runtime.cjs'),S=require('./r0040_passive_sampler.cjs');
const driver=path.resolve(__dirname,'../r0040/capture.cjs'),identity=M.mechanismIdentity(driver);
const source=fs.readFileSync(driver),expressions=B.originalExpressions(source),sha=x=>createHash('sha256').update(x).digest('hex');
const clone=x=>JSON.parse(JSON.stringify(x));
const diagnostic=D.diagnosticIdentity(D.transformHelper(fs.readFileSync(path.join(__dirname,'fixtures/r0040-precip-eval-original.txt'))).identity);

function retention(t){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'mechanism-control-'));
  const retain=new M.MechanismRetention(path.join(root,'evidence'),{out:path.join(root,'original'),expected:{utcMs:1000},pins:{},
    diagnostic,passive:identity.passive,mechanism:identity,collectionTimeoutMs:25,networkTimeoutMs:25});
  const before=process.exitCode;t.after(()=>{retain.journal.close();fs.rmSync(root,{recursive:true,force:true});process.exitCode=before;});
  return retain;
}
const {completeData}=require('./r0040_mechanism_fixture.cjs');

test('new identity pins exact reversible seams and the unchanged reviewed passive leaf',()=>{
  assert.equal(identity.operationalDiagnosticExtended,true);assert.equal(identity.originalCallbackBodyUnchanged,true);
  assert.deepEqual(identity.passive,P.passiveIdentity(driver));assert.equal(identity.sources['r0040_passive.cjs'],sha(fs.readFileSync(path.join(__dirname,'r0040_passive.cjs'))));
  assert.deepEqual(M.verifySources(),M.SOURCE_PINS);assert.equal(identity.networkLimits.bytes,2*1024*1024);
});

test('page adapter forwards the original argument and return while extending only the pinned listener callable',async t=>{
  const retain=retention(t),raw=new EventEmitter(),payload={utc:1000,rectRecipe:'[]'},result={returned:true},calls=[];
  raw.evaluate=async(fn,arg)=>{calls.push([fn,arg]);return result;};
  const wrapped=retain.wrapPage(raw),original=vm.runInNewContext('('+expressions.main+')');
  assert.equal(await wrapped.evaluate(original,payload),result);assert.equal(calls[0][1],payload);
  assert.equal(B.reverseMain(calls[0][0].toString()),original.toString());assert.equal(retain.mechanism.mainInstall.status,'INSTALLED');
  const other=()=>42;assert.equal(await wrapped.evaluate(other,payload),result);assert.equal(calls[1][0],other);
  assert.throws(()=>wrapped.evaluate(original,payload),/one original/);
});

test('page adapter retains the exact original rejection object and records its installation failure',async t=>{
  const retain=retention(t),raw=new EventEmitter(),primary=Error('original page evaluate rejected');raw.evaluate=async()=>{throw primary;};
  const wrapped=retain.wrapPage(raw);await assert.rejects(wrapped.evaluate(vm.runInNewContext('('+expressions.main+')'),{}),e=>e===primary);
  assert.equal(retain.mechanism.mainInstall.status,'INCOMPLETE');assert.equal(retain.mechanism.mainInstall.error.message,primary.message);
});

test('CDP adapter leaves ACK promise/listeners and actual original stop response untouched',async t=>{
  const retain=retention(t),calls=[],listeners=[],ack=Promise.resolve({ack:true}),stopResult={result:{value:[{at:1010,phaseMs:12}]}},
    sampler={protocol:'r0040-passive-sampler/1',clockDomain:'isolated-performance',timeOriginMs:1000,limit:4096,rows:[[0,10,11,12]],dropped:0,faults:0};
  retain.mechanismPage={evaluate:async()=>({partialMain:true})};
  const raw={send(method,params){calls.push([method,params]);
    if(method==='Page.screencastFrameAck')return ack;
    if(method==='Page.createIsolatedWorld')return Promise.resolve({executionContextId:9});
    if(method==='Runtime.evaluate')return Promise.resolve(params.expression===STOP?stopResult:
      params.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'?{result:{value:sampler}}:
      params.expression===B.READ_JOIN?{result:{value:{partialJoin:true}}}:{result:{value:true}});
    return Promise.resolve({});},on(name,fn){listeners.push([name,fn]);},detach:async()=>true};
  const cdp=retain.wrapCDP(raw),handler=()=>{};cdp.on('Page.screencastFrame',handler);
  assert.equal(cdp.send('Page.screencastFrameAck',{sessionId:1}),ack);assert.deepEqual(listeners,[['Page.screencastFrame',handler]]);
  await cdp.send('Page.createIsolatedWorld',{worldName:'r0040-native-clock'});
  await cdp.send('Runtime.evaluate',{contextId:9,expression:expressions.isolated,returnByValue:true});
  assert.equal(S.reverseStart(B.reverseIsolated(calls.at(-1)[1].expression)),expressions.isolated);
  await cdp.send('Page.startScreencast');await cdp.send('Page.stopScreencast');
  assert.equal(await cdp.send('Runtime.evaluate',{contextId:9,expression:STOP,returnByValue:true}),stopResult);
  const retained=fs.readFileSync(path.join(retain.journal.directory,'passive-original-stop-1.json'));
  assert.deepEqual(retained,Buffer.from(JSON.stringify(stopResult,null,2)+'\n'));
  assert.deepEqual(retain.mechanism.bracket.main.raw,{partialMain:true});assert.deepEqual(retain.mechanism.bracket.join.raw,{partialJoin:true});
  const stopIndex=calls.findIndex(r=>r[1]?.expression===STOP),joinIndex=calls.findIndex(r=>r[1]?.expression===B.READ_JOIN);assert.ok(joinIndex>stopIndex);
});
const STOP='globalThis.active=false; globalThis.samples';

test('diagnostic extraction failure cannot replace the original stop result or its Buffer',async t=>{
  const retain=retention(t);retain.mechanismPage={evaluate:async()=>{throw Error('main observation failed');}};
  await retain.collectBrackets({context:()=>9,raw:{send:async()=>({result:{value:{preservedJoinPrefix:true}}})}},'after-original-stop');
  assert.equal(retain.mechanism.bracket.main.status,'INCOMPLETE');assert.equal(retain.mechanism.bracket.join.status,'OBSERVED');
  assert.deepEqual(retain.mechanism.bracket.join.raw,{preservedJoinPrefix:true});
});

test('bracket and network completeness remain independent on the same retained failure packet',async()=>{
  const f=await completeData(),networkMissing=clone(f.observation);networkMissing.network.setup.status='INCOMPLETE';
  const first=M.inspectMechanism(networkMissing,identity,f.baseBody,f.passive,f.stop);
  assert.equal(first.status,'INCOMPLETE');assert.equal(first.bracket.status,'OBSERVED');assert.equal(first.network.status,'INCOMPLETE');
  const bracketMissing=clone(f.observation);bracketMissing.bracket=null;
  const second=M.inspectMechanism(bracketMissing,identity,f.baseBody,f.passive,null);
  assert.equal(second.status,'INCOMPLETE');assert.equal(second.bracket.status,'INCOMPLETE');assert.equal(second.network.status,'OBSERVED');
});

test('actual Buffer admission preserves the old full checks and refuses actual exit1 or forged completion',async()=>{
  const f=await completeData(),admit=(receipt=f.receipt,exit=0,stop=f.stop)=>M.admitMechanismReceipt(receipt,f.baseBytes,f.passiveBytes,identity,diagnostic,exit,stop);
  assert.equal(admit().status,'OBSERVED');
  for(const code of [1,86,null,false,'0'])assert.throws(()=>admit(f.receipt,code),/actual mechanism child/);
  assert.throws(()=>admit(f.receipt,0,JSON.parse(f.stop)),/Buffer/);
  const missing=clone(f.receipt);missing.observation.network.rows.pop();assert.throws(()=>admit(missing),/incomplete|inspection/);
  const falseStatus=clone(f.receipt);falseStatus.status='PASS';assert.throws(()=>admit(falseStatus),/receipt/);
  const shortened=clone(f.receipt);shortened.observation.bracket.main.raw.rows.pop();shortened.observation.bracket.join.raw.rows.pop();
  assert.throws(()=>admit(shortened),/incomplete|inspection/);
});

test('current actual nonzero base/passive status cannot be upgraded by complete extra observations',async()=>{
  const f=await completeData(),failed=JSON.parse(f.passiveBytes);failed.exitCode=1;failed.status='FAILED';
  const bytes=Buffer.from(JSON.stringify(failed)),receipt=clone(f.receipt);receipt.passiveAdmission={file:'passive-observation.json',bytes:bytes.length,sha256:sha(bytes)};
  assert.throws(()=>M.admitMechanismReceipt(receipt,f.baseBytes,bytes,identity,diagnostic,0,f.stop),/passive final/);
});

test('finalization retains old failure receipts and independent diagnostic prefix with actual nonzero precedence',t=>{
  const retain=retention(t);retain.finalize(7,()=>{});
  assert.equal(process.exitCode,7);
  const base=JSON.parse(fs.readFileSync(path.join(retain.journal.directory,'final-admission.json'))),
    passive=JSON.parse(fs.readFileSync(path.join(retain.journal.directory,'passive-observation.json'))),
    extra=JSON.parse(fs.readFileSync(path.join(retain.journal.directory,M.ARTIFACT)));
  assert.equal(base.exitCode,7);assert.equal(passive.exitCode,7);assert.equal(extra.exitCode,7);assert.equal(extra.status,'FAILED');
  assert.equal(extra.inspection.bracket.status,'INCOMPLETE');assert.equal(extra.inspection.network.status,'INCOMPLETE');
  const rows=fs.readFileSync(path.join(retain.journal.directory,'events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  assert.equal(rows.at(-2).event,'driver-process-ended');assert.equal(rows.at(-1).event,'passive-terminal-status');
  assert.ok(rows.findIndex(r=>r.event==='mechanism-observation-ended')<rows.findIndex(r=>r.event==='passive-observation-ended'));
});

test('missing current namespace remains a real entry refusal before original imports',()=>{
  const env={...process.env};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
  const run=require('node:child_process').spawnSync(process.execPath,[path.join(__dirname,'r0040_mechanism.cjs'),
    '--driver',driver,'--manifest','/nonexistent','--prepared','/nonexistent','--preparation-process','/nonexistent',
    '--preparation-entry','/nonexistent','--evidence','/nonexistent','--','/nonexistent','/nonexistent','/nonexistent','/nonexistent','chromium','bday','moderate','M1'],
    {env,encoding:'utf8',timeout:5000});
  assert.equal(run.status,1);assert.match(run.stderr,/namespace|isolation/);assert.doesNotMatch(run.stderr,/Cannot find module.*playwright/);
});
