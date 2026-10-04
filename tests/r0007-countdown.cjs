'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const {test} = require('node:test');
const {modelRealm, prayerRecord, loadRender, loadLifecycle, source, modelSource, renderSource, lifecycle, sha256, countedIntl} = require('./r0008-clock-harness.cjs');
console.log(`SOURCE ${sha256(source)} MODEL ${sha256(modelSource)} RENDER ${sha256(renderSource)}`);
for(const [name,date,now,target,zone,expected] of [
  ['spring', '2026-03-08','2026-03-08T01:30:00-05:00','2026-03-08T05:00:00-04:00','America/New_York',150],
  ['fall first 01:30','2026-11-01','2026-11-01T01:30:00-04:00','2026-11-01T05:00:00-05:00','America/New_York',270],
  ['ordinary control','2026-09-07','2026-09-07T01:30:00-04:00','2026-09-07T05:00:00-04:00','America/New_York',210],
  ['fall 00:30 additional control','2026-11-01','2026-11-01T00:30:00-04:00','2026-11-01T05:00:00-05:00','America/New_York',330],
  ['fall second 01:30','2026-11-01','2026-11-01T01:30:00-05:00','2026-11-01T05:00:00-05:00','America/New_York',210],
  ['fractional offset control','2026-09-07','2026-09-07T01:30:00+05:45','2026-09-07T05:00:00+05:45','Asia/Kathmandu',210]
]) test(name + ' reaches actual model and countdown assignments', () => {
  const c=loadRender(modelRealm({zone,wall:Date.parse(now),globals:{today:prayerRecord(date,zone)}}));
  c.clock.reads=0;
  const m=c.run('model()');
  assert.equal(m.leftMin,expected); assert.equal(m.nextKey,'Fajr'); assert.equal(m.nextTime,'05:00');
  assert.equal(m.nextDateStr,date.split('-').reverse().join('-')); assert.equal(m.nextZone,zone);
  assert.equal(m.nextEpoch,Date.parse(target)); assert.equal(c.clock.reads,1,'model snapshots the current instant once');
  c.run('render()');
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert(c.dom.querySelector('.left').innerHTML.includes(`${Math.floor(expected/60)}h ${expected%60}m`));
  assert(c.dom.querySelector('.times').innerHTML.includes('Fajr'));
});

test('overnight uses the actual next-day date across spring; missing/wrong-day data stays unavailable then recovers', () => {
  const zone='America/New_York';
  const c=loadRender(modelRealm({zone,wall:Date.parse('2026-03-07T23:30:00-05:00'),
    globals:{today:prayerRecord('2026-03-07',zone)}}));
  assert(Number.isNaN(c.run('model().leftMin')));
  c.run('render()');
  assert.equal(c.dom.querySelector('.nt').textContent,'—');
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  c.context.tomorrow=prayerRecord('2026-03-07',zone); c.run('render()');
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  c.context.tomorrow=prayerRecord('2026-03-08',zone); c.run('render()');
  assert.equal(c.run('model().leftMin'),270);
  assert.equal(c.run('model().nextEpoch'),Date.parse('2026-03-08T05:00:00-04:00'));
  assert.equal(c.run('model().nextDateStr'),'08-03-2026');
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert(c.dom.querySelector('.left').innerHTML.includes('4h 30m'));
  c.context.fmt24=false; c.run('render()');
  assert.equal(c.dom.querySelector('.nt').textContent,'5:00 AM');
});

for(const [name,now,date,clocks] of [
  ['gap','2026-03-08T01:30:00-05:00','2026-03-08',{Fajr:'02:30'}],
  ['fold','2026-11-01T00:30:00-04:00','2026-11-01',{Fajr:'01:30'}]
]) test(name+' endpoint is withheld by actual render', () => {
  const c=loadRender(modelRealm({zone:'America/New_York',wall:Date.parse(now),
    globals:{today:prayerRecord(date,'America/New_York',clocks)}}));
  c.run('render()');
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  assert.equal(c.dom.querySelector('.nt').textContent,'—');
});

test('exact boundary selects the following event and ordinary wall progress is retained', () => {
  const c=modelRealm({zone:'UTC',wall:Date.parse('2026-09-07T15:30Z'),globals:{today:prayerRecord('2026-09-07','UTC')}});
  const m=c.run('model()');
  assert.equal(m.currentKey,'Asr'); assert.equal(m.nextKey,'Maghrib'); assert.equal(m.nextTime,'18:00');
  assert.equal(m.leftMin,150); assert.equal(m.progress,0);
  assert.equal(m.noon,720); assert.equal(m.sunrise,360); assert.equal(m.sunset,1080);
  assert.deepEqual(Array.from(m.dots,d=>[d.k,d.abs]),[['Fajr',300],['Sunrise',360],['Dhuhr',720],['Asr',930],['Maghrib',1080],['Isha',1170]]);
});

