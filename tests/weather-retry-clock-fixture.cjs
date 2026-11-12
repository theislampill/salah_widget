'use strict';
// R000D / issue #13 (ES0D-01..15): weather and radar retry SPACING is measured on this document's elapsed
// clock, while source/receipt provenance stays UTC wall time. The real fetchWeather/fetchRadar gates,
// admission, header/effects consumers and qaState run through the r000c source fixture; the wall clock
// (Date) and the elapsed clock (performance.now + setTimeout) are independent controllable doubles.
// Network, Image and DOM are contained doubles. A synthetic clock step is not an NTP incident and this is
// source-consumer evidence only, not a native/browser qualification.
const assert = require('node:assert/strict'), { test } = require('node:test');
const fs = require('node:fs'), path = require('node:path'), Module = require('node:module');
const fixturePath = path.join(__dirname, 'r000c-weather.test.cjs'), fixtureText = fs.readFileSync(fixturePath, 'utf8');
const end = fixtureText.indexOf("test('control: actual fresh acquisition"); assert(end > 0);
const sourceLine = "const source = fs.readFileSync(sourcePath, 'utf8');";
assert.equal(fixtureText.split(sourceLine).length, 2, 'one fixture source binding');
// Load the actual r000c fixture, optionally over an in-memory source text (mutation controls never write disk).
function load(sourceText = null) {
  const m = new Module(fixturePath, module); m.filename = fixturePath; m.paths = Module._nodeModulePaths(__dirname);
  m.__source = sourceText;
  m._compile(fixtureText.slice(0, end).replace(sourceLine, "const source = module.__source ?? fs.readFileSync(sourcePath, 'utf8');") +
    '\nmodule.exports={fixture,healthy,NOW,sourcePath,source};', fixturePath);
  return m.exports;
}
const base = load();
const { NOW } = base;
const flush = async () => { for (let i = 0; i < 8; i++) await new Promise(resolve => setImmediate(resolve)); };
const iso = ms => new Date(ms).toISOString().slice(0, 16);
const response = data => ({ ok: true, status: 200, json: async () => data });
function deferred() { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
// A provider that publishes evidence valid at the request's own wall time (so a replacement made after a
// backward wall step is genuinely current at that corrected wall time).
function livePayload(healthy, wall, overrides = {}) {
  const minute = Math.floor(wall / 60000) * 60000, hour = Math.floor(wall / 3600000) * 3600000, p = healthy({ time: iso(minute), ...overrides });
  p.hourly.time = [iso(hour), iso(hour + 3600000)]; return p;
}
const liveManifest = wall => ({ generated: wall / 1000, host: 'https://tilecache.rainviewer.com', radar: { past: [{ time: wall / 1000, path: '/v2/radar/' + wall / 1000 }] } });
function transport(mod, { weather = 'live', radar = 'live' } = {}) {
  return (url, clock) => {
    if (url.includes('open-meteo')) {
      if (typeof weather === 'function') return weather(url, clock);
      if (weather === 'fail') return { ok: false, status: 503, json: async () => ({ error: true }) };
      return response(livePayload(mod.healthy, clock.now));
    }
    if (typeof radar === 'function') return radar(url, clock);
    if (radar === 'fail') return { ok: false, status: 503, json: async () => ({}) };
    return response(liveManifest(clock.now));
  };
}
// Independent clocks. elapse() advances both the elapsed and the wall clock (ordinary time passing) and
// delivers due elapsed timers; step() moves ONLY the wall clock (a wall-clock correction).
function clocks(f, mono = 1000) {
  const c = { mono }, pending = new Map(); let next = 1;
  f.context.performance.now = () => c.mono;
  f.context.setTimeout = (fn, ms) => { const id = next++; pending.set(id, { fn, at: c.mono + ms }); return id; };
  f.context.clearTimeout = id => pending.delete(id);
  return { pending, get mono() { return c.mono; }, step(ms) { f.clock.now += ms; },
    elapse(ms) { c.mono += ms; f.clock.now += ms; for (const [id, t] of [...pending]) if (t.at <= c.mono) { pending.delete(id); t.fn(); } } };
}
function setup({ mod = base, mono = 1000, weather, radar, opts = {} } = {}) {
  const f = mod.fixture({ fetch: transport(mod, { weather, radar }), ...opts }), t = clocks(f, mono); return { f, t };
}
const wxCalls = f => f.calls.filter(u => u.includes('open-meteo')).length;
const radarCalls = f => f.calls.filter(u => u.includes('rainviewer')).length;
const retry = f => JSON.parse(JSON.stringify(f.view().qa.wxTruth.retry));   // plain copy out of the vm realm

// ---- scenarios (also reused by tests/weather-retry-clock-mutations.test.cjs) ---------------------------
async function weatherRollback(mod = base, S = 2 * 3600000) {
  const { f, t } = setup({ mod });
  await f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 1);
  let v = f.view(); assert.equal(v.qa.cache.currentEligible, true); assert.equal(f.nodes.get('#wt').textContent, '20°');
  const accepted = f.read().weather;
  t.step(-S);                                                     // backward wall-clock correction
  v = f.view();                                                   // ES0D-05: future-dated receipt is ineligible, not laundered
  assert.equal(v.qa.cache.currentEligible, false, 'future-dated receipt must be ineligible');
  assert(v.qa.cache.weatherAgeSec < 0, 'receipt age stays negative (no max(0,age))');
  assert.equal(v.a.wxTemp, null); assert.equal(f.nodes.get('#wt').textContent, '');
  t.elapse(59999); await f.fetchWeather(); await flush();
  assert.equal(wxCalls(f), 1, 'no replacement before 60 000 ms elapsed');
  t.elapse(1); await f.fetchWeather(); await flush();
  assert.equal(wxCalls(f), 2, 'replacement request at 60 000 ms elapsed after a backward wall step');
  v = f.view();                                                   // ES0D-14: the replacement reaches the actual consumers
  assert.notEqual(f.read().weather, accepted); assert.equal(v.qa.cache.currentEligible, true);
  assert.equal(v.a.wxTemp, 20); assert.equal(f.nodes.get('#wt').textContent, '20°'); assert.equal(v.a.cls, 'thunder');
  assert.equal(f.read().wxBusy, false);
  // Provenance stays UTC wall time.
  assert.equal(f.read().weather.retrievedAt, f.clock.now); assert.equal(f.read().lastWxAt, f.clock.now); assert.equal(f.cache().ts, f.clock.now);
  return f;
}
async function radarRollback(mod = base, S = 2 * 3600000) {
  const { f, t } = setup({ mod });
  await f.fetchRadar(); await flush(); assert.equal(radarCalls(f), 1); assert.equal(f.view().qa.wxTruth.radarAvailable, true);
  const accepted = f.read().weatherRadar;
  t.step(-S);
  assert.equal(f.view().qa.wxTruth.radarAvailable, false, 'future-dated radar receipt must be unavailable');
  t.elapse(599999); await f.fetchRadar(); await flush();
  assert.equal(radarCalls(f), 1, 'no radar replacement before 600 000 ms elapsed');
  t.elapse(1); await f.fetchRadar(); await flush();
  assert.equal(radarCalls(f), 2, 'radar replacement request at 600 000 ms elapsed after a backward wall step');
  assert.equal(f.images.length, 2); assert.notEqual(f.read().weatherRadar, accepted);
  assert.equal(f.view().qa.wxTruth.radarAvailable, true); assert.equal(f.read().weatherRadar.retrievedAt, f.clock.now);
  assert.equal(f.read().radarBusy, false); assert.equal(f.radarPrecipNow(), 0);
  return f;
}
// Boundaries with a failing provider (no evidence, so the shortcut is not involved). Eligibility is
// inclusive at exactly the interval, matching the existing `elapsed-start < interval -> wait` predicate.
async function boundary(mod = base, kind = 'weather', wallStep = 0) {
  const interval = kind === 'weather' ? 60000 : 600000, call = kind === 'weather' ? 'fetchWeather' : 'fetchRadar', count = kind === 'weather' ? wxCalls : radarCalls;
  const { f, t } = setup({ mod, weather: 'fail', radar: 'fail' });
  await f[call](); await flush(); assert.equal(count(f), 1);
  t.step(wallStep);
  t.elapse(interval - 1); await f[call](); await flush(); assert.equal(count(f), 1, kind + ' blocked at ' + (interval - 1) + ' ms elapsed, wall step ' + wallStep);
  t.elapse(1); await f[call](); await flush(); assert.equal(count(f), 2, kind + ' requested at ' + interval + ' ms elapsed, wall step ' + wallStep);
}
// ES0D-07: a forward wall jump expires the evidence by UTC age but neither shortens the elapsed spacing nor
// causes a per-frame storm; every-frame callers get one request per elapsed interval.
async function forwardNoStorm(mod = base) {
  const { f, t } = setup({ mod });
  await f.fetchWeather(); await f.fetchRadar(); await flush(); assert.equal(wxCalls(f), 1); assert.equal(radarCalls(f), 1);
  t.step(2 * 3600000);
  assert.equal(f.view().qa.cache.currentEligible, false); assert.equal(f.view().qa.wxTruth.radarAvailable, false);
  for (let ms = 16; ms < 60000; ms += 16) { t.elapse(16); f.fetchWeather(); f.fetchRadar(); if (ms % 1600 === 0) await flush(); }
  await flush(); assert.equal(wxCalls(f), 1, 'forward wall jump must not open the weather spacing early'); assert.equal(radarCalls(f), 1);
  t.elapse(60000 - 59984 + 0); await f.fetchWeather(); await flush();
  assert.equal(t.mono, 61000); assert.equal(wxCalls(f), 2, 'one request when 60 000 ms have elapsed');
  for (let i = 0; i < 50; i++) { t.elapse(16); await f.fetchWeather(); } assert.equal(wxCalls(f), 2, 'no storm after the replacement');
  assert.equal(f.view().qa.cache.currentEligible, true);
  t.elapse(600000 - (t.mono - 1000)); await f.fetchRadar(); await flush(); assert.equal(radarCalls(f), 2);
  assert.equal(f.view().qa.wxTruth.radarAvailable, true);
}
// ES0D-04: null is "never attempted here"; a real attempt at elapsed 0 is a cooldown start.
async function zeroIsAttempt(mod = base) {
  const { f, t } = setup({ mod, mono: 0, weather: 'fail', radar: 'fail' });
  assert.equal(retry(f).weather.lastAttemptElapsedMs, null); assert.equal(retry(f).weather.state, 'eligible');
  await f.fetchWeather(); await f.fetchRadar(); await flush();
  assert.equal(wxCalls(f), 1, 'first-ever weather acquisition eligible immediately at elapsed 0');
  assert.equal(radarCalls(f), 1, 'first-ever radar acquisition eligible immediately at elapsed 0');
  assert.equal(retry(f).weather.lastAttemptElapsedMs, 0); assert.equal(retry(f).weather.state, 'cooldown');
  t.elapse(59999); await f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 1, 'an attempt at elapsed 0 is a real attempt');
  t.elapse(1); await f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 2);
}
// Weather and radar keep distinct records.
async function independent(mod = base) {
  const { f, t } = setup({ mod, mono: 0, weather: 'fail', radar: 'fail' });
  await f.fetchWeather(); await flush(); t.elapse(30000);
  await f.fetchRadar(); await flush(); assert.equal(radarCalls(f), 1, 'a weather attempt does not start the radar cooldown');
  t.elapse(30000); await f.fetchWeather(); await f.fetchRadar(); await flush();
  assert.equal(wxCalls(f), 2); assert.equal(radarCalls(f), 1, 'weather eligibility does not release radar');
  assert.equal(retry(f).radar.lastAttemptElapsedMs, 30000); assert.equal(retry(f).weather.lastAttemptElapsedMs, 60000);
  t.elapse(569999); await f.fetchRadar(); await flush(); assert.equal(radarCalls(f), 1);
  t.elapse(1); await f.fetchRadar(); await flush(); assert.equal(radarCalls(f), 2);
}
// D2: without performance.now the existing Date.now fallback is used, disclosed as degraded wall-clock spacing.
async function fallbackHost(mod = base, S = 5 * 60000) {
  // A failing provider keeps evidence out of the way: with accepted evidence the wall catch-up also makes the old
  // receipt eligible again, so the shortcut (not spacing) would decide.
  const f = mod.fixture({ fetch: transport(mod, { weather: 'fail', radar: 'fail' }) }); f.context.performance = {};
  const r0 = retry(f); assert.equal(r0.clock, 'wall-fallback'); assert.match(r0.guarantee, /degraded/);
  await f.fetchWeather(); await f.fetchRadar(); await flush(); assert.equal(wxCalls(f), 1); assert.equal(radarCalls(f), 1);
  assert.equal(retry(f).weather.clock, 'wall-fallback'); assert.equal(retry(f).weather.lastAttemptElapsedMs, NOW, 'fallback stamp is wall time');
  f.clock.now -= S;                                              // the only clock available is corrected backwards
  f.clock.now += 60000; await f.fetchWeather(); await flush();
  assert.equal(wxCalls(f), 1, 'documented degraded guarantee: wall fallback spacing follows the corrected wall clock');
  assert.equal(retry(f).weather.nextEligibleInMs, S, 'diagnostic discloses the extra wait instead of claiming monotonic spacing');
  f.clock.now += S; await f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 2);
  assert.equal(retry(f).clock, 'wall-fallback');
}
// ES0D-08: an active owner prevents overlap across a wall step; its elapsed deadline is unchanged; a stale
// attempt's late settlement cannot release or overwrite the successor.
async function ownershipAcrossStep(mod = base, S = -3600000) {
  const first = deferred(), second = deferred(); let n = 0;
  const { f, t } = setup({ mod, weather: () => ++n === 1 ? first.promise : second.promise });
  const a = f.fetchWeather(); await flush(); assert.equal(f.read().wxBusy, true);
  t.step(S); await f.fetchWeather(); assert.equal(wxCalls(f), 1, 'busy owner prevents overlap after a wall step');
  t.elapse(9999); await flush(); assert.equal(f.read().wxBusy, true, 'elapsed deadline unchanged by the wall step');
  t.elapse(1); await a; assert.equal(f.read().wxBusy, false);
  t.elapse(50000); const b = f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 2); assert.equal(f.read().wxBusy, true);
  first.resolve(response(livePayload(mod.healthy, NOW))); await flush();
  assert.equal(f.read().wxBusy, true, 'stale attempt cannot release the successor'); assert.equal(f.read().weather, null);
  second.resolve(response(livePayload(mod.healthy, f.clock.now))); await b;
  assert.equal(f.read().wxBusy, false); assert.equal(f.view().qa.cache.currentEligible, true); assert.equal(t.pending.size, 0);
}
// ES0D-08: a superseded attempt's late error/finally cannot release the successor's busy owner.
async function supersededFinally(mod = base) {
  const old = deferred(), next = deferred(); let n = 0;
  const { f } = setup({ mod, weather: () => ++n === 1 ? old.promise : next.promise });
  const a = f.fetchWeather(); await flush();
  f.set({ lat: 30, lon: 0, lastWxTry: 0, lastRadarAt: 0, retry: { weather: null, radar: null } }); f.beginRuntimeGeneration();  // the resetForNewLocation pair
  const b = f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 2);
  old.resolve({ ok: false, status: 500 }); await a; await flush();
  assert.equal(f.read().wxBusy, true, 'obsolete finally cannot release the successor');
  next.resolve(response(livePayload(mod.healthy, f.clock.now))); await b; assert.equal(f.read().wxBusy, false);
}
// ES0D-06/09: ordinary cadence without clock steps; healthy current+track suppresses duplicates.
async function ordinaryCadence(mod = base) {
  const { f, t } = setup({ mod });
  await f.fetchWeather(); await f.fetchRadar(); await flush();
  for (let i = 1; i <= 29; i++) { t.elapse(30000); await f.fetchWeather(); await f.fetchRadar(); await flush(); }
  assert.equal(t.mono, 871000); assert.equal(wxCalls(f), 1, 'healthy current+track suppresses duplicate weather requests');
  assert.equal(radarCalls(f), 2, 'radar refreshes once after 600 000 ms');
  assert.equal(retry(f).weather.state, 'fresh-data-satisfied');
  t.elapse(30001); await f.fetchWeather(); await flush(); assert.equal(wxCalls(f), 2, 'expired evidence no longer suppresses');
}

module.exports = { load, base, NOW, setup, clocks, transport, livePayload, response, deferred, flush, wxCalls, radarCalls, retry, weatherRollback, radarRollback, boundary, forwardNoStorm, zeroIsAttempt, independent, fallbackHost, ownershipAcrossStep, supersededFinally, ordinaryCadence };
