'use strict';
// Synthetic source-control fixture only. No browser or namespace is launched.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {EventEmitter}=require('node:events'),{createHash}=require('node:crypto');
const M=require('./r0040_mechanism.cjs'),P=require('./r0040_passive.cjs'),D=require('./r0040_dateonly.cjs');
const N=require('./r0040_mechanism_network.cjs'),U=require('./r0040_passive_runtime.cjs'),S=require('./r0040_passive_sampler.cjs');
const driver=path.resolve(__dirname,'../r0040/capture.cjs'),identity=M.mechanismIdentity(driver);
const sha=x=>createHash('sha256').update(x).digest('hex'),clone=x=>JSON.parse(JSON.stringify(x));
const diagnostic=D.diagnosticIdentity(D.transformHelper(fs.readFileSync(path.join(__dirname,'fixtures/r0040-precip-eval-original.txt'))).identity);

function clockProof(){
  const preserved=Object.fromEntries(['Date','performance','performanceNow','timeOrigin','setTimeout','clearTimeout','setInterval',
    'clearInterval','requestAnimationFrame','cancelAnimationFrame','queueMicrotask'].map(k=>[k,true]));
  const sample=p=>({performanceBeforeMs:p,performanceAfterMs:p,dateNowMs:1000+p,newDateMs:1000+p,timeOriginMs:1000,preserved});
  const raw={protocol:'r0040-date-only-clock-proof/1',status:'COMPLETE',utcMs:1000,anchorPerformanceMs:0,timeOriginMs:1000,
    before:sample(0),after:sample(41),timer:{requestedDelayMs:40,sample:sample(40)},
    frames:[{timestampMs:10,sample:sample(10)},{timestampMs:20,sample:sample(20)}],error:null};
  return {status:'OBSERVED',raw,admission:D.admitClockProof(raw,1000),error:null};
}
async function completeData(){
  const base='http://127.0.0.1:40001',blob='blob:'+base+'/moon',n=new N.NetworkObserver({timeoutMs:25}),root=new EventEmitter();
  let alive=true;
  root.send=async(method,p={})=>{
    if(method==='Target.getTargets')return {targetInfos:alive?[{targetId:'moon',type:'worker',url:blob}]:[]};
    if(method==='Target.attachToTarget')return {sessionId:'moon-session'};
    if(method==='Target.sendMessageToTarget'){const m=JSON.parse(p.message);queueMicrotask(()=>root.emit('Target.receivedMessageFromTarget',{
      sessionId:p.sessionId,message:JSON.stringify({id:m.id,result:{}})}));}return {};
  };
  await n.start({newBrowserCDPSession:async()=>root},base);await n.settle();
  const requests=['dem','colour'].map((name,i)=>({id:10+i,url:base+'/moon/assets/'+name+'.bin.gz',method:'GET',browserState:'finished'}));
  for(const r of requests){const requestId='protocol-'+r.id;
    n.observe('moon-session','Network.requestWillBeSent',{requestId,timestamp:r.id,loaderId:'',type:'Fetch',request:r,initiator:{type:'script',stack:{callFrames:[]}}});
    n.observe('moon-session','Network.responseReceived',{requestId,timestamp:r.id+.1,response:{url:r.url,status:200,headers:{}}});
    n.observe('moon-session','Network.loadingFinished',{requestId,timestamp:r.id+.2,encodedDataLength:4});
  }
  alive=false;root.emit('Target.targetDestroyed',{targetId:'moon'});await n.finish();
  const stop=Buffer.from('{"result":{"value":[{"at":2010,"phaseMs":13},{"at":2020,"phaseMs":23}]}}\n');
  const sampler={protocol:'r0040-passive-sampler/1',clockDomain:'isolated-performance',timeOriginMs:2000,limit:4096,dropped:0,faults:0,
    rows:[[0,10,12,14],[1,20,22,24]]};
  const observer={protocol:'r0040-passive-workers/1',clockDomain:'main-performance',timeOriginMs:1000,limit:2048,workerLimit:16,
    workersConstructed:1,workersObserved:1,droppedWorkers:0,dropped:0,faults:0,installed:true,prototypePreserved:true,
    events:[{ordinal:0,event:'observer-installed',workerId:null,atMs:1},{ordinal:1,event:'worker-constructed',workerId:1,atMs:2,url:blob,urlType:'string'}]};
  const runtime={protocol:'r0040-passive-runtime-snapshot/1',clockDomain:'main-performance',timeOriginMs:1000,performanceBeforeMs:10,
    performanceAfterMs:20,observer,runtime:{availability:'ABSENT'}};
  const passive={protocol:'r0040-passive-observation/1',identity:identity.passive,errors:[],
    host:{protocol:'r0040-passive-host/1',clockDomain:'node-hrtime',limit:2048,dropped:0,faults:0,
      rows:['observer-created','playwright-page-closed','playwright-context-closed','server-closed'].map((event,ordinal)=>({ordinal,event,monotonicNs:String(ordinal+1)}))},
    runtimes:['readiness-returned','before-context-close'].map(phase=>({phase,status:'OBSERVED',error:null,raw:clone(runtime),inspection:U.inspectRuntime(runtime)})),
    samplers:[{id:1,contextId:9,start:identity.passive.sampler,streamStarted:true,streamStopped:true,originalStopReturned:true,originalSampleCount:2,detached:true,
      originalStopResponse:{protocol:'r0040-passive-original-stop/1',status:'RETAINED',limits:P.STOP_LIMITS,error:null,observedBytes:stop.length,
        artifact:{file:'passive-original-stop-1.json',bytes:stop.length,sha256:sha(stop)}},
      extractions:[{phase:'after-original-stop',status:'OBSERVED',error:null,raw:sampler,inspection:S.inspectSampler(sampler)}]}]};
  const baseBody={protocol:'r0040-capture-final-admission/1',status:D.ADMITTED,exitCode:0,originalExitCode:0,continuationVetoed:false,
    retentionError:null,issues:[],diagnostic,clockProofs:[clockProof()],requests,scene:{base}};
  const baseBytes=Buffer.from(JSON.stringify(baseBody));
  const p={protocol:'r0040-passive-final-observation/1',status:P.ADMITTED,exitCode:0,originalExitCode:0,continuationVetoed:false,retentionError:null,
    timingClass:'instrumented-passive-date-only',nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING',issues:[],
    baseAdmission:{file:'final-admission.json',bytes:baseBytes.length,sha256:sha(baseBytes)},observation:passive,inspection:P.inspectPassive(passive,identity.passive,stop)};
  const passiveBytes=Buffer.from(JSON.stringify(p));
  const observation={protocol:'r0040-mechanism-observation/1',identity,mainInstall:{status:'INSTALLED',identity:identity.main,error:null},
    isolatedInstall:{status:'INSTALLED',identity:identity.isolated,error:null},network:n.snapshot(),
    bracket:{phase:'after-original-stop',main:{status:'OBSERVED',error:null,raw:{protocol:'r0040-mechanism-main-bracket/1',clockDomain:'main-performance',
      timeOriginMs:1000,anchor:{protocol:'r0040-date-only-installed/1',utcMs:1000,anchorPerformanceMs:0,timeOriginMs:1000},limit:4096,calls:2,
      dropped:0,faults:0,clockPreserved:true,datePreserved:true,rows:[[0,100,12,14,'returned'],[1,101,22,24,'returned']]}},
      join:{status:'OBSERVED',error:null,raw:{protocol:'r0040-mechanism-event-join/1',clockDomain:'isolated-event-stamp',timeOriginMs:2000,
        limit:4096,calls:2,dropped:0,faults:0,rows:[[0,100],[1,101]]}}}};
  const inspection=M.inspectMechanism(observation,identity,baseBody,passive,stop);
  assert.equal(inspection.status,'OBSERVED');
  const receipt={protocol:'r0040-mechanism-final-observation/1',status:M.ADMITTED,exitCode:0,originalExitCode:0,continuationVetoed:false,retentionError:null,
    timingClass:M.TIMING,nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING',
    baseAdmission:{file:'final-admission.json',bytes:baseBytes.length,sha256:sha(baseBytes)},
    passiveAdmission:{file:'passive-observation.json',bytes:passiveBytes.length,sha256:sha(passiveBytes)},observation,inspection};
  return {baseBody,baseBytes,passive,passiveBytes,observation,receipt,stop};
}

module.exports={completeData,clockProof,identity,diagnostic};
