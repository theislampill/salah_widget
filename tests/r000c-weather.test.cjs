'use strict';
// Source-bound no-build WEATHER regressions. Network, image loading, wall clock and DOM are
// contained doubles; admission, cache, temporal converter, gate, atmosphere and paint are real.
// This is consumer logic evidence, not a browser/pixel or provider-coverage qualification.
const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const sourcePath = process.env.SALAH_WEATHER_SOURCE || path.join(__dirname, '..', 'index.html');
const source = fs.readFileSync(sourcePath, 'utf8');
const configSource = fs.readFileSync(path.join(__dirname, '..', 'config.js'), 'utf8');
const NOW = Date.parse('2026-09-07T21:00:00Z');
console.log('WEATHER source ' + sourcePath + ' SHA256 ' + crypto.createHash('sha256').update(source).digest('hex'));

function region(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a + start.length);
  assert(a >= 0 && b > a, 'actual source region missing: ' + start);
  return source.slice(a, b);
}
const runtime = [
  region('// ---- SINGLE TEMPORAL SOURCE OF TRUTH', '// ---- prayer-times data:'),
  region('// ---- weather (Open-Meteo:', '// ---- accurate Moon position'),
  region('const lerp =', '// QUARANTINED:'),
  region('const _ss=t=>', '\n'),
  region('const _PRECIP_MIN=', '// ---- CLOUD ENGINE:'),
  region('function atmosphere(M){', '// paint(A)'),
  region('function applyCloudState(A){', '// Size the present-prayer name'),
  region('window.qaState=function(){', '// debugMotion telemetry'),
].join('\n');

function healthy(overrides = {}) {
  return {
    elevation: 100,
    current: {
      time: '2026-09-07T21:00', interval: 900, weather_code: 95,
      temperature_2m: 20, apparent_temperature: 19, relative_humidity_2m: 90,
      dew_point_2m: 18, wind_speed_10m: 2, wind_direction_10m: 180,
      wind_gusts_10m: 4, cloud_cover: 95, precipitation: 2, is_day: 1,
      ...overrides,
    },
    hourly: {
      time: ['2026-09-07T21:00', '2026-09-07T22:00'],
      temperature_2m: [20, 19], weather_code: [95, 3],
      wind_direction_10m: [180, 180], precipitation: [2, 0],
    },
  };
}

