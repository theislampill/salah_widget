// R0027 exact-number oracle. The candidate graph uses the generated (transformed)
// real-sky/core/src/spectral.mjs; the oracle graph is the same generated tree with that one
// file served from the digest-pinned UNMODIFIED vendor bytes (fixture load hook). Same engine,
// same process. Every comparison is bit-exact (Float64 bytes / Object.is), never a tolerance.
// Cases are classified by the observed inner-map transitions: COLD (miss, fit inserted),
// HIT (no fit), EVICTED+RECOMPUTED (key was evicted, fit inserted again).
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {CAPACITY,probe,load,freshTag,spectralInstance,series,viaInner,bytes,assertSameSpectrum,sameOutput,orlando,SCENES,ROOT} from './spectral-fit-cache-fixture.mjs';

function* xorshift(seed){let x=seed>>>0;for(;;){x^=x<<13;x>>>=0;x^=x>>>17;x^=x<<5;x>>>=0;yield x/4294967296;}}

async function domain(){
 const sky=await load(freshTag('oracle'),'real-sky/core/src/sky-background.mjs'),out=new Set();
 const ulp=x=>{const b=new Float64Array([x]),i=new BigInt64Array(b.buffer);const up=new BigInt64Array([i[0]+(x>=0?1n:-1n)]),dn=new BigInt64Array([i[0]+(x>=0?-1n:1n)]);return [new Float64Array(up.buffer)[0],new Float64Array(dn.buffer)[0]];};
 for(const e of [-0.4,-0.3,-0.2737,-0.2736126163102475,-0.2736,-0.2735,-0.27,-0.1,1e-300,0.3,0.65,1,1.5,1.99,2]){out.add(e);for(const n of ulp(e))out.add(n);}
 const r=xorshift(0x52002700);for(let i=0;i<2000;i++)out.add(-0.4+2.4*r.next().value);
 // Actual caller domains: physical twilight B-V and the preview reference B-V.
 for(let i=0;i<=1200;i++){const bv=sky.patatTwilight(-15+i*0.01).bv;if(bv!=null)out.add(bv);}
 for(let i=0;i<=1000;i++){const f=sky.patatTwilight(-15+i*0.01);out.add(f.totalBMag-f.totalVMag);}
 return [...out];
}

test('ES27-03 cold / hit / evicted / recomputed selectSpectrum, passband and XYZ are bit-identical to the vendor oracle across >= 3x capacity keys',async t=>{
 const c=await spectralInstance('cand'),o=await spectralInstance('oracle'),D=await domain(),oracle=new Map();
 const expect=bv=>{let e=oracle.get(bv);if(!e){const v=o.spectral.selectSpectrum(viaInner(bv));e=[v,o.spectral.spectrumToXYZ(v.samples),o.spectral.gamutMapXYZ(o.spectral.spectrumToXYZ(v.samples)),v.colourFallback?null:[o.spectral.passbandIntegral(v.samples,'B'),o.spectral.passbandIntegral(v.samples,'V'),o.spectral.syntheticBV(v.samples)]];oracle.set(bv,e);}return e;};
 const counts={cold:0,hit:0,recomputed:0,fallback:0,compared:0},evictedOnce=new Set();
 const check=(bv,phase)=>{
  const was=c.inner.has(bv),evicted=evictedOnce.has(bv),s0=probe.stats(c.inner).sets,v=c.spectral.selectSpectrum(viaInner(bv)),fitted=probe.stats(c.inner).sets-s0;
  const [ev,exyz,ergb,epass]=expect(bv);
  assertSameSpectrum(assert,v,ev,phase+' bv '+bv);
  const xyz=c.spectral.spectrumToXYZ(v.samples);assert.ok(bytes(xyz).equals(bytes(exyz)),'XYZ '+bv);
  assert.ok(bytes(c.spectral.gamutMapXYZ(xyz)).equals(bytes(ergb)),'RGB '+bv);
  if(epass)assert.ok(bytes([c.spectral.passbandIntegral(v.samples,'B'),c.spectral.passbandIntegral(v.samples,'V'),c.spectral.syntheticBV(v.samples)]).equals(bytes(epass)),'passbands '+bv);
  counts.compared++;
  if(v.colourFallback){assert.equal(fitted,0,'fallback inserts nothing');counts.fallback++;}
  else if(was){assert.equal(fitted,0,'hit does not refit');counts.hit++;}
  else if(evicted){assert.equal(fitted,1);counts.recomputed++;}
  else{assert.equal(fitted,1);counts.cold++;}
 };
 // Every key leaving the map is recorded as evicted (observed, not assumed).
 const track=()=>{const before=new Set(c.inner.keys());return ()=>{for(const k of before)if(!c.inner.has(k))evictedOnce.add(k);};};
 let done=track();for(const bv of D)check(bv,'cold');done();
 for(const bv of D)check(bv,'hit');
 done=track();for(const bv of series(0,CAPACITY))check(bv,'flood S1');done();
 done=track();for(const bv of D)check(bv,'recomputed');done();
 done=track();for(const bv of series(1,CAPACITY))check(bv,'flood S2');done();
 done=track();for(const bv of series(0,CAPACITY))check(bv,'S1 recomputed');done();
 done=track();for(const bv of series(2,CAPACITY))check(bv,'flood S3');done();
 for(const bv of D.slice(0,200))check(bv,'tail');
 const s=probe.stats(c.inner),distinct=new Set([...D,...series(0,CAPACITY),...series(1,CAPACITY),...series(2,CAPACITY)]).size;
 t.diagnostic(`distinctKeys=${distinct} comparisons=${counts.compared} cold=${counts.cold} hit=${counts.hit} recomputed=${counts.recomputed} fallback=${counts.fallback} fits=${s.sets} evictions=${s.deletes} retained=${c.inner.size}`);
 assert.ok(distinct>=3*CAPACITY,'at least 3x capacity distinct keys');
 assert.ok(counts.cold>0&&counts.hit>0&&counts.recomputed>=CAPACITY,'every case class exercised');
 assert.ok(c.inner.size<=CAPACITY);
});

