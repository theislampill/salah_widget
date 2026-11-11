#!/usr/bin/env node
'use strict';
// Boundary controls only: the real BiDi owner, startSession, closeOwnedSession,
// first-phase collect and phase-2 finishOwnedCase run against simulated external
// Windows/process/page/socket boundaries. No browser execution or qualification.
// Removing either caller's join/final cut, handler ownership, or frozen receipt
// must fail an observable assertion below; no source-text pass assertions.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const os=require('node:os'),vm=require('node:vm'),crypto=require('node:crypto');
const {EventEmitter}=require('node:events');
const {performance:realPerformance}=require('node:perf_hooks');
const baseFile=process.env.R0017_FINALIZATION_BASE_SOURCE||path.join(__dirname,'r0017-windows-proof.cjs');
const phase2File=process.env.R0017_FINALIZATION_PHASE2_SOURCE||path.join(__dirname,'r0017-phase2-controls.cjs');
const baseSource=fs.readFileSync(baseFile,'utf8'),phase2Source=fs.readFileSync(phase2File,'utf8');
const prefix=baseSource.slice('#!/usr/bin/env node\n'.length,baseSource.indexOf('async function main(){'));
const root=path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const declared=JSON.parse(fs.readFileSync(path.join(root,'tests/smoke.html'),'utf8').match(/const CASES=(\[[\s\S]*?\n\]);/)[1]);
const evidenceRoot=process.env.R0017_FINALIZATION_TEST_OUT;
if(evidenceRoot)fs.mkdirSync(evidenceRoot,{recursive:true});
const SCALE=20,results=[];
const originalStall='Error: BiDi command deadline: script.evaluate\n    at simulated original observation boundary';
const fourErrors=Array(4).fill('Error: BiDi command deadline: network.continueRequest');
const clone=v=>JSON.parse(JSON.stringify(v));
function healthySnapshot(seed){
 const documentId='00000000-0000-0000-0000-000000000001',sourceSha256='1'.repeat(64),hash='simulated-owned-document';
 const fixture={run:'simulation',attempt:1,hash,mode:'healthy',documentId,sourceSha256};
 return {smoke:{status:'PASS',pass:141,fail:0,skip:0,required:{total:30,executed:30,failed:0,missing:[],cases:declared.map(([name,expected])=>({name,expected,state:'executed',assertions:expected,reason:null}))},fixture:{run:'simulation',attempts:[{attempt:1,hash,fixture}]}},
  viewport:{width:1100,height:900},dpr:1,preference:true,storage:{before:seed,after:seed,entries:[]},children:{preference:true}};
}
async function harness(name,options={}){
 const home=fs.mkdtempSync(path.join(evidenceRoot||os.tmpdir(),'r0017-finalization-'+name+'-'));
 const out=path.join(home,'receipts'),timers=new Set(),sockets=[],traceFailures=[];
 let deleted=false,deletedAt=null,session=null,mutableRow=null,phase2Finish=null,initialCommonCheck=null,clockOffset=0,clockOverride=null,joinDeadline=null;
 const clock={now:()=>clockOverride??(realPerformance.now()*SCALE+clockOffset)};
 function schedule(fn,ms,...args){const id=setTimeout(()=>{timers.delete(id);fn(...args);},ms/SCALE);timers.add(id);return id;}
 function clear(id){timers.delete(id);clearTimeout(id);}
 const delay=ms=>new Promise(resolve=>schedule(resolve,ms));
 const child=new EventEmitter();Object.assign(child,{pid:101,exitCode:null,signalCode:null,kill:()=>{child.exitCode=0;child.emit('exit',0,null);return true;}});
 const driver={ProcessId:101,ParentProcessId:1,Name:'simulated-driver',CreationDate:'2026-11-07T00:00:00.0000000Z'};
 const browser={ProcessId:102,ParentProcessId:101,Name:'simulated-browser',CreationDate:'2026-11-07T00:00:01.0000000Z'};
 class Socket{
  constructor(){this.listeners=new Map();this.sent=[];this.readyState=0;sockets.push(this);queueMicrotask(()=>{this.readyState=1;this.emit('open',{});});}
  addEventListener(type,fn,options){const items=this.listeners.get(type)||[];items.push({fn,once:options?.once===true});this.listeners.set(type,items);}
  emit(type,event){for(const item of [...(this.listeners.get(type)||[])]){if(item.once)this.listeners.set(type,this.listeners.get(type).filter(x=>x!==item));item.fn(event);}}
  message(value){this.emit('message',{data:JSON.stringify(value)});}
  send(encoded){if(this.readyState!==1)throw Error('BiDi closed');const command=JSON.parse(encoded);this.sent.push(command);
   if(command.method==='network.continueRequest'&&String(command.params.request).startsWith('pending-'))return;
   let result={};
   if(command.method==='browsingContext.getTree')result={contexts:[{context:'simulated-owned-top'}]};
   if(command.method==='browsingContext.navigate')result={url:command.params.url,navigation:'simulated-navigation'};
   if(command.method==='browsingContext.captureScreenshot'){
    result={data:Buffer.from('simulated screenshot boundary, not native image evidence').toString('base64')};
    if(options.onScreenshot)options.onScreenshot(api,session,mutableRow);
   }
   if(command.method==='script.evaluate'){
    const expression=command.params.expression;
    let value=expression.includes('window.__r0017Control??null')?{done:true,simulation:true}:
     expression.includes("summary:document.querySelector('#sum')?.textContent??null,cases:")?{done:true,child:null}:healthySnapshot(api.seeds('valid'));
    result={type:'success',realm:'simulated-page-realm',result:{type:'string',value:JSON.stringify(value)}};
   }
   queueMicrotask(()=>this.message({id:command.id,type:'success',result}));
  }
  close(){this.readyState=2;if(!options.neverClose)schedule(()=>this.releaseClose(),options.closeDelayMs??300);}
  releaseClose(){if(this.readyState===3)return;if(options.closeAtDeadlineOffsetMs!==undefined&&joinDeadline!==null)clockOverride=joinDeadline+options.closeAtDeadlineOffsetMs;this.readyState=3;this.emit('close',{code:1006,reason:'simulated delayed close',wasClean:false});}
 }
 const fsBoundary={...fs,rmSync(file,...args){const value=fs.rmSync(file,...args);if(options.afterProfileRemovalAdvanceMs&&String(file).startsWith(home+path.sep+'r0017-'))clockOffset+=options.afterProfileRemovalAdvanceMs;return value;},appendFileSync(file,bytes,...rest){
  if(options.traceFailure&&!traceFailures.length&&file.endsWith('bidi-trace.jsonl')&&String(bytes).includes(options.traceFailureKind?'"kind":"'+options.traceFailureKind+'"':'"stage":"cleanup-finished"')){traceFailures.push('simulated trace write failure at cleanup-finished');throw Error(traceFailures[0]);}
  return fs.appendFileSync(file,bytes,...rest);
 }};
 const localProcess={platform:'win32',argv:['node',baseFile,'--root',root,'--out',out],env:{RUNNER_TEMP:home},versions:process.versions,version:process.version,exitCode:0};
 function boundaryRequire(id){if(id==='node:fs')return fsBoundary;if(id==='node:child_process')return {spawn:()=>child,execFileSync:()=>{throw Error('Unadmitted external process call');}};if(id==='node:timers/promises')return {setTimeout:delay};return require(id);}
 const context={require:boundaryRequire,module:{exports:{}},Buffer,URL,URLSearchParams,AbortSignal,performance:clock,process:localProcess,WebSocket:Socket,setTimeout:schedule,clearTimeout:clear,queueMicrotask,console:{log:()=>{},error:()=>{}},__filename:baseFile,__dirname:path.dirname(baseFile),testBoundary:{
  locate:()=>({binary:'simulated-browser',driver:'simulated-driver',browserSha256:'simulated',driverSha256:'simulated'}),
  processTree:()=>deleted&&clock.now()-deletedAt>=(options.processExitDelayMs||0)?[]:[driver,browser],
  request:async(base,method,route)=>{if(route==='/status')return {ready:true};if(method==='DELETE'){deleted=true;deletedAt=clock.now();return null;}if(method==='POST'&&route==='/session')return {sessionId:'simulated-session',capabilities:{platformName:'windows','goog:processID':102,webSocketUrl:'ws://127.0.0.1:9666/session'}};return {};},
  capture:s=>{session=s;mutableRow=s.row;s.row.simulationOnly=true;s.row.nativeExecutions=0;if(typeof s.bidi.joinClose==='function'){const join=s.bidi.joinClose.bind(s.bidi);s.bidi.joinClose=deadline=>{joinDeadline=deadline;return join(deadline);};}if(options.afterStart)options.afterStart(api,s,s.row);}
 }};
 vm.runInNewContext(prefix+`
 locate=testBoundary.locate;freePort=async()=>9666;processTree=testBoundary.processTree;request=testBoundary.request;
 const actualStartSession=startSession;startSession=async(...args)=>{const s=await actualStartSession(...args);testBoundary.capture(s);return s;};
 source={treeSha256:'simulated-source-tree',files:{'index.html':{sha256:'${'1'.repeat(64)}'}}};declared=${JSON.stringify(declared)};
 module.exports={startSession,collect,checkCommon,result,OUT,ROOT,EXPECTED,PUBLIC,runId,sha,write,record,seeds,SNAPSHOT,PROGRESS,screenshot,operationTimeout,remainingBudgetMs,get source(){return source;},get declared(){return declared;}};`,context,{filename:baseFile});
 const api=context.module.exports;api.result.simulationOnly=true;api.result.nativeExecutions=0;
 const phaseContext={require:boundaryRequire,module:{exports:{}},Buffer,URL,URLSearchParams,performance:clock,process:localProcess,console};
 vm.runInNewContext(phase2Source+'\nmodule.exports.testOnlyFinishOwnedCase=finishOwnedCase;',phaseContext,{filename:phase2File});
 phase2Finish=phaseContext.module.exports.testOnlyFinishOwnedCase;
 function blocked(id){session.bidi.ws.message({method:'network.beforeRequestSent',params:{context:'simulated-owned-child',navigation:null,timestamp:1794089691000,redirectCount:0,isBlocked:true,request:{request:id,url:'https://theislampill.github.io/salah_widget/tests/widget-fixture.html?attempt='+id}}});}
 async function firstPhase(){const ok=await api.collect('chromium','healthy','reduce','valid',false,api.PUBLIC);return read(ok);}
 async function phaseTwo(status='PUBLIC_HEALTHY_PASSED_NOT_CLOSURE',error=null,withControl=false){
  const row={schema:'r0017-finalization-simulation/v1',name:'simulated-phase-two',engine:'chromium',stage:'observation',status,error,checks:{},screenshots:[{sha256:'simulated-existing-screenshot'}],smoke:null};
  const dir=path.join(out,row.name);fs.mkdirSync(dir,{recursive:true});api.result.cases.push(row);
  const s=await api.startSession('chromium','reduce',{width:1100,height:900},1,row,dir,api.PUBLIC);
  api.checkCommon(row,healthySnapshot(api.seeds('valid')),{width:1100,height:900},1,api.seeds('valid'));initialCommonCheck=clone(row.checks);
  if(options.afterCommon)options.afterCommon(api,s,row,blocked,delay);
  const began=clock.now();await phase2Finish(api,row,s,dir,Date.now(),withControl);return {...read(),callerElapsedMs:clock.now()-began};
 }
 function read(ok){const row=api.result.cases[0];return {ok,row:clone(row),mutableRow,stored:JSON.parse(fs.readFileSync(path.join(out,row.name,'result.json'),'utf8')),summary:JSON.parse(fs.readFileSync(path.join(out,'summary.json'),'utf8')).cases[0],frozen:Object.isFrozen(row)&&Object.isFrozen(row.network)&&Object.isFrozen(row.network.interceptErrors),initialCommonCheck};}
 async function afterLate(){for(const socket of sockets)socket.releaseClose();if(options.releaseHandler)options.releaseHandler();await delay(3000);api.write(path.join(out,'summary.json'),api.result);return read();}
 async function dispose(){for(const socket of sockets)socket.releaseClose();if(options.releaseHandler)options.releaseHandler();await Promise.resolve();await Promise.resolve();for(const timer of timers)clearTimeout(timer);timers.clear();if(!evidenceRoot)fs.rmSync(home,{recursive:true,force:true});}
 return {api,firstPhase,phaseTwo,blocked,delay,read,afterLate,dispose,get session(){return session;},get initialCommonCheck(){return initialCommonCheck;},home,clock};
}
async function check(name,fn){let h;try{const detail=await fn(options=>harness(name,options).then(x=>(h=x)));assert.equal(h.read().frozen,true,'final row and its error array must be frozen');results.push({name,passed:true,detail});}catch(e){results.push({name,passed:false,error:String(e.stack||e),observed:h?{...h.read(),mutableRow:undefined}:null});}finally{if(h)await h.dispose();}}
function sameReceipts(x){assert.deepEqual(x.stored,x.summary,'case receipt and summary must contain the identical final cut');assert.deepEqual(x.row,x.stored,'the retained summary case must be the written frozen cut');}
function assertFailed(x){assert(!/PASSED|DIAGNOSTIC_CAPTURED/.test(x.row.status),'a late protocol/network failure must not retain a passing status');}
(async()=>{
 await check('phase2-c09-two-pending-close-rejections',async make=>{
  const h=await make({closeDelayMs:1000,afterStart:(api,s,row)=>{row.network.interceptErrors.push(...fourErrors);s.bidi.seq=34;},afterCommon:(api,s,row,blocked)=>{blocked('pending-35');blocked('pending-36');}});
  const x=await h.phaseTwo('COLLECTOR_OR_ATTEMPT_ERROR',originalStall,true);sameReceipts(x);
  assert.deepEqual(x.stored.network.interceptErrors,[...fourErrors,'Error: BiDi closed','Error: BiDi closed']);
  assert.equal(x.row.primaryOutcome.error,originalStall);assert.equal(x.row.primaryOutcome.status,'COLLECTOR_OR_ATTEMPT_ERROR');
  assert.equal(x.row.error,originalStall);assert.equal(x.row.checks.networkInterceptionsClean,false);
  assert.equal(x.row.protocolFinalization.ok,true);assert.equal(x.row.protocolFinalization.socketClosed,true);assert.equal(x.row.protocolFinalization.pendingCommandCount,0);assert.equal(x.row.protocolFinalization.pendingEventHandlerCount,0);
  const trace=fs.readFileSync(path.join(h.api.OUT,x.row.name,'bidi-trace.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  assert.deepEqual(trace.filter(e=>e.kind==='command-close-rejection').map(e=>e.wireId),[35,36]);
  const late=await h.afterLate();sameReceipts(late);assert.deepEqual(late.stored,x.stored);
  return {interceptionErrors:x.stored.network.interceptErrors.length,pendingWiresReplayed:[35,36],primaryOutcomePreserved:true};
 });
 await check('first-phase-actual-collect-preserves-primary-and-joins-close',async make=>{
  let h;h=await make({closeDelayMs:1000,afterStart:(api,s,row)=>{row.network.interceptErrors.push(...fourErrors);s.bidi.seq=34;const evaluate=s.eval;s.eval=async(script,cleanup)=>{if(!cleanup&&script===api.PROGRESS){h.blocked('pending-35');h.blocked('pending-36');throw Error(originalStall);}return evaluate(script,cleanup);};}});
  const x=await h.firstPhase();sameReceipts(x);assert.equal(x.ok,false);assert.equal(x.row.network.interceptErrors.length,6);assert(x.row.primaryOutcome.error.includes(originalStall));assert.equal(x.row.error,x.row.primaryOutcome.error);assert.equal(x.row.protocolFinalization.ok,true);assert.equal(x.row.checks.networkInterceptionsClean,false);return {caller:'collect',interceptionErrors:x.row.network.interceptErrors.length,primaryOutcomePreserved:true};
 });
 await check('phase2-delayed-handler-invalidates-preliminary-clean-pass',async make=>{
  let release;const gate=new Promise(resolve=>release=resolve);
  const h=await make({afterCommon:(api,s,row,blocked,delay)=>{const call=s.bidi.call.bind(s.bidi);s.bidi.call=async(method,...args)=>{try{return await call(method,...args);}catch(error){if(method==='network.continueRequest')await gate;throw error;}};blocked('pending-late-handler');delay(1400).then(release);},releaseHandler:()=>release()});
  const x=await h.phaseTwo();assert.equal(x.initialCommonCheck.networkInterceptionsClean,true);sameReceipts(x);assertFailed(x);assert.equal(x.row.primaryOutcome.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(x.row.checks.networkInterceptionsClean,false);assert.deepEqual(x.row.network.interceptErrors,['Error: BiDi closed']);assert.equal(x.row.protocolFinalization.ok,true);return {preliminaryClean:true,finalClean:false,finalStatus:x.row.status};
 });
 await check('first-phase-actual-collect-invalidates-late-clean-pass',async make=>{
  let fired=false,h;h=await make({onScreenshot:()=>{if(!fired){fired=true;h.blocked('pending-after-common');}}});
  const x=await h.firstPhase();sameReceipts(x);assert.equal(x.row.primaryOutcome.status,'PHASE_CHECKS_PASSED');assert.equal(x.ok,false);assert.equal(x.row.status,'PHASE_CHECKS_FAILED');assert.equal(x.row.checks.networkInterceptionsClean,false);assert.deepEqual(x.row.network.interceptErrors,['Error: BiDi closed']);return {caller:'collect',preliminaryStatus:x.row.primaryOutcome.status,finalStatus:x.row.status};
 });
 await check('never-closing-transport-is-bounded-failed-and-frozen',async make=>{
  const h=await make({neverClose:true,afterCommon:(api,s,row,blocked)=>{blocked('pending-never-close');}});
  const x=await h.phaseTwo();sameReceipts(x);assertFailed(x);assert.equal(x.row.status,'PROTOCOL_FINALIZATION_FAILED');assert.equal(x.row.protocolFinalization.ok,false);assert.equal(x.row.protocolFinalization.socketClosed,false);assert.equal(x.row.protocolFinalization.pendingCommandCount,1);assert.equal(x.row.protocolFinalization.pendingEventHandlerCount,1);assert.equal(x.row.checks.protocolFinalizationComplete,false);assert.equal(x.row.cleanup.ok,true);assert(x.callerElapsedMs<6500,'protocol finalization must fit the existing five-second join window plus simulated capture overhead');assert.equal(h.api.result.stopLaunches.kind,'protocol-finalization-unverified');
  const late=await h.afterLate();sameReceipts(late);assert.deepEqual(late.stored,x.stored,'late close must not mutate the sealed failed receipt');assert.equal(late.mutableRow.network.interceptErrors.length,1,'late raw error is retained on its live owner');return {callerElapsedMs:x.callerElapsedMs,status:x.row.status,cleanupProcessProofPreserved:true,pendingCommandCount:x.row.protocolFinalization.pendingCommandCount};
 });
 await check('never-settling-handler-is-bounded-even-after-socket-close',async make=>{
  let release;const gate=new Promise(resolve=>release=resolve);
  const h=await make({afterCommon:(api,s,row,blocked)=>{const call=s.bidi.call.bind(s.bidi);s.bidi.call=async(method,...args)=>{try{return await call(method,...args);}catch(error){if(method==='network.continueRequest')await gate;throw error;}};blocked('pending-blocked-handler');},releaseHandler:()=>release()});
  const x=await h.phaseTwo();sameReceipts(x);assertFailed(x);assert.equal(x.row.status,'PROTOCOL_FINALIZATION_FAILED');assert.equal(x.row.protocolFinalization.socketClosed,true);assert.equal(x.row.protocolFinalization.pendingCommandCount,0);assert.equal(x.row.protocolFinalization.pendingEventHandlerCount,1);assert(x.callerElapsedMs<6500);const late=await h.afterLate();sameReceipts(late);assert.deepEqual(late.stored,x.stored);return {callerElapsedMs:x.callerElapsedMs,status:x.row.status,socketClosed:true,pendingEventHandlerCount:1};
 });
 await check('phase2-final-trace-write-error-cannot-retain-pass',async make=>{
  const h=await make({traceFailure:true});const x=await h.phaseTwo();sameReceipts(x);assertFailed(x);assert.equal(x.row.status,'COLLECTOR_TRACE_ERROR');assert.equal(x.row.checks.bidiTraceIntact,false);assert.equal(x.row.bidiTrace.writeErrors.length,1);return {traceWriteErrors:x.row.bidiTrace.writeErrors.length,status:x.row.status};
 });
 await check('socket-settlement-just-before-shared-deadline-is-accepted',async make=>{
  const h=await make({closeAtDeadlineOffsetMs:-1});const x=await h.phaseTwo();sameReceipts(x);assert.equal(x.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(x.row.protocolFinalization.ok,true);assert.equal(x.row.protocolFinalization.settledWithinDeadline,true);assert.equal(x.row.protocolFinalization.settledAtMonotonicMs,x.row.protocolFinalization.deadlineMonotonicMs-1);return {settlementOffsetMs:-1,status:x.row.status};
 });
 await check('late-socket-settlement-is-failed-even-with-zero-pending-work',async make=>{
  const h=await make({closeAtDeadlineOffsetMs:1});const x=await h.phaseTwo();sameReceipts(x);assert.equal(x.row.status,'PROTOCOL_FINALIZATION_FAILED');assert.equal(x.row.protocolFinalization.socketClosed,true);assert.equal(x.row.protocolFinalization.pendingCommandCount,0);assert.equal(x.row.protocolFinalization.pendingEventHandlerCount,0);assert.equal(x.row.protocolFinalization.settledWithinDeadline,false);assert.equal(x.row.protocolFinalization.settledAtMonotonicMs,x.row.protocolFinalization.deadlineMonotonicMs+1);return {settlementOffsetMs:1,pendingCommands:0,pendingHandlers:0,status:x.row.status};
 });
 await check('settlement-before-deadline-can-be-joined-after-deadline',async make=>{
  const h=await make({processExitDelayMs:1000,afterProfileRemovalAdvanceMs:6000});const x=await h.phaseTwo();sameReceipts(x);assert.equal(x.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(x.row.protocolFinalization.ok,true);assert.equal(x.row.protocolFinalization.settledWithinDeadline,true);assert(h.clock.now()>x.row.protocolFinalization.deadlineMonotonicMs);assert(x.row.protocolFinalization.settledAtMonotonicMs<x.row.protocolFinalization.deadlineMonotonicMs);return {joinedAfterDeadline:true,settledBeforeDeadline:true,status:x.row.status};
 });
 await check('join-exception-is-explicit-nonpass-with-process-proof-preserved',async make=>{
  const h=await make({afterStart:(api,s)=>{s.bidi.joinClose=async()=>{throw Error('simulated join failure');};}});const x=await h.phaseTwo('COLLECTOR_OR_ATTEMPT_ERROR',originalStall);sameReceipts(x);assert.equal(x.row.status,'PROTOCOL_FINALIZATION_FAILED');assert.equal(x.row.cleanup.ok,true);assert.equal(x.row.protocolFinalization.ok,false);assert(x.row.protocolFinalization.error.includes('simulated join failure'));assert.equal(x.row.primaryOutcome.error,originalStall);assert.equal(x.row.error,originalStall);return {status:x.row.status,cleanupProcessProofPreserved:true,primaryOutcomePreserved:true};
 });
 await check('late-trace-failure-keeps-the-incomplete-final-cut-immutable',async make=>{
  const h=await make({neverClose:true,traceFailure:true,traceFailureKind:'command-close-rejection',afterCommon:(api,s,row,blocked)=>blocked('pending-late-trace')});const x=await h.phaseTwo();sameReceipts(x);assert.equal(x.row.status,'PROTOCOL_FINALIZATION_FAILED');const late=await h.afterLate();sameReceipts(late);assert.deepEqual(late.stored,x.stored);assert.equal(late.mutableRow.bidiTrace.writeErrors.length,1);assert.equal(late.mutableRow.network.interceptErrors.length,1);const raw=fs.readFileSync(path.join(h.api.OUT,x.row.name,'protocol-errors.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.deepEqual(raw.at(-1).collectorLateTraceWriteError,clone(late.mutableRow.bidiTrace.writeErrors[0]));return {status:x.row.status,lateRawTraceErrors:1,lateRawInterceptionErrors:1};
 });
 await check('clean-first-phase-actual-collect-remains-passed',async make=>{
  const h=await make();const x=await h.firstPhase();sameReceipts(x);assert.equal(x.ok,true);assert.equal(x.row.status,'PHASE_CHECKS_PASSED');assert.equal(x.row.protocolFinalization.ok,true);assert.equal(x.row.checks.protocolFinalizationComplete,true);return {caller:'collect',status:x.row.status};
 });
 await check('clean-phase2-finish-retains-its-original-pass',async make=>{
  const h=await make();const x=await h.phaseTwo();sameReceipts(x);assert.equal(x.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(x.row.protocolFinalization.ok,true);assert.equal(x.row.checks.networkInterceptionsClean,true);return {caller:'finishOwnedCase',status:x.row.status};
 });
 console.log(JSON.stringify({schema:'r0017-protocol-finalization-controls/v1',nativeExecutions:0,simulationOnly:true,clockScale:SCALE,sourceSha256:sha(baseSource),phase2SourceSha256:sha(phase2Source),testSha256:sha(fs.readFileSync(__filename)),passed:results.filter(x=>x.passed).length,failed:results.filter(x=>!x.passed).length,results},null,2));process.exitCode=results.every(x=>x.passed)?0:1;
})().catch(e=>{console.error(e);process.exitCode=1;});
