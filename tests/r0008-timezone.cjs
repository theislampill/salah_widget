'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const {test} = require('node:test');
const {realm, countedIntl, sha256, source, temporal, modelRealm, loadRender, loadLifecycle, loadSettingsAffordance, prayerRecord} = require('./r0008-clock-harness.cjs');
console.log(`SOURCE ${sha256(source)} TEMPORAL ${sha256(temporal)}`);

const r = realm({zone: 'America/New_York'});
const convert = (parts, zone = 'America/New_York') => r.run(`epochForTzTime(${parts.join(',')},${JSON.stringify(zone)})`);
for (const [name, parts, zone, expected] of [
  ['valid spring post-transition 03:30', [2026,3,8,3,30], 'America/New_York', '2026-03-08T07:30:00Z'],
  ['pre-transition positive control', [2026,3,8,1,30], 'America/New_York', '2026-03-08T06:30:00Z'],
  ['ordinary positive control', [2026,9,7,3,30], 'America/New_York', '2026-09-07T07:30:00Z'],
  ['post-fold valid control', [2026,11,1,3,30], 'America/New_York', '2026-11-01T08:30:00Z'],
  ['fractional offset and previous UTC date', [2026,9,7,3,30], 'Asia/Kathmandu', '2026-09-06T21:45:00Z'],
  ['leap day', [2024,2,29,0,0], 'UTC', '2024-02-29T00:00:00Z'],
  ['year one does not become 1901', [1,1,1,0,0], 'UTC', '0001-01-01T00:00:00Z'],
  ['year 99 does not become 1999', [99,12,31,23,59], 'UTC', '0099-12-31T23:59:00Z']
]) test(name, () => assert.equal(convert(parts, zone), Date.parse(expected)));

for (const [name, parts, zone] of [
  ['spring gap', [2026,3,8,2,30], 'America/New_York'],
  ['fall fold', [2026,11,1,1,30], 'America/New_York'],
  ['invalid Gregorian date', [2026,2,30,0,0], 'UTC'],
  ['invalid IANA zone', [2026,9,7,3,30], 'Invalid/Zone'],
  ['nonfinite year', ['NaN',9,7,3,30], 'UTC'],
  ['fractional fields', [2026,9,7,3,30.5], 'UTC'],
  ['hour 24', [2026,9,7,24,0], 'UTC'],
  ['minute 60', [2026,9,7,3,60], 'UTC'],
  ['nonpositive year', [0,9,7,3,30], 'UTC']
]) test(name + ' fails closed', () => assert(Number.isNaN(convert(parts, zone))));

for (const [name, offset] of [['synthetic 30-second offset', 30000], ['synthetic >24-hour offset', 25*3600000]]) {
  test(name + ' rejects and caches the unsupported profile', () => {
    const {intl, counts} = countedIntl(offset), c = realm({intl});
    assert(Number.isNaN(c.run('epochForTzTime(2026,9,7,3,30,"UTC")')));
    const first = counts.projections;
    assert(Number.isNaN(c.run('epochForTzTime(2026,9,7,4,30,"UTC")')));
    assert.equal(counts.projections, first);
  });
}

test('same-day callers reuse the bounded exhaustive profile and fifth day evicts', () => {
  const {intl, counts} = countedIntl(), c = realm({intl});
  assert.equal(c.run('epochForTzTime(2026,9,7,0,0,"UTC")'), Date.parse('2026-09-07T00:00Z'));
  assert.equal(counts.projections, 4322);
  const first = counts.projections;
  for (let h=1; h<24; h++) c.run(`epochForTzTime(2026,9,7,${h},0,"UTC")`);
  assert.equal(counts.projections - first, 23);
  for (let d=8; d<=11; d++) c.run(`epochForTzTime(2026,9,${d},0,0,"UTC")`);
  const before = counts.projections;
  c.run('epochForTzTime(2026,9,7,0,0,"UTC")');
  assert.equal(counts.projections - before, 4322);
});

test('invalid explicit simulation rejects its anchor; changing to a valid zone recovers', () => {
  const c = realm({query: 'simTime=02:30', zone: 'America/New_York', wall: Date.parse('2026-03-08T12:00Z')});
  assert(Number.isNaN(c.run('simNow()')));
  c.run('tz="UTC"');
  assert.equal(c.run('simNow()'), Date.parse('2026-03-08T02:30Z'));
  c.run('tz="America/New_York"');
  assert(Number.isNaN(c.run('simNow()')));
});

