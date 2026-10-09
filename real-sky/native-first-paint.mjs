import {renderNativeBackgroundPreview} from './native-preview.mjs';
import {encodeNativeFrame} from './native-encoding.mjs';
import {joinNativeStarPreview} from './native-star-preview.mjs';

/** Run in the head, before the card's HTML can be painted. This is a bounded
 * coherent atmosphere/catalogue/Moon scene: no hidden card, timer, asset
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
  generation:0,sceneIdentity:[c.lat,c.lon,c.tz||'America/New_York','wall'].join('|'),tz:c.tz||'America/New_York',timeScale:1,units:c.units,lp:c.lp||0,dpr:Math.max(.5,Math.min(4,devicePixelRatio||1)),
  reducedMotion:params.get('motion')!=='full'&&matchMedia('(prefers-reduced-motion: reduce)').matches,paused:false,
  camera:{azDeg:number('skyAz',180),altDeg:number('skyAlt',45),fovYDeg:number('skyFov',90),rollDeg:number('skyRoll',0)},allowEstimates:params.get('skyEstimates')!=='off',weather:null};
 try{
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
  let moonUrl='';
  if(moon.visible){
   const local=document.createElement('canvas');local.width=moon.geometry.width;local.height=moon.geometry.height;
   local.getContext('2d').putImageData(new ImageData(moon.rgba,local.width,local.height),0,0);moonUrl=local.toDataURL();
  }
  const style=document.createElement('style');style.id='native-first-paint';
  style.textContent=window.SalahMoonHead.backgroundRule(cv.toDataURL(),moonUrl,moon);document.head.append(style);
  window.SalahFirstPaint={value:p,snapshot,moon,preparedAt:performance.now()};
 }catch(e){window.SalahFirstPaint={error:String(e.message??e)};}
}
