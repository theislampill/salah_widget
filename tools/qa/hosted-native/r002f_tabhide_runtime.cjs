'use strict';
// These functions execute in the disposable page. They replace Date only and
// observe the original owners; they never invoke an adopting Moon accessor.
function installClock(originUtc){
  const RealDate=Date,perf=performance,now=performance.now,originPerf=Reflect.apply(now,perf,[]);
  const names=['setTimeout','clearTimeout','setInterval','clearInterval','requestAnimationFrame','cancelAnimationFrame'];
  const callbacks=names.map(key=>globalThis[key]);
  const utc=()=>Math.floor(originUtc+Reflect.apply(now,perf,[])-originPerf);
  function TranslatedDate(...args){
    if(new.target)return Reflect.construct(RealDate,args.length?args:[utc()],new.target);
    return new RealDate(utc()).toString();
  }
  TranslatedDate.prototype=RealDate.prototype;Object.setPrototypeOf(TranslatedDate,RealDate);TranslatedDate.now=utc;
  globalThis.Date=TranslatedDate;
  globalThis.__r002fTabClock=Object.freeze({read(){const at=Reflect.apply(now,perf,[]);return {protocol:'r002f-translated-date/1',rate:1,originUtc,originPerf,
    utc:Math.floor(originUtc+at-originPerf),perf:at,nativeCallbacks:Date===TranslatedDate && Date.now===utc && performance===perf && performance.now===now &&
      names.every((key,i)=>globalThis[key]===callbacks[i])};}});
}
function installObserver(readPrayerSource){
  if(window.__r002fTabObserver)throw Error('duplicate tab observer');
  const readPrayer=(0,eval)('('+readPrayerSource+')');let trace=null;
  const snapshot=()=>{
    const card=document.querySelector('.c'),bounds=card?.getBoundingClientRect(),moon=window.SalahMoonRuntime?.observe(),
      sky=window.realSkyState?.(),state=moon?.state;
    return {clock:window.__r002fTabClock.read(),hidden:document.hidden,visibility:document.visibilityState,
      paused:!!card?.classList.contains('paused'),intersects:!!bounds && bounds.bottom>0 && bounds.right>0 && bounds.top<innerHeight && bounds.left<innerWidth,
      dpr:devicePixelRatio,prayer:readPrayer(),
      moon:{current:!!moon?.current,accepted:!!moon?.accepted,source:state?.visibleSource??null,quality:state?.quality??null,
        identity:state?.accepted?.identity??null,epoch:state?.epoch??null,pending:state?.pending??null,
        phasePositionBudget:state?.phasePrecision?.maximumPositionErrorDevicePixels??null,
        signedPositionDrift:state?.phasePrecision?.signedPositionDrift??null,adoption:state?.lastAdoption??null,
        quarantine:window.SalahMoonRuntime?.quarantineResearch??null},
      sky:{status:sky?.status??null,physical:sky?.physical===true,composed:!!card?.classList.contains('real-sky-composed'),
        displayed:!!sky?.displayed?.identity,displayedUtcMs:sky?.displayed?.utcMs??null,
        sunAltitude:sky?.last?.physicalState?.sun?.altDeg??null,utcMs:sky?.last?.utcMs??null}};
  };
  const push=(key,value)=>{if(!trace)return;if(trace.events.length+trace.marks.length>=trace.limit){trace.overflow=true;return;}trace[key].push(value);};
  const mark=name=>push('marks',{name,at:performance.now(),sample:snapshot()});
  const callbacks=()=>queueMicrotask(()=>{
    mark('callback-microtask');requestAnimationFrame(()=>{mark('raf-1');requestAnimationFrame(()=>mark('raf-2'));});
  });
  const visibility=event=>{
    if(!trace)return;push('events',{type:'visibilitychange',trusted:event.isTrusted,at:performance.now(),timeStamp:event.timeStamp,sample:snapshot()});
    if(trace.mode==='tabhide' && trace.triggered && !document.hidden)callbacks();
  };
  const navigation=event=>push('events',{type:event.type,trusted:event.isTrusted,at:performance.now(),timeStamp:event.timeStamp,
    persisted:event.persisted,sample:snapshot()});
  document.addEventListener('visibilitychange',visibility);window.addEventListener('pagehide',navigation);window.addEventListener('pageshow',navigation);
  window.__r002fTabObserver=Object.freeze({snapshot,begin(mode){
    if(!['no-hide','tabhide'].includes(mode)||document.hidden)throw Error('invalid visible start');
    trace={protocol:'r002f-tabhide-lifecycle/1',clockDomain:'page-performance-now-ms',mode,limit:64,overflow:false,
      events:[],marks:[],triggered:false,controlComplete:false};mark('begin');
  },trigger(){if(!trace||trace.triggered)throw Error('duplicate trigger');mark('trigger');trace.triggered=true;
  },completeControl(){if(trace?.mode!=='no-hide'||!trace.triggered||trace.controlComplete)throw Error('invalid control completion');
    trace.controlComplete=true;callbacks();
  },settled(){mark('settled');return snapshot();},read(){return structuredClone(trace);},dispose(){
    document.removeEventListener('visibilitychange',visibility);window.removeEventListener('pagehide',navigation);window.removeEventListener('pageshow',navigation);
    trace=null;
  }});
}
async function verifyClock(){
  const start=__r002fTabClock.read();let timerRan=false,rafRan=false;
  await new Promise(resolve=>setTimeout(()=>{timerRan=true;resolve();},40));
  await new Promise(resolve=>requestAnimationFrame(()=>{rafRan=true;resolve();}));
  const end=__r002fTabClock.read();return {timerRan,rafRan,nativeCallbacks:start.nativeCallbacks&&end.nativeCallbacks,
    performanceDeltaMs:end.perf-start.perf,dateDeltaMs:end.utc-start.utc};
}
module.exports={installClock,installObserver,verifyClock};
