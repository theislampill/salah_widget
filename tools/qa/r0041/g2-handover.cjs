'use strict';
// R0041 (issue 143) G2/G5 hand-over recorder. Native recipe; NOT part of the node glob; no product instrumentation.
// Usage: node g2-handover.cjs <servedRoot> <isoDir> <outDir> <side> <scene> <startISO> <dpr> <cell> [tmpDir]
//   cell: fault  healthy boot -> refined settled -> receiver removed + one invalidation -> refined again
//         boot   the embedded start-up receiver does not decode (fault present from boot) -> refined
//         vis    healthy boot -> refined settled -> real tab hidden -> visible, three times (per-frame --moonbeam)
// Isolation: every launch goes through the R0041 isolation launcher (loopback servers, loopback-only proxy, a
// context route '**/*' installed before navigation that aborts every non-loopback request; prayer times and weather
// come from synthetic fixtures). finish() throws if any non-loopback request was allowed.
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const [root,isoDir,outDir,side,scene,startISO,dprArg,cell,tmpArg]=process.argv.slice(2);
const {createEnv,launch}=require(path.join(isoDir,'iso.cjs'));const {decodePng}=require(path.join(isoDir,'png.cjs'));
// The isolation proxy answers a refused CONNECT with 403 and ends the socket but attaches no 'error' listener; when
// Chromium then resets that already-refused tunnel, Node raises an unhandled ECONNRESET and the run dies. Count and
// swallow exactly that error (read ECONNRESET); anything else still crashes the run.
let connResets=0;process.on('uncaughtException',e=>{if(e&&e.code==='ECONNRESET'&&e.syscall==='read'){connResets++;return;}console.error(e);process.exit(1);});
const DPR=+dprArg,W=325,H=530,LABEL=`${scene}-${cell}-dpr${DPR}-${side}`;
const tmp=path.join(tmpArg||path.join(outDir,'.tmp'),LABEL);fs.rmSync(tmp,{recursive:true,force:true});fs.mkdirSync(tmp,{recursive:true});fs.mkdirSync(outDir,{recursive:true});
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const DECODE_FAULT=`(()=>{const a=window.atob;window.atob=function(s){if(typeof s==='string'&&s.startsWith('U01IMR'))throw new Error('g2: injected receiver decode failure');return a.call(this,s);};})();`;
const SOURCES=['awaiting-terrain','initial-v5','terrain-preview','refined-terrain','phase-disc'];
// In-page instrument: one row per animation frame; a 1 px block recoloured every frame (so the compositor screencast
// delivers every frame) and a 2 px event marker (red before, green after each marked event; it toggles).
const INSTR=`(()=>{if(window.__g2)return;const S=${JSON.stringify(SOURCES)};const G=window.__g2={rows:[],truth:[],ev:[],mark:0};let mk=null,m2=null,n=0;
 const ensure=()=>{if(!document.documentElement)return false;if(!mk){mk=document.createElement('div');mk.style.cssText='position:fixed;right:0;bottom:0;width:1px;height:1px;z-index:2147483647;pointer-events:none';document.documentElement.appendChild(mk);
   m2=document.createElement('div');m2.style.cssText='position:fixed;right:2px;bottom:0;width:2px;height:2px;z-index:2147483647;pointer-events:none;background:rgb(255,0,0)';document.documentElement.appendChild(m2);}return true;};
 G.flip=()=>{G.mark^=1;if(ensure())m2.style.background=G.mark?'rgb(0,255,0)':'rgb(255,0,0)';return performance.timeOrigin+performance.now();};
 const row=()=>{let o=null;try{o=window.SalahMoonRuntime&&window.SalahMoonRuntime.observe?window.SalahMoonRuntime.observe():null;}catch(e){}
  const c=document.querySelector('.c'),m=document.querySelector('.moon-mask-disc'),has=k=>c&&c.classList.contains(k)?1:0,mb=c?parseFloat(c.style.getPropertyValue('--moonbeam')):NaN;
  return [+performance.now().toFixed(1),S.indexOf(o&&o.state?o.state.visibleSource:null),o&&o.current?1:0,has('moon-ready'),m&&m.classList.contains('mask-on')?1:0,Number.isFinite(mb)?mb:-1,document.hidden?1:0,has('sky-pending'),has('paused'),G.mark];};
 G.row=row;
 const tick=()=>{G.rows.push(row());if(ensure())mk.style.background=(n++&1)?'rgb(1,1,1)':'rgb(2,2,2)';requestAnimationFrame(tick);};requestAnimationFrame(tick);
 const truth=()=>{try{const t=window.qaState&&window.qaState().moonTruth;if(t)G.truth.push({t:+performance.now().toFixed(1),moonlightOpacity:t.moonlightOpacity,displayMode:t.displayMode,slotState:t.slotState===undefined?'(field absent)':t.slotState,degraded:t.degraded===undefined?'(field absent)':t.degraded,limitation:t.limitation===undefined?'(field absent)':t.limitation,surface:t.surface&&t.surface.status,visibleSource:t.surface&&t.surface.visibleSource,beam:t.lunarLight&&t.lunarLight.beam,eligible:t.lunarLight&&t.lunarLight.eligible,reason:t.lunarLight&&t.lunarLight.reason});}catch(e){}};
 setInterval(truth,200);G.truthNow=truth;
 const first=e=>{if(e.type==='visibilitychange'){G.flip();G.ev.push({n:'visibilitychange',phase:'first',hidden:document.hidden,trusted:e.isTrusted,row:row()});
   const t0=performance.now();if(!document.hidden)requestAnimationFrame(()=>G.ev.push({n:'visibilitychange',phase:'raf-begin',dt:+(performance.now()-t0).toFixed(1),row:row()}));}};
 document.addEventListener('visibilitychange',first,true);
 window.addEventListener('visibilitychange',e=>G.ev.push({n:'visibilitychange',phase:'dispatch-end',hidden:document.hidden,row:row()}));
})();`;
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
function measure(img,rect){
  const s=img.width/W,Wd=img.width,Hd=img.height,d=img.data;
  const x0=Math.floor(rect.x*s),y0=Math.floor(rect.y*s),S=Math.floor(Math.min(rect.w,rect.h)*s),cx=x0+S/2,cy=y0+S/2,disc=[];let ring=0,rn=0,sky=0,sn=0,stars=0;
  const at=(x,y)=>x<0||y<0||x>=Wd||y>=Hd?null:Y(d,4*(y*Wd+x));
  for(let y=Math.max(0,Math.floor(cy-1.25*S));y<Math.min(Hd,cy+1.25*S);y++)for(let x=Math.max(0,Math.floor(cx-1.25*S));x<Math.min(Wd,cx+1.25*S);x++){
    const r=Math.hypot(x+.5-cx,y+.5-cy),v=at(x,y);
    if(r<=.47*S){disc.push(v);if(r<=.47*S-3*s){let m=0,k=0;for(const [dx,dy] of [[2,0],[-2,0],[0,2],[0,-2]]){const u=at(x+Math.round(dx*s),y+Math.round(dy*s));if(u!=null){m+=u;k++;}}if(k&&v-m/k>30)stars++;}}
    else if(r>=.56*S&&r<=1.2*S){ring+=v;rn++;}}
  // sky patch (CSS x 20-200, y 60-200): clear of the header buckle; the Moon ring is measured separately.
  for(let y=Math.floor(60*s);y<Math.floor(200*s);y++)for(let x=Math.floor(20*s);x<Math.floor(200*s);x++){sky+=at(x,y);sn++;}
  let card=0;for(let i=0;i<d.length;i+=4)card+=Y(d,i);
  const mi=4*(Math.min(Hd-1,Math.floor(529*s))*Wd+Math.min(Wd-1,Math.floor(322*s))),mk=d[mi]>200&&d[mi+1]<80?0:d[mi+1]>200&&d[mi]<80?1:null;
  let dm=0;for(const v of disc)dm+=v;
  return {disc:Float32Array.from(disc),discMean:dm/Math.max(1,disc.length),ring:rn?ring/rn:null,sky:sn?sky/sn:null,card:card/(d.length/4),stars,mk};
}
const dist=(a,b)=>{if(!a||!b||a.length!==b.length)return null;let s=0;for(let i=0;i<a.length;i++)s+=Math.abs(a[i]-b[i]);return s/a.length;};
const stepOf=(a,b)=>{if(!a||!b)return null;let sa=0,o16=0;for(let i=0;i<a.disc.length;i++){const q=Math.abs(b.disc[i]-a.disc[i]);sa+=q;if(q>16)o16++;}
  return {discMeanDelta:+(b.discMean-a.discMean).toFixed(2),discMeanAbsDelta:+(sa/a.disc.length).toFixed(2),discShareOver16pct:+(100*o16/a.disc.length).toFixed(1),ringMeanDelta:+(b.ring-a.ring).toFixed(2),skyPatchMeanDelta:+(b.sky-a.sky).toFixed(2),cardMeanDelta:+(b.card-a.card).toFixed(3)};};
