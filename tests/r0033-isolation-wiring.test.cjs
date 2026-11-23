'use strict';
// R0033 remaining-row native recipes (issue 100): the isolation WIRING, exercised against a fake Playwright
// (tests/r0033-fake-playwright.cjs). Hermetic: no browser, no optional package, no non-loopback connection (the
// only sockets are the module's refusing proxy and the recipe's fixture server, both on 127.0.0.1). It proves what
// tests/r0033-isolation.test.cjs cannot: the catch-all and WebSocket routes exist before any page, the handler's
// dispositions, the ledger bookkeeping, both bypass listeners, the file-entry classification of unrouted file: URLs,
// the awaited server-address check, and the recipe's exit 3 on an escape.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawnSync}=require('node:child_process'),{pathToFileURL}=require('node:url');
const iso=require('../tools/qa/r0033_isolation.cjs'),fake=require('./r0033-fake-playwright.cjs');
const ROOT=path.resolve(__dirname,'..'),ORIGIN='http://127.0.0.1:41234';
const fixture=u=>u.hostname==='api.aladhan.com'&&u.pathname.startsWith('/v1/timings/')?{code:200}:null;
// Non-loopback hosts the widget or a browser could reach, plus look-alikes; none may ever be continued.
const HOSTS=['api.open-meteo.com','api.rainviewer.com','tilecache.rainviewer.com','tile.openstreetmap.org','a.tile.openstreetmap.org','nominatim.openstreetmap.org',
  'get.geojs.io','ipapi.co','fonts.googleapis.com','fonts.gstatic.com','cdn.jsdelivr.net','unpkg.com','api.aladhan.com','theislampill.github.io','github.com',
  'clients2.google.com','update.googleapis.com','safebrowsing.googleapis.com','detectportal.firefox.com','example.com','127.0.0.1.example.com','localhost.example.com',
  '8.8.8.8','10.0.0.1','192.168.1.1','[2001:db8::1]'];
async function run(scenario,policy={origin:ORIGIN,fixture},opts={}){
  const PW=fake.create(scenario),S=await iso.launch(PW,'chromium');
  try{const C=await S.context({viewport:{width:325,height:530}},policy),page=await C.newPage();await page.goto(opts.url||ORIGIN+'/index.html');await S.settle();
    return {log:PW.log,ledger:S.ledger,verdict:S.verdict()};}
  finally{await S.close();}
}
const dispositions=log=>Object.fromEntries(log.filter(e=>e.call==='disposition').map(e=>[e.url,e.disposition]));

test('R33-WIRE-01 the Node guard precedes the launch; both routes precede the first page; service workers are blocked; the proxy is loopback',async()=>{
  const {log}=await run({});
  const at=c=>log.findIndex(e=>e.call===c);
  assert.equal(log[at('launch')].guardInstalled,true);
  assert.match(log[at('launch')].proxy.server,/^http:\/\/127\.0\.0\.1:\d+$/);
  assert.ok(at('route')>at('newContext')&&at('routeWebSocket')>at('newContext'));
  assert.ok(at('route')<at('newPage')&&at('routeWebSocket')<at('newPage'),'routes before the page');
  assert.equal(log[at('route')].pattern,'**/*');assert.equal(log[at('route')].pagesBefore,0);
  assert.deepEqual(log[at('newPage')].routesInstalled,['**/*']);
  assert.equal(log[at('newContext')].serviceWorkers,'block');
  assert.equal(log.some(e=>e.call==='unroute'||e.call==='unrouteAll'),false);
  for(const evt of ['requestfinished','requestfailed','response'])assert.ok(log.some(e=>e.call==='context.on'&&e.evt===evt),evt);
});

