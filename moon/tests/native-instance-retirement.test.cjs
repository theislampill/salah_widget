'use strict';
// R0021 ES21-04/05/06/07/11: Moon runtime/detail instance ownership.
// Executes the REAL authored installer units (moon-install-guard when present,
// moon-detail, moon-precision, moon-native) and, separately, the GENERATED
// moon/moon-host.js wrapper. Only browser transport (DOM, Worker, timers) is
// controlled. Run: node --test moon/tests/native-instance-retirement.test.cjs
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const src=process.env.SALAH_MOON_SOURCE_DIR||path.join(__dirname,'../src');
const read=name=>fs.readFileSync(path.join(src,name),'utf8');
// The installer the generator places first in the host wrapper (absent at 645b53cc).
const guard=fs.existsSync(path.join(src,'moon-install-guard.mjs'))?read('moon-install-guard.mjs'):'';
const wrapper=()=>guard+'\n'+read('moon-native.mjs');

function realm(){
 let id=0;const workers=[],frames=new Map(),intervals=new Map(),timers=new Map(),listeners=new Map(),urls=new Set(),canvases=[];const counts={created:0,revoked:0,removed:0};
 const node=tag=>{const n={tag,width:0,height:0,style:{},className:'',isConnected:false,setAttribute(){},getContext:()=>({putImageData(){},resetTransform(){},clearRect(){}}),remove(){counts.removed++;n.removedCount=(n.removedCount??0)+1;}};if(tag==='canvas')canvases.push(n);return n;};
 class Worker{constructor(url){this.url=url;this.sent=[];this.terminated=false;workers.push(this);}postMessage(m){if(this.terminated)throw Error('worker closed');this.sent.push(m);}terminate(){this.terminated=true;}emit(m){this.onmessage?.({data:m});}}
 class U extends URL{};U.createObjectURL=()=>{counts.created++;const u='blob:mock/'+(++id);urls.add(u);return u;};U.revokeObjectURL=u=>{if(urls.delete(u))counts.revoked++;};
 const state={utcMs:1000,generation:0,sceneIdentity:'A',fraction:.5,waxing:false,up:1,dpr:1,timeScale:0,paused:false};
 const w={__SALAH_MOON_OFFLINE__:false,__SALAH_MOON_EMBEDDED__:true,SalahMoonHost:{capture:()=>({...state,maximumPresentationRatio:1}),publish(){},fallback(){}},SalahRealSky:{compose(){}}};
 const doc={currentScript:{src:''},baseURI:'about:blank',hidden:false,readyState:'complete',querySelector:()=>null,getElementById:()=>null,createElement:node,head:{append(){}},
  addEventListener:(n,f)=>{if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f);},removeEventListener:(n,f)=>{listeners.get(n)?.delete(f);}};
 const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
 const c=vm.createContext({window:w,document:doc,URL:U,Blob,Worker,TextEncoder,atob,assetDigest:digest,performance:{now:()=>0},structuredClone,Uint8ClampedArray,Uint8Array,Float32Array,Float64Array,Math,JSON,
  ImageData:class{constructor(d,w,h){this.data=d;this.width=w;this.height=h;}},blendCalendarBytes:a=>a,validateNativeRGBA:x=>x,nativeCloudChannel:x=>x,getComputedStyle:()=>({opacity:'1',filter:'none'}),devicePixelRatio:1,
  setTimeout:(f,ms)=>{const n=++id;timers.set(n,f);return n;},clearTimeout:n=>timers.delete(n),setInterval:f=>{const n=++id;intervals.set(n,f);return n;},clearInterval:n=>intervals.delete(n),
  requestAnimationFrame:f=>{const n=++id;frames.set(n,f);return n;},cancelAnimationFrame:n=>frames.delete(n),
  MOON_DEFAULT_PROFILE:{profile_id:'calendar-neutral-v5-01',mode:'calendar'},MOON_WORKER_SOURCE:'',MOON_WORKER_PIN:{bytes:10,sha256:digest('testworker')},MOON_OFFLINE_CHUNKS:[]});
 const frame=()=>{const f=[...frames.values()];frames.clear();f.forEach(x=>x(0));};
 const snapshot=()=>({workers:workers.length,canvases:canvases.length,intervals:intervals.size,frames:frames.size,timers:timers.size,visibility:listeners.get('visibilitychange')?.size??0,created:counts.created,detail:w.SalahMoonDetail,runtime:w.SalahMoonRuntime});
 return {c,w,workers,frames,intervals,listeners,canvases,counts,state,frame,snapshot,run:code=>vm.runInContext(code,c)};
}
function boot(){
 const r=realm();
 r.run(read('moon-detail.mjs')+'\n'+read('moon-precision.mjs'));
 r.run(wrapper());r.frame();r.frame();
 return r;
}
const surface={linear:new Float32Array(3),calendarLinear:new Float32Array(3),coverage:Float32Array.of(1),size:1,extent:1,identity:'controlled'};

