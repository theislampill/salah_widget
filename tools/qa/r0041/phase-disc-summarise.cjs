'use strict';
// R0041 phase-disc witness: per-cell aggregate of phase-disc-witness.cjs output. Recipe; NOT part of the node glob.
// A cell is one engine x pixel ratio x motion. An INVALID run is reported as invalid and is never counted as a pass.
// Usage: node phase-disc-summarise.cjs <witness.json> [<witness.json> ...]  -> JSON on stdout
const fs=require('node:fs');
const out={};
for(const file of process.argv.slice(2)){
  for(const [key,cell] of Object.entries(JSON.parse(fs.readFileSync(file,'utf8')))){
    const routes={},agg={key,engine:cell.engine,dpr:cell.dpr,motion:cell.motion,startISO:cell.startISO,red:!!cell.red,error:cell.error??null,isolationAllowedExternal:cell.isolation?.allowedExternal??null,
      loads:cell.runs.length,invalidLoads:cell.runs.filter(r=>!r.valid).map(r=>({run:r.run,kind:r.kind,invalid:r.invalid})),routes,opacity:[],handover:[],renderMs:[],initialRenderMs:[],receiverCalls:[],pageErrors:[...new Set(cell.runs.flatMap(r=>r.pageErrors??[]))],raf:{frames:0,notCurrent:0,moonReadyOff:0}};
    for(const r of cell.runs){
      for(const [name,v] of Object.entries(r.routes??{})){const o=routes[name]??={runs:0,events:0,frames:0,blankFrames:0,eventsWithBlank:0,maxAbsentMs:0};
        o.runs++;o.events+=v.events??0;o.frames+=v.frames??0;o.blankFrames+=v.blank??0;o.eventsWithBlank+=v.eventsWithBlank??(v.blank?1:0);o.maxAbsentMs=Math.max(o.maxAbsentMs,v.maxAbsentMs??0);
        if(name==='startup')(o.firstSkyMs??=[]).push(v.firstSkyMs);}
      if(r.opacity)agg.opacity.push(r.opacity);if(r.handover)agg.handover.push({kind:r.kind,...r.handover});
      if(r.renderMs?.phaseDisc!=null)agg.renderMs.push(+r.renderMs.phaseDisc.toFixed(1));if(r.initialRenderMs!=null)agg.initialRenderMs.push(+r.initialRenderMs.toFixed(1));if(r.receiverCalls!=null)agg.receiverCalls.push(r.receiverCalls);
      if(r.raf){agg.raf.frames+=r.raf.frames;agg.raf.notCurrent+=r.raf.notCurrent;agg.raf.moonReadyOff+=r.raf.moonReadyOff;}
    }
    out[key]=agg;
  }
}
console.log(JSON.stringify(out,null,1));
