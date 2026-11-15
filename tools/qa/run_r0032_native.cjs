'use strict';
// R0032 native recipe (issue 99; rows R32-02 native request count, R32-06 native crops, R32-11 steady-state pixels).
// Serves generated trees from --root (candidate) and --base (comparison tree, e.g. `git archive origin/main`) on
// 127.0.0.1 and routes EVERY non-local request: Aladhan and Open-Meteo get fixture replies, RainViewer is COUNTED and
// answered with a fixture manifest/503 tile, GeoJS/ipinfo/Nominatim/Zippopotam/BigDataCloud get fixture replies and are
// counted, Google Fonts get 503, anything else is aborted and counted as unexpected. No real provider is contacted and
// no real geolocation is used. Browser zone forced to Asia/Riyadh, clock mocked at INSTANT.
//
// Cells per engine:
//   requests   candidate live Madinah: load, renewal (+16 min), location change (applyConfig to Makkah),
//              long idle (+2 h): RainViewer requests per phase (must all be 0) and Open-Meteo requests (must be > 0)
//   pixels     .c crops of healthy scenes, base vs candidate, with a base-vs-base repeat as the noise control
//   elevation  candidate: A (elevation 2500 m) -> B (B weather served from its cache, B refresh failing) versus a
//              cold B load with the same storage; crops must be equal (base recorded for reference)
//
// Usage: node tools/qa/run_r0032_native.cjs --root <candidate tree> --base <base tree> --out <fresh dir>
//        [--engines chromium,firefox,webkit] [--cells requests,pixels,elevation] [--scenes live-night,noon,...] [--playwright <package path>]
const fs = require('node:fs'), path = require('node:path'), http = require('node:http'), crypto = require('node:crypto');
const argv = process.argv.slice(2), args = {};
for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) args[argv[i].slice(2)] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
const PW = require(args.playwright || 'playwright');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const roots = { cand: path.resolve(args.root || path.join(__dirname, '..', '..')), base: args.base ? path.resolve(args.base) : null };
const out = path.resolve(args.out || 'r0032-native-out'); fs.mkdirSync(out, { recursive: false });
const engines = (args.engines || 'chromium,firefox,webkit').split(',');
const cells = (args.cells || 'requests,pixels,elevation').split(',');
const INSTANT = '2026-09-08T19:00:00Z';
const LIVE = '#lat=24.47&lon=39.61&label=Madinah&tz=Asia%2FRiyadh&units=c&method=4&seed=1';
const ordinary = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'tests', 'r0002-ordinary.json'), 'utf8'));
function record(day) {
  const r = JSON.parse(JSON.stringify(ordinary)), [d, mo, y] = day.split('-').map(Number);
  r.meta.timezone = 'Asia/Riyadh';
  r.date.gregorian = { ...r.date.gregorian, date: day, day: String(d).padStart(2, '0'), month: { number: mo, en: 'September' }, year: String(y) };
  return r;
}
function weather(now, elevation) {
  const q = Math.floor(now / 900000) * 900000, iso = ms => new Date(ms + 3 * 3600000).toISOString().slice(0, 16), hr = q - q % 3600000;
  return { timezone: 'Asia/Riyadh', elevation, current_units: { temperature_2m: '°C', wind_speed_10m: 'm/s' },
    current: { time: iso(q), interval: 900, weather_code: 2, temperature_2m: 24, apparent_temperature: 24, relative_humidity_2m: 80, dew_point_2m: 18,
      wind_speed_10m: 3, wind_direction_10m: 225, wind_gusts_10m: 5, precipitation: 0, rain: 0, showers: 0, snowfall: 0, is_day: 0, cloud_cover: 30,
      cloud_cover_low: 0, cloud_cover_mid: 8, cloud_cover_high: 28, visibility: 6000 },
    hourly: { time: [iso(hr - 3600000), iso(hr), iso(hr + 3600000), iso(hr + 7200000)], temperature_2m: [24, 23, 22, 21], weather_code: [2, 2, 2, 2],
      cloud_cover: [30, 30, 30, 30], precipitation: [0, 0, 0, 0] } };
}
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.bin': 'application/octet-stream', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.webp': 'image/webp' };
function serve(root) {
  return http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x'), p = path.normalize(path.join(root, decodeURIComponent(u.pathname)));
    if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' }); fs.createReadStream(p).pipe(res);
  });
}
const json = (route, status, body) => route.fulfill({ status, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(body) });

