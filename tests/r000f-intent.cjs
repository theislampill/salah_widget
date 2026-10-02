"use strict";
const assert=require("node:assert/strict");
const {fixture:sourceFixture}=require("./r000f-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
function removeGate(source,fn,gate) {
  const start=source.indexOf(`function ${fn}(`), end=source.indexOf("\n}",start)+2;
  if(start<0||end<2)throw new Error("mutant function boundary missing");
  const body=source.slice(start,end); if(!body.includes(gate))throw new Error("mutant gate missing");
  return source.slice(0,start)+body.split(gate).join("")+source.slice(end);
}
function fixture(kind,options={}) {
  const mutate=source=>{
    if(kind==="builder"&&["coarse","reverse","gps","forward"].includes(mutant)) {
      const fn={coarse:"detectArea",reverse:"fillNameFromCoords",gps:"locate",forward:"doSearch"}[mutant];
      return removeGate(source,fn,"if(!ownsLookup(owner)) return;");
    }
    if(kind==="settings"&&mutant==="settings-gps")return removeGate(source,"_usePrecise","if(!_ownsSetLookup(owner)) return;");
    if(kind==="settings"&&mutant==="close")return source.replace("_setOpen=false; _setSession++; _invalidateSetLocation(); clearTimeout(_setFocusTimer);","clearTimeout(_setFocusTimer);");
    if(kind==="settings"&&mutant==="candidate") {
      source=removeGate(source,"_invalidateSetLocation","_setCands=[]; _setCandOwner=null;");
      source=removeGate(source,"_showSetCand","if(!_setCandOwner || !_ownsSetLookup(_setCandOwner)) return;");
      return source.replace('_setCands.length>1 && _setCandOwner && _ownsSetLookup(_setCandOwner) && _setCandOwner.label===lab.value','_setCands.length>1');
    }
    return source;
  };
  return sourceFixture(kind,{...options,mutate:mutant?mutate:undefined});
}
const london={lat:51.5,lon:-0.12,name:"London",norm:"London",cc:"gb"};
const ontario={lat:42.98,lon:-81.25,name:"London, Ontario",norm:"London, Ontario",cc:"ca"};
const detected={ok:true,cfg:{lat:40.7,lon:-74,label:"New York",method:"2",source:"coarse-ip"}};
const cases=[];
const test=(name,body)=>cases.push({name,body});
async function search(f,name) { const id=f.kind==="builder"?"label":"set-label"; f.input(id,name); f.key(id,"Enter"); }
const initial=["Madinah","24.4672","39.6142","4"];
test("positive: builder current search and canonical serialized tuple",async()=>{
  const f=fixture("builder",{ref}); await search(f,"London"); await f.resolve("search",0,[london]);
  assert.deepEqual(f.tuple(),["London","51.50000","-0.12000","4"]);
  assert.equal(f.hash(),"lat=51.5&lon=-0.12&label=London&method=4&school=0");
});
test("positive: builder label input already invalidates an older search",async()=>{
  const f=fixture("builder",{ref}); await search(f,"London"); f.input("label","Cairo"); const before=f.snapshot();
  await f.resolve("search",0,[london]); assert.equal(f.snapshot(),before);
});
test("coarse-after-London cannot change form, feedback, pin, bias or export",async()=>{
  const f=fixture("builder",{ref}); await search(f,"London"); await f.resolve("search",0,[london]); const before=f.snapshot();
  await f.resolve("coarse",0,detected); assert.equal(f.snapshot(),before);
});
test("builder reverse body after newer reverse cannot mix a tuple",async()=>{
  const f=fixture("builder",{ref}); f.input("lat","40.7"); f.input("lon","-74"); await f.advance(700);
  f.input("lat","24.47"); f.input("lon","39.61"); await f.advance(700);
  await f.resolve("reverse",1,{city:"Madinah",countryCode:"SA",continentCode:"AS"}); const before=f.snapshot();
  await f.resolve("reverse",0,{city:"New York",countryCode:"US",continentCode:"NA"}); assert.equal(f.snapshot(),before);
  assert.deepEqual(f.tuple(),["Madinah","24.47","39.61","4"]);
});
test("builder GPS after manual coordinates is a complete no-op",async()=>{
  const f=fixture("builder",{ref}); f.click("geo"); f.input("lat","30"); f.input("lon","31"); const before=f.snapshot();
  await f.resolve("gps",0,{coords:{latitude:51.5,longitude:-0.12}}); assert.equal(f.snapshot(),before);
});
test("builder search after manual coordinates cannot overwrite export",async()=>{
  const f=fixture("builder",{ref}); await search(f,"London"); f.input("lat","30"); f.input("lon","31"); const before=f.snapshot();
  await f.resolve("search",0,[london]); assert.equal(f.snapshot(),before);
});
test("builder accepted GPS reverse continuation and manual method override",async()=>{
  const f=fixture("builder",{ref}); f.click("geo"); f.input("method","3","change"); f.input("units","c","change");
  await f.resolve("gps",0,{coords:{latitude:51.5,longitude:-0.12}});
  await f.resolve("reverse",0,{city:"London",countryCode:"GB",continentCode:"EU"});
  assert.deepEqual(f.tuple(),["London","51.50000","-0.12000","3"]);
  assert.equal(new URLSearchParams(f.hash()).get("units"),"c");
});
test("builder manual label retained during deliberate current GPS",async()=>{
  const f=fixture("builder",{ref}); f.input("label","Custom name"); f.click("geo");
  await f.resolve("gps",0,{coords:{latitude:51.5,longitude:-0.12}});
  await f.resolve("reverse",0,{city:"London",countryCode:"GB",continentCode:"EU"});
  assert.deepEqual(f.tuple(),["Custom name","51.50000","-0.12000","4"]);
});
test("settings London then Cairo Shift+Enter cannot save London",async()=>{
  const f=fixture("settings",{ref}); await search(f,"London"); f.input("set-label","Cairo"); f.key("set-label","Enter",true); const before=f.snapshot();
  await f.resolve("search",0,[london]); assert.equal(f.snapshot(),before); f.click("setClose");
  const saved=f.sandbox.SalahConfig.loadLocal(); assert.equal(saved.label,"Cairo"); assert.equal(saved.lat,24.4672);
});
test("settings changed query requests Cairo instead of cycling London",async()=>{
  const f=fixture("settings",{ref}); await search(f,"London"); await f.resolve("search",0,[london,ontario]); await search(f,"Cairo");
  assert.equal(f.calls.search.length,2); assert.equal(f.calls.search[1].q,"Cairo"); assert.equal(f.tuple()[0],"Cairo");
});
test("positive: both forms retain same-query candidate cycling",async()=>{
  for(const kind of ["builder","settings"]) {
    const f=fixture(kind,{ref}); await search(f,"London"); await f.resolve("search",0,[london,ontario]); const id=kind==="builder"?"label":"set-label";
    f.key(id,"Enter"); assert.equal(f.tuple()[1],"42.98000"); f.key(id,"Enter"); assert.equal(f.tuple()[1],"51.50000"); assert.equal(f.calls.search.length,1);
  }
});
test("both forms A to B to A bind results to newest generation",async()=>{
  for(const kind of ["builder","settings"]) {
    const f=fixture(kind,{ref}); const id=kind==="builder"?"label":"set-label";
    await search(f,"London"); f.input(id,"Cairo"); await search(f,"London");
    await f.resolve("search",1,[ontario]); const before=f.snapshot(); await f.resolve("search",0,[london]); assert.equal(f.snapshot(),before);
  }
});
test("settings GPS after manual coordinates cannot mark precise or save it",async()=>{
  const f=fixture("settings",{ref}); f.click("set-pin"); f.input("set-lat","30"); f.input("set-lon","31"); const before=f.snapshot();
  await f.resolve("gps",0,{ok:true,lat:51.5,lon:-0.12}); assert.equal(f.snapshot(),before); f.click("setClose"); assert.equal(f.sandbox.SalahConfig.loadLocal().lat,30);
});
test("settings precise permission await cannot outlive newer intent",async()=>{
  const f=fixture("settings",{ref,deferPermission:true}); f.click("set-pin"); await f.resolve("gps",0,{ok:true,lat:51.5,lon:-0.12});
  f.input("set-lat","30"); const before=f.snapshot(); await f.resolve("permission",0,"granted"); assert.equal(f.snapshot(),before);
});
test("settings close/reopen invalidates search, GPS and reset detection",async()=>{
  for(const op of ["search","gps","coarse"]) {
    const f=fixture("settings",{ref}); if(op==="search")await search(f,"London"); else f.click(op==="gps"?"set-pin":"set-reset");
    f.click("setClose"); f.buckle.dispatch("click"); const before=f.snapshot();
    await f.resolve(op,0,op==="search"?[london]:op==="gps"?{ok:true,lat:51.5,lon:-0.12}:detected); assert.equal(f.snapshot(),before);
  }
});
test("settings close alone makes pending search and GPS complete no-ops",async()=>{
  for(const op of ["search","gps"]) {
    const f=fixture("settings",{ref}); if(op==="search")await search(f,"London"); else f.click("set-pin");
    f.click("setClose"); const before=f.snapshot();
    await f.resolve(op,0,op==="search"?[london]:{ok:true,lat:51.5,lon:-0.12}); assert.equal(f.snapshot(),before);
  }
});
test("settings delayed open focus cannot steal restored opener after close",async()=>{
  const f=fixture("settings",{ref}); f.click("setClose"); await f.advance(30); assert.equal(f.document.activeElement,f.buckle);
});
test("settings reset detection after manual edit cannot applyConfig",async()=>{
  const f=fixture("settings",{ref}); f.click("set-reset"); f.input("set-lat","30"); f.input("set-lon","31"); const before=f.snapshot();
  await f.resolve("coarse",0,detected); assert.equal(f.snapshot(),before); assert.equal(f.calls.applied.length,0);
});
test("positive: settings current GPS and reset remain usable",async()=>{
  const f=fixture("settings",{ref}); f.click("set-pin"); await f.resolve("gps",0,{ok:true,lat:51.5,lon:-0.12}); assert.equal(f.tuple()[1],"51.50000");
  f.click("set-reset"); await f.resolve("coarse",0,detected); assert.equal(f.tuple()[1],"40.7"); assert.equal(f.calls.applied.length,1);
});
test("both forms current error survives obsolete failure and feedback timer",async()=>{
  for(const kind of ["builder","settings"]) {
    const f=fixture(kind,{ref}); await search(f,"London"); await search(f,"Cairo"); await f.reject("search",1); const before=f.snapshot();
    await f.reject("search",0); assert.equal(f.snapshot(),before);
    if(kind==="builder") { await search(f,"London"); await f.resolve("search",2,[london]); const success=f.snapshot(); await f.advance(4000); assert.equal(f.snapshot(),success); }
  }
});
test("settings unrelated preference edit preserves a current lookup",async()=>{
  const f=fixture("settings",{ref}); await search(f,"London"); f.input("set-method","3","change"); f.input("set-units","c","change");
  await f.resolve("search",0,[london]); assert.deepEqual(f.tuple(),["London","51.50000","-0.12000","3"]); f.click("setClose"); assert.equal(f.sandbox.SalahConfig.loadLocal().units,"c");
});
async function main() {
  let failed=0; for(const c of cases) { try { await c.body(); console.log("PASS",c.name); } catch(e) { failed++; console.error("FAIL",c.name,"\n",e.stack); } }
  console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"})); process.exitCode=failed?1:0;
}
main();
