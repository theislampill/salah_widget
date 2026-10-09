"""Independent displayed-limb reference using direct source-cell overlaps.

No terrain model or filtering changes are being qualified. This isolates the
existing N540 surface's sampling/placement/composition, not scientific accuracy.
"""
import base64, io
import numpy as np
from PIL import Image

REFERENCE=r'''()=>{
 const m=__mq.lastResult,s=m.surfaceSize,p=document.querySelector('.mphoto'),t=p.getScreenCTM(),d=devicePixelRatio;
 const x=t.a*+p.getAttribute('x')+t.e,y=t.d*+p.getAttribute('y')+t.f,w=t.a*+p.getAttribute('width'),h=t.d*+p.getAttribute('height');
 const L=Math.floor(x*d)-1,T=Math.floor(y*d)-1,W=Math.ceil((x+w)*d)-L+1,H=Math.ceil((y+h)*d)-T+1;
 const r=realSkyFrame().raster,b=document.querySelector('.real-sky-canvas').getBoundingClientRect(),E=r.effectiveExposure;
 const sample=(f,px,py,k)=>{px=Math.max(0,Math.min(r.width-1,px));py=Math.max(0,Math.min(r.height-1,py));const ix=Math.floor(px),iy=Math.floor(py),jx=Math.min(r.width-1,ix+1),jy=Math.min(r.height-1,iy+1),a=px-ix,c=py-iy;return f[3*(iy*r.width+ix)+k]*(1-a)*(1-c)+f[3*(iy*r.width+jx)+k]*a*(1-c)+f[3*(jy*r.width+ix)+k]*(1-a)*c+f[3*(jy*r.width+jx)+k]*a*c;};
 const up=SalahMoonRuntime.presentationUp,op=+getComputedStyle(document.querySelector('.moon')).opacity*+getComputedStyle(document.querySelector('.mfeatures')).opacity;
 const rgba=new Uint8ClampedArray(W*H*4),edge=[];
 for(let j=0;j<H;j++)for(let i=0;i<W;i++){
  const bounds=(v,n,z,dz)=>s/2+(((v/d-z)/dz)-.5)*s/(.96*m.surfaceExtent);
  const x0=bounds(L+i,s,x,w),x1=bounds(L+i+1,s,x,w),y0=bounds(T+j,s,y,h),y1=bounds(T+j+1,s,y,h),area=(x1-x0)*(y1-y0),sum=[0,0,0,0];
  // Explicit intersected cell rectangles: no integral/prefix-table algorithm.
  for(let cy=Math.max(0,Math.floor(y0));cy<Math.min(s,Math.ceil(y1));cy++)for(let cx=Math.max(0,Math.floor(x0));cx<Math.min(s,Math.ceil(x1));cx++){
   const weight=Math.max(0,Math.min(x1,cx+1)-Math.max(x0,cx))*Math.max(0,Math.min(y1,cy+1)-Math.max(y0,cy))/area,k=cy*s+cx;
   sum[3]+=m.surfaceCoverage[k]*weight;
   for(let z=0;z<3;z++)sum[z]+=(up*m.surfaceLinear[3*k+z]+(1-up)*m.calendarLinear[3*k+z])*weight;
  }
  const a=Math.min(1,sum[3]),px=((L+i+.5)/d-b.left)*r.width/b.width-.5,py=((T+j+.5)/d-b.top)*r.height/b.height-.5;
  for(let k=0;k<3;k++){
   const gas=sample(r.skyBackgroundLinear??r.backgroundLinear,px,py,k),direct=sample(r.stellarLinear,px,py,k)+sample(r.diffusePhysicalLinear,px,py,k);
   const surface=a?Math.min(1-1/131072,sum[k]/a):0;
   // PR42 foreground contract: air is between observer and opaque Moon.
   // The independent source-cell overlap reference still owns coverage; only
   // its transport boundary changes. Old gas-occlusion is a retained negative
   // control in lunar-atmosphere-negative.tap, not an acceptable rim oracle.
   const linear=gas+direct*(1-a)-Math.log1p(-surface)/E*a*op;
   const v=-Math.expm1(-E*Math.max(0,linear));rgba[4*(j*W+i)+k]=Math.round(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055));
  }
  rgba[4*(j*W+i)+3]=a>1e-10?255:0;
  // Partially covered outer edge only. No terminator pixels (coverage=1).
  // Exclude rounded-card clipping and the first device row at its top border.
  if(a>1e-8&&a<1-1e-8&&(L+i+.5)/d<b.right-15&&(T+j+.5)/d>b.top+3)edge.push([i,j,a]);
 }
 const cv=document.createElement('canvas');cv.width=W;cv.height=H;cv.getContext('2d').putImageData(new ImageData(rgba,W,H),0,0);
 return {left:L,top:T,width:W,height:H,edge,png:cv.toDataURL(),scope:'Direct overlap integration of unchanged worker N540 samples + independent scalar composition; partially covered outer limb only; cloud-free diagnostic'};
}'''


