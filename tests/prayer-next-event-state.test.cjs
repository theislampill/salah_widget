'use strict';

const test=require('node:test'),assert=require('node:assert/strict');
const {prayerRecord,modelRealm,loadRender}=require('./r0008-clock-harness.cjs');

// Exercise production admission/adoption, model and render. The existing fixture
// contains transport and unrelated sky producers; it makes no native pixel claim.
function admittedScene({now='2026-09-07T23:00:00Z',zone='UTC',date='2026-09-07',nextDate='2026-09-08',clocks={},nextClocks=clocks,next=true}={}){
  const c=loadRender(modelRealm({zone,wall:Date.parse(now),globals:{today:null,tomorrow:null}}));
  c.context.currentInput=prayerRecord(date,zone,clocks);
  c.context.currentInput.date.gregorian.date=date.split('-').reverse().join('-');
  assert.equal(c.run('adoptPrayerBundle(currentInput,currentInput.date.gregorian.date,null,true,false)'),true);
  if(next){
    c.context.nextInput=prayerRecord(nextDate,zone,nextClocks);
    c.context.nextInput.date.gregorian.date=nextDate.split('-').reverse().join('-');
    assert.equal(c.run('adoptPrayerBundle(nextInput,nextInput.date.gregorian.date,null,false,false)'),true);
  }
  return c;
}

test('ES07-01 actual admitted reordered tomorrow selects Isha 00:31 and 91 elapsed minutes',()=>{
  const c=admittedScene({clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}});
  c.run('render()');const actual=c.run('_lastRender');
  assert.equal(actual.nextKey,'Isha');
  assert.equal(actual.nextTime,'00:31');
  assert.equal(actual.nextDate,'08-09-2026');
  assert.equal(actual.nextEpoch,Date.parse('2026-09-08T00:31:00Z'));
  assert.equal(actual.leftMin,91);
  assert.equal(c.dom.querySelector('.nt').textContent,'00:31');
  assert.match(c.dom.querySelector('.left').innerHTML,/1h 31m/);
  assert.match(c.dom.querySelector('.left').innerHTML,/until-prayer">Isha</);
  assert.match(c.dom.querySelector('.times').innerHTML,/class="p on [^"]*" data-prayer-key="Isha"[^]*?<span class="tm">00:31<\/span>/);
});

test('ES07-02 actual admitted ordinary tomorrow retains Fajr 05:00 and 360 elapsed minutes',()=>{
  const c=admittedScene();c.run('render()');const actual=c.run('_lastRender');
  assert.equal(actual.nextKey,'Fajr');assert.equal(actual.nextTime,'05:00');
  assert.equal(actual.nextDate,'08-09-2026');
  assert.equal(actual.nextEpoch,Date.parse('2026-09-08T05:00:00Z'));
  assert.equal(actual.leftMin,360);
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert.match(c.dom.querySelector('.left').innerHTML,/6h 0m/);
});

for(const year of ['0001','0099','0999','1000','2026'])test('review SRC-02 admitted year '+year+' retains canonical target and completed-render dates',()=>{
  const date=year+'-09-07',canonical='07-09-'+year;
  const c=admittedScene({now:date+'T01:30:00Z',date,next:false}),m=c.run('model()');
  assert(m,'valid admitted current timetable remains usable');
  assert.equal(m.selection.state,'same-day-target');assert.equal(m.nextKey,'Fajr');
  assert.equal(m.nextEpoch,Date.parse(date+'T05:00:00Z'));assert.equal(m.leftMin,210);
  assert.equal(m.nextDateStr,canonical);assert.equal(m.nowWall.dateStr,canonical);
  c.run('render()');const r=c.run('_lastRender');
  assert.equal(r.nextDate,canonical);assert.equal(r.timetableDate,canonical);assert.equal(r.sim,canonical+' 01:30');
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert.match(c.dom.querySelector('.left').innerHTML,/3h 30m/);
});

