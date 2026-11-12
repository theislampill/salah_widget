// Effect-free probe (no network/DOM/writes): does a continuously interpolated forecast weather
// record in the native snapshot keep the refined lifecycle from ever accepting a result?
import {pathToFileURL} from 'node:url';
// Usage: node forecast-identity-probe.mjs <repo-root>
const root=new URL('real-sky/',pathToFileURL((process.argv[2]||'.').replace(/[\/]?$/,'/')));
const {NativeSkyLifecycle}=await import(new URL('native-lifecycle.mjs',root));
const {nativeIdentity}=await import(new URL('native-contract.mjs',root));
function run({rate,lerpWeather,workerMs,wallMs}){
  let t0=0,clock=0; // fake monotonic clock (ms)
  const base=Date.UTC(2026,10,12,12,0,0);
  const snap=()=>{const sim=base+clock*rate;const f=((Math.floor(sim/1000)*1000)/3600000)%1; // hourly lerp fraction like wxAt(), refreshed once per simulated second as render()/syncWeather()
    const w=lerpWeather?{src:'forecast',temp:20,rh:40+10*f,vis:20000,cloud:30+20*f,code:2,wind:3+f}:{src:'forecast',temp:20,rh:40,vis:20000,cloud:30,code:2,wind:3};
    return {utcMs:sim,lat:24.47,lon:39.61,heightM:0,generation:1,sceneIdentity:'24.47|39.61|Asia/Riyadh|x:'+rate,tz:'Asia/Riyadh',timeScale:rate,units:'c',lp:0,reducedMotion:false,paused:false,camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},allowEstimates:true,weather:w};};
  const events={accepted:0,invalidations:{},avail:[]};
  const pending=[];
  const lc=new NativeSkyLifecycle({capture:snap,now:()=>clock,physical:true,
    execute:job=>new Promise(res=>pending.push({at:clock+workerMs,res:()=>res({status:'ready',raster:{},utcMs:job.observer.utcMs})})),
    onResult:()=>{events.accepted++;},onInvalidate:r=>{events.invalidations[r]=(events.invalidations[r]||0)+1;},onError:()=>{},onAvailability:v=>events.avail.push(v.reason)});
  return (async()=>{
    for(clock=0;clock<=wallMs;clock+=50){ // 20 Hz like native-host animate/compose fences
      lc.current(lc.latest,snap());
      if(clock%500===0)lc.request(); // native-host request interval 500 ms
      for(let i=pending.length-1;i>=0;i--)if(pending[i].at<=clock){pending.splice(i,1)[0].res();}
      await new Promise(r=>setImmediate(r));
    }
    lc.dispose();
    return {rate,lerpWeather,workerMs,accepted:events.accepted,counts:lc.state,invalidations:events.invalidations,lastAvailability:events.avail.at(-1),rateThroughputReported:events.avail.includes('rate-throughput')};
  })();
}
const out=[];
for(const workerMs of [300,800,1200])for(const rate of [1,2,10])for(const lerp of [false,true])out.push(await run({rate,lerpWeather:lerp,workerMs,wallMs:20000}));
console.log(JSON.stringify(out,null,1));
// identity sensitivity: two snapshots 1 simulated second apart under lerp
const a={utcMs:0,lat:1,lon:1,heightM:0,generation:1,sceneIdentity:'s',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{rh:40.0001}},b={...a,weather:{rh:40.0002}};
console.log('identity differs on rh 40.0001 vs 40.0002:',nativeIdentity(a)!==nativeIdentity(b));
