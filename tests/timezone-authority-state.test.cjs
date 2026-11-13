'use strict';
// R002D timezone authority (docs/state-contracts/R002D.md; issue 94 rows D-01..D-11).
// VM evidence only: the actual config, admission, loader, clock and scene-identity owners run unchanged
// through the repository harnesses with stubbed provider responses. No network, no browser, no pixels.
// RED/mutation runs point SALAH_REQUEST_SOURCE / SALAH_REQUEST_CONFIG at another generated index.html /
// config.js (read once by tests/r0003-harness.cjs; also passed to the full-runtime r001d harness here).
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {harness,record,settle,source:currentSource}=require('./r0003-harness.cjs');
const {load}=require('./r001d-harness.cjs');
const root=path.resolve(__dirname,'..');
const indexSource=()=>process.env.SALAH_REQUEST_SOURCE?fs.readFileSync(process.env.SALAH_REQUEST_SOURCE,'utf8'):undefined;
const configSource=fs.readFileSync(process.env.SALAH_REQUEST_CONFIG||path.join(root,'config.js'),'utf8');

const BAD_HINTS=['Bogus/Zone','Asia/Riyad','+03:00',''];
// 22:00Z: New York is still on 07-09-2026 (18:00), Riyadh is already on 08-09-2026 (01:00).
const SPLIT_EPOCH='2026-09-07T22:00:00Z';
const dayOf=url=>{const m=/\/timings\/([^?]*)/.exec(String(url));return m?m[1]:null;};
const realDay=d=>typeof d==='string'&&/^\d{2}-\d{2}-\d{4}$/.test(d);
// config.js absent: the same source with the shared module hidden before the native owner reads it (W1b).
const legacySource=()=>{
  const raw=currentSource(),marker='// ---- config:';
  assert.ok(raw.includes(marker));
  return raw.replace(marker,marker+' (fixture: config.js absent)\nwindow.SalahConfig=undefined;\n//');
};

// Answer every timings request with the provider zone (an unresolvable day fails like a provider error).
async function serveProvider(h,zone='Asia/Riyadh',rounds=8){
  for(let i=0;i<rounds;i++){
    for(const r of h.requests){
      if(r.served)continue;r.served=true;
      const d=dayOf(r.url);
      if(realDay(d))r.ok(record(d,zone,'provider'));else r.fail();
    }
    await settle();await h.advance(h.elapsed()+2000);
  }
}
async function bootAndServe(h,zone){
  const {pending}=await h.startBoot();
  await serveProvider(h,zone);
  await Promise.race([pending,settle()]);
}
const admissible=zone=>{try{return typeof zone==='string'&&!!zone&&!/^[+-]/.test(zone)&&!!new Intl.DateTimeFormat('en',{timeZone:zone}).format(0);}catch{return false;}};

for(const legacy of [false,true])for(const hint of BAD_HINTS){
  test(`D-01 rejected hint ${JSON.stringify(hint)} recovers to the provider zone (${legacy?'legacy fallback W1b':'config.js W1'})`,async()=>{
    const h=harness({epoch:SPLIT_EPOCH,hash:`#lat=24.47&lon=39.61&label=Madinah&method=4&tz=${encodeURIComponent(hint)}`,...(legacy?{source:legacySource()}:{})});
    assert.equal(h.run('typeof window.SalahConfig'),legacy?'undefined':'object');
    const bound=h.state().tz;
    assert.ok(admissible(bound),'live tz is admissible from the first binding: '+bound);
    assert.equal(bound,'America/New_York','a rejected hint binds the absent-hint default');
    assert.equal(h.run('cacheKey()'),'salah:24.47|39.61|America/New_York|4|0','the cache key is that of an absent hint');
    await bootAndServe(h,'Asia/Riyadh');
    const days=h.requests.map(r=>dayOf(r.url));
    assert.ok(days.length>0&&days.every(realDay),'every request names a real civil day: '+JSON.stringify(days));
    // Hint day, then the one corrected day (existing R0004 budget), then the ordinary next-day prefetch.
    assert.deepEqual(days,['07-09-2026','08-09-2026','09-09-2026']);
    const s=h.state();
    assert.equal(s.tz,'Asia/Riyadh');assert.equal(s.today?.date?.gregorian?.date,'08-09-2026');assert.equal(s.lastDate,'08-09-2026');
    // The boot-time withdrawal (t=0) is the ordinary pre-acquisition presentation, as for a valid hint.
    assert.ok(!h.errors.some(e=>e.at>0&&/unavailable|Could not load/.test(e.text)),'no unavailable presentation after boot: '+JSON.stringify(h.errors));
    assert.ok(h.paints.some(p=>p.today&&p.tz==='Asia/Riyadh'),'the recovered timetable was painted');
  });
}

