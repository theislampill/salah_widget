// Exact CP8.3 mask implementation retained solely as a numerical/cost control.
export function nativeDiscMask(width,height,rect,m,radius){
 const det=m.a*m.d-m.b*m.c;if(!Number.isFinite(det)||Math.abs(det)<1e-12)throw new RangeError('Singular native Moon transform');
 const mask=new Float64Array(width*height),sx=rect.width/width,sy=rect.height/height;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const px=rect.left+(x+.5)*sx-m.e,py=rect.top+(y+.5)*sy-m.f;
  const xx=(m.d*px-m.c*py)/det,yy=(-m.b*px+m.a*py)/det;
  // One logical-pixel anti-alias ramp, transformed into the local disc coordinates.
  const aa=Math.max(1e-9,.5*(Math.hypot(m.d*sx,m.b*sx)+Math.hypot(m.c*sy,m.a*sy))/Math.abs(det));
  mask[y*width+x]=Math.max(0,Math.min(1,(Math.hypot(xx,yy)-radius)/aa+.5));
 }
 return mask;
}
