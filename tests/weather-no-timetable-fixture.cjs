'use strict';
// Actual complete authored runtime; only browser/transport/time boundaries are
// contained. Painter commands and a retained-raster sentinel are not pixels.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const root=path.resolve(__dirname,'..'),harnessPath=path.join(__dirname,'r001d-harness.cjs');
const harness=fs.readFileSync(harnessPath,'utf8'),configRead="fs.readFileSync(path.join(root,'config.js'),'utf8')";
assert.equal(harness.split(configRead).length,2,'one contained config boundary');
const {parseScripts,SetupError,requireSetup}=require('./native-script-contract.js');
// R000B source-state ingress only. This does not admit generated/browser delivery.
function extractAuthored(source){
 const scripts=parseScripts(source);
 requireSetup(scripts.length===2&&scripts[0].attributes.trim()==='src="config.js"'&&!scripts[0].body.trim()&&scripts[1].attributes.trim()==='','R000B expects exact authored config/native layout');
 const runtime=scripts[1].body;
 for(const owner of ['async function fetchTimings(','async function loadPrayerData(','function model(','function render(','window.qaState=function()','async function boot(){'])
  requireSetup(runtime.split(owner).length===2,'R000B missing or duplicate owner: '+owner);
 requireSetup(runtime.split('\nboot();').length===2&&/\nboot\(\);\s*$/.test(runtime),'R000B requires the real terminal boot caller');
 return runtime;
}
const harnessModule=new Module(harnessPath,module);harnessModule.filename=harnessPath;harnessModule.paths=Module._nodeModulePaths(__dirname);
harnessModule.r000bExtractor={nativeInlineRuntime:extractAuthored,SetupError};
const runtimeImport="const {nativeInlineRuntime,SetupError}=require('./native-inline-runtime.cjs');";
assert.equal(harness.split(runtimeImport).length,2,'one explicit runtime extraction boundary');
harnessModule._compile(harness.replace(configRead,"fs.readFileSync(path.join(root,'src/native/config.js'),'utf8')").replace(runtimeImport,'const {nativeInlineRuntime,SetupError}=module.r000bExtractor;'),harnessPath);
const {load,sha}=harnessModule.exports;
const sourcePath=process.env.SALAH_WITHDRAWAL_SOURCE||path.join(root,'src/native/index.html');
const sourceValid=Date.parse('2026-09-08T20:45:00Z'),initialWall=sourceValid+890000;
const copy=value=>JSON.parse(JSON.stringify(value));
async function fixture({source,hash='',reduced=false,cold=false,fetch:transport}={}){
 const h=load({sourcePath,source,hash:'#lat=24.47&lon=39.61&label=Madinah&tz=Asia%2FRiyadh&units=c&method=4&seed=1'+hash});
 h.clock.wall=initialWall;h.clock.now=0;h.ctx.matchMedia=()=>({matches:reduced});
 const cv=h.select('.cloudcanvas');cv.width=144;cv.height=232;
 const raster={clears:0,fills:0,currentFills:0};
 Object.assign(cv.ctx,{clearRect(){raster.clears++;raster.currentFills=0;},beginPath(){},arc(){},fill(){raster.fills++;raster.currentFills++;},
  createRadialGradient(){return {addColorStop(){}};},getImageData(x,y,w,height){const data=new Uint8ClampedArray(w*height*4);if(raster.currentFills)data[3]=255;return {data};}});
 const calls=[];let currentTime='2026-09-08T23:45';
 function payload(overrides={}){return {timezone:'Asia/Riyadh',elevation:100,current:{time:currentTime,interval:900,weather_code:95,
  temperature_2m:24,apparent_temperature:35,relative_humidity_2m:90,dew_point_2m:18,wind_speed_10m:7,wind_direction_10m:225,
  wind_gusts_10m:9,precipitation:2,rain:2,showers:0,snowfall:0,is_day:0,cloud_cover:95,cloud_cover_low:92,cloud_cover_mid:90,cloud_cover_high:60,visibility:10000,...overrides}};}
 h.ctx.fetch=async (url,init)=>{
  const u=new URL(String(url));calls.push({host:u.hostname,path:u.pathname,at:h.clock.wall});
  if(transport)return transport(u,init,h,payload);
  if(u.hostname==='api.open-meteo.com'){assert.equal(u.searchParams.get('timezone'),'Asia/Riyadh');return {ok:true,status:200,json:async()=>payload()};}
  if(u.hostname==='api.aladhan.com')return new Promise(()=>{}); // contained pending next-day provider; native deadlines remain owned
  if(u.hostname==='api.rainviewer.com')return {ok:true,status:200,json:async()=>({radar:{past:[]}})};
  throw Error('Unexpected fixture transport '+u.hostname);
 };
 h.run('tomorrow=null;weather=null;weatherTrack=null;lastWxAt=lastWxTry=0;window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:-20,azDeg:90},utcMs:simNow(),sample:()=>null})};');
 h.run('if(SIM.wx!=null)startWeather(true);');
 await h.run('fetchWeather()');
 if(cold)h.run('today=null;');
 h.run('render();paintClouds(simNow()/1000);tieRainToClouds()');
 function read(){return {...copy(h.run(`({model:!!model(),selected:!!selectedWeather(),eligibility:weatherEligibility(weather),
  scene:skySceneIdentity(),cov:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],targets:[cloudState.tgtLow,cloudState.tgtMid,cloudState.tgtHigh],ready:_cloudReady,
  density:_colDens?Math.max(..._colDens):0,population:_cloudMotion.population,phase:_cloudMotion.phase,life:_cloudMotion.life,wander:_cloudMotion.wander,
  raw:weather,lastWxAt,publication:typeof cloudPublicationReceipt==='function'?cloudPublicationReceipt():null,
  header:_lastWeatherHeader,qa:qaState(),fx:document.querySelector('.c').dataset.fx,precip:document.querySelector('.c').dataset.precip,
  lightning:document.querySelector('.c').dataset.lightning,rain:document.querySelector('.c').style.getPropertyValue('--rain-op'),
  independent:{pending:document.querySelector('.c').classList.contains('sky-pending'),stars:_starProjectionKey,
   geometry:moonGeometryObservation({nowMin:nowParts().h*60+nowParts().mi+nowParts().s/60}).fresh}})`)),raster:{...raster},requests:calls.length};}
 return {...h,read,raster,calls,payload,sourcePath,runtimeQualified:false,sourceSha256:sha(Buffer.from(source||fs.readFileSync(sourcePath,'utf8'))),
  at(age){h.clock.wall=sourceValid+age;h.clock.now=h.clock.wall-initialWall;},
  freshAtNow(){currentTime=new Date(h.clock.wall+3*3600000).toISOString().slice(0,16);},
  paint(){h.run('paintClouds(simNow()/1000);tieRainToClouds()');return read();},
  async refresh(overrides={}){h.ctx.__replacement=payload(overrides);h.ctx.fetch=async url=>{calls.push({host:new URL(String(url)).hostname,at:h.clock.wall});return {ok:true,status:200,json:async()=>h.ctx.__replacement};};await h.run('fetchWeather()');},
 };
}
function loopDriver(h){
 const frames=new Map(),listeners=new Map();let id=0;
 h.ctx.requestAnimationFrame=fn=>{frames.set(++id,fn);return id;};h.ctx.cancelAnimationFrame=i=>frames.delete(i);
 h.ctx.document.addEventListener=(name,fn)=>listeners.set(name,fn);h.run('startRenderLoop()');
 return {frames,frame(){assert.equal(frames.size,1);const [id,fn]=frames.entries().next().value;frames.delete(id);fn();assert.equal(frames.size,1);},
  visibility(state){h.ctx.document.visibilityState=state;listeners.get('visibilitychange')();}};
}
function withdrawn(state){assert.deepEqual(state.cov,[0,0,0]);assert.deepEqual(state.targets,[0,0,0]);assert.equal(state.ready,false);assert.equal(state.density,0);assert.equal(state.raster.currentFills,0);}
module.exports={fixture,loopDriver,withdrawn,copy,sourcePath,sourceValid,initialWall,sha,extractAuthored};