def verify_spatial(page,out,name,measurement):
    # Hide unrelated UI/optics without changing layout, geometry or the two
    # compositor canvases. Preserve the actual UI acceptance captures separately.
    style=page.add_style_tag(content='.c *{visibility:hidden!important}.c>.real-sky-canvas,.c>.moon-detail-canvas{visibility:visible!important}')
    ref=page.evaluate(REFERENCE)
    raw=base64.b64decode(ref.pop('png').split(',')[1]);(out/(name+'-spatial-reference.png')).write_bytes(raw)
    cvraw=base64.b64decode(page.evaluate("document.querySelector('.moon-detail-canvas').toDataURL()").split(',')[1]);(out/(name+'-spatial-canvas.png')).write_bytes(cvraw)
    canvas=np.array(Image.open(io.BytesIO(cvraw)).convert('RGB'),dtype=int)
    png=page.screenshot(path=out/(name+'-spatial-displayed.png'))
    # Rasterize the independent image through the same browser compositor. A
    # translated parent can be separately rasterized then resampled; comparing
    # its screenshot directly with raw reference texels would misclassify that
    # browser operation as a lunar coverage error.
    page.evaluate('''async r=>{const card=document.querySelector('.c'),b=card.getBoundingClientRect(),d=devicePixelRatio,sx=b.width/card.offsetWidth,sy=b.height/card.offsetHeight,cv=document.createElement('canvas');cv.id='independent-rim-reference';cv.width=r.width;cv.height=r.height;const im=new Image();im.src=r.png;await im.decode();cv.getContext('2d').drawImage(im,0,0);Object.assign(cv.style,{position:'absolute',left:((r.left/d-b.left)/sx-card.clientLeft)+'px',top:((r.top/d-b.top)/sy-card.clientTop)+'px',width:(r.width/d/sx)+'px',height:(r.height/d/sy)+'px',zIndex:'0'});cv.style.setProperty('visibility','visible','important');document.querySelector('.moon-detail-canvas').after(cv);}''',{**ref,'png':'data:image/png;base64,'+base64.b64encode(raw).decode()})
    page.evaluate("document.querySelector('.moon-detail-canvas').style.setProperty('visibility','hidden','important')")
    projected=page.screenshot(path=out/(name+'-spatial-browser-reference.png'))
    page.evaluate("document.querySelector('#independent-rim-reference').remove()")
    page.evaluate("document.querySelector('.moon-detail-canvas').style.visibility='visible'")
    style.evaluate('(e)=>e.remove()')
    expected=np.array(Image.open(io.BytesIO(raw)).convert('RGB'),dtype=int)
    actual=np.array(Image.open(io.BytesIO(png)).convert('RGB'),dtype=int)
    final_reference=np.array(Image.open(io.BytesIO(projected)).convert('RGB'),dtype=int)
    differences=[];canvas_differences=[];worst=[]
    for x,y,a in ref.pop('edge'):
        observed=actual[ref['top']+y,ref['left']+x];target=final_reference[ref['top']+y,ref['left']+x];differences.append(np.abs(observed-target))
        if canvas.shape==expected.shape:canvas_differences.append(np.abs(canvas[y,x]-expected[y,x]))
        worst.append({'x':x,'y':y,'coverage':a,'actual':observed.tolist(),'expected':target.tolist(),'delta':int(differences[-1].max())})
    delta=np.array(differences)
    # Allow one code for canvas quantization and three for the background raster
    # at partially covered texels resampled by the browser's parent compositor.
    result={**ref,'samples':len(delta),'maximumCode':int(delta.max()),'p95Code':float(np.percentile(delta,95)),
            'meanAbsoluteCode':float(delta.mean()),'toleranceCode':4,'maxCanvasCode':int(np.max(canvas_differences)) if canvas_differences else None,'worst':sorted(worst,key=lambda x:x['delta'],reverse=True)[:5]}
    result['passed']=result['samples']>60 and result['maximumCode']<=4
    return result
