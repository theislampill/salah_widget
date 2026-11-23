'use strict';
// R0033 remaining-row native recipes (issue 100): unit tests of the browser-isolation policy they all start through
// (tools/qa/r0033_isolation.cjs). Hermetic: no browser, no network, no optional package. The pure policy
// (classify) and the escape verdict are exercised directly; the recipes are checked statically for the rules a
// unit test cannot observe (no unroute, no browser or context outside the isolation module).
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const iso=require('../tools/qa/r0033_isolation.cjs');
const ORIGIN='http://127.0.0.1:41234',ROOT=path.resolve(__dirname,'..');
const fixture=u=>u.hostname==='api.aladhan.com'&&u.pathname.startsWith('/v1/timings/')?{code:200}:null;
const policy=p=>raw=>iso.classify(raw,p);

test('R33-ISO-01 only the exact loopback fixture origin continues over http',()=>{
  const c=policy({origin:ORIGIN,fixture});
  assert.deepEqual([c(ORIGIN+'/index.html').action,c(ORIGIN+'/moon/assets/dem.bin.gz').action],['continue','continue']);
  for(const raw of ['http://127.0.0.1:41235/index.html','https://127.0.0.1:41234/index.html','http://localhost:41234/index.html','http://[::1]:41234/x'])
    assert.equal(c(raw).action,'abort',raw);
  assert.equal(c('http://127.0.0.1:41235/x').why,'loopback-not-fixture-origin');
});

test('R33-ISO-02 every non-loopback destination is aborted, including look-alike hosts and userinfo tricks',()=>{
  const c=policy({origin:ORIGIN,fixture});
  for(const raw of ['https://api.open-meteo.com/v1/forecast?latitude=24.47','https://api.rainviewer.com/public/weather-maps.json','https://fonts.googleapis.com/css2?family=Inter',
    'https://nominatim.openstreetmap.org/reverse','https://get.geojs.io/v1/ip/geo.json','http://127.0.0.1.example.com/','http://127.0.0.1:41234'+'@'+'example.com/','http://example.com:41234/index.html',
    'https://api.aladhan.com/v1/calendar/2026/9','ws://example.com/socket','wss://127.0.0.1:41234/socket','ftp://example.com/x','not a url'])
    assert.equal(c(raw).action,'abort',raw);
  assert.equal(c('https://api.open-meteo.com/v1/forecast').why,'non-loopback');
});

test('R33-ISO-03 a provider URL is fulfilled only from the supplied fixture and never continued',()=>{
  const c=policy({origin:ORIGIN,fixture}),r=c('https://api.aladhan.com/v1/timings/08-09-2026?latitude=24.47&longitude=39.61&method=4');
  assert.equal(r.action,'fulfill');assert.deepEqual(r.body,{code:200});
  assert.equal(policy({origin:ORIGIN,fixture:null})('https://api.aladhan.com/v1/timings/08-09-2026').action,'abort');
});

test('R33-ISO-04 data:, blob: and about: stay local; file: is admitted only inside the served tree of a file-entry cell',()=>{
  const c=policy({origin:ORIGIN,fixture});
  for(const raw of ['data:image/png;base64,AAAA','blob:'+ORIGIN+'/0b0f','about:blank'])assert.equal(c(raw).action,'continue',raw);
  const inside=pathToFileURL(path.join(ROOT,'index.html')).href,outside=pathToFileURL(path.join(ROOT,'..','elsewhere.html')).href;
  assert.equal(c(inside).action,'abort');assert.equal(c(inside).why,'file-not-admitted');
  const f=policy({origin:null,fileRoot:ROOT,fixture});
  assert.equal(f(inside+'#lat=24.47').action,'continue');
  assert.equal(f(pathToFileURL(path.join(ROOT,'moon','file-data','r0033-withheld-chunk.js')).href).action,'continue');
  assert.equal(f(outside).action,'abort');assert.equal(f(outside).why,'file-outside-root');
  assert.equal(f('file://fileserver.example.com/share/index.html').why,'file-remote-host');
  assert.equal(f(ORIGIN+'/index.html').action,'abort','a file-entry cell has no http origin');
});

test('R33-ISO-05 the verdict fails on every kind of escape and passes on a clean ledger',()=>{
  const clean=iso.newLedger();clean.requests.push({action:'abort',host:'api.rainviewer.com'},{action:'continue',host:'127.0.0.1'});clean.aborted=1;clean.continued=1;
  const v=iso.verdict(clean);assert.equal(v.ok,true);assert.deepEqual(v.abortedHosts,['api.rainviewer.com']);assert.equal(v.seen,2);
  for(const [field,kind] of [['offLoopbackContinued','continued-off-loopback'],['bypassed','bypassed-route'],['offLoopbackResponses','response-off-loopback'],['proxyRefused','reached-proxy']]){
    const l=iso.newLedger();l[field].push({url:'https://example.com/'});const r=iso.verdict(l);assert.equal(r.ok,false,field);assert.equal(r.escapes[0].kind,kind);
  }
  const n=iso.verdict(iso.newLedger(),[{kind:'socket',target:'example.com:443'}]);assert.equal(n.ok,false);assert.equal(n.escapes[0].kind,'node-refused');assert.equal(n.escapes[0].refusal,'socket');
});

test('R33-ISO-06 static rules: the route precedes any page, nothing removes it, and the recipes start browsers only through the module',()=>{
  const module_=fs.readFileSync(path.join(ROOT,'tools','qa','r0033_isolation.cjs'),'utf8'),cells=fs.readFileSync(path.join(ROOT,'tools','qa','r0033_remaining_cells.cjs'),'utf8');
  for(const [name,text] of [['module',module_],['cells',cells]])assert.equal(/\.unroute(All)?\s*\(/.test(text),false,name+' must never remove a route');
  const route=module_.indexOf("ctx.route('**/*'"),page=module_.indexOf('ctx.newPage()');
  assert.ok(route>0&&page>route,'the catch-all route is installed before the context can create a page');
  assert.ok(module_.indexOf('guard.install();')<module_.indexOf('.launch({'),'the Node guard is installed before a browser is launched');
  assert.match(module_,/serviceWorkers:'block'/);assert.match(module_,/proxy:\{server:'http:\/\/127\.0\.0\.1:'/);
  assert.equal(/\.newContext\s*\(|\]\.launch\s*\(|\.launchPersistentContext\s*\(|\.connect(OverCDP)?\s*\(/.test(cells),false,'recipes open no browser or context of their own');
  assert.match(cells,/^require\('\.\/v1_net_guard\.cjs'\)\.install\(\);/m);
  assert.match(cells,/process\.exitCode=3/);
  // Synthetic fixture only: no geolocation is granted or read, and no repository document is opened as a page.
  assert.equal(/geolocation/.test(cells.replace('no geolocation permission is granted','')),false);
  assert.equal(/permissions\s*:/.test(cells),false);
  const targets=[...cells.matchAll(/\.goto\(([^;]*?)\);/g)].map(m=>m[1]);
  assert.equal(targets.length,3);for(const t of targets)assert.match(t,/index\.html|tests\/smoke\.html|^url$/,t);
  assert.equal(/README|\.md\b/.test(cells),false);
});
