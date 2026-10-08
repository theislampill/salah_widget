// CP8 host owns time/config/weather acceptance; the optional renderer only reads this boundary.
// CP9: independent custody of an elevation admitted for this exact native target.
// The native legacy scalar is not reused as accepted astronomical metadata.
let _cp9SiteElevation=null;
window.SalahNativeSkyHost=Object.freeze({
 acceptedElevation(heightM,generation,latitude,longitude){
  if(typeof heightM!=='number'||!Number.isFinite(heightM)||heightM<-500||heightM>10000||generation!==_runtimeGeneration||latitude!==lat||longitude!==lon)return false;
  _cp9SiteElevation=Object.freeze({heightM,generation,lat:latitude,lon:longitude});return true;
 },
 lunarSurface(){return window.SalahMoonRuntime?.surface()??null;},
 cloudLighting(){return window.SalahNativeCloudLighting?.(this.capture(false))??null;},
 capture(includePresentation=true){
  const identity=simulationReady()?skySceneIdentity():null;
  const cw=selectedWeather();
  const elevation=cw&&_cp9SiteElevation&&_cp9SiteElevation.generation===_runtimeGeneration&&_cp9SiteElevation.lat===lat&&_cp9SiteElevation.lon===lon?_cp9SiteElevation:null;
  const cameraNumber=(name,fallback)=>q.has(name)?(q.get(name).trim()===''?NaN:Number(q.get(name))):fallback;
  const card=$('.c');let solarAnchor=null;
  // Cloud lighting consumes physical direction, never decorative-body layout.
  // Avoid forcing CSS layout on every native cloud/atmosphere update. The
  // default renderer boundary still measures the actually presented body.
  if(includePresentation){
  const body=$('.sunbody'),attached=$('.suncorner'),sx=parseFloat(card?.style.getPropertyValue('--sunx2')),sy=parseFloat(card?.style.getPropertyValue('--sunlift'));
  // The native transform is eased by CSS. Register attached light to the
  // centre actually presented now, not the future --sunlift target. This is
  // presentation metadata only; no astronomical UTC/identity is substituted.
  const br=body?.getBoundingClientRect?.(),vr=($('.real-sky-canvas')??$('.real-sky-preview'))?.getBoundingClientRect?.();
  const actual=br&&vr&&vr.width>0&&vr.height>0&&Number.isFinite(br.left)&&Number.isFinite(br.top)?{x:(br.left+br.width/2-vr.left)*325/vr.width,y:(br.top+br.height/2-vr.top)*530/vr.height}:null;
  const presence=attached&&typeof getComputedStyle==='function'?Number(getComputedStyle(attached).opacity):null;
  solarAnchor=Number.isFinite(sx)&&Number.isFinite(sy)?{...(actual??{x:sx,y:sy}),...(Number.isFinite(presence)?{presence}: {})}:null;
  }
  return {utcMs:simNow(),lat,lon,heightM:elevation?.heightM??0,elevationSource:elevation?'native response elevation bound to this target generation':'default zero; no bound eligible weather height',elevationOwner:elevation?{...elevation}:null,generation:_runtimeGeneration,sceneIdentity:identity,
   tz,timeScale:TIMESCALE,units,lp:LPOLL,reducedMotion:isMotionReduced(),paused:document.hidden||!!$('.c')?.classList.contains('paused'),
   camera:{azDeg:cameraNumber('skyAz',180),altDeg:cameraNumber('skyAlt',45),fovYDeg:cameraNumber('skyFov',90),rollDeg:cameraNumber('skyRoll',0)},allowEstimates:q.get('skyEstimates')!=='off',
   weather:cw?{src:cw.src??'accepted-native',temp:cw.temp??null,rh:cw.rh??null,vis:cw.vis??null,cloud:cw.cloud??null,code:cw.code??null,wind:cw.wind??null}:null,
   solarAnchor,
   prayerReady:!!today,moonReady:!!window.SalahMoonRuntime?.surface(),pbrFailed:_pbrFailed};
 },
 // Preview has its own accepted-input/expiry check on every animation frame.
 // A synchronous second producer here ran during native paint, before clouds,
 // then repeated in that same frame at high rates. Bootstrap still paints
 // immediately; target changes remain fenced by beginSkyScene and preview rAF.
 notify(){window.SalahRealSky?.request();}
});
// CP9 additive diagnostic join, adopted from the donor's native-QA integration.
// Original prayer/weather/calendar fields remain untouched; this is not render authority.
if(typeof window.qaState==='function'){
 const nativeQA=window.qaState;
 window.qaState=function(...args){
  const original=nativeQA.apply(this,args);let realSky;
  try{const s=window.realSkyState?.();realSky=s?{checkpoint:s.checkpoint,status:s.status,renders:s.renders,frameUtcMs:s.last?.utcMs??null,catalogue:s.last?.catalogue??null,generation:s.last?.native?.generation??null,assumptions:s.last?.native?.assumptions??null,composition:s.last?.composition??null,errors:s.errors??[]}:{checkpoint:'9',status:'loading',frameUtcMs:null};}
  catch(e){realSky={checkpoint:'9',status:'unavailable',frameUtcMs:null,error:String(e?.message??e)};}
  const m=window.SalahMoonRuntime?.state;
  const moonRenderer=m?{backend:m.backend,status:m.status,quality:m.quality,legacyFallback:m.legacyFallback,currentNativeFraction:m.currentNativeFraction,renderedFraction:m.accepted?.scene?.fraction??null,calendarProxyWeight:m.calendarProxyWeight,profile:m.accepted?.profile??null,errors:m.errors}:null;
  return {...original,realSky,moonRenderer,legacySyntheticStarTelemetry:{active:false,replacement:'realSky; raster diagnostics, not old synthetic DOM arrays'}};
 };
}
