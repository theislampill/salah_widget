// Run with Node from any directory. All times are supplied, never wall clock.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {prepareScene,replayObserver} from './qualification_scene.mjs';
import {glassMembership,replayFrame,starOffset} from './stellar_replay.mjs';
import {lagSweep,populationEnvelope} from './signal_checks.mjs';
import {changedRectangles} from './changed_rectangles.mjs';
import {nativeDiscMask} from '../../real-sky/native-contract.mjs';

const read = name=>readFileSync(new URL('../../vendor/real-sky/data/'+name,import.meta.url),'utf8');
const pack = {catalogueText:read('bright-stars.json'),manifestText:read('registered-starlight/runtime-manifest.json'),
  assetTexts:{128:read('registered-starlight/V-nside128.json')}};
const glass = [{x:14,y:76,width:86,height:18},{x:18,y:276,width:289,height:24}];
const width=325,height=530, utc='2026-11-09T00:00:00Z', utcMs=Date.parse(utc);
const cfg={scope:'all',glassFactor:1,margin:0,multiplier:1};
const clear={glass,mask:null,moonRGBA:null,cloudRGBA:null};
const hash=v=>createHash('sha256').update(v).digest('hex');
function difference(a,b,predicate=()=>true) {
  let count=0,maximum=0;
  for(let i=0;i<a.length;i+=4){
    if (!predicate(i/4)) continue;
    const d=Math.max(...[0,1,2].map(k=>Math.abs(a[i+k]-b[i+k])));
    if(d) count++; maximum=Math.max(maximum,d);
  }
  return {pixels:count,maxRgbCode:maximum};
}
const evidence={scope:'reference reconstruction; registered physical raster and native operators; mock foreground/DOM bounds; pre-glass RGB; no browser timing or perception',utc,observer:replayObserver,glass,scenes:{},groups:{},moon:[]};
let dark;
for (const [scene,time] of Object.entries({dark:utc,moonlit:'2026-11-24T00:00:00Z',nearFajr:'2026-11-09T02:15:00Z',twilight:'2026-11-09T03:15:00Z',day:'2026-11-09T09:00:00Z'})) {
  const t=Date.parse(time);
  for (const tier of ['preview','refined']) {
    const frame=await prepareScene(pack,{...replayObserver,utcMs:t},tier);
    const base=replayFrame(frame.raster,frame.stars,t,cfg,clear,{paused:true}).rgba;
    const active=replayFrame(frame.raster,frame.stars,t,cfg,clear);
    evidence.scenes[scene+'-'+tier]={utc:time,physicalSunAltDeg:frame.raster.physicalState.sun.altDeg,
      physicalMoonAltDeg:frame.raster.physicalState.moon.altDeg,projected:frame.projected,
      sourceDiagnostics:frame.diagnostics,selected:active.selected.length,baselineSha256:hash(base),activeSha256:hash(active.rgba),
      change:difference(base,active.rgba),catalogueSha256:frame.catalogueSha256,diffuseSha256:frame.diffuseSha256};
    if(scene==='dark'&&tier==='refined') dark=frame;
  }
}
const base=replayFrame(dark.raster,dark.stars,utcMs,cfg,clear,{paused:true}).rgba;
for(const scope of ['preview-members','all']) for(const multiplier of [1,2,3,4]) for(const glassFactor of [0,.5,1]) {
  const conf={scope,multiplier,glassFactor,margin:4};
  const frame=replayFrame(dark.raster,dark.stars,utcMs,conf,clear);
  const areas=changedRectangles(base,frame.rgba,width,height);
  evidence.groups[[scope,multiplier,glassFactor].join('/')]={
    selected:frame.selected.length,centerUnderGlass:frame.glass.length,centerInMargin:frame.margins.length,
    encoded:difference(base,frame.rgba),
    underGlass:difference(base,frame.rgba,p=>glassMembership({x:p%width+.5,y:Math.floor(p/width)+.5},glass,0)),
    tiles:areas.length,pixelsWritten:areas.reduce((n,a)=>n+a.width*a.height,0)};
  if(multiplier===1&&glassFactor===0){
    evidence.groups[[scope,multiplier,glassFactor].join('/')].centerUnderGlassIDs=frame.glass;
    evidence.groups[[scope,multiplier,glassFactor].join('/')].centerInMarginIDs=frame.margins;
  }
}
// Historical measured header bounds, explicitly distinct from the synthetic
// boxes above and from today's unresolved glass. The times GRID was measured;
// individual equal-height rows inferred from its six children and the 6px gap.
const historicName='../../docs/state-contracts/evidence/R0003/20261111-native/candidate-chromium-report.json';
const historicBytes=readFileSync(new URL(historicName,import.meta.url));
const historic=JSON.parse(historicBytes),boxes=historic.cells.label.before.boxes;
const inset=1,scaleX=325/323,scaleY=530/528;
const normalize=([x,y,w,h])=>({x:(x-boxes.card[0]-inset)*scaleX,y:(y-boxes.card[1]-inset)*scaleY,width:w*scaleX,height:h*scaleY});
const header=[normalize(boxes.loc),normalize(boxes.buckle)];
const [gx,gy,gw,gh]=boxes.times,rowHeight=(gh-5*6)/6;
const historicalGlass=header.concat(Array.from({length:6},(_,i)=>normalize([gx,gy+i*(rowHeight+6),gw,rowHeight])));
evidence.historicalGlass={source:historicName,sourceSha256:hash(historicBytes),servedIndex:historic.servedSha256['index.html'],
  layout:'historical left strap and buckle measured; pill rectangle estimate from measured six-row grid and 6 CSS px gap; right strap dimensions absent; no blur, rounded corner, or header cutout inferred',
  nativeBounds:historicalGlass,curves:[]};
