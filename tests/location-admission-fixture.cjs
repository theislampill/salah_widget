'use strict';
// R0026 / issue #68 source controls, shared by location-admission-outcomes.test.cjs and the mutation controls.
// The actual generated config.js runs in a Node vm with controlled provider replies, manual timers and a stubbed
// geolocation double; builder/settings consumers are the actual generated scripts loaded by r000f-fixture.cjs.
// No network request leaves the process and no real position is read. Not native evidence.
const assert = require('node:assert/strict'), vm = require('node:vm');
const { fixture, readSource, drain, deferred } = require('./r000f-fixture.cjs');

// S = {config: config.js text, builderMutate/indexMutate: optional page-script transforms (mutation controls)}.
const base = { config: readSource('config.js'), builderMutate: undefined, indexMutate: undefined };
const SECRET = 'fixture-body-secret';
const plain = v => JSON.parse(JSON.stringify(v));
const UNSETTLED = Symbol('unsettled');

// Provider reply double: 'network' rejects, 'hang' never settles (abort-ignorant), {status, body|malformed}.
function reply(spec) {
  if (spec === undefined) return Promise.reject(new TypeError('fixture: no route'));
  if (spec === 'network') return Promise.reject(new TypeError('controlled network failure'));
  if (spec === 'hang') return new Promise(() => {});
  const status = spec.status ?? 200;
  return Promise.resolve({ ok: status >= 200 && status < 300, status,
    json: () => spec.malformed ? Promise.reject(new SyntaxError('Unexpected token <')) : spec.later ? spec.later.promise : Promise.resolve(spec.body) });
}
function host(url) {
  const h = new URL(url).hostname;
  return h === 'get.geojs.io' ? 'geojs' : h === 'ipinfo.io' ? 'ipinfo' : h === 'nominatim.openstreetmap.org' ? 'nominatim'
    : h === 'api.zippopotam.us' ? 'zippopotam' : h;
}
function engine(S, routes = {}, position, extra = {}) {
  const timers = new Map(), requests = []; let id = 0;
  const ctx = { URL, URLSearchParams, AbortController, Intl, Date, console, ...extra,
    setTimeout: (fn, ms) => { const k = ++id; timers.set(k, { fn, ms }); return k; },
    clearTimeout: k => { timers.delete(k); },
    fetch: url => { requests.push(String(url)); return reply(routes[host(url)]); } };
  if (position !== undefined) ctx.navigator = { geolocation: { getCurrentPosition: ok => ok(position) } };
  ctx.window = ctx; vm.createContext(ctx); vm.runInContext(S.config, ctx);
  return { api: ctx.SalahConfig, requests, timers,
    fire() { const all = [...timers]; timers.clear(); for (const [, t] of all) t.fn(); } };
}
async function settle(p) { let v = UNSETTLED; p.then(x => { v = x; }, e => { v = e; }); await drain(); return v; }

