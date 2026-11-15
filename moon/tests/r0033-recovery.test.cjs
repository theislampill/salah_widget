'use strict';
// R0033 (issue 100): Moon refinement recovery (M1, M1-cache), initial-tier failure
// eligibility (M2), the non-adopting presence predicate (M4, runtime half), the
// Moon-side throw guards (M7) and the generated refinement tail (M3, EF-E04/EF-E07).
// Executes the REAL authored moon-native.mjs / moon-worker.mjs and the GENERATED
// moon/moon-host.js; only browser transport (DOM, Worker, timers, fetch) is a double.
// Run: node --test moon/tests/r0033-recovery.test.cjs
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const src=process.env.SALAH_MOON_SOURCE_DIR||path.join(__dirname,'../src');
const HOST=process.env.SALAH_MOON_HOST||path.join(__dirname,'../moon-host.js');
const BACKOFF=[30000,120000,600000];

function rig({initial=false,file=false,embedded=true,deferWorker=false,initialThrows=0,initialError=null}={}){
 let clock=0,id=0;const jobs=new Map(),frames=new Map(),workers=[],nodes=new Map(),events=new Map(),scripts=[];let published=0,fallbacks=0,initialRenders=0;
 const state={utcMs:1000,generation:0,sceneIdentity:'A',fraction:.5,waxing:false,up:1,dpr:1,timeScale:0,paused:false};
 for(let i=0;i<2;i++)nodes.set('moon-embedded-'+i,{textContent:'AAAA',remove(){nodes.delete('moon-embedded-'+i)}});
 const faults={};
 const detail={available:false,adopt(s){if(faults.adopt)throw new RangeError(faults.adopt);this.available=true},clear(){this.available=false},dispose(){}};
 class Worker{constructor(){this.sent=[];this.terminated=false;workers.push(this)}postMessage(m){if(faults.post?.(m))throw new Error('injected postMessage '+m.kind);this.sent.push(m)}terminate(){this.terminated=true}emit(m){this.onmessage?.({data:m})}}
 class U extends URL{};U.createObjectURL=()=>'blob:mock/'+(++id);U.revokeObjectURL=()=>{};
 const host={capture:()=>({...state,paused:state.paused||doc.hidden,maximumPresentationRatio:1}),publish:()=>{if(faults.publish)throw new Error(faults.publish);published++;},fallback:()=>{fallbacks++;if(faults.fallback)throw new Error(faults.fallback);}};
 const w={__SALAH_MOON_OFFLINE__:true,__SALAH_MOON_EMBEDDED__:embedded&&!file,SalahMoonHost:host,SalahRealSky:{compose(){}}};
 if(initialError)w.SalahMoonInitialError=initialError;
 let throwsLeft=initialThrows;
 if(initial)w.SalahMoonInitial={identity:{sha256:'fixture-receiver'},render(scene){initialRenders++;if(throwsLeft!==0){throwsLeft--;throw new Error('injected initial render failure');}const size=2,out=scene.outSize;return {kind:'initial',scene:{...scene,size},width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:size,surfaceExtent:scene.extent,surfaceLinear:new Float32Array(size*size*3),calendarLinear:new Float32Array(size*size*3),surfaceCoverage:new Float32Array(size*size),physicalIdentity:'initial:'+state.generation,profileIdentity:'profile',diagnostics:{receiverIdentity:'fixture-receiver',quality:{status:'initial-v5'},totalMs:0}};}};
 const doc={currentScript:{src:'https://test/moon/moon-host.js'},baseURI:'https://test/',hidden:false,readyState:'complete',querySelector:()=>({getBoundingClientRect:()=>({width:104,height:104})}),getElementById:k=>nodes.get(k),createElement:()=>({width:0,height:0,style:{},getContext:()=>({putImageData(){}}),remove(){this.removed=true}}),head:{append(el){scripts.push(el)}},addEventListener:(n,f)=>events.set(n,f),removeEventListener:n=>events.delete(n)};
 const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
 const c=vm.createContext({window:w,document:doc,URL:U,Blob,Worker,TextEncoder,assetDigest:digest,performance:{now:()=>clock},structuredClone,Uint8ClampedArray,Float32Array,
  ImageData:class{constructor(d,width,height){if(faults.imageData||d.length!==width*height*4)throw new RangeError(faults.imageData||'ImageData size');this.data=d;this.width=width;this.height=height}},
  startMoonDetail:()=>detail,blendCalendarBytes:a=>{if(faults.blend)throw new RangeError(faults.blend);return a;},setTimeout:(f,ms)=>{const n=++id;jobs.set(n,{f,ms});return n},clearTimeout:n=>jobs.delete(n),setInterval:()=>++id,clearInterval:()=>{},
  MOON_DEFAULT_PROFILE:{profile_id:'calendar-neutral-v5-01',mode:'calendar'},MOON_WORKER_SOURCE:'',MOON_WORKER_PIN:{bytes:10,sha256:digest('testworker')},MOON_OFFLINE_CHUNKS:[{name:'dem',index:0,last:true},{name:'colour',index:0,last:true}]});
 c.requestAnimationFrame=f=>{const n=++id;frames.set(n,f);return n;};c.cancelAnimationFrame=n=>frames.delete(n);
 if(file)c.MOON_OFFLINE_CHUNKS=[0,1].map(index=>({name:'assets/dem.bin.gz',index,path:`file-data/dem-${String(index).padStart(3,'0')}.js`,last:index===1}));
 const frame=()=>{const callbacks=[...frames.values()];frames.clear();callbacks.forEach(f=>f(clock));};
 vm.runInContext(fs.readFileSync(path.join(src,'moon-precision.mjs'),'utf8')+'\n'+fs.readFileSync(path.join(src,'moon-native.mjs'),'utf8'),c);
 if(!deferWorker){frame();frame();}
 const flush=()=>{for(let guard=0;guard<20;guard++){const j=[...jobs].find(([,v])=>v.ms===0);if(!j)break;jobs.delete(j[0]);j[1].f()}};
 const fire=ms=>{for(const [k,v] of [...jobs])if(v.ms===ms){jobs.delete(k);v.f();}};
 const lastRender=()=>workers.at(-1).sent.findLast(m=>m.kind==='render');
 const response=(kind='result',patch={})=>{const r=lastRender(),n=r.scene.size,out=r.scene.outSize;return {kind,id:r.id,identity:r.identity,scene:structuredClone(r.scene),width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:n,surfaceExtent:r.scene.extent,surfaceLinear:new Float32Array(n*n*3),calendarLinear:new Float32Array(n*n*3),surfaceCoverage:new Float32Array(n*n),physicalIdentity:'physical',profileIdentity:'profile',diagnostics:{kernel:'metric-radial-terrain-wasm-mb1',quality:{status:kind==='preview'?'preview':'empirical-adaptive'}},...patch}};
 const rt=()=>w.SalahMoonRuntime;
 // Advance the page clock and give the runtime its ordinary 4 Hz poll opportunity.
 const tick=(ms,step=250)=>{for(let t=0;t<ms;t+=step){clock+=Math.min(step,ms-t);rt().request();}};
 const setHidden=hidden=>{doc.hidden=hidden;events.get('visibilitychange')?.();};
 return {w,c,workers,state,detail,nodes,events,jobs,scripts,faults,doc,frame,flush,fire,lastRender,response,rt,tick,setHidden,
  execute(el){doc.currentScript=el;try{vm.runInContext(fs.readFileSync(path.join(src,'..',new URL(el.src).pathname.replace('/moon/','')),'utf8'),c,{filename:el.src});}finally{doc.currentScript=null;}el.onload?.();},
  get published(){return published},get fallbacks(){return fallbacks},get initialRenders(){return initialRenders},get clock(){return clock},advance:t=>clock+=t};
}
const boots=r=>r.workers.map(x=>x.sent.find(m=>m.kind==='boot'));
const ready=r=>{const w=r.workers.at(-1);w.emit({kind:'ready'});return w;};