test('ES21-06 first boot installs one runtime with its own detail and starts one worker',()=>{
 const r=boot(),runtime=r.w.SalahMoonRuntime,detail=r.w.SalahMoonDetail;
 assert.ok(runtime&&detail);assert.equal(r.workers.length,1);assert.equal(r.intervals.size,1);assert.equal(r.listeners.get('visibilitychange').size,1);
 assert.equal(runtime.state.status,'loading');assert.equal(detail.available,false,'no geometry in this realm, but the detail is not disposed');
 assert.doesNotThrow(()=>detail.adopt(surface),'a live detail adopts');
});

test('ES21-06 worker-source refinement and bounded retry remain distinct from wrapper replay',()=>{
 const r=boot(),runtime=r.w.SalahMoonRuntime,detail=r.w.SalahMoonDetail;
 assert.equal(runtime.installWorkerSource('testworker'),true);
 assert.equal(r.w.SalahMoonRuntime,runtime);assert.equal(r.w.SalahMoonDetail,detail,'refinement keeps the same owners');
 r.workers[0].emit({kind:'boot-error',error:'controlled boot failure'});
 assert.equal(r.workers[0].terminated,true);assert.equal(runtime.state.status,'unavailable');
 assert.equal(runtime.retry(),true);assert.equal(r.workers.length,2,'ES21-11 sticky failure recovers through a NEW worker');
 assert.notEqual(r.workers[1],r.workers[0]);assert.equal(r.w.SalahMoonDetail,detail);
});

test('ES21-05 full-wrapper replay over a live runtime is refused before any mutation',()=>{
 const r=boot(),before=r.snapshot(),runtime=r.w.SalahMoonRuntime,detail=r.w.SalahMoonDetail;
 assert.throws(()=>r.run(wrapper()),/replay/i,'unsupported replay is an explicit refusal');
 const after=r.snapshot();
 assert.deepEqual(after,before,'no canvas, worker, timer, rAF, listener, object URL or registry change');
 assert.equal(runtime.state.status,'loading');assert.doesNotThrow(()=>detail.adopt(surface),'the live detail was not disposed');
 assert.equal(r.canvases.filter(x=>x.removedCount).length,0,'no detail canvas removed');
});

test('ES21-04 retirement uses captured resources: an old runtime never disposes its successor detail',()=>{
 const r=boot(),a=r.w.SalahMoonRuntime,da=r.w.SalahMoonDetail;
 a.dispose();
 assert.equal(a.state.status,'disposed');assert.equal(da.adopt(surface),false,'its own captured detail retired');
 assert.notEqual(r.w.SalahMoonDetail,da,'the registry pointer to the retired detail is released');
 // Supported after retirement: a new wrapper with its own detail.
 r.run(wrapper());r.frame();r.frame();
 const b=r.w.SalahMoonRuntime,db=r.w.SalahMoonDetail;
 assert.notEqual(b,a);assert.notEqual(db,da);
 a.dispose();a.invalidate('stale');
 assert.equal(r.w.SalahMoonDetail,db);assert.equal(r.w.SalahMoonRuntime,b);
 assert.doesNotThrow(()=>db.adopt(surface),'the successor detail is live');
 // A late message to the old worker cannot adopt into the successor.
 const old=r.workers[0];old.emit({kind:'ready'});
 assert.equal(b.state.status,'loading');
});

test('ES21-04 conditional registry cleanup: retiring never clears a slot another owner holds',()=>{
 const r=boot(),a=r.w.SalahMoonRuntime,other={dispose(){throw Error('unowned detail disposed');},clear(){},available:false};
 r.w.SalahMoonDetail=other;
 assert.doesNotThrow(()=>a.dispose());assert.equal(r.w.SalahMoonDetail,other);
});

