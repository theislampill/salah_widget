'use strict';
// R000D mutation controls. Each disposable in-memory mutant of the generated runtime reaches the same real
// consumer scenario as its healthy run and must fail an actual assertion (setup errors are not detection).
// No mutated source is written to disk.
const { test } = require('node:test'), assert = require('node:assert/strict');
const S = require('./weather-retry-clock-fixture.cjs'), source = S.base.source;
const cases = [
  ['m1 restore wall cooldown (weather)', 'const now=Date.now(), elapsed=_RAFNOW();\n  if(retryGate("weather"', 'const now=Date.now(), elapsed=Date.now();\n  if(retryGate("weather"', m => S.weatherRollback(m)],
  ['m1 restore wall cooldown (radar)', 'const now=Date.now(), elapsed=_RAFNOW();\n  if(retryGate("radar"', 'const now=Date.now(), elapsed=Date.now();\n  if(retryGate("radar"', m => S.radarRollback(m)],
  ['m2 elapsed zero treated as unset', 'if(r!==null&&elapsed-r.startedAt<', 'if(r&&r.startedAt&&elapsed-r.startedAt<', m => S.zeroIsAttempt(m)],
  ['m2 unset sentinel stored as elapsed zero', '_wxRetry={weather:null,radar:null};', '_wxRetry={weather:{startedAt:0,clock:"monotonic"},radar:{startedAt:0,clock:"monotonic"}};', m => S.zeroIsAttempt(m)],
  ['m3 weather and radar share one record', 'const r=_wxRetry[kind]; if(r!==null', 'const r=_wxRetry.weather; if(r!==null', m => S.independent(m)],
  ['m4 boundary off by one', '<(kind==="weather"?_WX_RETRY:_RADAR_REFRESH)) return "cooldown";', '<=(kind==="weather"?_WX_RETRY:_RADAR_REFRESH)) return "cooldown";', m => S.boundary(m, 'weather', 0)],
  ['m5 fallback silently reported as monotonic', '?"monotonic":"wall-fallback"; }', '?"monotonic":"monotonic"; }', m => S.fallbackHost(m)],
  ['substitute simulated time', 'const now=Date.now(), elapsed=_RAFNOW();\n  if(retryGate("weather"', 'const now=Date.now(), elapsed=simNow();\n  if(retryGate("weather"', m => S.weatherRollback(m)],
  ['accept negative receipt shortcut', 'selectedWeather(now)&&weatherTrack&&now-lastWxAt<_WX_CURRENT_TTL', 'weather&&weatherTrack&&now-lastWxAt<_WX_CURRENT_TTL', m => S.weatherRollback(m, 5 * 60000)],
  ['old finally clears successor', 'finally{ finishAttempt(op,a); if(finishRequest(op)) wxBusy=false; }', 'finally{ finishAttempt(op,a); finishRequest(op); wxBusy=false; }', m => S.supersededFinally(m)],
  ['retry every frame', '_wxRetry.weather={startedAt:elapsed,clock:retryClockDomain()};', '_wxRetry.weather=null;', m => S.forwardNoStorm(m)],
  ['negative control: relax freshness to mask the stranded retry', 'sourceAge>=0&&sourceAge<=_WX_CURRENT_TTL&&receiptAge>=0&&receiptAge<=_WX_CURRENT_TTL', 'sourceAge<=_WX_CURRENT_TTL&&receiptAge<=_WX_CURRENT_TTL', m => S.weatherRollback(m)],
];
for (const [name, from, to, discriminator] of cases) test('R000D mutation discriminator: ' + name, async () => {
  assert.equal(source.split(from).length, 2, 'one declared mutation location');
  await discriminator(S.base);
  const mutant = S.load(source.replace(from, to));
  await assert.rejects(() => discriminator(mutant), error => error instanceof assert.AssertionError, 'only an actual assertion failure detects the mutant');
});
