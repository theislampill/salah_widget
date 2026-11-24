'use strict';
// R0041 (issue 143): aggregate gd-vis.cjs / swp.cjs launch summaries into one slim JSON (no frame logs, no paths).
// The verdict is RE-DERIVED here from the per-frame records (frames.json beside each launch) with one rule for every
// launch (rule v3): ABSENT if point-like stars above baseline >= 10, or the disc mean moved > 4 codes from the last
// PRESENT frame at least 1 s earlier, or the mean per-pixel change exceeds 4 AND the mean moved > 1 code. The last
// clause exists because a sub-pixel move of the Moon slot changes which pixels are sampled (seen: a present, unchanged
// disc at 4.75 mean per-pixel change and 0.0 mean change), which otherwise locks a rolling reference.
// Usage: node gd-aggregate.cjs <outJson> <label> <launchJson>...
const fs=require('node:fs'),path=require('node:path');
const [outFile,label,...files]=process.argv.slice(2);
const out={schema:'r0041-gd-aggregate/1',label,rule:'v3: stars>=10 || dMean>4 || (dRoll>4 && dMean>1)',launches:[],cells:[]};
function replay(list,tKey,from,to){let refMean=null,refT=-1e18,abs=[];const res=[],seedN={},seedA={};let ctlN=0,ctlA=0;
  let started=false;for(const f of list){const t=f[tKey];if(f.dFixed!=null)started=true;if(t==null||f.mean==null||!started)continue;   // frames before the settled reference (and its star baseline) exist are not judged
const excl=f.inSeed||f.inCtl;
    if(refMean==null&&t>from&&!excl&&f.stars<10){refMean=f.mean;refT=t;}
    const dMean=refMean==null?0:Math.abs(f.mean-refMean),a=f.stars>=10||dMean>4||((f.dRoll??0)>4&&dMean>1);
    if(!a&&!excl&&t-refT>=1000){refMean=f.mean;refT=t;}
    if(t>from&&t<to&&!excl)res.push({t,a});
    if(f.inSeed){seedN[f.inSeed]=(seedN[f.inSeed]||0)+1;if(a)seedA[f.inSeed]=(seedA[f.inSeed]||0)+1;}
    if(f.inCtl){ctlN++;if(a)ctlA++;}}
  const iv=[];let open=null;for(const x of res){if(x.a&&open==null)open=x.t;if(!x.a&&open!=null){iv.push(x.t-open);open=null;}}if(open!=null)iv.push(null);
  return {judged:res.length,absent:res.filter(x=>x.a).length,intervalsMs:iv,at:res.filter(x=>x.a).map(x=>x.t),positiveControls:{seedFrames:seedN,seedAbsent:seedA,endControlFrames:ctlN,endControlAbsent:ctlA}};}
