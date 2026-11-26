'use strict';
// Offline behavior controls. The actual pinned sampler runs in deterministic
// JavaScript contexts; no browser, namespace or native capture is executed.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const samplerPath=path.join(__dirname,'r0040_passive_sampler.cjs');
function sampler(){assert.ok(fs.existsSync(samplerPath),'passive sampler module has not been implemented');return require(samplerPath);}
const source=fs.readFileSync(path.resolve(__dirname,'../r0040/capture.cjs'),'utf8');
const starts=[...source.matchAll(/await isolated\(`([\s\S]*?)`\);/g)];
assert.equal(starts.length,1,'one original isolated sampler expression required');
const original=starts[0][1],stop='globalThis.active=false; globalThis.samples';
const plain=value=>JSON.parse(JSON.stringify(value));

function runExpression(expression,{times=[[10,12],[20,25],[30,31]],clockFault=false,dispatchError=null}={}){
  const queue=[],calls=[],clock={at:0,reads:0};
  const bus={textContent:'',dispatchEvent(event){
    calls.push(['dispatch',event.type]);if(dispatchError)throw dispatchError;
    clock.at+=2;this.textContent=JSON.stringify({phaseMs:clock.at+200,poseMs:clock.at/2,tuple:['synthetic']});
  }};
  const context=vm.createContext({document:{querySelector(selector){assert.equal(selector,'#r0040-audit');return bus;}},
    Event:class{constructor(type){this.type=type;}},
    performance:{timeOrigin:1000,now(){clock.reads++;if(clockFault&&clock.reads===1)throw Error('synthetic supplemental clock fault');return clock.at;}},
    requestAnimationFrame(callback){calls.push(['request-rAF']);queue.push(callback);return queue.length;}});
  assert.equal(vm.runInContext(expression,context),true);
  let primary=null;
  for(const [timestamp,entry]of times){clock.at=entry;try{queue.shift()(timestamp);}catch(error){primary=error;break;}}
  const samples=plain(vm.runInContext(stop,context));
  if(queue.length)queue.shift()(999);
  return {samples,calls,primary,raw:plain(vm.runInContext('globalThis.__R0040_PASSIVE_SAMPLER__??null',context)),clockReads:clock.reads};
}

test('instrumented actual sampler preserves every original sample and rAF scheduling action',()=>{
  const S=sampler(),transformed=S.instrumentStart(original),baseline=runExpression(original),observed=runExpression(transformed.expression);
  assert.deepEqual(observed.samples,baseline.samples);assert.deepEqual(observed.calls,baseline.calls);
  assert.deepEqual(observed.samples,[
    {phaseMs:214,poseMs:7,tuple:['synthetic'],at:1010},
    {phaseMs:227,poseMs:13.5,tuple:['synthetic'],at:1020},
    {phaseMs:233,poseMs:16.5,tuple:['synthetic'],at:1030}]);
  assert.deepEqual(observed.raw.rows,[[0,10,12,14],[1,20,25,27],[2,30,31,33]]);
  assert.equal(S.reverseStart(transformed.expression),original);
  const inspected=S.inspectSampler(observed.raw);
  assert.equal(inspected.status,'OBSERVED');assert.equal(inspected.clockDomain,'isolated-performance');
  assert.deepEqual(inspected.intervals,[
    {ordinal:0,callbackLagMs:2,synchronousDispatchMs:2},
    {ordinal:1,callbackLagMs:5,synchronousDispatchMs:2},
    {ordinal:2,callbackLagMs:1,synchronousDispatchMs:2}]);
});

test('source drift refuses a sampler extension before evaluating substituted code',()=>{
  const S=sampler();
  for(const changed of [original+' ',original.replace('requestAnimationFrame(read)','setTimeout(read,1)'),original.replace('samples.push','other.push')])
    assert.throws(()=>S.instrumentStart(changed),/source|digest|sampler/);
  assert.throws(()=>S.reverseStart(original),/extension|reversal|sampler/);
});

test('bounded supplemental overflow retains its prefix and every original sample',()=>{
  const S=sampler(),times=Array.from({length:4098},(_,i)=>[i*10,i*10+1]);
  const originalRun=runExpression(original,{times}),observed=runExpression(S.instrumentStart(original).expression,{times});
  assert.deepEqual(observed.samples,originalRun.samples);assert.deepEqual(observed.calls,originalRun.calls);
  assert.equal(observed.samples.length,4098);assert.equal(observed.raw.rows.length,4096);assert.equal(observed.raw.dropped,2);
  assert.deepEqual(observed.raw.rows[0],[0,0,1,3]);assert.deepEqual(observed.raw.rows.at(-1),[4095,40950,40951,40953]);
  assert.throws(()=>S.inspectSampler(observed.raw),/overflow|incomplete/);
});

test('supplemental clock failure cannot suppress the original dispatch sample or scheduling',()=>{
  const S=sampler(),baseline=runExpression(original),observed=runExpression(S.instrumentStart(original).expression,{clockFault:true});
  assert.deepEqual(observed.samples,baseline.samples);assert.deepEqual(observed.calls,baseline.calls);
  assert.equal(observed.primary,null);assert.equal(observed.raw.faults,1);assert.equal(observed.raw.rows[0][2],null);
  assert.throws(()=>S.inspectSampler(observed.raw),/fault|incomplete/);
});

test('primary original dispatch exception remains the same exception with an honest prefix',()=>{
  const S=sampler(),primary=Error('synthetic original dispatch exception');
  const baseline=runExpression(original,{dispatchError:primary}),observed=runExpression(S.instrumentStart(original).expression,{dispatchError:primary});
  assert.equal(observed.primary,primary);assert.equal(baseline.primary,primary);
  assert.deepEqual(observed.samples,baseline.samples);assert.deepEqual(observed.calls,baseline.calls);
  assert.deepEqual(observed.raw.rows,[]);
});

