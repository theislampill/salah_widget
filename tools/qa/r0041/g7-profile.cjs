'use strict';
// R0041 (issue 143) G7: restoring-dispatch profiler. Native recipe; NOT part of the node glob; no product instrumentation.
// Usage: node g7-profile.cjs <servedRoot> <isoDir> <outJson> <label> <startISO> <dpr> <returns> [--cpu] [--reduced] [--fault]
// Headed Chromium, real tab switch (a second real tab brought to front; focus emulation off on the widget tab).
// Instrumentation is injected by init script only: wrappers with performance.now() around listener dispatch,
// animation-frame callbacks, render stages and the Moon/sky entry points; optional CDP CPU profile per return.
const fs=require('node:fs'),path=require('node:path');
const [root,isoDir,outFile,label,startISO,dprArg,retArg,...flags]=process.argv.slice(2);
const CPU=flags.includes('--cpu'),REDUCED=flags.includes('--reduced'),FAULT=flags.includes('--fault');
const {createEnv,launch}=require(path.join(isoDir,'iso.cjs'));
let connResets=0;process.on('uncaughtException',e=>{if(e&&e.code==='ECONNRESET'&&e.syscall==='read'){connResets++;return;}console.error(e);process.exit(1);});
const TMP=outFile+'.frames',DPR=+dprArg,W=325,H=530,N=+retArg||6;
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const DECODE_FAULT=`(()=>{const a=window.atob;window.atob=function(s){if(typeof s==='string'&&s.startsWith('U01IMR'))throw new Error('prof: injected receiver decode failure');return a.call(this,s);};})();`;
const INSTR=`(()=>{if(window.__P)return;const P=window.__P={on:false,t0:0,calls:[],depth:0,ret:[],mark:0};const now=()=>performance.now();
 const rec=(name,f,self,args)=>{if(!P.on)return f.apply(self,args);if(name==='writePrayerStatus'){const r=P.ret.at(-1);if(r&&r.prayerWrite==null){try{return f.apply(self,args);}finally{r.prayerWrite=now()-P.t0;}}}const s=now(),d=P.depth++;try{return f.apply(self,args);}finally{P.depth--;P.calls.push([name,+(s-P.t0).toFixed(2),+(now()-s).toFixed(2),d]);}};
 const label=fn=>{const s=String(fn);return (fn.name||'anon')+':'+s.replace(/\\s+/g,' ').slice(0,60);};
 const AEL=EventTarget.prototype.addEventListener,REL=EventTarget.prototype.removeEventListener,map=new WeakMap();
 EventTarget.prototype.addEventListener=function(type,fn,o){if((type==='visibilitychange'||type==='pageshow'||type==='pagehide')&&typeof fn==='function'&&!fn.__p){const tag=(this===document?'doc':this===window?'win':'el')+'/'+type+'/'+label(fn);const w=function(...a){return rec('L '+tag,fn,this,a);};w.__p=1;map.set(fn,w);return AEL.call(this,type,w,o);}return AEL.call(this,type,fn,o);};
 EventTarget.prototype.removeEventListener=function(type,fn,o){return REL.call(this,type,map.get(fn)||fn,o);};
 const RAF=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=function(cb){const tag='rAF '+label(cb);return RAF(function(t){return rec(tag,cb,this,[t]);});};
 const proto=(o,k,name)=>{const f=o[k];if(typeof f!=='function')return;o[k]=function(...a){return rec(name,f,this,a);};};
 proto(HTMLCanvasElement.prototype,'toDataURL','toDataURL');proto(CanvasRenderingContext2D.prototype,'putImageData','putImageData');proto(CanvasRenderingContext2D.prototype,'getImageData','getImageData');proto(CanvasRenderingContext2D.prototype,'drawImage','drawImage');
 proto(window,'getComputedStyle','getComputedStyle');proto(Element.prototype,'getBoundingClientRect','getBoundingClientRect');proto(SVGGraphicsElement.prototype,'getScreenCTM','getScreenCTM');
 const wrapObj=(o,k,name)=>{try{if(!o||typeof o[k]!=='function'||o[k].__p)return false;const f=o[k];const w=function(...a){return rec(name,f,this,a);};w.__p=1;o[k]=w;return o[k]===w;}catch(e){return false;}};
 P.wrapped={};const later=()=>{
  const t=[['SalahMoonRuntime','request'],['SalahMoonRuntime','surface'],['SalahMoonDetail','compose'],['SalahMoonDetail','adopt'],['SalahRealSky','compose'],['SalahSkyPreview','present'],['SalahSkyPreview','update']];
  for(const [g,k] of t){const n=g+'.'+k;if(!P.wrapped[n]&&window[g])P.wrapped[n]=wrapObj(window[g],k,n);}
  for(const k of ['updateSkySurface','maintainPrayerDay','render','noteMoonSurfaceChange','renderMoon','projectStars','paintClouds','runRenderStage','writePrayerStatus']){if(!P.wrapped[k]&&typeof window[k]==='function'){if(k==='runRenderStage'){const f=window[k];window[k]=function(name,fn,...r){return rec('stage '+name,f,this,[name,fn,...r]);};P.wrapped[k]=true;}else P.wrapped[k]=wrapObj(window,k,k);}}
  // the receiver object is frozen: replace the global with an unfrozen pass-through after the first document handoff
  const I=window.SalahMoonInitial;if(!P.wrapped.receiver&&I&&window.SalahMoonRuntime?.observe?.().current){const r=I.render;window.SalahMoonInitial={identity:I.identity,render:function(...a){return rec('SalahMoonInitial.render',r,I,a);}};P.wrapped.receiver=true;}
 };setInterval(later,100);
 // first listener of every visibilitychange (capture, registered before any page script)
 P.hides=[];AEL.call(document,'visibilitychange',()=>{P.mark^=1;if(document.hidden){P.hides.push({wall:performance.timeOrigin+now(),mark:P.mark});return;}P.on=true;P.calls=[];P.t0=now();P.depth=0;const r={t0:P.t0,mark:P.mark,wall:performance.timeOrigin+P.t0};P.ret.push(r);
   const adopted=()=>{try{return !!window.SalahMoonRuntime.observe().current;}catch(e){return null;}};
   RAF(()=>{r.frameStart=now()-P.t0;r.adoptedAtFrameStart=adopted();const mc=new MessageChannel();mc.port1.onmessage=()=>{r.frameDone=now()-P.t0;r.adoptedAfterFrame=adopted();};mc.port2.postMessage(0);});
   setTimeout(()=>{P.on=false;r.calls=P.calls;P.calls=[];},1500);},true);
 window.addEventListener('visibilitychange',()=>{if(!document.hidden&&P.ret.length){const r=P.ret.at(-1);r.dispatchMs=now()-P.t0;try{r.adoptedAtDispatchEnd=!!window.SalahMoonRuntime.observe().current;}catch(e){}}});
 // marker for compositor frames: 2 px, toggled at each visibilitychange; 1 px block recoloured each frame
 let mk=null,m2=null,n=0;const ensure=()=>{if(!document.documentElement)return false;if(!mk){mk=document.createElement('div');mk.style.cssText='position:fixed;right:0;bottom:0;width:1px;height:1px;z-index:2147483647;pointer-events:none';document.documentElement.appendChild(mk);m2=document.createElement('div');m2.style.cssText='position:fixed;right:2px;bottom:0;width:2px;height:2px;z-index:2147483647;pointer-events:none';document.documentElement.appendChild(m2);}return true;};
 AEL.call(document,'visibilitychange',()=>{if(ensure())m2.style.background=P.mark?'rgb(0,255,0)':'rgb(255,0,0)';},true);
 const tick=()=>{if(ensure()){mk.style.background=(n++&1)?'rgb(1,1,1)':'rgb(2,2,2)';if(!m2.style.background)m2.style.background='rgb(255,0,0)';}RAF(tick);};RAF(tick);
 // prayer text: first mutation of the prayer list / countdown text after each return
 const mo=new MutationObserver(ms=>{const r=P.ret.at(-1);if(!r||r.prayerMut!=null||!P.on)return;for(const m of ms){const el=m.target.nodeType===3?m.target.parentElement:m.target;if(el&&el.closest&&el.closest('.c')&&!el.closest('.sky')&&!el.closest('svg')){r.prayerMut=now()-P.t0;r.prayerMutTarget=(el.className&&String(el.className).slice(0,40))||el.tagName;break;}}});
 const startMo=()=>{if(document.body)mo.observe(document.body,{subtree:true,characterData:true,childList:true});else setTimeout(startMo,20);};startMo();
})();`;
(async()=>{
  const out={schema:'r0041-g7-prof/1',label,root:path.basename(root),startISO,dpr:DPR,returns:N,cpu:CPU,reducedMotion:REDUCED,fault:FAULT,engine:'chromium',headed:true,notes:[],void:[]};
  const env=await createEnv({root,extra:{'/away.html':()=>({body:'<!doctype html><meta charset="utf-8"><title>away</title><body style="margin:0;background:#20262e;color:#9aa;font:14px sans-serif"><p style="padding:16px">another tab</p>'})}});
  const L=await launch(env,{engine:'chromium',mode:'route',headless:false,reducedMotion:REDUCED?'reduce':'no-preference',deviceScaleFactor:DPR,viewport:{width:W,height:H},extraArgs:DPR>1?['--force-device-scale-factor='+DPR]:[]});
  let cdp=null,page=null;const frames=[];
  try{
    out.browserVersion=L.browser?L.browser.version():null;
    await L.context.addInitScript(SHIFT);await L.context.addInitScript(INSTR);if(FAULT)await L.context.addInitScript(DECODE_FAULT);
    const other=await L.context.newPage();await other.goto(env.origins.url('127.0.0.1','/away.html'));
    page=await L.context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,200)));out.pageErrors=errors;
    try{const impl=page._connection.toImpl(page);await impl.delegate._mainFrameSession._client.send('Emulation.setFocusEmulationEnabled',{enabled:false});}catch(e){out.void.push('focus emulation could not be switched off: '+String(e.message||e).slice(0,80));}
    cdp=await L.context.newCDPSession(page);
    fs.rmSync(TMP,{recursive:true,force:true});fs.mkdirSync(TMP,{recursive:true});let seq=0;
    cdp.on('Page.screencastFrame',async f=>{const ts=f.metadata.timestamp*1000;const file=path.join(TMP,String(seq++).padStart(6,'0')+'.png');fs.writeFileSync(file,Buffer.from(f.data,'base64'));frames.push({ts,file});try{await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId});}catch(e){}});
    await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'commit',timeout:120000});
    await cdp.send('Page.startScreencast',{format:'png',everyNthFrame:1,maxWidth:W*DPR,maxHeight:H*DPR});
    const refined=async(ms)=>page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain'&&window.SalahMoonRuntime.observe().current,null,{timeout:ms,polling:100}).then(()=>true).catch(()=>false);
    if(FAULT){const ok=await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().current,null,{timeout:120000,polling:100}).then(()=>true).catch(()=>false);if(!ok)out.void.push('no Moon after boot');await page.waitForTimeout(6000);}
    else if(!(await refined(300000)))out.void.push('the refined Moon did not arrive after boot');
    await page.waitForTimeout(4000);
    out.wrapped=await page.evaluate(()=>window.__P.wrapped);out.dprInPage=await page.evaluate(()=>devicePixelRatio);
    out.before=await page.evaluate(()=>{const o=window.SalahMoonRuntime.observe();return {source:o.state.visibleSource,current:o.current,detail:window.SalahMoonDetail?.state};});
    out.rect=await page.evaluate(()=>{const r=document.querySelector('.mphoto').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});out.firstHideWall=null;
    out.hiddenChecks=[];out.cpuProfiles=[];
    for(let k=0;k<N;k++){
      await other.bringToFront();await other.waitForTimeout(1500);out.hiddenChecks.push(await page.evaluate(()=>document.visibilityState));
      if(CPU){await cdp.send('Profiler.enable');await cdp.send('Profiler.setSamplingInterval',{interval:50});await cdp.send('Profiler.start');}
      await page.bringToFront();await page.waitForTimeout(2200);
      if(CPU){const {profile}=await cdp.send('Profiler.stop');out.cpuProfiles.push(summariseProfile(profile));}
      await page.waitForTimeout(2500);
    }
    await page.addStyleTag({content:'.moon-detail-canvas,.sky .moon{visibility:hidden!important}'});await page.waitForTimeout(700);out.absentWall=await page.evaluate(()=>performance.timeOrigin+performance.now());await page.waitForTimeout(400);
    await cdp.send('Page.stopScreencast').catch(()=>{});await page.waitForTimeout(200);
    out.hideWalls=await page.evaluate(()=>window.__P.hides);
    const g=await page.evaluate(()=>({ret:window.__P.ret,origin:performance.timeOrigin}));
    out.returns=analyse(g.ret,frames,out);
    out.after=await page.evaluate(()=>{const o=window.SalahMoonRuntime.observe();return {source:o.state.visibleSource,current:o.current,detail:window.SalahMoonDetail?.state,lastAdoption:o.state.lastAdoption};});
  }catch(e){out.error=String(e.stack||e).slice(0,900);out.void.push('harness error');}
  await L.close().catch(()=>{});
  const iso=env.finish();out.isolation={allowedExternal:iso.allowedExternal,externalAttempts:iso.externalAttempts,totals:iso.totalRequests,refusedTunnelResetsSwallowed:connResets};
  if(iso.allowedExternal!==0)out.void.push('isolation: a non-loopback request was allowed');
  fs.rmSync(TMP,{recursive:true,force:true});
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));
  const r=out.returns||[];const pick=k=>r.map(x=>x[k]==null?null:+(+x[k]).toFixed(1));
  console.log(JSON.stringify({label,dpr:DPR,void:out.void,allowed:iso.allowedExternal,dispatch:pick('dispatchMs'),frameDone:pick('frameDone'),firstNewFrame:pick('firstNewFrameMs'),firstNewHasMoon:r.map(x=>x.firstNewFrameHasMoon),firstMoonFrame:pick('firstMoonFrameMs'),moonlessNewFrames:r.map(x=>x.moonlessNewFrames),prayerWrite:pick('prayerWrite'),firstFrameAfterPrayer:pick('firstFrameAfterPrayerMs'),adoptedEnd:r.map(x=>x.adoptedAtDispatchEnd)}));
})();
function summariseProfile(p){
  // self time per function, and inclusive time per function, for samples whose stack is under a visibilitychange
  // listener or an animation-frame callback (attributed to the outermost such frame)
  const nodes=new Map();for(const n of p.nodes)nodes.set(n.id,n);const parent=new Map();for(const n of p.nodes)for(const c of n.children||[])parent.set(c,n.id);
  const dt=p.timeDeltas;const self={},incl={},roots={};let total=0;
  const nm=n=>{const c=n.callFrame;return (c.functionName||'(anon)')+'@'+(c.url?c.url.split('/').pop().slice(0,24):'')+':'+c.lineNumber;};
  for(let i=0;i<p.samples.length;i++){const d=(dt[i+1]??0)/1000;let id=p.samples[i];const chain=[];while(id!=null){chain.push(nodes.get(id));id=parent.get(id);}
    const top=chain[0];const tn=top.callFrame.functionName;if(tn==='(idle)'||tn==='(program)'||tn==='(garbage collector)'){self[tn]=(self[tn]||0)+d;continue;}
    total+=d;self[nm(top)]=(self[nm(top)]||0)+d;const seen=new Set();for(const n of chain){const k=nm(n);if(!seen.has(k)){seen.add(k);incl[k]=(incl[k]||0)+d;}}
    const root=chain.at(-2)||chain.at(-1);roots[nm(root)]=(roots[nm(root)]||0)+d;}
  const top=(o,n)=>Object.entries(o).sort((a,b)=>b[1]-a[1]).slice(0,n).map(([k,v])=>[k,+v.toFixed(2)]);
  return {jsMs:+total.toFixed(1),self:top(self,30),inclusive:top(incl,50),roots:top(roots,12)};
}

