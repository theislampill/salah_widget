// Test-only startup observation. Install before document scripts. No product
// calls, font loads, DOM edits, clock changes or replacement scheduler.
(() => {
  'use strict';
  const fonts=document.fonts,nativeSetTimeout=window.setTimeout.bind(window);
  const done=new WeakSet(),failed=new WeakSet(),known=new Map(),events=[],lifecycleErrors=[];
  let nextId=0,pendingDeferred=0;
  const relevant=face=>/^(Fraunces|Inter)$/i.test(String(face.family||'').replace(/["']/g,'').trim());
  const metadata=face=>({family:face.family,weight:face.weight,style:face.style,status:face.status});
  function identify(face){
    if(!known.has(face))known.set(face,{id:++nextId,lastStatus:face.status,descriptors:JSON.stringify([face.family,face.weight,face.style])});
    return known.get(face);
  }
  function scan(){
    const faces=[...fonts].filter(relevant),current=new Set(faces);
    for(const [face,record] of known){
      if(!current.has(face)&&!lifecycleErrors.includes('removed:'+record.id))lifecycleErrors.push('removed:'+record.id);
    }
    for(const face of faces){
      const record=identify(face),descriptors=JSON.stringify([face.family,face.weight,face.style]);
      if(record.descriptors!==descriptors&&!lifecycleErrors.includes('changed:'+record.id))lifecycleErrors.push('changed:'+record.id);
      if(['loaded','error'].includes(record.lastStatus)&&['loading','unloaded'].includes(face.status)&&!lifecycleErrors.includes('restarted:'+record.id))lifecycleErrors.push('restarted:'+record.id);
      record.lastStatus=face.status;
    }
    return faces;
  }
  function settled(){
    const faces=scan();
    return fonts.status==='loaded'&&pendingDeferred===0&&lifecycleErrors.length===0&&faces.every(face=>
      face.status==='unloaded'||face.status==='loaded'&&done.has(face)||face.status==='error'&&failed.has(face));
  }
  for(const type of ['loading','loadingdone','loadingerror'])fonts.addEventListener(type,event=>{
    scan();
    const faces=[...(event.fontfaces||[])].filter(relevant);
    const receipt={kind:'dispatch',type,at:performance.now(),faces:faces.map(face=>({id:identify(face).id,...metadata(face)}))};
    events.push(receipt);
    if(type==='loading'||faces.length===0)return;
    pendingDeferred++;
    // A task (not a microtask) runs after the entire native event dispatch,
    // including the product listeners registered after this early observer.
    // This one-shot observer timer is separate from the product timer ledger.
    nativeSetTimeout(()=>{
      for(const face of faces)(type==='loadingdone'?done:failed).add(face);
      pendingDeferred--;
      scan();
      events.push({kind:'deferred-receipt',type,at:performance.now(),faces:faces.map(face=>({id:identify(face).id,...metadata(face)}))});
    },0);
  });
  window.__r0007FontSettlement=Object.freeze({settled,read:()=>{
    const isSettled=settled();
    return {scope:'STATIC_AUTHORED_FONT_STARTUP_ONLY',status:fonts.status,settled:isSettled,pendingDeferred,
      lifecycleErrors:lifecycleErrors.slice(),faces:scan().map(face=>({id:identify(face).id,...metadata(face),loadingdoneReceipt:done.has(face),loadingerrorReceipt:failed.has(face)})),events:events.slice()};
  }});
})();

// independent mismatch
