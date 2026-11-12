'use strict';
// Effect-free probe (lane B): does the retry gate ever permit a replacement BEFORE the admitted current record's
// source age crosses 900 s? Exact authored regions, stubbed fetch/clock. No network, no browser, no writes.
const fs=require('fs'),vm=require('vm'),path=require('path');
const src=fs.readFileSync(path.join(process.argv[2],'src/native/index.html'),'utf8');
function region(a,b){const i=src.indexOf(a),j=src.indexOf(b,i+a.length); if(i<0||j<0) throw new Error(a); return src.slice(i,j);}
const code=[region('function cacheKey(){','// Read only the selected legacy main-format envelope.'),region('// ---- weather (Open-Meteo:','// ---- accurate Moon position')].join('\n');
const T0=Date.parse('2026-11-12T06:15:00Z'); let wall=T0+20e3, elapsed=20e3; const RealDate=Date;
class FakeDate extends RealDate{constructor(...a){super(...(a.length?a:[wall]));} static now(){return wall;}}
let fetches=0;
const iso=ms=>{const d=new RealDate(ms+3*3600e3);return d.toISOString().slice(0,16);};   // Asia/Riyadh wall (UTC+3)
const ctx={console,Math,JSON,Date:FakeDate,Promise,Number,Object,Array,Set,Map,String,Error,Intl,isFinite,setTimeout,clearTimeout,AbortController,
  performance:{now:()=>elapsed},localStorage:{getItem:()=>null,setItem(){},removeItem(){}},
  fetch:async()=>{fetches++; const q=Math.floor(wall/900e3)*900e3; return {ok:true,status:200,json:async()=>({timezone:"Asia/Riyadh",elevation:600,
    current:{time:iso(q),interval:900,weather_code:3,temperature_2m:20,cloud_cover:95,precipitation:0},current_units:{temperature_2m:"°C"},
    hourly:{time:[iso(q-q%3600e3),iso(q-q%3600e3+3600e3)],temperature_2m:[20,20],weather_code:[3,3]},hourly_units:{temperature_2m:"°C"}})};}};
vm.createContext(ctx);
vm.runInContext(`var lat=24.47,lon=39.61,units="c",tz="Asia/Riyadh",_cacheTz=tz,method="4",school="0",SIM={wx:null},ADVANCING=false,_clockPreview=false,
  CONFIG={source:"hash",locationEvidence:{intent:"fixed-site",source:"hash"}},_renderDirty=false,_prayerCooldown={current:null,prefetch:null};
  const _RAFNOW=()=>performance.now(); const enc=encodeURIComponent; const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
  function zoneFormatter(z){return new Intl.DateTimeFormat("en-US",{timeZone:z});}
  function epochForTzTime(y,mo,d,h,mi){return Date.UTC(y,mo-1,d,h,mi)-3*3600e3;}
  ${code}
  globalThis.__p={fetchWeather,retryGate,selectedWeather,get weather(){return weather}};`,ctx);
const p=ctx.__p, rows=[];
(async()=>{
  await p.fetchWeather();                                    // first accepted record (valid at 06:15)
  // Model the loop's ~30 s visible poll for 31 minutes; record gate state, selection and fetch count.
  for(let s=50;s<=31*60;s+=30){ wall=T0+s*1000; elapsed=s*1000;
    const selBefore=!!p.selectedWeather(wall), before=fetches, gate=p.retryGate('weather',wall,elapsed); await p.fetchWeather();
    const sel=!!p.selectedWeather(wall);
    rows.push({selectedBeforePoll:selBefore,utc:new RealDate(wall).toISOString().slice(11,19),gate,fetched:fetches>before,selectedAfterPoll:sel,sourceAgeS:p.weather?Math.round((wall-p.weather.currentValidAt)/1000):null});
  }
  const gaps=rows.filter(r=>!r.selectedAfterPoll);
  console.log(JSON.stringify({fetches,anyFetchWhileStillSelected:rows.some(r=>r.fetched&&r.selectedBeforePoll),pollsFindingNoEligibleCurrent:rows.filter(r=>!r.selectedBeforePoll).map(r=>r.utc),
    sample:rows.filter(r=>/^06:(29|30|44|45)/.test(r.utc)),boundaryCheck:[900,1800].map(b=>{wall=T0+b*1000+1;return {utc:new RealDate(wall).toISOString().slice(11,23),selected:!!p.selectedWeather(wall)};})},null,1));
})();
