'use strict';
// Disposable date fixtures; font cases bind the actual native runtime inventory.
// This module never launches a browser or changes source.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function unique(source,anchor,label){if(source.split(anchor).length!==2)throw Error('Expected unique '+label+' anchor');}
const SCRIPT_LAYOUTS={
  legacy:{sourceSha256:'51c09cfdd0bb535018ba76c02878c7bb8574b82a957de0c62392ed379f4834ef',nativeOrdinal:2,scripts:[
    [' src="config.js"','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',0],
    [' id="native-first-paint-code" data-sha256="41f1bffb47c6ce03664506179394d409778460cdcf806d59a8ab90bc96e16ad6"','41f1bffb47c6ce03664506179394d409778460cdcf806d59a8ab90bc96e16ad6',0],
    ['','6f8bc6bfb22794a8a954fc8b0214a0c045fc17f51f891b7e36fe77cafe714862',1],
    [' src="real-sky/native-sky.js"','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',0]]},
  combined_r1r2_01:{sourceSha256:'420dfd6467c52b977a8ea93df0b3cd58fbafa00c7f78b676a5fd7abab27e9234',nativeOrdinal:3,scripts:[
    [' src="config.js"','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',0],
    [' id="native-first-paint-code" data-sha256="f133e73fd3f760c53a5988b5b229403f6cec32109460a650dbb3296ee5437554"','f133e73fd3f760c53a5988b5b229403f6cec32109460a650dbb3296ee5437554',0],
    [' id="moon-initial-code"','0f6289cc4a3cc762288e3c13254beae7f78c02a0039639f6dd9cbf08a050f3a7',0],
    ['','a36585ace0ba7b223cafae72de14277f9b8c8874df53147eb03c08352243c8f2',1],
    [' id="moon-refinement-code"','7c08099b69b6aaaa635c9793415ca0aa59a89909155acbdc40d21693370ff580',0],
    [' src="real-sky/native-sky.js"','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',0]]},
  combined_r1r2_02:{sourceSha256:'90a8429c77fce50425b6e8effca7d7e7b6a210d25110394c72e2a074d0465b83',nativeOrdinal:3,scripts:[
    [' src="config.js"','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',0],
    [' id="native-first-paint-code" data-sha256="127aec1eee1a73ce5eb168fa771a90852ae60daf89ba6e8626f4466392d2820d"','127aec1eee1a73ce5eb168fa771a90852ae60daf89ba6e8626f4466392d2820d',0],
    [' id="moon-initial-code"','f2a05231133f2847f4fd1b10dcf36f3161bb60ce6714a59d83e8484b4ee6a7cc',0],
    ['','a36585ace0ba7b223cafae72de14277f9b8c8874df53147eb03c08352243c8f2',1],
    [' id="moon-refinement-code"','7c08099b69b6aaaa635c9793415ca0aa59a89909155acbdc40d21693370ff580',0],
    [' src="real-sky/native-sky.js"','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',0]]}
};
function strictNativeRuntime(source){
  const all=Array.from(source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g));
  const split=all.some(m=>/id="moon-(?:initial|refinement)-code"/.test(m[1]));
  const layoutId=split?(all.some(m=>m[1]===SCRIPT_LAYOUTS.combined_r1r2_02.scripts[1][0])?'combined_r1r2_02':'combined_r1r2_01'):'legacy',profile=SCRIPT_LAYOUTS[layoutId];
  if(all.length!==profile.scripts.length)throw Error('Expected exactly '+profile.scripts.length+' actual script elements for '+layoutId);
  for(let i=0;i<all.length;i++){
    const [attrs,digest,bootCount]=profile.scripts[i],m=all[i];
    if(m[1]!==attrs)throw Error('Script role/order/attributes drift at '+i+' for '+layoutId);
    if(sha(m[2])!==digest)throw Error('Script digest drift at '+i+' for '+layoutId);
    if(m[2].split('\nboot();').length-1!==bootCount)throw Error('Script boot-owner count drift at '+i+' for '+layoutId);
  }
  if(sha(source)!==profile.sourceSha256)throw Error('Whole source identity has no sealed script-layout admission');
  return {native:all[profile.nativeOrdinal][2],layoutId,sourceSha256:profile.sourceSha256,scripts:all.map((m,i)=>({ordinal:i,attrs:m[1],sha256:sha(m[2]),bytes:Buffer.byteLength(m[2]),bootCount:m[2].split('\nboot();').length-1}))};
}
function record(root,day,ah,zone='UTC',wall=false,lat=24.47,lon=39.61,method='4'){
  const original=require(path.join(root,'tests/r0009-calendar-harness.cjs')).record;
  const r=original(day.slice(0,2),ah);const [d,mo,y]=day.split('-').map(Number);
  r.date.gregorian={date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:mo===3?'March':mo===11?'November':'September'},year:String(y)};
  r.meta={...r.meta,latitude:lat,longitude:lon,timezone:zone,method:{id:Number(method)}};
  if(wall)Object.assign(r.timings,{Asr:'15:30',Isha:'19:30'});
  return r;
}
const implemented={wall:['prayer','promotion','held','back-late','retry','visibility','modes'],
  timezone:['scenes','recovery','capture','track','modes','profiles'],
  access:['keyboard','touch','presets','long','font','transitions','effects','builder']};
