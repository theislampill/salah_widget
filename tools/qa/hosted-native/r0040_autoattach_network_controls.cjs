'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const N=require(process.env.R0040_AUTOATTACH_TEST_HELPER||'./r0040_autoattach_network.cjs');
const {fakeBrowser,fixture,request,complete,inspect,BASE,BLOB,selected,workers,policy}=require('./r0040_autoattach_fixture.cjs');
const clone=x=>JSON.parse(JSON.stringify(x));
function refused(raw){assert.throws(()=>inspect(raw));}

test('automatic owned worker route retains complete real starts and all policy/network/tunnel acknowledgements',async()=>{
  const f=await complete(),result=inspect(f.raw);
  assert.equal(f.raw.protocol,'r0040-autoattach-network/1');assert.equal(result.status,'OBSERVED');
  assert.deepEqual(result.requests.map(r=>[r.legacyRequestId,r.targetId,r.workerId,r.terminal]),[[10,'moon',1,'finished'],[11,'moon',1,'finished']]);
  assert.equal(result.cause,'NOT_ESTABLISHED');assert.equal(result.javascriptReaderCompletion,'NOT_OBSERVED');
  assert.ok(f.fake.calls.some(r=>r.method==='Target.setAutoAttach'&&r.route.length===1));
  assert.ok(f.fake.calls.some(r=>r.method==='Network.enable'&&r.route.length===2));
  assert.ok(f.fake.calls.filter(r=>r.method==='Target.attachToTarget').every(r=>r.params.targetId==='page'));
  assert.ok(!f.fake.calls.some(r=>/Runtime\.|Page\.|detach|Fetch\.|setCache|getResponseBody/.test(r.method)));
});
test('nested worker routes preserve ownership and acknowledge every containing public tunnel',async()=>{
  const f=await fixture();f.fake.addWorker({targetId:'nested',parent:'moon',url:'blob:'+BASE+'/nested'});await f.o.settle();
  request(f,0);request(f,1);const raw=await f.finish();assert.equal(inspect(raw).status,'OBSERVED');
  assert.ok(f.fake.calls.some(c=>c.method==='Network.enable'&&c.route.length===3));
  assert.ok(raw.rows.some(r=>r.event==='session-detached'&&r.targetId==='nested'));
});
test('automatic attachment before discovery is retained with its actual origin and later reconciled',async()=>{
  const f=await complete({workerOptions:{discovery:'after'}});assert.equal(inspect(f.raw).status,'OBSERVED');
  const rows=f.raw.rows.filter(r=>r.targetId==='moon');assert.equal(rows[0].event,'target-observed-from-attachment');
  assert.ok(rows.some(r=>r.event==='target-discovered'));assert.equal(rows.some(r=>r.event==='target-created'),false);
});
test('an unconfirmed global target population cannot be inferred from automatic attachment',async()=>{
  const f=await complete({workerOptions:{discovery:'none'}});refused(f.raw);
});
test('a discovered but uncovered worker never triggers manual attachment fallback',async()=>{
  const f=await fixture({worker:false}),info={targetId:'uncovered',type:'worker',url:BLOB,browserContextId:'context'};
  f.fake.targets.set(info.targetId,info);f.fake.root.emit('Target.targetCreated',{targetInfo:info});await f.o.settle();
  f.fake.targets.delete(info.targetId);f.fake.root.emit('Target.targetDestroyed',{targetId:info.targetId});refused(await f.finish());
  assert.ok(f.fake.calls.filter(r=>r.method==='Target.attachToTarget').every(r=>r.params.targetId==='page'));
});
for(const waiting of [true,null,'false'])test('unexpected waiting flag '+JSON.stringify(waiting)+' remains incomplete without resume',async()=>{
  const f=await complete({workerOptions:{waitingForDebugger:waiting}});refused(f.raw);
  assert.ok(!f.fake.calls.some(r=>/runIfWaiting|detach|pause|resume/.test(r.method)));
});
test('native24-shaped missing starts remain orphan faults despite successful automatic policy',async()=>{
  const f=await fixture();request(f,0,{start:false});request(f,1,{start:false});const raw=await f.finish();refused(raw);
  assert.equal(raw.rows.filter(r=>r.event==='orphan-response').length,2);assert.ok(raw.faults>=4);
});
test('failed terminals remain descriptive network failures without reader or cause claims',async()=>{
  const f=await fixture();request(f,0,{terminal:'failed'});request(f,1,{terminal:'failed'});const raw=await f.finish();
  const result=inspect(raw,selected.map(r=>({...r,browserState:'failed'})));assert.ok(result.requests.every(r=>r.terminal==='failed'));
  assert.equal(result.readerCancellation,'NOT_OBSERVED');assert.equal(result.originalFailureOverride,false);
});
test('request events may precede enable acknowledgement but actual later acknowledgement is mandatory',async()=>{
  const f=await fixture({worker:false,hold:(route,m)=>route.length===2&&m.method==='Network.enable'});
  f.fake.addWorker();await new Promise(resolve=>setImmediate(resolve));request(f,0);request(f,1);
  f.fake.held.splice(0).forEach(fn=>fn());await f.o.settle();assert.equal(inspect(await f.finish()).status,'OBSERVED');
});
for(const method of ['Target.setAutoAttach','Network.enable','Target.sendMessageToTarget'])test('missing '+method+' acknowledgement remains bounded incomplete',async()=>{
  const f=await fixture({hold:(_route,m)=>m.method===method});request(f,0);request(f,1);const raw=await f.finish();refused(raw);
  assert.ok(raw.issues.some(r=>/timed out|incomplete/.test(r.message)));
});
test('rejected automatic policy is retained and never replaced by a manual worker command',async()=>{
  const f=await complete({reject:(_r,m)=>m.method==='Target.setAutoAttach'});refused(f.raw);
  assert.ok(f.raw.issues.some(r=>/unsupported/.test(r.message)));assert.ok(f.fake.calls.filter(r=>r.method==='Target.attachToTarget').every(r=>r.params.targetId==='page'));
});
test('unsupported public discovery keeps its original bounded setup refusal',async()=>{
  const f=await complete({unsupported:true});assert.equal(f.raw.setup.status,'INCOMPLETE');refused(f.raw);
});
for(const missing of ['moon','page'])test('missing actual '+missing+' session detach cannot be inferred from target destruction',async()=>{
  const f=await fixture();request(f,0);request(f,1);refused(await f.finish({missingDetach:missing}));
});
test('missing worker destruction or a still-live owned target remains incomplete',async()=>{
  const f=await fixture();request(f,0);request(f,1);refused(await f.finish({missingDestroy:'moon'}));
});
test('foreign child route cannot borrow a known worker session to produce metadata',async()=>{
  const f=await fixture();f.fake.emit(['page-session','foreign-parent','moon-session'],{method:'Network.loadingFinished',params:{requestId:'x',timestamp:2,encodedDataLength:0}});
  request(f,0);request(f,1);refused(await f.finish());
});
test('duplicate automatic session or target ownership is retained as a refusal',async()=>{
  const f=await fixture();f.fake.addWorker();request(f,0);request(f,1);refused(await f.finish());
});
test('wrong-route and duplicate command responses cannot complete another pending command',async()=>{
  const f=await fixture();const command=f.fake.calls.find(r=>r.route.length===2&&r.method==='Network.enable');
  f.fake.emit(['page-session'],{id:command.id,result:{}});request(f,0);request(f,1);refused(await f.finish());
});
for(const limits of [{events:8},{bytes:500},{workers:1},{messageBytes:100}])test('lowered collection limit '+JSON.stringify(limits)+' cannot report a complete prefix',async()=>{
  const f=await fixture({limits});if(limits.workers)f.fake.addWorker({targetId:'overflow',url:'blob:'+BASE+'/overflow'});
  request(f,0);request(f,1);refused(await f.finish());
});
test('route ancestry cannot exceed the existing worker population bound',async()=>{
  const f=await fixture({autoLimits:{routeDepth:1}});request(f,0);request(f,1);refused(await f.finish());
});
test('oversized actual public message and malformed nested payload are bounded faults',async()=>{
  const f=await fixture();f.fake.root.emit('Target.receivedMessageFromTarget',{sessionId:'page-session',message:'x'.repeat(262145)});
  f.fake.emit(['page-session'],{method:'Target.receivedMessageFromTarget',params:{sessionId:'moon-session',message:'{bad'}});
  request(f,0);request(f,1);const raw=await f.finish();assert.ok(raw.faults>=2);refused(raw);
});
for(const drift of ['created','completed-attachment','info','detached','destroyed','late-response'])test('final snapshot '+drift+' cannot conceal late route or lifecycle work',async()=>{
  const f=await fixture({finalSnapshot:async fake=>{
    if(drift==='created'){const info={targetId:'late',type:'worker',url:BLOB};fake.root.emit('Target.targetCreated',{targetInfo:info});fake.root.emit('Target.targetDestroyed',{targetId:'late'});}
    if(drift==='completed-attachment'){fake.addWorker({targetId:'late',url:BLOB});await new Promise(resolve=>setImmediate(resolve));fake.targets.delete('late');fake.root.emit('Target.targetDestroyed',{targetId:'late'});}
    if(drift==='info')fake.root.emit('Target.targetInfoChanged',{targetInfo:{targetId:'moon',type:'worker',url:BLOB,browserContextId:'context'}});
    if(drift==='detached')fake.emit(['page-session'],{method:'Target.detachedFromTarget',params:{sessionId:'moon-session',targetId:'moon'}});
    if(drift==='destroyed')fake.root.emit('Target.targetDestroyed',{targetId:'moon'});
    if(drift==='late-response')fake.emit(['page-session'],{id:999999,result:{}});
  }});request(f,0);request(f,1);const raw=await f.finish();refused(raw);
  assert.equal(raw.drain.status,'INCOMPLETE');
});
test('late unresolved replies cannot mutate the frozen incomplete result or defer cleanup indefinitely',async()=>{
  const f=await fixture({hold:(_r,m)=>m.method==='Network.enable'});request(f,0);request(f,1);const raw=await f.finish(),saved=clone(raw);
  f.fake.held.splice(0).forEach(fn=>fn());await new Promise(resolve=>setTimeout(resolve,45));assert.deepEqual(raw,saved);refused(raw);
});
test('retained route, acknowledgement and clock tampering is refused even with repaired byte totals',async()=>{
  const f=await complete();for(const mutate of [r=>r.rows[0].hostMonotonicNs='-1',r=>r.autoAttachLimits.routeDepth=18,
    r=>r.rows.splice(r.rows.findIndex(x=>x.event==='autoattach-enabled'),1),r=>r.rows.find(x=>x.event==='session-detached'&&x.targetId==='moon').targetId='page']){
    const raw=clone(f.raw);mutate(raw);raw.rows.forEach((r,i)=>r.ordinal=i);raw.observedEvents=raw.rows.length;
    raw.retainedMetadataBytes=raw.observedMetadataBytes=raw.rows.reduce((n,r)=>n+Buffer.byteLength(JSON.stringify(r)),0);refused(raw);
  }
});

