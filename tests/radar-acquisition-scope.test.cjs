'use strict';
// R0032 (issue 99) machine RA — radar acquisition scope (ISM-WX-004), owner decision D-32-1 = A2:
// live radar acquisition is OFF in every product configuration; the authored acquisition code, its host
// admission and its diagnostics are retained and reachable only by test harnesses that call the authored
// fetchRadar() directly. Product paths are exercised through the complete authored runtime
// (tests/r0032-fixture.cjs); the retained path through the accepted r000c source fixture. No provider is
// contacted: every transport is a recorded double.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const {runtime,sourcePath}=require('./r0032-fixture.cjs');
const root=path.resolve(__dirname,'..');
// The retained-path fixture binds the generated entry (index.html), as r000d does; product paths bind src/native.
const fixturePath=path.join(__dirname,'r000c-weather.test.cjs'),fixtureText=fs.readFileSync(fixturePath,'utf8');
const end=fixtureText.indexOf("test('control: actual fresh acquisition");assert(end>0);
const fixtureModule=new Module(fixturePath,module);fixtureModule.filename=fixturePath;fixtureModule.paths=Module._nodeModulePaths(__dirname);
fixtureModule._compile(fixtureText.slice(0,end)+'\nmodule.exports={fixture,NOW};',fixturePath);
const {fixture,NOW}=fixtureModule.exports;
const source=fs.readFileSync(sourcePath,'utf8');
const SEC=NOW/1000,HOST='https://tilecache.rainviewer.com';
const manifestWith=(host,p='/v2/radar/'+SEC)=>({generated:SEC,host,radar:{past:[{time:SEC,path:p}]}});
const tile=(x,y,p='/v2/radar/'+SEC)=>HOST+p+'/256/6/'+x+'/'+y+'/2/1_1.png';
const external=r=>r.imageSrcs().filter(s=>!s.startsWith('data:'));
const counts=r=>{const c={};for(const x of r.log)c[x.host]=(c[x.host]||0)+1;return c;};
async function frames(r,n,ms=30001){for(let i=0;i<n;i++){await r.frame(ms);while([...r.timers.values()].some(t=>t.at<=r.clock.now))r.advanceTimer();await r.flush(2);}}
async function drive(r,code){let done=false;const p=r.run(code);Promise.resolve(p).then(()=>{done=true;},()=>{done=true;});
  for(let i=0;i<200&&!done;i++){await r.flush(2);if(!r.advanceTask()&&!r.advanceFrame())r.advanceTimer();}assert.ok(done,code+' settled');return p;}

