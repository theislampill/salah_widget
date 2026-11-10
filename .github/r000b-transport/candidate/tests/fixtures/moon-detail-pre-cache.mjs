/** DPR-aware local lunar join. Physics stays in the existing sky raster; only
 * the lunar region is sampled at device resolution. No UI-thread terrain solver.
 * Native cloud pixels use the same bounded display-transfer owner as the sky.
 */
function prefixSurface({size,linear,coverage}){
 if(!Number.isInteger(size)||size<1||size>768||linear?.length!==size*size*3||coverage?.length!==size*size)throw new RangeError('surface prefix shape');
 const stride=size+1,data=new Float64Array(stride*stride*4);
 for(let y=0;y<size;y++){
  const row=[0,0,0,0];
  for(let x=0;x<size;x++){
   const i=y*size+x,a=coverage[i];if(!Number.isFinite(a)||a<0||a>1)throw new RangeError('surface coverage');
   const c=[linear[3*i],linear[3*i+1],linear[3*i+2],a];
   for(let k=0;k<4;k++){if(!Number.isFinite(c[k])||c[k]<0||(k<3&&c[k]>a+1e-6))throw new RangeError('premultiplied display surface');row[k]+=c[k];data[4*((y+1)*stride+x+1)+k]=data[4*(y*stride+x+1)+k]+row[k];}
  }
 }return {size,stride,data};
}
function integral(p,x,y,k){
 x=Math.max(0,Math.min(p.size,x));y=Math.max(0,Math.min(p.size,y));
 const ix=Math.min(p.size-1,Math.floor(x)),iy=Math.min(p.size-1,Math.floor(y)),fx=x-ix,fy=y-iy,s=p.stride,d=p.data;
 return d[4*(iy*s+ix)+k]*(1-fx)*(1-fy)+d[4*(iy*s+ix+1)+k]*fx*(1-fy)+d[4*((iy+1)*s+ix)+k]*(1-fx)*fy+d[4*((iy+1)*s+ix+1)+k]*fx*fy;
}
function boxSurface(p,x0,y0,x1,y1){
 const area=(x1-x0)*(y1-y0);if(![x0,y0,x1,y1].every(Number.isFinite)||area<=0||x1<=x0||y1<=y0)throw new RangeError('surface box');
 const out=[0,0,0,0];for(let k=0;k<4;k++)out[k]=Math.max(0,(integral(p,x1,y1,k)-integral(p,x0,y1,k)-integral(p,x1,y0,k)+integral(p,x0,y0,k))/area);
 if(out[3]>1+1e-8)throw new Error('area coverage out of range');out[3]=Math.min(1,out[3]);return out;
}
function sampleField(field,W,H,x,y){
 if(!field)return [0,0,0];x=Math.max(0,Math.min(W-1,x));y=Math.max(0,Math.min(H-1,y));const ix=Math.floor(x),iy=Math.floor(y),jx=Math.min(ix+1,W-1),jy=Math.min(iy+1,H-1),fx=x-ix,fy=y-iy,r=[0,0,0];
 for(let k=0;k<3;k++)r[k]=field[3*(iy*W+ix)+k]*(1-fx)*(1-fy)+field[3*(iy*W+jx)+k]*fx*(1-fy)+field[3*(jy*W+ix)+k]*(1-fx)*fy+field[3*(jy*W+jx)+k]*fx*fy;return r;
}
function joinLunarPixel({gas,direct,premult,coverage:a,opacity,cloud,exposure}){
 if(!Number.isFinite(a)||a<0||a>1||!Number.isFinite(opacity)||opacity<0||opacity>1||!Number.isFinite(exposure)||exposure<=0)throw new RangeError('lunar join');
 const ma=a*opacity,ca=cloud[3],out=[0,0,0];
 for(let k=0;k<3;k++){
  const surface=a>0?Math.max(0,Math.min(1-1/131072,premult[k]/a)):0;
  // Gas is foreground atmospheric path radiance, not distant background.
  // Opaque terrain blocks stars/diffuse sources, never the air in front of it.
  // Calendar opacity scales surface emphasis only; it cannot grant star leaks.
  const beforeCloud=gas[k]+direct[k]*(1-a)+(-Math.log1p(-surface)/exposure)*ma;
  out[k]=beforeCloud*(1-ca)+cloud[k]*ca;
 }return out;
}
function startMoonDetail(){
 let table=null,calendarTable=null,surface=null,last=null,prepared=null,disposed=false;
 const cv=document.createElement('canvas'),cloudCv=document.createElement('canvas');cv.className='moon-detail-canvas';cv.setAttribute('aria-hidden','true');
 Object.assign(cv.style,{position:'absolute',pointerEvents:'none',zIndex:'0',visibility:'hidden'});
 const context=cv.getContext('2d'),cx=cloudCv.getContext('2d',{willReadFrequently:true});
 const stat={renders:0,skips:0,totalMs:0,maxMs:0,dpr:0,pixels:0,mode:'local-device-resolution; inherited physics grid unchanged'};
 const clear=()=>{cv.style.visibility='hidden';last=null;};
 function geometry(){
  const card=document.querySelector('.c'),photo=document.querySelector('.mphoto'),group=document.querySelector('.moon'),features=document.querySelector('.mfeatures'),disc=document.querySelector('.moon-mask-disc'),t=photo?.getScreenCTM(),cardRect=card?.getBoundingClientRect(),rect=document.querySelector(card?.classList.contains('real-sky-composed')?'.real-sky-canvas':'.real-sky-preview')?.getBoundingClientRect();
  if(!surface||!table||!t||!rect||!(rect.width>0&&rect.height>0)||!cardRect||!card.classList.contains('moon-ready')||!disc?.classList.contains('mask-on')||+getComputedStyle(disc).opacity===0||t.a<=0||t.d<=0||Math.abs(t.b)>1e-8||Math.abs(t.c)>1e-8)return null;
  // Sample in viewport device pixels, then convert to the absolute child's
  // containing block. Its origin is inside the card border, not cardRect.left.
  // Including the viewport origin also preserves fractional card placement.
  const x=t.a*Number(photo.getAttribute('x'))+t.e,y=t.d*Number(photo.getAttribute('y'))+t.f,w=t.a*Number(photo.getAttribute('width')),h=t.d*Number(photo.getAttribute('height')),dpr=Math.max(.5,Math.min(4,devicePixelRatio||1));
  const scaleX=cardRect.width/card.offsetWidth,scaleY=cardRect.height/card.offsetHeight;
  const originX=cardRect.left+card.clientLeft*scaleX,originY=cardRect.top+card.clientTop*scaleY;
  const opacity=Math.max(0,Math.min(1,+getComputedStyle(group).opacity*+getComputedStyle(features).opacity));
  if(w<=0||h<=0||opacity===0)return null;
  const left=Math.floor(x*dpr)-1,top=Math.floor(y*dpr)-1,width=Math.ceil((x+w)*dpr)-left+1,height=Math.ceil((y+h)*dpr)-top+1;
  if(width*height>1024*1024)throw new Error('Moon detail viewport budget');
  const up=Math.max(0,Math.min(1,window.SalahMoonRuntime?.presentationUp??window.SalahMoonHost?.capture()?.up??1));
  return {card,photo,rect,x,y,w,h,dpr,opacity,left,top,width,height,up,originX,originY,scaleX,scaleY};
 }
 function available(){try{return !disposed&&!!context&&!!cx&&!!geometry();}catch{return false;}}
 function compose(frame,encode){
  if(disposed||!frame||!window.SalahMoonRuntime?.surface()||!context||!cx){clear();return;}
  const g=geometry();if(!g||!(g.card.classList.contains('real-sky-composed')||frame.preview&&g.card.classList.contains('real-sky-preview-ready'))){clear();return;}
  const began=performance.now(),r=frame.raster;
  const base=document.querySelector(frame.preview?'.real-sky-preview':'.real-sky-canvas');
  // Native lunar optics precede the original opaque SVG photo. Preserve that
  // ownership when the photo is replaced: placing this canvas immediately
  // after the base sky put the WHOLE native SVG (including its bright-centred
  // corona) over refined Earthshine. Clouds are already in this local join;
  // foreground weather/UI retain their later/higher layers.
  const behind=g.card.querySelector('.sky')??base;
  if(behind&&cv.previousSibling!==behind)behind.after(cv);else if(!cv.isConnected)g.card.prepend(cv);
  const {width:W,height:H,dpr}=g;
  if(cloudCv.width!==W||cloudCv.height!==H){cloudCv.width=W;cloudCv.height=H;}
  cx.resetTransform();cx.clearRect(0,0,W,H);cx.globalCompositeOperation='source-over';cx.globalAlpha=1;
  const cloud=document.querySelector('.cloudcanvas');
  if(cloud){
   const f=getComputedStyle(cloud).filter,b=/^blur\(([\d.]+)px\)$/.exec(f);if(f!=='none'&&!b)throw new Error('Unsupported lunar cloud filter');
   const cr=cloud.getBoundingClientRect();
   cx.filter=b?`blur(${+b[1]*dpr*g.scaleX}px)`:'none';cx.drawImage(cloud,cr.left*dpr-g.left,cr.top*dpr-g.top,cr.width*dpr,cr.height*dpr);cx.filter='none';
   const grad=cx.createLinearGradient(0,cr.top*dpr-g.top,0,cr.bottom*dpr-g.top);for(const [at,c] of [[0,'rgba(0,0,0,0)'],[.03,'#000'],[.24,'#000'],[.34,'rgba(0,0,0,0)'],[1,'rgba(0,0,0,0)']])grad.addColorStop(at,c);
   cx.globalCompositeOperation='destination-in';cx.fillStyle=grad;cx.fillRect(0,0,W,H);cx.globalCompositeOperation='source-over';
  }
  const cloudRGBA=validateNativeRGBA(cx.getImageData(0,0,W,H).data,W*H);
  const key=JSON.stringify([surface.identity,W,H,g.left,g.top,g.x,g.y,g.w,g.h,g.rect.left,g.rect.top,g.rect.width,g.rect.height,g.opacity,dpr,r.effectiveExposure,g.up]);
  if(last&&last.frame===frame&&last.key===key&&last.cloud.length===cloudRGBA.length&&last.cloud.every((x,i)=>x===cloudRGBA[i])){stat.skips++;return;}
  const exposure=r.effectiveExposure;
  const linear=new Float64Array(W*H*3);
  if(!prepared||prepared.frame!==frame||prepared.key!==key){
   const covered=new Uint8Array(W*H),before=new Float64Array(W*H*3),ss=surface.size/(.96*surface.extent),ox=surface.size/2-.5*ss,oy=ox;
   const stepX=ss/(g.w*dpr),stepY=ss/(g.h*dpr),startX=((g.left/dpr-g.x)/g.w)*ss+ox,startY=((g.top/dpr-g.y)/g.h)*ss+oy;
   const sky=r.skyBackgroundLinear??r.backgroundLinear;
   for(let y=0;y<H;y++)for(let x=0;x<W;x++){
    const i=y*W+x,x0=startX+x*stepX,y0=startY+y*stepY,x1=x0+stepX,y1=y0+stepY;
    const sp=boxSurface(g.up===0&&calendarTable?calendarTable:table,x0,y0,x1,y1),a=sp[3];
    if(a<=1e-10)continue;covered[i]=1;
    if(g.up>0&&g.up<1&&calendarTable){const token=boxSurface(calendarTable,x0,y0,x1,y1);for(let k=0;k<3;k++)sp[k]=g.up*sp[k]+(1-g.up)*token[k];}
    const px=((g.left+x+.5)/dpr-g.rect.left)*r.width/g.rect.width-.5,py=((g.top+y+.5)/dpr-g.rect.top)*r.height/g.rect.height-.5;
    const gas=sampleField(sky,r.width,r.height,px,py),stars=sampleField(r.stellarLinear,r.width,r.height,px,py),diffuse=sampleField(r.diffusePhysicalLinear,r.width,r.height,px,py);
    before.set(joinLunarPixel({gas,direct:stars.map((v,k)=>v+diffuse[k]),premult:sp,coverage:a,opacity:g.opacity,cloud:[0,0,0,0],exposure}),3*i);
   }
   prepared={frame,key,covered,before};
  }
  const covered=prepared.covered,before=prepared.before;
  for(let i=0;i<covered.length;i++){if(!covered[i])continue;const ci=4*i,alpha=cloudRGBA[ci+3]/255;
   for(let k=0;k<3;k++)linear[3*i+k]=nativeCloudChannel(before[3*i+k],cloudRGBA[ci+k],alpha,exposure);
  }
  const rgba=encode(linear,exposure);for(let i=0;i<covered.length;i++)rgba[4*i+3]=covered[i]?255:0;
  if(frame.preview&&!frame.current()){clear();return;}
  if(cv.width!==W||cv.height!==H){cv.width=W;cv.height=H;}
  context.putImageData(new ImageData(rgba,W,H),0,0);
  Object.assign(cv.style,{left:`${(g.left/dpr-g.originX)/g.scaleX}px`,top:`${(g.top/dpr-g.originY)/g.scaleY}px`,width:`${W/dpr/g.scaleX}px`,height:`${H/dpr/g.scaleY}px`,visibility:'visible'});
  last={frame,key,cloud:cloudRGBA};stat.renders++;stat.totalMs=performance.now()-began;stat.maxMs=Math.max(stat.maxMs,stat.totalMs);stat.dpr=dpr;stat.pixels=W*H;stat.skyOwner=frame.preview?'atmospheric-preview':'refined-sky';stat.atmosphereOwner='foreground path radiance, never lunar-occluded';
 }
 return {adopt(s){table=prefixSurface(s);calendarTable=s.calendarLinear?prefixSurface({size:s.size,linear:s.calendarLinear,coverage:s.coverage}):null;surface=s;last=null;prepared=null;},clear,compose,get available(){return available();},get state(){return {...stat,visible:cv.style.visibility==='visible'};},dispose(){disposed=true;clear();cv.remove();table=null;calendarTable=null;surface=null;prepared=null;}};
}
function projectSurfaceCodes({size,linear,coverage,extent},diameter=312,shift=[0,0]){
 const p=prefixSurface({size,linear,coverage}),N=Math.ceil(diameter*1.1),scale=size/(diameter*extent),out=new Float32Array(N*N*3);
 const ox=size/2-N*scale/2-shift[0]*scale,oy=size/2-N*scale/2-shift[1]*scale;
 for(let y=0;y<N;y++)for(let x=0;x<N;x++){
  const c=boxSurface(p,ox+x*scale,oy+y*scale,ox+(x+1)*scale,oy+(y+1)*scale);
  for(let k=0;k<3;k++){const v=Math.max(0,Math.min(1,c[k]));out[3*(y*N+x)+k]=(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055)*255;}
 }return out;
}
