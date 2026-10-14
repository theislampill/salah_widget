module.exports = () => {
  if(window.__r000bMoonWithdrawal)throw Error('Duplicate withdrawal observer');
  const detail=window.SalahMoonDetail;if(!detail)throw Error('Moon detail owner unavailable');
  const original=detail.clear,events=[],observationErrors=[];
  const read=()=>{const p=window.SalahSkyPreview?.state,s=window.SalahRealSky?.state;
    return {elapsedMs:performance.now()-__widgetFixture.started,wallUtcMs:Date.now(),
      detail:detail.state,moon:window.SalahMoonHost?.capture(),
      classes:document.querySelector('.c').className,
      temperature:document.querySelector('#wt').textContent,icon:document.querySelector('#wi').textContent,
      preview:p?{status:p.status,utcMs:p.utcMs,reason:p.reason,draws:p.draws}:null,
      previewFrameCurrent:window.SalahSkyPreview?.frame?.current?.()??false,
      sky:s?{status:s.status,reason:s.reason,presentationUtcMs:s.presentationUtcMs,renders:s.renders}:null};};
  const observe=(phase,fn)=>{try{return fn();}catch(e){observationErrors.push({phase,error:String(e)});return null;}};
  detail.clear=function(...args){
    const before=observe('before',read),caller=observe('caller',()=>new Error('Moon detail clear caller').stack);
    try{return Reflect.apply(original,this,args);}
    finally{observe('after',()=>events.push({ordinal:events.length,caller,argumentCount:args.length,before,after:read()}));}
  };
  window.__r000bMoonWithdrawal={read,events,observationErrors,originalClearSource:String(original),wrapperSource:String(detail.clear)};
};