function fixture(options = {}) {
  const opts = { lat: 24.47, lon: 39.61, units: 'c', zone: 'UTC', ...options };
  const clock = { now: NOW }, calls = [], images = [], storage = new Map(opts.storage || []);
  class ClockDate extends Date {
    constructor(...args) { super(...(args.length ? args : [clock.now])); }
    static now() { return clock.now; }
  }
  const nodes = new Map();
  function element() {
    const props = new Map();
    return { dataset: {}, textContent: '', title: '', style: {
      setProperty(k, v) { props.set(k, String(v)); },
      getPropertyValue(k) { return props.get(k) || ''; },
    } };
  }
  const pixels = new Uint8ClampedArray(256 * 256 * 4);
  for (let i = 0; i < pixels.length; i += 4) pixels.set(opts.rgba || [82, 147, 196, 255], i);
  if (opts.sparse) {
    pixels.fill(0);
    // Madinah zoom-6 site pixel independently established as (10,130).
    for (const [dx, dy] of [[3, 3], [3, 2], [2, 3]]) pixels.set([82, 147, 196, 255], ((130 + dy) * 256 + 10 + dx) * 4);
  }
  const canvas = { width: 256, height: 256, getContext: () => ({
    drawImage() {}, getImageData() { if (opts.canvasError) throw Error('contained canvas error'); return { data: pixels }; },
  }) };
  const document = {
    querySelector(selector) { if (selector === '.cloudcanvas') return canvas; if (!nodes.has(selector)) nodes.set(selector, element()); return nodes.get(selector); },
    createElement(tag) { assert.equal(tag, 'canvas'); return canvas; },
  };
  class ImageDouble {
    set src(url) { images.push(url); queueMicrotask(() => opts.imageError ? this.onerror() : this.onload()); }
  }
  const context = vm.createContext({
    opts, Date: ClockDate, URLSearchParams, AbortController, Intl, console, setTimeout, clearTimeout,
    performance: { now: () => clock.now - NOW }, document, Image: ImageDouble,
    localStorage: { getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v) },
    getComputedStyle: el => el.style,
    fetch: async url => {
      calls.push(url);
      if (opts.fetch) return opts.fetch(url, clock);
      if (url.includes('open-meteo')) {
        if (opts.offline) throw Error('contained offline');
        return { ok: opts.ok !== false, status: opts.status || 200, json: async () => {
          if (opts.jsonError) throw Error('contained malformed JSON');
          return Object.hasOwn(opts, 'payload') ? opts.payload : healthy();
        } };
      }
      assert.equal(url, 'https://api.rainviewer.com/public/weather-maps.json');
      const frame = opts.frameSec ?? clock.now / 1000;
      return { ok: opts.radarOk !== false, status: opts.radarOk === false ? 500 : 200, json: async () => Object.hasOwn(opts, 'manifest') ? opts.manifest : ({
        generated: opts.indexSec ?? clock.now / 1000, host: 'https://tilecache.rainviewer.com',
        radar: { past: [{ time: frame, path: '/v2/radar/' + frame }] },
      }) };
    },
    isDayNow: () => true, sunMetrics: () => ({ altDeg: 45, x: 15, y: 12 }),
    skyLum: () => 1, _airDrift: () => 0.5, mwGeom: () => ({ alt: 10, H: 0 }),
    moonNow: () => ({ frac: 0.6, waxing: true }),
    physSky: () => ({ g1: [90, 130, 160], g2: [100, 140, 170], g3: [120, 150, 170],
      glow: [200, 170, 130, 0.2], hor: [200, 170, 130, 0.2], stars: 0,
      accent: [200, 170, 120], accent2: [200, 170, 120], text: [240, 240, 240] }),
    model: () => ({ nowMin: 1260, noon: 720 }), isMotionReduced: () => false,
  });
  context.window = context;
  vm.runInContext(`
    let lat=opts.lat, lon=opts.lon, units=opts.units, tz=opts.zone;
    const SIM={wx:null,time:null,moon:null,...opts.sim}, q=new URLSearchParams(opts.hash||'');
    const clamp=x=>Math.min(1,Math.max(0,x)), enc=encodeURIComponent, pad=n=>String(n).padStart(2,'0');
    const $=s=>document.querySelector(s), DEBUGOPTIC=null, DEBUGLAYERS=false, LPOLL=0;
    let moonSky={alt:20,H:0,_min:1260,sx:.84,sy:.1};
    let cloudState={covLow:0,covMid:0,covHigh:0}, _cloudReady=false, _cloudDirty=false, _cloudFieldSeed=1;
    let _starEls=[], lastDate=null, today=null, tomorrow=null, _prayerStale=false, _rolloverNextTry=0, _lastRender=null;
    let _hashCfg={}, _cfgMode='hardcoded', CONFIG=null, label='', _autoDetectSource=null, _autoDetectStatus='idle';
    let _storageErr=null, _geoPermission='unknown', _geoLastError=null;
  ` + runtime + `
    globalThis.api={fetchWeather,fetchRadar,loadWx,wxAt,syncWeather,wxDrivers,gateWeatherCode,wxClass,radarPrecipNow,
      read:()=>({weather,weatherTrack,weatherRadar,lastWxAt,lastWxTry,wxBusy,radarBusy,siteElev}),
      set:(values)=>{if('lat' in values)lat=values.lat;if('lon' in values)lon=values.lon;if('units' in values)units=values.units;
        if('zone' in values)tz=values.zone;if('weather' in values)weather=values.weather;if('lastWxAt' in values)lastWxAt=values.lastWxAt;
        if('weatherTrack' in values)weatherTrack=values.weatherTrack;if('wxBusy' in values)wxBusy=values.wxBusy;
        if('radarBusy' in values)radarBusy=values.radarBusy;if('lastWxTry' in values)lastWxTry=values.lastWxTry;
        if('lastRadarAt' in values)lastRadarAt=values.lastRadarAt;},
      view:()=>{const a=atmosphere(model());paint(a);return {a,qa:window.qaState()};}
    };
  `, context, { filename: sourcePath });
  vm.runInContext(configSource, context, { filename: 'config.js' });
  for (const fn of ['fetchWeather', 'fetchRadar', 'loadWx', 'wxAt', 'syncWeather', 'wxDrivers', 'gateWeatherCode', 'radarPrecipNow']) assert.equal(typeof context.api[fn], 'function', 'real entrypoint missing ' + fn);
  return { ...context.api, context, clock, calls, images, storage, nodes,
    cache: () => JSON.parse(storage.get('salahwx:' + opts.lat + '|' + opts.lon + '|' + opts.units) || 'null'),
  };
}