test('review SRC-02 small-year next-day event retains its actual civil successor',()=>{
  const c=admittedScene({now:'0001-09-07T23:00:00Z',date:'0001-09-07',nextDate:'0001-09-08',clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}});
  c.run('render()');const r=c.run('_lastRender');assert(r,'valid admitted timetable renders');
  assert.equal(r.nextKey,'Isha');assert.equal(r.nextDate,'08-09-0001');assert.equal(r.timetableDate,'07-09-0001');
  assert.equal(r.nextEpoch,Date.parse('0001-09-08T00:31:00Z'));assert.equal(r.leftMin,91);
});

function assertUnavailable(c,state){
  c.run('render()');const m=c.run('model()'),receipt=c.run('_lastRender');
  assert(m,'current timetable remains usable');assert.equal(m.selection.state,state);
  assert.equal(m.nextKey,null);assert.equal(m.nextTime,null);assert(Number.isNaN(m.nextEpoch));
  assert.equal(c.dom.querySelector('.nt').textContent,'—');
  assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  assert.equal(receipt.nextKey,null);assert.equal(receipt.selectionState,state);
  const rows=c.dom.querySelector('.times').innerHTML;
  assert.equal((rows.match(/data-prayer-key=/g)||[]).length,6);assert.doesNotMatch(rows,/class="p on\b/);
  assert.doesNotMatch(rows,/NaN|Infinity|undefined/);assert.match(c.dom.querySelector('#ce').textContent,/2026/);
  assert(Number.isFinite(m.progress));
}

test('ES07-05/12 missing, rejected, foreign-zone and wrong-day successors never guess a next target',()=>{
  for(const kind of ['missing','bad-clock','wrong-day','wrong-zone']){
    const c=admittedScene({next:false,clocks:{Isha:'00:30'}});
    if(kind!=='missing'){
      c.context.rejected=prayerRecord(kind==='wrong-day'?'2026-09-09':'2026-09-08',kind==='wrong-zone'?'America/New_York':'UTC',kind==='bad-clock'?{Isha:'24:00'}:{Isha:'00:31'});
      assert.equal(c.run('adoptPrayerBundle(rejected,"08-09-2026",null,false,false)'),false,kind);
    }
    assertUnavailable(c,'next-day-required');
  }
});

for(const [name,now,key,current,left] of [
  ['same day','2026-09-07T12:30:00Z','Asr','Dhuhr',180],
  ['strict exact event','2026-09-07T15:30:00Z','Maghrib','Asr',150],
  ['Sunrise instant','2026-09-07T06:00:00Z','Dhuhr','Sunrise',360],
  ['Forenoon boundary','2026-09-07T06:20:00Z','Dhuhr','Forenoon',340]
])test('ES07-03 '+name+' preserves ordinary rendered labels',()=>{
  const c=admittedScene({now,next:false});c.run('render()');const m=c.run('model()');
  assert.equal(m.selection.state,'same-day-target');assert.equal(m.nextKey,key);assert.equal(m.currentKey,current);assert.equal(m.leftMin,left);
  assert.equal(c.dom.querySelector('.cn').textContent,current);assert.match(c.dom.querySelector('.left').innerHTML,new RegExp('until-prayer">'+key+'<'));
});

test('ES07-11/13 reordered target supplies one date/zone/interval/marker and completed-render receipt',()=>{
  const c=admittedScene({clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}}),m=c.run('model()');
  assert.equal(m.selection.state,'next-day-target');assert.equal(m.selection.target.sourceRecord,c.context.nextInput);
  assert.equal(m.selection.target.generation,0);assert.equal(m.selection.target.zone,'UTC');
  assert.equal(m.nextMin,1471);assert.equal(m.prevMin,1080);assert.equal(m.progress,300/391);
  assert.equal(m.dots.find(x=>x.k==='Isha').abs,31);assert.equal(m.dots.find(x=>x.k==='Fajr').abs,300);
  assert.throws(()=>c.run('"use strict"; model().selection.target.key="Fajr"'),/read only|readonly|Cannot assign/i);
  c.run('render()');const receipt=c.run('_lastRender');
  assert.equal(receipt.nextZone,'UTC');assert.equal(receipt.nextKey,'Isha');assert.equal(receipt.selectionState,m.selection.state);
  assert.equal(receipt.prevMin,1080);assert.equal(receipt.nextMin,1471);assert.equal(receipt.progressKind,'wall-interval');
});

