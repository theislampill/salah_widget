'use strict';
// R0031 / issue #98 source controls: builder reverse-geocode admission (PRA-F-05), local-mode suppression
// (D-31-1 A), the Nominatim jsonv2 place-kind field (PRA-F-30, D-31-4 A) and the settings GPS / permission
// discriminator (PRA-F-29, D-31-3 pending: a todo witness, not an acceptance). The actual generated builder.html,
// config.js and index.html settings slice run in a Node vm (tests/r000f-fixture.cjs) with controlled timers,
// provider doubles and geolocation; no request leaves the process and no real position is read. Not native evidence.
// R0031_REF=<commit> runs the same scenarios against that commit's generated files (the RED witness).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { fixture: sourceFixture, readSource } = require('./r000f-fixture.cjs');
const L = require('./location-admission-fixture.cjs');

const ref = process.env.R0031_REF || undefined;
// R0031_MUTANT=<name> applies one disposable in-memory mutant (builder-reverse-admission-mutations.test.cjs).
const MUTANTS = {
  'drop-ok': ['builder', 'if(!r || r.ok!==true) throw new Error("http"); ', ''],
  'else-4': ['builder', 'if(methodAuto && a.continent) $("method").value = (a.continent==="NA") ? "2" : "4";', 'if(methodAuto) $("method").value = (j && j.continentCode==="NA") ? "2" : "4";'],
  'no-deadline': ['builder', 'await Promise.race([work,deadline])', 'await work'],
  'local-request': ['builder', 'if(embedMode==="local") return;                  // D-31-1 A', '// mutant'],
  'mode-epoch': ['builder', 'epoch!==reverseModeEpoch || embedMode==="local"', 'false'],
  'epoch-compare': ['builder', 'epoch!==reverseModeEpoch || ', ''],
  'epoch-bump': ['builder', 'if(nextMode!==embedMode) reverseModeEpoch++;', ''],
  'loose-continent': ['builder', '/^[A-Z]{2}$/.test(j.continentCode)', '/^[A-Za-z ]{2,3}$/.test(j.continentCode)'],
  'class-only': ['config', 'return r.class !== undefined ? r.class : r.category;', 'return r.class;'],
};
const mutant = process.env.R0031_MUTANT ? MUTANTS[process.env.R0031_MUTANT] : null;
if (process.env.R0031_MUTANT && !mutant) throw new Error('unknown mutant');
function mutateOf(kind) {
  if (!mutant || mutant[0] !== kind) return undefined;
  return source => { if (source.split(mutant[1]).length !== 2) throw new Error('mutant anchor missing'); return source.replace(mutant[1], () => mutant[2]); };
}
const mutateBuilder = mutateOf('builder');
const config = (mutateOf('config') || (x => x))(readSource('config.js', ref));
function builder(options = {}) { return sourceFixture('builder', { ref, mutate: mutateBuilder, ...options }); }
// Everything a reverse reply could change: form tuple, tip, pin, bias country, export code and the issued preview.
const observed = f => JSON.stringify({ snap: f.snapshot(), issued: f.run('issued && issued.identity'), hash: f.hash() });
// A North-American portable draft whose method is still automatic: coordinates edited, method ISNA "2".
async function naDraft(options) {
  const f = builder(options);
  f.input('lat', '40.7'); f.input('lon', '-74'); f.run('$("method").value="2"; update();');
  assert.equal(f.run('methodAuto'), true); await f.advance(700);
  assert.equal(f.calls.reverse.length, 1, 'one reverse request for the coordinate edit');
  return f;
}
async function replyChangesNothing(body, options) {
  const f = await naDraft(options), before = observed(f);
  await f.resolve('reverse', 0, body);
  assert.equal(observed(f), before, `reply ${JSON.stringify(body)} must not change tuple, bias, export or preview`);
  assert.equal(f.tuple()[3], '2');
  return f;
}

// ---- R31-02: no method change (and no other write) without admitted evidence --------------------------------------
for (const body of [{}, { status: 429, description: 'rate limited' }, { continentCode: ['NA'] }, null, [], 'NA', 5,
  { error: { code: 'rate-limit' }, continentCode: null }])
  test(`R31-02 reply ${JSON.stringify(body)} writes nothing (method stays 2)`, () => replyChangesNothing(body));
for (const status of [429, 500, 503, 404, 403])
  test(`R31-02 non-OK ${status} with a well-formed EU body writes nothing`, () =>
    replyChangesNothing({ city: 'London', countryCode: 'GB', continentCode: 'EU' }, { reverseResponse: { ok: false, status } }));