test('D-01 non-string stored/bound hints bind the default, and config.js normalize applies the same predicate',()=>{
  const h=harness({hash:'#lat=24.47&lon=39.61&method=4&tz=Asia%2FRiyadh'});
  for(const raw of [42,{},['Asia/Riyadh'],'Asia/Riyad','+03:00','-05:00']){
    h.run(`bindConfig({...CONFIG,tz:${JSON.stringify(raw)}})`);
    assert.equal(h.run('tz'),'America/New_York',JSON.stringify(raw));assert.equal(h.run('_cacheTz'),'America/New_York');
    h.run('bindConfig({...CONFIG,tz:"Asia/Riyadh"})');assert.equal(h.run('tz'),'Asia/Riyadh');
  }
  const ctx=vm.createContext({window:{},URLSearchParams,Intl,Promise,Date,console});ctx.window=ctx;vm.runInContext(configSource,ctx);
  const table=['UTC','Asia/Riyadh','America/New_York','Asia/Kathmandu','Etc/GMT+3','Bogus/Zone','Asia/Riyad','+03:00','-05:00','',null,undefined,42,{},' Asia/Riyadh'];
  for(const z of table){
    const index=h.run(`admissibleZone(${z===undefined?'undefined':JSON.stringify(z)})`);
    const normalized=ctx.SalahConfig.normalize({tz:z}).tz;
    assert.equal(index,admissible(z),'index predicate '+JSON.stringify(z));
    assert.equal(normalized===z,index,'config.js normalize agrees for '+JSON.stringify(z));
    if(!index)assert.equal(normalized,'America/New_York');
    // Provider metadata uses the same predicate (behaviour-identical extraction).
    h.run(`window.__r=${JSON.stringify(record('07-09-2026','UTC'))};__r.meta.timezone=${z===undefined?'undefined':JSON.stringify(z)};`);
    assert.equal(h.run('admitPrayerRecord(__r,"07-09-2026").ok'),index,'admitPrayerRecord zone rule for '+JSON.stringify(z));
  }
});

for(const legacy of [false,true])test(`D-02 rejected hint with simTime: scene valid, prayer acquired, fragment re-anchored in the adopted zone (${legacy?'legacy':'config.js'})`,async()=>{
  const h=harness({epoch:'2026-09-07T12:00:00Z',hash:'#lat=24.47&lon=39.61&method=4&tz=Bogus%2FZone&simTime=22:00',...(legacy?{source:legacySource()}:{})});
  assert.ok(Number.isFinite(h.run('simNow()')),'the explicit scene projects in the effective hint');
  await bootAndServe(h,'Asia/Riyadh');
  assert.ok(!h.errors.some(e=>e.text==='Simulation time unavailable'),JSON.stringify(h.errors));
  const s=h.state();assert.equal(s.tz,'Asia/Riyadh');assert.ok(s.today,'prayer acquired');
  assert.equal(h.run('_simTz'),'Asia/Riyadh','the fragment anchor re-anchored in the adopted zone');
  assert.equal(h.run('(p=>p.h+":"+p.mi)(partsInTz(simNow()))'),'22:0');
  assert.ok(h.requests.every(r=>realDay(dayOf(r.url))));
});

test('D-03 qaState exposes configured/admitted/effective/adopted/source without changing visible text',async()=>{
  const h=load({source:indexSource(),hash:'#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Bogus%2FZone&units=c&seed=1'});
  const z=h.run('qaState().zone');
  assert.deepEqual(JSON.parse(JSON.stringify(z)),{configured:'Bogus/Zone',admitted:false,effective:'America/New_York',adopted:null,source:null,live:'America/New_York',anchor:'wall'});
  h.run('today=null;tomorrow=null;lastDate=null;');
  await h.complete(h.run('loadPrayerData()'),{turns:200});
  const after=JSON.parse(JSON.stringify(h.run('qaState().zone')));
  assert.equal(after.adopted,'Asia/Riyadh');assert.equal(after.live,'Asia/Riyadh');assert.ok(['network','record'].includes(after.source));assert.equal(after.effective,'America/New_York');
  const v=load({source:indexSource(),hash:'#lat=24.47&lon=39.61&method=4&tz=Asia%2FRiyadh'});
  assert.deepEqual(JSON.parse(JSON.stringify(v.run('qaState().zone'))),{configured:'Asia/Riyadh',admitted:true,effective:'Asia/Riyadh',adopted:null,source:null,live:'Asia/Riyadh',anchor:'wall'});
});

