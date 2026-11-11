// R0027 mutation controls. Each in-memory mutant of the GENERATED spectral module (never
// written to disk) is loaded as a fresh realm and must fail an actual assertion of the named
// discriminator. Retention mutants that keep every number right are killed by the state
// discriminators while the oracle stays green; numeric mutants that keep every count right
// are killed by the oracle while the state discriminator stays green. Ordinary standard /
// provided / template / fallback positives stay valid in every mutant.
import test from 'node:test';
import assert from 'node:assert/strict';
import {read,SPECTRAL_REL,registerMutant,spectralInstance,assertSameSpectrum,boundary,fifo,outerUnchanged,callerRetained,smallOracle} from './spectral-fit-cache-fixture.mjs';

const source=read(SPECTRAL_REL).toString('utf8');
const EVICT='if(sfFitCache.size>=sfFitCacheLimit)sfFitCache.delete(sfFitCache.keys().next().value);';
async function positives(assert,prefix){
 const c=await spectralInstance(prefix),o=await spectralInstance('oracle');
 const sed={source:'r0027 provided',samples:Array.from({length:95},(_,i)=>1+i/95)};
 for(const star of [{hip:91262},{hip:49669,bv:-0.087},{spectralType:'A0V',bv:0.02},{spectralType:'B7V',bv:-0.05},{sed},{},{bv:null},{bv:3}])
  assertSameSpectrum(assert,c.spectral.selectSpectrum(star),o.spectral.selectSpectrum(star),JSON.stringify(star).slice(0,60));
}
const cases=[
 // [name, from, to, killing discriminator, discriminator that must stay green]
 ['m1 no eviction (numbers right, entries leak)',EVICT,'',boundary,smallOracle],
 ['m2a capacity 11,999','sfFitCacheLimit=12000','sfFitCacheLimit=11999',boundary,smallOracle],
 ['m2b capacity 12,001','sfFitCacheLimit=12000','sfFitCacheLimit=12001',boundary,smallOracle],
 ['m2c comparison off by one (> for >=)','sfFitCache.size>=sfFitCacheLimit','sfFitCache.size>sfFitCacheLimit',boundary,smallOracle],
 ['omit capacity guard (evict unconditionally)','if(sfFitCache.size>=sfFitCacheLimit)sfFitCache.delete','sfFitCache.delete',boundary,smallOracle],
 ['m3 LRU instead of FIFO','if(sfFitCache.has(bv))return sfFitCache.get(bv);','if(sfFitCache.has(bv)){const f=sfFitCache.get(bv);sfFitCache.delete(bv);sfFitCache.set(bv,f);return f;}',fifo,smallOracle],
 ['m4 evicts the newest','sfFitCache.delete(sfFitCache.keys().next().value)','sfFitCache.delete([...sfFitCache.keys()].pop())',fifo,smallOracle],
 ['m5 clears the whole map at capacity','sfFitCache.delete(sfFitCache.keys().next().value)','sfFitCache.clear()',boundary,smallOracle],
 ['m6 bounds the outer map too','if(sfCache.size<12000)sfCache.set(key,value);','if(sfCache.size>=12000)sfCache.delete(sfCache.keys().next().value);sfCache.set(key,value);',outerUnchanged,smallOracle],
 ['m9a fit iterations 48 -> 47 (counts right, numbers wrong)','for(let i=0;i<48;i++)','for(let i=0;i<47;i++)',smallOracle,boundary],
 ['m9b reordered temperature arithmetic','const T=Math.sqrt(lo*hi),fit=','const T=Math.exp((Math.log(lo)+Math.log(hi))/2),fit=',smallOracle,boundary],
 ['round B-V key','function sfFitColour(bv){','function sfFitColour(bv){bv=Math.round(bv*1e4)/1e4;',smallOracle,null],
 ['m11 mutate shared returned samples on eviction','Object.freeze(value.samples);Object.freeze(value);','Object.freeze(value);',callerRetained,null,
  [[EVICT,'if(sfFitCache.size>=sfFitCacheLimit){const k=sfFitCache.keys().next().value;sfFitCache.get(k).samples.fill(0);sfFitCache.delete(k);}']]],
];

test('healthy generated module passes every discriminator',async()=>{
 for(const d of [boundary,fifo,outerUnchanged,callerRetained,smallOracle,positives])await d(assert,'cand');
});

for(const [name,from,to,kill,green,extra=[]] of cases)test('R0027 mutation discriminator: '+name,async t=>{
 let mutated=source;
 for(const [a,b] of [[from,to],...extra]){assert.equal(mutated.split(a).length,2,'one declared mutation location: '+a);mutated=mutated.replace(a,b);}
 const key=name.split(' ')[0]+'-'+cases.findIndex(c=>c[0]===name);registerMutant(key,mutated);
 await assert.rejects(()=>kill(assert,'mut:'+key),e=>{t.diagnostic('killed by '+kill.name+': '+String(e.message).split('\n')[0].slice(0,160));return e instanceof assert.AssertionError;},'only an actual assertion failure detects the mutant');
 if(green)await green(assert,'mut:'+key);
 await positives(assert,'mut:'+key);
});
