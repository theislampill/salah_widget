'use strict';
// R003A R3A-02.3: headless cloud-drift trajectory matrix over the actual authored runtime (R000B fixture boundary; no
// network, no browser). For each case the real applyCloudState(atmosphere(model())) installs wind, then the real
// advanceCloudMotion integrates 60 steps of 100 ms; phase/life/wander and cloudState.wx/wspd are recorded per step.
// Usage: node tools/qa/r003a_drift_matrix.cjs [authored source path]  (default: src/native/index.html) -> JSON on stdout
const path=require('node:path');
if(process.argv[2])process.env.SALAH_WITHDRAWAL_SOURCE=path.resolve(process.argv[2]);
const {fixture}=require('../../tests/weather-no-timetable-fixture.cjs');
const DIRS=[0,90,180,225,270,null],SPEEDS=[0,3,7,20],RATES=[1,4];
async function trajectory({dir,speed,rate,reduced,record}){
 const h=await fixture({reduced});
 h.run('window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:20,azDeg:120},utcMs:simNow(),sample:()=>null})}');
 if(record){h.run(`weather.wind=${speed};weather.windDir=${dir===null?'null':dir};`);}else h.run('weather=null;');
 if(rate!==1)h.run(`FOLLOW_WALL_CLOCK=false;TIMESCALE=${rate};`);
 const steps=[];h.at(890500);h.run('applyCloudState(atmosphere(model()))');
 for(let i=1;i<=60;i++){h.at(890500+100*i);h.run('applyCloudState(atmosphere(model()))');
  steps.push(JSON.parse(h.run('JSON.stringify({phase:_cloudMotion.phase,life:_cloudMotion.life,wander:_cloudMotion.wander,wx:cloudState.wx,wspd:cloudState.wspd})')));}
 return steps;}
(async()=>{const cases=[];
 for(const reduced of [false,true])for(const rate of RATES){
  cases.push({record:false,dir:null,speed:null,rate,reduced});
  for(const dir of DIRS)for(const speed of SPEEDS)cases.push({record:true,dir,speed,rate,reduced});}
 const out=[];for(const c of cases)out.push({case:c,steps:await trajectory(c)});
 process.stdout.write(JSON.stringify({schema:'r003a-drift-matrix/1',cases:out.length,trajectories:out})+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
