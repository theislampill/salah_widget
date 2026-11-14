'use strict';
// R0030 native recipe (issue 97: settings Reset authority, dirty-close commit, apply-failure state).
// Serves unchanged generated trees on 127.0.0.1 and routes EVERY non-local request: GeoJS and ipinfo get a
// fixture (Madinah, SA) that the recipe can HOLD to keep the Reset race window open; Aladhan gets the
// ordinary fixture; Open-Meteo, RainViewer and Google Fonts get a fixture 503; anything else is aborted.
// No real provider is contacted and real geolocation is never used. Browser zone forced to Asia/Riyadh,
// clock mocked at INSTANT (running), reduced motion. Real localStorage, read back in a fresh page.
//
// Behaviour cells (branch tree, per engine): R1, R2, R3, N1, ES30-09 (storage denied), ES30-08a
// (detection fails after close), ES30-12 (injected bindConfig fault: no unhandledrejection, G3 copy).
// Pixel control (healthy scenes, settings closed and open): --main <tree> is captured twice (noise) and
// compared with the branch tree, per engine: closed card, open panel, completed Reset (open), and the
// session-only warning (closed). Differences are counted per pixel over the 325x530 card.
//
// Usage: node tools/qa/run_r0030_native.cjs --root <branch tree> --main <main tree> --out <fresh dir>
//        [--engines chromium,firefox,webkit] [--playwright <path to the playwright package>]
const fs = require('node:fs'), path = require('node:path'), http = require('node:http'), crypto = require('node:crypto');
const argv = process.argv.slice(2), args = {};
for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) args[argv[i].slice(2)] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
const PW = require(args.playwright || 'playwright');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const branchRoot = path.resolve(args.root || path.join(__dirname, '..', '..')), mainRoot = args.main ? path.resolve(args.main) : null;
const out = path.resolve(args.out || 'r0030-native-out'); fs.mkdirSync(out, { recursive: false });
const engines = (args.engines || 'chromium,firefox,webkit').split(',');
const INSTANT = '2026-09-07T09:00:00Z', KEY = 'salah_widget:config:v1';
const ordinary = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'tests', 'r0002-ordinary.json'), 'utf8'));
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
function record(day) {
  const r = JSON.parse(JSON.stringify(ordinary)), [d, mo, y] = day.split('-').map(Number);
  r.date.gregorian = { ...r.date.gregorian, date: day, day: String(d).padStart(2, '0'), month: { number: mo, en: MONTHS[mo - 1] }, year: String(y) };
  return r;
}
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.bin': 'application/octet-stream', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.webp': 'image/webp' };
function serve(root) {
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x'), p = path.normalize(path.join(root, decodeURIComponent(u.pathname)));
    if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' }); fs.createReadStream(p).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r({ server, base: 'http://127.0.0.1:' + server.address().port })));
}
const GEO_INIT = `(()=>{const geo={getCurrentPosition(ok,bad){bad&&bad({code:1,message:"denied by fixture"});},watchPosition(){return 0;},clearWatch(){}};
 Object.defineProperty(Navigator.prototype,'geolocation',{get(){return geo;},configurable:true});
 window.__r0030={unhandled:0};addEventListener('unhandledrejection',()=>{window.__r0030.unhandled++;});})();`;
const json = (route, status, body) => route.fulfill({ status, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(body) });
const LONDON = { lat: 51.5, lon: -0.12, label: 'London', method: '3', units: 'f', source: 'manual', tz: 'Europe/London' };