for(const [name,date,next,now,target] of [
  ['year boundary','2026-12-31','2027-01-01','2026-12-31T23:30Z','2027-01-01T05:00Z'],
  ['leap boundary','2024-02-28','2024-02-29','2024-02-28T23:30Z','2024-02-29T05:00Z']
]) test(name+' resolves next-day Fajr without adding 24 elapsed hours', () => {
  const c=modelRealm({zone:'UTC',wall:Date.parse(now),globals:{today:prayerRecord(date,'UTC'),tomorrow:prayerRecord(next,'UTC')}});
  assert.equal(c.run('model().nextEpoch'),Date.parse(target)); assert.equal(c.run('model().leftMin'),330);
  assert.equal(c.run('tomorrowStr()'),next.split('-').reverse().join('-'));
});

for(const clocks of [{Fajr:'--:--'},{Sunset:'Infinity:00'},{Sunset:'1e300:00'}]) test('finite model defense precedes normalization '+JSON.stringify(clocks), () => {
  const c=loadRender(modelRealm({zone:'UTC',globals:{today:prayerRecord('2026-09-07','UTC',clocks)}}));
  let result;
  assert.doesNotThrow(()=>{result=vm.runInContext('model()',c.context,{timeout:100});});
  assert.equal(result,null);
  c.run('render()');
  assert.equal(c.dom.querySelector('.left').textContent,'Prayer times unavailable');
});

test('ordinary baseline control reaches real render without tomorrow', () => {
  const c=loadRender(modelRealm({zone:'America/New_York',wall:Date.parse('2026-09-07T01:30-04:00'),
    globals:{today:prayerRecord('2026-09-07','America/New_York')}}));
  const m=c.run('model()'); assert.equal(m.leftMin,210); assert.equal(m.nextKey,'Fajr'); assert.equal(m.nextTime,'05:00');
  c.run('render()'); assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert(c.dom.querySelector('.left').innerHTML.includes('3h 30m'));
});

test('actual repeated model consumer reuses the same day profile', () => {
  const {intl,counts}=countedIntl();
  const c=modelRealm({intl,zone:'UTC',wall:Date.parse('2026-09-07T01:30Z'),globals:{today:prayerRecord('2026-09-07','UTC')}});
  c.run('model()'); const before=counts.projections;
  for(let i=0;i<20;i++) {c.clock.wall+=1000; assert.equal(c.run('model().nextKey'),'Fajr');}
  assert.equal(counts.projections-before,40,'one wall projection and one endpoint check per model; no day rebuild');
});

test('invalid explicit model exits before nonfinite wall projection', () => {
  const {intl,counts}=countedIntl();
  const c=modelRealm({intl,query:'simTime=02:30',zone:'America/New_York',wall:Date.parse('2026-03-08T12:00Z'),
    globals:{today:prayerRecord('2026-03-08','America/New_York')}});
  assert.equal(c.run('model()'),null); assert.equal(counts.invalid,0);
});

test('wall-minute subtraction and today-plus-24h mutants are caught while ordinary control survives', () => {
  const wall=modelSource.replace('leftMin, nowEpoch, nextEpoch,','leftMin:nextMin-nowMin, nowEpoch, nextEpoch,'); assert.notEqual(wall,modelSource);
  function withModel(block,now,date,tomorrow=null) {
    const c=modelRealm({zone:'America/New_York',wall:Date.parse(now),globals:{today:prayerRecord(date,'America/New_York'),tomorrow}});
    c.run(block); return c.run('model()');
  }
  assert.equal(withModel(wall,'2026-09-07T01:30-04:00','2026-09-07').leftMin,210);
  assert.equal(withModel(wall,'2026-03-08T01:30-05:00','2026-03-08').leftMin,210);
  assert.equal(withModel(wall,'2026-11-01T01:30-04:00','2026-11-01').leftMin,210);
  const elapsed24=modelSource.replace('const nextEpoch=nextDay ?','const nextEpoch=tomorrowFlag && currentDay ? epochForTzTime(currentDay.y,currentDay.mo,currentDay.d,nextHour,nextMinute,nextZone)+86400000 : nextDay ?'); assert.notEqual(elapsed24,modelSource);
  const m=withModel(elapsed24,'2026-03-07T23:30-05:00','2026-03-07',prayerRecord('2026-03-08','America/New_York'));
  assert.equal(m.leftMin,330); assert.notEqual(m.leftMin,270);
  console.log(`MUTANT wall-minutes ${sha256(wall)} / elapsed-24h ${sha256(elapsed24)} rejected`);
});

