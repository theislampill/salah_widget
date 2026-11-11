'use strict';
// R000D / issue #13 ES0D source controls. Scenarios live in weather-retry-clock-fixture.cjs (shared with the
// mutation controls); see that file for the clock/transport model and its limits.
const assert = require('node:assert/strict'), { test } = require('node:test');
const { base, NOW, setup, clocks, transport, flush, wxCalls, radarCalls, retry, weatherRollback, radarRollback, boundary,
  forwardNoStorm, zeroIsAttempt, independent, fallbackHost, ownershipAcrossStep, supersededFinally, ordinaryCadence } = require('./weather-retry-clock-fixture.cjs');

for (const S of [5 * 60000, 2 * 3600000]) {
  test('ES0D-01/05/14 weather: backward wall step ' + S / 60000 + ' min still allows a replacement after 60 s elapsed', () => weatherRollback(base, S));
  test('ES0D-02/05/14 radar: backward wall step ' + S / 60000 + ' min still allows a replacement after 600 s elapsed', () => radarRollback(base, S));
}
for (const kind of ['weather', 'radar']) for (const step of [0, -3600000, 3600000])
  test('ES0D-03 ' + kind + ' boundary is inclusive on the elapsed clock (wall step ' + step / 60000 + ' min)', () => boundary(base, kind, step));
test('ES0D-07 forward wall jump: no early retry, no per-frame storm, one request per elapsed interval', () => forwardNoStorm(base));
test('ES0D-04 unset sentinel: first-ever acquisition is immediate and elapsed zero is a real attempt', () => zeroIsAttempt(base));
test('ES0D-13 weather and radar retry records are independent', () => independent(base));
test('D2 fallback host: Date.now fallback is identified as degraded wall-clock spacing', () => fallbackHost(base));
test('ES0D-08 control: active owner, elapsed deadline and stale attempt without a wall step', () => ownershipAcrossStep(base, 0));
test('ES0D-08 active owner, elapsed deadline and stale attempt across a backward wall step', () => ownershipAcrossStep(base, -3600000));
test('ES0D-08 superseded attempt error/finally cannot release the successor', () => supersededFinally(base));
test('ES0D-06/09 ordinary cadence and healthy shortcut without clock steps', () => ordinaryCadence(base));

test('ES0D-15 diagnostics name the clock domain, elapsed stamps and reason, without inventing source time', async () => {
  const { f, t } = setup({ weather: 'fail', radar: 'fail' });
  let r = retry(f);
  assert.equal(r.clock, 'monotonic'); assert.match(r.guarantee, /elapsed/);
  assert.deepEqual(r.weather, { state: 'eligible', intervalMs: 60000, lastAttemptElapsedMs: null, nextEligibleInMs: 0, clock: null });
  assert.deepEqual(r.radar, { state: 'eligible', intervalMs: 600000, lastAttemptElapsedMs: null, nextEligibleInMs: 0, clock: null });
  await f.fetchWeather(); await flush(); t.step(-3600000); t.elapse(20000);
  r = retry(f);
  assert.deepEqual(r.weather, { state: 'cooldown', intervalMs: 60000, lastAttemptElapsedMs: 1000, nextEligibleInMs: 40000, clock: 'monotonic' });
  assert.equal(r.radar.state, 'eligible');
  const q = f.view().qa; assert.equal(q.cache.lastWeatherRefresh, null, 'a failed attempt is not a receipt');
  assert.equal(q.wxTruth.requests.weather.state, 'unavailable');
  const busy = setup({ weather: () => new Promise(() => {}) }); busy.f.fetchWeather(); await flush();
  assert.equal(retry(busy.f).weather.state, 'active-owned-attempt');
  const sim = setup({ opts: { sim: { wx: 95 } } }); assert.equal(retry(sim.f).weather.state, 'suppressed-by-mode'); assert.equal(retry(sim.f).radar.state, 'suppressed-by-mode');
  const off = setup({ opts: { lat: 95 } }); assert.equal(retry(off.f).weather.state, 'target-ineligible');
  await off.f.fetchWeather(); await off.f.fetchRadar(); assert.equal(off.f.calls.length, 0);
});
test('ES0D-10 SIM and invalid-target suppression intact; acquisition adds no timer loop', async () => {
  const sim = setup({ opts: { sim: { wx: 95 } } }); await sim.f.fetchWeather(); await sim.f.fetchRadar(); assert.equal(sim.f.calls.length, 0);
  const { f, t } = setup(); await f.fetchWeather(); await f.fetchRadar(); await flush();
  assert.equal(t.pending.size, 0, 'no timer survives a settled acquisition');
  const region = base.source.slice(base.source.indexOf('// ---- weather (Open-Meteo:'), base.source.indexOf('// ---- accurate Moon position'));
  assert(region.length > 0); assert(!/setInterval|requestAnimationFrame/.test(region), 'weather acquisition owns no interval/frame loop');
});
test('ES0D-12 reload: a new document starts unset; the UTC cache keeps its meaning and stores no elapsed stamp', async () => {
  const a = setup({ mono: 500000 }); await a.f.fetchWeather(); await a.f.fetchRadar(); await flush();
  const stored = [...a.f.storage].filter(([k]) => k.startsWith('salahwx:'));
  assert.equal(stored.length, 1); assert.deepEqual(Object.keys(JSON.parse(stored[0][1])).sort(), ['ts', 'w']);
  assert.equal(JSON.parse(stored[0][1]).ts, NOW);
  const b = base.fixture({ fetch: transport(base), storage: stored }); clocks(b, 0);
  b.loadWx(); assert.equal(b.view().qa.cache.currentEligible, true, 'UTC cache admitted by its own UTC rules');
  assert.equal(retry(b).weather.lastAttemptElapsedMs, null); assert.equal(retry(b).radar.lastAttemptElapsedMs, null);
  await b.fetchWeather(); await b.fetchRadar(); await flush();
  assert.equal(wxCalls(b), 1, 'cached current without a track is not a fresh-data shortcut'); assert.equal(radarCalls(b), 1);
});

