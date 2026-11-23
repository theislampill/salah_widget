'use strict';
// R0041 (issue 143), owner decision 2026-11-22 (G6, G8): REAL-WORLD restoration witness. Native recipe; NOT part of the
// node glob. HEADED browser, real-time video recording, real (trusted) lifecycle events; nothing is dispatched
// synthetically. Every launch goes through iso.cjs (loopback only; zero allowed non-loopback requests or the cell is
// void). One browser at a time. Synthetic fixture only (lat 24.47, lon 39.61), simulated clock.
//
// Routes
//   tab      an actual tab switch: a second real tab in the same window is brought to the front (the widget tab becomes
//            hidden: trusted visibilitychange) and the widget tab is brought back. Chromium only: Playwright keeps every
//            page "visible" through its focus emulation, which this recipe switches off on the widget tab (Playwright
//            internals); Playwright's Firefox and WebKit builds expose no such switch, so the route is VOID there.
//   bfcache  an actual back/forward-cache restoration: a real navigation to another loopback document, then
//            history.back(). VALID only when the widget page reports a trusted pageshow with persisted === true for
//            every event; a reload is VOID, never a pass.
//   active   Playwright WebKit only, and NOT a tab switch: the engine's own page-active state is switched off and on
//            (trusted visibilitychange through the engine's visibility machinery). Reported under its own name.
//
// Judgement, per restoration event (pixels, not event order):
//   - VIDEO: every frame of the real-time recording that shows the event's marker (a 12 px block recoloured in the
//     first listener of the restoring event) is classified from the Moon-slot pixels: ABSENT when the disc region is
//     closer to the absent reference (Moon layers hidden by an injected style, recorded at the end) than to the present
//     reference (the settled Moon before the first event).
//   - SHOTS: a serial screenshot burst for 2.5 s after the restoration, classified the same way against screenshot
//     references. Screenshots paint on demand, so they can catch a document state between the event task and the next
//     animation frame that a compositor frame would not show.
//   - STATE (auxiliary): Moon adopted when the visibilitychange dispatch ends (a window-level bubble listener, after
//     every document-level listener), at the next task and when the first animation frame begins; the duration of that
//     dispatch (the synchronous cost of composing in the event task); long tasks where the engine reports them.
// Fail closed: a cell is VOID when the lifecycle events were not real (untrusted, missing, or pageshow not persisted),
// the page was never hidden, the Moon was not presented before the first event, the absent control is not classified
// absent, the references do not differ, a restoration has too few judged frames, or any non-loopback request was allowed.
// Usage: node real-witness.cjs <repoRoot> <outDir> <engine> <route> <startISO> [events=3] [--fault] [--label=name]
//   --fault  the embedded start-up receiver does not decode, so each restoration presents the phase-disc fallback.
// Needs ffmpeg on PATH (frame decoding of the recording) and PLAYWRIGHT_PKG.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),{spawn}=require('node:child_process');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const argv=process.argv.slice(2),FAULT=argv.includes('--fault'),[root,outDir,engine,route,startISO,eventsArg]=argv.filter(a=>!a.startsWith('--'));
const EVENTS=+(eventsArg||3),LABEL=argv.find(a=>a.startsWith('--label='))?.slice(8)??`${engine}-${route}${FAULT?'-fault':''}`;
if(EVENTS<1||EVENTS>3)throw new Error('1-3 events (the marker palette holds seven states)');
const W=325,H=530,VW=326,VH=530,TH_FAR=20;
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const DECODE_FAULT=`(()=>{const a=window.atob;window.atob=function(s){if(typeof s==='string'&&s.startsWith('U01IMR'))throw new Error('r0041 witness: injected receiver decode failure');return a.call(this,s);};})();`;
const PAL=[[255,0,0],[0,255,0],[0,0,255],[255,255,0],[255,0,255],[0,255,255],[255,128,0],[255,255,255]];
// In-page instrument. Marker state c: 0 before the first event, odd while hidden, even (2k) after restoration k;
// the control (Moon layers hidden by a style) shows the eighth colour.
const INSTR=`(()=>{const PAL=${JSON.stringify(PAL)};const R=window.__rw={ev:[],c:0,phase:'visible',frames:[],control:false,burst:0};let mk=null;
 const paint=()=>{if(!mk){if(!document.documentElement)return;mk=document.createElement('div');mk.id='rw-mark';mk.style.cssText='position:fixed;right:0;bottom:0;width:12px;height:12px;z-index:2147483647;pointer-events:none';document.documentElement.appendChild(mk);}mk.style.background='rgb('+PAL[R.control?7:R.c%7]+')';};
 const st=()=>{let o=null;try{o=window.SalahMoonRuntime&&window.SalahMoonRuntime.observe?window.SalahMoonRuntime.observe():null;}catch(e){}const c=document.querySelector('.c'),has=k=>!!(c&&c.classList.contains(k));
  return {t:+performance.now().toFixed(1),hidden:document.hidden,cur:!!(o&&o.current),src:o&&o.state?o.state.visibleSource:null,slot:o&&o.state?o.state.slot:null,paused:has('paused'),ready:has('moon-ready'),preview:has('real-sky-preview-ready'),composed:has('real-sky-composed'),detail:!!(window.SalahMoonDetail&&window.SalahMoonDetail.state&&window.SalahMoonDetail.state.visible)};};
 R.st=st;R.paint=paint;const log=(n,phase,e,x)=>R.ev.push(Object.assign({n,phase,c:R.c,trusted:e?e.isTrusted:undefined,persisted:e?e.persisted:undefined},st(),x||{}));
 const first=n=>e=>{const hiding=n==='pagehide'||(n==='visibilitychange'&&document.hidden),showing=(n==='pageshow'&&e.persisted)||(n==='visibilitychange'&&!document.hidden);let step=false;
  if(hiding&&R.phase==='visible'){R.phase='hidden';R.c++;step=true;paint();}else if(showing&&R.phase==='hidden'){R.phase='visible';R.c++;step=true;paint();R.burst=performance.now()+3000;}
  log(n,'first',e,{step});const t0=performance.now(),mc=new MessageChannel();mc.port1.onmessage=()=>{log(n,'next-task',null,{dt:+(performance.now()-t0).toFixed(1)});mc.port1.close();};mc.port2.postMessage(0);
  if(showing)requestAnimationFrame(()=>log(n,'raf-begin',null,{dt:+(performance.now()-t0).toFixed(1)}));};
 document.addEventListener('visibilitychange',first('visibilitychange'),true);window.addEventListener('pagehide',first('pagehide'),true);window.addEventListener('pageshow',first('pageshow'),true);
 for(const n of ['freeze','resume'])document.addEventListener(n,e=>log(n,'first',e),true);
 window.addEventListener('visibilitychange',e=>log('visibilitychange','dispatch-end',e));
 try{new PerformanceObserver(l=>{for(const e of l.getEntries())R.ev.push({n:'longtask',t:+e.startTime.toFixed(1),dur:+e.duration.toFixed(1)});}).observe({type:'longtask'});}catch(e){}
 const tick=()=>{if(performance.now()<R.burst){const s=st();R.frames.push([s.t,R.c,s.cur?1:0,s.ready?1:0,s.detail?1:0,s.preview?1:0,s.composed?1:0]);}requestAnimationFrame(tick);};requestAnimationFrame(tick);
 addEventListener('DOMContentLoaded',paint);})();`;