// ---- coarse acquisition ---------------------------------------------------------------------------------------
const geo = (lat, lon, extra = {}) => ({ body: { latitude: lat, longitude: lon, city: 'Fixture', country_code: 'SA', ...extra } });
const ipinfo = { body: { loc: '51.5,-0.12', city: 'London', country: 'GB' } };
async function coarseRejectsPrimary(S, lat, lon = '39.61') {
  const e = engine(S, { geojs: geo(lat, lon), ipinfo }), r = await settle(e.api.coarseDetect({ timeoutMs: 5 }));
  assert.notEqual(r, UNSETTLED);
  assert.equal(r.ok, true); assert.equal(r.provider, 'ipinfo', 'invalid GeoJS evidence must reach the one fallback');
  assert.deepEqual([r.cfg.lat, r.cfg.lon], [51.5, -0.12]); assert.equal(e.requests.length, 2); assert.equal(e.timers.size, 0);
  assert.deepEqual(plain(r.attempts).map(a => [a.provider, a.state]), [['GeoJS', 'admission'], ['ipinfo', 'ok']]);
}
async function coarseAdmits(S, lat, lon, expected) {
  const e = engine(S, { geojs: geo(lat, lon), ipinfo }), r = await e.api.coarseDetect({ timeoutMs: 5 });
  assert.equal(r.provider, 'GeoJS'); assert.equal(e.requests.length, 1);
  assert.ok(Object.is(r.cfg.lat, expected[0]) && Object.is(r.cfg.lon, expected[1]), `admitted unchanged: ${r.cfg.lat},${r.cfg.lon}`);
}
async function coarseIpinfo(S, loc, expected) {
  const e = engine(S, { geojs: 'network', ipinfo: { body: { loc, city: 'X', country: 'GB' } } }), r = await e.api.coarseDetect({ timeoutMs: 5 });
  if (expected === null) { assert.equal(r.ok, false); assert.equal(r.cfg, undefined); return; }
  assert.equal(r.provider, 'ipinfo'); assert.ok(Object.is(r.cfg.lat, expected[0]) && Object.is(r.cfg.lon, expected[1]));
}
async function coarseBothInvalid(S) {
  const e = engine(S, { geojs: geo('999', '999'), ipinfo: { body: { loc: '999,999', city: 'X', country: 'GB' } } });
  const r = await settle(e.api.coarseDetect({ timeoutMs: 5 }));
  assert.deepEqual(plain(r), { ok: false, source: 'coarse-ip', status: 'failed',
    attempts: [{ provider: 'GeoJS', state: 'admission', reason: 'latitude' }, { provider: 'ipinfo', state: 'admission', reason: 'latitude' }] });
  assert.equal(e.requests.length, 2); assert.equal(e.timers.size, 0);
}
async function coarseAccuracy(S, accuracy, expected) {
  const e = engine(S, { geojs: geo('24.47', '39.61', accuracy === undefined ? {} : { accuracy }) }), r = await e.api.coarseDetect({ timeoutMs: 5 });
  assert.equal(r.provider, 'GeoJS'); assert.ok(Object.is(r.cfg.accuracy, expected), `accuracy ${String(accuracy)} → ${r.cfg.accuracy}`);
}
async function coarseAttemptsBounded(S) {
  const e = engine(S, { geojs: { status: 503, body: { latitude: '24.47', longitude: '39.61', city: SECRET } }, ipinfo: { body: { loc: '51.5,-0.12', city: SECRET, country: 'GB' } } });
  const r = await e.api.coarseDetect({ timeoutMs: 5 });
  assert.equal(r.ok, true); assert.equal(r.status, 'ok'); assert.equal(r.source, 'coarse-ip'); assert.equal(r.provider, 'ipinfo');
  const attempts = plain(r.attempts);
  assert.deepEqual(attempts, [{ provider: 'GeoJS', state: 'http', reason: 'status 503' }, { provider: 'ipinfo', state: 'ok', reason: null }]);
  assert.doesNotMatch(JSON.stringify(attempts), new RegExp(SECRET));
  const t = engine(S, { geojs: 'hang', ipinfo }), p = t.api.coarseDetect({ timeoutMs: 5 }); await drain(); t.fire();
  assert.deepEqual(plain((await p).attempts).map(a => a.state), ['timeout', 'ok']);
}