test('legacy valid hour/minute parsing and frozen/accelerated explicit modes survive', () => {
  const c = realm({query: 'simTime=27:30', zone: 'UTC'});
  assert.equal(c.run('simNow()'), Date.parse('2026-09-07T03:30Z'));
  c.clock.mono=60000; c.clock.wall+=3600000;
  assert.equal(c.run('simNow()'), Date.parse('2026-09-07T03:30Z'));
  const a = realm({query: 'simTime=03:30&timeScale=60', zone: 'UTC'});
  a.run('simNow()'); a.clock.mono=1000;
  assert.equal(a.run('simNow()'), Date.parse('2026-09-07T03:31Z'));
});

test('actual boot rejects an invalid scene before stars/moon/day acquisition', async () => {
  const c=loadLifecycle(loadRender(modelRealm({query:'simTime=02:30',zone:'America/New_York',wall:Date.parse('2026-03-08T12:00Z')})));
  await c.run('boot()');
  assert.equal(c.calls.stars,0); assert.equal(c.calls.moon,0); assert.equal(c.calls.requests.length,0);
  assert.equal(c.dom.querySelector('.nt').textContent,'—');
  assert.equal(c.dom.querySelector('.left').textContent,'Simulation time unavailable');
  assert.equal(c.dom.querySelector('.simclock').textContent,'SIM unavailable');
  assert.equal(c.dom.querySelector('.simclock').style.display,'block');
});

test('actual render/apply/loop invalidate a prior scene and restore valid configuration visibility', async () => {
  const c=loadLifecycle(loadRender(modelRealm({query:'simTime=02:30',zone:'UTC',wall:Date.parse('2026-03-08T12:00Z'),
    globals:{today:prayerRecord('2026-03-08','UTC')}})));
  c.run('render()'); c.run('startRenderLoop()'); c.frame();
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  c.dom.querySelector('.climate').style.visibility='hidden';
  const oldMoon=c.calls.moon, oldCloud=c.calls.cloud;
  c.run('tz="America/New_York"'); c.run('render()'); c.frame();
  assert.equal(c.calls.moon,oldMoon); assert.equal(c.calls.cloud,oldCloud);
  for(const selector of ['.sky','#wxfx','.arc','.times','.d']) assert.equal(c.dom.querySelector(selector).style.visibility,'hidden');
  assert.equal(c.dom.querySelector('.left').textContent,'Simulation time unavailable');
  assert.notEqual(c.dom.querySelector('.h').style.visibility,'hidden');
  assert.notEqual(c.dom.querySelector('.settings').style.visibility,'hidden');
  await c.run('applyConfig({lat:24,lon:39,tz:"UTC"})'); c.frame();
  assert.equal(c.dom.querySelector('.sky').style.visibility,undefined);
  assert.equal(c.dom.querySelector('.climate').style.visibility,'hidden','preexisting visibility is restored');
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert.equal(c.dom.querySelector('.simclock').style.display,undefined);
  const requests=c.calls.requests.length;
  await c.run('applyConfig({lat:24,lon:39,tz:"America/New_York"})');
  assert.equal(c.calls.requests.length,requests);
  assert.equal(c.dom.querySelector('.left').textContent,'Simulation time unavailable');
});

test('all actual inline widget scripts parse', () => {
  const scripts=Array.from(source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g),match=>match[1]).filter(text=>text.trim());
  assert(scripts.length); for(const text of scripts) assert.doesNotThrow(()=>new vm.Script(text));
});

test('single-offset mutant preserves ordinary control and fails the exact spring oracle', () => {
  const a=temporal.indexOf('function epochForTzTime('), b=temporal.indexOf('function initSim()',a);
  assert(a>=0 && b>a);
  const block=temporal.slice(0,a)+'function epochForTzTime(y,mo,d,h,mi){ const guess=Date.UTC(y,mo-1,d,h,mi,0); const p=partsInTz(guess); return guess-(Date.UTC(p.y,p.mo-1,p.d,p.h,p.mi,p.s)-guess); }\n'+temporal.slice(b);
  const c=realm({block,zone:'America/New_York'});
  assert.equal(c.run('epochForTzTime(2026,9,7,3,30)'),Date.parse('2026-09-07T07:30Z'));
  assert.equal(c.run('epochForTzTime(2026,3,8,3,30)'),Date.parse('2026-03-08T08:30Z'));
  assert.notEqual(c.run('epochForTzTime(2026,3,8,3,30)'),Date.parse('2026-03-08T07:30Z'));
  console.log(`MUTANT single-offset ${sha256(block)} rejected spring oracle; ordinary control retained`);
});