test('R31-02 OK-less headers (ok undefined) are not success', () =>
  replyChangesNothing({ city: 'London', countryCode: 'GB', continentCode: 'EU' }, { reverseResponse: { ok: undefined, status: 200 } }));
test('R31-02 unparsable body (json rejects) writes nothing', async () => {
  const f = await naDraft(), before = observed(f); await f.reject('reverse', 0); assert.equal(observed(f), before);
});
test('R31-02 transport failure (fetch rejects) writes nothing', async () => {
  const f = builder(); f.sandbox.fetch = () => Promise.reject(new TypeError('controlled network failure'));
  f.input('lat', '40.7'); f.input('lon', '-74'); f.run('$("method").value="2"; update();'); const before = observed(f);
  await f.advance(700); await f.advance(9000); assert.equal(observed(f), before);
});

// ---- R31-03 / R31-03a: positive controls and the shape rule ------------------------------------------------------
test('R31-03 continentCode NA → ISNA 2 from an Umm al-Qura draft; label and bias admitted', async () => {
  const f = builder(); f.input('lat', '40.7'); f.input('lon', '-74'); await f.advance(700); assert.equal(f.tuple()[3], '4');
  await f.resolve('reverse', 0, { city: 'Newark', countryCode: 'US', continentCode: 'NA' });
  assert.deepEqual(f.tuple(), ['Newark', '40.7', '-74', '2']); assert.equal(f.run('homeCC'), 'us');
  assert.equal(new URLSearchParams(f.hash()).get('method'), '2');
});
for (const code of ['EU', 'AS', 'AF', 'OC', 'SA', 'AN', 'ZZ'])
  test(`R31-03${code === 'ZZ' ? 'a' : ''} continentCode ${code} → 4`, async () => {
    const f = await naDraft(); await f.resolve('reverse', 0, { continentCode: code });
    assert.equal(f.tuple()[3], '4'); assert.equal(new URLSearchParams(f.hash()).get('method'), '4');
  });
for (const code of ['na', 'NAM', ' NA', 'NA ', '', null, ['NA'], 5, true, 'N', 'Na'])
  test(`R31-03a malformed continentCode ${JSON.stringify(code)} leaves the method`, () => replyChangesNothing({ continentCode: code }));
test('R31-03 label from the first admitted string field; non-string and blank fields are skipped', async () => {
  for (const [body, label] of [[{ city: 'Leeds' }, 'Leeds'], [{ city: 5, locality: 'Shoreditch' }, 'Shoreditch'],
    [{ city: '  ', principalSubdivision: ' England ' }, 'England'], [{ countryName: 'United Kingdom' }, 'United Kingdom']]) {
    const f = await naDraft(); await f.resolve('reverse', 0, body); assert.equal(f.tuple()[0], label, JSON.stringify(body));
    assert.equal(f.tuple()[3], '2', 'no continentCode → method unchanged');
  }
  const long = await naDraft(), before = long.tuple()[0];
  await long.resolve('reverse', 0, { city: 'x'.repeat(201) }); assert.equal(long.tuple()[0], before, 'an unbounded label is not admitted');
});
test('R31-03 countryCode GB → bias gb; invalid codes leave the bias', async () => {
  const f = await naDraft(); await f.resolve('reverse', 0, { countryCode: 'GB' }); assert.equal(f.run('homeCC'), 'gb');
  for (const cc of ['', 'GBR', ['GB'], 5, 'G1', null]) {
    const g = await naDraft(), bias = g.run('homeCC'); await g.resolve('reverse', 0, { countryCode: cc });
    assert.equal(g.run('homeCC'), bias, `countryCode ${JSON.stringify(cc)}`);
  }
});
test('R31-03 manual method and label choices still win over an admitted reply', async () => {
  const reply = { city: 'Newark', countryCode: 'US', continentCode: 'NA' };
  const m = builder(); m.input('method', '3', 'change'); m.input('lat', '40.7'); m.input('lon', '-74'); await m.advance(700);
  await m.resolve('reverse', 0, reply); assert.deepEqual([m.tuple()[0], m.tuple()[3]], ['Newark', '3']);
  const l = builder(); l.input('label', 'My place'); l.input('lat', '40.7'); l.input('lon', '-74'); await l.advance(700);
  await l.resolve('reverse', 0, reply); assert.deepEqual([l.tuple()[0], l.tuple()[3]], ['My place', '2']);
  const both = builder(); both.input('label', 'My place'); both.input('method', '3', 'change'); both.input('lat', '40.7'); both.input('lon', '-74');
  await both.advance(700); assert.equal(both.calls.reverse.length, 0, 'both automatic controls off: no request (existing)');
});

