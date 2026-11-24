'use strict';
// R0041 (issue 143) preview-host A/B: per SalahSkyPreview.clear call of a swp.cjs launch (flag preview), the v3-ABSENT
// recorded frames (same rule as gd-aggregate.cjs) in [call-40 ms, call+1000 ms). Usage: node pv-clear.cjs <outDir> <label>...
const fs=require('fs'),path=require('path');
const [outDir,...labels]=process.argv.slice(2);const res={};
for(const label of labels){const L=JSON.parse(fs.readFileSync(path.join(outDir,label+'.json'),'utf8'));const tree=L.root;
  const T=res[label]={tree,isolation:L.isolation.allowedExternal,cells:[]};
  for(const [name,c] of Object.entries(L.cells)){if(c.error){T.cells.push({name,error:c.error.slice(0,120)});continue;}
    const F=JSON.parse(fs.readFileSync(path.join(outDir,label,name,'frames.json'),'utf8'));
    const ctl0=Math.min(...F.shots.filter(x=>x.inCtl).map(x=>x.t0-1000));
    let refMean=null,refT=-1e18,refFm=null,started=false;const judged=[];let shifted=0;
    for(const f of F.video||[]){const t=f.sys;if(f.dFixed!=null)started=true;if(t==null||f.mean==null||!started)continue;const excl=f.inSeed||f.inCtl;
      if(refMean==null&&!excl&&f.stars<10){refMean=f.mean;refT=t;if(f.fm!=null)refFm=f.fm;}
      if(f.fm!=null&&refFm!=null&&Math.abs(f.fm-refFm)>6&&!excl){if(t<ctl0)shifted++;continue;}
      const dMean=refMean==null?0:Math.abs(f.mean-refMean),a=f.stars>=10||dMean>4||((f.dRoll??0)>4&&dMean>1);
      if(!a&&!excl&&t-refT>=1000){refMean=f.mean;refT=t;if(f.fm!=null)refFm=f.fm;}
      if(!excl&&t<ctl0)judged.push({t,a,mean:f.mean,ref:refMean});}
    const clears=(F.inpage.forced||[]).filter(x=>x[0]==='preview-clear').map(x=>x[1]);
    const inval=(F.inpage.forced||[]).filter(x=>x[0]==='sky-invalidate').map(x=>x[1]);
    const per=clears.map(t=>{const w=judged.filter(f=>f.t>=t-40&&f.t<t+1000&&f.a);return {absentFrames:w.length,offsetsMs:w.map(f=>f.t-t),means:w.map(f=>[+f.ref.toFixed(1),f.mean])};});
    const all=judged.filter(f=>f.a);
    const ctlFrames=(F.video||[]).filter(x=>x.inCtl);
    T.cells.push({name,valid:c.valid,invalidReasons:c.invalidReasons,settled:c.settledToRefined,clears:clears.length,invalidates:inval.length,clearsWithAbsent:per.filter(p=>p.absentFrames).length,per:per.filter(p=>p.absentFrames),
      recordedJudged:judged.length,recordedAbsentTotal:all.length,absentNotNearClear:all.filter(f=>!clears.some(t=>f.t>=t-40&&f.t<t+1000)).map(f=>({t:f.t,nearestInvalidateMs:Math.min(...inval.map(i=>f.t-i).filter(d=>d>=-40))})),wholeFrameShiftNotJudged:shifted,
      endControl:{frames:ctlFrames.length,absent:ctlFrames.filter(x=>x.absentRoll).length},swaps:c.swaps,videoUnreadable:c.video.unreadableMarker,videoFrames:c.video.frames,truthAtEnd:c.truthAtEnd});}}
console.log(JSON.stringify(res,null,1));
