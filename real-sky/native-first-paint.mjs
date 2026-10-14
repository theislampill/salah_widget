import {renderNativeBackgroundPreview} from './native-preview.mjs';
import {encodeNativeFrame} from './native-encoding.mjs';
import {joinNativeStarPreview} from './native-star-preview.mjs';
import {nativeIdentity,nativeResultCurrent} from './native-contract.mjs';

// The static head image has the same authority and original age fence as the
// native preview. The existing lunar poll owns checks; this adds no timer or
// celestial clock. Retired snapshots remain diagnostic, never reusable pixels.
const nativeFirstPaintOwners=new WeakMap();
function getNativeFirstPaintOwner(){
 const page=window;let owner=nativeFirstPaintOwners.get(page);
 if(!owner){owner=createNativeFirstPaintOwner(page);nativeFirstPaintOwners.set(page,owner);}
 return owner;
}
function createNativeFirstPaintOwner(window){
 const {document,location,performance,Date}=window;
 const matchMedia=query=>window.matchMedia(query);
 let active=null,history=null;
 const dpr=()=>Math.max(.5,Math.min(4,window.devicePixelRatio||1));
 function headSnapshot(params=new URLSearchParams(location.hash.slice(1))){
  if(['simTime','simDate','timeScale'].some(k=>params.has(k)))return null;
  const c=window.SalahConfig?.resolve(location.hash)?.cfg;
  if(!c||!Number.isFinite(c.lat)||!Number.isFinite(c.lon))return null;
  const number=(key,fallback)=>params.has(key)?Number(params.get(key)):fallback;
  return {utcMs:Date.now(),lat:c.lat,lon:c.lon,heightM:0,elevationSource:'default zero; no bound eligible weather height',elevationOwner:null,
   generation:0,sceneIdentity:[c.lat,c.lon,c.tz||'America/New_York','wall'].join('|'),tz:c.tz||'America/New_York',timeScale:1,units:c.units,lp:c.lp||0,dpr:dpr(),
   reducedMotion:params.get('motion')!=='full'&&matchMedia('(prefers-reduced-motion: reduce)').matches,paused:document.hidden,
   camera:{azDeg:number('skyAz',180),altDeg:number('skyAlt',45),fovYDeg:number('skyFov',90),rollDeg:number('skyRoll',0)},allowEstimates:params.get('skyEstimates')!=='off',weather:null};
 }
 function currentSnapshot(){
  const host=window.SalahNativeSkyHost;
  const s=host?host.capture(false):headSnapshot();return s?{...s,dpr:dpr()}:null;
 }
 function admitNative(snapshot,source){
  if(!window.SalahStartupTiming)return null;
  try{
   const s={...snapshot,dpr:dpr()},configIdentity=nativeIdentity(s);
   if(s.paused||document.hidden)return null;
   const admissionId=window.SalahStartupTiming.admit(s,source,configIdentity);
   return admissionId?{admissionId,snapshot:structuredClone(s),source,configIdentity}:null;
  }catch{return null;}
 }
 function stage(kind,link,details={}){try{if(link)window.SalahStartupTiming?.stage(kind,{...link,...details});}catch{/* Diagnostics cannot grant or veto presentation. */}}
 function revoke(reason,status='withdrawn'){
  if(!active)return false;
  document.querySelector('#native-first-paint')?.remove();
  history={...history,active:false,status,reason,retiredAt:performance.now()};
  window.SalahFirstPaint={snapshot:structuredClone(history.snapshot),preparedAt:history.preparedAt,firstAdmission:structuredClone(history.firstAdmission),value:null,moon:null,status,reason};
  active=null;return false;
 }
 function invalidReason(s){
  if(!active)return 'head image retired';
  if(document.hidden||!s||s.paused)return 'native target unavailable or hidden';
  if(location.hash!==active.hash)return 'native configuration changed';
  if(s.dpr!==active.snapshot.dpr)return 'native device geometry changed';
  if(!nativeResultCurrent(active.job,s))return 'native head target changed or expired';
  // Use the native ordinary input, never performance time as astronomical UTC.
  // The unchanged native lunar 1s discontinuity test is measured from admission.
  if(Math.abs((s.utcMs-active.snapshot.utcMs)-(performance.now()-active.startedAt)*(active.snapshot.timeScale??1))>1000)return 'native clock discontinuity';
  if(active.lunar&&!window.SalahMoonRuntime?.headCurrent(active.lunar,s))return 'native head lunar geometry or presentation changed';
  return null;
 }
 function check(reason='native head currentness',snapshot=null){
  if(!active)return false;
  try{const why=invalidReason(snapshot?{...snapshot,dpr:dpr()}:currentSnapshot());return why?revoke(why):true;}
  catch{return revoke(reason+' unavailable');}
 }
 window.SalahFirstPaintLifecycle={check,current(snapshot){return check('native preview read',snapshot);},
  invalidate(reason='native invalidation'){
   // Native initialization revokes its own pending work, but a checked early
   // scene may bridge that SAME target until the real preview publishes.
   if(reason==='native beginSkyScene'&&window.SalahNativeSkyHost&&window.SalahMoonHost){
    try{if(window.SalahMoonHost.capture().presentationReady===false&&check(reason))return true;}catch{/* Invalid input withdraws below. */}
   }
   return revoke(reason);
  },retire(reason='native preview published'){return revoke(reason,'handed-off');},admitNative,
  takeInitial(snapshot,scene){
   // The head result is private numerical data, not a new target or epoch.
   // Prove the ORIGINAL head scene before releasing it once to native adoption.
   if(history?.status!=='published'||!active?.initial||!check('native initial reuse',snapshot))return null;
   const cached=active.initial;active.initial=null;
   const identity=cached.owner.identity,computed=cached.result.scene;
   if(cached.owner!==window.SalahMoonInitial||identity?.schema!=='moon-initial-receivers/1'||
      typeof identity.sha256!=='string'||!/^[0-9a-f]{64}$/.test(identity.sha256)||cached.result.kind!=='initial'||
      cached.result.diagnostics?.quality?.status!=='initial-v5'||
      cached.result.diagnostics?.receiverIdentity!==identity.sha256||
      !cached.result.physicalIdentity?.startsWith(identity.sha256+'|')||
      cached.result.profileIdentity!==JSON.stringify(scene?.profile)||
      ['mode','size','outSize','diameter','distance','extent','tilt'].some(k=>computed[k]!==scene?.[k])||
      JSON.stringify(computed.basis)!==JSON.stringify(scene?.basis)||JSON.stringify(computed.earth)!==JSON.stringify(scene?.earth))return null;
   return cached.result;
  },
  nativeAdopted(link){
   try{const current=currentSnapshot();if(link&&!document.hidden&&!current?.paused&&link.configIdentity===nativeIdentity(current))stage('native-adoption',link);}catch{/* Missing diagnostics cannot change the adopted scene. */}
  },
  get state(){return history?structuredClone(history):{active:false,status:'not-admitted'};}
 };
 window.addEventListener('hashchange',()=>check('native hash target changed'));
 return {headSnapshot,begin(snapshot){
   if(active)revoke('head preparation replaced');
   const configIdentity=nativeIdentity(snapshot),startedAt=performance.now(),link=admitNative(snapshot,'head');
   const firstAdmission={snapshot:structuredClone(snapshot),configIdentity,at:startedAt,admissionId:link?.admissionId??null};
   active={snapshot:structuredClone(snapshot),hash:location.hash,startedAt,job:{native:{identity:configIdentity},observer:{utcMs:snapshot.utcMs}},lunar:null,link};
   history={active:true,status:'computing',snapshot:structuredClone(snapshot),firstAdmission,preparedAt:null};
   window.SalahFirstPaint={snapshot:structuredClone(snapshot),firstAdmission:structuredClone(firstAdmission),value:null,moon:null,preparedAt:null};
   stage('head-work-start',link);return snapshot;
  },lunar(moon,sim,sunAltitude){
   if(active)active.lunar=structuredClone({visible:moon.visible,capture:moon.capture?{...moon.capture,profileMode:'calendar',referenceIdentity:null}:null,scene:moon.scene,geometry:moon.geometry,sim,sunAltitude,presentation:moon.presentation});
  },published(value,moon,style){
   if(!check('head publication')){stage('head-work-end',history?.firstAdmission?.admissionId?{admissionId:history.firstAdmission.admissionId,snapshot:history.snapshot,source:'head',configIdentity:history.firstAdmission.configIdentity}:null,{status:'superseded',reason:history?.reason});if(history)history.status='superseded';return false;}
   // Keep the genuine renderer's arrays private. Diagnostic reads receive an
   // isolated copy. Mutating public diagnostic data cannot change the owned
   // one-shot handoff. Metadata and local RGBA are detached before publication.
   const {result,...moonMetadata}=moon,publicMoon=structuredClone(moonMetadata);
   if(result){
    // The producer shares its constructor coverage with later render results;
    // detach that one array too. Other surface/output arrays are render-local.
    const owned={...result,surfaceCoverage:result.surfaceCoverage.slice(),scene:structuredClone(result.scene),diagnostics:structuredClone(result.diagnostics)};
    active.initial={owner:window.SalahMoonInitial,result:owned};
    Object.defineProperty(publicMoon,'result',{enumerable:true,get:()=>structuredClone(owned)});
   }
   if(!check('head initial ownership publication')){stage('head-work-end',history?.firstAdmission?.admissionId?{admissionId:history.firstAdmission.admissionId,snapshot:history.snapshot,source:'head',configIdentity:history.firstAdmission.configIdentity}:null,{status:'superseded',reason:history?.reason});if(history)history.status='superseded';return false;}
   document.head.append(style);history.status='published';history.preparedAt=performance.now();
   window.SalahFirstPaint={value,snapshot:structuredClone(active.snapshot),moon:publicMoon,preparedAt:history.preparedAt,firstAdmission:structuredClone(history.firstAdmission)};
   stage('head-work-end',active.link,{status:'published'});return true;
  },error(error){const link=active?.link,message=String(error.message??error);revoke(message,'error');window.SalahFirstPaint={...window.SalahFirstPaint,error:message};stage('head-work-end',link,{status:'error',reason:message});}
 };
}