test('ES07-13 supported before-first target retains decorative wall progress without invented previous history',()=>{
  const c=admittedScene({now:'2026-09-07T01:30:00Z',next:false}),m=c.run('model()');
  assert.equal(m.nextKey,'Fajr');assert.equal(m.progress,360/570);assert.equal(m.prevMin,-270);assert.equal(m.nextMin,300);
  assert.equal(m.progressKind,'decorative-before-first');assert.equal(m.previousEpoch,null);assert.equal(m.previousDateStr,null);
});

for(const [name,now,clock,nextDate,wantEpoch,wantLeft,wantState] of [
  ['future tie','2026-09-07T01:30:00Z','05:00','2026-09-08','2026-09-07T05:00:00Z',210,'same-day-target'],
  ['exact tie','2026-09-07T05:00:00Z','05:00','2026-09-08','2026-09-08T05:00:00Z',1440,'next-day-target'],
  ['midnight polar tie','2026-09-07T23:00:00Z','00:00','2026-09-08','2026-09-08T00:00:00Z',60,'next-day-target']
])test('ES07-04 '+name+' stays admitted with deterministic rank and finite progress',()=>{
  const clocks=Object.fromEntries(['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Sunset','Isha'].map(k=>[k,clock]));
  const c=admittedScene({now,clocks,nextDate}),m=c.run('model()');c.run('render()');
  assert.equal(m.nextKey,'Fajr');assert.equal(m.currentKey,'Isha');assert.equal(m.nextEpoch,Date.parse(wantEpoch));assert.equal(m.leftMin,wantLeft);
  assert.equal(m.selection.state,wantState);assert(Number.isFinite(m.progress));assert(m.progress>=0&&m.progress<=1);
});

for(const [name,now,clocks,key,epoch,left] of [
  ['gap later than healthy winner','2026-03-08T01:00:00-05:00',{Fajr:'01:30',Sunrise:'02:30'},'Fajr','2026-03-08T06:30:00Z',30],
  ['gap already elapsed','2026-03-08T03:30:00-04:00',{Fajr:'02:30'},'Sunrise','2026-03-08T10:00:00Z',150],
  ['fold later than healthy winner','2026-11-01T00:15:00-04:00',{Fajr:'00:30',Sunrise:'01:30'},'Fajr','2026-11-01T04:30:00Z',15],
  ['fold all alternatives elapsed','2026-11-01T01:40:00-05:00',{Fajr:'01:30'},'Sunrise','2026-11-01T11:00:00Z',260]
])test('ES07-08 '+name+' does not blanket-disable a supported target',()=>{
  const c=admittedScene({now,zone:'America/New_York',date:now.slice(0,10),clocks,next:false}),m=c.run('model()');c.run('render()');
  assert.equal(m.nextKey,key);assert.equal(m.nextEpoch,Date.parse(epoch));assert.equal(m.leftMin,left);
  assert.notEqual(c.dom.querySelector('.left').textContent,'Countdown unavailable');
});
for(const [name,now,date,clocks] of [
  ['potentially earlier gap','2026-03-08T01:45:00-05:00','2026-03-08',{Fajr:'02:30'}],
  ['fold wall past but second epoch future','2026-11-01T01:40:00-04:00','2026-11-01',{Fajr:'01:30'}]
])test('ES07-08 '+name+' blocks false next precision',()=>{
  assertUnavailable(admittedScene({now,zone:'America/New_York',date,clocks,next:false}),'endpoint-unresolved');
});

