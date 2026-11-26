'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),{EventEmitter}=require('node:events');
const helper=()=>require('./r0040_mechanism_network.cjs');
const clone=value=>JSON.parse(JSON.stringify(value));
const BASE='http://127.0.0.1:40001',BLOB='blob:'+BASE+'/owned-moon';
const selected=[{id:10,url:BASE+'/moon/assets/dem.bin.gz',method:'GET',browserState:'failed'},
  {id:11,url:BASE+'/moon/assets/colour.bin.gz',method:'GET',browserState:'failed'}];
const workers=[{event:'worker-constructed',workerId:1,url:BLOB}];

function fakeBrowser({unsupported=false,hangEnable=false,rejectBeforeAck=false}={}){
  const root=new EventEmitter(),calls=[],targets=new Map();let sessions=0;
  root.send=async(method,params={})=>{
    calls.push([method,clone(params)]);
    if(unsupported&&method==='Target.setDiscoverTargets')throw Error('unsupported public Target discovery');
    if(method==='Target.getTargets')return {targetInfos:[...targets.values()]};
    if(method==='Target.attachToTarget')return {sessionId:'session-'+(++sessions)};
    if(method==='Target.sendMessageToTarget'){
      const message=JSON.parse(params.message);if(hangEnable&&message.method==='Network.enable')return {};
      if(rejectBeforeAck){
        root.emit('Target.receivedMessageFromTarget',{sessionId:params.sessionId,
          message:JSON.stringify({id:message.id,error:{code:-1,message:'unsupported Network.enable'}})});
        await new Promise(resolve=>setTimeout(resolve,5));return {};
      }
      queueMicrotask(()=>root.emit('Target.receivedMessageFromTarget',{sessionId:params.sessionId,message:JSON.stringify({id:message.id,result:{}})}));
    }
    return {};
  };
  root.detach=async()=>{};
  return {root,calls,targets,browser:{async newBrowserCDPSession(){calls.push(['newBrowserCDPSession',{}]);return root;}}};
}

async function fixture(options={}){
  const N=helper(),fake=fakeBrowser(options),o=new N.NetworkObserver({timeoutMs:25,...options});
  await o.start(fake.browser,BASE);
  const info={targetId:'moon',type:'worker',url:BLOB,browserContextId:'private-context'};
  fake.targets.set(info.targetId,info);fake.root.emit('Target.targetCreated',{targetInfo:info});
  await o.settle();
  const session=o.snapshot().rows.find(x=>x.event==='target-attached')?.sessionId;
  const emit=(method,params)=>o.observe(session,method,params);
  const finish=async()=>{fake.targets.delete('moon');fake.root.emit('Target.targetDestroyed',{targetId:'moon'});await o.finish();return o.snapshot();};
  return {N,o,fake,session,emit,finish};
}

function request(f,index,{terminal='failed',status=200}={}){
  const id='request-'+index,url=selected[index].url;
  f.emit('Network.requestWillBeSent',{requestId:id,loaderId:'',documentURL:BLOB,type:'Fetch',timestamp:1+index,
    request:{url,method:'GET'},initiator:{type:'script',stack:{callFrames:[{functionName:'read',scriptId:'worker-script',url:BLOB,lineNumber:6,columnNumber:15}]}}});
  f.emit('Network.responseReceived',{requestId:id,loaderId:'',type:'Fetch',timestamp:1.1+index,response:{url,status,mimeType:'application/octet-stream',
    fromDiskCache:false,fromServiceWorker:false,headers:{'Content-Length':'4','Content-Encoding':'identity'}}});
  const data={requestId:id,timestamp:1.2+index,dataLength:4,encodedDataLength:4};
  Object.defineProperty(data,'data',{get(){throw Error('response body must never be observed');}});f.emit('Network.dataReceived',data);
  if(terminal==='failed')f.emit('Network.loadingFailed',{requestId:id,timestamp:1.3+index,type:'Fetch',errorText:'net::ERR_ABORTED',canceled:true});
  if(terminal==='finished')f.emit('Network.loadingFinished',{requestId:id,timestamp:1.3+index,encodedDataLength:4});
}

