'use strict';
// R0033 (issue 100) M4: native lunar-light eligibility is bound to the presented
// Moon surface through the runtime's pure, non-adopting `presentable` predicate.
// Whole generated native runtime in the R001D VM harness; the Moon runtime is either
// absent (the construction-failure fault path) or a stub that presents a current
// surface. Call/state behaviour only: no pixels, compositing or texture proof.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {load,root}=require('./r001d-harness.cjs');
const {nativeInlineRuntime}=require('./native-inline-runtime.cjs');
const sourcePath=process.env.SALAH_R0033_ENTRY||path.join(root,'index.html');
const CONSUMERS=['illumination','beam','cloudLight','localStarWash','localGlow','halo','corona','paraselenae'];
const css=(h,k,sel='.c')=>+h.select(sel).style.getPropertyValue(k);
const microtasks=()=>new Promise(resolve=>setImmediate(resolve));

// A registered runtime that presents a current surface (the R001D stub pattern).
function presenting(h,value=true,{adoptOnRequest=false}={}){
 h.run(`window.__r33={value:${value},adopt:${adoptOnRequest},reads:{presentable:0,surface:0,state:0,detailEnabled:0,request:0}};
  { const cv=document.createElement('canvas');
    window.SalahMoonRuntime={get presentable(){__r33.reads.presentable++;return __r33.value;},
     surface(){__r33.reads.surface++;return __r33.value?cv:null;},
     // Like the real runtime: the initial tier adopts only once the native scene warrants it.
     request(){__r33.reads.request++;const q=SalahMoonHost.capture();if(__r33.adopt&&!__r33.value&&q.presentationReady&&q.initialWarranted){__r33.value=true;SalahMoonHost.publish(cv);}return __r33.value;},
     get state(){__r33.reads.state++;return {status:'ready',visibleSource:'refined-terrain',quality:'empirical-adaptive',accepted:{identity:'stub'}};},
     get detailEnabled(){__r33.reads.detailEnabled++;return false;},invalidate(){},finishInitialDocument(){},presentationUp:1,disposed:false}; }
  document.querySelector('.mphoto').setAttribute('href','data:image/png;base64,STUB');`);
 return h;
}
const night=(extra='')=>load({sourcePath,extraHash:extra});

test('R33-15 no registered runtime (construction-failure path): zero lunar light, reason surface-unavailable, opaque calendar presence kept',()=>{
 const h=night();h.run('SIM.moon="0.5";render();render();');
 const light=h.run('qaState().moonTruth.lunarLight');
 assert.equal(light.eligible,false);assert.equal(light.eligibility,0);assert.equal(light.reason,'surface-unavailable');
 for(const key of CONSUMERS)assert.equal(light[key],0,key);
 for(const key of ['--moonbeam','--mhalo','--mcorona','--mparhelia'])assert.equal(css(h,key),0,key);
 assert.equal(css(h,'--mgo','.mglow'),0,'local glow');assert.equal(h.run('cloudState.moonLit'),0,'cloud light');
 const A=h.run('atmosphere(model())');assert.equal(A.moonLocalWash,0,'star/cloud local wash');assert.equal(A.moonlightIntensity,0,'sky lift input');
 assert.equal(css(h,'--moongrp'),1,'the calendar disc opacity never depends on light permission');assert.equal(css(h,'--moonocc'),1);
 assert.equal(h.run('qaState().moonTruth.moonlightOpacity'),0);
});

for(const optic of ['lunarhalo','paraselene'])test(`R33-15 debugOptic=${optic} cannot force lunar optics without a presented surface`,()=>{
 const h=night('&debugOptic='+optic);h.run('SIM.moon="1";SIM.moonAlt="5";render();render();');
 assert.equal(css(h,optic==='lunarhalo'?'--mhalo':'--mparhelia'),0);
 assert.equal(h.run('qaState().moonTruth.lunarLight.reason'),'surface-unavailable');
});

