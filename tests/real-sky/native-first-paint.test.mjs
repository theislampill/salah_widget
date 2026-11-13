import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {prepareNativeFirstPaint} from '../../real-sky/native-first-paint.mjs';

test('head presentation accepts only a resolved site and native ordinary wall time',()=>{
 const restore={window:globalThis.window,document:globalThis.document,location:globalThis.location,matchMedia:globalThis.matchMedia,ImageData:globalThis.ImageData,devicePixelRatio:globalThis.devicePixelRatio};
 const now=Date.now;let admitted=null,styles=[];
 try{
  Date.now=()=>Date.parse('2026-10-07T15:09:00Z');
  const backgroundRule=Function(fs.readFileSync(new URL('../../moon/src/moon-first-paint.mjs',import.meta.url),'utf8')+'\nreturn nativeHeadMoonBackgroundRule;')();
  // This unit isolates the daytime admission/atmosphere owner. The real Moon
  // composition and DPR mapping have separate source and actual-entry controls.
  globalThis.window={SalahConfig:{resolve:()=>({cfg:admitted})},SalahMoonHead:{compose:()=>({visible:false,presentation:{moonShow:0,moonlight:0}}),backgroundRule}};
  globalThis.devicePixelRatio=1;globalThis.location={hash:'#local=1'};globalThis.matchMedia=()=>({matches:false});
  globalThis.ImageData=class{constructor(data,w,h){assert.equal(data.length,w*h*4);}};
  globalThis.document={head:{append:s=>styles.push(s)},createElement:name=>name==='canvas'?{getContext:()=>({putImageData(){}}),toDataURL:()=> 'data:image/png;test'}:{}};
  prepareNativeFirstPaint();assert.equal(styles.length,0);assert.equal(window.SalahFirstPaint,undefined,'No invented observer or daytime state');
  admitted={lat:28.5383,lon:-81.3792,tz:'America/New_York',units:'c'};prepareNativeFirstPaint();
  assert.equal(window.SalahFirstPaint.snapshot.utcMs,Date.now());assert.equal(window.SalahFirstPaint.value.utcMs,Date.now());
  assert.equal(window.SalahFirstPaint.snapshot.sceneIdentity,'28.5383|-81.3792|America/New_York|wall');assert.equal(window.SalahFirstPaint.value.quality,'physical-background-preview');
  assert.match(styles[0].textContent,/background-image:url/);assert.doesNotMatch(styles[0].textContent,/opacity|display\s*:/);
  // The head already contains the opaque V5 Moon and physical H1 atmosphere.
  // A native paint can reveal the SVG before asynchronous preview publication.
  // Only its four replaced layers may be withdrawn, for this style's lifetime.
  const hidden=[...styles[0].textContent.matchAll(/([^{}]+)\{visibility:hidden!important\}/g)].flatMap(m=>m[1].split(',').map(x=>x.trim())).sort();
  assert.deepEqual(hidden,['.c .sky .mbeam','.c .sky .mglow','.c .sky .moccluder','.c .sky .mphoto'],'Initial scene must not double-compose legacy Moon surface, backing or diffuse light');
  assert.doesNotMatch(styles[0].textContent.split('}')[0],/visibility/,'The card and its celestial scene remain visible');
  assert.match(styles[0].textContent,/--moongrp:0\.000/);
  location.hash='#local=1&simTime=11:00';prepareNativeFirstPaint();assert.equal(styles.length,1,'Explicit temporal owner is not replaced with wall UTC');
  location.hash='#local=1';window.SalahMoonHead.compose=()=>{throw Error('controlled initial surface failure');};prepareNativeFirstPaint();
  assert.equal(styles.length,1,'A failed head preparation cannot install a legacy-layer withdrawal');
  assert.match(window.SalahFirstPaint.error,/controlled initial surface failure/);
 }finally{Date.now=now;for(const [k,v] of Object.entries(restore))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
});

test('boot republishes the accepted preview after native scene invalidation before yielding to prayer transport',async()=>{
 const source=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
 const boot=source.slice(source.indexOf('async function boot(){'),source.indexOf('// SINGLE rAF render clock'));
 const events=[],frames=[],tasks=[];let visible=true;
 const context={_runtimeGeneration:0,_skyInitialDocument:true,finishInitialSkyDocument(){},_cfgMode:'bare',QA:false,lat:28.5,lon:-81.4,
  beginSkyScene(){},simulationReady:()=>true,buildSceneOnce(){},renderMoon(){},startWeather(){events.push('weather');},
  // paint() invalidates the bootstrap scene when it first adopts its scene key.
  render(){visible=false;events.push('native-render');},
  window:{SalahSkyPreview:{update(){visible=true;events.push('preview');}}},
  requestAnimationFrame:cb=>frames.push(cb),MessageChannel:class{constructor(){this.port1={close(){}};this.port2={close(){},postMessage:()=>tasks.push(()=>this.port1.onmessage())};}},fetchWeather(){},fetchRadar(){},
  loadPrayerData(){events.push('prayer-await');return new Promise(()=>{});},startRenderLoop(){}};
 vm.createContext(context);vm.runInContext(boot+'\nboot();',context);
 assert.equal(visible,true,'A valid daytime sky must exist at the first asynchronous yield');
 assert.deepEqual(events,['weather','native-render','preview']);
 frames.shift()();frames.shift()();tasks.shift()();await Promise.resolve();
 assert.equal(visible,true,'Provider acquisition must not withdraw the already-published scene');
 assert.deepEqual(events,['weather','native-render','preview','prayer-await']);
});

for(const cached of [true,false])test(`${cached?'cached':'network'} prayer bootstrap cannot expose a cleared daytime preview`,async()=>{
 const source=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
 const load=source.slice(source.indexOf('async function loadPrayerData(){'),source.indexOf('// Invalid explicit boot postpones'));
 let visible=true,resolve,updates=0,renders=0;
 const day='07-10-2026',data={meta:{timezone:'America/New_York'}};
 const s={simulationReady:()=>true,lat:28.5,lon:-81.4,tz:'America/New_York',today:null,
  _loopStarted:false,_renderDirty:true,_prayerCooldown:{current:{}},
  beginPrayerRequest:()=>({}),prayerCivilDay:()=>day,requestEligible:()=>true,prayerResultEligible:()=>true,
  readPrayerCache:()=>cached?{date:day,timezone:s.tz,data}:null,
  adoptPrayerBundle(){s.today=data;return true;},
  // Actual native paint adopts the scene key and clears the earlier preview.
  render(){renders++;visible=false;},
  window:{SalahSkyPreview:{update(){updates++;visible=true;}}},
  fetchTimings:()=>new Promise(r=>resolve=r),showError(){throw Error('unexpected');},finishPrayerRequest(){}};
 vm.createContext(s);vm.runInContext(load+'\npending=loadPrayerData();',s);
 if(cached)assert.equal(visible,true,'Cached prayer paint must republish before yielding to network/rAF');
 resolve(data);await s.pending;
 assert.equal(visible,true,'Fresh prayer paint must republish before yielding to the first native rAF');
 assert.equal(updates,renders);assert.ok(renders>0);
 // Once running, the existing final native rAF remains the sole presenter.
 const before={updates,renders};s._loopStarted=true;vm.runInContext('pending=loadPrayerData();',s);resolve(data);await s.pending;
 assert.deepEqual({updates,renders},before,'No extra synchronous render or presenter in ordinary operation');
});

// R0034 (issue 101) ISM-SKY-019 parse parity: the head declines exactly when the
// native snapshot would refuse the same fragment, and agrees with it otherwise.
const nativeSource=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
const hooksSource=fs.readFileSync(new URL('../../real-sky/native-host-hooks.js',import.meta.url),'utf8');
function firstPaint(hash,cfg={lat:24.47,lon:39.61,tz:'Asia/Riyadh',units:'c'},reduce=false){
 const restore={window:globalThis.window,document:globalThis.document,location:globalThis.location,matchMedia:globalThis.matchMedia,ImageData:globalThis.ImageData,devicePixelRatio:globalThis.devicePixelRatio};
 const now=Date.now,styles=[];
 try{
  Date.now=()=>Date.parse('2026-10-07T15:09:00Z');
  const backgroundRule=Function(fs.readFileSync(new URL('../../moon/src/moon-first-paint.mjs',import.meta.url),'utf8')+'\nreturn nativeHeadMoonBackgroundRule;')();
  globalThis.window={SalahConfig:{resolve:()=>({cfg})},SalahMoonHead:{compose:()=>({visible:false,presentation:{moonShow:0,moonlight:0}}),backgroundRule}};
  globalThis.devicePixelRatio=1;globalThis.location={hash};globalThis.matchMedia=()=>({matches:reduce});
  globalThis.ImageData=class{constructor(data,w,h){this.data=data;this.width=w;this.height=h;}};
  globalThis.document={head:{append:s=>styles.push(s)},createElement:name=>name==='canvas'?{getContext:()=>({putImageData(){}}),toDataURL:()=> 'data:image/png;test'}:{}};
  prepareNativeFirstPaint();return {styles,fp:window.SalahFirstPaint};
 }finally{Date.now=now;for(const [k,v] of Object.entries(restore))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
}
function nativeCamera(hash){
 const line=hooksSource.match(/const cameraNumber=\(name,fallback\)=>[^;]+;/)[0];
 const q=new URLSearchParams(hash.slice(1));
 return Function('q',line+'\nreturn {azDeg:cameraNumber("skyAz",180),altDeg:cameraNumber("skyAlt",45),fovYDeg:cameraNumber("skyFov",90),rollDeg:cameraNumber("skyRoll",0)};')(q);
}
test('ES34-11 a blank or invalid camera parameter installs no head, as the native snapshot refuses it',()=>{
 for(const key of ['skyAz','skyAlt','skyFov','skyRoll'])for(const raw of ['',' ','abc']){
  const hash=`#local=1&${key}=${encodeURIComponent(raw)}`,native=nativeCamera(hash);
  assert.ok(!Object.values(native).every(Number.isFinite),'native refuses '+hash);
  const {styles,fp}=firstPaint(hash);assert.equal(styles.length,0,hash);assert.equal(fp,undefined,hash);
 }
});
test('ES34-11 numeric camera values equal the native parse',()=>{
 for(const hash of ['#local=1','#local=1&skyAz=12.5&skyAlt=30&skyFov=60&skyRoll=-5','#local=1&skyAz=-90']){
  const {styles,fp}=firstPaint(hash);assert.equal(styles.length,1,hash);assert.deepEqual(fp.snapshot.camera,nativeCamera(hash),hash);
 }
});
test('ES34-11 temporal exclusion keys cover the native temporal owners (simTime, timeScale); simDate stays head-less pending G1',()=>{
 const native=new Set([...nativeSource.matchAll(/q\.get\("(simTime|timeScale|simDate)"\)/g)].map(m=>m[1]));
 assert.deepEqual([...native].sort(),['simTime','timeScale'],'the native clock reads simTime and timeScale and never simDate');
 for(const key of ['simTime=11:00','timeScale=2','timeScale=1'])assert.equal(firstPaint('#local=1&'+key).styles.length,0,key);
 assert.equal(firstPaint('#local=1&simDate=2026-01-01').styles.length,0,'simDate (no native owner) is retained as head-less: accepted moon/tests contract; owner sub-choice G1');
 assert.equal(firstPaint('#local=1&simMoon=0.5').styles.length,1,'a non-temporal simulation key does not suppress the head');
});
test('ES34-11 scene identity and reduced motion equal the native owners for default and non-default zones',()=>{
 const scene=nativeSource.slice(nativeSource.indexOf('function skySceneIdentity(){'),nativeSource.indexOf('let _skySceneKey=null'));
 const motion=nativeSource.match(/const MOTIONFULL = [^;]+;/)[0]+'\n'+nativeSource.match(/const isMotionReduced = [^;]+;/)[0];
 for(const cfg of [{lat:24.47,lon:39.61,tz:'Asia/Riyadh',units:'c'},{lat:51.5072,lon:-0.1276,tz:'Europe/London',units:'f'},{lat:28.5383,lon:-81.3792,units:'c'}])
  for(const hash of ['#local=1','#local=1&motion=full','#local=1&motion=FULL'])for(const reduce of [false,true]){
   const {fp}=firstPaint(hash,cfg,reduce);
   // R002D: the native zone element is the configured effective hint (_cacheTz), default America/New_York.
   const ctx={lat:cfg.lat,lon:cfg.lon,_cacheTz:cfg.tz||'America/New_York',FOLLOW_WALL_CLOCK:true,simNow:()=>0,q:new URLSearchParams(hash.slice(1)),window:{matchMedia:()=>({matches:reduce})}};
   vm.createContext(ctx);vm.runInContext(scene+'\n'+motion+'\nthis.identity=skySceneIdentity();this.reduced=isMotionReduced();',ctx);
   assert.equal(fp.snapshot.sceneIdentity,ctx.identity,JSON.stringify(cfg));assert.equal(fp.snapshot.tz,ctx._cacheTz);
   assert.equal(fp.snapshot.reducedMotion,ctx.reduced,hash+' reduce='+reduce);
  }
});