test('ES27-03 catalogue star colours (spectralStarFlux over all records) are bit-identical to the vendor oracle',async t=>{
 const c=await spectralInstance('cand'),o=await spectralInstance('oracle');
 const stars=JSON.parse(fs.readFileSync(new URL('vendor/real-sky/data/bright-stars.json',ROOT),'utf8')).stars;let n=0;
 for(const pass of ['cold','hit'])for(const s of stars){if(s.vmag==null)continue;
  let a,b,ea,eb;try{a=c.spectral.spectralStarFlux(s,40,{});}catch(e){ea=e;}try{b=o.spectral.spectralStarFlux(s,40,{});}catch(e){eb=e;}
  if(eb){assert.equal(ea?.message,eb.message);continue;}sameOutput(assert,a,b,pass+' star '+s.id);n++;}
 t.diagnostic(`starComparisons=${n} candidateInner=${c.inner.size} oracleInner=${o.inner.size}`);
});

test('ES27-06/14 actual callers (createSkyModel, first-paint preview, refined renderPhysicalSky) cold / hit / recomputed are bit-identical to the oracle graph',async t=>{
 const ct=freshTag('cand'),ot=freshTag('oracle');
 const cand={preview:await load(ct,'real-sky/native-preview.mjs'),contract:await load(ct,'real-sky/native-contract.mjs'),physical:await load(ct,'real-sky/core/src/physical-sky-renderer.mjs'),sky:await load(ct,'real-sky/core/src/sky-background.mjs'),spectral:await load(ct,'real-sky/core/src/spectral.mjs')};
 const orac={preview:await load(ot,'real-sky/native-preview.mjs'),contract:await load(ot,'real-sky/native-contract.mjs'),physical:await load(ot,'real-sky/core/src/physical-sky-renderer.mjs'),sky:await load(ot,'real-sky/core/src/sky-background.mjs')};
 const mark=probe.mark();
 // Saturate the candidate outer selection cache first, so caller keys are not held there and
 // a later request must go through the inner fit cache (the only way to recompute).
 for(const bv of series(3,CAPACITY))cand.spectral.selectSpectrum({bv});
 const [inner]=probe.since(mark,'inner');
 const run=(m,utc)=>{const s=orlando(utc),j=m.contract.nativeJob(s,true);
  const raw=m.physical.renderPhysicalSky([],{...j.options,view:{...j.options.view,width:65,height:106},observer:j.observer,diffuse:null});
  const sky=m.sky.createSkyModel(raw.physicalState,j.options.atmosphere,{residualNight:j.options.diffuse.residualNight});
  const dirs=[{altDeg:90,azDeg:0},{altDeg:5,azDeg:265},{altDeg:20,azDeg:90},{altDeg:45,azDeg:180}];
  return {preview:m.preview.renderNativeBackgroundPreview(s),refined:raw,samples:dirs.map(d=>sky.sample(d))};};
 let bytesCompared=0;const kinds={cold:0,hit:0,recomputed:0};
 for(const utc of SCENES){
  const expected=run(orac,utc);
  const s0=probe.stats(inner).sets,cold=run(cand,utc),f0=probe.stats(inner).sets-s0;
  const s1=probe.stats(inner).sets,hit=run(cand,utc),f1=probe.stats(inner).sets-s1;
  for(const bv of series(4,CAPACITY))cand.spectral.selectSpectrum({bv:bv+SCENES.indexOf(utc)*1e-7,spectralType:'r0027-flood'});// distinct per scene, inside the fit domain
  const s2=probe.stats(inner).sets,again=run(cand,utc),f2=probe.stats(inner).sets-s2;
  assert.equal(f1,0,utc+': second run is all hits');assert.equal(f2,f0,utc+': flooded run refits exactly what the cold run fitted');
  if(f0>0){kinds.cold++;kinds.recomputed++;}kinds.hit++;
  for(const [name,actual] of [['cold',cold],['hit',hit],['recomputed',again]])bytesCompared+=sameOutput(assert,actual,expected,utc+' '+name).n;
 }
 t.diagnostic(`scenes=${SCENES.length} twilightScenesWithFits=${kinds.cold} bytesCompared=${bytesCompared} retainedInner=${inner.size}`);
 assert.ok(kinds.cold>=3,'at least three scenes exercise fitted twilight colours');
 assert.ok(inner.size<=CAPACITY);
});
