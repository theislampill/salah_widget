"use strict";
const assert=require("node:assert/strict"),{widget,drain}=require("./r0011-fixture.cjs"),{fixture,readSource}=require("./r000f-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
const T=Date.parse("2026-10-02T12:00:00Z"),day=86400000;
const seed={lat:51.5,lon:-.12,label:"London",method:"3",units:"f",source:"manual"};
const position=(accuracy=25,timestamp=T)=>({coords:{latitude:52.52,longitude:13.41,accuracy},timestamp});
function configMutate(source){return mutant==="capture-time"?source.replace('acquiredAt: pos && pos.timestamp','acquiredAt: null')
  :mutant==="fix-age"?source.replace('c.v = 1; c.savedAt = Date.now();','c.v = 1; c.savedAt = Date.now(); if(c.locationEvidence) c.locationEvidence.acquiredAt=c.savedAt;'):source;}
function mutate(source){return mutant==="form-drop"?source.replace('locationEvidence:_setLocationEvidence,','locationEvidence:null,')
  :mutant==="label-clears"?source.replace('if(id!=="set-label"){','if(true){'):source;}
function make(extra={}){return widget({ref,seed,now:T,...extra,configMutate:mutant?configMutate:undefined,mutate:mutant?mutate:undefined});}
async function acquire(f,pos=position()){f.click("set-pin");await f.resolveCall("gps",f.calls.gps.length-1,pos);}
function evidence(f){return f.config()?.locationEvidence;}
function record(source,intent,accuracyM=null,acquiredAt=null,extra={}){return {intent,source,accuracyM,acquiredAt,provider:null,area:null,bounds:null,...extra};}
function builder(){const f=fixture("builder",{ref});f.sandbox.Date=class extends Date{static now(){return T;}};return f;}
const cases=[],test=(name,body)=>cases.push({name,body});
test("shared geolocation captures original measured accuracy and fix timestamp",async()=>{
  const f=make(),p=f.sandbox.SalahConfig.geolocate({});await f.resolveCall("gps",0,position());const r=await p;
  assert.equal(r.accuracy,25);assert.equal(r.acquiredAt,T);assert.deepEqual(JSON.parse(JSON.stringify(r.locationEvidence)),record("browser-geolocation","device-position",25,T));assert.deepEqual(JSON.parse(JSON.stringify(f.calls.gps[0].args)),{enableHighAccuracy:false,timeout:10000,maximumAge:600000});
});
test("actual GPS form apply save load retains exactly 25 metres and original epoch",async()=>{
  const f=make();await acquire(f);f.click("setClose");assert.deepEqual(evidence(f),record("browser-geolocation","device-position",25,T));
  const saved=f.sandbox.SalahConfig.loadLocal();assert.deepEqual(JSON.parse(JSON.stringify(saved.locationEvidence)),evidence(f));assert.equal(saved.source,"localStorage");assert.equal(saved.origin,"browser-geolocation");assert.equal(saved.savedAt,T);assert.deepEqual([saved.lat,saved.lon],[52.52,13.41]);
});
test("label and units saves a day later preserve fix age while savedAt advances",async()=>{
  const f=make();await acquire(f);f.click("setClose");f.now(T+day);f.buckle.dispatch("click");f.input("set-label","Home");f.key("set-label","Enter",true);f.input("set-units","c","change");f.click("setClose");
  const saved=f.sandbox.SalahConfig.loadLocal();assert.equal(saved.locationEvidence?.acquiredAt,T);assert.equal(saved.locationEvidence?.accuracyM,25);assert.equal(saved.savedAt,T+day);assert.equal(saved.origin,"browser-geolocation");assert.equal(saved.label,"Home");assert.equal(f.calls.gps.length,1);
  f.buckle.dispatch("click");assert.match(f.elements.get("set-pin").title,/Saved browser position/);assert.doesNotMatch(f.elements.get("set-pin").title,/GPS|Using precise|current position/);
});
test("a cached five-minute fix retains its acquisition time",async()=>{
  const f=make();await acquire(f,position(25,T-300000));f.click("setClose");assert.equal(evidence(f)?.acquiredAt,T-300000);assert.equal(f.sandbox.SalahConfig.loadLocal().locationEvidence?.acquiredAt,T-300000);
});
test("saved old browser target remains usable without becoming a current device claim",()=>{
  const f=make({seed:{...seed,source:"browser-geolocation",locationEvidence:record("browser-geolocation","device-position",25,T-day)},now:T+day});
  assert.equal(f.config().lat,51.5);assert.equal(evidence(f)?.acquiredAt,T-day);assert.match(f.elements.get("set-pin").title,/Saved browser position/);assert.doesNotMatch(f.elements.get("set-pin").title,/GPS|current|precise/i);
});
test("coordinate edits deliberately replace acquisition with a manual fixed site",async()=>{
  const f=make();await acquire(f);f.input("set-lat","52.53000");f.click("setClose");assert.deepEqual(evidence(f),record("manual","fixed-site"));assert.equal(f.config().lat,52.53);assert.equal(f.sandbox.SalahConfig.loadLocal().origin,"manual");
});
test("display name edit alone preserves browser evidence and coordinates",async()=>{
  const f=make();await acquire(f);f.input("set-label","Chosen name");f.key("set-label","Enter",true);f.click("setClose");assert.deepEqual(evidence(f),record("browser-geolocation","device-position",25,T));assert.deepEqual([f.config().lat,f.config().lon],[52.52,13.41]);
});
test("malformed accuracies stay unknown and zero metres is a valid reported value",async()=>{
  for(const accuracy of [undefined,null,NaN,Infinity,-1,"25"]){const f=make();await acquire(f,{coords:{latitude:52.52,longitude:13.41,accuracy},timestamp:T});f.click("setClose");assert.equal(evidence(f)?.accuracyM,null);assert.equal(evidence(f)?.acquiredAt,T);}
  const f=make();await acquire(f,position(0));f.click("setClose");assert.equal(evidence(f)?.accuracyM,0);
});
test("missing malformed and future timestamps stay unknown with no age-zero substitution",async()=>{
  for(const timestamp of [undefined,null,NaN,Infinity,0,-1,T+1,String(T)]){const f=make();await acquire(f,{coords:{latitude:52.52,longitude:13.41,accuracy:25},timestamp});f.click("setClose");assert.equal(evidence(f)?.acquiredAt,null);assert.equal(evidence(f)?.accuracyM,25);f.now(T+day);f.buckle.dispatch("click");f.input("set-units","c","change");f.click("setClose");assert.equal(evidence(f)?.acquiredAt,null);}
});
test("denied and timed-out positions do not replace evidence or retry",async()=>{
  for(const code of [1,3]){const f=make(),before=f.config();f.click("set-pin");f.calls.gps[0].reject({code,message:code===1?"denied":"timeout"});await drain();assert.deepEqual(f.config(),before);assert.equal(f.calls.gps.length,1);assert.match(f.elements.get("set-status").textContent,/unavailable/);}
});
test("unsupported geolocation leaves manual target usable",async()=>{
  const f=make();delete f.sandbox.navigator.geolocation;f.click("set-pin");await drain();assert.equal(f.calls.gps.length,0);assert.match(f.elements.get("set-status").textContent,/isn't available/);assert.equal(f.config().label,"London");
});
test("legacy browser origin keeps target but no precision or savedAt-as-fix",()=>{
  const f=make({seed:{...seed,source:"browser-geolocation"}});assert.deepEqual(evidence(f),record("legacy","device-position"));assert.equal(f.config().savedAt,T);assert.equal(f.config().lat,51.5);assert.match(f.elements.get("set-pin").title,/Saved browser position/);
});
test("legacy unresolved origin stays unknown and saved bytes remain usable",()=>{
  const f=make({seed:{...seed,source:"localStorage"}});assert.deepEqual(evidence(f),record("legacy","unknown"));assert.equal(f.config().lat,51.5);assert.equal(f.sandbox.SalahConfig.loadLocal().method,"3");
});
test("normalization owns fresh metadata primitives and bounds instead of the input object",()=>{
  const f=make(),ev=record("place","fixed-site",null,null,{provider:"Nominatim",area:"Berlin",bounds:{south:52,north:53,west:13,east:14}}),c=f.sandbox.SalahConfig.normalize({...seed,source:"place",locationEvidence:ev});ev.bounds.south=0;ev.provider="changed";assert.equal(c.locationEvidence?.bounds?.south,52);assert.equal(c.locationEvidence?.provider,"Nominatim");
});
test("real coarse parser keeps area provider and explicitly unknown metric accuracy",async()=>{
  const f=make();f.sandbox.AbortController=AbortController;f.run(readSource("config.js",ref));f.sandbox.fetch=async()=>({ok:true,json:async()=>({latitude:"24.47",longitude:"39.61",city:"Madinah",country:"Saudi Arabia",country_code:"SA",accuracy:"5"})});const r=await f.sandbox.SalahConfig.coarseDetect();assert.deepEqual(JSON.parse(JSON.stringify(r.cfg.locationEvidence)),record("coarse-ip","coarse-area",null,null,{provider:"GeoJS",area:"Madinah, Saudi Arabia"}));assert.equal(r.cfg.accuracy,5);
});
test("actual geocoder selection carries real bounds without invented point precision",async()=>{
  const f=make();f.sandbox.AbortController=AbortController;f.run(readSource("config.js",ref));f.sandbox.fetch=async()=>({ok:true,json:async()=>[{class:"place",lat:"52.52",lon:"13.41",address:{city:"Berlin",country:"Germany",country_code:"de"},boundingbox:["52","53","13","14"]}]});f.input("set-label","Berlin");f.key("set-label","Enter");for(let i=0;i<3;i++)await drain();f.click("setClose");assert.deepEqual(evidence(f),record("place","fixed-site",null,null,{provider:"Nominatim",area:"Berlin, Germany",bounds:{south:52,north:53,west:13,east:14}}));
});
test("geocoder absent malformed bounds remain unknown",async()=>{
  const f=make();f.input("set-label","Place");f.key("set-label","Enter");await f.resolveCall("search",0,[{lat:52.52,lon:13.41,name:"Place",norm:"Place, Country",bounds:{south:NaN,north:53,west:13,east:14}}]);f.click("setClose");assert.deepEqual(evidence(f),record("place","fixed-site",null,null,{area:"Place, Country"}));
  f.sandbox.AbortController=AbortController;f.run(readSource("config.js",ref));f.sandbox.fetch=async()=>({ok:true,json:async()=>[{class:"place",lat:"52.52",lon:"13.41",name:"Place",boundingbox:["",null," ",false]}]});const cs=await f.sandbox.SalahConfig.geocodeSearch("Place");assert.equal(cs[0].bounds,null);
});
test("manual five-decimal coordinates do not become measured precision",()=>{
  const f=make();f.input("set-lat","52.52000");f.input("set-lon","13.41000");f.click("setClose");assert.deepEqual(evidence(f),record("manual","fixed-site"));
});
test("builder captures evidence while portable recipient receives only fixed target",async()=>{
  const f=builder();f.click("geo");await f.resolve("gps",0,position());const c=f.run("formConfig()");assert.deepEqual(JSON.parse(JSON.stringify(c.locationEvidence)),record("browser-geolocation","device-position",25,T));
  const h=f.run("hash()"),receiver=f.sandbox.SalahConfig.resolve("#"+h).cfg;assert.deepEqual(JSON.parse(JSON.stringify(receiver.locationEvidence)),record("hash","fixed-site"));assert.deepEqual([receiver.lat,receiver.lon],[52.52,13.41]);assert.doesNotMatch(h,/accuracy|acquiredAt|timestamp|locationEvidence|device-position|browser-geolocation/);
});
test("builder reverse naming and label preference edits cannot improve or refresh fix",async()=>{
  const f=builder();f.click("geo");await f.resolve("gps",0,position());await f.resolve("reverse",0,{city:"Berlin",countryCode:"DE",continentCode:"EU",accuracy:1,timestamp:T+day});f.input("label","Home");f.input("units","c","change");assert.deepEqual(JSON.parse(JSON.stringify(f.run("formConfig().locationEvidence"))),record("browser-geolocation","device-position",25,T));
});
test("builder coordinate edit clears browser metadata and late reverse cannot restore it",async()=>{
  const f=builder();f.click("geo");await f.resolve("gps",0,position());f.input("lat","30");f.input("lon","31");await f.resolve("reverse",0,{city:"Old Berlin",countryCode:"DE"});const c=f.sandbox.SalahConfig.normalize(f.run("formConfig()"));assert.deepEqual(JSON.parse(JSON.stringify(c.locationEvidence)),record("manual","fixed-site"));
});
test("abandoned GPS cannot overwrite newer manual metadata or saved outcome",async()=>{
  const f=make();f.click("set-pin");f.input("set-lat","30");f.input("set-lon","31");f.click("setClose");const before=f.config();await f.resolveCall("gps",0,position());assert.deepEqual(f.config(),before);assert.deepEqual(evidence(f),record("manual","fixed-site"));
});
test("denied persistence retains accurate in-memory evidence with session-only feedback",async()=>{
  const f=make();f.sandbox.localStorage.setItem=()=>{throw new DOMException("blocked","SecurityError");};await acquire(f);f.click("setClose");assert.deepEqual(evidence(f),record("browser-geolocation","device-position",25,T));assert.equal(f.config().source,"browser-geolocation");assert.match(f.elements.get("settings-persistence-status").textContent,/session only/);
});
test("hardcoded local and preferLocal keep target semantics and preference precedence",async()=>{
  const ev=record("browser-geolocation","device-position",25,T-day);
  const f=make({seed:{...seed,source:"browser-geolocation",locationEvidence:ev},hash:"#preferLocal=1&lat=24.47&lon=39.61&method=2&units=c"});assert.deepEqual(evidence(f),ev);assert.equal(f.config().method,"3");assert.equal(f.config().units,"f");assert.equal(f.calls.gps.length,0);
  const h=make({hash:"#lat=0&lon=0&method=2&units=c"});assert.deepEqual(evidence(h),record("hash","fixed-site"));assert.equal(h.config().lat,0);assert.equal(h.config().units,"c");assert.equal(h.calls.gps.length,0);
});
test("portable and local serialization never emits private acquisition history",()=>{
  const f=make(),c={...seed,source:"browser-geolocation",locationEvidence:record("browser-geolocation","device-position",25,T)};
  for(const opts of [{},{mode:"preferLocal"},{mode:"local",explicitPrefs:["method","units"]}]){const h=f.sandbox.SalahConfig.serialize(c,opts);assert.doesNotMatch(h,/accuracy|acquiredAt|timestamp|locationEvidence|device-position|browser-geolocation/);if(opts.mode==="local")assert.equal(new URLSearchParams(h).has("lat"),false);}
  assert.equal(f.sandbox.SalahConfig.parseHash("#lat=1&lon=2&acquiredAt="+T+"&accuracyM=25").cfg.acquiredAt,undefined);
});
(async()=>{let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0;})();