test('inspector separates structural validity from any cadence or product gate',()=>{
  const S=sampler(),observed=runExpression(S.instrumentStart(original).expression);
  const delayed=plain(observed.raw);delayed.rows=[[0,10,5010,15010]];
  const result=S.inspectSampler(delayed);assert.equal(result.status,'OBSERVED');
  assert.deepEqual(result.intervals,[{ordinal:0,callbackLagMs:5000,synchronousDispatchMs:10000}]);
  for(const mutate of [x=>x.clockDomain='host',x=>x.rows[0][0]=2,x=>x.rows[0][3]=null,x=>x.rows[0][2]=Infinity]){
    const changed=plain(observed.raw);mutate(changed);assert.throws(()=>S.inspectSampler(changed));
  }
});

const runtimePath=path.join(__dirname,'r0040_passive_runtime.cjs');
function runtime(){assert.ok(fs.existsSync(runtimePath),'passive runtime module has not been implemented');return require(runtimePath);}
function workerContext(){
  const calls=[],constructorError=Error('synthetic constructor fault'),methodError=Error('synthetic Worker method fault');
  const result={nativeResult:true};let now=100;
  class NativeWorker extends EventTarget {
    constructor(...args){super();calls.push(['construct',args,new.target]);if(args[0]==='throw')throw constructorError;this.url=args[0];}
    postMessage(...args){calls.push(['postMessage',this,args]);if(args[0]==='throw')throw methodError;return result;}
    terminate(...args){calls.push(['terminate',this,args]);if(args[0]==='throw')throw methodError;return result;}
  }
  const context=vm.createContext({Worker:NativeWorker,performance:{timeOrigin:1000,now:()=>now++}});
  vm.runInContext('globalThis.window=globalThis',context);
  vm.runInContext('('+runtime().installWorkerObserver.toString()+')()',context);
  const Wrapped=vm.runInContext('Worker',context),snapshot=()=>plain(vm.runInContext('__R0040_PASSIVE_WORKERS__.snapshot()',context));
  return {context,calls,constructorError,methodError,result,NativeWorker,Wrapped,snapshot};
}
function workerMessage(worker,data,type='message'){
  const event=new Event(type);Object.defineProperty(event,'data',{value:data});worker.dispatchEvent(event);return event;
}

test('Worker construction methods receivers returns and primary exceptions preserve the native API',()=>{
  const x=workerContext(),options={name:'synthetic'},worker=new x.Wrapped('blob:synthetic',options);
  assert.ok(worker instanceof x.NativeWorker);assert.ok(worker instanceof x.Wrapped);
  assert.equal(x.Wrapped.prototype,x.NativeWorker.prototype);assert.equal(x.calls[0][1][1],options);
  class Derived extends x.Wrapped{}const derived=new Derived('blob:derived');assert.ok(derived instanceof Derived);
  const payload={kind:'boot',offline:false,cache:'force-cache',workerSource:'synthetic source'},transfer=[];
  assert.equal(worker.postMessage(payload,transfer),x.result);assert.equal(x.calls.at(-1)[1],worker);
  assert.equal(x.calls.at(-1)[2][0],payload);assert.equal(x.calls.at(-1)[2][1],transfer);
  assert.equal(worker.terminate(),x.result);
  for(const action of [()=>new x.Wrapped('throw'),()=>worker.postMessage('throw'),()=>worker.terminate('throw')])
    assert.throws(action,error=>error===x.constructorError||error===x.methodError);
  assert.throws(()=>x.Wrapped('without-new'),TypeError);
  const other={receiver:true};assert.equal(worker.postMessage.call(other,payload),x.result);assert.equal(x.calls.at(-1)[1],other);
  const raw=x.snapshot();assert.equal(raw.clockDomain,'main-performance');assert.equal(raw.workersConstructed,2);
  assert.ok(raw.events.some(row=>row.event==='worker-construction-threw'));
  assert.ok(raw.events.some(row=>row.event==='worker-post'&&row.kind==='boot'&&row.workerSourceLength===16));
  assert.ok(raw.events.some(row=>row.event==='worker-terminate-threw'));
  assert.equal(JSON.stringify(raw).includes('synthetic source'),false);
});

test('Worker observation reads only admitted primitive metadata and never payload arrays or getters',()=>{
  const x=workerContext(),worker=new x.Wrapped('blob:synthetic');let delivered=0;
  worker.addEventListener('message',()=>delivered++);
  const untouched=()=>{throw Error('payload getter must not be read');};
  const data={kind:'preview',id:3};for(const key of ['rgba','surfaceLinear','surfaceCoverage','calendarRgba','diagnostics','scene','error'])
    Object.defineProperty(data,key,{get:untouched});
  workerMessage(worker,data);assert.equal(delivered,1);
  const boot={kind:'boot',offline:true,cache:'no-cache'};Object.defineProperty(boot,'workerSource',{get:untouched});
  assert.equal(worker.postMessage(boot),x.result);
  workerMessage(worker,{kind:'boot-error',error:'synthetic boot error'});
  const raw=x.snapshot();assert.equal(raw.faults,0);
  assert.ok(raw.events.some(row=>row.event==='worker-message'&&row.kind==='preview'&&row.id===3));
  assert.ok(raw.events.some(row=>row.event==='worker-message'&&row.kind==='boot-error'&&row.error==='synthetic boot error'));
  assert.equal(runtime().inspectRuntime({protocol:'r0040-passive-runtime-snapshot/1',clockDomain:'main-performance',
    timeOriginMs:1000,performanceBeforeMs:10,performanceAfterMs:10000,observer:raw,runtime:{availability:'ABSENT'}}).status,'OBSERVED');
});

test('Worker observation overflow keeps a bounded raw prefix without suppressing native messages',()=>{
  const x=workerContext(),worker=new x.Wrapped('blob:synthetic');let delivered=0;
  worker.addEventListener('message',()=>delivered++);
  for(let i=0;i<2050;i++)workerMessage(worker,{kind:'progress',id:7,stage:'synthetic',row:i,total:2050});
  const raw=x.snapshot();assert.equal(delivered,2050);assert.equal(raw.events.length,2048);assert.ok(raw.dropped>0);
  assert.equal(raw.events[0].event,'observer-installed');assert.equal(raw.events[1].event,'worker-constructed');
  assert.throws(()=>runtime().inspectRuntime({protocol:'r0040-passive-runtime-snapshot/1',clockDomain:'main-performance',
    timeOriginMs:1000,performanceBeforeMs:10,performanceAfterMs:10000,observer:raw,runtime:{availability:'ABSENT'}}),/overflow|incomplete/);
});

