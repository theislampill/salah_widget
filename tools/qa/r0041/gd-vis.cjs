'use strict';
// R0041 (issue 143) rows R41-GD (phase 1, on the BASE build), R41-VIS and R41-LGT (night cells), and the normal-operation
// swap counts of R41-SWP. Native recipe; NOT part of the node glob.
//
// One HEADED browser per invocation (one browser at a time), viewport 325 x 530 (the widget card) at the requested
// device-pixel ratio (Chromium also --force-device-scale-factor). Several cells run in that ONE browser, each in its own
// isolated context (iso.cjs newContext: the same proxy, resolver rules, catch-all route before navigation and in-page
// shim), concurrently, so a window cell and its control share the same load. Synthetic fixture (lat 24.47, lon 39.61,
// method 4); an init-script Date shift starts each page clock at its cell instant, then real speed.
//
// Per cell:
//   - a REAL-TIME RECORDING (Playwright recordVideo; in Chromium this is the DevTools screencast) at CSS size;
//   - a FRAME SEQUENCE: a serial screenshot loop clipped to the .mphoto rectangle at device pixels, each shot timed by
//     its request and return instants on the system clock;
//   - a TIME MARKER: four 8 x 8 px blocks at the card's bottom-right corner (outside the Moon) encode the system clock
//     in 40 ms slots (12 bits) at the animation frame that painted them, so every recorded frame carries the instant
//     it shows (harness instrument; it covers 32 x 8 px of the card's corner);
//   - in-page 4 Hz log: the .mphoto rectangle, observe() (accepted record key, visibleSource, current), reveal classes,
//     visibilityState; 1 Hz qaState().moonTruth light fields; every refinement job posted to the Moon worker.
//   - optional positive control (cell flag 'seed'): at settle + 60 s, SalahMoonDetail.clear() and, 300 ms later,
//     SalahRealSky.compose() (the seeded 300 ms blank of R41-GD); its frames are reported separately.
//   - end controls: the Moon layers hidden by a style for 1.5 s (absent reference) - must be classified ABSENT.
//
// Detector (issue 143 G.1, literal), on every shot and every recorded frame, inside the disc (r <= 0.47 x side):
//   Y = 0.2126R + 0.7152G + 0.0722B; stars = disc pixels with Y > max(median_disc, median_corner) + 40, corners
//   r >= 0.53 x side; dRef = mean |Y - Y_ref| over the disc; ABSENT if stars >= 10 or dRef > 4.
//   Two references are reported: FIXED (the first frame after the first refined result, as G.1 states) and ROLLING
//   (the last frame judged PRESENT, at least 1 s earlier) because the Moon moves and re-renders over ten minutes.
//
// Usage: node gd-vis.cjs <repoRoot> <outDir> <engine> <dpr> <motion:reduce|full> <secondsAfterSettle> <label>
//          <cell>[,<cell>...]       cell = name=ISO[:seed]
// Needs PLAYWRIGHT_PKG and ffmpeg on PATH.
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [root,outDir,engine,dprArg,motion,secArg,label,cellArg]=process.argv.slice(2);
const DPR=+dprArg,SECONDS=+secArg,W=325,H=530,VW=326,VH=530;
const CELLS=cellArg.split(',').map(c=>{const [name,rest]=c.split('=');const [iso,flag]=rest.split(/:(?=seed$)/);return {name,iso,seed:flag==='seed',startMs:Date.parse(iso)};});
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1'+(motion==='full'?'&motion=full':'');
const PAL=[[0,0,0],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[255,0,255],[0,255,255],[255,255,255]];
const shift=ms=>`(()=>{const ND=Date,sys=ND.now.bind(ND),off=${ms}-sys();window.__sysNow=sys;class D extends ND{constructor(...a){super(...(a.length?a:[sys()+off]));}static now(){return sys()+off;}}window.Date=D;})();`;
const INSTR=`(()=>{const PAL=${JSON.stringify(PAL)};const R=window.__gd={log:[],light:[],jobs:[],seed:[]};let mk=null,last=-1;
 {const P=Worker.prototype.postMessage;Worker.prototype.postMessage=function(m,...t){try{if(m&&m.kind==='render'&&m.scene)R.jobs.push({sys:window.__sysNow(),fraction:m.scene.fraction,lead:m.scene.leadDirection??null,sunY:Array.isArray(m.scene.sun)?m.scene.sun[1]:null});}catch(e){}return P.call(this,m,...t);};}
 const paint=()=>{if(!document.documentElement)return;if(!mk){mk=document.createElement('div');mk.style.cssText='position:fixed;right:8px;bottom:6px;width:32px;height:8px;z-index:2147483647;pointer-events:none;display:flex';for(let k=0;k<4;k++){const b=document.createElement('div');b.style.cssText='width:8px;height:8px';mk.appendChild(b);}document.documentElement.appendChild(mk);}
  const slot=Math.floor(window.__sysNow()/40)&4095;if(slot===last)return;last=slot;for(let k=0;k<4;k++)mk.children[k].style.background='rgb('+PAL[(slot>>(3*k))&7]+')';};
 const tick=()=>{paint();requestAnimationFrame(tick);};requestAnimationFrame(tick);
 setInterval(()=>{let o=null;try{o=window.SalahMoonRuntime?.observe?.()??null;}catch(e){}const c=document.querySelector('.c'),m=document.querySelector('.mphoto'),b=m?m.getBoundingClientRect():null,s=o?.state,sc=s?.accepted?.scene;
  R.log.push([window.__sysNow(),b?+b.x.toFixed(2):null,b?+b.y.toFixed(2):null,b?+b.width.toFixed(2):null,s?.visibleSource??null,o?.current?1:0,sc?[sc.mode,sc.fraction,sc.utcMs??sc.utc??null,sc.leadDirection??null].join('|'):null,c&&c.classList.contains('moon-ready')?1:0,c&&c.classList.contains('real-sky-composed')?1:0,document.visibilityState==='visible'?1:0,Date.now()]);},250);
 setInterval(()=>{try{const t=window.qaState?.().moonTruth;if(t)R.light.push([window.__sysNow(),t.moonlightOpacity,t.displayMode,JSON.stringify(t.lunarLight??null).slice(0,160),t.phaseFraction,t.moonAltitudeDeg]);}catch(e){}},1000);
})();`;
const Yf=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
const median=a=>{if(!a.length)return 0;const s=Float64Array.from(a).sort();return s[s.length>>1];};
// Disc sample of a raster: (x0,y0) top-left of the Moon square in raster pixels, S its side in raster pixels.
function disc(data,width,height,ch,x0,y0,S){const cx=x0+S/2,cy=y0+S/2,d=[],corner=[],pts=[];const at=(x,y)=>x<0||y<0||x>=width||y>=height?null:Yf(data,ch*(y*width+x));
  for(let y=Math.floor(y0);y<y0+S;y++)for(let x=Math.floor(x0);x<x0+S;x++){if(x<0||y<0||x>=width||y>=height)continue;const r=Math.hypot(x+.5-cx,y+.5-cy),v=at(x,y);
    if(r<=.47*S){d.push(v);if(r<=.47*S-3){let m=0,n=0;for(const [dx,dy] of [[2,0],[-2,0],[0,2],[0,-2],[2,2],[2,-2],[-2,2],[-2,-2]]){const u=at(x+dx,y+dy);if(u!=null){m+=u;n++;}}pts.push(v-(n?m/n:v));}else pts.push(0);}
    else if(r>=.53*S)corner.push(v);}
  return {d:Float32Array.from(d),corner,pts,key:[Math.round(x0*10),Math.round(y0*10),Math.round(S*10)].join(',')};}