// ---- M1: automatic, bounded, classed recovery ----------------------------------
test('R33-01 a transient worker failure recovers automatically after its backoff, without an explicit retry()',()=>{
 const r=rig();ready(r);r.workers[0].emit({kind:'boot-error',error:'Moon asset HTTP 404'});
 const s=r.rt().state;assert.equal(s.status,'unavailable');
 assert.equal(s.recovery.state,'scheduled');assert.equal(s.recovery.attempts,0);assert.equal(s.recovery.lastClass,'boot');assert.equal(s.recovery.nextAt,BACKOFF[0]);
 r.tick(BACKOFF[0]-250);assert.equal(r.workers.length,1,'no attempt before the declared backoff');
 r.tick(250);assert.equal(r.workers.length,2,'the runtime itself starts a NEW worker');
 assert.equal(r.rt().state.retryCount,0,'the QA driver budget is untouched');
 assert.equal(r.rt().state.recovery.attempts,1);
 ready(r);r.rt().refresh();r.workers[1].emit(r.response());
 const after=r.rt().state;assert.equal(after.visibleSource,'refined-terrain');assert.equal(after.recovery.outcome,'recovered');assert.equal(after.recovery.state,'idle');
});

test('R33-02 persistent failure stops at three automatic attempts with the declared backoff, leaves no schedule, and the initial tier keeps presenting',()=>{
 const r=rig({initial:true});r.rt().request();assert.equal(r.rt().state.visibleSource,'initial-v5');
 const starts=[];
 r.workers[0].emit({kind:'boot-error',error:'Moon asset HTTP 503'});
 for(let i=0;i<4*3600*4;i++){const n=r.workers.length;r.tick(250);if(r.workers.length!==n){starts.push(r.clock);r.workers.at(-1).emit({kind:'boot-error',error:'Moon asset HTTP 503'});}}
 assert.equal(r.workers.length,4,'first boot plus exactly three automatic attempts over four simulated hours');
 assert.deepEqual(starts.map((t,i)=>t-(i?starts[i-1]:0)),BACKOFF,'30 s, 2 min, 10 min after each failure');
 const s=r.rt().state;assert.equal(s.recovery.state,'exhausted');assert.equal(s.recovery.attempts,3);assert.equal(s.recovery.nextAt,null);
 assert.equal(s.status,'unavailable');assert.equal(s.current,true);assert.equal(s.visibleSource,'initial-v5','opaque V5 initial disc retained, never blank');
 assert.equal(r.rt().presentable,true);
});