test('runtime snapshot uses only passive observe and disposed while retaining observer prefix on observation failure',()=>{
  const x=workerContext();let reads=0,disposedReads=0;
  const state={status:'unavailable',workerAlive:false,retryCount:0,renders:0,rejected:1,cancelled:1,
    recovery:{state:'scheduled',attempts:0,limit:3,nextAt:30100,lastClass:'boot',outcome:null},
    progress:{stage:'synthetic',row:2,total:3},errors:['synthetic failure']};
  const observed={accepted:false,waitingPreview:false,current:false,wouldPresent:false,state};
  Object.defineProperty(observed,'surface',{get(){throw Error('surface must not be read');}});
  const moon={observe(){reads++;return observed;},get disposed(){disposedReads++;return false;}};
  for(const name of ['state','surface','detailEnabled','retry','refresh','dispose'])Object.defineProperty(moon,name,{get(){throw Error('active runtime access '+name);}});
  x.context.SalahMoonRuntime=moon;
  const snapshot=()=>plain(vm.runInContext('('+runtime().snapshotPassiveRuntime.toString()+')()',x.context));
  const raw=snapshot();assert.equal(reads,1);assert.equal(disposedReads,1);assert.equal(raw.runtime.state.status,'unavailable');
  assert.equal(runtime().inspectRuntime(raw).status,'OBSERVED');assert.equal(raw.runtime.state.workerAlive,false);
  moon.observe=()=>{throw Error('synthetic observe failure');};const failed=snapshot();
  assert.equal(failed.runtime.availability,'EVALUATION_FAILED');assert.ok(failed.observer.events.length>0);
  assert.throws(()=>runtime().inspectRuntime(failed),/runtime.*unavailable|incomplete/);
});

const passivePath=path.join(__dirname,'r0040_passive.cjs');
function passive(){assert.ok(fs.existsSync(passivePath),'passive capture adapter has not been implemented');return require(passivePath);}
function passiveRetention(t){
  const root=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'passive-control-')),P=passive(),D=require('./r0040_dateonly.cjs');
  const fixture=fs.readFileSync(path.join(__dirname,'fixtures/r0040-precip-eval-original.txt'));
  const retain=new P.PassiveRetention(path.join(root,'evidence'),{out:path.join(root,'original'),expected:{utcMs:1790154360000},pins:{},
    diagnostic:D.diagnosticIdentity(D.transformHelper(fixture).identity),passive:P.passiveIdentity(path.resolve(__dirname,'../r0040/capture.cjs')),collectionTimeoutMs:30});
  t.after(()=>{retain.journal.close();fs.rmSync(root,{recursive:true,force:true});});return retain;
}

