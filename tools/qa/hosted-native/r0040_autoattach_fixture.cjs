'use strict';
// Public-CDP fakes only: these exercise the actual collector, never a browser.
const assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');
const N=require(process.env.R0040_AUTOATTACH_TEST_HELPER||'./r0040_autoattach_network.cjs');
const clone=x=>JSON.parse(JSON.stringify(x));
const BASE='http://127.0.0.1:40001',BLOB='blob:'+BASE+'/moon';
const selected=['dem','colour'].map((name,i)=>({id:10+i,url:BASE+'/moon/assets/'+name+'.bin.gz',method:'GET',browserState:'finished'}));
const workers=[{event:'worker-constructed',workerId:1,url:BLOB}];
const policy={autoAttach:true,waitForDebuggerOnStart:false,flatten:false,filter:[{type:'worker'},{exclude:true}]};

function fakeBrowser(options={}){
  const root=new EventEmitter(),calls=[],targets=new Map(),routes=new Map(),held=[];
  const page={targetId:'page',type:'page',url:BASE+'/index.html',browserContextId:'context'};
  targets.set('page',page);routes.set('page',['page-session']);
  let snapshots=0;
  function emit(route,body){
    let nested=body;
    for(let i=route.length-1;i>0;i--)nested={method:'Target.receivedMessageFromTarget',params:{sessionId:route[i],message:JSON.stringify(nested)}};
    root.emit('Target.receivedMessageFromTarget',{sessionId:route[0],message:JSON.stringify(nested)});
  }
  function response(route,message,error){emit(route,error?{id:message.id,error}:{id:message.id,result:{}});}
  function processMessage(route,message){
    calls.push({route:clone(route),method:message.method,params:clone(message.params||{}),id:message.id});
    if(message.method==='Target.sendMessageToTarget'){
      processMessage([...route,message.params.sessionId],JSON.parse(message.params.message));
    }else if(message.method==='Target.setAutoAttach'){
      assert.deepEqual(message.params,policy,'collector must request only bounded no-pause worker attachment');
    }else assert.equal(message.method,'Network.enable','collector must not issue other child commands');
    if(options.onCommand)options.onCommand({route,message,emit,response});
    if(options.hold?.(route,message)){held.push(()=>response(route,message));return;}
    const error=options.reject?.(route,message)?{code:-1,message:'synthetic unsupported '+message.method}:null;
    queueMicrotask(()=>response(route,message,error));
  }
  root.send=async(method,params={})=>{
    calls.push({route:[],method,params:clone(params)});
    if(method==='Target.setDiscoverTargets'){
      if(options.unsupported)throw Error('synthetic discovery unsupported');return {};
    }
    if(method==='Target.getTargets'){
      snapshots++;
      if(snapshots>1&&options.finalSnapshot)await options.finalSnapshot(api);
      return {targetInfos:[...targets.values()].map(clone)};
    }
    if(method==='Target.attachToTarget'){
      assert.equal(params.targetId,'page','manual worker fallback is forbidden');
      assert.equal(params.flatten,false);return {sessionId:'page-session'};
    }
    assert.equal(method,'Target.sendMessageToTarget','collector must use public observation commands');
    processMessage([params.sessionId],JSON.parse(params.message));
    if(options.holdOuter)await new Promise(()=>{});
    return {};
  };
  root.detach=()=>{throw Error('observer detach is forbidden');};
  const api={root,calls,targets,routes,held,emit,response,
    browser:{newBrowserCDPSession:async()=>root},
    addWorker({targetId='moon',parent='page',sessionId=targetId+'-session',url=BLOB,waitingForDebugger=false,discovery='before'}={}){
      const info={targetId,type:'worker',url,browserContextId:'context'},parentRoute=routes.get(parent);
      assert.ok(parentRoute,'fixture parent route required');targets.set(targetId,info);
      if(discovery==='before')root.emit('Target.targetCreated',{targetInfo:info});
      routes.set(targetId,[...parentRoute,sessionId]);
      emit(parentRoute,{method:'Target.attachedToTarget',params:{sessionId,targetInfo:info,waitingForDebugger}});
      if(discovery==='after')root.emit('Target.targetCreated',{targetInfo:info});
      return info;
    },
    close({missingDetach=null,missingDestroy=null}={}){
      for(const [id,route]of [...routes].sort((a,b)=>b[1].length-a[1].length)){
        if(id!==missingDetach){const params={sessionId:route.at(-1),targetId:id};
          if(route.length===1)root.emit('Target.detachedFromTarget',params);
          else emit(route.slice(0,-1),{method:'Target.detachedFromTarget',params});}
        if(id!==missingDestroy){targets.delete(id);root.emit('Target.targetDestroyed',{targetId:id});}
      }
    },
  };
  return api;
}
async function fixture(options={}){
  const fake=fakeBrowser(options),o=new N.NetworkObserver({timeoutMs:35,limits:options.limits,autoLimits:options.autoLimits});
  await o.start(fake.browser,BASE);await o.settle();
  if(options.worker!==false){fake.addWorker(options.workerOptions);await o.settle();}
  const emit=(method,params,target='moon')=>fake.emit(fake.routes.get(target),{method,params});
  const finish=async(closeOptions)=>{fake.close(closeOptions);return o.finish();};
  return {fake,o,emit,finish};
}
function request(f,index,{target='moon',start=true,terminal='finished',bodyGetter=false}={}){
  const requestId='request-'+index,url=selected[index].url;
  if(start)f.emit('Network.requestWillBeSent',{requestId,timestamp:1+index,loaderId:'',type:'Fetch',request:{url,method:'GET'},
    initiator:{type:'script',stack:{callFrames:[{functionName:'read',scriptId:'script',url:BLOB,lineNumber:6,columnNumber:15}]}}},target);
  f.emit('Network.responseReceived',{requestId,timestamp:1.1+index,response:{url,status:200,headers:{'Content-Length':'4'}}},target);
  const data={requestId,timestamp:1.2+index,dataLength:4,encodedDataLength:4};
  if(bodyGetter)Object.defineProperty(data,'data',{get(){throw Error('no body consumer read');}});
  f.emit('Network.dataReceived',data,target);
  if(terminal==='finished')f.emit('Network.loadingFinished',{requestId,timestamp:1.3+index,encodedDataLength:4},target);
  if(terminal==='failed')f.emit('Network.loadingFailed',{requestId,timestamp:1.3+index,errorText:'net::ERR_ABORTED',canceled:true},target);
}
function inspect(raw,legacy=selected,owners=workers){return N.inspectNetwork(raw,legacy,owners,BASE);}
async function complete(options={}){const f=await fixture(options);request(f,0);request(f,1);return {...f,raw:await f.finish()};}


async function completeData(){
  const fs=require('node:fs'),path=require('node:path'),A=require(process.env.R0040_AUTOATTACH_TEST_ENTRY||'./r0040_autoattach.cjs');
  const old=await require('./r0040_mechanism_fixture.cjs').completeData(),network=await complete();
  const identity=A.mechanismIdentity(path.resolve(__dirname,'../r0040/capture.cjs'));
  const observation={...old.observation,protocol:'r0040-autoattach-observation/1',identity,network:network.raw};
  const inspection=A.inspectMechanism(observation,identity,old.baseBody,old.passive,old.stop);
  const receipt={...old.receipt,protocol:'r0040-autoattach-final-observation/1',status:A.ADMITTED,timingClass:A.TIMING,observation,inspection};
  return {...old,identity,observation,receipt};
}
module.exports={fakeBrowser,fixture,request,complete,completeData,inspect,BASE,BLOB,selected,workers,policy};