test('public protocol collection records exact request/worker ownership and failed terminals without assigning cause',async()=>{
  const f=await fixture();request(f,0);request(f,1);const raw=await f.finish(),r=f.N.inspectNetwork(raw,selected,workers);
  assert.equal(r.status,'OBSERVED');assert.equal(r.requests.length,2);assert.equal(r.requests[0].legacyRequestId,10);
  assert.equal(r.requests[0].workerId,1);assert.equal(r.requests[0].targetId,'moon');assert.equal(r.requests[0].terminal,'failed');
  assert.equal(r.requests[0].canceled,true);assert.equal(r.requests[0].receivedDataBytes,4);assert.equal(r.cause,'NOT_ESTABLISHED');
  assert.equal(r.javascriptReaderCompletion,'NOT_OBSERVED');assert.equal(r.originalFailureOverride,false);
  const methods=f.fake.calls.map(x=>x[0]);assert.ok(methods.includes('Target.attachToTarget'));
  assert.ok(!methods.some(x=>/pause|resume|runIfWaiting|setAutoAttach|setCache|Fetch\.|getResponseBody/.test(x)));
  for(const [,p]of f.fake.calls)assert.notEqual(p.waitForDebuggerOnStart,true);
  for(const [method,p]of f.fake.calls)if(method==='Target.sendMessageToTarget')assert.equal(JSON.parse(p.message).method,'Network.enable');
  assert.equal(JSON.stringify(raw).includes('response body'),false);
});

test('browser loadingFinished is represented as network completion without claiming JavaScript consumption',async()=>{
  const f=await fixture();request(f,0,{terminal:'finished'});request(f,1,{terminal:'finished'});const raw=await f.finish();
  const complete=selected.map(r=>({...r,browserState:'finished'})),result=f.N.inspectNetwork(raw,complete,workers);
  assert.ok(result.requests.every(r=>r.terminal==='finished'));assert.equal(result.javascriptReaderCompletion,'NOT_OBSERVED');
  assert.equal(result.nativeQualification,'NOT_VERIFIED');
});

test('unsupported public discovery retains a precise incomplete prefix and never changes startup policy',async()=>{
  const f=await fixture({unsupported:true});const raw=await f.finish();
  assert.equal(raw.setup.status,'INCOMPLETE');assert.ok(raw.issues.some(x=>/unsupported/.test(x.message)));
  assert.throws(()=>f.N.inspectNetwork(raw,selected,workers),/setup|incomplete|protocol/);
  assert.ok(!f.fake.calls.some(x=>/setAutoAttach|runIfWaiting|pause/.test(x[0])));
});

test('missing selected starts terminals or worker target identities cannot imply complete coverage',async()=>{
  const f=await fixture();request(f,0);request(f,1);const original=await f.finish();
  for(const event of ['request-start','request-failed','target-attached','target-created','network-enabled','target-destroyed']){
    const raw=clone(original),index=raw.rows.findIndex(r=>r.event===event);raw.rows.splice(index,1);
    assert.throws(()=>f.N.inspectNetwork(raw,selected,workers));
  }
  assert.throws(()=>f.N.inspectNetwork(original,selected,[]),/worker|owner/);
  assert.throws(()=>f.N.inspectNetwork(original,selected,[...workers,{...workers[0],workerId:2}]),/unique|ambiguous/);
});

test('actual orphan and unfinished request events are retained and refused',async()=>{
  const f=await fixture();request(f,0,{terminal:null});
  f.emit('Network.responseReceived',{requestId:'missing-start',timestamp:2,type:'Fetch',response:{url:selected[1].url,status:200,headers:{}}});
  f.emit('Network.loadingFailed',{requestId:'missing-start',timestamp:3,errorText:'net::ERR_ABORTED'});
  const raw=await f.finish();assert.ok(raw.rows.some(r=>r.event==='orphan-response'));assert.ok(raw.issues.length);
  assert.throws(()=>f.N.inspectNetwork(raw,selected,workers),/incomplete|orphan|terminal/);
});

test('duplicate terminals, request identifiers and ambiguous legacy joins remain incomplete',async()=>{
  const f=await fixture();request(f,0);request(f,1);
  f.emit('Network.loadingFinished',{requestId:'request-0',timestamp:4,encodedDataLength:4});
  const raw=await f.finish();assert.throws(()=>f.N.inspectNetwork(raw,selected,workers),/terminal|incomplete/);
  const g=await fixture();request(g,0);request(g,1);const good=await g.finish();
  assert.throws(()=>g.N.inspectNetwork(good,[...selected,{...selected[0],id:12}],workers),/unique|population|ambiguous/);
});

test('selected redirects and conflicting response URLs cannot be silently normalized',async()=>{
  const f=await fixture();request(f,0);request(f,1);
  f.emit('Network.requestWillBeSent',{requestId:'request-0',timestamp:4,request:{url:selected[0].url,method:'GET'},initiator:{type:'other'},redirectResponse:{status:302}});
  const raw=await f.finish();assert.ok(raw.issues.some(r=>/redirect|duplicate/.test(r.message)));
  assert.throws(()=>f.N.inspectNetwork(raw,selected,workers));
});

