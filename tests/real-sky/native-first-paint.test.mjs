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
  assert.match(styles[0].textContent,/background-image:url/);assert.doesNotMatch(styles[0].textContent,/visibility|opacity|display\s*:/);
  assert.match(styles[0].textContent,/--moongrp:0\.000/);
  location.hash='#local=1&simTime=11:00';prepareNativeFirstPaint();assert.equal(styles.length,1,'Explicit temporal owner is not replaced with wall UTC');
 }finally{Date.now=now;for(const [k,v] of Object.entries(restore))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
});

test('boot republishes the accepted preview after native scene invalidation before yielding to prayer transport',async()=>{
 const source=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
 const boot=source.slice(source.indexOf('async function boot(){'),source.indexOf('// SINGLE rAF render clock'));
 const events=[],frames=[],tasks=[];let visible=true;
 const context={_runtimeGeneration:0,_cfgMode:'bare',QA:false,lat:28.5,lon:-81.4,
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
