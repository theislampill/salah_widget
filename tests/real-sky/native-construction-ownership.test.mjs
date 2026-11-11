import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import * as contract from '../../real-sky/native-contract.mjs';
import {LatestRenderQueue} from '../../real-sky/core/src/latest-render-queue.mjs';
import {ReferenceRenderClient} from '../../real-sky/core/src/reference-worker-client.mjs';
import {nativeCloudChannel,validateNativeRGBA,nativeCloudDisplayFrame} from '../../real-sky/native-cloud-transfer.mjs';

// R0021 ES21 construction/retirement ownership. Executes the REAL authored
// installers (preview host, refined host, asset loader, lifecycle, composition
// and solar publication) in one realm; only browser transport (DOM, canvas,
// Worker, Image, timers) and the expensive astronomy result are controlled.
// Run: node --test tests/real-sky/native-construction-ownership.test.mjs
// This is source evidence, not native/CSP evidence.
const SOURCE_DIR=process.env.SALAH_REAL_SKY_SOURCE_DIR?new URL('file:///'+process.env.SALAH_REAL_SKY_SOURCE_DIR.replace(/\\/g,'/').replace(/\/?$/,'/')):new URL('../../real-sky/',import.meta.url);
const sources=['native-composition','native-lifecycle','native-host','native-preview-host','native-assets'].map(name=>
 fs.readFileSync(new URL(name+'.mjs',SOURCE_DIR),'utf8').replace(/^import .*;\r?\n/gm,'').replaceAll('export ',''));
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};

