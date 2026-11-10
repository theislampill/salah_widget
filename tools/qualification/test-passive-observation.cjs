#!/usr/bin/env node
'use strict';
// Browser-free boundary controls. Run the actual session, public consumer and
// finalizer with simulated Windows/process/socket/page boundaries. No native credit.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),crypto=require('node:crypto');
const {EventEmitter}=require('node:events'),{performance:clock}=require('node:perf_hooks');
const baseFile=process.env.R0017_PASSIVE_BASE_SOURCE||path.join(__dirname,'r0017-windows-proof.cjs');
const phaseFile=process.env.R0017_PASSIVE_PHASE2_SOURCE||path.join(__dirname,'r0017-phase2-controls.cjs');
const entryFile=path.join(__dirname,'r0017-windows-passive.cjs'),methodFile=path.join(__dirname,'r0017-passive-network.cjs');
const root=path.resolve(__dirname,'../..'),base=fs.readFileSync(baseFile,'utf8'),phase=fs.readFileSync(phaseFile,'utf8');
const prefix=base.slice('#!/usr/bin/env node\n'.length,base.indexOf('async function main(){'));
const declared=JSON.parse(fs.readFileSync(path.join(root,'tests/smoke.html'),'utf8').match(/const CASES=(\[[\s\S]*?\n\]);/)[1]);
const hash=v=>crypto.createHash('sha256').update(v).digest('hex'),copy=v=>JSON.parse(JSON.stringify(v));
const evidence=process.env.R0017_PASSIVE_TEST_OUT;if(evidence)fs.mkdirSync(evidence,{recursive:true});
const results=[],SCALE=10,PUBLIC='https://theislampill.github.io/salah_widget/',payloadBytes=Buffer.from('SIMULATION ONLY: public dependency bytes'),payloadSHA=hash(payloadBytes);
const selected=['chromium-public-healthy-no-preference','chromium-public-healthy-reduce'];
const CORE_PATH='C:\\Program Files\\PowerShell\\7\\pwsh.exe',CORE_SHA='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233';
const ORIGINAL_QUERY_SHA='feecf593a83ac68c2e3e76f9899d624b7a16ae273baf2be93ae51863e583f9d1';
function originalQuery(call){assert.equal(call.options.timeout,5000);assert.equal(call.options.windowsHide,true);assert.deepEqual(call.args.slice(0,-1),['-NoLogo','-NoProfile','-NonInteractive','-Command']);assert.equal(hash(call.args.at(-1).replace(/@\(\d+(?:,\d+)*\) \| ForEach-Object/,'@(2288) | ForEach-Object')),ORIGINAL_QUERY_SHA);}

