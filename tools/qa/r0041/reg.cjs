'use strict';
// R0041 (issue 143) row R41-REG, the AGENTS gates D, E, I and J scene evidence for one tree. Native recipe; NOT part
// of the node glob. Chromium, headless, through iso.cjs (loopback only), synthetic fixture (lat 24.47, lon 39.61,
// method 4), clear sky unless the scene sets weather. Crops are written at device pixels (DPR 1 and 2) to <cropDir>
// (kept outside the repository); a JSON index of measurements is written to <outJson>.
// Scenes (AGENTS "Evidence requirements" for D, E, I, J):
//   D  crescent (right limb in frame), half, gibbous, full, new (opaque ashen calendar disc), each frozen at its
//      instant; opacity proof = point-like bright pixels inside the disc (the witness rule) and the Moon-mask state
//   E  forced lunar halo (&debugOptic=lunarhalo), forced paraselene (&debugOptic=paraselene), thin-cloud halo/corona
//      scene (&simWx=2&simCloud=30), on an eligible night Moon; moonTruth light and optic readouts recorded
//   I  star twinkle: real speed, full motion, a Moon-free sky region shot twice 1 s apart (pixels changed counted)
//   J  header (buckle zoom) and footer crops of every scene; footer date row bottom within the card
// Corrections (2026-11-24, minimal): the paraselene element is `.mparhelia` (the product has no `.mparaselene`), and its
// box and computed visibility are recorded; gate I watches R41_TWINKLE_S seconds (default 30) at real speed, a shot
// every 500 ms, and counts sky pixels whose luma range over the watch is >= 4 (and >= 12) outside the Moon square (the
// SVG star layer is display:none under the refined sky, so the product's debugMotion star sample cannot see it).
// R41_REG_ONLY=<comma ids> limits the scenes; R41_REG_DPRS=<list> the ratios; R41_HEADED=1 launches headed.
// Usage: node reg.cjs <repoRoot> <outJson> <cropDir>
const fs=require('node:fs'),path=require('node:path');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [root,outFile,cropDir]=process.argv.slice(2);fs.mkdirSync(cropDir,{recursive:true});
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&qa=1';
const CLEAR='&simWx=0&simCloud=0';
const SCENES=[
  {id:'D-crescent',iso:'2026-11-12T15:30:00Z',frag:CLEAR},{id:'D-half',iso:'2026-11-17T16:30:00Z',frag:CLEAR},{id:'D-gibbous',iso:'2026-11-20T17:00:00Z',frag:CLEAR},
  {id:'D-full',iso:'2026-11-23T16:30:00Z',frag:CLEAR},{id:'D-new',iso:'2027-01-06T19:30:00Z',frag:CLEAR},
  {id:'E-lunarhalo-forced',iso:'2026-11-23T16:30:00Z',frag:CLEAR+'&debugOptic=lunarhalo'},{id:'E-paraselene-forced',iso:'2026-11-23T16:30:00Z',frag:CLEAR+'&debugOptic=paraselene'},
  {id:'E-thin-cloud-halo-corona',iso:'2026-11-20T17:00:00Z',frag:'&simWx=2&simCloud=30'},
  {id:'I-star-twinkle',iso:'2027-01-06T19:30:00Z',frag:CLEAR+'&motion=full&debugMotion=1',live:true}].filter(s=>!process.env.R41_REG_ONLY||process.env.R41_REG_ONLY.split(',').includes(s.id));