// ---- forward search ------------------------------------------------------------------------------------------
const nom = (...items) => ({ body: items.map(([lat, lon, city = 'Fixture']) => ({ class: 'place', lat, lon, name: city, address: { city, country: 'Fixture', country_code: 'fx' } })) });
const zip = (latitude, longitude) => ({ body: { country: 'Canada', 'country abbreviation': 'CA', places: [{ 'place name': 'Toronto', state: 'Ontario', latitude, longitude }] } });
async function detailed(S, q, routes) {
  const e = engine(S, routes), p = e.api.geocodeSearchDetailed(q, {});
  let r = await settle(p);
  if (r === UNSETTLED) { e.fire(); r = await settle(p); }
  assert.notEqual(r, UNSETTLED, 'one terminal outcome');
  const le = engine(S, routes), lp = le.api.geocodeSearch(q, {});
  let legacy = await settle(lp);
  if (legacy === UNSETTLED) { le.fire(); legacy = await settle(lp); }
  return { r: plain(r), e, legacy };
}
// Returns the detailed result after checking the shared invariants every outcome must satisfy.
async function forward(S, q, routes, expected) {
  const { r, e, legacy } = await detailed(S, q, routes);
  assert.equal(r.status, expected.status, JSON.stringify(r));
  if ('coverage' in expected) assert.equal(r.coverage, expected.coverage);
  if (expected.states) assert.deepEqual(r.attempts.map(a => [a.provider, a.state]), expected.states);
  if ('count' in expected) assert.equal(r.candidates.length, expected.count);
  for (const c of r.candidates) assert.ok(Number.isFinite(c.lat) && Math.abs(c.lat) <= 90 && Number.isFinite(c.lon) && Math.abs(c.lon) <= 180, 'only admitted candidates');
  for (const a of r.attempts) {
    assert.deepEqual(Object.keys(a).sort(), ['provider', 'reason', 'state']);
    assert.ok(a.reason === null || typeof a.reason === 'string' && a.reason.length <= 40);
  }
  const text = JSON.stringify(r.attempts) + JSON.stringify(Object.keys(r));
  assert.doesNotMatch(text, new RegExp(SECRET)); assert.ok(!text.includes(q.trim()), 'no query in the bounded record');
  assert.ok(Array.isArray(legacy), 'legacy projection stays an array'); assert.deepEqual(plain(legacy), r.candidates);
  return { r, e };
}
const T = 'M5V2T6';  // Canadian-style prefix: Nominatim + Zippopotam
async function nominatim503(S) {
  await forward(S, 'London', { nominatim: { status: 503, body: nom(['51.5', '-0.12', 'London']).body } }, { status: 'unavailable', coverage: 'none', states: [['Nominatim', 'http']], count: 0 });
}
async function nominatimFailures(S) {
  for (const [route, state] of [[{ status: 429, body: [] }, 'http'], ['network', 'transport'], [{ malformed: true }, 'parse'], [{ body: { error: SECRET } }, 'parse'], [{ body: null }, 'parse'], ['hang', 'timeout']])
    await forward(S, 'London', { nominatim: route }, { status: 'unavailable', coverage: 'none', states: [['Nominatim', state]], count: 0 });
}
async function nominatimNoMatch(S) { await forward(S, 'Nowhere', { nominatim: { body: [] } }, { status: 'no-match', coverage: 'complete', states: [['Nominatim', 'no-match']], count: 0 }); }
async function nominatimInvalid(S) {
  for (const [lat, lon] of [['999', '999'], ['Infinity', '10'], ['NaN', '10'], ['12junk', '10'], [null, '10'], ['', '10'], ['10', '181'], ['0x10', '10'], ['1e1', '10'], [true, '10'], [['10'], '10']])
    await forward(S, 'Fixture', { nominatim: nom([lat, lon]) }, { status: 'unavailable', coverage: 'none', states: [['Nominatim', 'admission']], count: 0 });
  const { r } = await forward(S, 'Fixture', { nominatim: nom(['999', '999'], ['51.5', '-0.12', 'London']) }, { status: 'matches', coverage: 'complete', count: 1 });
  assert.equal(r.candidates[0].name, 'London');
}
async function forwardBoundaries(S) {
  for (const [lat, lon, expected] of [['0', '30', [0, 30]], ['30', '0', [30, 0]], ['0', '0', [0, 0]], ['-0', '-0', [-0, -0]], ['90', '180', [90, 180]], ['-90', '-180', [-90, -180]], [' 24.47 ', '+39.61', [24.47, 39.61]], [-33.5, 151.25, [-33.5, 151.25]]]) {
    const e = engine(S, { nominatim: nom([lat, lon]) }), r = await e.api.geocodeSearchDetailed('Fixture', {});
    assert.equal(r.status, 'matches'); assert.ok(Object.is(r.candidates[0].lat, expected[0]) && Object.is(r.candidates[0].lon, expected[1]), `${lat},${lon} → ${r.candidates[0].lat},${r.candidates[0].lon}`);
  }
}
async function zippopotam(S) {
  await forward(S, T, { nominatim: { body: [] }, zippopotam: { status: 404, body: {} } }, { status: 'no-match', coverage: 'complete', states: [['Nominatim', 'no-match'], ['Zippopotam', 'no-match']], count: 0 });
  for (const [route, state] of [[{ status: 503, body: zip('43.6', '-79.4').body }, 'http'], [{ status: 429, body: {} }, 'http'], ['network', 'transport'], [{ malformed: true }, 'parse']])
    await forward(S, T, { nominatim: { body: [] }, zippopotam: route }, { status: 'unavailable', coverage: 'partial', states: [['Nominatim', 'no-match'], ['Zippopotam', state]], count: 0 });
}
async function zippopotamMissingLatitude(S) {
  for (const [lat, lon] of [[null, '-79.4'], ['', '-79.4'], [undefined, '-79.4'], ['43.6', null]])
    await forward(S, T, { nominatim: { body: [] }, zippopotam: zip(lat, lon) }, { status: 'unavailable', coverage: 'partial', states: [['Nominatim', 'no-match'], ['Zippopotam', 'admission']], count: 0 });
}
async function partialMatches(S) {
  let { r } = await forward(S, T, { nominatim: nom(['43.64', '-79.39', 'Toronto']), zippopotam: { status: 503, body: {} } }, { status: 'matches', coverage: 'partial', states: [['Nominatim', 'ok'], ['Zippopotam', 'http']], count: 1 });
  assert.equal(r.candidates[0].provider, 'Nominatim');
  ({ r } = await forward(S, T, { nominatim: 'network', zippopotam: zip('43.6', '-79.4') }, { status: 'matches', coverage: 'partial', states: [['Nominatim', 'transport'], ['Zippopotam', 'ok']], count: 1 }));
  assert.equal(r.candidates[0].provider, 'Zippopotam'); assert.deepEqual([r.candidates[0].lat, r.candidates[0].lon], [43.6, -79.4]);
  await forward(S, T, { nominatim: nom(['43.64', '-79.39', 'Toronto']), zippopotam: zip('43.6', '-79.4') }, { status: 'matches', coverage: 'complete', count: 1 });
}
async function bothFail(S) {
  await forward(S, T, { nominatim: { status: 503, body: [] }, zippopotam: 'network' }, { status: 'unavailable', coverage: 'none', states: [['Nominatim', 'http'], ['Zippopotam', 'transport']], count: 0 });
}
async function emptyPlusFailure(S) {
  await forward(S, T, { nominatim: { body: [] }, zippopotam: { status: 503, body: {} } }, { status: 'unavailable', coverage: 'partial', count: 0 });
  await forward(S, T, { nominatim: { status: 503, body: [] }, zippopotam: { status: 404, body: {} } }, { status: 'unavailable', coverage: 'partial', states: [['Nominatim', 'http'], ['Zippopotam', 'no-match']], count: 0 });
}
async function dedupe(S) {
  const { r } = await forward(S, T, { nominatim: nom(['43.64', '-79.39', 'Toronto'], ['Infinity', '10', 'Bad'], ['51.5', '-0.12', 'London']), zippopotam: zip('43.65', '-79.38') }, { status: 'matches', coverage: 'complete', count: 2 });
  assert.deepEqual(r.candidates.map(c => [c.name, c.provider, c.lat]), [['Toronto', 'Nominatim', 43.64], ['London', 'Nominatim', 51.5]]);
}
async function notRequested(S) {
  for (const q of [' X ', ' ', '', null]) {
    const e = engine(S, {}), r = plain(await e.api.geocodeSearchDetailed(q, {}));
    assert.deepEqual(r, { status: 'not-requested', coverage: null, candidates: [], attempts: [] }); assert.deepEqual(e.requests, []);
    assert.deepEqual(plain(await e.api.geocodeSearch(q, {})), []);
  }
}
async function lateBody(S) {
  const errors = [], listener = error => errors.push(error); process.on('unhandledRejection', listener);
  try {
    const later = deferred(), e = engine(S, { nominatim: { later } }), p = e.api.geocodeSearchDetailed('London', {});
    let n = 0, value; p.then(v => { n++; value = v; }); await drain(); assert.equal(n, 0);
    assert.equal(e.timers.size, 1, 'one existing forward deadline'); assert.equal([...e.timers.values()][0].ms, 8000);
    e.fire(); await drain(); assert.equal(n, 1); assert.equal(value.status, 'unavailable'); assert.equal(value.attempts[0].state, 'timeout');
    later.resolve(nom(['51.5', '-0.12']).body); await drain(); assert.equal(n, 1); assert.equal(value.candidates.length, 0);
    const late = deferred(), f = engine(S, { nominatim: { later: late } }), q = f.api.geocodeSearchDetailed('London', {}); await drain(); f.fire(); await q;
    late.reject(new SyntaxError('late')); await new Promise(resolve => setImmediate(resolve)); assert.deepEqual(errors, []);
  } finally { process.removeListener('unhandledRejection', listener); }
}
async function legacyProjection(S) {
  const routes = [{ nominatim: { status: 503, body: [] } }, { nominatim: 'network' }, { nominatim: { body: [] } }, { nominatim: nom(['51.5', '-0.12']) }, { nominatim: { body: { error: 1 } } }];
  for (const r of routes) { const v = await settle(engine(S, r).api.geocodeSearch('London', {})); assert.ok(Array.isArray(v), 'array for every case'); }
  const v = await settle(engine(S, { nominatim: 'hang' }).api.geocodeSearch('London', {}));
  assert.equal(v, UNSETTLED, 'the projection keeps the engine deadline (settles only when the deadline fires)');
}

