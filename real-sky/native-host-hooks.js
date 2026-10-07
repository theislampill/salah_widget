// CP8 host owns time/config/weather acceptance; the optional renderer only reads this boundary.
// CP9: independent custody of an elevation admitted for this exact native target.
// The native legacy scalar is not reused as accepted astronomical metadata.
let _cp9SiteElevation=null;
window.SalahNativeSkyHost=Object.freeze({
 acceptedElevation(heightM,generation,latitude,longitude){
  if(typeof heightM!=='number'||!Number.isFinite(heightM)||heightM<-500||heightM>10000||generation!==_runtimeGeneration||latitude!==lat||longitude!==lon)return false;
  _cp9SiteElevation=Object.freeze({heightM,generation,lat:latitude,lon:longitude});return true;
 },
 lunarSurface(){return window.SalahMoonRuntime?.surface()??((_pbrReady||_moonFallbackReady)?_moonCv:null);},
 capture(){
  const identity=simulationReady()?skySceneIdentity():null;
  const cw=selectedWeather();
  const elevation=cw&&_cp9SiteElevation&&_cp9SiteElevation.generation===_runtimeGeneration&&_cp9SiteElevation.lat===lat&&_cp9SiteElevation.lon===lon?_cp9SiteElevation:null;
  const cameraNumber=(name,fallback)=>q.has(name)?(q.get(name).trim()===''?NaN:Number(q.get(name))):fallback;
  return {utcMs:simNow(),lat,lon,heightM:elevation?.heightM??0,elevationSource:elevation?'native response elevation bound to this target generation':'default zero; no bound eligible weather height',elevationOwner:elevation?{...elevation}:null,generation:_runtimeGeneration,sceneIdentity:identity,
   tz,timeScale:TIMESCALE,units,lp:LPOLL,reducedMotion:isMotionReduced(),paused:document.hidden||!!$('.c')?.classList.contains('paused'),
   camera:{azDeg:cameraNumber('skyAz',180),altDeg:cameraNumber('skyAlt',45),fovYDeg:cameraNumber('skyFov',90),rollDeg:cameraNumber('skyRoll',0)},allowEstimates:q.get('skyEstimates')!=='off',
   weather:cw?{src:cw.src??'accepted-native',temp:cw.temp??null,rh:cw.rh??null,vis:cw.vis??null,cloud:cw.cloud??null,code:cw.code??null,wind:cw.wind??null}:null,
   prayerReady:!!today,moonReady:!!(window.SalahMoonRuntime?.surface()||_pbrReady||_moonFallbackReady),pbrFailed:_pbrFailed};
 },
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
