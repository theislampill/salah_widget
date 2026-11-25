// A fixed accepted scene and foreground. Precompute only *provably* unchanged
// quantized pixels. The full-frame slow replay remains an independent oracle.
import {nativeCalendarRegion,nativeForeground} from '../../real-sky/native-composition.mjs';
import {encodeNativeDisplay} from '../../real-sky/native-host.mjs';
import {nativeCloudDisplayFrame} from '../../real-sky/native-cloud-transfer.mjs';
import {starOffset,glassMembership} from './stellar_replay.mjs';

function compose(raster,base,gas,cloud,moon) {
  if (raster.starPreview) {
    const encoded=encodeNativeDisplay(base,raster.effectiveExposure);
    return nativeCloudDisplayFrame(encoded,cloud??new Uint8ClampedArray(encoded.length),moon);
  }
  const joined=nativeForeground(base,{cloudRGBA:cloud,moonRGBA:moon,atmosphereLinear:gas,exposure:raster.effectiveExposure});
  return encodeNativeDisplay(joined.linear,raster.effectiveExposure);
}

function visitPatch(star,width,visit) {
  for (let y=0;y<star.h;y++) for (let x=0;x<star.w;x++) {
    visit((star.y0+y)*width+star.x0+x,3*(y*star.w+x));
  }
}
function gather(input,indices,stride) {
  if(!input) return null;
  const out=new input.constructor(indices.length*stride);
  for(let i=0;i<indices.length;i++) for(let k=0;k<stride;k++) out[stride*i+k]=input[stride*indices[i]+k];
  return out;
}
export function prepareReplay(raster,stars,config,foreground) {
  if (!['all','preview-members'].includes(config.scope)||![1,2,3,4].includes(config.multiplier)
      || !Number.isFinite(config.glassFactor)||config.glassFactor<0||config.glassFactor>1
      || !Number.isFinite(config.margin)||config.margin<0) throw new RangeError('Explicit qualification options required');
  const {cloudRGBA:cloud,moonRGBA:moon,mask,glass}=foreground;
  const signalMask=foreground.signalMask??mask;
  const base=nativeCalendarRegion(raster,mask), gas=raster.skyBackgroundLinear??raster.backgroundLinear;
  const nominal=compose(raster,base,gas,cloud,moon), envelope=new Float64Array(base.length);
  const sources=[];
  for(const star of stars){
    if (!star.detectable||star.altDeg<=0||config.scope==='preview-members'&&star.vmag>4.5) continue;
    const glassScale=glassMembership(star,glass,config.margin)?config.glassFactor:1;
    if (!glassScale) continue;
    sources.push({star,glassScale});
    // Positivity of every PSF permits summing a worst-case bound, including
    // overlapping sources. Foreground transfer/encoding are monotonic.
    const bound=.04*config.multiplier*glassScale;
    visitPatch(star,raster.width,(p,src)=>{
      for(let k=0;k<3;k++) envelope[3*p+k]+=bound*star.linear[src+k];
    });
  }
  const extremum=sign=>{
    const linear=base.map((v,i)=>{
      const span=envelope[i]*(signalMask?.[Math.floor(i/3)]??1);
      // Conservative floating-point clearance at the extrema; a candidate
      // near an encoding tie must be evaluated, never discarded by epsilon.
      const slack=span?64*Number.EPSILON*(1+Math.abs(v)+span):0;
      return Math.max(0,v+sign*(span+slack));
    });
    return compose(raster,linear,gas,cloud,moon);
  };
  const low=extremum(-1), high=extremum(1), indices=[], map=new Int32Array(base.length/3).fill(-1);
  for(let p=0;p<map.length;p++) {
    const i=4*p;
    if(low[i]!==high[i]||low[i+1]!==high[i+1]||low[i+2]!==high[i+2]){
      map[p]=indices.length;indices.push(p);
    }
  }
  for(const source of sources){
    const offsets=[],weights=[];
    visitPatch(source.star,raster.width,(p,src)=>{
      if(map[p]<0||!(source.star.linear[src]||source.star.linear[src+1]||source.star.linear[src+2])) return;
      offsets.push(3*map[p]);weights.push(...source.star.linear.subarray(src,src+3));
    });
    source.offsets=Uint32Array.from(offsets);source.weights=Float64Array.from(weights);
  }
  const bg=gather(base,indices,3), atmosphere=gather(gas,indices,3),direct=gather(signalMask,indices,1);
  const cloudPixels=gather(cloud,indices,4),moonPixels=gather(moon,indices,4),delta=new Float64Array(bg.length);
  const linear=new Float64Array(bg.length), rgba=nominal.slice();
  // Rank the brightest *displayed* center using each individual source's
  // withdrawal through the actual foreground and nonlinear encoder. Catalog
  // V magnitude alone cannot distinguish a bright star behind an opaque Moon.
  const centers=sources.map(({star})=>Math.floor(star.y)*raster.width+Math.floor(star.x));
  const withdrawal=gather(base,centers,3);
  for(let j=0;j<sources.length;j++){
    const {star}=sources[j],m=signalMask?.[centers[j]]??1;
    const q=3*((Math.floor(star.y)-star.y0)*star.w+Math.floor(star.x)-star.x0);
    for(let k=0;k<3;k++) withdrawal[3*j+k]=Math.max(0,withdrawal[3*j+k]-m*star.linear[q+k]);
  }
  const without=compose(raster,withdrawal,gather(gas,centers,3),gather(cloud,centers,4),gather(moon,centers,4));
  let brightest=null,largest=0,contributingCenters=0;
  for(let j=0;j<sources.length;j++){
    let difference=0;
    for(let k=0;k<3;k++) difference+=[.2126,.7152,.0722][k]*(nominal[4*centers[j]+k]-without[4*j+k]);
    if(difference>0)contributingCenters++;
    if(difference>largest){largest=difference;brightest=sources[j];}
  }
  return {nominal,indices,sourceCount:sources.length,contributingCenters,present(utcMs,motion={}){
    delta.fill(0);
    let factor=1;
    for(const src of sources){
      const shift=starOffset(src.star,utcMs,config.multiplier,motion)*src.glassScale;
      if(src===brightest)factor=1+shift;
      if(!shift)continue;
      for(let j=0;j<src.offsets.length;j++){
        const d=src.offsets[j],w=3*j;
        for(let k=0;k<3;k++) delta[d+k]+=shift*src.weights[w+k];
      }
    }
    for(let i=0;i<linear.length;i++) linear[i]=Math.max(0,bg[i]+delta[i]*(direct?.[Math.floor(i/3)]??1));
    const codes=compose(raster,linear,atmosphere,cloudPixels,moonPixels);
    for(let j=0;j<indices.length;j++){
      const d=4*indices[j],s=4*j;
      rgba[d]=codes[s];rgba[d+1]=codes[s+1];rgba[d+2]=codes[s+2];
    }
    let sample=null;
    if(brightest){
      const star=brightest.star,p=4*(Math.floor(star.y)*raster.width+Math.floor(star.x));
      sample={id:star.id,factor,centerDelta:[0,1,2].map(k=>rgba[p+k]-nominal[p+k])};
    }
    return {rgba,sample};
  }};
}

// Cover only the final pixels whose native encoded RGB actually changed.
// An empty pixel exposes the host's own canvas. A changed pixel uses a fully
// opaque replacement, avoiding nonlinear screen blending or a second encode.
export function stellarOverlay(prepared,rgba){
  const layer=new Uint8ClampedArray(rgba.length);
  for(const p of prepared.indices){
    const i=4*p;
    if(rgba[i]===prepared.nominal[i]&&rgba[i+1]===prepared.nominal[i+1]&&rgba[i+2]===prepared.nominal[i+2])continue;
    layer[i]=rgba[i];layer[i+1]=rgba[i+1];layer[i+2]=rgba[i+2];layer[i+3]=255;
  }
  return layer;
}