for(const fixture of [
  {name:'elapsed start-of-day gap',zone:'America/Santiago',date:'2026-09-06',now:'2026-09-06T05:00:00Z',clocks:{Fajr:'00:30'},gapKey:'Fajr',key:'Sunrise',clock:'06:00',epoch:'2026-09-06T09:00:00Z',left:240,lower:-Infinity,upper:Date.parse('2026-09-06T04:00:00Z')},
  {name:'later end-of-day gap',zone:'America/Nuuk',date:'2026-03-28',now:'2026-03-29T00:00:00Z',clocks:{Fajr:'22:30',Isha:'23:30'},gapKey:'Isha',key:'Fajr',clock:'22:30',epoch:'2026-03-29T00:30:00Z',left:30,lower:Date.parse('2026-03-29T00:59:00Z'),upper:Infinity}
])test('review SRC-01 '+fixture.name+' retains its known ordering bound without inventing an endpoint',()=>{
  const c=admittedScene({...fixture,next:false}),m=c.run('model()');
  assert.equal(m.selection.state,'same-day-target');assert.equal(m.nextKey,fixture.key);
  assert.equal(m.nextEpoch,Date.parse(fixture.epoch));assert.equal(m.leftMin,fixture.left);
  const gap=m.selection.currentCandidates.find(candidate=>candidate.key===fixture.gapKey);
  assert.equal(gap.unavailableReason,'gap');assert(Number.isNaN(gap.epoch));
  assert.equal(gap.lowerEpoch,fixture.lower);assert.equal(gap.upperEpoch,fixture.upper);
  c.run('render()');const r=c.run('_lastRender');assert.equal(r.nextKey,fixture.key);assert.equal(r.nextEpoch,Date.parse(fixture.epoch));
  assert.equal(c.dom.querySelector('.nt').textContent,fixture.clock);
  assert.match(c.dom.querySelector('.left').innerHTML,new RegExp('until-prayer">'+fixture.key+'<'));
});

for(const fixture of [
  {zone:'America/Santiago',date:'2026-09-06',now:'2026-09-06T05:00:00Z',clocks:{},epoch:'2026-09-06T08:00:00Z',left:180},
  {zone:'America/Nuuk',date:'2026-03-28',now:'2026-03-29T00:00:00Z',clocks:{Fajr:'22:30',Isha:'22:50'},epoch:'2026-03-29T00:30:00Z',left:30}
])test('review SRC-01 ordinary companion in '+fixture.zone+' preserves its supported Fajr target',()=>{
  const c=admittedScene({...fixture,next:false});c.run('render()');const r=c.run('_lastRender');
  assert.equal(r.nextKey,'Fajr');assert.equal(r.nextEpoch,Date.parse(fixture.epoch));assert.equal(r.leftMin,fixture.left);
});

test('ES07-08 unsupported inverse profile cannot skip uncertain candidates',()=>{
  const {countedIntl}=require('./r0008-clock-harness.cjs'),{intl}=countedIntl(30000);
  const c=loadRender(modelRealm({intl,wall:Date.parse('2026-09-07T01:30:00Z'),globals:{today:null,tomorrow:null}}));
  c.context.input=prayerRecord('2026-09-07','UTC');
  assert.equal(c.run('adoptPrayerBundle(input,"07-09-2026",null,true,false)'),true);
  assertUnavailable(c,'endpoint-unresolved');
});

for(const [date,nextDate,epoch] of [
  ['2026-09-30','2026-10-01','2026-10-01T00:31:00Z'],
  ['2026-12-31','2027-01-01','2027-01-01T00:31:00Z'],
  ['2024-02-28','2024-02-29','2024-02-29T00:31:00Z'],
  ['2024-02-29','2024-03-01','2024-03-01T00:31:00Z']
])test('ES07-09 reordered target uses actual successor '+nextDate,()=>{
  const c=admittedScene({now:date+'T23:00:00Z',date,nextDate,clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}});c.run('render()');
  const r=c.run('_lastRender');assert.equal(r.nextKey,'Isha');assert.equal(r.nextEpoch,Date.parse(epoch));assert.equal(r.leftMin,91);
  assert.equal(r.nextDate,nextDate.split('-').reverse().join('-'));
});

