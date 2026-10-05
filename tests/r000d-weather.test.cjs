'use strict';
const assert = require('node:assert/strict'), { test } = require('node:test');
const fs = require('node:fs'), path = require('node:path'), Module = require('node:module');
const fixturePath = path.join(__dirname, 'r000c-weather.test.cjs'), fixtureText = fs.readFileSync(fixturePath, 'utf8');
const end = fixtureText.indexOf("test('control: actual fresh acquisition"); assert(end > 0);
const fixtureModule = new Module(fixturePath, module); fixtureModule.filename = fixturePath;
fixtureModule.paths = Module._nodeModulePaths(__dirname);
fixtureModule._compile(fixtureText.slice(0, end) + '\nmodule.exports={fixture,healthy,NOW};', fixturePath);
const { fixture, healthy, NOW } = fixtureModule.exports;
const flush = () => new Promise(resolve => setImmediate(resolve));
const response = data => ({ ok: true, status: 200, json: async () => data });
const manifest = () => ({ generated: NOW / 1000, host: 'https://tilecache.rainviewer.com', radar: { past: [{ time: NOW / 1000, path: '/v2/radar/' + NOW / 1000 }] } });
function deferred() { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
function timers(f) {
  let now = 0, next = 1; const pending = new Map(), callbacks = [];
  f.context.performance.now = () => now;
  f.context.setTimeout = (fn, ms) => { const id = next++; pending.set(id, { fn, at: now + ms }); callbacks.push(fn); return id; };
  f.context.clearTimeout = id => pending.delete(id);
  return { pending, callbacks, advance(ms, deliver = true) {
    now += ms; if (deliver) for (const [id, task] of [...pending]) if (task.at <= now) { pending.delete(id); task.fn(); }
  } };
}
function tracked(promise) { const result = { settled: false, promise: null }; result.promise = promise.then(value => { result.settled = true; return value; }); return result; }
function images(f) {
  const held = []; f.context.Image = class HeldImage { set src(url) { f.images.push(url); held.push(this); } }; return held;
}
const fn = kind => kind === 'weather' ? 'fetchWeather' : 'fetchRadar';
const busy = kind => kind === 'weather' ? 'wxBusy' : 'radarBusy';
const data = kind => kind === 'weather' ? healthy() : manifest();
test('control: healthy weather and readable tile reach actual current consumers', async () => {
  const f = fixture(), timer = timers(f); await f.fetchWeather(); await f.fetchRadar();
  assert.equal(f.view().a.wxTemp, 20); assert.equal(f.view().qa.cache.currentEligible, true);
  assert(f.read().weatherRadar.sample); assert.equal(f.radarPrecipNow(), 0);
  assert.equal(f.read().wxBusy, false); assert.equal(f.read().radarBusy, false); assert.equal(timer.pending.size, 0);
});
for (const kind of ['weather', 'radar']) for (const stage of ['headers', 'body']) {
  test('R000D ' + kind + ' ' + stage + ' is busy at 9999ms and released at 10000ms', async () => {
    const gate = deferred(), f = fixture({ fetch: () => stage === 'headers' ? gate.promise : { ok: true, json: () => gate.promise } });
    const timer = timers(f), attempt = tracked(f[fn(kind)]()); await flush();
    timer.advance(9999); await flush(); assert.equal(f.read()[busy(kind)], true); assert.equal(attempt.settled, false);
    if (kind === 'radar') assert.equal(f.images.length, 0);
    timer.advance(1); await flush(); assert.equal(attempt.settled, true); assert.equal(f.read()[busy(kind)], false);
    assert.equal(timer.pending.size, 0);
    gate.resolve(stage === 'headers' ? response(data(kind)) : data(kind)); await flush();
    assert.equal(kind === 'weather' ? f.read().weather : f.read().weatherRadar, null);
  });
  test('R000D ' + kind + ' ' + stage + ' timeout permits healthy retry only after existing throttle', async () => {
    const gate = deferred(); let calls = 0;
    const f = fixture({ fetch: () => ++calls === 1 ? stage === 'headers' ? gate.promise : { ok: true, json: () => gate.promise } : response(data(kind)) });
    const timer = timers(f); f[fn(kind)](); await flush(); timer.advance(10000); await flush();
    f.clock.now += kind === 'weather' ? 59999 : 599999; await f[fn(kind)](); assert.equal(f.calls.length, 1);
    f.clock.now += 1; await f[fn(kind)](); assert.equal(f.calls.length, 2); assert.equal(f.read()[busy(kind)], false);
    assert.equal(timer.pending.size, 0);
    if (kind === 'weather') { assert.equal(f.view().a.wxTemp, 20); assert.equal(f.view().qa.cache.currentEligible, true); }
    else assert.equal(f.view().qa.wxTruth.radarAvailable, true);
    gate.resolve(stage === 'headers' ? response(data(kind)) : data(kind)); await flush();
    assert.equal(f.read()[busy(kind)], false);
  });
}
test('R000D delayed timer delivery cannot admit weather body after absolute elapsed deadline', async () => {
  const body = deferred(), f = fixture({ fetch: () => ({ ok: true, json: () => body.promise }) });
  const timer = timers(f), attempt = f.fetchWeather(); await flush(); timer.advance(10001, false);
  body.resolve(healthy()); await attempt; assert.equal(f.read().weather, null); assert.equal(f.cache(), null);
  assert.equal(f.read().wxBusy, false); assert.equal(timer.pending.size, 0); assert.equal(f.clock.now, NOW);
});
test('R000D timeout reason cannot renew stale current, accepted timestamp or cache', async () => {
  let calls = 0; const body = deferred();
  const f = fixture({ fetch: () => ++calls === 1 ? response(healthy()) : { ok: true, json: () => body.promise } }), timer = timers(f);
  await f.fetchWeather(); const prior = f.read().weather, cached = f.storage.get('salahwx:24.47|39.61|c');
  f.clock.now += 900001; const pending = f.fetchWeather(); await flush(); timer.advance(10000); await pending;
  const view = f.view(); assert.equal(view.qa.wxTruth.requests.weather.reason, 'body timeout');
  assert.equal(f.read().weather, prior); assert.equal(f.read().lastWxAt, NOW); assert.equal(view.a.wxTemp, null);
  assert.equal(f.storage.get('salahwx:24.47|39.61|c'), cached);
  body.reject(Error('late ignored transport abort')); await flush(); assert.equal(timer.pending.size, 0);
});
test('R000D explicit advancing scene still uses ten seconds of real elapsed attempt time', async () => {
  const headers = deferred(), f = fixture({ hash: 'timeScale=3600', fetch: () => headers.promise }), timer = timers(f);
  const pending = tracked(f.fetchWeather()); timer.advance(9999); await flush(); assert.equal(f.read().wxBusy, true);
  timer.advance(1); await flush(); assert.equal(pending.settled, true); assert.equal(f.read().wxBusy, false);
  headers.resolve(response(healthy())); await flush(); assert.equal(f.read().weather, null);
});
test('R000D radar image deadline detaches handlers and retained callbacks cannot install', async () => {
  const f = fixture(), held = images(f), timer = timers(f), attempt = tracked(f.fetchRadar()); await flush();
  const load = held[0].onload, error = held[0].onerror;
  timer.advance(9999); await flush(); assert.equal(f.read().radarBusy, true); assert.equal(attempt.settled, false);
  timer.advance(1); await flush(); assert.equal(attempt.settled, true); assert.equal(f.read().radarBusy, false);
  assert.equal(held[0].onload, null); assert.equal(held[0].onerror, null); assert.equal(timer.pending.size, 0);
  load(); error(); await flush(); assert.equal(f.read().weatherRadar, null); assert.equal(f.radarPrecipNow(), 0);
});
test('control: manifest 9999ms then image 9999ms succeeds within combined bound', async () => {
  const body = deferred(), f = fixture({ fetch: () => ({ ok: true, json: () => body.promise }) });
  const held = images(f), timer = timers(f), attempt = f.fetchRadar(); await flush();
  timer.advance(9999); body.resolve(manifest()); await flush(); assert.equal(held.length, 1);
  timer.advance(9999); held[0].onload(); await attempt;
  assert(f.read().weatherRadar.sample); assert.equal(f.read().radarBusy, false); assert.equal(timer.pending.size, 0);
  assert.equal(held[0].onload, null); assert.equal(held[0].onerror, null); assert.equal(f.radarPrecipNow(), 0);
});
test('R000D image absolute deadline rejects late load even before its timer callback', async () => {
  const f = fixture(), held = images(f), timer = timers(f), pending = f.fetchRadar(); await flush();
  timer.advance(10001, false); held[0].onload(); await pending;
  assert.equal(f.read().weatherRadar, null); assert.equal(f.read().radarBusy, false); assert.equal(timer.pending.size, 0);
});
test('R000D saved old timeout after success cannot clear a new active weather owner', async () => {
  let calls = 0; const body = deferred(), f = fixture({ fetch: () => ++calls === 1 ? response(healthy()) : { ok: true, json: () => body.promise } });
  const timer = timers(f); await f.fetchWeather(); const oldTimeout = timer.callbacks[0];
  assert.equal(timer.pending.size, 0); f.clock.now += 900001; const b = tracked(f.fetchWeather()); await flush();
  oldTimeout(); assert.equal(f.read().wxBusy, true); assert.equal(b.settled, false);
  body.resolve(healthy({ time: '2026-09-07T21:15' })); await b.promise;
  assert.equal(f.read().wxBusy, false); assert.equal(timer.pending.size, 0);
});
for (const kind of ['weather', 'radar']) test('R0003 ' + kind + ' obsolete error/finally cannot release successor', async () => {
  const old = deferred(), next = deferred(); let calls = 0;
  const f = fixture({ fetch: () => ++calls === 1 ? old.promise : next.promise }); const timer = timers(f);
  const a = f[fn(kind)](); await flush(); assert.equal(typeof f.beginRuntimeGeneration, 'function');
  f.set({ lat: 30, lon: 0, lastWxTry: 0, lastRadarAt: 0 }); f.beginRuntimeGeneration();
  const b = tracked(f[fn(kind)]()); await flush(); assert.equal(f.calls.length, 2);
  old.resolve({ ok: false, status: 500 }); await a; await flush();
  assert.equal(f.read()[busy(kind)], true); assert.equal(b.settled, false);
  next.resolve(response(data(kind))); await b.promise;
  assert.equal(f.read()[busy(kind)], false); assert.equal(timer.pending.size, 0);
});
test('R0003 old weather success cannot install or persist after target/unit replacement', async () => {
  const old = deferred(), next = deferred(); let calls = 0;
  const f = fixture({ fetch: () => ++calls === 1 ? old.promise : next.promise }); const timer = timers(f);
  const a = f.fetchWeather(); await flush(); f.set({ lat: 30, lon: 0, units: 'f', lastWxTry: 0 }); f.beginRuntimeGeneration();
  const b = f.fetchWeather(); await flush(); old.resolve(response(healthy())); await a;
  assert.equal(f.read().weather, null); assert.equal(f.read().weatherTrack, null); assert.equal(f.read().siteElev, 0); assert.equal(f.cache(), null);
  assert.equal(f.read().wxBusy, true); next.resolve(response(healthy({ temperature_2m: 68 }))); await b;
  assert.equal(f.read().weather.units, 'f'); assert.equal(f.view().a.wxTemp, 68);
  assert(f.storage.has('salahwx:30|0|f')); assert(!f.storage.has('salahwx:24.47|39.61|c')); assert.equal(timer.pending.size, 0);
});
test('R0003 old image onload cannot install or clear current target image attempt', async () => {
  const f = fixture({ lat: 0, lon: 30 }), held = images(f), timer = timers(f); const a = f.fetchRadar(); await flush();
  const oldLoad = held[0].onload; f.set({ lat: 30, lon: 0, lastRadarAt: 0 }); f.beginRuntimeGeneration();
  const b = tracked(f.fetchRadar()); await flush(); oldLoad(); await a;
  assert.equal(f.read().weatherRadar, null); assert.equal(f.read().radarBusy, true); assert.equal(b.settled, false);
  held[1].onload(); await b.promise; assert(f.images[1].includes('/256/6/32/26/'));
  assert.equal(f.read().radarBusy, false); assert.equal(timer.pending.size, 0);
});
for (const [name, opts] of [['weather rejection', { offline: true }], ['malformed JSON', { jsonError: true }], ['image error', { imageError: true }], ['canvas failure', { canvasError: true }]]) {
  test('control: ordinary ' + name + ' releases its timers and slots', async () => {
    const f = fixture(opts), timer = timers(f); await f.fetchWeather(); await f.fetchRadar();
    assert.equal(f.read().wxBusy, false); assert.equal(f.read().radarBusy, false); assert.equal(timer.pending.size, 0);
  });
}
