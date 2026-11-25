'use strict';
// R0041 (issue 143) row R41-NAT: seconds below refined and refinement jobs per cell, re-derived from the in-page 4 Hz
// log that gd-vis.cjs keeps beside each launch (frames.json: inpage.log rows [sys, x, y, w, visibleSource, current,
// key, moonReady, composed, visible, pageNow]; inpage.jobs). No browser is launched; it reads recordings already made.
// Per cell, over the observation [first refined result, end of observation before the end control):
//   belowRefinedSeconds = 0.25 s x samples whose visibleSource is not 'refined-terrain'
//   notCurrentSeconds   = 0.25 s x samples with observe().current false
//   jobs                = refinement jobs posted to the Moon worker in that span
//   startupSeconds      = first log sample to the first refined-terrain sample (time below refined at start-up)
// Usage: node nat.cjs <outJson> <label>=<launchDir>[,<launchDir>...] ...   (a launch dir holds one folder per cell)
const fs=require('node:fs'),path=require('node:path');
const [outFile,...groups]=process.argv.slice(2);
const out={schema:'r0041-nat/1',rule:'4 Hz in-page samples; 0.25 s per sample; span = first refined-terrain sample .. last sample before the end control',groups:{}};
for(const g of groups){const [label,dirs]=g.split('=');const rows=[];
  for(const d of dirs.split(',')){const launch=path.basename(d);const meta=fs.existsSync(d+'.json')?JSON.parse(fs.readFileSync(d+'.json','utf8')):null;
    for(const cell of fs.readdirSync(d)){const f=path.join(d,cell,'frames.json');if(!fs.existsSync(f))continue;
      const F=JSON.parse(fs.readFileSync(f,'utf8')),log=F.inpage.log||[],jobs=F.inpage.jobs||[];
      const first=log.findIndex(e=>e[4]==='refined-terrain');const cm=meta?.cells?.[cell];
      const endAt=cm?.absentControl&&F.shots?.find(s=>s.inCtl)?.t0||log.at(-1)?.[0];
      const span=first<0?[]:log.slice(first).filter(e=>e[0]<endAt);
      rows.push({launch,cell,engine:meta?.engine,dpr:meta?.dpr,motion:meta?.motion,settled:first>=0,
        startupSeconds:first<0?null:+((log[first][0]-log[0][0])/1000).toFixed(2),observedSeconds:+(span.length*0.25).toFixed(1),
        belowRefinedSeconds:+(span.filter(e=>e[4]!=='refined-terrain').length*0.25).toFixed(2),
        notCurrentSeconds:+(span.filter(e=>!e[5]).length*0.25).toFixed(2),
        sourcesSeen:[...new Set(span.map(e=>e[4]))],
        jobs:first<0?null:jobs.filter(j=>j.sys>=log[first][0]&&j.sys<endAt).length});}}
  out.groups[label]=rows;}
fs.writeFileSync(outFile,JSON.stringify(out,null,1)+'\n');
for(const [k,rows] of Object.entries(out.groups))for(const r of rows)console.log(k,r.launch,r.cell,'below',r.belowRefinedSeconds,'notCurrent',r.notCurrentSeconds,'jobs',r.jobs,'startup',r.startupSeconds,'obs',r.observedSeconds);