async function harness({preview=true,assets=true,failPreview=null}={}){
 let serial=0,cloudAlpha=31,previewDraws=0,refinedDraws=0,arm=null;
 const trace=[],nodes=new Set(),classes=new Set(),styleSets=[],images=[],issued=[],workers=[],rafs=new Map(),intervals=new Map(),events=new Map(),docEvents=new Map(),urls=new Set(),counts={revoke:0,terminate:0,removeDoc:0,canvasRemove:0};
 // One-shot failure injection at an exact acquisition stage.
 const fire=stage=>{if(arm===stage){arm=null;throw new Error('controlled '+stage+' failure');}};
 const cloud={width:325,height:530};
 const card={className:'c',style:{setProperty:(k,v)=>styleSets.push([k,v]),removeProperty:k=>styleSets.push([k,null])},classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)},
  prepend:n=>{nodes.add(n);n.parent=card;},append:n=>{nodes.add(n);n.parent=card;}};
 function element(tag){
  const style={};
  const node={tag,width:325,height:530,style,dataset:{},className:'',attrs:{},
   setAttribute(k,v){if(k==='role'&&node.className==='real-sky-status')fire('badge');node.attrs[k]=v;},
   remove(){if(tag==='canvas')counts.canvasRemove++;nodes.delete(node);node.parent=null;},
   getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};
  let text='';Object.defineProperty(node,'textContent',{get:()=>text,set:v=>{if(node.className==='real-sky-status')fire('registered');text=v;}});
  let alpha=0,pixels=null;
  const ctx={resetTransform(){},clearRect(){alpha=0;pixels=null;},fillRect(){},setTransform(){},createLinearGradient:()=>({addColorStop(){}}),
   drawImage(source){if(source===cloud)alpha=cloudAlpha;},
   getImageData(_x,_y,width,height){const data=new Uint8ClampedArray(width*height*4);data[3]=alpha;return {data};},
   putImageData(image){pixels=image.data;trace.push([node.className,crypto.createHash('sha256').update(image.data).digest('hex')]);if(node.className==='real-sky-preview')previewDraws++;if(node.className==='real-sky-canvas')refinedDraws++;}};
  node.getContext=(_type,options)=>{
   if(node.className==='real-sky-canvas'&&arm==='context'){arm=null;return null;}
   if(node.className==='real-sky-preview'&&arm==='preview-context'){arm=null;return null;}
   if(options?.willReadFrequently&&(arm==='foreground'||arm==='preview-foreground')){arm=null;return null;}
   return ctx;};
  node.toDataURL=()=>`data:image/png;base64,controlled-mask-${pixels?.[3]??0}`;
  return node;
 }
 class ControlledImage{
  constructor(){images.push(this);this.value='';}
  set src(value){this.value=value;if(value)issued.push(value);}
  get src(){return this.value;}
  decode(){return new Promise((resolve,reject)=>{this.resolve=resolve;this.reject=reject;});}
 }
 class ControlledWorker{
  constructor(url){fire('worker');this.url=url;this.terminated=false;workers.push(this);}
  postMessage(message){if(message.kind==='boot')queueMicrotask(()=>{if(!this.terminated)this.onmessage?.({data:{kind:'ready'}});});}
  terminate(){if(!this.terminated)counts.terminate++;this.terminated=true;}
 }
 const snapshot={utcMs:1700000000000,lat:24.47,lon:39.61,heightM:0,sceneIdentity:'ownership-control',generation:1,timeScale:1,paused:false,reducedMotion:true,
  camera:{azDeg:180,altDeg:35,fovYDeg:90,rollDeg:0},weather:null,lp:0,units:'c',tz:'UTC'};
 const backgroundRGBA=new Uint8ClampedArray(325*530*4);for(let i=3;i<backgroundRGBA.length;i+=4)backgroundRGBA[i]=255;
 let cloudRevision=0;
 const w={__SALAH_REAL_SKY_PACK__:{controlled:true},
  addEventListener(name,callback){events.set(name,callback);},removeEventListener(name,callback){if(events.get(name)===callback)events.delete(name);},
  // R000B cloud-publication ports: receipts are revisions; withdrawal is out of scope here.
  SalahNativeSkyHost:{capture:()=>{if(arm==='preview-update'){arm=null;throw new Error('controlled preview-update failure');}return {...snapshot};},lunarSurface:()=>null,reconcileClouds:()=>({revision:cloudRevision}),cloudsCurrent:receipt=>!receipt||receipt.revision===cloudRevision}};
 const document={querySelector:q=>q==='.c'?card:q==='.cloudcanvas'?cloud:null,createElement:element,
  addEventListener(name,callback){fire('listener');if(!docEvents.has(name))docEvents.set(name,new Set());docEvents.get(name).add(callback);},
  removeEventListener(name,callback){if(docEvents.get(name)?.delete(callback))counts.removeDoc++;}};
 const context={window:w,document,
  ...contract,LatestRenderQueue,ReferenceRenderClient,nativeCloudChannel,validateNativeRGBA,nativeCloudDisplayFrame,
  Uint8ClampedArray,Float64Array,structuredClone,AbortController,Image:ControlledImage,Worker:ControlledWorker,Blob,
  URL:{createObjectURL:()=>{const url=`blob:controlled-${++serial}`;urls.add(url);return url;},revokeObjectURL(url){if(urls.delete(url))counts.revoke++;}},
  ImageData:class{constructor(data,width,height){this.data=data;this.width=width;this.height=height;}},
  performance:{now:()=>0},getComputedStyle:()=>({filter:'none',visibility:'visible',opacity:'1'}),setTimeout,clearTimeout,
  setInterval:callback=>{fire('interval');const id=++serial;intervals.set(id,callback);return id;},clearInterval:id=>intervals.delete(id),
  requestAnimationFrame:callback=>{fire('raf');const id=++serial;rafs.set(id,callback);return id;},cancelAnimationFrame:id=>rafs.delete(id),
  NativeStarPreview:class{static async create(){return null;}},
  renderNativeBackgroundPreview:s=>({job:contract.nativeJob(s,true),utcMs:s.utcMs,quality:'controlled-background',rgba:backgroundRGBA.slice(),raster:{width:325,height:530,physicalState:{sun:{altDeg:30}}}}),
  encodeNativeFrame(){throw Error('controlled preview supplies its own pixels');},requireNativeWorker(){throw Error('unexpected worker fallback');}};
 vm.createContext(context);vm.runInContext(sources.join('\n'),context);
 const h={trace,window:w,context,classes,styleSets,images,issued,workers,rafs,intervals,events,docEvents,nodes,urls,counts,snapshot,
  arm(stage){arm=stage;},get armed(){return arm;},
  changeMask(){cloudAlpha++;},get draws(){return previewDraws;},get refinedDraws(){return refinedDraws;},
  async finishMasks(){for(const image of images)image.resolve?.();await flush();},
  of:className=>[...nodes].filter(node=>node.className===className),
  listeners:name=>docEvents.get(name)?.size??0,
  resources(){return {rafs:new Set(rafs.keys()),intervals:new Set(intervals.keys()),visibility:new Set(docEvents.get('visibilitychange')??[]),urls:new Set(urls),workers:workers.filter(x=>!x.terminated)};},
  dispatch(name,event={}){const listener=events.get(name);assert(listener,`missing ${name} listener`);listener(event);},
  startRefined(){return context.startNativeSky({controlled:true},'controlled-worker-source',true);},
  close(){try{w.SalahSkyPreview?.dispose();}catch{}try{w.SalahRealSkyAssets?.dispose();}catch{}try{w.SalahRealSky?.dispose();}catch{}}};
 if(preview){if(failPreview)h.arm(failPreview);try{context.startNativeSkyPreview();}catch(error){h.previewError=error;}}
 if(assets){
  context.startNativeSkyAssets(pack=>context.startNativeSky(pack,'controlled-worker-source',true),'https://example.test/real-sky/native-sky.js');
  await flush();await h.finishMasks();
  try{
   assert.equal(w.SalahRealSkyAssets.state.status,'ready');
   if(preview)assert.equal(w.SalahSkyPreview.state.status,'ready',JSON.stringify(w.SalahSkyPreview.state));
  }catch(error){h.close();throw error;}
 }else await flush();
 return h;
}
// Resources created after `before` that are still live.
function leaked(h,before){
 const now=h.resources();
 return {rafs:[...now.rafs].filter(x=>!before.rafs.has(x)).length,intervals:[...now.intervals].filter(x=>!before.intervals.has(x)).length,
  visibility:[...now.visibility].filter(x=>!before.visibility.has(x)).length,urls:[...now.urls].filter(x=>!before.urls.has(x)).length,
  workers:now.workers.filter(x=>!before.workers.includes(x)).length};
}
const none={rafs:0,intervals:0,visibility:0,urls:0,workers:0};