const CLASSES=[
 ['boot-error','boot',true,r=>r.workers[0].emit({kind:'boot-error',error:'Moon asset HTTP 404'})],
 ['worker crash (onerror)','crash',true,r=>r.workers[0].onerror({message:'crash'})],
 ['message decode','crash',true,r=>r.workers[0].onmessageerror()],
 ['startup deadline','deadline',true,r=>r.fire(120000)],
 ['render error','render',true,r=>{ready(r);r.workers[0].emit({kind:'error',id:r.lastRender().id,identity:r.lastRender().identity,error:'Moon row worker failed'});}],
 ['render deadline','deadline',true,r=>{ready(r);r.fire(240000);}],
 ['result contract','contract',false,r=>{ready(r);r.workers[0].emit(r.response('result',{width:7}));}],
 ['quality criterion','contract',false,r=>{ready(r);const m=r.response();m.diagnostics.quality.status='limit-reached';r.workers[0].emit(m);}],
 ['nonfinite surface','contract',false,r=>{ready(r);const m=r.response();m.surfaceCoverage[0]=NaN;r.workers[0].emit(m);}],
 ['message contract','contract',false,r=>r.workers[0].emit(null)],
 ['embedded payload missing','transport-identity',false,null,{deferWorker:true,setup:r=>{r.nodes.clear();r.frame();r.frame();}}],
 ['offline transport identity','transport-identity',false,r=>{const el=r.scripts[0];r.doc.currentScript=el;el.SalahMoonAssetChunk('wrong',0,'AAAA',false);r.doc.currentScript=null;},{file:true}],
 ['offline script unavailable','transport',true,r=>r.scripts[0].onerror(),{file:true}],
 ['job post failure','start',true,r=>{r.faults.post=m=>m.kind==='render';ready(r);}],
];
for(const [name,cls,retry,trigger,options={}] of CLASSES)test(`R33-03 failure class ${name} -> ${cls}, ${retry?'retried':'never retried'}`,()=>{
 const r=rig(options);options.setup?.(r);trigger?.(r);
 const s=r.rt().state;assert.equal(s.status,'unavailable');assert.equal(s.recovery.lastClass,cls);
 assert.equal(s.recovery.state,retry?'scheduled':'exhausted');
 r.faults.post=null;const before=r.workers.length;r.tick(BACKOFF[0]+1000);
 assert.equal(r.workers.length,before+(retry?1:0),retry?'one automatic attempt':'a deterministic class never loops');
});

