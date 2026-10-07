"use strict";
const test=require("node:test"), assert=require("node:assert/strict");
const {source,clone,ordinary,polar,harness,finiteConsumers}=require("./r0002-harness.cjs");
function circles(svg) { return [...svg.matchAll(/<circle class="([^"]*)" cx="([^"]*)" cy="([^"]*)" r="([^"]*)"([^>]*?)(?:\/>|>(.*?)<\/circle>)/gs)].map(x=>({cls:x[1],x:x[2],y:x[3],r:x[4],attrs:x[5],title:x[6]||""})); }
function adjustment(dot,status) { assert.match(dot.attrs,new RegExp(`data-adjustment="${status}"`)); assert.ok(dot.title.length>0,"adjustment description absent"); }
async function london(raw) {
  const data=clone(ordinary); data.date.gregorian={date:"21-06-2026",day:"21",month:{number:6,en:"June"},year:"2026"};
  data.timings={Fajr:"02:31",Sunrise:"04:43",Dhuhr:"13:02",Asr:"17:25",Sunset:"21:22",Maghrib:"21:22",Isha:"23:27"};
  data.meta={timezone:"Europe/London",method:{id:3,params:{Fajr:18,Isha:17}},latitudeAdjustmentMethod:"ANGLE_BASED"};
  const h=harness({source:raw,data,date:"21-06-2026",epoch:"2026-06-21T11:00:00Z",zone:"Europe/London",lat:51.5074,lon:-0.1278});
  await h.load(); return {h,...finiteConsumers(h)};
}
// Restoring universal -14 or sharing Fajr's result with Isha must break these
// assertions on actual emitted marker classes; helper-only status is insufficient.
test("London accepted 18/17 method gains both adjusted markers, retains geometry",async()=>{
  const {svg}=await london(); const dots=circles(svg);
  assert.equal(dots.length,6); assert.match(dots[0].cls,/\badj\b/); assert.match(dots[5].cls,/\badj\b/);
  adjustment(dots[0],"unreachable-angle"); adjustment(dots[5],"unreachable-angle");
  assert.deepEqual([dots[0].x,dots[0].y,dots[0].r],["19.37","134.93","5"]);
  assert.deepEqual([dots[5].x,dots[5].y,dots[5].r],["274.41","133.93","5"]);
  assert.match(dots[1].cls,/\bring\b/); assert.equal(dots[1].y,"104.00"); assert.equal(dots[4].y,"104.00");
  assert.equal(dots[2].x,"149.84","Dhuhr's post-transit placement changed");
});
test("complete Tromso summer retains both adjusted rings",async()=>{
  const p=polar("summer"), data=p.envelope.data;
  const h=harness({data,body:p.envelope,date:"21-06-2026",epoch:p.epoch,zone:"Europe/Oslo",lat:69.6492,lon:18.9553});
  await h.load(); const dots=circles(finiteConsumers(h).svg);
  assert.match(dots[0].cls,/\badj\b/); assert.match(dots[5].cls,/\badj\b/);
});
test("Madinah angle remains reachable, 90 min Isha is explicit unknown",async()=>{
  const data=clone(ordinary); data.timings={Fajr:"04:46",Sunrise:"06:05",Dhuhr:"12:20",Asr:"15:49",Sunset:"18:34",Maghrib:"18:34",Isha:"20:04"};
  data.meta={timezone:"Asia/Riyadh",method:{id:4,params:{Fajr:18.5,Isha:"90 min"}},latitudeAdjustmentMethod:"ANGLE_BASED"};
  const h=harness({data,epoch:"2026-09-07T09:00:00Z",zone:"Asia/Riyadh",method:4}); await h.load(); const dots=circles(finiteConsumers(h).svg);
  assert.doesNotMatch(dots[0].cls,/\badj\b/); adjustment(dots[0],"reachable-angle");
  assert.doesNotMatch(dots[5].cls,/\badj\b/); adjustment(dots[5],"unknown");
  assert.match(dots[5].title,/unavailable/i); assert.doesNotMatch(dots[5].title,/unadjusted/i);
});
async function isolatedRange(min,max,params,raw) {
  const data=clone(ordinary); data.meta.method={id:3,params};
  const h=harness({data,source:raw}); await h.load();
  // Extrema double only for isolated numerical boundaries; full solar consumers
  // above retain the production elevation helper.
  h.run(`solarElevationDeg=(M,a)=>Math.abs(a-(M.sunrise+M.sunset)/2)<1e-6 ? ${max} : ${min};`);
  return circles(h.run("drawArc(model())"));
}
for(const [min,max,params,fajr,isha] of [
  [-17.5,40,{Fajr:18,Isha:17},"unreachable-angle","reachable-angle"],
  [-17.5,40,{Fajr:17,Isha:18},"reachable-angle","unreachable-angle"],
  [-18,40,{Fajr:18,Isha:18},"reachable-angle","reachable-angle"],
  [-17.999,40,{Fajr:18,Isha:18},"unreachable-angle","unreachable-angle"],
  [-18.001,40,{Fajr:18,Isha:18},"reachable-angle","reachable-angle"],
  [-40,-20,{Fajr:18,Isha:18},"unreachable-angle","unreachable-angle"]
]) test(`independent angle/range boundary ${min}/${max}/${JSON.stringify(params)}`,async()=>{
  const d=await isolatedRange(min,max,params); adjustment(d[0],fajr); adjustment(d[5],isha);
  for(const [i,want] of [[0,fajr],[5,isha]]) assert.equal(/\badj\b/.test(d[i].cls),want==="unreachable-angle");
});
for(const param of ["90 min","18",null,0,-18,"abc","90 mins <img>"]) test(`unsupported method parameter stays unknown: ${param}`,async()=>{
  const d=await isolatedRange(-17.5,40,{Fajr:param,Isha:param});
  for(const i of [0,5]) {adjustment(d[i],"unknown"); assert.doesNotMatch(d[i].cls,/\badj\b/); assert.doesNotMatch(d[i].title,/<img>/);}
});
test("nonfinite and missing method metadata stays unknown",async()=>{
  const {h}=await london(); h.run("today.meta.method.params={Fajr:NaN,Isha:Infinity}");
  let d=circles(h.run("drawArc(model())")); adjustment(d[0],"unknown"); adjustment(d[5],"unknown");
  h.run("delete today.meta.method"); d=circles(h.run("drawArc(model())")); adjustment(d[0],"unknown"); adjustment(d[5],"unknown");
});
test("new accepted payload parameters are consumed on next synchronous arc",async()=>{
  const {h}=await london(); h.body.data.meta.method.params={Fajr:12,Isha:17}; await h.load();
  assert.equal(h.requests.length,2); assert.equal(h.run("today.meta.method.params.Fajr"),12);
  const d=circles(h.run("drawArc(model())"));
  adjustment(d[0],"reachable-angle"); adjustment(d[5],"unreachable-angle");
  assert.doesNotMatch(d[0].cls,/\badj\b/); assert.match(d[5].cls,/\badj\b/);
});
function mutant(before,after) {
  const raw=source(); assert.equal(raw.split(before).length-1,1,"mutation owner drifted"); return raw.replace(before,after);
}
test("mutant restoring universal 14 is killed by actual London marker classes",async()=>{
  const raw=mutant('const adj = classification&&classification.status==="unreachable-angle";','const adj = minRealE > -14 && (p.k==="Fajr"||p.k==="Isha");');
  const {svg}=await london(raw), d=circles(svg);
  assert.throws(()=>assert.match(d[0].cls,/\badj\b/)); assert.throws(()=>assert.match(d[5].cls,/\badj\b/));
});
test("mutant sharing Fajr result is killed by asymmetric Isha",async()=>{
  const raw=mutant("const angle=params&&params[k];","const angle=params&&params.Fajr;");
  const d=await isolatedRange(-17.5,40,{Fajr:18,Isha:17},raw);
  assert.throws(()=>adjustment(d[5],"reachable-angle")); assert.match(d[5].cls,/\badj\b/);
});
test("mutant parseFloat interval is killed by actual unknown class/description",async()=>{
  const raw=mutant("const angle=params&&params[k];","const angle=params&&parseFloat(params[k]);");
  const d=await isolatedRange(-17.5,40,{Fajr:18,Isha:"90 min"},raw);
  assert.throws(()=>adjustment(d[5],"unknown")); assert.match(d[5].cls,/\badj\b/);
});
test("mutant description-only change is killed by actual class output",async()=>{
  const raw=mutant('const adj = classification&&classification.status==="unreachable-angle";','const adj = false;');
  const {svg}=await london(raw), d=circles(svg); adjustment(d[0],"unreachable-angle");
  assert.throws(()=>assert.match(d[0].cls,/\badj\b/));
});
test("mutant claiming unknown reachable is killed by status",async()=>{
  const raw=mutant('return {status:"unknown",description:','return {status:"reachable-angle",description:');
  const d=await isolatedRange(-17.5,40,{Fajr:18,Isha:"90 min"},raw); assert.throws(()=>adjustment(d[5],"unknown"));
});
test("mutant ignoring maximum is killed by range wholly below target",async()=>{
  const raw=mutant("const reached=minRealE<=-angle && -angle<=maxRealE;","const reached=minRealE<=-angle;");
  const d=await isolatedRange(-40,-20,{Fajr:18,Isha:18},raw); assert.throws(()=>adjustment(d[0],"unreachable-angle"));
});
test("mutant strict equality is killed by boundary",async()=>{
  const raw=mutant("const reached=minRealE<=-angle && -angle<=maxRealE;","const reached=minRealE<-angle && -angle<maxRealE;");
  const d=await isolatedRange(-18,40,{Fajr:18,Isha:18},raw); assert.throws(()=>adjustment(d[0],"reachable-angle"));
});
