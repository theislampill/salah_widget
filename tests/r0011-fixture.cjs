"use strict";
// Actual config resolution, boot, applyConfig and settings source. Provider and
// renderer lifecycle doubles contain no owner storage, GPS or network effects.
// DOM/event scheduling here is supplementary to the parent's native bridge.
const {environment,readSource,deferred,drain}=require("./r000f-fixture.cjs");
function widget(options={}) {
  const f=environment(), page=readSource("index.html",options.ref);
  const cardTag=page.match(/<div class="c(?:\s[^"]*)?"[^>]*>/);if(!cardTag)throw Error("card source tag missing");f.initializeTag(f.card,cardTag[0]);
  for(const cls of ["mphoto","moon-mask-disc"]){const tag=page.match(new RegExp('<[^>]+class="'+cls+'"[^>]*>'));if(tag)f.initializeTag(f.el(cls),tag[0]);}
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
  for(const id of ["set-lat","set-lon","set-label","set-method","set-school","set-time","set-units","set-appearance","set-datefmt","set-datefmt-preset","setClose","set-pin","set-reset","set-status","settings-persistence-status"]){const e=f.el(id);e.eventParent=panel;panel.children.push(e);}
  const start=page.indexOf("const q = new URLSearchParams(location.hash.slice(1));"), end=page.indexOf("// ---- simulation overrides",start);
  if(start<0 || end<start)throw new Error("resolution source boundary missing");
  f.run(page.slice(start,end));
  Object.assign(f.sandbox,{
    QA:false, buildStars:()=>calls.stars++, buildWeather:()=>calls.buildWeather++,renderMoon:()=>{},
    startWeather:()=>calls.weather++,
    loadPrayerData:()=>queue("prayer",{}),startRenderLoop:()=>calls.loop++,
    render:()=>calls.render++,showError:msg=>calls.errors.push(msg)
  });
  // Execute the widget's selector and lifecycle closure in a pristine realm;
  // builder's $ selector accepts IDs and must not stand in for widget CSS lookup.
  // Only providers and pixel/catalog builders above are explicit scope doubles.
  if(new URLSearchParams(f.sandbox.location.hash.slice(1)).has("simTime"))throw new Error("explicit simulation belongs to CLOCK fixture");
  const load=source=>f.run(options.mutate?options.mutate(source):source);
  function helper(name){const start=page.indexOf("function "+name+"("),end=page.indexOf("\n}",start);if(start<0||end<start)throw new Error(name+" source boundary missing");return page.slice(start,end+2);}
  function declaration(pattern){const match=page.match(pattern);if(!match)throw Error(pattern+" declaration source boundary missing");const end=page.indexOf(";",match.index);if(end<0)throw Error("declaration terminator missing");return page.slice(match.index,end+1).trim();}
  load(declaration(/^const \$\s*=/m));
  for(const pattern of [/^let today=/m,/^let weather=null/m,/^let weatherTrack=null/m,/^let weatherRadar=null/m,/^let _prayerStale=/m])load(declaration(pattern));
  if(/^let _renderDirty=/m.test(page))load(declaration(/^let _renderDirty=/m));
  if(page.includes("function beginSkyScene(")){
    for(const pattern of [/^let _skySceneKey=/m,/^let _starEls=/m,/^let _mAlb=/m,/^let _pbrFailed=/m,/^let _cloudReady=/m,/^let cloudState=/m,/^let _cloudCv=/m])load(declaration(pattern));
    load(helper("updateSkySurface"));load(helper("beginSkyScene"));
  }else if(/^let _starEls=/m.test(page))load(declaration(/^let _starEls=/m));
  if(page.includes("function simulationReady()")){
    f.sandbox.SIM={time:null};f.run("const _simHidden=new Map(); let _simClockDisplay=null;");load(helper("simulationReady"));
  }
  if(page.includes("function buildSceneOnce()")){load(declaration(/^let _sceneBuilt=/m));load(helper("buildSceneOnce"));}
  if(page.includes("beginRuntimeGeneration();")){
    const first=page.indexOf("function cacheKey()"),last=page.indexOf("function readPrayerCache(",first);if(first<0||last<first)throw Error("request lifecycle source boundary missing");
    f.sandbox.AbortController=AbortController;load(declaration(/^const _RAFNOW\s*=/m));load(declaration(/^const _prayerCooldown=/m));load(page.slice(first,last));
  }
  load(helper("resetForNewLocation"));
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