test('ES07-11 diagnostics retain the rendered model instant when wall time moves during the consumer',()=>{
  const c=admittedScene({clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}});
  c.clock.reads=0;c.run('model()');assert.equal(c.clock.reads,1);
  c.context.advanceAfterSelection=()=>{c.clock.wall+=60000;};
  c.run('const receiptModel=model;model=function(){const chosen=receiptModel();advanceAfterSelection();return chosen;};render()');
  const r=c.run('_lastRender');assert.equal(r.acceptedUtcMs,Date.parse('2026-09-07T23:00:00Z'));assert.equal(r.sim,'07-09-2026 23:00');assert.equal(r.leftMin,91);
});

function frozenScene(format24=true){
  const {loadLifecycle}=require('./r0008-clock-harness.cjs');
  const c=loadLifecycle(loadRender(modelRealm({query:'simTime=23:00',zone:'UTC',wall:Date.parse('2026-09-07T23:00:00Z'),globals:{today:null,tomorrow:null,fmt24:format24}})),undefined,{autoTimings:false});
  c.context.input=prayerRecord('2026-09-07','UTC',{Isha:'00:30'});assert.equal(c.run('adoptPrayerBundle(input,"07-09-2026",null,true,false)'),true);
  c.run('startRenderLoop()');c.frame();assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  assert.equal(c.prayerTransport.requests.length,1);assert.equal(c.prayerTransport.requests[0].day,'08-09-2026');return c;
}
for(const format24 of [true,false])test('ES07-06 actual frozen next-day arrival restores reordered target on first dirty frame '+(format24?'24h':'12h'),async()=>{
  const c=frozenScene(format24),now=c.run('simNow()');assert.equal(c.run('_renderDirty'),false);
  c.prayerTransport.requests[0].resolve(prayerRecord('2026-09-08','UTC',{Isha:'00:31'}));await c.prayerTransport.settle();
  assert.equal(c.run('_renderDirty'),true);c.frame();
  const r=c.run('_lastRender');assert.equal(r.nextKey,'Isha');assert.equal(r.nextEpoch,Date.parse('2026-09-08T00:31:00Z'));assert.equal(r.leftMin,91);
  assert.equal(r.acceptedUtcMs,now);assert.equal(c.run('simNow()'),now);assert.equal(c.dom.querySelector('.nt').textContent,format24?'00:31':'12:31 AM');
});

test('ES07-10 A to B to A rejects old held current and next replies before frozen selected target',async()=>{
  const c=frozenScene(),oldNext=c.prayerTransport.requests[0];
  const b=c.run('applyConfig({lat:25,lon:40,tz:"UTC"})'),bCurrent=c.prayerTransport.requests[1];
  const a=c.run('applyConfig({lat:24,lon:39,tz:"UTC"})'),aCurrent=c.prayerTransport.requests[2];
  assert.equal(c.run('_runtimeGeneration'),2);assert.equal(oldNext.init.signal.aborted,true);assert.equal(bCurrent.init.signal.aborted,true);
  oldNext.resolve(prayerRecord('2026-09-08','UTC',{Isha:'00:10'}));bCurrent.resolve(prayerRecord('2026-09-07','UTC',{Isha:'00:12'}));await c.prayerTransport.settle();
  assert.equal(c.context.today,null);assert.equal(c.context.tomorrow,null);
  aCurrent.resolve(prayerRecord('2026-09-07','UTC',{Isha:'00:30'}));await Promise.all([a,b]);c.frame();
  const currentNext=c.prayerTransport.requests[3];assert.equal(currentNext.day,'08-09-2026');
  currentNext.resolve(prayerRecord('2026-09-08','UTC',{Isha:'00:31'}));await c.prayerTransport.settle();c.frame();
  const r=c.run('_lastRender');assert.equal(r.generation,2);assert.equal(r.nextKey,'Isha');assert.equal(r.leftMin,91);assert.equal(r.nextZone,'UTC');
});