test('first-fold-candidate and ignored-explicit-zone mutants are discriminated', () => {
  const fold=temporal.replace('entry.length!==1','entry.length===0'); assert.notEqual(fold,temporal);
  assert(Number.isFinite(realm({block:fold}).run('epochForTzTime(2026,11,1,1,30,"America/New_York")')));
  const ignored=temporal.replace('function epochForTzTime(y,mo,d,h,mi,zone=tz){','function epochForTzTime(y,mo,d,h,mi,zone=tz){ zone=tz;'); assert.notEqual(ignored,temporal);
  const c=realm({block:ignored,zone:'Asia/Riyadh'});
  assert.equal(c.run('epochForTzTime(2026,3,8,3,30,"America/New_York")'),Date.parse('2026-03-08T00:30Z'));
  assert.notEqual(c.run('epochForTzTime(2026,3,8,3,30,"America/New_York")'),Date.parse('2026-03-08T07:30Z'));
  console.log(`MUTANT first-fold ${sha256(fold)} / ignored-zone ${sha256(ignored)} rejected`);
});

test('bypassing simulation validity is caught by the actual boot caller', async () => {
  const block=temporal.replace('const valid=SIM.time==null || Number.isFinite(simNow()),','const valid=true,'); assert.notEqual(block,temporal);
  const c=loadLifecycle(loadRender(modelRealm({block,query:'simTime=02:30',zone:'America/New_York',wall:Date.parse('2026-03-08T12:00Z')})));
  const boot=c.run('boot()'); assert(c.calls.stars>0);
  // A deliberately unguarded NaN scene has no civil request day. Cancel its real loader through
  // the accepted ownership boundary rather than letting invalid transport retries hold this mutant.
  c.run('beginRuntimeGeneration()'); await boot;
  assert.notEqual(c.dom.querySelector('.left').textContent,'Simulation time unavailable');
  console.log(`MUTANT invalid-scene-bypass ${sha256(block)} rejected by boot boundary`);
});

for(const mode of ['local','preferLocal']) for(const zone of ['UTC','America/New_York']) {
  test(`${mode} ${zone} boot keeps actual settings button reachable before scene validity`, async () => {
    const c=loadSettingsAffordance(loadLifecycle(loadRender(modelRealm({query:'simTime=02:30',zone,wall:Date.parse('2026-03-08T12:00Z')}))));
    c.context._cfgMode=mode;
    await c.run('boot()');
    const buckle=c.dom.querySelector('.buckle');
    assert.equal(buckle.getAttribute('role'),'button'); assert.equal(buckle.getAttribute('tabindex'),'0');
    assert.equal(buckle.getAttribute('aria-label'),'Widget settings');
    assert(buckle.events.has('click')); assert(buckle.events.has('keydown'));
    assert.notEqual(buckle.style.visibility,'hidden'); assert.notEqual(c.dom.querySelector('.settings').style.visibility,'hidden');
    assert.equal(c.calls.stars,zone==='UTC'?1:0); assert.equal(c.calls.weatherBuild,zone==='UTC'?1:0);
  });
}

test('initial invalid boot then valid config initializes scene builders once across further recoveries', async () => {
  const c=loadLifecycle(loadRender(modelRealm({query:'simTime=02:30',zone:'America/New_York',wall:Date.parse('2026-03-08T12:00Z')})));
  await c.run('boot()'); assert.equal(c.calls.stars,0); assert.equal(c.calls.weatherBuild,0);
  await c.run('applyConfig({lat:24,lon:39,tz:"UTC"})'); c.frame();
  assert.equal(c.calls.stars,1); assert.equal(c.calls.weatherBuild,1);
  assert.equal(c.run('Number.isFinite(simNow())'),true); assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  await c.run('applyConfig({lat:24,lon:39,tz:"UTC"})'); await c.run('applyConfig({lat:24,lon:39,tz:"America/New_York"})');
  assert.equal(c.dom.querySelector('.left').textContent,'Simulation time unavailable');
  await c.run('applyConfig({lat:24,lon:39,tz:"UTC"})'); c.frame();
  assert.equal(c.calls.stars,1); assert.equal(c.calls.weatherBuild,1); assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
});

