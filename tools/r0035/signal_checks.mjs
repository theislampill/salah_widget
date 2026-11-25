import {starModes,starOffset} from './stellar_replay.mjs';

// Normalized correlation on a fixed-length window at every lag, including
// each window's own mean. Do not use missing overlap to dilute the tails.
export function lagSweep(star,startMs) {
  const hz=20,n=6000,first=5*hz,last=300*hz;
  const s=Float64Array.from({length:n+last},(_,i)=>starOffset(star,startMs+1000*i/hz,2,{}));
  const sum=new Float64Array(s.length+1),squares=new Float64Array(s.length+1);
  for(let i=0;i<s.length;i++){sum[i+1]=sum[i]+s[i];squares[i+1]=squares[i]+s[i]**2;}
  let maxAbsoluteCorrelation=0,lagSeconds=null;
  for(let k=first;k<=last;k++){
    let xy=0;for(let i=0;i<n;i++) xy+=s[i]*s[i+k];
    const sx=sum[n],sy=sum[k+n]-sum[k],vx=squares[n]-sx*sx/n,vy=squares[k+n]-squares[k]-sy*sy/n;
    const r=(xy-sx*sy/n)/Math.sqrt(vx*vy);
    if(Math.abs(r)>maxAbsoluteCorrelation){maxAbsoluteCorrelation=Math.abs(r);lagSeconds=k/hz;}
  }
  return {id:star.id,hz,referenceSeconds:n/hz,firstLagSeconds:5,lastLagSeconds:300,maxAbsoluteCorrelation,lagSeconds};
}

// Equal-altitude catalogue control isolates periodic population power from
// flux, altitude and orbital drift. Correlated envelopes evade signed
// pairwise correlation. Compare the retained model with an aligned control.
export function populationEnvelope(ids,startMs,aligned=false) {
  const stars=ids.map(id=>{const modes=starModes(id);if(aligned)modes.offsetMs=0;return {detectable:true,altDeg:35,modes};});
  const rms=Array.from({length:8},(_,phase)=>{
    let squared=0;
    for(let cycle=0;cycle<12;cycle++)for(const s of stars){
      const v=starOffset(s,startMs+cycle*2000+phase*250,2,{});squared+=v*v;
    }
    return Math.sqrt(squared/(12*stars.length));
  });
  return {starCount:stars.length,cycles:12,altitudeDeg:35,phaseStepMs:250,rms,maximumToMinimumRms:Math.max(...rms)/Math.min(...rms)};
}
