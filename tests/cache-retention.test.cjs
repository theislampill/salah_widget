'use strict';
// R0032 (issue 99) machine CR — per-location cache retention (ISM-CFG-002 / ISM-WX-001).
// Owner decisions: D-32-2 = B (bounded eviction of expired or unreadable entries, outside the boot-critical
// path) and D-32-3 = A (Reset does not clear these caches). Complete authored runtime (tests/r0032-fixture.cjs)
// with an enumerable storage double that records every read, enumeration and removal.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {runtime,prayerForDate,flush}=require('./r0032-fixture.cjs');
const root=path.resolve(__dirname,'..');
// Fixture wall clock: 2026-09-08T19:00Z (UTC civil day 08-09-2026; 22:00 in Asia/Riyadh).
const WALL=Date.parse('2026-09-08T19:00:00Z'),H=3600e3;
const SEL='salah:24.47|39.61|Asia/Riyadh|4|0',WSEL='salahwx:24.47|39.61|c';
const P=(day,zone='Asia/Riyadh')=>JSON.stringify({date:day,data:prayerForDate(day)});
const W=ts=>JSON.stringify({w:{temp:20},ts});
function seeded(){return [
  [SEL,P('01-09-2026')],                                      // protected: stale wrong-day record under the selected key
  [WSEL,W(WALL-7*H)],                                         // protected: expired record under the selected weather key
  ['salah:21.42|39.83|Asia/Riyadh|4|0',P('01-09-2026')],      // expired: a week old
  ['salah:21.43|39.83|Asia/Riyadh|4|0',P('05-09-2026')],      // expired: before the cut-off (UTC day − 2 = 06-09)
  ['salah:21.44|39.83|Asia/Riyadh|4|0',P('06-09-2026')],      // kept: exactly the cut-off day
  ['salah:21.45|39.83|Asia/Riyadh|4|0',P('08-09-2026')],      // kept: current day for another instance
  ['salah:21.46|39.83|Asia/Riyadh|4|0',P('10-09-2026')],      // kept: future-dated (device-clock skew is not evidence)
  ['salah:1|2|UTC|4|0','{not json'],                          // unreadable
  ['salah:1|3|UTC|4|0',JSON.stringify({date:'08-09-2026'})],  // unreadable: no admissible record
  ['salahwx:21.42|39.83|c',W(WALL-1*H)],                      // kept: inside six hours
  ['salahwx:21.43|39.83|c',W(WALL-6*H+1000)],                 // kept: one second inside the window
  ['salahwx:21.44|39.83|c',W(WALL-6*H)],                      // expired: at the six-hour bound (loadWx rejects >=)
  ['salahwx:21.45|39.83|c',W(WALL+60000)],                    // expired: future receipt
  ['salahwx:21.46|39.83|c','nope'],                           // unreadable
  ['salahwx:21.47|39.83|c',JSON.stringify({w:{}})],           // unreadable: no receipt
  // Never touched: other prefixes, config, V1 namespaces, look-alikes without the colon.
  ['salah_widget:config:v1','{"lat":1}'],['salah_widget:v1:config:v1','{"lat":2}'],
  ['salah_widget:v1:prayer:1|2','{not json'],['salah_widget:v1:weather:1|2','nope'],
  ['salahwx','nope'],['salah','nope'],['salah-other:1','nope'],['other','nope'],
];}
const EVICTED=['salah:21.42|39.83|Asia/Riyadh|4|0','salah:21.43|39.83|Asia/Riyadh|4|0','salah:1|2|UTC|4|0','salah:1|3|UTC|4|0',
  'salahwx:21.44|39.83|c','salahwx:21.45|39.83|c','salahwx:21.46|39.83|c','salahwx:21.47|39.83|c'].sort();
const held=()=>{let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};};
// Boot with every provider answer held, so the boot cache-selection phase can be observed on its own.
async function heldBoot(opts={}){
  const gates={prayer:held(),weather:held()};
  const r=runtime({storage:seeded(),...opts,route:(u)=>u.hostname==='api.aladhan.com'?gates.prayer.promise:u.hostname==='api.open-meteo.com'?gates.weather.promise:undefined});
  const done={v:false};r.run('boot()').then(()=>{done.v=true;},()=>{done.v=true;});
  for(let i=0;i<30;i++){await flush(2);r.advanceTask()||r.advanceFrame();}
  return {r,gates,done};
}
const okPrayer=day=>({ok:true,status:200,json:async()=>({code:200,status:'OK',data:prayerForDate(day)})});
const okWeather=wall=>({ok:true,status:200,json:async()=>require('./r0032-fixture.cjs').weatherBody(wall)});