// ---- R31-04: one deadline over headers and body ---------------------------------------------------------------
test('R31-04 a body pending past 8 s settles once at the deadline; the late body is inert; abort is called', async () => {
  const f = await naDraft(), before = observed(f), signal = f.calls.reverseInit[0] && f.calls.reverseInit[0].signal;
  assert.ok(signal, 'the request carries an abort signal'); assert.equal(signal.aborted, false);
  await f.advance(7999); assert.equal(signal.aborted, false); await f.advance(1); assert.equal(signal.aborted, true);
  await f.resolve('reverse', 0, { city: 'Late', countryCode: 'GB', continentCode: 'EU' });
  assert.equal(observed(f), before);
});
test('R31-04 a body inside the deadline applies and leaves no deadline timer behind', async () => {
  const f = await naDraft(); await f.advance(7999);
  await f.resolve('reverse', 0, { continentCode: 'EU' }); assert.equal(f.tuple()[3], '4');
  assert.equal(f.calls.reverseInit[0].signal.aborted, false);
  assert.equal([...f.timers.values()].length, 0, 'deadline timer cleared');
});
test('R31-04 headers that never arrive settle at the deadline; a later rejection is handled', async () => {
  const unhandled = []; const onUnhandled = e => unhandled.push(e); process.on('unhandledRejection', onUnhandled);
  try {
    const f = builder(); let rejectLate; const inits = [];
    f.sandbox.fetch = (url, init) => { inits.push(init); return new Promise((_, reject) => { rejectLate = reject; }); };
    f.input('lat', '40.7'); f.input('lon', '-74'); f.run('$("method").value="2"; update();'); const before = observed(f);
    await f.advance(700); assert.equal(inits.length, 1); await f.advance(8000); assert.equal(inits[0].signal.aborted, true);
    rejectLate(new Error('AbortError')); await f.advance(10); await new Promise(r => setImmediate(r));
    assert.equal(observed(f), before); assert.deepEqual(unhandled, []);
  } finally { process.off('unhandledRejection', onUnhandled); }
});

// ---- R31-05: R000F ownership preserved (newer edit supersedes) --------------------------------------------------
test('R31-05 an older admitted reply after a newer coordinate edit has no effect', async () => {
  const f = await naDraft(); f.input('lat', '24.47'); f.input('lon', '39.61'); const before = observed(f);
  await f.resolve('reverse', 0, { city: 'Newark', countryCode: 'US', continentCode: 'NA' }); assert.equal(observed(f), before);
});

// ---- R31-06: self-configuring (local) mode makes no reverse request ----------------------------------------------
test('R31-06 local mode: coordinate edits and builder GPS send no reverse request; export method unchanged', async () => {
  const f = builder(); f.click('mode-local'); assert.equal(f.run('embedMode'), 'local');
  const method = new URLSearchParams(f.hash()).get('method');
  f.input('lat', '40.7'); f.input('lon', '-74'); await f.advance(700); await f.advance(5000);
  f.click('geo'); await f.resolve('gps', 0, { coords: { latitude: 51.5, longitude: -0.12 } }); await f.advance(5000);
  assert.equal(f.calls.reverse.length, 0); assert.equal(new URLSearchParams(f.hash()).get('method'), method);
  assert.equal(new URLSearchParams(f.hash()).get('local'), '1');
});
test('R31-06 switching back to portable issues no catch-up lookup; the next portable edit schedules one', async () => {
  const f = builder(); f.click('mode-local'); f.input('lat', '40.7'); f.input('lon', '-74'); await f.advance(700);
  f.click('mode-portable'); await f.advance(5000); assert.equal(f.calls.reverse.length, 0);
  f.input('lat', '40.8'); await f.advance(699); assert.equal(f.calls.reverse.length, 0); await f.advance(1); assert.equal(f.calls.reverse.length, 1);
  await f.resolve('reverse', 0, { continentCode: 'NA' }); assert.equal(f.tuple()[3], '2');
});
test('R31-06 a mode change supersedes a pending portable lookup (no write after switching to local)', async () => {
  const f = await naDraft(); f.click('mode-local'); const before = observed(f);
  await f.resolve('reverse', 0, { city: 'Lisbon', countryCode: 'PT', continentCode: 'EU' }); assert.equal(observed(f), before);
});
test('R31-06 a portable → local → portable round trip supersedes the pending lookup (mode epoch)', async () => {
  const f = await naDraft(); f.click('mode-local'); f.click('mode-portable'); assert.equal(f.run('embedMode'), 'portable');
  const before = observed(f);
  await f.resolve('reverse', 0, { city: 'Lisbon', countryCode: 'PT', continentCode: 'EU' }); assert.equal(observed(f), before);
  assert.equal(f.tuple()[3], '2');
});
test('R31-06 a debounce scheduled in portable mode that fires after switching to local sends nothing', async () => {
  const f = builder(); f.input('lat', '40.7'); f.input('lon', '-74'); f.click('mode-local'); await f.advance(700);
  assert.equal(f.calls.reverse.length, 0);
});

