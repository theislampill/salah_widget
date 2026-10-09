'use strict';
// Additional isolated audit fixtures only. Original expectations are preserved.
// Actual source regions/callers come from the delivered index; no production file is edited.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget', {source,record,harness,req,settle}=require(path.join(root,'tests/r0003-harness.cjs'));
const SHA=x=>crypto.createHash('sha256').update(x).digest('hex'), receipts=[];
async function check(name,fn){const observed=await fn();receipts.push({name,status:'PASS',observed:observed||null,environment:'Windows/Node v22.16.0; actual source-bound VM recording DOM; no browser or pixel claim'});}
const text=n=>(n.textContent||n.innerHTML||'').replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim();
function mutate(before,after){const raw=source();assert.equal(raw.split(before).length,2);return raw.replace(before,after);}
(async()=>{
 await check('R0004 omitted-hint same-day12Z Tokyo control needs no corrected-day request',async()=>{
  const h=harness({epoch:'2026-09-07T12:00:00Z',hash:'#lat=35.68&lon=139.69&method=2'}),boot=h.boot();
  req(h).ok(record('07-09-2026','Asia/Tokyo','same-day'));await settle();await boot;
  assert.equal(h.state().today.tag,'same-day');assert.equal(h.state().lastDate,'07-09-2026');assert.equal(h.state().tz,'Asia/Tokyo');
  assert.equal(h.requests.filter(r=>r.url.includes('/timings/07-09-2026?')).length,1);assert.ok(h.requests.every(r=>!r.url.includes('/timings/08-09-2026?')||h.run('_requestSlots.prefetch')!==null));
  return {currentDate:h.state().lastDate,zone:h.state().tz,currentDayRequests:1,requestDates:h.requests.map(r=>new URL(r.url).pathname.split('/').pop())};
 });
 await check('R0004 early hint-day cache-filter mutant loses valid offline Tokyo day8; explicit-zone control survives',async()=>{
  const before='const cached=readPrayerCache(op.cacheKey);',raw=mutate(before,'const rawCached=readPrayerCache(op.cacheKey); const cached=rawCached && rawCached.date===prayerCivilDay() ? rawCached : null;');
  const h=harness({source:raw,epoch:'2026-09-07T22:00:00Z',hash:'#lat=35.68&lon=139.69&method=2',offline:true});
  const oldBytes=JSON.stringify({date:'08-09-2026',data:record('08-09-2026','Asia/Tokyo','cached8')});h.storage.set('salah:35.68|139.69|America/New_York|2|0',oldBytes);
  const boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today,null);assert.equal(h.storage.get('salah:35.68|139.69|America/New_York|2|0'),oldBytes);
  const positive=harness({source:raw,epoch:'2026-09-07T22:00:00Z',hash:'#lat=35.68&lon=139.69&tz=Asia%2FTokyo&method=2',offline:true});
  positive.storage.set('salah:35.68|139.69|Asia/Tokyo|2|0',JSON.stringify({date:'08-09-2026',data:record('08-09-2026','Asia/Tokyo','cached8')}));
  const p=positive.boot();await positive.advance(2700);await p;assert.equal(positive.state().today.tag,'cached8');
  receipts.push({name:'early-filter mutant identity',sourceSha256:SHA(raw),mutantExpected:'omitted-hint offline cached8 unavailable; explicit-zone cached8 remains available',mutantObserved:'matched'});
  return {omittedHintMutantCurrent:null,explicitHintMutantTag:positive.state().today.tag,oldBytesRetained:true};
 });
 await check('R0004 removed loader day-correction check is contained by independent day-classifier; explicit control survives',async()=>{
  const raw=mutate('if(day!==requested){','if(false){');
  const h=harness({source:raw,epoch:'2026-09-07T22:00:00Z',hash:'#lat=35.68&lon=139.69&method=2'}),boot=h.boot();
  req(h).ok(record('07-09-2026','Asia/Tokyo','bootstrap'));await settle();await boot;
  assert.equal(h.state().today,null);assert.equal(h.paints.length,0);assert.equal(h.requests.length,1);
  const p=harness({source:raw,epoch:'2026-09-07T22:00:00Z',hash:'#lat=35.68&lon=139.69&tz=Asia%2FTokyo&method=2'}),pb=p.boot();
  req(p,'08-09-2026').ok(record('08-09-2026','Asia/Tokyo','explicit'));await settle();await pb;assert.equal(p.state().today.tag,'explicit');
  receipts.push({name:'post-response check mutant identity',sourceSha256:SHA(raw),mutantExpected:'cannot establish first qualified current paint; independent classifier prevents false current paint',mutantObserved:'matched; no regression was hidden as a PASS for boot availability'});
  return {omittedHintMutant:{today:null,paints:0,requests:1},explicitHintMutantTag:p.state().today.tag};
 });
 function P(day,ah){const r=record(day,'UTC',day);r.date.hijri.day=String(ah);return r;}
 await check('R0005 exact AH19→20 completed offline promotion preserves selected day20 across midnight',async()=>{
  const h=harness({epoch:'2026-09-07T23:59:59Z',offline:true});h.seed(P('07-09-2026',19),P('08-09-2026',20));h.run('render();startRenderLoop()');
  assert.equal(h.run('selectCalendarDisplay(model()).hijriText'),'1448-02-20');
  await h.advance(2000);await h.frame();assert.equal(h.state().lastDate,'08-09-2026');assert.equal(h.state()._prayerStale,false);
  assert.equal(h.run('selectCalendarDisplay(model()).hijriText'),'1448-02-20');assert.equal(h.nodes.get('.c').dataset.stale,'');
  assert.ok(text(h.nodes.get('#ah')).includes('1448-02-20'));
  assert.equal(JSON.parse(h.storage.get('salah:10|10|UTC|2|0')).date,'08-09-2026');
  return {date:h.state().lastDate,hijriText:h.run('selectCalendarDisplay(model()).hijriText'),renderedAH:text(h.nodes.get('#ah')),stale:h.state()._prayerStale,cacheDate:'08-09-2026'};
 });
 await check('R0005 late duplicate cannot poison tomorrow; next Sep9 data advances following Maghrib toAH21',async()=>{
  const h=harness({epoch:'2026-09-07T23:59:59Z'});h.seed(P('07-09-2026',19));h.run('render();startRenderLoop()');const old=req(h,'08-09-2026');
  await h.advance(1000);await h.frame();h.requests.filter(r=>r.url.includes('/timings/08-09-2026?'))[1].ok(P('08-09-2026',20));await settle();old.ok(P('08-09-2026',20));await settle();await h.frame();
  assert.equal(h.state().today.date.gregorian.date,'08-09-2026');assert.notEqual(h.state().tomorrow?.date.gregorian.date,'08-09-2026');
  req(h,'09-09-2026').ok(P('09-09-2026',21));await settle();h.wallBy(18*3600000);await h.frame();
  assert.equal(h.run('selectCalendarDisplay(model()).hijriText'),'1448-02-21');assert.equal(h.run('selectCalendarDisplay(model()).selectedSource'),'tomorrow');
  assert.ok(text(h.nodes.get('#ah')).includes('1448-02-21'));return {todayDate:h.state().today.date.gregorian.date,tomorrowDate:h.state().tomorrow.date.gregorian.date,hijriText:'1448-02-21',renderedAH:text(h.nodes.get('#ah')),selectedSource:'tomorrow'};
 });
 for(const [epoch,day,next]of [['2024-02-28T23:59:59Z','28-02-2024','29-02-2024'],['2024-02-29T23:59:59Z','29-02-2024','01-03-2024']])await check('R0005 exact2024 civil promotion '+day+'→'+next,async()=>{
  const h=harness({epoch,offline:true});h.seed(record(day,'UTC','old'),record(next,'UTC','next'));h.run('startRenderLoop()');await h.frame();await h.advance(1000);await h.frame();
  assert.equal(h.state().lastDate,next);assert.equal(h.state().today.tag,'next');assert.equal(h.state()._prayerStale,false);
  return {from:day,to:h.state().lastDate,stale:h.state()._prayerStale};
 });
 await check('R0007 actual drawArc SVG unaffected by wall-minute countdown mutant at spring01:30;150m current interval is discriminated',async()=>{
  const before='leftMin, nowEpoch, nextEpoch,',raw=mutate(before,'leftMin:nextMin-nowMin, nowEpoch, nextEpoch,');
  const opts={epoch:'2026-03-08T06:30:00Z',hash:'#lat=40.71&lon=-74.01&tz=America%2FNew_York&method=2'},good=harness(opts),bad=harness({...opts,source:raw});
  for(const h of [good,bad])h.seed(record('08-03-2026','America/New_York','spring'));
  assert.equal(good.run('model().leftMin'),150);assert.equal(bad.run('model().leftMin'),210);
  const actual=good.run('drawArc(model())');assert.equal(actual,bad.run('drawArc(model())'));assert.doesNotMatch(actual,/NaN|Infinity|undefined/);
  receipts.push({name:'actual-arc equality identity',svgSha256:SHA(actual),mutantSourceSha256:SHA(raw),pixelLimitation:'Source SVG equality is not a rendered crop; the required browser spring150m layout remains unverified.'});
  return {nowEpoch:Date.parse('2026-03-08T06:30:00Z'),expectedNextEpoch:Date.parse('2026-03-08T09:00:00Z'),leftMin:150,wallMutantLeftMin:210,arcEqual:true,arcSha256:SHA(actual)};
 });
 const out={schema:'pr42-worker-A-isolated-controls/1',targetCommit:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',indexSha256:SHA(source()),fixtureSha256:SHA(fs.readFileSync(__filename)),status:'PASS_SCOPED',checks:receipts.filter(r=>r.status==='PASS').length,receipts,limits:['No browser or rendered-pixel proof','Mutations are source strings confined to this VM, with original expectations disclosed; final production bytes were not changed.']};
 fs.writeFileSync(path.join(__dirname,'targeted-controls.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