test('R33-16 a presented current surface keeps the R0022 eligible light',()=>{
 const h=presenting(night());h.run('render();SIM.moon="0.5";render();');
 const light=h.run('qaState().moonTruth.lunarLight');assert.equal(light.eligible,true);assert.equal(light.reason,'eligible');
 assert.ok(css(h,'--moonbeam')>0);assert.ok(light.cloudLight>0&&light.localStarWash>0);
});

test('R33-18 the eligibility path reads only the pure predicate (no surface(), state, detailEnabled or request())',()=>{
 const h=presenting(night());h.run('render();');
 h.run('for(const k in __r33.reads)__r33.reads[k]=0;');
 const p=h.run('lunarPresentation(-40)');assert.equal(p.moonLightEligible,true);
 assert.deepEqual(JSON.parse(h.run('JSON.stringify(__r33.reads)')),{presentable:1,surface:0,state:0,detailEnabled:0,request:0});
});

test('R33-18 static: no production path grants native lunar light without the presence predicate',()=>{
 const native=nativeInlineRuntime(fs.readFileSync(sourcePath,'utf8'));
 const calls=[...native.matchAll(/nativeLunarPresentation\(/g)].length;
 assert.equal(calls,2,'one definition and one gated call site');
 const gate=native.match(/^function lunarPresentation\(solarElevation\)\{[^\n]*\}$/m)?.[0];
 assert.ok(gate&&/nativeLunarPresentation\(moonSky,solarElevation,!/.test(gate)&&gate.includes('moonSurfacePresentable()'),gate);
 assert.ok(!/nativeLunarPresentation\([^)]*_pbrFailed/.test(native),'the legacy decode flag is no longer a light input');
 const predicate=native.slice(native.indexOf('function moonSurfacePresentable('),native.indexOf('\n}',native.indexOf('function moonSurfacePresentable('))+2);
 assert.ok(predicate.includes('.presentable'),predicate);
 for(const forbidden of ['surface(','.state','detailEnabled','request(','presentation('])assert.ok(!predicate.includes(forbidden),forbidden);
});

test('R33-18 frozen clock: publish/fallback mark a render only when the presence decision changes',async()=>{
 const h=presenting(night(),false);h.run('render();render();');
 assert.equal(css(h,'--moonbeam'),0);assert.equal(h.run('_renderDirty'),false);
 h.run('SalahMoonHost.publish(document.createElement("canvas"))');await microtasks();
 assert.equal(h.run('_renderDirty'),false,'an unchanged decision schedules nothing (no render loop)');
 h.run('__r33.value=true;SalahMoonHost.publish(document.createElement("canvas"))');await microtasks();
 assert.equal(h.run('_renderDirty'),true,'an adopted surface after the last render requests one');
 h.run('_renderDirty=false;render();');assert.ok(css(h,'--moonbeam')>0,'eligible light within one frame');
 h.run('__r33.value=false;SalahMoonHost.fallback()');await microtasks();
 assert.equal(h.run('_renderDirty'),true);h.run('_renderDirty=false;render();');assert.equal(css(h,'--moonbeam'),0,'withdrawn the same way');
});

test('R33-18 a surface adopted during paint defers the sky commit to the consistent next render (no unlit committed frame)',async()=>{
 const h=presenting(night(),false,{adoptOnRequest:true});h.run('render();');
 assert.equal(h.run('_skyCommitted'),false,'the frame computed without the surface is not committed');
 await microtasks();assert.equal(h.run('_renderDirty'),true);
 h.run('_renderDirty=false;render();');
 assert.equal(h.run('_skyCommitted'),true);assert.ok(css(h,'--moonbeam')>0);
});

test('R33-18 coherence: without a timetable, a surface adopted by the celestial paint is revealed WITH its moonlight in the same call',()=>{
 const h=presenting(night(),false,{adoptOnRequest:true});
 h.run('window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:-40,azDeg:90},utcMs:simNow(),sample:()=>null})};today=null;tomorrow=null;render();');
 assert.equal(h.run('model()'),null,'no-timetable path');
 assert.equal(h.select('.c').classList.contains('moon-ready'),true,'disc revealed');
 assert.ok(css(h,'--moonbeam')>0,'with its light in the same call, never an unlit disc that later brightens');
});

