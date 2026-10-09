import {renderNativeBackgroundPreview} from './native-preview.mjs';
import {encodeNativeFrame} from './native-encoding.mjs';
import {joinNativeStarPreview} from './native-star-preview.mjs';

/** Run in the head, before the card's HTML can be painted. This is a bounded
 * atmospheric background, NOT a readiness gate: no hidden card, timer, asset
 * request, provider wait or independent clock. The shared configuration resolver
 * admits the site and Date.now is the native ordinary wall-clock input. Explicit
 * temporal previews are left to the existing native temporal owner. */
export function prepareNativeFirstPaint(){
 const params=new URLSearchParams(location.hash.slice(1));
 if(['simTime','simDate','timeScale'].some(k=>params.has(k)))return;
 const resolved=window.SalahConfig?.resolve(location.hash),c=resolved?.cfg;
 if(!c||!Number.isFinite(c.lat)||!Number.isFinite(c.lon))return;
 const number=(key,fallback)=>params.has(key)?Number(params.get(key)):fallback;
 const snapshot={utcMs:Date.now(),lat:c.lat,lon:c.lon,heightM:0,elevationSource:'default zero; no bound eligible weather height',elevationOwner:null,
  generation:0,sceneIdentity:[c.lat,c.lon,c.tz||'America/New_York','wall'].join('|'),tz:c.tz||'America/New_York',timeScale:1,units:c.units,lp:c.lp||0,
  reducedMotion:params.get('motion')!=='full'&&matchMedia('(prefers-reduced-motion: reduce)').matches,paused:false,
  camera:{azDeg:number('skyAz',180),altDeg:number('skyAlt',45),fovYDeg:number('skyFov',90),rollDeg:number('skyRoll',0)},allowEstimates:params.get('skyEstimates')!=='off',weather:null};
 try{
  let p=renderNativeBackgroundPreview(snapshot);
  const cv=document.createElement('canvas');cv.width=325;cv.height=530;
  let bytes=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure);
  const catalogue=window.SalahStarBootstrap;
  if(catalogue){const stars=catalogue.render(p.job,p.raster.physicalState,{background:bytes,exposure:p.raster.effectiveExposure});p=joinNativeStarPreview(p,bytes,stars);bytes=p.rgba;}
  cv.getContext('2d').putImageData(new ImageData(bytes,325,530),0,0);
  const style=document.createElement('style');style.id='native-first-paint';
  // The raw HTML must not expose a default night Moon at an accepted daytime
  // site. The native painter supplies the detailed body/weather terms at boot.
  style.textContent='.c{background-image:url("'+cv.toDataURL()+'");background-size:100% 100%;--moon:'+(p.raster.physicalState.sun.altDeg>0?0:1)+'}';document.head.append(style);
  window.SalahFirstPaint={value:p,snapshot,preparedAt:performance.now()};
 }catch(e){window.SalahFirstPaint={error:String(e.message??e)};}
}