test('CDP adapter preserves ACK promise listeners and original stop response, extracting only after the original stream stop',async t=>{
  const retain=passiveRetention(t),calls=[],callbacks=[],ack=Promise.resolve({ack:true}),stopResult={result:{value:[{original:true}]}},rawTrace=runExpression(sampler().instrumentStart(original).expression).raw;
  const raw={send(method,params){calls.push([method,params]);
    if(method==='Page.screencastFrameAck')return ack;
    if(method==='Page.createIsolatedWorld')return Promise.resolve({executionContextId:9});
    if(method==='Runtime.evaluate')return Promise.resolve(params.expression===stop?stopResult:
      params.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'?{result:{value:rawTrace}}:{result:{value:true}});
    return Promise.resolve({});},on(name,callback){callbacks.push([name,callback]);return this;},detach(){return Promise.resolve('detached');}};
  const cdp=retain.wrapCDP(raw),callback=()=>{};cdp.on('Page.screencastFrame',callback);
  assert.equal(callbacks.length,1);assert.equal(callbacks[0][1],callback);assert.equal(cdp.send('Page.screencastFrameAck',{sessionId:7}),ack);
  await cdp.send('Page.createIsolatedWorld',{worldName:'r0040-native-clock',frameId:'frame'});
  await cdp.send('Runtime.evaluate',{contextId:9,expression:original,returnByValue:true});
  assert.equal(sampler().reverseStart(calls.at(-1)[1].expression),original);
  await cdp.send('Page.startScreencast',{format:'png'});
  assert.equal(calls.filter(row=>row[0]==='Runtime.evaluate').length,1);
  await cdp.send('Page.stopScreencast');
  assert.equal(await cdp.send('Runtime.evaluate',{contextId:9,expression:stop,returnByValue:true}),stopResult);
  assert.equal(calls.at(-1)[1].expression,'globalThis.__R0040_PASSIVE_SAMPLER__??null');
  assert.equal(retain.passive.samplers[0].extractions[0].status,'OBSERVED');
  assert.deepEqual(retain.passive.samplers[0].extractions[0].raw,rawTrace);
  assert.equal(await cdp.detach(),'detached');
});

test('failed or overflowing sampler extraction retains raw prefix without replacing the original stop result',async t=>{
  const retain=passiveRetention(t),rawTrace=runExpression(sampler().instrumentStart(original).expression).raw;
  rawTrace.dropped=2;const stopResult={result:{value:[{original:true}]}};
  const raw={async send(method,params){
    if(method==='Page.createIsolatedWorld')return {executionContextId:9};
    if(method==='Runtime.evaluate')return params.expression===stop?stopResult:
      params.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'?{result:{value:rawTrace}}:{result:{value:true}};
    return {};}};
  const cdp=retain.wrapCDP(raw);await cdp.send('Page.createIsolatedWorld',{worldName:'r0040-native-clock'});
  await cdp.send('Runtime.evaluate',{contextId:9,expression:original,returnByValue:true});
  await cdp.send('Page.startScreencast');await cdp.send('Page.stopScreencast');
  assert.equal(await cdp.send('Runtime.evaluate',{contextId:9,expression:stop,returnByValue:true}),stopResult);
  const extraction=retain.passive.samplers[0].extractions[0];assert.equal(extraction.status,'INCOMPLETE');
  assert.deepEqual(extraction.raw,rawTrace);assert.match(extraction.error.message,/overflow/);
  const events=fs.readFileSync(path.join(retain.journal.directory,'events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  assert.deepEqual(events.find(row=>row.event==='passive-sampler-prefix').observation.raw,rawTrace);
});

test('CDP extension refuses changed source and foreign clock context without sending substituted sampler code',async t=>{
  const retain=passiveRetention(t),calls=[],raw={async send(method,params){calls.push([method,params]);return {executionContextId:9};}};
  const cdp=retain.wrapCDP(raw);await cdp.send('Page.createIsolatedWorld',{worldName:'r0040-native-clock'});
  for(const params of [{contextId:9,expression:original+' ',returnByValue:true},{contextId:8,expression:original,returnByValue:true},
    {contextId:9,expression:original,returnByValue:false}])assert.throws(()=>cdp.send('Runtime.evaluate',params),/sampler|context|source|value/);
  assert.equal(calls.length,1);
});

// Reuse the actual-driver/actual-CRLF-helper control, changing only declared
// browser dependencies. Every seam is unique; the original recipe is never
// copied or altered by this control.
function dateOnlyChildSource(){
  const dated=fs.readFileSync(path.join(__dirname,'r0040_dateonly_controls.cjs'),'utf8');
  const start=dated.indexOf('function childSource(){'),end=dated.indexOf('\nfunction run(t,mode)',start);
  assert.ok(start>=0&&end>start);
  return vm.runInNewContext('('+dated.slice(start,end)+')()',{fs,path,assert,__dirname});
}
function passiveChildSource(){
  let code=dateOnlyChildSource();
  function replace(before,after){assert.equal(code.split(before).length,2,'passive control seam '+before);code=code.replace(before,()=>after);}
  replace("const D=require(entry),{DateOnlyRetention:CaptureRetention,executeOriginal}=D,load=Module.createRequire(driver);",
    "const P=require(entry),D=require(path.join(path.dirname(entry),'r0040_dateonly.cjs')),{PassiveRetention:CaptureRetention,executeOriginal}=P,load=Module.createRequire(driver);");
  replace("const vm=require('node:vm');let proofContext=null,blockedTimer=null;",
    "const vm=require('node:vm');let proofContext=null,blockedTimer=null,workerInstaller=null,samplerContext=null,samplerQueue=[],sampleClock=0,controlWorker=null;");
  replace("page.addInitScript=async(fn,value)=>{if(mode==='install-failure')throw Error('controlled Date-only installation fault');if(fn.name!=='installDateOnly')throw Error('unexpected init script');proofContext=clockContext(value.utcMs);};",
    "page.addInitScript=async(fn,value)=>{\n"+
    "      if(fn.name==='installWorkerObserver'){if(mode==='passive-install-failure')throw Error('controlled passive install fault');workerInstaller=fn;return;}\n"+
    "      if(mode==='install-failure')throw Error('controlled Date-only installation fault');if(fn.name!=='installDateOnly')throw Error('unexpected init script');\n"+
    "      proofContext=clockContext(value.utcMs);proofContext.Worker=class extends EventTarget{postMessage(){} terminate(){}};\n"+
    "      if(!workerInstaller)throw Error('passive installation missing before navigation');vm.runInContext('('+workerInstaller.toString()+')()',proofContext);};");
  replace("const text=String(expression);",
    "const text=String(expression);\n"+
    "      if(expression?.name==='snapshotPassiveRuntime'){if(mode==='runtime-evaluate')throw Error('controlled passive runtime evaluation fault');\n"+
    "        const raw=JSON.parse(JSON.stringify(vm.runInContext('('+expression.toString()+')()',proofContext)));if(mode==='runtime-overflow')raw.observer.dropped=1;return raw;}\n");
  replace("page.goto=async url=>{await routed(url);await routed('https://unknown.invalid/blocked');};",
    "page.goto=async url=>{\n"+
    "      controlWorker=new EventEmitter();controlWorker.url=()=> 'blob:synthetic-worker';page.emit('worker',controlWorker);\n"+
    "      vm.runInContext(\"globalThis.controlWorker=new Worker('blob:synthetic-worker');controlWorker.postMessage({kind:'boot',offline:false,cache:'force-cache',workerSource:'synthetic'});\",proofContext);\n"+
    "      await routed(url);await routed('https://unknown.invalid/blocked');};");
  replace("try{await ctx.handler(raw);ctx.emit('requestfinished',req);}",
    "try{await ctx.handler(raw);if(!trace.aborted.includes(url))ctx.emit('response',{request:()=>req,status:()=>200,statusText:()=> 'OK',fromServiceWorker:()=>false,\n"+
    "        headers:()=>{trace.provisionalHeaderReads=(trace.provisionalHeaderReads||0)+1;return {'content-type':'application/javascript','content-length':'17'};},\n"+
    "        allHeaders(){throw Error('response header RPC forbidden');},body(){throw Error('response body copy forbidden');}});ctx.emit('requestfinished',req);}");
  replace("if(name==='Runtime.evaluate')return {result:{value:args.expression.includes('globalThis.active=false')?[sample,{...sample,at:1017}]:true}};",
    "if(name==='Runtime.evaluate'){\n"+
    "        trace.isolatedCalls=(trace.isolatedCalls||[]);trace.isolatedCalls.push({start:args.expression.includes('globalThis.samples=[]'),stop:args.expression==='globalThis.active=false; globalThis.samples',extract:args.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null',inStream});\n"+
    "        if(args.expression.includes('globalThis.samples=[]')){\n"+
    "          const bus={textContent:'',dispatchEvent(){sampleClock+=2;this.textContent=JSON.stringify(sample);}};\n"+
    "          samplerContext=vm.createContext({document:{querySelector:()=>bus},Event:class{constructor(type){this.type=type;}},performance:{timeOrigin:1000,now:()=>sampleClock},requestAnimationFrame:fn=>{samplerQueue.push(fn);return samplerQueue.length;}});\n"+
    "        }\n"+
    "        if(args.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'&&mode==='sampler-evaluate')throw Error('controlled passive sampler evaluation fault');\n"+
    "        if(args.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'&&mode==='sampler-timeout')return new Promise(()=>{});\n"+
    "        const value=JSON.parse(JSON.stringify(vm.runInContext(args.expression,samplerContext)));\n"+
    "        if(args.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'&&mode==='sampler-overflow')value.dropped=1;\n"+
    "        return {result:{value}};\n"+
    "      }");
  replace("if(name==='Page.startScreencast'){inStream=true;",
    "if(name==='Page.startScreencast'){trace.frameListenerCount=cdp.listenerCount('Page.screencastFrame');\n"+
    "        for(let i=0;i<(mode==='passive-extra-sample'?3:2);i++){sampleClock=i*17+1;samplerQueue.shift()(i*17);}inStream=true;");
  replace("const report=path.join(out,'capture.json');if(fs.existsSync(report))reportBeforeClose=hash(fs.readFileSync(report));",
    "const report=path.join(out,'capture.json');if(fs.existsSync(report))reportBeforeClose=hash(fs.readFileSync(report));\n"+
    "      if(mode==='passive-stop-remove')fs.unlinkSync(path.join(root,'evidence','passive-original-stop-1.json'));\n"+
    "      if(controlWorker)controlWorker.emit('close');\n"+
    "      if(mode==='passive-late-network'){const req={url:()=> 'http://127.0.0.1:8765/late',method:()=> 'GET',resourceType:()=> 'image',failure:()=>({errorText:'late network failure'})};ctx.emit('request',req);await ctx.handler({request:()=>req,async continue(){},async abort(){},async fulfill(){}});ctx.emit('requestfailed',req);}");
  replace("if(mode==='proof-invalid-veto'){", "if(mode==='proof-invalid-veto'||mode==='passive-stop-fsync-veto'){");
  replace("if(mode==='close-failure')throw Error('original context close fault');",
    "if(mode==='close-failure'||mode==='passive-stop-fsync-close')throw Error('original context close fault');");
  replace("diagnostic:D.diagnosticIdentity(D.transformHelper(fs.readFileSync(helper)).identity),proofTimeoutMs:mode==='proof-timeout'?100:5000});",
    "diagnostic:D.diagnosticIdentity(D.transformHelper(fs.readFileSync(helper)).identity),proofTimeoutMs:mode==='proof-timeout'?100:5000,\n"+
    "      passive:P.passiveIdentity(driver),collectionTimeoutMs:100});");
  replace("process.env.R0040_DISPERSION='common';delete process.env.R0040_OPTIONS;",
    "if(mode.startsWith('passive-stop-fsync')){const open=fs.openSync;let stopFd=null;fs.openSync=(file,...args)=>{const fd=open(file,...args);if(String(file).endsWith('passive-original-stop-1.json.pending'))stopFd=fd;return fd;};\n"+
    "      const fsync=fs.fsyncSync;fs.fsyncSync=(fd,...args)=>{if(fd===stopFd){stopFd=null;throw Error('original stop response fsync fault');}return fsync(fd,...args);};}\n"+
    "    if(mode==='passive-receipt-fsync'){const open=fs.openSync;let passiveFd=null;fs.openSync=(file,...args)=>{const fd=open(file,...args);if(String(file).endsWith('passive-observation.json.pending'))passiveFd=fd;return fd;};\n"+
    "      const fsync=fs.fsyncSync;fs.fsyncSync=(fd,...args)=>{if(fd===passiveFd)throw Error('passive final receipt fsync fault');return fsync(fd,...args);};}\n"+
    "    process.env.R0040_DISPERSION='common';delete process.env.R0040_OPTIONS;");
  return code;
}
function runPassive(t,mode){
  const root=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'passive-driver-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const result=require('node:child_process').spawnSync(process.execPath,['-e',passiveChildSource(),passivePath,path.resolve(__dirname,'../r0040/capture.cjs'),root,mode,'',''],
    {encoding:'utf8',timeout:mode==='timeout'?1800:10000,env:{...process.env,NODE_OPTIONS:''}});
  const evidence=path.join(root,'evidence'),file=path.join(evidence,'events.jsonl');
  const events=fs.existsSync(file)?fs.readFileSync(file,'utf8').trim().split('\n').map(JSON.parse):[];
  const read=name=>fs.existsSync(name)?JSON.parse(fs.readFileSync(name)):null;
  const stopFile=path.join(evidence,'passive-original-stop-1.json');
  return {root,result,events,base:read(path.join(evidence,'final-admission.json')),receipt:read(path.join(evidence,'passive-observation.json')),trace:read(path.join(root,'control-trace.json')),
    stopBytes:fs.existsSync(stopFile)?fs.readFileSync(stopFile):null};
}

test('actual pinned capture and helper preserve report PNGs stream callback and original arguments with separate passive admission',t=>{
  const r=runPassive(t,'complete'),P=passive(),D=require('./r0040_dateonly.cjs');
  assert.equal(r.result.status,0,r.result.stderr);assert.equal(r.base.status,D.ADMITTED);assert.equal(r.receipt.status,P.ADMITTED);
  assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);assert.equal(r.trace.rawCdp,true);
  assert.equal(r.trace.frameListenerCount,1);assert.equal(r.trace.streamFsyncs,0);assert.equal(r.trace.streamPngWrites,2);
  assert.equal(r.trace.contextCloseCalls,1);assert.equal(r.trace.isolatedCalls.filter(row=>row.extract).length,1);
  assert.equal(r.trace.isolatedCalls.find(row=>row.extract).inStream,false);
  assert.ok(r.receipt.observation.host.rows.some(row=>row.event==='playwright-worker-closed'));
  const response=r.receipt.observation.host.rows.find(row=>row.event==='browser-response');assert.ok(response.requestId>0);assert.equal(response.status,200);
  assert.equal(P.admitPassiveReceipt(r.receipt,fs.readFileSync(path.join(r.root,'evidence/final-admission.json')),
    P.passiveIdentity(path.resolve(__dirname,'../r0040/capture.cjs')),r.base.diagnostic,r.result.status,r.stopBytes).status,'OBSERVED');
  const stop=r.receipt.observation.samplers[0].originalStopResponse;
  assert.equal(stop.status,'RETAINED');assert.equal(stop.artifact.bytes,r.stopBytes.length);
  assert.equal(stop.artifact.sha256,require('node:crypto').createHash('sha256').update(r.stopBytes).digest('hex'));
  assert.deepEqual(JSON.parse(r.stopBytes).result.value.map(row=>row.at),[1000,1017]);
  const baseline=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'passive-parity-'));t.after(()=>fs.rmSync(baseline,{recursive:true,force:true}));
  const prior=require('node:child_process').spawnSync(process.execPath,['-e',dateOnlyChildSource(),path.join(__dirname,'r0040_dateonly.cjs'),
    path.resolve(__dirname,'../r0040/capture.cjs'),baseline,'complete','',''],{encoding:'utf8',timeout:10000,env:{...process.env,NODE_OPTIONS:''}});
  assert.equal(prior.status,0,prior.stderr);
  for(const file of ['capture.json','f00000.png','f00001.png'])assert.deepEqual(fs.readFileSync(path.join(r.root,'original',file)),fs.readFileSync(path.join(baseline,'original',file)),file+' original bytes differ');
});

