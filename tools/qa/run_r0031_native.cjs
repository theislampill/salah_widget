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
// Settings GPS with a never-settling permission query is NOT a cell: decision D-31-3 is pending.
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
const json = (route, status, body) => route.fulfill({ status, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(body) });

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const report = { scope: 'R0031 builder reverse-admission native cells; every external request routed to a fixture or aborted; mocked running clock at ' + INSTANT + '; zone Asia/Riyadh',
    inputs: Object.fromEntries(['builder.html', 'config.js', 'index.html'].map(f => [f, sha(fs.readFileSync(path.join(root, f)))])),
    playwright: require((args.playwright || 'playwright') + '/package.json').version, engines: {}, cells: [] };
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
  server.close();
  report.allPass = report.cells.every(c => c.pass);
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1) + '\n');
  console.log(JSON.stringify(report.cells.map(c => [c.engine, c.cell, c.pass ? 'PASS' : 'FAIL'])));
  if (!report.allPass) process.exitCode = 1;
})().catch(e => { console.error(e); server.close(); process.exitCode = 1; });
