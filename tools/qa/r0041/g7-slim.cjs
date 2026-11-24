'use strict';
// R0041 (issue 143) G7: the post-processor that turned g7-profile.cjs outputs into the committed evidence under
// docs/state-contracts/evidence/R0041/owner-gates/g7/. Per return it replaces the raw `calls` records by three sums:
// listenersMs (each visibilitychange listener), inDispatchMs (named entry points that STARTED before the dispatch
// ended) and within1500Ms (the same entry points over the whole 1.5 s window). The raw `calls` are not kept, so figures
// for a window other than 1.5 s (for example "within 1 s") cannot be re-derived from the committed files; re-run the
// recipe for those. Usage: node g7-slim.cjs <in.json> <out.json> <treeLabel>
const fs=require('node:fs');
const [inp,outp,tree]=process.argv.slice(2);
const NAMES=['SalahMoonInitial.render','SalahMoonDetail.adopt','SalahMoonDetail.compose','SalahSkyPreview.update','SalahSkyPreview.present','toDataURL','SalahRealSky.compose','writePrayerStatus','SalahMoonRuntime.request'];
const o=JSON.parse(fs.readFileSync(inp,'utf8'));
o.returns=o.returns.map(r=>{const {calls,...rest}=r;const inTask={},within={},listeners={};
  for(const c of calls){if(c[0].startsWith('L ')){const k=c[0].slice(0,60);listeners[k]=+((listeners[k]||0)+c[2]).toFixed(2);}
    if(NAMES.includes(c[0])){within[c[0]]=+((within[c[0]]||0)+c[2]).toFixed(2);if(c[1]<r.dispatchMs)inTask[c[0]]=+((inTask[c[0]]||0)+c[2]).toFixed(2);}}
  return {...rest,listenersMs:listeners,inDispatchMs:inTask,within1500Ms:within};});
o.tree=tree;delete o.root;
fs.writeFileSync(outp,JSON.stringify(o,null,1)+'\n');