// ---- lifecycle owners through the R0003 harness (real applyConfig/resetForNewLocation/startRenderLoop) ----
const { harness, record, cfg } = require('./r0003-harness.cjs');
test('ES0D-11 hidden/resume creates one ordinary poll opportunity, not a backlog', async () => {
  const h = harness(); h.seed(record(), record('08-09-2026'));
  h.run('globalThis.__polls={weather:0,radar:0};fetchWeather=()=>{__polls.weather++;};fetchRadar=()=>{__polls.radar++;};');
  h.run('startRenderLoop()'); await h.frame();
  await h.advance(31000); await h.frame(); assert.deepEqual({ ...h.run('__polls') }, { weather: 1, radar: 1 });
  h.hide(); await h.advance(31000 + 3600000); assert.equal(h.frames.size, 0, 'no background poll while hidden');
  assert.deepEqual({ ...h.run('__polls') }, { weather: 1, radar: 1 });
  h.show(); await h.frame(); await h.frame(); await h.frame();
  assert.deepEqual({ ...h.run('__polls') }, { weather: 2, radar: 2 }, 'one opportunity on resume, not one per missed interval');
});
test('ES0D-13 current config contract: a units-only or coordinate change retires both records; appearance-only keeps them', async () => {
  for (const next of [cfg(10, '10', { units: 'c' }), cfg(20, '20')]) {
    const h = harness(); h.seed(record(), record('08-09-2026')); h.apply(cfg(10, '10')); await h.settle();
    h.run('_wxRetry.weather={startedAt:5,clock:"monotonic"};_wxRetry.radar={startedAt:7,clock:"monotonic"};');
    h.apply(next); await h.settle();
    assert.deepEqual({ ...h.run('({w:_wxRetry.weather,r:_wxRetry.radar})') }, { w: null, r: null });
  }
  const h = harness(); h.seed(record(), record('08-09-2026')); h.apply(cfg(10, '10')); await h.settle();
  h.run('_wxRetry.weather={startedAt:5,clock:"monotonic"};_wxRetry.radar={startedAt:7,clock:"monotonic"};');
  h.apply(cfg(10, '10', { appearance: 'contrast' })); await h.settle();
  assert.deepEqual(JSON.parse(h.run('JSON.stringify(_wxRetry)')), { weather: { startedAt: 5, clock: 'monotonic' }, radar: { startedAt: 7, clock: 'monotonic' } });
});