test('valid boot and subsequent config reuse builders; bare embeds keep existing settings behavior', async () => {
  const c=loadSettingsAffordance(loadLifecycle(loadRender(modelRealm({query:'simTime=02:30',zone:'UTC',wall:Date.parse('2026-03-08T12:00Z')}))));
  c.context._cfgMode='bare'; await c.run('boot()');
  assert.equal(c.dom.querySelector('.buckle').getAttribute('role'),null);
  assert.equal(c.calls.stars,1); assert.equal(c.calls.weatherBuild,1);
  await c.run('applyConfig({lat:24,lon:39,tz:"UTC"})'); c.frame(); await c.run('boot()');
  assert.equal(c.calls.stars,1); assert.equal(c.calls.weatherBuild,1);
});

test('actual failed save discloses session-only state before acquisition and a successful retry clears it',
  {skip:!source.includes('_publishPersistence("save",r)')}, async()=>{
  const c=loadSettingsAffordance(loadLifecycle(loadRender(modelRealm({query:'simTime=02:30',zone:'UTC',
    wall:Date.parse('2026-03-08T12:00Z')})),undefined,{autoTimings:false}));
  c.run('enableSettingsAffordance()');
  const buckle=c.dom.querySelector('.buckle'), storage=c.context.localStorage;
  assert.equal(c.dom.getElementById('settings-persistence-status'),c.dom.querySelector('#settings-persistence-status'));
  const setItem=storage.setItem, blocked=Object.assign(new Error('fixture denied'),{name:'SecurityError'});
  storage.setItem=()=>{throw blocked;};
  const applying=c.run('applyConfig({lat:24,lon:39,tz:"UTC",source:"manual"},{save:true})');
  assert.equal(c.run('_persistOutcome.status'),'session-only'); assert.equal(c.run('_storageErr'),'SecurityError');
  assert.equal(c.dom.querySelector('#settings-persistence-status').textContent,
    'Changes apply for this session only. Could not save settings (SecurityError).');
  assert(c.dom.querySelector('#set-status').classList.contains('err'));
  assert(buckle.classList.contains('persist-warning'));
  assert.equal(buckle.getAttribute('aria-label'),'Widget settings — changes not saved; session only');
  assert.equal(buckle.querySelector('.gear').textContent,'!');
  assert.equal(c.run('CONFIG.source'),'manual'); assert.equal(c.run('CONFIG.savedAt'),null);
  assert.equal(c.run('SalahConfig.loadLocal()'),null);
  assert.equal(c.prayerTransport.requests.length,1); assert.equal(c.context.today,null);
  assert.equal(c.run('_runtimeGeneration'),1,'failed persistence still applies the session configuration');
  c.prayerTransport.requests[0].resolve(); await applying; c.frame();
  assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert.equal(c.run('model().nextEpoch'),Date.parse('2026-03-08T05:00Z'));
  assert.equal(c.run('model().leftMin'),150);
  assert.equal((c.dom.querySelector('.times').innerHTML.match(/class="p /g)||[]).length,6);
  assert(buckle.classList.contains('persist-warning'),'successful prayer acquisition is not a successful settings save');

  storage.setItem=setItem;
  const retry=c.run('applyConfig({lat:24,lon:39,tz:"UTC",source:"manual"},{save:true})');
  assert.equal(c.run('_persistOutcome.status'),'saved'); assert.equal(c.run('_storageErr'),null);
  assert.equal(c.dom.querySelector('#settings-persistence-status').textContent,'Settings saved in this browser.');
  assert.equal(c.dom.querySelector('#set-status').classList.contains('err'),false);
  assert.equal(buckle.classList.contains('persist-warning'),false);
  assert.equal(buckle.getAttribute('aria-label'),'Widget settings'); assert.equal(buckle.querySelector('.gear').textContent,'⚙');
  assert.equal(c.run('CONFIG.source'),'localStorage'); assert.equal(c.run('CONFIG.origin'),'manual');
  assert.equal(c.run('CONFIG.savedAt'),c.clock.wall);
  assert.equal(c.run('SalahConfig.loadLocal().savedAt'),c.clock.wall);
  const pending=c.prayerTransport.requests.at(-1); assert.equal(pending.day,'08-03-2026'); assert.equal(pending.zone,'UTC');
  pending.resolve(); await retry; c.frame();
  assert.equal(c.run('_runtimeGeneration'),2); assert.equal(c.dom.querySelector('.nt').textContent,'05:00');
  assert.equal(c.run('model().leftMin'),150);
});
