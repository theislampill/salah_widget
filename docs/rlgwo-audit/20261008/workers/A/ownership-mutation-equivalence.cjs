'use strict';
// Original behavioral ownership oracle, with only isolated source substitutions.
// Inert legacy mutations are reported as contained, never as killed mutations.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),vm=require('node:vm');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const ROOT='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const {source,copy,record,harness,cfg,req,settle}=require(path.join(ROOT,'tests/r0003-harness.cjs'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex'),raw=source();
assert.equal(hash(raw),'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee');
function edit(before,after){assert.equal(raw.split(before).length,2,'One exact current anchor');return raw.replace(before,after);}
const prayerVariants=[['original',raw],
 ['legacy-prayer-global-key',edit('saveCache(current,today,op?op.cacheKey:cacheKey());','saveCache(current,today,cacheKey());')],
 ['remove-first-loader-zone-guard',edit('if(!prayerResultEligible(op)) return;\n    tz=data.meta.timezone;', '// Isolated single guard removal\n    tz=data.meta.timezone;')]];
async function prayerRace(name,mutant){
 const h=harness({source:mutant,epoch:'2026-09-07T16:00:00Z'});h.run('var auditKeyWrites=[];var auditOriginalSave=saveCache;saveCache=function(day,data,key){auditKeyWrites.push({key,captured:_requestSlots.current&&_requestSlots.current.cacheKey,current:cacheKey(),generation:_runtimeGeneration});return auditOriginalSave(day,data,key);};');
 const A=cfg(24.47,'Madinah',{lon:39.61,method:'4'}),B=cfg(40.71,'New York',{lon:-74.01});
 const dataA=record(undefined,'Asia/Riyadh','A-old'),dataB=record(undefined,'America/New_York','B-current');
 Object.assign(dataA.timings,{Fajr:'04:46',Asr:'15:49',Isha:'19:30'});Object.assign(dataB.timings,{Fajr:'05:00',Asr:'15:30',Isha:'19:30'});
 const a=h.apply(A),old=req(h,undefined,24.47),b=h.apply(B),winner=req(h,undefined,40.71);winner.ok(dataB);await settle();await b;
 const observe=()=>({state:h.state(),cache:[...h.storage],writes:copy(h.writes),errors:copy(h.errors),keyWrites:copy(h.run('auditKeyWrites'))});
 const before=observe();assert.equal(h.run('model().nextTime'),'15:30');assert.equal(before.keyWrites.length,1);assert.equal(before.keyWrites[0].captured,before.keyWrites[0].current);assert.equal(before.keyWrites[0].key,before.keyWrites[0].captured);
 old.ok(dataA);await settle();await a;assert.deepEqual(observe(),before,'No old zone/cache/state/error mutation');
 assert.equal(h.state().tz,'America/New_York');assert.equal(h.run('_requestSlots.current'),null);
 return {variant:name,sourceSha256:hash(mutant),expected:'B succeeds through actual apply/load/adoption/render; late A changes no zone/state/cache/error/slot',observed:{winner:'B-current',zone:h.state().tz,asr:h.run('model().nextTime'),acceptedKeyWrites:before.keyWrites,lateChanges:false},disposition:name==='original'?'positive original behavioral oracle passed':'Single legacy mutation inert under independent unchanged transport/adoption ownership fences; not a killed-mutation claim'};
}
async function weatherRace(){
 const mutant=edit('localStorage.setItem(captured.cacheKey,JSON.stringify({w:current,ts:ctx.retrievedAt}));','localStorage.setItem(wxKey(),JSON.stringify({w:current,ts:ctx.retrievedAt}));');
 const previous=process.env.SALAH_WEATHER_SOURCE,local=path.join(__dirname,'ownership-weather-key-mutant.html');fs.writeFileSync(local,mutant);process.env.SALAH_WEATHER_SOURCE=local;
 const p=path.join(ROOT,'tests/r000c-weather.test.cjs'),text=fs.readFileSync(p,'utf8'),end=text.indexOf("test('control: actual fresh acquisition");assert(end>0);
 const m=new Module(p,module);m.filename=p;m.paths=Module._nodeModulePaths(path.dirname(p));m._compile(text.slice(0,end)+'\nmodule.exports={fixture,healthy,NOW};',p);
 if(previous===undefined)delete process.env.SALAH_WEATHER_SOURCE;else process.env.SALAH_WEATHER_SOURCE=previous;
 let releaseA,releaseB,n=0;const f=m.exports.fixture({fetch:()=>new Promise(resolve=>{if(n++===0)releaseA=resolve;else releaseB=resolve;})});
 vm.runInContext('var auditKeyWrites=[];var auditOriginalSet=localStorage.setItem;localStorage.setItem=function(key,value){auditKeyWrites.push({key,captured:_requestSlots.weather&&_requestSlots.weather.weatherCacheKey,current:wxKey(),generation:_runtimeGeneration});return auditOriginalSet(key,value);};',f.context);
 const a=f.fetchWeather();await settle();
 // Exactly the authoritative source sequence: invalidate generation first,
 // then bind the new fields/reset throttle, then dispatch its current work.
 f.beginRuntimeGeneration();f.set({lat:51.48,lon:-0.001,units:'f',zone:'UTC',lastWxTry:0,lastWxAt:0});const b=f.fetchWeather();await settle();assert.equal(n,2);
 const payload=m.exports.healthy({temperature_2m:68});
 releaseB({ok:true,status:200,json:async()=>payload});await b;
 const before={state:copy(f.read()),cache:[...f.storage],keyWrites:copy(vm.runInContext('auditKeyWrites',f.context))};assert.equal(before.state.weather.temp,68);assert.equal(before.state.weather.units,'f');assert.equal(before.keyWrites.length,1);assert.equal(before.keyWrites[0].captured,before.keyWrites[0].current);assert.equal(before.keyWrites[0].key,'salahwx:51.48|-0.001|f');
 releaseA({ok:true,status:200,json:async()=>m.exports.healthy()});await a;
 assert.deepEqual({state:copy(f.read()),cache:[...f.storage],keyWrites:copy(vm.runInContext('auditKeyWrites',f.context))},before);
 return {variant:'legacy-weather-global-key',sourceSha256:hash(mutant),expected:'Legitimate generation replacement permits London/Fahrenheit; stale Madinah/Celsius cannot commit or persist',observed:{temperature:68,units:'f',acceptedKeyWrites:before.keyWrites,lateChanges:false},disposition:'Single legacy mutation inert under unchanged request/attempt ownership before persistence; recording weather boundary uses the exact production generation/reset sequence, not an unfenced direct global edit. Actual settings browser proof remains absent.'};
}
(async()=>{
 const receipts=[];for(const [name,mutant]of prayerVariants)receipts.push(await prayerRace(name,mutant));receipts.push(await weatherRace());
 const result={schema:'request-mutation-equivalence/1',status:'PASS FOR SCOPED ORIGINAL OWNERSHIP ORACLES; LEGACY MUTANTS CONTAINED',targetCommit:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',sourceSha256:hash(raw),fixtureSha256:hash(fs.readFileSync(__filename)),environment:{node:process.version,platform:process.platform,arch:process.arch},preciseInvariant:'Production key components lat/lon/_cacheTz/method/school/units are assigned before acquisition at initialization, before acquisition after guarded coarseDetect, or by applyConfig only after beginRuntimeGeneration invalidates prior slots. Eligible old-generation continuations cannot reach persistence. Same-generation accepted prayer timezone discovery mutates tz but not frozen _cacheTz; it cannot change either key. Therefore current global key and captured key agree at reachable accepted commits, while old-generation commits are rejected before key selection.',replacementDiscriminators:'Actual applyConfig deferred A→B, B succeeds then old A, exact winning timezone/Asr/cache/error and slot identity; existing independently executed method/school/ABA/finally/abort tests; weather actual request/body/attempt consumers with production generation/reset order. The invariant is bounded to current product callers, not arbitrary script writes to private globals.',sourceRanges:[{path:'src/native/index.html',start:673,end:698},{path:'src/native/index.html',start:999,end:1058},{path:'src/native/index.html',start:1060,end:1095},{path:'src/native/index.html',start:1128,end:1154},{path:'src/native/index.html',start:1355,end:1385},{path:'src/native/index.html',start:3251,end:3288},{path:'src/native/index.html',start:3310,end:3327},{path:'src/native/index.html',start:3355,end:3367}],receipts,limitations:['No actual browser, pixels or live provider claim','No false negative-control kill claim; these original single-guard mutants are contained by later architecture','Arbitrary direct global edits without the accepted configuration fence would violate the product interface and are not manufactured as a defect']};
 fs.writeFileSync(path.join(__dirname,'ownership-mutation-equivalence.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,receipts:receipts.length,sourceSha256:result.sourceSha256}));
})().catch(e=>{console.error(e);process.exitCode=1;});