test('actual driver retains malformed raw prefixes and unavailable evaluations while preserving its original success report',t=>{
  for(const mode of ['runtime-overflow','runtime-evaluate','sampler-overflow','sampler-evaluate','sampler-timeout']){
    const r=runPassive(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.base.originalExitCode,0);
    assert.equal(r.base.status,require('./r0040_dateonly.cjs').ADMITTED);assert.equal(r.receipt.status,'INCOMPLETE');
    assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
    const row=mode.startsWith('runtime')?r.receipt.observation.runtimes[0]:r.receipt.observation.samplers[0].extractions[0];
    if(mode.endsWith('overflow')){assert.ok(row.raw);assert.equal(row.status,'INCOMPLETE');assert.match(row.error.message,/overflow/);}
    else{assert.equal(row.raw,null);assert.equal(row.status,'UNAVAILABLE');}
  }
});

test('actual original oracle cleanup late network and page failures keep their report and failure precedence',t=>{
  for(const mode of ['oracle-failure','close-failure','late-pageerror','late-page-crash','unexpected-disconnect','passive-late-network']){
    const r=runPassive(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.base.status,'FAILED');assert.equal(r.receipt.status,'FAILED');
    assert.equal(r.trace.contextCloseCalls,1);if(mode==='oracle-failure')assert.equal(r.base.originalReport,null);
    else assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
  }
});