test('actual attachment targetInfo supplies its URL when discovery saw an empty startup URL',async()=>{
  const f=await fixture({worker:false});
  f.fake.root.emit('Target.targetCreated',{targetInfo:{targetId:'moon',type:'worker',url:'',browserContextId:'context'}});
  f.fake.addWorker({discovery:'none'});await f.o.settle();request(f,0);request(f,1);
  const raw=await f.finish();assert.equal(inspect(raw).requests[0].workerId,1);
  assert.ok(raw.rows.some(r=>r.event==='target-info-from-attachment'&&r.targetId==='moon'&&r.url===BLOB));
});
test('late parent policy acknowledgement cannot rehabilitate an actual initialization timeout',async()=>{
  const f=await fixture({worker:false,hold:(route,m)=>route.length===1&&m.method==='Target.setAutoAttach'});
  f.fake.addWorker();await new Promise(resolve=>setImmediate(resolve));request(f,0);request(f,1);
  f.fake.held.splice(0).forEach(fn=>fn());await f.o.settle();refused(await f.finish());
  // The first bounded fixture setup already timed out waiting for the held
  // parent command. A later reply must not rehabilitate that actual timeout.
});
test('actual child attachment before a pending parent policy acknowledgement can complete without a new startup wait',async()=>{
  const fake=fakeBrowser({hold:(route,m)=>route.length===1&&m.method==='Target.setAutoAttach'}),o=new N.NetworkObserver({timeoutMs:35});
  await o.start(fake.browser,BASE);await new Promise(resolve=>setImmediate(resolve));fake.addWorker();
  const f={emit:(method,params)=>fake.emit(['page-session','moon-session'],{method,params})};request(f,0);request(f,1);
  fake.held.splice(0).forEach(fn=>fn());await o.settle();fake.close();assert.equal(inspect(await o.finish()).status,'OBSERVED');
});
test('missing actual waiting state is refused rather than defaulted to false',async()=>{
  const f=await fixture({worker:false});
  f.fake.emit(['page-session'],{method:'Target.attachedToTarget',params:{sessionId:'moon-session',targetInfo:{targetId:'moon',type:'worker',url:BLOB,browserContextId:'context'}}});
  const raw=await f.finish();refused(raw);assert.ok(raw.issues.some(r=>/waiting/.test(r.message)));
});
for(const autoLimits of [{logicalCommands:1},{pendingResponses:1}])test('derived pending bound '+JSON.stringify(autoLimits)+' cannot silently drop initialization',async()=>{
  const f=await complete({autoLimits});refused(f.raw);assert.ok(f.raw.issues.some(r=>/bounded/.test(r.message)));
});
test('duplicate actual nested acknowledgement is a retained fault',async()=>{
  const f=await fixture(),c=f.fake.calls.find(r=>r.route.length===2&&r.method==='Network.enable');
  f.fake.emit(c.route,{id:c.id,result:{}});request(f,0);request(f,1);const raw=await f.finish();refused(raw);
  assert.ok(raw.issues.some(r=>/duplicate/.test(r.message)));
});