test('ES21-03 healthy construction reaches pending/active with exactly one owned resource set',async()=>{
 const h=await harness();
 try{
  const sky=h.window.SalahRealSky;
  assert.ok(sky);assert.equal(sky.state.lifecycle.disposed,false);assert.match(sky.state.status,/^(loading|pending|ready)$/);
  assert.equal(h.of('real-sky-canvas').length,1);assert.equal(h.of('real-sky-status').length,1);assert.equal(h.of('real-sky-preview').length,1);
  assert.equal(h.intervals.size,1,'one refined request interval');assert.equal(h.listeners('visibilitychange'),1);
  assert.equal(h.workers.filter(x=>!x.terminated).length,1);assert.equal(h.urls.size,1);
  assert.equal(h.window.SalahSkyPreview.state.status,'ready','the preview presentation stays current');
  assert.equal(typeof h.window.realSkyFrame,'function');
 }finally{h.close();}
});

test('ES21-01 failed context leaves no candidate canvas; repeated failures still none; retry yields one',async()=>{
 const h=await harness();
 try{
  for(let i=0;i<2;i++){
   h.arm('context');const result=await h.window.SalahRealSkyAssets.retry();
   assert.equal(result.status,'unavailable');assert.equal(h.armed,null,'the injected context refusal was reached');
   assert.equal(h.of('real-sky-canvas').length,0,`no candidate canvas after failure ${i+1}`);
   assert.equal(h.of('real-sky-status').length,0,'no refined status badge');
   assert.equal(h.window.SalahRealSky,null);
  }
  assert.equal(h.of('real-sky-preview').length,1,'preview fallback remains');
  h.changeMask();h.window.SalahSkyPreview.clear('controlled');h.window.SalahSkyPreview.update();await h.finishMasks();
  assert.equal(h.window.SalahSkyPreview.state.status,'ready','preview fallback still functional');
  const result=await h.window.SalahRealSkyAssets.retry();assert.equal(result.status,'ready');
  assert.equal(h.of('real-sky-canvas').length,1,'recovery constructs exactly one');
 }finally{h.close();}
});