test('failed passive installation closes the acquired context and keeps the exact primary failure',t=>{
  const r=runPassive(t,'passive-install-failure');assert.equal(r.result.status,1,r.result.stderr);
  assert.equal(r.trace.contextCloseCalls,1);assert.match(r.result.stderr,/controlled passive install fault/);
  assert.equal(r.base.originalReport,null);assert.equal(r.receipt.status,'FAILED');
});

test('guard veto remains86 and no unknown external continuation occurs despite incomplete diagnostics',t=>{
  const r=runPassive(t,'proof-invalid-veto');assert.equal(r.result.status,86,r.result.stderr);
  assert.equal(r.receipt.status,'CONTINUATION_VETOED');assert.equal(r.receipt.exitCode,86);
  assert.equal(r.trace.continued.includes('https://unknown.invalid/blocked'),false);assert.ok(r.trace.aborted.includes('https://unknown.invalid/blocked'));
});

test('terminal or supplemental receipt fsync failure stays an actual failure and cannot publish passive admission',t=>{
  for(const mode of ['final-fsync','receipt-fsync','passive-receipt-fsync']){
    const r=runPassive(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.receipt,null);
    assert.ok(r.trace.reportAfterClose);assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);assert.match(r.result.stderr,/fsync fault/);
    if(mode==='passive-receipt-fsync')assert.equal(r.base.status,require('./r0040_dateonly.cjs').ADMITTED);
  }
});

test('outer timeout retains actual original PNGs and pre-stream passive prefix without terminal receipts',t=>{
  const r=runPassive(t,'timeout');assert.equal(r.result.signal,'SIGTERM',r.result.stderr);assert.equal(r.receipt,null);assert.equal(r.base,null);
  assert.deepEqual(fs.readdirSync(path.join(r.root,'original')).sort(),['f00000.png','f00001.png']);
  assert.ok(r.events.some(row=>row.event==='passive-runtime-prefix'&&row.observation.phase==='readiness-returned'));
  assert.equal(r.events.some(row=>row.event==='passive-observation-ended'),false);
});

test('terminal admission recomputes raw startup source clock and cleanup custody rather than accepting copied status',t=>{
  const r=runPassive(t,'complete'),P=passive(),identity=P.passiveIdentity(path.resolve(__dirname,'../r0040/capture.cjs'));
  const bytes=fs.readFileSync(path.join(r.root,'evidence/final-admission.json'));
  const check=(receipt,base=bytes,exit=0)=>P.admitPassiveReceipt(receipt,base,identity,r.base.diagnostic,exit,r.stopBytes);
  for(const mutate of [x=>x.status='PASS',x=>x.observation.identity.entrySha256='0'.repeat(64),x=>x.observation.runtimes.pop(),
    x=>x.observation.runtimes[0].raw.observer.events[0].event='unobserved-startup',
    x=>x.observation.runtimes[0].raw.observer.events[0].atMs=Number.MAX_SAFE_INTEGER,
    x=>x.observation.host.rows.splice(x.observation.host.rows.findIndex(row=>row.event==='server-closed'),1),
    x=>{const row=x.observation.samplers[0].extractions[0];row.raw.rows.pop();row.inspection=sampler().inspectSampler(row.raw);x.inspection.samplerRows=row.raw.rows.length;},
    x=>x.observation.samplers[0].extractions[0].raw.rows[0][0]=2,
    x=>x.observation.samplers[0].extractions[0].raw.clockDomain='main-performance',
    x=>x.timingClass='original-native',x=>x.nativeQualification='PASS']){
    const changed=plain(r.receipt);mutate(changed);assert.throws(()=>check(changed));
  }
  for(const exit of [1,86,null,false])assert.throws(()=>check(r.receipt,bytes,exit));
  assert.throws(()=>check(r.receipt,Buffer.concat([bytes,Buffer.from(' ')])));
  const base=plain(r.base);base.clockProofs[0].raw.after.dateNowMs+=100;
  const changedBytes=Buffer.from(JSON.stringify(base)),changed=plain(r.receipt);
  changed.baseAdmission.bytes=changedBytes.length;changed.baseAdmission.sha256=require('node:crypto').createHash('sha256').update(changedBytes).digest('hex');
  assert.throws(()=>check(changed,changedBytes),/clock|Date|anchor/);
});