test('control: actual fresh acquisition, model gate, atmosphere and chip are reached', async () => {
  const f = fixture(); await f.fetchWeather();
  assert.equal(f.read().weather.temp, 20); assert.equal(f.read().weatherTrack.ep[0], NOW);
  assert.equal(f.cache().w.temp, 20); assert.equal(f.read().wxBusy, false);
  const view = f.view(); assert.equal(view.a.cls, 'thunder'); assert.equal(f.nodes.get('#wt').textContent, '20°');
  assert.equal(view.qa.wxTruth.finalDataFx, 'thunder');
});

for (const [name, input, want] of [['null', null, null], ['missing', undefined, null], ['zero', 0, 0], ['negative', -12.5, -12]]) {
  test('R000C temperature ' + name + ' survives acquisition/cache/paint without coercion', async () => {
    const f = fixture({ payload: healthy({ temperature_2m: input }) }); await f.fetchWeather();
    assert.equal(f.read().weather.temp, want); assert.equal(f.cache().w.temp, want);
    f.view(); assert.equal(f.nodes.get('#wt').textContent, want == null ? '' : want + '°');
  });
}
test('R000C negative Fahrenheit remains request-bound', async () => {
  const f = fixture({ units: 'f', payload: healthy({ temperature_2m: -8, apparent_temperature: -10 }) });
  await f.fetchWeather(); assert.equal(f.read().weather.temp, -8); assert.equal(f.read().weather.units, 'f');
  assert.equal(new URL(f.calls[0]).searchParams.get('temperature_unit'), 'fahrenheit');
});
test('R000C HTTP 500 healthy-shaped body cannot mutate any admitted state', async () => {
  const f = fixture({ ok: false, status: 500 }); await f.fetchWeather();
  assert.equal(f.read().weather, null); assert.equal(f.read().weatherTrack, null);
  assert.equal(f.read().lastWxAt, 0); assert.equal(f.read().siteElev, 0); assert.equal(f.cache(), null);
});
test('R000C historical malformed 500 lookalike is rejected before mutation', async () => {
  const f = fixture({ ok: false, status: 500, payload: { elevation: 'invalid', current: {
    weather_code: 999, temperature_2m: null, precipitation: 'Infinity' }, hourly: { time: ['invalid'] } } });
  await f.fetchWeather(); assert.equal(f.read().weather, null); assert.equal(f.read().weatherTrack, null);
  assert.equal(f.read().siteElev, 0); assert.equal(f.read().lastWxAt, 0); assert.equal(f.read().wxBusy, false);
});
test('control: ordinary HTTP 400 provider error is unavailable', async () => {
  const f = fixture({ ok: false, status: 400, payload: { error: true, reason: 'bad request' } });
  await f.fetchWeather(); assert.equal(f.read().weather, null); assert.equal(f.read().wxBusy, false);
});
for (const [name, opts] of [['null root', { payload: null }], ['array root', { payload: [] }],
  ['provider error', { payload: { ...healthy(), error: true } }], ['bad JSON', { jsonError: true }]]) {
  test('R000C successful transport with ' + name + ' does not renew prior valid state', async () => {
    let fail = false;
    const f = fixture({ fetch: async () => ({ ok: true, status: 200, json: async () => {
      if (!fail) return healthy();
      if (opts.jsonError) throw Error('contained JSON failure');
      return opts.payload;
    } }) });
    await f.fetchWeather(); const prior = f.read().weather; const stored = f.storage.get('salahwx:24.47|39.61|c');
    fail = true; f.clock.now += 900001; await f.fetchWeather();
    assert.equal(f.read().weather, prior); assert.equal(f.read().lastWxAt, NOW);
    assert.equal(f.storage.get('salahwx:24.47|39.61|c'), stored); assert.equal(f.read().wxBusy, false);
    assert.equal(f.view().a.wxTemp, null);
  });
}
for (const code of [999, '95', -1, 95.5]) test('R000C invalid current WMO code ' + code + ' never becomes current', async () => {
  const f = fixture({ payload: healthy({ weather_code: code }) }); await f.fetchWeather();
  assert.equal(f.read().weather, null); assert.equal(f.read().lastWxAt, 0); assert(f.read().weatherTrack);
  assert.equal(f.view().a.wxTemp, null);
});
for (const [name, value, want] of [['string', 'Infinity', null], ['nan', NaN, null], ['infinite', Infinity, null], ['negative', -1, null], ['missing', undefined, null], ['zero', 0, 0]]) {
  test('R000C precipitation ' + name + ' preserves unknown versus quantitative zero', async () => {
    const f = fixture({ payload: healthy({ precipitation: value }) }); await f.fetchWeather();
    assert.equal(f.read().weather.precip, want); assert.equal(f.view().a.cls, 'overcast');
    assert.equal(f.gateWeatherCode(95, { precip: value, cloud: 95 }, 0), 3);
  });
}
test('R000C invalid optional fields and elevation cannot poison drivers', async () => {
  const payload = healthy({ relative_humidity_2m: 101, cloud_cover: -1, wind_direction_10m: 361,
    wind_speed_10m: '2', wind_gusts_10m: -1, visibility: -1, is_day: 2 }); payload.elevation = 'invalid';
  const f = fixture({ payload }); await f.fetchWeather();
  for (const k of ['rh', 'cloud', 'windDir', 'wind', 'gust', 'vis', 'isDay']) assert.equal(f.read().weather[k], null);
  assert.equal(f.read().siteElev, 0); for (const v of Object.values(f.wxDrivers())) assert(Number.isFinite(v));
});
test('control: field domain boundaries and negative elevation remain valid', async () => {
  const payload = healthy({ relative_humidity_2m: 0, cloud_cover: 100, wind_direction_10m: 360,
    wind_speed_10m: 0, wind_gusts_10m: 0, visibility: 0, is_day: 0 }); payload.elevation = -100;
  const f = fixture({ payload }); await f.fetchWeather();
  assert.equal(f.read().weather.rh, 0); assert.equal(f.read().weather.vis, 0); assert.equal(f.read().siteElev, -100);
});
for (const block of ['current', 'hourly']) test('R000C contradictory ' + block + ' units reject only that block', async () => {
  const payload = healthy(); payload[block + '_units'] = { temperature_2m: '°F', wind_speed_10m: 'm/s' };
  const f = fixture({ payload }); await f.fetchWeather();
  assert.equal(f.read()[block === 'current' ? 'weather' : 'weatherTrack'], null);
  assert(f.read()[block === 'current' ? 'weatherTrack' : 'weather']);
});
for (const block of ['current', 'hourly']) {
  test('R000C advertised radians cannot be consumed as degrees in ' + block, async () => {
    const payload = healthy({ wind_direction_10m: 2 }); payload.hourly.wind_direction_10m = [2, 2];
    payload[block + '_units'] = { wind_direction_10m: 'rad' };
    const f = fixture({ payload }); await f.fetchWeather();
    assert.equal(f.read()[block === 'current' ? 'weather' : 'weatherTrack'], null);
    assert(f.read()[block === 'current' ? 'weatherTrack' : 'weather']);
    if (block === 'current') assert.equal(f.view().a.wxTemp, null);
    else assert.equal(f.wxAt(NOW + 1800000), null);
  });
  for (const [name, meta] of [['advertised degrees', { wind_direction_10m: '°' }], ['missing direction units', {}]]) {
    test('control: ' + name + ' keep ' + block + ' wind direction usable', async () => {
      const payload = healthy({ wind_direction_10m: 90 }); payload.hourly.wind_direction_10m = [90, 90];
      payload[block + '_units'] = meta;
      const f = fixture({ payload }); await f.fetchWeather();
      assert(f.read().weather); assert(f.read().weatherTrack);
      if (block === 'current') {
        assert.equal(f.read().weather.windDir, 90); assert.equal(f.wxDrivers().windX, -1);
      } else assert.equal(f.wxAt(NOW + 1800000).windDir, 90);
    });
  }
}
for (const [name, change] of [
  ['mismatched required array', h => { h.temperature_2m = [20]; }],
  ['mismatched optional array', h => { h.visibility = [20000]; }],
  ['non-array optional', h => { h.visibility = 20000; }],
  ['null optional array', h => { h.visibility = null; }],
  ['invalid calendar', h => { h.time[1] = '2026-02-30T22:00'; }],
  ['duplicate epoch', h => { h.time[1] = h.time[0]; }],
  ['decreasing epoch', h => { h.time.reverse(); }],
  ['malformed time', h => { h.time[1] = 'invalid'; }],
]) test('R000C bad hourly ' + name + ' cannot discard good current', async () => {
  const payload = healthy(); change(payload.hourly); const f = fixture({ payload }); await f.fetchWeather();
  assert(f.read().weather); assert.equal(f.read().weatherTrack, null);
});
test('R000C missing optional arrays and two null endpoints stay null at actual wxAt', async () => {
  const payload = healthy(); payload.hourly.temperature_2m = [null, null]; delete payload.hourly.wind_direction_10m;
  const f = fixture({ payload }); await f.fetchWeather(); const w = f.wxAt(NOW + 1800000);
  assert.equal(w.temp, null); assert.equal(w.windDir, null); assert.equal(w.vis, null); assert.equal(w.isDay, null);
});
test('R000C invalid optional hourly elements cannot fabricate measurements at wxAt', async () => {
  const payload = healthy(); payload.hourly.temperature_2m = ['20', Infinity];
  payload.hourly.wind_direction_10m = [null, '180']; payload.hourly.relative_humidity_2m = [101, -1];
  const f = fixture({ payload }); await f.fetchWeather(); const w = f.wxAt(NOW + 1800000);
  assert.equal(w.temp, null); assert.equal(w.windDir, null); assert.equal(w.rh, null);
});
test('control: one interpolation neighbour and wrapping wind remain usable', async () => {
  const payload = healthy(); payload.hourly.temperature_2m = [null, 10]; payload.hourly.wind_direction_10m = [350, 10];
  const f = fixture({ payload }); await f.fetchWeather(); const w = f.wxAt(NOW + 1800000);
  assert.equal(w.temp, 10); assert(Math.abs(w.windDir) < 0.001 || Math.abs(w.windDir - 360) < 0.001);
  assert.equal(w.code, 3); assert.equal(f.wxAt(NOW - 1).code, 95); assert.equal(f.wxAt(NOW + 7200000).code, 3);
});
test('R000C cache normalization contains malformed code but healthy fetch recovers', async () => {
  const key = 'salahwx:24.47|39.61|c', raw = JSON.stringify({ w: { code: 999, temp: '0', precip: 'Infinity' }, ts: NOW });
  const f = fixture({ storage: [[key, raw]] }); f.loadWx(); assert.equal(f.read().weather, null);
  assert.equal(f.storage.get(key), raw); await f.fetchWeather(); assert.equal(f.read().weather.temp, 20);
});
test('R000B legacy zero-valued cache is retained without current authority and does not suppress fetch', async () => {
  const key = 'salahwx:24.47|39.61|c', raw = JSON.stringify({ w: { code: 0, temp: 0, precip: 0 }, ts: NOW });
  const f = fixture({ storage: [[key, raw]] }); f.loadWx(); assert.equal(f.read().weather.temp, 0);
  assert.equal(f.storage.get(key), raw); assert.equal(f.view().a.wxTemp, null);
  assert.equal(f.nodes.get('#wi').title, 'Weather unavailable'); await f.fetchWeather(); assert.equal(f.calls.length, 1);
});
test('R000B future cache receipt cannot become current weather', () => {
  const f = fixture({ storage: [['salahwx:24.47|39.61|c', JSON.stringify({ w: { code: 95, precip: 2 }, ts: NOW + 86400000 })]] });
  f.loadWx(); assert.equal(f.read().weather, null); assert.equal(f.read().lastWxAt, 0);
});
test('R000B five-hour retained legacy cache stays unavailable after 24h outage', async () => {
  const raw = JSON.stringify({ w: { code: 95, temp: 20, precip: 2, cloud: 95 }, ts: NOW - 18000000 });
  const f = fixture({ storage: [['salahwx:24.47|39.61|c', raw]], offline: true }); f.loadWx();
  assert(f.read().weather); f.clock.now += 86400000; await f.fetchWeather();
  assert.equal(f.view().a.wxTemp, null); assert.equal(f.view().a.cls, 'clear');
  assert.equal(f.view().qa.cache.weatherAgeSec, 104400); assert.equal(f.read().wxBusy, false);
});
test('R000B fresh metadata cache remains eligible and still fetches its missing hourly track', async () => {
  const w = { code: 0, temp: 0, precip: 0, currentValidAt: NOW, currentIntervalSec: 900,
    retrievedAt: NOW, units: 'c', currentZone: 'UTC', currentTime: '2026-09-07T21:00' };
  const f = fixture({ storage: [['salahwx:24.47|39.61|c', JSON.stringify({ w, ts: NOW })]] }); f.loadWx();
  assert.equal(f.view().a.wxTemp, 0); await f.fetchWeather(); assert.equal(f.calls.length, 1); assert(f.read().weatherTrack);
});
test('R000B old source with fresh download never reaches current consumers', async () => {
  const f = fixture({ payload: healthy({ time: '2026-09-07T17:00' }) }); await f.fetchWeather();
  const view = f.view(); assert.equal(view.a.wxTemp, null); assert.equal(view.a.cls, 'clear');
  assert.equal(view.a.cloudCover, 0); assert.equal(view.a.cloudLayerLow, 0); assert.equal(view.a.windSpeed, 0);
  assert.equal(f.read().lastWxAt, 0); assert.equal(view.qa.wxTruth.activeThunder, false);
});
for (const [name, changes] of [['missing time', { time: undefined }], ['bad interval', { interval: 0 }], ['future source', { time: '2026-09-07T21:01' }]]) {
  test('R000B ' + name + ' cannot supply current chip or effects', async () => {
    const f = fixture({ payload: healthy(changes) }); await f.fetchWeather();
    assert.equal(f.view().a.wxTemp, null); assert.equal(f.read().lastWxAt, 0);
  });
}
for (const [age, eligible] of [[899999, true], [900000, true], [900001, false], [-1, false]]) {
  test('R000B source-age inclusive boundary ' + age, async () => {
    const f = fixture(); await f.fetchWeather(); f.read().weather.currentValidAt = NOW - age;
    assert.equal(f.view().a.wxTemp, eligible ? 20 : null);
  });
  test('R000B receipt-age inclusive boundary ' + age, async () => {
    const f = fixture(); await f.fetchWeather(); f.read().weather.retrievedAt = NOW - age;
    assert.equal(f.view().a.wxTemp, eligible ? 20 : null);
  });
}
test('R000B current expires before offline refresh; fresh replacement restores eligibility', async () => {
  let offline = false; const f = fixture({ fetch: async () => {
    if (offline) throw Error('contained offline');
    return { ok: true, status: 200, json: async () => healthy({ time: offline ? 'invalid' : f.clock.now === NOW ? '2026-09-07T21:00' : '2026-09-07T21:16' }) };
  } });
  await f.fetchWeather(); assert.equal(f.view().a.cls, 'thunder'); f.clock.now = NOW + 960000; offline = true;
  await f.fetchWeather(); const view = f.view(); assert.equal(view.a.cls, 'clear'); assert.equal(view.a.wxTemp, null);
  assert.equal(view.a.windSpeed, 0); assert.equal(view.qa.wx.temp, null); assert.equal(view.qa.cache.weatherStale, true);
  offline = false; f.clock.now += 60001; await f.fetchWeather(); assert.equal(f.view().a.cls, 'thunder');
});
test('control: real-time clear current never becomes hourly thunder; explicit preview does', async () => {
  const payload = healthy({ weather_code: 0, precipitation: 0 }); payload.hourly.weather_code = [95, 95];
  const f = fixture({ payload }); await f.fetchWeather(); f.syncWeather(); assert.equal(f.view().a.cls, 'clear');
  const preview = fixture({ payload, hash: 'timeScale=1' }); await preview.fetchWeather(); preview.syncWeather();
  assert.equal(preview.read().weather.src, 'forecast'); assert.equal(preview.view().a.cls, 'thunder');
});
test('R000C captured request fields survive asynchronous global unit/zone changes', async () => {
  let deliver; const f = fixture({ fetch: () => new Promise(resolve => { deliver = resolve; }) });
  const pending = f.fetchWeather(); f.set({ units: 'f', zone: 'Asia/Riyadh' });
  deliver({ ok: true, status: 200, json: async () => healthy() }); await pending;
  assert(f.storage.has('salahwx:24.47|39.61|c')); assert(!f.storage.has('salahwx:24.47|39.61|f'));
  assert.equal(f.read().weather.units, 'c'); assert.equal(f.read().weather.currentZone, 'UTC');
});