test('R32-08 boot cache selection reads only the selected keys and neither enumerates nor deletes',async()=>{
  const {r}=await heldBoot();
  assert.equal(r.run('cacheKey()'),SEL);assert.equal(r.run('wxKey()'),WSEL);
  assert.deepEqual([...new Set(r.reads)].sort(),[SEL,WSEL].sort(),'boot reads');
  assert.equal(r.enumerations.count,0,'no scan on the boot path');assert.deepEqual(r.removes,[]);
});
test('R32-08 after the first fresh cache write: only expired/unreadable non-protected entries in the two namespaces are removed',async()=>{
  const {r,gates}=await heldBoot(),before=new Map(seeded());
  gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  assert.deepEqual([...r.removes].sort(),EVICTED);
  for(const [k,v] of before){
    if(EVICTED.includes(k)){assert.equal(r.storage.has(k),false,k);continue;}
    if(k===WSEL)continue;                                           // rewritten by the fresh weather write itself
    assert.equal(r.storage.get(k),v,'byte-identical: '+k);
  }
  assert.ok(JSON.parse(r.storage.get(WSEL)).ts>WALL-H,'selected weather key holds the fresh record, not removed');
  assert.equal(r.storage.get(SEL),before.get(SEL),'stale selected prayer record survives (README: it may resolve the zone)');
});
test('R32-08 the pass runs at most once per document; a later write does not scan again',async()=>{
  const {r,gates}=await heldBoot();gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  const scans=r.enumerations.count;assert.ok(scans>0);
  r.storage.set('salahwx:9|9|c',W(WALL-9*H));
  gates.prayer.resolve(okPrayer('08-09-2026'));await flush(16);
  assert.ok(r.reads.length>0);assert.equal(r.enumerations.count,scans,'no second enumeration');
  assert.equal(r.storage.has('salahwx:9|9|c'),true);
});
test('R32-08 a prayer write alone also triggers the single pass (either fresh write is the trigger)',async()=>{
  const {r,gates}=await heldBoot();gates.prayer.resolve(okPrayer('08-09-2026'));await flush(16);
  assert.deepEqual([...r.removes].sort(),EVICTED);
});
test('R32-08 concurrent writer: an entry replaced between classification and removal is kept',async()=>{
  const {r,gates}=await heldBoot(),K='salah:21.42|39.83|Asia/Riyadh|4|0',fresh=P('08-09-2026');let swapped=0;
  const get=r.ctx.localStorage.getItem;let seen=0;
  r.ctx.localStorage.getItem=k=>{if(k===K&&++seen===2){r.storage.set(K,fresh);swapped++;}return get(k);};
  gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  assert.equal(swapped,1,'the pass re-read the classified entry before removing it');
  assert.equal(r.storage.get(K),fresh);assert.equal(r.removes.includes(K),false);
});
test('R32-08 interrupted pass: a throwing removal does not stop the pass or escape; a throwing enumeration is contained',async()=>{
  const {r,gates}=await heldBoot(),rm=r.ctx.localStorage.removeItem;
  r.ctx.localStorage.removeItem=k=>{if(k==='salah:1|2|UTC|4|0')throw Error('contained quota/security error');return rm(k);};
  gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  assert.deepEqual([...r.removes].sort(),EVICTED.filter(k=>k!=='salah:1|2|UTC|4|0'));
  assert.equal(r.run('weather&&weather.temp'),24,'the write and display are unaffected');
  const b=await heldBoot();b.r.ctx.localStorage.key=()=>{throw Error('contained enumeration error');};
  b.gates.weather.resolve(okWeather(b.r.clock.wall));await flush(12);
  assert.deepEqual(b.r.removes,[]);assert.equal(b.r.run('weather&&weather.temp'),24);
});
test('R32-08 eviction never changes the current session: displayed prayer and weather state are identical with and without it',async()=>{
  const runs=[];
  for(const storage of [seeded(),seeded().filter(([k])=>!EVICTED.includes(k))]){
    const {r,gates}=await heldBoot({storage});gates.weather.resolve(okWeather(r.clock.wall));gates.prayer.resolve(okPrayer('08-09-2026'));await flush(16);
    runs.push(r.run('JSON.stringify({today:today&&today.date.gregorian.date,tz,w:weather&&weather.temp,sel:localStorage.getItem(cacheKey())})'));
  }
  assert.equal(runs[0],runs[1]);
});
test('R32-09 D-32-3 A: Reset (clearLocal) removes only salah_widget:config:v1; caches and V1 keys stay',()=>{
  const store=new Map(seeded()),before=new Map(store);
  const ctx=vm.createContext({localStorage:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k)}});
  ctx.window=ctx;vm.runInContext(fs.readFileSync(path.join(root,'src/native/config.js'),'utf8'),ctx);
  assert.equal(vm.runInContext('SalahConfig.clearLocal().ok',ctx),true);
  for(const [k,v] of before){if(k==='salah_widget:config:v1')assert.equal(store.has(k),false);else assert.equal(store.get(k),v,k);}
});