test('coupled sampler-prefix and copied-count changes cannot replace the complete original stop population',t=>{
  const r=runPassive(t,'passive-extra-sample'),P=passive(),identity=P.passiveIdentity(path.resolve(__dirname,'../r0040/capture.cjs'));
  assert.equal(r.result.status,0,r.result.stderr);
  const baseBytes=fs.readFileSync(path.join(r.root,'evidence/final-admission.json'));
  const check=receipt=>P.admitPassiveReceipt(receipt,baseBytes,identity,r.base.diagnostic,r.result.status,r.stopBytes);
  assert.equal(check(r.receipt).status,'OBSERVED');
  assert.equal(JSON.parse(r.stopBytes).result.value.length,3);
  assert.equal(JSON.parse(fs.readFileSync(path.join(r.root,'original/capture.json'))).audit.states.length,2);
  const changed=plain(r.receipt),record=changed.observation.samplers[0],row=record.extractions[0];
  row.raw.rows.pop();record.originalSampleCount--;
  row.inspection=sampler().inspectSampler(row.raw);changed.inspection.samplerRows=row.raw.rows.length;
  assert.throws(()=>check(changed),/population|sample|stop/);
});

test('offline sampler admission requires actual stop bytes and exact complete ordinal timestamp mapping',t=>{
  const r=runPassive(t,'complete'),P=passive(),identity=P.passiveIdentity(path.resolve(__dirname,'../r0040/capture.cjs'));
  const base=fs.readFileSync(path.join(r.root,'evidence/final-admission.json'));
  const check=(receipt,bytes)=>P.admitPassiveReceipt(receipt,base,identity,r.base.diagnostic,0,bytes);
  assert.equal(check(r.receipt,r.stopBytes).status,'OBSERVED');
  for(const bytes of [undefined,null,JSON.parse(r.stopBytes),r.stopBytes.toString(),Buffer.concat([r.stopBytes,Buffer.from(' ')])])
    assert.throws(()=>check(r.receipt,bytes),/stop|bytes/);
  const changed=plain(r.receipt),row=changed.observation.samplers[0].extractions[0];
  row.raw.rows[0][1]+=1;row.inspection=sampler().inspectSampler(row.raw);
  assert.throws(()=>check(changed,r.stopBytes),/timestamp/);
  const altered=JSON.parse(r.stopBytes);altered.result.value[0].at+=1;
  const alteredBytes=Buffer.from(JSON.stringify(altered)),copied=plain(r.receipt),artifact=copied.observation.samplers[0].originalStopResponse.artifact;
  artifact.bytes=alteredBytes.length;artifact.sha256=require('node:crypto').createHash('sha256').update(alteredBytes).digest('hex');
  copied.observation.samplers[0].originalStopResponse.observedBytes=alteredBytes.length;
  assert.throws(()=>check(copied,r.stopBytes),/identity|bytes/);
  assert.throws(()=>check(copied,alteredBytes),/timestamp/);
  artifact.file='../original/capture.json';assert.throws(()=>check(copied,alteredBytes),/identity/);
  assert.deepEqual(fs.readFileSync(path.join(r.root,'evidence/passive-original-stop-1.json')),r.stopBytes);
});

test('bounded original stop retention failure preserves the exact original response and supplemental prefix',async t=>{
  const P=passive(),rawTrace=runExpression(sampler().instrumentStart(original).expression).raw;
  for(const stopResult of [{result:{value:Array.from({length:P.STOP_LIMITS.samples+1},()=>({at:1000}))}},
    {result:{value:[{at:1000}]},syntheticOversize:'x'.repeat(P.STOP_LIMITS.bytes)}]){
    const retain=passiveRetention(t),raw={async send(method,params){
      if(method==='Page.createIsolatedWorld')return {executionContextId:9};
      if(method==='Runtime.evaluate')return params.expression===stop?stopResult:
        params.expression==='globalThis.__R0040_PASSIVE_SAMPLER__??null'?{result:{value:rawTrace}}:{result:{value:true}};
      return {};}};
    const cdp=retain.wrapCDP(raw);await cdp.send('Page.createIsolatedWorld',{worldName:'r0040-native-clock'});
    await cdp.send('Runtime.evaluate',{contextId:9,expression:original,returnByValue:true});
    await cdp.send('Page.startScreencast');await cdp.send('Page.stopScreencast');
    assert.equal(await cdp.send('Runtime.evaluate',{contextId:9,expression:stop,returnByValue:true}),stopResult);
    const record=retain.passive.samplers[0];assert.equal(record.originalSampleCount,stopResult.result.value.length);
    assert.equal(record.originalStopResponse.status,'INCOMPLETE');assert.equal(record.originalStopResponse.artifact,null);
    assert.match(record.originalStopResponse.error.message,/bounded/);assert.deepEqual(record.extractions[0].raw,rawTrace);
    assert.equal(fs.existsSync(path.join(retain.journal.directory,'passive-original-stop-1.json')),false);
    assert.equal(fs.existsSync(path.join(retain.journal.directory,'passive-original-stop-1.json.pending')),false);
    assert.ok(retain.passive.errors.some(row=>row.phase==='original-stop-retention'));
  }
});

test('actual post-stream stop artifact faults preserve original report cleanup failure and veto precedence',t=>{
  for(const mode of ['passive-stop-fsync','passive-stop-fsync-close','passive-stop-fsync-veto','passive-stop-remove']){
    const r=runPassive(t,mode),veto=mode.endsWith('veto'),close=mode.endsWith('close');
    assert.equal(r.result.status,veto?86:1,r.result.stderr);assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
    assert.equal(r.trace.contextCloseCalls,1);assert.equal(r.trace.streamFsyncs,0);assert.equal(r.trace.frameListenerCount,1);
    assert.equal(r.base.originalExitCode,close?1:0);assert.equal(r.receipt.status,veto?'CONTINUATION_VETOED':close?'FAILED':'INCOMPLETE');
    assert.equal(r.stopBytes,null);assert.ok(fs.existsSync(path.join(r.root,'evidence/passive-original-stop-1.json.pending')));
    if(mode!=='passive-stop-remove'){
      const stop=r.receipt.observation.samplers[0].originalStopResponse;
      assert.equal(stop.status,'INCOMPLETE');assert.equal(stop.artifact,null);assert.match(stop.error.message,/fsync fault/);
    }
    if(close)assert.match(r.result.stderr,/original context close fault/);
    if(veto){assert.equal(r.receipt.exitCode,86);assert.equal(r.trace.continued.includes('https://unknown.invalid/blocked'),false);
      assert.ok(r.trace.aborted.includes('https://unknown.invalid/blocked'));}
  }
});