for(const stage of ['context','badge','foreground','worker','interval','raf','listener','registered'])
 test(`ES21-02 failure at ${stage} releases exactly the candidate's resources and touches no unrelated DOM`,async()=>{
  const h=await harness();
  try{
   // A pre-existing unowned node with the same class must not be deleted.
   const stranger=h.context.document.createElement('canvas');stranger.className='real-sky-canvas';stranger.unowned=true;
   h.window.SalahRealSky.dispose();h.window.SalahRealSky=null;h.nodes.add(stranger);
   const before=h.resources(),classes=[...h.classes].sort().join();
   h.arm(stage);
   let error=null;try{h.startRefined();}catch(e){error=e;}
   if(stage==='worker'){
    // Worker refusal is recovered inside the render client (labelled fallback),
    // not a constructor throw; it still owns and later releases its blob URL.
    assert.equal(error,null);assert.equal(h.armed,null);
    const sky=h.window.SalahRealSky;assert.ok(sky);sky.dispose();
   }else{
    assert.ok(error,'construction throws its primary cause');assert.match(String(error.message),new RegExp('controlled '+stage+'|Canvas 2D unavailable|foreground capture unavailable'));
    assert.equal(h.armed,null,'the injected stage was reached');
   }
   assert.deepEqual(h.of('real-sky-canvas'),[stranger],'only the unrelated node remains');
   assert.equal(h.of('real-sky-status').length,0);
   assert.deepEqual(leaked(h,before),none,'no timer, rAF, listener, worker or object URL left without owner');
   assert.equal(h.window.SalahRealSky,null,'no half-registered owner');
   assert.equal([...h.classes].sort().join(),classes,'no card class change');
   // Retry constructs exactly one owner.
   h.nodes.delete(stranger);h.startRefined();
   assert.equal(h.of('real-sky-canvas').length,1);assert.equal(leaked(h,before).intervals,1);assert.equal(leaked(h,before).visibility,1);
  }finally{h.close();}
 });

test('ES21-07 dispose is idempotent and late callbacks of a disposed instance cannot republish',async()=>{
 const h=await harness();
 try{
  const sky=h.window.SalahRealSky,animate=[...h.rafs.values()].at(-1),poll=[...h.intervals.values()].at(-1);
  sky.dispose();
  const after={...h.counts},styles=h.styleSets.length,classes=[...h.classes].sort().join(),draws=h.refinedDraws,issued=h.issued.length;
  assert.doesNotThrow(()=>sky.dispose());
  assert.deepEqual(h.counts,after,'a second dispose releases nothing further');
  // Late callbacks captured before disposal.
  const scheduled=[h.rafs.size,h.intervals.size];
  animate(1e6);poll();sky.compose();sky.request(true);sky.invalidate('late');await flush();
  assert.deepEqual([h.rafs.size,h.intervals.size],scheduled,'a late frame cannot reschedule a retired loop');
  for(const worker of h.workers)worker.onmessage?.({data:{kind:'result',id:1,result:{status:'ready'}}});await flush();
  assert.equal(h.styleSets.length,styles,'no CSS mutation');assert.equal([...h.classes].sort().join(),classes,'no class mutation');
  assert.equal(h.refinedDraws,draws);assert.equal(h.issued.length,issued,'no publication');
  assert.equal(sky.state.status,'disposed');
 }finally{h.close();}
});

