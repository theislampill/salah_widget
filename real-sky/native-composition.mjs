/** CP8.2 native foreground operator.
 * Input sky has received molecular/aerosol transport, NOT cloud attenuation.
 * Painted native cloud alpha is the sole total cloud transmission owner. Native
 * RGB/PBR are display-referred presentations, not measured radiance; inversion of
 * the SAME exposure/encoding places them in one explicit linear compositing space.
 */
export function nativeInverseCode(code,exposure){
 if(!Number.isFinite(exposure)||exposure<=0||exposure>100000)throw new RangeError('Positive shared native exposure required');
 if(!Number.isFinite(code)||code<0||code>255)throw new RangeError('Native sRGB code out of range');
 const s=code/255,l=s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
 // Code 255 denotes saturation, not infinite radiance. Clip at one half 16-bit step;
 // encoding this endpoint returns 255. The censoring assumption is explicit.
 return -Math.log1p(-Math.min(1-1/131072,l))/exposure;
}
export function nativeCloudMaskAt(y){if(!Number.isFinite(y))throw new RangeError('Cloud mask coordinate');return y<=0||y>=.34?0:y<.03?y/.03:y<=.24?1:(.34-y)/.10;}
export function nativeForeground(base,{cloudRGBA=null,moonRGBA=null,exposure}={}){
 if(!base||base.length%3)throw new RangeError('Native linear RGB input required');
 const pixels=base.length/3;for(const a of [cloudRGBA,moonRGBA])if(a&&a.length!==pixels*4)throw new RangeError('Native foreground dimensions');
 const inv=Float64Array.from({length:256},(_,i)=>nativeInverseCode(i,exposure)),out=new Float64Array(base.length);
 let cloudAlphaSum=0,maxAlpha=0,moonPixels=0;
 for(let p=0;p<pixels;p++){
  const ci=p*4,li=p*3,ma=moonRGBA?moonRGBA[ci+3]/255:0,ca=cloudRGBA?cloudRGBA[ci+3]/255:0,T=1-ca;
  cloudAlphaSum+=ca;maxAlpha=Math.max(maxAlpha,ca);if(ma>0)moonPixels++;
  for(let k=0;k<3;k++){
   const v=base[li+k];if(!Number.isFinite(v)||v<0)throw new RangeError('Nonphysical native base channel');
   const lunar=ma? v*(1-ma)+inv[moonRGBA[ci+k]]*ma:v;
   out[li+k]=lunar*T+(ca?inv[cloudRGBA[ci+k]]*ca:0);
  }
 }
 return {linear:out,diagnostics:{cloudApplications:1,meanCloudAlpha:cloudAlphaSum/Math.max(1,pixels),maxCloudAlpha:maxAlpha,moonPixels,cloudTransmissionOwner:'1 - native painted alpha after native blur and vertical mask',order:'gas-transported sky → calendar direct-light cutout → native PBR material → native cloud screen → one shared encode',cloudColour:'display-referred native painter; inverse shared tone map; not measured cloud radiance',exposureOwner:'CP7 sky+diffuse meter before calendar/foreground; native foreground excluded',saturation:'native code 255 uses 1 - 1/131072 in inverse tone map'}};
}
/** Exact leading-row restriction of the calendar/direct-light join. */
export function nativeCalendarRegion(raster,mask=null,rows=raster.height){
 if(!Number.isInteger(rows)||rows<1||rows>raster.height)throw new RangeError('Native region rows');
 const pixels=raster.width*rows;if(mask&&mask.length!==pixels)throw new RangeError('Native regional mask dimensions');
 const out=new Float64Array(pixels*3),sky=raster.skyBackgroundLinear??raster.backgroundLinear,diffuse=raster.diffusePhysicalLinear;
 for(let i=0;i<out.length;i++){const m=mask?mask[Math.floor(i/3)]:1;out[i]=sky[i]+(raster.stellarLinear[i]+(diffuse?.[i]??0))*m;}return out;
}
/** Cover the moving Moon's old and new bounds, and the native cloud support.
 * Two logical-pixel padding covers antialiasing; never crop the physical frame. */
export function nativeForegroundRows(height,currentBottom=0,previousBottom=0){
 if(!Number.isInteger(height)||height<1||!Number.isFinite(currentBottom)||!Number.isFinite(previousBottom))throw new RangeError('Native foreground bounds');
 return Math.max(1,Math.min(height,Math.ceil(Math.max(.34*height,currentBottom,previousBottom)+2)));
}
/** Capture DOM pixels without a second sky/clock/weather owner. Uses the native
 * 300px backing canvas directly (the SVG image path adds an avoidable resample):
 * no re-lit Moon, no new texture and no asynchronous PNG/phase race.
 */
