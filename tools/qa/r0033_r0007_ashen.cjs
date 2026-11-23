'use strict';
// R0033 (issue 100), owner decision 2026-11-22: controlled re-capture of the accepted R0007 case
// `R0007-warm-ashen-below-horizon` at an astronomically consistent instant. The original ran at the fixed clock
// 2026-03-08T06:30Z, when the REAL Moon (which the refined sky follows; simMoon* does not reach it) was 78% lit at
// +22 degrees, while the scene simulated a new Moon below the horizon. This recipe keeps the original hash byte for
// byte (New York, method 2, simTime=01:30, simMoon=0.01, simWax=1, simMoonAlt=-20, simMoonH=42, clear sky, weather
// and radar offline) and changes only the fixed epoch, to 2026-02-18T06:30Z (01:30 EST, the same wall time and UTC
// offset), when the real Moon is a waxing 0.7% crescent at -56.5 degrees: below the horizon, consistent with the
// simulated one. The choice is justified by the effect-free computation
//   node tools/qa/r0033_m6_lunar_divergence.mjs --instants 2026-02-18T06:30:00Z --lat 40.71 --lon -74.01
// (refined lunar term exactly 0). This recipe also OBSERVES the refined sky's own instant and Moon in the page
// (realSkyState().last: utcMs, physicalState.moon, exposure; a pure diagnostic read).
// Isolation: every browser starts through tools/qa/r0033_isolation.cjs (Node guard, refusing proxy, catch-all route
// and WebSocket route before any page, every request logged, exit 3 on any escape). Synthetic fixture only; the
// prayer request is fulfilled from a fixture copied from the original case input; weather and radar fail in-page, as
// in the original ('weather-offline', 'radar-offline'). No provider is contacted; no geolocation is granted.
// Moon facts are read through SalahMoonRuntime.observe() only (R0036), never .state/.surface().
// Usage: node tools/qa/r0033_r0007_ashen.cjs --root <tree> --out <dir> --engine <chromium|firefox> [--playwright <pkg>]
//        [--epoch 2026-02-18T06:30:00.000Z]
// Output: <out>/record.json, card-1s.png, card-15s.png, moon-1s.png, moon-15s.png, requests.json; one JSON line on stdout.
// Exit: 0 complete and every check holds, 1 error, 2 INCOMPLETE (not ready in time), 3 isolation escape (overrides),
//       4 FAIL (complete, a check does not hold).
require('./v1_net_guard.cjs').install();                                  // before any other module can connect
const iso=require('./r0033_isolation.cjs');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),zlib=require('node:zlib'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium';
const EPOCH=a.epoch||'2026-02-18T06:30:00.000Z';
fs.mkdirSync(out,{recursive:true});
// The original case's hash, unchanged (docs/rlgwo-execution/20261014/R0007/preservation/*/R0007-warm-ashen-below-horizon/case-input.json).
const HASH='#lat=40.71&lon=-74.01&label=NewYork&method=2&school=0&time=24&tz=America%2FNew_York&simTime=01%3A30&simMoon=0.01&simWax=1&simMoonAlt=-20&simMoonH=42&simWx=0&simCloud=0';
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.gz':'application/octet-stream','.bin':'application/octet-stream','.woff2':'font/woff2'};
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
// The original 'healthy' prayer payload; its Gregorian date follows the request (dateFromRequest), the rest is copied.
const prayer=day=>{const [d,m,y]=day.split('-').map(Number);return {timings:{Fajr:'05:00',Sunrise:'06:00',Dhuhr:'12:00',Asr:'15:30',Sunset:'18:00',Maghrib:'18:00',Isha:'19:30'},
 date:{gregorian:{date:day,day:String(d).padStart(2,'0'),month:{number:m,en:MONTHS[m-1]},year:String(y)},hijri:{date:'19-02-1448',day:'19',month:{number:2,en:'Safar'},year:'1448'}},meta:{timezone:'America/New_York'}};};
const fixture=u=>{const m=u.hostname==='api.aladhan.com'&&/\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u.pathname);return m?{code:200,status:'OK',data:prayer(m[1])}:null;};
const SHIM=`(()=>{const nf=window.fetch.bind(window);window.fetch=(input,init)=>{const u=String(input&&input.url||input);
 if(u.includes('api.open-meteo.com'))return Promise.reject(new TypeError('controlled weather unavailable'));
 if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
 return nf(input,init);};})();`;
const READY=`(()=>{const c=document.querySelector('.c'),o=window.SalahMoonRuntime?.observe?.();const src=o?.state?.visibleSource;
 return !!(c&&c.classList.contains('moon-ready')&&document.fonts.status==='loaded'&&o&&o.current&&(src==='terrain-preview'||src==='refined-terrain'));})()`;