test('native entry refuses namespace absence before original helper browser or outputs and refuses dependency byte drift',t=>{
  const root=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'passive-admission-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const args=['--driver','unopened','--manifest','unopened','--prepared','unopened','--preparation-process','unopened','--preparation-entry','unopened',
    '--evidence',path.join(root,'evidence'),'--','unopened','unopened','unopened',path.join(root,'out'),'chromium','bday','moderate','M1'];
  const env={...process.env,NODE_OPTIONS:''};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
  const result=require('node:child_process').spawnSync(process.execPath,[passivePath,...args],{encoding:'utf8',env});
  assert.equal(result.status,1);assert.match(result.stderr,/admitted isolation receipt required/);assert.equal(fs.existsSync(path.join(root,'evidence')),false);
  for(const name of ['r0040_passive.cjs',...Object.keys(passive().SOURCE_PINS)])fs.copyFileSync(path.join(__dirname,name),path.join(root,name));
  fs.appendFileSync(path.join(root,'r0040_passive_runtime.cjs'),'\n// synthetic source drift\n');
  const drift=require('node:child_process').spawnSync(process.execPath,[path.join(root,'r0040_passive.cjs'),...args],{encoding:'utf8',env});
  assert.equal(drift.status,1);assert.match(drift.stderr,/passive dependency source drift/);assert.equal(fs.existsSync(path.join(root,'evidence')),false);
});

test('server error observation preserves native unhandled exceptions and existing error-handler delivery',async t=>{
  const retain=passiveRetention(t),{EventEmitter}=require('node:events'),server=new EventEmitter();server.close=()=>server.emit('close');
  await retain.wrapHelper({async serve(){return {srv:server,base:'http://127.0.0.1:8765'};}}).serve();
  const request=new EventEmitter();request.url='/synthetic';request.method='GET';
  const response=new EventEmitter();response.statusCode=200;response.getHeader=()=>undefined;
  server.emit('request',request,response);
  assert.equal(request.listenerCount('error'),0);assert.equal(response.listenerCount('error'),0);assert.equal(server.listenerCount('error'),0);
  const primary=Error('synthetic unhandled request failure');assert.throws(()=>request.emit('error',primary),error=>error===primary);
  const secondary=Error('synthetic unhandled response failure');assert.throws(()=>response.emit('error',secondary),error=>error===secondary);
  const serverError=Error('synthetic unhandled server failure');assert.throws(()=>server.emit('error',serverError),error=>error===serverError);
  let delivered;response.on('error',error=>{delivered=error;});assert.equal(response.emit('error',primary),true);assert.equal(delivered,primary);
  assert.ok(retain.passive.host.rows.some(row=>row.event==='server-request-error'&&row.error===primary.message));
  assert.ok(retain.passive.host.rows.some(row=>row.event==='server-response-error'&&row.error===secondary.message));
  assert.ok(retain.passive.host.rows.some(row=>row.event==='server-error'&&row.error===serverError.message));
});

test('unchanged historical HTTP helper retains exact asset and 404 responses with complete server lifecycle observations',async t=>{
  const http=require('node:http'),Module=require('node:module'),D=require('./r0040_dateonly.cjs'),retain=passiveRetention(t);
  const file=path.join(__dirname,'fixtures/r0040-precip-eval-original.txt'),bytes=fs.readFileSync(file);
  assert.equal(require('node:crypto').createHash('sha256').update(bytes).digest('hex'),D.ORIGINAL_SHA256);
  const helper=new Module(file,module);helper.filename=file;helper.paths=Module._nodeModulePaths(__dirname);helper._compile(bytes.toString(),file);
  const root=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'passive-http-control-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const body=Buffer.from('synthetic original served bytes\n');fs.writeFileSync(path.join(root,'asset.css'),body);
  const get=url=>new Promise((resolve,reject)=>{const request=http.get(url,response=>{const chunks=[];
    response.on('data',data=>chunks.push(data));response.on('end',()=>resolve({status:response.statusCode,
      contentType:response.headers['content-type']??null,cacheControl:response.headers['cache-control']??null,body:Buffer.concat(chunks)}));
    response.on('error',reject);});request.on('error',reject);});
  async function exercise(original){
    const serving=await original.serve(root);
    try{return [await get(serving.base+'/asset.css'),await get(serving.base+'/missing.css')];}
    finally{await new Promise((resolve,reject)=>serving.srv.close(error=>error?reject(error):resolve()));}
  }
  const baseline=await exercise(helper.exports),observed=await exercise(retain.wrapHelper(helper.exports));
  assert.deepEqual(observed,baseline);assert.deepEqual(observed[0],{status:200,contentType:'text/css',cacheControl:'no-store',body});
  assert.equal(observed[1].status,404);assert.equal(observed[1].body.length,0);
  const rows=retain.passive.host.rows,requests=rows.filter(row=>row.event==='server-request');
  assert.deepEqual(requests.map(row=>row.url),['/asset.css','/missing.css']);
  for(const [i,request]of requests.entries()){
    const finishes=rows.filter(row=>row.event==='server-response-finish'&&row.serverRequestId===request.serverRequestId);
    const closes=rows.filter(row=>row.event==='server-response-close'&&row.serverRequestId===request.serverRequestId);
    assert.equal(finishes.length,1);assert.equal(closes.length,1);assert.equal(finishes[0].status,observed[i].status);
  }
  assert.equal(rows.filter(row=>row.event==='server-closed').length,1);assert.deepEqual(retain.passive.errors,[]);
});