export class NativeForegroundCapture{
 constructor(canvas){this.canvas=canvas;this.cloud=document.createElement('canvas');this.moon=document.createElement('canvas');for(const c of [this.cloud,this.moon]){c.width=325;c.height=530;}this.cx=this.cloud.getContext('2d',{willReadFrequently:true});this.mx=this.moon.getContext('2d',{willReadFrequently:true});if(!this.cx||!this.mx)throw new Error('Native foreground capture unavailable');}
 bottom(){
  const p=document.querySelector('.mphoto'),m=p?.getScreenCTM(),r=this.canvas.getBoundingClientRect();
  if(!m||!(r.height>0))return 0;
  const x=Number(p.getAttribute('x')),y=Number(p.getAttribute('y')),w=Number(p.getAttribute('width')),h=Number(p.getAttribute('height'));
  return Math.max(...[[x,y],[x+w,y],[x,y+h],[x+w,y+h]].map(([a,b])=>(m.b*a+m.d*b+m.f-r.top)*530/r.height));
 }
 capture(rows=530){
  if(!Number.isInteger(rows)||rows<1||rows>530)throw new RangeError('Native capture rows');
  for(const c of [this.cloud,this.moon])if(c.height!==rows)c.height=rows;
  const cloud=document.querySelector('.cloudcanvas'),photo=document.querySelector('.mphoto'),group=document.querySelector('.moon'),features=document.querySelector('.mfeatures'),card=document.querySelector('.c');
  const rect=this.canvas.getBoundingClientRect();if(!(rect.width>0&&rect.height>0))throw new Error('Native canvas has no drawable bounds');
  const cx=this.cx,mx=this.mx;cx.resetTransform();cx.clearRect(0,0,325,530);cx.globalCompositeOperation='source-over';cx.globalAlpha=1;
  if(cloud){const filter=getComputedStyle(cloud).filter;const blur=/^blur\(([\d.]+)px\)$/.exec(filter);if(filter!=='none'&&!blur)throw new Error('Unsupported native cloud filter');cx.filter=blur?'blur('+(Number(blur[1])*325/rect.width)+'px)':'none';cx.drawImage(cloud,0,0,325,530);cx.filter='none';
   // Native mask-image is explicitly bound by the source-preservation test. Mask after filtering.
   const grad=cx.createLinearGradient(0,0,0,530);grad.addColorStop(0,'rgba(0,0,0,0)');grad.addColorStop(.03,'#000');grad.addColorStop(.24,'#000');grad.addColorStop(.34,'rgba(0,0,0,0)');grad.addColorStop(1,'rgba(0,0,0,0)');cx.globalCompositeOperation='destination-in';cx.fillStyle=grad;cx.fillRect(0,0,325,530);cx.globalCompositeOperation='source-over';
  }
  mx.resetTransform();mx.clearRect(0,0,325,530);mx.globalAlpha=1;
  const surface=window.SalahNativeSkyHost.lunarSurface();
  const ready=!!(card?.classList.contains('moon-ready')&&photo?.getAttribute('href')&&surface);
  let moonAlpha=0;
  if(ready){const t=photo.getScreenCTM();if(!t)throw new Error('Native Moon transform unavailable');moonAlpha=Math.max(0,Math.min(1,Number(getComputedStyle(group).opacity)*Number(getComputedStyle(features).opacity)));
   if(moonAlpha>0){const sx=325/rect.width,sy=530/rect.height;mx.setTransform(t.a*sx,t.b*sy,t.c*sx,t.d*sy,(t.e-rect.left)*sx,(t.f-rect.top)*sy);mx.globalAlpha=moonAlpha;
    mx.drawImage(surface,Number(photo.getAttribute('x')),Number(photo.getAttribute('y')),Number(photo.getAttribute('width')),Number(photo.getAttribute('height')));mx.resetTransform();mx.globalAlpha=1;
   }
  }
  return {cloudRGBA:cx.getImageData(0,0,325,rows).data,moonRGBA:mx.getImageData(0,0,325,rows).data,native:{moonSurface:ready?'native-300px-backing-canvas':'unavailable',moonAlpha,cloudBuffer:cloud?{width:cloud.width,height:cloud.height}:null,maskStops:[0,.03,.24,.34,1],cloudSource:getComputedStyle(cloud).visibility}};
 }
}

/** Exact dirty-input guard adapted from the donor's cloud-only reuse check.
 * Our native Moon is inside the joined framebuffer, so cloud equality alone
 * is insufficient. Capture arrays are owned snapshots from getImageData.
 */
export function sameNativePresentation(a,b){
 if(!a||!b||!a.frame||a.frame!==b.frame||a.rows!==b.rows||a.maskKey!==b.maskKey)return false;
 for(const key of ['cloudRGBA','moonRGBA']){
  const x=a[key],y=b[key];if(!x||!y||x.length!==y.length)return false;
  for(let i=0;i<x.length;i++)if(x[i]!==y[i])return false;
 }
 return true;
}
