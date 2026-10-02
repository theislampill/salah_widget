"use strict";
// Actual config resolution, boot, applyConfig and settings source. Provider and
// renderer lifecycle doubles contain no owner storage, GPS or network effects.
// DOM/event scheduling here is supplementary to the parent's native bridge.
const {fixture,readSource,deferred,drain}=require("./r000f-fixture.cjs");
function widget(options={}) {
  const f=fixture("builder",{ref:options.ref}), page=readSource("index.html",options.ref);
  f.buckle.querySelector=selector=>selector===".gear"?f.buckle.children.find(c=>c.className==="gear"||c.classList.contains("gear"))||null:null;
  f.sandbox.location.hash=options.hash || "#local=1";
  const config=readSource("config.js",options.ref);
  f.run(options.configMutate?options.configMutate(config):config);
  let now=options.now ?? Date.now();
  f.sandbox.Date=class extends Date { constructor(...args){super(...(args.length?args:[now]));} static now(){return now;} };
  if(options.seed)f.sandbox.SalahConfig.saveLocal(options.seed);
  const calls={coarse:[],gps:[],search:[],prayer:[],weather:0,render:0,loop:0,stars:0,buildWeather:0,errors:[]};
  function queue(name,args){const d=deferred();calls[name].push({...d,args});return d.promise;}
  if(!options.realCoarse)f.sandbox.SalahConfig.coarseDetect=(...args)=>queue("coarse",args);
  f.sandbox.SalahConfig.geocodeSearch=(...args)=>queue("search",args);
  f.sandbox.navigator.geolocation={getCurrentPosition:(ok,bad,opts)=>{queue("gps",opts).then(ok,bad);}};
  f.sandbox.SalahConfig.permissionState=()=>Promise.resolve("granted");
  if(options.moduleMissing)delete f.sandbox.SalahConfig;
  const panel=f.el("settings");
  for(const id of ["set-lat","set-lon","set-label","set-method","set-school","set-time","set-units","set-datefmt","set-datefmt-preset","setClose","set-pin","set-reset","set-status","settings-persistence-status"]){const e=f.el(id);e.eventParent=panel;panel.children.push(e);}
  const start=page.indexOf("const q = new URLSearchParams(location.hash.slice(1));"), end=page.indexOf("// ---- simulation overrides",start);
  if(start<0 || end<start)throw new Error("resolution source boundary missing");
  f.run(page.slice(start,end));
  Object.assign(f.sandbox,{
    QA:false, buildStars:()=>calls.stars++, buildWeather:()=>calls.buildWeather++,renderMoon:()=>{},
    resetForNewLocation:()=>{},startWeather:()=>calls.weather++,
    loadPrayerData:()=>queue("prayer",{}),startRenderLoop:()=>calls.loop++,
    render:()=>calls.render++,showError:msg=>calls.errors.push(msg)
  });
  const applyStart=page.indexOf("async function applyConfig("), bootStart=page.indexOf("async function boot(){",applyStart), bootEnd=page.indexOf("// SINGLE rAF render clock",bootStart);
  if(applyStart<0 || bootStart<applyStart || bootEnd<bootStart)throw new Error("apply/boot source boundary missing");
  let runtime=page.slice(applyStart,bootEnd);
  if(options.mutate)runtime=options.mutate(runtime);
  f.run(runtime);
  const settingsStart=page.indexOf("function enableSettingsAffordance(){"), settingsEnd=page.lastIndexOf("\nboot();");
  if(settingsStart<0 || settingsEnd<settingsStart)throw new Error("settings source boundary missing");
  let settings=page.slice(settingsStart,settingsEnd);
  if(options.mutate)settings=options.mutate(settings);
  f.run(settings);
  if(options.open!==false){ f.run('_cfgMode="local"; _enableSettingsAffordance(); _openSettings();'); }
  return {...f,page,calls,now:value=>{now=value;},json:expression=>JSON.parse(f.run("JSON.stringify("+expression+")")),
    config:()=>JSON.parse(f.run("JSON.stringify(CONFIG)")), boot:()=>f.run("boot()"),
    resolveCall:async(name,index,value)=>{calls[name][index].resolve(value);await drain();}};
}
module.exports={widget,deferred,drain};
