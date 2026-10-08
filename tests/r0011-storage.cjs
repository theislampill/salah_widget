"use strict";
const assert=require("node:assert/strict"),{widget,drain}=require("./r0011-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
const seed={lat:51.5,lon:-.12,label:"London",method:"3",units:"f",source:"manual"};
const detected={ok:true,cfg:{lat:24.47,lon:39.61,label:"Madinah",area:"Madinah, SA",method:"4",units:"c",source:"coarse-ip"}};
const security=()=>{throw new DOMException("blocked","SecurityError");};
function make(extra={}){
  const mutate=source=>mutant==="save-result"?source.replace('_publishPersistence("save",r);','_publishPersistence("save",{ok:true});')
    :mutant==="reset-result"?source.replace('if(!r.ok){','if(false){')
    :mutant==="cancel-hint"?source.replace('_setStatus("Enter to search a place · Shift+Enter to keep the typed name."); return;','return;')
    :mutant==="status-overwrite"?source.replace('s.textContent=[message,_setHint.msg].filter(Boolean).join("\\n");','s.textContent=_setHint.msg;')
    :mutant==="scene-reset"&&source.startsWith("function beginSkyScene(){")?'function beginSkyScene(){}'
    :mutant==="scene-surface"&&source.startsWith("function updateSkySurface(){")?'function updateSkySurface(){}'
    :mutant==="generation-reset"?source.replace('a.expired=true; if(a.cancel) a.cancel();','a.expired=true;')
      .replace('if(a.controller) a.controller.abort();',''):source;
  return widget({ref,seed,...extra,mutate:mutant?mutate:undefined});
}
const status=f=>f.elements.get("set-status").textContent;
function warning(f,phrase){assert.match(f.buckle.getAttribute("aria-label"),phrase);assert.equal(f.buckle.querySelector(".gear").textContent,"!");assert.equal(f.buckle.classList.contains("persist-warning"),true);assert.match(f.elements.get("settings-persistence-status").textContent,/SecurityError/);}
const cases=[],test=(name,body)=>cases.push({name,body});
test("denied save applies session choice and publishes closed feedback before prayer settles",async()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY,old=f.storage.get(key);f.sandbox.localStorage.setItem=security;
  f.input("set-units","c","change");f.key("set-units","Escape");
  assert.equal(f.config().units,"c");assert.equal(f.storage.get(key),old);assert.equal(f.run("_storageErr"),"SecurityError");assert.equal(f.calls.prayer.length,1);assert.equal(f.calls.loop,0);
  assert.equal(f.card.classList.contains("settings-open"),false);assert.equal(f.document.activeElement,f.buckle);warning(f,/changes not saved.*session only/);assert.match(status(f),/Changes apply for this session only.*Could not save settings \(SecurityError\)/s);
  f.buckle.dispatch("click");assert.match(status(f),/session only/);assert.match(status(f),/Enter to search/);assert.equal(f.elements.get("set-units").value,"c");
  f.calls.prayer[0].resolve();await drain();assert.match(status(f),/session only/);
});
test("denied reset preserves saved bytes and active config without detection",async()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY,old=f.storage.get(key),before=f.config();f.sandbox.localStorage.removeItem=security;f.click("set-reset");
  assert.equal(f.storage.get(key),old);assert.deepEqual(f.config(),before);assert.equal(f.calls.coarse.length,0);assert.equal(f.calls.prayer.length,0);assert.match(status(f),/Could not clear saved settings \(SecurityError\).*saved settings remain/s);assert.doesNotMatch(status(f),/cleared|estimated area/);warning(f,/could not be cleared/);
  f.click("setClose");f.buckle.dispatch("click");assert.match(status(f),/saved settings remain/);
});
test("subsequent successful save clears warning and retains normalized stored data",()=>{
  const f=make(),put=f.sandbox.localStorage.setItem;f.sandbox.localStorage.setItem=security;f.input("set-units","c","change");f.click("setClose");f.buckle.dispatch("click");
  f.sandbox.localStorage.setItem=put;f.input("set-time","12","change");f.click("setClose");const saved=f.sandbox.SalahConfig.loadLocal();assert.deepEqual([saved.units,saved.time,saved.origin],["c","12","manual"]);assert.equal(f.run("_storageErr"),null);assert.equal(f.buckle.getAttribute("aria-label"),"Widget settings");assert.equal(f.buckle.querySelector(".gear").textContent,"⚙");assert.equal(f.buckle.classList.contains("persist-warning"),false);assert.match(f.elements.get("settings-persistence-status").textContent,/Settings saved in this browser/);f.buckle.dispatch("click");assert.match(status(f),/Settings saved in this browser/);assert.doesNotMatch(status(f),/session only/);
});
test("successful removal publishes cleared and detecting while lookup is pending",()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY;f.click("set-reset");assert.equal(f.storage.has(key),false);assert.equal(f.calls.coarse.length,1);assert.match(status(f),/Saved settings cleared.*Detecting your area/s);assert.equal(f.buckle.classList.contains("persist-warning"),false);
});
test("successful removal plus detection failure leaves manual setup usable",async()=>{
  const f=make();f.click("set-reset");await f.resolveCall("coarse",0,{ok:false});assert.equal(f.sandbox.SalahConfig.loadLocal(),null);assert.match(status(f),/Saved settings cleared.*enter your location/is);assert.doesNotMatch(status(f),/using estimated area/i);assert.equal(f.card.classList.contains("settings-open"),true);
});
test("successful removal plus detection success applies without accidental resave",async()=>{
  const f=make();f.click("set-reset");await f.resolveCall("coarse",0,detected);assert.equal(f.config().label,"Madinah");assert.equal(f.storage.has(f.sandbox.SalahConfig.KEY),false);assert.equal(f.calls.prayer.length,1);f.calls.prayer[0].resolve();await drain();assert.match(status(f),/Saved settings cleared.*using estimated area: Madinah, SA/is);assert.equal(f.run("_setDirty"),false);f.click("setClose");assert.equal(f.sandbox.SalahConfig.loadLocal(),null);
});
test("search and reopen retain failure instead of replacing it with an ordinary hint",async()=>{
  const f=make();f.sandbox.localStorage.setItem=security;f.input("set-units","c","change");f.click("setClose");f.buckle.dispatch("click");f.input("set-label","Berlin");f.key("set-label","Enter");assert.match(status(f),/session only.*Searching/s);await f.resolveCall("search",0,[{lat:52.52,lon:13.41,name:"Berlin",norm:"Berlin, Germany",cc:"de"}]);assert.match(status(f),/session only.*Found: Berlin/s);
});
test("location edit abandons pending reset feedback and preserves newer form",async()=>{
  const f=make();f.click("set-reset");f.input("set-lat","30");f.input("set-lon","31");const before=status(f);await f.resolveCall("coarse",0,detected);assert.equal(status(f),before);assert.equal(f.elements.get("set-lat").value,"30");assert.equal(f.config().label,"London");assert.equal(f.calls.prayer.length,0);
});
test("close and new failed save supersede pending reset completion",async()=>{
  const f=make();f.click("set-reset");f.sandbox.localStorage.setItem=security;f.input("set-units","c","change");f.click("setClose");f.buckle.dispatch("click");const before=status(f);await f.resolveCall("coarse",0,detected);assert.equal(status(f),before);warning(f,/session only/);assert.equal(f.config().units,"c");
});
test("save and reset leave unrelated cache and test keys unchanged",async()=>{
  const f=make();for(const k of ["prayer:fixture","weather:fixture","test:sentinel"])f.storage.set(k,k+":original");f.input("set-units","c","change");f.click("setClose");f.buckle.dispatch("click");f.click("set-reset");await f.resolveCall("coarse",0,{ok:false});for(const k of ["prayer:fixture","weather:fixture","test:sentinel"])assert.equal(f.storage.get(k),k+":original");
});
test("blocked reads, malformed JSON and future-version records stay null without deletion",()=>{
  const f=make(),SC=f.sandbox.SalahConfig;
  assert.equal(SC.loadLocal({getItem:security}),null);for(const raw of ["broken",JSON.stringify({...seed,v:2})]){const bytes=new Map([[SC.KEY,raw]]),storage={getItem:k=>bytes.get(k),removeItem:()=>assert.fail("must not delete")};assert.equal(SC.loadLocal(storage),null);assert.equal(bytes.get(SC.KEY),raw);}
});
test("failure error names are bounded literal text in feedback",()=>{
  const f=make();f.sandbox.localStorage.setItem=()=>{throw {name:"<b>"+"x".repeat(200)+"</b>"};};f.input("set-units","c","change");f.click("setClose");const msg=f.elements.get("settings-persistence-status").textContent;assert.match(msg,/session only/);assert.ok(msg.length<150);assert.doesNotMatch(msg,/[<>]/);
});
test("outside polite status markup and warning overlay avoid a new stack row",()=>{
  const f=make(),before=f.page.slice(0,f.page.indexOf('<div class="settings"'));
  assert.ok(/<[^>]*id="settings-persistence-status"[^>]*aria-live="polite"/.test(before),"polite status is outside dialog");assert.ok(/\.buckle\.persist-warning \.gear[^}]*opacity:1/.test(f.page),"warning reuses overlaid gear");assert.ok(/\.set-live-status\{[^}]*position:absolute/.test(f.page),"status adds no flow row");
});
test("failed reset cancels pending search hint while keeping bytes and current config",async()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY,old=f.storage.get(key),before=f.config();f.input("set-label","Berlin");f.key("set-label","Enter");assert.match(status(f),/Searching/);f.sandbox.localStorage.removeItem=security;f.click("set-reset");
  assert.match(status(f),/saved settings remain/);assert.match(status(f),/Enter to search/);assert.doesNotMatch(status(f),/Searching/);assert.equal(f.storage.get(key),old);assert.deepEqual(f.config(),before);assert.equal(f.calls.coarse.length,0);const after=status(f);
  await f.resolveCall("search",0,[{lat:52.52,lon:13.41,name:"Berlin",norm:"Berlin, Germany",cc:"de"}]);assert.equal(status(f),after);assert.deepEqual(f.config(),before);
});
test("failed reset cancels pending GPS hint and abandoned fix cannot revive it",async()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY,old=f.storage.get(key),before=f.config();f.click("set-pin");assert.match(status(f),/Requesting.*location/);f.sandbox.localStorage.removeItem=security;f.click("set-reset");
  assert.match(status(f),/saved settings remain/);assert.match(status(f),/Enter to search/);assert.doesNotMatch(status(f),/Requesting/);assert.equal(f.storage.get(key),old);assert.deepEqual(f.config(),before);assert.equal(f.calls.coarse.length,0);const after=status(f);
  await f.resolveCall("gps",0,{coords:{latitude:52.52,longitude:13.41,accuracy:25},timestamp:Date.now()});assert.equal(status(f),after);assert.deepEqual(f.config(),before);
});
test("realm-local storage getter denial reaches caller then successful reset clears the warning",async()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY,old=f.storage.get(key);f.sandbox.fixturePrivateStore=f.sandbox.localStorage;f.sandbox.DOMException=DOMException;
  // Node's contextified global swallows some host-created getter exceptions.
  // Define the denied getter in the same realm as the actual production caller.
  f.run('Object.defineProperty(window,"localStorage",{configurable:true,get(){throw new DOMException("blocked getter","SecurityError");}})');
  f.input("set-units","c","change");f.key("set-units","Escape");assert.equal(f.config().units,"c");assert.equal(f.storage.get(key),old);assert.equal(f.run("_storageErr"),"SecurityError");warning(f,/session only/);
  f.buckle.dispatch("click");f.click("set-reset");assert.equal(f.calls.coarse.length,0);assert.match(status(f),/saved settings remain/);assert.equal(f.storage.get(key),old);
  f.run('Object.defineProperty(window,"localStorage",{configurable:true,value:fixturePrivateStore,writable:true})');f.click("set-reset");assert.equal(f.storage.has(key),false);assert.equal(f.calls.coarse.length,1);assert.equal(f.run("_storageErr"),null);assert.equal(f.buckle.querySelector(".gear").textContent,"⚙");await f.resolveCall("coarse",0,{ok:false});assert.match(status(f),/Saved settings cleared.*Enter your location/s);
});
test("actual boot and apply execute scene reset and surface gates with faithful DOM classes",async()=>{
  const f=make(),photo=f.elements.get("mphoto"),mask=f.elements.get("moon-mask-disc");
  assert.equal(f.run('$(".c")===document.querySelector(".c")'),true);assert.equal(f.card.classList.contains("sky-pending"),true);assert.equal(f.card.dataset.appearance,"glass");
  photo.setAttribute("href","fixture-owned-pixels");
  // A decoded legacy map no longer owns visible Moon readiness. This storage
  // fixture supplies the already accepted terrain boundary, not rendered pixels.
  f.run('var fixtureTerrain={};window.SalahMoonRuntime={surface:()=>fixtureTerrain,invalidate(){fixtureTerrain=null;}};');
  f.run('_pbrReady=true;_skySceneKey="old";_skyMoonPresence=1;updateSkySurface()');
  assert.equal(f.card.classList.contains("moon-ready"),true);assert.equal(mask.classList.contains("mask-on"),true);
  f.sandbox.sceneClearCalls=[];
  const dirtyScene=()=>f.run('_skyCommitted=true;_starsProjected=true;_cloudReady=true;cloudState.covLow=.8;cloudState.covMid=.7;cloudState.covHigh=.6;_colDens=new Float32Array([1,2]);_cloudCv={width:7,height:9};_cloudCtx={clearRect:(...args)=>sceneClearCalls.push(args)}');
  const clearedScene=()=>{
    assert.deepEqual(f.json('[_skySceneKey,_skyCommitted,_skyMoonPresence,_starsProjected,_cloudReady,cloudState.covLow,cloudState.covMid,cloudState.covHigh]'),[null,false,0,false,false,0,0,0]);
    assert.deepEqual(f.json('Array.from(_colDens)'),[0,0]);assert.deepEqual(f.json('sceneClearCalls.at(-1)'),[0,0,7,9]);
    assert.equal(f.card.classList.contains("sky-pending"),true);assert.equal(f.card.classList.contains("sky-initializing"),true);assert.equal(f.card.classList.contains("moon-ready"),false);assert.equal(mask.classList.contains("mask-on"),false);
  };
  dirtyScene();const boot=f.boot();clearedScene();assert.deepEqual([f.calls.stars,f.calls.buildWeather],[1,1]);f.calls.prayer[0].resolve();await boot;
  f.run('fixtureTerrain={};_skySceneKey="second-old";_skyMoonPresence=1;updateSkySurface()');dirtyScene();
  f.sandbox.sceneNext={...f.config(),appearance:"contrast"};const apply=f.run('applyConfig(sceneNext,{save:false})');clearedScene();
  assert.equal(f.card.dataset.appearance,"contrast");assert.equal(f.card.getAttribute("data-appearance"),"contrast");assert.deepEqual([f.calls.stars,f.calls.buildWeather],[1,1]);f.calls.prayer[1].resolve();await apply;
});
test("actual apply invalidates owned request attempts before deferred provider work",async()=>{
  const f=make();f.sandbox.cancelled=[];
  f.run('globalThis.ownedOps=Object.keys(_requestSlots).map(kind=>{const op=beginRequest(kind);const a=beginAttempt(op,10000);a.cancel=()=>cancelled.push(kind);a.timer=setTimeout(()=>{},10000);return {op,a};});wxBusy=radarBusy=true;_prayerCooldown.current=_prayerCooldown.prefetch={until:99};');
  f.sandbox.sceneNext={...f.config(),units:"c",appearance:"contrast"};const apply=f.run('applyConfig(sceneNext,{save:false})');
  assert.equal(f.run('_runtimeGeneration'),1);assert.deepEqual(f.json('Object.values(_requestSlots)'),[null,null,null,null]);
  assert.deepEqual(f.json('ownedOps.map(({op,a})=>[requestEligible(op),a.expired,a.controller.signal.aborted,a.timer,op.attempt])'),Array.from({length:4},()=>[false,true,true,null,null]));
  assert.deepEqual(f.sandbox.cancelled,["current","prefetch","weather","radar"]);assert.deepEqual(f.json('[wxBusy,radarBusy,_prayerCooldown.current,_prayerCooldown.prefetch]'),[false,false,null,null]);
  assert.deepEqual([f.config().units,f.config().appearance,f.card.dataset.appearance],["c","contrast","contrast"]);assert.equal(f.calls.prayer.length,1);assert.equal(f.calls.loop,0);f.calls.prayer[0].resolve();await apply;assert.equal(f.calls.loop,1);
});
(async()=>{let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0;})();