for(const scope of ['preview-members','all'])for(const margin of [0,2,4,8,16]){
  const conf={scope,margin,multiplier:2,glassFactor:0},fg={...clear,glass:historicalGlass};
  const sample=replayFrame(dark.raster,dark.stars,utcMs,conf,fg);
  evidence.historicalGlass.curves.push({scope,margin,selected:sample.selected.length,inside:sample.glass.length,marginIDs:sample.margins,
    changedUnderRectangle:difference(base,sample.rgba,p=>glassMembership({x:p%width+.5,y:Math.floor(p/width)+.5},historicalGlass,0)),
    changedOutsideRectangle:difference(base,sample.rgba,p=>!glassMembership({x:p%width+.5,y:Math.floor(p/width)+.5},historicalGlass,0))});
}
// Same registered field with distinct synthetic calendar footprints, deliberately
// crossing stars. Calendar phase does not make the dark lunar hemisphere clear.
for(const [label,x,y,radius] of [['crescent',80,72,20],['half',131,102,28],['gibbous',228,121,36],['full',262,72,43]]) {
  const mask=nativeDiscMask(width,height,{left:0,top:0,width,height},{a:1,b:0,c:0,d:1,e:x,f:y},radius);
  const fg={...clear,mask}, nominal=replayFrame(dark.raster,dark.stars,utcMs,cfg,fg,{paused:true}).rgba;
  const counters={interiorComparisons:0,interiorChanges:0,exteriorChangedFrames:0,centersCovered:dark.stars.filter(s=>Math.hypot(s.x-x,s.y-y)<radius).length};
  for(let i=0;i<60;i++){
    const frame=replayFrame(dark.raster,dark.stars,utcMs+i*1000/60,cfg,fg);
    counters.interiorComparisons+=mask.reduce((n,m)=>n+(m===0),0);
    counters.interiorChanges+=difference(nominal,frame.rgba,p=>mask[p]===0).pixels;
    counters.exteriorChangedFrames+=+(difference(nominal,frame.rgba,p=>mask[p]===1).pixels>0);
  }
  assert.equal(counters.interiorChanges,0);assert.equal(counters.exteriorChangedFrames,60);assert.ok(counters.centersCovered>0);
  evidence.moon.push({label,x,y,radius,frames:60,...counters});
}
const cloud=new Uint8ClampedArray(width*height*4);const alpha=[0,128,255];
for(let i=0;i<cloud.length;i+=4){cloud.set([103,112,124,alpha[Math.floor((i/4%width)*3/width)]],i);}
const fg={...clear,cloudRGBA:cloud},cloudNominal=replayFrame(dark.raster,dark.stars,utcMs,cfg,fg,{paused:true}).rgba;
const cloudActive=replayFrame(dark.raster,dark.stars,utcMs,cfg,fg).rgba;
evidence.cloud=alpha.map(a=>({alpha:a,...difference(cloudNominal,cloudActive,p=>cloud[p*4+3]===a)}));
assert.equal(evidence.cloud[2].pixels,0);assert.ok(evidence.cloud[1].pixels>0);
const stars=dark.stars.slice().sort((a,b)=>a.vmag-b.vmag).slice(0,12);
const count=3600, series=stars.map(s=>Array.from({length:count},(_,i)=>starOffset(s,utcMs+i*1000/60,2,{})));
const mean=a=>a.reduce((n,v)=>n+v,0)/a.length;
const corr=(a,b)=>{const ax=mean(a),bx=mean(b);let ab=0,aa=0,bb=0;for(let i=0;i<a.length;i++){
  const x=a[i]-ax,y=b[i]-bx;ab+=x*y;aa+=x*x;bb+=y*y;
}return ab/Math.sqrt(aa*bb);};
const pair=[];for(let i=0;i<series.length;i++)for(let j=0;j<i;j++) pair.push(corr(series[i],series[j]));
evidence.signal={fps:60,seconds:60,clock:'synthetic prescribed 60 Hz',multiplier:2,ids:stars.map(s=>s.id),
  maximumAbsoluteMean:Math.max(...series.map(a=>Math.abs(mean(a)))),maximumAbsoluteOffset:Math.max(...series.flat().map(Math.abs)),
  meanPairCorrelation:mean(pair),maximumAbsolutePairCorrelation:Math.max(...pair.map(Math.abs))};
evidence.autocorrelation=stars.slice(0,3).map(s=>lagSweep(s,utcMs));
const ids=JSON.parse(pack.catalogueText).stars.filter(s=>s.emission?.enabled).slice(0,640).map(s=>s.id);
evidence.populationEnvelope={selection:'first 640 enabled records in pinned catalogue; equal altitude isolates temporal covariance',
  staggered:populationEnvelope(ids,utcMs),alignedNegativeControl:populationEnvelope(ids,utcMs,true)};
assert.ok(evidence.populationEnvelope.staggered.maximumToMinimumRms<1.05);
assert.ok(evidence.populationEnvelope.alignedNegativeControl.maximumToMinimumRms>1.3);
const out=JSON.stringify(evidence,null,2)+'\n';
if(process.argv[2]) writeFileSync(process.argv[2],out);else process.stdout.write(out);