test('ES21-07 an exception during retirement still releases every owned resource and settles disposed',async()=>{
 const h=await harness();
 try{
  const sky=h.window.SalahRealSky,before={rafs:new Set(),intervals:new Set(),visibility:new Set(),urls:new Set(),workers:[]};
  const live=leaked(h,before);
  h.window.SalahMoonDetail={clear(){throw new Error('controlled detail clear failure');},state:{skyOwner:'refined-sky'}};
  assert.throws(()=>sky.dispose(),/controlled detail clear failure/,'the primary cause is not swallowed');
  delete h.window.SalahMoonDetail;
  assert.equal(sky.state.status,'disposed');assert.equal(sky.state.lifecycle.disposed,true);
  assert.equal(h.of('real-sky-canvas').length,0);assert.equal(h.of('real-sky-status').length,0);
  assert.equal(h.intervals.size,live.intervals-1);assert.equal(h.listeners('visibilitychange'),0);
  assert(h.workers.every(x=>x.terminated));assert.equal(h.urls.size,0);
  assert.equal(h.window.SalahRealSky,null,'registry released by its owner');
  assert.doesNotThrow(()=>sky.dispose(),'repeat is inert');
 }finally{h.close();}
});

test('ES21-04 retirement is instance-owned: a stale owner cannot affect its successor',async()=>{
 const h=await harness();
 try{
  const a=h.window.SalahRealSky;
  h.startRefined();const b=h.window.SalahRealSky;
  assert.notEqual(a,b);assert.equal(a.state.status,'disposed','declared policy: dispose-then-construct');
  h.classes.add('real-sky-composed');const styles=h.styleSets.length;
  a.dispose();a.invalidate('stale');
  assert.equal(h.window.SalahRealSky,b);assert.equal(b.state.lifecycle.disposed,false);
  assert.equal(h.of('real-sky-canvas').length,1);assert.ok(h.classes.has('real-sky-composed'),'old retirement cannot clear successor DOM');
  assert.equal(h.styleSets.length,styles);
  const intervals=h.intervals.size;b.dispose();
  assert.equal(b.state.status,'disposed');assert.equal(h.intervals.size,intervals-1,'the successor retires its own resources');
  assert.equal(h.of('real-sky-canvas').length,0);assert.equal(h.window.SalahRealSky,null);
 }finally{h.close();}
});

test('ES21-08 declared policy: a failed replacement fully cleans the candidate after disposing the predecessor; preview remains',async()=>{
 const h=await harness();
 try{
  const old=h.window.SalahRealSky;h.arm('interval');
  assert.throws(()=>h.startRefined(),/controlled interval failure/);
  assert.equal(old.state.status,'disposed','predecessor retention is not supported');
  assert.equal(h.window.SalahRealSky,null);assert.equal(h.window.realSkyFrame(),null,'registry tuple coherent: none');
  assert.equal(h.of('real-sky-canvas').length,0);assert.equal(h.intervals.size,0);assert(h.workers.every(x=>x.terminated));assert.equal(h.urls.size,0);
  h.changeMask();h.window.SalahSkyPreview.clear('controlled');h.window.SalahSkyPreview.update();await h.finishMasks();
  assert.equal(h.window.SalahSkyPreview.state.status,'ready','preview fallback functional');
 }finally{h.close();}
});

// Retirement-initiated publication (routed finding; comments 6768062051/6788978150).
for(const terminal of ['pagehide','dispose'])test(`asset ${terminal} retires the refined owner without issuing a preview mask`,async()=>{
 const h=await harness();
 try{
  const old=h.window.SalahRealSky,issued=h.issued.length,draws=h.draws;
  h.changeMask();
  if(terminal==='pagehide')h.dispatch('pagehide');else h.window.SalahRealSkyAssets.dispose();
  assert.equal(h.issued.length,issued,'retirement must not start a new nonempty Image.src publication');
  assert.equal(h.draws,draws);assert.equal(old.state.status,'disposed');assert.equal(old.state.lifecycle.disposed,true);
  assert.equal(h.window.SalahRealSky,null);assert.equal(h.intervals.size,0);assert(h.workers.every(worker=>worker.terminated));
  assert.equal(h.of('real-sky-canvas').length,0);
  assert.equal(h.window.SalahRealSkyAssets.state.status,terminal==='pagehide'?'suspended':'disposed');
  old.dispose();assert.equal(h.issued.length,issued,'repeated retirement stays inert');
  if(terminal==='pagehide'){
   h.dispatch('pageshow',{persisted:true});await flush();await h.finishMasks();
   assert.equal(h.window.SalahRealSkyAssets.state.status,'ready');assert.notEqual(h.window.SalahRealSky,old);
   assert.equal(h.window.SalahSkyPreview.state.status,'ready');assert(h.issued.length>issued,'resumption retains its live preview handoff');
  }else assert.equal(h.events.size,0);
 }finally{h.close();}
});

