'use strict';
// R0041 (issue 143): aggregate gd-vis.cjs / swp.cjs launch summaries into one slim JSON (no frame logs, no paths).
// Usage: node gd-aggregate.cjs <outJson> <label> <launchJson>...
const fs=require('node:fs'),path=require('node:path');
const [outFile,label,...files]=process.argv.slice(2);
const out={schema:'r0041-gd-aggregate/1',label,launches:[],cells:[]};
for(const f of files){const o=JSON.parse(fs.readFileSync(f,'utf8'));
  out.launches.push({label:o.label,tree:o.root,engine:o.engine,dpr:o.dpr,motion:o.motion,browserVersion:o.browserVersion,secondsAfterSettle:o.secondsAfterSettle,isolation:o.isolation});
  for(const [name,c] of Object.entries(o.cells)){if(c.error){out.cells.push({launch:o.label,cell:name,error:c.error});continue;}
    out.cells.push({launch:o.label,engine:o.engine,dpr:o.dpr,motion:o.motion,cell:name,instant:c.iso,valid:c.valid,invalidReasons:c.invalidReasons,minuteSteps:c.minuteSteps,
      stepsWithAbsentShot:(c.perStep||[]).filter(p=>p.shotsAbsentRoll>0).length,stepsWithAbsentRecordedFrame:(c.perStep||[]).filter(p=>p.videoAbsentRoll>0).length,
      shots:{count:c.shots.count,medianIntervalMs:c.shots.medianIntervalMs,p90IntervalMs:c.shots.p90IntervalMs,absent:c.shots.absentRoll,absentLiteralG1:c.shots.absentLiteral,absentFixedReference:c.shots.absentFixed,absentIntervalsMs:c.shots.absentRollIntervals.map(i=>i.ms)},
      recording:c.video.error?{error:c.video.error}:{frames:c.video.frames,unreadableMarker:c.video.unreadableMarker,observed:c.video.observed,offset:c.video.offset,absent:c.video.absentRoll,absentLiteralG1:c.video.absentLiteral,absentIntervalsMs:c.video.absentRollIntervals.map(i=>i.ms)},
      refinementJobs:c.jobsPosted,acceptedRecordChanges:c.acceptedRecordChanges,swaps:c.swaps,forced:c.forced?c.forced.length:undefined,truthAtEnd:c.truthAtEnd,
      light:{distinct:c.light.distinct.length,values:[...new Set(c.light.distinct.map(x=>x.split(' ').slice(0,2).join(' ')))],phaseFraction:c.light.phaseFraction,moonAltitudeDeg:c.light.moonAltitudeDeg},
      seed:c.seed?{detailClear:c.seed.detailClear,styleHide300ms:c.seed.styleHide300ms}:null,absentControl:c.absentControl,hiddenSamples:c.hiddenSamples,pageErrors:c.pageErrors.length});}}
fs.writeFileSync(outFile,JSON.stringify(out,null,1)+'\n');
const t={};for(const c of out.cells){if(c.error)continue;const k=c.cell;t[k]=t[k]||{cells:0,valid:0,steps:0,stepsAbsentShot:0,stepsAbsentRec:0,absentShots:0,absentRec:0,jobs:0};const x=t[k];x.cells++;x.valid+=c.valid?1:0;x.steps+=c.minuteSteps;x.stepsAbsentShot+=c.stepsWithAbsentShot;x.stepsAbsentRec+=c.stepsWithAbsentRecordedFrame;x.absentShots+=c.shots.absent;x.absentRec+=c.recording.absent||0;x.jobs+=c.refinementJobs;}
console.log(JSON.stringify(t,null,0));
