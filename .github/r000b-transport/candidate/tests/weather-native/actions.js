// Owned, closed weather case actions. No product script body, sampler or permission logic is replaced.
(() => {
  'use strict';
  const control=window.__weatherFixtureControl,report=window.__widgetFixture,api=window.__smokeWeather;
  const copy=value=>value==null?null:JSON.parse(JSON.stringify(value));
  const events=[];let nextStep=0;const strikeElementIds=new WeakMap();let strikeElementSerial=0;
  const assertOwner=owner=>control.assertOwned(owner);
  const diagnosticTiming=effect=>{
    const value=effect.getTiming();
    for(const member of ['iterations','duration'])if(value[member]===Infinity)value[member]={kind:'positive-infinity',source:'AnimationEffect.getTiming()',member};
    return value;
  };
  const information=()=>{
    const wi=document.querySelector('#wi'),sink=document.querySelector('#weather-information'),b=document.querySelector('.buckle');
    const style=sink?getComputedStyle(sink):null;
    return {name:wi?.getAttribute('aria-label'),title:wi?.title,description:sink?.textContent??null,
      describedBy:wi?.getAttribute('aria-describedby'),sinkExposed:!!sink&&style.display!=='none'&&style.visibility!=='hidden'&&sink.getAttribute('aria-hidden')!=='true',
      buckle:{name:b?.getAttribute('aria-label'),title:b?.title,role:b?.getAttribute('role'),tabindex:b?.getAttribute('tabindex'),describedBy:b?.getAttribute('aria-describedby')},
      header:copy(_lastWeatherHeader),decision:copy(weatherDecision())};
  };
  const snapshot=owner=>{assertOwner(owner);const state=api.read(owner);return {...state,information:information(),events:copy(events)};};
  const rawPresent=action=>{
    const now=Date.now(),target=currentWeatherTarget();
    const raw={scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',
      target:copy(target),measurementAt:now,retrievedAt:now,validFrom:now,validUntil:now+(action.validFor||60000),
      frameAt:now,issuedAt:now,units:'categorical',footprint:{kind:'point',coverage:'target',lat:target.lat,lon:target.lon},
      quality:{status:'qualified',sampling:'direct',operationalHealth:'operational',localObservationAt:now},
      present:{...action.present,quantity:null}};
    if(action.quantity){const q=action.quantity;raw.present.quantity={kind:q.kind,value:q.value,units:q.units,from:now+q.fromOffset,to:now+q.toOffset};}
    if(action.nearby)raw.spatial={state:'nearby-precipitation',distanceKm:[8,12],observedAt:now-(action.spatialAge||0)};
    if(action.noEcho)raw.spatial={state:'observed-area-no-echo',distanceKm:[0,10],observedAt:now};
    if(action.trajectory)raw.approach={from:now+600000,to:now+1800000,derivedFrom:action.trajectory};
    const mutation=action.qualityMutation;
    if(mutation==='outside')raw.footprint.coverage='outside';
    if(mutation==='health-unknown')raw.quality.operationalHealth='unknown';
    if(mutation==='nonoperational')raw.quality.operationalHealth='nonoperational';
    if(mutation==='local-age-null')raw.quality.localObservationAt=null;
    if(mutation==='local-age-old')raw.quality.localObservationAt=now-1080000;
    if(mutation==='ambiguous')raw.quality.status='ambiguous';
    if(mutation==='interpolated')raw.quality.sampling='interpolated';
    return raw;
  };
  function action(owner,value){
    assertOwner(owner);let result;
    if(value.present){const raw=rawPresent(value);result=api.installSynthetic(owner,raw);events.push({action:'present',input:raw,result:copy(result.admission)});}
    else if(value.clearPresent){weatherSynthetic=admitWeatherFixture(null,currentWeatherTarget(),Date.now());_wxDecisionCache=null;render();events.push({action:'present-unavailable'});}
    else if(value.advance!=null){result=api.advanceClock(owner,value.advance);events.push({action:'advance',ms:value.advance});}
    else if(value.nextGeneration){result=api.nextGeneration(owner);events.push({action:'generation',target:copy(currentWeatherTarget())});}
    else if(value.forecast){
      const now=Date.now(),probability=value.forecast.probability;
      const raw={scope:'simulation-fixture',policy:'synthetic-forecast-v1',provider:'Synthetic QA',product:'probability contract',target:copy(currentWeatherTarget()),
        issuedAt:now,retrievedAt:now,validFrom:now+600000,validUntil:now+1800000,amount:{kind:'interval-amount',value:2,units:'mm'},probability,
        probabilityEvent:probability===null?null:{event:'precipitation',from:now+600000,to:now+1800000},resolution:'synthetic fixture; calibration unavailable'};
      try{result=api.installSyntheticForecast(owner,raw);if(value.expectRefusal)throw Error('Expected ordinary-live refusal did not happen');
        if(value.forecastOnly){weather=null;weatherTrack=null;_wxDecisionCache=null;render();events.push({action:'forecast-only-model-null-track-null'});}}
      catch(error){if(!value.expectRefusal||!String(error).includes('ordinary live lane'))throw error;result={refused:true,reason:String(error)};}
      events.push({action:'forecast',input:raw,result:copy(result)});
    }else if(value.resourcePrecompute){result=precompute(owner);events.push({action:'resource-tape',tape:copy(result)});
    }else if(value.settingsFailures){
      if(_cfgMode!=='local')throw Error('Settings control requires seeded local config');
      _publishPersistence('save',{ok:false,error:'QuotaExceededError'});events.push({action:'persistence-save-failed',information:information()});
      _publishPersistence('clear',{ok:false,error:'SecurityError'});events.push({action:'persistence-clear-failed',information:information()});
    }else throw Error('Unknown closed action');
    render();return snapshot(owner);
  }
  function checks(state,expected){
    const truth=state.qa.wxTruth,result={};
    if('temperature'in expected){result.temperature=state.raw?.temp===expected.temperature&&state.cached?.w.temp===expected.temperature&&state.temperature===(expected.temperature===null?'':String(expected.temperature)+'°');}
    if('current'in expected)result.current=truth.current===expected.current;
    if('spatial'in expected)result.spatial=truth.spatial.state===expected.spatial;
    if('horizon'in expected)result.horizon=truth.horizon.state===expected.horizon;
    if('presentAvailable'in expected)result.present=truth.present.available===expected.presentAvailable;
    if('radarAvailable'in expected)result.radarAvailable=truth.radarAvailable===expected.radarAvailable;
    if('radarInstalled'in expected)result.radarInstalled=(state.radar!==null)===expected.radarInstalled;
    if('wet'in expected)result.effects=expected.wet?state.precip==='on'&&state.visibleParticles>0:state.precip==='off'&&state.visibleParticles===0;
    if('strikes'in expected)result.strikePermission=truth.visualPermissions.lightning===expected.strikes&&state.lightning===(expected.strikes?'on':'off');
    if('observed'in expected)result.observed=truth.observedPresent===expected.observed;
    if(expected.sim)result.simInformation=state.information.description?.includes('SIM');
    if(expected.simForecast)result.simForecast=state.information.description?.includes('SIM Synthetic QA');
    if('probability'in expected)result.probability=truth.forecast?.probability===expected.probability&&state.information.description?.includes(expected.probability===null?'probability unavailable':String(expected.probability)+'% for precipitation');
    if(expected.modelEstimate)result.modelEstimate=state.information.description?.includes('CURRENT MODEL ESTIMATE')&&truth.permissions.rain===false&&truth.permissions.lightning===false;
    if(expected.quantityUnavailable)result.quantityUnavailable=state.information.description?.includes('amount unavailable')&&state.raw?.precip===null;
    if(expected.local)result.localSettings=state.information.buckle.role==='button'&&state.information.buckle.describedBy?.split(/\s+/).includes('weather-information');
    if(expected.settingsWarning)result.settingsWarning=state.information.buckle.name?.includes('saved settings could not be cleared');
    result.cardGeometry=state.card.width===325&&state.card.height===530;result.footerFits=state.footer.top>=0&&state.footer.bottom<=530.1;
    if(expected.group!=='RESOURCE'){
      result.descriptionExposed=state.information.sinkExposed&&state.information.description===state.information.header?.information?.summary;
      result.namePreservesTitleAndSummary=state.information.description?.length>0&&state.information.name===state.information.title&&state.information.name.includes(state.information.description);
      result.titleSameSnapshot=state.information.title?.includes(state.information.description);
    }
    return result;
  }
  const nativeRead=owner=>snapshot(owner);
  // Resource-only dependency/control: correctness/permission/pixel conclusions may not use replay output.
  let resourceBase=Date.now(),originalDecision=weatherDecision,replay=null,counts=null,resourceOriginals=null,resourceTape=null;
  function resourceStage(owner,name){
    assertOwner(owner);
    if(name==='cold'){weather=null;weatherTrack=null;weatherSynthetic=null;}
    else if(name==='wet'||name==='dry'){
      const raw={time:new Date(resourceBase+3*3600000).toISOString().slice(0,16),interval:900,weather_code:name==='wet'?63:0,
        temperature_2m:20,precipitation:name==='wet'?2:0,cloud_cover:95,wind_speed_10m:2,wind_direction_10m:180};
      weather=admitWeatherRecord(raw,{units,zone:tz,retrievedAt:resourceBase,target:currentWeatherTarget()});weatherTrack=null;weatherSynthetic=null;
    }else if(name==='expiry'){
      if(Date.now()<resourceBase+900001)control.advance(owner,resourceBase+900001-Date.now());
      const raw={time:new Date(resourceBase+3*3600000).toISOString().slice(0,16),interval:900,weather_code:63,temperature_2m:20,precipitation:2,cloud_cover:95};
      weather=admitWeatherRecord(raw,{units,zone:tz,retrievedAt:resourceBase,target:currentWeatherTarget()});weatherTrack=null;weatherSynthetic=null;
    }else if(name==='new-generation')beginRuntimeGeneration();else throw Error('Unknown resource epoch');
    _wxDecisionCache=null;
    if(replay){const entry=replay.entries.find(x=>x.stage===name);if(!entry)throw Error('Replay epoch missing');
      replay.active=entry;replay.current=selectedWeather();replay.target=currentWeatherTarget();replay.track=weatherTrack;replay.synthetic=weatherSynthetic;
      if(JSON.stringify({target:replay.target,current:replay.current,track:weatherTrack,synthetic:weatherSynthetic,now:Date.now()})!==entry.signature)throw Error('Replay input tape mismatch');}
    render();return nativeRead(owner);
  }
  const stages=['cold','wet','dry','expiry','new-generation'];
  function precompute(owner){
    assertOwner(owner);resourceBase=Date.now();const entries=[];
    for(const stage of stages){resourceStage(owner,stage);const target=currentWeatherTarget(),current=selectedWeather(),decision=originalDecision();
      entries.push({stage,signature:JSON.stringify({target,current,track:weatherTrack,synthetic:weatherSynthetic,now:Date.now()}),decision:copy(decision)});}
    const tape={policy:'r0024-scaffold-resource-baseline/v1',sourceSha256:report.sourceSha256,base:resourceBase,stages,entries};
    events.push({action:'resource-precompute',bytes:new TextEncoder().encode(JSON.stringify(tape)).byteLength});return tape;
  }
  function resourceArm(owner,arm,tape){
    assertOwner(owner);if(!['full','replay'].includes(arm)||tape.policy!=='r0024-scaffold-resource-baseline/v1'||tape.sourceSha256!==report.sourceSha256)throw Error('Resource identity/scope mismatch');
    if(Date.now()!==tape.base)throw Error('Tape requires fresh fixed-clock document');resourceBase=tape.base;
    const freeze=value=>{if(value&&typeof value==='object'){for(const child of Object.values(value))freeze(child);Object.freeze(value);}return value;};
    resourceTape=freeze(copy(tape)); // Identical retained tape in both arms.
    counts={decision:0,reconcile:0,forecast:0,lookup:0,legacySelection:0,cacheHit:0,cacheMiss:0};
    resourceOriginals={reconcile:reconcileWeatherEvidence,forecast:weatherForecast,decision:weatherDecision};
    reconcileWeatherEvidence=(...args)=>{counts.reconcile++;return resourceOriginals.reconcile(...args);};
    weatherForecast=(...args)=>{counts.forecast++;return resourceOriginals.forecast(...args);};
    if(arm==='full')weatherDecision=(...args)=>{counts.decision++;const old=_wxDecisionCache?.decision,value=resourceOriginals.decision(...args);counts[value===old?'cacheHit':'cacheMiss']++;return value;};
    else{replay={entries:resourceTape.entries,active:null,current:null,target:null,track:null,synthetic:null};
      weatherDecision=()=>{counts.decision++;counts.lookup++;if(!replay.active)throw Error('Replay epoch not selected');
        const target=currentWeatherTarget(),current=selectedWeather(),code=gateWeatherCode(current?current.code:null,current,0);wxClass(code);counts.legacySelection++;
        if(target!==replay.target||current!==replay.current||weatherTrack!==replay.track||weatherSynthetic!==replay.synthetic)throw Error('Replay lease/input changed');
        return replay.active.decision;};}
    return {arm,tapeBytes:new TextEncoder().encode(JSON.stringify(tape)).byteLength,observerCounts:counts};
  }
  window.__weatherCases=Object.freeze({identity:control.identity,read:nativeRead,
    temporalRead(owner){assertOwner(owner);const qa=window.qaState();return {wall:Date.now(),monotonic:_RAFNOW(),generation:_runtimeGeneration,
      weather:copy(weather),radar:copy(weatherRadar),header:copy(_lastWeatherHeader),wxTruth:copy(qa.wxTruth),prayerLoaded:qa.cache.prayerLoaded,
      wxBusy,radarBusy,requests:copy(_wxRequests),slots:Object.fromEntries(['weather','radar'].map(kind=>{const op=_requestSlots[kind],a=op?.attempt;return [kind,op?{operationId:op.operationId,generation:op.generation,attemptId:a?.attemptId??null,deadlineAt:a?.deadlineAt??null}:null];})),
      providerLedger:copy(report.ledger.filter(x=>!x.url.includes('/product/')))};},
    retryWallOffset(owner,ms){assertOwner(owner);if(!report.case.transport||report.case.transport.retryClock!=='wall-offset')throw Error('Only reviewed transport radar backoff offset is permitted');control.advance(owner,ms);return this.temporalRead(owner);},
    transportImages(owner){assertOwner(owner);return typeof window.__weatherTransportImages==='function'?window.__weatherTransportImages():null;},
    run(owner){assertOwner(owner);const spec=report.case;const receipts=[];for(const value of spec.actions||[]){const state=action(owner,value),result=value.checkpoint?checks(state,value.checkpoint):null;receipts.push({action:copy(value),state,checks:result});}
      const state=nativeRead(owner),result=checks(state,{...spec.expect,group:spec.group});return {id:spec.id,state,receipts,checks:result};},
    step(owner,index){assertOwner(owner);if(!Number.isSafeInteger(index)||index!==nextStep||index>=(report.case.actions||[]).length)throw Error('Ordered closed action required');const value=report.case.actions[nextStep++];return {action:copy(value),state:action(owner,value)};},
    checks,information,resourcePrecompute:precompute,resourceArm,resourceStage,
    resourceRead(owner){assertOwner(owner);const decision=copy(weatherDecision());return {counts:copy(counts),inputSignature:JSON.stringify({target:currentWeatherTarget(),current:selectedWeather(),track:weatherTrack,synthetic:weatherSynthetic,now:Date.now()}),decision};},
    resourceProbe(owner,iterations,kind='cached'){assertOwner(owner);if(!Number.isSafeInteger(iterations)||iterations<1||iterations>100000)throw Error('Bounded probe count required');
      if(kind==='cached'){let value;for(let i=0;i<iterations;i++)value=weatherDecision();return {count:iterations,last:copy(value),counts:copy(counts)};}
      if(!['tare','legacy'].includes(kind)||!resourceTape)throw Error('Unknown tare');let value;
      for(let i=0;i<iterations;i++){if(kind==='legacy'){const current=selectedWeather(),target=currentWeatherTarget();value=wxClass(gateWeatherCode(current?current.code:null,current,0));counts.legacySelection++;}else value=resourceTape.entries[0].decision;}
      return {count:iterations,last:copy(value),counts:copy(counts)};},
    strikeRead(owner){assertOwner(owner);return [...document.querySelectorAll('.flash,.bolt,.lightning,.boltline')].map(e=>{if(!strikeElementIds.has(e))strikeElementIds.set(e,++strikeElementSerial);return {elementId:strikeElementIds.get(e),class:e.className,opacity:+getComputedStyle(e).opacity,animations:e.getAnimations().map(a=>diagnosticTiming(a.effect))};});}
  });
})();
