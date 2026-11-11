// R0027 (issue #69) source-state contract for the inner exact-B-V fit cache of the GENERATED
// core module real-sky/core/src/spectral.mjs and its actual twilight callers.
// Observation is external (Map.prototype instrumentation in the fixture); no export is added.
// Each scenario owns a fresh module realm, like one generated bundle instance.
import test from 'node:test';
import assert from 'node:assert/strict';
import {CAPACITY,probe,load,freshTag,spectralInstance,series,bvAt,viaInner,bytes,assertSameSpectrum,
 boundary,fifo,outerUnchanged,callerRetained} from './spectral-fit-cache-fixture.mjs';

test('ES27-01 capacity-1 / capacity / capacity+1 / +2: inner fit retention never exceeds 12,000',async()=>{await boundary(assert);});

test('ES27-01/03 FIFO: hit neither refits nor reorders; oldest evicted first; evicted key refits bit-identically',async()=>{await fifo(assert);});

test('ES27-02 outer selection cache keeps its unchanged admission bound, reported separately',async t=>{
 const c=await outerUnchanged(assert);
 t.diagnostic(`outer=${c.outer.size} inner=${c.inner.size} innerSets=${probe.stats(c.inner).sets} innerDeletes=${probe.stats(c.inner).deletes}`);
});

test('ES27-04 caller-held returned samples stay frozen and bit-identical after their fit is evicted',async()=>{
 const {held}=await callerRetained(assert),o=await spectralInstance('oracle');
 for(const [v,,bv] of held)assertSameSpectrum(assert,v,o.spectral.selectSpectrum(viaInner(bv)),'held bv '+bv);
});

test('ES27-05 invalid / out-of-fit / fallback inputs at capacity: unchanged results, no insertion, no eviction',async()=>{
 const c=await spectralInstance('cand'),o=await spectralInstance('oracle');
 for(const bv of series(4,CAPACITY-1))c.spectral.selectSpectrum({bv});
 assert.equal(c.inner.size,CAPACITY);
 const before={...probe.stats(c.inner)},order=[...c.inner.keys()];
 const inputs=[{bv:-0.4},{bv:-0.3},{bv:-0.27362},{bv:2.0000001},{bv:2.5},{bv:-0.5},{bv:null},{},{bv:5},
  {bv:NaN},{bv:'0.3'},{bv:-0.6},{bv:Infinity},{bv:5.1}];
 for(const input of inputs){
  let a,b,ea,eb;try{a=c.spectral.selectSpectrum({...input,spectralType:'r0027-fallback'});}catch(e){ea=e;}
  try{b=o.spectral.selectSpectrum({...input,spectralType:'r0027-fallback'});}catch(e){eb=e;}
  if(eb){assert.ok(ea,'candidate must throw like the oracle for '+JSON.stringify(input));assert.equal(ea.constructor.name,eb.constructor.name);assert.equal(ea.message,eb.message);}
  else{assert.ok(!ea,String(ea));assertSameSpectrum(assert,a,b,JSON.stringify(input));}
 }
 const after=probe.stats(c.inner);
 assert.equal(after.sets,before.sets,'no fit inserted by invalid/out-of-fit/fallback inputs');
 assert.equal(after.deletes,before.deletes,'no eviction caused by a failed or fallback computation');
 assert.deepEqual([...c.inner.keys()],order);
});

test('ES27-07 exact keys: 1-ulp neighbours are distinct entries; +0/-0 share the Map key exactly as before',async()=>{
 const c=await spectralInstance('cand'),o=await spectralInstance('oracle'),x=0.65,y=x+2**-53*2;// next double above 0.65
 assert.notEqual(x,y);
 const s0=c.inner.size;c.spectral.selectSpectrum({bv:x});c.spectral.selectSpectrum({bv:y});
 assert.equal(c.inner.size,s0+2,'1-ulp neighbours are not conflated');
 assert.ok(c.inner.has(x)&&c.inner.has(y));
 assertSameSpectrum(assert,c.spectral.selectSpectrum(viaInner(x)),o.spectral.selectSpectrum(viaInner(x)),'x');
 assertSameSpectrum(assert,c.spectral.selectSpectrum(viaInner(y)),o.spectral.selectSpectrum(viaInner(y)),'y');
 const z=c.inner.size;c.spectral.selectSpectrum({bv:0});c.spectral.selectSpectrum({bv:-0});
 assert.equal(c.inner.size,z+1,'SameValueZero: +0 and -0 are one inner key (unchanged semantics)');
 assertSameSpectrum(assert,c.spectral.selectSpectrum({bv:-0}),o.spectral.selectSpectrum({bv:-0}),'-0');
});