// Two star counts. LITERAL (G.1): disc pixels with Y > max(median_disc, median_corner) + 40. POINT-LIKE (the validated
// variant of witness.cjs, contract 2.1): Y exceeds the mean of its 8 neighbours at distance 2 by > 30 and the corner
// median by > 30, counted above the cell's own baseline (the fixed reference frame), because bright lunar relief at
// full Moon exceeds the literal threshold in frames that are present (seen: 30 such pixels at 23 Nov, a present Moon).
function judge(s,refFixed,refRoll,baseline){const md=median(s.d),mc=median(s.corner),th=Math.max(md,mc)+40;let lit=0,pt=0;for(let i=0;i<s.d.length;i++){if(s.d[i]>th)lit++;if(s.pts[i]>30&&s.d[i]>mc+30)pt++;}
  const dr=r=>r&&r.length===s.d.length?(()=>{let t=0;for(let i=0;i<r.length;i++)t+=Math.abs(s.d[i]-r[i]);return t/r.length;})():null;
  const mean=s.d.reduce((p,v)=>p+v,0)/(s.d.length||1),ptx=pt-(baseline??0),sameGrid=!!refRoll&&refRoll.key===s.key,dF=dr(refFixed),dR=sameGrid?dr(refRoll.d):null,dMean=refRoll?Math.abs(mean-refRoll.mean):null;
  // ROLLING verdict (the one reported as absentRoll): point-like stars above baseline, or the disc mean moved > 4 codes
  // from the last PRESENT frame, or (same sampling grid only) the mean per-pixel change > 4. A frame whose sampling grid
  // moved (the Moon slot drifts by sub-pixel amounts as the Moon moves) is compared by mean and stars only; if it is
  // present it re-anchors the reference (a stale reference at a shifted grid otherwise locks every later frame ABSENT).
  return {starsLit:lit,starsPt:pt,stars:ptx,dFixed:dF==null?null:+dF.toFixed(2),dRoll:dR==null?null:+dR.toFixed(2),mean:+mean.toFixed(1),absentLiteral:lit>=10||(dF!=null&&dF>4),absentFixed:ptx>=10||(dF!=null&&dF>4),absentRoll:ptx>=10||(dMean!=null&&dMean>4)||(dR!=null&&dR>4),dMean:dMean==null?null:+dMean.toFixed(2),sameGrid,n:s.d.length};}