// ---- R32-02: product paths issue zero radar requests ------------------------------------------------------------
test('R32-02 live boot plus 60 modelled minutes of loop polls and renewals: zero RainViewer manifest or tile requests',async()=>{
  const r=runtime();await r.boot();await frames(r,120);
  const c=counts(r);
  assert.equal(r.radarRequests(),0,'radar requests in product paths: '+JSON.stringify(c)+' '+JSON.stringify(external(r)));
  assert.equal(c['api.rainviewer.com']||0,0);assert.deepEqual(external(r),[]);
  // I3: weather acquisition is independent of radar enablement; the header still carries the admitted model value.
  assert.ok((c['api.open-meteo.com']||0)>=4,'weather requests continue: '+JSON.stringify(c));
  assert.equal(r.run('weather&&weather.temp'),24);
});
test('R32-02 location change, renewal and long idle: zero radar requests, weather follows the new target',async()=>{
  const r=runtime();await r.boot();await frames(r,10);
  r.ctx.__cfgB={lat:21.42,lon:39.83,tz:'Asia/Riyadh',label:'Makkah',method:'4',school:'0',time:'24',units:'c',datefmt:'YYYY-MM-DD',source:'manual'};
  await drive(r,'applyConfig(__cfgB)');await frames(r,40);
  await frames(r,1,3*3600000);await frames(r,40);           // long idle: one three-hour gap, then ordinary polls
  assert.equal(r.radarRequests(),0,JSON.stringify(counts(r)));
  assert.ok(r.log.some(x=>x.host==='api.open-meteo.com'&&x.url.includes('latitude=21.42')),'weather requested for B');
});
test('R32-03 A2: no URL fragment, query-shaped fragment flag or configuration field enables product radar',async()=>{
  for(const extra of ['&radar=1','&debugRadar=1','&radarAcquisition=1','&simRadar=1','&debugRadar=1&qa=1']){
    const r=runtime({hash:'#lat=24.47&lon=39.61&label=Madinah&tz=Asia%2FRiyadh&units=c&method=4'+extra});await r.boot();await frames(r,25);
    assert.equal(r.radarRequests(),0,extra);
  }
  const r=runtime();await r.boot();
  r.ctx.__cfgR={lat:24.47,lon:39.61,tz:'Asia/Riyadh',label:'Madinah',method:'4',school:'0',time:'24',units:'f',datefmt:'YYYY-MM-DD',source:'manual',radar:true,debugRadar:true};
  await drive(r,'applyConfig(__cfgR)');await frames(r,25);assert.equal(r.radarRequests(),0);
});
test('R32-02 postcondition: qaState reports radar as not acquired with an explicit reason, not "unavailable / simulation"',async()=>{
  const r=runtime();await r.boot();const t=r.run('qaState().wxTruth');
  assert.equal(t.radarSource,'none (radar acquisition disabled in the product)');
  assert.deepEqual({...t.radarAcquisition},{enabled:false,reason:'disabled in the product (R0032 D-32-1 A2; retained for tests only)'});
  assert.equal(t.radarAvailable,false);assert.equal(t.requests.radar,null);
});
test('R32-03 A2 source search: one predicate, a literal off, and the product entry is the gate',()=>{
  const code=source.replace(/\/\/[^\n]*/g,'');                           // identifiers in code, not in comments
  assert.match(code,/const RADAR_ACQUISITION=Object\.freeze\(\{enabled:false,/);
  assert.equal(code.split('RADAR_ACQUISITION').length-1,3,'declaration, predicate and qa reason only');
  assert.match(code,/function radarAcquisitionEnabled\(\)\{ return RADAR_ACQUISITION\.enabled===true; \}/);
  assert.match(code,/async function fetchRadar\(\)\{ if\(!radarAcquisitionEnabled\(\)\) return; return acquireRadar\(\); \}/);
  assert.equal(code.split('acquireRadar(').length-1,2,'definition and the gate are the only references');
  assert.equal(code.split('fetchRadar();').length-1,3,'boot, startWeather (apply) and the loop poll call the gate');
});

// ---- Retained (test-only) path: host admission R32-04 --------------------------------------------------------------
test('R32-04 control: the allowlisted https host reaches the image stage with the unchanged tile URL',async()=>{
  const f=fixture({manifest:manifestWith(HOST)});await f.fetchRadar();
  assert.deepEqual(f.images,[tile(39,27)]);assert.ok(f.read().weatherRadar.sample);
  assert.equal(f.radarPrecipNow(),0);                                     // R32-05: no authority change
});
for(const [name,host] of [['plain http',' http://tilecache.rainviewer.com'.trim()],['foreign host','https://tiles.example.net'],
  ['suffix host','https://tilecache.rainviewer.com.example.net'],['userinfo','https://user:pw@tilecache.rainviewer.com'],
  ['port','https://tilecache.rainviewer.com:8443'],['host path','https://tilecache.rainviewer.com/extra'],
  ['host query','https://tilecache.rainviewer.com?x=1'],['host fragment','https://tilecache.rainviewer.com#x'],
  ['protocol-relative','//tilecache.rainviewer.com'],['non-string host',42]]){
  test('R32-04 host admission rejects '+name+': no image request, rejection reason recorded',async()=>{
    const f=fixture({manifest:manifestWith(host)});await f.fetchRadar();
    assert.deepEqual(f.images,[]);assert.equal(f.read().weatherRadar,null);
    const req=f.view().qa.wxTruth.requests.radar;assert.equal(req.state,'rejected');assert.equal(req.reason,'radar tile host not admitted');
  });
}
for(const [name,p] of [['absolute URL path','https://tiles.example.net/v2/radar/1'],['protocol-relative path','//tiles.example.net/v2/radar/1'],
  ['dot-dot path','/v2/radar/../../x'],['trailing dot-dot','/v2/radar/1/..'],['query in path','/v2/radar/1?x=1'],
  ['relative path','v2/radar/1'],['dot segment','/v2/radar/.'],['dot-dot segment','/v2/radar/..'],['empty frame id','/v2/radar/'],['other prefix','/v3/tiles/1']]){
  test('R32-04 frame path admission rejects '+name+': no image request',async()=>{
    const f=fixture({manifest:manifestWith(HOST,p)});await f.fetchRadar();
    assert.deepEqual(f.images,[]);
    const req=f.view().qa.wxTruth.requests.radar;assert.equal(req.state,'rejected');assert.equal(req.reason,'radar frame path not admitted');
  });
}

// ---- Retained path: tile indices at extreme latitude and the antimeridian (registry candidate CI-05) ------------------
for(const la of [86,-86]){
  test('CI-05 latitude '+la+'° (beyond Web Mercator ±85.0511°) is rejected before any tile request',async()=>{
    const f=fixture({lat:la,lon:39.61});await f.fetchRadar();
    assert.deepEqual(f.images,[],'no out-of-range tile row may be requested');
    const req=f.view().qa.wxTruth.requests.radar;assert.equal(req.state,'rejected');assert.equal(req.reason,'radar tile index outside Web Mercator');
  });
}
test('CI-05 longitude +180 addresses the in-range column 0 (the same meridian as -180), never column 2^z',async()=>{
  const f=fixture({lat:24.47,lon:180});await f.fetchRadar();
  assert.equal(f.images.length,1);const x=+f.images[0].split('/256/6/')[1].split('/')[0];
  assert.equal(x,0);assert.ok(f.read().weatherRadar.sample);
});
test('CI-05 longitude -180 and +180 address the same tile (pair case)',async()=>{
  const a=fixture({lat:24.47,lon:-180}),b=fixture({lat:24.47,lon:180});await a.fetchRadar();await b.fetchRadar();
  assert.equal(a.images.length,1);assert.deepEqual(b.images,a.images);
});
test('CI-05 control: longitude -180 keeps column 0 and an in-range latitude keeps its row',async()=>{
  const f=fixture({lat:85,lon:-180});await f.fetchRadar();
  assert.equal(f.images.length,1);const [x,y]=f.images[0].split('/256/6/')[1].split('/').map(Number);
  assert.equal(x,0);assert.ok(y>=0&&y<64);
});
test('CI-05 longitude outside [-180, 180] is rejected, not wrapped',async()=>{
  for(const lo of [180.5,-181]){const f=fixture({lat:24.47,lon:lo});await f.fetchRadar();assert.deepEqual(f.images,[],String(lo));}
});

// Unit cases on the retained tile-index function itself (the coordinate admission upstream hides out-of-domain
// longitudes from fetchRadar, so the guard is discriminated directly). Bound from the generated entry.
const generated=fs.readFileSync(process.env.SALAH_WEATHER_SOURCE||path.join(__dirname,'..','index.html'),'utf8');
function tileIndexFn(){const a=generated.indexOf('function radarTileIndex(');if(a<0)return null;
  const b=generated.indexOf('\n}\n',a);return new Function(generated.slice(a,b+2)+'\nreturn radarTileIndex;')();}
test('CI-05 unit: longitude outside [-180, 180] is rejected, never wrapped to a valid column',()=>{
  const f=tileIndexFn();assert.equal(typeof f,'function','radarTileIndex present');
  for(const lo of [190,-190,180.5,-180.5,360,NaN,Infinity])assert.equal(f(24.47,lo,6),null,String(lo));
  assert.equal(f(24.47,180,6).xt,0);assert.equal(f(24.47,-180,6).xt,0);assert.equal(f(24.47,39.61,6).xt,39);
  for(const la of [86,-86,90,-90])assert.equal(f(la,39.61,6),null,String(la));
});
