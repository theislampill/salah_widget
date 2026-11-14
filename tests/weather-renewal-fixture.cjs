'use strict';
// R002F (issue 96): drives the ACTUAL authored runtime and its ACTUAL render loop (weather-no-timetable-fixture's
// loopDriver) across a provider-step boundary. The provider is a contained stub that follows the upstream
// Open-Meteo rule current.time = floor(server now, 15 min), interval 900 s, with a CHOSEN publication lag and
// device-clock offset. Request latency is zero (a resolved transport); add real latency to every gap below.
// Nothing here contacts a provider. This is source-consumer evidence, not a browser/pixel qualification.
const assert=require('node:assert/strict');
const {fixture,loopDriver,sourceValid}=require('./weather-no-timetable-fixture.cjs');
// B = the end of a provider step (the TTL boundary of the record for the step before it): 23:45 Asia/Riyadh, so a scene
// stays inside the fixture's civil day (its next-day prayer provider is pending; crossing midnight would withhold clouds).
const STEP=900000, B=sourceValid, FRAME=100;
const iso=(ms,zoneOffset=3*3600000)=>new Date(ms+zoneOffset).toISOString().slice(0,16);   // Asia/Riyadh wall text
const flush=async()=>{for(let i=0;i<6;i++)await new Promise(r=>setImmediate(r));};
// skewMs > 0: the device clock is AHEAD of the provider's clock by skewMs (server = device - skewMs).
// maxStep: the provider never serves a step after it (a provider that stops advancing). fail(h): true -> HTTP 503.
// mutate(h,body): may return a replacement body, or the string 'throw' (the JSON body read throws).
function provider({lagMs=0,skewMs=0,interval=900,offsetMs=0,code=95,precipitation=2,hold=null,maxStep=Infinity,fail=null,mutate=null}={}){
  code??=95; precipitation??=2;
  return async(u,init,h,payload)=>{
    if(u.hostname==='api.aladhan.com')return new Promise(()=>{});
    if(u.hostname==='api.rainviewer.com')return {ok:true,status:200,json:async()=>({radar:{past:[]}})};
    assert.equal(u.hostname,'api.open-meteo.com');
    if(fail&&fail(h)) return {ok:false,status:503,json:async()=>({error:true})};
    const q=Math.min(maxStep,Math.floor((h.clock.wall-skewMs-lagMs)/STEP)*STEP)+offsetMs,hr=q-q%3600000;
    const body=payload({time:iso(q),interval,weather_code:code,precipitation});
    body.hourly={time:[iso(hr-3600000),iso(hr),iso(hr+3600000),iso(hr+7200000)],temperature_2m:[24,23,22,21],weather_code:[code,code,code,code],
      cloud_cover:[95,90,85,80],precipitation:[precipitation,precipitation,precipitation,precipitation]};
    const m=mutate?mutate(h,body):undefined, final=m===undefined?body:m;
    const response={ok:true,status:200,json:async()=>{ if(final==='throw') throw Error('contained malformed JSON'); return final; }};
    return hold?hold(response):response;
  };
}
// One scene: a record fetched at B+fetchAt (by default the step ending at B), then the real loop started so that its
// 30 s poll falls `phaseMs` after B. Wall and elapsed clocks advance together by `frame` ms per frame.
async function scene({phaseMs=10000,lagMs=0,skewMs=0,interval=900,offsetMs=0,source,hash='',reduced=false,hold=null,code,precipitation,
  fetchAt=-120000,frame=FRAME,maxStep,fail,mutate}={}){
  const h=await fixture({source,hash,reduced,fetch:provider({lagMs,skewMs,interval,offsetMs,hold,code,precipitation,maxStep,fail,mutate})});
  const s={wall:B+fetchAt,perf:1e6}, skip=h.calls.length;   // the fixture's own setup fetch is not part of the scene
  const set=()=>{h.clock.wall=s.wall;h.clock.now=s.perf;};
  set();h.run('weather=null;weatherTrack=null;lastWxAt=0;lastWxTry=0;_wxRetry.weather=null;_wxDecisionCache=null;if(SIM.wx!=null)startWeather(true);');
  await h.run('fetchWeather()');await flush();
  const period=frame*(Math.floor(30000/frame)+1);              // the loop polls on the first frame more than 30 000 ms later
  let W0=B+phaseMs; while(W0-period>B+fetchAt) W0-=period;      // the loop's first frame polls; a whole number of periods later it polls at B+phase
  s.perf+=W0-s.wall;s.wall=W0;set();
  const L=loopDriver(h);
  const wx=()=>h.calls.slice(skip).filter(c=>c.host==='api.open-meteo.com');
  const look=()=>JSON.parse(JSON.stringify(h.run(`({sel:!!selectedWeather(),ready:_cloudReady,density:_colDens?Math.max(..._colDens):0,cov:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],
    precip:document.querySelector('.c').dataset.precip,lightning:document.querySelector('.c').dataset.lightning,fx:document.querySelector('.c').dataset.fx||null,
    header:_lastWeatherHeader?{icon:_lastWeatherHeader.icon,temperature:_lastWeatherHeader.temperature,state:_lastWeatherHeader.conditionState}:null,
    step:weather&&weather.currentValidAt,seed:_cloudFieldSeed,population:_cloudMotion.population,phase:_cloudMotion.phase,
    renewal:retryDiagnostics().renewal||null})`)));
  // Advance to `until` (absolute wall ms) frame by frame, recording what each frame presents.
  async function run(until,{hidden=false,onFrame}={}){
    const out=[];
    let first=!started; started=true;
    while(s.wall<until){ if(!first){ s.wall+=frame;s.perf+=frame;set(); } first=false; if(hidden) continue;
      L.frame();await flush(); const v={t:s.wall-B,requests:wx().length,...look()}; out.push(v); if(onFrame)onFrame(v); }
    return out;
  }
  let started=false;
  return {h,L,set,run,look,requests:()=>wx().length,requestTimes:()=>wx().map(c=>c.at-B),get t(){return s.wall-B;},
    step(ms){s.wall+=ms;set();}, elapse(ms){s.wall+=ms;s.perf+=ms;set();}};
}
// The withdrawal window around one boundary: first frame after B that is unselected, first that is selected again.
function gap(frames){
  const off=frames.find(f=>f.t>0&&!f.sel), on=off&&frames.find(f=>f.t>off.t&&f.sel);
  return {offAt:off?off.t:null,onAt:on?on.t:null};
}
module.exports={scene,provider,gap,flush,iso,B,STEP,FRAME,sourceValid};
