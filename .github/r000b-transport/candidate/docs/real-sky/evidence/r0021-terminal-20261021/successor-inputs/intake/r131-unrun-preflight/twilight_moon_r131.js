// Diagnostic after the unchanged ordinary twilight observation. No physical,
// geometry, light, scene or clock input changes; hidden-layer crops are labelled.
async () => {
 const frame=window.realSkyFrame(),moon=document.querySelector('.moon-detail-canvas'),sky=document.querySelector('.real-sky-canvas');
 if(!frame?.raster||!moon||!sky)throw Error('Current refined composition required');
 const box=e=>{const s=getComputedStyle(e);return {rect:e.getBoundingClientRect().toJSON(),opacity:s.opacity,visibility:s.visibility,display:s.display,blend:s.mixBlendMode,zIndex:s.zIndex,filter:s.filter};};
 const mp=moon.getContext('2d').getImageData(0,0,moon.width,moon.height),sp=sky.getContext('2d').getImageData(0,0,sky.width,sky.height);
 const mr=moon.getBoundingClientRect(),sr=sky.getBoundingClientRect();
 let opaque=0,partial=0,zero=0,maxRgb=0,totalRgb=0,nonzero=0;const histogram={};
 for(let y=0;y<moon.height;y++)for(let x=0;x<moon.width;x++){
  const i=4*(y*moon.width+x),a=mp.data[i+3];if(!a){zero++;continue;}if(a===255)opaque++;else partial++;
  // This is a nearest source-buffer probe, not an exact display subtraction:
  // browser resampling, UI/glass and evolving on-screen frames are separate.
  const sx=Math.floor((mr.x+(x+.5)*mr.width/moon.width-sr.x)*sky.width/sr.width),sy=Math.floor((mr.y+(y+.5)*mr.height/moon.height-sr.y)*sky.height/sr.height);
  if(sx<0||sy<0||sx>=sky.width||sy>=sky.height)continue;
  const j=4*(sy*sky.width+sx);let d=0;for(let k=0;k<3;k++)d=Math.max(d,Math.abs(mp.data[i+k]-sp.data[j+k]));
  histogram[d]=(histogram[d]||0)+1;maxRgb=Math.max(maxRgb,d);totalRgb+=d;if(d)nonzero++;
 }
 const style=document.createElement('style'),cases=['full-control','hidden-detail-only','hidden-calendar-all'];
 function clear(){style.remove();}
 function apply(name){clear();if(!cases.includes(name))throw Error('Unknown control');if(name==='full-control')return;style.textContent=name==='hidden-detail-only'?'.moon-detail-canvas{visibility:hidden!important}':'.moon-detail-canvas,.sky .moon{visibility:hidden!important}';document.head.append(style);}
 window.__GlowControl={apply,clear};
 return {classification:'DIAGNOSTIC, not product output or continuous evidence. Hiding only labels layer influence; nearest buffer differences do not prove display contrast.',cases,frameUtcMs:frame.utcMs,physicalState:frame.raster.physicalState,exposure:frame.raster.effectiveExposure,native:window.SalahNativeSkyHost.capture(false),moonState:window.SalahMoonRuntime.state,presentationUp:window.SalahMoonRuntime.presentationUp,layers:{detail:box(moon),sky:box(sky),group:box(document.querySelector('.moon')),features:box(document.querySelector('.mfeatures')),mask:box(document.querySelector('.moon-mask-disc'))},buffers:{moon:{width:moon.width,height:moon.height,png:moon.toDataURL('image/png')},sky:{width:sky.width,height:sky.height,png:sky.toDataURL('image/png')}},probe:{opaque,partial,zero,maxRgb,totalRgb,nonzero,histogram}};
}