test('D-04 an unresolved civil day issues no provider request and recovers once the day resolves',async()=>{
  const h=harness({epoch:'2026-09-07T12:00:00Z',hash:'#lat=24.47&lon=39.61&method=4&tz=Asia%2FRiyadh'});
  h.run('window.__civil=prayerCivilDay;prayerCivilDay=()=>null;');
  const {pending}=await h.startBoot();await settle();await h.advance(5000);await Promise.race([pending,settle()]);
  assert.equal(h.requests.length,0,'no request for an unresolved day: '+JSON.stringify(h.requests.map(r=>r.url)));
  assert.equal(h.state().today,null);
  assert.equal(h.run('_requestSlots.current'),null,'no current owner is held');
  for(let i=0;i<3;i++){h.elapse(1000);await h.frame();}
  assert.equal(h.requests.length,0,'maintenance does not retry while the day is unresolved');
  h.run('prayerCivilDay=window.__civil;');
  for(let i=0;i<4&&!h.requests.length;i++){h.elapse(1000);await h.frame();}
  assert.deepEqual(h.requests.map(r=>dayOf(r.url)),['07-09-2026'],'retried on a later maintenance opportunity');
  await serveProvider(h,'Asia/Riyadh');assert.equal(h.state().today?.date?.gregorian?.date,'07-09-2026');
  await assert.rejects(h.run('fetchTimings(null)'),/unresolved prayer day/);
  assert.equal(h.run('beginPrayerRequest("prefetch","null")'),null);
});

test('D-05 an admitted hint keeps the R0004 cache key and request sequence',async()=>{
  for(const [hash,key,days] of [
    ['#lat=24.47&lon=39.61&method=4&tz=Asia%2FRiyadh','salah:24.47|39.61|Asia/Riyadh|4|0',['08-09-2026','09-09-2026']],
    ['#lat=24.47&lon=39.61&method=4','salah:24.47|39.61|America/New_York|4|0',['07-09-2026','08-09-2026','09-09-2026']]]){
    const h=harness({epoch:SPLIT_EPOCH,hash});
    assert.equal(h.run('cacheKey()'),key);
    await bootAndServe(h,'Asia/Riyadh');
    assert.deepEqual(h.requests.map(r=>dayOf(r.url)),days,hash);
    assert.equal(h.run('cacheKey()'),key,'adoption never re-keys the cache');
    assert.deepEqual(h.writes.map(w=>w.key),[key]);
  }
});

// Full native runtime (r001d): count scene restarts and Moon invalidations across an ordinary boot.
async function sceneTrial(hash){
  const h=load({source:indexSource(),hash});
  h.run('today=null;tomorrow=null;lastDate=null;');
  const realHost=h.run('window.SalahNativeSkyHost');
  h.ctx.__realCapture=realHost&&realHost.capture?realHost.capture.bind(realHost):null;
  h.run('window.__inv=[];window.SalahMoonRuntime={request(){return false},surface(){return null},invalidate(r){window.__inv.push(r)},finishInitialDocument(){},get state(){return {}},get disposed(){return false}};');
  h.run('window.SalahNativeSkyHost={cloudLighting(){return {sun:{altDeg:-30}}},notify(){},capture(){return __realCapture?__realCapture():null}};');
  h.run('window.__scenes=[];window.__pending=[];const __b=beginSkyScene;beginSkyScene=function(...a){window.__scenes.push(skySceneIdentity());return __b.apply(this,a);};');
  const before=h.run('skySceneIdentity()');
  await h.complete(h.run('boot()'),{turns:200});
  const committed=h.run('_skySceneKey');
  for(let i=0;i<5;i++){h.run('_renderDirty=true');try{h.advanceFrame();}catch{}}
  return {before,committed,after:h.run('skySceneIdentity()'),tz:h.run('tz'),scenes:h.run('window.__scenes.length'),
    inv:h.run('window.__inv.length'),pending:h.select('.c').classList.contains('sky-pending'),key:h.run('_skySceneKey'),
    days:h.requests.map(r=>r.dateStr),captureTz:h.run('(()=>{try{return __realCapture?__realCapture().tz:null}catch(e){return "capture-error"}})()')};
}
test('D-06 wall-mode zone adoption keeps the scene, Moon scope and refined identity zone (builder shape vs control)',async()=>{
  const builder=await sceneTrial('#lat=24.47&lon=39.61&label=Madinah&method=4');
  const control=await sceneTrial('#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh');
  assert.equal(builder.tz,'Asia/Riyadh');assert.equal(control.tz,'Asia/Riyadh');
  assert.equal(builder.scenes,control.scenes,'adoption begins no extra scene: '+JSON.stringify({builder,control}));
  assert.equal(builder.inv,control.inv,'adoption invalidates no extra Moon scope');
  assert.equal(builder.after,builder.before,'scene identity unchanged by hint->adopted transition');
  assert.equal(builder.key,builder.committed);
  assert.equal(builder.pending,control.pending,'no sky-pending re-add after the first commit');
  if(builder.captureTz!==null&&builder.captureTz!=='capture-error')assert.equal(builder.captureTz,'America/New_York','refined identity zone is the configured hint, not the adopted zone');
});