test('pagehide cancels a pending stale preview mask without replacement or late publication',async()=>{
 const h=await harness();
 try{
  h.changeMask();h.window.SalahSkyPreview.clear('controlled withdrawal');h.window.SalahSkyPreview.update();
  const pending=h.images.at(-1),issued=h.issued.length,draws=h.draws;
  assert(pending.src);h.dispatch('pagehide');
  assert.equal(h.issued.length,issued,'canceling old work cannot start a replacement during pagehide');
  assert.equal(pending.src,'');await h.finishMasks();assert.equal(h.draws,draws,'late old decode cannot restore retired pixels');
  assert.equal(h.window.SalahSkyPreview.state.status,'pending');
 }finally{h.close();}
});

test('live invalidation still initiates its same-turn preview handoff regardless of diagnostic reason',async()=>{
 const h=await harness();
 try{
  h.changeMask();const issued=h.issued.length,draws=h.draws;
  h.window.SalahRealSky.invalidate('disposed');
  assert.equal(h.issued.length,issued+1,'a reason string does not make a live instance retired');
  await h.finishMasks();assert(h.draws>draws);assert.equal(h.window.SalahSkyPreview.state.status,'ready');
  assert.equal(h.window.SalahRealSky.state.lifecycle.disposed,false);
 }finally{h.close();}
});

test('active asset retry preserves its immediate preview handoff and usable successor',async()=>{
 const h=await harness();
 try{
  h.changeMask();const old=h.window.SalahRealSky,issued=h.issued.length;
  const retried=h.window.SalahRealSkyAssets.retry();
  assert.equal(h.issued.length,issued+1,'active retry must hand off before asynchronous asset acquisition');
  await retried;await h.finishMasks();
  assert.equal(old.state.status,'disposed');assert.notEqual(h.window.SalahRealSky,old);
  assert.equal(h.window.SalahRealSkyAssets.state.status,'ready');assert.equal(h.window.SalahSkyPreview.state.status,'ready');
 }finally{h.close();}
});

test('default direct disposal retains the same-turn handoff before any successor exists',async()=>{
 const h=await harness();
 try{
  h.changeMask();const old=h.window.SalahRealSky,issued=h.issued.length;
  old.dispose();
  assert.equal(h.issued.length,issued+1,'no-argument disposal preserves the live handoff without help from a successor');
  assert.equal(old.state.status,'disposed');await h.finishMasks();assert.equal(h.window.SalahSkyPreview.state.status,'ready');
 }finally{h.close();}
});

test('direct refined replacement preserves the default live handoff',async()=>{
 const h=await harness();
 try{
  h.changeMask();const old=h.window.SalahRealSky,issued=h.issued.length;
  h.startRefined();
  assert(h.issued.length>issued,'ordinary replacement retains the existing preview transition');
  await flush();await h.finishMasks();
  assert.equal(old.state.status,'disposed');assert.notEqual(h.window.SalahRealSky,old);
  assert.equal(h.window.SalahRealSky.state.lifecycle.disposed,false);assert.equal(h.window.SalahSkyPreview.state.status,'ready');
 }finally{h.close();}
});

