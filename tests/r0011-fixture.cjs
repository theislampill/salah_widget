"use strict";
// Actual config resolution, boot, applyConfig and settings source. Provider and
// renderer lifecycle doubles contain no owner storage, GPS or network effects.
// DOM/event scheduling here is supplementary to the parent's native bridge.
const {environment,readSource,deferred,drain}=require("./r000f-fixture.cjs");
const {nativeInlineRuntime,SetupError}=require("./native-inline-runtime.cjs");
function widget(options={}) {
  const f=environment(), page=options.source??readSource("index.html",options.ref),source=nativeInlineRuntime(page);
  const cardTag=page.match(/<div class="c(?:\s[^"]*)?"[^>]*>/);if(!cardTag)throw Error("card source tag missing");f.initializeTag(f.card,cardTag[0]);
  for(const cls of ["mphoto","moon-mask-disc"]){const tag=page.match(new RegExp('<[^>]+class="'+cls+'"[^>]*>'));if(tag)f.initializeTag(f.el(cls),tag[0]);}
  f.sandbox.location.hash=options.hash || "#local=1";
  const config=readSource("config.js",options.ref);
  f.run(options.configMutate?options.configMutate(config):config);
  let now=options.now ?? Date.now();
  f.sandbox.Date=class extends Date { constructor(...args){super(...(args.length?args:[now]));} static now(){return now;} };
  if(options.seed)f.sandbox.SalahConfig.saveLocal(options.seed);
  const calls={coarse:[],gps:[],search:[],prayer:[],weather:0,weatherFetch:0,radarFetch:0,render:0,loop:0,stars:0,buildWeather:0,errors:[]};
  function queue(name,args){const d=deferred();calls[name].push({...d,args});return d.promise;}
  if(!options.realCoarse)f.sandbox.SalahConfig.coarseDetect=(...args)=>queue("coarse",args);
  f.sandbox.SalahConfig.geocodeSearch=(...args)=>queue("search",args);
  f.sandbox.navigator.geolocation={getCurrentPosition:(ok,bad,opts)=>{queue("gps",opts).then(ok,bad);}};
  f.sandbox.SalahConfig.permissionState=()=>Promise.resolve("granted");
  if(options.moduleMissing)delete f.sandbox.SalahConfig;
  const panel=f.el("settings");
  for(const id of ["set-lat","set-lon","set-label","set-method","set-school","set-time","set-units","set-appearance","set-datefmt","set-datefmt-preset","setClose","set-pin","set-reset","set-status","settings-persistence-status"]){const e=f.el(id);e.eventParent=panel;panel.children.push(e);}
  const start=source.indexOf("const q = new URLSearchParams(location.hash.slice(1));"), end=source.indexOf("// ---- simulation overrides",start);
  if(start<0 || end<start)throw new SetupError("resolution source boundary missing");
  f.run(source.slice(start,end));
  Object.assign(f.sandbox,{
    QA:false, buildStars:()=>calls.stars++, buildWeather:()=>calls.buildWeather++,renderMoon:()=>{},
    startWeather:()=>calls.weather++,fetchWeather:()=>calls.weatherFetch++,fetchRadar:()=>calls.radarFetch++,
    // Explicit UI/condition boundary doubles; storage and config remain actual source.
    withdrawPrayerPresentation(){}, weatherDecision:()=>({record:null}), weatherHeader:()=>({}), paintWeatherHeader(){},
    loadPrayerData:()=>queue("prayer",{}),startRenderLoop:()=>calls.loop++,
    render:()=>calls.render++,showError:msg=>calls.errors.push(msg)
  });
  // Execute the widget's selector and lifecycle closure in a pristine realm;
  // builder's $ selector accepts IDs and must not stand in for widget CSS lookup.
  // Only providers and pixel/catalog builders above are explicit scope doubles.
  if(new URLSearchParams(f.sandbox.location.hash.slice(1)).has("simTime"))throw new Error("explicit simulation belongs to CLOCK fixture");
  const load=source=>f.run(options.mutate?options.mutate(source):source);
  function unique(pattern,label){
    const matches=[...source.matchAll(new RegExp(pattern.source,pattern.flags.replace('g','')+'g'))];
    if(matches.length!==1)throw new SetupError(label+" source boundary missing or ambiguous");return matches[0];
  }
  function helper(name){const match=unique(new RegExp('^function '+name+'\\(','m'),name),end=source.indexOf("\n}",match.index);if(end<0)throw new SetupError(name+" source boundary missing");return source.slice(match.index,end+2);}
  function declaration(pattern){const match=unique(pattern,String(pattern)),end=source.indexOf(";",match.index);if(end<0)throw new SetupError("declaration terminator missing");return source.slice(match.index,end+1).trim();}
  load(declaration(/^const \$\s*=/m));
  for(const pattern of [/^let today=/m,/^let weather=null/m,/^let weatherTrack=null/m,/^let weatherRadar=null/m,/^let _prayerStale=/m])load(declaration(pattern));
  if(/^let _renderDirty=/m.test(source))load(declaration(/^let _renderDirty=/m));
  if(source.includes("function beginSkyScene(")){
    for(const pattern of [/^let _skySceneKey=/m,/^let _starEls=/m,/^let _mAlb=/m,/^let _pbrFailed=/m,/^let _cloudReady=/m,/^let cloudState=/m,/^let _cloudCv=/m])load(declaration(pattern));
    load(helper("updateSkySurface"));load(helper("beginSkyScene"));
  }else if(/^let _starEls=/m.test(source))load(declaration(/^let _starEls=/m));
  if(source.includes("_skyInitialDocument")){
    load(declaration(/^let _skyInitialDocument=/m));
    load(unique(/^function finishInitialSkyDocument\(\)\{[^\n]+\}$/m,'finishInitialSkyDocument')[0]);
  }
  if(source.includes("function simulationReady()")){
    f.sandbox.SIM={time:null};f.run("const _simHidden=new Map(); let _simClockDisplay=null;");load(helper("simulationReady"));
  }
  if(source.includes("function buildSceneOnce()")){load(declaration(/^let _sceneBuilt=/m));load(helper("buildSceneOnce"));}
  if(source.includes("beginRuntimeGeneration();")){
    const first=source.indexOf("function cacheKey()"),last=source.indexOf("function readPrayerCache(",first);if(first<0||last<first)throw new SetupError("request lifecycle source boundary missing");
    f.sandbox.AbortController=AbortController;load(declaration(/^const _RAFNOW\s*=/m));load(declaration(/^const _prayerCooldown=/m));load(source.slice(first,last));
  }
  if(source.includes("function withdrawCloudState(")){
    // beginSkyScene revokes the cloud publication through the actual R000B
    // owners. Load those owners and the exact target/scene/mode identities they
    // read; the weather decision itself stays the explicit boundary double above.
    function region(start,end){const a=source.indexOf(start),b=source.indexOf(end,a);if(a<0||b<a)throw new SetupError(start+" source boundary missing");return source.slice(a,b);}
    if(!/^const _RAFNOW\s*=/m.test(source)||!source.includes("beginRuntimeGeneration();"))throw new SetupError("cloud publication clock boundary missing");
    for(const pattern of [/^const _tsParam=/m,/^let TIMESCALE =/m,/^let ADVANCING =/m,/^let FOLLOW_WALL_CLOCK =/m,/^let _clockPreview=/m,/^let _rafT0=/m])load(declaration(pattern));
    load(helper("simNow"));load(helper("skySceneIdentity"));
    load(region("function wxNumber(","\nfunction wxValue("));
    load(region("function captureWeatherTarget(","\nfunction loadWx("));
    load(region("// A receipt of what the cloud consumer published","// Pure final-publication fence."));
  }
  load(helper("resetForNewLocation"));
  const applyStart=source.indexOf("async function applyConfig("), bootStart=source.indexOf("async function boot(){",applyStart), bootEnd=source.indexOf("// SINGLE rAF render clock",bootStart);
  if(applyStart<0 || bootStart<applyStart || bootEnd<bootStart)throw new SetupError("apply/boot source boundary missing");
  let runtime=source.slice(applyStart,bootEnd);
  if(options.mutate)runtime=options.mutate(runtime);
  f.run(runtime);
  const settingsStart=source.indexOf("function enableSettingsAffordance(){"), settingsEnd=source.lastIndexOf("\nboot();");
  if(settingsStart<0 || settingsEnd<settingsStart)throw new SetupError("settings source boundary missing");
  let settings=source.slice(settingsStart,settingsEnd);
  if(options.mutate)settings=options.mutate(settings);
  f.run(settings);
  if(options.open!==false){ f.run('_cfgMode="local"; _enableSettingsAffordance(); _openSettings();'); }
  return {...f,page,calls,now:value=>{now=value;},json:expression=>JSON.parse(f.run("JSON.stringify("+expression+")")),
    config:()=>JSON.parse(f.run("JSON.stringify(CONFIG)")), boot:()=>f.run("boot()"),
    resolveCall:async(name,index,value)=>{calls[name][index].resolve(value);await drain();}};
}
module.exports={widget,deferred,drain};