test('R33-04 (VM) the first boot is cache-preferring and every recovery attempt revalidates',()=>{
 const r=rig();r.workers[0].emit({kind:'boot-error',error:'Moon asset HTTP 404'});r.tick(BACKOFF[0]);
 assert.deepEqual(boots(r).map(m=>m.cache),['force-cache','no-cache']);
 r.workers[1].emit({kind:'boot-error',error:'again'});assert.equal(r.rt().retry(),true,'explicit driver retry keeps its own guard');
 assert.equal(boots(r)[2].cache,'no-cache','a driver retry after failure also revalidates');
});

async function workerRead(cache){
 const seen=[],body=new Uint8Array([1,2,3,4]);
 const self={postMessage(m){seen.push(m);},addEventListener(){}};
 const c=vm.createContext({self,URL,Uint8Array,Promise,Map,DOMException,atob,Error,String,
  fetch:async(url,init)=>{seen.push({fetch:String(url),cache:init?.cache});let sent=false;return {ok:true,status:200,body:{getReader:()=>({read:async()=>sent?{done:true}:(sent=true,{done:false,value:body}),cancel:async()=>{}})}};},
  MOON_ASSET_MANIFEST:{assets:{dem:{path:'assets/dem.bin.gz',bytes:4},colour:{path:'assets/colour.bin.gz',bytes:4}}},MOON_WASM_BASE64:'',
  MoonPool:{create:async()=>({})},adaptiveRender:async()=>{throw new Error('unused');},nativeCalendarResult:()=>({})});
 vm.runInContext(fs.readFileSync(path.join(src,'moon-worker.mjs'),'utf8'),c);
 self.onmessage({data:{kind:'boot',base:'https://test/moon/',offline:false,workerSource:'x',...(cache===undefined?{}:{cache})}});
 for(let i=0;i<20&&!seen.some(m=>m.kind);i++)await new Promise(setImmediate);
 return seen;
}
test('R33-04 (VM) the worker uses the boot message cache mode for asset reads, and only force-cache or no-cache',async()=>{
 for(const [mode,want] of [[undefined,'force-cache'],['force-cache','force-cache'],['no-cache','no-cache'],['reload','force-cache']]){
  const seen=await workerRead(mode);
  assert.deepEqual(seen.filter(m=>m.fetch).map(m=>m.cache),[want,want],String(mode));
  assert.equal(seen.find(m=>m.kind).kind,'ready');
 }
});

test('R33-06 no automatic attempt while hidden; the due attempt starts on the next visible poll',()=>{
 const r=rig();r.workers[0].emit({kind:'boot-error',error:'controlled'});
 r.setHidden(true);r.tick(BACKOFF[0]*3);assert.equal(r.workers.length,1,'never started while hidden');
 assert.equal(r.rt().state.recovery.state,'scheduled');
 r.setHidden(false);assert.equal(r.workers.length,2,'visible after due: start');
});

