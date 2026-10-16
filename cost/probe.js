/* Observation only; installed before generated disposable application scripts. */
(()=>{'use strict';
function recorder(now,capacity=200000){
 const raw=new Float64Array(capacity*7),start=new Float64Array(128),child=new Float64Array(128),children=new Uint16Array(128),ids=new Uint16Array(128),fault=new Uint8Array(128);
 const names=[],lookup=new Map(),errors=[];let depth=0,count=0,invalid=false;
 function enter(name){
  let id=lookup.get(name);if(id===undefined){id=names.length;lookup.set(name,id);names.push(name);}
  const token=depth++;if(token>=128){invalid=true;return token;}if(token)children[token-1]++;ids[token]=id;child[token]=0;children[token]=0;fault[token]=0;start[token]=now();return token;
 }
 function caught(token,error){if(token<128)fault[token]=1;errors.push({at:now(),token,message:String(error?.stack||error).slice(0,2000)});}
 function leave(token){
  const end=now();if(token!==--depth||token>=128){invalid=true;return;}
  const inclusive=end-start[token],exclusive=inclusive-child[token];
  if(depth)child[depth-1]+=inclusive;
  if(count>=capacity||exclusive<-.000001){invalid=true;return;}
  const off=count++*7;raw[off]=ids[token];raw[off+1]=start[token];raw[off+2]=inclusive;raw[off+3]=Math.max(0,exclusive);raw[off+4]=depth;raw[off+5]=fault[token];raw[off+6]=children[token];
 }
 return {enter,leave,caught,mark:()=>({at:now(),count,depth,invalid}),export:()=>({columns:['scopeId','startMs','inclusiveMs','exclusiveElapsedMs','depth','exception','directChildren'],names:[...names],raw:Array.from(raw.subarray(0,count*7)),errors:[...errors],invalid,capacity,probeBufferBytes:raw.byteLength+start.byteLength+child.byteLength+children.byteLength+ids.byteLength+fault.byteLength})};
}
if(typeof window==='undefined'){module.exports={recorder};return;}
const now=performance.now.bind(performance),timing=recorder(now);
const owners=new Map(),raf=new Map(),timers=new Map(),listeners=[],workers=[],canvases=[];
const counts={rafScheduled:0,rafExecuted:0,rafCancelled:0,timerScheduled:0,timerExecuted:0,timerCancelled:0,listenerAdded:0,listenerRemoved:0,workerCreated:0,workerTerminated:0,workerMessagesOut:0,workerMessagesIn:0,canvasCreated:0,canvasResizeWrites:0};
const callbacks=new WeakMap();let callbackSeq=0,bufferSeq=0;const buffers=new WeakMap();
const callbackId=fn=>{if(!callbacks.has(fn))callbacks.set(fn,++callbackSeq);return {id:callbacks.get(fn),name:fn.name||'<anonymous>'};};
const nativeRAF=window.requestAnimationFrame.bind(window),nativeCancel=window.cancelAnimationFrame.bind(window);
window.requestAnimationFrame=function(fn){const meta=callbackId(fn);let id;id=nativeRAF(function(t){raf.delete(id);counts.rafExecuted++;return fn.call(this,t);});raf.set(id,meta);counts.rafScheduled++;return id;};
window.cancelAnimationFrame=function(id){if(raf.delete(id))counts.rafCancelled++;return nativeCancel(id);};
for(const [setName,clearName,interval]of [['setTimeout','clearTimeout',false],['setInterval','clearInterval',true]]){
 const set=window[setName].bind(window),clear=window[clearName].bind(window);
 window[setName]=function(fn,delay,...args){
  if(typeof fn!=='function')throw new Error('Cost probe cannot observe string timers');
  const meta={...callbackId(fn),interval,delay:Number(delay)||0};let id;
  id=set(function(...passed){if(!interval)timers.delete(id);counts.timerExecuted++;return fn.apply(this,passed);},delay,...args);
  timers.set(id,meta);counts.timerScheduled++;return id;
 };
 window[clearName]=function(id){if(timers.delete(id))counts.timerCancelled++;return clear(id);};
}
const nativeAdd=EventTarget.prototype.addEventListener,nativeRemove=EventTarget.prototype.removeEventListener;
EventTarget.prototype.addEventListener=function(type,fn,options){
 if(!fn)return nativeAdd.call(this,type,fn,options);
 const capture=typeof options==='boolean'?options:!!options?.capture;
 const existing=listeners.find(r=>r.active&&!r.signal?.deref()?.aborted&&r.target.deref()===this&&r.fn.deref()===fn&&r.type===type&&r.capture===capture);
 if(existing)return nativeAdd.call(this,type,existing.wrapper.deref(),options);
 const rec={target:new WeakRef(this),fn:new WeakRef(fn),type,capture,once:!!options?.once,signal:options?.signal?new WeakRef(options.signal):null,active:!options?.signal?.aborted,wrapper:null};
 function wrapped(e){if(rec.once)rec.active=false;return typeof fn==='function'?fn.call(this,e):fn.handleEvent(e);}
 rec.wrapper=new WeakRef(wrapped);nativeAdd.call(this,type,wrapped,options);listeners.push(rec);counts.listenerAdded++;
};
EventTarget.prototype.removeEventListener=function(type,fn,options){
 const capture=typeof options==='boolean'?options:!!options?.capture;
 const rec=listeners.find(r=>r.active&&!r.signal?.deref()?.aborted&&r.target.deref()===this&&r.fn.deref()===fn&&r.type===type&&r.capture===capture);
 if(rec){rec.active=false;counts.listenerRemoved++;return nativeRemove.call(this,type,rec.wrapper.deref(),options);}
 return nativeRemove.call(this,type,fn,options);
};
const NativeWorker=window.Worker,workerInfo=new WeakMap();
window.Worker=new Proxy(NativeWorker,{construct(target,args,newTarget){
 const w=Reflect.construct(target,args,newTarget),rec={id:workers.length+1,ref:new WeakRef(w),url:String(args[0]),terminated:false,out:0,in:0,kinds:{}};
 workers.push(rec);workerInfo.set(w,rec);counts.workerCreated++;
 nativeAdd.call(w,'message',()=>{rec.in++;counts.workerMessagesIn++;});return w;
}});
const post=NativeWorker.prototype.postMessage,terminate=NativeWorker.prototype.terminate;
NativeWorker.prototype.postMessage=function(...args){const r=workerInfo.get(this);if(r){r.out++;counts.workerMessagesOut++;const k=String(args[0]?.kind??args[0]?.type??'<none>');r.kinds[k]=(r.kinds[k]||0)+1;}return post.apply(this,args);};
NativeWorker.prototype.terminate=function(){const r=workerInfo.get(this);if(r&&!r.terminated){r.terminated=true;counts.workerTerminated++;}return terminate.call(this);};
const create=Document.prototype.createElement;
Document.prototype.createElement=function(...args){const node=create.apply(this,args);if(node instanceof HTMLCanvasElement){counts.canvasCreated++;canvases.push(new WeakRef(node));}return node;};
for(const key of ['width','height']){const d=Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype,key);Object.defineProperty(HTMLCanvasElement.prototype,key,{...d,set(value){counts.canvasResizeWrites++;return d.set.call(this,value);}});}
function inventory(value){
 const found=[],seen=new WeakSet();let nodes=0,truncated=false;
 function visit(v,p,level){
  if(v===null||typeof v!=='object')return;
  if(seen.has(v))return;seen.add(v);if(++nodes>30000||level>9){truncated=true;return;}
  if(ArrayBuffer.isView(v)||v instanceof ArrayBuffer){const b=v instanceof ArrayBuffer?v:v.buffer;if(!buffers.has(b))buffers.set(b,++bufferSeq);found.push({path:p,type:v.constructor.name,byteLength:v.byteLength,bufferId:buffers.get(b),bufferBytes:b.byteLength});return;}
  if(v instanceof HTMLCanvasElement){found.push({path:p,type:'canvas',width:v.width,height:v.height,connected:v.isConnected});return;}
  if(v instanceof Node||v instanceof Worker)return;
  if(Array.isArray(v))found.push({path:p,type:'Array',length:v.length,capacity:'unavailable'});
  for(const [k,d]of Object.entries(Object.getOwnPropertyDescriptors(v)))if('value'in d)visit(d.value,p+'.'+k,level+1);
 }
 visit(value,'owner',0);return {arraysAndCanvases:found,truncated,visitedObjects:nodes};
}
function snapshot(){
 const begin=now(),ownerState={};
 for(const [name,instances]of owners){try{const state=instances.at(-1).read();ownerState[name]={instanceCount:instances.length,instanceIds:instances.map(x=>x.id),inventory:inventory(state),fields:Object.keys(state),scalars:Object.fromEntries(Object.entries(state).filter(([,v])=>v===null||['string','number','boolean'].includes(typeof v))),pendingId:state.pending?.id??null,acceptedIdentity:state.accepted?.scope??null,workerId:workerInfo.get(state.worker)?.id??null,workerPresent:!!state.worker};}catch(e){ownerState[name]={error:String(e)};}}
 const moon=window.SalahMoonRuntime?.state,sky=window.SalahRealSky?.state,native=window.SalahNativeSkyHost?.capture(false),lunar=window.SalahMoonHost?.capture(),qa=window.qaState?.();
 const rect=document.querySelector('.c')?.getBoundingClientRect();
 return {at:begin,readDurationMs:now()-begin,visibility:document.visibilityState,dpr:devicePixelRatio,fonts:document.fonts.status,fontFaces:[...document.fonts].map(f=>({family:f.family,weight:f.weight,style:f.style,status:f.status})),fontChecks:{Fraunces:document.fonts.check('400 12px Fraunces','CENTRAL FL 0123456789'),Inter:document.fonts.check('400 12px Inter','CENTRAL FL 0123456789')},viewport:{width:innerWidth,height:innerHeight},civilZone:Intl.DateTimeFormat().resolvedOptions().timeZone,civilDate:new Date().toISOString(),card:rect?{width:rect.width,height:rect.height}:null,
  native:native?{utcMs:native.utcMs,lat:native.lat,lon:native.lon,generation:native.generation,timeScale:native.timeScale,paused:native.paused,weather:native.weather,tz:native.tz,camera:native.camera}:null,
  lunar,moon,sky,preview:window.SalahSkyPreview?.state,prayer:{generation:qa?.generation,render:qa?.render,dates:qa?.dates},
  owners:ownerState,counts:{...counts},pendingRAF:[...raf.values()],timers:[...timers.values()],
  listeners:listeners.filter(r=>r.active&&r.target.deref()&&!r.signal?.deref()?.aborted).map(r=>({type:r.type,capture:r.capture,once:r.once,target:r.target.deref()?.constructor.name})),
  workers:workers.map(r=>({id:r.id,url:r.url,reachable:!!r.ref.deref(),terminated:r.terminated,out:r.out,in:r.in,kinds:{...r.kinds}})),
  canvases:[...new Set([...canvases.map(r=>r.deref()).filter(Boolean),...document.querySelectorAll('canvas')])].map(c=>({width:c.width,height:c.height,connected:c.isConnected})),provider:structuredClone(window.__r21Provider||{}),timing:timing.mark()};
}
function overhead(){
 const observed=[];for(let i=0;i<10000;i++){const a=now();timing.leave(timing.enter('probe.empty'));observed.push(now()-a);}
 const nested=[];for(let i=0;i<1000;i++){const a=now(),p=timing.enter('probe.parent');timing.leave(timing.enter('probe.child'));timing.leave(p);nested.push(now()-a);}
 let last=now();const resolution=[];for(let i=0;i<200000&&resolution.length<1000;i++){const t=now();if(t>last){resolution.push(t-last);last=t;}}
 return {emptyObservedMs:observed,nestedObservedMs:nested,clockPositiveStepsMs:resolution};
}
let ownerSequence=0;
window.__r21={...timing,snapshot,overhead,registerOwner:(name,read)=>{if(!owners.has(name))owners.set(name,[]);owners.get(name).push({id:++ownerSequence,read});},ready:()=>{
 const moon=window.SalahMoonRuntime?.state,sky=window.SalahRealSky?.state;
 return {at:now(),ready:moon?.current&&moon?.visibleSource==='refined-terrain'&&!moon.pending&&sky?.status==='ready'&&!sky?.lifecycle?.pending&&document.fonts.status==='loaded',moon:moon?{status:moon.status,current:moon.current,pending:moon.pending,visibleSource:moon.visibleSource}:null,sky:sky?{status:sky.status,pending:sky.lifecycle?.pending}:null};
}};
})();
