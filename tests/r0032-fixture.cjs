'use strict';
// R0032 (issue 99) source-bound fixture. The COMPLETE authored runtime of src/native/index.html runs in a VM
// through the accepted r001d harness (the same authored-source ingress weather-no-timetable-fixture uses).
// Only browser boundaries are doubles: a routing fetch that records every request by host, an Image double
// that records every dispatched src, an enumerable localStorage double that records reads, enumerations and
// removals, and the harness clock. Nothing here contacts a provider. This is source-consumer evidence, not a
// browser/pixel qualification (the native recipe is tools/qa/run_r0032_native.cjs).
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const root=path.resolve(__dirname,'..'),harnessPath=path.join(__dirname,'r001d-harness.cjs');
const harness=fs.readFileSync(harnessPath,'utf8'),configRead="fs.readFileSync(path.join(root,'config.js'),'utf8')";
assert.equal(harness.split(configRead).length,2,'one contained config boundary');
const {extractAuthored}=require('./weather-no-timetable-fixture.cjs');
const {SetupError}=require('./native-script-contract.js');
const harnessModule=new Module(harnessPath,module);harnessModule.filename=harnessPath;harnessModule.paths=Module._nodeModulePaths(__dirname);
harnessModule.r0032Extractor={nativeInlineRuntime:extractAuthored,SetupError};
const runtimeImport="const {nativeInlineRuntime,SetupError}=require('./native-inline-runtime.cjs');";
assert.equal(harness.split(runtimeImport).length,2,'one explicit runtime extraction boundary');
harnessModule._compile(harness.replace(configRead,"fs.readFileSync(path.join(root,'src/native/config.js'),'utf8')").replace(runtimeImport,'const {nativeInlineRuntime,SetupError}=module.r0032Extractor;'),harnessPath);
const {load,prayerForDate}=harnessModule.exports;
const sourcePath=process.env.SALAH_R0032_SOURCE||path.join(root,'src/native/index.html');
const LIVE='#lat=24.47&lon=39.61&label=Madinah&tz=Asia%2FRiyadh&units=c&method=4';
const flush=async(n=8)=>{for(let i=0;i<n;i++)await new Promise(r=>setImmediate(r));};

// Healthy Open-Meteo body for the request's own clock (step floor(now,15 min) in Asia/Riyadh wall text).
function weatherBody(wall,{elevation=100,is_day=0}={}){
  const q=Math.floor(wall/900000)*900000,iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16),hr=q-q%3600000;
  return {timezone:'Asia/Riyadh',elevation,current_units:{temperature_2m:'°C',wind_speed_10m:'m/s'},
    current:{time:iso(q),interval:900,weather_code:2,temperature_2m:24,apparent_temperature:24,relative_humidity_2m:80,dew_point_2m:18,
      wind_speed_10m:3,wind_direction_10m:225,wind_gusts_10m:5,precipitation:0,rain:0,showers:0,snowfall:0,is_day,cloud_cover:30,
      cloud_cover_low:0,cloud_cover_mid:8,cloud_cover_high:28,visibility:6000},
    hourly:{time:[iso(hr-3600000),iso(hr),iso(hr+3600000),iso(hr+7200000)],temperature_2m:[24,23,22,21],weather_code:[2,2,2,2],
      cloud_cover:[30,30,30,30],precipitation:[0,0,0,0]}};
}
function manifest(wall){const s=Math.floor(wall/1000);return {generated:s,host:'https://tilecache.rainviewer.com',radar:{past:[{time:s,path:'/v2/radar/'+s}]}};}

// route(u,h) may return a response object, a promise, or undefined for the default healthy route.
function runtime({hash=LIVE,source,route=null,storage=[]}={}){
  const h=load({sourcePath,source,hash});
  const log=[],reads=[],removes=[],enumerations={count:0};
  for(const [k,v] of storage)h.storage.set(k,v);
  // Enumerable storage double (the harness double has no key()/length); every effect is recorded.
  const ls={getItem(k){reads.push(k);return h.storage.has(k)?h.storage.get(k):null;},setItem(k,v){h.storage.set(k,String(v));},
    removeItem(k){removes.push(k);h.storage.delete(k);},key(i){enumerations.count++;return [...h.storage.keys()][i]??null;}};
  Object.defineProperty(ls,'length',{configurable:true,get(){enumerations.count++;return h.storage.size;}});
  h.ctx.localStorage=ls;
  h.ctx.fetch=async(url)=>{
    const u=new URL(String(url));log.push({host:u.hostname,path:u.pathname,url:String(url),at:h.clock.wall});
    const routed=route?route(u,h):undefined;if(routed!==undefined)return routed;
    if(u.hostname==='api.aladhan.com'){const d=/\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u.pathname)[1];return {ok:true,status:200,json:async()=>({code:200,status:'OK',data:prayerForDate(d)})};}
    if(u.hostname==='api.open-meteo.com')return {ok:true,status:200,json:async()=>weatherBody(h.clock.wall)};
    if(u.hostname==='api.rainviewer.com')return {ok:true,status:200,json:async()=>manifest(h.clock.wall)};
    throw Error('R0032 fixture denies network '+u.hostname);
  };
  const imageSrcs=()=>h.images.map(i=>i._src).filter(Boolean);
  const radarRequests=()=>log.filter(r=>/rainviewer/i.test(r.host)).length+imageSrcs().filter(s=>/rainviewer/i.test(s)).length;
  // The boot entrypoint, its two paint opportunities and posted task, then the render loop's frames.
  // Ready posted tasks and frames run first; boot-owned timers are delivered only while boot is unsettled.
  async function boot(){let done=false;const p=h.run('boot()');p.then(()=>{done=true;},()=>{done=true;});
    for(let i=0;i<200&&!done;i++){await flush(2);if(!h.advanceTask()&&!h.advanceFrame())h.advanceTimer();}
    await flush();assert.ok(done,'boot settled within the fixture budget');return p;}
  // One loop frame after `ms` of elapsed and wall time (frames are the loop's only poll opportunities).
  async function frame(ms){h.clock.now+=ms;h.clock.wall+=ms;const cb=h.rafs.shift();if(cb)cb();await flush();}
  return {...h,log,reads,removes,enumerations,imageSrcs,radarRequests,boot,frame,flush};
}
module.exports={runtime,weatherBody,manifest,prayerForDate,LIVE,sourcePath,flush};
