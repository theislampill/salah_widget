"use strict";
const test=require("node:test"), assert=require("node:assert/strict");
const {source,sha256,clone,ordinary,polar,harness,finiteConsumers}=require("./r0002-harness.cjs");
// Removing required-clock validation, cache admission or own-key lookup must
// make the corresponding reachable loader/formatter assertions fail.
async function rejected(options) {
  const h=harness(options); await h.load(); const s=h.state();
  assert.equal(s.today,null,"invalid record entered today");
  assert.equal(s.tomorrow,null); assert.equal(s.zone,options?.zone||"UTC","invalid record adopted a timezone");
  assert.equal(h.writes.length,0,"invalid record persisted");
  assert.equal(h.rendered.length,0,"invalid record reached render");
  assert.match(s.error,/Could not load prayer times/);
  assert.equal(h.requests.length,3);
}
test("source and ordinary synthetic fixture identities",()=>{
  console.log(JSON.stringify({sourceSHA256:sha256(source()),ordinaryFixtureSHA256:sha256(JSON.stringify(ordinary))}));
});
test("ordinary record reaches real loader/cache/model/arc",async()=>{
  const h=harness(); await h.load(); assert.equal(h.state().today.date.gregorian.date,"07-09-2026");
  assert.equal(h.requests.length,1); assert.equal(h.writes.length,1); assert.equal(h.writes[0].key,"salah:24.47|39.61|UTC|3|0");
  assert.equal(h.state().lastDate,"07-09-2026"); finiteConsumers(h);
});
test("ordinary provider 400 envelope stays rejected",()=>rejected({httpOk:false,httpStatus:400,body:{code:400,status:"ERROR",data:{}}}));
const invalid=[
  ["empty timings",d=>{d.timings={};}],
  ["missing Fajr",d=>{delete d.timings.Fajr;}],
  ["nonfinite exponent Dhuhr",d=>{d.timings.Dhuhr="1e999:00";}],
  ["out-of-range clock",d=>{d.timings.Dhuhr="25:99";}],
  ["extra clock component",d=>{d.timings.Fajr="05:00:10";}],
  ["missing clock component",d=>{d.timings.Fajr="05:";}],
  ["clock nonstring",d=>{d.timings.Fajr=500;}],
  ["wrong requested Gregorian date",d=>{d.date.gregorian={date:"06-09-2026",day:"06",month:{number:9,en:"September"},year:"2026"};}],
  ["contradictory Gregorian primitives",d=>{d.date.gregorian.day="06";}],
  ["normalized impossible Gregorian date",d=>{d.date.gregorian={date:"31-09-2026",day:"31",month:{number:9},year:"2026"};}],
  ["invalid timezone",d=>{d.meta.timezone="Invalid/Zone";}],
  ["offset string is not an IANA timezone",d=>{d.meta.timezone="+00:00";}],
  ["malformed optional Sunset",d=>{d.timings.Sunset="18:99";}]
];
for(const [name,mutate] of invalid) test(`${name} rejected before adoption/persistence`,()=>{
  const data=clone(ordinary); mutate(data); return rejected({data});
});
for(const options of [
  {httpOk:false,httpStatus:500,body:{code:500,status:"ERROR",data:ordinary}},
  {httpOk:false,httpStatus:500,body:{code:200,status:"OK",data:ordinary}},
  {httpOk:true,body:{code:500,status:"ERROR",data:ordinary}},
  {httpOk:true,body:{code:200,status:"ERROR",data:ordinary}},
  {httpOk:null,body:{code:200,status:"OK",data:ordinary}},
  {httpOk:true,body:[]}
]) test(`HTTP/envelope contradiction ${JSON.stringify(options).slice(0,65)}`,()=>rejected(options));
test("corrupt matching cache misses and healthy live source recovers",async()=>{
  const h=harness({cache:{date:"07-09-2026",data:{timings:null,meta:{timezone:"UTC"}}}});
  await h.load(); assert.ok(h.requests.length>0); assert.equal(h.state().today.date.gregorian.date,"07-09-2026");
  assert.equal(h.rendered.length,1); assert.equal(h.writes.length,1); finiteConsumers(h);
});
for(const cache of ["{broken",{date:"07-09-2026",data:{...clone(ordinary),timings:{}}}]) test("invalid cache is a miss",async()=>{
  const h=harness({cache}); await h.load(); assert.equal(h.rendered.length,1); assert.equal(h.requests.length,1); finiteConsumers(h);
});
test("legacy valid cache survives denied network and writes",async()=>{
  const h=harness({cache:{date:"07-09-2026",data:ordinary},networkDenied:true,writeDenied:true});
  await h.load(); assert.equal(h.rendered.length,1); assert.equal(h.writes.length,0);
  assert.equal(h.state().error,""); finiteConsumers(h);
});
test("valid live record survives storage denial",async()=>{
  const h=harness({writeDenied:true,readDenied:true}); await h.load(); assert.equal(h.state().error,""); finiteConsumers(h);
});
test("suffix clocks and absent Sunset remain compatible",async()=>{
  const data=clone(ordinary); data.timings.Fajr=" 05:00 (UTC) "; delete data.timings.Sunset;
  const h=harness({data}); await h.load(); assert.equal(h.run("fmt(today.timings.Fajr)"),"05:00"); finiteConsumers(h);
});
for(const season of ["summer","winter"]) for(const mode of ["network","offline-cache"]) test(`complete Tromso ${season} ${mode} consumer replay`,async()=>{
  const p=polar(season), data=p.envelope.data, date=data.date.gregorian.date;
  const h=harness({data,body:p.envelope,date,epoch:p.epoch,lat:69.6492,lon:18.9553,zone:"Europe/Oslo",method:3,
    ...(mode==="offline-cache"?{cache:{date,data},networkDenied:true}: {})});
  await h.load(); assert.equal(h.state().today.date.gregorian.date,date); assert.equal(h.state().zone,"Europe/Oslo"); finiteConsumers(h);
  if(mode==="offline-cache") assert.equal(h.writes.length,0); else assert.equal(h.writes.length,1);
});
test("missing optional AH does not discard usable timings",async()=>{
  const data=clone(ordinary); delete data.date.hijri;
  const h=harness({data}); await h.load(); finiteConsumers(h); assert.equal(h.run("fmtDate(today.date.hijri)"),"");
});
for(const hijri of [ {}, {year:"1448",day:"bad",month:{number:2,en:"Safar"}}, {year:"1448",day:"99",month:{number:99,en:"Safar"}}, {year:"1e999",day:"19",month:{number:2,en:"Safar"}}, {year:"1448",day:"19",month:{number:2,en:7}} ]) test(`malformed optional AH remains unavailable ${JSON.stringify(hijri)}`,async()=>{
  const data=clone(ordinary); data.date.hijri=hijri;
  const h=harness({data,hash:"&datefmt=YYYY%20YY%20MMMM%20MMM%20MM%20M%20DD%20D"}); await h.load(); finiteConsumers(h);
  assert.equal(h.run("fmtDate(today.date.hijri)"),"");
});
test("longest formatter tokens preserved",async()=>{
  const h=harness({hash:"&datefmt=YYYY%20YY%20MMMM%20MMM%20MM%20M%20DD%20D"}); await h.load();
  assert.equal(h.run("fmtDate(today.date.hijri)"),"1448 48 Safar Saf 02 2 19 19");
});
test("numeric formatter needs no optional month name",async()=>{
  const data=clone(ordinary); delete data.date.hijri.month.en;
  const h=harness({data}); await h.load(); assert.equal(h.run("fmtDate(today.date.hijri)"),"1448-02-19");
});
test("optional AH 31 is unavailable while real Gregorian 31 remains valid",async()=>{
  const data=clone(ordinary); data.date.hijri.day="31";
  const h=harness({data}); await h.load(); finiteConsumers(h); assert.equal(h.run("fmtDate(today.date.hijri,'hijri')"),"");
  assert.equal(h.run("fmtDate({year:'2026',month:{number:8,en:'August'},day:'31'})"),"2026-08-31");
});
test("valid AH month 2 day 30 stays displayable before explicit calendar caller joins",async()=>{
  const data=clone(ordinary); data.date.hijri.day="30";
  const h=harness({data}); await h.load(); finiteConsumers(h);
  assert.equal(h.run("fmtDate(today.date.hijri)"),"1448-02-30");
  assert.equal(h.run("fmtDate(today.date.hijri,'hijri')"),"1448-02-30");
});
for(const literal of ["constructor","__proto__","toString","valueOf","hasOwnProperty"]) test(`missing-config format literal ${literal}`,async()=>{
  const h=harness({config:false,hash:`&datefmt=${literal}`}); await h.load(); assert.equal(h.run("fmtDate(today.date.hijri)"),literal);
});
for(const [alias,want] of [["iso","1448-02-19"],["us","02/19/1448"],["eu","19/02/1448"],["long","19 Safar 1448"]]) for(const config of [true,false]) test(`format alias ${alias}, config=${config}`,async()=>{
  const h=harness({config,hash:`&datefmt=${alias}`}); await h.load(); assert.equal(h.run("fmtDate(today.date.hijri)"),want);
});
function mutant(before,after) {
  const raw=source(); assert.equal(raw.split(before).length-1,1,"mutation owner drifted");
  return raw.replace(before,after);
}
test("mutant bypassing network admission is killed by actual loader state",async()=>{
  const raw=mutant("const admitted=admitPrayerRecord(j.data,dateStr);","const admitted={ok:true,data:j.data,timezone:j.data.meta.timezone};");
  const data=clone(ordinary); data.timings={};
  await assert.rejects(rejected({source:raw,data}),/invalid record entered today/);
});
test("mutant removing required clocks is killed before model consumption",async()=>{
  const raw=mutant('for(const k of prayers) if(!validClock(data.timings[k])) return {ok:false,reason:"clock:"+k};',"");
  const data=clone(ordinary); data.timings.Dhuhr="1e999:00";
  await assert.rejects(rejected({source:raw,data}),/invalid record entered today/);
});
test("mutant bypassing cache admission is killed by recovery render boundary",async()=>{
  const raw=mutant("const admitted=admitPrayerRecord(j.data,j.date); if(admitted.ok) return admitted.data;","return j.data;");
  const h=harness({source:raw,cache:{date:"07-09-2026",data:{...clone(ordinary),timings:{}}}}); await h.load();
  assert.throws(()=>assert.equal(h.rendered.length,1),/2 !== 1/);
  assert.equal(Object.keys(h.rendered[0].today.timings).length,0);
});
test("mutant removing own-key alias guard is killed by literal output",async()=>{
  const raw=mutant('Object.prototype.hasOwnProperty.call(_P,_df.toLowerCase())?_P[_df.toLowerCase()]:_df','_P[_df.toLowerCase()]||_df');
  const h=harness({source:raw,config:false,hash:"&datefmt=constructor"}); await h.load();
  assert.throws(()=>assert.equal(h.run("fmtDate(today.date.hijri)"),"constructor"));
});
for(const season of ["summer","winter"]) test(`mutant strict ordering is killed by complete ${season} captured record`,async()=>{
  const raw=mutant('const h=data.date.hijri;', 'for(let i=1;i<prayers.length;i++) if(mins(data.timings[prayers[i]])<=mins(data.timings[prayers[i-1]])) return {ok:false,reason:"strict-order"};\n  const h=data.date.hijri;');
  const p=polar(season), data=p.envelope.data;
  const h=harness({source:raw,data,body:p.envelope,date:data.date.gregorian.date,epoch:p.epoch,lat:69.6492,lon:18.9553,zone:"Europe/Oslo"}); await h.load();
  assert.throws(()=>assert.ok(h.state().today,"captured polar record rejected"),/captured polar record rejected/);
});
test("mutant dropping HTTP gate is killed independently of provider envelope",async()=>{
  const raw=mutant('if(r.ok!==true) throw new Error("bad api HTTP");',"");
  await assert.rejects(rejected({source:raw,httpOk:false,httpStatus:500,body:{code:200,status:"OK",data:ordinary}}),/invalid record entered today/);
});