test('ES21-07 detail disposal is idempotent and adoption after disposal is refused',()=>{
 const r=boot(),d=r.w.SalahMoonDetail,cv=r.canvases[0];
 d.dispose();const removed=cv.removedCount;
 assert.doesNotThrow(()=>d.dispose());assert.equal(cv.removedCount,removed,'second dispose releases nothing further');
 assert.equal(d.adopt(surface),false);assert.equal(d.adopt({size:-1}),false,'refused before validation, no throw');
 assert.equal(d.available,false);
});

test('ES21-07 runtime disposal is idempotent and releases its timers, listener, worker and URL once',()=>{
 const r=boot(),a=r.w.SalahMoonRuntime;
 a.dispose();const once={...r.counts,intervals:r.intervals.size,frames:r.frames.size};
 assert.equal(r.intervals.size,0);assert.equal(r.listeners.get('visibilitychange').size,0);assert(r.workers.every(x=>x.terminated));
 a.dispose();assert.deepEqual({...r.counts,intervals:r.intervals.size,frames:r.frames.size},once);
});

// The generated wrapper is the actual consumer of the units above.
test('ES21-05 generated moon-host.js: first install works and a live replay is refused before any mutation',()=>{
 const host=fs.readFileSync(path.join(__dirname,'../moon-host.js'),'utf8'),r=realm();
 delete r.c.MOON_WORKER_SOURCE;delete r.c.MOON_WORKER_PIN;delete r.c.assetDigest;delete r.c.blendCalendarBytes;delete r.c.validateNativeRGBA;delete r.c.nativeCloudChannel;
 r.run(host);r.frame();r.frame();
 const runtime=r.w.SalahMoonRuntime,detail=r.w.SalahMoonDetail,initial=r.w.SalahMoonInitial;
 assert.ok(runtime&&detail,'first install');assert.equal(r.workers.length,1,'refinement source installed through installWorkerSource');
 const before=r.snapshot();
 assert.throws(()=>r.run(host),/replay/i);
 assert.deepEqual(r.snapshot(),before);assert.equal(r.w.SalahMoonInitial,initial,'not even the initial receiver global is replaced');
 assert.doesNotThrow(()=>detail.adopt(surface));
});

// Review follow-ups (independent source review of ef6549c9).
test('ES21-05 replay is refused for a live runtime even when the detail slot is empty',()=>{
 const r=boot(),runtime=r.w.SalahMoonRuntime;r.w.SalahMoonDetail=null;const before=r.snapshot();
 assert.throws(()=>r.run(wrapper()),/replay/i);
 assert.deepEqual(r.snapshot(),before);assert.equal(r.w.SalahMoonRuntime,runtime);
});

for(const stage of ['url','interval','frame'])test(`ES21-02 Moon wrapper failure at ${stage} releases its detail, slot, listener and timers`,()=>{
 const r=realm();r.run(read('moon-detail.mjs')+'\n'+read('moon-precision.mjs'));
 const restore={URL:r.c.URL,setInterval:r.c.setInterval,requestAnimationFrame:r.c.requestAnimationFrame};
 if(stage==='url'){r.w.__SALAH_MOON_EMBEDDED__=false;r.c.URL=class extends restore.URL{constructor(){throw Error('controlled url failure');}};Object.assign(r.c.URL,{createObjectURL:restore.URL.createObjectURL,revokeObjectURL:restore.URL.revokeObjectURL});}
 if(stage==='interval')r.c.setInterval=()=>{throw Error('controlled interval failure');};
 if(stage==='frame')r.c.requestAnimationFrame=()=>{throw Error('controlled frame failure');};
 assert.throws(()=>r.run(wrapper()),new RegExp('controlled '+stage+' failure'));
 Object.assign(r.c,restore);r.w.__SALAH_MOON_EMBEDDED__=true;
 assert.equal(r.w.SalahMoonDetail??null,null,'no orphan registered detail');
 assert.equal(r.canvases.filter(c=>c.className==='moon-detail-canvas'&&!c.removedCount).length,0,'detail canvas released or never created');
 assert.equal(r.listeners.get('visibilitychange')?.size??0,0);assert.equal(r.intervals.size,0);assert.equal(r.frames.size,0);
 assert.equal(r.w.SalahMoonRuntime??null,null,'a half-built runtime does not stay registered');
 // Recovery: a new wrapper installs exactly one live runtime.
 r.run(wrapper());r.frame();r.frame();
 assert.equal(r.w.SalahMoonRuntime.disposed,false);assert.ok(r.w.SalahMoonDetail);assert.equal(r.intervals.size,1);assert.equal(r.workers.length,1);
});
