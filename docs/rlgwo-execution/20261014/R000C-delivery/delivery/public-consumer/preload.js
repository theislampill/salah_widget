(function(){
"use strict";
  const nativeFetch=window.fetch.bind(window),NativeDate=window.Date;
  const query=new URLSearchParams(location.search),mode=query.get("mode")||"healthy";
  const attempt=Number(query.get("attempt")),hash=location.hash.slice(1),run=query.get("run")||"direct-fixture";
  const fixed=NativeDate.parse(query.get("night")==="1"?"2026-09-07T18:30:00.000Z":"2026-09-07T09:30:00.000Z"),rootURL=new URL("/product/",location.href);
  let clockNow=fixed; const started=performance.now(),moving=query.get("night")==="1";
  const wall=()=>moving?fixed+performance.now()-started:clockNow;
  const recovery=()=>moving&&performance.now()-started>=35000;
  const caseId=query.get("case"),caseSet=new Set(["12-null-temp","12-absent-temp","12-zero-temp","12-invalid-precip","12-zero-precip","12-wet","12-night-recovery"]);
  if(!caseSet.has(caseId))throw Error("Unknown bounded weather case");
  const cfg=new URLSearchParams(hash),wantLat=String(Number(cfg.get("lat"))),wantLon=String(Number(cfg.get("lon")));
  const documentId=crypto.randomUUID(),ownedDocument=document;
  const policy="default-src 'none'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob:; worker-src 'self' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'none'; base-uri 'self'; form-action 'none'";
  const report=window.__widgetFixture={mode,run,attempt,documentId,hash,state:"setup",error:null,sourceSha256:null,
    weatherOracle:"H5/H8 current model may support quantity-gated model particles; no direct observation or lightning inferred",bridgeSha256:null,
    clockPolicy:moving?"advancing-1x":"fixed",started,storageIsolated:false,clockFixed:false,clockNow:fixed,fetchIntercepted:false,initialStorageEntries:0,ledger:[],storageEvents:[],consoleErrors:[],weatherEvents:[]};
  const identity=()=>({run,attempt,documentId,hash,sourceSha256:report.sourceSha256});
  function assertOwned(owner){
    if(!owner||owner.run!==run||owner.attempt!==attempt||owner.documentId!==documentId||owner.hash!==hash||owner.sourceSha256!==report.sourceSha256||
      document!==ownedDocument||window.__widgetFixture!==report||location.hash.slice(1)!==hash||report.state!=="ready")
      throw Error("Fixture requires the exact ready attempt/document/source identity");
  }
  function failure(error){report.error=String(error&&error.message||error);report.state="error";
    const el=document.getElementById("fixture-error");if(el)el.textContent="Fixture bootstrap error: "+report.error;}
  // Synthetic data only: Hijri fields are invented test inputs, not date conversions.
  function prayerFixture(day){
    if(day!=="07-09-2026"&&day!=="08-09-2026")throw Error("Unexpected fixture date: "+day);
    const tomorrow=day==="08-09-2026";
    return {data:{timings:{Fajr:"05:00",Sunrise:"06:00",Dhuhr:"12:00",Asr:"15:30",Sunset:"18:00",Maghrib:"18:00",Isha:"19:30"},
      meta:{timezone:"Asia/Riyadh"},date:{
        gregorian:{date:day,day:tomorrow?"08":"07",month:{number:9,en:"September"},year:"2026"},
        hijri:{day:tomorrow?"02":"01",month:{number:1,en:"Synthetic month"},year:"1500"}
      }}};
  }
  // A complete model INPUT, not a local precipitation observation or trusted permission.
  function modelInput(){
    const date=new NativeDate(wall()+3*3600000),time=date.toISOString().slice(0,16);
    const celsius=new URLSearchParams(hash).get("units")==="c";
    const invalid=caseId==="12-invalid-precip"||(caseId==="12-night-recovery"&&!recovery()),dry=caseId==="12-zero-precip";
    const value={time,interval:900,weather_code:95,temperature_2m:celsius?20:68,apparent_temperature:celsius?19:66.2,
      relative_humidity_2m:90,dew_point_2m:celsius?18:64.4,wind_speed_10m:2,wind_direction_10m:180,wind_gusts_10m:4,
      cloud_cover:95,cloud_cover_low:60,cloud_cover_mid:60,cloud_cover_high:30,visibility:20000,is_day:moving?0:1,
      precipitation:invalid?"Infinity":dry?0:2,
      rain:invalid?null:dry?0:2,showers:0,snowfall:0,
      ...(caseId==="12-null-temp"?{temperature_2m:null}:caseId==="12-zero-temp"?{temperature_2m:0}:{})};
    if(caseId==="12-absent-temp")delete value.temperature_2m;
    return value;
  }
  function jsonResponse(value,row){
    const response=new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}),nativeJson=response.json.bind(response);
    response.json=()=>{row.jsonReads++;row.result="json-consumed";return nativeJson().then(value=>{row.parsedBody=value;row.jsonSettled=true;row.elapsedMs=performance.now()-started;return value;});};return Promise.resolve(response);
  }
  function fixtureFetch(input,init){
    const u=new URL(typeof input==="string"||input instanceof URL?String(input):input.url,location.href);
    const row={attempt,url:u.href,jsonReads:0,elapsedMs:performance.now()-started,result:"requested",cache:init&&init.cache||null};report.ledger.push(row);
    const weatherKeys=["latitude","longitude","current","hourly","forecast_days","temperature_unit","wind_speed_unit","timezone"];
    const currentFields="temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility,is_day,weather_code,precipitation,rain,showers,snowfall";
    const hourlyFields="temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,weather_code,visibility,is_day";
    if(u.origin==="https://api.open-meteo.com"&&u.pathname==="/v1/forecast"&&
      u.searchParams.get("latitude")===wantLat&&u.searchParams.get("longitude")===wantLon&&u.searchParams.get("timezone")==="Asia/Riyadh"&&
      u.searchParams.get("temperature_unit")===(new URLSearchParams(hash).get("units")==="c"?"celsius":"fahrenheit")&&
      u.searchParams.get("wind_speed_unit")==="ms"&&u.searchParams.get("forecast_days")==="3"&&u.searchParams.get("current")===currentFields&&
      u.searchParams.get("hourly")===hourlyFields&&[...u.searchParams.keys()].length===weatherKeys.length&&[...u.searchParams.keys()].every(k=>weatherKeys.includes(k)))
      return jsonResponse({timezone:"Asia/Riyadh",elevation:100,current:modelInput()},row);
    // An admitted empty index is diagnostic unavailability, never confirmed dry.
    if(u.href==="https://api.rainviewer.com/public/weather-maps.json")
      return jsonResponse({generated:Math.floor(wall()/1000),host:location.origin+"/tile",radar:{past:[{time:Math.floor(wall()/1000),path:"/v2/radar/"+Math.floor(wall()/1000)}]}},row);
    const day=u.pathname.slice("/v1/timings/".length),expected={latitude:wantLat,longitude:wantLon,method:"4",school:"0"};
    const allowed=u.origin==="https://api.aladhan.com"&&u.pathname.startsWith("/v1/timings/")&&
      Object.entries(expected).every(([k,v])=>u.searchParams.get(k)===v)&&[...u.searchParams.keys()].length===4&&
      (day==="07-09-2026"||day==="08-09-2026");
    if(!allowed){row.result="unexpected-request";failure("Unexpected fixture request: "+u.href);return Promise.reject(Error(report.error));}
    if(mode==="reject"){row.result="rejected";return Promise.reject(Error("Controlled prayer rejection"));}
    if(mode==="hang"){row.result="pending";return new Promise(()=>{});}
    return jsonResponse(prayerFixture(day),row);
  }