const r2=v=>v==null?null:+v.toFixed(2);

(async()=>{
  const out={schema:'r0041-g2/1',label:LABEL,side,scene,cell,dpr:DPR,startISO,engine:'chromium',headed:true,motion:'default (no reduced-motion preference)',deviceScale:DPR>1?'Chromium launched with --force-device-scale-factor='+DPR+' and a context deviceScaleFactor of '+DPR+' (compositor frames arrive at device pixels)':'1',notes:[],void:[]};
  const env=await createEnv({root,extra:{'/away.html':()=>({body:'<!doctype html><meta charset="utf-8"><title>away</title><body style="margin:0;background:#20262e;color:#9aa;font:14px sans-serif"><p style="padding:16px">another tab</p>'})}});
  const L=await launch(env,{engine:'chromium',mode:'route',headless:false,reducedMotion:'no-preference',deviceScaleFactor:DPR,viewport:{width:W,height:H},extraArgs:DPR>1?['--force-device-scale-factor='+DPR]:[]});
  const meta=[];let seq=0,cdp=null,page=null;
  try{
    out.browserVersion=L.browser?L.browser.version():null;
    await L.context.addInitScript(SHIFT);await L.context.addInitScript(INSTR);if(cell==='boot')await L.context.addInitScript(DECODE_FAULT);
    let other=null;if(cell==='vis'){other=await L.context.newPage();await other.goto(env.origins.url('127.0.0.1','/away.html'));}
    page=await L.context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,200)));out.pageErrors=errors;
    if(cell==='vis'){try{const impl=page._connection.toImpl(page);await impl.delegate._mainFrameSession._client.send('Emulation.setFocusEmulationEnabled',{enabled:false});}catch(e){out.void.push('focus emulation could not be switched off: '+String(e.message||e).slice(0,80));}}
    cdp=await L.context.newCDPSession(page);
    cdp.on('Page.screencastFrame',async f=>{const i=seq++;const file=path.join(tmp,String(i).padStart(6,'0')+'.png');fs.writeFileSync(file,Buffer.from(f.data,'base64'));meta.push({i,ts:f.metadata.timestamp*1000,file});try{await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId});}catch(e){}});
    const tNav=Date.now();
    await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'commit',timeout:120000});
    await cdp.send('Page.startScreencast',{format:'png',everyNthFrame:1,maxWidth:W*DPR,maxHeight:H*DPR});
    await page.waitForFunction(()=>{const g=document.querySelector('.moon'),r=document.querySelector('.mphoto')?.getBoundingClientRect();return g&&g.getAttribute('transform')!=='translate(250 64) scale(0.62)'&&r&&r.width>0;},null,{timeout:60000,polling:50});
    out.rect=await page.evaluate(()=>{const r=document.querySelector('.mphoto').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});
    out.perfOrigin=await page.evaluate(()=>performance.timeOrigin);
    const wall=()=>page.evaluate(()=>performance.timeOrigin+performance.now());
    const refined=async(ms)=>page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain'&&window.SalahMoonRuntime.observe().current,null,{timeout:ms,polling:100}).then(()=>true).catch(()=>false);
    const ev={};
    if(!(await refined(300000)))out.void.push('the refined Moon did not arrive after boot');
    ev.refinedFirst=await wall();await page.waitForTimeout(4000);
    if(cell==='fault'){
      ev.fault=await page.evaluate(()=>{const w=window.__g2.flip();window.__g2Keep=window.SalahMoonInitial;window.SalahMoonInitial=null;window.SalahMoonRuntime.invalidate('g2 fault: receiver missing');window.__g2.truthNow();return w;});
      out.stateAfterFault=await page.evaluate(()=>{const o=window.SalahMoonRuntime.observe();return {current:o.current,visibleSource:o.state.visibleSource,slot:o.state.slot??'(field absent)',phaseDisc:o.state.phaseDisc??'(field absent)'};});
      await page.waitForTimeout(300);
      if(!(await refined(300000)))out.void.push('the refined Moon did not arrive after the fault');
      ev.refinedAgain=await wall();await page.waitForTimeout(4000);
    }else if(cell==='vis'){
      out.hiddenChecks=[];
      for(let k=0;k<3;k++){await other.bringToFront();await other.waitForTimeout(1500);out.hiddenChecks.push(await page.evaluate(()=>document.visibilityState));await page.bringToFront();await page.waitForTimeout(5000);}
    }
    ev.end=await wall();
    // Absent reference: the Moon layers hidden by an injected style (after the recorded interval).
    await page.addStyleTag({content:'.moon-detail-canvas,.sky .moon{visibility:hidden!important}'});await page.waitForTimeout(700);ev.absentFrom=await wall();await page.waitForTimeout(500);ev.absentTo=await wall();
    await cdp.send('Page.stopScreencast').catch(()=>{});await page.waitForTimeout(200);
    const g=await page.evaluate(()=>({rows:window.__g2.rows,truth:window.__g2.truth,ev:window.__g2.ev}));
    out.events=ev;out.rows=g.rows;out.truth=g.truth;out.pageEvents=g.ev;out.navToEndMs=Date.now()-tNav;
  }catch(e){out.error=String(e.stack||e).slice(0,900);out.void.push('harness error');}
  await L.close().catch(()=>{});
  const iso=env.finish();out.isolation={allowedExternal:iso.allowedExternal,externalAttempts:iso.externalAttempts,byLayerHostOutcome:iso.externalByLayerHostOutcome,totals:iso.totalRequests};
  if(iso.allowedExternal!==0)out.void.push('isolation: a non-loopback request was allowed');
  out.isolation.refusedTunnelResetsSwallowed=connResets;

  // ---------------- analysis (pixels) ----------------
  try{
    meta.sort((a,b)=>a.ts-b.ts);const ev=out.events,O=out.perfOrigin,rows=out.rows.map(r=>({w:O+r[0],src:SOURCES[r[1]]??null,cur:r[2],ready:r[3],mask:r[4],beam:r[5],hidden:r[6],skyPending:r[7],paused:r[8],mark:r[9]}));
    const first=meta[0];const dims=decodePng(fs.readFileSync(first.file));out.frameSize={width:dims.width,height:dims.height};
    if(dims.width!==W*DPR||dims.height!==H*DPR)out.notes.push(`screencast frames are ${dims.width}x${dims.height}, not ${W*DPR}x${H*DPR}`);
    const F=[];for(const m of meta){let img;try{img=decodePng(fs.readFileSync(m.file));}catch(e){continue;}if(img.width!==dims.width||img.height!==dims.height)continue;F.push({...m,m:measure(img,out.rect)});}
    for(let i=0;i<F.length;i++)F[i].dur=i+1<F.length?F[i+1].ts-F[i].ts:0;
    const rowAt=w=>{let lo=0,hi=rows.length-1;while(lo<hi){const mid=(lo+hi+1)>>1;if(rows[mid].w<=w)lo=mid;else hi=mid-1;}return rows[lo];};
    const lastBefore=w=>{let f=null;for(const x of F){if(x.ts<w)f=x;else break;}return f;},firstAt=w=>F.find(x=>x.ts>=w)??null,near=w=>F.reduce((p,x)=>!p||Math.abs(x.ts-w)<Math.abs(p.ts-w)?x:p,null);
    const absent=near((ev.absentFrom+ev.absentTo)/2),recEnd=ev.end;
    const stills=[],keep=(key,label,f,t0)=>{if(!f)return;const name=`${LABEL}-${String(stills.length+1).padStart(2,'0')}-${key}.png`;fs.copyFileSync(f.file,path.join(outDir,name));const r=rowAt(f.ts);
      stills.push({key,label,file:name,msFromRef:r2(f.ts-t0),videoMs:r2(f.ts-F[0].ts),discMean:r2(f.m.discMean),ringMean:r2(f.m.ring),skyPatchMean:r2(f.m.sky),cardMean:+f.m.card.toFixed(3),starLikeInDisc:f.m.stars,pageState:{visibleSource:r.src,current:r.cur,moonReady:r.ready,moonbeam:r.beam}});};
    const classify=(f,refs)=>{let best=null,bd=1e9;const ds={};for(const [k,v] of Object.entries(refs)){if(!v)continue;const d=dist(f.m.disc,v.m.disc);ds[k]=r2(d);if(d<bd){bd=d;best=k;}}return {cls:best,ds};};
    const truthAt=w=>{const t=out.truth.map(x=>({...x,w:O+x.t}));return t.reduce((p,x)=>!p||Math.abs(x.w-w)<Math.abs(p.w-w)?x:p,null);};
    const pick=t=>t?{moonlightOpacity:t.moonlightOpacity,beam:t.beam,displayMode:t.displayMode,slotState:t.slotState,degraded:t.degraded,surface:t.surface,lightReason:t.reason}:null;
    const R={};
    if(cell==='fault'){
      const tf=ev.fault,before=lastBefore(tf),after=F.find(x=>x.ts>=tf-50&&x.m.mk===1)??firstAt(tf);
      const refRefined=before;
      // textured = a V5 terrain surface (worker preview or refined result) is the current source in the page state
      const texturedRow=rows.find(r=>r.w>tf&&r.cur&&(r.src==='terrain-preview'||r.src==='refined-terrain')),refinedRow=rows.find(r=>r.w>tf&&r.cur&&r.src==='refined-terrain');
      const steadyGap=near(tf+500),refGap=steadyGap; // what the slot shows 500 ms after the fault
      const refs={refined:refRefined,absent,gap:null};
      const gapIsFallback=rowAt(steadyGap.ts).src==='phase-disc'&&rowAt(steadyGap.ts).cur===1;
      if(gapIsFallback)refs.fallback=refGap;
      const win=F.filter(x=>x.ts>=after.ts&&x.ts<=ev.refinedAgain+1500).map(x=>({f:x,...classify(x,{refined:refs.refined,absent:refs.absent,fallback:refs.fallback})}));
      const sum=c=>{const xs=win.filter(x=>x.cls===c);return {frames:xs.length,ms:r2(xs.reduce((p,x)=>p+x.f.dur,0))};};
      const firstTex=win.find(x=>x.cls==='refined'),lastGap=firstTex?win.filter(x=>x.f.ts<firstTex.f.ts).at(-1):win.at(-1);
      const steadyRef=near(ev.refinedAgain+2500);
      keep('before-fault','last frame before the fault',before,tf);keep('after-fault','first frame after the fault',after,tf);keep('gap-steady','500 ms after the fault ('+(gapIsFallback?'fallback steady':'slot state on this side')+')',steadyGap,tf);
      keep('last-gap','last frame before the terrain disc returns',lastGap?.f,tf);keep('first-terrain','first frame with the terrain disc back',firstTex?.f,tf);keep('refined-steady','refined steady (2.5 s after the refined result)',steadyRef,tf);
      R.faultAtVideoMs=r2(tf-F[0].ts);R.gapSource=rowAt(steadyGap.ts).src;R.gapIsFallback=gapIsFallback;
      R.framesAfterFault=win.length;R.emptySlot=sum('absent');R.fallbackPresented=sum('fallback');R.terrainPresented=sum('refined');
      R.firstTerrainFrameMsAfterFault=firstTex?r2(firstTex.f.ts-tf):null;R.pageTerrainPreviewMsAfterFault=texturedRow?r2(texturedRow.w-tf):null;R.pageRefinedResultMsAfterFault=refinedRow?r2(refinedRow.w-tf):null;
      R.stepAtFault=stepOf(before.m,after.m);R.stepAtTerrainReturn=firstTex&&lastGap?stepOf(lastGap.f.m,firstTex.f.m):null;R.stepGapSteadyVsRefinedBefore=stepOf(before.m,steadyGap.m);R.stepRefinedBeforeVsRefinedAfter=stepOf(before.m,steadyRef.m);
      R.distances={gapToRefined:r2(dist(steadyGap.m.disc,before.m.disc)),gapToAbsent:r2(dist(steadyGap.m.disc,absent.m.disc)),refinedToAbsent:r2(dist(before.m.disc,absent.m.disc))};
      R.starLikeInDisc={beforeFault:before.m.stars,gapSteady:steadyGap.m.stars,maxDuringGap:Math.max(0,...win.filter(x=>x.cls!=='refined').map(x=>x.f.m.stars)),absentReference:absent.m.stars};
      const beams=rows.filter(r=>r.w>=tf-1000&&r.w<=ev.refinedAgain+1500);
      R.moonbeam={before:rowAt(tf-100).beam,minAfterFault:Math.min(...beams.filter(r=>r.w>=tf).map(r=>r.beam)),maxAfterFault:Math.max(...beams.filter(r=>r.w>=tf).map(r=>r.beam)),framesAtZero:beams.filter(r=>r.w>=tf&&r.beam===0).length,msAtZero:r2((()=>{let s=0;const b=beams.filter(r=>r.w>=tf);for(let i=0;i+1<b.length;i++)if(b[i].beam===0)s+=b[i+1].w-b[i].w;return s;})()),end:rowAt(ev.refinedAgain+2500).beam};
      R.moonTruth={before:pick(truthAt(tf-300)),atFault:pick(out.truth.map(x=>({...x,w:O+x.t})).find(x=>x.w>=tf-1)),during:pick(truthAt(tf+500)),after:pick(truthAt(ev.refinedAgain+2500))};
      R.sequence=win.map(x=>[r2(x.f.ts-tf),x.cls,r2(x.f.m.discMean)]);
    }else if(cell==='boot'){
      const skyRow=rows.find(r=>r.skyPending===0&&r.w>F[0].ts),t0=skyRow?skyRow.w:F[0].ts;
      const texturedRow=rows.find(r=>r.w>=t0&&r.cur&&(r.src==='terrain-preview'||r.src==='refined-terrain')),refinedRow=rows.find(r=>r.w>=t0&&r.cur&&r.src==='refined-terrain');
      const steadyRef=near(ev.refinedFirst+2500),fbRow=rows.find(r=>r.w>=t0&&r.cur&&r.src==='phase-disc'),fbFrame=fbRow?near(Math.min(fbRow.w+500,(texturedRow?texturedRow.w:fbRow.w+800)-60)):null;
      const refs={refined:steadyRef,absent,fallback:fbFrame&&rowAt(fbFrame.ts).src==='phase-disc'?fbFrame:null};
      const win=F.filter(x=>x.ts>=t0&&x.ts<=ev.refinedFirst+1500).map(x=>({f:x,...classify(x,refs)}));
      const sum=c=>{const xs=win.filter(x=>x.cls===c);return {frames:xs.length,ms:r2(xs.reduce((p,x)=>p+x.f.dur,0))};};
      const firstTex=win.find(x=>x.cls==='refined'),lastGap=firstTex?win.filter(x=>x.f.ts<firstTex.f.ts).at(-1):win.at(-1);
      keep('pending','last frame before the sky is shown',lastBefore(t0),t0);keep('first-sky','first frame with the sky shown',win[0]?.f,t0);keep('gap-steady','500 ms after the sky is shown',near(t0+500),t0);
      keep('last-gap','last frame before the terrain disc arrives',lastGap?.f,t0);keep('first-terrain','first frame with the terrain disc',firstTex?.f,t0);keep('refined-steady','refined steady (2.5 s after the refined result)',steadyRef,t0);
      R.skyShownAtVideoMs=r2(t0-F[0].ts);R.gapSource=rowAt(t0+500).src;R.framesFromSky=win.length;R.emptySlot=sum('absent');R.fallbackPresented=sum('fallback');R.terrainPresented=sum('refined');
      R.firstTerrainFrameMsAfterSky=firstTex?r2(firstTex.f.ts-t0):null;R.pageTerrainPreviewMsAfterSky=texturedRow?r2(texturedRow.w-t0):null;R.pageRefinedResultMsAfterSky=refinedRow?r2(refinedRow.w-t0):null;
      R.stepAtTerrainArrival=firstTex&&lastGap?stepOf(lastGap.f.m,firstTex.f.m):null;
      R.starLikeInDisc={gapSteady:near(t0+500).m.stars,maxDuringGap:Math.max(0,...win.filter(x=>x.cls!=='refined').map(x=>x.f.m.stars)),absentReference:absent.m.stars};
      const b=rows.filter(r=>r.w>=t0&&r.w<=ev.refinedFirst+1500);R.moonbeam={min:Math.min(...b.map(r=>r.beam)),max:Math.max(...b.map(r=>r.beam)),atSky:rowAt(t0+20).beam,end:rowAt(ev.refinedFirst+2500).beam};
      R.moonTruth={during:pick(truthAt(t0+500)),after:pick(truthAt(ev.refinedFirst+2500))};
      R.sequence=win.map(x=>[r2(x.f.ts-t0),x.cls,r2(x.f.m.discMean)]);
    }else if(cell==='vis'){
      const shows=out.pageEvents.filter(e=>e.n==='visibilitychange'&&e.phase==='first'&&e.hidden===false),hides=out.pageEvents.filter(e=>e.n==='visibilitychange'&&e.phase==='first'&&e.hidden===true);
      R.lifecycle={hides:hides.length,shows:shows.length,trusted:out.pageEvents.filter(e=>e.phase==='first').every(e=>e.trusted===true),hiddenChecks:out.hiddenChecks};
      if(hides.length<3||shows.length<3||!R.lifecycle.trusted)out.void.push('the tab was not really hidden and shown three times');
      R.restorations=[];
      shows.forEach((s,k)=>{const ts=O+s.row[0],th=O+hides[k].row[0],steadyRow=rowAt(th-200),steady=steadyRow.beam,steadyF=lastBefore(th);
        const after=rows.filter(r=>r.w>=ts&&r.w<=ts+4500),zero=after.filter(r=>r.beam<steady*0.5),lastLow=zero.at(-1),rec=after.find(r=>(!lastLow||r.w>lastLow.w)&&Math.abs(r.beam-steady)<=0.002*Math.max(1,steady)+0.0015);
        const end=O+out.pageEvents.filter(e=>e.n==='visibilitychange'&&e.phase==='dispatch-end'&&e.hidden===false)[k]?.row[0];
        const tRec=rec?rec.w:null,fr=F.filter(x=>x.ts>=ts-1&&x.ts<=ts+4500&&x.m.mk===(hides[k].row[9]^1)),low=tRec?fr.filter(x=>x.ts<tRec):[],firstRec=tRec?fr.find(x=>x.ts>=tRec):null,late=near(ts+3500);
        const d=(f)=>f?{ms:r2(f.ts-ts),discMean:r2(f.m.discMean),ringMean:r2(f.m.ring),skyPatchMean:r2(f.m.sky),cardMean:+f.m.card.toFixed(3),ringDeltaVsBeforeHide:r2(f.m.ring-steadyF.m.ring),skyPatchDeltaVsBeforeHide:r2(f.m.sky-steadyF.m.sky),cardDeltaVsBeforeHide:+(f.m.card-steadyF.m.card).toFixed(3),discToBeforeHide:r2(dist(f.m.disc,steadyF.m.disc)),discToAbsent:r2(dist(f.m.disc,absent.m.disc)),moonbeam:rowAt(f.ts).beam}:null;
        keep(`r${k+1}-before-hide`,`restoration ${k+1}: last frame before the tab was hidden`,steadyF,ts);keep(`r${k+1}-first`,`restoration ${k+1}: first frame after the tab returned`,fr[0],ts);
        if(low.length>1)keep(`r${k+1}-low-last`,`restoration ${k+1}: last frame recorded while --moonbeam was below its value`,low.at(-1),ts);
        keep(`r${k+1}-recovered`,`restoration ${k+1}: first frame after --moonbeam recovered`,firstRec,ts);keep(`r${k+1}-steady`,`restoration ${k+1}: 3.5 s after the return`,late,ts);
        R.restorations.push({k:k+1,moonbeamBeforeHide:steady,moonbeamAtFirstListener:s.row[5],moonbeamAtDispatchEnd:out.pageEvents.filter(e=>e.n==='visibilitychange'&&e.phase==='dispatch-end'&&e.hidden===false)[k]?.row[5],restoringDispatchMs:end?r2(end-ts):null,
          moonAdoptedAtDispatchEnd:out.pageEvents.filter(e=>e.n==='visibilitychange'&&e.phase==='dispatch-end'&&e.hidden===false)[k]?.row[2]===1,
          rafRowsBelowHalf:zero.length,msUntilMoonbeamRecovered:tRec?r2(tRec-ts):null,trace:after.filter((r,i)=>i<40||r.w<=(tRec??ts)+60).slice(0,60).map(r=>[r2(r.w-ts),r.beam,r.src,r.cur]),
          lowRows:zero.map(r=>[r2(r.w-ts),r.beam,r.src,r.cur]),lowMs:r2((()=>{let s=0;for(const z of zero){const nx=after.find(r=>r.w>z.w);s+=(nx?nx.w:z.w)-z.w;}return s;})()),
          framesDuringLow:zero.length?F.filter(x=>x.ts>=zero[0].w&&x.ts<=(tRec??zero.at(-1).w)+34).map(d):[],
          window600:F.filter(x=>x.ts>=ts-1&&x.ts<=ts+600).map(x=>[r2(x.ts-ts),r2(dist(x.m.disc,steadyF.m.disc)),r2(dist(x.m.disc,absent.m.disc)),r2(x.m.ring-steadyF.m.ring),r2(x.m.sky-steadyF.m.sky),rowAt(x.ts).beam]),
          framesRecordedBeforeRecovery:low.length,framesBeforeRecovery:low.map(d),firstRecoveredFrame:d(firstRec),steadyFrame:d(late)});});
      R.moonTruthSteady=pick(truthAt(O+hides[0].row[0]-400));
    }
    out.result=R;out.stills=stills;out.frames={count:F.length,firstTs:F[0].ts,lastTs:F.at(-1).ts,medianIntervalMs:r2(F.map(x=>x.dur).filter(Boolean).sort((a,b)=>a-b)[F.length>>1])};
    // ---------------- real-time video from the lossless frames, at their own timestamps; no scaling ----------------
    const V=F.filter(x=>x.ts<=recEnd);const list=path.join(tmp,'list.txt');
    fs.writeFileSync(list,V.map((x,i)=>`file '${x.file.replace(/\\/g,'/')}'\nduration ${(Math.max(1,(i+1<V.length?V[i+1].ts:recEnd)-x.ts)/1000).toFixed(4)}`).join('\n')+`\nfile '${V.at(-1).file.replace(/\\/g,'/')}'\n`);
    const even=n=>n+(n&1),vf=`pad=${even(dims.width)}:${even(dims.height)}:0:0:black`,video=LABEL+'.mp4';
    const r=spawnSync('ffmpeg',['-v','error','-y','-f','concat','-safe','0','-i',list,'-vf',vf,'-fps_mode','cfr','-r','60','-c:v','libx264','-preset','medium','-crf','10','-pix_fmt','yuv420p','-movflags','+faststart',path.join(outDir,video)],{encoding:'utf8'});
    if(r.status!==0)out.void.push('ffmpeg: '+String(r.stderr).slice(0,300));
    out.video={file:video,width:even(dims.width),height:even(dims.height),padded:even(dims.width)!==dims.width?'1 px black column added on the right (H.264 needs even dimensions); no scaling':'none',fps:60,codec:'H.264, CRF 10, 4:2:0',sourceFrames:V.length,durationMs:r2(recEnd-V[0].ts),bytes:fs.existsSync(path.join(outDir,video))?fs.statSync(path.join(outDir,video)).size:0};
  }catch(e){out.analysisError=String(e.stack||e).slice(0,900);out.void.push('analysis error');}
  const slim={...out};delete slim.rows;slim.rowCount=out.rows?.length;slim.truthSamples=out.truth?.length;delete slim.truth;
  slim.moonbeamTrace=(out.rows||[]).filter((r,i,a)=>i===0||r[5]!==a[i-1][5]||r[1]!==a[i-1][1]||r[2]!==a[i-1][2]||r[6]!==a[i-1][6]).map(r=>[r[0],r[5],SOURCES[r[1]]??null,r[2],r[6]]);
  fs.writeFileSync(path.join(outDir,LABEL+'.json'),JSON.stringify(slim,null,1));
  fs.rmSync(tmp,{recursive:true,force:true});
  console.log(LABEL,out.void.length?'VOID '+JSON.stringify(out.void):'ok','frames',out.frames?.count,'allowedExternal',out.isolation.allowedExternal,'attempts',out.isolation.externalAttempts,JSON.stringify(out.result?{gap:out.result.gapSource,empty:out.result.emptySlot,fb:out.result.fallbackPresented,first:out.result.firstTerrainFrameMsAfterFault??out.result.firstTerrainFrameMsAfterSky}:{}).slice(0,300),out.error||out.analysisError||'');
})().catch(e=>{console.error(e);process.exit(1);});