// Use the same uniquely anchored production mutation as the native companion.
// Every negative reaches the intended real consumer; bootstrap failure is not a kill.
function mutatedOwner(variant,start,end){
  const {source,slice,sha256}=require('./r0008-clock-harness.cjs');
  const altered=require('./rlgwo/prayer-browser-fixture.cjs').instrument(source,{variant});
  console.log('MUTANT '+variant+' '+sha256(altered));return slice(start,end,altered);
}
function renderMutatedModel(c,variant){c.run(mutatedOwner(variant,'// build everything render() needs','// draw the solar-prayer arc'));c.run('render()');return c.run('_lastRender');}
for(const variant of ['hardcoded-fajr','name-order'])test('ES07 mutation '+variant+' fails reordered consumer while ordinary target survives',()=>{
  const bad=renderMutatedModel(admittedScene({clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}}),variant);
  assert.equal(bad.nextKey,'Fajr');assert.equal(bad.leftMin,360);assert.throws(()=>assert.equal(bad.nextKey,'Isha'));
  const healthy=renderMutatedModel(admittedScene(),variant);assert.equal(healthy.nextKey,'Fajr');assert.equal(healthy.leftMin,360);
});
test('ES07 mutation lost-date is caught by actual next-date consumer with healthy same-day companion',()=>{
  const bad=renderMutatedModel(admittedScene({clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}}),'lost-date');
  assert.equal(bad.nextKey,null);assert.throws(()=>assert.equal(bad.nextEpoch,Date.parse('2026-09-08T00:31:00Z')));
  const healthy=renderMutatedModel(admittedScene({now:'2026-09-07T12:30:00Z',next:false}),'lost-date');assert.equal(healthy.nextKey,'Asr');assert.equal(healthy.leftMin,180);
});
test('ES07 mutation ambiguous-epoch cannot invent precision from the first fold alternative',()=>{
  const bad=renderMutatedModel(admittedScene({now:'2026-11-01T00:30:00-04:00',zone:'America/New_York',date:'2026-11-01',next:false,clocks:{Fajr:'01:30'}}),'ambiguous-epoch');
  assert.equal(bad.nextEpoch,Date.parse('2026-11-01T05:30:00Z'));assert.equal(bad.leftMin,60);
  assert.throws(()=>assert.equal(bad.selectionState,'endpoint-unresolved'));
  const healthy=renderMutatedModel(admittedScene(),'ambiguous-epoch');assert.equal(healthy.leftMin,360);
});
test('ES07 mutation independent-label is caught despite a correct selected epoch and countdown',()=>{
  const c=admittedScene({clocks:{Isha:'00:30'},nextClocks:{Isha:'00:31'}});
  c.run(mutatedOwner('independent-label','function render(){','function updateSimClock'));c.run('render()');
  const r=c.run('_lastRender');assert.equal(r.nextKey,'Isha');assert.equal(r.leftMin,91);
  assert.match(c.dom.querySelector('.left').innerHTML,/until-prayer">Fajr</);
  assert.throws(()=>assert.match(c.dom.querySelector('.left').innerHTML,/until-prayer">Isha</));
});
test('ES07 mutation remove-next-dirty is caught after genuine adoption on a frozen existing-loop source control',async()=>{
  const c=frozenScene();c.run(mutatedOwner('remove-next-dirty','function adoptPrayerBundle(','function prefetchPrayerDay'));
  c.prayerTransport.requests[0].resolve(prayerRecord('2026-09-08','UTC',{Isha:'00:31'}));await c.prayerTransport.settle();
  assert.equal(c.run('model().leftMin'),91,'accepted data is actually present');assert.equal(c.run('_renderDirty'),false);
  c.frame();assert.equal(c.dom.querySelector('.left').textContent,'Countdown unavailable');
  assert.throws(()=>assert.equal(c.run('_lastRender.nextKey'),'Isha'));
});

test('single adoption-hook mutation survives because actual prefetch finalization also wakes the frozen frame',async()=>{
  const c=frozenScene();c.run(mutatedOwner('remove-adoption-dirty-only','function adoptPrayerBundle(','function beginPrayerRequest'));
  c.prayerTransport.requests[0].resolve(prayerRecord('2026-09-08','UTC',{Isha:'00:31'}));await c.prayerTransport.settle();
  assert.equal(c.run('_renderDirty'),true);c.frame();assert.equal(c.run('_lastRender.nextKey'),'Isha');assert.equal(c.run('_lastRender.leftMin'),91);
});