test('ES27-08 union of retained references: outer may still hold samples whose inner fit was evicted',async t=>{
 const c=await spectralInstance('cand'),sel=c.spectral.selectSpectrum;
 for(const bv of series(5,2*CAPACITY))sel({bv});
 assert.equal(c.inner.size,CAPACITY);assert.equal(c.outer.size,CAPACITY);
 const innerArrays=new Set([...c.inner.values()].map(f=>f.samples)),outerArrays=new Set([...c.outer.values()].map(v=>v.samples));
 const union=new Set([...innerArrays,...outerArrays]),evictedButHeld=[...c.outer.keys()].filter(k=>{const bv=Number(k.split('|')[2]);return !c.inner.has(bv);});
 assert.ok(evictedButHeld.length>0,'outer keeps selections whose inner fit was evicted');
 for(const k of evictedButHeld.slice(0,50))assert.ok(Object.isFrozen(c.outer.get(k).samples));
 assert.ok(union.size<=2*CAPACITY,'union of distinct retained sample arrays per instance <= 24,000');
 t.diagnostic(`inner=${c.inner.size} outer=${c.outer.size} distinctSampleArrays=${union.size} outerOnly=${evictedButHeld.length}`);
});

const twilightState=altDeg=>({utcMs:Date.parse('2026-10-07T23:45:00Z'),sun:{altDeg,azDeg:265},moon:{altDeg:-30,azDeg:90,phaseAngleDeg:120}});
test('ES27-06 actual physical caller: createSkyModel over continuous twilight altitudes is bounded',async t=>{
 const tag=freshTag('cand'),sky=await load(tag,'real-sky/core/src/sky-background.mjs'),sp=await load(tag,'real-sky/core/src/spectral.mjs'),mark=probe.mark();
 // Fit domain of the unchanged algorithm: [-0.4,2] intersected with [B-V(200000 K), B-V(1500 K)].
 const lo=Math.max(-.4,sp.syntheticBV(sp.blackbodyShape(200000))),hi=Math.min(2,sp.syntheticBV(sp.blackbodyShape(1500)));
 const distinct=new Set();let n=0;
 for(let i=0;i<12600;i++){const alt=-14.99+i*0.00094;sky.createSkyModel(twilightState(alt));const bv=sky.patatTwilight(alt).bv;if(bv!=null)distinct.add(bv);n++;}
 const [inner]=probe.since(mark,'inner'),[outer]=probe.since(mark,'outer'),s=probe.stats(inner);
 const fittable=[...distinct].filter(bv=>bv>=lo&&bv<=hi).length;
 t.diagnostic(`altitudes=${n} distinctTwilightBV=${distinct.size} inFitDomain=${fittable} neutralFallbacks=${distinct.size-fittable} fits=${s.sets} retainedInner=${inner.size} outer=${outer.size} evictions=${s.deletes}`);
 assert.ok(fittable>CAPACITY,'the sweep must present more than 12,000 distinct fittable twilight colours');
 assert.ok(distinct.size>fittable,'intentional out-of-fit-domain fallbacks are preserved, not tuned into fits');
 assert.equal(s.sets,fittable,'each distinct admissible twilight B-V is fitted once');
 assert.equal(inner.size,CAPACITY,'createSkyModel retention is bounded at 12,000');
 assert.equal(outer.size,CAPACITY);
});

test('ES27-06 actual preview caller: renderNativeBackgroundPreview at twilight inserts through the bounded map',async t=>{
 const tag=freshTag('cand'),preview=await load(tag,'real-sky/native-preview.mjs'),spectral=await load(tag,'real-sky/core/src/spectral.mjs'),mark=probe.mark();
 for(const bv of series(6,CAPACITY))spectral.selectSpectrum({bv});
 const [inner]=probe.since(mark,'inner'),before={...probe.stats(inner)};
 assert.equal(inner.size,CAPACITY);
 const snap=m=>({utcMs:Date.parse('2026-10-07T23:20:00Z')+m*60000,lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'r0027-twilight',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:60,code:2,temp:72},units:'f',lp:0,timeScale:60});
 let twilight=0;
 for(let m=0;m<60;m+=2){const p=preview.renderNativeBackgroundPreview(snap(m));if(p.raster.twilightDisplay)twilight++;}
 const after=probe.stats(inner);
 t.diagnostic(`previews=30 withTwilightDisplay=${twilight} newFits=${after.sets-before.sets} evictions=${after.deletes-before.deletes} retained=${inner.size}`);
 assert.ok(after.sets-before.sets>=30,'preview twilight colours were fitted in this realm');
 assert.equal(after.deletes-before.deletes,after.sets-before.sets,'every preview insertion at capacity evicted exactly one oldest fit');
 assert.equal(inner.size,CAPACITY);
});