test('R33-06 dispose during a scheduled wait cancels it; disposed implies idle',()=>{
 const r=rig();r.workers[0].emit({kind:'boot-error',error:'controlled'});r.rt().dispose();
 assert.equal(r.rt().state.recovery.state,'idle');assert.equal(r.rt().state.recovery.nextAt,null);
 r.advance(BACKOFF[0]*4);r.rt().request();r.rt().refresh();assert.equal(r.workers.length,1);assert.equal(r.jobs.size,0);
});

test('R33-06 a live worker blocks automatic starts: explicit retry during the wait leaves exactly one worker',()=>{
 const r=rig();r.workers[0].emit({kind:'boot-error',error:'controlled'});
 assert.equal(r.rt().retry(),true);assert.equal(r.workers.length,2);
 r.tick(BACKOFF[0]*2);assert.equal(r.workers.length,2,'no second concurrent worker');
 assert.equal(r.rt().state.recovery.state,'idle');assert.equal(r.rt().state.recovery.attempts,0,'a driver attempt does not spend the automatic budget');
});

test('R33-06 stale callbacks from a terminated worker neither double-schedule nor spend budget',()=>{
 const r=rig(),old=r.workers[0];old.emit({kind:'boot-error',error:'controlled'});
 const at=r.rt().state.recovery.nextAt;
 old.onerror({message:'late'});old.emit({kind:'boot-error',error:'late'});r.fire(120000);
 assert.equal(r.rt().state.recovery.nextAt,at);assert.equal(r.rt().state.recovery.attempts,0);
});

test('R33-06 target change A->B->A during backoff: the recovered worker renders the current scope and no stale result adopts',()=>{
 const r=rig(),old=r.workers[0];ready(r);const oldJob=r.lastRender();old.emit({kind:'boot-error',error:'controlled'});
 r.state.sceneIdentity='B';r.tick(1000);r.state.sceneIdentity='A';r.state.generation=1;r.tick(BACKOFF[0]);
 assert.equal(r.workers.length,2);ready(r);
 old.emit({...r.response(),id:oldJob.id,identity:oldJob.identity});assert.equal(r.rt().state.current,false,'terminated worker result ignored');
 const job=r.lastRender();assert.ok(job.identity.key.includes('"A"')&&JSON.parse(job.identity.key)[0]===1,'new worker renders the CURRENT generation/scope');
});

test('R33-07 a dead worker never reports paused in a visible document',()=>{
 const r=rig();r.workers[0].emit({kind:'boot-error',error:'controlled'});
 r.setHidden(true);assert.equal(r.rt().state.status,'paused');
 r.setHidden(false);assert.notEqual(r.rt().state.status,'paused');
});

test('R33-08 embedded chunks replay on an automatic attempt; file chunk scripts are requested once per attempt',()=>{
 const e=rig();e.flush();e.workers[0].emit({kind:'boot-error',error:'controlled'});e.tick(BACKOFF[0]);e.flush();
 assert.equal(e.workers[1].sent.filter(m=>m.kind==='asset-chunk').length,2);assert.equal(e.nodes.size,2,'inert payloads retained for the next attempt');
 const f=rig({file:true});f.execute(f.scripts[0]);f.flush();f.execute(f.scripts[1]);f.flush();
 assert.equal(f.scripts.length,2);f.workers[0].emit({kind:'boot-error',error:'controlled'});f.tick(BACKOFF[0]);
 assert.equal(f.workers.length,2);assert.equal(f.scripts.length,3,'one new chunk script for the new attempt');
 f.execute(f.scripts[2]);f.flush();f.execute(f.scripts[3]);f.flush();
 assert.deepEqual(f.workers[1].sent.filter(m=>m.kind==='asset-chunk').map(m=>m.index),[0,1]);
});

