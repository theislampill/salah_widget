'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const src=process.env.SALAH_MOON_SOURCE_DIR||path.join(__dirname,'../src');
function rig({inline=false,diameter=104}={}){
 let clock=0,id=0;const jobs=new Map(),workers=[],nodes=new Map(),events=new Map();let published=0,fallbacks=0;
 const state={utcMs:1000,generation:0,sceneIdentity:'A',fraction:.5,waxing:false,up:1,dpr:1,timeScale:0,paused:false};
 for(let i=0;i<2;i++)nodes.set('moon-embedded-'+i,{textContent:'AAAA',remove(){nodes.delete('moon-embedded-'+i)}});
 const detail={available:false,adopt(s){for(const a of [s.linear,s.calendarLinear,s.coverage])for(const v of a)if(!Number.isFinite(v))throw Error('nonfinite worker result');this.available=true},clear(){this.available=false},dispose(){}};
 class Worker{constructor(){this.sent=[];this.terminated=false;workers.push(this)}postMessage(m){if(this.terminated)throw Error('worker closed');this.sent.push(m)}terminate(){this.terminated=true}emit(m){this.onmessage?.({data:m})}}
 class U extends URL{};U.createObjectURL=()=> 'blob:mock/'+(++id);U.revokeObjectURL=()=>{};
 const w={__SALAH_MOON_OFFLINE__:true,__SALAH_MOON_EMBEDDED__:true,SalahMoonHost:{capture:()=>({...state}),publish:()=>published++,fallback:()=>fallbacks++},SalahRealSky:{compose(){}}};
 const doc={currentScript:{src:inline?'':'https://test/moon/moon-host.js'},baseURI:inline?'about:blank':'https://test/',hidden:false,querySelector:()=>({getBoundingClientRect:()=>({width:diameter,height:diameter})}),getElementById:k=>nodes.get(k),createElement:()=>({width:0,height:0,style:{},getContext:()=>({putImageData(){}}),remove(){}}),head:{append(){}},addEventListener:(n,f)=>events.set(n,f),removeEventListener:n=>events.delete(n)};
 const c=vm.createContext({window:w,document:doc,URL:U,Blob,Worker,performance:{now:()=>clock},structuredClone,Uint8ClampedArray,Float32Array,ImageData:class{constructor(d,w,h){this.data=d;this.width=w;this.height=h}},startMoonDetail:()=>detail,blendCalendarBytes:a=>a,setTimeout:(f,ms)=>{const n=++id;jobs.set(n,{f,ms});return n},clearTimeout:n=>jobs.delete(n),setInterval:()=>++id,clearInterval:()=>{},MOON_DEFAULT_PROFILE:{profile_id:'calendar-neutral-v5-01',mode:'calendar'},MOON_WORKER_SOURCE:'',MOON_OFFLINE_CHUNKS:[{name:'dem',index:0,last:true},{name:'colour',index:0,last:true}]});
 vm.runInContext(fs.readFileSync(path.join(src,'moon-precision.mjs'),'utf8')+'\n'+fs.readFileSync(path.join(src,'moon-native.mjs'),'utf8'),c);
 const flush=()=>{for(let guard=0;guard<20;guard++){const j=[...jobs].find(([,v])=>v.ms===0);if(!j)break;jobs.delete(j[0]);j[1].f()}};
 const request=()=>workers.at(-1).sent.findLast(m=>m.kind==='render');
 const response=(kind='result')=>{const r=request(),n=r.scene.size,out=r.scene.outSize;return {kind,id:r.id,identity:r.identity,scene:structuredClone(r.scene),width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:n,surfaceExtent:r.scene.extent,surfaceLinear:new Float32Array(n*n*3),calendarLinear:new Float32Array(n*n*3),surfaceCoverage:new Float32Array(n*n),physicalIdentity:'physical',profileIdentity:'profile',diagnostics:{kernel:'metric-radial-terrain-wasm-mb1',quality:{status:kind==='preview'?'preview':'empirical-adaptive'}}}};
 return {w,workers,state,detail,nodes,events,jobs,flush,request,response,get published(){return published},get fallbacks(){return fallbacks},advance:t=>clock+=t};
}
test('embedded source survives boot-error and a retry replays every chunk',()=>{const r=rig();r.flush();assert.equal(r.workers[0].sent.filter(m=>m.kind==='asset-chunk').length,2);r.workers[0].emit({kind:'boot-error',error:'controlled'});assert.equal(r.w.SalahMoonRuntime.retry(),true);r.flush();assert.equal(r.workers[1].sent.filter(m=>m.kind==='asset-chunk').length,2);assert.equal(r.nodes.size,2);});

