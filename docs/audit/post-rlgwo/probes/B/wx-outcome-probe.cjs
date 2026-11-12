'use strict';
// Effect-free probe (lane B). Reads authored src/native/index.html, evaluates the exact request-owner and
// weather regions in a VM with stubbed fetch/Image/localStorage/clock. No network, no browser, no writes.
const fs=require('fs'),vm=require('vm'),path=require('path');
const repo=process.argv[2]; const src=fs.readFileSync(path.join(repo,'src/native/index.html'),'utf8');
function region(a,b){const i=src.indexOf(a),j=src.indexOf(b,i+a.length); if(i<0||j<0) throw new Error('region '+a); return src.slice(i,j);}
const code=[region('function cacheKey(){','// Read only the selected legacy main-format envelope.'),
  region('// ---- weather (Open-Meteo:','// ---- accurate Moon position')].join('\n');
const out={};
async function run(label,responder,opts={}){
  let elapsed=1000; const store=new Map();
  const ctx={console,Math,JSON,Date,Promise,Number,Object,Array,Set,Map,String,Error,Intl,isFinite,setTimeout,clearTimeout,
    AbortController,performance:{now:()=>elapsed},
    localStorage:{getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k)},
    fetch:async(url)=>responder(url), Image:class{set src(u){this._u=u; setTimeout(()=>opts.image?opts.image(this):this.onerror&&this.onerror(),0);}},
    document:{createElement:()=>({getContext:()=>({drawImage(){},getImageData:()=>({data:new Uint8ClampedArray(256*256*4)})})})},
  };
  vm.createContext(ctx);
  vm.runInContext(`var lat=24.47,lon=39.61,units="c",tz="Asia/Riyadh",_cacheTz=tz,method="4",school="0",SIM={wx:null},ADVANCING=false,_clockPreview=false,
    CONFIG={source:"hash",locationEvidence:{intent:"fixed-site",source:"hash"}},_renderDirty=false,_prayerCooldown={current:null,prefetch:null};
    const _RAFNOW=()=>performance.now(); const enc=encodeURIComponent; const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
    function zoneFormatter(z){return new Intl.DateTimeFormat("en-US",{timeZone:z});}
    function epochForTzTime(y,mo,d,h,mi,zone){return Date.UTC(y,mo-1,d,h,mi)-3*3600e3;}
    function simNow(){return Date.now();}
    ${code}
    globalThis.__p={fetchWeather,fetchRadar,get req(){return _wxRequests},get weather(){return weather},get radar(){return weatherRadar},get wxBusy(){return wxBusy},get radarBusy(){return radarBusy},retryDiagnostics,
      setLoc(a,b){lat=a;lon=b;}, get siteElev(){return siteElev}};`,ctx);
  const p=ctx.__p;
  await (opts.kind==='radar'?p.fetchRadar():p.fetchWeather());
  out[label]={request:JSON.parse(JSON.stringify(p.req[opts.kind||'weather'])),weatherAdmitted:!!p.weather,radarAdmitted:!!p.radar,busy:opts.kind==='radar'?p.radarBusy:p.wxBusy,
    retry:p.retryDiagnostics()[opts.kind||'weather'].state,siteElev:p.siteElev};
}
const okJson=body=>({ok:true,status:200,json:async()=>body});
(async()=>{
  await run('weather provider error body {error:true}',()=>okJson({error:true,reason:"x"}));
  await run('weather body with no current/hourly',()=>okJson({latitude:24.47}));
  await run('weather body: only elevation, invalid current',()=>okJson({elevation:2400,current:{weather_code:999},hourly:{time:["bad"]}}));
  await run('weather HTTP 503',()=>({ok:false,status:503,json:async()=>({})}));
  await run('radar manifest without host',()=>okJson({radar:{past:[{time:1,path:"/x"}]}}),{kind:'radar'});
  await run('radar manifest host not https (no allowlist)',()=>okJson({host:"http://example.invalid",generated:Math.floor(Date.now()/1000),radar:{past:[{time:Math.floor(Date.now()/1000),path:"/p"}]}}),
    {kind:'radar',image:im=>im.onerror&&im.onerror()});
  console.log(JSON.stringify(out,null,1));
})().catch(e=>{console.error(e);process.exit(1);});