function analyse(rets,frames,out){
  const {decodePng}=require(path.join(isoDir,'png.cjs'));const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
  frames.sort((a,b)=>a.ts-b.ts);const cache=new Map();
  const load=f=>{if(cache.has(f.file))return cache.get(f.file);let m=null;try{const img=decodePng(fs.readFileSync(f.file));const s=img.width/W,d=img.data,Wd=img.width;
    const x=Math.min(Wd-1,Math.floor(322*s)),y=Math.min(img.height-1,Math.floor(529*s)),i=4*(y*Wd+x);const mk=d[i]>200&&d[i+1]<80?0:d[i+1]>200&&d[i]<80?1:null;
    const rc=out.rect,x0=Math.floor(rc.x*s),y0=Math.floor(rc.y*s),S=Math.floor(Math.min(rc.w,rc.h)*s),cx=x0+S/2,cy=y0+S/2,disc=[];
    for(let yy=Math.floor(cy-.47*S);yy<cy+.47*S;yy++)for(let xx=Math.floor(cx-.47*S);xx<cx+.47*S;xx++){if(xx<0||yy<0||xx>=Wd||yy>=img.height)continue;if(Math.hypot(xx+.5-cx,yy+.5-cy)<=.47*S)disc.push(Y(d,4*(yy*Wd+xx)));}
    m={mk,disc:Float32Array.from(disc)};}catch(e){}cache.set(f.file,m);return m;};
  const dist=(a,b)=>{if(!a||!b||a.length!==b.length)return null;let s=0;for(let i=0;i<a.length;i++)s+=Math.abs(a[i]-b[i]);return s/a.length;};
  const near=w=>frames.reduce((p,x)=>!p||Math.abs(x.ts-w)<Math.abs(p.ts-w)?x:p,null),lastBefore=w=>{let r=null;for(const f of frames){if(f.ts<w)r=f;else break;}return r;};
  const absent=load(near(out.absentWall+200));
  return rets.map((r,k)=>{const w=r.wall,h=(out.hideWalls||[])[k];const pre=h?load(lastBefore(h.wall)):null;
    const win=frames.filter(f=>f.ts>=w-1&&f.ts<=w+900).map(f=>({f,m:load(f)})).filter(x=>x.m&&x.m.mk===r.mark);
    const cls=x=>{const dp=dist(x.m.disc,pre?.disc),da=dist(x.m.disc,absent?.disc);return {dp,da,moon:dp!=null&&da!=null&&dp<da};};
    const c=win.map(x=>({ms:+(x.f.ts-w).toFixed(1),...cls(x)}));const firstMoon=c.find(x=>x.moon);
    const pw=r.prayerWrite!=null?r.prayerWrite:null;const afterPrayer=pw!=null?c.find(x=>x.ms>=pw):null;
    const {calls,...rest}=r;
    return {...rest,calls,firstNewFrameMs:c[0]?.ms??null,firstNewFrameHasMoon:c[0]?.moon??null,firstMoonFrameMs:firstMoon?.ms??null,moonlessNewFrames:firstMoon?c.filter(x=>x.ms<firstMoon.ms).length:c.length,
      firstFrameAfterPrayerMs:afterPrayer?.ms??null,frames:c.slice(0,8).map(x=>[x.ms,x.dp==null?null:+x.dp.toFixed(2),x.da==null?null:+x.da.toFixed(2),x.moon]),refDist:pre&&absent?+dist(pre.disc,absent.disc).toFixed(2):null};});
}