async function engineRun(name, root, base, cells, shots, tag) {
  const browser = await PW[name].launch({ headless: true }), external = [];
  const detect = { hold: false, fail: false, waiting: [], count: 0 };
  const context = await browser.newContext({ viewport: { width: 420, height: 640 }, deviceScaleFactor: 1, timezoneId: 'Asia/Riyadh', locale: 'en-US', reducedMotion: 'reduce' });
  await context.addInitScript(GEO_INIT);
  await context.route('**/*', async route => {
    const url = route.request().url(); if (url.startsWith(base)) return route.continue();
    const u = new URL(url); external.push(u.hostname + u.pathname);
    if (u.hostname === 'get.geojs.io' || u.hostname === 'ipinfo.io') {
      detect.count++;
      if (detect.hold) await new Promise(r => detect.waiting.push(r));
      if (detect.fail) return route.fulfill({ status: 503, body: '' });
      return u.hostname === 'get.geojs.io' ? json(route, 200, { latitude: '24.4672', longitude: '39.6142', city: 'Madinah', country: 'Saudi Arabia', country_code: 'SA', timezone: 'Asia/Riyadh' })
        : json(route, 200, { loc: '24.4672,39.6142', city: 'Madinah', country: 'SA', timezone: 'Asia/Riyadh' });
    }
    const m = url.match(/\/timings\/([^/?]+)/);
    if (u.hostname === 'api.aladhan.com' && m && /^\d{2}-\d{2}-\d{4}$/.test(m[1])) return json(route, 200, { code: 200, status: 'OK', data: record(m[1]) });
    if (/open-meteo\.com$|rainviewer\.com$|fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) return route.fulfill({ status: 503, body: '' });
    return route.abort();
  });
  const release = () => { const w = detect.waiting.splice(0); w.forEach(r => r()); };
  async function fresh(hash, seed) {
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(String(e).slice(0, 200)));
    await page.clock.install({ time: new Date(INSTANT) });
    await page.goto(base + '/index.html' + hash);
    await page.waitForFunction(() => !!window.SalahConfig, null, { timeout: 15000 });
    await page.evaluate(([k, s]) => { localStorage.removeItem(k); if (s) SalahConfig.saveLocal(s); }, [KEY, seed || null]);
    await page.reload(); await page.waitForFunction(() => document.querySelector('.buckle.interactive'), null, { timeout: 15000 });
    await page.waitForTimeout(1500);
    return { page, errors };
  }
  const stored = page => page.evaluate(k => localStorage.getItem(k), KEY);
  const cfg = page => page.evaluate(() => ({ lat: CONFIG && CONFIG.lat, label: CONFIG && CONFIG.label, source: CONFIG && CONFIG.source, units: CONFIG && CONFIG.units, method: CONFIG && CONFIG.method }));
  const open = page => page.click('.buckle'), close = page => page.click('#setClose');
  const cell = (id, pass, detail) => cells.push({ engine: name, cell: id, pass: !!pass, ...detail });
  const readback = async () => { const p = await context.newPage(); await p.goto(base + '/index.html#local=1&qa=1'); await p.waitForFunction(() => !!window.SalahConfig);
    const v = await p.evaluate(() => SalahConfig.loadLocal()); await p.close(); return v; };
  if (tag === 'branch') {
    // R1: pre-dispatch method edit, Reset, close during detection; the target lands after close.
    let { page, errors } = await fresh('#local=1', LONDON);
    await open(page); await page.selectOption('#set-method', '2'); detect.hold = true; const n = detect.count;
    await page.click('#set-reset'); await page.waitForTimeout(300); await close(page); const afterClose = await stored(page);
    detect.hold = false; release(); await page.waitForTimeout(2500);
    let c = await cfg(page), rb = await readback();
    cell('R1', afterClose === null && rb === null && c.lat > 24 && c.lat < 25 && detect.count === n + 1, { afterClose, readback: rb, runtime: c, errors: errors.length }); await page.close();
    // R2: display-name edit during detection, close, release.
    ({ page, errors } = await fresh('#local=1', LONDON));
    await open(page); detect.hold = true; await page.click('#set-reset'); await page.fill('#set-label', 'Home'); await close(page);
    detect.hold = false; release(); await page.waitForTimeout(2500); c = await cfg(page); rb = await readback();
    cell('R2', rb && rb.lat > 24 && rb.lat < 25 && rb.label === 'Home' && c.label === 'Home', { readback: rb && { lat: rb.lat, label: rb.label }, runtime: c }); await page.close();
    // R3: saved browser-position record; Reset; close clean; reopen -> no "Saved" claim (accessible name).
    ({ page, errors } = await fresh('#local=1', { ...LONDON, source: 'browser-geolocation', locationEvidence: { source: 'browser-geolocation', accuracyM: 12, acquiredAt: Date.parse(INSTANT) - 60000 } }));
    await open(page); const beforeName = await page.getAttribute('#set-pin', 'aria-label'); detect.hold = true; await page.click('#set-reset'); await close(page); await open(page);
    const afterName = await page.getAttribute('#set-pin', 'aria-label'); c = await cfg(page); detect.hold = false; release(); await page.waitForTimeout(300);
    cell('R3', /^Saved/.test(beforeName) && !/Saved/.test(afterName) && c.source !== 'localStorage', { beforeName, afterName, source: c.source }); await page.close();
    // N1: preferLocal hash site; Reset makes no coarse request and applies the hash site.
    ({ page, errors } = await fresh('#preferLocal=1&lat=21.4225&lon=39.8262&label=Makkah', LONDON));
    const n1 = detect.count; await open(page); await page.click('#set-reset'); await page.waitForTimeout(2500); c = await cfg(page);
    const st = await page.textContent('#set-status');
    cell('N1', detect.count === n1 && Math.abs(c.lat - 21.4225) < 1e-6 && c.source === 'hash' && !/Detecting|estimated/.test(st), { coarseRequests: detect.count - n1, runtime: c, status: st }); await page.close();
    // ES30-09: storage write denied; label edit during Reset; close -> session-only warning, nothing written.
    ({ page, errors } = await fresh('#local=1', LONDON));
    await open(page); detect.hold = true; await page.click('#set-reset');
    await page.evaluate(() => { Storage.prototype.setItem = function () { throw new DOMException('blocked', 'SecurityError'); }; });
    await page.fill('#set-label', 'Home'); await close(page); detect.hold = false; release(); await page.waitForTimeout(2500);
    const live = await page.textContent('#settings-persistence-status'), warn = await page.evaluate(() => document.querySelector('.buckle').classList.contains('persist-warning'));
    c = await cfg(page); rb = await readback();
    cell('ES30-09', rb === null && warn && /session only/.test(live) && c.label === 'Home', { live, warn, readback: rb, runtime: c }); await page.close();
    // ES30-08a: detection fails after close; deferred units edit session-only; no reopen; next open says so.
    ({ page, errors } = await fresh('#local=1', LONDON));
    await open(page); detect.hold = true; detect.fail = true; await page.click('#set-reset'); await page.selectOption('#set-units', 'c'); await close(page);
    release(); detect.hold = false; await page.waitForTimeout(2500); detect.fail = false;
    const opened = await page.evaluate(() => document.querySelector('.c').classList.contains('settings-open')); c = await cfg(page); rb = await readback();
    await open(page); const st2 = await page.textContent('#set-status');
    cell('ES30-08a', !opened && rb === null && c.units === 'c' && c.lat === 51.5 && /Enter your location\./.test(st2), { opened, readback: rb, runtime: c, status: st2 }); await page.close();
    // ES30-12: injected bindConfig fault on close-save -> no unhandledrejection, G3 copy, save kept.
    ({ page, errors } = await fresh('#local=1', LONDON));
    await open(page); await page.evaluate(() => { window.bindConfig = () => { throw new TypeError('injected'); }; });
    await page.fill('#set-lat', '30'); await page.fill('#set-lon', '31'); await close(page); await page.waitForTimeout(800);
    const r12 = await page.evaluate(() => ({ unhandled: window.__r0030.unhandled, live: document.getElementById('settings-persistence-status').textContent }));
    rb = await readback();
    cell('ES30-12', r12.unhandled === 0 && /Settings saved in this browser\.\nSettings could not be applied \(TypeError\)/.test(r12.live) && rb && rb.lat === 30, { ...r12, readbackLat: rb && rb.lat, pageErrors: errors }); await page.close();
  }
  // Pixel scenes (healthy). Same steps on every tree; the card is clipped at its own box.
  async function shot(page, scene) {
    await page.clock.pauseAt(new Date(Date.parse(INSTANT) + 60000)); await page.waitForTimeout(1200);
    const file = `${name}-${tag}-${scene}.png`, box = await page.locator('.c').boundingBox();
    await page.screenshot({ path: path.join(out, file), clip: { x: Math.round(box.x), y: Math.round(box.y), width: 325, height: 530 } });
    shots.push({ engine: name, tree: tag, scene, file, box });
  }
  let { page } = await fresh('#local=1', LONDON); await shot(page, 'closed'); await page.close();
  ({ page } = await fresh('#local=1', LONDON)); await open(page); await page.waitForTimeout(400); await shot(page, 'open'); await page.close();
  ({ page } = await fresh('#local=1', LONDON)); await open(page); await page.click('#set-reset'); await page.waitForTimeout(2500); await shot(page, 'reset-complete'); await page.close();
  ({ page } = await fresh('#local=1', LONDON)); await open(page);
  await page.evaluate(() => { Storage.prototype.setItem = function () { throw new DOMException('blocked', 'SecurityError'); }; });
  await page.selectOption('#set-units', 'c'); await close(page); await page.waitForTimeout(1500); await shot(page, 'session-only'); await page.close();
  const version = browser.version(); await context.close(); await browser.close();
  return { version, external: [...new Set(external)].sort() };
}
async function diff(name, a, b) {
  const browser = await PW.chromium.launch({ headless: true }), page = await browser.newPage();
  const data = f => 'data:image/png;base64,' + fs.readFileSync(path.join(out, f)).toString('base64');
  const r = await page.evaluate(async ([x, y]) => {
    const load = src => new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = src; });
    const [p, q] = await Promise.all([load(x), load(y)]), w = p.width, h = p.height;
    const px = img => { const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); g.drawImage(img, 0, 0); return g.getImageData(0, 0, w, h).data; };
    const A = px(p), B = px(q); let n = 0, max = 0;
    for (let i = 0; i < A.length; i += 4) { const d = Math.max(Math.abs(A[i] - B[i]), Math.abs(A[i + 1] - B[i + 1]), Math.abs(A[i + 2] - B[i + 2])); if (d) n++; if (d > max) max = d; }
    return { width: w, height: h, sameSize: p.width === q.width && p.height === q.height, differingPixels: n, maxChannelDelta: max };
  }, [data(a), data(b)]);
  await browser.close(); return { engine: name, a, b, ...r };
}
(async () => {
  const report = { scope: 'R0030 native cells; every external request routed to a fixture or aborted; mocked running clock at ' + INSTANT + '; zone Asia/Riyadh; reduced motion',
    inputs: { branch: Object.fromEntries(['index.html', 'config.js'].map(f => [f, sha(fs.readFileSync(path.join(branchRoot, f)))])) },
    playwright: require((args.playwright || 'playwright') + '/package.json').version, engines: {}, cells: [], shots: [], diffs: [] };
  if (mainRoot) report.inputs.main = Object.fromEntries(['index.html', 'config.js'].map(f => [f, sha(fs.readFileSync(path.join(mainRoot, f)))]));
  for (const name of engines) {
    const runs = [['branch', branchRoot]]; if (mainRoot) runs.unshift(['main-a', mainRoot], ['main-b', mainRoot]);
    for (const [tag, root] of runs) {
      const { server, base } = await serve(root);
      try { const r = await engineRun(name, root, base, report.cells, report.shots, tag); report.engines[name] = r.version; report[name + '-' + tag + '-external'] = r.external; }
      finally { server.close(); }
    }
    if (mainRoot) for (const scene of ['closed', 'open', 'reset-complete', 'session-only']) {
      report.diffs.push({ kind: 'noise main-a vs main-b', scene, ...(await diff(name, `${name}-main-a-${scene}.png`, `${name}-main-b-${scene}.png`)) });
      report.diffs.push({ kind: 'main-a vs branch', scene, ...(await diff(name, `${name}-main-a-${scene}.png`, `${name}-branch-${scene}.png`)) });
    }
  }
  report.allPass = report.cells.every(c => c.pass);
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1) + '\n');
  console.log(JSON.stringify(report.cells.map(c => [c.engine, c.cell, c.pass ? 'PASS' : 'FAIL'])));
  console.log(JSON.stringify(report.diffs.map(d => [d.engine, d.scene, d.kind, d.differingPixels, d.maxChannelDelta])));
  if (!report.allPass) process.exitCode = 1;
})().catch(e => { console.error(e); process.exitCode = 1; });
