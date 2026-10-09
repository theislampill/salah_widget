'use strict';
// PREPARATION ONLY. Extends the existing browser wrapper; product scripts stay exact.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const original=path.join(root,'tests/widget-fixture.html'),out=path.join(__dirname,'browser-fixtures');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
let text=fs.readFileSync(original,'utf8');const before=hash(text),changes=[];
function replace(from,to,purpose){const count=text.split(from).length-1;if(count!==1)throw Error('Fixture anchor count '+count+': '+purpose);text=text.replace(from,to);changes.push({from,to,purpose,anchorCount:count});}
replace('rootURL=new URL("../",location.href);','rootURL=new URL("/product/",location.href);','Serve untouched target under a separate HTTP alias; audit wrapper is outside repository');
replace('let clockNow=fixed;',`let clockNow=fixed;
  const caseId=query.get("case"),caseSet=new Set(["12-null-temp","12-zero-temp","12-invalid-precip","12-wet","14-dry","14-wet","30-equator","30-meridian","30-origin"]);
  if(!caseSet.has(caseId))throw Error("Unknown bounded weather case");
  const cfg=new URLSearchParams(hash),wantLat=String(Number(cfg.get("lat"))),wantLon=String(Number(cfg.get("lon")));`, 'Known closed case list and captured expected numeric coordinate identity');
replace('weatherOracle:"joined R0024: useful model; local permission requires admitted synthetic fixture"','weatherOracle:"H5/H8 current model may support quantity-gated model particles; no direct observation or lightning inferred"','Correct stale fixture description only; no existing assertion weakened');
replace('precipitation:5,rain:5,showers:0,snowfall:0};',`precipitation:caseId==="12-invalid-precip"?"Infinity":caseId==="14-dry"?0:2,
      rain:caseId==="12-invalid-precip"?null:caseId==="14-dry"?0:2,showers:0,snowfall:0,
      ...(caseId==="12-null-temp"?{temperature_2m:null}:caseId==="12-zero-temp"?{temperature_2m:0}:{})};`, 'Actual fetchWeather receives null/zero/malformed/healthy amounts before startup, not helper installation');
replace('u.searchParams.get("latitude")==="24.47"&&u.searchParams.get("longitude")==="39.61"','u.searchParams.get("latitude")===wantLat&&u.searchParams.get("longitude")===wantLon','Weather request must consume exact requested zero-axis pair; retains complete fields, units, zone and parameter count');
replace('return jsonResponse({generated:Math.floor(clockNow/1000),host:"https://tilecache.rainviewer.com",radar:{past:[]}},row);',`return jsonResponse({generated:Math.floor(clockNow/1000),host:location.origin+"/tile",radar:{past:[{time:Math.floor(clockNow/1000),path:"/v2/radar/"+Math.floor(clockNow/1000)}]}},row);`, 'Actual browser Image/canvas loads an HTTP uniform 0dBZ palette tile; no fake accessor/Image/canvas');
replace('expected={latitude:"24.47",longitude:"39.61",method:"4",school:"0"}','expected={latitude:wantLat,longitude:wantLon,method:"4",school:"0"}','Target-bound synthetic prayer fixture changes only coordinates; no real prayer-provider availability claim');
replace('icon:document.querySelector("#wi").textContent,temperature:document.querySelector("#wt").textContent});',`icon:document.querySelector("#wi").textContent,temperature:document.querySelector("#wt").textContent,
      raw:copy(weather),radar:copy(weatherRadar),wxBusy,radarBusy,
      cached:copy((()=>{try{const raw=localStorage.getItem(wxKey());return raw==null?null:JSON.parse(raw);}catch{return null;}})()),
      visibleParticles:[...document.querySelectorAll(".drop,.flake")].filter(e=>{const s=getComputedStyle(e);return s.display!=="none"&&s.visibility==="visible"&&+s.opacity>.03;}).length,
      fx:document.querySelector(".c").dataset.fx,precip:document.querySelector(".c").dataset.precip,lightning:document.querySelector(".c").dataset.lightning,
      headerLabel:document.querySelector("#wi").title,
      card:(()=>{const r=document.querySelector(".c").getBoundingClientRect();return {width:r.width,height:r.height};})(),
      footer:(()=>{const r=document.querySelector(".d").getBoundingClientRect(),c=document.querySelector(".c").getBoundingClientRect();return {top:r.top-c.top,bottom:r.bottom-c.top};})()});`, 'Read-only consumer snapshots after actual acquisitions; gate invocation is diagnostic only');
// The current HTTP app uses an owned wasm module. Allow only native wasm compilation,
// not generic eval. Product bytes/anchors and unexpected-resource failures remain exact.
const cspCount=text.split("script-src 'self' 'unsafe-inline' blob:").length-1;
if(cspCount!==2)throw Error('Expected exactly two original wrapper CSP copies');
text=text.replaceAll("script-src 'self' 'unsafe-inline' blob:","script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob:");
changes.push({purpose:'Permit owned current HTTP app wasm compilation in the isolated wrapper only; no generic eval',anchorCount:cspCount});
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'widget-fixture.html'),text);
fs.writeFileSync(path.join(__dirname,'browser-fixture-preparation.json'),JSON.stringify({status:'PREPARED NOT EXECUTED',
 target:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',sourceFixture:original,sourceFixtureSha256:before,
 preparedFixtureSha256:hash(text),changes,expectations:'Original script count, config/native-first-paint/native-sky/Moon anchors, script-body equality, hook/storage/clock/source-owner identity and unexpected-request/resource failures retained. Product function bodies never patched.',
 limitations:'No browser execution by C. Fixed clock and blocked external fonts do not qualify ordinary live M0 or original typography; primary rollout/retained motion evidence must satisfy those independently.'},null,2)+'\n');
console.log(JSON.stringify({status:'PREPARED NOT EXECUTED',fixtureSha256:hash(text),disclosedChanges:changes.length}));