test('R33-WIRE-02 handler dispositions: fixture origin continues, the provider fixture is fulfilled, every non-loopback host is aborted',async()=>{
  const requests=[{url:ORIGIN+'/index.html',type:'document'},{url:ORIGIN+'/moon/assets/dem.bin.gz'},{url:'https://api.aladhan.com/v1/timings/08-09-2026?latitude=24.47'},
    {url:'http://127.0.0.1:9/elsewhere'},...HOSTS.flatMap(h=>[{url:'https://'+h+'/x'},{url:'http://'+h+':80/y'}]),{url:'data:image/png;base64,AAAA'}];
  const {log,ledger,verdict}=await run({requests}),d=dispositions(log);
  assert.equal(d[ORIGIN+'/index.html'],'continue');assert.equal(d[ORIGIN+'/moon/assets/dem.bin.gz'],'continue');
  assert.equal(d['https://api.aladhan.com/v1/timings/08-09-2026?latitude=24.47'],'fulfill');
  assert.equal(d['http://127.0.0.1:9/elsewhere'],'abort');
  for(const h of HOSTS){assert.equal(d['https://'+h+'/x'],'abort',h);assert.equal(d['http://'+h+':80/y'],'abort',h);}
  assert.equal(ledger.requests.length,requests.length);
  assert.equal(ledger.continued,3);assert.equal(ledger.fulfilled,1);assert.equal(ledger.aborted,requests.length-4);
  assert.equal(verdict.ok,true);assert.equal(verdict.escapes.length,0);
  assert.ok(verdict.abortedHosts.includes('tile.openstreetmap.org'));
});

test('R33-WIRE-03 a broken policy that continues a non-loopback request is caught by the ledger, not trusted',async()=>{
  const original=iso.classify;iso.classify=()=>({action:'continue',why:'broken-policy',host:'example.com'});
  try{const {log,ledger,verdict}=await run({requests:[{url:'https://example.com/leak'}]});
    assert.equal(dispositions(log)['https://example.com/leak'],'continue');
    assert.equal(ledger.offLoopbackContinued.length,1);assert.equal(verdict.ok,false);assert.equal(verdict.escapes[0].kind,'continued-off-loopback');}
  finally{iso.classify=original;}
});

test('R33-WIRE-04 a request that never passed the route is an escape, from either listener',async()=>{
  for(const fail of [false,true]){
    const {ledger,verdict}=await run({bypass:[{url:'https://api.open-meteo.com/v1/forecast',fail}]});
    assert.equal(ledger.bypassed.length,1,'fail='+fail);assert.equal(verdict.ok,false);assert.equal(verdict.escapes[0].kind,'bypassed-route');
  }
  const local=await run({bypass:[{url:'data:text/plain,x'},{url:'blob:'+ORIGIN+'/0'},{url:'about:blank'}]});
  assert.equal(local.verdict.ok,true);
});

test('R33-WIRE-05 file entry: an unrouted in-tree file: URL is logged, not an escape; anything else unrouted still is',async()=>{
  const inside=pathToFileURL(path.join(ROOT,'index.html')).href+'#lat=24.47',chunk=pathToFileURL(path.join(ROOT,'moon','file-data','x.js')).href;
  const outside=pathToFileURL(path.join(ROOT,'..','elsewhere.html')).href,file={origin:null,fileRoot:ROOT,fixture};
  const ok=await run({bypass:[{url:inside,type:'document'},{url:chunk,type:'script',fail:true}]},file,{url:inside});
  assert.equal(ok.verdict.ok,true);assert.equal(ok.ledger.fileUnrouted.length,2);assert.equal(ok.verdict.fileUnrouted,2);
  assert.ok(ok.ledger.requests.every(r=>r.why==='file-entry-unrouted'));
  for(const url of [outside,'https://api.open-meteo.com/v1/forecast','http://127.0.0.1:9/x']){
    const bad=await run({bypass:[{url}]},file,{url:inside});assert.equal(bad.verdict.ok,false,url);assert.equal(bad.verdict.escapes[0].kind,'bypassed-route');
  }
  const notFileCell=await run({bypass:[{url:inside}]});assert.equal(notFileCell.verdict.ok,false,'no fileRoot: an unrouted file: URL is an escape');
  const routed=await run({requests:[{url:inside}]},file,{url:inside});assert.equal(dispositions(routed.log)[inside],'continue');assert.equal(routed.verdict.ok,true);
});

