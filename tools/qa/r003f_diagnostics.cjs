'use strict';
const {lightness,luminance,quantile}=require('./r003f_p1.cjs');
const mean=a=>a.length?a.reduce((s,v)=>s+v,0)/a.length:null;
function spread(a){
  const m=mean(a);return m===null?null:Math.sqrt(mean(a.map(v=>(v-m)**2)));
}
function distribution(a){
  if(!a.length)return {count:0,median:null,p95:null,max:null};
  const median=quantile(a,.5),p95=quantile(a,.95); // quantile sorts the array.
  return {count:a.length,median,p95,max:a[a.length-1]};
}
const channel=Float64Array.from({length:256},(_,i)=>{const c=i/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4;});
function lab(rgba,i){
  const [r,g,b]=[0,1,2].map(k=>channel[rgba[4*i+k]]);
  const f=y=>y>216/24389?Math.cbrt(y):(24389/27*y+16)/116;
  const x=f((.4124564*r+.3575761*g+.1804375*b)/.95047),y=f(.2126729*r+.7151522*g+.072175*b),z=f((.0193339*r+.119192*g+.9503041*b)/1.08883);
  return [116*y-16,500*(x-y),200*(y-z)];
}
function deltaE(masks,a,b){
  return distribution(masks.discPixels.map(i=>{const u=lab(a,i),v=lab(b,i);return Math.hypot(...u.map((k,j)=>k-v[j]));}));
}
function terrain(masks,frame){
  const lit=masks.lit.map(i=>luminance(frame,i)-masks.g0),dark=masks.dark.map(i=>lightness(luminance(frame,i)));
  const m=mean(lit);
  return {litCount:lit.length,litCV:m>0?spread(lit)/m:null,darkCount:dark.length,darkSdL:spread(dark)};
}
function crossings(masks,frame,waxing){
  const width=325*masks.dpr, rows=new Map();
  const byY=indices=>{
    const result=new Map();
    for(const i of indices){const y=Math.floor(i/width);if(!result.has(y))result.set(y,[]);result.get(y).push(i);}
    return result;
  };
  const all=byY(masks.discPixels),lit=byY(masks.lit),dark=byY(masks.dark);
  for(const [y,values] of all){
    if(!lit.has(y)||!dark.has(y))continue;
    const med=ids=>quantile(ids.map(i=>luminance(frame,i)),.5);
    const lo=med(dark.get(y)),hi=med(lit.get(y));
    if(!(hi>lo))continue;
    const half=(lo+hi)/2, xs=[];
    for(let j=1;j<values.length;j++){
      const i=values[j],a=luminance(frame,values[j-1]),b=luminance(frame,i);
      if(waxing?a<half&&b>=half:a>=half&&b<half)xs.push(i%width-1+(half-a)/(b-a));
    }
    rows.set(y,xs);
  }
  return rows;
}
function terminator(masks,frame,reference,waxing){
  const cr=crossings(masks,frame,waxing),rr=crossings(masks,reference,waxing),shifts=[];
  let ambiguous=0,missing=0;
  for(const [y,xs] of rr){
    const observed=cr.get(y);
    if(!xs.length||!observed?.length){missing++;continue;}
    // No nearest-neighbour cherry-picking through texture- or UI-induced crossings.
    if(xs.length!==1||observed.length!==1){ambiguous++;continue;}
    shifts.push(Math.abs(observed[0]-xs[0]));
  }
  return {eligibleRows:rr.size,ambiguous,missing,matched:shifts.length,mean:mean(shifts),...distribution(shifts)};
}
function occultation(masks,frame,hidden){
  const width=325*masks.dpr, members=new Set(masks.dark), dark=masks.dark.map(i=>luminance(frame,i));
  const median=quantile(dark,.5),peaks=[];
  if(!(median>0))return {median,hiddenPeaks:0,starCoincidences:null,maxOverMedian:null};
  const skyMedian=quantile(masks.dark.map(i=>luminance(hidden,i)),.5);
  for(const i of masks.dark){
    const around=[i-width-1,i-width,i-width+1,i-1,i+1,i+width-1,i+width,i+width+1];
    if(!around.every(j=>members.has(j)))continue;
    const s=luminance(hidden,i),visible=luminance(frame,i);
    if(s>skyMedian && around.every(j=>s>luminance(hidden,j)))peaks.push({i,ratio:visible/median,
      candidatePeak:around.every(j=>visible>=luminance(frame,j))});
  }
  return {median,maxOverMedian:Math.max(...dark)/median,hiddenPeaks:peaks.length,
    starCoincidences:peaks.filter(p=>p.candidatePeak&&p.ratio>3),sampledPeakRatios:distribution(peaks.map(p=>p.ratio))};
}
function compareTransitions(sequence,baseline){
  if(sequence.length<2 || sequence.length!==baseline.length)return {status:'INCOMPLETE',reason:'missing paired frames'};
  const steps=[],baseSteps=[];
  for(let i=0;i<sequence.length;i++){
    if(![sequence[i].litL,baseline[i].litL].every(Number.isFinite)||sequence[i].minute!==baseline[i].minute||
      (i>0&&sequence[i].minute!==sequence[i-1].minute+1))return {status:'INCOMPLETE',reason:'missing or unaligned geometry minute'};
    if(i){steps.push(sequence[i].litL-sequence[i-1].litL);baseSteps.push(baseline[i].litL-baseline[i-1].litL);}
  }
  return {status:'MEASURED',maxStep:Math.max(...steps),baseMaxStep:Math.max(...baseSteps),db3:Math.max(...steps)<=Math.max(...baseSteps)};
}
function buckleRate(a,b,n){
  if(n<20)return {p:null,reason:'fewer than twenty pairs of each type'};
  const pooled=(a+b)/(2*n);
  if(pooled===0||pooled===1)return {p:null,reason:'degenerate pooled variance',a,b,n};
  const z=Math.abs(a/n-b/n)/Math.sqrt(2*pooled*(1-pooled)/n);
  const t=1/(1+.2316419*z), p=2*Math.exp(-.5*z*z)/Math.sqrt(2*Math.PI)*t*
    (.319381530+t*(-.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));
  return {p:Math.min(1,p),z,a,b,n};
}
module.exports={terrain,terminator,occultation,deltaE,compareTransitions,buckleRate,lab};
