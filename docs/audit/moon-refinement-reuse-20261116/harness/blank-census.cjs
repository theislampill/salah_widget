'use strict';
// Moon-reuse audit, Job 2: blank-disc events and star visibility inside the disc in blank frames.
// Model frame analysis, NOT human perception. Usage: node blank-census.cjs <out.json> <cropDir> <defect-*.json...>
const fs=require('node:fs'),path=require('node:path');const {decodePng}=require('./png.cjs');
const [outFile,cropDir,...ins]=process.argv.slice(2);const out={};
function discStats(file){const img=decodePng(fs.readFileSync(file)),W=img.width,H=img.height,cx=W/2,cy=H/2,R=.47*Math.min(W,H);const L=[];
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){if((x+.5-cx)**2+(y+.5-cy)**2>R*R)continue;const i=4*(y*W+x);L.push(.2126*img.data[i]+.7152*img.data[i+1]+.0722*img.data[i+2]);}
  const s=[...L].sort((a,b)=>a-b),med=s[s.length>>1];return {meanLuma:+(L.reduce((a,b)=>a+b,0)/L.length).toFixed(2),medianLuma:+med.toFixed(2),maxLuma:+s.at(-1).toFixed(1),starLikePixels:L.filter(v=>v>med+40).length,discPixels:L.length};}
for(const f of ins)for(const [label,d] of Object.entries(JSON.parse(fs.readFileSync(f,'utf8')))){
  const fr=d.frames||[],n=fr[0]&&fr[0].discPixels||1;
  const ev=fr.filter(x=>x.changed>=.9*x.discPixels&&x.over8>=.3*x.discPixels);
  const pairs=[];for(let i=0;i+1<ev.length;i+=2)if(ev[i+1].t-ev[i].t<3000)pairs.push({startS:+(ev[i].t/1000).toFixed(2),visibleBlankMsUpperBound:Math.round(ev[i+1].t-ev[i].t)});
  const crops=(d.crops||[]).map(c=>({t:+(c.t/1000).toFixed(2),before:discStats(path.join(cropDir,c.before)),after:discStats(path.join(cropDir,c.after))}));
  out[label]={frameIntervalMs:Math.round(d.frameSummary.meanIntervalMs),jobs:(d.workerLog||[]).filter(x=>x.kind==='render').length,blankEvents:pairs.length,blank:pairs,crops};
}
fs.writeFileSync(outFile,JSON.stringify(out,null,1));
for(const [k,v] of Object.entries(out))console.log(k,'jobs',v.jobs,'blanks',v.blankEvents,v.blank.map(b=>b.visibleBlankMsUpperBound).join(','),'crop0',v.crops[0]?JSON.stringify({b:v.crops[0].before.meanLuma,a:v.crops[0].after.meanLuma,stars:v.crops[0].after.starLikePixels,starsBefore:v.crops[0].before.starLikePixels}):'');
