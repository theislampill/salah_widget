// Controlled late-font discriminator WITHOUT Playwright routing (HTTP cache untouched).
// The font stylesheet and woff2 files are mirrored once from Google Fonts (Firefox UA) and
// served by this script's own HTTP server with configurable delays. The page under test is the
// generated index.html with ONLY the stylesheet href (and optionally one more edit, see --variant)
// changed, served as /diag.html.
// Usage: node ff_font_delay.cjs <siteRoot> <outDir> <arm> <runs> <cssDelayMs> <fontDelayMs> [variant] [seconds]
//   arm: fonts | nofonts (pref gfx.downloadable_fonts.enabled=false)
//   variant: asis | (others added as remedies are tested)
const path = require('path'), fs = require('fs'), http = require('http'), https = require('https');
const pw = require(path.join(process.env.PW_ROOT, 'playwright'));
const [siteRoot, outDir, arm, runsArg, cssDelayArg, fontDelayArg, variantArg, secsArg] = process.argv.slice(2);
const runs = Number(runsArg), cssDelay = Number(cssDelayArg), fontDelay = Number(fontDelayArg), variant = variantArg || 'asis', secs = Number(secsArg || 9);
const GF = 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0';
const mirrorDir = path.join(path.dirname(outDir), 'font-mirror');
const get = url => new Promise((res, rej) => https.get(url, { headers: { 'User-Agent': UA } }, r => { const c = []; r.on('data', d => c.push(d)); r.on('end', () => res(Buffer.concat(c))); }).on('error', rej));

async function mirror() {
  const cssFile = path.join(mirrorDir, 'fonts.css');
  if (fs.existsSync(cssFile)) return;
  fs.mkdirSync(mirrorDir, { recursive: true });
  let css = (await get(GF)).toString('utf8');
  fs.writeFileSync(path.join(mirrorDir, 'original.css'), css);
  const urls = [...new Set(css.match(/https:\/\/fonts\.gstatic\.com\/[^)]+/g))];
  for (let i = 0; i < urls.length; i++) {
    fs.writeFileSync(path.join(mirrorDir, `f${i}.woff2`), await get(urls[i]));
    css = css.split(urls[i]).join(`/__fonts/f${i}.woff2`);
  }
  fs.writeFileSync(cssFile, css);
}

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2' };
const LINK_RE = /<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com\/css2[^>]*>/;
function diagHtml() {
  let html = fs.readFileSync(path.join(siteRoot, 'index.html'), 'utf8');
  const m = html.match(LINK_RE);
  if (!m) throw new Error('font stylesheet link not found');
  let link = m[0].replace(/href="[^"]+"/, 'href="/__fonts/fonts.css"');
  if (variant !== 'asis') {
    const patch = path.join(__dirname, 'variants', variant + '.js');
    ({ html, link } = require(patch)({ html, link, original: m[0] }));
  }
  return html.replace(m[0], link);
}
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
  const send = (body, type, delay) => setTimeout(() => { res.writeHead(200, { 'Content-Type': type, 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'max-age=3600' }); res.end(body); }, delay);
  if (rel === 'diag.html') return send(diagHtml(), 'text/html', 0);
  if (rel === '__fonts/fonts.css') return send(fs.readFileSync(path.join(mirrorDir, 'fonts.css')), 'text/css', cssDelay);
  if (rel.startsWith('__fonts/')) return send(fs.readFileSync(path.join(mirrorDir, path.basename(rel))), 'font/woff2', fontDelay);
  const file = path.resolve(siteRoot, rel || 'index.html');
  fs.readFile(file, (err, data) => { if (err) { res.writeHead(404); return res.end(); } send(data, MIME[path.extname(file)] || 'application/octet-stream', 0); });
});

// In-page observer: event log + a 10x10 px marker at the top-left of the viewport whose colour
// encodes the latest font phase, so video frames can be aligned with page events by pixels.
const observer = () => {
  const log = (window.__fontLog = []);
  const now = () => Math.round(performance.now() * 10) / 10;
  let marker;
  const paint = c => { if (!marker && document.documentElement) { marker = document.createElement('div'); marker.style.cssText = 'position:fixed;left:0;top:0;width:10px;height:10px;z-index:99999;background:#000'; document.documentElement.appendChild(marker); } if (marker) marker.style.background = c; };
  const push = (kind, colour, extra) => { log.push(Object.assign({ t: now(), kind }, extra || {})); if (colour) paint(colour); };
  document.fonts.addEventListener('loading', () => push('fonts.loading', '#00ff00'));
  document.fonts.addEventListener('loadingdone', e => push('fonts.loadingdone', '#0000ff', { n: e.fontfaces.length }));
  document.fonts.addEventListener('loadingerror', () => push('fonts.loadingerror', '#ff00ff'));
  new MutationObserver(ms => { for (const m of ms) if (m.target.tagName === 'LINK' && m.attributeName === 'media') push('link.media=' + m.target.media, '#ff0000'); }).observe(document, { attributes: true, subtree: true, attributeFilter: ['media'] });
  const iv = setInterval(() => { const el = document.querySelector('.times'); if (el && el.textContent.trim().length > 20) { push('dom.rows-populated', '#ffff00'); clearInterval(iv); } }, 16);
};

(async () => {
  await mirror();
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const prefs = Object.assign(arm === 'nofonts' ? { 'gfx.downloadable_fonts.enabled': false } : {}, JSON.parse(process.env.EXTRA_PREFS || '{}'));
  for (let i = 1; i <= runs; i++) {
    const runDir = path.join(outDir, `${process.env.TAG || ''}${variant}-${arm}-css${cssDelay}-font${fontDelay}-${String(i).padStart(2, '0')}`);
    fs.mkdirSync(runDir, { recursive: true });
    const browser = await pw.firefox.launch({ headless: false, firefoxUserPrefs: prefs });
    const context = await browser.newContext({ viewport: { width: 370, height: 570 }, deviceScaleFactor: 1, timezoneId: 'America/New_York', recordVideo: { dir: runDir, size: { width: 370, height: 570 } } });
    await context.addInitScript(observer);
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${port}/diag.html#lat=40.7128&lon=-74.006&label=NewYork&method=2`, { waitUntil: 'commit' });
    await page.waitForTimeout(secs * 1000);
    const fontLog = await page.evaluate(() => window.__fontLog).catch(e => [{ error: String(e) }]);
    const faces = await page.evaluate(() => [...document.fonts].map(f => f.family + '|' + f.weight + '|' + f.status + '|' + f.display)).catch(() => []);
    const used = await page.evaluate(() => ['.cn', '.nt', '.times', '.until-label'].map(s => { const e = document.querySelector(s); return e ? s + ':' + getComputedStyle(e).fontFamily.slice(0, 40) : s + ':absent'; })).catch(() => []);
    const video = page.video();
    await context.close();
    const videoPath = await video.path();
    const version = browser.version();
    await browser.close();
    fs.writeFileSync(path.join(runDir, 'trace.json'), JSON.stringify({ arm, variant, cssDelay, fontDelay, run: i, prefs, firefox: version, fontLog, faces, used, video: path.basename(videoPath) }, null, 1));
    console.log(path.basename(runDir) + ': loaded ' + faces.filter(f => f.includes('|loaded|')).length + '/' + faces.length + '; ' + fontLog.map(e => `${e.kind}@${e.t}`).join(' '));
  }
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