for(const timeScale of [null,60])test(`D-07 fragment anchors still re-anchor in the adopted zone (simTime${timeScale?'+timeScale':''})`,async()=>{
  const h=harness({epoch:'2026-09-07T12:00:00Z',hash:'#lat=24.47&lon=39.61&method=4&simTime=22:00'+(timeScale?'&timeScale='+timeScale:'')});
  assert.equal(h.run('simNow(),_simTz'),'America/New_York');
  await bootAndServe(h,'Asia/Riyadh');
  assert.equal(h.run('simNow(),_simTz'),'Asia/Riyadh','re-anchored on zone settle');
  if(!timeScale)assert.equal(h.run('(p=>p.h+":"+p.mi)(partsInTz(simNow()))'),'22:0');
});

for(const rate of [0,60])test(`D-08/D-09 SalahClock ${rate?'advancing':'frozen'} preview survives zone adoption`,async()=>{
  const h=harness({epoch:'2026-09-07T12:00:00Z',hash:'#lat=35.68&lon=139.69&method=2'});
  const {pending}=await h.startBoot();
  const target=Date.parse('2026-12-25T03:00:00Z');
  h.run('var _wxDecisionCache=null;');h.run(`SalahClock.set({utcMs:${target},rate:${rate}})`);
  const t0=h.elapsed();
  assert.equal(h.state().tz,'America/New_York');
  await serveProvider(h,'Asia/Tokyo');await Promise.race([pending,settle()]);
  assert.equal(h.state().tz,'Asia/Tokyo','the provider zone was adopted');
  const expected=target+(h.elapsed()-t0)*rate;
  assert.equal(h.run('simNow()'),expected,'the requested instant (plus elapsed x rate) survives adoption');
  assert.equal(h.run('_clockPreview'),true);
  h.run('SalahClock.set({live:true})');assert.equal(h.run('_clockPreview'),false);assert.equal(h.run('simNow()'),h.run('Date.now()'));
});

test('D-11 first-paint and native identity agree for hint!=provider and hint=provider',async()=>{
  const fp=fs.readFileSync(path.join(root,'real-sky/native-first-paint.mjs'),'utf8');
  assert.ok(fp.includes("sceneIdentity:[c.lat,c.lon,c.tz||'America/New_York','wall'].join('|')"),'first-paint identity formula is the bound one');
  const ctx=vm.createContext({window:{},URLSearchParams,Intl,Promise,Date,console});ctx.window=ctx;vm.runInContext(configSource,ctx);
  for(const hash of ['#lat=24.47&lon=39.61&label=Madinah&method=4','#lat=24.47&lon=39.61&method=4&tz=Asia%2FRiyadh','#lat=24.47&lon=39.61&method=4&tz=Bogus%2FZone']){
    const c=ctx.SalahConfig.resolve(hash).cfg,first=[c.lat,c.lon,c.tz||'America/New_York','wall'].join('|');
    const t=await sceneTrial(hash);
    assert.equal(t.before,first,'boot identity = first-paint identity: '+hash);
    assert.equal(t.after,first,'identity after adoption = first-paint identity: '+hash);
  }
});