// Marker blocks: CSS x 285+8k .. 292+8k, y 516..523 (right 8 px, bottom 6 px: Firefox's recording shows the viewport
// shifted by about (+4, -2) px and cropped, so the marker stays away from the edges). (dx, dy) is the recording's offset,
// calibrated per recording by the best-reading offset over its first frames.
const readMarker=(data,width,ch,dx=0,dy=0)=>{let slot=0,worst=0;for(let k=0;k<4;k++){let r=0,g=0,b=0,n=0;const bx=W-40+8*k+dx;for(let y=H-12+dy;y<H-8+dy;y++)for(let x=bx+2;x<bx+6;x++){const i=ch*(y*width+x);r+=data[i];g+=data[i+1];b+=data[i+2];n++;}r/=n;g/=n;b/=n;
  let best=0,bd=1e9;PAL.forEach((p,j)=>{const dd=Math.abs(p[0]-r)+Math.abs(p[1]-g)+Math.abs(p[2]-b);if(dd<bd){bd=dd;best=j;}});worst=Math.max(worst,bd);slot|=best<<(3*k);}return {slot,worst};};
const rectAt=(log,sys)=>{let best=null;for(const e of log){if(e[1]==null)continue;if(e[0]<=sys+125)best=e;else break;}return best?{x:best[1],y:best[2],w:best[3]}:null;};
function decodeVideo(file,onFrame){return new Promise((resolve,reject)=>{const size=VW*VH*3;let buf=Buffer.alloc(0),err='',i=0;
  const p=spawn('ffmpeg',['-v','error','-i',file,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],{stdio:['ignore','pipe','pipe']});
  p.stdout.on('data',d=>{buf=buf.length?Buffer.concat([buf,d]):d;while(buf.length>=size){onFrame(buf.subarray(0,size),i++);buf=buf.subarray(size);}});
  p.stderr.on('data',d=>{err+=d;});p.on('error',reject);p.on('close',code=>code===0?resolve(i):reject(new Error('ffmpeg '+code+': '+err.slice(0,300))));});}