// ---- browser geolocation -------------------------------------------------------------------------------------
const pos = (latitude, longitude, accuracy = 20) => ({ coords: { latitude, longitude, accuracy }, timestamp: Date.now() - 1000 });
const BAD_POSITIONS = [[999, 10], [-91, 10], [10, 181], [NaN, 10], [Infinity, 10], [undefined, 10], [null, 10], ['12abc', 10], [10, -Infinity]];
async function geolocateAdmission(S) {
  for (const [lat, lon] of BAD_POSITIONS) {
    const r = plain(await engine(S, {}, pos(lat, lon)).api.geolocate({}));
    assert.equal(r.ok, false, `${lat},${lon} must not be published`); assert.equal(r.lat, undefined); assert.equal(r.error, 'invalid coordinates');
  }
  for (const [lat, lon] of [[0, 0], [-0, 30], [90, -180], [52.52, 13.41]]) {
    const r = await engine(S, {}, pos(lat, lon)).api.geolocate({});
    assert.equal(r.ok, true); assert.ok(Object.is(r.lat, lat) && Object.is(r.lon, lon)); assert.equal(r.accuracy, 20);
  }
  for (const accuracy of [NaN, -1, Infinity, '25', undefined]) {
    const r = await engine(S, {}, pos(52.52, 13.41, accuracy)).api.geolocate({});
    assert.equal(r.ok, true); assert.equal(r.accuracy, null); assert.equal(r.locationEvidence.accuracyM, null);
  }
}

