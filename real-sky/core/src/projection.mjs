import {DEG,finite,wrapDeg,clamp} from './astronomy.mjs';
/** All-sky map: north up, east LEFT, zenith centred. This is a sky chart seen from inside.
 * Set eastLeft:false only for an explicitly labelled ENU diagram, not silently.
 */
export function projectAllSky(h,{width=325,height=325,eastLeft=true,padding=4}={}){
 finite(width,'width',1);finite(height,'height',1);finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');
 finite(padding,'padding',0,Math.min(width,height)/2-Number.EPSILON);const R=Math.min(width,height)/2-padding;if(R<=0)throw new RangeError('No all-sky radius');const r=(90-h.altDeg)/90*R,a=h.azDeg*DEG;
 return {x:width/2+(eastLeft?-1:1)*r*Math.sin(a),y:height/2-r*Math.cos(a),visible:h.altDeg>=0};
}
export function unprojectAllSky(x,y,{width=325,height=325,eastLeft=true,padding=4}={}){
 finite(width,'width',1);finite(height,'height',1);finite(x,'x');finite(y,'y');finite(padding,'padding',0,Math.min(width,height)/2-Number.EPSILON);const R=Math.min(width,height)/2-padding;if(R<=0)throw new RangeError('No all-sky radius');const dx=(x-width/2)*(eastLeft?-1:1),dy=height/2-y,r=Math.hypot(dx,dy);
 return {altDeg:90-r/R*90,azDeg:r<1e-12?0:wrapDeg(Math.atan2(dx,dy)/DEG)};
}
/** Exact legacy PR38 geometry, expressed in north-zero/east-positive azimuth.
 * It is an anisotropically compressed crop, NOT a camera with a physical field of view.
 */
export function projectWidgetDome(h){finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');const r=(90-h.altDeg)/90*270,a=h.azDeg*DEG;
 const x=162-r*Math.sin(a),y=-30+.8*r*Math.cos(a);
 return {x,y,visible:h.altDeg>=0&&x>=-24&&x<=349&&y>=-24&&y<=250};
}
/** Perspective camera. True azimuth north0/east90; positive roll rotates camera right
 * towards the unrolled up axis. Altitude/azimuth always describe one rigid camera. */
function cameraBasis(c={}){
 const width=finite(c.width??325,'width',1,16384),height=finite(c.height??530,'height',1,16384),az=finite(c.azDeg??180,'camera azimuth'),alt=finite(c.altDeg??35,'camera altitude',-90,90),fov=finite(c.fovYDeg??90,'vertical FOV',1,170),roll=finite(c.rollDeg??0,'camera roll')*DEG;
 const a=az*DEG,e=alt*DEG,fw=[Math.cos(e)*Math.sin(a),Math.cos(e)*Math.cos(a),Math.sin(e)],rt=[Math.cos(a),-Math.sin(a),0],up=[-Math.sin(e)*Math.sin(a),-Math.sin(e)*Math.cos(a),Math.cos(e)];
 return {width,height,f:height/(2*Math.tan(fov*DEG/2)),fw,rt:rt.map((v,i)=>v*Math.cos(roll)+up[i]*Math.sin(roll)),up:up.map((v,i)=>v*Math.cos(roll)-rt[i]*Math.sin(roll)),fovXDeg:2*Math.atan(width/height*Math.tan(fov*DEG/2))/DEG};
}
export function cameraGeometry(c={}){const b=cameraBasis(c);return {width:b.width,height:b.height,focalPixels:b.f,fovXDeg:b.fovXDeg};}
export function projectPerspective(h,c={}){
 finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');const b=cameraBasis(c),ha=h.azDeg*DEG,he=h.altDeg*DEG,v=[Math.cos(he)*Math.sin(ha),Math.cos(he)*Math.cos(ha),Math.sin(he)];
 const d=(u,w)=>u.reduce((s,x,i)=>s+x*w[i],0),z=d(v,b.fw);if(z<=0)return null;
 const x=b.width/2+b.f*d(v,b.rt)/z,y=b.height/2-b.f*d(v,b.up)/z,inFrame=x>=0&&x<=b.width&&y>=0&&y<=b.height;
 return {x,y,inFrame,visible:h.altDeg>=0&&inFrame};
}
export function unprojectPerspective(x,y,c={}){
 finite(x,'x');finite(y,'y');const b=cameraBasis(c),u=(x-b.width/2)/b.f,w=(b.height/2-y)/b.f,v=b.fw.map((a,i)=>a+u*b.rt[i]+w*b.up[i]),len=Math.hypot(...v),r=Math.hypot(v[0],v[1]);
 return {altDeg:Math.atan2(v[2],r)/DEG,azDeg:r<1e-14?0:wrapDeg(Math.atan2(v[0],v[1])/DEG),enu:v.map(a=>a/len)};
}

/** CP7.5: hoist rigid camera constants once per render, NOT once per UTC/location.
 * The per-ray arithmetic remains identical to the public reference functions.
 * No approximate ray grid, frame cache, or new celestial coordinate system.
 */
export function prepareInverseProjection(view={}){
 const c={...view},type=c.type??'camera';
 if(type==='camera'){
  const b=cameraBasis(c);
  return (x,y)=>{finite(x,'x');finite(y,'y');const u=(x-b.width/2)/b.f,w=(b.height/2-y)/b.f,v=b.fw.map((a,i)=>a+u*b.rt[i]+w*b.up[i]),len=Math.hypot(...v),r=Math.hypot(v[0],v[1]);
   return {altDeg:Math.atan2(v[2],r)/DEG,azDeg:r<1e-14?0:wrapDeg(Math.atan2(v[0],v[1])/DEG),enu:v.map(a=>a/len)};};
 }
 if(type==='allsky'){
  const width=finite(c.width??325,'width',1),height=finite(c.height??325,'height',1),padding=finite(c.padding??4,'padding',0,Math.min(width,height)/2-Number.EPSILON),eastLeft=c.eastLeft??true,R=Math.min(width,height)/2-padding;
  if(R<=0)throw new RangeError('No all-sky radius');
  return (x,y)=>{finite(x,'x');finite(y,'y');const dx=(x-width/2)*(eastLeft?-1:1),dy=height/2-y,r=Math.hypot(dx,dy);return {altDeg:90-r/R*90,azDeg:r<1e-12?0:wrapDeg(Math.atan2(dx,dy)/DEG)};};
 }
 throw new RangeError('Prepared projection must be camera or allsky');
}