// ---- M2: initial-tier transient failure ----------------------------------------
test('R33-10 one transient initial render throw is re-attempted after 60 s and restores the V5 initial tier',()=>{
 const r=rig({initial:true,initialThrows:1,deferWorker:true});r.rt().request();
 let s=r.rt().state;assert.equal(r.rt().surface(),null);assert.match(s.initialError,/injected/);assert.equal(s.initialEligible,false);
 r.tick(59750);assert.equal(r.initialRenders,1,'never re-attempted per frame/poll');
 r.tick(500);s=r.rt().state;assert.equal(r.initialRenders,2);assert.equal(s.visibleSource,'initial-v5');assert.ok(r.rt().surface());
 assert.equal(s.initialEligible,true);assert.match(s.initialError,/injected/,'the record is retained for diagnostics');
});

test('R33-10 a scene epoch (clear) is an eligibility event, at most one re-attempt each, and three throws exhaust the tier',()=>{
 const r=rig({initial:true,initialThrows:-1,deferWorker:true});r.rt().request();
 for(let i=0;i<10;i++){r.rt().invalidate('native beginSkyScene');r.rt().request();r.rt().request();}
 assert.equal(r.initialRenders,3);assert.equal(r.rt().state.initialRetry.state,'exhausted');
 r.tick(3600000,5000);assert.equal(r.initialRenders,3,'exhausted for the page');
});

test('R33-10 a decode failure (SalahMoonInitialError) is permanent and never re-attempted',()=>{
 const r=rig({initial:true,initialError:'decode failed',deferWorker:true});
 r.tick(3600000,5000);r.rt().invalidate('x');r.rt().request();
 assert.equal(r.initialRenders,0);assert.equal(r.rt().state.initialEligible,false);assert.equal(r.rt().state.initialRetry.state,'permanent');
});

test('R33-11 initial throw plus worker failure: no permanent empty slot while either tier can recover',()=>{
 const r=rig({initial:true,initialThrows:1});r.rt().request();r.workers[0].emit({kind:'boot-error',error:'controlled'});
 assert.equal(r.rt().surface(),null);r.tick(60250);
 assert.ok(r.rt().surface(),'initial tier re-attempt restores the opaque disc');assert.equal(r.workers.length,2,'and the refinement worker recovered');
});

// ---- M4: the non-adopting presence predicate -----------------------------------
test('R33-18 presentable is true exactly when presentation() would be, without adopting or publishing',()=>{
 const r=rig();ready(r);assert.equal(r.rt().presentable,false);
 const capture=r.w.SalahMoonHost.capture;let reads=0;
 r.w.SalahMoonHost.capture=()=>{const s=capture();return ++reads===2?{...s,paused:true}:s;};
 r.workers[0].emit(r.response('preview'));r.w.SalahMoonHost.capture=capture;
 assert.equal(r.published,0,'preview queued, not adopted');
 assert.equal(r.rt().presentable,true);assert.equal(r.rt().presentable,true);assert.equal(r.published,0,'the predicate never adopts or publishes');
 assert.ok(r.rt().surface());assert.equal(r.published,1);
 r.state.sceneIdentity='Z';assert.equal(r.rt().presentable,false,'a target change is not presentable');
 r.state.sceneIdentity='A';r.rt().dispose();assert.equal(r.rt().presentable,false);
});

test('R33-18 a failure without a still-matching surface withdraws presentability',()=>{
 const r=rig();ready(r);r.workers[0].emit(r.response('preview'));assert.equal(r.rt().presentable,true);
 r.workers[0].emit({kind:'boot-error',error:'controlled'});assert.equal(r.rt().presentable,true,'a still-matching validated surface is retained');
 r.state.generation++;assert.equal(r.rt().presentable,false);
});