function plan(root,suite,name,variant='default'){
  if(!implemented[suite]?.includes(name))throw Error('Unknown native case '+suite+'/'+name);
  const p={suite,name,variant,clock:'2026-09-07T17:59:59Z',mono:0,zone:'UTC',lat:24.47,lon:39.61,
    method:'4',units:'f',format:'YYYY-MM-DD',simWx:'0',records:{},hold:[],initialPolicies:{},countResolver:false,originalCase:null};
  if(suite==='wall'){
    p.clock=name==='prayer'?'2026-09-07T15:29:59Z':name==='retry'?'2026-09-07T12:00:00Z':name==='back-late'?'2026-09-08T00:00:01Z':'2026-09-07T23:59:59Z';
    for(const [day,ah]of [['07','19'],['08','20'],['09','21']])p.records[day+'-09-2026']=record(root,day+'-09-2026',ah,'UTC',true);
    if(name==='back-late'){
      p.clock=variant==='prefetch8-back7'?'2026-09-07T23:59:59Z':'2026-09-08T00:00:01Z';
      p.hold=variant==='prefetch9-back7'?['prayer:09-09-2026']:['prayer:08-09-2026'];
    }
    if(name==='retry')p.initialPolicies['prayer:07-09-2026']='reject';
    if(name==='modes'){p.clock='2026-09-07T12:00:00Z';p.clockQuery=variant==='frozen'?'simTime=03:30':variant==='sim1'?'simTime=03:30&timeScale=1':variant==='sim60'?'simTime=03:30&timeScale=60':variant==='scale1'?'timeScale=1':variant==='scale60'?'timeScale=60':'';}
  }else if(suite==='timezone'){
    p.zone='America/New_York';p.lat=40.7128;p.lon=-74.006;p.method='2';p.units='c';
    p.clock=['capture','track'].includes(name)?'2026-03-08T07:35:00Z':'2026-03-08T12:00:00Z';
    if(variant.startsWith('fold'))p.clock=name==='track'?'2026-11-01T08:35:00Z':'2026-11-01T12:00:00Z';
    const day=p.clock.slice(0,10).split('-').reverse().join('-'),next=day.startsWith('08')?'09-03-2026':'02-11-2026';
    p.records[day]=record(root,day,'01',p.zone,true,p.lat,p.lon,p.method);p.records[next]=record(root,next,'02',p.zone,true,p.lat,p.lon,p.method);
    if(name==='scenes'||name==='recovery')p.clockQuery='simTime='+(variant==='gap'?'02:30':variant==='fold-invalid'?'01:30':'03:30');
    if(name==='modes'){p.zone='UTC';p.clockQuery=variant==='ordinary'?'':'simTime=03:30'+(variant==='scale1'?'&timeScale=1':variant==='scale60'?'&timeScale=60':'');for(const r of Object.values(p.records))r.meta.timezone='UTC';}
    if(name==='capture'){p.simWx=null;p.hold=['weather','prayer:'+day];}
    if(name==='capture'&&variant==='ignored-zone-mutant')p.mutant='ignored-explicit-zone';
    if(name==='recovery'&&variant==='provider-zone'){p.zone='UTC';p.clockQuery='simTime=02:30';p.hold=['prayer:'+day];for(const r of Object.values(p.records))r.meta.timezone='UTC';}
    if(name==='track'){p.simWx=null;p.hold=[];}
    if(name==='profiles'){
      p.simWx=null;p.countResolver=variant!=='uninstrumented';
      for(const [index,day]of ['08','09','10','11','12','13'].entries())p.records[day+'-03-2026']=record(root,day+'-03-2026',String(index+1).padStart(2,'0'),p.zone,true,p.lat,p.lon,p.method);
    }
    const date=p.clock.slice(0,10),time=date+'T03:30';
    let times=[time,date+'T04:30'];
    if(variant==='gap')times=[date+'T02:30',time];
    if(variant==='fold-invalid')times=[date+'T01:30',time];
    if(variant==='duplicate')times=[time,time];
    if(variant==='decreasing')times=[date+'T04:30',time];
    p.weather={timezone:p.zone,elevation:10,current_units:{temperature_2m:'°C'},hourly_units:{temperature_2m:'°C'},
      current:{time:variant==='invalid-current'?date+'T02:30':time,interval:900,weather_code:0,temperature_2m:20,
        apparent_temperature:20,relative_humidity_2m:50,dew_point_2m:10,wind_speed_10m:1,wind_direction_10m:0,
        wind_gusts_10m:2,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,precipitation:0,rain:0,showers:0,snowfall:0,visibility:20000,is_day:1},
      hourly:{time:times,temperature_2m:[20,21],weather_code:[0,0]}};
  }else{
    const exported=require(path.join(root,'tests/r0009-browser-fixture.cjs'));
    const selected=name==='presets'?(variant==='default'?'long':variant):name==='long'?(variant==='unescaped-control'?'literal':variant==='default'?'very-long':variant):name==='font'?'long':name==='touch'?'long-month':name==='transitions'?'late':'before';
    if(name==='long'&&variant==='unescaped-control')p.mutant='unescaped-date-value';
    if(!exported.cases.includes(selected))throw Error('Unknown original calendar case '+selected);
    const original=exported.spec(selected);p.originalCase=selected;p.clock=original.clock;p.zone=original.zone;p.format=original.format;p.saved=original.saved;
    p.records[original.today.date.gregorian.date]=original.today;p.records[original.tomorrow.date.gregorian.date]=original.tomorrow;
    if(name==='transitions'){
      p.clock='2026-09-07T17:59:59Z';p.records['09-09-2026']=record(root,'09-09-2026','21');p.records['10-09-2026']=record(root,'10-09-2026','22');
    }
    if(name==='font'){
      // The longest ordinary current-prayer label is reached through the actual model.
      p.clock=variant.includes('sunrise')?'2026-09-07T06:05:00Z':variant.includes('maghrib')?'2026-09-07T18:01:00Z':'2026-09-07T09:30:00Z';
      p.zone='UTC';p.format='DD MMMM YYYY';p.records={
        '07-09-2026':record(root,'07-09-2026','19'),
        '08-09-2026':record(root,'08-09-2026','20')};
    }
    if(original.holdTomorrow)p.hold=['prayer:'+original.tomorrow.date.gregorian.date];
    if(original.injectedNext||original.stale)p.selectorOnly={injectedNext:original.injectedNext,stale:original.stale};
  }
  const q=new URLSearchParams({lat:String(p.lat),lon:String(p.lon),label:'Madinah',method:p.method,school:'0',tz:p.zone,time:'24',datefmt:p.format,units:p.units,motion:'full'});
  if(p.simWx!=null)q.set('simWx',p.simWx);
  if(p.saved){q.delete('datefmt');q.set('local','1');}
  if(name==='held'||name==='recovery')q.set('preferLocal','1');
  if(p.clockQuery)for(const [k,v]of new URLSearchParams(p.clockQuery))q.set(k,v);
  p.hash='#'+q.toString();return p;
}
function installPreScript(fixture){
  const NativeDate=Date,nativeNow=performance.now.bind(performance),nativeRAF=requestAnimationFrame.bind(window),nativeCancel=cancelAnimationFrame.bind(window);
  const nativeTimeout=setTimeout.bind(window),nativeClear=clearTimeout.bind(window);
  const nativeFetch=fixture.runtimePaths?window.fetch.bind(window):null,runtimePaths=new Set(fixture.runtimePaths||[]);
  let wall=NativeDate.parse(fixture.clock),mono=fixture.mono;
  const trace=[],frames=[],active=new Map(),timers=[],activeTimers=new Map(),inputEvents=[],storage=new Map(),effects=[],requests=[],hold=new Set(fixture.hold),policies=new Map(Object.entries(fixture.initialPolicies||{}));
  const stamp=event=>({event,wall,mono,nativePerformance:nativeNow()});
  window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[wall]));}static now(){return wall;}};
  Object.defineProperty(performance,'now',{configurable:true,value:()=>mono});
  Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem(k){k=String(k);effects.push({...stamp('get'),key:k});return storage.get(k)??null;},setItem(k,v){k=String(k);v=String(v);effects.push({...stamp('set'),key:k,value:v});storage.set(k,v);},removeItem(k){k=String(k);effects.push({...stamp('remove'),key:k});storage.delete(k);},clear(){throw Error('Fixture forbids storage.clear');}}});
  if(fixture.saved)storage.set('salah_widget:config:v1',JSON.stringify({v:1,lat:fixture.lat,lon:fixture.lon,tz:fixture.zone,label:'Madinah',method:fixture.method,school:'0',time:'24',datefmt:fixture.format,units:fixture.units,lp:0,source:'manual',savedAt:wall}));
  window.requestAnimationFrame=function(callback){let id;id=nativeRAF(t=>{active.delete(id);frames.push({...stamp('fired'),id,name:callback.name,t});callback(t);});active.set(id,callback.name);frames.push({...stamp('requested'),id,name:callback.name});return id;};
  window.cancelAnimationFrame=function(id){active.delete(id);frames.push({...stamp('cancelled'),id});nativeCancel(id);};
  window.setTimeout=function(callback,ms=0,...args){let id;const delay=Number(ms)||0;id=nativeTimeout(()=>{activeTimers.delete(id);timers.push({...stamp('fired'),id,ms:delay});callback(...args);},delay);activeTimers.set(id,delay);timers.push({...stamp('requested'),id,ms:delay});return id;};
  window.clearTimeout=function(id){activeTimers.delete(id);timers.push({...stamp('cancelled'),id});nativeClear(id);};
  if(typeof document.addEventListener==='function')for(const type of ['keydown','pointerdown','touchstart','focusin','wheel'])document.addEventListener(type,event=>inputEvents.push({...stamp(type),trusted:event.isTrusted,target:event.target?.id||event.target?.tagName,key:event.key||null}),{capture:true,passive:true});
  const resolverCounts={constructs:0,projections:0};
  const fitMeasurements=[];
  if(typeof CanvasRenderingContext2D!=='undefined'){
    const actualMeasure=CanvasRenderingContext2D.prototype.measureText;
    CanvasRenderingContext2D.prototype.measureText=function(...args){const value=actualMeasure.apply(this,args);if(window.__rlgwo?.fitScope)fitMeasurements.push({...stamp('fit-measureText'),text:String(args[0]),font:this.font,width:value.width,ascent:value.actualBoundingBoxAscent,descent:value.actualBoundingBoxDescent});return value;};
  }
  if(fixture.countResolver){const Original=Intl.DateTimeFormat;function Counted(...args){const f=new Original(...args),opts=args[1]||{};if(opts.calendar==='gregory'&&opts.numberingSystem==='latn'&&opts.hourCycle==='h23'){resolverCounts.constructs++;const original=f.formatToParts.bind(f);Object.defineProperty(f,'formatToParts',{value(...inputs){resolverCounts.projections++;return original(...inputs);}});}return f;}Object.setPrototypeOf(Counted,Original);Counted.prototype=Original.prototype;Intl.DateTimeFormat=Counted;}
  function request(input,init={}){
    const url=new URL(typeof input==='string'?input:input.url,location.href);
    const nativeRuntime=!!nativeFetch&&url.origin===location.origin&&runtimePaths.has(url.pathname.slice(1));
    const kind=nativeRuntime?'native-runtime':url.origin==='https://api.aladhan.com'?'prayer':url.origin==='https://api.open-meteo.com'?'weather':'optional';
    const day=kind==='prayer'?url.pathname.split('/').pop():null,key=kind==='prayer'?'prayer:'+day:kind;
    const row={...stamp('requested'),id:requests.length+1,url:url.href,kind,day,key,owner:window.__rlgwo?.ownerForSignal?.(init.signal)||null,settled:false,bodyRead:false,aborted:false};requests.push(row);
    if(init.signal)init.signal.addEventListener('abort',()=>{row.aborted=true;trace.push({...stamp('aborted'),id:row.id});});
    if(nativeRuntime){row.scope='Font-only native same-origin exact runtime_identity file';return nativeFetch(input,init).then(response=>{row.settled=true;row.status=response.status;trace.push({...stamp('native-runtime-response'),id:row.id,status:response.status});return response;},error=>{row.settled=true;row.error=String(error);throw error;});}
    if(kind==='optional'){row.settled=true;row.status=503;return Promise.resolve(new Response('Explicit date-only optional transport unavailable',{status:503}));}
    if(kind==='weather'&&!fixture.weather){row.settled=true;row.status=503;row.scope='Declared unused weather transport in date-only builder/input lane';return Promise.resolve(new Response('Explicit date-only current weather unavailable',{status:503}));}
    const payload=kind==='weather'?fixture.weather:fixture.records[day];
    if(!payload){row.settled=true;row.error='unconfigured input';return Promise.reject(Error('Fixture request input not configured '+key));}
    const action=policies.get(key)|| (hold.has(key)?'hold':'release');
    if(action==='reject'){row.settled=true;row.error='declared rejected transport';trace.push({...stamp('fetch-rejected'),id:row.id});return Promise.reject(Error('Declared synthetic transport failure'));}
    let release,reject;const body=new Promise((a,b)=>{release=a;reject=b;});
    row.release=function(value){if(row.settled)throw Error('Body already settled '+row.id);row.settled=true;trace.push({...stamp('body-released'),id:row.id,key});release(kind==='prayer'?{code:200,status:'OK',data:value||payload}:value||payload);};
    row.reject=function(){if(row.settled)throw Error('Body already settled '+row.id);row.settled=true;reject(Error('Declared synthetic transport failure'));};
    if(action==='release')row.release();
    return Promise.resolve({ok:true,status:200,json(){row.bodyRead=true;trace.push({...stamp('json-entered'),id:row.id});return body.then(value=>new Response(JSON.stringify(value)).json());}});
  }
  window.fetch=request;window.__sw_sec_probe=0;
  window.__rlgwo={fixture,trace,frames,timers,inputEvents,fitMeasurements,storage,effects,requests,resolverCounts,
    clock:()=>({wall,mono,nativePerformance:nativeNow()}),setWall(value){const next=typeof value==='number'?value:NativeDate.parse(value);if(!Number.isFinite(next))throw Error('Invalid fixture wall');wall=next;trace.push(stamp('wall-set'));},
    setMono(value){if(!Number.isFinite(value)||value<mono)throw Error('Monotonic fixture cannot reverse');mono=value;trace.push(stamp('mono-set'));},
    policy(key,value){if(!['hold','release','reject'].includes(value))throw Error('Invalid body policy');policies.set(key,value);},
    release(id,value){const row=requests.find(x=>x.id===id);if(!row?.release)throw Error('No releasable body '+id);row.release(value);},
    reject(id){const row=requests.find(x=>x.id===id);if(!row?.reject)throw Error('No rejectable body '+id);row.reject();},
    waitFrames(n=2){return new Promise(resolve=>{function tick(){if(--n<=0)resolve();else nativeRAF(tick);}nativeRAF(tick);});},
    injectVisibility(value){if(!['hidden','visible'].includes(value))throw Error('Invalid visibility fixture input');Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>value});Object.defineProperty(document,'hidden',{configurable:true,get:()=>value==='hidden'});document.dispatchEvent(new Event('visibilitychange'));trace.push({...stamp('injected-visibility'),value,scope:'Controlled document properties/event; not native suspend.'});},
    activeFrames:()=>[...active.entries()],requestReadback:()=>requests.map(({release,reject,...r})=>({...r})),
    effectsReadback:()=>({effects:effects.map(r=>({...r})),requests:requests.map(({release,reject,...r})=>({...r})),storage:[...storage]})};
  trace.push({...stamp('pre-script-installed'),fontStatus:document.fonts?.status||'unsupported'});
}
function hooks(){return `
// Checked test-only observation. Actual boot/render/loader/classifier and native callbacks remain owners.
function rlgwoOp(op){return op?{generation:op.generation,operationId:op.operationId,kind:op.kind,requestedDay:op.requestedDay,requestZone:op.requestZone,cacheKey:op.cacheKey,prayerAttempts:op.prayerAttempts||0,attempt:op.attempt?{attemptId:op.attempt.attemptId,deadlineAt:op.attempt.deadlineAt,expired:op.attempt.expired}:null}:null;}
window.__rlgwo.read=()=>({clock:window.__rlgwo.clock(),now:Number.isFinite(simNow())?simNow():null,nowFinite:Number.isFinite(simNow()),parts:Number.isFinite(simNow())?nowParts():null,valid:_simValid,zone:tz,clockAnchor:Number.isFinite(_simBase)?_simBase:null,anchorFinite:Number.isFinite(_simBase),clockMode:{followWall:FOLLOW_WALL_CLOCK,rate:TIMESCALE,advancing:ADVANCING},generation:_runtimeGeneration,loopStarted:_loopStarted,sceneBuilt:_sceneBuilt,sceneBuilds:{stars:window.__rlgwo.trace.filter(x=>x.event==='buildStars').length,weather:window.__rlgwo.trace.filter(x=>x.event==='buildWeather').length},config:CONFIG,mode:_cfgMode,day:lastDate,today,tomorrow,date:_lastDateTruth,model:window.__rlgwo.lastModel??null,cnFit:_cnFit,slots:Object.fromEntries(Object.entries(_requestSlots).map(([k,v])=>[k,rlgwoOp(v)])),cooldown:_prayerCooldown,weather,track:weatherTrack,weatherEligibility:weatherEligibility(weather),selectedWeather:selectedWeather(),profileKeys:[..._zoneDays.keys()],limits:{prayerAttempt:10000,weatherBody:_WX_BODY_WAIT,rolloverRetry:_ROLLOVER_RETRY_MS},activeFrames:window.__rlgwo.activeFrames()});
window.__rlgwo.apply=cfg=>applyConfig(cfg,{save:false});
window.__rlgwo.ownerForSignal=signal=>rlgwoOp(Object.values(_requestSlots).find(op=>op?.attempt?.controller?.signal===signal));
const rlgwoModel=model;model=function(...args){const value=rlgwoModel.apply(this,args);window.__rlgwo.lastModel=value;return value;};
const rlgwoAdopt=adoptPrayerBundle;adoptPrayerBundle=function(...args){const before=window.__rlgwo.read(),value=rlgwoAdopt.apply(this,args);window.__rlgwo.trace.push({event:'adoptPrayerBundle',requestedDay:args[1],payloadDay:args[0]?.date?.gregorian?.date,operation:rlgwoOp(args[2]),value,before,after:window.__rlgwo.read()});return value;};
const rlgwoZoneDay=zoneDay;zoneDay=function(...args){const key=JSON.stringify([args[3],...args.slice(0,3)]),hit=_zoneDays.has(key),counts=window.__rlgwo.resolverCounts,projections=counts.projections,start=window.__rlgwo.clock().nativePerformance;const value=rlgwoZoneDay.apply(this,args);window.__rlgwo.trace.push({event:'zoneDay',args,key,hit,supported:!!value.minutes,profileCount:_zoneDays.size,projections:counts.projections-projections,durationMs:window.__rlgwo.clock().nativePerformance-start});return value;};
const rlgwoFit=fitCn;fitCn=function(...args){const fixture=window.__rlgwo,before=_cnFit,measurements=fixture.fitMeasurements.length;fixture.fitScope=true;let value;try{value=rlgwoFit.apply(this,args);}finally{fixture.fitScope=false;}fixture.trace.push({event:'fitCn',before,after:_cnFit,measurements:fixture.fitMeasurements.length-measurements,faces:Array.from(document.fonts||[],face=>({family:face.family,status:face.status})),...fixture.clock()});return value;};
window.__rlgwo.invalidateFitControl=()=>{const before=_cnFit;_cnFit='';window.__rlgwo.trace.push({event:'explicit-fit-invalidation-control',before,scope:'Named diagnostic control only; production/natural-fit claims exclude this stage.'});};
const rlgwoRender=render;render=function(...args){const result=rlgwoRender.apply(this,args);window.__rlgwo.trace.push({event:'actual-render',...window.__rlgwo.clock(),state:window.__rlgwo.read()});return result;};
const rlgwoWxEpoch=wxEpoch;wxEpoch=function(...args){const value=rlgwoWxEpoch.apply(this,args);window.__rlgwo.trace.push({event:'wxEpoch',args,value,globalZone:tz,...window.__rlgwo.clock()});return value;};
const rlgwoEpoch=epochForTzTime;epochForTzTime=function(...args){const value=rlgwoEpoch.apply(this,args);window.__rlgwo.trace.push({event:'epochForTzTime',args,value,globalZone:tz,...window.__rlgwo.clock()});return value;};
const rlgwoBegin=beginRequest;beginRequest=function(...args){const op=rlgwoBegin.apply(this,args);window.__rlgwo.trace.push({event:'beginRequest',args,operation:rlgwoOp(op),...window.__rlgwo.clock()});return op;};
const rlgwoAttempt=beginAttempt;beginAttempt=function(...args){const value=rlgwoAttempt.apply(this,args);window.__rlgwo.trace.push({event:'beginAttempt',operation:rlgwoOp(args[0]),timeoutMs:args[1],accepted:!!value,...window.__rlgwo.clock()});return value;};
const rlgwoFinish=finishRequest;finishRequest=function(op){const before=window.__rlgwo.read(),value=rlgwoFinish.call(this,op);window.__rlgwo.trace.push({event:'finishRequest',operation:rlgwoOp(op),value,before,after:window.__rlgwo.read()});return value;};
const rlgwoBuildStars=buildStars;buildStars=function(...args){const value=rlgwoBuildStars.apply(this,args);window.__rlgwo.trace.push({event:'buildStars',...window.__rlgwo.clock()});return value;};
const rlgwoBuildWeather=buildWeather;buildWeather=function(...args){const value=rlgwoBuildWeather.apply(this,args);window.__rlgwo.trace.push({event:'buildWeather',...window.__rlgwo.clock()});return value;};
window.__rlgwo.trace.push({event:'readonly-hooks-installed',...window.__rlgwo.clock()});
`;}
function prepare({root,suite,name,variant='default',source,runtimeIdentity}){
  root=path.resolve(root);source=source??fs.readFileSync(path.join(root,'index.html'),'utf8');
  const config=fs.readFileSync(path.join(root,'config.js'));
  unique(source,'<script src="config.js">','pre-config');unique(source,'\nboot();','native boot');
  const selectedSourceSha256=sha(source),p=plan(root,suite,name,variant),admission=strictNativeRuntime(source),selectedNative=admission.native;
  let native=selectedNative;
  if(p.mutant==='ignored-explicit-zone'){
    const anchor='function epochForTzTime(y,mo,d,h,mi,zone=tz){';unique(native,anchor,'ignored-zone native mutant');native=native.replace(anchor,anchor+' zone=tz;');
  }
  if(p.mutant==='unescaped-date-value'){
    const anchor='const text=(id,value)=>{ const el=$("#"+id); if(el.textContent!==value) el.textContent=value; };';unique(native,anchor,'unescaped date-value native control');native=native.replace(anchor,'const text=(id,value)=>{ const el=$("#"+id); if(el.textContent!==value) el.innerHTML=value; };');
  }
  unique(source,selectedNative,'actual native body');
  const effectiveSource=source.replace(selectedNative,native);
  const h=hooks();
  if(suite==='access'&&name==='font'){
    if(!runtimeIdentity?.files||runtimeIdentity.files['index.html']?.sha256!==sha(source))throw Error('Font cases require exact full runtime_identity matching selected index.html');
    p.runtimePaths=Object.keys(runtimeIdentity.files).sort();p.runtimeTreeSha256=runtimeIdentity.treeSha256;
  }else if(runtimeIdentity)throw Error('Native runtime inventory is reserved for font cases');
  const data=JSON.stringify(p).replace(/</g,'\\u003c').replace(/>/g,'\\u003e').replace(/&/g,'\\u0026');
  const preScript='('+installPreScript.toString()+')('+data+');';
  const nativeScript=native.replace('\nboot();',h+'\nboot();');
  const page=source.replace('<script src="config.js">','<script id="rlgwo-pre-script">'+preScript+'</script><script src="config.js">').replace(selectedNative,nativeScript);
  return {page,preScript,hooks:h,nativeScript,plan:p,identity:{sourceSha256:selectedSourceSha256,effectiveSourceSha256:sha(effectiveSource),sourceMutation:p.mutant||null,scriptLayout:{id:admission.layoutId,nativeOrdinal:SCRIPT_LAYOUTS[admission.layoutId].nativeOrdinal,scripts:admission.scripts},configSha256:sha(config),fixtureSha256:sha(page),
    originalFixtureSha256:sha(fs.readFileSync(path.join(root,'tests/r0009-browser-fixture.cjs'))),adapterSha256:sha(fs.readFileSync(__filename)),
    runtimeTreeSha256:p.runtimeTreeSha256||null,
    optionalTransport:p.runtimePaths?'Native fetch for same-origin exact runtime_identity files; controlled provider bodies; unrelated HTTP 503. Instrumented wall/mono/storage/callbacks; no whole-sky/first-scene/performance qualification':'HTTP 503; no whole-sky/first-scene/performance qualification',fonts:'Native FontFaceSet only; browser driver supplies explicit missing/delayed/loaded policy'}};
}
if(require.main===module){const [root,suite,name,variant,out,inventory]=process.argv.slice(2);if(!out)throw Error('Usage: node fixture.cjs root suite case variant output-prefix [runtime-identity-json]');const runtimeIdentity=inventory?JSON.parse(fs.readFileSync(inventory,'utf8')):undefined;const built=prepare({root,suite,name,variant,runtimeIdentity});fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out+'.html',built.page);fs.writeFileSync(out+'.json',JSON.stringify({plan:built.plan,identity:built.identity},null,2)+'\n');console.log(JSON.stringify({html:out+'.html',metadata:out+'.json',...built.identity}));}
module.exports={implemented,plan,prepare,record,strictNativeRuntime,SCRIPT_LAYOUTS};