for(const f of files){const o=JSON.parse(fs.readFileSync(f,'utf8'));
  out.launches.push({label:o.label,tree:o.root,engine:o.engine,dpr:o.dpr,motion:o.motion,browserVersion:o.browserVersion,secondsAfterSettle:o.secondsAfterSettle,isolation:o.isolation});
  for(const [name,c] of Object.entries(o.cells)){if(c.error){out.cells.push({launch:o.label,cell:name,error:c.error});continue;}
    const fr=path.join(path.dirname(f),o.label,name,'frames.json');let v3=null,v3ctl=null;
    if(fs.existsSync(fr)){const F=JSON.parse(fs.readFileSync(fr,'utf8'));const steps=(c.perStep||[]).map(p=>p.sys);const from=steps.length?steps[0]-60000:0,to=(c.perStep&&c.perStep.length)?Math.max(...steps)+15000:1e18;
      const endAt=Math.min(to,...(F.shots||[]).filter(x=>x.inCtl).map(x=>x.t0-1000));   // the end control is applied about 300 ms before its first labelled shot
      const sh=replay(F.shots||[],'t',from,endAt),vi=replay(F.video||[],'sys',from,endAt);
      const perStep=steps.map(s=>({shots:sh.at.filter(t=>t>=s-1000&&t<s+15000).length,recording:vi.at.filter(t=>t>=s-1000&&t<s+15000).length}));
      const vc=(F.video||[]).filter(x=>x.inCtl);v3ctl={reanalysed:!!F.videoReanalysed,recordingControlFrames:vc.length,recordingControlAbsent:vc.filter(x=>x.absentRoll).length};
      v3={shots:{judged:sh.judged,absent:sh.absent,intervalsMs:sh.intervalsMs,controls:sh.positiveControls},recording:{judged:vi.judged,absent:vi.absent,intervalsMs:vi.intervalsMs,controls:vi.positiveControls},stepsWithAbsentShot:perStep.filter(p=>p.shots).length,stepsWithAbsentRecordedFrame:perStep.filter(p=>p.recording).length,
        absentOutsideStepWindows:{shots:sh.at.filter(t=>!steps.some(s=>t>=s-1000&&t<s+15000)).length,recording:vi.at.filter(t=>!steps.some(s=>t>=s-1000&&t<s+15000)).length}};}
    out.cells.push({v3,launch:o.label,engine:o.engine,dpr:o.dpr,motion:o.motion,cell:name,instant:c.iso,valid:(c.invalidReasons||[]).filter(r=>!/seeded detail\.clear\(\) not seen/.test(r)).filter(r=>!(v3ctl&&v3ctl.reanalysed&&/absent control not classified absent in the recording/.test(r)&&v3ctl.recordingControlFrames>0&&v3ctl.recordingControlAbsent>=v3ctl.recordingControlFrames*0.5)).length===0,v3ctl,invalidReasons:c.invalidReasons,recipeValid:c.valid,minuteSteps:c.minuteSteps,
      stepsWithAbsentShot:(c.perStep||[]).filter(p=>p.shotsAbsentRoll>0).length,stepsWithAbsentRecordedFrame:(c.perStep||[]).filter(p=>p.videoAbsentRoll>0).length,
      shots:{count:c.shots.count,medianIntervalMs:c.shots.medianIntervalMs,p90IntervalMs:c.shots.p90IntervalMs,absent:c.shots.absentRoll,absentLiteralG1:c.shots.absentLiteral,absentFixedReference:c.shots.absentFixed,absentIntervalsMs:c.shots.absentRollIntervals.map(i=>i.ms)},
      recording:c.video.error?{error:c.video.error}:{frames:c.video.frames,unreadableMarker:c.video.unreadableMarker,observed:c.video.observed,offset:c.video.offset,absent:c.video.absentRoll,absentLiteralG1:c.video.absentLiteral,absentIntervalsMs:c.video.absentRollIntervals.map(i=>i.ms)},
      refinementJobs:c.jobsPosted,acceptedRecordChanges:c.acceptedRecordChanges,swaps:c.swaps,forced:c.forced?c.forced.length:undefined,truthAtEnd:c.truthAtEnd,
      light:{distinct:c.light.distinct.length,values:[...new Set(c.light.distinct.map(x=>x.split(' ').slice(0,2).join(' ')))],phaseFraction:c.light.phaseFraction,moonAltitudeDeg:c.light.moonAltitudeDeg},
      seed:c.seed?{detailClear:c.seed.detailClear,styleHide300ms:c.seed.styleHide300ms}:null,absentControl:c.absentControl,hiddenSamples:c.hiddenSamples,pageErrors:c.pageErrors.length});}}
fs.writeFileSync(outFile,JSON.stringify(out,null,1)+'\n');
const t={};for(const c of out.cells){if(c.error)continue;const k=c.cell;t[k]=t[k]||{cells:0,valid:0,steps:0,stepsAbsentShot:0,stepsAbsentRec:0,absentShots:0,absentRec:0,jobs:0};const x=t[k];x.cells++;x.valid+=c.valid?1:0;x.steps+=c.minuteSteps;x.stepsAbsentShot+=c.v3?c.v3.stepsWithAbsentShot:0;x.stepsAbsentRec+=c.v3?c.v3.stepsWithAbsentRecordedFrame:0;x.absentShots+=c.v3?c.v3.shots.absent:0;x.absentRec+=c.v3?c.v3.recording.absent:0;x.jobs+=c.refinementJobs;}
console.log(JSON.stringify(t,null,0));
