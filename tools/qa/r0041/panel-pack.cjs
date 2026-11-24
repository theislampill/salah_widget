'use strict';
// R0041 (issue 143) rows R41-GD and R41-REV: build the visual-panel pack from gd-vis.cjs / swp.cjs outputs. Recipe;
// NOT part of the node glob. Output goes to a PRIVATE directory (never committed): blinded items, each with
//   clip-<k>.mp4   the real-time recording from 3 s before to 4 s after a page-clock minute step (re-encoded, 25 fps)
//   strip-<k>.png  every recorded frame of that clip's Moon slot side by side (CSS-size recording crops, 2x enlarged)
//   native/        native-size (device-pixel) shots around the step when the run saved them (swp.cjs strip flag)
// and key.json mapping item IDs to their source (tree, engine, DPR, motion, cell) - for the integrator, NOT for judges.
// Blinding: item IDs are shuffled with a seeded PRNG; window and control cells, and the two trees, get no label.
// Usage: node panel-pack.cjs <outDir> <seed> <steps=3> <runDir>[,<runDir>...]
//   each runDir is "<tree tag>|<directory holding <label>.json and <label>/<cell>/>"
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const [outDir,seedArg,stepsArg,runsArg]=process.argv.slice(2);const STEPS=+(stepsArg||3);
let seed=+seedArg||1;const rnd=()=>{seed=(seed*1103515245+12345)%2147483648;return seed/2147483648;};
fs.mkdirSync(outDir,{recursive:true});const items=[];
for(const spec of runsArg.split(',')){const [tag,dir]=spec.split('|');
  for(const f of fs.readdirSync(dir).filter(f=>f.endsWith('.json'))){const o=JSON.parse(fs.readFileSync(path.join(dir,f),'utf8'));if(!o.cells)continue;
    for(const [cell,c] of Object.entries(o.cells)){if(c.error||!c.video||c.video.error)continue;const cdir=path.join(dir,o.label,cell),fr=path.join(cdir,'frames.json');if(!fs.existsSync(fr))continue;
      const frames=JSON.parse(fs.readFileSync(fr,'utf8')).video||[];
      for(const st of (c.perStep||[]).slice(0,STEPS)){const near=frames.filter(v=>v.sys!=null&&Math.abs(v.sys-st.sys)<60);if(!near.length)continue;
        items.push({tree:tag,engine:o.engine,dpr:o.dpr,motion:o.motion,cell,instant:c.iso,step:st.pageISO,videoFile:path.join(cdir,cell+'.webm'),frameIndex:near[0].i,cdir,stepSys:st.sys,detector:{shotsAbsent:st.shotsAbsentRoll,recordedAbsent:st.videoAbsentRoll}});}}}}
for(let i=items.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[items[i],items[j]]=[items[j],items[i]];}
const key=[];items.forEach((it,k)=>{const id='P'+String(k+1).padStart(3,'0'),d=path.join(outDir,id);fs.mkdirSync(d,{recursive:true});
  const t0=Math.max(0,it.frameIndex/25-3);
  try{execFileSync('ffmpeg',['-v','error','-y','-ss',String(t0),'-i',it.videoFile,'-t','7','-r','25','-c:v','libx264','-pix_fmt','yuv420p','-crf','12',path.join(d,'clip.mp4')]);}catch(e){}
  try{execFileSync('ffmpeg',['-v','error','-y','-ss',String(t0+2),'-i',it.videoFile,'-t','3','-vf','crop=120:120:205:0,scale=240:240:flags=neighbor,tile=15x5','-frames:v','1',path.join(d,'strip.png')]);}catch(e){}
  const nat=path.join(it.cdir,'strip');if(fs.existsSync(nat)){const nd=path.join(d,'native');fs.mkdirSync(nd,{recursive:true});for(const f of fs.readdirSync(nat)){const t=+(f.match(/-(\d+)\.png$/)||[])[1];if(Math.abs(t-it.stepSys)<=1600)fs.copyFileSync(path.join(nat,f),path.join(nd,'t'+String(t-it.stepSys).padStart(6,'0')+'ms.png'));}}
  key.push({id,...it,videoFile:undefined,cdir:undefined});});
fs.writeFileSync(path.join(outDir,'..','key-'+path.basename(outDir)+'.json'),JSON.stringify(key,null,1));
console.log('items',items.length,'key written beside the pack (keep it from the judges)');