// ---- R31-08: Nominatim jsonv2 place kind (D-31-4 A) ----------------------------------------------------------
// Documented jsonv2 shape: `category` (Nominatim docs/api/Output.md "JSONv2" at edbe8c7d); `class` is the json shape.
function springfield(key) {
  const item = (kind, type, lat, lon, place, state) => ({ [key]: kind, type, lat, lon, name: place,
    address: kind === 'place' ? { city: place, state, country: 'United States', country_code: 'us' } : { road: place, state, country: 'United States', country_code: 'us' } });
  return { body: [item('highway', 'residential', '40.04', '-75.32', 'Springfield Road', 'Pennsylvania'),
    item('place', 'city', '39.80', '-89.65', 'Springfield', 'Illinois'), item('amenity', 'school', '42.10', '-72.59', 'Springfield School', 'Massachusetts')] };
}
async function search(body) {
  const e = L.engine({ config }, { nominatim: body }); const r = await e.api.geocodeSearchDetailed('Springfield', {});
  return JSON.parse(JSON.stringify(r));
}
for (const key of ['category', 'class'])
  test(`R31-08 place preference selects the city for a ${key}-keyed Springfield reply`, async () => {
    const r = await search(springfield(key));
    assert.equal(r.status, 'matches'); assert.equal(r.coverage, 'complete');
    assert.deepEqual(r.candidates.map(c => c.norm), ['Springfield, Illinois, United States']);
    assert.deepEqual(r.attempts, [{ provider: 'Nominatim', state: 'ok', reason: null }]);
  });
test('R31-08 no place/boundary item: all admitted items in provider order (either key)', async () => {
  for (const key of ['category', 'class']) {
    const body = springfield(key); body.body.splice(1, 1); const r = await search(body);
    assert.deepEqual(r.candidates.map(c => c.name), ['Springfield Road', 'Springfield School'], key);
  }
});
test('R31-08 an item carrying class is ranked by class alone (category ignored when class is present)', async () => {
  const r = await search({ body: [{ class: 'highway', category: 'place', lat: '40.04', lon: '-75.32', address: { road: 'A', country_code: 'us' }, name: 'A' },
    { class: 'boundary', category: 'highway', lat: '39.80', lon: '-89.65', address: { city: 'B', country_code: 'us' }, name: 'B' }] });
  assert.deepEqual(r.candidates.map(c => c.name), ['B']);
});
test('R31-08 boundary via category is preferred; admission still precedes preference', async () => {
  const r = await search({ body: [{ category: 'boundary', lat: '999', lon: '0', name: 'Bad', address: { city: 'Bad' } },
    { category: 'highway', lat: '10', lon: '10', name: 'Road', address: { road: 'Road' } },
    { category: 'boundary', lat: '11', lon: '11', name: 'County', address: { county: 'County' } }] });
  assert.deepEqual(r.candidates.map(c => c.name), ['County']); assert.equal(r.attempts[0].reason, 'rejected 1');
});

// ---- R31-07: settings GPS publication versus the permission diagnostic (D-31-3 PENDING — todo witness) ---------
// Under every D-31-3 option except C the fix must be applied while the diagnostic query never settles. Today the
// publication awaits permissionState() (src/native/index.html _usePrecise); this witness stays a todo until the owner
// decides (index.html is outside this lane). It is NOT acceptance evidence. These two always load the working-tree
// index.html (unchanged by R0031; `git show` of the generated entry exceeds the fixture's buffer under R0031_REF).
test('R31-07 (D-31-3 pending) a never-settling permission query does not block a valid GPS fix', { todo: 'D-31-3 owner decision pending; index.html _usePrecise' }, async () => {
  const f = sourceFixture('settings', { deferPermission: true });
  f.click('set-pin'); await f.resolve('gps', 0, { ok: true, lat: 51.5, lon: -0.12, accuracy: 20 }); await f.advance(600000);
  assert.deepEqual(f.tuple().slice(1, 3), ['51.50000', '-0.12000']);
});
test('R31-07 control: a settling permission query publishes the fix (current behaviour)', async () => {
  const f = sourceFixture('settings', { deferPermission: true });
  f.click('set-pin'); await f.resolve('gps', 0, { ok: true, lat: 51.5, lon: -0.12, accuracy: 20 }); await f.resolve('permission', 0, 'granted');
  assert.deepEqual(f.tuple().slice(1, 3), ['51.50000', '-0.12000']);
});
