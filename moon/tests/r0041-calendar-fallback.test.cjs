'use strict';
// R0041 owner decision 2 (issue 143, "Owner decision recorded — R0041 remaining Moon-presence routes"): when refinement
// expires with no immediately adoptable successor, the fallback is the EXISTING V5 calendar presentation through the
// same presenter, never retention of the expired surface (the 0.0416 device-pixel bound is unchanged).
// The V5 calendar presentation (moon-calendar.mjs calendarProxy / blendCalendarBytes) is DERIVED from a rendered phase
// surface: its only producers are the V5 initial receiver (window.SalahMoonInitial.render) and a worker result. These
// tests prove where it is and is not available. Drives the UNMODIFIED rigs of r0033-recovery.test.cjs (extracted
// read-only) over the REAL authored moon-native.mjs and the GENERATED moon/moon-host.js.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const r33=fs.readFileSync(path.join(__dirname,'r0033-recovery.test.cjs'),'utf8');
const cut=(from,to)=>{const a=r33.indexOf(from),b=r33.indexOf(to,a);assert.ok(a>=0&&b>a,'rig boundary '+from);return r33.slice(a,b);};
const NL=String.fromCharCode(10);
const body=cut('const src=','const boots=')+cut('function realm(){','test(\'R33-13 a construction failure');
const {rig,realm,generated}=new Function('require','__dirname','process','fs','vm','path','crypto','assert',body+';return {rig,realm,generated};')(require,__dirname,process,fs,vm,path,crypto,assert);
const native=fs.readFileSync(path.join(__dirname,'../src/moon-native.mjs'),'utf8');
const D=104,BOUND=.0416;
const result=(r,patch={})=>{const m=r.response('result');m.diagnostics={kernel:'metric-radial-terrain-wasm-mb1',quality:{status:'empirical-adaptive'}};return Object.assign(m,patch);};
// A presented refined surface, then the Moon moves past the unchanged bound in the same scope with no refined successor.
function refinedThenExpire(r,{up=1}={}){
 Object.assign(r.state,{timeScale:1,up,fraction:.6,waxing:true});
 const w=r.workers.at(-1);w.emit({kind:'ready'});r.rt().request();w.emit(result(r));
 assert.equal(r.rt().state.visibleSource,'refined-terrain');
 const before={fallbacks:r.fallbacks,renders:r.initialRenders,expired:r.rt().state.accepted.scene};
 const a=Math.acos(2*r.state.fraction-1)-3*BOUND*2/D;r.state.fraction=(1+Math.cos(a))/2;r.advance(250);r.state.utcMs+=250;r.rt().request();
 return before;
}
const sceneGeometry=s=>({fraction:s.fraction,sun:s.sun,basis:s.basis,earth:s.earth,extent:s.extent,outSize:s.outSize,waxing:s.waxing,leadDirection:s.leadDirection});