// Minimal PNG encoder (RGB, filter 0) for crops.
const zlib=require('node:zlib');const crcT=(()=>{const t=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
const crc=b=>{let c=0xffffffff;for(const x of b)c=crcT[(c^x)&255]^(c>>>8);return (c^0xffffffff)>>>0;};
const chunk=(type,data)=>{const l=Buffer.alloc(4);l.writeUInt32BE(data.length);const td=Buffer.concat([Buffer.from(type),data]);const c=Buffer.alloc(4);c.writeUInt32BE(crc(td));return Buffer.concat([l,td,c]);};
function encodePng(w,h,rgb){const raw=Buffer.alloc((3*w+1)*h);for(let y=0;y<h;y++){raw[y*(3*w+1)]=0;rgb.copy?rgb.copy(raw,y*(3*w+1)+1,3*w*y,3*w*(y+1)):Buffer.from(rgb.buffer,rgb.byteOffset+3*w*y,3*w).copy(raw,y*(3*w+1)+1);}
  const ih=Buffer.alloc(13);ih.writeUInt32BE(w,0);ih.writeUInt32BE(h,4);ih[8]=8;ih[9]=2;return Buffer.concat([Buffer.from([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a]),chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);}
const rgbOf=img=>{const n=img.width*img.height,o=Buffer.alloc(3*n);for(let i=0;i<n;i++){o[3*i]=img.data[4*i];o[3*i+1]=img.data[4*i+1];o[3*i+2]=img.data[4*i+2];}return o;};

// Every page call is bounded (a hung call in one engine must not hold the whole launch); a timed-out call is recorded.
const T=(p,ms,tag,list)=>{let h;return Promise.race([Promise.resolve(p).finally(()=>clearTimeout(h)),new Promise(r=>{h=setTimeout(()=>{list&&list.push(tag);r('timeout');},ms);})]);};
async function runCell(L,env,cell,dir){const hung=[];
  const ctx=await L.newContext({recordVideo:{dir:path.join(dir,'.video'),size:{width:VW,height:VH}}});
  await ctx.addInitScript(shift(cell.startMs));await ctx.addInitScript(INSTR);
  const page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,200)));
  const pageCreatedSys=Date.now();
  await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'load',timeout:120000});
  const settledOk=await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:240000,polling:250}).then(()=>true).catch(()=>false);
  const settleSys=Date.now();
  const shots=[];let rect=null,capturing=true,ctlFrom=null,ctlTo=null,seedFrom=null,seedTo=null,hideFrom=null,hideTo=null;
  const crops=path.join(dir,'crops');fs.mkdirSync(crops,{recursive:true});
  let refFixed=null,refRoll=null,baseline=null,lastPresentSys=0,saved=0;
  const updateRect=async()=>{const r=await page.evaluate(()=>{const b=document.querySelector('.mphoto')?.getBoundingClientRect();return b?{x:b.x,y:b.y,w:b.width,h:b.height}:null;}).catch(()=>null);if(r)rect=r;};
  await updateRect();
  const rectTimer=setInterval(()=>{updateRect();},1000);
  // Chromium: full-page shots (a clipped Chromium screenshot re-sizes the recording's screencast), timed by the marker
  // they show; Firefox and WebKit: shots clipped to the Moon square (faster), timed by request/return on the system clock.
  const FULL=engine==='chromium';
  // Firefox and WebKit: shot starts at least PACE ms apart (an unpaced loop over four headed pages starved Firefox's
  // protocol: screenshot, evaluate and close calls timed out); Chromium's full-page shots are slower than this anyway.
  const PACE=+(process.env.R41_PACE_MS||40);let lastStart=0;
  const loop=(async()=>{while(capturing){if(!rect){await new Promise(r=>setTimeout(r,50));continue;}const r=rect;
    if(!FULL){const w=lastStart+PACE-Date.now();if(w>0)await new Promise(q=>setTimeout(q,w));lastStart=Date.now();}
    const clip={x:Math.max(0,Math.floor(r.x)),y:Math.max(0,Math.floor(r.y))};clip.width=Math.min(W-clip.x,Math.ceil(r.x+r.w)-clip.x);clip.height=Math.min(H-clip.y,Math.ceil(r.y+r.h)-clip.y);
    const t0=Date.now();let png;try{png=await T(page.screenshot(FULL?{scale:'device',animations:'allow',caret:'initial'}:{clip,scale:'device',animations:'allow',caret:'initial'}),8000,'screenshot',hung);if(png==='timeout')continue;}catch(e){await new Promise(r=>setTimeout(r,30));continue;}const t1=Date.now();
    let img;try{img=decodePng(png);}catch(e){continue;}
    let t=t0,markerOk=null;
    if(FULL){const k=img.width/W,small={data:new Uint8Array(W*H*4)};for(let y=H-16;y<H;y++)for(let x=W-48;x<W;x++){const si=4*(Math.floor(y*k)*img.width+Math.floor(x*k)),di=4*(y*W+x);small.data[di]=img.data[si];small.data[di+1]=img.data[si+1];small.data[di+2]=img.data[si+2];}
      const mk=readMarker(small.data,W,4);markerOk=mk.worst<=200;if(markerOk){const base=Math.floor(t0/40),c=[-1,0,1].map(w=>(Math.floor(base/4096)+w)*4096+mk.slot).sort((x,y)=>Math.abs(x-base)-Math.abs(y-base))[0];t=c*40;}}
    const ox=FULL?0:clip.x,oy=FULL?0:clip.y,k=FULL?img.width/W:img.width/clip.width,S=Math.min(r.w,r.h)*k,s=disc(img.data,img.width,img.height,4,(r.x-ox)*k,(r.y-oy)*k,S);
    if(!refFixed&&t0>settleSys){refFixed=s.d;baseline=judge(s,null,null,0).starsPt;refRoll={d:s.d,mean:judge(s,null,null,0).mean,key:s.key};lastPresentSys=t;}
    const j=judge(s,refFixed,refRoll,baseline);
    const inCtl=ctlFrom&&t0>=ctlFrom&&t0<=(ctlTo??Infinity),inSeed=(seedFrom&&t1>=seedFrom&&t0<=(seedTo??seedFrom+300)+200)||(hideFrom&&t1>=hideFrom&&t0<=(hideTo??hideFrom+300)+200);
    if(!j.absentRoll&&!inCtl&&!inSeed&&t0>settleSys&&(!refRoll||t-lastPresentSys>=1000||refRoll.key!==s.key)){refRoll={d:s.d,mean:j.mean,key:s.key};lastPresentSys=t;}
    const f={t,t0,t1,markerOk,...j,inCtl:inCtl?1:0,inSeed:inSeed?1:0};delete f.n;shots.push(f);
    if((j.absentRoll||inSeed)&&saved<150&&t0>settleSys){fs.writeFileSync(path.join(crops,`shot-${t0}-${j.absentRoll?'A':'p'}${inSeed?'-seed':''}${inCtl?'-ctl':''}.png`),png);saved++;}
  }})();
  // observation
  const endAt=settleSys+SECONDS*1000;const seedAt=cell.seed?settleSys+60000:null;
  while(Date.now()<endAt){
    if(seedAt&&!seedFrom&&Date.now()>=seedAt){const w=await T(page.evaluate(()=>{const s=window.__sysNow();window.SalahMoonDetail?.clear();window.__gd.seed.push({clear:s});setTimeout(()=>{window.__gd.seed.push({compose:window.__sysNow()});window.SalahRealSky?.compose();},300);return s;}),10000,'seed-clear',hung);seedFrom=w==='timeout'?Date.now():w;seedTo=seedFrom+300;}
    if(seedAt&&!hideFrom&&Date.now()>=seedAt+60000){const w=await T(page.evaluate(()=>{const s=window.__sysNow(),st=document.createElement('style');st.textContent='.moon-detail-canvas,.sky .moon,.mphoto{visibility:hidden!important}';document.head.appendChild(st);window.__gd.seed.push({hide:s});setTimeout(()=>{st.remove();window.__gd.seed.push({show:window.__sysNow()});},300);return s;}),10000,'seed-hide',hung);hideFrom=w==='timeout'?Date.now():w;hideTo=hideFrom+300;}
    await new Promise(r=>setTimeout(r,250));}
  // absent control
  ctlFrom=Date.now()+300;await T(page.evaluate(()=>{const st=document.createElement('style');st.textContent='.moon-detail-canvas,.sky .moon,.mphoto{visibility:hidden!important}';document.head.appendChild(st);}),10000,'control-style',hung);await new Promise(r=>setTimeout(r,1800));ctlTo=Date.now();
  capturing=false;await T(loop,15000,'loop-end',hung);clearInterval(rectTimer);
  let inpage=await T(page.evaluate(()=>({log:window.__gd.log,light:window.__gd.light,jobs:window.__gd.jobs,seed:window.__gd.seed})),20000,'inpage-read',hung);if(inpage==='timeout')inpage={log:[],light:[],jobs:[],seed:[],swaps:[],forced:[],truth:null};
  const video=page.video();await T(page.close(),90000,'page-close',hung);await T(ctx.close(),120000,'context-close',hung);
  let vpath=video?await T(video.path(),60000,'video-path',hung):null;if(vpath==='timeout')vpath=null;
  return {hung,pageCreatedSys,settleSys,settledOk,endAt,ctlFrom,ctlTo,seedFrom,seedTo,hideFrom,hideTo,shots,inpage,errors,vpath};
}
async function analyseVideo(cell,r,dir){
  if(!r.vpath||!fs.existsSync(r.vpath))return {error:'no recording'};
  const final=path.join(dir,cell.name+'.webm');fs.copyFileSync(r.vpath,final);
  const frames=[];let refFixed=null,refRoll=null,vbase=null,lastPresent=0,prevSys=r.pageCreatedSys;const vcrops=path.join(dir,'vcrops');fs.mkdirSync(vcrops,{recursive:true});let saved=0;
  // calibrate the recording's offset: the (dx, dy) that reads the marker best over frames 100-160 of the recording
  let cal=null;{const sample=[];await decodeVideo(final,(buf,i)=>{if(i>=100&&i<160&&i%3===0)sample.push(Buffer.from(buf));});let best=null;
    for(let dx=-6;dx<=8;dx++)for(let dy=-6;dy<=4;dy++){let ok=0;for(const b of sample)if(readMarker(b,VW,3,dx,dy).worst<=90)ok++;if(!best||ok>best.ok)best={dx,dy,ok};}cal=best;}
  const DX=cal?cal.dx:0,DY=cal?cal.dy:0;
  await decodeVideo(final,(buf,i)=>{const mk=readMarker(buf,VW,3,DX,DY);if(mk.worst>200){frames.push({i,bad:1});return;}
    // unwrap the 12-bit slot to the system clock near the previous frame (or the expected time)
    const base=Math.floor(prevSys/40),cand=[-1,0,1].map(w=>(Math.floor(base/4096)+w)*4096+mk.slot).sort((a,b)=>Math.abs(a-base)-Math.abs(b-base))[0],sys=cand*40;prevSys=sys;
    const rc=rectAt(r.inpage.log,sys);if(!rc){frames.push({i,sys,norect:1});return;}
    const s=disc(buf,VW,VH,3,rc.x+DX,rc.y+DY,rc.w);if(!refFixed&&sys>r.settleSys){refFixed=s.d;vbase=judge(s,null,null,0).starsPt;refRoll={d:s.d,mean:judge(s,null,null,0).mean,key:s.key};lastPresent=sys;}
    const j=judge(s,refFixed,refRoll,vbase);const inCtl=r.ctlFrom&&sys>=r.ctlFrom&&sys<=r.ctlTo,inSeed=(r.seedFrom&&sys>=r.seedFrom-50&&sys<=r.seedTo+250)?1:(r.hideFrom&&sys>=r.hideFrom-50&&sys<=r.hideTo+250)?2:0;
    if(!j.absentRoll&&!inCtl&&!inSeed&&sys>r.settleSys&&(!refRoll||sys-lastPresent>=1000||refRoll.key!==s.key)){refRoll={d:s.d,mean:j.mean,key:s.key};lastPresent=sys;}
    frames.push({i,sys,stars:j.stars,starsLit:j.starsLit,absentLiteral:j.absentLiteral?1:0,dFixed:j.dFixed,dRoll:j.dRoll,mean:j.mean,absentRoll:j.absentRoll?1:0,absentFixed:j.absentFixed?1:0,inCtl:inCtl?1:0,inSeed});
    if((j.absentRoll||inSeed)&&sys>r.settleSys&&saved<80){const x0=Math.max(0,Math.floor(rc.x)-4),y0=Math.max(0,Math.floor(rc.y)-4),w=Math.min(VW-x0,Math.ceil(rc.w)+8),h=Math.min(VH-y0,Math.ceil(rc.w)+8),o=Buffer.alloc(3*w*h);
      for(let y=0;y<h;y++)buf.copy(o,3*w*y,3*(VW*(y0+y)+x0),3*(VW*(y0+y)+x0+w));fs.writeFileSync(path.join(vcrops,`v-${sys}-${j.absentRoll?'A':'p'}${inSeed?'-seed':''}.png`),encodePng(w,h,o));saved++;}});
  return {file:path.basename(final),bytes:fs.statSync(final).size,frames,offset:cal};
}
function intervalsOf(list,key,tkey){const out=[];let open=null,last=null;for(const f of list){if(f[key]&&open==null)open=f[tkey];if(!f[key]&&open!=null){out.push({from:open,to:f[tkey],ms:f[tkey]-open});open=null;}last=f[tkey];}if(open!=null)out.push({from:open,to:null,ms:null});return out;}
(async()=>{
  fs.mkdirSync(outDir,{recursive:true});
  const env=await createEnv({root});
  const extraArgs=engine==='chromium'?['--disable-features=NetworkPrediction,OptimizationHints,MediaRouter,CalculateNativeWinOcclusion','--disable-backgrounding-occluded-windows',...(DPR>1?['--force-device-scale-factor='+DPR]:[])]:[];
  const L=await launch(env,{engine,mode:'route',headless:false,deviceScaleFactor:DPR,reducedMotion:motion==='full'?'no-preference':'reduce',extraArgs});
  const out={schema:'r0041-gd-vis/1',label,root:path.basename(path.resolve(root)),engine,dpr:DPR,motion,headed:true,browserVersion:L.browser?.version?.()??null,secondsAfterSettle:SECONDS,fragment:FRAG,cells:{}};
  let results;
  try{results=await Promise.all(CELLS.map(c=>{const dir=path.join(outDir,label,c.name);fs.mkdirSync(dir,{recursive:true});return runCell(L,env,c,dir).then(r=>({c,r,dir}),e=>({c,error:String(e.stack||e).slice(0,600),dir}));}));}
  finally{const closed=await T(L.close().catch(()=>{}),180000,'browser-close',null);if(closed==='timeout'){try{L.browser?.process?.()?.kill();}catch(e){}out.browserCloseTimedOut=true;}}
  const iso=env.finish();out.isolation={allowedExternal:iso.allowedExternal,externalAttempts:iso.externalAttempts,totalRequests:iso.totalRequests,byLayerHostOutcome:iso.externalByLayerHostOutcome};
  for(const {c,r,dir,error} of results){
    if(error){out.cells[c.name]={error};continue;}
    const v=await analyseVideo(c,r,dir).catch(e=>({error:String(e).slice(0,300)}));
    const off=c.startMs-r.pageCreatedSys;   // page clock = system clock + (startMs - t_shift); approximate to the first log
    const firstLog=r.inpage.log[0];const pageOff=firstLog?firstLog[10]-firstLog[0]:off;
    const pageMs=sys=>sys+pageOff;
    const obsShots=r.shots.filter(s=>s.t>r.settleSys&&s.t<r.endAt);
    const steps=[];for(let m=Math.ceil(pageMs(r.settleSys)/60000)*60000;m<pageMs(r.endAt);m+=60000)steps.push(m-pageOff);
    const perStep=steps.map(sys=>{const win=obsShots.filter(s=>s.t>=sys-1000&&s.t<Math.min(sys+15000,r.endAt)&&!s.inSeed);const vf=(v.frames||[]).filter(f=>f.sys>=sys-1000&&f.sys<Math.min(sys+15000,r.endAt)&&!f.inSeed&&!f.inCtl);
      return {sys,pageISO:new Date(pageMs(sys)).toISOString(),shotsAbsentRoll:win.filter(s=>s.absentRoll).length,shotsAbsentFixed:win.filter(s=>s.absentFixed).length,videoAbsentRoll:vf.filter(f=>f.absentRoll).length,videoAbsentFixed:vf.filter(f=>f.absentFixed).length,
        jobsPosted:r.inpage.jobs.filter(j=>j.sys>=sys-1000&&j.sys<sys+59000).length};});
    const vObs=(v.frames||[]).filter(f=>f.sys>r.settleSys&&f.sys<r.endAt&&!f.inSeed&&!f.inCtl);
    const log=r.inpage.log.filter(e=>e[0]>r.settleSys&&e[0]<r.endAt);const keys=[];for(const e of log)if(e[6]!==keys.at(-1)?.k)keys.push({sys:e[0],k:e[6],src:e[4]});
    const shotsI=obsShots.map((s,i)=>i?s.t0-obsShots[i-1].t0:null).filter(Boolean);
    const cellOut={hungCalls:r.hung,iso:c.iso,seed:c.seed,settledToRefined:r.settledOk,settleAfterLoadMs:r.settleSys-r.pageCreatedSys,pageErrors:r.errors,
      minuteSteps:steps.length,
      shots:{count:obsShots.length,medianIntervalMs:median(shotsI),p90IntervalMs:shotsI.length?Float64Array.from(shotsI).sort()[Math.floor(.9*shotsI.length)]:null,
        absentRoll:obsShots.filter(s=>s.absentRoll&&!s.inSeed).length,absentFixed:obsShots.filter(s=>s.absentFixed&&!s.inSeed).length,
        absentLiteral:obsShots.filter(s=>s.absentLiteral&&!s.inSeed).length,markerUnread:obsShots.filter(s=>s.markerOk===false).length,absentRollIntervals:intervalsOf(obsShots.filter(s=>!s.inSeed),'absentRoll','t').slice(0,40),maxStars:Math.max(0,...obsShots.map(s=>s.stars)),maxDRoll:Math.max(0,...obsShots.map(s=>s.dRoll??0)),maxDFixed:Math.max(0,...obsShots.map(s=>s.dFixed??0))},
      video:v.error?{error:v.error}:{offset:v.offset,file:v.file,bytes:v.bytes,frames:v.frames.length,unreadableMarker:v.frames.filter(f=>f.bad).length,observed:vObs.length,absentRoll:vObs.filter(f=>f.absentRoll).length,absentFixed:vObs.filter(f=>f.absentFixed).length,absentLiteral:vObs.filter(f=>f.absentLiteral).length,
        absentRollIntervals:intervalsOf(vObs,'absentRoll','sys').slice(0,40),maxStars:Math.max(0,...vObs.map(f=>f.stars)),maxDRoll:Math.max(0,...vObs.map(f=>f.dRoll??0))},
      perStep,jobsPosted:r.inpage.jobs.filter(j=>j.sys>r.settleSys&&j.sys<r.endAt).length,jobs:r.inpage.jobs.filter(j=>j.sys>r.settleSys-60000&&j.sys<r.endAt),
      acceptedRecordChanges:keys.length-1,recordTimeline:keys.slice(0,60),
      hiddenSamples:log.filter(e=>!e[9]).length,notCurrentSamples:log.filter(e=>!e[5]).length,moonReadyOffSamples:log.filter(e=>!e[7]).length,
      light:{samples:r.inpage.light.filter(x=>x[0]>r.settleSys&&x[0]<r.endAt).length,distinct:[...new Set(r.inpage.light.filter(x=>x[0]>r.settleSys&&x[0]<r.endAt).map(x=>[x[1],x[2],x[3]].join(' ')))].slice(0,12),phaseFraction:r.inpage.light.at(-1)?.[4],moonAltitudeDeg:r.inpage.light.at(-1)?.[5]},
      seed:c.seed?{detailClearAt:r.seedFrom,styleHideAt:r.hideFrom,inpage:r.inpage.seed,
        detailClear:{shots:r.shots.filter(s=>s.inSeed&&s.t0<r.seedTo+500).length,shotsAbsent:r.shots.filter(s=>s.inSeed&&s.absentRoll&&s.t0<r.seedTo+500).length,videoFrames:(v.frames||[]).filter(f=>f.inSeed===1).length,videoAbsent:(v.frames||[]).filter(f=>f.inSeed===1&&f.absentRoll).length},
        styleHide300ms:{shots:r.shots.filter(s=>s.inSeed&&r.hideFrom&&s.t1>=r.hideFrom).length,shotsAbsent:r.shots.filter(s=>s.inSeed&&s.absentRoll&&r.hideFrom&&s.t1>=r.hideFrom).length,videoFrames:(v.frames||[]).filter(f=>f.inSeed===2).length,videoAbsent:(v.frames||[]).filter(f=>f.inSeed===2&&f.absentRoll).length}}:null,
      absentControl:{shots:r.shots.filter(s=>s.inCtl).length,shotsAbsent:r.shots.filter(s=>s.inCtl&&s.absentRoll).length,videoFrames:(v.frames||[]).filter(f=>f.inCtl).length,videoAbsent:(v.frames||[]).filter(f=>f.inCtl&&f.absentRoll).length}};
    const valid=[];if(!r.settledOk)valid.push('never reached refined-terrain');if(steps.length<10)valid.push('fewer than 10 minute steps');if(cellOut.hiddenSamples)valid.push('page hidden during observation');if(r.hung.length)valid.push('bounded page call timed out: '+r.hung.join(','));
    if(!cellOut.absentControl.shots||cellOut.absentControl.shotsAbsent<cellOut.absentControl.shots)valid.push('absent control not classified absent in shots');
    if(cellOut.absentControl.videoFrames&&cellOut.absentControl.videoAbsent<cellOut.absentControl.videoFrames*0.5)valid.push('absent control not classified absent in the recording');
    if(c.seed&&!(cellOut.seed.detailClear.videoAbsent+cellOut.seed.detailClear.shotsAbsent>0))valid.push('seeded detail.clear() not seen');if(c.seed&&r.hideFrom&&!(cellOut.seed.styleHide300ms.videoAbsent>0&&cellOut.seed.styleHide300ms.shotsAbsent>0))valid.push('seeded 300 ms hide not seen in both the recording and the shots');
    cellOut.invalidReasons=valid;cellOut.valid=valid.length===0;
    fs.writeFileSync(path.join(dir,'frames.json'),JSON.stringify({shots:r.shots,video:v.frames,inpage:r.inpage}));
    out.cells[c.name]=cellOut;
    console.log(label,c.name,'steps',steps.length,'shots',obsShots.length,'absentRoll',cellOut.shots.absentRoll,'video',cellOut.video.absentRoll,'jobs',cellOut.jobsPosted,'valid',cellOut.valid,valid.join('; '));
  }
  fs.writeFileSync(path.join(outDir,label+'.json'),JSON.stringify(out,null,1));
  console.log('isolation allowed',out.isolation.allowedExternal);
  process.exit(out.isolation.allowedExternal!==0?2:0);   // explicit: a browser that would not close must not hold the recipe open
})().catch(e=>{console.error(e);process.exit(1);});