for(const error of [null,false,0,''])test('contradictory result and error '+JSON.stringify(error)+' cannot acknowledge a nested command',async()=>{
  const fake=fakeBrowser({hold:(route,m)=>route.length===2&&m.method==='Network.enable'}),o=new N.NetworkObserver({timeoutMs:35});
  await o.start(fake.browser,BASE);await o.settle();fake.addWorker();await new Promise(resolve=>setImmediate(resolve));
  const command=fake.calls.find(r=>r.route.length===2&&r.method==='Network.enable');
  fake.emit(command.route,{id:command.id,result:{},error});
  const f={emit:(method,params)=>fake.emit(['page-session','moon-session'],{method,params})};request(f,0);request(f,1);
  await o.settle();fake.close();const raw=await o.finish();refused(raw);
  assert.ok(raw.issues.some(row=>/response|acknowledgement/.test(row.message)));
});
test('automatic attachment cannot lose its actual targetInfo provenance even after counters are repaired',async()=>{
  const {raw:actual}=await complete(),raw=clone(actual);
  const index=raw.rows.findIndex(row=>row.event==='target-info-from-attachment'&&row.targetId==='moon');assert.ok(index>=0);
  raw.rows.splice(index,1);raw.rows.forEach((row,ordinal)=>row.ordinal=ordinal);raw.observedEvents=raw.rows.length;
  raw.retainedMetadataBytes=raw.observedMetadataBytes=raw.rows.reduce((n,row)=>n+Buffer.byteLength(JSON.stringify(row)),0);
  raw.drain.boundary.versionBefore=raw.drain.boundary.versionAfter=raw.rows.length;
  refused(raw);
});
test('missing outer public send acknowledgement cannot be inferred from complete nested replies',async()=>{
  const f=await complete({holdOuter:true});refused(f.raw);
  assert.ok(f.raw.issues.some(row=>/transport.*timed out/.test(row.message)));
});
test('foreign automatic child context cannot borrow the owned page route',async()=>{
  const f=await fixture({worker:false}),info={targetId:'moon',type:'worker',url:BLOB,browserContextId:'foreign-context'};
  f.fake.targets.set('moon',info);f.fake.root.emit('Target.targetCreated',{targetInfo:info});
  f.fake.emit(['page-session'],{method:'Target.attachedToTarget',params:{sessionId:'moon-session',targetInfo:info,waitingForDebugger:false}});
  const raw=await f.finish();refused(raw);assert.ok(raw.issues.some(row=>/context/.test(row.message)));
});
test('each logical initialization uses one shared absolute deadline rather than one timer per tunnel layer',async()=>{
  const fake=fakeBrowser({hold:(route,m)=>route.length===2&&['Target.setAutoAttach','Network.enable'].includes(m.method)}),
    o=new N.NetworkObserver({timeoutMs:35});await o.start(fake.browser,BASE);await o.settle();
  const original=globalThis.setTimeout;let timers=0;
  try{globalThis.setTimeout=(...args)=>{timers++;return original(...args);};fake.addWorker();await new Promise(resolve=>setImmediate(resolve));}
  finally{globalThis.setTimeout=original;}
  fake.held.splice(0).forEach(fn=>fn());await o.settle();
  const f={emit:(method,params)=>fake.emit(['page-session','moon-session'],{method,params})};request(f,0);request(f,1);fake.close();
  assert.equal(inspect(await o.finish()).status,'OBSERVED');assert.equal(timers,2,'two logical worker initialization operations');
});
test('an already exhausted logical deadline never dispatches an outer command afterwards',async()=>{
  const f=await fixture({worker:false}),original=f.fake.root.send;let calls=0;
  f.fake.root.send=async()=>{calls++;return {};};
  await assert.rejects(f.o.command(['page-session'],'Network.enable',{},-1),/deadline exhausted/);
  await new Promise(resolve=>setImmediate(resolve));f.fake.root.send=original;
  const actualCalls=calls;await f.finish();assert.equal(actualCalls,0);assert.equal(f.o.responses.size,0);assert.equal(f.o.logical.size,0);
});