test('overflow limits retain bounded metadata with original counts and no body payloads',async()=>{
  const f=await fixture({limits:{events:12}});request(f,0);request(f,1);const raw=await f.finish();
  assert.ok(raw.dropped>0);assert.ok(raw.observedEvents>raw.rows.length);assert.ok(raw.rows.length<=12);
  assert.throws(()=>f.N.inspectNetwork(raw,selected,workers),/limit|overflow|incomplete/);
  const g=await fixture({limits:{bytes:500}});request(g,0);request(g,1);const small=await g.finish();
  assert.ok(small.observedMetadataBytes>small.retainedMetadataBytes);assert.ok(small.retainedMetadataBytes<=500);
  assert.throws(()=>g.N.inspectNetwork(small,selected,workers));
});

test('bounded initiator truncation is explicit and cannot qualify the prefix',async()=>{
  const f=await fixture();f.emit('Network.requestWillBeSent',{requestId:'request-0',timestamp:1,type:'Fetch',loaderId:'',
    request:{url:selected[0].url,method:'GET'},initiator:{type:'script',stack:{callFrames:Array.from({length:9},()=>({functionName:'read',scriptId:'x',url:BLOB,lineNumber:0,columnNumber:0}))}}});
  const raw=await f.finish();assert.ok(raw.truncatedFields>0);assert.ok(raw.issues.some(x=>/stack|truncat/.test(x.message)));
  assert.throws(()=>f.N.inspectNetwork(raw,selected,workers));
});

test('bounded network-enable timeout preserves refusal without pausing or waiting for another frame',async()=>{
  const f=await fixture({hangEnable:true});const raw=await f.finish();
  assert.ok(raw.issues.some(r=>/timed out/.test(r.message)));assert.throws(()=>f.N.inspectNetwork(raw,selected,workers));
  assert.ok(!f.fake.calls.some(x=>/Runtime\.|Page\./.test(x[0])));
});

test('nested protocol rejection before public command acknowledgement stays a retained diagnostic error',async()=>{
  const f=await fixture({rejectBeforeAck:true});const raw=await f.finish();
  assert.ok(raw.issues.some(r=>/Network.enable protocol error/.test(r.message)));
  assert.throws(()=>f.N.inspectNetwork(raw,selected,workers));
  assert.equal(raw.setup.status,'OBSERVED');
});

test('exhausted drain budget does not start another public protocol command',async()=>{
  const N=helper(),fake=fakeBrowser(),o=new N.NetworkObserver({timeoutMs:25});
  await o.start(fake.browser,BASE);
  o.pending.add(new Promise(()=>{})); // Explicit synthetic unfinished attachment.
  const raw=await o.finish();
  assert.equal(raw.drain.status,'INCOMPLETE');
  assert.ok(raw.issues.some(r=>/drain incomplete|deadline exhausted/.test(r.message)));
  assert.equal(fake.calls.filter(([method])=>method==='Target.getTargets').length,1);
});

test('metadata bytes, ordinals, clock order and summary tampering are detected from retained rows',async()=>{
  const f=await fixture();request(f,0);request(f,1);const raw=await f.finish();
  for(const mutate of [x=>x.retainedMetadataBytes++,x=>x.rows[0].ordinal=2,x=>x.rows[1].hostMonotonicNs='0',
      x=>x.rows.find(r=>r.event==='request-failed').timestamp=-1,x=>x.finalTargets=['moon'],x=>x.setup.status='UNAVAILABLE']){
    const changed=clone(raw);mutate(changed);assert.throws(()=>f.N.inspectNetwork(changed,selected,workers));
  }
});

test('unrelated request metadata is excluded and URL origin/path restrictions stay exact',async()=>{
  const f=await fixture();
  for(const [id,url]of [['unrelated',BASE+'/index.html'],['external','https://elsewhere.invalid/moon/assets/dem.bin.gz'],['query',selected[0].url+'?changed=1']]){
    f.emit('Network.requestWillBeSent',{requestId:id,timestamp:0,request:{url,method:'GET'},initiator:{type:'other'}});
    f.emit('Network.loadingFinished',{requestId:id,timestamp:1,encodedDataLength:100});
  }
  request(f,0);request(f,1);const raw=await f.finish();assert.equal(f.N.inspectNetwork(raw,selected,workers).status,'OBSERVED');
  assert.ok(!raw.rows.some(r=>r.requestId==='unrelated'||r.requestId==='external'||r.requestId==='query'));
});

module.exports={fakeBrowser,fixture,request,BASE,BLOB,selected,workers};