// ---- R0032 review round: key ownership, bounds and outer containment --------------------------------------------
const FOREIGN=[['salah:something-else','{not json'],['salah:1|2|UTC|4','{not json'],['salahwx:1|2|k','nope'],
  ['salah:24.47|39.61|4|0',P('01-09-2026')],['salahwx:24.47|39.61|c|extra',W(WALL-9*H)]];
test('R32-08 ownership: only keys of the exact cacheKey()/wxKey() shape are evicted; foreign or malformed keys under the prefixes survive',async()=>{
  const {r,gates}=await heldBoot({storage:[...seeded(),...FOREIGN]});
  gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  assert.deepEqual([...r.removes].sort(),EVICTED);
  for(const [k,v] of FOREIGN)assert.equal(r.storage.get(k),v,'foreign key untouched: '+k);
  const rep=r.run('qaState().cacheRetention');assert.equal(rep.removed,EVICTED.length);assert.equal(rep.foreign,FOREIGN.length);
  assert.equal(rep.protected,2);assert.equal(rep.bounded,false);
});
test('R32-08 bound: at most 256 removals per pass, and the report says the pass was bounded',async()=>{
  const many=Array.from({length:300},(_,i)=>['salahwx:'+(10+i)+'|5|c',W(WALL-9*H)]);
  const {r,gates}=await heldBoot({storage:many});gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  assert.equal(r.removes.length,256);assert.equal(r.run('qaState().cacheRetention.bounded'),true);
  assert.equal([...r.storage.keys()].filter(k=>k.startsWith('salahwx:')&&k!==WSEL).length,44);
});
test('R32-08 bound: at most 1024 entry reads per pass however many own entries exist',async()=>{
  const many=Array.from({length:1500},(_,i)=>['salahwx:'+(10+i)+'|5|c',W(WALL-H)]);
  const {r,gates}=await heldBoot({storage:many});const before=r.reads.length;
  gates.weather.resolve(okWeather(r.clock.wall));await flush(12);
  const passReads=r.reads.slice(before).filter(k=>k!==WSEL&&k!==SEL).length;
  assert.equal(passReads,1024);assert.deepEqual(r.removes,[]);assert.equal(r.run('qaState().cacheRetention.read'),1024);
});
test('R32-08 outer containment: a storage whose enumeration throws breaks neither the prayer write, renewal nor a settings change',async()=>{
  const {r,gates}=await heldBoot();
  Object.defineProperty(r.ctx.localStorage,'length',{get(){throw Error('contained access-denied enumeration');}});
  const unhandled=[];const on=e=>unhandled.push(e);process.on('unhandledRejection',on);
  try{
    gates.prayer.resolve(okPrayer('08-09-2026'));await flush(16);   // the prayer write is the first trigger
    assert.equal(r.run('today&&today.date.gregorian.date'),'08-09-2026','prayer adoption completed');
    assert.ok(r.storage.get(SEL).includes('08-09-2026'),'prayer cache written');
    gates.weather.resolve(okWeather(r.clock.wall));await flush(12);assert.equal(r.run('weather&&weather.temp'),24);
    assert.deepEqual(r.removes,[]);assert.equal(r.run('qaState().cacheRetention.failed'),true);
    r.ctx.__cfg={lat:21.42,lon:39.83,tz:'Asia/Riyadh',label:'Makkah',method:'4',school:'0',time:'24',units:'c',datefmt:'YYYY-MM-DD',source:'manual'};
    let done=false;r.run('applyConfig(__cfg)').then(()=>{done=true;},()=>{done=true;});
    for(let i=0;i<200&&!done;i++){await flush(2);if(!r.advanceTask()&&!r.advanceFrame())r.advanceTimer();}
    assert.ok(done,'settings change settled');assert.equal(r.run('lat'),21.42);
  }finally{process.off('unhandledRejection',on);}
  assert.deepEqual(unhandled,[]);
});
