'use strict';
// Adapted from the retained independent eight-case RED control (SHA-256
// b889072e820360d8a6c7a1a315625d9e0486e7733c266fb3a04ae9e6c0cbe8b2).
// Bounded public-CDP test doubles. No browser, namespace or native
// preparation. Each case exercises the current exported collector and inspector.
const test=require('node:test'),assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');
const N=require('./r0040_mechanism_network.cjs');
const base='http://127.0.0.1:40001',blob='blob:'+base+'/review-owned-worker';
const legacy=['dem','colour'].map((name,i)=>({id:10+i,url:base+'/moon/assets/'+name+'.bin.gz',method:'GET',browserState:'finished'}));
const workers=[{event:'worker-constructed',workerId:1,url:blob}];
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const cases=['ordinary','late-held-attachment','late-held-network-response','late-completed-attachment',
  'late-target-info','late-session-detached','late-owned-destruction','final-snapshot-timeout','late-nested-fault'];

async function run(scenario){
  const root=new EventEmitter(),commands=[];
  let snapshots=0,ownedAlive=true;
  const owned={targetId:'owned',type:'worker',url:blob,browserContextId:'owned-context'};
  const late={targetId:'late',type:'worker',url:'blob:'+base+'/late-worker',browserContextId:'owned-context'};
  root.send=async(method,params={})=>{
    commands.push({method,targetId:params.targetId??null});
    if(method==='Target.getTargets'){
      snapshots++;
      if(snapshots===2){
        if(scenario==='final-snapshot-timeout')return new Promise(()=>{});
        if(scenario.startsWith('late-held-')||scenario==='late-completed-attachment'||scenario==='late-nested-fault'){
          root.emit('Target.targetCreated',{targetInfo:late});
          root.emit('Target.targetDestroyed',{targetId:late.targetId});
          // Let the actual attachment attempt enter its Network.enable wait.
          if(scenario!=='late-held-attachment')await pause(2);
        }else if(scenario==='late-target-info'){
          root.emit('Target.targetInfoChanged',{targetInfo:{...owned,browserContextId:'changed-context'}});
        }else if(scenario==='late-session-detached'){
          root.emit('Target.detachedFromTarget',{sessionId:'owned-session',targetId:'owned'});
        }else if(scenario==='late-owned-destruction'){
          ownedAlive=false;root.emit('Target.targetDestroyed',{targetId:'owned'});
        }
      }
      return {targetInfos:ownedAlive?[owned]:[]};
    }
    if(method==='Target.attachToTarget'){
      if(params.targetId==='late'&&scenario==='late-held-attachment')return new Promise(()=>{});
      return {sessionId:params.targetId+'-session'};
    }
    if(method==='Target.sendMessageToTarget'){
      const message=JSON.parse(params.message);
      if(params.sessionId==='late-session'&&scenario==='late-held-network-response')return {};
      queueMicrotask(()=>root.emit('Target.receivedMessageFromTarget',{
        sessionId:params.sessionId,message:JSON.stringify(params.sessionId==='late-session'&&scenario==='late-nested-fault'?
          {id:message.id,error:{code:-1,message:'late Network.enable rejection'}}:{id:message.id,result:{}})}));
    }
    return {};
  };
  const observer=new N.NetworkObserver({timeoutMs:40});
  await observer.start({newBrowserCDPSession:async()=>root},base);
  await observer.settle();
  for(const [i,request]of legacy.entries()){
    const requestId='r'+i;
    observer.observe('owned-session','Network.requestWillBeSent',{
      requestId,timestamp:1+i,type:'Fetch',request,initiator:{type:'script',stack:{callFrames:[]}}});
    observer.observe('owned-session','Network.responseReceived',{
      requestId,timestamp:1.1+i,response:{url:request.url,status:200,headers:{}}});
    observer.observe('owned-session','Network.loadingFinished',{
      requestId,timestamp:1.2+i,encodedDataLength:4});
  }
  if(scenario!=='late-owned-destruction'){
    ownedAlive=false;root.emit('Target.targetDestroyed',{targetId:'owned'});
  }
  const returned=await observer.finish();
  const pendingAtReturn=observer.pending.size,responsesAtReturn=observer.responses.size;
  let status=null,error=null;
  try{status=N.inspectNetwork(returned,legacy,workers).status;}catch(e){error=e.message;}
  const expected=scenario==='ordinary'?'OBSERVED':'INCOMPLETE';
  const accepted=expected==='OBSERVED'?status==='OBSERVED'&&returned.drain.status==='OBSERVED'&&pendingAtReturn===0&&responsesAtReturn===0:
    status===null&&returned.drain.status==='INCOMPLETE';
  await pause(55);
  return {scenario,expected,accepted,status,error,pendingAtReturn,responsesAtReturn,
    returned,afterDeadline:{pending:observer.pending.size,responses:observer.responses.size,faults:observer.raw.faults},commands};
}
for(const scenario of cases)test('final public snapshot completion: '+scenario,async()=>{
  const result=await run(scenario);
  assert.equal(result.accepted,true,JSON.stringify(result));
  assert.equal(result.commands.filter(c=>c.method==='Target.getTargets').length,2);
  assert.ok(result.commands.every(c=>['Target.setDiscoverTargets','Target.getTargets',
    'Target.attachToTarget','Target.sendMessageToTarget'].includes(c.method)));
  if(scenario==='late-nested-fault')assert.ok(result.returned.issues.some(r=>/late Network.enable rejection/.test(r.message)));
});

test('replay requires a complete actual final boundary matching retained lifecycle rows',async()=>{
  const {returned}=await run('ordinary');
  assert.deepEqual(returned.drain.boundary,{lifecycleBefore:2,lifecycleAfter:2,pendingAttachments:0,pendingResponses:0});
  for(const mutate of [x=>delete x.drain.boundary,x=>x.drain.boundary.lifecycleBefore++,
      x=>x.drain.boundary.lifecycleAfter++,x=>x.drain.boundary.pendingAttachments=1,
      x=>x.drain.boundary.pendingResponses=1,x=>x.drain.boundary.lifecycleBefore=true,
      x=>{x.drain.boundary.lifecycleBefore++;x.drain.boundary.lifecycleAfter++;}]){
    const changed=JSON.parse(JSON.stringify(returned));mutate(changed);
    assert.throws(()=>N.inspectNetwork(changed,legacy,workers),/boundary|lifecycle|pending/);
  }
});