// ---- M7: Moon-side throw guards on request()/surface()/poll()/adoption -----------
const GUARDS=[
 ['syncTexture ImageData size','imageData','texture'],
 ['blendCalendarBytes RangeError','blend','texture'],
 ['SalahMoonHost.publish (toDataURL)','publish','texture'],
];
for(const [name,fault] of GUARDS)test(`R33-27 ${name}: no escape, recorded, presentation withdrawn`,()=>{
 const r=rig();ready(r);r.faults[fault]='injected '+fault;
 assert.doesNotThrow(()=>r.workers[0].emit(r.response()));
 assert.doesNotThrow(()=>r.rt().request());assert.doesNotThrow(()=>r.rt().surface());
 const s=r.rt().state;assert.ok(s.errors.some(e=>e.includes('injected '+fault)),JSON.stringify(s.errors));
 assert.equal(r.rt().surface(),null);assert.equal(r.rt().presentable,false,'no light without a presented surface');
 r.faults[fault]=null;r.rt().refresh();ready(r);
});
test('R33-27 a queued-preview detail.adopt RangeError inside presentation(): surface()/request() do not throw',()=>{
 const r=rig();ready(r);const capture=r.w.SalahMoonHost.capture;let reads=0;
 r.w.SalahMoonHost.capture=()=>{const s=capture();return ++reads===2?{...s,paused:true}:s;};
 r.workers[0].emit(r.response('preview'));r.w.SalahMoonHost.capture=capture;
 r.faults.adopt='injected adopt';
 assert.doesNotThrow(()=>assert.equal(r.rt().surface(),null));assert.doesNotThrow(()=>r.rt().request());
 assert.ok(r.rt().state.errors.some(e=>e.includes('injected adopt')));assert.equal(r.rt().presentable,false);
});
test('R33-27 render postMessage throw goes through failed(); cancel postMessage throw is recorded, never escapes',()=>{
 const r=rig();r.faults.post=m=>m.kind==='render';assert.doesNotThrow(()=>ready(r));
 assert.equal(r.rt().state.recovery.lastClass,'start');
 const q=rig();ready(q);q.faults.post=m=>m.kind==='cancel';
 q.state.fraction=.2;assert.doesNotThrow(()=>q.rt().request());
 assert.ok(q.rt().state.errors.some(e=>e.includes('injected postMessage cancel')));
});
test('R33-27 a throwing native fallback hook cannot escape request()',()=>{
 const r=rig();ready(r);r.workers[0].emit(r.response());r.faults.fallback='injected fallback';
 r.state.generation++;assert.doesNotThrow(()=>r.rt().request());
 assert.ok(r.rt().state.errors.some(e=>e.includes('injected fallback')));
});

// ---- M3: generated wrapper construction failure and refinement tail ---------------
function realm(){
 let id=0;const workers=[],frames=new Map(),intervals=new Map(),timers=new Map(),listeners=new Map();const calls={prepare:0};
 const node=tag=>({tag,width:0,height:0,style:{},className:'',setAttribute(){},getContext:()=>({putImageData(){},resetTransform(){},clearRect(){}}),remove(){}});
 class Worker{constructor(){this.sent=[];workers.push(this);}postMessage(m){this.sent.push(m);}terminate(){}}
 class U extends URL{};U.createObjectURL=()=>'blob:mock/'+(++id);U.revokeObjectURL=()=>{};
 const state={utcMs:1000,generation:0,sceneIdentity:'A',fraction:.5,waxing:false,up:1,dpr:1,timeScale:0,paused:false};
 const w={__SALAH_MOON_OFFLINE__:false,__SALAH_MOON_EMBEDDED__:true,SalahMoonHost:{capture:()=>({...state,maximumPresentationRatio:1}),publish(){},fallback(){}},SalahRealSky:{compose(){}},SalahPrepareFirstPaint(){calls.prepare++;}};
 const doc={currentScript:{src:''},baseURI:'about:blank',hidden:false,readyState:'complete',querySelector:()=>null,getElementById:()=>null,createElement:node,head:{append(){}},
  addEventListener:(n,f)=>{if(!listeners.has(n))listeners.set(n,new Set());listeners.get(n).add(f);},removeEventListener:(n,f)=>{listeners.get(n)?.delete(f);}};
 const c=vm.createContext({window:w,document:doc,URL:U,Blob,Worker,TextEncoder,atob,performance:{now:()=>0},structuredClone,Uint8ClampedArray,Uint8Array,Uint16Array,Int16Array,Float32Array,Float64Array,Math,JSON,
  ImageData:class{constructor(d,w,h){this.data=d;this.width=w;this.height=h;}},getComputedStyle:()=>({opacity:'1',filter:'none'}),devicePixelRatio:1,
  setTimeout:(f,ms)=>{const n=++id;timers.set(n,f);return n;},clearTimeout:n=>timers.delete(n),setInterval:f=>{const n=++id;intervals.set(n,f);return n;},clearInterval:n=>intervals.delete(n),
  requestAnimationFrame:f=>{const n=++id;frames.set(n,f);return n;},cancelAnimationFrame:n=>frames.delete(n)});
 return {c,w,workers,frames,intervals,calls,run:code=>vm.runInContext(code,c)};
}
const generated=()=>{const host=fs.readFileSync(HOST,'utf8'),i=host.lastIndexOf('\nwindow.SalahMoonRuntime');assert.ok(i>0,'refinement tail boundary');return {wrapper:host.slice(0,i+1),tail:host.slice(i+1)};};

