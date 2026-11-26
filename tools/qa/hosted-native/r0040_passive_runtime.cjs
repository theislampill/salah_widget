'use strict';
// Serializable main-world observers. They never read pixel/worker source
// bodies, call an adopting runtime getter, or change the product's timers.
function installWorkerObserver(){
  if(Object.hasOwn(globalThis,'__R0040_PASSIVE_WORKERS__'))throw Error('fresh passive Worker witness required');
  const NativeWorker=globalThis.Worker,nativePerformance=performance,nativeNow=performance.now;
  if(typeof NativeWorker!=='function')throw Error('native Worker constructor unavailable');
  const state={protocol:'r0040-passive-workers/1',clockDomain:'main-performance',timeOriginMs:performance.timeOrigin,
    limit:2048,workerLimit:16,workersConstructed:0,workersObserved:0,droppedWorkers:0,dropped:0,faults:0,events:[]};
  const primitive=value=>value===null||typeof value==='boolean'?value:typeof value==='string'?value.slice(0,512):
    typeof value==='number'&&Number.isFinite(value)?value:undefined;
  const own=(value,key)=>{
    if(!value||typeof value!=='object')return undefined;
    const descriptor=Object.getOwnPropertyDescriptor(value,key);
    return descriptor&&Object.hasOwn(descriptor,'value')?descriptor.value:undefined;
  };
  const safe=fn=>{try{return fn();}catch(_){state.faults++;}};
  const record=(event,workerId,fields={})=>safe(()=>{
    const atMs=nativeNow.call(nativePerformance);if(!Number.isFinite(atMs))throw Error('nonfinite observer clock');
    if(state.events.length===state.limit){state.dropped++;return;}
    const row={ordinal:state.events.length,event,workerId,atMs};
    for(const [key,value]of Object.entries(fields)){const v=primitive(value);if(v!==undefined)row[key]=v;}
    state.events.push(row);return row;
  });
  const metadata=data=>{
    const kind=own(data,'kind');if(typeof kind!=='string')return null;
    if(!['boot','ready','boot-error','error','progress','preview','result','cancel','asset-chunk',
      'shard-boot','shard-ready','shard-error','shard-progress','shard-result','shard-cancel','render','shard-render'].includes(kind))return null;
    const fields={kind};
    for(const key of ['id','offline','cache','base','stage','row','total','sourceSamples','selected','name','index','last']){
      const value=primitive(own(data,key));if(value!==undefined)fields[key]=value;
    }
    if(kind==='boot'){const body=own(data,'workerSource');fields.workerSourceType=typeof body;
      if(typeof body==='string')fields.workerSourceLength=body.length;}
    if(['boot-error','error','shard-error'].includes(kind)){const error=primitive(own(data,'error'));if(error!==undefined)fields.error=error;}
    return fields;
  };
  const errorFields=error=>({errorName:primitive(error?.name),error:primitive(error?.message)});
  const Wrapped=new Proxy(NativeWorker,{construct(target,args,newTarget){
    let worker;
    try{worker=Reflect.construct(target,args,newTarget);}
    catch(error){safe(()=>record('worker-construction-threw',null,errorFields(error)));throw error;}
    const workerId=++state.workersConstructed;
    if(state.workersObserved>=state.workerLimit){state.droppedWorkers++;return worker;}
    state.workersObserved++;
    record('worker-constructed',workerId,{url:primitive(args[0]),urlType:typeof args[0]});
    safe(()=>{
      for(const name of ['postMessage','terminate']){
        const method=worker[name];
        Object.defineProperty(worker,name,{configurable:true,writable:true,enumerable:false,value:new Proxy(method,{apply(fn,receiver,values){
          if(receiver!==worker)return Reflect.apply(fn,receiver,values);
          if(name==='terminate')record('worker-terminate',workerId);
          else safe(()=>{const fields=metadata(values[0]);if(fields)record('worker-post',workerId,fields);});
          try{return Reflect.apply(fn,receiver,values);}
          catch(error){safe(()=>record(name==='terminate'?'worker-terminate-threw':'worker-post-threw',workerId,errorFields(error)));throw error;}
        }})});
      }
      worker.addEventListener('message',event=>safe(()=>{const fields=metadata(event.data);if(fields)record('worker-message',workerId,fields);}));
      worker.addEventListener('error',event=>safe(()=>record('worker-error',workerId,
        {error:primitive(event.message),filename:primitive(event.filename),line:primitive(event.lineno),column:primitive(event.colno)})));
      worker.addEventListener('messageerror',()=>record('worker-messageerror',workerId));
    });
    return worker;
  }});
  globalThis.Worker=Wrapped;
  Object.defineProperty(globalThis,'__R0040_PASSIVE_WORKERS__',{configurable:false,writable:false,value:Object.freeze({
    snapshot(){return {...state,installed:globalThis.Worker===Wrapped,prototypePreserved:Wrapped.prototype===NativeWorker.prototype,
      events:state.events.map(row=>({...row}))};}
  })});
  record('observer-installed',null);
}

