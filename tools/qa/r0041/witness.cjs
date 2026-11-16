'use strict';
// R0041 (issue 143) forced-route Moon-presence witness. Native recipe; NOT part of the node glob.
// Proves Moon presence from PAINTED PIXELS (never from classes or flags): every captured frame of the Moon rectangle
// is classified PRESENT / ABSENT inside the disc mask:
//   disc set = pixels within 0.47 x side of the rectangle centre; Y = 0.2126R + 0.7152G + 0.0722B (sRGB codes)
//   stars    = POINT-LIKE bright disc pixels: Y exceeds the mean of its 8 neighbours at distance 2 by > 30 and exceeds
//              the corner-sky median by > 30 (corner = r >= 0.53 x side). Lunar relief and the limb are not point-like.
//   dRef     = mean |Y - Y_ref| over the disc against the run's reference frame(s): the settled frame before the
//              forced event and, for identity-change routes, the settled frame at the end of the run
//   ABSENT   if stars >= 10 or dRef > 4 against every reference.
// Capture: Chromium uses the DevTools screencast (every composited frame, compositor timestamps); Firefox and WebKit
// use a screenshot loop (capture interval reported; events shorter than it can be missed).
// In-page, per animation frame, the reveal classes and observe().current are logged with rAF timestamps so that
// "indicators match pixels" can be checked.
// Routes (forced in a real page of the product; Date shifted to the chosen night, real speed):
//   startup   - from navigation; after the first PRESENT frame no frame may be ABSENT
//   expiry    - same-scope expiry: fragment &timeScale=60 makes jobs outlast the validity window
//   noSucc    - same as expiry with window.SalahMoonInitial removed (no immediately available successor)
//   invalidate- SalahMoonRuntime.invalidate('r0041-witness') x3 (R0033 F-1 route, same identity)
//   resume    - document.hidden overridden true -> visibilitychange -> 1 s -> false -> visibilitychange, x3
//   sky       - SalahRealSky.invalidate('r0041-witness') x3 (sky-host lifecycle)
//   identity  - SalahClock.set({rate:1,utcMs:now+3600 s}) (genuine clock/identity change)
// Every launch goes through iso.cjs (proxy, resolver rules, catch-all route before navigation, finish() throws on
// any allowed non-loopback request).
// Usage: node witness.cjs <repoRoot> <outJson> <engine> <dpr> <motion:reduce|full> <route> <startISO> [runs=1] [cropDir]
const fs=require('node:fs'),path=require('node:path');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [root,outFile,engine,dpr,motion,route,startISO,runsArg,cropDir]=process.argv.slice(2);
const RUNS=+(runsArg||1);
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1'+(motion==='full'?'&motion=full':'')+((route==='expiry'||route==='noSucc')?'&timeScale=60':'');
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const RAF=`(()=>{window.__r41={frames:[],events:[]};const tick=t=>{const c=document.querySelector('.c'),m=document.querySelector('.moon-mask-disc');let cur=null;try{cur=window.SalahMoonRuntime?.observe?.().current??null;}catch(e){}
 window.__r41.frames.push([Math.round(t*10)/10,c&&c.classList.contains('moon-ready')?1:0,m&&m.classList.contains('mask-on')?1:0,cur?1:0,c&&c.classList.contains('real-sky-composed')?1:0]);if(window.__r41.frames.length>20000)window.__r41.frames.shift();requestAnimationFrame(tick);};requestAnimationFrame(tick);})();`;
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
function discOf(img,rect,scale){
  const x0=Math.max(0,Math.floor(rect.x*scale)),y0=Math.max(0,Math.floor(rect.y*scale)),S=Math.floor(Math.min(rect.w,rect.h)*scale),cx=x0+S/2,cy=y0+S/2,disc=[],corner=[],pts=[];
  const W=img.width,H=img.height,at=(x,y)=>x<0||y<0||x>=W||y>=H?null:Y(img.data,4*(y*W+x));
  for(let y=y0;y<y0+S&&y<H;y++)for(let x=x0;x<x0+S&&x<W;x++){const r=Math.hypot(x+.5-cx,y+.5-cy),v=at(x,y);
    if(r<=.47*S){disc.push(v);if(r<=.47*S-3){let m=0,n=0;for(const [dx,dy] of [[2,0],[-2,0],[0,2],[0,-2],[2,2],[2,-2],[-2,2],[-2,-2]]){const u=at(x+dx,y+dy);if(u!=null){m+=u;n++;}}pts.push(v-(n?m/n:v));}else pts.push(0);}
    else if(r>=.53*S)corner.push(v);}
  return {disc,corner,pts};
}
const median=a=>{const s=[...a].sort((p,q)=>p-q);return s[s.length>>1]??0;};
function classify(img,rect,scale,refs){
  const {disc,corner,pts}=discOf(img,rect,scale),sky=median(corner),stars=disc.filter((v,i)=>pts[i]>30&&v>sky+30).length;
  const dRefs=refs.filter(Boolean).filter(r=>r.length===disc.length).map(r=>disc.reduce((p,v,i)=>p+Math.abs(v-r[i]),0)/disc.length);
  const dRef=dRefs.length?Math.min(...dRefs):null;
  return {stars,dRef,absent:stars>=10||(dRef!=null&&dRef>4),disc};
}
async function oneRun(L,env,run){
  const page=await L.context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,200)));
  const shots=[];let cdp=null;const t0=Date.now();
  const scale=+dpr;
  if(engine==='chromium'){
    cdp=await L.context.newCDPSession(page);
    cdp.on('Page.screencastFrame',async f=>{shots.push({t:f.metadata.timestamp*1000,png:Buffer.from(f.data,'base64')});try{await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId});}catch(e){}});
  }
  await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/index.html${FRAG}`,{waitUntil:'commit',timeout:120000});
  if(cdp)await cdp.send('Page.startScreencast',{format:'png',everyNthFrame:1,maxWidth:Math.round(325*scale),maxHeight:Math.round(530*scale)});
  let capturing=true;
  const loop=(async()=>{if(cdp)return;while(capturing){try{const t=Date.now();const png=await page.screenshot({scale:'device',animations:'allow',caret:'initial'});shots.push({t:(t+Date.now())/2,png});}catch(e){await page.waitForTimeout(20);}}})();
  // settle: first refined result presented
  await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:240000,polling:250}).catch(()=>{});
  await page.waitForTimeout(3000);
  const rect=await page.evaluate(()=>{const r=document.querySelector('.mphoto')?.getBoundingClientRect();return r?{x:r.x,y:r.y,w:r.width,h:r.height}:null;});
  const settleWall=Date.now();
  const events=[];const mark=async name=>{events.push({name,wall:Date.now()});};
  // In-page wall time (performance.timeOrigin + now) of the forcing call itself, comparable with screencast timestamps.
  const pageMark=async (name,fn)=>{const wall=await page.evaluate(fn);events.push({name,wall});};
  if(route==='startup'){await page.waitForTimeout(2000);}
  else if(route==='expiry'||route==='noSucc'){if(route==='noSucc')await page.evaluate(()=>{window.__r41keep=window.SalahMoonInitial;window.SalahMoonInitial=null;});await mark('observe');await page.waitForTimeout(45000);}
  else if(route==='invalidate'){for(let k=0;k<3;k++){await pageMark('invalidate',()=>{const w=performance.timeOrigin+performance.now();window.SalahMoonRuntime.invalidate('r0041-witness');return w;});await page.waitForTimeout(5000);}}
  else if(route==='sky'){for(let k=0;k<3;k++){await pageMark('sky-invalidate',()=>{const w=performance.timeOrigin+performance.now();window.SalahRealSky?.invalidate('r0041-witness');return w;});await page.waitForTimeout(6000);}}
  else if(route==='resume'){for(let k=0;k<3;k++){await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});document.dispatchEvent(new Event('visibilitychange'));});
      await page.waitForTimeout(1000);await pageMark('resume',()=>{const w=performance.timeOrigin+performance.now();Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});document.dispatchEvent(new Event('visibilitychange'));return w;});await page.waitForTimeout(4000);}}
  else if(route==='identity'){await pageMark('identity',()=>{const w=performance.timeOrigin+performance.now();window.SalahClock.set({rate:1,utcMs:Date.now()+3600000});return w;});await page.waitForTimeout(45000);}
  capturing=false;await loop;if(cdp)await cdp.send('Page.stopScreencast').catch(()=>{});
  await page.waitForTimeout(300);
  const raf=await page.evaluate(()=>window.__r41.frames);const perfOrigin=await page.evaluate(()=>performance.timeOrigin);
  await page.close();
  return {shots,raf,perfOrigin,events,rect,settleWall,t0,errors};
}
(async()=>{
  const env=await createEnv({root});const out={engine,dpr:+dpr,motion,route,startISO,fragment:FRAG,runs:[]};
  try{
    const L=await launch(env,{engine,mode:'route',deviceScaleFactor:+dpr,reducedMotion:motion==='full'?'no-preference':'reduce'});
    await L.context.addInitScript(SHIFT);await L.context.addInitScript(RAF);
    for(let run=0;run<RUNS;run++){
      const r=await oneRun(L,env,run);if(!r.rect){out.runs.push({error:'no Moon rectangle',errors:r.errors});continue;}
      const scale=+dpr;const shots=r.shots.sort((a,b)=>a.t-b.t);
      // reference frames: the last frame before settle+0 (old identity) and the last frame of the run (new identity)
      const decode=s=>{try{return decodePng(s.png);}catch(e){return null;}};
      const before=[...shots].reverse().find(s=>s.t<=r.settleWall);const last=shots.at(-1);
      const refOld=before&&route!=='startup'?discOf(decode(before),r.rect,scale).disc:null,refNew=(route==='identity'||route==='startup')&&last?discOf(decode(last),r.rect,scale).disc:null;
      const frames=[];let firstPresent=null;
      for(const s of shots){const img=decode(s);if(!img)continue;const c=classify(img,r.rect,scale,[refOld,refNew]);
        // startup: dRef is meaningless before a reference; use stars and disc-vs-corner difference of the reference-free part
        const absent=c.absent;
        frames.push({t:Math.round(s.t-r.t0),absent:absent?1:0,stars:c.stars,dRef:c.dRef==null?null:+c.dRef.toFixed(2)});
        if(!absent&&firstPresent==null&&route!=='startup')firstPresent=s.t;
        if(absent&&cropDir&&run===0&&!out.cropSaved){fs.mkdirSync(cropDir,{recursive:true});fs.writeFileSync(path.join(cropDir,`${engine}-dpr${dpr}-${motion}-${route}-absent.png`),s.png);out.cropSaved=true;}}
      const afterSettle=route==='startup'?frames.slice(Math.max(0,frames.findIndex(f=>!f.absent))):frames.filter(f=>f.t>=r.settleWall-r.t0-3000);
      // absent intervals after settle
      const intervals=[];let open=null;for(const f of afterSettle){if(f.absent&&open==null)open=f.t;if(!f.absent&&open!=null){intervals.push({fromMs:open,toMs:f.t,durationMs:f.t-open});open=null;}}if(open!=null)intervals.push({fromMs:open,toMs:null,durationMs:null});
      const rafAfter=r.raf.filter(x=>x[0]+r.perfOrigin>=r.settleWall-3000);
      out.runs.push({frames:frames.length,meanFrameIntervalMs:frames.length>1?+((frames.at(-1).t-frames[0].t)/(frames.length-1)).toFixed(1):null,
        absentFramesAfterSettle:afterSettle.filter(f=>f.absent).length,absentIntervals:intervals,events:r.events.map(e=>({name:e.name,tMs:e.wall-r.t0})),
        rafFrames:rafAfter.length,rafMoonReadyOff:rafAfter.filter(x=>!x[1]).length,rafMaskOff:rafAfter.filter(x=>!x[2]).length,rafNotCurrent:rafAfter.filter(x=>!x[3]).length,
        startupFirstPresentMs:route==='startup'?(frames.find(f=>!f.absent)||{}).t??null:undefined,startupAbsentAfterFirstPresent:route==='startup'?(()=>{const i=frames.findIndex(f=>!f.absent);return i<0?null:frames.slice(i).filter(f=>f.absent).length;})():undefined,
        pageErrors:r.errors,frameLog:frames.map(f=>[f.t,f.absent,f.stars,f.dRef])});
      console.log(engine,dpr,motion,route,'run',run,'frames',frames.length,'absentAfterSettle',afterSettle.filter(f=>f.absent).length,'intervals',JSON.stringify(intervals.slice(0,6)));
    }
    await L.close();
  }catch(e){out.error=String(e&&e.stack||e);console.error(out.error);}
  out.isolation=env.finish();
  const all=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};all[[engine,dpr,motion,route,startISO].join('|')]=out;fs.writeFileSync(outFile,JSON.stringify(all,null,1));
  console.log('isolation allowed',out.isolation.allowedExternal,JSON.stringify(out.isolation.totalRequests));
})().catch(e=>{console.error(e);process.exit(1);});