// ---- actual consumers ----------------------------------------------------------------------------------------
// The consumer's SalahConfig acquisition/persistence entries come from the (possibly mutated) engine source.
function wire(f, e) { for (const k of ['geocodeSearch', 'geocodeSearchDetailed', 'coarseDetect', 'geolocate', 'admitCoordinates', 'saveLocal', 'loadLocal']) f.sandbox.SalahConfig[k] = e.api[k]; }
function consumer(S, kind, routes = {}, position) {
  const f = fixture(kind, { mutate: kind === 'builder' ? S.builderMutate : S.indexMutate }), e = engine(S, routes, position, { localStorage: f.sandbox.localStorage });
  wire(f, e); return { f, e };
}
const status = f => f.elements.get(f.kind === 'builder' ? 'geotip' : 'set-status').textContent;
async function search(f, e, q) {
  const id = f.kind === 'builder' ? 'label' : 'set-label'; f.input(id, q); f.key(id, 'Enter');
  await drain(); if (e.timers.size) { e.fire(); } await drain(); await drain();
}
const INITIAL = { builder: ['24.4672', '39.6142'], settings: ['24.4672', '39.6142'] };
const NOT_FOUND = { builder: /^Couldn’t find that/, settings: /^Couldn’t find “/ };
const UNAVAILABLE = /^Search unavailable/;
async function uiNoMatch(S, kind) {
  const { f, e } = consumer(S, kind, { nominatim: { body: [] } }); await search(f, e, 'Nowhere');
  assert.match(status(f).split('\n').pop(), NOT_FOUND[kind]); assert.deepEqual(f.tuple().slice(1, 3), INITIAL[kind]);
}
async function uiUnavailable(S, kind) {
  for (const route of [{ status: 503, body: nom(['51.5', '-0.12', 'London']).body }, 'network', { malformed: true }, { body: { error: 1 } }, 'hang', nom(['999', '999'])]) {
    const { f, e } = consumer(S, kind, { nominatim: route }); await search(f, e, 'London');
    const text = status(f).split('\n').pop();
    assert.match(text, UNAVAILABLE, `${JSON.stringify(route)}: ${text}`); assert.doesNotMatch(text, /Couldn’t find/);
    assert.deepEqual(f.tuple().slice(1, 3), INITIAL[kind], 'no location published');
    if (kind === 'settings') assert.equal(f.elements.get('set-status').classList.contains('err'), true);
  }
}
async function uiPartial(S, kind) {
  let { f, e } = consumer(S, kind, { nominatim: nom(['43.64', '-79.39', 'Toronto']), zippopotam: { status: 503, body: {} } }); await search(f, e, T);
  assert.match(status(f).split('\n').pop(), /^Found \(partial search\): Toronto/); assert.deepEqual(f.tuple().slice(1, 3), ['43.64000', '-79.39000']);
  ({ f, e } = consumer(S, kind, { nominatim: nom(['43.64', '-79.39', 'Toronto'], ['51.5', '-0.12', 'London']), zippopotam: 'network' })); await search(f, e, T);
  assert.match(status(f), /^Match 1(\/| of )2 \(partial search\): Toronto/m);
  f.key(kind === 'builder' ? 'label' : 'set-label', 'Enter'); assert.match(status(f), /^Match 2(\/| of )2 \(partial search\): London/m); assert.equal(f.tuple()[1], '51.50000');
  ({ f, e } = consumer(S, kind, { nominatim: nom(['43.64', '-79.39', 'Toronto']), zippopotam: zip('43.6', '-79.4') })); await search(f, e, T);
  assert.match(status(f).split('\n').pop(), /^Found: Toronto/); assert.doesNotMatch(status(f), /partial/);
}
async function builderCoarse(S) {
  let { f, e } = consumer(S, 'builder', { geojs: geo('999', '999'), ipinfo }); f.run('detectArea()'); await drain(); await drain();
  assert.deepEqual(f.tuple().slice(1, 3), ['51.50000', '-0.12000']); assert.match(status(f), /^Detected: London/);
  ({ f, e } = consumer(S, 'builder', { geojs: geo('999', '999'), ipinfo: { body: { loc: '999,999' } } })); f.run('detectArea()'); await drain(); await drain();
  assert.deepEqual(f.tuple().slice(1, 3), INITIAL.builder); assert.match(status(f), /^Couldn’t detect/); assert.equal(f.elements.get('geo').classList.contains('off'), true);
}
async function builderGeolocation(S) {
  for (const [lat, lon] of BAD_POSITIONS) {
    const f = fixture('builder', { mutate: S.builderMutate }), e = engine(S); wire(f, e);
    f.click('geo'); await f.resolve('gps', 0, pos(lat, lon));
    assert.deepEqual(f.tuple().slice(1, 3), INITIAL.builder, `${lat},${lon} must not be published`);
    assert.match(status(f), /^Browser location unusable/); assert.equal(f.calls.reverse.length, 0);
  }
  for (const [lat, lon, shown] of [[0, -0, ['0.00000', '0.00000']], [-90, 180, ['-90.00000', '180.00000']], [52.52, 13.41, ['52.52000', '13.41000']]]) {
    const f = fixture('builder', { mutate: S.builderMutate }), e = engine(S); wire(f, e);
    f.click('geo'); await f.resolve('gps', 0, pos(lat, lon)); assert.deepEqual(f.tuple().slice(1, 3), shown); assert.match(status(f), /^Using browser position/);
  }
}
async function settingsGeolocation(S) {
  for (const [lat, lon] of BAD_POSITIONS.slice(0, 5)) {
    const { f } = consumer(S, 'settings', {}, pos(lat, lon)); f.click('set-pin'); await drain(); await drain();
    assert.deepEqual(f.tuple().slice(1, 3), INITIAL.settings); assert.match(status(f), /Browser location unavailable \(invalid coordinates\)/);
  }
  const { f } = consumer(S, 'settings', {}, pos(-33.5, 151.25)); f.click('set-pin'); await drain(); await drain();
  assert.deepEqual(f.tuple().slice(1, 3), ['-33.50000', '151.25000']);
}
// Stale success and stale error are no-ops for the current form and report the consumer-derived outcome.
async function staleLookup(S, kind, late) {
  const f = fixture(kind, { mutate: kind === 'builder' ? S.builderMutate : S.indexMutate }), q = [];
  f.sandbox.SalahConfig.geocodeSearchDetailed = f.sandbox.SalahConfig.geocodeSearch = () => { const d = deferred(); q.push(d); return d.promise; };
  const label = kind === 'builder' ? 'label' : 'set-label', run = kind === 'builder' ? 'doSearch' : '_runSetSearch';
  const ok = (name, lat) => ({ status: 'matches', coverage: 'complete', candidates: [{ lat, lon: 10, name, norm: name, cc: 'fx', provider: 'Nominatim', bounds: null }], attempts: [] });
  f.input(label, 'London'); const a = f.run(`${run}("London")`);
  f.input(label, 'Cairo'); const b = f.run(`${run}("Cairo")`);
  q[1].resolve(ok('Cairo', 30)); await drain(); assert.equal(await b, 'matches'); const current = f.snapshot();
  if (late === 'error') q[0].reject(new Error('controlled late failure')); else q[0].resolve(ok('London', 51.5));
  await drain(); assert.equal(f.snapshot(), current, 'stale result cannot touch the current form');
  assert.equal(await a, 'superseded');
  const c = f.run(`${run}("Cairo")`); f.input(label, 'Paris'); const before = f.snapshot();
  q[2].reject(new Error('controlled late failure')); await drain(); assert.equal(f.snapshot(), before); assert.equal(await c, 'superseded');
}
// A8: manual, hash and saved configuration keep R001E normalization (clamping) — distinct from external admission.
async function manualClampPreserved(S) {
  const { f } = consumer(S, 'settings'); f.input('set-lat', '999'); f.input('set-lon', '-999'); f.click('setClose');
  assert.deepEqual([f.calls.applied[0].cfg.lat, f.calls.applied[0].cfg.lon], [90, -180]);
  const api = engine(S).api;
  assert.deepEqual([api.resolve('#lat=999&lon=999').cfg.lat, api.resolve('#lat=999&lon=999').cfg.lon], [90, 180]);
  assert.equal(api.normalize({ lat: '0x10' }).lat, 16); assert.equal(api.normalize({ lat: '1e2' }).lat, 90); assert.equal(api.normalize({ lat: '12abc' }).lat, null);
  assert.equal(api.validate({ lat: '', lon: '', method: '2', school: '0', time: '24', units: 'f' }).ok, true, 'R001E validate quirk unchanged');
}
// ES26-14: a save never renews the fix time (admitted browser fix → apply → save → load).
async function fixAgeSurvivesSave(S) {
  const t = Date.now() - 600000, { f } = consumer(S, 'settings', {}, { coords: { latitude: 52.52, longitude: 13.41, accuracy: 25 }, timestamp: t });
  f.click('set-pin'); await drain(); await drain(); f.click('setClose');
  const saved = vm.runInContext('SalahConfig.loadLocal()', f.context);
  assert.equal(saved.locationEvidence.acquiredAt, t); assert.equal(saved.locationEvidence.accuracyM, 25); assert.notEqual(saved.savedAt, t);
}

module.exports = { base, engine, settle, UNSETTLED, coarseRejectsPrimary, coarseAdmits, coarseIpinfo, coarseBothInvalid, coarseAccuracy,
  coarseAttemptsBounded, nominatim503, nominatimFailures, nominatimNoMatch, nominatimInvalid, forwardBoundaries, zippopotam,
  zippopotamMissingLatitude, partialMatches, bothFail, emptyPlusFailure, dedupe, notRequested, lateBody, legacyProjection,
  geolocateAdmission, uiNoMatch, uiUnavailable, uiPartial, builderCoarse, builderGeolocation, settingsGeolocation,
  staleLookup, manualClampPreserved, fixAgeSurvivesSave };