const FREEZE=ms=>`(()=>{const ND=Date,at=${ms};class D extends ND{constructor(...a){super(...(a.length?a:[at]));}static now(){return at;}}window.Date=D;})();`;
const SHIFT=ms=>`(()=>{const ND=Date,off=${ms}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const Yf=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
// Minimal PNG encoder (RGB) for crops.
const zlib=require('node:zlib');const crcT=(()=>{const t=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
const crc=b=>{let c=0xffffffff;for(const x of b)c=crcT[(c^x)&255]^(c>>>8);return (c^0xffffffff)>>>0;};
const chunk=(type,data)=>{const l=Buffer.alloc(4);l.writeUInt32BE(data.length);const td=Buffer.concat([Buffer.from(type),data]);const c=Buffer.alloc(4);c.writeUInt32BE(crc(td));return Buffer.concat([l,td,c]);};
function png(img,x0,y0,w,h){x0=Math.max(0,Math.floor(x0));y0=Math.max(0,Math.floor(y0));w=Math.min(img.width-x0,Math.ceil(w));h=Math.min(img.height-y0,Math.ceil(h));const raw=Buffer.alloc((3*w+1)*h);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const si=4*((y0+y)*img.width+x0+x),di=y*(3*w+1)+1+3*x;raw[di]=img.data[si];raw[di+1]=img.data[si+1];raw[di+2]=img.data[si+2];}
  const ih=Buffer.alloc(13);ih.writeUInt32BE(w,0);ih.writeUInt32BE(h,4);ih[8]=8;ih[9]=2;return Buffer.concat([Buffer.from([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a]),chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);}
function discStats(img,rect){const k=img.width/325,S=Math.min(rect.w,rect.h)*k,x0=rect.x*k,y0=rect.y*k,cx=x0+S/2,cy=y0+S/2,at=(x,y)=>x<0||y<0||x>=img.width||y>=img.height?null:Yf(img.data,4*(y*img.width+x));
  const corner=[],d=[];let pts=0;for(let y=Math.floor(y0);y<y0+S;y++)for(let x=Math.floor(x0);x<x0+S;x++){const r=Math.hypot(x+.5-cx,y+.5-cy),v=at(x,y);if(v==null)continue;if(r>=.53*S)corner.push(v);else if(r<=.47*S)d.push([x,y,v,r]);}
  corner.sort((a,b)=>a-b);const mc=corner[corner.length>>1]??0;
  for(const [x,y,v,r] of d){if(r>.47*S-3)continue;let m=0,n=0;for(const [dx,dy] of [[2,0],[-2,0],[0,2],[0,-2],[2,2],[2,-2],[-2,2],[-2,-2]]){const u=at(x+dx,y+dy);if(u!=null){m+=u;n++;}}if(v-m/n>30&&v>mc+30)pts++;}
  const inFrame=d.length/(Math.PI*(.47*S)**2);return {discMeanY:+(d.reduce((p,q)=>p+q[2],0)/d.length).toFixed(1),cornerMedianY:+mc.toFixed(1),pointLikeBrightInDisc:pts,discFractionInFrame:+Math.min(1,inFrame).toFixed(3)};}
async function scene(L,env,sc,dpr){
  const ctx=await L.newContext({deviceScaleFactor:dpr,reducedMotion:sc.live?'no-preference':'reduce'});await ctx.addInitScript(sc.live?SHIFT(Date.parse(sc.iso)):FREEZE(Date.parse(sc.iso)));
  const page=await ctx.newPage();await page.goto(env.origins.url('127.0.0.1','/index.html')+BASE+sc.frag,{waitUntil:'load',timeout:120000});
  const settled=await page.waitForFunction(()=>{const o=window.SalahMoonRuntime?.observe?.();return o?.current&&o.state.visibleSource==='refined-terrain'&&document.querySelector('.c')?.classList.contains('real-sky-composed');},null,{timeout:180000,polling:250}).then(()=>true).catch(()=>false);
  await page.waitForTimeout(5000);
  const geo=await page.evaluate(()=>{const r=s=>{const e=document.querySelector(s);if(!e)return null;const b=e.getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};};
    const t=window.qaState().moonTruth,o=window.SalahMoonRuntime.observe(),c=document.querySelector('.c');
    return {mphoto:r('.mphoto'),card:r('.c'),footerLast:(()=>{const f=[...document.querySelectorAll('.c *')].filter(e=>e.getBoundingClientRect().height>0);let m=0;for(const e of f)m=Math.max(m,e.getBoundingClientRect().bottom);return m;})(),
      header:r('.hdr')||r('header')||r('.belt'),truth:{phaseFraction:t.phaseFraction,alt:t.moonAltitudeDeg,displayMode:t.displayMode,moonlightOpacity:t.moonlightOpacity,lunarLight:t.lunarLight,degraded:t.degraded,limitation:t.limitation,source:o.state.visibleSource},
      maskOn:!!document.querySelector('.moon-mask-disc.mask-on'),moonReady:c.classList.contains('moon-ready'),
      optics:(()=>{const v=s=>{const e=document.querySelector(s);return e?{opacity:getComputedStyle(e).opacity,display:getComputedStyle(e).display}:null;};return {mhalo:v('.mhalo'),mcorona:v('.mcorona'),mparhelia:v('.mparhelia'),mparheliaBox:r('.mparhelia'),mparheliaVisibility:(()=>{const e=document.querySelector('.mparhelia');return e?getComputedStyle(e).visibility:null;})()};})()};});
  const img=decodePng(await page.screenshot({scale:'device'}));let twinkle=null;
  if(sc.live){const k=img.width/325,mp=geo.mphoto,x0=Math.floor(10*k),x1=Math.floor(315*k),y0=Math.floor(62*k),y1=Math.floor(250*k);
    const inMoon=(x,y)=>mp&&x>=(mp.x-8)*k&&x<(mp.x+mp.w+8)*k&&y>=(mp.y-8)*k&&y<(mp.y+mp.h+8)*k;
    const n=(x1-x0)*(y1-y0),mn=new Float32Array(n).fill(1e9),mx=new Float32Array(n).fill(-1e9);let shots=0,last=img;const S=+(process.env.R41_TWINKLE_S||30),t0=Date.now(),dbg=[];
    const acc=im=>{let i=0;for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++,i++){const v=Yf(im.data,4*(y*im.width+x));if(v<mn[i])mn[i]=v;if(v>mx[i])mx[i]=v;}shots++;};acc(img);
    while(Date.now()-t0<S*1000){await page.waitForTimeout(500);last=decodePng(await page.screenshot({scale:'device'}));acc(last);if(dbg.length<200)dbg.push(await page.evaluate(()=>document.querySelector('.dbgmotion')?.textContent?.split(/\n/).filter(l=>/star|rAF|reduced/.test(l)).join(' | ')??null));}
    let c4=0,c12=0,counted=0,i=0;for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++,i++){if(inMoon(x,y))continue;counted++;const d=mx[i]-mn[i];if(d>=4)c4++;if(d>=12)c12++;}
    {const w=x1-x0,h=y1-y0,rm={width:w,height:h,data:new Uint8Array(4*w*h)};let p=0;let pts=0;for(let q=0;q<w*h;q++){const d=Math.min(255,Math.round(8*(mx[q]-mn[q])));rm.data[4*q]=rm.data[4*q+1]=rm.data[4*q+2]=d;}
      // point-like share: pixels with range >= 12 whose range exceeds the mean range of their 8 neighbours at distance 2 by >= 8
      for(let y=2;y<h-2;y++)for(let x=2;x<w-2;x++){const q=y*w+x,d=mx[q]-mn[q];if(d<12)continue;let m=0;for(const [dx,dy] of [[2,0],[-2,0],[0,2],[0,-2],[2,2],[2,-2],[-2,2],[-2,-2]]){const u=q+dy*w+dx;m+=mx[u]-mn[u];}if(d-m/8>=8)pts++;}
      p=pts;fs.writeFileSync(path.join(cropDir,`${sc.id}-dpr${dpr}-range-x8.png`),png(rm,0,0,w,h));var pointLike12=p;}
    twinkle={pointLikeRangeAtLeast12:pointLike12,region:'CSS x 10-315, y 62-250 minus the Moon square (+8 px)',watchSeconds:S,shots,pixels:counted,rangeAtLeast4:c4,rangeAtLeast12:c12,debugMotion:[dbg[0],dbg[Math.floor(dbg.length/2)],dbg.at(-1)]};
    fs.writeFileSync(path.join(cropDir,`${sc.id}-dpr${dpr}-t1.png`),png(last,0,0,last.width,last.height));}
  await ctx.close();const k=img.width/325,m=geo.mphoto;
  const files=[`${sc.id}-dpr${dpr}-card.png`,`${sc.id}-dpr${dpr}-moon.png`,`${sc.id}-dpr${dpr}-header.png`,`${sc.id}-dpr${dpr}-footer.png`];
  fs.writeFileSync(path.join(cropDir,files[0]),png(img,0,0,img.width,img.height));
  const pad=sc.id.startsWith('E-')?70:6;fs.writeFileSync(path.join(cropDir,files[1]),png(img,(m.x-pad)*k,(m.y-pad)*k,(m.w+2*pad)*k,(m.h+2*pad)*k));
  fs.writeFileSync(path.join(cropDir,files[2]),png(img,0,0,img.width,60*k));fs.writeFileSync(path.join(cropDir,files[3]),png(img,0,(530-70)*k,img.width,70*k));
  return {id:sc.id,dpr,instant:sc.iso,fragmentExtra:sc.frag,clock:sc.live?'real speed from the instant':'frozen',settledToRefined:settled,image:[img.width,img.height],...geo,disc:discStats(img,m),twinkle,files};
}
(async()=>{
  const env=await createEnv({root});const out={schema:'r0041-reg-scenes/1',tree:path.basename(path.resolve(root)),engine:'chromium',headless:process.env.R41_HEADED!=='1',scenes:[]};
  for(const dpr of (process.env.R41_REG_DPRS||'1,2').split(',').map(Number)){const L=await launch(env,{engine:'chromium',mode:'route',reducedMotion:'reduce',headless:process.env.R41_HEADED!=='1',deviceScaleFactor:dpr,extraArgs:dpr>1?['--force-device-scale-factor=2']:[]});
    try{for(let i=0;i<SCENES.length;i+=3){const res=await Promise.all(SCENES.slice(i,i+3).map(s=>scene(L,env,s,dpr)));out.scenes.push(...res);for(const r of res)console.log(r.id,dpr,JSON.stringify(r.disc),JSON.stringify(r.truth).slice(0,160),r.twinkle?JSON.stringify(r.twinkle):'');}}
    finally{await L.close().catch(()=>{});}}
  out.isolation=env.finish();out.isolation={allowedExternal:out.isolation.allowedExternal,externalAttempts:out.isolation.externalAttempts};
  fs.writeFileSync(outFile,JSON.stringify(out,null,1)+'\n');console.log('allowed',out.isolation.allowedExternal);
})().catch(e=>{console.error(e);process.exit(1);});
