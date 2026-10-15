'use strict';
// Disposable ingress and observation only. Importing this file starts no server or browser.
const crypto=require('node:crypto');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function preload(spec){
 return `(() => {
  'use strict';
  const spec=${JSON.stringify(spec).replace(/</g,'\\u003c')}, NativeDate=Date, nativeFetch=fetch.bind(window);
  const started=performance.now(), nativeSet=setTimeout.bind(window), nativeClear=clearTimeout.bind(window);
  const F=window.__prayerFixture={caseId:spec.caseId,started,events:[],snapshots:[],requests:[],storageLog:[],timerLog:[],unexpected:[],assets:[],rules:spec.responseRules||[],clockEpoch:null,ordinal:0};
  F.resourceTiming=()=>performance.getEntriesByType?.('resource').map(r=>({name:r.name,initiatorType:r.initiatorType,startTime:r.startTime,duration:r.duration,transferSize:r.transferSize,responseStatus:r.responseStatus??null}))||[];
  for(const event of ['load','error']) window.addEventListener?.(event,e=>{const target=e.target;
   if(target&&['IMG','SCRIPT','LINK'].includes(target.tagName))F.assets.push({event,tagName:target.tagName,url:target.currentSrc||target.src||target.href||null,naturalWidth:target.naturalWidth??null,realElapsedMs:performance.now()-started});},true);
  // Observe detached native radar Images without replacing their handlers or pixels.
  // Reflect.construct preserves the native constructor and its native prototype.
  const nativeImages=[]; F.imageEvents=[];
  const imageState=im=>({src:im.currentSrc||im.src,complete:im.complete,naturalWidth:im.naturalWidth,naturalHeight:im.naturalHeight,
    onloadPresent:typeof im.onload==='function',onerrorPresent:typeof im.onerror==='function'});
  F.imageStates=()=>nativeImages.map(imageState);
  if(spec.observeImages){
   const OriginalImage=window.Image;
   window.Image=new Proxy(OriginalImage,{construct(target,args,newTarget){
    const im=Reflect.construct(target,args,newTarget); nativeImages.push(im);
    for(const event of ['load','error'])im.addEventListener(event,()=>F.imageEvents.push({event,...imageState(im),
      realElapsedMs:performance.now()-started,owner:F.peekSlots?F.peekSlots():null}));
    return im;
   }});
  }
  const log=(type,fields={})=>F.events.push({type,realElapsedMs:performance.now()-started,wallUtcMs:Date.now(),...fields});
  const mode=spec.clockPolicy?.mode||'native';
  let base=mode==='native'?null:NativeDate.parse(spec.clockPolicy.epoch), baseElapsed=started;
  const wall=()=>mode==='advancing'?base+performance.now()-baseElapsed:base;
  if(mode!=='native'){
   if(!Number.isFinite(base)) throw Error('Invalid fixture epoch');
   window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[wall()]));}static now(){return wall();}};
   F.clockEpoch=base;
  }
  F.setClock=epoch=>{if(mode==='native')throw Error('native clock cannot be changed');base=NativeDate.parse(epoch);if(!Number.isFinite(base))throw Error('Invalid fixture epoch');baseElapsed=performance.now();log('fixture-clock',{epoch:base});};
  const storage=new Map((spec.cacheSeeds||[]).map(s=>[String(s.key),String(s.value)]));
  F.storage=()=>Array.from(storage,([key,value])=>({key,value}));
  Object.defineProperty(window,'localStorage',{configurable:true,value:{
   getItem:key=>{key=String(key);const value=storage.get(key)??null;F.storageLog.push({operation:'get',key,value,realElapsedMs:performance.now()-started});if(spec.storageReadDenied)throw Error('fixture storage denied');return value;},
   setItem:(key,value)=>{key=String(key);value=String(value);const denied=!!spec.storageWriteDenied;F.storageLog.push({operation:'set',key,value,denied,realElapsedMs:performance.now()-started});if(denied)throw Error('fixture storage denied');storage.set(key,value);},
   removeItem:key=>{key=String(key);F.storageLog.push({operation:'remove',key,value:storage.get(key)??null,realElapsedMs:performance.now()-started});if(spec.storageWriteDenied)throw Error('fixture storage denied');storage.delete(key);},
   clear:()=>{F.storageLog.push({operation:'clear',values:F.storage(),realElapsedMs:performance.now()-started});if(spec.storageWriteDenied)throw Error('fixture storage denied');storage.clear();},
   key:index=>Array.from(storage.keys())[index]??null,get length(){return storage.size;}
  }});
  const timerIds=new Set();
  window.setTimeout=(fn,ms,...args)=>{let id;id=nativeSet(typeof fn==='function'?function(...passed){timerIds.delete(id);F.timerLog.push({operation:'fire',id,realElapsedMs:performance.now()-started});return fn.apply(this,passed);}:fn,ms,...args);timerIds.add(id);F.timerLog.push({operation:'start',id,ms:Number(ms)||0,realElapsedMs:performance.now()-started});return id;};
  window.clearTimeout=id=>{timerIds.delete(id);F.timerLog.push({operation:'clear',id,realElapsedMs:performance.now()-started});return nativeClear(id);};
  F.activeTimers=()=>Array.from(timerIds);
  function kindOf(url){return url.hostname==='api.aladhan.com'?'prayer':url.hostname==='api.open-meteo.com'?'weather':url.hostname==='api.rainviewer.com'?'radar':null;}
  function matches(rule,url,kind){
   if(rule.kind!==kind||(rule.used||0)>=(rule.times??Infinity))return false;
   if(rule.day&&url.pathname.split('/').pop()!==rule.day)return false;
   return Object.entries(rule.match||{}).every(([key,value])=>url.searchParams.get(key)===String(value));
  }
  const pending=new Map();
  F.release=(id,occurrence=1)=>{const key=id+':'+occurrence,p=pending.get(key);if(!p)throw Error('No pending boundary '+key);pending.delete(key);log('release',{key});p.resolve();};
  F.reject=(id,occurrence=1)=>{const key=id+':'+occurrence,p=pending.get(key);if(!p)throw Error('No pending boundary '+key);pending.delete(key);log('reject',{key});p.reject(Error('fixture rejected boundary'));};
  F.pending=()=>Array.from(pending.keys());
  F.setRule=(id,patch)=>{const rule=F.rules.find(r=>r.id===id);if(!rule)throw Error('Unknown rule '+id);Object.assign(rule,patch);log('rule-change',{id,patch});};
  function hold(rule,key,signal,phase){
   return new Promise((resolve,reject)=>{
    let done=false;const settle=(fn,value)=>{if(done)return;done=true;pending.delete(key);if(signal)signal.removeEventListener('abort',abort);fn(value);};
    const abort=()=>{log(phase+'-abort',{key,ignoreAbort:!!rule.ignoreAbort});if(!rule.ignoreAbort)settle(reject,new DOMException('Aborted','AbortError'));};
    pending.set(key,{resolve:()=>settle(resolve),reject:e=>settle(reject,e)});log(phase+'-hold',{key});
    if(signal){if(signal.aborted)abort();else signal.addEventListener('abort',abort,{once:true});}
   });
  }
  window.fetch=async(input,init={})=>{
   const url=new URL(typeof input==='string'?input:input.url,location.href),kind=kindOf(url);
   if(!kind){if(url.origin===location.origin)return nativeFetch(input,init);F.unexpected.push({url:url.href});log('unmatched',{url:url.href});throw Error('unmatched provider fetch '+url.href);}
   const rule=F.rules.find(r=>matches(r,url,kind));
   const request={serial:F.requests.length+1,url:url.href,kind,realElapsedMs:performance.now()-started,wallUtcMs:Date.now(),owner:F.peekSlots?F.peekSlots():null,cooldown:F.peekCooldown?F.peekCooldown():null,rule:rule?.id||null};F.requests.push(request);
   if(!rule){F.unexpected.push(request);throw Error('unmatched provider fetch '+url.href);}
   rule.used=(rule.used||0)+1;const key=rule.id+':'+rule.used;request.occurrence=rule.used;log('fetch',{...request});
   if(rule.failure)throw Error('fixture offline '+rule.id);
   if(rule.hold&&rule.phase==='headers')await hold(rule,key,init.signal,'headers');
   const body=()=>{
    const data=JSON.parse(JSON.stringify(rule.payload));
    if(kind==='radar'&&data.host==='__ORIGIN__')data.host=location.origin;
    if(rule.dateFromRequest&&kind==='prayer'){
     const day=url.pathname.split('/').pop(),[d,mo,y]=day.split('-').map(Number);
     data.data.date.gregorian={...data.data.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:new NativeDate(Date.UTC(y,mo-1,d)).toLocaleString('en',{month:'long',timeZone:'UTC'})},year:String(y)};
    }
    return data;
   };
   log('headers',{key,status:rule.httpStatus??200});
   return {ok:(rule.httpStatus??200)>=200&&(rule.httpStatus??200)<300,status:rule.httpStatus??200,json:async()=>{
    log('json-start',{key});if(rule.hold&&rule.phase==='body')await hold(rule,key,init.signal,'body');const result=body();log('json-settle',{key});return result;
   }};
  };
  window.addEventListener?.('error',e=>log('error',{message:e.message}));
  window.addEventListener?.('unhandledrejection',e=>log('unhandledrejection',{message:String(e.reason)}));
 })();`;
}
function observerHook(){return `
// TEST-ONLY read-only completed-render receipt; never computes product diagnostics.
const prayerFixture=window.__prayerFixture;
const prayerCopy=(value,seen=new Set())=>{
 if(typeof value==='number'&&!Number.isFinite(value))return {finite:false,value:null};
 if(value===undefined)return {unavailable:true};if(value===null||typeof value!=='object')return value;
 if(seen.has(value))return {circular:true};seen.add(value);
 const out=Array.isArray(value)?[]:{};
 for(const key of Object.keys(value)){const field=value[key];if(typeof field!=='function'&&key!=='controller'&&key!=='cancel')out[key]=prayerCopy(field,new Set(seen));}
 return out;
};
const prayerOwner=op=>op?{generation:op.generation,operationId:op.operationId,kind:op.kind,requestedDay:op.requestedDay,lat:op.lat,lon:op.lon,method:op.method,school:op.school,units:op.units,requestZone:op.requestZone,cacheKey:op.cacheKey,weatherCacheKey:op.weatherCacheKey,prayerAttempts:op.prayerAttempts,attempt:op.attempt?{operationId:op.attempt.operationId,attemptId:op.attempt.attemptId,requestedDay:op.attempt.requestedDay,deadlineAt:op.attempt.deadlineAt,timer:op.attempt.timer,expired:op.attempt.expired,aborted:op.attempt.controller?op.attempt.controller.signal.aborted:null}:null}:null;
prayerFixture.peekSlots=()=>Object.fromEntries(Object.entries(_requestSlots).map(([key,op])=>[key,prayerOwner(op)]));
prayerFixture.peekCooldown=()=>prayerCopy(_prayerCooldown);
const prayerDom=selector=>{const e=document.querySelector(selector);if(!e)return {unavailable:true};const r=e.getBoundingClientRect();return {tagName:String(e.tagName||'unavailable').toLowerCase(),text:e.textContent,html:e.innerHTML,geometry:{x:r.x,y:r.y,width:r.width,height:r.height},font:getComputedStyle(e).fontFamily};};
const prayerSnapshot=stage=>{
 const state={caseId:prayerFixture.caseId,renderOrdinal:prayerFixture.ordinal,stage,wallUtcMs:Date.now(),realElapsedMs:performance.now()-prayerFixture.started,runtimeGeneration:_runtimeGeneration,
  config:{lat,lon,label,method,school,units,cacheTz:_cacheTz},
  ownerSummary:Object.fromEntries(Object.entries(_requestSlots).map(([key,op])=>[key,op?{generation:op.generation,lat:op.lat,lon:op.lon,operationId:op.operationId}:null])),
  timezone:tz,currentDay:today?.date?.gregorian?.date??null,tomorrowDay:tomorrow?.date?.gregorian?.date??null,today:prayerCopy(today),tomorrow:prayerCopy(tomorrow),
  slots:prayerFixture.peekSlots(),cooldown:prayerFixture.peekCooldown(),render:prayerCopy(_lastRender),dateTruth:prayerCopy(_lastDateTruth),weatherHeader:prayerCopy(_lastWeatherHeader),
  weatherDecision:prayerCopy(typeof _wxDecisionCache!=='undefined'&&_wxDecisionCache?_wxDecisionCache.decision:undefined),
  weather:prayerCopy(weather),weatherTrack:prayerCopy(weatherTrack),weatherRadar:prayerCopy(weatherRadar),lastWxAt,lastRadarAt,
  wxRequests:prayerCopy(typeof _wxRequests!=='undefined'?_wxRequests:undefined),dirty:_renderDirty,
  clock:{TIMESCALE,FOLLOW_WALL_CLOCK,ADVANCING},dom:Object.fromEntries(['.c','.cn','.nt','.left','.times','#ce','#ah','.arc','.buckle','.d','#dateDialog','#dateHijri','#dateReason','#wt','#wi'].map(s=>[s,prayerDom(s)])),
  fonts:document.fonts?.status??'unavailable',assets:prayerCopy(prayerFixture.assets),storageLogLength:prayerFixture.storageLog.length,timerLogLength:prayerFixture.timerLog.length,
  flags:{lastDate,prayerStale:_prayerStale,wxBusy,radarBusy,fetchingTomorrow,siteElev,currentOwnerLat:_requestSlots.current?.lat??null},
  visibility:{state:document.visibilityState,paused:document.querySelector('.c')?.classList.contains('paused')}};
 if(stage==='read-only-checkpoint'){
  state.storage=prayerFixture.storage();state.imageStates=prayerFixture.imageStates();
  state.elevationCustody=prayerCopy(typeof _cp9SiteElevation!=='undefined'?_cp9SiteElevation:undefined);
  state.moonConsumed=prayerCopy(_lastMoonPaint);state.cloudMotion=prayerCopy(_cloudMotion);
 }
 prayerFixture.snapshots.push(state);return state;
};
prayerFixture.readSnapshot=()=>prayerSnapshot('read-only-checkpoint');
const prayerOriginalRender=render;
render=function(...args){const result=prayerOriginalRender.apply(this,args);prayerFixture.ordinal++;prayerSnapshot('render-completed');return result;};
if(typeof showError==='function'){const prayerOriginalError=showError;showError=function(...args){const result=prayerOriginalError.apply(this,args);prayerFixture.events.push({type:'error-output',renderOrdinal:prayerFixture.ordinal,message:args[0],realElapsedMs:performance.now()-prayerFixture.started});prayerSnapshot('error-output');return result;};}
`;}
function instrument(source,spec){
 let normalized=source.replace(/\r\n/g,'\n');
 const variants={
  'no-abort':['controller:typeof AbortController!=="undefined"?new AbortController():null','controller:null'],
  'wall-countdown':['leftMin, nowEpoch, nextEpoch,','leftMin:nextMin-nowMin, nowEpoch, nextEpoch,'],
  'sec-only':['if(sec!==_lastSec || _renderDirty)','if(sec!==_lastSec)'],
  'epoch-plus24':['const nextEpoch=nextDay ?','const nextEpoch=tomorrowFlag && nextDay && currentDay ? epochForTzTime(currentDay.y,currentDay.mo,currentDay.d,nextHour,nextMinute,nextZone)+86400000 : nextDay ?'],
  'early-cache-filter':['const cached=readPrayerCache(op.cacheKey);','const rawCached=readPrayerCache(op.cacheKey); const cached=rawCached && rawCached.date===prayerCivilDay() ? rawCached : null;'],
  'removed-day-check':['if(day!==requested){','if(false){'],
  'unconditional-finally':['if(!requestEligible(op)) return false;\n  _requestSlots[op.kind]=null; return true;','_requestSlots[op.kind]=null; return true;']
 };
 if(spec.variant){
  const edit=variants[spec.variant];if(!edit||normalized.split(edit[0]).length!==2)throw Error('exact variant anchor drift: '+spec.variant);
  normalized=normalized.replace(edit[0],edit[1]);
 }
 if(normalized.split('\nboot();').length!==2)throw Error('unique natural boot anchor drift');
 if(normalized.split('<head>').length!==2)throw Error('unique head anchor drift');
 return normalized.replace('<head>','<head><script>'+preload(spec)+'</script>').replace('\nboot();',observerHook()+'\nboot();');
}
module.exports={sha,preload,observerHook,instrument};
if(require.main===module){const fs=require('node:fs');const source=fs.readFileSync(process.argv[2],'utf8'),spec=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));process.stdout.write(instrument(source,spec));}
