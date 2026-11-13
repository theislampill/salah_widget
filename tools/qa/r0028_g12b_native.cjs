'use strict';
// R0028 G-12(b) native observation. Serves the tree on 127.0.0.1; every non-loopback request is
// either fulfilled from a fixture (prayer timings) or aborted. Frozen clock, forced timezone.
// Usage: node tools/qa/r0028_g12b_native.cjs <tree root> <directory containing the playwright package>
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const [root, pwDir] = process.argv.slice(2);
const pw = require(path.join(pwDir, 'playwright'));
const types = {'.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.wasm': 'application/wasm', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.bin': 'application/octet-stream'};
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/^\/+/, '');
  const file = path.resolve(root, rel || 'index.html');
  if (!file.startsWith(path.resolve(root)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'content-type': types[path.extname(file)] || 'application/octet-stream'});
  fs.createReadStream(file).pipe(res);
});
function timings(dateStr) {
  return {code: 200, status: 'OK', data: {timings: {Fajr: '04:46', Sunrise: '06:05', Dhuhr: '12:19', Asr: '15:48', Maghrib: '18:33', Sunset: '18:33', Isha: '20:03'},
    meta: {timezone: 'Asia/Riyadh', method: {id: 4, params: {Fajr: 18.5, Isha: '90 min'}}},
    date: {gregorian: {date: dateStr, day: +dateStr.slice(0, 2), month: {number: +dateStr.slice(3, 5), en: 'September'}, year: +dateStr.slice(6)},
      hijri: {day: 26, month: {number: 3, en: 'Rabi'}, year: 1448}}}};
}
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port, results = [], external = [];
  for (const name of ['chromium', 'firefox', 'webkit']) {
    const browser = await pw[name].launch();
    const context = await browser.newContext({timezoneId: 'Asia/Riyadh', locale: 'en-US', viewport: {width: 325, height: 530}, reducedMotion: 'reduce'});
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.hostname === '127.0.0.1') return route.continue();
      external.push(name + ' ' + url.hostname);
      const m = /timings\/(\d{2}-\d{2}-\d{4})/.exec(url.pathname);
      if (url.hostname.endsWith('aladhan.com') && m) return route.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify(timings(m[1]))});
      return route.abort();
    });
    const page = await context.newPage();
    await page.clock.install({time: new Date('2026-09-08T09:30:00Z')});
    await page.goto('http://127.0.0.1:' + port + '/index.html#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&simWx=95&simPrecip=5&qa=1');
    await page.clock.runFor(3000);
    await page.waitForFunction(() => typeof window.qaState === 'function' && window.qaState().wxTruth, null, {timeout: 20000});
    const truth = await page.evaluate(() => { const q = window.qaState(); return {wxTruth: q.wxTruth, fx: document.querySelector('.c')?.dataset.fx ?? null}; });
    results.push({engine: name, version: browser.version(), truth});
    await browser.close();
  }
  server.close();
  console.log(JSON.stringify({results, externalRequests: external}, null, 1));
})().catch(e => { console.error(e); server.close(); process.exit(1); });