const FACTS=`(()=>{const c=document.querySelector('.c'),cs=c?getComputedStyle(c):null,o=window.SalahMoonRuntime?.observe?.()??null,q=window.qaState?.()??null,
  rs=window.realSkyState?.()??null,last=rs?.last??null,ph=document.querySelector('.mphoto'),r=ph?ph.getBoundingClientRect():null,cr=c?c.getBoundingClientRect():null;
 const mt=q?.moonTruth??null;
 return {now:Date.now(),nowIso:new Date(Date.now()).toISOString(),moonReady:c?c.classList.contains('moon-ready'):null,
  css:cs?{moonbeam:cs.getPropertyValue('--moonbeam').trim(),moongrp:cs.getPropertyValue('--moongrp').trim(),moonocc:cs.getPropertyValue('--moonocc').trim()}:null,
  runtime:o?{visibleSource:o.state?.visibleSource??null,status:o.state?.status??null,current:o.current??null,presentable:o.presentable??null}:null,
  moonTruth:mt?{phaseFraction:mt.phaseFraction,waxing:mt.waxing,moonAltitudeDeg:mt.moonAltitudeDeg,moonlightOpacity:mt.moonlightOpacity,calendarMoonVisible:mt.calendarMoonVisible,
   earthshine:mt.earthshine,reason:mt.reason??null,lunarLight:mt.lastConsumed?.observation?.light??null}:null,
  refinedSky:last?{utcMs:last.utcMs,utcIso:new Date(last.utcMs).toISOString(),moon:last.physicalState?.moon??null,sun:last.physicalState?.sun?{altDeg:last.physicalState.sun.altDeg,azDeg:last.physicalState.sun.azDeg}:null,exposure:last.exposure??null}:null,
  refinedSkyStatus:rs?.status??null,
  card:cr?{x:cr.x,y:cr.y,width:cr.width,height:cr.height}:null,disc:r?{x:r.x,y:r.y,width:r.width,height:r.height}:null};})()`;
// Minimal PNG decoder (8-bit RGB/RGBA, non-interlaced), for the disc/sky pixel statistics below.
function decodePng(buf){let p=8,w=0,h=0,ct=0;const idat=[];while(p<buf.length){const len=buf.readUInt32BE(p),type=buf.toString('ascii',p+4,p+8),d=buf.subarray(p+8,p+8+len);
  if(type==='IHDR'){w=d.readUInt32BE(0);h=d.readUInt32BE(4);if(d[8]!==8||d[12]!==0)throw Error('unsupported png');ct=d[9];}else if(type==='IDAT')idat.push(d);else if(type==='IEND')break;p+=12+len;}
 const bpp=ct===6?4:ct===2?3:0;if(!bpp)throw Error('unsupported colour type '+ct);const raw=zlib.inflateSync(Buffer.concat(idat)),stride=w*bpp,px=Buffer.alloc(h*stride);
 for(let y=0;y<h;y++){const f=raw[y*(stride+1)],src=raw.subarray(y*(stride+1)+1,(y+1)*(stride+1)),row=px.subarray(y*stride,(y+1)*stride),prev=y?px.subarray((y-1)*stride,y*stride):null;
  for(let i=0;i<stride;i++){const A=i>=bpp?row[i-bpp]:0,B=prev?prev[i]:0,C=prev&&i>=bpp?prev[i-bpp]:0;let x=src[i];
   if(f===1)x+=A;else if(f===2)x+=B;else if(f===3)x+=(A+B)>>1;else if(f===4){const pa=Math.abs(B-C),pb=Math.abs(A-C),pc=Math.abs(A+B-2*C);x+=pa<=pb&&pa<=pc?A:pb<=pc?B:C;}row[i]=x&255;}}
 return {w,h,bpp,px};}
