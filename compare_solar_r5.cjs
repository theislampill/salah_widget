const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const O=__dirname,R='<candidate>';
const {load}=require(path.join(R,'tests/r001d-harness.cjs'));
const paths=[path.join(O,'intake/solar-before-r4.html'),path.join(R,'src/native/index.html')];
const rigs=paths.map(sourcePath=>load({sourcePath,hash:'#lat=24.47&lon=39.61&tz=Asia/Riyadh&units=c&method=4'}));
const fields=['--sunamt','--sunbodyamt','--suncore','--sunmid','--sunprofile','--sunlift','--sunx2','--sunvx','--sunvy','--sundisc','--sunflat','--sunray','--sunpulse','--sunlow','--moongrp','--moonbeam','--moonfeat','--moonocc','--mrad','--g1','--g2','--g3'];
const rows=[];
for(const reduced of [false,true])for(const [code,cloud,vis] of [[0,0,20000],[2,35,20000],[3,100,20000],[45,100,1000],[63,65,6000]])for(const elevation of [-20,-8,-1.5,-.5,0,1,5.5,10,39.9,40,65]){
 const values=rigs.map(h=>{
  h.ctx.matchMedia=()=>({matches:reduced});
  h.run(`window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:${elevation},azDeg:90},utcMs:simNow(),sample:()=>null})};__fixtureWeatherCurrent.weather_code=${code};__fixtureWeatherCurrent.cloud_cover=${cloud};__fixtureWeatherCurrent.visibility=${vis};weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:'c',zone:tz,retrievedAt:Date.now()})`);
  const atmosphere=JSON.parse(h.run('JSON.stringify(atmosphere(model()))'));
  h.run('paint(atmosphere(model()))');
  return {atmosphere,styles:Object.fromEntries(fields.map(k=>[k,h.select('.c').style.getPropertyValue(k)]))};
 });
 assert.deepEqual(values[1],values[0],JSON.stringify({reduced,code,cloud,vis,elevation}));
 rows.push({reduced,code,cloud,vis,elevation,equal:true,valuesSha256:crypto.createHash('sha256').update(JSON.stringify(values[0])).digest('hex')});
}
const result={schema:'r0021-solar-preservation/v1',sourcePaths:paths,sourceSha256:paths.map(p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')),rows,total:rows.length,status:'PASS',scope:'Whole atmosphere vector plus22 solar/lunar/palette CSS sinks with the horizon present, under doubled DOM/clock/provider boundaries. No native-pixel or performance claim.'};
fs.writeFileSync(path.join(O,'intake/solar-preservation-r5.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,total:result.total,sourceSha256:result.sourceSha256}));