report.sourceSha256="7dd8067334c842025ea209d8cbdc20ce1ee31cd783a1f4da279072b1b310f0de";
    // These hooks must exist before DOM parsing and before either widget script.
    const data=new Map(),privateStore={
      get length(){return data.size;},key(n){return [...data.keys()][n]??null;},
      getItem(k){k=String(k);report.storageEvents.push(["get",k]);return data.has(k)?data.get(k):null;},
      setItem(k,v){k=String(k);report.storageEvents.push(["set",k]);data.set(k,String(v));},
      removeItem(k){k=String(k);report.storageEvents.push(["remove",k]);data.delete(k);},
      clear(){report.storageEvents.push(["clear"]);data.clear();}
    };
    Object.defineProperty(window,"localStorage",{configurable:true,enumerable:true,get:()=>privateStore});
    if(window.localStorage!==privateStore)throw Error("Cannot isolate localStorage before widget parsing");
    class FixtureDate extends NativeDate{constructor(...args){super(...(args.length?args:[wall()]));}static now(){return wall();}}
    window.Date=FixtureDate;window.fetch=fixtureFetch;
    window.__fixtureClock=Object.freeze({identity,assertOwned});
    report.initialStorageEntries=data.size;
    function verifyHooks(){
      report.storageIsolated=window.localStorage===privateStore;
      report.clockIsolated=window.Date===FixtureDate&&Math.abs(Date.now()-wall())<10;
      report.clockFixed=!moving&&report.clockIsolated&&Date.now()===clockNow;
      report.fetchIntercepted=window.fetch===fixtureFetch;
      if(!report.storageIsolated||!report.clockIsolated||!report.fetchIntercepted)throw Error("Fixture hooks were replaced");
    }
    verifyHooks();

report.documentMode="actual-pages-ingress-preload";report.state="loading";
document.addEventListener("DOMContentLoaded",()=>{try{verifyHooks();if(!window.SalahConfig||typeof window.qaState!=="function")throw Error("Actual widget/config missing");if(!report.error)report.state="ready";}catch(e){failure(e);}},{once:true});
})();