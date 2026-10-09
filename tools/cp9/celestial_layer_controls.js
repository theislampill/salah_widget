// Explicit diagnostic interventions AFTER ordinary startup capture. Never used
// as repaired-product evidence. Every physical component uses one frozen frame.
async () => {
 const base=new URL('.',location.href),load=p=>import(new URL(p,base));
 const [{nativeAtmosphereFields},{encodeNativeFrame},{NativeForegroundCapture,nativeForeground},{nativeJob},{createSkyModel},{skyProjection},{projectPerspective}]=await Promise.all([
  load('real-sky/native-preview.mjs'),load('real-sky/native-encoding.mjs'),load('real-sky/native-composition.mjs'),load('real-sky/native-contract.mjs'),load('real-sky/core/src/sky-background.mjs'),load('real-sky/core/src/physical-sky-renderer.mjs'),load('real-sky/core/src/projection.mjs')]);
 const frame=window.realSkyFrame(),snapshot=window.SalahNativeSkyHost.capture(false);
 if(!frame?.raster)throw Error('A current full physical frame is required for component attribution');
 const r=frame.raster,job=nativeJob(snapshot,true),state=r.physicalState,view=job.options.view,residual=job.options.diffuse.residualNight;
 const grid=[Math.ceil(325/8),Math.ceil(530/8)],fields=nativeAtmosphereFields(state,r.atmosphere,view,residual,...grid);
 const withoutMoon=nativeAtmosphereFields({...state,moon:{...state.moon,altDeg:-90}},r.atmosphere,view,residual,...grid);
 const lunar=Float64Array.from(fields.background,(v,i)=>v-withoutMoon.background[i]);
 const noNatural=nativeAtmosphereFields({...state,moon:{...state.moon,altDeg:-90}},r.atmosphere,view,{...residual,zenithCdM2:0},...grid);
 const natural=Float64Array.from(withoutMoon.background,(v,i)=>v-noNatural.background[i]);
 const original=r.skyBackgroundLinear??r.backgroundLinear;
 let maxFieldDifference=0;for(let i=0;i<original.length;i++)maxFieldDifference=Math.max(maxFieldDifference,Math.abs(fields.background[i]-original[i]));
 const style=document.createElement('style'),canvas=document.createElement('canvas'),card=document.querySelector('.c');
 canvas.width=325;canvas.height=530;canvas.style='position:absolute;inset:0;width:100%;height:100%;z-index:0;border-radius:inherit;pointer-events:none';
 const ctx=canvas.getContext('2d'),capture=new NativeForegroundCapture(canvas);
 const cases=['full-control','no-native-solar-overlays','no-calendar-moon-and-optics','no-css-glass','recomposition-control','no-physical-lunar-field','no-residual-night-field','no-catalogue','no-registered-diffuse','no-native-clouds'];
 const css={
  'no-native-solar-overlays':'.atmo{visibility:hidden!important}',
  'no-calendar-moon-and-optics':'.sky .moon,.moon-detail-canvas{visibility:hidden!important}',
  'no-css-glass':'.scrim,.c::before,.c::after{display:none!important}.c{box-shadow:none!important}.times .p{background:none!important;box-shadow:none!important}',
 };
 function clear(){style.remove();canvas.remove();}
 function apply(name){
  clear();if(!cases.includes(name))throw Error('Unknown diagnostic control');
  if(name==='full-control')return;
  if(css[name]){style.textContent=css[name];document.head.append(style);return;}
  card.prepend(canvas);const foreground=capture.capture(530),linear=Float64Array.from(r.linear),gas=Float64Array.from(original);
  const remove=name==='no-physical-lunar-field'?lunar:name==='no-residual-night-field'?natural:name==='no-catalogue'?r.stellarLinear:name==='no-registered-diffuse'?r.diffuseLinear:null;
  if(remove)for(let i=0;i<linear.length;i++){linear[i]=Math.max(0,linear[i]-remove[i]);if(name==='no-physical-lunar-field'||name==='no-residual-night-field')gas[i]=Math.max(0,gas[i]-remove[i]);}
  if(name==='no-native-clouds')foreground.cloudRGBA=new Uint8ClampedArray(325*530*4);
  const joined=nativeForeground(linear,{...foreground,atmosphereLinear:gas,exposure:r.effectiveExposure});
  ctx.putImageData(new ImageData(encodeNativeFrame(joined.linear,r.effectiveExposure),325,530),0,0);
  style.textContent='.real-sky-canvas,.real-sky-preview{visibility:hidden!important}';document.head.append(style);
 }
 const box=el=>{const s=getComputedStyle(el),b=el.getBoundingClientRect();return {selector:el.className.baseVal??el.className,opacity:s.opacity,visibility:s.visibility,display:s.display,blend:s.mixBlendMode,filter:s.filter,rect:{x:b.x,y:b.y,width:b.width,height:b.height}};};
 const mapping=skyProjection(view),model=createSkyModel(state,r.atmosphere,{residualNight:residual});
 const probes=[[3,218],[160,80],[160,400]].map(([x,y])=>({pixel:[x,y],direction:mapping.unproject(x,y),components:model.sample(mapping.unproject(x,y)),solidAngle:mapping.solidAngle(x,y)}));
 window.__GlowControl={apply,clear};
 return {classification:'DIAGNOSTIC ONLY; frozen physical frame, same exposure, one removed component per image; ordinary composite retained separately',cases,frameUtcMs:frame.utcMs,snapshot,physicalState:state,view,atmosphere:r.atmosphere,exposure:r.effectiveExposure,nominalExposure:r.nominalExposure,display:r.displayPresentation??null,maxFieldDifference,projectedMoon:projectPerspective(state.moon,view),projectedSun:projectPerspective(state.sun,view),probes,opticalLayers:[...document.querySelectorAll('.atmo > *, .suncorner > *, .sunbody, .sky .moon > *, .moon-detail-canvas, .scrim')].map(box),rawFields:{backgroundMaximum:Math.max(...original.subarray(0,325*3)),lunarAtLeft:lunar[(218*325+3)*3],naturalAtLeft:natural[(218*325+3)*3]}};
}