const AWAY='<!doctype html><meta charset="utf-8"><title>away</title><body style="margin:0;background:#20262e;color:#9aa;font:14px sans-serif"><p style="padding:16px">R0041 witness: another document</p>';
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
// Disc-region luminance (r <= 0.47 S, as witness.cjs) and the marker colour, from an RGB(A) raster of the page at CSS scale.
function sample(data,width,channels,rect){
  const x0=Math.floor(rect.x),y0=Math.floor(rect.y),S=Math.floor(Math.min(rect.w,rect.h)),cx=x0+S/2,cy=y0+S/2,out=[];
  for(let y=Math.max(0,y0);y<y0+S&&y<H;y++)for(let x=Math.max(0,x0);x<x0+S&&x<W;x++)if(Math.hypot(x+.5-cx,y+.5-cy)<=.47*S)out.push(Y(data,channels*(y*width+x)));   // the in-frame part of the disc
  let r=0,g=0,b=0,n=0;for(let y=H-9;y<H-3;y++)for(let x=W-9;x<W-3;x++){const i=channels*(y*width+x);r+=data[i];g+=data[i+1];b+=data[i+2];n++;}r/=n;g/=n;b/=n;
  let best=-1,bd=1e9;PAL.forEach((p,k)=>{const d=Math.abs(p[0]-r)+Math.abs(p[1]-g)+Math.abs(p[2]-b);if(d<bd){bd=d;best=k;}});
  return {disc:Uint8Array.from(out,v=>Math.round(v)),marker:bd<150?best:-1};
}
const dist=(a,b)=>{let s=0;for(let i=0;i<a.length;i++)s+=Math.abs(a[i]-b[i]);return s/a.length;};
const mean=a=>{let s=0;for(const v of a)s+=v;return s/a.length;};
const classify=(disc,refP,refA)=>{const dP=dist(disc,refP),dA=dist(disc,refA);return {dP:+dP.toFixed(2),dA:+dA.toFixed(2),verdict:Math.min(dP,dA)>TH_FAR?'far':dA<dP?'absent':'present'};};
function decodeVideo(file,rect){return new Promise((resolve,reject)=>{
  const frames=[],size=VW*VH*3;let buf=Buffer.alloc(0),err='';
  const p=spawn('ffmpeg',['-v','error','-i',file,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],{stdio:['ignore','pipe','pipe']});
  p.stdout.on('data',d=>{buf=buf.length?Buffer.concat([buf,d]):d;while(buf.length>=size){frames.push(sample(buf.subarray(0,size),VW,3,rect));buf=buf.subarray(size);}});
  p.stderr.on('data',d=>{err+=d;});p.on('error',reject);p.on('close',code=>code===0?resolve(frames):reject(new Error('ffmpeg '+code+': '+err.slice(0,300))));});}