test('finite equal/reordered polar records remain usable', () => {
  for(const clocks of [
    {Fajr:'00:00',Sunrise:'00:00',Dhuhr:'00:00',Asr:'00:00',Maghrib:'00:00',Sunset:'00:00',Isha:'00:00'},
    {Fajr:'18:00',Sunrise:'19:00',Dhuhr:'12:00',Asr:'05:00',Maghrib:'06:00',Sunset:'06:00',Isha:'09:00'}
  ]) {
    const c=modelRealm({zone:'UTC',globals:{today:prayerRecord('2026-09-07','UTC',clocks),tomorrow:prayerRecord('2026-09-08','UTC',clocks)}});
    const m=c.run('model()'); assert(m); assert(Number.isFinite(m.progress));
  }
});

function heldOvernight(block=lifecycle){
  const c=loadLifecycle(loadRender(modelRealm({query:'simTime=23:30',zone:'America/New_York',
    wall:Date.parse('2026-03-07T23:30:00-05:00'),globals:{today:prayerRecord('2026-03-07','America/New_York')}})),block,{autoTimings:false});
  c.run('startRenderLoop()'); c.frame();
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  assert.equal(c.dom.querySelector('.nt').textContent,'—');
  assert.equal(c.prayerTransport.requests.length,1);
  assert.equal(c.prayerTransport.requests[0].day,'08-03-2026');
  assert.equal(c.prayerTransport.requests[0].zone,'America/New_York');
  assert.equal(c.run('_requestSlots.prefetch.requestedDay'),'08-03-2026');
  assert.equal(c.run('_renderDirty'),false);
  return c;
}
async function settleOvernight(c){
  const instant=c.run('simNow()');
  c.prayerTransport.requests[0].resolve(); await c.prayerTransport.settle();
  assert.equal(c.run('tomorrow.date.gregorian.date'),'08-03-2026');
  assert.equal(c.run('_requestSlots.prefetch'),null);
  assert.equal(c.prayerTransport.timers.size,0);
  assert.equal(c.run('_renderDirty'),true);
  c.frame(); assert.equal(c.run('simNow()'),instant,'late arrival does not advance a frozen scene');
  return c;
}
test('actual held prefetch restores the frozen overnight countdown on the dirty visible frame', async()=>{
  const c=await settleOvernight(heldOvernight());
  assert.equal(c.run('model().leftMin'),270);
  assert.equal(c.run('model().nextEpoch'),Date.parse('2026-03-08T05:00:00-04:00'));
  assert.equal(c.run('model().nextDateStr'),'08-03-2026');
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert(c.dom.querySelector('.left').innerHTML.includes('4h 30m'));
  assert.equal((c.dom.querySelector('.times').innerHTML.match(/class="p /g)||[]).length,6);
  c.context.fmt24=false; c.run('_renderDirty=true'); c.frame();
  assert.equal(c.dom.querySelector('.nt').textContent,'5:00 AM');
});
test('sec-only loop mutant cannot paint a late countdown in a frozen scene', async()=>{
  const predicate='if(sec!==_lastSec || _renderDirty)';
  assert.equal(lifecycle.split(predicate).length,2);
  const secOnly=lifecycle.replace(predicate,'if(sec!==_lastSec)');
  const c=await settleOvernight(heldOvernight(secOnly));
  assert.equal(c.run('model().leftMin'),270,'actual adoption still supplies the valid endpoint');
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  assert.equal(c.dom.querySelector('.nt').textContent,'—');
  console.log(`MUTANT sec-only ${sha256(secOnly)} rejected by actual late-prefetch consumer`);
});
test('actual config generation cancels a held old-zone prefetch before the recovered countdown', async()=>{
  const c=heldOvernight(), obsolete=c.prayerTransport.requests[0];
  const applying=c.run('applyConfig({lat:24,lon:39,tz:"UTC"})');
  assert.equal(obsolete.init.signal.aborted,true);
  assert.equal(c.run('_runtimeGeneration'),1);
  assert.equal(c.prayerTransport.requests.length,2);
  const current=c.prayerTransport.requests[1];
  assert.equal(current.day,'08-03-2026'); assert.equal(current.zone,'UTC');
  obsolete.resolve(); await c.prayerTransport.settle();
  assert.equal(c.context.tz,'UTC'); assert.equal(c.context.today,null); assert.equal(c.context.tomorrow,null);
  assert.equal(c.run('_requestSlots.current.requestZone'),'UTC');
  current.resolve(); await applying; c.frame();
  assert.equal(c.context.today.meta.timezone,'UTC');
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  const next=c.prayerTransport.requests[2]; assert(next);
  assert.equal(next.day,'09-03-2026'); assert.equal(next.zone,'UTC');
  next.resolve(); await c.prayerTransport.settle(); c.frame();
  assert.equal(c.run('model().nextEpoch'),Date.parse('2026-03-09T05:00:00Z'));
  assert.equal(c.run('model().leftMin'),330);
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert(c.dom.querySelector('.left').innerHTML.includes('5h 30m'));
});
