// R0027 shared fixture: fresh module realms, read-only Map instrumentation and the
// untouched vendor oracle for the fitted-spectrum retention tests. Not a test file.
//
// * Every import made through load(tag, path) gets a fresh module graph: the resolve
//   hook propagates `?r0027=<tag>` to relative imports, so each tag owns its own
//   spectral.mjs instance (own sfCache/sfFitCache) exactly as one generated bundle does.
// * tag `oracle*`: real-sky/core/src/spectral.mjs is served from the digest-pinned,
//   UNMODIFIED vendor bytes; every other module is the same generated file. The only
//   difference between an oracle graph and a candidate graph is therefore the R0027 delta.
// * tag `mut:*`: spectral.mjs is served from an in-memory mutant (never written to disk).
// * Map.prototype.set/delete are wrapped to OBSERVE the two private maps. Nothing is
//   exported from or injected into the product; the hook only counts and forwards.
import {registerHooks} from 'node:module';
import fs from 'node:fs';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';

export const ROOT=new URL('../../',import.meta.url);
export const CAPACITY=12000;
export const VENDOR_SPECTRAL_SHA256='565517270e1cb313e72875409b93199e38237c7b74ed1b452a52ccd6b889120b';
export const SPECTRAL_REL='real-sky/core/src/spectral.mjs';
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
export const read=rel=>fs.readFileSync(new URL(rel,ROOT));
export const vendorSpectral=read('vendor/real-sky/src/spectral.mjs');
if(sha256(vendorSpectral)!==VENDOR_SPECTRAL_SHA256)throw new Error('R0027 oracle input drift: vendor spectral.mjs is not the digest-pinned scientific source');
// The rest of the oracle graph must be the same scientific bytes as vendor.
for(const p of ['astronomy.mjs','photometry.mjs','spectral-tables.mjs','sky-background.mjs','atmosphere.mjs']){
 if(sha256(read('real-sky/core/src/'+p))!==sha256(read('vendor/real-sky/src/'+p)))throw new Error('R0027 oracle dependency drift: '+p);
}