// Disc interior (radius 0.85) versus a sky annulus (1.6 to 3 radii) inside the card: a star is a pixel more than 24
// luma codes above its region's median. A model computation that supports, and does not replace, looking at the crop.
function discStats(png,disc,card){const img=decodePng(png),cx=disc.x-card.x+disc.width/2,cy=disc.y-card.y+disc.height/2,R=disc.width/2;
 const reg={inside:[],annulus:[]};for(let y=0;y<img.h;y++)for(let x=0;x<img.w;x++){const d=Math.hypot(x+.5-cx,y+.5-cy)/R,i=(y*img.w+x)*img.bpp,l=0.2126*img.px[i]+0.7152*img.px[i+1]+0.0722*img.px[i+2];
  if(d<=0.85)reg.inside.push(l);else if(d>=1.6&&d<=3)reg.annulus.push(l);}
 const sum=xs=>{const s=[...xs].sort((p,q)=>p-q),med=s[Math.floor(s.length/2)]??0;return {pixels:s.length,median:+med.toFixed(2),max:+(s[s.length-1]??0).toFixed(2),starLikePixels:s.filter(x=>x>med+24).length};};
 return {centreInCardPx:{x:+cx.toFixed(1),y:+cy.toFixed(1)},radiusPx:+R.toFixed(2),inside:sum(reg.inside),skyAnnulus:sum(reg.annulus)};}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const S=await iso.launch(PW,engine);let code=0;const record={schema:'r0033-r0007-ashen-recapture/1',caseId:'R0007-warm-ashen-below-horizon (controlled re-capture)',engine,version:S.browser.version(),
  playwright:(()=>{try{return require(path.join(path.dirname(require.resolve(a.playwright||'playwright')),'package.json')).version;}catch{return null;}})(),
  input:{entry:'index.html',hash:HASH,clock:{mode:'fixed (Playwright clock.setFixedTime; timers, performance and animation frames native)',epoch:EPOCH},viewport:{width:370,height:570},dpr:1,timezoneId:'America/New_York',locale:'en-US',reducedMotion:'no-preference',
   responses:{prayer:'fixture: the original healthy payload, Gregorian date from the request',weather:'offline (rejected in page)',radar:'offline (rejected in page)'}},
  documentHashes:{servedIndexHtml:sha(fs.readFileSync(path.join(root,'index.html')))}};
 try{
  const C=await S.context({viewport:{width:370,height:570},deviceScaleFactor:1,timezoneId:'America/New_York',locale:'en-US',reducedMotion:'no-preference'},{origin:base,fixture});
  await C.context.addInitScript(SHIM);const page=await C.newPage();await page.clock.setFixedTime(new Date(EPOCH));
  const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
  await page.goto(base+'/index.html'+HASH);const t0=Date.now();let ready=false;
  while(Date.now()-t0<120000){if(await page.evaluate(READY))(ready=true);if(ready)break;await page.waitForTimeout(250);}
  record.readyMs=ready?Date.now()-t0:null;
  if(!ready){record.result='INCOMPLETE';record.final=await page.evaluate(FACTS);code=2;}
  else{const shots={};
   for(const [label,wait] of [['1s',1000],['15s',14000]]){await page.waitForTimeout(wait);const f=await page.evaluate(FACTS),card=await page.locator('.c').screenshot();
    const pad=24,clip={x:Math.max(0,f.disc.x-pad),y:Math.max(0,f.disc.y-pad),width:f.disc.width+2*pad,height:f.disc.height+2*pad},moon=await page.screenshot({clip});
    fs.writeFileSync(path.join(out,`card-${label}.png`),card);fs.writeFileSync(path.join(out,`moon-${label}.png`),moon);
    shots[label]={facts:f,cardPng:{sha256:sha(card),bytes:card.length},moonPng:{sha256:sha(moon),bytes:moon.length,clip},pixels:discStats(card,f.disc,f.card)};}
   record.captures=shots;const f=shots['15s'].facts,m=f.refinedSky?.moon;
   const checks={refinedSkyAtEpoch:f.refinedSky?.utcIso===new Date(EPOCH).toISOString(),refinedMoonBelowHorizon:m!=null&&m.altDeg<0,refinedMoonNearNew:m!=null&&m.illuminatedFraction<0.02,
    moonlightOpacityZero:f.moonTruth?.moonlightOpacity===0,calendarMoonVisible:f.moonTruth?.calendarMoonVisible===true,moonReady:f.moonReady===true,
    currentTerrain:f.runtime?.current===true&&['terrain-preview','refined-terrain'].includes(f.runtime?.visibleSource),
    noStarLikePixelsInsideDisc:Object.values(shots).every(s=>s.pixels.inside.starLikePixels===0),card325x530:f.card?.width===325&&f.card?.height===530};
   record.checks=checks;record.result=Object.values(checks).every(Boolean)?'PASS':'FAIL';if(record.result!=='PASS')code=4;}
  record.pageErrors=errors;
 }catch(e){record.error=String(e.stack||e).slice(0,600);code=1;}
 finally{await S.settle();record.isolation=S.verdict();fs.writeFileSync(path.join(out,'requests.json'),JSON.stringify({verdict:S.verdict(),requests:S.ledger.requests},null,1)+'\n');await S.close();server.close();}
 fs.writeFileSync(path.join(out,'record.json'),JSON.stringify(record,null,1)+'\n');
 console.log(JSON.stringify({engine,result:record.result??'ERROR',checks:record.checks??null,isolation:record.isolation}));
 if(!record.isolation.ok){console.error('ISOLATION ESCAPE '+JSON.stringify(record.isolation.escapes));process.exitCode=3;}else process.exitCode=code;
})();
