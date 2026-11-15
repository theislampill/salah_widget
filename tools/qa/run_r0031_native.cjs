'use strict';
// R0031 native recipe (issue 98; R31-13 builder cells and the R31-09 builder wrapper/snippet check). Serves an
// unchanged generated tree from --root on 127.0.0.1 and routes EVERY non-local request: GeoJS, ipinfo, Nominatim,
// Zippopotam, BigDataCloud and Aladhan get fixture replies; Open-Meteo, RainViewer and Google Fonts get a fixture
// 503; anything else is aborted. No real provider is contacted. navigator.geolocation and the geolocation
// permission query are init-script doubles. Browser zone forced to Asia/Riyadh, clock mocked (running) at INSTANT.
//
// Builder cells per engine (one page, in order):
//   boot        coarse detect (GeoJS fixture: Madinah, SA) -> method 4
//   non-ok      coordinate edit 40.7/-74, BigDataCloud HTTP 429 with a well-formed NA body -> export unchanged (method 4)
//   na          edit 40.8, HTTP 200 {city:Newark,countryCode:US,continentCode:NA} -> method 2, label Newark
//   empty       edit 40.9, HTTP 200 {} -> export unchanged (method 2)
//   local       self-configuring mode, coordinate edit and pin (fixture position) -> zero BigDataCloud requests
//   wrapper     #pv bounding box, snippet iframe style, builder crop (R31-09)
// Settings GPS cells (owner decision D-31-3 = A) run with --cells gps; see gpsCells below.
//
// Usage: node tools/qa/run_r0031_native.cjs --root <tree> --out <fresh dir> [--engines chromium,firefox,webkit]
//        [--playwright <path to the playwright package>]
const fs = require('node:fs'), path = require('node:path'), http = require('node:http'), crypto = require('node:crypto');
const argv = process.argv.slice(2), args = {};
for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) args[argv[i].slice(2)] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
const PW = require(args.playwright || 'playwright');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const root = path.resolve(args.root || path.join(__dirname, '..', '..'));
const out = path.resolve(args.out || 'r0031-native-out'); fs.mkdirSync(out, { recursive: false });
const engines = (args.engines || 'chromium,firefox,webkit').split(',');
const INSTANT = '2026-09-07T09:00:00Z';
const ordinary = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'tests', 'r0002-ordinary.json'), 'utf8'));
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
function record(day) {
  const r = JSON.parse(JSON.stringify(ordinary)), [d, mo, y] = day.split('-').map(Number);
  r.date.gregorian = { ...r.date.gregorian, date: day, day: String(d).padStart(2, '0'), month: { number: mo, en: MONTHS[mo - 1] }, year: String(y) };
  return r;
}
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.bin': 'application/octet-stream', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'), p = path.normalize(path.join(root, decodeURIComponent(u.pathname)));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' }); fs.createReadStream(p).pipe(res);
});
const GEO_INIT = `(()=>{const g=window.__r0031Geo={calls:0,perm:0};
 const geo={getCurrentPosition(ok){g.calls++;setTimeout(()=>ok({coords:{latitude:51.5,longitude:-0.12,accuracy:20},timestamp:Date.now()}),50);},watchPosition(){return 0;},clearWatch(){}};
 Object.defineProperty(Navigator.prototype,'geolocation',{get(){return geo;},configurable:true});
 if(navigator.permissions){const q=navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query=d=>{if(d&&d.name==='geolocation'){g.perm++;return Promise.resolve({state:'granted'});}return q(d);};}})();`;
function finish(report) {
  server.close();
  report.allPass = report.cells.every(c => c.pass);
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1) + '\n');
  console.log(JSON.stringify(report.cells.map(c => [c.engine, c.cell, c.pass ? 'PASS' : 'FAIL'])));
  if (!report.allPass) process.exitCode = 1;
}
// ---- settings GPS cells (--cells gps; owner decision D-31-3 = A, issue 98 comment 6878230757) ---------------------
// Per engine and permission-diagnostic variant, a fresh context whose init script stubs navigator.geolocation (one
// fix 51.5/-0.12, accuracy 20 m, after 50 ms) and overrides navigator.permissions.query: never settles, rejects,
// absent (no navigator.permissions), or resolves granted/denied/prompt. The widget is served in local mode with a saved Madinah config;
// the cell opens settings, clicks the pin and samples the status line every 100 ms for 3 s (no flicker: the
// distinct statuses are only "Requesting browser location…" then one "Browser position …"). Expected qaState
// geolocation permission state: "unknown" for never/reject/absent, else the resolved state. Cell reset-gps-never:
// a saved Cairo config in local mode, Reset with detection held, then a fix while the diagnostic never settles; the
// pin call site must end the Reset on adoption (R0030), so after close and release the fix is the configuration.
const VARIANTS = { never: '()=>new Promise(()=>{})', reject: '()=>Promise.reject(new Error("fixture"))', absent: null,
  granted: '()=>Promise.resolve({state:"granted"})', denied: '()=>Promise.resolve({state:"denied"})', prompt: '()=>Promise.resolve({state:"prompt"})' };