const sha256=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');

(async()=>{
  fs.mkdirSync(outDir,{recursive:true});const videoDir=path.join(outDir,'.video-'+LABEL);fs.rmSync(videoDir,{recursive:true,force:true});
  const env=await createEnv({root,extra:{'/away.html':()=>({body:AWAY})}});
  const opts={engine,mode:'route',headless:false,reducedMotion:'reduce',recordVideo:{dir:videoDir,size:{width:VW,height:VH}}};
  if(engine==='chromium'&&route==='bfcache')opts.ignoreDefaultArgs=['--disable-back-forward-cache'];
  const out={schema:'r0041-real-witness/1',label:LABEL,engine,route,fault:FAULT,startISO,headed:true,events:EVENTS,void:[],notes:[]};
  const L=await launch(env,opts);let page=null,videoPath=null;
  const shots=[],refs={};
  try{
    await L.context.addInitScript(SHIFT);await L.context.addInitScript(INSTR);if(FAULT)await L.context.addInitScript(DECODE_FAULT);
    let other=null;
    if(route==='tab'){other=await L.context.newPage();await other.goto(env.origins.url('127.0.0.1','/away.html'));}
    page=await L.context.newPage();out.browserVersion=L.browser?L.browser.version():null;
    if(route==='tab'){
      // Playwright's focus emulation keeps a background tab "visible"; it is switched off on the widget tab only, so the
      // browser's own tab activation decides visibility. Not available for Firefox or WebKit.
      try{const impl=page._connection.toImpl(page);await impl.delegate._mainFrameSession._client.send('Emulation.setFocusEmulationEnabled',{enabled:false});}
      catch(e){out.void.push('focus emulation could not be switched off in this engine: a real tab switch cannot hide the page ('+String(e.message||e).slice(0,80)+')');}
    }
    await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'load'});
    await page.waitForFunction(()=>window.__rw&&window.__rw.st().cur&&window.__rw.st().ready,null,{timeout:60000,polling:100});
    await page.waitForTimeout(6000);
    const rect=await page.evaluate(()=>{const r=document.querySelector('.mphoto').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});out.rect=rect;
    out.before=await page.evaluate(()=>window.__rw.st());
    const shoot=async tag=>{const t0=Date.now(),png=await page.screenshot({type:'png'}),img=decodePng(png),s=sample(img.data,img.width,img.data.length/(img.width*img.height),rect);return {tag,t0,t1:Date.now(),png,...s};};
    refs.present=await shoot('ref-present');fs.writeFileSync(path.join(outDir,LABEL+'-ref-present.png'),refs.present.png);
    const burst=async k=>{const end=Date.now()+2500;let n=0;while(Date.now()<end){const s=await shoot('restore-'+k);if(n++===0)fs.writeFileSync(path.join(outDir,`${LABEL}-restore${k}-first-shot.png`),s.png);delete s.png;shots.push({k,...s});}};
    out.hiddenChecks=[];
    for(let k=1;k<=EVENTS;k++){
      if(route==='tab'){
        await other.bringToFront();await other.waitForTimeout(1500);
        out.hiddenChecks.push(await page.evaluate(()=>document.visibilityState));
        await page.bringToFront();await burst(k);
      }else if(route==='bfcache'){
        await page.goto(env.origins.url('127.0.0.1','/away.html'),{waitUntil:'load'});await page.waitForTimeout(1200);
        out.hiddenChecks.push(await page.evaluate(()=>document.title));
        await page.evaluate(()=>{history.back();});
        await page.waitForFunction(()=>!!window.__rw,null,{timeout:15000,polling:20});await burst(k);
      }else if(route==='active'){
        const impl=page._connection.toImpl(page),session=impl.delegate._pageProxySession;
        await session.send('Emulation.setActiveAndFocused',{active:false});await page.waitForTimeout(1500);
        out.hiddenChecks.push(await page.evaluate(()=>document.visibilityState));
        await session.send('Emulation.setActiveAndFocused',{active:true});await burst(k);
      }else throw new Error('unknown route '+route);
      await page.waitForTimeout(2500);
    }
    out.after=await page.evaluate(()=>window.__rw.st());
    // Absent control: the Moon layers hidden by a style, under the control marker.
    await page.evaluate(()=>{window.__rw.control=true;window.__rw.paint();});
    await page.addStyleTag({content:'.moon-detail-canvas,.sky .moon{visibility:hidden!important}'});await page.waitForTimeout(600);
    refs.absent=await shoot('ref-absent');fs.writeFileSync(path.join(outDir,LABEL+'-ref-absent.png'),refs.absent.png);await page.waitForTimeout(900);
    out.log=await page.evaluate(()=>({ev:window.__rw.ev,frames:window.__rw.frames,c:window.__rw.c}));
    out.truth=await page.evaluate(()=>{const t=window.qaState&&window.qaState().moonTruth;return t?{displayMode:t.displayMode,degraded:t.degraded===undefined?'(field absent)':t.degraded,limitation:t.limitation,slotState:t.slotState,surfaceStatus:t.surface&&t.surface.status,moonlightOpacity:t.moonlightOpacity}:null;});
    videoPath=await page.video().path();
  }catch(e){out.error=String(e.stack||e).slice(0,700);out.void.push('harness error');}
  await L.close().catch(()=>{});
  const iso=env.finish();out.isolation={allowedExternal:iso.allowedExternal,externalAttempts:iso.externalAttempts,byLayerHostOutcome:iso.externalByLayerHostOutcome};
  if(iso.allowedExternal!==0)out.void.push('isolation: non-loopback request allowed');
  try{
    // ---- lifecycle validity
    const ev=out.log?.ev??[],steps=ev.filter(e=>e.phase==='first'&&e.step);
    const hides=steps.filter(e=>e.c%2===1),shows=steps.filter(e=>e.c%2===0);
    out.lifecycle={order:ev.filter(e=>e.phase==='first').map(e=>e.n+(e.persisted===undefined?'':'('+e.persisted+')')+(e.trusted?'':'!untrusted')),hides:hides.length,restores:shows.length,
      persisted:ev.filter(e=>e.n==='pageshow'&&e.phase==='first'&&e.c>0).map(e=>e.persisted)};
    if(hides.length!==EVENTS||shows.length!==EVENTS)out.void.push(`expected ${EVENTS} real hide and restore events on the widget page; saw ${hides.length} and ${shows.length}`+(route==='bfcache'?' (the page was not restored from the back/forward cache: it was reloaded)':''));
    if(steps.some(e=>e.trusted!==true))out.void.push('an untrusted lifecycle event');
    if(route==='bfcache'){const ps=ev.filter(e=>e.n==='pageshow'&&e.phase==='first'&&e.c>0);if(ps.length!==EVENTS||ps.some(e=>e.persisted!==true||e.trusted!==true))out.void.push('pageshow.persisted was not true for every restoration');
      if(out.hiddenChecks?.some(t=>t!=='away'))out.void.push('the other document was not shown');}
    else if(out.hiddenChecks?.some(v=>v!=='hidden'))out.void.push('the widget page was not hidden during the switch');
    if(!out.before?.cur||!out.before?.ready)out.void.push('the Moon was not presented before the first event');
    // ---- state at the end of the restoring dispatch, and its synchronous cost
    out.restorations=[];
    for(let k=1;k<=EVENTS;k++){const c=2*k,f=ev.find(e=>e.phase==='first'&&e.step&&e.c===c),at=p=>ev.find(e=>e.c===c&&e.phase===p&&e.t>=(f?.t??1e18));
      const endV=ev.find(e=>e.c===c&&e.n==='visibilitychange'&&e.phase==='dispatch-end'),firstV=ev.find(e=>e.c===c&&e.n==='visibilitychange'&&e.phase==='first'&&e.hidden===false);
      const fr=(out.log?.frames??[]).filter(x=>x[1]===c);
      out.restorations.push({k,event:f?.n??null,persisted:f?.persisted,adoptedAtDispatchEnd:endV?endV.cur:null,sourceAtDispatchEnd:endV?.src??null,moonReadyAtDispatchEnd:endV?endV.ready:null,
        visibilityDispatchMs:endV&&firstV?+(endV.t-firstV.t).toFixed(1):null,adoptedAtNextTask:at('next-task')?.cur??null,adoptedAtFirstFrame:at('raf-begin')?.cur??null,firstFrameAfterMs:at('raf-begin')?.dt??null,
        animationFrames:fr.length,animationFramesWithoutMoon:fr.filter(x=>!x[2]||!x[3]).length,
        longTasks:ev.filter(e=>e.n==='longtask'&&f&&e.t>=f.t-5&&e.t<=f.t+1500).map(e=>e.dur)});}
    // ---- pixels: screenshots
    const judgeShots=k=>{const s=shots.filter(x=>x.k===k).map(x=>({marker:x.marker,...classify(x.disc,refs.present.disc,refs.absent.disc)}));const mine=s.filter(x=>x.marker===(2*k)%7);
      return {shots:s.length,withEventMarker:mine.length,absent:mine.filter(x=>x.verdict==='absent').length,far:mine.filter(x=>x.verdict==='far').length,maxDPresent:mine.length?Math.max(...mine.map(x=>x.dP)):null,otherMarker:s.length-mine.length};};
    const refShot=refs.present&&refs.absent?classify(refs.absent.disc,refs.present.disc,refs.absent.disc):null;
    out.references={screenshot:refs.present&&refs.absent?{presentMeanY:+mean(refs.present.disc).toFixed(1),absentMeanY:+mean(refs.absent.disc).toFixed(1),distance:+dist(refs.present.disc,refs.absent.disc).toFixed(1),discPixels:refs.present.disc.length,presentMarker:refs.present.marker,absentMarker:refs.absent.marker}:null};
    if(!refs.present||!refs.absent||dist(refs.present.disc,refs.absent.disc)<8)out.void.push('screenshot references do not differ (no Moon in the present reference, or the control did not hide it)');
    if(refs.absent&&refs.absent.marker!==7)out.void.push('control marker not seen in the absent screenshot');
    // ---- pixels: the recording
    let video=null;
    if(videoPath&&fs.existsSync(videoPath)){
      const final=path.join(outDir,LABEL+'.webm');fs.copyFileSync(videoPath,final);
      const frames=await decodeVideo(final,out.rect);
      const firstEvent=frames.findIndex(f=>f.marker>0&&f.marker<7),lastZero=(()=>{for(let i=(firstEvent<0?frames.length:firstEvent)-1;i>=0;i--)if(frames[i].marker===0)return i;return -1;})();
      const controls=frames.map((f,i)=>f.marker===7?i:-1).filter(i=>i>=0),vP=lastZero>=0?frames[lastZero].disc:null,vA=controls.length?frames[controls.at(-1)].disc:null;
      video={file:path.basename(final),bytes:fs.statSync(final).size,sha256:sha256(final),frames:frames.length,framesPerSecond:25,durationSeconds:+(frames.length/25).toFixed(1),noMarkerFrames:frames.filter(f=>f.marker<0).length,
        presentReferenceFrame:lastZero,controlFrames:controls.length,perRestoration:[]};
      if(!vP||!vA)out.void.push('the recording holds no settled frame before the first event, or no control frame');
      else{
        video.references={presentMeanY:+mean(vP).toFixed(1),absentMeanY:+mean(vA).toFixed(1),distance:+dist(vP,vA).toFixed(1)};
        if(dist(vP,vA)<8)out.void.push('video references do not differ');
        const ctl=controls.slice(Math.floor(controls.length/2)).map(i=>classify(frames[i].disc,vP,vA).verdict);video.controlFramesAbsent=ctl.filter(v=>v==='absent').length;video.controlFramesJudged=ctl.length;
        if(ctl.some(v=>v!=='absent'))out.void.push('the absent control is not classified absent in the recording');
        for(let k=1;k<=EVENTS;k++){const mine=frames.map((f,i)=>({i,f})).filter(x=>x.f.marker===(2*k)%7).map(x=>({i:x.i,...classify(x.f.disc,vP,vA)}));
          const bad=mine.filter(x=>x.verdict!=='present');
          video.perRestoration.push({k,frames:mine.length,firstFrame:mine[0]?.i??null,absent:mine.filter(x=>x.verdict==='absent').length,far:mine.filter(x=>x.verdict==='far').length,maxDPresent:mine.length?Math.max(...mine.map(x=>x.dP)):null,minDAbsent:mine.length?Math.min(...mine.map(x=>x.dA)):null,notPresentFrames:bad.slice(0,12)});
          if(mine.length<15)out.void.push(`restoration ${k}: only ${mine.length} recorded frames show its marker`);}
        video.hiddenStateFrames=frames.filter(f=>f.marker>0&&f.marker<7&&f.marker%2===1).length;
      }
    }else out.void.push('no recording');
    out.video=video;
    out.perRestoration=out.restorations.map(r=>({...r,screenshots:judgeShots(r.k),video:video?.perRestoration?.find(x=>x.k===r.k)??null}));delete out.restorations;
    for(const r of out.perRestoration)if(r.screenshots.withEventMarker<5)out.void.push(`restoration ${r.k}: only ${r.screenshots.withEventMarker} screenshots show its marker`);
    void refShot;
    const judged={videoFrames:0,videoWithoutMoon:0,shots:0,shotsWithoutMoon:0};
    for(const r of out.perRestoration){judged.videoFrames+=r.video?.frames??0;judged.videoWithoutMoon+=(r.video?.absent??0)+(r.video?.far??0);judged.shots+=r.screenshots.withEventMarker;judged.shotsWithoutMoon+=r.screenshots.absent+r.screenshots.far;}
    out.judged=judged;out.adoptedAtDispatchEnd=out.perRestoration.filter(r=>r.adoptedAtDispatchEnd===true).length+' of '+EVENTS;
  }catch(e){out.void.push('judgement error: '+String(e.stack||e).slice(0,300));}
  fs.rmSync(videoDir,{recursive:true,force:true});
  out.valid=out.void.length===0;
  out.verdict=!out.valid?'VOID':(out.judged.videoWithoutMoon===0&&out.judged.shotsWithoutMoon===0?'NO FRAME WITHOUT THE MOON':'FRAMES WITHOUT THE MOON');
  const slim={...out};if(slim.log){slim.log={events:slim.log.ev.filter(e=>e.n!=='longtask'),animationFrameCount:slim.log.frames.length};}
  fs.writeFileSync(path.join(outDir,LABEL+'.json'),JSON.stringify(slim,null,1));
  console.log(JSON.stringify({label:LABEL,verdict:out.verdict,void:out.void,lifecycle:out.lifecycle,judged:out.judged,adoptedAtDispatchEnd:out.adoptedAtDispatchEnd,
    perRestoration:(out.perRestoration||[]).map(r=>({k:r.k,event:r.event,persisted:r.persisted,end:r.adoptedAtDispatchEnd,src:r.sourceAtDispatchEnd,ms:r.visibilityDispatchMs,raf:r.adoptedAtFirstFrame,long:r.longTasks,video:r.video&&[r.video.frames,r.video.absent,r.video.far,r.video.maxDPresent],shots:[r.screenshots.withEventMarker,r.screenshots.absent,r.screenshots.far,r.screenshots.maxDPresent]})),
    video:out.video&&{frames:out.video.frames,refs:out.video.references,control:[out.video.controlFramesAbsent,out.video.controlFramesJudged]},refs:out.references,isolation:out.isolation?.allowedExternal},null,0));
  process.exit(out.valid?0:2);
})();
