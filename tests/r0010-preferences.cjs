"use strict";
const assert=require("node:assert/strict");
const {fixture,readSource,drain}=require("./r000f-fixture.cjs");
const {widget}=require("./r0011-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
function make(platform="Win32") {
  const f=fixture("builder",{ref,platform});
  if(mutant) {
    let source=readSource("config.js",ref);
    source=source.replace(mutant==="method"?'c.method !== DEFAULTS.method || explicit.indexOf("method") >= 0':'c.units === "c" || explicit.indexOf("units") >= 0',mutant==="method"?'c.method !== DEFAULTS.method':'c.units === "c"');
    f.run(source);
  }
  f.input("method","2","change");f.input("units","f","change");f.run('setMode("local")');return f;
}
const cases=[],test=(name,body)=>cases.push({name,body});
for(const method of ["2","4"])for(const units of ["f","c"])test(`fresh runtime follows selected ${method}/${units} through every export`,async()=>{
  for(const appearance of ["glass","contrast"])for(const mode of ["local","portable"]){
    const f=make();f.input("method",method,"change");f.input("units",units,"change");f.input("appearance",appearance,"change");f.run(`setMode("${mode}")`);
    const h=f.run("hash()"),p=new URLSearchParams(h);
    const expected=mode==="local"?`local=1&method=${method}&units=${units}&appearance=${appearance}`
      :`lat=24.4672&lon=39.6142&label=Madinah&method=${method}&school=0${units==="c"?"&units=c":""}&appearance=${appearance}`;
    assert.equal(h,expected);assert.equal(p.get("appearance"),appearance);assert.equal(p.has("lat"),mode==="portable");assert.equal(p.has("lon"),mode==="portable");
    const snippet=f.elements.get("code").value,preview=f.elements.get("pv").src;
    assert.equal(new URL(snippet.match(/src="([^"]+)"/)[1]).hash.slice(1),h);assert.equal(new URL(preview).hash.slice(1),h);
    for(const platform of ["Win32","Linux"]){
      f.sandbox.navigator.platform=platform;const command=f.run("installCmd().cmd"),carried=command.match(/SALAH_WIDGET_HASH='([^']+)'/)[1];assert.equal(carried,h);
      const w=widget({ref,hash:"#"+carried,open:false}),boot=w.boot();
      if(mode==="local")await w.resolveCall("coarse",0,{ok:true,provider:"GeoJS",cfg:{lat:24.47,lon:39.61,label:"Madinah",method:"4",units:"c",appearance:appearance==="glass"?"contrast":"glass",source:"coarse-ip"}});
      else assert.equal(w.calls.coarse.length,0);
      assert.deepEqual([w.config().method,w.config().units,w.config().appearance],[method,units,appearance]);assert.equal(w.json("units"),units);assert.equal(w.card.dataset.appearance,appearance);assert.equal(w.card.getAttribute("data-appearance"),appearance);
      w.calls.prayer[0].resolve();await boot;
    }
  }
});
test("generic local API stays automatic and ignores unsupported explicit names",async()=>{
  const f=make(),SC=f.sandbox.SalahConfig;
  assert.equal(SC.serialize({}, {mode:"local"}),"local=1");assert.equal(SC.serialize({}, {mode:"local",explicitPrefs:["lat","seed","school"]}),"local=1");
  const w=widget({ref,hash:"#local=1",open:false}), boot=w.boot();await w.resolveCall("coarse",0,{ok:true,cfg:{lat:24.47,lon:39.61,method:"4",units:"c",source:"coarse-ip"}});
  assert.deepEqual([w.config().method,w.config().units],["4","c"]);w.calls.prayer[0].resolve();await boot;
});
test("saved viewer preferences win local and preferLocal on both reloads",async()=>{
  const f=make(),h=f.run("hash()"),seed={lat:51.5,lon:-.12,label:"London",method:"3",units:"c",appearance:"contrast",source:"manual"};
  for(const hash of ["#"+h,"#preferLocal=1&lat=24.47&lon=39.61&method=2&units=f&appearance=glass"])for(let reload=0;reload<2;reload++){
    const w=widget({ref,hash,seed,open:false}),boot=w.boot();assert.equal(w.calls.coarse.length,0);assert.deepEqual([w.config().label,w.config().method,w.config().units,w.config().appearance],["London","3","c","contrast"]);assert.equal(w.card.dataset.appearance,"contrast");w.calls.prayer[0].resolve();await boot;
  }
});
test("portable literal encoding and zero coordinates remain compatible",()=>{
  const f=make(),SC=f.sandbox.SalahConfig,h=SC.serialize({lat:1,lon:2,label:"A & B'#<>",method:"2",school:"0",datefmt:"D / M & YYYY"});
  assert.equal(h,"lat=1&lon=2&label=A+%26+B%27%23%3C%3E&method=2&school=0&datefmt=D+%2F+M+%26+YYYY");
  assert.equal(SC.parseHash(h).cfg.label,"A & B'#<>");assert.equal(SC.parseHash(h).cfg.datefmt,"D / M & YYYY");
  assert.equal(SC.resolve("#lat=0&lon=0").mode,"hardcoded");assert.equal(SC.resolve("#lat=0&lon=0").cfg.lat,0);
});
test("local explanatory prose identifies explicit preferences and saved priority",()=>{
  const f=make(),prose=f.elements.get("modenote").innerHTML;assert.match(prose,/Self-configuring location/);assert.match(prose,/selected here.*fresh viewer/);assert.match(prose,/saved widget settings take precedence/);assert.match(prose,/allow.*geolocation/);
});
test("absent config module retains actual legacy fixed-coordinate boot",async()=>{
  const w=widget({ref,hash:"#lat=0&lon=0&label=Zero&method=2&units=f",moduleMissing:true,open:false}),boot=w.boot();
  assert.deepEqual([w.config().lat,w.config().lon,w.config().label,w.config().method,w.config().units],[0,0,"Zero","2","f"]);
  assert.equal(w.calls.coarse.length,0);w.calls.prayer[0].resolve();await boot;
});
(async()=>{let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0;})();
