'use strict';
// Every mutant reaches the same actual consumer assertion as its healthy run.
// Setup errors are not mutation detection; no mutated source is written to disk.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {fixture,withdrawn,sourcePath}=require('./weather-no-timetable-fixture.cjs');
const source=fs.readFileSync(sourcePath,'utf8');
const expiry=async source=>{const h=await fixture({source});assert(h.read().raster.currentFills>0);h.at(901000);h.run('render()');withdrawn(h.read());};
const cases=[
 ['bypass no-model withdrawal','reconcileCloudPublication(d);withdrawWeatherEffects(d,"prayer timetable unavailable");','withdrawWeatherEffects(d,"prayer timetable unavailable");',expiry],
 ['header-only repair','if(changed){','if(false){',expiry],
 ['zero numeric state but retain raster','if(_cloudCtx&&_cloudCv)_cloudCtx.clearRect(0,0,_cloudCv.width,_cloudCv.height);','if(_cloudCtx&&_cloudCv)void _cloudCv;',expiry],
 ['expiry checked only at acquisition','return weatherEligibility(record,now).eligible?record:null;','return record;',async source=>{const h=await fixture({source});assert(h.read().raster.currentFills>0);h.at(900000);h.run('render()');h.at(900077);withdrawn(h.paint());}],
 ['source age reset on receipt','w.currentValidAt=cached?wxNumber(input.currentValidAt):wxEpoch(w.currentTime,ctx.zone);','w.currentValidAt=ctx.retrievedAt;',async source=>{const h=await fixture({source,fetch:async(u,init,h,payload)=>u.hostname==='api.open-meteo.com'?{ok:true,json:async()=>payload({time:'2026-09-08T23:44'})}:new Promise(()=>{})});assert.equal(h.read().selected,false);withdrawn(h.read());}],
 ['reseed every tick','if(key!==_cloudMotion.key){','if(true){',async source=>{const h=await fixture({source}),initial=h.read();assert(initial.raster.currentFills>0);h.at(891000);const moved=h.paint();assert.notDeepEqual(moved.phase,initial.phase);}],
 ['unknown labelled observed-clear','{icon:"—",label:"Weather unavailable — no eligible current condition"}','{icon:"☀️",label:"Observed clear"}',async source=>{const h=await fixture({source});h.at(901000);h.run('render()');assert.equal(h.read().header.icon,'—');assert.match(h.read().header.label,/Weather unavailable/);}],
];
for(const [name,from,to,discriminator]of cases)test('real-consumer mutation discriminator: '+name,async()=>{
 assert.equal(source.split(from).length,2,'one declared mutation location');await discriminator(source);
 await assert.rejects(()=>discriminator(source.replace(from,to)),error=>error instanceof assert.AssertionError,'only an actual assertion failure detects the mutant');
});