test('R41-CAL-SRC: the V5 calendar presentation has exactly two producers, the initial receiver and a worker result',()=>{
 // calendarBytes (the below-horizon calendar texture) is set only in adopt(), from an initial-receiver result or a
 // validated worker message; every other assignment withdraws it. No third (legacy or synthesised) producer exists.
 const sets=[...native.matchAll(/calendarBytes=([^;,]+)/g)].map(m=>m[1]);
 assert.deepEqual([...new Set(sets)].sort(),['m.calendarRgba','null'].sort(),JSON.stringify(sets));
 assert.equal((native.match(/calendarBytes=m\.calendarRgba/g)||[]).length,1,'only adopt() sets it');
 assert.equal((native.match(/SalahMoonInitial\.render\(/g)||[]).length,1,'the receiver renders in one place (initialPresentation)');
 assert.ok(!/renderMoonCalendarFallback|SalahMoonLegacy|legacyFallback=true/.test(native),'the deprecated legacy Moon is never a producer');
});

for(const up of [1,0])test(`R41-CAL-1 (receiver available, up=${up}): expiry without a refined successor presents the V5 tier for the CURRENT phase through the one presenter`,()=>{
 const r=rig({initial:true}),b=refinedThenExpire(r,{up}),s=r.rt().state;
 assert.equal(s.visibleSource,'initial-v5');assert.equal(r.fallbacks,b.fallbacks,'no withdrawal: nothing is hidden first');
 assert.equal(r.detail.available,true,'the runtime-owned detail presents it');assert.equal(r.rt().presentable,true);
 assert.equal(r.initialRenders,b.renders+1,'one receiver render (eligibility unchanged)');
 // Phase and limb geometry: within the UNCHANGED bound for the current capture (the canonical scene is placed one
 // bound ahead of the motion, exactly as every refined job is), and the SAME directed calendar scene a refined request
 // for this capture uses (the worker's next job), so the terminator, lit limb and disc footprint match the refined disc.
 assert.ok(Math.abs(s.phasePrecision.signedPositionDrift)<=BOUND+1e-9,String(s.phasePrecision.signedPositionDrift));
 const job=r.lastRender().scene;assert.equal(JSON.stringify(sceneGeometry(s.accepted.scene)),JSON.stringify(sceneGeometry(job)),'cross-realm values compared by value');
 assert.notDeepEqual(s.accepted.scene.fraction,b.expired.fraction,'never the expired surface');
 assert.equal(s.calendarProxyWeight,1-up,'below the horizon this IS the calendar disc the product shows (weight 1); above, the lit V5 tier');
});

test('R41-CAL-2a (receiver missing at construction): the calendar presentation is NOT available; the route is not met',()=>{
 const r=rig({initial:false}),b=refinedThenExpire(r),s=r.rt().state;
 assert.equal(s.initialRetry.state,'permanent');assert.equal(s.initialEligible,false,'no producer for the current phase');
 assert.equal(s.visibleSource,'awaiting-terrain');assert.equal(r.rt().presentable,false);assert.equal(r.detail.available,false);
 assert.equal(r.fallbacks,b.fallbacks+1,'truthful withdrawal (no retention of the expired surface)');
 assert.ok(r.rt().state.pending,'the in-flight refined successor is the only producer left (asynchronous)');
});

test('R41-CAL-2b (receiver decode failure, SalahMoonInitialError): the calendar presentation is NOT available; the route is not met',()=>{
 const r=rig({initial:true,initialError:'decode failed'}),b=refinedThenExpire(r),s=r.rt().state;
 assert.equal(s.initialRetry.state,'permanent');assert.equal(r.initialRenders,0,'never rendered');
 assert.equal(s.visibleSource,'awaiting-terrain');assert.equal(r.fallbacks,b.fallbacks+1);
});

test('R41-CAL-3 (initial-tier budget exhausted): the calendar presentation is NOT available without breaking R0033 M2; the route is not met',()=>{
 const r=rig({initial:true,initialThrows:-1});
 for(let i=0;i<4;i++){r.rt().invalidate('native beginSkyScene');r.rt().request();}
 assert.equal(r.rt().state.initialRetry.state,'exhausted');assert.equal(r.initialRenders,3);
 const b=refinedThenExpire(r),s=r.rt().state;
 assert.equal(r.initialRenders,3,'the exhausted receiver is never called again (R0033 M2 budget unchanged)');
 assert.equal(s.visibleSource,'awaiting-terrain');assert.equal(r.rt().presentable,false);assert.equal(r.fallbacks,b.fallbacks+1);
});

test('R41-CAL-4 (waiting re-attempt, R0033 M2): inside the 60 s wait the receiver is not called early; not met until it is eligible',()=>{
 const r=rig({initial:true,initialThrows:1});r.rt().request();assert.equal(r.rt().state.initialRetry.state,'waiting');
 const b=refinedThenExpire(r);assert.equal(r.initialRenders,1);assert.equal(r.rt().state.visibleSource,'awaiting-terrain');assert.equal(r.fallbacks,b.fallbacks+1);
});

test('R41-CAL-LIGHT: moonlight eligibility follows the presented surface only (R0033 M4), never granted or withdrawn by the fallback itself',()=>{
 // Available case: the V5 tier is a presented physical surface, so the one presence predicate is true; physical light
 // then follows the existing native rules (R0022 below-horizon / near-new / daylight reasons still zero it).
 const a=rig({initial:true});refinedThenExpire(a,{up:0});assert.equal(a.rt().presentable,true);
 assert.equal(a.rt().presentable,a.rt().observe().wouldPresent,'one predicate (R0036 observation agrees)');
 // Unavailable case: nothing is presented, so light is withdrawn with the surface (surface-unavailable), exactly as R0033.
 const n=rig({initial:false});refinedThenExpire(n);assert.equal(n.rt().presentable,false);assert.equal(n.rt().observe().current,false);
});

test('R41-CAL-HANDOFF: the later refined result replaces the V5 tier without any withdrawal (blank-free swap)',()=>{
 const r=rig({initial:true});const order=[];const dc=r.detail.clear.bind(r.detail),da=r.detail.adopt.bind(r.detail);
 r.detail.clear=()=>{order.push('clear');dc();};r.detail.adopt=x=>{order.push('adopt');return da(x);};
 refinedThenExpire(r);assert.equal(r.rt().state.visibleSource,'initial-v5');order.length=0;
 r.rt().request();const job=r.lastRender();r.workers.at(-1).emit(result(r));
 assert.equal(r.rt().state.visibleSource,'refined-terrain');assert.deepEqual(order,['adopt'],'adopted in place, never cleared first');
 assert.ok(job,'the successor job existed');
});

test('R41-CAL-R33: the DG-1=B construction-failure state is exactly as R0033 certified, and it has no presenter at all',()=>{
 const {wrapper,tail}=generated(),r=realm();r.c.setInterval=()=>{throw Error('controlled interval failure');};
 assert.throws(()=>r.run(wrapper),/controlled interval failure/);
 assert.equal(r.w.SalahMoonRuntime??null,null,'no runtime: no expiry route can exist');
 assert.equal(r.w.SalahMoonDetail??null,null,'no presenter handle: no host can compose a Moon, calendar or otherwise');
 assert.match(r.w.SalahMoonConstructionError,/controlled interval failure/);assert.doesNotThrow(()=>r.run(tail));
 const healthy=realm();healthy.run(wrapper);assert.equal(typeof healthy.w.SalahMoonDetail?.compose,'function');
 assert.ok(healthy.w.SalahMoonRuntime,'a registered runtime is NOT construction failure, even with no receiver');
});
