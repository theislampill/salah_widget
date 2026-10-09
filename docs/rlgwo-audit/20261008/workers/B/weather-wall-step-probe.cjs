'use strict';
// Source-only discriminator for R0020's existing retry consumer. No network,
// browser, OS clock, storage, or production source writes occur in this fixture.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const file='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget/index.html';
const source=fs.readFileSync(file,'utf8');
const start=source.indexOf('async function fetchWeather(){'),end=source.indexOf('// RainViewer tiles retain',start);
assert(start>=0&&end>start);const block=source.slice(start,end);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const base=Date.parse('2026-09-07T12:00:00Z');
async function scenario(step){
  const clock={wall:base,mono:0},calls=[];
  class FixtureDate extends Date{static now(){return clock.wall;}}
  const c=vm.createContext({Date:FixtureDate,SIM:{wx:null},lat:24.47,lon:39.61,weatherTrack:null,lastWxAt:0,lastWxTry:0,wxBusy:false,
    performance:{now:()=>clock.mono},_WX_CURRENT_TTL:900000,_WX_BODY_WAIT:15000,_WX_HOURLY:'temperature_2m,weather_code',
    enc:encodeURIComponent,usableWeatherCoordinates:()=>true,selectedWeather:()=>null,
    beginRequest(){calls.push({wall:clock.wall,mono:clock.mono});return {lat:24.47,lon:39.61,units:'c',requestZone:'UTC',weatherCacheKey:'fixture',generation:0};},
    captureWeatherTarget:()=>({generation:0,lat:24.47,lon:39.61}),beginAttempt:()=>({}),
    // A completed failed acquisition establishes the actual lastWxTry state.
    wxFetchJson:async()=>({ok:false}),attemptEligible:()=>true,finishAttempt(){},finishRequest:()=>true});
  vm.runInContext(block,c);
  await vm.runInContext('fetchWeather()',c);assert.equal(calls.length,1);assert.equal(c.wxBusy,false);
  clock.mono=60000;clock.wall=base+60000+step;
  await vm.runInContext('fetchWeather()',c);
  return {wallStepMs:step,elapsedSinceFailedAttemptMs:clock.mono,now:clock.wall,lastWxTry:c.lastWxTry,totalAttempts:calls.length,
    expectedTotalAttempts:2,postcondition:calls.length===2?'SATISFIED':'UNMET',calls};
}
(async()=>{
  const ordinary=await scenario(0),backward=await scenario(-3600000),forward=await scenario(3600000);
  assert.equal(ordinary.totalAttempts,2,'unchanged-wall eligible retry is a positive control');
  assert.equal(backward.totalAttempts,1,'actual backward correction suppresses the otherwise eligible second attempt');
  assert.equal(forward.totalAttempts,2,'forward correction reaches the wrapper');
  console.log(JSON.stringify({auditTarget:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',sourceSha256:sha(source),extractedFunctionSha256:sha(block),
    scope:'Actual fetchWeather wrapper; acquisition/freshness/ownership dependencies are controlled doubles; no full scheduler/browser claim',
    scenarios:[ordinary,backward,forward],finding:'A completed failed weather acquisition can remain retry-ineligible for approximately one hour after a backward one-hour device wall step, although 60000 ms monotonic time has elapsed.'},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