(async () => {
  const servers = {}, bases = {};
  for (const [k, r] of Object.entries(roots)) if (r) { servers[k] = serve(r); await new Promise(ok => servers[k].listen(0, '127.0.0.1', ok)); bases[k] = 'http://127.0.0.1:' + servers[k].address().port; }
  const report = { scope: 'R0032 native cells; every external request routed to a fixture, counted or aborted; mocked clock at ' + INSTANT + '; zone Asia/Riyadh',
    inputs: Object.fromEntries(Object.entries(roots).filter(([, r]) => r).map(([k, r]) => [k, Object.fromEntries(['index.html', 'config.js'].map(f => [f, sha(fs.readFileSync(path.join(r, f)))]))])),
    playwright: require((args.playwright || 'playwright') + '/package.json').version, engines: {}, cells: [] };
  const cell = (engine, id, pass, detail) => { report.cells.push({ engine, cell: id, pass: !!pass, ...detail }); console.log(engine, id, pass ? 'PASS' : 'FAIL', JSON.stringify(detail).slice(0, 300)); };
  for (const name of engines) {
    const browser = await PW[name].launch({ headless: true });
    report.engines[name] = browser.version();
    // One context per scenario; `opts.weather(lat)` gives an elevation or 'fail'.
    async function open(which, hash, opts = {}) {
      const log = [], context = opts.context || await browser.newContext({ viewport: { width: 420, height: 620 }, deviceScaleFactor: 1, timezoneId: 'Asia/Riyadh', locale: 'en-US', reducedMotion: 'reduce' });
      await context.route('**/*', route => {
        const url = route.request().url(); if (/^(data|blob):/.test(url)) return route.continue();   // in-page resources (WebKit routes them)
        if (url.startsWith(bases.cand) || (bases.base && url.startsWith(bases.base))) return route.continue();
        const u = new URL(url); log.push({ host: u.hostname, path: u.pathname });
        const m = url.match(/\/timings\/([^/?]+)/);
        if (u.hostname === 'api.aladhan.com' && m && /^\d{2}-\d{2}-\d{4}$/.test(m[1])) return json(route, 200, { code: 200, status: 'OK', data: record(m[1]) });
        if (u.hostname === 'api.open-meteo.com') { const e = (opts.weather || (() => 100))(u.searchParams.get('latitude')); return e === 'fail' ? route.fulfill({ status: 503, body: '' }) : json(route, 200, weather(Date.now(), e)); }
        if (u.hostname === 'api.rainviewer.com') { const s = Math.floor(Date.now() / 1000); return json(route, 200, { generated: s, host: 'https://tilecache.rainviewer.com', radar: { past: [{ time: s, path: '/v2/radar/' + s }] } }); }
        if (u.hostname === 'tilecache.rainviewer.com') return route.fulfill({ status: 503, body: '' });
        if (u.hostname === 'get.geojs.io') return json(route, 200, { latitude: '24.4672', longitude: '39.6142', city: 'Madinah', country_code: 'SA', timezone: 'Asia/Riyadh' });
        if (u.hostname === 'ipinfo.io') return json(route, 200, { loc: '24.4672,39.6142', city: 'Madinah', country: 'SA', timezone: 'Asia/Riyadh' });
        if (u.hostname === 'nominatim.openstreetmap.org') return json(route, 200, []);
        if (/zippopotam\.us$|bigdatacloud\.net$/.test(u.hostname)) return json(route, 404, {});
        if (/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) return route.fulfill({ status: 503, body: '' });
        log.push({ host: u.hostname, unexpected: true }); return route.abort();
      });
      const page = await context.newPage(), errors = [];
      page.on('pageerror', e => errors.push(String(e).slice(0, 200))); page.on('crash', () => errors.push('page crash'));
      if (opts.init) await page.addInitScript(opts.init);
      if (!opts.context) await page.clock.install({ time: new Date(INSTANT) });   // the clock belongs to the context
      await page.goto(bases[which] + '/index.html' + hash);
      await page.waitForFunction(() => document.querySelector('.c') && typeof window.qaState === 'function', null, { timeout: 20000 });
      return { page, context, log, errors };
    }
    const count = (log, re) => log.filter(x => re.test(x.host)).length;
    const crop = async (page, file) => { const b = await page.locator('.c').screenshot({ path: path.join(out, file) }); return b; };
    async function diff(page, a, b) {
      return page.evaluate(async ([x, y]) => {
        const load = src => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = 'data:image/png;base64,' + src; });
        const [p, q] = await Promise.all([load(x), load(y)]); if (p.width !== q.width || p.height !== q.height) return { sizeMismatch: true };
        const c = document.createElement('canvas'); c.width = p.width; c.height = p.height; const g = c.getContext('2d', { willReadFrequently: true });
        g.drawImage(p, 0, 0); const d1 = g.getImageData(0, 0, c.width, c.height).data; g.clearRect(0, 0, c.width, c.height); g.drawImage(q, 0, 0);
        const d2 = g.getImageData(0, 0, c.width, c.height).data; let n = 0, max = 0;
        for (let i = 0; i < d1.length; i += 4) { const m = Math.max(Math.abs(d1[i] - d2[i]), Math.abs(d1[i + 1] - d2[i + 1]), Math.abs(d1[i + 2] - d2[i + 2]), Math.abs(d1[i + 3] - d2[i + 3])); if (m) { n++; if (m > max) max = m; } }
        return { pixels: d1.length / 4, differing: n, maxChannel: max };
      }, [a.toString('base64'), b.toString('base64')]);
    }
    // Settle: let boot finish and the loop run a few mocked seconds.
    // The installed clock runs in real time; fastForward jumps it (and the loop's elapsed clock), then real frames run.
    const settle = async (page, ms = 4000) => { await page.clock.fastForward(ms); await page.waitForTimeout(1500); };

    if (cells.includes('requests')) {
      const s = await open('cand', LIVE), phases = {};
      let mark = 0; const phase = id => { const slice = s.log.slice(mark); mark = s.log.length; phases[id] = { radar: count(slice, /rainviewer/), weather: count(slice, /open-meteo/), unexpected: slice.filter(x => x.unexpected).length, unexpectedHosts: [...new Set(slice.filter(x => x.unexpected).map(x => x.host))] }; };
      await settle(s.page, 6000); await s.page.waitForFunction(() => document.querySelector('#wt') && /\d/.test(document.querySelector('#wt').textContent), null, { timeout: 15000 }).catch(() => {});
      await settle(s.page, 61000); phase('load');
      await s.page.clock.fastForward('16:00'); await settle(s.page, 31000); phase('renewal');
      await s.page.evaluate(() => applyConfig({ lat: 21.42, lon: 39.83, tz: 'Asia/Riyadh', label: 'Makkah', method: '4', school: '0', time: '24', units: 'c', datefmt: 'YYYY-MM-DD', source: 'manual' }));
      await settle(s.page, 31000); phase('location-change');
      await s.page.clock.fastForward('02:00:00'); await settle(s.page, 61000); phase('long-idle');
      const qa = await s.page.evaluate(() => { const t = qaState().wxTruth; return { radarSource: t.radarSource, radarAcquisition: t.radarAcquisition, lat }; });
      const total = Object.values(phases).reduce((a, p) => a + p.radar, 0);
      cell(name, 'requests', total === 0 && Object.values(phases).every(p => p.weather > 0 && p.unexpected === 0) && qa.lat === 21.42,
        { radarRequestsTotal: total, phases, qa, pageErrors: s.errors });
      await s.context.close();
    }
    if (cells.includes('pixels') && bases.base) {
      const scenes = [['live-night', LIVE], ['noon', LIVE + '&simTime=12:30'], ['sunset', LIVE + '&simTime=18:20'], ['broken', LIVE + '&simTime=10:00&simWx=2&simCloud=50'],
        ['rain', LIVE + '&simTime=15:00&simWx=63'], ['crescent', LIVE + '&simTime=21:30&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42']];
      // Deterministic capture: pause the context clock at one fixed instant, run a second of frames, let CSS
      // transitions finish in real time. Two base and two candidate pages per scene; base-vs-base is the noise floor.
      const FIX = Date.parse(INSTANT) + 20000;
      const only = args.scenes ? args.scenes.split(',') : null;
      for (const [id, hash] of scenes.filter(([id]) => !only || only.includes(id))) {
        const shots = {};
        let keep = null;
        for (const [k, which] of [['base1', 'base'], ['base2', 'base'], ['cand1', 'cand'], ['cand2', 'cand']]) {
          const s = await open(which, hash); await s.page.waitForTimeout(6000); await s.page.clock.pauseAt(FIX); await s.page.clock.runFor(1000); await s.page.waitForTimeout(2500);
          shots[k] = await crop(s.page, name + '-' + id + '-' + k + '.png');
          if (keep) await keep.context.close(); keep = s;
        }
        const d = {}; for (const [x, y] of [['base1', 'base2'], ['cand1', 'cand2'], ['base1', 'cand1'], ['base2', 'cand2'], ['base1', 'cand2'], ['base2', 'cand1']]) d[x + '~' + y] = await diff(keep.page, shots[x], shots[y]);
        await keep.context.close();
        const noise = Math.max(d['base1~base2'].differing, d['cand1~cand2'].differing), cross = Math.min(d['base1~cand1'].differing, d['base2~cand2'].differing, d['base1~cand2'].differing, d['base2~cand1'].differing);
        cell(name, 'pixels:' + id, cross <= noise, Object.fromEntries(Object.entries(d).map(([k, v]) => [k, [v.differing, v.maxChannel]])));
      }
    }
    if (cells.includes('elevation')) {
      const bKey = 'salahwx:21.42|39.83|c', tableA = la => la === '24.47' ? 2500 : 'fail';
      for (const which of ['cand', ...(bases.base ? ['base'] : [])]) {
        const context = await browser.newContext({ viewport: { width: 420, height: 620 }, deviceScaleFactor: 1, timezoneId: 'Asia/Riyadh', locale: 'en-US', reducedMotion: 'reduce' });
        await context.clock.install({ time: new Date(INSTANT) });
        const a = await open(which, LIVE + '&debugLayers=1', { context, weather: tableA }); await settle(a.page, 6000);
        await a.page.evaluate(k => { const b = { time: new Date(Date.now() + 3 * 3600000 - Date.now() % 900000).toISOString().slice(0, 16), interval: 900, weather_code: 2, temperature_2m: 24, apparent_temperature: 24,
          relative_humidity_2m: 80, dew_point_2m: 18, wind_speed_10m: 3, wind_direction_10m: 225, wind_gusts_10m: 5, precipitation: 0, rain: 0, showers: 0, snowfall: 0, is_day: 0,
          cloud_cover: 30, cloud_cover_low: 0, cloud_cover_mid: 8, cloud_cover_high: 28, visibility: 6000 };
          localStorage.setItem(k, JSON.stringify({ w: admitWeatherRecord(b, { lat: 21.42, lon: 39.83, units: 'c', zone: 'Asia/Riyadh', retrievedAt: Date.now() }), ts: Date.now() })); }, bKey);
        await a.page.evaluate(() => applyConfig({ lat: 21.42, lon: 39.83, tz: 'Asia/Riyadh', label: 'Makkah', method: '4', school: '0', time: '24', units: 'c', datefmt: 'YYYY-MM-DD', source: 'manual' }));
        await settle(a.page, 3000);
        const T = await a.page.evaluate(() => Date.now() + 90000);
        const b = await open(which, '#lat=21.42&lon=39.83&label=Makkah&tz=Asia%2FRiyadh&units=c&method=4&seed=1&debugLayers=1', { context, weather: tableA });
        await b.page.waitForTimeout(3000); await b.page.clock.pauseAt(T); await b.page.clock.runFor(1500); await b.page.waitForTimeout(300);   // one shared context clock
        const read = s => s.page.evaluate(() => ({ elev: (/elev (-?\d+)m/.exec(document.querySelector('.dbglayers')?.textContent || '') || [])[1], temp: weather && weather.temp, lat }));
        const ra = await read(a), rb = await read(b);
        // Crop the card without the debug read-out: hide it for the capture only.
        for (const s of [a, b]) await s.page.evaluate(() => { const d = document.querySelector('.dbglayers'); if (d) d.style.visibility = 'hidden'; });
        const ca = await crop(a.page, name + '-elev-' + which + '-AtoB.png'), cb = await crop(b.page, name + '-elev-' + which + '-coldB.png');
        const d = await diff(b.page, ca, cb);
        // Whole-card crops of two pages also differ by path-dependent state (cloud history, label), so the elevation
        // effect is isolated on the foreground cold-B page at the paused clock: noise = two frames, effect = A's 2500 m re-imposed.
        let probe = null;
        if (which === 'cand') {
          const frame = async () => { await b.page.clock.runFor(34); await b.page.waitForTimeout(2500); return b.page.locator('.c').screenshot(); };
          const f0 = await frame(), f1 = await frame();
          await b.page.evaluate(() => { _siteElevAt = { lat, lon }; siteElev = 2500; _renderDirty = true; });
          const f2 = await frame(); await b.page.evaluate(() => { _siteElevAt = null; _renderDirty = true; }); const f3 = await frame();
          probe = { noise: await diff(b.page, f0, f1), carriedAElevation: await diff(b.page, f1, f2), restored: await diff(b.page, f1, f3) };
          fs.writeFileSync(path.join(out, name + '-elev-probe-carried.png'), f2);
        }
        cell(name, 'elevation:' + which, which === 'cand' ? ra.elev === '0' && rb.elev === '0' : true,
          { AtoB: ra, coldB: rb, twoPageCrops: d, probe, reference: which === 'base' });
        await context.close();
      }
    }
    await browser.close();
  }
  for (const s of Object.values(servers)) s.close();
  report.allPass = report.cells.every(c => c.pass);
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1) + '\n');
  if (!report.allPass) process.exitCode = 1;
})().catch(e => { console.error(e); process.exitCode = 1; process.exit(1); });