// 10.3 preview host construction (same narrow exception-safety class).
for(const stage of ['preview-context','preview-foreground','raf','preview-update'])
 test(`preview construction failure at ${stage} leaves no orphan canvas or partial owner; retry yields one`,async()=>{
  const h=await harness({assets:false,failPreview:stage});
  try{
   // A refused 2D context is an unavailable optional preview (like a missing
   // card/host): no throw into boot, no owner. Other stages keep their thrown
   // primary cause (the existing public contract).
   if(stage==='preview-context')assert.equal(h.previewError,undefined);
   else assert.ok(h.previewError,'construction reports its primary cause');
   assert.equal(h.armed,null,'the injected stage was reached');
   assert.equal(h.of('real-sky-preview').length,0,'no orphan preview canvas');
   assert.equal(h.window.SalahSkyPreview,undefined,'no half-registered preview owner');
   assert.equal(h.rafs.size,0,'no animation frame left without owner');
   assert.equal(h.classes.has('real-sky-preview-ready'),false);
   h.context.startNativeSkyPreview();await flush();await h.finishMasks();
   assert.equal(h.of('real-sky-preview').length,1,'retry constructs exactly one preview canvas');
   assert.equal(h.window.SalahSkyPreview.state.status,'ready');assert.equal(h.rafs.size,1);
  }finally{h.close();}
 });

test('a healthy preview construction is unchanged: one canvas, registered, ready',async()=>{
 const h=await harness({assets:false});
 try{
  await h.finishMasks();
  assert.equal(h.of('real-sky-preview').length,1);assert.equal(h.window.SalahSkyPreview.state.status,'ready');assert.equal(h.rafs.size,1);
 }finally{h.close();}
});

// Tripwire: sibling suites (native-host-composition, native-preview-host,
// r000b-sky-withdrawal) evaluate text slices of these owners in vm contexts.
// A moved anchor must fail here by name, not as a ReferenceError elsewhere.
test('source-slice anchors used by sibling harnesses remain present and unique',()=>{
 const host=fs.readFileSync(new URL('native-host.mjs',SOURCE_DIR),'utf8'),preview=fs.readFileSync(new URL('native-preview-host.mjs',SOURCE_DIR),'utf8');
 for(const anchor of [' function clear(',' // Identity/age fences',' function compositionFailed(','\n function accept(',' function failure(','\n client=new ReferenceRenderClient'])assert.equal(host.split(anchor).length,2,anchor);
 const lines=host.split('\n');
 assert.equal(lines.filter(line=>line.startsWith(' window.SalahRealSky=')&&line.includes('dispose(')).length,1);
 assert.equal(lines.filter(line=>line.startsWith(' function animate(')).length,1);
 assert.equal(lines.filter(line=>line.startsWith(' function release(')).length,1);
 for(const anchor of [' function clear(',' function prepareForeground'])assert.equal(preview.split(anchor).length,2,anchor);
});

// Visual-identity guard (the look is finished): a scripted NORMAL-operation
// sequence (startup, mask change, live invalidation, active retry, refined
// replacement) yields a presentation trace of every framebuffer upload, CSS
// mask/class write and issued mask request. Run with SALAH_REAL_SKY_SOURCE_DIR
// pointing at the 645b53cc owners to compare; the digest is a diagnostic.
test('normal-operation presentation trace (compare across source revisions)',async t=>{
 const h=await harness();
 try{
  h.changeMask();h.window.SalahSkyPreview.update();await h.finishMasks();
  h.changeMask();h.window.SalahRealSky.invalidate('controlled live withdrawal');await h.finishMasks();
  h.changeMask();await h.window.SalahRealSkyAssets.retry();await h.finishMasks();
  h.changeMask();h.startRefined();await flush();await h.finishMasks();
  const record={uploads:h.trace,styles:h.styleSets,issued:h.issued,classes:[...h.classes].sort(),preview:h.window.SalahSkyPreview.state.status};
  const digest=crypto.createHash('sha256').update(JSON.stringify(record)).digest('hex');
  t.diagnostic('r0021-presentation-trace '+digest+' uploads='+h.trace.length+' styles='+h.styleSets.length+' issued='+h.issued.length);
  assert.ok(h.trace.length>0&&h.issued.length>0);
 }finally{h.close();}
});