async function harness(name,options={}){
 const home=fs.mkdtempSync(path.join(evidence||os.tmpdir(),'r0017-passive-'+name+'-')),out=path.join(home,'receipts'),timers=new Set(),sockets=[];
 let deleted=false,session=null,spawnCount=0,preference='reduce',currentURL=null,navCount=0,failCapture=false,sessionRequested=false,currentFixtureURL=null,currentFixtureFrame=null,failAccountingWrite=!!options.accountingWriteFailure;const inventoryCalls=[],coreBytes=Buffer.from('SIMULATION ONLY: substituted admitted Core binary and digest');
 const localClock={now:()=>clock.now()*SCALE};
 function later(fn,ms,...args){const id=setTimeout(()=>{timers.delete(id);fn(...args);},ms/SCALE);timers.add(id);return id;}
 function cancel(id){timers.delete(id);clearTimeout(id);}
 const delay=ms=>new Promise(resolve=>later(resolve,ms));
 let child;function newChild(){const owned=new EventEmitter();Object.assign(owned,{pid:101,exitCode:null,signalCode:null,kill:()=>{owned.exitCode=0;owned.emit('exit',0,null);return true;}});return owned;}
 const accountingMode=options.requestAccounting==='observed-records';
 const accounting=accountingMode?require('./r0017-request-accounting.cjs'):null,indexSHA=accountingMode?accounting.PINNED_SOURCE['index.html'].sha256:payloadSHA;
 const sourceFiles=accountingMode?Object.fromEntries([...new Set([...Object.keys(accounting.PINNED_SOURCE),'real-sky/native-sky.css','real-sky/native-first-paint.mjs','README.md','docs/state-contracts/R0017.md'])].map(file=>{const b=fs.readFileSync(path.join(root,file));return [file,{bytes:b.length,sha256:hash(b)}];})):null;
 function profile(f,baseline=false){if(!accountingMode)return f;Object.assign(f,{scriptContract:'salah-native-script-adapter/1',scriptProfile:'split-moon',scriptPrerequisites:[{role:'first-paint',sha256:'3591c4460aeb291e487ef1f750071b6b7436fa904b619fb3b54659c6fa4b83ed'},{role:'moon-initial',sha256:'837b77f23fffcb5fc24c3561632143733653d32918046dd1f65a17e227456a14'},{role:'moon-refinement',sha256:'d4f90ac35284f19e4675b6314ae60b0fc4ad441be54b1b78c74c173b1d80d7a4'}],firstPaintSourceSha256:'3591c4460aeb291e487ef1f750071b6b7436fa904b619fb3b54659c6fa4b83ed',ledger:[{attempt:f.attempt,url:'https://api.aladhan.com/v1/timings/07-09-2026?latitude=24.47',jsonReads:1,result:'json-consumed'}]});
 if(options.missingJSON&&!baseline||options.baselineMissingJSON&&baseline)f.ledger[0].jsonReads=0;
 if(options.staleFixture&&!baseline)f.attempt++;if(options.sourceDrift&&!baseline)f.sourceSha256='0'.repeat(64);return f;}
 function cdp(socket,event,params,sessionId='simulated-owned-cdp'){socket.message({method:'goog:cdp.'+event,params:{event,params,session:sessionId}});}
 function documentEvents(socket,id,url,frame,parentId){const u=new URL(url),base=u.origin+u.pathname+u.search,fragment=u.hash;
 cdp(socket,'Network.requestWillBeSent',{requestId:id,request:{url:base,urlFragment:fragment,method:'GET'},documentURL:base,frameId:frame,loaderId:id,type:'Document',initiator:{type:'other'}});
 cdp(socket,'Network.loadingFinished',{requestId:id,encodedDataLength:12});
 const f={id:frame,loaderId:id,url:base,urlFragment:fragment,...(parentId?{parentId}:{})};cdp(socket,'Page.frameNavigated',{frame:f});
 const realm='realm-'+id;socket.message({method:'script.realmCreated',params:{realm,type:'window',context:frame,origin:new URL(PUBLIC).origin}});
 cdp(socket,'Runtime.executionContextCreated',{context:{id:navCount,uniqueId:realm,origin:new URL(PUBLIC).origin,auxData:{frameId:frame,isDefault:true,type:'default'}}});
 if(url.includes('widget-fixture.html'))cdp(socket,'Page.documentOpened',{frame:f});}
 const driver={ProcessId:101,ParentProcessId:1,Name:'simulated-driver',ExecutablePath:'C:/sim/driver.exe',CreationDate:'2026-11-07T00:00:00.0000000Z'},browser={ProcessId:102,ParentProcessId:101,Name:'simulated-browser',ExecutablePath:'C:/sim/browser.exe',CreationDate:'2026-11-07T00:00:01.0000000Z'};
 function snapshot(){const seed=Object.fromEntries(Object.keys(api.seeds('absent')).map(k=>[k,null])),sha256=indexSHA,documentId='00000000-0000-0000-0000-000000000001',h='simulated-owned-document';
  const fixture={run:'simulation',attempt:1,hash:h,mode:'healthy',documentId,sourceSha256:sha256,state:'ready',error:null,storageIsolated:true,clockFixed:true,fetchIntercepted:true};
  profile(fixture);
  const cases=declared.map(([name,expected])=>({name,expected,state:'executed',assertions:expected,reason:null}));
  const smoke={status:'PASS',pass:141,fail:0,skip:0,required:{total:30,executed:30,failed:0,missing:[],cases},fixture:{run:'simulation',attempts:[{attempt:1,hash:h,mode:'healthy',result:'ready',reason:null,documentId,sourceSha256:sha256,fixture}]}};
  if(options.missingCase){smoke.required.executed=29;smoke.required.missing=[declared[22][0]];smoke.required.cases[22].state='missing';smoke.required.cases[22].assertions=0;smoke.required.cases[22].reason='simulated original case missing';smoke.status='FAIL';}
  return {smoke,assertionLog:Array.from({length:141},(_,i)=>'✓ PASS  simulated assertion '+i).join('\n'),viewport:{width:1100,height:900},dpr:1,preference:preference==='reduce',children:{preference:preference==='reduce'},storage:{before:seed,after:seed,entries:[]}};
 }
 function baseline(){const u=new URL(currentURL),h=u.hash.slice(1),sha256=indexSHA,fixture={run:u.searchParams.get('run'),attempt:1,hash:h,mode:'healthy',documentId:'00000000-0000-0000-0000-000000000002',sourceSha256:sha256,bridgeSha256:'2'.repeat(64),state:'ready',error:null,storageIsolated:true,clockFixed:true,fetchIntercepted:true,scriptProfile:'split-moon'};
  profile(fixture,true);
  const pulse=options.flatMotion?1:1.03;
  return {ready:true,snapshot:snapshot(),data:{fixture,owner:{...fixture},hash:h,url:currentURL,originalMatchMediaRestored:true,nativeReduced:false,motionFull:false,pulse,pulseRaw:String(pulse),qa:{sim:'07-09-2026 12:30',sunEl:60,cache:{prayerDate:'07-09-2026'},render:{currentKey:'Dhuhr',nextKey:'Asr',leftMin:180}},model:{nextTime:'15:30'},transforms:['.suncorner .corona','.suncorner .rays'].map(selector=>({selector,count:1,raw:'matrix('+pulse+', 0, 0, '+pulse+', 0, 0)',error:null,matrix:{is2D:true,m11:pulse,m12:0,m21:0,m22:pulse}}))}};
 }
 class Socket{
  constructor(){this.listeners=new Map();this.sent=[];this.readyState=0;sockets.push(this);queueMicrotask(()=>{this.readyState=1;this.emit('open',{});});}
  addEventListener(type,fn,options){const a=this.listeners.get(type)||[];a.push({fn,once:options?.once});this.listeners.set(type,a);}
  emit(type,event){for(const x of [...(this.listeners.get(type)||[])]){if(x.once)this.listeners.set(type,this.listeners.get(type).filter(y=>y!==x));x.fn(event);}}
  message(value){this.emit('message',{data:JSON.stringify(value)});}
  send(encoded){if(this.readyState!==1)throw Error('simulated socket closed');const c=JSON.parse(encoded);this.sent.push(c);let result={};
   if(c.method==='session.subscribe'&&(options.subscriptionFailure||options.cdpSubscriptionFailure&&c.params.events.some(e=>e.startsWith('goog:cdp.')))){queueMicrotask(()=>this.message({id:c.id,type:'error',error:'invalid argument',message:'simulated unsupported lifecycle event'}));return;}
   if(c.method==='browsingContext.getTree')result={contexts:options.ambiguousTop?[{context:'simulated-top'},{context:'unexpected-top'}]:[{context:'simulated-top'}]};
   if(c.method==='goog:cdp.getSession')result=options.missingCdpSession?{}:{session:'simulated-owned-cdp'};
   if(c.method==='goog:cdp.sendCommand'){
    if(options.securityCommandFailure===c.params.method){queueMicrotask(()=>this.message({id:c.id,type:'error',error:'unknown command',message:'simulated unsupported '+c.params.method}));return;}
    result={result:{},session:options.wrongCdpSession?'unexpected-cdp':c.params.session};
    if(options.securityReplay){const method=c.params.method==='Log.enable'?'Log.entryAdded':'Audits.issueAdded',params=method==='Log.entryAdded'?{entry:{source:'security',level:'error',text:'SIMULATED CSP diagnostic replay',timestamp:1794089691000}}:{issue:{code:'ContentSecurityPolicyIssue',details:{contentSecurityPolicyIssueDetails:{blockedURL:'data',violatedDirective:'img-src',isReportOnly:false,contentSecurityPolicyViolationType:'kURLViolation'}}}};queueMicrotask(()=>this.message({method:'goog:cdp.'+method,params:{session:c.params.session,event:method,params}}));}
   }
   if(c.method==='browsingContext.navigate'){currentURL=c.params.url;const navigation='nav-'+(++navCount);result={url:currentURL,navigation};queueMicrotask(()=>{if(options.omitNetworkEvents)return;event('network.beforeRequestSent','document-'+navCount,currentURL,{context:'simulated-top',navigation});if(!options.pendingNavigation)event('network.responseCompleted','document-'+navCount,currentURL,{context:'simulated-top',navigation,response:{url:currentURL,status:200,statusText:'OK'}});if(accountingMode){documentEvents(this,'document-'+navCount,currentURL,'simulated-top');if(currentURL.includes('widget-fixture.html')){currentFixtureURL=currentURL;currentFixtureFrame='simulated-top';}else{const f=snapshot().smoke.fixture.attempts[0].fixture;currentFixtureURL=PUBLIC+'tests/widget-fixture.html?mode=healthy&run=simulation&attempt=1#'+f.hash;currentFixtureFrame='simulated-fixture';documentEvents(this,'fixture-'+navCount,currentFixtureURL,currentFixtureFrame,'simulated-top');}}});}
   if(c.method==='script.evaluate'){let value=c.params.expression.includes('const ready=!!f&&')?baseline():c.params.expression.includes('progress:(()=>')?{progress:{done:true,child:null},snapshot:snapshot()}:snapshot();result={type:'success',realm:'simulated-realm',result:{type:'string',value:JSON.stringify(value)}};}
   if(c.method==='browsingContext.captureScreenshot')result={data:Buffer.from('simulated screenshot; not native evidence').toString('base64')};
   queueMicrotask(()=>this.message({id:c.id,type:'success',result}));
  }
  close(){this.readyState=2;if(accountingMode&&options.accountingUnknown){const u='blob:https://theislampill.github.io/simulated-owned-worker';cdp(this,'Network.requestWillBeSent',{requestId:'unknown-'+navCount,request:{url:u,method:'GET'},documentURL:u,frameId:currentFixtureFrame,loaderId:'',type:'Script',initiator:{type:'other',url:currentFixtureURL}},options.unboundSession?'ALIEN':'simulated-owned-cdp');}if(options.onClose)options.onClose({event,socket:this,session,armCaptureFailure:()=>{failCapture=true;}});if(!options.neverClose)later(()=>this.release(),300);}
  release(){if(this.readyState===3)return;this.readyState=3;this.emit('close',{code:1000,reason:'simulated owned teardown',wasClean:true});}
 }
 const fsBoundary={...fs,writeFileSync(file,...args){if(failAccountingWrite&&String(file).endsWith('request-accounting.json')){failAccountingWrite=false;throw Error('simulated final accounting write failure');}return fs.writeFileSync(file,...args);},readFileSync(file,...args){if(file===CORE_PATH){if(options.missingCore)throw Error('simulated installed Core file missing');return options.mismatchedCore?Buffer.from('SIMULATION ONLY: wrong Core identity'):coreBytes;}return fs.readFileSync(file,...args);},appendFileSync(file,...args){if(failCapture&&String(file).endsWith(options.captureFailureFile||'network.jsonl')){failCapture=false;throw Error('simulated network capture disk error');}return fs.appendFileSync(file,...args);}};
 const proc={platform:'win32',argv:['node',baseFile,'--root',root,'--out',out],env:{RUNNER_TEMP:home},versions:process.versions,version:process.version,exitCode:0};
 // Only the simulated Core fixture gets the S0 digest. Other source hashes use real crypto.
 const cryptoBoundary={...crypto,createHash(algorithm,...args){const h=crypto.createHash(algorithm,...args);let core=false;return {update(value,...rest){core=value===coreBytes;h.update(value,...rest);return this;},digest(encoding){return core&&algorithm==='sha256'&&encoding==='hex'?CORE_SHA:h.digest(encoding);}};}};
 function boundaryRequire(id){if(id==='node:fs')return fsBoundary;if(id==='node:crypto')return cryptoBoundary;if(id==='node:child_process')return {spawn:()=>{spawnCount++;deleted=false;sessionRequested=false;child=newChild();return child;},execFileSync(executable,args,options){if(!['powershell.exe',CORE_PATH].includes(executable))throw Error('Unadmitted process boundary: '+executable);inventoryCalls.push(copy({executable,args,options}));if((harnessOptions.inventoryFailureCalls||[]).includes(inventoryCalls.length))throw Error('simulated inventory query failure');return JSON.stringify(deleted||child.exitCode!==null?[]:sessionRequested?[driver,browser]:[driver]);}};if(id==='node:timers/promises')return {setTimeout:delay};return require(id);}
 const harnessOptions=options;
 const ctx={require:boundaryRequire,module:{exports:{}},Buffer,URL,URLSearchParams,AbortSignal,performance:localClock,process:proc,WebSocket:Socket,setTimeout:later,clearTimeout:cancel,queueMicrotask,console,__filename:baseFile,__dirname:path.dirname(baseFile),boundary:{
  locate:()=>({binary:'simulated-browser',driver:'simulated-driver',browserSha256:'simulated',driverSha256:'simulated'}),
  request:async(base,method,route)=>{if(route==='/status')return {ready:true};if(method==='DELETE'){deleted=true;return null;}if(route==='/session'){sessionRequested=true;return {sessionId:'simulated-session',capabilities:{platformName:'windows','goog:processID':102,webSocketUrl:'ws://127.0.0.1:9666/session'}};}return {};},capture:(s,p)=>{session=s;preference=p;s.row.simulationOnly=true;s.row.nativeExecutions=0;if(options.fakeCleanup){const close=s.close.bind(s);s.close=async()=>{await close();s.row.cleanup.ownedProcesses=[];return s.row.cleanup;};}if(options.omitFinalCut){const boundary=s.bidi.boundary.bind(s.bidi);s.bidi.boundary=stage=>stage==='case-final-cut'?null:boundary(stage);}},sourceManifest:sourceFiles?{commit:'eebba178172f96b3ffe5ab3845bc0fffd57c6e1b',files:sourceFiles}:null
 }};
 vm.runInNewContext(prefix+`\nlocate=boundary.locate;freePort=async()=>9666;request=boundary.request;const realStart=startSession;startSession=async(...args)=>{const s=await realStart(...args);boundary.capture(s,args[1]);return s;};source=boundary.sourceManifest||{treeSha256:'simulated',files:{'index.html':{sha256:'${payloadSHA}'},'tests/smoke.html':{sha256:'${payloadSHA}'},'tests/widget-fixture.html':{sha256:'${payloadSHA}'}}};declared=${JSON.stringify(declared)};module.exports={startSession,checkCommon,result,OUT,ROOT,EXPECTED,PUBLIC,runId,sha,write,record,seeds,preload,SNAPSHOT,PROGRESS,screenshot,publicReadback,operationTimeout,remainingBudgetMs,launchBlock,notAttempted,get source(){return source;},get declared(){return declared;}};`,ctx,{filename:baseFile});
 const api=ctx.module.exports;api.result.simulationOnly=true;api.result.nativeExecutions=0;
 const fetches=[];const fetchBoundary=async(raw,init)=>{const url=String(raw);assert.equal(init.redirect,'error');assert(url.startsWith(PUBLIC));fetches.push(url);let bytes=accountingMode?fs.readFileSync(path.join(root,decodeURIComponent(new URL(url).pathname.slice(new URL(PUBLIC).pathname.length)))):payloadBytes;if(options.mismatchedReadback||options.changedNativeData&&url.endsWith('/real-sky/native-data.js'))bytes=Buffer.from('SIMULATION ONLY: changed dependency');return {ok:true,status:200,url,headers:{get:()=>null},arrayBuffer:async()=>bytes};};ctx.fetch=fetchBoundary;
 const phaseSource=options.omitReducer?phase.replace("const ledger=require('./r0017-passive-network.cjs').finalize(row);","const ledger=undefined; /* SIMULATED omitted actual reducer invocation */"):phase;
 if(options.omitReducer)assert.notEqual(phaseSource,phase,'The deliberate missing-call mutant must alter the actual finalizer');
 const pc={require:boundaryRequire,module:{exports:{}},Buffer,URL,URLSearchParams,AbortSignal,fetch:fetchBoundary,performance:localClock,process:proc,WebSocket:Socket,console};vm.runInNewContext(phaseSource+'\nmodule.exports.testConsumers={finishOwnedCase,collectPublic,observedPublicReadback,accountingPublicReadback:typeof accountingPublicReadback==="function"?accountingPublicReadback:null};',pc,{filename:phaseFile});
 const consumers=pc.module.exports.testConsumers;
 function event(method,id,url=PUBLIC+'index.html',extra={}){session.bidi.ws.message({method,params:{context:null,navigation:null,timestamp:1794089691000,redirectCount:0,isBlocked:false,request:{request:id,url,method:'GET'},...extra}});}
 async function start(mode='passive',engine='chromium',origin=PUBLIC){const row={schema:'r0017-passive-simulation/v1',name:'simulated-case',engine,status:'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE',stage:'observation',plannedTopLevelDocuments:1,checks:{},screenshots:[{sha256:'simulated'}]};const dir=path.join(out,row.name);fs.mkdirSync(dir,{recursive:true});api.result.cases.push(row);if(options.securityProvenance){require(entryFile).configure(api,{groups:'public',cases:selected.join(','),'network-observation':'passive','security-provenance':options.securityProvenance});await api.startSession(engine,'reduce',{width:1100,height:900},1,row,dir,origin);}else await api.startSession(engine,'reduce',{width:1100,height:900},1,row,dir,origin,...(mode==='default'?[]:[mode]));return {row,dir};}
 async function finish(row,dir){await consumers.finishOwnedCase(api,row,session,dir,Date.now(),false);const cut=api.result.cases.find(x=>x.name===row.name);return {row:copy(cut),stored:JSON.parse(fs.readFileSync(path.join(dir,'result.json'))),summary:JSON.parse(fs.readFileSync(path.join(out,'summary.json'))).cases.find(x=>x.name===row.name),frozen:Object.isFrozen(cut)&&Object.isFrozen(cut.network)};}
 async function publicCase(pref='reduce'){const entry=require(entryFile);if(api.networkObservation===undefined)entry.configure(api,{groups:'public',cases:selected.join(','),'network-observation':'passive',...(options.securityProvenance?{'security-provenance':options.securityProvenance}:{}),...(options.imageAssignmentProvenance?{'image-assignment-provenance':options.imageAssignmentProvenance}:{}),...(accountingMode?{'request-accounting':'observed-records'}:{})});if(accountingMode&&!api.result.publicReadback){api.result.publicReadback=await api.publicReadback();api.result.publicReadback=await consumers.accountingPublicReadback(api);if(options.missingPublicExecutable)api.result.publicReadback=api.result.publicReadback.filter(x=>x.file!=='real-sky/native-data.js');}await consumers.collectPublic(api,'chromium',pref,declared);const row=api.result.cases.at(-1);return {row:copy(row),stored:JSON.parse(fs.readFileSync(path.join(out,row.name,'result.json'))),summary:JSON.parse(fs.readFileSync(path.join(out,'summary.json'))).cases.at(-1),frozen:Object.isFrozen(row)};}
 async function dispose(){for(const s of sockets)s.release();await delay(10);for(const id of timers)clearTimeout(id);timers.clear();if(!evidence)fs.rmSync(home,{recursive:true,force:true});}
 return {api,start,finish,publicCase,readback:()=>consumers.observedPublicReadback(api),fetches,event,snapshot,delay,dispose,get session(){return session;},get inventoryCalls(){return inventoryCalls;},get spawnCount(){return spawnCount;},get sent(){return sockets.flatMap(x=>x.sent);},get exitCode(){return proc.exitCode;},home};
}
async function check(name,fn){let h;try{const detail=await fn(async options=>(h=await harness(name,options)));results.push({name,passed:true,detail});}catch(e){results.push({name,passed:false,error:String(e.stack||e)});}finally{if(h)await h.dispose();}}
function equalCuts(x){assert.deepEqual(x.row,x.stored);assert.deepEqual(x.stored,x.summary);assert.equal(x.frozen,true);}
function failed(x){assert(!/PASSED/.test(x.row.status));}
function before(h,id,url,extra){h.event('network.beforeRequestSent',id,url,extra);}
function complete(h,id,url,extra){h.event('network.responseCompleted',id,url,{response:{url:url||PUBLIC+'index.html',status:200,statusText:'OK'},...extra});}
const IMAGE_MARKER='R0017_IMAGE_ASSIGNMENT ';
function imageOptions(){return {groups:'public',cases:selected.join(','),'network-observation':'passive','security-provenance':'csp','image-assignment-provenance':'src'};}
function imageRealm(preload,options={}){
 const calls=[],logs=[],storage=new Map(),listeners=[],nativeFailure=Error('SIMULATED native setter exception');let debugFailures=options.debugFailures||0,openCalls=0;
 class ImageElement{}
 const originalGet=function(){return this.value;};
 const originalSet=function(value){calls.push({receiver:this,value});if(!(this instanceof ImageElement))throw nativeFailure;if(value==='throw-native')throw nativeFailure;this.value=String(value);return 73;};
 Object.defineProperty(ImageElement.prototype,'src',{get:originalGet,set:originalSet,enumerable:true,configurable:!options.nonconfigurable});
 const ctx={HTMLImageElement:ImageElement,Image:ImageElement,location:{origin:options.foreign?'https://other.example':new URL(PUBLIC).origin,href:PUBLIC+'tests/widget-fixture.html?attempt=15#phase'},
  crypto:{randomUUID:()=>options.nonce||'simulated-realm-0001'},Date:{now:()=>1794284293000},performance:{now:()=>123.5},devicePixelRatio:1,
  console:{debug(text){if(debugFailures-->0)throw Error('SIMULATED console transport unavailable');logs.push(text);options.onLog?.(text);}},
  localStorage:{getItem:key=>storage.get(key)??null,setItem:(key,value)=>storage.set(key,value)},matchMedia:()=>({matches:false}),
  document:{readyState:'complete',open(){openCalls++;listeners.length=0;return ctx.document;},addEventListener:(...args)=>listeners.push(args)},
  addEventListener:(...args)=>listeners.push(args),originalCalls:0};
 ctx.window=ctx;ctx.top=ctx;ctx.document.defaultView=ctx;const context=vm.createContext(ctx),originalOpen=ctx.document.open;
 const returnValue=vm.runInContext('('+preload+')()',context,{filename:'SIMULATION_ONLY_combined-preload.js'});
 return {ctx,context,calls,logs,storage,listeners,originalGet,originalSet,originalOpen,nativeFailure,returnValue,ImageElement,
  get openCalls(){return openCalls;},markers:()=>logs.filter(v=>v.startsWith(IMAGE_MARKER)).map(v=>JSON.parse(v.slice(IMAGE_MARKER.length)))};
}
function cdpEvent(socket,event,params){socket.message({method:'goog:cdp.'+event,params:{event,params,session:'simulated-owned-cdp'}});}
function publicAbsentSeed(h){return Object.fromEntries(Object.keys(h.api.seeds('absent')).map(key=>[key,null]));}
function configuredImagePreload(h){require(entryFile).configure(h.api,imageOptions());return h.api.preload(publicAbsentSeed(h),PUBLIC,false);}
(async()=>{
 const v2={requestAccounting:'observed-records',securityProvenance:'csp',accountingUnknown:true};
 for(const fault of ['matching','wrong-url','missing-url','wrong-type','wrong-parent-frame'])await check('c18 unknown bootstrap '+fault+' attachment governs the actual next consumer without a terminal',async make=>{
  const h=await make({...v2,onClose:({socket})=>{
   const targetInfo={targetId:'unknown-2',type:'worker',url:'blob:https://theislampill.github.io/simulated-owned-worker',parentFrameId:'simulated-fixture'};
   if(fault==='wrong-url')targetInfo.url=PUBLIC+'tests/widget-fixture.html';if(fault==='missing-url')delete targetInfo.url;if(fault==='wrong-type')targetInfo.type='iframe';if(fault==='wrong-parent-frame')targetInfo.parentFrameId='ALIEN';
   cdpEvent(socket,'Target.attachedToTarget',{sessionId:'unknown-child',targetInfo,waitingForDebugger:false});
  }}),first=await h.publicCase('no-preference'),second=await h.publicCase('reduce');equalCuts(first);if(fault==='matching')equalCuts(second);else{assert.deepEqual(second.row,second.stored);assert.deepEqual(second.stored,second.summary);}
  const a=first.row.network.accounting,record=a.records.find(x=>x.requestId==='unknown-2');assert.equal(record.outcome,'unobserved');assert.equal(record.terminals.length,0);assert.equal(a.allNetworkOutcomesObserved,false);
  if(fault==='matching'){assert.equal(a.sourceClaimsBound,true);assert.equal(a.captureProblems.length,0);assert.equal(first.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(second.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(h.spawnCount,2);}
  else{assert.equal(a.sourceClaimsBound,false);assert(a.captureProblems.length>0);assert.equal(first.row.status,'PUBLIC_HEALTHY_FAILURE');assert.equal(first.row.checks.passiveObservationIntegrity,false);assert.equal(first.row.passiveObservationContinuation.decision,'BLOCK_EQUIVALENT_ENGINE');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);}
  return {firstStatus:first.row.status,outcome:record.outcome,secondStatus:second.row.status,simulatedSpawnCount:h.spawnCount};
 });
 await check('c18 contradictory attachment cannot complete a required script or admit the actual next consumer',async make=>{
  const h=await make({...v2,onClose:({socket})=>{
   cdpEvent(socket,'Network.requestWillBeSent',{requestId:'contradictory-required',request:{url:PUBLIC+'config.js',method:'GET'},documentURL:PUBLIC+'tests/smoke.html',loaderId:'',type:'Script',initiator:{type:'parser',url:PUBLIC+'tests/smoke.html'}});
   cdpEvent(socket,'Target.attachedToTarget',{sessionId:'contradictory-child',targetInfo:{targetId:'contradictory-required',type:'worker',url:PUBLIC+'tests/widget-fixture.html'},waitingForDebugger:false});
   socket.message({method:'goog:cdp.Network.loadingFinished',params:{event:'Network.loadingFinished',session:'contradictory-child',params:{requestId:'contradictory-required',encodedDataLength:12}}});
  }}),first=await h.publicCase('no-preference'),second=await h.publicCase('reduce');equalCuts(first);
  const a=first.row.network.accounting,record=a.records.find(x=>x.requestId==='contradictory-required');
  assert.equal(record.outcome,'unobserved');assert.equal(record.terminals.length,0);assert(a.orphans.some(x=>x.raw?.requestId==='contradictory-required'));assert(a.captureProblems.length>0);assert.equal(a.sourceClaimsBound,false);
  assert.equal(first.row.status,'PUBLIC_HEALTHY_FAILURE');assert.equal(first.row.checks.passiveObservationIntegrity,false);assert.equal(first.row.passiveObservationContinuation.decision,'BLOCK_EQUIVALENT_ENGINE');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);
  return {firstStatus:first.row.status,outcome:record.outcome,secondStatus:second.row.status,simulatedSpawnCount:h.spawnCount};
 });
 await check('c18 explicit method refuses unknown mode or image instrumentation before acquisition',async()=>{const e=require(entryFile),baseArgs=['--network-observation','passive','--groups','public','--cases',selected.join(','),'--base-file',baseFile,'--base-sha',hash(base),'--root',root,'--out','simulation'];const parsed=e.parse([...baseArgs,'--request-accounting','observed-records','--security-provenance','csp']);assert.equal(parsed['request-accounting'],'observed-records');assert.throws(()=>e.parse([...baseArgs,'--request-accounting','unknown','--security-provenance','csp']));assert.throws(()=>e.parse([...baseArgs,'--request-accounting','observed-records']));assert.throws(()=>e.parse([...baseArgs,'--request-accounting','observed-records','--security-provenance','csp','--image-assignment-provenance','src']));});
 await check('c18 real finalizer accounts source-bound unknown and launches exactly one next selected consumer',async make=>{const h=await make(v2),first=await h.publicCase('no-preference');equalCuts(first);assert.equal(first.row.schema,'r0017-public-passive-proof/v2');assert.equal(first.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(first.row.network.accounting.counts.unknown,1);assert.equal(first.row.network.accounting.allNetworkOutcomesObserved,false);assert.equal(Object.hasOwn(first.row.checks,'allNetworkOutcomesObserved'),false);assert.equal(first.row.checks.passiveObservationIntegrity,true);assert.equal(first.row.checks.passiveRequiredConsumersObserved,true);assert.equal(first.row.passiveObservationContinuation.decision,'NO_OBSERVATION_INTEGRITY_BLOCK');const second=await h.publicCase('reduce');equalCuts(second);assert.equal(second.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(h.spawnCount,2);assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate').length,3);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);});
 for(const fault of [{label:'unbound worker session',unboundSession:true},{label:'missing final cut',omitFinalCut:true},{label:'empty owned identity census',fakeCleanup:true},{label:'stale fixture attempt',staleFixture:true},{label:'drifted fixture source',sourceDrift:true},{label:'late malformed message',onClose:({socket})=>socket.emit('message',{data:'{bad'})}])await check('c18 actual next consumer is NOT_ATTEMPTED after '+fault.label,async make=>{const h=await make({...v2,...fault}),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert.equal(first.row.checks.passiveObservationIntegrity,false);const second=await h.publicCase('reduce');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);});
 for(const fault of [{label:'missing current JSON',missingJSON:true},{label:'missing independent baseline JSON',baselineMissingJSON:true},{label:'missing original calendar callback',missingCase:true}])await check('c18 original consumer remains failed despite reconciled observations: '+fault.label,async make=>{const h=await make({...v2,...fault}),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert.equal(first.row.network.accounting.allObservedRecordsReconciled,true);assert.equal(first.row.checks.passiveRequiredConsumersObserved,false);assert.equal(first.row.checks.passiveObservationIntegrity,true);if(fault.baselineMissingJSON){assert.equal(first.row.checks.fullOriginalHealthy,true);assert(first.row.network.accounting.requiredConsumerEvidence.gaps.some(x=>x.consumer?.startsWith('baseline:')&&x.kind==='CURRENT_JSON_NOT_CONSUMED'));}const second=await h.publicCase('reduce');assert.notEqual(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,2);});
 for(const fault of [{label:'CDP-only HTTP and fetch failure',inject(socket){cdpEvent(socket,'Network.requestWillBeSent',{requestId:'error',request:{url:PUBLIC+'image.png',method:'GET'},type:'Image'});cdpEvent(socket,'Network.responseReceived',{requestId:'error',response:{url:PUBLIC+'image.png',status:503}});cdpEvent(socket,'Network.loadingFailed',{requestId:'error',errorText:'actual CDP error',blockedReason:'csp',canceled:false});}},{label:'retained security error',inject(socket){cdpEvent(socket,'Log.entryAdded',{entry:{level:'error',source:'security',text:'CSP error'}});}}])await check('c18 actual cleanliness rejects '+fault.label,async make=>{const h=await make({...v2,onClose:({socket})=>fault.inject(socket)}),x=await h.publicCase();equalCuts(x);failed(x);assert.equal(x.row.checks.passiveObservationClean,false);assert(x.row.network.accounting.observedErrors.length>0);assert.equal(x.row.checks.passiveObservationIntegrity,true);});
 for(const fault of [{label:'ungrouped invalid raw begin',onClose:({event})=>event('network.beforeRequestSent',undefined,PUBLIC+'invalid-identity.png')},{label:'ungrouped authentication event',onClose:({event})=>event('network.authRequired','auth',PUBLIC+'auth.png')},{label:'failed final accounting write',accountingWriteFailure:true},{label:'omitted reducer invocation mutant',omitReducer:true}])await check('c18 actual finalizer blocks continuation for '+fault.label,async make=>{const h=await make({...v2,...fault}),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert.equal(first.row.checks.passiveObservationIntegrity,false);if(fault.label.startsWith('ungrouped')){assert(first.row.network.observedNetworkEvents.length>0);assert(first.row.network.accounting.orphans.length>0);}const second=await h.publicCase('reduce');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);});
 await check('c18 CDP-only forbidden destination stops actual continuation',async make=>{const h=await make({...v2,onClose:({socket})=>{cdpEvent(socket,'Network.requestWillBeSent',{requestId:'forbidden',request:{url:'https://provider.example/image',method:'GET'},type:'Image'});cdpEvent(socket,'Network.loadingFinished',{requestId:'forbidden',encodedDataLength:1});}}),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert.equal(first.row.checks.noUnexpectedNetwork,false);assert.equal(first.row.passiveObservationContinuation.decision,'BLOCK_UNEXPECTED_NETWORK');assert.equal(first.row.checks.passiveObservationIntegrity,true);const second=await h.publicCase('reduce');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);});
 await check('c18 union readback includes a CDP-only actual dependency',async make=>{const h=await make({...v2,onClose:({socket})=>{cdpEvent(socket,'Network.requestWillBeSent',{requestId:'cdp-config',request:{url:PUBLIC+'config.js',method:'GET'},type:'Script'});cdpEvent(socket,'Network.loadingFinished',{requestId:'cdp-config',encodedDataLength:1});}});await h.publicCase();h.fetches.length=0;const r=await h.readback();assert.equal(r.passed,true);assert(r.plannedPaths.includes('config.js'));assert(h.fetches.includes(PUBLIC+'config.js'));});
 await check('c18 actual union readback retains an unmapped CDP-only path',async make=>{const h=await make({...v2,onClose:({socket})=>{cdpEvent(socket,'Network.requestWillBeSent',{requestId:'cdp-unmapped',request:{url:PUBLIC+'unmapped.png',method:'GET'},type:'Image'});cdpEvent(socket,'Network.loadingFinished',{requestId:'cdp-unmapped',encodedDataLength:1});}});await h.publicCase();const r=await h.readback();assert.equal(r.passed,false);assert(r.unmapped.some(x=>x.url===PUBLIC+'unmapped.png'));});
 await check('c18 changed served native data refuses before acquiring a process',async make=>{const h=await make({...v2,changedNativeData:true});await assert.rejects(h.publicCase(),/source|native-data|mismatch/i);assert.equal(h.spawnCount,0);});
 await check('c18 missing served executable cannot acquire despite unchanged local source',async make=>{const h=await make({...v2,missingPublicExecutable:true});const x=await h.publicCase();failed(x);assert.equal(h.spawnCount,0);});
 await check('passive-installed-core-is-admitted-before-acquisition-and-owned-by-setup-and-cleanup',async make=>{const h=await make(),{row,dir}=await h.start();assert.equal(h.session.inventoryHost,row.inventoryHost);assert.equal(Object.isFrozen(row.inventoryHost),true);assert.equal(Object.isFrozen(row.inventoryHost.versionEvidence),true);assert.throws(()=>{h.session.inventoryHost={};},TypeError);assert.equal(row.inventoryHost.executablePath,CORE_PATH);assert.equal(row.inventoryHost.sha256,CORE_SHA);assert.equal(row.inventoryHost.runtimeReadback.status,'ADMITTED_IDENTICAL_EXECUTABLE');assert.equal(row.inventoryHost.versionEvidence.version,'7.6.9');assert.equal(row.inventoryHost.versionEvidence.kind,'PRIOR_S0_OBSERVATION_BOUND_TO_IDENTICAL_EXECUTABLE');assert.equal(row.inventoryHost.versionEvidence.runId,'42433584408');await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');const x=await h.finish(row,dir);equalCuts(x);assert.equal(x.row.cleanup.ok,true);assert.deepEqual(x.row.cleanup.inventoryHost,x.row.inventoryHost);assert.equal(h.inventoryCalls.length,5);for(const call of h.inventoryCalls){assert.equal(call.executable,CORE_PATH);originalQuery(call);}return {simulatedInventoryCalls:h.inventoryCalls.length,executable:CORE_PATH,versionReadback:'PRIOR_S0_ONLY',standaloneVersionInvocations:0};});
 await check('passive-installed-core-missing-refuses-before-acquisition-without-fallback',async make=>{const h=await make({missingCore:true});await assert.rejects(h.start(),/Core.*missing|inventory.*admission|missing/i);assert.equal(h.spawnCount,0);assert.equal(h.inventoryCalls.length,0);const r=h.api.result.cases[0].inventoryHost;assert.equal(r.runtimeReadback.status,'REFUSED');assert.equal(Object.isFrozen(r),true);return {spawnCount:0,inventoryCalls:0,status:r.runtimeReadback.status};});
 await check('passive-installed-core-hash-mismatch-refuses-before-acquisition-without-fallback',async make=>{const h=await make({mismatchedCore:true});await assert.rejects(h.start(),/hash|identity|inventory.*admission/i);assert.equal(h.spawnCount,0);assert.equal(h.inventoryCalls.length,0);const r=h.api.result.cases[0].inventoryHost;assert.equal(r.runtimeReadback.status,'REFUSED');assert.notEqual(r.runtimeReadback.sha256,CORE_SHA);return {spawnCount:0,inventoryCalls:0,status:r.runtimeReadback.status};});
 await check('passive-setup-query-error-keeps-same-admitted-host-for-error-cleanup',async make=>{const h=await make({inventoryFailureCalls:[2]});await assert.rejects(h.start(),/simulated inventory query failure/);const row=h.api.result.cases[0];assert.equal(h.spawnCount,1);assert.equal(row.cleanup.ok,true);assert.equal(row.cleanup.inventoryHost,row.inventoryHost);assert.equal(h.inventoryCalls.length,5);for(const call of h.inventoryCalls){assert.equal(call.executable,CORE_PATH);originalQuery(call);}return {setupError:true,ownedCleanup:row.cleanup.ok,simulatedInventoryCalls:h.inventoryCalls.length};});
 await check('passive-mode-refuses-invalid-strategy-before-process-acquisition',async make=>{const h=await make();await assert.rejects(h.start('passive-ish'),/observation|strategy|mode/i);assert.equal(h.spawnCount,0);return {spawnCount:0};});
 await check('passive-mode-refuses-uncommissioned-engine-before-process-acquisition',async make=>{const h=await make();await assert.rejects(h.start('passive','firefox'),/Chromium|chromium|scope/i);assert.equal(h.spawnCount,0);return {spawnCount:0};});
 await check('default-enforced-session-still-intercepts-and-continues-blocked-event',async make=>{const h=await make(),{row,dir}=await h.start('default');assert(h.sent.some(c=>c.method==='network.addIntercept'));assert.equal(row.inventoryHost,undefined);assert(h.inventoryCalls.length>=2);for(const call of h.inventoryCalls){assert.equal(call.executable,'powershell.exe');originalQuery(call);}before(h,'enforced',PUBLIC+'index.html',{isBlocked:true});await h.delay(100);assert(h.sent.some(c=>c.method==='network.continueRequest'&&c.params.request==='enforced'));h.api.checkCommon(row,h.snapshot(),{width:1100,height:900},1,h.snapshot().storage.before);assert.equal(row.checks.networkInterceptionsClean,true);const x=await h.finish(row,dir);equalCuts(x);assert.equal(x.row.checks.networkInterceptionsClean,true);return {allowed:x.row.network.allowed};});
 await check('passive-actual-session-subscribes-before-navigation-and-never-mutates-network',async make=>{const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');before(h,'blocked-foreign', 'https://api.aladhan.com/v1/timings/07-09-2026',{isBlocked:true});complete(h,'blocked-foreign','https://api.aladhan.com/v1/timings/07-09-2026');await h.delay(50);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);const subscription=h.sent.findIndex(c=>c.method==='session.subscribe'),navigation=h.sent.findIndex(c=>c.method==='browsingContext.navigate');assert(subscription>=0&&subscription<navigation);await assert.rejects(h.session.bidi.call('network.continueRequest',{request:'escape'}),/passive|forbidden/i);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.network.commandRefusals.length,1);assert.equal('networkInterceptionsClean' in x.row.checks,false);return {networkWireCommands:0,status:x.row.status};});
 await check('passive-repeated-url-redirect-and-null-context-identity-retained',async make=>{const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');const url=PUBLIC+'same.png';before(h,'repeat-a',url);complete(h,'repeat-a',url);before(h,'repeat-b',url);complete(h,'repeat-b',url);before(h,'redirect',url);complete(h,'redirect',url,{response:{url,status:302,statusText:'Found'}});before(h,'redirect',url,{redirectCount:1});complete(h,'redirect',url,{redirectCount:1});h.session.bidi.ws.message({method:'script.realmCreated',params:{realm:'worker-1',type:'dedicated-worker',origin:new URL(PUBLIC).origin,owners:['realm-main']}});await h.delay(100);const x=await h.finish(row,dir);equalCuts(x);assert.equal(x.row.network.requests.length,5);assert.equal(new Set(x.row.network.requests.map(r=>r.key)).size,5);const repeats=x.row.network.requests.filter(r=>r.url===url);assert.equal(repeats.length,4);assert(repeats.every(r=>r.context===null&&r.navigation===null));assert.deepEqual(repeats.filter(r=>r.requestId==='redirect').map(r=>r.redirectCount),[0,1]);assert.deepEqual(x.row.network.lifecycle.find(e=>e.method==='script.realmCreated').params.owners,['realm-main']);assert.equal(x.row.checks.passiveRequestsAccounted,true);return {requestCount:5,nullContextRequests:4};});
 await check('passive-pending-and-unmatched-requests-fail-without-invented-completion',async make=>{const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');before(h,'pending');complete(h,'unmatched');await h.delay(50);const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.checks.passiveRequestsAccounted,false);assert.equal(x.row.network.finalBoundary.pendingRequests.length,1);assert.equal(x.row.network.finalBoundary.unmatchedRequests.length,1);assert.equal(x.row.network.requests.find(r=>r.requestId==='pending').terminalEvents.length,0);return {pending:1,unmatched:1};});
 await check('passive-policy-and-raw-http-fetch-errors-are-not-whitelisted',async make=>{const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');for(const [id,url]of [['provider','https://api.aladhan.com/v1/timings/07-09-2026'],['external','https://fonts.googleapis.com/css2'],['outside','https://theislampill.github.io/outside']]){before(h,id,url);complete(h,id,url);}before(h,'http');h.event('network.responseCompleted','http',PUBLIC+'index.html',{response:{url:PUBLIC+'index.html',status:503,statusText:'raw Service Unavailable'}});before(h,'cancel');h.event('network.fetchError','cancel',PUBLIC+'index.html',{errorText:'net::ERR_ABORTED'});await h.delay(50);const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.network.policyViolations.length,3);assert.equal(x.row.network.httpErrors[0].response.status,503);assert.equal(x.row.network.fetchErrors[0].errorText,'net::ERR_ABORTED');assert.equal(x.row.checks.passiveObservationClean,false);return {policyViolations:3,httpStatus:503,fetchError:'net::ERR_ABORTED'};});
 await check('passive-allowed-embedded-and-normal-favicon-are-explicit-location-decisions',async make=>{const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');for(const [id,url]of [['embedded','data:image/png;base64,YQ=='],['blob','blob:https://theislampill.github.io/owned'],['favicon','https://theislampill.github.io/favicon.ico']]){before(h,id,url);complete(h,id,url);}await h.delay(50);const x=await h.finish(row,dir);equalCuts(x);assert.equal(x.row.network.policyViolations.length,0);assert.deepEqual(x.row.network.requests.slice(1).map(r=>r.policy.classification),['allowed-embedded-image','allowed-embedded-blob','allowed-normal-favicon']);assert.equal(x.row.checks.passiveObservationClean,true);return {decisions:x.row.network.requests.slice(1).map(r=>r.policy.classification)};});
 await check('passive-finalizer-joins-late-fetch-protocol-and-capture-errors-in-one-frozen-cut',async make=>{const h=await make({onClose:({event,socket,armCaptureFailure})=>{event('network.beforeRequestSent','late');event('network.fetchError','late',PUBLIC+'index.html',{errorText:'raw late abort'});socket.message({id:9876,type:'error',error:'unknown error',message:'raw late protocol error'});armCaptureFailure();event('network.beforeRequestSent','capture');}}),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');h.api.checkCommon(row,h.snapshot(),{width:1100,height:900},1,h.snapshot().storage.before);assert.equal(row.checks.passiveObservationClean,true);const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.network.fetchErrors.at(-1).errorText,'raw late abort');assert(x.row.network.protocolErrors.some(e=>e.protocol?.value?.message==='raw late protocol error'));assert(x.row.network.captureErrors.some(e=>e.error.includes('simulated network capture disk error')));assert.equal(x.row.checks.passiveObservationClean,false);return {status:x.row.status,lateErrorsRetained:true};});
 await check('passive-unavailable-subscription-fails-setup-with-owned-cleanup',async make=>{const h=await make({subscriptionFailure:true});await assert.rejects(h.start(),/unsupported lifecycle/);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);const row=h.api.result.cases[0];assert.equal(row.cleanup.ok,true);assert.equal(row.protocolFinalization.ok,true);assert(row.network.protocolErrors.some(e=>e.protocol?.value?.error==='invalid argument'));return {cleanup:row.cleanup.status};});
 await check('explicit-entry-and-phase2-caller-refuse-implicit-or-expanded-population',async()=>{const entry=require(entryFile);for(const args of [[],['--network-observation','enforced'],['--network-observation','passive','--groups','current','--cases',selected.join(',')],['--network-observation','passive','--groups','public','--cases',selected[0]],['--network-observation','passive','--network-observation','passive']])assert.throws(()=>entry.parse(args));const parsed=entry.parse(['--network-observation','passive','--groups','public','--cases',selected.join(','),'--base-file',baseFile,'--base-sha',hash(base),'--root',root,'--out','simulation']);assert.equal(parsed['network-observation'],'passive');assert.throws(()=>entry.configure({startSession(){throw Error('must not start');}}, {...parsed,cases:selected.join(',')+',firefox-public-healthy-reduce'}));return {plannedNativeSessions:2,meaningfulTopLevelDocuments:3};});
 await check('passive-actual-public-consumer-retains-original-30-141-and-same-frozen-output',async make=>{const h=await make(),x=await h.publicCase();equalCuts(x);assert.equal(x.row.schema,'r0017-public-passive-proof/v1');assert.equal(x.row.checks.originalDenominator,true);assert.equal(x.row.checks.fullOriginalHealthy,true);assert.equal(x.row.checks.exactHealthyLog,true);assert.equal(x.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(x.row.nativeExecutions,0);assert.equal(x.row.simulationOnly,true);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);return {consumerStatus:x.row.status,nativeExecutions:0};});
 await check('passive-actual-public-consumer-rejects-missing-original-case',async make=>{const h=await make({missingCase:true}),x=await h.publicCase();equalCuts(x);failed(x);assert.equal(x.row.checks.fullOriginalHealthy,false);assert.equal(x.row.smoke.required.executed,29);return {consumerStatus:x.row.status,executed:29};});
 await check('passive-actual-no-preference-consumer-rejects-flat-motion',async make=>{const h=await make({flatMotion:true}),x=await h.publicCase('no-preference');equalCuts(x);failed(x);assert.equal(x.row.nativeNoPreferenceBaseline.checks.actualNoonConsumer,false);assert.equal(x.row.checks.actualNativeNoPreferenceConsumer,false);assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate').length,2);return {consumerStatus:x.row.status,meaningfulDocuments:2};});
 await check('passive-absent-network-observation-cannot-earn-passing-credit',async make=>{const h=await make({omitNetworkEvents:true}),x=await h.publicCase();equalCuts(x);failed(x);assert.equal(x.row.checks.fullOriginalHealthy,true);assert.equal(x.row.network.requests.length,0);assert.equal(x.row.checks.passiveRequestsAccounted,false);assert.equal(x.row.checks.passiveTopDocumentsObserved,false);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);return {consumerStatus:x.row.status,observedRequests:0,originalAssertions:141};});
 await check('passive-actual-no-preference-consumer-keeps-baseline-and-original-smoke',async make=>{const h=await make(),x=await h.publicCase('no-preference');equalCuts(x);assert.equal(x.row.status,'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE');assert.equal(x.row.checks.actualNativeNoPreferenceConsumer,true);assert.equal(x.row.checks.originalDenominator,true);assert.equal(x.row.checks.fullOriginalHealthy,true);assert.equal(x.row.checks.passiveTopDocumentsObserved,true);assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate').length,2);return {simulatedMeaningfulDocuments:2,originalAssertions:141,consumerStatus:x.row.status};});
 await check('passive-observed-dependency-readback-reaches-new-schema-actual-consumer',async make=>{const h=await make(),x=await h.publicCase();equalCuts(x);const r=await h.readback();assert.equal(r.passed,true);assert.deepEqual([...r.plannedPaths],['tests/smoke.html']);assert.equal(r.rows[0].expected.sha256,payloadSHA);assert.deepEqual(h.fetches,[PUBLIC+'tests/smoke.html']);return {readbackPassed:r.passed,observedPaths:[...r.plannedPaths]};});
 await check('passive-observed-dependency-readback-rejects-changed-bytes',async make=>{const h=await make({mismatchedReadback:true});await h.publicCase();const r=await h.readback();assert.equal(r.passed,false);assert.equal(r.rows[0].matches,false);assert.notEqual(r.rows[0].sha256,r.rows[0].expected.sha256);return {readbackPassed:r.passed,observedPaths:[...r.plannedPaths]};});
 for(const invalid of [{name:'request-missing',id:undefined,redirect:0},{name:'request-empty',id:'',redirect:0},{name:'request-number',id:17,redirect:0},{name:'request-object',id:{opaque:'bad'},redirect:0},{name:'request-null',id:null,redirect:0},{name:'redirect-missing',id:'bad-hop',redirect:undefined},{name:'redirect-null',id:'bad-hop',redirect:null},{name:'redirect-string',id:'bad-hop',redirect:'0'},{name:'redirect-negative',id:'bad-hop',redirect:-1},{name:'redirect-fraction',id:'bad-hop',redirect:0.5}]){
  await check('passive-actual-callback-refuses-'+invalid.name,async make=>{const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');const extra={redirectCount:invalid.redirect};before(h,invalid.id,PUBLIC+'index.html',extra);complete(h,invalid.id,PUBLIC+'index.html',extra);const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.checks.passiveRequestsAccounted,false);const bad=x.row.network.observationErrors.filter(e=>e.kind==='INVALID_REQUEST_IDENTITY');assert.equal(bad.length,2);assert.deepEqual(bad[0].rawEvent.params.request,copy({request:invalid.id,url:PUBLIC+'index.html',method:'GET'}));assert.equal(Object.hasOwn(bad[0].rawEvent.params,'redirectCount'),invalid.redirect!==undefined);assert.deepEqual(x.row.network.finalBoundary.invalidRequestIdentities,bad.map(e=>e.eventReceiptId));assert.equal(x.row.network.requests.length,1);return {invalid:invalid.name,consumerStatus:x.row.status,rawMalformedEvents:bad.length};});
 }
 // F-C14-P02: an integrity failure at the actual finalizer must stop the
 // second commissioned preference before acquiring another process. Ordinary
 // observed HTTP/fetch/product failures retain a trustworthy observation route.
 const integrityCases=[
  {name:'unparsed-protocol-message',onClose:({socket})=>socket.emit('message',{data:'{malformed simulation'})},
  {name:'unmatched-protocol-response',onClose:({socket})=>socket.message({id:900001,type:'success',result:{}})},
  {name:'malformed-request-identity',onClose:({event})=>{event('network.beforeRequestSent',undefined);event('network.responseCompleted',undefined,PUBLIC+'index.html',{response:{url:PUBLIC+'index.html',status:200}});}},
  {name:'pending-observed-request',onClose:({event})=>event('network.beforeRequestSent','pending-after-smoke')},
  {name:'unmatched-network-terminal',onClose:({event})=>event('network.responseCompleted','no-begin',PUBLIC+'index.html',{response:{url:PUBLIC+'index.html',status:200}})},
  {name:'absent-observation',omitNetworkEvents:true},
  {name:'capture-failure',onClose:({event,armCaptureFailure})=>{armCaptureFailure();event('network.beforeRequestSent','capture-failed');event('network.responseCompleted','capture-failed',PUBLIC+'index.html',{response:{url:PUBLIC+'index.html',status:200}});}}
 ];
 for(const fault of integrityCases)await check('passive-integrity-blocks-next-actual-consumer-'+fault.name,async make=>{const h=await make(fault),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert.equal(first.row.cleanup.ok,true);if(fault.name!=='capture-failure')assert.equal(first.row.protocolFinalization.ok,true);const second=await h.publicCase('reduce');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);assert.equal(first.row.checks.passiveObservationIntegrity,false);assert.equal(first.row.passiveObservationContinuation.decision,'BLOCK_EQUIVALENT_ENGINE');assert.equal(first.row.passiveObservationContinuation.receipt,first.row.name+'/result.json');assert.equal(h.api.result.engineSetupBlocks.chromium.case,first.row.name);const block=copy(h.api.result.engineSetupBlocks.chromium);assert.equal(second.row.executionStarted,false);assert.equal(h.spawnCount,1);assert.deepEqual(second.row,second.stored);assert.deepEqual(second.row,second.summary);assert.equal(second.row.reference.case,first.row.name);return {fault:fault.name,firstStatus:first.row.status,secondStatus:second.row.status,simulatedNativeAcquisitions:h.spawnCount,engineBlock:block};});
 const ordinaryCases=[
  {name:'http-503',onClose:({event})=>{event('network.beforeRequestSent','http-failure');event('network.responseCompleted','http-failure',PUBLIC+'index.html',{response:{url:PUBLIC+'index.html',status:503}});}},
  {name:'fetch-error',onClose:({event})=>{event('network.beforeRequestSent','fetch-failure');event('network.fetchError','fetch-failure',PUBLIC+'index.html',{errorText:'net::ERR_ABORTED'});}},
  {name:'original-product-assertion',missingCase:true}
 ];
 for(const fault of ordinaryCases)await check('passive-trustworthy-verdict-allows-next-actual-consumer-'+fault.name,async make=>{const h=await make(fault),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert.equal(first.row.protocolFinalization.ok,true);assert.equal(first.row.cleanup.ok,true);assert.equal(first.row.checks.passiveObservationIntegrity,true);assert.equal(first.row.passiveObservationContinuation.decision,'NO_OBSERVATION_INTEGRITY_BLOCK');assert.equal(h.api.result.engineSetupBlocks.chromium,undefined);assert.equal(h.api.launchBlock({engine:'chromium'}),null);const second=await h.publicCase('reduce');equalCuts(second);assert.notEqual(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,2);assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate').length,3);return {fault:fault.name,firstStatus:first.row.status,secondStatus:second.row.status,simulatedNativeAcquisitions:h.spawnCount};});
 // C15 captures provenance on the real owned callback. It supplies no substitute
 // terminals and does not turn a diagnostic mock into native acceptance.
 const diagnosticEvents=['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed','Target.attachedToTarget','Target.detachedFromTarget','Target.targetCreated','Target.targetDestroyed','Target.targetCrashed'].map(e=>'goog:cdp.'+e);
 await check('c15-actual-session-subscribes-to-finite-diagnostics-before-navigation',async make=>{
  const h=await make(),{row,dir}=await h.start();
  await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');
  const subscription=h.sent.find(c=>c.method==='session.subscribe');
  assert.deepEqual(subscription.params.events.filter(e=>e.startsWith('goog:cdp.')),diagnosticEvents);
  assert.equal(h.sent.filter(c=>c.method==='session.subscribe').length,1);
  assert(h.sent.indexOf(subscription)<h.sent.findIndex(c=>c.method==='browsingContext.navigate'));
  assert.equal(h.sent.filter(c=>c.method.startsWith('network.')||c.method.startsWith('goog:cdp.')).length,0);
  const x=await h.finish(row,dir);equalCuts(x);
  assert.equal(x.row.network.diagnosticProvenance.purpose,'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT');
  assert.equal(x.row.network.diagnosticProvenance.transport,'EXISTING_BIDI_CONNECTION_ONLY');
  assert.deepEqual(x.row.network.diagnosticProvenance.events,diagnosticEvents);
  return {diagnosticSubscriptions:diagnosticEvents.length,newConnections:0,networkOrCdpWireCommands:0};
 });
 await check('c15-emitted-bidi-initiator-and-destination-survive-actual-callback-and-cut',async make=>{
  const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');
  const url=PUBLIC+'moon/assets/dem.bin.gz',initiator={type:'script',stackTrace:{callFrames:[{url:PUBLIC+'moon/moon-worker.mjs',functionName:'read',lineNumber:7,columnNumber:2}]}};
  before(h,'provenance',url,{initiator,request:{request:'provenance',url,method:'GET',destination:'empty'}});complete(h,'provenance',url);
  const x=await h.finish(row,dir);equalCuts(x);
  const r=x.row.network.requests.find(r=>r.requestId==='provenance');
  assert.deepEqual(r.beforeEvents[0].initiator,initiator);assert.equal(r.beforeEvents[0].request.destination,'empty');
  assert.equal(r.terminalEvents[0].initiator,null);assert.equal(r.terminalEvents[0].request.destination,null);
  assert.equal(r.context,null);assert.equal(r.navigation,null);
  const recorded=fs.readFileSync(path.join(dir,'network.jsonl'),'utf8').trim().split('\n').map(s=>JSON.parse(s)).find(e=>e.request.id==='provenance');
  assert.deepEqual(recorded,r.beforeEvents[0]);
  return {emittedInitiatorRetained:true,absentFieldsRemainNull:true,ownerInvented:false};
 });
 await check('c15-raw-session-request-target-envelopes-never-replace-missing-bidi-terminal',async make=>{
  const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');before(h,'same-id');
  const rows=[
   ['Network.requestWillBeSent',{session:'worker-a',event:'Network.requestWillBeSent',params:{requestId:'same-id',request:{url:PUBLIC+'index.html'},loaderId:'loader-a'}}],
   ['Network.requestWillBeSent',{session:'worker-b',event:'Network.requestWillBeSent',params:{requestId:'same-id',request:{url:PUBLIC+'index.html'},loaderId:'loader-b'}}],
   ['Network.loadingFinished',{session:'worker-b',event:'Network.loadingFinished',params:{requestId:'same-id',timestamp:2,encodedDataLength:123}}],
   ['Network.loadingFailed',{session:'worker-a',event:'Network.loadingFailed',params:{requestId:'same-id',timestamp:3,errorText:'net::ERR_ABORTED',canceled:true}}],
   ['Target.attachedToTarget',{session:'parent',event:'Target.attachedToTarget',params:{sessionId:'worker-a',targetInfo:{targetId:'target-a',type:'worker'},waitingForDebugger:false}}],
   ['Target.detachedFromTarget',{session:'parent',event:'Target.detachedFromTarget',params:{sessionId:'worker-a',targetId:'target-a'}}],
   ['Target.targetDestroyed',{session:'parent',event:'Target.targetDestroyed',params:{targetId:'target-a'}}],
   ['Target.targetCrashed',{session:'parent',event:'Target.targetCrashed',params:{targetId:'target-b',status:'crashed',errorCode:1}}]
  ];
  for(const [event,params]of rows)h.session.bidi.ws.message({method:'goog:cdp.'+event,params});
  const x=await h.finish(row,dir);equalCuts(x);failed(x);
  const captured=x.row.network.lifecycle.filter(e=>e.method.startsWith('goog:cdp.'));
  assert.deepEqual(captured.map(e=>[e.method.slice('goog:cdp.'.length),e.params]),rows);
  assert(captured.every(e=>e.trace.connectionId===x.row.network.identity.connectionId&&typeof e.trace.eventReceiptId==='string'));
  assert.equal(x.row.network.requests.find(r=>r.requestId==='same-id').terminalEvents.length,0);
  assert.equal(x.row.network.finalBoundary.pendingRequests.length,1);assert.equal(x.row.checks.passiveRequestsAccounted,false);
  const recorded=fs.readFileSync(path.join(dir,'lifecycle.jsonl'),'utf8').trim().split('\n').map(s=>JSON.parse(s));
  assert.deepEqual(recorded,captured);
  return {rawEnvelopes:rows.length,sameIdSessions:2,syntheticTerminals:0,consumerStatus:x.row.status};
 });
 await check('c15-unsupported-extension-refuses-setup-without-fallback-or-navigation',async make=>{
  const h=await make({cdpSubscriptionFailure:true});await assert.rejects(h.start(),/unsupported lifecycle/);
  assert.equal(h.spawnCount,1);assert.equal(h.sent.filter(c=>c.method==='session.subscribe').length,1);
  assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate'||c.method.startsWith('network.')||c.method.startsWith('goog:cdp.')).length,0);
  const row=h.api.result.cases[0];assert.equal(row.cleanup.ok,true);assert.equal(row.protocolFinalization.ok,true);
  assert(row.network.protocolErrors.some(e=>e.protocol?.value?.error==='invalid argument'));
  return {setupRefused:true,cleanup:row.cleanup.ok,fallback:false,navigations:0};
 });
 await check('c15-diagnostic-capture-error-fails-actual-consumer-and-blocks-next-acquisition',async make=>{
  const h=await make({captureFailureFile:'lifecycle.jsonl',onClose:({socket,armCaptureFailure})=>{armCaptureFailure();socket.message({method:'goog:cdp.Network.loadingFinished',params:{session:'worker-a',event:'Network.loadingFinished',params:{requestId:'diagnostic-only',timestamp:1}}});}});
  const first=await h.publicCase('no-preference');equalCuts(first);failed(first);
  assert.equal(first.row.cleanup.ok,true);assert.equal(first.row.checks.passiveObservationIntegrity,false);
  assert(first.row.network.captureErrors.some(e=>e.file==='lifecycle.jsonl'));
  assert.equal(first.row.network.lifecycle.filter(e=>e.method==='goog:cdp.Network.loadingFinished').length,1);
  const second=await h.publicCase('reduce');assert.equal(second.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);
  return {captureFailureRetained:true,secondStatus:second.row.status,simulatedAcquisitions:h.spawnCount};
 });
 await check('c15-diagnostic-success-cannot-erase-observed-fetch-error',async make=>{
  const h=await make(),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');before(h,'failed');
  h.event('network.fetchError','failed',PUBLIC+'index.html',{errorText:'net::ERR_ABORTED'});
  h.session.bidi.ws.message({method:'goog:cdp.Network.loadingFinished',params:{session:'worker-a',event:'Network.loadingFinished',params:{requestId:'failed',timestamp:1}}});
  const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.checks.passiveRequestsAccounted,true);
  assert.equal(x.row.network.fetchErrors[0].errorText,'net::ERR_ABORTED');assert.equal(x.row.checks.passiveObservationClean,false);
  return {fetchErrorRetained:true,consumerStatus:x.row.status};
 });

 // C17: execute the actual configured preload against simulated browser
 // primitives, then retain its raw debug events through the real observer.
 await check('c17-option-is-explicit-exact-and-requires-security-correlation',async()=>{
  const entry=require(entryFile),args=['--network-observation','passive','--groups','public','--cases',selected.join(','),'--base-file',baseFile,'--base-sha',hash(base),'--root',root,'--out','simulation'];
  assert.equal(entry.parse([...args,'--security-provenance','csp','--image-assignment-provenance','src'])['image-assignment-provenance'],'src');
  assert.equal(entry.parse(args)['image-assignment-provenance'],undefined);
  for(const value of ['all','off','SRC','decode'])assert.throws(()=>entry.parse([...args,'--security-provenance','csp','--image-assignment-provenance',value]));
  assert.throws(()=>entry.parse([...args,'--image-assignment-provenance','src']));
  assert.throws(()=>entry.configure({startSession(){},preload(){}},{...imageOptions(),'image-assignment-provenance':'all'}));
  return {explicitMode:'src',requiresSecurity:true};
 });
 await check('c17-unselected-default-keeps-original-preload-function-and-bytes',async make=>{
  const h=await make(),original=h.api.preload,seed=h.api.seeds('absent'),bytes=original(seed,PUBLIC,false);
  require(entryFile).configure(h.api,{groups:'public',cases:selected.join(','),'network-observation':'passive','security-provenance':'csp'});
  assert.equal(h.api.preload,original);assert.equal(h.api.preload(seed,PUBLIC,false),bytes);
  const r=imageRealm(bytes);assert.equal(Object.getOwnPropertyDescriptor(r.ImageElement.prototype,'src').set,r.originalSet);assert.equal(r.markers().length,0);
  return {defaultPreloadUnchanged:true};
 });
 await check('c17-configured-preload-preserves-original-storage-and-origin-fence',async make=>{
  const h=await make(),preload=configuredImagePreload(h),r=imageRealm(preload);
  assert.equal(r.ctx.__r0017Recorder.schema,'r0017-storage/v1');assert.deepEqual(copy(r.ctx.__r0017Recorder.before),publicAbsentSeed(h));assert.equal(r.storage.size,0);
  assert.equal(r.ctx.__r0017Recorder.entries.filter(e=>e.event==='document-preload').length,1);assert.equal(r.markers().filter(e=>e.event==='installed').length,1);
  const foreign=imageRealm(preload,{foreign:true});assert.equal(foreign.ctx.__r0017Recorder,undefined);assert.equal(foreign.logs.length,0);assert.equal(Object.getOwnPropertyDescriptor(foreign.ImageElement.prototype,'src').set,foreign.originalSet);
  return {originalStoragePreloadOnce:true,publicSeedWrites:0,foreignMutation:false};
 });
 await check('c17-wrapper-preserves-original-preload-return-and-exception',async()=>{
  const entry=require(entryFile),api={startSession(){},preload(){return '()=>{window.originalCalls++;return 91;}';}};
  entry.configure(api,imageOptions());const r=imageRealm(api.preload({},PUBLIC,false));assert.equal(r.returnValue,91);assert.equal(r.ctx.originalCalls,1);assert.equal(r.markers().filter(e=>e.event==='installed').length,1);
  const throwing={startSession(){},preload(){return '()=>{window.originalCalls++;throw Error("original-preload-failure");}';}};
  entry.configure(throwing,imageOptions());assert.throws(()=>imageRealm(throwing.preload({},PUBLIC,false)),/original-preload-failure/);
  return {originalReturnPreserved:true,originalExceptionPreserved:true};
 });
 await check('c17-full-string-stack-and-image-sequence-bind-assignment-and-empty-cancellation',async make=>{
  const h=await make(),r=imageRealm(configuredImagePreload(h));r.ctx.__widgetFixture={run:'run-c17',attempt:15,documentId:'fixture-15',hash:'original-hash',mode:'healthy',sourceSha256:'a'.repeat(64)};
  const full='data:image/png;base64,'+'A'.repeat(39064),a=new r.ImageElement(),b=new r.ImageElement(),desc=Object.getOwnPropertyDescriptor(r.ImageElement.prototype,'src');
  assert.equal(desc.get,r.originalGet);assert.equal(desc.enumerable,true);assert.equal(desc.configurable,true);assert.notEqual(desc.set,r.originalSet);
  function actualPublishingCaller(){return desc.set.call(a,full);}assert.equal(actualPublishingCaller(),73);desc.set.call(a,'');desc.set.call(b,full);
  const rows=r.markers().filter(e=>e.event==='setter-invocation-attempt');assert.equal(rows.length,3);assert.equal(rows[0].assignedString,full);assert.equal(rows[1].assignedString,'');assert.equal(rows[0].imageId,rows[1].imageId);assert.notEqual(rows[0].imageId,rows[2].imageId);
  assert(rows[0].stack.includes('actualPublishingCaller'));assert.equal(rows[0].fixture.documentId,'fixture-15');assert.equal(rows[0].fixture.attempt,15);
  assert.equal(rows[0].purpose,'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT');assert.equal(rows[0].phase,'BEFORE_NATIVE_SETTER');assert(rows.every(e=>e.realmNonce==='simulated-realm-0001'));
  assert(rows.every((e,i)=>i===0||e.sequence>rows[i-1].sequence));assert.equal(r.calls.length,3);assert.equal(r.calls[0].receiver,a);assert.equal(r.calls[0].value,full);
  return {fullStringCodeUnits:full.length,imageIds:2,assignments:3,acceptanceCredit:false};
 });
 await check('c17-nonstring-coercion-receiver-and-native-exception-preserved-exactly-once',async make=>{
  const h=await make(),r=imageRealm(configuredImagePreload(h)),a=new r.ImageElement(),setter=Object.getOwnPropertyDescriptor(r.ImageElement.prototype,'src').set;let coercions=0;
  const value={toString(){coercions++;return 'coerced-by-native-only';}};assert.equal(setter.call(a,value),73);assert.equal(coercions,1);assert.equal(r.calls[0].value,value);assert.equal(a.src,'coerced-by-native-only');
  assert.throws(()=>setter.call(a,'throw-native'),e=>e===r.nativeFailure);assert.throws(()=>setter.call(null,'invalid-receiver'),e=>e===r.nativeFailure);assert.equal(r.calls.length,3);
  const row=r.markers().find(e=>e.event==='setter-invocation-attempt'&&e.valueType==='object');assert(row);assert.equal(Object.hasOwn(row,'assignedString'),false);assert.equal(row.stringCoverage,'NON_STRING_NOT_COERCED');
  return {coercions:1,nativeCalls:3,nativeExceptionIdentityPreserved:true};
 });
 await check('c17-console-failure-cannot-skip-or-double-native-setter-and-is-visible-later',async make=>{
  const h=await make(),r=imageRealm(configuredImagePreload(h),{debugFailures:2}),a=new r.ImageElement();a.src='first';a.src='second';
  assert.equal(r.calls.length,2);assert.equal(a.src,'second');const row=r.markers().find(e=>e.assignedString==='second');assert(row);assert(row.recordingFailuresBefore>=2);assert(row.sequence>=3);
  return {nativeCalls:2,priorRecordingFailuresVisible:true};
 });
 await check('c17-installation-failure-is-diagnostic-and-leaves-native-setter-usable',async make=>{
  const h=await make(),r=imageRealm(configuredImagePreload(h),{nonconfigurable:true}),a=new r.ImageElement();a.src='native-still-works';
  assert.equal(a.src,'native-still-works');assert.equal(r.calls.length,1);assert.equal(Object.getOwnPropertyDescriptor(r.ImageElement.prototype,'src').set,r.originalSet);
  assert(r.markers().some(e=>e.event==='installation-failed'));assert.equal(r.markers().filter(e=>e.event==='installed').length,0);
  return {diagnosticFailureRetained:true,originalSetterRetained:true};
 });
 await check('c17-real-clocks-console-and-prototype-survive-fixture-clock-and-document-open',async make=>{
  const h=await make(),r=imageRealm(configuredImagePreload(h));r.ctx.Date.now=()=>-100;r.ctx.performance.now=()=>-200;r.ctx.console.debug=()=>{throw Error('replacement console must not be used');};
  assert.equal(r.ctx.document.open,r.originalOpen);r.ctx.document.open();const a=new r.ImageElement();a.src='after-document-open';
  const row=r.markers().find(e=>e.assignedString==='after-document-open');assert(row);assert.equal(row.realEpochMs,1794284293000);assert.equal(row.realPerformanceMs,123.5);assert.equal(r.listeners.length,0);assert.equal(r.openCalls,1);
  return {capturedRealClocks:true,additionalLifecycleListeners:0,documentOpenReplaced:false,simulationOnly:true};
 });
 await check('c17-actual-public-consumer-retains-exact-combined-preload-and-diagnostic-binding',async make=>{
  const h=await make({securityProvenance:'csp',imageAssignmentProvenance:'src'}),x=await h.publicCase('no-preference');equalCuts(x);
  const sent=h.sent.filter(c=>c.method==='script.addPreloadScript');assert.equal(sent.length,1);const source=sent[0].params.functionDeclaration;
  const saved=fs.readFileSync(path.join(h.home,'receipts',x.row.name,'preload.js'),'utf8');assert.equal(saved,source+'\n');assert.equal(x.row.preloadSha256,hash(source));assert(source.includes(IMAGE_MARKER));
  assert.equal(x.row.imageAssignmentProvenance.purpose,'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT');assert.equal(x.row.imageAssignmentProvenance.probeSourceSha256,hash(require(entryFile).imageAssignmentProbe.toString()));
  assert.equal(h.sent.filter(c=>c.method.startsWith('goog:cdp.')).length,3);assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate').length,2);
  assert.equal(x.row.checks.fullOriginalHealthy,true);assert.equal(x.row.smoke.pass,141);assert.equal(x.row.smoke.required.executed,30);
  const r=imageRealm(source);const a=new r.ImageElement();a.src='data:image/png;base64,YQ==';assert(r.markers().some(e=>e.assignedString==='data:image/png;base64,YQ=='));
  return {preloadByteIdentity:true,existingCdpCommands:3,newConnections:0,nativeExecutions:0};
 });
 await check('c17-real-callback-keeps-full-debug-marker-and-all-raw-failures-at-final-cut',async make=>{
  const h=await make({securityProvenance:'csp'}),preload=configuredImagePreload(h);
  // configure above is the sole owner; use the actual configured start directly.
  const row={name:'c17-debug-simulation',engine:'chromium',status:'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE',stage:'observation',plannedTopLevelDocuments:1,checks:{},screenshots:[{sha256:'simulated'}]},dir=path.join(h.home,'receipts',row.name);fs.mkdirSync(dir);h.api.result.cases.push(row);
  await h.api.startSession('chromium','reduce',{width:1100,height:900},1,row,dir,PUBLIC);await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');
  const r=imageRealm(preload,{onLog:text=>h.session.bidi.ws.message({method:'log.entryAdded',params:{type:'console',method:'debug',level:'debug',source:{realm:'simulated-image-realm',context:'simulated-top'},timestamp:1794284293000,args:[{type:'string',value:text}],text}})});
  const a=new r.ImageElement(),full='data:image/png;base64,'+'B'.repeat(39064);a.src=full;
  before(h,'failed-csp',full);h.event('network.fetchError','failed-csp',full,{errorText:''});before(h,'unfinished');const x=await h.finish(row,dir);equalCuts(x);failed(x);
  const logs=fs.readFileSync(path.join(dir,'console.jsonl'),'utf8').trim().split('\n').map(v=>JSON.parse(v)),marker=logs.find(e=>e.args?.[0]?.value?.includes(full));assert(marker);assert.equal(marker.source.realm,'simulated-image-realm');assert(marker.trace.eventReceiptId);
  assert.equal(x.row.network.consoleErrors.length,0);assert.equal(x.row.network.fetchErrors.length,1);assert.equal(x.row.network.requests.find(q=>q.requestId==='unfinished').terminalEvents.length,0);assert.equal(x.row.checks.passiveObservationIntegrity,false);assert.equal(x.row.checks.passiveObservationClean,false);
  const next=await h.publicCase('reduce');assert.equal(next.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);
  return {rawFullDebugRetained:true,cspAndPendingRetained:true,next:next.row.status};
 });
 await check('c17-diagnostic-opt-in-never-supplies-missing-original-case-credit',async make=>{
  const h=await make({securityProvenance:'csp',imageAssignmentProvenance:'src',missingCase:true}),x=await h.publicCase('reduce');equalCuts(x);failed(x);assert.equal(x.row.smoke.required.executed,29);assert.equal(x.row.checks.fullOriginalHealthy,false);
  return {missingCaseRemainsFailure:true,nativeExecutions:0};
 });

 // C16: opt-in security diagnostic. Real entry/session/consumer/finalizer,
 // mocked OS/socket boundaries; added telemetry never supplies acceptance.
 await check('c16-explicit-option-is-exact-and-default-remains-unselected',async()=>{
  const entry=require(entryFile),args=['--network-observation','passive','--groups','public','--cases',selected.join(','),'--base-file',baseFile,'--base-sha',hash(base),'--root',root,'--out','simulation'];
  assert.equal(entry.parse([...args,'--security-provenance','csp'])['security-provenance'],'csp');
  assert.equal(entry.parse(args)['security-provenance'],undefined);
  for(const value of ['all','off','CSP','network'])assert.throws(()=>entry.parse([...args,'--security-provenance',value]));
  return {mode:'csp',default:'unselected'};
 });
 await check('c16-actual-consumer-enables-only-two-domains-on-owned-session-before-navigation-and-retains-early-replay',async make=>{
  const h=await make({securityProvenance:'csp',securityReplay:true}),x=await h.publicCase('no-preference');equalCuts(x);
  const s=x.row.network.securityProvenance;assert.equal(s.status,'ENABLED_BEFORE_MEANINGFUL_NAVIGATION');assert.equal(s.context,'simulated-top');assert.equal(s.session,'simulated-owned-cdp');assert.equal(s.purpose,'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT');
  const cdp=h.sent.filter(c=>c.method.startsWith('goog:cdp.'));assert.deepEqual(cdp.map(c=>[c.method,c.params]),[['goog:cdp.getSession',{context:'simulated-top'}],['goog:cdp.sendCommand',{method:'Log.enable',params:{},session:'simulated-owned-cdp'}],['goog:cdp.sendCommand',{method:'Audits.enable',params:{},session:'simulated-owned-cdp'}]]);
  const sub=h.sent.findIndex(c=>c.method==='session.subscribe'),firstCdp=h.sent.findIndex(c=>c.method.startsWith('goog:cdp.')),lastCdp=h.sent.findLastIndex(c=>c.method.startsWith('goog:cdp.')),nav=h.sent.findIndex(c=>c.method==='browsingContext.navigate');assert(sub<firstCdp&&lastCdp<nav);
  assert.deepEqual(s.commands.map(c=>c.method),['browsingContext.getTree','goog:cdp.getSession','goog:cdp.sendCommand','goog:cdp.sendCommand']);assert(s.commands.every(c=>c.status==='SUCCEEDED'&&c.issued?.command?.commandReceiptId===c.response?.command?.commandReceiptId&&c.response?.association==='pending'));
  const events=h.sent[sub].params.events;for(const e of ['Log.entryAdded','Audits.issueAdded','Page.frameNavigated','Page.frameDetached','Page.documentOpened','Runtime.executionContextCreated','Runtime.executionContextDestroyed','Runtime.executionContextsCleared'])assert(events.includes('goog:cdp.'+e));
  const raw=x.row.network.lifecycle.filter(e=>['goog:cdp.Log.entryAdded','goog:cdp.Audits.issueAdded'].includes(e.method));assert.equal(raw.length,2);assert(raw.every(e=>e.params.session==='simulated-owned-cdp'));assert.equal(raw[1].params.params.issue.details.contentSecurityPolicyIssueDetails.violatedDirective,'img-src');
  const traces=fs.readFileSync(path.join(h.home,'receipts',x.row.name,'bidi-trace.jsonl'),'utf8').trim().split('\n').map(v=>JSON.parse(v));
  for(let i=0;i<2;i++){const receipt=traces.find(e=>e.kind==='event-observed'&&e.eventReceiptId===raw[i].trace.eventReceiptId);assert(receipt);assert(receipt.traceSequence<s.commands[i+2].response.traceSequence);}
  const stored=fs.readFileSync(path.join(h.home,'receipts',x.row.name,'lifecycle.jsonl'),'utf8').trim().split('\n').map(v=>JSON.parse(v));for(const e of raw)assert(stored.some(v=>v.trace.eventReceiptId===e.trace.eventReceiptId));
  assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);assert.equal(x.row.checks.fullOriginalHealthy,true);assert.equal(x.row.nativeExecutions,0);
  return {domains:['Log','Audits'],sameOwnedConnection:true,earlyReplayRetained:2,nativeExecutions:0};
 });
 for(const fault of [
  {name:'missing-session',missingCdpSession:true},
  {name:'ambiguous-top-context',ambiguousTop:true},
  {name:'wrong-response-session',wrongCdpSession:true},
  {name:'log-enable-unsupported',securityCommandFailure:'Log.enable'},
  {name:'audits-enable-unsupported',securityCommandFailure:'Audits.enable'}
 ])await check('c16-security-setup-refuses-'+fault.name+'-with-owned-cleanup',async make=>{
  const h=await make({securityProvenance:'csp',...fault}),x=await h.publicCase('no-preference');failed(x);equalCuts(x);
  assert.equal(x.row.network.securityProvenance.status,'FAILED');assert.equal(x.row.cleanup.ok,true);assert.equal(x.row.protocolFinalization.ok,true);assert.equal(h.sent.filter(c=>c.method==='browsingContext.navigate').length,0);
  assert.equal(h.sent.filter(c=>c.method.startsWith('network.')).length,0);const next=await h.publicCase('reduce');assert.equal(next.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);
  return {fault:fault.name,cleanup:x.row.cleanup.status,next:next.row.status,simulatedAcquisitions:1};
 });
 await check('c16-unapproved-cdp-commands-are-refused-before-wire',async make=>{
  const h=await make({securityProvenance:'csp'}),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');
  for(const params of [{method:'Network.enable',params:{},session:'simulated-owned-cdp'},{method:'Log.enable',params:{},session:'another-session'}])await assert.rejects(h.session.bidi.call('goog:cdp.sendCommand',params),/refused|diagnostic/i);
  const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(h.sent.filter(c=>c.method==='goog:cdp.sendCommand').length,2);assert.equal(x.row.network.commandRefusals.length,2);
  return {unapprovedWireCommands:0,refusals:2};
 });
 await check('c16-csp-diagnostic-does-not-excuse-fetch-error-or-invent-terminal',async make=>{
  const h=await make({securityProvenance:'csp',securityReplay:true}),{row,dir}=await h.start();await h.session.navigate(PUBLIC+'tests/smoke.html?fixture=healthy');before(h,'failed-image','data:image/png;base64,YQ==');h.event('network.fetchError','failed-image','data:image/png;base64,YQ==',{errorText:''});before(h,'still-pending');
  const x=await h.finish(row,dir);equalCuts(x);failed(x);assert.equal(x.row.network.fetchErrors.length,1);assert.equal(x.row.checks.passiveObservationClean,false);assert.equal(x.row.checks.passiveRequestsAccounted,false);assert.equal(x.row.network.requests.find(r=>r.requestId==='still-pending').terminalEvents.length,0);
  return {rawFetchErrors:1,rawPending:1,acceptanceRelaxation:false};
 });
 await check('c16-security-capture-failure-is-retained-and-blocks-next-acquisition',async make=>{
  const h=await make({securityProvenance:'csp',captureFailureFile:'lifecycle.jsonl',onClose:({socket,armCaptureFailure})=>{armCaptureFailure();socket.message({method:'goog:cdp.Log.entryAdded',params:{session:'simulated-owned-cdp',event:'Log.entryAdded',params:{entry:{source:'security',level:'error',text:'SIMULATED late CSP',timestamp:1794089691000}}}});}}),first=await h.publicCase('no-preference');equalCuts(first);failed(first);assert(first.row.network.captureErrors.some(e=>e.file==='lifecycle.jsonl'));assert.equal(first.row.checks.passiveObservationIntegrity,false);
  const next=await h.publicCase('reduce');assert.equal(next.row.status,'NOT_ATTEMPTED');assert.equal(h.spawnCount,1);return {captureFailureRetained:true,next:next.row.status};
 });
 const report={schema:'r0017-passive-observation-controls/v1',nativeExecutions:0,simulationOnly:true,baseSha256:hash(base),phase2Sha256:hash(phase),entrySha256:fs.existsSync(entryFile)?hash(fs.readFileSync(entryFile)):null,methodSha256:fs.existsSync(methodFile)?hash(fs.readFileSync(methodFile)):null,testSha256:hash(fs.readFileSync(__filename)),passed:results.filter(x=>x.passed).length,failed:results.filter(x=>!x.passed).length,results};console.log(JSON.stringify(report,null,2));process.exitCode=report.failed?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