function snapshotPassiveRuntime(){
  const primitive=value=>value===null||typeof value==='boolean'?value:typeof value==='string'?value.slice(0,512):
    typeof value==='number'&&Number.isFinite(value)?value:undefined;
  const pick=(value,keys)=>Object.fromEntries(keys.flatMap(key=>{
    const descriptor=value&&Object.getOwnPropertyDescriptor(value,key),v=descriptor&&Object.hasOwn(descriptor,'value')?primitive(descriptor.value):undefined;
    return v===undefined?[]:[[key,v]];
  }));
  const before=performance.now(),witness=globalThis.__R0040_PASSIVE_WORKERS__;
  const result={protocol:'r0040-passive-runtime-snapshot/1',clockDomain:'main-performance',timeOriginMs:performance.timeOrigin,
    performanceBeforeMs:before,performanceAfterMs:null,observer:witness?.snapshot()??null,runtime:{availability:'ABSENT'}};
  try{
    const runtime=globalThis.SalahMoonRuntime;
    if(runtime){
      const observed=runtime.observe(),state=observed.state;
      result.runtime={availability:'OBSERVED',disposed:runtime.disposed,
        ...pick(observed,['accepted','waitingPreview','current','wouldPresent','detailAvailable']),
        state:pick(state,['status','backend','workerAlive','retryCount','renders','rejected','cancelled','quality','visibleSource','initialError',
          'reason','retainedReason','pending','epoch','generation','initialRejected','current','degraded','limitation'])};
      for(const key of ['recovery','initialRetry','progress','phaseDisc']){
        const value=Object.getOwnPropertyDescriptor(state,key)?.value;
        result.runtime.state[key]=pick(value,['state','attempts','limit','nextAt','lastClass','outcome','count','notBefore','epoch',
          'stage','row','total','sourceSamples','selected','cause','renders','lastMs','error','errorEpoch']);
      }
      const errors=Object.getOwnPropertyDescriptor(state,'errors')?.value;
      if(Array.isArray(errors))result.runtime.state.errors=errors.slice(-8).map(primitive).filter(value=>value!==undefined);
    }
  }catch(error){result.runtime={availability:'EVALUATION_FAILED',error:{name:String(error?.name??'Error').slice(0,512),message:String(error?.message??error).slice(0,512)}};}
  result.performanceAfterMs=performance.now();return result;
}

function inspectRuntime(raw){
  const need=(ok,message)=>{if(!ok)throw Error(message);};
  const finite=value=>typeof value==='number'&&Number.isFinite(value);
  const count=value=>Number.isSafeInteger(value)&&value>=0;
  need(raw&&raw.protocol==='r0040-passive-runtime-snapshot/1'&&raw.clockDomain==='main-performance'&&
    finite(raw.timeOriginMs)&&raw.timeOriginMs>0&&finite(raw.performanceBeforeMs)&&finite(raw.performanceAfterMs)&&
    raw.performanceBeforeMs>=0&&raw.performanceAfterMs>=raw.performanceBeforeMs,'complete same-domain passive runtime snapshot required');
  const o=raw.observer;
  need(o&&o.protocol==='r0040-passive-workers/1'&&o.clockDomain===raw.clockDomain&&o.timeOriginMs===raw.timeOriginMs&&
    o.limit===2048&&o.workerLimit===16&&o.installed===true&&o.prototypePreserved===true,'complete passive Worker identity required');
  need(['workersConstructed','workersObserved','droppedWorkers','dropped','faults'].every(key=>count(o[key]))&&
    o.workersObserved<=16&&o.workersObserved+o.droppedWorkers===o.workersConstructed,'passive Worker population differs');
  need(o.dropped===0&&o.droppedWorkers===0,'passive Worker overflow is incomplete');
  need(o.faults===0,'passive Worker collection fault is incomplete');
  need(Array.isArray(o.events)&&o.events.length>0&&o.events.length<=2048,'bounded Worker observation prefix required');
  need(o.events[0].event==='observer-installed'&&o.events[0].workerId===null,'passive Worker startup prefix missing');
  let previous=-1,constructed=0;
  for(const [i,row]of o.events.entries()){
    need(row&&row.ordinal===i&&typeof row.event==='string'&&finite(row.atMs)&&row.atMs>=0&&row.atMs>=previous&&row.atMs<=raw.performanceAfterMs&&
      (row.workerId===null||Number.isInteger(row.workerId)&&row.workerId>0&&row.workerId<=o.workersConstructed),
      'Worker event identity or same-domain clock differs');
    previous=row.atMs;
    if(row.event==='worker-constructed')need(row.workerId===++constructed,'Worker construction prefix differs');
    if(row.workerId!==null)need(row.workerId<=constructed,'Worker event precedes observed construction');
    need(Object.values(row).every(value=>value===null||typeof value==='boolean'||typeof value==='string'&&value.length<=512||finite(value)),
      'only bounded primitive Worker fields admitted');
  }
  need(constructed===o.workersObserved,'complete Worker construction prefix required');
  need(raw.runtime&&['ABSENT','OBSERVED'].includes(raw.runtime.availability),'passive runtime unavailable or incomplete');
  if(raw.runtime.availability==='OBSERVED')need(typeof raw.runtime.disposed==='boolean'&&raw.runtime.state&&
    typeof raw.runtime.state==='object'&&!Array.isArray(raw.runtime.state),'passive runtime state incomplete');
  function bounded(value,depth=0){
    if(value===null||typeof value==='boolean'||finite(value)||typeof value==='string'&&value.length<=512)return true;
    if(!value||typeof value!=='object'||depth>3)return false;
    if(Array.isArray(value))return value.length<=8&&value.every(item=>bounded(item,depth+1));
    return Object.keys(value).length<=32&&Object.values(value).every(item=>bounded(item,depth+1));
  }
  need(bounded(raw.runtime),'bounded primitive runtime state required');
  return {protocol:'r0040-passive-runtime-inspection/1',status:'OBSERVED',clockDomain:raw.clockDomain,
    runtimeAvailability:raw.runtime.availability,workersConstructed:o.workersConstructed,events:o.events.length,
    interpretation:'Passive state and host-delivered Worker messages; observed runtime failure or absence is not a product acceptance verdict.'};
}

module.exports={installWorkerObserver,snapshotPassiveRuntime,inspectRuntime};
