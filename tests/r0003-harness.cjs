"use strict";
// Source-bound fixture. Actual config, clock, admission/cache/transport, model, render,
// boot/apply and the existing rAF loop run unchanged. Moon/star/theme/canvas doubles
// contain unrelated rendering; these tests make no native or visual qualification claim.
const fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const assert=require("node:assert/strict"),crypto=require("node:crypto");
const repo=path.resolve(__dirname,"..");
const sourcePath=process.env.SALAH_REQUEST_SOURCE||path.join(repo,"index.html");
const source=()=>fs.readFileSync(sourcePath,"utf8");
const config=fs.readFileSync(process.env.SALAH_REQUEST_CONFIG||path.join(repo,"config.js"),"utf8");
const ordinaryRaw=fs.readFileSync(path.join(repo,"tests/r0002-ordinary.json"),"utf8");
assert.equal(crypto.createHash("sha256").update(ordinaryRaw).digest("hex"),"40c6412a36a4644ec9db9a5c92ae2e682aa22dfd6bac45be249886cfe7e76282");
const ordinary=JSON.parse(ordinaryRaw),copy=x=>JSON.parse(JSON.stringify(x));
function between(raw,a,b){const i=raw.indexOf(a),j=raw.indexOf(b,i+a.length);assert.ok(i>=0&&j>i,`source owner missing: ${a} / ${b}`);return raw.slice(i,j);}
function record(day="07-09-2026",zone="UTC",tag="ordinary"){
  const r=copy(ordinary),[d,mo,y]=day.split("-").map(Number);r.tag=tag;r.meta.timezone=zone;
  r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,"0"),month:{number:mo,en:"September"},year:String(y)};
  return r;
}
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
async function settle(){for(let i=0;i<16;i++)await Promise.resolve();}
function harness(options={}){
  const raw=options.source||source();
  const slice=(a,b)=>between(raw,a,b);
  let elapsed=0,wall=Date.parse(options.epoch||"2026-09-07T12:00:00Z"),serial=0,context;
  const timers=new Map(),frames=new Map(),events=new Map(),nodes=new Map(),storage=new Map(),writes=[],requests=[],paints=[],errors=[];
  class ClockDate extends Date {constructor(...a){super(...(a.length?a:[wall]));}static now(){return wall;}}
  function run(code){return vm.runInContext(code,context,{timeout:300});}
  function state(){return copy(run("({today,tomorrow,tz,lat,lon,method,school,lastDate,fetchingTomorrow,_prayerStale,_loopStarted})"));}
  function node(selector){if(!nodes.has(selector)){
    let html="",text="";const n={dataset:{},style:{setProperty(){}},classList:{add(){},toggle(){},remove(){},contains(){return false;}},setAttribute(){},getAttribute(){return null;}};
    Object.defineProperty(n,"innerHTML",{get:()=>html,set:v=>{html=String(v);if(selector==="#ce")paints.push({ce:html,at:elapsed,...state()});}});
    Object.defineProperty(n,"textContent",{get:()=>text,set:v=>{text=String(v);if(selector===".left")errors.push({text,at:elapsed});}});nodes.set(selector,n);
  }return nodes.get(selector);}
  const sandbox={URLSearchParams,Intl,Date:ClockDate,AbortController,console:{warn(){},log(){}},performance:{now:()=>elapsed},
    location:{hash:options.hash||"#lat=10&lon=10&tz=UTC&method=2"},
    setTimeout:(fn,ms=0)=>{const id=++serial;timers.set(id,{at:elapsed+Number(ms),fn});return id;},clearTimeout:id=>timers.delete(id),
    requestAnimationFrame:fn=>{const id=++serial;frames.set(id,fn);return id;},cancelAnimationFrame:id=>frames.delete(id),
    document:{visibilityState:"visible",querySelector:node,querySelectorAll:()=>[],addEventListener:(name,fn)=>events.set(name,fn)},
    localStorage:{getItem:k=>storage.get(k)??null,setItem:(key,value)=>{storage.set(key,value);writes.push({key,value,at:elapsed});}},
    fetch:(url,init={})=>{const headers=deferred(),body=deferred(),req={url,init,headers,body,at:elapsed};requests.push(req);
      req.ok=(data)=>{headers.resolve({ok:true,status:200,json:()=>body.promise});body.resolve({code:200,status:"OK",data:copy(data)});};
      req.fail=()=>headers.reject(new Error("offline fixture"));
      if(options.offline)req.fail();return headers.promise;
    }
  };sandbox.window=sandbox;context=vm.createContext(sandbox);
  run(config);
  run(slice('"use strict";',"// ---- weather (Open-Meteo:")+"\n"+
    "let weather=null,weatherTrack=null,weatherRadar=null,lastWxAt=0,lastWxTry=0,lastRadarAt=0,wxBusy=false,radarBusy=false;\n"+
    "let _starsProjected=false,_cloudDirty=false;const moonSky={_min:-1};\n"+
    "function loadWx(){} function fetchWeather(){} function fetchRadar(){} function syncWeather(){}\n"+
    "function buildStars(){} function buildWeather(){} function renderMoon(){} function projectStars(){} function fitCn(){} function applyTheme(){}\n"+
    "function moonNow(){return {phase:0.5};} function phaseEmoji(){return 'moon';} function moonGeometryObservation(){return {fresh:true};} function paintClouds(){} function tieRainToClouds(){} function updateSimClock(){}\n"+
    "function enableSettingsAffordance(){} function openSettings(){}\n"+
    slice("// ---- state ----","// ---- continuous time-of-day sky")+"\n"+
    slice("function solarElevationDeg(M,a){","function sunAltAt(M,a){")+"\n"+
    slice("let _lastBolt=-1, _lastRender=null;","function updateSimClock(n){")+"\n"+
    slice("let _loopStarted=false;","// ——————————————————————— in-widget settings"));
  async function advance(to){assert.ok(to>=elapsed);let budget=0;while(true){await settle();const next=[...timers].filter(([,t])=>t.at<=to).sort((a,b)=>a[1].at-b[1].at)[0];if(!next)break;if(++budget>200)throw Error("fixture timer bound");const [id,t]=next;timers.delete(id);const at=Math.max(elapsed,t.at);wall+=at-elapsed;elapsed=at;t.fn();}wall+=to-elapsed;elapsed=to;await settle();}
  async function frame(){const pending=[...frames];frames.clear();for(const [,fn]of pending)fn(elapsed);await settle();}
  return {run,state,storage,writes,requests,paints,errors,nodes,timers,frames,advance,frame,settle,
    wallBy:ms=>{wall+=ms;},elapse:ms=>{elapsed+=ms;wall+=ms;},elapsed:()=>elapsed,
    hide:()=>{sandbox.document.visibilityState="hidden";events.get("visibilitychange")?.();},
    show:()=>{sandbox.document.visibilityState="visible";events.get("visibilitychange")?.();},
    seed:(current,next=null)=>{sandbox.fixtureCurrent=copy(current);sandbox.fixtureNext=next&&copy(next);run("today=fixtureCurrent;tomorrow=fixtureNext;lastDate=today.date.gregorian.date;tz=today.meta.timezone;");},
    apply:cfg=>{sandbox.fixtureConfig=cfg;return run("applyConfig(fixtureConfig,{save:false})");},
    boot:()=>run("boot()")};
}
function cfg(lat,label=String(lat),extra={}){return {lat,lon:lat,tz:"UTC",label,method:"2",school:"0",time:"24",units:"f",datefmt:"YYYY-MM-DD",source:"manual",...extra};}
function req(h,day="07-09-2026",lat=null){return h.requests.find(r=>r.url.includes(`/timings/${day}?`)&&(lat===null||new URL(r.url).searchParams.get("latitude")===String(lat)));}


module.exports={source,sourcePath,copy,record,harness,cfg,req,settle};