test('R33-WIRE-06 a late non-loopback server address is awaited and fails the verdict; a context without a WebSocket route is refused',async()=>{
  const {verdict}=await run({responses:[{url:ORIGIN+'/index.html',ip:'93.184.216.34'}]});
  assert.equal(verdict.ok,false);assert.equal(verdict.escapes[0].kind,'response-off-loopback');
  const clean=await run({responses:[{url:ORIGIN+'/index.html',ip:'127.0.0.1'}]});assert.equal(clean.verdict.ok,true);
  const L=await iso.launch(fake.create({responses:[{url:ORIGIN+'/x',ip:'93.184.216.34'}]}),'chromium');   // close() alone must also wait
  await (await (await L.context({},{origin:ORIGIN,fixture})).newPage()).goto(ORIGIN+'/x');await L.close();assert.equal(L.verdict().ok,false);
  const S=await iso.launch(fake.create({noRouteWebSocket:true}),'chromium');
  try{await assert.rejects(S.context({},{origin:ORIGIN,fixture}),/no routeWebSocket/);}finally{await S.close();}
  const T=await iso.launch(fake.create({}),'chromium');
  try{await assert.rejects(T.context({},{origin:'http://example.com:80',fixture}),/must be loopback/);}finally{await T.close();}
});

// The recipe end to end (smoke cell) in a child process against the fake: exit 0 when clean, exit 3 on any escape.
function recipe(scenario){
  const out=fs.mkdtempSync(path.join(os.tmpdir(),'r0033-wire-')),logFile=path.join(out,'fake-log.json');
  try{const r=spawnSync(process.execPath,[path.join(ROOT,'tools','qa','r0033_remaining_cells.cjs'),'--cell','smoke','--root',ROOT,'--out',out,'--engine','chromium','--playwright',path.join(__dirname,'r0033-fake-playwright.cjs')],
      {encoding:'utf8',timeout:60000,env:{...process.env,R33_FAKE:JSON.stringify(scenario),R33_FAKE_LOG:logFile}});
    const requests=JSON.parse(fs.readFileSync(path.join(out,'smoke-chromium-requests.json'),'utf8')),log=JSON.parse(fs.readFileSync(logFile,'utf8'));
    return {status:r.status,stdout:r.stdout,stderr:r.stderr,requests,log};}
  finally{fs.rmSync(out,{recursive:true,force:true});}
}
test('R33-WIRE-07 the recipe exits 0 on a clean run and 3 when any request escaped the route, whatever the cell reported',()=>{
  const clean=recipe({requests:[{url:'https://api.open-meteo.com/v1/forecast'},{url:'https://tile.openstreetmap.org/1/1/1.png'}]});
  assert.equal(clean.status,0,clean.stderr);const line=JSON.parse(clean.stdout.trim().split('\n').pop());
  assert.equal(line.status,'PASS');assert.equal(line.isolation.ok,true);assert.deepEqual(line.isolation.abortedHosts.sort(),['api.open-meteo.com','tile.openstreetmap.org']);
  assert.equal(clean.requests.verdict.ok,true);assert.equal(clean.requests.requests.length,2);
  assert.ok(clean.log.findIndex(e=>e.call==='route')<clean.log.findIndex(e=>e.call==='newPage'));
  for(const scenario of [{bypass:[{url:'https://api.rainviewer.com/public/weather-maps.json'}]},{responses:[{url:'http://127.0.0.1/x',ip:'93.184.216.34'}]}]){
    const r=recipe(scenario);assert.equal(r.status,3,JSON.stringify(scenario));assert.match(r.stderr,/ISOLATION ESCAPE/);assert.equal(r.requests.verdict.ok,false);
  }
});