for (const [name, rgba] of [['0dBZ', [130, 123, 105, 73]], ['15dBZ', [136, 221, 238, 255]],
  ['20dBZ', [0, 163, 224, 255]], ['45dBZ', [255, 68, 0, 255]], ['transparent', [0, 0, 0, 0]]]) {
  test('R000E ' + name + ' actual tile sampler never contributes quantitative authority', async () => {
    const f = fixture({ rgba }); await f.fetchRadar(); assert.equal(f.read().radarBusy, false);
    assert.equal(f.radarPrecipNow(), 0); assert.equal(f.read().weatherRadar.precipMm, 0);
    assert.equal(f.gateWeatherCode(95, { precip: 0, cloud: 95 }, f.radarPrecipNow()), 3);
  });
}
for (const [raw, precip, radar, want] of [[63, 0, 2, 3], [95, 0, 5, 3], [95, 0.3, 5, 63], [95, 2, 0, 95], [0, 0, 5, 0]]) {
  test('R000E lower-level model control ' + [raw, precip, radar].join('/') + ' -> ' + want, () => {
    const f = fixture(); assert.equal(f.gateWeatherCode(raw, { precip, cloud: 95 }, radar), want);
  });
}
test('R000E nearby sparse echoes with dry centre stay diagnostic', async () => {
  const f = fixture({ sparse: true }); await f.fetchRadar(); assert.equal(f.radarPrecipNow(), 0);
  assert.equal(f.read().weatherRadar.sample.returnCount, 3);
  assert.equal(f.gateWeatherCode(63, { precip: 0, cloud: 95 }, 2), 3);
});
for (const [name, opts] of [['HTTP failure', { radarOk: false }], ['missing frame', { manifest: { host: 'https://tilecache.rainviewer.com', generated: NOW / 1000, radar: { past: [] } } }],
  ['missing frame time', { manifest: { host: 'https://tilecache.rainviewer.com', generated: NOW / 1000, radar: { past: [{ path: '/v2/radar/' + NOW / 1000 }] } } }]]) {
  test('R000E radar ' + name + ' cannot become a readable current mosaic', async () => {
    const f = fixture(opts); await f.fetchRadar(); assert.equal(f.read().weatherRadar, null);
    assert.equal(f.read().radarBusy, false); assert.equal(f.radarPrecipNow(), 0);
  });
}
for (const [name, opts] of [['image error', { imageError: true }], ['canvas error', { canvasError: true }]]) {
  test('R000E ' + name + ' remains unavailable and releases settled attempt', async () => {
    const f = fixture(opts); await f.fetchRadar(); assert.equal(f.radarPrecipNow(), 0); assert.equal(f.read().radarBusy, false);
  });
}
test('R000B repeat-download old radar cannot renew frame validity', async () => {
  const f = fixture({ frameSec: (NOW - 14400000) / 1000 }); await f.fetchRadar();
  assert.equal(f.view().qa.wxTruth.radarFrameAgeSec, 14400); assert.equal(f.view().qa.wxTruth.radarAvailable, false);
  f.clock.now += 600001; await f.fetchRadar(); assert.equal(f.view().qa.wxTruth.radarFrameAgeSec, 15000);
  assert.equal(f.view().qa.wxTruth.radarAgeSec, 0); assert.equal(f.view().qa.wxTruth.radarAvailable, false);
});
for (const [age, available] of [[1199999, true], [1200000, true], [1200001, false], [-1, false]]) {
  test('R000B radar frame-age inclusive boundary ' + age, async () => {
    const f = fixture({ frameSec: (NOW - age) / 1000 }); await f.fetchRadar();
    assert.equal(f.view().qa.wxTruth.radarAvailable, available); assert.equal(f.radarPrecipNow(), 0);
  });
  test('R000B radar receipt-age inclusive boundary ' + age, async () => {
    const f = fixture(); await f.fetchRadar(); f.read().weatherRadar.retrievedAt = NOW - age;
    assert.equal(f.view().qa.wxTruth.radarAvailable, available); assert.equal(f.radarPrecipNow(), 0);
  });
}
for (const [lat, lon, tile] of [[0, 30, '/37/32/'], [30, 0, '/32/26/'], [0, 0, '/32/32/'], [-0, -0, '/32/32/'], [0.000001, 30, '/37/31/'], [24.47, 39.61, '/39/27/']]) {
  test('R001E both real acquisitions preserve coordinate ' + lat + ',' + lon, async () => {
    const f = fixture({ lat, lon }); await f.fetchWeather(); await f.fetchRadar(); assert.equal(f.calls.length, 2);
    const url = new URL(f.calls[0]); assert.equal(url.origin + url.pathname, 'https://api.open-meteo.com/v1/forecast');
    assert.equal(url.searchParams.get('latitude'), String(lat)); assert.equal(url.searchParams.get('longitude'), String(lon));
    assert.equal(url.searchParams.get('wind_speed_unit'), 'ms'); assert.equal(url.searchParams.get('timezone'), 'UTC');
    assert.equal(f.images.length, 1); assert(f.images[0].includes('/256/6' + tile));
  });
}
for (const [lat, lon] of [[null, 30], [undefined, 30], [NaN, 30], [Infinity, 30], [-Infinity, 30],
  [91, 30], [-91, 30], [30, 181], [30, -181], [30, null], [30, NaN], ['0', 30]]) {
  test('R001E direct invalid runtime pair ' + String(lat) + ',' + String(lon) + ' never dispatches', async () => {
    const f = fixture({ lat, lon }); await f.fetchWeather(); await f.fetchRadar(); assert.equal(f.calls.length, 0);
  });
}
test('R001E real config normalizer still admits raw string zero and preserves clamping', async () => {
  const f = fixture(); const normalize = f.context.SalahConfig.normalize;
  const cfg = normalize({ lat: '0', lon: '0' }); assert.equal(f.context.SalahConfig.validate(cfg).ok, true);
  assert.equal(cfg.lat, 0); assert.equal(cfg.lon, 0); f.set(cfg); await f.fetchWeather(); await f.fetchRadar(); assert.equal(f.calls.length, 2);
  const clamped = normalize({ lat: 100, lon: 200 }); assert.equal(clamped.lat, 90); assert.equal(clamped.lon, 180);
});
for (const [name, opts, state] of [['busy', {}, { wxBusy: true, radarBusy: true }],
  ['SIM', { sim: { wx: 95 } }, {}], ['throttle', {}, { lastWxTry: NOW, lastRadarAt: NOW }]]) {
  test('control: existing ' + name + ' eligibility still suppresses both requests', async () => {
    const f = fixture(opts); f.set(state); await f.fetchWeather(); await f.fetchRadar(); assert.equal(f.calls.length, 0);
  });
}
test('R001E radar tile uses captured pair after async configuration change', async () => {
  let deliver; const f = fixture({ lat: 0, lon: 30, fetch: () => new Promise(resolve => { deliver = resolve; }) });
  const pending = f.fetchRadar(); f.set({ lat: 30, lon: 0 });
  assert.equal(typeof deliver, 'function', 'eligible zero-axis radar must dispatch before configuration changes');
  deliver({ ok: true, status: 200, json: async () => ({ generated: NOW / 1000, host: 'https://tilecache.rainviewer.com',
    radar: { past: [{ time: NOW / 1000, path: '/v2/radar/' + NOW / 1000 }] } }) }); await pending;
  assert.equal(f.images.length, 1); assert(f.images[0].includes('/256/6/37/32/'));
});
test.todo('R0003 join: obsolete acquisition cannot install/persist or clear successor attempt');
test.todo('R0008 join: captured New York 2026-03-08T03:30 converts to 07:30Z after global zone change; gap/fold stay unavailable');
test.todo('R000D join: unresolving JSON and image bodies settle within accepted deadline');
test.todo('R0024 join: fresh current model eligibility remains positive while final live strong-particle permission is withheld');
test.todo('native/browser qualification: fixture chip/data-fx, zero-axis consumer, layout/moon/motion pixel evidence');
