// Installed before widget scripts only in the ordinary-clock qualification lane.
// Leave performance.now(), rAF, elapsed timers, and explicit Date arguments intact.
function installTrialWallClock(targetUtc) {
  const NativeDate=Date, offset=targetUtc-NativeDate.now();
  const shiftedNow=()=>NativeDate.now()+offset;
  globalThis.Date=new Proxy(NativeDate,{
    construct(target,args,receiver){return Reflect.construct(target,args.length?args:[shiftedNow()],receiver);},
    apply(){return new NativeDate(shiftedNow()).toString();},
    get(target,key,receiver){return key==='now'?shiftedNow:Reflect.get(target,key,receiver);}
  });
  window.__r35Clock={utc:targetUtc,at:performance.now()};
}