test('normal loading and preview cannot publish an inferior Moon before refined terrain',()=>{
 const r=rig();assert.equal(r.w.SalahMoonRuntime.surface(),null);
 r.workers[0].emit({kind:'ready'});const p=r.response('preview');p.diagnostics.quality.status='preview';r.workers[0].emit(p);
 assert.equal(r.w.SalahMoonRuntime.state.status,'refining');
 assert.equal(r.w.SalahMoonRuntime.surface(),null,'Unqualified preview must not become visible');
 assert.equal(r.published,0);assert.equal(r.detail.available,false);
 const f=r.response();f.diagnostics.quality.status='empirical-adaptive';r.workers[0].emit(f);
 assert.ok(r.w.SalahMoonRuntime.surface());assert.equal(r.w.SalahMoonRuntime.state.visibleSource,'refined-terrain');
});

test('unsettled final result is never called a refined visible Moon',()=>{
 const r=rig();r.workers[0].emit({kind:'ready'});const f=r.response();f.diagnostics.quality.status='limit-reached';r.workers[0].emit(f);
 assert.equal(r.w.SalahMoonRuntime.surface(),null);assert.equal(r.published,0);
});
test('malformed numeric surface withdraws safely without publishing',()=>{const r=rig();r.flush();r.workers[0].emit({kind:'ready'});const m=r.response();m.surfaceLinear[0]=NaN;assert.doesNotThrow(()=>r.workers[0].emit(m));assert.equal(r.published,0);assert.equal(r.w.SalahMoonRuntime.state.visibleSource,'withheld-until-refined');assert.equal(r.w.SalahMoonRuntime.state.status,'unavailable');assert.equal(r.workers[0].terminated,true);});
test('complete result becomes current, preview remains pending',()=>{const r=rig();r.workers[0].emit({kind:'ready'});r.workers[0].emit(r.response('preview'));assert.equal(r.w.SalahMoonRuntime.state.status,'refining');assert.equal(r.w.SalahMoonRuntime.state.pending,true);assert.equal(r.w.SalahMoonRuntime.surface(),null);r.workers[0].emit(r.response());assert.equal(r.w.SalahMoonRuntime.state.status,'ready');assert.equal(r.w.SalahMoonRuntime.state.pending,false);r.w.SalahMoonRuntime.dispose();});
test('A B A generations cannot publish the original request',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const stale=r.response();r.state.generation=1;r.state.sceneIdentity='B';r.w.SalahMoonRuntime.request();r.state.generation=2;r.state.sceneIdentity='A';r.w.SalahMoonRuntime.request();r.workers[0].emit(stale);assert.equal(r.published,0);assert.equal(r.w.SalahMoonRuntime.state.rejected,1);});
test('profile change rejects predecessor even at identical phase',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const stale=r.response();r.w.SalahMoonRuntime.setProfile('reference');r.workers[0].emit(stale);assert.equal(r.published,0);assert.equal(r.request().scene.profile.lift,0);});
test('DPR change rejects predecessor',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const m=r.response();r.state.dpr=3;r.w.SalahMoonRuntime.request();r.workers[0].emit(m);assert.equal(r.published,0);});
test('native invalid input withdraws accepted surface',()=>{const r=rig();r.workers[0].emit({kind:'ready'});r.workers[0].emit(r.response());r.state.utcMs=NaN;assert.equal(r.w.SalahMoonRuntime.request(),false);assert.equal(r.w.SalahMoonRuntime.surface(),null);});
test('native time seek invalidates same-geometry work',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const m=r.response();r.state.utcMs-=10000;r.w.SalahMoonRuntime.request();r.workers[0].emit(m);assert.equal(r.published,0);});
test('hide return does not retain a predecessor',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const m=r.response();r.state.paused=true;r.w.SalahMoonRuntime.request();r.state.paused=false;r.w.SalahMoonRuntime.request();r.workers[0].emit(m);assert.equal(r.published,0);});
test('dead-worker cleanup is nonthrowing and bounded retries',()=>{const r=rig();r.workers[0].terminated=true;assert.doesNotThrow(()=>r.workers[0].onerror({message:'crash'}));for(let i=0;i<3;i++){assert.equal(r.w.SalahMoonRuntime.retry(),true);r.workers.at(-1).emit({kind:'boot-error',error:'again'});}assert.equal(r.w.SalahMoonRuntime.retry(),false);});
test('dispose revokes publication and further retry',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const m=r.response();r.w.SalahMoonRuntime.dispose();r.workers[0].emit(m);assert.equal(r.published,0);assert.equal(r.w.SalahMoonRuntime.retry(),false);assert.equal(r.events.size,0);});