/** Run in the head, before the card's HTML can be painted. This is a bounded
 * coherent atmosphere/catalogue/Moon scene: no hidden card, timer, asset
 * request, provider wait or independent clock. The shared configuration resolver
 * admits the site and Date.now is the native ordinary wall-clock input. Explicit
 * temporal previews are left to the existing native temporal owner. */
export function prepareNativeFirstPaint(){
 // Install exactly one page owner even when head rendering is excluded. Its
 // native admission hooks remain available to the existing temporal owner.
 const nativeFirstPaintOwner=getNativeFirstPaintOwner();
 const params=new URLSearchParams(location.hash.slice(1));
 const snapshot=nativeFirstPaintOwner.headSnapshot(params);if(!snapshot||snapshot.paused)return;
 try{
  nativeFirstPaintOwner.begin(snapshot);
  let p=renderNativeBackgroundPreview(snapshot);
  const cv=document.createElement('canvas');cv.width=325;cv.height=530;
  let bytes=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure);
  const catalogue=window.SalahStarBootstrap;
  if(catalogue){const stars=catalogue.render(p.job,p.raster.physicalState,{background:bytes,exposure:p.raster.effectiveExposure});p=joinNativeStarPreview(p,bytes,stars);bytes=p.rgba;}
  cv.getContext('2d').putImageData(new ImageData(bytes,325,530),0,0);
  // Match the native SIM owner's four lunar parameter names; temporal previews
  // still belong wholly to its existing clock and are excluded above.
  const sim={moon:params.get('simMoon'),wax:params.get('simWax'),moonAlt:params.get('simMoonAlt'),moonH:params.get('simMoonH')};
  const moon=window.SalahMoonHead.compose(p,snapshot,sim,encodeNativeFrame);
  nativeFirstPaintOwner.lunar(moon,sim,p.raster.physicalState.sun.altDeg);
  let moonUrl='';
  if(moon.visible){
   const local=document.createElement('canvas');local.width=moon.geometry.width;local.height=moon.geometry.height;
   local.getContext('2d').putImageData(new ImageData(moon.rgba,local.width,local.height),0,0);moonUrl=local.toDataURL();
  }
  const style=document.createElement('style');style.id='native-first-paint';
  style.textContent=window.SalahMoonHead.backgroundRule(cv.toDataURL(),moonUrl,moon);nativeFirstPaintOwner.published(p,moon,style);
 }catch(e){nativeFirstPaintOwner.error(e);}
}