test('R33-13 a construction failure leaves an empty slot, a truthful record and a refinement tail that does not throw',()=>{
 const {wrapper,tail}=generated(),r=realm();r.c.setInterval=()=>{throw Error('controlled interval failure');};
 assert.throws(()=>r.run(wrapper),/controlled interval failure/,'construction failure stays loud');
 assert.equal(r.w.SalahMoonRuntime??null,null,'no half-built runtime registered (ES21-02)');
 assert.match(r.w.SalahMoonConstructionError,/controlled interval failure/);
 assert.doesNotThrow(()=>r.run(tail),'EF-E04: no TypeError from the separate refinement script');
 assert.equal(r.workers.length,0);
});

test('R33-14 under DG-1=B the head owner still installs after a construction failure but cannot present a Moon',()=>{
 const {wrapper}=generated(),r=realm();r.c.setInterval=()=>{throw Error('controlled interval failure');};
 assert.throws(()=>r.run(wrapper));
 assert.equal(r.calls.prepare,1,'EF-E07: the sky first paint is still prepared');
 assert.equal(typeof r.w.SalahMoonHead?.compose,'function');
 // A night head request: the head must refuse to present a Moon that would then vanish.
 const night=h=>{try{h.w.SalahMoonHead.compose({raster:{starPreview:true,physicalState:{sun:{altDeg:-40}}}},{timeScale:1,paused:false,utcMs:Date.parse('2026-09-08T19:00:00Z'),lat:24.47,lon:39.61,dpr:1},{moon:'0.5',wax:'1',moonAlt:'20',moonH:'42'},x=>x);return 'composed';}catch(e){return String(e.message);}};
 assert.equal(night(r),'Head Moon qualified initial unavailable','no initial receiver is handed to the head without a registered runtime');
 const healthy=realm();healthy.run(wrapper);assert.ok(healthy.w.SalahMoonRuntime);
 assert.notEqual(night(healthy),'Head Moon qualified initial unavailable','a registered runtime keeps the head Moon');
});

test('R33-13 the tail still fails loudly on a source-identity mismatch and stays idempotent on a live runtime',()=>{
 const {wrapper,tail}=generated(),r=realm();r.run(wrapper);r.run(tail);r.frames.forEach(f=>f(0));
 const frames=[...r.frames.values()];r.frames.clear();frames.forEach(f=>f(0));
 assert.equal(r.workers.length,1);
 assert.doesNotThrow(()=>r.run(tail));r.frames.forEach(f=>f(0));assert.equal(r.workers.length,1,'a duplicate tail never restarts refinement');
 assert.throws(()=>r.run(tail.replace(/\("[\s\S]*"\)/,'("wrong worker")')),/source identity/);
});
