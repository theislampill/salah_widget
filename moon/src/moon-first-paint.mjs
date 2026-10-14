/* Bounded head composition. The caller supplies the existing admitted
 * head snapshot and native source-owner functions. This module has no clock,
 * ephemeris, phase atlas, terrain, asset wait, provider or DOM readiness gate.
 * support functions are the SAME moon-detail/native-encoding owners.
 */
function nativeHeadMoonGeometry(moon,dpr){
 if(!moon?.valid||!Number.isFinite(dpr)||dpr<.5||dpr>4)throw Error('Head Moon geometry');
 // .c has border-box325x530,border1; absolute inset0 children use323x528.
 // .sky explicitly says preserveAspectRatio="none", so scaling is anisotropic.
 // The source writes a transform rounded to .1/.001 before getScreenCTM().
 const innerWidth=323,innerHeight=528,originX=1,originY=1,sx=innerWidth/325,sy=innerHeight/530;
 const mx=Number(moon.x.toFixed(1)),my=Number(moon.y.toFixed(1)),scale=Number(moon.scale.toFixed(3));
 const x=originX+(mx-48*scale)*sx,y=originY+(my-48*scale)*sy,w=96*scale*sx,h=96*scale*sy;
 const left=Math.floor(x*dpr)-1,top=Math.floor(y*dpr)-1,width=Math.ceil((x+w)*dpr)-left+1,height=Math.ceil((y+h)*dpr)-top+1;
 if(width*height>1024*1024)throw Error('Head Moon viewport budget');
 const phaseDiameter=Math.ceil(Math.max(w,h)*dpr),maximumPhaseDiameter=Math.ceil(phaseDiameter*Math.max(1,MOON_SCALE_MAX/moon.scale));
 return {x,y,w,h,left,top,width,height,dpr,originX,originY,innerWidth,innerHeight,phaseDiameter,maximumPhaseDiameter,
  backgroundLeft:left/dpr-originX,backgroundTop:top/dpr-originY,backgroundWidth:width/dpr,backgroundHeight:height/dpr};
}

function composeNativeHeadMoon(preview,snapshot,sim,owner,support){
 if(!snapshot||snapshot.timeScale!==1||snapshot.paused||!Number.isFinite(snapshot.utcMs)||!Number.isFinite(snapshot.lat)||!Number.isFinite(snapshot.lon)||!Number.isFinite(snapshot.dpr))throw Error('Head Moon accepted input');
 if(!preview?.raster?.starPreview)throw Error('Head Moon needs admitted catalogue preview');
 const moon=owner.snapshot(new Date(snapshot.utcMs),snapshot.lat,snapshot.lon,sim),presentation=owner.presentation(moon,preview.raster.physicalState.sun.altDeg,false);
 if(!moon.valid)throw Error('Head Moon native snapshot');
 // Use the native style sink's existing .toFixed(3) opacity, not binary night.
 const opacity=Number(presentation.moonShow.toFixed(3));
 if(opacity<=0)return {visible:false,moon,presentation,snapshot};
 if(!support.initial)throw Error('Head Moon qualified initial unavailable');
 const g=nativeHeadMoonGeometry(moon,snapshot.dpr),capture={...snapshot,fraction:moon.frac,waxing:moon.waxing,up:moon.up,phaseDiameter:g.phaseDiameter,maximumPhaseDiameter:g.maximumPhaseDiameter,
  phaseQuantum:support.phaseQuantum(g.phaseDiameter),physicalFraction:support.canonicalFraction(moon.frac,g.phaseDiameter)};
 const scene=owner.scene(capture,support.profile),result=support.initial.render(scene);
 const table=support.prefixSurface({size:result.surfaceSize,linear:result.surfaceLinear,coverage:result.surfaceCoverage});
 const calendar=support.prefixSurface({size:result.surfaceSize,linear:result.calendarLinear,coverage:result.surfaceCoverage});
 const r=preview.raster,E=r.effectiveExposure,sky=r.skyBackgroundLinear??r.backgroundLinear,stars=r.stellarLinear,diffuse=r.diffusePhysicalLinear;
 const W=g.width,H=g.height,linear=new Float64Array(W*H*3),covered=new Uint8Array(W*H);
 const ss=result.surfaceSize/(.96*result.surfaceExtent),ox=result.surfaceSize/2-.5*ss,oy=ox;
 const stepX=ss/(g.w*g.dpr),stepY=ss/(g.h*g.dpr),startX=((g.left/g.dpr-g.x)/g.w)*ss+ox,startY=((g.top/g.dpr-g.y)/g.h)*ss+oy;
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){
  const i=y*W+x,x0=startX+x*stepX,y0=startY+y*stepY,x1=x0+stepX,y1=y0+stepY;
  const sp=support.boxSurface(moon.up===0?calendar:table,x0,y0,x1,y1),a=sp[3];if(a<=1e-10)continue;covered[i]=1;
  if(moon.up>0&&moon.up<1){const token=support.boxSurface(calendar,x0,y0,x1,y1);for(let k=0;k<3;k++)sp[k]=moon.up*sp[k]+(1-moon.up)*token[k];}
  const px=((g.left+x+.5)/g.dpr-g.originX)*r.width/g.innerWidth-.5,py=((g.top+y+.5)/g.dpr-g.originY)*r.height/g.innerHeight-.5;
  const gas=support.sampleField(sky,r.width,r.height,px,py),direct=support.sampleField(stars,r.width,r.height,px,py),d=support.sampleField(diffuse,r.width,r.height,px,py);
  // Same native detail join: gas stays foreground; opaque lunar coverage
  // removes direct catalogue/diffuse light even during calendar emphasis.
  linear.set(support.joinLunarPixel({gas,direct:direct.map((v,k)=>v+d[k]),premult:sp,coverage:a,opacity,cloud:[0,0,0,0],exposure:E}),3*i);
 }
 const rgba=support.encode(linear,E);for(let i=0;i<covered.length;i++)rgba[4*i+3]=covered[i]?255:0;
 return {visible:true,moon,presentation,snapshot,capture,scene,result,geometry:g,rgba,quality:'initial-v5'};
}

// Keep the existing325x530 atmosphere/catalogue dataURL as the second layer.
// The first layer is only the device-resolution local lunar patch. This uses
// default padding-box background origin, same as the absolute-child origin.
function nativeHeadMoonBackgroundRule(backgroundUrl,moonUrl,prepared){
 const p=prepared.presentation,permission='--moongrp:'+p.moonShow.toFixed(3)+';--moonfeat:1;--moonocc:1;--moonbeam:'+(0.6*p.moonlight).toFixed(3)+';';
 if(!prepared.visible)return '.c,.c.sky-pending{background-image:url("'+backgroundUrl+'");background-size:100% 100%;background-repeat:no-repeat;'+permission+'}';
 const g=prepared.geometry;
 return '.c,.c.sky-pending{background-image:url("'+moonUrl+'"),url("'+backgroundUrl+'");background-size:'+g.backgroundWidth+'px '+g.backgroundHeight+'px,100% 100%;background-position:'+g.backgroundLeft+'px '+g.backgroundTop+'px,0 0;background-repeat:no-repeat,no-repeat;background-origin:padding-box;'+permission+'}';
}