test('fully embedded document needs no relative resource base',()=>{const r=rig({inline:true});r.flush();assert.equal(r.workers[0].sent.filter(m=>m.kind==='asset-chunk').length,2);});
test('wrong surface extent is rejected before publication',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const m=r.response();m.surfaceExtent=NaN;r.workers[0].emit(m);assert.equal(r.published,0);assert.equal(r.w.SalahMoonRuntime.state.status,'unavailable');});
test('wrong output footprint is rejected before publication',()=>{const r=rig();r.workers[0].emit({kind:'ready'});const m=r.response();m.width=m.height=8;m.rgba=new Uint8ClampedArray(256);m.calendarRgba=new Uint8ClampedArray(256);r.workers[0].emit(m);assert.equal(r.published,0);assert.equal(r.w.SalahMoonRuntime.state.status,'unavailable');});
test('startup deadline triggers fallback, not a main-thread solver',()=>{const r=rig();const d=[...r.jobs.values()].find(v=>v.ms===120000);assert.ok(d);d.f();assert.equal(r.w.SalahMoonRuntime.state.status,'unavailable');assert.equal(r.published,0);assert.equal(r.workers[0].terminated,true);});
test('refinement deadline withdraws preview safely',()=>{const r=rig();r.workers[0].emit({kind:'ready'});r.workers[0].emit(r.response('preview'));[...r.jobs.values()].find(v=>v.ms===240000).f();assert.equal(r.w.SalahMoonRuntime.surface(),null);assert.equal(r.w.SalahMoonRuntime.state.status,'unavailable');});

test('normal 1x observed Firefox sequence admits the 169-second refinement within the original display error',()=>{
 for(const dpr of [1,1.25,2,3]){
  const r=rig();r.state.dpr=dpr;r.state.timeScale=1;r.state.fraction=.0815410407195768;r.workers[0].emit({kind:'ready'});
  const start=r.request(),final=r.response();r.workers[0].emit(r.response('preview'));
  for(let sec=1;sec<=169;sec++){
   r.advance(1000);r.state.utcMs+=1000;
   // The recorded native phase updates at 60-second intervals; the Moon host polls faster.
   r.state.fraction=sec<60?.0815410407195768:sec<120?.0814985561:.08145601121898355;
   r.w.SalahMoonRuntime.request();
   assert.equal(r.request().id,start.id,`unnecessary phase cancellation at ${sec}s / DPR ${dpr}`);
   const angleError=Math.abs(Math.acos(2*start.scene.fraction-1)-Math.acos(2*r.state.fraction-1));
   assert.ok(104*dpr/2*angleError<=.041600001,'projected terminator displacement exceeds existing budget');
  }
  r.workers[0].emit(final);assert.equal(r.w.SalahMoonRuntime.state.status,'ready');assert.equal(r.w.SalahMoonRuntime.state.pending,false);
  r.advance(600000);r.state.utcMs+=600000;r.state.fraction=.0809;r.w.SalahMoonRuntime.request();
  assert.notEqual(r.request().id,start.id,'phase must not freeze permanently');
 }
});

test('forward and backward seeks reject obsolete results even before the next poll',()=>{
 for(const delta of [-60000,60000]){const r=rig();r.state.timeScale=1;r.workers[0].emit({kind:'ready'});const old=r.response();r.state.utcMs+=delta;r.workers[0].emit(old);assert.equal(r.published,0);r.w.SalahMoonRuntime.request();assert.notEqual(r.request().id,old.id);}
});

test('waxing and reference changes reject old epochs',()=>{
 const r=rig();r.workers[0].emit({kind:'ready'});const old=r.response();r.state.waxing=!r.state.waxing;r.w.SalahMoonRuntime.request();r.workers[0].emit(old);assert.equal(r.published,0);
 const prior=r.response();r.w.SalahMoonRuntime.setReferenceScene({mode:'physical-reference',size:32,outSize:32,basis:[0,1,0,0,0,1,1,0,0],sun:[1,0,0],earth:[384400,0,0],distance:384400,extent:1.08});r.workers[0].emit(prior);assert.equal(r.published,0);
});

test('crescent half gibbous and near-full 1x sequences complete at both senses and DPR 1 through 3',()=>{
 for(const fraction of [.01,.12,.5,.75,.99])for(const waxing of [false,true])for(const dpr of [1,1.25,2,3]){
  const r=rig(),alpha=Math.acos(2*fraction-1);Object.assign(r.state,{fraction,waxing,dpr,timeScale:1});r.workers[0].emit({kind:'ready'});
  let request=r.request(),since=0,complete=false;
  for(let sec=1;sec<=480;sec++){
   r.advance(1000);r.state.utcMs+=1000;
   const a=Math.max(0,Math.min(Math.PI,alpha+(waxing?-1:1)*2.7e-6*Math.floor(sec/60)*60));r.state.fraction=(1+Math.cos(a))/2;
   r.w.SalahMoonRuntime.request();
   if(r.request().id!==request.id){request=r.request();since=sec;}
   const error=104*dpr/2*Math.abs(Math.acos(2*request.scene.fraction-1)-a);assert.ok(error<=.041600001);
   if(sec-since>=169){r.workers[0].emit(r.response());complete=r.w.SalahMoonRuntime.state.status==='ready';break;}
  }
  assert.ok(complete,`${fraction} / ${waxing} / ${dpr} starved`);
 }
});
