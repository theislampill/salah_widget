// Typed QA inputs and native observations only. Never replaces native decision/render/sampler owners.
(() => {
  'use strict';
  const report=window.__widgetFixture,control=window.__weatherFixtureControl,api=window.__smokeWeather;
  const copy=x=>x==null?null:JSON.parse(JSON.stringify(x)),records=[],nativeEvents=[];
  const owners=[weatherDecision,reconcileWeatherEvidence,render,fetchWeather,fetchRadar,admitWeatherRecord,admitWeatherFixture,tieRainToClouds,paintClouds];
  const assertOwner=owner=>{control.assertOwned(owner);const live=[weatherDecision,reconcileWeatherEvidence,render,fetchWeather,fetchRadar,admitWeatherRecord,admitWeatherFixture,tieRainToClouds,paintClouds];if(live.some((v,i)=>v!==owners[i]))throw Error('Native owner replaced');};
  const check=(name,passed,detail)=>{records.push({name,passed:passed===true,detail:copy(detail)});return passed===true;};
  for(const name of ['visibilitychange','freeze','resume'])document.addEventListener(name,e=>nativeEvents.push({type:e.type,trusted:e.isTrusted,visibility:document.visibilityState,wall:Date.now(),monotonic:performance.now()}));
  function diagnosticTiming(effect){
    const timing=effect.getTiming();
    // These two Web Animations members permit +Infinity. Preserve it as typed
    // diagnostic data; unrelated nonfinite values still fail the strict publisher.
    for(const member of ['iterations','duration'])if(timing[member]===Infinity)timing[member]={kind:'positive-infinity',source:'AnimationEffect.getTiming()',member};
    return timing;
  }
  function origins(){
    const card=document.querySelector('.c'),box=card.getBoundingClientRect(),density=_colDens?Array.from(_colDens):[],mx=Math.max(0,...density);
    const particles=[...document.querySelectorAll('.drop,.flake')].map(e=>{
      const style=getComputedStyle(e),left=parseFloat(e.style.left)||50,col=Math.max(0,Math.min(density.length-1,(left/100*density.length)|0));
      return {kind:e.classList.contains('drop')?'rain':'snow',leftPercent:left,column:col,density:density[col]??null,densityFraction:mx>0?(density[col]??0)/mx:null,
        authoredTop:style.top,authoredTopPx:parseFloat(style.top),visible:style.display!=='none'&&style.visibility==='visible'&&+style.opacity>.03,opacity:+style.opacity,
        animationName:style.animationName,animationState:style.animationPlayState,animations:e.getAnimations().map(a=>({playState:a.playState,currentTime:a.currentTime,timing:diagnosticTiming(a.effect)}))};});
    return {card:{width:box.width,height:box.height},density,mx,particles,cloudOriginReview:'PENDING actual card/crop/clip; snow must also satisfy cloud-column requirement'};
  }
  function read(owner){assertOwner(owner);return {wall:Date.now(),monotonic:performance.now(),visibility:document.visibilityState,paused:document.querySelector('.c').classList.contains('paused'),nativeEvents:copy(nativeEvents),
    state:__weatherCases.read(owner),cloud:{fieldSeed:_cloudFieldSeed,motion:copy(_cloudMotion),state:copy(cloudState)},origins:origins(),checks:copy(records),
    eligibility:copy(weatherEligibility(weather)),held:report.case.staleResponse?control.held(owner):[],slots:__weatherCases.temporalRead(owner).slots,
    cacheByTarget:report.case.staleResponse?{A:localStorage.getItem('salahwx:24.47|39.61|c'),B:localStorage.getItem('salahwx:30|0|c')}:null,
    capturedOperation:(()=>{const op=_requestSlots.weather;return op?{generation:op.generation,operationId:op.operationId,lat:op.lat,lon:op.lon,units:op.units,zone:op.requestZone,cacheKey:op.weatherCacheKey}:null;})()};}
  function presentRaw(){const n=Date.now(),target=currentWeatherTarget();return {scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',target:copy(target),measurementAt:n,retrievedAt:n,validFrom:n,validUntil:n+60000,frameAt:n,issuedAt:n,units:'categorical',footprint:{kind:'point',coverage:'target',lat:target.lat,lon:target.lon},quality:{status:'qualified',sampling:'direct',operationalHealth:'operational',localObservationAt:n},present:{state:'wet',type:'rain',lightning:'not-observed',quantity:null}};}
  function clearDecision(){_wxDecisionCache=null;render();}
  function modelRaw(n){return {time:new Date(n+3*3600000).toISOString().slice(0,16),interval:900,weather_code:63,temperature_2m:20,precipitation:2,cloud_cover:95,cloud_cover_low:60,cloud_cover_mid:60,cloud_cover_high:30};}
  async function run(owner,kind){
    assertOwner(owner);if(!(report.case.nativeSteps||[]).some(x=>x.kind===kind))throw Error('Unlisted typed native step');
    if(kind==='live-present-refusal'){
      const before=read(owner);let refused=false;try{api.installSynthetic(owner,presentRaw());}catch(e){refused=String(e).includes('ordinary live lane');}
      const after=read(owner);check('liveSyntheticRefused',refused);check('liveRefusalPreservesModelCache',JSON.stringify(before.state.raw)===JSON.stringify(after.state.raw)&&JSON.stringify(before.state.cached)===JSON.stringify(after.state.cached)&&before.state.precip===after.state.precip);
    }else if(kind==='present-refusal-preservation'){
      const before=weatherSynthetic;
      for(const [name,mutate]of [['future-from',r=>r.validFrom=Date.now()+1],['wrong-quantity-unit',r=>r.present.quantity={kind:'rate',value:1.6,units:'mm',from:Date.now()-1,to:Date.now()}],['null-measurement',r=>r.measurementAt=null],['nonfinite-quantity',r=>r.present.quantity={kind:'amount',value:Infinity,units:'mm',from:Date.now()-900000,to:Date.now()}]]){
        const raw=presentRaw();mutate(raw);const admission=api.admitSynthetic(owner,raw);check('presentReject:'+name,admission.ok===false,admission);check('presentAdmissionReadPreserves:'+name,weatherSynthetic===before);
      }
    }else if(kind==='forecast-preservation'){
      const n=Date.now(),original=weatherDecision().forecast,raw={scope:'simulation-fixture',policy:'synthetic-forecast-v1',provider:'Synthetic QA',product:'probability contract',target:copy(currentWeatherTarget()),issuedAt:n,retrievedAt:n,validFrom:n+600000,validUntil:n+1800000,amount:{kind:'interval-amount',value:2,units:'mm'},probability:0,probabilityEvent:{event:'precipitation',from:n+600000,to:n+1800000},resolution:'synthetic fixture; calibration unavailable'};
      for(const name of ['owner','target','event','units','expired','stale-receipt','future-issue','partial-number']){const bad=copy(raw),wrong=copy(owner),dependency=weatherForecast;if(name==='owner')wrong.documentId='wrong';if(name==='target')bad.target.generation++;if(name==='event')bad.probabilityEvent.to++;if(name==='units')bad.amount.units='mm/h';if(name==='expired'){bad.validFrom=n-2;bad.validUntil=n-1;}if(name==='stale-receipt'){bad.issuedAt=n-21600001;bad.retrievedAt=n-21600001;}if(name==='future-issue')bad.issuedAt=n+1;if(name==='partial-number')bad.amount.value='2mm';let refused=false;try{api.installSyntheticForecast(wrong,bad);}catch(e){refused=true;}check('forecastReject:'+name,refused);check('forecastPreserved:'+name,weatherDecision().forecast===original&&weatherForecast===dependency,{raw:bad,refused});}
      api.clearSyntheticForecast(owner);check('forecastCleared',weatherDecision().forecast===null);
      api.installSyntheticForecast(owner,raw);control.advance(owner,900001);control.advance(owner,899999);clearDecision();check('forecastExclusiveExpiry',weatherDecision().forecast===null);
      const m=Date.now(),fresh={...raw,target:copy(currentWeatherTarget()),issuedAt:m,retrievedAt:m,validFrom:m+600000,validUntil:m+1800000,probabilityEvent:{event:'precipitation',from:m+600000,to:m+1800000}};
      api.installSyntheticForecast(owner,fresh);beginRuntimeGeneration();clearDecision();check('forecastGenerationWithdraws',weatherDecision().forecast===null);
    }else if(kind==='source-boundary'){
      const source=weather.currentValidAt,receipt=weather.retrievedAt;control.advance(owner,source+900000-Date.now());clearDecision();check('sourceInclusive900000',weatherEligibility(weather).eligible&&Date.now()-source===900000&&Date.now()-receipt<900000,weatherEligibility(weather));
      control.advance(owner,1);clearDecision();check('sourceExclusive900001',!weatherEligibility(weather).eligible&&Date.now()-source===900001,weatherEligibility(weather));
    }else if(kind==='receipt-boundary'){
      const n=Date.now(),raw=modelRaw(n),ctx={units,zone:tz,retrievedAt:n-60000,target:currentWeatherTarget()};weather=admitWeatherRecord(raw,ctx);weatherTrack=null;clearDecision();
      check('receiptViaActualAdmission',weather!==null&&weather.currentValidAt===n&&weather.retrievedAt===n-60000,{input:raw,context:ctx,admitted:weather});
      control.advance(owner,840000);clearDecision();check('receiptInclusive900000',weatherEligibility(weather).eligible&&Date.now()-weather.retrievedAt===900000&&Date.now()-weather.currentValidAt===840000,weatherEligibility(weather));
      control.advance(owner,1);clearDecision();check('receiptExclusive900001',!weatherEligibility(weather).eligible&&Date.now()-weather.currentValidAt===840001,weatherEligibility(weather));
    }else if(kind==='radar-receipt-not-renewal'){
      const before=copy(weatherRadar);control.advance(owner,600001);await fetchRadar();const result=radarEvidence();check('oldSourceExpiresDespiteFreshReceipt',before!==null&&weatherRadar.frameGeneratedAt===before.frameGeneratedAt&&weatherRadar.retrievedAt===Date.now()&&!result.available&&result.receiptAgeMs===0&&result.frameAgeMs>1200000,{before,result,after:weatherRadar});clearDecision();
    }else if(kind==='prepare-live-expiry'){
      const end=Math.min(weather.currentValidAt,weather.retrievedAt)+900001,advance=Math.floor(end-Date.now()-2000);control.advance(owner,advance);clearDecision();check('liveBeforeSuspensionEligible',weatherEligibility(weather).eligible);check('liveDeadlineWithin2s',end-Date.now()<=2001&&end-Date.now()>0,{end,now:Date.now()});
    }else if(kind==='stale-response')throw Error('Stale response is a driver-ordered multi-step control');
    return read(owner);
  }
  function stale(owner,step){assertOwner(owner);if(!report.case.staleResponse)throw Error('Wrong closed stale-response case');
    if(step==='A'){control.advance(owner,60001);control.holdNext(owner);fetchWeather();}
    else if(step==='B'){beginRuntimeGeneration();lat=30;lon=0;control.advance(owner,60001);control.holdNext(owner);fetchWeather();loadPrayerData();clearDecision();}
    else if(step==='release'){return control.release(owner);}
    else if(step==='tick'){control.advance(owner,1001);}
    else throw Error('Unknown closed stale-response step');return read(owner);
  }
  async function recovery(owner){assertOwner(owner);if(!report.case.suspend?.recover)throw Error('Recovery not in closed case');
    if(!report.ledger.some(r=>r.sequence===2&&r.result==='controlled-native-503'))await fetchWeather();
    check('actualOutageAttemptRetained',report.ledger.some(r=>r.sequence===2&&r.result==='controlled-native-503'));
    check('outageDoesNotRestoreExpiredCurrent',!weatherEligibility(weather).eligible);const unavailable=read(owner);
    control.advance(owner,60001);await fetchWeather();return {unavailable,restoredInput:read(owner)};}
  window.__r24NativeControl=Object.freeze({identity:control.identity,read,run,stale,recovery});
})();