const gpsInit = v => `(()=>{const g=window.__r0031Geo={calls:0,perm:0};
 const geo={getCurrentPosition(ok){g.calls++;setTimeout(()=>ok({coords:{latitude:51.5,longitude:-0.12,accuracy:20},timestamp:Date.now()}),50);},watchPosition(){return 0;},clearWatch(){}};
 Object.defineProperty(Navigator.prototype,'geolocation',{get(){return geo;},configurable:true});
 ${VARIANTS[v] === null ? "Object.defineProperty(Navigator.prototype,'permissions',{get(){return undefined;},configurable:true});"
    : `if(navigator.permissions){const q=navigator.permissions.query.bind(navigator.permissions),f=${VARIANTS[v]};navigator.permissions.query=d=>{if(d&&d.name==='geolocation'){g.perm++;return f();}return q(d);};}`}})();`;
async function gpsCells(base, report) {
  for (const name of engines) {
    const browser = await PW[name].launch({ headless: true }); report.engines[name] = browser.version();
    const external = new Set();
    async function ctx(variant, detect) {
      const context = await browser.newContext({ viewport: { width: 420, height: 640 }, deviceScaleFactor: 1, timezoneId: 'Asia/Riyadh', locale: 'en-US', reducedMotion: 'reduce' });
      await context.addInitScript(gpsInit(variant));
      await context.route('**/*', async route => {
        const url = route.request().url(); if (url.startsWith(base)) return route.continue();
        const u = new URL(url); external.add(u.hostname + u.pathname);
        if (u.hostname === 'get.geojs.io' || u.hostname === 'ipinfo.io') {
          if (detect && detect.hold) await new Promise(r => detect.waiting.push(r));
          return u.hostname === 'get.geojs.io' ? json(route, 200, { latitude: '24.4672', longitude: '39.6142', city: 'Madinah', country_code: 'SA', timezone: 'Asia/Riyadh' })
            : json(route, 200, { loc: '24.4672,39.6142', city: 'Madinah', country: 'SA', timezone: 'Asia/Riyadh' });
        }
        if (u.hostname === 'nominatim.openstreetmap.org') return json(route, 200, []);
        if (u.hostname === 'api.zippopotam.us') return json(route, 404, {});
        if (u.hostname === 'api.bigdatacloud.net') return json(route, 503, {});
        const m = url.match(/\/timings\/([^/?]+)/);
        if (u.hostname === 'api.aladhan.com' && m && /^\d{2}-\d{2}-\d{4}$/.test(m[1])) return json(route, 200, { code: 200, status: 'OK', data: record(m[1]) });
        if (/open-meteo\.com$|rainviewer\.com$|fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) return route.fulfill({ status: 503, body: '' });
        return route.abort();
      });
      const page = await context.newPage(), errors = [];
      page.on('pageerror', e => errors.push(String(e).slice(0, 200)));
      await page.clock.install({ time: new Date(INSTANT) });
      return { context, page, errors };
    }
    const sample = async page => { const seq = []; for (let i = 0; i < 30; i++) { const t = await page.evaluate(() => document.getElementById('set-status').textContent.split('\n').pop()); if (seq[seq.length - 1] !== t) seq.push(t); await page.waitForTimeout(100); } return seq; };
    // --variants never,reject,... and --reset 0 split a slow engine's run into shorter invocations.
    for (const variant of (args.variants || Object.keys(VARIANTS).join(',')).split(',').filter(v => v in VARIANTS)) {
      const { context, page, errors } = await ctx(variant);
      await page.goto(base + '/index.html#local=1'); await page.waitForFunction(() => !!window.SalahConfig, null, { timeout: 20000 });
      await page.evaluate(() => { localStorage.removeItem('salah_widget:config:v1'); SalahConfig.saveLocal({ lat: 24.47, lon: 39.61, label: 'Madinah', method: '4', source: 'manual', tz: 'Asia/Riyadh' }); });
      await page.reload(); await page.waitForFunction(() => document.querySelector('.buckle.interactive'), null, { timeout: 20000 }); await page.waitForTimeout(1000);
      await page.click('.buckle'); await page.waitForFunction(() => document.querySelector('.c').classList.contains('settings-open'));
      await page.click('#set-pin'); const seq = await sample(page);
      const st = await page.evaluate(() => ({ lat: document.getElementById('set-lat').value, lon: document.getElementById('set-lon').value,
        permission: qaState().config.geolocationPermissionState, geo: window.__r0031Geo }));
      const want = ['never', 'reject', 'absent'].includes(variant) ? 'unknown' : variant;
      const statuses = seq.filter(t => t);
      const steady = statuses.length >= 1 && /^Browser position/.test(statuses[statuses.length - 1])
        && statuses.every(t => /^(Requesting browser location|Browser position)/.test(t)) && statuses.filter(t => /^Browser position/.test(t)).length === 1;
      const pass = st.lat === '51.50000' && st.lon === '-0.12000' && steady && st.permission === want && st.geo.calls === 1;
      report.cells.push({ engine: name, cell: 'gps-' + variant, pass, statuses, form: [st.lat, st.lon], permission: st.permission, expected: want,
        geoCalls: st.geo.calls, permissionQueries: st.geo.perm, pageErrors: errors.length });
      await context.close();
    }
    if (args.reset !== '0') { // reset-gps-never: R0030 Reset, then a GPS fix while the diagnostic never settles
      const detect = { hold: false, waiting: [] }, { context, page, errors } = await ctx('never', detect);
      await page.goto(base + '/index.html#local=1');
      await page.waitForFunction(() => !!window.SalahConfig, null, { timeout: 20000 });
      await page.evaluate(() => { localStorage.removeItem('salah_widget:config:v1'); SalahConfig.saveLocal({ lat: 30.04, lon: 31.24, label: 'Cairo', method: '5', units: 'c', source: 'manual', tz: 'Africa/Cairo' }); });
      await page.reload(); await page.waitForFunction(() => document.querySelector('.buckle.interactive'), null, { timeout: 20000 }); await page.waitForTimeout(1000);
      await page.click('.buckle'); detect.hold = true; await page.click('#set-reset'); await page.waitForTimeout(300);
      await page.click('#set-pin'); await page.waitForTimeout(1500);
      const pending = await page.evaluate(() => !!_setReset);
      await page.click('#setClose'); detect.hold = false; detect.waiting.splice(0).forEach(r => r()); await page.waitForTimeout(3000);
      const c = await page.evaluate(() => ({ lat: CONFIG.lat, lon: CONFIG.lon, source: CONFIG.source, saved: SalahConfig.loadLocal() }));
      const pass = !pending && c.lat === 51.5 && c.lon === -0.12 && !!c.saved && c.saved.lat === 51.5;
      report.cells.push({ engine: name, cell: 'reset-gps-never', pass, resetPendingAfterFix: pending, runtime: { lat: c.lat, lon: c.lon, source: c.source },
        savedLat: c.saved && c.saved.lat, pageErrors: errors.length });
      await context.close();
    }
    report[name + 'External'] = [...external].sort();
    await browser.close();
  }
}
const json = (route, status, body) => route.fulfill({ status, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(body) });

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const report = { scope: 'R0031 builder reverse-admission native cells; every external request routed to a fixture or aborted; mocked running clock at ' + INSTANT + '; zone Asia/Riyadh',
    inputs: Object.fromEntries(['builder.html', 'config.js', 'index.html'].map(f => [f, sha(fs.readFileSync(path.join(root, f)))])),
    playwright: require((args.playwright || 'playwright') + '/package.json').version, engines: {}, cells: [] };
  if (args.cells === 'gps') { await gpsCells(base, report); finish(report); return; }
  for (const name of engines) {
    const browser = await PW[name].launch({ headless: true }), external = [], bdc = [];
    report.engines[name] = browser.version();
    const replies = [];   // queue of BigDataCloud replies, consumed in request order
    const context = await browser.newContext({ viewport: { width: 1100, height: 1000 }, deviceScaleFactor: 1, timezoneId: 'Asia/Riyadh', locale: 'en-US', reducedMotion: 'reduce' });
    await context.addInitScript(GEO_INIT);
    await context.route('**/*', route => {
      const url = route.request().url(); if (url.startsWith(base)) return route.continue();
      const u = new URL(url); external.push(u.hostname + u.pathname);
      if (u.hostname === 'get.geojs.io') return json(route, 200, { latitude: '24.4672', longitude: '39.6142', city: 'Madinah', country_code: 'SA', timezone: 'Asia/Riyadh' });
      if (u.hostname === 'ipinfo.io') return json(route, 200, { loc: '24.4672,39.6142', city: 'Madinah', country: 'SA', timezone: 'Asia/Riyadh' });
      if (u.hostname === 'nominatim.openstreetmap.org') return json(route, 200, []);
      if (u.hostname === 'api.zippopotam.us') return json(route, 404, {});
      if (u.hostname === 'api.bigdatacloud.net') { bdc.push(url); const r = replies.shift() || [503, {}]; return json(route, r[0], r[1]); }
      const m = url.match(/\/timings\/([^/?]+)/);
      if (u.hostname === 'api.aladhan.com' && m && /^\d{2}-\d{2}-\d{4}$/.test(m[1])) return json(route, 200, { code: 200, status: 'OK', data: record(m[1]) });
      if (/open-meteo\.com$|rainviewer\.com$|fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) return route.fulfill({ status: 503, body: '' });
      return route.abort();
    });
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(String(e).slice(0, 200)));
    await page.clock.install({ time: new Date(INSTANT) });
    await page.goto(base + '/builder.html');
    const state = () => page.evaluate(() => ({ tuple: ['label', 'lat', 'lon', 'method'].map(id => document.getElementById(id).value),
      code: document.getElementById('code').value, tip: document.getElementById('geotip').textContent, mode: embedMode }));
    const method = s => new URLSearchParams(s.code.match(/src="([^"]+)"/)[1].split('#')[1]).get('method');
    const cell = (id, pass, detail) => report.cells.push({ engine: name, cell: id, pass: !!pass, ...detail });
    await page.waitForFunction(() => /^(Detected|Couldn)/.test(document.getElementById('geotip').textContent), null, { timeout: 15000 });
    let s = await state(); cell('boot', s.tuple[3] === '4' && method(s) === '4', { state: { tuple: s.tuple, tip: s.tip } });
    async function edit(lat, lon, reply) {
      replies.push(reply); const n = bdc.length;
      await page.fill('#lat', lat); if (lon) await page.fill('#lon', lon);
      const before = await state();
      for (let i = 0; i < 40 && bdc.length < n + 1; i++) await page.waitForTimeout(100);
      await page.waitForTimeout(800);
      return { before, after: await state(), requests: bdc.length - n };
    }
    let r = await edit('40.7', '-74', [429, { city: 'New York', countryCode: 'US', continentCode: 'NA' }]);
    cell('non-ok', r.requests === 1 && r.after.code === r.before.code && method(r.after) === '4' && r.after.tuple[0] === r.before.tuple[0], { requests: r.requests, method: method(r.after), label: r.after.tuple[0] });
    r = await edit('40.8', null, [200, { city: 'Newark', countryCode: 'US', continentCode: 'NA' }]);
    cell('na', r.requests === 1 && method(r.after) === '2' && r.after.tuple[3] === '2' && r.after.tuple[0] === 'Newark', { requests: r.requests, method: method(r.after), label: r.after.tuple[0] });
    r = await edit('40.9', null, [200, {}]);
    cell('empty', r.requests === 1 && r.after.code === r.before.code && method(r.after) === '2', { requests: r.requests, method: method(r.after) });
    await page.click('#mode-local'); const n = bdc.length;
    await page.fill('#lat', '41.0'); await page.fill('#lon', '-73.9'); await page.waitForTimeout(1500);
    await page.click('#geo'); await page.waitForTimeout(1500);
    s = await state(); const geoCalls = await page.evaluate(() => window.__r0031Geo.calls);
    cell('local', s.mode === 'local' && bdc.length === n && geoCalls >= 1 && /[#&]local=1/.test(s.code), { reverseRequests: bdc.length - n, geoCalls, method: method(s) });
    const box = await page.locator('#pv').boundingBox(), style = await page.locator('#pv').getAttribute('style');
    const snippetStyle = (s.code.match(/style="([^"]+)"/) || [])[1];
    await page.click('#mode-portable'); await page.waitForTimeout(300);
    // Crop: the preview wrapper and the exported snippet together, after the preview has had time to render.
    await page.waitForTimeout(6000);
    const a = await page.locator('#pv').boundingBox(), c = await page.locator('#code').boundingBox();
    const x = Math.floor(Math.min(a.x, c.x)), y = Math.floor(Math.min(a.y, c.y));
    const clip = { x, y, width: Math.ceil(Math.max(a.x + a.width, c.x + c.width)) - x, height: Math.ceil(Math.max(a.y + a.height, c.y + c.height)) - y };
    const crop = name + '-builder-card.png'; await page.screenshot({ path: path.join(out, crop), clip, fullPage: true });
    cell('wrapper', Math.round(box.width) === 325 && Math.round(box.height) === 530 && snippetStyle === 'width:325px;height:530px;border:0;border-radius:28px;overflow:hidden',
      { box: { width: box.width, height: box.height }, pvStyle: style, snippetStyle, crop });
    report.cells.filter(c => c.engine === name).forEach(c => { c.pageErrors = errors.length; });
    report[name + 'External'] = [...new Set(external)].sort();
    await context.close(); await browser.close();
  }
  finish(report);
})().catch(e => { console.error(e); server.close(); process.exitCode = 1; });