const mutants=new Map();
registerHooks({
 resolve(specifier,context,next){
  const result=next(specifier,context);
  const tag=context.parentURL?.startsWith('file:')?new URL(context.parentURL).searchParams.get('r0027'):null;
  if(tag&&specifier.startsWith('.')&&result.url.startsWith('file:')){const u=new URL(result.url);u.search='?r0027='+encodeURIComponent(tag);return {...result,url:u.href,shortCircuit:true};}
  return result;
 },
 load(url,context,next){
  if(url.startsWith('file:')){
   const u=new URL(url),tag=u.searchParams.get('r0027');
   if(tag&&fileURLToPath(u).replace(/\\/g,'/').endsWith('/'+SPECTRAL_REL)){
    if(tag.startsWith('oracle'))return {format:'module',source:vendorSpectral,shortCircuit:true};
    if(tag.startsWith('mut:')){const name=tag.slice(4).replace(/#.*$/,'');if(!mutants.has(name))throw new Error('unregistered mutant '+name);return {format:'module',source:mutants.get(name),shortCircuit:true};}
   }
  }
  return next(url,context);
 },
});
export function registerMutant(name,source){mutants.set(name,source);}

// ---- read-only Map observation ------------------------------------------------
const realSet=Map.prototype.set,realDelete=Map.prototype.delete,info=new WeakMap(),observed=[];
const isFit=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===2&&'samples' in v&&'temperatureProxyK' in v;
const isSelection=v=>v!==null&&typeof v==='object'&&'kind' in v&&'samples' in v&&'colourFallback' in v;
Map.prototype.set=function(key,value){
 let s=info.get(this);
 if(!s){const role=typeof key==='number'&&isFit(value)?'inner':typeof key==='string'&&isSelection(value)?'outer':null;
  if(role){s={role,sets:0,deletes:0,seq:observed.length};info.set(this,s);observed.push(this);}}
 if(s)s.sets++;
 return realSet.call(this,key,value);
};
Map.prototype.delete=function(key){const s=info.get(this),r=realDelete.call(this,key);if(s&&r)s.deletes++;return r;};
export const probe={
 mark:()=>observed.length,
 since(mark,role){return observed.slice(mark).filter(m=>info.get(m).role===role);},
 stats:m=>({...info.get(m),size:m.size}),
};

let instance=0;
export async function load(tag,rel){return import(new URL(rel,ROOT).href+'?r0027='+encodeURIComponent(tag));}
export const freshTag=prefix=>prefix+'#'+(++instance);

// ---- deterministic inputs -------------------------------------------------------
// 8 disjoint interleaved series of exact doubles inside the fit domain (-0.2736.., 2].
const LO=-0.27,SPAN=2.27,SLOTS=8,PER=40000;
export const bvAt=(slot,i)=>LO+(i*SLOTS+slot+.5)*(SPAN/(SLOTS*PER));
export function* series(slot,n,start=0){for(let i=start;i<start+n;i++)yield bvAt(slot,i);}
// A distinct outer key for the same exact B-V forces the inner fit cache to be consulted
// even when the outer selection cache already holds (or refused) the plain key.
let probeKey=0;export const viaInner=bv=>({bv,spectralType:'r0027-probe-'+(++probeKey)});

export const bytes=a=>Buffer.from(Float64Array.from(a).buffer);
export function assertSameSpectrum(assert,actual,expected,label){
 assert.ok(bytes(actual.samples).equals(bytes(expected.samples)),label+': samples differ bit-for-bit');
 assert.ok(Object.is(actual.temperatureProxyK,expected.temperatureProxyK),label+': temperatureProxyK '+actual.temperatureProxyK+' vs '+expected.temperatureProxyK);
 const meta=v=>{const o={...v};delete o.samples;return o;};
 assert.deepEqual(meta(actual),meta(expected),label+': selection metadata');
}

// One fresh spectral instance with its inner/outer maps located through the observer.
export async function spectralInstance(prefix='cand',rel=SPECTRAL_REL){
 const tag=freshTag(prefix),mod=await load(tag,rel);
 const spectral=rel===SPECTRAL_REL?mod:await load(tag,SPECTRAL_REL);
 const mark=probe.mark();spectral.selectSpectrum({bv:bvAt(7,PER-1)});// one sentinel fit locates the maps
 const inner=probe.since(mark,'inner'),outer=probe.since(mark,'outer');
 if(inner.length!==1||outer.length!==1)throw new Error('could not attribute exactly one inner/outer map to '+tag);
 return {tag,mod,spectral,inner:inner[0],outer:outer[0],sentinel:bvAt(7,PER-1)};
}

// ---- discriminators shared by the state and mutation tests ------------------------
// Capacity boundaries: capacity-1, capacity, capacity+1 and +2 distinct exact keys.
export async function boundary(assert,prefix='cand'){
 const c=await spectralInstance(prefix),sel=c.spectral.selectSpectrum;
 let n=1;for(const bv of series(0,CAPACITY-2)){sel({bv});n++;}
 assert.equal(c.inner.size,CAPACITY-1,'capacity-1 distinct fits are all retained');
 assert.equal(probe.stats(c.inner).deletes,0,'no eviction below capacity');
 sel({bv:bvAt(0,CAPACITY-2)});n++;
 assert.equal(c.inner.size,CAPACITY,'exactly capacity distinct fits retained at capacity');
 assert.equal(probe.stats(c.inner).deletes,0,'no eviction when reaching capacity');
 const first=c.inner.keys().next().value;assert.ok(Object.is(first,c.sentinel),'oldest key is the first inserted');
 sel({bv:bvAt(0,CAPACITY-1)});n++;
 assert.equal(c.inner.size,CAPACITY,'capacity+1: retained count stays at capacity');
 assert.equal(probe.stats(c.inner).deletes,1,'capacity+1: exactly one eviction');
 assert.ok(!c.inner.has(c.sentinel),'capacity+1: the oldest key was evicted');
 sel({bv:bvAt(0,CAPACITY)});n++;
 assert.equal(c.inner.size,CAPACITY,'capacity+2: retained count stays at capacity');
 assert.equal(probe.stats(c.inner).sets,n,'every distinct key was fitted exactly once');
 assert.ok(!c.inner.has(bvAt(0,0)),'capacity+2: the next-oldest key was evicted');
 return c;
}

// FIFO, not LRU: a hit does not reorder or refit; a re-requested evicted key is refitted
// and gives bit-identical output; eviction order is insertion order.
export async function fifo(assert,prefix='cand'){
 const c=await spectralInstance(prefix),sel=c.spectral.selectSpectrum;
 for(const bv of series(1,CAPACITY-1))sel({bv});
 assert.equal(c.inner.size,CAPACITY);
 const sets=probe.stats(c.inner).sets,order=[...c.inner.keys()],snapshot=sel(viaInner(c.sentinel));
 assert.equal(probe.stats(c.inner).sets,sets,'a hit does not refit');
 assert.deepEqual([...c.inner.keys()],order,'a hit does not reorder (FIFO, not LRU)');
 sel({bv:bvAt(1,CAPACITY-1)});
 assert.ok(!c.inner.has(c.sentinel),'the oldest inserted key is evicted even though it was just hit');
 assert.ok(c.inner.has(bvAt(1,CAPACITY-1)),'the newest key is retained');
 assert.ok(Object.is([...c.inner.keys()][0],bvAt(1,0)),'the next oldest becomes the eviction candidate');
 const before=probe.stats(c.inner).sets,again=sel(viaInner(c.sentinel));
 assert.equal(probe.stats(c.inner).sets,before+1,'an evicted key is refitted on demand');
 assert.ok(!c.inner.has(bvAt(1,0)),'refit insertion evicts the next oldest key');
 assert.equal(c.inner.size,CAPACITY);
 assertSameSpectrum(assert,again,snapshot,'refitted evicted key');
 return c;
}

// The outer selection cache keeps its own unchanged admission rule (first 12,000 keys).
export async function outerUnchanged(assert,prefix='cand',extra=50){
 const c=await spectralInstance(prefix),sel=c.spectral.selectSpectrum,keys=['||'+c.sentinel];
 for(const bv of series(2,CAPACITY+extra)){sel({bv});keys.push('||'+bv);}
 assert.equal(c.outer.size,CAPACITY,'outer bound intact at 12,000');
 assert.equal(probe.stats(c.outer).deletes,0,'outer map never evicts');
 assert.deepEqual([...c.outer.keys()],keys.slice(0,CAPACITY),'outer retains exactly the first 12,000 admitted keys');
 assert.ok(c.inner.size<=CAPACITY,'inner bound reported separately: '+c.inner.size);
 return c;
}

// Caller-held values: frozen arrays stay frozen and bit-identical after their fit is evicted.
export async function callerRetained(assert,prefix='cand'){
 const c=await spectralInstance(prefix),sel=c.spectral.selectSpectrum,held=[];
 for(const bv of series(3,64)){const v=sel(viaInner(bv));held.push([v,bytes(v.samples),bv]);}
 for(const bv of series(3,CAPACITY,64))sel({bv});
 assert.ok(!c.inner.has(bvAt(3,0)),'held fits have been evicted');
 for(const [v,b] of held){
  assert.ok(Object.isFrozen(v)&&Object.isFrozen(v.samples),'returned value and samples stay frozen');
  assert.ok(bytes(v.samples).equals(b),'caller-held samples unchanged after eviction');
 }
 return {c,held};
}

// Exact numbers against the untouched vendor module for a small, eviction-free set.
export async function smallOracle(assert,prefix='cand'){
 const c=await spectralInstance(prefix),o=await spectralInstance('oracle');
 for(const bv of [-0.2736,-0.2,0,0.3,0.65,1,1.5,2,0.3+Number.EPSILON,0.65000001])
  assertSameSpectrum(assert,c.spectral.selectSpectrum({bv}),o.spectral.selectSpectrum({bv}),'bv '+bv);
}

// ---- generated bundle access -----------------------------------------------------
export const HOOK_SOURCE=`globalThis.__r0027={inner:[],outer:[]};{const set=Map.prototype.set;
Map.prototype.set=function(k,v){if(typeof k==='number'&&v&&typeof v==='object'&&Object.keys(v).length===2&&'temperatureProxyK' in v&&!__r0027.inner.includes(this))__r0027.inner.push(this);
 if(typeof k==='string'&&v&&typeof v==='object'&&'kind' in v&&'colourFallback' in v&&!__r0027.outer.includes(this))__r0027.outer.push(this);return set.call(this,k,v);};}`;
export function workerContext(source){
 const ctx=vm.createContext({self:{postMessage(){},addEventListener(){}},performance,console});
 vm.runInContext(HOOK_SOURCE,ctx);vm.runInContext(source,ctx,{filename:'native-worker.js'});return ctx;
}
// The concatenation step of tools/build_native.py (import lines removed, `export ` dropped).
export const concatStrip=text=>text.replace(/^import .*?;\s*$/gm,'').replace(/\bexport (?=(?:const|let|function|class|async function)\b)/g,'');
// The worker bundle the untouched vendor module generates: swap exactly the one generated
// spectral segment for the vendor segment. Everything else is the same generated text.
export function vendorBundle(text){
 const cand=concatStrip(read(SPECTRAL_REL).toString('utf8')),vend=concatStrip(vendorSpectral.toString('utf8')),parts=text.split(cand);
 if(parts.length!==2)throw new Error('generated spectral segment must occur exactly once, found '+(parts.length-1));
 return parts.join(vend);
}

// Exact structural equality of two outputs: typed arrays byte-for-byte, numbers by Object.is,
// recursively. Only wall-clock timing fields are excluded (they are not computed values).
const TIMING=/^(buildMs|started|assetMs|renderMs|totalMs|timings|elapsedMs|ms)$/;
export function sameOutput(assert,a,b,path='$',budget={n:0}){
 if(ArrayBuffer.isView(a)||ArrayBuffer.isView(b)){
  assert.ok(ArrayBuffer.isView(a)&&ArrayBuffer.isView(b)&&a.constructor.name===b.constructor.name,path+': typed array kind');
  const x=Buffer.from(a.buffer,a.byteOffset,a.byteLength),y=Buffer.from(b.buffer,b.byteOffset,b.byteLength);
  assert.ok(x.equals(y),path+': '+a.constructor.name+'['+a.length+'] differs byte-for-byte');budget.n+=a.byteLength;return budget;
 }
 if(typeof a==='number'||typeof b==='number'){assert.ok(Object.is(a,b),path+': '+a+' vs '+b);budget.n+=8;return budget;}
 if(typeof a==='function'||typeof b==='function')return budget;
 if(a===null||b===null||typeof a!=='object'||typeof b!=='object'){assert.equal(a,b,path);return budget;}
 if(a instanceof Map||b instanceof Map||Object.prototype.toString.call(a)==='[object Map]'){sameOutput(assert,[...a.entries()],[...b.entries()],path+'<map>',budget);return budget;}
 const ka=Object.keys(a).filter(k=>!TIMING.test(k)),kb=Object.keys(b).filter(k=>!TIMING.test(k));
 assert.deepEqual(ka,kb,path+': keys');
 for(const k of ka)sameOutput(assert,a[k],b[k],path+'.'+k,budget);
 return budget;
}
export const orlando=(utc,timeScale=1)=>({utcMs:Date.parse(utc),lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'r0027-orlando',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:60,code:2,temp:72},units:'f',lp:0,timeScale});
// Real scenes crossing the twilight colour band (sun ~-2..-16 deg) plus day and night controls.
export const SCENES=['2026-10-07T23:25:00Z','2026-10-07T23:45:00Z','2026-10-08T00:05:00Z','2026-10-08T00:30:00Z','2026-10-07T15:09:00Z','2026-10-08T03:30:00Z'];

// A generated worker bundle executed as a classic script in the global scope of its own
// worker thread (like the browser worker realm). vm contexts are avoided: their global
// interceptors make the bundle orders of magnitude slower and lack TextEncoder/crypto.
import {Worker} from 'node:worker_threads';
const REALM=`const {parentPort,workerData}=require('node:worker_threads');const vm=require('node:vm');
const out=[];globalThis.self={postMessage:m=>out.push(m),addEventListener(){}};
const clean=x=>{if(typeof x==='function')return undefined;if(x===null||typeof x!=='object'||ArrayBuffer.isView(x))return x;
 if(x instanceof Map)return {'<map>':[...x.entries()].map(clean)};if(Array.isArray(x))return x.map(clean);
 const o={};for(const k of Object.keys(x)){const v=clean(x[k]);if(v!==undefined||x[k]===undefined)o[k]=v;}return o;};
vm.runInThisContext(workerData.hook);vm.runInThisContext(workerData.source,{filename:workerData.name});
parentPort.on('message',async m=>{try{let r;
 if(m.op==='eval')r=vm.runInThisContext(m.code);else if(m.op==='msg'){await self.onmessage({data:m.data});r=out.pop();}
 else if(m.op==='job'){await self.onmessage({data:{kind:'render',id:m.id,job:vm.runInThisContext(m.code)}});r=out.pop();}
 parentPort.postMessage({ok:true,r:clean(r)});}catch(e){parentPort.postMessage({ok:false,e:String(e&&e.stack||e)});}});`;
export function bundleRealm(source,name='native-worker.js'){
 const w=new Worker(REALM,{eval:true,workerData:{hook:HOOK_SOURCE,source,name}});
 let chain=Promise.resolve();
 const call=msg=>(chain=chain.then(()=>new Promise((res,rej)=>{w.once('message',m=>m.ok?res(m.r):rej(new Error(m.e)));w.once('error',rej);w.postMessage(msg);})));
 return {eval:code=>call({op:'eval',code}),message:data=>call({op:'msg',data}),job:(code,id)=>call({op:'job',code,id}),close:()=>w.terminate()};
}
